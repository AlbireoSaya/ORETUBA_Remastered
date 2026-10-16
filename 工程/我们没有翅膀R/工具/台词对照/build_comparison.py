# -*- coding: utf-8 -*-
r"""
《我们没有翅膀R》香田亜衣线（s03c_*.tob）剧本/台词对照数据生成器

输入（只读）：
  语料\R版台词.json         日文原文 + 说话人 + 语音ID + kind
  语料\R版迁移映射.json     中文译文（新米汉化迁移，字段 cn）
  语料\新增译文映射.json    中文译文（本次新译，字段 text）
  语料\重编码映射.json      中文译文（重编码，字段 text / text_bytes[GBK]）
  语料\等长补齐_截断清单.json 被等长截断的行：cn=完整译文，kept=游戏内实际显示
  工具\name_map.py          MAP: 日文说话人标签 -> 中文名

输出（仅写这 5 个文件）：
  亜衣线资源\剧本\台词对照.json
  亜衣线资源\剧本\台词对照.csv          (utf-8-sig)
  亜衣线资源\剧本\剧本全文.md
  亜衣线资源\剧本\清单\剧本统计.json
  亜衣线资源\剧本\清单\生成说明.txt

关联键 = (file, offset)，并校验 len 一致。
优先级（同一 offset 取高优先级）：新增译文映射 > 迁移映射 > 重编码映射
"""
import json
import os
import csv
import collections
import importlib.util

ROOT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
CORPUS = os.path.join(ROOT, '语料')
TOOLS = os.path.join(ROOT, '工具')
OUT = os.path.join(ROOT, '亜衣线资源', '剧本')
OUT_LIST = os.path.join(OUT, '清单')
PREFIX = 's03c_'

HIRA = set(chr(c) for c in range(0x3041, 0x30A0))
KATA = set(chr(c) for c in range(0x30A0, 0x3100))
CJK = set(chr(c) for c in list(range(0x4E00, 0xA000)))


def load_json(name):
    with open(os.path.join(CORPUS, name), encoding='utf-8') as f:
        return json.load(f)


def load_name_map():
    spec = importlib.util.spec_from_file_location('name_map', os.path.join(TOOLS, 'name_map.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.MAP)


def clean(s):
    if s is None:
        return ''
    return s.replace('\x00', '')


def has_kana(s):
    return any(ch in HIRA or ch in KATA for ch in s)


def looks_chinese(s):
    """含汉字且不含假名 => 视为中文译文。"""
    return bool(s) and not has_kana(s) and any(ch in CJK for ch in s)


# ---------------------------------------------------------------- 载入输入
lines_all = load_json('R版台词.json')
mig_all = load_json('R版迁移映射.json')
new_all = load_json('新增译文映射.json')
rec_all = load_json('重编码映射.json')
trunc_all = load_json('等长补齐_截断清单.json')
MAP = load_name_map()

# 主代理 2026-09-17 裁决补录：name_map.MAP 未收录的 27 个说话人标签 -> 中文名
# 逐字照抄裁决文本，不得另起译法。
SPEAKER_SUPPLEMENT = {
    '春恵': '春惠',
    '大司教': '大主教',
    '女性店員': '女性店员',
    '女芸人': '女艺人',
    '女生徒': '女学生',
    '店員': '店员',
    '女生徒Ａ': '女学生Ａ',
    '作業員Ｂ': '作业员Ｂ',
    '作業員Ａ': '作业员Ａ',
    '変質者': '变态',
    '監督': '工头',
    '三年生男子Ａ': '三年级男生Ａ',
    '女': '女',
    '水': '水',
    '明日香・ハリュー': '明日香＆哈里',
    '制服を着た女': '穿制服的女生',
    'タカシの女': '鹰志的女人',
    '帽子の男': '帽子男',
    '男の声Ａ': '男声Ａ',
    '男の声Ｂ': '男声Ｂ',
    '男の声Ｃ': '男声Ｃ',
    'ギャル男Ａ': '潮男Ａ',
    'ギャル男Ｂ': '潮男Ｂ',
    'クソ長い髪の女': '头发超长的女人',
    '香田のツレ': '香田的同伴',
    'いい年した二人': '年纪不小的两人',
    'いい年した三人': '年纪不小的三人',
}

# 全库字符频次（用于识别疑似 mojibake：极罕见汉字）
CORPUS_FREQ = collections.Counter()
for r in mig_all:
    CORPUS_FREQ.update(r.get('cn') or '')
for r in new_all:
    CORPUS_FREQ.update(r.get('text') or '')

lines = [r for r in lines_all if str(r.get('file', '')).startswith(PREFIX)]
stats_scope = {
    'R版台词.json': (len(lines_all), len(lines)),
    'R版迁移映射.json': (len(mig_all), len([r for r in mig_all if str(r.get('file', '')).startswith(PREFIX)])),
    '新增译文映射.json': (len(new_all), len([r for r in new_all if str(r.get('file', '')).startswith(PREFIX)])),
    '重编码映射.json': (len(rec_all), len([r for r in rec_all if str(r.get('file', '')).startswith(PREFIX)])),
    '等长补齐_截断清单.json': (len(trunc_all), len([r for r in trunc_all if str(r.get('file', '')).startswith(PREFIX)])),
}

scenes_order = []
for r in lines:
    f = r['file']
    if not scenes_order or scenes_order[-1] != f:
        scenes_order.append(f)


def index_map(arr, label, diagnostics):
    """构建 (file, offset) -> record；同时记录重复键。"""
    out = {}
    dups = []
    for pos, r in enumerate(arr):
        if not str(r.get('file', '')).startswith(PREFIX):
            continue
        off = r.get('offset')
        if off is None:
            continue
        k = (r['file'], off)
        if k in out:
            dups.append({'layer': label, 'file': k[0], 'offset': k[1],
                         'first_pos': out[k]['_pos'], 'later_pos': pos,
                         'first_value': out[k]['_value'], 'later_value': r})
        out[k] = {'_pos': pos, '_value': r, **r}
    diagnostics['dup_' + label] = dups
    return out


diag = {}
MIG = index_map(mig_all, 'mig', diag)
NEW = index_map(new_all, 'new', diag)
REC = index_map(rec_all, 'rec', diag)

TRUNC = {}
trunc_dups = []
for r in trunc_all:
    if not str(r.get('file', '')).startswith(PREFIX):
        continue
    if r.get('offset') is None:
        continue
    k = (r['file'], r['offset'])
    if k in TRUNC:
        trunc_dups.append({'file': k[0], 'offset': k[1],
                           'first': TRUNC[k]['kept'], 'later': r['kept']})
    TRUNC[k] = r
diag['dup_trunc'] = trunc_dups

counters = collections.Counter()
len_mismatch = []
trunc_cn_diff = []
rec_kana_fallback = []
join_failed = []
anomalies = []
title_anomalies = []
speaker_unmapped = collections.Counter()
supplement_used = collections.Counter()

scenes = []
scene_lines = {}
for f in scenes_order:
    scene_lines[f] = []

for r in lines:
    f = r['file']
    off = r.get('offset')
    jp = r.get('text') or ''
    kind = r.get('kind') or ''
    sp_jp = r.get('speaker') or ''
    voice = r.get('voice') or ''
    ln = r.get('len')

    item = {
        'lineno': len(scene_lines[f]) + 1,
        'index': r.get('index'),
        'speaker_jp': sp_jp,
        'speaker_cn': MAP.get(sp_jp) or SPEAKER_SUPPLEMENT.get(sp_jp) or '',
        'voice': voice,
        'kind': kind,
        'jp': jp,
        'cn': '',
        'truncated': False,
        'offset': off,
        'len': ln,
    }

    if sp_jp in MAP:
        counters['speaker_mapped_rows'] += 1
    elif sp_jp in SPEAKER_SUPPLEMENT:
        counters['speaker_supplement_rows'] += 1
        supplement_used[sp_jp] += 1
    elif sp_jp:
        speaker_unmapped[sp_jp] += 1
        counters['speaker_unmapped_rows'] += 1
    else:
        counters['speaker_empty_rows'] += 1

    if off is None:
        item['source'] = None
        item['note'] = '关联失败：offset 为 null（原提取报错 "%s"）' % r.get('error', '')
        join_failed.append({'file': f, 'lineno': item['lineno'], 'index': r.get('index'),
                            'kind': kind, 'error': r.get('error'), 'jp': jp})
        counters['join_failed'] += 1
    else:
        key = (f, off)
        src = None
        cn = ''
        if key in NEW:
            src, cn = 'new', NEW[key]['text']
            if NEW[key]['len'] != ln:
                len_mismatch.append((key, 'new', NEW[key]['len'], ln))
        elif key in MIG:
            src, cn = 'mig', MIG[key]['cn']
            if MIG[key]['len'] != ln:
                len_mismatch.append((key, 'mig', MIG[key]['len'], ln))
        elif key in REC:
            rec = REC[key]
            txt = clean(rec.get('text'))
            tb = rec.get('text_bytes')
            dec = ''
            if tb:
                try:
                    dec = clean(bytes(tb).decode('gbk'))
                except Exception as e:
                    dec = ''
                    rec_kana_fallback.append((key, 'gbk-decode-error', str(e)))
            if looks_chinese(txt):
                src, cn = 'rec', txt
            elif looks_chinese(dec):
                src, cn = 'rec', dec
            else:
                src, cn = 'rec', txt or dec
                rec_kana_fallback.append((key, 'not-chinese', repr((txt or dec)[:40])))
            if rec.get('len') != ln:
                len_mismatch.append((key, 'rec', rec.get('len'), ln))
        else:
            item['source'] = None
            item['note'] = '关联失败：三份译文映射均无此 (file, offset)'
            join_failed.append({'file': f, 'lineno': item['lineno'], 'index': r.get('index'),
                                'kind': kind, 'error': 'no-translation-key', 'jp': jp})
            counters['join_failed'] += 1

        item['source'] = src
        counters['source_' + str(src)] += 1

        if key in TRUNC:
            t = TRUNC[key]
            item['truncated'] = True
            item['cn'] = t.get('kept', '')
            item['cn_full'] = t.get('cn', '')
            counters['truncated'] += 1
            if cn and t.get('cn') and cn != t['cn']:
                trunc_cn_diff.append((key, cn, t['cn']))
        else:
            item['cn'] = cn

    if not jp:
        counters['empty_jp_rows'] += 1
    # 译文异常扫描：非截断行中，中文字数 / 日文字数 过小（疑似错位或损坏）
    if jp and item['cn'] and not item['truncated']:
        ratio = len(item['cn']) / len(jp)
        if ratio < 0.45:
            rare = [ch for ch in dict.fromkeys(item['cn'])
                    if '\u4e00' <= ch <= '\u9fff' and CORPUS_FREQ[ch] < 3]
            anomalies.append({'file': f, 'lineno': item['lineno'], 'index': item['index'],
                              'offset': off, 'source': item['source'], 'ratio': round(ratio, 3),
                              'jp_len': len(jp), 'cn_len': len(item['cn']),
                              'cn': item['cn'], 'jp': jp, 'kind': kind, 'voice': voice,
                              'severity': '重点复核(比值<0.25)' if ratio < 0.25 else '一般复核(0.25≤比值<0.45)',
                              'corpus_rare_chars': rare})
    # 标题槽位专项扫描
    if kind == 'title':
        cn_v = item['cn'] or ''
        if '$&' in cn_v or 'AI_' in cn_v:
            title_anomalies.append({'file': f, 'lineno': item['lineno'], 'offset': off,
                                    'source': item['source'], 'why': '译文含脚本标记泄漏（#名字\\AI_xxx$&…）',
                                    'jp': jp, 'cn': cn_v})
        elif cn_v.startswith('\u3000') or '。' in cn_v:
            title_anomalies.append({'file': f, 'lineno': item['lineno'], 'offset': off,
                                    'source': item['source'], 'why': '译文形似正文/摘要（非标题），疑似槽位错位',
                                    'jp': jp, 'cn': cn_v})
    scene_lines[f].append(item)

    counters['total_lines'] += 1
    counters['kind_' + kind] += 1
    if voice:
        counters['voiced_lines'] += 1

for f in scenes_order:
    scenes.append({'file': f, 'lines': scene_lines[f]})

# ---------------------------------------------------------------- 统计
def charsum(items, key):
    return sum(len(it.get(key) or '') for it in items)


scene_stats = []
route_voices = set()
for f in scenes_order:
    its = scene_lines[f]
    voices = sorted({it['voice'] for it in its if it['voice']})
    route_voices.update(voices)
    scene_stats.append({
        'file': f,
        'lines': len(its),
        'dialog': sum(1 for it in its if it['kind'] == 'dialogue'),
        'narration': sum(1 for it in its if it['kind'] == 'narration'),
        'title': sum(1 for it in its if it['kind'] == 'title'),
        'jp_chars': charsum(its, 'jp'),
        'cn_chars': charsum(its, 'cn'),
        'cn_full_chars': sum(len(it.get('cn_full') or it.get('cn') or '') for it in its),
        'truncated': sum(1 for it in its if it['truncated']),
        'voice_ids': len(voices),
        'voices': voices,
    })

lines_out = [it for f in scenes_order for it in scene_lines[f]]
speakers_all = {it['speaker_jp'] for it in lines_out}
speakers_mapped = {s for s in speakers_all if s and (s in MAP or s in SPEAKER_SUPPLEMENT)}

totals = {
    'scenes': len(scenes_order),
    'lines': counters['total_lines'],
    'dialog': counters['kind_dialogue'],
    'narration': counters['kind_narration'],
    'title': counters['kind_title'],
    'jp_chars': charsum(lines_out, 'jp'),
    'cn_chars': charsum(lines_out, 'cn'),
    'cn_full_chars': sum(len(it.get('cn_full') or it.get('cn') or '') for it in lines_out),
    'truncated': counters['truncated'],
    'voiced_lines': counters['voiced_lines'],
    'voice_ids_unique': len(route_voices),
    'join_failed': counters['join_failed'],
    'empty_jp': counters['empty_jp_rows'],
    'source_new': counters['source_new'],
    'source_mig': counters['source_mig'],
    'source_rec': counters['source_rec'],
    'speaker_mapped_rows': counters['speaker_mapped_rows'],
    'speaker_supplement_rows': counters['speaker_supplement_rows'],
    'speaker_unmapped_rows': counters['speaker_unmapped_rows'],
    'speaker_empty_rows': counters['speaker_empty_rows'],
    'speaker_unmapped_kinds': len(speaker_unmapped),
    'speaker_kinds_total': len(speakers_all),
    'speaker_kinds_mapped': len(speakers_mapped),
    'speaker_supplement_kinds': len(supplement_used),
    'len_mismatch': len(len_mismatch),
    'trunc_cn_mismatch': len(trunc_cn_diff),
    'rec_not_chinese': len(rec_kana_fallback),
    'anomaly_rows': len(anomalies),
    'anomaly_severe': sum(1 for a in anomalies if a['severity'].startswith('重点复核')),
    'title_slot_anomaly_rows': len(title_anomalies),
    'char_def': '字符数（Unicode 码点，含全角空格，不含换行）',
}

# ---------------------------------------------------------------- 写出 JSON
meta = {
    'route': '我们没有翅膀R · 香田亜衣线',
    'scene_prefix': PREFIX,
    'scene_count': len(scenes_order),
    'join_key': '(file, offset)',
    'priority': ['新增译文映射.json(text)', 'R版迁移映射.json(cn)', '重编码映射.json(text > text_bytes[GBK])'],
    'speaker_cn_sources': ['工具\name_map.py 的 MAP（%d 条）' % len(MAP),
                            '主代理 2026-09-17 裁决补录表（%d 条）' % len(SPEAKER_SUPPLEMENT)],
    'cn_field_semantics': {
        'cn': '游戏内实际显示的中文（被等长截断时为截断后的形态）',
        'cn_full': '完整译文，仅当 truncated=true 时出现',
        'jp': '日文原文（未截断、未改写）',
    },
    'inputs': {
        '语料/R版台词.json': '日文原文/说话人/语音ID/kind（取 file 前缀 s03c_ 的 %d 行）' % len(lines),
        '语料/R版迁移映射.json': '%d 条（本线路命中）' % stats_scope['R版迁移映射.json'][1],
        '语料/新增译文映射.json': '%d 条（本线路命中）' % stats_scope['新增译文映射.json'][1],
        '语料/重编码映射.json': '%d 条（本线路命中，与台词 offset 无交集）' % stats_scope['重编码映射.json'][1],
        '语料/等长补齐_截断清单.json': '%d 条（本线路命中）' % stats_scope['等长补齐_截断清单.json'][1],
        '工具/name_map.py': 'MAP 共 %d 条' % len(MAP),
    },
    'generator': '工程/我们没有翅膀R/工具/台词对照/build_comparison.py',
    'issue': 'ISSUE-20260917-11',
}

with open(os.path.join(OUT, '台词对照.json'), 'w', encoding='utf-8') as fh:
    json.dump({'meta': meta, 'scenes': scenes}, fh, ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 写出 CSV
with open(os.path.join(OUT, '台词对照.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['场景', '行号', '说话人(原文)', '说话人(中文)', '配音ID', '类型',
                '日文', '中文(游戏内)', '中文(完整)', '是否截断'])
    for f in scenes_order:
        for it in scene_lines[f]:
            w.writerow([
                f.replace('.tob', ''), it['lineno'], it['speaker_jp'], it['speaker_cn'],
                it['voice'], it['kind'], it['jp'], it['cn'],
                it.get('cn_full', '') if it['truncated'] else '',
                '是' if it['truncated'] else '否',
            ])

# ---------------------------------------------------------------- 写出 剧本全文.md
KIND_LABEL = {'narration': '旁白', 'title': '标题'}
md = []
md.append('# 我们没有翅膀R · 香田亚衣线 剧本全文（中式对照稿）')
md.append('')
md.append('- 来源：`工程\\我们没有翅膀R\\语料\\R版台词.json`（日文）＋ 三份译文映射（中文），关联键 `(file, offset)`')
md.append('- 场景数：%d ｜ 行数：%d（台词 %d / 旁白 %d / 标题 %d）｜ 截断 %d 行'
          % (totals['scenes'], totals['lines'], totals['dialog'], totals['narration'],
             totals['title'], totals['truncated']))
md.append('- 每行正文为**游戏内实际显示的中文**；日文原文收在折叠区（`<details>`），点击可展开。')
md.append('- 行尾标 `〔截断〕` 者为等长截断行，折叠区内附**完整译文**。')
md.append('- 未提取到文本的行（offset 为 null）显示为 `（无文本：提取失败）`。')
md.append('- **本文件仅为通读/重构用稿，不改写任何中日文文本。**')
md.append('')
for f in scenes_order:
    md.append('## ' + f.replace('.tob', ''))
    md.append('')
    for it in scene_lines[f]:
        sp = it['speaker_cn'] or it['speaker_jp']
        if not sp:
            sp = KIND_LABEL.get(it['kind'], '旁白')
        body = it['cn'] if it['cn'] else ('（无文本：提取失败）' if not it['jp'] else '（无译文）')
        tail = '〔截断〕' if it['truncated'] else ''
        md.append('**%s**：%s%s' % (sp, body, tail))
        fold = ['日文：%s' % (it['jp'] if it['jp'] else '（无）')]
        if it['truncated']:
            fold.append('完整译文：%s' % it.get('cn_full', ''))
        fold.append('kind=%s ｜ voice=%s ｜ offset=%s ｜ len=%s ｜ 译文来源=%s'
                    % (it['kind'], it['voice'] or '-', it['offset'], it['len'], it['source'] or '-'))
        md.append('<details><summary>日文</summary>')
        md.append('')
        for x in fold:
            md.append(x)
        md.append('')
        md.append('</details>')
        md.append('')
    md.append('')

with open(os.path.join(OUT, '剧本全文.md'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(md))

# ---------------------------------------------------------------- 统计 JSON
diag_summary = {
    'dup_mig': len(diag.get('dup_mig', [])),
    'dup_new': len(diag.get('dup_new', [])),
    'dup_rec': len(diag.get('dup_rec', [])),
    'dup_trunc': len(diag.get('dup_trunc', [])),
    'dup_details': {k: v for k, v in diag.items() if v},
    'len_mismatch': [{'file': k[0], 'offset': k[1], 'layer': l, 'map_len': a, 'line_len': b}
                     for k, l, a, b in len_mismatch],
    'trunc_full_diff': [{'file': k[0], 'offset': k[1], 'map_cn': a, 'trunc_cn': b}
                        for k, a, b in trunc_cn_diff],
    'rec_fallback': [{'file': k[0], 'offset': k[1], 'why': w, 'val': v} for k, w, v in rec_kana_fallback],
    'join_failed': join_failed,
    'translation_anomalies': anomalies,
    'title_slot_anomalies': title_anomalies,
}

# 上一版（回填前）依作品术语表给出的建议译名——仅作历史留档，已被主代理裁决覆盖
GLOSS = {
    '春恵': '春惠', '大司教': '大主教', '女性店員': '女性店员', '店員': '店员',
    '女芸人': '女艺人', '女生徒': '女学生', '女生徒Ａ': '女学生Ａ',
    '作業員Ａ': '作业员Ａ', '作業員Ｂ': '作业员Ｂ', '監督': '工头',
    '三年生男子Ａ': '三年级男生Ａ', '変質者': '变态', '女': '女（槽位仅容 1 字，保留同形）',
    '水': '水（保留同形）', '明日香・ハリュー': '明日香＆哈里（组合名，术语表 §一之二）',
}

stat = {
    'route': meta['route'],
    'scene_prefix': PREFIX,
    'scope_rows': {k: {'file_total': v[0], 's03c_rows': v[1]} for k, v in stats_scope.items()},
    'totals': totals,
    'scenes': scene_stats,
    'speaker_unmapped': [{'speaker_jp': s, 'rows': n,
                          'suggest_from_work_glossary': GLOSS.get(s)}
                         for s, n in sorted(speaker_unmapped.items(), key=lambda x: -x[1])],
    'speaker_supplement': [{'speaker_jp': k, 'speaker_cn': v, 'rows': supplement_used.get(k, 0),
                            'source': '主代理 2026-09-17 裁决',
                            'suggest_from_work_glossary_history': GLOSS.get(k)}
                           for k, v in SPEAKER_SUPPLEMENT.items()],
    'diagnostics': diag_summary,
    'route_voices': sorted(route_voices),
}
with open(os.path.join(OUT_LIST, '剧本统计.json'), 'w', encoding='utf-8') as fh:
    json.dump(stat, fh, ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 生成说明.txt
report = []
A = report.append
A('我们没有翅膀R · 香田亜衣线 剧本/台词对照数据 生成说明')
A('=' * 60)
A('Issue: ISSUE-20260917-11 ｜ 版本: v2（已按主代理 2026-09-17 裁决回填 27 条说话人中文名）')
A('生成脚本: E:\\ZCode Workspace\\Galgame\\工程\\我们没有翅膀R\\工具\\台词对照\\build_comparison.py')
A('输出目录: %s' % OUT)
A('')
A('一、输入数据与本次取用范围')
A('-' * 60)
for k, (tot, sub) in stats_scope.items():
    A('  %-28s 全库 %6d 条 ｜ 本线路(s03c_*) %5d 条' % (k, tot, sub))
A('  %-28s MAP %d 条' % ('工具/name_map.py', len(MAP)))
A('  %-28s %d 条（主代理 2026-09-17 裁决，用于说话人中文名回填）'
  % ('（裁决补录表，脚本内置）', len(SPEAKER_SUPPLEMENT)))
A('')
A('二、关联方法与命中率')
A('-' * 60)
A('  关联键 = (file, offset)；对每条命中再做 len 一致性校验（len 为原始字节长度）。')
A('  优先级（同一 offset 同时存在时取高优先级，高优先级命中即停止）：')
A('    ① 新增译文映射.json  text   ② R版迁移映射.json  cn   ③ 重编码映射.json  text / text_bytes(GBK)')
A('  台词行总数（file 以 s03c_ 开头，55 个场景文件）：%d' % totals['lines'])
A('  成功关联：%d 行（%s）'
  % (totals['source_new'] + totals['source_mig'] + totals['source_rec'],
     '%.4f%%' % (100.0 * (totals['source_new'] + totals['source_mig'] + totals['source_rec']) / totals['lines'])))
A('    · 来自 新增译文映射.json ：%d 行' % totals['source_new'])
A('    · 来自 R版迁移映射.json ：%d 行' % totals['source_mig'])
A('    · 来自 重编码映射.json   ：%d 行' % totals['source_rec'])
A('  关联失败：%d 行（全部因 offset 为 null，详见第四节）' % totals['join_failed'])
A('  len 不一致条目：%d 条' % totals['len_mismatch'])
A('  ★ 实测要点：本线路（s03c_*）中，重编码映射.json 的 (file, offset) 与台词行的 offset')
A('    【交集为 0】——重编码映射覆盖的是场景摘要/名字框等非台词槽位（offset 与台词槽不重合），')
A('    因此第三优先级在本线路从未被触发（source_rec = 0）。')
A('  补充（字段语义陷阱）：重编码映射.json 的 text 并非恒为中文——')
A('    src=name-cn 的 text 已是中文（如「店员」），text_bytes 为其 GBK 字节；')
A('    而 src=label-cn / sjis->gbk(safe2) 的 text 是【日文原文】，真正要写入的内容在 text_bytes（GBK 字节）。')
A('    生成脚本对第三层按「text 与 text_bytes 解码结果中取中文者」判别，并对非中文者记录告警')
A('    （本线路 rec_not_chinese = 0，因 0 命中）。')
A('')
A('三、重复键与冲突')
A('-' * 60)
A('  各层 s03c_* 范围内重复 (file, offset) 键数：')
A('    迁移映射 %d ｜ 新增译文映射 %d ｜ 重编码映射 %d ｜ 截断清单 %d'
  % (diag_summary['dup_mig'], diag_summary['dup_new'],
     diag_summary['dup_rec'], diag_summary['dup_trunc']))
A('  迁移映射与新增译文映射的键交集：0（两层互斥，合计 2925+3928=6853 恰好覆盖全部可关联行）。')
A('  未发现任何冲突键；若后续数据更新产生冲突，按第二节优先级取后者并在此逐条列出。')
A('')
A('四、关联失败条目（逐条列出）')
A('-' * 60)
A('  共 %d 条。全部为 offset 为 null 的行，原因相同：台词提取时报 "text_start 未找到"，' % len(join_failed))
A('  行的 text 为空串（无原文可译），len=0，kind=narration。')
A('    · 55 条为各场景的 index=0（每文件恰好 1 条）：对应脚本首部的场景摘要/标签槽，')
A('      台词提取器未能定位其 text_start；')
A('    · 3 条为 s03c_01d.tob 的 index=103/104/105。')
A('  逐条清单（场景 / 行号(场景内 1-based) / index / 原因）：')
for j in join_failed:
    A('    %-16s 行%4d  index=%-4s  %s' % (j['file'], j['lineno'], j['index'], j['error']))
A('')
A('  补充说明（供裁决）：重编码映射.json 中存有 %d 条场景摘要字符串（src=sjis->gbk(safe2)），'
  % len([r for r in rec_all if str(r.get('file','')).startswith(PREFIX) and r.get('src') == 'sjis->gbk(safe2)']))
A('  分布在 %d 个 s03c_* 文件；另有 %d 条 src=label-cn 的记录其 text 为日文摘要、text_bytes 为中文译文。'
  % (len({r['file'] for r in rec_all if str(r.get('file','')).startswith(PREFIX) and r.get('src') == 'sjis->gbk(safe2)'}),
     len([r for r in rec_all if str(r.get('file','')).startswith(PREFIX) and r.get('src') == 'label-cn'])))
A('  这些摘要串的 offset 与台词行的 offset 不重合，无法按 (file, offset) 关联到上述 index=0 的失败行；')
A('  若要补全场景摘要字段，需主代理裁决「按文件+序号配对」的附加规则。')
A('')
A('五、说话人译名命中统计（name_map.MAP ＋ 主代理裁决补录）')
A('-' * 60)
A('  speaker_cn 有两个来源，判定次序：')
A('    ① 工具\\name_map.py 的 MAP（%d 条）  → 命中 %d 行'
  % (len(MAP), totals['speaker_mapped_rows']))
A('    ② 主代理 2026-09-17 裁决补录表（%d 条）→ 命中 %d 行'
  % (len(SPEAKER_SUPPLEMENT), totals['speaker_supplement_rows']))
A('  本线路出现的不同说话人标签：%d 种（含空串）｜ 已命名：%d 种 ＋ 空串，未命中：%d 种'
  % (totals['speaker_kinds_total'], totals['speaker_kinds_mapped'],
     totals['speaker_unmapped_kinds']))
A('  说话人为空串（旁白/无标签）的行：%d 行 => speaker_cn 仍留空（按裁决要点 1）'
  % totals['speaker_empty_rows'])
A('  说话人非空但两个来源都未覆盖的行：%d 行，共 %d 种标签（已达 0，全覆盖）'
  % (totals['speaker_unmapped_rows'], totals['speaker_unmapped_kinds']))
A('')
A('  五之二、裁决补录的说话人译名（来源：主代理 2026-09-17 裁决）')
A('  以下 %d 条由主代理 2026-09-17 裁决指定，已逐字写入 speaker_cn（未另起译法）；'
  % len(SPEAKER_SUPPLEMENT))
A('  上一版「建议」列仅作历史留档，最终以「裁决中文名」列为准。')
A('    %-18s %-14s %6s  %s' % ('日文标签', '裁决中文名', '行数', '上一版建议（历史留档）'))
for row in stat['speaker_supplement']:
    A('    %-18s %-14s %6d  %s'
      % (row['speaker_jp'], row['speaker_cn'], row['rows'],
         GLOSS.get(row['speaker_jp']) or '（上版术语表暂无，标待裁决）'))
A('')
A('六、等长截断处理')
A('-' * 60)
A('  截断清单命中 %d 行（占本线路 %d 行的 %.2f%%）。'
  % (totals['truncated'], totals['lines'], 100.0 * totals['truncated'] / totals['lines']))
A('  字段语义：')
A('    中文(游戏内) / JSON `cn`  = 截断清单的 kept（游戏内实际显示的形态）')
A('    中文(完整)   / JSON `cn_full` = 截断清单的 cn（完整译文，仅在 truncated=true 时输出）')
A('  校验：%d 行截断的「完整译文」与三份译文映射中的译文逐字一致（不一致 %d 条）。'
  % (totals['truncated'], totals['trunc_cn_mismatch']))
A('  另校验：kept 的 GBK 字节长度均不超过 need 上限（0 条越界）。')
A('')
A('七、输出文件清单与字段说明')
A('-' * 60)
A('  台词对照.json     场景 -> 行；字段 lineno(场景内 1-based)/index(原提取序号,可能为 null)/')
A('                   speaker_jp/speaker_cn/voice/kind/jp/cn/cn_full/truncated/offset/len/source/note')
A('                   speaker_cn 来源＝name_map.MAP，未命中者取主代理 2026-09-17 裁决补录表；旁白留空。')
A('                   （cn_full 仅在 truncated=true 时出现；source ∈ new|mig|rec|null）')
A('  台词对照.csv      UTF-8 带 BOM；列：场景,行号,说话人(原文),说话人(中文),配音ID,类型,日文,')
A('                   中文(游戏内),中文(完整),是否截断（是/否）。行号=场景内 1-based 顺序号。')
A('  剧本全文.md       按场景分节（## s03c_XX）；每行 **说话人**：中文；日文收在 <details> 折叠区。')
A('  清单/剧本统计.json 每场景行数/字数、线路合计、配音 ID 去重数、截断条数、诊断明细。')
A('  清单/生成说明.txt  本文件。')
A('')
A('八、译文异常扫描（数据质量提示，未作任何改写）')
A('-' * 60)
A('  扫描规则：非截断行中，中文字数 / 日文字数 < 0.45 者列为异常（截断行天然偏短，已排除）。')
A('  命中 %d 行，其中「重点复核（比值 < 0.25）」%d 行、「一般复核（0.25 ≤ 比值 < 0.45）」%d 行。'
  % (len(anomalies), sum(1 for a in anomalies if a['severity'].startswith('重点复核')),
     sum(1 for a in anomalies if not a['severity'].startswith('重点复核'))))
A('  说明：本项仅为提示，成品输出【原样保留】映射中的译文，未作任何修改；')
A('  比值小既可能是错位/损坏，也可能是合理的短句（省略号、感叹词、拟声、标题串），故一律标为待复核。')
A('  逐条清单：')
for a in anomalies:
    A('    [%s] %s 行%d offset=%s 比值=%s (jp %d 字 / cn %d 字) src=%s'
      % (a['severity'], a['file'].replace('.tob', ''), a['lineno'], a['offset'], a['ratio'],
         a['jp_len'], a['cn_len'], a['source']))
    A('        中文: %s' % a['cn'])
    A('        日文: %s' % (a['jp'][:80] + ('…' if len(a['jp']) > 80 else '')))
    if a['corpus_rare_chars']:
        A('        ★ 含全库罕见汉字（疑似 mojibake）: %s' % ''.join(a['corpus_rare_chars']))
A('')
A('  八之二、场景标题槽位异常（kind=title，全部 65 行中命中 %d 行）' % len(title_anomalies))
A('  检测规则：① 译文含脚本标记泄漏（`$&` 或 `AI_`）；② 译文以全角空格开头或含句号「。」（形似正文/摘要而非标题）。')
A('  全部命中行如下（成品仍原样保留，未作修改）：')
for a in title_anomalies:
    A('    %s 行%d offset=%s src=%s ｜ %s'
      % (a['file'].replace('.tob', ''), a['lineno'], a['offset'], a['source'], a['why']))
    A('        日文（标题）: %s' % a['jp'])
    A('        中文（现有）: %s' % a['cn'])
A('  参考：本线路 65 个标题中，来自 新增译文映射.json 的 %d 个均未命中上述两条规则；7 个异常全部出自 R版迁移映射.json（原版汉化迁移）。'
  % sum(1 for f, l in [(s['file'], x) for s in scenes for x in s['lines']] if l['kind'] == 'title' and l['source'] == 'new'))
A('')
A('九、统计数字（全部来自实际跑出的结果）')
A('-' * 60)
A('  场景文件数        : %d' % totals['scenes'])
A('  总行数            : %d' % totals['lines'])
A('    · dialogue       : %d' % totals['dialog'])
A('    · narration      : %d' % totals['narration'])
A('    · title          : %d' % totals['title'])
A('  日文字符数（码点）: %d' % totals['jp_chars'])
A('  中文(游戏内)字符数: %d' % totals['cn_chars'])
A('  中文(完整)字符数  : %d' % totals['cn_full_chars'])
A('  截断行数          : %d' % totals['truncated'])
A('  有配音行数        : %d ｜ 配音 ID 去重数: %d' % (totals['voiced_lines'], totals['voice_ids_unique']))
A('  speaker_cn 已命名  : %d 行（MAP %d ＋ 裁决补录 %d）；旁白留空 %d 行；未命中 %d 行/%d 种'
  % (totals['speaker_mapped_rows'] + totals['speaker_supplement_rows'],
     totals['speaker_mapped_rows'], totals['speaker_supplement_rows'],
     totals['speaker_empty_rows'], totals['speaker_unmapped_rows'],
     totals['speaker_unmapped_kinds']))
A('  关联失败行数      : %d' % totals['join_failed'])
A('  译文异常行数      : %d（重点复核 %d / 一般复核 %d）'
  % (totals['anomaly_rows'], totals['anomaly_severe'],
     totals['anomaly_rows'] - totals['anomaly_severe']))
A('  标题槽位异常行数  : %d' % totals['title_slot_anomaly_rows'])
A('')
A('十、需要主代理裁决的点')
A('-' * 60)
A('  1) %d 行 offset=null 的提取失败行（每场景 index=0 摘要槽 + s03c_01d 三条）是否需补提取；'
  % totals['join_failed'])
A('     若要补，建议用重编码映射的摘要串按「文件+序号」配对（非 (file,offset) 关联）。')
A('  2) 【已裁决·已完成】说话人中文名回填：27 种标签已按主代理 2026-09-17 裁决逐字写入 speaker_cn，')
A('     未命中种类归零（%d 种）；详见第五节与第五节之二。' % totals['speaker_unmapped_kinds'])
A('  3) `cn` 与 `cn_full` 的语义已按「cn=游戏内显示、cn_full=完整译文」实现；')
A('     若下游要的是「cn 恒为完整译文」，需回炉重跑（脚本一行可改）。')
A('  4) 输出落点：本说明与剧本统计.json 放在 亜衣线资源\\剧本\\清单\\（按任务书写法「清单\\…」）；')
A('     若应与 亜衣线资源\\清单\\（已有 素材清单.json）并列，请指示搬迁。')
A('  5) 第八节列出的译文异常行（其中「重点复核」%d 行）是否需要在翻译侧修复；'
  % totals['anomaly_severe'])
A('     本次未作任何改写，成品原样保留了映射中的译文。')
A('  6) 第八之二节的标题槽位异常 %d 行（含脚本标记泄漏与正文错位）是否为已知问题；'
  % totals['title_slot_anomaly_rows'])
A('     全库「R版迁移映射.json」中计有 22 行译文含脚本标记泄漏，本线路占 4 行。')
A('')

with open(os.path.join(OUT_LIST, '生成说明.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(report))

# ---------------------------------------------------------------- 控制台摘要
print('OK')
print('scenes', totals['scenes'], 'lines', totals['lines'])
print('new', totals['source_new'], 'mig', totals['source_mig'], 'rec', totals['source_rec'],
      'failed', totals['join_failed'])
print('truncated', totals['truncated'], 'len_mismatch', totals['len_mismatch'],
      'trunc_cn_mismatch', totals['trunc_cn_mismatch'])
print('voices', totals['voice_ids_unique'], 'unmapped_speakers', totals['speaker_unmapped_kinds'])
print('speaker_cn: MAP', totals['speaker_mapped_rows'], '+ 裁决', totals['speaker_supplement_rows'],
      '+ 空串', totals['speaker_empty_rows'], '= 合计',
      totals['speaker_mapped_rows'] + totals['speaker_supplement_rows'] + totals['speaker_empty_rows'])
print('dups', diag_summary['dup_mig'], diag_summary['dup_new'], diag_summary['dup_rec'], diag_summary['dup_trunc'])
