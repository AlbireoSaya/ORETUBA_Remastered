# -*- coding: utf-8 -*-
import collections
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
c = collections.Counter()
samples = collections.defaultdict(list)
tot = 0
for f in sorted(glob.glob('*.jsonl')):
    for ln in open(f, encoding='utf-8'):
        r = json.loads(ln)
        if r['kind'] != 'other':
            continue
        tot += 1
        b = r['body']
        if ('\\' in b) or ('/' in b) or ('.' in b and b.isascii()):
            k = 'resource'
        elif len(b) <= 2:
            k = 'short'
        else:
            k = 'text'
        c[k] += 1
        if len(samples[k]) < 15:
            samples[k].append((os.path.basename(f), b[:70]))
print('other 合计', tot, dict(c))
for k, v in samples.items():
    print('---', k)
    for a, b in v:
        print('   ', a, '|', repr(b))