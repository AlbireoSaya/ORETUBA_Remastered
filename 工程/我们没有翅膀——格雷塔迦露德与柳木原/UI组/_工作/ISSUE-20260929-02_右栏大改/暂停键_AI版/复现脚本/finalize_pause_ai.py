# -*- coding: utf-8 -*-
r"""E5 · AI 版暂停键 —— 定稿规格化 + 自证 + 对照图

做三件事（全部可重跑、幂等）：
  ① 定稿：把选定候选按「环外径 → 108」等比缩放、环 bbox 中心对准 (59,59)、裁 119×119，
     导出 PNG-32 真 alpha → `x_ui_pbkick_pause_AI_off.png`
  ② 自证：实测尺寸 / mode / alpha 分布 / 最外 1px 帧 α；与 pbkick_off / 派生版暂停 同口径对照
     → `_自证数据.json`（正文写进 `自证报告.md`）
  ③ 对照图：三行（播放键_off / 派生版暂停_off / AI版暂停），每行 整幅×4 + 字形局部×4 + 中心×8
     → `AI版_vs_派生版_vs_播放键.png`

用法：python finalize_pause_ai.py [--pick C15]
"""
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                                 # 暂停键_AI版
UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))   # UI组
CAND = os.path.join(BASE, "候选")
REF = os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_off.png")
DER = os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_pause_off.png")
OUT_FINAL = os.path.join(BASE, "x_ui_pbkick_pause_AI_off.png")
OUT_SHEET = os.path.join(BASE, "AI版_vs_派生版_vs_播放键.png")
OUT_JSON = os.path.join(BASE, "_自证数据.json")
T = 119
GLYPH_CROP = (26, 26, 93, 93)         # 字形局部（67×67，含盘心与两条）

FONT = None
for c in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
    if os.path.exists(c):
        FONT = c; break


def ring_bbox(im):
    a = im.getchannel("A"); W, H = im.size; px = a.load()
    xs = [x for x in range(W) if any(px[x, y] >= 250 for y in range(H))]
    ys = [y for y in range(H) if any(px[x, y] >= 250 for x in range(W))]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def norm119(im):
    """等比缩放使环外径 → 108，环 bbox 中心对准 (59,59)，裁 119×119（等比，无变形）。"""
    im = im.convert("RGBA")
    bb = ring_bbox(im)
    if bb is None:
        raise SystemExit("无 alpha>=250 的环，无法归一化")
    d = max(bb[2] - bb[0] + 1, bb[3] - bb[1] + 1)
    k = 108.0 / d
    im2 = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cx = (bb[0] + bb[2] + 1) / 2.0 * k
    cy = (bb[1] + bb[3] + 1) / 2.0 * k
    out = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    out.alpha_composite(im2, (round(59 - cx), round(59 - cy)))
    return out


def stats(im, label):
    raw_mode = im.mode          # ★ 真实 mode 必须在 convert 之前读
    im = im.convert("RGBA")
    W, H = im.size
    a = im.getchannel("A"); ap = a.load()
    h = a.histogram()
    n = W * H
    frame = [ap[x, 0] for x in range(W)] + [ap[x, H - 1] for x in range(W)] + \
            [ap[0, y] for y in range(H)] + [ap[W - 1, y] for y in range(H)]
    al = list(a.getdata())
    return dict(label=label, size=[W, H], mode=raw_mode,
                alpha_zero=h[0], alpha_full=h[255],
                alpha_partial=n - h[0] - h[255],
                pct_zero=round(100.0 * h[0] / n, 2),
                pct_full=round(100.0 * h[255] / n, 2),
                pct_partial=round(100.0 * (n - h[0] - h[255]) / n, 2),
                frame1px_max=max(frame), frame1px_nonzero=sum(1 for v in frame if v > 0),
                alpha_ge16=sum(1 for v in al if v >= 16),
                alpha_ge128=sum(1 for v in al if v >= 128))


def ring_metrics(im):
    """环芯半径 / 环 ΔL（与 _measure_cands.py 同口径，便于两张表对读）。"""
    im = im.convert("RGBA"); W, H = im.size
    a = im.getchannel("A").load(); px = im.load()
    bb = ring_bbox(im)
    cx = (bb[0] + bb[2]) / 2.0; cy = (bb[1] + bb[3]) / 2.0
    R = max(bb[2] - bb[0] + 1, bb[3] - bb[1] + 1) / 2.0
    base = px[int(cx), int(cy - 0.7 * R)][:3]
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    fillL = lum(base)
    best = None
    for ang in (-90, 0, 90, 180):
        rad = math.radians(ang)
        for i in range(0, int(0.25 * R / 0.25) + 1):
            d = 0.78 * R + i * 0.25
            x = int(round(cx + d * math.cos(rad))); y = int(round(cy + d * math.sin(rad)))
            if 0 <= x < W and 0 <= y < H and a[x, y] >= 200:
                if best is None or lum(px[x, y][:3]) < best[1]:
                    best = (d, lum(px[x, y][:3]), px[x, y][:3])
    return dict(disc_fill_rgb=list(base), disc_fill_lum=round(fillL, 1),
                ring_r=round(best[0], 2), ring_lum=round(best[1], 1),
                ring_delta_lum=round(fillL - best[1], 1), ring_rgb=list(best[2]))


def glyph_metrics119(im):
    """在**已归一化的 119 画布**上量字形（k=1，读数即最终像素）。
    字形判定：以 0.55R–0.90R 环带的中位色当盘面底色，盘心区内偏离它的像素即字形。"""
    im = im.convert("RGBA"); W, H = im.size
    a = im.getchannel("A").load(); px = im.load()
    bb = ring_bbox(im)
    cx = (bb[0] + bb[2]) / 2.0; cy = (bb[1] + bb[3]) / 2.0
    R = max(bb[2] - bb[0] + 1, bb[3] - bb[1] + 1) / 2.0
    samp = []
    for y in range(H):
        for x in range(W):
            dd = math.hypot(x - cx, y - cy)
            if 0.55 * R <= dd <= 0.90 * R and a[x, y] >= 200:
                samp.append(px[x, y][:3])
    samp.sort(key=lambda c: c[0] + c[1] + c[2])
    base = samp[len(samp) // 2]
    def g(x, y):
        if a[x, y] < 190 or math.hypot(x - cx, y - cy) > 0.55 * R:
            return False
        return math.dist(px[x, y][:3], base) > 18
    cols = [x for x in range(W) if any(g(x, y) for y in range(H))]
    rows = [y for y in range(H) if any(g(x, y) for x in range(W))]
    if not cols or not rows:
        return {}
    runs, cur = [], None
    for x in range(min(cols), max(cols) + 1):
        on = any(g(x, y) for y in range(H))
        if on and cur is None:
            cur = x
        elif not on and cur is not None:
            runs.append((cur, x - 1)); cur = None
    if cur is not None:
        runs.append((cur, max(cols)))
    runs = [r for r in runs if r[1] - r[0] + 1 > 2]
    # 圆角等效半径：条顶行相对条宽的每侧内缩（圆角 r 的几何近似 inset ≈ r - sqrt(2r-1)）
    cr = None
    if runs:
        x0, x1 = runs[0]
        ytop = min(y for y in range(H) if any(g(x, y) for x in range(x0, x1 + 1)))
        wt = sum(1 for x in range(x0, x1 + 1) if g(x, ytop))
        inset = (x1 - x0 + 1 - wt) / 2.0
        # 反解 r：inset = r - sqrt(2r-1)
        rr = None
        for cand in [i / 10.0 for i in range(0, 121)]:
            if abs((cand - math.sqrt(max(2 * cand - 1, 0))) - inset) < 0.05:
                rr = cand; break
        cr = None if rr is None else round(rr, 1)
    return dict(n_bars=len(runs),
                bar_w=[(r[1] - r[0] + 1) for r in runs],
                gap=(runs[1][0] - runs[0][1] - 1) if len(runs) >= 2 else None,
                group_w=max(cols) - min(cols) + 1, h=max(rows) - min(rows) + 1,
                corner_r_est=cr,
                bbox=[min(cols), min(rows), max(cols), max(rows)])


def build_sheet(final, pick):
    ref_im = Image.open(REF).convert("RGBA")
    der_im = Image.open(DER).convert("RGBA")
    fin_im = Image.open(final).convert("RGBA")
    notes = []
    gA = glyph_metrics119(fin_im); gB = glyph_metrics119(der_im)
    notes.append("▶ 三角：bbox 48×51，右偏 w/8 光学居中")
    notes.append("‖ 条宽 %s ｜ 间隙 %s ｜ 组宽 %s ｜ 条高 %s（规格 16/16/48/54）" % (
        gB["bar_w"], gB["gap"], gB["group_w"], gB["h"]))
    notes.append("‖ 条宽 %s ｜ 间隙 %s ｜ 组宽 %s ｜ 条高 %s —— 间隙偏窄 %d、组宽偏窄 %d" % (
        gA["bar_w"], gA["gap"], gA["group_w"], gA["h"],
        16 - gA["gap"], 48 - gA["group_w"]))
    rows = [("播放键_off（原版 · 基准）", ref_im, notes[0]),
            ("派生版暂停_off（像素同源 · 基准）", der_im, notes[1]),
            ("AI版暂停_off（候选 %s · 图生图）" % pick, fin_im, notes[2])]
    Z, CZ = 4, 8
    full = T * Z
    cw = (GLYPH_CROP[2] - GLYPH_CROP[0]) * Z
    c2 = 64 * CZ
    pad, lab, head = 16, 96, 104
    rowh = max(full, c2) + lab + pad
    LC = 430
    W = pad + LC + full + cw + c2 + pad * 4
    H = head + len(rows) * rowh + pad
    sheet = Image.new("RGB", (W, H), (24, 26, 31))
    d = ImageDraw.Draw(sheet)
    f1 = ImageFont.truetype(FONT, 22) if FONT else ImageFont.load_default()
    f2 = ImageFont.truetype(FONT, 17) if FONT else ImageFont.load_default()
    f3 = ImageFont.truetype(FONT, 15) if FONT else ImageFont.load_default()
    d.text((pad, 10), "暂停键三版对照｜119×119 PNG-32 真 alpha｜放大一律最近邻（NEAREST）",
           font=f1, fill=(228, 236, 247))
    d.text((pad, 44), "AI 版＝备用版，不接线、不入 assets（用户二选一前只作对照）",
           font=f3, fill=(150, 172, 196))
    cx0 = pad + LC
    cx1 = cx0 + full + pad
    cx2 = cx1 + cw + pad
    d.text((cx0, head - 30), "整幅 ×4", font=f2, fill=(160, 196, 232))
    d.text((cx1, head - 30), "字形局部 ×4", font=f2, fill=(160, 196, 232))
    d.text((cx2, head - 30), "中心 ×8", font=f2, fill=(160, 196, 232))
    for i, (name, im, note) in enumerate(rows):
        y = head + i * rowh
        d.text((pad, y + 6), name, font=f1, fill=(214, 226, 240))
        st = stats(im, name); gm = ring_metrics(im)
        d.text((pad, y + 36), "尺寸 %d×%d ｜ mode %s ｜ 最外 1px 帧 αmax=%d" % (
            im.width, im.height, im.mode, st["frame1px_max"]), font=f2, fill=(168, 186, 208))
        d.text((pad, y + 58), "α=0 %.1f%% ｜ 半透明 %.1f%% ｜ α=255 %.1f%% ｜ 环芯 r=%.1f ｜ 环ΔL=%.1f" % (
            st["pct_zero"], st["pct_partial"], st["pct_full"], gm["ring_r"], gm["ring_delta_lum"]),
            font=f2, fill=(168, 186, 208))
        d.text((pad, y + 80), note, font=f3, fill=(206, 220, 236))
        def blit(img, x, yy, w, h):
            bg = Image.new("RGB", (w, h), (48, 51, 58))
            bg.paste(img.convert("RGB"), (0, 0), img)
            sheet.paste(bg, (x, yy))
        blit(im.resize((full, full), Image.NEAREST), cx0, y + lab, full, full)
        blit(im.crop(GLYPH_CROP).resize((cw, cw), Image.NEAREST), cx1, y + lab + (c2 - cw) // 2, cw, cw)
        blit(im.crop((59 - 32, 59 - 32, 59 + 32, 59 + 32)).resize((c2, c2), Image.NEAREST),
             cx2, y + lab, c2, c2)
    sheet.save(OUT_SHEET)
    return OUT_SHEET, notes


def main():
    pick = "C15"
    if "--pick" in sys.argv:
        pick = sys.argv[sys.argv.index("--pick") + 1]
    src = os.path.join(CAND, "pause_AI_cand_%s.png" % pick)
    im = Image.open(src)
    assert im.mode == "RGBA", "候选不是 RGBA：%s" % im.mode
    fin = norm119(im)
    fin.save(OUT_FINAL)                       # PNG-32（RGBA）真 alpha
    res = dict(pick=pick, src=os.path.basename(src), src_size=list(im.size),
               final=os.path.basename(OUT_FINAL), final_size=list(fin.size),
               final_mode=Image.open(OUT_FINAL).mode,
               stats=[stats(Image.open(REF).convert("RGBA"), "播放键_off"),
                      stats(Image.open(DER).convert("RGBA"), "派生版暂停_off"),
                      stats(fin, "AI版暂停_off")],
               ring=[ring_metrics(Image.open(REF).convert("RGBA")),
                     ring_metrics(Image.open(DER).convert("RGBA")),
                     ring_metrics(fin)],
               glyph_119=dict(liuhua=glyph_metrics119(fin),
                              derived=glyph_metrics119(Image.open(DER).convert("RGBA"))))
    sheet, notes = build_sheet(OUT_FINAL, pick)
    res["sheet"] = os.path.basename(sheet)
    res["sheet_notes"] = notes
    json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("定稿 ->", OUT_FINAL, fin.size, Image.open(OUT_FINAL).mode)
    print("对照图 ->", sheet)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
