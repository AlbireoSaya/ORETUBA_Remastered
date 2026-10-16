# -*- coding: utf-8 -*-
r"""M51 · BGM 鉴赏页 · **草稿自检**（在 `28_music.draft.json` 上跑，**不碰磁盘上的 28_music.json**）

为什么需要：`28_music.json` 尚未落盘（生成器 `m34_build_screens.build_music` 未退休 ⇒ 直接改会让
`test_gen_sync.py` 报 UNSYNC），故正式守门脚本（`gen_layout` / `verify_ui` / `test_*`）暂时读不到本屏。
本脚本把其中**与本屏有关的那几条判据**复算一遍，先给出可核对的证据。

判据（与既有守门脚本同口径，逐条注明出处）
  ① 元素 id 全局唯一 —— `gen_layout.py` 约束 1
  ② `@palette.<key>` 必须存在于 `palette.json` —— `gen_layout.py` 约束 2
  ③ `image` / `item_buttons` / `slider.rail` / `slider.handle` 引用的 PNG 必须存在 —— `verify_ui.py` [1]
  ④ 无 `nine` 的 `image`：`w/h` 必须 = PNG 实尺寸；`item_buttons` 同判据 —— `verify_ui.py` [2]
  ⑤ `item_buttons` / `item_text` 矩形必须**在块内**（块内局部坐标，不出块）—— `_schema.md` §四 M06 守卫
  ⑥ `opacity` ∈ 0–255 —— `verify_ui.py` [7]
  ⑦ 本屏命中元素（hit/list）**互不重叠**或高 z 明确胜出（逐对复算，报出重叠对）—— `_schema.md` §四 铁律一/二
  ⑧ 参考作 BGM 页 **34 条**逐条对照（一致 / 有意不同 / 不适用）
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
DRAFT = os.path.join(HERE, "28_music.draft.json")

ok_all = True


def say(ok, name, detail=""):
    global ok_all
    ok_all &= bool(ok)
    print("  [%s] %-52s %s" % ("OK " if ok else "NG!", name, detail))
    return bool(ok)


def main():
    with open(DRAFT, encoding="utf-8") as f:
        d = json.load(f)
    with open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8") as f:
        pal = json.load(f)["colors"]
    els = d["elements"]
    print("=" * 100)
    print("M51 · BGM 页草稿自检：%s" % DRAFT)
    print("  元素 %d 件 ｜ 屏 id=%s ｜ owner=%s ｜ attach=%s"
          % (len(els), d["id"], d.get("owner"), d.get("attach")))
    print("=" * 100)

    # ① id 唯一
    ids = [e["id"] for e in els]
    dup = [i for i in set(ids) if ids.count(i) > 1]
    say(not dup, "① 元素 id 全局唯一", "重名 %s" % dup if dup else "%d 个 id" % len(ids))

    # ② 色板键存在
    bad = set()
    for e in els:
        for v in list(e.values()) + list((e.get("font") or {}).values()):
            if isinstance(v, str) and v.startswith("@palette."):
                if v.split(".", 1)[1] not in pal:
                    bad.add(v)
        hl = e.get("highlight") or {}
        for v in hl.values():
            if isinstance(v, str) and v.startswith("@palette.") and v.split(".", 1)[1] not in pal:
                bad.add(v)
        if isinstance(e.get("highlight_font_color"), str) and e["highlight_font_color"].startswith("@palette."):
            if e["highlight_font_color"].split(".", 1)[1] not in pal:
                bad.add(e["highlight_font_color"])
        for b in (e.get("item_buttons") or []):
            for v in list((b.get("font") or {}).values()):
                if isinstance(v, str) and v.startswith("@palette.") and v.split(".", 1)[1] not in pal:
                    bad.add(v)
    say(not bad, "② `@palette.*` 引用键均存在", "缺键 %s" % sorted(bad) if bad else "全部命中")

    # ③④ 素材存在 + 尺寸 1:1
    refs = []           # (用途, asset, 期望 w, 期望 h, 是否允许 nine)
    for e in els:
        if e["kind"] == "image":
            refs.append((e["id"], e["asset"], e["w"], e["h"], e.get("nine")))
            for k, v in (e.get("state_assets") or {}).items():
                refs.append((e["id"] + "." + k, v, e["w"], e["h"], e.get("nine")))
        if e["kind"] == "slider":
            refs.append((e["id"] + ".rail", e["rail"]["asset"], None, None, None))
            h = e["handle"]
            refs.append((e["id"] + ".handle", h["asset"], None, None, None))
            for k, v in (h.get("state_assets") or {}).items():
                refs.append((e["id"] + ".handle." + k, v, None, None, None))
        for b in (e.get("item_buttons") or []):
            for k, v in (b.get("state_assets") or {"normal": b.get("asset")}).items():
                refs.append((e["id"] + "[" + b["key"] + "]." + k, v, b["w"], b["h"], b.get("nine")))
        fr = e.get("item_frame") or {}
        if fr:
            refs.append((e["id"] + ".item_frame", fr["asset"], e.get("item_w"), e.get("item_h"), fr.get("nine")))
            for k, v in (fr.get("state_assets") or {}).items():
                refs.append((e["id"] + ".item_frame." + k, v, e.get("item_w"), e.get("item_h"), fr.get("nine")))
    missing, sizemismatch = [], []
    for who, rel, ew, eh, nine in refs:
        p = os.path.join(ASSETS, os.path.basename(rel))
        if not os.path.exists(p):
            missing.append("%s -> %s" % (who, rel))
            continue
        if ew is None:
            continue
        with Image.open(p) as im:
            w, h = im.size
        if nine:
            if ew < nine["l"] + nine["r"] or eh < nine["t"] + nine["b"]:
                sizemismatch.append("%s nine 越界 %dx%d" % (who, w, h))
        elif (w, h) != (ew, eh):
            sizemismatch.append("%s 期望 %dx%d 实为 %dx%d" % (who, ew, eh, w, h))
    say(not missing, "③ 引用素材全部存在", "缺 %d：%s" % (len(missing), missing) if missing else "%d 条引用" % len(refs))
    say(not sizemismatch, "④ 无 nine 件尺寸 1:1", "; ".join(sizemismatch) if sizemismatch else "全部一致")

    # ⑤ 块内几何
    probs = []
    for e in els:
        if e["kind"] != "list":
            continue
        bw, bh = e["item_w"], e["item_h"]
        for b in (e.get("item_buttons") or []):
            if b["x"] < 0 or b["y"] < 0 or b["x"] + b["w"] > bw or b["y"] + b["h"] > bh:
                probs.append("%s[%s] 出块" % (e["id"], b["key"]))
        it = e.get("item_text")
        if it and (it["x"] < 0 or it["y"] < 0 or it["x"] + it["w"] > bw or it["y"] + it["h"] > bh):
            probs.append("%s item_text 出块" % e["id"])
    say(not probs, "⑤ item_buttons / item_text 均在块内", "; ".join(probs) if probs else "全部在块内")

    # ⑥ opacity 范围
    badop = [e["id"] for e in els if isinstance(e.get("opacity"), int) and not (0 <= e["opacity"] <= 255)]
    say(not badop, "⑥ opacity ∈ 0–255", str(badop) if badop else "全部合规")

    # ⑦ 命中元素重叠复算
    hits = [(e["id"], e["x"], e["y"], e["w"], e["h"], e.get("z", 0))
            for e in els if e["kind"] in ("hit", "list")]
    ov = []
    for i in range(len(hits)):
        for j in range(i + 1, len(hits)):
            a, b = hits[i], hits[j]
            if a[1] < b[1] + b[3] and b[1] < a[1] + a[3] and a[2] < b[2] + b[4] and b[2] < a[2] + a[4]:
                ov.append("%s(z%d) ∩ %s(z%d)" % (a[0], a[5], b[0], b[5]))
    say(not ov, "⑦ 命中元素无重叠（同 z 会互抢）", "; ".join(ov) if ov else "%d 个命中元素两两不交" % len(hits))

    # ⑧ 参考作 34 条对照（人工逐条，脚本只打印清单供核对）
    print("-" * 100)
    print("⑧ 参考作 BGM 页 34 条 → 本屏处置（逐条）")
    for line in REF34:
        print("    " + line)
    print("=" * 100)
    print("RESULT=%s" % ("OK 草稿自检全过" if ok_all else "NG 有自检未过（见上）"))
    print("★ 正式守门（gen_layout / verify_ui / test_* / HTML 自检 / 引擎巡演）**必须在本屏落盘后**跑；")
    print("  落盘前置条件：主代理裁决「退休 `m34_build_screens.build_music`」（任务书 D 条）。")
    print("=" * 100)
    return 0 if ok_all else 1


REF34 = [
    " 1 Sound/caption (67,100,469,62)        → 归**共享外壳**（`39_gal_shell`，本屏 attach；标题由引擎绘制）",
    " 2 Sound/曲名/オフ・オンマウス 1344×564   → **有意不同**：不照抄整张曲名位图；逐行 `item_text` 引擎绘制（铁律禁文字烘焙）",
    " 3 Sound/曲名/オン 1344×564              → **有意不同**：同上；选中态改由 `highlight` 块 + `highlight_font_color` 表达",
    " 4-33 Sound/pos/#0|#1|#2/0…9（30 条）    → **一致**：1 个二维网格 list（3×10=30 槽/页，列步进 527、行步进 60、行矩形 481×59）",
    "     ↳ 逐条差异：折行**行优先**（M1 口径）vs 参考作列优先 → 有意差异（已登记）",
    "34 Sound/item/unknown (409,226,46,22)   → **不适用**：收录口径只收剧本实际引用过的曲目 ⇒ 无「未解锁」概念；不实现（登记）",
    "35 Sound/item/play (171,214,29,40)      → **一致**：`item_buttons[0]` 块内局部 (0,7,29,40)（块起点 171）",
    "36 Sound/item/オフ (205,217,452,37)      → **一致**：`item_frame.state_assets.normal`（卡体块内 (34,10)-(486,47)）",
    "37 Sound/item/オンマウス 同矩形          → **一致**：`state_assets.hover`（M46 逐项三态）",
    "38 Sound/item/オン (199,211,464,49)      → **一致（形态不同）**：`state_assets.pressed` 同卡体尺寸（M46 只支持同几何三态）",
    "39 Sound/item/#rect (190,207,481,59)     → **一致**：`list` 项矩形（我方 526×59，卡体绝对位对齐）",
    "40-47 Sound/ボタン/#pos/{none,one,all,rnd,prev,playpause,stop,next} 59×59 → **一致**：8 键逐键出件（x=609/702/793/885/975/1062/1153/1234, y831）",
    "     ↳ 逐条差异：参考作是**整张图标条三态位图**（647×47/653×53）→ 我方逐键三态（同 M37 路线，已登记）",
    "     ↳ 字形差异：参考作 `1`/`ALL`/`RND` 是烘焙拉丁字 → 我方改纯图形（禁文字烘焙）",
    "48-50 Sound/ボタン/pause/{オフ,オンマウス,オン} → **已出件未接线**：`x_ui_bgm_pb_pause_*`（播放/暂停互换态，运行时状态，无机制承接）",
    "51-53 Sound/ボタン/play/{オフ,オンマウス,オン}（visible=0） → **不适用**：参考作该组默认隐藏、是 pause 的互换对侧；我方 `playpause` 键已含 ▶ 字形",
    "54-56 Sound/ボタン/{オフ,オンマウス,オン}（图标条） → **有意不同**：整条位图 → 逐键出件（同上）",
    "57 Sound/volume/#rect (769,907,382,29)  → **一致**：音量滑块拖动热区（我方 714,898,496,38，含轨道+手柄）",
    "58 Sound/volume/オン (945,907,29,29)    → **一致**：`handle.state_assets.hover`（`x_ui_bgm_knob_over.png`，带 ♪ 图形）",
    "59 Sound/volume/オフ (945,907,29,29)    → **一致**：`handle.state_assets.normal`（`x_ui_bgm_knob.png`，素圆）",
    "60 Sound/volume/バー (718,915,488,14)   → **一致**：`slider.rail`（`x_ui_bgm_rail.png` 488×14，1:1）",
    "61 Sound/#speana (781,966,359,48)       → **一致**：`mu.speana`（复用既有 `x_ui_speana.png` + nine；装饰，不接线）",
    "── 另加（参考作 BGM 页**无**、我方为两页必需）：翻页键 2 枚 + 页码文本（取 CG 页页码键几何 790/1074, y939, 56×56）",
    "── 另加（我方机制要求）：`list` 的 `highlight` 选中块（参考作的选中态是运行时绘制、容器内无对应件）",
]


if __name__ == "__main__":
    sys.exit(main())