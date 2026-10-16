# -*- coding: utf-8 -*-
"""提取各选择支场景的选项文本（中文，ISSUE-ORETUBAR-SAVE）。"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as LP

LPK = r'E:\ZCode Workspace\Galgame\_game_ascii\ORETSUBA_R\SCRIPT.LPK'
SCENES = ['s01_02c.tob', 's01_02e.tob', 's01_03b.tob', 's01_04e.tob', 's01_04l.tob',
          's02_03b.tob', 's02_05a.tob', 's02_05e.tob', 's02_06b.tob', 's02_06f.tob',
          's03_03b.tob', 's03_03i.tob', 's03_05c.tob', 's03c_01d.tob',
          's01_08c0.tob', 's01_08d0.tob', 's01_08d4.tob', 's01_09c0.tob',
          's01_12b.tob', 's01_13b.tob', 's04_03e.tob', 's04_05i.tob', 's02_10c.tob', 's03_04b.tob']


def is_opt(t):
    if '\\' in t or '/' in t:
        return False
    if re.search(r'\.[A-Za-z]{3}$', t):
        return False
    if len(t) < 3 or len(t) > 30:
        return False
    if re.fullmatch(r'[A-Za-z0-9_]+', t):
        return False
    return True


def main():
    lp = LP.load(LPK)
    for fn in SCENES:
        try:
            raw = LP.read_entry(lp, fn)['plain']
        except Exception:
            continue
        opts = []
        for m in re.finditer(rb'\x01\x01(..)', raw):
            j = m.start()
            ln = raw[j + 2] | (raw[j + 3] << 8)
            if not (6 < ln < 90):
                continue
            body = raw[j + 4:j + 4 + ln]
            if body[-1:] != b'\x00':
                continue
            try:
                t = body[:-1].decode('gbk')
            except Exception:
                continue
            t = t.strip('\u3000 ')
            if is_opt(t):
                opts.append(t)
        if opts:
            print('=== %s ===' % fn)
            for t in opts[:8]:
                print('   %s' % t)
            print()


if __name__ == '__main__':
    main()
