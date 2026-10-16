# -*- coding: utf-8 -*-
r"""measure_stroke.py —— ISSUE-20260927-07 取证：选择支节点描边「厚度均匀性」数字 + 8× 放大对照图。

**方法（改前/改后同一口径，与实现无关）**：不复算任何候选实现，直接从磁盘 PNG 反解覆盖率：
    基准 base = recolor(原件)（「只改色不描边」的应有值；recolor/SPEC/ON_GAIN 从
                make_node_variant_a.py 导入 ⇒ 口径唯一，避免两处实现漂移）
    实测 out  = 改前（`改前素材快照\`）/ 改后（`krkr\assets\ui\`）
    最小二乘反解覆盖率：cov = Σ_c (base_c − out_c)(base_c − color_c) / Σ_c (base_c − color_c)²
    （合成关系 out = cov×color + (1−cov)×base ⇒ 上式即最佳拟合；限幅 [0,1]）
  · 改前 = paste(色, ring) ⇒ cov 恰 0/1（**二值**）；改后 = AA 覆盖 ⇒ cov 取分数值。
  · **只改 RGB、alpha 不动** ⇒ 用同样关系反解即可，不需 alpha（alpha 另由自检②锁定）。

**指标**（每部位逐行/逐列）：
  run_px   扫描线上与带外端相连、cov ≥ 0.5 的**连续像素数**（= 眼里的带宽，整像素）
  sub      Σ cov（**子像素**带宽 ← AA 的意义所在：介于整数之间，故内缘可落在任意 1/16）
  eff      Σ cov × alpha/255（**视觉厚度**：把半透明折算掉）
  on_face  其中落在**可见实体面**（alpha ≥ SOLID）内的像素数 —— 旧实现相当一部分带宽落在
           柔光边（alpha 129…229）⇒ 那里不是实色描边，是「发毛/忽明忽暗」的来源
  alpha    带内 alpha 均值

**几何厚度**（不含扫描线切角 t/cosφ 的污染）：直线段 = 带面积 ÷ 带长；圆角 = 拟合圆扇区的
带面积 ÷ 弧长（解 t 的一元二次方程，弧长取带中径）。
**合成对照**（隔离「算法几何」与「素材噪声」）：理想圆盘掩码（1× 二值、半径 40）上分别跑
旧算法（`alpha>128` − `MinFilter(5)` 方核）与新算法（4× 超采样 + 圆盘腐蚀），量 0° 与 45° 的
几何厚度 —— 方核 45° 应 ≈ 2√2 = 2.83，圆盘应 ≈ 2.00。

产物：`描边厚度_改前改后.png`（8× 最近邻三部位对照）、`描边几何_数字.txt`。
"""
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import importlib.util                                                    # noqa: E402
import numpy as np                                                       # noqa: E402
from PIL import Image, ImageDraw, ImageFilter                            # noqa: E402

HERE = Path(__file__).resolve().parent
UI = HERE.parents[2]                       # …\UI组
ASSETS = UI / "krkr" / "assets" / "ui"
BEFORE = HERE / "改前素材快照"
SPEC_PY = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "复现脚本" / "make_node_variant_a.py"

_s = importlib.util.spec_from_file_location("mk_node", SPEC_PY)
mk = importlib.util.module_from_spec(_s)
_s.loader.exec_module(mk)

KIND = "select"
COLOR = np.array(mk.SPEC[KIND][3], dtype=float)          # #2A5490
SOLID = mk.SOLID_THR
STATES = ("off", "on")
SHEET = HERE / "描边厚度_改前改后.png"
TXT = HERE / "描边几何_数字.txt"
OLD_THR = 128                                            # 旧实现用的掩码阈值

REGIONS = [("① 左端圆角区", (0, 0, 44, 30)),
           ("② 顶边中段", (100, 0, 144, 26)),
           ("③ 底边中段", (100, 39, 144, 65))]
ZOOM = 8


# ------------------------------------------------------------------ 反解
def base_rgb(state):
    """「只改色不描边」的应有 RGB（口径与 build() 逐字一致）。"""
    hue, sat, vmul, _ = mk.SPEC[KIND]
    if state == "on":
        g, s = mk.ON_GAIN[KIND]
        sat, vmul = sat * s, vmul * g
    src = Image.open(mk.BACKUP / f"x_ui_node_{KIND}_{state}.png").convert("RGBA")
    return src, np.asarray(mk.recolor(src, hue=hue, sat=sat, vmul=vmul))[..., :3].astype(float)


def coverage(out_rgb, base):
    d = base - COLOR.reshape(1, 1, 3)
    den = (d * d).sum(axis=2)
    num = ((base - out_rgb.astype(float)) * d).sum(axis=2)
    return np.clip(np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0.0), 0.0, 1.0)


def load(tag, state):
    src, base = base_rgb(state)
    p = (BEFORE if tag == "before" else ASSETS) / f"x_ui_node_{KIND}_{state}.png"
    arr = np.asarray(Image.open(p).convert("RGBA"))
    return arr[..., 3].astype(float), coverage(arr[..., :3], base)


# ------------------------------------------------------------------ 逐扫描线
def run_from(cov, alpha, lines, axis, from_start=True):
    """返回每行/列 (run_px, sub=Σcov, eff=Σcov·α/255, on_face, alpha_mean)，取「与带外端相连」的连续段。"""
    out = []
    for k in lines:
        line = cov[k, :] if axis == 1 else cov[:, k]
        al = alpha[k, :] if axis == 1 else alpha[:, k]
        n = line.shape[0]
        order = range(n) if from_start else range(n - 1, -1, -1)
        i0 = next((i for i in order if line[i] > 0), None)
        if i0 is None:
            out.append((0, 0.0, 0.0, 0, 0.0))
            continue
        step = 1 if from_start else -1
        idx, i = [], i0
        while 0 <= i < n and line[i] > 0:
            idx.append(i)
            i += step
        seg, sea = line[idx], al[idx]
        out.append((int((seg >= 0.5).sum()), float(seg.sum()),
                    float((seg * sea / 255.0).sum()),
                    int(((seg >= 0.5) & (sea >= SOLID)).sum()), float(sea.mean())))
    return np.array(out, dtype=float)


def fmt_stats(rows):
    r = rows
    return ("n=%3d  带宽px min=%3.0f max=%3.0f 极差=%3.0f 均=%5.2f ｜ "
            "子像素宽 sub min=%5.2f max=%5.2f 极差=%5.2f 均=%5.2f ｜ "
            "视觉厚 eff 均=%5.2f ｜ 实体面 min=%3.0f max=%3.0f ｜ 带内α均=%5.1f"
            % (len(r), r[:, 0].min(), r[:, 0].max(), r[:, 0].max() - r[:, 0].min(), r[:, 0].mean(),
               r[:, 1].min(), r[:, 1].max(), r[:, 1].max() - r[:, 1].min(), r[:, 1].mean(),
               r[:, 2].mean(), r[:, 3].min(), r[:, 3].max(), r[:, 4].mean()))


# ------------------------------------------------------------------ 几何厚度
def strip_thickness(cov, rows, cols, along):
    """直线段几何厚度 = 带面积 ÷ 带长（排除逐行切角 t/cosφ 放大）。

    rows/cols 划定一个**只含目标边**的窗口（不能横跨上/下两条横带）；along='x' 除以列数
    （量顶/底边），along='y' 除以行数（量左/右端）。窗口位置不影响结果 ⇒ 改前/改后可比。
    """
    sub = cov[rows[0]:rows[1], cols[0]:cols[1]]
    n = sub.shape[1] if along == "x" else sub.shape[0]
    return float(sub.sum()) / n


def band_center(cov, npts=14, from_bottom=False, left=True):
    """对该**带自己的外轮廓**（每行最外一个 cov>0 像素）拟合圆心；from_bottom 从下往上取弧。"""
    ys = range(cov.shape[0] - 1, -1, -1) if from_bottom else range(cov.shape[0])
    pts = []
    for y in ys:
        xs = np.where(cov[y, :40] > 0)[0]
        if len(xs):
            pts.append((xs.min() if left else xs.max(), y))
        if len(pts) >= npts:
            break
    P = np.array(pts, float)
    x, y = P[:, 0], P[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    c, _, _, _ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
    cx, cy = c[0], c[1]
    R = float(np.sqrt(c[2] + cx * cx + cy * cy))
    res = float(np.max(np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R)))
    return cx, cy, R, res


def sector_thickness(cov, cx, cy, target_deg, half_deg=15.0):
    """圆角几何厚度：±half_deg 扇区内的带面积 ÷ 弧长。

    对**圆环扇区** A = Δθ(R₂²−R₁²)/2、r̄ = (R₁+R₂)/2 ⇒ **t = Σcov / (r̄·Δθ) 精确成立**，
    不需要 R₁/R₂（r̄ 用 cov 加权半径现算）⇒ 对圆心拟合偏差不敏感、改前/改后同口径。
    扇区必须围绕该拐角**自己的**圆心（左上/左下分别拟合），否则会吃到邻边的竖带。
    """
    Y, X = np.mgrid[0:cov.shape[0], 0:cov.shape[1]]
    r = np.hypot(X - cx, Y - cy)
    ang = np.degrees(np.arctan2(Y - cy, X - cx))
    d = np.abs((ang - target_deg + 180) % 360 - 180)
    sel = (d <= half_deg) & (cov > 0)
    A = float(cov[sel].sum())
    if A <= 0:
        return 0.0, 0
    rbar = float((cov[sel] * r[sel]).sum() / A)
    return A / (rbar * np.deg2rad(2 * half_deg)), int(sel.sum())


# ------------------------------------------------------------------ 合成对照
def synthetic_kernel_test():
    """理想 1× 二值圆盘（半径 40，圆心已知 (50,50)）上比旧（方核）/新（圆盘）算法的几何厚度。"""
    from PIL import ImageChops
    n = 101
    yy, xx = np.mgrid[0:n, 0:n]
    disk = ((xx - 50.0) ** 2 + (yy - 50.0) ** 2) <= 40.0 ** 2
    alpha = np.where(disk, 255, 0).astype(np.uint8)
    im = Image.fromarray(np.dstack([np.full((n, n), 90, np.uint8)] * 3 + [alpha]), "RGBA")

    m = im.getchannel("A").point(lambda p: 255 if p > OLD_THR else 0)      # 旧：方核
    old_cov = (np.asarray(ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(5)))) > 0).astype(float)
    new_cov = mk.stroke_coverage(alpha, width=mk.STROKE_W, scale=mk.SS, thr=mk.SOLID_THR)

    rows = []
    for lab, cov in (("旧：方核 MinFilter(5)（1×）", old_cov),
                     ("新：圆盘腐蚀 + 4× 超采样", new_cov)):
        ts = [(tgt,) + sector_thickness(cov, 50.0, 50.0, tgt, half_deg=15.0) for tgt in (0.0, 45.0)]
        rows.append((lab, ts))
    return rows


# ------------------------------------------------------------------ 主流程
def main():
    rec = {(st, tag): load(tag, st) for st in STATES for tag in ("before", "after")}
    lines = []
    print("=" * 118)
    print("ISSUE-20260927-07 · 选择支节点描边厚度取证（覆盖率由 PNG 反解；改前/改后同一口径）")
    print("合成口径 out = cov×#2A5490 + (1−cov)×base（base = recolor(原件)）；实体面 = alpha ≥ %d" % SOLID)
    print("=" * 118)

    for state in STATES:
        print("\n■ select_%s" % state)
        for tag, cn in (("before", "改前"), ("after", "改后")):
            alpha, cov = rec[(state, tag)]
            band = cov[cov > 0]
            lvl = np.unique(np.round(band * 16) / 16)
            print("  %s：描边带 cov>0 %4d px（cov≥0.5 %4d）｜ 覆盖率档位(1/16 量化) %d 档 %s"
                  "｜ 带内 α 均 %.1f（min %d）"
                  % (cn, len(band), int((band >= 0.5).sum()), len(lvl), np.round(lvl, 3).tolist(),
                     alpha[cov > 0].mean(), alpha[cov > 0].min()))
            solid = alpha >= SOLID
            ymin, ymax = np.where(solid.any(axis=1))[0].min(), np.where(solid.any(axis=1))[0].max()
            xmin = np.where(solid.any(axis=0))[0].min()
            x0 = {y: np.where(solid[y])[0].min() for y in range(ymin, ymax + 1) if solid[y].any()}
            straight = [y for y, v in x0.items() if v == xmin and ymin + 2 <= y <= ymax - 2]
            arc_all = [y for y, v in x0.items() if v > xmin]
            # 弧段里 y=8/9、y=55/56 整行落在「横带」内（逐行量到的是横带厚度）⇒ 排除
            runs_all = {y: run_from(cov, alpha, [y], 1, True)[0][0] for y in arc_all}
            arc = [y for y in arc_all if runs_all[y] < 25]
            locs = [
                ("顶边中段(逐列 x81-180)", run_from(cov, alpha, range(81, 181), 0, True)),
                ("底边中段(逐列 x81-180)", run_from(cov, alpha, range(81, 181), 0, False)),
                ("左端直线段(逐行 y%d-%d)" % (straight[0], straight[-1]),
                 run_from(cov, alpha, straight, 1, True)),
                ("左端弧段(逐行 y%d-%d)※%d行" % (arc[0], arc[-1], len(arc)),
                 run_from(cov, alpha, arc, 1, True)),
            ]
            for lab, rows in locs:
                t = "     %-28s %s" % (lab, fmt_stats(rows))
                print(t)
                lines.append("select_%s %s %s" % (state, cn, t.strip()))
            # 几何厚度（无切角放大）
            tt = strip_thickness(cov, rows=(ymin - 3, ymin + 8), cols=(81, 181), along="x")
            tl = strip_thickness(cov, rows=(straight[0], straight[-1] + 1),
                                 cols=(xmin - 2, xmin + 8), along="y")
            cx, cy, Rf, resf = band_center(cov)
            t_tl, n_tl = sector_thickness(cov, cx, cy, -135.0)
            cbx, cby, Rfb, resfb = band_center(cov, from_bottom=True)
            t_bl, n_bl = sector_thickness(cov, cbx, cby, 135.0)
            print("     几何厚度（带面积 ÷ 带长/弧长，排除切角放大）：顶边=%.2f 左端=%.2f px ｜ "
                  "左上弧45°=%.2f 左下弧45°=%.2f px（圆心左上 %.1f,%.1f R=%.2f 残差%.2f ｜ "
                  "左下 %.1f,%.1f R=%.2f 残差%.2f）"
                  % (tt, tl, t_tl, t_bl, cx, cy, Rf, resf, cbx, cby, Rfb, resfb))
            lines.append("select_%s %s 几何厚度 顶边=%.2f 左端=%.2f 左上45°=%.2f 左下45°=%.2f"
                         % (state, cn, tt, tl, t_tl, t_bl))
            print("     ※ 左端弧段逐行的带宽含 1/cosφ 切角放大（弧上法向不在扫描方向），非缺陷，"
                  "仅作逐行参考；均匀性以「几何厚度 / 子像素宽 sub」为准。")
            lines.append("")

    # 合成对照
    print("\n■ 合成对照（理想 1× 二值圆盘 r=40，隔离算法几何与素材噪声；几何厚度，±15° 扇区）")
    rows = synthetic_kernel_test()
    hdr = "     %-30s %-14s %-14s" % ("算法", "0°（直边）", "45°（圆角）")
    print(hdr)
    lines.append("")
    lines.append(hdr.strip())
    for lab, ts in rows:
        cells = ["%.2f px" % t for _, t, _ in ts]
        print("     %-30s %-14s %-14s" % (lab, cells[0], cells[1]))
        lines.append("     %-30s %-14s %-14s" % (lab, cells[0], cells[1]))
    print("     理论：方核（Chebyshev r=2）45° 厚度 = 2√2 ≈ 2.83；圆盘核 = 2.00 恒定。")

    draw_sheet()
    draw_overview()
    print("\n对照图：%s" % SHEET)
    print("全览图：%s" % (HERE / "描边全览_改前改后.png"))
    print("数字存档：%s" % TXT)
    TXT.write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------------ 全览（2×，看整体）
def draw_overview():
    f_h, f_n = mk.font(21, True), mk.font(16)
    z = 2
    ims = {t: Image.open((BEFORE if t == "before" else ASSETS) / "x_ui_node_select_off.png").convert("RGBA")
           for t in ("before", "after")}
    w, h = ims["before"].size
    W, H = 20 * 2 + w * z, 76 + (h * z + 40) * 2 + 20
    sheet = Image.new("RGB", (W, H), (22, 26, 34))
    d = ImageDraw.Draw(sheet)
    d.text((20, 18), "select_off 全览 · 改前 / 改后 · %d× 最近邻" % z, font=f_h, fill=(238, 244, 252))
    d.text((20, 44), "素材 263×65；看整体轮廓与描边的贴合", font=f_n, fill=(158, 172, 190))
    y = 76
    for tag, cn, col in (("before", "改前（旧实现：阶梯/粗细不均/圆角钩刺）", (240, 150, 150)),
                         ("after", "改后（4× 超采样 + 圆盘腐蚀：均匀 2px）", (150, 220, 170))):
        im = ims[tag].resize((w * z, h * z), Image.NEAREST).convert("RGB")
        sheet.paste(im, (20, y))
        d.rectangle([19, y - 1, 20 + w * z, y + h * z], outline=(72, 88, 110))
        d.text((20, y + h * z + 8), cn, font=f_n, fill=col)
        y += h * z + 40
    sheet.save(HERE / "描边全览_改前改后.png")


# ------------------------------------------------------------------ 8× 对照图
def draw_sheet():
    f_title, f_h, f_n = mk.font(30, True), mk.font(21, True), mk.font(16)
    pad, gap = 20, 26
    panels = [(lab, (b[2] - b[0]) * ZOOM, (b[3] - b[1]) * ZOOM) for lab, b in REGIONS]
    W = pad * 2 + max(p[1] for p in panels) * 2 + gap
    H = 100 + sum(46 + p[2] + 34 for p in panels) + pad
    sheet = Image.new("RGB", (W, H), (22, 26, 34))
    d = ImageDraw.Draw(sheet)
    d.text((pad, pad - 2), "选择支节点描边 · 改前 / 改后 · %d× 最近邻放大（无插值）" % ZOOM,
           font=f_title, fill=(238, 244, 252))
    d.text((pad, pad + 42), "x_ui_node_select_off.png (263×65)｜改前 = alpha>128 − MinFilter(5) 二值环带"
                            "｜改后 = 4× 超采样 + 圆盘腐蚀 + BOX 降采样（alpha 逐字节不变）",
           font=f_n, fill=(158, 172, 190))
    ims = {t: Image.open((BEFORE if t == "before" else ASSETS) / "x_ui_node_select_off.png").convert("RGBA")
           for t in ("before", "after")}
    y = 104
    for lab, box in REGIONS:
        d.text((pad, y), lab, font=f_h, fill=(255, 214, 140))
        y0 = y + 34
        for j, (tag, cn, col) in enumerate((("before", "改前", (240, 150, 150)),
                                            ("after", "改后", (150, 220, 170)))):
            pw, ph = (box[2] - box[0]) * ZOOM, (box[3] - box[1]) * ZOOM
            crop = ims[tag].crop(box).resize((pw, ph), Image.NEAREST).convert("RGB")
            x = pad + j * (pw + gap)
            sheet.paste(crop, (x, y0))
            d.rectangle([x - 1, y0 - 1, x + pw, y0 + ph], outline=(72, 88, 110))
            d.text((x, y0 + ph + 6), "%s" % cn, font=f_h, fill=col)
        y = y0 + ph + 34
    sheet.save(SHEET)


if __name__ == "__main__":
    main()
