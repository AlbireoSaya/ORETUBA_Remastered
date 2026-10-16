# -*- coding: utf-8 -*-
"""独立校验：不复用生成器逻辑，直接从原始输入重算并比对输出成品。"""
import json, csv, io, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
C = os.path.join(ROOT, '语料')
O = os.path.join(ROOT, '亜衣线资源', '剧本')
J = lambda p: json.load(open(os.path.join(C, p), encoding='utf-8'))

Jd = {'file': 'd', 'offset': 'o'}
raw = [r for r in J('R版台词.json') if str(r.get('file', '')).startswith('s03c_')]
new = {(r['file'], r['offset']): r for r in J('新增译文映射.json')}
mig = {(r['file'], r['offset']): r for r in J('R版迁移映射.json')}
rec = {(r['file'], r['offset']): r for r in J('重编码映射.json')}
tru = {(r['file'], r['offset']): r for r in J('等长补齐_截断清单.json')}

out = json.load(open(os.path.join(O, '台词对照.json'), encoding='utf-8'))
flat = [l for s in out['scenes'] for l in s['lines']]
flatfile = [s['file'] for s in out['scenes'] for _ in s['lines']]
fail = []

# 1) 行数与顺序
if len(flat) != len(raw):
    fail.append('行数不符 out=%d raw=%d' % (len(flat), len(raw)))

# 2) 逐行重算期望值并与成品比对
exp_src = collections.Counter()
for i, (o, r) in enumerate(zip(flat, raw)):
    k = (r['file'], r.get('offset'))
    if o['jp'] != r['text']:
        fail.append('jp 不一致 #%d %s' % (i, k))
    if o['speaker_jp'] != (r.get('speaker') or ''):
        fail.append('speaker 不一致 #%d %s' % (i, k))
    if o['voice'] != (r.get('voice') or ''):
        fail.append('voice 不一致 #%d %s' % (i, k))
    if o['kind'] != r.get('kind'):
        fail.append('kind 不一致 #%d %s' % (i, k))
    if o['offset'] != r.get('offset') or o['index'] != r.get('index') or o['len'] != r.get('len'):
        fail.append('offset/index/len 不一致 #%d %s' % (i, k))
    if r.get('offset') is None:
        if o['cn'] != '' or o['truncated'] or o.get('source') is not None:
            fail.append('null 行不该有译文 #%d' % i)
        continue
    if k in new:
        want, want_src = new[k]['text'], 'new'
    elif k in mig:
        want, want_src = mig[k]['cn'], 'mig'
    elif k in rec:
        want, want_src = None, 'rec'
    else:
        want, want_src = None, 'MISS'
    exp_src[want_src] += 1
    if want_src != 'rec':
        if o['source'] != want_src:
            fail.append('source 不一致 #%d %s got=%s want=%s' % (i, k, o['source'], want_src))
        if k in tru:
            if not o['truncated'] or o['cn'] != tru[k]['kept'] or o.get('cn_full') != tru[k]['cn']:
                fail.append('截断行不一致 #%d %s' % (i, k))
        else:
            if o['truncated'] or o['cn'] != want or 'cn_full' in o:
                fail.append('cn 不一致 #%d %s' % (i, k))
    # 未译文检查
    if o['cn'] == '' and not o['truncated']:
        fail.append('空译文 #%d %s jp=%r' % (i, k, o['jp']))

# 3) CSV 与 JSON 对齐
rows = list(csv.reader(io.StringIO(open(os.path.join(O, '台词对照.csv'), encoding='utf-8-sig').read())))
hdr = rows[0]; body = rows[1:]
if body[0][0] != 's03c_01a':
    fail.append('CSV 首行场景异常 ' + body[0][0])
if len(body) != len(flat):
    fail.append('CSV 行数 %d != JSON %d' % (len(body), len(flat)))
bad = 0
for o, c, fn in zip(flat, body, flatfile):
    if (c[0] != fn.replace('.tob', '')
            or int(c[1]) != o['lineno'] or c[2] != o['speaker_jp'] or c[3] != o['speaker_cn']
            or c[4] != o['voice'] or c[5] != o['kind'] or c[6] != o['jp'] or c[7] != o['cn']
            or c[8] != (o.get('cn_full', '') if o['truncated'] else '')
            or c[9] != ('是' if o['truncated'] else '否')):
        bad += 1
        if bad < 4:
            fail.append('CSV/JSON 不一致 %r vs %r' % (c, o))
if bad:
    fail.append('CSV/JSON 不一致行数 %d' % bad)

# 4) 统计 JSON 交叉核对
st = json.load(open(os.path.join(O, '清单', '剧本统计.json'), encoding='utf-8'))
t = st['totals']
chk = {
    'scenes': len({r['file'] for r in raw}),
    'lines': len(raw),
    'dialog': sum(1 for r in raw if r.get('kind') == 'dialogue'),
    'narration': sum(1 for r in raw if r.get('kind') == 'narration'),
    'title': sum(1 for r in raw if r.get('kind') == 'title'),
    'truncated': sum(1 for l in flat if l['truncated']),
    'join_failed': sum(1 for r in raw if r.get('offset') is None),
    'voice_ids_unique': len({r['voice'] for r in raw if r.get('voice')}),
    'jp_chars': sum(len(r['text'] or '') for r in raw),
    'source_new': exp_src['new'], 'source_mig': exp_src['mig'], 'source_rec': exp_src['rec'],
}
for k, v in chk.items():
    if t[k] != v:
        fail.append('统计 %s out=%s want=%s' % (k, t[k], v))
sc = {s['file']: s for s in st['scenes']}
for f in {r['file'] for r in raw}:
    n = sum(1 for r in raw if r['file'] == f)
    if sc.get(f, {}).get('lines') != n:
        fail.append('场景行数不符 %s' % f)

print('校验项：行数/字段/译文来源/截断/CSV/统计/speaker_cn 回填')

# 5) 独立复核 speaker_cn 回填（裁决表在此独立誊录，用于交叉验证成品字面值）
import importlib.util
spec = importlib.util.spec_from_file_location('nm', os.path.join(ROOT, '工具', 'name_map.py'))
_m = importlib.util.module_from_spec(spec); spec.loader.exec_module(_m)
MAP2 = dict(_m.MAP)
RULING = {
    '春恵': '春惠', '大司教': '大主教', '女性店員': '女性店员', '女芸人': '女艺人',
    '女生徒': '女学生', '店員': '店员', '女生徒Ａ': '女学生Ａ', '作業員Ｂ': '作业员Ｂ',
    '作業員Ａ': '作业员Ａ', '変質者': '变态', '監督': '工头', '三年生男子Ａ': '三年级男生Ａ',
    '女': '女', '水': '水', '明日香・ハリュー': '明日香＆哈里', '制服を着た女': '穿制服的女生',
    'タカシの女': '鹰志的女人', '帽子の男': '帽子男', '男の声Ａ': '男声Ａ', '男の声Ｂ': '男声Ｂ',
    '男の声Ｃ': '男声Ｃ', 'ギャル男Ａ': '潮男Ａ', 'ギャル男Ｂ': '潮男Ｂ',
    'クソ長い髪の女': '头发超长的女人', '香田のツレ': '香田的同伴',
    'いい年した二人': '年纪不小的两人', 'いい年した三人': '年纪不小的三人',
}
bad_sp = unmapped = 0
seen_speakers = set()
for o, r in zip(flat, raw):
    sp = r.get('speaker') or ''
    seen_speakers.add(sp)
    want = MAP2.get(sp) or RULING.get(sp) or ''
    if o['speaker_cn'] != want:
        bad_sp += 1
        if bad_sp < 4:
            fail.append('speaker_cn 不符 %r got=%r want=%r' % (sp, o['speaker_cn'], want))
    if sp and sp not in MAP2 and sp not in RULING:
        unmapped += 1
if bad_sp:
    fail.append('speaker_cn 不符行数 %d' % bad_sp)
if unmapped:
    fail.append('仍未命中的说话人行数 %d' % unmapped)
kinds_unmapped = {s for s in seen_speakers if s and s not in MAP2 and s not in RULING}
if kinds_unmapped:
    fail.append('仍未命中的说话人种类 %s' % kinds_unmapped)
print('speaker_cn 不符行数:', bad_sp, '｜ 未命中行数:', unmapped,
      '｜ 未命中种类:', len(kinds_unmapped), '｜ 裁决表覆盖本线路种类:',
      len({s for s in seen_speakers if s in RULING}))

print('期望来源分布:', dict(exp_src))
print('失败数:', len(fail))
for x in fail[:40]:
    print('  FAIL', x)
print('RESULT:', 'PASS' if not fail else 'FAIL')
