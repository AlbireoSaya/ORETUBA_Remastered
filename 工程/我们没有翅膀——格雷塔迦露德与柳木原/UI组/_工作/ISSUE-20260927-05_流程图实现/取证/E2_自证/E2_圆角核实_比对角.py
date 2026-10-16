#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2_圆角核实_比对角.py — 把**任意一张生产图上的某个折角**与 `E2_圆角核实_参照POC.py`
渲出的参照矩阵（miter/bevel/round 三种 join，引擎自己画的）逐像素比对，
取残差最小者作为「实际生效的 join」。

为什么不用「面积算理论值」：w=4 时三种 join 的凹口面积只差 0.86~2.0 px²，
而实测存在 +0.5px 半像素偏移、线宽落在半像素上 ⇒ 面积会跨 3×3 像素块摊开，
手算模型容易差 0.4 px²。用**引擎自己的三种设置**当参照，则连"GDI+ 到底怎么铺
半像素"这件事都被自动抵消（两侧同一条渲染管线）。

用法
  python E2_圆角核实_比对角.py --prod <生产PNG> --pts "1040,792" --vertex 1
        [--ink 0xFF266080] [--bgx/-bgy 背景参考点] [--r 6]
  · --pts  : 折线点集（"x,y;x,y;..." 或 JSON 文件路径）
  · --vertex: 要测的内部顶点下标（1..n-2）
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REF_PNG = Path(r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\临时\e2_round_poc\runtime\savedata\round_ref.png")
CORNER_Y = (120, 260, 400)          # 朝向 L（臂在角**右侧**，d1=−x）三个折角的 y
CORNER_Y2 = (480, 560, 640)         # 朝向 R（臂在角**左侧**，d1=+x）三个折角的 y
JOIN_NAMES = ["miter", "bevel", "round"]
# ★ 参照图用的是 #FF65B1D4（POC 固定）；生产线色可能是别的（如 #FF266080）⇒
#   参照窗口的覆盖率**必须用参照自己的线色**反解，否则半覆盖像素的比例全错
#   （实测踩过：两边线色不同时残差 0.15 上下、三档糊在一起）
INK_REF = (101, 177, 212)


def parse_pts(s):
    p = Path(s)
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        pts = d["pts"] if isinstance(d, dict) else d
    else:
        pts = [[float(a) for a in seg.split(",")] for seg in s.split(";")]
    return [(float(x), float(y)) for x, y in pts]


def cover(px, x, y, ink, bg):
    """覆盖率：优先用 alpha 反解（与线色无关）；背景不透明时退回颜色反解"""
    p = px[x, y]
    ao = p[3] / 255.0
    ab = bg[3] / 255.0
    if ab < 0.995:
        return max(0.0, min(1.0, (ao - ab) / (1 - ab)))
    est = []
    for k in range(3):
        d = ink[k] - bg[k]
        if abs(d) > 12:
            est.append((p[k] - bg[k]) / d)
    if not est:
        return 0.0
    est.sort()
    return max(0.0, min(1.0, est[len(est) // 2]))


def window(px, cx, cy, r, ink, bg):
    return [[cover(px, cx + dx, cy + dy, ink, bg) for dx in range(-r, r + 1)]
            for dy in range(-r, r + 1)]


def resid(a, b):
    n = 0.0
    mx = 0.0
    for ra, rb in zip(a, b):
        for va, vb in zip(ra, rb):
            d = abs(va - vb)
            n += d * d
            mx = max(mx, d)
    cnt = sum(len(r) for r in a)
    return (n / cnt) ** 0.5, mx


def triple_png(path, items, zoom=14, r=6):
    cell = (2 * r + 1) * zoom
    out = Image.new("RGB", (cell * len(items) + 20 * (len(items) + 1), cell + 46), (18, 18, 22))
    d = ImageDraw.Draw(out)
    x0 = 20
    for title, arr in items:
        im = Image.new("RGB", (2 * r + 1, 2 * r + 1))
        p = im.load()
        for j, row in enumerate(arr):
            for i, v in enumerate(row):
                c = int(max(0, min(1, v)) * 255)
                p[i, j] = (c, c, c)
        out.paste(im.resize((cell, cell), Image.NEAREST), (x0, 30))
        d.text((x0, 12), title, fill=(255, 220, 120))
        x0 += cell + 20
    out.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prod", required=True)
    ap.add_argument("--pts", required=True, help='"x,y;x,y;..." 或 JSON 文件')
    ap.add_argument("--vertex", type=int, default=1)
    ap.add_argument("--ink", default="0xFF65B1D4")
    ap.add_argument("--bg", default="", help="背景参考点 x,y（默认自动取角点外侧 8px）")
    ap.add_argument("--r", type=int, default=6)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    inkint = int(args.ink, 16)
    ink = ((inkint >> 16) & 0xFF, (inkint >> 8) & 0xFF, inkint & 0xFF)
    pts = parse_pts(args.pts)
    i = args.vertex
    C = pts[i]
    cx, cy = int(round(C[0])), int(round(C[1]))
    d1 = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
    d2 = (pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
    print("production : %s" % args.prod)
    print("corner     : vertex %d @(%d,%d)  d1=(%g,%g) d2=(%g,%g)" % (i, cx, cy, d1[0], d1[1], d2[0], d2[1]))

    prod = Image.open(args.prod).convert("RGBA")
    ppx = prod.load()
    if args.bg:
        bx, by = [int(v) for v in args.bg.split(",")]
    else:                                  # 自动：沿 −d1 方向退 8px、再沿 d2 方向退 8px（线外）
        bx = int(round(cx - 8 * (1 if d1[0] else 0) - 0))
        by = int(round(cy - 8 * (1 if d1[1] else 0)))
        bx = cx - 8 if d1[0] != 0 else cx
        by = cy + 8 if d2[1] != 0 else (cy - 8 if d1[1] != 0 else cy)
    bg = ppx[bx, by]
    print("bg ref     : (%d,%d) rgba=%s" % (bx, by, bg))

    pm = window(ppx, cx, cy, args.r, ink, bg)
    ref = Image.open(REF_PNG).convert("RGBA")
    rpx = ref.load()
    scores = []
    items = [("PROD corner", pm)]
    # 参照折角朝向 = (d1=+x, d2=+y)；生产若朝向不同则先旋转点集（这里只支持同向，
    # 不同向请改参照 POC 增加对应朝向——见报告「参照矩阵只覆盖 2 种朝向」的说明）
    # ★ 折向必须与参照一致，否则两侧成镜像、残差全高（实测踩过）：
    #   d1 的 x 分量为负 ⇒ 臂在角右侧 = 参照 L 组 @x=248；为正 ⇒ 臂在角左侧 = 参照 R 组 @x=400
    if d1[0] < 0:
        refx = 248
        refy = CORNER_Y
        orient = "L(=臂在角右侧)"
    else:
        refx = 400
        refy = CORNER_Y2
        orient = "R(=臂在角左侧)"
    print("orientation: %s ⇒ 参照组 (x=%d)" % (orient, refx))
    for k, nm in enumerate(JOIN_NAMES):
        rm = window(rpx, refx, refy[k], args.r, INK_REF, (0, 0, 0, 255))
        rms, mx = resid(pm, rm)
        scores.append((rms, mx, nm))
        items.append(("REF %s" % nm, rm))
    for rms, mx, nm in sorted(scores):
        print("   %-6s RMS=%.4f max=%.3f" % (nm, rms, mx))
    print("   ⇒ 最接近 = %s" % sorted(scores)[0][2])
    out = args.out or str(HERE / ("E2_圆角核实_比对角_%s.png" % Path(args.prod).stem[:40]))
    triple_png(out, items, r=args.r)
    print("   对照图 = %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
