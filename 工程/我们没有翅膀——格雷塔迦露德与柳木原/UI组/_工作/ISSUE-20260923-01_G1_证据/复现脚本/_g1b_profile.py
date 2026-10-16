# -*- coding: utf-8 -*-
r"""G1b · 量源图里圆底「外圈柔光」的真实径向衰减，用于定 R_BALL / R_HALO。

对每个圆：以实测圆心为中心，按整数半径取环带，输出 mean alpha / max alpha / mean RGB。
半径以**源图像素**为单位；同时给出「相对圆底半径的倍数」，便于换算到 56 画布。
"""
import json, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
RAW = os.path.join(EV, "原始大图")

# 各候选图里第 1 格（lock）与第 12 格（option）的实测圆心/圆径（见 圆几何归一化.json）
CELLS = {
    "sheet_off_v2": {"lock": (247.5, 235.5, 299.0), "option": (2530.0, 1534.0, 300.0)},
    "sheet_on_v2": {"lock": (212.0, 201.0, 298.0), "option": (1324.0, 831.5, 299.0)},
}


def profile(img_rgba, cx, cy, d):
    a = np.array(img_rgba)[..., 3].astype(np.float64)
    rgb = np.array(img_rgba)[..., :3].astype(np.float64)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    R = d / 2.0
    rows = []
    rmax = int(R * 1.9)
    for ri in range(0, rmax + 1, 4):
        m = (r >= ri - 2) & (r < ri + 2)
        if m.sum() == 0:
            continue
        rows.append((ri, ri / R, float(a[m].mean()), float(a[m].max()),
                     rgb[m].mean(axis=0)))
    return R, rows


for name, cells in CELLS.items():
    p = os.path.join(RAW, name + ".png")
    im = Image.open(p).convert("RGBA")
    for key, (cx, cy, d) in cells.items():
        R, rows = profile(im, cx, cy, d)
        print("=" * 92)
        print("%s · %s  圆心(%.1f,%.1f) 圆径 %.1f → 圆底半径 R=%.1f" % (name, key, cx, cy, d, R))
        print("  r(源px)  r/R    meanA  maxA   meanRGB")
        for ri, k, ma, xa, rgb in rows:
            if ri > R * 1.75:
                break
            bar = "#" * int(ma / 6)
            print("  %6d  %5.3f  %6.1f %5.0f   (%3.0f,%3.0f,%3.0f) %s"
                  % (ri, k, ma, xa, rgb[0], rgb[1], rgb[2], bar))
