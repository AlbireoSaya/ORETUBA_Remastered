# -*- coding: utf-8 -*-
r"""选择性解包（只读游戏归档 + 只导出指定条目）。
用法：
  python -X utf8 _lpk_sel.py list  <LPK 路径> [关键字正则]
  python -X utf8 _lpk_sel.py get   <LPK 路径> <输出目录> <条目名> [条目名...]
密钥取自 工具\lucifen\Lucifen-Tools\LPK-Keys.json（本作 R 版有登记）。
"""
import os, re, sys, json, struct, mmap

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = r'E:\ZCode Workspace\Galgame\工具\lucifen\Lucifen-Tools'
sys.path.insert(0, TOOLS)
import lpk_extractor as X

KEYS = os.path.join(TOOLS, 'LPK-Keys.json')
GAME = 'Ore-tachi ni Tsubasa wa Nai'


def _load_keys():
    """LPK-Keys.json 缺外层花括号（非法 JSON），容错包裹后解析。"""
    t = open(KEYS, encoding='utf-8').read().strip()
    if not t.startswith('{'):
        t = '{' + t + '}'
    return json.loads(t)['LPK-Keys']['KnownKeys']


def aux_for(lpk_name: str):
    j = _load_keys()
    g = j.get(GAME) or {}
    k = g.get(lpk_name.upper())
    return (k['Key1'], k['Key2']) if k else None


def parse(path):
    base = os.path.splitext(os.path.basename(path))[0]
    base_sjis = base.encode('cp932', errors='ignore')
    k1, k2 = X.BASE_KEY1, X.BASE_KEY2
    for i in range(len(base_sjis)):
        b = base_sjis[i]
        e = base_sjis[len(base_sjis) - 1 - i]
        k1 ^= e
        k2 ^= b
        k1 = X.rotr32(k1, 7)
        k2 = X.rotl32(k2, 7)
    aux = aux_for(os.path.basename(path))
    if aux:
        k1 ^= aux[0]
        k2 ^= aux[1]
    f = open(path, 'rb')
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    if struct.unpack_from('<I', mm, 0)[0] != 0x314B504C:
        raise ValueError('not LPK1')
    hx = struct.unpack_from('<I', mm, 4)[0] ^ k2
    flags = (hx >> 24) & 0xFF
    tsize = hx & 0xFFFFFF
    if flags & X.ALIGNED_OFFSET:
        tsize = (tsize << 11) - 8
    table = bytearray(mm[8:8 + tsize])
    X.decrypt_table(table, k2, X.ROTATE_PATTERN)
    off = 0
    cnt = struct.unpack_from('<I', table, off)[0]; off += 4
    plen = table[off]; off += 1
    prefix = table[off:off + plen]; off += plen
    osize = 4 if table[off] != 0 else 2; off += 1
    ltlen = struct.unpack_from('<I', table, off)[0]; off += 4
    ents_off = off + ltlen
    esize = 13 if (flags & X.IS_COMPRESSED) else 9
    minis = X.traverse_index(table, off, osize, ents_off, esize)
    ents = []
    for pos0, name in minis:
        pos = pos0
        ef = 0
        if esize & 1:
            ef = table[pos]; pos += 1
        o = struct.unpack_from('<I', table, pos)[0]; pos += 4
        if flags & X.ALIGNED_OFFSET:
            o <<= 11
        sc = struct.unpack_from('<I', table, pos)[0]; pos += 4
        so = sc
        if flags & X.IS_COMPRESSED:
            so = struct.unpack_from('<I', table, pos)[0]; pos += 4
        ents.append(dict(name=name, eflags=ef, off=o, sc=sc, so=so))
    return dict(f=f, mm=mm, flags=flags, k1=k1, k2=k2, prefix=prefix, cnt=cnt, ents=ents)


def extract(lp, name, out_dir):
    e = next(x for x in lp['ents'] if x['name'] == name)
    chunk = bytearray(lp['mm'][e['off']:min(e['off'] + e['sc'], len(lp['mm']))])
    if lp['flags'] & X.IS_COMPRESSED:
        chunk = X.lzss_decompress(bytes(chunk), e['so'])
    if lp['flags'] & X.IS_ENCRYPTED2:
        X.decrypt_content_2_full(chunk, X.CONTENT_XOR)
    if lp['flags'] & X.IS_ENCRYPTED1:
        X.decrypt_content_1_first_256(chunk, lp['k1'], X.ROTATE_PATTERN)
    if lp['prefix']:
        chunk = bytearray(lp['prefix']) + chunk
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, os.path.basename(name))
    open(p, 'wb').write(chunk)
    return p, len(chunk), e['so'], bytes(chunk[:8])


if __name__ == '__main__':
    mode = sys.argv[1]
    lpk = sys.argv[2]
    lp = parse(lpk)
    if mode == 'list':
        pat = re.compile(sys.argv[3], re.I) if len(sys.argv) > 3 else None
        print('%s: %d 条目 flags=0x%02x' % (os.path.basename(lpk), len(lp['ents']), lp['flags']))
        hit = [e for e in lp['ents'] if (pat.search(e['name']) if pat else True)]
        for e in sorted(hit, key=lambda z: -z['so'])[:80]:
            print('   %-40s raw=%-9d orig=%-9d' % (e['name'], e['sc'], e['so']))
        print('   命中 %d 条' % len(hit))
    elif mode == 'get':
        out = sys.argv[3]
        for name in sys.argv[4:]:
            p, n, so, head = extract(lp, name, out)
            print('   %-40s → %s (%d 字节, orig=%d, 头=%s)' % (name, p, n, so, head.hex()))
