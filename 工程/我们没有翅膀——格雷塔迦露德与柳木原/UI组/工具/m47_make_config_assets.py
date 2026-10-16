# -*- coding: utf-8 -*-
r"""M47 · 设置（config）屏重设 · W1 素材模块 —— 程序化生成 20 件 UI 素材

Issue : ISSUE-20260924-01（设置屏重设 · 素材模块 W1）
方案  : `_工作\M47_设置屏重设方案.md` §二 素材清单（**接口冻结书**）

■■ 这是一次性脚手架（跑一次就够）
    · 本脚本**只产出 PNG、绝不写任何 JSON**；落盘后
      **`layout\screens\25_config.json` 才是真相源**（元素几何 / 九宫格 / z / 动作全在那边）。
    · 因此**重跑本脚本不会回退任何用户或数据侧的改动**（不碰 JSON、不碰 .tjs/.js）。
    · 幂等：同一版本脚本重跑逐字节一致（无随机、无时间戳）。PIL + 本地字体轮廓绘制，
      **不联网、不用 AI 生图、不复制任何原版/参考作的像素**。

■ 产出的 20 件（`krkr\assets\ui\`，文件名与尺寸严格照冻结书 §二 表）
    ┌ 九宫格件（**必须是 RGBA，圆角外真透明 α=0**；中心区可无痕拉伸）
    │ frame          96×96   l24 t24 r24 b24   巨型外框（2px 细边 + 圆角 20 + 8px 柔外发光，内近全透明）
    │ page_strip     64×64   l20 t20 r20 b20   页签条底（磨砂白 12% + 下沿 2px 冰蓝线）
    │ tab_on        120×50   l25 t0  r25 b0    选中页签（accent→霜白 横向渐变胶囊）
    │ tab_off       120×50   l25 t0  r25 b0    未选中（全透明 + 极小圆角痕）
    │ opt_off        80×40   l14 t6  r14 b6    值按钮未选底（**全透明**，照冻结书语义）
    │ opt_on         80×40   l14 t6  r14 b6    值按钮选中底（同 tab_on 渐变、降饱和 10%）
    │ opt_over       80×40   l14 t6  r14 b6    悬停（胶囊 + 1px 高光边）
    │ btn            80×40   l16 t8  r16 b8    通用小按钮（磨砂白 10% + 2px 细边 + 圆角 10）
    │ btn_over       80×40   l16 t8  r16 b8    悬停（填充 20% + 边发光）
    │ name_sel       80×43   l16 t0  r16 b0    选中角色名胶囊（highlight × highlight_opa，圆角 8）
    │ preview_frame  96×96   l24 t24 r24 b24   预览框/角色横幅框（细边 + 半透磨砂底）
    └ 1:1 件（**无 nine**，元素 w/h 必须等于 PNG 实尺寸）
      rail          364×11              滑块轨道（panel_edge 60% 圆角线，4px 粗居中）
      knob           29×29              手柄常态（霜白圆 + 2px 冰蓝环 + 外发光）
      knob_over      29×29              手柄悬停（环加粗为 accent 实色）
      chk_off        21×21              空方框（2px panel_edge 圆角 3）
      chk_on         21×21              勾选（方框 + accent 勾）
      dot            12×12              列表圆点（accent 实心圆）
      spk            22×32              喇叭图标（方体 + 三角 + 两道弧，text_menu 色）
      preview_bg    612×154             预览示例画面（**程序化**冰蓝渐变 + 示意色带/几何块）
      preview_mask  612×154             预览遮罩（**与对话框遮罩同口径**：α = 255·t 线性）

■ 配色：**一律取自 `layout\palette.json`**（唯一色值来源；本脚本运行时读它，不在代码里另起色号）。
   用到的键：panel_edge / panel_edge_opa / accent / highlight / highlight_opa / panel_fill / text_menu。
   少数**合成色**（霜白、界面暗底）在下方以 `# 合成色（推导自 …）` 标注推导来源，不引入新色号。

■ 关键工程学（为什么这样画才不会被九宫格拉伸弄坏）
   引擎侧九宫格实现见 `krkr\game\ui_widget.tjs:144 uiWidgetNine()`：九个块分别
   `operateStretch(...)`，**中段是「拉伸」不是「平铺」**，且滤镜为 **stNearest**。故：
     · 中段（中心 cell）必须**纯色或纯透明**；本脚本对每个九宫格件做程序化自证（见 main 的 [2]/[3]）。
     · 横向渐变的件（tab_on / opt_on / opt_over）**必须逐行完全相同**（纵向均匀），
       这样纵向拉伸是逐像素复制、横向拉伸只把平滑渐变轻微拉长，不会出现接缝。
     · 圆角/描边等细节一律落在 nine 边带内（已按各件边带宽度选半径，见各 build 函数注释）。

■ 运行
    python 工具\m47_make_config_assets.py
    （退出码 0 = 20 件全部写出且全部自证通过；打印每件的文件名 / 尺寸 / 模式 / 字节数 + 合计）
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))                 # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                                  # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")

# ──────────────────────────────────────────────────────────────── 调色板
def load_palette(path=PALETTE):
    """读 layout/palette.json（唯一色值来源）。缺键即报错，**不做静默回落**。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)["colors"]


PAL = load_palette()


def C(key):
    """@palette.<key> 的 #RRGGBB → (r,g,b)"""
    return hex2rgb(PAL[key]["value"])


def OPA(key):
    """@palette.<key> 的 0–255 不透明度"""
    return int(PAL[key]["value"])


# 合成色（palette.json 无此键，推导来源已注明；不新增独立色号）
FROST = (244, 248, 255)      # 合成色（推导自 @palette.accent 向白 78%）：霜白，用于胶囊/手柄高光
INK_HI = (26, 36, 60)        # 合成色（推导自 @palette.panel_fill 提亮 12%）：预览底图渐变上端


# ──────────────────────────────────────────────────────────────── 基础工具
def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def mix(a, b, t):
    """线性混色：t=0 → a，t=1 → b"""
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def desat(rgb, amount):
    """降饱和：向同亮度灰混合 amount（0..1）"""
    g = int(round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]))
    return mix(rgb, (g, g, g), amount)


def tint(alpha_mask, rgb, alpha=255):
    """L 掩膜 + 颜色 → RGBA（掩膜值 × alpha/255）"""
    m = alpha_mask
    if alpha != 255:
        m = m.point(lambda v: v * alpha // 255)
    im = Image.new("RGBA", m.size, tuple(rgb) + (0,))
    im.putalpha(m)
    return im


def aa(size, draw_fn, scale=4):
    """超采样画掩膜：在 scale 倍画布上绘制后 LANCZOS 降采样（纯程序化抗锯齿，无噪声）"""
    w, h = size
    m = Image.new("L", (w * scale, h * scale), 0)
    draw_fn(ImageDraw.Draw(m), scale)
    return m.resize((w, h), Image.LANCZOS)


def rr_mask(size, box, radius, scale=4):
    """圆角矩形掩膜。

    ★ **box 采用半开区间语义**（far edge 为独占边界）：实心铺满整张图写 `(0, 0, W, H)`，
      内缩 8px 写 `(8, 8, W-8, H-8)`。
      原因（实测得到的教训）：若按「包含末像素」写成 `(0,0,W-1,H-1)`，SSAA 降采样后
      **最后一行/列只有 25% 覆盖率**（该行 3/4 的采样点在形状外）——
      对九宫格件就是「末行淡成一格」或顶底不对称（实测 name_sel 末行 α=0、tab 顶行满底行淡）。
      半开区间写法则顶底/左右对称，且形状边界处的覆盖率在数学上精确。
    """
    def _d(d, s):
        d.rounded_rectangle([v * s for v in box], radius=radius * s, fill=255)
    return aa(size, _d, scale)


def circ_mask(size, cx, cy, r, scale=4):
    def _d(d, s):
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255)
    return aa(size, _d, scale)


def glow_of(mask, sigma, gain):
    """柔发光：高斯模糊 + 强度衰减（纯函数，无随机）"""
    g = mask.filter(ImageFilter.GaussianBlur(sigma))
    return g.point(lambda v: min(255, int(v * gain)))


def clip_low_alpha(img, thr=3):
    """把 α≤thr 的抗锯齿残影归零 —— **圆角/圆弧外必须是 α=0**（本工作区血泪教训：
    棋盘格/白底被烘焙进像素；此处反向：宁可硬一点也不能留 1–3 级残影）。
    3/255 = 1.2%，肉眼不可见，但能让「圆角外真透明」成为**逐像素可验证**的事实。
    ⚠️ **不用于 preview_mask**（它的 α 剖面必须逐行等于 round(255·y/(H-1))，含 1、2、3 级）。"""
    a = img.getchannel("A").point(lambda v: 0 if v <= thr else v)
    out = img.copy()
    out.putalpha(a)
    return out


def hgrad(size, stops, alpha):
    """**逐行相同**的横向渐变 RGBA（stops=[(pos0..1,(r,g,b)), ...] 按位置升序）。

    刻意先造 1 行再 NEAREST 纵向放大 ⇒ 数学上保证「逐行完全相同」，
    这正是九宫格横向拉伸（t=b=0 的件）与纵向拉伸都不出接缝的前提。
    """
    w, h = size
    row = Image.new("RGBA", (w, 1))
    px = row.load()
    for x in range(w):
        t = x / float(w - 1) if w > 1 else 0.0
        rgb = stops[0][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                rgb = mix(c0, c1, k)
                break
            rgb = c1
        px[x, 0] = tuple(rgb) + (alpha,)
    return row.resize((w, h), Image.NEAREST)


# ──────────────────────────────────────────────────────────────── 各件生成
def build_frame():
    """x_ui_cfg_frame.png 96×96 · nine l24 t24 r24 b24 —— 「总体巨型方框」

    2px @palette.panel_edge 细边（圆角 20）+ 8px 柔外发光；**内近全透明**。
    安全性：内缩 8px 给外发光留位置；边带 24px 内才有像素（下方用闸门强制，
    中心 48×48 保证恒为 α=0）。描边与发光都只随 y 变化 ⇒ 横向拉伸无痕。
    """
    W = H = 96
    INSET, RAD, BW = 8.0, 20.0, 2.0
    edge = C("panel_edge") * 1
    edge_a = OPA("panel_edge_opa")

    outer = rr_mask((W, H), (INSET, INSET, W - INSET, H - INSET), RAD)
    inner = rr_mask((W, H), (INSET + BW, INSET + BW, W - INSET - BW, H - INSET - BW), RAD - BW)
    ring = ImageChops.subtract(outer, inner)                       # 2px 环

    glow = glow_of(ring, 3.1, 0.62)                                # 8px 柔外发光
    alpha = ImageChops.lighter(ring, glow)
    # 闸门：**只允许 nine 边带（24px）内有像素**（含描边与发光），中心 48×48 及其内侧一律 0
    gate = ImageChops.invert(rr_mask((W, H), (24, 24, W - 24, H - 24), 8.0))
    alpha = ImageChops.multiply(alpha, gate)

    img = tint(alpha, edge, edge_a)
    return img


def build_page_strip():
    """x_ui_cfg_page_strip.png 64×64 · nine l20 t20 r20 b20 —— 页签条底

    磨砂白 12% 圆角填充（圆角 10 < 边带 20）+ 下沿 2px @palette.accent 冰蓝线。
    安全区：中心 24×24 只有均一的 12% 填充（无渐变、无圆弧）⇒ 横纵拉伸均无痕；
    冰蓝线落在下边带（行 60..61 ∈ 44..63）⇒ 纵向不被拉伸、横向被拉伸成整条线。
    """
    W = H = 64
    RAD = 10.0
    base = rr_mask((W, H), (1, 1, W - 1, H - 1), RAD)
    img = tint(base, FROST, 31)                                    # 磨砂白 12%（255×0.12≈31）

    line = Image.new("L", (W, H), 0)
    ImageDraw.Draw(line).rectangle([0, 60, W, 62], fill=255)
    line = ImageChops.multiply(line, base)                          # 被圆角裁掉两端
    return Image.alpha_composite(img, tint(line, C("accent")))


def _capsule_grad(size, stops, alpha, radius=None, inset_x=0.0, snap_nine=None):
    """圆角/胶囊底 + 横向渐变（**纵向必须为 0 内缩**：见下方说明）。

    纵向内缩刻意取 0（box 的 y 从 0 到 H-1）：
      t=b=0 的件（tab_* / name_sel）整高都是中段，若纵向留 0.75px 内缩，
      顶/底行会变成**半透明的那一行**（实测 α 只有 240 的 65/255），
      既破坏「中段逐行相同」，也会在实机顶部出现一条淡边。
      形状顶边落在 y=0 ⇒ 顶行于直边段被 100% 覆盖，只有圆角处（角块内）才有抗锯齿。

    snap_nine：给出 nine 边距时，把**九宫格中段（中心 cell）整块掩膜钉成 255**
      —— 胶囊的端帽与直边在 x = l 处相切，抗锯齿会在该列留下 99.5% 覆盖率
      （≈1 级 α），正是「中段必须可无痕拉伸」的最后一根刺；钉满即把该列变成精确的
      100%，改动量 <1 级 α（不可见），但让**九宫格安全区成为可逐像素验证的事实**。
    """
    W, H = size
    rad = ((H - 1) / 2.0) if radius is None else radius
    m = rr_mask(size, (inset_x, 0, W - inset_x, H), rad)
    if snap_nine:
        m.paste(255, (snap_nine["l"], snap_nine["t"], W - snap_nine["r"], H - snap_nine["b"]))
    g = hgrad(size, stops, alpha)
    g.putalpha(ImageChops.multiply(g.getchannel("A"), m))
    return g


def build_tab_on():
    """x_ui_cfg_tab_on.png 120×50 · nine l25 t0 r25 b0 —— 选中页签胶囊

    @palette.accent → 霜白 的横向渐变胶囊（半径 24.5 = (H-1)/2，正胶囊；前 62% 保持
    accent 不提前冲淡，末段才收到霜白）。
    t=b=0 ⇒ 整高都是中段：**必须逐行相同**（hgrad 保证纵向为逐像素复制；
    形状顶边落在 y=0 保证顶/底行不是半透明行），纵向拉伸即复制；
    横向只有中段 70px 被拉伸（左/右 25px 为端帽），nearest 拉伸平滑渐变无可见台阶。
    """
    return _capsule_grad((120, 50), [(0.0, C("accent")), (0.62, C("accent")), (1.0, FROST)], 240,
                         snap_nine=dict(l=25, t=0, r=25, b=0))


def build_tab_off():
    """x_ui_cfg_tab_off.png 120×50 · nine l25 t0 r25 b0 —— 未选中页签（全透明 + 极小圆角痕）

    冻结书 §二：「全透明（只有极小圆角痕），文字靠 text 元素调 @palette.text_menu」。
    圆角外 α=0；仅剩 1px 胶囊轮廓作为「痕」（峰值 α≈13，见自证打印）。
    中段逐行沿 x 恒定 ⇒ 横纵拉伸都不产生接缝。
    """
    W, H = 120, 50
    outer = rr_mask((W, H), (0, 0, W, H), H / 2.0)
    inner = rr_mask((W, H), (1, 1, W - 1, H - 1), (H - 2) / 2.0)
    ring = ImageChops.subtract(outer, inner)
    return tint(ring, C("text_menu"), 26)


def build_rail():
    """x_ui_cfg_rail.png 364×11 —— 滑块轨道（无 nine，元素 w/h 必须 = 364×11）

    @palette.panel_edge 60% 圆角线：4px 粗、居中（行心 y=5.5）、两端圆角。
    参照原作 r005（364×11，线体仅 3px、居中）⇒ 取 4px 细节层级；元素按中心线绘制。
    """
    W, H = 364, 11
    m = rr_mask((W, H), (0.0, 3.5, W, 7.5), 2.0)
    return tint(m, C("panel_edge"), int(round(255 * 0.60)))         # 60% = 153


def build_knob(over=False):
    """x_ui_cfg_knob[_over].png 29×29 —— 滑块手柄（无 nine，1:1）

    常态：霜白圆 + 2px @palette.accent 冰蓝环 + 外发光。
    悬停：环加粗为 3px @palette.accent 实色 + 更强的外发光。
    外发光在 r=14.5（画布内切圆）处衰减到 0 ⇒ 圆外四角真透明、边缘无硬切。
    """
    W = H = 29
    cx = cy = 14.5
    r_fill = 10.5
    r_ring_out = 12.5 if not over else 13.5
    ring_a = 235 if not over else 255
    fill_a = 245 if not over else 255
    gain = 0.42 if not over else 0.58

    disc = circ_mask((W, H), cx, cy, r_ring_out)
    glow = glow_of(disc, 1.5, gain)
    img = tint(glow, C("accent"))
    ring = ImageChops.subtract(disc, circ_mask((W, H), cx, cy, r_fill))
    img = Image.alpha_composite(img, tint(ring, C("accent"), ring_a))
    img = Image.alpha_composite(img, tint(circ_mask((W, H), cx, cy, r_fill), FROST, fill_a))
    return img


def build_opt(which):
    """x_ui_cfg_opt_[off|on|over].png 80×40 · nine l14 t6 r14 b6 —— 值按钮三态底

    off ：**全透明**（冻结书 §二「透明 + 无描边」；参照作未选值按钮也只有文字）
    on  ：冰蓝胶囊（同 tab_on 渐变、**降饱和 10%**）
    over：胶囊 + 1px 霜白高光边
    安全区：中段（行 6..33 / 列 14..65）为逐行相同的横向渐变（on/over）或纯透明（off）
    ⇒ 横向拉伸平滑、纵向拉伸逐像素复制。半径 20 = 半高（正胶囊，与参照作胶囊语言一致）。
    """
    W, H = 80, 40
    if which == "off":
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stops = [(0.0, desat(C("accent"), 0.10)),
             (0.62, desat(C("accent"), 0.10)),
             (1.0, desat(FROST, 0.10))]
    alpha = 235 if which == "on" else 245
    img = _capsule_grad((W, H), stops, alpha)
    if which == "over":
        outer = rr_mask((W, H), (0, 0, W, H), H / 2.0)
        inner = rr_mask((W, H), (1, 1, W - 1, H - 1), (H - 2) / 2.0)
        rim = ImageChops.subtract(outer, inner)
        img = Image.alpha_composite(img, tint(rim, FROST, 210))
    return img


def build_btn(over=False):
    """x_ui_cfg_btn[_over].png 80×40 · nine l16 t8 r16 b8 —— 通用小按钮（初始化／右上三键）

    常态：磨砂白 10% 填充 + 2px @palette.panel_edge 细边（圆角 10）
    悬停：填充提到 20% + 边发光（accent 系柔光）
    安全区：中段（行 8..31 / 列 16..63）只有均一团填充 ⇒ 双向拉伸无痕；
    圆角半径 10 略超 t=b=8 ⇒ 圆弧下沿落在左右边带（该带仅被纵向拉伸 ×2.5），
    观感为「略被拉长的圆角」而非硬接缝（已实测，见 contact sheet）。
    """
    W, H = 80, 40
    INSET, RAD, BW = 1.5, 10.0, 2.0
    outer = rr_mask((W, H), (INSET, INSET, W - INSET, H - INSET), RAD)
    inner = rr_mask((W, H), (INSET + BW, INSET + BW, W - INSET - BW, H - INSET - BW), RAD - BW)
    ring = ImageChops.subtract(outer, inner)
    fill_a = 26 if not over else 51                                 # 磨砂白 10% / 20%
    img = tint(outer, FROST, fill_a)                                # 填充铺满圆角矩形（描边随后压上）
    if over:
        img = Image.alpha_composite(img, tint(glow_of(ring, 2.2, 0.50), C("accent")))
    img = Image.alpha_composite(img, tint(ring, C("panel_edge"),
                                           OPA("panel_edge_opa") if not over else 240))
    return img


def build_chk(on=False):
    """x_ui_cfg_chk_[off|on].png 21×21 —— MUTE 勾选框（无 nine，1:1）

    空方框：2px @palette.panel_edge 圆角 3；勾选：方框 + @palette.accent 勾（2.5px 线）。
    """
    W = H = 21
    box_o = rr_mask((W, H), (1.5, 1.5, W - 1.5, H - 1.5), 3.0)
    box_i = rr_mask((W, H), (3.5, 3.5, W - 3.5, H - 3.5), 1.5)
    img = tint(ImageChops.subtract(box_o, box_i), C("panel_edge"), 240)
    if on:
        def _d(d, s):
            d.line([(5.5 * s, 11.0 * s), (9.0 * s, 14.5 * s), (15.5 * s, 7.0 * s)],
                   fill=255, width=int(round(2.5 * s)), joint="curve")
        img = Image.alpha_composite(img, tint(aa((W, H), _d), C("accent")))
    return img


def build_name_sel():
    """x_ui_cfg_name_sel.png 80×43 · nine l16 t0 r16 b0 —— 选中角色名胶囊

    @palette.highlight × @palette.highlight_opa，圆角 8（＜边带 16 ⇒ 圆弧全在端帽内）。
    t=b=0 ⇒ 整高即中段，但本件**每行都相同**（纯色、α 均匀、纵向 0 内缩 ⇒ 顶/底行也是
    满 α 而不是半透明行）⇒ 纵向为逐像素复制、横向中段 48px → 218px 的 nearest 拉伸
    在纯色区完全无痕（元素高 43 = 素材高，纵向 1:1）。
    """
    W, H = 80, 43
    m = rr_mask((W, H), (0, 0, W, H), 8.0)
    return tint(m, C("highlight"), OPA("highlight_opa"))


def build_dot():
    """x_ui_cfg_dot.png 12×12 —— 角色列表圆点（无 nine，1:1）：@palette.accent 实心圆"""
    return tint(circ_mask((12, 12), 6.0, 6.0, 6.0), C("accent"))


def build_spk():
    """x_ui_cfg_spk.png 22×32 —— 音量行喇叭（无 nine，1:1）

    @palette.text_menu 线性图标，程序化绘制：方体（箱体）+ 三角（喇叭口）+ 两道弧（声波）。
    4× 超采样降采样得到干净边缘（真 alpha，无黑边、无棋盘格）。
    """
    W, H = 22, 32
    col = C("text_menu")

    def _solid(d, s):
        d.rectangle([1 * s, 12 * s, 6 * s, 20 * s], fill=255)
        d.polygon([(6 * s, 12 * s), (12 * s, 6 * s), (12 * s, 26 * s), (6 * s, 20 * s)], fill=255)

    def _arcs(d, s):
        for r, a0, a1 in ((4.0, -60, 60), (7.5, -55, 55)):
            d.arc([(12 - r) * s, (16 - r) * s, (12 + r) * s, (16 + r) * s],
                  a0, a1, fill=255, width=int(round(2 * s)))

    img = tint(aa((W, H), _solid), col)
    return Image.alpha_composite(img, tint(aa((W, H), _arcs), col))


def build_preview_frame():
    """x_ui_cfg_preview_frame.png 96×96 · nine l24 t24 r24 b24 —— 预览框／角色横幅框（共用）

    2px @palette.panel_edge 细边（内缩 8，圆角 10）+ **极淡半透明磨砂底**
    （@palette.panel_fill α=55，均一填充 ⇒ 中心可无痕拉伸）+ 顶内 1px accent 高光线。
    高光线是水平直线（只随 y 变化）⇒ 横向拉伸无痕，且落在上边带（行 11 ∈ 0..23）。
    内缩 8 是为了让预览底图（preview_bg 内缩 10）**不会盖住本框的描边**（行 8..9 vs 行 ≥10）。
    """
    W = H = 96
    INSET, RAD, BW = 8.0, 10.0, 2.0
    outer = rr_mask((W, H), (INSET, INSET, W - INSET, H - INSET), RAD)
    inner = rr_mask((W, H), (INSET + BW, INSET + BW, W - INSET - BW, H - INSET - BW), RAD - BW)
    ring = ImageChops.subtract(outer, inner)

    img = tint(inner, C("panel_fill"), 55)                          # 极淡半透明磨砂底
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([0, 11, W, 12], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, inner), C("accent"), 90))
    img = Image.alpha_composite(img, tint(ring, C("panel_edge"), OPA("panel_edge_opa")))
    return img


def build_preview_bg():
    """x_ui_cfg_preview_bg.png 612×154 —— 预览示例画面（**100% 程序化**，无任何原版像素）

    冰蓝渐变（**横向**：左暗右亮 —— 实测取样第 20 行 (32,46,76)→(77,115,177) 递增、x=300 列近恒色；
    一审数据模块 Minor：原 docstring 写「上暗下亮/纵向」与实现不符，此处按实现订正）+ 2 条示意色带
    + 2 个暗色几何块（示意远景/前景）+ 1 个极淡光斑。只有少量色阶与直线边界，
    无 8-bit 噪声 ⇒ PNG 体积很小。
    四边内缩 10 + 圆角 16：既保持与 preview_frame 描边（行 8..9）不重叠，
    也让本图**不含任何棋盘格/白底烘焙**（圆角外真透明）。
    """
    W, H = 612, 154
    grad = Image.new("RGBA", (W, 1))
    px = grad.load()
    stops = [(0.00, INK_HI),
             (0.42, mix(C("panel_fill"), C("highlight"), 0.55)),
             (0.64, C("highlight")),
             (1.00, mix(C("highlight"), C("accent"), 0.55))]
    for x in range(W):
        t = x / float(W - 1)
        rgb = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                rgb = mix(c0, c1, 0.0 if p1 == p0 else (t - p0) / (p1 - p0))
                break
        px[x, 0] = tuple(rgb) + (255,)
    grad = grad.resize((W, H), Image.NEAREST)

    m = rr_mask((W, H), (10, 10, W - 10, H - 10), 16.0)
    img = grad
    img.putalpha(m)

    # 示意色带 2 条（水平，模拟地平线/光带）
    for y0, y1, col, a in ((46, 58, C("accent"), 26), (96, 104, FROST, 40)):
        band = Image.new("L", (W, H), 0)
        ImageDraw.Draw(band).rectangle([0, y0, W, y1], fill=255)
        img = Image.alpha_composite(img, tint(ImageChops.multiply(band, m), col, a))

    # 示意几何块 2 个（模拟远景建筑/家具剪影）
    blocks = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(blocks)
    bd.rounded_rectangle([48, 74, 150, 145], radius=4, fill=255)
    bd.rounded_rectangle([410, 66, 556, 145], radius=4, fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(blocks, m), C("panel_fill"), 175))

    # 极淡光斑（模拟画面里的亮部，供遮罩对比）
    spot = glow_of(circ_mask((W, H), 300.0, 96.0, 40.0), 26.0, 0.45)
    return Image.alpha_composite(img, tint(ImageChops.multiply(spot, m), FROST, 70))


def build_preview_mask():
    r"""x_ui_cfg_preview_mask.png 612×154 —— 预览用遮罩（无 nine，元素 612×154，1:1）

    ★★ **与 `x_ui_dlgmask_bottom_350.png` 同口径**：RGB 纯黑 #000000，
       纵向**线性**剖面 `alpha = round(255 × t)`，`t = 行号 / (H-1)`（H=154），
       即**上行全透明（α=0）、下行全浓（α=255）**；**素材上限保留 255**，
       实际强度**只由元素的 `opacity` 决定**（改浓度不必重出图）——与对话框遮罩同一旋钮。
       （实测 x_ui_dlgmask_bottom_350.png 亦为逐行 α=round(255·y/349) 的线性剖面；
         此处按 (H-1) 归一，正是为了末行恰为 255，与「下行全浓／上限保留 255」一致。
         冻结书 §二 括注写的 `t=行/154` 若照字面则末行只有 253，故作此归一。）
    ⚠️ 本件是**满幅**线性遮罩（不做圆角裁切），以保证「每行 α 严格相等」可被逐行验证；
       它与 preview_bg（内缩 10/圆角 16）叠放时，底部浓档会把 preview_frame 的圆角描边一并压暗
       —— 处置建议见交付报告「未决问题」。
    """
    W, H = 612, 154
    raw = bytearray()
    for y in range(H):
        a = int(round(255.0 * (y / float(H - 1))))
        raw += bytes((0, 0, 0, a)) * W
    return Image.frombytes("RGBA", (W, H), bytes(raw))


# ──────────────────────────────────────────────────────────────── 清单（接口冻结书 §二 表）
# name -> (builder, size, nine, 中心安全区语义, 四角是否必须全透明)
ASSETS = [
    ("x_ui_cfg_frame.png",         build_frame,                 (96, 96),   dict(l=24, t=24, r=24, b=24), "trans", True),
    ("x_ui_cfg_page_strip.png",    build_page_strip,            (64, 64),   dict(l=20, t=20, r=20, b=20), "solid", True),
    ("x_ui_cfg_tab_on.png",        build_tab_on,                (120, 50),  dict(l=25, t=0, r=25, b=0),   "vgrad", True),
    ("x_ui_cfg_tab_off.png",       build_tab_off,               (120, 50),  dict(l=25, t=0, r=25, b=0),   "xonly", True),
    ("x_ui_cfg_rail.png",          build_rail,                  (364, 11),  None,                          "-",     True),
    ("x_ui_cfg_knob.png",          lambda: build_knob(False),   (29, 29),   None,                          "-",     True),
    ("x_ui_cfg_knob_over.png",     lambda: build_knob(True),    (29, 29),   None,                          "-",     True),
    ("x_ui_cfg_opt_off.png",       lambda: build_opt("off"),    (80, 40),   dict(l=14, t=6, r=14, b=6),   "trans", True),
    ("x_ui_cfg_opt_on.png",        lambda: build_opt("on"),     (80, 40),   dict(l=14, t=6, r=14, b=6),   "vgrad", True),
    ("x_ui_cfg_opt_over.png",      lambda: build_opt("over"),   (80, 40),   dict(l=14, t=6, r=14, b=6),   "vgrad", True),
    ("x_ui_cfg_btn.png",           lambda: build_btn(False),    (80, 40),   dict(l=16, t=8, r=16, b=8),   "solid", True),
    ("x_ui_cfg_btn_over.png",      lambda: build_btn(True),     (80, 40),   dict(l=16, t=8, r=16, b=8),   "xonly", True),
    ("x_ui_cfg_chk_off.png",       lambda: build_chk(False),    (21, 21),   None,                          "-",     True),
    ("x_ui_cfg_chk_on.png",        lambda: build_chk(True),     (21, 21),   None,                          "-",     True),
    ("x_ui_cfg_name_sel.png",      build_name_sel,              (80, 43),   dict(l=16, t=0, r=16, b=0),   "solid", True),
    ("x_ui_cfg_dot.png",           build_dot,                   (12, 12),   None,                          "-",     True),
    ("x_ui_cfg_spk.png",           build_spk,                   (22, 32),   None,                          "-",     True),
    ("x_ui_cfg_preview_frame.png", build_preview_frame,         (96, 96),   dict(l=24, t=24, r=24, b=24), "solid", True),
    ("x_ui_cfg_preview_bg.png",    build_preview_bg,            (612, 154), None,                          "-",     True),
    ("x_ui_cfg_preview_mask.png",  build_preview_mask,          (612, 154), None,                          "-",     False),
]


# ──────────────────────────────────────────────────────────────── 自证
def _say(ok, name, detail):
    print("  [%s] %-44s %s" % ("OK " if ok else "NG!", name, detail))
    return bool(ok)


def _center_rows(img, nine):
    """中段（中心 cell）的行范围与列范围"""
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    return (t, img.size[1] - b), (l, img.size[0] - r)


def verify(name, img, size, nine, center_kind, corner_clear):
    ok = True
    ok &= _say(img.mode == "RGBA", name + " · 模式 RGBA（真 alpha）", img.mode)
    ok &= _say(img.size == size, name + " · 尺寸 = %dx%d" % size, "%dx%d" % img.size)

    px = img.load()
    W, H = img.size

    if corner_clear:
        cs = [px[0, 0][3], px[W - 1, 0][3], px[0, H - 1][3], px[W - 1, H - 1][3]]
        ok &= _say(max(cs) == 0, name + " · 四角完全透明 α=0", str(cs))

    if nine and center_kind != "-":
        (y0, y1), (x0, x1) = _center_rows(img, nine)
        if center_kind == "trans":
            bad = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if px[x, y][3] != 0]
            ok &= _say(not bad, name + " · 中心区全透明可拉伸",
                       "中心 %dx%d 区" % (x1 - x0, y1 - y0) + ("，违规像素 %d" % len(bad) if bad else ""))
        elif center_kind == "solid":
            ref = px[x0, y0]
            bad = sum(1 for y in range(y0, y1) for x in range(x0, x1) if px[x, y] != ref)
            ok &= _say(bad == 0, name + " · 中心区纯色可拉伸",
                       "%dx%d 区 unique=1 rgba=%s" % (x1 - x0, y1 - y0, ref) if bad == 0
                       else "违规像素 %d" % bad)
        elif center_kind == "vgrad":
            # 横向渐变的件：中段必须**逐行完全相同**（纵向拉伸即复制）
            row0 = [px[x, y0] for x in range(x0, x1)]
            badrows = [y for y in range(y0, y1) if [px[x, y] for x in range(x0, x1)] != row0]
            ok &= _say(not badrows, name + " · 中段逐行相同（横向渐变，纵向可拉伸）",
                       "列 %d..%d / 行 %d..%d，行不一致数 %d" % (x0, x1 - 1, y0, y1 - 1, len(badrows)))
        elif center_kind == "xonly":
            # 中段**只随 y 变化**（y 方向为柔光/圆角痕的衰减）：横向拉伸无痕；
            # 纵向拉伸会把该衰减曲线拉长（仍是连续剖面，不产生接缝）—— 如实打印其幅度。
            badrows = [y for y in range(y0, y1) if len(set(px[x, y] for x in range(x0, x1))) > 1]
            dys = [abs(px[(x0 + x1) // 2, y + 1][3] - px[(x0 + x1) // 2, y][3])
                   for y in range(y0, y1 - 1)]
            ok &= _say(not badrows, name + " · 中段沿 x 恒定（横向无痕；纵向为连续衰减剖面）",
                       "列 %d..%d / 行 %d..%d，行内不一致 %d 行；中段相邻行 |Δα| max = %d"
                       % (x0, x1 - 1, y0, y1 - 1, len(badrows), max(dys) if dys else 0))
    elif nine and center_kind == "-":
        pass

    if name == "x_ui_cfg_rail.png":
        rows = [[px[x, y][3] for x in range(W)] for y in range(H)]
        nz = [y for y in range(H) if max(rows[y]) > 8]
        ok &= _say(nz == [4, 5, 6, 7] or nz == [3, 4, 5, 6, 7],
                   name + " · 线体居中且束于中带（无边缘硬切）", "非零行 %s" % nz)

    if name == "x_ui_cfg_preview_mask.png":
        aa = [px[0, y][3] for y in range(H)]
        lin = [int(round(255.0 * y / (H - 1))) for y in range(H)]
        ok &= _say(aa == lin, name + " · 逐行 α == round(255·y/(H-1))（与对话框遮罩同口径）",
                   "首行 %d / 中线 %d / 末行 %d" % (aa[0], aa[H // 2], aa[-1]))
        ok &= _say(all(aa[i] <= aa[i + 1] for i in range(H - 1)), name + " · 纵向单调不减", "min step %d"
                   % min(aa[i + 1] - aa[i] for i in range(H - 1)))
        ok &= _say(aa[0] == 0 and aa[-1] == 255, name + " · 上行透明 / 下行全浓（上限保留 255）",
                   "%d → %d" % (aa[0], aa[-1]))
        rgb_black = all(px[x, y][:3] == (0, 0, 0) for x, y in ((0, 0), (W - 1, H - 1), (W // 2, H // 2)))
        ok &= _say(rgb_black, name + " · RGB 纯黑 #000000", "采样 3 点")

    if name == "x_ui_cfg_opt_off.png":
        ok &= _say(all(px[x, y][3] == 0 for y in range(H) for x in range(W)),
                   name + " · 全透明（冻结书 §二：透明 + 无描边）",
                   "max α = %d" % max(px[x, y][3] for y in range(H) for x in range(W)))
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 96)
    print("M47 · 设置屏重设 · W1 素材生成（20 件程序化生成；不写任何 JSON）")
    print("  输出目录 : %s" % OUT)
    print("  调色板   : %s（唯一色值来源，运行时读取）" % os.path.relpath(PALETTE, UI_GROUP))
    print("  参考键值 : panel_edge=%s/%d  accent=%s  highlight=%s/%d  panel_fill=%s  text_menu=%s"
          % (PAL.get("panel_edge", {}).get("value"), OPA("panel_edge_opa"),
             PAL.get("accent", {}).get("value"), PAL.get("highlight", {}).get("value"),
             OPA("highlight_opa"), PAL.get("panel_fill", {}).get("value"),
             PAL.get("text_menu", {}).get("value")))
    print("=" * 96)

    rows, total, ok_all = [], 0, True
    for name, fn, size, nine, ckind, cclear in ASSETS:
        img = fn()
        assert img.size == size, "%s：builder 产出 %s ≠ 表定 %s" % (name, img.size, size)
        if name != "x_ui_cfg_preview_mask.png":
            img = clip_low_alpha(img, 3)     # 抗锯齿残影归零（preview_mask 除外，见函数注释）
        p = os.path.join(OUT, name)
        img.save(p, optimize=True, compress_level=9)
        b = os.path.getsize(p)
        total += b
        rows.append((name, img.size, img.mode, b))
        print("-" * 96)
        print("【%s】" % name)
        ok_all &= verify(name, img, size, nine, ckind, cclear)

    print("=" * 96)
    print("生成清单（文件名 / 尺寸 / 模式 / 字节）：")
    for name, size, mode, b in rows:
        print("  %-30s %4d×%-4d %-5s %7d B" % (name, size[0], size[1], mode, b))
    print("  %-30s %-14s %-5s %7d B（%d 件；%.3f MB；预算上限 0.8 MB）"
          % ("合计", "", "", total, len(rows), total / 1048576.0))
    print("  九宫格参数（与冻结书 §二 表一致，供 W2 写 JSON 照抄）：")
    for name, fn, size, nine, ckind, cclear in ASSETS:
        if nine:
            print("    %-30s nine {l:%d, t:%d, r:%d, b:%d}  素材 %dx%d"
                  % (name, nine["l"], nine["t"], nine["r"], nine["b"], size[0], size[1]))
        else:
            print("    %-30s **无 nine** ⇒ 元素 w/h 必须 = %dx%d（1:1）" % (name, size[0], size[1]))
    ok_all &= _say(total <= int(0.8 * 1048576), "体积合计 ≤ 0.8 MB",
                   "%.3f MB" % (total / 1048576.0))
    print("  md5（逐件，供 W2/审查对账）：")
    for name, _fn, _s, _n, _c, _cc in ASSETS:
        with open(os.path.join(OUT, name), "rb") as f:
            print("    %-30s %s" % (name, hashlib.md5(f.read()).hexdigest()))
    print("=" * 96)
    print("RESULT=%s" % ("OK 20 件全部写出且自证通过" if ok_all else "NG 有自证未过（见上）"))
    print("★ 提醒：落盘后 layout\\screens\\25_config.json 才是真相源；本脚本重跑只覆盖这 20 张 PNG，"
          "不回退任何 JSON / 数据侧改动。")
    print("=" * 96)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
