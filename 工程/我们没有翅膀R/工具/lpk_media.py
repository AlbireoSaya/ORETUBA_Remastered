# -*- coding: utf-8 -*-
r"""Lucifen 素材归档（CHR/PIC/SYS/BGM/SE/VOICE/DATA.LPK）的选择性提取。

与 `lpk_patch.py` 的分工：后者专精 SCRIPT.LPK（自研四层实现，已验证）；
本模块借道社区工具（`工具\lucifen\Lucifen-Tools\lpk_extractor.py`，GPL-3.0，**只 import 不复制**）
处理其余归档——它们的索引变体与 SCRIPT.LPK 不同（我们的实现会 IndexError），
且密钥取自社区 `LPK-Keys.json` 中本作（Ore-tachi ni Tsubasa wa Nai R）条目。

用法（库）：
    import lpk_media as M
    lp = M.load(r'...\CHR.LPK')
    names = M.names(lp)                       # 全部条目名
    data  = M.read(lp, 'chr\\ai_01.elg')      # 大小写不敏感
用法（命令行）：
    python -X utf8 lpk_media.py list <LPK> [正则]
    python -X utf8 lpk_media.py get  <LPK> <输出目录> <条目名> [...]
"""
import os, re, sys, json, struct, mmap, collections

WS = r'E:\ZCode Workspace\Galgame'
COMMUNITY = os.path.join(WS, '工具', 'lucifen', 'Lucifen-Tools')
KEYS = os.path.join(COMMUNITY, 'LPK-Keys.json')
GAME = 'Ore-tachi ni Tsubasa wa Nai R'
sys.path.insert(0, COMMUNITY)
import lpk_extractor as X  # noqa: E402


def _known_keys():
    t = open(KEYS, encoding='utf-8').read().strip()
    if not t.startswith('{'):          # 该文件缺外层花括号（非法 JSON），容错包裹
        t = '{' + t + '}'
    return json.loads(t)['LPK-Keys']['KnownKeys']


def aux_for(lpk_path: str):
    g = _known_keys().get(GAME) or {}
    k = g.get(os.path.basename(lpk_path).upper())
    return (k['Key1'], k['Key2']) if k else None


def load(lpk_path):
    """解析归档索引，返回句柄（不读数据区，mmap 惰性）。"""
    base = os.path.splitext(os.path.basename(lpk_path))[0]
    k1, k2 = X.BASE_KEY1, X.BASE_KEY2
    bs = base.encode('cp932', errors='ignore')
    for i in range(len(bs)):
        k1 ^= bs[len(bs) - 1 - i]
        k2 ^= bs[i]
        k1 = X.rotr32(k1, 7)
        k2 = X.rotl32(k2, 7)
    aux = aux_for(lpk_path)
    if aux:
        k1 ^= aux[0]
        k2 ^= aux[1]
    f = open(lpk_path, 'rb')
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    if struct.unpack_from('<I', mm, 0)[0] != 0x314B504C:
        raise ValueError('不是 LPK1：%s' % lpk_path)
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
    esize = 13 if (flags & X.IS_COMPRESSED) else 9
    minis = X.traverse_index(table, off, osize, off + ltlen, esize)
    ents = {}
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
        ents[name.lower()] = dict(name=name, eflags=ef, off=o, sc=sc, so=so)
    return dict(path=lpk_path, f=f, mm=mm, flags=flags, k1=k1, k2=k2,
                prefix=prefix, cnt=cnt, ents=ents)


def names(lp):
    return sorted(e['name'] for e in lp['ents'].values())


def has(lp, name: str):
    return name.lower() in lp['ents']


def info(lp, name: str):
    return lp['ents'].get(name.lower())


def read(lp, name: str) -> bytes:
    """按名取条目明文（大小写不敏感）。"""
    e = lp['ents'].get(name.lower())
    if e is None:
        raise KeyError(name)
    mm = lp['mm']
    chunk = bytearray(mm[e['off']:min(e['off'] + e['sc'], len(mm))])
    if lp['flags'] & X.IS_COMPRESSED:
        chunk = X.lzss_decompress(bytes(chunk), e['so'])
    if lp['flags'] & X.IS_ENCRYPTED2:
        X.decrypt_content_2_full(chunk, X.CONTENT_XOR)
    if lp['flags'] & X.IS_ENCRYPTED1:
        X.decrypt_content_1_first_256(chunk, lp['k1'], X.ROTATE_PATTERN)
    if lp['prefix']:
        chunk = bytearray(lp['prefix']) + chunk
    return bytes(chunk)


def usage(lp):
    """返回 {条目名: 明文大小}（用于体积预估，不解数据）。"""
    return {e['name']: e['so'] for e in lp['ents'].values()}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    mode, path = sys.argv[1], sys.argv[2]
    lp = load(path)
    if mode == 'list':
        pat = re.compile(sys.argv[3], re.I) if len(sys.argv) > 3 else None
        hit = [e for e in lp['ents'].values() if (pat.search(e['name']) if pat else True)]
        print('%s: %d 条目 flags=0x%02x' % (os.path.basename(path), len(lp['ents']), lp['flags']))
        for e in sorted(hit, key=lambda z: -z['so'])[:100]:
            print('   %-38s raw=%-9d orig=%-9d' % (e['name'], e['sc'], e['so']))
        print('   命中 %d 条' % len(hit))
    elif mode == 'get':
        out = sys.argv[3]
        for name in sys.argv[4:]:
            d = read(lp, name)
            os.makedirs(out, exist_ok=True)
            p = os.path.join(out, info(lp, name)['name'])
            open(p, 'wb').write(d)
            print('   %-38s → %s (%d 字节, 头=%s)' % (name, p, len(d), d[:8].hex()))


if __name__ == '__main__':
    main()
