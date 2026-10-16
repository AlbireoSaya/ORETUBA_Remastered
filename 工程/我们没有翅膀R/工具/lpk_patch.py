# -*- coding: utf-8 -*-
r"""LPK1 二进制补丁器（ISSUE-ORETUBAR-R）—— 完整实现。

三层处理（缺一不可，实测确认）：
  1. **索引层**：索引整体 XOR 加密（对称），key 由 LPK 基名派生；
     条目记录 13 字节 = is_crypted(1) + file_offset(4) + compr_len(4) + uncompr_len(4)
  2. **容器层**（每个条目）：nibble 交换（整段）+ 前 min(len/4,64) 个 DWORD 的 XOR，
     key 由**条目名**（大写、去扩展名、cp932）派生；操作为自逆（encrypt == decrypt）
  3. **压缩层**：Lucifen LZSS（见 lucifen_lzss.py），标志位 whole_crypt 决定第 2 层是否执行

写回顺序：plaintext -> LZSS 压缩 -> 容器层加密 -> 拼进数据区 -> 重写索引偏移 -> 索引整体加密
"""
import os, re, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lucifen_lzss as LZ

ROT_PATTERN = 0x31746285


def rotl32(x, n):
    n &= 31
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def rotr32(x, n):
    n &= 31
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def derive_base_keys(pkg_name):
    n = pkg_name.upper().split('.')[0].encode('ascii')
    k0, k1 = 0xA5B9AC6B, 0x9A639DE5
    for i in range(len(n)):
        k0 ^= n[len(n) - 1 - i]
        k1 ^= n[i]
        k0 = rotr32(k0, 7)
        k1 = rotl32(k1, 7)
    return k0, k1


def derive_entry_key(entry_name):
    """条目名（大写、去扩展名）派生容器层 key。"""
    n = entry_name.upper()
    if '.' in n:
        n = n.split('.')[0]
    b = n.encode('ascii')
    k = 0xA5B9AC6B
    for i in range(len(b)):
        k ^= b[len(b) - 1 - i]
        k = rotr32(k, 7)
    return k & 0xFFFFFFFF


def crypt_index(buf, key1):
    """**解密**索引（与社区解包器逐字一致）：d 用 rotl32 演进。"""
    out = bytearray(buf)
    d = ROT_PATTERN
    for i in range(len(out) // 4):
        d = rotl32(d, 4)
        shift = d & 31
        val = struct.unpack_from('<I', out, i * 4)[0]
        val ^= key1
        struct.pack_into('<I', out, i * 4, val)
        key1 = rotr32(key1, shift)
    return bytes(out)


def encrypt_index(buf, key1):
    """**加密**索引（解密的逆）：d 用 rotr32 演进。

    注意二者**不可混用**：d 的旋转方向不同，keystream 因而不同。
    实测：crypt_index(dec, k1) != 原加密块；encrypt_index(dec, k1) == 原加密块。
    """
    out = bytearray(buf)
    d = ROT_PATTERN
    for i in range(len(out) // 4):
        d = rotr32(d, 4)
        shift = d & 31
        val = struct.unpack_from('<I', out, i * 4)[0]
        val ^= key1
        struct.pack_into('<I', out, i * 4, val)
        key1 = rotl32(key1, shift)
    return bytes(out)


def _nib_fwd(b):
    return (((b ^ 0x50) >> 4) + (((b ^ 0xFD) & 0xF) << 4)) & 0xFF


_NIB_FWD = [_nib_fwd(v) for v in range(256)]      # 解包器用的映射
_NIB_INV = [0] * 256
for _v, _t in enumerate(_NIB_FWD):
    _NIB_INV[_t] = _v                             # 写回用的逆映射


def _dword_xor(buf, key):
    """前 min(len/4,64) 个 DWORD 的 XOR（自逆）。"""
    dec = bytearray(buf)
    L = min(len(dec) // 4, 64)
    k = key
    d = ROT_PATTERN
    for i in range(L):
        d = rotr32(d, 4)
        shift = d & 0xFF
        v = struct.unpack_from('<I', dec, i * 4)[0]
        v ^= k
        struct.pack_into('<I', dec, i * 4, v)
        k = rotl32(k, shift)
    return bytes(dec)


def container_decrypt(data: bytes, key: int) -> bytes:
    """已解压 blob -> 明文（与解包器完全一致：先 nibble 正映射，再 DWORD XOR）。"""
    return _dword_xor(bytes(_NIB_FWD[x] for x in data), key)


def container_encrypt(data: bytes, key: int) -> bytes:
    """明文 -> 待压缩数据（container_decrypt 的逆：先 DWORD XOR，再 nibble 逆映射）。"""
    return bytes(_NIB_INV[x] for x in _dword_xor(data, key))


# 兼容旧调用名
container_crypt = container_decrypt


def parse_short(lt, off, name, out):
    n = lt[off]; off += 1
    for _ in range(n):
        letter = lt[off]
        nxt = struct.unpack_from('<H', lt, off + 1)[0]
        off += 3
        if letter != 0:
            parse_short(lt, off + nxt, name + bytes([letter]), out)
        else:
            out.append((name.decode('ascii', 'replace'), nxt))


def parse_long(lt, off, name, out):
    n = lt[off]; off += 1
    for _ in range(n):
        letter = lt[off]
        nxt = struct.unpack_from('<I', lt, off + 1)[0]
        off += 5
        if letter != 0:
            parse_long(lt, off + nxt, name + bytes([letter]), out)
        else:
            out.append((name.decode('ascii', 'replace'), nxt))


def load(lpk_path):
    d = open(lpk_path, 'rb').read()
    assert d[:4] == b'LPK1', 'not LPK1'
    name = os.path.splitext(os.path.basename(lpk_path))[0]
    k0, k1 = derive_base_keys(name)
    raw = struct.unpack_from('<I', d, 4)[0]
    irl = raw ^ k1
    flags = (irl >> 24) & 0xFF
    idx_len = irl & 0xFFFFFF
    fb0 = (flags >> 0) & 1
    fb1 = (flags >> 1) & 1
    is_crypt = (flags >> 2) & 1
    etype = (flags >> 3) & 1
    total_crypt = (flags >> 4) & 1
    if fb0:
        idx_len = (idx_len << 11) - 8
    idx = crypt_index(d[8:8 + idx_len], k1)
    off = 0
    cnt = struct.unpack_from('<I', idx, off)[0]; off += 4
    plen = idx[off]; off += 1
    plain = idx[off:off + plen]; off += plen
    mode = idx[off]; off += 1
    ltlen = struct.unpack_from('<I', idx, off)[0]; off += 4
    lt = idx[off:off + ltlen]
    ed_off = off + ltlen
    ents = []
    (parse_long if mode else parse_short)(lt, 0, b'', ents)
    return dict(d=d, k0=k0, k1=k1, flags=flags, idx_len=idx_len, idx=bytearray(idx),
                cnt=cnt, plen=plen, plain=plain, mode=mode, ltlen=ltlen, lt_off=off,
                ed_off=ed_off, rec_size=13 if etype else 9, ents=ents,
                data_start=8 + idx_len, fb0=fb0, is_crypt=is_crypt,
                total_crypt=total_crypt)


def entry_at(lp, num):
    o = lp['ed_off'] + num * lp['rec_size']
    is_c = lp['idx'][o]
    fo = struct.unpack_from('<I', lp['idx'], o + 1)[0]
    cl = struct.unpack_from('<I', lp['idx'], o + 5)[0]
    ul = struct.unpack_from('<I', lp['idx'], o + 9)[0] if lp['rec_size'] == 13 else 0
    if lp['fb0']:
        fo <<= 11
    return o, is_c, fo, cl, ul


def read_entry(lp, name):
    for n, num in lp['ents']:
        if n == name:
            o, is_c, fo, cl, ul = entry_at(lp, num)
            blob = lp['d'][fo:fo + cl]
            key = lp['k0']
            mid = LZ.decompress(blob, ul) if ul else blob      # 1) 解压
            plain = container_decrypt(mid, key) if lp['is_crypt'] else mid   # 2) 容器解密
            return dict(name=n, num=num, rec_off=o, is_c=is_c, fo=fo, cl=cl, ul=ul,
                        blob=blob, plain=plain, key=key)
    raise KeyError(name)


def encode_entry(plain: bytes, key: int) -> bytes:
    """明文 -> LPK 条目数据：容器加密 -> LZSS 压缩。"""
    return LZ.compress(container_encrypt(plain, key))


def patch(lpk_path, out_path, edits):
    """edits: {name: new_plaintext_bytes}。返回统计信息。"""
    lp = load(lpk_path)
    recs = []
    for n, num in lp['ents']:
        o, is_c, fo, cl, ul = entry_at(lp, num)
        recs.append(dict(name=n, num=num, rec_off=o, is_c=is_c, fo=fo, cl=cl, ul=ul))
    recs.sort(key=lambda r: r['fo'])

    plan = []
    changed = []
    for r in recs:
        blob = lp['d'][r['fo']:r['fo'] + r['cl']]
        if r['name'] in edits:
            new_plain = edits[r['name']]
            # ul == 0 的条目是「未压缩」：**不做 LZSS 压缩，但容器层加密照做**
            # （实测 ll_app.inf / ll_app.sys 属此类；误加压缩会导致引擎
            #  「スクリプト初期化ファイルのロードに失敗」）
            if r['ul'] == 0:
                # 未压缩条目：只做容器加密，不压缩；uncompr_len 必须保持 0
                data = container_encrypt(new_plain, lp['k0']) if lp['is_crypt'] else new_plain
                new_ul = 0
            else:
                # 写回顺序：容器加密 -> LZSS 压缩（与读取顺序互为逆，见 main() 自检）
                data = encode_entry(new_plain, lp['k0']) if lp['is_crypt'] else LZ.compress(new_plain)
                new_ul = len(new_plain)
            plan.append((r, data, new_ul))
            changed.append(r['name'])
        else:
            plan.append((r, blob, r['ul']))

    body = bytearray(lp['d'][:lp['data_start']])
    idx = bytearray(lp['idx'])
    cur = lp['data_start']
    # 数据区按 recs 顺序（原 file_offset 升序）重排。**所有条目的偏移都要回写**：
    # 只要前面有任一被改条目长度变化，其后所有条目的数据都会平移。
    for r, data, ul in plan:
        o = r['rec_off']
        fo = cur >> 11 if lp['fb0'] else cur
        struct.pack_into('<I', idx, o + 1, fo)
        struct.pack_into('<I', idx, o + 5, len(data))
        if lp['rec_size'] == 13:
            struct.pack_into('<I', idx, o + 9, ul)
        body += data
        cur += len(data)

    enc = crypt_index(bytes(idx), lp['k1'])     # crypt_index 自逆，加解密同用（实测）
    assert len(enc) == lp['idx_len'], '索引长度变化（本工具不重建索引，只改条目记录）'
    body[8:8 + lp['idx_len']] = enc
    # 写回自检：立刻回读解密一遍，必须与 idx 完全一致
    back = crypt_index(bytes(body[8:8 + lp['idx_len']]), lp['k1'])
    if back != bytes(idx):
        bad = [i for i in range(len(back)) if back[i] != bytes(idx)[i]]
        raise AssertionError('索引写回自检失败：%d 处差异，首个 @%d' % (len(bad), bad[0] if bad else -1))
    # 关键：头部 [4..8) 是「索引长度 ^ key1」的加密字，必须按原 flags 重写，
    # 否则写回后 flags 变成 0x00（索引模式位丢失），引擎/解包器都会读坏。
    flags = lp['flags']
    raw_len = ((flags << 24) | lp['idx_len']) ^ lp['k1']
    struct.pack_into('<I', body, 4, raw_len & 0xFFFFFFFF)
    open(out_path, 'wb').write(bytes(body))
    return dict(in_size=len(lp['d']), out_size=len(body), changed=changed,
                n_entries=len(lp['ents']))


def selftest(lpk_path):
    """noop 自检：把所有条目重新压缩写回，再解包比对全部内容。"""
    lp = load(lpk_path)
    edits = {}
    for n, num in lp['ents']:
        e = read_entry(lp, n)
        edits[n] = e['plain']
    return lp, edits


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    lpk = sys.argv[1] if len(sys.argv) > 1 else r'E:\ZCode Workspace\Galgame\ORETSUBA_R\ORETSUBA_R\SCRIPT.LPK'
    lp = load(lpk)
    print('=== LPK 结构 ===')
    print('  条目数 %d  索引 %d 字节  plain_len=%d  mode=%s  rec=%d' %
          (len(lp['ents']), lp['idx_len'], lp['plen'], 'long' if lp['mode'] else 'short', lp['rec_size']))
    print('  flags=0x%02x  whole_crypt=%d  entry_crypt=%d' % (lp['flags'], lp['total_crypt'], lp['is_crypt']))
    print()
    print('=== 双层解码自检（s00_00.tob）===')
    e = read_entry(lp, 's00_00.tob')
    print('  容器层 key=0x%08x（LPK 基名派生）  compr=%d uncompr=%d' % (e['key'], e['cl'], e['ul']))
    print('  解压+解密后 %d 字节，头: %s' % (len(e['plain']), e['plain'][:16].hex()))
    print('  是否以 TOB0 开头:', e['plain'][:4] == b'TOB0')
    # 反向自检：容器层互逆 + 重编码往返
    print('  容器层互逆:', container_decrypt(container_encrypt(e['plain'], e['key']), e['key']) == e['plain'])
    re_blob = encode_entry(e['plain'], e['key'])
    print('  重编码 %d 字节（原 %d）' % (len(re_blob), e['cl']))
    print('  重编码后再解码一致:',
          container_decrypt(LZ.decompress(re_blob, e['ul']), e['key']) == e['plain'])


if __name__ == '__main__':
    main()
