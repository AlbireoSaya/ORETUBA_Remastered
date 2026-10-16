# -*- coding: utf-8 -*-
"""A1 复算：配置屏静音行 visible_default、z 平票、判据收紧的影响面。
读 committed 副本 25_config.json（= git show 5fc961f:...）。"""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(HERE, "25_config.json")
d = json.load(io.open(f, encoding="utf-8"))
els = d["elements"]

def cand_krkr(e):
    """ui_screens.tjs @5fc961f 判据复算"""
    if e.get("state_assets") is not None:
        return True
    if e.get("kind") != "hit":
        return False
    return (e.get("state_group") or "") != ""

def cand_loose(e):
    """旧判据（收紧前）：带 state_assets 或 任何 hit"""
    return e.get("state_assets") is not None or e.get("kind") == "hit"

print("配置屏元素数 =", len(els))
print("visible_default:false 件数 =", sum(1 for e in els if e.get("visible_default") is False))

print("\n--- 静音行相关（id 含 mute） ---")
for e in els:
    if "mute" in e["id"]:
        print("  %-22s kind=%-5s z=%-5s vis_def=%-5s group=%-14s state_assets=%s rect=(%s,%s,%s,%s)" % (
            e["id"], e.get("kind"), e.get("z"), e.get("visible_default"),
            repr(e.get("state_group")), "Y" if e.get("state_assets") else "-",
            e["x"], e["y"], e["w"], e["h"]))

print("\n--- cfg.mute_off 的 state_assets 落地元素（同组） ---")
mute_off = [e for e in els if e["id"] == "cfg.mute_off"]
print("  找到 %d 件 cfg.mute_off" % len(mute_off))
for e in mute_off:
    print("   ", json.dumps(e, ensure_ascii=False)[:400])

print("\n--- 与 cfg.mute_off 同组的元素 ---")
if mute_off:
    g = mute_off[0].get("state_group")
    for e in els:
        if e.get("state_group") == g:
            print("  %-22s kind=%-5s z=%-5s vis_def=%-5s assets=%s" % (
                e["id"], e.get("kind"), e.get("z"), e.get("visible_default"),
                "Y" if e.get("state_assets") else "-"))

print("\n--- cfg.mute_hit / cfg.it_facewindow_hit ---")
for e in els:
    if e["id"] in ("cfg.mute_hit", "cfg.it_facewindow_hit"):
        print("  %-24s kind=%-5s z=%-5s vis=%-5s group=%-14s rect=(%s,%s,%s,%s)" % (
            e["id"], e.get("kind"), e.get("z"), e.get("visible_default"),
            repr(e.get("state_group")), e["x"], e["y"], e["w"], e["h"]))

def winner(els_, x, y, cand):
    best_z, best = -1, None
    for e in els_:
        if e.get("visible_default") is False:
            continue
        if not cand(e):
            continue
        if not (e["x"] <= x < e["x"] + e["w"] and e["y"] <= y < e["y"] + e["h"]):
            continue
        if e.get("z", 0) < best_z:
            continue
        best_z, best = e.get("z", 0), e
    return best

if mute_off:
    e = mute_off[0]
    cx, cy = e["x"] + e["w"] / 2.0, e["y"] + e["h"] / 2.0
    print("\n--- 在 cfg.mute_off 几何中心 (%.1f,%.1f) 复算胜出者 ---" % (cx, cy))
    for name, cand in (("收紧后(现行)", cand_krkr), ("收紧前(任何 hit)", cand_loose)):
        w = winner(els, cx, cy, cand)
        print("  %-20s -> %s  组=%s" % (name, w["id"] if w else "(无)",
                                        repr(w.get("state_group")) if w else "-"))

print("\n--- 判据收紧的差值（收紧前 - 收紧后 的候选集） ---")
loose = set(id(e) for e in els if cand_loose(e))
tight = set(id(e) for e in els if cand_krkr(e))
print("  宽松候选数=%d 收紧候选数=%d 差值=%d" % (len(loose), len(tight), len(loose - tight)))
for e in els:
    if id(e) in (loose - tight):
        print("    落在判据外: %-22s kind=%-5s z=%-5s group=%r" % (e["id"], e.get("kind"), e.get("z"), e.get("state_group")))
