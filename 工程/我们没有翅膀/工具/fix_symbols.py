# -*- coding: utf-8 -*-
"""fix_symbols.py —— 符号回退定点修正（ISSUE-20260917-14）

`♪`(U+266A) **不可 GBK 编码**。作品级裁决：按通用层回退表 **`♪ → ☆`**（不得删除，删除=丢信息）。
本脚本只改「原文含 ♪ 而译文既无 ♪ 也无 ☆」的槽：
  ♪ 位于正文首 → 前置 ☆；位于正文尾 → 追加 ☆；位于中间 → 原位替换为 ☆（按出现序号对齐）。

用法：python -X utf8 fix_symbols.py batch_008 [batch_NNN ...]
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
        if not os.path.exists(p):
            print('%s: 无译文，跳过' % name)
            continue
        out, n = [], 0
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            slot = line.split('\t')[0]
            cn = '\t'.join(line.split('\t')[1:])
            jb = src.get(slot, '')
            k = jb.count('♪')
            if k and cn.count('☆') < k:
                need = k - cn.count('☆')
                body = cn.lstrip('-?0123456789<>\\')       # 跳过内嵌控制码
                ctl = cn[:len(cn) - len(body)]
                for _ in range(need):
                    if jb.strip().startswith('♪'):
                        body = '☆' + body
                    elif jb.strip().endswith('♪'):
                        body = body + '☆'
                    else:
                        body = body.replace('～', '☆', 1) if '☆' not in body else body
                cn = ctl + body
                n += 1
            out.append(slot + '\t' + cn)
        open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
        print('%s: 补回 ♪→☆ 共 %d 槽' % (name, n))
        total += n
    print('合计 %d 槽' % total)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
