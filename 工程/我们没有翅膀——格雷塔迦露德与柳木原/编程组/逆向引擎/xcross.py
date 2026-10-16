#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xcross.py — 用第二个构建（OT_PREDE.EXE）交叉验证 Lucifen VM 结构。

做法（不依赖地址相同）：
  1) 找 **恰好 47 项** 的 `jmp dword ptr [reg*4 + tbl]` 跳转表（VM op 数 = 0x00..0x2E）。
  2) 找**被调用次数最多**的 `E8 rel32` 目标（= handler 注册器 sub_422730 的对应物）。
  3) 找 `SCRIPT\\FUNC_LIB.SOB` / `SOB2` 串（装载器）。
  4) 对 ORE 与 PREDE 输出同构对照。

用法：python -X utf8 xcross.py
"""
import collections
import struct
import sys

import capstone

from pe_min import PE

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

EXES = {
    "ORE":   r"D:\Gal\[Navel]我们没有翅膀\ORE_TUBA.EXE",
    "PREDE": r"D:\Gal\壌偨偪偵梼偼側偄乣Prelude乣\OT_PREDE.EXE",
}


def text(pe):
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    return s, pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]], pe.image_base + s["vaddr"]


def jump_tables(pe):
    s, code, va0 = text(pe)
    prev = None
    out = []
    for ins in md.disasm(code, va0):
        if ins.id == 0:
            prev = None
            continue
        if ins.mnemonic == "jmp" and ins.operands and \
                ins.operands[0].type == capstone.x86.X86_OP_MEM and ins.operands[0].mem.index:
            out.append((ins.address, ins.operands[0].mem.disp))
        prev = ins
    res = []
    for va, tbl in out:
        if tbl < pe.image_base:      # capstone disp 为有符号；负值跳过（非绝对表址）
            continue
        n, ent = 0, []
        while True:
            if tbl + 4 * n < pe.image_base:
                break
            p = pe.rva_to_off(tbl + 4 * n - pe.image_base)
            if p is None or p < 0 or p + 4 > len(pe.data):
                break
            v = struct.unpack_from("<I", pe.data, p)[0]
            off = pe.rva_to_off(v - pe.image_base) if v >= pe.image_base else None
            sec = pe.section_of_off(off) if off is not None else None
            if not sec or sec["name"] != ".text":
                break
            ent.append(v)
            n += 1
            if n > 400:
                break
        res.append((va, tbl, ent))
    return res


def most_called(pe):
    s, code, va0 = text(pe)
    cnt = collections.Counter()
    for m in range(len(code) - 5):
        if code[m] == 0xE8:
            rel = struct.unpack_from("<i", code, m + 1)[0]
            t = va0 + m + 5 + rel
            off = pe.rva_to_off(t - pe.image_base) if t >= pe.image_base else None
            sec = pe.section_of_off(off) if off is not None else None
            if sec and sec["name"] == ".text":
                cnt[t] += 1
    return cnt


def main():
    for name, path in EXES.items():
        pe = PE(path)
        print("===== %s  size=%d imagebase=0x%X =====" % (name, len(pe.data), pe.image_base))
        # --- 47-entry jump tables ---
        t47 = [x for x in jump_tables(pe) if len(x[2]) == 47]
        print("  47 项跳转表: %d 张" % len(t47))
        for va, tbl, ent in t47:
            print("    jmp@0x%08X tbl=0x%08X  ent[0]=0x%08X ent[1]=0x%08X ent[2]=0x%08X"
                  % (va, tbl, ent[0], ent[1], ent[2]))
            # 检查 op 0 是否 mov eax,1; ret 形状
            o = pe.rva_to_off(ent[0] - pe.image_base)
            if o is None:
                continue
            b = pe.data[o:o + 16]
            print("      ent[0] bytes = %s" % " ".join("%02X" % x for x in b[:12]))
        # --- registrar candidate ---
        mc = most_called(pe)
        print("  被调用最多的 6 个目标：")
        for t, n in mc.most_common(6):
            print("    0x%08X  x%d" % (t, n))
        # --- loader strings ---
        for pat in (b"SCRIPT\\FUNC_LIB.SOB", b"SCRIPT\\USER_VAR.SOB", b"SOB2", b"SCRIPT\\%s.SOB"):
            p = pe.data.find(pat)
            va = pe.image_base + pe.off_to_rva(p) if p >= 0 else 0
            print("    str %-22r found=%s VA=%s" % (pat, p >= 0, hex(va) if p >= 0 else "-"))
        print()


if __name__ == "__main__":
    main()
