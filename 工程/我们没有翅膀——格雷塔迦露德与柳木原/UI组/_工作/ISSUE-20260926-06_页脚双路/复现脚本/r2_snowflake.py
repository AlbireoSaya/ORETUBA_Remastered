# -*- coding: utf-8 -*-
r"""r2 · 雪晶掩码（连通域）：底板上的「局部高对比淡蓝装饰」
判定：br=plate(b-r) 减去 r=20 盒模糊的局部底 → br_local_hi = br - blur(br) > 3
      且 br>=5 且 lum<=253；再做 8 连通域，去掉 area<12 的碎片。
输出：_证据\r_plate\snowflake_mask.npy + 可视化 snowflake_mask.png + 连通域台账
"""
import sys, os
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
EV = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路", "_证据", "r_plate")
plate = np.load(os.path.join(EV, "plate.npy")).astype(np.float32)
H, W = plate.shape[:2]
br = plate[:, :, 2] - plate[:, :, 0]
lum = plate.mean(axis=2)
loc = np.asarray(Image.fromarray(np.clip(br + 30, 0, 255).astype(np.uint8)).filter(
    ImageFilter.BoxBlur(20)), np.float32) - 30.0
hi = br - loc
valid0 = np.load(os.path.join(EV, "plate_valid.npy"))
m = (hi > 3) & (br >= 5) & (lum <= 253) & valid0


def components(mask):
    lab = np.zeros(mask.shape, np.int32)
    comps = []
    ys, xs = np.nonzero(mask)
    unvisited = mask.copy()
    cur = 0
    for y0, x0 in zip(ys, xs):
        if not unvisited[y0, x0]:
            continue
        cur += 1
        stack = [(y0, x0)]
        unvisited[y0, x0] = False
        pix = []
        while stack:
            y, x = stack.pop()
            pix.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and unvisited[ny, nx]:
                        unvisited[ny, nx] = False
                        stack.append((ny, nx))
        a = np.array(pix)
        comps.append({"n": len(pix), "y0": int(a[:, 0].min()) + 930, "y1": int(a[:, 0].max()) + 930,
                      "x0": int(a[:, 1].min()) + 850, "x1": int(a[:, 1].max()) + 850, "pix": pix})
    return comps


comps = components(m)
comps.sort(key=lambda c: -c["n"])
print("8连通域数 =", len(comps))
keep = [c for c in comps if c["n"] >= 12]
print("area>=12 的域数 =", len(keep), " 总像素 =", sum(c["n"] for c in keep))
for c in keep[:25]:
    print("  area=%6d  x%4d-%4d y%4d-%4d" % (c["n"], c["x0"], c["x1"], c["y0"], c["y1"]))
sm = np.zeros(m.shape, bool)
for c in keep:
    for (y, x) in c["pix"]:
        sm[y, x] = True
np.save(os.path.join(EV, "snowflake_mask.npy"), sm)
vis = np.clip(plate, 0, 255).astype(np.uint8).copy()
vis[sm] = (255, 0, 0)
Image.fromarray(vis[:, 900 - 850:1560 - 850]).resize(
    ((1560 - 900) * 2, H * 2), Image.NEAREST).save(os.path.join(EV, "snowflake_mask_2x.png"))
Image.fromarray(vis).save(os.path.join(EV, "snowflake_mask.png"))
print("saved snowflake_mask")
