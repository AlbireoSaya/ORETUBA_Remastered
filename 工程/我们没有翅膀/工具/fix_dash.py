# -*- coding: utf-8 -*-
"""fix_dash.py —— 统一感叹词拖音标记（ISSUE-20260917-14）

作品级裁决：**感叹词/语气词的拖音**（あー、ふーん、うーん、おー 等）一律用 `～`；
`——` 只留给「句尾拖长」（ただいまー → 我回来了——）与破折号/中断。
本脚本只改「汉字感叹词 + `——` + 标点」这一模式，避免误伤真正的破折号。

用法：python -X utf8 fix_dash.py batch_011 batch_012 ...
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')

# 感叹词（单字/双字）+ —— + 标点  →  感叹词 + ～
PAT = re.compile(r'([啊哦唔嗯哈呼诶欸咦呀哎喂哟咯嘛]|哈哈|啊啊)——(?=[，。！？、…])')


def main():
    total = 0
    names = sys.argv[1:]
    if not names:
        import glob as _g
        names = sorted(os.path.basename(x)[:-4] for x in _g.glob(os.path.join(TRANS, 'batch_*.tsv')))
    for name in names:
        p = os.path.join(TRANS, name + '.tsv')
        if not os.path.exists(p):
            print('%s: 无译文，跳过' % name)
            continue
        out, n = [], 0
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            cn = '\t'.join(line.split('\t')[1:])
            new, k = PAT.subn(r'\1～', cn)
            n += k
            out.append(line.split('\t')[0] + '\t' + new)
        open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
        print('%s: 感叹词拖音 —— → ～ 共 %d 处' % (name, n))
        total += n
    print('合计 %d 处' % total)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
