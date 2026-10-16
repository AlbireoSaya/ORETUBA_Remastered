# -*- coding: utf-8 -*-
r"""修复前审计（ISSUE-20260915-06）：只读。

1) 映射覆盖率（台词槽 vs 迁移/新译/重编码映射）
2) GBK 不可编码译文清单（bug B 根因）
3) 声明串 NUL 审计（bug A 根因）：原版以 0x00 结尾、现行末字节非 0 的记录
"""
import os, sys, json, collections, re

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
ORIG = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
CUR = os.path.join(WS, '_game_ascii', 'ORETSUBA_R', 'SCRIPT.LPK')

slots = json.load(open(os.path.join(Y, 'R版台词.json'), encoding='utf-8'))
rec = json.load(open(os.path.join(Y, '重编码映射.json'), encoding='utf-8'))
new = json.load(open(os.path.join(Y, '新增译文映射.json'), encoding='utf-8'))
mig = json.load(open(os.path.join(Y, 'R版迁移映射.json'), encoding='utf-8'))


def key(r):
    o = r.get('offset')
    if o is None:
        return None
    return (r.get('file'), int(o))


S1 = set(k for k in (key(r) for r in (mig + new)) if k)
S2 = set(k for k in (key(r) for r in rec) if k)
KS = set(k for k in (key(r) for r in slots) if k)
print('slots(有offset)=%d  S1(mig+new)=%d  S2(rec)=%d  overlap=%d'
      % (len(KS), len(S1), len(S2), len(S1 & S2)))
un = [r for r in slots if key(r) and key(r) not in (S1 | S2)]
print('未被任何映射覆盖的槽: %d' % len(un))
print('   按前缀:', dict(collections.Counter((r.get('file') or '?')[:5] for r in un)))
print('   按 kind:', dict(collections.Counter(r.get('kind') for r in un)))

print('\nrec 行 src 分布:', dict(collections.Counter(r.get('src', '?') for r in rec)))

bad = []
for r in mig + new:
    t = r.get('cn') or r.get('text') or ''
    if not t:
        continue
    try:
        t.encode('gbk')
    except UnicodeEncodeError as e:
        bad.append((r.get('file'), int(r.get('offset', -1)), int(r.get('len', -1)), t))
print('\nGBK 不可编码译文: %d 条' % len(bad))
cc = collections.Counter()
for f, o, l, t in bad:
    for ch in t:
        try:
            ch.encode('gbk')
        except UnicodeEncodeError:
            cc[ch] += 1
    print('   %-14s @%-6d len=%-4d %r' % (f, o, l, t))
print('   罪魁字符:', dict(cc))

# ---------- 3) 声明串 NUL 审计 ----------
lo = LP.load(ORIG)
lc = LP.load(CUR)
namecn = set((r['file'], int(r['offset'])) for r in rec if r.get('src') == 'name-cn')
labelcn = set((r['file'], int(r['offset'])) for r in rec if r.get('src') == 'label-cn')
u16name = set((r['file'], int(r['offset'])) for r in rec if r.get('src') == 'sjis->gbk(u16name)')

tot = lost = 0
byclass = collections.Counter()
lastvals = collections.Counter()
overread = collections.Counter()
samples = []
for n, num in lo['ents']:
    a = LP.read_entry(lo, n)['plain']
    b = LP.read_entry(lc, n)['plain']
    if len(a) != len(b):
        print('!! 长度不一致', n, len(a), len(b))
    for m in re.finditer(rb'\x01\x01', a):
        i = m.start()
        if i + 4 > len(a):
            continue
        L = a[i + 2] | (a[i + 3] << 8)
        if not (3 <= L <= 400):
            continue
        boff = i + 4
        if boff + L > len(a):
            continue
        if a[boff + L - 1] != 0x00:      # 只审计「原本以 NUL 结尾」的记录
            continue
        tot += 1
        if boff + L > len(b):
            continue
        if b[boff + L - 1] != 0x00:
            lost += 1
            lastvals[b[boff + L - 1]] += 1
            if (n, boff) in namecn:
                byclass['name-cn'] += 1
            elif (n, boff) in labelcn:
                byclass['label-cn'] += 1
            elif (n, boff) in u16name:
                byclass['u16name-recode'] += 1
            elif (n, boff) in S2:
                byclass['rec-other'] += 1
            elif (n, boff) in S1:
                byclass['mig/new(译文)'] += 1
            else:
                byclass['未覆盖'] += 1
            # 越读长度：从记录末尾读到下一个 0x00 为止
            k = boff + L
            while k < len(b) and b[k] != 0x00:
                k += 1
            overread[k - (boff + L)] += 1
            if len(samples) < 12:
                samples.append((n, i, L, bytes(a[boff:boff + L]), bytes(b[boff:boff + L]), bytes(b[boff + L:k + 1])))

print('\nNUL 结尾声明串(原版): %d；现行末字节非 0: %d' % (tot, lost))
print('   按类别:', dict(byclass))
print('   现行末字节值:', {'0x%02x' % k: v for k, v in lastvals.items()})
print('   越读字节数分布:', dict(overread))
for n, i, L, ab, bb, ob in samples:
    print('   %-14s @%-6d L=%-3d 原:%-24s 现:%-24s 后续(至NUL):%s'
          % (n, i, L, ab.hex(), bb.hex(), ob.hex()))
