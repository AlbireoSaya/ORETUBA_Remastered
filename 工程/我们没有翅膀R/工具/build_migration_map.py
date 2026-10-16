# -*- coding: utf-8 -*-
r"""build_migration_map.py —— 参照汉化（原版 2009）→ R 版 的**逐槽译文迁移映射**构建器
（ISSUE-ORETUBAR-R · 译文迁移模块 · v2）

输入（全部只读）
================
1. `参照\原版汉化_逐槽字节.json` —— ref_extract_bytes.py 的字节级零损失产物（120,952 条记录）；
2. `语料\R版SCRIPT\*.tob`（418 个）—— `工具\tob_extract.py` 定位消息槽后，按 offset/len
   **切片取原始 SJIS 字节**（不经任何有损解码）。

参照汉化的结构（v2 实测）
========================
每个 `.sob` 的文本记录**分两半**：
  * 前半 = 2009 原版**日文**（旁白 + 台词；文件序 = 显示序**倒序**；台词带 `#说话人[\语音ID]$&` 前缀）
  * 后半 = **中文译文**（同形；文件序 = 显示序**正序**）
配对 = 把「前半（文件序）」与「后半（文件序的倒序）」做**语音 ID 锚定的全局对齐**
（Needleman–Wunsch，整数打分），可容忍两半的少量增删槽；无法语音锚定的槽按单调位置补齐。

匹配策略（R 版槽 → 参照译文）
============================
  ① 同场景 + 日文字节完全相同               → `src = "ref:原版汉化"`
  ② 全库唯一的日文字节完全相同（跨场景）      → `src = "ref:跨场景"`
  ③ 同场景 + 归一化近似（忽略首尾全角空格/标点差异）→ `src = "ref:近似"`（附原文/译文供人工复核）
  ④ 其余 → `语料\待翻译清单.json`

用法
====
    python -X utf8 build_migration_map.py
    python -X utf8 build_migration_map.py --quiet
"""
import json
import os
import re
import sys
import collections

PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
TOOLS = os.path.join(PROJ, '工具')
REF_JSON = os.path.join(PROJ, '参照', '原版汉化_逐槽字节.json')
R_SRC = os.path.join(PROJ, '语料', 'R版SCRIPT')
OUT_PAIRS = os.path.join(PROJ, '参照', '中日对照表.json')
OUT_MAP = os.path.join(PROJ, '语料', 'R版迁移映射.json')
OUT_TODO = os.path.join(PROJ, '语料', '待翻译清单.json')

sys.path.insert(0, TOOLS)
import tob_extract  # noqa: E402
import ref_extract_bytes as RF  # noqa: E402

REF_SRC = os.path.join(PROJ, '参照', '原版汉化SCRIPT_CHS')

KANA_FW = re.compile(r'[\u3040-\u30ff]')
KANA_HW = re.compile(r'[\uff61-\uff9f]')
HAN = re.compile(r'[\u4e00-\u9fff]')
VOICE_ID_RE = re.compile(r'^[A-Za-z0-9_]{4,16}$')

PREFIXES = ['s00', 's01', 's02', 's03c', 's03', 's04']


# ------------------------------------------------------------------ 小工具
def dec(b: bytes, enc: str):
    try:
        return b.decode(enc)
    except Exception:
        return None


def view(b: bytes, enc: str):
    """人读视图：不可解字节渲染成 \\xNN（不用 U+FFFD）。"""
    return b.decode(enc, 'backslashreplace')


def pk(v):
    """bytes → latin-1 打包 str（JSON 用）；已是 str 则原样返回。"""
    return v.decode('latin-1') if isinstance(v, bytes) else v


def ub(v):
    """latin-1 打包 str → bytes；已是 bytes 则原样返回。"""
    return v.encode('latin-1') if isinstance(v, str) else v


def voice_of(meta_b: bytes) -> str:
    """meta（= <说话人>[\\<语音ID>]）里的语音 ID；无名或无语音返回 ''。"""
    if b'\\' not in meta_b:
        return ''
    v = meta_b.rsplit(b'\\', 1)[1]
    s = dec(v, 'ascii')
    if s and VOICE_ID_RE.match(s) and any(c.isalpha() for c in s):
        return s
    return ''


def speaker_of(meta_b: bytes, enc: str) -> str:
    return dec(meta_b.split(b'\\')[0], enc) or ''


def scene_of(fname: str) -> str:
    return os.path.splitext(os.path.basename(fname))[0]


def prefix_of(scene: str) -> str:
    for p in PREFIXES:
        if scene.startswith(p):
            return p
    return '其他'


# ------------------------------------------------------------------ 归一化（近似匹配用）
_PUNCT = ('　 \t\r\n「」『』（）()“”‘’、。，．！？!?…‥―—‐-ー〜～·・：:；;／/＼\\＝=＋+＿_｜|＊*')
_NORM_MAP = {
    '〜': '~', '～': '~', '―': '-', '—': '-', '‐': '-', '－': '-',
    '…': '.', '‥': '.', '．': '.', '。': '.',
    '、': ',', '，': ',', '　': '', ' ': '',
    '！': '!', '？': '?', '「': '"', '」': '"', '『': '"', '』': '"',
    '（': '(', '）': ')', '：': ':', '；': ';',
}


def norm_jp(t: str) -> str:
    """近似匹配键：去首尾全角空格/标点 + 删内部空白 + 标点归一。"""
    t = t.strip().strip(_PUNCT)
    return ''.join(_NORM_MAP.get(c, c) for c in t)


_STRIP_ALL = set(_PUNCT)


def norm_jp2(t: str) -> str:
    """二阶归一化键：删除所有标点与空白（应对「」、。、… 等差异）。"""
    return ''.join(c for c in t if c not in _STRIP_ALL)


# ------------------------------------------------------------------ 语言判定与分界
def body_kind(b: bytes) -> str:
    """JP = 含全角假名；CN = GBK 解出 ≥2 汉字且无假名；NEU = 其余（标点/数字等）。

    用于**语言分界**判定（要求保守：宁可把短句算中性，也不要误判边界）。
    配对级的译侧判定见 `cn_side_kind`（放宽到 1 汉字，因为配对已有日文侧做锚）。
    """
    jp = dec(b, 'cp932')
    if jp and KANA_FW.search(jp):
        return 'JP'
    cn = dec(b, 'gbk')
    if cn and not KANA_FW.search(cn) and len(HAN.findall(cn)) >= 2:
        return 'CN'
    return 'NEU'


def cn_side_kind(b: bytes) -> str:
    """配对级：判定**译文侧**字节的语种（锚定日文侧之后使用）。

    * 解出全角假名            → `JP`（该槽参照汉化未译，仍是日文）
    * GBK 可解且无假名        → 有汉字则 `CN`，纯标点/拉丁/数字则 `NEU`（照样可迁移）
    * 其余                    → `UNK`
    """
    jp = dec(b, 'cp932')
    if jp and KANA_FW.search(jp):
        return 'JP'
    cn = dec(b, 'gbk')
    if cn is None:
        return 'UNK'
    if KANA_FW.search(cn) or KANA_HW.search(cn):
        return 'UNK'
    return 'CN' if HAN.search(cn) else 'NEU'


def split_point(kinds):
    """前半=日文/后半=中文 的最优切点（违例最少，平手取靠中）。"""
    n = len(kinds)
    best = None
    for k in range(1, n):
        v = sum(1 for x in kinds[:k] if x == 'CN') + sum(1 for x in kinds[k:] if x == 'JP')
        key = (v, abs(k - n // 2))
        if best is None or key < best[0]:
            best = (key, k)
    return best[1] if best else n // 2


# ------------------------------------------------------------------ 全局对齐
def dp_align(A, B):
    """Needleman–Wunsch（整数打分）。A/B = 显示序上的语音 ID 序列（'' = 无语音）。"""
    n, m = len(A), len(B)
    GAP = -2

    def sc(a, b):
        if a and b:
            return 4 if a == b else -4
        if not a and not b:
            return 1
        return -1

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + GAP
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + GAP
    for i in range(1, n + 1):
        ai = A[i - 1]
        row, prev = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            v = prev[j - 1] + sc(ai, B[j - 1])
            u = prev[j] + GAP
            w = row[j - 1] + GAP
            row[j] = v if v >= u and v >= w else (u if u >= w else w)
    i, j = n, m
    out = []
    while i > 0 and j > 0:
        if dp[i][j] == dp[i - 1][j - 1] + sc(A[i - 1], B[j - 1]):
            out.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + GAP:
            i -= 1
        else:
            j -= 1
    out.reverse()
    return out


# ------------------------------------------------------------------ 参照侧：配对
def prep(ref_slots):
    for s in ref_slots:
        for k in ('head_b', 'meta_b', 'speaker_b', 'voice_b', 'body_b', 'tail_b'):
            if k in s:
                s[k] = ub(s[k])
        s['body_bytes'] = s['body_b']
    return ref_slots


def build_pairs(ref_slots):
    by_scene = collections.OrderedDict()
    for s in ref_slots:
        by_scene.setdefault(s['scene'], []).append(s)
    pairs = []
    stats = collections.Counter()
    for scene, slots in by_scene.items():
        n = len(slots)
        if n < 4:
            stats['跳过_记录<4文件'] += 1
            continue
        kinds = [body_kind(s['body_bytes']) for s in slots]
        k = split_point(kinds)
        stats['分界违例_' + ('0' if True else '')] += 0
        viol = sum(1 for x in kinds[:k] if x == 'CN') + sum(1 for x in kinds[k:] if x == 'JP')
        if viol:
            stats['分界违例槽'] += viol
            stats['分界违例文件'] += 1
        jp_side = slots[:k]
        cn_side = slots[k:]
        # 显示序：JP 前半文件序即显示序倒序；CN 后半文件序即显示序正序 → 倒过来对齐
        A = [voice_of(s['meta_b']) for s in jp_side]
        B = [voice_of(s['meta_b']) for s in reversed(cn_side)]
        al = dp_align(A, B)
        used = set()
        for (i, j) in al:
            jp_slot = jp_side[i]
            cn_slot = list(reversed(cn_side))[j]
            used.add(i)
            jb, cb = jp_slot['body_bytes'], cn_slot['body_bytes']
            jk = kinds[i]
            vj, vc = voice_of(jp_slot['meta_b']), voice_of(cn_slot['meta_b'])
            # 配对级语种：以 JP 侧为锚；JP 侧本身语言中性（纯标点）时整对记为 NEU
            if jk == 'NEU':
                kind = 'NEU'
            else:
                kind = cn_side_kind(cb)
            stats['配对_' + kind] += 1
            if vj and vc:
                stats['语音一致' if vj == vc else '语音不一致'] += 1
            pairs.append({
                'scene': scene,
                'jp_index': jp_slot['index'],
                'cn_index': cn_slot['index'],
                'speaker_b': pk(jp_slot['speaker_b']),
                'voice_b': pk(jp_slot['voice_b']),
                'speaker': speaker_of(jp_slot['meta_b'], 'cp932'),
                'voice': vj,
                'speaker_cn': speaker_of(cn_slot['meta_b'], 'gbk'),
                'voice_cn': vc,
                'jp': jp_slot['jp_view'],
                'cn': (dec(cb, 'gbk') if dec(cb, 'gbk') is not None else view(cb, 'gbk')),
                'jp_b': pk(jb),
                'cn_b': pk(cb),
                'cn_kind': kind,
                'voice_match': bool(vj and vc and vj == vc),
                'ref_offset': jp_slot['offset'],
                'ref_cn_offset': cn_slot['offset'],
                'jp_bytes': jb,
                'cn_bytes': cb,
            })
        missed = k - len(used)
        if missed:
            stats['前半未配上的记录'] += missed
    return pairs, stats


def build_indexes(pairs):
    scene_idx = collections.defaultdict(list)
    norm_idx = collections.defaultdict(list)
    norm2_idx = collections.defaultdict(list)
    global_idx = collections.defaultdict(list)
    for p in pairs:
        if p['cn_kind'] not in ('CN', 'NEU'):
            continue
        jb = p['jp_bytes']
        if not jb:
            continue
        scene_idx[(p['scene'], jb)].append(p)
        global_idx[jb].append(p)
        nj = norm_jp(p['jp'])
        if len(nj) >= 6:
            norm_idx[(p['scene'], nj)].append(p)
        nj2 = norm_jp2(p['jp'])
        if len(nj2) >= 8:
            norm2_idx[(p['scene'], nj2)].append(p)
    return scene_idx, norm_idx, norm2_idx, global_idx


def pick(entries):
    """候选里选唯一解：全部 cn 字节一致才可用。"""
    if not entries:
        return None, 'none'
    if len(entries) == 1:
        return entries[0], 'unique'
    if len({e['cn_bytes'] for e in entries}) == 1:
        return entries[0], 'dup-consistent'
    return None, 'ambiguous'


# ------------------------------------------------------------------ 章节标题（NUL 终止串）
def _find_title_cn(data: bytes, jb: bytes):
    """在参照 .sob 里按 NUL 终止串找 JP 标题，并取其后的第一个 GBK 汉字串为译文。"""
    off = data.find(b'\x00' + jb + b'\x00')
    if off < 0:
        return None
    off += 1
    tail = data[off + len(jb):off + len(jb) + 400]
    for m in RF.RUN.finditer(tail):
        seg = m.group(0)
        if m.start() and tail[m.start() - 1] != 0x00:
            continue
        if m.end() < len(tail) and tail[m.end()] != 0x00:
            continue
        cn = dec(seg, 'gbk')
        if cn and len(HAN.findall(cn)) >= 2 and not KANA_FW.search(cn):
            return seg
    return None


def resolve_titles(r_rows, todo):
    """给未命中的**章节标题**槽（kind=title）补译文：同场景 .sob 优先，再全库。"""
    cache = {}
    got = 0
    for e in todo:
        if e.get('kind') != 'title':
            continue
        jb = ub(e['text_b'])
        scene = scene_of(e['file'])
        cands = [scene]
        for sc in cands:
            p = os.path.join(REF_SRC, sc + '.sob')
            if not os.path.exists(p):
                continue
            if sc not in cache:
                with open(p, 'rb') as fp:
                    cache[sc] = fp.read()
            cn = _find_title_cn(cache[sc], jb)
            if cn:
                e['cn'] = dec(cn, 'gbk')
                e['cn_b'] = pk(cn)
                e['src'] = 'ref:标题串'
                e['ref_scene'] = sc
                got += 1
                break
    return got


# ------------------------------------------------------------------ R 侧：读取
def load_r_slots():
    files = sorted(f for f in os.listdir(R_SRC) if f.lower().endswith('.tob'))
    rows = []
    warns = 0
    for f in files:
        p = os.path.join(R_SRC, f)
        info, msgs, ws = tob_extract.parse_messages(p)
        warns += len(ws)
        with open(p, 'rb') as fp:
            data = fp.read()
        for m in msgs:
            off, ln = m.get('offset'), m.get('len')
            raw = data[off:off + ln] if (off is not None and ln) else b''
            rows.append({
                'file': f,
                'scene': scene_of(f),
                'index': m['index'],
                'offset': off,
                'len': ln,
                'op': m.get('op'),
                'speaker': m.get('speaker') or '',
                'voice': m.get('voice') or '',
                'kind': m.get('kind') or ('dialogue' if m.get('op') == 0x19 else 'narration'),
                'extra': bool(m.get('extra')),
                'text_b': raw,
                'text': dec(raw, 'cp932') if raw else '',
            })
    return rows, warns


# ------------------------------------------------------------------ 主流程
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    quiet = '--quiet' in sys.argv
    out = []

    def P(*a):
        s = ' '.join(str(x) for x in a)
        out.append(s)
        if not quiet:
            print(s)

    # ---- 1. 参照侧配对
    with open(REF_JSON, encoding='utf-8') as fp:
        ref = json.load(fp)
    ref_slots = prep(ref['slots'])
    P('== 参照汉化（原版 2009）==')
    P('逐槽字节 JSON: 记录 %d / 文件 %d（自述 %d）'
      % (len(ref_slots), len(ref['source_file_md5']), ref['slot_count']))
    pairs, pstat = build_pairs(ref_slots)
    P('配对总数: %d' % len(pairs))
    P('  配对语种: ' + '；'.join('%s=%d' % (k.split('_')[1], v)
                              for k, v in sorted(pstat.items()) if k.startswith('配对_')))
    P('  语音校验: 一致 %d / 不一致 %d （%.3f%% 一致）'
      % (pstat['语音一致'], pstat['语音不一致'],
         100.0 * pstat['语音一致'] / max(1, pstat['语音一致'] + pstat['语音不一致'])))
    P('  语言分界违例: %d 槽 / %d 文件（共 %d 文件）'
      % (pstat['分界违例槽'], pstat['分界违例文件'], len(ref['source_file_md5'])))
    if pstat['前半未配上的记录']:
        P('  前半未配上（对齐空位）: %d' % pstat['前半未配上的记录'])
    P('可迁移对照: CN 对 %d ；NEU 对 %d ；JP 残留对 %d ；UNK %d'
      % (sum(1 for p in pairs if p['cn_kind'] == 'CN'),
         sum(1 for p in pairs if p['cn_kind'] == 'NEU'),
         sum(1 for p in pairs if p['cn_kind'] == 'JP'),
         sum(1 for p in pairs if p['cn_kind'] == 'UNK')))

    # ---- 2. 写 中日对照表.json
    table = [{
        'scene': p['scene'],
        'speaker_b': p['speaker_b'],
        'voice_b': p['voice_b'],
        'speaker': p['speaker'],
        'speaker_cn': p['speaker_cn'],
        'voice': p['voice'],
        'jp': p['jp'],
        'cn': p['cn'],
        'jp_b': p['jp_b'],
        'cn_b': p['cn_b'],
        'cn_kind': p['cn_kind'],
        'voice_match': p['voice_match'],
        'jp_index': p['jp_index'],
        'cn_index': p['cn_index'],
        'ref_offset': p['ref_offset'],
        'ref_cn_offset': p['ref_cn_offset'],
        'ref_file': '原版汉化SCRIPT_CHS/%s.sob' % p['scene'],
    } for p in pairs]
    with open(OUT_PAIRS, 'w', encoding='utf-8') as fp:
        json.dump(table, fp, ensure_ascii=False)
    P('写出 参照\\中日对照表.json: %d 条 (%.1f MB)'
      % (len(table), os.path.getsize(OUT_PAIRS) / 1048576.0))

    # ---- 3. 索引
    scene_idx, norm_idx, norm2_idx, global_idx = build_indexes(pairs)
    amb = sum(1 for v in scene_idx.values() if len({e['cn_bytes'] for e in v}) > 1)
    P('索引: 同场景键 %d（歧义 %d）; 全库键 %d; 一阶归一化键 %d; 二阶归一化键 %d'
      % (len(scene_idx), amb, len(global_idx), len(norm_idx), len(norm2_idx)))

    # ---- 4. R 版槽
    r_rows, r_warns = load_r_slots()
    P('== R 版剧情脚本 ==')
    P('槽总数: %d （结构警告 %d）' % (len(r_rows), r_warns))

    # ---- 5. 匹配
    mapping = []
    todo = []
    stat = collections.Counter()
    char_all = collections.Counter()
    char_hit = collections.Counter()
    voice_ok = speaker_ok = voice_cmp = speaker_cmp = 0
    near_examples = []
    amb_examples = []
    r_empty = 0
    for r in r_rows:
        rb = r['text_b']
        scene = r['scene']
        pf = prefix_of(scene)
        if not rb:
            r_empty += 1
            continue
        nchar = len(r['text']) if r['text'] else len(view(rb, 'cp932'))
        char_all[pf] += nchar
        char_all['ALL'] += nchar
        ent = src_tag = None
        e, why = pick(scene_idx.get((scene, rb), []))
        if e:
            ent, src_tag = e, 'ref:原版汉化'
            stat['命中_同场景'] += 1
        else:
            if why == 'ambiguous':
                stat['歧义_同场景'] += 1
                if len(amb_examples) < 8:
                    amb_examples.append(scene)
            ent2, why2 = pick(global_idx.get(rb, []))
            if ent2:
                ent, src_tag = ent2, 'ref:跨场景'
                stat['命中_跨场景'] += 1
            else:
                nj = norm_jp(r['text'] or view(rb, 'cp932'))
                if len(nj) >= 6:
                    e3, _ = pick(norm_idx.get((scene, nj), []))
                    if e3:
                        ent, src_tag = e3, 'ref:近似'
                        stat['命中_近似'] += 1
                        if len(near_examples) < 12:
                            near_examples.append((scene, r['index'], r['text'], e3['jp'], e3['cn']))
                if ent is None:
                    nj2 = norm_jp2(r['text'] or view(rb, 'cp932'))
                    if len(nj2) >= 8:
                        e4, _ = pick(norm2_idx.get((scene, nj2), []))
                        if e4:
                            ent, src_tag = e4, 'ref:近似'
                            stat['命中_近似二阶'] += 1
                            if len(near_examples) < 12:
                                near_examples.append((scene, r['index'], r['text'], e4['jp'], e4['cn']))
        if ent:
            char_hit[pf] += nchar
            char_hit['ALL'] += nchar
            if r['voice'] and ent['voice']:
                voice_cmp += 1
                voice_ok += 1 if r['voice'] == ent['voice'] else 0
            if r['speaker'] and ent['speaker']:
                speaker_cmp += 1
                speaker_ok += 1 if r['speaker'] == ent['speaker'] else 0
            mapping.append({
                'file': r['file'], 'index': r['index'], 'offset': r['offset'], 'len': r['len'],
                'cn': ent['cn'], 'cn_b': ent['cn_b'], 'src': src_tag,
                'ref_scene': ent['scene'], 'ref_offset': ent['ref_offset'],
                'ref_cn_offset': ent['ref_cn_offset'],
                'jp': r['text'], 'jp_b': pk(r['text_b']),
                'speaker': r['speaker'], 'voice': r['voice'], 'kind': r['kind'],
                'cn_kind': ent['cn_kind'],
                'voice_ok': (r['voice'] == ent['voice']) if (r['voice'] and ent['voice']) else None,
                'speaker_ok': (r['speaker'] == ent['speaker']) if (r['speaker'] and ent['speaker']) else None,
            })
            if src_tag == 'ref:近似':
                mapping[-1]['ref_jp'] = ent['jp']
                mapping[-1]['ref_cn'] = ent['cn']
        else:
            stat['未命中_' + pf] += 1
            entry = {
                'file': r['file'], 'index': r['index'], 'offset': r['offset'], 'len': r['len'],
                'speaker': r['speaker'], 'voice': r['voice'],
                'text': r['text'] if r['text'] else view(rb, 'cp932'),
                'text_b': pk(r['text_b']), 'kind': r['kind'], 'op': r['op'],
            }
            # 参照里其实有同日文字节、但译文不唯一（歧义）时，附候选供人工复核
            cands = scene_idx.get((scene, rb)) or global_idx.get(rb)
            if cands and len({c['cn_bytes'] for c in cands}) > 1:
                seen_cn = set()
                uniq = []
                for c in cands:
                    if c['cn_bytes'] in seen_cn:
                        continue
                    seen_cn.add(c['cn_bytes'])
                    uniq.append(c)
                entry['ref_candidates'] = [
                    {'scene': c['scene'], 'cn': c['cn'], 'ref_offset': c['ref_offset']}
                    for c in uniq[:3]
                ]
                stat['未命中_附参照候选'] += 1
            todo.append(entry)

    # ---- 5b. 章节标题补扫（NUL 终止串路径）
    got_titles = resolve_titles(r_rows, todo)
    promoted = [e for e in todo if e.get('src') == 'ref:标题串']
    if promoted:
        todo = [e for e in todo if e.get('src') != 'ref:标题串']
        for e in promoted:
            nchar = len(e['text'])
            pf = prefix_of(scene_of(e['file']))
            char_hit[pf] += nchar
            char_hit['ALL'] += nchar
            stat['命中_标题串'] += 1
            mapping.append({
                'file': e['file'], 'index': e['index'], 'offset': e['offset'], 'len': e['len'],
                'cn': e['cn'], 'cn_b': e['cn_b'], 'src': 'ref:标题串',
                'ref_scene': e['ref_scene'], 'ref_offset': None, 'ref_cn_offset': None,
                'jp': e['text'], 'jp_b': e['jp_b'] if 'jp_b' in e else e['text_b'],
                'speaker': e['speaker'], 'voice': e['voice'], 'kind': e['kind'],
                'cn_kind': 'CN', 'voice_ok': None, 'speaker_ok': None,
            })

    # ---- 6. 写映射与清单
    with open(OUT_MAP, 'w', encoding='utf-8') as fp:
        json.dump(mapping, fp, ensure_ascii=False)
    with open(OUT_TODO, 'w', encoding='utf-8') as fp:
        json.dump(todo, fp, ensure_ascii=False)
    P('写出 语料\\R版迁移映射.json: %d 条 (%.1f MB)'
      % (len(mapping), os.path.getsize(OUT_MAP) / 1048576.0))
    P('写出 语料\\待翻译清单.json: %d 条 (%.1f MB)'
      % (len(todo), os.path.getsize(OUT_TODO) / 1048576.0))

    # ---- 7. 统计
    n_all = len(mapping) + len(todo)
    P('')
    P('== 命中率 ==')
    P('槽数口径: %d / %d = %.2f%% （未命中 %d；结构槽 %d）'
      % (len(mapping), n_all, 100.0 * len(mapping) / n_all, len(todo), r_empty))
    P('  其中 同场景 %d ；跨场景 %d ；近似一阶 %d ；近似二阶 %d ；章节标题串 %d'
      % (stat['命中_同场景'], stat['命中_跨场景'], stat['命中_近似'], stat['命中_近似二阶'],
         stat['命中_标题串']))
    P('字符口径: %d / %d = %.2f%%'
      % (char_hit['ALL'], char_all['ALL'], 100.0 * char_hit['ALL'] / char_all['ALL']))
    if voice_cmp:
        P('独立校验（命中槽中可比对者）: voice 一致 %.2f%% (%d/%d)'
          % (100.0 * voice_ok / voice_cmp, voice_ok, voice_cmp))
    if speaker_cmp:
        P('                            speaker 一致 %.2f%% (%d/%d)'
          % (100.0 * speaker_ok / speaker_cmp, speaker_ok, speaker_cmp))
    P('')
    P('== 未命中分布（按场景前缀）==')
    P('%-6s %8s %8s %9s   %s' % ('前缀', '未命中槽', '总槽', '未命中率', '未命中字符/总字符'))
    for pf in PREFIXES + ['其他']:
        tot = sum(1 for r in r_rows if prefix_of(r['scene']) == pf and r['text_b'])
        if not tot:
            continue
        miss = stat['未命中_' + pf]
        P('%-6s %8d %8d %8.2f%%   %d/%d' % (
            pf, miss, tot, 100.0 * miss / tot, char_all[pf] - char_hit[pf], char_all[pf]))
    P('')
    P('== 未命中最多的场景（前 20）==')
    cnt = collections.Counter(t['file'] for t in todo)
    for f, c in cnt.most_common(20):
        P('   %-18s %d' % (f, c))
    P('未命中中「参照存在同字节日文键但译文不唯一」者（已附 ref_candidates 候选）: %d'
      % stat['未命中_附参照候选'])
    # 未命中的 kind / src 细分供翻译阶段排期
    P('未命中 kind 分布: %s' % dict(collections.Counter(t['kind'] for t in todo)))
    if near_examples:
        P('')
        P('== 近似命中样例（供人工复核）==')
        for sc, idx, jp_r, jp, cn in near_examples:
            P('   %s#%s' % (sc, idx))
            P('     R 版原文 : %s' % (jp_r or '')[:64])
            P('     参照原文 : %s' % jp[:64])
            P('     参照译文 : %s' % cn[:64])
    if amb_examples:
        P('')
        P('== 同场景歧义键（同字节不同译文，已跳过精确命中）样例 ==')
        for sc in amb_examples:
            P('   %s' % sc)
    log = os.path.join(os.path.dirname(OUT_MAP), 'migration_log.txt')
    with open(log, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(out))
    P('')
    P('统计文本已写入: %s' % log)
    return 0


if __name__ == '__main__':
    sys.exit(main())
