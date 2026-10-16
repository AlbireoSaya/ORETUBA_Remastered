# -*- coding: utf-8 -*-
r"""M22 · 对话框探针 v4：名字框上沿水平范围 + 右侧雪花列剖面。"""
from __future__ import annotations

import os

from PIL import Image

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
EVID = os.path.join(UI, "_工作", "M22_证据")

crop = Image.open(os.path.join(EVID, "dialog2_crop_raw.png")).convert("RGBA")
px = crop.load()
W, H = crop.size


def lum(p):
    return (p[0] * 299 + p[1] * 587 + p[2] * 114) // 1000


print("=== 名字框上沿描边 (y=11..15) 的 x 范围：逐 x 找该列在 y∈[9,17] 的最暗值 ===")
vals = []
for x in range(60, 600):
    if px[x, 12][3] < 128:
        continue
    v = min(lum(px[x, y]) for y in range(9, 18) if px[x, y][3] >= 128)
    vals.append((x, v))
dark = [x for x, v in vals if v <= 210]
print("  v<=210 的 x: %s..%s  n=%d" % (dark[0] if dark else None,
                                        dark[-1] if dark else None, len(dark)))
# 连续段
runs, s0, prev = [], None, None
for x in dark:
    if s0 is None:
        s0 = x
    elif x - prev > 3:
        runs.append((s0, prev)); s0 = x
    prev = x
if s0 is not None:
    runs.append((s0, prev))
print("  连续段: %s" % runs)

print("\n=== 名字框下沿描边 (y∈[83,88]) 的 x 范围 ===")
dark = []
for x in range(60, 600):
    if px[x, 86][3] < 128:
        continue
    v = min(lum(px[x, y]) for y in range(83, 89) if px[x, y][3] >= 128)
    if v <= 210:
        dark.append(x)
print("  x: %s..%s n=%d" % (dark[0] if dark else None, dark[-1] if dark else None, len(dark)))

print("\n=== 右侧雪花：列剖面（x 900..1623，y 70..300，lum>=242 的像素数）===")
prof = []
for x in range(900, 1624):
    c = sum(1 for y in range(70, 300) if px[x, y][3] >= 128 and lum(px[x, y]) >= 242)
    prof.append((x, c))
# 打印每 20 列的计数
print("  " + " ".join("%d:%d" % (x, c) for x, c in prof[::20]))
first = next((x for x, c in prof if c >= 3), None)
print("  首个 count>=3 的 x = %s" % first)

print("\n=== 右侧雪花：行剖面（y 60..310，x 1100..1620，lum>=242）===")
for y in range(60, 310, 10):
    c = sum(1 for x in range(1100, 1620) if px[x, y][3] >= 128 and lum(px[x, y]) >= 242)
    print("  y=%d count=%d" % (y, c))

print("\n=== 左侧羽毛：列剖面（x 0..300，y 70..300，lum>=242）===")
for x in range(0, 300, 10):
    c = sum(1 for y in range(70, 300) if px[x, y][3] >= 128 and lum(px[x, y]) >= 242)
    print("  x=%d count=%d" % (x, c))

print("\n=== 大框四边描边（alpha>=128 且 lum<=205 的边界扫描）===")
for y in (100, 200, 280):
    dark = [x for x in range(0, 80) if px[x, y][3] >= 128 and lum(px[x, y]) <= 205]
    dark2 = [x for x in range(1550, W) if px[x, y][3] >= 128 and lum(px[x, y]) <= 205]
    print("  y=%d 左缘暗线 %s ; 右缘暗线 %s" % (y, dark[:8], dark2[-8:]))
for x in (700, 1200):
    dark = [y for y in range(40, 90) if px[x, y][3] >= 128 and lum(px[x, y]) <= 205]
    dark2 = [y for y in range(280, 319) if px[x, y][3] >= 128 and lum(px[x, y]) <= 205]
    print("  x=%d 上缘暗线 %s ; 下缘暗线 %s" % (x, dark[:8], dark2[-8:]))