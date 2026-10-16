# -*- coding: utf-8 -*-
"""W11b 诊断：列出多源组的候选明细 + np/otv 跨源内容相似度抽检"""
import os, re, sys, csv, hashlib
from collections import defaultdict
from PIL import Image, ImageChops

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
SOURCES = ["ot", "ota", "otp", "otr", "otv", "np"]

by_stem = defaultdict(list)
for src in SOURCES:
    d = os.path.join(LIB, src, "pic")
    for fn in sorted(os.listdir(d)):
        raw = fn[:-4]
        stem = raw[len(src) + 1:].lower()
        p = os.path.join(d, fn)
        with Image.open(p) as im:
            w, h = im.size
        by_stem[stem].append((src, raw, w, h, p))


def sig(p, n=48):
    with Image.open(p) as im:
        return im.convert("L").resize((n, n), Image.BILINEAR)


def sim(p1, p2, n=48):
    a, b = sig(p1, n), sig(p2, n)
    diff = ImageChops.difference(a, b)
    px = list(diff.getdata())
    return 1.0 - (sum(px) / (len(px) * 255.0))


mode = sys.argv[1] if len(sys.argv) > 1 else "multi"

if mode == "multi":
    multi = {k: v for k, v in by_stem.items() if len(v) > 1}
    print("多源组数:", len(multi), "/", len(by_stem))
    # 尺寸组合分布
    combos = defaultdict(int)
    for k, v in multi.items():
        combos[tuple(sorted({(x[2], x[3]) for x in v}))] += 1
    for c, n in sorted(combos.items(), key=lambda x: -x[1]):
        print("   %-40s %d" % (str(c), n))

elif mode == "np":
    print("== np 与其它源同 stem 的内容相似度（缩放到 48x48 灰度，1.0=完全一致） ==")
    rows = []
    for stem in sorted(by_stem):
        v = by_stem[stem]
        npc = [x for x in v if x[0] == "np"]
        oth = [x for x in v if x[0] != "np"]
        if not npc or not oth:
            continue
        best = None
        for a in npc:
            for b in oth:
                s = sim(a[4], b[4])
                if best is None or s > best[0]:
                    best = (s, a, b)
        rows.append((stem, best))
    rows.sort(key=lambda r: r[1][0])
    for stem, (s, a, b) in rows:
        print("   %-14s sim=%.3f  np %dx%d  vs  %s %dx%d" % (stem, s, a[2], a[3], b[0], b[2], b[3]))
    print("   共 %d 组；sim>=0.90: %d ; 0.75-0.90: %d ; <0.75: %d"
          % (len(rows), sum(1 for _, (s, _, _) in rows if s >= 0.9),
             sum(1 for _, (s, _, _) in rows if 0.75 <= s < 0.9),
             sum(1 for _, (s, _, _) in rows if s < 0.75)))

elif mode == "otv":
    print("== otv 与 Lucifen 源同 stem 的内容相似度 ==")
    rows = []
    for stem in sorted(by_stem):
        v = by_stem[stem]
        vc = [x for x in v if x[0] == "otv"]
        oth = [x for x in v if x[0] != "otv"]
        if not vc or not oth:
            continue
        best = None
        for a in vc:
            for b in oth:
                s = sim(a[4], b[4])
                if best is None or s > best[0]:
                    best = (s, a, b)
        rows.append((stem, best))
    rows.sort(key=lambda r: r[1][0])
    for stem, (s, a, b) in rows:
        print("   %-14s sim=%.3f  otv %dx%d  vs  %s %dx%d" % (stem, s, a[2], a[3], b[0], b[2], b[3]))
    print("   共 %d 组；sim>=0.90: %d ; 0.75-0.90: %d ; <0.75: %d"
          % (len(rows), sum(1 for _, (s, _, _) in rows if s >= 0.9),
             sum(1 for _, (s, _, _) in rows if 0.75 <= s < 0.9),
             sum(1 for _, (s, _, _) in rows if s < 0.75)))

elif mode == "dims":
    for src in SOURCES:
        c = defaultdict(int)
        for stem, v in by_stem.items():
            for x in v:
                if x[0] == src:
                    c[(x[2], x[3])] += 1
        print(src, sorted(c.items(), key=lambda x: -x[1])[:12])