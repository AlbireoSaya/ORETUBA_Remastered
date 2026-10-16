# -*- coding: utf-8 -*-
"""只读探针 7：全部主 token 的 PSV cx 分布（严口径 + 宽口径）。

严口径 = PC 该 (scene,seq) 恰 1 个「立绘族」节点 ∧ PSV 该 (scene,seq) 恰 1 个带 cx 的事件
          ∧ 该事件 task_type ∈ 该 V 的允许角色集。
宽口径 = PC 有 token ∧ PSV 该 (scene,seq) 至少 1 个带 cx 的事件。
"""
import csv, collections, os, re

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组"
FAM = {
    "ot": {"0x1C43C": (6, 5, None), "0x1C5B0": (3, None, None), "0x18B74": (4, 3, 2),
           "0x19808": (3, 2, None), "0x186C8": (3, 2, 1), "0x10428": (6, None, 5),
           "0x14084": (3, 2, None), "0x17514": (4, 3, None)},
    "otr": {"0x1C43C": (6, 5, None), "0x1C5B0": (3, None, None), "0x18B74": (4, 3, 2),
            "0x19808": (3, 2, None), "0x186C8": (3, 2, 1), "0x10428": (6, None, 5),
            "0x14084": (3, 2, None), "0x17514": (4, 3, None)},
    "otp": {"0x1A618": (4, 3, None), "0x11078": (3, 2, None), "0x14534": (4, 3, None),
            "0x15BAC": (4, 3, 2), "0x16828": (3, 2, None), "0x156E8": (4, 3, 2),
            "0x1A970": (1, None, None)},
}
ROLE = {"0x18B74": {"CharacterMove", "CharacterAction"}, "0x15BAC": {"CharacterMove", "CharacterAction"},
        "0x186C8": {"CharacterOpen", "CharacterOpenBS"}, "0x156E8": {"CharacterOpen", "CharacterOpenBS"},
        "0x10428": {"SpriteMove", "SpriteBS", "SpriteBG"}}
TOKRE = re.compile(r"![clr]|[lr]?[<>]\d+|[clr][+-]\d+|[<>]|[clr]|[+-]\d+|[du]|[_$]")


def pa(ev):
    m = re.search(r"args=\[(.*?)\]", ev)
    if not m:
        return None
    if m.group(1) == "":
        return []
    out = []
    for p in m.group(1).split(","):
        p = p.strip()
        if p.startswith("N:"):
            out.append(("N", int(p[2:])))
        elif p.startswith("S:"):
            out.append(("S", p[2:]))
    return out


def main():
    gold = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(BASE, "PSV演出", "立绘事件流.tsv"), encoding="utf-8"), delimiter="\t"):
        if r["cx"].strip() != "":
            gold[(r["scene_id"], int(r["seq"]))].append((r["task_type"], int(r["cx"])))
    strict = collections.defaultdict(collections.Counter)
    loose = collections.defaultdict(collections.Counter)
    tot = collections.Counter()
    for src, reg in FAM.items():
        rows = list(csv.DictReader(open(os.path.join(BASE, "SOB0解码", "解出_%s.tsv" % src), encoding="utf-8"), delimiter="\t"))
        pcc = collections.Counter()
        for r in rows:
            m = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            if m and m.group(1) in reg:
                pcc[(r["scene_id"], int(r["seq"]))] += 1
        for r in rows:
            m = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            if not m or m.group(1) not in reg:
                continue
            V = m.group(1)
            a = pa(r["evidence"])
            ctrl = reg[V][2]
            if a is None or ctrl is None or ctrl >= len(a) or a[ctrl][0] != "S":
                continue
            mm = TOKRE.search(a[ctrl][1])
            tok = mm.group(0) if mm else "(无方位)"
            tot[tok] += 1
            key = (r["scene_id"], int(r["seq"]))
            g = gold.get(key)
            if not g:
                continue
            allow = ROLE.get(V)
            gs = [x for x in g if (allow is None or x[0] in allow)]
            if pcc[key] == 1 and len(g) == 1 and (allow is None or g[0][0] in allow):
                strict[tok][g[0][1]] += 1
            for _, x in g:
                loose[tok][x] += 1
    print("%-12s %6s %6s %s" % ("token", "cnt", "n_strict", "strict cx dist"))
    for tok, c in tot.most_common():
        st = strict[tok]
        print("%-12s %6d %6d %s" % (repr(tok), c, sum(st.values()), st.most_common(7)))


if __name__ == "__main__":
    main()
