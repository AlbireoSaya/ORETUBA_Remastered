# -*- coding: utf-8 -*-
r"""q2 · 页脚带内「蓝像素连通域」普查：区分 文字笔画/文字辉光 与 雪晶（装饰）
判据候选：
  glyph_strong = (b-r>55) & (lum<238)     强蓝描边 → 文字骨架
  pale         = (b-r>18) & (b-r<=55)     淡蓝 → 辉光尾 或 雪晶
输出：_证据/q_gm1/q2_comp_<件>.png（4x 上色）+ 控制台清单
"""
import sys, os
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据", "q_gm1"); os.makedirs(EV, exist_ok=True)
BX0, BX1, BY0, BY1 = 850, 1910, 930, 1088


def load(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    band = a[BY0:BY1, BX0:BX1]
    band = np.asarray(Image.alpha_composite(
        Image.new("RGBA", (BX1 - BX0, BY1 - BY0), (255, 255, 255, 255)),
        Image.fromarray(band.astype(np.uint8), "RGBA"))).astype(np.float32)[:, :, :3]
    return band


def label(mask):
    H, W = mask.shape
    parent = np.arange(H * W)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    def uni(x, y):
        rx, ry = find(x), find(y)
        if rx != ry: parent[rx] = ry

    idx = np.flatnonzero(mask.ravel())
    for i in idx:
        r, c = divmod(int(i), W)
        if r > 0 and mask[r - 1, c]: uni(i, i - W)
        if c > 0 and mask[r, c - 1]: uni(i, i - 1)
        if r > 0 and c > 0 and mask[r - 1, c - 1]: uni(i, i - W - 1)
        if r > 0 and c < W - 1 and mask[r - 1, c + 1]: uni(i, i - W + 1)
    from collections import defaultdict
    g = defaultdict(list)
    for i in idx: g[find(int(i))].append(int(i))
    out = []
    for v in g.values():
        rs = [i // W for i in v]; cs = [i % W for i in v]
        out.append({"n": len(v), "x0": min(cs), "x1": max(cs), "y0": min(rs), "y1": max(rs), "idx": v})
    out.sort(key=lambda d: -d["n"])
    return out


def run(name, show=14):
    band = load(name)
    br = band[:, :, 2] - band[:, :, 0]
    lum = band.mean(axis=2)
    strong = (br > 55) & (lum < 238)
    pale = (br > 18) & (br <= 55)
    print("=" * 84)
    print(name, " strong px=%d  pale px=%d" % (int(strong.sum()), int(pale.sum())))
    comps = label(pale)
    for c in comps[:show]:
        v = c["idx"]
        rs, cs = np.divmod(np.array(v), pale.shape[1])
        mr, mg, mb = band[rs, cs].mean(axis=0)
        print("  pale comp n=%6d  x%4d-%4d y%3d-%3d (w%3d h%3d) meanRGB=(%5.1f,%5.1f,%5.1f) lum=%5.1f" %
              (c["n"], c["x0"] + BX0, c["x1"] + BX0, c["y0"] + BY0, c["y1"] + BY0,
               c["x1"] - c["x0"] + 1, c["y1"] - c["y0"] + 1,
               float(mr), float(mg), float(mb), float(lum[rs, cs].mean())))
    # 上色图：强蓝=红，淡蓝=绿
    vis = np.clip(band, 0, 255).astype(np.uint8).copy()
    vis[strong] = (230, 40, 40)
    vis[pale] = (30, 170, 60)
    im = Image.fromarray(vis).resize(((BX1 - BX0) * 2, (BY1 - BY0) * 2), Image.NEAREST)
    im.save(os.path.join(EV, "q2_comp_" + name.replace(".png", "") + ".png"))
    return comps


if __name__ == "__main__":
    for n in ["otv_gm_bg1.png"]:
        run(n)
