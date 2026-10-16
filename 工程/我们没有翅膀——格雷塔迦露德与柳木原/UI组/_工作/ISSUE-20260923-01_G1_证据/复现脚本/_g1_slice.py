# -*- coding: utf-8 -*-
r"""G1c · 快捷条 12 圆图标 · 结构驱动切件 + 圆几何归一化 → **64x64 / 圆径 56 / 加粗描边 / 保留柔光**

■ 规格（主代理 2026-09-23 最终裁定，替换 G1 的 56x56/圆径48）
  · 画布 **64x64** PNG-32 真 alpha；圆底**圆径 56**；圆心 **(31.5, 31.5)**；同项两态一致。
  · **保留圆外柔光**，且**在画布内侧自然衰减为 0**：`r >= 31.5` 一律 alpha=0（不在边缘硬切）。
  · **描边加粗提饱和**：青蓝细边 → **约 2px** 且更饱和，与 `x_ui_menuicon_*.png` 同族。

■ 描边参数怎么定的（`_g1c_rimcal.py` 实测同族素材）
  `x_ui_menuicon_start.png`（96 画布、圆径 82、R=41）圆缘剖面：
      r=39.5 色(162,206,246) B−R= 84
      r=40.5 色(133,203,246) B−R=112   ← 描边峰值
      r=41.5 色(154,220,250) B−R= 96
      r=42.5 色(154,218,248) B−R= 93   ← 外晕
  ⇒ 同族描边 = **约 2px 宽**、峰值色 **(133,203,246)**（`#85CBF6`）、蓝度 B−R≈113，
    峰值位置 r/R≈0.99；圆内（r/R≈0.94）B−R 仅 36 ⇒ 描边是「一圈明显更蓝的环」。

■ 归一化算法（逐步可复算）
  1. 裁剪 + LANCZOS，使圆底（alpha>=210 包围盒）**严格映射为圆径 56**、圆心 (31.5,31.5)。
     ⇒ 圆底外缘 **R_EDGE = 28.0**，画布内给柔光留 3.5px。
  2. 量**径向均值 alpha 剖面** `p(r)`，r ∈ [28.0, 31.5]，步长 0.25px。
  3. 造**非增包络** `ENV(r) = min( cummin(p), T(r) )`：
       · `cummin(p)` = 由内向外的累积最小 ⇒ 非增（压平「邻居圆渗入」造成的反弹：
         源图第 1/2 行的圆，其向下的柔光在 r/R≈1.19 撞到下一行的圆，alpha 由 85 反弹到 234）；
       · `T(r)` = 从 `p(28)` 用余弦缓动**恰在 r=31.5 降到 0** ⇒ 非增且端点归零；
       · 两个非增函数取 min ⇒ ENV **非增**、`ENV(31.5)=0`、**无台阶**。
     ⇒ 等价于「保留源柔光并把它被邻居截断的尾巴平滑补到画布内侧」。
  4. 合成 alpha/RGB（`w` = smoothstep，仅在 28.0→30.0 由 0 升到 1）：
       alpha = (1-w)·src_alpha + w·ENV(r)      （r<=28 时 w=0 ⇒ 圆底与图标**逐像素原样不动**）
       rgb   = (1-w)·src_rgb   + w·halo_rgb(r) （halo_rgb = 该半径的实测柔光色）
     ⇒ 圆底外缘真实软边保留，再往外逐渐成为**径向对称柔光** ⇒ **沿任意半径 alpha 都单调**。
  5. **加粗描边**：在源图自己的圆缘内侧采样描边色，**提饱和 ×1.75**，以 **2.4px 宽**的
     平滑环**over 合成**；环带外沿**恰好落在 R_EDGE=28.0**，故完全落在圆内、不影响柔光区。
  6. `r >= 31.5` 强制 alpha=0；随后 alpha==0 处 RGB 一并清零（否则「全透明」不干净）。
"""
import json, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
_G = HERE
for _ in range(6):
    if os.path.isdir(os.path.join(_G, "krkr")) and os.path.isdir(os.path.join(_G, "layout")):
        break
    _G = os.path.dirname(_G)
UI = os.path.join(_G, "krkr", "assets", "ui")
RAW = os.path.join(EV, "原始大图")
CUT = os.path.join(EV, "切件_64")
os.makedirs(CUT, exist_ok=True)

KEYS = ["lock", "save", "load", "qsave", "qload", "auto",
        "skip", "next", "prev", "log", "chart", "option"]

CANVAS = 64
CX = CY = 31.5
D_BALL = 56.0                    # 圆底圆径（主代理最终规格）
R_EDGE = D_BALL / 2.0            # 28.0 —— 圆底外缘
R_CROSS1 = R_EDGE + 2.0          # 30.0 —— 到此处已完全转为径向对称柔光
R_HALO = 31.5                    # 柔光外缘：r>=31.5 一律 alpha=0（画布内侧）
THR_BALL = 210
MIN_BAND = 60
THRS = [210, 180, 150, 120]
STEP = 0.25

# ── 描边 / 配色（G1e · 按 vision「拿参照截图重判」后的四条目标重定）────────────────
#
# 参照（两款同属 Applique，同一套设计）实测：常态圆 = **中性银白**（圆底 luma 194、B−R≈4）、
#   **深中性灰环** luma 106、**窄而强的纯白外晕**；圆底/环明度差 **88**；悬停 = 饱和青、底明度 −27%。
# G1d 诊断（vision 判定实验）：底近白 ⇒ 冰蓝屏底上圆底彻底消失（1.048）；
#   但「继续压深圆底」也不是要害 —— 明度已与参照持平（199.6 vs 194），**偏的是彩度**（B−R 64 vs 4）。
#
# ★ luma 口径 = **Rec.601**：`L = 0.299R + 0.587G + 0.114B`
#   （用 G1d 的 #B4C9F4 复现出 vision 报的 199.6、用 #5A9BE6 复现出 144.1，二值完全吻合 ⇒ 口径确认。）
#
# 四条目标 → 取值（色相一律留在**我方冰蓝族**；偏离参照的那一维是刻意的）：
#   1【最高】外光晕 → **白/近白**（原淡蓝 (144,187,239) 合成到冰蓝屏底后偏暗 ⇒ 被读作脏边）；
#                    收紧到环外缘外约 2.5px 归零（原 3.5px），同样不透明度集中到更窄带 ⇒ 紧而亮。
#   2【高】  环     → luma 118（原 144.1）⇒ 环/底明度差 200−118 = **82 ≥75**（参照 88）
#   3【中】  圆底   → **去彩度 B−R 20 ≤25**（霜白冷灰 #C1C9D5），luma 200（保持 195–205，不更亮不更暗）
#   4【中】  两态步长 → 悬停底 luma 162 = 常态 **−19%**；环同步加深（118→87，环/底差仍 75）
def solve_rgb(L, D, E):
    """由 Rec.601 luma L、B−R=D、G−R=E 反解 RGB（「向目标色相/色度映射」用）。
    推导：0.299R+0.587(R+E)+0.114(R+D) = L ⇒ R = L − 0.587E − 0.114D。"""
    R = L - 0.587 * E - 0.114 * D
    return (R, R + E, R + D)


CONF = {
    "off": {"fill_L": 200.0, "fill_D": 20.0, "fill_E": 8.0,      # → #C1C9D5 霜白冷灰
            "rim_L": 118.0, "rim_D": 117.0, "rim_E": 50.0,       # → #4B7DC0 冰蓝族深环
            "rim_a": 255.0, "rim_hw": 1.15},                     # 实测环宽 1.75px
    "on": {"fill_L": 158.5, "fill_D": 75.0, "fill_E": 30.0,      # → 实测落 ~163 ⇒ 常态 −18.6%
           "rim_L": 87.0, "rim_D": 117.0, "rim_E": 50.0,         # → #2A5C9F 环同步加深
           "rim_a": 255.0, "rim_hw": 1.40},                      # 实测环宽 2.25px（环「加重」）
}
HALO_IN = (255, 255, 255)        # B1：白晕用**纯白**（对齐参照实测的 (255,255,255)）
HALO_OUT = (255, 255, 255)
RIM_PLATEAU = 0.5                # 环峰区平台半宽（占比）

# ── 统一 alpha 剪影曲线（★ 两态共用；状态差异只走「颜色/材质」）─────────────────
# 必须统一的理由：各态沿用自家源柔光的 alpha 会让 alpha>=128 等值线落在 off≈28.4 / on≈28.9，
# 量化后 d128 = 56 vs 58（两态差 2px，违反「≤1px」）；统一后 alpha 场逐像素相同 ⇒ Δ=0、悬停不跳。
# G1e 把 128 交叉点仍钉在 r=R_EDGE=28.0（⇒ d128=56 不变），但**收紧尾部**：
# 0 落在 r=30.6（环外缘约 R_EDGE 之外 2.5px），取代 G1d 的 31.5。
# ── B1（主代理终态精修）：白晕做成参照那样的「**1px 近实白 + 1px 渐隐**」──────────
# vision 实测参照白晕 = 2px 满不透明纯白 (255,255,255)；我们上版峰值仅 α120 ⇒ 读作"柔和复刻"。
# 新曲线：环外缘 r=28.0 起 **0.9px 保 α≥200（近实白）**，再 ~1px 渐隐到 0（r=29.85 归零，远在画布内）。
# ★ 主代理已放开「d128=56」这个自设比较量（非项目契约）：白晕会让 alpha≥128 等值线外扩到 r≈29.15
#   ⇒ d128 ≈ 58。**真契约是「两态 alpha 场一致 ⇒ 悬停不跳动」**，见报告的两态剪影差自证。
CURVE_R = np.array([26.00, 27.00, 27.50, 28.00, 28.90, 29.15, 29.50, 29.85, 30.40])
CURVE_A = np.array([255.0, 255.0, 246.0, 205.0, 200.0, 128.0, 62.0, 0.0, 0.0])
CURVE_W0 = R_EDGE - 2.0          # 26.0 —— 源 alpha 完全保留到此
CURVE_W1 = R_EDGE - 0.5          # 27.5 —— 到此处已完全由曲线接管

_YY, _XX = np.mgrid[0:CANVAS, 0:CANVAS]
# 画布几何中心（边坐标）= CANVAS/2 ⇒ 64 画布为 32.0（介于像素 31 与 32 之间）。
# 像素 i 的采样位置 = i+0.5 ⇒ 必须保留这个 +0.5，否则圆心会整体偏 0.5px（G1 的旧写法就偏了）。
CTR = CANVAS / 2.0
RGRID = np.sqrt((_XX + 0.5 - CTR) ** 2 + (_YY + 0.5 - CTR) ** 2)
RS = np.arange(R_EDGE, R_HALO + STEP, STEP)


def runs(mask, mind):
    out, s = [], None
    for i, v in enumerate(mask):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if i - s >= mind:
                out.append((s, i - 1))
            s = None
    if s is not None and len(mask) - s >= mind:
        out.append((s, len(mask) - 1))
    return out


def bbox_of(m):
    ys, xs = np.nonzero(m)
    return None if len(ys) == 0 else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def circularity(m, bb):
    x0, y0, x1, y1 = bb
    area = float(m[y0:y1 + 1, x0:x1 + 1].sum())
    r = max(x1 - x0 + 1, y1 - y0 + 1) / 2.0
    return area / (np.pi * r * r)


def analyze(path):
    """结构驱动找 4 列 × 3 行；每格给**两套圆底几何**：
      · thr 高（210，用于干净分带）→ 圆心/圆径，用于定位；
      · thr=128（与验收口径一致）→ 圆心/圆径，**用于定标度**。
    """
    rgba = Image.open(path).convert("RGBA")
    al = np.array(rgba)[..., 3]
    diag = ["  %s  %s" % (os.path.basename(path), rgba.size)]
    for thr in THRS:
        m = al >= thr
        cb = runs(m.sum(axis=0) > 0, MIN_BAND)
        rb = runs(m.sum(axis=1) > 0, MIN_BAND)
        if len(cb) == 4 and len(rb) == 3:
            m128 = al >= 128
            cells, circs, bad = {}, [], False
            for ri, (y0, y1) in enumerate(rb):
                for ci, (x0, x1) in enumerate(cb):
                    sub = np.zeros_like(m)
                    sub[y0:y1 + 1, x0:x1 + 1] = m[y0:y1 + 1, x0:x1 + 1]
                    bb = bbox_of(sub)
                    sub2 = np.zeros_like(m128)
                    sub2[y0:y1 + 1, x0:x1 + 1] = m128[y0:y1 + 1, x0:x1 + 1]
                    bb2 = bbox_of(sub2)
                    if bb is None or bb2 is None:
                        diag.append("  x thr%d 格(%d,%d) 空" % (thr, ri, ci))
                        bad = True
                        break
                    d = float(max(bb[2] - bb[0] + 1, bb[3] - bb[1] + 1))
                    d2 = float(max(bb2[2] - bb2[0] + 1, bb2[3] - bb2[1] + 1))
                    cells[(ri, ci)] = {
                        "c210": ((bb[0] + bb[2] + 1) / 2.0, (bb[1] + bb[3] + 1) / 2.0, d),
                        "c128": ((bb2[0] + bb2[2] + 1) / 2.0, (bb2[1] + bb2[3] + 1) / 2.0, d2),
                        "circ": circularity(m, bb)}
                    circs.append(cells[(ri, ci)]["circ"])
                if bad:
                    break
            if bad:
                continue
            diag.append("  OK thr%d ｜ 列带 4 %s ｜ 行带 3 %s" % (thr, cb, rb))
            diag.append("     圆度 mean=%.3f min=%.3f ｜ 圆径(210) %.0f~%.0f ｜ 圆径(128) %.0f~%.0f"
                        % (float(np.mean(circs)), float(np.min(circs)),
                           min(c["c210"][2] for c in cells.values()),
                           max(c["c210"][2] for c in cells.values()),
                           min(c["c128"][2] for c in cells.values()),
                           max(c["c128"][2] for c in cells.values())))
            return rgba, thr, cells, float(np.min(circs)), diag
        diag.append("     thr%-4d 列带 %d 行带 %d → 不合格" % (thr, len(cb), len(rb)))
    return rgba, None, None, -1.0, diag


def _luma601(rgb):
    """Rec.601 luma：0.299R + 0.587G + 0.114B（vision 报数用的就是这个口径）。"""
    a = np.asarray(rgb, dtype=np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def _fill_mask(rgba_arr):
    """圆底**填充**掩码：r<=26 且 alpha>200 且亮度>=150（=排除深蓝图形象与环）。"""
    return ((RGRID <= CURVE_W0) & (rgba_arr[..., 3] > 200)
            & (rgba_arr[..., :3].mean(axis=-1) >= 150.0))


def _fill_mean(rgba_arr):
    m = _fill_mask(rgba_arr)
    if m.sum() < 30:
        return np.array([230.0, 240.0, 251.0])
    return rgba_arr[..., :3][m].mean(axis=0)


def _fill_luma(rgba_arr):
    m = _fill_mask(rgba_arr)
    if m.sum() < 30:
        return 232.0
    return float(rgba_arr[..., :3][m].mean())


def _measure_rim_luma(rgba_arr):
    """环峰值亮度：r∈[R_EDGE-5, R_EDGE+0.1] 内按 0.25px 取各半径均值，再取**最暗**那个半径的 luma。"""
    al, px = rgba_arr[..., 3], rgba_arr[..., :3]
    best = None
    for r in np.arange(R_EDGE - 5.0, R_EDGE + 0.11, 0.25):
        m = (RGRID >= r - 0.125) & (RGRID < r + 0.125) & (al > 200)
        if m.sum() < 6:
            continue
        l = float(_luma601(px[m].mean(axis=0)))
        if best is None or l < best:
            best = l
    return 118.0 if best is None else best


def rim_geometry(state):
    """环带 alpha 剖面（分态：常态偏淡、悬停实心，且悬停略宽）。"""
    r0, hw = R_EDGE - 1.2, CONF[state]["rim_hw"]
    dr = np.abs(RGRID - r0)
    k = np.clip((hw - dr) / (hw * (1.0 - RIM_PLATEAU)), 0.0, 1.0)
    off = dr <= hw * RIM_PLATEAU
    prof = k * k * (3.0 - 2.0 * k)
    prof[off] = 1.0
    return prof * (CONF[state]["rim_a"] / 255.0)


def crop_center(rgba, cx, cy, side):
    """按给定窗口边长裁切并缩到 CANVAS；**圆心精确落在画布几何中心**。

    ★ G1 的旧写法 `int(round(cx-side/2))` 会把圆心整体偏 0.5px（裁切窗口取整 + resize
      隐含的像素中心约定）；这里改为**浮点窗口 + 裁切后按实测圆心做整数重定位**，
      实测圆心与 (CTR,CTR) 的残差 <=0.5px 且**对所有 24 件一致**。
    """
    x0 = cx - side / 2.0
    y0 = cy - side / 2.0
    box = (int(np.floor(x0)), int(np.floor(y0)),
           int(np.ceil(x0 + side)), int(np.ceil(y0 + side)))
    crop = rgba.crop(box).resize((CANVAS, CANVAS), Image.LANCZOS)
    a = np.array(crop)[..., 3]
    bb = bbox_of(a >= 128)
    if bb is None:
        return crop
    mx = (bb[0] + bb[2] + 1) / 2.0          # 实测圆心（索引度量，等价边坐标）
    my = (bb[1] + bb[3] + 1) / 2.0
    dx, dy = int(round(CTR - mx)), int(round(CTR - my))
    if dx or dy:
        sh = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        sh.paste(crop, (dx, dy))
        crop = sh
    return crop


def _render(rgba, cx, cy, side, state, want_rim=True):
    """渲染一件：圆底/图标逐像素取自源图 → 圆底填充**配色重定** → 统一剪影 → 环 → 柔光。

    · alpha：r<=26.0 源样；26.0→27.5 平滑过渡到**两态共用的统一剪影曲线**；r>=27.5 纯曲线。
    · RGB（本版 = 主代理 vision 裁定后的新配色，全部落在锚点冰蓝族）：
        - 圆底填充：整体平移命中 CONF[state]['fill']（深蓝图形象按亮度加权保护、保持原样）
        - 环      ：固定目标色 CONF[state]['rim']（常态偏淡 alpha=170 / 悬停实心 alpha=255）
        - 柔光    ：由环色向族内更淡色作径向插值 CONF[state]['halo'] → HALO_OUTER
    """
    crop = crop_center(rgba, cx, cy, side)
    src = np.array(crop).astype(np.float64)
    c = CONF[state]

    w = np.clip((RGRID - CURVE_W0) / (CURVE_W1 - CURVE_W0), 0.0, 1.0)
    w = w * w * (3.0 - 2.0 * w)
    cv = np.interp(RGRID, CURVE_R, CURVE_A, left=CURVE_A[0], right=0.0)

    out = src.copy()
    out[..., 3] = (1.0 - w) * src[..., 3] + w * cv
    # 圆底实心区 alpha 统一抬到 255（源底实际 alpha≈252，会让单调性在 r≈26 冒 +3 抖动）
    core = (RGRID <= R_EDGE - 1.5) & (src[..., 3] > 128)
    out[..., 3][core] = 255.0

    # ── 圆底填充：**亮度传递式重着色**（源图只贡献亮度纹理；色相/彩度由目标色决定）──
    # `out = TARGET × (L / L_ref)` 是**标量**缩放 ⇒ 填充像素色相/彩度 = 目标，源图左上斜向
    # 磨砂高光与明暗结构仍在。★ 不能用「按通道常量平移」：那只改亮度不改色相，源图圆底外圈
    # 那圈饱和青会透出、把环拉宽并重新逼近霓虹（G1d 踩过）。
    # 深蓝图形象按 Rec.601 luma 加权保护（L<=120 原样；L>=160 整像素重着色）。
    L601 = _luma601(src[..., :3])
    wf = np.clip((L601 - 120.0) / 40.0, 0.0, 1.0)
    wf = wf * wf * (3.0 - 2.0 * wf) * (RGRID <= CURVE_W0)
    fill_rgb = np.array(solve_rgb(c["fill_L"], c["fill_D"], c["fill_E"]), dtype=np.float64)
    rim_rgb = np.array(solve_rgb(c["rim_L"], c["rim_D"], c["rim_E"]), dtype=np.float64)
    gray = src[..., :3].sum(axis=-1) / 3.0                  # 迭代时用灰度估目标缩放
    tgt_f, tgt_r = fill_rgb.copy(), rim_rgb.copy()
    for _ in range(10):                                     # 联合迭代：命中实测 环/底 双 luma
        lref = _fill_luma(src)
        recol = np.clip(gray[..., None] / max(lref, 1.0) * tgt_f, 0, 255)
        for ch in range(3):
            out[..., ch] = src[..., ch] * (1.0 - wf) + recol[..., ch] * wf

        # ── 外光晕：白/近白（由内缘冷调插值到外缘纯白）──
        u = np.clip((RGRID - R_EDGE) / (29.85 - R_EDGE), 0.0, 1.0)
        for ch in range(3):
            hc = HALO_IN[ch] + (HALO_OUT[ch] - HALO_IN[ch]) * u
            out[..., ch] = (1.0 - w) * out[..., ch] + w * hc

        # ── 环（固定目标色 + 分态宽度，over 合成）──
        ra = rim_geometry(state)
        for ch in range(3):
            out[..., ch] = tgt_r[ch] * ra + out[..., ch] * (1.0 - ra)
        out[..., 3] = ra * 255.0 + out[..., 3] * (1.0 - ra)

        e_f = c["fill_L"] - _luma601(_fill_mean(out))
        e_r = c["rim_L"] - _measure_rim_luma(out)
        if max(abs(e_f), abs(e_r)) < 0.4:
            break
        # 只调 luma、保住目标的 B−R / G−R（重新反解 RGB），避免越迭代越偏色
        kf = (c["fill_L"] + e_f) / max(c["fill_L"], 1e-6)
        tgt_f = np.array(solve_rgb(c["fill_L"] * kf, c["fill_D"], c["fill_E"]))
        tgt_r = np.array(solve_rgb(c["rim_L"] + e_r, c["rim_D"], c["rim_E"]))
    c_rim, c_rim_b = tuple(tgt_r), tuple(rim_rgb)

    out[RGRID >= R_HALO] = 0.0
    out = np.round(np.clip(out, 0, 255)).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return Image.fromarray(out, "RGBA"), c_rim, c_rim_b


def normalize(rgba, cx, cy, d128_src, state, want_debug=False):
    """标度：把源图 **alpha>=128 的圆底圆径**映射为 D_BALL（与验收口径一致）。

    统一剪影已在 `_render` 内生效 ⇒ 输出的 d128 由曲线在 r=R_EDGE 处恰为 128 保证，
    **两态完全一致**；无需回代迭代（实测 24 件全部 d128=56）。
    """
    side = d128_src * CANVAS / D_BALL
    piece, c_rim, c_rim_b = _render(rgba, cx, cy, side, state)
    if want_debug:
        return piece, {"rim_src": c_rim, "rim_new": c_rim_b, "side": side}
    return piece


# ─────────────────────────── 验收复测 ───────────────────────────

def radial_mean_alpha(piece, r, half=0.5):
    a = np.array(piece)[..., 3].astype(float)
    m = (RGRID >= r - half) & (RGRID < r + half)
    return float(a[m].mean()) if m.sum() else 0.0


def monotone_check(piece):
    """自 R_EDGE 到 R_HALO 按 0.25px 采样径向均值 alpha，统计「增」>2 的处数。"""
    prof = np.array([radial_mean_alpha(piece, r, STEP / 2) for r in RS])
    bad = [(round(float(RS[i + 1]), 2), round(float(prof[i]), 1), round(float(prof[i + 1]), 1))
           for i in range(len(prof) - 1) if prof[i + 1] - prof[i] > 2.0]
    return prof, bad


def rim_stats(piece):
    """描边实测：在 r∈[R_EDGE-5, R_EDGE] 内按 0.25px 求**各半径的均值蓝度 B-R**，
    取峰值半径、峰值色、以及「蓝度 > 60% 峰值」的**径向宽度**（px）。"""
    a = np.array(piece).astype(float)
    al, px = a[..., 3], a[..., :3]
    rr = np.arange(R_EDGE - 5.0, R_EDGE + 0.26, 0.25)
    prof, cols = [], []
    for r in rr:
        m = (RGRID >= r - 0.125) & (RGRID < r + 0.125) & (al > 200)
        if m.sum() < 6:
            prof.append(-1e9); cols.append((0, 0, 0)); continue
        prof.append(float((px[..., 2][m] - px[..., 0][m]).mean()))
        cols.append(tuple(px[m].mean(axis=0)))
    prof = np.asarray(prof)
    j = int(np.argmax(prof))
    peak_r, peak_br = float(rr[j]), float(prof[j])
    peak_rgb = tuple(round(float(v)) for v in cols[j])
    inside = [i for i in range(len(rr)) if prof[i] >= peak_br * 0.6 and abs(rr[i] - peak_r) <= 3]
    width = (max(rr[i] for i in inside) - min(rr[i] for i in inside) + 0.25) if inside else 0.0
    return {"peak_r": peak_r, "peak_rgb": peak_rgb, "peak_br": peak_br,
            "width_px": round(float(width), 2), "profile": [round(float(v), 1) for v in prof],
            "profile_r": [round(float(v), 2) for v in rr]}


def measured(piece):
    a = np.array(piece)[..., 3]
    bb = bbox_of(a >= 128)
    nz = np.nonzero(a > 0)
    c = ((bb[0] + bb[2] + 1) / 2.0, (bb[1] + bb[3] + 1) / 2.0)
    return {"center": c,
            "off_from_ctr": (round(c[0] - CTR, 2), round(c[1] - CTR, 2)),
            "d128": float(max(bb[2] - bb[0] + 1, bb[3] - bb[1] + 1)),
            "alpha0": float((a == 0).mean()),
            "halo_r": float(RGRID[nz].max()) if len(nz[0]) else 0.0,
            "ge315_nonzero": int((a[RGRID >= R_HALO] != 0).sum()),
            "rgb_at_alpha0": int((np.array(piece)[..., :3][a == 0].max(axis=-1) != 0).sum())}


def main():
    chosen = {}
    for st, vers in (("off", (1, 2)), ("on", (1, 2))):
        best = None
        for v in vers:
            p = os.path.join(RAW, "sheet_%s_v%d.png" % (st, v))
            if not os.path.exists(p):
                continue
            rgba, thr, cells, q, diag = analyze(p)
            print("=" * 78)
            print("态 %s · v%d  （圆度下限 %.3f）" % (st, v, q))
            for dd in diag:
                print(dd)
            if cells is not None and (best is None or q > best[3]):
                best = (p, rgba, cells, q, thr, v)
                print("    → 暂选 v%d" % v)
        if best:
            chosen[st] = best

    # ── 统一 alpha 剪影曲线（常量，两态共用；见文件头 §统一剪影）──
    print("【统一 alpha 剪影曲线（两态共用）】r=%s\n                                 alpha=%s"
          % (list(CURVE_R), list(CURVE_A)))

    geo = {}
    for st in ("off", "on"):
        if st not in chosen:
            print("!! 态 %s 无可切候选" % st)
            continue
        p, rgba, cells, q, thr, v = chosen[st]
        for i, key in enumerate(KEYS):
            r, c = divmod(i, 4)
            cell = cells[(r, c)]
            cx, cy, d128 = cell["c128"]          # 用 thr=128 的圆底几何定标度
            piece, dbg = normalize(rgba, cx, cy, d128, st, want_debug=True)
            sfx = "" if st == "off" else "_on"
            piece.save(os.path.join(CUT, "x_ui_qbicon_%s%s.png" % (key, sfx)))
            ms = measured(piece)
            prof, bad = monotone_check(piece)
            rs = rim_stats(piece)
            geo["%s_%s" % (st, key)] = {
                "state": st, "version": v, "thr": thr, "key": key,
                "src_center128": [round(cx, 2), round(cy, 2)], "src_d128": round(d128, 2),
                "src_d210": round(cell["c210"][2], 2),
                "out_center": [round(ms["center"][0], 2), round(ms["center"][1], 2)],
                "out_center_off": list(ms["off_from_ctr"]),
                "out_d128": round(ms["d128"], 2), "alpha0": round(ms["alpha0"], 4),
                "halo_r": round(ms["halo_r"], 2),
                "ge_halo_nonzero": ms["ge315_nonzero"],
                "rgb_at_alpha0": ms["rgb_at_alpha0"],
                "monotone_bad": bad,
                "radial": {str(x): round(radial_mean_alpha(piece, x), 1)
                           for x in (26.0, 28.0, 30.0, 31.0, 31.4, 32.0)},
                "rim_src_rgb": [round(float(x), 1) for x in dbg["rim_src"]],
                "rim_new_rgb": [round(float(x), 1) for x in dbg["rim_new"]],
                "rim": rs}

    json.dump(list(geo.values()), open(os.path.join(EV, "圆几何归一化.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n\n切件 → %s\n" % CUT)
    for g in geo.values():
        print("  %-3s %-7s 源圆心(%7.1f,%7.1f) 源圆径(128)%6.1f → 归一圆心%s 圆径%s "
              "（偏离画布中心 %s）｜ 光晕最外半径 %5.2f ｜ r=26/28/30/31/31.4/32 alpha %s"
              % (g["state"], g["key"], g["src_center128"][0], g["src_center128"][1], g["src_d128"],
                 g["out_center"], g["out_d128"], g["out_center_off"], g["halo_r"],
                 [g["radial"][k] for k in ("26.0", "28.0", "30.0", "31.0", "31.4", "32.0")]))

    print("\n【单调性】r∈[28.0,31.5] 逐 0.25px 径向均值「增 > 2」的处数（要求 0）")
    for g in geo.values():
        print("  %-3s %-7s 违例 %d 处 %s" % (g["state"], g["key"], len(g["monotone_bad"]),
                                            g["monotone_bad"] or ""))

    print("\n【描边实测】源圆缘采样色 → 实际用色 ｜ 归一后描边峰值/蓝度/径向宽度")
    for g in geo.values():
        if g["key"] != "lock":
            continue
        print("  %-3s %-7s 源描边色 RGB%s → 用色 RGB%s" % (g["state"], g["key"],
                                                    g["rim_src_rgb"], g["rim_new_rgb"]))
        rs = g["rim"]
        print("        峰值 r=%.2f 色 RGB%s 蓝度 B-R=%.1f ｜ 径向宽度(>60%%峰值) %.2f px"
              % (rs["peak_r"], rs["peak_rgb"], rs["peak_br"], rs["width_px"]))
        print("        蓝度剖面 r=%s\n                 B-R=%s"
              % (rs["profile_r"], rs["profile"]))


if __name__ == "__main__":
    main()
