# -*- coding: utf-8 -*-
r"""M22 · 暂定对话框裁切图（1628×319）的描边定位探针（只读）。"""
from __future__ import annotations

import os

from PIL import Image

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
EVID = os.path.join(UI, "_工作", "M22_证据")

crop = Image.open(os.path.join(EVID, "dialog2_crop_raw.png")).convert("RGBA")
px = crop.load()
W, H = crop.size
print("crop %dx%d" % (W, H))


def lum(p):
    return (p[0] * 299 + p[1] * 587 + p[2] * 114) // 1000


def scan_h(y, x0, x1, step=1):
    """沿 y 行扫描，返回亮度序列。"""
    return [(x, lum(px[x, y]), px[x, y][3]) for x in range(x0, x1, step)]


def scan_v(x, y0, y1, step=1):
    return [(y, lum(px[x, y]), px[x, y][3]) for y in range(y0, y1, step)]


def dips(seq, win=3, depth=8):
    """局部极小（亮度下凹）= 描边候选。"""
    out = []
    for i in range(win, len(seq) - win):
        v = seq[i][1]
        if v <= seq[i - win][1] - depth and v <= seq[i + win][1] - depth:
            out.append((seq[i][0], v))
    # 合并相邻
    merged = []
    for p, v in out:
        if merged and p - merged[-1][1] <= 2:
            if v < merged[-1][2]:
                merged[-1] = (merged[-1][0], p, v)
        else:
            merged.append((p, p, v))
    return merged


print("\n=== 名字框：竖直扫描（找左右描边）===")
for y in (30, 45, 60):
    s = scan_h(y, 0, 700)
    print(" y=%d dips: %s" % (y, dips(s, 3, 8)))

print("\n=== 名字框：水平扫描（找上下描边）===")
for x in (200, 300, 400, 500):
    s = scan_v(x, 0, 140)
    print(" x=%d dips: %s" % (x, dips(s, 3, 8)))

print("\n=== 大框：水平扫描（找上下描边）===")
for x in (700, 800, 900, 1000, 1100, 1200):
    s = scan_v(x, 0, H)
    print(" x=%d dips: %s" % (x, dips(s, 4, 8)))

print("\n=== 大框：竖直扫描（找左右描边）===")
for y in (150, 200, 250):
    s = scan_h(y, 0, W)
    print(" y=%d dips: %s" % (y, dips(s, 4, 8)))

print("\n=== 右侧雪花装饰范围（在窗口内部）===")
for y in (140, 200, 260):
    row = [(x, lum(px[x, y])) for x in range(1150, W)]
    # 雪花是白色高亮（比底色更亮）
    bright = [x for x, v in row if v >= 235]
    print(" y=%d 亮像素(x>=1150) %s..%s  n=%d" % (y, bright[0] if bright else None,
                                                   bright[-1] if bright else None, len(bright)))

print("\n=== 左侧羽毛范围（窗口内部）===")
for y in (150, 200, 260):
    row = [(x, lum(px[x, y])) for x in range(0, 200)]
    bright = [x for x, v in row if v >= 235]
    print(" y=%d 亮像素(x<200) %s..%s  n=%d" % (y, bright[0] if bright else None,
                                                bright[-1] if bright else None, len(bright)))

print("\n=== alpha 通道：非透明范围 ===")
a = crop.getchannel("A")
for th in (8, 64, 128, 200):
    print(" th=%d bbox %s" % (th, a.point(lambda v: 255 if v >= th else 0).getbbox()))

print("\n=== 逐列 alpha>=64 计数（找左/右内容边界）===")
ap = a.point(lambda v: 255 if v >= 64 else 0).load()
colc = [sum(1 for y in range(H) if ap[x, y]) for x in range(W)]
runs = []
s0 = None
for x, c in enumerate(colc):
    if c > 0 and s0 is None:
        s0 = x
    elif c == 0 and s0 is not None:
        runs.append((s0, x - 1)); s0 = None
if s0 is not None:
    runs.append((s0, W - 1))
print(" 非空列段: %s" % runs)