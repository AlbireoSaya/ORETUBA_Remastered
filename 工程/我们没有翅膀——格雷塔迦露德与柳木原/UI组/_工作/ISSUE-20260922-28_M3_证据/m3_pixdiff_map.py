# -*- coding: utf-8 -*-
"""M3 证据：定位两态截图的差异分布（bbox + 16x16 网格块的差异计数）"""
import sys
from PIL import Image, ImageChops

a = Image.open(sys.argv[1]).convert("RGB")
b = Image.open(sys.argv[2]).convert("RGB")
d = ImageChops.difference(a, b).convert("L")
bb = d.getbbox()
print("差异 bbox =", bb, "  图像尺寸 =", a.size)
w, h = a.size
px = d.load()
CELL = 100
print("按 %dpx 网格的差异像素数（只列 > 0 的块；列为 x 块号）:" % CELL)
for gy in range(0, h, CELL):
    row = []
    for gx in range(0, w, CELL):
        n = 0
        for y in range(gy, min(gy + CELL, h), 2):
            for x in range(gx, min(gx + CELL, w), 2):
                if px[x, y] > 8:
                    n += 1
        row.append(n if n else None)
    if any(row):
        print("y=%4d-%4d : %s" % (gy, gy + CELL,
              " ".join(("%5d" % v) if v else "    ." for v in row)))
