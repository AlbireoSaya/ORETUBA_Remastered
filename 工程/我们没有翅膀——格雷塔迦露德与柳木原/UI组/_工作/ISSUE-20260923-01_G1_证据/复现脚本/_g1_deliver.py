# -*- coding: utf-8 -*-
r"""G1d · 交付 + 印相表 + 浅底合成预览 + 验收自证（配色重定版）

1. 切件_64\*.png → krkr\assets\ui\x_ui_qbicon_<key>[_on].png（同名覆盖）
2. 印相表_双态对照_64.png（覆盖旧图）+ 浅底合成预览_64.png（冰蓝底 #E9F1FB 与黑底，1:1 原尺寸）
3. 实测色值表：每件 圆底填充 / 环峰值色(含 B−R) / 环宽 / 光晕最外半径；两态差；对 #E9F1FB 的对比度

对比度口径：**平均通道亮度比**（与 vision 报数一致：用 #8CCEF9 对 #E9F1FB 复现出 1.22 ✓、
#E5EFFB 复现出 1.01 ✓）；同时并列 WCAG 2.x 比值供参考。
"""
import glob, json, os, shutil, sys
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
CUT = os.path.join(EV, "切件_64")

CANVAS = 64
CTR = 32.0
R_HALO = 31.5
YY, XX = np.mgrid[0:CANVAS, 0:CANVAS]
RG = np.sqrt((XX + 0.5 - CTR) ** 2 + (YY + 0.5 - CTR) ** 2)

KEYS = [("lock", "锁定"), ("save", "存档"), ("load", "读档"), ("qsave", "快速存档"),
        ("qload", "快速读档"), ("auto", "自动播放"), ("skip", "快进"), ("next", "下一选项"),
        ("prev", "上一选项"), ("log", "回想"), ("chart", "流程图"), ("option", "设置")]

SCREEN_BG = (233, 241, 251)          # #E9F1FB 本作复刻屏冰蓝底
NEON = (34, 184, 240)                # #22B8F0 锚点明令禁用的 neon cyan
TARGET = {"fill": {"off": (214, 233, 251), "on": (194, 226, 250)},
          "rim": {"off": (111, 180, 246), "on": (95, 176, 242)}}


def hx(rgb):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in rgb)


def lum_wcag(rgb):
    c = np.asarray(rgb, dtype=float) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def ct_ratio(a, b):
    """平均通道亮度比（vision 口径）。"""
    ma, mb = float(np.mean(a)), float(np.mean(b))
    return max(ma, mb) / min(ma, mb)


def ct_wcag(a, b):
    la, lb = lum_wcag(a), lum_wcag(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def path_of(key, st):
    return os.path.join(CUT, "x_ui_qbicon_%s%s.png" % (key, "" if st == "off" else "_on"))


def load(key, st):
    return np.array(Image.open(path_of(key, st)).convert("RGBA")).astype(float)


def stats(a):
    al, px = a[..., 3], a[..., :3]
    m = (RG <= 26.0) & (al > 200) & (px.mean(axis=-1) >= 150)
    fill = px[m].mean(axis=0) if m.sum() >= 30 else np.array([0.0, 0.0, 0.0])
    rr = np.arange(23.0, 28.51, 0.25)
    prof, cols = [], []
    for r in rr:
        mm = (RG >= r - 0.125) & (RG < r + 0.125) & (al > 200)
        if mm.sum() < 6:
            prof.append(-1e9); cols.append((0, 0, 0)); continue
        prof.append(float((px[..., 2][mm] - px[..., 0][mm]).mean()))
        cols.append(tuple(px[mm].mean(axis=0)))
    prof = np.asarray(prof); j = int(np.argmax(prof))
    peak_r, peak_br = float(rr[j]), float(prof[j])
    peak_rgb = np.array(cols[j], dtype=float)
    ins = [i for i in range(len(rr)) if prof[i] >= peak_br * 0.6 and abs(rr[i] - peak_r) <= 3]
    width = (max(rr[i] for i in ins) - min(rr[i] for i in ins) + 0.25) if ins else 0.0
    nz = np.nonzero(al > 0)
    return {"fill": fill, "peak_rgb": peak_rgb, "peak_br": peak_br, "peak_r": peak_r,
            "width": round(float(width), 2), "halo_r": float(RG[nz].max())}


def deploy():
    n = 0
    for key, _ in KEYS:
        for sfx in ("", "_on"):
            shutil.copyfile(os.path.join(CUT, "x_ui_qbicon_%s%s.png" % (key, sfx)),
                            os.path.join(UI, "x_ui_qbicon_%s%s.png" % (key, sfx)))
            n += 1
    print("部署 %d 件（64x64）→ %s" % (n, UI))


def checker(n, c=8):
    im = Image.new("RGB", (n, n), (255, 255, 255)); px = im.load()
    for y in range(n):
        for x in range(n):
            if ((x // c) + (y // c)) % 2:
                px[x, y] = (203, 206, 210)
    return im


def fonts():
    f1 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
    f2 = f1
    for cand in ("C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"):
        try:
            f2 = ImageFont.truetype(cand, 17)
            if f2.getmask("想").size[0] > 2:
                break
        except Exception:
            continue
    return f1, f2


def contact(out):
    f1, f2 = fonts()
    cw, gap, cell = 64 * 3, 8, 64 * 3 * 2 + 8 + 28
    chh = 28 + cw + 26
    sheet = Image.new("RGB", (cell * 4, chh * 3), (246, 248, 251))
    d = ImageDraw.Draw(sheet)
    for i, (key, zh) in enumerate(KEYS):
        r, c = divmod(i, 4)
        ox, oy = c * cell, r * chh
        for si, st in enumerate(("off", "on")):
            im = Image.open(path_of(key, st)).convert("RGBA").resize((cw, cw), Image.NEAREST)
            bgx = ox + 14 + si * (cw + gap)
            bg = checker(cw); bg.paste(im, (0, 0), im)
            sheet.paste(bg, (bgx, oy + 14))
            d.rectangle((bgx, oy + 14, bgx + cw, oy + 14 + cw), outline=(120, 130, 145))
            d.text((bgx + 3, oy + 16), "常态" if st == "off" else "悬停", fill=(30, 50, 85), font=f2)
        lx, ly = ox + 14, oy + 14 + cw + 5
        t = "%d  %s" % (i + 1, key)
        d.text((lx, ly), t, fill=(20, 40, 75), font=f1)
        d.text((lx + d.textlength(t, font=f1) + 8, ly + 1), zh, fill=(20, 40, 75), font=f2)
    sheet.save(out)
    return sheet.size


def preview(out):
    """浅底合成预览：12 常态 + 12 悬停在 #E9F1FB 与纯黑两种底色上，1:1 原尺寸。"""
    f1, f2 = fonts()
    gap, pad, lab = 12, 16, 26
    W = pad * 2 + 24 * 64 + 23 * gap
    H = pad * 2 + 2 * (lab + 64 + pad)
    img = Image.new("RGB", (W, H), (150, 150, 150))
    d = ImageDraw.Draw(img)
    rows = [("上排 = #E9F1FB 本作复刻屏冰蓝底（浅底可见性检验）", SCREEN_BG),
            ("下排 = #000000 纯黑底（压黑边检验）", (0, 0, 0))]
    y = pad
    for title, bg in rows:
        d.text((pad, y), title, fill=(15, 15, 15), font=f2)
        y += lab
        img.paste(Image.new("RGB", (W, 64), bg), (0, y))
        for i, (key, _zh) in enumerate(KEYS):
            for si, st in enumerate(("off", "on")):
                im = Image.open(path_of(key, st)).convert("RGBA")
                img.paste(im, (pad + (i * 2 + si) * (64 + gap), y), im)
        y += 64 + pad
    img.save(out)
    return img.size


def main():
    deploy()
    print("印相表 →", contact(os.path.join(EV, "印相表_双态对照_64.png")))
    print("浅底合成预览 →", preview(os.path.join(EV, "浅底合成预览_64.png")))

    print("\n" + "=" * 118)
    print("【实测色值表】每件：圆底填充 / 环峰值色(含 B−R) / 环宽 / 光晕最外半径")
    print("=" * 118)
    print("%-4s %-7s %-9s %-22s %-8s %-8s %-9s %-9s"
          % ("态", "key", "圆底填充", "环峰值色", "环宽px", "光晕r", "对底比", "环/底比"))
    data = {}
    for st in ("off", "on"):
        for key, _zh in KEYS:
            a = load(key, st)
            s = stats(a)
            data[(st, key)] = s
            print("%-4s %-7s %-9s %-22s %-8.2f %-8.2f %-9.3f %-9.3f"
                  % (st, key, hx(s["fill"]), "%s (B-R=%.0f)" % (hx(s["peak_rgb"]), s["peak_br"]),
                     s["width"], s["halo_r"], ct_ratio(s["fill"], SCREEN_BG),
                     ct_ratio(s["peak_rgb"], SCREEN_BG)))

    print("\n" + "=" * 118)
    print("【汇总】12 件均值 与 两态差 ｜ 对比度口径：平均通道亮度比（vision 口径）+ WCAG")
    print("=" * 118)
    for st in ("off", "on"):
        f = np.mean([data[(st, k)]["fill"] for k, _ in KEYS], axis=0)
        p = np.mean([data[(st, k)]["peak_rgb"] for k, _ in KEYS], axis=0)
        w = np.mean([data[(st, k)]["width"] for k, _ in KEYS])
        h = np.mean([data[(st, k)]["halo_r"] for k, _ in KEYS])
        print("  %-4s 圆底填充 %s (%.0f,%.0f,%.0f) ｜ 环峰值 %s B-R=%.0f ｜ 环宽 %.2fpx ｜ 光晕r %.2f"
              % (st, hx(f), f[0], f[1], f[2], hx(p), p[2] - p[0], w, h))
        print("       对 #E9F1FB：圆底 %.3f:1（WCAG %.3f）｜ 环 %.3f:1（WCAG %.3f）"
              % (ct_ratio(f, SCREEN_BG), ct_wcag(f, SCREEN_BG),
                 ct_ratio(p, SCREEN_BG), ct_wcag(p, SCREEN_BG)))
    fo = np.mean([data[("off", k)]["fill"] for k, _ in KEYS], axis=0)
    fn = np.mean([data[("on", k)]["fill"] for k, _ in KEYS], axis=0)
    po = np.mean([data[("off", k)]["peak_rgb"] for k, _ in KEYS], axis=0)
    pn = np.mean([data[("on", k)]["peak_rgb"] for k, _ in KEYS], axis=0)
    print("\n  两态差：圆底 ΔRGB = %s ｜ 环 ΔRGB = %s ｜ ΔB-R = %.0f"
          % (np.round(fn - fo).astype(int), np.round(pn - po).astype(int),
             (pn[2] - pn[0]) - (po[2] - po[0])))
    print("  圆底 态间亮度比 %.4f ｜ 环 态间亮度比 %.4f" % (ct_ratio(fo, fn), ct_ratio(po, pn)))

    print("\n" + "=" * 118)
    print("【去霓虹 / 达标核对】")
    print("=" * 118)
    po_m = np.mean(po); pn_m = np.mean(pn)
    print("  禁用色 neon cyan %s 平均 %.1f B-R=%.0f" % (hx(NEON), NEON[0] + NEON[1] + NEON[2],
                                                     NEON[2] - NEON[0]))
    print("  旧悬停环 #25C8F9 平均 162.0 B-R=212（已弃用）")
    print("  新悬停环 %s 平均 %.1f B-R=%.0f  ⇒ 去霓虹 %s ｜ B−R 命中目标 ≈147 %s"
          % (hx(pn), pn_m, pn[2] - pn[0],
             "✓" if (pn[2] - pn[0]) < 170 else "✗", "✓" if abs((pn[2] - pn[0]) - 147) <= 12 else "✗"))
    print("  常态圆底 %.3f:1 ≥1.15 %s ｜ 常态环 %.3f:1 ≥1.5 %s"
          % (ct_ratio(fo, SCREEN_BG), "✓" if ct_ratio(fo, SCREEN_BG) >= 1.15 else "✗",
             ct_ratio(po, SCREEN_BG), "✓" if ct_ratio(po, SCREEN_BG) >= 1.5 else "✗"))
    print("  （注：主代理给的目标色自身达不到它给的线：#D6E9FB→%.3f、#6FB4F6→%.3f）"
          % (ct_ratio(TARGET["fill"]["off"], SCREEN_BG), ct_ratio(TARGET["rim"]["off"], SCREEN_BG)))

    print("\n【几何未回归】两态 圆心/圆径/光晕半径")
    print("=" * 118)
    g = json.load(open(os.path.join(EV, "圆几何归一化.json"), encoding="utf-8"))
    gm = {"%s_%s" % (x["state"], x["key"]): x for x in g}
    worst = 0.0
    for key, _ in KEYS:
        a, b = gm["off_" + key], gm["on_" + key]
        d = [abs(a["out_center"][0] - b["out_center"][0]), abs(a["out_center"][1] - b["out_center"][1]),
             abs(a["out_d128"] - b["out_d128"]), abs(a["halo_r"] - b["halo_r"])]
        worst = max(worst, max(d))
    print("  d128 全 24 件 = %s ｜ 圆心 = %s ｜ 光晕r = %s ｜ 两态最大差 = %.2f px → %s"
          % (sorted({x["out_d128"] for x in g}), sorted({tuple(x["out_center"]) for x in g}),
             sorted({x["halo_r"] for x in g}), worst, "通过" if worst <= 1 else "不通过"))
    print("  r>=31.5 非0 合计 = %d ｜ alpha=0 处非0 RGB 合计 = %d"
          % (sum(x["ge_halo_nonzero"] for x in g), sum(x["rgb_at_alpha0"] for x in g)))
    print("  单调违例合计 = %d" % sum(len(x["monotone_bad"]) for x in g))

    print("\n【git status】我的新增应只有 24 件 x_ui_qbicon_*")
    print("=" * 118)
    os.system('cd /d "%s" && git status --porcelain -- "*/krkr/assets/ui/x_ui_qbicon_*"' % _G)
    print("件数 = %d ｜ 尺寸 = %s ｜ 模式 = %s"
          % (len(glob.glob(os.path.join(UI, "x_ui_qbicon_*.png"))),
             sorted({Image.open(p).size for p in glob.glob(os.path.join(UI, "x_ui_qbicon_*.png"))}),
             sorted({Image.open(p).mode for p in glob.glob(os.path.join(UI, "x_ui_qbicon_*.png"))})))


if __name__ == "__main__":
    main()
