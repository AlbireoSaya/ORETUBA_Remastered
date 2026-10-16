# -*- coding: utf-8 -*-
r"""p2 · 图标/文字细分：在词 bbox 内用低阈值蓝掩码找列空隙，定位图标段与文字段
同时统计：背景白度、雪晶像素强度、字面高、笔画宽（用于 A 路字号标定）
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))

def runs1d(v, min_len):
    idx = np.flatnonzero(v)
    if len(idx) == 0: return []
    g = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [(int(x[0]), int(x[-1])) for x in g if x[-1] - x[0] + 1 >= min_len]

for name, words in bbox.items():
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    br = b - r
    lum = (r + g + b) / 3.0
    print("=" * 80); print(name)
    # 背景采样：页脚区各词间隙
    for w in words:
        x0, x1, y0, y1 = w["x0"], w["x1"], w["y0"], w["y1"]
        pad = 12
        ring = []
        for yy in range(y0 - pad, y1 + pad):
            for xx in list(range(x0 - pad, x0)) + list(range(x1 + 1, x1 + pad)):
                if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]:
                    ring.append((br[yy, xx], lum[yy, xx]))
        ring = np.array(ring)
        sub = br[y0:y1 + 1, x0:x1 + 1]
        subL = lum[y0:y1 + 1, x0:x1 + 1]
        low = sub > 12
        cr = runs1d(low.any(axis=0), 1)
        gaps = [(int(cr[i][1]), int(cr[i + 1][0]), int(cr[i + 1][0] - cr[i][1] - 1)) for i in range(len(cr) - 1)]
        print("  word x%d-%d y%d-%d  ring b-r mean %.1f max %.1f / lum mean %.1f  | b-r>12 cols %d, gaps>=5: %s"
              % (x0, x1, y0, y1, ring[:, 0].mean(), ring[:, 0].max(), ring[:, 1].mean(),
                 int(low.any(axis=0).sum()), [x for x in gaps if x[2] >= 5]))
        # 文字段（gap 之后）字面高与笔画宽：取最后一长段
        if len(cr) >= 2:
            t0 = cr[-1][0]
            # 找“文字”起点 = 第一个 gap>=6 之后
            tx = None
            for (e, s2, gg) in gaps:
                if gg >= 6:
                    tx = s2; break
            print("      text seg start col(+%d)=%s  col runs=%s" % (x0, tx, cr[:14]))
        # 该词内最白与最蓝
        print("      sub br max %.1f  lum min %.1f  lum max %.1f  px(br>25) %d" %
              (sub.max(), subL.min(), subL.max(), int((sub > 25).sum())))
