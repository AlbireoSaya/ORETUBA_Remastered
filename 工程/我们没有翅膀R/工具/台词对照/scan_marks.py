# -*- coding: utf-8 -*-
"""扫描译文中的脚本标记泄漏（#名字$& 之类），用于数据质量提示。"""
import json, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
OUT = os.path.join(ROOT, '亜衣线资源', '剧本')

MARKS = ['$&', 'AI_', '「', '』']
SUSPECT = ['$&', 'AI_']


def suspicious(v):
    return any(m in v for m in SUSPECT)


d = json.load(open(os.path.join(OUT, '台词对照.json'), encoding='utf-8'))
fl = [(s['file'], l) for s in d['scenes'] for l in s['lines']]
hit = [(f, l) for f, l in fl if suspicious(l['cn'] or '')]
print('本线路 cn 含 $& / AI_ 的行数:', len(hit))
for f, l in hit:
    print('  %-14s kind=%-9s off=%-6s src=%-4s trunc=%d' % (f.replace('.tob', ''), l['kind'], l['offset'], l['source'], l['truncated']))
    print('     jp:', (l['jp'] or '')[:70])
    print('     cn:', l['cn'])

print()
print('全库同项扫描:')
for p, fld in [('R版迁移映射.json', 'cn'), ('新增译文映射.json', 'text')]:
    arr = json.load(open(os.path.join(ROOT, '语料', p), encoding='utf-8'))
    n = sum(1 for r in arr if suspicious(r.get(fld) or ''))
    print('  %-24s 含标记 %d / %d' % (p, n, len(arr)))

# 场景标题行的完整性检查：标题译文中若含句末句号或长度异常则列出
print()
print('标题行（kind=title）逐条：jp -> cn / 是否含标记')
tt = [(f, l) for f, l in fl if l['kind'] == 'title']
print('title 条数', len(tt), '｜含标记', sum(1 for f, l in tt if suspicious(l['cn'] or '')))
