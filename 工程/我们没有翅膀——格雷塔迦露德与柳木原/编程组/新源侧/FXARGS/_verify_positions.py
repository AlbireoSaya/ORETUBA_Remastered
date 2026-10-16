#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_verify_positions.py —— `效果族参数位.tsv` 的**可失败**校验 + 变异自证。

三种运行：
  python -X utf8 _verify_positions.py                 # 正常校验（应 PASS）
  python -X utf8 _verify_positions.py --selftest      # 正常校验 + 两种变异；变异**必须 FAIL**
  python -X utf8 _verify_positions.py --mutate pos    # 只跑变异体（把某 PSV对拍 判据改坏）
  python -X utf8 _verify_positions.py --mutate scale  # 只跑变异体（帧换算常数 0.06→0.05）

校验项（每条都可失败）
  C1 `来源` ∈ {PSV对拍, PC自证, 未证}
  C2 `来源=PSV对拍` ⇒ 表内命中率与**从原始数据重算**的数值逐位一致（找不到规格 ⇒ FAIL）
  C3 `来源=PSV对拍` ⇒ 达到门槛：exact ≥0.90 且 exact 样本 ≥10（或 seq ≥0.90 且样本 ≥20），
     且相对**置换基线**的最大增益 ≥ 0.15
  C4 `来源=未证` 且表内有命中率 ⇒ **不得**达到 C3 门槛（达到 ⇒ 该位应升档，FAIL）
  C5 `语义` 含「未证/疑」⇒ `来源` 必须为 `未证`（禁忌：把值域猜测写成已解）
  C6 `来源=PC自证` ⇒ `语义` 必须属**直证白名单**（控制流选择子 / 常量 / 方向 token / 素材路径）
  C7 `位号` < argc（读到 argc 之外必须被显式标出，本表不允许静默越界）
  C8 对拍样本量 < 10 ⇒ 该行必须出现「样本小」
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _probe_psv_join as PJ            # noqa: E402
import _emit_positions as EM            # noqa: E402

TABLE = os.path.join(HERE, "效果族参数位.tsv")
SRC = EM.SRC
THRESH_RATE = 0.90
THRESH_GAIN = 0.15

PC_WHITELIST = ["转场图案选择子", "常量，无信息", "方向 token", "素材路径"]


def load_table(path=TABLE):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) < len(head):
                p += [""] * (len(head) - len(p))
            rows.append(dict(zip(head, p)))
    return rows


def specs_of(mutate=None):
    """返回 {(V, pos): (types, nz, gnz)}；`mutate` 用于把判据改坏。"""
    m = {}
    for (v, pos, types, nz, gnz) in EM.SPECS:
        if mutate == "pos" and v == "0x1B69C" and pos == 5:
            pos = 4                     # 变异①：把「位 5 = 时长」改成「位 4 = 时长」
        m[(v, pos)] = (types, nz, gnz)
    return m


def scale_of(mutate):
    return 0.05 if mutate == "scale" else 0.06


def recompute(v, pos, types, nz, gnz, scale):
    """-> {src: {...}}  逐源重算（与 `_probe_psv_join.join` 同口径）。"""
    out = {}
    for src in SRC.split(","):
        rr = PJ.join(src, v, pos, types.split("+"), nz, gold_nz=gnz, scale=scale)
        if rr["n"]:
            out[src] = rr
    return out


def rates(d):
    """三口径的 (rate, num, den) + 置换基线（取三口径里分母≥10 的最大增益）。"""
    res = {}
    for k in ("exact", "seq", "scene"):
        num, den = d[k], d["n_" + k]
        nu = d.get("null", {})
        nnum, nden = nu.get(k, 0), nu.get("n_" + k, 0)
        res[k] = (num, den, (num / den if den else None),
                  (nnum / nden if nden else None))
    return res


def primary_src(comp):
    """主源 = 对拍分母最大者（本批恒为 ot；otr 只作跨 build 复现）。"""
    return max(comp.items(), key=lambda kv: max(kv[1]["n_exact"], kv[1]["n_seq"],
                                                kv[1]["n_scene"]))[0]


def meets_threshold(d):
    """C3 门槛：exact 优先，或 seq；且最大增益 ≥ 0.15。返回 (bool, 说明)"""
    r = rates(d)
    best_gain = None
    ok = False
    why = []
    for k in ("exact", "seq"):
        num, den, rate, base = r[k]
        if rate is None:
            continue
        need = 10 if k == "exact" else 20
        if den >= need and rate >= THRESH_RATE:
            ok = True
            why.append("%s=%d/%d 达 %.2f（样本 %d≥%d）" % (k, num, den, rate, den, need))
    for k in ("exact", "seq", "scene"):
        num, den, rate, base = r[k]
        if rate is None or base is None or den < 10:
            continue
        g = rate - base
        if best_gain is None or g > best_gain:
            best_gain = g
    if ok and (best_gain is None or best_gain >= THRESH_GAIN):
        why.append("最大增益 %.3f ≥ %.2f" % (best_gain, THRESH_GAIN))
        return True, "；".join(why)
    return False, "；".join(why + ["最大增益 %s（需 ≥ %.2f）" %
                                   ("%.3f" % best_gain if best_gain is not None else "-",
                                    THRESH_GAIN)])


def check(mutate=None, verbose=True):
    rows = load_table()
    sp = specs_of(mutate)
    scale = scale_of(mutate)
    fails = []
    n_psv = n_pc = n_un = 0
    for r in rows:
        srcn = r["来源"]
        if srcn not in ("PSV对拍", "PC自证", "未证"):
            fails.append("C1 %s 位%s 来源非法：%r" % (r["V"], r["位号"], srcn))
        if srcn == "PSV对拍":
            n_psv += 1
            key = (r["V"], int(r["位号"]))
            if key not in sp:
                fails.append("C2 %s 位%s 标 PSV对拍，但规格表里没有该位的判据" % key)
                continue
            types, nz, gnz = sp[key]
            comp = recompute(r["V"], int(r["位号"]), types, nz, gnz, scale)
            if not comp:
                fails.append("C2 %s 位%s 重算无样本" % key)
                continue
            prim = primary_src(comp)
            for src, d in comp.items():
                # C2：逐源比对**分数**（分母 0 跳过）
                if d["n_exact"]:
                    tag = "exact %d/%d" % (d["exact"], d["n_exact"])
                    if tag not in r["命中率"]:
                        fails.append("C2 %s 位%s 表内命中率与重算不一致：表缺 %r"
                                     % (key[0], key[1], tag))
                if d["n_seq"]:
                    tag = "seq %d/%d" % (d["seq"], d["n_seq"])
                    if tag not in r["命中率"]:
                        fails.append("C2 %s 位%s 表内命中率与重算不一致：表缺 %r"
                                     % (key[0], key[1], tag))
                # C3：门槛只压**主源**（样本最大者）；另一 build 只作跨 build 复现记录
                if src == prim:
                    ok, why = meets_threshold(d)
                    if not ok:
                        fails.append("C3 %s 位%s（%s）未达门槛：%s" % (key[0], key[1], src, why))
        elif srcn == "PC自证":
            n_pc += 1
            if not any(w in r["语义"] for w in PC_WHITELIST):
                fails.append("C6 %s 位%s 标 PC自证 但语义不属直证白名单：%r"
                             % (r["V"], r["位号"], r["语义"]))
        else:
            n_un += 1
            if "未证" not in r["语义"] and "疑" not in r["语义"]:
                if r["语义"] != "-":
                    fails.append("C5? %s 位%s 来源=未证 但语义未写「未证/疑」：%r"
                                 % (r["V"], r["位号"], r["语义"]))
            if r["命中率"] and r["命中率"] != "-":
                key = (r["V"], int(r["位号"]))
                if key in sp:
                    types, nz, gnz = sp[key]
                    comp = recompute(r["V"], int(r["位号"]), types, nz, gnz, scale)
                    if comp:
                        src0 = primary_src(comp)
                        ok, why = meets_threshold(comp[src0])
                        if ok:
                            fails.append("C4 %s 位%s 标未证 但主源(%s)重算达到门槛（应升档）：%s"
                                         % (key[0], key[1], src0, why))
        # C5 语义含未证/疑 ⇒ 来源必须未证
        if ("未证" in r["语义"] or "疑" in r["语义"]) and srcn != "未证":
            fails.append("C5 %s 位%s 语义含「未证/疑」但来源=%s" % (r["V"], r["位号"], srcn))
        # C7 位号 < argc
        acs = [int(x.split("×")[0]) for x in r["argc"].split(",") if "×" in x]
        if acs and int(r["位号"]) >= max(acs):
            fails.append("C7 %s 位%s 越界（argc=%s）" % (r["V"], r["位号"], r["argc"]))
        # C8 样本小
        nums = [int(x) for x in re.findall(r":(\d+)", r["对拍样本量"] or "")]
        if nums and max(nums) < 10 and "样本小" not in r["命中率"] and "样本小" not in r["备注"]:
            fails.append("C8 %s 位%s 对拍样本量 %s < 10 但未标「样本小」"
                         % (r["V"], r["位号"], r["对拍样本量"]))
    if verbose:
        print("== 校验（mutate=%s, scale=%.2f）==" % (mutate, scale))
        print("  表行 %d（PSV对拍 %d / PC自证 %d / 未证 %d）" % (len(rows), n_psv, n_pc, n_un))
        if fails:
            print("  失败 %d 条：" % len(fails))
            for x in fails[:20]:
                print("   - " + x)
        print("VERDICT = %s" % ("PASS" if not fails else "FAIL"))
    return not fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", choices=["pos", "scale"])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.mutate:
        ok = check(mutate=a.mutate)
        return 0 if ok else 1
    if a.selftest:
        print("### ① 正常校验")
        ok1 = check()
        print("### ② 变异 A：把 0x1B69C 的「位5=时长」判据改坏成「位4」（表仍列位5）")
        ok2 = check(mutate="pos")
        print("### ③ 变异 B：把帧换算常数 0.06 改坏成 0.05")
        ok3 = check(mutate="scale")
        print("### 汇总：正常=%s / 变异A=%s / 变异B=%s → 自证 %s" % (
            "PASS" if ok1 else "FAIL", "PASS" if ok2 else "FAIL",
            "PASS" if ok3 else "FAIL",
            "通过（变异都 FAIL）" if (ok1 and not ok2 and not ok3) else "**未通过**"))
        return 0 if (ok1 and not ok2 and not ok3) else 1
    ok = check()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
