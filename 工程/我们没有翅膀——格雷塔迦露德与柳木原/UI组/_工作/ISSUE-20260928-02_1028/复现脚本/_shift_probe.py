# -*- coding: utf-8 -*-
r"""_shift_probe.py —— 内移偏移量标定：ramp(shift) 在 outpaint 与 tonematch 上的分布/残留计数。

只读 outpaint\ 与 outpaint_tonematch\。
"""
import sys, os, csv
WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
import numpy as np
from PIL import Image

ROWS = list(csv.DictReader(open(os.path.join(ISSUE_DIR, "质量轴.tsv"), encoding="utf-8"), delimiter="\t"))
SHIFTS = [0, 2, 4, 6, 8, 10, 12, 16]
HALF = 8


def ramp_shifted(cm, cmc, xl, xr, sh):
    """cm=(1920,) 灰度列均值; cmc=(3,1920) 通道列均值。返回灰度 max 两侧 / 通道 max 两侧。"""
    W = len(cm)
    g = 0.0
    c = 0.0
    for a, b, r0, r1 in ((0, HALF, xl + sh, xl + sh + HALF),
                         (W - HALF, W, xr - sh - HALF, xr - sh)):
        g = max(g, abs(float(cm[a:b].mean() - cm[r0:r1].mean())))
        for k in range(3):
            c = max(c, abs(float(cmc[k, a:b].mean() - cmc[k, r0:r1].mean())))
    return g, c


def cols(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    cmc = np.stack([a[:, :, k].mean(axis=0) for k in range(3)])
    cm = 0.299 * cmc[0] + 0.587 * cmc[1] + 0.114 * cmc[2]
    return cm, cmc


def main():
    tm_dir = os.path.join(ISSUE_DIR, "outpaint_tonematch")
    res = {sh: {"o": [], "t": []} for sh in SHIFTS}
    tc = {sh: {"o": [], "t": []} for sh in SHIFTS}
    for i, r in enumerate(ROWS):
        nm = r["统一名"]
        xl, xr = int(r["xl"]), int(r["xr"])
        po = os.path.join(ISSUE_DIR, "outpaint", nm)
        if not os.path.exists(po):
            continue
        cm, cmc = cols(po)
        for sh in SHIFTS:
            g, c = ramp_shifted(cm, cmc, xl, xr, sh)
            res[sh]["o"].append(g)
            tc[sh]["o"].append(c)
        pt = os.path.join(tm_dir, nm)
        if os.path.exists(pt):
            cm, cmc = cols(pt)
            for sh in SHIFTS:
                g, c = ramp_shifted(cm, cmc, xl, xr, sh)
                res[sh]["t"].append(g)
                tc[sh]["t"].append(c)
        if (i + 1) % 160 == 0:
            print("  %d/%d" % (i + 1, len(ROWS)), flush=True)
    n_tm = len(res[0]["t"])
    print("n_outpaint=%d n_tonematch=%d" % (len(res[0]["o"]), n_tm))
    print("%-6s | %-28s | %-28s" % ("shift", "outpaint(640) 灰度/通道 >=15 />=25", "tonematch(%d) 灰度/通道" % n_tm))
    for sh in SHIFTS:
        o = np.array(res[sh]["o"]); oc = np.array(tc[sh]["o"])
        t = np.array(res[sh]["t"]); tcc = np.array(tc[sh]["t"])
        print("  %2d   | p50 %5.2f max %6.2f | >=15 %3d >=25 %3d | >=15 %3d | "
              "p50 %5.2f max %6.2f | >=15 %3d(%.1f%%) >=25 %3d | >=15 %3d"
              % (sh, np.median(o), o.max(), int((o >= 15).sum()), int((o >= 25).sum()),
                 int((oc >= 15).sum()),
                 np.median(t), t.max(), int((t >= 15).sum()), 100.0 * (t >= 15).mean(),
                 int((t >= 25).sum()), int((tcc >= 15).sum())))
    # 哪些件在 shift=10 上对 tonematch 残留 >=15
    names = [r["统一名"] for r in ROWS if os.path.exists(os.path.join(tm_dir, r["统一名"]))]
    for sh in (0, 10):
        vals = {}
        for r in ROWS:
            nm = r["统一名"]
            pt = os.path.join(tm_dir, nm)
            if not os.path.exists(pt):
                continue
            cm, cmc = cols(pt)
            g, c = ramp_shifted(cm, cmc, int(r["xl"]), int(r["xr"]), sh)
            vals[nm] = g
        bad = sorted([(v, k) for k, v in vals.items() if v >= 15], reverse=True)
        print("shift=%2d tonematch 残留>=15: %d 件 -> %s" % (sh, len(bad),
              ", ".join("%s(%.1f)" % (k, v) for v, k in bad[:40])))


if __name__ == "__main__":
    main()
