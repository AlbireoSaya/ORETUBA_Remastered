# -*- coding: utf-8 -*-
r"""psv_fix_config_screen.py —— 25 设置屏（C 组换皮）**修复轮**：版面侧 6 项缺陷的数据修法

**Issue**：ISSUE-20260926-06_C设置屏修复 ｜ 输入/输出：`layout/screens/25_config.json`（就地覆写）

派单把「一审不达标」拆成 ①~⑥ 六条。本脚本处理**版面侧**的全部条目；素材侧两条由
`工具\psv_fix_cfg_residue.py`（缺陷 ① 的底图残留检验 + 缺陷 ⑤ 的盖片）与
`工具\psv_fix_preview_bg.py`（缺陷 ③）承担。逐条：

①  **页标题残影**：实测为**引擎绘制**节题（见 `psv_fix_cfg_residue.py` 文件头 §一）。
    修法：`cfg.sec_*` 7 件色值 → `@palette.psv_ink`（浅霜板上的可读墨色，对比度 11.9:1）；
    `cfg.sec_picture` / `cfg.sec_volume` 的 y 214 → **218**（让开页签药丸 `cfg.tab1_on`
    下缘 y216 ⇒ 由「重叠 2px」变为「净空 2px」；两件同 y 保持一致）。
②  **值列药丸不一致**：根因 = 选中态药丸只由**左槽**的 `x_ui_cfg_opt_on.png` 提供，**右槽**
    元素 `cfg.o_<行>_off` 的 `state_assets.normal` 指向 `x_ui_cfg_opt_off.png`（**α 恒 0**，
    实测 alpha min/max = 0/0）⇒ 当前值落在右槽的行（`cfg_v_voicecut`/`cfg_v_curhide`='off'，
    `shot_19` 里 `cfg_v_display`='full'）**整行无药丸**。
    修法（**只增件 + 收窄一件的 vis_when，语义字段零改**）：
      · 每行新增 `cfg.o_<行>_off_sel`（image，asset 同 `x_ui_cfg_opt_on.png`、九宫格同，
        z=23，`state_assets`/`state_group` 与 `cfg.o_<行>_off` **同组**）——
        `vis_flag=cfg_v_<行>` / `vis_when=<右槽值>` ⇒ **右槽为当前值时显示同款冰蓝药丸**；
        因为它与 `_off` 同组，悬停/按下时两件一起换图（画面仍是 hover/pressed 图，无叠加感）；
      · 新增 `cfg.o_<行>_off_tx_sel`（text，暗字 `@palette.panel_fill`，z=27，
        `vis_flag/vis_when` 同 `_off_sel`）—— 药丸上的当前值文字；
      · `cfg.o_<行>_off_tx`（浅字/未选值）的 `vis_when` 由 `sys|snd` 收窄为**左槽值**
        （display→`window`，其余→`on`）⇒ 与既有 `cfg.o_<行>_on_tx`（vis_when=<右槽值>）
        互为镜像，两槽「当前值 = 暗字 + 药丸 / 非当前值 = 墨字无底」完全对称。
    覆盖 10 行：display / facewindow / drama / effect / voicecut / curhide / savedialog /
    loaddialog / allskip / textcolchg（= 送审点名的 8 行 + 右列同类 2 行）。
③  **预览区硬边矩形**：素材侧，见 `工具\psv_fix_preview_bg.py`。
④  **弱对比**：按 `psv_config_contrast.py` 的量化清单，把「压在浅霜板/浅色件上的文字」
    改走两个新色板键：主文字 → `@palette.psv_ink`、次级说明 → `@palette.psv_ink_dim`
    （预览说明段由 #B8B8C8 加深 **2 档**至 #3E4E70）。
⑤  **组标题错位**：`cfg.sec_voice`（「语音设定」）由左栏尾 (152,706) 上移到**其组之前**——
    即页2 第 5 行槽位 (136,552)；「主音量（语音）/角色音量」两行**整体下移一个节距 74px**
    （槽位 5→6、6→7），使 (a) 组标题落在组前、(b) 原标题位置被下移的「角色音量」行填满
    （消除下部大留白）。下移后露出的**残留标签带**（原被 `tag_snd_05` 盖住）由
    `工具\psv_fix_cfg_residue.py` 派生的 `cfg.cover_c2_05` 盖片抹平。
⑥  **两页 16px 错位**：`label_zone` c1/c2 在 PSV 底图里本就差 8px(1×)=16px(2×)，
    但两页的**药丸壳与行标签都是我方自绘**（页面里的药丸已被去字件擦除，**无烘焙物可对齐**，
    实测：把 `pill_c1_01`/`c2_01` 在各自页面里做全带搜索，最佳 mean|d|≈55 ⇒ 页面里没有药丸）
    ⇒ 对齐**不会破坏与底图的相对位置**，故按派单口径把**声音页壳/标签 x 左移 16px**
    对齐系统页（tag/snd 标签/spk/两个节题）。

**幂等**：所有改动都带「已应用则跳过」判据（新件存在即不重复插入，值已等于目标即不写）。
**备份**：首次运行把 C 组换皮版存 `_证据/25_config.C组换皮版.json`（只新建不覆盖）。
**不动**：`flags_default`（25 键）、`action`/`value`、`setting`/`min`/`max`/`step`、
`state_assets`/`state_group` 现有值、元素 id、kind、z（除新增件外）。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_C设置屏修复\复现脚本\psv_fix_config_screen.py [--dry-run]
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
BACKUP = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏修复", "_证据", "25_config.C组换皮版.json")

PILL = "ui/x_ui_cfg_opt_on.png"
PILL_NINE = {"l": 14, "t": 6, "r": 14, "b": 6}
PILL_SRC = ("程序化生成（PIL）→ `工具\\m47_make_config_assets.py`（M47 · W1）；"
            "本件与 `x_ui_cfg_opt_on.png` **同一素材**（同款冰蓝胶囊）")
COVER_NAME = "cfg.cover_c2_05"
COVER_ASSET = "ui/x_ui_psv_cfg_cover_c2_05.png"

# ── ② 10 个二选一行：id 前缀 → (左槽值, 右槽值)。左/右槽值即 `<行>_on` / `<行>_off` 的 vis_when
ROWS = [
    ("display",    "window", "full"),
    ("facewindow", "on",     "off"),
    ("drama",      "on",     "off"),
    ("effect",     "on",     "off"),
    ("voicecut",   "on",     "off"),
    ("curhide",    "on",     "off"),
    ("savedialog", "on",     "off"),
    ("loaddialog", "on",     "off"),
    ("allskip",    "on",     "off"),
    ("textcolchg", "on",     "off"),
]

# ── ④ 两档色板键
INK = "@palette.psv_ink"
INK_DIM = "@palette.psv_ink_dim"
INK_IDS = [
    # 节题（缺陷 ①）
    "cfg.sec_picture", "cfg.sec_confirm", "cfg.sec_text", "cfg.sec_preview",
    "cfg.sec_volume", "cfg.sec_voice", "cfg.sec_charvoice",
    # 行标签（左右栏）+ 声音页行名
    "cfg.row_display_lb", "cfg.row_facewindow_lb", "cfg.row_drama_lb", "cfg.row_effect_lb",
    "cfg.row_voicecut_lb", "cfg.row_curhide_lb", "cfg.row_savedialog_lb", "cfg.row_loaddialog_lb",
    "cfg.row_winopac_lb", "cfg.row_textspeed_lb", "cfg.row_autospeed_lb",
    "cfg.row_allskip_lb", "cfg.row_textcolchg_lb", "cfg.row_cfmovie_lb",
    "cfg.snd_vol_master_lb", "cfg.snd_vol_bgm_lb", "cfg.snd_vol_se_lb",
    "cfg.snd_vol_sysse_lb", "cfg.snd_vol_voice_lb", "cfg.snd_vol_char_lb",
    # 静音 / 滑条两端刻度
    "cfg.snd_vol_master_mute_lb", "cfg.snd_vol_bgm_mute_lb", "cfg.snd_vol_se_mute_lb",
    "cfg.snd_vol_sysse_mute_lb", "cfg.snd_vol_voice_mute_lb", "cfg.snd_vol_char_mute_lb",
    # 页签（未选态）+ 顶右四钮
    "cfg.tab1_tx", "cfg.tab2_tx",
    "cfg.btn_game_tx", "cfg.btn_title_tx", "cfg.btn_end_tx", "cfg.reset_tx",
    # 角色网格名 / 当前角色名
    "cfg.pv_name_asu", "cfg.pv_name_snd",
]
INK_PREFIX = ("cfg.sl_winopac_end_", "cfg.sl_textspeed_end_", "cfg.sl_autospeed_end_",
              "cfg.sl_master_end_", "cfg.sl_bgm_end_", "cfg.sl_se_end_",
              "cfg.sl_sysse_end_", "cfg.sl_voice_end_", "cfg.sl_char_end_")
INK_DIM_IDS = ["cfg.pv_note", "cfg.pv_note_x", "cfg.row_winopac_hint"]

# ── ⑤ 声音页行 5/6 整体下移一个节距
PITCH = 74
SND_MOVE = [("cfg.snd_vol_voice", PITCH), ("cfg.sl_voice", PITCH), ("cfg.o_mute_vol_voice", PITCH),
            ("cfg.snd_vol_char", PITCH), ("cfg.sl_char", PITCH), ("cfg.o_mute_vol_char", PITCH)]
SEC_VOICE_XY = (136, 552)
# ── ⑥ 声音页壳/标签左移 16px 对齐系统页
SND_SHIFT_X = -16
#   注：`cfg.sec_voice` 由 ⑤ 直接写到对齐后的最终 x=136（见 SEC_VOICE_XY），不在此列（否则会被减两次）
SND_SHIFT_IDS = ["cfg.sec_volume"]
SND_SHIFT_PREFIX = ("cfg.tag_snd_", "cfg.snd_vol_")


def put_xy(e, x=None, y=None):
    if x is not None:
        e["x"] = x
    if y is not None:
        e["y"] = y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    with open(SCREEN, encoding="utf-8") as fh:
        doc = json.load(fh)
    els = doc["elements"]
    by = {e["id"]: e for e in els}
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    if not os.path.exists(BACKUP) and not args.dry_run:
        shutil.copy2(SCREEN, BACKUP)          # 只新建不覆盖

    log, added, edited = [], [], []

    def note(a, m):
        log.append("[%s] %s" % (a, m))

    # ============================================================ ① 节题：色 + 让开页签
    for eid in ("cfg.sec_picture", "cfg.sec_volume"):
        e = by[eid]
        if e["y"] == 214:
            put_xy(e, y=218)
            note("①", "%s y 214 → 218（让开页签药丸下缘 216）" % eid)
            edited.append(eid)
    # ============================================================ ④ 色值（含节题）
    for eid in INK_IDS:
        e = by.get(eid)
        if e is None:
            continue
        if e.get("font", {}).get("color") != INK:
            e.setdefault("font", {})["color"] = INK
            edited.append(eid)
    for e in els:
        if any(e["id"].startswith(p) for p in INK_PREFIX) and e.get("font", {}).get("color") != INK:
            e["font"]["color"] = INK
            edited.append(e["id"])
        if e["id"].startswith("cfg.ch_") and e["id"].endswith("_tx") and \
                e.get("font", {}).get("color") != INK:
            e["font"]["color"] = INK
            edited.append(e["id"])
        if e["id"].startswith("cfg.ch_") and e["id"].endswith("_tx_sel") and \
                e.get("font", {}).get("color") != "@palette.panel_fill":
            e["font"]["color"] = "@palette.panel_fill"
            edited.append(e["id"])
    for eid in INK_DIM_IDS:
        e = by.get(eid)
        if e is not None and e.get("font", {}).get("color") != INK_DIM:
            e["font"]["color"] = INK_DIM
            edited.append(eid)
    # `cfg.pv_name_*` 33 件（当前角色名）→ 墨色（底是浅磨砂框）
    for e in els:
        if e["id"].startswith("cfg.pv_name_") and e.get("font", {}).get("color") != INK:
            e["font"]["color"] = INK
            edited.append(e["id"])
    # `cfg.o_*_tx`（非当前值浅字）→ 墨色
    for e in els:
        if e["id"].startswith("cfg.o_") and e["id"].endswith("_tx") and \
                e.get("font", {}).get("color") == "@palette.text_menu":
            e["font"]["color"] = INK
            edited.append(e["id"])

    # ============================================================ ② 右槽「当前值药丸 + 暗字」
    for row, von, voff in ROWS:
        off = by["cfg.o_%s_off" % row]
        txoff = by["cfg.o_%s_off_tx" % row]
        # (a) 右槽当前值药丸（仅增加件）
        sel_id = "cfg.o_%s_off_sel" % row
        if sel_id not in by:
            el = dict(id=sel_id, kind="image", z=23, visible_default=True,
                      asset=PILL, x=off["x"], y=off["y"], w=off["w"], h=off["h"], opacity=255,
                      nine=dict(PILL_NINE), source=PILL_SRC,
                      note=("★ C 组修复（2026-09-26 · 缺陷 ②）：**右槽的「当前值」药丸**。"
                            "全部 10 个二选一行在此对称化：左槽当前值由 `cfg.o_%s_on` 提供药丸，"
                            "右槽当前值原本**无药丸**（`cfg.o_%s_off` 的 normal 是 α≡0 的 "
                            "`x_ui_cfg_opt_off.png`）⇒ 凡当前值落右槽（`%s`）的行整行无药丸。"
                            "本件 `vis_flag=cfg_v_%s` / `vis_when=%s`（**只在此值为当前值时可见**），"
                            "`state_assets`/`state_group` 与 `cfg.o_%s_off` **同组** ⇒ 悬停/按下时"
                            "两件一起换图，不产生叠加。`vis_when` 是缺陷所在一（送审原文："
                            "「若属机制就修 vis_when」）。" % (row, row, voff, row, voff, row)),
                      state_assets={"normal": PILL, "hover": "ui/x_ui_cfg_opt_over.png",
                                    "pressed": PILL},
                      state_group=off.get("state_group"),
                      vis_flag="cfg_v_%s" % row, vis_when=voff)
            idx = els.index(off) + 1
            els.insert(idx, el)
            by[sel_id] = el
            added.append(sel_id)
        # (b) 右槽当前值文字（暗字，压药丸）
        tsel_id = "cfg.o_%s_off_tx_sel" % row
        if tsel_id not in by:
            t = dict(id=tsel_id, kind="text", z=27, visible_default=True,
                     x=txoff["x"], y=txoff["y"], w=txoff["w"], h=txoff["h"],
                     font=dict(txoff["font"], color="@palette.panel_fill"),
                     sample=txoff.get("sample"),
                     note=("★ C 组修复（缺陷 ②）：右槽**当前值**文字（暗字，压 `%s` 的冰蓝药丸）。"
                           "与既有 `cfg.o_%s_on_tx_sel` 逐条对称：色 `@palette.panel_fill`"
                           "（实测压药丸 7.68:1）。`vis_flag=cfg_v_%s` / `vis_when=%s`。"
                           % (sel_id, row, row, voff)),
                     vis_flag="cfg_v_%s" % row, vis_when=voff)
            for k in ("align", "valign", "wrap"):
                if k in txoff:
                    t[k] = txoff[k]
            idx = els.index(txoff) + 1
            els.insert(idx, t)
            by[tsel_id] = t
            added.append(tsel_id)
        # (c) 收窄非当前值浅字的可见条件（页 flag → 值 flag），与 `_on_tx` 互为镜像
        if txoff.get("vis_flag") != "cfg_v_%s" % row or txoff.get("vis_when") != von:
            txoff["vis_flag"] = "cfg_v_%s" % row
            txoff["vis_when"] = von
            txoff["font"]["color"] = INK
            txoff["note"] = (txoff.get("note", "").split("★ C 组修复")[0] +
                             "★ C 组修复（缺陷 ②）：**vis_when 由页 flag 收窄为「左槽值」%s** —— "
                             "本件是「右槽非当前值」的浅字，只应在左槽为当前值时出场；"
                             "右槽为当前值时由 `cfg.o_%s_off_tx_sel`（暗字 + 药丸）接管。"
                             "此改动使两槽的「当前/非当前」完全对称。" % (von, row))
            edited.append(txoff["id"])

    # ============================================================ ⑤ 组标题上移 + 两行下移
    e = by["cfg.sec_voice"]
    done5 = (e["y"] == SEC_VOICE_XY[1])
    if not done5:                       # ★ 幂等：已上移过就不再移行（否则 +74 会叠）
        for el in els:
            if any(el["id"].startswith(p) for p, _ in SND_MOVE):
                el["y"] += PITCH
                edited.append(el["id"])
    # 行名药丸壳：随行下移（壳与行始终配对；下移后 05 盖住原 band6 (650,676)、06 落到 700）
    if by["cfg.tag_snd_05"]["y"] == 552:            # ★ 幂等：已移过则跳过
        for tid in ("cfg.tag_snd_05", "cfg.tag_snd_06"):
            by[tid]["y"] += PITCH
            edited.append(tid)
    e["x"], e["y"] = SEC_VOICE_XY
    e["note"] = ("★ C 组修复（缺陷 ⑤）：节题「语音设定」由**左栏尾**(152,706) 上移到**其组之前**"
                 "——页2 第 5 行槽位 (136,552)；原槽位由下移一个节距的「主音量（语音）」行顶替，"
                 "下部不再留空。页2 的后两行（主音量（语音）/角色音量）**整体下移 74px**"
                 "（槽位 5→6、6→7），下移后露出的残留标签带由 `%s` 盖片抹平。" % COVER_NAME)
    edited.append("cfg.sec_voice")
    if COVER_NAME not in by:
        # 盖片：抹掉下移后露出的页2 行5 残留标签带（见 工具\psv_fix_cfg_residue.py）
        page2 = by["cfg.page2_bg"]
        el = dict(id=COVER_NAME, kind="image", z=9, visible_default=True, asset=COVER_ASSET,
                  x=230, y=570, w=520, h=48, opacity=255,
                  source="由 `cfg.page2_bg` 自身同行的**干净参考列窗**（x900..1200）均值按行铺满 → "
                         "工具\\psv_fix_cfg_residue.py",
                  note="★ C 组修复（缺陷 ⑤ 配套）：**残留标签带盖片** —— 抹掉页2 第 5 行被擦除日文"
                       "行名留下的亮度凹陷（实测 y584..606、最深 5.33/255、x262..~710）。该带原被 "
                       "`cfg.tag_snd_05`(152,552,560,72) 盖住；⑤ 把该行下移一个节距后它会露出，"
                       "故按 m54 的盖槽片口径派生本件。补底取同行干净参考列窗均值 ⇒ **最外 6px "
                       "接缝 max=0.46/255**（面板在这些行严格恒色，实测）。",
                  vis_flag="cfg_page", vis_when="snd")
        idx = els.index(page2) + 1
        els.insert(idx, el)
        by[COVER_NAME] = el
        added.append(COVER_NAME)

    # ============================================================ ⑥ 声音页壳/标签左移 16px
    if by["cfg.tag_snd_01"]["x"] != 136:           # ★ 幂等：已是 136 则跳过
        for el in els:
            if el["id"].endswith("_mute_lb"):
                continue            # 「静音」标签属**值列**（与滑条/勾选框同列），无系统页对应件，不对齐
            if el["id"] in SND_SHIFT_IDS or any(el["id"].startswith(p) for p in SND_SHIFT_PREFIX):
                el["x"] += SND_SHIFT_X
                edited.append(el["id"])
    by["cfg.sec_volume"]["note"] = (by["cfg.sec_volume"].get("note", "").split("★ C 组修复")[0] +
                                    "★ C 组修复（缺陷 ⑥）：x 152 → 136，与系统页 `cfg.sec_picture` "
                                    "同一内缩（两页 PSV 底图 label_zone 本就差 8px(1×)，但药丸壳与"
                                    "行标签均为我方自绘、页面里无烘焙物可对齐 ⇒ 对齐不破坏底图关系，"
                                    "见修复报告 ⑥ 的实测）。")
    for e in els:
        if e["id"].startswith("cfg.tag_snd_"):
            e["note"] = (e.get("note", "").split("★ C 组修复")[0] +
                         "★ C 组修复（缺陷 ⑥）：x 152 → 136，与系统页 `cfg.tag_sys_*` 同一口径"
                         "（壳左沿 136、右沿 696）。")

    # ============================================================ 屏级 note
    doc["note"] = doc["note"].split("\n\n---\n**★ C 组修复")[0] + (
        "\n\n---\n**★ C 组修复（2026-09-26 · ISSUE-20260926-06_C设置屏修复）**\n"
        "· **①节题**：`cfg.sec_*`（7 件）色值 → `@palette.psv_ink`；`cfg.sec_picture`/"
        "`cfg.sec_volume` y 214→218（让开页签药丸下缘 216）。送审指控的「底图日文页标题残留」"
        "经 `工具\\psv_fix_cfg_residue.py` 逐像素检验证伪：那 4 个浅白大字是**引擎绘制**的节题\n"
        "· **②值列药丸**：10 个二选一行各增 `_off_sel`（同款冰蓝药丸，`vis_when`=右槽值）与 "
        "`_off_tx_sel`（暗字）；`_off_tx` 的 `vis_when` 由页 flag 收窄为左槽值 ⇒ 两槽对称、"
        "凡有值即有药丸（根因：`x_ui_cfg_opt_off.png` 的 α 恒 0）\n"
        "· **③预览硬边块**：素材侧柔化（`工具\\psv_fix_preview_bg.py`，过渡带 1px→15px）\n"
        "· **④弱对比**：新增 `psv_ink`/`psv_ink_dim` 两键并逐件改色（清单见 "
        "`psv_config_contrast.py` 输出），预览说明段 #B8B8C8 → #3E4E70（加深 2 档）\n"
        "· **⑤组标题**：`cfg.sec_voice` 上移到 (136,552)（其组之前）；页2 后两行整体下移 74px；"
        "新增 `cfg.cover_c2_05` 盖片抹掉因此露出的残留标签带\n"
        "· **⑥两页对齐**：声音页壳/行标签/喇叭/两个节题 x −16，对齐系统页口径\n"
        "· **语义字段零改**：`flags_default` 25 键、`action`/`value`、`setting`/`min`/`max`/`step`、"
        "既有 `state_assets`/`state_group` 一律未动；仅 `_off_tx` 的 `vis_when` 按 ② 的机制修正收窄。")

    print("=" * 118)
    print("25 设置屏 · 修复轮版面改动%s" % ("（dry-run）" if args.dry_run else ""))
    print("=" * 118)
    for ln in log:
        print(ln)
    print("元素 %d → %d（新增 %d：%s）｜ 改值/改位 %d 件"
          % (len(els) - len(added), len(els), len(added), "、".join(added) or "无", len(set(edited))))
    if args.dry_run:
        print("（dry-run，未写盘）")
        return 0
    with open(SCREEN, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("已写入 %s" % os.path.relpath(SCREEN, UI))
    print("备份（C 组换皮版）：%s" % os.path.relpath(BACKUP, UI))
    return 0


if __name__ == "__main__":
    sys.exit(main())
