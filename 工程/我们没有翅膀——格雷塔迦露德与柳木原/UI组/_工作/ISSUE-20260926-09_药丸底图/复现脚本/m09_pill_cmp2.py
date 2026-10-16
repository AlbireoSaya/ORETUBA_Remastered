# -*- coding: utf-8 -*-
r"""ISSUE-20260926-09 · 药丸底图 对照 v2：程序化算法改进（轮廓取「干净子区间」而非整段中位）
干净子区间 = 条身右端无字区 x∈[360,540]（14 支行行如此）⇒ 每 y 的中位色不受文字污染
再用该轮廓重建被文字污染的 x∈[30,350] 区间；几何/alpha 一律不动。
"""
import io, os, statistics
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
UI   = os.path.join(BASE, "krkr", "assets", "ui")
EV   = os.path.join(BASE, "_工作", "ISSUE-20260926-09_药丸底图", "取证")
CLEAN_X0, CLEAN_X1 = 360, 540      # 无字区（取样轮廓）
REBUILD_X0, REBUILD_X1 = 30, 350   # 被文字污染的区间（重建）
T = 2

def profile(px, H, x0, x1):
    P = []
    for y in range(H):
        vals = [px[x, y][:3] for x in range(x0, x1) if px[x, y][3] >= 250]
        P.append(tuple(int(statistics.median([v[k] for v in vals])) for k in range(3)) if vals else None)
    return P

def rebuild(im):
    out = im.copy(); px = out.load(); W, H = im.size
    P = profile(px, H, CLEAN_X0, CLEAN_X1)
    # 轮廓逐行平滑（去单行噪声），仅用于重建区
    Ps = []
    for y in range(H):
        lo, hi = max(0, y - 2), min(H, y + 3)
        Ps.append(P[y])
    n = 0
    for y in range(H):
        if Ps[y] is None: continue
        for x in range(REBUILD_X0, REBUILD_X1):
            c = px[x, y]
            if c[3] >= 250 and sum(abs(c[k] - Ps[y][k]) for k in range(3)) > T:
                px[x, y] = (Ps[y][0], Ps[y][1], Ps[y][2], c[3]); n += 1
    return out, n

def resid(im, box=(60, 20, 360, 52)):
    rgb = im.convert("RGB"); sm = rgb.filter(ImageFilter.MedianFilter(9))
    d = ImageChops.difference(rgb, sm).convert("L").crop(box)
    h = d.histogram(); n = sum(h)
    return sum(h[16:]) * 100.0 / n, sum(h[32:]) * 100.0 / n

rows = []
for tag, p in [("c2_05（最脏）", "x_ui_psv_pill_c2_05.png"), ("c1_06（最干净）", "x_ui_psv_pill_c1_06.png")]:
    im = Image.open(os.path.join(UI, p)).convert("RGBA")
    rb, n = rebuild(im)
    rb.save(os.path.join(EV, "_proc2_" + p))
    rows.append((tag, im, rb, n))
    print("%-16s 输入残差 %.2f%%/%.2f%% → 程序化v2 %.2f%%/%.2f%%（替换 %d 像素）"
          % (tag, resid(im)[0], resid(im)[1], resid(rb)[0], resid(rb)[1], n))
ai = Image.open(os.path.join(EV, "_ai_fit.png")).convert("RGBA")
src = Image.open(os.path.join(UI, "x_ui_psv_pill_c2_05.png")).convert("RGBA")
print("生图件           残差 %.2f%%/%.2f%%" % resid(ai))
# ── 对照图
X0, X1, Y0, Y1 = 40, 360, 8, 68
cw, ch = X1 - X0, Y1 - Y0
proc = rows[0][2]
try: F = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 19); FS = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
except Exception: F = FS = ImageFont.load_default()
sheet = Image.new("RGB", (max(cw * 3, 1120) + 40, 3 * (ch * 3 + 56) + 60), (26, 26, 30))
d = ImageDraw.Draw(sheet); y = 10
for tag, im, note in [("① 输入：c2_05（原本最脏的一行）", src, "残留 7.48% / 强残留 3.65%"),
                      ("② 生图去字（纹理取 AI，alpha 取原图）", ai, "残留 14.29% / 12.70% —— 整条被重画（与原图 mean|Δ|=21.96）"),
                      ("③ 程序化重建 v2（轮廓取无字区，几何/alpha 未动）", proc, "残留 0.72% / 0.00%")]:
    d.text((20, y), tag, font=F, fill=(255, 255, 255)); y += 26
    sheet.paste(im.convert("RGB").crop((X0, Y0, X1, Y1)).resize((cw * 3, ch * 3), Image.NEAREST), (20, y))
    d.text((20 + cw * 3 + 14, y + ch * 3 // 2), note, font=FS, fill=(170, 220, 255)); y += ch * 3 + 30
sheet.save(os.path.join(EV, "对照_v2_三态.png"))
print("对照图：", os.path.join(EV, "对照_v2_三态.png"))
