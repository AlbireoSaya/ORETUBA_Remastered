#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_07_dll.py — 反汇编 DS_SPRITE.DLL 的导出与定位其控制对象 vtable (只读).

用法: python -X utf8 _probe_07_dll.py [ds|tvpgl] [--fn 0x60003720] [--va .. ]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _probe_common as C

DLLS = {
    "ds": os.path.join(C.HERE, "work", "DS_SPRITE.DLL"),
    "movie": r"D:\Gal\[Navel]我们没有翅膀\DS_MOVIE.DLL",
    "tvpgl": os.path.join(C.HERE, "work", "tvpgl.dll"),
}

which = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "ds"
pe = C.PE(DLLS[which])
print("== %s imgbase=0x%08X size=%d ==" % (DLLS[which], pe.image_base, len(pe.data)))
for s in pe.sections:
    print("   %-8s va=0x%08X vsz=0x%06X raw=0x%06X" %
          (s["name"], pe.image_base + s["vaddr"], s["vsize"], s["rawsize"]))

if "--fn" in sys.argv:
    va = int(sys.argv[sys.argv.index("--fn") + 1], 0)
    C.show(pe, va, 0x200, title="fn 0x%08X" % va)
elif "--va" in sys.argv:
    va = int(sys.argv[sys.argv.index("--va") + 1], 0)
    ln = int(sys.argv[sys.argv.index("--len") + 1], 0) if "--len" in sys.argv else 0x120
    C.show(pe, va, ln)
elif "--vt" in sys.argv:
    vt = int(sys.argv[sys.argv.index("--vt") + 1], 0)
    print("vtable @ 0x%08X:" % vt)
    for i in range(40):
        v = pe.u32(vt + 4 * i)
        if v is None:
            break
        tgt = v
        print("  [%2d] +0x%02X -> 0x%08X" % (i, 4 * i, tgt))
