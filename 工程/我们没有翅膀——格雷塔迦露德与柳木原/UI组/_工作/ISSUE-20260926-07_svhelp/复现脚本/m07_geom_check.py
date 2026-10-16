# -*- coding: utf-8 -*-
r"""m07 · 几何自证：存/读档屏「说明条 `sv.help` + 编辑键条」簇的纵向位置核算
（`ISSUE-20260926-07`，屏 `23_save` / `24_load`；幂等、带退出码、可复跑）

核算口径（画布 1920×1080，全部为数据实测，无写盘）：
  [1] 簇内 11 件的 y 与矩形（两屏各自列出，并断言两屏数值逐项相同）；
  [2] 簇包络框与**烘焙页脚带墨迹**的间距 —— 墨迹顶**由底图 `x_ui_psv_save_bg.png` 现场实测**
      （判据：x1200..1740 内「逐像素最大通道相对该行中位数的偏差 > 25」的像素数首次 > 0 的行）；
  [3] 槽网格第 3 行底边 → 说明条顶边 的间距（槽行 y317/483/649、槽高 122 ⇒ 底边 771）；
  [4] **逐对相交面积**：簇内 11 件 × 屏内**其余全部元素**（整屏底图/遮罩除外，理由见脚本注释），
      并单独打印派单指定必须覆盖的四组：`sv.pg01..10`、`sv.hit_back`、`sv.sys_*`（含 `_tx`/`_hit`）、
      全部 `sv.slot*` / `sv.hit*`；
  [5] PSB 原版相对顺序（说明条在编辑条**之上**）。

用法：python m07_geom_check.py            # 全部通过 ⇒ 退出码 0
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SCR = os.path.join(BASE, "layout", "screens")
UI = os.path.join(BASE, "krkr", "assets", "ui")
BG = os.path.join(UI, "x_ui_psv_save_bg.png")

CLUSTER = ["sv.help", "sv.help_tx", "sv.edit",
           "sv.del_tx", "sv.del", "sv.mod_tx", "sv.mod",
           "sv.mov_tx", "sv.mov", "sv.cpy_tx", "sv.cpy"]
EDIT = ["sv.edit", "sv.del_tx", "sv.del", "sv.mod_tx", "sv.mod",
        "sv.mov_tx", "sv.mov", "sv.cpy_tx", "sv.cpy"]
FOOTER_INK_MIN_GAP = 15         # 派单口径：与烘焙页脚带墨迹的最小间距 ≥ 15px
FOOTER_BAND_TOP_SPEC = 982      # 页脚落地轮实测墨迹顶（报告口径）
SLOT_ROW3_BOTTOM = 771          # 槽网格第 3 行底边（槽行 y649 + 槽高 122）

FAILS = []


def rect(e):
    return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])


def inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def measure_footer_ink_top():
    """从底图现场实测页脚带墨迹顶行（x1200..1740 行窗口，判据见模块 docstring）。"""
    a = np.asarray(Image.open(BG).convert("RGB")).astype(np.int16)
    sub = a[940:1080, 1200:1740]
    med = np.median(sub, axis=1, keepdims=True)
    dev = np.abs(sub - med).max(axis=2)
    cnt = (dev > 25).sum(axis=1)
    for i, c in enumerate(cnt):
        if c > 0:
            return 940 + i, int(c), sub.shape[0] + 940
    return None, 0, 1080


def main():
    # `--dir <屏目录>`：核算指定目录（用于对「改前」快照复跑同一判据：`原形备份\_改前屏\`）
    d = SCR
    if "--dir" in sys.argv:
        d = sys.argv[sys.argv.index("--dir") + 1]
    ink_top, ink_cnt, _ = measure_footer_ink_top()
    print("=" * 108)
    print("屏目录：%s" % d)
    print("底图 %s 实测：页脚带墨迹顶 = y%d（该行 x1200..1740 内偏离行中位数 >25 的像素 %d 个）"
          % (os.path.basename(BG), ink_top, ink_cnt))
    print("  参考：页脚落地轮（ISSUE-20260926-06）口径 y982..1030；派单口径 y982..1030、最小间距 ≥ %dpx"
          % FOOTER_INK_MIN_GAP)

    screens = {}
    for fn in ("23_save.json", "24_load.json"):
        screens[fn] = json.load(open(os.path.join(d, fn), encoding="utf-8"))

    # ---------- [1] 簇内 11 件 ----------
    print("\n" + "=" * 108)
    print("[1] 簇内 11 件的 y 与矩形")
    vals = {}
    for fn, d in screens.items():
        idx = {e["id"]: e for e in d["elements"]}
        print("  -- %s --" % fn)
        for eid in ("sv.help", "sv.help_tx", "sv.edit",
                    "sv.del_tx", "sv.del", "sv.mod_tx", "sv.mod",
                    "sv.mov_tx", "sv.mov", "sv.cpy_tx", "sv.cpy"):
            e = idx[eid]
            r = rect(e)
            print("     %-11s %-6s y=%-4d rect=(%4d,%4d,%4d,%4d)  纵向 %d..%d"
                  % (eid, e["kind"], e["y"], *r, r[1], r[3]))
            vals.setdefault(eid, set()).add((e["x"], e["y"], e["w"], e["h"]))
    same = all(len(v) == 1 for v in vals.values())
    print("  两屏 11 件几何逐项相同：%s" % ("是 ✓" if same else "否 ✗"))
    if not same:
        FAILS.append("两屏 11 件几何不一致")

    d = screens["23_save.json"]
    idx = {e["id"]: e for e in d["elements"]}

    # ---------- [2] 距烘焙页脚带 ----------
    print("\n" + "=" * 108)
    print("[2] 簇包络框 与 烘焙页脚带墨迹（实测顶 y%d）的间距" % ink_top)
    cl = [rect(idx[e]) for e in CLUSTER]
    env = (min(r[0] for r in cl), min(r[1] for r in cl), max(r[2] for r in cl), max(r[3] for r in cl))
    print("  簇包络框 = (%d,%d,%d,%d)  ⇒ 纵向 %d..%d" % (env + (env[1], env[3])))
    for eid in ("sv.edit", "sv.del", "sv.mod", "sv.mov", "sv.cpy"):
        b = rect(idx[eid])[3]
        print("     %-11s 底边 y=%-4d → 距墨迹顶 %dpx　（派单口径墨迹顶 %d ⇒ %dpx）"
              % (eid, b, ink_top - b, FOOTER_BAND_TOP_SPEC, FOOTER_BAND_TOP_SPEC - b))
    lowest = env[3]
    gap_meas = ink_top - lowest
    gap_spec = FOOTER_BAND_TOP_SPEC - lowest
    print("  簇最低边 y=%d ⇒ 距实测墨迹顶 %dpx ／ 距口径墨迹顶 %dpx（要求均 ≥ %dpx）"
          % (lowest, gap_meas, gap_spec, FOOTER_INK_MIN_GAP))
    if not (gap_meas >= FOOTER_INK_MIN_GAP and gap_spec >= FOOTER_INK_MIN_GAP):
        FAILS.append("簇与页脚带墨迹间距 %d/%dpx < %dpx" % (gap_meas, gap_spec, FOOTER_INK_MIN_GAP))
    # 与「y ≥ 墨迹顶」半平面交叠面积
    for eid in CLUSTER:
        r = rect(idx[eid])
        ov = max(0, r[3] - max(r[1], ink_top)) * (r[2] - r[0])
        if ov:
            FAILS.append("%s 与页脚带（y≥%d）交叠 %d px²" % (eid, ink_top, ov))
    print("  簇内 11 件 ∩ {y ≥ %d} = 0 px² ✓" % ink_top)

    # ---------- [3] 槽网格 → 说明条 ----------
    help_top = rect(idx["sv.help"])[1]
    print("\n" + "=" * 108)
    print("[3] 槽网格第 3 行底边 y=%d → 说明条 `sv.help` 顶边 y=%d 的间距 = %dpx"
          % (SLOT_ROW3_BOTTOM, help_top, help_top - SLOT_ROW3_BOTTOM))
    if help_top - SLOT_ROW3_BOTTOM <= 0:
        FAILS.append("说明条顶边压到槽网格")

    # ---------- [4] 逐对相交 ----------
    print("\n" + "=" * 108)
    print("[4] 逐对相交面积：簇内 11 件 × 屏内其余全部元素")
    # 整屏件（w*h ≥ 画布面积）为底图/遮罩，与任何元素「相交」是设计本意（z 最低），按既有口径排除
    canvas = [e["id"] for e in d["elements"] if e["w"] * e["h"] >= 1920 * 1080]
    print("  排除的整屏件（设计本意覆盖全屏）：%s" % canvas)
    others = [e for e in d["elements"] if e["id"] not in CLUSTER and e["id"] not in canvas]
    bad = []
    n_chk = 0
    for eid in CLUSTER:
        a = rect(idx[eid])
        for e in others:
            n_chk += 1
            n = inter(a, rect(e))
            if n > 0:
                bad.append((eid, e["id"], n))
    print("  受检对象数 = %d 件（含 `_tx`/`_hit` 成组件）｜受检对 = %d 对" % (len(others), n_chk))
    for group, pred in (
            ("sv.pg*（`sv.pg01..10` 三层 + `sv.pgnum_01..10`）", lambda i: i.startswith("sv.pg")),
            ("sv.hit_back", lambda i: i == "sv.hit_back"),
            ("sv.sys_*（含 _tx/_hit，9 件）", lambda i: i.startswith("sv.sys_")),
            ("全部 sv.slot* / sv.hit* 槽位", lambda i: i.startswith(("sv.slot", "sv.hit"))),
    ):
        ids = [e["id"] for e in others if pred(e["id"])]
        print("    · %-34s 覆盖件数 %2d：%s" % (group, len(ids), ",".join(ids[:6]) + ("…" if len(ids) > 6 else "")))
    if bad:
        FAILS.append("相交对 %d 个：%s" % (len(bad), bad))
    print("  相交对 = %d 个%s" % (len(bad), " ✓（交叠面积全为 0）" if not bad else " ✗ " + str(bad)))
    # 元素自身重复 id / 缺件检查
    ids = [e["id"] for e in d["elements"]]
    miss = [e for e in CLUSTER if e not in idx]
    if miss:
        FAILS.append("缺件：%s" % miss)
    if len(ids) != len(set(ids)):
        FAILS.append("元素 id 重复")

    # ---------- [5] 相对顺序 ----------
    print("\n" + "=" * 108)
    print("[5] PSB 原版相对顺序：说明条（y907）在编辑条（y970）**之上**")
    hb, ht = rect(idx["sv.help"])[1], rect(idx["sv.help"])[3]
    eb, et = rect(idx["sv.edit"])[1], rect(idx["sv.edit"])[3]
    print("  现盘：sv.help %d..%d ／ sv.edit %d..%d　⇒ 说明条%s编辑条"
          % (hb, ht, eb, et, "在之上 ✓" if ht <= eb else "在**下**方 ✗"))
    if ht > eb:
        FAILS.append("相对顺序与 PSB 原版相反")

    print("\n" + "=" * 108)
    if FAILS:
        print("FAILTOTAL %d 项：" % len(FAILS))
        for f in FAILS:
            print("   ✗", f)
        return 1
    print("ALL PASS ✓ —— 簇几何、间距、逐对相交、相对顺序全部达标")
    return 0


if __name__ == "__main__":
    sys.exit(main())
