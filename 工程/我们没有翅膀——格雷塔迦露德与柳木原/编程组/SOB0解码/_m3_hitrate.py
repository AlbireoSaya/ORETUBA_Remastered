# -*- coding: utf-8 -*-
"""M3 只读探针 6：候选映射的命中率精确计算（含变异自证接口）。

用法：
  python -X utf8 _m3_hitrate.py --spec "0x1B69C,5,time,ms,EffectQuake+SpriteQuake"
  python -X utf8 _m3_hitrate.py --spec "0x1B69C,4,time,ms,EffectQuake+SpriteQuake"   # 变异：位偏移
spec = V,pos,field,transform(id|ms|ms2),types(+分隔)

口径：
  exact  = 该 seq 恰 1 条指定 type 行 且 f(arg)==其 field（含分母）
  seqhit = f(arg) ∈ 该 seq 指定 type 行的 field 值集合
  scenhit= f(arg) ∈ 该场指定 type 行的 field 值集合
  base   = 该 type 全库 field 值分布的 top1 占比（随机基线）
"""
import os, sys, collections, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
import decode_sob0 as D

_CACHE = {}


def get(src):
    if src in _CACHE:
        return _CACHE[src]
    ledger = D.Ledger(D.LEDGER if os.path.isfile(D.LEDGER) else "")
    scenes, agg = D.collect(src, ledger)
    psv_by_scene, _ = D.load_psv_timeline()
    nodes = []
    for sid, (rows, info) in scenes.items():
        for nd in info["nodes"]:
            nodes.append((sid, nd["seq"], nd["V"], nd["args"], len(info["nodes"])))
    psvr = []
    for sid, rows in psv_by_scene.items():
        for r in rows:
            if r.get("type") != "Message":
                psvr.append((sid, int(r["seq"]), r["type"], r))
    _CACHE[src] = (nodes, psvr)
    return _CACHE[src]


def compute(src, V, pos, field, tf, types):
    nodes, psvr = get(src)
    seq = collections.defaultdict(list)      # (sid,seq) -> [(type,val)]
    scn = collections.defaultdict(list)      # sid -> [(type,val)]
    pcnt = collections.defaultdict(collections.Counter)  # (sid,seq) -> type count
    pool = collections.Counter()
    for sid, s2, ty, r in psvr:
        if types and ty not in types:
            continue
        v = r.get(field, "")
        try:
            iv = int(v)
        except (ValueError, TypeError):
            iv = None
        seq[(sid, s2)].append((ty, iv))
        scn[sid].append((ty, iv))
        if iv is not None:
            pool[iv] += 1
    # 基线
    tot_pool = sum(pool.values())
    base = (pool.most_common(1)[0][1] / tot_pool) if tot_pool else 0.0
    if tf == "ms":
        f = lambda v: int(round(v * 0.06))
    elif tf == "ms2":
        f = lambda v: int(round(v * 0.12))
    else:
        f = lambda v: v
    ex_h = ex_t = sh = sh_t = st = st_t = 0
    nex_h = nex_t = nsh = nsh_t = nst = nst_t = 0
    nonnum = 0
    for sid, s2, vv, args, _n in nodes:
        if vv != V or pos >= len(args):
            continue
        k, val = args[pos]
        if not isinstance(val, int):
            nonnum += 1
            continue
        x = f(val)
        cand = seq.get((sid, s2), [])
        vals = {iv for _t, iv in cand if iv is not None}
        sc_vals = {iv for _t, iv in scn.get(sid, []) if iv is not None}
        sh_t += 1
        if x in vals:
            sh += 1
        st_t += 1
        if x in sc_vals:
            st += 1
        single = (len(cand) == 1 and cand[0][1] is not None)
        if single:
            ex_t += 1
            if x == cand[0][1]:
                ex_h += 1
        # 非默认（值 != 0）口径：默认值 0 往往表示「用引擎默认」，金标不可直接比
        if val != 0:
            nsh_t += 1
            if x in vals:
                nsh += 1
            nst_t += 1
            if x in sc_vals:
                nst += 1
            if single:
                nex_t += 1
                if x == cand[0][1]:
                    nex_h += 1
    return dict(V=V, pos=pos, field=field, tf=tf, types=sorted(types) if types else "ALL",
                nodes=sum(1 for n in nodes if n[2] == V),
                nonnum=nonnum,
                exact=(ex_h, ex_t), seq=(sh, sh_t), scene=(st, st_t),
                nexact=(nex_h, nex_t), nseq=(nsh, nsh_t), nscene=(nst, nst_t),
                base=base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--spec", action="append", default=[])
    a = ap.parse_args()
    for sp in a.spec:
        parts = sp.split(",")
        V = int(parts[0], 16)
        pos = int(parts[1])
        field = parts[2]
        tf = parts[3]
        types = set(parts[4].split("+")) if len(parts) > 4 and parts[4] else None
        r = compute(a.src, V, pos, field, tf, types)
        def f2(pair):
            return "%d/%d(%.3f)" % (pair[0], pair[1], (pair[0] / pair[1]) if pair[1] else 0)
        print("V=0x%-6X pos%d %-7s %-3s types=%-22s 节点%-5d base=%.3f nonnum=%d\n"
              "       全:n=%d  exact=%s seq=%s scene=%s\n"
              "      非零:n=%d  exact=%s seq=%s scene=%s" %
              (r["V"], r["pos"], r["field"], r["tf"],
               ",".join(r["types"]) if isinstance(r["types"], list) else r["types"],
               r["nodes"], r["base"], r["nonnum"],
               r["seq"][1], f2(r["exact"]), f2(r["seq"]), f2(r["scene"]),
               r["nseq"][1], f2(r["nexact"]), f2(r["nseq"]), f2(r["nscene"])))


if __name__ == "__main__":
    main()
