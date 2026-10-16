# -*- coding: utf-8 -*-
r"""q7 · 提高阈值，分离「雪晶笔画」与「背景渐变」；并给出各件窗内雪晶量"""
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


B = np.stack([band(n) for n in ORDER])
spread = (B.max(axis=0) - B.min(axis=0)).max(axis=2)
allsame = spread < 0.5
bg = B[ORDER.index("otv_mv_bg.png")].copy()
bg[:, 1556 - BX0:] = np.median(B, axis=0)[:, 1556 - BX0:]
bgvalid = np.ones(allsame.shape, bool); bgvalid[:, 1556 - BX0:] = allsame[:, 1556 - BX0:]
H, W = allsame.shape

# 雪晶本体：在长项区 x1002-1095 y960-1025 采样其 b-r 分布
sub = bg[960 - BY0:1026 - BY0, 1000 - BX0:1096 - BX0]
sbr = sub[:, :, 2] - sub[:, :, 0]
slum = sub.mean(axis=2)
print("雪晶区 x1000-1096 y960-1026 b-r 分布:")
for lo, hi in [(6, 12), (12, 20), (20, 30), (30, 45), (45, 60), (60, 999)]:
    m = (sbr > lo) & (sbr <= hi)
    if m.sum():
        print("   (%3d,%4d] n=%5d  mean b-r=%5.1f lum=%6.1f  max b-r=%5.1f" %
              (lo, hi, m.sum(), sbr[m].mean(), slum[m].mean(), sbr[m].max()))
    else:
        print("   (%3d,%4d] none" % (lo, hi))

# 雪晶笔画判定阈值
print("\n雪晶笔画判定：b-r>20")
for thr in (15, 20, 25, 30):
    deco = bgvalid & ((bg[:, :, 2] - bg[:, :, 0]) > thr) & (bg.mean(axis=2) < 250)
    print("  thr>%d 全带装饰 px=%d" % (thr, int(deco.sum())))
    if thr == 20:
        # 连通域
        parent = np.arange(H * W)
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        def uni(a, b):
            ra, rb = find(a), find(b)
            if ra != rb: parent[ra] = rb
        idx = np.flatnonzero(deco.ravel())
        for i in idx:
            r, c = divmod(int(i), W)
            for dr, dc in ((-1, 0), (0, -1), (-1, -1), (-1, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < H and 0 <= cc < W and deco[rr, cc]:
                    uni(i, rr * W + cc)
        from collections import defaultdict
        g = defaultdict(list)
        for i in idx: g[find(int(i))].append(int(i))
        comps = sorted(g.values(), key=len, reverse=True)
        wins = {}
        for n in ORDER:
            m = np.zeros((H, W), bool)
            for w in bbox[n]:
                m[max(0, w["y0"] - 5 - BY0):w["y1"] + 6 - BY0, w["x0"] - BX0:w["x1"] + 7 - BX0] = True
            wins[n] = m
        print("  连通域:")
        for v in comps[:10]:
            if len(v) < 15: break
            rs, cs = np.divmod(np.array(v), W)
            hit = [n.replace("otv_", "").replace(".png", "") for n in ORDER if wins[n][rs, cs].any()]
            print("    n=%6d x%4d-%4d y%4d-%4d  窗内相交: %s" %
                  (len(v), cs.min() + BX0, cs.max() + BX0, rs.min() + BY0, rs.max() + BY0,
                   ",".join(hit) if hit else "无"))
        print("  逐件窗内雪晶 px:")
        for n in ORDER:
            tot = 0
            for v in comps:
                rs, cs = np.divmod(np.array(v), W)
                tot += int(wins[n][rs, cs].sum())
            print("    %-22s %6d" % (n, tot))
        vis = np.clip(bg, 0, 255).astype(np.uint8).copy()
        vis[deco] = (0, 150, 50)
        Image.fromarray(vis[:, 120:760]).resize((640 * 3, (BY1 - BY0) * 3), Image.NEAREST).save(
            os.path.join(EV, "q7_deco20_left_3x.png"))
        print("  saved q7_deco20_left_3x.png")
