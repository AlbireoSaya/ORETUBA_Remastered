# -*- coding: utf-8 -*-
r"""q1 · 原版 vs 现 A 路 逐件差异：定位被误擦的雪晶；并统计孤立雪晶的像素特征"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
EV = os.path.join(WORK, "_证据", "q_gm1"); os.makedirs(EV, exist_ok=True)
FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088

ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]

def orig_rgb(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(
        Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")).astype(np.float32)

for n in ORDER:
    o = orig_rgb(n)[FY0:FY1, FX0:FX1]
    a = np.asarray(Image.open(os.path.join(OUT, n.replace(".png", "") + "_A_程序化.png")).convert("RGB")).astype(np.float32)
    d = np.abs(o - a).max(axis=2)
    # 除字区外的显著差异（>12）— 即可能误擦的装饰
    er = d > 12
    lab = "?"
    print("=" * 76)
    print(n, "  差异>12 px=%d  最大差=%.0f" % (int(er.sum()), d.max()))
    # 找连通域（简单行扫描 + 4 邻域并查集）
    H, W = er.shape
    parent = np.arange(H * W)
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def uni(x, y):
        rx, ry = find(x), find(y)
        if rx != ry: parent[rx] = ry
    idx = np.flatnonzero(er.ravel())
    for i in idx:
        r, c = divmod(i, W)
        if r > 0 and er[r - 1, c]: uni(i, i - W)
        if c > 0 and er[r, c - 1]: uni(i, i - 1)
    from collections import defaultdict
    grp = defaultdict(list)
    for i in idx: grp[find(i)].append(i)
    comps = sorted(grp.values(), key=len, reverse=True)
    for g in comps[:6]:
        rs = [i // W for i in g]; cs = [i % W for i in g]
        print("   comp n=%5d  裁片 x%d-%d y%d-%d (@2x 实际 x%d-%d y%d-%d)" %
              (len(g), min(cs), max(cs), min(rs), max(rs),
               min(cs) + FX0, max(cs) + FX0, min(rs) + FY0, max(rs) + FY0))

# 孤立雪晶特征：gm_bg1 页脚带内、长项右侧 (1510-1580, 970-1010) 那片
a = orig_rgb("otv_gm_bg1.png")
for tag, (x0, y0, x1, y1) in {
        "snowA": (1508, 965, 1585, 1015),
        "snowB": (990, 965, 1085, 1000),
        "snowC": (1600, 1050, 1660, 1090)}.items():
    sub = a[y0:y1, x0:x1]
    br = sub[:, :, 2] - sub[:, :, 0]
    lum = sub.mean(axis=2)
    print("-" * 60); print(tag, (x0, y0, x1, y1))
    for lo, hi in [(10, 20), (20, 30), (30, 45), (45, 60), (60, 100), (100, 999)]:
        m = (br > lo) & (br <= hi)
        if m.sum():
            print("   b-r(%3d,%4d] n=%5d mean=(%6.1f,%6.1f,%6.1f) lum=%6.1f" %
                  (lo, hi, m.sum(), *sub[m].mean(axis=0), lum[m].mean()))
    # 该区 8x
    c = Image.fromarray(np.clip(sub, 0, 255).astype(np.uint8))
    c.resize((c.width * 8, c.height * 8), Image.NEAREST).save(os.path.join(EV, "q1_%s.png" % tag))
