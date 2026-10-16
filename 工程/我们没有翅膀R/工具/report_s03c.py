# -*- coding: utf-8 -*-
r"""亜衣线（s03c_*）专项检查报告（ISSUE-20260915-06）：只读。用法：
python -X utf8 report_s03c.py <新 SCRIPT.LPK>
输出：跨度统计 / 乱码残留 / 截断清单 / 抽样对照（日文原句 → 中文成句）
"""
import os, sys, json, collections

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
CACHE = os.path.join(WS, '临时', '_audit_cache', 'orig')
NEW = sys.argv[1]

slash = json.load(open(os.path.join(Y, 'R版台词.json'), encoding='utf-8'))
trunc = json.load(open(os.path.join(Y, '等长补齐_截断清单.json'), encoding='utf-8'))
mig = json.load(open(os.path.join(Y, 'R版迁移映射.json'), encoding='utf-8'))
newm = json.load(open(os.path.join(Y, '新增译文映射.json'), encoding='utf-8'))

cn_by = {}
for r in mig + newm:
    if r.get('offset') is None:
        continue
    cn_by[(r['file'], int(r['offset']))] = r.get('cn') or r.get('text') or ''

lp = LP.load(NEW)
ents = {n: LP.read_entry(lp, n)['plain'] for n, num in lp['ents']}

s03c = sorted(set(r['file'] for r in slash if r['file'].startswith('s03c_')))
print('亜衣线文件数: %d' % len(s03c))
tot = chg = unt = 0
samples = []
for r in slash:
    if not r['file'].startswith('s03c_'):
        continue
    o = r.get('offset')
    if o is None:
        continue
    f, off, ln = r['file'], int(o), int(r.get('len') or 0)
    if ln <= 0:
        continue
    tot += 1
    a = open(os.path.join(CACHE, f), 'rb').read()
    b = ents[f]
    if a[off:off + ln] == b[off:off + ln]:
        unt += 1
    else:
        chg += 1
    if len(samples) < 400 and ln > 8:
        jp = a[off:off + ln].decode('cp932', 'replace')
        cn = b[off:off + ln].decode('gbk', 'replace')
        samples.append((f, off, ln, jp, cn))
print('台词跨度: %d；已写入(中文) %d；未改动 %d' % (tot, chg, unt))

tr = [x for x in trunc if x['file'].startswith('s03c_')]
print('截断条目（s03c）: %d / 全部 %d' % (len(tr), len(trunc)))
tb = collections.Counter(x['file'] for x in tr)
print('   截断最多的文件:', dict(tb.most_common(8)))
for x in tr[:6]:
    print('   [截断] %-14s @%-6d need=%d\n      原文译: %r\n      截后:   %r'
          % (x['file'], x['offset'], x['need'], x['cn'][:60], x['kept'][:60]))

print('\n抽样对照（日文原句 → 中文成句，含截断后形态）:')
import random
random.seed(20260915)
for f, off, ln, jp, cn in random.sample(samples, min(12, len(samples))):
    print('   %-14s @%-6d len=%d' % (f, off, ln))
    print('      JP: %s' % jp[:52])
    print('      CN: %s' % cn[:52])
