# -*- coding: utf-8 -*-
"""W11b 诊断：跨源同 stem 组的内容相似度（宽高比感知：等比缩放->中心裁切->比较）
用于判定「同 stem 不同分辨率/宽高比」的候选是否同一张画。
"""
import os, re, sys
from collections import defaultdict
from PIL import Image, ImageChops

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
SOURCES = ["ot", "ota", "otp", "otr", "otv", "np"]

by_stem = defaultdict(list)
for src in SOURCES:
    d = os.path.join(LIB, src, "pic")
    for fn in sorted(os.listdir(d)):
        stem = fn[:-4][len(src) + 1:].lower()
        p = os.path.join(d, fn)
        with Image.open(p) as im:
            w, h = im.size
        by_stem[stem].append((src, fn[:-4], w, h, p))

N = 64


def norm(p):
    with Image.open(p) as im:
        g = im.convert("L")
        w, h = g.size
        nw = N
        nh = max(1, round(h * N / w))
        g = g.resize((nw, nh), Image.BILINEAR)
        if nh > N:
            top = (nh - N) // 2
            g = g.crop((0, top, N, top + N))
        elif nh < N:
            # 补黑到 N 高
            canvas = Image.new("L", (N, N), 0)
            canvas.paste(g, (0, (N - nh) // 2))
            g = canvas
        return g


def sim(p1, p2):
    a, b = norm(p1), norm(p2)
    d = ImageChops.difference(a, b)
    px = list(d.getdata())
    return 1.0 - sum(px) / (len(px) * 255.0)


def report(pairs_filter, title):
    print("== %s ==" % title)
    rows = []
    for stem in sorted(by_stem):
        v = by_stem[stem]
        a_list = [x for x in v if pairs_filter(x[0])]
        b_list = [x for x in v if not pairs_filter(x[0])]
        if not a_list or not b_list:
            continue
        best = None
        for a in a_list:
            for b in b_list:
                s = sim(a[4], b[4])
                if best is None or s > best[0]:
                    best = (s, a, b)
        rows.append((stem, best))
    rows.sort(key=lambda r: r[1][0])
    for stem, (s, a, b) in rows:
        ar_a = a[2] / a[3]
        ar_b = b[2] / b[3]
        same_ar = abs(ar_a - ar_b) / min(ar_a, ar_b) <= 0.02
        print("   %-12s sim=%.3f  %s %dx%d vs %s %dx%d  AR同=%s"
              % (stem, s, a[0], a[2], a[3], b[0], b[2], b[3], same_ar))
    hi = sum(1 for _, (s, _, _) in rows if s >= 0.90)
    mid = sum(1 for _, (s, _, _) in rows if 0.80 <= s < 0.90)
    lo = sum(1 for _, (s, _, _) in rows if s < 0.80)
    print("   共 %d 组；sim>=0.90: %d ; 0.80-0.90: %d ; <0.80: %d" % (len(rows), hi, mid, lo))
    return rows


which = sys.argv[1] if len(sys.argv) > 1 else "otv"
if which == "otv":
    report(lambda s: s == "otv", "otv vs Lucifen 源")
elif which == "np":
    report(lambda s: s == "np", "np vs 其它源")
elif which == "otv960":
    # 只看 otv 的 960x544 / 960x540（16:9）与 800x600 的相似度
    def f(s):
        return s == "otv"
    rows = []
    for stem in sorted(by_stem):
        v = by_stem[stem]
        a_list = [x for x in v if x[0] == "otv" and x[2] in (960, 1080)]
        b_list = [x for x in v if x[2] == 800 and x[3] == 600]
        if not a_list or not b_list:
            continue
        best = max(((sim(a[4], b[4]), a, b) for a in a_list for b in b_list), key=lambda t: t[0])
        rows.append((stem, best))
    rows.sort(key=lambda r: r[1][0])
    for stem, (s, a, b) in rows:
        print("   %-12s sim=%.3f  otv %dx%d vs ot %dx%d" % (stem, s, a[2], a[3], b[2], b[3]))
    print("   共 %d 组；sim>=0.90: %d ; 0.80-0.90: %d ; <0.80: %d"
          % (len(rows), sum(1 for _, (s, _, _) in rows if s >= .9),
             sum(1 for _, (s, _, _) in rows if .8 <= s < .9),
             sum(1 for _, (s, _, _) in rows if s < .8)))