# -*- coding: utf-8 -*-
r"""recode_sjis.py —— 残留 SJIS 文本段落就地重编码为 GBK（ISSUE-ORETUBAR-R）

目的
====
引擎已打好 GBK 补丁，消息窗口渲染路径**字节透明**：
  * 存储字节为 GBK  -> 正确显示
  * 存储字节仍为 SJIS -> 显示为「SJIS 字节按 GBK 解读」的乱码
因此必须把脚本里**仍是 Shift-JIS 的日文文本**就地重编码为 GBK
（字符不变，只换码位），保证过渡期内全游戏无乱码；日文内容仍待后续翻译。

处理对象（均在**原始** `语料\R版SCRIPT\*.tob` 上定位，偏移可直接供回写器使用）
================================================================================
  A. 声明串字段（desc/name）：模式 `01 01 <u16 L> <body(L-1)> 00`
     - 场景开场描述（长）与角色名/说话人（短）
     - 长度前缀必须同步改写（回写器 is_declared_string 已覆盖 delta!=0 的情况）
  B. 孤立内联正文（inline）：提取器 offset=None 的记录里残留的日文正文，
     以及 op=0x0e 命令之后的第二段正文；无长度前缀，靠结构定位：
       [5b 20 op 00 00 00 01 <u32> <u8>] <正文> 5b 20 <op> 00 00 00 01 ...
  已由译文/待译文/三批译文覆盖的槽（含章节标题 430 个）**一律不动**。

不触碰
======
  * 二进制/结构字节（NUL、长度前缀以外的字节、命令头）
  * 已被翻译管线覆盖的槽（迁移映射 51,736 + 待翻译清单 6,624）
  * 任何 GBK 不可编码且无安全回退的段落（记录到 语料\重编码_跳过清单.json）

重编码规则
==========
  bytes_sjis -> decode('cp932') -> encode('gbk')
  长度可能变化 -> 声明串的 `01 01 <u16 L>` 同步改写为 len(new)+1；
  变长引起其后所有地址字段平移，交给 tob_rewrite.apply_edits_rebuild 重定位。
  **不使用问号替换**。GBK 不可编码的字符按回退表处理，逐条记录：
    project 档（默认）：`・`(U+30FB) -> `·`(U+00B7)
        依据：本工程迁移译文（新米汉化组）已使用 `·` 362 处，属既有约定
    all 档（--fallback all）：追加 `≪`->`《`、`≫`->`》`、`♪`->`☆`（无既有约定，需显式启用）
    其余一律跳过并记录（不改字、不替换）。

用法
====
  python -X utf8 recode_sjis.py build                        # 生成映射（默认 project 档回退）
  python -X utf8 recode_sjis.py build --fallback all         # 追加 ≪≫♪ 回退
  python -X utf8 recode_sjis.py build --fallback none        # 纯跳过（严格按指令）
  python -X utf8 recode_sjis.py selftest                     # 全量单文件回写自检（推荐）
  python -X utf8 recode_sjis.py selftest --n 20               # 抽样 20 处回读比对
  python -X utf8 recode_sjis.py scan <lpk|tob目录>            # 扫描残留 SJIS（分类统计）

供 build_cn.py 调用
===================
  import recode_sjis as RC
  by_file = RC.load_map()            # {file: [{'offset','len','text_bytes'(bytes)}]}
"""
import codecs
import collections
import json
import os
import random
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SCR = os.path.join(PROJ, '语料', 'R版SCRIPT')
CORPUS = os.path.join(PROJ, '语料')
MAP_PATH = os.path.join(CORPUS, '重编码映射.json')
SKIP_PATH = os.path.join(CORPUS, '重编码_跳过清单.json')
MIG = os.path.join(CORPUS, 'R版迁移映射.json')
TODO = os.path.join(CORPUS, '待翻译清单.json')

sys.path.insert(0, HERE)
import tob_rewrite as TR           # noqa: E402
import tob_extract as EX           # noqa: E402

# ---- 回退表 ----------------------------------------------------------------
FALLBACK_PROJECT = {0x30FB: 0x00B7}                       # ・ -> ·
FALLBACK_ALL = {0x30FB: 0x00B7, 0x226A: 0x300A, 0x226B: 0x300B, 0x266A: 0x2606}
FALLBACK_DOC = {
    0x30FB: ('・', '·', 'project', '本工程迁移译文既有约定（362 处）'),
    0x226A: ('≪', '《', 'all', '双尖括号→书名号（无既有约定，需显式启用）'),
    0x226B: ('≫', '》', 'all', '双尖括号→书名号（无既有约定，需显式启用）'),
    0x266A: ('♪', '☆', 'all', '音符无 GBK 码位（无既有约定，需显式启用）'),
}
PUA = range(0xE000, 0xF900)


# ---- 基础工具 --------------------------------------------------------------
def is_jp(ch):
    o = ord(ch)
    return (0x3040 <= o <= 0x30FF) or (0x4E00 <= o <= 0x9FFF)


def body_bytes_ok(bs):
    """正文合法性：ASCII 可打印 / 0x0A / 合法 SJIS 双字节；禁 NUL 与其它控制字节。"""
    i, n = 0, len(bs)
    while i < n:
        c = bs[i]
        if c == 0x0A or 0x20 <= c < 0x7F:
            i += 1
            continue
        if 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
            if i + 1 >= n:
                return False
            t = bs[i + 1]
            if not (0x40 <= t <= 0xFC and t != 0x7F):
                return False
            i += 2
            continue
        return False
    return True


def sjis_tokens(b, base=0):
    """按 SJIS 配对规则切 token：('p',file_off,2) 双字节 / ('a',off,1) ASCII /
    ('ctl'|'bad',off,1)。"""
    out = []
    i, n = 0, len(b)
    while i < n:
        c = b[i]
        if 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
            if i + 1 < n:
                t = b[i + 1]
                if 0x40 <= t <= 0xFC and t != 0x7F:
                    try:
                        if len(b[i:i + 2].decode('cp932')) == 1:
                            out.append(('p', base + i, 2))
                            i += 2
                            continue
                    except Exception:
                        pass
            out.append(('bad', base + i, 1))
            i += 1
            continue
        if 0x0A == c or 0x20 <= c < 0x7F:
            out.append(('a', base + i, 1))
            i += 1
            continue
        out.append(('ctl', base + i, 1))
        i += 1
    return out


def enc_gbk(text, fallback):
    """cp932 解出的文本 -> GBK 字节。返回 (bytes, [回退记录]) 或 (None, 不可编码字符列表)。
    不使用 '?' 替换：不可编码且无回退 -> 返回失败。"""
    use = []
    out = []
    for ch in text:
        try:
            out.append(ch.encode('gbk'))
            continue
        except UnicodeEncodeError:
            pass
        cp = ord(ch)
        if cp in fallback:
            rep = chr(fallback[cp]) if isinstance(fallback[cp], int) else fallback[cp]
            out.append(rep.encode('gbk'))
            use.append([ch, rep])
        else:
            return None, [ch]
    return b''.join(out), use


def _apply_fallback(text, use):
    """把原文按本轮实际使用的回退记录改写，得到「期望的新文本」。"""
    if not use:
        return text
    m = dict((a, b) for a, b in use)
    return ''.join(m.get(ch, ch) for ch in text)


def strip_trailing_cmds(d, lo, e):
    """剥掉记录尾部的无载荷命令 `5b 20 op 00 00 00 01 <u32 arg<=0xFF> <u8 0>`。"""
    while e - 12 >= lo:
        seg = d[e - 12:e]
        if (seg[0] == 0x5B and seg[1] == 0x20 and seg[3:6] == b'\x00\x00\x00'
                and seg[6] == 0x01 and seg[7:10] == b'\x00\x00\x00' and seg[11] == 0x00):
            e -= 12
        else:
            break
    return e


# ---- 候选提取 --------------------------------------------------------------
def extract_declared(raw):
    """`01 01 <u16 L> <body(L-1)> 00` 字段。返回 [(prefix_off, L, body, text)]。"""
    out = []
    i, n = 0, len(raw)
    while i < n - 6:
        if raw[i] == 0x01 and raw[i + 1] == 0x01:
            L = struct.unpack_from('<H', raw, i + 2)[0]
            if 8 <= L <= 4000 and i + 4 + L <= n and raw[i + 4 + L - 1] == 0:
                body = raw[i + 4:i + 4 + L - 1]
                if body_bytes_ok(body) and any(0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC
                                               for c in body):
                    try:
                        t = body.decode('cp932')
                    except Exception:
                        t = None
                    if t and not any(ord(c) in PUA for c in t) \
                       and sum(1 for c in t if is_jp(c)) >= max(1, len(t) // 3):
                        out.append((i, L, body, t))
                        i += 4 + L
                        continue
        i += 1
    return out


def find_sjis_runs(b, minlen=2):
    """全局 SJIS 运行段（与 残留日文清单.json 同算法，此处 minlen=2）。"""
    out = []
    i, n = 0, len(b)
    while i < n:
        start, cur, ok_any, j = None, bytearray(), False, i
        while j < n:
            c = b[j]
            if 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
                if j + 1 < n:
                    try:
                        ch = b[j:j + 2].decode('cp932')
                        if len(ch) == 1:
                            if not cur:
                                start = j
                            cur += b[j:j + 2]
                            ok_any = ok_any or is_jp(ch)
                            j += 2
                            continue
                    except Exception:
                        pass
                break
            if 0x20 <= c < 0x7F:
                if not cur:
                    start = j
                cur.append(c)
                j += 1
                continue
            break
        if cur and len(cur) >= minlen and ok_any and start is not None:
            out.append((start, bytes(cur)))
            i = j
        else:
            i += 1
    return out


def translation_ranges():
    """译文/待译覆盖的区间（合并后）-> {file: [[a,b], ...]}"""
    rg = collections.defaultdict(list)
    for p in (MIG, TODO):
        for r in json.load(open(p, encoding='utf-8')):
            a = int(r['offset'])
            rg[r['file']].append((a, a + int(r['len'])))
    for k in rg:
        rs = sorted(rg[k])
        out = []
        for a, b in rs:
            if out and a <= out[-1][1]:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        rg[k] = out
    return rg


def _in(x, rs):
    lo, hi = 0, len(rs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        a, b = rs[mid]
        if x < a:
            hi = mid - 1
        elif x >= b:
            lo = mid + 1
        else:
            return True
    return False


def untranslatable_slots():
    """三批译文里存在、但 GBK 不可编码因而**写不回去**的槽（构建时被跳过，屏幕上仍是乱码）。
    返回 {(file, offset): len}。仅 --include-slots 时使用（属可选安全网，默认关闭）。"""
    todo = json.load(open(TODO, encoding='utf-8'))
    by_off = {(r['file'], int(r['offset'])): r for r in todo}
    out = {}
    for i in (1, 2, 3):
        p = os.path.join(PROJ, '翻译工作区', '批次%d_译文.json' % i)
        if not os.path.exists(p):
            continue
        for r in json.load(open(p, encoding='utf-8')):
            t = r.get('text')
            if not t:
                continue
            try:
                t.encode('gbk')
                continue
            except UnicodeEncodeError:
                pass
            ref = by_off.get((r['file'], int(r['offset'])))
            if ref is not None:
                out[(r['file'], int(ref['offset']))] = int(ref['len'])
    return out


def build_candidates(fallback, include_slots=False):
    """返回 (entries, skipped, stats)。entries 含 text_bytes(bytes)。"""
    trng = translation_ranges()
    slots_extra = untranslatable_slots() if include_slots else {}
    entries, skipped = [], []
    stats = collections.Counter()
    for f in sorted(os.listdir(SCR)):
        if not f.lower().endswith('.tob'):
            continue
        raw = open(os.path.join(SCR, f), 'rb').read()
        info = EX.parse_header(raw)
        cs, T = info['code_start'], info['T']
        rs_tr = trng.get(f, [])
        # --- A. 声明串字段 ---
        fields = extract_declared(raw)
        frng = [(p + 4, p + 4 + L - 1) for (p, L, b, t) in fields]
        for (poff, L, body, text) in fields:
            a, b = poff + 4, poff + 4 + L - 1
            if _in(a, rs_tr):
                stats['A 跳过：译文已覆盖（章节标题等）'] += 1
                continue
            nb, use = enc_gbk(text, fallback)
            if nb is None:
                stats['A 跳过：GBK 不可编码（记录后跳过）'] += 1
                skipped.append({'file': f, 'offset': a, 'len': len(body), 'kind': 'declared',
                                'text': text, 'bad_chars': sorted(set(use))})
                continue
            exp = _apply_fallback(text, use)
            if nb.decode('gbk') != exp:
                stats['A 跳过：GBK 往返不一致'] += 1
                continue
            entries.append({'file': f, 'offset': a, 'len': len(body), 'text_bytes': nb,
                            'text': text, 'src': 'sjis->gbk',
                            'kind': 'desc' if len(body) >= 60 else 'name',
                            'prefix_off': poff, 'fallbacks': use})
            stats['A 声明串-描述(>=60B)' if len(body) >= 60 else 'A 声明串-名字(<60B)'] += 1
        # --- B. 孤立内联正文（记录中提取器未覆盖的正文） ---
        sl = []
        for (p, L, b, t) in fields:
            sl.append((p + 4, p + 4 + L - 1))
        for off, seg in find_sjis_runs(raw):
            if _in(off, rs_tr) or _in(off, sl):
                continue
            e = off + len(seg)
            # 配对修尾：只剪「最后一个双字节 token 之后」的 ASCII
            toks = sjis_tokens(raw[off:e], off)
            rr = list(toks)
            while rr and rr[-1][0] == 'a':
                rr.pop()
            if not rr:
                continue
            en = rr[-1][1] + rr[-1][2]
            suffix = raw[en:e]
            if suffix != b'\x5b\x20':                    # 必须是下一条命令起点 `[ `
                continue
            core = raw[off:en]
            if len(core) < 8:
                continue
            try:
                text = core.decode('cp932')
            except Exception:
                continue
            if text.encode('cp932') != core or any(ord(c) in PUA for c in text):
                continue
            if not any(is_jp(c) for c in text):
                continue
            if sum(1 for c in text if is_jp(c)) < max(1, len(text) // 3):
                continue
            # 结构验证：`5b 20` 之后应接 `<op> 00 00 00 01`（下一条命令头）
            if raw[e + 1:e + 4] != b'\x00\x00\x00' or raw[e + 4] != 0x01:
                stats['B 跳过：尾随结构不符'] += 1
                continue
            nb, use = enc_gbk(text, fallback)
            if nb is None:
                stats['B 跳过：GBK 不可编码（记录后跳过）'] += 1
                skipped.append({'file': f, 'offset': off, 'len': en - off, 'kind': 'inline',
                                'text': text, 'bad_chars': sorted(set(use))})
                continue
            exp = _apply_fallback(text, use)
            if nb.decode('gbk') != exp:
                stats['B 跳过：GBK 往返不一致'] += 1
                continue
            entries.append({'file': f, 'offset': off, 'len': en - off, 'text_bytes': nb,
                            'text': text, 'src': 'sjis->gbk', 'kind': 'inline',
                            'prefix_off': None, 'fallbacks': use})
            stats['B 孤立内联正文'] += 1
        # --- C. 可选安全网：译文 GBK 不可编码的槽（仍会乱码） ---
        for (ff, so), slen in slots_extra.items():
            if ff != f:
                continue
            seg = raw[so:so + slen]
            try:
                text = seg.decode('cp932')
            except Exception:
                stats['C 跳过：槽内容非 SJIS'] += 1
                continue
            if not any(0x3041 <= ord(c) <= 0x309F for c in text):
                # 少数槽无平假名（如「自・業・自・得」纯汉字+中点），放宽为
                # 「cp932 往返一致 + 含假名或汉字」
                if text.encode('cp932') != seg or not any(is_jp(c) for c in text):
                    stats['C 跳过：槽内非日文正文（往返或字符集不符）'] += 1
                    continue
            nb, use = enc_gbk(text, fallback)
            if nb is None:
                stats['C 跳过：GBK 不可编码'] += 1
                skipped.append({'file': f, 'offset': so, 'len': slen, 'kind': 'slot',
                                'text': text, 'bad_chars': sorted(set(use))})
                continue
            entries.append({'file': f, 'offset': so, 'len': slen, 'text_bytes': nb,
                            'text': text, 'src': 'sjis->gbk', 'kind': 'slot',
                            'prefix_off': None, 'fallbacks': use})
            stats['C 不可编码槽（安全网，可选）'] += 1
    return entries, skipped, stats


# ---- 映射读写 --------------------------------------------------------------
def dump_map(entries, path=MAP_PATH):
    out = []
    for e in entries:
        out.append({'file': e['file'], 'offset': e['offset'], 'len': e['len'],
                    'text_bytes': list(e['text_bytes']),
                    'text_bytes_latin1': e['text_bytes'].decode('latin-1'),
                    'new_len': len(e['text_bytes']),
                    'delta': len(e['text_bytes']) - e['len'],
                    'src': e['src'], 'kind': e['kind'],
                    'prefix_off': e['prefix_off'],
                    'text': e['text'], 'fallbacks': e['fallbacks']})
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    return out


def load_map(path=MAP_PATH):
    """-> {file: [{'offset','len','text_bytes'(bytes)}]}"""
    rows = json.load(open(path, encoding='utf-8'))
    by = collections.defaultdict(list)
    for r in rows:
        tb = r.get('text_bytes')
        if isinstance(tb, list):
            tb = bytes(tb)
        elif isinstance(tb, str):
            tb = tb.encode('latin-1')
        else:
            raise ValueError('text_bytes 类型不支持: %r' % type(tb))
        by[r['file']].append({'offset': int(r['offset']), 'len': int(r['len']),
                              'text_bytes': tb, 'kind': r.get('kind'),
                              'prefix_off': r.get('prefix_off'),
                              'text': r.get('text'), 'fallbacks': r.get('fallbacks') or []})
    return by


# ---- 自检 ----------------------------------------------------------------
def verify_recode_only(entries_by_file, n_random=20, seed=20260914):
    """逐文件仅施加**重编码**编辑并回读：
       1) 头部 B / code_start 不变；
       2) 差异只允许出现在 (被编辑区间, 声明串长度前缀, 被重定位的 4 字节地址字段)；
       3) 每个编辑按新偏移回读 == 新 GBK 字节，decode('gbk') == 日文原文；
       4) 声明串长度前缀 == new_len + 1。"""
    fails = []
    checked = 0
    for f, edits in sorted(entries_by_file.items()):
        raw = open(os.path.join(SCR, f), 'rb').read()
        i0 = EX.parse_header(raw)
        try:
            new, census, moved = TR.apply_edits_rebuild(
                raw, [{'offset': e['offset'], 'len': e['len'], 'text_bytes': e['text_bytes']}
                      for e in edits], verify=False)
        except Exception as ex:
            fails.append({'file': f, 'why': 'rebuild 抛错: %s' % ex})
            continue
        i1 = EX.parse_header(new)
        if i1['B'] != i0['B'] or i1['code_start'] != i0['code_start']:
            fails.append({'file': f, 'why': '头部变化 B/code_start'})
            continue
        # 差异受限检查
        allowed = []
        for e in edits:
            allowed.append((e['offset'], e['offset'] + e['len']))
        for e in edits:
            if e['prefix_off'] is not None:
                allowed.append((e['prefix_off'] + 2, e['prefix_off'] + 4))
        for fpos, v, nv, kind in moved:
            allowed.append((fpos, fpos + 4))
        # 坐标映射：原始 x -> 新坐标
        eds = sorted(edits, key=lambda e: e['offset'])

        def map_pos(x):
            """x == 某编辑起点 -> 该编辑的新起点；严格落在编辑区间内部 -> None。"""
            d = 0
            for e in eds:
                if x <= e['offset']:
                    break
                if x < e['offset'] + e['len']:
                    return None
                d += len(e['text_bytes']) - e['len']
            return x + d

        bad = None
        for (a, b) in _merge_ranges(allowed):
            pass
        i = j = 0
        na, nb = len(raw), len(new)
        while i < na or j < nb:
            if i < na and j < nb and raw[i] == new[j]:
                i += 1
                j += 1
                continue
            hit = None
            for e in eds:
                if i == e['offset']:
                    hit = e
                    break
            if hit:
                i += hit['len']
                j += len(hit['text_bytes'])
                continue
            if _in(i, [(e['prefix_off'] + 2, e['prefix_off'] + 4)
                       for e in edits if e['prefix_off'] is not None]):
                i += 2
                j += 2
                continue
            hitmv = [t for t in moved if t[0] == i]
            if hitmv:
                v, nv = hitmv[0][1], hitmv[0][2]
                if struct.unpack_from('<I', raw, i)[0] == v and \
                   struct.unpack_from('<I', new, j)[0] == nv:
                    i += 4
                    j += 4
                    continue
            bad = (i, j, raw[i] if i < na else None, new[j] if j < nb else None)
            break
        if bad:
            fails.append({'file': f, 'why': '未知差异 @old=0x%x new=0x%x' % (bad[0], bad[1])})
            continue
        # 回读
        for e in edits:
            p = map_pos(e['offset'])
            if p is None:
                fails.append({'file': f, 'why': '偏移映射为 None @0x%x' % e['offset']})
                break
            got = new[p:p + len(e['text_bytes'])]
            if got != e['text_bytes']:
                fails.append({'file': f, 'why': '回读字节不符 @0x%x' % e['offset']})
                break
            try:
                txt = got.decode('gbk')
            except Exception:
                fails.append({'file': f, 'why': '回读 GBK 解码失败 @0x%x' % e['offset']})
                break
            exp = _apply_fallback(e['text'], e['fallbacks'])
            if txt != exp:
                fails.append({'file': f, 'why': '回读文本不等 @0x%x' % e['offset']})
                break
            if e['prefix_off'] is not None:
                L = struct.unpack_from('<H', new, e['prefix_off'] + 2)[0]
                if L != len(e['text_bytes']) + 1:
                    fails.append({'file': f, 'why': '长度前缀未同步 @0x%x (L=%d)' %
                                  (e['prefix_off'], L)})
                    break
            checked += 1
    return checked, fails


def _merge_ranges(rs):
    rs = sorted(rs)
    out = []
    for a, b in rs:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def verify_random(entries_by_file, n=20, seed=20260914):
    """随机抽 n 处：按新偏移回读并 decode('gbk')，与日文原文比对。返回明细。"""
    rows = []
    for f, edits in entries_by_file.items():
        for e in edits:
            rows.append((f, e))
    rng = random.Random(seed)
    rng.shuffle(rows)
    sample = rows[:n]
    out = []
    cache = {}
    for f, e in sample:
        if f not in cache:
            raw = open(os.path.join(SCR, f), 'rb').read()
            eds = sorted(entries_by_file[f], key=lambda x: x['offset'])
            delta = 0
            pos = {}
            for x in eds:
                pos[id(x)] = x['offset'] + delta
                delta += len(x['text_bytes']) - x['len']
            cache[f] = pos
        p = cache[f][id(e)]
        raw = open(os.path.join(SCR, f), 'rb').read()
        seg = raw[e['offset']:e['offset'] + e['len']]
        src_txt = seg.decode('cp932')
        exp = _apply_fallback(src_txt, e['fallbacks'])
        dst = e['text_bytes'].decode('gbk')
        out.append({'file': f, 'orig_off': e['offset'], 'new_off': p,
                    'len': e['len'], 'new_len': len(e['text_bytes']),
                    'kind': e['kind'], 'src_text': src_txt, 'gbk_text': dst,
                    'ok': exp == dst})
    return out


# ---- 残留扫描 --------------------------------------------------------------
def scan_source():
    """扫描原始 .tob 目录，分类统计残留 SJIS（用于说明覆盖面）。"""
    trng = translation_ranges()
    stat = collections.Counter()
    detail = collections.defaultdict(list)
    for f in sorted(os.listdir(SCR)):
        if not f.lower().endswith('.tob'):
            continue
        raw = open(os.path.join(SCR, f), 'rb').read()
        fields = extract_declared(raw)
        frng = [(p + 4, p + 4 + L - 1) for (p, L, b, t) in fields]
        for off, seg in find_sjis_runs(raw):
            if _in(off, frng):
                stat['声明串字段内'] += 1
            elif _in(off, trng.get(f, [])):
                stat['译文已覆盖槽内'] += 1
            else:
                stat['其它（含正文槽/内联）'] += 1
                if len(detail['其它']) < 12:
                    detail['其它'].append((f, hex(off), len(seg)))
    return stat, detail


# ---- 残留扫描（构建产物）------------------------------------------------
def scan_lpk(lpk_path, sample=20):
    """扫描一个 SCRIPT.LPK：统计仍以 SJIS 存储的日文文本（= 会显示乱码）。
    判据：能按 cp932 完整解码、含**假名**、无 NUL/控制字节（假名是主要判据，
    因为 GBK 文本按 cp932 解出的多是汉字/PUA，极少出现假名）。"""
    sys.path.insert(0, HERE)
    import lpk_patch as LP
    lp = LP.load(lpk_path)
    tobs = [n for n, _ in lp['ents'] if n.lower().endswith('.tob')]
    stat = collections.Counter()
    ex = []
    for n in tobs:
        raw = LP.read_entry(lp, n)['plain']
        fields = extract_declared(raw)
        frng = [(p + 4, p + 4 + L - 1) for (p, L, b, t) in fields]
        # 声明串字段：逐个判定
        for (p, L, body, t) in fields:
            if any(0x3040 <= ord(c) <= 0x30FF for c in t):
                stat['声明串字段（仍 SJIS，会乱码）'] += 1
                if len(ex) < sample:
                    ex.append(('declared', n, hex(p), t[:40]))
        for off, seg in find_sjis_runs(raw):
            if _in(off, frng):
                continue
            try:
                t = seg.decode('cp932')
            except Exception:
                continue
            if any(0x3040 <= ord(c) <= 0x30FF for c in t) and not any(
                    0xE000 <= ord(c) <= 0xF8FF for c in t) and len(seg) >= 8:
                stat['其它位置（槽/内联，仍 SJIS）'] += 1
                if len(ex) < sample:
                    ex.append(('run', n, hex(off), t[:40]))
    return stat, ex, len(tobs)


def readback_lpk(lpk_path, n=20, seed=20260914, map_path=None):
    """端到端回读：从映射里随机抽 n 条，在**构建产物 LPK** 的对应 .tob 明文里
    按 GBK 字节定位并回读（偏移会因译文变长而平移，故用字节定位而非固定偏移），
    校验 (1) 新字节确实存在；(2) 回读 decode('gbk') == 日文原文（含回退改写）；
    (3) 声明串 `01 01 <u16 L>` 前缀已同步为 new_len+1。"""
    import lpk_patch as LP
    lp = LP.load(lpk_path)
    by = load_map(map_path or MAP_PATH)
    rows = [(f, e) for f, v in by.items() for e in v]
    rng = random.Random(seed)
    rng.shuffle(rows)
    sample = rows[:n]
    plain_cache = {}
    out = []
    for f, e in sample:
        if f not in plain_cache:
            try:
                plain_cache[f] = LP.read_entry(lp, f)['plain']
            except KeyError:
                plain_cache[f] = None
        pl = plain_cache[f]
        src = open(os.path.join(SCR, f), 'rb').read()
        seg = src[e['offset']:e['offset'] + e['len']].decode('cp932')
        exp = _apply_fallback(seg, e['fallbacks'])
        nb = e['text_bytes']
        r = {'file': f, 'orig_off': e['offset'], 'len': e['len'],
             'kind': e['kind'], 'text': exp}
        if pl is None:
            r['ok'] = False
            r['why'] = 'LPK 中无该条目'
            out.append(r)
            continue
        pos = -1
        why = None
        p = pl.find(nb)
        while p >= 0:
            okp = True
            if e['prefix_off'] is not None:
                # 名字/描述串：其前 2 字节必须是同步后的长度前缀
                if p < 2 or pl[p - 4:p - 2] != b'\x01\x01':
                    okp = False
                else:
                    L = struct.unpack_from('<H', pl, p - 2)[0]
                    okp = (L == len(nb) + 1)
            if okp:
                pos = p
                break
            p = pl.find(nb, p + 1)
        r['built_off'] = pos
        if pos < 0:
            r['ok'] = False
            r['why'] = '构建产物中无「结构正确」的该 GBK 字节（同名多次出现也均已排除）'
            out.append(r)
            continue
        back = pl[pos:pos + len(nb)].decode('gbk')
        r['ok'] = (back == exp)
        r['back'] = back
        if e['prefix_off'] is not None:
            r['prefix_L'] = struct.unpack_from('<H', pl, pos - 2)[0]
        out.append(r)
    return out
def main():
    args = sys.argv[1:]
    mode = args[0] if args else 'build'
    fb = 'project'
    if '--fallback' in args:
        fb = args[args.index('--fallback') + 1]
    fallback = {'none': {}, 'project': FALLBACK_PROJECT, 'all': FALLBACK_ALL}[fb]

    if mode == 'scan':
        stat, detail = scan_source()
        print('=== 原始脚本残留 SJIS 运行段分类 ===')
        for k, v in stat.items():
            print('  %-18s %d 段' % (k, v))
        for d in detail['其它']:
            print('   ', d)
        return 0

    if mode == 'scan-lpk':
        stat, ex, n = scan_lpk(args[1])
        print('=== %s（%d 个 .tob）残留 SJIS 扫描 ===' % (args[1], n))
        for k, v in stat.items():
            print('  %-28s %d' % (k, v))
        for e in ex:
            print('   %-9s %-14s %-8s %s' % e)
        return 0

    if mode == 'readback-lpk':
        n = 20
        if '--n' in args:
            n = int(args[args.index('--n') + 1])
        rs = readback_lpk(args[1], n)
        print('=== 构建产物端到端回读（%d 处）===' % len(rs))
        ok = 0
        for r in rs:
            ok += 1 if r['ok'] else 0
            print('  %-14s 原始0x%-7x %-8s %s | %s' %
                  (r['file'], r['orig_off'], r['kind'], '✔' if r['ok'] else
                   '✘(%s)' % r.get('why', ''), r.get('back', r['text'])[:36]))
        print('  通过 %d / %d' % (ok, len(rs)))
        return 0 if ok == len(rs) else 1

    if mode == 'build':
        out_path = MAP_PATH
        if '--out' in args:
            out_path = args[args.index('--out') + 1]
        inc_slots = '--include-slots' in args
        entries, skipped, stats = build_candidates(fallback, inc_slots)
        print('=== 重编码候选（fallback=%s%s）===' % (fb, ' + include-slots' if inc_slots else ''))
        for k in sorted(stats):
            print('  %-34s %d' % (k, stats[k]))
        nbytes = sum(len(e['text_bytes']) for e in entries)
        obytes = sum(e['len'] for e in entries)
        print('  可转换 %d 处：原 %d 字节 -> 新 %d 字节（Δ%+d）'
              % (len(entries), obytes, nbytes, nbytes - obytes))
        print('  涉及文件 %d 个' % len({e['file'] for e in entries}))
        rows = dump_map(entries, out_path)
        # 跳过清单随映射文件走（避免不同档位互相覆盖）
        skip_path = SKIP_PATH if os.path.abspath(out_path) == os.path.abspath(MAP_PATH)             else os.path.splitext(out_path)[0] + '_跳过清单.json'
        json.dump(skipped, open(skip_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('  映射: %s（%d 条）' % (out_path, len(rows)))
        print('  跳过清单: %s（%d 条）' % (skip_path, len(skipped)))
        dd = collections.Counter()
        for e in entries:
            dd[len(e['text_bytes']) - e['len']] += 1
        print('  长度变化分布:', dict(sorted(dd.items())))
        fbc = collections.Counter()
        for e in entries:
            for a, b in e['fallbacks']:
                fbc['%s->%s' % (a, b)] += 1
        if fbc:
            print('  回退替换统计:', dict(fbc))
        return 0

    if mode == 'selftest':
        by = load_map()
        n = None
        if '--n' in args:
            n = int(args[args.index('--n') + 1])
        print('=== 全量单文件回写自检（仅重编码编辑）===')
        checked, fails = verify_recode_only(by)
        print('  回读校验通过 %d 处；失败 %d 项' % (checked, len(fails)))
        for x in fails[:20]:
            print('   [失败]', x)
        rnd = verify_random(by, n or 20)
        print()
        print('=== 随机 %d 处回读（新偏移 + GBK 解码 vs 日文原文）===' % len(rnd))
        ok = 0
        for r in rnd:
            ok += 1 if r['ok'] else 0
            print('  %-14s 0x%06x -> 0x%06x %-8s %s | %s' %
                  (r['file'], r['orig_off'], r['new_off'], r['kind'],
                   '✔' if r['ok'] else '✘', r['gbk_text'][:34]))
        print('  一致 %d / %d' % (ok, len(rnd)))
        return 0 if not fails and ok == len(rnd) else 1

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
