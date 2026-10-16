# -*- coding: utf-8 -*-
"""D10 / C8 辅助：列出所有「带态图 + 带组」元素（= test_state_targets 检查的 25 个），
并列出状态组的两端归属（image 承美术 / hit 承检测）。"""
import io, json, glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
SCREENS = os.path.join(UI, "layout", "screens")

print("UI =", UI)
tot = 0
group_map = {}
for f in sorted(glob.glob(os.path.join(SCREENS, "[0-9]*.json"))):
    d = json.load(io.open(f, encoding="utf-8"))
    name = os.path.basename(f)
    for e in d.get("elements") or []:
        g = e.get("state_group") or ""
        has = e.get("state_assets") is not None
        if not (has or g):
            continue
        if has and g:
            tot += 1
            print("  [目标] %-22s %-16s kind=%-5s z=%-4s vis=%-5s group=%s rect=(%s,%s,%s,%s)" % (
                name, e["id"], e.get("kind"), e.get("z"), e.get("visible_default"),
                g, e["x"], e["y"], e["w"], e["h"]))
        group_map.setdefault(g or "(无组)", []).append((name, e["id"], e.get("kind"), has))
        if not g:
            print("  [仅态图·无组] %-16s %-22s kind=%s" % (name, e["id"], e.get("kind")))
print("\n合计「态图+组」元素 =", tot)
print("\n--- 组清单（组名 -> 成员） ---")
for g in sorted(group_map):
    print("  %-24s %s" % (g, group_map[g]))
