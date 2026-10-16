# -*- coding: utf-8 -*-
r"""Lucifen 素材归档（CHR/PIC/SYS/BGM/SE/VOICE/DATA.LPK）的选择性提取 —— 多作品参数化版。

**本文件是 `工程\我们没有翅膀R\工具\lpk_media.py` 的副本并做了参数化改造**（原件的 GAME 常量
写死为 `'Ore-tachi ni Tsubasa wa Nai R'`，无法处理本工程的 S1 本篇与 S3 After Story）。
原件属于其他会话的在用工具，**不得修改**；本副本归《我们没有翅膀——格雷塔迦露德与柳木原》资源组使用。

与 `lpk_patch.py` 的分工：后者专精 SCRIPT.LPK（自研四层实现）；本模块借道社区工具
（`工具\lucifen\Lucifen-Tools\lpk_extractor.py`，GPL-3.0，**只 import 不复制**）处理其余归档——
它们的索引变体与 SCRIPT.LPK 不同（自研实现会 IndexError），密钥取自社区 `LPK-Keys.json`。

用法（库）：
    import lpk_media as M
    lp = M.load(r'...\CHR.LPK', game='Ore-tachi ni Tsubasa wa Nai')
    names = M.names(lp)                        # 全部条目名
    data  = M.read(lp, 'chr\\ai_01.elg')       # 大小写不敏感
    M.usage(lp)                                # {条目名: 明文大小}

用法（命令行）：
    python -X utf8 lpk_media.py list <LPK> --game "<键名>" [正则]
    python -X utf8 lpk_media.py get  <LPK> <输出目录> --game "<键名>" <条目名> [...]
    python -X utf8 lpk_media.py games           # 列出 LPK-Keys.json 中全部可用作品键名
    python -X utf8 lpk_media.py keys <gameinit.sob> --game "<键名>"   # 自述密钥 vs 社区表比对

**密钥覆盖**：社区 `LPK-Keys.json` 中 `Ore-tachi ni Tsubasa wa Nai` 的 SE.LPK Key1 有误
（0x9A5AF6DE → 0x935AF6DE），本模块用 `KEY_OVERRIDES` 覆盖（不改社区文件）；
覆盖值取自该作品 `gameinit.sob` 的游戏自述。详见 `KEY_OVERRIDES` 上方注释。

本工程用到的三个键名（已实测七档齐全）：
    S1 本篇         Ore-tachi ni Tsubasa wa Nai
    S2 R 版         Ore-tachi ni Tsubasa wa Nai R
    S3 After Story  Ore-tachi ni Tsubasa wa Nai AfterStory
"""
import os, re, sys, json, struct, mmap

WS = r'E:\ZCode Workspace\Galgame'
COMMUNITY = os.path.join(WS, '工具', 'lucifen', 'Lucifen-Tools')
KEYS = os.path.join(COMMUNITY, 'LPK-Keys.json')
sys.path.insert(0, COMMUNITY)
import lpk_extractor as X  # noqa: E402

# ---------------------------------------------------------------------------
# 密钥覆盖表（W5b 修复，ISSUE-20260918-06）
# ---------------------------------------------------------------------------
# 背景：社区 `LPK-Keys.json` 中 `Ore-tachi ni Tsubasa wa Nai` 的 SE.LPK 条目
# **Key1 写错 1 字节**（0x9A5AF6DE → 应为 0x935AF6DE）。Key1 仅用于
# `decrypt_content_1_first_256()`（内容区前 256 字节），Key2 正确 → 索引正常、
# 只有文件头损坏（症状：ffprobe 报 CRC mismatch、无 Vorbis identification header）。
#
# 证据：`工程\我们没有翅膀\解包\SCRIPT\gameinit.sob` 中游戏自述的 7 条密钥记录
# （偏移 0x1594 起、间隔 0x88、结构 <u32 Key1><u32 flag=8><u32 Key2>），
# 与社区表逐条比对 6/7 命中，唯一不命中的就是 SE.LPK 的 Key1。
# 其余 6 档（SYS/CHR/PIC/BGM/VOICE/DATA）与社区表逐字节一致。
#
# 社区文件 `工具\lucifen\Lucifen-Tools\LPK-Keys.json` **只读、不得修改**；
# 覆盖一律在本表进行。值取自游戏自述（gameinit.sob），非猜测。
KEY_OVERRIDES = {
    ('Ore-tachi ni Tsubasa wa Nai', 'SE.LPK'): {
        'Key1': 0x935AF6DE,
        'Key2': 0xCB1866C7,
        'source': 'gameinit.sob@0x17B4（游戏自述；社区表 Key1 有误）',
    },
}


def _known_keys():
    t = open(KEYS, encoding='utf-8').read().strip()
    if not t.startswith('{'):          # 该文件缺外层花括号（非法 JSON），容错包裹
        t = '{' + t + '}'
    return json.loads(t)['LPK-Keys']['KnownKeys']


def known_games():
    return sorted(_known_keys().keys())


def aux_for(lpk_path: str, game: str):
    """返回 (Key1, Key2)；先查社区表，再套用本模块的覆盖表。"""
    base = os.path.basename(lpk_path).upper()
    g = _known_keys().get(game) or {}
    k = g.get(base)
    if not k:
        return None
    pair = (k['Key1'], k['Key2'])
    ov = KEY_OVERRIDES.get((game, base))
    if ov:
        return (ov['Key1'], ov['Key2'])
    return pair


def community_aux_for(lpk_path: str, game: str):
    """只返回社区表原值（用于交叉校验/报告，不受覆盖影响）。"""
    g = _known_keys().get(game) or {}
    k = g.get(os.path.basename(lpk_path).upper())
    return (k['Key1'], k['Key2']) if k else None


# ---------------------------------------------------------------------------
# gameinit.sob 自述密钥解析（通用能力，为后续作品防止同类问题）
# ---------------------------------------------------------------------------
# 结构（S1 本篇实测）：记录 = <u32 Key1><u32 count=8><u32 Key2><u32 count=5>
#                               <u32 0x67><u32 0><u32 0x0180BE8A><u32 0x0C> ...
# 记录间隔 0x88；但**偏移与字段常量可能因作品而异**，故做健壮搜索：
#   1) 结构签名法：找连续 ≥min_run 条、间隔 stride、且 +4/+12 两处常量一致 的记录；
#   2) 社区表回退法：用社区表的 (Key1,Key2) 对反查出现位置并验证 stride。
# Key1 取 +0，Key2 取 +8。
GAMEGEN_STRIDE = 0x88
GAMEGEN_SIG_A = 4     # +4 处 u32 常量（记录内计数）
GAMEGEN_SIG_B = 12    # +12 处 u32 常量


def _find_structural_run(d, stride=GAMEGEN_STRIDE, min_run=4):
    """结构签名法：返回 (base_off, n_records) 或 None。"""
    n = len(d)
    best = None
    o = 0
    while o + stride * min_run + 12 < n:
        a = struct.unpack_from('<I', d, o + GAMEGEN_SIG_A)[0]
        b = struct.unpack_from('<I', d, o + GAMEGEN_SIG_B)[0]
        if a == 8 and b == 5:
            cnt = 1
            p = o + stride
            while p + 12 < n:
                if (struct.unpack_from('<I', d, p + GAMEGEN_SIG_A)[0] == 8
                        and struct.unpack_from('<I', d, p + GAMEGEN_SIG_B)[0] == 5):
                    cnt += 1
                    p += stride
                else:
                    break
            if cnt >= min_run and (best is None or cnt > best[1]):
                best = (o, cnt)
            o = p if cnt >= min_run else o + 4
        else:
            o += 4
    return best


def _find_community_run(d, cand_pairs, stride=GAMEGEN_STRIDE, min_run=4):
    """社区表回退法：cand_pairs = set of (Key1,Key2)。"""
    hits = {}
    for k1, k2 in cand_pairs:
        b1 = struct.pack('<I', k1)
        b2 = struct.pack('<I', k2)
        start = 0
        while True:
            i = d.find(b1, start)
            if i < 0:
                break
            if i + 12 <= len(d) and struct.unpack_from('<I', d, i + 8)[0] == k2:
                hits.setdefault(i, 0)
                hits[i] += 1
            start = i + 1
    # 找最长的 stride 链
    offs = sorted(hits)
    best = None
    i = 0
    while i < len(offs):
        run = [offs[i]]
        j = i + 1
        while j < len(offs) and offs[j] - run[-1] == stride:
            run.append(offs[j]); j += 1
        if len(run) >= min_run and (best is None or len(run) > len(best[1])):
            best = (run[0], run)
        i = j if len(run) >= min_run else i + 1
    return best


def parse_gameinit_keys(sob_path, community_pairs=None, stride=GAMEGEN_STRIDE,
                        min_run=4):
    """从 gameinit.sob 解析自述密钥记录，返回 dict：
        {'method', 'base_offset', 'count', 'records': [{'index','offset','key1','key2'}]}
    community_pairs：可选的 (Key1,Key2) 集合，用于结构法失败时回退。
    """
    with open(sob_path, 'rb') as f:
        d = f.read()
    run = _find_structural_run(d, stride, min_run)
    method = 'structural'
    if run is None and community_pairs:
        c = _find_community_run(d, community_pairs, stride, min_run)
        if c:
            base, offs = c
            run = (base, len(offs))
            method = 'community-fallback'
    if run is None:
        raise ValueError('未能在 %s 中定位自述密钥记录表' % sob_path)
    base, cnt = run
    recs = []
    for i in range(cnt):
        o = base + i * stride
        k1 = struct.unpack_from('<I', d, o)[0]
        k2 = struct.unpack_from('<I', d, o + 8)[0]
        recs.append({'index': i, 'offset': o, 'key1': k1, 'key2': k2})
    return {'method': method, 'base_offset': base, 'count': cnt, 'records': recs}


def cross_check_keys(sob_path, game, stride=GAMEGEN_STRIDE):
    """解析自述密钥并与社区表逐条比对（先按 Key2 唯一配对，再按顺序配对）。

    返回 dict：{'records', 'comparisons':[{archive, gameinit, community, match, field}],
               'mismatches', 'unmatched'}
    社区表中 SE.LPK 的 Key1 与自述不符即为预期的不一致项。
    """
    community = _known_keys().get(game) or {}
    pairs = {(v['Key1'], v['Key2']) for v in community.values()}
    parsed = parse_gameinit_keys(sob_path, pairs, stride=stride)
    recs = parsed['records']

    # 归档名推定：优先按 Key2 唯一匹配，其次按 Key1，再按出现顺序（S1 实测顺序固定）
    by_k2 = {}
    by_k1 = {}
    for name, v in community.items():
        by_k2.setdefault(v['Key2'], []).append(name)
        by_k1.setdefault(v['Key1'], []).append(name)
    order = ['SYS.LPK', 'CHR.LPK', 'PIC.LPK', 'BGM.LPK', 'SE.LPK',
             'VOICE.LPK', 'DATA.LPK']

    comps = []
    used = set()
    for r in recs:
        name = None
        if len(by_k2.get(r['key2'], [])) == 1:
            name = by_k2[r['key2']][0]
        elif len(by_k1.get(r['key1'], [])) == 1:
            name = by_k1[r['key1']][0]
        elif r['index'] < len(order) and order[r['index']] not in used:
            name = order[r['index']]
        used.add(name)
        cv = community.get(name) if name else None
        row = {'index': r['index'], 'offset': hex(r['offset']), 'archive': name,
               'gameinit': {'Key1': r['key1'], 'Key2': r['key2']},
               'community': ({'Key1': cv['Key1'], 'Key2': cv['Key2']} if cv else None)}
        if cv:
            row['match_Key1'] = (r['key1'] == cv['Key1'])
            row['match_Key2'] = (r['key2'] == cv['Key2'])
            row['match'] = row['match_Key1'] and row['match_Key2']
        else:
            row['match'] = None
        comps.append(row)

    mismatches = [c for c in comps if c.get('match') is False]
    unmatched = [c for c in comps if c.get('match') is None]
    return {'method': parsed['method'], 'base_offset': hex(parsed['base_offset']),
            'count': parsed['count'], 'records': recs,
            'comparisons': comps, 'mismatches': mismatches, 'unmatched': unmatched}


def load(lpk_path, game=None):
    """解析归档索引，返回句柄（不读数据区，mmap 惰性）。

    game：LPK-Keys.json 中的作品键名。缺省取环境变量 LPK_GAME。
    """
    game = game or os.environ.get('LPK_GAME')
    if not game:
        raise ValueError('必须指定 game（LPK-Keys.json 的作品键名）；可用 %s' % known_games())
    base = os.path.splitext(os.path.basename(lpk_path))[0]
    k1, k2 = X.BASE_KEY1, X.BASE_KEY2
    bs = base.encode('cp932', errors='ignore')
    for i in range(len(bs)):
        k1 ^= bs[len(bs) - 1 - i]
        k2 ^= bs[i]
        k1 = X.rotr32(k1, 7)
        k2 = X.rotl32(k2, 7)
    aux = aux_for(lpk_path, game)
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
                prefix=prefix, cnt=cnt, ents=ents, game=game)


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


def _split_argv(argv):
    """从 argv 中摘出 --game <值>，返回 (其余参数, game)。"""
    game = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == '--game':
            game = argv[i + 1]; i += 2
        elif argv[i].startswith('--game='):
            game = argv[i].split('=', 1)[1]; i += 1
        else:
            rest.append(argv[i]); i += 1
    return rest, game


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args, game = _split_argv(sys.argv[1:])
    if not args:
        print(__doc__)
        return
    if args[0] == 'games':
        for g in known_games():
            print('  %s' % g)
        return
    if args[0] == 'keys':
        # 解析 gameinit.sob 自述密钥并与社区表比对（--game 指定作品键名）
        sob = args[1]
        cc = cross_check_keys(sob, game)
        print('解析方式 %s，基址 %s，共 %d 条' % (cc['method'], cc['base_offset'], cc['count']))
        print('%-10s %-14s %-14s %-14s %s' % ('归档', '自述Key1', '社区Key1', '自述Key2', '一致'))
        for c in cc['comparisons']:
            g1 = '0x%08X' % c['gameinit']['Key1']
            g2 = '0x%08X' % c['gameinit']['Key2']
            c1 = ('0x%08X' % c['community']['Key1']) if c['community'] else '(未匹配)'
            mark = 'OK' if c['match'] else ('不一致' if c['match'] is False else '未匹配')
            print('%-10s %-14s %-14s %-14s %s' % (c['archive'], g1, c1, g2, mark))
        print('不一致项 %d 条' % len(cc['mismatches']))
        for m in cc['mismatches']:
            print('   ! %s 自述 Key1=0x%08X 社区 Key1=0x%08X' %
                  (m['archive'], m['gameinit']['Key1'], m['community']['Key1']))
        return
    mode, path = args[0], args[1]
    lp = load(path, game)
    if mode == 'list':
        pat = re.compile(args[2], re.I) if len(args) > 2 else None
        hit = [e for e in lp['ents'].values() if (pat.search(e['name']) if pat else True)]
        print('%s [%s]: %d 条目 flags=0x%02x' % (os.path.basename(path), lp['game'], len(lp['ents']), lp['flags']))
        for e in sorted(hit, key=lambda z: -z['so'])[:100]:
            print('   %-38s raw=%-9d orig=%-9d' % (e['name'], e['sc'], e['so']))
        print('   命中 %d 条' % len(hit))
    elif mode == 'get':
        out = args[2]
        for name in args[3:]:
            d = read(lp, name)
            os.makedirs(out, exist_ok=True)
            p = os.path.join(out, info(lp, name)['name'])
            open(p, 'wb').write(d)
            print('   %-38s → %s (%d 字节, 头=%s)' % (name, p, len(d), d[:8].hex()))
    else:
        print('未知模式：%s' % mode)


if __name__ == '__main__':
    main()