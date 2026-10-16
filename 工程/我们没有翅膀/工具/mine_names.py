# -*- coding: utf-8 -*-
"""mine_names.py —— 定向挖掘「新米汉化」的人名/地名（ISSUE-20260917-14）

授权边界（用户 2026-09-17 指令）：**只允许使用新米汉化的人名/地名**，
**不得使用其剧情译文**。本脚本因此只做「专名级」对照：
  · 以**代码地址（addr）+ 序号（idx）**做键，把原版 JP 串与 SCRIPT_CHS 的 CN 串配对
    （新米只改写了字符串指针、保留全部代码与地址，故地址键一一对应）；
  · 只输出**短串**（章节标题、说话人显示名、地名、UI 词）供主代理人工裁决；
  · 剧情正文（长句）**不导出、不使用**。
输出：工程\\我们没有翅膀\\参照\\新米_专名候选.tsv
"""
import os
import re
import sys
import json
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from extract_sob0 import parse_sob0, classify  # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
CHS = os.path.join(GAME, 'SCRIPT_CHS')
JP_DIR = os.path.join(PROJ, '语料', '原文')
OUT = os.path.join(PROJ, '参照', '新米_专名候选.tsv')
KANA = re.compile('[\u3041-\u309f\u30a0-\u30fa]')


def slots(path, enc='cp932'):
    d = open(path, 'rb').read()
    texts, info = parse_sob0(d)
    if texts is None:
        return {}
    out = {}
    for t in texts:
        kind, spk, voice, body = classify(t['raw'])
        out[(t['addr'], t['idx'])] = dict(kind=kind, speaker=spk, voice=voice,
                                          body=body.decode(enc, 'replace'),
                                          raw=t['raw'])
    return out


def main():
    maxlen = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    rows = []
    stat = collections.Counter()
    for scr in sorted(os.listdir(CHS)):
        if not scr.endswith('.sob'):
            continue
        jp = slots(os.path.join(PROJ, '解包', 'SCRIPT', scr))
        cn = slots(os.path.join(CHS, scr), enc='gbk')
        for k, v in jp.items():
            c = cn.get(k)
            if not c:
                continue
            jb, cb = v['body'].strip(), c['body'].strip().rstrip('$').strip()
            if not jb or not cb:
                continue
            stat['paired'] += 1
            # 只收「短串」：章节标题 / 显示名 / 地名 / UI 词
            if len(jb) <= maxlen and (KANA.search(jb) or re.search('[\u4e00-\u9fff]', jb)):
                rows.append((scr, '%d' % v.get('addr', k[0]), k[1], v['kind'],
                             v['speaker'], jb, cb))
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write('script\taddr\tidx\tkind\tspeaker\tJP\tCN\n')
        for r in rows:
            f.write('\t'.join(str(x).replace('\t', ' ').replace('\n', '\\n') for x in r) + '\n')
    print('配对槽位 =', stat['paired'])
    print('短串候选 =', len(rows))
    print('输出 =', OUT)
    # 控制台抽样
    for r in rows[:25]:
        print('  %-14s %-6s %-9s JP=%-24s CN=%s' % (r[0], r[1], r[3], r[5][:24], r[6][:24]))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
