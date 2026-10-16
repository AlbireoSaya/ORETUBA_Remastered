# -*- coding: utf-8 -*-
"""只读：未证 op 的 **逐位置** 值域 + 原始 body hex 样本 + 邻接（prev/next op）。"""
import io, collections, re, itertools

UNPROVEN = ["0x03","0x04","0x09","0x0e","0x11","0x1b","0x23","0x25","0x26","0x27","0x28","0x29",
            "0x2a","0x2b","0x2d","0x31","0x38","0x39","0x3a","0x3c","0x3d","0x3f","0x40","0x47",
            "0x4a","0x4b","0x4c","0x4e","0x4f","0x50","0x55","0x56","0x5a","0x5b","0x5c","0x5e",
            "0x5f","0x60","0x68","0x69","0x6a","0x6b","0x6c","0x6d","0x6e","0x6f","0x71","0x72",
            "0x73","0x74","0x78","0x79","0x7c"]
UNS = set(int(x,16) for x in UNPROVEN)

recs = []
with io.open("_records_ota.tsv", encoding="utf-8") as f:
    next(f)
    for line in f:
        recs.append(line.rstrip("\n").split("\t"))

# 邻接：按 scene 内出现次序
by_scene = collections.defaultdict(list)
for idx, r in enumerate(recs):
    by_scene[r[0]].append(idx)
posinfo = {}
for s, idcs in by_scene.items():
    for k, i in enumerate(idcs):
        posinfo[i] = (idcs[k-1] if k > 0 else None,
                      idcs[k+1] if k+1 < len(idcs) else None)

def toks(items):
    return items.split("|") if items else []

def norm(t):
    if t == "()":
        return "o"
    if t.startswith('"'):
        return "S"
    if t.startswith("i"):
        return "i:" + t[1:]
    if t.startswith("u"):
        return "u:" + t[1:]
    return "?"

for op in sorted(UNS):
    idcs = [i for i, r in enumerate(recs) if int(r[2]) == op]
    n = len(idcs)
    # 逐位置值域
    perpos = collections.defaultdict(collections.Counter)
    prevc = collections.Counter(); nextc = collections.Counter()
    for i in idcs:
        ts = toks(recs[i][7])
        for k, t in enumerate(ts):
            perpos[k][norm(t)] += 1
        p, nx = posinfo[i]
        prevc[recs[p][2] if p is not None else "START"] += 1
        nextc[recs[nx][2] if nx is not None else "END"] += 1
    print("\n===== op=0x%02x  n=%d =====" % (op, n))
    for k in sorted(perpos):
        top = perpos[k].most_common(8)
        print("   pos%-2d %s" % (k, top))
    print("   prev op(dec): %s" % prevc.most_common(6))
    print("   next op(dec): %s" % nextc.most_common(6))
    # body hex 样本 3 条
    for i in idcs[:3]:
        print("     e.g. %s @%s  body=%s" % (recs[i][0], recs[i][1], recs[i][8]))
