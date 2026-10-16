# -*- coding: utf-8 -*-
r"""lookup_terms.py —— 专名对照查询（**只读新米汉化的人名 / 地名写法**，不产出任何成句译文）

用户 2026-09-17 追加要求：新米汉化资源只允许使用其人名 / 地名；剧情正文一律不得使用。
本脚本据此只截取「日文专名出现处」的**短窗口**用于判读中文写法，输出内容不作为译文使用。

用法：
  python lookup_terms.py タカシ ギルティ ...
  python lookup_terms.py --file 待查清单.txt
"""
import io
import json
import os
import re
import sys

REF = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\参照\中日对照表.json'
WIN = 28


def short(jp, cn, term, win=WIN):
    i = jp.find(term)
    if i < 0:
        return None
    a = max(0, i - win)
    return jp[a:i + len(term) + win].replace('\n', ' ')


def main():
    args = sys.argv[1:]
    if '--file' in args:
        terms = [l.strip() for l in io.open(args[args.index('--file') + 1], encoding='utf-8')
                 if l.strip() and not l.startswith('#')]
    else:
        terms = args
    ref = json.load(io.open(REF, encoding='utf-8'))
    for term in terms:
        shown = 0
        print('### %s' % term)
        for r in ref:
            jp, cn = r.get('jp') or '', r.get('cn') or ''
            if term in jp and cn:
                s = short(jp, cn, term)
                print('   JP> %s' % s)
                print('   CN> %s' % cn[:len(s) + 6])
                shown += 1
                if shown >= 2:
                    break
        if not shown:
            print('   （新米对照表中无命中 → 该专名属 AfterStory 独有或写法不同，需自行定名）')


if __name__ == '__main__':
    main()
