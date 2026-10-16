# -*- coding: utf-8 -*-
r"""_emit_other_strict.py — 从 `其他语义_族身份.tsv` 抽出**严格梯（tier1）**白名单。

背景（一审 RV-D1 M1，ISSUE-20261007-02）：
  `其他语义_族身份.tsv` 的 562 条「最小安全集」谓词只排除 `psv_conflict=1`，把
  `psv_conflict=''`（无唯一 PSV 金标 ＝ 未校验）也算作安全。一审要求**按 PSV 金标来源分层**：
    · 严格梯：`[Chara<slot>]` **精确命中** ∧ `psv_conflict=0`                        = 194
    · 兜底梯：金标来自「块内唯一 `[CharaN]` 兜底」（slot 归属为推断）                = 258
    · 未校验梯：`psv_conflict=''`（无可唯一定族的金标）                              = 110
  本器只产出**严格梯 194 条**的白名单（第一梯队，最保守）。

方法（与 RV-D1 的 `rv_safe_quality.py` 同口径；只读上游，不改被审的族身份表）：
  1. 读 `资源组\演出\其他语义_族身份.tsv`（17 列，逐行原样保留）。
  2. 按**改进的 PSV 宏→Task 行序一一配对**（与 `_emit_other_family.py` 同源）重解析 PSV，
     对每个 `(scene, slot, ctrl, ms)` 记录：`[Chara<slot>]` 是否**精确命中**（`used_fb=False`），
     或仅靠「块内唯一 `[CharaN]` 兜底」（`used_fb=True`）。
  3. 选行：`src∈{ot,otp}` ∧ `fam≠''` ∧ `ctrl∈7 token` ∧ `psv_conflict='0'`
           ∧ 该键在 PSV 侧存在 ∧ `used_fb=False` ⇒ **严格梯**。
  4. 断言严格梯 == 194，落盘 `资源组\演出\其他语义_族身份_严格梯.tsv`（17 列，同表结构）。

只读上游；**不接入构建、不改 build_story.py、不改族身份表本身**。
"""
from __future__ import annotations

import collections
import csv
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE)
PROJ = os.path.dirname(PRG)
sys.path.insert(0, os.path.join(PRG, "工具"))
sys.path.insert(0, os.path.join(PROJ, "资源组", "工具"))
sys.dont_write_bytecode = True
import _research_slot as RS      # noqa: E402  （RE_MACRO / load_scene_map / PSV_SCRIPT_DIR / fam_of_token）

FAM_TSV = os.path.join(PROJ, "资源组", "演出", "其他语义_族身份.tsv")
OUT_TSV = os.path.join(PROJ, "资源组", "演出", "其他语义_族身份_严格梯.tsv")

RE_TASK = re.compile(r'^\s*\[Task(\d+)\]\s*$')
RE_CHARA = re.compile(r'^\s*\[Chara(\d+)\]\s*$')
RE_ST = re.compile(r'<<\s*(st_[^>\s]+)\s*>>', re.I)

MAPPED = {"!l", "!r", "c", "l", "r"}
DPAT = re.compile(r"^[<>][0-9]$")

EXPECT_STRICT = 194


def ctrl_in7(ctrl):
    return bool(ctrl) and (ctrl in MAPPED or DPAT.match(ctrl))


def parse_psv_fb():
    """→ {(scene_id, slot, ctrl, ms): (used_fb: bool, tuple(chara_keys))}。

    与 `rv_safe_quality.py` / `_emit_other_family.parse_psv_ordered` 同款：遇 `//chr_anime`
    入队、遇 `[TaskN]` 出队一个宏配对（行序一一对应）；块内优先 `[Chara<slot>]`，
    缺失且块内仅一个 `[CharaN]` 时兜底（`used_fb=True`）。
    """
    smap = RS.load_scene_map()
    psv_dir = RS.PSV_SCRIPT_DIR
    fb = {}
    for sid, script in smap.items():
        p = os.path.join(psv_dir, script)
        if not os.path.isfile(p):
            continue
        lines = open(p, "rb").read().decode("cp932", "replace").split("\n")
        pend = []
        for i, l in enumerate(lines):
            ma = RS.RE_MACRO.match(l)
            if ma:
                try:
                    slot = int(ma.group(1).strip())
                except ValueError:
                    continue
                pend.append((i, slot, ma.group(2), int(ma.group(3)) if ma.group(3) else None))
                continue
            mt = RE_TASK.match(l)
            if mt and pend:
                _ml, slot, ctrl, ms = pend.pop(0)
                end = next((k for k in range(i + 1, len(lines)) if RE_TASK.match(lines[k])), len(lines))
                ch, cur = {}, None
                for k in range(i, end):
                    mc = RE_CHARA.match(lines[k])
                    if mc:
                        cur = int(mc.group(1))
                        continue
                    m2 = RE_ST.search(lines[k])
                    if m2 and cur is not None and cur not in ch:
                        ch[cur] = m2.group(1)
                st = ch.get(slot)
                used_fb = False
                if st is None and len(ch) == 1:
                    st = next(iter(ch.values()))
                    used_fb = True
                fb[(sid, slot, ctrl, ms)] = (used_fb, tuple(sorted(ch.keys())))
    return fb


def key_of(r):
    if r.get("slot") in (None, "") or r.get("ms") in (None, ""):
        return None
    try:
        return (r["scene_id"], int(r["slot"]), r["ctrl"], int(r["ms"]))
    except (ValueError, KeyError):
        return None


def main():
    rows = list(csv.DictReader(io.open(FAM_TSV, encoding="utf-8"), delimiter="\t"))
    header = list(rows[0].keys()) if rows else []

    fb = parse_psv_fb()

    strict = []
    detail = collections.Counter()
    for r in rows:
        if not (r.get("src") in ("ot", "otp") and r.get("fam")
                and ctrl_in7(r.get("ctrl") or "") and r.get("psv_conflict") != "1"):
            continue
        k = key_of(r)
        e = fb.get(k) if k else None
        if r.get("psv_conflict") == "" or e is None:
            detail["未校验（无唯一金标/键缺失）"] += 1
        elif e[0]:
            detail["兜底（块内唯一 Chara，slot 推断）"] += 1
        else:
            strict.append(r)
            detail["严格（[Chara<slot>] 精确 ∧ 冲突=0）"] += 1

    by_src = collections.Counter(r["src"] for r in strict)
    by_tok = collections.Counter(r["ctrl"] for r in strict)

    print("=== 严格梯抽取（一审 RV-D1 M1 口径）===")
    print("族身份表 %d 行 ｜ 562 最小安全集分层：%s" % (len(rows), dict(detail)))
    print("严格梯 %d 条（期望 %d）｜ 按源 %s ｜ 按 token %s"
          % (len(strict), EXPECT_STRICT, dict(by_src), dict(by_tok)))
    if len(strict) != EXPECT_STRICT:
        print("[FAIL] 严格梯条数 != %d，不落盘（口径漂移，须核查）" % EXPECT_STRICT)
        return 2

    with io.open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in strict:
            f.write("\t".join("" if r.get(c) in (None, "") else str(r.get(c)) for c in header) + "\n")
    print("已落盘：%s（%d 数据行 × %d 列）" % (OUT_TSV, len(strict), len(header)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
