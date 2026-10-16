# -*- coding: utf-8 -*-
r"""q9 · 雪晶定量：在「雪晶连通域」上比较 原件 / 底板 / 现 A 的淡蓝像素数与逐像素差
雪晶连通域定义：底板背景上 b-r>=7 且 lum<=251 的连通块中，落在长项区的那一枚。
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
EV = os.path.join(WORK, "_证据", "q_plate"); os.makedirs(EV, exist_ok=True)
BX0, BY0 = 850, 930
FX0, FY0 = 880, 940
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[930:1088, 850:1910, :3]


B = np.stack([band(n) for n in ORDER])
spread = (B.max(axis=0) - B.min(axis=0)).max(axis=2)
allsame = spread < 0.5
plate = B[ORDER.index("otv_mv_bg.png")].copy()
plate[:, 1556 - 850:] = np.median(B, axis=0)[:, 1556 - 850:]

# 雪晶区（长项左侧那枚）
X0, X1, Y0, Y1 = 995, 1100, 955, 1032
reg = plate[Y0 - BY0:Y1 - BY0, X0 - BX0:X1 - BX0]
br = reg[:, :, 2] - reg[:, :, 0]
lum = reg.mean(axis=2)
snow = (br >= 7) & (lum <= 251)
print("底板雪晶区 b-r>=7 & lum<=251 : px=%d  (b-r mean=%.1f max=%.1f, lum mean=%.1f)" %
      (int(snow.sum()), br[snow].mean(), br[snow].max(), lum[snow].mean()))

for thr in (6, 7, 8, 10, 12, 14):
    m = (br >= thr) & (lum <= 251)
    print("  thr b-r>=%2d : px=%d" % (thr, int(m.sum())))

# 原件（gm_bg1）中该区
o = B[ORDER.index("otv_gm_bg1.png")][Y0 - BY0:Y1 - BY0, X0 - BX0:X1 - BX0]
obr = o[:, :, 2] - o[:, :, 0]
print("\n原件（含日文）同区：b-r>=7&lum<=251 px=%d（日文辉光污染，不能当雪晶）" % int(((obr >= 7) & (o.mean(axis=2) <= 251)).sum()))

# 现 A
a_raw = np.asarray(Image.open(os.path.join(OUT, "otv_gm_bg1_A_程序化.png")).convert("RGB")).astype(np.float32)
a = np.full(plate.shape, 255.0, np.float32)
a[FY0 - BY0:1088 - BY0, FX0 - BX0:1904 - BX0] = a_raw
ar = a[Y0 - BY0:Y1 - BY0, X0 - BX0:X1 - BX0]
abr = ar[:, :, 2] - ar[:, :, 0]
alum = ar.mean(axis=2)
asnow = (abr >= 7) & (alum <= 251)
print("现 A 同区：b-r>=7&lum<=251 px=%d" % int(asnow.sum()))
# 与底板逐像素差（仅雪晶域）
diff = np.abs(ar - reg).max(axis=2)
print("现 A vs 底板 在该区：max=%.0f mean=%.2f  px(d>2)=%d  px(d>6)=%d" %
      (diff.max(), diff.mean(), int((diff > 2).sum()), int((diff > 6).sum())))
# 只看雪晶域像素（底板上是雪晶的位置）被破坏程度
print("雪晶域像素处 A 与底板差：max=%.0f mean=%.2f  px(d>2)=%d / %d (%.1f%%)" %
      (diff[snow].max(), diff[snow].mean(), int((diff[snow] > 2).sum()), int(snow.sum()),
       100.0 * (diff[snow] > 2).sum() / max(1, snow.sum())))

# 新中文是否覆盖该区：A 中「不是背景色」的像素，用与底板差>6 近似
cov = diff > 6
print("现 A 中差>6 的像素（含新中文笔画）px=%d" % int(cov.sum()))

# 8x 三联图
z = 8
panels = []
for arr, lbl in [(B[ORDER.index("otv_gm_bg1.png")], "orig"), (plate, "plate"), (a, "A_v1")]:
    c = arr[Y0 - BY0:Y1 - BY0, X0 - BX0:X1 - BX0]
    panels.append(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).resize(
        (c.shape[1] * z, c.shape[0] * z), Image.NEAREST))
W = max(p.width for p in panels) * 3 + 24
H = max(p.height for p in panels)
sh = Image.new("RGB", (W, H + 20), (30, 30, 30))
x = 0
for p in panels:
    sh.paste(p, (x, 20)); x += p.width + 12
sh.save(os.path.join(EV, "q9_snow_8x_orig_plate_Av1.png"))
print("saved q9_snow_8x_orig_plate_Av1.png  (左=orig 中=plate 右=现A)")
