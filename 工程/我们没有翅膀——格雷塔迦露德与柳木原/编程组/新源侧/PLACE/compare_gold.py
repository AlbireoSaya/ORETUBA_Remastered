#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compare_gold.py —— 与 PSV 金标对拍 `x1920`（ISSUE-20261008-09 / PLACE 模块 · D）

金标: `工程\\我们没有翅膀——格雷塔迦露德与柳木原\\编程组\\PSV演出\\立绘事件流.tsv`
      有现成列 `x1920 = cx × 1.5`（1280 空间 → 1920 空间），**直接使用**。
对拍: `立绘落位_ot.tsv`（本模块 C 产物）里 `src=ot` 的行。

两种口径:
  * **严口径（判别口径）**: 该 (scene_id, seq) 上我方**恰 1 条**有像素 x1920 的行 ∧ 金标**恰 1 条**带 cx 的事件
                           ⇒ 单点比较 x1920 是否相等。
  * **宽口径（召回口径）**: 金标该 (scene_id, seq) **有 ≥1 条**带 cx 的事件 ⇒ 命中 = 任一 cx×1.5 与 x1920 相等。
    （宽口径天然被同屏其它角色污染，不是数据缺陷；判别口径是严口径。）
  * **画外档**（`!l`/`!r`，本批不给像素）: 只用不等式判据
       `!l` ⇒ 金标任一 x1920 < 0 ；`!r` ⇒ 金标任一 x1920 ≥ 2250（= cx≥1500 × 1.5）。

CLI:
  python -X utf8 compare_gold.py             # 打印对拍报告（只读）
  python -X utf8 compare_gold.py --emit      # 另写 金标对拍_ot.tsv 与 金标对拍_反例.tsv
"""
import collections
import csv
import os
import sys

# 只读纪律：import PLACE 的模块不得在 PLACE 目录产生 __pycache__
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
# 工作区根：复用 place_dsl 的多候选解析（`--ws-root` / GRETA_WS_ROOT / 向上搜索 Galgame.md），
# 不再按「距脚本 3 层」硬编码——入库到 `新源侧\PLACE\`（5 层）后原位可跑。
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import place_dsl as P          # noqa: E402
WS = P.WS
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")


def _resolve_input(rel_file, rel_dir):
    """按候选根顺序找输入文件；返回 (**文件**绝对路径, 是否命中)。未命中退回最近根的 rel_dir。
    ★ 2026-10-09 修复（审核 RV-C E1）：旧版误把 `os.path.dirname(p)`（目录）返回给 `GOLD`，
    `open(GOLD)` 恒崩 PermissionError ⇒ v1 基线 0.9616 不可复跑。现返回文件路径。
    """
    for r in P.WS_ROOTS:
        p = os.path.join(r, rel_file)
        if os.path.isfile(p):
            return p, True
    return os.path.join(P.WS_ROOTS[0], rel_dir, os.path.basename(rel_file)), False


GOLD, _GOLD_OK = _resolve_input(os.path.join(PROJ_REL, "PSV演出", "立绘事件流.tsv"),
                                os.path.join(PROJ_REL, "PSV演出"))
MINE = os.path.join(HERE, "立绘落位_ot.tsv")

OFF_RIGHT_MIN = 1500 * 1.5      # 2250

# 与 SOB0ARGS 同口径的「角色约束」：某 V 的 PC 节点只与允许的 PSV task_type 比
ROLE_ALLOW = {
    "0x18B74": {"CharacterMove", "CharacterAction"},
    "0x186C8": {"CharacterOpen", "CharacterOpenBS"},
    "0x10428": {"SpriteMove", "SpriteBS", "SpriteBG"},
}
TOKEN_VS = {"ot": ("0x18B74", "0x186C8", "0x10428")}


def v_of(ev):
    i = ev.find("V=")
    if i < 0:
        return ""
    j = i + 2
    while j < len(ev) and ev[j] not in " \t":
        j += 1
    return ev[i + 2:j]


def load_gold():
    """{(scene_id, seq): [ (cx, x1920, task_type, ps_name) ... ]}  （仅 src=ot，cx 非空）"""
    g = collections.defaultdict(list)
    with open(GOLD, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["src"] != "ot":
                continue
            if r["cx"] == "":
                continue
            try:
                cx = int(r["cx"])
            except ValueError:
                continue
            x1920 = int(r["x1920"]) if r["x1920"] != "" else int(round(cx * 1.5))
            g[(r["scene_id"], int(r["seq"]))].append((cx, x1920, r["task_type"], r["ps_name"], r["op"]))
    return g


_TOKRE = __import__("re").compile(r"![clr]|[lr]?[<>]\d+|[clr][+-]\d+|[<>]|[clr]|[+-]\d+|[du]|[_$]")


def load_mine(mode="file"):
    """mode='file'（默认）/ 'state' 时读**磁盘上的 C 产物**（`立绘落位_ot.tsv`，即交付口径）；
    'static' / 'auto' 则用 A 模块现算（不写盘），便于口径对照。"""
    if mode in ("file", "state"):
        if not os.path.exists(MINE):
            raise SystemExit("缺 %s，请先跑 build_place.py --emit" % MINE)
        with open(MINE, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter="\t"))
    import place_dsl as P
    import layer_by_slot as L
    build = P.build_rows("ot", mode=mode)
    _, zmap, _ = L.compute_z("ot", build=build)
    out = []
    for r, f in build:
        ctrl = f.get("ctrl") or ""
        m = _TOKRE.search(ctrl)
        out.append({
            "scene_id": r["scene_id"], "src": "ot", "seq": str(r["seq"]),
            "ord": str(f["ord"]), "fam": P.fam_short(f["fdef"]["role"]),
            "name": f.get("name") or "",
            "slot": "" if f.get("slot") is None else str(f["slot"]),
            "dir_token": m.group(0) if m else "",
            "x1920": "" if f.get("x") is None else str(f["x"]),
            "y1920": "" if f.get("y") is None else str(f["y"]),
            "z_rank": zmap.get((r["scene_id"], r["file_idx"]), ""),
            "conf": f.get("conf") or "", "evidence": r["evidence"],
        })
    return out


def compare(mode="file"):
    """口径（与 SOB0ARGS §五 逐条一致，另加本模块的状态量）:
       严: (scene,seq) 上 V∈TOKEN_VS 的 PC 节点恰 1 个 ∧ 金标恰 1 条带 cx 的事件
           ∧ 该事件 task_type ∈ ROLE_ALLOW[V] ∧ 我方该行 x1920 已解
       宽: 同上，但金标允许多条（命中 = 任一 task_type 合规事件的 x1920 相等）
       画外: 同上但用不等式判据（!l → x1920<0 ; !r → x1920>=2250）
    """
    gold = load_gold()
    mine = load_mine(mode)
    res_rows = []
    stat = collections.Counter()
    per_tok = collections.defaultdict(lambda: [0, 0])

    my_nodes = collections.defaultdict(list)      # (scene,seq) -> [PC 节点(V∈TOKEN_VS)]
    for r in mine:
        v = v_of(r["evidence"])
        if v in TOKEN_VS["ot"]:
            my_nodes[(r["scene_id"], int(r["seq"]))].append(r)

    for r in mine:
        v = v_of(r["evidence"])
        if v not in TOKEN_VS["ot"]:
            continue
        scene, seq = r["scene_id"], int(r["seq"])
        cxlist_all = gold.get((scene, seq), [])
        allow = ROLE_ALLOW[v]
        cxlist = [c for c in cxlist_all if c[2] in allow]
        tok = r["dir_token"]
        node_ok = (len(my_nodes[(scene, seq)]) == 1)
        if not cxlist:
            continue
        if r["x1920"] != "":
            mine_x = int(r["x1920"])
            if node_ok and len(cxlist) == 1:
                hit = (cxlist[0][1] == mine_x)
                stat["strict"] += 1
                per_tok[tok][1] += 1
                if hit:
                    stat["strict_hit"] += 1
                    per_tok[tok][0] += 1
                else:
                    stat["strict_miss"] += 1
                res_rows.append((scene, seq, tok, str(mine_x), v, "严",
                                 "HIT" if hit else "MISS", str(cxlist[0][1]),
                                 "金标 %s/%s cx=%d" % (cxlist[0][0], cxlist[0][2], cxlist[0][1])))
            hit = any(c[1] == mine_x for c in cxlist)
            stat["loose"] += 1
            if hit:
                stat["loose_hit"] += 1
            else:
                stat["loose_miss"] += 1
            res_rows.append((scene, seq, tok, str(mine_x), v, "宽",
                             "HIT" if hit else "MISS",
                             ",".join(str(c[1]) for c in cxlist),
                             "金标 %s" % ",".join("%s/%s cx=%d" % (c[0], c[2], c[1]) for c in cxlist)))
        elif tok in ("!l", "!r"):
            if tok == "!l":
                hit = any(c[1] < 0 for c in cxlist)
                need = "任一 x1920 < 0"
            else:
                hit = any(c[1] >= OFF_RIGHT_MIN for c in cxlist)
                need = "任一 x1920 >= 2250"
            stat["offscreen"] += 1
            per_tok[tok][1] += 1
            if hit:
                stat["offscreen_hit"] += 1
                per_tok[tok][0] += 1
            else:
                stat["offscreen_miss"] += 1
            res_rows.append((scene, seq, tok, "(画外,无像素)", v, "画外",
                             "HIT" if hit else "MISS",
                             ",".join(str(c[1]) for c in cxlist), need))
    # 严口径分母中还包含「x 未解」的节点（覆盖缺口），单列统计
    unknown = 0
    for key, nodes in my_nodes.items():
        if len(nodes) != 1:
            continue
        cxlist = [c for c in gold.get(key, []) if c[2] in ROLE_ALLOW[v_of(nodes[0]["evidence"])]]
        if len(cxlist) == 1 and nodes[0]["x1920"] == "":
            unknown += 1
    stat["strict_unknown"] = unknown
    return res_rows, stat, per_tok


def print_report(res_rows, stat, per_tok):
    print("== D · 金标对拍（金标: %s）==" % os.path.basename(GOLD))
    print("金标 ot 带 cx 的 (scene_id,seq) 数、我方 x1920 非空行数见下")
    print()
    print("-- 严口径（PC 单节点 ∧ 金标单事件 ∧ task_type 合规）--")
    n = stat["strict"]
    h = stat["strict_hit"]
    print("  样本量 = %d   命中 = %d   未命中 = %d   命中率 = %s"
          % (n, h, stat["strict_miss"], ("%.4f" % (h / n)) if n else "N/A"))
    print("  （另有严口径内**我方 x 未解**而未判的行数 = %d）" % stat["strict_unknown"])
    print("-- 宽口径（金标该 seq 有 ≥1 条 task_type 合规的 cx）--")
    n = stat["loose"]
    h = stat["loose_hit"]
    print("  样本量 = %d   命中 = %d   未命中 = %d   命中率 = %s"
          % (n, h, stat["loose_miss"], ("%.4f" % (h / n)) if n else "N/A"))
    print("-- 画外档（不等式判据）--")
    n = stat["offscreen"]
    h = stat["offscreen_hit"]
    print("  样本量 = %d   命中 = %d   未命中 = %d   命中率 = %s"
          % (n, h, stat["offscreen_miss"], ("%.4f" % (h / n)) if n else "N/A"))
    print()
    print("-- 分 token 命中率（严口径 + 画外）--")
    print("  %-8s %8s %8s %8s" % ("token", "命中", "总数", "命中率"))
    for tok in sorted(per_tok, key=lambda t: -per_tok[t][1]):
        a, b = per_tok[tok]
        print("  %-8s %8d %8d %8s" % (tok or "(无)", a, b, ("%.4f" % (a / b)) if b else "-"))
    print()
    print("-- 反例清单（未命中；严口径排前，上限 40 条）--")
    miss = [r for r in res_rows if r[6] == "MISS"]
    miss.sort(key=lambda r: (0 if r[5] == "严" else (1 if r[5] == "画外" else 2), r[0], r[1]))
    seen = set()
    k = 0
    for r in miss:
        key = (r[0], r[1], r[5])
        if key in seen:
            continue
        seen.add(key)
        print("   %-2s %-14s :%-6d %-6s %-8s 我=%s  金标=%s  %s"
              % (r[5], r[0], r[1], r[2] or "(无)", r[4], r[3], r[7], r[8]))
        k += 1
        if k >= 40:
            break
    print()
    print("  反例总数（去重后，仅列出前 40 条）= %d（严 %d / 画外 %d / 宽 %d）"
          % (len(seen),
             sum(1 for r in miss if r[5] == "严"),
             sum(1 for r in miss if r[5] == "画外"),
             sum(1 for r in miss if r[5] == "宽")))
    return stat


def emit(res_rows):
    p1 = os.path.join(HERE, "金标对拍_ot.tsv")
    with open(p1, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(["scene_id", "seq", "dir_token", "我方x1920", "V", "口径", "结果",
                           "金标x1920", "备注"]) + "\n")
        for r in res_rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    p2 = os.path.join(HERE, "金标对拍_反例.tsv")
    miss = [r for r in res_rows if r[6] == "MISS"]
    miss.sort(key=lambda r: (0 if r[5] == "严" else (1 if r[5] == "画外" else 2), r[0], r[1]))
    with open(p2, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(["口径", "scene_id", "seq", "dir_token", "V", "我方x1920",
                           "金标x1920", "金标cx/判据"]) + "\n")
        for r in miss:
            f.write("\t".join([r[5], r[0], str(r[1]), r[2] or "(无)", r[4], r[3], r[7], r[8]]) + "\n")
    print("WROTE %s (%d 行)" % (os.path.basename(p1), len(res_rows)))
    print("WROTE %s (%d 行)" % (os.path.basename(p2), len(miss)))


def counterfactual():
    """参考（**不写入产物**）：若把「无控制串的 CharacterOpen」默认 x 取 960
    （引擎 `cb 0x14450` 写 VAR#778[idx]=400 的候选语义，EXE_POS §9.2 标未证），
    在同口径（PC 单节点 ∧ 金标单事件 ∧ task_type ∈ {CharacterOpen, CharacterOpenBS}）下金标命中率会变成多少？
    —— 只作裁决参考，本批不采用。"""
    gold = load_gold()
    mine = load_mine("state")
    cand = collections.defaultdict(list)
    for r in mine:
        if r["fam"] == "open" and r["slot"] != "" and r["x1920"] == "":
            cand[(r["scene_id"], int(r["seq"]))].append(r)
    st = collections.Counter()
    for key, rows in cand.items():
        if len(rows) != 1:
            continue
        ours = rows[0]["name"]
        cx = [c for c in gold.get(key, []) if c[2] in ("CharacterOpen", "CharacterOpenBS")]
        # 再加「同一角色」约束：我方名 与 金标 ps_name 互为前缀（我方常记基名，金标带变体后缀）
        cx = [c for c in cx if ours and (c[3].startswith(ours) or ours.startswith(c[3]))]
        if len(cx) != 1:
            continue
        st["n"] += 1
        if cx[0][1] == 960:
            st["hit"] += 1
    return st


def _guard_inputs():
    """输入缺失 ⇒ 打印 `INPUT_MISSING` + 明确路径，返回退出码 3（≠ 对拍失败 0/1）。"""
    miss = list(P.missing_inputs())          # SOB0 解出_*.tsv（counterfactual 用 --mode state 时要）
    if not os.path.isfile(GOLD):
        miss.append(GOLD)
    if not os.path.isfile(MINE):
        miss.append(MINE)
    if not miss:
        return None
    print("== INPUT_MISSING（compare_gold 无法执行：输入缺失，非「对拍失败」）==")
    for p in miss:
        print("   缺输入: %s" % p)
    print("CHECK_ERROR=INPUT_MISSING  files=%d" % len(miss))
    return 3


def main(argv):
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    rc = _guard_inputs()
    if rc is not None:
        return rc
    mode = "file"
    if "--mode" in argv:
        mode = argv[argv.index("--mode") + 1]
    res_rows, stat, per_tok = compare(mode)
    print("== 口径: x1920 取值模式 = %s ==" % mode)
    print_report(res_rows, stat, per_tok)
    cf = counterfactual()
    print()
    print("-- 参考（**不写入产物**，仅供裁决）: 若把「无控制串 CharacterOpen」默认 x 取 960 --")
    print("   同口径样本 %d，命中 960 的 %d，命中率 = %.4f"
          % (cf["n"], cf["hit"], (cf["hit"] / cf["n"]) if cf["n"] else 0))
    if "--emit" in argv:
        emit(res_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
