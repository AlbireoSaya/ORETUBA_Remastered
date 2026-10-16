# -*- coding: utf-8 -*-
"""LPK 中是否有真 GBK 中文 + CHS 头指针是否指向追加的 CN 池"""
import struct, os, sys, re, collections, json
sys.stdout.reconfigure(encoding='utf-8')
GAME = r'D:\Gal\[Navel]我们没有翅膀'
D = open(os.path.join(GAME, 'SCRIPT.LPK'), 'rb').read()
def rotl(x, n):
    n &= 31; return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
def rotr(x, n):
    n &= 31; return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
NIBF = bytes(((((b ^ 0x50) >> 4) | (((b ^ 0xFD) & 0x0F) << 4)) & 0xFF) for b in range(256))
k1, k0 = 0x9A639DE5, 0xA5B9AC6B
for i, ch in enumerate(b'SCRIPT'):
    k0 ^= b'SCRIPT'[5 - i]; k1 ^= ch; k0 = rotr(k0, 7); k1 = rotl(k1, 7)
raw = struct.unpack_from('<I', D, 4)[0] ^ k1
idxlen = raw & 0xFFFFFF
enc = bytearray(D[8:8 + idxlen]); d = 0x31746285
for i in range(len(enc) // 4):
    d = rotl(d, 4); struct.pack_into('<I', enc, i * 4, struct.unpack_from('<I', enc, i * 4)[0] ^ k1); k1 = rotr(k1, d & 31)
idx = bytes(enc); off = 5 + idx[4] + 1
ltlen = struct.unpack_from('<I', idx, off)[0]; off += 4
lt = idx[off:off + ltlen]; ed_off = off + ltlen
ents = []
def walk(o, nm):
    n = lt[o]; o += 1
    for _ in range(n):
        ch = lt[o]; nxt = struct.unpack_from('<H', lt, o + 1)[0]; o += 3
        if ch: walk(o + nxt, nm + bytes([ch]))
        else: ents.append((nm.decode(), nxt))
walk(0, b'')
def at(num):
    o = ed_off + num * 13
    return struct.unpack_from('<I', idx, o + 1)[0], struct.unpack_from('<I', idx, o + 5)[0], struct.unpack_from('<I', idx, o + 9)[0]
def lzss(src, unc):
    win = bytearray(0x1000); cur = 0xfee; pos = 0; out = bytearray()
    while pos < len(src):
        ctrl = src[pos]; pos += 1
        for bit in range(8):
            if pos >= len(src): break
            if ctrl & (1 << bit):
                b = src[pos]; pos += 1; out.append(b); win[cur] = b; cur = (cur + 1) & 0xFFF
            else:
                b0, b1 = src[pos], src[pos + 1]; pos += 2
                o = b0 | ((b1 & 0xF0) << 4); l = (b1 & 0x0F) + 3
                for i in range(l):
                    b = win[(o + i) & 0xFFF]; out.append(b); win[cur] = b; cur = (cur + 1) & 0xFFF
            if unc and len(out) >= unc: break
        if unc and len(out) >= unc: break
    return bytes(out)
def cont(data):
    b = bytearray(data.translate(NIBF)); L = min(len(b) // 4, 64); k = k0; dd = 0x31746285
    for i in range(L):
        dd = rotr(dd, 4)
        struct.pack_into('<I', b, i * 4, struct.unpack_from('<I', b, i * 4)[0] ^ k); k = rotl(k, dd & 0xFF)
    return bytes(b)
PLAIN = {}
for n, num in ents:
    fo, cl, ul = at(num); blob = D[fo:fo + cl]
    PLAIN[n] = cont(lzss(blob, ul)) if ul else cont(blob)
CHS = os.path.join(GAME, 'SCRIPT_CHS')
cl = {n.lower(): n for n in os.listdir(CHS)}
def C(n): return open(os.path.join(CHS, cl[n.lower()]), 'rb').read()

HW = re.compile('[\uff61-\uff9f]')
HIRA = re.compile('[\u3041-\u309f]')
KATA = re.compile('[\u30a1-\u30fa]')
RUN = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\xfc])+')
def classify(b):
    try: j = b.decode('cp932')
    except Exception: j = b.decode('cp932', 'replace')
    if HIRA.search(j) or KATA.search(j): return 'JP-kana'
    # GBK 中文经 cp932 解读会出现大量半角片假名
    if len(HW.findall(j)) >= max(2, len(b) // 6): return 'CN-gbk'
    return 'KANJI-only'

print('=== Q1 附加：SCRIPT.LPK 全条目非 ASCII 段语言分类（独立判据）===')
c1 = collections.Counter()
for n in PLAIN:
    for m in RUN.finditer(PLAIN[n]):
        b = m.group(0)
        if len(b) < 6: continue
        c1[classify(b)] += 1
print('  ', dict(c1))
zh = [(n, PLAIN[n][m.start():m.end()].decode('gbk', 'replace')[:40])
      for n in PLAIN for m in RUN.finditer(PLAIN[n])
      if len(m.group(0)) >= 6 and classify(m.group(0)) == 'CN-gbk']
print('  被判为 GBK 中文的段数 =', len(zh), ' 例:', zh[:5])

print('\n=== 同一判据用于 SCRIPT_CHS（对照）===')
c2 = collections.Counter()
for n in sorted(PLAIN):
    if n.lower() not in cl: continue
    for m in RUN.finditer(C(n)):
        b = m.group(0)
        if len(b) < 6: continue
        c2[classify(b)] += 1
print('  ', dict(c2))

print('\n=== Q2 判定：CHS 头部指针是否指向「追加 CN 池」 ===')
for name in ('s01_01a.sob', 's00_00.sob'):
    L, c = PLAIN[name], C(name)
    tsz = struct.unpack_from('<I', L, 4)[0]
    tsz2 = struct.unpack_from('<I', c, 4)[0]
    tend = tsz + 8
    lo_end = tend + 8
    print('--- %s: table_size LPK=%d CHS=%d  table_end=%d  header_end=%d  文件 %d->%d' % (name, tsz, tsz2, tend, lo_end, len(L), len(c)))
    # 解析 LPK 与 CHS 的 maps（全部组）
    def maps(f, end):
        p = 8; out = []
        while p < end:
            wp = struct.unpack_from('<I', f, p)[0]; p += 4
            mm = {}
            for _ in range(wp):
                k, v = struct.unpack_from('<II', f, p); p += 8
                mm[k] = v
            out.append(mm)
        return out
    ma, mb = maps(L, tend), maps(c, tend)
    print('    map 组数 LPK=%d CHS=%d' % (len(ma), len(mb)))
    for gi in range(min(len(ma), len(mb))):
        ka, kb = set(ma[gi]), set(mb[gi])
        ch = [k for k in ka & kb if ma[gi][k] != mb[gi][k]]
        print('     组%d: 键数 %d/%d 共有键 %d，值改变 %d' % (gi, len(ka), len(kb), len(ka & kb), len(ch)))
        if gi == 4 and ch:
            for k in ch[:4]:
                va, vb = ma[gi][k], mb[gi][k]
                print('        addr=%08X  LPK_ptr=%d(0x%X) -> CHS_ptr=%d(0x%X)  Δ=%+d' % (k, va, va, vb, vb, vb - va))
                ta = lo_end + va
                tb = lo_end + vb
                print('           LPK 指向处: %s' % L[max(0, ta - 4):ta + 40])
                print('           CHS 指向处: %s' % c[max(0, tb - 4):tb + 40])
    # 追加区起点
    print('   LPK 长度 %d；CHS 中 >=LPK长度 的 GBK 串数(粗略) = %d' % (len(L), len(re.findall(rb'[\xa1-\xfe]{4,}', c[len(L):]))))
