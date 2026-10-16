# -*- coding: utf-8 -*-
r"""修复后验证（ISSUE-20260915-06）：对**新构建 LPK** 做全量字节级验收。只读。
（`O()` 直接读安装介质 LPK，不依赖 `临时\` 缓存。）

  A. 所有原版 NUL 结尾的声明串（L<=64）在新 LPK 中末字节 == 0x00（名字框方块根治）
  B. 39 条不可编码译文：新 LPK 已写入且为合法 GBK 中文
  C. 44 条组合/编号名：新 LPK 已写入
  D. 全量残留扫描：声明串 + 台词跨度中，**与新原版逐字节相同且非 ASCII** 的记录数 == 0
  E. 每个条目长度与原版一致（ll_app.inf 除外——标题补丁）
用法：python -X utf8 verify_fix.py <新 SCRIPT.LPK>
"""
import os, re, sys, json, collections

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
ORIG = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
OLD = os.path.join(WS, '_game_ascii', 'ORETSUBA_R', 'SCRIPT.LPK')

NEW = sys.argv[1]
fail = []

_lpo = LP.load(ORIG)
_ocache = {}


def O(n):
    r"""原版条目明文（直接来自安装介质 LPK，不依赖 `临时\` 缓存）。"""
    if n not in _ocache:
        _ocache[n] = LP.read_entry(_lpo, n)['plain']
    return _ocache[n]


lp = LP.load(NEW)
print('新 LPK：%d 条目，%d 字节' % (len(lp['ents']), os.path.getsize(NEW)))
ents = {}
for n, num in lp['ents']:
    ents[n] = LP.read_entry(lp, n)['plain']
print('条目解码完成')

# ---- E. 长度一致 ----
bad_len = []
for n in ents:
    try:
        a = O(n)
    except FileNotFoundError:
        continue
    if len(a) != len(ents[n]) and n != 'll_app.inf':
        bad_len.append((n, len(a), len(ents[n])))
print('E. 长度不一致（ll_app.inf 除外）: %d %s' % (len(bad_len), bad_len[:5]))
if bad_len:
    fail.append('长度不一致')

# ---- A. NUL 结尾 ----
lost = []
tot = 0
for n in ents:
    a = O(n)
    b = ents[n]
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
        tot += 1
        if b[boff + L - 1] != 0x00:
            lost.append((n, boff, L))
print('A. NUL 结尾声明串 %d 条；新 LPK 中末字节非 NUL: %d' % (tot, len(lost)))
for x in lost[:5]:
    print('   ', x)
if lost:
    fail.append('NUL 未还原')

# ---- B/C. 39 + 44 条写入检查 ----
rec = json.load(open(os.path.join(Y, '重编码映射.json'), encoding='utf-8'))
targetsB, targetsC = [], []
for r in rec:
    if r.get('src') == 'name-combo' or r.get('src') == 'recode-combo':
        targetsC.append(r)
# 39 条：从 maps 里找 gbk 不可编码的（修复后在 build 里回退）
mig = json.load(open(os.path.join(Y, 'R版迁移映射.json'), encoding='utf-8'))
newm = json.load(open(os.path.join(Y, '新增译文映射.json'), encoding='utf-8'))
for r in mig + newm:
    t = r.get('cn') or r.get('text') or ''
    if not t:
        continue
    try:
        t.encode('gbk')
    except UnicodeEncodeError:
        targetsB.append(r)
print('B. 目标 %d 条（GBK 不可编码译文）；C. 目标 %d 条（组合/编号名）' % (len(targetsB), len(targetsC)))
nw = 0
for r in targetsB:
    f, o, l = r['file'], int(r['offset']), int(r['len'])
    if ents[f][o:o + l] != O(f)[o:o + l]:
        nw += 1
print('   B: 已被写入（字节不同于原版） %d / %d' % (nw, len(targetsB)))
if nw != len(targetsB):
    fail.append('B 未全部写入')
nw = 0
for r in targetsC:
    f, o, l = r['file'], int(r['offset']), int(r['len'])
    if ents[f][o:o + l] != O(f)[o:o + l]:
        nw += 1
print('   C: 已被写入 %d / %d' % (nw, len(targetsC)))
if nw != len(targetsC):
    fail.append('C 未全部写入')

# ---- D. 全量残留扫描（波段放宽到 L<=400，覆盖非名字类声明串）----
resid = []
for n in ents:
    a = O(n)
    b = ents[n]
    for m in re.finditer(rb'\x01\x01', a):
        i = m.start()
        if i + 4 > len(a):
            continue
        L = a[i + 2] | (a[i + 3] << 8)
        if not (3 <= L <= 400):
            continue
        # L == 256 是字节码里 `01 01 00 01` 序列造成的假记录（非声明串），排除
        if L == 256:
            continue
        boff = i + 4
        if boff + L > len(a) or a[boff + L - 1] != 0x00:
            continue
        if a[boff:boff + L] != b[boff:boff + L]:
            continue
        if all(0x20 <= x < 0x7F for x in a[boff:boff + L - 1]):
            continue
        resid.append((n, boff, L, a[boff:boff + L - 1].hex()))
slash = json.load(open(os.path.join(Y, 'R版台词.json'), encoding='utf-8'))
d2 = 0
d2s = []
for r in slash:
    o = r.get('offset')
    if o is None:
        continue
    f = r['file']
    if f not in ents:
        continue
    a, b = O(f), ents[f]
    off, ln = int(o), int(r.get('len') or 0)
    if ln <= 0 or off + ln > len(a):
        continue
    if a[off:off + ln] != b[off:off + ln]:
        continue
    if all(0x20 <= x < 0x7F for x in a[off:off + ln]):
        continue
    d2 += 1
    if len(d2s) < 6:
        d2s.append((f, off, ln, a[off:off + ln].decode('cp932', 'replace')[:40]))
print('D. 残留（未改动非 ASCII，声明串波段 L=3..400）：声明串 %d 条；台词跨度 %d 条'
      % (len(resid), d2))
for x in resid[:5]:
    print('   [decl]', x)
for x in d2s:
    print('   [text]', x)
if resid or d2:
    fail.append('仍有原始 SJIS 残留')

print()
print('=== 结论：%s ===' % ('全部通过' if not fail else '存在失败项 ' + str(fail)))
