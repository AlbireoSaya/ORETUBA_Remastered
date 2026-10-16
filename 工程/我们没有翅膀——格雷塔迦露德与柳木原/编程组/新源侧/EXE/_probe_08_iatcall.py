#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_08_iatcall.py — 找 .text 中对给定 IAT 槽 (绝对 VA) 的调用点 (只读).

同时解析该 IAT 槽名字 (走 _probe_01 的解析).
用法: python -X utf8 _probe_08_iatcall.py 0x4ED05C 0x4ED080 ...
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, iter_insns

pe = PE()


def iat_map():
    rva, sz = pe.ddirs[1]
    off = pe.rva_to_off(rva)
    raw = pe.data[off:off + sz]
    m = {}
    p = 0
    while p + 20 <= len(raw):
        ilt, ts, fc, name_rva, iat = struct.unpack_from("<IIIII", raw, p)
        if ilt == 0 and ts == 0 and name_rva == 0:
            break
        dll = pe.cstr(pe.image_base + name_rva, 64).decode("latin1")
        tho = pe.rva_to_off(ilt) if ilt else pe.rva_to_off(iat)
        ia = iat
        while tho is not None:
            ent = struct.unpack_from("<I", pe.data, tho)[0]
            if ent == 0:
                break
            fn = ("#%d" % (ent & 0xFFFF)) if (ent & 0x80000000) else \
                pe.cstr(pe.image_base + ent + 2, 64).decode("latin1")
            m[pe.image_base + ia] = (dll, fn)
            tho += 4
            ia += 4
        p += 20
    return m


iat = iat_map()
t0, t1 = pe.sec_range(".text")
targets = {}
for a in sys.argv[1:]:
    v = int(a, 0)
    targets[v] = iat.get(v, ("?", "?"))

for ins in iter_insns(pe, t0, t1):
    if ins.mnemonic == "call" and ins.op_str.startswith("dword ptr [0x"):
        try:
            v = int(ins.op_str[len("dword ptr ["):-1], 16)
        except ValueError:
            continue
        if v in targets:
            dll, fn = targets[v]
            print("0x%08X  call [0x%08X] = %s!%s" % (ins.address, v, dll, fn))
