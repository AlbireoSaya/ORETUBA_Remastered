# -*- coding: utf-8 -*-
r"""
make_seam_strips.py —— 重出接缝验收证据「全高缝条」（ISSUE-20260928-02 · 1028 补边续作 · 交付物 5）

为什么重出
    上一批 `证据\pilot_对照图\*_三联.png` 里的接缝放大条只取 y∈[483,598]（= 高度的 10.6%），
    看不见上/下段的接缝与色调漂移 ⇒ **不足以做逐件目视**（vision 验收的结论之一）。

本脚本产出
    对 **HARD + MID-补充 + MID** 件，逐件出一张 `证据\缝条\<统一名>_缝条.png`：
        · 左缝条 + 右缝条 **全高**
        · 缝条 = [缝-32, 缝+32) 共 64 列（缝恰好在条内 index 32，居中，便于定位）
        · 宽度可选 1:1 或 2×（HARD 用 2×，其余 1:1）
        · 有修正产物的件按「上=outpaint 原样（LaMa）／下=修正后」两行叠出，直接判 before/after
          （色调匹配 pass 覆盖 349 件、几何延展 3 件；其余件只有 outpaint 一行）
    坐标口径同 `quality_axes.out_seams`（逐件按真实源尺寸算，不用 1440）。

产物
    证据\缝条\<统一名>_缝条.png     逐件
    证据\缝条_汇总.txt              件数 / 尺度 / 体量 / 覆盖说明

用法
    python make_seam_strips.py                 # HARD+MID（幂等跳过已有）
    python make_seam_strips.py --classes HARD  # 只 HARD
    python make_seam_strips.py --scale1 1      # 全部 1:1
    python make_seam_strips.py --force
"""
import sys, os, csv, time, argparse

WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image
from quality_axes import out_seams, AXES_TSV, DISP_TSV

OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
TONEMATCH = os.path.join(ISSUE_DIR, "outpaint_tonematch")
GEO = os.path.join(ISSUE_DIR, "outpaint_geo")
STRIP_DIR = os.path.join(ISSUE_DIR, "证据", "缝条")
SUM_TXT = os.path.join(ISSUE_DIR, "证据", "缝条_汇总.txt")

HALF = 32          # 缝两侧各 32 列
GAP = 6            # 左/右条之间、行与行之间的分隔
LABEL = 16         # 每行上方的行标题高度


def strip_of(im, x_center, half=HALF):
    W, H = im.size
    x0 = max(0, min(W - 2 * half, x_center - half))
    return im.crop((x0, 0, x0 + 2 * half, H))


def compose(name, rows, scale):
    """rows = [(标签, 图片)]（均为 1920×1080）。返回合成图。"""
    strips = []
    for lab, im in rows:
        strips.append((lab, strip_of(im, XS[name][0]), strip_of(im, XS[name][1])))
    w = 2 * HALF * scale
    tot_w = w * 2 + GAP
    tot_h = len(strips) * (1080 * scale + LABEL)
    canvas = Image.new("RGB", (tot_w, tot_h), (12, 12, 12))
    from PIL import ImageDraw, ImageFont
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 13)
    except Exception:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(canvas)
    y = 0
    for lab, l, r in strips:
        d.text((3, y + 2), lab, fill=(255, 220, 80), font=font)
        y += LABEL
        if scale != 1:
            l = l.resize((l.width * scale, l.height * scale), Image.NEAREST)
            r = r.resize((r.width * scale, r.height * scale), Image.NEAREST)
        canvas.paste(l, (0, y))
        canvas.paste(r, (w + GAP, y))
        y += 1080 * scale
    return canvas


XS = {}     # name -> (xl, xr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", default="HARD,MID-补充,MID")
    ap.add_argument("--scale-hard", type=int, default=2)
    ap.add_argument("--scale-mid", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    want = {c.strip() for c in args.classes.split(",") if c.strip()}

    # 分类来自 质量轴.tsv（分类列与处置列都在里面）
    rows = list(csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t"))
    jobs = [r for r in rows if r["分类"] in want]
    for r in jobs:
        XS[r["统一名"]] = (int(r["xl"]), int(r["xr"]))
    if args.limit:
        jobs = jobs[:args.limit]
    os.makedirs(STRIP_DIR, exist_ok=True)
    print("缝条对象 %d 件（分类 %s）｜ 尺度 HARD=%d× 其余=%d×"
          % (len(jobs), ",".join(sorted(want)), args.scale_hard, args.scale_mid), flush=True)

    # 源尺寸（决定几何）——用 outpaint 的产物尺寸恒为 1920×1080，几何已在 质量轴.tsv 的 xl/xr
    n_new = n_skip = 0
    fails, t0 = [], time.time()
    for i, r in enumerate(jobs):
        nm = r["统一名"]
        dst = os.path.join(STRIP_DIR, "%s_缝条.png" % os.path.splitext(nm)[0])
        if not args.force and os.path.exists(dst):
            n_skip += 1
            continue
        try:
            scale = args.scale_hard if r["分类"] == "HARD" else args.scale_mid
            imgs = []
            p = os.path.join(OUTPAINT, nm)
            if not os.path.exists(p):
                raise AssertionError("outpaint 产物缺失")
            imgs.append(("outpaint(LaMa)  缝在条内 x=32", Image.open(p).convert("RGB")))
            p2 = os.path.join(TONEMATCH, nm)
            if os.path.exists(p2):
                imgs.append(("tonematch  缝在条内 x=32", Image.open(p2).convert("RGB")))
            p3 = os.path.join(GEO, nm)
            if os.path.exists(p3):
                imgs.append(("geo-edgeclamp  缝在条内 x=32", Image.open(p3).convert("RGB")))
            compose(nm, imgs, scale).save(dst)
            for _, im in imgs:
                im.close()
            n_new += 1
            if (i + 1) % 25 == 0:
                print("  [%d/%d] %d 新出  %.1fs" % (i + 1, len(jobs), n_new, time.time() - t0),
                      flush=True)
        except Exception as e:
            fails.append((nm, repr(e)))
            print("  FAIL %s %r" % (nm, e), flush=True)

    files = [f for f in os.listdir(STRIP_DIR) if f.endswith(".png")]
    tot = sum(os.path.getsize(os.path.join(STRIP_DIR, f)) for f in files)
    import collections
    cnt = collections.Counter(r["分类"] for r in jobs)
    lines = ["缝条证据汇总",
             "  本轮出 %d 件（跳过已有 %d，失败 %d）｜ 目录内共 %d 张 ｜ 体量 %.1f MiB"
             % (n_new, n_skip, len(fails), len(files), tot / 1048576),
             "  尺度：HARD ×%d，其余 ×%d ｜ 条宽 %d 列（缝居中于条内 x=32）｜ 全高 1080"
             % (args.scale_hard, args.scale_mid, 2 * HALF),
             "  分类构成: " + " / ".join("%s=%d" % (k, cnt[k]) for k in sorted(cnt)),
             "  行数：有 tonematch 产物加 1 行、有 geo 产物再加 1 行 ⇒ 直接判 before/after"]
    if fails:
        lines.append("  失败: " + ", ".join(x[0] for x in fails))
    txt = "\n".join(lines)
    open(SUM_TXT, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)


if __name__ == "__main__":
    main()
