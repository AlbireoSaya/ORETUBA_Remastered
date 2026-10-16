# -*- coding: utf-8 -*-
r"""scan_names.py —— 扫描 AfterStory 全部 .tob 的「声明串」与 op 分布

用途：
  1. 统计消息 op 分布（判断本作是否有名字框）；
  2. 提取所有 `01 01 <u16 L> <内容> 00` 声明串，剔除资源路径（含反斜杠 / 扩展名）后，
     列出疑似人名·地名·标签，作为作品术语表的**证据来源**（替代 R 版只靠说话人标签取证的做法）。

用法：python scan_names.py
"""
import io
import json
import os
import re
import struct
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '语料', '原文')
PAT = re.compile(rb'\x01\x01(..)')


def collect():
    names, allstr = Counter(), Counter()
    ops = Counter()
    per_file_names = {}
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith('.tob'):
            continue
        raw = io.open(os.path.join(SRC, fn), 'rb').read()
        got = []
        for m in PAT.finditer(raw):
            L = struct.unpack('<H', m.group(1))[0]
            if L == 0 or L > 80:
                continue
            d = raw[m.start() + 4:m.start() + 4 + L]
            if len(d) != L or d[-1] != 0:
                continue
            body = d[:-1]
            try:
                s = body.decode('cp932')
            except UnicodeDecodeError:
                continue
            if '\\' in s or '.' in s or '/' in s:
                continue                      # 资源路径
            if not s or all(0x20 <= c < 0x7f for c in body):
                continue                      # 纯 ASCII（脚本内部命令/变量）
            allstr[s] += 1
            got.append(s)
        if got:
            per_file_names[fn] = got
    try:
        data = json.load(io.open(os.path.join(os.path.dirname(HERE), '语料', '台词.json'),
                                 encoding='utf-8'))
        ops = Counter(m['op'] for v in data.values() for m in v['messages'])
    except FileNotFoundError:
        pass
    return allstr, ops, per_file_names


def main():
    allstr, ops, per_file = collect()
    print('消息 op 分布:', ops.most_common())
    print()
    print('非资源类声明串共 %d 种 / %d 处；前 60 种：' % (len(allstr), sum(allstr.values())))
    for s, c in allstr.most_common(60):
        print('   %-22s %5d' % (s, c))
    out = os.path.join(os.path.dirname(HERE), '语料', '声明串统计.json')
    io.open(out, 'w', encoding='utf-8').write(json.dumps(
        {'counts': dict(allstr), 'per_file': per_file}, ensure_ascii=False, indent=1))
    print('\n已写出', out)


if __name__ == '__main__':
    main()
