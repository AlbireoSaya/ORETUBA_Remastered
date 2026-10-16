# -*- coding: utf-8 -*-
r"""E5 · 定稿 vs 播放键_off 的量化差异（供自证报告的「目视差异评语」落数字）。
输出：_差异实测.json + 控制台表。用法：python _diff_vs_ref.py
"""
import os, json, math
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
PAIRS = [("播放键_off", os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_off.png")),
         ("派生版暂停_off", os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_pause_off.png")),
         ("AI版暂停_off", os.path.join(BASE, "x_ui_pbkick_pause_off_AI_off.png"))]
PAIRS[2] = ("AI版暂停_off", os.path.join(BASE, "x_ui_pbkick_pause_AI_off.png"))


def probe(im):
    im = im.convert("RGBA"); W, H = im.size
    a = im.getchannel("A").load(); px = im.load()
    cx = cy = (W - 1) / 2.0
    # 盘心区（r<40）均值色与均值 α —— 盘面本身的「调子」
    def region(rlo, rhi):
        n = 0; s = [0, 0, 0]; sa = 0
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - cx, y - cy)
                if rlo <= d < rhi:
                    n += 1; sa += a[x, y]
                    for i in range(3):
                        s[i] += px[x, y][i]
        return [round(v / n, 1) for v in s], round(sa / float(n), 1)
    core_rgb, core_a = region(0, 40)
    fill_rgb, fill_a = region(40, 47)
    # 径向 α 剖面（8 方向平均）：α 首次 <128 与 <16 的半径
    def radius_at(thr):
        for k in range(1, 300):
            r = 40 + k * 0.25
            vals = []
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                x = int(round(cx + r * math.cos(rad))); y = int(round(cy + r * math.sin(rad)))
                if 0 <= x < W and 0 <= y < H:
                    vals.append(a[x, y])
            if vals and sum(vals) / float(len(vals)) < thr:
                return round(r, 2)
        return None
    return dict(core_rgb=core_rgb, core_mean_alpha=core_a,
                fill_rgb_40_47=fill_rgb, fill_mean_alpha_40_47=fill_a,
                r_alpha_lt128=radius_at(128), r_alpha_lt16=radius_at(16))


def main():
    res = {}
    print("%-16s %-20s %-10s %-22s %-10s %-10s %-10s" % (
        "件", "盘心均值RGB(α)", "盘心α", "环带40-47 RGB(α)", "环带α", "α<128 r", "α<16 r"))
    for name, p in PAIRS:
        im = Image.open(p)
        r = probe(im)
        res[name] = r
        print("%-16s %-20s %-10s %-22s %-10s %-10s %-10s" % (
            name, tuple(r["core_rgb"]), r["core_mean_alpha"], tuple(r["fill_rgb_40_47"]),
            r["fill_mean_alpha_40_47"], r["r_alpha_lt128"], r["r_alpha_lt16"]))
    # 与播放键的逐像素差（仅统计环内 r<47 的盘面区）
    ref = Image.open(PAIRS[0][1]).convert("RGBA")
    for name, p in PAIRS[1:]:
        im = Image.open(p).convert("RGBA")
        W, H = im.size; cx = cy = (W - 1) / 2.0
        ra = ref.getchannel("A").load(); ia = im.getchannel("A").load()
        rp = ref.load(); ip = im.load()
        mx = 0; mxat = None; nz = 0; tot = 0
        for y in range(H):
            for x in range(W):
                if math.hypot(x - cx, y - cy) < 47:
                    tot += 1
                    d = max(abs(rp[x, y][i] - ip[x, y][i]) for i in range(3))
                    d = max(d, abs(ra[x, y] - ia[x, y]))
                    if d > 0:
                        nz += 1
                    if d > mx:
                        mx = d; mxat = [x, y]
        print("%-16s 盘面区(r<47) 与播放键逐像素：非零 %d/%d = %.1f%%，最大差 %d @%s" % (
            name, nz, tot, 100.0 * nz / tot, mx, mxat))
        res[name + "_diff_vs_play"] = dict(nonzero=nz, total=tot,
                                           pct_nonzero=round(100.0 * nz / tot, 2),
                                           max_abs_diff=mx, max_at=mxat)
    json.dump(res, open(os.path.join(BASE, "_差异实测.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("->", os.path.join(BASE, "_差异实测.json"))


if __name__ == "__main__":
    main()
