#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""_probe_27_k2sets.py —— 「PSV 的 k=2 无单一集合」**可复跑复现器**（只读）

复现 `排布表.tsv` 第 24 行注的替代实测（2026-10-09 补，回应审核 RV-A R-3 / RV-C N3）：

    {336,944} 354 场 / {640,944} 20 场

口径（跨源）：
  1. 读 `<工作区根>\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\PSV演出\立绘事件流.tsv`；
  2. 只取 `cx` 非空的行，按 `(scene_id, seq)` 分组；
  3. 取**组内不同 `ps_name` 数恰为 2** 的组，统计每组内的 `cx` 集合；
  4. 数「集合恰为 {336,944}」与「恰为 {640,944}」的组数。

只读；缺输入 ⇒ 打印 `INPUT_MISSING` + 退出码 3。
复跑：`cd 新源侧\EXE_POS && python -X utf8 _probe_27_k2sets.py`
"""
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_WS_ENV = "GRETA_WS_ROOT"
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
GOLD_REL = os.path.join(PROJ_REL, "PSV演出", "立绘事件流.tsv")
EXPECT = {(336, 944): 354, (640, 944): 20}


def _candidate_roots():
    env = os.environ.get(_WS_ENV)
    if env:
        return [os.path.abspath(env)]
    roots, d = [], HERE
    while True:
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            roots.append(d)
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
    if not roots:
        roots = [os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))]
    return roots


def resolve_gold():
    for r in _candidate_roots():
        p = os.path.join(r, GOLD_REL)
        if os.path.isfile(p):
            return p
    return os.path.join(_candidate_roots()[0], GOLD_REL)


def main():
    gold = resolve_gold()
    if not os.path.isfile(gold):
        print("== INPUT_MISSING（_probe_27_k2sets.py 无法执行：输入缺失）==")
        print("   缺输入: %s" % gold)
        print("  说明: `立绘事件流.tsv` 在真实工作区的 `编程组\\PSV演出\\` 下（只读）；")
        print("        或用 `GRETA_WS_ROOT=<工作区根>` 指向已有输入的工作区。")
        print("CHECK_ERROR=INPUT_MISSING  files=1")
        return 3

    groups = collections.defaultdict(list)
    with open(gold, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["cx"].strip() == "":
                continue
            groups[(r["scene_id"], r["seq"])].append(r)

    cnt = collections.Counter()
    for rs in groups.values():
        if len({r["ps_name"] for r in rs}) != 2:
            continue
        cnt[tuple(sorted({int(r["cx"]) for r in rs}))] += 1

    print("== PSV k=2（组内不同 ps_name 数恰为 2）的 cx 集合分布 ==")
    print("   输入: %s" % gold)
    print("   cx 非空行分出的 (scene_id,seq) 组 = %d；其中 ps_name 数恰为 2 的组 = %d"
          % (len(groups), sum(cnt.values())))
    for s, n in cnt.most_common(8):
        mark = "  ⇐ 排布表注引用" if s in EXPECT else ""
        print("   %-16s %4d 场%s" % (str(s), n, mark))
    ok = all(cnt[s] == n for s, n in EXPECT.items())
    print("   目标值：{336,944} = %d（期望 %d）｜{640,944} = %d（期望 %d）"
          % (cnt[(336, 944)], EXPECT[(336, 944)], cnt[(640, 944)], EXPECT[(640, 944)]))
    print("\nREPRODUCE=%s（对照 `排布表.tsv` 第 24 行注：{336,944} 354 场 / {640,944} 20 场）"
          % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
