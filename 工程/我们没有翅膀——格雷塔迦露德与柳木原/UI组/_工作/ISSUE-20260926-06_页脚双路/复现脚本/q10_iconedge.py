# -*- coding: utf-8 -*-
r"""q10 · 图标右缘 / 文字左缘 定标：给 erase 区左界找安全位置
对每件每个词：用 br>20 列剖面找图标簇与文字簇，输出簇间空隙；并给出
d=|screen-plate| 在图标右缘附近的量级（判断左侧切边会不会留台阶）。
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
ICON_W = 47


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[930:1088, 850:1910, :3]


B = np.stack([band(n) for n in ORDER])
spread = (B.max(axis=0) - B.min(axis=0)).max(axis=2)
allsame = spread < 0.5
plate = B[ORDER.index("otv_mv_bg.png")].copy()
plate[:, 1556 - 850:] = np.median(B, axis=0)[:, 1556 - 850:]
ink_union = np.zeros(allsame.shape, bool)
for i in range(7):
    br = B[i][:, :, 2] - B[i][:, :, 0]
    ink_union |= br > 20


def runs(v, min_len=2):
    idx = np.flatnonzero(v)
    if len(idx) == 0: return []
    g = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [(int(a[0]), int(a[-1])) for a in g if a[-1] - a[0] + 1 >= min_len]


for n in ORDER:
    bi = ORDER.index(n)
    d = np.abs(B[bi] - plate).max(axis=2)
    print("=" * 86)
    print(n)
    for k, w in enumerate(bbox[n]):
        x0, y0, x1, y1 = w["x0"], w["y0"], w["x1"], w["y1"]
        sub = B[bi][y0 - 8 - 930:y1 + 9 - 930, x0 - 850:x1 + 8 - 850]
        br = sub[:, :, 2] - sub[:, :, 0]
        colp = (br > 20).any(axis=0)
        rr = runs(colp, 2)
        # 第一个簇（图标）右界 = 从第一个 run 起、run 间空隙 <=6 的连续块
        iend = rr[0][1] if rr else 0
        for i in range(1, len(rr)):
            if rr[i][0] - iend - 1 <= 6:
                iend = rr[i][1]
            else:
                break
        # 该簇之后的第一个大空隙
        gap_start = gap_end = None
        for i in range(len(rr)):
            if rr[i][0] > iend:
                gap_start, gap_end = iend, rr[i][0]
                break
        # 图标区尾部的 d 量级（沿 x）
        ds = d[y0 - 930:y1 - 930, x0 + iend - 850:x0 + iend + 24 - 850]
        dmax = ds.max(axis=0) if ds.size else np.zeros(0)
        print("  item%d word x%d-%d | 图标簇右界 x%d (簇=%s)" %
              (k + 1, x0, x1, x0 + iend, rr[:4]))
        if gap_start is not None:
            print("       图标后空隙 x%d..x%d (宽%d)；文字簇起 x%d" %
                  (x0 + gap_start, x0 + gap_end, gap_end - gap_start, x0 + gap_end))
        print("       d 沿 x 剖面(x=%d..%d): %s" %
              (x0 + iend, x0 + iend + 15, " ".join("%.0f" % v for v in dmax[:16])))
