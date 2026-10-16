# -*- coding: utf-8 -*-
import json
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows_n.json', encoding='utf-8'))
def st(v):
    v=sorted(v); n=len(v)
    return 'n=%d 中位%d p95=%d max=%d' % (n, v[n//2], v[int(n*.95)], v[-1])
for k in ('dialogue','other'):
    g=[r for r in rows if r['kind']==k and r['ltr']>=40]
    print('%-9s len>=40 blk: %s ; blk>=15: %d' % (k, st([r['blk'] for r in g]), sum(1 for r in g if r['blk']>=15)))
    print('           ratio: ', end='')
    v=sorted(r['ratio'] for r in g); print('n=%d 均值%.3f 中位%.3f p95=%.3f max=%.3f' % (len(v), sum(v)/len(v), v[len(v)//2], v[int(len(v)*.95)], v[-1]))
print()
print('=== TOP20 (按 blk 降序) ===')
for i, r in enumerate(sorted(rows, key=lambda x: -x['blk'])[:20], 1):
    print('%2d. %s ratio=%.2f blk=%2d nblk=%2d len=%d/%d' % (i, r['slot'], r['ratio'], r['blk'], r['nblk'], r['ltr'], r['lnm']))
    print('    原: %s' % r['src'][:95].replace('\n','\n'))
    print('    我: %s' % r['tr'][:95].replace('\n','\n'))
    print('    米: %s' % r['nm'][:95].replace('\n','\n'))
