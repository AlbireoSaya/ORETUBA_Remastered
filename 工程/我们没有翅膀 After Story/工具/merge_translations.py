# -*- coding: utf-8 -*-
r"""merge_translations.py —— 合并 23 批译文 → 全作译文语料 + 逐脚本中文文本

产出：
  语料\译文.json            {脚本名: {code_start, messages:[{index,kind,speaker,voice,cn}]}}
  语料\中文字幕\<脚本名>.txt  「说话人｜原文 ⇒ 译文」对照（人工复核用）
  语料\合并报告.json        条数、缺批、空译、总字符数

用法：python merge_translations.py [--strict]
  --strict：任何缺批 / 缺条 / 错位即非零退出（收尾验收用）
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')
CORPUS = os.path.join(PROJ, '语料')


def main():
    strict = '--strict' in sys.argv
    man = json.load(io.open(os.path.join(WD, '批次清单.json'), encoding='utf-8'))
    jp = json.load(io.open(os.path.join(CORPUS, '台词.json'), encoding='utf-8'))
    tr_map = {}
    missing, mism = [], []
    for m in man['batches']:
        n = m['batch']
        p = os.path.join(WD, m['dst'])
        if not os.path.exists(p):
            missing.append(n)
            continue
        d = json.load(io.open(p, encoding='utf-8'))['tr']
        src = json.load(io.open(os.path.join(WD, m['src']), encoding='utf-8'))['lines']
        if [x['i'] for x in d] != [x['i'] for x in src]:
            mism.append(n)
        for row in d:
            tr_map[row['i']] = row.get('cn') or ''

    out, i, empty, chars = {}, 0, 0, 0
    for fn in sorted(jp):
        msgs = []
        for m in jp[fn]['messages']:
            cn = tr_map.get(i, None)
            if cn is None:
                cn = ''
            if not cn and m['text']:
                empty += 1
            chars += len(cn)
            msgs.append({'index': m['index'], 'kind': m['kind'], 'speaker': m['speaker'],
                         'voice': m['voice'], 'jp': m['text'], 'cn': cn,
                         'off': m.get('off'), 'len': m.get('len'), 'decl': m.get('decl')})
            i += 1
        out[fn] = {'code_start': jp[fn]['code_start'], 'messages': msgs}
    io.open(os.path.join(CORPUS, '译文.json'), 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))

    sub = os.path.join(CORPUS, '中文字幕')
    os.makedirs(sub, exist_ok=True)
    for fn, v in out.items():
        lines = []
        for m in v['messages']:
            tag = m['kind'] == 'title' and '【标题】' or (m['speaker'] or '旁白')
            lines.append('[%s] %s' % (tag, m['cn']))
            lines.append('    JP: %s' % (m['jp'] or ''))
        io.open(os.path.join(sub, fn.replace('.tob', '') + '.txt'), 'w', encoding='utf-8').write(
            '\n'.join(lines))

    rep = {'剧本数': len(out), '总条数': i, '未合并条数': i - len(tr_map),
           '缺批次': missing, '次序不符批次': mism, '空译条数（原文非空）': empty, '译文总字符': chars}
    io.open(os.path.join(CORPUS, '合并报告.json'), 'w', encoding='utf-8').write(
        json.dumps(rep, ensure_ascii=False, indent=1))
    for k, v in rep.items():
        print('%-16s %s' % (k, v))
    if strict and (missing or empty):
        print('!! 严格模式：存在缺批或缺译，验收不通过'); sys.exit(1)


if __name__ == '__main__':
    main()
