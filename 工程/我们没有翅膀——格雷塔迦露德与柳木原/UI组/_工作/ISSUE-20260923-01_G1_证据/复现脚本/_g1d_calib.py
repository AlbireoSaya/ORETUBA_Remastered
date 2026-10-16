# -*- coding: utf-8 -*-
r"""G1d · 标定「圆底填充 / 环」的测量口径，使其复现 vision 子代理报出的现值。

vision 实测（本轮要改的基线）：常态圆底 #E5EFFB、常态环 #8CCEF9、悬停圆底 #D0EBFB、悬停环 #25C8F9。
本脚本用若干候选掩码量现有 64 件，挑出与 vision 数值最接近的口径，作为后续“实测色值自证”的统一定义。
"""
import glob, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_G = HERE
for _ in range(6):
    if os.path.isdir(os.path.join(_G, "krkr")) and os.path.isdir(os.path.join(_G, "layout")):
        break
    _G = os.path.dirname(_G)
UI = os.path.join(_G, "krkr", "assets", "ui")

YY, XX = np.mgrid[0:64, 0:64]
RG = np.sqrt((XX + 0.5 - 32.0) ** 2 + (YY + 0.5 - 32.0) ** 2)


def wcag_lum(rgb):
    c = np.asarray(rgb, dtype=float) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(a, b):
    la, lb = wcag_lum(a), wcag_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hexs(rgb):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in rgb)


BASE = (233, 241, 251)      # #E9F1FB 本作复刻屏冰蓝底

MASKS = {
    "A r<=20 & alpha>200": lambda a, al: (RG <= 20) & (al > 200),
    "B r<=20 & min>=200": lambda a, al: (RG <= 20) & (a.min(axis=-1) >= 200),
    "C r<=20 & min>=170": lambda a, al: (RG <= 20) & (a.min(axis=-1) >= 170),
    "D r<=24 & min>=150": lambda a, al: (RG <= 24) & (a.min(axis=-1) >= 150),
    "E r<=20 & lum>=235": lambda a, al: (RG <= 20) & (a.mean(axis=-1) >= 235),
}

print("vision 基线：常态圆底 #E5EFFB / 悬停圆底 #D0EBFB；常态环 #8CCEF9 / 悬停环 #25C8F9")
print("=" * 104)
for name, fn in MASKS.items():
    out = {}
    for st in ("off", "on"):
        vals = []
        for p in sorted(glob.glob(os.path.join(UI, "x_ui_qbicon_*%s.png" % ("" if st == "off" else "_on")))):
            im = Image.open(p).convert("RGBA")
            a = np.array(im).astype(float)
            al = a[..., 3]
            m = fn(a[..., :3], al)
            if m.sum() < 30:
                continue
            vals.append(a[..., :3][m].mean(axis=0))
        out[st] = np.mean(vals, axis=0)
    print("%-22s 常态 %s  悬停 %s   ｜ 常态底对比冰蓝屏底 %.3f:1"
          % (name, hexs(out["off"]), hexs(out["on"]), contrast(out["off"], BASE)))

print("=" * 104)
print("\n环峰值色（r∈[R_EDGE-5,R_EDGE] 内蓝度 B-R 最大者的实测色）")
for st in ("off", "on"):
    pk = []
    for p in sorted(glob.glob(os.path.join(UI, "x_ui_qbicon_*%s.png" % ("" if st == "off" else "_on")))):
        a = np.array(Image.open(p).convert("RGBA")).astype(float)
        al, px = a[..., 3], a[..., :3]
        rr = np.arange(23.0, 28.26, 0.25)
        best = None
        for r in rr:
            m = (RG >= r - 0.125) & (RG < r + 0.125) & (al > 200)
            if m.sum() < 6:
                continue
            br = float((px[..., 2][m] - px[..., 0][m]).mean())
            if best is None or br > best[0]:
                best = (br, tuple(px[m].mean(axis=0)), float(r))
        pk.append(best)
    br = np.mean([b[0] for b in pk])
    col = np.mean([b[1] for b in pk], axis=0)
    rad = np.mean([b[2] for b in pk])
    print("  %-4s 峰值色 %s  B-R=%.1f  r=%.2f  ｜ 对冰蓝屏底对比 %.3f:1"
          % (st, hexs(col), br, rad, contrast(col, BASE)))
