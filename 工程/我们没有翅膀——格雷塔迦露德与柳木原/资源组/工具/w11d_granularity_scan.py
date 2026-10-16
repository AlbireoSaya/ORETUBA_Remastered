# -*- coding: utf-8 -*-
r"""
W11d / ISSUE-20260918-06 · 任务2b：系统UI 全量「粒度不同被误并」扫描
====================================================================
背景：W11c 把 `ss_bg1`–`ss_bg5` 归并为一组，但两候选粒度不同
      （`ot` 800×600 场景选择底板 vs `otv` 960×1012 场景选择整页）。
      本脚本按同一判据全量复扫 系统UI 的 1,551 组。

判据（三段式，全部实算，不靠命名猜测）：
  A. 组内候选 ≥ 2；
  B. 存在候选对 (小 P, 大 Q) 同时满足：
     B1 宽高比相对差 > 20%（远超规格 §3.3 的 2% 阈值）且 面积比 Q/P ≥ 1.5
        （→ 版式与尺度同时悬殊；全 499 个多候选组中仅 7 组命中）；
     B2 尺度门槛：P 面积 ≥ 10,000 px 且 Q 面积 ≥ 100,000 px
        （排除 `ec2_name` 96×19 / `ec3_name` 100×19 这类小标签）；
  C. **内容对应（佐证）**：Q 中存在一条**不等于整幅**的横带，其按 P 的尺寸重采样后
     与 P 的灰度 MAD ≤ 50——即 Q 的某一部分就是 P 的画面，Q 另含 P 所无的 UI 面板
     → Q 是「整页」、P 是「底板/局部」→ 粒度不同被误并。

  C 的对照（见输出 cross_control）：同一 P 与「同族其它 ss_bg 的 Q」交叉比，
  实测 34.95–58.12，与正样本 14.62–46.78 区间重叠 → **C 单独不足以判定**，
  仅作佐证；**判定以 B1∧B2 为准**（B 已把范围收敛到 5 组）。

只读源；结果写 子代理工作区\...\W11d\_granularity.json
"""
import os, sys, json, csv
from PIL import Image, ImageChops, ImageStat

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
KRKR = os.path.join(BASE, "krkr素材库")
UNI = os.path.join(BASE, "美术统一")
OUT = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20260918-06\W11d\_granularity.json"

SOURCES = ["ot", "ota", "otp", "otv"]
KINDS = ["sys", "etc"]
PFX = ("otv_", "ota_", "otp_", "ot_")
AR_THR = 0.20          # 判据 B：宽高比相对差阈值
RATIO_THR = 1.5        # 判据 B：面积比阈值
MAD_THR = 50.0         # 判据 C（佐证）：内容对应 MAD 阈值
P_AREA_MIN = 10000     # 判据 B2
Q_AREA_MIN = 100000    # 判据 B2


def norm(stem):
    s = stem.lower()
    for p in PFX:
        if s.startswith(p):
            return s[len(p):]
    return s


def collect():
    groups = {}
    for s in SOURCES:
        for k in KINDS:
            d = os.path.join(KRKR, s, k)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if fn.lower().endswith(".png"):
                    groups.setdefault(norm(fn[:-4]), []).append((s, k, fn[:-4], os.path.join(d, fn)))
    return groups


def mad(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a.convert("RGB"), b.convert("RGB"))).mean) / 3.0


def best_band_mad(P_path, Q_path, step=8):
    """在 Q 中找一条横带（高度不等于 Q 全高），缩放到 P 尺寸后与 P 比灰度 MAD。
    返回 (best_mad, band_h, q_h)。"""
    P = Image.open(P_path).convert("RGB")
    Q = Image.open(Q_path).convert("RGB")
    pw, ph = P.size
    qw, qh = Q.size
    best = (1e9, 0)
    # 候选带高：由 P 的宽高比与 Q 宽推出（等比缩放）附近 ±40% 扫描
    base = int(round(ph * qw / float(pw)))
    lo = max(8, int(base * 0.55))
    hi = min(qh, int(base * 1.45))
    for hb in range(lo, hi + 1, step):
        for y0 in (0, qh - hb):
            c = Q.crop((0, y0, qw, y0 + hb)).resize((pw, ph), Image.BILINEAR)
            d = mad(P, c)
            if d < best[0]:
                best = (d, hb)
    P.close(); Q.close()
    return round(best[0], 2), best[1], qh


def main():
    groups = collect()
    print("组数 =", len(groups), " 图像 =", sum(len(v) for v in groups.values()))

    man = {}
    with open(os.path.join(UNI, "清单_系统UI.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            man[r["统一名"][:-4]] = r
    print("清单_系统UI 组数 =", len(man), " 仅脚本有:", len(set(groups) - set(man)),
          " 仅清单有:", len(set(man) - set(groups)))

    multi, bpairs, hits, controls = 0, [], [], []
    dist = []
    for stem, cands in sorted(groups.items()):
        if len(cands) < 2:
            continue
        multi += 1
        meta = []
        for s, k, st, p in cands:
            im = Image.open(p); w, h = im.size; md = im.mode; im.close()
            meta.append(dict(src=s, kind=k, stem=st, path=p, w=w, h=h, mode=md,
                             area=w * h, ar=w / float(h)))
        # 记录本组最大 AR 差 / 最大面积比（用于分布统计）
        maxard = maxar = 0.0
        for i in range(len(meta)):
            for j in range(i + 1, len(meta)):
                a, b = meta[i], meta[j]
                ard = abs(a["ar"] - b["ar"]) / min(a["ar"], b["ar"])
                rr = max(a["area"], b["area"]) / float(min(a["area"], b["area"]))
                maxard = max(maxard, ard); maxar = max(maxar, rr)
                P, Q = (a, b) if a["area"] <= b["area"] else (b, a)
                if ard > AR_THR and rr >= RATIO_THR:
                    bpairs.append((stem, ard, rr, P, Q))
        dist.append((stem, round(maxard, 4), round(maxar, 3)))

    print("多候选组 =", multi, " 通过判据B的候选对 =", len(bpairs))

    # 判据 C
    for stem, ard, rr, P, Q in bpairs:
        bm, bh, qh = best_band_mad(P["path"], Q["path"])
        rec = dict(stem=stem, ard=round(ard, 4), ratio=round(rr, 3),
                   small="%s:%s %dx%d" % (P["src"], P["stem"], P["w"], P["h"]),
                   large="%s:%s %dx%d" % (Q["src"], Q["stem"], Q["w"], Q["h"]),
                   small_area=P["area"], large_area=Q["area"],
                   best_band_mad=bm, band_h=bh, large_h=qh,
                   band_is_sub=(bh < qh * 0.98),
                   size_ok=(P["area"] >= P_AREA_MIN and Q["area"] >= Q_AREA_MIN),
                   hit=(bm <= MAD_THR and bh < qh * 0.98
                        and P["area"] >= P_AREA_MIN and Q["area"] >= Q_AREA_MIN),
                   in_manifest=stem in man,
                   manifest_sel=(man[stem]["选中源"] + ":" + man[stem]["选中原名"]) if stem in man else "")
        (hits if rec["hit"] else controls).append(rec)
        print("  %-14s ARdiff=%5.1f%% ratio=%.2f  best_band_MAD=%6.2f band_h=%-5d Qh=%-5d sub=%s -> %s" % (
            stem, ard * 100, rr, bm, bh, qh, rec["band_is_sub"], "HIT" if rec["hit"] else "no"))

    # 对照：把 ss_bg1 的 P 与其它 ss_bg 的 Q 交叉比（负样本）
    xctl = []
    p1 = None
    for stem, cands in groups.items():
        if stem == "ss_bg1":
            for s, k, st, p in cands:
                if s == "ot":
                    p1 = p
    if p1:
        for other in ("ss_bg2", "ss_bg3", "ss_bg4", "ss_bg5"):
            for s, k, st, p in groups.get(other, []):
                if s == "otv":
                    bm, bh, qh = best_band_mad(p1, p)
                    xctl.append(dict(pair="ot:ss_bg1 vs %s:%s" % (s, st), best_band_mad=bm, band_h=bh))
                    print("  负样本对照 %s best_band_MAD=%.2f" % (st, bm))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dict(stats=dict(groups=len(groups), images=sum(len(v) for v in groups.values()),
                                  multi=multi, bpairs=len(bpairs), hits=len(hits),
                                  ar_thr=AR_THR, ratio_thr=RATIO_THR, mad_thr=MAD_THR),
                       hits=hits, controls=controls, cross_control=xctl,
                       dist_top=sorted(dist, key=lambda x: -x[1])[:25],
                       dist_top_ratio=sorted(dist, key=lambda x: -x[2])[:25]),
                  f, ensure_ascii=False, indent=1)
    print("命中:", len(hits), "->", OUT)


if __name__ == "__main__":
    main()