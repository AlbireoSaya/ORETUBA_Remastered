# -*- coding: utf-8 -*-
r"""psv_build_abasic_screens.py —— A 基础组三屏 PSV 换皮（**一次性脚手架**）

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）｜ 依据 `PSV换皮_素材与文字处置清单.md` §一 + §七。
对象：`layout/screens/21_confirm.json`（确认框）／`22_loading.json`（加载提示）／`36_choices.json`（选择支）。

★★ **本脚本是一次性脚手架，产物已入库；此后三屏手工维护，不要重跑本脚本**——
   重跑会覆盖此后对这三屏的任何手工修改。生成器登记（`工具\test_gen_sync.py`）里
   三屏的现状见该文件的 `ACK_UNSYNC["21_confirm.json"]` / `ACK_UNSYNC["36_choices.json"]` /
   `GENERATORS` 的 m33 条目注释。

■ 几何（全部实测，见 `_工作\ISSUE-20260926-06_A基础组三屏换皮\证据\psv_abasic_geometry.txt`）
  PSV 2× 件即本作画布口径（PSV 960×544 ×2 = 1920×1088 ≈ 本作 1920×1080）⇒ **1:1 摆放，零缩放**。
  · 22 张确认板：**1044×540 / 1044×602**，水平居中 `x = (1920-1044)/2 = 438`；
    **纵向按"板体"对齐**（两种高度共用同一板体 y6..534）⇒ 一律 `y = 270`：
    540 型板体落在 276..804（= (1080-528)/2 正中）✓；602 型板体同位（多出的 62px 是
    底部左侧那对羽毛 YES/NO 徽章带，落在板体下方 809..872）。**.zero 位移，两型板体永不跳位。**
  · 烘焙 YES/NO 实测（板内坐标）：**YES 文字 x415..485 / NO 文字 x534..580，y336..368**
    （合成 bbox = 清单 §一 的 (416,336)-(580,367)）⇒ 画布 `853..923 / 972..1018 × 606..638`。
  · 两型板**共用同一对热区**（`140×85` @ 画布 `(788,605)` / `(942,605)`）：矩形必须**同时**盖住
    15 张的烘焙 YES/NO 文字带（606..638）与 7 张的我方按钮带（642..684）⇒ h=85。
    7 张补按钮板的按钮**统一放板内 y=372**（= 最长文案板 22 的末行 y366 + 6px）——
    因为热区无法逐板换 y（一个元素一对 flag），逐板移动按钮会让 22/23 落到热区外点不到。
  · 22 加载牌 `640×240`：墨迹实测 `x69..574 × y68..172`（505×104）**在画布内居中**（左69/右66、上68/下68）
    ⇒ 画布居中摆放（`x=(1920-640)/2=640, y=(1080-240)/2=420`）即墨迹居中。
  · 36 选择支条 `1240×128` 两态（公共画布；源 bbox 粉 1227×126 ／ 蓝 1223×126）⇒
    `x=(1920-1240)/2=340`、`item_h=107`、`gap=17`（沿用旧值）⇒ 6 行 = 6×107+5×17 = 727 → y300..1027 ✓ 不出画布。

■ 旗标（`cf_which` 选板）
  `flags_default: {"cf_which": "01"}`；22 张板各带 `vis_flag:"cf_which"` + `vis_when:"<板号>"`。
  **同一时刻只显一块**（取值严格相等 ⇒ 天然互斥）。调用方在进屏后 `uiScreenFlagSet("cf_which","<板号>")`
  （屏栈 reset 会按 `flags_default` 重置 ⇒ 必须在**进屏之后**写）。
  ★ 靠 flag 控显隐的元素 `visible_default` **必须 true**（`_schema.md` §四铁律），本脚本全部显式写 true。

■ 7 张无 YES/NO 板（20–24/42/45）为何要 4 件/张 × 7 = 28 件
  `vis_flag` **一个元素只允许一对**（`_schema.md` §四）⇒「按板号显隐」的一个值只能对应一张板，
  故"我方是/否按钮的图与文字"必须**逐板各写一份**（28 件）。热区**不重复**（两型板共用同一对，
  见上）⇒ 21 确认框总件数 = 1（dim）+ 22（板）+ 2（热区）+ 28（补按钮）= **53 件**。
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
SCR = os.path.join(UI, "layout", "screens")

CFM_ALL = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
           "20", "21", "22", "23", "24", "25", "42", "43", "44", "45"]
CFM_WITH_YESNO = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "25", "43", "44"}
CFM_H = {nn: (602 if nn in CFM_WITH_YESNO else 540) for nn in CFM_ALL}
CFM_ADD_BTN = [nn for nn in CFM_ALL if nn not in CFM_WITH_YESNO]      # 20-24/42/45 = 7 张

PANEL_X, PANEL_Y, PANEL_W = 438, 270, 1044
# ── 两型板共用的**热区**（画布坐标）─────────────────────────────────────────────
#   x：同时满足「盖住 15 张的烘焙 YES/NO 文字」(853..923 / 972..1018) 与「容纳 7 张的我方 140×42 按钮」
#      ⇒ 140 宽、不重叠、间隙 14px；一对中心 = 935（PSV 烘焙文字的成对中心，比画布中心左 25px）。
#   y/h：**必须同时覆盖两条带** ——
#      ① 烘焙 YES/NO 文字带：画布 606..638（板内 336..368）
#      ② 我方按钮带：画布 642..684（板内 372..414）
#      ⇒ 取 605..690（h=85）。**为什么按钮带是统一的 372 而不是逐板贴文案下沿**：
#        `vis_flag` 一个元素只允许一对 ⇒ 热区**无法逐板换 y**，若按钮逐板变 y，
#        22/23 的按钮就会落到共用热区之外（点不到）。实测 22 板文案末行到板内 y366
#        ⇒ 7 张统一取 372（= 最长文案末行 + 6px），5 张短文案板因此按钮偏下（落雪带上沿，可接受）。
#      ⇒ 热区高 85 > 按钮高 42：按钮之外那 43px 是**惰性内边距**（点它派发同一动作，无害）。
HIT_YES = (788, 605, 140, 85)
HIT_NO = (942, 605, 140, 85)
# ⚠️ 一律用**画布坐标**（与元素 x/y 同系）；板内 y=372 ⇒ 画布 **642**（= 270 + 372）。
#    首版误把板内值直接写进元素 y（画布 372）⇒ 按钮跑到文案上方、且落在共用热区之外 —— 预览表复盘时发现并修正。
BTN_YES = (788, 642, 140, 42)
BTN_NO = (942, 642, 140, 42)
BTN_NINE = {"l": 19, "t": 10, "r": 19, "b": 10}     # 沿用旧屏是/否按钮底的九宫格
BTN_FONT = {"size": 28, "bold": True, "color": "@palette.node_locked",
            "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
BTN_STATE = {"normal": "ui/x_ui_btn_l_off.png",
             "hover": "ui/x_ui_btn_l_over.png",
             "pressed": "ui/x_ui_btn_l_on.png"}
SRC_PSV = ("PSV系统UI参考\\AI中文化\\2x\\otv_dlg_bg_<NN>_cn.png（PSV 系统 UI 中文弹窗板，"
           "ISSUE-20260926-03/-04 产；入库件 `krkr\\assets\\ui\\x_ui_psv_cfm_<NN>.png`，"
           "脚本 工具\\psv_make_assets.py：1:1 不缩放 + 每通道降 6bit）")

LOAD_PLATE = dict(x=640, y=420, w=640, h=240)
CHOICE_X, CHOICE_Y, CHOICE_W, CHOICE_H, CHOICE_GAP = 340, 300, 1240, 107, 17

CONFIRM_NOTE = """**PSV 换皮（2026-09-26，ISSUE-20260926-06）· 21 确认框**。用户裁决（`PSV换皮_素材与文字处置清单.md` §七）：
★ **22 张 PSV 中文弹窗全部采用**（`otv_dlg_bg_01..12/20..25/42..45_cn`，2× 件 1044×540/602 **1:1 摆放**，
  零缩放——PSV 2× 即本作画布口径 960×544×2=1920×1088≈1920×1080）。**文案烘焙在图内**：
  本屏不再引擎绘字，`cf.msg` 与旧 `cf.panel`（AI 冰蓝面板）**已退场**；换文案需换板号或重跑生图。
★ **选板 = 屏级 flag `cf_which`**：22 张板各带 `vis_flag:"cf_which"` + `vis_when:"<板号>"`，取值严格相等
  ⇒ 同一时刻只显一块。`flags_default.cf_which = "01"`；调用方进屏后 `uiScreenFlagSet("cf_which","<板号>")`
  （**屏栈 reset 会按 flags_default 重置 ⇒ 必须在进屏之后写**）。靠 flag 控显隐的元素一律 `visible_default:true`（§四铁律）。
★ **两型板**：
  · 15 张 `01–12/25/43/44`（高 602）**已含烘焙 YES/NO**（实测板内 YES x415..485 / NO x534..580、y336..368）
    ⇒ 只在其上放**透明热区**（`cf.hit_yes`/`cf.hit_no`，`action` 沿用 `confirm_yes`/`confirm_no`）。
  · 7 张 `20–24/42/45`（高 540）**无 YES/NO** ⇒ 补**我方是/否按钮**（沿用现屏 `x_ui_btn_l_off/over/on.png`
    三态 + 引擎绘「是/否」）。`vis_flag` 一个元素只允许一对 ⇒ 逐板各一份（7×4 = 28 件）。
★ **两型板共用同一对热区**（`140×85`，`x788`/`x942`，`y605`，**不重叠、间隙 14px**）：几何同时满足
  「盖住 15 张的烘焙 YES/NO 文字带（画布 606..638）」与「容纳 7 张的我方 140×42 按钮带（画布 642..684）」。
  一对的中心 = 935（PSV 烘焙文字的成对中心；比画布中心 960 左 25px，属 PSV 版式）。
  **为何 140 宽而非旧屏 203**：PSV 的 YES/NO 文字只隔 107px，两枚 ≥170 宽的按钮无法同时
  「各自盖住自己的文字」且「互不重叠」（107 < 170+间隙）——几何硬约束。
★ **7 张补按钮板的按钮统一放板内 y=372**（画布 642..684）：= **最长文案板**（22 板 4 行、末行到板内 y366）
  +6px。**为什么不能逐板贴文案下沿**：`vis_flag` 一个元素只允许一对 ⇒ 热区**无法逐板换 y**，
  按钮逐板移动会让 22/23 的按钮落到共用热区（605..690）之外 ⇒ 点不到。热区高 85 > 按钮高 42，
  多出的 43px 是**惰性内边距**（派发同一动作）。
★ **纵向一律 `y=270`**（板）：两种高度共用同一板体（y6..534）⇒ 板体恒落 276..804（正中 (1080-528)/2）；
  602 型多出的 62px 是**底部左侧那对羽毛 YES/NO 徽章带**（809..872），属该件的固有构图。
★ 素材：`ui/x_ui_psv_cfm_<板号>.png`（22 件，`工具\\psv_make_assets.py` 入库；降 6bit 见该脚本 docstring）。
★ 退场登记：`工具\\test_gen_sync.py` 的 `ACK_UNSYNC["21_confirm.json"]`（生成器 `m34_build_screens.build_confirm()`
  仍在 `__main__` 接线里 ⇒ 重跑会把本屏整体改回旧形，**不得重跑**）。"""

# ★ 订正（2026-09-29 · ISSUE-20260929-02 · E3 登记，非本脚本的产物变更）：
#   本常量只描述 **PSV 换皮当时** 的加载屏。此后 `22_loading.json` 的 `ld.bg` 元素已按用户指令 6
#   删除（该屏 3 件 → 2 件：`ld.dim` / `ld.text`），故本常量末段「`ld.bg` … 保留现状」已与盘上不符。
#   ⚠ **不得重跑本脚本**：整跑会把本常量写回屏 note（抹掉现 note 里的 2026-09-29 订正），
#   并可能覆盖同批其他屏。`工具\\test_gen_sync.py` 的 GENERATORS m33 条目已把本屏登记为
#   「失效生成器会改坏的屏」，闸门每次都会点名（退出码不受影响）。
LOADING_NOTE = """**PSV 换皮（2026-09-26，ISSUE-20260926-06）· 22 加载提示**。
★ `ld.plate` 由 AI 冰蓝提示牌（`x_ui_loading_plate.png` 420×148）**换成 PSV 件** `ui/x_ui_psv_loading.png`
  （`otv_loading_cn.png` 640×240，1:1、无 nine ⇒ `w/h` == PNG 实尺寸）。**图上烘焙「载入中…」**
  （墨迹实测 505×104，在 640×240 内居中：左69/右66、上68/下68）⇒ 画布居中摆放 `x=640 y=420` 即墨迹居中。
★ 故 `ld.text`（引擎绘「加载中……」）**退场**：与新图文字重复（会叠字）。
  ⚠️ 措辞随之由「加载中……」变为图内烘焙的「**载入中…**」（三字 + 空心圆省略号）。
★ `ld.bg`（满幅冰蓝底）与 `ld.dim`（压暗遮罩 `@palette.backdrop` ×100）**保留现状**（用户裁决允许"保留现状或按
  PSV 观感调整"）——PSV 件本身是透明底文字层，压在现有底上观感与 PSV 原屏一致。
★ 退场登记：`工具\\test_gen_sync.py` 的 `GENERATORS` m33 条目（该模块已标"失效、不得再运行"，
  其 `build_loading()` 产出的是 `x_gen_sd_*` 旧素材体系；重跑会改回旧形并引用缺图）。"""

CHOICES_NOTE = """★ **PSV 换皮（2026-09-26，ISSUE-20260926-06）**：条框换成 PSV 件，用户裁决「按深度换皮口径取 PSV 版式」。
  · **两态拆件**：`ui/x_ui_psv_choice_norm.png`（蓝紫＝常态）/`ui/x_ui_psv_choice_sel.png`（悬停/按下＝粉），
    由 `PSV系统UI参考\\超分2x\\otv_selwin.png` 拆出（`工具\\psv_make_assets.py`）：
    实测源内 bbox 粉 `x11..1237 × y9..133`、蓝紫 `x57..1279 × y169..293`（α≥16 口径），
    各自裁切后**居中到公共画布 1240×128**（同尺寸同轴向 ⇒ 换态不跳位）。
    ★ 公共画布而非各裁各放：两胶囊在源图内**水平相差 44px**（粉中心 x624 / 蓝中心 x668），各裁各放会让
      蓝紫条比粉条右移 44px、悬停即"跳一下"。拆件全程**统一倍率 1.0（无重采样）**，符合会话交接 §5 铁律
      「压缩素材必须整图统一倍率缩放后按切分，禁止逐件归一化」。
  · **三态映射**（用户/主代理口径，2026-09-26）：`normal` = 蓝紫 ／ `hover` = 粉 ／ `pressed` = 粉。
    PSV 只给两态（粉＝选中、蓝紫＝常态）⇒ **按下与悬停同图**（两态折叠，不再有第三色）。
    ⚠️ 若日后判定"粉＝常态、蓝紫＝悬停"或其他语义，只改本字段三者映射即可（不动素材）。
  · **版式**：`w 1113 → 1240`（PSV 条 1:1）、`x 404 → 340`（居中）、`item_h 83 → 107`（PSV 条高）、
    `gap 17` 与 `max_rows 6` **沿用旧值**（6 行 = 6×107+5×17 = 727 → y300..1027 不出画布；
    不取 PSV 节距 155 是因为它会让 6 行高 893px 溢出画布，进而必须把 `max_rows` 降到 4–5 ⇒ 改变既有翻页行为）。
  · **文字随条几何同步**：字号 `34 → 44`（= 34 × 107/83，**保持旧屏已验收的"字高/条高 = 41%"比例**），
    仍由引擎逐项绘制（`labels` 居中于条），**未把文字烘焙进图**。
  · 旧三态素材 `x_ui_choice_off/over/press.png`（1135×105）随本屏换皮**不再被引用**（按工程惯例**保留不删**）。"""


def img(eid, z, asset, x, y, w, h, note, source=None, **kw):
    d = {"id": eid, "kind": "image", "z": z, "visible_default": True, "asset": asset,
         "x": x, "y": y, "w": w, "h": h, "opacity": 255, "note": note}
    if source is not None:
        d["source"] = source
    d.update(kw)
    return d


def txt(eid, z, x, y, w, h, sample, note, **kw):
    d = {"id": eid, "kind": "text", "z": z, "visible_default": True,
         "x": x, "y": y, "w": w, "h": h, "font": dict(BTN_FONT),
         "align": "center", "valign": "middle", "wrap": False, "max_lines": 1,
         "sample": sample, "note": note}
    d.update(kw)
    return d


def build_confirm(old):
    els = []
    dim = [e for e in old["elements"] if e["id"] == "cf.dim"][0]
    dim["note"] = "全屏压暗遮罩（保留现状：PSV 板为半透明霜板，压暗保证板面可读）"
    els.append(dim)
    for nn in CFM_ALL:
        h = CFM_H[nn]
        t = "含烘焙 YES/NO（板内 YES x415..485 / NO x534..580、y336..368）" if nn in CFM_WITH_YESNO \
            else "**无 YES/NO**（本屏补我方是/否按钮与热区）"
        els.append(img("cf.panel_%s" % nn, 10, "ui/x_ui_psv_cfm_%s.png" % nn,
                       PANEL_X, PANEL_Y, PANEL_W,
                       h, "PSV 中文弹窗板 %s（%d×%d，1:1）｜%s" % (nn, PANEL_W, h, t),
                       source=SRC_PSV.replace("<NN>", nn),
                       vis_flag="cf_which", vis_when=nn))
    # 两型板合成的一对热区（透明；本屏是"内容板"而非"按钮组"，故给 state_group 让 7 张板的按钮三态联动）
    els.append({
        "id": "cf.hit_yes", "kind": "hit", "z": 95, "visible_default": True,
        "x": HIT_YES[0], "y": HIT_YES[1], "w": HIT_YES[2], "h": HIT_YES[3],
        "action": "confirm_yes", "label": "", "state_group": "confirm.yes",
        "font": dict(BTN_FONT), "align": "center",
        "note": "「是」热区（`action=confirm_yes`）。**两型板共用**（矩形同时覆盖 15 张的烘焙 YES 文字带 606..638 "
                "与 7 张的我方按钮带 642..684 ⇒ h=85）：两型板点击面一致。透明不绘任何美术；悬停/按下经 "
                "`state_group`「confirm.yes」联动同组图（仅 7 张无 YES/NO 板有同组可见图，其余板悬停无视觉变化"
                "——用户裁决「只需透明热区」）。按钮之外那 43px 为惰性内边距（派发同一动作）。",
    })
    els.append({
        "id": "cf.hit_no", "kind": "hit", "z": 95, "visible_default": True,
        "x": HIT_NO[0], "y": HIT_NO[1], "w": HIT_NO[2], "h": HIT_NO[3],
        "action": "confirm_no", "label": "", "state_group": "confirm.no",
        "font": dict(BTN_FONT), "align": "center",
        "note": "「否」热区（`action=confirm_no`）。同 `cf.hit_yes`：两型板共用（覆盖烘焙 NO 文字 972..1018 "
                "与我方按钮 942..1082）。",
    })
    for nn in CFM_ADD_BTN:
        for key, (bx, by, bw, bh), lab, grp in (("yes", BTN_YES, "是", "confirm.yes"),
                                                ("no", BTN_NO, "否", "confirm.no")):
            els.append(img("cf.%s_b%s" % (key, nn), 20, "ui/x_ui_btn_l_off.png",
                           bx, by, bw, bh,
                           "板 %s（无 YES/NO）的「%s」按钮底——三态图，`vis_flag=cf_which`/`vis_when=%s` ⇒ 仅本板可见。"
                           "★ 7 张板 y 统一 642（画布）= 板内 372 = 最长文案板（22 板末行板内 y366）+6px："
                           "**热区无法逐板换 y**（一个元素一对 flag），按钮必须落在共用热区 605..690 内 ⇒ "
                           "逐板移动会让 22/23 的按钮落到热区外点不到。热区 z=95 高于本件 z=20 ⇒ 悬停胜出者为热区、组内一致。"
                           % (nn, lab, nn),
                           source="AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py（沿用旧屏按钮底）",
                           nine=dict(BTN_NINE), state_assets=dict(BTN_STATE), state_group=grp,
                           vis_flag="cf_which", vis_when=nn))
            els.append(txt("cf.%s_tx%s" % (key, nn), 25, bx, by, bw, bh, lab,
                           "板 %s（无 YES/NO）的「%s」按钮文字（引擎绘制；`vis_flag=cf_which`/`vis_when=%s`）。"
                           % (nn, lab, nn),
                           vis_flag="cf_which", vis_when=nn))
    return els


def main():
    applied = []

    # ---------- 21 确认框 ----------
    old = json.load(io.open(os.path.join(SCR, "21_confirm.json"), encoding="utf-8"))
    scr = dict(old)
    scr["note"] = CONFIRM_NOTE
    scr["flags_default"] = {"cf_which": "01"}
    scr["elements"] = build_confirm(old)
    # 顺序：屏级字段排在一起（flags_default 紧跟 owner/note）
    out = {}
    for k in ("id", "title_cn", "owner", "flags_default", "note", "elements"):
        if k in scr:
            out[k] = scr[k]
    for k in scr:
        if k not in out:
            out[k] = scr[k]
    paths = {}
    paths["21_confirm.json"] = out
    applied.append(("21_confirm.json", len(out["elements"])))

    # ---------- 22 加载提示 ----------
    old = json.load(io.open(os.path.join(SCR, "22_loading.json"), encoding="utf-8"))
    els = []
    for e in old["elements"]:
        if e["id"] == "ld.text":
            continue                                    # 退场：图内已有「载入中…」
        if e["id"] == "ld.plate":
            e = dict(e)
            e.update(asset="ui/x_ui_psv_loading.png", x=LOAD_PLATE["x"], y=LOAD_PLATE["y"],
                     w=LOAD_PLATE["w"], h=LOAD_PLATE["h"])
            e.pop("nine", None)                         # 无 nine ⇒ w/h 必须 == PNG 实尺寸（640×240）
            e["source"] = ("PSV系统UI参考\\AI中文化\\2x\\otv_loading_cn.png"
                           "（PSV「载入中…」加载牌，ISSUE-20260926-04 产；"
                           "入库件 krkr\\assets\\ui\\x_ui_psv_loading.png，逐字节复制）")
            e["note"] = ("PSV 加载牌（640×240，1:1、无 nine）：图内烘焙「载入中…」，墨迹实测 505×104"
                         "且在画布内居中 ⇒ 画布居中摆放即墨迹居中（原 AI 提示牌 x_ui_loading_plate.png 420×148 退场，"
                         "素材保留不删）")
        els.append(e)
    scr = dict(old)
    scr["note"] = LOADING_NOTE
    scr["elements"] = els
    paths["22_loading.json"] = scr
    applied.append(("22_loading.json", len(els)))

    # ---------- 36 选择支 ----------
    old = json.load(io.open(os.path.join(SCR, "36_choices.json"), encoding="utf-8"))
    scr = dict(old)
    els = []
    for e in old["elements"]:
        e = json.loads(json.dumps(e, ensure_ascii=False))
        if e["id"] == "ch.choices":
            e["x"] = CHOICE_X
            e["y"] = CHOICE_Y
            e["w"] = CHOICE_W
            e["item_h"] = CHOICE_H
            e["gap"] = CHOICE_GAP
            e.pop("h", None)
            e["font"]["size"] = 44
            e["item_frame"] = {
                "asset": "ui/x_ui_psv_choice_norm.png",
                "nine": {"l": 0, "t": 0, "r": 0, "b": 0},
                "opacity": 255,
                "state_assets": {
                    "normal": "ui/x_ui_psv_choice_norm.png",
                    "hover": "ui/x_ui_psv_choice_sel.png",
                    "pressed": "ui/x_ui_psv_choice_sel.png",
                },
            }
            e["source"] = ("PSV系统UI参考\\超分2x\\otv_selwin.png（PSV 选择支两态条）→ 工具\\psv_make_assets.py "
                           "拆两态：ui/x_ui_psv_choice_norm.png（蓝紫）/ ui/x_ui_psv_choice_sel.png（粉）")
            e["note"] = CHOICES_NOTE
        els.append(e)
    scr["note"] = ("**M34（2026-09-21）· 按《交汇协奏曲》PSB 坐标 100% 复刻**（用户裁定：「完全复刻《交汇协奏曲》的 UI 系统…只是配色不同」）。\n"
                   "★ **M45e/M45f/M46 三轮回的终值**：本屏为**1 个 `list`**（项数自适应 + `max_rows:6` 翻页），"
                   "悬停/按下反馈走 `item_frame.state_assets`（逐项换图）。\n"
                   "★ **M45f 备注**：三行选项曾整体 y −170（470/570/670 → 300/400/500）；换 list 后 `y=300` 即承接该终值。\n"
                   "★ **M46**：`item_frame.state_assets{normal,hover,pressed}` ⇒ 逐项三态（回落链 pressed > hover > normal > asset）。\n"
                   + CHOICES_NOTE)
    scr["elements"] = els
    paths["36_choices.json"] = scr
    applied.append(("36_choices.json", len(els)))

    for fn, n in applied:
        p = os.path.join(SCR, fn)
        # ★ 行尾用 CRLF：`layout/screens/*.json` 全库为 CRLF（`gen_layout.py` 在 Windows 文本模式下
        #   写出的 `ui_layout.json`/`.tjs`/`.js` 同样是 CRLF）；写 LF 会让 git diff 变成"整文件重写"。
        with io.open(p, "w", encoding="utf-8", newline="\r\n") as f:
            json.dump(paths[fn], f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("  写出 %-18s 元素 %d 件" % (fn, n))
    print("[OK] 三屏已写出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
