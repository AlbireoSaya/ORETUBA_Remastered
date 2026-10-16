# -*- coding: utf-8 -*-
r"""psv_config_fielddiff.py —— 修复前后**逐字段差异台账**（纪律自证：哪些字段被改、改了本不该改的没有）

对比 `_证据/25_config.C组换皮版.json`（修前）与 `layout/screens/25_config.json`（修后）：
  · 逐元素逐字段列出「新增 / 改动 / 删除」；
  · 对**语义字段白名单**（flags_default / action / value / setting / min / max / step /
    state_assets / state_group / id / kind）单独判定：除**新增元素**外不得有任何变化。
用法：python _工作\ISSUE-20260926-06_C设置屏修复\复现脚本\psv_config_fielddiff.py
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OLD = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏修复", "_证据", "25_config.C组换皮版.json")
NEW = os.path.join(UI, "layout", "screens", "25_config.json")
SEMANTIC = ("id", "kind", "z", "action", "value", "setting", "min", "max", "step",
            "state_assets", "state_group")

old = json.load(open(OLD, encoding="utf-8"))
new = json.load(open(NEW, encoding="utf-8"))
bo = {e["id"]: e for e in old["elements"]}
bn = {e["id"]: e for e in new["elements"]}
dirs = ("font.color", "x", "y", "vis_flag", "vis_when", "note")
chg = collections.Counter()
per_dir = collections.Counter()
for eid in sorted(set(bo) | set(bn)):
    a, b = bo.get(eid), bn.get(eid)
    if a is None:
        chg["新增元素"] += 1
        continue
    if b is None:
        chg["删除元素"] += 1
        continue
    for k in set(a) | set(b):
        va, vb = a.get(k), b.get(k)
        if va != vb:
            chg["字段 " + k] += 1
            per_dir[k] += 1
    # 语义字段单独判
    for k in SEMANTIC:
        if a.get(k) != b.get(k):
            chg["★语义字段 " + k] += 1
print("=" * 100)
print("修复前后逐字段差异台账（修前 %d 件 → 修后 %d 件）" % (len(bo), len(bn)))
print("=" * 100)
for k, v in sorted(chg.items()):
    print("  %-34s %d" % (k, v))
print("-" * 100)
bad = [k for k in chg if k.startswith("★语义字段")]
print("flags_default 是否改动：%s" % ("否 ✓" if old["flags_default"] == new["flags_default"] else "是 ✗"))
print("元素 id 集合：修前 %d / 修后 %d ｜ 删除 %d（应为 0）｜ 新增 %d（= ② 的 20 件 + ⑤ 的 1 件盖片）"
      % (len(bo), len(bn), len(set(bo) - set(bn)), len(set(bn) - set(bo))))
print("语义字段（既有元素）是否被改动：%s" % ("**无** ✓" if not bad else "**有**：" + ",".join(bad)))
print("改动字段分布：%s" % "、".join("%s %d 件" % (k, v) for k, v in sorted(per_dir.items(), key=lambda x: -x[1])))
sys.exit(1 if bad else 0)
