# -*- coding: utf-8 -*-
r"""E5 工具：候选几何实测（相对盘面 Ø108 的归一化口径）。
输出 TSV + 控制台表：环外径、字形 bbox、条宽 / 间隙 / 条高、圆角估计、盘面圆度、外发光溢出量。
用法：python _measure_cands.py
"""
import os, glob, json, math
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
CAND = os.path.join(BASE, "候选")
CAND_UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # UI组
REF = os.path.join(CAND_UI, "krkr", "assets", "ui", "x_ui_pbkick_off.png")
DER = os.path.join(CAND_UI, "krkr", "assets", "ui", "x_ui_pbkick_pause_off.png")


def bbox(pred, w, h):
    xs = [x for x in range(w) if any(pred(x, y) for y in range(h))]
    ys = [y for y in range(h) if any(pred(x, y) for x in range(w))]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def analyse(im):
    """★ 字形判定不能只按颜色阈值（实测踩坑：环色 (146,159,183) 与字色 (167,203,241) 同族，
    阈值一放就把环当成字形）。改为：以「盘心圆内像素的中位色」当盘面底色，偏离它的才是字形。"""
    im = im.convert("RGBA")
    W, H = im.size
    a = im.getchannel("A").load()
    px = im.load()

    def ring(x, y):
        return a[x, y] >= 250

    rb = bbox(ring, W, H)
    if rb is None:
        return dict(size=[W, H], ring_bbox=None), None
    cx = (rb[0] + rb[2]) / 2.0
    cy = (rb[1] + rb[3]) / 2.0
    R = max(rb[2] - rb[0] + 1, rb[3] - rb[1] + 1) / 2.0

    # 盘面底色中位色：取 0.55R–0.90R 的**环带**（该环带内只有盘面，绝无字形 ——
    # 若采盘心圆，字形面积可占 76%，中位色会变成字色，反而把盘面判成字形；实测踩过）
    samp = []
    for y in range(max(0, int(cy - R)), min(H, int(cy + R) + 1)):
        for x in range(max(0, int(cx - R)), min(W, int(cx + R) + 1)):
            d = math.hypot(x - cx, y - cy)
            if 0.55 * R <= d <= 0.90 * R and a[x, y] >= 200:
                samp.append(px[x, y][:3])
    if not samp:
        return dict(size=[W, H], ring_bbox=rb), None
    samp.sort(key=lambda c: c[0] + c[1] + c[2])
    base = samp[len(samp) // 2]

    def glyph(x, y):
        if a[x, y] < 190:
            return False
        if math.hypot(x - cx, y - cy) > 0.55 * R:     # 只在盘心区找字形（排除环与发光）
            return False
        r, g, b = px[x, y][:3]
        return math.dist((r, g, b), base) > 18

    gb = bbox(glyph, W, H)
    ab = bbox(lambda x, y: a[x, y] > 0, W, H)
    out = dict(size=[W, H], ring_bbox=rb, disc_center=[cx, cy], disc_base_rgb=list(base),
               ring_d=int(round(max(rb[2] - rb[0] + 1, rb[3] - rb[1] + 1))),
               glyph_bbox=gb, content_bbox=ab)
    if gb is None:
        return out, None
    k = 108.0 / out["ring_d"]                      # 归一化倍率：环外径 → 108
    gx0, gy0, gx1, gy1 = gb
    gw = (gx1 - gx0 + 1) * k
    gh = (gy1 - gy0 + 1) * k
    # 逐列投影找两条（用原始分辨率扫描，再乘 k）
    colsum = []
    for x in range(gx0, gx1 + 1):
        colsum.append(sum(1 for y in range(gy0, gy1 + 1) if glyph(x, y)))
    runs, cur = [], None
    for i, v in enumerate(colsum):
        if v > 0 and cur is None:
            cur = i
        elif v == 0 and cur is not None:
            runs.append((cur + gx0, i - 1 + gx0)); cur = None
    if cur is not None:
        runs.append((cur + gx0, len(colsum) - 1 + gx0))
    runs = [r for r in runs if (r[1] - r[0] + 1) > 2]
    bars = [(r[1] - r[0] + 1) * k for r in runs]
    gap = ((runs[1][0] - runs[0][1] - 1) * k) if len(runs) >= 2 else None
    # 圆角尺度：条顶行墨迹宽相对条宽的每侧内缩（圆角 r 的等效尺度）
    rc = None
    if runs:
        x0r, x1r = runs[0]
        ytop = min(y for y in range(gy0, gy1 + 1) if any(glyph(x, y) for x in range(x0r, x1r + 1)))
        wtop_orig = sum(1 for x in range(x0r, x1r + 1) if glyph(x, ytop))
        wbar = x1r - x0r + 1
        if wtop_orig < wbar:
            rc = ((wbar - wtop_orig) / 2.0) * k
    # 外发光溢出：内容 bbox 四角到盘心的最远距离（归一化后），>59.5 即被 119 画布裁掉
    overflow = None
    if ab:
        r_needed = max(math.hypot(ab[0] - cx, ab[1] - cy), math.hypot(ab[2] - cx, ab[1] - cy),
                       math.hypot(ab[0] - cx, ab[3] - cy), math.hypot(ab[2] - cx, ab[3] - cy)) * k
        overflow = round(r_needed, 1)
    out.update(k=round(k, 4),
               norm_bar_w=[round(b, 1) for b in bars],
               norm_gap=None if gap is None else round(gap, 1),
               norm_group_w=round(gw, 1), norm_h=round(gh, 1),
               norm_toprow_inset=None if rc is None else round(rc, 2),
               glow_corner_radius_after_norm=overflow, canvas_half=59.5)

    # ── 环的可读性：沿四个轴向从 0.80R 扫到 1.02R，取亮度最低点当环芯；
    #    环厚 = 亮度低于「盘面亮度−25」的采样数（步长 0.25）换算成**归一化单位（盘面 Ø108）**。
    def lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    fillL = lum(base)
    samples = []
    for ang in (-90, 0, 90, 180):
        rad = math.radians(ang)
        for i in range(0, int(0.22 * R / 0.25) + 1):
            d = (0.80 * R) + i * 0.25
            x = int(round(cx + d * math.cos(rad))); y = int(round(cy + d * math.sin(rad)))
            # ★ 只取 alpha>=200 的采样点：边缘半透明像素常带暗 RGB（未预乘），
            #   纳入会把「环ΔL」污染成假的高对比（实测 C13 因此量到 220）。
            if 0 <= x < W and 0 <= y < H and a[x, y] >= 200:
                samples.append((d, px[x, y][:3], a[x, y]))
    if samples:
        dmin, cmin, amin = min(samples, key=lambda t: lum(t[1]))
        thick = sum(1 for t in samples if lum(t[1]) < fillL - 25) * 0.25 * k
        out.update(disc_fill_lum=round(fillL, 1),
                   ring_rgb_at_min=list(cmin), ring_lum=round(lum(cmin), 1),
                   ring_delta_lum=round(fillL - lum(cmin), 1),
                   ring_r_at_min_norm=round(dmin * k, 2),
                   ring_thickness_norm=round(thick, 2))
    return out, k


def main():
    items = [("播放键_off（基准）", REF), ("派生版暂停_off（基准）", DER)]
    for f in sorted(glob.glob(os.path.join(CAND, "pause_AI_cand_C*.png"))):
        items.append((os.path.basename(f), f))
    rows = []
    print("%-34s %-8s %-8s %-24s %s" % ("件", "环外径", "归一化k", "条宽/间隙/组宽/条高", "环ΔL / 环芯r(归一) / 环厚 / 盘面L / 发光外接r"))
    for name, p in items:
        im = Image.open(p)
        if "A" not in im.mode:
            print("%-34s RGB（无 alpha）— 跳过" % name); continue
        r, k = analyse(im)
        rows.append((name, r))
        print("%-34s %-8s %-8s %-24s %s" % (
            name, r.get("ring_d"), r.get("k"),
            "%s/%s/%s/%s" % (r.get("norm_bar_w"), r.get("norm_gap"), r.get("norm_group_w"), r.get("norm_h")),
            "%s / %s / %s / %s / %s" % (r.get("ring_delta_lum"), r.get("ring_r_at_min_norm"),
                                         r.get("ring_thickness_norm"), r.get("disc_fill_lum"),
                                         r.get("glow_corner_radius_after_norm"))))
    out = os.path.join(BASE, "候选", "_几何实测.json")
    json.dump([{"name": n, "m": r} for n, r in rows], open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n-> ", out)
    print("\n规格（接口冻结 §A.1 定稿）：条宽 16 / 间隙 16 / 组宽 48 / 条高 54 / 圆角 2 / 环外径 108")


if __name__ == "__main__":
    main()
