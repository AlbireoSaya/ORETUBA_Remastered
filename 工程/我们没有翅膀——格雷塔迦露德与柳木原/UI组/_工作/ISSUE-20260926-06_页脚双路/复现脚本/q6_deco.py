# -*- coding: utf-8 -*-
r"""q6 · 页脚带「背景装饰（雪晶）」普查：
背景取自 mv_bg（x<=1555 全干净）+ 7 屏全同像素（x>=1556）；
装饰 = 背景上 b-r>6 的淡蓝结构；统计其连通域，并与各件文字窗求交。
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
ICON_W = 47


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[BY0:BY1, BX0:BX1, :3]


B = np.stack([band(n) for n in ORDER])
spread = (B.max(axis=0) - B.min(axis=0)).max(axis=2)
allsame = spread < 0.5
bg = B[ORDER.index("otv_mv_bg.png")].copy()
bg[:, 1556 - BX0:] = np.median(B, axis=0)[:, 1556 - BX0:]
bgvalid = np.ones(allsame.shape, bool)
bgvalid[:, 1556 - BX0:] = allsame[:, 1556 - BX0:]
print("背景有效像素占比 %.1f%%" % (100.0 * bgvalid.sum() / bgvalid.size))

br = bg[:, :, 2] - bg[:, :, 0]
lum = bg.mean(axis=2)
deco = bgvalid & (br > 6) & (lum < 252)
print("装饰像素 px=%d" % int(deco.sum()))

# 连通域
H, W = deco.shape
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

# 文字窗（含图标）
wins = {}
for n in ORDER:
    m = np.zeros((H, W), bool)
    for w in bbox[n]:
        m[max(0, w["y0"] - 5 - BY0):w["y1"] + 6 - BY0, w["x0"] - BX0:w["x1"] + 7 - BX0] = True
    wins[n] = m

print("\n装饰连通域（前 12，n>=20）:")
for v in comps[:12]:
    if len(v) < 20: break
    rs, cs = np.divmod(np.array(v), W)
    x0, x1, y0, y1 = cs.min() + BX0, cs.max() + BX0, rs.min() + BY0, rs.max() + BY0
    hit = [n for n in ORDER if wins[n][rs, cs].any()]
    print("  n=%6d x%4d-%4d y%4d-%4d (w%3d h%3d)  与文字窗相交: %s" %
          (len(v), x0, x1, y0, y1, x1 - x0 + 1, y1 - y0 + 1, ",".join(hit) if hit else "无"))

# 逐件：文字窗内的装饰像素数（= 会被误擦的雪晶像素）
print("\n逐件「文字窗内装饰像素」= 现 A 路会一并擦掉的雪晶量:")
for n in ORDER:
    tot = 0
    for v in comps:
        rs, cs = np.divmod(np.array(v), W)
        tot += int(wins[n][rs, cs].sum())
    print("  %-24s %6d px" % (n, tot))

# 图证：整带装饰可视化
vis = np.clip(bg, 0, 255).astype(np.uint8).copy()
vis[deco] = (0, 160, 60)
vis[~bgvalid] = (200, 200, 200)
Image.fromarray(vis).save(os.path.join(EV, "q6_deco_map.png"))
Image.fromarray(vis[:, 100:750]).resize((650 * 3, (BY1 - BY0) * 3), Image.NEAREST).save(
    os.path.join(EV, "q6_deco_left_3x.png"))
print("saved q6_deco_map.png / q6_deco_left_3x.png")
