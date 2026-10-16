# -*- coding: utf-8 -*-
import json, statistics
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows_n.json', encoding='utf-8'))
L = [r['ltr'] for r in rows]
print('我方译文长度: 均值%.1f 中位%d 最短%d 最长%d' % (sum(L)/len(L), statistics.median(L), min(L), max(L)))
print('我方译文总字数 =', sum(L))
long_ = [r for r in rows if r['ltr'] >= 30]
print('长度>=30 的槽 =', len(long_))
print()
print('### A. 原始最长连续公共子串 blk>=15 的全部槽 (%d 条)' % sum(1 for r in rows if r['blk']>=15))
for r in sorted(rows, key=lambda x: -x['blk']):
    if r['blk'] < 15: break
    print('- %s blk=%d nblk=%d ratio=%.2f len=%d/%d | 我: %s || 米: %s'
          % (r['slot'], r['blk'], r['nblk'], r['ratio'], r['ltr'], r['lnm'], r['tr'], r['nm']))
print()
print('### B. ratio>=0.90 且长度>=20 的槽')
n=0
for r in sorted(rows, key=lambda x: -x['ratio']):
    if r['ratio'] < 0.90 or r['ltr'] < 20: continue
    n+=1
    print('- %s ratio=%.2f blk=%d nblk=%d len=%d/%d | 我: %s || 米: %s'
          % (r['slot'], r['ratio'], r['blk'], r['nblk'], r['ltr'], r['lnm'], r['tr'], r['nm']))
print('小计', n)
print()
print('### C. ratio>=0.95（不限长度）')
for r in sorted(rows, key=lambda x: -x['ratio']):
    if r['ratio'] < 0.95: continue
    print('- %s ratio=%.3f blk=%d len=%d/%d | 我: %s || 米: %s' % (r['slot'], r['ratio'], r['blk'], r['ltr'], r['lnm'], r['tr'], r['nm']))
print()
print('### D. 分批次')
import collections
by = collections.defaultdict(list)
for r in rows: by[r['batch']].append(r)
for k in sorted(by):
    g = by[k]; rr = sorted(x['ratio'] for x in g); bb = sorted(x['blk'] for x in g)
    print('batch_%03d n=%d ratio均值%.3f 中位%.3f | blk中位%d p95=%d max=%d | blk>=15:%d'
          % (k, len(g), sum(rr)/len(rr), rr[len(rr)//2], bb[len(bb)//2], bb[int(len(bb)*.95)], bb[-1],
             sum(1 for x in bb if x>=15)))
