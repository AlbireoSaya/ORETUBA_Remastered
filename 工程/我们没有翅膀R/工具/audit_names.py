# -*- coding: utf-8 -*-
"""审计：构建产物里所有「名字声明串」的尾部填充情况（ISSUE-ORETUBAR-R）。"""
import os, re, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as LP

LPK = r'E:\ZCode Workspace\Galgame\_game_ascii\ORETSUBA_R\SCRIPT.LPK'
SP = ' '
FW = '\u3000'


def is_name_text(t):
    for c in t:
        if 0x4E00 <= ord(c) <= 0x9FFF:
            continue
        if c in (SP, FW) or c == '\u30fb':
            continue
        if 'Ａ' <= c <= 'Ｚ':
            continue
        return False
    return True


def main():
    lp = LP.load(LPK)
    files = sorted(n for n, _ in lp['ents'] if n.lower().endswith('.tob'))
    stat = defaultdict(Counter)
    example = {}
    for fn in files:
        raw = LP.read_entry(lp, fn)['plain']
        for m in re.finditer(rb'\x01\x01', raw):
            j = m.start()
            if j + 4 > len(raw):
                continue
            ln = raw[j + 2] | (raw[j + 3] << 8)
            if not (2 < ln < 64):
                continue
            body = raw[j + 4:j + 4 + ln]
            if body[-1:] != b'\x00':
                continue
            core = body[:-1]
            if not core:
                continue
            try:
                t = core.decode('gbk')
            except Exception:
                continue
            if not is_name_text(t):
                continue
            base = t.rstrip(SP + FW)
            if not base:
                continue
            nh = len(t) - len(t.rstrip(SP))
            nf = len(t) - len(t.rstrip(FW))
            stat[base][(nh, nf)] += 1
            example.setdefault(base, (fn, j, ln, body))

    print('名字种类: %d' % len(stat))
    print()
    print('=== 有尾部填充的（半角空格数, 全角空格数）===')
    bad = []
    for name, c in sorted(stat.items(), key=lambda x: -sum(x[1].values())):
        tot = sum(c.values())
        pads = [(k, v) for k, v in c.items() if k != (0, 0)]
        if not pads:
            continue
        bad.append((name, tot, pads))
        fn, j, ln, body = example[name]
        print('  %-12s 共 %-5d 条  填充分布=%s' % (name, tot, dict(pads)))
        print('      样例: %s @%d body=%s' % (fn, j, body.hex(' ')))
    print()
    print('有填充的名字: %d 种' % len(bad))
    print('无填充的名字: %d 种' % (len(stat) - len(bad)))


if __name__ == '__main__':
    main()
