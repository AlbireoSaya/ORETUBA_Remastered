# -*- coding: utf-8 -*-
r"""q5 · 用 mv_bg（页脚带最干净：仅 2 项，x1556+/x1741+）作参照：
 1) 校验 gm_bg1 与 mv_bg 在「长项字素外」是否逐像素相同；
 2) 定位长项雪晶几何；
 3) 检查 決定/戻る/選択 列内是否有雪晶（那三列无干净参照，只能用插值）。
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据", "q_plate"); os.makedirs(EV, exist_ok=True)
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]


def full(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[:, :, :3]


G = full("otv_gm_bg1.png"); M = full("otv_mv_bg.png"); Q = full("otv_quick_load_bg.png")

# 1) 长项区 (x1015-1520, y975-1045) gm_bg1 vs mv_bg，逐像素差
print("== gm_bg1 vs mv_bg 在长项外区域（应≈0） ==")
for tag, (x0, y0, x1, y1) in {
        "长项左图标槽 x971-1017": (971, 980, 1017, 1040),
        "长项下缘 y1045-1080": (1018, 1045, 1520, 1080),
        "长项上缘 y940-975": (1018, 940, 1520, 975),
        "右邻空隙 x1520-1552": (1520, 975, 1552, 1045),
}.items():
    d = np.abs(G[y0:y1, x0:x1] - M[y0:y1, x0:x1])
    print("  %-26s max=%6.1f mean=%.3f px(>1)=%d" % (tag, d.max(), d.mean(), int((d.max(axis=2) > 1).sum())))

print("\n== mv_bg vs quick_load_bg 同区域（互证参照一致） ==")
for tag, (x0, y0, x1, y1) in {"长项区 x1015-1520 y975-1045": (1015, 975, 1520, 1045),
                              "整带 x850-1910 y975-1045": (850, 975, 1910, 1045)}.items():
    d = np.abs(M[y0:y1, x0:x1] - Q[y0:y1, x0:x1])
    print("  %-28s max=%6.1f mean=%.3f px(>1)=%d" % (tag, d.max(), d.mean(), int((d.max(axis=2) > 1).sum())))

# 2) 长项字素足迹 = |gm_bg1 - mv_bg| > 1 in x1015-1520
print("\n== 长项字素足迹（|gm_bg1-mv_bg|>1，含辉光尾） ==")
x0, y0, x1, y1 = 1015, 970, 1522, 1046
d = np.abs(G[y0:y1, x0:x1] - M[y0:y1, x0:x1]).max(axis=2)
m = d > 1
ys, xs = np.nonzero(m)
print("  px=%d  bbox x%d-%d y%d-%d" % (int(m.sum()), xs.min() + x0, xs.max() + x0, ys.min() + y0, ys.max() + y0))
for t in (1, 2, 3, 5, 10, 20):
    mm = d > t
    ys2, xs2 = np.nonzero(mm)
    print("   thr>%2d px=%6d bbox x%d-%d y%d-%d" %
          (t, int(mm.sum()), xs2.min() + x0 if len(xs2) else 0, xs2.max() + x0 if len(xs2) else 0,
           ys2.min() + y0 if len(ys2) else 0, ys2.max() + y0 if len(ys2) else 0))

# 3) 雪晶几何：mv_bg 长项区内的淡蓝装饰（b-r>6），排除与 gm_bg1 字素重合处
sub = M[970:1046, 1015:1522]
br = sub[:, :, 2] - sub[:, :, 0]
mbr = m & (br > 6)
ys3, xs3 = np.nonzero(mbr)
print("\n== 长项区内 mv_bg 淡蓝像素(b-r>6) 且落在字素足迹内 px=%d ==" % int(mbr.sum()))
if len(xs3):
    print("   bbox x%d-%d y%d-%d" % (xs3.min() + x0, xs3.max() + x0, ys3.min() + y0, ys3.max() + y0))
# 纯装饰（字素足迹外）用于看雪晶本体
dbr = (br > 6) & ~m
ys4, xs4 = np.nonzero(dbr)
print("   字素足迹外的淡蓝装饰 px=%d" % int(dbr.sum()))
if len(xs4):
    print("   bbox x%d-%d y%d-%d" % (xs4.min() + x0, xs4.max() + x0, ys4.min() + y0, ys4.max() + y0))

# 4) 右三列（決定/戻る/選択）内是否有淡蓝装饰：用 mv_bg（x1603+ 有戻る）无法判定，
#    改用「7 屏中至少有 1 屏在该像素无字」的区域统计
B = np.stack([full(n)[970:1046, 850:1910] for n in ORDER])
spread = (B.max(axis=0) - B.min(axis=0)).max(axis=2)
allsame = spread < 0.5
print("\n== 右三列区 x1600-1910 y970-1046：7 屏全同像素占比 %.1f%% ==" %
      (100.0 * allsame[:, 1600 - 850:].sum() / allsame[:, 1600 - 850:].size))
pl = np.median(B, axis=0)
# 全同像素处 plate 必为背景 → 看那里有无淡蓝
plbr = pl[:, :, 2] - pl[:, :, 0]
dec = allsame & (plbr > 6)
print("   全同像素中的淡蓝装饰 px=%d" % int(dec[:, 1600 - 850:].sum()))
ys5, xs5 = np.nonzero(dec[:, 1600 - 850:])
if len(xs5):
    print("   bbox x%d-%d y%d-%d" % (xs5.min() + 1600, xs5.max() + 1600, ys5.min() + 970, ys5.max() + 970))

# 图证
z = 4
cx0, cy0, cx1, cy1 = 960, 960, 1180, 1050
c = Image.fromarray(np.clip(M[cy0:cy1, cx0:cx1], 0, 255).astype(np.uint8))
c.resize((c.width * 6, c.height * 6), Image.NEAREST).save(os.path.join(EV, "q5_snow_gm1zone_6x.png"))
print("\nsaved q5_snow_gm1zone_6x.png")
