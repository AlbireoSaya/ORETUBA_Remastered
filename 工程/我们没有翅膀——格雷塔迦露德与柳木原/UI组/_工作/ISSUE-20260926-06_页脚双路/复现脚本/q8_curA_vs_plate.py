# -*- coding: utf-8 -*-
r"""q8 · 现 A 输出 vs 精确背景板：定位 v1 的全部残留（图标被削/辉光残尾/雪晶丢失）"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
EV = os.path.join(WORK, "_证据", "q_plate"); os.makedirs(EV, exist_ok=True)
BX0, BX1, BY0, BY1 = 850, 1910, 930, 1088
FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[BY0:BY1, BX0:BX1, :3]


B = np.stack([band(n) for n in ORDER])
spread = (B.max(axis=0) - B.min(axis=0)).max(axis=2)
allsame = spread < 0.5
bg = B[ORDER.index("otv_mv_bg.png")].copy()
bg[:, 1556 - BX0:] = np.median(B, axis=0)[:, 1556 - BX0:]
bgvalid = np.ones(allsame.shape, bool); bgvalid[:, 1556 - BX0:] = allsame[:, 1556 - BX0:]

# 末「无字」蒙版：任意屏在该像素无 ink 即有效（用 ink=强蓝膨胀近似，保守）
strong_any = np.zeros(allsame.shape, bool)
for i in range(7):
    br = B[i][:, :, 2] - B[i][:, :, 0]
    strong_any |= (br > 20)

for n in ORDER:
    a_raw = np.asarray(Image.open(os.path.join(OUT, n.replace(".png", "") + "_A_程序化.png")).convert("RGB")).astype(np.float32)
    assert a_raw.shape[:2] == (FY1 - FY0, FX1 - FX0), a_raw.shape
    a = np.full(bg.shape, 255.0, np.float32)
    a[FY0 - BY0:FY1 - BY0, FX0 - BX0:FX1 - BX0] = a_raw
    d = np.abs(a - bg).max(axis=2)
    dd = np.where(bgvalid, d, 0)
    print("=" * 78)
    print(n, " vs plate: max=%.0f  px(d>3)=%d  px(d>10)=%d" %
          (dd.max(), int((dd > 3).sum()), int((dd > 10).sum())))
    # 残余按 x 段统计
    for lo, hi in [(850, 970), (970, 1010), (1010, 1100), (1100, 1300), (1300, 1430),
                   (1430, 1560), (1560, 1600), (1600, 1700), (1700, 1740), (1740, 1900)]:
        seg = dd[:, lo - BX0:hi - BX0]
        if seg.size:
            print("   x%4d-%4d  max=%6.1f  px>3=%5d  px>10=%5d" %
                  (lo, hi, seg.max(), int((seg > 3).sum()), int((seg > 10).sum())))
# 图标区特写（gm_bg1 长项图标 + save 返回图标）8x
for tag, n, (x0, y0, x1, y1) in [
        ("gm1_icon", "otv_gm_bg1.png", (960, 975, 1050, 1045)),
        ("gm1_snow", "otv_gm_bg1.png", (1000, 960, 1130, 1045))]:
    o = np.clip(band(n), 0, 255).astype(np.uint8)
    a = np.asarray(Image.open(os.path.join(OUT, n.replace(".png", "") + "_A_程序化.png")).convert("RGB"))
    ai = Image.fromarray(a).resize((1024, 148), Image.LANCZOS)
    # 拼接 原/板/现A
    p = np.clip(bg, 0, 255).astype(np.uint8)
    rows = []
    for src_, lbl in [(o, "orig"), (p, "plate")]:
        c = src_[y0 - BY0:y1 - BY0, x0 - BX0:x1 - BX0]
        c = Image.fromarray(c).resize((c.shape[1] * 6, c.shape[0] * 6), Image.NEAREST)
        rows.append(c)
    c = np.asarray(ai)[y0 - FY0:y1 - FY0, x0 - FX0:x1 - FX0]
    rows.append(Image.fromarray(c).resize((c.shape[1] * 6, c.shape[0] * 6), Image.NEAREST))
    Wt = max(r.width for r in rows); Ht = sum(r.height for r in rows) + 12
    sheet = Image.new("RGB", (Wt, Ht), (255, 255, 255))
    yy = 0
    for r in rows:
        sheet.paste(r, (0, yy)); yy += r.height + 6
    sheet.save(os.path.join(EV, "q8_%s_orig_plate_A.png" % tag))
print("\nsaved q8_*_orig_plate_A.png (上=orig 中=plate 下=现A)")
