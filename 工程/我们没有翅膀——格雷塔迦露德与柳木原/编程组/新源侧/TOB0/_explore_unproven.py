# -*- coding: utf-8 -*-
"""只读：对 53 个未证 op 做形态聚类 / 邻接 / 值域画像。输入 = _records_ota.tsv（已生成）。"""
import csv, collections, json, io, sys

HERE = "."
UNPROVEN = ["0x03","0x04","0x09","0x0e","0x11","0x1b","0x23","0x25","0x26","0x27","0x28","0x29",
            "0x2a","0x2b","0x2d","0x31","0x38","0x39","0x3a","0x3c","0x3d","0x3f","0x40","0x47",
            "0x4a","0x4b","0x4c","0x4e","0x4f","0x50","0x55","0x56","0x5a","0x5b","0x5c","0x5e",
            "0x5f","0x60","0x68","0x69","0x6a","0x6b","0x6c","0x6d","0x6e","0x6f","0x71","0x72",
            "0x73","0x74","0x78","0x79","0x7c"]
UNS = set(int(x,16) for x in UNPROVEN)

# 逐记录读入（**不用 csv.reader**：items 里的引号会被 csv 当成包围引号剥掉）
recs = []   # (scene, off, op, L, ok, nitems, items_str, body_hex, err)
with io.open("_records_ota.tsv", encoding="utf-8") as f:
    next(f)
    for line in f:
        recs.append(line.rstrip("\n").split("\t"))

def shape(items_str):
    """把 items 列归一成形态签名：S=声明串, i=tag01/00 整数, u=tag02, o=() 空项。"""
    if items_str == "":
        return ""
    toks = items_str.split("|")
    out = []
    for t in toks:
        if t == "()":
            out.append("o")
        elif t.startswith('"'):
            out.append("S")
        elif t.startswith("i"):
            out.append("i")
        elif t.startswith("u"):
            out.append("u")
        else:
            out.append("?" )
    return "".join(out)

# 需要跨记录邻接 → 按文件内顺序
# 先按 scene 分组，保持出现顺序（审计档按文件排序、文件内按偏移升序）
by_op = collections.defaultdict(list)
for idx, r in enumerate(recs):
    op = int(r[2])
    if op in UNS:
        by_op[op].append(idx)

print("=== 各未证 op：次数 / 形态签名分布 / 除错 ===")
report = {}
for op in sorted(UNS):
    idcs = by_op.get(op, [])
    n = len(idcs)
    sigs = collections.Counter()
    for i in idcs:
        sigs[shape(recs[i][7])] += 1
    report[op] = {"n": n, "sigs": dict(sigs)}
    print("\n-- op=0x%02x  n=%d" % (op, n))
    for s, c in sigs.most_common(12):
        print("     %-14s %d" % (s if s else "(empty)", c))

json.dump({("0x%02x"%k):v for k,v in report.items()},
          open("_prof_shapes.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwrote _prof_shapes.json")
