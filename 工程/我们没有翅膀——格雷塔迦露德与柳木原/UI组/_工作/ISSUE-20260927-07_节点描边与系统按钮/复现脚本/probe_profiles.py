# -*- coding: utf-8 -*-
"""探针 2（只读）：off/on 关系、相位无关的「径向剖面表」、掩码(alpha>=230)边界的抖动。"""
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


def load(k, st="off"):
    return np.asarray(Image.open(BACKUP / ("x_ui_node_%s_%s.png" % (k, st))).convert("RGBA")
                      .getchannel("A")).astype(np.float64)


def rect_of(a):
    H, W = a.shape
    m = a >= 230
    ys, xs = np.where(m)
    rows = np.arange(ys.min() + 18, ys.max() - 17)
    cols = np.arange(xs.min() + 18, xs.max() - 17)
    lp = a[rows, :].mean(axis=0)
    tp = a[:, cols].mean(axis=1)
    x0 = first_cross(lp) + 0.5
    x1 = (W - 1) - first_cross(lp[::-1]) + 0.5
    y0 = first_cross(tp) + 0.5
    y1 = (H - 1) - first_cross(tp[::-1]) + 0.5
    return (float(x0), float(x1), float(y0), float(y1))


def prof_line(a, rect, side):
    """返回 (line_values, b, u0)：line_values[i] = 该边中央带在像素 i 的均值（i 为 x 或 y 索引）。

    约定：line 覆盖整幅图的对应轴（0..W-1 或 0..H-1），值 = 中央带（去掉角区 20px）的行/列均值。
    """
    x0, x1, y0, y1 = rect
    H, W = a.shape
    if side in ("L", "R"):
        rows = np.arange(max(0, int(y0) + 22), min(H, int(y1) - 21))
        return a[rows, :].mean(axis=0), (x0 if side == "L" else x1), rows
    cols = np.arange(max(0, int(x0) + 22), min(W, int(x1) - 21))
    return a[:, cols].mean(axis=1), (y0 if side == "T" else y1), cols


def bin_means(vals, b, outward, decreasing=False):
    """相位无关的 1px 环带均值：bin d 覆盖到边界距离 [d, d+1)（outward=True）或 [-d-1, -d)。

    像素 i 覆盖 [i, i+1)（常量模型）；与环带求重叠长度加权平均。
    ★ decreasing：该边的「向外」是索引减小方向（L: −x、T: −y），必须翻转，否则内外颠倒。
    """
    out = {}
    for d in range(0, 18):
        s = -1.0 if decreasing else 1.0
        if outward:
            lo, hi = b + s * d, b + s * (d + 1.0)
            lo, hi = min(lo, hi), max(lo, hi)
        else:
            lo, hi = b - s * (d + 1.0), b - s * d
            lo, hi = min(lo, hi), max(lo, hi)
        tot, wsum = 0.0, 0.0
        for i in range(int(np.floor(lo)) - 1, int(np.ceil(hi)) + 1):
            if i < 0 or i >= len(vals):
                continue
            ov = min(hi, i + 1.0) - max(lo, float(i))
            if ov > 0:
                tot += vals[i] * ov
                wsum += ov
        out[d] = (tot / wsum) if wsum > 0 else None
    return out


def mask_boundary(a, rect, side, thr=230):
    """掩码(alpha>=thr)在该边的逐行/列「首个实体像素索引」，返回统计（抖动）。"""
    x0, x1, y0, y1 = rect
    H, W = a.shape
    idxs = []
    if side in ("L", "R"):
        for y in range(int(y0) + 20, int(y1) - 19):
            row = np.where(a[y] >= thr)[0]
            if len(row):
                idxs.append(int(row[0]) if side == "L" else int(row[-1]))
    else:
        for x in range(int(x0) + 20, int(x1) - 19):
            col = np.where(a[:, x] >= thr)[0]
            if len(col):
                idxs.append(int(col[0]) if side == "T" else int(col[-1]))
    idxs = np.array(idxs)
    d = np.diff(idxs)
    return {"n": len(idxs), "min": int(idxs.min()), "max": int(idxs.max()),
            "uniq": sorted(set(int(v) for v in idxs)),
            "n_gt1_steps": int((np.abs(d) > 0).sum()),
            "max_step": int(np.abs(d).max()) if len(d) else 0}


def main():
    print("### A. off vs on 的 alpha 关系")
    for k in KINDS:
        ao, an = load(k, "off"), load(k, "on")
        same = bool((ao == an).all())
        d = an - ao
        print("  %-8s alpha 完全一致=%s ｜ Δ 范围 [%.0f, %.0f] ｜ 不同像素 %d ｜ 若非零："
              % (k, same, d.min(), d.max(), int((d != 0).sum())))
        if not same:
            ro, rn = rect_of(ao), rect_of(an)
            print("             off rect=%s" % [round(v, 3) for v in ro])
            print("             on  rect=%s" % [round(v, 3) for v in rn])
            # 差值的空间分布：是否只在柔光区
            m = (d != 0)
            ys, xs = np.where(m)
            print("             差异像素包围盒 x[%d..%d] y[%d..%d]" % (xs.min(), xs.max(), ys.min(), ys.max()))

    print("\n### B. 相位无关径向剖面表（off 件；单位 alpha/255）")
    for k in KINDS:
        a = load(k, "off")
        rect = rect_of(a)
        print("\n  -- %s  rect=%s" % (k, [round(v, 3) for v in rect]))
        for side in ("L", "T", "R", "B"):
            vals, b, band = prof_line(a, rect, side)
            dec = side in ("L", "T")          # 向外 = 索引减小
            out = bin_means(vals, b, True, dec)
            ins = bin_means(vals, b, False, dec)
            row_out = "  ".join("%5.1f" % out[d] if out[d] is not None else "    —" for d in range(0, 14))
            row_in = "  ".join("%5.1f" % ins[d] if ins[d] is not None else "    —" for d in range(0, 13))
            print("     %s 边界=%.3f  中央带 n=%d" % (side, b, len(band)))
            print("        向外 d=0..13 : %s" % row_out)
            print("        向内 d=1..13 : %s" % row_in)

    print("\n### C. 掩码(alpha>=230) 边界的逐行/列抖动（现状）")
    for k in KINDS:
        a = load(k, "off")
        rect = rect_of(a)
        print("  %-8s" % k)
        for side in ("L", "T", "R", "B"):
            st = mask_boundary(a, rect, side)
            print("     %s 首实体像素 %s ｜ 相邻变化次数=%d 最大步进=%d（n=%d）"
                  % (side, st["uniq"], st["n_gt1_steps"], st["max_step"], st["n"]))

    print("\n### D. 底边实体行/列概览（找「凸起」所在行）")
    for k in KINDS:
        a = load(k, "off")
        rect = rect_of(a)
        H, W = a.shape
        print("  %-8s y1=%.3f" % (k, rect[3]))
        for y in range(int(rect[3]) - 3, int(rect[3]) + 2):
            row = a[y]
            xs = np.where(row >= 230)[0]
            if len(xs) == 0:
                print("     y=%2d 无实体像素（该行最大 alpha=%.0f）" % (y, row.max()))
                continue
            rr = np.arange(xs.min(), xs.max() + 1)
            holes = [int(x) for x in rr if row[x] < 230]
            print("     y=%2d 实体 x[%d..%d] n=%d 缺格=%s 行内 alpha [%.0f..%.0f]"
                  % (y, xs.min(), xs.max(), len(xs), holes[:10], row[xs.min():xs.max() + 1].min(),
                     row[xs.min():xs.max() + 1].max()))


if __name__ == "__main__":
    main()
