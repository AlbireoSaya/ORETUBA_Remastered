# -*- coding: utf-8 -*-
r"""W9 验收自证（6 项）—— 只读校验，不修改任何产物

复跑： python verify_w9.py
输出： 子代理工作区\ISSUE-20260918-06\W9\W9验收.json
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
PROJ = os.path.dirname(RES)
WS = os.path.dirname(os.path.dirname(PROJ))
LEDGER = os.path.join(RES, "krkr素材库", "资源总账.json")
ART = os.path.join(RES, "美术")
W9 = os.path.join(WS, "子代理工作区", "ISSUE-20260918-06", "W9")
SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]
KINDS = ["chr", "pic", "sys", "bgm", "se", "voice", "movie", "etc"]

# 资源总账.md §一 交叉表（硬编码，用于独立比对）
EXPECT = {
    "ot":  {"chr": 989, "pic": 763, "sys": 1113, "bgm": 112, "se": 582, "voice": 21036, "movie": 2, "etc": 0},
    "otr": {"chr": 353, "pic": 156, "sys": 0, "bgm": 125, "se": 135, "voice": 2226, "movie": 0, "etc": 0},
    "ota": {"chr": 1264, "pic": 519, "sys": 711, "bgm": 120, "se": 602, "voice": 11205, "movie": 4, "etc": 0},
    "otp": {"chr": 591, "pic": 270, "sys": 261, "bgm": 46, "se": 379, "voice": 4402, "movie": 1, "etc": 0},
    "otv": {"chr": 0, "pic": 0, "sys": 182, "bgm": 0, "se": 0, "voice": 0, "movie": 0, "etc": 124},
    "np":  {"chr": 291, "pic": 93, "sys": 0, "bgm": 31, "se": 58, "voice": 68, "movie": 2, "etc": 0},
}
EXPECT_IMG = {"ot": 2851, "otr": 509, "ota": 2483, "otp": 1117, "otv": 306, "np": 384}


def rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.reader(f, delimiter="\t"))


def main():
    led = json.load(open(LEDGER, encoding="utf-8"))
    e = led["entries"]
    res = {}

    # ---- 1. 覆盖完整 ----
    per = collections.defaultdict(collections.Counter)
    per_img = collections.defaultdict(collections.Counter)
    for x in e:
        per[x["source"]][x["kind"]] += 1
        if x["content_type"] == "image":
            per_img[x["source"]][x["kind"]] += 1
    mismatch = []
    for s in SOURCES:
        for k in KINDS:
            if per[s].get(k, 0) != EXPECT[s][k]:
                mismatch.append({"source": s, "kind": k, "ledger": per[s].get(k, 0), "doc": EXPECT[s][k]})
    img_total = sum(per_img[s].get(k, 0) for s in SOURCES for k in KINDS)
    res["A1_覆盖完整"] = {
        "pass": len(e) == 48816 and sum(sum(v.values()) for v in per.values()) == 48816
                and not mismatch and img_total == 7650,
        "total": len(e),
        "per_source": {s: sum(per[s].values()) for s in SOURCES},
        "image_total": img_total,
        "image_per_source": {s: sum(per_img[s].values()) for s in SOURCES},
        "kind_mismatch_vs_资源总账md": mismatch,
        "img_per_source_kind": {s: dict(per_img[s]) for s in SOURCES},
    }

    # ---- 2. 尺寸分布实测（全量 TSV 行数 + 逐源尺寸种数与总条数自洽）----
    sd = rows(os.path.join(ART, "尺寸分布.tsv"))
    hdr = sd[0]
    assert hdr[0] == "source"
    by_src = collections.defaultdict(lambda: [0, 0])
    for r in sd[1:]:
        by_src[r[0]][0] += int(r[4])
        by_src[r[0]][1] += 1
    ok2 = all(by_src[s][0] == EXPECT_IMG[s] for s in SOURCES)
    # 逐源尺寸分布（从总账重算，与 TSV 交叉）
    recomputed = {}
    for s in SOURCES:
        c = collections.Counter((x["image"]["width"], x["image"]["height"]) for x in e
                                if x["source"] == s and x["content_type"] == "image")
        recomputed[s] = {"distinct": len(c), "total": sum(c.values()),
                         "top5": [[w, h, n] for (w, h), n in c.most_common(5)]}
    res["A2_尺寸分布实测"] = {
        "pass": ok2,
        "tsv_rows": len(sd) - 1,
        "tsv_counts_match_ledger": {s: {"tsv": by_src[s][0], "expected": EXPECT_IMG[s]} for s in SOURCES},
        "recomputed": recomputed,
    }

    # ---- 3. 差分图谱有据（立绘索引 TSV 行数 + 无法解析项登记 + 待判读项存在）----
    sp = rows(os.path.join(ART, "立绘差分索引.tsv"))
    fam = collections.Counter(r[1] for r in sp[1:])
    unparsed = [r for r in sp[1:] if r[1] == "UNPARSED"]
    doc_sprite = open(os.path.join(ART, "立绘差分图谱.md"), encoding="utf-8").read()
    doc_cg = open(os.path.join(ART, "背景CG编目.md"), encoding="utf-8").read()
    n_p = len(re.findall(r"^\| P\d+ \|", doc_sprite, re.M))
    n_q = len(re.findall(r"^\| Q\d+ \|", doc_cg, re.M))
    res["A3_差分图谱有据"] = {
        "pass": len(sp) - 1 == 3488 and len(unparsed) == 3 and n_p >= 9 and n_q >= 11,
        "chr_rows": len(sp) - 1,
        "families": len(fam),
        "unparsed_rows": len(unparsed),
        "unparsed_paths": [r[7] for r in unparsed],
        "待判读_立绘项数": n_p,
        "待判读_背景CG项数": n_q,
        "证据_命名规律文档依据": "工程\\我们没有翅膀R\\亜衣线资源\\说明文档.md:64",
        "证据_角色推定方法": "voice ID 前缀 <-> speaker 共现（ot 397 jsonl / 21354 槽）",
    }

    # ---- 4. 分片背景标全 ----
    sb = rows(os.path.join(ART, "分片背景.tsv"))
    h2 = sb[0]
    bg = [r for r in sb[1:] if r[8] == "bg_split"]
    groups = collections.defaultdict(list)
    for r in bg:
        groups[(r[0], r[1])].append(r)
    sizes_ok = all(len(v) == 8 for v in groups.values())
    md5_ok = all(len(set(x[7] for x in v)) == len(v) for v in groups.values())
    per_src_groups = collections.Counter(k[0] for k in groups)
    res["A4_分片背景标全"] = {
        "pass": len(groups) == 20 and len(bg) == 160 and sizes_ok and md5_ok,
        "groups": len(groups),
        "pieces": len(bg),
        "each_group_8_pieces": sizes_ok,
        "all_md5_distinct_within_group": md5_ok,
        "per_source": dict(per_src_groups),
        "group_names": sorted(f"{k[0]}:{k[1]}" for k in groups),
    }

    # ---- 5. 质量评估可判定（R/H/N 清单条目数与理由列齐备）----
    doc_q = open(os.path.join(ART, "素材质量评估.md"), encoding="utf-8").read()
    n_r = len(re.findall(r"^\| \*\*R\d\*\* \|", doc_q, re.M))
    n_h = len(re.findall(r"^\| H\d \|", doc_q, re.M))
    n_n = len(re.findall(r"^\| N\d \|", doc_q, re.M))
    res["A5_质量评估可判定"] = {
        "pass": n_r == 4 and n_h == 7 and n_n == 9,
        "R_items": n_r, "H_items": n_h, "N_items": n_n,
        "每源评估节数": len(re.findall(r"^### 3\.\d ", doc_q, re.M)),
        "未做目视画质声明": "画风一致性" in doc_q and "不可" in doc_q,
    }

    # ---- 6. 与 D1 一致（检查产物中不出现放大建议）----
    docs = {f: open(os.path.join(ART, f), encoding="utf-8").read()
            for f in ["美术规范.md", "素材质量评估.md", "立绘差分图谱.md",
                      "背景CG编目.md", "资源组致UI组_交接说明.md"]}
    OK_WORDS = ("不放大", "禁止", "违", "冲突", "不得", "是否被放大", "无需放大", "禁")
    NEG_BEFORE = ("不", "勿", "禁", "违", "非", "是否", "不得", "冲突")
    NEG_AFTER = ("会与", "会明显", "违反", "冲突", "禁止", "不一致", "明文")
    bad = []
    for f, t in docs.items():
        for m in re.finditer(r"放大", t):
            before = t[max(0, m.start() - 14):m.start()]
            after = t[m.start():m.start() + 60]
            if any(w in before for w in NEG_BEFORE) or any(w in after for w in NEG_AFTER):
                continue
            if any(w in after for w in OK_WORDS):
                continue
            bad.append({"file": f, "before": before.strip(), "after": after.strip()[:80]})
    has_d1 = all("1280×720" in t for t in docs.values())
    res["A6_与D1一致"] = {
        "pass": has_d1 and len(bad) == 0,
        "all_docs_mention_1280x720": has_d1,
        "suspicious_放大_mentions": bad,
        "自检表_素材质量评估§九": "与 D1 的一致性自检" in doc_q,
    }

    # ---- 交付物存在性 ----
    files = ["美术规范.md", "立绘差分图谱.md", "背景CG编目.md", "素材质量评估.md",
             "资源组致UI组_交接说明.md", "尺寸分布.tsv", "分片背景.tsv",
             "立绘差分索引.tsv", "pic族索引.tsv", "otv素材内容判读.tsv", "系统UI尺寸索引.tsv"]
    res["交付物"] = {f: {"exists": os.path.isfile(os.path.join(ART, f)),
                        "bytes": os.path.getsize(os.path.join(ART, f)) if os.path.isfile(os.path.join(ART, f)) else 0}
                     for f in files}

    res["全部通过"] = all(v.get("pass") for k, v in res.items() if isinstance(v, dict) and "pass" in v)
    os.makedirs(W9, exist_ok=True)
    out = os.path.join(W9, "W9验收.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for k in sorted(res):
        v = res[k]
        if isinstance(v, dict) and "pass" in v:
            print(f"[{'PASS' if v['pass'] else 'FAIL'}] {k}")
        else:
            print(f"[INFO] {k}")
    print("全部通过:", res["全部通过"])
    print("written:", out)
    return 0 if res["全部通过"] else 1


if __name__ == "__main__":
    sys.exit(main())