# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 8：逐 op 语义特征（控制串/坐标串/ms 值域）只读"""
import os, struct, collections, re

ROOT = r"E:\ZCode Workspace\Galgame"
TOBDIR = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")
CTRL = re.compile(r"^[!_]|^[a-z]<|^[a-z]>|^[A-Z]? ?[a-z]<|^[a-z]$|^[a-z][+-]")
COORD = re.compile(r"^\((\d+),\s*(\d+),\s*(-?\d+)\)")
POS_TOKENS = ("!l", "!r", "l<2", "r>2", "<2", ">2", "<d", ">d")


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
    i, n = cs, len(d)
    while i + 11 <= n:
        if is_hdr(d, i):
            op = d[i + 2]
            L = struct.unpack_from("<I", d, i + 7)[0]
            yield (i, op, L, d[i + 11:i + 11 + (L - 4)] if L >= 4 else b"")
            i += L + 7
        else:
            i += 1


def items(body):
    if not body:
        return []
    cnt = body[0]; p = 1; out = []
    for _ in range(cnt):
        if p >= len(body):
            return out
        tag = body[p]; p += 1
        if tag == 0:
            out.append(("e", None))
        elif tag == 1:
            sel = body[p]; p += 1
            if sel == 0:
                out.append(("i", struct.unpack_from("<I", body, p)[0])); p += 4
            elif sel == 1:
                n = struct.unpack_from("<H", body, p)[0]; p += 2
                out.append(("s", body[p:p + n])); p += n
            else:
                out.append(("x%d" % sel, body[p:])); p = len(body)
        elif tag == 2:
            out.append(("u", struct.unpack_from("<I", body, p)[0])); p += 4
        else:
            out.append(("t%02x" % tag, body[p:])); p = len(body)
    return out


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    decls = collections.defaultdict(collections.Counter)
    intvals = collections.defaultdict(collections.Counter)
    coordcnt = collections.Counter()
    poscnt = collections.Counter()
    posbyop = collections.defaultdict(collections.Counter)
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs = parse_header(d)
        for (off, op, L, body) in scan(d, cs):
            for (t, v) in items(body):
                if t == "s":
                    try:
                        s = v[:-1].decode("cp932")
                    except Exception:
                        continue
                    decls[op][s] += 1
                    if COORD.match(s):
                        coordcnt[op] += 1
                    for tk in POS_TOKENS:
                        if tk in s:
                            poscnt[tk] += 1
                            posbyop[op][tk] += 1
                elif t in ("i", "u"):
                    intvals[op][v] += 1
    print("=== 位置 token 计数（含子串） ===")
    print(dict(poscnt))
    for op in sorted(posbyop):
        print("   op=0x%02x" % op, dict(posbyop[op]))
    print("\n=== 坐标串计数 ===", dict(coordcnt))

    print("\n=== 逐 op 数值 + 字符串摘要 ===")
    for op in sorted(set(list(decls) + list(intvals))):
        ds = decls[op]
        vs = intvals[op]
        print("\nop=0x%02x (%d)" % (op, op))
        if ds:
            sample = [s for s, c in ds.most_common(10)]
            print("   strs(%d distinct): %s" % (len(ds), sample))
        if vs:
            top = vs.most_common(8)
            n_le2000 = sum(c for v, c in vs.items() if v <= 2000)
            print("   ints(%d distinct) top=%s | <=2000:%d" % (len(vs), top, n_le2000))


if __name__ == "__main__":
    main()
