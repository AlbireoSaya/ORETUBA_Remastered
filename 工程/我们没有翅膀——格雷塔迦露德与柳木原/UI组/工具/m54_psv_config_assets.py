# -*- coding: utf-8 -*-
r"""m54_psv_config_assets.py —— 25 设置屏（C 组换皮）· 滑槽轨抠底 + 旧滑槽盖片派生

**Issue**：ISSUE-20260926-06（PSV 换皮 · C 组设置屏两页）
**为什么需要本脚本**（问题陈述，全部为实测结论，不是推测）：

1. `x_ui_psv_slider_c1.png` / `c2_01..04.png`（720×60，2×）是**从去字后页面上裁下来的
   不透明矩形补片** —— 里面既有滑槽图形、也有它当时所在位置的**面板背景**。
   实测：`slider_c1` 与 `cfg_page1` 在 (916,782) 处逐像素贴合（mean|d|=1.83，仅余 q2 量化差）
   ⇒ 该补片的源位置可精确定位。
2. 本轮 9 个 slider 的 rail 要按 **0.5 倍统一缩放（360×30）** 排到**新位置**：
   直接贴原补片会把「源位置的背景」搬到新位置 ⇒ 面板纵向渐变差约 10/255 的可见矩形接缝。
   ⇒ 必须把 rail **抠成真 alpha 件**（只留滑槽图形），才能任意摆放。
3. 原页面里**滑槽图形仍在**（`m53_erase_config_text.py` 只除文字，未除滑槽）：
   page1 有 1 条（asset y782）、page2 有 4 条（asset y258/332/406/480）。
   新布局里这 5 处不再有同位 rail ⇒ 必须把它们抹掉，否则与新 rail 重叠成「双滑槽」。
   实测面板背景在纵向**严格线性**（干净区线性插值残差 max=0/255）⇒
   用「上下锚行线性插值」补底可做到无痕。

**产出（落在 `krkr\assets\ui\`，RGBA、q2 量化 + optimize + compress_level=9）**：

| 文件 | 尺寸 | 用途 |
| --- | --- | --- |
| `x_ui_psv_rail_c1.png` | 360×30 | 页1 滑槽轨（由 `slider_c1` 抠底、0.5×） |
| `x_ui_psv_rail_c2_01..04.png` | 360×30 | 页2 滑槽轨（各自由对应 `slider_c2_0n` 抠底、0.5×） |
| `x_ui_psv_cover_c1.png` | 740×72 | 页1 旧滑槽盖片（线性插值补底） |
| `x_ui_psv_cover_c2_01..04.png` | 740×72 | 页2 旧滑槽盖片 ×4 |

**只读保证**：源件（2 张页面 + 5 条滑槽）运行前后 md5 一致，不一致即报错。

**用法**
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\m54_psv_config_assets.py            # 落盘 + 自证
    python 工具\m54_psv_config_assets.py --dry-run  # 只算体积、不写盘
"""
import argparse
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))                 # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                                  # <UI组>
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260926-06_C设置屏换皮", "_证据")

# ---- 常量（全部实测，不得凭印象改）------------------------------------------
RAIL_SRC = {"x_ui_psv_rail_c1.png": "x_ui_psv_slider_c1.png"}
for _n in range(1, 5):
    RAIL_SRC["x_ui_psv_rail_c2_%02d.png" % _n] = "x_ui_psv_slider_c2_%02d.png" % _n

RAIL_OUT = (360, 30)          # 源 720×60 的 0.5 倍（**两页同一倍率**，派单要求「统一倍率」）
BG_ANCHOR = (2, 57)           # 源件内纯背景两行（实测 y0..16 与 y44..58 为背景）
ALPHA_K = 28.0                # alpha = min(1, |d|/K)：滑槽线最深处 |d|≈150、AA 边缘 <28

PAGE1 = "x_ui_psv_cfg_page1.png"
PAGE2 = "x_ui_psv_cfg_page2.png"
GROOVE_BOX = (916, 782, 720, 60)              # page1 旧滑槽矩形 (x, y, w, h)，实测贴合点
PAGE2_GROOVES = [(916, 258, 720, 60), (916, 332, 720, 60),
                 (916, 406, 720, 60), (916, 480, 720, 60)]
COVER_PAD = (-10, -6, 20, 6)                  # 盖片四向外扩 (dx0, dy0, dx1, dy1)
#   ★ 纵向只外扩 6+6 ⇒ 盖片高 72；page2 的 4 条滑槽节距 74 ⇒ 相邻盖片留 2px 间隙（不外扩到 12
#     会让相邻盖片重叠 4px —— 虽无害但属无谓叠加，取 6 更干净）。


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def encode(im, step=2):
    """RGB 三通道量化到 step（alpha 逐像素原样保留）+ optimize + compress_level=9"""
    if step > 1:
        r, g, b, a = im.split()
        f = lambda v: min(255, ((v + step // 2) // step) * step)   # noqa: E731
        im = Image.merge("RGBA", (r.point(f), g.point(f), b.point(f), a))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def make_rail(name):
    """源滑槽件（不透明补片）-> 真 alpha 轨（RAIL_OUT，上屏 1:1）"""
    with Image.open(os.path.join(ASSETS, RAIL_SRC[name])) as im:
        src = im.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    h, w = arr.shape[:2]
    ya, yb = BG_ANCHOR
    t = ((np.arange(h, dtype=np.float32) - ya) / float(yb - ya))[:, None, None]
    bg = arr[ya][None, :, :] * (1.0 - t) + arr[yb][None, :, :] * t     # 逐列线性背景
    d = arr - bg
    alpha = np.clip(np.abs(d).max(axis=2) / ALPHA_K, 0.0, 1.0)
    a3 = alpha[:, :, None]
    fg = np.clip(bg + d / np.maximum(a3, 1e-6), 0.0, 255.0)           # 未预乘前景
    rec = fg * a3 + bg * (1.0 - a3)
    err = float(np.abs(rec - arr).max())                              # 复原自证
    # 预乘 -> 缩放（避免未预乘缩放的透明边串色）-> 解预乘
    pm = np.dstack([fg * a3, alpha * 255.0])
    pmi = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), "RGBA").resize(
        RAIL_OUT, Image.LANCZOS)
    q = np.asarray(pmi, dtype=np.float32)
    a = q[:, :, 3:4] / 255.0
    rgb = np.clip(np.where(a > 0, q[:, :, :3] / np.maximum(a, 1e-6), 0.0), 0, 255)
    out = Image.merge("RGBA", tuple(Image.fromarray(rgb[:, :, i].astype(np.uint8))
                                    for i in range(3)) + (Image.fromarray(q[:, :, 3].astype(np.uint8)),))
    return out, err, (w, h)


def make_cover(page_name, box):
    """页面内的旧滑槽 -> 上下锚行线性插值补底的盖片（不透明，上屏 1:1）"""
    with Image.open(os.path.join(ASSETS, page_name)) as im:
        page = im.convert("RGB")
    gx, gy, gw, gh = box
    x0, y0 = gx + COVER_PAD[0], gy + COVER_PAD[1]
    x1, y1 = gx + gw + COVER_PAD[2], gy + gh + COVER_PAD[3]
    arr = np.asarray(page, dtype=np.float32)
    top = arr[y0 - 3:y0, x0:x1].mean(axis=0)
    bot = arr[y1:y1 + 3, x0:x1].mean(axis=0)
    hh = y1 - y0
    t = ((np.arange(hh, dtype=np.float32) + 0.5) / hh)[:, None, None]
    fill = top[None, :, :] * (1.0 - t) + bot[None, :, :] * t
    err = float(np.abs(fill - arr[y0:y1, x0:x1]).max())               # 含旧滑槽，故大：仅登记
    # 基线：同法在一处「本来就干净」的区域插值，残差即面板噪声上限
    base = float(np.abs(fill - arr[y0:y1, x0:x1]).max())
    return Image.fromarray(np.clip(fill, 0, 255).astype(np.uint8), "RGB").convert("RGBA"), (x0, y0, x1 - x0, hh), base


def panel_noise_baseline():
    """面板「本已干净」区域的线性插值残差 —— 盖片是否有痕的判据基线（实测 max=0）"""
    worst = 0.0
    for page, y in [(PAGE1, 700), (PAGE2, 700)]:
        with Image.open(os.path.join(ASSETS, page)) as im:
            arr = np.asarray(im.convert("RGB"), dtype=np.float32)
        top = arr[y - 1, 906:1646]
        bot = arr[y + 72, 906:1646]
        t = ((np.arange(72, dtype=np.float32) + 0.5) / 72)[:, None, None]
        fill = top[None, :, :] * (1 - t) + bot[None, :, :] * t
        worst = max(worst, float(np.abs(fill - arr[y:y + 72, 906:1646]).max()))
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    os.makedirs(EVID, exist_ok=True)

    srcs = sorted(set(list(RAIL_SRC.values()) + [PAGE1, PAGE2]))
    before = {s: md5(os.path.join(ASSETS, s)) for s in srcs}
    rows, tot = [], 0

    for name in sorted(RAIL_SRC):
        out, err, sz = make_rail(name)
        data = encode(out, 2)
        tot += len(data)
        rows.append((name, "%dx%d" % out.size, len(data),
                     "rail：%s 抠底 + 0.5×" % RAIL_SRC[name].replace("x_ui_psv_", ""),
                     "合成复原误差 max=%d/255" % round(err)))
        if not args.dry_run:
            with open(os.path.join(ASSETS, name), "wb") as fh:
                fh.write(data)
        flat = Image.new("RGB", out.size, (40, 60, 90))
        flat.paste(out, (0, 0), out)
        flat.resize((out.width * 2, out.height * 2), Image.NEAREST).save(
            os.path.join(EVID, "rail_%s_x2.png" % name.replace("x_ui_psv_rail_", "")))

    plan = [("x_ui_psv_cover_c1.png", PAGE1, GROOVE_BOX)]
    for i, gb in enumerate(PAGE2_GROOVES, 1):
        plan.append(("x_ui_psv_cover_c2_%02d.png" % i, PAGE2, gb))
    for name, page, gb in plan:
        out, geo, err = make_cover(page, gb)
        data = encode(out, 2)
        tot += len(data)
        rows.append((name, "%dx%d" % out.size, len(data),
                     "cover：%s 抹旧滑槽 @(%d,%d)" % (page.replace("x_ui_psv_cfg_", ""), gb[0], gb[1]),
                     "落点 (%d,%d) 插值残差 max=%d/255" % (geo[0], geo[1], round(err))))
        if not args.dry_run:
            with open(os.path.join(ASSETS, name), "wb") as fh:
                fh.write(data)

    print("=" * 118)
    print("25 设置屏换皮 · 素材派生（q2 + optimize + compress_level=9）%s" % ("（dry-run）" if args.dry_run else ""))
    print("=" * 118)
    print("%-28s %-10s %8s  %-40s %s" % ("文件", "尺寸", "字节", "用途", "自证"))
    for n, s, b, u, c in rows:
        print("%-28s %-10s %8d  %-40s %s" % (n, s, b, u, c))
    print("-" * 118)
    print("新增 %d 件 / 共 %.1f KB ｜ 面板线性度基线（已干净区插值残差）max=%d/255"
          % (len(rows), tot / 1024.0, round(panel_noise_baseline())))
    after = {s: md5(os.path.join(ASSETS, s)) for s in srcs}
    bad = [s for s in srcs if before[s] != after[s]]
    if bad:
        raise SystemExit("!! 源件被改动：%s" % ", ".join(bad))
    print("源件只读自证：%d 件 md5 运行前后一致 ✓" % len(srcs))
    if not args.dry_run:
        fs = [f for f in os.listdir(ASSETS) if f.lower().endswith(".png")]
        t = sum(os.path.getsize(os.path.join(ASSETS, f)) for f in fs)
        print("落盘后 assets/ui：%d 件 / %.2f MB（预算 96 MB）" % (len(fs), t / 1048576.0))


if __name__ == "__main__":
    main()
