# -*- coding: utf-8 -*-
r"""M22 · 对话框裁切图探针 v2：只在 alpha 有效区取样（透明区 RGB 是垃圾）。"""
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


print("=== 采样点 (x,y) -> RGBA ===")
for pt in [(200, 50), (400, 50), (800, 200), (300, 200), (1500, 200), (1000, 30), (600, 30),
           (900, 300), (60, 200), (100, 50), (50, 50), (20, 200), (1600, 200), (1620, 200),
           (300, 100), (300, 90), (300, 110)]:
    print("  %s -> %s  lum=%d" % (pt, px[pt[0], pt[1]], lum(px[pt[0], pt[1]])))


def scan_h(y, x0, x1, mina=128):
    return [(x, lum(px[x, y]), px[x, y][3]) for x in range(x0, x1) if px[x, y][3] >= mina]


def scan_v(x, y0, y1, mina=128):
    return [(y, lum(px[x, y]), px[x, y][3]) for y in range(y0, y1) if px[x, y][3] >= mina]


def dips(seq, win=3, depth=8):
    out = []
    for i in range(win, len(seq) - win):
        v = seq[i][1]
        if v <= seq[i - win][1] - depth and v <= seq[i + win][1] - depth:
            out.append((seq[i][0], v))
    merged = []
    for p, v in out:
        if merged and p - merged[-1][1] <= 3:
            if v < merged[-1][2]:
                merged[-1] = (merged[-1][0], p, v)
        else:
            merged.append((p, p, v))
    return merged


print("\n=== alpha>=128 的逐列计数（找不透明内容的左右边界）===")
ap = crop.getchannel("A").load()
colc = [sum(1 for y in range(H) if ap[x, y] >= 128) for x in range(W)]
runs, s0 = [], None
for x, c in enumerate(colc):
    if c > 0 and s0 is None:
        s0 = x
    elif c == 0 and s0 is not None:
        runs.append((s0, x - 1)); s0 = None
if s0 is not None:
    runs.append((s0, W - 1))
print(" 段: %s" % runs[:10])
print(" 前 60 列计数: %s" % colc[:60])
print(" 末 60 列计数: %s" % colc[-60:])

print("\n=== alpha>=128 的逐行计数 ===")
rowc = [sum(1 for x in range(W) if ap[x, y] >= 128) for y in range(H)]
print(" 前 70 行: %s" % rowc[:70])
print(" 末 40 行: %s" % rowc[-40:])

print("\n=== 名字框：水平扫描（alpha>=128）找上下描边 ===")
for x in (200, 300, 400, 500):
    print(" x=%d dips: %s" % (x, dips(scan_v(x, 0, 140), 3, 8)))

print("\n=== 名字框：竖直扫描（alpha>=128）找左右描边 ===")
for y in (30, 45, 60, 75):
    print(" y=%d dips: %s" % (y, dips(scan_h(y, 0, 700), 3, 8)))

print("\n=== 大框：水平扫描找上下描边 ===")
for x in (700, 900, 1100, 1300):
    print(" x=%d dips: %s" % (x, dips(scan_v(x, 0, H), 4, 8)))

print("\n=== 大框：竖直扫描找左右描边 ===")
for y in (150, 200, 250):
    print(" y=%d dips: %s" % (y, dips(scan_h(y, 0, W), 4, 8)))