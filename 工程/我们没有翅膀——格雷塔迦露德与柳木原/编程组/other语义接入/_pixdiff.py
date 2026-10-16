# -*- coding: utf-8 -*-
r"""_pixdiff.py —— 纯 PIL 逐像素比较 off/tier1 两张 shot_901。
输出: 不同像素数 / 占比 / 差异包围盒 / 横向差异段(top5)。
用法: python -X utf8 _pixdiff.py <off.png> <tier1.png>
"""
import sys
from PIL import Image, ImageChops


def main():
    off = Image.open(sys.argv[1]).convert("RGB")
    t1 = Image.open(sys.argv[2]).convert("RGB")
    if off.size != t1.size:
        print("SIZE-MISMATCH", off.size, t1.size); return 2
    W, H = off.size
    d = ImageChops.difference(off, t1)
    # 逐通道阈值 → 掩码合并（避免亮度换算把色差吃掉）
    masks = [c.point(lambda v: 255 if v > 0 else 0) for c in d.split()]
    m = masks[0]
    for k in masks[1:]:
        m = ImageChops.lighter(m, k)
    bbox = m.getbbox()
    if bbox is None:
        print("IDENTICAL  size=%dx%d  diff=0" % (W, H)); return 0
    hist = m.histogram()
    n = hist[255]
    x0, y0, x1, y1 = bbox
    print("DIFFERENT  size=%dx%d  diff_px=%d (%.3f%%)  bbox=[%d..%d]x[%d..%d]"
          % (W, H, n, 100.0 * n / (W * H), x0, x1 - 1, y0, y1 - 1))
    px = m.load()
    colhas = [False] * W
    for x in range(x0, x1):
        for y in range(y0, y1):
            if px[x, y]:
                colhas[x] = True
                break
    segs, s = [], None
    for x in range(W):
        if colhas[x] and s is None:
            s = x
        elif not colhas[x] and s is not None:
            segs.append((s, x - 1)); s = None
    if s is not None:
        segs.append((s, W - 1))
    segs.sort(key=lambda t: t[1] - t[0], reverse=True)
    print("  横向差异段(top5, 宽): " + ", ".join("[%d..%d]w%d" % (a, b, b - a + 1) for a, b in segs[:5]))
    for a, b in segs[:5]:
        ymin, ymax, cnt = H, -1, 0
        for x in range(a, b + 1):
            for y in range(y0, y1):
                if px[x, y]:
                    cnt += 1
                    if y < ymin: ymin = y
                    if y > ymax: ymax = y
        print("    段[%d..%d] y=[%d..%d] px=%d" % (a, b, ymin, ymax, cnt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
