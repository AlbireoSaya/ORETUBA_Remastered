#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_18_argstats.py — 全语料统计立绘相关命令的实参向量分布 (只读).

目的: 判定"脚本实参是否携带层序(H1)" —— 若任一实参位出现 1..10 值域且与 PSV :Priority 无关,
      即为层序候选; 若各实参位值域只有 {0, 1, -1, 名字串, 小整数(位置/模式)} 且无 1..10 语义, H1 否定.

用法: python -X utf8 _probe_18_argstats.py 0x1C43C 0x14084 0x15A04 0x14F98 0x1C5B0 0x186C8 0x18B74
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_17_scene_args import calls_of, SCRIPTDIR
from _probe_12_funclib import Sob

targets = set(int(x, 0) for x in sys.argv[1:])
if not targets:
    print("usage: ... <V> [<V> ...]")
    sys.exit(1)

# arg[i] -> Counter(value)
per_pos = {t: collections.defaultdict(collections.Counter) for t in targets}
sites = collections.Counter()
files = 0
for fn in sorted(os.listdir(SCRIPTDIR)):
    if not fn.endswith(".sob"):
        continue
    try:
        sob = Sob(os.path.join(SCRIPTDIR, fn))
    except Exception:
        continue
    if not sob.maps[3]:
        continue
    files += 1
    for pos, t, args in calls_of(sob, targets):
        sites[t] += 1
        for i, av in enumerate(args):
            per_pos[t][i][av] += 1

print("扫描场景文件(含 maps[3])=%d" % files)
for t in sorted(targets):
    print("=" * 70)
    print("V=0x%X  调用站总数=%d" % (t, sites[t]))
    for i in sorted(per_pos[t]):
        c = per_pos[t][i]
        top = c.most_common(12)
        kinds = collections.Counter()
        for k, n in c.items():
            if k.startswith("imm "):
                v = int(k[4:])
                kinds["imm:0" if v == 0 else
                      "imm:-1" if v == 0xFFFFFFFF else
                      ("imm:1..10" if 1 <= v <= 10 else "imm:other")] += n
            elif k.startswith("VAR#"):
                kinds["VAR"] += n
            else:
                kinds[k.split("=")[0]] += n
        print("  arg[%d] 取值种数=%d  值域分档=%s" % (i, len(c), dict(kinds)))
        for k, n in top:
            print("      %-40s x%d" % (k[:40], n))
