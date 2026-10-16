#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xscan.py — 全 .text 线性反汇编 + 指定 disp 的内存操作数枚举（读/写分类）。

口径：
  * **skipdata=True**（全节覆盖，不截断；上一轮 R1 教训）。
  * 用 capstone detail 取每条指令的 mem 操作数（base/index/disp/size），
    打印 base 寄存器名、disp、读/写（写 = 该操作数是目的操作数）。
  * disp 由调用参数给出（如 0xD4,0xD8）；也可 --all 列出所有 disp∈[0x10,0x200) 的
    「非 esp/ebp 基址」访问，用于找对象字段消费点。

用法：
  python -X utf8 xscan.py --disp 0xD4,0xD8
  python -X utf8 xscan.py --disp 0x1C8 --class                # 归类首地址
  python -X utf8 xscan.py --srcreg 0x19C8                     # 只看 [reg+0x19C8]
"""
import collections
import struct
import sys

import capstone

from pe_min import PE, DUMP_PATH

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

# 写目的操作数：这些 mnemonic 的第一个操作数若为 mem 则为「写」
WRITE_FIRST = {
    "mov", "movzx", "movsx", "lea", "add", "adc", "sub", "sbb", "and", "or",
    "xor", "inc", "dec", "neg", "not", "shl", "shr", "sar", "sal", "rol",
    "ror", "movsd", "movsb", "movsw", "stosd", "stosb", "xchg",
}
# 但 mov/cmp/test 的「读」形态：mov reg,[mem] 首操作数是 reg ⇒ 读
# 我们直接看 operand[0].type：若 == MEM 且 mnemonic 会写目的 ⇒ 写；否则若
# 某 operand.type == MEM ⇒ 读。


def mem_ops(ins):
    out = []
    if ins.id == 0:            # SKIPDATA 的 .byte 伪指令无 detail
        return out
    for i, op in enumerate(ins.operands):
        if op.type == capstone.x86.X86_OP_MEM:
            m = op.mem
            out.append(dict(idx=i, base=ins.reg_name(m.base) if m.base else "",
                            index=ins.reg_name(m.index) if m.index else "",
                            scale=m.scale, disp=m.disp, size=op.size))
    return out


def is_write(ins, op_idx):
    if op_idx != 0:
        return False
    m = ins.mnemonic
    if m in ("cmp", "test", "push", "call", "jmp", "inc", "dec"):
        # inc/dec [mem] 实际写，但这里按「数据字段写」口径单列；此处保守：不含
        return False
    # push/call/jmp [mem] 是读
    return True


def scan(pe, want_disp=None, want_reg=None):
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    n = 0
    hits = []
    for ins in md.disasm(code, va0):
        n += 1
        for mo in mem_ops(ins):
            if mo["index"]:
                continue
            if want_disp is not None and mo["disp"] not in want_disp:
                continue
            if want_reg is not None and (mo["base"] or "") != want_reg:
                continue
            hits.append((ins.address, ins.mnemonic, ins.op_str,
                         mo["base"], mo["disp"],
                         "W" if is_write(ins, mo["idx"]) else "R"))
    return n, hits


def main():
    pe = PE(DUMP_PATH)
    a = sys.argv[1:]
    want = None
    if "--disp" in a:
        want = set(int(x, 0) for x in a[a.index("--disp") + 1].split(","))
    reg = a[a.index("--srcreg") + 1] if "--srcreg" in a else None
    n, hits = scan(pe, want, reg)
    print("== 全 .text 线性反汇编(skipdata=True) 指令数 = %d ==" % n)
    if "--class" in a:
        c = collections.Counter()
        for va, mn, ops, base, disp, rw in hits:
            c[(disp, rw)] += 1
        for (d, rw), k in sorted(c.items()):
            print("  disp=0x%X %s : %d" % (d, rw, k))
        return
    print("== 命中 %d ==" % len(hits))
    for va, mn, ops, base, disp, rw in hits:
        print("  0x%08X  %s %-6s %-40s [%s+0x%X] %s"
              % (va, rw, mn, ops, base, disp, ""))


if __name__ == "__main__":
    main()
