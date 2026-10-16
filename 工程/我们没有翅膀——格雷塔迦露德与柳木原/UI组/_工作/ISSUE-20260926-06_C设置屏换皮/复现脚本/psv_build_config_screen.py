# -*- coding: utf-8 -*-
r"""psv_build_config_screen.py —— 25 设置屏（C 组换皮）· 数据重排（一次性脚手架）

**Issue**：ISSUE-20260926-06（PSV 换皮 · C 组设置屏两页）
**输入**：`layout/screens/25_config.json`（M47 版，435 件）
**输出**：同路径覆写（**先备份到 `_工作\ISSUE-20260926-06_C设置屏换皮\_证据\25_config.M47.json`**）

**本脚手架只做「几何重排 + 2 件退场 + 6 件新增 + rail/source/note 改写**：
`flags_default`（25 键）、全部 `vis_flag`/`vis_when`、全部 `action`/`value`、9 个 `slider` 的
`min/max/step/value/setting/handle`、`state_assets`/`state_group`、`kind`、`z`、元素 id —— **一律不动**。

**几何口径（实测，来自 `_工作\ISSUE-20260926-02_PSVconfig去字\复现脚本\rects_manifest.json`
与 `_工作\ISSUE-20260926-06_C设置屏换皮\_证据\几何实测.md`）**：
  · PSV 1× → 我方画布：`asset_x = PSV_x*2`，`asset_y = PSV_y*2 − 4`（PSV 全屏 2× = 1920×1088，我方 1920×1080 上下各去 4px）
  · 面板 panel PSV[65,100,897,460] → asset [130,196,1794,916]
  · 标签列左内缩：page1 PSV x68 → asset 136；page2 PSV x76 → asset 152
  · PSV 行节距 PSV 36.9 → asset 74；8 行（页1）/ 6 行（页2）的标签文字带（asset y）实测为
    (278..306)(356..382)(428..454)(500..528)(578..604)(652..678)(724..750)(800..826)  /
    (282..308)(354..380)(428..454)(502..528)(578..604)(650..676)
  · 药丸壳 560×72（= PSV 280×36 @2×）**1:1**；滑槽轨 360×30（720×60 的 0.5×，**两页同一倍率**）

**用法**（在 `<UI组>\` 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_C设置屏换皮\复现脚本\psv_build_config_screen.py
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # <UI组>
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
BACKUP = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏换皮", "_证据", "25_config.M47.json")

# ------------------------------------------------------------------ 常量
PAGE1_BG = "ui/x_ui_psv_cfg_page1.png"
PAGE2_BG = "ui/x_ui_psv_cfg_page2.png"
RAIL_C1 = "ui/x_ui_psv_rail_c1.png"
RAIL_C2 = "ui/x_ui_psv_rail_c2_%02d.png"
COVER_C1 = "ui/x_ui_psv_cover_c1.png"
COVER_C2 = "ui/x_ui_psv_cover_c2_%02d.png"
SRC_C1 = ("PSV系统UI参考\\去字件\\2x\\bgc01_page.png → 工具\\m53\\m54 整流（去字件，日文已除净）")
TAG_W, TAG_H = 560, 72          # 药丸壳 1:1
OPT_W, OPT_H = 115, 59          # ON/OFF 值底（1:1，不缩放）
RAIL_W, RAIL_H = 360, 30        # 滑槽轨（720×60 的 0.5×）

# 页1（系统）· 左栏 8 行标签的 tag 顶边 y（节距 74，与页面残留标签带的实测位置对齐；
#   后两行（确认信息设定）跨过中间那道节题，故 700 → 728/804）
SYS_TAGS = [256, 330, 404, 478, 552, 626]
SYS_CONFIRM_TAGS = [720, 796]
# 页2（声音）· 6 行
SND_ROWKEYS = ["master", "bgm", "se", "sysse", "voice", "char"]
SND_TAGS = [256, 330, 404, 478, 552, 626]
# 页2 · 角色网格（3 列 × 11 行，沿用原列序；列内自上而下）
CH_COLS_X = [1110, 1340, 1570]
CH_PILL_W, CH_PILL_H = 222, 36
CH_COL_STEP, CH_ROW_STEP = 230, 39
CH_GRID_Y0 = 486

RETIRE = ["cfg.frame", "cfg.page_strip"]          # 旧件退场（PSV 底图取代）

G = {}          # id -> (x, y, w, h)
S = {}          # id -> 备注（覆盖/追加）
SRC = {}        # id -> source


def put(i, x, y, w, h):
    G[i] = (x, y, w, h)


def opt_group(prefix, y_txt, on_x, on_w, off_x, off_w, label_box=None):
    """一组值控件（on/off 或 两选一）—— 文本与热区一律与图同矩形（M47 既有口径）"""
    for suf, x, w in [("on", on_x, on_w), ("off", off_x, off_w)]:
        put("cfg.o_%s_%s" % (prefix, suf), x, y_txt, w, OPT_H)
        put("cfg.o_%s_%s_hit" % (prefix, suf), x, y_txt, w, OPT_H)
    put("cfg.o_%s_on_tx_sel" % prefix, on_x, y_txt, on_w, OPT_H)
    put("cfg.o_%s_on_tx" % prefix, on_x, y_txt, on_w, OPT_H)
    put("cfg.o_%s_off_tx" % prefix, off_x, y_txt, off_w, OPT_H)
    if label_box:
        put("cfg.row_%s_lb" % prefix, *label_box)


# ================================================================== 页1（系统）
# 两栏版式（实测依据见文件头）：
#   左栏 x136..1158 = 画面设定 6 行 + 确认信息设定 2 行（**8 行全部带 PSV 药丸壳标签**）
#   右栏 x1180..1794 = 文本设定 5 行（3 滑槽 + 2 开关）+ 预览块
put("cfg.sec_picture", 136, 214, 400, 36)
# --- 画面设定（6 行，带壳）-----------------------------------------------------
put("cfg.row_display_lb", 196, SYS_TAGS[0], 440, TAG_H)
opt_group("display", SYS_TAGS[0] + 6, 716, 205, 937, 221)
put("cfg.row_facewindow_lb", 196, SYS_TAGS[1], 440, TAG_H)
opt_group("facewindow", SYS_TAGS[1] + 6, 716, OPT_W, 847, OPT_W)
put("cfg.row_drama_lb", 196, SYS_TAGS[2], 440, TAG_H)
opt_group("drama", SYS_TAGS[2] + 6, 716, OPT_W, 847, OPT_W)
put("cfg.row_effect_lb", 196, SYS_TAGS[3], 440, TAG_H)
opt_group("effect", SYS_TAGS[3] + 6, 716, OPT_W, 847, OPT_W)
put("cfg.row_voicecut_lb", 196, SYS_TAGS[4], 440, TAG_H)
opt_group("voicecut", SYS_TAGS[4] + 6, 716, OPT_W, 847, OPT_W)
put("cfg.row_curhide_lb", 196, SYS_TAGS[5], 440, TAG_H)
opt_group("curhide", SYS_TAGS[5] + 6, 716, OPT_W, 847, OPT_W)
# --- 确认信息设定（左栏下；节题放在 A6 壳右侧的同一水平带）---------------------
put("cfg.sec_confirm", 760, 690, 400, 36)
put("cfg.row_savedialog_lb", 196, SYS_CONFIRM_TAGS[0], 440, TAG_H)
opt_group("savedialog", SYS_CONFIRM_TAGS[0] + 6, 716, OPT_W, 847, OPT_W)
put("cfg.row_loaddialog_lb", 196, SYS_CONFIRM_TAGS[1], 440, TAG_H)
opt_group("loaddialog", SYS_CONFIRM_TAGS[1] + 6, 716, OPT_W, 847, OPT_W)
# --- 文本设定（右栏；滑槽行 = 名在上、轨在下 + 两端刻度）------------------------
put("cfg.sec_text", 1180, 214, 400, 36)
put("cfg.row_winopac_lb", 1180, 254, 340, 30)
put("cfg.sl_winopac", 1230, 290, RAIL_W, RAIL_H)
put("cfg.sl_winopac_hit", 1220, 246, 380, 72)
put("cfg.sl_winopac_end_lo", 1180, 294, 46, 21)
put("cfg.sl_winopac_end_hi", 1594, 294, 46, 21)
put("cfg.row_winopac_hint", 1180, 322, 420, 26)
put("cfg.row_textspeed_lb", 1180, 358, 340, 30)
put("cfg.sl_textspeed", 1230, 394, RAIL_W, RAIL_H)
put("cfg.sl_textspeed_hit", 1220, 348, 380, 72)
put("cfg.sl_textspeed_end_lo", 1180, 398, 46, 21)
put("cfg.sl_textspeed_end_hi", 1594, 398, 46, 21)
put("cfg.row_autospeed_lb", 1180, 430, 340, 30)
put("cfg.sl_autospeed", 1230, 466, RAIL_W, RAIL_H)
put("cfg.sl_autospeed_hit", 1220, 420, 380, 76)
put("cfg.sl_autospeed_end_lo", 1180, 470, 46, 21)
put("cfg.sl_autospeed_end_hi", 1594, 470, 46, 21)
put("cfg.row_allskip_lb", 1180, 506, 300, OPT_H)
opt_group("allskip", 506, 1500, OPT_W, 1631, OPT_W)
put("cfg.row_textcolchg_lb", 1180, 572, 300, OPT_H)
opt_group("textcolchg", 572, 1500, OPT_W, 1631, OPT_W)
# --- 预览（右栏底；框 612 宽 = 右栏宽，1:1 未缩放）-----------------------------
put("cfg.sec_preview", 1180, 632, 400, 36)
put("cfg.pv_frame", 1180, 674, 612, 154)
put("cfg.pv_bg", 1180, 674, 612, 154)
put("cfg.pv_mask", 1190, 684, 592, 134)
put("cfg.pv_text", 1194, 686, 584, 134)
put("cfg.pv_note", 1180, 832, 612, 56)
put("cfg.pv_note_x", 1180, 890, 612, 26)
# --- 预留行「播放影片」（永久不可见，停放于右栏尾；见报告）----------------------
put("cfg.row_cfmovie_lb", 1180, 856, 300, OPT_H)
put("cfg.row_cfmovie_bg", 1500, 856, OPT_W, OPT_H)
put("cfg.row_cfmovie_hit", 1500, 856, 256, OPT_H)

# ================================================================== 页2（声音）
put("cfg.sec_volume", 152, 214, 400, 36)
for k, ty in zip(SND_ROWKEYS, SND_TAGS):
    put("cfg.snd_vol_%s_lb" % k, 212, ty, 440, TAG_H)
    put("cfg.snd_vol_%s_mute_lb" % k, 880, ty + 51, 89, 21)
    put("cfg.o_mute_vol_%s_off" % k, 948, ty + 51, 21, 21)
    put("cfg.o_mute_vol_%s_on" % k, 948, ty + 51, 21, 21)
    put("cfg.o_mute_vol_%s_on_hit" % k, 948, ty + 51, 21, 21)
    put("cfg.o_mute_vol_%s_off_hit" % k, 880, ty + 51, 68, 21)
    put("cfg.sl_%s" % k, 732, ty + 21, RAIL_W, RAIL_H)
    put("cfg.sl_%s_hit" % k, 722, ty + 6, 380, 45)
    put("cfg.sl_%s_end_lo" % k, 732, ty + 51, 46, 21)
    put("cfg.sl_%s_end_hi" % k, 1046, ty + 51, 46, 21)
put("cfg.snd_vol_se_spk", 162, SND_TAGS[2] + 14, 22, 32)
put("cfg.snd_vol_sysse_spk", 162, SND_TAGS[3] + 14, 22, 32)
put("cfg.snd_vol_voice_spk", 162, SND_TAGS[4] + 14, 22, 32)
put("cfg.snd_vol_char_spk", 162, SND_TAGS[5] + 14, 22, 32)
put("cfg.sec_voice", 152, 706, 400, 36)
put("cfg.sec_charvoice", 1110, 214, 400, 36)
put("cfg.banner_frame", 1110, 240, 644, 239)

# ================================================================== 页签 / 屏题
put("cfg.tab1_on", 136, 166, 181, 50)
put("cfg.tab1_off", 136, 166, 181, 50)
put("cfg.tab1_tx_sel", 136, 143, 181, 96)
put("cfg.tab1_tx", 136, 143, 181, 96)
put("cfg.tab1_hit", 136, 143, 181, 96)
put("cfg.tab2_on", 337, 166, 180, 50)
put("cfg.tab2_off", 337, 166, 180, 50)
put("cfg.tab2_tx_sel", 337, 143, 180, 96)
put("cfg.tab2_tx", 337, 143, 180, 96)
put("cfg.tab2_hit", 337, 143, 180, 96)
put("cfg.title_sys", 400, 52, 900, 80)
put("cfg.title_snd", 400, 52, 900, 80)

# ================================================================== 顶右四钮（位置沿用）
for i in ("cfg.reset_hit", "cfg.reset_bg", "cfg.reset_tx"):
    put(i, 1708, 76, 182, 76)
for i in ("cfg.btn_game_bg", "cfg.btn_game_tx"):
    put(i, 1227, 33, 206, 40)
put("cfg.btn_game_hit", 1221, 27, 218, 52)
for i in ("cfg.btn_title_bg", "cfg.btn_title_tx"):
    put(i, 1451, 32, 208, 41)
put("cfg.btn_title_hit", 1445, 26, 220, 53)
for i in ("cfg.btn_end_bg", "cfg.btn_end_tx"):
    put(i, 1674, 32, 201, 41)
put("cfg.btn_end_hit", 1668, 26, 213, 53)


def main():
    # ★ 幂等：本脚本从 **备份（M47 原版）** 起步 —— 重复运行不会在已换皮的盘面上二次套用几何。
    src = BACKUP if os.path.exists(BACKUP) else SCREEN
    with open(src, encoding="utf-8") as fh:
        doc = json.load(fh)
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    if src is SCREEN:
        shutil.copy2(SCREEN, BACKUP)
    els = doc["elements"]
    by = {e["id"]: e for e in els}
    if len(by) != len(els):
        raise SystemExit("!! 元素 id 重复")

    # ---- 角色网格：列序沿用「原列内自上而下」的顺序（3 列 × 11 行）----------------
    fams = [e["vis_when"] for e in els
            if e["id"].startswith("cfg.ch_") and e["id"].endswith("_pill")]
    if len(fams) != 33:
        raise SystemExit("!! 角色数不是 33，实测 %d" % len(fams))
    for i, fam in enumerate(fams):
        col, row = i // 11, i % 11
        cx = CH_COLS_X[col]
        cy = CH_GRID_Y0 + CH_ROW_STEP * row
        put("cfg.ch_%s_pill" % fam, cx, cy, CH_PILL_W, CH_PILL_H)
        put("cfg.ch_%s_dot" % fam, cx + 6, cy + 12, 12, 12)
        put("cfg.ch_%s_tx" % fam, cx + 26, cy, CH_PILL_W - 26, CH_PILL_H)
        put("cfg.ch_%s_tx_sel" % fam, cx + 26, cy, CH_PILL_W - 26, CH_PILL_H)
        put("cfg.ch_%s_hit" % fam, cx, cy, CH_PILL_W, CH_PILL_H)
        put("cfg.pv_face_%s" % fam, 1553, 240, 191, 239)
        put("cfg.pv_name_%s" % fam, 1136, 300, 390, 60)

    # ---- slider rail / 备注 -----------------------------------------------------
    sys_rails = ("cfg.sl_winopac", "cfg.sl_textspeed", "cfg.sl_autospeed")
    snd_rail_map = {"cfg.sl_master": 1, "cfg.sl_bgm": 2, "cfg.sl_se": 3, "cfg.sl_sysse": 4,
                    "cfg.sl_voice": 1, "cfg.sl_char": 2}
    for eid, e in by.items():
        if e["kind"] != "slider":
            continue
        if eid in sys_rails:
            e["rail"] = {"asset": RAIL_C1}
            tag = "页1 滑槽 c1"
        else:
            n = snd_rail_map[eid]
            e["rail"] = {"asset": RAIL_C2 % n}
            tag = "页2 滑槽 c2_%02d" % n
        S[eid] = ("★ PSV 换皮（C 组，2026-09-26）：rail 换 **%s**（PSV 滑槽件 720×60 经 "
                  "`工具\\m54_psv_config_assets.py` 抠底 + 0.5× ⇒ 360×30 真 alpha 件，**两页同一倍率**）；"
                  "元素框 w/h 与素材 1:1（无 nine）。`min/max/step/value/setting/handle` **一字未改**。"
                  % tag)

    # ---- 逐件套几何 --------------------------------------------------------------
    moved = 0
    for e in els:
        eid = e["id"]
        if eid in RETIRE:
            continue
        if eid in G:
            e["x"], e["y"], e["w"], e["h"] = G[eid]
            moved += 1
        elif eid not in ("cfg.dim",):
            raise SystemExit("!! 元素未在几何表中：%s" % eid)

    # ---- 备注（几何说明；不改语义字段）------------------------------------------
    S["cfg.row_display_lb"] = ("★ PSV 换皮（C 组）：行名**叠在 PSV 药丸壳**（`cfg.tag_sys_01`）之内，"
                               "x 由 100 → 196（让开药丸尖端区），框高 = 壳高 72。")
    S["cfg.sec_picture"] = ("★ PSV 换皮（C 组）：节题移到面板顶线下方（136,214），居左内缩 = 面板内标签列 x；"
                            "y=214 是为**让开页签**（页签占 166..216）。")
    S["cfg.sec_confirm"] = ("★ PSV 换皮（C 组）：节题停放在 A6 壳**右侧同一水平带**（760,690）"
                            "—— 左栏 8 行节距 74 已排满，行间无处插入；纯节题文字，位置无机制含义。")
    S["cfg.pv_frame"] = ("★ PSV 换皮（C 组）：预览块移到**右栏底**（1180,674,612,154，**1:1 未缩放**，"
                         "612 宽恰等于右栏宽）；素材与九宫格未改。")
    S["cfg.row_winopac_lb"] = ("★ PSV 换皮（C 组）：本行自「画面设定」组**改归「文本设定」组**"
                               "（它本就是文本窗口设置，且新布局里唯一的滑槽列在右栏）；见屏级 note。")
    S["cfg.row_cfmovie_lb"] = ("★ PSV 换皮（C 组）：**预留行**（`visible_default:false`，永久不可见）"
                               "停放于右栏尾（1180,856）—— 新两栏版式无空槽可放；该行与 `cfg.pv_note` "
                               "的矩形有重叠，但**不可见 ⇒ 产品不可达、无观感与命中影响**。")
    S["cfg.title_sys"] = "★ PSV 换皮（C 组）：屏题移到 PSV 底图烘焙题字「CONFIG」右侧（400,52），与之同一基线。"
    S["cfg.tab1_on"] = ("★ PSV 换皮（C 组）：两个页签移入 **PSV 面板左上角的章节标签槽**"
                        "（PSV label_zone [68,91,198,122] → asset [136,178,396,240]，页签压面板上边框）。"
                        "九宫格 l=r=25 / t=b=0 未改 ⇒ **h 必须 = 素材高 50**，故 h 保持 50。")
    for i in ("cfg.ch_asu_pill",):
        S[i] = ("★ PSV 换皮（C 组）：角色网格由 **3 列 × 11 行（单元 250×36 / 步进 250×39）**"
                "改为 **单元 222×36 / 列步进 230 / 行步进 39**（列序与行序**不变**），"
                "让出右栏宽度给 PSV 面板右缘（1794）；九宫格 l=r=16 / t=b=8 未改。")
    S["cfg.banner_frame"] = "★ PSV 换皮（C 组）：角色横幅移到右栏顶（1110,240,644,239），九宫格未改。"
    S["cfg.sec_charvoice"] = "★ PSV 换皮（C 组）：角色语音节题移到右栏顶线（1110,214），在横幅上方。"
    S["cfg.sec_voice"] = ("★ PSV 换皮（C 组）：节题「语音设定」在左栏 6 行排满后**停放在左栏尾**"
                          "（152,706）—— 6 行节距 74 已占满，无处插入行间；纯节题文字，位置无机制含义。")
    for k in SND_ROWKEYS:
        S["cfg.snd_vol_%s_lb" % k] = ("★ PSV 换皮（C 组）：行名**叠在 PSV 药丸壳**（`cfg.tag_snd_%02d`）之内"
                                      "（x 212 = 壳内缩 60），框高 = 壳高 72。"
                                      % (SND_ROWKEYS.index(k) + 1))
        S["cfg.sl_%s" % k] = (S.get("cfg.sl_%s" % k, "") +
                              " 几何：轨 (732, tag+21, 360, 30)；「静音 + 勾选」与两端刻度移到轨**下方**的 21px 带内"
                              "（勾选与 `_off_hit` 沿 M47 原相对几何：标签 x0 w89 / 勾选 x0+68 w21 / "
                              "`_off_hit` x0 w68 ⇒ 二者不重叠）。")
    for i, e in enumerate(els):
        if e["id"] in S:
            e["note"] = S[e["id"]]

    # ---- 退场 + 新增 -------------------------------------------------------------
    els[:] = [e for e in els if e["id"] not in RETIRE]
    new = [
        dict(id="cfg.page1_bg", kind="image", z=8, visible_default=True,
             asset=PAGE1_BG, x=0, y=0, w=1920, h=1080, opacity=255,
             source="PSV系统UI参考\\去字件\\2x\\bgc01_page.png（超分去字件，日文已除净）→ "
                    "工具\\m53_psv_ui_assets.py 载入（上下各去 4px）",
             note="★ PSV 换皮（C 组）：**页1（系统）整屏底图**（1920×1080，1:1 无 nine）。取代 M47 的 "
                  "`cfg.frame` + `cfg.page_strip`（两旧件已退场，登记见 `工具\\test_gen_sync.py` 的 NO_GEN 注）。"
                  "本件含 PSV 的 CONFIG 题字、面板、雪带与左右箭头；页脚 y988-1032 属**待定区**，本轮不处理。",
             vis_flag="cfg_page", vis_when="sys"),
        dict(id="cfg.page2_bg", kind="image", z=8, visible_default=True,
             asset=PAGE2_BG, x=0, y=0, w=1920, h=1080, opacity=255,
             source="PSV系统UI参考\\去字件\\2x\\bgc02_page.png（超分去字件，日文已除净）→ "
                    "工具\\m53_psv_ui_assets.py 载入（上下各去 4px）",
             note="★ PSV 换皮（C 组）：**页2（声音）整屏底图**。与 `cfg.page1_bg` 同族，仅页面内容不同"
                  "（实测两页面板区逐像素一致，差异只在滑槽条带与残留标签带）。",
             vis_flag="cfg_page", vis_when="snd"),
        dict(id="cfg.cover_c1", kind="image", z=9, visible_default=True,
             asset=COVER_C1, x=906, y=776, w=750, h=72, opacity=255,
             source="由 `cfg.page1_bg` 自身该区域**上下锚行线性插值**派生 → 工具\\m54_psv_config_assets.py",
             note="★ PSV 换皮（C 组）：**盖槽片** —— 抹掉页面里烘焙的旧滑槽（asset 916,782,720,60）。"
                  "本布局里 9 个 slider 的 rail 已改为 360×30 的真 alpha 件（位置/宽度都不同）⇒ "
                  "页面自带的旧滑槽必须抹掉，否则与新 rail 叠成「双滑槽」。面板背景纵向严格线性"
                  "（干净区插值残差 max=0/255）⇒ 盖片接缝实测 mean|d|≤0.41/255。",
             vis_flag="cfg_page", vis_when="sys"),
    ]
    for i, gy in enumerate((258, 332, 406, 480), 1):
        new.append(dict(id="cfg.cover_c2_%02d" % i, kind="image", z=9, visible_default=True,
                        asset=COVER_C2 % i, x=906, y=gy - 6, w=750, h=72, opacity=255,
                        source="由 `cfg.page2_bg` 自身该区域上下锚行线性插值派生 → 工具\\m54_psv_config_assets.py",
                        note="★ PSV 换皮（C 组）：盖槽片（抹页面里烘焙的旧滑槽 #%d，asset 916,%d,720,60）。"
                             "理由同 `cfg.cover_c1`。" % (i, gy),
                        vis_flag="cfg_page", vis_when="snd"))
    # --- 5 个带标签的行：药丸壳（1:1，仅装饰；悬停/按下仍由既有值按钮承担）--------
    # --- 行名标签底：页1 8 个壳（1..6 → 画面设定六行；7/8 → 确认信息设定两行）------
    tag_owner = {
        1: ("cfg.row_display_lb", SYS_TAGS[0]),
        2: ("cfg.row_facewindow_lb", SYS_TAGS[1]),
        3: ("cfg.row_drama_lb", SYS_TAGS[2]),
        4: ("cfg.row_effect_lb", SYS_TAGS[3]),
        5: ("cfg.row_voicecut_lb", SYS_TAGS[4]),
        6: ("cfg.row_curhide_lb", SYS_TAGS[5]),
        7: ("cfg.row_savedialog_lb", SYS_CONFIRM_TAGS[0]),
        8: ("cfg.row_loaddialog_lb", SYS_CONFIRM_TAGS[1]),
    }
    for n in range(1, 9):
        owner, ty = tag_owner[n]
        new.append(dict(id="cfg.tag_sys_%02d" % n, kind="image", z=12, visible_default=True,
                        asset="ui/x_ui_psv_pill_c1_%02d.png" % n, x=136, y=ty, w=TAG_W, h=TAG_H,
                        opacity=255,
                        source="PSV系统UI参考\\去字件\\2x\\bgc01_pill_%02d.png（无字药丸壳）→ 工具\\m53" % n,
                        note="★ PSV 换皮（C 组）：页1 第 %d 行的**行名药丸壳**（1:1，560×72；叠在其上的"
                             "行名由引擎绘制，见 `%s`）。**仅常态**：不带 `state_assets`/`state_group`，"
                             "不进悬停候选并集 ⇒ 该行的悬停/按下反馈仍由既有值按钮 `cfg.o_*` 的 "
                             "`state_assets` + 热区 `state_group` 承担。" % (n, owner),
                        vis_flag="cfg_page", vis_when="sys"))
    for n, k in enumerate(SND_ROWKEYS, 1):
        new.append(dict(id="cfg.tag_snd_%02d" % n, kind="image", z=12, visible_default=True,
                        asset="ui/x_ui_psv_pill_c2_%02d.png" % n, x=152, y=SND_TAGS[n - 1],
                        w=TAG_W, h=TAG_H, opacity=255,
                        source="PSV系统UI参考\\去字件\\2x\\bgc02_pill_%02d.png（无字药丸壳）→ 工具\\m53" % n,
                        note="★ PSV 换皮（C 组）：页2 第 %d 行（%s）的行名药丸壳（1:1，560×72；8/6 个壳与"
                             "PSV 页2 的 6 行一一对应）。仅常态，理由同 `cfg.tag_sys_01`。"
                             % (n, k), vis_flag="cfg_page", vis_when="snd"))
    els.extend(new)

    # ---- 屏级备注 ----------------------------------------------------------------
    doc["note"] = doc["note"] + (
        "\n\n---\n**★ PSV 换皮（C 组 · 2026-09-26 · ISSUE-20260926-06）**\n"
        "· **底图**：两页各一张 PSV 去字件整屏底（`cfg.page1_bg` sys / `cfg.page2_bg` snd，"
        "1920×1080，1:1）；旧件 `cfg.frame` / `cfg.page_strip` **退场**"
        "（`x_ui_cfg_page_strip.png` 仍被 39 鉴赏外壳屏共用，故素材不归档）。\n"
        "· **行分配**：面板 panel asset [130,196,1794,916]；**PSV 行节距 74**（PSV 36.9×2）。"
        "页1 我方 13 项 > PSV 8 行 ⇒ 分两栏：左栏 = 画面设定 6 行（**tag 顶边 256/330/404/478/552/626**，"
        "与页面残留标签带实测位置对齐）+ 预览；右栏 = 确认信息设定 2 行 + 文本设定 5 行（含 3 滑槽）。"
        "页2 我方 6 项 = PSV 6 行，**不作压缩**，逐行同位（tag 顶边同上）。\n"
        "· **药丸壳（14 件）用在哪**：实测页面**值列（PSV x420..880）里没有任何药丸形状**"
        "（去字件的差异分析只剩滑槽与残留标签带）⇒ PSV 的值单元本就是**裸文字**；而 14 个壳来自"
        "**雪碧条的行名标签**（8 条 = 页1 八行、6 条 = 页2 六行，与行数一一对应）。因此 14 个壳"
        "**全部用作行名标签底**（页1 8 + 页2 6），1:1 摆放，叠在其上的中文由引擎绘制；"
        "值控件仍用 `x_ui_cfg_opt_*` 三态件（1:1 未缩放）。\n"
        "· **滑槽**：5 条 PSV 滑槽件经 `工具\\m54_psv_config_assets.py` **抠成真 alpha 轨并 0.5×**"
        "（360×30，两页同一倍率）；页1 3 个 slider 用 c1，页2 6 个用 c2_01..04（其中 c2_01/c2_02 "
        "各复用一次，见各 slider 的 note）。手柄仍用既有 `ui/x_ui_cfg_knob.png`（不新增件）。"
        "页面里烘焙的 5 条旧滑槽由 5 张**盖槽片**抹除。\n"
        "· **不改语义**：`flags_default` 25 键、全部 `vis_flag`/`vis_when`、`config_set_*`/`config_char_*`"
        "动作、9 个 slider 的 `min/max/step/value/setting`、`state_assets`/`state_group` **一律未改**。\n"
        "· **未决**：页脚 y988-1032（待定区）未处理；`cfg.sec_voice` 停放在左栏尾；"
        "`cfg.row_cfmovie_*`（永久不可见）停放右栏尾；行距依据与字号取舍见工程记录。")

    with open(SCREEN, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("元素 %d → %d（退场 %d，新增 %d，重排 %d）" % (len(els) - len(new) + len(RETIRE), len(els),
                                                      len(RETIRE), len(new), moved))
    print("退场：%s" % ", ".join(RETIRE))
    print("备份：%s" % BACKUP)


if __name__ == "__main__":
    main()
