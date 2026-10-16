# -*- coding: utf-8 -*-
"""cn_check.py —— 核实 SCRIPT_CHS 中「原版串之外」的追加串是中文译文（只读）"""
import os
import re
import collections

GAME = r'D:\Gal\[Navel]我们没有翅膀'
CHS = os.path.join(GAME, 'SCRIPT_CHS')
RUN = re.compile(rb'(?:[\x81-\xfe][\x40-\xfe]){3,}')
HIRA = re.compile('[\u3041-\u309f\u30a1-\u30fa]')
# 中文高频功能字（真中文句子几乎必含其一，SJIS→GBK 乱码几乎不会出现）
CN_FUNC = set('的了是我你他她不在有就都也很和这那吗么呢吧们说起来去过后着被把让给对向从所以为与而且但是个一二三上下里内外时候')


def main():
    cnt = collections.Counter()
    samples = []
    for fn in sorted(os.listdir(CHS)):
        p = os.path.join(CHS, fn)
        if not os.path.isfile(p):
            continue
        b = open(p, 'rb').read()
        for m in RUN.finditer(b):
            r = m.group(0)
            if len(r) < 8:
                continue
            j = r.decode('cp932', 'replace')
            if HIRA.search(j):
                cnt['JP'] += 1
                continue
            g = r.decode('gbk', 'replace')
            if len(set(g) & CN_FUNC) >= 2:
                cnt['CN'] += 1
                if len(samples) < 12 and len(g) > 12:
                    samples.append((fn, m.start(), g[:70]))
            else:
                cnt['?'] += 1
    print('=== SCRIPT_CHS 全文段分类（严格判据）===')
    print('  日文（cp932 解出假名）段：%d' % cnt['JP'])
    print('  中文（GBK 且含 >=2 个中文高频功能字）段：%d' % cnt['CN'])
    print('  未定（既无假名也无中文功能字，多为含汉字/记号/路径的短串）：%d' % cnt['?'])
    print('\n=== 中文样本 ===')
    for fn, off, s in samples:
        print('  %-16s @%-7d %s' % (fn, off, s))


if __name__ == '__main__':
    main()
