# -*- coding: utf-8 -*-
r"""M22 · 右侧雪花（低对比半透明白）局部对比度检测。"""
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


Y0, Y1 = 70, 300
print("=== 列剖面：x 中「比该行中位亮度高出 >=8」的像素数（窗口内部）===")
prof = []
for x in range(900, 1624):
    c = 0
    for y in range(Y0, Y1):
        row = sorted(lum(px[xx, y]) for xx in range(900, 1624, 4))
        med = row[len(row) // 2]
        if px[x, y][3] >= 128 and lum(px[x, y]) >= med + 8:
            c += 1
    prof.append((x, c))
print("  " + " ".join("%d:%d" % (x, c) for x, c in prof[::20]))
run = [x for x, c in prof if c >= 5]
print("  count>=5 的 x: %s..%s n=%d" % (run[0] if run else None, run[-1] if run else None, len(run)))
run3 = [x for x, c in prof if c >= 3]
print("  count>=3 的 x: %s..%s n=%d" % (run3[0] if run3 else None, run3[-1] if run3 else None, len(run3)))

print("\n=== 行剖面：y 中「高于行中位 >=8」的像素数（x 1000..1620）===")
for y in range(60, 310, 10):
    row = sorted(lum(px[xx, y]) for xx in range(1000, 1620, 4))
    med = row[len(row) // 2]
    c = sum(1 for x in range(1000, 1620) if px[x, y][3] >= 128 and lum(px[x, y]) >= med + 8)
    print("  y=%d count=%d (med=%d)" % (y, c, med))

print("\n=== 名字框内部：逐行「高于中位 >=8」的像素数（y 14..84, x 130..540）===")
for y in range(14, 85, 4):
    row = sorted(lum(px[xx, y]) for xx in range(130, 540, 4))
    med = row[len(row) // 2]
    c = sum(1 for x in range(130, 540) if px[x, y][3] >= 128 and lum(px[x, y]) >= med + 8)
    print("  y=%d count=%d" % (y, c))