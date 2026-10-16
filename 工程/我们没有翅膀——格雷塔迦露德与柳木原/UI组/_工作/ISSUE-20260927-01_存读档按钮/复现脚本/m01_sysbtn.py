# -*- coding: utf-8 -*-
r"""m01_sysbtn.py —— 存/读档屏右上「三系统按钮组」整体左移（ISSUE-20260927-01 · 模块 B）

用户指令（原话）：「存档/读档页右上角的三个按钮挡住页码了，把它们整体向左移」

口径（画布 1920×1080；两屏同款处理）
  · 目标：**沿 x 整体左移 190px**（Δx = −190），使**可见件组右沿 1880 → 1690**
    —— 页码徽章列自 x=1699 起（引擎绘 `sv.pgnum_01..10`），留 **9px** 间隙；
    hit 层右沿 1888 → 1698，仍不压徽章列 1699。
  · 位移基准 = 盘上实测旧值（`sv.sys_end` x1670 + w210 = 1880），不引用任何派单转述数字。
  · **只改 x**：三件各自的 w、彼此间距、顺序一律不变；`y`/`h`/`z`/`asset`/`font`/
    `action`/`vis_flag`/`vis_when` 与全部机制字段一律不动（含 `_hit` 与 `_tx`）。
  · `note` **只追加**本次口径（旧 note 一字不改），并带幂等标记。

幂等：盘上每个 x 断言 ∈ {旧, 新}；九件必须**同为旧或同为新**（半应用态直接报错退出）；
      全部已为新 ⇒ **只报不写**（退出码 0）。
落盘格式：`json.dumps(indent=1, ensure_ascii=False)` + CRLF + UTF-8 无 BOM
      —— 已实测与盘上原字节**逐字节相同**（改前自证见 m01_geom_check.py [0]）。

用法：
  python m01_sysbtn.py            # 应用（幂等）
  python m01_sysbtn.py --check     # 只读核查，不写盘
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
SCREENS = UI / "layout" / "screens"
FILES = ("23_save.json", "24_load.json")

DELTA = -190

# 九件（含 _tx / _hit）：id -> (旧 x, 新 x)
TARGETS = {
    "sv.sys_game":     (1062, 1062 + DELTA),
    "sv.sys_game_tx":  (1062, 1062 + DELTA),
    "sv.sys_game_hit": (1054, 1054 + DELTA),
    "sv.sys_title":     (1312, 1312 + DELTA),
    "sv.sys_title_tx":  (1312, 1312 + DELTA),
    "sv.sys_title_hit": (1304, 1304 + DELTA),
    "sv.sys_end":     (1670, 1670 + DELTA),
    "sv.sys_end_tx":  (1670, 1670 + DELTA),
    "sv.sys_end_hit": (1662, 1662 + DELTA),
}
ORDER = ["sv.sys_game", "sv.sys_game_tx", "sv.sys_game_hit",
         "sv.sys_title", "sv.sys_title_tx", "sv.sys_title_hit",
         "sv.sys_end", "sv.sys_end_tx", "sv.sys_end_hit"]

MARK = "★ **右上三系统按钮左移轮（2026-09-27 · ISSUE-20260927-01；依据＝用户实测反馈）**"
NOTE_ADD = (
    "\n\n" + MARK + "：上一轮（ISSUE-20260926-06）用「三件整体上移 22px（按钮/文字 y44→22、"
    "热区 y36→14）」把与数字盒的矩形相交压到 0，但**用户实机仍觉按钮「挡住页码」**（原话："
    "「存档/读档页右上角的三个按钮挡住页码了，把它们整体向左移」）⇒ 本轮改为**沿 x 整体左移 190px**：\n"
    "  · `sv.sys_game` / `_tx` / `_hit`：x **1062 / 1062 / 1054 → 872 / 872 / 864**\n"
    "  · `sv.sys_title` / `_tx` / `_hit`：x **1312 / 1312 / 1304 → 1122 / 1122 / 1114**\n"
    "  · `sv.sys_end` / `_tx` / `_hit`：x **1670 / 1670 / 1662 → 1480 / 1480 / 1472**\n"
    "  ⇒ **可见件组右沿 1880 → 1690**，与页码徽章列左沿 1699（引擎绘 `sv.pgnum_01..10`）留 "
    "**9px 间隙**；hit 层右沿 1888 → **1698**，仍不压徽章列 1699；与烘焙「/10」条带"
    "（x≈1763..1845、y≈80..140）横向上完全让开（原状 `sv.sys_end` 右沿 1880 与之同 x 段、"
    "仅 8px 纵向隔开）。\n"
    "  · **依据 = 用户实测反馈**（非推定）：改前可见件组横向 **1062..1880** 完整覆盖徽章列 "
    "**1699..1759**（重叠 **60px** 宽，仅 8px 纵向隔开）⇒ 用户判定为「挡住页码」；"
    "以「整组左移、右沿退到徽章列之前」为验收。\n"
    "  · **组内相对关系不变**：三件各自 w（210/318/210）、彼此间距（40px / 40px）、顺序"
    "（游戏→标题→结束）一律不变；`y`/`h`/`z`/`asset`/`font`/`action`/`vis_flag`/`vis_when`/"
    "机制字段**一律未动**（含 `_hit` 与 `_tx`）；未新增任何相交（可见件与 hit 层皆 0 对）。\n"
    "  · 两屏同款处理，改后两屏该组几何逐项相同。几何自证与逐字段 diff："
    "`_工作\\ISSUE-20260927-01_存读档按钮\\复现脚本\\m01_geom_check.py`；"
    "幂等脚本 `m01_sysbtn.py`；原形备份 `原形备份\\{23_save,24_load}.json`。"
)


def dump_bytes(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False).replace("\n", "\r\n").encode("utf-8")


def main():
    check_only = "--check" in sys.argv
    refix = "--refix-note" in sys.argv          # 只把本轮追加段替换为当前 NOTE_ADD（幂等、不改 x）
    rc = 0
    for fn in FILES:
        path = SCREENS / fn
        obj = json.loads(path.read_bytes().decode("utf-8"))
        idx = {e["id"]: e for e in obj["elements"]}

        missing = [i for i in ORDER if i not in idx]
        if missing:
            print("!! %s 缺件：%s" % (fn, missing))
            return 2

        states = set()
        for eid in ORDER:
            x = idx[eid]["x"]
            old, new = TARGETS[eid]
            if x == old:
                states.add("old")
            elif x == new:
                states.add("new")
            else:
                print("!! %s %s 的 x=%s 既非旧值 %s 也非新值 %s（半应用/被外部改动）"
                      % (fn, eid, x, old, new))
                return 2
        if len(states) != 1:
            print("!! %s 九件状态不一致：%s（半应用态，拒绝写盘）" % (fn, sorted(states)))
            return 2
        state = states.pop()

        if refix:
            note = obj.get("note", "")
            i = note.find(MARK)
            if i < 0:
                print("!! %s note 无本轮标记，--refix-note 不适用" % fn)
                return 2
            new_note = note[:i] + NOTE_ADD.lstrip("\n")
            if new_note == note:
                print("   %s note 已是当前口径，无需改写（幂等）✓" % fn)
            else:
                obj["note"] = new_note
                path.write_bytes(dump_bytes(obj))
                print("   %s note 追加段已替换为当前口径（%d → %d 字）" % (fn, len(note), len(new_note)))
            continue

        print("-" * 92)
        print("%s  状态 = %s" % (fn, "已应用（新值）" if state == "new" else "未应用（旧值）"))
        for eid in ORDER:
            old, new = TARGETS[eid]
            print("   %-18s x %5d → %5d  (w=%3d)" % (eid, old, new, idx[eid]["w"]))

        if state == "new":
            print("   ⇒ 已应用：只报不写 ✓（幂等）")
            if MARK not in obj.get("note", ""):
                print("   !! 但 note 缺本轮标记 —— 请人工核查")
                rc = 1
            continue

        if check_only:
            print("   --check：不写盘")
            continue

        # ---- 应用 ----
        for eid in ORDER:
            idx[eid]["x"] = TARGETS[eid][1]
        if MARK not in obj.get("note", ""):
            obj["note"] = obj["note"].rstrip("\r\n") + NOTE_ADD
            print("   note：已追加本轮口径（%d 字）" % len(NOTE_ADD))
        else:
            print("   note：本轮标记已存在，跳过追加")

        out = dump_bytes(obj)
        path.write_bytes(out)
        print("   已写入 %s（%d 字节）" % (path, len(out)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
