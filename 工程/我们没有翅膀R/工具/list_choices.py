# -*- coding: utf-8 -*-
"""列出各选择支场景的实际选项文本（中文，ISSUE-ORETUBAR-SAVE）。"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as LP

LPK = r'E:\ZCode Workspace\Galgame\_game_ascii\ORETSUBA_R\SCRIPT.LPK'

# 攻略涉及的选择支场景（按剧情顺序）
SCENES = ['s01_02c.tob', 's01_02e.tob', 's01_03b.tob', 's01_04e.tob', 's01_04l.tob',
          's02_03b.tob', 's02_05a.tob', 's02_05e.tob', 's02_06b.tob', 's02_06f.tob',
          's03_03b.tob', 's03_03i.tob', 's03_05c.tob', 's03c_01d.tob',
          's01_08c0.tob', 's01_08d0.tob', 's01_08d4.tob', 's01_09c0.tob',
          's01_12b.tob', 's01_13b.tob', 's04_03e.tob', 's04_05i.tob', 's02_10c.tob', 's03_04b.tob']


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
            if 2 <= len(t) <= 40 and not t.startswith('_'):
                opts.append((j, t))
        if opts:
            print('=== %s ===' % fn)
            for j, t in opts[:8]:
                print('   @%-6d %s' % (j, t))
            print()


if __name__ == '__main__':
    main()
