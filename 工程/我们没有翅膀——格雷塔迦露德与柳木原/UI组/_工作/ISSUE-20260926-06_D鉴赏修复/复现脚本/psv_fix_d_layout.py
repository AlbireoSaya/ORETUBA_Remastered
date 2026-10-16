# -*- coding: utf-8 -*-
r"""psv_fix_d_layout.py —— D 组**修复轮**（ISSUE-20260926-06_D鉴赏修复）：28 / 37 / 39 布局数据修正。

Issue：`ISSUE-20260926-06_D鉴赏修复`（vision 四页鉴赏换皮不达标 → 逐条修复）。
落在 `_工作\...\复现脚本\`（一次性脚手架，照 D 组先例），**不入 `工具\`**。

**做什么**（只改这三屏；27/38 只动底图件，不动布局数据）：
① **37 立绘鉴赏**：把「面板边框横穿内容」的 5 处几何整体收进面板安全区（与面板边框 ≥6px），
   左右内边距对齐，末行补同款按钮框。**底图不动**（37 的底图无烘焙装饰，缺陷全在面板件与内容的相对几何）。
② **28 BGM**：8 控键 / 音量滑块重排 —— 消除信息框中部 75px 空区（控件整体居中、贴合信息框）。
③ **39 外壳**：四页签选中框改**统一固定宽度 171**（标签居中、中心位置不变）⇒ 切页不再「跳宽」。

**幂等**：全部目标值为**绝对常量**（不是「当前值 + 偏移」）；新增件带存在性判定 ⇒ 重复运行逐字节相同。

**证据/口径**（本脚本只写 layout JSON；底图件由 `工具\psv_fix_replay_bg.py` / `工具\psv_fix_music_bg.py` 处理）：
  · 37 面板件 `x_ui_dress_big_off.png`（466×278·nine l116/t69/r116/b69）实测：屏上可见边框
    左 x238..241 / 右 x962..967 / 上 y250..255 / 下 y555..558（元素框 (203,212,782,386) 时）
    ⇒ 可见内区 = 元素框 +(39,44)..+(w-24,h-44)；外框 = +(36,39)..+(w-20,h-39)。
  · 37 名单件 `x_ui_dress_name_off.png`（212×667·nine 全 0 ⇒ 整图缩放）实测：边框 src x13..14 / 197..198、
    y13..14 / 652..653 ⇒ 元素框 (X,Y,W,H) 的可见内区 = X+15·sx .. X+196·sx、Y+15·sy .. Y+651·sy（sx=W/212、sy=H/667）。
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)                      # _工作\ISSUE-20260926-06_D鉴赏修复
UI = os.path.dirname(os.path.dirname(WORK))       # <UI组>
SCR = os.path.join(UI, "layout", "screens")

# ---------------- 37: 面板与内容的安全区常量（绝对目标值） ----------------
# 面板件的可见边框相对元素框的内缩量（实测，见文件头）
BIG_IN = (39, 44, 24, 44)          # 左 / 上 / 右 / 下：可见内区相对元素框
BIG_OUT = (36, 39, 20, 39)         # 左 / 上 / 右 / 下：边框外沿相对元素框
NAME_SX, NAME_SY = 212.0, 667.0    # 名单件源尺寸（nine 全 0 ⇒ 整图缩放）
NAME_IN = (15, 15, 196, 651)       # 源内区（边框内侧）

DRE_BIG = (170, 173, 829, 460)     # 新主面板元素框（可见内区 209..975 × 217..590）
DRE_NAMELIST = (6, 201, 182, 446)  # 新名单底板元素框（可见内区 18.9..174.3 × 211.0..636.3）
DRE_ROW0_Y, DRE_ROW_STEP, DRE_ROW_H = 220, 60, 47
DRE_NAME_TX = (47, 120)            # 名单行文字 x / w（起点右移给 ▼ 让位；w 收进面板）
DRE_HIT_NAME = (12, 166)           # 名单行热区 x / w
DRE_SEL_MARK = (25, 232, 17, 23)   # ▼ 选中指示（收进面板内区）
DRE_FACE_PLAT = {"id": "dr.btn_face", "asset": "ui/x_ui_sqkey_s_off.png"}

# ---------------- 28: 信息框内控件重排 ----------------
MUS_INFO_IN_Y0, MUS_INFO_IN_Y1 = 228, 436   # 信息框可见内区（实测边框 222..227 / 437..440）
MUS_KEY_H, MUS_SLIDER_H, MUS_GAP = 59, 29, 26

# ---------------- 39: 页签选中框统一宽度 ----------------
SHELL_TAB_ON_W = 171               # = 最窄页签（tab1）自身宽度；最宽标签「BGM 鉴赏」两侧各 ≥12px
SHELL_TAB_ON_X = [360, 566, 815, 1068]          # 统一宽度后的 x（由「原 x + 原 w/2 − 171/2」取整而来）
SHELL_TAB_CX = [445.5, 651.0, 900.0, 1153.5]    # 各页签**标签中心**（未改，供 note 记录）


def load(name):
    with open(os.path.join(SCR, name), encoding="utf-8") as f:
        return json.load(f)


def save(d, name):
    p = os.path.join(SCR, name)
    raw = open(p, "rb").read()
    crlf = b"\r\n" in raw
    s = json.dumps(d, ensure_ascii=False, indent=2)
    if crlf:
        s = s.replace("\n", "\r\n")
    s += "\r\n" if crlf else "\n"
    with open(p, "wb") as f:
        f.write(s.encode("utf-8"))
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def by_id(d):
    return {e["id"]: e for e in d["elements"]}


def set_rect(e, t):
    e["x"], e["y"], e["w"], e["h"] = t


def note_append(d, mark, text):
    i = d["note"].find(mark)
    d["note"] = (d["note"][:i] if i >= 0 else d["note"]) + mark + text


# ============================================================
FIX37 = ("\n★ **修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）**"
         "：vision 实测「参数面板 / 名单底板 的**可见边框**（件内透明边距所致，不在元素框边缘）"
         "横穿我方内容」共 5 处 ⇒ 本轮把内容整体收进面板安全区（面板边框内侧 ≥6px）：")
FIX28 = ("\n★ **修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）**"
         "：vision 实测「信息框内控件与音量滑块之间 75px 空区（未画完观感）」⇒ 本轮把 8 控键与滑块"
         "**作为一组整体垂直居中**于信息框可见内区（228..436），组内间隙 26px：")
FIX39 = ("\n★ **修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）**"
         "：vision 实测「四页选中蓝块宽度 171/220/258/229 不等 ⇒ 切页跳宽、左右内边距不等」"
         "⇒ 本轮改为**统一固定宽度 171**（标签仍居中、四页标签中心不变）：")


def build_dress():
    d = load("37_dress.json")
    el = by_id(d)

    # ① 主面板：放大到把全部面板内容含在可见内区里（左右内边距对齐 8/8）
    set_rect(el["dr.big"], DRE_BIG)
    el["dr.big"]["note"] = (
        "主操作区面板底板。★ 修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）：**尺寸按"
        "「面板件可见边框」重算为 (170,173,829,460)**。根因：本件 `x_ui_dress_big_off.png` "
        "**自带透明边距**（466×278 画布内，可见边框只在 src x36..38 / x444..446 / y39..41 / y236..239），"
        "经 九宫格 l116/t69/r116/b69 铺到 (203,212,782,386) 后，**屏上可见边框**落在 "
        "左 x238..241 / 右 x962..967 / 上 y250..255 / 下 y555..558 —— 而元素框是 (203..985, 212..598) ⇒ "
        "可见内区只有 720×299（不是元素框的 782×386），面板内容（含 17 个按钮底板 + 4 条行标签 + "
        "7 行名单外的 22 文 17 热）总包围盒 x217..967 × y225..581 = 750×356，**装不进 720×299** ⇒ "
        "vision 实测到 4 处横穿（保留/隐藏 骑上边框、行标签 骑左边框、服装5 右内边距仅 2px、表情 01 压下边框）。"
        "本轮**不改任何内容元素的位置与尺寸**（派单要求 36 热区 action 仍空、31 文字语义不变），"
        "改为把底板放大到 (170,173,829,460) ⇒ 可见内区 209..975 × 217..589 = 766×372，"
        "内容 750×356 落入其中，**左右各 8px、上下各 8px 内边距（左右对齐）**。"
        "与相邻件净空：外框上沿 y212 距控制条热区底 y204 8px、左沿 x206 距名单底板外框右沿 x182 24px。"
        "素材仍是 466×278 / 九宫格不变（四角不拉伸）。"
        "　（历史）★ T3（2026-09-24，用户指令「dr.big 背景太小了！根本放不下那么多按钮」）："
        "矩形 (288,189) 672×278 → (204,164) 782×386。")
    # ② 名单底板：加高加宽起点，使 7 行名单落入可见内区（上下各 9px）
    set_rect(el["dr.namelist"], DRE_NAMELIST)
    el["dr.namelist"]["note"] = (
        "角色名列表底（PSB idx76 `名前/オフ`，x0 y184 w186 h641）（素材 212×667，nine 全 0 ⇒ **整图缩放**，"
        "sx=W/212、sy=H/667）。★ 修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）："
        "**元素框 (0,212,182,420) → (6,201,182,446)**。根因：本件同样**自带透明边距**"
        "（可见边框只在 src x13..14 / x197..198 / y13..14 / y652..653），经整图缩放后**屏上可见内区**"
        "只有 x12.9..168.3 × y221.5..621.9（≈155×400），而 7 行名单（行框 47 高、步进 60）从 y209 到 y616"
        "共 407px ⇒ 第 1 行文字（墨迹 y≈219..247）正好被**上边框 y≈221.5** 横穿（vision 实测 ①）。"
        "本轮把底板改为 (6,201,182,446) ⇒ sy=0.66867、可见内区 x18.9..174.3 × y211.0..636.3；"
        "同时名单 7 行整体下移 **+11**（行框 220..627）⇒ 上下各留 **9.0 / 9.3px** 内边距。"
        "横向 +6px 是为把 ▼ 选中指示与行文字一起收进可见内区（见 `dr.sel_mark` / `dr.name_tx_*`）。")
    # ③ 名单 7 行：整体 +11，文字起点 +13、宽度收进面板；热区随之
    for k in range(1, 8):
        y = DRE_ROW0_Y + DRE_ROW_STEP * (k - 1)
        tx = el["dr.name_tx_%d" % k]
        tx["x"], tx["y"], tx["w"], tx["h"] = DRE_NAME_TX[0], y, DRE_NAME_TX[1], DRE_ROW_H
        tx["note"] = (tx["note"].split("　★ T2")[0]
                      + "　★ T2（2026-09-24）：名单 11→7 行。"
                        "　★ 修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）：行框整体下移 +11"
                        "（y209→220 起步进仍 60），x34→47、w192→120，收进名单底板可见内区"
                        "（x18.9..174.3）并给左侧 ▼ 让位 ⇒ 首行文字不再被上边框横穿。")
        hit = el["dr.hit_name_%d" % k]
        hit["x"], hit["y"], hit["w"], hit["h"] = DRE_HIT_NAME[0], y, DRE_HIT_NAME[1], DRE_ROW_H
        assert hit["action"] == "", hit["id"]
    set_rect(el["dr.sel_mark"], DRE_SEL_MARK)
    MARK_SEL = "　★ 修复轮（2026-09-26）：x9→25、y221→232（随名单行 +11）"
    if MARK_SEL not in el["dr.sel_mark"]["note"]:      # 幂等：notes 只在首次追加
        el["dr.sel_mark"]["note"] += (MARK_SEL + "，使「▼」落入名单底板可见内区（左内边距 7px）。")
    # ④ 末行补同款按钮框（与其余各行按钮底板同素材同九宫格）
    spec = dict(el["dr.btn_keep"])
    spec.update({"id": DRE_FACE_PLAT["id"], "asset": DRE_FACE_PLAT["asset"],
                 "x": el["dr.face_tx"]["x"], "y": el["dr.face_tx"]["y"],
                 "w": el["dr.face_tx"]["w"], "h": el["dr.face_tx"]["h"]})
    spec["source"] = el["dr.btn_keep"]["source"]
    spec["note"] = ("**末行「表情」名槽的按钮底板**（★ 修复轮 2026-09-26 · ISSUE-20260926-06_D鉴赏修复 新增）。"
                    "vision 实测 ⑤：「末行『表情 01』文字压住下边框，且该行无按钮框（其余四行有）」⇒ "
                    "本轮按**其余各行按钮完全同款**补件：同素材 `ui/x_ui_sqkey_s_off.png`、"
                    "同九宫格 l13/t12/r13/b12、同 z=20，几何 = `dr.face_tx` 逐像素同矩形 "
                    "(%d,%d,%d,%d)；文字（`dr.face_tx`，z=25）仍在其上。"
                    "机制面无影响：本件是**纯装饰 image**，不带 action / state_group、不参与命中"
                    "（hit 集合与 action 一字未改）。"
                    % (spec["x"], spec["y"], spec["w"], spec["h"]))
    assert spec["nine"] == el["dr.btn_keep"]["nine"], "同款要求九宫格一致"
    if DRE_FACE_PLAT["id"] in el:
        el[DRE_FACE_PLAT["id"]].update(spec)
    else:
        d["elements"].insert(d["elements"].index(el["dr.big"]) + 1, spec)

    # ⑤ 自检：内容包围盒 ⊂ 面板可见内区（含 ≥6px 内边距）
    el = by_id(d)
    big_in = (DRE_BIG[0] + BIG_IN[0], DRE_BIG[1] + BIG_IN[1],
              DRE_BIG[0] + DRE_BIG[2] - BIG_IN[2], DRE_BIG[1] + DRE_BIG[3] - BIG_IN[3])
    panel_ids = [e["id"] for e in d["elements"]
                 if not e["id"].startswith(("dr.name_tx_", "dr.hit_name_", "dr.sel_mark"))
                 and e["id"] not in ("dr.bg", "dr.namelist", "dr.ctrl", "dr.big", "dr.reset",
                                     "dr.reset_tx", "dr.hit_reset", "dr.time_day",
                                     "dr.time_dusk", "dr.time_night", "dr.time_night2",
                                     "dr.hit_ctrl_left", "dr.hit_ctrl_bg", "dr.hit_ctrl_right",
                                     "dr.hit_ctrl_time", "dr.hit_ctrl_text", "dr.hit_ctrl_textwin",
                                     "dr.hit_ctrl_capture", "dr.hit_ctrl_save", "dr.hit_ctrl_load",
                                     "dr.hit_ctrl_hide", "dr.hit_ctrl_help")]
    xs0 = min(el[i]["x"] for i in panel_ids)
    ys0 = min(el[i]["y"] for i in panel_ids)
    xs1 = max(el[i]["x"] + el[i]["w"] for i in panel_ids)
    ys1 = max(el[i]["y"] + el[i]["h"] for i in panel_ids)
    assert xs0 >= big_in[0] and ys0 >= big_in[1] and xs1 <= big_in[2] and ys1 <= big_in[3], \
        "面板内容出安全区：内容 (%d,%d)-(%d,%d)  vs 内区 %s" % (xs0, ys0, xs1, ys1, big_in)
    assert (xs0 - big_in[0]) == (big_in[2] - xs1), \
        "左右内边距未对齐：L%d R%d" % (xs0 - big_in[0], big_in[2] - xs1)
    sx, sy = DRE_NAMELIST[2] / NAME_SX, DRE_NAMELIST[3] / NAME_SY
    nl_in = (DRE_NAMELIST[0] + NAME_IN[0] * sx, DRE_NAMELIST[1] + NAME_IN[1] * sy,
             DRE_NAMELIST[0] + NAME_IN[2] * sx, DRE_NAMELIST[1] + NAME_IN[3] * sy)
    r0 = el["dr.name_tx_1"]
    r7 = el["dr.name_tx_7"]
    assert r0["y"] - nl_in[1] >= 6, "名单首行距上边框 %d < 6" % (r0["y"] - nl_in[1])
    assert nl_in[3] - (r7["y"] + r7["h"]) >= 6, "名单末行距下边框 %d < 6" % (nl_in[3] - (r7["y"] + r7["h"]))

    hits = [e for e in d["elements"] if e["kind"] == "hit"]
    txts = [e for e in d["elements"] if e["kind"] == "text"]
    assert len(hits) == 36, len(hits)
    assert len(txts) == 31, len(txts)
    assert all(e["action"] == "" for e in hits)
    note_append(d, FIX37, (
        "① **名单底板** (0,212,182,420)→**(6,201,182,446)**（可见内区 18.9..174.3 × 211.0..636.3）；"
        "**7 行名单整体 +11**（行框 220..627）、文字 **x34→47 / w192→120**、热区 **(12,y,166,47)**、"
        "▼ `dr.sel_mark` **(25,232)** ⇒ 首行文字距上边框 **9px**、末行距下边框 **9.3px**（改前首行文字被上边框横穿）。"
        "② **主面板** (203,212,782,386)→**(170,173,829,460)**：可见内区 209..975 × 217..590（766×373）。"
        "行标签（x217..271）距左边框 8px（改前骑在左边框 x240 上）；保留/隐藏（y225..281）距上边框 8px"
        "（改前横跨上边框 y251..253）；服装5 右缘 967 距右边框 8px、服装1 左缘 276 距…"
        "**面板内容包围盒 217..967 左右内边距各 8px（改前右 2px / 左 41px，严重不对称）**。"
        "③ **末行补按钮框**：新增 `dr.btn_face`（image，同素材同九宫格同 z=20，几何 = `dr.face_tx` 同矩形）；"
        "`dr.face_tx` 底沿 y581 距下边框 9px（改前 y538..557 压住下边框 555..558）。"
        "④ **不动项**：36 个 hit 的 action 仍为空串、31 个 text 的语义与几何全部未改、底图未改；"
        "元素总数 93→94（仅新增纯装饰 image 一件）。"))

    # 37 has no page_flag; keep as-is
    return save(d, "37_dress.json")


def build_music():
    d = load("28_music.json")
    el = by_id(d)
    h = MUS_KEY_H
    y0 = MUS_INFO_IN_Y0 + (MUS_INFO_IN_Y1 - MUS_INFO_IN_Y0 - (h + MUS_GAP + MUS_SLIDER_H)) // 2
    keys_y = y0
    slider_y = y0 + h + MUS_GAP
    for e in d["elements"]:
        eid = e["id"]
        if eid.startswith("mu.pb_") and e["kind"] in ("image", "hit"):
            e["y"] = keys_y
        elif eid == "mu.vol":
            e["y"] = slider_y
        elif eid == "mu.vol_hit":
            e["y"] = slider_y - 9
    assert keys_y == 275 and slider_y == 360, (keys_y, slider_y)
    MARK_VOL = "　★ 修复轮（2026-09-26）：滑块 y385→**360**"
    if MARK_VOL not in (el["mu.vol"].get("note") or ""):   # 幂等：notes 只在首次追加
        el["mu.vol"]["note"] = (el["mu.vol"].get("note", "")
                                + MARK_VOL + "（随控件组居中重排）。")
    note_append(d, FIX28, (
        "8 控键 y253→**275**（59 高 ⇒ 275..334）、音量滑块 y385→**360**、其热区 y376→**351**；"
        "改前 控键底 312 与滑块顶 385 之间 **73px 空区**（vision 实测 75px），改后组内间隙 **26px**、"
        "上下内边距 **47/47px**（组整体垂直居中于可见内区 228..436）⇒ 空区消除、观感不再「未画完」。"
        "**不动项**：8 个 `bgm_*` action、`page_flag`、逐项三态 `item_frame`、行内播放键 `item_buttons`、"
        "列表框几何（169,504,1580,419）与 21 首/页 × 3 页分页全部未改；控件与滑块 x 坐标未动。"))
    return save(d, "28_music.json")


def build_shell():
    d = load("39_gal_shell.json")
    el = by_id(d)
    for i in range(4):
        on = el["gs.tab%d_on" % (i + 1)]
        if not (on["w"] == SHELL_TAB_ON_W and on["x"] == SHELL_TAB_ON_X[i]):
            # 首次运行：必须是「D 轮输出」的原形（原宽 + 原中心），否则报错（不静默按现值猜）
            assert on["w"] in (171, 220, 258, 229), on["w"]
            assert on["x"] + on["w"] / 2.0 == SHELL_TAB_CX[i],                 "第 %d 页签原中心 %s ≠ 常量 %s" % (i + 1, on["x"] + on["w"] / 2.0, SHELL_TAB_CX[i])
        cx = SHELL_TAB_CX[i]                                 # ★ 用常量（不用「当前值」），逐次运行结果相同
        nx = SHELL_TAB_ON_X[i]
        on["x"], on["w"] = nx, SHELL_TAB_ON_W
        on["note"] = ("页签 %d 的**选中指示**（承载屏 = %s 时显示，`vis_flag:gal_tab`）。"
                      "★ 修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）：**几何改为"
                      "「统一固定宽度 %d × 高 76」并让标签居中**——改前选中框 = 页签全宽"
                      "（171/220/258/229 四值不等，块内左右内边距 26/28、37/38、65/67、50/53 亦不等），"
                      "vision 实测「切页跳宽 + 内边距不等」；现四条选中框**宽度全部 = %d**，"
                      "中心 = 该页签标签中心 (%.1f)（整数栅格取整，偏差 ≤0.5px）⇒ 切页不再跳宽。"
                      "宽度取 171 = 最窄页签自身宽度（选中框不外溢到相邻页签、也不超自身热区）；"
                      "最宽标签「BGM 鉴赏」两侧仍各留 ≥12px。**页签文字 / 热区几何与 action 一字未改。**"
                      % (i + 1, ["gallery", "music", "dress", "replay"][i], SHELL_TAB_ON_W,
                         SHELL_TAB_ON_W, cx))
    ents = [e for e in d["elements"] if e["kind"] == "hit"]
    assert len(ents) == 5 and len(d["elements"]) == 17
    assert all(el["gs.tab%d_on" % (i + 1)]["w"] == SHELL_TAB_ON_W for i in range(4))
    for i in range(4):
        t = el["gs.tab%d_tx" % (i + 1)]
        on = el["gs.tab%d_on" % (i + 1)]
        err = abs((on["x"] + on["w"] / 2.0) - (t["x"] + t["w"] / 2.0))
        assert err <= 0.5, "标签未居中（第 %d 页签，偏差 %.1f）" % (i + 1, err)
    note_append(d, FIX39, (
        "四条选中框宽度由 **171/220/258/229 → 全部 171**（x = 360 / 566 / 815 / 1068，y12 h76）；"
        "中心 = 各页签标签中心 445.5 / 651 / 900 / 1153.5（整数栅格取整，偏差 ≤0.5px）⇒ **切页不跳宽**；"
        "页签文字（`gs.tab*_tx`）、热区（`gs.tab*_hit`）与 action（`gallery_tab_1..4` / `close`）"
        "**几何与语义一字未改**，元素总数仍 17、热区仍 5。"))
    return save(d, "39_gal_shell.json")


def main():
    res = [("37_dress.json", build_dress()), ("28_music.json", build_music()),
           ("39_gal_shell.json", build_shell())]
    for k, v in res:
        print("%-20s md5=%s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
