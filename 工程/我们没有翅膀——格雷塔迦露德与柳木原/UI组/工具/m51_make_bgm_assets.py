# -*- coding: utf-8 -*-
r"""M51 · BGM 鉴赏页 · 素材模块 —— 程序化生成 `x_ui_bgm_*` 全套（37 件）

Issue : ISSUE-20260924-08（鉴赏模式四页重构 · **M3 = BGM 页**）
契约  : `_工作\ISSUE-20260924-08_鉴赏模式\方案.md`
        §0（参考件：`工程\交汇协奏曲\解包\gallery\结构清单.md` §2.2 BGM 页 34 条 + `layers_75.json`）
        §3（BGM 鉴赏页）、§8（纪律：PNG-32 真 alpha、我方冰蓝霜白、**禁止把文字烘焙进图**）

■■ 产出（全部落 `krkr\assets\ui\`，**新前缀 `x_ui_bgm_`，旧件一件不删**）
    ── 曲目行（`list.item_frame.state_assets` 逐项三态；1:1 件，无 nine）
    x_ui_bgm_row_{off,over,on}.png   526×59  （卡体 = 块内 x34..486 / y10..47，圆角 10，
                                              对应 PSB `Sound/item/オフ` 452×37 @(205,217)）
    ── 行内「播放」键（`list.item_buttons[0]`，块内局部 (0,7,29,40)，PSB `Sound/item/play`）
    x_ui_bgm_play_{off,over,on}.png  29×40
    ── 播放控制 8 键（PSB `Sound/ボタン/#pos/{none,one,all,rnd,prev,playpause,stop,next}` 59×59 @y831）
    x_ui_bgm_pb_<key>_{off,over,on}.png  59×59  × 8 键 = 24 件
    ── 播放/暂停互换态（PSB `Sound/ボタン/pause/*`，原作 `play/*` 组 visible=0 ⇒ 运行时互换）
    x_ui_bgm_pb_pause_{off,over,on}.png  59×59  × 3 件  ⇒ **本轮不接线**（见文件末「未接线」）
    ── 翻页键（参考作 BGM 页**无**页码键 ⇒ 取 CG 页页码键几何；与 M2 的 `x_ui_gal_pg*` 同形同尺寸）
    x_ui_bgm_pgprev_{off,over,on}.png / x_ui_bgm_pgnext_{off,over,on}.png  56×56  × 6 件
    ── 音量（PSB `Sound/volume/バー` 488×14、`volume/オン|オフ` 29×29）
    x_ui_bgm_rail.png          488×14
    x_ui_bgm_knob.png / x_ui_bgm_knob_over.png   29×29
    合计 3+3+24+3+6+1+2 = **42 件**

    ★ 标题牌 `x_ui_bgm_caption.png`（469×62）**本版不产出**：主代理 2026-09-24 裁决「页签 = 切屏」，
      共享外壳（页签条 + 标题 + 返回键）由 M1 的浮层屏 `39_gal_shell.json` 提供，本屏 `attach` 它
      （与 M2 的 `27_gallery.json` 同口径）⇒ 标题牌归外壳，本屏不重复出件。
    ★ 曲目区底板**本版不产出**：与 `26_backlog` / `27_gallery` / `37_dress` 同口径 ——
      系统屏是**透明浮层**，只留一层薄压暗（`mu.dim`），画面透出下层剧情背景；
      可读性由**行内卡体**（`x_ui_bgm_row_*`，α 235–252）承担（同 26_backlog 的 `x_ui_msgblock.png`）。

■■ 字形一律**图形**、**不含任何文字**
    原作图标条里 `1` / `ALL` / `RND` 是**烘焙进图**的拉丁字；本工程铁律禁止文字烘焙
    （`方案.md` §8）⇒ 本件改用**纯图形**：`none`=圆圈加斜杠、`one`=循环弧+单点、
    `all`=循环弧+三点、`rnd`=交叉箭头、`prev/next`=双三角、`playpause`=单三角、
    `stop`=方块、`pause`=双竖条。**键名/曲名/页码一律由引擎绘制**。

■■ 风格口径（我方冰蓝霜白族）
    配色**一律取自 `layout\palette.json`**（唯一色值来源，运行时读取；缺键即报错、不静默回落）。
    用到的键：accent / panel_edge / panel_edge_opa / panel_fill / panel_fill_opa / text_menu / node_locked。
    霜白 FROST 为合成色（推导自 accent 向白），与 M47/M49 同口径，**不新增色板键**。
    程序化绘制、4× 超采样降采样 ⇒ 真 alpha、无 8-bit 噪声、无棋盘格/白底烘焙、**可复现**
    （无随机、无时间戳 ⇒ 同版本脚本重跑逐字节一致）。

■■ 运行
    python 工具\m51_make_bgm_assets.py
  退出码 0 = 38 件全部写出且全部自证通过。**本脚本只产 PNG、绝不写任何 JSON**
  （`layout\screens\28_music.json` 才是几何真相源）。
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))                 # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                                  # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")

# 与 M47/M49 同一套基础工具（**import，不复制公式**，与 `test_quickbar_reach.py` 的守门口径一致）
sys.path.insert(0, HERE)
import m49_make_backlog_assets as base                            # noqa: E402

FROST = base.FROST


def load_palette(path=PALETTE):
    import json
    with open(path, encoding="utf-8") as f:
        return json.load(f)["colors"]


PAL = load_palette()


def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    return hex2rgb(PAL[key]["value"])


def OPA(key):
    return int(PAL[key]["value"])


mix = base.mix
tint = base.tint
aa = base.aa
glow_of = base.glow_of
clip_low_alpha = base.clip_low_alpha
rr_mask = base.rr_mask

ACCENT = C("accent")
EDGE = C("panel_edge")
EDGE_OPA = OPA("panel_edge_opa")
PFILL = C("panel_fill")
PFILL_OPA = OPA("panel_fill_opa")
TEXT_MENU = C("text_menu")

# 三态档（**唯一出处**：数据侧与自证都引用这里，避免两处各写一套）
ST = {
    "off":  {"body": 0.10, "body_a": 235, "rim": EDGE,   "rim_a": 150, "glow": 0.00, "glyph": 0.25, "glyph_a": 205},
    "over": {"body": 0.24, "body_a": 246, "rim": ACCENT, "rim_a": 220, "glow": 0.50, "glyph": 0.60, "glyph_a": 255},
    "on":   {"body": 0.62, "body_a": 252, "rim": ACCENT, "rim_a": 255, "glow": 0.72, "glyph": 1.00, "glyph_a": 255},
}
GLYPH_ON = FROST            # on 态字形用霜白（压在 accent 底上）


# ──────────────────────────────────────────────────────────── 通用底：圆角盘
def build_disc(size, radius, state, inset=1.5, rim_w=2.0, glyph_fn=None, glyph_scale=1.0):
    """三态圆角盘（+ 可选字形）。size=(W,H)；radius=圆角半径（外缘）。"""
    W, H = size
    s = ST[state]
    outer = rr_mask(size, (inset, inset, W - inset, H - inset), radius)
    inner = rr_mask(size, (inset + rim_w, inset + rim_w,
                           W - inset - rim_w, H - inset - rim_w), radius - rim_w)
    ring = ImageChops.subtract(outer, inner)

    img = tint(outer, mix(FROST, ACCENT, s["body"]), s["body_a"])
    if s["glow"] > 0:
        img = Image.alpha_composite(img, tint(glow_of(ring, 2.6, s["glow"]), ACCENT))
    # 顶内 1px 霜白高光（族语言：玻璃质感）
    hl = Image.new("L", size, 0)
    ImageDraw.Draw(hl).rectangle([0, int(inset + rim_w), W, int(inset + rim_w) + 1], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, inner), FROST, 150))
    img = Image.alpha_composite(img, tint(ring, s["rim"], s["rim_a"]))
    if glyph_fn is not None:
        gm = glyph_fn(size, glyph_scale)
        col = GLYPH_ON if (state == "on" and s["glyph"] >= 1.0) else mix(ACCENT, FROST, s["glyph"])
        img = Image.alpha_composite(img, tint(gm, col, s["glyph_a"]))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────── 图形字形（无文字）
def g_none(size, k=1.0):
    """⊘ 圆圈加斜杠（无循环）"""
    W, H = size
    cx, cy, r = W / 2.0, H / 2.0, 9.5 * k

    def _d(d, s):
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
                  outline=255, width=int(round(2.2 * k * s)))
        o = r * 0.7071
        d.line([(cx - o) * s, (cy - o) * s, (cx + o) * s, (cy + o) * s],
               fill=255, width=int(round(2.2 * k * s)))
    return aa(size, _d)


def g_one(size, k=1.0):
    """循环弧 + 中心单点（单曲循环）"""
    W, H = size
    cx, cy, r = W / 2.0, H / 2.0, 9.5 * k

    def _d(d, s):
        d.arc([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
              35, 325, fill=255, width=int(round(2.2 * k * s)))
        ax, ay = cx + r * math.cos(math.radians(35)), cy - r * math.sin(math.radians(35))
        d.polygon([(ax * s, ay * s), ((ax - 3.2 * k) * s, (ay - 1.0 * k) * s),
                   ((ax - 1.0 * k) * s, (ay + 3.2 * k) * s)], fill=255)
        d.ellipse([(cx - 2.2 * k) * s, (cy - 2.2 * k) * s,
                   (cx + 2.2 * k) * s, (cy + 2.2 * k) * s], fill=255)
    return aa(size, _d)


def g_all(size, k=1.0):
    """循环弧 + 三点（全曲循环）"""
    W, H = size
    cx, cy, r = W / 2.0, H / 2.0, 9.5 * k

    def _d(d, s):
        d.arc([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
              35, 325, fill=255, width=int(round(2.2 * k * s)))
        ax, ay = cx + r * math.cos(math.radians(35)), cy - r * math.sin(math.radians(35))
        d.polygon([(ax * s, ay * s), ((ax - 3.2 * k) * s, (ay - 1.0 * k) * s),
                   ((ax - 1.0 * k) * s, (ay + 3.2 * k) * s)], fill=255)
        for a in (90, 210, 330):
            px = cx + 4.6 * k * math.cos(math.radians(a))
            py = cy - 4.6 * k * math.sin(math.radians(a))
            d.ellipse([(px - 2.1 * k) * s, (py - 2.1 * k) * s,
                       (px + 2.1 * k) * s, (py + 2.1 * k) * s], fill=255)
    return aa(size, _d)


def g_rnd(size, k=1.0):
    """交叉箭头（随机）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0
    w = int(round(2.2 * k))

    def _d(d, s):
        for dy in (-4.2 * k, 4.2 * k):
            d.line([(cx - 8.5 * k) * s, (cy + dy) * s, (cx + 8.5 * k) * s, (cy - dy) * s],
                   fill=255, width=w * s)
        for dx in (8.5 * k,):
            for dy in (-4.2 * k, 4.2 * k):
                d.polygon([((cx + dx) * s, (cy + dy) * s),
                           ((cx + dx - 3.4 * k) * s, (cy + dy - 1.4 * k) * s),
                           ((cx + dx - 3.4 * k) * s, (cy + dy + 1.4 * k) * s)], fill=255)
                d.polygon([((cx - dx) * s, (cy - dy) * s),
                           ((cx - dx + 3.4 * k) * s, (cy - dy - 1.4 * k) * s),
                           ((cx - dx + 3.4 * k) * s, (cy - dy + 1.4 * k) * s)], fill=255)
    return aa(size, _d)


def _tri(d, s, x0, x1, cy, half, k):
    d.polygon([(x0 * s, (cy - half) * s), (x0 * s, (cy + half) * s), (x1 * s, cy * s)], fill=255)


def g_prev(size, k=1.0):
    """◀◀（apex 朝左 ⇒ `_tri` 的 x1 < x0；首版 x1 > x0 画成了 ▶▶，
    与 `next` 只差竖条位置、**肉眼不可分**，看图后修正）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        _tri(d, s, cx + 8.6 * k, cx + 1.0 * k, cy, 6.4 * k, k)
        _tri(d, s, cx + 0.6 * k, cx - 7.0 * k, cy, 6.4 * k, k)
        d.rectangle([(cx - 9.6 * k) * s, (cy - 6.4 * k) * s,
                     (cx - 8.4 * k) * s, (cy + 6.4 * k) * s], fill=255)
    return aa(size, _d)


def g_next(size, k=1.0):
    """▶▶（apex 朝右；竖条在最右 = 「跳到末尾」）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        _tri(d, s, cx - 8.6 * k, cx - 1.0 * k, cy, 6.4 * k, k)
        _tri(d, s, cx - 0.6 * k, cx + 7.0 * k, cy, 6.4 * k, k)
        d.rectangle([(cx + 8.4 * k) * s, (cy - 6.4 * k) * s,
                     (cx + 9.6 * k) * s, (cy + 6.4 * k) * s], fill=255)
    return aa(size, _d)


def g_play(size, k=1.0):
    """▶"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        d.polygon([((cx - 5.4 * k) * s, (cy - 7.6 * k) * s), ((cx - 5.4 * k) * s, (cy + 7.6 * k) * s),
                   ((cx + 7.6 * k) * s, cy * s)], fill=255)
    return aa(size, _d)


def g_stop(size, k=1.0):
    """■"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0
    q = 6.4 * k

    def _d(d, s):
        d.rectangle([(cx - q) * s, (cy - q) * s, (cx + q) * s, (cy + q) * s], fill=255)
    return aa(size, _d)


def g_pause(size, k=1.0):
    """‖"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        for dx in (-4.2 * k, 4.2 * k):
            d.rectangle([(cx + dx - 2.0 * k) * s, (cy - 7.6 * k) * s,
                         (cx + dx + 2.0 * k) * s, (cy + 7.6 * k) * s], fill=255)
    return aa(size, _d)


def g_play_glyph(size, k=1.0):
    """行内「播放」三角（29×40 竖长比例，非圆盘）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        d.polygon([((cx - 5.0 * k) * s, (cy - 9.0 * k) * s),
                   ((cx - 5.0 * k) * s, (cy + 9.0 * k) * s),
                   ((cx + 8.0 * k) * s, cy * s)], fill=255)
    return aa(size, _d)


def g_page_prev(size, k=1.0):
    """◀◀（翻页键字形；与 M2 的 `x_ui_gal_pgprev_*` 同形：双雪佛龙、无竖条）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        _tri(d, s, cx + 7.4 * k, cx + 0.8 * k, cy, 5.8 * k, k)
        _tri(d, s, cx - 0.6 * k, cx - 7.2 * k, cy, 5.8 * k, k)
    return aa(size, _d)


def g_page_next(size, k=1.0):
    """▶▶"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        _tri(d, s, cx - 7.4 * k, cx - 0.8 * k, cy, 5.8 * k, k)
        _tri(d, s, cx + 0.6 * k, cx + 7.2 * k, cy, 5.8 * k, k)
    return aa(size, _d)


def g_note(size, k=1.0):
    """♪（音量手柄「オン」态的图形字形；非文字）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0

    def _d(d, s):
        d.ellipse([(cx - 5.0 * k) * s, (cy + 1.0 * k) * s,
                   (cx - 1.4 * k) * s, (cy + 4.6 * k) * s], fill=255)
        d.rectangle([(cx - 1.8 * k) * s, (cy - 5.6 * k) * s,
                     (cx - 1.0 * k) * s, (cy + 3.0 * k) * s], fill=255)
        d.polygon([((cx - 1.0 * k) * s, (cy - 5.6 * k) * s),
                   ((cx + 5.0 * k) * s, (cy - 3.4 * k) * s),
                   ((cx + 5.0 * k) * s, (cy - 0.6 * k) * s),
                   ((cx - 1.0 * k) * s, (cy - 2.8 * k) * s)], fill=255)
    return aa(size, _d)


# ──────────────────────────────────────────────────────────── 翻页键 / 行底 / 行内播放 / 音量
def build_page(state, glyph_fn):
    """56×56 翻页键（**圆角方盘**，与 M2 的 `x_ui_gal_pgprev/pgnext_*` 同形同尺寸）"""
    return build_disc((56, 56), 12.0, state, inset=1.5, rim_w=2.0,
                      glyph_fn=glyph_fn, glyph_scale=1.15)


ROW_W = 526                        # 块宽（= 参考作列步进 527 − 行距 1；见文件末「几何依据」）
ROW_H = 59                         # 块高（= 参考作行步进 60 − 行距 1）
ROW_BOX = (34, 10, 486, 47)        # 卡体（块内局部；对应 PSB `Sound/item/オフ` 452×37 @(205,217)）
ROW_R = 10                         # 卡体圆角（参考作实测 ≈10px）


def build_row(state):
    """526×59 曲目行（1:1；卡体 inset，左侧 34px 留给行内播放键）"""
    W, H = ROW_W, ROW_H
    s = ST[state]
    card = rr_mask((W, H), ROW_BOX, ROW_R)
    ring = ImageChops.subtract(card, rr_mask((W, H), (ROW_BOX[0] + 2, ROW_BOX[1] + 2,
                                                       ROW_BOX[2] - 2, ROW_BOX[3] - 2), ROW_R - 2))
    img = tint(card, mix(FROST, ACCENT, s["body"]), s["body_a"])
    if s["glow"] > 0:
        img = Image.alpha_composite(img, tint(glow_of(ring, 2.6, s["glow"]), ACCENT))
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([ROW_BOX[0], ROW_BOX[1] + 2, ROW_BOX[2], ROW_BOX[1] + 3], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, card), FROST, 130))
    img = Image.alpha_composite(img, tint(ring, s["rim"], s["rim_a"]))
    return clip_low_alpha(img, 3)


def build_rail():
    """488×14 音量轨道"""
    W, H, R = 488, 14, 7
    outer = rr_mask((W, H), (0.5, 0.5, W - 0.5, H - 0.5), R)
    inner = rr_mask((W, H), (1.5, 1.5, W - 1.5, H - 1.5), R - 1.0)
    ring = ImageChops.subtract(outer, inner)
    img = tint(outer, mix(FROST, ACCENT, 0.06), 205)
    img = Image.alpha_composite(img, tint(ring, EDGE, 150))
    return clip_low_alpha(img, 3)


def build_knob(state):
    """29×29 音量手柄（normal = 素盘；over = accent 环 + ♪）"""
    st = "off" if state == "normal" else "on"
    return build_disc((29, 29), 13.0, st, inset=1.5, rim_w=2.0,
                      glyph_fn=(None if state == "normal" else g_note),
                      glyph_scale=1.35)


def build_play(state):
    """29×40 行内播放三角（无底盘，1:1）"""
    s = ST[state]
    gm = g_play_glyph((29, 40), 1.0)
    col = GLYPH_ON if state == "on" else mix(ACCENT, FROST, s["glyph"])
    img = tint(gm, col, s["glyph_a"])
    if s["glow"] > 0:
        img = Image.alpha_composite(img, tint(glow_of(gm, 2.2, s["glow"] * 0.8), ACCENT))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────── 清单（**唯一出处**）
PB_KEYS = ["none", "one", "all", "rnd", "prev", "playpause", "stop", "next"]
PB_GLYPH = {"none": g_none, "one": g_one, "all": g_all, "rnd": g_rnd,
            "prev": g_prev, "playpause": g_play, "stop": g_stop, "next": g_next}
# 59×59 圆盘（半径 26、inset 1.5 ⇒ 盘径 56）内的字形缩放：**唯一出处**。
#  1.0 时字形只占盘径约 1/3，看图判定「偏小」⇒ 取 1.5（字形约占盘径 0.51）。
PB_GLYPH_SCALE = 1.5

ASSETS = (
    [("x_ui_bgm_row_%s.png" % s, (lambda st: (lambda: build_row(st)))(s), (ROW_W, ROW_H))
       for s in ("off", "over", "on")]
    + [("x_ui_bgm_play_%s.png" % s, (lambda st: (lambda: build_play(st)))(s), (29, 40))
       for s in ("off", "over", "on")]
    + [("x_ui_bgm_pb_%s_%s.png" % (k, s),
        (lambda kk, ss: (lambda: build_disc((59, 59), 26.0, ss, glyph_fn=PB_GLYPH[kk],
                                            glyph_scale=PB_GLYPH_SCALE)))(k, s), (59, 59))
       for k in PB_KEYS for s in ("off", "over", "on")]
    + [("x_ui_bgm_pb_pause_%s.png" % s,
        (lambda ss: (lambda: build_disc((59, 59), 26.0, ss, glyph_fn=g_pause,
                                        glyph_scale=PB_GLYPH_SCALE)))(s), (59, 59))
       for s in ("off", "over", "on")]
    + [("x_ui_bgm_pgprev_%s.png" % s, (lambda ss: (lambda: build_page(ss, g_page_prev)))(s), (56, 56))
       for s in ("off", "over", "on")]
    + [("x_ui_bgm_pgnext_%s.png" % s, (lambda ss: (lambda: build_page(ss, g_page_next)))(s), (56, 56))
       for s in ("off", "over", "on")]
    + [("x_ui_bgm_rail.png", build_rail, (488, 14))]
    + [("x_ui_bgm_knob.png", (lambda: build_knob("normal")), (29, 29))]
    + [("x_ui_bgm_knob_over.png", (lambda: build_knob("over")), (29, 29))]
)

# 只读自证：旧 28_music 素材**一件不删**（冻结书 §8 / 任务书 C 条）
OLD_KEEP = ["x_ui_music_list.png", "x_ui_music_list_on.png", "x_ui_track_off.png",
            "x_ui_track_over.png", "x_ui_track_playing.png", "x_ui_pb_play.png",
            "x_ui_pb_stop.png", "x_ui_pb_repeat.png", "x_ui_pb_pause.png",
            "x_ui_speana.png", "x_ui_tab_off.png", "x_ui_tab_on.png", "x_ui_tab_over.png"]


def _say(ok, name, detail):
    print("  [%s] %-46s %s" % ("OK " if ok else "NG!", name, detail))
    return bool(ok)


# 逐件自证期望（**唯一出处**）：半透明件（底板/轨道）与「只画字形、无底盘」的件
# 峰值 α 天然 < 240 ⇒ 按件给阈值；`glyph` 表该件应有可辨字形；`card` 表应有实心卡体。
EXPECT = {
    "x_ui_bgm_row_off.png":  dict(peak=225, glyph=False, card=True),
    "x_ui_bgm_row_over.png": dict(peak=225, glyph=False, card=True),
    "x_ui_bgm_row_on.png":   dict(peak=225, glyph=False, card=True),
    "x_ui_bgm_play_off.png": dict(peak=195, glyph="alpha"),   # 只画三角、无底盘（off 态 α=205）
    "x_ui_bgm_play_over.png": dict(peak=240, glyph="alpha"),
    "x_ui_bgm_play_on.png":  dict(peak=240, glyph="alpha"),
    "x_ui_bgm_rail.png":     dict(peak=180, glyph=False),     # 半透明轨道
    "x_ui_bgm_knob.png":     dict(peak=225, glyph=False),
    "x_ui_bgm_knob_over.png": dict(peak=225, glyph=True),     # 悬停态带 ♪ 字形
}
# 播放控制 8 键 + pause 组：不透明圆盘 + 字形
for _k in PB_KEYS + ["pause"]:
    for _s in ("off", "over", "on"):
        EXPECT["x_ui_bgm_pb_%s_%s.png" % (_k, _s)] = dict(peak=240, glyph=True)
# 翻页键（56×56 圆角方盘 + 双雪佛龙字形）
for _k in ("pgprev", "pgnext"):
    for _s in ("off", "over", "on"):
        EXPECT["x_ui_bgm_%s_%s.png" % (_k, _s)] = dict(peak=240, glyph=True)


def verify(name, img, size):
    """逐件自证。判据按 `EXPECT` 取；**四角 α=0 与尺寸 1:1 是硬判据**。"""
    exp = EXPECT[name]
    ok = True
    ok &= _say(img.mode == "RGBA", name + " · 模式 RGBA（真 alpha）", img.mode)
    ok &= _say(img.size == size, name + " · 尺寸 = %dx%d（1:1 件，无 nine）" % size, "%dx%d" % img.size)
    W, H = img.size
    px = img.load()
    cs = [px[0, 0][3], px[W - 1, 0][3], px[0, H - 1][3], px[W - 1, H - 1][3]]
    ok &= _say(max(cs) == 0, name + " · 四角完全透明 α=0", str(cs))
    peak = max(px[x, y][3] for y in range(H) for x in range(W))
    ok &= _say(peak >= exp["peak"], name + " · 峰值 α ≥ %d" % exp["peak"], "αmax=%d" % peak)
    if exp.get("card"):
        # 卡体中段应实心（块内局部 x34..486 / y10..47 的中心）
        cx, cy = (34 + 486) // 2, (10 + 47) // 2
        a = [px[cx + dx, cy][3] for dx in (-100, 0, 100)]
        ok &= _say(min(a) >= 200, name + " · 卡体中段实心 α ≥ 200", str(a))
    if exp.get("glyph") == "alpha":
        # **无底盘、只画字形**的件（`x_ui_bgm_play_*`）：判据只能按 α（这类件在 α=0 处
        # 仍保留 RGB，逐色作差恒为 0 —— 初版按盘体色比对即被这条咬到，已改）。
        n = sum(1 for y in range(H // 4, 3 * H // 4) for x in range(W // 4, 3 * W // 4)
                if px[x, y][3] > 100)
        ok &= _say(n > 40, name + " · 中心区有字形（α > 100 的像素数）", "%d px" % n)
    elif exp.get("glyph"):
        # 有底盘的件：以**盘体色**（顶缘内侧的纯底点）为基准，数中心区偏离 > 18 的像素
        bx, by = W // 2, 10
        body = px[bx, by]
        n = sum(1 for y in range(H // 4, 3 * H // 4) for x in range(W // 4, 3 * W // 4)
                if max(abs(px[x, y][i] - body[i]) for i in range(3)) > 18)
        ok &= _say(n > 40, name + " · 中心区有字形（与盘体色差异 > 18 的像素数）", "%d px" % n)
    return ok


def diff_px(a, b):
    n = 0
    pa, pb = a.load(), b.load()
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            if max(abs(pa[x, y][i] - pb[x, y][i]) for i in range(4)) > 8:
                n += 1
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 100)
    print("M51 · BGM 鉴赏页 · 素材模块（`x_ui_bgm_*` 42 件，程序化生成）")
    print("  输出目录 : %s" % OUT)
    print("  调色板   : %s（唯一色值来源，运行时读取）" % os.path.relpath(PALETTE, UI_GROUP))
    print("  参考键值 : accent=%s  panel_edge=%s/%d  panel_fill=%s/%d  text_menu=%s"
          % (PAL.get("accent", {}).get("value"), PAL.get("panel_edge", {}).get("value"), EDGE_OPA,
             PAL.get("panel_fill", {}).get("value"), PFILL_OPA, PAL.get("text_menu", {}).get("value")))
    print("  基础工具 : import m49_make_backlog_assets（同一套 aa/rr_mask/tint/glow/调色板读取）")
    print("=" * 100)

    print("旧件只读自证（**本脚本不写这些文件**；任务书 C 条：旧 28_music 素材一件不删）：")
    for n in OLD_KEEP:
        p = os.path.join(OUT, n)
        if os.path.exists(p):
            with open(p, "rb") as f:
                b = f.read()
            with Image.open(p) as im:
                sz, mode = im.size, im.mode
            print("  [OK ] %-28s 存在 %s %-5s %8d B  md5=%s"
                  % (n, "%dx%d" % sz, mode, len(b), hashlib.md5(b).hexdigest()))
        else:
            print("  [NG!] %-28s **不存在**" % n)

    ok_all, rows, built = True, [], {}
    for name, fn, size in ASSETS:
        img = fn()
        assert img.size == size, "%s 尺寸 %s != %s" % (name, img.size, size)
        built[name] = img
        p = os.path.join(OUT, name)
        img.save(p, optimize=True, compress_level=9)
        b = os.path.getsize(p)
        rows.append((name, size, b))
        print("-" * 100)
        print("【%s】%dx%d" % (name, size[0], size[1]))
        ok_all &= verify(name, img, size)

    # 三态互异自证（**族语言**：on 明显更蓝更亮）
    print("-" * 100)
    print("三态互异自证（逐组：off↔over、off↔on 差异像素 > 100）：")
    for grp in (["x_ui_bgm_row", "x_ui_bgm_play"]
                + ["x_ui_bgm_pb_" + k for k in PB_KEYS] + ["x_ui_bgm_pb_pause"]
                + ["x_ui_bgm_pgprev", "x_ui_bgm_pgnext"]):
        a = built["%s_off.png" % grp]
        o = built["%s_over.png" % grp]
        n = built["%s_on.png" % grp]
        d1, d2 = diff_px(a, o), diff_px(a, n)
        ok_all &= _say(d1 > 100 and d2 > 100, grp + " 三态互异",
                       "off↔over %d px ｜ off↔on %d px" % (d1, d2))

    print("-" * 100)
    print("生成清单（文件名 / 尺寸 / 模式 / 字节）：")
    for name, size, b in rows:
        print("  %-34s %dx%d RGBA %7d B" % (name, size[0], size[1], b))
    print("  合计 %d 件 ｜ %d B" % (len(rows), sum(b for _n, _s, b in rows)))
    print("  md5（逐件，供数据侧与审查对账）：")
    for name, _s, _b in rows:
        with open(os.path.join(OUT, name), "rb") as f:
            print("    %-34s %s" % (name, hashlib.md5(f.read()).hexdigest()))
    print("=" * 100)
    print("★ 未接线（如实登记，不得声称已生效）：")
    print("  · `x_ui_bgm_pb_pause_*`（3 件）是**播放/暂停互换态**的 ‖ 字形组（原作 `Sound/ボタン/pause/*`；")
    print("    原作 `play/*` 组三态 visible=0 ⇒ 该互换是**运行时状态**）。本作**无音频代码**（M47 已登记），")
    print("    本轮**没有**承接「播放中」的 flag/机制 ⇒ 这 3 件**已产出但未被数据引用**，留给编程组接线。")
    print("  · 同理：8 键的「当前循环模式高亮」在本工程无对应运行态机制，本轮**不做**（原作亦只有整条三态）。")
    print("=" * 100)
    print("RESULT=%s" % ("OK %d 件全部写出且自证通过" % len(rows) if ok_all else "NG 有自证未过（见上）"))
    print("★ 提醒：`layout\\screens\\28_music.json` 才是几何真相源；本脚本重跑只覆盖这 %d 张 PNG。" % len(rows))
    print("=" * 100)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())