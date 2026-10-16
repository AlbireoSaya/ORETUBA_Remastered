# -*- coding: utf-8 -*-
r"""G1c · 标定「圆底描边」：量同族 x_ui_menuicon_*.png 的描边半径/宽度/色值。
用于给 64x64 新规格定描边参数（主代理要求「加粗到约 2px 并提高饱和度，与 menuicon 同族」）。
"""
import glob, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_G = HERE
for _ in range(6):
    if os.path.isdir(os.path.join(_G, "krkr")) and os.path.isdir(os.path.join(_G, "layout")):
        break
    _G = os.path.dirname(_G)
UI = os.path.join(_G, "krkr", "assets", "ui")


def prof(p, canvas, step=0.5):
    im = Image.open(p).convert("RGBA")
    a = np.array(im).astype(np.float64)
    n = a.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    al = a[..., 3]
    ys, xs = np.nonzero(al >= 128)
    d = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
    R = d / 2.0
    rows = []
    rr = np.arange(R * 0.72, R * 1.10, step)
    for x in rr:
        m = (r >= x - step / 2) & (r < x + step / 2)
        if m.sum() == 0:
            continue
        am = al[m]
        px = a[..., :3][m]
        sat = (px[:, 2] - px[:, 0])          # 蓝度 B-R
        rows.append((x, x / R, float(am.mean()), tuple(px.mean(axis=0)), float(sat.mean())))
    return R, d, rows


print("=" * 96)
print("x_ui_menuicon_* （96x96 画布）圆缘剖面：r/R < 1 为圆内，= 1 为 alpha>=128 外缘")
for p in sorted(glob.glob(os.path.join(UI, "x_ui_menuicon_start.png"))):
    R, d, rows = prof(p, 96, 1.0)
    print("  %s  圆径=%d R=%.1f" % (os.path.basename(p), d, R))
    print("    r(px)  r/R    meanA  meanRGB            B-R")
    for x, k, ma, rgb, sat in rows:
        print("   %6.1f %5.3f  %6.1f  (%3.0f,%3.0f,%3.0f)  %6.1f %s"
              % (x, k, ma, rgb[0], rgb[1], rgb[2], sat, "#" * int(max(0, sat) / 4)))
