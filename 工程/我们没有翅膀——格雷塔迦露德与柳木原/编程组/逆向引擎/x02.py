#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""x02.py — ctx+0x10（= mgr+0x14）语义反推：全库 op 0x02 / op 0x03 站点与上下文（只读）。

引擎语义（handler VA 直读）：
  0x02 (0x4336A1) COND-CALL:  a = pop(); if (a==0) return 0;
                              ctx[0x10] = *op;   pc = a
  0x03 (0x4336C1)            :  *op = ctx[0x10]; pc += 4

⇒ op 0x02 把**它自己的操作数**写进 ctx+0x10，然后跳到「栈上弹出的目标」；
   op 0x03 把 ctx+0x10 写进**它自己的操作数**指向的槽。
本脚本枚举两者，打印站点的上下文（前后各若干项）与操作数的 maps 归属，
用于判定 ctx+0x10 承载的是「指针 / 立即数 / 引用字」。

用法：
  python -X utf8 x02.py --all  "E:/.../解包/SCRIPT"
  python -X utf8 x02.py --file "E:/.../decoded.ssob"
  python -X utf8 x02.py --all ... --dump02        # 打印每个 0x02 站点前后 8 项
"""
import os
import sys
import collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402

VM_LEN = {0x00: 1, 0x01: 1, 0x02: 2, 0x03: 2, 0x04: 2, 0x05: 4, 0x06: 2,
          0x07: 0, 0x08: 2, 0x09: 2, 0x0A: 2, 0x0B: 2, 0x0C: 2, 0x0D: 4,
          0x0E: 4, 0x0F: 4, 0x10: 4, 0x11: 4, 0x12: 4, 0x13: 4, 0x14: 4,
          0x15: 4, 0x16: 3, 0x17: 3, 0x18: 4, 0x19: 4, 0x1A: 2, 0x1B: 2,
          0x1C: 2, 0x1D: 2, 0x1E: 3, 0x1F: 3, 0x20: 3, 0x21: 3, 0x22: 3,
          0x23: 3, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 3, 0x28: 3, 0x29: 4,
          0x2A: 4, 0x2B: 4, 0x2C: 4, 0x2D: 4, 0x2E: 4}
SENTINEL = 0xFFFFFFFF
OPS = {i: "op%02X" % i for i in range(0x2F)}


def decode_items(cells, trunc07=False):
    items = []
    i, n = 0, len(cells)
    while i < n:
        t = cells[i]
        if t > 0x2E:
            break
        if t == 0x07:
            if trunc07:
                break          # 旧口径：遇 0x07 即停
            j = i + 2
            while j < n and cells[j] != SENTINEL:
                j += 1
            items.append((i, t, list(range(i + 1, j + 1))))
            i = j + 1 if j < n else n
            continue
        L = VM_LEN.get(t, 1) - 1
        items.append((i, t, list(range(i + 1, min(i + 1 + L, n)))))
        i += VM_LEN.get(t, 1)
    return items


def ann(sob, ci):
    site = ci * 4
    out = []
    for name, m in zip(("map0", "map1", "map2", "map3", "map4"), sob.maps):
        if site in m:
            out.append("%s=0x%X" % (name, m[site]))
    return ",".join(out) or "-"


def scan(path, dump=False, trunc07=False):
    try:
        sob = Sob0(path)
    except Exception as e:
        return None, None, []
    items = decode_items(sob.cells, trunc07=trunc07)
    sites02, sites03 = [], []
    for idx, (oc, op, ops) in enumerate(items):
        if op == 0x02:
            operand = ops[0] if ops else None
            sites02.append(dict(file=os.path.basename(path), cell=oc, byte=oc * 4,
                                operand=sob.cells[operand] if operand is not None else None,
                                operand_ann=ann(sob, operand) if operand is not None else "-",
                                ctx=[(o, sob.cells[o], ann(sob, o)) for (_, _op, oo) in items[max(0, idx - 5):idx] for o in oo] if dump else None))
        elif op == 0x03:
            operand = ops[0] if ops else None
            sites03.append(dict(file=os.path.basename(path), cell=oc,
                                operand_ann=ann(sob, operand) if operand is not None else "-"))
    return sob, sites02, sites03


def main():
    a = sys.argv[1:]
    dump = "--dump02" in a
    trunc07 = "--trunc" in a
    files = []
    if "--file" in a:
        files = [a[a.index("--file") + 1]]
    elif "--all" in a:
        root = a[a.index("--all") + 1]
        files = [os.path.join(root, f) for f in sorted(os.listdir(root))
                 if f.lower().endswith(".sob")]

    all02, all03 = [], []
    n02_by_file = collections.Counter()
    n03_by_file = collections.Counter()
    operands = collections.Counter()
    pre_hist = collections.Counter()      # op02 前一个 op 的类型
    pre0C = collections.Counter()         # 若前一个是 0x0C，其操作数
    next_hist = collections.Counter()     # op02 后一个 op
    p3_prev = collections.Counter()       # op03 前一个 op
    p3_region = collections.Counter()     # op03 目标落在代码区/串区
    ret1_prev = collections.Counter()     # op01 前一个 op
    frame_cmp = collections.Counter()     # op02 处 0x0C 帧释放 vs 最近 0x0B 帧分配
    n_full = 0
    for p in files:
        sob, s02, s03 = scan(p, dump, trunc07)
        if s02 is None:
            continue
        all02 += s02
        all03 += s03
        if s02:
            n02_by_file[os.path.basename(p)] = len(s02)
        if s03:
            n03_by_file[os.path.basename(p)] = len(s03)
        for s in s02:
            operands[(hex(s["operand"]) if s["operand"] is not None else "?", s["operand_ann"])] += 1
        # 位置关系统计
        items = decode_items(sob.cells)
        for i, (oc, op, ops) in enumerate(items):
            if op != 0x02:
                continue
            prev = items[i - 1][1] if i > 0 else None
            nxt = items[i + 1][1] if i + 1 < len(items) else None
            pre_hist["op%02X" % prev if prev is not None else "NONE"] += 1
            if prev == 0x0C and items[i - 1][2]:
                pre0C[sob.cells[items[i - 1][2][0]]] += 1
                # 与「最近的 op 0x0B（帧分配）操作数」比对
                j = i - 1
                frame = None
                while j >= 0:
                    if items[j][1] == 0x0B and items[j][2]:
                        frame = sob.cells[items[j][2][0]]
                        break
                    j -= 1
                f_dealloc = sob.cells[items[i - 1][2][0]]
                if frame is None:
                    frame_cmp["no-prior-op0B"] += 1
                elif frame == f_dealloc:
                    frame_cmp["MATCH"] += 1
                else:
                    frame_cmp["MISMATCH"] += 1
            next_hist["op%02X" % nxt if nxt is not None else "NONE"] += 1
        # op 0x03 / op 0x01 统计
        for i, (oc, op, ops) in enumerate(items):
            if op == 0x03:
                prev = items[i - 1][1] if i > 0 else None
                p3_prev["op%02X" % prev if prev is not None else "NONE"] += 1
                if ops:
                    v = sob.maps[4].get(ops[0] * 4)
                    if v is None:
                        p3_region["non-map4"] += 1
                    elif v < sob.ss:
                        p3_region["code"] += 1
                    else:
                        p3_region["string"] += 1
            elif op == 0x01:
                prev = items[i - 1][1] if i > 0 else None
                ret1_prev["op%02X" % prev if prev is not None else "NONE"] += 1
        # 解码是否走到代码区末尾
        last = items[-1][0] if items else 0
        n_full += 1 if last * 4 + 4 >= sob.ss else 0

    print("== op0x02 total = %d ; op0x03 total = %d ==" % (len(all02), len(all03)))
    print("-- op0x02 by file --")
    for f, n in n02_by_file.most_common():
        print("   %-20s %d" % (f, n))
    print("-- op0x02 operand value/annotation histogram --")
    for (v, an), n in operands.most_common():
        print("   operand=%s  maps=%s  x%d" % (v, an, n))
    print("-- op0x02 predecessor op histogram --")
    for k, n in pre_hist.most_common():
        print("   prev=%-6s %d" % (k, n))
    print("-- op0x02 preceded by op0C: its operand (frame size) histogram --")
    for k, n in pre0C.most_common(15):
        print("   op0C[0x%X]  x%d" % (k, n))
    print("-- op0x02 successor op histogram --")
    for k, n in next_hist.most_common():
        print("   next=%-6s %d" % (k, n))
    print("-- op0x03 predecessor op histogram --")
    for k, n in p3_prev.most_common(12):
        print("   prev=%-6s %d" % (k, n))
    print("-- op0x03 target region --")
    for k, n in p3_region.most_common():
        print("   %-10s %d" % (k, n))
    print("-- op0x02 epilogue frame check (0x0C dealloc vs nearest prior 0x0B alloc) --")
    for k, n in frame_cmp.most_common():
        print("   %-16s %d" % (k, n))
    print("-- op0x01 (plain RET) predecessor op histogram --")
    for k, n in ret1_prev.most_common(10):
        print("   prev=%-6s %d" % (k, n))
    print("-- files decoded to end: %d --" % n_full)
    print("-- all op0x02 sites --")
    for s in all02:
        print("   %-20s cell[%d] byte=0x%X operand=0x%X [%s]"
              % (s["file"], s["cell"], s["byte"],
                 s["operand"] if s["operand"] is not None else -1, s["operand_ann"]))
        if dump and s["ctx"]:
            print("       ctx back: %s" % ["c%d=0x%X(%s)" % (c, v, an)
                                           for (c, v, an) in s["ctx"]])
    print("-- op0x03 by file (top 20) --")
    for f, n in n03_by_file.most_common(20):
        print("   %-20s %d" % (f, n))
    # 03 槽的 maps 归属分布
    hist = collections.Counter()
    for s in all03:
        for kv in s["operand_ann"].split(","):
            hist[kv.split("=")[0] if "=" in kv else kv] += 1
    print("-- op0x03 operand map-bucket histogram --")
    for k, n in hist.most_common():
        print("   %-8s %d" % (k, n))


if __name__ == "__main__":
    main()
