# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 9：候选 ms op 的上下文（前后记录 op）只读"""
import os, struct, collections

ROOT = r"E:\ZCode Workspace\Galgame"
TOBDIR = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")
CAND = [0x14, 0x3b, 0x5d, 0x61, 0x73, 0x5e, 0x5f, 0x60, 0x69, 0x78, 0x27, 0x71, 0x03]


def parse_header(d):
    nlab = struct.unpack_from("<I", d, 8)[0]
    p = 0x0C
    for _ in range(nlab):
        p += 1 + d[p]
    B = struct.unpack_from("<I", d, p + 4)[0]
    return p + 8 + 4 * B


def is_hdr(d, i):
    return (i + 11 <= len(d) and d[i:i + 2] == b"\x5b\x20"
            and d[i + 3:i + 6] == b"\x00\x00\x00" and d[i + 6] == 0x01)


def scan(d, cs):
    out, i, n = [], cs, len(d)
    while i + 11 <= n:
        if is_hdr(d, i):
            op = d[i + 2]
            L = struct.unpack_from("<I", d, i + 7)[0]
            out.append((i, op, L, d[i + 11:i + 11 + L - 4] if L >= 4 else b""))
            i += L + 7
        else:
            i += 1
    return out


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    prevnext = collections.defaultdict(collections.Counter)
    ex = collections.defaultdict(list)
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs = parse_header(d)
        recs = scan(d, cs)
        for j, (off, op, L, body) in enumerate(recs):
            if op in CAND:
                pv = recs[j - 1][1] if j > 0 else None
                nx = recs[j + 1][1] if j + 1 < len(recs) else None
                prevnext[op][(pv, nx)] += 1
                if len(ex[op]) < 6:
                    ex[op].append((fn, off, pv, nx, body.hex()))
    for op in CAND:
        print("\n=== op=0x%02x 前/后 ===" % op)
        for k, c in prevnext[op].most_common(6):
            print("   prev=0x%02x next=0x%02x : %d" % (k[0] if k[0] else -1, k[1] if k[1] else -1, c))
        for e in ex[op][:3]:
            print("   ex %s@0x%x prev=0x%02x next=0x%02x body=%s" % (e[0], e[1], e[2], e[3], e[4]))


if __name__ == "__main__":
    main()
