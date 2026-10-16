#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_psv_join.py —— 只读探针：把「PC 侧实参位」与 PSV 金标 时间线.tsv 对拍。

口径（**分开报，禁止混报**）
  * `exact`：该 seq 上**恰 1 条**指定类型的 PSV 行，且 `round(ms×0.06)` **等于**其 `time`。
  * `seq`  ：`round(ms×0.06)` ∈ 该 seq 上该类型行的 `time` 值集合。
  * `scene`：`round(ms×0.06)` ∈ 该场该类型行的 `time` 值集合（抗 seq 错位）。
  * `nz`   ：把「位值 == 默认值」的节点排除后重算（默认值会把命中率稀释成假低）。
  * `base` ：该类型全库 `time` 值分布的 top1 占比（**随机基线**，用来看「命中是不是碰巧」）。
换算：`PSV :Time(帧) = round(PC 毫秒 × 0.06)`（60fps；Fade 已证，本批沿用同一常数）。

另：`--profile` 给出各 Tasktype 的列填充率（回答「金标到底有没有这一列」）。

复跑（只读）：
  python -X utf8 _probe_psv_join.py --profile
  python -X utf8 _probe_psv_join.py --spec "0x1B69C,5,EffectQuake+SpriteQuake" \
      --spec "0x1B040,3,InOut_Act" ...
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from functools import lru_cache

G = r"E:/ZCode Workspace/Galgame"
PG = G + "/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组"
TSVDIR = PG + "/SOB0解码"
PSV = PG + "/PSV演出/时间线.tsv"


def split_args(ev):
    k = ev.find("args=[")
    if k < 0:
        return None
    i = k + 6
    out, cur, depth = [], [], 1
    while i < len(ev):
        ch = ev[i]
        if ch == "]" and depth == 1:
            break
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 1:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    if len(out) == 1 and out[0] == "":
        return []
    return out


@lru_cache(maxsize=None)
def load_psv():
    """-> {(scene,seq): [(type,time,line,name,fade,rule)], per_type_time_counter}"""
    by = defaultdict(list)
    tcnt = defaultdict(Counter)
    with open(PSV, "r", encoding="utf-8", errors="replace") as f:
        head = f.readline().rstrip("\n").split("\t")
        ci = {c: n for n, c in enumerate(head)}
        for no, ln in enumerate(f, start=2):
            p = ln.rstrip("\n").split("\t")
            if len(p) < len(head):
                p += [""] * (len(head) - len(p))
            ty = p[ci["type"]]
            tv = p[ci["time"]].strip()
            try:
                ti = int(tv)
            except Exception:
                ti = None
            key = (p[ci["scene_id"]], p[ci["seq"]])
            by[key].append({"type": ty, "time": ti, "line": no,
                            "name": p[ci["name"]], "fade": p[ci["fade"]].strip(),
                            "rule": p[ci["rule"]].strip(), "task": p[ci["task"]]})
            if ti is not None:
                tcnt[ty][ti] += 1
    return by, tcnt, head


@lru_cache(maxsize=None)
def load_pc(src):
    """-> {(scene,seq): [ (V, ms_per_pos(list), argc, line) ]}"""
    p = os.path.join(TSVDIR, "解出_%s.tsv" % src)
    out = defaultdict(list)
    if not os.path.exists(p):
        return out
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        head = f.readline().rstrip("\n").split("\t")
        ci = {c: n for n, c in enumerate(head)}
        for no, ln in enumerate(f, start=2):
            q = ln.rstrip("\n").split("\t")
            if len(q) <= ci["evidence"]:
                continue
            ev = q[ci["evidence"]]
            m = re.search(r"V=(0x[0-9A-Fa-f]+)", ev)
            if not m:
                continue
            args = split_args(ev)
            if args is None:
                continue
            vals = []
            for tok in args:
                mm = re.match(r"^N:(.*)$", tok, re.S)
                vals.append(int(mm.group(1)) if mm else None)
            out[(q[ci["scene_id"]], q[ci["seq"]])].append(
                {"V": m.group(1), "vals": vals, "argc": len(args), "line": no,
                 "raw": ev})
    return out


def join(src, V, pos, types, nz_default=0, use_scene_rule=False, scale=0.06,
         gold_nz=False, frame_off=0):
    """三口径各自的分母**分别记账**（口径写死，避免混报）：
      N_all      = 该 (src,V,pos) 的非默认节点总数（不看金标）
      N_scene    = 其中「本场有该类型 ≥1 条带 time 的金标行」的节点数 —— scene 口径分母
      N_seq      = 其中「本 seq 有该类型 ≥1 条带 time 的金标行」的节点数 —— seq 口径分母
      N_exact    = 其中「本 seq **恰 1 条**该类型带 time 的金标行」的节点数 —— exact 口径分母
    """
    by, tcnt, _ = load_psv()
    sc = defaultdict(lambda: defaultdict(set))
    for (sid, sq), rows in by.items():
        for r in rows:
            if r["time"] is not None:
                sc[sid][r["type"]].add(r["time"])
    pc = load_pc(src)
    types = set(types)
    stat = Counter()
    ex_lines, seq_lines, scene_lines = [], [], []
    for key, nodes in pc.items():
        sid = key[0]
        rows = [r for r in by.get(key, []) if r["type"] in types and r["time"] is not None]
        tset_seq = set(r["time"] for r in rows)
        tset_scene = set()
        for t in types:
            tset_scene |= sc[sid].get(t, set())
        has_scene = len(tset_scene) > 0
        for nd in nodes:
            if nd["V"] != V or pos >= len(nd["vals"]):
                continue
            ms = nd["vals"][pos]
            if ms is None:
                continue
            if nz_default is not None and ms == nz_default:
                stat["_default"] += 1
                continue
            stat["_all"] += 1
            if not has_scene:
                continue
            stat["_scene"] += 1
            fr = int(round(ms * scale)) + frame_off
            if fr in tset_scene:
                stat["scene"] += 1
            else:
                scene_lines.append((nd["line"], key, ms, fr, sorted(tset_scene)[:8], nd["raw"]))
            if tset_seq:
                stat["_seq"] += 1
                if fr in tset_seq:
                    stat["seq"] += 1
                else:
                    seq_lines.append((nd["line"], key, ms, fr, sorted(tset_seq)[:8], nd["raw"]))
            if len(rows) == 1:
                if gold_nz and rows[0]["time"] == 0:
                    stat["_degen"] += 1          # 金标退化值（time=0）⇒ 不计入 exact 分母
                else:
                    stat["_exact"] += 1
                    if rows[0]["time"] == fr:
                        stat["exact"] += 1
                    else:
                        ex_lines.append((nd["line"], key, ms, fr, rows[0]["line"],
                                         rows[0]["type"], rows[0]["time"], nd["raw"]))
    # ---- 置换基线（null）：把 (key, ms) 的 ms 整体错位一格，再对同一批 key 对拍 ----
    pairs = []
    for key, nodes in pc.items():
        rows = [r for r in by.get(key, []) if r["type"] in types and r["time"] is not None]
        if not rows:
            tss = set()
            for t in types:
                tss |= sc[key[0]].get(t, set())
            if not tss:
                continue
        for nd in nodes:
            if nd["V"] != V or pos >= len(nd["vals"]):
                continue
            ms = nd["vals"][pos]
            if ms is None or (nz_default is not None and ms == nz_default):
                continue
            pairs.append((key, ms))
    nul = Counter()
    keys = [k for k, _ in pairs]
    mss = [v for _, v in pairs]
    for j in range(len(pairs)):
        ms = mss[(j + 1) % len(mss)] if len(mss) > 1 else None
        if ms is None:
            continue
        k2 = keys[j]                     # key 不动，ms 错位 ⇒ 真置换
        rows = [r for r in by.get(k2, []) if r["type"] in types and r["time"] is not None]
        tss = set(r["time"] for r in rows)
        tsc = set()
        for t in types:
            tsc |= sc[k2[0]].get(t, set())
        fr = int(round(ms * scale)) + frame_off
        nul["_all"] += 1
        if tss:
            nul["_seq"] += 1
            nul["seq"] += 1 if fr in tss else 0
        if tsc:
            nul["_scene"] += 1
            nul["scene"] += 1 if fr in tsc else 0
        if len(rows) == 1:
            nul["_exact"] += 1
            nul["exact"] += 1 if rows[0]["time"] == fr else 0

    n = max(stat["_all"], 1)
    return {"src": src, "V": V, "pos": pos, "types": "+".join(sorted(types)),
            "null": {"n": nul["_all"], "exact": nul["exact"], "n_exact": nul["_exact"],
                     "seq": nul["seq"], "n_seq": nul["_seq"],
                     "scene": nul["scene"], "n_scene": nul["_scene"]},
            "n": stat["_all"], "default": stat["_default"],
            "n_scene": stat["_scene"], "n_seq": stat["_seq"], "n_exact": stat["_exact"],
            "exact": stat["exact"], "seq": stat["seq"], "scene": stat["scene"],
            "ex_lines": ex_lines, "seq_lines": seq_lines, "scene_lines": scene_lines,
            "degen": stat["_degen"]}


HDR = ("%-9s %-4s %-22s %-6s %-5s %-9s %-9s %-9s" %
       ("V", "pos", "types", "nz_n", "默认", "exact", "seq", "scene"))


def rowline(r):
    f = lambda a, b: "%d/%d=%.3f" % (a, b, a / b) if b else "-"
    nu = r.get("null", {})
    return ("%-9s %-4d %-22s %-6d %-5d %-9s %-9s %-9s | 置换基线 %s %s %s"
            % (r["V"], r["pos"], r["types"], r["n"], r["default"],
               f(r["exact"], r["n_exact"]), f(r["seq"], r["n_seq"]),
               f(r["scene"], r["n_scene"]),
               f(nu.get("exact", 0), nu.get("n_exact", 0)),
               f(nu.get("seq", 0), nu.get("n_seq", 0)),
               f(nu.get("scene", 0), nu.get("n_scene", 0))))


@lru_cache(maxsize=None)
def profile():
    by, tcnt, head = load_psv()
    ncol = Counter()
    fill = defaultdict(Counter)
    for rows in by.values():
        for r in rows:
            ncol[r["type"]] += 1
    # 重新逐行读，统计列填充
    with open(PSV, "r", encoding="utf-8", errors="replace") as f:
        head = f.readline().rstrip("\n").split("\t")
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) < len(head):
                p += [""] * (len(head) - len(p))
            ty = p[head.index("type")]
            for i, c in enumerate(head):
                if p[i].strip() != "":
                    fill[ty][c] += 1
    print("== PSV 时间线.tsv 各 Tasktype 列填充率（只列含 time 的列是否非空）==")
    print("%-22s %7s  %s" % ("type", "rows", "非空列（计数）"))
    for ty, n in sorted(ncol.items()):
        cols = ", ".join("%s:%d" % (c, v) for c, v in fill[ty].items() if c not in
                         ("scene_id", "script", "task", "type"))
        print("%-22s %7d  %s" % (ty, n, cols))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", action="append", default=[],
                    help="V,pos,Type1+Type2[,nz=默认值]")
    ap.add_argument("--sweep", action="append", default=[],
                    help="V,Type1+Type2,nz[,maxpos]  逐位扫（找出该 type 下最像 ms 的位）")
    ap.add_argument("--src", default="ot,otr")
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--show", type=int, default=3)
    ap.add_argument("--fail", action="store_true", help="打印全部反例")
    ap.add_argument("--scale", type=float, default=0.06, help="帧换算系数（默认 0.06 = 60fps）")
    ap.add_argument("--frame-off", type=int, default=0,
                    help="值偏移变异：帧值统一 +N（用于证明「对位/对值都敏感」）")
    ap.add_argument("--gold-nz", action="store_true",
                    help="非退化口径：金标 time=0 的行不计入 exact 分母（对齐上游 final_ms.tsv 口径）")
    a = ap.parse_args()
    if a.profile:
        profile()
        return 0
    print("== PSV 对拍（round(ms×0.06) vs PSV :Time 帧）==")
    print(HDR)
    for sw in a.sweep:
        parts = sw.split(",")
        V, types = parts[0], parts[1]
        nz = int(parts[2]) if len(parts) > 2 and parts[2] != "" else 0
        mx = int(parts[3]) if len(parts) > 3 else 19
        print("-- sweep %s vs %s (nz=%d)" % (V, types, nz))
        for pos in range(mx + 1):
            for src in a.src.split(","):
                r = join(src, V, pos, types.split("+"), nz, scale=a.scale,
                         gold_nz=a.gold_nz, frame_off=a.frame_off)
                if r["n"] < 3:
                    continue
                print("  [%s] %s" % (src, rowline(r)))
    for spec in a.spec:
        parts = spec.split(",")
        V, pos, types = parts[0], int(parts[1]), parts[2].split("+")
        nz = 0
        for p in parts[3:]:
            if p.startswith("nz="):
                nz = int(p[3:])
        for src in a.src.split(","):
            r = join(src, V, pos, types, nz, scale=a.scale,
                     gold_nz=a.gold_nz, frame_off=a.frame_off)
            if r["n"] == 0:
                print("%-9s %-4d %-22s  [%s] 无样本" % (V, pos, r["types"], src))
                continue
            print("[%s] %s" % (src, rowline(r)))
            for row in r["ex_lines"][:(99 if a.fail else a.show)]:
                print("     exact反例 解出_%s.tsv:%d (scene=%s seq=%s) ms=%s frame=%s"
                      " vs 时间线.tsv:%d %s=%s" %
                      (src, row[0], row[1][0], row[1][1], row[2], row[3],
                       row[4], row[5], row[6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
