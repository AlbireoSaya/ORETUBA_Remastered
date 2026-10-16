# -*- coding: utf-8 -*-
"""
W11b · CG 与场景背景（pic）六源统一
规格：资源组\美术统一_规格.md（v1.0）
Issue：ISSUE-20260918-06

流程：
  1. 只读枚举 6 源 pic 目录全部文件
  2. 归一化命名（去源前缀 + 小写），按归一化 stem 分组（§二.2 / §三.1）
  3. 分片背景（bgNN / bgNNa 的 _0.._7 八片）以「组」为单位整组同源
  4. 组内选优：w*h 最大 > w 最大 > 源优先级 ot>otr>ota>otp>otv>np（§3.2）
  5. 分类（single / same_res_same / same_res_diff / diff_res_same_drawing / diff_res_diff_drawing）
  6. 宽高比感知的内容相似度抽检（§3.3 高风险组）+ np 独立素材配对尝试（§四）
  7. 输出 清单 / 待复核 / 统一图像（复制，原字节）
  8. 自证 7 项

用法：
  python unify_pic.py --analyze   # 只分析，不写产物
  python unify_pic.py             # 写产物
"""
import os, re, sys, csv, hashlib, shutil, random
from collections import defaultdict, Counter

from PIL import Image, ImageChops

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
ART = os.path.join(PROJ, "资源组", "美术")
OUT_ROOT = os.path.join(PROJ, "资源组", "美术统一")
OUT_IMG = os.path.join(OUT_ROOT, "CG背景")

SOURCES = ["ot", "ota", "otp", "otr", "otv", "np"]
PRIO = {"ot": 0, "otr": 1, "ota": 2, "otp": 3, "otv": 4, "np": 5}

RE_SPLIT = re.compile(r"^(bg\d+[a-z]?)_(\d+)$")
AR_TOL = 0.02          # 宽高比相对差阈值（§3.3）
SIM_HIGH = 0.90        # 同宽高比组的内容高风险阈值
SIM_PAIR = 0.95        # np 内容配对阈值

ANALYZE_ONLY = "--analyze" in sys.argv

# ------------------------------------------------------------------ 工具
_sig_cache = {}


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fam_of(stem):
    s = stem[2:] if stem.startswith("e_") else stem
    m = re.match(r"^([a-z]+)", s)
    return m.group(1) if m else ""


def sig(path, n):
    """宽高比感知签名：等比缩放到宽 n，中心裁切/补黑到 n×n 灰度"""
    key = (path, n)
    if key in _sig_cache:
        return _sig_cache[key]
    with Image.open(path) as im:
        g = im.convert("L")
        w, h = g.size
        nh = max(1, round(h * n / w))
        g = g.resize((n, nh), Image.BILINEAR)
        if nh > n:
            top = (nh - n) // 2
            g = g.crop((0, top, n, top + n))
        elif nh < n:
            c = Image.new("L", (n, n), 0)
            c.paste(g, (0, (n - nh) // 2))
            g = c
    _sig_cache[key] = g
    return g


def sim(p1, p2, n=64):
    a, b = sig(p1, n), sig(p2, n)
    hist = ImageChops.difference(a, b).histogram()
    tot = sum(hist)
    mean = sum(i * c for i, c in enumerate(hist)) / tot
    return 1.0 - mean / 255.0


# ------------------------------------------------------------------ 1. 枚举
records = []
by_stem = defaultdict(list)

for src in SOURCES:
    d = os.path.join(LIB, src, "pic")
    if not os.path.isdir(d):
        raise SystemExit("MISSING DIR " + d)
    seen = set()
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".png"):
            print("NON-PNG SKIPPED:", src, fn)
            continue
        raw = fn[:-4]
        if not raw.startswith(src + "_"):
            raise SystemExit("UNEXPECTED PREFIX: %s/%s" % (src, fn))
        stem = raw[len(src) + 1:].lower()
        if stem in seen:
            raise SystemExit("DUPLICATE STEM in %s: %s" % (src, stem))
        seen.add(stem)
        p = os.path.join(d, fn)
        with Image.open(p) as im:
            w, h = im.size
            mode = im.mode
        rec = dict(src=src, raw=raw, stem=stem, w=w, h=h, mode=mode,
                   bytes=os.path.getsize(p), md5=md5_of(p),
                   rel="%s/pic/%s" % (src, fn), path=p)
        records.append(rec)
        by_stem[stem].append(rec)

print("== 1 枚举 == 文件 %d ; 归一化组数 %d" % (len(records), len(by_stem)))
for s in SOURCES:
    print("   %-4s %d" % (s, sum(1 for r in records if r["src"] == s)))

# ---------------------------------------------------- 2. 角色代号族（chr 目录）
charfam = set()
for src in SOURCES:
    d = os.path.join(LIB, src, "chr")
    if not os.path.isdir(d):
        continue
    for fn in os.listdir(d):
        raw = fn[:-4].lower()
        if raw.startswith(src + "_"):
            raw = raw[len(src) + 1:]
        if raw.startswith("st_"):
            raw = raw[3:]
        f = fam_of(raw)
        if f:
            charfam.add(f)

# ------------------------------------------------------------ 3. 分片组选源
split_groups = defaultdict(lambda: defaultdict(dict))
for stem, cands in by_stem.items():
    m = RE_SPLIT.match(stem)
    if m:
        for r in cands:
            split_groups[m.group(1)][r["src"]][int(m.group(2))] = r

split_choice, split_detail = {}, {}
for base, persrc in split_groups.items():
    best = None
    detail = {}
    for src, pieces in persrc.items():
        area = max(r["w"] * r["h"] for r in pieces.values())
        mw = max(r["w"] for r in pieces.values())
        detail[src] = dict(n=len(pieces), area=area, w=mw,
                           dims=sorted({(r["w"], r["h"]) for r in pieces.values()}),
                           idxs=sorted(pieces))
        key = (area, mw, -PRIO[src])
        if best is None or key > best[0]:
            best = (key, src)
    split_choice[base] = best[1]
    split_detail[base] = detail

print("\n== 3 分片组（bg 系）整组选源 ==")
for base in sorted(split_groups):
    print("   %-8s -> %-4s | %s" % (base, split_choice[base],
          " ".join("%s:n=%d%s" % (s, v["n"], v["dims"]) for s, v in sorted(split_detail[base].items()))))

# -------------------------------------------------------- 4. 分类 / 选优
def classify_group(cands):
    if len(cands) == 1:
        return "single"
    dims = {(c["w"], c["h"]) for c in cands}
    if len(dims) == 1:
        return "same_res_same" if len({c["md5"] for c in cands}) == 1 else "same_res_diff"
    ars = [c["w"] / c["h"] for c in cands]
    return "diff_res_same_drawing" if (max(ars) - min(ars)) / min(ars) <= AR_TOL \
        else "diff_res_diff_drawing"


def best_of(cands):
    return sorted(cands, key=lambda c: (-(c["w"] * c["h"]), -c["w"], PRIO[c["src"]], c["raw"]))[0]


def cat_of(stem):
    s = stem
    if s.startswith("bg"):
        return "背景", "命名族 bg"
    if s.startswith("ec"):
        return "CG", "命名族 ec（事件CG）"
    if s.startswith("cin"):
        return "CG", "命名族 cin（W9 usage=演出CG）"
    if s.startswith("ef"):
        return "其他", "命名族 ef（特效）"
    if s.startswith("wipe"):
        return "其他", "命名族 wipe（转场擦除帧）"
    if s.startswith("th_"):
        return "其他", "命名族 th_（缩略图/装饰）"
    f = fam_of(s)
    if f in charfam:
        return "CG", "角色代号族 %s（W9 §3.5：角色相关CG）" % f
    return "未判定", "命名族 %s 语义未定（W9 待判读）" % (f or "?")


rows, review = [], []

for stem in sorted(by_stem):
    cands = by_stem[stem]
    cls = classify_group(cands)
    m = RE_SPLIT.match(stem)
    grp = m.group(1) if m else ""

    if grp:
        csrc = split_choice[grp]
        idx = int(m.group(2))
        if idx in split_groups[grp].get(csrc, {}):
            chosen = split_groups[grp][csrc][idx]
        else:
            alts = [c for c in cands if c["src"] != csrc]
            chosen = best_of(alts) if alts else best_of(cands)
            review.append(dict(unified=stem + ".png", cls=cls, sim="-", risk="高",
                               cands="; ".join("%s:%s:%dx%d:%s" % (c["src"], c["raw"], c["w"], c["h"], c["md5"][:8]) for c in cands),
                               chosen="%s:%s:%dx%d" % (chosen["src"], chosen["raw"], chosen["w"], chosen["h"]),
                               why="分片组 %s 整组选源 %s，但该源缺此片，退到 %s" % (grp, csrc, chosen["src"]),
                               doubt="分片组内该片与整组不同源（跨源混源风险）"))
        reason = "分片组 %s 整组选源=%s；本片取该源" % (grp, csrc)
        mx = max(c["w"] * c["h"] for c in cands)
        if chosen["w"] * chosen["h"] < mx:
            reason += "；本片非全局最大分辨率"
    else:
        chosen = best_of(cands)
        reason = "分辨率最高 %dx%d" % (chosen["w"], chosen["h"])
        if len({c["w"] * c["h"] for c in cands}) == 1:
            reason += "（组内面积相同）"
        if len(cands) > 1:
            reason += "；源优先级 %s" % chosen["src"]

    category, cat_reason = cat_of(stem)

    # 内容相似度（仅多源组）：选中项 vs 各落选者的「最差」相似度
    worstsim = None
    if len(cands) > 1:
        worstsim = min(sim(chosen["path"], c["path"]) for c in cands if c is not chosen)

    rows.append(dict(unified=stem + ".png", category=category, grp=grp,
                     dim="%dx%d" % (chosen["w"], chosen["h"]), mode=chosen["mode"],
                     bytes=chosen["bytes"], src=chosen["src"], raw=chosen["raw"],
                     n=len(cands), cls=cls, reason=reason, cat_reason=cat_reason,
                     path=chosen["path"], sim=worstsim))

    risk = "-" if worstsim is None else ("低" if worstsim >= 0.90 else ("中" if worstsim >= 0.80 else "高"))
    candstr = "; ".join("%s:%s:%dx%d:%s" % (c["src"], c["raw"], c["w"], c["h"], c["md5"][:8])
                        for c in sorted(cands, key=lambda x: PRIO[x["src"]]))
    if cls == "same_res_diff":
        review.append(dict(unified=stem + ".png", cls=cls, sim="%.3f" % worstsim, risk=risk,
                           cands=candstr,
                           chosen="%s:%s:%dx%d" % (chosen["src"], chosen["raw"], chosen["w"], chosen["h"]),
                           why=reason, doubt="同分辨率不同内容（md5 不一致），按源优先级选一"))
    elif cls == "diff_res_diff_drawing":
        review.append(dict(unified=stem + ".png", cls=cls, sim="%.3f" % worstsim, risk=risk,
                           cands=candstr,
                           chosen="%s:%s:%dx%d" % (chosen["src"], chosen["raw"], chosen["w"], chosen["h"]),
                           why=reason,
                           doubt="宽高比差异>2%%：按规格 §3.3 仍选最高分辨率，但两版画幅不同（疑同景不同取景/裁切），保留在源中未删"))
    elif cls == "diff_res_same_drawing" and worstsim is not None and worstsim < SIM_HIGH:
        review.append(dict(unified=stem + ".png", cls=cls, sim="%.3f" % worstsim, risk=risk,
                           cands=candstr,
                           chosen="%s:%s:%dx%d" % (chosen["src"], chosen["raw"], chosen["w"], chosen["h"]),
                           why=reason,
                           doubt="宽高比接近但内容相似度低（<%.2f）：疑非同图，人工复核" % SIM_HIGH))

# ------------------------------------------- 5. np 独立素材 + 内容配对尝试
np_only = [s for s in by_stem if all(c["src"] == "np" for c in by_stem[s])]
non_np = [c for c in records if c["src"] != "np"]
np_pair_hits = []
for stem in sorted(np_only):
    cands = by_stem[stem]
    ar = cands[0]["w"] / cands[0]["h"]
    pool = [c for c in non_np if abs(c["w"] / c["h"] - ar) / min(c["w"] / c["h"], ar) <= AR_TOL]
    best = None
    for a in cands:
        for b in pool:
            s = sim(a["path"], b["path"], 32)
            if best is None or s > best[0]:
                best = (s, a, b)
    if best and best[0] >= SIM_PAIR:
        np_pair_hits.append((stem, best))
        review.append(dict(unified=stem + ".png", cls="single", sim="%.3f" % best[0], risk="低",
                           cands="np:%s:%dx%d:%s（其它五源无同 stem）" % (best[1]["raw"], best[1]["w"], best[1]["h"], best[1]["md5"][:8]),
                           chosen="np:%s:%dx%d" % (best[1]["raw"], best[1]["w"], best[1]["h"]),
                           why="np 独立素材（无同 stem 候选），按命名规则独立成组",
                           doubt="内容配对候选：%s:%s:%dx%d sim=%.3f（宽高比相同、相似度高）——若确认同图，需主代理裁决是否并入该组"
                                 % (best[2]["src"], best[2]["raw"], best[2]["w"], best[2]["h"], best[0])))
    else:
        review.append(dict(unified=stem + ".png", cls="single", sim=("-" if not best else "%.3f" % best[0]), risk="-",
                           cands="np:%s:%dx%d:%s（其它五源无同 stem）" % (cands[0]["raw"], cands[0]["w"], cands[0]["h"], cands[0]["md5"][:8]),
                           chosen="np:%s:%dx%d" % (cands[0]["raw"], cands[0]["w"], cands[0]["h"]),
                           why="np 独立素材（无同 stem 候选）",
                           doubt="无法与其它源配对，已作独立素材"))

print("\n== 4 统一结果 == 产物数(=组数) %d ; Σ组内候选数 %d ; 节省重复 %d"
      % (len(rows), sum(r["n"] for r in rows), len(records) - len(rows)))
print("   分类:", dict(Counter(r["cls"] for r in rows)))
print("   类别:", dict(Counter(r["category"] for r in rows)))
print("   待复核条数: %d（np 独立素材 %d，其中 np 内容配对候选 %d）"
      % (len(review), len(np_only), len(np_pair_hits)))
print("   待复核风险分布:", dict(Counter(r["risk"] for r in review)))

# ------------------------------------------------------------------ 6. 写产物
if not ANALYZE_ONLY:
    os.makedirs(OUT_IMG, exist_ok=True)
    for r in rows:
        shutil.copyfile(r["path"], os.path.join(OUT_IMG, r["unified"]))

    with open(os.path.join(OUT_ROOT, "清单_CG背景.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "类别", "组名", "尺寸(w,h)", "模式", "字节",
                    "选中源", "选中原名", "组内候选数", "分类", "理由"])
        for r in rows:
            w.writerow([r["unified"], r["category"], r["grp"], r["dim"], r["mode"],
                        r["bytes"], r["src"], r["raw"], r["n"], r["cls"],
                        r["reason"] + "；" + r["cat_reason"]])

    RANK = {"高": 0, "中": 1, "低": 2, "-": 3}
    review.sort(key=lambda r: (RANK[r["risk"]], r["cls"], r["unified"]))
    with open(os.path.join(OUT_ROOT, "待复核_CG背景.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "分类", "内容相似度", "风险", "候选清单（源:原名:尺寸:md5前8）", "选中项", "选中理由", "疑点"])
        for r in review:
            w.writerow([r["unified"], r["cls"], r["sim"], r["risk"], r["cands"], r["chosen"], r["why"], r["doubt"]])

    print("\n== 6 已写出 ==\n   %s  (%d 个文件)\n   %s\n   %s"
          % (OUT_IMG, len(rows), os.path.join(OUT_ROOT, "清单_CG背景.tsv"),
             os.path.join(OUT_ROOT, "待复核_CG背景.tsv")))

# ------------------------------------------------------------------ 7. 自证
print("\n===== 自证 =====")
print("V1 产物数==组数: %d == %d -> %s ; 统一名唯一: %s"
      % (len(rows), len(by_stem), len(rows) == len(by_stem),
         len({r["unified"] for r in rows}) == len(rows)))

per_src = Counter(c["src"] for c in records)
tot = sum(r["n"] for r in rows)
print("V2 覆盖守恒: Σ组内候选数=%d ; 源文件总数=%d -> %s" % (tot, len(records), tot == len(records)))
print("   逐源:", {s: per_src[s] for s in SOURCES})

print("V3 分片组整组同源:")
allok = True
for base in sorted(split_groups):
    ch = split_choice[base]
    outs = {r["src"] for r in rows if r["grp"] == base}
    ok = outs == {ch}
    allok &= ok
    print("   %-8s 统一选中源=%-4s 产物片数=%d 片号=%s 产物源集合=%s 同源=%s"
          % (base, ch, sum(1 for r in rows if r["grp"] == base),
             sorted(split_groups[base][ch]), sorted(outs), ok))
print("   分片组统一名总数 %d（预期 6 组 × 8 片 = 48）"
      % sum(1 for r in rows if r["grp"]))
print("   分片组同源全部一致: %s" % allok)

print("V4 宽高比差异>2%% 的组（diff_res_diff_drawing）:")
n4 = [r for r in rows if r["cls"] == "diff_res_diff_drawing"]
for r in sorted(n4, key=lambda x: x["unified"]):
    print("   %-16s %-9s sim=%s | %s" % (r["unified"], r["dim"],
          ("%.3f" % r["sim"]) if r["sim"] is not None else "-", r["reason"]))
print("   合计 %d 组（全部已逐条列入 待复核_CG背景.tsv）" % len(n4))

bad = []
for stem, cands in by_stem.items():
    m = RE_SPLIT.match(stem)
    mx = max(c["w"] * c["h"] for c in cands)
    mw = max(c["w"] for c in cands)
    row = next(r for r in rows if r["unified"] == stem + ".png")
    ch = next(c for c in cands if c["src"] == row["src"] and c["raw"] == row["raw"])
    if ch["w"] * ch["h"] != mx or ch["w"] != mw:
        bad.append((stem, ch, mx, mw))
print("V5 选优: 选中非「面积最大」的组数 = %d" % len(bad))
for stem, ch, mx, mw in bad[:20]:
    print("   反例 %s: 选中 %dx%d(%s) 组内最大面积=%d 最大宽=%d" % (stem, ch["w"], ch["h"], ch["src"], mx, mw))

random.seed(20260919)
sample = random.sample(rows, 20)
if not ANALYZE_ONLY:
    ok = 0
    for r in sample:
        if open(r["path"], "rb").read() == open(os.path.join(OUT_IMG, r["unified"]), "rb").read():
            ok += 1
        else:
            print("   BYTE MISMATCH", r["unified"])
    print("V6 原字节保真: 随机抽 20 -> %d/20 逐字节相同" % ok)
    print("   抽样清单:", [r["unified"] for r in sample])
else:
    print("V6 原字节保真: 跳过（--analyze）")

print("V7 未判定/待复核: 类别=未判定 %d 组 ; 待复核 %d 条"
      % (sum(1 for r in rows if r["category"] == "未判定"), len(review)))