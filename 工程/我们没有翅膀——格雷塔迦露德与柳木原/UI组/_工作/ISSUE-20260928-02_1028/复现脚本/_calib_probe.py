# -*- coding: utf-8 -*-
r"""_calib_probe.py —— 探测：为 v2 判据标定「单侧分带」与「参考带内移」口径。

只读 outpaint\。用法：
    python _calib_probe.py
    python _calib_probe.py --names yy_19.png,kob68.png
"""
import sys, os, csv, argparse
WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
import numpy as np
from PIL import Image
from quality_axes import out_seams, load_rgb, AXES_TSV

OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
NB = 6


def band_stats(rgb, xl, xr, shift):
    H, W, _ = rgb.shape
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    edges = [int(round(i * H / NB)) for i in range(NB + 1)]
    res = {}
    for tag, ext_sl, ref_sl in (
            ("L", slice(0, 8), slice(xl + shift, xl + shift + 8)),
            ("R", slice(W - 8, W), slice(xr - shift - 8, xr - shift))):
        e = rgb[:, ext_sl, :].mean(axis=1).astype(np.float32)      # (H,3)
        r = rgb[:, ref_sl, :].mean(axis=1).astype(np.float32)
        el = lum[:, ext_sl].mean(axis=1)
        rl = lum[:, ref_sl].mean(axis=1)
        d_ch = np.zeros((NB, 3), np.float32)
        d_lu = np.zeros(NB, np.float32)
        for i in range(NB):
            y0, y1 = edges[i], edges[i + 1]
            d_ch[i] = e[y0:y1].mean(axis=0) - r[y0:y1].mean(axis=0)
            d_lu[i] = float(el[y0:y1].mean() - rl[y0:y1].mean())
        res[tag] = {"d_ch": d_ch, "d_lu": d_lu,
                    "ramp8": abs(float(el.mean() - rl.mean())),
                    "ramp_ch": max(abs(float(e[:, c].mean() - r[:, c].mean())) for c in range(3))}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default="yy_19.png,kob68.png,kob68a.png,kob68b.png,kob68c.png,"
                                      "sl_01.png,asu62.png,sr0_01.png,miy63.png,cg_ai_01.png,nar20b.png")
    a = ap.parse_args()
    rows = {r["统一名"]: r for r in csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t")}
    for nm in [x.strip() for x in a.names.split(",")]:
        r = rows.get(nm)
        if not r:
            print(nm, "MISSING"); continue
        xl, xr = int(r["xl"]), int(r["xr"])
        rgb = np.asarray(Image.open(os.path.join(OUTPAINT, nm)).convert("RGB")).astype(np.float32)
        print("=" * 100)
        print("%s  xl=%d xr=%d  旧 ramp(灰度,ref shift0)=%s  ramp_ch=%s" % (nm, xl, xr, r["ramp"], r["ramp_ch"]))
        for shift in (0, 2, 4, 6, 8, 10, 12):
            b = band_stats(rgb, xl, xr, shift)
            for tag in ("L", "R"):
                d = b[tag]["d_ch"]
                dlu = b[tag]["d_lu"]
                # 分带通道绝对差的最大 / 中位（跨 6 带），先按通道取 max 再按通道 max
                absc = np.abs(d)
                mx = float(absc.max())
                med_per_ch = [float(np.median(absc[:, c])) for c in range(3)]
                med = max(med_per_ch)
                print("  shift=%2d %s ramp8=%6.2f ramp_ch=%6.2f | 分带最大(ch)=%6.2f 分带中位(ch)=%6.2f | "
                      "分带最大(luma)=%6.2f 中位(luma)=%6.2f | 最负带 luma=%.2f @b%d | 带ch=%s"
                      % (shift, tag, b[tag]["ramp8"], b[tag]["ramp_ch"], mx, med,
                         float(np.abs(dlu).max()), float(np.median(np.abs(dlu))),
                         float(dlu.min()), int(dlu.argmin()),
                         np.array2string(d[np.abs(dlu).argmax()].round(1))))
        del rgb


if __name__ == "__main__":
    main()
