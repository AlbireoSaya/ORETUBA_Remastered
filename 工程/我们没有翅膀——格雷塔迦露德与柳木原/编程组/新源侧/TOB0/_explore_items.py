# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 5：body 项流文法穷举验证（只读）

假设：body = <u8 count> + count 个 item
      item = <u8 tag> + payload
        tag 0x00 → 0 字节
        tag 0x01 → <u8 sel> + (sel==0x00 → u32 ; sel==0x01 → <u16 len> + len 字节)
        tag 0x02 → u32
验证目标：全部 72,822 条记录 body 恰好切完（剩余 0），且无未知 tag/sel。
"""
import os, struct, collections, sys

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


def split_items(body):
    """→ (ok, items, err)。items = [(tag, sel, repr)]"""
    if not body:
        return False, [], "empty body"
    cnt = body[0]
    p = 1
    items = []
    for _ in range(cnt):
        if p >= len(body):
            return False, items, "truncated at item header (p=%d len=%d)" % (p, len(body))
        tag = body[p]; p += 1
        if tag == 0x00:
            items.append((tag, None, None))
        elif tag == 0x01:
            if p + 1 > len(body):
                return False, items, "trunc tag01 sel"
            sel = body[p]; p += 1
            if sel == 0x00:
                if p + 4 > len(body):
                    return False, items, "trunc tag01/00 u32"
                v = struct.unpack_from("<I", body, p)[0]; p += 4
                items.append((tag, sel, v))
            elif sel == 0x01:
                if p + 2 > len(body):
                    return False, items, "trunc tag01/01 len"
                n = struct.unpack_from("<H", body, p)[0]; p += 2
                if p + n > len(body):
                    return False, items, "trunc tag01/01 body n=%d rem=%d" % (n, len(body) - p)
                items.append((tag, sel, body[p:p + n])); p += n
            else:
                return False, items, "unknown sel 0x%02x" % sel
        elif tag == 0x02:
            if p + 4 > len(body):
                return False, items, "trunc tag02 u32"
            v = struct.unpack_from("<I", body, p)[0]; p += 4
            items.append((tag, sel if False else None, v))
        else:
            return False, items, "unknown tag 0x%02x" % tag
    return (p == len(body)), items, ("remainder %d" % (len(body) - p) if p != len(body) else "")


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    tot = ok = 0
    errs = collections.Counter()
    bad_ex = []
    tagcnt = collections.Counter()
    selcnt = collections.Counter()
    cntdist = collections.Counter()
    # per-op failure
    opfail = collections.Counter()
    op_tot = collections.Counter()
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs = parse_header(d)
        for (off, op, L, body) in scan(d, cs):
            tot += 1
            op_tot[op] += 1
            good, items, err = split_items(body)
            if good:
                ok += 1
                cntdist[body[0]] += 1
                for (t, s, v) in items:
                    tagcnt[t] += 1
                    if t == 0x01:
                        selcnt[s] += 1
            else:
                errs[err.split('(')[0].strip()] += 1
                opfail[op] += 1
                if len(bad_ex) < 12:
                    bad_ex.append((fn, off, op, L, body.hex(), err))
    print("records %d  ok %d  fail %d" % (tot, ok, tot - ok))
    print("err kinds:", errs.most_common(20))
    print("tags:", dict(tagcnt))
    print("sel(under tag01):", dict(selcnt))
    print("count distribution:", sorted(cntdist.items())[:20])
    print("ops with failures:", opfail.most_common(20))
    for b in bad_ex:
        print("  BAD", b)


if __name__ == "__main__":
    main()
