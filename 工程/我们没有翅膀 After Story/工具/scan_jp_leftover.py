# -*- coding: utf-8 -*-
r"""scan_jp_leftover.py —— 扫描译文中的"日文形残留"（该用中文定名却留着日文写形）

对 `语料\译名锁定表.json` 中**中日写法不同**的条目（说话人名 + 正文专名/术语）逐一扫描：
若译文里直接出现日文写形（如 榴樺／羽田鷹志／ガルーダ），即为漏改。

用法：python scan_jp_leftover.py
"""
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')
KANA_OK = ('あたとど', 'いもももと', 'いももと', 'みぜＬＯＶＥる')
# 中日同形且本身即合法中文词者，不作"日文形残留"处理
ZH_SAME = {'一同', '少女', '女子', '男子', '子供', '声', '京', '優', '翔', '三人', '全員',
           '母親', '中年女性', '平民', '本文', '件名'}


def main():
    lock = json.load(io.open(os.path.join(PROJ, '语料', '译名锁定表.json'), encoding='utf-8'))
    pairs = {}
    for src in ('speakers', 'terms'):
        for jp, zh in lock[src].items():
            if jp != zh and len(jp) >= 2 and jp not in ZH_SAME:
                pairs[jp] = zh
    hits = {}
    for f in sorted(glob.glob(os.path.join(WD, '批次*_译文.json'))):
        d = json.load(io.open(f, encoding='utf-8'))
        for row in d['tr']:
            cn = row.get('cn') or ''
            if any(k in cn for k in KANA_OK):
                continue
            for jp, zh in pairs.items():
                if jp in cn:
                    hits.setdefault(jp, []).append((os.path.basename(f), row['i'], cn[:44]))
    print('对照条目 %d 组；扫描已完成批次 %d 个'
          % (len(pairs), len(glob.glob(os.path.join(WD, '批次*_译文.json')))))
    if not hits:
        print('  ✅ 未发现日文形残留')
        return
    for jp, v in sorted(hits.items(), key=lambda x: -len(x[1])):
        print('  ⚠ %s（应作 %s）：%d 处  例：%s | %s'
              % (jp, pairs[jp], len(v), v[0][0], v[0][2]))


if __name__ == '__main__':
    sys.exit(main())
