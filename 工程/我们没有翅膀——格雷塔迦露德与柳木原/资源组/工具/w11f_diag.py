# -*- coding: utf-8 -*-
"""W11f 诊断：pic/sys 门控候选明细 + alpha 组抽检 + 撞名集合落盘。只读。"""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w11f_analyze as A

cache = A.load()
WORK = A.WORK


def detail(entries, normfn, label):
    g = A.build_groups(entries, normfn)
    rows = []
    for stem, cands in g.items():
        if len(cands) < 2:
            continue
        ars = [A.car(c) for c in cands]
        mx = max(A.rel(a, b) for a in ars for b in ars)
        if mx > A.GATE:
            rows.append(dict(stem=stem, n=len(cands), max_rel=round(mx, 4),
                             cands=["%s:%s %dx%d ar=%.4f" % (c["src"], c["name"], c["w"], c["h"], A.car(c)) for c in cands]))
    rows.sort(key=lambda r: -r["max_rel"])
    print("== %s 门控候选 %d 组 ==" % (label, len(rows)))
    for r in rows[:60]:
        print("  %-18s rel=%.3f n=%d | %s" % (r["stem"], r["max_rel"], r["n"], " ; ".join(r["cands"])))
    if len(rows) > 60:
        print("  ... 其余 %d 组" % (len(rows) - 60))
    return rows


pic = [v for v in cache.values() if v["kind"] == "pic"]
sys_ = [v for v in cache.values() if v["kind"] in ("sys", "etc")]
pr = detail(pic, lambda m: m["name"][:-4][len(m["src"]) + 1:].lower(), "CG背景(pic)")
sr = detail(sys_, lambda m: m["name"][:-4][len(m["src"]) + 1:].lower(), "系统UI(sys+etc)")

# alpha 多源组抽检：canvas 选 vs 内容选 是否可能不同
print("\n== alpha 多源组（pic） ==")
g = A.build_groups(pic, lambda m: m["name"][:-4][len(m["src"]) + 1:].lower())
cnt = 0
for stem, cands in g.items():
    if len(cands) > 1 and any(c["has_alpha"] for c in cands):
        cnt += 1
        if cnt <= 20:
            print("  %-14s %s" % (stem, " ; ".join(
                "%s:%s %dx%d bbox=%s cov=%.3f" % (c["src"], c["name"], c["w"], c["h"], c["bbox"], c["cov"]) for c in cands)))
print("  alpha 多源组数:", cnt)

print("\n== alpha 多源组（sys） ==")
g2 = A.build_groups(sys_, lambda m: m["name"][:-4][len(m["src"]) + 1:].lower())
cnt = 0
diffsel = 0
for stem, cands in g2.items():
    if len(cands) > 1 and any(c["has_alpha"] for c in cands):
        cnt += 1
        old = A.pick_old_canvas(cands); new = A.pick_new(cands)
        if old["path"] != new["path"]:
            diffsel += 1
            print("  DIFF %-14s old=%s new=%s" % (stem, old["name"], new["name"]))
        elif cnt <= 15:
            print("  %-14s %s" % (stem, " ; ".join(
                "%s:%s %dx%d bbox=%s" % (c["src"], c["name"], c["w"], c["h"], c["bbox"]) for c in cands)))
print("  alpha 多源组数:", cnt, " 选源分歧:", diffsel)

json.dump(dict(pic_gate=pr, sys_gate=sr), open(os.path.join(WORK, "_gate_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwrote _gate_candidates.json")