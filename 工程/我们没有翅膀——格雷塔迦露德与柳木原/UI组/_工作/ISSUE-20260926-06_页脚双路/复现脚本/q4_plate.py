# -*- coding: utf-8 -*-
r"""q4 · 跨屏背景底板（plate）：
7 件页脚带背景逐像素相同（q3 已验证 max diff 0），故对同一像素取「各屏中位」即真背景；
仅当 7 屏在同像素都有字时底板无效（= 決定/戻る/選択 列）。
输出：_证据/q_plate/{plate.png, valid.png} + 各屏 glyph 足迹统计 + 雪晶连通域普查
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据", "q_plate"); os.makedirs(EV, exist_ok=True)
BX0, BX1, BY0, BY1 = 850, 1910, 930, 1088
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[BY0:BY1, BX0:BX1, :3]


B = np.stack([band(n) for n in ORDER])          # (7,H,W,3)
H, W = B.shape[1], B.shape[2]
print("band", B.shape)

# 7 屏在该像素的极差；=0 表示全屏一致 → 该像素必为背景（无字）
spread = B.max(axis=0) - B.min(axis=0)
allsame = spread.max(axis=2) < 0.5
print("全 7 屏一致像素占比 = %.1f%%" % (100.0 * allsame.sum() / allsame.size))

plate = np.median(B, axis=0)
# valid = 至少 3 屏在极差<0.5 的同一值上… 更实用：中位即背景（≥4 屏一致时必成立）
nb = (spread.max(axis=2) < 0.5).sum(axis=0)     # 每像素有 7 - (#离群) ...
# 直接算法：对每像素统计「与中位差<=0.5 的屏数」，>=4 即中位=背景
agree = (np.abs(B - plate[None]).max(axis=3) <= 0.5).sum(axis=0)
valid = agree >= 4
print("plate 有效像素占比 = %.1f%%" % (100.0 * valid.sum() / valid.size))

# 无效区分布
inv = ~valid
print("无效区 x 范围:", end=" ")
xs = np.flatnonzero(inv.any(axis=0))
if len(xs): print("%d-%d" % (xs.min() + BX0, xs.max() + BX0))
else: print("无")

# 各屏 glyph 足迹 = |screen - plate| > 2（仅 plate 有效处）
for i, n in enumerate(ORDER):
    d = np.abs(B[i] - plate).max(axis=2)
    m = (d > 2) & valid
    ys, xs2 = np.nonzero(m)
    extra = ""
    if len(xs2):
        # 落在 plate 无效区内的字素（无法用底板恢复）
        m2 = (d > 2) & (~valid)
        extra = "  [底板无效区字素 px=%d]" % int(m2.sum())
    print("  %-24s glyph px=%6d  bbox x%d-%d y%d-%d%s" %
          (n, int(m.sum()), xs2.min() + BX0 if len(xs2) else 0, xs2.max() + BX0 if len(xs2) else 0,
           ys.min() + BY0 if len(ys) else 0, ys.max() + BY0 if len(ys) else 0, extra))

# 雪晶普查：底板上的淡蓝装饰（plate 有效区，且离任何屏幕字素都远）
pl_br = plate[:, :, 2] - plate[:, :, 0]
deco = (pl_br > 8) & valid
lo = np.array([255, 255, 255], np.float32)
print("\n底板上淡蓝装饰 (b-r>8) px=%d" % int(deco.sum()))

Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).save(os.path.join(EV, "plate.png"))
vis = np.clip(plate, 0, 255).astype(np.uint8).copy()
vis[~valid] = (255, 0, 0)
Image.fromarray(vis).save(os.path.join(EV, "plate_validmask.png"))
# 底板长项区放大
c = Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)[45:118, 150:700])
c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(os.path.join(EV, "plate_longzone_4x.png"))
print("saved plate.png / plate_validmask.png / plate_longzone_4x.png")
np.save(os.path.join(EV, "plate.npy"), plate)
np.save(os.path.join(EV, "valid.npy"), valid)
