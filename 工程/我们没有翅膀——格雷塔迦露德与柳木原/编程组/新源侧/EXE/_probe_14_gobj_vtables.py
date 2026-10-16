#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_14_gobj_vtables.py — 找"图形对象"类 vtable (其 +4 方法返回 4..10 的类型码) (只读).

依据: 绘制 handler 形如
    mov ecx,[esi] ; mov eax,[ecx] ; call [eax+4] ; and eax,0xff ; add eax,-4 ; cmp eax,6 ; jmp table
即图形对象的 vtable[1] 返回类型码 4..10.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, dis, fmt

pe = PE()
t0, t1 = pe.sec_range(".text")

# 收集所有 vtable 候选
runs = []
for secname in (".rdata", ".data"):
    lo, hi = pe.sec_range(secname)
    o = pe.off(lo)
    n = (hi - lo) // 4
    i = 0
    while i < n:
        v = struct.unpack_from("<I", pe.data, o + 4 * i)[0]
        if t0 <= v < t1:
            j = i
            vals = []
            while j < n:
                w = struct.unpack_from("<I", pe.data, o + 4 * j)[0]
                if not (t0 <= w < t1):
                    break
                vals.append(w)
                j += 1
            if len(vals) >= 3:
                runs.append((lo + 4 * i, vals))
            i = j
        else:
            i += 1

print("vtable candidates: %d" % len(runs))
found = []
for vt, vals in runs:
    m1 = vals[1] if len(vals) > 1 else None
    if m1 is None:
        continue
    ins = dis(pe, m1, 24)
    if not ins:
        continue
    txt = " | ".join("%s %s" % (x.mnemonic, x.op_str) for x in ins[:3])
    m = re.match(r"^(mov|push|or|xor)\s+(eax|al|eax),\s*(0x[0-9a-fA-F]+|\d+)$", txt)
    if m:
        val = int(m.group(3), 16) if m.group(3).startswith("0x") else int(m.group(3))
        if 4 <= val <= 10:
            found.append((vt, m1, val, txt, len(vals)))
for vt, m1, val, txt, n in found:
    print("  vt=0x%08X len=%d  vtbl[1]=0x%08X -> type=%d   [%s]" % (vt, n, m1, val, txt))
print("found %d" % len(found))
