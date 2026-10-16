# -*- coding: utf-8 -*-
import sys, os, io, json, collections
sys.path.insert(0, os.path.join(os.getcwd(), '编程组', '工具'))
import importlib.util
spec = importlib.util.spec_from_file_location('p', '编程组/SOB0解码/_v_naming_probe.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
D = m.D
fl = D.Sob0(os.path.join(D.SOURCES['ot']['dir'], 'func_lib.sob'))
t1 = json.load(open('编程组/SOB0解码/_v_naming.json', encoding='utf-8'))['t1']

# (a) 无 0x120 串、但 0x200/0x400 有串
no120 = [k for k, e in t1.items() if not e['sens']['0x120']['first']
         and (e['sens']['0x200']['first'] or e['sens']['0x400']['first'])]
print('(a) 0x120 无串但 0x200/0x400 有串 =', len(no120))
for k in sorted(no120, key=lambda x: -t1[x]['nodes_all']):
    e = t1[k]
    f = lambda w: e['sens'][w]['first'] or '-'
    print('    %-9s nodes=%-6d gap=%-6d 0x200=%-10s 0x400=%-10s overrun200=%s'
          % (k, e['nodes_all'], e['gap_to_next_V'], f('0x200')[:10], f('0x400')[:10], e['gap_to_next_V'] < 0x200))

# (b) 全 93 head 分布 + 非 0xB/0x20 者的样例
hd = collections.Counter(e['head'] for e in t1.values())
print('(b) head 全分布 =', dict(sorted(hd.items(), key=lambda x: -x[1])))
for h in ('0x23', '0x28', '0x1F', '0x4'):
    vs = sorted([k for k, e in t1.items() if e['head'] == h], key=lambda x: -t1[x]['nodes_all'])
    print('    head=%s (%d 个):' % (h, len(vs)))
    for k in vs:
        e = t1[k]
        print('       %-9s nodes_cmd=%-6d walk=%s' % (k, e['nodes_cmd'], ",".join(e['walk_tags'])))

# (c) 0x14084 -> 0x17514 相邻（两口径）
def adj(files, tag):
    import glob
    nA = nAnext = nBnA = nB = 0
    for fn in sorted(files):
        try: s = D.Sob0(fn)
        except Exception: continue
        nodes = s.command_nodes()
        vs = [s.cells[i + 1] for i in nodes]
        for k, v in enumerate(vs):
            if v == 0x14084:
                nA += 1
                if k + 1 < len(vs) and vs[k + 1] == 0x17514: nAnext += 1
            if v == 0x17514:
                nB += 1
                if k > 0 and vs[k - 1] == 0x14084: nBnA += 1
    print('(c) [%s] 0x14084=%d 其中下一个是 0x17514 的 %d (%.4f) | 0x17514=%d 其中上一个是 0x14084 的 %d (%.4f)'
          % (tag, nA, nAnext, nAnext / nA, nB, nBnA, nBnA / nB))
sc = m.load_scenes()
corpus = set()
for line in io.open(os.path.join(D.SCENE_DIR, 'scene_ot.jsonl'), encoding='utf-8'):
    o = json.loads(line)
    p = os.path.join(D.SOURCES['ot']['dir'], o['script'] + '.sob')
    if os.path.isfile(p): corpus.add(p)
adj(corpus, '语料 367 场')
adj([os.path.join(D.SOURCES['ot']['dir'], f) for f in sorted(os.listdir(D.SOURCES['ot']['dir'])) if f.endswith('.sob')], '全库 412 文件')

# (d) 场级闸门：每个 V 全部 type 的场级候选（P>=0.90, base<0.95）；统计每 type 的候选 V 数
psv, _ = D.load_psv_timeline()
gold = {s: psv[s] for s in sc if s in psv}; gs = sorted(gold)
t_sc = collections.defaultdict(set)
for sid in gs:
    for r in gold[sid]:
        t_sc[r.get('type', '')].add(sid)
v_sc = collections.defaultdict(set)
for sid, d in sc.items():
    if sid in gold:
        for V, q, a in d['nodes']: v_sc[V].add(sid)
N = len(gs)
cand = collections.defaultdict(list)
for V, vs in v_sc.items():
    for t, ts in t_sc.items():
        inter = vs & ts
        if not inter: continue
        P = len(inter) / len(vs); base = len(ts) / N
        if P >= 0.90 and base < 0.95 and len(vs) >= 20:
            cand[t].append(V)
print('(d) 场级闸门(P>=.90, base<.95, |V场|>=20) 每个 type 的候选 V 数（>=2 的）：')
for t, vs in sorted(cand.items(), key=lambda x: -len(x[1])):
    if len(vs) >= 2:
        print('    %-18s %d 个: %s' % (t, len(vs), ", ".join('0x%X' % v for v in sorted(vs))))
print('    SpriteBG=%d CharacterOpen=%d SeStop=%d' %
      (len(cand['SpriteBG']), len(cand['CharacterOpen']), len(cand['SeStop'])))

# (e) 单事件 seq 的 type 先验
seq_label = {}
for sid in gs:
    by = collections.defaultdict(list)
    for r in gold[sid]:
        if r.get('type') == 'Message': continue
        by[str(r['seq'])].append(r['type'])
    for q, ts in by.items():
        if len(ts) == 1: seq_label[(sid, q)] = ts[0]
prior = collections.Counter(seq_label.values())
tot = sum(prior.values())
print('(e) 单事件 seq 总数=%d；type 先验 top5 = %s'
      % (tot, [(t, n, round(n / tot, 4)) for t, n in prior.most_common(5)]))

# (f) 0x1AD18 的 EyeCatch / EyeCatchEnd 计数签名是否完全相同
vc = collections.defaultdict(collections.Counter); tc = collections.defaultdict(collections.Counter)
for sid, d in sc.items():
    if sid in gold:
        for V, q, a in d['nodes']: vc[V][sid] += 1
for sid in gs:
    for r in gold[sid]:
        if r.get('type') != 'Message': tc[r.get('type','')][sid] += 1
for t in ('EyeCatch', 'EyeCatchEnd'):
    c = tc[t]
    sad = sum(abs(vc[0x1AD18][s] - c[s]) for s in gs)
    ex = sum(1 for s in gs if vc[0x1AD18][s] == c[s])
    print('(f) 0x1AD18 vs %-12s sad=%-4d ex=%.4f  Vtot=%d Ttot=%d' % (t, sad, ex/len(gs), sum(vc[0x1AD18][s] for s in gs), sum(c[s] for s in gs)))

# (g) 0x1FAD4 宽松标签众数并列
print('(g) 0x1FAD4 D_all 分布 =', json.load(open('编程组/SOB0解码/_v_naming.json', encoding='utf-8'))['t2']['0x1FAD4']['single_all'])
