# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索：记录文法侦察（只读，产物落本模块目录）"""
import os, sys, struct, io, collections

ROOT = r"E:\ZCode Workspace\Galgame"
TOBDIR = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")


def parse_header(d):
    if d[:4] != b"TOB0":
        raise ValueError("not TOB0")
    size = struct.unpack_from("<I", d, 4)[0]
    nlab = struct.unpack_from("<I", d, 8)[0]
    p = 0x0C
    labels = []
    for _ in range(nlab):
        ln = d[p]
        nm = d[p + 1:p + 1 + ln] if ln < 5 else d[p + 1:p + 1 + ln]
        p += 1 + ln
    A = struct.unpack_from("<I", d, p)[0]
    B = struct.unpack_from("<I", d, p + 4)[0]
    T = list(struct.unpack_from("<%dI" % B, d, p + 8))
    code_start = p + 8 + 4 * B
    return dict(size=size, B=B, T=T, code_start=code_start, header_end=p)


def rec_scan(d, start):
    """顺序扫描记录头 5b 20 <op> 00 00 00 01"""
    out = []
    i = start
    n = len(d)
    while i + 11 <= n:
        if d[i:i + 2] == b"\x5b\x20" and d[i + 3:i + 6] == b"\x00\x00\x00" and d[i + 6] == 0x01:
            op = d[i + 2]
            L = struct.unpack_from("<I", d, i + 7)[0]
            out.append((i, op, L))
            i += L + 7 if False else (L + 7)
        else:
            i += 1
    return out


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    tot_rec = 0
    oplist = collections.Counter()
    modcheck = collections.Counter()
    gapstats = collections.Counter()
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        try:
            info = parse_header(d)
        except Exception as e:
            print("HDR FAIL", fn, e)
            continue
        cs = info["code_start"]
        recs = rec_scan(d, cs)
        # verify contiguity: each next offset == prev offset + L + 7
        prev_end = None
        bad = 0
        for (off, op, L) in recs:
            oplist[op] += 1
            modcheck[off % 4] += 1
            if prev_end is not None and off != prev_end:
                bad += 1
                gapstats[(prev_end - off)] += 1
            prev_end = off + L + 7
        tot_rec += len(recs)
        if bad:
            pass
    print("files", len(files), "records", tot_rec)
    print("op count", len(oplist))
    print("op values", sorted(oplist))
    print("mod4", dict(modcheck))
    print("gaps", gapstats.most_common(10))


if __name__ == "__main__":
    main()
