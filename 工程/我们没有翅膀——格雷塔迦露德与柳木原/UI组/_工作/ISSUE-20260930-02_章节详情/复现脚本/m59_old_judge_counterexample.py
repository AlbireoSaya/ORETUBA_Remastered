# -*- coding: utf-8 -*-
r"""m59_old_judge_counterexample.py · 一审建议项的**反例自证**（ISSUE-20260930-02 · 第 2 轮 · T5）

要证明的事：`gen_flow_layout.py::intro_overlay_violations()` 的「浮层件 z 必须高于本屏所有
非浮层热区」这条断言，**改前**（`kind=="hit"` ＋ `isinstance(z, int)`）会被两种反例骗过，
**改后**（`kind ∈ {hit, list}` ＋ `_z_num()` 数值化）必被检出。

做法（纯内存，不落盘、不改任何产物）：
  1) 取生成器的**真实静态快照**与画布；
  2) `old_violations()`  —— 逐字复刻**改前**的判据（一审用反例实测的那两处窄口径）；
     `new_violations()` —— 直接调模块里**改后**的函数；
  3) 三种输入各跑一遍：
     · 真数据（两侧都应 0 违规）；
     · 反例 H：把非浮层热区 `fc.p_plus_hit` 的 `z` 写成**字符串** `"250"`；
     · 反例 I：把该件 `kind` 换成 `"list"` 且 `z = 240`（引擎同样把它当点击候选）；
  4) 断言：真数据两侧都 0；两个反例 **旧判据 0 违规（假绿）／新判据 ≥1 违规（检出）**。

■ 运行：export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
        cd "<UI组>" && python "_工作/ISSUE-20260930-02_章节详情/复现脚本/m59_old_judge_counterexample.py"
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GEN = os.path.join(UI_GROUP, "工具", "gen_flow_layout.py")


def load_gen():
    spec = importlib.util.spec_from_file_location("_gfl_m59", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def old_z_of(e):
    """**改前**的 z 读取：只认 `int`（字符串一律当「不是 z」跳过）。"""
    z = e.get("z")
    return z if isinstance(z, int) else None


def old_violations(gen, elements, float_ids):
    """**改前**的浮层 z 判据（与当时的实现逐字同义）：候选只筛 `kind=="hit"`、z 只认 `int`。

    ⚠ 本演示把**浮层族集合**按**现行 8 件**传入（`float_ids`）—— 目的是**隔离「族集合变化」
    这个无关变量**，只比较**判据口径**（`kind` 过滤 ／ `z` 类型强制）这一处差异。
    """
    msgs = []
    by = {e["id"]: e for e in elements}
    pair = float_ids[:6]                       # 当时受区间约束的是基座 6 件
    other = [old_z_of(e) for e in elements
             if e.get("kind") == "hit" and e["id"] not in float_ids and old_z_of(e) is not None]
    mz = max(other) if other else 0
    for i in pair:
        z = old_z_of(by[i])
        if z is None or not (200 <= z <= 235):
            msgs.append("%s 区间" % i)
        elif z <= mz:
            msgs.append("%s ≤ max_hit_z %d" % (i, mz))
    return msgs, mz


def old_violations_literal_6(gen, elements):
    """**改前**那支原样（浮层族＝当时的 6 件）跑在**现行数据**上 —— 用来展示「旧口径 + 新数据」
    本身就会**假失败**（把合法的关闭件 z237 当成「既有热区」）。"""
    return old_violations(gen, elements, tuple(
        "fc.intro_scrim fc.intro_scrim_hit fc.intro_bg "
        "fc.intro_panel_hit fc.intro_title_tx fc.intro_text_tx".split()))


def main():
    gen = load_gen()
    canvas = gen.load_canvas()
    cw, ch = canvas["width"], canvas["height"]
    els = gen.load_static_elements()
    float_ids = tuple(gen.INTRO_FLOAT_IDS)
    ok = True

    def run(tag, mutate, want_old, want_new):
        nonlocal ok
        m = copy.deepcopy(els)
        if mutate:
            for e in m:
                if e["id"] == gen.PLUS_HIT_ID:
                    mutate(e)
        vo, _mz = old_violations(gen, m, float_ids)
        vn = gen.intro_overlay_violations(m, cw, ch)
        good = (len(vo) == want_old) and (len(vn) >= want_new)
        ok = ok and good
        print("  %-30s 旧判据违规 %d 条（期望 %d）｜新判据违规 %d 条（期望 ≥%d）%s"
              % (tag, len(vo), want_old, len(vn), want_new, " ✓" if good else " ✗"))
        return vn

    print("=" * 78)
    print("m59 · 一审建议项的反例自证（浮层 z 判据：改前窄口径 vs 改后对齐引擎）")
    print("=" * 78)
    run("真数据", None, 0, 0)
    run("反例 H：z = \"250\"（字符串）", lambda e: e.update(z="250"), 0, 1)
    vn = run("反例 I：kind = \"list\" 且 z = 240", lambda e: e.update(kind="list", z=240), 0, 1)
    print("-" * 78)
    if vn:
        print("  新判据对反例 I 的报错原文（前 2 条）：")
        for x in vn[:2]:
            print("    · %s" % x)
    # 旁证：旧口径（浮层族按当时的 6 件）跑在**现行数据**上会**假失败** —— 因为它把合法的
    #   关闭件热区 `fc.intro_close_hit`（z237）误当「既有热区」。这本身证明「判据必须随数据口径一起改」。
    vo6, mz6 = old_violations_literal_6(gen, els)
    print("-" * 78)
    print("  旁证（不参与断言）：旧口径把浮层族当 6 件跑现行数据 ⇒ 违规 **%d 条**，"
          "因 `fc.intro_close_hit`(z237) 被误算进「既有热区最高 z = %d」" % (len(vo6), mz6))
    print("=" * 78)
    print("结论：**%s**（改前两条反例都是「假绿」；改后必被检出 ⇒ 判据对齐引擎后不再漏）"
          % ("成立" if ok else "不成立"))
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
