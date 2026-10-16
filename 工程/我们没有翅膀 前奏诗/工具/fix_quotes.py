# -*- coding: utf-8 -*-
"""fix_quotes.py —— 补齐译文缺失的外层中文引号（一审打回项）

判据：原文 body 以 `「` 起、以 `」` 收（台词槽）时，译文必须以 `“` 起、`”` 收
      （通用规范「「」→“”」）。实测 batch_001/009/010/011/018(staff)/019 共 963 槽缺失。
"""
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
MAN = {r['slot']: r for r in json.load(open(os.path.join(PROJ, '语料', '可译清单.json'), encoding='utf-8'))}

total = 0
for p in sorted(glob.glob(os.path.join(TRANS, 'batch_*.tsv'))):
    lines = io.open(p, encoding='utf-8').read().split('\n')
    out, n = [], 0
    for ln in lines:
        if not ln or ln.startswith('slot\t'):
            out.append(ln)
            continue
        parts = ln.split('\t')
        if len(parts) < 2:
            out.append(ln)
            continue
        slot, cn = parts[0], '\t'.join(parts[1:])
        r = MAN.get(slot)
        jp = r['body'] if r else ''
        if jp.startswith('「'):
            core = jp[:-1] if jp.endswith('$') else jp
            if core.endswith('」') and '“' not in cn and '”' not in cn:
                cn = '“' + cn + '”'
                n += 1
        out.append(slot + '\t' + cn)
    if n:
        io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    total += n
    if n:
        print('%-18s 补引号 %d 槽' % (os.path.basename(p), n))
print('合计补引号 =', total)