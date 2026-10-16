# -*- coding: utf-8 -*-
r"""q0 · 侦察 gm_bg1 长项区的雪晶与笔画像素特征（为「雪晶保护带」定标）"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据", "q_gm1"); os.makedirs(EV, exist_ok=True)

im = Image.open(os.path.join(SRC, "otv_gm_bg1.png")).convert("RGBA")
a = np.asarray(im).astype(np.float32)
# 白底合成（与 pA 同口径）
bgwhite = np.ones_like(a) * 255.0
al = a[:, :, 3:4] / 255.0
comp = a[:, :, :3] * al + bgwhite[:, :, :3] * (1 - al)
print("image size", im.size, "mode", im.mode)

# 长项：word x971-1505 y987-1033 ; 文字窗 wx0=1018..wx1=1512
X0, X1 = 1000, 1520
Y0, Y1 = 975, 1045
sub = comp[Y0:Y1, X0:X1]
br = sub[:, :, 2] - sub[:, :, 0]
lum = sub.mean(axis=2)
print("region", (X0, Y0, X1, Y1), "shape", sub.shape)
for lo, hi in [(-999, 0), (0, 10), (10, 20), (20, 30), (30, 45), (45, 60), (60, 100), (100, 140), (140, 999)]:
    m = (br > lo) & (br <= hi)
    if m.sum():
        print("  b-r in (%4d,%4d] n=%6d  meanRGB=(%6.1f,%6.1f,%6.1f) lum=%6.1f" %
              (lo, hi, m.sum(), *sub[m].mean(axis=0), lum[m].mean()))
    else:
        print("  b-r in (%4d,%4d] none" % (lo, hi))

# 列剖面上视：每列 b-r>20 的最大亮度、像素数（找出雪晶列）
m20 = br > 20
print("\n列剖面（每 8 列）: x, n(b-r>20), maxlum, meanRGB")
for x in range(0, sub.shape[1], 8):
    col = m20[:, x]
    if col.sum():
        print("  x=%4d n=%3d maxlum=%6.1f  mean=(%5.1f,%5.1f,%5.1f)" %
              (X0 + x, col.sum(), lum[:, x][col].max(), *sub[:, x][col].mean(axis=0)))
    else:
        print("  x=%4d n=  0" % (X0 + x))

# 8x 放大裁片（含雪晶区），供肉眼看
for tag, (cx0, cy0, cx1, cy1) in {
    "long_full": (960, 970, 1520, 1050),
    "snow_zoom": (1150, 960, 1420, 1050),
}.items():
    c = Image.fromarray(np.clip(comp[cy0:cy1, cx0:cx1], 0, 255).astype(np.uint8))
    z = 8 if tag == "snow_zoom" else 4
    c.resize((c.width * z, c.height * z), Image.NEAREST).save(os.path.join(EV, "q0_%s.png" % tag))
    print("saved", tag, c.size, "->", z, "x")
