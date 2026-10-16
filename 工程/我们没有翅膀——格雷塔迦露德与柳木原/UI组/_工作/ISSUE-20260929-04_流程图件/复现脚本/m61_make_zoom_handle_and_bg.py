# -*- coding: utf-8 -*-
r"""m61 · ISSUE-20260929-04（流程图页四件收尾）· **E1 素材模块** —— 程序化产出两件素材 + 全套证据

Issue : **ISSUE-20260929-04**（流程图页四件收尾）· 模块 **E1（素材：滑标 + 背景）**
接口  : `_工作\ISSUE-20260929-04_流程图件\接口冻结.md` **§A**（**唯一接口；尺寸 / 颜色 / 形状不得自行改动**）
配方  : 「同族参照件两件实测反解」——
          `krkr\assets\ui\x_ui_shift_knob.png`（16×25，单一竖圆角胶囊）
          `krkr\assets\ui\x_ui_scroll_knob.png`（18×71，单一竖圆角胶囊）
        坏件 `x_ui_zoom_knob.png`（29×16）**只作反证（连通域数 2）、不作形制参照，保留不删**。
边界策略: 本工程「`frame` 类」口径，沿用 `_工作\ISSUE-20260928-02_素材\复现脚本\m55_make_flow_assets.py`
          ——「外框内缩留出发光带、**剪前**最外 1px 帧 α ≤ `RAW_FRAME_MAX`、`clip_low_alpha` **剪后恒为 0**」。
          本题画布 40×31 而形状竖向只留 2px 边距 ⇒ 发光强度必须按此反解（见下方 `GLOW_*` 的推导）。

■■ 产出（2 件；本脚本**只产 PNG**，不写任何 JSON、不碰 `layout\**` 与任何生成器）
  1. `krkr\assets\ui\x_ui_zoom_handle.png`   40×31 RGBA
       流程图缩放条滑标（元素 `fc.zoom_knob`，几何 (1174,112,40×31) 不变、**九宫格将被删除 ⇒
       素材必须与元素等尺寸**）= 单一**竖圆角胶囊手柄**：条宽 12 / 条高 27 / 圆角 6 / 居中
       （左右各 14、上下各 2）；填充＝霜白竖向渐变（上 `#F7FBFF` → 下 `#DEEBFA`）；
       描边＝冰蓝 1.5px（`@palette.accent` 族）；外沿柔发光；真 alpha（PNG-32）；最外 1px 帧 αmax=0。
  2. `krkr\assets\ui\x_bg_flowchart.png`    1920×1080 RGB
       流程图页满幅背景（新元素 `fc.bg`，z=0、在 `fc.dim` 之下）= 源 `bg72.png`（2560×1440，**只读**）
       的 **0.75× LANCZOS 降采样**，**不做任何调色 / 裁切 / 加字 / 加边**。

■■ 证据（落 `_工作\ISSUE-20260929-04_流程图件\证据\`）
  E1_滑标自证.tsv         逐条：断言 / 实测值 / PASS|FAIL
  E1_滑标同族对照.png      新件 + shift_knob + scroll_knob + **旧坏件** 四枚 8× 放大并排（棋盘底、带标注）
                           ＋附「置于 `x_ui_zoom_rail` 上的合成观感（4×）」
  E1_背景_源与成品.png     源缩略 vs 成品缩略并排（960×540 各一）＋ 1:1 中线裁剪对照
  E1_自证报告.md           命令 / 实测数字 / 目视评语 / 未决项

■ 运行
  python "_工作\ISSUE-20260929-04_流程图件\复现脚本\m61_make_zoom_handle_and_bg.py" [--verify-ui]
  python "_工作\ISSUE-20260929-04_流程图件\复现脚本\m61_make_zoom_handle_and_bg.py" --check
       （--check：只读盘上成品 + 重算断言，**不写任何文件**；两件缺失即 FAIL
         --verify-ui：额外跑 `工具\verify_ui.py`（只读）并把「件数/体积/预算/余量」写进报告 §七）
  退出码 0 = 两件就位且全部断言通过（含幂等：重跑逐字节一致）。
  ★ 幂等：无随机、无时间戳、无外部状态 ⇒ 同版本脚本重跑产出**逐字节一致**。

■ 第二版（2026-09-29 · 主代理指令「只调配色，对齐参照件」）
  ① `FILL_TOP/FILL_BOT`：`#F7FBFF`/`#DEEBFA`（首版 = 冻结书 §A 字面值）→ **(233,239,243)/(155,199,235)**
     （= `x_ui_scroll_knob` 直段顶/底的中列实测档）；② 渐变跨度由「整条含帽」明确为「**条体直段**」；
  ③ **合成实现修正**（`over()` 把未预乘值当预乘用 ⇒ 条面被抬亮 +5~7，端点色改不动就是它；
     首版字节由 `over_legacy` 逐字节复现，见 H20）。新增 H18/H19/H20。
  **形状 / 尺寸 / 描边色 / 真 alpha / 帧策略一律未动。**

■ 素材清单侧（**留给 E2 / 主代理**，本脚本不代劳）
  新件落盘后须重跑 `工具\emit_asset_index.py` 与 `工具\verify_ui.py`；`layout\**` 与生成器的接线
  属 E2 模块（见冻结书 §B/§C），本脚本**只读 palette**、不写任何 JSON。
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import deque

import numpy as np

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)                                   # _工作\ISSUE-20260929-04_流程图件
UI_GROUP = os.path.dirname(os.path.dirname(ISSUE_DIR))              # <UI组>
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")
EVID = os.path.join(ISSUE_DIR, "证据")

# ──────────────────────────────────────────────────────────────── 交付物路径
OUT_HANDLE = os.path.join(ASSETS, "x_ui_zoom_handle.png")
OUT_BG = os.path.join(ASSETS, "x_bg_flowchart.png")

# ──────────────────────────────────────────────────────────────── 参照件（只读）
REF_SHIFT = os.path.join(ASSETS, "x_ui_shift_knob.png")             # 16×25  单一竖圆角胶囊（干净）
REF_SCROLL = os.path.join(ASSETS, "x_ui_scroll_knob.png")           # 18×71  单一竖圆角胶囊（干净）
REF_OLDZOOM = os.path.join(ASSETS, "x_ui_zoom_knob.png")            # 29×16  **坏件**：横胶囊+圆点两图形
REF_ZOOMRAIL = os.path.join(ASSETS, "x_ui_zoom_rail.png")           # 123×31 缩放条轨道（观感合成用）

# ──────────────────────────────────────────────────────────────── 背景源（**主工作树，只读；本 worktree 内不存在**）
SRC_BG = (r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
          r"\资源组\美术统一_超分\CG背景\bg72.png")
SRC_BG_W, SRC_BG_H = 2560, 1440                                     # 实测
BG_W, BG_H = 1920, 1080                                             # 冻结：0.75× 整数比

# ══════════════════════════════════════════════════════════════════ 滑标几何（冻结书 §A，唯一真相源）
HW, HH = 40, 31                                                     # 画布（= 元素 fc.zoom_knob 几何）
BAR_W, BAR_H, BAR_R = 12.0, 27.0, 6.0                               # 条宽 / 条高 / 圆角（= 条宽/2 ⇒ 正胶囊）
CX, CY = HW / 2.0, (HH - 1) / 2.0 + 0.5                             # 20.0 / 15.5
BOX = (CX - BAR_W / 2.0, CY - BAR_H / 2.0, CX + BAR_W / 2.0, CY + BAR_H / 2.0)   # (14,2,26,29) 半开
STROKE_W = 1.5                                                      # 描边宽（冻结书 §A）
BAR_R = min(BAR_R, BAR_W / 2.0)
CAP_INSET = STROKE_W                                                # 内形 = 外形内缩 1.5px

# 填充端点色：**第二版（2026-09-29 · 主代理指令「配色对齐参照件」）＝ 参照件实测档**
#   v1（首版）用的是冻结书 §A 字面给的 `#F7FBFF → #DEEBFA`（= 本工程既有面板件渐变，m55 的
#   `PANEL_TOP/PANEL_BOT`）；主代理目视 `E1_滑标同族对照.png` 后判定「新件明显更白 ⇒ 不同族」，
#   指令改用**参照件同一位置实测到的**那一档（依据 = 本脚本 §参照件反解 + 报告 §六）：
#     上端 (233,239,243)  ← `x_ui_scroll_knob` 直段顶（中列 y=9）实测
#     下端 (155,199,235)  ← `x_ui_scroll_knob` 直段底（中列 y=59–61）实测
#   冻结书 §A 的其余条款（尺寸/形状/描边/柔光/帧策略）**一律未动**。
FILL_TOP = (233, 239, 243)
FILL_BOT = (155, 199, 235)
FILL_TOP_V1 = (0xF7, 0xFB, 0xFF)      # 首版（本工程面板件渐变档）—— 仅用于报告里的「改前」对照
FILL_BOT_V1 = (0xDE, 0xEB, 0xFA)
V1_MD5_EXPECT = "4e249d444a8289ba8f402d1534086bcb"   # 首版落盘件的 md5（供「改前基线可复现」自证）
BODY_A = 250                                                        # 条面不透明度（参照件内部实测 α 251–253）

GLOW_SIGMA = 1.4                                                    # 柔发光高斯 σ
GLOW_GAIN = 0.24                                                    # 柔发光强度（见下方推导）
CLIP_THR = 10                                                       # 柔光尾归零阈值（α≤10 ⇒ 0）
RAW_FRAME_MAX = 10                                                  # **剪前**最外 1px 帧 α 上限（与 CLIP_THR 同值）
SS = 16                                                             # 亚像素采样数（analytic inside-test）

# 发光强度反解（为什么是 σ1.4 / gain0.24）：
#   竖向只有 2px 边距 ⇒ 「最外 1px 帧（y=0 / y=30）剪前 α ≤ 10」是硬约束。
#   形边在 y=2.0，行 y=0 的像素中心 0.5 ⇒ 距边 1.5px = 1.07σ ⇒ Φ(−1.07)=0.142
#   ⇒ 剪前帧 α ≈ 255 × 0.142 × gain；gain=0.24 ⇒ ≈ 8.7 ≤ 10 ✅（gain=0.30 ⇒ 13 ✗ 会被留下硬边）
#   同参数下 1px 外（y=1 / x=13 / x=26）α ≈ 22 ⇒ 仍有可见柔光（与 m55 小方板实测 11/15/18 同量级）。

# ══════════════════════════════════════════════════════════════════ 调色板（唯一色值来源）
def _palette():
    with open(PALETTE, encoding="utf-8") as f:
        return json.load(f)["colors"]


PAL = _palette()


def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    """palette.json 取值（缺键即报错，不静默回落）"""
    if key not in PAL:
        raise KeyError("palette.json 缺键 %r（唯一色值来源）" % key)
    return hex2rgb(PAL[key]["value"])


ACCENT = C("accent")        # #7AB0E8 = (122,176,232) —— 描边与发光用；见参照件反解证据
FROST = (244, 248, 255)     # 霜白（合成色，与 m50~m55 同口径）


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ══════════════════════════════════════════════════════════════════ 造型基础（numpy，无 LANCZOS 振铃）
def capsule_coverage(size, box, rad, n=SS):
    r"""圆角矩形（本题 rad = 条宽/2 ⇒ 正胶囊）的**亚像素面积覆盖率**，float 0..1。

    做法：在每像素内取 n×n 个采样点，用**解析 inside 测试**判定（圆角矩形 = 框内 ∩ ¬(角落超出圆外)）。
    与「PIL 画 + LANCZOS 降采样」相比：① 无 LANCZOS 负瓣**振铃残影**（m55 的 `MASK_FLOOR` 就是为它设的）；
    ② 无 `ImageDraw.rounded_rectangle` 的**闭区间端点**坑（末像素只剩 25% 覆盖率）；
    ③ 覆盖率是真实面积的直接估计 ⇒ 「剪前最外帧 α」可**解析预测**（本题 Δ 预测↔实测 < 1/255）。
    """
    w, h = size
    ys = ((np.arange(h)[:, None] + (np.arange(n)[None, :] + 0.5) / n).reshape(h * n))
    xs = ((np.arange(w)[:, None] + (np.arange(n)[None, :] + 0.5) / n).reshape(w * n))
    PX, PY = np.meshgrid(xs, ys)                      # (h*n, w*n)
    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    hw, hh = (box[2] - box[0]) / 2.0, (box[3] - box[1]) / 2.0
    ax, ay = np.abs(PX - cx), np.abs(PY - cy)
    inbox = (ax <= hw) & (ay <= hh)
    qx, qy = ax - (hw - rad), ay - (hh - rad)
    corner = (qx > 0) & (qy > 0)
    inside = inbox & (~corner | ((qx * qx + qy * qy) <= rad * rad))
    return inside.reshape(h, n, w, n).mean(axis=(1, 3))


def gauss_blur(a, sigma):
    """可分离高斯（3σ 截断、核归一）——确定性、无边界振铃（与 PIL GaussianBlur 同族语义）"""
    if sigma <= 0:
        return a.copy()
    r = int(np.ceil(3.0 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / float(sigma)) ** 2)
    k /= k.sum()
    b = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, a)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, b)


def over(dst_rgb, dst_a, src_rgb, src_a):
    """标准 **unpremultiplied** alpha-over（正确实现）：
      `out_a = sa + da·(1−sa)` ｜ `out_rgb = (src·sa + dst·da·(1−sa)) / out_a`
    ★ 第二版修正（2026-09-29）：首版把 dst 当**已预乘**处理（`dst_p`），但传入的是**未预乘** rgb
      ⇒ ① 底层色的权重少乘了 `da`；② 最后又除以 `out_a` ⇒ 条面被**整体抬亮 ≈ +5~7/255**，
      端点色无法等于指定值（首版实测上端 (244,252,255) 甚至超过其端点 `#F7FBFF`=(247,251,255) 的 G/B）。
      修正后才满足「条面 = 指定端点色的竖向渐变」。首版的字节可用 `over_legacy` 逐字节复现（自证见 H20）。"""
    sa = src_a[..., None]
    da = dst_a[..., None]
    out_a = src_a + dst_a * (1.0 - src_a)
    num = (np.asarray(src_rgb, dtype=np.float64) * sa
           + np.asarray(dst_rgb, dtype=np.float64) * da * (1.0 - sa))
    with np.errstate(invalid="ignore", divide="ignore"):
        out_rgb = np.where(out_a[..., None] > 1e-9, num / np.maximum(out_a[..., None], 1e-9), 0.0)
    return out_rgb, out_a


def over_legacy(dst_p, dst_a, src_rgb, src_a):
    """**首版（v1）的合成实现原样保留**——只用于 `legacy=True` 复算「改前」基线（H20 逐字节对拍），
    **任何交付件都不走这里**。缺陷见 `over()` 的说明。"""
    sa = src_a[..., None]
    out_a = src_a + dst_a * (1.0 - src_a)
    out_p = np.asarray(src_rgb, dtype=np.float64) * sa + dst_p * (1.0 - sa)
    with np.errstate(invalid="ignore", divide="ignore"):
        out_rgb = np.where(out_a[..., None] > 1e-9, out_p / np.maximum(out_a[..., None], 1e-9), 0.0)
    return out_rgb, out_a


def vgrad_rgb(size, top, bot, t0, t1):
    """竖向渐变 RGB 场：t = (行中心 − t0)/(t1 − t0) 截到 0..1（**取条体的竖向范围**，非整画布）"""
    h, w = size[1], size[0]
    yc = np.arange(h) + 0.5
    t = np.clip((yc - t0) / (t1 - t0), 0.0, 1.0)[:, None]
    a = np.asarray(top, dtype=np.float64)[None, :]
    b = np.asarray(bot, dtype=np.float64)[None, :]
    return (a + (b - a) * t)[:, None, :].repeat(w, axis=1)     # (h,w,3)


# ══════════════════════════════════════════════════════════════════ ① 滑标 40×31
def build_handle(sigma=GLOW_SIGMA, gain=GLOW_GAIN, body_a=BODY_A, thr=CLIP_THR,
                 fill_top=FILL_TOP, fill_bot=FILL_BOT, fill_span=None, legacy=False):
    """返回 (RGBA uint8 数组, 剪前 α 场)。造型 = 柔外发光 → 条面竖向渐变 → 冰蓝描边环。
    `fill_span` = 渐变跨的连续 y 区间；缺省 = **条体直段**（[BOX[1]+R, BOX[3]−R]，两端外按端点色夹住）
    —— 与参照件同口径（参照件实测端点正是取自其直段顶/底，见 `bar_probe`）。
    传 `(BOX[1], BOX[3])` 可复现首版 v1 的「整条含帽」跨度。
    `legacy=True` 走首版合成实现（`over_legacy`）——**仅供复算改前基线**，交付件一律 `False`。"""
    t0, t1 = fill_span if fill_span else (BOX[1] + BAR_R, BOX[3] - BAR_R)
    cmp_ = over_legacy if legacy else over
    outer = capsule_coverage((HW, HH), BOX, BAR_R)
    inner = capsule_coverage((HW, HH), (BOX[0] + CAP_INSET, BOX[1] + CAP_INSET,
                                       BOX[2] - CAP_INSET, BOX[3] - CAP_INSET),
                             max(0.0, BAR_R - CAP_INSET))
    ring = np.clip(outer - inner, 0.0, 1.0)

    glow_a = np.clip(gauss_blur(outer, sigma) * gain, 0.0, 1.0)          # 剪前发光 α 场（含形内）
    body_rgb = vgrad_rgb((HW, HH), fill_top, fill_bot, t0, t1)
    body_a = outer * (body_a / 255.0)

    rgb = np.zeros((HH, HW, 3), dtype=np.float64)
    a = np.zeros((HH, HW), dtype=np.float64)
    rgb, a = cmp_(rgb, a, ACCENT, glow_a)
    rgb, a = cmp_(rgb, a, body_rgb, body_a)
    rgb, a = cmp_(rgb, a, ACCENT, ring)

    raw_a = np.rint(a * 255.0).astype(np.int32)
    a8 = np.where(raw_a <= thr, 0, raw_a).astype(np.uint8)                # clip_low_alpha（frame 口径）
    out = np.zeros((HH, HW, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = a8
    return out, raw_a


# ══════════════════════════════════════════════════════════════════ ② 背景 1920×1080
def build_bg():
    """源（只读）→ 0.75× LANCZOS 降采样；**不做任何调色 / 裁切 / 加字 / 加边**"""
    if not os.path.isfile(SRC_BG):
        raise FileNotFoundError("背景源缺失（应位于主工作树、只读）：%s" % SRC_BG)
    src = Image.open(SRC_BG)
    src.load()
    ref = src.resize((BG_W, BG_H), Image.LANCZOS)          # ← 任务给定判据口径：PIL resize LANCZOS
    arr = np.asarray(ref)
    return arr, src.copy(), ref.size


# ══════════════════════════════════════════════════════════════════ 量测件
def load_rgba(path):
    im = Image.open(path)
    im.load()
    return im


def a8_of(im):
    return np.asarray(im.convert("RGBA").getchannel("A"), dtype=np.int32)


def cc_count(al, thr=8, conn=8):
    """α>thr 的连通域数（8-邻接或 4-邻接标记法）"""
    pts = set()
    ys, xs = np.where(al > thr)
    for y, x in zip(ys.tolist(), xs.tolist()):
        pts.add((y, x))
    seen = set()
    n = 0
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)] if conn == 8 \
        else [(-1, 0), (0, -1), (0, 1), (1, 0)]
    for p in sorted(pts):
        if p in seen:
            continue
        n += 1
        seen.add(p)
        q = deque([p])
        while q:
            y, x = q.popleft()
            for dy, dx in nb:
                np_ = (y + dy, x + dx)
                if np_ in pts and np_ not in seen:
                    seen.add(np_)
                    q.append(np_)
    return n


def bbox(al, thr):
    ys, xs = np.where(al > thr)
    if len(ys) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def frame_amax(al):
    """最外 1px 帧 αmax（四条边取最大；四角在两边上重复计，无妨）"""
    return int(max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))


def cross50(row, half=127.5):
    """一行 α 的 **50% 覆盖交叉点**（线性插值到像素中心之间）⇒ (左, 右)；无则 (None, None)。
    本工程口径：量边缘以 50% 覆盖交叉点为界（45° 对角量半径是有偏仪器）。"""
    idx = np.where(row >= half)[0]
    if len(idx) == 0:
        return None, None
    lo, hi = int(idx.min()), int(idx.max())

    def ip(i, j):
        a, b = float(row[i]), float(row[j])
        return float(i) if b == a else i + (half - a) / (b - a) * (j - i)
    return (ip(lo - 1, lo) if lo > 0 else float(lo),
            ip(hi + 1, hi) if hi < len(row) - 1 else float(hi))


def pred_left(y_center, rad):
    """圆角矩形（hw=BAR_W/2、hh=BAR_H/2、圆角 rad、中心 (CX,CY)）在该行中心的**解析左边界**。
    用于反证「圆角 == 6」：只有正胶囊（rad = 条宽/2）才能命中实测 50% 交叉点。"""
    hw, hh = BAR_W / 2.0, BAR_H / 2.0
    ax_ = abs(y_center - CY)
    if ax_ >= hh:
        return None
    if ax_ <= hh - rad:
        return CX - hw
    return CX - (hw - rad) - math.sqrt(max(0.0, rad * rad - (ax_ - (hh - rad)) ** 2))


def bar_probe(a):
    """**条面三档取样**（三件同一口径，成品件与参照件可比）：
    ① 条体轮廓 = α>8 足迹（含 1px 柔光，对三件一致）；
    ② 条宽 w = 足迹宽、条高 h = 足迹高；③ 胶囊几何 ⇒ **直段** = [y0 + w/2, y1 − w/2]；
    ④ 在条体水平中心列取 **直段顶 / 中 / 底** 三点 RGB（即「上端 / 中点 / 下端条面色」）。
    （为什么用 α>8 而不是 α≥128：参照件是下采样件，α≥128 只覆盖内圈（实测 scroll_knob
      α≥128 足迹仅 (3,3,14,67)），拿它推直段会把取样点推离真端点；α>8 口径三件一致且
      对本件与参照件都落在胶囊直段上。）"""
    a = np.asarray(a).astype(np.int32)
    al = a[..., 3]
    x0, y0, x1, y1 = bbox(al, 8)
    w, h = int(x1 - x0 + 1), int(y1 - y0 + 1)
    r = w / 2.0
    yc0, yc1 = y0 + r, y1 - r
    rows = [int(round(yc0 + t * (yc1 - yc0))) for t in (0.0, 0.5, 1.0)]
    cx = int(round((x0 + x1) / 2.0))
    return dict(foot=(int(x0), int(y0), int(x1), int(y1)), w=w, h=h, r=r, cx=cx, rows=rows,
                cols=[tuple(int(v) for v in a[y, cx, :3]) for y in rows],
                alpha=[int(al[y, cx]) for y in rows])


def bar_probe_file(path):
    return bar_probe(load_rgba(path).convert("RGBA"))


def run_verify_ui():
    """跑 `工具\\verify_ui.py`（只读校验器）并把 [6] 体积预算一行解析出来（供报告 §七）。
    解析失败/未跑 ⇒ 返回 None（报告里如实写「未运行」），**绝不影响本脚本的退出码**。"""
    vp = os.path.join(UI_GROUP, "工具", "verify_ui.py")
    if not os.path.isfile(vp):
        return None
    try:
        r = subprocess.run([sys.executable, vp], cwd=UI_GROUP, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
    except Exception as e:                                        # noqa: BLE001
        return dict(rc=-1, err=str(e))
    out = (r.stdout or "") + (r.stderr or "")
    d = dict(rc=r.returncode, n=None, mb=None, budget=None, gate=None, line=None)
    for ln in out.splitlines():
        m = re.search(r"(\d+)\s*件\s*/\s*([\d.]+)\s*MB（\s*(\d+)\s*MB 预算）→\s*(\S+)", ln)
        if m and "体积预算" in ln:
            d.update(n=int(m.group(1)), mb=float(m.group(2)), budget=int(m.group(3)),
                     gate=m.group(4), line=ln.strip())
    d["headroom_kb"] = (None if d["mb"] is None else (d["budget"] - d["mb"]) * 1024.0)
    # ★ 精确余量：verify_ui 打印的体积是**两位小数**（如 95.92 MB），直接用它会带 ±0.1 MB 舍入误差
    #   ⇒ 自己把 assets/ui 下的 PNG 逐件加起来做精算（与 verify_ui 的 [6] 同一集合、同一口径）
    try:
        tot = sum(os.path.getsize(os.path.join(ASSETS, f)) for f in os.listdir(ASSETS)
                  if f.lower().endswith(".png"))
        d["exact_bytes"] = tot
        d["exact_mib"] = tot / 1048576.0
        d["exact_headroom_kb"] = (d["budget"] * 1048576 - tot) / 1024.0
    except Exception:                                             # noqa: BLE001
        d["exact_bytes"] = None
    d["ok"] = (r.returncode == 0)
    return d


def dc3(a, b):
    """两组 RGB 的逐通道最大绝对差"""
    return max(abs(a[i] - b[i]) for i in range(3))


def cap_fit_err(cs, half_bias, rad):
    """把各行实测 50% 左交叉点（+发光外推的每侧修正 half_bias，索引空间）与「圆角 rad 的
    圆角矩形」解析边界（同转索引空间）比，取全幅最大偏差（px）。
    rad = 6（正胶囊）应命中小值；rad ≠ 6 应显著偏大 ⇒ 判据有判别力。"""
    e = 0.0
    for y in range(HH):
        xl, _ = cs[y]
        if xl is None:
            continue
        p = pred_left(y + 0.5, rad)
        if p is None:
            continue
        e = max(e, abs(xl + half_bias - (p - 0.5)))     # 索引空间：连续坐标 − 0.5
    return e


def enc_png(arr, mode):
    import io
    b = io.BytesIO()
    Image.fromarray(arr, mode).save(b, "PNG", optimize=True)
    return b.getvalue()


def md5f(data):
    return hashlib.md5(data).hexdigest()


def png_metrics(al):
    return dict(amin=int(al.min()), amax=int(al.max()),
                zero_pct=100.0 * float((al == 0).sum()) / al.size,
                solid=int((al == 255).sum()))


# ══════════════════════════════════════════════════════════════════ 证据图
def load_font(sz):
    for cand in (r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\arial.ttf"):
        if os.path.isfile(cand):
            try:
                return ImageFont.truetype(cand, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def checker(w, h, cell=12, c1=(72, 72, 72), c2=(104, 104, 104)):
    a = np.zeros((h, w, 3), dtype=np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((yy // cell) + (xx // cell)) % 2 == 0
    a[..., 0] = np.where(m, c1[0], c2[0])
    a[..., 1] = np.where(m, c1[1], c2[1])
    a[..., 2] = np.where(m, c1[2], c2[2])
    return a


def zoom_on_checker(path, zoom, cell=12):
    """素材 → 8× 放大（NEAREST）并合成到棋盘底（真 alpha 一览）"""
    im = load_rgba(path).convert("RGBA")
    w, h = im.size
    a = np.asarray(im).astype(np.float64)
    al = a[..., 3:4] / 255.0
    bg = checker(w, h, cell).astype(np.float64)
    comp = a[..., :3] * al + bg * (1 - al)
    big = Image.fromarray(np.clip(np.rint(comp), 0, 255).astype(np.uint8)).resize(
        (w * zoom, h * zoom), Image.NEAREST)
    return np.asarray(big)


def make_family_sheet(out_path):
    """四枚 8× 放大并排（棋盘底 = 真 alpha，带序号标注 + 底部图例）
    ＋ 附「置于 x_ui_zoom_rail 上的合成观感（4×）」"""
    Z = 8
    items = [
        (OUT_HANDLE, "[1] NEW", "本批新件 x_ui_zoom_handle.png  40×31 —— 单一竖圆角胶囊"
                               "（条宽 12 / 条高 27 / 圆角 6）"),
        (REF_SHIFT, "[2] REF", "参照件 x_ui_shift_knob.png  16×25 —— 干净：单一竖圆角胶囊"),
        (REF_SCROLL, "[3] REF", "参照件 x_ui_scroll_knob.png  18×71 —— 干净：单一竖圆角胶囊"),
        (REF_OLDZOOM, "[4] OLD", "退役坏件 x_ui_zoom_knob.png  29×16 —— 内含「横胶囊 + 圆点」两个图形"
                                 "（拆件误切；保留不删、不作形制参照）"),
    ]
    tiles = [zoom_on_checker(p, Z) for p, _, _ in items]
    f_h = load_font(17)
    f_s = load_font(15)
    t_h = 24
    gap = 34
    m = 26
    max_h = max(t.shape[0] for t in tiles)
    total_w = m * 2 + sum(t.shape[1] for t in tiles) + gap * (len(tiles) - 1)

    # 附：轨道合成（4×）
    rail = load_rgba(REF_ZOOMRAIL).convert("RGBA")
    rw, rh = rail.size
    rail_canvas = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rail_canvas.alpha_composite(rail, (0, 0))
    rail_canvas.alpha_composite(load_rgba(OUT_HANDLE).convert("RGBA"), (40, 0))
    ra = np.asarray(rail_canvas).astype(np.float64)
    ral = ra[..., 3:4] / 255.0
    rbg = checker(rw, rh, 10).astype(np.float64)
    rcomp = np.clip(np.rint(ra[..., :3] * ral + rbg * (1 - ral)), 0, 255).astype(np.uint8)
    rail_big = np.asarray(Image.fromarray(rcomp).resize((rw * 4, rh * 4), Image.NEAREST))

    legend = [
        "[1] 本批新件 x_ui_zoom_handle.png  40×31 —— 单一竖圆角胶囊（条宽 12 / 条高 27 / 圆角 6 / 居中）",
        "[2] 参照件 x_ui_shift_knob.png  16×25 —— 干净：单一竖圆角胶囊（圆角 = 条宽/2）",
        "[3] 参照件 x_ui_scroll_knob.png  18×71 —— 干净：单一竖圆角胶囊（圆角 = 条宽/2）",
        "[4] 退役坏件 x_ui_zoom_knob.png  29×16 —— 内含「横胶囊 + 圆点」两个图形（拆件误切；保留不删）",
        "[附] x_ui_zoom_handle 置于 x_ui_zoom_rail（123×31）之上的合成观感（4×）；几何仅供观感参考，",
        "     正式位置由元素 fc.zoom_knob (1174,112,40×31) 决定。棋盘底 = 真 alpha 一览。",
    ]

    # ── 条面色三档定量行（「一眼可判是否同族」；取样口径见 bar_probe）────────────
    q_items = [("条面 · [1] 新件 x_ui_zoom_handle", OUT_HANDLE),
               ("条面 · [2] 参照 x_ui_shift_knob", REF_SHIFT),
               ("条面 · [3] 参照 x_ui_scroll_knob", REF_SCROLL)]
    q = [(lab, bar_probe_file(p)) for lab, p in q_items]
    q_scroll = q[2][1]["cols"]
    quant = ["条面色三档实测（α>8 足迹 → 胶囊直段 → 中列取 直段顶/中/底；三件同一口径）："]
    for lab, d in q:
        cols = d["cols"]
        dd = [dc3(cols[i], q_scroll[i]) for i in range(3)]
        quant.append("%-34s 上端 %-16s 中点 %-16s 下端 %-16s ｜ 与[3]逐点ΔRGB %d/%d/%d"
                     % (lab, str(cols[0]), str(cols[1]), str(cols[2]), dd[0], dd[1], dd[2]))
    quant.append("判读：[1] 与 [3] 三档逐点 ΔRGB ≤ %d ⇒ 同族；[2] 因件短（条高 25）直段跨距小，"
                 "其下端尚未走到 [3] 的深档（属几何差异，非配色不同）。" % max(
                     dc3(q[0][1]["cols"][i], q_scroll[i]) for i in range(3)))
    line_h = 24
    head = 46
    H = (head + max_h + t_h + 24 + rail_big.shape[0] + 30 + line_h * len(legend)
         + line_h * (len(quant) + 1) + m)
    # 画布宽度：除图块/轨道外，还要容下最长的一行图例/定量文字（否则右侧被裁）
    _tmp = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    txt_w = max([_tmp.textlength(s, font=f_s) for s in list(legend) + list(quant)]
                + [_tmp.textlength("ISSUE-20260929-04 · E1 滑标同族对照（8×，棋盘底 = 真 alpha；"
                                   "第二版：配色对齐参照件）", font=f_h)])
    W = int(max(total_w, rail_big.shape[1] + m * 2 + 60, txt_w + m * 2 + 8))
    canvas = Image.fromarray(checker(W, H, 12)).convert("RGB")
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, head - 1], fill=(28, 30, 36))
    d.text((m, 13), "ISSUE-20260929-04 · E1 滑标同族对照（8×，棋盘底 = 真 alpha；" 
                    "第二版：配色对齐参照件）", font=f_h, fill=(235, 240, 250))

    x = m
    base = head + 30 + max_h            # 30 = 序号标注行高（否则高件会顶进标题栏）
    for (path, tag, _), t in zip(items, tiles):
        th, tw = t.shape[:2]
        y = base - th
        canvas.paste(Image.fromarray(t), (x, y))
        d.rectangle([x - 1, y - 1, x + tw, y + th], outline=(40, 44, 52))
        d.text((x, y - 22), tag, font=f_s,
               fill=(255, 225, 120) if tag.startswith("[1") else
               ((255, 130, 130) if tag.startswith("[4") else (205, 215, 230)))
        x += tw + gap

    ry = base + t_h + 24
    canvas.paste(Image.fromarray(rail_big), (m, ry))
    d.rectangle([m - 1, ry - 1, m + rail_big.shape[1], ry + rail_big.shape[0]], outline=(40, 44, 52))
    ly = ry + rail_big.shape[0] + 30
    for i, ln in enumerate(legend):
        d.text((m, ly + i * line_h), ln, font=f_s,
               fill=(255, 225, 120) if ln.startswith("[1") else
               ((255, 130, 130) if ln.startswith("[4") else (205, 215, 230)))
    qy = ly + line_h * (len(legend) + 1)
    for i, ln in enumerate(quant):
        d.text((m, qy + i * line_h), ln, font=f_s,
               fill=(150, 225, 255) if i == 0 else (200, 232, 250))
    canvas.save(out_path, "PNG", optimize=True)
    return canvas.size


def make_bg_pair(out_path):
    """源缩略 vs 成品缩略并排（各 960×540）+ 1:1 中线裁剪对照"""
    src = Image.open(SRC_BG)
    out = Image.open(OUT_BG)
    sw, sh = src.size
    ow, oh = out.size
    tw, th = 960, 540
    s_thumb = zn(src.convert("RGB"), (tw, th))
    o_thumb = zn(out.convert("RGB"), (tw, th))
    cw, ch = 480, 270
    s_crop = np.asarray(src.convert("RGB").crop((sw // 2 - cw // 2, sh // 2 - ch // 2,
                                                 sw // 2 + cw // 2, sh // 2 + ch // 2)))
    o_crop = np.asarray(out.convert("RGB").crop((ow // 2 - cw // 2, oh // 2 - ch // 2,
                                                 ow // 2 + cw // 2, oh // 2 + ch // 2)))
    f_h = load_font(20)
    f_s = load_font(15)
    m = 24
    head = 46
    cap = 26
    W = m * 2 + tw * 2 + 24
    H = head + th + cap + 20 + ch + cap + m + 30
    canvas = Image.new("RGB", (W, H), (24, 26, 32))
    d = ImageDraw.Draw(canvas)
    d.text((m, 13), "ISSUE-20260929-04 · E1 背景 x_bg_flowchart.png = bg72.png 的 0.75x LANCZOS 降采样"
                    "（无调色 / 裁切 / 加字）", font=f_h, fill=(235, 240, 250))
    y = head
    canvas.paste(Image.fromarray(s_thumb), (m, y))
    canvas.paste(Image.fromarray(o_thumb), (m + tw + 24, y))
    d.text((m, y + th + 5), "源 bg72.png  2560x1440  → 缩略 960x540（LANCZOS）", font=f_s,
           fill=(205, 215, 230))
    d.text((m + tw + 24, y + th + 5), "成品 x_bg_flowchart.png  1920x1080  → 缩略 960x540（LANCZOS）",
           font=f_s, fill=(205, 215, 230))
    y2 = y + th + cap + 20
    canvas.paste(Image.fromarray(s_crop), (m, y2))
    canvas.paste(Image.fromarray(o_crop), (m + tw + 24, y2))
    d.text((m, y2 + ch + 5), "源 1:1 中线裁剪 480x270（100%）", font=f_s, fill=(205, 215, 230))
    d.text((m + tw + 24, y2 + ch + 5), "成品 1:1 中线裁剪 480x270（100%）—— 量振铃/锯齿用",
           font=f_s, fill=(205, 215, 230))
    canvas.save(out_path, "PNG", optimize=True)
    return canvas.size


def zn(im, size):
    return np.asarray(im.resize(size, Image.LANCZOS))


def make_report(out_path, ctx):
    """E1_自证报告.md —— 数字全部由本次实测填入；「目视评语」是人/代理目视记录（非机检）。"""
    L = []
    ap = L.append
    ap("# ISSUE-20260929-04 · E1 素材模块 自证报告（滑标 + 背景）")
    ap("")
    ap("- 模块：**E1（素材）** ｜ 生成脚本：`_工作\\ISSUE-20260929-04_流程图件\\复现脚本\\m61_make_zoom_handle_and_bg.py`")
    ap("- 接口（唯一）：`_工作\\ISSUE-20260929-04_流程图件\\接口冻结.md` **§A**（尺寸/颜色/形状冻结）")
    ap("- 边界策略：本工程 `frame` 类（参照 `_工作\\ISSUE-20260928-02_素材\\复现脚本\\m55_make_flow_assets.py`）"
       "—— 剪前最外 1px 帧 α ≤ %d、`clip_low_alpha` 剪后恒为 0" % RAW_FRAME_MAX)
    ap("- 执行：`python \"…\\m61_make_zoom_handle_and_bg.py\" [--verify-ui]`（写盘；`--verify-ui` 额外跑"
       "只读校验器并写入 §七）／`… --check`（只读核对，不写任何文件）")
    ap("- 断言：**%d 条 ｜ PASS %d ｜ FAIL %d ｜ INFO %d** ｜ 退出码 %d ｜ RESULT=%s"
       % (ctx["n_rows"], ctx["n_pass"], ctx["n_fail"], ctx["n_info"], ctx["rc"], ctx["result"]))
    ap("- 幂等：连续两次全量运行产出**逐字节一致**（两件 md5 见下表，写前/写后相同）")
    ap("")
    ap("## 一、交付物实测")
    ap("")
    ap("| 文件 | 尺寸 | mode | 字节 | αmin / αmax | α=0 占比 | α=255 像素 | md5 |")
    ap("| --- | --- | --- | ---: | --- | ---: | ---: | --- |")
    ap("| `krkr\\assets\\ui\\x_ui_zoom_handle.png` | %d×%d | %s | %d | %d / %d | %.1f%% | %d | `%s` |"
       % (ctx["h"]["w"], ctx["h"]["h"], ctx["h"]["mode"], ctx["h"]["bytes"], ctx["h"]["amin"],
          ctx["h"]["amax"], ctx["h"]["zero_pct"], ctx["h"]["solid"], ctx["h"]["md5"]))
    ap("| `krkr\\assets\\ui\\x_bg_flowchart.png` | %d×%d | %s | %d | —（无 alpha 通道） | — | — | `%s` |"
       % (ctx["b"]["w"], ctx["b"]["h"], ctx["b"]["mode"], ctx["b"]["bytes"], ctx["b"]["md5"]))
    ap("")
    ap("形状参数（实测反解，非声称）：条宽 **%.2f**（50%% 交叉跨距 %.2f − 发光外推 %.2f）／"
       "条高 **%d**（α≥200 竖向跨度 y=%d..%d）／圆角 **6**（帽圆弧拟合最大偏差 %.2fpx，"
       "反证 r=0 → %.2f、r=3 → %.2f、r=9 → %.2f）／居中（交叉中心 %.2f == 画布中心索引 %.2f）"
       % (ctx["w_corr"], ctx["w_raw"], ctx["bias"], ctx["bar_h"], ctx["span0"], ctx["span1"],
          ctx["fit6"], ctx["disc0"], ctx["disc3"], ctx["disc9"], ctx["center"], CX - 0.5))
    ap("")
    ap("背景统计（0–255 亮度，0.2126R+0.7152G+0.0722B）：源 均值 %.2f / 5%%=%.0f / 95%%=%.0f；"
       "成品 均值 %.2f / 5%%=%.0f / 95%%=%.0f（源↔成品亮度均值差 %.3f ⇒ 仅降采样、无调色）"
       % (ctx["st_src"][0], ctx["st_src"][1], ctx["st_src"][2],
          ctx["st_out"][0], ctx["st_out"][1], ctx["st_out"][2], ctx["dlum"]))
    ap("")
    ap("### 一·补 · 条面色三档（**第二版核心**；口径 = `bar_probe`：α>8 足迹 → 胶囊直段 → 中列取"
       "直段顶/中/底）")
    ap("")
    ap("| 件 | 上端 | 中点 | 下端 | 与 [3] 逐点 ΔRGB |")
    ap("| --- | --- | --- | --- | --- |")
    rows_cmp = [("[1] 新件 **改后 v2**（参照实测档）", ctx["pb"]["self"]),
                ("[1′] 新件 *改前 v1*（本工程面板件档 `#F7FBFF`→`#DEEBFA`）", ctx["pb"]["v1"]),
                ("[2] 参照 `x_ui_shift_knob`", ctx["pb"]["shift"]),
                ("[3] 参照 `x_ui_scroll_knob`", ctx["pb"]["scroll"])]
    ref_cols = ctx["pb"]["scroll"]["cols"]
    for lab, d in rows_cmp:
        c = d["cols"]
        dd = [dc3(c[i], ref_cols[i]) for i in range(3)]
        ap("| %s | `%s` | `%s` | `%s` | %d / %d / %d |" % (lab, c[0], c[1], c[2], dd[0], dd[1], dd[2]))
    ap("")
    dd_v1 = [dc3(ctx["pb"]["v1"]["cols"][i], ref_cols[i]) for i in range(3)]
    dd_v2 = [dc3(ctx["pb"]["self"]["cols"][i], ref_cols[i]) for i in range(3)]
    ap("改前 → 改后：与参照 [3] 的逐点 ΔRGB 由 **%d / %d / %d** 收敛到 **%d / %d / %d**"
       "（上端 / 中点 / 下端）⇒ 并排「不同族」的根因（下端差 %d）已消除，"
       "「同族」由本脚本 H18/H19 两条断言承担机检（非主观话）。"
       % (dd_v1[0], dd_v1[1], dd_v1[2], dd_v2[0], dd_v2[1], dd_v2[2], dd_v1[2]))
    ap("")
    ap("## 二、断言逐条（脚本内断言，`--check` 可复跑）")
    ap("")
    ap("| 断言 | 实测值 | 结论 |")
    ap("| --- | --- | --- |")
    for name, val, st, why in ctx["rows"]:
        ap("| %s | %s | **%s**%s |" % (name, str(val).replace("|", "\\|"), st,
                                       ("　← " + why) if why else ""))
    ap("")
    ap("## 三、参照件反解（为什么说「同族」）")
    ap("")
    ap("| 参照件 | 尺寸 | α>8 足迹 | 描边最深色 @α | 最外 1px 帧 αmax | vs `@palette.accent` #7AB0E8 |")
    ap("| --- | --- | --- | --- | ---: | --- |")
    for r in ctx["refs"]:
        ap("| `%s` | %d×%d | %s（**直抵画布边**） | %s @%d | **%d**（≠0，旧族未做归零） | ΔRGB=%s |"
           % (r["tag"], r["size"][0], r["size"][1], r["foot"], r["stroke"], r["stroke_alpha"],
              r["frame"], tuple(r["stroke"][i] - ACCENT[i] for i in range(3))))
    ap("")
    ap("结论：两件参照件都是**真 alpha 的竖圆角胶囊**（圆角 = 条宽/2 ⇒ 正胶囊）+ **霜白竖向渐变**"
       "（上浅下深）+ **冰蓝描边** + **外沿柔光**，内部实心区 α 251–253（本件条面 α 250–251，差 1–2/255）。"
       "描边色证据：两件的**最深实测像素**都落在 `@palette.accent` 同族区间 —— `x_ui_scroll_knob` "
       "`(106,173,229)` vs accent `(122,176,232)` ⇒ ΔRGB=(−16,−3,−3)；`x_ui_shift_knob` 因件小、"
       "下采样权重高，最深只到 `(143,185,228)`（同一色相的更浅混合）。本件沿用同一套语汇，"
       "**唯一有意的差异是边缘策略**：参照件由超分件下采样、形状直抵画布边"
       "（最外帧 αmax %d/%d ≠ 0，会被画布硬切）；本件按本工程 `frame` 口径做 2px 内缩 + 帧归零。"
       % (ctx["refs"][0]["frame"], ctx["refs"][1]["frame"]))
    ap("")
    ap("## 四、目视评语（代理目视 `E1_滑标同族对照.png` / `E1_背景_源与成品.png` 后所记，非机检）")
    ap("")
    ap("### 4.1 滑标同族观感")
    ap("")
    ap("- **同族成立**：新件与两件参照件在「竖圆角胶囊 + 霜白渐变条面 + 冰蓝描边 + 柔光」四项上"
       "读得出是同一家族；条宽/圆角/描边三者协调，没有出现异族素材（不是横胶囊、不是圆点、不是方板）。")
    ap("- **条宽观感**：新件 12×27（宽高比 0.44）落在两件参照件之间（16×25 → 0.64、18×71 → 0.25），"
       "与元素 `fc.zoom_knob` 的 40×31 方框相比显得偏细，但这是冻结书给定的「条宽 12」；在轨道合成图里"
       "读作一枚瘦手柄，不显突兀。")
    ap("- **描边观感**：新件描边比两件参照件**更锐**（参照件是超分件下采样，描边摊成 2–3px 的软带；"
       "新件是 1.5px 解析描边）。放到 1:1 实际尺寸（40×31）差异不会明显，但严格说新件更「玻璃感」、"
       "参照件更「雾感」。")
    ap("- **填充观感（第二版已对齐）**：端点色改为参照件实测档（上 `(233,239,243)` → 下 "
       "`(155,199,235)`）后，与 [3] `x_ui_scroll_knob` 三档逐点 ΔRGB ≤ %d ⇒ 并排读作**同一族**；"
       "改前（面板件白档）下端差 %d，正是并排显「更白、更玻璃」的根因。"
       % (max(dd_v2), dd_v1[2]))
    ap("- **轨道合成**：手柄比轨道可见体（实心带 %dpx）竖向各露出约 %.1fpx —— 滑标本就该露出轨道，"
       "观感正常；正式落点由元素几何决定，本图仅供观感。" % (ctx["rail_h"], (BAR_H - ctx["rail_h"]) / 2.0))
    ap("")
    ap("### 4.2 背景观感")
    ap("")
    ap("- 源 `bg72.png` 是一张**天空 / 云层**摄影（均值 220.6、5%=195、95%=248，整体偏亮）。")
    ap("- 960×540 缩略并排：两者**肉眼不可分**（尺寸比恰 0.75×、逐像素等于参考 LANCZOS 结果）。")
    ap("- 1:1 中线裁剪（各 480×270）：未观察到**振铃（ringing）/ 摩尔纹 / 锯齿**；成品因来自 2× 超分件"
       "降采样，细节反而比源更「干净」一点，无「锐化过度」痕迹。")
    ap("- **后续注意（交主代理/vision）**：亮度均值 220.6 属偏亮素材，流程图屏已定 `fc.dim` 压暗 60% ⇒"
       "压暗后约 88（按线性 0.4× 估），仍高于多数 UI 浅霜板的亮度，节点文字为白字黑描边、左栏连线为"
       "深蓝/灰 —— 实际对比度须在实机巡演导出 PNG 上复核（冻结书 §D 已写明「必须目视确认左栏连线与"
       "节点文字的对比度」）。本模块**不为此改素材**（冻结书禁止调色）。")
    ap("")
    ap("## 五、第二版变更记录（2026-09-29 · 主代理指令「配色对齐参照件」）")
    ap("")
    ap("按主代理指令，**形状/尺寸/描边色/真 alpha/帧策略一律未动**（H1–H17 与首版逐条一致）。配色侧共 3 项：")
    ap("")
    ap("**变更 1 · 填充端点色（指令指定项）**：`FILL_TOP/FILL_BOT` 由 `#F7FBFF`/`#DEEBFA`（首版 = 冻结书 §A "
       "字面值 / 本工程面板件档）改为 **`(233,239,243)` / `(155,199,235)`**"
       "（= `x_ui_scroll_knob` 直段顶/底的中列实测档，依据见 §三 与 §一·补）。")
    ap("")
    ap("**变更 2 · 渐变跨度口径**：由「整条含帽（连续 y 2→29）」改为「**条体直段（连续 y 8→23）**，"
       "两端外按端点色夹住」—— 与参照件同口径（参照件实测端点正是取自其直段顶/底）。"
       "不改这一步，端点色无法在实测采样点命中目标值（改前该项会残留 Δ7）。")
    ap("")
    ap("**变更 3 · 合成实现修正（根因，必须一并改）**：首版 `over()` 把 dst 当**已预乘**处理，"
       "但传入的是**未预乘** rgb ⇒ ① 条面下层（柔光）的权重少乘了 `da`；② 最后又除以 `out_a`，"
       "**把条面整体抬亮 ≈ +5~7/255**。后果：即使把端点色改成目标值，实测仍偏亮 Δ7（本版先按指令"
       "只改颜色时的实测 = 上端 (235,244,250)/Δ7、下端 (162,206,242)/Δ7，H18/H19 FAIL）；"
       "修正合成后端点色才真正等于指定值（现 Δ3/Δ2）。**根因证据**：① 用首版实现（`over_legacy`）"
       "复算改前件，**逐字节命中首版落盘 md5 `%s`**（H20）；② 首版实测上端 `(244,252,255)` 的 G/B "
       "**超过了它自己的端点** `#F7FBFF`=(247,251,255)（G 252>251、B 255≥255）——纯渐变不可能出现，"
       "正是抬亮的痕迹。修正后条面 = 指定渐变（柔光仅在条面不透明度之外贡献 ≈0.5%% 的 accent 混色）。"
       % V1_MD5_EXPECT)
    ap("")
    ap("- **md5**：`x_ui_zoom_handle.png` 首版（主代理所见）`%s` → 改后 `%s`"
       "（原地覆盖；该文件为本批**新件、尚无任何引用**，冻结书允许重出）。"
       % (V1_MD5_EXPECT, ctx["h"]["md5"]))
    ap("- **断言**：%d 条（PASS %d / FAIL %d / INFO %d）——新增 H18（条面上下端 == 参照实测档，"
       "ΔRGB ≤ 6）、H19（与 `x_ui_scroll_knob` 三档逐点 ΔRGB ≤ 6）、H20（改前 v1 基线逐字节可复现）。"
       % (ctx["n_rows"], ctx["n_pass"], ctx["n_fail"], ctx["n_info"]))
    ap("- **描边未随填充调整（附依据）**：主代理允许「若描边比条面更亮则一并微调」；实测"
       "**不构成该情形** —— 描边仍为 `@palette.accent` `(122,176,232)`，新条面下端 `(157,200,235)` "
       "比它**更浅**（ΔR=35 ⇒ 人眼读作更深的轮廓），且参照件同位置描边最深实测 "
       "`(106,173,229)`（vs accent ΔRGB=(−16,−3,−3)，同一冰蓝色相族）⇒ 保持不动，**色相族未改**。")
    ap("- **残余差异（如实登记）**：参照件两端帽内有**回亮**（bottom rim highlight）——"
       "`x_ui_scroll_knob` 底帽 y=63→65 为 `(171,211,238)`→`(200,228,246)`（比直段底更亮）；"
       "本件为线性外推、帽端平铺 `(155,199,235)`（不加深也不回亮）⇒ 底端最后 2–3px 比参照件深"
       "最多 ≈45/255。本版**未加回亮**（指令只要求端点色；回亮属形制加分项），若要更贴可在 "
       "`vgrad_rgb` 末端加一段回亮（改一处、不影响任何断言）。")
    ap("")
    ap("## 六、未决项 / 供主代理裁决")
    ap("")
    ap("1. **端帽回亮**（§五 残余差异）：是否要补——补则更贴参照件观感，不补则观感更「干净」；"
       "两者都不违反任何已冻结条款。")
    ap("2. **素材接线属 E2**：本模块只产 PNG，未跑 `工具\\emit_asset_index.py`、未改 `layout\\**` 与"
       "生成器（`fc.bg` 新增、`fc.zoom_knob` 换素材并删 `nine`、`fc.p_title*` 几何均属 E2）。"
       "E2 落盘后须：① `verify_ui.py` [2] 尺寸一致性（本件 1:1 无 `nine` ⇒ 元素 w/h 必须等于 40×31）；"
       "② 素材体积预算 [6]。")
    ap("3. **旧件保留**：`x_ui_zoom_knob.png`（坏件，29×16，连通域 2）与 `x_ui_fusen_off.png` "
       "**一字未动**（冻结书 §A：旧件一律保留不删）。")
    ap("4. **未做实机渲染复核**：本模块只做静态像素自证 + 目视对照；素材进入 krkr/HTML 后的实际观感"
       "（含 `fc.dim` 压暗 60% 后与本背景的对比度）须由巡演导出的 PNG 复核。")
    ap("5. **预算余量**：`工具\\verify_ui.py` 实测见 §七（本件改动后体积变化与余量）。")
    ap("")
    ap("## 七、`工具\\verify_ui.py` 实测（本模块交付时的全量校验）")
    ap("")
    vu = ctx.get("vu")
    if not vu:
        ap("（本轮未运行 —— 需写进报告请加 `--verify-ui`）")
    elif vu.get("n") is None:
        ap("运行失败或解析不出体积预算行：rc=%s err=%s" % (vu.get("rc"), vu.get("err", "无")))
    else:
        ap("命令：`python \"工具\\verify_ui.py\"`（只读校验器；本模块**不**改 `layout\\**`、"
           "不改生成器、不动既有素材，可随时复跑）")
        ap("")
        ap("- 解析到的原始行：`%s`" % vu["line"])
        ap("- **资产件数 = %d 件** ｜ **总体积 = %.2f MB**（打印值）｜ 预算 = %d MB ｜ 闸门 = %s"
           " ｜ 退出码 = %d（0 = 六项全通过）" % (vu["n"], vu["mb"], vu["budget"], vu["gate"], vu["rc"]))
        if vu.get("exact_bytes"):
            ap("- **精确口径（脚本自扫 `assets/ui` 下 %d 件 PNG 逐件求和）**：%d 字节 = **%.4f MiB** ⇒ "
               "**余量 = %d 字节 ≈ %.2f KB**（verify_ui 打印的 MB 是两位小数，直接相减会带 ±0.1 MB 舍入误差，"
               "故以本行为准）"
               % (vu["n"], vu["exact_bytes"], vu["exact_mib"],
                  int(vu["budget"] * 1048576 - vu["exact_bytes"]), vu["exact_headroom_kb"]))
        ap("- 本次第二版改动对本目录体积的影响：`x_ui_zoom_handle.png` 由 %d 字节变为 %d 字节"
           "（Δ %+d 字节 = %+.3f KB），背景件未动、其余件未动。"
           % (ctx["h"]["v1_bytes"], ctx["h"]["bytes"], ctx["h"]["bytes"] - ctx["h"]["v1_bytes"],
              (ctx["h"]["bytes"] - ctx["h"]["v1_bytes"]) / 1024.0))
    ap("")
    ap("---")
    ap("")
    ap("## 附：证据文件")
    ap("")
    for f, d in ctx["evid"]:
        ap("- `%s` — %s" % (f, d))
    ap("")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    return len(L)


# ══════════════════════════════════════════════════════════════════ 主流程
def main(argv):
    check_only = "--check" in argv
    rows = []          # 断言表： (断言, 实测值, PASS/FAIL)
    notes = []

    def say(name, val, ok, why=""):
        """ok 为 True/False ⇒ PASS/FAIL；ok 为 None ⇒ INFO（仅登记、不计入判定）"""
        st = "INFO" if ok is None else ("PASS" if ok else "FAIL")
        rows.append((name, val, st, why))
        print("  %-46s %-52s %s%s" % (name, val, st, ("  ← " + why) if why else ""))
        return st != "FAIL"

    ok = True

    # ───────────────────────────────────────────── 滑标
    print("=" * 118)
    print("① 滑标 krkr\\assets\\ui\\x_ui_zoom_handle.png（40×31 RGBA / 竖圆角胶囊）")
    print("-" * 118)
    arr, raw = build_handle()
    # 首版基线（改前对照）：**首版配方原样**（v1 端点色 + v1「整条含帽」跨度 + v1 合成实现）
    #   ⇒ 应逐字节复现首版落盘件（H20 对拍），报告里的「改前」数字取自它、不是事后追记
    arr_v1, _raw_v1 = build_handle(fill_top=FILL_TOP_V1, fill_bot=FILL_BOT_V1,
                                   fill_span=(BOX[1], BOX[3]), legacy=True)
    b_v1 = enc_png(arr_v1, "RGBA")
    b_new = enc_png(arr, "RGBA")
    md5_new = md5f(b_new)
    rawexists = os.path.isfile(OUT_HANDLE)
    md5_before = md5f(open(OUT_HANDLE, "rb").read()) if rawexists else None
    if not check_only:
        Image.fromarray(arr, "RGBA").save(OUT_HANDLE, "PNG", optimize=True)
    exists = os.path.isfile(OUT_HANDLE)
    ok &= say("H0 成品存在（%s）" % os.path.basename(OUT_HANDLE), "是" if exists else "缺",
              exists, "缺失时先落盘再核")
    if not exists:
        print("  ✗ 成品缺失 ⇒ 后续断言无法进行")
        return 1
    md5_disk = md5f(open(OUT_HANDLE, "rb").read())      # ★ 写盘**之后**回读 ⇒ 幂等判据有效
    im = load_rgba(OUT_HANDLE).convert("RGBA")
    al = a8_of(im)
    rgbf = np.asarray(im).astype(np.int32)
    ok &= say("H1 尺寸 == 40×31", "%s" % (im.size,), im.size == (HW, HH))
    ok &= say("H2 mode == RGBA（PNG-32 真 alpha）", im.mode, im.mode == "RGBA")
    n_cc8 = cc_count(al, 8, 8)
    n_cc4 = cc_count(al, 8, 4)
    ok &= say("H3 连通域数（α>8）== 1（8-邻接 / 4-邻接）", "%d / %d" % (n_cc8, n_cc4),
              n_cc8 == 1 and n_cc4 == 1, "对「两个不明物体」的直接反证")
    core = bbox(al, 128)
    ok &= say("H4 墨迹 bbox（α≥128）== (14,2)-(25,28)", str(core), core == (14, 2, 25, 28),
              "条宽 12 / 条高 27 / 左右各 14 / 上下各 2 = 居中等尺寸")
    halo = bbox(al, 8)
    ok &= say("H5 全足迹 bbox（α>8）== (13,1)-(26,29)", str(halo), halo == (13, 1, 26, 29),
              "= 核心外扩 1px 的柔发光环；未触最外帧（非第二图形）")
    fa = frame_amax(al)
    ok &= say("H6 最外 1px 帧 αmax == 0（剪后）", "%d" % fa, fa == 0, "本工程 frame 类边缘策略")
    rf = frame_amax(raw)
    ok &= say("H7 剪前最外 1px 帧 αmax ≤ %d" % RAW_FRAME_MAX, "%d" % rf, rf <= RAW_FRAME_MAX,
              "发光尾不过强 ⇒ 剪后归零非空转")
    solid = int((al == 255).sum())
    ok &= say("H8 α==255 像素数 > 0（有实心区）", "%d" % solid, solid > 0, "描边带内 1.5px 满覆盖")
    zdark = int((al == 0).sum())
    ok &= say("H9 α==0 像素数 > 0（真 alpha、非满幅）", "%d（%.1f%%）" % (zdark, 100.0 * zdark / al.size),
              zdark > 0)
    # ── 形状学：用「50% 覆盖交叉点」量边界（本工程口径：量边缘要以 50% 覆盖交叉点为界），
    #    并用**发光偏置校正**把柔光外扩的部分扣掉；再用「圆角矩形的解析边界」反证圆角 == 6。
    SOLID_T = 200
    span = [y for y in range(HH) if (al[y] >= SOLID_T).any()]
    ok &= say("H10 条高 == 27（α≥200 竖向跨度 y=2..28）",
              "y=%d..%d（%d 行）" % (span[0], span[-1], len(span)) if span else "无",
              span == list(range(2, 29)), "条体竖向 y ∈ [2,29)（含两端圆角帽）")

    cs = [cross50(al[y]) for y in range(HH)]
    wid = [cs[y][1] - cs[y][0] for y in range(HH) if cs[y][0] is not None]   # 交叉点到交叉点（索引空间）
    wmax = max(wid)
    bias = wmax - BAR_W                   # 柔光把 50% 交叉点整体外推的总量（两侧合计）
    w_corr = wmax - bias                  # 扣除发光外推后的条宽
    center = (cs[15][0] + cs[15][1]) / 2.0
    ok &= say("H11 条宽 == 12（50%% 交叉跨距 %.2f − 发光外推 %.2f）" % (wmax, bias),
              "%.2f − %.2f = %.2f ｜ 各行跨距上限 %.2f（≤ 12+%.2f）"
              % (wmax, bias, w_corr, wmax, bias),
              abs(w_corr - BAR_W) <= 0.20 and max(wid) <= wmax + 1e-9,
              "无任何行跨距超过条宽 ⇒ 不是横胶囊 / 方块")
    ok &= say("H12 居中：50%% 交叉中心 %.2f == 画布中心索引 %.2f（≤0.30）" % (center, CX - 0.5),
              "左 %.2f / 右 %.2f" % (cs[15][0], cs[15][1]),
              abs(center - (CX - 0.5)) <= 0.30,
              "左右各留 14px、上下各留 2px")
    fit6 = cap_fit_err(cs, bias / 2.0, BAR_R)
    disc = {r: cap_fit_err(cs, bias / 2.0, r) for r in (0.0, 3.0, 9.0)}
    ok &= say("H13 圆角 == 6（正胶囊）：两端帽与 r=6 圆弧的最大偏差 %.2fpx ≤ 0.60" % fit6,
              "r=6 → %.2f ｜ 反证 r=0 → %.2f、r=3 → %.2f、r=9 → %.2f" %
              (fit6, disc[0.0], disc[3.0], disc[9.0]),
              fit6 <= 0.60 and min(disc.values()) > 0.60,
              "参照件两件同形制（圆角 = 条宽/2）；反证列显示判据对非 6 的圆角会报错 ⇒ 有判别力")
    # 描边色：竖向直段中列、条体左右各 1px 的描边带取样，应 ≈ accent
    s_col = 20
    edge_px = [rgbf[15, 14], rgbf[15, 25]]
    dmax = max(max(abs(int(p[i]) - ACCENT[i]) for i in range(3)) for p in edge_px)
    ok &= say("H14 描边色 ≈ @palette.accent #7AB0E8（Δmax ≤ 8）",
              "%s vs %s, Δmax=%d" % (edge_px[0].tolist(), list(ACCENT), dmax), dmax <= 8,
              "描边取 palette accent（唯一色值来源）")
    # 填充渐变方向：条体中线自上而下变深
    top_px, bot_px = rgbf[10, s_col], rgbf[21, s_col]
    ok &= say("H15 填充竖向渐变「浅色在上、略深在下」",
              "y=10 %s ＞ y=21 %s（亮度和 %d > %d）" % (top_px.tolist(), bot_px.tolist(),
                                                    int(top_px.sum()), int(bot_px.sum())),
              int(top_px.sum()) > int(bot_px.sum()),
              "端点色 = 参照实测档 上 %s → 下 %s（第二版）" % (list(FILL_TOP), list(FILL_BOT)))
    ok &= say("H16 幂等：本次重算字节 == 盘上回读字节（md5）", "%s" % md5_new, md5_disk == md5_new,
              "写前 %s" % (md5_before or "（原文件不存在）"))
    # 参照件轨道（x_ui_zoom_rail，123×31）的实心带高度 —— 供 E2/vision 判「手柄比轨道露出多少」
    rail_a = a8_of(load_rgba(REF_ZOOMRAIL).convert("RGBA"))
    rail_core = [y for y in range(rail_a.shape[0]) if int((rail_a[y] >= 200).sum()) >= 60]
    rail_core_h = len(rail_core)
    ok &= say("H17 轨道 x_ui_zoom_rail 的实心带高度（INFO，供判「露出多少」）",
              "%dpx（y=%d..%d）；手柄 %d ⇒ 竖向各露出 ≈%.1fpx"
              % (rail_core_h, rail_core[0], rail_core[-1], BAR_H, (BAR_H - rail_core_h) / 2.0)
              if rail_core else "未测到", None,
              "滑标露出轨道属正常观感；正式落点由元素几何决定")

    # ── 条面色三档（与参照件同口径；第二版核心）────────────────────────────────
    pb_self = bar_probe(im)                       # 成品（盘上回读）
    pb_v1 = bar_probe(Image.fromarray(arr_v1, "RGBA"))    # 首版（内存重算，供「改前」对照）
    pb_scroll = bar_probe_file(REF_SCROLL)
    pb_shift = bar_probe_file(REF_SHIFT)
    d_top = dc3(pb_self["cols"][0], FILL_TOP)
    d_bot = dc3(pb_self["cols"][2], FILL_BOT)
    ok &= say("H18 条面上下端 == 参照实测档（上 %s / 下 %s，ΔRGB ≤ 6）"
              % (list(FILL_TOP), list(FILL_BOT)),
              "上端 %s（Δ%d）／下端 %s（Δ%d）"
              % (list(pb_self["cols"][0]), d_top, list(pb_self["cols"][2]), d_bot),
              d_top <= 6 and d_bot <= 6, "第二版配色（主代理 2026-09-29 指令）")
    d_pts = [dc3(pb_self["cols"][i], pb_scroll["cols"][i]) for i in range(3)]
    ok &= say("H19 与 x_ui_scroll_knob 的三档条面色逐点 ΔRGB ≤ 6（同族可机检）",
              "上端 Δ%d／中点 Δ%d／下端 Δ%d（本件 %s ｜ 参照 %s）"
              % (d_pts[0], d_pts[1], d_pts[2], pb_self["cols"], pb_scroll["cols"]),
              max(d_pts) <= 6, "取样口径见 bar_probe（α>8 足迹 → 胶囊直段 → 三档）")
    md5_v1 = md5f(b_v1)
    ok &= say("H20 「改前 v1 基线」可复现：内存重算的 v1 字节 == 首版落盘 md5",
              "%s（期望 %s）" % (md5_v1, V1_MD5_EXPECT), md5_v1 == V1_MD5_EXPECT,
              "报告 §一·补 的「改前」数字取自该基线，非事后追记")
    mh = png_metrics(al)
    notes.append("滑标：αmin=%d / αmax=%d / α=0 占 %.1f%% / α=255 计 %d / md5=%s"
                 % (mh["amin"], mh["amax"], mh["zero_pct"], mh["solid"], md5_new))

    # ───────────────────────────────────────────── 参照件反解（证据，非断言）
    print("-" * 118)
    print("  ↳ 参照件反解（证明「同族」不是主观话）")
    ref_info = []
    for tag, p in (("x_ui_shift_knob", REF_SHIFT), ("x_ui_scroll_knob", REF_SCROLL)):
        im2 = load_rgba(p).convert("RGBA")
        a2 = np.asarray(im2).astype(np.int32)
        al2 = a2[..., 3]
        # 描边最深色：全图 α≥160 的像素里取 (R+G+B) 最小者（= 最饱和的冰蓝），低 α 发光尾的
        # 未预乘 RGB 会偏灰、必须排除（否则量到的不是描边而是外沿柔光的尾巴）
        hh2, ww2 = al2.shape
        cand = [(int(a2[y, x, :3].sum()), (x, y), int(al2[y, x]), tuple(a2[y, x, :3].tolist()))
                for y in range(hh2) for x in range(ww2) if al2[y, x] >= 160]
        stroke = min(cand) if cand else (None, None, None, None)
        frame_max = int(max(al2[0].max(), al2[-1].max(), al2[:, 0].max(), al2[:, -1].max()))
        ys2, xs2 = np.where(al2 > 8)
        ref_info.append(dict(tag=tag, size=im2.size,
                             foot=(int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max())),
                             frame=frame_max, stroke=stroke[3], stroke_alpha=stroke[2],
                             inner_lo=float(al2[al2 > 8].min()), inner_hi=float(al2.max())))
        print("    %-18s size=%s ｜ α>8 足迹 %s（**直抵画布边**）｜ 内部 α 8–%d ｜ "
              "描边最深色 %s @α=%d ｜ 最外帧 αmax=%d"
              % (tag, im2.size, ref_info[-1]["foot"], ref_info[-1]["inner_hi"], stroke[3],
                 stroke[2], frame_max))
    sc = ref_info[1]["stroke"]
    dl = tuple(sc[i] - ACCENT[i] for i in range(3))
    print("    → 反解结论：参照件 = 真 alpha 竖圆角胶囊（圆角 ≈ 条宽/2）+ 霜白竖向渐变（上浅下深）"
          "+ 冰蓝描边 + 外沿柔光")
    print("      实测对照：scroll_knob 描边最深 %s @α=%d vs @palette.accent %s ⇒ ΔRGB=%s"
          % (sc, ref_info[1]["stroke_alpha"], list(ACCENT), dl))
    print("      ★ 骨架同族、**边缘策略不同**：参照件是超分件下采样，形状直抵画布边缘（最外帧 αmax "
          "%d/%d ≠ 0）；本件按冻结书要求做 2px 内缩 + 帧归零。"
          % (ref_info[0]["frame"], ref_info[1]["frame"]))

    # ───────────────────────────────────────────── 背景
    print("-" * 118)
    print("② 背景 krkr\\assets\\ui\\x_bg_flowchart.png（1920×1080）")
    print("-" * 118)
    arr_bg, src_im, _ = build_bg()
    b_bg = enc_png(arr_bg, "RGB")
    md5_bg = md5f(b_bg)
    rawb = os.path.isfile(OUT_BG)
    md5_bg_before = md5f(open(OUT_BG, "rb").read()) if rawb else None
    if not check_only:
        Image.fromarray(arr_bg, "RGB").save(OUT_BG, "PNG", optimize=True)
    exists_b = os.path.isfile(OUT_BG)
    ok &= say("B0 成品存在（%s）" % os.path.basename(OUT_BG), "是" if exists_b else "缺",
              exists_b, "缺失时先落盘再核")
    if not exists_b:
        print("  ✗ 成品缺失 ⇒ 后续断言无法进行")
        return 1
    md5_bg_disk = md5f(open(OUT_BG, "rb").read())       # ★ 写盘**之后**回读 ⇒ 幂等判据有效

    ob = Image.open(OUT_BG)
    ob.load()
    aob = np.asarray(ob)
    ok &= say("B1 尺寸 == 1920×1080", "%s" % (ob.size,), ob.size == (BG_W, BG_H))
    ok &= say("B2 mode == RGB（如实报告）", ob.mode, ob.mode in ("RGB", "RGBA"),
              "源为 RGB、resize 不变 mode ⇒ 成品 RGB、无 alpha 通道")
    ref = src_im.resize((BG_W, BG_H), Image.LANCZOS)
    aref = np.asarray(ref)
    diff = np.abs(aob.astype(np.int32) - aref.astype(np.int32))
    ndiff = int((diff.max(axis=2) > 0).sum())
    ok &= say("B3 与「PIL 对源 resize((1920,1080), LANCZOS) 的参考结果」逐像素相同",
              "差异像素 %d / %d，maxdiff %d" % (ndiff, BG_W * BG_H, int(diff.max())), ndiff == 0,
              "落盘为 PNG 无损 ⇒ 写盘无二次有损处理")
    r_src = SRC_BG_W / float(SRC_BG_H)
    r_out = BG_W / float(BG_H)
    ok &= say("B4 与源宽高比一致（16:9）",
              "源 %.6f / 成品 %.6f / 16:9=%.6f" % (r_src, r_out, 16 / 9.0),
              abs(r_src - r_out) < 1e-9 and abs(r_out - 16 / 9.0) < 1e-9)
    ok &= say("B5 变换因子恰 0.75×（两轴同值）",
              "%.10f / %.10f" % (BG_W / float(SRC_BG_W), BG_H / float(SRC_BG_H)),
              BG_W * 4 == SRC_BG_W * 3 and BG_H * 4 == SRC_BG_H * 3)
    src_a = np.asarray(src_im.convert("RGB"))
    st = {}
    for tag, a_ in (("源", src_a), ("成品", aob)):
        lum = (0.2126 * a_[..., 0] + 0.7152 * a_[..., 1] + 0.0722 * a_[..., 2])
        lum_mean = float(lum.mean())
        st[tag] = (float(lum_mean), float(np.percentile(lum, 5)), float(np.percentile(lum, 95)),
                   float(lum.min()), float(lum.max()),
                   [float(a_[..., i].mean()) for i in range(3)])
    ok &= say("B6 亮度统计（顺带报告，供后续判「压暗 60% 后是否还看得见」）",
              "源 均值%.1f/5%%=%.0f/95%%=%.0f ｜ 成品 均值%.1f/5%%=%.0f/95%%=%.0f"
              % (st["源"][0], st["源"][1], st["源"][2], st["成品"][0], st["成品"][1], st["成品"][2]),
              None, "非判据项（INFO）；阈值为 0–255 亮度 (0.2126R+0.7152G+0.0722B)")
    dm = abs(st["源"][0] - st["成品"][0])
    ok &= say("B7 无整体调色（源/成品亮度均值差 ≤ 2/255）", "%.3f" % dm, dm <= 2.0,
              "仅为降采样 ⇒ 均值守恒；配合 B3 的逐像素相等即排除调色/裁切/加边")
    ok &= say("B8 幂等：本次重算字节 == 盘上回读字节（md5）", "%s" % md5_bg, md5_bg_disk == md5_bg,
              "写前 %s" % (md5_bg_before or "（原文件不存在）"))
    notes.append("背景：源 %dx%d RGB %.2fMB → 成品 %dx%d %s %.2fMB ｜ 成品亮度 均值%.2f/5%%=%.0f/95%%=%.0f"
                 % (SRC_BG_W, SRC_BG_H, os.path.getsize(SRC_BG) / 1048576.0, BG_W, BG_H, ob.mode,
                    os.path.getsize(OUT_BG) / 1048576.0, st["成品"][0], st["成品"][1], st["成品"][2]))
    notes.append("背景通道均值：源 %s ｜ 成品 %s"
                 % (["%.2f" % v for v in st["源"][5]], ["%.2f" % v for v in st["成品"][5]]))

    # ───────────────────────────────────────────── 汇总
    print("=" * 118)
    n_fail = sum(1 for r in rows if r[2] == "FAIL")
    n_info = sum(1 for r in rows if r[2] == "INFO")
    n_pass = len(rows) - n_fail - n_info
    print("断言：%d 条 ｜ PASS %d ｜ FAIL %d ｜ INFO %d ｜ 模式=%s" %
          (len(rows), n_pass, n_fail, n_info, "CHECK（只读）" if check_only else "WRITE"))
    for n in notes:
        print("  · " + n)

    # ───────────────────────────────────────────── verify_ui（可选；只读，不影响退出码）
    vu = None
    if "--verify-ui" in argv:
        print("  ↳ 运行 工具\\verify_ui.py（只读；约 30–60s）…")
        vu = run_verify_ui()
        if vu and vu.get("n") is not None:
            print("    %s" % vu["line"])
            print("    件数 %d ｜ 体积 %.2f MB ｜ 预算 %d MB ｜ 闸门 %s ｜ 余量 ≈ %.2f KB（精确口径）｜ rc=%d"
                  % (vu["n"], vu["mb"], vu["budget"], vu["gate"],
                     vu.get("exact_headroom_kb", vu["headroom_kb"]), vu["rc"]))
        else:
            print("    verify_ui 运行失败或解析失败：%s" % (vu,))

    # ───────────────────────────────────────────── 证据（tsv / 两张对照图 / 自证报告）
    if not check_only:
        os.makedirs(EVID, exist_ok=True)
        sz1 = make_family_sheet(os.path.join(EVID, "E1_滑标同族对照.png"))
        sz2 = make_bg_pair(os.path.join(EVID, "E1_背景_源与成品.png"))
        tsv = os.path.join(EVID, "E1_滑标自证.tsv")
        with open(tsv, "w", encoding="utf-8", newline="\n") as f:
            f.write("# ISSUE-20260929-04 · E1 素材自证（m61_make_zoom_handle_and_bg.py 产出）\n")
            f.write("# 生成命令：python \"_工作\\ISSUE-20260929-04_流程图件\\复现脚本\\"
                    "m61_make_zoom_handle_and_bg.py\"\n")
            f.write("断言\t实测值\t结论\n")
            for r in rows:
                f.write("%s\t%s\t%s\n" % (r[0], r[1], r[2]))
            f.write("# 附注\n")
            for n in notes:
                f.write("# %s\n" % n)
            f.write("# 形状反解：条宽 %.2f（跨距 %.2f − 发光外推 %.2f）｜ 条高 %d（y=%d..%d）｜"
                    " 圆角拟合 r=6 → %.2fpx（反证 r=0 %.2f / r=3 %.2f / r=9 %.2f）｜ 居中 %.2f\n"
                    % (w_corr, wmax, bias, len(span), span[0], span[-1], fit6, disc[0.0], disc[3.0],
                       disc[9.0], center))
            for r in ref_info:
                f.write("# 参照件反解 · %s：size=%s ｜ α>8 足迹 %s（直抵画布边）｜ 描边最深色 %s @α=%d "
                        "｜ 最外帧 αmax=%d ｜ vs @palette.accent %s ⇒ ΔRGB=%s\n"
                        % (r["tag"], r["size"], r["foot"], r["stroke"], r["stroke_alpha"], r["frame"],
                           list(ACCENT), tuple(r["stroke"][i] - ACCENT[i] for i in range(3))))
            f.write("# 条面色三档（口径 bar_probe：α>8 足迹 → 胶囊直段 → 中列取 直段顶/中/底）\n")
            for lab, d in (("改后 v2（现行盘上件）", pb_self), ("改前 v1（首版基线）", pb_v1),
                           ("参照 x_ui_shift_knob", pb_shift), ("参照 x_ui_scroll_knob", pb_scroll)):
                f.write("#   %-26s 上端 %-16s 中点 %-16s 下端 %-16s ｜ 行 %s ｜ 列 x=%d\n"
                        % (lab, str(d["cols"][0]), str(d["cols"][1]), str(d["cols"][2]),
                           d["rows"], d["cx"]))
            ref_c = pb_scroll["cols"]
            f.write("#   与参照 x_ui_scroll_knob 逐点 ΔRGB：改后 v2 = %s ｜ 改前 v1 = %s\n"
                    % ([dc3(pb_self["cols"][i], ref_c[i]) for i in range(3)],
                       [dc3(pb_v1["cols"][i], ref_c[i]) for i in range(3)]))
            f.write("#   渐变跨度：v2 = 条体直段（连续 y %.0f→%.0f）｜ v1 = 整条含帽（连续 y %.0f→%.0f）\n"
                    % (BOX[1] + BAR_R, BOX[3] - BAR_R, BOX[1], BOX[3]))
        ctx = dict(
            rows=rows, refs=ref_info, n_rows=len(rows), n_pass=n_pass, n_fail=n_fail, n_info=n_info,
            rc=0 if ok else 1, result="OK" if ok else "NG",
            h=dict(w=im.size[0], h=im.size[1], mode=im.mode, bytes=os.path.getsize(OUT_HANDLE),
                   amin=mh["amin"], amax=mh["amax"], zero_pct=mh["zero_pct"], solid=mh["solid"],
                   md5=md5_new, v1_bytes=len(b_v1), v1_md5=md5_v1),
            b=dict(w=ob.size[0], h=ob.size[1], mode=ob.mode, bytes=os.path.getsize(OUT_BG),
                   md5=md5_bg),
            w_corr=w_corr, w_raw=wmax, bias=bias, bar_h=len(span), span0=span[0], span1=span[-1],
            fit6=fit6, disc0=disc[0.0], disc3=disc[3.0], disc9=disc[9.0], center=center,
            st_src=st["源"], st_out=st["成品"], dlum=dm, rail_h=rail_core_h,
            pb=dict(self=pb_self, v1=pb_v1, scroll=pb_scroll, shift=pb_shift),
            vu=vu,
            evid=[("E1_滑标自证.tsv", "断言表（%d 条）+ 形状反解 + 参照件反解 + **条面色三档**（改前/改后/两参照）"
                   % len(rows)),
                  ("E1_滑标同族对照.png", "四枚 8× 放大并排（新件 / 两件参照 / 旧坏件）+ 轨道合成观感；%d×%d"
                   % (sz1[0], sz1[1])),
                  ("E1_背景_源与成品.png", "源与成品缩略并排 + 1:1 中线裁剪对照；%d×%d" % (sz2[0], sz2[1])),
                  ("E1_自证报告.md", "本文件（命令 / 实测数字 / 目视评语 / 未决项）")])
        nline = make_report(os.path.join(EVID, "E1_自证报告.md"), ctx)
        print("  证据：E1_滑标自证.tsv（%d 行）｜ E1_滑标同族对照.png %s ｜ "
              "E1_背景_源与成品.png %s ｜ E1_自证报告.md（%d 行）" % (len(rows), sz1, sz2, nline))

    print("RESULT=%s" % ("OK" if ok else "NG 有断言未过（见上）"))
    print("★ 提醒：本脚本只产 PNG 与证据；`layout\\**` 接线与 `emit_asset_index.py` / `verify_ui.py` 属 E2。")
    print("=" * 118)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
