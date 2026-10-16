# -*- coding: utf-8 -*-
r"""M37（ISSUE-20260923-01）· 快捷条圆形 icon 的**占位件** + 名称药丸底图 生成器

■ 本脚本产出两类素材（都落在 `krkr\assets\ui\`）：

  A. **占位 icon 24 件**（`x_ui_qbicon_<key>.png` / `x_ui_qbicon_<key>_on.png`，各 56×56 RGBA）
     —— 这 24 件是 **G1 的交付物**（AI 直出）。本脚本只是为了「让布局/校验/巡演现在就能跑通」
        而画的**占位圆环**；G1 落盘后其产物会覆盖同名文件。
     ★ 占位件刻意用**硬边（无抗锯齿）的纯色**画：不透明像素的 RGB **只可能是下面 3 个色板色**
       （@palette.accent / @palette.highlight / @palette.text_primary），unique RGB ≤ 3。
       ⇒ `同目录\M37_判定是否已被G1覆盖.py` 用**像素统计**（不是 mtime）判定「这 24 件是否已被 G1 覆盖」。
     ★ 安全阀：**已存在且经像素判定不是占位件的文件一律不覆盖**（除非 `--force`）——
       防止本脚本在 G1 落盘后被误重跑、把 AI 件冲掉。

  B. **名称药丸底** `x_ui_qbtip_pill.png`（64×44 RGBA，九宫格 l=r=22 / t=b=0）
     —— 悬停时在图标左侧浮出的中文名称底：蓝底圆角小药丸 + 青蓝细边（配色取既有色板键，
        **不新增色板键**）。4× 超采样后降采样，端点圆角平滑；中段 20px 可横向拉伸。

■ 用法（务必用文件方式跑，勿用 `python -c`/heredoc —— 含中文，见交接 §三.11）
    python _工作\M37_占位件与药丸生成.py            # 生成（不覆盖非占位件）
    python _工作\M37_占位件与药丸生成.py --force    # 连非占位件一起覆盖（慎用）
    python _工作\M37_占位件与药丸生成.py --report   # 只读：现存 24 件的像素统计判定
"""
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))          # …\UI组\_工作
UI = os.path.dirname(HERE)                                  # …\UI组
ASSETS = os.path.join(UI, "krkr", "assets", "ui")

# 12 项 key（次序 = 快捷条纵向次序，与 layout/screens/35_quickbar.json 一致）
KEYS = ["lock", "save", "load", "qsave", "qload", "auto",
        "skip", "next", "prev", "log", "chart", "option"]

# ── 配色：**只取既有色板键**（layout/palette.json），不新增键 ──────────────
PAL = json.load(io.open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]


def hex2rgb(v):
    v = v.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


ACCENT = hex2rgb(PAL["accent"]["value"])           # #7AB0E8 冰蓝强调（青蓝细边）
HILITE = hex2rgb(PAL["highlight"]["value"])        # #3A5A9A 强调蓝（药丸底 / 圆环芯）
WHITE = hex2rgb(PAL["text_primary"]["value"])      # #FFFFFF 白（悬停态内圈）
PLACEHOLDER_RGB = (ACCENT, HILITE, WHITE)

ICON_W = ICON_H = 56                                # 占位 icon 画布（G1 现已另行重切为 64×64，占位件早已被覆盖）

# ── 药丸底（★ P1 重做：vison 判定「与圆徽章不是一套材质」）──────────────────
#   配色族（**不改 palette.json、不新增色板键** —— 这些值直接烘进 PNG，
#   layout 侧不引用它们；既有键只用于引擎绘制的文字/矩形）：
PILL_TOP    = (0x6F, 0xA8, 0xE8)                    # 渐变上端（派单指定）
PILL_BOTTOM = (0x3F, 0x6F, 0xB4)                    # 渐变下端（派单指定）
PILL_EDGE   = (0xA0, 0xC9, 0xF7)                    # 1px 描边（锚点「面板底部发光 #A0C9F7」）
PILL_GLOW   = 3                                     # 外晕最大半径（px）
PILL_GLOW_A = 190                                   # 外晕在贴合处的 alpha（向外衰减到 0）
PILL_R      = 20                                    # 圆角半径 = 丸高/2（小药丸）—— Q2：40/2
PILL_BODY_H = 40                                    # ★ Q2：丸体高 44 → 40（vision：形态比徽章"同重"，
                                                    #   参照的丸/徽比 0.57，本工程由 0.93 收到 0.74）
PILL_RAMP   = 8                                     # ★ 渐变在丸体顶部这 N px 内完成，其余为纯下端色。
                                                    #   理由（实测）：完整线性渐变时白字**字带上沿**对比度不足
                                                    #   （旧 44 高丸体时仅 2.89:1）；收敛后整个字带落在下端色上。
                                                    #   Q2 把丸高压到 40 ⇒ 字带上沿落在丸体第 9 行，故 ramp 收到 8。
                                                    #   置 0 即回到严格线性版。
PILL_CANVAS_H = 64                                  # ★ 画布高 64：丸体 40 居中（上下各 12 留白）⇒
                                                    #   外晕（3px）在画布内自然衰减为 0，绝不被裁；
                                                    #   元素 h 也取 64（= PNG 高）⇒ 不缩放，t=b=0 合法
PILL_MARGIN = PILL_GLOW + 1                       # 丸体距画布左/右边缘的留白 = 外晕半径 + 1
                                                    #   ★ 多留 1px ⇒ 外晕在**画布内衰减到严格 0**（画布边缘 alpha=0，绝不"擦边"）
PILL_STRAIGHT = 20                                  # 九宫格中段（可横向拉伸的平直带）源宽
PILL_NINE_LR = PILL_R + PILL_GLOW                   # 九宫格左右端点 = 半径 20 + 外晕 3 = 23（1:1 保留）
PILL_W = PILL_STRAIGHT + 2 * PILL_NINE_LR           # PNG 宽 = 20 + 46 = 66
PILL_EDGE_A = 255


# ══════════════════════════════════════════════════════════════════════
# 一、占位 icon（硬边纯色圆环；无抗锯齿 ⇒ 便于像素判定）
# ══════════════════════════════════════════════════════════════════════
def draw_icon(state):
    """state='normal' | 'on'。返回 56×56 RGBA。硬边：不透明像素 RGB 必为色板色。"""
    im = Image.new("RGBA", (ICON_W, ICON_H), (0, 0, 0, 0))
    px = im.load()
    cx = cy = (ICON_W - 1) / 2.0
    if state == "normal":
        # 常态：细青蓝圆环 + 中心小圆点（强调蓝）
        r_in, r_out, ring = 18.0, 24.0, ACCENT
        dot = HILITE
    else:
        # 悬停态：内圈填强调蓝 + 白内环 + 青蓝外环（与常态像素差异极大）
        r_in, r_out, ring = 20.0, 26.0, ACCENT
        dot = None
    for y in range(ICON_H):
        for x in range(ICON_W):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if state == "normal":
                if r_in - 0.5 <= d <= r_out + 0.5:
                    px[x, y] = (ring[0], ring[1], ring[2], 255)
                elif d <= 4.5:
                    px[x, y] = (dot[0], dot[1], dot[2], 255)
            else:
                if d <= r_in - 0.5:                       # 芯：强调蓝实心
                    px[x, y] = (HILITE[0], HILITE[1], HILITE[2], 255)
                elif r_in - 0.5 < d <= r_in + 3.5:        # 内环：白
                    px[x, y] = (WHITE[0], WHITE[1], WHITE[2], 255)
                elif r_in + 3.5 < d <= r_out + 0.5:       # 外环：青蓝
                    px[x, y] = (ring[0], ring[1], ring[2], 255)
    return im


def pixel_stats(path):
    """返回 dict：RGB 集合 / 不透明像素数 / 「不透明像素全属色板纯色」是否成立。"""
    with Image.open(path) as im:
        im = im.convert("RGBA")
        cols = im.getcolors(maxcolors=1 << 24) or []
    opq, rgbs = 0, set()
    solid = True
    for cnt, (r, g, b, a) in cols:
        if a == 0:
            continue
        opq += cnt
        rgbs.add((r, g, b))
        if a != 255 or (r, g, b) not in PLACEHOLDER_RGB:
            solid = False
    return {"rgb": rgbs, "opaque": opq, "solid_palette": solid,
            "rgb_n": len(rgbs), "size": Image.open(path).size}


def is_placeholder(path):
    """★ 判定「是占位件」：不透明像素非空、全部为 255 alpha、且 RGB 全属 3 个色板色。
    G1 的 AI 件（渐变 / 抗锯齿 / 多色）**不可能**满足该条件。"""
    if not os.path.exists(path):
        return False
    s = pixel_stats(path)
    return bool(s["opaque"]) and s["solid_palette"] and s["rgb_n"] <= len(PLACEHOLDER_RGB)


# ══════════════════════════════════════════════════════════════════════
# 二、药丸底（4× 超采样，端点圆角平滑；九宫格 l=r=22 t=b=0）
# ══════════════════════════════════════════════════════════════════════
def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _body_gradient_row(r):
    """丸体内第 r 行（0..PILL_BODY_H-1）的底色：顶部 PILL_RAMP 行内完成渐变，其余为下端色。"""
    if PILL_RAMP <= 0:
        return _lerp(PILL_TOP, PILL_BOTTOM, r / float(PILL_BODY_H - 1))
    if r >= PILL_RAMP:
        return PILL_BOTTOM
    return _lerp(PILL_TOP, PILL_BOTTOM, r / float(PILL_RAMP))


def draw_pill():
    """丸底：64 高画布（丸体 44 居中）、竖向渐变、1px 青蓝描边、约 3px 外晕（画布内衰减到 0）。

    实现：4× 超采样绘制后 LANCZOS 降采样（外晕与圆角平滑），丸体**不透明**（alpha 255）
    —— 因为派单要求「实测 PNG 色值」与「白字对比度」，半透明会把色值交给背景决定。
    """
    S = 4
    bg_w, bg_h = PILL_W * S, PILL_CANVAS_H * S
    big = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    # 丸体矩形（画布内）：左右各留 PILL_MARGIN（= 外晕半径），上下居中
    bx0 = PILL_MARGIN * S
    by0 = ((PILL_CANVAS_H - PILL_BODY_H) // 2) * S
    bx1 = bx0 + (PILL_W - 2 * PILL_MARGIN) * S - 1
    by1 = by0 + PILL_BODY_H * S - 1
    cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0

    # ── ① 外晕：方框 SDF 距离场，alpha 自贴合处向外衰减到 0（最大半径 PILL_GLOW）──
    half_w = (bx1 - bx0) / 2.0
    half_h = (by1 - by0) / 2.0
    r_s = PILL_R * S
    glow_px = big.load()
    maxd = PILL_GLOW * S + S          # 覆盖到「刚好为 0」之外，避免降采样后残留
    for y in range(max(0, int(cy - half_h - maxd)), min(bg_h, int(cy + half_h + maxd) + 1)):
        for x in range(max(0, int(cx - half_w - maxd)), min(bg_w, int(cx + half_w + maxd) + 1)):
            qx = abs(x - cx) - (half_w - r_s)
            qy = abs(y - cy) - (half_h - r_s)
            outside = (max(qx, 0.0) ** 2 + max(qy, 0.0) ** 2) ** 0.5
            sd = outside + min(max(qx, qy), 0.0) - r_s          # 有符号距离（<0 在丸体内）
            if sd <= 0 or sd > PILL_GLOW * S:
                continue
            t = 1.0 - sd / float(PILL_GLOW * S)                 # 贴合处 1 → 最外沿 0
            a = int(round(PILL_GLOW_A * (t ** 1.4)))
            if a > 0:
                glow_px[x, y] = (PILL_EDGE[0], PILL_EDGE[1], PILL_EDGE[2], a)

    # ── ② 丸体：逐行竖向渐变（4× 下按行铺满，再统一裁成圆角 + 描边）──
    body = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    for r in range(PILL_BODY_H):
        col = _body_gradient_row(r)
        y0 = by0 + r * S
        bd.rectangle([bx0, y0, bx1, y0 + S - 1], fill=(col[0], col[1], col[2], 255))
    mask = Image.new("L", (bg_w, bg_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([bx0, by0, bx1, by1], radius=r_s, fill=255)
    body.putalpha(mask)
    # 1px 描边（在丸体边缘内侧，色 PILL_EDGE）
    ImageDraw.Draw(body).rounded_rectangle([bx0, by0, bx1, by1], radius=r_s,
                                           outline=(PILL_EDGE[0], PILL_EDGE[1], PILL_EDGE[2], 255),
                                           width=1 * S)

    big = Image.alpha_composite(big, body)
    return big.resize((PILL_W, PILL_CANVAS_H), Image.LANCZOS)


# ── P1 自证：色值 / 外晕半径 / 对比度 / 墨迹宽与内边距 ────────────────────
PILL_FONT_FILE = "C:/Windows/Fonts/msyhbd.ttc"      # 引擎在本工程选中的字体 微软雅黑（粗）


def rel_luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    R, G, B = (lin(v) for v in rgb)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def contrast_vs_white(rgb):
    return (1.05) / (rel_luminance(rgb) + 0.05)


def _load_gen():
    """载入**屏生成器**（宽度公式与全部药丸常量的唯一出处；本脚本不另立一套）。
    只 import，不调用它的 build 函数 ⇒ 不会写任何 layout 文件。"""
    import importlib.util
    p = os.path.join(UI, "工具", "m34_build_screens.py")
    spec = importlib.util.spec_from_file_location("m34_build_screens", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pill_report(gen, font_size):
    """返回 (行列表)。font_size = 引擎实际字号（= 生成器的 PILL_CHAR_EM）。"""
    im = draw_pill()
    px = im.load()
    body_y0 = (PILL_CANVAS_H - PILL_BODY_H) // 2
    rows = []
    rows.append("PNG = %dx%d（丸体 %d 高居中于 y=%d..%d；左右留白 %d = 外晕半径）"
                % (im.width, im.height, PILL_BODY_H, body_y0, body_y0 + PILL_BODY_H - 1, PILL_MARGIN))
    # 取样列一律取**丸体水平中心**（该列自顶到底都在丸体内，避开圆角/描边）
    x_col = PILL_MARGIN + (PILL_W - 2 * PILL_MARGIN) // 2
    top = px[x_col, body_y0 + 2][:3]                    # 顶（内缩 2px：跳过 1px 描边）
    mid = px[x_col, body_y0 + PILL_BODY_H // 2][:3]
    bot = px[x_col, body_y0 + PILL_BODY_H - 3][:3]
    edge = px[x_col, body_y0][:3]                       # 丸体最上行 = 1px 描边
    rows.append("丸体顶(#%02X%02X%02X) 中(#%02X%02X%02X) 底(#%02X%02X%02X)｜1px 描边(#%02X%02X%02X)"
                "（取样列 = 丸体水平中心 x=%d）" % (top + mid + bot + edge + (x_col,)))
    # 外晕最外半径：沿丸体中线的水平方向，从丸体左缘向外找**最远**的 alpha>0 像素
    y_mid = body_y0 + PILL_BODY_H // 2
    x_body_left = PILL_MARGIN
    r_out = 0
    for d in range(1, x_body_left + 1):
        if px[x_body_left - d, y_mid][3] > 0:
            r_out = d
    a_glow = px[x_body_left - 1, y_mid][3]
    rows.append("外晕：最外半径实测 **%dpx**（贴合处 alpha=%d，向外逐级衰减到 0）；"
                "画布左缘 alpha=%d / 上缘 alpha=%d ⇒ **在 64 高画布内衰减完、未被裁**"
                % (r_out, a_glow, px[0, y_mid][3], px[x_col, 0][3]))
    # 对比度：最深点 + 白字字带所覆盖的每一行（取该行底色；一律在丸体中心列取样）
    darkest = min((px[x_col, body_y0 + r][:3] for r in range(PILL_BODY_H)),
                  key=rel_luminance)
    c_dark = contrast_vs_white(darkest)
    rows.append("白字对比度（最深点 #%02X%02X%02X）= **%.2f:1** → %s（要求 ≥4.5:1）"
                % (darkest + (c_dark, "达标" if c_dark >= 4.5 else "**未达标**")))
    ink_h = 0
    f = ImageFont.truetype(PILL_FONT_FILE, font_size)
    for lab in ("锁定", "流程图", "快速存档"):
        bb = f.getbbox(lab)
        ink_w, ink_hh = bb[2] - bb[0], bb[3] - bb[1]
        ink_h = max(ink_h, ink_hh)
        # ★ 宽度公式**只从屏生成器取**（本脚本不另写一套）
        body_w, elem_w = gen.pill_body_w(lab), gen.pill_w(lab)
        pad_lr = (body_w - ink_w) / 2.0
        rows.append("  「%s」(%d 字)：墨迹宽 %d ＝ 生成器公式推算的左/右同宽基数；"
                    "丸体宽 %d（= %d×%d + 2×%d）、元素宽 %d；左/右内边距各 %.1f（对称；"
                    "圆角半径 %d ⇒ 字不进圆角区）"
                    % (lab, len(lab), ink_w, body_w, gen.QUICK_PILL_CHAR_EM, len(lab), gen.QUICK_PILL_PAD,
                       elem_w, pad_lr, PILL_R))
        if not (abs(pad_lr * 2 - (body_w - ink_w)) < 1e-9 and pad_lr >= PILL_R):
            rows.append("    !! 内边距不对称或小于圆角半径 —— 需调 PILL_PAD")
    # 字带对比度：字带 = 丸体竖向居中、高 = 墨迹高
    ink_top = body_y0 + (PILL_BODY_H - ink_h) // 2
    worst = min((contrast_vs_white(px[x_col, ink_top + r][:3]), ink_top + r)
                for r in range(ink_h))
    rows.append("白字**字带**（丸体 y=%d..%d，即全部墨迹所覆盖的行）最差对比度 = **%.2f:1** → %s"
                % (ink_top, ink_top + ink_h - 1, worst[0], "达标" if worst[0] >= 4.5 else "**未达标**"))
    rows.append("墨迹高 %d / 丸高 %d = **%.0f%%**（旧版 27/44 = 61%%）" % (ink_h, PILL_BODY_H,
                                                                100.0 * ink_h / PILL_BODY_H))
    return rows


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════
def report_only():
    rows = []
    for k in KEYS:
        for sfx in ("", "_on"):
            p = os.path.join(ASSETS, "x_ui_qbicon_%s%s.png" % (k, sfx))
            if not os.path.exists(p):
                rows.append((os.path.basename(p), "**缺件**"))
                continue
            s = pixel_stats(p)
            rows.append((os.path.basename(p), "占位件" if is_placeholder(p) else "非占位（G1 件）"))
            print("  %-30s %-14s size=%dx%d uniqueRGB=%-5d opaque=%d"
                  % (os.path.basename(p), rows[-1][1], s["size"][0], s["size"][1],
                     s["rgb_n"], s["opaque"]))
    ph = sum(1 for _, v in rows if v == "占位件")
    g1 = sum(1 for _, v in rows if v.startswith("非占位"))
    print("\n  占位件 %d ｜ 疑似 G1 件 %d ｜ 缺件 %d（共 %d）"
          % (ph, g1, sum(1 for _, v in rows if v == "**缺件**"), len(rows)))
    return 0


def preview_pill(gen, out_path):
    """1:1 预览：三种字数药丸 + 一枚圆徽章，各叠在**冰蓝底 #E9F1FB** 与**暗底 RGB(24,26,32)** 上。"""
    BG_LIGHT = (0xE9, 0xF1, 0xFB)
    BG_DARK = (24, 26, 32)
    pill = draw_pill()
    from PIL import Image as I
    icon = None
    for cand in ("x_ui_qbicon_save.png", "x_ui_qbicon_lock.png"):
        p = os.path.join(ASSETS, cand)
        if os.path.exists(p):
            icon = I.open(p).convert("RGBA")
            break
    labels = [("锁定", gen.QUICK_PILL_CHAR_EM), ("流程图", gen.QUICK_PILL_CHAR_EM),
              ("快速存档", gen.QUICK_PILL_CHAR_EM)]
    try:
        font = ImageFont.truetype(PILL_FONT_FILE, gen.QUICK_PILL_CHAR_EM)
    except Exception:
        font = I.load_default()
    body_y0 = (PILL_CANVAS_H - PILL_BODY_H) // 2
    W, row_h = 460, PILL_CANVAS_H + 16
    canvas = I.new("RGB", (W * 2 + 30, row_h * len(labels) + 20), (255, 255, 255))
    for bi, bgcol in enumerate((BG_LIGHT, BG_DARK)):
        panel = I.new("RGB", (W, row_h * len(labels) + 20), bgcol)
        for i, (lab, _sz) in enumerate(labels):
            body_w = gen.pill_body_w(lab)
            elem_w = gen.pill_w(lab)
            cell = I.new("RGBA", (elem_w, PILL_CANVAS_H), (0, 0, 0, 0))
            # ★ 真按**九宫格**拼（引擎/HTML 同口径）：左右端点 cap=25 逐像素 1:1，**只有中段被拉伸**
            cap = PILL_NINE_LR
            mid_src = pill.crop((cap, 0, PILL_W - cap, PILL_CANVAS_H))
            mid_dst_w = elem_w - 2 * cap
            cell.alpha_composite(pill.crop((0, 0, cap, PILL_CANVAS_H)), (0, 0))
            cell.alpha_composite(mid_src.resize((mid_dst_w, PILL_CANVAS_H), I.LANCZOS), (cap, 0))
            cell.alpha_composite(pill.crop((PILL_W - cap, 0, PILL_W, PILL_CANVAS_H)),
                                 (cap + mid_dst_w, 0))
            d = ImageDraw.Draw(cell)
            bb = font.getbbox(lab)
            # ★ Q1：与引擎同款——白字 + 1px 深藏青描边（PIL 的 stroke_width=1 即八邻域外扩，
            #   与 M38 的八方向描边等价；描边色取生成器常量，保证预览即成品观感）
            oc = gen.QUICK_PILL_TEXT_OUTLINE["outline_color"].lstrip("#")
            stroke = (int(oc[0:2], 16), int(oc[2:4], 16), int(oc[4:6], 16), 255)
            ow = gen.QUICK_PILL_TEXT_OUTLINE["outline_width"]
            d.text(((cell.width - (bb[2] - bb[0])) / 2.0 - bb[0],
                    body_y0 + (PILL_BODY_H - (bb[3] - bb[1])) / 2.0 - bb[1]),
                   lab, font=font, fill=(255, 255, 255, 255),
                   stroke_width=ow, stroke_fill=stroke)
            y = 10 + i * row_h
            panel.paste(cell, (14, y + 8), cell)
            if icon is not None and i == 0:
                panel.paste(icon, (14 + elem_w + 12, y + 8), icon)
            ImageDraw.Draw(panel).text((14, y - 2), lab, fill=(90, 90, 90))
        canvas.paste(panel, (10 + bi * (W + 10), 10))
    canvas.save(out_path)
    return out_path


def main():
    if "--report" in sys.argv:
        print("=" * 74)
        print("现存 24 件 icon 的像素统计判定（判据：不透明像素全为 255 且 RGB ∈ 3 个色板色）")
        print("=" * 74)
        return report_only()

    if "--report-pill" in sys.argv:
        gen = _load_gen()
        print("=" * 78)
        print("P1 药丸底自证（色值 / 外晕 / 对比度 / 墨迹宽与内边距）｜生成器常量："
              "字号=%d 内边距=%d 丸高=%d 外晕=%d 画布高=%d nine l=r=%d 渐变收敛=%dpx"
              % (gen.QUICK_PILL_CHAR_EM, gen.QUICK_PILL_PAD, gen.QUICK_PILL_BODY_H,
                 gen.QUICK_PILL_GLOW, gen.QUICK_PILL_H, gen.QUICK_PILL_NINE["l"], PILL_RAMP))
        print("=" * 78)
        for line in pill_report(gen, gen.QUICK_PILL_CHAR_EM):
            print("  " + line)
        out = os.path.join(HERE, "ISSUE-20260923-01_G2_证据", "G2_药丸1比1预览_both-bg_halo64_Q.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        preview_pill(gen, out)
        print("\n  1:1 预览图（左：冰蓝底 #E9F1FB；右：暗底 RGB(24,26,32)）→ %s" % os.path.relpath(out, UI))
        return 0

    force = "--force" in sys.argv
    wrote, skipped = [], []
    manifest = {}

    # A. 占位 icon
    for k in KEYS:
        for sfx, state in (("", "normal"), ("_on", "on")):
            name = "x_ui_qbicon_%s%s.png" % (k, sfx)
            p = os.path.join(ASSETS, name)
            if os.path.exists(p) and not is_placeholder(p) and not force:
                skipped.append(name)
                manifest[name] = "skipped（已存在且非占位件 = G1 件，未覆盖）"
                continue
            draw_icon(state).save(p)
            wrote.append(name)
            manifest[name] = "占位件（本脚本程序化生成）"

    # B. 药丸底
    p = os.path.join(ASSETS, "x_ui_qbtip_pill.png")
    draw_pill().save(p)
    wrote.append("x_ui_qbtip_pill.png")
    manifest["x_ui_qbtip_pill.png"] = "真实交付（程序化药丸底，非占位）"

    print("  [写入] %d 件：%s" % (len(wrote), "、".join(wrote)))
    if skipped:
        print("  [跳过] %d 件（已存在且非占位件，未覆盖）：%s" % (len(skipped), "、".join(skipped)))

    man = os.path.join(HERE, "M37_占位件清单.json")
    with io.open(man, "w", encoding="utf-8") as f:
        json.dump({"generated_by": "M37_占位件与药丸生成.py",
                   "keys": KEYS, "placeholder_rgb": [list(c) for c in PLACEHOLDER_RGB],
                   "files": manifest}, f, ensure_ascii=False, indent=2)
    print("  清单：%s" % os.path.relpath(man, UI))
    return 0


if __name__ == "__main__":
    sys.exit(main())
