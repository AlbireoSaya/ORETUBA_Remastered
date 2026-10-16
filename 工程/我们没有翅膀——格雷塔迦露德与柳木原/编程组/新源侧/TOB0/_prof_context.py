# -*- coding: utf-8 -*-
"""只读：未证 op 的 (a) 场景内位置分位 (b) 特定配对率 (c) 0x04 载荷 (d) 值域。
输出 _prof_context.json 供 op名表 引用。"""
import io, collections, json, re

UNPROVEN = [0x03,0x04,0x09,0x0e,0x11,0x1b,0x23,0x25,0x26,0x27,0x28,0x29,
            0x2a,0x2b,0x2d,0x31,0x38,0x39,0x3a,0x3c,0x3d,0x3f,0x40,0x47,
            0x4a,0x4b,0x4c,0x4e,0x4f,0x50,0x55,0x56,0x5a,0x5b,0x5c,0x5e,
            0x5f,0x60,0x68,0x69,0x6a,0x6b,0x6c,0x6d,0x6e,0x6f,0x71,0x72,
            0x73,0x74,0x78,0x79,0x7c]

recs = []
with io.open("_records_ota.tsv", encoding="utf-8") as f:
    next(f)
    for line in f:
        recs.append(line.rstrip("\n").split("\t"))

# 场景内序列
by_scene = collections.OrderedDict()
for r in recs:
    by_scene.setdefault(r[0], []).append(r)

# 全局统计
out = {}
for op in UNPROVEN:
    n = 0
    nxt = collections.Counter()
    prv = collections.Counter()
    pair = collections.Counter()   # (prev,next)
    is_last = 0
    is_first = 0
    scenes = collections.Counter()
    for s, seq in by_scene.items():
        for k, r in enumerate(seq):
            if int(r[2]) != op:
                continue
            n += 1
            scenes[s] += 1
            p = seq[k-1][2] if k > 0 else "START"
            x = seq[k+1][2] if k+1 < len(seq) else "END"
            prv[p] += 1; nxt[x] += 1; pair[(p, x)] += 1
            if k+1 == len(seq): is_last += 1
            if k == 0: is_first += 1
    out["0x%02x" % op] = {
        "n": n,
        "n_scenes": len(scenes),
        "is_last": is_last, "is_first": is_first,
        "prev_top": prv.most_common(4),
        "next_top": nxt.most_common(4),
        "pair_top": [[list(k), v] for k, v in pair.most_common(3)],
    }

json.dump(out, open("_prof_context.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 0x04 载荷剖析
print("=== 0x04 payload words ===")
w4 = collections.Counter()
for r in recs:
    if int(r[2]) != 4: continue
    b = bytes.fromhex(r[8])
    # body = count(1) + '01 01 03' + 2-byte len? 打印前 8 字节的 u32/u16
    # 直接切 4 字节字看分布
    for i in range(0, min(24, len(b)-4), 4):
        w4[(i, int.from_bytes(b[i:i+4], 'little'))] += 1
for key, c in sorted(w4.items()):
    i, v = key
    if c > 50 or i < 8:
        print("  off%-2d u32=%d(0x%x) x%d" % (i, v, v, c))
print()
print("=== 0x09：是否场景末条 ===")
for s, seq in by_scene.items():
    ops = [int(r[2]) for r in seq]
    if 9 in ops:
        print("  %s last_ops=%s" % (s, ["0x%02x"%o for o in ops[-6:]]))
print()
print("=== 0x0e/0x11 所在场景 ===")
sc0e = sorted(s for s,seq in by_scene.items() if any(int(r[2])==0x0e for r in seq))
sc11 = sorted(s for s,seq in by_scene.items() if any(int(r[2])==0x11 for r in seq))
print("  0x0e scenes(%d): %s" % (len(sc0e), sc0e))
print("  0x11 scenes(%d): %s" % (len(sc11), sc11))
print()
print("=== 0x5a→0x73 配对 ===")
c = collections.Counter()
for s, seq in by_scene.items():
    for k, r in enumerate(seq):
        if int(r[2]) == 0x5a:
            c[seq[k+1][2] if k+1 < len(seq) else "END"] += 1
print("  0x5a next:", c.most_common(6))
print("=== 0x5b→0x74 配对 ===")
c = collections.Counter()
for s, seq in by_scene.items():
    for k, r in enumerate(seq):
        if int(r[2]) == 0x5b:
            c[seq[k+1][2] if k+1 < len(seq) else "END"] += 1
print("  0x5b next:", c.most_common(6))
