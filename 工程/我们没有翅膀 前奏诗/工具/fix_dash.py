# -*- coding: utf-8 -*-
"""fix_dash.py —— 统一拖音记号（作品层术语表 §五/§十）

判据（与 batch_009/010/015–019 已执行的口径一致）：
  `——` → `～` 当且仅当同时满足：
    ① 该槽原文 body **不含**破折号字符 `─`(U+2500) `―`(U+2015) `—`(U+2014)（即译文里的 `——` 不是破折号）
    ② 该 `——` 不在槽首（槽首 `——` 视为跨槽续行标记）
    ③ 该 `——` 之后紧跟的字符不是 `。！？…“”‘’）` 且不是行尾（即不是句尾拖长）
用法：python -X utf8 fix_dash.py [批次名 ...]   （缺省 = batch_008/011/012/013/014）
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
MAN = {r['slot']: r for r in json.load(open(os.path.join(PROJ, '语料', '可译清单.json'), encoding='utf-8'))}

DASHES = ('\u2500', '\u2015', '\u2014')
SENT_END = '。！？…“”‘’）'


def fix(cn):
    out, i, n = [], 0, 0
    while i < len(cn):
        if cn.startswith('——', i):
            prev = out[-1] if out else ''
            nxt = cn[i + 2] if i + 2 < len(cn) else ''
            if prev != '' and nxt != '' and nxt not in SENT_END:
                out.append('～')
                n += 1
                i += 2
                continue
        out.append(cn[i])
        i += 1
    return ''.join(out), n


names = sys.argv[1:] or ['batch_008', 'batch_011', 'batch_012', 'batch_013', 'batch_014']
total = 0
for name in names:
    p = os.path.join(TRANS, name + '.tsv')
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
        if any(d in jp for d in DASHES):
            out.append(ln)
            continue
        cn2, k = fix(cn)
        n += k
        out.append(slot + '\t' + cn2)
    if n:
        io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    total += n
    print('%-14s 拖音 ——→～ %d 处' % (name, n))
print('合计 =', total)