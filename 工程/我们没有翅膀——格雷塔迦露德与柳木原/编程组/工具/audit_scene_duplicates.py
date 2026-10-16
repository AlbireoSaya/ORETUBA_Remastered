#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_scene_duplicates.py —— 六源语料「重复场景」全量审计（编程组，ISSUE-20261004-12）
====================================================================================
背景：发现 `otv_P03_01A–D`（PSV 美咲线 P03）与 `otp_p03_01a–d`（前奏诗 p03 美咲篇）是同一段
内容的两个副本。用户裁定「去重，留在前奏诗集里」，并要求**对全部剧情做一次系统性去重统计**。

本脚本对语料 `资源组\剧本\scene_*.jsonl` 的**全部场景**做三层比对：
  ① 完全重复  ：去标题、去内联控制码、去空白后的正文**逐字相同**（sha1 同值）。
  ② 高度相似  ：按「行哈希集合的 Jaccard 相似度」找候选（≥0.70 才报，且共享行数 ≥5）。
  ③ 标题撞车  ：`title_jp` 相同但正文不同（同题异文，单独列出不判为重复）。

输出：
  - `编程组\剧情审计_重复场景.tsv`（一行一对，含组号/类型/相似度/两侧信息/是否入构建）
  - stdout 摘要统计

只读：不修改语料、不写 story。只写上面这一个 TSV。
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj> = 工程\<译名>
WS = os.path.dirname(os.path.dirname(os.path.dirname(PROJ)))   # 工作区根


def norm(s):
    s = re.sub(r"<\d+>", "", s or "")          # 内联控制码 <8> <16> …
    s = s.replace("\\", "")
    s = re.sub(r"[\s\u3000]+", "", s)
    return s


def load_corpus(data_root):
    rows = []
    pat = os.path.join(data_root, "工程", os.path.basename(PROJ), "资源组", "剧本", "scene_*.jsonl")
    for f in sorted(glob.glob(pat)):
        for ln, line in enumerate(open(f, encoding="utf-8"), 1):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("scene_id"):
                d["_file"] = os.path.basename(f)
                d["_line"] = ln
                rows.append(d)
    return rows


def body_lines(d):
    """去掉标题行（jp 或 cn 与标题相同者）后的正文（规范化）。"""
    t = norm(d.get("title_jp") or "")
    tc = norm(d.get("title_cn") or "")
    out = []
    for l in d.get("lines") or []:
        n = norm(l.get("jp") or "")
        if not n or n == t or n == tc:
            continue
        out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=WS)
    ap.add_argument("--out", default=os.path.join(PROJ, "编程组", "剧情审计_重复场景.tsv"))
    ap.add_argument("--jac", type=float, default=0.70, help="高度相似的 Jaccard 阈值")
    ap.add_argument("--min-shared", type=int, default=5, help="构成候选所需的最少共享行数")
    args = ap.parse_args()

    rows = load_corpus(args.data_root)
    print("语料场景总数：%d" % len(rows))

    # 预处理
    info = {}
    for d in rows:
        sid = d["scene_id"]
        body = body_lines(d)
        joined = "\x01".join(body)
        h = hashlib.sha1(joined.encode("utf-8")).hexdigest()
        lhash = [hashlib.sha1(x.encode("utf-8")).hexdigest()[:16] for x in body]
        built = os.path.exists(os.path.join(PROJ, "编程组", "krkr", "game", "story",
                                            "scene_%s.tjs" % sid))
        info[sid] = {
            "id": sid, "src": d.get("source"), "route": d.get("route"),
            "tjp": (d.get("title_jp") or "").strip(), "tcn": (d.get("title_cn") or "").strip(),
            "n": len(body), "hash": h, "set": set(lhash), "built": built,
            "file": d.get("_file"), "line": d.get("_line"),
        }
    built_n = sum(1 for v in info.values() if v["built"])
    print("入构建（story\\scene_*.tjs 存在）：%d" % built_n)

    # ① 完全重复
    byhash = defaultdict(list)
    for v in info.values():
        byhash[v["hash"]].append(v["id"])
    exact = sorted([sorted(v) for v in byhash.values() if len(v) > 1], key=lambda g: g[0])

    # ② 高度相似（倒排索引 → 候选对 → Jaccard）
    inv = defaultdict(set)
    for sid, v in info.items():
        for h2 in v["set"]:
            inv[h2].add(sid)
    cand = defaultdict(int)
    for h2, ids in inv.items():
        if len(ids) < 2 or len(ids) > 60:
            continue
        ids = sorted(ids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                cand[(ids[i], ids[j])] += 1
    near = []
    for (a, b), shared in cand.items():
        va, vb = info[a], info[b]
        m = min(len(va["set"]), len(vb["set"]))
        if m == 0 or shared < min(args.min_shared, m):
            continue
        jac = shared / float(len(va["set"] | vb["set"]))
        if jac >= args.jac and va["hash"] != vb["hash"]:
            near.append((jac, a, b, shared))
    near.sort(reverse=True)

    # ③ 标题撞车（同 title_jp、正文不同）
    bytitle = defaultdict(list)
    for v in info.values():
        if v["tjp"]:
            bytitle[v["tjp"]].append(v["id"])
    title_clash = sorted([sorted(v) for v in bytitle.values() if len(v) > 1], key=lambda g: g[0])
    # 已被 ①/② 覆盖的不再单列
    pair_in = set()
    for g in exact:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                pair_in.add((g[i], g[j]))
    for _, a, b, _ in near:
        pair_in.add((a, b))
    title_only = [g for g in title_clash
                  if not any((g[i], g[j]) in pair_in or (g[j], g[i]) in pair_in
                             for i in range(len(g)) for j in range(i + 1, len(g)))]

    # 汇总组（把互相重叠的对并成组）
    parent = {sid: sid for sid in info}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for g in exact:
        for x in g[1:]:
            union(g[0], x)
    for _, a, b, _ in near:
        union(a, b)
    groups = defaultdict(list)
    for sid in info:
        groups[find(sid)].append(sid)
    dup_groups = {k: sorted(v) for k, v in groups.items() if len(v) > 1}

    # 类型判定（组级）
    gtype = {}
    for k, g in dup_groups.items():
        hs = {info[s]["hash"] for s in g}
        gtype[k] = "完全重复" if len(hs) == 1 else "高度相似"

    # ── 写 TSV ──
    def row_of(gid, g):
        out = []
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = info[g[i]], info[g[j]]
                inter = len(a["set"] & b["set"])
                uni = len(a["set"] | b["set"]) or 1
                jac = 1.0 if a["hash"] == b["hash"] else round(inter / float(uni), 3)
                out.append([
                    "G%02d" % gid, gtype.get(find(g[0]), ""), a["id"], a["src"], a["tjp"], a["tcn"],
                    a["n"], "是" if a["built"] else "否", b["id"], b["src"], b["tjp"], b["tcn"],
                    b["n"], "是" if b["built"] else "否", jac,
                    "%s:%s / %s:%s" % (a["file"], a["line"], b["file"], b["line"]),
                ])
        return out

    hdr = ["组", "类型", "场景A", "源A", "标题A(jp)", "标题A(cn)", "正文行A", "入构建A",
           "场景B", "源B", "标题B(jp)", "标题B(cn)", "正文行B", "入构建B", "相似度", "语料位置"]
    lines_out = ["\t".join(hdr)]
    gid = 0
    for k in sorted(dup_groups, key=lambda k: (-len(dup_groups[k]), dup_groups[k][0])):
        gid += 1
        for r in row_of(gid, dup_groups[k]):
            lines_out.append("\t".join(str(x) for x in r))
    # 标题撞车（同题异文）单独附在表尾
    for g in title_only:
        gid += 1
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = info[g[i]], info[g[j]]
                lines_out.append("\t".join(str(x) for x in [
                    "T%02d" % gid, "同题异文", a["id"], a["src"], a["tjp"], a["tcn"], a["n"],
                    "是" if a["built"] else "否", b["id"], b["src"], b["tjp"], b["tcn"], b["n"],
                    "是" if b["built"] else "否", "", "%s:%s / %s:%s" % (a["file"], a["line"], b["file"], b["line"])]))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines_out) + "\n")

    # ── 摘要 ──
    print()
    print("=== 摘要 ===")
    print("① 完全重复组：%d 组（%d 场景）" % (
        sum(1 for k in dup_groups if gtype[k] == "完全重复"),
        sum(len(dup_groups[k]) for k in dup_groups if gtype[k] == "完全重复")))
    print("② 高度相似组：%d 组（%d 场景）" % (
        sum(1 for k in dup_groups if gtype[k] == "高度相似"),
        sum(len(dup_groups[k]) for k in dup_groups if gtype[k] == "高度相似")))
    print("③ 同题异文（不判重复）：%d 组" % len(title_only))
    print("TSV → %s" % args.out)
    for k in sorted(dup_groups, key=lambda k: (-len(dup_groups[k]), dup_groups[k][0])):
        g = dup_groups[k]
        print("  %s [%s] %d 场: %s" % ("G", gtype[k], len(g),
              " | ".join("%s(%s,%s行%s)" % (s, info[s]["src"], info[s]["n"],
                                           "" if info[s]["built"] else ",未入构建") for s in g)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
