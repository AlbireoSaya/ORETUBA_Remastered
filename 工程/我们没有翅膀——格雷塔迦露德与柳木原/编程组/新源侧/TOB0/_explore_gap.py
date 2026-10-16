# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 3：定位长度不符的记录并 hexdump（只读）"""
import os, struct, binascii

ROOT = r"E:\ZCode Workspace\Galgame"
TOBDIR = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")


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


def hx(d, a, b, base=0):
    o = a
    while o < b:
        chunk = d[o:o + 16]
        rel = o - base
        print("  %06x (base+%04x)  %-47s  %s" % (o, rel, binascii.hexlify(chunk).decode(),
                                                 ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)))
        o += 16


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    shown = 0
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs = parse_header(d)
        i = cs
        while i + 11 <= len(d):
            if not is_hdr(d, i):
                i += 1
                continue
            op = d[i + 2]
            L = struct.unpack_from("<I", d, i + 7)[0]
            exp = i + L + 7
            if not is_hdr(d, exp):
                if shown < 4:
                    shown += 1
                    print("=== %s @0x%x op=0x%02x L=%d expected_next=0x%x ===" % (fn, i, op, L, exp))
                    hx(d, i, min(i + L + 7 + 24, len(d)), base=i)
                    # find next header
                    j = exp
                    while j < len(d) and not is_hdr(d, j):
                        j += 1
                    print("  actual next header @0x%x (delta=%d, L+7+%d)" % (j, j - i, j - i - L - 7))
            i += L + 7
        if shown >= 4:
            break


if __name__ == "__main__":
    main()
