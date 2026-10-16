# -*- coding: utf-8 -*-
"""final_stats.py —— 归档头对比 + SCRIPT.LPK 日文正文规模（只读）"""
import os
import re
import sys
import struct

TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
sys.path.insert(0, TOOLS)
import lpk_patch as LP  # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
SCEN = re.compile(r'^s\d\d[a-z]?_\d+[a-z]?\d*\.sob$', re.I)

print('=== 归档头 8 字节（魔数 + 索引长^key 字）===')
for name in ['BGM.LPK', 'CHR.LPK', 'DATA.LPK', 'PIC.LPK', 'SCRIPT.LPK', 'SE.LPK', 'SYS.LPK', 'VOICE.LPK']:
    with open(os.path.join(GAME, name), 'rb') as f:
        h = f.read(8)
    w = struct.unpack_from('<I', h, 4)[0]
    print('  %-12s %s  u32=0x%08x  flags=(w^key)>>24 待解' % (name, h[:4].decode(), w))

lp = LP.load(os.path.join(GAME, 'SCRIPT.LPK'))
jp_bytes = 0
msg = 0
plain_total = 0
n_scen = 0
for name, num in sorted(lp['ents']):
    if not name.lower().endswith('.sob'):
        continue
    if SCEN.match(name):
        n_scen += 1
    p = LP.read_entry(lp, name)['plain']
    plain_total += len(p)
    jp_bytes += sum(1 for b in p if b >= 0x80)
    msg += p.count(b'$&')

print('\n=== SCRIPT.LPK 剧情正文规模 ===')
print('  剧情脚本文件数 %d（另有系统 .sob %d）' % (n_scen, 413 - n_scen))
print('  全部 .sob 解压后明文合计 %d 字节（%.1f MB）' % (plain_total, plain_total / 1048576.0))
print('  其中非 ASCII（日文双字节）字节 %d（%.1f MB）' % (jp_bytes, jp_bytes / 1048576.0))
print('  `$&`（台词正文定界符）出现次数 %d → 约 %d 条台词/文本槽' % (msg, msg))
