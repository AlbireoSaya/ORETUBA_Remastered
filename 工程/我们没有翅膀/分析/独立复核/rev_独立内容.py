# -*- coding: utf-8 -*-
"""独立复核 C1b/C1c/C1d + C2 的字节布局（reviewer 自写）"""
import struct, os, sys, collections, re, json, hashlib

sys.stdout.reconfigure(encoding='utf-8')
GAME = r'D:\Gal\[Navel]我们没有翅膀'
SCRIPT = os.path.join(GAME, 'SCRIPT.LPK')
CHS = os.path.join(GAME, 'SCRIPT_CHS')
D = open(SCRIPT, 'rb').read()

def rotl(x, n):
    n &= 31
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
def rotr(x, n):
    n &= 31
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def nib(b):
    return (((b ^ 0x50) >> 4) | (((b ^ 0xFD) & 0x0F) << 4)) & 0xFF
NIBF = bytes(nib(v) for v in range(256))

BASE = os.path.splitext(os.path.basename(SCRIPT))[0].upper()
kb = BASE.encode('ascii')
k1, k0 = 0x9A639DE5, 0xA5B9AC6B
for i in range(len(kb)):
    k0 ^= kb[len(kb) - 1 - i]; k1 ^= kb[i]
    k0 = rotr(k0, 7); k1 = rotl(k1, 7)

raw = struct.unpack_from('<I', D, 4)[0] ^ k1
flags = raw >> 24
idxlen = raw & 0xFFFFFF
enc = bytearray(D[8:8 + idxlen]); d = 0x31746285; kk = k1
for i in range(len(enc) // 4):
    d = rotl(d, 4); v = struct.unpack_from('<I', enc, i * 4)[0] ^ kk
    struct.pack_into('<I', enc, i * 4, v); kk = rotr(kk, d & 31)
idx = bytes(enc)
cnt = struct.unpack_from('<I', idx, 0)[0]; off = 5 + idx[4]
mode = idx[off]; off += 1
ltlen = struct.unpack_from('<I', idx, off)[0]; off += 4
lt = idx[off:off + ltlen]; ed_off = off + ltlen; rec = 13
ents = []
def walk(o, nm):
    n = lt[o]; o += 1
    for _ in range(n):
        ch = lt[o]
        nxt = struct.unpack_from('<H', lt, o + 1)[0]; o += 3
        if ch: walk(o + nxt, nm + bytes([ch]))
        else: ents.append((nm.decode(), nxt))
walk(0, b'')

def at(num):
    o = ed_off + num * rec
    return idx[o], struct.unpack_from('<I', idx, o + 1)[0], struct.unpack_from('<I', idx, o + 5)[0], struct.unpack_from('<I', idx, o + 9)[0]
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
def cont(data, key):
    b = bytearray(data.translate(NIBF)); L = min(len(b) // 4, 64)
    k = key; dd = 0x31746285
    for i in range(L):
        dd = rotr(dd, 4)
        struct.pack_into('<I', b, i * 4, struct.unpack_from('<I', b, i * 4)[0] ^ k)
        k = rotl(k, dd & 0xFF)
    return bytes(b)

PLAIN = {}
for n, num in ents:
    isc, fo, cl, ul = at(num)
    blob = D[fo:fo + cl]
    mid = lzss(blob, ul) if ul else blob
    PLAIN[n] = cont(mid, k0) if flags & 4 else mid

# ================= C1b: 剧情脚本计数 =================
STORY = re.compile(r'^s\d\d[a-z]?_\d\d[a-z]?\.sob$', re.I)
story = sorted(n for n in PLAIN if STORY.match(n))
print('=== C1b 剧情脚本 ===')
print('SOB0 条目数 =', sum(1 for p in PLAIN.values() if p[:4] == b'SOB0'))
print('TOB0 条目数 =', sum(1 for p in PLAIN.values() if p[:4] == b'TOB0'))
print('其它魔数条目 =', [(n, PLAIN[n][:4]) for n in PLAIN if PLAIN[n][:4] not in (b'SOB0', b'TOB0')])
print('正则 s\\d\\d[a-z]?_\\d\\d[a-z]?\\.sob 命中 =', len(story))
pref = collections.Counter(n.split('_')[0] for n in story)
print('前缀分布 =', dict(sorted(pref.items())))
named = sorted(n for n in PLAIN if n not in story)
print('非剧情类 .sob (%d) =' % len(named), named)

# ================= C1c: 日文连贯性 =================
HIRA = re.compile('[\u3041-\u309f]')
KATA = re.compile('[\u30a1-\u30fa]')
print('\n=== C1c 日文证据 ===')
t = PLAIN['s01_01a.sob'].decode('cp932', 'replace')
key = 'あともう少しだけ、僕の空っぽな物語は続くんだ。'
print('s01_01a.sob 含目标句:', key in t)
i = t.find(key)
print('上下文:', repr(t[max(0, i - 60):i + len(key) + 20]))
tot_hira = sum(len(HIRA.findall(PLAIN[n].decode('cp932', 'replace'))) for n in PLAIN)
print('全 418 条目按 cp932 解的平假名总数 =', tot_hira)

# ================= C1d: 规模统计 =================
print('\n=== C1d 规模统计 ===')
sob = [n for n in PLAIN if n.endswith('.sob')]
tot = sum(len(PLAIN[n]) for n in sob)
nonascii = sum(1 for n in sob for b in PLAIN[n] if b >= 0x80)
print('.sob 条数 =', len(sob), ' 解压后明文合计 =', tot)
print('其中 >=0x80 字节数 =', nonascii)
amp = sum(PLAIN[n].count(b'$&') for n in sob)
print("$& 出现次数 =", amp)
tot_all = sum(len(v) for v in PLAIN.values())
print('全部条目明文合计 =', tot_all)

# ================= C2: 外挂 SCRIPT_CHS 比对 =================
print('\n=== C2 外挂比对 ===')
RUN = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\xfc])+')
chs_names = os.listdir(CHS)
chs_low = {n.lower(): n for n in chs_names}
miss = [n for n in PLAIN if n.lower() not in chs_low]
print('LPK 条目数 =', len(PLAIN), ' SCRIPT_CHS 文件数 =', len(chs_names))
print('未覆盖 (%d) = %s' % (len(miss), sorted(miss)))
extra = [n for n in chs_names if n.lower() not in {k.lower() for k in PLAIN}]
print('CHS 中 LPK 没有的文件 =', extra)

# 抽样逐条验证「JP 非 ASCII 段 100% 原样存在」
def runs(b, minlen=8):
    return [m.group(0) for m in RUN.finditer(b) if len(m.group(0)) >= minlen]
samples = ['s01_01a.sob', 's00_00.sob', 's01_02a.sob', 'gameinit.sob', 's02_14e.sob', 's03_10a.sob', 's03c_04b.sob', 's04_05e.sob']
print('%-18s %8s %8s %6s %6s %s' % ('file', 'LPKsize', 'CHSsize', 'runs', 'hit', 'rate'))
for s in samples:
    if s not in PLAIN or s.lower() not in chs_low: continue
    L = PLAIN[s]; C = open(os.path.join(CHS, chs_low[s.lower()]), 'rb').read()
    R = runs(L)
    hit = sum(1 for r in R if r in C)
    print('%-18s %8d %8d %6d %6d %s' % (s, len(L), len(C), len(R), hit, '100%' if hit == len(R) else '%.1f%%' % (100.0 * hit / max(1, len(R)))))

# 全量统计（所有共同文件）
tot_r = tot_h = 0
bad = []
for n, L in PLAIN.items():
    if n.lower() not in chs_low: continue
    C = open(os.path.join(CHS, chs_low[n.lower()]), 'rb').read()
    R = runs(L); tot_r += len(R)
    h = sum(1 for r in R if r in C); tot_h += h
    if h != len(R): bad.append((n, len(R), h))
print('全量（%d 共同文件）：JP 段 %d，逐字节命中 %d = %.4f%%' % (len(PLAIN) - len(miss), tot_r, tot_h, 100.0 * tot_h / max(1, tot_r)))
print('未 100%% 命中的文件数 =', len(bad), ' 例:', bad[:8])

# CHS 里是否真有 GBK 中文串
TRAP = set()
for cp in list(range(0x3041, 0x3097)) + list(range(0x30A1, 0x30FB)):
    try: s = chr(cp).encode('cp932').decode('gbk')
    except Exception: continue
    TRAP |= {c for c in s if c >= '\u3000'}
CNRUN = re.compile(r'[\u4e00-\u9fff][\u4e00-\u9fff\u3000-\u303f\uff00-\uffef，。！？、…—～“”‘’：；（）\w]{5,}')
n_cn = 0; examples = []
for n in sorted(PLAIN):
    if n.lower() not in chs_low: continue
    C = open(os.path.join(CHS, chs_low[n.lower()]), 'rb').read()
    ok = True
    # 该文件是否含 >=6 连续非 ASCII 段，且 cp932 无假名而 gbk 解出真中文
    for m in RUN.finditer(C):
        b = m.group(0)
        if len(b) < 8: continue
        try: j = b.decode('cp932')
        except Exception: j = b.decode('cp932', 'replace')
        if HIRA.search(j) or KATA.search(j): continue
        try: g = b.decode('gbk')
        except Exception: continue
        if sum(1 for c in g if c in TRAP) >= 2: continue
        for mm in CNRUN.finditer(g):
            n_cn += 1
            if len(examples) < 6: examples.append((n, mm.group(0)[:50]))
            ok = False
            break
    if not ok: continue
print('CHS 中判定为真 GBK 中文的串数（粗计）=', n_cn)
for e in examples: print('   ', e[0], '->', e[1])

json.dump({'story': story, 'miss': miss, 'extra': extra, 'nonstory': named},
          open(r'E:\ZCode Workspace\Galgame\临时\独立的_清单.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
