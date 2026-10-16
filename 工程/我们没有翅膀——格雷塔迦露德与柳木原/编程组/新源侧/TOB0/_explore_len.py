# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 2：记录长度模型校准（只读）"""
import os, re, struct, collections

ROOT = r"E:\ZCode Workspace\Galgame"
TOBDIR = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")

HDR_RE = re.compile(rb"\x5b\x20(.)\x00\x00\x00\x01")


def parse_header(d):
    nlab = struct.unpack_from("<I", d, 8)[0]
    p = 0x0C
    for _ in range(nlab):
        ln = d[p]
        p += 1 + ln
    B = struct.unpack_from("<I", d, p + 4)[0]
    code_start = p + 8 + 4 * B
    return code_start


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    deltas = collections.Counter()
    total = 0
    ex = []
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs = parse_header(d)
        hits = [(m.start(), m.group(1)[0]) for m in HDR_RE.finditer(d, cs)]
        for idx in range(len(hits) - 1):
            off, op = hits[idx]
            noff, nop = hits[idx + 1]
            L = struct.unpack_from("<I", d, off + 7)[0]
            delta = noff - off
            deltas[(delta - L)] += 1
            if total < 5:
                ex.append((fn, off, op, L, delta))
            total += 1
    print("pairs", total)
    print("(delta - L) distribution top20:")
    for k, v in deltas.most_common(20):
        print("  %8d : %d" % (k, v))
    print("sample:", ex)


if __name__ == "__main__":
    main()
