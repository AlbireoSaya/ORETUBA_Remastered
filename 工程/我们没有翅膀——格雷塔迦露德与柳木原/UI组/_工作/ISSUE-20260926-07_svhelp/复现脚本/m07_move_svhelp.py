# -*- coding: utf-8 -*-
r"""m07 · 存/读档屏「说明条 `sv.help` + 编辑键条」整簇上移量 122px → 60px
（`ISSUE-20260926-07`，屏 `23_save` / `24_load`，11 件/屏 × 2 屏 = 22 处）

背景（主代理已核实）：
  · 上一轮（`ISSUE-20260926-06` 页脚落地轮）**只动编辑键条**：`sv.edit` y970→848、
    `sv.del|mod|mov|cpy` 的 `_tx`/`hit` y964→842 ⇒ 让出烘焙中文页脚带（实测墨迹 y982..1030）。
    S=122 是「只动编辑键条」时的碰撞下界 +4px（正上方 `sv.help` y907..952 把小幅上移堵死：
    编辑键 hit 盒高 61 ⇒ 底边须 ≤ 907）。
  · 但 PSV 原版（《交汇协奏曲》PSB idx82）**说明条（y907）在编辑条（y970）之上**；
    上移 122 之后本屏变成「编辑条在上、说明条在下」，**与 PSV 原版顺序相反**。
  · **用户 2026-09-26 裁决**：①「调整 `sv.help` 至合适的位置」；② 采纳 **S=60** 方案（编辑键条更贴页脚）。

本次改动（**唯一目标**）：整簇上移量 122px → 60px ＝ 编辑键条**当前 y 再下移 62px**、说明条**上移 60px**：
    sv.edit                 848 → 910
    sv.del_tx / sv.del      842 → 904
    sv.mod_tx / sv.mod      842 → 904
    sv.mov_tx / sv.mov      842 → 904
    sv.cpy_tx / sv.cpy      842 → 904
    sv.help / sv.help_tx    907 → 847
  **只改 `y`**；`x`/`w`/`h`/`z`/`asset`/`action`/`font`/`vis_flag`/`vis_when`/机制字段一律不得改
  （脚本逐字段断言）；11 件的 `note` 追加新口径，屏级 `note` 追加「说明条回调轮」段。

脚本内断言（全部硬失败）：
  ① 仅 `y`（与追加的 `note`）变化，其余字段逐字未变；
  ② 与烘焙页脚带墨迹（**底图现场实测**顶行 + 派单口径 y982）交叠面积 = 0 且间距 ≥ 15px；
  ③ 与屏内**其余全部元素**（整屏底图/遮罩除外）矩形相交面积 = 0；
  ④ 两屏 11 件几何逐项相同；⑤ PSB 原版相对顺序恢复（说明条在编辑条之上）。
  ⑥ 幂等：已应用则只报告、不重写。

用法：python m07_move_svhelp.py --dry    # 只算不写
      python m07_move_svhelp.py          # 落盘（原形首份备份保留在 `原形备份\`，不覆盖）
"""
import sys, os, json, shutil
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SCR = os.path.join(BASE, "layout", "screens")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-07_svhelp")
BAK = os.path.join(WORK, "原形备份")
BG = os.path.join(BASE, "krkr", "assets", "ui", "x_ui_psv_save_bg.png")

TARGETS = {
    "sv.edit": (848, 910),
    "sv.del_tx": (842, 904), "sv.del": (842, 904),
    "sv.mod_tx": (842, 904), "sv.mod": (842, 904),
    "sv.mov_tx": (842, 904), "sv.mov": (842, 904),
    "sv.cpy_tx": (842, 904), "sv.cpy": (842, 904),
    "sv.help": (907, 847), "sv.help_tx": (907, 847),
}
EDIT_IDS = ["sv.edit", "sv.del_tx", "sv.del", "sv.mod_tx", "sv.mod",
            "sv.mov_tx", "sv.mov", "sv.cpy_tx", "sv.cpy"]
CLUSTER = EDIT_IDS + ["sv.help", "sv.help_tx"]
FOOTER_INK_MIN_GAP = 15
FOOTER_BAND_TOP_SPEC = 982
NOTE_KEY = ("　★ 2026-09-26（ISSUE-20260926-07）用户裁决：上移量由 122px 回调为 60px"
            "（编辑键条更贴页脚）；sv.help 相应上移 60px，回到 PSB 原版的相对顺序"
            "（说明条在编辑条之上）。")
NOTE_APPEND_EDIT = NOTE_KEY + ("本件相对 ISSUE-20260926-06 落地态**下移 62px**（y %d→%d，整簇上移量 122→60）。")
NOTE_APPEND_HELP = NOTE_KEY + ("本件即 `sv.help`，随簇**上移 60px**（y %d→%d）；编辑键条相对上一轮"
                               "落地态下移 62px（S 122→60、更贴页脚）。")
SCREEN_NOTE = (r"\n★ **说明条回调轮（2026-09-26 · ISSUE-20260926-07；用户裁决「调整 sv.help 至合适的位置」"
               r"+ 采纳 S=60）**：上一轮「只动编辑键条」的 S=122 使本屏变成「编辑条在上、说明条在下」，"
               r"与 PSV 原版（《交汇协奏曲》PSB idx82：说明条 y907 在编辑条 y970 之上）**顺序相反**。"
               r"本轮把**说明条 + 编辑键条整簇**的上移量由 122px 回调为 60px：`sv.edit` y848→910、"
               r"`sv.del|mod|mov|cpy`（含 `_tx`）y842→904（即相对上一轮落地态**下移 62px**、更贴页脚），"
               r"`sv.help`/`sv.help_tx` y907→847（**上移 60px**）⇒ 恢复 PSB 原版相对顺序（说明条在编辑条之上）。"
               r"簇最低边 y965 距烘焙页脚带墨迹（底图实测顶 y983）**17px**（≥ 派单阈值 15px）；"
               r"与屏内其余元素矩形相交 = 0；`x`/`w`/`h`/`z`/`asset`/`action`/`font`/`vis_flag`/`vis_when` "
               r"与全部机制字段未改。几何自证与取证：`_工作\ISSUE-20260926-07_svhelp\`（`复现脚本\m07_geom_check.py`）。")


def rect(e):
    return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])


def inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def measure_ink_top():
    a = np.asarray(Image.open(BG).convert("RGB")).astype(np.int16)
    sub = a[940:1080, 1200:1740]
    dev = np.abs(sub - np.median(sub, axis=1, keepdims=True)).max(axis=2)
    cnt = (dev > 25).sum(axis=1)
    for i, c in enumerate(cnt):
        if c > 0:
            return 940 + i
    return None


def load_raw(p):
    """按盘上原样读（`newline=''` 保留 CRLF）。"""
    return open(p, encoding="utf-8", newline="").read()


def dump_raw(d):
    """盘上实际格式（实测）：`json.dumps(indent=1)` 的 `\\n` → `\\r\\n`，**无文件尾换行**。
    本函数保证「除本次应改的行外，其余字节与改动前逐字相同」。"""
    return json.dumps(d, ensure_ascii=False, indent=1).replace("\n", "\r\n")


def main():
    dry = "--dry" in sys.argv
    ink_top = measure_ink_top()
    print("底图实测页脚带墨迹顶 = y%d（派单口径 y%d）" % (ink_top, FOOTER_BAND_TOP_SPEC))
    geoms = {}
    for fn in ("23_save.json", "24_load.json"):
        p = os.path.join(SCR, fn)
        raw = load_raw(p)
        d = json.loads(raw)
        assert raw == dump_raw(d), "%s 格式与本脚本写出格式不符（应为 CRLF + indent=1 + 无尾换行）" % fn
        idx = {e["id"]: e for e in d["elements"]}
        for eid in CLUSTER:
            assert eid in idx, "%s 缺元素 %s" % (fn, eid)

        cur = {eid: idx[eid]["y"] for eid in CLUSTER}
        if all(cur[eid] == TARGETS[eid][1] for eid in CLUSTER):
            print("=" * 108)
            print("%s：**已应用**（22 处 y 全在目标值）⇒ 不重写（幂等）" % fn)
            geoms[fn] = [(eid, TARGETS[eid][1]) for eid in CLUSTER]
            continue
        # 目标态只可能是「未动（旧值 122 态）」或「已应用」，其余一律拒绝（防二次平移）
        for eid in CLUSTER:
            assert cur[eid] == TARGETS[eid][0], \
                "%s 的 %s y=%d 既非旧值 %d 也非目标 %d ⇒ 拒绝执行" % (
                    fn, eid, cur[eid], TARGETS[eid][0], TARGETS[eid][1])

        pre = {e["id"]: dict(e) for e in d["elements"]}
        print("=" * 108)
        print("%s · 说明条 + 编辑键条整簇：上移量 122px → 60px" % fn)
        for eid in CLUSTER:
            e = idx[eid]
            y0, y1 = TARGETS[eid]
            e["y"] = y1
            if eid in EDIT_IDS:
                e["note"] = e.get("note", "") + (NOTE_APPEND_EDIT % (y0, y1))
            else:
                e["note"] = e.get("note", "") + (NOTE_APPEND_HELP % (y0, y1))
            assert NOTE_KEY in e["note"]
            print("   %-11s y %4d → %4d  (%+d)  rect=(%d,%d,%d,%d)"
                  % (eid, y0, y1, y1 - y0, *rect(e)))

        # ---- 自证 ①：除 y / note 外逐字段未变 ----
        for eid in CLUSTER:
            for k, v in pre[eid].items():
                if k in ("y", "note"):
                    continue
                assert idx[eid][k] == v, "!! %s 的字段 %s 被改动" % (eid, k)
            for k in ("x", "w", "h", "z", "kind", "asset", "action", "font",
                      "vis_flag", "vis_when", "nine", "source", "opacity", "label", "sample"):
                if k in pre[eid]:
                    assert idx[eid][k] == pre[eid][k], "!! %s 的机制/几何字段 %s 被改动" % (eid, k)
        print("   自证①：仅 y（+ 追加 note）变化；x/w/h/z/kind/asset/action/font/vis_flag/vis_when/"
              "nine/source/opacity 逐字未变 ✓")

        # ---- 自证 ②：与页脚带 ----
        for eid in CLUSTER:
            r = rect(idx[eid])
            for top in (ink_top, FOOTER_BAND_TOP_SPEC):
                ov = max(0, r[3] - max(r[1], top)) * (r[2] - r[0])
                assert ov == 0, "!! %s 与 y≥%d 带交叠 %d px²" % (eid, top, ov)
        lowest = max(rect(idx[eid])[3] for eid in CLUSTER)
        assert ink_top - lowest >= FOOTER_INK_MIN_GAP, \
            "!! 簇最低边 y%d 距实测墨迹顶 %dpx < %dpx" % (lowest, ink_top - lowest, FOOTER_INK_MIN_GAP)
        assert FOOTER_BAND_TOP_SPEC - lowest >= FOOTER_INK_MIN_GAP, "!! 派单口径间距不足"
        print("   自证②：簇最低边 y%d 距实测墨迹顶 y%d = **%dpx** ／ 距口径 y%d = %dpx（≥ %dpx）；"
              "∩{y≥%d} = 0 ✓" % (lowest, ink_top, ink_top - lowest, FOOTER_BAND_TOP_SPEC,
                                 FOOTER_BAND_TOP_SPEC - lowest, FOOTER_INK_MIN_GAP, ink_top))

        # ---- 自证 ③：与其余全部元素零相交 ----
        canvas = [e["id"] for e in d["elements"] if e["w"] * e["h"] >= 1920 * 1080]
        bad = []
        for eid in CLUSTER:
            a = rect(idx[eid])
            for e in d["elements"]:
                if e["id"] in CLUSTER or e["id"] in canvas:
                    continue
                n = inter(a, rect(e))
                if n > 0:
                    bad.append((eid, e["id"], n))
        assert not bad, "!! 与其余元素相交：%s" % bad
        print("   自证③：11 件 × 屏内其余 %d 件元素（整屏件 %s 除外）= 0 相交对 ✓"
              % (len(d["elements"]) - len(CLUSTER) - len(canvas), canvas))

        # ---- 自证 ⑤：相对顺序 ----
        hb, ht = rect(idx["sv.help"])[1], rect(idx["sv.help"])[3]
        eb = rect(idx["sv.edit"])[1]
        assert ht <= eb, "!! 说明条未回到编辑条之上（%d..%d vs %d）" % (hb, ht, eb)
        print("   自证⑤：sv.help %d..%d 在 sv.edit %d..%d **之上** ⇒ PSB 原版相对顺序恢复 ✓" % (hb, ht, eb, rect(idx["sv.edit"])[3]))

        d["note"] = d["note"] + SCREEN_NOTE
        out = dump_raw(d)
        if not dry:
            bp = os.path.join(BAK, fn)
            if not os.path.exists(bp):            # 首份（真正的改动前）快照一旦存在就绝不覆盖
                shutil.copyfile(p, bp)
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(out)
            print("   已写盘 %s（%d → %d 字符）" % (p, len(raw), len(out)))
        else:
            print("   (dry-run，未写盘)")
        geoms[fn] = [(eid, idx[eid]["y"]) for eid in CLUSTER]

    # ---- 自证 ④：两屏几何逐项相同 ----
    a, b = geoms["23_save.json"], geoms["24_load.json"]
    assert a == b, "!! 两屏几何不一致：%s vs %s" % (a, b)
    print("=" * 108)
    print("自证④：23_save / 24_load 的 11 件几何逐项相同 ✓")
    # 簇最低边（现盘回读，不靠硬编码高度）
    dchk = json.loads(load_raw(os.path.join(SCR, "23_save.json")))
    ichk = {e["id"]: e for e in dchk["elements"]}
    low = max(rect(ichk[e])[3] for e in CLUSTER)
    if not dry:
        print("\nALL PASS ✓ —— 22 处 y 已就位；两屏簇最低边 y%d，距底图实测页脚带墨迹顶 y%d = %dpx"
              % (low, measure_ink_top(), measure_ink_top() - low))
    else:
        print("\nDRY PASS ✓ —— 22 处 y 将写为：%s" % ", ".join("%s=%d" % (e, TARGETS[e][1]) for e in CLUSTER))


if __name__ == "__main__":
    main()
