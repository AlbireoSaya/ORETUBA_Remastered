# -*- coding: utf-8 -*-
"""check_terms.py —— 术语一致性总检（ISSUE-20260917-14 收尾专项）

做法：解析作品层 `作品skill\术语表.md` 的全部 markdown 表格，取出「日文原词 → 中文译法」对；
     再扫全部批次译文，对**原文含该原词**的槽，检查译文是否含该定译；不含即报「疑似不一致」。

用法：
  python -X utf8 check_terms.py            # 汇总：每个词条的违规槽数
  python -X utf8 check_terms.py --detail    # 附每条前若干违规槽的原文/译文
  python -X utf8 check_terms.py --term ポッポ   # 只查某词条
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
GLOSS = os.path.join(PROJ, '作品skill', '术语表.md')

# 这些定译值不是「可校验的译法」，跳过
SKIP_CN = re.compile(r'不译|保留|待确认|^—$|^$|原样|同上|见上|同上条')


def parse_glossary():
    """返回 [(日文原词, 中文译法, 所在小节)]，按小节标题分组。"""
    pairs, section = [], ''
    header = None
    for line in open(GLOSS, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('#'):
            section = line.lstrip('#').strip()
            header = None
            continue
        if not line.startswith('|'):
            header = None
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
            continue
        try:
            i_jp = next(i for i, h in enumerate(header) if '原词' in h or '日文' in h)
        except StopIteration:
            header = None
            continue
        i_cn = None
        for i, h in enumerate(header):
            if '中文译法' in h or h == '译法' or '中文' in h:
                i_cn = i
                break
        if i_cn is None or max(i_jp, i_cn) >= len(cells):
            continue
        jp, cn = cells[i_jp], cells[i_cn]
        # 剥掉 markdown 装饰（**加粗**、`代码`、*斜体*），否则永远匹配不上
        cn = re.sub(r'[*`]', '', cn).strip()
        jp = re.sub(r'[*`]', '', jp).strip()
        if not jp or not cn or SKIP_CN.search(cn):
            continue
        if jp == cn:          # 同形汉字，无需校验
            continue
        pairs.append((jp, cn, section))
    return pairs


def load_corpus():
    """[(batch, slot, jp, cn)]"""
    import json
    man = json.load(open(os.path.join(PROJ, '语料', '可译清单.json'), encoding='utf-8'))
    meta = {r['slot']: r['body'] for r in man}
    rows = []
    for p in sorted(glob.glob(os.path.join(TRANS, 'batch_*.tsv'))):
        b = os.path.basename(p)[:-4]
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            slot, cn = line.split('\t', 1)
            rows.append((b, slot, meta.get(slot, ''), cn))
    return rows


def main():
    detail = '--detail' in sys.argv
    only = None
    if '--term' in sys.argv:
        only = sys.argv[sys.argv.index('--term') + 1]
    pairs = parse_glossary()
    if only:
        pairs = [p for p in pairs if p[0] == only]
    corpus = load_corpus()
    print('词条 %d 条；语料 %d 槽' % (len(pairs), len(corpus)))
    bad_total = 0
    reports = []
    for jp, cn, sec in pairs:
        hits, bad = [], []
        for b, slot, jbody, cbody in corpus:
            if jp not in jbody:
                continue
            hits.append(slot)
            if cn not in cbody:
                bad.append((b, slot, jbody, cbody))
        if bad:
            bad_total += len(bad)
            reports.append((len(bad), len(hits), jp, cn, sec, bad))
    reports.sort(reverse=True)
    for nbad, nhit, jp, cn, sec, bad in reports:
        print('\n[%s] %s → %s   违规 %d / 命中 %d' % (sec, jp, cn, nbad, nhit))
        if detail:
            for b, slot, jbody, cbody in bad[:4]:
                print('    %s %s' % (b, slot))
                print('      JP: %s' % jbody[:60].replace('\n', '\\n'))
                print('      CN: %s' % cbody[:60])
    print('\n合计违规槽 %d（词条 %d 条）' % (bad_total, len(reports)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()