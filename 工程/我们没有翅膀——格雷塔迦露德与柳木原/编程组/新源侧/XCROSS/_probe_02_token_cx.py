#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_02_token_cx.py — 只读：金标 cx 与 PC 方向 token 的交叉表（token × cx）。

问题：金标 `cx` 是不是等价于「PC 的 token 求值结果」？

口径：
  * PC 侧：`编程组\\SOB0解码\\解出_ot.tsv`（ot 源），逐行解析 `args=[...]`（token 取实参向量里的
    控制串，不用 evidence 尾部的 `ctrl=`——后者常为 None/仅解码器猜测）。
    带方向 token 的族：`0x18B74`（ctrl=args[2], slot=args[3]）、`0x186C8`（ctrl=args[1], slot=args[2]）。
    token = 控制串按空白切的最后一段，且必须整体匹配「单步位置 token」：
        c / l / r / !l / !r / !c / l<N / r>N / <N / >N / [clr]?±N
    形如 `l_` / `c_` / `$` / `_` / `a0 c` / `100>3 300<> c` 的不算单步（前者是姿态动画，后者是多步转场）。
  * 分类（class）＝解码器对 0x18B74/0x186C8 行的 action 标签（`arg2` 列）：
        CharacterMove  → 单步位移（0x18B74）
        CharacterOpen  → 入场定位（0x186C8）
        (空)           → 解码器未定名（含多步转场 / `a0 X` 等），单列一档
  * 角色（fam）：随 `seq` 递增维护「槽号 → 角色族」表；开立站带角色名时写入，名为 `0` 时清空。
  * 金标：`PSV演出\\立绘事件流.tsv`；键 `(scene_id, seq, fam)` → [(task_type, cx)]（cx 非空行）。
  * 配对：1) (scene,seq,fam) 唯一 cx；2) 同键多条 → 优先 task_type=='CharacterMove'；
          3) 否则 (scene,seq) 唯一 cx / 唯一 CharacterMove cx（标记 seq 级）。
  * token → 预测（DSL 规格，见 00_任务书 §8.6）：c/!c=640、l=336、r=944、l<N/r>N 档位、
    <N/>N 半屏档、!l=画外左(x<0)、!r=画外右(x>=1500)、[clr]?±N=相对位移（基准中央）。

用法:
  python -X utf8 _probe_02_token_cx.py [--out token_vs_cx.tsv]
"""
import argparse
import collections
import csv
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BASE = os.path.join(PROJ, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
PC_TSV = os.path.join(BASE, "SOB0解码", "解出_ot.tsv")
PSV_TSV = os.path.join(BASE, "PSV演出", "立绘事件流.tsv")

TOKEN_FAM = {"0x18B74": (2, 3), "0x186C8": (1, 2)}
OPEN_V = {"0x1C43C", "0x14084", "0x186C8"}
ARGS_RE = re.compile(r"args=\[(.*)\]")
PURE = re.compile(r"^(c|l|r|!l|!r|!c|l<\d+|r>\d+|<\d+|>\d+|[clr]?[+-]\d+)$")


def split_top(s):
    out, cur, d = [], [], 0
    for ch in s:
        if ch == "(":
            d += 1
        elif ch == ")":
            d -= 1
        if ch == "," and d == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def parse_args(evidence):
    m = ARGS_RE.search(evidence or "")
    if not m:
        return None
    if m.group(1) == "":
        return []
    a = []
    for p in split_top(m.group(1)):
        if p.startswith("N:"):
            try:
                a.append(("N", int(p[2:])))
            except ValueError:
                a.append(("?", p))
        elif p.startswith("S:"):
            a.append(("S", p[2:]))
        else:
            a.append(("?", p))
    return a


def fam_of(name):
    m = re.match(r"^([A-Za-z]+)", name or "")
    return m.group(1).lower() if m else None


def predict(tok):
    fixed = {"c": ("eq", 640), "!c": ("eq", 640), "l": ("eq", 336), "r": ("eq", 944),
             "l<2": ("eq", 236), "r>2": ("eq", 1044), "!l": ("lt", 0), "!r": ("ge", 1500)}
    if tok in fixed:
        return fixed[tok]
    if re.match(r"^[clr]?[+-]\d+$", tok):
        return ("eq", 640)
    if re.match(r"^l<\d+$", tok):
        return ("band", -64, 240)
    if re.match(r"^r>\d+$", tok):
        return ("band", 940, 1600)
    if re.match(r"^<\d+$", tok):
        return ("lt", 640)
    if re.match(r"^>\d+$", tok):
        return ("gt", 640)
    return ("unknown",)


def hit(pred, cx):
    k = pred[0]
    if k == "eq":
        return cx == pred[1]
    if k == "band":
        return pred[1] <= cx <= pred[2]
    if k == "lt":
        return cx < pred[1]
    if k == "gt":
        return cx > pred[1]
    if k == "ge":
        return cx >= pred[1]
    return None


def load_gold():
    g = collections.defaultdict(list)       # (scene,seq,fam) -> [(task_type,cx)]
    gs = collections.defaultdict(list)      # (scene,seq) -> [(fam,task_type,cx)]
    n = 0
    with io.open(PSV_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["cx"].strip() == "":
                continue
            fam, cx = r["fam"].strip(), int(r["cx"])
            g[(r["scene_id"], int(r["seq"]), fam)].append((r["task_type"], cx))
            gs[(r["scene_id"], int(r["seq"]))].append((fam, r["task_type"], cx))
            n += 1
    return g, gs, n


def pick_cx(fam, scene, seq, gold, gold_seq, want_move=True):
    key = (scene, seq, fam)
    if fam and key in gold:
        lst = gold[key]
        if want_move:
            mv = {cx for tt, cx in lst if tt == "CharacterMove"}
            if len(mv) == 1:
                return next(iter(mv)), "fam+Move"
        if len({cx for _tt, cx in lst}) == 1:
            return lst[0][1], "fam"
    g = gold_seq.get((scene, seq))
    if g:
        if want_move:
            mv = {cx for _f, tt, cx in g if tt == "CharacterMove"}
            if len(mv) == 1:
                return next(iter(mv)), "seq+Move"
        if len({cx for _f, _tt, cx in g}) == 1:
            return g[0][2], "seq"
    return None, None


CLSNAME = {"CharacterMove": "单步位移(0x18B74)", "CharacterOpen": "入场定位(0x186C8)",
           "": "未定名(多步/a0/其他)"}


def hit_of(p, st):
    return sum(st["hist"][c] for c in st["hist"] if hit(p, c) is True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "token_vs_cx.tsv"))
    a = ap.parse_args()
    gold, gold_seq, ngold = load_gold()

    pairs = []
    stat = collections.defaultdict(lambda: dict(n=0, hist=collections.Counter()))
    cls_tot = collections.Counter()
    cur, slot2fam = None, {}
    for r in csv.DictReader(io.open(PC_TSV, encoding="utf-8"), delimiter="\t"):
        scene = r["scene_id"]
        if not scene.startswith("ot_"):
            continue
        if scene != cur:
            cur, slot2fam = scene, {}
        seq = int(r["seq"])
        ev = r["evidence"] or ""
        m = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
        V = m.group(1) if m else None
        if V in OPEN_V:
            ar = parse_args(ev)
            si, ni = {"0x1C43C": (5, 4), "0x14084": (2, 1), "0x186C8": (2, None)}[V]
            if ar and si < len(ar):
                sv = ar[si][1]
                if ni is not None and ni < len(ar) and ar[ni][0] == "S":
                    nm = ar[ni][1]
                    slot2fam[sv] = None if nm == "0" else fam_of(nm)
                elif sv not in slot2fam:
                    slot2fam[sv] = None
        if V not in TOKEN_FAM:
            continue
        ar = parse_args(ev)
        if ar is None:
            continue
        ci, si = TOKEN_FAM[V]
        if ci >= len(ar) or si >= len(ar) or ar[ci][0] != "S":
            continue
        parts = ar[ci][1].split()
        tok = parts[-1] if parts else ar[ci][1]
        if not PURE.match(tok):
            continue
        cls = r["arg2"] or ""
        slot = ar[si][1]
        fam = slot2fam.get(slot)
        cls_tot[cls] += 1
        cx, level = pick_cx(fam, scene, seq, gold, gold_seq, want_move=True)
        if cx is None:
            continue
        pairs.append((scene, seq, fam or "?", cls, tok, cx, level))
        st = stat[(cls, tok)]
        st["n"] += 1
        st["hist"][cx] += 1

    cxs = sorted(set(p[5] for p in pairs))
    classes = [c for c in ["CharacterMove", "CharacterOpen", ""]
               if any(k[0] == c for k in stat)]
    cls_rank = {"CharacterMove": 0, "CharacterOpen": 1, "": 2}

    with io.open(a.out, "w", encoding="utf-8") as f:
        f.write("# 金标 cx × PC 方向 token 交叉表（ot 源）\n")
        f.write("# 金标 cx 总行数=%d；PC 单步位置 token 事件（按 class 计）=%s\n"
                % (ngold, dict(cls_tot)))
        f.write("# 配对键 (scene_id,seq,fam)；配对级别见 token_vs_cx_pairs.tsv\n")
        for cls in classes:
            toks = sorted([k[1] for k in stat if k[0] == cls],
                          key=lambda t: -stat[(cls, t)]["n"])
            f.write("\n# === %s ===\n" % CLSNAME.get(cls, cls))
            f.write("\t".join(["token", "n", "pred"] + ["cx=%d" % c for c in cxs]
                              + ["hit", "rate", "cx_hist"]) + "\n")
            for t in toks:
                st = stat[(cls, t)]
                p = predict(t)
                h = hit_of(p, st)
                row = [t, str(st["n"]), "/".join(str(x) for x in p)]
                row += [str(st["hist"][c]) if st["hist"][c] else "" for c in cxs]
                row += ["%d/%d" % (h, st["n"]), ("%.4f" % (h / st["n"])) if st["n"] else "",
                        ",".join("%d:%d" % (c, st["hist"][c]) for c in sorted(st["hist"]))]
                f.write("\t".join(row) + "\n")
            tot = sum(stat[(cls, t)]["n"] for t in toks)
            hp = sum(hit_of(predict(t), stat[(cls, t)]) for t in toks)
            f.write("# 小计 %s: 配对事件=%d 命中=%d 命中率=%.4f\n"
                    % (CLSNAME.get(cls, cls), tot, hp, hp / tot if tot else 0))

    print("金标 cx 行数=%d；PC 单步位置 token 事件=%s；可配对=%d"
          % (ngold, dict(cls_tot), len(pairs)))
    grand_n = grand_h = 0
    for cls in sorted(classes, key=lambda c: cls_rank[c]):
        toks = sorted([k[1] for k in stat if k[0] == cls],
                      key=lambda t: -stat[(cls, t)]["n"])
        tot = sum(stat[(cls, t)]["n"] for t in toks)
        hp = sum(hit_of(predict(t), stat[(cls, t)]) for t in toks)
        grand_n += tot
        grand_h += hp
        print("\n=== %s ===  配对=%d 命中=%d 命中率=%.4f"
              % (CLSNAME.get(cls, cls), tot, hp, hp / tot if tot else 0))
        for t in toks:
            st = stat[(cls, t)]
            h = hit_of(predict(t), st)
            print("  %-6s n=%-4d hit=%-4d rate=%.3f  hist=%s"
                  % (t, st["n"], h, h / st["n"] if st["n"] else 0,
                     ",".join("%d:%d" % (c, st["hist"][c]) for c in sorted(st["hist"])[:8])))
    print("\n总计 配对=%d 命中=%d 命中率=%.4f" % (grand_n, grand_h, grand_h / grand_n))

    detail = os.path.join(HERE, "token_vs_cx_pairs.tsv")
    with io.open(detail, "w", encoding="utf-8") as f:
        f.write("scene_id\tseq\tfam\tclass\ttoken\tpsv_cx\tpair_level\n")
        for row in pairs:
            f.write("\t".join(str(x) for x in row) + "\n")
    print("交叉表 → %s\n明细 → %s" % (a.out, detail))


if __name__ == "__main__":
    main()
