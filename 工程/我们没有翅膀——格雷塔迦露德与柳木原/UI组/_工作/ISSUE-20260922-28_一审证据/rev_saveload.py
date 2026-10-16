# -*- coding: utf-8 -*-
"""save/load 屏 sv.cpy 与 sv.hit_back 的像素级归属复算（复算 uiScreenClick 口径）。"""
import io, json, os

UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAY = json.load(io.open(os.path.join(UI, "layout", "ui_layout.json"), encoding="utf-8"))


def vis(e, flags):
    if e.get("visible_default") is False:
        return False
    fn = e.get("vis_flag")
    if fn in (None, ""):
        return True
    want = "" if e.get("vis_when") is None else str(e["vis_when"])
    cur = flags.get(fn, "")
    return (cur != "") if want == "*" else (cur == want)


def winner(els, x, y, flags):
    bz, b = -1, None
    for e in els:
        if e.get("kind") not in ("hit", "list"):
            continue
        if not all(k in e for k in ("x", "y", "w", "h")):
            continue
        if not vis(e, flags):
            continue
        if not (e["x"] <= x < e["x"] + e["w"] and e["y"] <= y < e["y"] + e["h"]):
            continue
        if e.get("z", 0) < bz:
            continue
        bz, b = e.get("z", 0), e
    return b


for sid in ("save", "load"):
    sc = LAY["screens"][sid]
    els = sc["elements"]
    flags = dict(sc.get("flags_default") or {})
    print("=" * 76)
    print("屏 %s" % sid)
    order = [e["id"] for e in els if e.get("kind") in ("hit", "list")]
    print("  点击候选声明序（后 = 后声明）:", order)
    for eid in ("sv.cpy", "sv.mov", "sv.hit_back"):
        e = [x for x in els if x["id"] == eid][0]
        d = {}
        for yy in range(e["y"], e["y"] + e["h"]):
            for xx in range(e["x"], e["x"] + e["w"]):
                wid = (winner(els, xx, yy, flags) or {}).get("id", "(无)")
                d[wid] = d.get(wid, 0) + 1
        tot = e["w"] * e["h"]
        own = d.get(eid, 0)
        print("  %-12s rect=%s  面积=%d  自身胜出=%d (%.1f%%)  分布=%s  action=%r"
              % (eid, (e["x"], e["y"], e["w"], e["h"]), tot, own, 100.0 * own / tot, d, e.get("action")))
