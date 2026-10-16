# -*- coding: utf-8 -*-
"""assemble_cn.py —— 把分批译文装配成交付物（ISSUE-20260917-14）

输入：`语料\\可译清单.json`（槽位总表：script/seq/addr/cmd/sel/idx/kind/speaker/voice/td/body）
       `翻译工作区\\译文\\batch_NNN.tsv`（两列 slot<TAB>译文）
输出（交付物，入 git）：
  `汉化\\剧情汉化\\<脚本>.jsonl` —— 每行一槽：{seq, addr, kind, speaker, voice, td, jp, cn, trailer}
       `cn` 为**纯译文正文**（不含 `#说话人\\语音ID$&` 前缀与结尾 `$`；`trailer` 标记原串是否以 `$` 结尾）
  `汉化\\剧情汉化\\_总表.tsv`  —— `脚本  slot  kind  说话人  原文  译文`（人工审阅用）
  `汉化\\剧情汉化\\_交付统计.json` —— 覆盖度统计
用法：python -X utf8 assemble_cn.py
"""
import os
import re
import sys
import json
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJ, '语料', '可译清单.json')
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
OUT = os.path.join(PROJ, '汉化', '剧情汉化')


def main():
    rows = json.load(open(MANIFEST, encoding='utf-8'))
    by_slot = {r['slot']: r for r in rows}
    cn = {}
    batches = 0
    for p in sorted(glob.glob(os.path.join(TRANS, 'batch_*.tsv'))):
        batches += 1
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line or line.startswith('slot\t'):
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            cn[parts[0].strip()] = '\t'.join(parts[1:]).replace('\\n', '\n')

    os.makedirs(OUT, exist_ok=True)
    per_script = collections.defaultdict(list)
    for r in rows:
        per_script[r['script']].append(r)

    stat = dict(batches=batches, slots_total=len(rows), slots_done=0,
                chars_jp=0, chars_cn=0, scripts=len(per_script), missing_slots=[])
    total_tsv = [('脚本', 'slot', 'kind', '说话人', '原文', '译文')]
    for sc, rs in sorted(per_script.items()):
        out_rows = []
        for r in rs:
            c = cn.get(r['slot'])
            if c is None:
                stat['missing_slots'].append(r['slot'])
                c = ''
            else:
                stat['slots_done'] += 1
                stat['chars_cn'] += len(c)
            stat['chars_jp'] += len(r['body'])
            out_rows.append(dict(seq=r['seq'], addr=r['addr'], sel=r['sel'], idx=r['idx'], kind=r['kind'],
                                 speaker=r['speaker'], voice=r['voice'], td=r['td'],
                                 jp=r['body'], cn=c))
            total_tsv.append((sc, r['slot'], r['kind'], r['speaker'], r['body'], c))
        with open(os.path.join(OUT, sc + '.jsonl'), 'w', encoding='utf-8') as f:
            for x in out_rows:
                f.write(json.dumps(x, ensure_ascii=False) + '\n')
    with open(os.path.join(OUT, '_总表.tsv'), 'w', encoding='utf-8', newline='') as f:
        for t in total_tsv:
            f.write('\t'.join(str(x).replace('\t', ' ').replace('\r', ' ').replace('\n', '\\n')
                              for x in t) + '\n')
    stat['missing_slots'] = stat['missing_slots'][:50]
    stat['coverage'] = round(100.0 * stat['slots_done'] / max(1, stat['slots_total']), 2)
    json.dump(stat, open(os.path.join(OUT, '_交付统计.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('批次数 = %d' % batches)
    print('槽位覆盖 = %d / %d（%.2f%%）' % (stat['slots_done'], stat['slots_total'], stat['coverage']))
    print('字符：原文 %d → 译文 %d' % (stat['chars_jp'], stat['chars_cn']))
    print('脚本数 = %d；未译槽 %d' % (stat['scripts'], stat['slots_total'] - stat['slots_done']))
    print('输出 =', OUT)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
