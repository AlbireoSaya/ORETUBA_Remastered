# -*- coding: utf-8 -*-
"""独立 LPK1 解析器（reviewer 自写，不复用被审工具的任何函数）。"""
import struct, os, sys, hashlib, json, collections, re

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT = r'D:\Gal\[Navel]我们没有翅膀\SCRIPT.LPK'
D = open(SCRIPT, 'rb').read()

print('文件大小 =', len(D))
print('魔数 =', D[:4])
print('mtime =', os.path.getmtime(SCRIPT))
print('md5 =', hashlib.md5(D).hexdigest())

def rotl(x, n):
    n &= 31
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def rotr(x, n):
    n &= 31
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF

# ---- key 派生（只用文件名 SCRIPT）----
BASE = os.path.splitext(os.path.basename(SCRIPT))[0].upper()
kb = BASE.encode('ascii')
k1 = 0x9A639DE5
k0 = 0xA5B9AC6B
for i in range(len(kb)):
    k0 ^= kb[len(kb) - 1 - i]
    k1 ^= kb[i]
    k0 = rotr(k0, 7)
    k1 = rotl(k1, 7)
print('BASENAME=%r key1=0x%08X key0=0x%08X' % (BASE, k1, k0))

raw = struct.unpack_from('<I', D, 4)[0]
irl = raw ^ k1
flags = (irl >> 24) & 0xFF
idxlen = irl & 0xFFFFFF
print('raw_len_word=0x%08X -> irl=0x%08X flags=0x%02X idxlen_raw=%d' % (raw, irl, flags, idxlen))
fb0 = flags & 1
if fb0:
    idxlen = (idxlen << 11) - 8
print('flags bits: b0=%d b1=%d b2(entry_crypt)=%d b3(rec13)=%d b4(whole)=%d' %
      ((flags >> 0) & 1, (flags >> 1) & 1, (flags >> 2) & 1, (flags >> 3) & 1, (flags >> 4) & 1))
print('idx_len =', idxlen, ' data_start =', 8 + idxlen, ' 尾部剩余 =', len(D) - (8 + idxlen))

# ---- 索引解密（独立实现）----
enc = bytearray(D[8:8 + idxlen])
d = 0x31746285
kk = k1
for i in range(len(enc) // 4):
    d = rotl(d, 4)
    sh = d & 31
    v = struct.unpack_from('<I', enc, i * 4)[0]
    v ^= kk
    struct.pack_into('<I', enc, i * 4, v)
    kk = rotr(kk, sh)
idx = bytes(enc)

cnt = struct.unpack_from('<I', idx, 0)[0]
off = 4
plen = idx[off]; off += 1
plain = idx[off:off + plen]; off += plen
mode = idx[off]; off += 1
ltlen = struct.unpack_from('<I', idx, off)[0]; off += 4
lt = idx[off:off + ltlen]
ed_off = off + ltlen
print('count=%d plen=%d mode=%d ltlen=%d ed_off=%d' % (cnt, plen, mode, ltlen, ed_off))
print('plain(索引模式串) =', plain)
rec = 13 if (flags >> 3) & 1 else 9
print('rec_size =', rec, ' 记录表占 =', cnt * rec, ' 索引结束 =', ed_off + cnt * rec, ' idx_len =', idxlen)

# ---- trie 解析 ----
ents = []
def walk(o, name):
    n = lt[o]; o += 1
    for _ in range(n):
        ch = lt[o]
        if mode:
            nxt = struct.unpack_from('<I', lt, o + 1)[0]; o += 5
        else:
            nxt = struct.unpack_from('<H', lt, o + 1)[0]; o += 3
        if ch != 0:
            walk(o + nxt, name + bytes([ch]))
        else:
            ents.append((name.decode('ascii', 'replace'), nxt))
walk(0, b'')
print('解析出条目数 =', len(ents))

def entry_at(num):
    o = ed_off + num * rec
    isc = idx[o]
    fo = struct.unpack_from('<I', idx, o + 1)[0]
    cl = struct.unpack_from('<I', idx, o + 5)[0]
    ul = struct.unpack_from('<I', idx, o + 9)[0] if rec == 13 else 0
    if fb0:
        fo <<= 11
    return o, isc, fo, cl, ul

# ---- LZSS（独立实现，按 skill 描述）----
def lzss_decomp(src, unc_len):
    win = bytearray(0x1000)
    cur = 0xfee
    pos = 0
    out = bytearray()
    while pos < len(src) and (len(out) < unc_len or unc_len == 0):
        ctrl = src[pos]; pos += 1
        for bit in range(8):
            if pos >= len(src):
                break
            if ctrl & (1 << bit):
                b = src[pos]; pos += 1
                out.append(b); win[cur] = b; cur = (cur + 1) & 0xFFF
            else:
                b0 = src[pos]; b1 = src[pos + 1]; pos += 2
                o = b0 | ((b1 & 0xF0) << 4)
                l = (b1 & 0x0F) + 3
                for i in range(l):
                    b = win[(o + i) & 0xFFF]
                    out.append(b); win[cur] = b; cur = (cur + 1) & 0xFFF
            if unc_len and len(out) >= unc_len:
                break
    return bytes(out)

def nib(b):
    return (((b ^ 0x50) >> 4) | (((b ^ 0xFD) & 0x0F) << 4)) & 0xFF
NIBF = bytes(nib(v) for v in range(256))

def cont_dec(data, key):
    b = bytearray(data.translate(NIBF))
    L = min(len(b) // 4, 64)
    k = key; d = 0x31746285
    for i in range(L):
        d = rotr(d, 4)
        v = struct.unpack_from('<I', b, i * 4)[0] ^ k
        struct.pack_into('<I', b, i * 4, v)
        k = rotl(k, d & 0xFF)
    return bytes(b)

def read_entry(name):
    for n, num in ents:
        if n == name:
            o, isc, fo, cl, ul = entry_at(num)
            blob = D[fo:fo + cl]
            mid = lzss_decomp(blob, ul) if ul else blob
            p = cont_dec(mid, k0) if (flags >> 2) & 1 else mid
            return dict(name=n, num=num, isc=isc, fo=fo, cl=cl, ul=ul, plain=p)
    raise KeyError(name)

print('\n--- 条目扩展名分布 ---')
ext = collections.Counter(os.path.splitext(n)[1].lower() for n, _ in ents)
print(dict(ext))

# 记录表自洽性检查
print('\n--- 记录表自洽性 ---')
bad = []
rng = []
for n, num in ents:
    o, isc, fo, cl, ul = entry_at(num)
    if fo < 8 + idxlen or fo + cl > len(D):
        bad.append((n, fo, cl))
    rng.append((fo, fo + cl, n))
rng.sort()
ov = [1 for i in range(1, len(rng)) if rng[i][0] < rng[i - 1][1]]
print('越界记录数 =', len(bad), ' 重叠区间数 =', len(ov))
print('数据区首条 @%d = data_start? %s' % (rng[0][0], rng[0][0] == 8 + idxlen))
print('数据区末条结束 = %d 文件大小 = %d  差 = %d' % (rng[-1][1], len(D), len(D) - rng[-1][1]))
# 是否有未被任何条目覆盖的间隙
gaps = []
prev = 8 + idxlen
for a, b, n in rng:
    if a > prev:
        gaps.append((prev, a - prev))
    prev = max(prev, b)
if prev < len(D):
    gaps.append((prev, len(D) - prev))
print('数据区间隙(未被条目覆盖的字节) = %d 处，合计 %d 字节' % (len(gaps), sum(g[1] for g in gaps)))
if gaps:
    print('  前若干间隙:', gaps[:12])

# 按 num 排序的记录偏移是否单调
mons = all(entry_at(ents[i][1])[2] <= entry_at(ents[i + 1][1])[2] for i in range(len(ents) - 1))
print('num 递增 ↔ file_offset 递增:', mons)

json.dump([dict(name=n, num=u) for n, u in ents],
          open(r'E:\ZCode Workspace\Galgame\临时\独立的_ents.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('条目清单已存 临时\\独立的_ents.json')
