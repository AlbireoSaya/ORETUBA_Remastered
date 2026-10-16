#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xtab.py — 枚举 `jmp dword ptr [reg*4 + disp]` 跳转表：表址、表长、入口 VA、以及
紧邻其前的 `cmp reg, imm`（case 上界）。用于定位「节点 tag 分派」等真·switch。

口径：skipdata=True 全节线性反汇编。表长以「表址到下一个 .text 内指令地址」估算，
并给出前 8 个表项。若表项落 .text 外或非法则标注。

用法：python -X utf8 xtab.py [--range lo hi] [--min N]
"""
import struct
import sys

import capstone

from pe_min import PE, DUMP_PATH

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


def main():
    pe = PE(DUMP_PATH)
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    tlo, thi = va0, va0 + len(code)
    a = sys.argv[1:]
    lo, hi = (int(a[a.index("--range") + 1], 0), int(a[a.index("--range") + 2], 0)) \
        if "--range" in a else (tlo, thi)
    prev = None
    rows = []
    for ins in md.disasm(code, va0):
        if ins.id == 0:
            prev = None
            continue
        if ins.mnemonic == "jmp" and ins.operands and \
                ins.operands[0].type == capstone.x86.X86_OP_MEM:
            m = ins.operands[0].mem
            if m.index:
                rows.append((ins.address, ins.op_str, m.disp, prev))
        prev = ins
    for va, ops, tbl, prev in rows:
        if not (lo <= va < hi):
            continue
        # 表长：从 tbl 起，读到第一个落 .text 外的值
        size = 0
        ent = []
        while True:
            p = pe.rva_to_off(tbl + 4 * size - pe.image_base)
            if p is None or p + 4 > len(pe.data):
                break
            v = struct.unpack_from("<I", pe.data, p)[0]
            off = pe.rva_to_off(v - pe.image_base) if v >= pe.image_base else None
            sec = pe.section_of_off(off) if off is not None else None
            if not sec or sec["name"] != ".text":
                break
            ent.append(v)
            size += 1
            if size > 400:
                break
        bound = ""
        if prev is not None and prev.mnemonic == "cmp":
            bound = "%s %s" % (prev.mnemonic, prev.op_str)
        print("jmp@0x%08X  tbl=0x%08X len=%d  prev=(0x%08X %s)  first=%s"
              % (va, tbl, size, prev.address if prev else 0, bound,
                 ",".join("0x%X" % e for e in ent[:8])))
    print("共 %d 张（range 0x%X..0x%X）" % (len(rows), lo, hi))


if __name__ == "__main__":
    main()
