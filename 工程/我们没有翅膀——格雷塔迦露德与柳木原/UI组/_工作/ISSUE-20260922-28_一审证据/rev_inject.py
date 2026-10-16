# -*- coding: utf-8 -*-
"""一审独立反向注入（内存内，不写磁盘）：
1) 在**非 quickbar** 屏给某个状态目标注入更高 z 的异组遮挡 —— test_state_targets 应 FAIL。
2) 给 23_save 注入一件 z=999 的**纯热区**（无 state_assets / 无 state_group）盖住 sv.cpy 中心
   —— 验证「纯热区遮挡」是否能被现两道守门抓到。
"""
import io, json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(UI, "工具")
sys.path.insert(0, TOOLS)
import test_state_targets as T


def load_all():
    out = []
    for f in sorted(glob.glob(os.path.join(T.SCREENS, "[0-9]*.json"))):
        out.append((os.path.basename(f), json.load(io.open(f, encoding="utf-8"))))
    return out


docs = load_all()

print("=" * 78)
print("【破坏 1】在 26_backlog.json 给状态目标注入 z=999 异组遮挡（非 01_title，自证未覆盖的屏）")
print("=" * 78)
vic = None
for name, d in docs:
    if name != "26_backlog.json":
        continue
    for e in d["elements"]:
        if T.group_of(e) and T.is_candidate(e) and e.get("visible_default") is not False:
            vic = (name, e)
            break
print("选中的受害者:", vic[1]["id"], "组=", T.group_of(vic[1]))
d2 = []
for name, d in docs:
    dd = json.loads(json.dumps(d))
    if name == vic[0]:
        e = vic[1]
        dd["elements"].append({"id": "zz.rev_occluder", "kind": "hit", "z": 999, "action": "close",
                               "label": "", "note": "一审注入",
                               "x": e["x"], "y": e["y"], "w": e["w"], "h": e["h"],
                               "state_group": "zz.rev_other"})
    d2.append((name, dd))
f, cov, _ = T.check_reach(d2)
hit = [x for x in f if "zz.rev_occluder" in x]
print("test_state_targets.check_reach 失败 %d 项，其中含 zz.rev_occluder 的 %d 项："
      % (len(f), len(hit)))
for x in hit[:4]:
    print("    ✗", x)
print("⇒ %s" % ("守门抓到（符合预期）✓" if hit else "**守门漏掉** ✗"))

print()
print("=" * 78)
print("【破坏 2】23_save.json 注入 z=999 **纯热区**（无态图无组）盖住 sv.cpy 全矩形")
print("=" * 78)
d3 = []
for name, d in docs:
    dd = json.loads(json.dumps(d))
    if name == "23_save.json":
        dd["elements"].append({"id": "zz.plain_hit", "kind": "hit", "z": 999, "action": "close",
                              "label": "", "note": "一审注入：纯热区",
                              "x": 1623, "y": 964, "w": 156, "h": 61})
    d3.append((name, dd))
f3, _, _ = T.check_reach(d3)
print("test_state_targets 失败项 %d（含 zz.plain_hit 的 %d 项）"
      % (len(f3), len([x for x in f3 if "zz.plain_hit" in x])))
print("⇒ %s" % ("被抓到" if any("zz.plain_hit" in x for x in f3) else
                "**未被抓到** —— 悬停层守门对「纯热区遮挡」天然免疫（口径不同，非缺陷但需知）"))

# 用点击层口径复算：sv.cpy 是否已被现网数据吞掉（不是注入）
print()
print("=" * 78)
print("【事实核查】现网 23_save.json：sv.cpy 逐像素点击归属（点击层口径 uiScreenClick）")
print("=" * 78)
sd = [d for n, d in docs if n == "23_save.json"][0]
els = sd["elements"]
flags = dict(sd.get("flags_default") or {})


def click_winner(x, y):
    bz, b = -1, None
    for e in els:
        if e.get("kind") not in ("list", "hit"):
            continue
        if not T.flag_visible(e, flags):
            continue
        if not (e["x"] <= x < e["x"] + e["w"] and e["y"] <= y < e["y"] + e["h"]):
            continue
        if e.get("z", 0) < bz:
            continue
        bz, b = e.get("z", 0), e
    return b


cpy = [e for e in els if e["id"] == "sv.cpy"][0]
d = {}
for yy in range(cpy["y"], cpy["y"] + cpy["h"]):
    for xx in range(cpy["x"], cpy["x"] + cpy["w"]):
        w = click_winner(xx, yy)
        d[(w or {}).get("id", "(无)")] = d.get((w or {}).get("id", "(无)"), 0) + 1
print("sv.cpy 面积=%d 胜者分布=%s ⇒ sv.cpy 自身胜出 %d 点"
      % (cpy["w"] * cpy["h"], d, d.get("sv.cpy", 0)))
