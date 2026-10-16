# -*- coding: utf-8 -*-
"""M3 只读探针 2：PC 侧「效果/转场类命令」的实参画像。

对每个目标 V（按源本地），报告：节点数 / argc 分布 / 逐位 kind 分布与数值值域。
只读 `.sob`；只打印，不写盘。
用法：python -X utf8 _m3_node_inventory.py [--json out.json]
"""
import os, sys, json, collections, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
import decode_sob0 as D

TARGET = {
    "ot": {
        0x1B888: "Flash", 0x1B69C: "EffectQuake", 0x7480: "Window",
        0x1B040: "InOut_Act", 0x186C8: "sp_move", 0x10150: "bg_move",
        0xFDF4: "bg_zoom", 0x13300: "bg_blur", 0x2A150: "cross",
        0x19D58: "EffectQuakeEnd", 0x1C330: "EffectQuakeEnd(cand)",
        0x1BD8C: "EffectQuake(cand)", 0x1AD18: "EyeCatch/End",
        0x1C8D0: "SceneTitle", 0x11784: "EffectStart(?)", 0x11B0C: "EffectStart(cand)",
        0xEFF0: "?(EffectQuake)", 0x1ABF0: "?",
    },
    "otp": {},   # 由 V_NAMING 无 otp；下面按 name 反查
    "otr": {},
}


def short(v, n=24):
    if isinstance(v, str):
        s = v.replace("\n", "\\n")
        return s if len(s) <= n else s[:n] + "…"
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    out = {}
    for src, cfg in D.SOURCES.items():
        tgt = dict(TARGET.get(src, {}))
        sdir = cfg["dir"]
        prefix, ext = cfg["prefix"], cfg["ext"]
        # 收集所有 sob 文件
        files = []
        if os.path.isdir(sdir):
            for fn in sorted(os.listdir(sdir)):
                if not fn.endswith(ext):
                    continue
                if prefix and not fn.startswith(prefix):
                    continue
                files.append(os.path.join(sdir, fn))
        inv = {}
        for fp in files:
            try:
                sob = D.Sob0(fp)
            except Exception:
                continue
            nodes = sob.command_nodes()
            for i in nodes:
                V = sob.cells[i + 1]
                if V not in tgt:
                    continue
                args = sob.node_args(i)
                ent = inv.setdefault(V, dict(nodes=0, argc=collections.Counter(),
                                             pos=collections.defaultdict(collections.Counter),
                                             posnum=collections.defaultdict(list),
                                             files=set()))
                ent["nodes"] += 1
                ent["argc"][len(args)] += 1
                ent["files"].add(os.path.basename(fp))
                for p, (k, v) in enumerate(args):
                    ent["pos"][p][k] += 1
                    if k in ("N", "A", "I") and isinstance(v, int):
                        ent["posnum"][p].append(v)
        for cfg2 in (TARGET.get(src, {}),):
            pass
        out[src] = {}
        print("=" * 78)
        print("### 源 %s (%s)  文件 %d" % (src, cfg["note"], len(files)))
        for V in sorted(tgt):
            e = inv.get(V)
            if not e:
                print("  V=0x%-6X %-20s 节点 0" % (V, tgt[V]))
                continue
            print("  V=0x%-6X %-20s 节点 %-5d argc=%s" %
                  (V, tgt[V], e["nodes"], dict(e["argc"])))
            rec = dict(name=tgt[V], nodes=e["nodes"], argc=dict(e["argc"]), pos={})
            for p in sorted(e["pos"]):
                kinds = dict(e["pos"][p])
                nums = e["posnum"][p]
                rng = ""
                top = []
                if nums:
                    c = collections.Counter(nums)
                    top = c.most_common(5)
                    rng = " 值域[%d,%d]" % (min(nums), max(nums))
                ans = ""
                if any(k == "S" for k in kinds):
                    ans = " (含串)"
                print("       pos%d kinds=%s%s top=%s%s" %
                      (p, kinds, rng, top, ans))
                rec["pos"][p] = dict(kinds=kinds, n_num=len(nums),
                                     vmin=(min(nums) if nums else None),
                                     vmax=(max(nums) if nums else None),
                                     top=top)
            out[src]["0x%X" % V] = rec
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("\n[JSON] ->", a.json)


if __name__ == "__main__":
    main()
