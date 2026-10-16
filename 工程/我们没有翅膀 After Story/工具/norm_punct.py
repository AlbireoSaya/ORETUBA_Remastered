# -*- coding: utf-8 -*-
r"""norm_punct.py —— 全批标点字符归一（第二道：把"日文码位/近形字符"统一到规定字形）

规则（依据通用术语表 §6.1）：
  * 破折号：`─`(U+2500) / `―`(U+2015) / `‐`(U+2010) / `‒`(U+2012) / `−`(U+2212) → **`—`(U+2014)**
    （原文成对出现，逐个替换即保持 1:1，不改变标点数量）
  * 波线：`〜`(U+301C) → **`～`(U+FF5E)**
  * 中点：`・`(U+30FB) → **`·`(U+00B7)**
  * 全角空格：`　`(U+3000) → 删除
**不动**：`ー`(U+30FC 片假名长音)、`－`(U+FF0D 全角连字符，用于 Ｒ－ウィング 等)、`·`(U+00B7 已正确)、`—`/`…`。

用法：python norm_punct.py [批次号 ...]   # 缺省全部
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')

DASH = ['\u2500', '\u2015', '\u2010', '\u2012', '\u2212']
WAVE = '\u301c'          # 〜 JP 波线
WAVE_CN = '\uff5e'       # ～ 规定字形
MIDDOT = '\u30fb'        # ・ JP 中点
MIDDOT_CN = '\u00b7'     # · 规定字形
IDSP = '\u3000'          # 全角空格


def norm(s):
    n = 0
    for ch in DASH:
        if ch in s:
            n += s.count(ch)
            s = s.replace(ch, '\u2014')
    for k, v in ((WAVE, WAVE_CN), (MIDDOT, MIDDOT_CN), (IDSP, '')):
        if k in s:
            n += s.count(k)
            s = s.replace(k, v)
    return s, n


def main():
    which = [int(x) for x in sys.argv[1:] if x.isdigit()]
    if not which:
        which = list(range(1, 24))
    tot = 0
    for b in which:
        p = os.path.join(WD, '批次%02d_译文.json' % b)
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding='utf-8'))
        k = 0
        for row in d['tr']:
            cn = row.get('cn') or ''
            new, n = norm(cn)
            if n:
                row['cn'] = new
                k += n
        if k:
            io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
        print('批次%02d：归一 %d 个字符' % (b, k))
        tot += k
    print('合计 %d 个字符' % tot)


if __name__ == '__main__':
    main()
