#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_10_vtables.py — 在 .rdata/.data 中枚举 vtable 候选 (连续 >=N 个指向 .text 的 dword) (只读).

用法:
  python -X utf8 _probe_10_vtables.py --contains 0x4956C0
  python -X utf8 _probe_10_vtables.py --range 0x495600 0x495E00
  python -X utf8 _probe_10_vtables.py --all
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE

pe = PE()
t0, t1 = pe.sec_range(".text")
MINRUN = 4


def collect():
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
                if len(vals) >= MINRUN:
                    runs.append((lo + 4 * i, secname, vals))
                i = j
            else:
                i += 1
    return runs


runs = collect()
if "--contains" in sys.argv:
    tgt = int(sys.argv[sys.argv.index("--contains") + 1], 0)
    print("vtables containing 0x%08X:" % tgt)
    for va, sec, vals in runs:
        if tgt in vals:
            idx = vals.index(tgt)
            print("  vt=0x%08X (%s) len=%d  idx=%d offset=+0x%02X"
                  % (va, sec, len(vals), idx, 4 * idx))
elif "--range" in sys.argv:
    lo = int(sys.argv[sys.argv.index("--range") + 1], 0)
    hi = int(sys.argv[sys.argv.index("--range") + 2], 0)
    print("vtables whose entries fall in [0x%X,0x%X):" % (lo, hi))
    for va, sec, vals in runs:
        sub = [v for v in vals if lo <= v < hi]
        if sub:
            print("  vt=0x%08X (%s) len=%d  in-range=%d: %s"
                  % (va, sec, len(vals), len(sub), " ".join("0x%X" % v for v in sub[:12])))
else:
    print("total vtable-run candidates:", len(runs))
    for va, sec, vals in runs:
        print("  vt=0x%08X (%s) len=%d : %s" %
              (va, sec, len(vals), " ".join("0x%X" % v for v in vals[:8])))
