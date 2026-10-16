# -*- coding: utf-8 -*-
"""ISSUE-20261008-09 TOB0 探索 6：逐 op 项流形态签名（只读）"""
import os, struct, collections

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


def decode_items(body):
    """宽松解码：返回 [(tag, sel, val, raw)]，遇未知即停止并置 err。"""
    if not body:
        return None, [(0, None, b"", b"")]
    cnt = body[0]
    p, items = 1, []
    for _ in range(cnt):
        if p >= len(body):
            return None, items
        tag = body[p]; p += 1
        if tag == 0x00:
            items.append((0, None, None, b""))
        elif tag == 0x01:
            if p >= len(body):
                return None, items
            sel = body[p]; p += 1
            if sel == 0x00:
                if p + 4 > len(body):
                    return None, items
                v = struct.unpack_from("<I", body, p)[0]; items.append((1, 0, v, b"")); p += 4
            elif sel == 0x01:
                if p + 2 > len(body):
                    return None, items
                n = struct.unpack_from("<H", body, p)[0]; p += 2
                if p + n > len(body):
                    return None, items
                items.append((1, 1, body[p:p + n], body[p:p + n])); p += n
            else:
                items.append((1, sel, body[p:], body[p:])); return None, items
        elif tag == 0x02:
            if p + 4 > len(body):
                return None, items
            v = struct.unpack_from("<I", body, p)[0]; items.append((2, None, v, b"")); p += 4
        else:
            return None, items
    return (p == len(body)), items


def main():
    files = sorted(f for f in os.listdir(TOBDIR) if f.lower().endswith(".tob"))
    per_op_shapes = collections.defaultdict(collections.Counter)
    per_op_ex = collections.defaultdict(dict)
    strs_by_op = collections.defaultdict(collections.Counter)
    for fn in files:
        d = open(os.path.join(TOBDIR, fn), "rb").read()
        cs = parse_header(d)
        for (off, op, L, body) in scan(d, cs):
            good, items = decode_items(body)
            sig = ",".join("%d%s" % (t, "" if s is None else "/%d" % s) for (t, s, v, r) in items)
            per_op_shapes[op][sig if good else sig + "  <<FAIL>>"] += 1
            if op not in per_op_ex:
                per_op_ex[op] = (fn, off, body.hex(), items)
            for (t, s, v, r) in items:
                if t == 1 and s == 1:
                    try:
                        txt = r[:-1].decode("cp932")
                    except Exception:
                        txt = "<non-cp932>"
                    strs_by_op[op][txt] += 1
    for op in sorted(per_op_shapes):
        shp = per_op_shapes[op]
        print("\n=== op=0x%02x (%d) 共 %d 条 ===" % (op, op, sum(shp.values())))
        for s, c in shp.most_common(4):
            print("   %6d  %s" % (c, s))
        ex = per_op_ex[op]
        print("   ex: %s@0x%x body=%s" % (ex[0], ex[1], ex[2]))
        if strs_by_op[op]:
            print("   decl strs:", [s for s, _ in strs_by_op[op].most_common(6)])


if __name__ == "__main__":
    main()
