# -*- coding: utf-8 -*-
r"""m56_make_plusbtn_assets.py · 章节详情「加号按钮」三态素材（ISSUE-20260930-02 · M1 · E1）

接口 : `_工作\ISSUE-20260930-02_章节详情\接口冻结.md`
       §一 裁定 1（新做 44×44 三态小徽章，风格对齐 `fc.pbkick`）
       §二 素材（M1）：`x_ui_plusbtn_{off,over,press}.png` 44×44 RGBA、真 alpha、四角 α=0、
             `optimize=True`、三件合计 ≤ 6 KiB
       §三.1 元素 `fc.p_plus` 矩形 (1803,625,44×44)（**本脚本不碰布局**）

■■ 做法（**复用既有风格代码，不新画**）

  · **盘面 = m55 `pbkick_base()` 的同一套三层画法**：柔外发光 → 盘面（霜白竖向渐变）→ 细环。
    本脚本的 `disc_base()` 是 `pbkick_base()` 的**参数化改写**（把写死的 W=H=119 / R=54 / 环宽 3 /
    σ=2.6 提成入参），**层序、色源、alpha 口径逐行相同**；并由 `assert_style_replica()` 用
    `disc_base(119,119,54.0,3.0,2.6)` 与 m55 的 `pbkick_base()` **逐像素比对**证明「同一套画法」
    （三态全等，否则直接非 0 退出）。
    三态色 **直接取 m55 的 `PBKICK_STYLE`**（off/over/on ⇒ 本件 off/over/press）：
      off   = `PBKICK_STYLE["off"]`   —— #E8F1FD 盘 α235 ＋ #929FB7 细环 ＋ #A7CBF1 字形
      over  = `PBKICK_STYLE["over"]`  —— #D7E7F9 盘 α248 ＋ ACCENT 环 ＋ 字形加深 ＋ 发光 ×3（悬停）
      press = `PBKICK_STYLE["on"]`    —— #A8CBF1 **实底** α252 ＋ ACCENT 环 ＋ 白字形（按下）
    几何**同比缩放**到 44×44：`SCALE = 44/119` ⇒ R = 54·S = 19.9664、环宽 = 3·S = 1.1092
    （＝冻结书 §二 的「1px 亮边」）、σ = 2.6·S = 0.9614。**不新增任何色号 / 不新增任何画法。**
    ★ **第 2 轮订正（用户裁定 7 · vision 实测后）**：**盘面**仍同比缩放，但**外圈环改为按目标尺寸
    1:1 直绘**（`ring_mask_1x`：像素中心落在环带内 ⇒ α255；off 环色＝族规 `RING_OFF`
    (146,159,183)、over/press＝`ACCENT`）。起因：把 119 上的 3px 环按 S=0.37 缩到 44 ⇒ 环带只剩
    1.109px，4×SSAA + LANCZOS 下采样后**没有任何像素拿到满覆盖** ⇒ 环色被摊薄成实测
    **(174,186,206)@α186**（vision 记 (172,185,206)@α186），与 pbkick 的 (146,159,183)@α255
    差一档 ⇒ 描边观感偏浅。改后环色与 pbkick **逐值相等**、环↔盘合成亮度差 66.3 ≈ pbkick 的 66.0。
    ⚠ `disc_base_styled()`（层序逐行同 m55）**保留**——它只用于 `assert_style_replica()` 的
    「同一套画法」逐像素证明与 `legacy_scaled_ring_base()` 的旧法对照读数；产出路径是
    `disc_base_target()`。
    三态语义与库内既有族实测一致（off→over 提亮：盘 α235→248、发光 gain 0.10→0.30、环由灰蓝转 ACCENT；
    on 态实底 #A8CBF1 α252 —— 与 `x_ui_gal_pgnext_on` / `x_ui_bgm_pb_prev_on` 实测主色 **逐字节同色**）。

  · **加号字形不手绘**：从既有 `x_ui_zoomin_off.png`（29×29，m55 `plate_base(29,29,"off")` ＋
    `plate_glyph(29,29,"plus")` 合成，实测与 m55 现版输出**逐字节一致**）中**精确反解**出字形覆盖率。
    ⚠️ **实测订正（派单原假设不成立）**：该件 **alpha 覆盖整块圆角盘面**（不是「只盖字形」），
       且**框线与字形同色**（框线 #A5C9F0=(165,201,240)、字形 #A7CBF1=(167,203,241)，色差仅 2）
       ⇒ **按 alpha 掩膜取不出字形、按颜色阈值也分不开**。故改用**反解 alpha-composite 方程**
       （见 `extract_plus_coverage()`）：支撑区（`m55.glyph_isolate` 逐像素差）内逐通道解出
       字形覆盖率 ga = (out_C·out_a − Cb·ba) / (gc − Cb·ba)，三通道取最小值、clip[0,1]。
       实测反解出的字形 = **16×16 十字、笔画 ≈4.15px、尖端圆头**（与 8× 放大目视一致）。

  · **下沉 1px** = 按下态整幅合成图**刚性下移 1 像素**后重新落画布（`sink()`），不缩放、不改几何
    （`fc.p_plus` 的 44×44 矩形不动）。由 `sink` 自证：`shift(不落沉的 press, +1)` 与落沉 press
    **逐字节相等**，且 α 加权质心位移实测 **+1.000 px**。

■ 幂等：纯程序化（无随机 / 无时间戳 / 无网络 / 不生成式生图）；**只读** palette.json 与既有素材
    `x_ui_zoomin_off.png`；同版本重跑**逐字节一致**（脚本内「每件连造两次字节比对」＋ 运行两次比 md5）。
■ 退出码：0 = 三件全部写出且结构 / 语义 / 字形 / 状态可辨 / 预算断言全过；任一不达标即 1 并打印明细。
■ 依赖：Pillow（`rounded_rectangle` 需 ≥8.2）、numpy；本机实测 Pillow 12.3.0 / numpy 2.5.3。
■ 运行：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260930-02_章节详情\复现脚本\m56_make_plusbtn_assets.py
    python _工作\ISSUE-20260930-02_章节详情\复现脚本\m56_make_plusbtn_assets.py --dry-run
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)                                    # …\ISSUE-20260930-02_章节详情
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(ISSUE, "证据")
M55_PATH = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材",
                        "复现脚本", "m55_make_flow_assets.py")
ZOOMIN_OFF = os.path.join(OUT, "x_ui_zoomin_off.png")
FONT_CANDIDATES = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                   r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\arialbd.ttf"]

# ══════════════════════════════════════════════════════════════ m55 复用（同源风格代码）
_spec = importlib.util.spec_from_file_location("m55_make_flow_assets", M55_PATH)
m55 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m55)

ACCENT = m55.ACCENT                     # #7AB0E8（palette.accent）
FROST = m55.FROST
MIX = m55.mix
# 三态色 = m55 的 PBKICK_STYLE（off/over/on ⇒ 本件 off/over/press）；**不另立色号**
DISC_STYLE = {
    "off":   dict(m55.PBKICK_STYLE["off"]),
    "over":  dict(m55.PBKICK_STYLE["over"]),
    "press": dict(m55.PBKICK_STYLE["on"]),
}
PRESS_SINK = 1                          # 按下态整体下移像素数（冻结书 §二）

# ══════════════════════════════════════════════════════════════ 几何（同比缩放 119 → 44）
W = H = 44
SCALE = W / 119.0                       # 0.369748
DISC_R = m55.PBKICK_R * SCALE           # 19.9664（pbkick 54 × S）
RING_W = 3.0 * SCALE                    # 1.1092（pbkick 环宽 3 × S ⇒ 冻结书「1px 亮边」）
GLOW_SIGMA_PROP = m55.PBKICK_STYLE["off"]["sig"] * SCALE   # 0.9613（pbkick σ2.6 × S，**同比值**）
# ★ σ **唯一偏离同比**（0.9613 → 0.60），理由与实测见 `assert_glow_fits()` 与交付报告：
#   44×44 画布上盘缘到画布边只剩 1.53px（pbkick 在 119 上是 5.0px），同比 σ 会让发光尾
#   触到画布边缘并被**硬切**（实测剪前最外 1px 帧 off/over/press = 5/15/21 > 10，
#   而 pbkick 原样仅 1/3/5）⇒ 破坏 m55 `frame` 口径的族内不变量「剪后最外 1px 帧 α=0」。
#   0.60 = 保住该不变量的最大 0.05 网格值（实测 2/6/9 ≤ 10）。**单常量可回退**。
GLOW_SIGMA = 0.60
CX = CY = (W - 1) / 2.0                 # 21.5
PLUS_SPAN = 18                          # 加号字形目标外接方框边长（px）
#   ↑ 取 45.1% 盘径（Ø39.93）：pbkick 字形／盘径实测比 = ▶ 48/108 = 44.4%、■ 44/108 = 40.7%
#     ⇒ 落在同族band内。**单常量可调**（冻结书 §七.2：笔画粗细／内边距由 vision + 用户目视裁定）。
MASK_FLOOR = m55.MASK_FLOOR             # 6（沿用 m55 的次像素残影归零口径）
RAW_FRAME_MAX = m55.RAW_FRAME_MAX       # 10
BUDGET_3 = 6 * 1024                     # 三件合计上限 6 KiB（冻结书 §二）
CASES = [("off", "常态"), ("over", "悬停（提亮）"), ("press", "按下（实底 + 下沉 1px）")]


# ══════════════════════════════════════════════════════════════ ① 盘面（m55 画法的参数化改写）
def disc_base_styled(style, w, h, r, ring_w, sigma):
    """`m55.pbkick_base()` 的**参数化同构改写**：层序 / 色源 / alpha 口径逐行相同，
    只把写死的 W=H=119、`PBKICK_R`=54、环宽 3、σ=2.6 提成入参。

    ⚠ **本函数只用于「同一套画法」的逐像素复刻证明**（`assert_style_replica()` 拿它跟
    `m55.pbkick_base()` 比）。**产出路径不用它**（见 `disc_base_target()` 的 1:1 环）。"""
    cx = cy = (w - 1) / 2.0
    disc = m55.circ_mask((w, h), cx, cy, r)
    ring = m55.sub_mask(disc, m55.circ_mask((w, h), cx, cy, r - ring_w))
    img = m55.flat((w, h))
    img = Image.alpha_composite(img, m55.tint(m55.glow_of(disc, sigma, style["gain"]), ACCENT))
    img = Image.alpha_composite(img, m55.body_fill((w, h), disc, style["fill"], style["ga"]))
    img = m55.paint(img, ring, style["ring"], 255)
    return img


def ring_mask_1x(size, cx, cy, r_out, r_in):
    r"""★★ 第 2 轮 · **按目标尺寸 1:1 直绘的环掩膜**（用户在裁定 7 之后由 vision 实测暴露的真缺陷）。

    病根：旧做法把 119 上的 **3px 环**按 S = 44/119 = 0.3697 缩到 44 ⇒ 环带只剩 **1.109px**；
    4×SSAA + LANCZOS 下采样后**没有任何一个像素拿到满覆盖**（斜向最多 ~73%）⇒ 环色被摊薄成
    实测 **(172,185,206)@α186**（vision 实测），而 pbkick 的环是 **(146,159,183)@α255**
    ⇒ 合成后与盘面的亮度差只有一半左右（vision 记 26 vs 45），观感「描边偏浅」。

    修法：**不再缩放环**，而是按目标尺寸逐像素判定「像素中心是否落在环带 `[r_in, r_out]`」，
    落内即 **255**。⇒ 环色**逐值等于**族规色（off = `RING_OFF` (146,159,183)@255；
    over/press = `ACCENT`），与 pbkick 的 off 环像素**逐通道相等**。
    外缘仍是几何硬边界（1px 环在 44 画布上本就是硬笔画），盘面自身的 AA 留在环带内缘之内。
    """
    w, h = size
    ys = np.arange(h, dtype=float)[:, None]
    xs = np.arange(w, dtype=float)[None, :]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    m = ((d <= r_out) & (d >= r_in)).astype(np.uint8) * 255
    return Image.fromarray(m, mode="L")


def disc_base_target(style, w, h, r, ring_w, sigma):
    """**产出路径**：盘面层序与 `disc_base_styled` 逐行相同，**只有环改成 1:1 直绘**。"""
    cx = cy = (w - 1) / 2.0
    disc = m55.circ_mask((w, h), cx, cy, r)
    img = m55.flat((w, h))
    img = Image.alpha_composite(img, m55.tint(m55.glow_of(disc, sigma, style["gain"]), ACCENT))
    img = Image.alpha_composite(img, m55.body_fill((w, h), disc, style["fill"], style["ga"]))
    ring = ring_mask_1x((w, h), cx, cy, r, r - ring_w)
    img = m55.paint(img, ring, style["ring"], 255)
    return img


def disc_base(state, w, h, r, ring_w, sigma):
    return disc_base_target(DISC_STYLE[state], w, h, r, ring_w, sigma)


def msg_frame(sigma, r=DISC_R):
    """给定 σ（与盘半径）时三态「剪前最外 1px 帧 αmax」——发光尾是否触到画布边缘的判据。

    ★ 用**产出路径**（`disc_base_target`，1:1 环）⇒ 该读数与实际落盘件同源。"""
    return [m55.frame_max(disc_base_target(DISC_STYLE[st], W, H, r, RING_W, sigma), 1)
            for st, _zh in CASES]


def assert_glow_fits():
    """σ 扫描：**证明 0.60 是为保住「剪后最外 1px 帧 α=0」的最小代价**，并给出同比值的失败读数。"""
    scan = [(sg, msg_frame(sg)) for sg in (0.4, 0.5, 0.60, 0.7, 0.8, 0.9, GLOW_SIGMA_PROP)]
    out = [("σ 扫描（盘 R=%.4f 固定）→ 剪前最外帧 off/over/press" % DISC_R,
            "；".join("%.4f→%s" % (sg, v) for sg, v in scan), True)]
    prop = scan[-1][1]                                  # 末项即同比值 σ=PBKICK σ×S
    out.append(("同比 σ=%.4f 时三态剪前帧 = %s（press %d > %d ⇒ 画布硬切，不可用）"
                % (GLOW_SIGMA_PROP, prop, prop[2], RAW_FRAME_MAX), "见左", prop[2] > RAW_FRAME_MAX))
    cur = msg_frame(GLOW_SIGMA)
    out.append(("实取 σ=%.2f 时三态剪前帧 = %s（全 ≤%d ⇒ 剪后恒 0）" % (GLOW_SIGMA, cur, RAW_FRAME_MAX),
                "见左", max(cur) <= RAW_FRAME_MAX))
    out.append(("盘面几何仍为**同比**：R = PBKICK_R(%.0f) × S(%.6f) = %.4f；环宽 = 3 × S = %.4f"
                % (m55.PBKICK_R, SCALE, DISC_R, RING_W), "见左",
                abs(DISC_R - m55.PBKICK_R * SCALE) < 1e-9 and abs(RING_W - 3.0 * SCALE) < 1e-9))
    return out


def assert_style_replica():
    """**同一套画法的硬证据**：`disc_base_styled(PBKICK_STYLE[s],119,119,54,3,σ)` 与
    m55 `pbkick_base(s)` 三态逐像素相等（对应关系 pbkick off/over/on ⇒ 本件 off/over/press）。"""
    out, bad = [], []
    for pb, ours in (("off", "off"), ("over", "over"), ("on", "press")):
        a = np.asarray(disc_base_styled(m55.PBKICK_STYLE[pb], 119, 119, m55.PBKICK_R, 3.0,
                                        m55.PBKICK_STYLE[pb]["sig"]))
        b = np.asarray(m55.pbkick_base(pb))
        same = a.shape == b.shape and bool((a == b).all())
        diff = 0 if same else int((np.abs(a.astype(int) - b.astype(int))).max())
        out.append(("pbkick_base(%s) 复刻 / 本件 %s 逐像素相等" % (pb, ours),
                    "相等" if same else "最大差 %d" % diff, same))
        if not same:
            bad.append(pb)
    return out


# ══════════════════════════════════════════════════════════════ ② 加号字形（精确反解，不手绘）
def assert_zoomin_reproduced():
    """既有 `x_ui_zoomin_off.png` 与 m55 现版输出**逐字节一致** ⇒ 反解基准可信。

    （射程内的必要前提：反解用的「无字形基准」必须就是该件的真实底盘。）"""
    fresh = m55.build_plate_button(29, 29, "plus", "off")
    b = io.BytesIO(); fresh.save(b, "PNG", optimize=True)
    disk = open(ZOOMIN_OFF, "rb").read()
    return ("x_ui_zoomin_off.png ≡ m55 plate_base+plus（逐字节）",
            "md5 %s" % hashlib.md5(disk).hexdigest()[:12], b.getvalue() == disk)


def extract_plus_coverage():
    """从 `x_ui_zoomin_off.png` **反解**加号字形覆盖率（0..1），返回 (cov(29×29 float), bbox)。

    反解 alpha-composite 方程（成品 = over(基准, 字形@GLYPH_OFF α255)），逐通道：
        out_C·out_a = gc·ga + Cb·ba·(1−ga)   →   ga = (out_C·out_a − Cb·ba) / (gc − Cb·ba)
    支持区取 `m55.glyph_isolate()` 的逐像素差掩膜**膨胀 1px**（把被阈值吃掉的 AA 羽化纳入）。
    """
    fin = m55.build_plate_button(29, 29, "plus", "off")     # 成品（剪后，与磁盘件逐字节同）
    base = m55.plate_base(29, 29, "off")                    # 无字形基准（剪前）
    ink = m55.glyph_isolate(fin, base)                      # 支撑掩膜（二值）
    support = ink.copy()
    support[1:, :] |= ink[:-1, :]; support[:-1, :] |= ink[1:, :]
    support[:, 1:] |= ink[:, :-1]; support[:, :-1] |= ink[:, 1:]

    F = np.asarray(fin).astype(float)
    B = np.asarray(base).astype(float)
    out_a, ba = F[:, :, 3] / 255.0, B[:, :, 3] / 255.0
    gc = np.array(m55.GLYPH_OFF, dtype=float) / 255.0
    cov = np.ones((29, 29))
    for c in range(3):
        den = gc[c] - B[:, :, c] / 255.0 * ba
        num = F[:, :, c] / 255.0 * out_a - B[:, :, c] / 255.0 * ba
        with np.errstate(divide="ignore", invalid="ignore"):
            g = np.where(np.abs(den) > 1e-6, num / den, np.nan)
        cov = np.where(np.isnan(g), cov, g) if c == 0 else np.minimum(cov, np.where(np.isnan(g), cov, g))
    cov = np.clip(cov, 0.0, 1.0)
    cov[~support] = 0.0
    ys, xs = np.nonzero(ink)
    return cov, (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def plus_mask(span, w, h, cx, cy, cov, bbox):
    """字形掩膜：裁剪到反解 bbox → LANCZOS 缩放到 span×span → 居中落盘（亚像素残影归零）。"""
    x0, y0, x1, y1 = bbox
    crop = cov[y0:y1 + 1, x0:x1 + 1]
    m = Image.fromarray(np.round(crop * 255.0).astype(np.uint8), mode="L")
    m = m.resize((span, span), Image.LANCZOS).point(lambda v: 0 if v <= MASK_FLOOR else v)
    canvas = Image.new("L", (w, h), 0)
    left = int(round((w - span) / 2.0))
    top = int(round((h - span) / 2.0))
    canvas.paste(m, (left, top))
    return canvas, (left, top)


def build_plusbtn(state, cov, bbox, apply_sink=True):
    """三态成品（已剪）：盘面（同比缩放的 pbkick 画法）＋ 字形；press 再整体下沉 1px。

    `apply_sink=False` 供「下沉自证」取不落沉的 press 参照件。"""
    disc = disc_base(state, W, H, DISC_R, RING_W, GLOW_SIGMA)
    gm, _pos = plus_mask(PLUS_SPAN, W, H, CX, CY, cov, bbox)
    img = m55.paint(disc, gm, DISC_STYLE[state]["glyph"], 255)
    img = m55.clip_low_alpha(img)
    if state == "press" and apply_sink:
        img = sink(img, PRESS_SINK)
    return img, gm


def sink(img, dy):
    """整体刚性下移 dy 像素（不缩放、不改画布）：直接搬像素，出界即裁。"""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, dy))
    return out


# ══════════════════════════════════════════════════════════════ ③b 环像素实测（★ 第 2 轮）
BACKDROP = (28, 41, 57)   # ≈ `x_ui_gal_cell_off` 内部实色（与对照图 `bg` 同源）


def annulus_pixels(img, cx, cy, r0, r1, with_xy=False):
    a = np.asarray(img).astype(float)
    h, w = a.shape[:2]
    ys = np.arange(h)[:, None].astype(float)
    xs = np.arange(w)[None, :].astype(float)
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    m = (d >= r0) & (d <= r1)
    if not with_xy:
        return a[m]
    yy = np.repeat(np.arange(h), w).reshape(h, w)[m]
    xx = np.tile(np.arange(w), (h, 1))[m]
    return a[m], yy, xx


def composite(px, bg=BACKDROP):
    """RGBA 逐像素合成到不透明底色上（px 形状 (...,4)）。"""
    if px.size == 0:
        return px
    a = px[..., 3:4] / 255.0
    return px[..., :3] * a + np.asarray(bg, dtype=float) * (1.0 - a)


def luma(c):
    return 0.299 * float(c[0]) + 0.587 * float(c[1]) + 0.114 * float(c[2])


def ring_reading(img, cx, cy, r_out, r_in, band=0.7, dy=0):
    r"""环读数（★ 第 2 轮）。

    三项：
      · `rgb`/`a` —— 环带内**覆盖率最高的一档**（α ≥ 带内峰值 −1）的代表值。
        改后（1:1 直绘）峰值恒 255 ⇒ 读数 ＝ **族规环色本身**；
      · `top_rgb`/`top_a` —— **正上方 cardinal 的环像素**＝几何环带中线的那个像素
        `(round(cx), round(cy − (r_in+r_out)/2) + dy)` —— 这是「外圈描边」最自然的取样点，
        也是 vision 实测 (172,185,206)@α186 的取法（`dy` 供 press 态整体下沉 1px 用）；
      · `diff` —— |median(luma(环核合成色)) − median(luma(盘面圈合成色))|（底色 `BACKDROP`）。
        盘面圈 ＝ 环内缘再往里 2..6px（已避开字形：44 上字形最远角 ≈ r12.7 < 12.86）。
    """
    arr = np.asarray(img).astype(float)
    h, w = arr.shape[:2]
    ring, ysb, xsb = annulus_pixels(img, cx, cy, max(0.0, r_in - band), r_out + band, with_xy=True)
    if ring.size:
        peak = float(ring[:, 3].max())
        core = ring[ring[:, 3] >= peak - 1.0]
    else:
        core = ring
    xm = min(max(int(round(cx)), 0), w - 1)
    ym = min(max(int(round(cy - (r_in + r_out) / 2.0)) + dy, 0), h - 1)
    top = arr[ym, xm]
    body = annulus_pixels(img, cx, cy, max(1.0, r_in - 6.0), max(1.0, r_in - 2.0))
    ref = core if core.size else ring
    rl = [luma(c) for c in composite(ref)] if ref.size else [0.0]
    bl = [luma(c) for c in composite(body)] if body.size else [0.0]
    return dict(n=int(ring.shape[0]), n_core=int(core.shape[0]),
                rgb=[int(np.median(ref[:, i])) for i in range(3)] if ref.size else [0, 0, 0],
                a=int(np.median(ref[:, 3])) if ref.size else 0,
                top_rgb=[int(top[i]) for i in range(3)], top_a=int(top[3]),
                top_xy=(xm, ym),
                a_max=int(ring[:, 3].max()) if ring.size else 0,
                ring_luma=float(np.median(rl)), body_luma=float(np.median(bl)),
                diff=float(abs(np.median(rl) - np.median(bl))))


def legacy_scaled_ring_base(state):
    """**改前的产出路径**（缩放得到的环，第 2 轮修复的对照物）——只用于自证「旧法读数」。"""
    return disc_base_styled(DISC_STYLE[state], W, H, DISC_R, RING_W, GLOW_SIGMA)


# ══════════════════════════════════════════════════════════════ ③ 量测工具
def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def alpha_feature(im):
    """特征点：盘顶首行（α≥250，即环／实底盘完全覆盖的首行）＋ α 加权质心（亚像素）。

    ⚠️ 阈值必须取 ≥250：实测 over/press 的**第 1 行**行内最大 α 已达 187/201（SSAA+LANCZOS
       的盘缘 AA），取 200 会把「部分覆盖行」也认成盘顶 ⇒ 下沉量读成 0（改前实跑踩到过）。"""
    a = np.asarray(im.getchannel("A")).astype(float)
    ys = np.nonzero((a >= 250).any(axis=1))[0]
    tot = a.sum()
    yy = np.arange(a.shape[0])[:, None]
    cy = float((a * yy).sum() / tot) + 0.5
    xs = np.nonzero((a >= 250).any(axis=0))[0]
    return dict(top250=int(ys.min()), bot250=int(ys.max()),
                left250=int(xs.min()), right250=int(xs.max()),
                cy=cy, mass=float(tot / 255.0))


def diff_stats(a, b):
    x = np.asarray(a).astype(int)
    y = np.asarray(b).astype(int)
    d = np.abs(x - y)
    return dict(px=int((d.max(axis=2) > 12).sum()), n=int(d.shape[0] * d.shape[1]),
                maxrgb=int(d[:, :, :3].max()), maxa=int(d[:, :, 3].max()),
                maxall=int(d.max()))


def measure_shift(a, b, rng=3):
    """整幅刚性位移量测：在 dy,dx ∈ [−rng,rng] 内找「行和 / 列和剖面最贴合」的位移。

    纯剖面互相关，**不受状态配色影响**（对比 α≥250 之类状态相关掩膜：off 的环是 α255、
    press 的实底盘是 α252 ⇒ 掩膜本身随态变化，质心读数不可比 —— 改前实跑踩到过）。"""
    A = np.asarray(a).astype(float)[:, :, 3]
    B = np.asarray(b).astype(float)[:, :, 3]
    RA, CA = A.sum(axis=1), A.sum(axis=0)
    best, bd = None, None
    for dy in range(-rng, rng + 1):
        RB = np.roll(B, dy, axis=0).sum(axis=1)
        for dx in range(-rng, rng + 1):
            CB = np.roll(B, dx, axis=1).sum(axis=0)
            d = float(((RA - RB) ** 2).sum() + ((CA - CB) ** 2).sum())
            if bd is None or d < bd:
                best, bd = (dy, dx), d
    return best, bd


def ink_profile(mask):
    """字形墨迹形态：外接框 / 面积（覆盖率求和，含 AA）/ 四端 / 杠长 / 等效笔画宽。

    等效笔画宽 w 由面积反解（十字 面积 = 2Lw − w² ⇒ w = L − √(L²−A)）——**不用于判「笔画粗细」的
    字面值**，只作「源件 → 成品等比」的可核对量（与源件同式读数比较）。"""
    arr = np.asarray(mask).astype(float) / 255.0
    ys, xs = np.nonzero(arr > 0.02)
    hcol, hrow = arr.sum(axis=0), arr.sum(axis=1)
    nzc, nzr = np.nonzero(arr > 0.02)
    w = int(xs.max() - xs.min() + 1); h = int(ys.max() - ys.min() + 1)
    area = float(arr.sum())
    span = float(max(w, h))
    return dict(x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()), w=w, h=h,
                area=area, bar_w=float(hrow.max()), bar_h=float(hcol.max()),
                eff_stroke=span - (span ** 2 - area) ** 0.5,
                left_col=float(hcol[nzc[0]]), right_col=float(hcol[nzc[-1]]),
                top_row=float(hrow[nzr[0]]), bot_row=float(hrow[nzr[-1]]))


# ══════════════════════════════════════════════════════════════ ④ 3× 对照图
def build_evidence(finals):
    """3× 三态横排对照图：纯色深底（**非棋盘格烘焙**）＋ 一根水平参考线 ＋ α 通道灰度条。"""
    s, pad, gap = 3, 24, 52
    bw, bh = W * s, H * s
    y_lab, y_btn = 10, 34                                  # 主标签行 / 三态画布顶
    y_num = y_btn + bh + 5                                 # 逐态读数行
    y_cap1, y_cap2 = y_num + 20, y_num + 38                # 两行说明
    y_strip = y_cap2 + 16                                  # α 通道条顶
    bg = (28, 41, 57)                                      # ≈ `x_ui_gal_cell_off` 内部实色（真实屏内色）
    fp = next(p for p in FONT_CANDIDATES if os.path.exists(p))
    font, small = ImageFont.truetype(fp, 15), ImageFont.truetype(fp, 12)
    ORANGE, GREY, DIM = (255, 122, 69), (190, 205, 225), (150, 170, 195)

    caps = ["橙线＝off 盘顶（α≥250 首行）；press 盘顶比 off 低 %d px（图中 ×3 = %d px）"
            % (tops_delta(finals), tops_delta(finals) * s),
            "下排＝α 通道（白=不透明／黑=全透明）：四角纯黑 = 真 alpha（非棋盘格烘焙）"]
    foot = ("off %d B / over %d B / press %d B / 合计 %d B（44×44 RGBA, optimize=True）"
            % (meta_bytes(finals, "off"), meta_bytes(finals, "over"), meta_bytes(finals, "press"),
               sum(meta_bytes(finals, st) for st, _zh in CASES)))
    # 画布宽度由文字实测自适应（**文字一律不许被裁**：超宽即报错，不静默截断）
    scratch = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    tw = int(max(scratch.textlength(t, font=small) for t in caps + [foot]))
    wpx = max(pad * 2 + bw * 3 + gap * 2, tw + 2 * pad)
    hpx = y_strip + H + 30
    fig = Image.new("RGB", (wpx, hpx), bg)
    dr = ImageDraw.Draw(fig)
    for txt in caps + [foot]:
        if dr.textlength(txt, font=small) > wpx - 2 * pad:
            raise RuntimeError("对照图文字超宽（%d > %d）：%s"
                               % (dr.textlength(txt, font=small), wpx - 2 * pad, txt))

    tops = []
    for i, (st, zh) in enumerate(CASES):
        im = finals[st]
        x = pad + i * (bw + gap)
        big = im.resize((bw, bh), Image.NEAREST)
        fig.paste(big, (x, y_btn), big)                    # 真 alpha 合成到底色（非棋盘格烘焙）
        f = alpha_feature(im)
        tops.append(f["top250"])
        dr.text((x, y_lab), "%s  %s" % (st, zh), fill=(255, 255, 255), font=font)
        dr.text((x, y_num), "盘顶 y=%d ｜ 盘底 y=%d" % (f["top250"], f["bot250"]), fill=ORANGE, font=small)
        al = im.getchannel("A").convert("RGB")             # α 通道灰度条（白 = 不透明）
        fig.paste(al, (x, y_strip))

    refline = y_btn + tops[0] * s                          # 钉在 off 态盘顶（α≥250 首行）贯穿三态
    dr.line([(0, refline), (wpx, refline)], fill=ORANGE, width=1)
    for i in range(3):
        x = pad + i * (bw + gap)
        dr.line([(x - 8, refline), (x - 1, refline)], fill=ORANGE, width=2)
        dr.line([(x + bw, refline), (x + bw + 7, refline)], fill=ORANGE, width=2)
    dr.text((pad, y_cap1), caps[0], fill=ORANGE, font=small)
    dr.text((pad, y_cap2), caps[1], fill=GREY, font=small)
    dr.text((pad, hpx - 22), foot, fill=DIM, font=small)
    return fig


def tops_delta(finals):
    return alpha_feature(finals["press"])["top250"] - alpha_feature(finals["off"])["top250"]


def meta_bytes(finals, st):
    return len(png_bytes(finals[st]))


# ══════════════════════════════════════════════════════════════ ⑤ 主流程
def run(write=True):
    rows, checks, fails = [], [], []
    ok = lambda lab, val, cond: (checks.append((lab, val, bool(cond))), None)  # noqa: E731

    # ── 前置：风格复刻 + 反解基准 + 发光贴合 ────────────────────
    for lab, val, o in assert_style_replica() + assert_glow_fits():
        ok(lab, val, o)
        if not o:
            fails.append(lab)
    lab, val, o = assert_zoomin_reproduced()
    ok(lab, val, o)
    if not o:
        fails.append(lab)

    cov, bbox = extract_plus_coverage()
    src = ink_profile(Image.fromarray(np.round(cov * 255).astype(np.uint8), mode="L"))

    # ── 逐件生成 ───────────────────────────────────────────────
    finals, gm_ref, meta = {}, None, {}
    for st, zh in CASES:
        im, gm = build_plusbtn(st, cov, bbox)
        im2, _ = build_plusbtn(st, cov, bbox)
        b1, b2 = png_bytes(im), png_bytes(im2)
        raw = m55.frame_max(m55.build_unclipped(lambda s=st: build_plusbtn(s, cov, bbox)[0]), 1)
        cut = m55.frame_max(im, 1)
        a = np.asarray(im)
        corners = [int(a[0, 0, 3]), int(a[0, -1, 3]), int(a[-1, 0, 3]), int(a[-1, -1, 3])]
        stt = m55.stats_of(im)
        name = "x_ui_plusbtn_%s.png" % st
        path = os.path.join(OUT, name)
        old = open(path, "rb").read() if os.path.exists(path) else None
        errs = []
        if im.mode != "RGBA":
            errs.append("mode=%s" % im.mode)
        if im.size != (W, H):
            errs.append("尺寸 %s" % (im.size,))
        if stt["amin"] != 0:
            errs.append("αmin=%d≠0" % stt["amin"])
        if stt["amax"] != 255:
            errs.append("αmax=%d≠255" % stt["amax"])
        if max(corners) != 0:
            errs.append("四角 α=%s 非全 0" % corners)
        if raw > RAW_FRAME_MAX:
            errs.append("剪前最外 1px 帧 αmax=%d>%d" % (raw, RAW_FRAME_MAX))
        if cut != 0:
            errs.append("剪后最外 1px 帧 αmax=%d≠0" % cut)
        if b1 != b2:
            errs.append("幂等失败（同进程两次字节不同）")
        feat = alpha_feature(im)
        rows.append(dict(name=name, state=st, size="%dx%d" % im.size, mode=im.mode, bytes=len(b1),
                         amin=stt["amin"], amax=stt["amax"], cov=stt["cov"], top=stt["top"],
                         corners=corners, rawframe=raw, frame=cut,
                         idem=("OK" if b1 == b2 else "FAIL"),
                         before=("新增" if old is None else ("未变" if old == b1 else "改写")),
                         md5=hashlib.md5(b1).hexdigest(), feat=feat,
                         ink=ink_profile(gm)))
        meta[st] = dict(bytes=len(b1), md5=hashlib.md5(b1).hexdigest(), feat=feat,
                        ink=ink_profile(gm), img=im, path=path, old=old)
        if gm_ref is None:
            gm_ref = np.asarray(gm).astype(int)
        if errs:
            fails.append("%s：%s" % (name, "; ".join(errs)))
        elif write:
            im.save(path, "PNG", optimize=True)
        finals[st] = im

    # ── 语义断言 ───────────────────────────────────────────────
    ik = meta["off"]["ink"]
    sc = PLUS_SPAN / float(src["w"])                      # 字形缩放比（18/16 = 1.125）
    ok("字形 bbox %d×%d（十字｜期望等边且 ≈%d）" % (ik["w"], ik["h"], PLUS_SPAN),
       "期望 %d×%d" % (PLUS_SPAN, PLUS_SPAN), ik["w"] == ik["h"] and abs(ik["w"] - PLUS_SPAN) <= 2)
    ok("字形杠长 横 %.2f／竖 %.2f（源 %.2f／%.2f × %.3f ⇒ 期望 %.2f／%.2f）"
       % (ik["bar_w"], ik["bar_h"], src["bar_w"], src["bar_h"], sc,
          src["bar_w"] * sc, src["bar_h"] * sc),
       "等比 ±1px", abs(ik["bar_w"] - src["bar_w"] * sc) <= 1.0
       and abs(ik["bar_h"] - src["bar_h"] * sc) <= 1.0)
    ok("字形等效笔画宽 %.2fpx（源件 %.2fpx × %.3f = %.2f ±0.2；**冻结书字面「2px」不符**）"
       % (ik["eff_stroke"], src["eff_stroke"], sc, src["eff_stroke"] * sc),
       "等比 ±0.2", abs(ik["eff_stroke"] - src["eff_stroke"] * sc) <= 0.2)
    ok("字形四端对称（左 %.2f vs 右 %.2f／上 %.2f vs 下 %.2f）"
       % (ik["left_col"], ik["right_col"], ik["top_row"], ik["bot_row"]),
       "对称", abs(ik["left_col"] - ik["right_col"]) <= 1.0 and abs(ik["top_row"] - ik["bot_row"]) <= 1.0)
    ok("字形面积 %.1f px²（源 %.1f × %.3f² = %.1f ±6%%）"
       % (ik["area"], src["area"], sc, src["area"] * sc ** 2),
       "等比", abs(ik["area"] - src["area"] * sc ** 2) <= 0.06 * src["area"] * sc ** 2)
    ok("字形对盘心居中（盘心 %.1f；字形 bbox 中心 %.1f）"
       % (CX, (ik["x0"] + ik["x1"]) / 2.0),
       "居中", abs((ik["x0"] + ik["x1"]) / 2.0 - CX) <= 0.01)

    # 下沉 1px：与「不落沉的 press」严格差一个刚性位移
    unsunk, _ = build_plusbtn("press", cov, bbox, apply_sink=False)
    d = diff_stats(finals["press"], sink(unsunk, PRESS_SINK))
    ok("下沉自证：press ≡ shift(不落沉 press, +%d)（差异像素 %d／%d，最大 ΔRGBA %d）"
       % (PRESS_SINK, d["px"], d["n"], d["maxall"]), "0 差异像素", d["px"] == 0)
    fc = {s: meta[s]["feat"] for s in meta}
    dt = fc["press"]["top250"] - fc["off"]["top250"]
    ok("下沉量实测·盘顶首行：off y=%d → press y=%d（= +%d）"
       % (fc["off"]["top250"], fc["press"]["top250"], dt), "+%d" % PRESS_SINK, dt == PRESS_SINK)
    # ★ 第 2 轮订正：α 质心的下沉量**必须比同款式的「不落沉 press」**（改前这里拿 off 比 press ——
    #   两态底填充/发光不同，质心本就差 ~0.04px；改成 1:1 硬环后该差从 0.000 变 0.036 ⇒ 假失败）。
    #   同款式对照才是「位移量」的正确读数，判据**没有放松**（仍要求 = +1.000，容差 0.01）。
    cy_unsunk = alpha_feature(unsunk)["cy"]
    dc = fc["press"]["cy"] - cy_unsunk
    ok("下沉量实测·α 加权质心（vs **不落沉 press**，同款式）：不落沉 %.3f → press %.3f（= %+.3f）"
       % (cy_unsunk, fc["press"]["cy"], dc), "+%d.000" % PRESS_SINK, abs(dc - PRESS_SINK) < 0.01)
    ok("对照·off 与 press 的质心差 %.3f（**非下沉量**：两态底填充/发光不同 ⇒ 质心本就不同；"
       "仅供读图参考）" % (fc["press"]["cy"] - fc["off"]["cy"]), "见左", True)
    (dy, dx), _ = measure_shift(finals["press"], unsunk)
    ok("下沉量实测·剖面互相关（press vs 不落沉 press）：位移 (dy,dx) = (+%d, %+d)（期望 (+%d, 0)）"
       % (dy, dx, PRESS_SINK), "(%+d, 0)" % PRESS_SINK, (dy, dx) == (PRESS_SINK, 0))
    (oy, ox), _ = measure_shift(finals["over"], build_plusbtn("over", cov, bbox, apply_sink=False)[0])
    ok("对照·over 自身零位移：位移 (dy,dx) = (%+d, %+d)（期望 (0, 0)）" % (oy, ox),
       "(0, 0)", (oy, ox) == (0, 0))
    d3 = diff_stats(build_plusbtn("over", cov, bbox, apply_sink=False)[0], unsunk)
    ok("press 与 over 的差别不止下沉（两者均不落沉时差异像素 %d／%d，最大 ΔRGBA %d）"
       % (d3["px"], d3["n"], d3["maxall"]), ">0", d3["px"] > 0)

    for p in (("off", "over"), ("off", "press")):
        d = diff_stats(finals[p[0]], finals[p[1]])
        ok("三态可辨 %s↔%s：差异像素 %d/%d（%.1f%%）、最大 ΔRGB %d、最大 ΔA %d、最大 ΔRGBA %d"
           % (p[0], p[1], d["px"], d["n"], 100.0 * d["px"] / d["n"], d["maxrgb"], d["maxa"], d["maxall"]),
           ">15%%", d["px"] > 0.15 * d["n"])
    am = {st: float(np.asarray(finals[st].getchannel("A")).mean()) for st in finals}
    ok("盘面「提亮／更实」实测平均 α：off %.1f → over %.1f → press %.1f（递增）"
       % (am["off"], am["over"], am["press"]), "递增", am["off"] < am["over"] < am["press"])

    # ── ★★ 第 2 轮：环像素实测（1:1 直绘 vs 旧法缩放摊薄）─────────────────
    #   判据（用户裁定 7「外圈描边加深到 pbkick 同值」的可机检形式）：
    #     ① 三态环核 α 满覆盖（255）；② off 环色逐值 == 族规 RING_OFF(146,159,183)；
    #     ③ off 环色与 `x_ui_pbkick_off.png` 的环像素逐值相等；
    #     ④ over/press 环色逐值 == ACCENT（族规）；⑤ 环↔盘合成亮度差 ≈ pbkick 的同一读数。
    pb = Image.open(os.path.join(OUT, "x_ui_pbkick_off.png")).convert("RGBA")
    pb_ring = ring_reading(pb, (pb.size[0] - 1) / 2.0, (pb.size[1] - 1) / 2.0,
                           m55.PBKICK_R, m55.PBKICK_R - 3.0)
    ring_reads = {st: ring_reading(finals[st], CX, CY, DISC_R, DISC_R - RING_W,
                                   dy=(PRESS_SINK if st == "press" else 0))
                  for st, _zh in CASES}
    legacy_ring = ring_reading(legacy_scaled_ring_base("off"), CX, CY, DISC_R, DISC_R - RING_W)

    ok("环核 α（off/over/press = %d/%d/%d；**旧法缩放环仅 %d**）"
       % (ring_reads["off"]["a"], ring_reads["over"]["a"], ring_reads["press"]["a"], legacy_ring["a"]),
       "三态恒 255", all(ring_reads[st]["a"] == 255 for st, _zh in CASES))
    ok("off 环色逐值 == 族规 RING_OFF %s（实测 %s，核 %d/%d px）"
       % (tuple(m55.RING_OFF), tuple(ring_reads["off"]["rgb"]),
          ring_reads["off"]["n_core"], ring_reads["off"]["n"]),
       "逐值相等", tuple(ring_reads["off"]["rgb"]) == tuple(m55.RING_OFF))
    ok("off 环色与 x_ui_pbkick_off 环像素逐值相等（本件 %s ／ pbkick %s；正上方 cardinal α %d ／ %d）"
       % (tuple(ring_reads["off"]["rgb"]), tuple(pb_ring["rgb"]),
          ring_reads["off"]["top_a"], pb_ring["top_a"]),
       "逐值相等", tuple(ring_reads["off"]["rgb"]) == tuple(pb_ring["rgb"])
       and tuple(ring_reads["off"]["top_rgb"]) == tuple(pb_ring["top_rgb"])
       and ring_reads["off"]["top_a"] == pb_ring["top_a"] == 255)
    for st in ("over", "press"):
        ok("%s 环色逐值 == ACCENT %s（实测 %s；正上方 cardinal %s@α%d）"
           % (st, tuple(ACCENT), tuple(ring_reads[st]["rgb"]),
              tuple(ring_reads[st]["top_rgb"]), ring_reads[st]["top_a"]),
           "逐值相等", tuple(ring_reads[st]["rgb"]) == tuple(ACCENT))
    ok("环↔盘 合成亮度差（底色 %s）：本件 off %.1f ／ over %.1f ／ press %.1f ｜ pbkick off %.1f"
       "（差 %+.1f，要求 ≤1.0）"
       % (BACKDROP, ring_reads["off"]["diff"], ring_reads["over"]["diff"], ring_reads["press"]["diff"],
          pb_ring["diff"], ring_reads["off"]["diff"] - pb_ring["diff"]),
       "≈pbkick", abs(ring_reads["off"]["diff"] - pb_ring["diff"]) <= 1.0)
    ok("旧法（缩放环）对照读数：cardinal %s@α%d、带内**满覆盖占比 %d/%d = %.1f%%**、带内峰值 α%d"
       "（改后为 %d/%d = %.1f%%）⇒ **复现 vision 的「偏浅」病因**：1.1px 环带经 SSAA 下采样后"
       "几乎全是羽化边、够不到族规环色（vision 实测 (172,185,206)@α186 即取自该羽化边）"
       % (tuple(legacy_ring["top_rgb"]), legacy_ring["top_a"],
          legacy_ring["n_core"], legacy_ring["n"],
          100.0 * legacy_ring["n_core"] / max(1, legacy_ring["n"]), legacy_ring["a_max"],
          ring_reads["off"]["n_core"], ring_reads["off"]["n"],
          100.0 * ring_reads["off"]["n_core"] / max(1, ring_reads["off"]["n"])),
       "旧法 <10%", legacy_ring["top_a"] < 255 and legacy_ring["a_max"] < pb_ring["a_max"]
       and legacy_ring["n_core"] < 0.10 * legacy_ring["n"])
    ok("环「满覆盖占比」与 pbkick 同档（本件 off %.1f%% ／ pbkick %.1f%%，差 %.1fpp ≤5pp）"
       % (100.0 * ring_reads["off"]["n_core"] / max(1, ring_reads["off"]["n"]),
          100.0 * pb_ring["n_core"] / max(1, pb_ring["n"]),
          abs(100.0 * ring_reads["off"]["n_core"] / max(1, ring_reads["off"]["n"])
              - 100.0 * pb_ring["n_core"] / max(1, pb_ring["n"]))),
       "≤5pp",
       abs(ring_reads["off"]["n_core"] / max(1, ring_reads["off"]["n"])
           - pb_ring["n_core"] / max(1, pb_ring["n"])) <= 0.05)

    tot = sum(meta[st]["bytes"] for st in meta)
    ok("三件合计 %d B ≤ %d B（6 KiB）" % (tot, BUDGET_3), "余 %d B" % (BUDGET_3 - tot), tot <= BUDGET_3)

    # ── 预算余量（**读** verify_ui.py 的 DEF_BUDGET_MB，不写死、不 import 以免留下字节码） ──
    import re
    vu = os.path.join(UI_GROUP, "工具", "verify_ui.py")
    mm = re.search(r"^DEF_BUDGET_MB\s*=\s*([0-9.]+)", open(vu, encoding="utf-8").read(), re.M)
    if mm is None:
        raise RuntimeError("verify_ui.py 未找到 DEF_BUDGET_MB")
    DEF_BUDGET_MB = float(mm.group(1))
    aset = sorted(os.path.join(OUT, f) for f in os.listdir(OUT) if f.lower().endswith(".png"))
    used = sum(os.path.getsize(f) for f in aset)
    cap = int(DEF_BUDGET_MB * 1024 * 1024)
    ok("素材预算（DEF_BUDGET_MB=%s MB）：%d 件 / %d B，余量 %d B；本批占 %d B（%.1f%%）"
       % (DEF_BUDGET_MB, len(aset), used, cap - used, tot, 100.0 * tot / max(1, cap - used)),
       "不越界", used <= cap)

    # ── 对照图 ─────────────────────────────────────────────────
    fig = build_evidence(finals)
    if write:
        os.makedirs(EVID, exist_ok=True)
        fig.save(os.path.join(EVID, "E1_三态对照_3x.png"), "PNG", optimize=True)

    # ── 报告 ───────────────────────────────────────────────────
    print("=" * 112)
    print("m56_make_plusbtn_assets.py · 章节详情加号按钮三态（ISSUE-20260930-02 · M1 素材 · E1）")
    print("风格源：%s" % os.path.relpath(M55_PATH, UI_GROUP))
    print("字形源：%s（反解，非手绘）｜ 落点：%s" % (os.path.relpath(ZOOMIN_OFF, UI_GROUP), OUT))
    print("几何：%d×%d ｜ 盘径 %.4f（=54×%.6f，同比）｜ 环宽 %.4f（=3×S，同比）｜ σ %.2f"
          "（同比 %.4f，**唯一偏离**）｜ 字形外接 %dpx（%.3f×）｜ 下沉 %dpx"
          % (W, H, DISC_R * 2, SCALE, RING_W, GLOW_SIGMA, GLOW_SIGMA_PROP, PLUS_SPAN,
             PLUS_SPAN / float(src["w"]), PRESS_SINK))
    print("-" * 112)
    print("%-26s %-6s %-6s %9s %4s %4s %7s %-14s %6s %6s %6s %s"
          % ("文件", "尺寸", "mode", "字节", "amin", "amax", "覆盖%", "四角α", "剪前帧", "剪后帧", "幂等", "写前"))
    for r in rows:
        print("%-26s %-6s %-6s %9d %4d %4d %7.2f %-14s %6d %6d %6s %s"
              % (r["name"], r["size"], r["mode"], r["bytes"], r["amin"], r["amax"], r["cov"],
                 str(r["corners"]), r["rawframe"], r["frame"], r["idem"], r["before"]))
    print("-" * 112)
    print("字形源件（反解自 x_ui_zoomin_off.png）：bbox %d×%d（x %d..%d, y %d..%d）｜ 面积 %.1f px²｜ "
          "杠长 %.2f／%.2f｜ 等效笔画 %.2fpx｜ 四端 左%.2f 右%.2f 上%.2f 下%.2f"
          % (src["w"], src["h"], src["x0"], src["x1"], src["y0"], src["y1"], src["area"],
             src["bar_w"], src["bar_h"], src["eff_stroke"], src["left_col"], src["right_col"],
             src["top_row"], src["bot_row"]))
    ik = meta["off"]["ink"]
    print("字形成品（%d×%d 盘面内居中）：bbox %d×%d（x %d..%d, y %d..%d）｜ 面积 %.1f px²｜ "
          "杠长 %.2f／%.2f｜ 等效笔画 %.2fpx｜ 四端 左%.2f 右%.2f 上%.2f 下%.2f"
          % (W, H, ik["w"], ik["h"], ik["x0"], ik["x1"], ik["y0"], ik["y1"], ik["area"],
             ik["bar_w"], ik["bar_h"], ik["eff_stroke"], ik["left_col"], ik["right_col"],
             ik["top_row"], ik["bot_row"]))
    for st, zh in CASES:
        f = meta[st]["feat"]
        print("  %-5s 盘顶 y %d ｜ 盘底 y %d ｜ α 质心 %.3f ｜ α 总质量 %.1f ｜ md5 %s"
              % (st, f["top250"], f["bot250"], f["cy"], f["mass"], meta[st]["md5"]))
    print("-" * 112)
    print("环像素实测（★ 第 2 轮：外圈环按目标尺寸 1:1 直绘）：")
    print("  %-7s %-18s %-4s %-22s %-9s %-8s %-8s %s"
          % ("态", "环核 RGB", "α", "正上方 cardinal(x,y)", "核/带 px", "环 luma", "盘 luma", "环↔盘 亮度差"))
    for st, _zh in CASES:
        rr = ring_reads[st]
        print("  %-7s %-18s %-4d %-22s %-9s %-8.1f %-8.1f %.1f"
              % (st, str(tuple(rr["rgb"])), rr["a"],
                 "%s@α%d @%d,%d" % (tuple(rr["top_rgb"]), rr["top_a"], rr["top_xy"][0], rr["top_xy"][1]),
                 "%d/%d" % (rr["n_core"], rr["n"]),
                 rr["ring_luma"], rr["body_luma"], rr["diff"]))
    print("  %-7s %-18s %-4d %-22s %-9s %-8.1f %-8.1f %.1f   ← 对照件（119×119 原生环）"
          % ("pbkick", str(tuple(pb_ring["rgb"])), pb_ring["a"],
             "%s@α%d @%d,%d" % (tuple(pb_ring["top_rgb"]), pb_ring["top_a"],
                                pb_ring["top_xy"][0], pb_ring["top_xy"][1]),
             "%d/%d" % (pb_ring["n_core"], pb_ring["n"]),
             pb_ring["ring_luma"], pb_ring["body_luma"], pb_ring["diff"]))
    print("  %-7s %-18s %-4d %-22s %-9s %-8.1f %-8.1f %.1f   ← **旧法**（缩放环，已废）"
          % ("旧法", str(tuple(legacy_ring["rgb"])), legacy_ring["a"],
             "%s@α%d @%d,%d" % (tuple(legacy_ring["top_rgb"]), legacy_ring["top_a"],
                                legacy_ring["top_xy"][0], legacy_ring["top_xy"][1]),
             "%d/%d" % (legacy_ring["n_core"], legacy_ring["n"]),
             legacy_ring["ring_luma"], legacy_ring["body_luma"], legacy_ring["diff"]))
    print("-" * 112)
    print("md5 清单：")
    for st, _zh in CASES:
        print("  %s  x_ui_plusbtn_%s.png" % (meta[st]["md5"], st))
    print("-" * 112)
    for lab, val, o in checks:
        print("  [%s] %s = %s" % ("OK" if o else "!!", lab, val))
    print("-" * 112)
    print("合计：%d 件 / %d B（%.2f KiB，上限 %d B）｜ 幂等 %d/%d ｜ 断言失败 %d 项"
          % (len(rows), tot, tot / 1024.0, BUDGET_3, sum(1 for r in rows if r["idem"] == "OK"),
             len(rows), sum(1 for _l, _v, o in checks if not o)))
    for f in fails:
        print("  !! %s" % f)
    result = not fails and all(o for _l, _v, o in checks)
    print("结果：**%s**" % ("全部通过" if result else "存在失败项"))
    print("=" * 112)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(run(write="--dry-run" not in sys.argv))
