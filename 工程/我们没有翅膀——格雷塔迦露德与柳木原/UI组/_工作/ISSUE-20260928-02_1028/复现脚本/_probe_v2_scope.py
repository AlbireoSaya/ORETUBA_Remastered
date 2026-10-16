# -*- coding: utf-8 -*-
r"""_probe_v2_scope.py —— 只读探针：确认 v2 补跑范围、内容自梯度、锚点两版的可比性。

不写任何图像产物；只打印统计，供设计 tonematch_pass_v2.py 用。
★ 缝位一律取 tsv 里的 xl/xr（输出坐标系）；**不得**用图片自身尺寸再过 out_seams
  （out 已是 1920×1080，out_seams 会返回 0/1920 —— 上一版探针即因此算错）。
"""
import sys, os, csv
WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
import numpy as np
from PIL import Image
from quality_axes import REF_SHIFT

f = lambda r, k: float(r.get(k) or 0)
RESID8 = ["cg_eri02.png", "cg_eri02a.png", "cg_eri02b.png", "kob65.png", "kob65a.png",
          "kob65b.png", "kob65c.png", "kob69.png"]


def load(p):
    return {r["统一名"]: r for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t")
            if r.get("统一名")}


def self_grad(nm, xl, xr, arr):
    """内容自带梯度：缝内 8 列 vs 内移 REF_SHIFT 后 8 列（两侧、灰度/通道取最大）。"""
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

    def pair(sl_a, sl_b):
        g = abs(float(lum[:, sl_a].mean()) - float(lum[:, sl_b].mean()))
        c = max(abs(float(arr[:, sl_a, k].mean()) - float(arr[:, sl_b, k].mean())) for k in range(3))
        return g, c
    gL, cL = pair(slice(xl, xl + 8), slice(xl + REF_SHIFT, xl + REF_SHIFT + 8))
    gR, cR = pair(slice(xr - 8, xr), slice(xr - REF_SHIFT - 8, xr - REF_SHIFT))
    return max(gL, cL, gR, cR), (gL, cL, gR, cR)


def main():
    op = load(os.path.join(ISSUE_DIR, "质量轴_v2.tsv"))
    tm = load(os.path.join(ISSUE_DIR, "质量轴_v2_tonematch.tsv"))
    hard = lambda r: (f(r, "mL4") >= 30 or f(r, "mRGB4") >= 40 or f(r, "er_fill") >= 4)
    struct = lambda r: (f(r, "mL4") >= 12 or f(r, "mRGB4") >= 15 or f(r, "bD16") >= 30
                        or f(r, "er_fill") >= 2)
    N = sorted(n for n, r in op.items() if (f(r, "ramp") >= 25 or f(r, "ramp_ch") >= 25
                                            or f(r, "bandmed_ch") >= 25))
    noP = [n for n in N if n not in tm]
    tone80 = [n for n in noP if not struct(op[n]) and not hard(op[n])]
    print("N=%d  noProd=%d  tone-only80=%d" % (len(N), len(noP), len(tone80)))
    rest = sorted(n for n in noP if n not in tone80)
    print("noProd 里其余 %d 件为结构/重绘触发（跑色调无益），前 10: %s" % (len(rest), ", ".join(rest[:10])))

    print("\n== A. 80 件内容自梯度（outpaint 内容区，缝位取 tsv）==")
    vals, rows = [], []
    for nm in tone80:
        a = np.asarray(Image.open(os.path.join(ISSUE_DIR, "outpaint", nm)).convert("RGB")).astype(np.float32)
        v, det = self_grad(nm, int(op[nm]["xl"]), int(op[nm]["xr"]), a)
        vals.append(v); rows.append((v, nm, det))
    rows.sort(reverse=True)
    vals = np.array(vals)
    print("  max(两侧,灰度/通道): p50 %.2f p90 %.2f p99 %.2f max %.2f ｜ >=25: %d 件 ｜ >=10: %d 件"
          % (np.percentile(vals, 50), np.percentile(vals, 90), np.percentile(vals, 99), vals.max(),
             int((vals >= 25).sum()), int((vals >= 10).sum())))
    for v, nm, d in rows[:10]:
        print("    %-14s self=%5.2f (L 灰度 %5.2f 通道 %5.2f ｜ R 灰度 %5.2f 通道 %5.2f)"
              % ((nm, v) + d))

    print("\n== B. 8 件残留件内容自梯度（outpaint，缝位取 tsv）==")
    for nm in RESID8:
        a = np.asarray(Image.open(os.path.join(ISSUE_DIR, "outpaint", nm)).convert("RGB")).astype(np.float32)
        xl, xr = int(op[nm]["xl"]), int(op[nm]["xr"])
        v, d = self_grad(nm, xl, xr, a)
        print("    %-14s self=%6.2f (L 灰度 %6.2f 通道 %6.2f ｜ R 灰度 %6.2f 通道 %6.2f)"
              % ((nm, v) + d))

    print("\n== C. 残留件左缝内容逐列 luma / 逐通道剖面（xl=241，内容 col0..20）==")
    for nm in ("cg_eri02.png", "kob65.png", "kob69.png"):
        a = np.asarray(Image.open(os.path.join(ISSUE_DIR, "outpaint", nm)).convert("RGB")).astype(np.float32)
        xl = int(op[nm]["xl"])
        lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
        cml = lum.mean(axis=0)
        print("  %s  L-content luma:" % nm, " ".join("%.0f" % cml[xl + i] for i in range(21)))
        for k, kn in enumerate("RGB"):
            ck = a[:, :, k].mean(axis=0)
            print("      %s:" % kn, " ".join("%.0f" % ck[xl + i] for i in range(21)))
        print("      band sh0=%.2f  sh10=%.2f  最外8列(ext far) luma=%.2f"
              % (cml[xl:xl + 8].mean(), cml[xl + 10:xl + 18].mean(), cml[:8].mean()))

    print("\n== D. 80 件里 tone 门触发原因分布 ==")
    import collections
    cnt = collections.Counter()
    for nm in tone80:
        r = op[nm]; w = []
        if f(r, "ramp") >= 25: w.append("gray")
        if f(r, "ramp_ch") >= 25: w.append("ch")
        if f(r, "bandmed_ch") >= 25: w.append("band")
        cnt["+".join(w)] += 1
    for k, v in cnt.most_common():
        print("    %-16s %d 件" % (k, v))


if __name__ == "__main__":
    main()
