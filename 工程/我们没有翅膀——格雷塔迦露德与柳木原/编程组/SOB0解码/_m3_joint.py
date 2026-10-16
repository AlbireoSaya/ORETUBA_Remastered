# -*- coding: utf-8 -*-
"""M3 只读探针 5：某 V 的「实参位取值 → PSV 同 seq 字段值」联合分布。

用途：看某个位是不是某字段（值 → 该 seq 上 PSV 行的值集合），
并单独列出「非众数样本」（往往是判别力最强的证据）。
用法：python -X utf8 _m3_joint.py --V 0x1B69C --field time --pos 3 --pos 4 --pos 5
"""
import os, sys, collections, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
import decode_sob0 as D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--V", default="0x1B69C")
    ap.add_argument("--field", default="time")
    ap.add_argument("--pos", type=int, action="append", default=[])
    ap.add_argument("--types", default="")
    ap.add_argument("--min", type=int, default=1)
    a = ap.parse_args()
    V = int(a.V, 16)
    types = set(a.types.split(",")) if a.types else None
    ledger = D.Ledger(D.LEDGER if os.path.isfile(D.LEDGER) else "")
    scenes, agg = D.collect(a.src, ledger)
    psv_by_scene, _ = D.load_psv_timeline()
    psv = collections.defaultdict(list)
    for sid, rows in psv_by_scene.items():
        for r in rows:
            if r.get("type") == "Message":
                continue
            if types and r["type"] not in types:
                continue
            psv[(sid, int(r["seq"]))].append(r)
    # 取该 V 节点
    nodes = []
    for sid, (rows, info) in scenes.items():
        for nd in info["nodes"]:
            if nd["V"] == V:
                nodes.append((sid, nd["seq"], nd))
    print("V=0x%X 节点 %d" % (V, len(nodes)))
    pos = a.pos or [0]
    for p in pos:
        tab = collections.defaultdict(collections.Counter)
        for sid, seq, nd in nodes:
            args = nd["args"]
            if p >= len(args):
                continue
            k, v = args[p]
            if not isinstance(v, int):
                continue
            for r in psv.get((sid, seq), []):
                q = r.get(a.field, "")
                tab[v][q] += 1
        print("\n-- pos%d → %s（同 seq）--" % (p, a.field))
        for v in sorted(tab):
            if sum(tab[v].values()) < a.min:
                continue
            print("   p%d=%-8s n=%-4d %s" % (p, v, sum(tab[v].values()),
                                             tab[v].most_common(6)))


if __name__ == "__main__":
    main()
