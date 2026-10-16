# -*- coding: utf-8 -*-
r"""
`selftest_term_unify.py` · `fix_type=term_unify` 的**负向自证**（ISSUE-20260930-12，只读、幂等、可复跑）

用途
    `修正表_裁决20260930.tsv`（123 行）的 `old_text`/`new_text` 语义已改为**词形级**
    （`old_text` = 被替换词形的正则，`new_text` = 替换值，消费方式 `re.sub(old_text, new_text, cn)`）。
    本脚本是配套硬闸门 `verify_schema_enums.py`（枚举）与生成器 `build_rulings_fixtable.py` G0b
    （正则可编译）之外的第三道负向自证：**证明 `_term_unify` 的三个分支都能真的走到，且子串陷阱不得自爆**。
    它是 `_term_unify.py` 的回归测试，不改任何表与语料。

覆盖的判据（任一失败 ⇒ `ALL_PASS = False` 且退出码 1）
    1 **子串陷阱（最重要）**：对全部 123 行 `old_text`，作用于**采用值 `new_text`** 时不得命中/改写
      （不得产生 `美美空学院院` 这类畸形拼接）；并显式逐一断言四条「空学族」上下文守卫在 `美空学院` 上零改动。
    2 `applied` 分支：变体命中 ⇒ `re.sub` 生效 ⇒ 状态 `"applied"`。
    3 `noop` 分支：变体不命中但已是后态（含采用值）⇒ 原样返回 ⇒ 状态 `"noop"`。
    4 `fail loud` 分支：变体不命中且非后态 ⇒ **必须抛 `SystemExit`**（捕获不到即判失败）。
    5 **正则闸门（G0b 的独立复核）**：逐行 `old_text` 可 `re.compile`、非空、**不匹配空串**；`new_text` 非空。
    6 **表结构断言**：123 数据行；`fix_type` 全为 `term_unify`；`old_text != new_text`；
      16 个已知变体不含任何正则元字符（`.-^$*+?()[]{}|\`）；表中「无元字符的旧写形」必 ⊆ 该 16 变体集合。
    7 **反向自证（谓词非恒真）**：第 4 项的谓词在**明知正确**的输入上不得抛错
      （`apply("游隼", "游隼", "隼")` 必须正常返回）——否则「抛 SystemExit」这个判据可能是恒真的。
    8 （附加）`_term_unify.verify` 互证：8a/8b = 正/负两例；8c–8f = 新参数 `ignore_u3000`
      与 `later_layers_touched` 的「只豁免 U+3000、不放行别的字符、两条豁免互不替代」四条判据。
      `verify()` 判据与消费分支独立实现，故可互证（共用实现会变成自证）。

复跑：
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/selftest_term_unify.py"
"""
from __future__ import annotations

import csv
import importlib.util
import io
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
TSV = os.path.join(RES, "修正", "修正表_裁决20260930.tsv")
MODULE = os.path.join(HERE, "_term_unify.py")

EXPECT_ROWS = 123

# `old_text` 中出现过的四条「空学族」上下文守卫（变体是采用值的子串，裸替换会自爆）
GUARDS = (
    r"(?<!美)空学(?!院|府|园)",
    r"(?<!美)空学院",
    r"(?<!美)空学园",
    r"美空学(?!院|府|园|生)",
)

# `build_rulings_fixtable.py` 模块头声称「全部 16 个变体均不含正则元字符」——本表是对该前提的独立复核
VARIANTS_16 = (
    "古罗利亚斯", "游隼", "耳语材料", "细语材质", "罗伊希滕",
    "空学院", "空学", "空学园", "美空学园",
    "柳木原普利广场", "柳波广场", "柳木原广场",
    "羽田宅邸", "羽田宅", "苍羽女学院", "美空学",
)
META = set(".-^$*+?()[]{}|\\")

FAILS = []


def record(name, ok, detail=""):
    print("[%s] %s%s" % ("OK" if ok else "FAIL", name, (" — " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def load_module():
    spec = importlib.util.spec_from_file_location("term_unify_under_test", MODULE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_rows():
    """只读：utf-8-sig + 制表符 DictReader（表头 11 列）。"""
    with io.open(TSV, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        return r.fieldnames or [], list(r)


# ---------------------------------------------------------------- 1 子串陷阱
def check_substring_trap(rows):
    for i, pat in enumerate(GUARDS, 1):
        got = re.sub(pat, "美空学院", "美空学院")
        record("1a.%d 守卫 %s 在「美空学院」上零改动" % (i, pat),
               got == "美空学院", "结果=%r" % (got,))

    corrupt = []
    selfmatch = []
    for n, row in enumerate(rows, 1):
        pat, val = row["old_text"], row["new_text"]
        if re.search(pat, val):
            selfmatch.append((n, row["source"], row["locator"], pat, val))
        if re.sub(pat, val, val) != val:
            corrupt.append((n, row["source"], row["locator"], pat, val,
                            re.sub(pat, val, val)))
    record("1b 全部 %d 行 old_text 在采用值 new_text 上零改写（无畸形拼接）" % len(rows),
           not corrupt,
           "" if not corrupt else "%d 条改写：%s" % (len(corrupt), corrupt[:3]))
    record("1c 全部 %d 行 old_text 不自匹配自身采用值 new_text" % len(rows),
           not selfmatch,
           "" if not selfmatch else "%d 条自匹配：%s" % (len(selfmatch), selfmatch[:3]))


# ---------------------------------------------------------------- 2/3/4/7 apply 三分支 + 谓词非恒真
def check_apply_branches(mod):
    # 2 applied
    got, st = mod.apply("这是游隼的故事", "游隼", "隼")
    record("2 applied 分支：游隼→隼 命中并替换",
           (got, st) == ("这是隼的故事", mod.APPLIED),
           "got=%r status=%r" % (got, st))

    # 3 noop
    got2, st2 = mod.apply("这是美空学院", r"(?<!美)空学(?!院|府|园)", "美空学院")
    record("3 noop 分支：已是后态 ⇒ 原样返回 + noop",
           (got2, st2) == ("这是美空学院", mod.NOOP),
           "got=%r status=%r" % (got2, st2))

    # 4 fail loud
    raised = False
    try:
        mod.apply("完全无关的句子", "游隼", "隼")
    except SystemExit:
        raised = True
    record("4 fail loud 分支：无关句 ⇒ 抛 SystemExit", raised,
           "" if raised else "未捕获到 SystemExit（判据恒假 / 未 fail loud）")

    # 7 反向自证：同一谓词在明知正确的输入上不得抛错 ⇒ 证明第 4 项不是恒真
    try:
        g, s = mod.apply("游隼", "游隼", "隼")
    except SystemExit as e:
        record("7 谓词非恒真：apply(\"游隼\",\"游隼\",\"隼\") 不得抛 SystemExit", False,
               "意外抛错：%r" % (e,))
    else:
        record("7 谓词非恒真：apply(\"游隼\",\"游隼\",\"隼\") 正常返回",
               (g, s) == ("隼", mod.APPLIED), "got=%r status=%r" % (g, s))


# ---------------------------------------------------------------- 5 正则闸门（G0b 独立复核）
def check_regex_gate(rows):
    bad_compile, empty_pat, empty_match, empty_new = [], [], [], []
    for n, row in enumerate(rows, 1):
        pat = row["old_text"]
        try:
            cpat = re.compile(pat)
        except re.error as e:
            bad_compile.append((n, row["source"], row["locator"], pat, str(e)))
            continue
        if not pat.strip():
            empty_pat.append((n, row["source"], row["locator"], pat))
        if cpat.search("") is not None:
            empty_match.append((n, row["source"], row["locator"], pat))
        if not (row["new_text"] or "").strip():
            empty_new.append((n, row["source"], row["locator"], row["new_text"]))
    record("5a 全部 %d 行 old_text 可 re.compile" % len(rows), not bad_compile,
           "" if not bad_compile else str(bad_compile[:3]))
    record("5b 全部 %d 行 old_text 非空" % len(rows), not empty_pat,
           "" if not empty_pat else str(empty_pat[:3]))
    record("5c 全部 %d 行 old_text 不匹配空串（search('') is None）" % len(rows),
           not empty_match, "" if not empty_match else str(empty_match[:3]))
    record("5d 全部 %d 行 new_text 非空" % len(rows), not empty_new,
           "" if not empty_new else str(empty_new[:3]))


# ---------------------------------------------------------------- 6 表结构断言
def check_table_shape(fields, rows):
    need = ["source", "file", "locator", "kind", "field", "old_text", "new_text",
            "fix_type", "method", "evidence", "confidence"]
    record("6a 表头含全部 11 列", all(c in (fields or []) for c in need),
           "header=%s" % (fields,))
    record("6b 数据行数 == %d" % EXPECT_ROWS, len(rows) == EXPECT_ROWS,
           "实际=%d" % len(rows))
    bad_type = [(i + 1, r["fix_type"]) for i, r in enumerate(rows)
                if r["fix_type"] != "term_unify"]
    record("6c 全部行 fix_type == term_unify", not bad_type, str(bad_type[:3]))
    same = [(i + 1, r["old_text"]) for i, r in enumerate(rows)
            if r["old_text"] == r["new_text"]]
    record("6d 全部行 old_text != new_text", not same, str(same[:3]))

    dirty = [(v, sorted(set(v) & META)) for v in VARIANTS_16 if set(v) & META]
    record("6e 16 个已知变体不含正则元字符", not dirty, str(dirty[:5]))

    literals = sorted({r["old_text"] for r in rows if not (set(r["old_text"]) & META)})
    extra = [v for v in literals if v not in VARIANTS_16]
    record("6f 表中「无元字符的旧写形」⊆ 16 变体集合（%d 个）" % len(literals),
           not extra, "表外=%s" % (extra,))
    print("       6f 明细：无元字符 old_text = %s" % (literals,))


# ---------------------------------------------------------------- 8 verify() 互证：正/负 + ignore_u3000 / later_layers_touched
def check_verify(mod):
    ok1, why1 = mod.verify("这是游隼的故事", "这是隼的故事", "游隼", "隼")
    record("8a verify() 正向：cn_before 命中且 cn_after == 纯替换结果", ok1,
           "ok=%r why=%r" % (ok1, why1))
    ok2, why2 = mod.verify("这是隼的故事", "这是隼的故事", "游隼", "隼")
    record("8b verify() 负向：cn_before 未命中 ⇒ 判失败（locator 漂移）", not ok2,
           "ok=%r why=%r" % (ok2, why2))

    # otr 形态：cn_before 带前导 U+3000，而流水线 ②.5 在套表**之后**删掉它（见 _term_unify.verify 文档）
    before = mod.U3000 + "这是游隼的故事"
    after = "这是隼的故事"

    # 8c ignore_u3000=True：只豁免 U+3000 一个字符 ⇒ 纯替换结果对得上
    ok3, why3 = mod.verify(before, after, "游隼", "隼",
                           later_layers_touched=False, ignore_u3000=True)
    record("8c ignore_u3000=True：前导 U+3000 被豁免 ⇒ ok", ok3,
           "ok=%r why=%r" % (ok3, why3))

    # 8d ★ 对照：同一组入参、两条豁免都关 ⇒ 必须失败
    #    （证明 8c 不是恒真——ignore_u3000 只豁免 U+3000，不是把判据 ② 整体放行）
    ok4, why4 = mod.verify(before, after, "游隼", "隼",
                           later_layers_touched=False, ignore_u3000=False)
    record("8d 对照 ignore_u3000=False + later=False：同一组入参必须失败（8c 非恒真）", not ok4,
           "ok=%r why=%r" % (ok4, why4))

    # 8e later_layers_touched 是另一条独立理由：同 8d 入参、只开 later ⇒ ok（两条豁免互不替代）
    ok5, why5 = mod.verify(before, after, "游隼", "隼",
                           later_layers_touched=True, ignore_u3000=False)
    record("8e later_layers_touched=True 独立放行：同 8d 入参 ⇒ ok", ok5,
           "ok=%r why=%r" % (ok5, why5))

    # 8f 硬判据：ignore_u3000 只删 U+3000，其余仍逐字符比——内部字符被改动必须失败
    ok6, why6 = mod.verify(before, "这隼是的故事", "游隼", "隼",
                           later_layers_touched=False, ignore_u3000=True)
    record("8f ignore_u3000 只豁免 U+3000：内部字符被改动 ⇒ 仍必须失败", not ok6,
           "ok=%r why=%r" % (ok6, why6))


def main() -> int:
    print("=" * 78)
    print("term_unify 负向自证（只读；表 = %s）"
          % os.path.relpath(TSV, RES))
    print("=" * 78)

    mod = load_module()
    fields, rows = load_rows()

    print("-- 1 子串陷阱 --")
    check_substring_trap(rows)
    print("-- 2/3/4/7 apply 三分支 + 谓词非恒真 --")
    check_apply_branches(mod)
    print("-- 5 正则闸门（G0b 独立复核）--")
    check_regex_gate(rows)
    print("-- 6 表结构 --")
    check_table_shape(fields, rows)
    print("-- 8 verify() 互证（附加）--")
    check_verify(mod)

    ok = not FAILS
    print()
    if FAILS:
        print("失败项 %d 个：%s" % (len(FAILS), FAILS))
    print("ALL_PASS = %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
