#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_13_v2handlers.py — 把 v_regions.tsv 的 V -> native 下标 展开为 handler VA (只读).

数据源:
  v_regions.tsv        (V, 既有定名, native下标, 被CALL目标, core串/过程串)
  handler_features.tsv (vec_index -> va)
用法: python -X utf8 _probe_13_v2handlers.py [V前缀过滤]
"""
import csv
import os
import sys

RE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\逆向引擎"

hf = list(csv.DictReader(open(os.path.join(RE, "handler_features.tsv"), encoding="utf-8"),
                         delimiter="\t"))
idx2va = {int(r["vec_index"]): r["va"] for r in hf}
print("handler_features rows=%d" % len(hf))

vr = list(csv.DictReader(open(os.path.join(RE, "v_regions.tsv"), encoding="utf-8"),
                         delimiter="\t"))
filt = sys.argv[1] if len(sys.argv) > 1 else None

for r in vr:
    if filt and filt.lower() not in (r.get("既有定名", "") or "").lower() and \
       filt.lower() not in r["V"].lower():
        continue
    nm = r.get("既有定名", "")
    nats = [x for x in (r.get("native下标", "") or "").split(",") if x.strip()]
    vas = []
    for n in nats:
        try:
            vas.append(idx2va.get(int(n), "?"))
        except ValueError:
            vas.append("?")
    print("=" * 70)
    print("V=%s  name=%r  core=%s..%s  proc_to=%s  instr=%s  strings=%r"
          % (r["V"], nm, r["core起"], r["core止"], r["过程止"],
             r.get("过程指令数", ""), r.get("过程串", "")))
    print("  CALL targets: %s" % r.get("被CALL目标", ""))
    print("  native (%d): %s" % (len(nats), ",".join(nats)))
    print("  native VA:   %s" % ",".join(vas))
