# -*- coding: utf-8 -*-
"""一审独立复算：全屏可点击元素重叠 + quickbar 四角/逐点可达性。
只读：不改任何被审文件。"""
import os, io, json, sys, glob

UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCR = os.path.join(UI, "layout", "screens")
LAY = json.load(io.open(os.path.join(UI, "layout", "ui_layout.json"), encoding="utf-8"))


def vis(e, flags):
    if e.get("visible_default") is False:
        return False
    fn = e.get("vis_flag")
    if fn is None or fn == "":
        return True
    want = e.get("vis_when")
    want = "" if want is None else str(want)
    cur = flags.get(fn, "")
    return (cur != "") if want == "*" else (cur == want)


def winner(els, x, y, flags, kinds=("hit", "list")):
    bestz, best = -1, None
    for e in els:
        if e.get("kind") not in kinds:
            continue
        if not all(k in e for k in ("x", "y", "w", "h")):
            continue
        if not vis(e, flags):
            continue
        if not (e["x"] <= x < e["x"] + e["w"] and e["y"] <= y < e["y"] + e["h"]):
            continue
        z = e.get("z", 0)
        if z < bestz:
            continue
        bestz, best = z, e
    return best

def ov(a, b):
    x0 = max(a["x"], b["x"]); x1 = min(a["x"] + a["w"], b["x"] + b["w"])
    y0 = max(a["y"], b["y"]); y1 = min(a["y"] + a["h"], b["y"] + b["h"])
    return max(0, x1 - x0) * max(0, y1 - y0)


print("=" * 78)
print("【1】全屏 kind in {hit,list} 两两重叠 —— 高 z 覆盖低 z 的可点击元素")
print("=" * 78)
found = 0
for sid in sorted(LAY["screens"].keys()):
    sc = LAY["screens"][sid]
    els = sc.get("elements") or []
    flags = dict(sc.get("flags_default") or {})
    cl = [e for e in els if e.get("kind") in ("hit", "list")
          and all(k in e for k in ("x", "y", "w", "h"))]
    for i in range(len(cl)):
        for j in range(i + 1, len(cl)):
            a, b = cl[i], cl[j]
            # rect-only overlap (ignore list internal item mapping)
            if a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]:
                continue
            if a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"]:
                continue
            o = ov(a, b)
            if o <= 0:
                continue
            bool_high = "?"
            hi, lo = (a, b) if a.get("z", 0) > b.get("z", 0) else (b, a)
            if hi.get("z", 0) == lo.get("z", 0):
                hi, lo = b, a   # 同 z：声明更晚者胜
                bool_high = "z-equal->later-wins"
            # 高 z 者能否真的吃掉低 z 者的**几何中心**
            cx = lo["x"] + lo["w"] / 2.0; cy = lo["y"] + lo["h"] / 2.0
            w = winner(els, cx, cy, flags)
            eaten = (w is not None and w["id"] == hi["id"]) if (
                cx < hi["x"] + hi["w"] and cx >= hi["x"] and cy < hi["y"] + hi["h"] and cy >= hi["y"]) else None
            found += 1
            print("[overlap] %-11s %-28s(z=%-3s) x %-28s(z=%-3s)  重叠=%5d  低z中心胜者=%s%s"
                  % (sid, hi["id"], hi.get("z"), lo["id"], lo.get("z"), o,
                     (w or {}).get("id", "(无)"),
                     "  <== 低z项中心被高z吞" if eaten else ""))
print("合计重叠对：%d" % found)

print()
print("=" * 78)
print("【2】quickbar 独立复算：收起态 / 展开态（中心 + 四角 + 全矩形逐点）")
print("=" * 78)
qb = LAY["screens"]["quickbar"]
els = qb["elements"]
ITEMS = ["lock", "save", "load", "qsave", "qload", "auto", "skip",
         "next", "prev", "log", "chart", "option"]
tog = [e for e in els if e["id"] == "quick.hit_toggle"][0]


def scan_full(flags, rect, step=1):
    x0, y0, w, h = rect
    d = {}
    for yy in range(int(y0), int(y0 + h), step):
        for xx in range(int(x0), int(x0 + w), step):
            wid = (winner(els, xx, yy, flags) or {}).get("id", "(无)")
            d[wid] = d.get(wid, 0) + 1
    return d


f0 = dict(qb.get("flags_default") or {})
print("收起态 flags=%s" % json.dumps(f0, ensure_ascii=False))
print("  竖条区域分布:", scan_full(f0, (tog["x"], tog["y"], tog["w"], tog["h"])))
print("  12 项在收起态可见者:", [k for k in ITEMS if vis([e for e in els if e['id'] == 'quick.hit_' + k][0], f0)])

fe = dict(f0); fe["quickbar"] = "expanded"
print("展开态 flags=%s" % json.dumps(fe, ensure_ascii=False))
bad = []
for k in ITEMS:
    e = [x for x in els if x["id"] == "quick.hit_" + k][0]
    pts = [(e["x"], e["y"]), (e["x"] + e["w"] - 1, e["y"]), (e["x"], e["y"] + e["h"] - 1),
           (e["x"] + e["w"] - 1, e["y"] + e["h"] - 1),
           (e["x"] + e["w"] / 2.0, e["y"] + e["h"] / 2.0)]
    names = ["左上", "右上", "左下", "右下", "中心"]
    for (px, py), nm in zip(pts, names):
        w = winner(els, px, py, fe)
        if (w or {}).get("id") != e["id"]:
            bad.append("%s %s(%g,%g) -> %s" % (e["id"], nm, px, py, (w or {}).get("id", "(无)")))
print("  展开态四角+中心失配点数:", len(bad))
for b in bad:
    print("    ✗", b)
print("  展开态：12 项**完整矩形逐点**扫描（每项 %d 点）" % (75 * 73))
tot_bad = 0
for k in ITEMS:
    e = [x for x in els if x["id"] == "quick.hit_" + k][0]
    d = scan_full(fe, (e["x"], e["y"], e["w"], e["h"]))
    if set(d.keys()) != {e["id"]}:
        tot_bad += 1
        print("    ✗ %s 矩形内胜者分布 = %s" % (e["id"], d))
print("  完整矩形非独占的项数:", tot_bad)
print("  展开态把手矩形分布:", scan_full(fe, (tog["x"], tog["y"], tog["w"], tog["h"])))

# 项间缝隙：展开态下 12 项之间 2px 缝 的胜者
gaps = []
for i in range(len(ITEMS) - 1):
    a = [x for x in els if x["id"] == "quick.hit_" + ITEMS[i]][0]
    b = [x for x in els if x["id"] == "quick.hit_" + ITEMS[i + 1]][0]
    y = a["y"] + a["h"]
    while y < b["y"]:
        gaps.append((y, (winner(els, 1885, y, fe) or {}).get("id", "(无)")))
        y += 1
print("  项间缝隙(y, 胜者):", gaps)
