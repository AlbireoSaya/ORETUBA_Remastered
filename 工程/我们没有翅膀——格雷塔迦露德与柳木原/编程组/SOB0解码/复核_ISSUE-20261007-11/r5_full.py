# -*- coding: utf-8 -*-
"""复算 §8 陷阱①：把「场级共现」当采纳线时，同一 PSV type 会被多少个 V 认领。
本脚本**不复用被截断的 JSON**，而是从语料+金标全量重算。"""
import sys, os, json, collections, importlib.util
sys.path.insert(0, os.path.join(os.getcwd(), '编程组', '工具'))
spec = importlib.util.spec_from_file_location('p', '编程组/SOB0解码/_v_naming_probe.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
D = m.D
sc = m.load_scenes(); psv, _ = D.load_psv_timeline()
gold = {s: psv[s] for s in sc if s in psv}; N = len(gold); gs = sorted(gold)
t_sc = collections.defaultdict(set)
for sid in gs:
    for r in gold[sid]:
        if r.get('type') != 'Message': t_sc[r.get('type', '')].add(sid)
v_sc = collections.defaultdict(set)
for sid, d in sc.items():
    if sid in gold:
        for V, q, a in d['nodes']: v_sc[V].add(sid)
GATE = lambda P, base, nv, inter: P >= 0.90 and base < 0.95 and nv >= 20 and inter >= 20
# 口径 ①：每个 V 的「场级最优过闸 type」（按 P 降序、并列取 R 降序）
first = collections.defaultdict(list)
anyt = collections.defaultdict(list)
for V, vs in v_sc.items():
    rows = []
    for t, ts in t_sc.items():
        inter = vs & ts
        if not inter: continue
        rows.append((len(inter) / len(vs), len(inter) / len(ts), len(ts) / N, t, len(inter)))
    rows.sort(key=lambda x: (-x[0], -x[1], -x[2]))
    hit = None
    for P, R, base, t, inter in rows:
        if GATE(P, base, len(vs), inter):
            anyt[t].append(V)
            if hit is None: hit = t
    if hit: first[hit].append(V)
for name, c in (('① 每 V 取场级最优过闸 type', first), ('② 任意 type 都算（同 V 可计多次）', anyt)):
    print('--- %s ---' % name)
    tot = sum(len(v) for v in c.values())
    for t, vs in sorted(c.items(), key=lambda x: -len(x[1]))[:8]:
        print('   %-18s %2d 个' % (t, len(vs)))
    print('   >>> SpriteBG=%d  CharacterOpen=%d  SeStop=%d  Window=%d  BgmStop=%d  SePlay=%d'
          % (len(c['SpriteBG']), len(c['CharacterOpen']), len(c['SeStop']),
             len(c['Window']), len(c['BgmStop']), len(c['SePlay'])))
