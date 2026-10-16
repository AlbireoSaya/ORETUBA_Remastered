# -*- coding: utf-8 -*-
"""fix_keishou.py —— 按作品级裁决统一敬称落点（ISSUE-20260917-14）

裁决（作品层 术语表 §三之二）：**姓氏／名字＋くん → ○○君**；**さん → ○○同学**。
本脚本对已产出批次做**有原文依据**的定点回改：仅当**日文原文含 `Xくん`** 且译文含 `X同学` 时才替换，
避免把 `Xさん`（正确作「X同学」）误改。

用法：python -X utf8 fix_keishou.py batch_002 [batch_003 ...]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
BATCH = os.path.join(PROJ, '语料', '批次')
TRANS = os.path.join(PROJ, '翻译工作区', '译文')


def load_batch(name):
    rows = {}
    with open(os.path.join(BATCH, name + '.tsv'), encoding='utf-8') as f:
        f.readline()
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 7:
                rows[p[1]] = p[6].replace('\\n', '\n')
    return rows


def main():
    total = 0
    for name in sys.argv[1:]:
        src = load_batch(name)
        p = os.path.join(TRANS, name + '.tsv')
        lines = open(p, encoding='utf-8').read().split('\n')
        out, n = [], 0
        for line in lines:
            if not line.strip():
                continue
            slot, cn = line.split('\t')[0], '\t'.join(line.split('\t')[1:])
            jb = src.get(slot, '')
            # 找原文里所有「Xくん」（X = 1–4 个非空白字符，可取汉字/假名）
            for m in re.finditer(r'([^\s、。！？「」『』]{1,4})くん', jb):
                x = m.group(1)
                if x + '同学' in cn:
                    cn = cn.replace(x + '同学', x + '君')
                    n += 1
            out.append(slot + '\t' + cn)
        open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
        print('%s: 回改 %d 处「○同学 → ○君」' % (name, n))
        total += n
    print('合计 %d 处' % total)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
