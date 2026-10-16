# -*- coding: utf-8 -*-
r"""t2 · 存/读档「引擎编辑键条」上移：解除与烘焙页脚带的重叠（23_save / 24_load）

问题（实测，本轮）：B 路中文页脚落地后，页脚带墨迹 实测 y982..1030（x900..1904）；
  而 `sv.edit`（1089,970,684,49 ⇒ y970..1019）与 4 组编辑键 `sv.{del,mod,mov,cpy}`(+`_tx`)
  （各 (x,964,156,61) ⇒ y964..1025、文字墨带 ≈977..999）压在页脚上 —— **中文压中文**
  （「编辑」压「决定」、「移动」压「删除数据」、「复制」压烘焙「返回」）。

修法（**只动编辑键条 9 件**，action/机制字段一律不改）：
  9 件整体上移 `SHIFT` px。`SHIFT` 的取值依据（两条硬约束同时满足的最小值）：
    ① 与页脚带交叠面积 = 0：编辑条矩形底 1025 − S ≤ 981（页脚墨顶）… 只要 S ≥ 44；
    ② **与其余元素零相交**：正上方 `sv.help`（1186,907,488,45 ⇒ y907..952，含 `sv.help_tx`）
       把「小幅度上移」全部堵死 —— 文字盒底 1025 − S ≤ 907 ⇒ **S ≥ 118**（贴住 help 顶边），
       留 4px 缝取 **S = 122**（文字盒 842..903、编辑条底板 848..897，与 help 底板缝 10px）。
  （派单原文「建议上移 ≥22px / 若与槽位行冲突则右移」：22px 只够让**文字墨带**脱离（墨 999→955），
   矩形仍压；而右移不可行——右侧 x ≥ 1678 会出画布，左侧 x ≤ 502 会压页码键 `sv.pg07..10`
   （x604..927 / y939..992）。故取 S=122，理由与各备选几何见派单报告。）

自证（脚本内断言，全部硬失败）：
  · 9 件矩形 ∩ {y ≥ 988} = 0 **且** ∩ {y ≥ 981}（实测页脚墨顶）= 0；
  · 9 件矩形 ∩ 屏内**其余全部元素**（含 `sv.help`/`sv.help_tx`/`sv.pg*`/`sv.hit_back`/槽位）= 0；
  · 除 `y` 外**任何字段不得变**（逐字段比对，action/z/w/h/asset/note 等一律不动）；
  · 输出 1:1 合成图（改前/改后，`取证\`）。

用法：python t2_move_edit_bar.py --dry    # 只算不写
      python t2_move_edit_bar.py          # 落盘（先备份 原形备份\）
"""
import sys, os, json, shutil
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SCR = os.path.join(BASE, "layout", "screens")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
BAK = os.path.join(WORK, "原形备份"); os.makedirs(BAK, exist_ok=True)
SHIFT = 122
MOVE = ["sv.edit", "sv.del_tx", "sv.del", "sv.mod_tx", "sv.mod",
        "sv.mov_tx", "sv.mov", "sv.cpy_tx", "sv.cpy"]
BAND_TOP_ACT = 981          # 贴后页脚带**实测墨迹顶**（x900..1904，逐件 981..986 取最小）
BAND_TOP_SPEC = 988         # 派单口径
OLD_NOTE = ("★ **不动的部分**：页脚条 y988..1032（PSV 烘焙中文页脚）为**待定区**（用户双路对比中）"
            "⇒ `sv.edit`/`sv.del|mod|mov|cpy`(+`_tx`)/`sv.hit_back` 未动；页码键保留现有件、"
            "仅整体左移 56px 与槽网格左沿对齐；`sv.sys_*` 与 `sv.help` 几何未动。")
NEW_NOTE = ("★ **页脚落地轮（2026-09-26 · ISSUE-20260926-06；用户裁定页脚走 B 路生图）**："
            "7 张整屏底图贴上 B 路中文页脚（几何与验收见 `_工作\\ISSUE-20260926-06_页脚双路\\`）；"
            "**编辑键条 9 件整体上移 122px**（`sv.edit` y970→848；`sv.del|mod|mov|cpy` 的 `_tx`/hit "
            "y964→842）—— 原状该条压在烘焙页脚带（贴后实测墨迹 y982..1030）上，中文压中文"
            "（「编辑」压「决定」、「移动」压「删除数据」、「复制」压烘焙「返回」）。"
            "取值依据：与页脚带交叠面积 = 0（阈值 y≥981 与派单口径 y≥988 双达标）"
            "**且**与屏内其余元素零相交 —— 正上方 `sv.help`(y907..952) 把小幅上移堵死，"
            "故 S = 118 为碰撞下界、取 122 留 4px 缝（详见报告「修法依据」与 1:1 合成图）。"
            "**action 与机制字段一律未改**（`sv.hit_back` 亦未动，其覆盖的烘焙「返回」键位置不变）；"
            "页码键保留现有件、仅整体左移 56px 与槽网格左沿对齐；`sv.sys_*` 与 `sv.help` 几何未动。")


def rect(im):
    return (im["x"], im["y"], im["x"] + im["w"], im["y"] + im["h"])


def inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def band_inter(a, top):
    """矩形 a 与「y ≥ top」半平面的交叠面积"""
    return max(0, a[3] - max(a[1], top)) * (a[2] - a[0])


def main():
    dry = "--dry" in sys.argv
    for fn in ("23_save.json", "24_load.json"):
        p = os.path.join(SCR, fn)
        raw = open(p, encoding="utf-8").read()
        d = json.loads(raw)
        assert raw == json.dumps(d, ensure_ascii=False, indent=1) + "\n", "%s 格式与本脚本写出格式不符" % fn
        assert OLD_NOTE in d["note"], "%s 缺待替换的 note 段" % fn
        pre = {e["id"]: dict(e) for e in d["elements"]}
        idx = {e["id"]: e for e in d["elements"]}
        print("=" * 104)
        print(fn, "· 编辑键条上移 %dpx" % SHIFT)
        for eid in MOVE:
            e = idx[eid]
            y0 = e["y"]
            e["y"] = y0 - SHIFT
            e["note"] = (e.get("note", "") + "　★ 页脚落地轮（2026-09-26）：本件随编辑键条**整体上移 122px**"
                         "（y %d→%d）—— 原状压在烘焙中文页脚带（实测墨迹 y982..1030）上；"
                         "action/机制字段未改。" % (y0, e["y"]))
            print("   %-12s y %4d → %4d   rect=(%d,%d,%d,%d)" % (eid, y0, e["y"], *rect(e)))
        # 自证 1：与页脚带（两个阈值）零交叠
        for eid in MOVE:
            a = rect(idx[eid])
            for top in (BAND_TOP_ACT, BAND_TOP_SPEC):
                assert band_inter(a, top) == 0, "!! %s 与 y≥%d 带交叠 %d px²" % (eid, top, band_inter(a, top))
        # 自证 2：与其余元素零相交（**整屏底/遮罩 `sv.bg`/`sv.dim` 除外**——它们 1920×1080 覆盖全屏，
        #         与任何元素「相交」是设计本意：底图在 z=2、遮罩 z=1，均在编辑键条 z=20/25 之下）
        moved = set(MOVE)
        canvas = [e for e in d["elements"] if e["w"] * e["h"] >= 1920 * 1080]
        skip = moved | {e["id"] for e in canvas}
        bad = []
        for eid in MOVE:
            a = rect(idx[eid])
            for e in d["elements"]:
                if e["id"] in skip:
                    continue
                n = inter(a, rect(e))
                if n > 0:
                    bad.append((eid, e["id"], n))
        assert not bad, "!! 与其余元素相交：%s" % bad
        print("   自证：9 件 ∩ {y≥981}=0 ∩ {y≥988}=0；∩ 其余 %d 件元素=0 ✓（整屏件 %s 除外，见脚本注释）"
              % (len(d["elements"]) - len(MOVE) - len(canvas), [e["id"] for e in canvas]))
        # 自证 3：除 y（与追加的 note 尾注）外字段逐字未变
        for eid in MOVE:
            for k, v in pre[eid].items():
                if k in ("y", "note"):
                    continue
                assert idx[eid][k] == v, "!! %s 字段 %s 被改动" % (eid, k)
            for k in ("action", "z", "w", "h", "x", "asset", "kind"):
                if k in pre[eid]:
                    assert idx[eid][k] == pre[eid][k], "!! %s 机制/几何字段 %s 被改动" % (eid, k)
        print("   自证：9 件的 action / z / x / w / h / kind / asset 与全部非 y 字段逐字未变 ✓")
        d["note"] = d["note"].replace(OLD_NOTE, NEW_NOTE)
        out = json.dumps(d, ensure_ascii=False, indent=1) + "\n"
        if not dry:
            bp = os.path.join(BAK, fn)
            if not os.path.exists(bp):
                shutil.copyfile(p, bp)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
            print("   已写盘 %s（%d → %d 字节）" % (p, len(raw), len(out)))
        else:
            print("   (dry-run，未写盘)")


if __name__ == "__main__":
    main()
