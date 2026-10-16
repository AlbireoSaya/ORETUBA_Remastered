# -*- coding: utf-8 -*-
"""M3 只读探针 4：严口径「单节点 seq × 单事件 seq」的逐条并排对照。

`single` = PC 该 seq 恰 1 个命令节点（任意 V）∧ PSV 该 seq 恰 1 条非 Message 行。
只打印并排对，供人工判读「哪个实参位 ↔ 哪个 PSV 字段」。
用法：python -X utf8 _m3_single_pairs.py --src ot --V 0x1B69C --max 40
"""
import os, sys, collections, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
import decode_sob0 as D

NAMED = {
    "ot": ["Flash", "EffectQuake", "EffectQuakeEnd", "EffectQuakeEnd*", "EffectQuake*",
           "?quake", "?", "Window", "InOut_Act", "sp_move", "bg_move", "bg_zoom",
           "bg_blur", "cross", "EyeCatch/End", "SceneTitle", "EffectStart?", "EffectStart*"],
}

_csv = ["time", "rule", "fade", "priority", "cpri", "cx", "cy", "x", "y",
        "name", "nameid", "image", "type"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--V", default="0x1B69C")
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--allpos", action="store_true")
    a = ap.parse_args()
    V = int(a.V, 16)
    ledger = D.Ledger(D.LEDGER if os.path.isfile(D.LEDGER) else "")
    scenes, agg = D.collect(a.src, ledger)
    psv_by_scene, _ = D.load_psv_timeline()
    pc = collections.defaultdict(list)
    for sid, (rows, info) in scenes.items():
        for nd in info["nodes"]:
            pc[(sid, nd["seq"])].append(nd)
    psv = collections.defaultdict(list)
    for sid, rows in psv_by_scene.items():
        for r in rows:
            if r.get("type") != "Message":
                psv[(sid, int(r["seq"]))].append(r)
    n = 0
    print("=== V=0x%X single-seq 并排（最多 %d 条）===" % (V, a.max))
    print("%-16s %5s | %-18s %s" % ("scene", "seq", "PSV(type/fields)", "PC args"))
    for (sid, seq), nds in sorted(pc.items()):
        if len(nds) != 1 or nds[0]["V"] != V:
            continue
        ps = psv.get((sid, seq))
        if not ps or len(ps) != 1:
            continue
        r = ps[0]
        pf = " ".join("%s=%s" % (f, r.get(f)) for f in _csv if r.get(f, "") != "")
        args = " ".join("p%d=%s" % (i, v) for i, (k, v) in enumerate(nds[0]["args"]))
        print("%-16s %5d | %-18s %s" % (sid, seq, r["type"], pf))
        print("%-16s %5s |                 %s" % ("", "", args))
        n += 1
        if n >= a.max:
            break
    print("--- 共打印 %d 条 ---" % n)


if __name__ == "__main__":
    main()
