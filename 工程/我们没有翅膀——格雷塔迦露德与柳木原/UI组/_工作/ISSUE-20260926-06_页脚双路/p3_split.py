# -*- coding: utf-8 -*-
r"""p3 · 强蓝（b-r>60）列/行剖面：分图标段与文字段，标定图标框与文字框
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

out = {}
for name, words in bbox.items():
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    br = a[:, :, 2] - a[:, :, 0]
    print("=" * 84); print(name)
    out[name] = []
    for w in words:
        x0, x1, y0, y1 = w["x0"], w["x1"], w["y0"], w["y1"]
        sub = br[y0:y1 + 1, x0:x1 + 1]
        strong = sub > 60
        cr = runs1d(strong.any(axis=0), 1)
        # 图标段 = 从左边第一个 run 起、run 间空隙 <=4 的连续块，其右界
        icon_x1 = None
        if cr:
            last = cr[0][1]
            for i in range(1, len(cr)):
                if cr[i][0] - last - 1 <= 5:
                    last = cr[i][1]
                else:
                    break
            icon_x1 = last
        rows = np.flatnonzero(strong.any(axis=1))
        iy0, iy1 = (int(rows[0]), int(rows[-1])) if len(rows) else (0, 0)
        print("  word x%d-%d h%d | strong cols runs=%s" % (x0, x1, w["h"], cr[:20]))
        print("     强蓝整体行 y%d-%d" % (iy0 + y0, iy1 + y0))
        if icon_x1 is not None:
            isub = strong[:, :icon_x1 + 1]
            irows = np.flatnonzero(isub.any(axis=1))
            print("     图标段 x%d-%d (w%d)  y%d-%d (h%d)"
                  % (x0, x0 + icon_x1, icon_x1 + 1, int(irows[0]) + y0, int(irows[-1]) + y0,
                     int(irows[-1] - irows[0] + 1)))
            tx0 = x0 + icon_x1 + 1
            tsub = strong[:, icon_x1 + 1:]
            trows = np.flatnonzero(tsub.any(axis=1))
            if len(trows):
                print("     文字段 x%d-%d (w%d)  y%d-%d (h%d)"
                      % (tx0, x1, x1 - tx0 + 1, int(trows[0]) + y0, int(trows[-1]) + y0,
                         int(trows[-1] - trows[0] + 1)))
            out[name].append({"word": [x0, y0, x1, y1], "icon": [x0, int(irows[0]) + y0, x0 + icon_x1, int(irows[-1]) + y0],
                              "text": [tx0, int(trows[0]) + y0, x1, int(trows[-1]) + y0] if len(trows) else None})
with open(os.path.join(WORK, "footer_bbox_split.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote footer_bbox_split.json")
