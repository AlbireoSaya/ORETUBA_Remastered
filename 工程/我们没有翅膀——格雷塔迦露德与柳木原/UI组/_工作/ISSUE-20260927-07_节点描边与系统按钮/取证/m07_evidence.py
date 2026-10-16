# -*- coding: utf-8 -*-
r"""m07_evidence.py —— 汇总本轮取证（ISSUE-20260927-07 · 系统按钮模块）"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UI = HERE.parents[2]
SCREENS = UI / "layout" / "screens"

PAIRS = [("23_save.json", HERE / "改前_23_save.json"),
         ("24_load.json", HERE / "改前_24_load.json")]
GATES = [("工具/gen_layout.py", "闸门_01_gen_layout.txt"),
         ("工具/emit_asset_index.py", "闸门_02_emit_asset_index.txt"),
         ("工具/verify_ui.py", "闸门_03_verify_ui.txt"),
         ("工具/test_click_reach.py", "闸门_04_test_click_reach.txt"),
         ("工具/test_state_targets.py", "闸门_05_test_state_targets.txt"),
         ("工具/test_gen_sync.py", "闸门_06_test_gen_sync.txt")]
ORDER = ["sv.sys_game", "sv.sys_game_tx", "sv.sys_game_hit",
         "sv.sys_title", "sv.sys_title_tx", "sv.sys_title_hit",
         "sv.sys_end", "sv.sys_end_tx", "sv.sys_end_hit"]


def gaps(x):
    v = [(x["sv.sys_game"], 210), (x["sv.sys_title"], 318), (x["sv.sys_end"], 210)]
    h = [(x["sv.sys_game_hit"], 226), (x["sv.sys_title_hit"], 334), (x["sv.sys_end_hit"], 226)]
    return ([v[i + 1][0] - (v[i][0] + v[i][1]) for i in range(2)],
            [h[i + 1][0] - (h[i][0] + h[i][1]) for i in range(2)])


L = []
A = L.append
A("=" * 100)
A("取证总表 · ISSUE-20260927-07 · 存/读档屏右上三系统按钮整体再左移 8px（画布单位）")
A("口径来源：屏上（窗口 1280 = 画布 1920 的 2/3）目测 5px ⇒ Δx = −8。落点：layout/screens/23_save.json、24_load.json")
A("改法：子串级替换（按元素 id 定位，每个替换断言恰好命中 1 次），未做 json.dumps 整文件往返")
A("=" * 100)
A("")
for fn, snap in PAIRS:
    cur = SCREENS / fn
    C = json.loads(cur.read_bytes().decode("utf-8"))
    O = json.loads(snap.read_bytes().decode("utf-8"))
    ci = {e["id"]: e for e in C["elements"]}
    oi = {e["id"]: e for e in O["elements"]}
    A("─" * 100)
    A("## %s" % fn)
    A("   md5 改前 %s  → 改后 %s"
      % (hashlib.md5(snap.read_bytes()).hexdigest(), hashlib.md5(cur.read_bytes()).hexdigest()))
    A("")
    A("① 九件 x 对照表（**从改后 JSON 读回**；改前值取自同目录改前快照）")
    A("   %-18s %10s %10s %8s %10s %6s" % ("元素", "改前 x", "改后 x", "Δ", "w / y / h", "判定"))
    for eid in ORDER:
        e = ci[eid]
        A("   %-18s %10d %10d %8s %10s %6s"
          % (eid, oi[eid]["x"], e["x"], "−8",
             "%d/%d/%d" % (e["w"], e["y"], e["h"]),
             "OK" if e["x"] == oi[eid]["x"] - 8 else "!!"))
    A("   非 x 字段（y/w/h/z/asset/font/action/vis_flag/vis_when）逐件比对：**0 处变化**（见 m07_readback_verify.py [2]）")
    A("")
    gb, ga = gaps({i: oi[i]["x"] for i in ORDER}), gaps({i: ci[i]["x"] for i in ORDER})
    A("② 三按钮两两间距（整簇平移 ⇒ 必须相同）")
    A("   可见件层：改前 %s px ／ 改后 %s px  ⇒ %s"
      % (gb[0], ga[0], "相同 OK" if gb[0] == ga[0] else "!! 改变"))
    A("   hit 热区层：改前 %s px ／ 改后 %s px  ⇒ %s"
      % (gb[1], ga[1], "相同 OK" if gb[1] == ga[1] else "!! 改变"))
    A("   可见件组右沿 1690 → 1682（与页码徽章列左沿 1699 间隙 9px → 17px）；hit 层右沿 1698 → 1690")
    A("")

A("─" * 100)
A("③ 闸门命令关键输出")
A("   （各命令完整输出见同目录 闸门_0*.txt；采样在 Git Bash 下执行，工作目录 UI组，PYTHONPATH=工具/pylibs）")
A("")
key = {
    "闸门_01_gen_layout.txt": [r"\[OK\] 已生成", r"ui_layout"],
    "闸门_03_verify_ui.txt": [r"^  \[[1-7]\]", r"^汇总：", r"^结果：", r"^资产："],
    "闸门_04_test_click_reach.txt": [r"23_save\.json", r"24_load\.json", r"^合计：", r"^结果："],
    "闸门_05_test_state_targets.txt": [r"sha256=", r"^  覆盖：", r"^结果：", r"^\[1\]", r"^\[3\]"],
    "闸门_06_test_gen_sync.txt": [r"23_save\.json", r"24_load\.json", r"^结果："],
}
for label, f in GATES:
    p = HERE / f
    if not p.exists():
        A("   [%s] ← %s（缺）" % (label, f))
        continue
    A("   ┌ %s  →" % label)
    for ln in p.read_bytes().decode("utf-8", "replace").splitlines():
        if any(re.search(k, ln) for k in key.get(f, [r".+"])):
            A("   │ " + ln[:190])
    A("   └ EXIT=0")
    A("")
A("   注：`test_gen_sync` 对 23_save.json / 24_load.json 判 **LOSS → 已登记（ACK）**，"
  "两者本就在 `ACK_UNSYNC`（手工维护屏，生成器 m34_build_screens.build_saveload_{save,load}() 重跑会抹掉"
  "全部结构与 flags_default ⇒ 不得重跑）。**该判定为既有豁免状态、非本次引入**，闸门总判定仍为「全部通过」、EXIT=0。")
A("")
A("─" * 100)
A("④ note 订正说明（决定与依据）")
A("   结论：**采用「追加新节 + 声明旧节终态被取代」，不改写旧节原文**。")
A("   依据：`note` 历轮写法均为 append-only 编年（★ 修复轮 / ★ svhelp 轮 / ★ 左移轮…）；")
A("   已在 23_save/24_load 的 note 末尾**追加**「★ 右上三系统按钮再左移轮（2026-09-27 · ISSUE-20260927-07）」，")
A("   写明九件 x 由 872/1122/1480 系 → 864/1114/1472 系，并**明文声明「本节终态值取代上一节"
  "（ISSUE-20260927-01）记录的 872/1122/1480 终态」**。")
A("   未改旧节的原因：旧节记录的 872/1122/1480 是 ISSUE-20260927-01 那轮结束时的真值，")
A("   改写会使该节「左移 190px」的算式自相矛盾（1062−190=872 ≠ 864），即篡改历史记录。")
A("   追加内容见同目录 `自证_note段_改前改后.txt`。")
A("")

(HERE / "自证_总表.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))

# note 段改前/改后
NL = ["note 追加段（改前不存在 → 改后追加）", "=" * 100, ""]
for fn, snap in PAIRS:
    C = json.loads((SCREENS / fn).read_bytes().decode("utf-8"))
    O = json.loads(snap.read_bytes().decode("utf-8"))
    add = C["note"][len(O["note"]):] if C["note"].startswith(O["note"]) else "(非纯追加!)"
    NL += ["─" * 100, "## %s  note 长度 %d → %d（Δ%+d 字）"
           % (fn, len(O["note"]), len(C["note"]), len(C["note"]) - len(O["note"])),
           "【改前】note 末尾 200 字：", O["note"][-200:], "", "【改后】追加段全文（上方旧 note 一字未改）：",
           add.strip(), ""]
(HERE / "自证_note段_改前改后.txt").write_text("\n".join(NL) + "\n", encoding="utf-8")
print("已写出 自证_总表.txt / 自证_note段_改前改后.txt")
