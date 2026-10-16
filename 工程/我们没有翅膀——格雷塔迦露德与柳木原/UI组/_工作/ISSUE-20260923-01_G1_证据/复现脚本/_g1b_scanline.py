# -*- coding: utf-8 -*-
r"""G1b · 用**水平扫描线**（穿过圆心、朝相邻格之间的空隙方向）测圆底外圈柔光的真实衰减。

行扫描朝右走出本格后进入「本格与右邻格之间的空隙」，不会撞到别的圆 —— 比环形采样干净。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
RAW = os.path.join(EV, "原始大图")

CASES = [
    # (图, 标签, 圆心, 圆径d, 扫描方向)
    ("sheet_off_v2", "off lock", (197.5, 191.0, 295.0), "down"),      # 第 1 格：向下 = 行间空隙
    ("sheet_off_v2", "off option", (1340.5, 844.5, 297.0), "down"),   # 第 12 格：向下 = 图底留白
    ("sheet_on_v2", "on lock", (212.0, 201.0, 298.0), "down"),
    ("sheet_on_v2", "on option", (1324.0, 831.5, 299.0), "down"),
]


def scan(name, cx, cy, direction, span):
    im = Image.open(os.path.join(RAW, name + ".png")).convert("RGBA")
    a = np.array(im)[..., 3].astype(int)
    rgb = np.array(im)[..., :3].astype(int)
    h, w = a.shape
    xs, ys = [], []
    for k in range(span):
        y = int(round(cy)) + k
        x = int(round(cx))
        if y >= h or x >= w:
            break
        xs.append(k)
        ys.append((a[y, x], tuple(rgb[y, x])))
    return xs, ys


for name, tag, (cx, cy, d), direction in CASES:
    R = d / 2.0
    xs, ys = scan(name, cx, cy, direction, 260)
    print("=" * 96)
    print("%s · 圆心(%.1f,%.1f) R=%.1f ｜ 扫描：向下（行间空隙方向）" % (name, cx, cy, R))
    print("  偏移(源px)  r/R    alpha  RGB")
    keep = [0, 16, 32, 48, 64, 80, 96, 112, 128, 136, 144, 148, 150, 152, 156, 160,
            164, 168, 172, 176, 180, 184, 188, 192, 200, 208, 216, 224, 232, 240, 248]
    for k in keep:
        if k >= len(ys):
            break
        A, c = ys[k]
        print("  %8d  %5.3f   %4d   (%3d,%3d,%3d) %s"
              % (k, k / R, A, c[0], c[1], c[2], "#" * int(A / 6)))
    # 关键判据：alpha 降到 0 的半径
    z = [k for k in range(len(ys)) if ys[k][0] == 0]
    print("  → 扫描线上 alpha 首次为 0 的偏移 = %s (r/R = %s)"
          % (z[0] if z else "未出现", ("%.3f" % (z[0] / R)) if z else "-"))
    if z:
        for th in (32, 16, 8, 4, 2, 1):
            zz = [k for k in range(len(ys)) if ys[k][0] <= th]
            if zz:
                print("     alpha<=%-3d 起于偏移 %3d (r/R=%.3f)" % (th, zz[0], zz[0] / R))
