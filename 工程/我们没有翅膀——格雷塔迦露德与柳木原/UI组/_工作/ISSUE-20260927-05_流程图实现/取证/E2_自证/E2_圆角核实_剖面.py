#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2_圆角核实_剖面.py — 用**像素**判定「圆角连接 + 圆端帽」是否真的生效

三个判据（全部基于"墨迹面积"，对 AA 稳健；w=4 ⇒ 理论值如下）

【A】折角（join）：取折角处**外侧凹口方块**（边长 w/2=2px，共 4 个像素）的墨迹面积
      · miter（直角尖）  ≈ 4.00 px²（凹口被完全填满）
      · round（圆弧）    ≈ π·(w/2)²/4 = π ≈ 3.14 px²（外侧顶点被削掉）
      · bevel（斜切）    ≈ (w/2)²/2 = 2.00 px²
    凹口方块 = {C + a·d1 − b·d2 : a,b ∈ [0, w/2]}（d1=入边方向, d2=出边方向），
    由两段线宽的**两条外沿**围成，是唯一能区分三种 join 的区域。

【B/C】端帽（cap）：取端点外侧**半圆外接方块**（w×(w/2) = 4×2px，共 8 个像素）
      · butt/flat（平齐切）≈ 0 px²
      · round（半圆）      ≈ π·(w/2)²/2 = 2π ≈ 6.28 px²
      · square（方头）     ≈ w·(w/2) = 8.00 px²
    起点用 startCap、终点用 endCap（终点若带箭头，箭头多边形会盖住 ⇒ 只测起点）。

输出：逐探针的 alpha 表 + 面积 + 判词；并把每处 ≥12× 最近邻放大的裁剪存成 PNG。
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
TOL_BAND = 12          # 面积判定的带宽（AA/取整）


def hexstr(c):
    return "#%08X" % (c & 0xFFFFFFFF)


def load_links(args):
    if args.links.endswith(".json") and "32_flowchart" in args.links:
        d = json.loads(Path(args.links).read_text(encoding="utf-8"))
        return [{"id": l["id"], "pts": [list(p) for p in l["pts"]], "w": l["w"],
                 "color": l["color"], "arrow": bool(l.get("arrow"))} for l in d["links"]]
    d = json.loads(Path(args.links).read_text(encoding="utf-8"))
    L = d["links"] if isinstance(d, dict) and "links" in d else d
    return [{"id": l["id"], "pts": [list(p) for p in l["pts"]], "w": l["w"],
             "color": l["color"], "arrow": bool(l.get("arrow"))} for l in L]


def ink_area(px, cols, rows, exp, tol=40):
    """方块内「墨迹」面积 = Σcolor-match / 255（用 alpha 加权，
       与目标色的 RGB 距离 <= tol 才算墨迹，排除背景与别的美术）"""
    a = 0.0
    detail = []
    for y in rows:
        row = []
        for x in cols:
            p = px[x, y]
            d = max(abs(p[0] - exp[0]), abs(p[1] - exp[1]), abs(p[2] - exp[2]))
            hit = (p[3] > 0) and (d <= tol)
            row.append((p[3], d, hit))
            if hit:
                a += p[3] / 255.0
        detail.append(row)
    return a, detail


def unit(dx, dy):
    n = (dx * dx + dy * dy) ** 0.5
    return (dx / n, dy / n)


def probe_corner(px, C, d1, d2, w, exp):
    """凹口方块 = C + a·d1 − b·d2（a,b ∈ [0,w/2]）"""
    h = w // 2
    e1, e2 = d1, (-d2[0], -d2[1])
    xs, ys = [], []
    for a in (0, h):
        for b in (0, h):
            xs.append(C[0] + a * e1[0] + b * e2[0])
            ys.append(C[1] + a * e1[1] + b * e2[1])
    cols = list(range(int(min(xs)), int(max(xs))))
    rows = list(range(int(min(ys)), int(max(ys))))
    area, detail = ink_area(px, cols, rows, exp)
    if area >= 4.0 - TOL_BAND / 100:
        v = "miter（直角尖）"
    elif abs(area - 3.1416) <= 0.45:
        v = "round（圆角）"
    elif abs(area - 2.0) <= 0.4:
        v = "bevel（斜切）"
    else:
        v = "无法判定（面积落在三档之间）"
    return {"kind": "corner", "at": C, "cols": cols, "rows": rows, "area": area,
            "detail": detail, "verdict": v,
            "theory": "miter 4.00 / round 3.14 / bevel 2.00"}


def probe_cap(px, P, d, w, exp, which):
    """端帽外接方块：从端点沿「离开线段」的方向外扩 w/2，宽度 w
       （起点用 −d，终点用 +d；方块恰好外接 round 半圆 / square 方头）"""
    h = w // 2
    ux, uy = d
    if which == "start":
        ux, uy = -ux, -uy
    if abs(ux) > abs(uy):                      # 线段水平 ⇒ 沿 x 外扩
        cols = list(range(P[0], P[0] + h)) if ux > 0 else list(range(P[0] - h, P[0]))
        rows = list(range(P[1] - h, P[1] + h))
    else:                                      # 线段垂直 ⇒ 沿 y 外扩
        rows = list(range(P[1], P[1] + h)) if uy > 0 else list(range(P[1] - h, P[1]))
        cols = list(range(P[0] - h, P[0] + h))
    area, detail = ink_area(px, cols, rows, exp)
    if area <= 0.6:
        v = "butt/flat（平齐切）"
    elif abs(area - 6.2832) <= 0.7:
        v = "round（半圆）"
    elif abs(area - 8.0) <= 0.7:
        v = "square（方头）"
    else:
        v = "无法判定"
    return {"kind": "cap-" + which, "at": P, "cols": list(cols), "rows": list(rows),
            "area": area, "detail": detail, "verdict": v,
            "theory": "butt 0 / round 6.28 / square 8.00"}


def crop_zoom(im, cx, cy, r, zoom, path, label):
    box = (max(0, cx - r), max(0, cy - r), min(im.width, cx + r), min(im.height, cy + r))
    c = im.crop(box).convert("RGBA")
    c = c.resize((c.width * zoom, c.height * zoom), Image.NEAREST)
    bg = Image.new("RGBA", c.size, (20, 20, 24, 255))
    bg.alpha_composite(c)
    d = ImageDraw.Draw(bg)
    d.text((3, 2), label, fill=(255, 220, 120, 255))
    bg.save(path)
    return path


def report_probe(px, im, zoomdir, link, pr):
    e = pr["detail"]
    print("  [%s] @%s  方块 cols=%s rows=%s" % (pr["kind"], pr["at"], pr["cols"], pr["rows"]))
    print("       alpha 表（按行）:")
    for row in e:
        print("         " + "  ".join("a=%3d%s" % (a, "*" if hit else " ") for a, d, hit in row))
    print("       墨迹面积 = %.2f px²   理论: %s" % (pr["area"], pr["theory"]))
    print("       判词 = %s" % pr["verdict"])
    lab = "%s %s area=%.2f" % (link["id"], pr["kind"], pr["area"])
    p = crop_zoom(im, pr["at"][0], pr["at"][1], 10, 12,
                  zoomdir / ("E2_圆角核实_放大_%s_%s.png" % (link["id"].replace(".", "_"), pr["kind"])), lab)
    print("       放大图 = %s（12x 最近邻，窗口 ±10px）" % p.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", required=True)
    ap.add_argument("--links", required=True, help="fixture_effective*.json 或 layout/screens/32_flowchart.json")
    ap.add_argument("--link", default="", help="只测这一条（默认全测）")
    ap.add_argument("--only", default="", help="corner / cap-start / cap-end / 空=全部")
    args = ap.parse_args()

    im = Image.open(args.png).convert("RGBA")
    px = im.load()
    links = load_links(args)
    if args.link:
        links = [l for l in links if l["id"] == args.link]
    zoomdir = HERE
    print("PNG   : %s (%dx%d)" % (args.png, im.width, im.height))
    print("links : %s" % args.links)
    for lk in links:
        exp = ((lk["color"] >> 16) & 0xFF, (lk["color"] >> 8) & 0xFF, lk["color"] & 0xFF)
        pts, w = lk["pts"], lk["w"]
        print("\n%s  pts=%s w=%d color=%s arrow=%s" % (lk["id"], pts, w, hexstr(lk["color"]), lk["arrow"]))
        # 折角：所有内部顶点
        if args.only in ("", "corner"):
            for i in range(1, len(pts) - 1):
                C = pts[i]
                d1 = unit(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
                d2 = unit(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                if abs(C[0] - round(C[0])) > 1e-6 or abs(C[1] - round(C[1])) > 1e-6:
                    print("  （顶点 %s 非整数坐标 ⇒ 剖面会受 AA 影响，仅作参考）" % C)
                report_probe(px, im, zoomdir, lk,
                             probe_corner(px, (int(round(C[0])), int(round(C[1]))), d1, d2, w, exp))
        # 端帽
        d0 = unit(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
        dN = unit(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
        if args.only in ("", "cap-start") and len(pts) > 1:
            report_probe(px, im, zoomdir, lk,
                         probe_cap(px, (int(round(pts[0][0])), int(round(pts[0][1]))), d0, w, exp, "start"))
        if args.only in ("", "cap-end"):
            if lk["arrow"]:
                print("  [cap-end] 跳过：该边 arrow=true，终点被箭头多边形覆盖（测不出 endCap）")
            else:
                report_probe(px, im, zoomdir, lk,
                             probe_cap(px, (int(round(pts[-1][0])), int(round(pts[-1][1]))), dN, w, exp, "end"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
