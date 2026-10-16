# -*- coding: utf-8 -*-
"""M3 证据：统计两图在指定矩形内的逐像素差异（截图坐标系）。
用法：python m3_regioncount.py <a.png> <b.png> <x0> <y0> <x1> <y1>
"""
import sys
from PIL import Image, ImageChops

a = Image.open(sys.argv[1]).convert("RGB")
b = Image.open(sys.argv[2]).convert("RGB")
box = tuple(int(v) for v in sys.argv[3:7])
d = ImageChops.difference(a, b).convert("L").crop(box)
px = d.load()
w, h = d.size
nz = mx = 0
for y in range(h):
    for x in range(w):
        v = px[x, y]
        if v:
            nz += 1
            if v > mx:
                mx = v
print("矩形 %s 内：非零差异 %d / %d（%.2f%%），最大灰度差 %d" % (str(box), nz, w * h, 100.0 * nz / (w * h), mx))
