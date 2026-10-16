# -*- coding: utf-8 -*-
r"""M22 · 对话框装饰物（雪花/羽毛）范围实测 + 候选矩形输出。"""
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


# --- 名字框右侧（x>200）内的雪花：白亮像素
print("=== 名字框区 (x 100..560, y 0..95) 内白亮像素 (lum>=246, a>=128) ===")
xs = []
for y in range(0, 95):
    for x in range(100, 560):
        p = px[x, y]
        if p[3] >= 128 and lum(p) >= 246:
            xs.append((x, y))
if xs:
    print("  bbox x %d..%d  y %d..%d  n=%d"
          % (min(a for a, _ in xs), max(a for a, _ in xs),
             min(b for _, b in xs), max(b for _, b in xs), len(xs)))

# --- 大框内部右侧雪花
print("\n=== 大框内右侧白亮像素 (x 900..1623, y 65..300) ===")
for th in (244, 246, 248):
    xs = [(x, y) for y in range(65, 300) for x in range(900, 1624)
          if px[x, y][3] >= 128 and lum(px[x, y]) >= th]
    if xs:
        print("  th=%d bbox x %d..%d y %d..%d n=%d"
              % (th, min(a for a, _ in xs), max(a for a, _ in xs),
                 min(b for _, b in xs), max(b for _, b in xs), len(xs)))

# --- 大框内部左侧羽毛
print("\n=== 大框内左侧白亮像素 (x 0..300, y 65..300) ===")
for th in (244, 246, 248):
    xs = [(x, y) for y in range(65, 300) for x in range(0, 300)
          if px[x, y][3] >= 128 and lum(px[x, y]) >= th]
    if xs:
        print("  th=%d bbox x %d..%d y %d..%d n=%d"
              % (th, min(a for a, _ in xs), max(a for a, _ in xs),
                 min(b for _, b in xs), max(b for _, b in xs), len(xs)))

# --- 大框右缘 / 左缘（不透明边界）
print("\n=== 大框外边界（alpha>=128）===")
ap = crop.getchannel("A").load()
rowc = [sum(1 for x in range(W) if ap[x, y] >= 128) for y in range(H)]
big = [y for y, c in enumerate(rowc) if c >= 1000]
print("  宽度>=1000 的行段: %d..%d" % (min(big), max(big)))
colc = [sum(1 for y in range(H) if ap[x, y] >= 128) for x in range(W)]
bigc = [x for x, c in enumerate(colc) if c >= 200]
print("  高度>=200 的列段: %d..%d" % (min(bigc), max(bigc)))

# --- 名字框外边界：alpha 逐行计数中「只有名字框」的那一段
print("\n=== 名字框段（行计数 400..500 的行）===")
nmrows = [y for y, c in enumerate(rowc) if 400 <= c <= 500]
print("  行 %d..%d" % (min(nmrows), max(nmrows)))
for y in (13, 20, 30, 50, 57):
    cols = [x for x in range(W) if ap[x, y] >= 128]
    # 名字框主体是连续段，取最长的连续段
    runs, s0 = [], None
    for x in range(W):
        if ap[x, y] >= 128 and s0 is None:
            s0 = x
        elif ap[x, y] < 128 and s0 is not None:
            runs.append((s0, x - 1)); s0 = None
    if s0 is not None:
        runs.append((s0, W - 1))
    runs.sort(key=lambda r: r[1] - r[0], reverse=True)
    print("  y=%d 最长连续段 %s（其余 %s）" % (y, runs[0], runs[1:4]))