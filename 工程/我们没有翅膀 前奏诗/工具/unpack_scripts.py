#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《我们没有翅膀 前奏诗》SCRIPT.LPK 全量解包。
用法: python unpack_scripts.py <SCRIPT.LPK> <输出目录>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as P

LPK = sys.argv[1] if len(sys.argv) > 1 else r'D:/Gal/壌偨偪偵梼偼側偄乣Prelude乣/SCRIPT.LPK'
OUT = sys.argv[2] if len(sys.argv) > 2 else r'../解包/SCRIPT'

os.makedirs(OUT, exist_ok=True)
lp = P.load(LPK)
print('条目数', len(lp['ents']), 'flags=0x%02x' % lp['flags'])

summary = []
for name, num in sorted(lp['ents'], key=lambda x: x[1]):
    e = P.read_entry(lp, name)
    plain = e['plain']
    path = os.path.join(OUT, name)
    with open(path, 'wb') as f:
        f.write(plain)
    magic = plain[:4]
    summary.append((name, len(plain), magic))

print('%-18s %10s  %s' % ('name', 'bytes', 'magic'))
for name, ln, magic in summary:
    try:
        m = magic.decode('ascii')
    except UnicodeDecodeError:
        m = magic.hex()
    print('%-18s %10d  %s' % (name, ln, m))
print('合计 %d 文件, %d 字节' % (len(summary), sum(s[1] for s in summary)))