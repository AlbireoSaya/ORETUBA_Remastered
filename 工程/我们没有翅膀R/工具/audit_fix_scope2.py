# -*- coding: utf-8 -*-
r"""修复前审计·第二批（ISSUE-20260915-06）：只读。
先把 446 条目落盘缓存（临时\_audit_cache），随后做细粒度分析：
  1) NUL 丢失记录中「未分类」的 6 条是谁
  2) 越读=0 的样本（下一字节即 0x00）与 越读=3 的样本对照
  3) 'ＬＲ２００１' 名字记录现状（用户截图里显示 2 个方块）
  4) 「原版 NUL 结尾声明串」中，现行**完全未改动**且非 ASCII 的记录（潜在原始 SJIS 残留）
  5) 39 条不可编码译文：原文字节 / 现行字节 / 是否被写过
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
CACHE = os.path.join(WS, '临时', '_audit_cache')

for tag, path in (('orig', ORIG), ('cur', CUR)):
    d = os.path.join(CACHE, tag)
    os.makedirs(d, exist_ok=True)
    lp = LP.load(path)
    miss = [n for n, num in lp['ents'] if not os.path.exists(os.path.join(d, n))]
    print('缓存 %s：%d 条待导出' % (tag, len(miss)))
    for n in miss:
        open(os.path.join(d, n), 'wb').write(LP.read_entry(lp, n)['plain'])
print('缓存完成')


def O(n):
    return open(os.path.join(CACHE, 'orig', n), 'rb').read()


def C(n):
    return open(os.path.join(CACHE, 'cur', n), 'rb').read()


rec = json.load(open(os.path.join(Y, '重编码映射.json'), encoding='utf-8'))
new = json.load(open(os.path.join(Y, '新增译文映射.json'), encoding='utf-8'))
mig = json.load(open(os.path.join(Y, 'R版迁移映射.json'), encoding='utf-8'))
namecn = set((r['file'], int(r['offset'])) for r in rec if r.get('src') == 'name-cn')
allrec = set((r['file'], int(r['offset'])) for r in rec)
S1 = set((r['file'], int(r['offset'])) for r in (mig + new))


def decls(buf):
    """产出 (rec_start, boff, L)"""
    out = []
    for m in re.finditer(rb'\x01\x01', buf):
        i = m.start()
        if i + 4 > len(buf):
            continue
        L = buf[i + 2] | (buf[i + 3] << 8)
        if not (3 <= L <= 400):
            continue
        boff = i + 4
        if boff + L > len(buf):
            continue
        out.append((i, boff, L))
    return out


# ---------- 1) 未分类的 6 条 ----------
print('\n---- 1) NUL 丢失但不在 name-cn / 不在任何 rec 的 6 条 ----')
cnt = 0
for n, num in LP.load(ORIG)['ents']:
    a, b = O(n), C(n)
    for i, boff, L in decls(a):
        if a[boff + L - 1] != 0:
            continue
        if b[boff + L - 1] == 0:
            continue
        if (n, boff) in allrec:
            continue
        cnt += 1
        print('   %-14s rec@%-6d boff=%d L=%d' % (n, i, boff, L))
        print('      orig:', a[max(0, i - 8):boff + L + 16].hex())
        print('      cur :', b[max(0, i - 8):boff + L + 16].hex())
print('   合计 %d 条' % cnt)

# ---------- 2/3) 样本 ----------
print('\n---- 2) 越读模式抽样（各 6 条）----')
s0, s3 = [], []
for n, num in LP.load(ORIG)['ents']:
    a, b = O(n), C(n)
    for i, boff, L in decls(a):
        if a[boff + L - 1] != 0 or b[boff + L - 1] == 0 or (n, boff) not in namecn:
            continue
        k = boff + L
        while k < len(b) and b[k] != 0:
            k += 1
        over = k - (boff + L)
        s = (n, i, L, bytes(a[boff:boff + L]), bytes(b[boff:boff + L]), bytes(b[boff + L:k + 4]))
        (s0 if over == 0 else s3).append((over, s))
print('   越读=0 样本:')
for over, (n, i, L, ab, bb, ob) in s0[:6]:
    print('      %-14s @%-6d L=%-3d 原:%-20s 现:%-20s 后续:%s' % (n, i, L, ab.hex(), bb.hex(), ob.hex()))
print('   越读>0 样本:')
for over, (n, i, L, ab, bb, ob) in s3[:6]:
    print('      %-14s @%-6d L=%-3d 原:%-20s 现:%-20s 后续:%s (越读 %d)' % (n, i, L, ab.hex(), bb.hex(), ob.hex(), over))

print('\n---- 3) ＬＲ２００１ 名字记录 ----')
hit = 0
for n, num in LP.load(ORIG)['ents']:
    a, b = O(n), C(n)
    for i, boff, L in decls(a):
        if a[boff + L - 1] != 0:
            continue
        try:
            s = a[boff:boff + L - 1].decode('cp932')
        except Exception:
            continue
        if s != 'ＬＲ２００１':
            continue
        hit += 1
        if hit <= 4:
            k = boff + L
            while k < len(b) and b[k] != 0:
                k += 1
            print('   %-14s @%-6d L=%-3d 原:%-38s 现:%-38s 后续:%s (越读 %d)'
                  % (n, i, L, a[boff:boff + L].hex(), b[boff:boff + L].hex(), b[boff + L:k + 1].hex(), k - (boff + L)))
print('   合计 %d 条' % hit)

# ---------- 4) 未改动的非 ASCII 声明串 ----------
print('\n---- 4) 原版 NUL 结尾、现行逐字节未改动、含非 ASCII 的声明串 ----')
unt = collections.Counter()
samples = []
for n, num in LP.load(ORIG)['ents']:
    a, b = O(n), C(n)
    for i, boff, L in decls(a):
        if a[boff + L - 1] != 0:
            continue
        if a[boff:boff + L] != b[boff:boff + L]:
            continue
        body = a[boff:boff + L - 1]
        if all(0x20 <= x < 0x7F for x in body):
            continue
        unt[n] += 1
        if len(samples) < 8:
            samples.append((n, i, L, body.hex()))
print('   合计 %d 条，按文件:' % sum(unt.values()))
for f, v in unt.most_common(15):
    print('      %-16s %d' % (f, v))
for n, i, L, h in samples:
    print('      %-16s @%-6d L=%-3d %s' % (n, i, L, h))

# ---------- 5) 39 条不可编码：原文/现行 ----------
print('\n---- 5) GBK 不可编码的 39 条：原文 vs 现行 ----')
bad = []
for r in mig + new:
    t = r.get('cn') or r.get('text') or ''
    if not t:
        continue
    try:
        t.encode('gbk')
    except UnicodeEncodeError:
        bad.append((r.get('file'), int(r.get('offset', -1)), int(r.get('len', -1)), t))
byname = collections.defaultdict(list)
for f, o, l, t in bad:
    byname[f].append((o, l, t))
for f in sorted(byname):
    a, b = O(f), C(f)
    for o, l, t in byname[f]:
        same = a[o:o + l] == b[o:o + l]
        try:
            jp = a[o:o + l].decode('cp932')
        except Exception:
            jp = '<cp932失败>'
        print('   %-14s @%-6d len=%-4d 未被写入=%s' % (f, o, l, same))
        print('      原(JP): %r' % jp)
        print('      现(GBK): %r' % b[o:o + l].decode('gbk', errors='replace'))
        print('      待写(CN): %r' % t)
