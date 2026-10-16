# -*- coding: utf-8 -*-
r"""W9 美术资源归纳 · 只读分析器

输入（只读）：
  资源组\krkr素材库\资源总账.json          （48,816 条，25.8 MB，用脚本处理）
  资源组\krkr素材库\otv\_清单.json         （PSV 306 张，content_note 人工判读）
  工程\我们没有翅膀\汉化\剧情汉化\*.jsonl  （voice ID 前缀 <-> speaker 共现，用于立绘代号推定）
输出：
  子代理工作区\ISSUE-20260918-06\W9\art_stats.json  （机器可读全量统计）
  stdout 摘要（人读）

口径：所有数字来自总账实算或磁盘实读，**不估算**。
复跑： python analyze_art.py
"""
import collections
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                       # ...\资源组
PROJ = os.path.dirname(RES)                       # ...\我们没有翅膀——格雷塔迦露德与柳木原
WS = os.path.dirname(os.path.dirname(PROJ))       # ...\Galgame

LEDGER = os.path.join(RES, "krkr素材库", "资源总账.json")
OTV_MANIFEST = os.path.join(RES, "krkr素材库", "otv", "_清单.json")
OT_JSONL_DIR = os.path.join(WS, "工程", "我们没有翅膀", "汉化", "剧情汉化")
OUT_DIR = os.path.join(WS, "子代理工作区", "ISSUE-20260918-06", "W9")
ART_DIR = os.path.join(RES, "美术")          # W9 交付目录（供 UI 组直接使用）

SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]
SOURCE_LABEL = {
    "ot": "本篇", "otr": "R版亚衣线", "ota": "After Story",
    "otp": "前奏诗", "otv": "PSV美咲线UI", "np": "涅布＊プラス",
}
KINDS = ["chr", "pic", "sys", "bgm", "se", "voice", "movie", "etc"]

# D1 裁决基线（总纲 §三.5 / §八 D1）
CANVAS = (1280, 720)
D1_43_SOURCES = ["ot", "otr", "ota", "otp"]   # 800x600 原生 1:1 居中留边
D1_169_SOURCES = ["np"]                        # 1280x720 原生填满
D1_PSV_SOURCES = ["otv"]                       # 960x544 体系


def load_ledger():
    with open(LEDGER, encoding="utf-8") as f:
        return json.load(f)


def is_4_3(w, h):
    return h > 0 and abs(w / h - 4 / 3) < 0.02


def is_16_9(w, h):
    return h > 0 and abs(w / h - 16 / 9) < 0.03


def stem_of(filename, source):
    """与 W4/W5 同口径：去来源前缀 → 去扩展名 → 小写"""
    b = os.path.splitext(filename)[0]
    p = source + "_"
    if b.lower().startswith(p):
        b = b[len(p):]
    return b.lower()


# ---------------------------------------------------------------- 1. 基础统计
def base_stats(entries):
    per_source_kind = collections.defaultdict(collections.Counter)   # 含全部 content_type
    per_source_kind_img = collections.defaultdict(collections.Counter)
    per_source = collections.Counter()
    per_kind = collections.Counter()
    content_types = collections.Counter()
    for e in entries:
        s, k = e["source"], e["kind"]
        per_source[s] += 1
        per_kind[k] += 1
        per_source_kind[s][k] += 1
        content_types[e["content_type"]] += 1
        if e["content_type"] == "image":
            per_source_kind_img[s][k] += 1
    return {
        "total": len(entries),
        "per_source": dict(per_source),
        "per_kind": dict(per_kind),
        "per_source_kind": {s: dict(c) for s, c in per_source_kind.items()},
        "per_source_kind_image": {s: dict(c) for s, c in per_source_kind_img.items()},
        "content_types": dict(content_types),
    }


# ---------------------------------------------------------------- 2. 尺寸分布
def size_dist(entries):
    out = {}
    for s in SOURCES:
        imgs = [e for e in entries if e["source"] == s and e["content_type"] == "image"]
        c = collections.Counter((e["image"]["width"], e["image"]["height"]) for e in imgs)
        tot = len(imgs)
        out[s] = {
            "total": tot,
            "sizes": [
                {"w": w, "h": h, "count": n, "pct": round(100.0 * n / tot, 2) if tot else 0}
                for (w, h), n in c.most_common()
            ],
        }
    return out


def mode_dist(entries):
    out = {}
    for s in SOURCES:
        c = collections.Counter(e["image"]["mode"] for e in entries
                                if e["source"] == s and e["content_type"] == "image")
        out[s] = dict(c)
    return out


def mode_by_kind(entries):
    out = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for e in entries:
        if e["content_type"] == "image":
            out[e["source"]][e["kind"]][e["image"]["mode"]] += 1
    return {s: {k: dict(c) for k, c in v.items()} for s, v in out.items()}


# ---------------------------------------------------------------- 3. 立绘差分
# 立绘 stem 结构（四类，按优先序匹配）：
#   A. <code>_<sub><NN><sfx>   e.g. asu_a01l / cin_blk2 / f_mis01 / yy_10a
#   B. <code>_<NN><sfx>       e.g. ai_01 / ai_01a / lr201e（无下划线形态）
#   C. <code><NN><sfx>        e.g. ai01 / bg06b / hiy01a
#   D. 其余 → unparsed（如实登记，不猜）
CHR_PATTERNS = [
    re.compile(r"^([a-z]+)_([a-z]+)(\d+)([a-z]*)$"),   # A
    re.compile(r"^([a-z]+)_(\d+)([a-z]*)$"),           # B
    re.compile(r"^([a-z]+?)(\d+)([a-z]*)$"),           # C
]


def parse_chr_code(stem):
    """返回 (family, base, suffix, pattern) 或 None。
    family = 首段字母串（f_ 前缀单独登记为 family='f_<sub>'）；
    base   = 去掉尾部字母后缀的基名；suffix = 尾部字母（可为空串）。"""
    m = CHR_PATTERNS[0].match(stem)
    if m:
        code, sub, num, sfx = m.group(1), m.group(2), m.group(3), m.group(4)
        if code == "f":                      # f_mis01 → 家族登记为 f_mis，前缀 f 另行标注
            return ("f_" + sub, sub + num, sfx, "A")
        return (code, sub + num, sfx, "A")
    m = CHR_PATTERNS[1].match(stem)
    if m:
        return (m.group(1), m.group(1) + m.group(2), m.group(3), "B")
    m = CHR_PATTERNS[2].match(stem)
    if m:
        return (m.group(1), m.group(1) + m.group(2), m.group(3), "C")
    return None


def sprite_matrix(entries):
    """按源 → family → 基名 → {suffix: [paths]}；同时登记无法解析项"""
    out = {}
    unparsed = {}
    for s in SOURCES:
        chr_entries = [e for e in entries if e["source"] == s and e["kind"] == "chr"]
        if not chr_entries:
            continue
        tree = collections.defaultdict(lambda: collections.defaultdict(dict))
        bad = []
        pat = collections.Counter()
        for e in chr_entries:
            st = stem_of(e["filename"], s)
            p = parse_chr_code(st)
            if not p:
                bad.append(st)
                continue
            family, base, suffix, kind = p
            pat[kind] += 1
            tree[family][base].setdefault(suffix, []).append(e["out_relpath"])
        out[s] = {
            "total": len(chr_entries),
            "patterns": dict(pat),
            "families": {code: {b: dict(v) for b, v in bases.items()}
                         for code, bases in sorted(tree.items())},
            "unparsed": sorted(set(bad)),
        }
        unparsed[s] = sorted(set(bad))
    return out, unparsed


def chr_code_summary(sprite):
    """每 family：基名数、差分图总数、后缀字母集合、有无无后缀基图"""
    out = {}
    for s, d in sprite.items():
        codes = {}
        for code, bases in d["families"].items():
            n_variants = sum(len(v) for v in bases.values())
            suffixes = sorted({sfx for v in bases.values() for sfx in v})
            with_base = sum(1 for v in bases.values() if "" in v)
            out.setdefault(s, {})[code] = {
                "base_count": len(bases),
                "image_count": n_variants,
                "bases_without_suffix": with_base,
                "suffixes": suffixes,
                "bases": sorted(bases.keys()),
                "suffix_map": {b: sorted(v.keys()) for b, v in sorted(bases.items())},
            }
        out.setdefault(s, {})
    return out


def chr_sizes(entries):
    out = {}
    for s in SOURCES:
        arr = [e for e in entries if e["source"] == s and e["kind"] == "chr"]
        if not arr:
            continue
        c = collections.Counter((e["image"]["width"], e["image"]["height"]) for e in arr)
        h = collections.Counter(e["image"]["height"] for e in arr)
        out[s] = {
            "total": len(arr),
            "top_sizes": [{"w": w, "h": hh, "count": n} for (w, hh), n in c.most_common(15)],
            "height_dist": [{"h": k, "count": v} for k, v in h.most_common(15)],
        }
    return out


# ---------------------------------------------------------------- 4. 背景/CG 编目
PIC_CLASS = [
    ("bg", re.compile(r"^bg\d")),
    ("ec", re.compile(r"^ec\d|^ec_")),
    ("ef", re.compile(r"^ef\d")),
    ("th", re.compile(r"^th_")),
    ("cin", re.compile(r"^cin")),
    ("wipe", re.compile(r"^wipe")),
]


def classify_pic(stem):
    for name, rx in PIC_CLASS:
        if rx.match(stem):
            return name
    return "other"


def pic_catalog(entries):
    out = {}
    for s in SOURCES:
        arr = [e for e in entries if e["source"] == s and e["kind"] == "pic"]
        if not arr:
            continue
        cls = collections.defaultdict(list)
        for e in arr:
            cls[classify_pic(stem_of(e["filename"], s))].append(e)
        detail = {}
        for c, items in sorted(cls.items()):
            sc = collections.Counter((e["image"]["width"], e["image"]["height"]) for e in items)
            detail[c] = {
                "count": len(items),
                "top_sizes": [{"w": w, "h": h, "count": n} for (w, h), n in sc.most_common(10)],
                "stems": sorted(stem_of(e["filename"], s) for e in items),
            }
        out[s] = {"total": len(arr), "classes": detail}
    return out


SPLIT_RE = re.compile(r"^(.*?)_(\d+)$")
BG_SPLIT_RE = re.compile(r"^bg\d+[a-z]?$")          # 分片背景基名：bg06 / bg06a / bg06b / bg07a…


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def split_backgrounds(entries):
    """检出「基名_N」形式的分片：同源同 kind 内同基名 ≥2 片。
    一级：kind=pic 且基名匹配 ^bg\\d+[a-z]?$ → **分片背景**（本项目关心的那类）
    二级：其余多片数字序列 → 单独列出，标注 待判读（可能是滚动层/擦除帧/演出序列）
    每片附磁盘 md5（供判断「片间是否有重复/空片」），不解码像素。"""
    out = {}
    for s in SOURCES:
        groups = collections.defaultdict(list)
        for e in entries:
            if e["source"] != s or e["content_type"] != "image":
                continue
            st = stem_of(e["filename"], s)
            m = SPLIT_RE.match(st)
            if m:
                groups[(m.group(1), e["kind"])].append((int(m.group(2)), e))
        bg, other = [], []
        for (base, kind), items in sorted(groups.items()):
            if len(items) < 2:
                continue
            items.sort(key=lambda t: t[0])
            disk = [os.path.join(RES, "krkr素材库", e["out_relpath"].replace("/", os.sep))
                    for _, e in items]
            md5s = [_md5(p) if os.path.isfile(p) else "MISSING" for p in disk]
            rec = {
                "base": base,
                "kind": kind,
                "pieces": len(items),
                "indices": [i for i, _ in items],
                "sizes": sorted({(e["image"]["width"], e["image"]["height"]) for _, e in items}),
                "paths": [e["out_relpath"] for _, e in items],
                "md5": md5s,
                "distinct_md5": len(set(md5s)),
                "all_files_present": all(m != "MISSING" for m in md5s),
            }
            (bg if (kind == "pic" and BG_SPLIT_RE.match(base)) else other).append(rec)
        out[s] = {"bg_split": bg, "other_series": other}
    return out


# ---------------------------------------------------------------- 5. otv 清单
def otv_detail():
    with open(OTV_MANIFEST, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("entries", [])
    c = collections.Counter()
    notes = collections.Counter()
    for e in raw:
        c[e.get("kind", "?")] += 1
        notes[(e.get("content_note") or "").strip()] += 1
    return {"count": len(raw), "kind": dict(c),
            "content_note": [{"note": k, "count": v} for k, v in notes.most_common()]}


# ---------------------------------------------------------------- 6. D1 一致性评估
def d1_assess(entries):
    out = {}
    for s in SOURCES:
        arr = [e for e in entries if e["source"] == s and e["content_type"] == "image"]
        if not arr:
            continue
        buckets = collections.Counter()
        for e in arr:
            w, h = e["image"]["width"], e["image"]["height"]
            if (w, h) == CANVAS:
                buckets["exact_1280x720"] += 1
            elif (w, h) == (800, 600):
                buckets["native_800x600_4:3"] += 1
            elif (w, h) == (960, 544):
                buckets["psv_960x544_16:9"] += 1
            elif (w, h) == (967, 725):
                buckets["psv_cg_967x725"] += 1
            elif is_16_9(w, h):
                buckets["other_16:9"] += 1
            elif is_4_3(w, h):
                buckets["other_4:3"] += 1
            elif w < 800 and h < 600:
                buckets["smaller_than_800x600"] += 1
            elif w > CANVAS[0] or h > CANVAS[1]:
                buckets["larger_than_canvas"] += 1
            else:
                buckets["other"] += 1
        out[s] = dict(buckets)
    return out


def oversized_detail(entries, min_pixels=1280 * 720):
    """尺寸任一边超出 1280x720 的图（不放大原则下必须原样或裁切）"""
    res = collections.defaultdict(list)
    for e in entries:
        if e["content_type"] != "image":
            continue
        w, h = e["image"]["width"], e["image"]["height"]
        if w > CANVAS[0] or h > CANVAS[1]:
            res[e["source"]].append({"path": e["out_relpath"], "w": w, "h": h,
                                     "bytes": e["bytes"], "kind": e["kind"]})
    for s in res:
        res[s].sort(key=lambda x: -(x["w"] * x["h"]))
    return dict(res)


# ---------------------------------------------------------------- 7. 立绘代号证据
def voice_prefix_evidence():
    """ot 本篇 397 个 jsonl：voice ID 字母前缀 ↔ speaker 标签 共现计数。
    这是「立绘代号 → 角色」的**实测证据**（同一槽位内二者成对出现）。"""
    files = sorted(glob.glob(os.path.join(OT_JSONL_DIR, "*.jsonl")))
    m = collections.defaultdict(collections.Counter)
    total = 0
    per_file = 0
    for p in files:
        try:
            fh = open(p, encoding="utf-8")
        except OSError:
            continue
        per_file += 1
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            v, sp = (o.get("voice") or ""), (o.get("speaker") or "")
            if not v or not sp:
                continue
            pre = re.match(r"^([A-Za-z]+)", v)
            if pre:
                total += 1
                m[pre.group(1).upper()][sp] += 1
        fh.close()
    out = {}
    for k in sorted(m):
        c = m[k]
        s = sum(c.values())
        top = c.most_common(3)
        out[k] = {
            "slots": s,
            "top": [{"speaker": a, "count": b, "pct": round(100.0 * b / s, 1)} for a, b in top],
            "dominant_pct": round(100.0 * top[0][1] / s, 1),
        }
    return {"files": per_file, "slots": total, "prefixes": out}


# ---------------------------------------------------------------- main
def kind_size_dist(entries):
    """(源, kind) 维度的图像尺寸分布（UI 组按 sys/pic 找素材时用）"""
    out = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for e in entries:
        if e["content_type"] == "image":
            out[e["source"]][e["kind"]][(e["image"]["width"], e["image"]["height"])] += 1
    res = {}
    for s, kinds in out.items():
        res[s] = {}
        for k, c in kinds.items():
            tot = sum(c.values())
            res[s][k] = {
                "total": tot,
                "sizes": [{"w": w, "h": h, "count": n, "pct": round(100.0 * n / tot, 2)}
                          for (w, h), n in c.most_common()],
            }
    return res


def emit_tsvs(stats, entries, out_dir):
    """把完整明细落成 TSV（人可 grep / 机器可读），保证「逐源逐尺寸」全量可查"""
    written = []

    p = os.path.join(out_dir, "尺寸分布.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("source\tkind\tw\th\tcount\tpct_of_kind\n")
        for s in SOURCES:
            for k, d in sorted(stats["kind_size_dist"].get(s, {}).items()):
                for x in d["sizes"]:
                    f.write(f"{s}\t{k}\t{x['w']}\t{x['h']}\t{x['count']}\t{x['pct']}\n")
    written.append(p)

    p = os.path.join(out_dir, "分片背景.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("source\tbase\tkind\tpiece_index\tw\th\tout_relpath\tmd5\n")
        for s, d in stats["split_backgrounds"].items():
            for g in d["bg_split"] + d["other_series"]:
                grp = "bg_split" if g in d["bg_split"] else "other_series"
                for i, (idx, path, md5) in enumerate(zip(g["indices"], g["paths"], g["md5"])):
                    e = next(x for x in entries if x["out_relpath"] == path)
                    f.write(f"{s}\t{g['base']}\t{g['kind']}\t{idx}\t{e['image']['width']}\t"
                            f"{e['image']['height']}\t{path}\t{md5}\t{grp}\n")
    written.append(p)

    p = os.path.join(out_dir, "立绘差分索引.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("source\tfamily\tbase\tsuffix\tw\th\tmode\tout_relpath\tbytes\n")
        for e in sorted(entries, key=lambda x: (x["source"], x["out_relpath"])):
            if e["kind"] != "chr" or e["content_type"] != "image":
                continue
            st = stem_of(e["filename"], e["source"])
            pr = parse_chr_code(st)
            fam, base, sfx = (pr[0], pr[1], pr[2]) if pr else ("UNPARSED", st, "")
            f.write(f"{e['source']}\t{fam}\t{base}\t{sfx}\t{e['image']['width']}\t"
                    f"{e['image']['height']}\t{e['image']['mode']}\t{e['out_relpath']}\t{e['bytes']}\n")
    written.append(p)

    p = os.path.join(out_dir, "pic族索引.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("source\tclass\tstem\tw\th\tmode\tout_relpath\tbytes\tusage\n")
        for e in sorted(entries, key=lambda x: (x["source"], x["out_relpath"])):
            if e["kind"] != "pic" or e["content_type"] != "image":
                continue
            f.write(f"{e['source']}\t{classify_pic(stem_of(e['filename'], e['source']))}\t"
                    f"{stem_of(e['filename'], e['source'])}\t{e['image']['width']}\t"
                    f"{e['image']['height']}\t{e['image']['mode']}\t{e['out_relpath']}\t"
                    f"{e['bytes']}\t{'|'.join(e['usage'])}\n")
    written.append(p)

    p = os.path.join(out_dir, "otv素材内容判读.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("out_relpath\tw\th\tmode\tbytes\tusage\tcontent_note\n")
        for e in sorted(entries, key=lambda x: x["out_relpath"]):
            if e["source"] != "otv" or e["content_type"] != "image":
                continue
            f.write(f"{e['out_relpath']}\t{e['image']['width']}\t{e['image']['height']}\t"
                    f"{e['image']['mode']}\t{e['bytes']}\t{'|'.join(e['usage'])}\t"
                    f"{e['note'].replace(chr(9), ' ')}\n")
    written.append(p)

    p = os.path.join(out_dir, "系统UI尺寸索引.tsv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("source\tkind\tw\th\tmode\tout_relpath\tbytes\tusage\tusage_src\n")
        for e in sorted(entries, key=lambda x: (x["source"], x["out_relpath"])):
            if e["kind"] not in ("sys", "etc") or e["content_type"] != "image":
                continue
            f.write(f"{e['source']}\t{e['kind']}\t{e['image']['width']}\t{e['image']['height']}\t"
                    f"{e['image']['mode']}\t{e['out_relpath']}\t{e['bytes']}\t"
                    f"{'|'.join(e['usage'])}\t{e['usage_src']}\n")
    written.append(p)

    return written


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(ART_DIR, exist_ok=True)
    led = load_ledger()
    entries = led["entries"]

    stats = {
        "generated_by": "资源组\\工具\\analyze_art.py",
        "ledger_meta": {k: led["meta"][k] for k in
                        ("count", "source_order", "per_source", "per_source_kind")
                        if k in led["meta"]},
        "base": base_stats(entries),
        "size_dist": size_dist(entries),
        "kind_size_dist": kind_size_dist(entries),
        "mode_dist": mode_dist(entries),
        "mode_by_kind": mode_by_kind(entries),
        "chr_sizes": chr_sizes(entries),
        "pic_catalog": pic_catalog(entries),
        "split_backgrounds": split_backgrounds(entries),
        "otv_detail": otv_detail(),
        "d1_assess": d1_assess(entries),
        "oversized": oversized_detail(entries),
    }

    sprite, unparsed = sprite_matrix(entries)
    stats["sprite_codes"] = chr_code_summary(sprite)
    stats["sprite_patterns"] = {s: d["patterns"] for s, d in sprite.items()}
    stats["sprite_unparsed"] = unparsed
    stats["voice_prefix_evidence"] = voice_prefix_evidence()

    with open(os.path.join(OUT_DIR, "art_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    tsvs = emit_tsvs(stats, entries, ART_DIR)

    # ---------------- stdout 摘要 ----------------
    print("== 总览 ==")
    print("total", stats["base"]["total"], "content_types", stats["base"]["content_types"])
    print("per_source", stats["base"]["per_source"])
    print("per_source_kind_image", json.dumps(stats["base"]["per_source_kind_image"],
                                              ensure_ascii=False))
    print()
    print("== 尺寸分布（Top8 / 源）==")
    for s in SOURCES:
        d = stats["size_dist"][s]
        top = ", ".join(f"{x['w']}x{x['h']}:{x['count']}({x['pct']}%)" for x in d["sizes"][:8])
        print(f"{s} n={d['total']} distinct={len(d['sizes'])} | {top}")
    print()
    print("== 色彩模式 ==")
    for s in SOURCES:
        print(s, stats["mode_dist"][s])
    print()
    print("== D1 一致性分桶 ==")
    for s in SOURCES:
        print(s, stats["d1_assess"][s])
    print()
    print("== 立绘代号（源:代号数/图数）==")
    for s, codes in stats["sprite_codes"].items():
        tot = sum(c["image_count"] for c in codes.values())
        print(f"{s}: families={len(codes)} imgs={tot}  patterns={stats['sprite_patterns'][s]}")
        for c, d in sorted(codes.items()):
            print(f"    {c:6} 基{d['base_count']:>3} 图{d['image_count']:>4} "
                  f"无后缀基图{d['bases_without_suffix']:>3} 后缀={''.join(d['suffixes']) or '-'}")
        if stats["sprite_unparsed"][s]:
            print("    unparsed:", stats["sprite_unparsed"][s])
    print()
    print("== 分片背景（kind=pic 且 ^bg..$）==")
    for s, d in stats["split_backgrounds"].items():
        for g in d["bg_split"]:
            print(f"  {s} {g['base']} pieces={g['pieces']} idx={g['indices']} "
                  f"sizes={g['sizes']} distinct_md5={g['distinct_md5']} "
                  f"present={g['all_files_present']}")
    print()
    print("== 其他多片数字序列（待判读）==")
    for s, d in stats["split_backgrounds"].items():
        for g in d["other_series"]:
            print(f"  {s} {g['base']} [{g['kind']}] pieces={g['pieces']} sizes={g['sizes']}")
    print()
    print("== chr 尺寸 ==")
    for s, d in stats["chr_sizes"].items():
        print(s, "n=", d["total"], "| top:", ", ".join(
            f"{x['w']}x{x['h']}:{x['count']}" for x in d["top_sizes"]))
        print("    height:", ", ".join(f"{x['h']}px:{x['count']}" for x in d["height_dist"]))
    print()
    print("== pic 分类 ==")
    for s, d in stats["pic_catalog"].items():
        print(s, {k: v["count"] for k, v in d["classes"].items()})
    print()
    print("== otv content_note ==")
    for x in stats["otv_detail"]["content_note"][:30]:
        print(f"  {x['count']:>4}  {x['note']!r}")
    print()
    print("== 超出画布(>1280x720) ==")
    for s, arr in stats["oversized"].items():
        print(f"{s}: {len(arr)} 条 ->", [(a['path'], f"{a['w']}x{a['h']}") for a in arr[:8]])
    print()
    print("== voice 前缀证据（Top 主导率<100 的）==")
    ev = stats["voice_prefix_evidence"]
    print("files", ev["files"], "slots", ev["slots"], "prefixes", len(ev["prefixes"]))
    for k, v in ev["prefixes"].items():
        print(f"  {k:5} {v['slots']:>6}  " +
              ", ".join(f"{t['speaker']}:{t['count']}({t['pct']}%)" for t in v["top"]))
    print()
    print("written:", os.path.join(OUT_DIR, "art_stats.json"))
    for t in tsvs:
        print("written:", t)


if __name__ == "__main__":
    main()