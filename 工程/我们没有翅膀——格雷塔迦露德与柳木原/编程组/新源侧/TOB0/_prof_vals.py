# -*- coding: utf-8 -*-
"""只读：未证 op 的 值域 / 串样本 / 邻接 画像。输入=_records_ota.tsv。"""
import io, collections, json, re

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
# 保持 scene 内顺序；建立 index -> (scene,pos)
by_scene = collections.defaultdict(list)
for idx, r in enumerate(recs):
    by_scene[r[0]].append(idx)
pos_of = {}
for s, idcs in by_scene.items():
    for k, i in enumerate(idcs):
        pos_of[i] = (s, k, idcs)

def tokens(items):
    return items.split("|") if items else []

INT_RE = re.compile(r"^i(-?\d+)$")
U_RE = re.compile(r"^u(\d+)$")
S_RE = re.compile(r'^"(.*)"$')

def opname(opdec):
    return "0x%02x" % int(opdec)

for op in sorted(UNS):
    idcs = [i for i, r in enumerate(recs) if int(r[2]) == op]
    ints = collections.Counter()
    us = collections.Counter()
    strs = collections.Counter()
    for i in idcs:
        for t in tokens(recs[i][7]):
            m = INT_RE.match(t)
            if m: ints[int(m.group(1))] += 1; continue
            m = U_RE.match(t)
            if m: us[int(m.group(1))] += 1; continue
            m = S_RE.match(t)
            if m: strs[m.group(1)] += 1; continue
    print("\n===== op=0x%02x  n=%d =====" % (op, len(idcs)))
    if ints:
        top = ints.most_common(12)
        print("   ints top: %s" % top)
        print("   int vals distinct=%d min=%d max=%d" % (len(ints), min(ints), max(ints)))
    if us:
        top = us.most_common(12)
        print("   u32 top: %s" % [(v,c) for v,c in top])
        print("   u32 distinct=%d min=%d max=%d" % (len(us), min(us), max(us)))
        print("   u32hex: %s" % [(hex(v),c) for v,c in us.most_common(8)])
    if strs:
        print("   strs distinct=%d top:" % len(strs))
        for s, c in strs.most_common(15):
            print("        %5d  %r" % (c, s[:70]))
