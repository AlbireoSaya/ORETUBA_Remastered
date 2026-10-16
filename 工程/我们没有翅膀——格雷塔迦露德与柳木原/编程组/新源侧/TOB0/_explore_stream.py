# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 7：按消息序打印记录流（只读）"""
import os, struct, collections, sys

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
    out = []
    i, n = cs, len(d)
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


def dec(body):
    if not body:
        return ["<empty>"]
    cnt = body[0]; p = 1; out = []
    for _ in range(cnt):
        if p >= len(body):
            out.append("TRUNC"); break
        tag = body[p]; p += 1
        if tag == 0:
            out.append("()")
        elif tag == 1:
            sel = body[p]; p += 1
            if sel == 0:
                out.append("i%d" % struct.unpack_from("<I", body, p)[0]); p += 4
            elif sel == 1:
                n = struct.unpack_from("<H", body, p)[0]; p += 2
                r = body[p:p + n]; p += n
                try:
                    out.append("s'%s'" % r[:-1].decode("cp932"))
                except Exception:
                    out.append("s?%s" % r.hex())
            else:
                out.append("sel%d<%s>" % (sel, body[p:].hex())); p = len(body)
        elif tag == 2:
            out.append("u%d" % struct.unpack_from("<I", body, p)[0]); p += 4
        else:
            out.append("tag0x%02x<%s>" % (tag, body[p:].hex())); p = len(body)
    return out


def main():
    fn = sys.argv[1] if len(sys.argv) > 1 else "11_1b.tob"
    d = open(os.path.join(TOBDIR, fn), "rb").read()
    cs, B = parse_header(d)
    print("file", fn, "code_start", hex(cs), "B(messages)", B, "size", hex(len(d)))
    cur = 0
    for (off, op, L, body) in scan(d, cs):
        k = None
        if op == 0x0C and body and body[0] == 1 and body[1] == 1 and body[2] == 0:
            k = struct.unpack_from("<I", body, 3)[0]
        print("  @0x%06x  seq=%-4s op=0x%02x L=%-4d %s" % (off, k if k is not None else "", op, L, dec(body)))


if __name__ == "__main__":
    main()
