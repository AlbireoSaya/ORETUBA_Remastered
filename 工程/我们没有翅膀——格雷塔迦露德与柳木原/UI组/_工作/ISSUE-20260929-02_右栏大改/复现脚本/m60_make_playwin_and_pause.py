# -*- coding: utf-8 -*-
r"""m60_make_playwin_and_pause.py · 流程图右栏大改「大播放窗 + 暂停键」素材（4 件）—— 程序化生成

Issue : **ISSUE-20260929-02**（流程图右栏大改）· 模块 **E1 素材**
接口 : `_工作\ISSUE-20260929-02_右栏大改\接口冻结.md` **§A**（**唯一接口；字段与尺寸不得自行改动**）
用户指令 : `会话交接_20260929-02_流程图右栏大改_开工前状态.md` §一 第 2/3 条
前序配方 : `_工作\ISSUE-20260928-02_素材\复现脚本\m55_make_flow_assets.py`（**本脚本 import 它复用助手，不复制粘贴**）

■■ 产出清单（`krkr\assets\ui\`，**4 件**；仅新增，绝不覆盖任何既有件）

    x_ui_playwin_bg.png             380×300   1 态  大播放窗底板（**照 `build_replay_panel()` 同一配方**，仅尺寸改 380×300）
    x_ui_pbkick_pause_{off,over,on} 119×119   3 态  暂停键 ‖（**盘面 = 同态播放键逐像素同源**，只换字形掩膜）

■ 口径（逐条在 `证据\` 与交付报告里可复核）

  · **逐像素同源的可证明性靠「同一个函数」**：暂停键的盘面**不是**重画一遍，而是**直接调用**
    `M55.pbkick_base(state)`（及 `M55.PBKICK_STYLE` / `M55.PBKICK_R` / `M55.PBKICK_TRI_H`）。
    复制粘贴那段代码会毁掉这个证明 —— 本脚本**一行都没复制**（`import m55_make_flow_assets as M55`）。
    另加一条**母本再生自证**：`png_bytes(M55.build_pbkick(s))` 必须与磁盘上的
    `x_ui_pbkick_<s>.png` **逐字节相同** ⇒ 证明「磁盘母本就是这条代码路径的产物」。
  · **自证（必交）**：每态算 `diff = pause_<s> − pbkick_<s>`（RGBA 逐通道绝对差）。
    「字形 bbox」= `glyph_isolate` 量出的 ‖ 与 ▶ 两个墨迹 bbox 的**并集**；因 `aa()` 的 LANCZOS
    振铃会在直边外侧留 1px 淡晕（实测 4 像素、最大差 4），bbox **膨胀 1px** 作为容差 ⇒
    断言**盘面区（该区域之外）逐像素最大绝对差 = 0**。该区域还须落在冻结书 §A.1 的
    「以 119×119 中心为中心、≤66×60」窗口内。
  · **‖ 字形规格（冻结书 §A.1 + 派单，未自行改动）**：两条**圆角竖条**，圆角 **2.0**（与 ■ 同）、
    条高 = `M55.PBKICK_TRI_H`（**54**）、条宽 **16 / 间隙 16（合计 48，与 ▶ 等宽）**、
    以 `cx=cy=(W-1)/2` 为**整体居中**。
    ⚠ **实测校准（本条重要，否则实测会变成 50×56）**：`M55.aa()` 的 LANCZOS 降采样在**直边外侧**
      会留下超过 `M55.MASK_FLOOR`(6) 的振铃（实测该侧掩膜值 >6），使**实测墨迹比几何矩形每侧宽 ~1px**。
      故本脚本：① 圆角矩形的盒**直接写成目标墨迹的像素列/行区间**；② 掩膜再过一道
      `PAUSE_GLYPH_FLOOR=24` 把振铃归零。⇒ **实测** 暂停字形 bbox = **48×54**、条宽 **16/16**、
      间隙 **16**（与 ▶ 实测的 48×54 完全一致）。该等式由脚本**精确断言**（±0）。
  · **同族变体条（仅作证据，不落 assets）**：条宽 14 / 18 —— **间隙按「合计宽恒为 48」反解**（20 / 12）。
    ★ **派单原文写「间隙相应改为 17 / 15，保持合计宽 48」，该括注自相矛盾**：
      14+17+14=45、18+15+18=51，都≠48。本脚本取**可判定且被重复两次的不变量**「合计宽 48（＝▶ 宽）」
      为准（间隙=48−2×条宽），并把该矛盾写进交付报告待主代理裁决。另出 `on` 态 ■ 作形制参照。
  · **大播放窗照 `build_replay_panel()` 同一配方**（霜白竖向渐变 `PANEL_TOP`→`PANEL_BOT`、`INSET=5`、
    `RAD=12`、`BW=2`、外沿柔发光 `glow_of(plate,2.6,0.28)` 上 `ACCENT`、上沿内侧 1px 白高光带
    `FROST` α 0.42/34px 衰减），**仅 W,H 由 426×241 改 380×300**；盘面上**不烘焙任何文字**。
    该「同一配方」也不靠自述：脚本**把本配方跑一遍 426×241**，断言其字节
    **与 `M55.build_replay_panel()` 的输出逐字节相同**。
  · **真 alpha / 边缘策略 `frame`**：全部 PNG-32 真 alpha（无棋盘格、无白底烘焙）；
    外框内缩留发光带 ⇒ `M55.clip_low_alpha(thr=10)` 后**最外 1px 帧 α 恒为 0**（可机检）。
  · **配色**：一律读 `layout\palette.json`（唯一色值来源，经 M55 的 `ACCENT`/`PANEL_EDGE_BLUE` 等）；
    盘面合成色沿用 M55 实测值（`FROST`/`FILL_*`/`RING_OFF`/`GLYPH_*`），**不新增任何色号**。

■ 幂等
  · 纯程序化：**无随机、无时间戳、无网络、无 AI 生图、不读任何素材像素**（只读 palette.json）。
  · 同版本重跑**逐字节一致**；脚本自证「每件在内存里连造两次 + 与磁盘现值比对」。
  · 退出码 0 = 4 件全部写出且**结构 / 同源 / 字形 / 配方 / 母本完整性**断言全过；任一不达标即非 0 退出。

■ 依赖：Pillow（`ImageDraw.rounded_rectangle` 需 ≥ 8.2）、numpy（元数据与逐像素断言用）。
   字体：`C:\Windows\Fonts\msyhbd.ttc`（与 m55 同源，仅用于证据图标注）。
   本机实测：Python 3.14.7 / Pillow 12.3.0 / numpy 2.5.3。

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260929-02_右栏大改\复现脚本\m60_make_playwin_and_pause.py             # 产出 + 自证
    python _工作\ISSUE-20260929-02_右栏大改\复现脚本\m60_make_playwin_and_pause.py --dry-run   # 只自证，不写盘
"""
from __future__ import annotations

import hashlib
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)                                    # _工作\ISSUE-20260929-02_右栏大改
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(ISSUE_DIR, "证据")

# ★ 复用 m55 的助手（**逐像素同源的可证明性全靠这一步**；m55 带 `__main__` 守卫、可安全 import）
M55_DIR = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "复现脚本")
if M55_DIR not in sys.path:
    sys.path.insert(0, M55_DIR)
import m55_make_flow_assets as M55  # noqa: E402

# ── 母本基线 md5（2026-09-29 写前实测；只读比对，绝不改写） ────────────────────────
BASE_MD5 = {
    "x_ui_pbkick_off.png": "2e2bfac56e7e56e195b387f3d9b64920",
    "x_ui_pbkick_over.png": "d39806c167e62f63cd0e010bf0047088",
    "x_ui_pbkick_on.png": "ae5bc6bab757edef26cae3f0329f9661",
    "x_ui_replay_panel.png": "141caa79f10cffe788db4a45375949ab",
}

# ── 本批新增（**只准新增这 4 个名字**） ──────────────────────────────────────────
NEW_FILES = ["x_ui_playwin_bg.png",
             "x_ui_pbkick_pause_off.png", "x_ui_pbkick_pause_over.png", "x_ui_pbkick_pause_on.png"]

# ── 冻结书 §A.1 常量 ────────────────────────────────────────────────────────────
WIN_W, WIN_H = 380, 300          # 大播放窗底板尺寸（唯一改动：尺寸）
PAUSE_BAR_W = 16.0               # 定稿条宽
PAUSE_GAP = 16.0                 # 定稿间隙（合计宽 = 16+16+16 = 48 = ▶ 宽）
PAUSE_RAD = 2.0                  # 圆角（与 ■ 同）
PAUSE_GLYPH_FLOOR = 24           # LANCZOS 振铃归零（直边外侧实测抬高；M55.MASK_FLOOR=6 吃不下）
VARIANTS = [(14.0, 20.0), (16.0, 16.0), (18.0, 12.0)]   # (条宽, 间隙)，间隙 = 48 − 2×条宽

# 冻结书 §A.1 的「字形 bbox」窗口：以 119×119 中心为中心，宽 ≤66 / 高 ≤60
CENTER = (119 - 1) / 2.0
FREEZE_X0, FREEZE_X1 = int(CENTER - 33), int(CENTER - 33) + 65      # 66 列
FREEZE_Y0, FREEZE_Y1 = int(CENTER - 30), int(CENTER - 30) + 59      # 60 行

CROP = (30, 27, 94, 91)          # 证据图 4× 放大窗口（覆盖 ‖ / ▶ / ■ 三者）
ZOOM = 4

FONT_PATH = next((p for p in M55.FONT_CANDIDATES if os.path.exists(p)), None)
_FONT_CACHE: dict = {}


# ══════════════════════════════════════════════════════════════════ 小工具
def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def md5_of(b):
    return hashlib.md5(b).hexdigest()


def bbox_of(mask_bool):
    """布尔掩膜的 (x0,y0,x1,y1) 闭区间 bbox；空掩膜返回 None"""
    ys, xs = np.nonzero(mask_bool)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def runs_of(col_bool):
    """一维布尔（列有无墨迹）→ [(起,止,宽), ...]"""
    xs = np.nonzero(col_bool)[0]
    if len(xs) == 0:
        return []
    out, s, p = [], int(xs[0]), int(xs[0])
    for c in xs[1:]:
        c = int(c)
        if c == p + 1:
            p = c
        else:
            out.append((s, p, p - s + 1))
            s = p = c
    out.append((s, p, p - s + 1))
    return out


def dilate(mask_bool, r):
    m = mask_bool.copy()
    for _ in range(r):
        e = m.copy()
        e[1:, :] |= m[:-1, :]
        e[:-1, :] |= m[1:, :]
        e[:, 1:] |= m[:, :-1]
        e[:, :-1] |= m[:, 1:]
        m = e
    return m


def rect_mask(shape, box):
    m = np.zeros(shape, dtype=bool)
    m[box[1]:box[3] + 1, box[0]:box[2] + 1] = True
    return m


def set_rect(mask, box):
    mask[box[1]:box[3] + 1, box[0]:box[2] + 1] = True


def alpha_counts(im):
    a = np.asarray(im.getchannel("A"))
    return int((a == 0).sum()), int(((a > 0) & (a < 255)).sum()), int((a == 255).sum())


def ui_manifest():
    m = {}
    for p in sorted(os.listdir(OUT)):
        if p.lower().endswith(".png"):
            with open(os.path.join(OUT, p), "rb") as f:
                m[p] = md5_of(f.read())
    return m


def _font(sz):
    if sz not in _FONT_CACHE:
        _FONT_CACHE[sz] = ImageFont.truetype(FONT_PATH, sz)
    return _FONT_CACHE[sz]


C_CHECK_A, C_CHECK_B = (214, 218, 226), (176, 182, 194)
C_INK = (22, 30, 46)
C_DIM = (86, 96, 116)


def checker_bg(w, h, cs=10):
    im = Image.new("RGB", (w, h), C_CHECK_A)
    d = ImageDraw.Draw(im)
    for y in range(0, h, cs):
        for x in range(0, w, cs):
            if ((x // cs) + (y // cs)) % 2:
                d.rectangle([x, y, x + cs - 1, y + cs - 1], fill=C_CHECK_B)
    return im


def put_text(im, xy, s, sz, fill=C_INK, anchor="la"):
    ImageDraw.Draw(im).text(xy, s, font=_font(sz), fill=fill, anchor=anchor)


def text_w(s, sz):
    """文本像素宽度（用于按内容自适应画布宽，避免标注被裁）"""
    return ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(s, font=_font(sz))


# ══════════════════════════════════════════════════════════════════ ① 大播放窗底板
def build_playwin(w=WIN_W, h=WIN_H):
    r"""`x_ui_playwin_bg.png` · 380×300 · 大播放窗底板（边缘策略 frame）

    **照 `M55.build_replay_panel()` 同一配方**，仅 `W,H` 参数化 ⇒ 传 (426,241) 时与 m55 输出
    应**逐字节相同**（脚本对该等式做断言，这是「同一配方」的机器证明，不是自述）。
    盘面上**不烘焙任何文字 / 标题**（窗内文字与画面由引擎在运行期画）。
    """
    INSET, RAD, BW = 5.0, 12.0, 2.0
    box = (INSET, INSET, w - INSET, h - INSET)
    plate = M55.rr_mask((w, h), box, RAD)
    inner = M55.rr_mask((w, h), (box[0] + BW, box[1] + BW, box[2] - BW, box[3] - BW), RAD - BW)
    edge = M55.sub_mask(plate, inner)

    img = M55.flat((w, h))
    img = Image.alpha_composite(img, M55.tint(M55.glow_of(plate, 2.6, 0.28), M55.ACCENT))
    body = M55.vgrad((w, h), [(0.0, M55.PANEL_TOP), (1.0, M55.PANEL_BOT)], lambda t: 250 + 2 * t)
    body.putalpha(Image.fromarray(np.minimum(
        np.asarray(body.getchannel("A"), dtype=np.uint16),
        np.asarray(plate, dtype=np.uint16)).astype(np.uint8)))
    img = Image.alpha_composite(img, body)
    img = M55.paint(img, edge, M55.PANEL_EDGE_BLUE, 255)

    hl0 = M55.rr_mask((w, h), (box[0] + BW, box[1] + BW, box[2] - BW, box[3] - BW), RAD - BW)
    hl1 = M55.rr_mask((w, h), (box[0] + BW + 1, box[1] + BW + 1, box[2] - BW - 1, box[3] - BW - 1),
                      RAD - BW - 1)
    hl = M55.sub_mask(hl0, hl1)
    ramp = np.clip(1.0 - (np.arange(h, dtype=np.float32)[:, None] - (INSET + BW)) / 34.0, 0.0, 1.0)
    hl.putalpha(Image.fromarray(np.round(M55.A(hl) * ramp * 0.42).astype(np.uint8)))
    img = Image.alpha_composite(img, M55.tint(hl.getchannel("A"), M55.FROST))
    return M55.clip_low_alpha(img)


# ══════════════════════════════════════════════════════════════════ ② 暂停键 ‖
def pause_glyph(bar_w=PAUSE_BAR_W, gap=PAUSE_GAP):
    r"""‖ 字形掩膜：两条圆角竖条，整体居中于 `cx=cy=(W-1)/2`。

    条高 = `M55.PBKICK_TRI_H`(54)、圆角 `PAUSE_RAD`(2)、合计宽 = `2*bar_w + gap`（定稿 48 = ▶ 宽）。
    ★ 盒**直接写成目标墨迹的像素区间**（半开语义：`x0..x1` 即包含两端像素），再过
      `PAUSE_GLYPH_FLOOR=24` 归零 LANCZOS 振铃 ⇒ **实测墨迹 == 规格值**（16/16/16、48×54）。
    """
    W = H = 119
    total = 2 * bar_w + gap
    x0 = CENTER - total / 2.0
    y0 = CENTER - M55.PBKICK_TRI_H / 2.0
    l1 = x0 + bar_w - 1                    # 左条末列
    r0 = x0 + bar_w + gap                  # 右条首列
    r1 = r0 + bar_w - 1
    y1 = y0 + M55.PBKICK_TRI_H - 1

    def _bar(bx0, bx1):
        m = M55.rr_mask((W, H), (bx0, y0, bx1, y1), PAUSE_RAD)
        return m.point(lambda v: 0 if v <= PAUSE_GLYPH_FLOOR else v)

    return M55.union_mask(_bar(x0, l1), _bar(r0, r1))


def build_pause(state, bar_w=PAUSE_BAR_W, gap=PAUSE_GAP):
    r"""`x_ui_pbkick_pause_<state>.png` · 119×119 · 暂停键（边缘策略 frame）

    **盘面 = 同一态播放键逐像素同源**：`M55.pbkick_base(state)` 原样 + 换字形掩膜 + 同态字形色
    （`M55.PBKICK_STYLE[state]["glyph"]`）⇒ 与 `M55.build_pbkick(state)` 只差字形区。
    """
    img = M55.paint(M55.pbkick_base(state), pause_glyph(bar_w, gap),
                    M55.PBKICK_STYLE[state]["glyph"], 255)
    return M55.clip_low_alpha(img)


# ══════════════════════════════════════════════════════════════════ 证据图
def make_variant_strip(path):
    """字形对照条：暂停_14 / 暂停_16（定稿）/ 暂停_18 / 播放_off ＋ on 态方块（形制参照）

    ⚠ 标注一律用**中日文/ASCII 词**（「三角 / 方块 / 双竖条」）而非 ▶■‖ 等符号——
      证据字体 msyhbd 缺这些符号，直接写会渲染成豆腐块（实测踩到）。
    """
    tiles = [("暂停_14", build_pause("off", 14.0, 20.0), "条宽 14 · 间隙 20 · 合计宽 48"),
             ("暂停_16（定稿）", build_pause("off", 16.0, 16.0), "条宽 16 · 间隙 16 · 合计宽 48"),
             ("暂停_18", build_pause("off", 18.0, 12.0), "条宽 18 · 间隙 12 · 合计宽 48"),
             ("播放_off（三角参照）", M55.build_pbkick("off"), "三角 实测 bbox 48×54"),
             ("参照 播放_on（方块）", M55.build_pbkick("on"), "方块 bbox 44×44 · 圆角 2")]
    n = len(tiles)
    M, cg = 22, 24
    colw = max(119, (CROP[2] - CROP[0]) * ZOOM, 190)
    top = 74
    grid_w = 2 * M + n * colw + (n - 1) * cg
    t_title = "字形对照条 · 暂停键 条宽 14 / 16（定稿）/ 18 ＋ 播放键形制参照"
    t_sub = ("全部 1:1（119×119）置于棋盘格上；下层为字形区 4× 放大（NEAREST）"
             "｜暂停三变体合计宽恒为 48（＝播放键宽）")
    W = max(grid_w, int(max(text_w(t_title, 22), text_w(t_sub, 15))) + 2 * M + 8)
    tile_y = top + 26
    cap_y = tile_y + 119 + 8
    zlab_y = cap_y + 24
    zoom_y = zlab_y + 22
    H = zoom_y + (CROP[3] - CROP[1]) * ZOOM + 24
    im = checker_bg(W, H)
    d = ImageDraw.Draw(im)
    put_text(im, (M, 18), t_title, 22)
    put_text(im, (M, 48), t_sub, 15, C_DIM)
    for i, (name, tile, cap) in enumerate(tiles):
        cx = M + i * (colw + cg)
        if name.startswith("参照"):
            d.line([(cx - cg // 2, top), (cx - cg // 2, H - 18)], fill=(120, 128, 142), width=1)
        put_text(im, (cx + colw // 2, top - 2), name, 18, anchor="ma")
        im.paste(tile, (cx + (colw - 119) // 2, tile_y), tile)
        put_text(im, (cx + colw // 2, cap_y), cap, 14, C_DIM, anchor="ma")
        put_text(im, (cx + colw // 2, zlab_y), "4× 放大（字形区 64×64）", 14, C_DIM, anchor="ma")
        im.paste(tile.crop(CROP).resize(((CROP[2] - CROP[0]) * ZOOM,
                                         (CROP[3] - CROP[1]) * ZOOM), Image.NEAREST),
                 (cx + (colw - (CROP[2] - CROP[0]) * ZOOM) // 2, zoom_y))
    im.save(path, "PNG")


def make_sidebyside(path):
    """播放↔暂停 同屏对照：定稿暂停键三态 与 播放键三态 各一行并排（同底色、同 1:1）

    画布宽/高按**文本实测宽度**自适应，保证标注不被裁（首版曾因写死 489 宽而右缘截断）。
    ⚠ 标注用「三角 / 双竖条」等词，不用 ▶■ 符号（字体缺字形会变豆腐块）。
    """
    rows = [("暂停键（双竖条）· 定稿：条宽 16 / 间隙 16 / 高 54",
             [("暂停_%s" % s, build_pause(s)) for s in ("off", "over", "on")]),
            ("播放键（三角）· 既有 m55 件，本批未改动一个字节",
             [("播放_%s" % s, M55.build_pbkick(s)) for s in ("off", "over", "on")])]
    t_title = "播放 / 暂停 · 同屏对照（同一 119×119 画布 / 同一棋盘格 / 同一 1:1 比例）"
    t_sub = ("盘面逐像素同源：脚本直接调用 m55 的 pbkick_base(state)，只替换字形掩膜"
             "（见 暂停键逐像素同源自证.tsv）")
    t_note = ("★ 目视判据：两行应为「同一枚圆盘（同色 / 同环 / 同外发光）＋ 不同字形」；"
              "双竖条的笔画粗细应读作与三角同一视觉重量。")
    M, colw, cg = 22, 119, 44
    grid_w = 2 * M + 3 * colw + 2 * cg
    W = max(grid_w, int(max(text_w(t_title, 22), text_w(t_sub, 15), text_w(t_note, 15),
                             max(text_w(h, 18) for h, _ in rows))) + 2 * M + 8)
    top, rh, lab, rowgap, noteb = 78, 28, 24, 34, 26
    H = top + (rh + 119 + lab) * 2 + rowgap + noteb + 22
    im = checker_bg(W, H)
    y = top
    put_text(im, (M, 18), t_title, 22)
    put_text(im, (M, 48), t_sub, 15, C_DIM)
    for head, tiles in rows:
        put_text(im, (M, y), head, 18)
        y += rh
        for i, (name, tile) in enumerate(tiles):
            x = M + i * (colw + cg)
            im.paste(tile, (x, y), tile)
            put_text(im, (x + colw // 2, y + 119 + 2), name, 15, C_DIM, anchor="ma")
        y += 119 + lab + rowgap
    put_text(im, (M, H - noteb - 4), t_note, 15, C_INK)
    im.save(path, "PNG")


# ══════════════════════════════════════════════════════════════════ 自证报告
VIEW_MARK = "## 7. 目视核对与索引输出（E1 人工填写 · 脚本重跑保留本节）"
DEFAULT_TAIL = (VIEW_MARK + "\n\n"
                "（本节由 E1 在生成后目视两张对照 PNG、并跑 `工具\\emit_asset_index.py` 后填入；"
                "脚本重跑时本节**原样保留**。）\n")


def _preserve_tail(path):
    if os.path.exists(path):
        t = open(path, encoding="utf-8").read()
        i = t.find(VIEW_MARK)
        if i >= 0:
            return t[i:]
    return DEFAULT_TAIL


def write_report(res, rows, src_rows, fails, added, changed, removed, man_post):
    p = os.path.join(EVID, "自证报告.md")
    tail = _preserve_tail(p)
    L = []
    A = L.append
    A("# m60 自证报告 · 流程图右栏大改 E1 素材（ISSUE-20260929-02）")
    A("")
    A("- 脚本：`_工作\\ISSUE-20260929-02_右栏大改\\复现脚本\\m60_make_playwin_and_pause.py`"
      "（幂等、自带断言；**本报告 1–6 节全部机器产出，重跑逐字可复现**）")
    A("- 接口：`_工作\\ISSUE-20260929-02_右栏大改\\接口冻结.md` §A ｜ "
      "复用助手：`m55_make_flow_assets.py`（**import 同一函数，未复制一行**）")
    A("- 环境：Python 3.14.7 ｜ Pillow 12.3.0 ｜ numpy 2.5.3 ｜ 字体 `%s`" % FONT_PATH)
    A("- 结果：**%s**（断言 %d 项 / PASS %d / FAIL %d ｜ 结构失败 %d 件）"
      % ("全部通过" if (not fails and all(o for _, _, o in res)) else "存在失败项",
         len(res), sum(1 for _, _, o in res if o), sum(1 for _, _, o in res if not o), len(fails)))
    A("")
    A("## 1. 产出清单（4 件，**全部为新增**，未覆盖任何既有件）")
    A("")
    A("| 文件 | 期望尺寸 | 实测尺寸 | mode | 透明 / 半透明 / 不透明 | 最外1px帧αmax（剪后）| 写前状态 | md5 |")
    A("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        A("| `%s` | %s | %s | %s | %d / %d / %d | **%d** | %s | `%s` |"
          % (r["name"], r["exp"], r["size"], r["mode"], r["t"], r["s"], r["o"], r["cut"],
             r["before"], r["md5"]))
    A("")
    A("> 期望尺寸与实测尺寸逐件相等；全部 RGBA 真 alpha（αmin=0 / αmax=255，无棋盘格、无白底烘焙）；")
    A("> 边缘策略 `frame` ⇒ `clip_low_alpha(thr=10)` 后**最外 1px 帧 α 恒为 0**（上表「剪后」列）。")
    A("")
    A("## 2. 暂停键逐像素同源自证（每态）")
    A("")
    A("口径：`diff = pause_<s> − pbkick_<s>`（RGBA 逐通道绝对差）。「字形 bbox」= `glyph_isolate`")
    A("量出的 ‖ 与 ▶ 两个墨迹 bbox 的**并集**，**膨胀 1px** 作 AA 晕容差。")
    A("")
    A("| 态 | 暂停字形 bbox | 暂停列段（起-止-宽）| 播放字形 bbox | 联合 bbox | 盘面区非零像素 | **盘面区最大绝对差** | 联合bbox外（不膨胀）非零/最大 | 冻结窗口外非零/最大 |")
    A("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in src_rows:
        A("| %s | %s（**%d×%d**）| %s | %s | %s | %d | **%d** | %d / %d | %d / %d |"
          % (r["st"], r["bp"], r["bpw"], r["bph"],
             " ｜ ".join("%d-%d-**%d**" % c for c in r["cols"]), r["bt"], r["u"],
             r["out_cnt"], r["out_max"], r["d0_out"], r["d0_max"], r["fz_cnt"], r["fz_max"]))
    A("")
    A("> 「盘面区非零像素 = 0 且最大绝对差 = 0」= **盘面逐像素同源**的机器事实；")
    A("> 另两列给出更严的**不膨胀**口径（`off/over` 各 4 像素、最大 4；`on` 0 像素）——")
    A("> 这 4 个像素即形状边缘的 LANCZOS 振铃，位于字形 bbox 外沿 1px 内，故膨胀 1px 后归零。")
    A("> 冻结窗口 = 以 119×119 中心为中心、66×60 的居中矩形（冻结书 §A.1），联合 bbox 完全落在其内。")
    A("")
    A("## 3. 「同一配方」的机器证明（大播放窗底板）")
    A("")
    A("- `build_playwin(426, 241)` 的 PNG 字节 == `M55.build_replay_panel()` 的 PNG 字节：**%s**"
      % ("PASS" if any("配方证明" in lab and o for lab, _, o in res) else "FAIL"))
    A("  ⇒ 大播放窗确系 `build_replay_panel()` 的**同一配方**，唯一差异是尺寸（426×241 → **380×300**）。")
    A("- 4 角 α == 0 ｜ 中心 α > 240 ｜ 细蓝边像素数 > 300（见 §5 断言总表）。")
    A("")
    A("## 4. 母本（m55）未变 —— 三重证据")
    A("")
    A("| 母本 | 写前 md5（基线）| 写后 md5 | 一致 |")
    A("| --- | --- | --- | --- |")
    for nm, want in BASE_MD5.items():
        A("| `%s` | `%s` | `%s` | %s |" % (nm, want, man_post.get(nm, "—"),
                                          "PASS" if man_post.get(nm) == want else "FAIL"))
    A("")
    A("- **全库既有素材未变**：新增 %s ｜ 修改 **%d** ｜ 删除 **%d**"
      % (added if added else "无（本批 4 件已存在 ⇒ 幂等重跑）", len(changed), len(removed)))
    A("- **母本再生自证**：`M55.build_pbkick(off/over/on)` 与 `M55.build_replay_panel()` 的**内存产物**"
      "与**磁盘字节逐字节相同** ⇒ 磁盘母本正是这条代码路径的产物，本脚本叠加的正是同一个 `pbkick_base`。")
    A("")
    A("## 5. 断言总表（PASS / FAIL）")
    A("")
    A("| # | 判据 | 读数 | 结论 |")
    A("| --- | --- | --- | --- |")
    for i, (lab, val, ok) in enumerate(res, 1):
        A("| %d | %s | %s | **%s** |" % (i, lab, val, "PASS" if ok else "FAIL"))
    if fails:
        A("")
        A("**结构失败明细**：")
        for n, e in fails:
            A("- `%s`：%s" % (n, "; ".join(e)))
    A("")
    A("## 6. 幂等与已知偏离")
    A("")
    A("- 纯程序化：无随机、无时间戳、无网络、无 AI 生图、不读任何素材像素（只读 `layout\\palette.json`）；")
    A("  每件在内存里连造两次字节一致（§5 的结构断言含「幂等」项）。")
    A("- **偏离 1（已如实登记，待主代理裁决）**：派单原文「条宽 14 / 18（间隙相应改为 17 / 15，"
      "**保持合计宽 48**）」自相矛盾（14+17+14=45、18+15+18=51，均 ≠48）。"
      "本脚本按**被重复两次的不变量**「合计宽 48（＝ ▶ 宽）」反解间隙 ⇒ **20 / 12**；"
      "实测三变体均为 48×54、条宽 14/16/18、间隙 20/16/12。")
    A("- **偏离 2（实现细节，已登记）**：`M55.aa()` 的 LANCZOS 振铃在直边外侧残留掩膜值 > `M55.MASK_FLOOR`(6)，")
    A("  使**实测墨迹比几何矩形每侧宽 ~1px**（未处理时定稿实测为 50×56 而非 48×54）。")
    A("  故圆角矩形的盒**直接写成目标墨迹像素区间** + 掩膜过 `PAUSE_GLYPH_FLOOR=24` 归零振铃 ⇒ "
      "**实测 == 规格（48×54、16/16/16）**。该等式由脚本**精确断言**（±0）。")
    A("- 未触碰：`layout\\**`（只读 `palette.json`）、既有素材、m55 脚本、git（不提交）。")
    A("")
    A(tail)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return p


# ══════════════════════════════════════════════════════════════════ 主流程
def run(write=True):
    res = []       # (判据, 读数, ok)

    def add(label, val, ok):
        res.append((label, str(val), bool(ok)))

    if FONT_PATH is None:
        print("!! 找不到可用字体：%r" % M55.FONT_CANDIDATES)
        return 2

    # ── D. 母本完整性（写前） ──────────────────────────────────────
    man0 = ui_manifest()
    for nm, want in BASE_MD5.items():
        got = man0.get(nm)
        add("母本 md5 未变（写前）· %s" % nm, got, got == want)
    for st in ("off", "over", "on"):
        nm = "x_ui_pbkick_%s.png" % st
        disk = open(os.path.join(OUT, nm), "rb").read()
        add("母本再生自证·%s（M55.build_pbkick 内存产物 == 磁盘字节）" % nm,
            md5_of(png_bytes(M55.build_pbkick(st))),
            png_bytes(M55.build_pbkick(st)) == disk)
    rp_disk = open(os.path.join(OUT, "x_ui_replay_panel.png"), "rb").read()
    add("母本再生自证·x_ui_replay_panel（M55.build_replay_panel 内存产物 == 磁盘字节）",
        md5_of(png_bytes(M55.build_replay_panel())), png_bytes(M55.build_replay_panel()) == rp_disk)

    # ── C1. 大播放窗「同一配方」机器证明 ───────────────────────────
    add("配方证明：build_playwin(426,241) 字节 == M55.build_replay_panel() 字节",
        "%s vs %s" % (md5_of(png_bytes(build_playwin(426, 241))),
                      md5_of(png_bytes(M55.build_replay_panel()))),
        png_bytes(build_playwin(426, 241)) == png_bytes(M55.build_replay_panel()))

    # ── 组装 4 件（内存，先不写盘） ────────────────────────────────
    specs = [("x_ui_playwin_bg.png", (WIN_W, WIN_H), "frame", build_playwin)]
    for st in ("off", "over", "on"):
        specs.append(("x_ui_pbkick_pause_%s.png" % st, (119, 119), "frame",
                      (lambda s=st: build_pause(s))))
    built, rows, fails = {}, [], []
    for name, size, edgepol, fn in specs:
        im, im2 = fn(), fn()
        b1, b2 = png_bytes(im), png_bytes(im2)
        raw = M55.frame_max(M55.build_unclipped(fn), 1)
        cut = M55.frame_max(im, 1)
        t, s_, o = alpha_counts(im)
        errs = []
        if im.mode != "RGBA":
            errs.append("mode=%s（须 RGBA）" % im.mode)
        if im.size != size:
            errs.append("尺寸 %s ≠ 期望 %s" % (im.size, size))
        a = np.asarray(im.getchannel("A"))
        if int(a.min()) != 0:
            errs.append("αmin=%d ≠ 0（无真透明）" % int(a.min()))
        if int(a.max()) != 255:
            errs.append("αmax=%d ≠ 255（无实心像素）" % int(a.max()))
        if raw > M55.RAW_FRAME_MAX:
            errs.append("剪前最外 1px 帧 αmax=%d > %d（发光尾过强）" % (raw, M55.RAW_FRAME_MAX))
        if cut != 0:
            errs.append("剪后最外 1px 帧 αmax=%d ≠ 0" % cut)
        if b1 != b2:
            errs.append("幂等失败：同进程两次生成字节不同")
        old = None
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                old = f.read()
        if old is not None and old != b1:
            errs.append("写前状态=改写（既有件与本批产物不一致 ⇒ 拒绝覆盖）")
        built[name] = (im, b1)
        rows.append(dict(name=name, exp="%dx%d" % size, size="%dx%d" % im.size, mode=im.mode,
                         bytes=len(b1), t=t, s=s_, o=o, raw=raw, cut=cut,
                         before=("新增" if old is None else "未变"), md5=md5_of(b1)))
        if errs:
            fails.append((name, errs))
        add("结构·%s 尺寸/mode/α/帧/幂等" % name,
            "%s %s amin=0 amax=255 剪前帧=%d 剪后帧=%d 幂等=%s 写前=%s"
            % (rows[-1]["size"], im.mode, raw, cut, "OK" if b1 == b2 else "FAIL", rows[-1]["before"]),
            not errs)

    # ── B. 暂停键逐像素同源自证（每态） ───────────────────────────
    src_rows = []
    for st in ("off", "over", "on"):
        pause = built["x_ui_pbkick_pause_%s.png" % st][0]
        pbk = M55.build_pbkick(st)
        dm = np.abs(np.asarray(pause).astype(np.int16) - np.asarray(pbk).astype(np.int16)).max(axis=2)
        nz = dm > 0
        bp = bbox_of(M55.glyph_isolate(pause, M55.pbkick_base(st)))
        bt = bbox_of(M55.glyph_isolate(pbk, M55.pbkick_base(st)))
        u = (min(bp[0], bt[0]), min(bp[1], bt[1]), max(bp[2], bt[2]), max(bp[3], bt[3]))
        reg = dilate(rect_mask(nz.shape, u), 1)              # 字形 bbox + 1px AA 晕容差
        fz = rect_mask(nz.shape, (FREEZE_X0, FREEZE_Y0, FREEZE_X1, FREEZE_Y1))
        out_cnt, out_max = int((nz & ~reg).sum()), int(dm[~reg].max())
        fz_cnt, fz_max = int((nz & ~fz).sum()), int(dm[~fz].max())
        cols = runs_of((np.asarray(pause_glyph()) > 0).any(axis=0))
        add("同源·%s 盘面区（字形 bbox+1px 之外）最大绝对差 == 0" % st,
            "盘面区非零像素=%d 最大差=%d" % (out_cnt, out_max), out_cnt == 0 and out_max == 0)
        add("同源·%s 字形 bbox 落在冻结窗口（≤66×60 居中）内" % st,
            "联合 bbox %s ⊆ 窗口 x[%d,%d] y[%d,%d]" % (u, FREEZE_X0, FREEZE_X1, FREEZE_Y0, FREEZE_Y1),
            u[0] >= FREEZE_X0 and u[2] <= FREEZE_X1 and u[1] >= FREEZE_Y0 and u[3] <= FREEZE_Y1)
        add("同源·%s 窗口外（冻结书口径）非零像素 == 0" % st, "%d（最大差 %d）" % (fz_cnt, fz_max),
            fz_cnt == 0 and fz_max == 0)
        add("字形·%s 暂停字形 bbox == 48×54" % st,
            "%s（%d×%d）" % (bp, bp[2] - bp[0] + 1, bp[3] - bp[1] + 1),
            (bp[2] - bp[0] + 1, bp[3] - bp[1] + 1) == (48, 54))
        add("字形·%s 条宽/间隙 == 16/16（合计 48）" % st, "%s" % (cols,),
            len(cols) == 2 and cols[0][2] == 16 and cols[1][2] == 16
            and cols[1][0] - cols[0][1] - 1 == 16)
        src_rows.append(dict(st=st, bp=bp, bpw=bp[2] - bp[0] + 1, bph=bp[3] - bp[1] + 1,
                             cols=cols, bt=bt, u=u,
                             d0_out=int((nz & ~rect_mask(nz.shape, u)).sum()),
                             d0_max=int(dm[~rect_mask(nz.shape, u)].max()),
                             reg=reg, nz=int(nz.sum()),
                             out_cnt=out_cnt, out_max=out_max,
                             fz_cnt=fz_cnt, fz_max=fz_max,
                             nz_in_reg=int(nz[reg].sum())))

    # ── 变体（仅证据，不落 assets） ────────────────────────────────
    for bw, gp in VARIANTS:
        m = np.asarray(pause_glyph(bw, gp)) > 0
        b = bbox_of(m)
        cols = runs_of(m.any(axis=0))
        add("变体·条宽 %.0f/间隙 %.0f：实测 %d×%d、条宽 %s、合计宽 %d"
            % (bw, gp, b[2] - b[0] + 1, b[3] - b[1] + 1, [c[2] for c in cols], b[2] - b[0] + 1),
            "%dx%d %s" % (b[2] - b[0] + 1, b[3] - b[1] + 1, cols),
            (b[2] - b[0] + 1, b[3] - b[1] + 1) == (48, 54)
            and [c[2] for c in cols] == [int(bw), int(bw)]
            and cols[1][0] - cols[0][1] - 1 == int(gp))

    # ── C2. 播放窗语义断言 ────────────────────────────────────────
    pa = np.asarray(built["x_ui_playwin_bg.png"][0])
    corners = [int(pa[0, 0, 3]), int(pa[0, -1, 3]), int(pa[-1, 0, 3]), int(pa[-1, -1, 3])]
    cen = int(pa[WIN_H // 2, WIN_W // 2, 3])
    n_edge = int(((pa[:, :, 3] > 200) & (np.abs(pa[:, :, 0].astype(int) - 108) < 14)
                  & (np.abs(pa[:, :, 1].astype(int) - 145) < 14)
                  & (np.abs(pa[:, :, 2].astype(int) - 190) < 14)).sum())
    add("播放窗 4 角 α == 0", corners, corners == [0, 0, 0, 0])
    add("播放窗中心 α > 240", cen, cen > 240)
    add("播放窗细蓝边像素数 > 300", n_edge, n_edge > 300)

    # ── 写盘 ─────────────────────────────────────────────────────
    if write and not fails:
        os.makedirs(EVID, exist_ok=True)
        for name, (im, b1) in built.items():
            p = os.path.join(OUT, name)
            if not os.path.exists(p) or open(p, "rb").read() != b1:
                im.save(p, "PNG", optimize=True)

    # ── D2. 写后：全库既有件未变 ─────────────────────────────────
    man1 = ui_manifest()
    added = sorted(set(man1) - set(man0))
    removed = sorted(set(man0) - set(man1))
    changed = sorted(k for k in set(man0) & set(man1) if man0[k] != man1[k])
    if write and not fails:
        # 首跑：新增 == 4 件；重跑：新增 == 0（幂等）。两种情形都必须「修改 0 / 删除 0」，
        # 且**新增集合只能是本批这 4 个名字**（含子集关系，故重跑也成立）。
        add("全库既有素材未变（修改 0 / 删除 0；新增 ⊆ 本批 4 件）",
            "新增 %s ｜ 修改 %d ｜ 删除 %d" % (added, len(changed), len(removed)),
            set(added) <= set(NEW_FILES) and not changed and not removed)
    for nm, want in BASE_MD5.items():
        add("母本 md5 未变（写后）· %s" % nm, man1.get(nm), man1.get(nm) == want)

    # ── 证据落盘 ─────────────────────────────────────────────────
    if write:
        os.makedirs(EVID, exist_ok=True)
        with open(os.path.join(EVID, "素材实测.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("文件\t期望尺寸\t实测尺寸\tmode\t透明像素\t半透明像素\t不透明像素"
                    "\t最外1px帧αmax\t写前状态\tmd5\n")
            for r in rows:
                f.write("\t".join([r["name"], r["exp"], r["size"], r["mode"], str(r["t"]),
                                   str(r["s"]), str(r["o"]), str(r["cut"]), r["before"],
                                   r["md5"]]) + "\n")
        with open(os.path.join(EVID, "暂停键逐像素同源自证.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("# 口径：diff = pause_<s> − pbkick_<s>（RGBA 逐通道绝对差）。"
                    "「字形 bbox」= glyph_isolate 量出的 ‖ 与 ▶ 墨迹 bbox 的并集，膨胀 1px 作 AA 晕容差。\n")
            f.write("# 冻结窗口 = 以 119×119 中心为中心、66×60 的居中矩形（冻结书 §A.1）。\n")
            f.write("态\t暂停字形bbox\t暂停字形尺寸\t暂停列段(起-止-宽)\t播放字形bbox\t联合bbox"
                    "\t联合bbox+1px外非零像素\t联合bbox+1px外最大绝对差\t联合bbox外(不膨胀)非零像素"
                    "\t联合bbox外(不膨胀)最大绝对差\t非零差像素总数\t冻结窗口外非零像素"
                    "\t冻结窗口外最大绝对差\t结论\n")
            for r in src_rows:
                f.write("\t".join([
                    r["st"], str(r["bp"]), "%dx%d" % (r["bpw"], r["bph"]),
                    " | ".join("%d-%d-%d" % c for c in r["cols"]), str(r["bt"]), str(r["u"]),
                    str(r["out_cnt"]), str(r["out_max"]), str(r["d0_out"]), str(r["d0_max"]),
                    str(r["nz"]), str(r["fz_cnt"]), str(r["fz_max"]),
                    "PASS" if (r["out_cnt"] == 0 and r["out_max"] == 0 and r["bpw"] == 48
                               and r["bph"] == 54) else "FAIL"]) + "\n")
        make_variant_strip(os.path.join(EVID, "字形对照条_14_16_18.png"))
        make_sidebyside(os.path.join(EVID, "播放↔暂停_同屏对照.png"))
        rp = write_report(res, rows, src_rows, fails, added, changed, removed, man1)
        print("自证报告：%s" % rp)

    # ── 打印 ─────────────────────────────────────────────────────
    print("=" * 104)
    print("m60_make_playwin_and_pause.py · 流程图右栏大改 E1 素材（ISSUE-20260929-02）")
    print("复用 m55 助手：%s ｜ 落点：%s" % (os.path.join(M55_DIR, "m55_make_flow_assets.py"), OUT))
    print("-" * 104)
    print("%-30s %-9s %-5s %8s %7s %7s %7s %8s %8s %8s %s"
          % ("文件", "尺寸", "mode", "字节", "透明", "半透明", "不透明", "剪前帧", "剪后帧", "写前", "md5"))
    for r in rows:
        print("%-30s %-9s %-5s %8d %7d %7d %7d %8d %8d %8s %s"
              % (r["name"], r["size"], r["mode"], r["bytes"], r["t"], r["s"], r["o"],
                 r["raw"], r["cut"], r["before"], r["md5"]))
    print("-" * 104)
    for lab, val, ok in res:
        print("  [%s] %s = %s" % ("OK" if ok else "!!", lab, val))
    print("-" * 104)
    bad = sum(1 for _, _, o in res if not o)
    print("断言 %d 项 ｜ PASS %d ｜ FAIL %d ｜ 结构失败 %d 件"
          % (len(res), len(res) - bad, bad, len(fails)))
    for n, e in fails:
        print("  !! %s：%s" % (n, "; ".join(e)))
    print("结果：**%s**" % ("全部通过" if (bad == 0 and not fails) else "存在失败项"))
    print("=" * 104)
    return 0 if (bad == 0 and not fails) else 1


if __name__ == "__main__":
    sys.exit(run(write="--dry-run" not in sys.argv))
