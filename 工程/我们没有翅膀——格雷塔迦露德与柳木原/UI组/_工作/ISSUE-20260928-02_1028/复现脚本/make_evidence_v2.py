# -*- coding: utf-8 -*-
r"""
make_evidence_v2.py —— 证据补齐（ISSUE-20260928-02 · vision 打回项 1/6/7/8 的证据包）

vision 打回的三条证据缺陷
    ① 灰阶全高平均的 |ramp| 色相/分带盲区（本脚本不判，只出证据）；
    ② **LITE+CLEAN 共 71 件缝条 0 张**（其中 59 件连剖面也没有）——而"可直接采用"正是免验放行集合；
    ③ **缝条 MID 类为 1×**，1× 下看不出 1px 高光线；缝条里没有 xl/xr 与带号标注，无法定位；
       349 件 tonematch 里只有 25 件有全宽剖面。

本脚本产出（全部落 `证据\*`，只读 outpaint / outpaint_tonematch / outpaint_geo*）
    证据\缝条_v2\<名>_缝条.png      全 640 件，**一律 2×**、全高 1080；
                                    条宽 64 列（缝居中于条内 x=32）；左/右两条并列；
                                    行 = outpaint(LaMa) / tonematch（若有）/ geo（若有）；
                                    每行标 `统一名 xl xr 采用产物 分类`，条内画 6 条带界线 + 带号 + 缝列(红)
    证据\色调剖面_v2\<名>_剖面.png  全 640 件：全宽列均值剖面（灰=outpaint 原样 / 蓝=装配产物），
                                    **扩展区加底色**、缝列红竖线 —— 第三格才是判色调漂移的证据
    证据\三格卡\<名>_三格卡.png     全 640 件：① 整图 1/3 缩略（画两条缝列 + 扩展区边界框）
                                    ② 全高 2× 缝条（左右并列）③ 全宽列均值剖面（同上）
    证据\证据_v2_汇总.txt           件数 / 尺度 / 体量 / 覆盖

用法
    set PYTHONPYCACHEPREFIX=...\ISSUE-20260928-02_1028\_pycache
    python make_evidence_v2.py                 # 全部（幂等跳过已有）
    python make_evidence_v2.py --what strips
    python make_evidence_v2.py --names sr0_01.png,sl_01.png --force
"""
import sys, os, csv, time, argparse, collections

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image, ImageDraw, ImageFont

EVID = os.path.join(ISSUE_DIR, "证据")
DISP = os.path.join(ISSUE_DIR, "须处置清单_v2.tsv")
OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
TONEMATCH = os.path.join(ISSUE_DIR, "outpaint_tonematch")
GEO = os.path.join(ISSUE_DIR, "outpaint_geo")
STRIP_DIR = os.path.join(EVID, "缝条_v2")
PROF_DIR = os.path.join(EVID, "色调剖面_v2")
CARD_DIR = os.path.join(EVID, "三格卡")
SUM_TXT = os.path.join(EVID, "证据_v2_汇总.txt")

NB = 6
HALF = 32           # 缝两侧各 32 列
GAP = 6
LABEL = 20
SCALE = 2
CARD_THUMB = 3      # 整图缩略比


def font(sz=13):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def bands():
    return [(int(round(i * 1080 / NB)), int(round((i + 1) * 1080 / NB))) for i in range(NB)]


def row_strip(im, xc, scale=SCALE):
    x0 = max(0, min(1920 - 2 * HALF, xc - HALF))
    return im.crop((x0, 0, x0 + 2 * HALF, 1080)).resize(
        (2 * HALF * scale, 1080 * scale), Image.NEAREST)


def draw_marks(d, x_left, y_top, scale, f):
    """在已贴好的条上画 6 条带界线 + 带号 + 缝列（条内 index 32）。"""
    for i, (y0, y1) in enumerate(bands()):
        yy = y_top + int(y0 * scale / 1080 * 1080) if False else y_top + y0 * scale
        d.line([(x_left, yy), (x_left + 2 * HALF * scale, yy)], fill=(90, 90, 90), width=1)
        d.text((x_left + 2, yy + 2), "b%d" % i, fill=(150, 220, 150), font=f)
    yy = y_top + 1080 * scale
    d.line([(x_left, yy), (x_left + 2 * HALF * scale, yy)], fill=(90, 90, 90), width=1)
    d.text((x_left + 2, yy + 2), "b%d" % NB, fill=(150, 220, 150), font=f)
    xs = x_left + 32 * scale
    d.line([(xs, y_top), (xs, y_top + 1080 * scale)], fill=(255, 60, 60), width=1)


def make_strip(name, rec, paths, scale=SCALE):
    f = font(13)
    rows = [(lab, p) for lab, p in paths if p and os.path.exists(p)]
    w = 2 * HALF * scale
    tot_w = w * 2 + GAP
    tot_h = len(rows) * (1080 * scale + LABEL) + LABEL
    canvas = Image.new("RGB", (tot_w, tot_h), (12, 12, 12))
    d = ImageDraw.Draw(canvas)
    d.text((3, 2), "%s  xl=%d xr=%d ｜ 条宽 64 列(缝居中 x=32) ｜ %d× 全高 ｜ 装配产物=%s ｜ %s"
           % (name, int(rec["xl"]), int(rec["xr"]), scale, rec["采用产物"], rec["分类_v2"]),
           fill=(255, 220, 80), font=f)
    y = LABEL
    for lab, p in rows:
        im = Image.open(p).convert("RGB")
        d.text((3, y + 3), lab, fill=(160, 200, 255), font=f)
        y += LABEL
        canvas.paste(row_strip(im, int(rec["xl"]), scale), (0, y))
        draw_marks(d, 0, y, scale, f)
        canvas.paste(row_strip(im, int(rec["xr"]), scale), (w + GAP, y))
        draw_marks(d, w + GAP, y, scale, f)
        y += 1080 * scale
        im.close()
    canvas.save(os.path.join(STRIP_DIR, "%s_缝条.png" % os.path.splitext(name)[0]))


PROF_W, PROF_H = 700, 300
PAD_T = 16


def col_mean(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    g = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    return g.mean(axis=0)


def make_profile(name, rec, before, after, out_path, card=False):
    f = font(11 if card else 12)
    im = Image.new("RGB", (PROF_W, PROF_H), (16, 16, 16))
    d = ImageDraw.Draw(im)
    xl, xr = int(rec["xl"]), int(rec["xr"])
    h = PROF_H - PAD_T - 16

    def X(c):
        return int(round(c / 1919.0 * (PROF_W - 1)))

    def Y(v):
        return PAD_T + int(round((255.0 - float(np.clip(v, 0, 255))) / 255.0 * h))
    # 扩展区底色（左/右）
    for x0, x1, col in ((0, X(xl), (34, 22, 22)), (X(xr), PROF_W - 1, (34, 22, 22))):
        d.rectangle([x0, PAD_T, x1, PAD_T + h], fill=col)
    for v in range(0, 256, 64):
        d.line([(0, Y(v)), (PROF_W - 1, Y(v))], fill=(48, 48, 48), width=1)
        d.text((2, Y(v) + 1), str(v), fill=(140, 140, 140), font=f)
    for c, lab in ((xl, "xl"), (xr, "xr")):
        d.line([(X(c), PAD_T), (X(c), PAD_T + h)], fill=(205, 60, 60), width=1)
        d.text((X(c) + 2, PAD_T + 1), lab, fill=(205, 60, 60), font=f)
    for cm, col in ((before, (185, 185, 185)), (after, (85, 170, 255))):
        if cm is None:
            continue
        d.line([(X(c), Y(cm[c])) for c in range(0, 1920, 2)], fill=col, width=1)
    d.text((2, 1), "全宽列均值剖面  灰=outpaint 原样／蓝=%s  扩展区加底色"
           % (rec["采用产物"] if not card else rec["采用产物"]), fill=(160, 200, 160), font=f)
    im.save(out_path)


def make_card(name, rec, paths):
    f = font(13)
    w = 2 * HALF * SCALE
    tot_w = max(w * 2 + GAP, PROF_W, 1920 // CARD_THUMB)
    th = 1080 // CARD_THUMB
    n_rows = len([1 for lab, p2 in paths if p2 and os.path.exists(p2)])
    tot_h = LABEL + th + LABEL + n_rows * (1080 * SCALE + LABEL) + (PROF_H + LABEL)
    canvas = Image.new("RGB", (tot_w, tot_h), (12, 12, 12))
    d = ImageDraw.Draw(canvas)
    xl, xr = int(rec["xl"]), int(rec["xr"])
    # ① 整图 1/3 缩略 + 缝列 + 扩展区边界框
    y = 0
    d.text((3, y + 2), "① 整图 1/%d 缩略（红线=两条缝列；黄框=扩展区边界，供判断扩展区语义）｜%s ｜%s"
           % (CARD_THUMB, name, rec["分类_v2"]), fill=(255, 220, 80), font=f)
    y += LABEL
    src = next((p for lab, p in paths if p and os.path.exists(p)), None)
    im = Image.open(src).convert("RGB").resize((1920 // CARD_THUMB, th), Image.LANCZOS)
    canvas.paste(im, (0, y))
    for c in (xl, xr):
        xx = int(round(c / 1919.0 * (1920 // CARD_THUMB - 1)))
        d.line([(xx, y), (xx, y + th)], fill=(255, 60, 60), width=1)
    d.rectangle([0, y, int(xl / 1919.0 * (1920 // CARD_THUMB - 1)), y + th], outline=(220, 200, 60))
    d.rectangle([int(xr / 1919.0 * (1920 // CARD_THUMB - 1)), y,
                 (1920 // CARD_THUMB - 1), y + th], outline=(220, 200, 60))
    im.close()
    y += th
    # ② 全高 2× 缝条
    d.text((3, y + 2), "② 全高 %d× 缝条（左缝 | 右缝）  条宽 64 列，缝在条内 x=32（红）；带号 b0–b6" % SCALE,
           fill=(255, 220, 80), font=f)
    y += LABEL
    rows = [(lab, p) for lab, p in paths if p and os.path.exists(p)]
    for lab, p in rows:
        im = Image.open(p).convert("RGB")
        d.text((3, y + 3), lab, fill=(160, 200, 255), font=f)
        canvas.paste(row_strip(im, xl), (0, y))
        draw_marks(d, 0, y, SCALE, f)
        canvas.paste(row_strip(im, xr), (w + GAP, y))
        draw_marks(d, w + GAP, y, SCALE, f)
        y += 1080 * SCALE
        im.close()
    # ③ 剖面
    d.text((3, y + 2), "③ 全宽列均值剖面（判色调漂移：灰=outpaint 原样／蓝=装配产物；扩展区加底色）",
           fill=(255, 220, 80), font=f)
    y += LABEL
    before = col_mean(os.path.join(OUTPAINT, name))
    after_p = next((p for lab, p in paths if lab.startswith(("tonematch", "geo"))), None)
    after = col_mean(after_p) if after_p else None
    # 直接在主画布上画剖面
    d2 = d
    h = PROF_H - PAD_T - 16

    def X(c):
        return int(round(c / 1919.0 * (PROF_W - 1)))

    def Y(v):
        return y + PAD_T + int(round((255.0 - float(np.clip(v, 0, 255))) / 255.0 * h))
    for x0, x1 in ((0, X(xl)), (X(xr), PROF_W - 1)):
        d2.rectangle([x0, y + PAD_T, x1, y + PAD_T + h], fill=(34, 22, 22))
    for v in range(0, 256, 64):
        d2.line([(0, Y(v)), (PROF_W - 1, Y(v))], fill=(48, 48, 48), width=1)
    for c in (xl, xr):
        d2.line([(X(c), y + PAD_T), (X(c), y + PAD_T + h)], fill=(205, 60, 60), width=1)
    for cm, col in ((before, (185, 185, 185)), (after, (85, 170, 255))):
        if cm is not None:
            d2.line([(X(c), Y(cm[c])) for c in range(0, 1920, 2)], fill=col, width=1)
    canvas.save(os.path.join(CARD_DIR, "%s_三格卡.png" % os.path.splitext(name)[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", default="all", choices=["all", "strips", "profiles", "cards"])
    ap.add_argument("--names", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    recs = [r for r in csv.DictReader(open(DISP, encoding="utf-8"), delimiter="\t")
            if r.get("统一名")]
    if args.names:
        want = {n.strip() for n in args.names.split(",")}
        recs = [r for r in recs if r["统一名"] in want]
    if args.limit:
        recs = recs[:args.limit]
    for d0 in (STRIP_DIR, PROF_DIR, CARD_DIR):
        os.makedirs(d0, exist_ok=True)

    cnt = collections.Counter()
    fails, t0 = [], time.time()
    for i, rec in enumerate(recs):
        nm = rec["统一名"]
        paths = [("outpaint(LaMa)", os.path.join(OUTPAINT, nm))]
        pt = os.path.join(TONEMATCH, nm)
        if os.path.exists(pt):
            paths.append(("tonematch", pt))
        pg = os.path.join(GEO, nm)
        if os.path.exists(pg):
            paths.append(("geo(几何延展)", pg))
        try:
            if args.what in ("all", "strips"):
                dst = os.path.join(STRIP_DIR, "%s_缝条.png" % os.path.splitext(nm)[0])
                if args.force or not os.path.exists(dst):
                    make_strip(nm, rec, paths); cnt["strips"] += 1
            if args.what in ("all", "profiles"):
                dst = os.path.join(PROF_DIR, "%s_剖面.png" % os.path.splitext(nm)[0])
                if args.force or not os.path.exists(dst):
                    before = col_mean(os.path.join(OUTPAINT, nm))
                    ap_ = next((p for lab, p in paths if lab.startswith(("tonematch", "geo"))), None)
                    after = None
                    if ap_:
                        after = col_mean(ap_)
                    make_profile(nm, rec, before, after, dst)
                    cnt["profiles"] += 1
            if args.what in ("all", "cards"):
                dst = os.path.join(CARD_DIR, "%s_三格卡.png" % os.path.splitext(nm)[0])
                if args.force or not os.path.exists(dst):
                    make_card(nm, rec, paths); cnt["cards"] += 1
        except Exception as e:
            fails.append((nm, repr(e)))
            print("  FAIL %s %r" % (nm, e), flush=True)
        if (i + 1) % 50 == 0:
            print("  [%d/%d] %s  %.1fs" % (i + 1, len(recs), dict(cnt), time.time() - t0), flush=True)

    def size(d0):
        fs = [f for f in os.listdir(d0) if f.endswith(".png")]
        return len(fs), sum(os.path.getsize(os.path.join(d0, f)) for f in fs) / 1048576.0
    L = ["证据 v2 补齐汇总（只读 outpaint/outpaint_tonematch/outpaint_geo*，只写 证据\\*）",
         "  对象 %d 件（来自 须处置清单_v2.tsv）｜ 本轮新增 strips=%d profiles=%d cards=%d ｜ 失败 %d"
         % (len(recs), cnt["strips"], cnt["profiles"], cnt["cards"], len(fails))]
    for d0, lab in ((STRIP_DIR, "缝条_v2"), (PROF_DIR, "色调剖面_v2"), (CARD_DIR, "三格卡")):
        n, mb = size(d0)
        L.append("  %-12s %4d 张 ｜ %7.1f MiB ｜ %s" % (lab, n, mb, d0))
    n1, mb1 = size(os.path.join(EVID, "缝条"))
    n2, mb2 = size(os.path.join(EVID, "色调剖面"))
    L.append("  （旧证据 缝条 %d 张 / %.1f MiB、色调剖面 %d 张 / %.1f MiB 原样保留）" % (n1, mb1, n2, mb2))
    L.append("  缝条_v2 尺度：一律 2×、全高 1080、条宽 64 列（缝居中 x=32）、左/右并列；每张标 统一名/xl/xr/装配产物/分类 + 6 条带界线与带号 b0–b6")
    L.append("  三格卡：① 整图 1/3 缩略（两条缝列红 + 扩展区边界黄框）② 全高 2× 缝条 ③ 全宽列均值剖面（灰=原样/蓝=装配产物，扩展区加底色）")
    if fails:
        L.append("  失败件: " + ", ".join(x[0] for x in fails[:20]))
    txt = "\n".join(L)
    open(SUM_TXT, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)


if __name__ == "__main__":
    main()
