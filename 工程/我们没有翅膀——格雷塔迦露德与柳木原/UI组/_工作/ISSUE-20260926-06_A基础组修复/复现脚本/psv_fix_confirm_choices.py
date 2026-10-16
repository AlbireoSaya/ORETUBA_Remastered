# -*- coding: utf-8 -*-
r"""psv_fix_confirm_choices.py —— A 基础组修复轮：**21 确认框 / 36 选择支**数据侧修复

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）· **A 基础组修复轮**（vision 判不达标）。
依据：`PSV换皮_素材与文字处置清单.md` §七 line 136（**用户裁决**）＋ 本轮派单缺陷清单 ①③。
素材侧配套：`工具\psv_make_assets.py`（15 张 602 板裁 540；36 两态按双阈值重裁）——**先跑它再跑本脚本**。

■ 缺陷 ①（21 确认框）：15 张 602 高板在**板体之外**残留一对白羽 YES/NO 徽章（屏 x444–652 y811–872，
  与板内烘焙 YES/NO 重复、悬空在压暗底上）。
  **修法**：素材裁为 1044×540（`psv_make_assets.py`）＋ 本脚本把该 15 张板的 `h` 由 602 改 **540**
  （`y` 保持 270 ⇒ 板体仍恒落 276..804，两型板体不跳位）。
  ★ **与派单「必做连带」的有据偏离（必读）**：派单称「裁掉后板内 YES/NO 也一并消失」⇒ 要 22 板统一
    补我方按钮。**实测不成立**：裁剪窗 `(0,0,1044,540)` 完整保留**板内**烘焙 YES/NO（板内 y336..368
    → 画布 606..638）。若按「必做连带」再给 15 张补我方按钮，就会与残留的板内烘焙 YES/NO **叠成两行**
    （正是 vision 判为「重复」的同类缺陷）。且 `PSV换皮_素材与文字处置清单.md` §七 line 136 的**用户裁决**
    明文写：「01–12/25/43/44 已含烘焙 YES/NO（**加透明热区覆盖**），20–24/42/45 无 YES/NO（**补我方是/否按钮**）」
    ⇒ 本轮**按用户裁决**：15 张保留板内烘焙 YES/NO ＋ 透明热区（不补按钮），7 张保留我方按钮。
    若主代理仍要「22 板统一为无 YES/NO 板」，需另做一步**板内 YES/NO 补底**（本脚本不隐式改美术）。

■ 缺陷 ③-2（36 选择支）：`item_h` 107 与素材 128 不等比 ⇒ 端帽被纵向压扁（实绘 1216×92 vs 内容 1215×111）。
  **修法**：`item_h 107 → 128`（与素材 1:1，零缩放）；`gap 17 → 2` —— **画布硬约束**：`max_rows=6`
  要求 6×item_h + 5×gap ≤ 1080 − 300 = 780 ⇒ 6×128 + 5×2 = 778 ✓（其余 `item_h` ≥ 130 即溢出）。
  `max_rows`/`scroll`/`actions` **不动**（翻页行为不变）。

**幂等**：本脚本读盘 → 按固定值改 → 写回；重复运行结果逐字节相同（改前先比对，无变化则报 NOCHANGE）。
用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_A基础组修复\复现脚本\psv_fix_confirm_choices.py [--check]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))                    # …\复现脚本
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))            # …\UI组
SCR = os.path.join(UI, "layout", "screens")

CFM_ALL = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
           "20", "21", "22", "23", "24", "25", "42", "43", "44", "45"]
CFM_WITH_YESNO = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
                  "25", "43", "44"}          # 15 张：板内含烘焙 YES/NO
CFM_ADD_BTN = [nn for nn in CFM_ALL if nn not in CFM_WITH_YESNO]      # 7 张：我方是/否按钮

PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 438, 270, 1044, 540

# ── 两型板共用的**一对热区**（画布坐标，几何本轮**不变**）────────────────────────
#   上带 605..638 = 15 张板的**板内烘焙 YES/NO**文字带（画布 606..638）；
#   下带 642..684 = 7 张板的我方 140×42 按钮；x 788..928 / 942..1082（不重叠、间隙 14px）。
#   ⇒ 一对矩形**同时覆盖 22 张板的可点带**（`vis_when:"*"` ⇒ 有板在位时热区才生效）。
HIT_YES = (788, 605, 140, 85)
HIT_NO = (942, 605, 140, 85)

HIT_YES_NOTE = (
    "「是」热区（`action=confirm_yes`，透明无美术）。★ **两型板共用同一对**（矩形 x788..928、"
    "y605..690 同时覆盖 **15 张板的板内烘焙 YES 文字带**（画布 853..923 × 606..638）与 "
    "**7 张板的我方按钮**（788..928 × 642..684）⇒ 22 张板点击面一致）。\n"
    "★ **本轮修复（ISSUE-20260926-06 · A 基础组修复）**：① 加 `vis_flag:\"cf_which\"` + `vis_when:\"*\"` "
    "——「有板在位（`cf_which` 非空）时热区才生效」，与选板 flag 同源：无板时不残留可点热区；\n"
    "② 上带 605..638 的语义随 15 张板裁掉**板体之外**的白羽徽章带而更新：它现在覆盖的是**板内**烘焙 "
    "YES 文字带（**未**被裁掉——裁剪窗 0..540 含板内 y336..368）。热区高 85 > 7 张板按钮高 42，"
    "多出的 43px 为**惰性内边距**（派发同一动作，无害）。"
)
HIT_NO_NOTE = (
    "「否」热区（`action=confirm_no`，透明无美术）。同 `cf.hit_yes`：矩形 x942..1082 覆盖 "
    "**15 张板的板内烘焙 NO 文字带**（画布 972..1018 × 606..638）与 **7 张板的我方按钮**（942..1082 × 642..684）；"
    "`vis_flag:\"cf_which\"` + `vis_when:\"*\"`（有板在位时才生效）。"
)

FIX_NOTE = """★ **修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复，vision 判不达标后重做）**：
  · **①【高】板体之外的白羽 YES/NO 徽章带已裁除**：15 张 `01–12/25/43/44` 源件高 602 = 板体（y6..534）
    ＋ **板体之外底部左侧那对白羽 YES/NO 徽章带（y541..602 → 屏 811..872）**；后者与板内烘焙 YES/NO
    重复、且悬空在压暗底上。素材已按 `(0,0,1044,540)` 裁为 1044×540（`工具\\psv_make_assets.py`），
    本屏该 15 张板 `h 602 → 540`（`y` 仍 270 ⇒ 板体恒落 276..804，**与 7 张 540 型板体同位、不跳位**）。
    ★ **实测订正（与派单「必做连带」不同）**：裁剪窗**含**板内烘焙 YES/NO（板内 y336..368 → 画布 606..638），
      故 15 张板**不补我方按钮**——按 `PSV换皮_素材与文字处置清单.md` §七 line 136 的**用户裁决**
      「已含烘焙 YES/NO（加透明热区覆盖）／无 YES/NO 的 20–24/42/45 补我方是/否按钮」。
      详见 `_工作\\ISSUE-20260926-06_A基础组修复\\复现脚本\\psv_fix_confirm_choices.py` docstring。
    ⇒ 22 张板**不是**「统一为无 YES/NO 的板」，而是**按用户裁决的两型板**：15 张靠板内烘焙 YES/NO ＋
      透明热区，7 张靠我方按钮 ＋ 同一对热区；**一对热区几何统一覆盖全部 22 板**的可点带。
  · **② 热区加 `vis_flag:\"cf_which\"` + `vis_when:\"*\"`**：热区与选板同源 —— 有板在位才生效，
    无板（`cf_which` 空）时不残留可点热区；同屏只有当前板的按钮/烘焙文字可见（各带 `vis_when:<板号>`）。
  · **③ 几何自证**：`_工作\\ISSUE-20260926-06_A基础组修复\\复现脚本\\assert_21_confirm_geometry.py`
    逐板断言「板矩形 ⊂ 画布 / 按钮或烘焙文字带 ⊂ 板内安全区 / 热区覆盖该板可点带 / `vis_when` 集合 = 22 板号 /
    两热区无重叠」，并出 22 板接触印相表（`_工作\\ISSUE-20260926-06_A基础组修复\\取证\\sheet_21_confirm_22.png`）。
"""

CHOICE_FIX_NOTE = """  · **修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复）**：
    **③-1【中】胶囊端帽破口**：旧拆件用单一 α≥16 阈值取窗 ⇒ `norm` 右端 / `sel` 左端各切掉 7px
    羽尖柔光（vision 判「白缺＋第二道轮廓」）。现按**双阈值**重裁（`工具\\psv_make_assets.py`：
    水平 α≥2 把端帽与羽尖柔光全含 / 纵向 α≥11 —— 128 行画布硬约束下的最小阈值），
    实测源窗 `sel x4..1241`、`norm x54..1287`，两态内容中心同为画布 x619.5（水平零跳位），
    纵向只舍 α≤10（0.4% 不透明度）的边行。
    **③-2【轻】纵向非等比拉伸已消除**：`item_h 107 → 128`（与素材 1240×128 **1:1、零缩放** ⇒
    端帽不再被压扁；旧口径实绘 1216×92 vs 素材内容 1215×111 = y 0.83×）；
    `gap 17 → 2`（画布硬约束：`max_rows=6` ⇒ 6×128 + 5×2 = 778 ≤ 1080−300 = 780；`item_h≥130` 即溢出）。
    `max_rows` / `scroll` / `actions` / `labels` **未动**（翻页行为不变）。
    ⚠️ 字号随条高变：`font.size 44` **未改** —— 旧值 44 本是「随条等比」的产物（= 34 × 107/83，保持
    旧屏「字高/条高 = 41%」），本轮条高回正为 128 后若要维持该比例应为 52.4；**本轮判据只要求几何 1:1**，
    改字号会动到 vision 已审阅过的文字观感 ⇒ 维持 44（比例变为 34.4%），**已列为未决点上报主代理**。
"""


def w(src, path, data):
    with io.open(path, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return len(data.get("elements", []))


def fix_confirm(dry):
    p = os.path.join(SCR, "21_confirm.json")
    old = json.load(io.open(p, encoding="utf-8"))
    for e in old["elements"]:
        eid = e["id"]
        if eid.startswith("cf.panel_") and e["kind"] == "image":
            nn = eid.split("_")[1]
            assert nn in CFM_ALL, eid
            e["h"] = PANEL_H
            e["y"] = PANEL_Y
            e["x"], e["w"] = PANEL_X, PANEL_W
            if nn in CFM_WITH_YESNO:
                e["note"] = ("PSV 中文弹窗板 %s（1044×540，1:1）｜**板内**含烘焙 YES/NO"
                             "（板内 YES x415..485 / NO x534..580、y336..368 → 画布 853..923 / 972..1018 × 606..638）"
                             "＋ 本轮已裁去**板体之外**底部左侧那对白羽 YES/NO 徽章带（源 y541..602 → 屏 811..872）"
                             % nn)
                e["source"] = ("PSV系统UI参考\\AI中文化\\2x\\otv_dlg_bg_%s_cn.png（PSV 系统 UI 中文弹窗板，"
                               "源件 1044×602 = 板体 y6..534 ＋ 板外白羽徽章带 y541..602；"
                               "ISSUE-20260926-03/-04 产；入库件 `krkr\\assets\\ui\\x_ui_psv_cfm_%s.png`，"
                               "脚本 工具\\psv_make_assets.py：**裁 (0,0,1044,540)**（去板外徽章带、板体与板内烘焙 "
                               "YES/NO 全留）＋ 每通道降 6bit）" % (nn, nn))
            else:
                e["note"] = ("PSV 中文弹窗板 %s（1044×540，1:1）｜**无 YES/NO**"
                             "（本屏补我方是/否按钮与热区）" % nn)
        elif eid == "cf.hit_yes":
            e["x"], e["y"], e["w"], e["h"] = HIT_YES
            e["vis_flag"], e["vis_when"] = "cf_which", "*"
            e["note"] = HIT_YES_NOTE
        elif eid == "cf.hit_no":
            e["x"], e["y"], e["w"], e["h"] = HIT_NO
            e["vis_flag"], e["vis_when"] = "cf_which", "*"
            e["note"] = HIT_NO_NOTE
    # 7 张板的按钮/文字：几何与语义不变，仅更新 note 里的「7 张板 y 统一 642」措辞（仍有效）
    n_btn = 0
    for e in old["elements"]:
        if e["id"].startswith("cf.yes_b") or e["id"].startswith("cf.no_b"):
            nn = e["id"][-2:]
            key = "是" if "_b" in e["id"][:6] and e["id"].startswith("cf.yes") else "否"
            e["note"] = ("板 %s（无 YES/NO）的「%s」按钮底——三态图，`vis_flag=cf_which`/`vis_when=%s` "
                         "⇒ 仅本板可见。★ 7 张板按钮一律画布 y642..684（板内 372..414 = "
                         "**最长文案板**（22 板 4 行、末行到板内 y366）+6px，落在板内下缘留白内）；"
                         "两型板共用一对热区（605..690）⇒ 按钮必落在热区内（热区 z=95 > 本件 z=20："
                         "悬停胜出者为热区、`state_group` 组内一致）。" % (nn, key, nn))
            n_btn += 1

    note = old["note"]
    if "修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复" not in note:
        # 插在旧 PSV 段之后（保留全部历史段落）
        old["note"] = note.rstrip() + "\n" + FIX_NOTE
    # 旧 note 里已过时的两句（602 口径）就地订正（一次性：二次运行时旧串已不存在，自动成为 no-op）
    old["note"] = (old["note"]
                   .replace("· 15 张 `01–12/25/43/44`（高 602）**已含烘焙 YES/NO**",
                            "· 15 张 `01–12/25/43/44`（源件高 602，**已裁为 540**）**板内含烘焙 YES/NO**")
                   .replace(
                       "★ **纵向一律 `y=270`**（板）：两种高度共用同一板体（y6..534）"
                       "⇒ 板体恒落 276..804（正中 (1080-528)/2）；\n"
                       "  602 型多出的 62px 是**底部左侧那对羽毛 YES/NO 徽章带**（809..872），属该件的固有构图。",
                       "★ **纵向一律 `y=270`**（板；22 张现均 1044×540，板体 y6..534）" 
                       "⇒ 板体恒落 276..804（正中 (1080-528)/2）；**原 602 型多出的 62px"
                       "（板体之外左下角那对白羽 YES/NO 徽章带，811..872）本轮已随素材裁除**。")
                   .replace(
                       "`x_ui_psv_cfm_01.png`（22 件，`工具\\psv_make_assets.py` 入库；降 6bit 见该脚本 docstring）",
                       "`x_ui_psv_cfm_<板号>.png`（22 件，**均 1044×540**；`工具\\psv_make_assets.py` 入库；"
                       "降 6bit 见该脚本 docstring）"))
    out = {}
    for k in ("id", "title_cn", "owner", "flags_default", "note", "elements"):
        if k in old:
            out[k] = old[k]
    for k in old:
        if k not in out:
            out[k] = old[k]
    if dry:
        return "21_confirm.json（dry）元素 %d 件、7 张板按钮底 %d 件" % (len(out["elements"]), n_btn)
    n = w(None, p, out)
    return "21_confirm.json 元素 %d 件（7 张板各 4 件：按钮底 %d 件 + 文字 %d 件）" % (n, n_btn, n_btn)


def fix_choices(dry):
    p = os.path.join(SCR, "36_choices.json")
    old = json.load(io.open(p, encoding="utf-8"))
    hit = False
    for e in old["elements"]:
        if e["id"] != "ch.choices":
            continue
        e["item_h"], e["gap"] = 128, 2
        e["note"] = e["note"].rstrip() + "\n" + CHOICE_FIX_NOTE
        e["source"] = ("PSV系统UI参考\\超分2x\\otv_selwin.png（PSV 选择支两态条）→ 工具\\psv_make_assets.py "
                       "拆两态（**修复轮双阈值重裁**：水平 α≥2 全含端帽/羽尖、纵向 α≥11 装进 128 行画布）："
                       "ui/x_ui_psv_choice_norm.png（蓝紫）/ ui/x_ui_psv_choice_sel.png（粉）")
        hit = True
    assert hit, "没找到 ch.choices"
    if "修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复）" not in old["note"]:
        old["note"] = old["note"].rstrip() + "\n" + CHOICE_FIX_NOTE
    old["note"] = (old["note"]
                   .replace("`item_h 83 → 107`（PSV 条高）", "`item_h 83 → 107`（PSV 条高，**修复轮再改 128**）")
                   .replace("`gap 17` 与 `max_rows 6` **沿用旧值**（6 行 = 6×107+5×17 = 727 → y300..1027 不出画布；",
                            "`gap 17` 与 `max_rows 6` **沿用旧值**（旧：6 行 = 6×107+5×17 = 727 不出画布；"
                            "**修复轮改 `gap=2`**：6×128+5×2 = 778 ≤ 780 不出画布，见下；"))
    if dry:
        return "36_choices.json（dry）元素 %d 件" % len(old["elements"])
    n = w(None, p, old)
    return "36_choices.json 元素 %d 件" % n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报将改什么，不落盘")
    a = ap.parse_args()
    print("=" * 78)
    print("A 基础组修复轮：21 确认框 / 36 选择支 数据侧修复%s" % ("（--check 不落盘）" if a.check else ""))
    print("=" * 78)
    for fn, f in (("21_confirm.json", fix_confirm), ("36_choices.json", fix_choices)):
        print("  " + f(a.check))
    print("结果：%s" % ("仅比对" if a.check else "已落盘"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
