# -*- coding: utf-8 -*-
"""判别测试：高频（套语/固定搭配）→ 收敛必然；低频/唯一 → 可疑"""
import json, collections
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows_n.json', encoding='utf-8'))
corpus = ''.join(r['tr'] for r in rows)
tot = len(corpus)
print('我方语料总字数 =', tot)
print()
print('%-24s %-6s %-6s %-8s %s' % ('slot', 'blk', 'nblk', '共通串', '共通串在我方语料出现次数'))
out=[]
for r in sorted(rows, key=lambda x: -x['nblk']):
    if r['nblk'] < 12: break
    s = r['nstr']
    out.append((r, corpus.count(s)))
for r, c in out:
    print('[%s] blk=%d nblk=%d n=%d  %s' % (r['slot'], r['blk'], r['nblk'], c, r['nstr'][:40]))
print()
eq = [r for r in rows if r['tr'] == r['nm']]
print('完全相同（整槽逐字）的槽 = %d 条；最长 %d 字' % (len(eq), max(len(r['tr']) for r in eq)))
print('  其中长度>=15 的 = %d 条' % sum(1 for r in eq if len(r['tr']) >= 15))
for r in sorted(eq, key=lambda x: -len(x['tr']))[:20]:
    print('   %2d字 %s  %s' % (len(r['tr']), r['slot'], r['tr']))
