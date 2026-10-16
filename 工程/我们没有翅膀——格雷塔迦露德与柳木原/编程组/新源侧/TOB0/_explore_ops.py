# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 4：逐 op 抽样 body 十六进制（只读）"""
import os, struct, binascii, collections, sys

ROOT = r"E:\ZCode Workspace\Galgame"
TOBDIR = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")


def parse_header(d):
    nlab = struct.unpack_from("<I", d, 8)[0]
    p = 0x0C
    for _ in range(nlab):
        p += 1 + d[p]
    B = struct.unpack_from("<I", d, p + 4)[0]
    return p + 8 + 4 * B, B


def is_hdr(d, i):
    return (i + 11 <= len(d) and d[i:i + 2] == b"\x5b\x20"
            and d[i + 3:i + 6] == b"\x00\x00\x00" and d[i + 6] == 0x01)


def scan(d, cs):
    """顺序扫描；返回 [(off, op, L, body)]，body = 记录内 L 之后的字节（L-4 个）。"""
    out = []
    i = cs
    n = len(d)
    while i + 11 <= n:
        if is_hdr(d, i):
            op = d[i + 2]
            L = struct.unpack_from("<I", d, i + 7)[0]
            body = d[i + 11:i + 11 + (L - 4)] if L >= 4 else b""
            out.append((i, op, L, body))
            i += L + 7
        else:
            i += 1
    return out


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    samples = collections.defaultdict(list)
    counts = collections.Counter()
    lenmap = collections.defaultdict(collections.Counter)
    tailcount = collections.Counter()
    msgs = {}
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs, B = parse_header(d)
        recs = scan(d, cs)
        msgs[fn] = (B, len(recs))
        for (off, op, L, body) in recs:
            counts[op] += 1
            lenmap[op][L] += 1
            if op == 0x0C:
                tailcount[fn] += 1
            if len(samples[op]) < 4:
                samples[op].append((fn, off, L, body))

    print("=== 每文件 (B, 记录数, op=0x0c 数) ===")
    bad = 0
    for fn in files[:200]:
        B, nr = msgs[fn]
        t = tailcount[fn]
        if B != t:
            bad += 1
            if bad < 15:
                print("  MISMATCH %s B=%d recs=%d tails=%d" % (fn, B, nr, t))
    print("  B != tailcount files:", bad, "/", len(files))

    print("\n=== 78 op 抽样 ===")
    for op in sorted(counts):
        print("\n--- op=0x%02x (%d)  %d 次 ---" % (op, op, counts[op]))
        print("    L 分布 top5:", lenmap[op].most_common(5))
        for (fn, off, L, body) in samples[op][:3]:
            print("    %s @0x%x L=%d body(%d)= %s" % (fn, off, L, len(body), binascii.hexlify(body).decode()))


if __name__ == "__main__":
    main()
