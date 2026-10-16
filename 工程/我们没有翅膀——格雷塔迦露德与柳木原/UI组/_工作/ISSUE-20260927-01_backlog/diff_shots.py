# -*- coding: utf-8 -*-
"""比较两张实机导图的差异区（bbox + 差异像素数），定位「态变化」影响的元素范围。只读。"""
import sys, os
from PIL import Image, ImageChops

def diff(a, b):
    A = Image.open(a).convert("RGB"); B = Image.open(b).convert("RGB")
    D = ImageChops.difference(A, B)
    bbox = D.getbbox()
    px = D.load()
    n = 0; mx = 0
    for y in range(0, A.height, 1):
        for x in range(0, A.width, 1):
            v = max(px[x, y])
            if v > 8:
                n += 1
                if v > mx: mx = v
    print("%s vs %s\n   差异 bbox=%s  差异像素(>8)=%d  最大差=%d"
          % (os.path.basename(a), os.path.basename(b), bbox, n, mx))

if __name__ == "__main__":
    for i in range(1, len(sys.argv) - 1):
        diff(sys.argv[i], sys.argv[i + 1])
