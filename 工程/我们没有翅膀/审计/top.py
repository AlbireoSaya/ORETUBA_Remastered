# -*- coding: utf-8 -*-
import json, sys
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows.json', encoding='utf-8'))
rows.sort(key=lambda r: (-r['blk'], -r['ratio']))
print('=== blk>=12 全部槽（%d 条）===' % sum(1 for r in rows if r['blk']>=12))
for r in rows:
    if r['blk'] < 12: break
    print('[blk=%d ratio=%.2f] %s (addr=%d idx=%d %s) len %d/%d' %
          (r['blk'], r['ratio'], r['slot'], r['addr'], r['idx'], r['kind'], r['ltr'], r['lnm']))
    for sz, s in r['matches']:
        print('     <%.2d> %s' % (sz, s))
    print('     原: %s' % r['src'][:100])
    print('     我: %s' % r['tr'][:100])
    print('     米: %s' % r['nm'][:100])
