# -*- coding: utf-8 -*-
"""fix_sokuon.py —— 统一「促音独用」台词（ISSUE-20260917-14）

作品级裁决：日文 `っ` 独用（`「っ！」` / `「……っ」` / `「…………っ！」`）**保留声音、统一作「唔」**，
省略号个数与末尾标点**原样保留**（促音本身不另加字，但它是有声的喉音，不译即漏信息）。
产出形如：`「…………っ！」` → `“…………唔！”`；`「っ！」` → `“唔！”`。

用法：python -X utf8 fix_sokuon.py     # 缺省=全部已产出批次
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
BATCH = os.path.join(PROJ, '语料', '批次')
TRANS = os.path.join(PROJ, '翻译工作区', '译文')

PAT = re.compile(r'^「(…*)っ([！？]*)」$')
PAT2 = re.compile(r'^(…*)っ([！？]*)$')


def load_batch(name):
    rows = {}
    with open(os.path.join(BATCH, name + '.tsv'), encoding='utf-8') as f:
        f.readline()
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 7:
                rows[p[1]] = p[6].replace('\\n', '\n').strip()
    return rows


def main():
    names = sys.argv[1:] or sorted(os.path.basename(p)[:-4]
                                   for p in glob.glob(os.path.join(TRANS, 'batch_*.tsv')))
    grand = 0
    for name in names:
        src = load_batch(name)
        p = os.path.join(TRANS, name + '.tsv')
        if not os.path.exists(p):
            continue
        out, n = [], 0
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            slot = line.split('\t')[0]
            cn = '\t'.join(line.split('\t')[1:])
            jp = src.get(slot, '')
            m = PAT.match(jp)
            m2 = PAT2.match(jp)
            if m:
                want = '“%s唔%s”' % (m.group(1), m.group(2))
            elif m2:
                want = '%s唔%s' % (m2.group(1), m2.group(2))
            else:
                out.append(slot + '\t' + cn)
                continue
            if cn != want:
                cn = want
                n += 1
            out.append(slot + '\t' + cn)
        open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
        if n:
            print('%s: 统一促音独用 %d 处' % (name, n))
        grand += n
    print('合计 %d 处' % grand)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
