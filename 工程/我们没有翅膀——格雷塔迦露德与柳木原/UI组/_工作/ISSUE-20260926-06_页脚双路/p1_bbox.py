# -*- coding: utf-8 -*-
r"""p1 · 页脚文字实测 bbox：蓝饱和度掩码 → 列聚类 → 词/图标分界
输出：_证据/footer_bbox.json + footer_zoom.png（3× 放大）+ 每件裁片
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据"); os.makedirs(EV, exist_ok=True)

NAMES = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png",
         "otv_bklog.png", "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]

# 页脚搜索区（@2×）：x 860..1920（右缘留 20），y 960..1070
SX0, SY0, SX1, SY1 = 860, 960, 1900, 1070
BTH = 40          # 蓝饱和度阈值 b - r
COLGAP = 14       # 词间最小列空隙（@2×）
MINW = 6          # 有效游程最小宽


def bluemask(a):
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    lum = (r + g + b) / 3.0
    return ((b - r) > BTH) & (lum < 246)


def runs1d(v, min_len):
    idx = np.flatnonzero(v)
    if len(idx) == 0:
        return []
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [(int(g[0]), int(g[-1])) for g in groups if g[-1] - g[0] + 1 >= min_len]


def measure(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    reg = a[SY0:SY1, SX0:SX1]
    m = bluemask(reg)
    colp = m.sum(axis=0)
    # 列聚类：空隙 > COLGAP 合并（先取列游程）
    cr = runs1d(colp > 0, 1)
    words = []
    for (c0, c1) in cr:
        if words and c0 - words[-1][1] - 1 <= COLGAP:
            words[-1][1] = c1
        else:
            words.append([c0, c1])
    out = []
    for (c0, c1) in words:
        if c1 - c0 + 1 < MINW:
            continue
        sub = m[:, c0:c1 + 1]
        rows = np.flatnonzero(sub.any(axis=1))
        if len(rows) == 0:
            continue
        r0, r1 = int(rows[0]), int(rows[-1])
        # 在该词内再找列空隙（≥10px）以分出图标 vs 文字
        inner = runs1d(sub.any(axis=0), 1)
        gaps = []
        for i in range(len(inner) - 1):
            g = inner[i + 1][0] - inner[i][1] - 1
            if g >= 10:
                gaps.append((int(inner[i][1]), int(inner[i + 1][0]), g))
        out.append({
            "x0": int(c0 + SX0), "x1": int(c1 + SX0),
            "y0": int(r0 + SY0), "y1": int(r1 + SY0),
            "w": int(c1 - c0 + 1), "h": int(r1 - r0 + 1),
            "gaps": [[g[0] + SX0, g[1] + SX0, g[2]] for g in gaps],
            "px": int(sub.sum()),
        })
    # 视觉证据：3× 放大 + 框
    z = 3
    crop = im.crop((SX0, SY0, SX1, SY1)).convert("RGB")
    big = crop.resize((crop.width * z, crop.height * z), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for w in out:
        d.rectangle([(w["x0"] - SX0) * z, (w["y0"] - SY0) * z,
                     (w["x1"] - SX0 + 1) * z - 1, (w["y1"] - SY0 + 1) * z - 1],
                    outline=(220, 30, 30), width=2)
    big.save(os.path.join(EV, "zoom_" + name.replace(".png", "") + ".png"))
    return out


if __name__ == "__main__":
    res = {}
    for n in NAMES:
        r = measure(n)
        res[n] = r
        print("=" * 78)
        print(n)
        for w in r:
            print("  x %4d-%4d  y %4d-%4d  w %3d h %3d  px %5d  gaps %s"
                  % (w["x0"], w["x1"], w["y0"], w["y1"], w["w"], w["h"], w["px"], w["gaps"]))
    with open(os.path.join(WORK, "footer_bbox.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("\nwrote", os.path.join(WORK, "footer_bbox.json"))
