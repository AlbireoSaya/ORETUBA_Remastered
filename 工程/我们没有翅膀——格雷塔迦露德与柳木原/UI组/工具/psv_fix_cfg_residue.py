# -*- coding: utf-8 -*-
r"""psv_fix_cfg_residue.py —— 25 设置屏两页底图：**残留检验** + 页2 行5 残留带盖片派生（幂等）

**Issue**：ISSUE-20260926-06（PSV 换皮 · C 组设置屏）· **修复轮**（ISSUE-20260926-06_C设置屏修复）

===============================================================================
一、缺陷 ① 指控的「底图日文页标题残留」—— 本脚本是那次指控的**可执行检验**
===============================================================================
送审意见要求在 `x_ui_psv_cfg_page1/2.png` 的标题带 (137..275, 208..245) 程序化补除
「4 个浅白大字（系统页「画面設定」/声音页「音量設定」）」。本脚本给出的**实测结论**：

  · 该带里**没有**亮于本地底的成字结构。口径：检验带取**实际可见部分** (140,216)-(300,250)
    —— 上界 216 是因为页签药丸 `cfg.tab1_on`(136,166,181,50) 盖到 y216，其上不属「可见残影」；
    底取**本行中位**（面板在该带干净区逐值噪声 = 0/255，`m54` 已验证面板纵向严格线性）。
  · 高于本行中位 ≥6/255 的像素里，**≥200px 的连通域 = 雪花/描边等底图装饰**（不动）；
    其余小簇总量 < 500px / 5600px 带、且亮度上界仅 21/255（**不成字**，是雪花细臂与抗锯齿残粒）。
  ⇒ 因此本脚本**不写页底图**（no-op 即幂等）：那 4 个浅白大字是**引擎绘制**的
    `cfg.sec_picture`(系统页) / `cfg.sec_volume`(声音页) 节题，样文「画面设定」/「音量设定」、
    size=34、元素框 (136,214,400,36) / (152,214,400,36) ⇒ 4 字恰好占 x136..272、y≈212..245，
    与送审量到的带**逐值吻合**。处置在版面侧（色值 → `@palette.psv_ink`、y 让开页签），
    见 `_工作/ISSUE-20260926-06_C设置屏修复/复现脚本/psv_fix_config_screen.py`。
  · 像素级对照证据（`--evidence` 产出）：`shot_12_config.png` 与 `x_ui_psv_cfg_page1.png`
    同带差图里，**shot 更亮 >5 的像素共 676 个、bbox y210..239 x218..273** —— 正是引擎字的落点；
    而底图在该带的**唯一**亮点结构是左侧雪花（连通域 ≥200px）。

===============================================================================
二、缺陷 ⑤ 的配套件：页2 行 5 残留标签带**盖片**
===============================================================================
⑤ 把「语音设定」上移进页2 第 5 行槽位、并把「主音量（语音）/角色音量」两行整体下移一个节距
(74px)；原被 `tag_snd_05` 盖住的**残留标签带**（被擦除的日文行名留下的亮度凹陷）会露出来。
实测（本脚本口径）：
  · 凹陷带 **y584..606，最深 5.33/255（逐列均值口径）/ x262..~710**；
  · 该带**两侧 x≤230、x≥730 与原值逐列相等（差 0.00）**，且面板在 x900..1200 于这些行
    **严格恒色（逐行）** ⇒ 补底取「同行的干净参考列窗均值」按行铺满：**边缘逐值相等、无接缝**。
产出 `x_ui_psv_cfg_cover_c2_05.png`（520×48 @ (230,570)，z=9，口径同 m54 的 5 张盖槽片）。

**幂等**：本脚本对页底图**只读**；盖片为确定性派生（同一输入 ⇒ 同一字节）。
**只读保证**：运行前后两页底图 md5 一致（不一致即报错）。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\psv_fix_cfg_residue.py              # 检验 + 落盘盖片
    python 工具\psv_fix_cfg_residue.py --dry-run    # 只算、不写盘
    python 工具\psv_fix_cfg_residue.py --evidence   # 顺带产出缺陷 ①⑤ 的对照证据图
"""
import argparse
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
EVID = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏修复", "_证据")
SHOTS = "E:/ZCode Workspace/Galgame/临时/wt-qbicons/临时/ui_run/runtime/savedata"

PAGES = ("x_ui_psv_cfg_page1.png", "x_ui_psv_cfg_page2.png")
BAND = (140, 216, 300, 250)        # 检验带 = 送审指控区的**实际可见部分**（见 §一）
THR = 6.0
DECOR_PX = 200
EDGE_PX = 6                        # 「接缝」口径：盖片最外 6px

SND05_BAND = (240, 578, 680, 604)  # C 组 audit 登记的残留带（必须被盖住）
SND05_COVER = (230, 570, 750, 618)  # 盖片实落点 (x0,y0,x1,y1)
SND05_REF = (900, 1200)            # 干净参考列窗（无残留/无滑槽/无装饰）
COVER_NAME = "x_ui_psv_cfg_cover_c2_05.png"


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def encode(im, step=2):
    """RGB 量化 step / alpha 原样 + optimize + compress_level=9（口径同 m53/m54）"""
    if step > 1:
        r, g, b, a = im.split()
        f = lambda v: min(255, ((v + step // 2) // step) * step)   # noqa: E731
        im = Image.merge("RGBA", (r.point(f), g.point(f), b.point(f), a))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def components(mask):
    """4-邻域连通域标记；返回 (label 图, [(size, bbox, id)])"""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    out = []
    cur = 0
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or lab[sy, sx]:
                continue
            cur += 1
            stack = [(sy, sx)]
            lab[sy, sx] = cur
            n = 0
            x0 = x1 = sx
            y0 = y1 = sy
            while stack:
                y, x = stack.pop()
                n += 1
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        stack.append((ny, nx))
            out.append((n, (x0, y0, x1, y1), cur))
    return lab, out


def audit_page(name):
    """返回 (文字状亮簇, 装饰连通域, 亮度上界)：亮簇 = 高于本行中位 ≥THR 且 <DECOR_PX、且不贴装饰"""
    with Image.open(os.path.join(ASSETS, name)) as im:
        arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    x0, y0, x1, y1 = BAND
    L = arr[y0:y1, x0:x1].mean(axis=2)
    med = np.median(L, axis=1)[:, None]
    mask = L > med + THR
    lab, comps = components(mask)
    decor = [c for c in comps if c[0] >= DECOR_PX]
    small = [c for c in comps if c[0] < DECOR_PX]
    zone = np.zeros_like(mask)
    for n, box, cid in decor:
        zone |= (lab == cid)
    for _ in range(2):                                   # 装饰的 2px 膨胀域
        g = zone.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g |= np.roll(zone, (dy, dx), axis=(0, 1))
        zone = g
    text, touched = [], []
    for c in small:
        sub = zone[c[1][1]:c[1][3] + 1, c[1][0]:c[1][2] + 1]
        (touched if sub.any() else text).append(c)
    return text, decor, touched, (float((L - med)[mask].max()) if mask.any() else 0.0)


def make_cover():
    """页2 行5 残留带盖片 = 同行干净参考列窗均值按行铺满（见 §二）"""
    with Image.open(os.path.join(ASSETS, PAGES[1])) as im:
        page = im.convert("RGB")
    arr = np.asarray(page, dtype=np.float32)
    x0, y0, x1, y1 = SND05_COVER
    rx0, rx1 = SND05_REF
    ref = arr[:, rx0:rx1].mean(axis=1)
    fill = np.repeat(ref[y0:y1][:, None, :], x1 - x0, axis=1)
    diff = np.abs(fill - arr[y0:y1, x0:x1]).mean(axis=2)
    edge = max(float(diff[:, :EDGE_PX].max()), float(diff[:, -EDGE_PX:].max()))
    rows = np.nonzero(diff.max(axis=1) >= 3.0)[0]
    band_y = (y0 + int(rows.min()), y0 + int(rows.max())) if len(rows) else (0, 0)
    cover = Image.fromarray(np.clip(fill, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    return cover, (x0, y0, x1 - x0, y1 - y0), edge, float(diff.max()), band_y


def evidence():
    """缺陷 ① 的对照图 + 缺陷 ⑤ 盖片前后对照图"""
    os.makedirs(EVID, exist_ok=True)
    box = (130, 200, 300, 256)
    for p, tag in [(os.path.join(ASSETS, PAGES[0]), "asset_p1"),
                   (os.path.join(ASSETS, PAGES[1]), "asset_p2"),
                   (os.path.join(SHOTS, "shot_12_config.png"), "shot12")]:
        im = Image.open(p).convert("RGB").crop(box)
        im.resize((im.width * 4, im.height * 4), Image.LANCZOS).save(
            os.path.join(EVID, "defect1_band_%s_x4.png" % tag))
    a = np.asarray(Image.open(os.path.join(ASSETS, PAGES[0])).convert("RGB")).astype(np.float32)
    s = np.asarray(Image.open(os.path.join(SHOTS, "shot_12_config.png")).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = box
    d = (s[y0:y1, x0:x1] - a[y0:y1, x0:x1]).mean(axis=2)
    Image.fromarray(np.clip(128 + d * 5, 0, 255).astype(np.uint8)).resize(
        ((x1 - x0) * 4, (y1 - y0) * 4), Image.NEAREST).save(
        os.path.join(EVID, "defect1_shot_minus_asset_x4.png"))
    ys, xs = np.nonzero(d > 5)
    bb = (int(y0 + ys.min()), int(y0 + ys.max()), int(x0 + xs.min()), int(x0 + xs.max())) if len(ys) else None
    cov = Image.open(os.path.join(ASSETS, COVER_NAME)).convert("RGB")
    page = Image.open(os.path.join(ASSETS, PAGES[1])).convert("RGB")
    x0c, y0c, wc, hc = SND05_COVER
    before = page.crop((200, 250, 800, 640))
    page.paste(cov, (x0c, y0c))
    after = page.crop((200, 250, 800, 640))
    pair = Image.new("RGB", (before.width, before.height * 2 + 6), (255, 0, 128))
    pair.paste(before, (0, 0))
    pair.paste(after, (0, before.height + 6))
    pair.resize((pair.width * 2, pair.height * 2), Image.NEAREST).save(
        os.path.join(EVID, "defect5_cover_before_after_x2.png"))
    return int((d > 5).sum()), int((d < -5).sum()), bb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--evidence", action="store_true")
    args = ap.parse_args()
    os.makedirs(EVID, exist_ok=True)
    before = {p: md5(os.path.join(ASSETS, p)) for p in PAGES}

    print("=" * 122)
    print("25 设置屏底图 · 残留检验（缺陷 ①）+ 页2 行5 残留带盖片（缺陷 ⑤ 配套）%s"
          % ("（dry-run）" if args.dry_run else ""))
    print("=" * 122)
    tot = 0
    for p in PAGES:
        text, decor, touched, dmax = audit_page(p)
        tot += sum(c[0] for c in text)
        print("%s ｜ 检验带 (140,216)-(300,250) ｜ 高于本行中位 ≥%.0f 的亮度上界 %.1f/255" % (p, THR, dmax))
        print("      装饰连通域（≥%dpx，不动）%d 个：%s"
              % (DECOR_PX, len(decor),
                 "、".join("%dpx@(%d,%d)" % (c[0], c[1][0] + BAND[0], c[1][1] + BAND[1]) for c in decor[:6]) or "无"))
        print("      **文字状亮簇 %d 簇 / %d px** ｜ 贴装饰边缘（视作装饰）%d 簇 / %d px ｜ 带面积 %d px"
              % (len(text), sum(c[0] for c in text), len(touched), sum(c[0] for c in touched),
                 (BAND[2] - BAND[0]) * (BAND[3] - BAND[1])))
    print("-" * 122)
    print("**标题带文字状亮簇合计 %d px（上限判据 500）** ⇒ %s"
          % (tot, "底图无页标题残留；缺陷 ① 的可见浅白大字为**引擎绘制节题**（证据见 §一）"
             if tot < 500 else "底图可能有残留，需人工复核"))

    cover, geo, edge, removed, band_y = make_cover()
    data = encode(cover, 2)
    if not args.dry_run:
        with open(os.path.join(ASSETS, COVER_NAME), "wb") as fh:
            fh.write(data)
    ok = (geo[0] <= SND05_BAND[0] and geo[1] <= SND05_BAND[1] and
          geo[0] + geo[2] >= SND05_BAND[2] and geo[1] + geo[3] >= SND05_BAND[3])
    print("盖片 %s：%dx%d ｜ 落点 (%d,%d,%d,%d)，z=9" % (COVER_NAME, cover.width, cover.height, *geo))
    print("      实测凹陷带 y%d..%d ｜ 被抹残留最深 %.2f/255 ｜ **最外 %dpx 接缝 max=%.2f/255（要求 ≤1）**"
          " ｜ 覆盖 audit 登记带 (240,578)-(680,604)：%s ｜ %d B"
          % (band_y[0], band_y[1], removed, EDGE_PX, edge, "是" if ok else "否", len(data)))
    if args.evidence:
        npos, nneg, bb = evidence()
        print("证据图：%s ｜ 缺陷① 同带差图（shot−asset）：正差 >5 的像素 %d 个、bbox %s；负差 %d 个"
              % (EVID, npos, bb, nneg))
    after = {p: md5(os.path.join(ASSETS, p)) for p in PAGES}
    bad = [p for p in PAGES if before[p] != after[p]]
    if bad:
        raise SystemExit("!! 页底图被改动：%s" % ", ".join(bad))
    print("两页底图只读自证：md5 运行前后一致 ✓（本脚本对页底图只读）")
    fs = [f for f in os.listdir(ASSETS) if f.lower().endswith(".png")]
    t = sum(os.path.getsize(os.path.join(ASSETS, f)) for f in fs)
    print("落盘后 assets/ui：%d 件 / %.2f MB（预算 96 MB）" % (len(fs), t / 1048576.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
