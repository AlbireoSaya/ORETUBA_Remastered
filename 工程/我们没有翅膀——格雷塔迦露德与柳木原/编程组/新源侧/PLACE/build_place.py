#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_place.py —— 合并产出 `立绘落位_{ot,otr,otp}.tsv`（ISSUE-20261008-09 / PLACE 模块 · C）

列（任务书指定）:
  scene_id src seq ord fam name slot dir_token x1920 y1920 z_rank conf evidence

- `x1920`/`y1920` 由 `place_dsl.py`（A 模块，原生 token DSL 运行期求值）给出。
- `z_rank` 由 `layer_by_slot.py`（B 模块，槽号升序 ⇒ 名次即绘制序，名次大者在前）给出。
- `conf` 闭集 4 值（**只描述证据强度**，按强度升序，取本行最弱一环）:
    `slot缺`      —— 无槽号 ⇒ 层序与位置状态均不可定
    `token未覆盖` —— 位置没有落进已解 DSL 的覆盖范围
                     （(a) 该族位置不由 token 携带、无控制串；(b) 控制串含 unresolved token）
    `fb待定`      —— 位置已解，但 f/b 前缀使**层序规则未覆盖**
    `DSL已解`     —— 位置已解且无 f/b 标志（**v1 口径**）
  ★ **v1 的 `DSL已解` 与 v2 的 `conf` 不是同一档**（2026-10-09 同步）：v2（`..\\PAIR\\立绘落位_*_v2.tsv`）
    已把证据强度拆成 5 档——`DSL已解` ＋ `弱推断(UNP-7)` / `默认值未证(UNP-1)` / `源类比未对拍(otp|otr)`；
    v1 的 `DSL已解` 只表示「**本行**静态 DSL 求值成功」（ot 958 行）、不含状态机推导
    ⇒ **下游按 `conf` 取数一律以 v2 为准**（见 `..\\说明.md` §四、`..\\PAIR\\未证但已采用.tsv`）。
- `evidence` 为 `解出_<src>.tsv` 的 evidence 原文（含完整 32 位实参向量与 V 号），逐字保留。

CLI:
  python -X utf8 build_place.py --emit
  python -X utf8 build_place.py --check
  python -X utf8 build_place.py --selfcheck-mutate
  python -X utf8 build_place.py --verify
"""
import collections
import csv
import hashlib
import os
import sys

sys.dont_write_bytecode = True   # 只读：不得在 PLACE 目录产生 __pycache__（2026-10-09 补，与 compare_gold/layer_by_slot/pair_place 同款）

import place_dsl as P
import layer_by_slot as L

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "立绘落位_%s.tsv"
HEAD = ["scene_id", "src", "seq", "ord", "fam", "name", "slot", "dir_token",
        "x1920", "y1920", "z_rank", "conf", "evidence"]


import re

_TOKRE = re.compile(r"![clr]|[lr]?[<>]\d+|[clr][+-]\d+|[<>]|[clr]|[+-]\d+|[du]|[_$]")


def dir_token(ctrl):
    """控制串里第一个方位 token（与 SOB0ARGS 的 dir_token 同口径：长优先）。"""
    if not ctrl:
        return ""
    m = _TOKRE.search(ctrl)
    return m.group(0) if m else ""


def build_src(src, dsl=None):
    dsl = P.DSL if dsl is None else dsl
    rows = P.build_rows(src, dsl)
    _, zmap, _ = L.compute_z(src, build=rows)
    out = []
    for r, f in rows:
        ctrl = f.get("ctrl") or ""
        out.append([
            r["scene_id"], src, str(r["seq"]), str(f["ord"]),
            P.fam_short(f["fdef"]["role"]), f.get("name") or "",
            "" if f.get("slot") is None else str(f["slot"]),
            dir_token(ctrl),
            "" if f.get("x") is None else str(f["x"]),
            "" if f.get("y") is None else str(f["y"]),
            zmap.get((r["scene_id"], r["file_idx"]), ""),
            f.get("conf") or "",
            r["evidence"],
        ])
    return out


def render(src, dsl=None):
    lines = ["\t".join(HEAD)]
    for row in build_src(src, dsl):
        lines.append("\t".join(row))
    return "\n".join(lines) + "\n"


def artifacts(dsl=None):
    return {OUT % src: render(src, dsl) for src in P.SRCS}


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def do_emit():
    for name, txt in sorted(artifacts().items()):
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
        b = txt.encode("utf-8")
        print("  WROTE %-28s %d bytes  sha256=%s" % (name, len(b), sha(b)))
    return True


def do_check(mutate=None):
    dsl = dict(P.DSL)
    if mutate:
        dsl[mutate[0]] = mutate[1]
    arts = artifacts(dsl)
    allpass, ndiff = True, 0
    for name in sorted(arts):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            print("  MISS     %-28s" % name)
            allpass, ndiff = False, ndiff + 1
            continue
        with open(p, "rb") as f:
            ondisk = f.read()
        new = arts[name].encode("utf-8")
        if sha(ondisk) == sha(new):
            print("  OK       %-28s %d bytes  sha256=%s" % (name, len(ondisk), sha(ondisk)))
        else:
            a = ondisk.decode("utf-8").splitlines()
            b = arts[name].splitlines()
            d = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            print("  DIFF     %-28s %d 行不一致" % (name, d))
            allpass, ndiff = False, ndiff + 1
    print("ALL_PASS=%s  files=%d  diff_files=%d" % (allpass, len(arts), ndiff))
    print("READONLY=True（本模式不写任何文件）")
    return allpass


def expected_family_rows(src):
    """独立复算（不复用 build_rows 的过滤逻辑）：直接数 解出_<src>.tsv 里 V ∈ FAMILY[src] 的行。"""
    fam = P.FAMILY[src]
    n = 0
    per_v = collections.Counter()
    with open(os.path.join(P.SOB0_DIR, "解出_%s.tsv" % src), encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            v = (row["arg3"] or "").replace("V=", "")
            if v in fam:
                n += 1
                per_v[v] += 1
    return n, per_v


def _count_x(src):
    n = collections.Counter()
    for r, f in P.build_rows(src):
        if f.get("x") is not None:
            n["num"] += 1
        elif f.get("x_class") == "off_left":
            n["off_left"] += 1
        elif f.get("x_class") == "off_right":
            n["off_right"] += 1
    tot = n["num"] + n["off_left"] + n["off_right"]
    return tot, n["num"], n["off_left"], n["off_right"]


def do_verify():
    ok = True
    print("== V1 行数逐行对账（输出行数 vs 输入立绘族行数）==")
    for src in P.SRCS:
        p = os.path.join(HERE, OUT % src)
        with open(p, encoding="utf-8", newline="") as f:
            got = list(csv.DictReader(f, delimiter="\t"))
        exp_n, per_v = expected_family_rows(src)
        delta = len(got) - exp_n
        flag = "PASS" if delta == 0 else "FAIL"
        if delta != 0:
            ok = False
        print("  [%s] %-4s 输入立绘族 %d 行  输出 %d 行  差额 %d"
              % (flag, src, exp_n, len(got), delta))
        # 逐 (scene_id,seq,ord) 唯一性
        keys = collections.Counter((r["scene_id"], r["seq"], r["ord"]) for r in got)
        dup = sum(1 for k, v in keys.items() if v > 1)
        print("       逐行键 (scene_id,seq,ord) 重复数 = %d %s" % (dup, "PASS" if dup == 0 else "FAIL"))
        if dup:
            ok = False
        # 逐 V 对账
        got_v = collections.Counter()
        for r in got:
            v = r["evidence"]
            i = v.find("V=")
            got_v[v[i + 2:i + 2 + 7].split()[0]] += 1
        ds = {k: got_v.get(k, 0) - per_v.get(k, 0) for k in set(got_v) | set(per_v)}
        bad = {k: d for k, d in ds.items() if d != 0}
        print("       逐 V 对账差异 V 数 = %d %s" % (len(bad), "PASS" if not bad else "FAIL %s" % bad))
        if bad:
            ok = False
    print()
    print("== V2 conf 分布与闭集 ==")
    for src in P.SRCS:
        with open(os.path.join(HERE, OUT % src), encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        c = collections.Counter(r["conf"] for r in rows)
        extra = set(c) - {"DSL已解", "token未覆盖", "slot缺", "fb待定"}
        print("  %-4s %s  %s" % (src, dict(c), "PASS" if not extra else "FAIL 越界值 %s" % extra))
        if extra:
            ok = False
    print()
    print("== V3 x1920 与 conf 的一致性 ==")
    for src in P.SRCS:
        with open(os.path.join(HERE, OUT % src), encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        bad = sum(1 for r in rows if r["conf"] == "token未覆盖" and r["x1920"] != "")
        ok_flag = (bad == 0)
        if not ok_flag:
            ok = False
        # `slot缺` 是**层序侧**的缺口，与「位置能否由 token 自证」无关：
        # ot/otr 的 0x10428 族位置在 pos5 控制串里、但族内无槽号 ⇒ 有 x1920 而无槽号属预期
        nslot = sum(1 for r in rows if r["conf"] == "slot缺" and r["x1920"] != "")
        print("  %-4s token未覆盖却给 x1920 = %d %s ｜ slot缺但给 x1920 = %d（预期非 0，仅位置可自证而层序不可）"
              % (src, bad, "PASS" if ok_flag else "FAIL", nslot))
    print()
    print("== V4 z_rank 与 conf 的一致性 ==")
    for src in P.SRCS:
        with open(os.path.join(HERE, OUT % src), encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        nbad = sum(1 for r in rows if r["slot"] == "" and r["z_rank"] != "")
        nbad += sum(1 for r in rows if r["conf"] == "fb待定" and r["z_rank"] != "")
        print("  %-4s slot空却给 z_rank / fb待定却给 z_rank 的行数 = %d %s" % (src, nbad, "PASS" if nbad == 0 else "FAIL"))
        if nbad:
            ok = False
    print()
    print("== V6 conf 子类细分（`token未覆盖` 的内部构成，便于判读覆盖缺口）==")
    for src in P.SRCS:
        sub = collections.Counter()
        for r, f in P.build_rows(src):
            if f.get("conf") != "token未覆盖":
                continue
            ctrl = f.get("ctrl")
            if ctrl is None:
                sub["(a) 该族位置不由 token 携带（无控制串）"] += 1
            elif f.get("unks"):
                sub["(b) 控制串含 unresolved token"] += 1
            else:
                sub["(c) 控制串已全解但无绝对锚点（纯相对/保持档）"] += 1
        print("  %-4s %s" % (src, dict(sub)))
        print("       x1920 有值行数 = %d ｜ 其中 x_class=num %d / off_left %d / off_right %d"
              % (_count_x(src)))
    print()
    print("== V5 列数 ==")
    for src in P.SRCS:
        p = os.path.join(HERE, OUT % src)
        with open(p, encoding="utf-8", newline="") as f:
            rd = csv.reader(f, delimiter="\t")
            hdr = next(rd)
            bad = 0
            for row in rd:
                if len(row) != len(HEAD):
                    bad += 1
        print("  %-4s 表头 %d 列  逐行列数异常 %d %s" % (src, len(hdr), bad,
              "PASS" if (hdr == HEAD and bad == 0) else "FAIL"))
        if hdr != HEAD or bad:
            ok = False
    print()
    print("VERIFY_ALL_PASS=%s" % ok)
    return ok


def main(argv):
    if "--emit" in argv:
        do_emit()
        return 0
    if "--check" in argv:
        return 0 if do_check() else 1
    if "--selfcheck-mutate" in argv:
        print("== CHECK(MUTATE: DSL['r'] 1416 -> 1) ==")
        okd = do_check(mutate=("r", ("abs", 1)))
        print("MUTATE_SELFTEST=%s（期望 check FAIL）" % ("PASS" if not okd else "FAIL"))
        return 0 if not okd else 1
    if "--verify" in argv:
        return 0 if do_verify() else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
