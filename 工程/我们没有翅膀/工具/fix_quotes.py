# -*- coding: utf-8 -*-
"""fix_quotes.py —— 补齐「引号整体缺失」的台词（ISSUE-20260917-14）

问题（2026-09-18 由第 090 批发现、主代理核实）：部分批次把 `「…」` 的引号**整个丢掉**，
译文读起来变成旁白而非台词。实测 **2,827 槽**受影响（024/026/033/036 等批各约 290 处）。

修复规则（只做**可判定**的情形，不猜）：
  · 原文 body **以 `「` 开头且以 `」` 结尾**，且译文**不含任何引号** → 把译文整体包成 `“…”`
  · 原文 body **以 `『` 开头且以 `』` 结尾**，且译文不含引号 → 包成 `‘…’`
  · 其它情形（引号只在一侧、句中嵌套、译文已有引号）**不动**，仅报告，交收尾人工复核

用法：python -X utf8 fix_quotes.py [--apply]
"""
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
MANIFEST = os.path.join(PROJ, '语料', '可译清单.json')
QUOTES = ('“', '”', '‘', '’')


def main():
    apply = '--apply' in sys.argv
    man = {r['slot']: r for r in json.load(open(MANIFEST, encoding='utf-8'))}
    fixed = skipped = 0
    skip_ex = []
    for f in sorted(glob.glob(os.path.join(TRANS, 'batch_*.tsv'))):
        out, n = [], 0
        for line in io.open(f, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            p = line.split('\t')
            slot, cn = p[0], '\t'.join(p[1:])
            m = man.get(slot)
            if m and any(q in cn for q in QUOTES) is False:
                jp = m['body'].strip()
                if jp.startswith('「') and jp.endswith('」') and len(jp) > 2:
                    if apply:
                        cn = '“' + cn + '”'
                    n += 1
                elif jp.startswith('『') and jp.endswith('』') and len(jp) > 2:
                    if apply:
                        cn = '‘' + cn + '’'
                    n += 1
                elif ('「' in jp or '『' in jp) and m['kind'] == 'dialogue':
                    skipped += 1
                    if len(skip_ex) < 6:
                        skip_ex.append((slot, jp[:36], cn[:36]))
            out.append(slot + '\t' + cn)
        if apply and n:
            io.open(f, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
        fixed += n
    print('%s可整体包裹的槽 = %d' % ('已修复 ' if apply else '待修复 ', fixed))
    print('需人工复核（引号不全在两端/嵌套）的槽 = %d' % skipped)
    for s in skip_ex:
        print('   ', s[0], '|JP:', s[1], '|CN:', s[2])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()