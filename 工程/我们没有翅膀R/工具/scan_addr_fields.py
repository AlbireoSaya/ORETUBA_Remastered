# -*- coding: utf-8 -*-
r"""穷举扫描：TOB 内所有「疑似文件内地址」的 u32（ISSUE-ORETUBAR-R）。

对原始文件的每个 4 字节对齐/非对齐位置，读 u32：
  若 code_start <= v < len(file)（或 0 < v < len(code)），则视为「疑似地址」。
记录其 (偏移, 值) 及其「所指位置的特征」（是否命令起点 5b XX / 是否消息尾部等）。
用于发现 tob_rewrite 的地址模型**未覆盖**的字段。
"""
import os, re, struct, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import tob_extract as EX


def scan(raw, code_start):
    n = len(raw)
    out = []
    for i in range(0, n - 4):
        v = struct.unpack_from('<I', raw, i)[0]
        if v == 0:
            continue
        target = code_start + v
        if 0 < v and target < n:
            tgt = raw[target:target + 8]
            kind = []
            if len(tgt) >= 3 and tgt[0] == 0x5b:
                kind.append('cmd5b')
            if len(tgt) >= 18 and tgt[6:7] == b'\x01' and tgt[11:14] == b'\x01\x01\x00':
                kind.append('tail18')
            if target < code_start:
                kind.append('in-header')
            out.append((i, v, target, '|'.join(kind) or '-'))
    return out


def main():
    P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P, '临时', '_s01_02c_orig.tob')
    raw = open(path, 'rb').read()
    info = EX.parse_header(raw)
    cs = info['code_start']
    print('文件 %s: %d 字节 code_start=%d 消息数=%d' % (os.path.basename(path), len(raw), cs, info['B']))
    hits = scan(raw, cs)
    print('疑似地址 u32: %d 处' % len(hits))
    from collections import Counter
    c = Counter(h[3] for h in hits)
    print('按目标特征:', c.most_common())
    print()
    # tob_rewrite 已知的三类字段位置
    fields, census = __import__('tob_rewrite').collect_address_fields(raw)
    known = set(p for p, v, k in fields)
    print('tob_rewrite 已知字段数: %d（%s）' % (len(fields), census))
    unknown = [h for h in hits if h[0] not in known]
    print('**未被 tob_rewrite 覆盖的疑似地址: %d 处**' % len(unknown))
    print()
    for i, v, t, k in unknown[:40]:
        print('  @%-6d v=%-7d → 文件内 %-7d 特征=%s  前 8 字节: %s'
              % (i, v, t, k, raw[max(0, i - 8):i + 12].hex(' ')))
    if len(unknown) > 40:
        print('  ...（共 %d 处）' % len(unknown))


if __name__ == '__main__':
    main()
