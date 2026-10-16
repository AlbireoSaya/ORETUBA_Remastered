#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""_probe_10_enum_gold.py —— UNP-2 显式枚举档对拍金标的**可复跑复现器**
（2026-10-09 补，回应审核 RV-A R-1：把 `配对规则表.tsv` / `未证但已采用.tsv` 的
「0→0.999 / 1→0.952 / 2→0.954（0 档＝1314/1315）」口径落成可执行命令）。

复现 UNP-2 的「依据」数（ot 源）：

    0→640 1,314/1,315 ； 1→336 295/310 ； 2→944 292/306 ； 合计 1,901/1,931 = 98.45%
    （反例 = 30 条 = 1 + 15 + 14，与 UNP-2 备注「反例 30 行」自洽）

口径（与开发期 `_probe_03_enum.py` 同款；语言＝行，源＝ot）：
  1. **样本**：`0x1C43C`（CharacterOpen A）与 `0x14084`（CharacterOpen B）两族的行，
     位置枚举**显式 ∈ {0,1,2}**：
       * `0x1C43C`：枚举 = 本行 `args[2]`；名称 = `args[4]`；
       * `0x14084`：枚举 = 同 `(scene_id,seq)` 同槽（本行 `args[2]`）的**第一个**
         `0x17514` 的 `args[2]`；名称 = 本行 `args[1]`。
     （`0x17514` 自身不单独计入。）
  2. **金标匹配**：同 `(scene_id,seq)` 上 `task_type ∈ {CharacterOpen,CharacterOpenBS}`、
     且 `ps_name` 前 4 字 == 名称前 4 字 的事件**恰 1 条**时计入（0 条 / 多条均不计）。
  3. **命中**：该金标 `cx` == 枚举对应值（0→640 / 1→336 / 2→944；1280 系）。

只读；缺输入 ⇒ 打印 `INPUT_MISSING` + 退出码 3（与「复现失败」区分）。
复跑：`cd 新源侧\PAIR && python -X utf8 _probe_10_enum_gold.py`
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True          # 只读：不在本目录/PLACE 产生 __pycache__
import pair_place as PP                  # noqa: E402
import place_dsl as P                    # noqa: E402

SRC = "ot"
EXPECT = {0: (1314, 1315, 640), 1: (295, 310, 336), 2: (292, 306, 944)}


def main():
    miss = PP.missing_inputs()
    if miss:
        print("== INPUT_MISSING（_probe_10_enum_gold.py 无法执行：输入缺失）==")
        for p in miss:
            print("   缺输入: %s" % p)
        print("  说明: `解出_*.tsv` 被 .gitignore 排除，须先跑：")
        print("        python -X utf8 编程组/工具/decode_sob0.py --out 编程组/SOB0解码")
        print("  再跑本命令，或用 `--ws-root <工作区根>` 指向已有输入的工作区（只读）。")
        print("CHECK_ERROR=INPUT_MISSING  files=%d" % len(miss))
        return 3

    # 0x14084 的枚举取自「同 (scene,seq) 同槽的第一个 0x17514」（setter_pick=first）
    setters = collections.defaultdict(list)
    for r in PP.load_rows(SRC):
        if (r["arg3"] or "").replace("V=", "") == "0x17514":
            a = P.parse_args_from_evidence(r["evidence"]) or []
            setters[(r["scene_id"], r["seq"])].append((PP.argN(a, 3), PP.argN(a, 2)))

    gold = PP.load_gold(SRC)
    agg = collections.defaultdict(collections.Counter)
    cov = collections.Counter()
    miss_by_v = collections.Counter()
    for r in PP.load_rows(SRC):
        v = (r["arg3"] or "").replace("V=", "")
        if v not in ("0x1C43C", "0x14084"):
            continue
        a = P.parse_args_from_evidence(r["evidence"]) or []
        if v == "0x1C43C":
            name, val = PP.argS(a, 4), PP.argN(a, 2)
        else:
            name = PP.argS(a, 1)
            cand = [e for s, e in setters.get((r["scene_id"], r["seq"]), [])
                    if s == PP.argN(a, 2)]
            val = cand[0] if cand else None
        if val not in (0, 1, 2):
            continue
        g = [x for x in gold.get((r["scene_id"], r["seq"]), [])
             if x[2] in ("CharacterOpen", "CharacterOpenBS")]
        gg = [x for x in g if name and x[3].startswith(name[:4])]
        if len(gg) != 1:
            cov["nomatch"] += 1
            continue
        cov["n"] += 1
        agg[val][gg[0][0]] += 1
        if gg[0][0] != EXPECT[val][2]:
            miss_by_v[v] += 1

    print("== 显式枚举档对拍金标（ot；口径见本文件 docstring）==")
    print("  样本合计 n=%d（未匹配不计 = %d）" % (cov["n"], cov["nomatch"]))
    ok_all = True
    tot_h = tot_n = 0
    for val in (0, 1, 2):
        c = agg[val]
        n = sum(c.values())
        pr = EXPECT[val][2]
        h = c[pr]
        tot_h += h
        tot_n += n
        ok = (h, n) == (EXPECT[val][0], EXPECT[val][1])
        ok_all &= ok
        rest = {k: v for k, v in c.most_common() if k != pr}
        print("  enum=%d → 金标 %-3d ： 命中 %4d/%4d = %.4f  [未命中 %d 条，其余金标 %s]  %s"
              % (val, pr, h, n, (h / n) if n else 0, n - h, rest or "{}",
                 "OK" if ok else "MISMATCH(期望 %d/%d)" % EXPECT[val][:2]))
    print("  合计 %d/%d = %.4f（%.2f%%）；反例 %d 条（按 V 构成：%s）"
          % (tot_h, tot_n, tot_h / tot_n, 100.0 * tot_h / tot_n, tot_n - tot_h,
             dict(miss_by_v.most_common()) or "{}"))
    print("\nREPRODUCE=%s（对照 UNP-2：0→640 1,314/1,315；1→336 295/310；2→944 292/306；"
          "合计 1,901/1,931 = 98.45%%）" % ("PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
