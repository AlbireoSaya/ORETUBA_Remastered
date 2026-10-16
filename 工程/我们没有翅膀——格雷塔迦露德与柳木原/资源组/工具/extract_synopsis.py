# -*- coding: utf-8 -*-
r"""已游玩章节简介的三源抽取（ot / otr / otv）。

用途与口径
----------
抽取《我们没有翅膀——格雷塔迦露德与柳木原》（krkr 自建重构）所需的「章节简介」原文，
分三源各出一份原始 TSV（LF / 制表符 / UTF-8 无 BOM）：

  ot   本篇 Lucifen SOB0  —— `<MAIN>/我们没有翅膀/解包/SCRIPT/<script>.sob`
       简介 = 字符串池里 `ScSkip\0` 之后（**跳过连续 NUL**）的 NUL 终止 SJIS 串；
       另用「脚本名 + jp 逐字一致」从 `scene_ot.jsonl` 取我方中文译文
       （亚衣线 s03c 不在 scene_ot，改取 `scene_otr.jsonl` 的场景号 +
        本篇汉化语料 `汉化/剧情汉化/<script>.sob.jsonl` 的 cn，理由见 README）。
  otr  R 版 Lucifen TOB0  —— `<MAIN>/我们没有翅膀R/语料/R版SCRIPT/<script>.tob`
       简介 = 文件开头的声明串 `01 01 <u16 L> <SJIS>`（结构见
       `.zcode/skills/lucifen-unpack/SKILL.md` §三「声明串」；L = 内容字节数 + 1，
       末字节必须 0x00；长度是**硬约束**，不得变长重建）。
       定位判据：简介声明串之前紧邻 **30 字节 skip 结构**
       `01 02 d2 02 00*6 01 02 d0 02 00*6 01 02 d1 02 00*6`（实测 417/418 个 `.tob` 命中；
       仅 `s00_00` 无 ⇒ 该文件无简介）。文件名开头通常是**成对**声明串
       「场景标题 + 场景简介」，紧邻其前的那条记入 `前置标题jp` 列
       （实测 391/417 与 `scene_*.jsonl` 的 `title_jp` 逐字相同，其余多为 R 版加写 `Ｒ`/改写）。
       ⚠ **不要用「40 < L < 2000」这类长度启发式**：实测 20+ 个脚本的**标题**本身 ≥40 字节
       （例 `黄金の鷹伝説八十五章～ツヴァイ砦の攻防～` L=41），会误取标题。
       **扫描必须逐字节**（含重叠）——`re.finditer(rb'\x01\x01..')` 会漏掉
       `…01 01 01 1b 00 <串>` 这种「前导 0x01 紧邻标记」的落点；本工程旧实现
       （`工程/我们没有翅膀R/工具/desc_migrate.py` 的 `first_desc()`，窗口仅 2000 字节）
       实测只取到 370/418，漏 48 个文件（含 s03c_01d1、s04_06k——二者的简介确实存在，
       可用 `--crosscheck-otr-psv` 与 PSV 简介比对自证）。
  otv  PSV 明文 DSL       —— `<MAIN>/我们没有翅膀PSV/脚本解包/<SCRIPT>`
       简介 = `:Tasktype "SceneJumpDialog"` 任务块内的 `:Text "…"`；
       并与本工程既有库（`我们没有翅膀PSV/汉化/台词对照.json` 的「梗概」27 条 +
       `scene_otv.jsonl` 的 `kind=="summary"` 27 条）逐条对齐，标「是否已在我方库」。

输入一律**只读**；输出一律落在本 issue 工作树内（硬校验，见 `_guard_out`）。

用法
----
  export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"   # 本脚本不用第三方库，仅保持一致
  cd "E:/ZCode Workspace/Galgame/临时/wt-syn"
  python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/extract_synopsis.py"

  # 路径全部可参数化：
  python extract_synopsis.py --main <MAIN工程目录> --out <输出目录> [--sources ot,otr,otv]

  # 负向自证（故意把输入指错 / 把输出拼出工作树，确认报错而非静默产出空表）：
  python extract_synopsis.py --neg-selftest

幂等：同一输入重复运行产出逐字节相同的文件（脚本内自带幂等自证）。
"""
import argparse
import collections
import hashlib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------- 默认真实路径
_HERE = os.path.dirname(os.path.abspath(__file__))            # <WT>/资源组/工具
_RES_ROOT = os.path.dirname(_HERE)                            # <WT>/资源组
_WT_ROOT = os.path.dirname(os.path.dirname(_RES_ROOT))        # <WT>（临时/wt-syn 工作树根）
_WORKSPACE_ROOT = r'E:/ZCode Workspace/Galgame'               # AGENTS 铁律 1 的写入边界

DEFAULT_MAIN = r'E:/ZCode Workspace/Galgame/工程'             # 主工作区只读源
DEFAULT_OUT = os.path.join(_RES_ROOT, '剧本', '简介')

BS = chr(0x5C)  # 反斜杠（PSV 脚本里 `\n` 是**字面的反斜杠 + n**，不是真换行）


# ---------------------------------------------------------------- 守卫与工具
def _guard_out(path, root):
    """硬校验：输出路径必须落在 root 之内（禁止 `..` 逃逸出工作树）。

    本工程有前例：os.path.join(main, "..") 会指到工作区外，必须 fail loud。
    """
    rp = os.path.realpath(path)
    rr = os.path.realpath(root)
    if not (rp == rr or rp.startswith(rr + os.sep)):
        raise SystemExit('[FATAL] 输出路径越界：%s\n        必须落在 %s 之内（禁止 .. 逃逸）'
                         % (rp, rr))
    wr = os.path.realpath(_WORKSPACE_ROOT)
    if not (rp == wr or rp.startswith(wr + os.sep)):
        raise SystemExit('[FATAL] 输出路径落在工作区之外：%s' % rp)
    return rp


def _require_dir(path, what):
    if not os.path.isdir(path):
        raise SystemExit('[FATAL] %s 不存在或不是目录：%s' % (what, path))
    return path


def _require_file(path, what):
    if not os.path.isfile(path):
        raise SystemExit('[FATAL] %s 不存在：%s' % (what, path))
    return path


def _md5(b):
    return hashlib.md5(b).hexdigest()


def _norm_for_align(s):
    """对齐用归一化：字面 `\\n` → 真换行，再删去所有空白。

    原因：PSV 脚本 `:Text` 用**字面** `\\n`（反斜杠 + n）表示换行，我方库
    （台词对照.json / scene_otv.jsonl）用**真换行**且折行位置不同 ⇒ 必须去空白后比。
    """
    return re.sub(r'\s+', '', s.replace(BS + 'n', '\n'))


def _cell(s):
    """单元格转义：制表符与真换行会破坏 TSV，统一转成字面 `\\t` / `\\n`。"""
    return (s.replace('\t', BS + 't').replace('\r\n', BS + 'n')
             .replace('\n', BS + 'n').replace('\r', BS + 'n'))


# ================================================================ 源 1：ot
def parse_ot(main):
    """本篇 SOB0：`ScSkip\\0`（跳过连续 NUL）之后的 NUL 终止 SJIS 串 = 简介。"""
    script_dir = _require_dir(os.path.join(main, '我们没有翅膀', '解包', 'SCRIPT'),
                              'ot 脚本目录')
    ot_jsonl = _require_file(os.path.join(main, '我们没有翅膀——格雷塔迦露德与柳木原',
                                          '资源组', '剧本', 'scene_ot.jsonl'),
                             'scene_ot.jsonl')
    scenes, jp2cn = {}, {}
    with open(ot_jsonl, encoding='utf-8') as fh:
        for ln in fh:
            if not ln.strip():
                continue
            o = json.loads(ln)
            scenes[o['script']] = o['scene_id']
            for l in o['lines']:
                jp2cn.setdefault((o['script'], l['jp']), l['cn'])
    # 亚衣线 s03c 不在 scene_ot（由 scene_otr 覆盖，见作品skill §四）；
    # cn 取「本篇汉化语料」——即 schema.md §3.2.0 里 cn_base=`ot` 的原始语料。
    otr_jsonl = os.path.join(main, '我们没有翅膀——格雷塔迦露德与柳木原',
                             '资源组', '剧本', 'scene_otr.jsonl')
    otr_scenes = {}
    if os.path.isfile(otr_jsonl):
        with open(otr_jsonl, encoding='utf-8') as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                o = json.loads(ln)
                otr_scenes[o['script']] = o['scene_id']
    cn_dir = os.path.join(main, '我们没有翅膀', '汉化', '剧情汉化')

    files = sorted(f for f in os.listdir(script_dir) if f.lower().endswith('.sob'))
    rows, no_marker, anomalies = [], [], []
    for fn in files:
        script = fn[:-4]
        raw = open(os.path.join(script_dir, fn), 'rb').read()
        got = []
        for m in re.finditer(rb'ScSkip\x00', raw):
            off = m.end()
            # 跳过连续 NUL：s00_00 的形态是 `ScSkip\0\0<序文串>`
            while off < len(raw) and raw[off] == 0:
                off += 1
            end = raw.find(b'\x00', off)
            if end < 0:
                end = len(raw)
            try:
                s = raw[off:end].decode('cp932')
            except UnicodeDecodeError:
                anomalies.append('%s: ScSkip 后串非 cp932（offset %d）' % (script, off))
                continue
            # 丢弃 `ScSkip\0ScSkip\0<简介>` 的重复标记（s01_12b / s01_13b）
            if s and s != 'ScSkip':
                got.append((m.start(), off, s))
        if not got:
            no_marker.append(script)
            continue
        if len(got) > 1:
            anomalies.append('%s: ScSkip 处 %d 个候选（%s）'
                             % (script, len(got), [x[2][:12] for x in got]))
        mk, content_off, jp = got[0]

        kind, note = '简介', ''
        if not jp.startswith('\u3000'):
            if script == 's00_00':
                kind = '标题型'
                note = 'ScSkip 后为序文标题（%d 字），非剧情简介' % len(jp)
            else:
                kind = '简介（首行为小标题）'
                note = '首行为「%s」小标题，其后为简介正文' % jp.split('\n')[0]

        scene_id = scenes.get(script, '')
        cn = jp2cn.get((script, jp), '')
        if not scene_id and script.startswith('s03c'):
            scene_id = otr_scenes.get(script, '')
            cp = os.path.join(cn_dir, script + '.sob.jsonl')
            if os.path.isfile(cp):
                with open(cp, encoding='utf-8') as fh:
                    for ln in fh:
                        if not ln.strip():
                            continue
                        o = json.loads(ln)
                        if o['jp'] == jp and o.get('cn'):
                            cn = o['cn']
                            break
            note = ('scene_ot 无此脚本（亚衣线由 scene_otr.jsonl 覆盖）；cn 取自本篇汉化语料 '
                    '剧情汉化/%s.sob.jsonl（schema.md §3.2.0 的 cn_base=`ot` 原语料）' % script)
        rows.append(dict(script=script, scene_id=scene_id, jp=jp, cn=cn, chars=len(jp),
                         offset=mk, md5=_md5(jp.encode('cp932')), kind=kind, note=note))
    stats = dict(sob_files=len(files), rows=len(rows), no_marker=no_marker,
                 anomalies=anomalies, cn_empty=[r['script'] for r in rows if not r['cn']],
                 kinds=_count(rows, 'kind'),
                 s03c_rows=[r['script'] for r in rows if r['script'].startswith('s03c')])
    return rows, stats


# ================================================================ 源 2：otr
# 简介声明串前紧邻的 30 字节 skip 结构（三段 × 10 字节；实测 417/418 个 .tob 命中）
SKIP_SIG = bytes.fromhex('0102d202' + '00' * 6 + '0102d002' + '00' * 6 + '0102d102' + '00' * 6)


def _decl_at(raw, i):
    """raw[i:] 处是否为声明串 `01 01 <u16 L> <内容><0x00>`，是则返回 (content_off, L, text)。"""
    n = len(raw)
    if i + 4 > n or raw[i] != 0x01 or raw[i + 1] != 0x01:
        return None
    L = int.from_bytes(raw[i + 2:i + 4], 'little')
    end = i + 3 + L                       # 末字节（NUL）的下标
    if L < 2 or end >= n or raw[end] != 0x00:
        return None
    try:
        t = raw[i + 4:end].decode('cp932')
    except UnicodeDecodeError:
        return None
    return i + 4, L, t


def _scan_decls(raw, max_off=8192, limit=8):
    """逐字节扫描文件开头的声明串（**含重叠**；`01 01 01 1b 00 <串>` 必须命中）。"""
    out = []
    for i in range(0, min(max_off, len(raw) - 5)):
        d = _decl_at(raw, i)
        if d:
            out.append((i, d[1], d[2]))
            if len(out) >= limit:
                break
    return out


def parse_otr(main):
    """R 版 TOB0：简介 = 紧跟在 30 字节 `skip` 结构之后的声明串。

    判据（**结构化，非长度启发式**）：声明串 `01 01 <u16 L> <SJIS> <0x00>` 之前
    紧邻 30 字节固定结构 `01 02 d2 02 00…00 01 02 d0 02 00…00 01 02 d1 02 00…00`
    （每段 10 字节，实测 415 + 2 = 417 个 `.tob` 命中；`s00_00` 无）。
    **该判据已用 PSV `SceneJumpDialog :Text` 作独立金标验证**：417 个可比文件中
    404 个与 PSV 简介逐字一致（去空白），13 个为版本差异（如 R 版 `<<…>>` vs PSV `≪…≫`）。
    只按「40 < L < 2000」的长度启发式会误取长标题（实测 20+ 个脚本的标题本身 ≥40 字节，
    例 `黄金の鷹伝説八十五章～ツヴァイ砦の攻防～`）。
    """
    tob_dir = _require_dir(os.path.join(main, '我们没有翅膀R', '语料', 'R版SCRIPT'),
                           'otr 脚本目录')
    titles = {}
    for jn in ('scene_ot.jsonl', 'scene_otr.jsonl'):
        jp = os.path.join(main, '我们没有翅膀——格雷塔迦露德与柳木原', '资源组', '剧本', jn)
        if os.path.isfile(jp):
            with open(jp, encoding='utf-8') as fh:
                for ln in fh:
                    if ln.strip():
                        o = json.loads(ln)
                        titles.setdefault(o['script'], o.get('title_jp'))
    files = sorted(f for f in os.listdir(tob_dir) if f.lower().endswith('.tob'))
    rows, anomalies, prev_eq, dup_files = [], [], 0, []
    for fn in files:
        script = fn[:-4]
        raw = open(os.path.join(tob_dir, fn), 'rb').read()
        decls = _scan_decls(raw, max_off=20000, limit=40)
        marked = [d for d in decls
                  if d[0] >= len(SKIP_SIG) and raw[d[0] - len(SKIP_SIG):d[0]] == SKIP_SIG]
        if not marked:
            title = [d for d in decls if d[2].strip()]
            if not title:
                anomalies.append('%s: 文件开头无任何声明串' % script)
                continue
            i, L, jp = title[0]
            rows.append(dict(script=script, jp=jp, chars=len(jp), offset=i, prev_title='',
                             md5=_md5(jp.encode('cp932')), kind='标题型',
                             note='本文件无 skip 结构 ⇒ 无简介；此处为该文件首条声明串（序文标题）'))
            continue
        i, L, jp = marked[0]
        note = ''
        if len(marked) > 1:
            same = all(m[2] == jp for m in marked[1:])
            dup_files.append((script, len(marked)))
            note = ('本文件有 %d 处 skip 结构（%s）；本行为首处'
                    % (len(marked), '文本完全相同' if same else '文本不同，须复核'))
        # 前置标题：简介声明串之前最后一条声明串（实测 391/417 与 scene_*.jsonl 的 title_jp 逐字相同）
        before = [d for d in decls if d[0] < i - len(SKIP_SIG)]
        prev_title = before[-1][2] if before else ''
        if prev_title and titles.get(script) == prev_title:
            prev_eq += 1
        rows.append(dict(script=script, jp=jp, chars=len(jp), offset=i, prev_title=prev_title,
                         md5=_md5(jp.encode('cp932')), kind='简介', note=note))
    stats = dict(tob_files=len(files), rows=len(rows), anomalies=anomalies,
                 kinds=_count(rows, 'kind'),
                 skip_sig_rows=sum(1 for r in rows if r['kind'] == '简介'),
                 multi_sig=dup_files,
                 prev_title_rows=sum(1 for r in rows if r['prev_title']),
                 prev_title_eq_scene_title=prev_eq)
    return rows, stats


# ================================================================ 源 3：otv
_TASK_RE = re.compile(r':Tasktype\s+"SceneJumpDialog"')
# 终止符三选一：闭合引号 / 行尾 / 块尾（S01_14G1 的 :Text 字面量缺结尾引号，靠行尾兜底）
_TEXT_RE = re.compile(r':Text[ \t]*"([^"]*)(?:"|\r?\n|$)')


def parse_otv(main):
    """PSV 明文 DSL：SceneJumpDialog 任务块的 `:Text`。"""
    psv_dir = _require_dir(os.path.join(main, '我们没有翅膀PSV', '脚本解包'),
                           'otv 脚本目录')
    lib_path = _require_file(os.path.join(main, '我们没有翅膀PSV', '汉化', '台词对照.json'),
                             'PSV 台词对照.json')
    otv_jsonl = _require_file(os.path.join(main, '我们没有翅膀——格雷塔迦露德与柳木原',
                                           '资源组', '剧本', 'scene_otv.jsonl'),
                              'scene_otv.jsonl')

    lib = json.load(open(lib_path, encoding='utf-8'))
    lib27 = [(x.get('脚本', ''), x.get('日文', ''), x.get('中文') or '')
             for x in lib if x.get('类别') == '梗概']
    otv27 = []
    with open(otv_jsonl, encoding='utf-8') as fh:
        for ln in fh:
            if not ln.strip():
                continue
            o = json.loads(ln)
            for l in o['lines']:
                if l['kind'] == 'summary':
                    otv27.append((o['script'], l['jp'], l['cn']))
    lib_map = {}
    for sc, jp, cn in lib27:
        lib_map.setdefault(_norm_for_align(jp), []).append((sc, '台词对照.json'))
    for sc, jp, cn in otv27:
        lib_map.setdefault(_norm_for_align(jp), []).append((sc, 'scene_otv.jsonl'))

    rows, anomalies, skipped = [], [], []
    blocks_by_file = {}
    for fn in sorted(os.listdir(psv_dir)):
        fp = os.path.join(psv_dir, fn)
        if fn.endswith('.tsv') or not os.path.isfile(fp):
            skipped.append('%s: 非脚本文件（跳过）' % fn)
            continue
        raw = open(fp, 'rb').read()
        try:
            text = raw.decode('cp932')
        except UnicodeDecodeError as e:
            skipped.append('%s: 非 cp932（%s）' % (fn, e))
            continue
        if text.encode('cp932') != raw:                 # 字节级保真自证
            anomalies.append('%s: cp932 往返不逐字节（md5 可能不保真）' % fn)
        k = 0
        for m in _TASK_RE.finditer(text):
            end = text.find('\n\t}', m.end())
            if end < 0:
                nxt = text.find('\n\t[', m.end())     # 下一任务块
                end = nxt if nxt >= 0 else min(len(text), m.end() + 4000)
            blk = text[m.end(): end]
            k += 1
            tm = _TEXT_RE.search(blk)
            if not tm:
                rows.append(dict(script=fn, seq=k, jp='', chars=0, md5='', in_lib='否',
                                 kind='无 :Text', note='该 SceneJumpDialog 块内未找到 :Text'))
                anomalies.append('%s#%d: SceneJumpDialog 块内无 :Text' % (fn, k))
                continue
            jp = tm.group(1)
            closed = tm.group(0).rstrip('\r\n').endswith('"')
            kind, note = '简介', ''
            if not jp.strip('\u3000 \t'):
                kind = '空文本'
                note = ':Text 仅含全角空格「\u3000」（该场景无简介文案）'
            elif not closed:
                kind = '文本未闭合'
                note = '源脚本 :Text 的字符串字面量缺结尾引号；本行按行尾截取全文'
            hits = lib_map.get(_norm_for_align(jp), [])
            if hits:
                extra = '已在库：' + '、'.join('%s（%s）' % h for h in hits)
                if kind == '空文本':
                    extra += '（内容为占位全角空格，命中仅因同为空占位串，非真实简介复用）'
                note = (note + '；' if note else '') + extra
            rows.append(dict(script=fn, seq=k, jp=jp, chars=len(jp),
                             md5=_md5(jp.encode('cp932')) if jp else '',
                             in_lib='是' if hits else '否', kind=kind, note=note))
        if k:
            blocks_by_file[fn] = k
    # 重复标注（同串多块；按首次出现者）
    first = {}
    for r in rows:
        if r['jp']:
            first.setdefault(r['jp'], (r['script'], r['seq']))
    for r in rows:
        if not r['jp']:
            continue
        if (r['script'], r['seq']) != first[r['jp']]:
            fc, fs = first[r['jp']]
            tag = ('与本文件第 %d 块内容相同' % fs) if fc == r['script'] \
                else ('与 %s 的简介逐字相同（差分脚本复用）' % fc)
            r['note'] = (r['note'] + '；' if r['note'] else '') + tag
    stats = dict(script_files=len(blocks_by_file), blocks=len(rows),
                 with_text=sum(1 for r in rows if r['jp']),
                 unique=len(set(r['jp'] for r in rows if r['jp'])),
                 kinds=_count(rows, 'kind'),
                 per_prefix=_count([dict(s=r['script'].split('_')[0]) for r in rows], 's'),
                 per_series=_count([dict(s=_series(r['script'])) for r in rows], 's'),
                 lib_n=len(lib27), lib_otv_n=len(otv27),
                 in_lib_rows=['%s#%d' % (r['script'], r['seq']) for r in rows if r['in_lib'] == '是'],
                 in_lib_script_mismatch=[('%s#%d' % (r['script'], r['seq']),
                                          lib_map.get(_norm_for_align(r['jp']), []))
                                         for r in rows if r['in_lib'] == '是'
                                         and not any(h[0] == r['script'] for h in
                                                     lib_map.get(_norm_for_align(r['jp']), []))],
                 skipped=skipped, anomalies=anomalies)
    return rows, stats


def _count(items, key):
    return dict(sorted(collections.Counter(x[key] for x in items).items()))


def _series(script):
    """S01/S02/S03/S03C → S01…S04；M01–M09 → M；P01–P04 → P；其余取前缀。"""
    p = script.split('_')[0]
    if p[:2] == 'S0':
        return p[:3]
    if p[:1] in ('M', 'P'):
        return p[:1]
    return p


# ================================================================ 输出
SPEC = {
    'ot':  dict(fn='_raw_ot.tsv',
                header=['script', 'scene_id', '简介jp', '简介cn', 'jp字符数',
                        'sob偏移', 'jp的md5', '类型', '备注'],
                cells=lambda r: [r['script'], r['scene_id'], _cell(r['jp']), _cell(r['cn']),
                                 r['chars'], r['offset'], r['md5'], r['kind'], _cell(r['note'])],
                parse=parse_ot),
    'otr': dict(fn='_raw_otr.tsv',
                header=['script', '简介jp', 'jp字符数', 'tob偏移', 'jp的md5',
                        '前置标题jp', '类型', '备注'],
                cells=lambda r: [r['script'], _cell(r['jp']), r['chars'], r['offset'],
                                 r['md5'], _cell(r['prev_title']), r['kind'],
                                 _cell(r['note'])],
                parse=parse_otr),
    'otv': dict(fn='_raw_otv.tsv',
                header=['script', '块序号', '简介jp', 'jp字符数', 'jp的md5',
                        '是否已在我方库', '类型', '备注'],
                cells=lambda r: [r['script'], r['seq'], _cell(r['jp']), r['chars'],
                                 r['md5'], r['in_lib'], r['kind'], _cell(r['note'])],
                parse=parse_otv),
}
SORT = {'ot': lambda r: r['script'],
        'otr': lambda r: r['script'],
        'otv': lambda r: (r['script'], r['seq'])}


def serialize(src, rows):
    spec = SPEC[src]
    out = ['\t'.join(spec['header'])]
    for r in sorted(rows, key=SORT[src]):
        out.append('\t'.join(str(x) for x in spec['cells'](r)))
    return ('\n'.join(out) + '\n').encode('utf-8')


def run(main, out_dir, sources, verbose=True):
    _guard_out(out_dir, _WT_ROOT)          # 先校验再创建
    os.makedirs(out_dir, exist_ok=True)
    written = {}
    for src in sources:
        if src not in SPEC:
            raise SystemExit('[FATAL] 未知源：%s（可选 ot,otr,otv）' % src)
        rows, st = SPEC[src]['parse'](main)
        blob = serialize(src, rows)
        p = os.path.join(out_dir, SPEC[src]['fn'])
        tmp = p + '.tmp'
        with open(tmp, 'wb') as fh:
            fh.write(blob)
        os.replace(tmp, p)
        written[src] = dict(path=p, md5=_md5(blob), n=len(rows), stats=st, blob=blob)
        if verbose:
            print('[%s] 条数=%d  字节=%d  md5=%s' % (src, len(rows), len(blob), _md5(blob)))
            print('     → %s' % p)
            print('     统计=%s' % json.dumps(st, ensure_ascii=False))
    return written


def print_samples(out_dir, written):
    """每源贴 2 条真实日文 + 字符数（从已落盘 TSV 读，打印的就是产物内容）。"""
    for src in ('ot', 'otr', 'otv'):
        if src not in written:
            continue
        p = written[src]['path']
        jp_i = SPEC[src]['header'].index('简介jp')
        ch_i = SPEC[src]['header'].index('jp字符数')
        print('--- 样张 %s（%s）---' % (src, os.path.basename(p)))
        n = 0
        with open(p, encoding='utf-8') as fh:
            next(fh)
            for ln in fh:
                c = ln.rstrip('\n').split('\t')
                if len(c) <= max(jp_i, ch_i) or not c[jp_i].strip() or c[jp_i].strip() == '\u3000':
                    continue
                print('   %-10s %3s 字  %s' % (c[0], c[ch_i], c[jp_i][:74]))
                n += 1
                if n >= 2:
                    break
        print()


def neg_selftest(main, out_dir):
    """负向自证：输入指错 / 输出拼出工作树，都必须报错，不得静默产出空表。"""
    print('=== 负向自证（期望：全部 PASS，即全部报错而非静默通过/空表）===')
    ok = True

    def expect_fail(label, fn):
        nonlocal ok
        try:
            fn()
        except SystemExit as e:
            print('  PASS  %-34s → %s' % (label, str(e).splitlines()[0][:96]))
            return
        except Exception as e:  # noqa: BLE001
            print('  PASS  %-34s → %s: %s' % (label, type(e).__name__, str(e)[:80]))
            return
        print('  FAIL  %-34s → 未报错（静默通过，必须修）' % label)
        ok = False

    bad = os.path.join(main, '___NO_SUCH_DIR___')
    expect_fail('ot  输入目录指错', lambda: parse_ot(bad))
    expect_fail('otr 输入目录指错', lambda: parse_otr(bad))
    expect_fail('otv 输入目录指错', lambda: parse_otv(bad))
    expect_fail('ot  scene_ot.jsonl 缺失', lambda: parse_ot(os.path.join(main, '我们没有翅膀')))
    expect_fail('输出用 .. 逃出工作树',
                lambda: _guard_out(os.path.join(out_dir, '..', '..', '..', '..', '..', '_x'),
                                   _WT_ROOT))
    expect_fail('输出指向主工作区（工程\\）',
                lambda: _guard_out(r'E:/ZCode Workspace/Galgame/工程/_x', _WT_ROOT))
    expect_fail('输出指向工作区外（C:\\）',
                lambda: _guard_out(r'C:/_x', _WT_ROOT))
    print('NEG-SELFTEST %s' % ('PASS' if ok else 'FAIL'))
    return ok


def crosscheck_otr_psv(main, verbose=True):
    """独立金标验证：R 版取到的简介 vs PSV `SceneJumpDialog :Text`（去空白后逐字比）。

    PSV 与 R 版是同一批场景的两个版本，简介文案基本同源；该比对用于证明
    otr 的取串位置正确（而不是验证两版文案是否完全一致）。
    """
    ot, _ = parse_otr(main)
    otv, _ = parse_otv(main)
    psv = {}
    for r in otv:
        if r['jp'] and r['kind'] in ('简介', '文本未闭合'):
            psv.setdefault(r['script'].lower(), r['jp'])
    agree, disagree, no_psv = 0, [], 0
    for r in ot:
        if r['kind'] != '简介':
            continue
        tx = psv.get(r['script'])
        if tx is None:
            no_psv += 1
            continue
        if _norm_for_align(r['jp']) == _norm_for_align(tx):
            agree += 1
        else:
            disagree.append((r['script'], r['jp'][:60], tx[:60]))
    if verbose:
        print('=== otr ↔ PSV 简介 金标比对（去空白） ===')
        print('  可比 %d：一致 %d ｜ 不一致 %d ｜ PSV 无对应 %d'
              % (agree + len(disagree), agree, len(disagree), no_psv))
        print('  不一致明细（多为版本差异，非取串错误）：')
        for sc, a, b in disagree:
            print('   %-12s otr=%r\n                psv=%r' % (sc, a, b))
    return agree, disagree, no_psv


def main(argv=None):
    ap = argparse.ArgumentParser(description='三源章节简介抽取（ot/otr/otv）')
    ap.add_argument('--main', default=DEFAULT_MAIN, help='主工作区工程目录（只读源）')
    ap.add_argument('--out', default=DEFAULT_OUT, help='输出目录（必须在本工作树内）')
    ap.add_argument('--sources', default='ot,otr,otv')
    ap.add_argument('--neg-selftest', action='store_true')
    ap.add_argument('--crosscheck-otr-psv', action='store_true',
                    help='用 PSV SceneJumpDialog :Text 作金标，比对 otr 取到的简介')
    a = ap.parse_args(argv)
    _require_dir(a.main, '--main 工程目录')
    _guard_out(a.out, _WT_ROOT)
    if a.neg_selftest:
        return 0 if neg_selftest(a.main, a.out) else 1
    if a.crosscheck_otr_psv:
        crosscheck_otr_psv(a.main)
        return 0
    sources = [s.strip() for s in a.sources.split(',') if s.strip()]
    written = run(a.main, a.out, sources)
    print()
    print_samples(a.out, written)
    # 幂等自证：重跑解析与序列化，与已落盘字节逐字节比对
    idem = True
    for src in sources:
        rows, _ = SPEC[src]['parse'](a.main)
        if serialize(src, rows) != written[src]['blob']:
            idem = False
        print('[%s] 幂等自证（重跑解析→序列化 vs 落盘字节）字节一致=%s'
              % (src, serialize(src, rows) == written[src]['blob']))
    print('IDEMPOTENT %s' % ('PASS' if idem else 'FAIL'))
    return 0 if idem else 1


if __name__ == '__main__':
    sys.exit(main())
