# -*- coding: utf-8 -*-
"""
W11f · 分析：pic / sys 按新度量复核 + 撞名全量扫描 + np\\pic 定位
只读缓存，输出 JSON 到 子代理工作区\\ISSUE-20260918-06\\W11f\\。
"""
import os, sys, json, collections

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame"), "写入边界越界: " + WORK
CACHE = os.path.join(WORK, "_meta_cache.json")
UNI = os.path.join(PROJ, "资源组", "美术统一")

SRCS = ["ot", "ota", "otp", "otr", "otv", "np"]
PRIO = {s: i for i, s in enumerate(SRCS)}
GATE = 0.05

NP_PIC_10 = ["np_aki02b.png", "np_ban01a.png", "np_chi01i.png", "np_kaz01h.png",
             "np_kob02c.png", "np_kur01d.png", "np_mas01c.png", "np_mas01e.png",
             "np_mis01h.png", "np_miy02a.png"]


def load():
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def cmeta(m):
    x0, y0, x1, y1 = m["bbox"]
    bw, bh = x1 - x0, y1 - y0
    return bw, bh, bw * bh, x0, y0


def car(m):
    bw, bh, _, _, _ = cmeta(m)
    return bw / max(1, bh)


def rel(a, b):
    return abs(a - b) / max(a, b)


def clusters(cands):
    n = len(cands)
    par = list(range(n))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            if rel(car(cands[i]), car(cands[j])) <= GATE:
                ri, rj = find(i), find(j)
                if ri != rj:
                    par[max(ri, rj)] = min(ri, rj)
    cl = collections.defaultdict(list)
    for i, r in enumerate(cands):
        cl[find(i)].append(r)
    return [cl[k] for k in sorted(cl)]


def pick_new(cands):
    nps = [c for c in cands if c["src"] == "np"]
    pool = nps if nps else cands
    return max(pool, key=lambda c: (cmeta(c)[2], cmeta(c)[0], -PRIO[c["src"]]))


def pick_old_canvas(cands):
    return max(cands, key=lambda c: (c["w"] * c["h"], c["w"], -PRIO[c["src"]]))


def build_groups(entries, normfn):
    g = collections.defaultdict(list)
    for m in entries:
        g[normfn(m)].append(m)
    return g


def analyze_pic(cache):
    entries = [v for v in cache.values() if v["kind"] == "pic"]
    g = build_groups(entries, lambda m: m["name"][:-4][len(m["src"]) + 1:].lower())
    res = dict(groups=len(g), files=len(entries), sel_changes=[], gate_splits=[],
               alpha_groups=0, np_pic_in_groups=[])
    for stem, cands in g.items():
        if any(c["has_alpha"] for c in cands):
            res["alpha_groups"] += 1
        old = pick_old_canvas(cands)
        cl = clusters(cands)
        if len(cl) == 1:
            new = pick_new(cands)
            if new["path"] != old["path"]:
                res["sel_changes"].append(dict(stem=stem, old="%s:%s" % (old["src"], old["name"]),
                                               new="%s:%s" % (new["src"], new["name"]),
                                               old_area=cmeta(old)[2], new_area=cmeta(new)[2],
                                               old_canvas="%dx%d" % (old["w"], old["h"]),
                                               new_canvas="%dx%d" % (new["w"], new["h"])))
        else:
            # 门控命中：主簇 + alt 簇
            overall = pick_new(cands)
            main_cl = next(c for c in cl if any(x is overall for x in c))
            alts = [c for c in cl if c is not main_cl]
            sel_main = pick_new(main_cl)
            res["gate_splits"].append(dict(
                stem=stem, clusters=[[x["name"] for x in c] for c in cl],
                aspects={x["name"]: round(car(x), 4) for x in cands},
                main="%s:%s" % (sel_main["src"], sel_main["name"]),
                alts=["%s:%s" % (pick_new(c)["src"], pick_new(c)["name"]) for c in alts]))
        # np/pic 立绘定位
        for c in cands:
            if c["name"] in NP_PIC_10:
                res["np_pic_in_groups"].append(dict(name=c["name"], stem=stem,
                                                    new_win=("%s:%s" % (pick_new(cands)["src"], pick_new(cands)["name"])),
                                                    area=cmeta(c)[2]))
    return res


def analyze_sys(cache):
    entries = [v for v in cache.values() if v["kind"] in ("sys", "etc")]
    g = build_groups(entries, lambda m: m["name"][:-4][len(m["src"]) + 1:].lower())
    res = dict(groups=len(g), files=len(entries), sel_changes=[], gate_splits=[],
               alpha_groups=0)
    for stem, cands in g.items():
        if any(c["has_alpha"] for c in cands):
            res["alpha_groups"] += 1
        old = pick_old_canvas(cands)
        cl = clusters(cands)
        if len(cl) == 1:
            new = pick_new(cands)
            if new["path"] != old["path"]:
                res["sel_changes"].append(dict(stem=stem, old="%s:%s" % (old["src"], old["name"]),
                                               new="%s:%s" % (new["src"], new["name"]),
                                               old_area=cmeta(old)[2], new_area=cmeta(new)[2],
                                               old_canvas="%dx%d" % (old["w"], old["h"]),
                                               new_canvas="%dx%d" % (new["w"], new["h"])))
        else:
            overall = pick_new(cands)
            main_cl = next(c for c in cl if any(x is overall for x in c))
            alts = [c for c in cl if c is not main_cl]
            res["gate_splits"].append(dict(
                stem=stem, clusters=[[x["name"] for x in c] for c in cl],
                aspects={x["name"]: round(car(x), 4) for x in cands},
                main="%s:%s" % (pick_new(main_cl)["src"], pick_new(main_cl)["name"]),
                alts=["%s:%s" % (pick_new(c)["src"], pick_new(c)["name"]) for c in alts]))
    return res


def main():
    cache = load()
    out = {}
    out["pic"] = analyze_pic(cache)
    out["sys"] = analyze_sys(cache)

    # ---- 撞名扫描 ----
    def names(d):
        return {fn for fn in os.listdir(os.path.join(UNI, d)) if fn.lower().endswith(".png")}
    nc = names("立绘")
    ncg = names("CG背景")
    nui = names("系统UI")
    coll = dict(liritsu_cg=sorted(nc & ncg), liritsu_ui=sorted(nc & nui),
                cg_ui=sorted(ncg & nui))
    out["collisions"] = {k: dict(n=len(v), sample=v[:200]) for k, v in coll.items()}
    out["counts"] = dict(立绘=len(nc), CG背景=len(ncg), 系统UI=len(nui))

    with open(os.path.join(WORK, "_analyze.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== pic ===")
    print("groups", out["pic"]["groups"], "files", out["pic"]["files"],
          "alpha_groups", out["pic"]["alpha_groups"],
          "sel_changes", len(out["pic"]["sel_changes"]), "gate_splits", len(out["pic"]["gate_splits"]))
    print("np_pic_in_groups:", len(out["pic"]["np_pic_in_groups"]))
    for x in out["pic"]["np_pic_in_groups"]:
        print("   ", x)
    print("=== sys ===")
    print("groups", out["sys"]["groups"], "files", out["sys"]["files"],
          "alpha_groups", out["sys"]["alpha_groups"],
          "sel_changes", len(out["sys"]["sel_changes"]), "gate_splits", len(out["sys"]["gate_splits"]))
    print("=== collisions ===")
    for k, v in out["collisions"].items():
        print("  ", k, v["n"], v["sample"][:30])
    print("=== counts ===", out["counts"])


if __name__ == "__main__":
    main()