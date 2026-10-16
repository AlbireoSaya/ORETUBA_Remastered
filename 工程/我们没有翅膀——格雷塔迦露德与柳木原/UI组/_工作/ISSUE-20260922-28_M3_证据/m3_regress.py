# -*- coding: utf-8 -*-
"""M3 证据：改动前（baseline/）与改动后（final/）逐屏比对。
同时报「全图」与「画布区（自动定位黑底画布矩形）」两个口径的差异 ——
后者排除页面外壳（顶栏/页脚说明文字）的影响，直接答「渲染有没有回归」。
用法：python m3_regress.py <baseline_dir> <after_dir>
"""
import os
import sys
from PIL import Image, ImageChops


def canvas_rect(im):
    px = im.load()
    w, h = im.size
    lefts, rights = [], []
    for y in range(0, h, 7):
        xs = [x for x in range(w) if sum(px[x, y][:3]) < 12]
        if len(xs) > w // 3:
            lefts.append(xs[0]); rights.append(xs[-1])
    if not lefts:
        return None
    return (min(lefts), 0, max(rights) + 1, h)


def diffstats(a, b):
    d = ImageChops.difference(a, b).convert("L")
    px = d.load()
    w, h = a.size
    nz = mx = 0
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if v:
                nz += 1
                if v > mx:
                    mx = v
    return nz, w * h, mx


bd, ad = sys.argv[1], sys.argv[2]
for n in sorted(x for x in os.listdir(bd) if x.lower().endswith(".png")):
    pa, pb = os.path.join(bd, n), os.path.join(ad, n)
    if not os.path.exists(pb):
        print("%-14s 缺失 %s" % (n, pb)); continue
    a = Image.open(pa).convert("RGB"); b = Image.open(pb).convert("RGB")
    if a.size != b.size:
        print("%-14s 尺寸不同 %s vs %s" % (n, a.size, b.size)); continue
    nz, tot, mx = diffstats(a, b)
    r = canvas_rect(a)
    if r:
        ca, cb = a.crop(r), b.crop(r)
        cnz, ctot, cmx = diffstats(ca, cb)
    else:
        cnz = ctot = cmx = -1
    print("%-14s %s｜全图非零差异=%d/%d（%.4f%%，max=%d）｜画布区=%d/%d（%.4f%%，max=%d）%s"
          % (n, "%dx%d" % a.size, nz, tot, 100.0 * nz / tot, mx, cnz, ctot,
             (100.0 * cnz / ctot) if ctot else 0, cmx,
             "  ← 画布逐像素相同" if cnz == 0 else ""))
