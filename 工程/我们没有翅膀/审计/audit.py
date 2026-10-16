# -*- coding: utf-8 -*-
"""授权边界审计：我方译文(11批/5500槽) vs 新米汉化 SCRIPT_CHS 同(addr,idx)槽"""
import sys, os, json, re, difflib, statistics, collections
sys.path.insert(0, r'E:\ZCode Workspace\Galgame\临时\wt14\工程\我们没有翅膀\工具')
from extract_sob0 import parse_sob0

ROOT = r'E:\ZCode Workspace\Galgame\临时\wt14\工程\我们没有翅膀'
MAN  = os.path.join(ROOT, '语料', '可译清单.json')
TRD  = os.path.join(ROOT, '翻译工作区', '译文')
CHS  = r'D:\Gal\[Navel]我们没有翅膀\SCRIPT_CHS'

def body_of(raw):
    b = raw
    if b'$&' in b:
        b = b.split(b'$&', 1)[1]
    if b.endswith(b'$'):
        b = b[:-1]
    return b

# ---- 1. slot -> (script, addr, idx, body_src)
man = json.load(open(MAN, encoding='utf-8'))
slot2 = {}
for e in man:
    slot2[e['slot']] = e

# ---- 2. 逐批读取我方译文
slots = []
for n in range(1, 12):
    fp = os.path.join(TRD, 'batch_%03d.tsv' % n)
    with open(fp, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            if '\t' not in line:
                print('!! 无TAB:', n, line[:40]); continue
            s, t = line.split('\t', 1)
            slots.append((n, s, t))

# ---- 3. 解析新米 CHS 脚本
cache = {}
def chs_map(script):
    if script in cache:
        return cache[script]
    fp = os.path.join(CHS, script)
    if not os.path.exists(fp):
        cache[script] = None
        return None
    d = open(fp, 'rb').read()
    texts, info = parse_sob0(d)
    m = {}
    if texts:
        for t in texts:
            b = body_of(t['raw'])
            try:
                s = b.decode('gbk')
            except Exception:
                s = b.decode('gbk', 'replace')
            m[(t['addr'], t['idx'])] = s
    cache[script] = m
    return m

# ---- 4. 比对
rows = []
miss = collections.Counter()
for bn, slot, tr in slots:
    e = slot2.get(slot)
    if e is None:
        miss['slot不在可译清单'] += 1; continue
    m = chs_map(e['script'])
    if m is None:
        miss['CHS缺脚本:' + e['script']] += 1; continue
    k = (e['addr'], e['idx'])
    if k not in m:
        miss['CHS缺槽(%s addr=%d idx=%d)' % (e['script'], e['addr'], e['idx'])] += 1; continue
    nm = m[k]
    if not nm:
        miss['新米空串'] += 1; continue
    sm = difflib.SequenceMatcher(None, tr, nm, autojunk=False)
    ratio = sm.ratio()
    blk = max((b.size for b in sm.get_matching_blocks()), default=0)
    mbl = []
    for b in sm.get_matching_blocks():
        if b.size >= 6:
            mbl.append((b.size, tr[b.a:b.a+b.size]))
    mbl.sort(reverse=True)
    rows.append(dict(batch=bn, slot=slot, script=e['script'], addr=e['addr'], idx=e['idx'],
                     kind=e['kind'], src=e['body'], tr=tr, nm=nm, ratio=ratio, blk=blk,
                     matches=mbl[:3], ltr=len(tr), lnm=len(nm)))

json.dump(rows, open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows.json', 'w', encoding='utf-8'),
          ensure_ascii=False)

print('译文条数 =', len(slots), ' 成功配对 =', len(rows))
print('未配对：', dict(miss))
rs = [r['ratio'] for r in rows]
bl = [r['blk'] for r in rows]
rs.sort(); bl.sort()
def q(a, p): return a[min(len(a)-1, int(len(a)*p))]
print('ratio  均值=%.3f 中位=%.3f p75=%.3f p90=%.3f p95=%.3f p99=%.3f max=%.3f'
      % (sum(rs)/len(rs), q(rs,.5), q(rs,.75), q(rs,.90), q(rs,.95), q(rs,.99), rs[-1]))
print('ratio>=0.8 = %d ; >=0.6 = %d ; >=0.4 = %d ; >=0.3 = %d'
      % (sum(1 for x in rs if x>=.8), sum(1 for x in rs if x>=.6),
         sum(1 for x in rs if x>=.4), sum(1 for x in rs if x>=.3)))
print('连续公共子串 均值=%.2f 中位=%d p90=%d p95=%d p99=%d max=%d'
      % (sum(bl)/len(bl), q(bl,.5), q(bl,.90), q(bl,.95), q(bl,.99), bl[-1]))
for th in (8,10,12,15,18,20,25,30):
    print('  blk>=%d : %d 槽' % (th, sum(1 for x in bl if x>=th)))
