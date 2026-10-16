# -*- coding: utf-8 -*-
"""探针 3（只读）：内部是否均匀 / 逐边样本的噪声与趋势 / 半径复测 / 相位表。"""
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image                                                    # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
BACKUP = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "原形备份"
KINDS = ("section", "select", "frag")
SPRITE = {"section": (236, 65), "select": (263, 65), "frag": (228, 65)}
CROSS = 127.5


def load(k, st="off"):
    return np.asarray(Image.open(BACKUP / ("x_ui_node_%s_%s.png" % (k, st))).convert("RGBA")
                      .getchannel("A")).astype(np.float64)


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
    H, W = a.shape
    m = a >= 230
    ys, xs = np.where(m)
    rows = np.arange(ys.min() + pole, ys.max() - pole + 1)
    cols = np.arange(xs.min() + pole, xs.max() - pole + 1)
    lp = a[rows, :].mean(axis=0)
    tp = a[:, cols].mean(axis=1)
    x0 = first_cross(lp) + 0.5
    x1 = (W - 1) - first_cross(lp[::-1]) + 0.5
    y0 = first_cross(tp) + 0.5
    y1 = (H - 1) - first_cross(tp[::-1]) + 0.5
    return (float(x0), float(x1), float(y0), float(y1))


def main():
    print("### A. 内部均匀性（避开四角 r+6 的中央区）")
    for k in KINDS:
        a = load(k, "off")
        x0, x1, y0, y1 = rect_of(a)
        r = 22
        blk = a[int(y0 + r):int(y1 - r), int(x0 + r):int(x1 - r)]
        print("  %-8s 中央块 %s  均值=%.2f std=%.3f min=%.0f max=%.0f ｜ 每行均值范围 [%.1f..%.1f]"
              % (k, blk.shape, blk.mean(), blk.std(), blk.min(), blk.max(),
                 blk.mean(axis=1).min(), blk.mean(axis=1).max()))
        # 是否只有「内部洞/结构」：统计 !=253 的像素数
        print("             非 253 值分布: " + " ".join(
            "%d:%d" % (v, int((blk == v).sum())) for v in np.unique(blk)[:14]))

    print("\n### B. 逐边样本：相位 / 噪声 / 趋势（直线段）")
    for k in KINDS:
        a = load(k, "off")
        rect = rect_of(a)
        x0, x1, y0, y1 = rect
        r_est = {"section": 9.0, "select": 13.5, "frag": 14.0}[k]
        print("\n  -- %s rect=%s" % (k, [round(v, 3) for v in rect]))
        H, W = a.shape
        band_rows = np.arange(int(y0 + r_est + 3), int(y1 - r_est - 3))
        band_cols = np.arange(int(x0 + r_est + 3), int(x1 - r_est - 3))
        print("     直线带: 行[%d..%d] n=%d ｜ 列[%d..%d] n=%d"
              % (band_rows[0], band_rows[-1], len(band_rows),
                 band_cols[0], band_cols[-1], len(band_cols)))
        for side in ("L", "R", "T", "B"):
            if side in ("L", "R"):
                b = x0 if side == "L" else x1
                vals = a[band_rows, :] if side == "L" else a[band_rows, :]
                prof = a[band_rows, :].mean(axis=0)
                # 逐行在边界带上的原值（用于噪声/趋势）：取边界所在格与相邻两格
                i = int(np.floor(b + 0.5)) if side == "L" else int(np.ceil(b - 0.5))
                cells = [i - 1, i, i + 1] if side == "L" else [i + 1, i, i - 1]
                sam = a[np.ix_(band_rows, cells)]
                ph = (b - (i + 0.5)) * (1 if side == "L" else -1)
                print("     %s 边界=%.3f 相位(首格中心距,带符号,外向为正)=%+.3f" % (side, b, ph))
                for cix, cc in enumerate(cells):
                    col = sam[:, cix]
                    print("        x=%3d : 均值 %6.2f  std %4.2f  min %3.0f max %3.0f ｜ 线性趋势斜率 %+.3f/行"
                          % (cc, col.mean(), col.std(), col.min(), col.max(),
                             float(np.polyfit(band_rows, col, 1)[0])))
            else:
                b = y0 if side == "T" else y1
                prof = a[:, band_cols].mean(axis=1)
                i = int(np.floor(b + 0.5)) if side == "T" else int(np.ceil(b - 0.5))
                cells = [i - 1, i, i + 1] if side == "T" else [i + 1, i, i - 1]
                sam = a[np.ix_(cells, band_cols)]
                ph = (b - (i + 0.5)) * (1 if side == "T" else -1)
                print("     %s 边界=%.3f 相位(首格中心距,带符号,外向为正)=%+.3f" % (side, b, ph))
                for cix, cc in enumerate(cells):
                    row = sam[cix]
                    print("        y=%3d : 均值 %6.2f  std %4.2f  min %3.0f max %3.0f ｜ 线性趋势斜率 %+.3f/列"
                          % (cc, row.mean(), row.std(), row.min(), row.max(),
                             float(np.polyfit(band_cols, row, 1)[0])))

    print("\n### C. 半径复测（逐角：一维搜索拟合 + 45° 对角独立校核）")
    for k in KINDS:
        a = load(k, "off")
        rect = rect_of(a)
        x0, x1, y0, y1 = rect
        r_est = {"section": 9.0, "select": 13.5, "frag": 14.0}[k]
        print("  -- %s" % k)
        for c in ("TL", "TR", "BL", "BR"):
            left = c in ("TL", "BL")
            top = c in ("TL", "TR")
            side = "L" if left else "R"
            rows = (np.arange(int(np.ceil(y0)), int(np.floor(y0 + r_est))))
            if not top:
                rows = np.arange(int(np.ceil(y1 - r_est)), int(np.floor(y1)))
            pts = []
            for y in rows:
                prof = a[y]
                if side == "R":
                    cval = first_cross(prof[::-1])
                    cval = (len(prof) - 1) - cval if cval is not None else None
                else:
                    cval = first_cross(prof)
                if cval is not None:
                    pts.append((cval + 0.5, y + 0.5))
            P = np.array(pts)
            best = None
            for R in np.arange(2.0, 30.001, 0.01):
                cx = (x0 + R) if left else (x1 - R)
                cy = (y0 + R) if top else (y1 - R)
                dy = P[:, 1] - cy
                ok = np.abs(dy) <= R
                if ok.sum() < 4:
                    continue
                rad = np.sqrt(np.maximum(R * R - dy[ok] ** 2, 0.0))
                model = (cx - rad) if left else (cx + rad)
                rms = float(np.sqrt(np.mean((model - P[ok, 0]) ** 2)))
                if best is None or rms < best[1]:
                    best = (float(R), rms, int(ok.sum()))
            # 45 度
            sx = 1.0 if left else -1.0
            sy = 1.0 if top else -1.0
            px = x0 if left else x1
            py = y0 if top else y1
            kk = 1.0 / np.sqrt(2.0)

            def bil(u, v):
                iu, iv = int(np.floor(u)), int(np.floor(v))
                fu, fv = u - iu, v - iv
                return float(a[iv, iu] * (1 - fu) * (1 - fv) + a[iv, iu + 1] * fu * (1 - fv)
                             + a[iv + 1, iu] * (1 - fu) * fv + a[iv + 1, iu + 1] * fu * fv)
            rd = None
            prev = None
            for t in np.arange(0.0, 40.0, 0.02):
                v = bil(px + sx * kk * t, py + sy * kk * t)
                if prev is not None and v >= CROSS:
                    t0 = t - 0.02
                    tt = t0 + (0.02 * (CROSS - prev) / (v - prev) if v != prev else 0.0)
                    rd = tt / (np.sqrt(2.0) - 1.0)
                    break
                prev = v
            print("     %s  R=%.2f (rms=%.3f n=%d) ｜ 45°R=%.2f ｜ 行数=%d"
                  % (c, best[0], best[1], best[2], rd if rd else -1, len(pts)))


if __name__ == "__main__":
    main()
