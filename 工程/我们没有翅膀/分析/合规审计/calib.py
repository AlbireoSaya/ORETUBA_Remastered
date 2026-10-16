# -*- coding: utf-8 -*-
"""校准：模拟「抄袭后轻度改写」的 blk 签名，与我方实测对照"""
import json, random, difflib, statistics
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows_n.json', encoding='utf-8'))
def stats(v):
    v = sorted(v); n=len(v)
    return (sum(v)/n, v[n//2], v[int(n*.90)], v[int(n*.95)], v[n-1])
print('实测 我方 vs 新米 blk : 均值%.2f 中位%d p90=%d p95=%d max=%d' % stats([r['blk'] for r in rows]))
print('实测 我方 vs 新米 nblk: 均值%.2f 中位%d p90=%d p95=%d max=%d' % stats([r['nblk'] for r in rows]))
random.seed(7)
for p in (0.05, 0.10, 0.20, 0.30):
    v=[]
    for r in rows:
        s = r['nm']
        k = ''.join(ch for i,ch in enumerate(s) if random.random() >= p)
        if len(k) < 2: v.append(0); continue
        sm = difflib.SequenceMatcher(None, k, s, autojunk=False)
        v.append(max(b.size for b in sm.get_matching_blocks()))
    print('校准 新米原文 vs 新米删字%2d%%: 均值%.2f 中位%d p90=%d p95=%d max=%d'
          % (int(p*100), *stats(v)))
print()
long_ = [r for r in rows if r['ltr'] >= 40]
print('长度>=40 的槽 = %d 条；blk: 均值%.2f 中位%d p90=%d p95=%d max=%d'
      % (len(long_), *stats([r['blk'] for r in long_])))
dlg = [r for r in rows if r['kind'] == 'dialogue']; oth = [r for r in rows if r['kind'] != 'dialogue']
print('dialogue n=%d blk均值%.2f p95=%d max=%d | other n=%d blk均值%.2f p95=%d max=%d'
      % (len(dlg), *stats([r['blk'] for r in dlg])[:2], stats([r['blk'] for r in dlg])[3], stats([r['blk'] for r in dlg])[4],
         len(oth), stats([r['blk'] for r in oth])[0], stats([r['blk'] for r in oth])[3], stats([r['blk'] for r in oth])[4]))
print('长度>=40 且 blk>=15 的槽 =', sum(1 for r in long_ if r['blk']>=15))
for r in long_:
    if r['blk'] >= 15: print('   ', r['slot'], r['blk'], r['nstr'] if r['nblk']>=12 else '')
