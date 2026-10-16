#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
素材引用 → 美术交付件 映射器   (ISSUE-20260930-03 / greta-resource-audit)
================================================================================
**只读**。产出两张表：

  1. `资源组\交接编程组\素材库到统一名.tsv`——**全量**「素材库原件 → 美术统一名」映射
     （chr 3,741 + pic 1,920 + sys 2,267 逐件一行），含该件所属去重组的分类与是否代表件。
     **这是 `美术统一\清单_*.tsv` 与 `美术统一_交付\交付清单.tsv` 都没有的东西**：
     两张表只登记「每组的选中代表件」（`选中源`/`选中原名`），组内其余候选无从查得。
  2. `资源组\交接编程组\素材引用映射.tsv`——剧本 `assets[].out_relpath` 逐条映射结论
     （含「同组代表替代是否等价」判定），供编程组按剧本取图。
  对账结论与自证数据写在 `资源组\审计\`（`映射汇总.json` / `映射_未覆盖.tsv`）。

**命名规则的来源（不臆造，逐条对齐实现）**：
  - `chr`：`unify_chr.normalize()`（`工具\unify_chr.py:60`）→ 分组键 `key[:4]`；
    统一名 = 组内**源优先级最高**候选的 stem + `.png`（`unify_chr_w11e.py:223`）。
    np 的内容归并由 `美术统一\_npmerge_chr.tsv` 给出（`unify_chr_w11e.py:120-210`）。
  - `pic`：分组键 = 文件名去 `<源>_` 前缀后小写（`unify_pic.py:132`）；统一名 = 该 stem + `.png`。
  - `sys`：`norm_key()` = 文件名去 `SRC_PREFIX` 前缀后小写（`unify_sys.py:124-131`）；统一名 = 该键。

**自证（必须全绿，否则说明规则复刻有误、本表不可信）**：
  用「清单里每个代表件的 (`选中源`,`选中原名`)」反查本表，**逐件**核对是否得到该行的 `统一名`；
  另核「本表 统一名 集合 ⊇ 清单 统一名 集合」。

用法：
  python map_scene_art_refs.py [--data-root <主工作区>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys

GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
CAT2KIND = {"立绘": "chr", "CG背景": "pic", "系统UI": "sys"}


def find_main_workspace(cli):
    if cli:
        return os.path.abspath(cli)
    env = os.environ.get("GALGAME_MAIN")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        cur = os.path.dirname(cur)
        if os.path.isfile(os.path.join(cur, "工程", GAME, "资源组", "krkr素材库", "资源总账.json")):
            return cur
    raise SystemExit("[FATAL] 未找到主工作区，请用 --data-root 指定")


def assert_in_checkout(path):
    here = os.path.dirname(os.path.abspath(__file__))
    checkout = here
    for _ in range(4):
        if os.path.isdir(os.path.join(checkout, ".git")) or os.path.isfile(
            os.path.join(checkout, ".git")
        ):
            break
        checkout = os.path.dirname(checkout)
    p = os.path.abspath(path)
    if not (p == checkout or p.startswith(checkout + os.sep)):
        raise SystemExit(f"[FATAL] 产物路径不在本 checkout 内，拒绝写入：{p}")
    return p


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def strip_ext(n):
    return n[:-4] if n.lower().endswith(".png") else n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    a = ap.parse_args()
    data = find_main_workspace(a.data_root)
    res = os.path.join(data, REL_RES)
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = assert_in_checkout(os.path.join(here, "..", "审计"))
    os.makedirs(outdir, exist_ok=True)
    # 两张表是**交给编程组的产物**（跨组交付件），落在 `交接编程组\`；
    # `审计\` 只放对账结论与自证数据。
    handoff = assert_in_checkout(os.path.join(here, "..", "交接编程组"))
    os.makedirs(handoff, exist_ok=True)

    sys.path.insert(0, here)
    import unify_chr as UC  # noqa: E402  复刻 chr 归一化（只读、无副作用）

    # ---------------------------------------------------------------- 素材库枚举
    with open(os.path.join(res, "krkr素材库", "资源总账.json"), encoding="utf-8") as f:
        entries = json.load(f)["entries"]
    # `otv\etc\` 与 `otv\sys\` 同属系统UI命名空间（unify_sys.py:124 口径），
    # 故 kind=etc 的 124 件一并按 sys 处理，否则 otv 的 124 件会全部"无归属"。
    KIND_ALIAS = {"etc": "sys"}
    lib = collections.defaultdict(list)          # kind -> [ {kind,src,name} ]
    for e in entries:
        k = KIND_ALIAS.get(e["kind"], e["kind"])
        if k in ("chr", "pic", "sys"):
            lib[k].append({"kind": k, "src": e["source"], "name": e["filename"]})

    PRIO = UC.PRIO

    # ---------------------------------------------------------------- 清单侧（权威）
    # **(kind, 源, 文件名) -> [(统一名, 类别)]**。清单的 `选中原名` 只写文件名、不带目录，
    # 而同一文件名可能同时存在于 `chr\` / `pic\` / `sys\`（如 `ot_asu01.png` 既是立绘又是 CG）。
    # 故按**产物类别**定位到对应目录登记（立绘↔chr、CG背景↔pic、系统UI↔sys/etc）；
    # 该目录下没有该文件时（`np` 立绘实体在 `chr\`、`cin*` 在 `chr\` 归 CG背景 等跨类别归属）
    # 才退到其它目录——**先匹配类别，再兜种类**，避免同名跨目录串味。
    lib_keys = {(k, rec["src"], rec["name"]) for k, recs in lib.items() for rec in recs}
    reps = {}                                     # (kind, src, name) -> [(uname, cat)]
    uname_cat = {}                                # uname -> 类别
    uname_cls = {}                                # uname -> 该组分类
    for cat, fn in (("立绘", "清单_立绘.tsv"), ("CG背景", "清单_CG背景.tsv"),
                    ("系统UI", "清单_系统UI.tsv")):
        home = CAT2KIND[cat]
        for r in read_tsv(os.path.join(res, "美术统一", fn)):
            sp = (r.get("选中源") or "").strip().lower()
            on = (r.get("选中原名") or "").strip()
            if not sp or not on:
                continue
            if not on.lower().endswith(".png"):
                on = on + ".png"
            for k in [home] + [x for x in lib if x != home]:
                if (k, sp, on) in lib_keys:
                    reps.setdefault((k, sp, on), []).append((r["统一名"], cat))
                    break
            uname_cat[r["统一名"]] = cat
            uname_cls[r["统一名"]] = r.get("分类", "")

    # ---------------------------------------------------------------- 分组
    def chr_key(rec):
        k = UC.normalize(rec["src"], rec["name"])
        return (k[0], k[1], k[2], k[3])

    def stem_key(rec):
        """pic / sys 的组键＝文件名**去扩展名、去 `<源>_` 前缀**后小写
        （`unify_pic.py:132` / `unify_sys.py:124` 的键口径；扩展名不参与键）。"""
        n = rec["name"]
        if n.lower().endswith(".png"):
            n = n[:-4]
        if not n.lower().startswith(rec["src"] + "_"):
            raise SystemExit("%s 前缀异常: %s/%s" % (rec["kind"], rec["src"], rec["name"]))
        return n[len(rec["src"]) + 1 :].lower()

    npmerge = {}
    p_np = os.path.join(res, "美术统一", "_npmerge_chr.tsv")
    if os.path.isfile(p_np):
        for r in read_tsv(p_np):
            npmerge[r["np原名"]] = r["配对目标组(统一名)"]

    def group_key(rec):
        if rec["kind"] == "chr":
            if rec["name"] in npmerge:            # np 内容归并：目标组统一名已确定
                return ("_npmerge_", npmerge[rec["name"]])
            return chr_key(rec)
        return stem_key(rec)

    deliv = {}
    for r in read_tsv(os.path.join(res, "美术统一_交付", "交付清单.tsv")):
        deliv[r["统一名"]] = r["交付相对路径"]

    KIND2CAT = {"chr": "立绘", "pic": "CG背景", "sys": "系统UI"}
    groups = collections.defaultdict(list)        # (kind, key) -> [rec]
    for kind, recs in lib.items():
        for rec in recs:
            groups[(kind, group_key(rec))].append(rec)

    # ---------------------------------------------------------------- 组 → 统一名
    uname_of = {}                                 # (kind, src, name) -> uname
    split_groups, norep_groups, ambiguous, norep_recovered = [], [], [], []
    def guess_for(mem, kind, want_cat):
        """按**本类别的命名规则**反查该组应有的统一名。

        chr → `unify_chr.normalize()` 的 stem + `.png`；pic/sys → 去源前缀的 stem，
        候选顺序为 `cg_`/`ui_` 前缀件优先（跨类撞名时前缀件才属于本类）、再取无前缀件。

        **允许跨类别命中**：`cin*` 133 件实体在 `chr\\`、产物却归 `CG背景`（W12 迁移，
        已入库登记），这类跨类归属是**源数据事实**，不得拒收。同名跨类时（如
        `ot_asu04.png` 同时是 `cg_asu04.png`/`ui_asu04.png` 的代表件）由候选顺序化解：
        chr 组只取 `asu04.png`，pic 组先取 `cg_asu04.png`。同类别候选优先。
        """
        order = sorted(mem, key=lambda x: (PRIO[x["src"]], x["name"]))
        for r in order:
            if kind == "chr":
                cands = [UC.normalize(r["src"], r["name"])[4] + ".png"]
            else:
                stem = stem_key(r)
                pref = "cg_" if kind == "pic" else "ui_"
                cands = [pref + stem + ".png", stem + ".png"]
            hit = [c for c in cands if c in uname_cat]
            if hit:
                same = [c for c in hit if uname_cat[c] == want_cat]
                return (same or hit)[0]
        return None

    for (kind, key), mem in groups.items():
        want_cat = KIND2CAT[kind]
        # 组的兜底候选：本组成员都没有「自身清单登记」时使用（跨 kind 同名 / np 归并夺位 /
        # `cin*` 跨类别归属三种情形），按本类命名规则反查；
        # `_npmerge_` 组例外——组键本身就是 `_npmerge_chr.tsv` 给出的**目标统一名**，直接采用。
        group_guess = key[1] if key[0] == "_npmerge_" else guess_for(mem, kind, want_cat)
        for r in mem:
            own = {u: c for u, c in reps.get((kind, r["src"], r["name"]), [])}
            if len(own) == 1:
                # **逐件权威**：清单里这个原件只被一个产物登记 → 直接采用（不受 kind 推类别影响；
                # `np` 的立绘实体在 `pic\`、`cin*` 在 `chr\`、`ss_bg*_full` 在 `otv\sys\` 都靠这条归位）。
                u = next(iter(own))
            elif len(own) > 1:
                # 同一原件被 ≥2 个产物登记（如 `ot_asu04.png` 同时是 `cg_asu04.png` 与
                # `ui_asu04.png` 的代表）→ 只在本组类别内挑；挑不出就走命名规则，**绝不兜底取别类**。
                pref = [x for x, c in own.items() if c == want_cat]
                u = pref[0] if len(pref) == 1 else (group_guess if group_guess in own else None)
            else:
                u = group_guess
            if not u:
                norep_groups.append((kind, "%s[%s]" % (str(key)[:50], r["name"]), 1))
                continue
            uname_of[(kind, r["src"], r["name"])] = u
        if group_guess and all(
            uname_of.get((kind, r["src"], r["name"])) == group_guess for r in mem
        ):
            norep_recovered.append(dict(类=kind, 组键=str(key)[:60], 推得统一名=group_guess,
                                        成员数=len(mem),
                                        成员="/".join(r["name"] for r in mem[:6])))

    # ---------------------------------------------------------------- 拆分产物（权威覆盖）
    # `美术统一\_w11e_拆分明细.tsv`（立绘）与 `_w11g_拆分明细.tsv`（系统UI）是 unify 侧
    # 对「宽高比门控拆组」的**原始判定记录**，逐组给出「主产物 / 拆出产物」及其成员簇。
    # 分组规则无法从名字复原这一步（如 `mis01_altota.png` 的成员是 `ota_mis01` **和**
    # `otv_st_mis01`，源代号与 `_alt` 后缀不一致），故**以该明细为最终依据覆盖**。
    name2kind = {}
    overrides: list[dict] = []
    for k, recs in lib.items():
        for rec in recs:
            name2kind.setdefault((rec["src"], rec["name"]), k)

    def override(kind_src: str, name: str, uname: str, why: str):
        k = name2kind.get((kind_src, name))
        if k is None:
            return False
        if uname not in uname_cat:
            return False
        uname_of[(k, kind_src, name)] = uname
        overrides.append(dict(源=kind_src, 文件=name, 类别=KIND2CAT[k], 统一名=uname, 依据=why))
        return True

    for row in read_tsv(os.path.join(res, "美术统一", "_w11e_拆分明细.tsv")):
        main_orig = (row.get("主产物") or "").strip()
        uname_main = (row.get("统一名") or "").strip()
        alt_uname = (row.get("拆出产物") or "").strip()
        cluster = (row.get("簇") or "").strip()
        for s in UC.SRCS:
            if main_orig.lower().startswith(s + "_"):
                override(s, main_orig, uname_main, "w11e 拆分明细·主产物")
        # 簇里 `||` 两侧的顺序在既有 5 行中**不一致**（`cit001` 行的主产物在右侧、
        # `mis01*` 行在左侧），故不按左右解析：**除 `主产物` 外的全部成员归拆出产物**。
        names = [t.strip() for t in re.split(r"[|,;\s]+", cluster) if "." in t]
        for tok in names:
            if tok == main_orig:
                continue
            for s in UC.SRCS:
                if tok.lower().startswith(s + "_"):
                    override(s, tok, alt_uname, "w11e 拆分明细·拆出产物成员")

    for row in read_tsv(os.path.join(res, "美术统一", "_w11g_拆分明细.tsv")):
        uname_main = (row.get("统一名") or "").strip()
        s1 = (row.get("主产物源") or "").strip().lower()
        n1 = (row.get("主产物") or "").strip()
        s2 = (row.get("拆出产物源") or "").strip().lower()
        n2 = (row.get("拆出产物") or "").strip()
        if s1 and n1:
            override(s1, n1, uname_main, "w11g 拆分明细·主产物")
        if s2 and n2:
            override(s2, n2, n2, "w11g 拆分明细·拆出产物")

    # ---------------------------------------------------------------- 自证
    all_unames = set(uname_of.values())
    uncovered = sorted(set(uname_cat) - all_unames)
    no_uname = [k for k in uname_of if not uname_of[k]]
    # **逐件反查自证**：清单每个代表件的 (选中源, 选中原名) 反查本表，应得该行的统一名。
    # 例外只有一种且可穷举：**同一素材库文件被两个不同类别的产物同时登记为代表件**
    # （清单以 (源, 原名) 记代表件、不带类别）——此时按本组 kind 的类别归属，
    # 另一类别的那个统一名自然反查不到。例外逐条登记，不作静默放过。
    # 逐件反查：清单登记的每个 (kind, 源, 原名) 都应在表里得到该行的统一名。
    selfcheck_bad, selfcheck_exc = [], []
    for (k, sp, on), lst in sorted(reps.items()):
        unames = {u for u, _c in lst}
        got = uname_of.get((k, sp, on))
        if len(unames) == 1 and got == next(iter(unames)):
            continue
        if len(unames) > 1:
            # 同一目录同一文件被 ≥2 个产物登记（清单不带目录，`ot_asu04.png` 型同名双挂）：
            # 「期望」本身不唯一，逐条登记不静默放过。
            selfcheck_exc.append(dict(类=k, 源=sp, 原件=on,
                                      登记产物="/".join(sorted(unames)), 本表给=got or "（无）"))
            continue
        selfcheck_bad.append(dict(类=k, 源=sp, 原件=on,
                                  期望=next(iter(unames)), 实际=got or "（无）"))
    print("=" * 78)
    print("自证 · 分组与清单的一致性")
    print("=" * 78)
    print(f"  素材库美术件 {sum(len(v) for v in lib.values())} ；已归属统一名 "
          f"{len(uname_of)} ；无统一名 {len(no_uname)}")
    print(f"  清单统一名 {len(uname_cat)} ；本表未覆盖 {len(uncovered)}")
    print(f"  拆分产物权威覆盖 {len(overrides)} 条（来自 unify 拆分明细）")
    print(f"  按命名规则/归并表归位 {len(norep_recovered)} 件（无自身清单登记）")
    print(f"  未纳入美术统一（无统一名）{len(norep_groups)} 件"
          f" ；类别无法唯一消歧 {len(ambiguous)}")
    print(f"  逐件反查自证：不符 {len(selfcheck_bad)} ；"
          f"同名双挂例外 {len(selfcheck_exc)}（同一原件被两个类别同时记为代表件）")
    for g in norep_groups[:10]:
        print("   ✗ 无代表件:", g)
    if uncovered[:10]:
        print("   未覆盖统一名（前 10）:", uncovered[:10])
    for b in selfcheck_bad[:10]:
        print("   ✗ 反查不符:", b)

    # ---------------------------------------------------------------- 全量映射表
    SAFE_CLS = {"single", "same_res_same", "diff_res_same_drawing"}
    RISK_CLS = {"same_res_diff", "diff_res_diff_drawing"}
    rows = []
    for kind, recs in lib.items():
        lib_cat = KIND2CAT[kind]
        for rec in recs:
            uname = uname_of.get((kind, rec["src"], rec["name"]), "")
            cls = uname_cls.get(uname, "")
            # `类别` = **产物类别**（= 该统一名所在清单），不是素材库 kind 推导的类别：
            # `np` 立绘实体在 `pic\`、`cin*` 在 `chr\`、`ss_bg*` 在 `otv\sys|etc`——
            # 按 kind 推类别会让消费方「按类别筛」时漏掉这 177 件（一审提示）。
            cat = uname_cat.get(uname, lib_cat)
            is_rep = any(u == uname
                         for u, _c in reps.get((kind, rec["src"], rec["name"]), []))
            rows.append(
                dict(
                    源=rec["src"], 素材库kind=kind, 素材库文件=rec["name"], 类别=cat,
                    统一名=uname, 组分类=cls,
                    处置=("代表件" if is_rep else "同组非代表件"),
                    交付路径=deliv.get(uname, ""),
                    替代安全性=("等价" if cls in SAFE_CLS else ("有差异" if cls in RISK_CLS else "未知")),
                )
            )
    rows.sort(key=lambda r: (r["类别"], r["源"], r["素材库文件"]))
    write_tsv(os.path.join(handoff, "素材库到统一名.tsv"), rows,
              ["源", "素材库kind", "素材库文件", "类别", "统一名", "组分类", "处置",
               "交付路径", "替代安全性"])
    print(f"\n[out] 交接编程组\\素材库到统一名.tsv —— {len(rows)} 行")

    # ---------------------------------------------------------------- 引用映射
    refs = collections.defaultdict(set)            # relpath -> {"scene"}
    scenes_dir = os.path.join(res, "剧本")
    for src in ["ot", "otr", "ota", "otp", "otv", "np"]:
        for raw in open(os.path.join(scenes_dir, "scene_%s.jsonl" % src), encoding="utf-8"):
            o = json.loads(raw)
            for a in o["assets"]:
                rp = a.get("out_relpath")
                if rp and a["kind"] in ("chr", "pic", "sys"):
                    refs[rp].add(o["scene_id"])
    ref_rows = []
    stat = collections.Counter()
    for rp in sorted(refs):
        parts = rp.split("/")
        src, kind, fn = parts[0], parts[1], parts[-1]
        uname = uname_of.get((kind, src, fn), "")
        if uname and uname in deliv:
            cls = uname_cls.get(uname, "")
            is_rep = any(u == uname for u, _c in reps.get((kind, src, fn), []))
            safety = "代表件" if is_rep else ("等价替代" if cls in SAFE_CLS else
                                             ("有差异替代" if cls in RISK_CLS else "未知"))
            stat[safety] += 1
            ref_rows.append(dict(引用=rp, 统一名=uname, 交付路径=deliv[uname], 组分类=cls,
                                 结论=safety, 引用场景数=len(refs[rp]),
                                 样例场景=sorted(refs[rp])[0], 严重度=""))
        else:
            stat["无归属"] += 1
            ref_rows.append(dict(引用=rp, 统一名=uname, 交付路径="", 组分类="", 结论="无归属",
                                 引用场景数=len(refs[rp]), 样例场景=sorted(refs[rp])[0], 严重度="高"))
    ref_rows.sort(key=lambda r: (r["结论"] != "无归属", r["引用"]))
    write_tsv(os.path.join(handoff, "素材引用映射.tsv"), ref_rows,
              ["引用", "统一名", "交付路径", "组分类", "结论", "引用场景数", "样例场景", "严重度"])
    print(f"[out] 交接编程组\素材引用映射.tsv —— {len(ref_rows)} 行")
    print("  结论分布:", dict(stat))

    write_tsv(assert_in_checkout(os.path.join(outdir, "映射_未覆盖.tsv")),
              [dict(统一名=u, 类别=uname_cat.get(u, ""), 组分类=uname_cls.get(u, ""),
                    素材库可见=None) for u in uncovered],
              ["统一名", "类别", "组分类", "素材库可见"])

    summary = {
        "自证": {"清单统一名总数": len(uname_cat),
                 "清单统一名未被覆盖": len(uncovered),
                 "逐件反查不符": len(selfcheck_bad),
                 "同名双挂例外": len(selfcheck_exc),
                 "拆分产物权威覆盖(条)": len(overrides),
                 "按命名规则或np归并表归位(件)": len(norep_recovered),
                 "未纳入美术统一(件,非图像等)": len(norep_groups),
                 "未纳入样例": [list(g) for g in norep_groups[:20]],
                 "归位明细(前20)": norep_recovered[:20],
                 "拆分产物明细": overrides[:20],
                 "一组多产物": len(split_groups),
                 "类别无法消歧": len(ambiguous),
                 "未覆盖样例": uncovered[:10]},
        "全量映射表行数": len(rows),
        "引用映射": dict(stat),
        "引用去重件": len(ref_rows),
    }
    with open(assert_in_checkout(os.path.join(outdir, "映射汇总.json")), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return summary


if __name__ == "__main__":
    main()
