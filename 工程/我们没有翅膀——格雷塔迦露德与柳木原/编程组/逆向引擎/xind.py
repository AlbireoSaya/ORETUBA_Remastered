#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xind.py — 全 .text 间接控制流枚举（call/jmp reg 与 call/jmp [mem]）。

口径：skipdata=True 全节线性反汇编（不截断）。
输出分类：
  * callreg / jmpreg : FF D0-D7 / FF E0-E7
  * callmem / jmpmem : FF 10-17 / FF 20-27 / FF 50-57 / FF 60-67 / FF 90-97 / FF A0-A7 …（含 SIB 索引寻址 FF 14/15/24/25…）
  * indexed          : [reg*scale + disp]（真·跳转表/分派表）

用法：
  python -X utf8 xind.py                 # 汇总计数 + 全部 indexed
  python -X utf8 xind.py --range 0x415000 0x426000
  python -X utf8 xind.py --all
"""
import sys

import capstone

from pe_min import PE, DUMP_PATH

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


def scan(pe):
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    out = []
    for ins in md.disasm(code, va0):
        if ins.id == 0 or ins.mnemonic not in ("call", "jmp"):
            continue
        op = ins.operands[0]
        if op.type == capstone.x86.X86_OP_REG:
            out.append((ins.address, ins.mnemonic, "reg", ins.reg_name(op.reg), False, ins.op_str))
        elif op.type == capstone.x86.X86_OP_MEM:
            m = op.mem
            base = ins.reg_name(m.base) if m.base else ""
            idx = ins.reg_name(m.index) if m.index else ""
            out.append((ins.address, ins.mnemonic, "mem", "%s+%s*%d+0x%X" % (base, idx, m.scale, m.disp),
                        bool(idx), ins.op_str))
    return out


def main():
    pe = PE(DUMP_PATH)
    rows = scan(pe)
    a = sys.argv[1:]
    lo = hi = None
    if "--range" in a:
        lo, hi = int(a[a.index("--range") + 1], 0), int(a[a.index("--range") + 2], 0)
    n_reg = sum(1 for r in rows if r[2] == "reg")
    n_mem = sum(1 for r in rows if r[2] == "mem")
    n_idx = sum(1 for r in rows if r[4])
    print("间接控制流共 %d：reg=%d mem=%d（其中 indexed=%d）" % (len(rows), n_reg, n_mem, n_idx))
    print("== indexed（[reg*scale+disp] 分派表候选）==")
    for va, mn, kind, txt, isidx, ops in rows:
        if isidx and (lo is None or lo <= va < hi):
            print("  0x%08X  %s %s" % (va, mn, ops))
    if "--all" in a:
        print("== 全部 ==")
        for va, mn, kind, txt, isidx, ops in rows:
            if lo is None or lo <= va < hi:
                print("  0x%08X  %-4s %s" % (va, mn, ops))


if __name__ == "__main__":
    main()
