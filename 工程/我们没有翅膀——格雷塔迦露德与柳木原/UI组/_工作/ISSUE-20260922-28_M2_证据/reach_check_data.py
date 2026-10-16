# -*- coding: utf-8 -*-
r"""
reach_check_data.py —— 独立复核「把手热区 vs 12 项热区」的可达性（★ M2 · ISSUE-20260922-28）

复核对象：主代理裁决里 M1 的修复 A 自证（`_工作\ISSUE-20260922-28_M1_证据\reach_check_result.txt`）。
本脚本**自己从 `layout/ui_layout.json`（= 生成物，引擎实际读取的那份数据）重算一遍**，
不引用 M1 的脚本或结论，用于独立确认：

  1. 展开态（quickbar=expanded）：竖条区域（x∈[1842,1920) 全高）内**每个像素**的胜者
     —— 期望：12 项各自的矩形内像素全归该项、把手热区胜出 **0** 像素；
  2. 收起态（默认）：期望把手热区独占（12 项不可见）；
  3. 展开态 + 气泡 + 钉住：与 1 相同（气泡/钉住不改变命中）。

命中规则与 `krkr/game/ui_screens.tjs` 的命中链**同规则**：
  候选 = kind ∈ {hit, list} 且 `uiScreenElementVisible(el)` 通过；
  含点用**半开区间** [x, x+w) × [y, y+h)；胜者 = z 最大，**同 z 时声明在后者胜**。

复跑：  python reach_check_data.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))          # <UI组>
LAYOUT = os.path.join(UI, "layout", "ui_layout.json")

data = json.load(open(LAYOUT, encoding="utf-8"))
sc = data["screens"]["quickbar"]
els = sc["elements"]
reveal = sc["reveal"]
defaults = sc["flags_default"]


def visible(el, flags):
    if el.get("visible_default", True) is False:
        return False
    fn = el.get("vis_flag")
    if not fn:
        return True
    want = el.get("vis_when", "")
    cur = flags.get(fn, "")
    if want == "*":
        return cur != ""
    return cur == want


def resolve(x, y, flags):
    best_z, best_id = -1, ""
    for el in els:                                  # 声明顺序遍历：同 z 后者胜（z < best_z 才跳过）
        if el.get("kind") not in ("hit", "list"):
            continue
        if not visible(el, flags):
            continue
        if not (el["x"] <= x < el["x"] + el["w"] and el["y"] <= y < el["y"] + el["h"]):
            continue
        z = el.get("z", 0)
        if z < best_z:
            continue
        best_z, best_id = z, el["id"]
    return best_id


ITEMS = [e["id"] for e in els if e.get("kind") == "hit" and e["id"].startswith("quick.hit_")
         and e["id"] != "quick.hit_toggle"]
TOGGLE = "quick.hit_toggle"

scenarios = [
    ("收起态（flags_default 原值）", dict(defaults)),
    ("展开态", dict(defaults, quickbar="expanded", qbar_tip="", qbar_pin="")),
    ("展开态+气泡+钉住", dict(defaults, quickbar="expanded", qbar_tip="lock", qbar_pin="1")),
]

x0 = reveal["in_x"]
x1 = 1920
verdicts = []
for name, flags in scenarios:
    counts = {}
    for x in range(x0, x1):
        for y in range(0, 1080):
            w = resolve(x, y, flags)
            if w:
                counts[w] = counts.get(w, 0) + 1
    total = sum(counts.values())
    item_px = sum(v for k, v in counts.items() if k in ITEMS)
    toggle_px = counts.get(TOGGLE, 0)
    print("=" * 74)
    print("%s  flags=%s" % (name, flags))
    print("  竖条区域 x∈[%d,%d) 全高：命中像素 %d" % (x0, x1, total))
    print("  12 项胜出 %d ／ 把手热区(%s)胜出 %d ／ 其它 %d"
          % (item_px, TOGGLE, toggle_px,
             total - item_px - toggle_px))
    for k in sorted(counts):
        print("      %-20s %d" % (k, counts[k]))
    if "展开" in name:
        per_item_ok = all(counts.get(i, 0) == next(
            e["w"] * e["h"] for e in els if e["id"] == i) for i in ITEMS)
        ok = per_item_ok and toggle_px == 0
        print("  ⇒ 判定：12 项各自矩形满覆盖=%s，把手胜出 0 像素=%s ⇒ %s"
              % (per_item_ok, toggle_px == 0, "PASS" if ok else "**FAIL**"))
        verdicts.append(ok)
    else:
        ok = toggle_px > 0 and item_px == 0
        print("  ⇒ 判定：12 项 0 像素、把手独占 ⇒ %s" % ("PASS" if ok else "**FAIL**"))
        verdicts.append(ok)

print("=" * 74)
print("总判定：%s（%d/%d 场景 PASS）"
      % ("PASS" if all(verdicts) else "**FAIL**", sum(1 for v in verdicts if v), len(verdicts)))
