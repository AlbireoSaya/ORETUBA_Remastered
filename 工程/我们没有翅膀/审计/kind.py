# -*- coding: utf-8 -*-
import json
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows_n.json', encoding='utf-8'))
def st(v):
    v=sorted(v); n=len(v)
    return 'n=%d 均值%.2f 中位%d p90=%d p95=%d max=%d' % (n, sum(v)/n, v[n//2], v[int(n*.9)], v[int(n*.95)], v[-1])
for k in ('dialogue','other','ascii'):
    g=[r for r in rows if r['kind']==k]
    if g: print('%-9s blk: %s' % (k, st([r['blk'] for r in g])))
g=[r for r in rows if r['ltr']>=40]
print('len>=40    blk: %s ; blk>=15 的槽 = %d' % (st([r['blk'] for r in g]), sum(1 for r in g if r['blk']>=15)))
for r in g:
    if r['blk']>=15: print('  ', r['slot'], 'blk=%d nblk=%d ratio=%.2f' % (r['blk'],r['nblk'],r['ratio']))
