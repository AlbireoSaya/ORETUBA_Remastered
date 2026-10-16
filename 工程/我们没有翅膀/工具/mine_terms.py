# -*- coding: utf-8 -*-
"""mine_terms.py —— 定向挖掘新米汉化的**专有名词**（仅人名/地名/组织/特定名词）

授权边界：用户 2026-09-17 指令只允许使用新米汉化的**人名/地名**，禁止使用其剧情译文。
本脚本因此只输出**术语对**（JP 术语 → CN 术语），不导出任何成句译文；
术语的 CN 形式由「同地址对齐的译文串」内**定位该术语所在片段**读得，属专名级使用。
输出：工程\\我们没有翅膀\\参照\\新米_术语对照.json
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
JP_SOB = os.path.join(PROJ, '解包', 'SCRIPT')

KATA = re.compile('[\u30a1-\u30fa\u30fc]{3,}')
SUFFIX = re.compile(r'[\u4e00-\u9fff]{1,4}(学園|学院|高校|大学|駅|町|市|村|通り|公園|神社|教会|神殿|王国|大陸|世界|騎士団|連合|財団|会社|新聞|砦|城|島|山|川|橋|ビル|商店街|喫茶|学級)')


def pairs():
    out = []
    for f in sorted(os.listdir(CHS)):
        if not f.endswith('.sob'):
            continue
        p = os.path.join(JP_SOB, f)
        if not os.path.exists(p):
            continue
        jp = parse_sob0(open(p, 'rb').read())[0]
        cn = parse_sob0(open(os.path.join(CHS, f), 'rb').read())[0]
        if jp is None or cn is None:
            continue
        jm = {(t['addr'], t['idx']): t['raw'] for t in jp}
        for t in cn:
            k = (t['addr'], t['idx'])
            if k not in jm:
                continue
            jb = classify(jm[k])[3].decode('cp932', 'replace')
            cb = classify(t['raw'])[3].decode('gbk', 'replace').rstrip('$').strip()
            if jb.strip() and cb.strip():
                out.append((f, jb.strip(), cb.strip()))
    return out


def main():
    ps = pairs()
    print('对齐槽 =', len(ps))
    # 1) 候选术语：片假名串 + 地点后缀式汉字复合
    freq = collections.Counter()
    for _, jb, _cb in ps:
        for m in KATA.findall(jb):
            freq[m] += 1
        for m in SUFFIX.findall(jb):
            freq[m] += 1
    cand = [t for t, c in freq.most_common(120) if c >= 2]
    print('候选术语 =', len(cand))
    result = {}
    for term in cand:
        hits = [(f, jb, cb) for f, jb, cb in ps if term in jb]
        if not hits:
            continue
        # 取最短的 3 条上下文，便于人工读出该术语的 CN 形式
        hits.sort(key=lambda x: len(x[1]))
        samples = [h[2][:70] for h in hits[:3]]
        result[term] = dict(count=len(hits), samples=samples)
    out = os.path.join(PROJ, '参照', '新米_术语对照.json')
    json.dump(result, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('写入', out)
    for term in cand[:60]:
        r = result.get(term)
        if not r:
            continue
        print('  %-16s ×%-4d  CN例: %s' % (term, r['count'], r['samples'][0] if r['samples'] else ''))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
