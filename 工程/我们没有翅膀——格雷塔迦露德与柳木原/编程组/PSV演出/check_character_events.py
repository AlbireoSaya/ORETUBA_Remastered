#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_character_events.py —— 独立校验器（ISSUE-20261008-03 · M1，A1 复审后修订）

**不共用生成器实现**：本文件从头复算，不 import emit_character_events。
校验对象：`立绘事件流.tsv`（20 列 = 19 定死列 + 1 追加列）。

判据（C1–C10）：
  C1  表头逐字一致（20 列）+ 每行恰 20 个字段
  C2  无 BOM / 无 CR / 每行 TAB 数 = 19 / 字段**不含**引号 / 枚举列合法
  C3  `op` ∈ 七类闭集（＋已登记的外部 type 白名单，当前为空）
  C4  `seq` 为正整数且 ≤ 该场 `corpus_lines`（须 --scene-map）
  C5  `fam` 与 `ps_name` 推导一致（^[A-Za-z]+ 小写）
  C6  `x1920`/`y1920` == round(c*1.5)，缺值留空
  C7  每场 `remove` 数 ≤ `add` 数
  C8  slot_hint 不变量（**身份键 ＝ 逐立绘件名**）：add 不得落在已占用的槽（抓「同族并存挤同槽」）；
      非空 slot 的 remove/move/expr/expr_end/priority 必须指向当时在场的**同一件名或同族件**
  C9  覆盖：与金标逐场 chr 行数一致（须能取到 `时间线.tsv`）
  C10 归一映射 + 并存登记：① 用金标重算**逐场 by-op 计数**并与产物比（堵住 `op ↔ :Tasktype` 归一整面）；
      ② 独立重扫金标的「单任务同族 ≥2 名」证据集，与 `同族并存登记.tsv` **集合相等**，
         且每一对同名必须**同时在场且槽位不同**（抓修复前的挤槽）

用法：
  python -X utf8 check_character_events.py
  python -X utf8 check_character_events.py --tsv <旧模型.tsv>     # 负向对照
  python -X utf8 check_character_events.py --self-test
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _guess_workspace_root() -> str:
    p, hit = HERE, None
    for _ in range(8):
        p = os.path.dirname(p)
        if os.path.isfile(os.path.join(p, "Galgame.md")) and os.path.isdir(os.path.join(p, "工程")):
            hit = p
    return hit or r"E:\ZCode Workspace\Galgame"


DEFAULT_DATA_ROOT = _guess_workspace_root()
GAME_DIR = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原")
PSV_SUB = os.path.join("编程组", "PSV演出")
DEFAULT_EVIDENCE = os.path.join(DEFAULT_DATA_ROOT, "子代理工作区", "ISSUE-20261008-03", "M1")

EXPECT_COLS = ["scene_id", "src", "seq", "op", "task_type", "ps_name", "delivery", "fam",
               "slot_hint", "x", "y", "cx", "cy", "cpri", "priority", "time",
               "x1920", "y1920", "conf", "scene_degraded"]
OPS = ("add", "move", "remove", "expr", "expr_end", "priority", "wait")
REGISTERED_EXTRA_OPS: set[str] = set()
COEXIST_EVIDENCE_OPS = ("move", "remove", "expr", "expr_end")
SCALE = 1.5

_RE_FAM = re.compile(r"^([A-Za-z]+)")
_RE_INT = re.compile(r"^-?\d+$")


def fam_of(ps_name: str) -> str:
    m = _RE_FAM.match(ps_name or "")
    return m.group(1).lower() if m else ""


# ---------------------------------------------------------------- 读入

def parse_scene_map(path):
    scenes = {}
    with open(path, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        I = {k: i for i, k in enumerate(hdr)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            scenes[p[I["scene_id"]]] = int(p[I["corpus_lines"]])
    return scenes


def parse_golden(path):
    """返回 (逐场 chr 行数, 逐场 by-op 计数, 并存证据集)。均从金标独立重算。"""
    counts = collections.Counter()
    scene_op = collections.defaultdict(collections.Counter)
    by_task = collections.defaultdict(lambda: collections.defaultdict(list))
    tmap = {"CharacterOpen": "add", "CharacterOpenBS": "add", "CharacterMove": "move",
            "CharacterDelete": "remove", "CharacterAction": "expr",
            "CharacterActionEnd": "expr_end", "CharacterPriority": "priority",
            "CharacterWait": "wait", "CharacterStop": "wait"}
    with open(path, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        I = {k: i for i, k in enumerate(hdr)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[I["layer"]] != "chr":
                continue
            sid = p[I["scene_id"]]
            counts[sid] += 1
            op = tmap.get(p[I["type"]], p[I["type"]])
            scene_op[sid][op] += 1
            by_task[sid][p[I["task"]]].append((op, p[I["name"]]))
    coexist = set()
    for sid, tasks in by_task.items():
        for task, evs in tasks.items():
            ops = {o for o, _ in evs}
            if not (set(COEXIST_EVIDENCE_OPS) & ops):
                continue
            fams = collections.defaultdict(set)
            for _o, nm in evs:
                if nm:
                    fams[fam_of(nm)].add(nm)
            for F, ns in fams.items():
                if F and len(ns) >= 2:
                    coexist.add((sid, task, F))
    return counts, scene_op, coexist


def parse_registry(path):
    rows, keys = [], set()
    if not os.path.isfile(path):
        return rows, keys
    with open(path, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        I = {k: i for i, k in enumerate(hdr)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            r = {k: p[I[k]] for k in ("scene_id", "src", "task", "fam", "names", "ops")}
            rows.append(r)
            keys.add((r["scene_id"], r["task"], r["fam"]))
    return rows, keys


# ---------------------------------------------------------------- 判据

def run_checks(text, scene_lines=None, golden=None, golden_scene_op=None,
               registry_rows=None, registry_expected=None):
    """返回 ({crit: [msg,...]}, 数据行数)。"""
    V = collections.defaultdict(list)

    def add(crit, msg):
        if len(V[crit]) < 40:
            V[crit].append(msg)

    if text.startswith("\ufeff"):
        add("C2", "文件以 BOM 开头")
    if "\r" in text:
        add("C2", "含 CR（应 LF）")
    raw = text.split("\n")
    if raw and raw[-1] == "":
        raw = raw[:-1]
    if not raw:
        add("C1", "空文件")
        return V, 0

    header = raw[0].split("\t")
    body = []
    for i, ln in enumerate(raw[1:], start=2):
        if ln.count("\t") != len(EXPECT_COLS) - 1:
            add("C2", "第 %d 行 TAB 数 %d ≠ %d" % (i, ln.count("\t"), len(EXPECT_COLS) - 1))
        fields = ln.split("\t")
        if any('"' in f for f in fields):
            add("C2", "第 %d 行存在含引号的字段（契约：无引号包裹）" % i)
        body.append((i, fields))

    if header != EXPECT_COLS:
        add("C1", "表头不一致：%r" % (header,))
    badlen = [(i, len(f)) for i, f in body if len(f) != len(EXPECT_COLS)]
    if badlen:
        add("C1", "字段数 ≠ %d 的行 %d 例：%r" % (len(EXPECT_COLS), len(badlen), badlen[:5]))

    idx = {k: i for i, k in enumerate(EXPECT_COLS)}

    def g(f, k):
        i = idx[k]
        return f[i] if i < len(f) else ""

    per_scene_add = collections.Counter()
    per_scene_remove = collections.Counter()
    per_scene_run = collections.defaultdict(list)
    prod_scene_op = collections.defaultdict(collections.Counter)
    prod_counts = collections.Counter()

    for li, f in body:
        op, scene, seq = g(f, "op"), g(f, "scene_id"), g(f, "seq")
        nm, fam, slot = g(f, "ps_name"), g(f, "fam"), g(f, "slot_hint")
        cx, cy, x19, y19 = g(f, "cx"), g(f, "cy"), g(f, "x1920"), g(f, "y1920")
        conf, deg = g(f, "conf"), g(f, "scene_degraded")

        if op not in OPS and op not in REGISTERED_EXTRA_OPS:
            add("C3", "第 %d 行 op=%r 不在七类闭集" % (li, op))

        if not _RE_INT.match(seq) or int(seq) < 1:
            add("C4", "第 %d 行 seq=%r 非正整数" % (li, seq))
        elif scene_lines is not None:
            lim = scene_lines.get(scene)
            if lim is not None and int(seq) > lim:
                add("C4", "第 %d 行 seq=%s > 该场 corpus_lines=%d（%s）" % (li, seq, lim, scene))

        want = fam_of(nm)
        if fam != want:
            add("C5", "第 %d 行 fam=%r ≠ 由 ps_name=%r 推得 %r" % (li, fam, nm, want))

        for col, src, out in (("cx", cx, x19), ("cy", cy, y19)):
            if src == "":
                if out != "":
                    add("C6", "第 %d 行 %s 空但 %s0=%r（应留空）" % (li, col, col, out))
            elif _RE_INT.match(src):
                w = str(int(round(int(src) * SCALE)))
                if out != w:
                    add("C6", "第 %d 行 %s=%s → 应 %s0=%s，实为 %r" % (li, col, src, col, w, out))
            else:
                add("C6", "第 %d 行 %s=%r 非整数" % (li, col, src))

        if conf not in ("exact", "inferred"):
            add("C2", "第 %d 行 conf=%r 非枚举" % (li, conf))
        if deg not in ("0", "1"):
            add("C2", "第 %d 行 scene_degraded=%r 非 0/1" % (li, deg))

        prod_scene_op[scene][op] += 1
        prod_counts[scene] += 1
        if op == "add":
            per_scene_add[scene] += 1
        elif op == "remove":
            per_scene_remove[scene] += 1
        if op in ("add", "remove", "move", "expr", "expr_end", "priority"):
            per_scene_run[scene].append((li, op, nm, fam, slot))

    for sc in set(per_scene_add) | set(per_scene_remove):
        if per_scene_remove[sc] > per_scene_add[sc]:
            add("C7", "场 %s：remove %d > add %d" % (sc, per_scene_remove[sc], per_scene_add[sc]))

    # C8 —— 活槽位不变量（身份键 ＝ 逐立绘件名；引用/删除允许同族回退）
    observed_pairs = collections.defaultdict(set)
    for sc, evs in per_scene_run.items():
        slot2name, name2slot = {}, {}
        fam_live = collections.defaultdict(list)
        # 索引：件名的 add 位置与「引用」位置（move/remove/expr/expr_end/priority）
        adds_idx = collections.defaultdict(list)
        refs_idx = collections.defaultdict(list)
        for i, (_li, _op, _nm, _fam, _slot) in enumerate(evs):
            if not _nm:
                continue
            if _op == "add":
                adds_idx[_nm].append(i)
            else:
                refs_idx[_nm].append(i)

        def still_alive(nm, i):
            """被换下的 nm 在位置 i 之后**仍被引用**（且其间未再 add）⇒ 与新增者并存。"""
            nxt = next((a for a in adds_idx.get(nm, ()) if a > i), None)
            return any(r > i and (nxt is None or r < nxt) for r in refs_idx.get(nm, ()))

        for i, (li, op, nm, fam, slot) in enumerate(evs):
            if op == "add":
                if slot == "":
                    continue
                if not _RE_INT.match(slot):
                    add("C8", "场 %s 第 %d 行 slot_hint=%r 非整数" % (sc, li, slot))
                    continue
                s = int(slot)
                if s in slot2name and slot2name[s] != nm:
                    held = slot2name[s]
                    # 差分替换（合法）：被换下的旧件名此后**未再被引用**（或先被重新 add）。
                    # 同族并存挤槽（非法）：旧件名在本次 add 之后仍被引用 ⇒ 二者同时在场却同槽。
                    if still_alive(held, i):
                        add("C8", "场 %s 第 %d 行：add %s 挤占槽 %d（现持 %s），但 %s 在本次 add "
                                  "之后仍被引用（其间未再 add）⇒ 二者并存却同槽（同族=%s）"
                            % (sc, li, nm, s, held, held, fam_of(held) == fam))
                    else:                              # 合法替换 ⇒ 旧件被换下（同步复算状态）
                        name2slot.pop(held, None)
                        hf = fam_of(held)
                        if held in fam_live.get(hf, []):
                            fam_live[hf].remove(held)
                if nm and nm in name2slot and name2slot[nm] != s:
                    add("C8", "场 %s 第 %d 行：%s 已在槽 %d，却再分到槽 %d"
                        % (sc, li, nm, name2slot[nm], s))
                for other in fam_live.get(fam, []):
                    if other != nm and name2slot.get(other) != s:
                        observed_pairs[(sc, fam)].add(tuple(sorted((other, nm))))
                slot2name[s] = nm
                name2slot[nm] = s
                if nm not in fam_live[fam]:
                    fam_live[fam].append(nm)
                continue
            if slot == "":
                continue
            if not _RE_INT.match(slot):
                add("C8", "场 %s 第 %d 行 slot_hint=%r 非整数" % (sc, li, slot))
                continue
            s = int(slot)
            if s not in slot2name:
                add("C8", "场 %s 第 %d 行：%s 指向不在场的槽 %d" % (sc, li, op, s))
                continue
            held = slot2name[s]
            if nm and held != nm and fam_of(held) != fam:
                add("C8", "场 %s 第 %d 行：%s(%s) 指向槽 %d（现持 %s/%s，非同族）"
                    % (sc, li, op, nm, s, held, fam_of(held)))
            if op == "remove":
                del slot2name[s]
                if held in name2slot:
                    del name2slot[held]
                hf = fam_of(held)
                if held in fam_live.get(hf, []):
                    fam_live[hf].remove(held)

    # C9 —— 覆盖（逐场 chr 行数）
    if golden is not None:
        for sc, n in golden.items():
            if prod_counts.get(sc, 0) != n:
                add("C9", "场 %s：金标 %d 行，本表 %d 行" % (sc, n, prod_counts.get(sc, 0)))
        for sc in prod_counts:
            if sc not in golden:
                add("C9", "场 %s 在本表出现 %d 行，金标无" % (sc, prod_counts[sc]))

    # C10a —— 归一映射：逐场 by-op 计数（金标 vs 产物）
    if golden_scene_op is not None:
        for sc, expected in golden_scene_op.items():
            got = prod_scene_op.get(sc, collections.Counter())
            if dict(expected) != dict(got):
                add("C10a", "场 %s：金标 by-op %s ≠ 产物 %s"
                    % (sc, dict(sorted(expected.items())), dict(sorted(got.items()))))
        for sc in prod_scene_op:
            if sc not in golden_scene_op:
                add("C10a", "场 %s 在产物有行，金标 by-op 无此场" % sc)

    # C10b —— 并存登记：集合相等 + 登记对必须「同时在场且槽不同」
    if registry_expected is not None:
        got_keys = {(r["scene_id"], r["task"], r["fam"]) for r in (registry_rows or [])}
        miss = registry_expected - got_keys
        extra = got_keys - registry_expected
        if miss:
            add("C10b", "登记缺 %d 条：%s" % (len(miss), sorted(miss)[:5]))
        if extra:
            add("C10b", "登记多 %d 条（金标无此证据）：%s" % (len(extra), sorted(extra)[:5]))
    for r in (registry_rows or []):
        sc, F = r["scene_id"], r["fam"]
        names = [x for x in r["names"].split(",") if x]
        pairs = observed_pairs.get((sc, F), set())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pr = tuple(sorted((names[i], names[j])))
                if pr not in pairs:
                    add("C10b", "场 %s fam %s：%s 与 %s 未在同一时刻各自持槽（挤槽/未并存）"
                        % (sc, F, names[i], names[j]))

    return V, len(body)


# ---------------------------------------------------------------- 自证

def _mkrow(**kw):
    d = {c: "" for c in EXPECT_COLS}
    d.update(kw)
    return "\t".join(d[c] for c in EXPECT_COLS)


def broken_fixture():
    """人为破坏的输入：逐条引爆 C1–C8、C10a、C10b。"""
    rows = [
        _mkrow(scene_id="sOK", src="ot", seq="5", op="add", task_type="CharacterOpen",
               ps_name="KAZ01", fam="kaz", slot_hint="0", cx="640", cy="0",
               x1920="960", y1920="0", conf="exact", scene_degraded="0"),
        # C8：第二个 add 落在已占用的槽 0（＝修复前的挤槽缺陷）
        _mkrow(scene_id="sOK", src="ot", seq="6", op="add", task_type="CharacterOpen",
               ps_name="ASU01", fam="asu", slot_hint="0", cx="640", cy="0",
               x1920="960", y1920="0", conf="exact", scene_degraded="0"),
        # C7：场 sRM 无 add 却有 remove
        _mkrow(scene_id="sRM", src="ot", seq="7", op="remove", task_type="CharacterDelete",
               ps_name="KAZ09", fam="kaz", conf="inferred", scene_degraded="0"),
        # C3（op 非闭集）+ C5（fam 与 ps_name 不符）
        _mkrow(scene_id="sBad", src="ot", seq="8", op="bogus", task_type="CharacterFrob",
               ps_name="TEN01A", fam="WRONG", slot_hint="3", conf="exact", scene_degraded="0"),
        # C4（seq=0）+ C6（x1920 错）
        _mkrow(scene_id="sBad", src="ot", seq="0", op="add", task_type="CharacterOpen",
               ps_name="BOK01", fam="bok", slot_hint="0", cx="640", cy="0",
               x1920="999", y1920="0", conf="exact", scene_degraded="0"),
        # C4（seq 超界）+ C6（cy 有值但 y1920 空）
        _mkrow(scene_id="sBad", src="ot", seq="9999", op="move", task_type="CharacterMove",
               ps_name="TEN02", fam="ten", slot_hint="1", cx="336", cy="100",
               x1920="504", y1920="", conf="exact", scene_degraded="0"),
        # C2（TAB 数/引号）+ C1（字段数）
        _mkrow(scene_id="sBad", src="ot", seq="9", op="wait", task_type="CharacterWait",
               ps_name='"Q"', fam="", slot_hint="", conf="exact", scene_degraded="0") + "\tEXTRA",
        # C10a：task_type=CharacterMove 却归一成 add（金标说 move）
        _mkrow(scene_id="sX", src="ot", seq="3", op="add", task_type="CharacterMove",
               ps_name="MAS01", fam="mas", slot_hint="0", cx="640", cy="0",
               x1920="960", y1920="0", conf="exact", scene_degraded="0"),
        # C8 + C10b：同族两名挤同槽（登记却声称并存）
        _mkrow(scene_id="sZ", src="ot", seq="4", op="add", task_type="CharacterOpen",
               ps_name="CIN074B", fam="cin", slot_hint="0", cx="640", cy="0",
               x1920="960", y1920="0", conf="exact", scene_degraded="0"),
        _mkrow(scene_id="sZ", src="ot", seq="4", op="add", task_type="CharacterOpen",
               ps_name="CIN074C", fam="cin", slot_hint="0", cx="640", cy="0",
               x1920="960", y1920="0", conf="exact", scene_degraded="0"),
        # 本次 add 之后仍引用旧件名 ⇒ 二者确为并存（C8 挤槽 + C10b 未各持槽）
        _mkrow(scene_id="sZ", src="ot", seq="5", op="move", task_type="CharacterMove",
               ps_name="CIN074B", fam="cin", slot_hint="0", cx="336", cy="0",
               x1920="504", y1920="0", conf="exact", scene_degraded="0"),
        _mkrow(scene_id="sZ", src="ot", seq="5", op="move", task_type="CharacterMove",
               ps_name="CIN074C", fam="cin", slot_hint="0", cx="944", cy="0",
               x1920="1416", y1920="0", conf="exact", scene_degraded="0"),
    ]
    return "\t".join(EXPECT_COLS) + "\n" + "\n".join(rows) + "\n"


BROKEN_REGISTRY = [
    {"scene_id": "sZ", "src": "ot", "task": "5", "fam": "cin",
     "names": "CIN074B,CIN074C", "ops": "move"},
]


def self_test(out_dir):
    text = broken_fixture()
    scene_lines = {"sOK": 50, "sRM": 50, "sBad": 100, "sX": 50, "sZ": 50}
    prod_scene_op = collections.defaultdict(collections.Counter)
    for ln in text.split("\n")[1:]:
        if not ln:
            continue
        fl = ln.split("\t")
        if len(fl) >= 4:
            prod_scene_op[fl[0]][fl[3]] += 1
    exp = {sc: collections.Counter(c) for sc, c in prod_scene_op.items()}
    exp["sX"] = collections.Counter({"move": 1})          # 金标说 move ⇒ 引爆 C10a
    golden_expected = {("sZ", "5", "cin"), ("sY", "100", "cin")}   # sY 故意缺 ⇒ 引爆 C10b(i)

    V, n = run_checks(text, scene_lines=scene_lines, golden=None,
                      golden_scene_op=exp, registry_rows=BROKEN_REGISTRY,
                      registry_expected=golden_expected)

    os.makedirs(out_dir, exist_ok=True)
    fx = os.path.join(out_dir, "劣化输入_自证.tsv")
    with open(fx, "w", encoding="utf-8", newline="") as f:
        f.write(text)

    print("== 自证：人为破坏的输入（%d 行）应逐条引爆 C1–C8 / C10a / C10b ==" % n)
    print("   夹具：%s" % fx)
    all_ok = True
    for crit in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C10a", "C10b"):
        hits = V.get(crit, [])
        ok = len(hits) > 0
        all_ok &= ok
        print("   %-5s 引爆 %d 条  %s" % (crit, len(hits), "OK" if ok else "**未引爆**"))
        for m in hits[:3]:
            print("        - " + m)
    print("== 自证结论：%s ==" % ("每条判据都有牙齿" if all_ok else "有判据未被引爆（判据失效）"))
    return 0 if all_ok else 1


# ---------------------------------------------------------------- 主流程

def pick(name, explicit, data_root):
    if explicit:
        return explicit
    local = os.path.join(HERE, name)
    if os.path.isfile(local):
        return local
    return os.path.join(data_root, GAME_DIR, PSV_SUB, name)


def main(argv=None):
    ap = argparse.ArgumentParser(description="立绘事件流 · 独立校验器（C1–C10）")
    ap.add_argument("--tsv", default=os.path.join(HERE, "立绘事件流.tsv"))
    ap.add_argument("--scene-map", default=None)
    ap.add_argument("--timeline", default=None)
    ap.add_argument("--registry", default=None, help="同族并存登记.tsv（默认本目录）")
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT)
    ap.add_argument("--skip-golden", action="store_true", help="不做 C9/C10a/C10b 的金标对拍")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--out", default=DEFAULT_EVIDENCE, help="自证证据落盘目录")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.out)

    if not os.path.isfile(args.tsv):
        sys.exit("找不到 %s" % args.tsv)
    with open(args.tsv, encoding="utf-8", newline="") as f:
        text = f.read()

    scene_lines = None
    sm = pick("场景映射.tsv", args.scene_map, args.data_root)
    if os.path.isfile(sm):
        scene_lines = parse_scene_map(sm)
        print("[in] scene map = %s" % sm)
    else:
        print("[warn] 无场景映射 ⇒ 跳过 C4 上界")

    golden = golden_scene_op = coexist_expected = None
    registry_rows = []
    reg_path = pick("同族并存登记.tsv", args.registry, args.data_root)
    if os.path.isfile(reg_path):
        registry_rows, _ = parse_registry(reg_path)
        print("[in] registry  = %s" % reg_path)

    if not args.skip_golden:
        tl = pick("时间线.tsv", args.timeline, args.data_root)
        if os.path.isfile(tl):
            golden, golden_scene_op, coexist_expected = parse_golden(tl)
            print("[in] golden    = %s" % tl)
        else:
            print("[warn] 无金标 ⇒ 跳过 C9/C10")

    V, n = run_checks(text, scene_lines=scene_lines, golden=golden,
                      golden_scene_op=golden_scene_op, registry_rows=registry_rows,
                      registry_expected=coexist_expected)
    print("[check] 数据行 %d" % n)
    bad = 0
    for crit in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10a", "C10b"):
        hits = V.get(crit, [])
        print("  %-5s %s" % (crit, "PASS" if not hits else "FAIL(%d)" % len(hits)))
        for m in hits[:5]:
            print("      - " + m)
        bad += len(hits)
    print("[check] ALL_PASS = %s" % (bad == 0))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
