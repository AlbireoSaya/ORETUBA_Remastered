#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_06_strings.py — 只读转储 .data/.rdata 中的可打印串 (可选过滤)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE

pe = PE()
filt = sys.argv[1] if len(sys.argv) > 1 else None
pat = re.compile(filt, re.I) if filt else None

for secname in (".data", ".rdata"):
    lo, hi = pe.sec_range(secname)
    o = pe.off(lo)
    data = pe.data[o:o + (hi - lo)]
    i = 0
    while i < len(data):
        m = re.match(rb"[ -~]{4,}", data[i:])
        if m:
            s = m.group().decode("latin1")
            if pat is None or pat.search(s):
                print("%s 0x%08X  %s" % (secname, lo + i, s))
            i += len(m.group())
        else:
            i += 1
