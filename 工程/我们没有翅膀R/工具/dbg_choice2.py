# -*- coding: utf-8 -*-
"""调试：选择支跳转指令的合法性校验（ISSUE-ORETUBAR-R）。"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as LP
import tob_extract as EX


def analyze(path, name, tag):
    raw = open(path, 'rb').read() if path else None
    return raw


def main():
    for lpk_path, tag in ((r'E:\ZCode Workspace\Galgame\ORETSUBA_R\ORETSUBA_R\SCRIPT.LPK', '当前部署'),
                          (r'E:\ZCode Workspace\Galgame\临时\_test\SCRIPT.LPK', '实验版')):
        print('=' * 66)
        print(tag, lpk_path)
        lp = LP.load(lpk_path)
        for name in ('s01_12b.tob', 's01_13b.tob'):
            raw = LP.read_entry(lp, name)['plain']
            info = EX.parse_header(raw)
            cs = info['code_start']
            lbl = {l[0]: l[1] for l in info['labels']}
            print('  %s: %d 字节 code_start=%d' % (name, len(raw), cs))
            print('    标签: %s' % lbl)
            # 校验所有 `02 ff 00 <addr>` 跳转目标是否在文件内
            bad = 0
            tot = 0
            for m in re.finditer(rb'\x02\xff\x00(....)', raw, re.S):
                addr = int.from_bytes(m.group(1), 'little')
                tot += 1
                if cs + addr >= len(raw):
                    bad += 1
                    print('      ✘ 跳转越界 @%d addr=%d 目标=%d (文件 %d)'
                          % (m.start(), addr, cs + addr, len(raw)))
            print('    跳转指令 %d 条，越界 %d 条' % (tot, bad))
            # 校验标签目标处的字节形态
            for k, v in lbl.items():
                t = cs + v
                if t >= len(raw):
                    print('      ✘ 标签 %s 越界' % k)
                else:
                    print('      标签 %-8s → @%d，目标字节: %s' % (k, t, raw[t:t + 16].hex(' ')))
        print()


if __name__ == '__main__':
    main()
