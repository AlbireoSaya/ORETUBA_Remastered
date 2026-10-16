# -*- coding: utf-8 -*-
r"""q3 · 背景一致性检验：7 件的页脚背景是否为同一张（雪晶位置一致）？
在「全部件都无文字」的区域取样做逐像素比对。
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)).astype(np.float32)[:, :, :3]


B = {n: band(n) for n in ORDER}
print("sizes:", {n: B[n].shape for n in ORDER})

# 全件无文字区：y 940..1088, 逐列判断是否有任何件在该列有词
cols_busy = np.zeros(1920, bool)
rows_busy = np.zeros(1318, bool)
for n in ORDER:
    for w in bbox[n]:
        cols_busy[w["x0"] - 60:w["x1"] + 62] = True
        rows_busy[w["y0"] - 40:w["y1"] + 42] = True
free_cols = ~cols_busy
print("无文字列数(全带):", int(free_cols[850:1910].sum()))

# 取一段确定干净的区：x 880..960（各件都空），y 1000..1080
reg = (slice(995, 1085), slice(885, 965))
base = B["otv_mv_bg.png"][reg]
print("\n以 otv_mv_bg 为基准，干净区 x885-965 y995-1085 逐件最大差 / 均值差:")
for n in ORDER:
    d = np.abs(B[n][reg] - base)
    print("  %-24s max=%6.1f mean=%5.2f" % (n, d.max(), d.mean()))

# 再取 gm_bg1 长项左侧（x 971-1010 图标位）以外、且各件皆空的中段：x 1150-1250 y 950-980
reg2 = (slice(950, 982), slice(1150, 1252))
base2 = B["otv_mv_bg.png"][reg2]
print("\n干净区 x1150-1252 y950-982（长项上方，仅 gm_bg1 有字其下）:")
for n in ORDER:
    d = np.abs(B[n][reg2] - base2)
    print("  %-24s max=%6.1f mean=%5.2f  p99=%.1f" % (n, d.max(), d.mean(), np.percentile(d, 99)))

# 长项覆盖区 x1018-1505 y985-1035：各件差异（gm_bg1 与 干净件）
print("\n长项覆盖区 x1018-1505 y985-1035 相对 mv_bg 的差异（谁干净一看便知）:")
reg3 = (slice(982, 1040), slice(1015, 1510))
for n in ORDER:
    d = np.abs(B[n][reg3] - B["otv_mv_bg.png"][reg3])
    print("  %-24s mean=%6.2f  px(>12)=%6d" % (n, d.mean(), int((d.max(axis=2) > 12).sum())))

# 输出 mv_bg / quick_load / bklog 的长项区背景（供雪晶模板）
out = os.path.join(WORK, "_证据", "q_gm1"); os.makedirs(out, exist_ok=True)
for n in ["otv_mv_bg.png", "otv_quick_load_bg.png", "otv_bklog.png", "otv_gm_bg1.png"]:
    c = Image.fromarray(np.clip(B[n][975:1045, 1000:1520], 0, 255).astype(np.uint8))
    c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(
        os.path.join(out, "q3_%s_longzone.png" % n.replace(".png", "")))
print("\nsaved q3_*_longzone.png")
