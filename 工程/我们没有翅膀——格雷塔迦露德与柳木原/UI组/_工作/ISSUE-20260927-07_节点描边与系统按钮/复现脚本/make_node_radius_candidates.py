# -*- coding: utf-8 -*-
"""节点圆角「高分辨率重画」候选件 + 对比图生成器（ISSUE-20260927-07 · 圆角候选轮）

只产出**候选件与对比图**到证据目录，**不改正式素材**（krkr/assets/ui 只读），
**不改** make_node_variant_a.py（本脚本 import 它以复用改色/描边口径，保证口径一致）。

背景（用户 2026-09-27 反馈 + 主代理实测）
----------------------------------------
用户圈出实机渲染图四个角：「还有毛刺和不规整，四个角完全是像素风格」。
实测 x_ui_node_section_off.png（236×65）实体区左轮廓逐行 = 13,11,9,9,8,7,7,7
⇒ 圆角半径只有 ~7px、且用 2px 一档的粗折线画成（边缘本身是有 AA 的，问题在弧太粗）。

关键约束
--------
引擎按 nine 把左右端 1:1 摆放、只横向拉伸中段 ⇒ **不能靠整张 2×/4× 放大提分辨率**
（放大后圆角会被横向挤成椭圆）。正确做法＝**在内部用 8× 超采样把圆角重画成解析圆弧**
（并可加大半径），成品仍是 1×、尺寸不变、nine 不变。

算法（照主代理给定式实现）
--------------------------
① 实体区 bbox：另见下方 RECT 说明（实测微调，见「§几何口径」）。
② Z=8 画布上解析地画圆角矩形（半径 r_1x），超采样覆盖度平均得 1× 覆盖率 cov（0..1）。
③ 逐像素：new_alpha = min(orig_alpha, max(cov*255, min(orig_alpha, GLOW_CAP)))
   - 形状内部（cov=1）⇒ new = orig，原件内部像素与全部 RGB 一律不动；
   - 形状外侧（cov=0）⇒ new = min(orig, GLOW_CAP)，保留原件柔光、把「旧粗折线角」那部分实体截掉；
   - 形状边缘 ⇒ cov 给出干净抗锯齿。
④ RGBA = (orig_rgb, new_alpha)，尺寸与原件完全相同。

§几何口径（对主代理给定式的两处**实测微调**，理由写在此处）
----------------------------------------------------------
【微调 1 · 形状边界位置】主代理给的是「solid = alpha>=230 取 bbox」。实测：**thr=230 的 bbox 落在
AA 过渡带内侧**，bbox 外 1px 的像素实测高达 226，若以它为形状边界会被 CAP 截到 60 ⇒ 四条直边被削薄
（实测给定式全画布版：直边最大被削 81–112/255、184–711 px 降幅>8）。
故边界改取各边 **50% 覆盖交叉点**（sub-pixel 线性插值，见 first_cross / edge_bounds），
即「视觉边界」；且按 box 滤波覆盖率式取 **b = c + 0.5**（c 为轮廓的 50% 交叉索引），否则整条弧内缩 0.5px。

【微调 2 · 式的作用域】给定式是全画布的。但直边淡出像素的 `cov*255 < orig`（原件 AA 不对称，
如 section 右边 255→219.7→38.1）⇒ 全画布版仍会削直边。给定式的语义是「外侧保留柔光、只截掉旧
粗折线角那部分实体」，而**旧粗折线角只在角区** ⇒ 把作用域收到「角区方块 ∩ 矩形内」与语义完全等价，
且直边/柔光逐像素零回归（实测直边最大降 0.0）。这就是 candidate_alpha()。

★ 本式**只能压暗、不能提亮** ⇒ 当 r ≤ 原件既有角半径时，新形状反而包住旧形状，无可削像素：
  r=8 三类候选件与原件**逐字节相同**（空档）；select/frag 的 r=12 亦几乎等价（改动 41–42 px）。
  真正起作用的档是 r=16（三类改动 174–213 px）。选档时须以「原件角半径」为参照（实测
  section≈9.0 / select≈13.3 / frag≈13.9）。

用法
----
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python "_工作/ISSUE-20260927-07_节点描边与系统按钮/复现脚本/make_node_radius_candidates.py"

产物（全部落在 _工作/ISSUE-20260927-07_节点描边与系统按钮/ 下）
--------------------------------------------------------------
    取证/圆角候选/候选_x_ui_node_<kind>_off_r<N>.png            ← 候选件（RGB＝改色前原件色）
    取证/圆角候选/候选_x_ui_node_<kind>_off_r<N>_描边.png        ← select 用：原件色 + #2A5490 2px 内描边
    取证/圆角候选/候选_x_ui_node_select_off_r<N>_生效色_描边.png ← select 用：现行管线生效色（对照图同口径）
    取证/圆角候选/对比_圆角半径_三档.png                          ← 主交付物①（四角 8×，4 行）
    取证/圆角候选/对比_圆角候选_全节点.png                         ← 主交付物②（整节点 1:1 三类 + 2× 一行）
    取证/圆角候选/圆角候选_数字证据.txt                            ← 数字证据（JSON，含逐角明细）
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")

import numpy as np                                                       # noqa: E402
from PIL import Image, ImageDraw                                         # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve()
UI = HERE.parents[3]                                   # …\UI组
ISSUE = UI / "_工作" / "ISSUE-20260927-07_节点描边与系统按钮"
REPRO = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "复现脚本"
BACKUP = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "原形备份"
CUR = UI / "krkr" / "assets" / "ui"                     # **只读**：现行正式件（取「现状」行）
OUT = ISSUE / "取证" / "圆角候选"
SHOT = (UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "取证" / "E2_自证"
        / "E2_真实数据验收图_shot_84_flowchart.png")

sys.path.insert(0, str(REPRO))
import make_node_variant_a as MF                                          # noqa: E402  （__main__ 有保护，import 无副作用）

# ------------------------------------------------------------------ 关键参数
Z = 8                       # 超采样倍率（S = Z²+1 = 65 级覆盖率 → 边缘 AA 灰阶上限 65）
RADII = (8, 12, 16)         # 候选半径（1× px）
GLOW_CAP = 60               # 形状外侧 alpha 上限（实测原件柔光边峰值：section 48 / select 136 / frag 226
                            #  —— 取 60 是有意的「截断旧粗折线角」强度；见报告「未决点」）
CROSS = 127.5               # 视觉边界＝alpha 的 50% 交叉点
KINDS = ("section", "select", "frag")
KIND_CN = {"section": "章节点", "select": "选择支节点", "frag": "番外节点"}
SPRITE = {"section": (236, 65), "select": (263, 65), "frag": (228, 65)}
BG_FALLBACK = (39, 45, 59)  # 真实图表底色（从验收图干净区取样失败时的回退）
BG_SAMPLE_XY = (400, 190)   # 验收图内的干净取样点（实拍区，非渲染色块）

# ------------------------------------------------------------------ 小工具
def now_bg():
    """从真实验收图的干净区取底色（与既有做法一致：叠在真实图表底色上）。"""
    if not SHOT.exists():
        return BG_FALLBACK, "fallback(验收图缺失)"
    a = np.asarray(Image.open(SHOT).convert("RGB")).astype(int)
    x, y = BG_SAMPLE_XY
    blk = a[y:y + 100, x:x + 100]
    if blk.std(axis=(0, 1)).max() > 0.5:
        return BG_FALLBACK, "fallback(取样区不干净 std=%.2f)" % blk.std(axis=(0, 1)).max()
    return tuple(int(v) for v in blk.mean(axis=(0, 1)).round()), "验收图 (%d,%d) 100×100 实测" % (x, y)


def first_cross(prof, thr=CROSS):
    """自外向内在 prof 上找首个 >= thr 的交叉点，线性插值得 sub-pixel 位置；找不到返回 None。"""
    idx = np.where(prof >= thr)[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    if i == 0:
        return 0.0
    a, b = float(prof[i - 1]), float(prof[i])
    if b == a:
        return float(i)
    return (i - 1) + (thr - a) / (b - a)


def edge_bounds(a):
    """各边的「视觉边界」（50% 交叉，sub-pixel）。取中央带均值轮廓 ⇒ 抗单像素毛刺、抗角区干扰。

    ★ 坐标约定：像素 i 占 [i, i+1)、中心 i+0.5。覆盖率式（box 滤波）下，边界真位置 b 对应
      轮廓的 50% 交叉索引 c = b − 0.5 ⇒ 需要 +0.5 才是边界真位置。
    """
    H, W = a.shape
    m = a >= 230
    ys, xs = np.where(m)
    rows = np.arange(ys.min() + 18, ys.max() - 17)
    cols = np.arange(xs.min() + 18, xs.max() - 17)
    lp = a[rows, :].mean(axis=0)
    tp = a[:, cols].mean(axis=1)
    x0 = first_cross(lp) + 0.5
    rv = first_cross(lp[::-1])
    x1 = (W - 1) - rv + 0.5 if rv is not None else float(W)
    y0 = first_cross(tp) + 0.5
    rv = first_cross(tp[::-1])
    y1 = (H - 1) - rv + 0.5 if rv is not None else float(H)
    return float(x0), float(x1), float(y0), float(y1)


def coverage(W, H, rect, r, z=Z):
    """Z 倍超采样下解析圆角矩形的 1× 覆盖率 cov（0..1）。"""
    x0, x1, y0, y1 = rect
    xs = (np.arange(W * z) + 0.5) / z
    ys = (np.arange(H * z) + 0.5) / z
    U = xs[None, :]
    V = ys[:, None]
    inside = (U >= x0) & (U <= x1) & (V >= y0) & (V <= y1)
    # 圆角切除区：落在该角象限内 且 到圆心距离 > r 的点。sx/sy 为该角相对圆心的方向
    # （TL: u<x0+r 且 v<y0+r ⇒ (+1,+1)；TR: (-1,+1)；BL: (+1,-1)；BR: (-1,-1)）
    cut = np.zeros(inside.shape, dtype=bool)
    for cx, cy, sx, sy in ((x0 + r, y0 + r, 1, 1), (x1 - r, y0 + r, -1, 1),
                           (x0 + r, y1 - r, 1, -1), (x1 - r, y1 - r, -1, -1)):
        du = (U - cx) * sx
        dv = (V - cy) * sy
        d2 = (U - cx) ** 2 + (V - cy) ** 2
        cut |= (du < 0) & (dv < 0) & (d2 > r * r)
    inside &= ~cut
    return inside.reshape(H, z, W, z).mean(axis=(1, 3))


def new_alpha(orig, cov, cap=GLOW_CAP):
    """主代理给定式：new = min(orig, max(cov*255, min(orig, cap)))。"""
    return np.minimum(orig, np.maximum(cov * 255.0, np.minimum(orig, cap)))


def _center_xy(W, H):
    return (np.arange(W) + 0.5)[None, :], (np.arange(H) + 0.5)[:, None]


def rect_mask(W, H, rect):
    x0, x1, y0, y1 = rect
    X, Y = _center_xy(W, H)
    return (X > x0) & (X < x1) & (Y > y0) & (Y < y1)


def corner_mask(W, H, rect, r, gap=3.0):
    x0, x1, y0, y1 = rect
    X, Y = _center_xy(W, H)
    tl = (X < x0 + r + gap) & (Y < y0 + r + gap)
    tr = (X > x1 - r - gap) & (Y < y0 + r + gap)
    bl = (X < x0 + r + gap) & (Y > y1 - r - gap)
    br = (X > x1 - r - gap) & (Y > y1 - r - gap)
    return tl | tr | bl | br


def candidate_alpha(orig, cov, W, H, rect, r, cap=GLOW_CAP):
    """**只改角**：仅在「角区方块 ∩ 矩形内」套用覆盖度式，其余像素逐字节保留原件 alpha。

    理由（实测）：给定式是全画布的，而矩形边界取 50% 交叉点时，直边淡出像素的
    `cov*255 < orig`（原件 AA 不对称，如 section 右边 255→219.7→38.1）⇒ 实测直边最大被削
    106/255、184 px 降幅>8。给定式的语义是「外侧保留柔光、只截掉旧粗折线角那部分实体」，
    旧粗折线角**只在角区**，故把式的作用域收到角区即完全等价于其语义，且直边零回归。
    """
    ap = rect_mask(W, H, rect) & corner_mask(W, H, rect, r)
    return np.where(ap, new_alpha(orig, cov, cap), orig)



# ------------------------------------------------------------------ 轮廓 / 半径 / 阶梯
def _row_cross(a, y, side, thr=CROSS):
    """某一行上，从 side 方向进入实体的首个 >= thr 交叉的 sub-pixel x；无则 None。"""
    row = a[y]
    prof = row if side == "L" else row[::-1]
    c = first_cross(prof, thr)
    if c is None:
        return None
    return c if side == "L" else (len(row) - 1) - c


def _arc_rows(rect, r, corner):
    """该角弧所在的整行区间（不含切点外的直边行）。"""
    x0, x1, y0, y1 = rect
    if corner in ("TL", "TR"):
        lo, hi = int(np.ceil(y0)), int(np.floor(y0 + r - 0.5))
    else:
        lo, hi = int(np.ceil(y1 - r + 0.5)), int(np.floor(y1 - 0.5))
    return lo, hi


def arc_points(a, rect, r, corner):
    """沿弧逐行的「视觉边界」sub-pixel 点集（alpha 的 50% 交叉 ⇒ +0.5 得边界真位置）。"""
    side = "L" if corner in ("TL", "BL") else "R"
    lo, hi = _arc_rows(rect, r, corner)
    pts = []
    for y in range(max(0, lo), min(a.shape[0], hi + 1)):
        c = _row_cross(a, y, side)
        if c is not None:
            pts.append((float(c) + 0.5, y + 0.5))
    return pts


def radius_fit(pts, rect, corner):
    """半径实测：以「弧与两条直边相切」为约束做一维搜索（比 Kasa 稳，Kasa 会退化成大半径直线拟合）。

    模型（左/上角为例）：圆心 (x0+R, y0+R)，边界 x(y) = (x0+R) − √(R² − (y0+R−y)²)。
    返回 (R, rms, n)。
    """
    x0, x1, y0, y1 = rect
    left = corner in ("TL", "BL")
    top = corner in ("TL", "TR")
    if len(pts) < 4:
        return None
    P = np.array(pts, dtype=float)
    best = None
    for R in np.arange(2.0, 32.001, 0.01):
        cx = (x0 + R) if left else (x1 - R)
        cy = (y0 + R) if top else (y1 - R)
        dy = P[:, 1] - cy
        ok = np.abs(dy) <= R
        if ok.sum() < 4:
            continue
        rad = np.sqrt(np.maximum(R * R - dy[ok] ** 2, 0.0))
        model = (cx - rad) if left else (cx + rad)
        res = model - P[ok, 0]
        rms = float(np.sqrt(np.mean(res ** 2)))
        if best is None or rms < best[1]:
            best = (float(R), rms, int(ok.sum()))
    return best


def _bilinear(a, u, v):
    H, W = a.shape
    u = min(max(u, 0.0), W - 1.001)
    v = min(max(v, 0.0), H - 1.001)
    x0, y0 = int(np.floor(u)), int(np.floor(v))
    fx, fy = u - x0, v - y0
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
            + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


def radius_diag(a, rect, corner, thr=CROSS):
    """45° 对角线独立校核：角点到弧的沿对角线距离 t ⇒ r = t / (√2 − 1)。"""
    x0, x1, y0, y1 = rect
    sx = 1.0 if corner in ("TL", "BL") else -1.0
    sy = 1.0 if corner in ("TL", "TR") else -1.0
    px = x0 if sx > 0 else x1
    py = y0 if sy > 0 else y1
    k = 1.0 / np.sqrt(2.0)
    prev = None
    for t in np.arange(0.0, 40.0, 0.02):
        val = _bilinear(a, px + sx * k * t, py + sy * k * t)
        if prev is not None and val >= thr:
            t0 = t - 0.02
            if val != prev:
                t = t0 + 0.02 * (thr - prev) / (val - prev)
            return float(t / (np.sqrt(2.0) - 1.0))
        prev = val
    return None


def _mid_rows(rect, r, corner):
    """弧体行区间（去掉两端的切点邻域各 25%）—— 半径/弧形的良态测量区。"""
    lo, hi = _arc_rows(rect, r, corner)
    n = hi - lo + 1
    k = max(1, int(round(n * 0.25)))
    return lo + k, hi - k


def corner_metrics(a, rect, r, corner):
    """角区数字证据：阶梯 / 半径（两种独立口径）/ 弧形误差 / 边缘 AA 灰阶。

    分两个行域报告：
      全弧行 —— 含两端切点邻域（弧转平处）；那里本来就每行跨 ≥2px，只作参考；
      弧体行 —— 中央 50% 行，是判「真弧 vs 折线」与「请求半径是否被实现」的域。
    """
    side = "L" if corner in ("TL", "BL") else "R"
    lo, hi = _arc_rows(rect, r, corner)
    mlo, mhi = _mid_rows(rect, r, corner)
    pts = []
    for y in range(max(0, lo), min(a.shape[0], hi + 1)):
        c = _row_cross(a, y, side)
        if c is None:
            continue
        pts.append({"x": float(c) + 0.5, "y": y + 0.5, "yidx": y,
                    "i": int(np.floor(c)) if side == "L" else int(np.ceil(c))})
    x0, x1, y0, y1 = rect
    left = (side == "L")
    cx_a = (x0 + r) if left else (x1 - r)
    cy_a = (y0 + r) if corner in ("TL", "TR") else (y1 - r)

    def stats(sel):
        P = [p for p in pts if sel(p["yidx"])]
        ints = [p["i"] for p in P]
        d = np.diff(np.array(ints)) if len(ints) > 1 else np.array([])
        d2 = np.diff(d) if len(d) > 1 else np.array([])
        dev = []
        for p in P:
            dy = p["y"] - cy_a
            if abs(dy) > r:
                continue
            rad = np.sqrt(max(r * r - dy * dy, 0.0))
            dev.append(p["x"] - ((cx_a - rad) if left else (cx_a + rad)))
        dev = np.array(dev)
        return {
            "rows": len(ints),
            "n_ge2": int(np.count_nonzero(np.abs(d) >= 2)),
            "max_abs_d2": int(np.abs(d2).max()) if len(d2) else 0,
            "dev_rms": (round(float(np.sqrt(np.mean(dev ** 2))), 3) if dev.size else None),
            "dev_max": (round(float(np.abs(dev).max()), 3) if dev.size else None),
            "n_dev_gt035": (int((np.abs(dev) > 0.35).sum()) if dev.size else 0),
            "dev_rows": int(dev.size),
            "outline_int": ints[:24],
        }

    full = stats(lambda _y: True)
    mid = stats(lambda y: mlo <= y <= mhi)
    sub = [(p["x"], p["y"]) for p in pts]
    rf = radius_fit(sub, rect, corner)
    rd = radius_diag(a, rect, corner)
    # 边缘 AA 灰阶：以拟合圆为基准，取 |到弧距离| <= 1.5px 的像素，数 [1,254] 内不同 alpha
    lv = 0
    if rf:
        R = rf[0]
        cx = (x0 + R) if left else (x1 - R)
        cy = (y0 + R) if corner in ("TL", "TR") else (y1 - R)
        w = int(R) + 4
        bx0 = int(max(0, x0 - 6)) if left else int(max(0, x1 - w))
        bx1 = int(min(a.shape[1], x0 + w)) if left else int(min(a.shape[1], x1 + 7))
        by0 = int(max(0, y0 - 6)) if corner in ("TL", "TR") else int(max(0, y1 - w))
        by1 = int(min(a.shape[0], y0 + w)) if corner in ("TL", "TR") else int(min(a.shape[0], y1 + 7))
        win = a[by0:by1, bx0:bx1]
        yy = np.arange(by0, by1)[:, None] + 0.5
        xx = np.arange(bx0, bx1)[None, :] + 0.5
        inband = np.hypot(xx - cx, yy - cy) <= (R + 1.5)
        inband &= (xx <= cx) if left else (xx >= cx)
        inband &= (yy <= cy) if corner in ("TL", "TR") else (yy >= cy)
        vals = win[inband]
        lv = int(len(np.unique(vals[(vals >= 1) & (vals <= 254)])))
    return {
        "rows": full["rows"],
        "n_nonzero": None,
        "n_ge2": full["n_ge2"],
        "max_abs_d2": full["max_abs_d2"],
        "max_abs_jump": None,
        "dev_rms": full["dev_rms"],
        "dev_max": full["dev_max"],
        "n_dev_gt035": full["n_dev_gt035"],
        "dev_rows": full["dev_rows"],
        "mid": mid,
        "r_search": (round(rf[0], 2) if rf else None),
        "r_search_rms": (round(rf[1], 3) if rf else None),
        "r_diag45": (round(rd, 2) if rd else None),
        "aa_levels": lv,
        "outline_int": full["outline_int"],
    }



def ideal_metrics(W, H, rect, r):
    """理想解析弧（纯 cov*255，不受原件 min(orig,·) 约束）的同一套指标 —— 参考基准。"""
    cov = coverage(W, H, rect, r)
    a = np.rint(np.clip(cov * 255.0, 0, 255)).astype(np.float64)
    per = {c: corner_metrics(a, rect, float(r), c) for c in ("TL", "TR", "BL", "BR")}
    rs = [per[c]["r_search"] for c in per if per[c]["r_search"]]
    dv = [per[c]["mid"]["dev_rms"] for c in per if per[c]["mid"]["dev_rms"] is not None]
    return {"max_abs_d2": max(per[c]["mid"]["max_abs_d2"] for c in per),
            "n_ge2": sum(per[c]["mid"]["n_ge2"] for c in per),
            "n_nonzero": sum(per[c]["mid"]["rows"] for c in per),
            "dev_rms_mean": (round(float(np.mean(dv)), 3) if dv else None),
            "dev_max": max(per[c]["mid"]["dev_max"] for c in per
                           if per[c]["mid"]["dev_max"] is not None),
            "r_search_mean": round(float(np.mean(rs)), 2) if rs else None}


# ------------------------------------------------------------------ 候选件
def build_candidates(global_formula=False):
    """返回 {kind: {"orig": RGBA, "rect":…, "rows": {tag: RGBA}}}。

    global_formula=True 时用给定式的**全画布**版本（仅用于量化直边代价，不作为交付候选）。
    """
    data = {}
    for k in KINDS:
        src = Image.open(BACKUP / ("x_ui_node_%s_off.png" % k)).convert("RGBA")
        assert src.size == SPRITE[k], (k, src.size)
        a = np.asarray(src.getchannel("A")).astype(np.float64)
        rect = edge_bounds(a)
        rows = {}
        for r in RADII:
            cov = coverage(src.size[0], src.size[1], rect, r)
            if global_formula:
                na = np.rint(np.clip(new_alpha(a, cov), 0, 255)).astype(np.uint8)
            else:
                na = np.rint(np.clip(candidate_alpha(a, cov, src.size[0], src.size[1], rect, r),
                                     0, 255)).astype(np.uint8)
            assert na.shape == a.shape and src.size == SPRITE[k]
            cand = Image.merge("RGBA", (*src.convert("RGB").split(), Image.fromarray(na, "L")))
            rows["r=%d" % r] = cand
        data[k] = {"orig": src, "rect": rect, "rows": rows}
    return data


def eff_color(img, kind):
    """现行正式管线的生效色：recolor(SPEC) →（select）inner_stroke(#2A5490)。
    口径直接复用 make_node_variant_a，不改其文件；用于对比图（现状行 vs 候选行同管线）。"""
    hue, sat, vmul, stroke = MF.SPEC[kind]
    out = MF.recolor(img, hue=hue, sat=sat, vmul=vmul)
    if stroke:
        out = MF.inner_stroke(out, stroke, MF.STROKE_W)
    return out


def stroke_probe(img, kind):
    """描边跟随性：环带在左端的**径向有效宽度**（＝该行环带覆盖率之和，单位 1× px）。

    直边行（实体左端 x 相同）与角区行（左端内移）分别统计 min/med/max：
      - 理想 2px 圆盘内描边 ⇒ 每行都 ≈ 2.00（圆盘核保证各法线方向厚度一致）；
      - 角区行若出现明显 >2 的离群值 ⇒ 有毛刺/钩刺。
    """
    if MF.SPEC[kind][3] is None:
        return None
    a = np.asarray(img.getchannel("A")).astype(np.float64)
    ring = MF.stroke_coverage(img.getchannel("A"), width=MF.STROKE_W)
    solid = a >= MF.SOLID_THR
    per = []
    for y in range(a.shape[0]):
        row = np.where(solid[y])[0]
        if len(row) == 0:
            continue
        xin = int(row[0])
        w = float(ring[y, max(0, xin - MF.STROKE_W - 2):xin + MF.STROKE_W + 3].sum())
        per.append((xin, w))
    if not per:
        return None
    med = int(np.median([p[0] for p in per]))
    f = lambda v: [round(float(np.min(v)), 3), round(float(np.median(v)), 3), round(float(np.max(v)), 3)]
    straight = [p[1] for p in per if p[0] == med]
    corner = [p[1] for p in per if p[0] != med]
    return {"straight_min/med/max": f(straight), "corner_min/med/max": f(corner),
            "ring_mass": round(float(ring.sum()), 1),
            "ring_px_gt50pct": int((ring > 0.5).sum())}



# ------------------------------------------------------------------ 排版小工具
def wrap(draw, text, font, maxw):
    out, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=font) <= maxw:
            line += ch
        else:
            out.append(line)
            line = ch
    if line:
        out.append(line)
    return out


def block(draw, xy, lines, font, fill, spacing=5):
    x, y = xy
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += font.size + spacing
    return y


def composite(img, bg, pad):
    """把 1× 精灵叠到真实底色上并四周留 pad 边（便于裁到画布外）。"""
    W, H = img.size
    out = Image.new("RGB", (W + 2 * pad, H + 2 * pad), bg)
    out.paste(img, (pad, pad), img)
    return out


def no_jagged_note():
    return [
        "注 1：本图是「高分辨率作画 + 抗锯齿」的候选 —— 在素材内部用 8× 超采样把圆角重画成解析圆弧；",
        "      成品仍是 1× 分辨率、尺寸与原件完全相同（nine 与摆放方式均不变）。",
        "注 2：引擎把左右端 1:1 摆放、只横向拉伸中段 ⇒ 成品**不能**靠整张放大到 2×/4× 来提分辨率"
        "（圆角会被横向挤成椭圆）。",
        "注 3：候选件的 RGB ＝ 改色前原件色、alpha ＝ 新圆角几何；对比图统一用「现行改色/描边管线生效色」画，"
        "只看形状。",
    ]


# ------------------------------------------------------------------ 对比图 ①
def sheet_corners(data, path, kind, bg, meta):
    F = MF.font
    x0, x1, y0, y1 = data[kind]["rect"]
    pad = 20
    crop = 30
    zoom = 8
    panel = crop * zoom
    lab_w = 380
    gap = 14
    margin = 26
    top = 156
    names = ["左上角 TL", "右上角 TR", "左下角 BL", "右下角 BR", "直边中段（回归对照）"]

    def crops():
        xm = int(round((x0 + x1) / 2.0))
        ym = int(round((y0 + y1) / 2.0))
        return [
            (int(round(x0 - 5)), int(round(y0 - 5))),
            (int(round(x1 + 5)) - crop, int(round(y0 - 5))),
            (int(round(x0 - 5)), int(round(y1 + 5)) - crop),
            (int(round(x1 + 5)) - crop, int(round(y1 + 5)) - crop),
            (int(round(x0 - 5)), ym - crop // 2),
        ]

    cur = Image.open(CUR / ("x_ui_node_%s_off.png" % kind)).convert("RGBA")
    a_cur = np.asarray(cur.getchannel("A")).astype(float)
    cur_r = []
    for c in ("TL", "TR", "BL", "BR"):
        m = corner_metrics(a_cur, data[kind]["rect"], 12.0, c)
        if m["r_search"]:
            cur_r.append(corner_metrics(a_cur, data[kind]["rect"],
                                        max(4.0, min(24.0, m["r_search"])), c)["r_search"])
    cur_r = float(np.mean(cur_r)) if cur_r else 7.0
    rowspec = [("现状（原件实测 r≈%.1f，粗折线感）" % cur_r, cur, None)]
    for r in RADII:
        cand = data[kind]["rows"]["r=%d" % r]
        nd = int((np.asarray(cand.getchannel("A")).astype(int)
                  != np.asarray(cur.getchannel("A")).astype(int)).sum())
        tagtxt = "（空档：与现状逐字节相同）" if nd == 0 else "（改动 %d px）" % nd
        rowspec.append(("r=%d %s" % (r, tagtxt), eff_color(cand, kind), float(r)))

    W = margin * 2 + lab_w + len(names) * (panel + gap)
    H = top + len(rowspec) * (panel + 40) + 250
    sh = Image.new("RGB", (W, H), (18, 22, 32))
    d = ImageDraw.Draw(sh)
    d.text((margin, margin), "节点圆角候选：高分辨率重画 × 三档半径（%s / %s off 态，%d×65）"
           % (KIND_CN[kind], kind, SPRITE[kind][0]), font=F(21, True), fill=(238, 243, 250))
    d.text((margin, margin + 30), "四角 + 直边中段均为 8× 最近邻放大，叠在真实图表底色 RGB%s 上（%s）"
           % (str(bg), meta), font=F(14), fill=(158, 172, 190))
    for i, nm in enumerate(names):
        cx = margin + lab_w + i * (panel + gap)
        d.text((cx + 4, top - 26), nm, font=F(15, True), fill=(255, 214, 140))

    for ri, (lab, sprite, r_nom) in enumerate(rowspec):
        comp = composite(sprite, bg, pad)
        a = np.asarray(sprite.getchannel("A")).astype(np.float64)
        per = {}
        for c in ("TL", "TR", "BL", "BR"):
            m = corner_metrics(a, data[kind]["rect"], r_nom if r_nom else 12.0, c)
            if r_nom is None and m["r_search"]:
                m = corner_metrics(a, data[kind]["rect"], max(4.0, min(24.0, m["r_search"])), c)
            per[c] = m
        mj = max(per[c]["max_abs_jump"] or 0 for c in per)
        n2 = sum(per[c]["n_ge2"] for c in per)
        d2 = max(per[c]["mid"]["max_abs_d2"] for c in per)
        n2m = sum(per[c]["mid"]["n_ge2"] for c in per)
        dv = [per[c]["mid"]["dev_rms"] for c in per if per[c]["mid"]["dev_rms"] is not None]
        dvm = [per[c]["mid"]["dev_max"] for c in per if per[c]["mid"]["dev_max"] is not None]
        off = sum(per[c]["mid"]["n_dev_gt035"] for c in per)
        offrows = max(1, sum(per[c]["mid"]["dev_rows"] for c in per))
        aa = float(np.mean([per[c]["aa_levels"] for c in per]))
        rs = [per[c]["r_search"] for c in per if per[c]["r_search"]]
        rd = [per[c]["r_diag45"] for c in per if per[c]["r_diag45"]]
        ideal = data[kind].get("ideal", {}).get(lab, {}) if r_nom else None
        yy = top + ri * (panel + 40)
        lines = [lab,
                 "半径实测 %.1f ｜ 45° 校核 %.1f" % (np.mean(rs) if rs else -1, np.mean(rd) if rd else -1),
                 "弧形误差 rms %.3f px（最大 %.2f）" % (float(np.mean(dv)) if dv else -1, max(dvm) if dvm else -1),
                 "弧体 |Δ²|max %d ｜ 2px 档 %d 处" % (d2, n2m),
                 "A A 灰阶 %.0f 级（≥8 即有 AA）" % aa]
        if ideal:
            lines.append("理想弧 rms %.3f ｜ |Δ²|max %d" % (ideal["dev_rms_mean"], ideal["max_abs_d2"]))
        block(d, (margin, yy + panel // 2 - 62), lines,
              F(14, lab.startswith("现状")), (238, 243, 250), spacing=3)
        for i, (bx, by) in enumerate(crops()):
            tile = comp.crop((bx + pad, by + pad, bx + pad + crop, by + pad + crop))
            tile = tile.resize((panel, panel), Image.NEAREST)
            px = margin + lab_w + i * (panel + gap)
            sh.paste(tile, (px, yy))
            d.rectangle([px - 1, yy - 1, px + panel, yy + panel], outline=(70, 82, 100))

    ty = top + len(rowspec) * (panel + 40) + 14
    for ln in no_jagged_note():
        d.text((margin, ty), ln, font=F(14), fill=(168, 180, 196))
        ty += 21
    d.text((margin, ty + 4), "第 5 列直边中段：本方案只重画角区，直边与柔光逐像素保留 ⇒ 该列三档与「现状」完全一致"
           "（实测直边 alpha 最大变动 0）。", font=F(14), fill=(255, 214, 140))
    d.text((margin, ty + 25), "判读要点①：本式只能「压暗」不能「提亮」—— r 小于原件既有角半径时，新弧会落到旧实体之外，"
           "该段轮廓被旧角边界牵住（弧形误差变大、折线感残留）；r ≥ 原件角半径才是完整解析弧。", font=F(14), fill=(255, 214, 140))
    d.text((margin, ty + 46), "判读要点②：整数轮廓在弧肩部（弧转平处）本来就会出现 2px/行跨步 —— 现状与理想解析弧都有，"
           "故「2px 档计数」不是判据；判据是「弧形误差」与右侧 8× 目视。", font=F(14), fill=(255, 214, 140))
    d.text((margin, ty + 67), "判读要点③：原件三类的角半径本来就不同（实测 section≈8.9／select≈13.1／frag≈14.4），"
           "同一档 r 对三类是「变大还是变小」并不一致，选档时请分别对照。", font=F(14), fill=(255, 214, 140))
    d.text((margin, ty + 88), "判读要点④：主代理按「折线顶点跨度」粗估 section 角半径约 7px；本表按 45° 对角线 + 一维搜索实测约 9px"
           "（同一折线的两种估计口径，均远小于 r=12/16）。", font=F(14), fill=(255, 214, 140))
    d.text((margin, ty + 109), "判读要点⑤：原件角区的「柔光」本身是带宽度的量化台阶（select/frag 尤明显，过渡带可达 8–10px），"
           "本方案按给定式**保留**外侧柔光 ⇒ 只修好轮廓，不重做柔光。", font=F(14), fill=(255, 214, 140))
    d.text((margin, ty + 130), "判读要点⑥：本式只能削减 ⇒ r ≤ 原件角半径时新形状反而包住旧形状、无像素可削 —— "
           "实测 r=8 三类的候选件与原件**逐字节相同**（空档）；select/frag 的 r=12 亦几乎等价（改动 41–42 px，最大差 ≤34）。",
           font=F(14), fill=(255, 140, 140))
    sh.save(path)
    print("  对比图① 写出：%s  %s" % (path, sh.size))


# ------------------------------------------------------------------ 对比图 ②
def sheet_allnodes(data, path, bg, meta):
    F = MF.font
    margin, gap, lab_h, cpad = 26, 16, 28, 6
    specs = [("section", 1), ("select", 1), ("frag", 1), ("select", 2)]
    cols = ["现状", "r=8", "r=12", "r=16"]
    cells = []
    for kind, zoom in specs:
        cur = Image.open(CUR / ("x_ui_node_%s_off.png" % kind)).convert("RGBA")
        row = [cur] + [eff_color(data[kind]["rows"]["r=%d" % r], kind) for r in RADII]
        w = (SPRITE[kind][0] + 2 * cpad) * zoom
        h = (SPRITE[kind][1] + 2 * cpad) * zoom
        cells.append((kind, zoom, row, w, h))
    width = margin * 2 + max(c[3] * len(cols) + gap * (len(cols) - 1) for c in cells)
    rowheights = [lab_h + c[4] + 24 for c in cells]
    H = 128 + sum(rowheights) + 190
    sh = Image.new("RGB", (int(width), int(H)), (18, 22, 32))
    d = ImageDraw.Draw(sh)
    d.text((margin, margin), "节点圆角候选：整节点观感（三类 × 三档半径，叠在真实图表底色 RGB%s 上）" % str(bg),
           font=F(21, True), fill=(238, 243, 250))
    d.text((margin, margin + 30), "1:1 逐像素摆放（三类各一行），列＝现状 / r=8 / r=12 / r=16；末行 select 为 2× 最近邻放大。%s"
           % meta, font=F(14), fill=(158, 172, 190))
    y = 128
    for ci, (kind, zoom, row, cw, ch) in enumerate(cells):
        d.text((margin, y), "%s（%s）　%s" % (KIND_CN[kind], kind, "×2 放大" if zoom == 2 else "1:1"),
               font=F(16, True), fill=(255, 214, 140))
        x = margin
        for lab, im in zip(cols, row):
            t = composite(im, bg, cpad)
            if zoom != 1:
                t = t.resize((t.width * zoom, t.height * zoom), Image.NEAREST)
            sh.paste(t, (x, y + lab_h))
            d.rectangle([x - 1, y + lab_h - 1, x + t.width, y + lab_h + t.height], outline=(70, 82, 100))
            d.text((x + 4, y + lab_h + t.height + 4), lab, font=F(15, True), fill=(210, 220, 234))
            x += t.width + gap
        y += rowheights[ci]
    ty = y + 16
    for ln in no_jagged_note():
        d.text((margin, ty), ln, font=F(14), fill=(168, 180, 196))
        ty += 21
    d.text((margin, ty + 4), "整节点判读：角半径变大后节点四角的「视觉重量」随之变化 —— r=16 已接近药丸形；"
           "若要保持现有机读轮廓，建议只把「折线」换成真弧、半径取接近现状者。", font=F(14), fill=(255, 214, 140))
    sh.save(path)
    print("  对比图② 写出：%s  %s" % (path, sh.size))


# ------------------------------------------------------------------ 主流程
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, meta = now_bg()
    print("底色 RGB%s（%s）" % (str(bg), meta))
    print("参数：Z=%d  RADII=%s  GLOW_CAP=%d  CROSS=%.1f  STROKE_W=%d SS=%d SOLID_THR=%d"
          % (Z, RADII, GLOW_CAP, CROSS, MF.STROKE_W, MF.SS, MF.SOLID_THR))

    # —— 自证：现行正式件确实等于「原形备份 → 现行管线」⇒ 候选行 = 正式链在半径 r 下的预测
    print("\n[自证] 现行件 == recolor(原形备份) ?（select 含描边）")
    for k in KINDS:
        cur = np.asarray(Image.open(CUR / ("x_ui_node_%s_off.png" % k)).convert("RGBA"))
        mine = np.asarray(eff_color(Image.open(BACKUP / ("x_ui_node_%s_off.png" % k)).convert("RGBA"), k))
        same = bool((cur == mine).all())
        print("   %-8s 逐字节相同 = %s" % (k, same))

    data = build_candidates()
    rep = {"params": {"Z": Z, "RADII": list(RADII), "GLOW_CAP": GLOW_CAP,
                      "CROSS": CROSS, "stroke": {"color": "#2A5490", "w": MF.STROKE_W,
                                                 "SS": MF.SS, "solid_thr": MF.SOLID_THR}},
           "bg": list(bg), "bg_src": meta, "kinds": {}}

    # —— 候选件落盘
    print("\n[候选件]")
    for k in KINDS:
        src, rect, rows = data[k]["orig"], data[k]["rect"], data[k]["rows"]
        a_orig = np.asarray(src.getchannel("A")).astype(np.float64)
        rep["kinds"][k] = {"sprite": SPRITE[k], "rect": [round(v, 3) for v in rect],
                           "b230_bbox": None, "orig": {}, "rows": {}}
        m = a_orig >= 230
        ys, xs = np.where(m)
        rep["kinds"][k]["b230_bbox"] = [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())]
        for r in RADII:
            tag = "r=%d" % r
            cand = rows[tag]
            p = OUT / ("候选_x_ui_node_%s_off_r%d.png" % (k, r))
            cand.save(p)
            files = [p.name]
            if k == "select":
                # 对**新**轮廓做 4× 圆盘腐蚀取环带 ⇒ 只改 RGB、alpha 逐字节沿用候选件
                st = MF.inner_stroke(cand, MF.SPEC[k][3], MF.STROKE_W)
                ps = OUT / ("候选_x_ui_node_%s_off_r%d_描边.png" % (k, r))
                st.save(ps)
                eff = eff_color(cand, k)
                pe = OUT / ("候选_x_ui_node_%s_off_r%d_生效色_描边.png" % (k, r))
                eff.save(pe)
                files += [ps.name, pe.name]
                rep["kinds"][k].setdefault("stroke", {})[tag] = {
                    "stroked": ps.name, "eff": pe.name, "probe": stroke_probe(eff, k)}
            rep["kinds"][k].setdefault("files", {})[tag] = files
            print("   %s %s  %s" % (k, tag, " / ".join(files)))


    # —— 数字证据
    print("\n[数字证据]  （阶梯 = 沿弧逐行整数轮廓的差分；≥2px 记一档「粗折线跳档」）")
    for k in KINDS:
        A = np.asarray(data[k]["orig"].getchannel("A")).astype(np.float64)
        rect = data[k]["rect"]
        ent = rep["kinds"][k]
        items = [("现状", A, None)]
        for r in RADII:
            items.append(("r=%d" % r,
                          np.asarray(data[k]["rows"]["r=%d" % r].getchannel("A")).astype(np.float64), float(r)))
        for lab, arr, r_arc in items:
            per = {}
            for c in ("TL", "TR", "BL", "BR"):
                # 现状无标称半径：先用 r=12 粗测自身弧半径，再以其为弧行区间复测（两遍）
                m = corner_metrics(arr, rect, r_arc if r_arc else 12.0, c)
                if r_arc is None and m["r_search"]:
                    m = corner_metrics(arr, rect, max(4.0, min(24.0, m["r_search"])), c)
                per[c] = m
            mj = 0
            n2 = sum(per[c]["n_ge2"] for c in per)
            nn = sum(per[c]["rows"] for c in per)
            nr = sum(per[c]["rows"] for c in per)
            rs = [per[c]["r_search"] for c in per if per[c]["r_search"]]
            rd = [per[c]["r_diag45"] for c in per if per[c]["r_diag45"]]
            rmsd = [per[c]["r_search_rms"] for c in per if per[c]["r_search_rms"] is not None]
            mid_dev = [per[c]["mid"]["dev_rms"] for c in per if per[c]["mid"]["dev_rms"] is not None]
            mid_rows = sum(per[c]["mid"]["rows"] for c in per)
            mid_off = sum(per[c]["mid"]["n_dev_gt035"] for c in per)
            mid_devrows = sum(per[c]["mid"]["dev_rows"] for c in per)
            row = {
                "max_abs_jump": mj, "n_ge2": n2, "n_nonzero": nn, "arc_rows": nr,
                "max_abs_d2": max(per[c]["max_abs_d2"] for c in per),
                "r_search_mean": round(float(np.mean(rs)), 2) if rs else None,
                "r_search_range": [round(float(min(rs)), 2), round(float(max(rs)), 2)] if rs else None,
                "r_search_rms_max": (round(max(rmsd), 3) if rmsd else None),
                "r_diag45_mean": round(float(np.mean(rd)), 2) if rd else None,
                # ★ 弧体（中央 50% 行）—— 判「真弧 vs 折线」与「请求半径是否被实现」的主指标
                "mid_rows": mid_rows,
                "mid_n_ge2": sum(per[c]["mid"]["n_ge2"] for c in per),
                "mid_max_abs_d2": max(per[c]["mid"]["max_abs_d2"] for c in per),
                "mid_dev_rms_mean": (round(float(np.mean(mid_dev)), 3) if mid_dev else None),
                "mid_dev_max": max(per[c]["mid"]["dev_max"] for c in per
                                   if per[c]["mid"]["dev_max"] is not None),
                "mid_dev_frac_gt035": (round(mid_off / max(1, mid_devrows), 3) if mid_devrows else None),
                "aa_levels_mean": round(float(np.mean([per[c]["aa_levels"] for c in per])), 1),
                "alpha_unique_whole": int(len(np.unique(arr.astype(np.uint8)))),
                "per_corner": per,
            }
            if lab != "现状":
                R = float(lab.split("=")[1])
                gz = corner_mask(A.shape[1], A.shape[0], rect, R, gap=6.0)
                drop = (A - arr)[(~gz) & (A > 0)]
                row["straight_edge_max_drop"] = round(float(drop.max()), 1) if drop.size else 0.0
                row["straight_edge_n_gt8"] = int((drop > 8).sum())
                row["n_alpha_increased"] = int((arr > A).sum())
            ent["rows"][lab] = row
            print("   %-8s %-5s 弧体：弧形误差 rms=%.3f max=%.3f（%.0f%% 行>0.35px）｜|Δ²|max=%d 2px档=%d "
                  "‖ 半径实测=%.2f[%s] 45°=%.2f ‖ 直边最大降=%.1f"
                  % (k, lab, row["mid_dev_rms_mean"], row["mid_dev_max"],
                     100.0 * (row["mid_dev_frac_gt035"] or 0), row["mid_max_abs_d2"], row["mid_n_ge2"],
                     row["r_search_mean"], row["r_search_range"], row["r_diag45_mean"],
                     row.get("straight_edge_max_drop", 0.0)))

    # —— 理想解析弧基准（同口径指标；用于说明候选离「纯解析弧」有多近）
    print("\n[基准] 理想解析弧（cov*255，无原件 min 约束）")
    for k in KINDS:
        W, H = SPRITE[k]
        rect = data[k]["rect"]
        ent = rep["kinds"][k]
        ent["ideal"] = {}
        for r in RADII:
            im = ideal_metrics(W, H, rect, float(r))
            ent["ideal"]["r=%d" % r] = im
            data[k]["ideal"] = ent["ideal"]
            print("   %-8s r=%-3d 弧形误差 rms=%.3f max=%.3f ｜ 半径实测=%s ｜ |Δ²|max=%d 2px档=%d"
                  % (k, r, im["dev_rms_mean"], im["dev_max"], im["r_search_mean"],
                     im["max_abs_d2"], im["n_ge2"]))

    # —— 给定式「全画布版」的直边代价（仅量化，不作为交付候选）
    print("\n[对照] 给定式全画布版（未经角区收窄）的直边代价")
    gdata = build_candidates(global_formula=True)
    for k in KINDS:
        A = np.asarray(gdata[k]["orig"].getchannel("A")).astype(np.float64)
        for r in RADII:
            arr = np.asarray(gdata[k]["rows"]["r=%d" % r].getchannel("A")).astype(np.float64)
            gz = corner_mask(A.shape[1], A.shape[0], gdata[k]["rect"], float(r), gap=6.0)
            drop = (A - arr)[(~gz) & (A > 0)]
            rep["kinds"][k].setdefault("global_formula_straight_cost", {})["r=%d" % r] = {
                "max_drop": round(float(drop.max()), 1) if drop.size else 0.0,
                "n_gt8": int((drop > 8).sum())}
            print("   %-8s r=%-3d 直边最大降 %6.1f  降>8 的像素 %5d"
                  % (k, r, rep["kinds"][k]["global_formula_straight_cost"]["r=%d" % r]["max_drop"],
                     rep["kinds"][k]["global_formula_straight_cost"]["r=%d" % r]["n_gt8"]))

    # —— 其它不变量（尺寸 / alpha 不上升 / RGB 不动 / 描边）
    print("\n[不变量] 尺寸 / alpha 未上升 / RGB 不动 / 与原件差异 / 描边径向宽度（1× px）")
    for k in KINDS:
        ent = rep["kinds"][k]
        for r in RADII:
            tag = "r=%d" % r
            a0 = np.asarray(data[k]["orig"].getchannel("A")).astype(int)
            a1 = np.asarray(data[k]["rows"][tag].getchannel("A")).astype(int)
            rgb0 = np.asarray(data[k]["orig"].convert("RGB"))
            rgb1 = np.asarray(data[k]["rows"][tag].convert("RGB"))
            nd = int((a1 != a0).sum())
            dmax = int(np.abs(a1 - a0).max())
            ent["rows"][tag]["diff_vs_orig_px"] = nd
            ent["rows"][tag]["diff_vs_orig_max"] = dmax
            sp = (ent.get("stroke", {}).get(tag) or {}).get("probe") or "—"
            print("   %-8s %-5s 尺寸%s=%s alpha上升=%d RGB同=%s 改动像素=%4d（最大差%3d）%s"
                  % (k, tag, SPRITE[k], data[k]["rows"][tag].size == SPRITE[k],
                     int((a1 > a0).sum()), bool((rgb0 == rgb1).all()), nd, dmax,
                     "" if sp == "—" else "\n            描边 %s" % sp))



    # —— 对比图
    print("\n[对比图]")
    sheet_corners(data, OUT / "对比_圆角半径_三档.png", "section", bg, meta)
    sheet_allnodes(data, OUT / "对比_圆角候选_全节点.png", bg, meta)

    txt = OUT / "圆角候选_数字证据.txt"
    with open(txt, "w", encoding="utf-8") as f:
        f.write(json.dumps(rep, ensure_ascii=False, indent=2))
    print("  数字证据写出：%s" % txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
