#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_01_imports.py — 解析 IAT -> 函数名 (只读). 查任意 VA 是不是 IAT thunk."""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE

pe = PE()
rva, sz = pe.ddirs[1]
off = pe.rva_to_off(rva)
raw = pe.data[off:off + sz]
iat2name = {}
p = 0
descs = []
while p + 20 <= len(raw):
    ilt, ts, fc, name_rva, iat = struct.unpack_from("<IIIII", raw, p)
    if ilt == 0 and ts == 0 and name_rva == 0:
        break
    dll = pe.cstr(pe.image_base + name_rva, 64).decode("latin1")
    descs.append(dll)
    tho = pe.rva_to_off(ilt) if ilt else pe.rva_to_off(iat)
    ia = iat
    while tho is not None:
        ent = struct.unpack_from("<I", pe.data, tho)[0]
        if ent == 0:
            break
        if ent & 0x80000000:
            fn = "#%d" % (ent & 0xFFFF)
        else:
            hn = pe.cstr(pe.image_base + ent + 2, 64)
            fn = hn.decode("latin1") if hn else "?"
        iat2name[pe.image_base + ia] = (dll, fn)
        tho += 4
        ia += 4
    p += 20

print("dlls:", descs)
print("IAT entries:", len(iat2name))

# print full sorted IAT map
print("\n== full IAT map ==")
for va in sorted(iat2name):
    dll, fn = iat2name[va]
    print("  0x%08X  %-14s %s" % (va, dll, fn))

# query
targets = [int(x, 0) for x in sys.argv[1:]] or [0x4ED100, 0x4ED0E8, 0x4ED440, 0x4ED118, 0x4ED11C,
                                                0x4ED0A0, 0x4ED0A4, 0x4ED0A8]
print("\n== queries ==")
for t in targets:
    print("  0x%08X -> %r" % (t, iat2name.get(t)))
