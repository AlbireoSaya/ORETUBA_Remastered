# -*- coding: utf-8 -*-
"""针对全屏重叠扫描里被标记的候选，逐件核几何/可见性/动作，判断是否真的「子项不可达」。"""
import io, json, os

UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAY = json.load(io.open(os.path.join(UI, "layout", "ui_layout.json"), encoding="utf-8"))

CASES = [
    ("backlog", ["bl.up_hit", "bl.close_hit", "bl.spk_hit", "bl.jump_hit"]),
    ("config", ["cfg.mute_hit", "cfg.it_facewindow_hit", "cfg.on_hit", "cfg.off_hit", "cfg.sl1_hit"]),
    ("save", ["sv.hit_back", "sv.mov", "sv.cpy"]),
    ("load", ["sv.hit_back", "sv.mov", "sv.cpy"]),
]

for sid, ids in CASES:
    sc = LAY["screens"][sid]
    els = {e["id"]: e for e in sc["elements"]}
    print("=" * 78)
    print("屏 %s  flags_default=%s" % (sid, json.dumps(sc.get("flags_default") or {}, ensure_ascii=False)))
    for i in ids:
        e = els.get(i)
        if not e:
            print("  %-24s <不存在>" % i)
            continue
        print("  %-24s z=%-3s kind=%-5s rect=(%s,%s,%s,%s) vis_def=%s action=%r label=%r"
              % (i, e.get("z"), e.get("kind"), e.get("x"), e.get("y"), e.get("w"), e.get("h"),
                 e.get("visible_default"), e.get("action"), e.get("label")))
        print("        note=%s" % (e.get("note") or "")[:110])
    # 交集判定：低 z 者的**几何中心**是否落在高 z 者矩形内
    for lo_id, hi_id in ((ids[0], ids[1]), (ids[2], ids[3])) if len(ids) >= 4 else []:
        lo, hi = els.get(lo_id), els.get(hi_id)
        if not lo or not hi:
            continue
        cx, cy = lo["x"] + lo["w"] / 2.0, lo["y"] + lo["h"] / 2.0
        inside = (hi["x"] <= cx < hi["x"] + hi["w"] and hi["y"] <= cy < hi["y"] + hi["h"])
        print("  → %s 中心(%.0f,%.0f) 在 %s 内? %s（z %s vs %s）"
              % (lo_id, cx, cy, hi_id, inside, lo.get("z"), hi.get("z")))
