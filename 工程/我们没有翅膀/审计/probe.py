# -*- coding: utf-8 -*-
import sys, os, json, struct
sys.path.insert(0, r'E:\ZCode Workspace\Galgame\临时\wt14\工程\我们没有翅膀\工具')
from extract_sob0 import parse_sob0

P = r'D:\Gal\[Navel]我们没有翅膀\SCRIPT_CHS'
for name in ('s00_00.sob','s01_01a.sob','s01_02a.sob'):
    fp = os.path.join(P, name)
    d = open(fp,'rb').read()
    texts, info = parse_sob0(d)
    print(name, 'size', len(d), 'info', info)
    if texts is None: continue
    print('  textslots', len(texts))
    for t in texts[:6]:
        raw = t['raw']
        b = raw.split(b'$&',1)[1] if b'$&' in raw else raw
        if b.endswith(b'$'): b = b[:-1]
        try: s = b.decode('gbk')
        except Exception as e: s = '<GBKFAIL %s>' % e
        print('   addr=%d idx=%d sel=%d raw=%r -> %s' % (t['addr'],t['idx'],t['sel'],raw[:60],s[:60]))
