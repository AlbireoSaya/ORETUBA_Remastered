# -*- coding: utf-8 -*-
r"""
make_profiles.py —— 色调漂移的「列均值剖面」证据（ISSUE-20260928-02 · 补充证据）

为什么需要
    sr 族白底片尾卡 81 件的内容是**纯白平铺**，64 列宽的缝条里几乎全白，
    看不出「全屏边缘露 12–35 级灰晕」——那是一个**跨全宽的低频色调漂移**，不是局部缝结构。
    本脚本把「逐列灰度均值」画成剖面图：
        ① 全宽列均值（纵轴=列 0..1919，横轴=灰度 0..255）
        ② 左扩展区放大（纵轴=列 0..xl，横轴=偏差(相对内容带均值)）
        ③ 右扩展区放大（纵轴=列 xr-1..1919，同横轴）
    灰线 = outpaint 原样，蓝线 = 色调匹配后，红横线 = 内容区边界（缝）。
    ⇒ ② ③ 两格直接读出「原样在扩展区偏离内容带多少级、修正后是否贴合」。

产物
    证据\色调剖面\<统一名>_剖面.png      逐件（默认：全部 sr 族 + |ramp| 最大的 12 件）
    证据\色调剖面\_总表.png              3 列拼图
    证据\色调剖面\索引.txt               逐件 原/改后 |ramp| 与 mL4/mRGB4

用法
    python make_profiles.py
    python make_profiles.py --names sr0_01.png,hiy65.png
"""
import sys, os, csv, argparse

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from quality_axes import AXES_TSV

OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
TONEMATCH = os.path.join(ISSUE_DIR, "outpaint_tonematch")
OUT_DIR = os.path.join(ISSUE_DIR, "证据", "色调剖面")

W_PX, H_PX = 680, 372
PAD_T, PAD_B = 18, 18


def font(sz=11):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def profile(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    g = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    return g.mean(axis=0)


def panel_abs(d, f, x0, w, h, cm_b, cm_a, xl, xr):
    """① 全宽绝对列均值。"""
    def X(v):
        return x0 + int(round(np.clip(v, 0, 255) / 255.0 * w))

    def Y(c):
        return PAD_T + int(round(c / 1919.0 * h))
    for v in range(0, 256, 64):
        d.line([(X(v), PAD_T), (X(v), PAD_T + h)], fill=(52, 52, 52), width=1)
        d.text((X(v) - 9, PAD_T + h + 3), str(v), fill=(150, 150, 150), font=f)
    for c in range(0, 1920, 240):
        d.line([(x0, Y(c)), (x0 + w, Y(c))], fill=(38, 38, 38), width=1)
        d.text((2, Y(c) - 5), str(c), fill=(140, 140, 140), font=f)
    for c in (xl, xr):
        d.line([(x0, Y(c)), (x0 + w, Y(c))], fill=(205, 60, 60), width=1)
    for cm, col in ((cm_b, (175, 175, 175)), (cm_a, (85, 170, 255))):
        d.line([(X(cm[c]), Y(c)) for c in range(0, 1920, 2)], fill=col, width=1)
    d.text((x0, 3), "① 全宽列均值(0-255)  纵轴=列0-1919", fill=(160, 200, 160), font=f)


def panel_ext(d, f, x0, w, h, cm_b, cm_a, c0, c1, ref, label, seam_c):
    """② ③ 扩展区放大：纵轴=列区间，横轴=偏差(相对内容带均值)。"""
    n = max(c1 - c0, 2)

    def X(v):
        return x0 + int(round((float(np.clip(v, -40, 40)) + 40.0) / 80.0 * w))

    def Y(c):
        return PAD_T + int(round((c - c0) / float(n - 1) * h))
    for v in range(-40, 41, 10):
        d.line([(X(v), PAD_T), (X(v), PAD_T + h)], fill=(52, 52, 52), width=1)
        d.text((X(v) - 8, PAD_T + h + 3), str(v), fill=(150, 150, 150), font=f)
    d.line([(X(0), PAD_T), (X(0), PAD_T + h)], fill=(110, 110, 110), width=1)
    d.line([(x0, Y(seam_c)), (x0 + w, Y(seam_c))], fill=(205, 60, 60), width=1)
    for cm, col in ((cm_b, (175, 175, 175)), (cm_a, (85, 170, 255))):
        d.line([(X(cm[c] - ref), Y(c)) for c in range(c0, c1)], fill=col, width=1)
    d.text((x0, 3), label, fill=(160, 200, 160), font=f)
    d.text((x0 + 2, Y(seam_c) + 1), "←缝", fill=(205, 60, 60), font=f)


def draw_panel(cm_before, cm_after, xl, xr, name, ramp_b, ramp_a):
    im = Image.new("RGB", (W_PX, H_PX), (16, 16, 16))
    d = ImageDraw.Draw(im)
    f = font(11)
    h = H_PX - PAD_T - PAD_B
    w1, w23 = 240, 160
    panel_abs(d, f, 34, w1, h, cm_before, cm_after, xl, xr)
    ref = float(np.concatenate([cm_before[xl:xl + 8], cm_before[xr - 8:xr]]).mean())
    x2 = 34 + w1 + 40
    panel_ext(d, f, x2, w23, h, cm_before, cm_after, 0, xl + 1, ref,
              "② 左扩展区 纵轴=列0-%d" % xl, xl - 1)
    x3 = x2 + w23 + 40
    panel_ext(d, f, x3, w23, h, cm_before, cm_after, xr - 1, 1920, ref,
              "③ 右扩展区 纵轴=列%d-1919" % (xr - 1), xr)
    d.text((2, H_PX - 13),
           "%s  原|ramp|=%.1f 改后=%.1f  xl=%d xr=%d  内容带均值=%.1f  灰=outpaint原样 蓝=色调匹配"
           % (name, ramp_b, ramp_a, xl, xr, ref), fill=(240, 220, 120), font=f)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default=None)
    args = ap.parse_args()
    rows = list(csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t"))
    by = {r["统一名"]: r for r in rows}
    if args.names:
        names = [n.strip() for n in args.names.split(",")]
    else:
        sr = [r["统一名"] for r in rows if r["统一名"].startswith("sr")]
        top = [r["统一名"] for r in sorted(rows, key=lambda z: -float(z["ramp"]))[:12]
               if not r["统一名"].startswith("sr")]
        names = sr + top
    os.makedirs(OUT_DIR, exist_ok=True)
    after = {}
    cmp_tsv = os.path.join(ISSUE_DIR, "证据", "色调匹配_对照.tsv")
    if os.path.exists(cmp_tsv):
        for r in csv.DictReader(open(cmp_tsv, encoding="utf-8"), delimiter="\t"):
            after[r["统一名"]] = r.get("ramp_after", "")
    idx = ["色调剖面证据索引", "  统一名\t原|ramp|\t改后|ramp|\tmL4\tmRGB4\t有色调匹配产物"]
    for nm in names:
        r = by.get(nm)
        p0 = os.path.join(OUTPAINT, nm)
        p1 = os.path.join(TONEMATCH, nm)
        if r is None or not os.path.exists(p0):
            continue
        cm0 = profile(p0)
        cm1 = profile(p1) if os.path.exists(p1) else cm0
        xl, xr = int(r["xl"]), int(r["xr"])
        ra = after.get(nm) or r["ramp"]
        draw_panel(cm0, cm1, xl, xr, nm, float(r["ramp"]),
                   float(ra) if ra != "" else float(r["ramp"])).save(
            os.path.join(OUT_DIR, "%s_剖面.png" % os.path.splitext(nm)[0]))
        idx.append("  %s\t%s\t%s\t%s\t%s\t%s" % (nm, r["ramp"], ra, r["mL4"], r["mRGB4"],
                                                "有" if os.path.exists(p1) else "无"))
    cols = 3
    files = [f for f in sorted(os.listdir(OUT_DIR)) if f.endswith("_剖面.png")]
    sheet = Image.new("RGB", (W_PX * cols, H_PX * ((len(files) + cols - 1) // cols)), (8, 8, 8))
    for i, fn in enumerate(files):
        sheet.paste(Image.open(os.path.join(OUT_DIR, fn)), ((i % cols) * W_PX, (i // cols) * H_PX))
    sheet.save(os.path.join(OUT_DIR, "_总表.png"))
    open(os.path.join(OUT_DIR, "索引.txt"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    print("色调剖面 %d 件 -> %s" % (len(files), OUT_DIR))


if __name__ == "__main__":
    main()
