# -*- coding: utf-8 -*-
"""M3 只读探针 3：PC 效果/转场命令「实参位 → PSV 金标字段」对拍。

口径（全部分开报，禁止混报）：
  * `single`  = PC 该 seq 恰 1 节点 ∧ PSV 该 seq 恰 1 条非 Message 行（严）
  * `seqhit`  = `f(arg[pos])` ∈ {本 seq 上「期望 type」行的字段值}（同 seq 召回）
  * `scenehit`= `f(arg[pos])` ∈ {本场「期望 type」行的字段值}（同场召回，抗 seq 错位）
  * `base`    = 基线：随机一行该字段值命中率（用全库该 type 值分布估计）
变换 `f`：`id`（直读）/ `ms`（×0.06 → 帧）/ `hex`（RGB 直读）。
期望 type 由 `single` 口径的众数自动决定（不预设），另可手工覆盖。
只读；只打印。
用法：python -X utf8 _m3_arg_vs_psv.py [--src ot] [--json out.json]
"""
import os, sys, io, csv, json, collections, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
import decode_sob0 as D

TARGET = {
    "ot": {
        0x1B888: "Flash", 0x1B69C: "EffectQuake", 0x7480: "Window",
        0x1B040: "InOut_Act", 0x186C8: "sp_move", 0x10150: "bg_move",
        0xFDF4: "bg_zoom", 0x13300: "bg_blur", 0x2A150: "cross",
        0x19D58: "EffectQuakeEnd", 0x1C330: "EffectQuakeEnd*",
        0x1BD8C: "EffectQuake*", 0x1AD18: "EyeCatch/End",
        0x1C8D0: "SceneTitle", 0x11784: "EffectStart?", 0x11B0C: "EffectStart*",
        0xEFF0: "?quake", 0x1ABF0: "?",
    },
    "otp": {0x15BAC: "chr_anime(ref)"},
    "otr": {},
}
# 期望 PSV type（V → 类型集合）；空 = 不预设，由 single 众数自动填
EXPECT = {
    0x1B888: {"Flash"}, 0x1B69C: {"EffectQuake", "SpriteQuake"},
    0x19D58: {"EffectQuakeEnd", "EffectEnd"}, 0x1C330: {"EffectQuakeEnd"},
    0x1BD8C: {"EffectQuake", "SpriteQuake"}, 0xEFF0: {"EffectQuake"},
    0x7480: {"Window"}, 0x1B040: {"InOut_Act", "InOut"},
    0x186C8: {"SpriteMove", "SpriteBS", "Sprite"},
    0x10150: {"SpriteMove", "SpriteBS"},
    0x1AD18: {"EyeCatch", "EyeCatchEnd"}, 0x1C8D0: {"SetSceneName"},
    0x11784: {"EffectStart"}, 0x11B0C: {"EffectStart"},
}
FIELDS = ["time", "rule", "fade", "priority", "cpri", "cx", "cy", "x", "y"]


def num(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    src = a.src
    ledger = D.Ledger(D.LEDGER if os.path.isfile(D.LEDGER) else "")
    scenes, agg = D.collect(src, ledger)
    print("源 %s：场 %d 文件 %d 节点(kept) %d" % (src, len(scenes), agg["files"], agg["nodes_kept"]))
    psv_by_scene, _ = D.load_psv_timeline()

    # (sid,seq) -> [node];  (sid,seq) -> [psv non-message row]
    pc = collections.defaultdict(list)
    for sid, (rows, info) in scenes.items():
        for nd in info["nodes"]:
            pc[(sid, nd["seq"])].append(nd)
    psv = collections.defaultdict(list)
    for sid, rows in psv_by_scene.items():
        for r in rows:
            if r.get("type") != "Message":
                psv[(sid, int(r["seq"]))].append(r)

    out = {}
    for V, name in sorted(TARGET[src].items()):
        nodes = [(sid, seq, nd) for (sid, seq), nds in pc.items() for nd in nds if nd["V"] == V]
        if not nodes:
            print("\n=== V=0x%X %s : 0 节点(本语料) ===" % (V, name))
            continue
        argc = collections.Counter(len(nd["args"]) for _, _, nd in nodes)
        print("\n=== V=0x%X %s : 节点 %d argc=%s ===" % (V, name, len(nodes), dict(argc)))
        # single 口径：V→PSV type 众数
        vt = collections.Counter()
        for sid, seq, nd in nodes:
            ps = psv.get((sid, seq))
            if ps and len(ps) == 1 and len(pc[(sid, seq)]) == 1:
                vt[ps[0]["type"]] += 1
        print("   single 口径 V→PSV type 众数: %s" % vt.most_common(8))
        exp = EXPECT.get(V) or ({vt.most_common(1)[0][0]} if vt else set())
        if not exp:
            print("   （无期望 type，跳过字段对拍）")
            continue
        print("   期望 type = %s" % sorted(exp))
        # 字段值集合（按 seq / 按场），仅 exp 类型
        seq_vals = collections.defaultdict(lambda: collections.defaultdict(set))
        scene_vals = collections.defaultdict(lambda: collections.defaultdict(set))
        for (sid, s2), rr in psv.items():
            for r in rr:
                if r["type"] not in exp:
                    continue
                for f in FIELDS:
                    v = num(r.get(f))
                    if v is not None:
                        seq_vals[(sid, s2)][f].add(v)
                        scene_vals[sid][f].add(v)
        # 基线：某字段全库值分布（命中率上界估计）
        pool = collections.Counter()
        for (sid, s2), rr in psv.items():
            for r in rr:
                if r["type"] in exp:
                    v = num(r.get("time"))
                    if v is not None:
                        pool[v] += 1
        # 对拍
        rep = []
        for p in range(max(argc) + 1):
            for f in FIELDS:
                for tf, fn in (("ms", lambda v: int(round(v * 0.06))), ("id", lambda v: v)):
                    sh = st_ = tot = 0
                    for sid, seq, nd in nodes:
                        args = nd["args"]
                        if p >= len(args):
                            continue
                        k, v = args[p]
                        if k not in ("N", "A", "I") or not isinstance(v, int):
                            continue
                        try:
                            x = fn(v)
                        except Exception:
                            continue
                        tot += 1
                        if x in seq_vals.get((sid, seq), {}).get(f, ()): 
                            sh += 1
                        if x in scene_vals.get(sid, {}).get(f, ()): 
                            st_ += 1
                    if tot:
                        rep.append(dict(pos=p, field=f, tf=tf, n=tot, seq=sh, scene=st_,
                                        seqr=sh / tot, scener=st_ / tot))
        # 只打印：time(ms/id) 与 各字段 id 的最高 3 项
        rep.sort(key=lambda r: (-r["scener"], -r["seqr"]))
        print("   [对拍 top] pos field tf  n   seq%   scene%")
        for r in rep[:14]:
            print("      %2d %-8s %-3s %5d  %.3f  %.3f" %
                  (r["pos"], r["field"], r["tf"], r["n"], r["seqr"], r["scener"]))
        out["0x%X" % V] = dict(name=name, nodes=len(nodes), argc=dict(argc),
                               vtype=dict(vt), expect=sorted(exp), top=rep[:40])
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("\n[JSON] ->", a.json)


if __name__ == "__main__":
    main()
