# -*- coding: utf-8 -*-
"""节点底图「轮廓解析化 + 柔光重做」候选件 / 对比图生成器（ISSUE-20260927-07 · 解析化轮）

只产出**候选件与对比图**到证据目录；**不改正式素材**（krkr/assets/ui 只读）、**不跑引擎**、
**不改** make_node_variant_a.py（只 import 复用改色 / 描边口径）。

本轮要一次解决三件事
--------------------
① 底边「凸起」：实测根因 = 选择支底边 y=56 行 alpha 在阈值附近抖动（x=167 处 229 < 230）
   ⇒ `solid = alpha>=230` 掩码在该列出现 **1px 缺口** ⇒ 圆盘腐蚀的描边环带跟着鼓包。
   本轮不再「调阈值」，而是**整条轮廓解析化** ⇒ 掩码边界变成解析偏移曲线，缺口不可能存在。
② 四角 2px 折线：解析圆角矩形（半径可选）取代旧折线弧。
③ 柔光重做：不再用 GLOW_CAP 截断式（会留平台带），改用**逐边实测径向剖面表**。

算法（对主代理给定式的**保真化实现**，两处改动均有实测依据，见下）
------------------------------------------------------------------
主代理给定式：① 求实体矩形与半径 ② Z=8 画解析圆角矩形得 cov ③ 外侧柔光剖面 glow
              ④ new_alpha = max(cov*255, glow)

实测发现两处会导致直边回归，故把「coverage 项」与「glow 项」统一成**一条径向传递函数**：

  【改动 1 · 边缘不是 box 覆盖度】实测三条直边的边沿像素远亮于 box 覆盖度：
    section 左边 边界 6.734 ⇒ 边界格(x=6)覆盖 26.6%（box 给 68），实测 **91**；
    section 顶边 边界 7.019 ⇒ 最后内部格(x=7)覆盖 98.1%（box 给 250），实测 **215**。
    若按 `max(cov*255, glow)`（glow 只在外侧）⇒ 该列 alpha 变 68（−23）；select 底边更糟：
    y=57 实测 140 而 box 覆盖度只给 51（−89）⇒ 会沿底边出现一条**暗环**。
  【改动 2 · 外侧「首格」不是纯柔光】边界外的第 1 格同时含边缘过渡与柔光（section L 72.1、
    select 底 106.4…），把它当纯 glow 会高估。

  故改为：**以 50% 交叉点为轮廓、按边实测「alpha = f_边(到轮廓的有符号距离 t)」的径向剖面表**
  （查表 + 线性插值，主代理推荐的「后者更保真」），再对四边按轮廓法线方向做角向混合：

      alpha(p) = Σ_s w_s(p) · f_s( t(p) )        Σ w_s = 1
      t(p) = 到解析轮廓的有符号距离（外正内负，由 4 段直线 + 4 段圆弧的精确距离场给出）
      w_s(p) = 最近轮廓点的外向法线在该边上的分量（直线段=1，角弧上按角度混合）

  该式**完整包含**给定式：f_s(t) 在外侧就是实测柔光剖面 glow(t)，在内侧就是实测边缘过渡；
  「解析轮廓」与「柔光重做」两个目标都由它实现，且**直边逐像素可达零回归**（见报告）。

用法
----
    python "_工作/ISSUE-20260927-07_节点描边与系统按钮/复现脚本/make_node_contour_candidates.py"
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image, ImageDraw                                          # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
ISSUE = UI / "_工作" / "ISSUE-20260927-07_节点描边与系统按钮"
REPRO5 = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "复现脚本"
BACKUP = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "原形备份"
CUR = UI / "krkr" / "assets" / "ui"
OUT = ISSUE / "取证" / "圆角候选"
SHOT = (UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "取证" / "E2_自证"
        / "E2_真实数据验收图_shot_84_flowchart.png")

sys.path.insert(0, str(REPRO5))
import make_node_variant_a as MF                                          # noqa: E402

# ------------------------------------------------------------------ 参数
CROSS = 127.5            # 轮廓定义：alpha 的 50% 覆盖交叉点（沿用上一轮口径）
SOLID = MF.SOLID_THR     # 230（掩码阈值，不改）
KINDS = ("section", "select", "frag")
KIND_CN = {"section": "章节点", "select": "选择支节点", "frag": "番外节点"}
SPRITE = {"section": (236, 65), "select": (263, 65), "frag": (228, 65)}
UNIFORM_R = (12, 16, 20)
NOTCH_X = 167            # 主代理定位的底边缺口列
BG_FALLBACK = (39, 45, 59)
BG_SAMPLE_XY = (400, 190)
PROF_LO, PROF_HI = -6.0, 20.0     # 剖面表采样的有符号距离范围（px）
CONTOUR_ORDER = ("L", "T", "R", "B")


# ------------------------------------------------------------------ 基础量测
def first_cross(prof, thr=CROSS):
    idx = np.where(np.asarray(prof, dtype=float) >= thr)[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    if i == 0:
        return 0.0
    a, b = float(prof[i - 1]), float(prof[i])
    if b == a:
        return float(i)
    return (i - 1) + (thr - a) / (b - a)


def rect_of(a, pole=18):
    """四边 50% 交叉点（sub-pixel，含 +0.5 相位修正）。"""
    H, W = a.shape
    m = a >= 230
    ys, xs = np.where(m)
    rows = np.arange(ys.min() + pole, ys.max() - pole + 1)
    cols = np.arange(xs.min() + pole, xs.max() - pole + 1)
    lp = a[rows, :].mean(axis=0)
    tp = a[:, cols].mean(axis=1)
    return (float(first_cross(lp) + 0.5),
            float((W - 1) - first_cross(lp[::-1]) + 0.5),
            float(first_cross(tp) + 0.5),
            float((H - 1) - first_cross(tp[::-1]) + 0.5))


def _radius_fit_span(a, rect, corner, span):
    """在 [角点, 角点+span) 的行区间内做一维搜索拟合（span 须 ≈ 弧高，否则直边行会污染拟合）。"""
    x0, x1, y0, y1 = rect
    left = corner in ("TL", "BL")
    top = corner in ("TL", "TR")
    side = "L" if left else "R"
    if top:
        rows = np.arange(int(np.ceil(y0)), int(np.ceil(y0 + span)))
    else:
        rows = np.arange(int(np.ceil(y1 - span)), int(np.floor(y1)))
    pts = []
    for y in rows:
        prof = a[y]
        c = first_cross(prof[::-1]) if side == "R" else first_cross(prof)
        if c is None:
            continue
        xb = ((len(prof) - 1) - c if side == "R" else c) + 0.5
        pts.append((xb, y + 0.5))
    if len(pts) < 4:
        return None, None, 0
    P = np.array([p[0] for p in pts], dtype=float)
    yy = np.array([p[1] for p in pts], dtype=float)
    best = None
    for R in np.arange(2.0, 30.001, 0.01):
        cx = (x0 + R) if left else (x1 - R)
        cy = (y0 + R) if top else (y1 - R)
        dy = yy - cy
        ok = np.abs(dy) <= R
        if ok.sum() < 4:
            continue
        rad = np.sqrt(np.maximum(R * R - dy[ok] ** 2, 0.0))
        model = (cx - rad) if left else (cx + rad)
        rms = float(np.sqrt(np.mean((model - P[ok]) ** 2)))
        if best is None or rms < best[1]:
            best = (float(R), rms, int(ok.sum()))
    return best if best else (None, None, 0)


def radius_corner(a, rect, corner, span0=26.0, iters=4):
    """逐角半径：两遍迭代（粗测 span ⇒ 按实测半径收紧 span）避免直边行污染拟合。"""
    span = span0
    R = None
    for _ in range(iters):
        r, rms, n = _radius_fit_span(a, rect, corner, span)
        if r is None:
            break
        R = (r, rms, n)
        span = max(3.5, r * 1.12)
    if R is None:
        return None, None, 0
    r, rms, n = _radius_fit_span(a, rect, corner, span)
    return (R if r is None else (r, rms, n))


def corner_diag_radius(a, rect, corner, thr=CROSS):
    """45° 对角独立校核（另一路口径）：自**角点**沿对角线**向内**走，首次升过 50% 阈值处即圆弧。

    注意方向：圆角把矩形角点切在形状之外 ⇒ 向外走永远不穿轮廓；对称地，向内走 t 处穿轮廓，
    t = r(√2−1) ⇒ r = t/(√2−1)。
    """
    x0, x1, y0, y1 = rect
    left = corner in ("TL", "BL")
    top = corner in ("TL", "TR")
    px = x0 if left else x1
    py = y0 if top else y1
    dx = 1.0 if left else -1.0        # 由角点向**内**（TL 为右下）
    dy = 1.0 if top else -1.0
    k = 1.0 / np.sqrt(2.0)
    H, W = a.shape

    def bil(u, v):
        u = min(max(u, 0.0), W - 1.001)
        v = min(max(v, 0.0), H - 1.001)
        iu, iv = int(np.floor(u)), int(np.floor(v))
        fu, fv = u - iu, v - iv
        return float(a[iv, iu] * (1 - fu) * (1 - fv) + a[iv, iu + 1] * fu * (1 - fv)
                     + a[iv + 1, iu] * (1 - fu) * fv + a[iv + 1, iu + 1] * fu * fv)
    prev = None
    for t in np.arange(-30.0, 40.0, 0.02):
        val = bil(px + dx * k * t, py + dy * k * t)
        if prev is not None and val >= thr > prev:
            t0 = t - 0.02
            tt = t0 + (0.02 * (thr - prev) / (val - prev) if val != prev else 0.0)
            return float(tt / (np.sqrt(2.0) - 1.0))
        prev = val
    return None


# ------------------------------------------------------------------ 解析形状距离场
def _out_dir(corner):
    """该角**向外**的单位方向符号（ox, oy）：TL=(-1,-1)、TR=(+1,-1)、BR=(+1,+1)、BL=(-1,+1)。"""
    return (-1.0 if corner in ("TL", "BL") else 1.0,
            -1.0 if corner in ("TL", "TR") else 1.0)


def shape_fields(W, H, rect, radii):
    """解析圆角矩形（四角半径可不同）的距离场与轮廓法线。

    返回 (dist_unsigned, inside, t_signed, weights{L,T,R,B}, normal_x, normal_y)
      t_signed = +dist 在形状外 / −dist 在形状内（轮廓 = dist 0 等值线）
      weights  = 最近轮廓点的**外向法线**在各边上的分量（归一化）
    """
    x0, x1, y0, y1 = rect
    rTL, rTR, rBR, rBL = radii
    X = (np.arange(W) + 0.5)[None, :].astype(float)
    Y = (np.arange(H) + 0.5)[:, None].astype(float)
    Xb = np.broadcast_to(X, (H, W)).copy()
    Yb = np.broadcast_to(Y, (H, W)).copy()

    ins = (Xb >= x0) & (Xb <= x1) & (Yb >= y0) & (Yb <= y1)
    # 角象限：ox/oy = **向外**方向（TL 为左上）。切掉区 = 「向外的那个象限」且 ρ > r。
    corners = ((x0 + rTL, y0 + rTL, rTL, "TL"), (x1 - rTR, y0 + rTR, rTR, "TR"),
               (x1 - rBR, y1 - rBR, rBR, "BR"), (x0 + rBL, y1 - rBL, rBL, "BL"))
    for cx, cy, r, nm in corners:
        ox, oy = _out_dir(nm)
        du, dv = Xb - cx, Yb - cy
        ins &= ~((du * ox > 0) & (dv * oy > 0) & (np.hypot(du, dv) > r))

    best = np.full((H, W), np.inf)
    nxb = np.zeros((H, W))
    nyb = np.zeros((H, W))

    def take(d, vx, vy):
        nonlocal best, nxb, nyb
        m = d < best
        best = np.where(m, d, best)
        nxb = np.where(m, vx, nxb)
        nyb = np.where(m, vy, nyb)

    def seg(ax, ay, bx, by):
        ux, uy = bx - ax, by - ay
        L2 = ux * ux + uy * uy
        tp = np.clip(((Xb - ax) * ux + (Yb - ay) * uy) / L2, 0.0, 1.0)
        qx, qy = ax + tp * ux, ay + tp * uy
        d = np.hypot(Xb - qx, Yb - qy)
        dd = np.where(d > 1e-9, d, 1.0)
        return d, (Xb - qx) / dd, (Yb - qy) / dd

    take(*seg(x0 + rTL, y0, x1 - rTR, y0))            # 顶
    take(*seg(x0 + rBL, y1, x1 - rBR, y1))            # 底
    take(*seg(x0, y0 + rTL, x0, y1 - rBL))            # 左
    take(*seg(x1, y0 + rTR, x1, y1 - rBR))            # 右
    for cx, cy, r, nm in corners:                     # 四段圆弧
        ox, oy = _out_dir(nm)
        du, dv = Xb - cx, Yb - cy
        rho = np.hypot(du, dv)
        inarc = (du * ox >= -1e-9) & (dv * oy >= -1e-9)
        d = np.where(inarc, np.abs(rho - r), np.inf)
        dd = np.where(rho > 1e-9, rho, 1.0)
        sgn = np.where(rho - r >= 0, 1.0, -1.0)
        take(d, sgn * du / dd, sgn * dv / dd)

    nxb = np.where(ins, -nxb, nxb)                    # 内部取反 ⇒ 统一为外向法线
    nyb = np.where(ins, -nyb, nyb)
    tsig = np.where(ins, -best, best)
    wL = np.maximum(-nxb, 0.0)
    wR = np.maximum(nxb, 0.0)
    wT = np.maximum(-nyb, 0.0)
    wB = np.maximum(nyb, 0.0)
    tot = wL + wR + wT + wB
    tot = np.where(tot > 0, tot, 1.0)
    return best, ins, tsig, {"L": wL / tot, "R": wR / tot, "T": wT / tot, "B": wB / tot}, nxb, nyb


# ------------------------------------------------------------------ 剖面表
def collect_profiles(a, rect, band_radius):
    """按边实测「alpha = f(到 50% 轮廓的有符号距离 t)」样本（t 外正内负）。

    直线带 = 去掉四角（半径 band_radius + 2）后的中央区；每格取该带的均值 ⇒ 抗单像素噪声。
    """
    x0, x1, y0, y1 = rect
    H, W = a.shape
    br = np.arange(int(np.ceil(y0 + band_radius + 2)), int(np.floor(y1 - band_radius - 2)) + 1)
    bc = np.arange(int(np.ceil(x0 + band_radius + 2)), int(np.floor(x1 - band_radius - 2)) + 1)
    assert len(br) >= 6 and len(bc) >= 6, (band_radius, len(br), len(bc))
    prof = {}
    for side in CONTOUR_ORDER:
        if side in ("L", "R"):
            vals = a[br, :].mean(axis=0)
            b = x0 if side == "L" else x1
            n = W
            t_of = (lambda i, b=b, s=side: (b - (i + 0.5)) if s == "L" else ((i + 0.5) - b))
        else:
            vals = a[:, bc].mean(axis=1)
            b = y0 if side == "T" else y1
            n = H
            t_of = (lambda i, b=b, s=side: (b - (i + 0.5)) if s == "T" else ((i + 0.5) - b))
        ts, vs = [], []
        for i in range(n):
            t = t_of(i)
            if PROF_LO <= t <= PROF_HI:
                ts.append(t)
                vs.append(float(vals[i]))
        o = np.argsort(ts)
        ts = np.asarray(ts, dtype=float)[o]
        vs = np.asarray(vs, dtype=float)[o]
        # 尾部补锚点：外侧伸到 0、内侧钉住内部常量（实测内部 alpha = 253）
        inner = float(np.median(vs[ts <= PROF_LO + 1.0])) if (ts <= PROF_LO + 1.0).any() else 253.0
        ts = np.concatenate([[PROF_LO - 3.0], ts])
        vs = np.concatenate([[inner], vs])
        if vs[-1] > 0.5:
            ts = np.concatenate([ts, [ts[-1] + 3.0]])
            vs = np.concatenate([vs, [0.0]])
        prof[side] = (ts, vs)
    return prof, {"rows": br, "cols": bc}


def synth(prof, fields):
    """alpha = Σ_s w_s · f_s(t)（角向混合）。"""
    _d, _ins, tsig, w, _nx, _ny = fields
    out = np.zeros_like(tsig)
    for s in CONTOUR_ORDER:
        t, v = prof[s]
        out += w[s] * np.interp(tsig, t, v)
    return out


# ------------------------------------------------------------------ 数值指标
def annulus_profile(a, rect, side, dmax=12, margin=None):
    """相位无关的 1px 环带均值：bin d 覆盖 [b+d, b+d+1)（**外向**为正方向）。

    margin 默认 max(12, 该件角半径+2) ⇒ 直线带足够长（与 collect_profiles 同带口径）。
    """
    x0, x1, y0, y1 = rect
    H, W = a.shape
    if margin is None:
        margin = 22
    if side in ("L", "R"):
        rows = np.arange(int(y0) + margin, int(y1) - margin + 1)
        vals = a[rows, :].mean(axis=0)
        b = x0 if side == "L" else x1
    else:
        cols = np.arange(int(x0) + margin, int(x1) - margin + 1)
        vals = a[:, cols].mean(axis=1)
        b = y0 if side == "T" else y1
    out = []
    for d in range(dmax + 1):
        if side in ("L", "T"):
            lo, hi = b - d - 1.0, b - d
        else:
            lo, hi = b + d, b + d + 1.0
        tot, wsum = 0.0, 0.0
        for i in range(int(np.floor(lo)) - 1, int(np.ceil(hi)) + 1):
            if i < 0 or i >= len(vals):
                continue
            ov = min(hi, i + 1.0) - max(lo, float(i))
            if ov > 0:
                tot += vals[i] * ov
                wsum += ov
        out.append(round(tot / wsum, 2) if wsum > 0 else None)
    return out


def mask_report(a, rect, side, thr=SOLID):
    """掩码(alpha>=thr)在该边的首/末实体像素逐行(列)清单 ⇒ 缺口/鼓包的直接证据。"""
    x0, x1, y0, y1 = rect
    idxs = []
    if side in ("L", "R"):
        rng = range(int(y0) + 20, int(y1) - 19)
        for y in rng:
            w = np.where(a[y] >= thr)[0]
            if len(w):
                idxs.append((y, int(w[0]) if side == "L" else int(w[-1])))
    else:
        rng = range(int(x0) + 20, int(x1) - 19)
        for x in rng:
            w = np.where(a[:, x] >= thr)[0]
            if len(w):
                idxs.append((x, int(w[0]) if side == "T" else int(w[-1])))
    vals = np.array([v for _k, v in idxs])
    dd = np.diff(vals) if len(vals) > 1 else np.array([0])
    return {"n": len(vals), "uniq": sorted(set(int(v) for v in vals)),
            "n_step": int((dd != 0).sum()), "max_step": int(np.abs(dd).max()) if len(dd) else 0,
            "holes": [(int(k), int(v)) for k, v in
                      [(k, v) for k, v in idxs if abs(v - float(np.median(vals))) > 0.5]][:20]}


def ring_width_radial(img, rect, radii, samples=240):
    """沿解析轮廓法线的**径向**描边宽度（覆盖率沿法线积分，单位 1× px）。"""
    cov = MF.stroke_coverage(img.getchannel("A"), width=MF.STROKE_W)
    H, W = cov.shape
    x0, x1, y0, y1 = rect
    rTL, rTR, rBR, rBL = radii
    pts = []
    # 四条直边的内点（避开角弧 4px）
    for i in range(samples):
        u = (i + 0.5) / samples
        if rTL + 4 <= x0 + u * (x1 - x0) <= x1 - rTR - 4:
            pts.append((x0 + u * (x1 - x0), y0, 0.0, -1.0, "T"))
            pts.append((x0 + u * (x1 - x0), y1, 0.0, 1.0, "B"))
        if rTL + 4 <= y0 + u * (y1 - y0) <= y1 - rBL - 4:
            pts.append((x0, y0 + u * (y1 - y0), -1.0, 0.0, "L"))
            pts.append((x1, y0 + u * (y1 - y0), 1.0, 0.0, "R"))
    # 四段弧
    for cx, cy, r, a0 in ((x0 + rTL, y0 + rTL, rTL, 180.0), (x1 - rTR, y0 + rTR, rTR, 270.0),
                          (x1 - rBR, y1 - rBR, rBR, 0.0), (x0 + rBL, y1 - rBL, rBL, 90.0)):
        for j in range(24):
            ang = np.deg2rad(a0 + 90.0 * (j + 0.5) / 24.0)
            pts.append((cx + r * np.cos(ang), cy + r * np.sin(ang),
                        np.cos(ang), np.sin(ang), "arc"))

    def bil(u, v):
        u = min(max(u, 0.0), W - 1.001)
        v = min(max(v, 0.0), H - 1.001)
        iu, iv = int(np.floor(u)), int(np.floor(v))
        fu, fv = u - iu, v - iv
        return float(cov[iv, iu] * (1 - fu) * (1 - fv) + cov[iv, iu + 1] * fu * (1 - fv)
                     + cov[iv + 1, iu] * (1 - fu) * fv + cov[iv + 1, iu + 1] * fu * fv)
    ws = []
    for px, py, nx, ny, _tag in pts:
        s, step = 0.0, 0.2
        for k in range(1, 26):
            s += bil(px - nx * k * step, py - ny * k * step) * step
        ws.append(s)
    ws = np.array(ws)
    tags = np.array([p[4] for p in pts])
    stra = ws[tags != "arc"]
    arc = ws[tags == "arc"]

    def f(v):
        if not len(v):
            return None
        return {"p05": round(float(np.percentile(v, 5)), 3), "med": round(float(np.median(v)), 3),
                "p95": round(float(np.percentile(v, 95)), 3), "max": round(float(v.max()), 3),
                "n_lt1": int((v < 1).sum()), "n_gt3": int((v > 3).sum()), "n": int(len(v))}
    return {"直边": f(stra), "圆角弧": f(arc)}


def ring_width_at(rect, x0c, x1c, cov):
    """底边（y=rect[3]）上 x∈[x0c,x1c] 各列的**竖向**径向描边宽度（沿法线向内积分）。"""
    x0, x1, y0, y1 = rect
    out = []
    for x in range(int(x0c), int(x1c) + 1):
        s = 0.0
        for k in range(1, 26):
            s += _bil(cov, x + 0.5, y1 - 0.2 * k) * 0.2      # 底边外向 = +y ⇒ 向内 = −y
        out.append(round(s, 3))
    return out


def _bil(a, u, v):
    H, W = a.shape
    u = min(max(u, 0.0), W - 1.001)
    v = min(max(v, 0.0), H - 1.001)
    iu, iv = int(np.floor(u)), int(np.floor(v))
    fu, fv = u - iu, v - iv
    return float(a[iv, iu] * (1 - fu) * (1 - fv) + a[iv, iu + 1] * fu * (1 - fv)
                 + a[iv + 1, iu] * (1 - fu) * fv + a[iv + 1, iu + 1] * fu * fv)


# ------------------------------------------------------------------ 主构建
def build():
    data = {}
    for k in KINDS:
        src = Image.open(BACKUP / ("x_ui_node_%s_off.png" % k)).convert("RGBA")
        assert src.size == SPRITE[k]
        a = np.asarray(src.getchannel("A")).astype(np.float64)
        rect = rect_of(a)
        rad = {}
        for c in ("TL", "TR", "BR", "BL"):
            R, rms, n = radius_corner(a, rect, c)
            rad[c] = {"r": round(R, 3) if R else None, "rms": round(rms, 3) if rms else None,
                      "n": n, "r45": round(corner_diag_radius(a, rect, c) or -1, 3)}
        r_corners = tuple(rad[c]["r"] for c in ("TL", "TR", "BR", "BL"))
        r_mean = float(np.mean([v for v in r_corners if v]))
        band_r = max([v for v in r_corners if v])
        prof, band = collect_profiles(a, rect, band_r)
        data[k] = {"src": src, "alpha0": a, "rect": rect, "rad": rad,
                   "r_corners": r_corners, "r_mean": round(r_mean, 3),
                   "band_r": band_r, "prof": prof, "band": band}
    return data


# ------------------------------------------------------------------ 排版工具
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


def block(draw, xy, lines, font, fill, spacing=3):
    x, y = xy
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += font.size + spacing
    return y


def composite(img, bg, pad):
    W, H = img.size
    out = Image.new("RGB", (W + 2 * pad, H + 2 * pad), bg)
    out.paste(img, (pad, pad), img)
    return out


def now_bg():
    if not SHOT.exists():
        return BG_FALLBACK, "fallback(验收图缺失)"
    a = np.asarray(Image.open(SHOT).convert("RGB")).astype(int)
    x, y = BG_SAMPLE_XY
    blk = a[y:y + 100, x:x + 100]
    if blk.std(axis=(0, 1)).max() > 0.5:
        return BG_FALLBACK, "fallback(取样区不干净)"
    return tuple(int(v) for v in blk.mean(axis=(0, 1)).round()), "验收图 (%d,%d) 100×100 实测" % (x, y)


# ------------------------------------------------------------------ 对比图 ①：四角 + 底边中段（8×）
def sheet_corners(rows, kind, path, bg, meta, extra_note=None):
    """rows = [(标签, 图, 备注行列表), ...]（第一行 = 现状）。"""
    F = MF.font
    crop, zoom = 34, 8
    panel = crop * zoom
    labw, gap, margin, top = 400, 14, 26, 150
    names = (["左上角 TL", "右上角 TR", "左下角 BL", "右下角 BR", "底边中段（缺口处 x=%d）" % NOTCH_X]
             if kind == "select" else
             ["左上角 TL", "右上角 TR", "左下角 BL", "右下角 BR", "底边中段（回归对照）"])

    def crops(rect):
        x0, x1, y0, y1 = rect
        return [(int(round(x0)) - 7, int(round(y0)) - 7),
                (int(round(x1)) + 7 - crop, int(round(y0)) - 7),
                (int(round(x0)) - 7, int(round(y1)) + 7 - crop),
                (int(round(x1)) + 7 - crop, int(round(y1)) + 7 - crop),
                (NOTCH_X - crop // 2, int(round(y1)) + 7 - crop)]

    W = margin * 2 + labw + len(names) * (panel + gap)
    H = top + len(rows) * (panel + 44) + 150 + (60 if extra_note else 0)
    sh = Image.new("RGB", (W, H), (18, 22, 32))
    d = ImageDraw.Draw(sh)
    d.text((margin, margin), "节点轮廓解析化：四角 + 底边中段 8×（%s / %s，叠在真实图表底色 RGB%s 上）"
           % (KIND_CN[kind], kind, str(bg)), font=F(21, True), fill=(238, 243, 250))
    d.text((margin, margin + 30), "列＝四角与底边中段各 8× 最近邻；行＝现状 / 半径不变 / r=12 / r=16 / r=20。"
           "底色 %s" % meta, font=F(14), fill=(158, 172, 190))
    for i, nm in enumerate(names):
        cx = margin + labw + i * (panel + gap)
        d.text((cx + 4, top - 26), nm, font=F(15, True), fill=(255, 214, 140))
    for ri, row in enumerate(rows):
        lab, img, notes = row[0], row[1], row[2]
        comp = composite(img, bg, 16)
        yy = top + ri * (panel + 44)
        block(d, (margin, yy + 10), [lab] + notes, F(14, lab.startswith("现状")),
              (238, 243, 250) if ri == 0 else (222, 232, 244), spacing=3)
        cs = crops(RECT_OF[kind])
        for i, (bx, by) in enumerate(cs):
            tile = comp.crop((bx + 16, by + 16, bx + 16 + crop, by + 16 + crop))
            tile = tile.resize((panel, panel), Image.NEAREST)
            px = margin + labw + i * (panel + gap)
            sh.paste(tile, (px, yy))
            d.rectangle([px - 1, yy - 1, px + panel, yy + panel], outline=(70, 82, 100))
    ty = top + len(rows) * (panel + 44) + 10
    base = ["注 1：候选件的 RGB ＝ 原件 RGB（未改色），对比图统一按现行管线（改色 + select 的 #2A5490 2px 内描边）绘制 ⇒ 只看形状与柔光。",
            "注 2：alpha 由「解析圆角矩形 + 逐边实测径向剖面」生成，尺寸/ nine 摆放不变；遮罩阈值（alpha>=230）不再改。"]
    for ln in base + (extra_note or []):
        d.text((margin, ty), ln, font=F(14), fill=(168, 180, 196) if ln in base else (255, 214, 140))
        ty += 21
    sh.save(path)
    print("  图写出 %s %s" % (path.name, sh.size))


# ------------------------------------------------------------------ 对比图 ②：整节点
def sheet_allnodes(rm, path, bg, meta):
    F = MF.font
    margin, gap, labh, cpad = 26, 14, 26, 8
    cols = [r[0] for r in rm["select"]]
    kinds = [("section", 1), ("select", 1), ("frag", 1), ("select", 2)]
    tiles = []
    for kind, zoom in kinds:
        ims = []
        for row in rm[kind]:
            t = composite(row[1], bg, cpad)
            if zoom != 1:
                t = t.resize((t.width * zoom, t.height * zoom), Image.NEAREST)
            ims.append(t)
        tiles.append((kind, zoom, ims))
    width = margin * 2 + max(sum(t.width for t in ts) + gap * (len(ts) - 1) for _k, _z, ts in tiles)
    heights = [labh + ts[0].height + 26 for _k, _z, ts in tiles]
    H = 132 + sum(heights) + 130
    sh = Image.new("RGB", (int(width), int(H)), (18, 22, 32))
    d = ImageDraw.Draw(sh)
    d.text((margin, margin), "节点轮廓解析化：整节点观感（三类 × 五档，叠在真实图表底色 RGB%s 上）" % str(bg),
           font=F(21, True), fill=(238, 243, 250))
    d.text((margin, margin + 30), "1:1 逐像素（三行）＋ 末行 select ×2 最近邻放大。列＝%s；%s"
           % (" / ".join(cols), meta), font=F(14), fill=(158, 172, 190))
    y = 124
    for kind, zoom, ts in tiles:
        d.text((margin, y), "%s（%s）　%s" % (KIND_CN[kind], kind, "×2 放大" if zoom == 2 else "1:1"),
               font=F(16, True), fill=(255, 214, 140))
        x = margin
        for t, lab in zip(ts, cols):
            sh.paste(t, (x, y + labh))
            d.rectangle([x - 1, y + labh - 1, x + t.width, y + labh + t.height], outline=(70, 82, 100))
            d.text((x + 4, y + labh + t.height + 4), lab, font=F(14, True), fill=(210, 220, 234))
            x += t.width + gap
        y += labh + ts[0].height + 26
    ty = y + 8
    for ln in ["判读：行 1-3 为 1:1（section / select / frag），行 4 为 select ×2。select 列均为「现行改色 + #2A5490 2px 内描边」的生效色；",
               "      section / frag 无描边。半径变大 ⇒ 四角视觉重量变化；「半径不变」用逐角实测半径（section≈8.9 / select≈13.1 / frag≈13.4…15.3）。"]:
        d.text((margin, ty), ln, font=F(14), fill=(255, 214, 140))
        ty += 21
    sh.save(path)
    print("  图写出 %s %s" % (path.name, sh.size))


# ------------------------------------------------------------------ 对比图 ③：柔光剖面
def _axes(d, box, xmax, ymax, label, col=(120, 134, 156)):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], outline=col)
    for i in range(1, 4):
        d.line([x0, y0 + (y1 - y0) * i / 4, x1, y0 + (y1 - y0) * i / 4], fill=(46, 54, 70))
    d.text((x0, y0 - 18), label, font=MF.font(13, True), fill=(210, 220, 234))


def _axes(d, box, xmax, label, ymin=0, ymax=255, xticks=4, ylabel="", tick_label=True):
    x0, y0, x1, y1 = box
    col = (120, 134, 156)
    d.rectangle([x0, y0, x1, y1], outline=col)
    for i in range(1, 4):
        d.line([x0, y0 + (y1 - y0) * i / 4, x1, y0 + (y1 - y0) * i / 4], fill=(46, 54, 70))
        d.text((x0 - 44, y0 + (y1 - y0) * i / 4 - 8),
               "%d" % round(ymax - (ymax - ymin) * i / 4), font=MF.font(11), fill=(140, 154, 174))
    for i in range(1, xticks + 1):
        xx = x0 + (x1 - x0) * i / float(xticks)
        d.line([xx, y0, xx, y1], fill=(46, 54, 70))
        if tick_label:
            d.text((xx - 5, y1 + 2), "%d" % round(xmax * i / float(xticks)),
                   font=MF.font(11), fill=(140, 154, 174))
    d.text((x0, y0 - 20), label, font=MF.font(13, True), fill=(210, 220, 234))
    if ylabel:
        d.text((x0 - 46, y0 - 20), ylabel, font=MF.font(11), fill=(140, 154, 174))


def sheet_profiles(profnum, cand_annulus, orig_annulus, notch, path, bg, meta):
    F = MF.font
    W, H = 1620, 1120
    sh = Image.new("RGB", (W, H), (18, 22, 32))
    d = ImageDraw.Draw(sh)
    d.text((26, 20), "节点柔光剖面：现状 vs 候选（向外 1px 环带均值，0 = 50% 交叉点轮廓）",
           font=F(21, True), fill=(238, 243, 250))
    d.text((26, 50), "四条边分别量测 ⇒ 判断「对称柔光 / 带方向性投影」；候选按「逐边实测剖面表（外正内负）」重做 ⇒ 直边无回归。%s"
           % meta, font=F(14), fill=(158, 172, 190))
    COL = {"L": (120, 190, 255), "T": (255, 214, 140), "R": (140, 230, 170), "B": (255, 140, 140)}
    D = 8
    YMAX = 130
    for pi, kind in enumerate(KINDS):
        px = 70 + pi * 520
        py = 100
        bx = (px, py, px + 440, py + 300)
        _axes(d, bx, D, "%s %s（横＝向外 px，纵＝alpha 0..%d）" % (KIND_CN[kind], kind, YMAX), 0, YMAX)

        def Y(v):
            return bx[3] - (bx[3] - bx[1]) * min(v, YMAX) / float(YMAX)

        def X(i):
            return bx[0] + (bx[2] - bx[0]) * i / float(D)
        for side in CONTOUR_ORDER:
            o, c = orig_annulus[kind][side], cand_annulus[kind][side]
            for i in range(D):
                if o[i] is None or o[i + 1] is None:
                    continue
                d.line([X(i), Y(o[i]), X(i + 1), Y(o[i + 1])], fill=COL[side], width=3)
            for i in range(D):
                if c[i] is None or c[i + 1] is None:
                    continue
                if i % 2 == 0:
                    d.line([X(i), Y(c[i]), X(i + 1), Y(c[i + 1])], fill=(255, 255, 255), width=1)
        yt = bx[3] + 22
        d.text((bx[0], yt), "粗实线＝现状，白虚线＝候选「半径不变」", font=F(12), fill=(168, 180, 196))
        yt += 20
        for side in CONTOUR_ORDER:
            o, c = orig_annulus[kind][side], cand_annulus[kind][side]
            dv = max(abs(oo - cc) for oo, cc in zip(o, c) if oo is not None and cc is not None)
            d.text((bx[0], yt), "%s 现状 %s" % (side, " ".join("%4.0f" % v for v in o[:9] if v is not None)),
                   font=F(12), fill=COL[side])
            d.text((bx[0] + 200, yt), "候选 %s ・偏差≤%.1f"
                   % (" ".join("%4.0f" % v for v in c[:9] if v is not None), dv), font=F(12), fill=(200, 210, 224))
            yt += 17
    # 底边缺口面板（纵轴放大到 218..248 ⇒ 缺口可见）
    bx = (70, 560, 1550, 760)
    lo, hi = 218, 248
    _axes(d, bx, len(notch["x"]) - 1, "select 底边实体行 y=56 的 alpha 沿 x=%d..%d（修前 vs 修后），纵轴放大 %d..%d"
           % (notch["x"][0], notch["x"][-1], lo, hi), lo, hi, xticks=5, tick_label=False)
    for i in range(1, 6):
        xx = bx[0] + (bx[2] - bx[0]) * i / 5.0
        d.text((xx - 12, bx[3] + 14), "x=%d" % notch["x"][int(round((len(notch["x"]) - 1) * i / 5.0))],
               font=F(11), fill=(140, 154, 174))
    ythr = bx[3] - (bx[3] - bx[1]) * (230 - lo) / float(hi - lo)
    d.line([bx[0], ythr, bx[2], ythr], fill=(255, 120, 120), width=1)
    d.text((bx[2] - 90, ythr - 16), "阈值 230", font=F(12), fill=(255, 120, 120))
    for arr, col in ((notch["orig"], (120, 190, 255)), (notch["cand"], (255, 214, 140))):
        pts = []
        for i, v in enumerate(arr):
            X = bx[0] + (bx[2] - bx[0]) * i / float(max(1, len(arr) - 1))
            Y = bx[3] - (bx[3] - bx[1]) * (min(max(v, lo), hi) - lo) / float(hi - lo)
            pts.append((X, Y))
        for i in range(len(pts) - 1):
            d.line([pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]], fill=col, width=2)
        # 逐点小方块，便于看单像素
        for i, (X, Y) in enumerate(pts):
            if i % 2 == 0:
                d.rectangle([X - 2, Y - 2, X + 2, Y + 2], fill=col)
    d.text((bx[0], bx[3] + 8), "列范围 x=%d..%d（蓝＝现状，黄＝候选「半径不变」）；现状在 x=%d 处 alpha=229 < 230 ⇒ 掩码 1px 缺口 ⇒ 描边环带鼓包；"
           "候选该行恒为 %d（无缺口）。" % (notch["x"][0], notch["x"][-1], NOTCH_X, notch["cand_med"]),
           font=F(13), fill=(255, 214, 140))
    ty = 820
    d.text((70, ty), "【四边向外柔光剖面表（1px 环带均值）】  d = 0..12 px", font=F(15, True), fill=(238, 243, 250))
    d.text((760, ty), "候选 = 逐边实测剖面表重建", font=F(13), fill=(168, 180, 196))
    ty += 24
    for kind in KINDS:
        for side in CONTOUR_ORDER:
            o, c = orig_annulus[kind][side], cand_annulus[kind][side]
            dv = max(abs(oo - cc) for oo, cc in zip(o, c) if oo is not None and cc is not None)
            d.text((70, ty), "%-8s %s  现状 %s" % (kind, side, " ".join(
                "  —" if v is None else "%4.0f" % v for v in o)), font=F(12), fill=(200, 210, 224))
            d.text((760, ty), "候选 %s  ・最大偏差 %.1f" % (" ".join(
                "  —" if v is None else "%4.0f" % v for v in c), dv), font=F(12), fill=(255, 214, 140))
            ty += 16
    sh.save(path)
    print("  图写出 %s %s" % (path.name, sh.size))


# ------------------------------------------------------------------ 主流程
rows_master = {}
RECT_OF = {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, meta = now_bg()
    print("底色 RGB%s（%s）" % (str(bg), meta))
    data = build()
    rep = {"params": {"CROSS": CROSS, "SOLID_THR": SOLID, "UNIFORM_R": list(UNIFORM_R),
                      "PROF_RANGE": [PROF_LO, PROF_HI], "stroke": {"color": "#2A5490",
                      "w": MF.STROKE_W, "SS": MF.SS}},
           "bg": list(bg), "bg_src": meta, "kinds": {}}

    # ---------- 几何与剖面表
    print("\n[几何] 实体矩形（50% 交叉点）+ 逐角半径实测")
    for k in KINDS:
        d0 = data[k]
        rep["kinds"][k] = {"sprite": SPRITE[k], "rect": [round(v, 3) for v in d0["rect"]],
                           "corners": d0["rad"], "r_mean": d0["r_mean"], "band_r": d0["band_r"],
                           "band": {"rows": [int(d0["band"]["rows"][0]), int(d0["band"]["rows"][-1])],
                                    "cols": [int(d0["band"]["cols"][0]), int(d0["band"]["cols"][-1])]}}
        print("   %-8s rect=%s 宽=%.3f 高=%.3f ｜ 逐角 %s ｜ 均值 r=%.2f"
              % (k, [round(v, 3) for v in d0["rect"]], d0["rect"][1] - d0["rect"][0],
                 d0["rect"][3] - d0["rect"][2],
                 " ".join("%s=%.2f(45°%.2f)" % (c, d0["rad"][c]["r"], d0["rad"][c]["r45"])
                          for c in ("TL", "TR", "BR", "BL")), d0["r_mean"]))
    print("\n[剖面] 逐边样本（signed t, alpha；直线带 = 去角 %d+2 后的中央区）" % max(
        int(data[k]["band_r"]) for k in KINDS))
    for k in KINDS:
        d0 = data[k]
        for side in CONTOUR_ORDER:
            t, v = d0["prof"][side]
            print("   %-8s %s n=%2d  t=[%+.2f..%+.2f]  " % (k, side, len(t), t[0], t[-1])
                  + " ".join("%+.1f:%.0f" % (tt, vv) for tt, vv in zip(t[:12], v[:12])))

    # ---------- 候选件
    print("\n[候选件]")
    variants = {}
    for k in KINDS:
        d0 = data[k]
        W, H = SPRITE[k]
        fields_cache = {}
        vs = []
        for tag, radii in ([("半径不变", tuple(round(v, 3) for v in d0["r_corners"]))] +
                           [("r=%d" % r, (float(r),) * 4) for r in UNIFORM_R]):
            f = shape_fields(W, H, d0["rect"], radii)
            al = np.rint(np.clip(synth(d0["prof"], f), 0, 255)).astype(np.uint8)
            cand = Image.merge("RGBA", (*d0["src"].convert("RGB").split(), Image.fromarray(al, "L")))
            assert cand.size == SPRITE[k]
            vs.append((tag, radii, cand, f))
        variants[k] = vs
        for tag, radii, cand, _f in vs:
            slug = tag.replace("=", "").replace("半径不变", "r原件")
            fn = "候选_解析轮廓_x_ui_node_%s_off_%s.png" % (k, slug)
            cand.save(OUT / fn)
            names = [fn]
            if k == "select":
                MF.inner_stroke(cand, MF.SPEC[k][3], MF.STROKE_W).save(
                    OUT / ("候选_解析轮廓_x_ui_node_%s_off_%s_描边.png" % (k, slug)))
                eff = MF.recolor(cand, *MF.SPEC[k][:3])
                MF.inner_stroke(eff, MF.SPEC[k][3], MF.STROKE_W).save(
                    OUT / ("候选_解析轮廓_x_ui_node_%s_off_%s_生效色_描边.png" % (k, slug)))
                names += ["候选_解析轮廓_x_ui_node_%s_off_%s_描边.png" % (k, slug),
                          "候选_解析轮廓_x_ui_node_%s_off_%s_生效色_描边.png" % (k, slug)]
            print("   %-8s %-6s %s" % (k, tag, " / ".join(names)))

    # ---------- 指标
    print("\n[指标] 半径复测 / 直边偏差 / 掩码")
    for k in KINDS:
        d0 = data[k]
        a0 = d0["alpha0"]
        ent = rep["kinds"][k]
        ent["rows"] = {}
        for tag, radii, cand, f in variants[k]:
            al = np.asarray(cand.getchannel("A")).astype(np.float64)
            # 半径复测
            rmeas = {}
            for c in ("TL", "TR", "BR", "BL"):
                R, rms, n = radius_corner(al, d0["rect"], c)
                rmeas[c] = {"r": round(R, 3) if R else None, "rms": round(rms, 3) if rms else None,
                            "r45": round(corner_diag_radius(al, d0["rect"], c) or -1, 3)}
            # 直边偏差（去角 rmax+3）
            rmax = int(max(radii) if max(radii) > 0 else 0) + 3
            x0, x1, y0, y1 = d0["rect"]
            X = (np.arange(SPRITE[k][0]) + 0.5)[None, :]
            Y = (np.arange(SPRITE[k][1]) + 0.5)[:, None]
            band = ((X >= x0 + rmax) & (X <= x1 - rmax) & (Y >= y0 - 6) & (Y <= y1 + 6)) | \
                   ((Y >= y0 + rmax) & (Y <= y1 - rmax) & (X >= x0 - 6) & (X <= x1 + 6))
            dev = np.abs(al - a0)[band]
            kat = np.argwhere((np.abs(al - a0) * band) >= dev.max())
            loc = (int(kat[0][1]), int(kat[0][0])) if len(kat) else (-1, -1)
            # 掩码
            mr = {s: mask_report(al, d0["rect"], s) for s in CONTOUR_ORDER}
            mr0 = {s: mask_report(a0, d0["rect"], s) for s in CONTOUR_ORDER}
            nd = int((al != a0).sum())
            ent["rows"][tag] = {
                "radii": [round(v, 3) for v in radii], "r_measured": rmeas,
                "straight_dev_max": round(float(dev.max()), 1), "straight_dev_mean": round(float(dev.mean()), 3),
                "straight_dev_max_xy": loc,
                "straight_n_gt2": int((dev > 2).sum()), "straight_n_gt4": int((dev > 4).sum()),
                "straight_n_gt8": int((dev > 8).sum()), "straight_n_gt16": int((dev > 16).sum()),
                "straight_n": int(dev.size),
                "n_diff_px": nd, "n_diff_gt2": int((np.abs(al - a0) > 2).sum()),
                "n_diff_gt8": int((np.abs(al - a0) > 8).sum()),
                "n_alpha_up": int((al > a0).sum()), "n_alpha_down": int((al < a0).sum()),
                "mask": mr, "mask_orig": mr0,
            }
            print("   %-8s %-6s 半径复测 %s ｜ 直边 |Δ|max=%.1f@%s（>2 %d / >4 %d / >8 %d，共 %d 点）"
                  % (k, tag, " ".join("%s%s" % (c, ("%.2f" % rmeas[c]["r"]) if rmeas[c]["r"] else "—")
                                      for c in ("TL", "TR", "BR", "BL")),
                     dev.max(), loc, int((dev > 2).sum()), int((dev > 4).sum()), int((dev > 8).sum()),
                     dev.size))
            print("            整图改动 %d px（|Δ|>2 %d / >8 %d；升 %d / 降 %d）"
                  % (nd, int((np.abs(al - a0) > 2).sum()), int((np.abs(al - a0) > 8).sum()),
                     int((al > a0).sum()), int((al < a0).sum())))
            if tag == "半径不变":
                print("            掩码首/末实体：现状 " + " ".join(
                    "%s%s" % (s, mr0[s]["uniq"] if len(mr0[s]["uniq"]) < 4 else "[%d..%d]" % (mr0[s]["uniq"][0], mr0[s]["uniq"][-1]))
                    for s in CONTOUR_ORDER) + " ／ 候选 " + " ".join(
                    "%s%s" % (s, mr[s]["uniq"] if len(mr[s]["uniq"]) < 4 else "[%d..%d]" % (mr[s]["uniq"][0], mr[s]["uniq"][-1]))
                    for s in CONTOUR_ORDER))

    # ---------- 底边缺口专项
    print("\n[底边缺口专项] select off：y=56 行 alpha（x=155..180）")
    d0 = data["select"]
    a0 = d0["alpha0"]
    y = 56
    xs = list(range(155, 181))
    o_row = [int(a0[y, x]) for x in xs]
    print("   现状 x=155..180 : " + " ".join("%d" % v for v in o_row))
    notch = {"x": xs, "orig": o_row, "x_notch": NOTCH_X, "orig_at_notch": int(a0[y, NOTCH_X])}
    for tag, radii, cand, f in variants["select"]:
        al = np.asarray(cand.getchannel("A")).astype(np.float64)
        row = [int(al[y, x]) for x in xs]
        hole = [x for x in xs if al[y, x] < SOLID]
        print("   %-6s            : " % tag + " ".join("%d" % v for v in row) + "  掩码缺口=%s" % hole)
        notch.setdefault("cand", {})[tag] = {"row": row, "holes": hole,
                                            "med": int(np.median(al[y, np.arange(int(d0["rect"][0]) + 20, int(d0["rect"][1]) - 19)]))}
    notch["cand_med"] = notch["cand"]["半径不变"]["med"]
    rep["notch"] = notch

    # ---------- 角部旧折线残留 / 平台带
    print("\n[角部残留] 新轮廓之外、距轮廓<=3px 的角区：残留实体像素（alpha>=128 / >=200）与平台带计数")
    for k in KINDS:
        d0 = data[k]
        a0 = d0["alpha0"]
        ent = rep["kinds"][k]
        ent["corner_residual"] = {}
        for tag, radii, cand, f in variants[k]:
            dist, ins, tsig, w, nx, ny = f
            zone = (tsig > 0) & (tsig <= 3.0)
            X = (np.arange(SPRITE[k][0]) + 0.5)[None, :]
            Y = (np.arange(SPRITE[k][1]) + 0.5)[:, None]
            rmax = max(radii)
            corner = (((X < d0["rect"][0] + rmax + 3) | (X > d0["rect"][1] - rmax - 3))
                      & ((Y < d0["rect"][2] + rmax + 3) | (Y > d0["rect"][3] - rmax - 3)))
            z = zone & corner
            vals = np.asarray(cand.getchannel("A")).astype(np.float64)[z]
            vals0 = a0[z]
            plat = int(((vals >= 57) & (vals <= 63)).sum())
            ent["corner_residual"][tag] = {
                "n": int(z.sum()), "max": float(vals.max()) if vals.size else 0.0,
                "n_ge128": int((vals >= 128).sum()), "n_ge200": int((vals >= 200).sum()),
                "plateau_57_63": plat,
                "orig_max": float(vals0.max()) if vals0.size else 0.0,
                "orig_n_ge128": int((vals0 >= 128).sum())}
            print("   %-8s %-6s 角区外侧像素 n=%4d 最大 alpha=%.0f ｜>=128 %3d ｜>=200 %3d ｜[57,63] 平台带 %3d"
                  % (k, tag, int(z.sum()), vals.max() if vals.size else 0,
                     int((vals >= 128).sum()), int((vals >= 200).sum()), plat))
        # 现状（同口径）
        dist, ins, tsig, w, nx, ny = shape_fields(SPRITE[k][0], SPRITE[k][1], d0["rect"],
                                                  tuple(d0["r_corners"]))
        zone = (tsig > 0) & (tsig <= 3.0)
        X = (np.arange(SPRITE[k][0]) + 0.5)[None, :]
        Y = (np.arange(SPRITE[k][1]) + 0.5)[:, None]
        rmax = d0["band_r"]
        corner = (((X < d0["rect"][0] + rmax + 3) | (X > d0["rect"][1] - rmax - 3))
                  & ((Y < d0["rect"][2] + rmax + 3) | (Y > d0["rect"][3] - rmax - 3)))
        z = zone & corner
        vals0 = a0[z]
        print("   %-8s %-6s 角区外侧像素 n=%4d 最大 alpha=%.0f ｜>=128 %3d ｜>=200 %3d ｜[57,63] 平台带 %3d"
              % (k, "现状", int(z.sum()), vals0.max() if vals0.size else 0,
                 int((vals0 >= 128).sum()), int((vals0 >= 200).sum()),
                 int(((vals0 >= 57) & (vals0 <= 63)).sum())))

    # ---------- 描边跟随性
    print("\n[描边] select：沿解析轮廓法线的径向宽度（覆盖率积分，1× px）")
    cur = Image.open(CUR / "x_ui_node_select_off.png").convert("RGBA")
    rect_sel = data["select"]["rect"]          # ★ 显式取 select 的矩形（上面循环已把 d0 改成 frag）
    rep["stroke"] = {}
    for tag, radii, cand, f in variants["select"]:
        st = MF.inner_stroke(cand, MF.SPEC["select"][3], MF.STROKE_W)
        rw = ring_width_radial(st, rect_sel, radii)
        rep["stroke"][tag] = rw
        print("   %-6s 直边 p05/med/p95/max=%s/%s/%s/%s ｜ 圆角弧 %s/%s/%s/%s"
              % (tag, rw["直边"]["p05"], rw["直边"]["med"], rw["直边"]["p95"], rw["直边"]["max"],
                 rw["圆角弧"]["p05"], rw["圆角弧"]["med"], rw["圆角弧"]["p95"], rw["圆角弧"]["max"]))
    rep["stroke"]["现状(正式件)"] = ring_width_radial(cur, rect_sel, tuple(data["select"]["r_corners"]))
    rep["stroke"]["上一轮 r=16（min 削减式）"] = None
    prev = OUT / "候选_x_ui_node_select_off_r16_描边.png"
    if prev.exists():
        rep["stroke"]["上一轮 r=16（min 削减式）"] = ring_width_radial(
            Image.open(prev).convert("RGBA"), rect_sel, (16.0,) * 4)
    for nm in ("现状(正式件)", "上一轮 r=16（min 削减式）"):
        rw = rep["stroke"].get(nm)
        if rw:
            print("   %-22s 直边 p05/med/p95/max=%s/%s/%s/%s ｜ 圆角弧 %s/%s/%s/%s"
                  % (nm, rw["直边"]["p05"], rw["直边"]["med"], rw["直边"]["p95"], rw["直边"]["max"],
                     rw["圆角弧"]["p05"], rw["圆角弧"]["med"], rw["圆角弧"]["p95"], rw["圆角弧"]["max"]))

    # ---------- 底边缺口列的描边宽度（凸起量化）
    print("\n[缺口列描边] select 底边 x=158..176 各列的竖向径向描边宽度（修前 vs 修后）")
    cov_cur = MF.stroke_coverage(cur.getchannel("A"), width=MF.STROKE_W)
    rows = {}
    rows["现状(正式件)"] = ring_width_at(rect_sel, 158, 176, cov_cur)
    for tag, radii, cand, f in variants["select"]:
        st = MF.inner_stroke(cand, MF.SPEC["select"][3], MF.STROKE_W)
        rows[tag] = ring_width_at(rect_sel, 158, 176, MF.stroke_coverage(st.getchannel("A"),
                                                                          width=MF.STROKE_W))
    rep["notch_ring"] = {"x": list(range(158, 177)), "widths": rows}
    for nm, v in rows.items():
        print("   %-10s %s" % (nm, " ".join("%4.2f" % x for x in v)))

    # ---------- on 态可行性（同一 off 几何 + on 剖面表）
    print("\n[on 态可行性] 用 off 的实体矩形与逐角实测半径 + on 的剖面表 ⇒ 预测 on 的轮廓与柔光")
    rep["on_check"] = {}
    for k in KINDS:
        src_on = Image.open(BACKUP / ("x_ui_node_%s_on.png" % k)).convert("RGBA")
        a_on = np.asarray(src_on.getchannel("A")).astype(np.float64)
        rect_on_real = rect_of(a_on)
        d0 = data[k]
        prof_on, _band = collect_profiles(a_on, d0["rect"], d0["band_r"])
        radii = tuple(round(v, 3) for v in d0["r_corners"])
        f = shape_fields(SPRITE[k][0], SPRITE[k][1], d0["rect"], radii)
        al = np.rint(np.clip(synth(prof_on, f), 0, 255)).astype(np.uint8)
        cand = Image.merge("RGBA", (*d0["src"].convert("RGB").split(), Image.fromarray(al, "L")))
        cand.save(OUT / ("附_on态可行验证_候选_解析轮廓_x_ui_node_%s_on_r原件.png" % k))
        rect_pred = rect_of(al.astype(np.float64))
        r_real, r_pred = {}, {}
        for c in ("TL", "TR", "BR", "BL"):
            R1 = radius_corner(a_on, rect_on_real, c)[0]
            R2 = radius_corner(al.astype(np.float64), rect_pred, c)[0]
            r_real[c] = round(R1, 2) if R1 else None
            r_pred[c] = round(R2, 2) if R2 else None
        dev = np.abs(al - a_on)
        rep["on_check"][k] = {"rect_on_real": [round(v, 3) for v in rect_on_real],
                              "rect_pred": [round(v, 3) for v in rect_pred],
                              "rect_dev": [round(rect_pred[i] - rect_on_real[i], 3) for i in range(4)],
                              "r_on_real": r_real, "r_pred": r_pred,
                              "alpha_diff_max": int(dev.max()),
                              "alpha_diff_mean": round(float(dev.mean()), 3),
                              "alpha_diff_gt8": int((dev > 8).sum()),
                              "alpha_n": int(dev.size)}
        print("   %-8s 真实 on rect=%s ｜ 预测 rect=%s ｜ 偏差=%s"
              % (k, [round(v, 2) for v in rect_on_real], [round(v, 2) for v in rect_pred],
                 [round(rect_pred[i] - rect_on_real[i], 2) for i in range(4)]))
        print("            半径（真实 on / 预测，各以自身 rect 为锚，同仪器）：%s ｜ 预测 %s"
              % (" ".join("%s%s" % (c, r_real[c]) for c in ("TL", "TR", "BR", "BL")),
                 " ".join("%s%s" % (c, r_pred[c]) for c in ("TL", "TR", "BR", "BL"))))
        print("            |Δalpha| max=%d mean=%.2f（>8 的 %d / %d px）"
              % (int(dev.max()), dev.mean(), int((dev > 8).sum()), dev.size))

    # ---------- 剖面表（现状 vs 候选 半径不变）
    print("\n[柔光剖面表] 1px 环带均值，向外 d=0..12")
    orig_annulus, cand_annulus = {}, {}
    rep["annulus"] = {"_margin": {}}
    for k in KINDS:
        d0 = data[k]
        cand = [c for (t, r, c, f) in variants[k] if t == "半径不变"][0]
        ac = np.asarray(cand.getchannel("A")).astype(np.float64)
        orig_annulus[k], cand_annulus[k] = {}, {}
        rep["annulus"][k] = {}
        mg = max(12, int(np.ceil(max([v for v in d0["r_corners"] if v]) + 2)))
        for side in CONTOUR_ORDER:
            o = annulus_profile(d0["alpha0"], d0["rect"], side, margin=mg)
            c = annulus_profile(ac, d0["rect"], side, margin=mg)
            orig_annulus[k][side], cand_annulus[k][side] = o, c
            dv = max(abs(oo - cc) for oo, cc in zip(o, c) if oo is not None and cc is not None)
            rep["annulus"][k][side] = {"orig": o, "cand": c, "max_dev": round(dv, 2)}
            fmt = lambda arr: " ".join("   —" if v is None else "%5.1f" % v for v in arr)
            print("   %-8s %s 现状 %s" % (k, side, fmt(o)))
            print("   %-8s %s 候选 %s ｜ 最大偏差 %.2f ｜ 带 margin=%d" % (k, side, fmt(c), dv, mg))
        rep["annulus"]["_margin"][k] = mg

    # ---------- 与主代理「给定式 max(cov*255, glow)」的对照（量化其直边代价）
    print("\n[对照] 给定式 max(cov*255, glow)（glow 取实测向外剖面）——直边代价量化")
    rep["formula_vs_profile"] = {}
    for k in KINDS:
        d0 = data[k]
        a0 = d0["alpha0"]
        radii = (16.0,) * 4
        dist, ins, tsig, w, nx, ny = shape_fields(SPRITE[k][0], SPRITE[k][1], d0["rect"], radii)
        cov = np.clip(0.5 - tsig, 0.0, 1.0)                     # box 覆盖度（直线段上精确）
        glow = np.zeros_like(tsig)
        for s in CONTOUR_ORDER:
            t, v = d0["prof"][s]
            glow = np.maximum(glow, w[s] * np.interp(np.maximum(tsig, 0.0), t, v))
        al_f = np.rint(np.clip(np.maximum(cov * 255.0, glow), 0, 255)).astype(np.uint8)
        rmax = 19
        X = (np.arange(SPRITE[k][0]) + 0.5)[None, :]
        Y = (np.arange(SPRITE[k][1]) + 0.5)[:, None]
        x0, x1, y0, y1 = d0["rect"]
        band = ((X >= x0 + rmax) & (X <= x1 - rmax) & (Y >= y0 - 6) & (Y <= y1 + 6)) | \
               ((Y >= y0 + rmax) & (Y <= y1 - rmax) & (X >= x0 - 6) & (X <= x1 + 6))
        dev = np.abs(al_f.astype(float) - a0)[band]
        rows = {}
        for tag, radii2, cand, f in variants[k]:
            rows[tag] = rep["kinds"][k]["rows"][tag]["straight_dev_max"]
        rep["formula_vs_profile"][k] = {
            "formula_straight_dev_max": round(float(dev.max()), 1),
            "formula_straight_dev_mean": round(float(dev.mean()), 3),
            "formula_n_gt8": int((dev > 8).sum()), "straight_n": int(dev.size),
            "profile_straight_dev_max": rows.get("r=16")}
        print("   %-8s 给定式直边 |Δ|max=%.1f（>8 %d / %d 点）｜ 剖面表式 |Δ|max=%.1f"
              % (k, dev.max(), int((dev > 8).sum()), dev.size, rows.get("r=16")))
        if k == "select":
            yb = 55
            print("            给定式 y=56 行 x=160..172 = %s" % " ".join("%3d" % al_f[56, x] for x in range(160, 173)))
            print("            原件   同 行            = %s" % " ".join("%3d" % a0[56, x] for x in range(160, 173)))
            print("            给定式 y=57 行 x=160..172 = %s" % " ".join("%3d" % al_f[57, x] for x in range(160, 173)))
            print("            原件   同 行            = %s" % " ".join("%3d" % a0[57, x] for x in range(160, 173)))

    for k in KINDS:
        RECT_OF[k] = data[k]["rect"]
    for k in KINDS:
        vs = variants[k]
        cur = Image.open(CUR / ("x_ui_node_%s_off.png" % k)).convert("RGBA")
        rows = [("现状（正式件：原件 alpha + 现行管线）", cur, [], k)]
        for tag, radii, cand, f in vs:
            if k == "select":
                img = MF.inner_stroke(MF.recolor(cand, *MF.SPEC[k][:3]), MF.SPEC[k][3], MF.STROKE_W)
            else:
                img = MF.recolor(cand, *MF.SPEC[k][:3])
            al = np.asarray(cand.getchannel("A")).astype(np.float64)
            nd = int((al != data[k]["alpha0"]).sum())
            rmeas = rep["kinds"][k]["rows"][tag]["r_measured"]
            notes = ["逐角实测半径 %s ｜ 改动 %d px"
                     % (" ".join("%s%.1f" % (c, rmeas[c]["r"]) for c in ("TL", "TR", "BR", "BL")), nd),
                     "直边 |Δ|max %.1f ｜ 底边 y=56 掩码缺口 %s"
                     % (rep["kinds"][k]["rows"][tag]["straight_dev_max"],
                        rep["kinds"]["select"]["rows"][tag]["mask"]["B"]["uniq"]
                        if k == "select" else "—")]
            rows.append((tag, img, notes, k))
        rows_master[k] = [(r[0], r[1], r[2], r[3]) for r in rows]
        path = OUT / ("对比_轮廓解析化_四档.png" if k == "select"
                      else "对比_轮廓解析化_四档_%s.png" % k)
        sheet_corners(rows, k, path, bg, meta)
    sheet_allnodes(rows_master, OUT / "对比_轮廓解析化_全节点.png", bg, meta)
    notch_plot = {"x": notch["x"], "orig": notch["orig"],
                  "cand": notch["cand"]["半径不变"]["row"], "cand_med": notch["cand_med"]}
    sheet_profiles(None, cand_annulus, orig_annulus, notch_plot, OUT / "对比_柔光剖面.png", bg, meta)

    txt = OUT / "轮廓解析化_数字证据.json"
    with open(txt, "w", encoding="utf-8") as f:
        f.write(json.dumps(rep, ensure_ascii=False, indent=2))
    print("  数字证据写出 %s" % txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
