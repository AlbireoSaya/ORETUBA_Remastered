# -*- coding: utf-8 -*-
r"""p4 · 背景（除词框外）的蓝饱和度统计：确定文字掩码阈值的安全上限"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))

for name, words in bbox.items():
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    br = a[:, :, 2] - a[:, :, 0]
    lum = a.mean(axis=2)
    band = np.zeros(br.shape, bool)
    band[955:1075, 860:1900] = True
    for w in words:
        band[max(0, w["y0"] - 8):w["y1"] + 9, max(0, w["x0"] - 8):w["x1"] + 9] = False
    bb = br[band]; ll = lum[band]
    print(name, "  bg px", bb.size)
    print("   ", " ".join("b-r>%d:%d" % (t, int((bb > t).sum())) for t in [10, 15, 20, 25, 30, 40, 50, 60]))
    print("    bg b-r max %.1f p99.9 %.1f | lum min %.1f mean %.1f" %
          (bb.max(), np.percentile(bb, 99.9), ll.min(), ll.mean()))
