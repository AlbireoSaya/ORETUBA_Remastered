# -*- coding: utf-8 -*-
r"""G1e · 参照并排图：左 = 参照截图（月影魅像右端竖条）裁切，右 = 我方 12 枚 1:1。

参照标定（目视 + 亮度检测，见打印）：图标竖条 x∈[1358,1440]；圆底直径 ≈44px、pitch ≈57.5px。
把参照按 **圆底直径对齐**（×56/44 ≈ 1.273）后与我方 1:1 并排 —— 我方画布 64、圆径 56，
布局 pitch 为 73（=75×73 热区），56/73 = 0.767 ≈ 参照 44/57.5 = 0.765，故直径对齐即等价于 pitch 对齐。
输出 `参照并排_64.png`。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
_G = HERE
for _ in range(6):
    if os.path.isdir(os.path.join(_G, "krkr")) and os.path.isdir(os.path.join(_G, "layout")):
        break
    _G = os.path.dirname(_G)
UI = os.path.join(_G, "krkr", "assets", "ui")
REF = os.path.join(_G, "_工作", "M37_参照截图")

KEYS = ["lock", "save", "load", "qsave", "qload", "auto",
        "skip", "next", "prev", "log", "chart", "option"]

CROP = (1356, 52, 1442, 756)      # 参照图标竖条（目视标定）
REF_DISC = 44.0                   # 参照圆底直径（目视标定）
OUR_DISC = 56.0


def detect_centers(a):
    """在竖条内按「白色圆底」检测 12 个行中心：取 band 内最大亮度 > 阈值的行，聚簇取中心。"""
    lum = a.mean(axis=2)
    rowmax = lum.max(axis=1)
    thr = rowmax.max() * 0.86
    nz = np.nonzero(rowmax > thr)[0]
    if len(nz) == 0:
        return []
    cl, s, prev = [], nz[0], nz[0]
    for v in nz[1:]:
        if v - prev > 4:
            cl.append((s, prev)); s = v
        prev = v
    cl.append((s, prev))
    return [(a0 + b0) / 2.0 for a0, b0 in cl]


def main():
    f = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 19)
    src = Image.open(os.path.join(REF, "参照_月影魅像_右端竖条_悬停自动模式.png")).convert("RGB")
    strip = src.crop(CROP)
    cs = detect_centers(np.array(strip))
    print("参照裁切 %s ｜ 检测到 %d 个白底行中心 %s" % (strip.size, len(cs), [round(c, 1) for c in cs]))
    if len(cs) >= 2:
        print("  → 平均 pitch = %.1f px（首 %.1f / 末 %.1f）" % ((cs[-1] - cs[0]) / (len(cs) - 1), cs[0], cs[-1]))

    k = OUR_DISC / REF_DISC
    strip2 = strip.resize((int(round(strip.size[0] * k)), int(round(strip.size[1] * k))), Image.LANCZOS)
    print("参照按圆底直径对齐缩放 ×%.3f → %s" % (k, strip2.size))

    pad, gap, col = 18, 16, 64
    W = pad * 2 + strip2.size[0] + gap + 40 + col * 2 + 8 + 120
    H = pad * 2 + 52 + max(strip2.size[1], 12 * 70)
    out = Image.new("RGB", (W, H), (150, 154, 160))
    d = ImageDraw.Draw(out)
    d.text((pad, pad), "参照", fill=(12, 12, 12), font=f)
    out.paste(strip2, (pad, pad + 52))
    xo = pad + strip2.size[0] + gap + 30
    out.paste(Image.new("RGB", (W - xo - pad, H - pad - 52), (233, 241, 251)), (xo, pad + 52))
    d.text((xo, pad), "我方 常态|悬停", fill=(12, 12, 12), font=f)
    for i, key in enumerate(KEYS):
        y = pad + 52 + i * 70
        for si, st in enumerate(("", "_on")):
            im = Image.open(os.path.join(UI, "x_ui_qbicon_%s%s.png" % (key, st))).convert("RGBA")
            out.paste(im, (xo + 10 + si * (col + 8), y), im)
    p = os.path.join(EV, "参照并排_64.png")
    out.save(p)
    print("→ %s %s" % (p, out.size))


if __name__ == "__main__":
    main()
