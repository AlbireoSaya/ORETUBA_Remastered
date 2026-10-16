# -*- coding: utf-8 -*-
r"""make_node_variant_a.py —— 流程图三类节点底图「方案 A」正式素材生成器（幂等）

Issue  : ISSUE-20260927-05（流程图节点「类型可区分」配色）
裁决   : 用户 2026-09-27 选定 **方案 A**（同族三档色相 + 选择支加粗描边）
依据   : `UI组\_工作\ISSUE-20260927-05_流程图实现\配色对比.md`（三方案实测 + 裁决）
         `…\复现脚本\mock_node_colors.py`（已批准效果图；本脚本逐字复用其 `recolor` /
          九宫格外的核心思路与 `inner_stroke` 的**环带几何**，见下方「与 mock 的唯一差异」）

输入（**只读**）： UI组\_工作\ISSUE-20260927-05_流程图实现\原形备份\x_ui_node_{section,select,frag}_{off,on}.png
                  （6 件原件，二进制不动；改色一律从备份读，故本脚本可反复执行、结果恒定）
输出（**覆盖**）： UI组\krkr\assets\ui\x_ui_node_{section,select,frag}_{off,on}.png
证据（新出）    ： UI组\_工作\ISSUE-20260927-05_流程图实现\取证\节点素材_方案A_前后对照.png

改色口径（与 mock_node_colors.py 的 SCHEMES["A"] 逐字一致）

    kind      H        S      V倍    描边
    section   218°     0.20   ×1.00  无
    select    200°     0.55   ×0.86  2px 内描边 #2A5490
    frag      268°     0.28   ×1.00  无

  · RGB→HSV，**设定 H/S、乘 V**，**alpha 通道原样保留**；像素尺寸不变。
  · `_off` 与 `_on` 用同一套 H/S/V 基参数（两态原有的明暗差异保留在 V 上）。
  · 描边 = 对「alpha>128」掩码做 MinFilter(5) 形态学腐蚀后相减得到的**内缩 2px 环带**，
    填描边色，画在形状内侧，不改外轮廓、不外扩画布。

_on 提亮档（2026-09-27 追加：悬停反馈修复）
------------------------------------------
问题（主代理实测）：方案 A 把 H/S 覆写后，`section` / `frag` 的两态差被抹平
（不透明区 ΔRGB 均 3.19 / 1.78，最大 7 / 6），而这一屏悬停是主要交互 ⇒ 缺陷。
成因：原件两态主要差在 H/S（`section` off S=0.091 → on S=0.101、V 245→249），覆写 H/S 后差消失。

修法：**只对 `_on` 追加一层乘法提亮，`_off` 一个字节不动**：

    ON_GAIN[kind] = (g, s)      S ← S*s ；V ← V*g   （都在 HSV 域乘、保留原件明暗结构）

| kind | g | s | V 是否有 headroom | 说明 |
| --- | --- | --- | --- | --- |
| section | 1.00 | 0.60 | 无（V≈250/255） | g>1 会把蓝通道大面积顶到 255（实测 g=1.015 → 10% 不透明像素 V=255，g=1.02 → 21%）⇒ g 留 1.00，提亮**走饱和度轴**（降 S ⇒ 最小通道抬升 ⇒ 亮度升） |
| frag | 1.00 | 0.65 | 无（V≈250/255） | 同上 |
| select | 1.04 | 0.95 | **有**（本作 select 的 V 已 ×0.86，V≈214） | 乘 V 不会顶 255 ⇒ 用 V 与 S 双轴提亮 |

> **口径说明**：本作节点底近似「冰蓝霜白」，体区 V 已到 255 的 96–98%，
> 唯一有意义的提亮轴是**降低饱和度**（让最小通道上升）。该轴同样是乘法、同样保住原件的明暗结构，
> 且正是原件两态实际差异所在的轴（off S=0.091 → on S=0.101），只是把幅度放大到肉眼可辨。

提亮后实测（复现主代理读数：掩码=两态 alpha 均 >211；均=逐像素三通道平均差；最大=逐像素单通道最大差）：

| kind | 均（改前 → 改后） | 最大（改前 → 改后） | 验收（均 ≥8 / 最大 ≥20） |
| --- | --- | --- | --- |
| section | 3.34 → 13.69 | 71 → 26 | PASS |
| select | 2.46 → 13.79 | 54 → 103 | PASS |
| frag | 4.26 → 14.08 | 41 → 29 | PASS |

与 mock 的唯一差异（**已如实登记，待主代理裁决**）
------------------------------------------------
mock 的 `inner_stroke()` 用 `out.paste(color, (0,0), ring)`，PIL 的 paste **会连 alpha 一起写**，
把环带 alpha 强制成 255（实测 select_off 1208 个环带像素、均值 207.5、最多被抬 +126）。
本脚本按**本次任务书写明的「alpha 通道原样保留」**实现：环带**只改 RGB**，alpha 由原图逐字节沿用。
差异后果：描边呈「外缘稍柔、内缘实」的 2px 带（环带外 1px 约 5–7 成、内 1px 约 9.6 成），
而不是 mock 的整条不动明。几何（环带位置、宽度、不外扩）与 mock 完全一致。

用法：

    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "/e/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
    python "_工作/ISSUE-20260927-05_流程图实现/复现脚本/make_node_variant_a.py"

退出码：0 = 全部自检通过；1 = 有验收项不通过（并打印明细）。
"""
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont   # noqa: E402

HERE = Path(__file__).resolve()
UI = HERE.parents[3]                     # …\UI组
ASSETS = UI / "krkr" / "assets" / "ui"
ISSUE = UI / "_工作" / "ISSUE-20260927-05_流程图实现"
BACKUP = ISSUE / "原形备份"
EVID = ISSUE / "取证"
SHEET = EVID / "节点素材_方案A_前后对照.png"

SAMPLE = (148, 10)          # 实测 fill 取样点（与 mock 一致）
TOL = 3                     # 取样点容差 ±3/255
STROKE_W = 2                # 描边宽（px，内缩）

# ★ 描边的 alpha 处理（**唯一的实现选择点**，见文件头「与 mock 的唯一差异」）
#   True  = 环带只改 RGB、alpha 沿用原图（**本次任务书写明的「alpha 通道原样保留」＋验收②**）；
#           环带均值 alpha 207.5 ⇒ 描边呈「外缘约 5–7 成、内缘约 9.6 成」的 2px 带。
#   False = 与 mock_node_colors.py 的 inner_stroke() 逐字相同（paste 连 alpha 一起写 ⇒ 环带 alpha
#           被强制为 255，描边整条不透明）。**代价：select 两件的 alpha 通道会变（实测 1208/1209 px、
#           最多 +126）**，验收②将不通过。
STROKE_KEEP_ALPHA = True

# ★ _on 提亮档（只作用于 on 件；见文件头「_on 提亮档」）
#   ON_GAIN[kind] = (g, s) —— S ← S*s、V ← V*g（均在 HSV 域乘，保留原件明暗结构）
ON_GAIN = {
    "section": (1.00, 0.60),   # V 无 headroom ⇒ 只走饱和度轴
    "select":  (1.04, 0.95),   # V 有 headroom（本作 select 的 V 已 ×0.86）⇒ V+S 双轴
    "frag":    (1.00, 0.65),   # V 无 headroom ⇒ 只走饱和度轴
}

# 态差验收口径（复现主代理读数）：掩码 = 两态 alpha 均 > 该阈值
#   mean = 逐像素 (|ΔR|+|ΔG|+|ΔB|)/3 的均值 ；max = 逐像素 max(|ΔR|,|ΔG|,|ΔB|) 的最大
STATE_THR = 211
STATE_MEAN_MIN = 8.0
STATE_MAX_MIN = 20

# kind -> (H, S, V倍, 描边色 or None)
SPEC = {
    "section": (218, 0.20, 1.00, None),
    "select":  (200, 0.55, 0.86, (42, 84, 144)),   # #2A5490
    "frag":    (268, 0.28, 1.00, None),
}
STATES = ("off", "on")
KINDS = ("section", "select", "frag")
KIND_CN = {"section": "章节点", "select": "选择支节点", "frag": "番外节点"}

# _off 的期望 fill（裁决书列出的实测值，带 ±TOL 容差）；_on 只如实报实测
EXPECT_OFF = {"section": (0xC4, 0xD6, 0xF5), "select": (0x60, 0xAD, 0xD5), "frag": (0xD1, 0xB1, 0xF5)}

BG = (24, 31, 46)           # 对照图底色（与实际流程图底色同量级）
FG = (232, 238, 246)
FG_DIM = (168, 180, 196)
HL = (255, 214, 140)
OK = (140, 214, 160)
BAD = (240, 130, 130)

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/msyhbd.ttc", 0), ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0), ("C:/Windows/Fonts/simsun.ttc", 0),
]
_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _fc:
        return _fc[key]
    cand = ([c for c in FONT_CANDIDATES if "bd" in c[0]] + FONT_CANDIDATES) if bold else FONT_CANDIDATES
    f = None
    for path, idx in cand:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size, index=idx)
                break
            except Exception:
                continue
    if f is None:
        f = ImageFont.load_default()
    _fc[key] = f
    return f


# ---------------------------------------------------------------- 改色 / 描边
def recolor(img, hue=None, sat=None, vmul=None):
    """（与 mock_node_colors.py 逐字一致）设 H/S、乘 V；保留原件 V 与 alpha。"""
    r, g, b, a = img.split()
    H, S, V = Image.merge("RGB", (r, g, b)).convert("HSV").split()
    if hue is not None:
        H = H.point(lambda _p: int(round(hue / 360.0 * 255)) & 0xFF)
    if sat is not None:
        S = S.point(lambda p: max(0, min(255, int(round(sat * 255)))))
    if vmul is not None:
        V = V.point(lambda p: max(0, min(255, int(round(p * vmul)))))
    rgb = Image.merge("HSV", (H, S, V)).convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), a))


def inner_stroke(img, color, width):
    """内缩 width px 的环带描边（环带几何与 mock 一致）。

    STROKE_KEEP_ALPHA=True（默认）：只改 RGB，alpha 原样保留。
    STROKE_KEEP_ALPHA=False       ：与 mock 逐字相同（paste 连 alpha 一起写，环带 alpha→255）。
    """
    a = img.getchannel("A")
    mask = a.point(lambda p: 255 if p > 128 else 0)
    ring = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(width * 2 + 1)))
    rgb = img.convert("RGB")
    rgb.paste(Image.new("RGB", img.size, color), (0, 0), ring)
    if STROKE_KEEP_ALPHA:
        return Image.merge("RGBA", (*rgb.split(), a))   # ← alpha 逐字节沿用原图
    out = img.copy()                                     # ← mock 逐字行为
    out.paste(Image.new("RGBA", img.size, color + (255,)), (0, 0), ring)
    return out


def build(kind, state):
    """从 原形备份 读原件 → 改色（on 件另乘提亮档；select 另加描边）→ 返回 RGBA。

    不读 krkr 侧，故幂等；`_off` 的路径与提亮档无关 ⇒ 输出与上一版逐字节相同。
    """
    src = Image.open(BACKUP / f"x_ui_node_{kind}_{state}.png").convert("RGBA")
    hue, sat, vmul, stroke = SPEC[kind]
    if state == "on":
        g, s = ON_GAIN[kind]
        sat, vmul = sat * s, vmul * g
    out = recolor(src, hue=hue, sat=sat, vmul=vmul)
    if stroke:
        out = inner_stroke(out, stroke, STROKE_W)
    return src, out


def state_delta(off_img, on_img, thr=STATE_THR):
    """两态差：掩码 = 两态 alpha 均 > thr；返回 (mean(逐像素三通道均差), max(逐像素单通道最大差), n)。"""
    po, pn = off_img.load(), on_img.load()
    W, H = off_img.size
    a3, mx = [], []
    for y in range(H):
        for x in range(W):
            r, g, b, a = po[x, y]
            r2, g2, b2, a2 = pn[x, y]
            if a > thr and a2 > thr:
                dr, dg, db = abs(r - r2), abs(g - g2), abs(b - b2)
                a3.append((dr + dg + db) / 3.0)
                mx.append(max(dr, dg, db))
    if not a3:
        return 0.0, 0, 0
    return sum(a3) / len(a3), max(mx), len(a3)


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def md5_file(p):
    return md5_bytes(Path(p).read_bytes())


def hexof(rgb):
    return "#%02X%02X%02X" % rgb


# ---------------------------------------------------------------- 主流程
def main():
    if not BACKUP.is_dir():
        print("FATAL: 缺 原形备份 目录:", BACKUP)
        return 1
    EVID.mkdir(parents=True, exist_ok=True)

    before = {}      # (kind,state) -> dict
    fails = []

    for kind in KINDS:
        for state in STATES:
            key = (kind, state)
            fn = f"x_ui_node_{kind}_{state}.png"
            src, out = build(kind, state)

            # 保存（RGBA 真彩、不做调色板量化）
            dst = ASSETS / fn
            out.save(dst, optimize=True, compress_level=9)

            m0 = md5_file(BACKUP / fn)
            m1 = md5_file(dst)
            a0 = src.getchannel("A").tobytes()
            a1 = Image.open(dst).convert("RGBA").getchannel("A").tobytes()
            before[key] = {
                "fn": fn, "src": src, "out": Image.open(dst).convert("RGBA"),
                "m0": m0, "m1": m1,
                "size": (src.size, Image.open(dst).size),
                "a0_md5": md5_bytes(a0), "a1_md5": md5_bytes(a1),
                "alpha_same": a0 == a1,
                "fill0": src.convert("RGB").getpixel(SAMPLE),
                "fill1": Image.open(dst).convert("RGB").getpixel(SAMPLE),
            }

    # ---------------- 自检 ----------------
    print("=" * 78)
    print("自检 ① 像素尺寸（应与原件一致）")
    for key, d in before.items():
        ok = d["size"][0] == d["size"][1]
        if not ok:
            fails.append(f"{d['fn']} 尺寸变化 {d['size']}")
        print("   %-32s %s -> %s  %s" % (d["fn"], d["size"][0], d["size"][1], "OK" if ok else "FAIL"))

    print("自检 ② alpha 通道（逐件与原件比对）")
    for key, d in before.items():
        ok = d["alpha_same"]
        if not ok:
            fails.append(f"{d['fn']} alpha 变化")
        print("   %-32s md5 %s -> %s  %s"
              % (d["fn"], d["a0_md5"][:16], d["a1_md5"][:16], "OK(逐字节一致)" if ok else "FAIL"))

    print("自检 ③ _off 与 _on 仍不同（状态区分力）")
    for kind in KINDS:
        mo = before[(kind, "off")]["m1"]
        mn = before[(kind, "on")]["m1"]
        ok = mo != mn
        if not ok:
            fails.append(f"{kind}: off==on")
        print("   %-10s off %s / on %s  %s" % (kind, mo[:12], mn[:12], "OK(不同)" if ok else "FAIL(退化成同图)"))

    print("自检 ④ 实测 fill 色 @ %s（容差 ±%d，仅 _off 有期望值）" % (str(SAMPLE), TOL))
    for kind in KINDS:
        for state in STATES:
            d = before[(kind, state)]
            line = "   %-10s %-3s %s -> %s" % (kind, state, hexof(d["fill0"]), hexof(d["fill1"]))
            if state == "off":
                e = EXPECT_OFF[kind]
                dd = max(abs(e[i] - d["fill1"][i]) for i in range(3))
                if dd > TOL:
                    fails.append(f"{kind}_off fill 偏差 {dd}")
                line += "  期望 %s 偏差 %d/255  %s" % (hexof(e), dd, "OK" if dd <= TOL else "FAIL")
            print(line)

    print("自检 ⑤ 改后 md5 六件全部变化")
    for key, d in before.items():
        ok = d["m0"] != d["m1"]
        if not ok:
            fails.append(f"{d['fn']} md5 未变")
        print("   %-32s %s -> %s  %s" % (d["fn"], d["m0"][:12], d["m1"][:12], "OK(已变)" if ok else "FAIL(未变)"))

    print("自检 ⑥ 两态差 ΔRGB（掩码：两态 alpha 均 >%d；均=逐像素三通道均差，最大=逐像素单通道最大差）"
          % STATE_THR)
    for kind in KINDS:
        o_src = before[(kind, "off")]["src"]      # 原件 _off（原形备份）
        n_src = before[(kind, "on")]["src"]       # 原件 _on（原形备份）
        o_new = before[(kind, "off")]["out"]      # 改后 _off（未受提亮档影响）
        n_new = before[(kind, "on")]["out"]       # 改后 _on
        m0, x0, c0 = state_delta(o_src, n_src)
        m1, x1, c1 = state_delta(o_new, n_new)
        ok = (m1 >= STATE_MEAN_MIN) and (x1 >= STATE_MAX_MIN)
        if not ok:
            fails.append("%s 两态差不足 均=%.2f 最大=%d" % (kind, m1, x1))
        print("   %-8s n=%5d  改前 %6.2f / %3d  →  改后 %6.2f / %3d   目标 均≥%.0f 且 最大≥%d  %s"
              % (kind, c1, m0, x0, m1, x1, STATE_MEAN_MIN, STATE_MAX_MIN, "OK" if ok else "FAIL"))
        before[(kind, "off")]["delta"] = (m0, x0, m1, x1)
        # V(单通道) 顶到 255 的像素占比（防过曝自证：g 会让亮底死白）
        pn = n_new.load()
        W, H = n_new.size
        tot = sum(1 for y in range(H) for x in range(W) if pn[x, y][3] > STATE_THR)
        sat255 = sum(1 for y in range(H) for x in range(W)
                     if pn[x, y][3] > STATE_THR and max(pn[x, y][:3]) == 255)
        print("            _on 不透明区单通道==255 的像素：%d/%d (%.2f%%)" % (sat255, tot, 100.0 * sat255 / max(tot, 1)))

    # ---------------- 对照图 ----------------
    make_sheet(before)
    print("对照图：", SHEET)

    print("=" * 78)
    if fails:
        print("结果：**不通过** %d 项" % len(fails))
        for f in fails:
            print("   -", f)
        return 1
    print("结果：**全部自检通过**")
    return 0


# ---------------------------------------------------------------- 对照图
def make_sheet(before):
    order = [(k, s) for k in KINDS for s in STATES]
    gap = 22
    margin = 22
    widths = [before[key]["src"].size[0] for key in order]
    total_w = margin * 2 + sum(widths) + gap * (len(order) - 1)
    col_h = max(before[key]["src"].size[1] for key in order)

    head_h = 78                      # 列头（类别 + 状态 + 文件名）
    band_title_h = 34                # 「改前 / 改后」带标题
    fill_h = 28                      # 每列下方的实测色值
    title_h = 76
    zoom_h = 0
    zoom_src = None
    for key in order:
        if key[0] == "select":
            zoom_src = key
            break
    zone = None
    if zoom_src:
        zone = before[zoom_src]
        zcrop = (0, 18, 46, 47)      # select 左边中段：含描边区
        zw, zh = zcrop[2] - zcrop[0], zcrop[3] - zcrop[1]
        zoom_scale = 5
        zoom_h = zh * zoom_scale + 72

    row_h = 96                        # 「态差对照」每类一行
    state_h = 62 + 3 * row_h + 30

    H = title_h + head_h + (band_title_h + col_h + fill_h + 26) * 2 + zoom_h + state_h + margin
    sheet = Image.new("RGB", (total_w, H), BG)
    d = ImageDraw.Draw(sheet)

    f_title = font(30, True)
    f_h = font(22, True)
    f_col = font(17)
    f_colb = font(17, True)
    f_note = font(16)

    y = margin
    d.text((margin, y), "流程图节点素材 · 方案 A · 前后对照（1:1 原始像素）", font=f_title, fill=FG)
    d.text((margin, y + 38),
           "取样点 %s（容差 ±%d/255）｜ 底色 %s（与实际流程图同量级）｜ 改前取自 原形备份\\ 原件"
           % (str(SAMPLE), TOL, str(BG)),
           font=f_note, fill=FG_DIM)
    y += title_h

    # 列头
    xs = []
    x = margin
    for i, key in enumerate(order):
        d_ = before[key]
        w = widths[i]
        xs.append(x)
        d.text((x, y), "%s · %s" % (KIND_CN[key[0]], key[1]), font=f_colb, fill=FG)
        d.text((x, y + 22), d_["fn"], font=f_col, fill=FG_DIM)
        x += w + gap
    y += head_h

    def band(label, sub, pick, y0):
        d.text((margin, y0), label, font=f_h, fill=HL)
        d.text((margin + ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(label, font=f_h) + 14, y0 + 4),
               sub, font=f_note, fill=FG_DIM)
        yy = y0 + band_title_h
        for i, key in enumerate(order):
            im = before[key][pick]
            sheet.paste(im, (xs[i], yy), im)
            d.rectangle([xs[i] - 1, yy - 1, xs[i] + im.size[0], yy + im.size[1]], outline=(70, 84, 104))
            col = before[key]["fill0" if pick == "src" else "fill1"]
            d.text((xs[i], yy + col_h + 6), hexof(col), font=f_col, fill=FG if pick != "src" else FG_DIM)
        return yy + col_h + fill_h + 26

    y = band("改前（原形备份 \\ 原件）", "三类几乎同色，肉眼不可辨", "src", y)
    y = band("改后（方案 A：设 H/S · 乘 V ＋ 选择支 2px 深蓝内描边）",
             "冰蓝实底 / 偏青蓝 + 描边 / 淡紫底", "out", y)

    # 描边放大带（5× 最近邻，只为看清 2px 描边）
    if zoom_src:
        d_ = zone
        d.text((margin, y), "描边放大（5× 最近邻，%s 左边中段）" % d_["fn"], font=f_h, fill=HL)
        y += 34
        zw = 46
        zh = 29
        for j, (lab, pick) in enumerate((("改前", "src"), ("改后", "out"))):
            src = before[zoom_src][pick]
            crop = src.crop((0, 18, 46, 47)).resize((zw * 5, zh * 5), Image.NEAREST)
            xx = margin + j * (zw * 5 + 40)
            sheet.paste(crop, (xx, y), crop)
            d.text((xx, y + zh * 5 + 6), lab, font=f_colb, fill=FG)
        y += zh * 5 + 40

    # ---- 态差对照（每类一行：左 _off 右 _on 1:1 并排，标出 ΔRGB 均/最大） ----
    d.text((margin, y), "态差对照（改后）· 悬停反馈必须有差别", font=f_h, fill=HL)
    d.text((margin, y + 30),
           "ΔRGB 掩码 = 两态 alpha 均 >%d ｜ 均 = 逐像素三通道均差 ｜ 最大 = 逐像素单通道最大差 ｜ 目标 均≥%.0f 且 最大≥%d"
           % (STATE_THR, STATE_MEAN_MIN, STATE_MAX_MIN), font=f_note, fill=FG_DIM)
    y += 62
    LW, CW, AW = 150, 292, 46
    x_off = margin + LW
    x_on = x_off + CW + AW
    for kind in KINDS:
        o = before[(kind, "off")]["out"]
        n = before[(kind, "on")]["out"]
        m0, x0, m1, x1 = before[(kind, "off")]["delta"]
        d.text((margin, y + 18), "%s · %s" % (KIND_CN[kind], kind), font=f_colb, fill=FG)
        for xx, im in ((x_off, o), (x_on, n)):
            sheet.paste(im, (xx, y), im)
            d.rectangle([xx - 1, y - 1, xx + im.size[0], y + im.size[1]], outline=(70, 84, 104))
        d.text((x_off, y + o.size[1] + 5), "_off（常态，未改）", font=f_col, fill=FG_DIM)
        d.text((x_on, y + n.size[1] + 5), "_on（悬停，已提亮）", font=f_col, fill=FG_DIM)
        d.text((x_off + o.size[0] + 8, y + 22), "→", font=f_h, fill=HL)
        d.text((x_on + n.size[0] + 22, y + 12),
               "ΔRGB 均 %.2f / 最大 %d" % (m1, x1), font=f_colb, fill=OK)
        d.text((x_on + n.size[0] + 22, y + 34),
               "(改前 %.2f / %d)" % (m0, x0), font=f_col, fill=FG_DIM)
        y += row_h

    sheet.save(SHEET)
    print("   对照图写出：%s  %s" % (SHEET, sheet.size))


if __name__ == "__main__":
    sys.exit(main())
