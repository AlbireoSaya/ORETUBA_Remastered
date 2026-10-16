# -*- coding: utf-8 -*-
r"""修复前审计·第三批（ISSUE-20260915-06）：只读，走缓存。
 1) 未改动的非 ASCII 声明串全部列出（SJIS 解码 + 归属检查）
 2) 台词跨度：现行 == 原版 且非 ASCII 的全部列出（乱码跨度）
 3) ＬＲ２００１ 记录所在文件
"""
import os, sys, json, re, collections

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
CACHE = os.path.join(WS, '临时', '_audit_cache')


def O(n):
    return open(os.path.join(CACHE, 'orig', n), 'rb').read()


def C(n):
    return open(os.path.join(CACHE, 'cur', n), 'rb').read()


rec = json.load(open(os.path.join(Y, '重编码映射.json'), encoding='utf-8'))
new = json.load(open(os.path.join(Y, '新增译文映射.json'), encoding='utf-8'))
mig = json.load(open(os.path.join(Y, 'R版迁移映射.json'), encoding='utf-8'))
slash = json.load(open(os.path.join(Y, 'R版台词.json'), encoding='utf-8'))
allrec = set((r['file'], int(r['offset'])) for r in rec if r.get('offset') is not None)
S1 = set((r['file'], int(r['offset'])) for r in (mig + new) if r.get('offset') is not None)
recfile = collections.defaultdict(set)
for r in rec:
    if r.get('offset') is not None:
        recfile[r['file']].add(int(r['offset']))

print('---- 1) 未改动的非 ASCII 声明串（L<=64 的真实记录）----')
cnt = 0
for fn in sorted(os.listdir(os.path.join(CACHE, 'orig'))):
    if not (fn.endswith('.tob') or fn.endswith('.sob')):
        continue
    a, b = O(fn), C(fn)
    for m in re.finditer(rb'\x01\x01', a):
        i = m.start()
        if i + 4 > len(a):
            continue
        L = a[i + 2] | (a[i + 3] << 8)
        if not (3 <= L <= 64):
            continue
        boff = i + 4
        if boff + L > len(a) or a[boff + L - 1] != 0x00:
            continue
        if a[boff:boff + L] != b[boff:boff + L]:
            continue
        body = a[boff:boff + L - 1]
        if all(0x20 <= x < 0x7F for x in body):
            continue
        cnt += 1
        try:
            s = body.decode('cp932')
        except Exception:
            s = '<cp932失败>'
        print('   %-14s @%-6d L=%-3d %r   in_rec=%s in_S1=%s'
              % (fn, boff, L, s, (fn, boff) in allrec, (fn, boff) in S1))
print('   合计 %d 条' % cnt)

print('\n---- 2) 台词跨度：现行 == 原版 且非 ASCII ----')
cnt = 0
byf = collections.Counter()
for r in slash:
    o = r.get('offset')
    if o is None:
        continue
    fn = r['file']
    try:
        a = O(fn)
        b = C(fn)
    except FileNotFoundError:
        continue
    off = int(o)
    ln = int(r.get('len') or 0)
    if ln <= 0 or off + ln > len(a):
        continue
    if a[off:off + ln] != b[off:off + ln]:
        continue
    if all(0x20 <= x < 0x7F for x in a[off:off + ln]):
        continue
    cnt += 1
    byf[fn] += 1
    if cnt <= 45:
        try:
            jp = a[off:off + ln].decode('cp932')
        except Exception:
            jp = '<cp932失败>'
        print('   %-14s @%-6d len=%-4d %r' % (fn, off, ln, jp[:60]))
print('   合计 %d 条；按文件:' % cnt)
for f, v in byf.most_common(30):
    print('      %-16s %d' % (f, v))

print('\n---- 3) ＬＲ２００１ 所在文件 ----')
f_cnt = collections.Counter()
for fn in sorted(os.listdir(os.path.join(CACHE, 'orig'))):
    a = O(fn)
    for m in re.finditer(rb'\x01\x01', a):
        i = m.start()
        if i + 4 > len(a):
            continue
        L = a[i + 2] | (a[i + 3] << 8)
        if not (3 <= L <= 64):
            continue
        boff = i + 4
        if boff + L > len(a) or a[boff + L - 1] != 0x00:
            continue
        try:
            if a[boff:boff + L - 1].decode('cp932') == 'ＬＲ２００１':
                f_cnt[fn] += 1
        except Exception:
            pass
print('  ', dict(f_cnt))
