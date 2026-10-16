# -*- coding: utf-8 -*-
"""fix_first_person.py —— 第一人称分层统一（ISSUE-20260917-14）

设计口径：**只单向强制**——仅把「名单内角色却写成『我』」改回「俺」；
   反向（名单外角色写了「俺」）**只报告不自动改**，避免误伤正当的粗犷台词。

⚠️ 判据必须包含**汉字「俺」**：本篇原文粗犷男性自称实测汉字「俺」978 处、平假名「おれ」仅 1 处；
   只看平假名会漏掉 99% 的槽（2026-09-18 修正）。

作品级裁决（依据 R 版成品实测：`俺` 主要给隼人 92 处、咲夜 22 处，鷹志仅 12 处）：
  · **粗犷男性**（隼人 / 咲夜 / 狩男 / 和馬 / バニィＤ）：`おれ` → **俺**
  · **其余角色**（鷹志 / 鷲介 / 翔 / …）：`おれ` → **我**（通用层 §2.1 默认）
  · **旁白（无说话人标签）**：不改动（POV 无法从标签判定），仅提示。

命中条件（高精度，避免误伤）：
  `おれ` 出现在日文原文 **且** 原文不含 `僕` / `私` / `わし`（同槽多自称会让归属不可判定）→ 才改写。
  改写时避开「我们 / 我方 / 自我 / 我慢」等非人称用法。

用法：
  python -X utf8 fix_first_person.py --report      # 只统计
  python -X utf8 fix_first_person.py --apply       # 执行回改
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
MANIFEST = os.path.join(PROJ, '语料', '可译清单.json')

# 粗犷男性名单（作品层 §三之二 的权威口径；后续如有新人设补充，只在此处加）
ROUGH = {'隼人', '咲夜', '狩男', '和馬', 'バニィＤ', 'バニィD',
         'チケドン', 'ＬＲ２００１', 'マルチネス', 'ドレッド頭', 'コンドル',
         'レイヴン'}
# 只改「独立的『我』」：排除 我们/我方/自我/我慢 等非人称或复合用法。
# ⚠️ 2026-09-18 修正：原写作 `我(?=们|方|自|慢)`，方向反了——它只命中「我们」并改成「俺们」，
#    真正的「我」一个都没改（连跑 3 次统计值恒为 351 即此故）。正确写法是「我」后不接这些字。
STANDALONE_WO = re.compile(r'(?<!自)我(?!们|方|自|慢)')

# 例外槽：译文里的「俺」是在**讨论/引用自称本身**（元语言用法），不是说话人的第一人称。
# 机械回扫会误伤，故按槽号硬保护（依据：作品层术语表 §三之三十六 与本次定点专项裁决）。
EXCEPT_SLOTS = {'s01_14l.sob#204', 's03_03e.sob#355'}


def main():
    apply = '--apply' in sys.argv
    man = json.load(open(MANIFEST, encoding='utf-8'))
    meta = {r['slot']: r for r in man}
    to_an, to_wo = [], []
    for p in sorted(glob.glob(os.path.join(TRANS, 'batch_*.tsv'))):
        rows = []
        changed = 0
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            slot = line.split('\t')[0]
            cn = '\t'.join(line.split('\t')[1:])
            m = meta.get(slot)
            if not m:
                rows.append(slot + '\t' + cn)
                continue
            jp, spk = m['body'], m['speaker']
            if slot in EXCEPT_SLOTS:
                rows.append(slot + '\t' + cn)
                continue
            if ('おれ' in jp or '俺' in jp) and not any(x in jp for x in ('僕', '私', 'わし')):
                if spk in ROUGH:
                    if '我' in cn and '俺' not in cn:
                        to_an.append((slot, spk, jp[:24], cn[:24]))
                        if apply:
                            cn = STANDALONE_WO.sub('俺', cn)
                            changed += 1
                elif spk and spk != '':
                    if '俺' in cn:
                        to_wo.append((slot, spk, jp[:24], cn[:24]))
                        if apply:
                            cn = cn.replace('俺', '我')
                            changed += 1
            rows.append(slot + '\t' + cn)
        if apply and changed:
            open(p, 'w', encoding='utf-8', newline='').write('\n'.join(rows) + '\n')
            print('%s: 回改 %d 处' % (os.path.basename(p), changed))
    print('\n【统计】应为「俺」却写成「我」的台词槽（粗犷男性）= %d' % len(to_an))
    for s in to_an[:6]:
        print('   ', s[0], s[1], '| JP:', s[2], '| CN:', s[3])
    print('【统计】应为「我」却写成「俺」的台词槽（其他角色）= %d' % len(to_wo))
    for s in to_wo[:6]:
        print('   ', s[0], s[1], '| JP:', s[2], '| CN:', s[3])
    if not apply:
        print('\n（--report 模式，未修改任何文件；确认后用 --apply 执行）')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()