# -*- coding: utf-8 -*-
r"""m09_apply_config.py —— ISSUE-20260926-09 · 25 设置屏：药丸底图合并 + 左列内移 + 三处删除/合并

**幂等**：已应用 ⇒ 只报不写（退出码 0）；部分应用 ⇒ 补做未做的那部分。
**写盘前断言**：盘上每个目标字段的值必须 ∈ {旧值, 新值}（含**已作废的中间值**），否则报错停手。

改动共两轮：

  == 第一轮（2026-09-26，用户裁决）==
  A. 药丸底图 14 件 → 1 支共用件（asset + source）
  B. 左列内移：+30 × 103（x=136/146/196/230/716/847），+20 × 5（x=937 首行「全屏模式」组，
     当时的「唯一例外」——已由第二轮订正②作废）
  C. 三处删除/合并：删 `title_sys`/`title_snd`/`sec_confirm`；删 `tab1_tx_sel`/`tab2_tx_sel`，
     `tab1_tx`/`tab2_tx` 去 `vis_flag`+`vis_when` 改两页常显
  D. 110 处元素 note ＋ 屏级 note 追加

  == 第二轮（2026-09-26，用户对三处副作用的裁决）==
  ② 首行「全屏模式」组**移 +30 并收窄**：x 957 → 967、w 221 → 195（`_hit` 同改）
     ⇒ 组内间距 6px → **16px**（与其余 7 行一致）；右沿 1162（离右列 x=1180 留 18px）。
  ① 声音页左列滑条族**移 +30 并收窄**（24 件，与订正② 同款做法）：
       · 轨 `cfg.sl_<行>`（6）：x 732 → **762**，w 360 → **330** ⇒ 右沿仍 **1092**
       · 热区 `cfg.sl_<行>_hit`（6）：x 722 → **752**，w 380 → **350** ⇒ 右沿仍 **1102**
       · MIN 端点 `cfg.sl_<行>_end_lo`（6）：x 732 → **762**（w/h/y/z 不动）
       · MAX 端点 `cfg.sl_<行>_end_hi`（6）：**不动**（1046..1092，仍贴轨右端 = 右沿对齐不变）
       ⇒ 药丸右沿 726 ↔ 轨左沿 **762 = 36px**（恢复改前 696↔732）；
         `tag_snd_0N × sl_*_hit` 180 → **0 px²**；与角色列/banner（x=1110）**新增相交 0 对**。
     **只移不收窄**会造成轨右端 1092 → 1122、侵入角色列 12px（21 对可见 + 27 对 hit 新增）——
     这是本 issue 的一轮「停手并报告」结论（见 `取证\订正①_停手_放行新增相交清单.txt`），
     用户据此裁决改走「收窄」路线。
  ③ `layout\_schema.md` 的 125 → 147：**由主代理自行改动，本脚本不碰。**

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python "_工作\ISSUE-20260926-09_config\复现脚本\m09_apply_config.py"          # 应用
    python "_工作\ISSUE-20260926-09_config\复现脚本\m09_apply_config.py" --check  # 只检
"""
import argparse
import copy
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
MARK = "ISSUE-20260926-09"
MARK2 = "ISSUE-20260926-09·订正"                        # 第二轮块标记（判幂等）
MARK2A = "ISSUE-20260926-09·订正①·移+30并收窄"          # 订正①「已落地」标记
SENT2 = "**★ ISSUE-20260926-09·订正（2026-09-26"        # 第二轮块起始句（整块可重写）

PILL_NEW_ASSET = "ui/x_ui_psv_pill_blank.png"
PILL_NEW_SRC = ("用户 2026-09-26 裁定采用的**生图去字版**："
                "`_工作\\ISSUE-20260926-09_药丸底图\\取证\\_ai_fit.png`（纹理=生图 / alpha=原图，"
                "560×72 RGBA）→ `_工作\\ISSUE-20260926-09_config\\复现脚本\\m09_pill_blank.py`"
                "（RGB `&0xFC` 降色深 + alpha 逐字节不动 + optimize=True/compress_level=9）")

ROWS = ["display", "facewindow", "drama", "effect", "voicecut", "curhide", "savedialog", "loaddialog"]
SLD_ROWS = ["master", "bgm", "se", "sysse", "voice", "char"]
SLD_LABEL = {"master": "主音量", "bgm": "背景音乐", "se": "音效",
             "sysse": "系统音效", "voice": "主音量（语音）", "char": "角色音量"}

PILL_IDS = ["cfg.tag_sys_%02d" % n for n in range(1, 9)] + ["cfg.tag_snd_%02d" % n for n in range(1, 7)]
SEC_IDS = ["cfg.sec_picture", "cfg.sec_volume", "cfg.sec_voice"]
SPK_IDS = ["cfg.snd_vol_se_spk", "cfg.snd_vol_sysse_spk", "cfg.snd_vol_voice_spk", "cfg.snd_vol_char_spk"]
LB_IDS = (["cfg.row_%s_lb" % r for r in ROWS]
          + ["cfg.snd_vol_%s_lb" % k for k in ("master", "bgm", "se", "sysse", "voice", "char")])
COVER_IDS = ["cfg.cover_c2_05"]
ON_IDS = ["cfg.o_%s_on%s" % (r, s) for r in ROWS for s in ("", "_hit", "_tx", "_tx_sel")]
OFF_IDS = ["cfg.o_%s_off%s" % (r, s) for r in ROWS[1:] for s in ("", "_hit", "_sel", "_tx", "_tx_sel")]
DISPLAY_IDS = ["cfg.o_display_off%s" % s for s in ("", "_hit", "_sel", "_tx", "_tx_sel")]

SLD_RAIL_IDS = ["cfg.sl_%s" % r for r in SLD_ROWS]
SLD_HIT_IDS = ["cfg.sl_%s_hit" % r for r in SLD_ROWS]
SLD_LO_IDS = ["cfg.sl_%s_end_lo" % r for r in SLD_ROWS]
SLD_HI_IDS = ["cfg.sl_%s_end_hi" % r for r in SLD_ROWS]
SLD_IDS = SLD_RAIL_IDS + SLD_HIT_IDS + SLD_LO_IDS + SLD_HI_IDS

# 锚点 → (id 列表, Δ)；**滑条族另用 SLD_MOVE / SLD_WIDTH 处理**（因为要同时收窄）
SPANS = [
    (136, 30, PILL_IDS + SEC_IDS),
    (146, 30, SPK_IDS),
    (196, 30, LB_IDS),
    (230, 30, COVER_IDS),
    (716, 30, ON_IDS),
    (847, 30, OFF_IDS),
    (937, 30, DISPLAY_IDS),            # ★ 订正②：由 +20 改为 +30（并收窄 w）
]
# 订正①：x 位移（轨道 / 热区 / MIN 端点）；MAX 端点（_end_hi）**不动**
SLD_MOVE = {}
for _r in SLD_ROWS:
    SLD_MOVE["cfg.sl_%s" % _r] = (732, 762)
    SLD_MOVE["cfg.sl_%s_hit" % _r] = (722, 752)
    SLD_MOVE["cfg.sl_%s_end_lo" % _r] = (732, 762)
# 订正②：首行组宽度收窄；订正①：轨 / 热区宽度收窄
WIDTH_NEW = {i: 195 for i in DISPLAY_IDS}
WIDTH_OLD_ACCEPT = {i: {221, 195} for i in DISPLAY_IDS}
for _r in SLD_ROWS:
    WIDTH_NEW["cfg.sl_%s" % _r] = 330
    WIDTH_OLD_ACCEPT["cfg.sl_%s" % _r] = {360, 330}
    WIDTH_NEW["cfg.sl_%s_hit" % _r] = 350
    WIDTH_OLD_ACCEPT["cfg.sl_%s_hit" % _r] = {380, 350}

# 已作废的中间值（第一轮的「+20 例外」落点）——仍视为合法「旧值」，避免历史态无法复跑
INTERMEDIATE = {i: [957] for i in DISPLAY_IDS}

DELETE_IDS = ["cfg.title_sys", "cfg.title_snd", "cfg.sec_confirm", "cfg.tab1_tx_sel", "cfg.tab2_tx_sel"]
TABTX = {"cfg.tab1_tx": "系统", "cfg.tab2_tx": "声音"}

MOVE = {}                            # id -> (new_x, delta, anchor, allowed_old_xs)
for _ax, _d, _ids in SPANS:
    for _i in _ids:
        MOVE[_i] = (_ax + _d, _d, _ax, {_ax} | set(INTERMEDIATE.get(_i, [])))
for _i, (_ox, _nx) in SLD_MOVE.items():
    MOVE[_i] = (_nx, _nx - _ox, _ox, {_ox})

RIGHT_SLD_IDS = ["cfg.sl_%s%s" % (k, s) for k in ("winopac", "textspeed", "autospeed")
                 for s in ("", "_hit", "_end_lo", "_end_hi")]

# ★ 订正① 配套：轨的 `rail.nine` 全零 —— 让 `w=330`（≠ 素材实宽 360）合法
#   依据：`verify_ui.py` [2]「slider 的 rail 无 nine ⇒ 元素 w 必须 = rail PNG 实宽」（否则判「静默横向拉伸」）；
#         `ui_widget.tjs` 只在 `nine === void` 时才登记「缩放元素」；全零 nine 在 `uiWidgetNine`
#         里退化为**唯一一块整图 blit**（其余 8 块因 dw/dh=0 被跳过）⇒ 与「按 1:1 缩放」**渲染完全一致**，
#         但不再被两道闸门判为缺陷。`复刻/replica.js` 亦显式支持全零 nine（`isZeroNine` ⇒ `background-size:100% auto`）。
#   先例：`ui_flow_data.tjs` 的流程图方框即用 `nine:{l:0,t:0,r:0,b:0}` 表达「整图缩放」。
RAIL_NINE = {"l": 0, "t": 0, "r": 0, "b": 0}

SLD_NOTE_HEAD = "★ ISSUE-20260926-09·订正（2026-09-26，用户裁决·第二轮）：**声音页左列滑条族"


def pill_asset_old(eid):
    n = int(eid[-2:])
    return "ui/x_ui_psv_pill_c1_%02d.png" % n if eid.startswith("cfg.tag_sys_") else "ui/x_ui_psv_pill_c2_%02d.png" % n


def pill_src_old(eid):
    n = int(eid[-2:])
    pg = 1 if eid.startswith("cfg.tag_sys_") else 2
    return "PSV系统UI参考\\去字件\\2x\\bgc%02d_pill_%02d.png（无字药丸壳）→ 工具\\m53" % (pg, n)


def note_append(e, text, mark):
    if mark in (e.get("note") or ""):
        return False
    e["note"] = (e.get("note") or "") + "\n\n" + text
    return True


# ── 第一轮 note 文案 ──────────────────────────────────────────────────
def note_pill(eid, ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**药丸底图 14 件合 1 支共用件** —— `asset` 由 `%s`"
            "（该件自带**去字残留**：补块亮斑 + 残存笔画）改为 `%s`（用户 2026-09-26 裁定采用的"
            "生图去字版；560×72 RGBA、纹理=生图 / alpha=原图、RGB `&0xFC` 降色深、alpha 逐字节不动、"
            "1:1 摆放无九宫格）。旧 14 件已**移动**（未删除、字节不变）至 "
            "`_工作\\ISSUE-20260926-09_药丸底图\\旧素材归档\\`。**同批左列内移 +30**：x %d → %d"
            "（面板内沿实测 x=160 亮边线，原 x=136 探出面板 ⇒ 用户裁定「药丸 + 分节标题一起内移」，"
            "值按钮同步跟随；y/w/h/z 不变）。" % (MARK, pill_asset_old(eid), PILL_NEW_ASSET, ox, nx))


def note_sec(ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +30** —— x %d → %d；与药丸壳同批内移进面板"
            "（面板内沿实测 x=160 亮边线，原 x=136 探出面板约 24–30px）；y/w/h/z 不变。"
            "同批口径：14 件药丸壳合 1 支共用件 `%s`；复现脚本与证据见 "
            "`_工作\\ISSUE-20260926-09_config\\`。" % (MARK, ox, nx, PILL_NEW_ASSET))


def note_spk(ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +30** —— x %d → %d；跟随药丸壳内移进面板"
            "（面板内沿实测 x=160）；y/w/h/z 不变。同批口径：14 件药丸壳合 1 支共用件 `%s`。"
            % (MARK, ox, nx, PILL_NEW_ASSET))


def note_lb(ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +30** —— x %d → %d；行名叠在药丸壳之内，"
            "随壳内移（改后壳 x166..726，本行名框 x226..666 仍在壳内）；y/w/h/z 不变。"
            "同批口径：14 件药丸壳合 1 支共用件 `%s`。" % (MARK, ox, nx, PILL_NEW_ASSET))


def note_cover(ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +30** —— x %d → %d；盖槽片随左列整体内移，"
            "仍盖住页面里烘焙的旧滑槽带；y/w/h/z 不变。同批口径：14 件药丸壳合 1 支共用件 `%s`。"
            % (MARK, ox, nx, PILL_NEW_ASSET))


def note_on(ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +30** —— x %d → %d；本组为左列值按钮"
            "「窗口模式（window）」一族，随药丸内移，**与药丸右沿的相对间距不变**"
            "（改前 药丸右沿 696 ↔ 本按钮左沿 716 = 20px；改后 726 ↔ 746 = 20px）；y/w/h/z 不变。"
            "同批口径：14 件药丸壳合 1 支共用件 `%s`。" % (MARK, ox, nx, PILL_NEW_ASSET))


def note_off(ox, nx):
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +30** —— x %d → %d；本组为左列**第 2–8 行**"
            "「全屏模式（full）」值按钮家族（`_off`/`_off_sel`/`_off_tx`/`_off_tx_sel`/`_off_hit`），"
            "随药丸内移；y/w/h/z 不变。**注意**：左列第 1 行同族（`cfg.o_display_off*`）第一轮曾只移 "
            "+20，已由第二轮订正②改为 +30 并收窄，见该元素 note。" % (MARK, ox, nx))


def note_display(ox, nx):
    """第一轮的「+20 例外」文案（已被订正②作废；保留以便从原形重跑时留痕）"""
    return ("★ %s（2026-09-26，用户裁决）：**左列内移 +20（唯一例外，碰撞规避）** —— x %d → %d。"
            "本组是左列第 1 行「全屏模式」值按钮家族（w=221 ⇒ 右沿 %d）；整列 +30 会让右沿到 %d，"
            "压上右列 `cfg.sec_text`(x=1180) ⇒ 本组**只 +20**（右沿 %d < 1180），其余左列元素照 +30。"
            "y/w/h/z 不变。同批口径：14 件药丸壳合 1 支共用件 `%s`。"
            "（**注**：本节结论已被同 issue 第二轮订正②改写——改为 +30 并收窄，见下方订正段。）"
            % (MARK, ox, nx, ox + 221, ox + 30 + 221, nx + 221, PILL_NEW_ASSET))


def note_tabtx(eid, sample):
    base = eid[:eid.index("_tx")]        # cfg.tab1 / cfg.tab2
    return ("★ %s（2026-09-26，用户裁决）：**页签文字合并成一个常显元素** —— 删除 `%s_tx_sel`"
            "（原**选中态**页签名）；本元素（`%s`，sample「%s」）**去掉 `vis_flag` + `vis_when`**"
            "改为**两页常显**（选中与否完全由底件 `%s_on`/`%s_off` 区分——实测 `tab_off` 中心 "
            "alpha=0＝空心描边、`tab_on`＝实心蓝药丸）；颜色保持 `@palette.psv_ink` 不动。"
            "同批口径：14 件药丸壳合 1 支共用件 `%s`。"
            % (MARK, base, eid, sample, base, base, PILL_NEW_ASSET))


# ── 第二轮订正 note 文案 ──────────────────────────────────────────────
def note_display_fix(nx, w_old, w_new):
    return ("★ %s（2026-09-26，用户裁决·第二轮，**作废上一段的「+20 例外」**）：**首行「全屏模式」组"
            "移 +30 并收窄** —— x 957 → **%d**（= 原 937 +30）、w %d → **%d**（`cfg.o_display_off_hit` 同改）。"
            "**目的**：① 该组内间距恢复为 **16px**（与其余 7 行一致）——`cfg.o_display_on` 右沿 951 ↔ "
            "本组左沿 %d = 16px；② 右沿 **%d**，与右列 `cfg.sec_text`(x=1180) 留 **18px**，"
            "不再需要「+20」这种例外。y/h/z/asset/action/font/vis 系列一律未动；文字 `align`/`valign` "
            "保持原值（居中），故文字仍**自动居中于新框**（新框中心 %d，旧框中心 1067.5）。"
            % (MARK2, nx, w_old, w_new, nx, nx + w_new, nx + w_new / 2.0))


def note_slider_fix(r, kind, ox, nx, w_old, w_new):
    lab = SLD_LABEL.get(r, r)
    if kind == "rail":
        return ("★ %s（2026-09-26，用户裁决·第二轮）：**声音页左列滑条族「移 +30 并收窄」** —— "
                "x %d → **%d**、w %d → **%d**（%s 行的滑轨）。**因碰撞改为移 +30 并收窄 30px、右沿不变**："
                "只移不收窄会让轨右端 1092 → 1122，**侵入右邻角色列/banner（x=1110）12px**"
                "（实测 21 对可见件 + 27 对 hit 层新增相交，见 "
                "`取证\\订正①_停手_放行新增相交清单.txt`）；收窄后右沿仍 **1092**，左端内移 ⇒ "
                "「药丸右沿 726 ↔ 轨左沿 %d」= **36px**（恢复改前 696↔732）且**零新增相交**。"
                "与订正②（首行 w 221→195）同款做法。\n"
                "  ★ **同步补 `rail.nine = {l:0,t:0,r:0,b:0}`（全零）**：`w=330` 已不等于素材实宽 360，"
                "而 `verify_ui.py` [2] 明文「slider 的 rail **无 nine** ⇒ 元素 w 必须 = rail PNG 实宽"
                "（否则静默横向拉伸）」，且引擎只在 `nine` 缺失时才登记「缩放元素」。全零 nine 在 "
                "`uiWidgetNine` 里退化为唯一一块整图 blit（其余 8 块 dw/dh=0 被跳过）⇒ **渲染与"
                "「按原样缩放」逐像素一致**，但不再被判缺陷；HTML 侧 `replica.js` 亦有 `isZeroNine` "
                "分支走 `background-size:100%% auto`。**先例**：流程图方框（`ui_flow_data.tjs`）即用全零 nine "
                "表达「整图缩放」。\n"
                "  y/h/z/asset/action/font/vis 不变（`nine` 是本轮为满足 w=330 而**唯一新增**的字段，"
                "已在实测与两端代码上核准）。"
                % (MARK2A, ox, nx, w_old, w_new, lab, nx))
    if kind == "hit":
        return ("★ %s（2026-09-26，用户裁决·第二轮）：**声音页左列滑条族「移 +30 并收窄」** —— "
                "x %d → **%d**、w %d → **%d**（%s 行的滑块热区）。热区**必须与可视轨同步收窄**，"
                "否则右沿会由 1102 涨到 1132 而越界；改后右沿仍 **1102**，仍完整覆盖轨（%d..%d）。"
                "y/h/z/asset/action/vis 不变。" % (MARK2A, ox, nx, w_old, w_new, lab, nx, nx + w_new))
    if kind == "end_lo":
        return ("★ %s（2026-09-26，用户裁决·第二轮）：**声音页左列滑条族「移 +30 并收窄」** —— "
                "x %d → **%d**（%s 行的 MIN 端点文字）。随轨左端内移（轨 %d..%d），仍是「贴轨左端」；"
                "w/h/y/z/font/align 不变。" % (MARK2A, ox, nx, lab, nx, nx + 330))
    return ("★ %s（2026-09-26，用户裁决·第二轮）：**声音页左列滑条族「移 +30 并收窄」—— 本件不动** —— "
            "%s 行的 MAX 端点文字（x=1046..1092）**保持原位**：收窄后轨仍为 ..1092 ⇒ 本件**右沿与轨右端"
            "对齐关系不变**（原设计即如此）。故 x/w/y/h/z 全部未动；同批 24 件里只有本 6 件（MAX）不位移。"
            % (MARK2A, lab))


SCREEN_NOTE2 = """

---

**★ ISSUE-20260926-09·订正（2026-09-26，用户对三处副作用的裁决）—— 本节**追加**，上文（第一轮及更早记录）保留不改**

**订正② · 首行「全屏模式」组移 +30 并收窄（5 件）——【已落地】**
· `cfg.o_display_off` / `_off_sel` / `_off_tx` / `_off_tx_sel` / `_off_hit`：x 957 → **967**、w 221 → **195**（含 `_hit`）。
· **效果**：`cfg.o_display_on` 右沿 951 ↔ 本组左沿 967 = **16px**，与其余 7 行（如 facewindow：`_on` 861 ↔ `_off` 877）**完全一致**；本组右沿 **1162**，与右列 `cfg.sec_text`(x=1180) 留 18px、与 `cfg.row_winopac_lb`(x1180 y254 h30) 零相交。
· 第一轮写的「+20 例外（x=957，右沿 1178）」**已作废**。
· `y/h/z/asset/action/font/vis` 未动；`_off_tx`/`_off_tx_sel` 的 `align:"center"` / `valign:"middle"` 未改 ⇒ 文字仍自动居中于新框；实机墨迹中心 1063.5 vs 框中心 1064.5（−1.0px）。

**订正① · 声音页左列滑条族「移 +30 并收窄」（24 件）—— ISSUE-20260926-09·订正①·移+30并收窄【已落地】**
· **逐类**（行 = `master / bgm / se / sysse / voice / char`）：
  · 轨 `cfg.sl_<行>`（6）：x 732 → **762**、w 360 → **330** ⇒ 右沿仍 **1092**。
  · 热区 `cfg.sl_<行>_hit`（6）：x 722 → **752**、w 380 → **350** ⇒ 右沿仍 **1102**、仍完整覆盖轨。
  · MIN 端点 `cfg.sl_<行>_end_lo`（6）：x 732 → **762**（w/h/y/z 不动）⇒ 仍贴轨左端。
  · MAX 端点 `cfg.sl_<行>_end_hi`（6）：**不动**（1046..1092）⇒ 右沿仍与轨右端 1092 对齐。
· **效果**：药丸右沿 726 ↔ 轨左沿 **762 = 36px**（恢复改前 696↔732）；`cfg.tag_snd_0N × cfg.sl_*_hit` **180 → 0 px²**；与角色列/banner（x=1110）、`cfg.ch_*` 名条列、右列全部元素**新增相交 = 0 对（可见件与 hit 层皆 0）**。
· **为什么是「移 +30 并收窄」而不是「只移 +30」**：只移不收窄会让轨右端 1092 → 1122、`_hit` 右端 1102 → 1132，**侵入角色列/banner（x=1110）12px**——实测新增 **21 对可见件 ＋ 27 对 hit 层**相交（`cfg.banner_frame` z16 被轨 z22 压边框、`cfg.ch_*_pill` z30 与 `cfg.ch_*_dot` z24 被轨穿过）。该结论曾按派单「停手并报告」保留为证据（`取证\\订正①_停手_放行新增相交清单.txt`），用户据此裁决改走「收窄」路线。
· 右列滑条三支（`cfg.sl_winopac_*` / `sl_textspeed_*` / `sl_autospeed_*`，锚点 **1180**(`_end_lo`) / **1220**(`_hit`) / **1230**(轨) / **1594**(`_end_hi`)）**同名不同族，一律未动**（逐件核对）。
· 未动件留痕：静音复选族（`cfg.snd_vol_*_mute_lb` x=880、`cfg.o_mute_vol_*` x=880/948）不属滑条族、按派单未动；轨内相对位置实测（静音簇中心 924.5：改前在轨中心 912 右侧 12.5px，改后在轨中心 927 左侧 2.5px，相对位移 15px）⇒ 静音簇由「偏右」变为「近居中」，无居中失稳。〔订正（2026-09-27 一审）：原文写「轨中心 942／相对位移仅 5px」有误——942 = 762 + 旧半宽 180，正确轨中心 = 762 + 330/2 = 927。〕

**订正轮结论（通用口径）**
· **「整列位移 + 长条元素」的干净解法 = 锚定不冲突的那一端、只动另一端**（改 `x` 的同时改 `w`）——本例长轨保持右端 1092 不变、左端内移 30px，一举同时满足「左间距恢复 36px」与「零新增相交」；比「少移」干净：少移会让该行与同族其它行**永远不一致**（首行订正②同理：6px → 16px）。
· **热区必须与可视件同步改几何**——只改可视轨不改 `_hit`，右沿会从 1102 涨到 1132 直接越界（本例若漏改 `_hit` 的 `w`，`sl_*_hit` 反而多出 30px）。
· **位移的碰撞体检必须以「目标 `x+w`」试算，不能只看「不与 X 重叠」**：本轮阻碍点 `x=1110`（角色列/banner）比「右列 x≥1180」靠左 70px，只按 1180 检查会漏判。
· 按 x 锚点批量位移**必须先按「族」复核**：本屏左列滑条族（722/732/1046）与右列滑条族（1180/1220/1230/1594）**同名不同族**，锚点不交但命名同源。
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检不写")
    args = ap.parse_args()

    with io.open(SCREEN, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    els = {e["id"]: e for e in d["elements"]}
    before = copy.deepcopy(d)

    pres = set(els)
    moved_new = [i for i in MOVE if i in pres and els[i]["x"] == MOVE[i][0]]
    moved_old = [i for i in MOVE if i in pres and els[i]["x"] in MOVE[i][3]]
    moved_bad = [i for i in MOVE if i in pres and i not in moved_new and i not in moved_old]
    deleted_now = [i for i in DELETE_IDS if i not in pres]
    asset_new = [i for i in PILL_IDS if i in pres and els[i].get("asset") == PILL_NEW_ASSET]
    asset_old = [i for i in PILL_IDS if i in pres and els[i].get("asset") == pill_asset_old(i)]
    asset_bad = [i for i in PILL_IDS if i in pres and i not in asset_new and i not in asset_old]
    tab_new = [i for i in TABTX if i in pres and "vis_when" not in els[i] and "vis_flag" not in els[i]]
    tab_bad = [i for i in TABTX if i in pres
               and i not in tab_new and not els[i].get("vis_when")]
    wid_new = [i for i in WIDTH_NEW if i in pres and els[i]["w"] == WIDTH_NEW[i]]
    wid_bad = [i for i in WIDTH_NEW if i in pres and els[i]["w"] not in WIDTH_OLD_ACCEPT[i]]

    fully_applied = (len(moved_new) == len(MOVE) and len(wid_new) == len(WIDTH_NEW)
                     and len(deleted_now) == len(DELETE_IDS)
                     and len(asset_new) == len(PILL_IDS) and len(tab_new) == len(TABTX)
                     and all(els[i]["rail"].get("nine") == RAIL_NINE for i in SLD_RAIL_IDS)
                     and MARK2A in d["note"])
    if fully_applied:
        print("=" * 100)
        print("m09_apply_config：**已全部应用**（第一轮 ＋ 订正① ＋ 订正②）（幂等）——只报不写")
        print("=" * 100)
        print("  第一轮：左列内移 +30 %d/%d ｜ asset 换件 %d/%d ｜ 删除 %d/%d ｜ 页签常显 %d/%d"
              % (len(moved_new), len(MOVE), len(asset_new), len(PILL_IDS),
                 len(deleted_now), len(DELETE_IDS), len(tab_new), len(TABTX)))
        print("  订正①：滑条族 24 件（18 位移 ＋ 12 收窄 ＋ 6 件 MAX 不动）达标 %d 位移 / %d 收窄 / %d 全零 nine"
              % (len([i for i in SLD_MOVE if els[i]["x"] == SLD_MOVE[i][1]]),
                 len([i for i in WIDTH_NEW if i.startswith("cfg.sl_") and els[i]["w"] == WIDTH_NEW[i]]),
                 len([i for i in SLD_RAIL_IDS if els[i]["rail"].get("nine") == RAIL_NINE])))
        print("  订正②：首行 5 件 x=967 / w=195 已落地")
        print("  屏级 note 已含 %s：是" % MARK2A)
        return 0

    missing = [i for i in list(MOVE) + list(PILL_IDS) + list(TABTX) + list(WIDTH_NEW) if i not in pres]
    if missing:
        raise SystemExit("!! 目标元素不存在（数据已变，停手）：%s" % ", ".join(missing))
    if moved_bad:
        raise SystemExit("!! 下列元素 x 既不是旧值也不是新值（数据被改过，停手）：%s"
                         % ", ".join("%s x=%d" % (i, els[i]["x"]) for i in moved_bad))
    if asset_bad:
        raise SystemExit("!! 下列药丸 asset 既不是旧件也不是新件（停手）：%s" % ", ".join(asset_bad))
    if tab_bad:
        raise SystemExit("!! 下列页签名 vis 状态既不是旧也不是新（停手）：%s" % ", ".join(tab_bad))
    if wid_bad:
        raise SystemExit("!! 下列元素 w 既不是旧值也不是新值（停手）：%s" % ", ".join(wid_bad))
    bad_hi = [i for i in SLD_HI_IDS if els[i]["x"] != 1046]
    if bad_hi:
        raise SystemExit("!! `_end_hi` 应保持不动，实测被改：%s" % ", ".join(
            "%s x=%d" % (i, els[i]["x"]) for i in bad_hi))

    # ── A. asset 换件（+source）──────────────────────────────────────
    n_asset = n_src = 0
    for i in PILL_IDS:
        e = els[i]
        if e["asset"] != PILL_NEW_ASSET:
            assert e["asset"] == pill_asset_old(i), (i, e["asset"])
            e["asset"] = PILL_NEW_ASSET
            n_asset += 1
        if e.get("source") != PILL_NEW_SRC:
            assert e.get("source") == pill_src_old(i), (i, e.get("source"))
            e["source"] = PILL_NEW_SRC
            n_src += 1

    # ── B. 位移（左列 +30；含订正①的轨/热区/MIN）──────────────────
    n_move = 0
    for i, (nx, dl, ax, olds) in MOVE.items():
        e = els[i]
        if e["x"] != nx:
            assert e["x"] in olds, (i, e["x"], olds)
            e["x"] = nx
            n_move += 1
    n_wid = 0
    for i, w_new in WIDTH_NEW.items():
        e = els[i]
        if e["w"] != w_new:
            assert e["w"] in WIDTH_OLD_ACCEPT[i], (i, e["w"])
            e["w"] = w_new
            n_wid += 1
    # ★ 订正① 配套：轨的 rail.nine 全零（使 w=330 合法；见 RAIL_NINE 注释）
    n_nine = 0
    for i in SLD_RAIL_IDS:
        rl = els[i]["rail"]
        cur = rl.get("nine")
        if cur != RAIL_NINE:
            if cur is not None and cur != RAIL_NINE:
                raise SystemExit("!! %s 的 rail.nine 既不是缺省也不是全零（停手）：%s" % (i, cur))
            rl["nine"] = dict(RAIL_NINE)
            n_nine += 1

    # 写盘前不变量
    still_old = [i for i in MOVE if els[i]["x"] != MOVE[i][0]]
    assert not still_old, still_old
    still_wide = [i for i in WIDTH_NEW if els[i]["w"] != WIDTH_NEW[i]]
    assert not still_wide, still_wide

    # ── C. 删除 / 合并 ──────────────────────────────────────────────
    d["elements"] = [e for e in d["elements"] if e["id"] not in DELETE_IDS]
    n_del = len(before["elements"]) - len(d["elements"])
    n_tab = 0
    for i in TABTX:
        e = els[i]
        if "vis_when" in e or "vis_flag" in e:
            e.pop("vis_when", None)
            e.pop("vis_flag", None)
            n_tab += 1

    # ── D. note 追加 ────────────────────────────────────────────────
    n_note = 0
    for i in PILL_IDS:
        n_note += note_append(els[i], note_pill(i, MOVE[i][2], MOVE[i][0]), MARK)
    for i in SEC_IDS:
        n_note += note_append(els[i], note_sec(MOVE[i][2], MOVE[i][0]), MARK)
    for i in SPK_IDS:
        n_note += note_append(els[i], note_spk(MOVE[i][2], MOVE[i][0]), MARK)
    for i in LB_IDS:
        n_note += note_append(els[i], note_lb(MOVE[i][2], MOVE[i][0]), MARK)
    for i in COVER_IDS:
        n_note += note_append(els[i], note_cover(MOVE[i][2], MOVE[i][0]), MARK)
    for i in ON_IDS:
        n_note += note_append(els[i], note_on(MOVE[i][2], MOVE[i][0]), MARK)
    for i in OFF_IDS:
        n_note += note_append(els[i], note_off(MOVE[i][2], MOVE[i][0]), MARK)
    for i in DISPLAY_IDS:
        n_note += note_append(els[i], note_display(MOVE[i][2], MOVE[i][2] + 20), MARK)
    for i, smp in TABTX.items():
        n_note += note_append(els[i], note_tabtx(i, smp), MARK)
    n_fix2 = 0
    for i in DISPLAY_IDS:
        n_fix2 += note_append(els[i], note_display_fix(MOVE[i][0], 221, WIDTH_NEW[i]), MARK2)
    n_fix1 = 0
    for _r in SLD_ROWS:
        n_fix1 += note_append(els["cfg.sl_%s" % _r],
                              note_slider_fix(_r, "rail", 732, 762, 360, 330), MARK2A)
        n_fix1 += note_append(els["cfg.sl_%s_hit" % _r],
                              note_slider_fix(_r, "hit", 722, 752, 380, 350), MARK2A)
        n_fix1 += note_append(els["cfg.sl_%s_end_lo" % _r],
                              note_slider_fix(_r, "end_lo", 732, 762, 46, 46), MARK2A)
        n_fix1 += note_append(els["cfg.sl_%s_end_hi" % _r],
                              note_slider_fix(_r, "end_hi", 1046, 1046, 46, 46), MARK2A)

    # 屏级第二轮块：整块可重写（先截断旧块再追加，保证幂等）
    i0 = d["note"].find(SENT2)
    if i0 != -1:
        d["note"] = d["note"][:i0].rstrip()
    d["note"] = d["note"] + SCREEN_NOTE2
    assert MARK2A in d["note"]

    # ── 范围外元素必须一字未动 ───────────────────────────────────────
    touched = set(MOVE) | set(WIDTH_NEW) | set(SLD_HI_IDS) | set(TABTX)
    b_map = {e["id"]: e for e in before["elements"]}
    untouched_changed = []
    for e in d["elements"]:
        if e["id"] in touched:
            continue
        if json.dumps(b_map[e["id"]], ensure_ascii=False, sort_keys=True) != \
           json.dumps(e, ensure_ascii=False, sort_keys=True):
            untouched_changed.append(e["id"])
    if untouched_changed:
        raise SystemExit("!! 范围外元素被改动（停手）：%s" % ", ".join(untouched_changed))

    print("=" * 100)
    print("m09_apply_config · 变更汇总（未写盘）")
    print("=" * 100)
    print("  A asset 换件              %4d  （本次 %d）" % (len(PILL_IDS), n_asset))
    print("  A source 换口径            %4d  （本次 %d）" % (len(PILL_IDS), n_src))
    print("  B 位移（x 改写）           %4d  （本次 %d）—— 含订正① 18 件（轨 6/热区 6/MIN 6）"
          % (len(MOVE), n_move))
    print("  B/C 收窄（w 改写）         %4d  （本次 %d）—— 订正② 首行 5（221→195）"
          " ＋ 订正① 轨 6（360→330）/热区 6（380→350）" % (len(WIDTH_NEW), n_wid))
    print("  C 删除元素                %4d  （本次 %d）" % (len(DELETE_IDS), n_del))
    print("  订正① 轨补全零 rail.nine    %4d  （本次 %d；使 w=330 合法、不计「缩放元素」）"
          % (len(SLD_RAIL_IDS), n_nine))
    print("  C 页签名去 vis             %4d  （本次 %d）" % (len(TABTX), n_tab))
    print("  D note 追加（第一轮）      %4d  （本次 %d 处）" % (110, n_note))
    print("  D note 追加（订正②）       %4d  （本次 %d 处）" % (len(DISPLAY_IDS), n_fix2))
    print("  D note 追加（订正①）       %4d  （本次 %d 处；含 6 件 MAX「不动」说明）"
          % (len(SLD_IDS), n_fix1))
    print("  D 屏级订正块               %4s  （整块重写：订正① ＋ 订正② 均「已落地」）" % "1")
    print("  订正① MAX 端点（_end_hi）   %4d 件：x=1046 保持不动（右沿 1092 与轨右端对齐）" % len(SLD_HI_IDS))
    print("  右列滑条三支（不得动）      %4d 件：%s"
          % (len(RIGHT_SLD_IDS), " ".join("%s=%d" % (i, els[i]["x"]) for i in RIGHT_SLD_IDS[:4]) + " …"))
    print("  范围外元素未动             ✓（逐元素 JSON 比对）")
    if args.check:
        print("--check：未写盘。")
        return 0

    txt = json.dumps(d, ensure_ascii=False, indent=1)
    with io.open(SCREEN, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(txt)
    print("已写盘：%s（%d 字节）" % (SCREEN, os.path.getsize(SCREEN)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
