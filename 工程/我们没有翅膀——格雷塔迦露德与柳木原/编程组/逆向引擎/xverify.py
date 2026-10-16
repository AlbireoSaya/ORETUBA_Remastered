#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xverify.py — 用引擎侧「重定位表」反向验证 VM 反汇编语义（强交叉验证）。

原理：装载期重定位把「引用字」就地改写成运行期指针：
  maps[1] value → [manager+0x38][value]（handler 向量下标 → 原生函数指针）
  maps[3] value → func_lib_base + value（func_lib 代码指针）
  maps[4] value → 本模块缓冲基址 + value（本模块串/代码指针）
  maps[0] value → [manager+0x58][value]（变量槽指针，user_var）
所以在**文件层**，VM 指令的操作数字（尚未重定位的原始值）应恰好落在对应 map 的**键**上。

验证项（按 VM 表走查每一条指令）：
  A. op 0x05（call native）：操作数 0 的字节偏移 ∈ maps[1] 键，且其 value < handler 总数（≤800）
  B. op 0x04（call func_lib）：操作数 0 ∈ maps[3] 键
  C. op 0x09（push deref）/ 0x1F（store）：操作数命中 maps[0]/[3]/[4] 之一的比例
  D. 所有 op 位置的字 ≤ 0x2E（已在 xwalk 验证，这里再计）

用法：python -X utf8 xverify.py [root]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402
from xwalk import VM_LEN  # noqa: E402

HANDLER_MAX = 801   # 3(ctor) + 798(block)


def check(sob):
    c = sob.cells
    m1, m3, m4, m0 = sob.maps[1], sob.maps[3], sob.maps[4], sob.maps[0]
    r = dict(op05=0, op05_ok=0, op05_badidx=[], op04=0, op04_ok=0, op04_m4=0,
             op04_bad=[], op09=0, op09_ref=0, op1F=0, op1F_ref=0, bad_opcode=0,
             op05_dest=0, op05_dest_ok=0)
    i = 0
    while i < len(c):
        t = c[i]
        if t > 0x2E:
            r["bad_opcode"] += 1
            i += 1
            continue
        if t == 0x07:
            break
        L = VM_LEN.get(t, 1)
        site = (i + 1) * 4
        if t == 0x05:
            r["op05"] += 1
            if site in m1 and m1[site] < HANDLER_MAX:
                r["op05_ok"] += 1
            elif len(r["op05_badidx"]) < 5:
                r["op05_badidx"].append((i, hex(c[i + 1]), m1.get(site)))
            # 第 3 操作数（dest）= 写入位置，应命中某个 map（变量槽/本模块）
            dsite = (i + 3) * 4
            r["op05_dest"] += 1
            if dsite in m0 or dsite in m3 or dsite in m4:
                r["op05_dest_ok"] += 1
        elif t == 0x04:
            r["op04"] += 1
            if site in m3:
                r["op04_ok"] += 1
            elif site in m4:
                r["op04_m4"] += 1
            elif len(r["op04_bad"]) < 5:
                r["op04_bad"].append((i, hex(c[i + 1]), c[i + 1] & 0xFFFFFF))
        elif t == 0x09:
            r["op09"] += 1
            if site in m0 or site in m3 or site in m4:
                r["op09_ref"] += 1
        elif t == 0x1F:
            r["op1F"] += 1
            if (site + 4) in m0 or (site + 4) in m3 or (site + 4) in m4:
                r["op1F_ref"] += 1
        i += L
    return r


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else \
        r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT"
    tot = dict(op05=0, op05_ok=0, op04=0, op04_ok=0, op04_m4=0, op09=0, op09_ref=0,
               op1F=0, op1F_ref=0, bad_opcode=0, files=0, op05_dest=0, op05_dest_ok=0)
    ex05, ex04 = [], []
    for fn in sorted(os.listdir(root)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            sob = Sob0(os.path.join(root, fn))
        except Exception:
            continue
        r = check(sob)
        tot["files"] += 1
        for k in tot:
            if k != "files":
                tot[k] += r[k]
        if r["op05_badidx"] and len(ex05) < 5:
            ex05.append((fn, r["op05_badidx"]))
        if r["op04_bad"] and len(ex04) < 5:
            ex04.append((fn, r["op04_bad"]))
    print("== 交叉验证（root=%s，%d 文件）==" % (os.path.basename(root), tot["files"]))
    print("  A. op 0x05 call-native : %d 次，操作数∈maps[1] 且 value<%d : %d  (%.4f)"
          % (tot["op05"], HANDLER_MAX, tot["op05_ok"],
             tot["op05_ok"] / tot["op05"] if tot["op05"] else 0))
    print("  B. op 0x04 call-code  : %d 次，操作数∈maps[3]=%d(%.4f)  ∪maps[4]=%d(%.4f)  合计 %.4f"
          % (tot["op04"], tot["op04_ok"], tot["op04_ok"] / tot["op04"] if tot["op04"] else 0,
             tot["op04_m4"], tot["op04_m4"] / tot["op04"] if tot["op04"] else 0,
             (tot["op04_ok"] + tot["op04_m4"]) / tot["op04"] if tot["op04"] else 0))
    print("  B'. op 0x05 第 3 操作数(dest)∈maps[0/3/4]: %d/%d (%.4f)"
          % (tot["op05_dest_ok"], tot["op05_dest"],
             tot["op05_dest_ok"] / tot["op05_dest"] if tot["op05_dest"] else 0))
    print("  C. op 0x09 push-deref  : %d 次，操作数∈maps[0/3/4]        : %d  (%.4f)"
          % (tot["op09"], tot["op09_ref"], tot["op09_ref"] / tot["op09"] if tot["op09"] else 0))
    print("  D. op 0x1F store       : %d 次，目的∈maps[0/3/4]          : %d  (%.4f)"
          % (tot["op1F"], tot["op1F_ref"], tot["op1F_ref"] / tot["op1F"] if tot["op1F"] else 0))
    print("  E. op 位置字 > 0x2E（非法）: %d" % tot["bad_opcode"])
    if ex05:
        print("  op05 反例示例: %s" % ex05[:3])
    if ex04:
        print("  op04 反例示例: %s" % ex04[:3])


if __name__ == "__main__":
    main()
