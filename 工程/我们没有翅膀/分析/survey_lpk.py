# -*- coding: utf-8 -*-
"""survey_lpk.py —— 全归档普查 + 日文文本量统计（只读）"""
import os
import re
import sys
import struct
import collections

TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
sys.path.insert(0, TOOLS)
import lpk_patch as LP  # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
LPKS = ['BGM.LPK', 'CHR.LPK', 'DATA.LPK', 'PIC.LPK', 'SCRIPT.LPK', 'SE.LPK', 'SYS.LPK', 'VOICE.LPK']


def main():
    for name in LPKS:
        path = os.path.join(GAME, name)
        try:
            lp = LP.load(path)
        except Exception as ex:  # noqa: BLE001
            print('%-12s 解析失败: %s' % (name, ex))
            continue
        ext = collections.Counter()
        for n, _ in lp['ents']:
            ext[('.' + n.rsplit('.', 1)[-1].lower()) if '.' in n else '(none)'] += 1
        print('%-12s 条目 %-5d 索引键=0x%08x flags=0x%02x  类型分布: %s'
              % (name, len(lp['ents']), lp['k1'], lp['flags'],
                 ', '.join('%s×%d' % (k, v) for k, v in ext.most_common(6))))
        if name == 'SCRIPT.LPK':
            print('             条目名样本:', [n for n, _ in lp['ents'][:6]])
            print('             结尾条目名:', [n for n, _ in lp['ents'][-6:]])
            groups = collections.Counter()
            for n, _ in lp['ents']:
                m = re.match(r'^(s\d\d[a-z]?)_', n)
                groups[m.group(1) if m else ('系统:' + n.split('.')[0])] += 1
            print('             剧情分组:', dict(sorted(groups.items())))


if __name__ == '__main__':
    main()
