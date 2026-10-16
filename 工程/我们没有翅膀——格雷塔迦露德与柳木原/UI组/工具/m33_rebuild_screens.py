# -*- coding: utf-8 -*-
"""M33 · 系统屏重排（用户 2026-09-21 指令）

指令：
  1. 流程图三枚页签重叠 → 加大间距（宽 300、间距 16 → step 316）
  2. 系统菜单/确认框/加载提示/存档/读档 素材偏移 → 素材先归一化（norm_sd.py），
     再按「同族同尺寸 + 网格对齐」重排，元素矩形 = 素材实尺寸（1:1，零缩放）
  3. 音乐鉴赏曲目框完全去掉 → 改为引擎绘制横线分隔
  4. 回想框放大 → 近满屏 + 字号 86 / 行距 1.4 → 7 行
  5. 顺带修 25_config 的页签/音量条尺寸（归一化后 PNG 尺寸变了）

写权限：本脚本只写 layout/screens/*.json（UI 组自有），生成物由 gen_layout.py 产出。
幂等：全量重建这些屏的 elements，重复运行结果一致。
"""
import json, os, io

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(HERE, "..", "layout", "screens")

SD = "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\sd_gen.py + sd_slice.py + norm_sd.py"
FC = "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\build_assets.py"

HEAD = ("**M33（2026-09-21）· 系统屏重排**。承 M31 的「系统屏重置」，本轮按用户反馈修三处结构缺陷：\n"
        "★ ① **素材偏移**：M31 的拆件是按**内容包围盒**逐件裁切的，同族（同一控件的不同状态）PNG 尺寸各不相同"
        "（菜单项 off 407×58 / on 350×58；槽位卡 empty 380×170 / sel 380×204；曲目行 420×150/193/184），"
        "按「图左上角 + 自身尺寸」摆放必然参差、状态切换还会跳动。"
        "**修法**：先用 `工具\\lyai-image-api\\norm_sd.py` 把每族统一到同一画布（内容居中），"
        "再让同族所有元素用**同一个矩形**（w/h = 归一化后的 PNG 实尺寸，1:1 零缩放）。\n"
        "★ ② **曲目框去掉**：用户要求「曲目框完全去掉，引擎画横线分割」——`SD-8-1` 三态底图**已从本屏撤下**，"
        "改用 `rect` 画 2px 分隔线 + 一行高亮块表示「播放中」（与原作《交汇协奏曲》一致，原作也是 GdiPlus 现画）。\n"
        "★ ③ 文字一律由引擎绘制（素材面无字）。")

HEAD_FLOW = ("**M33（2026-09-21）· 页签重叠修复**。M31 把页签底放大到 300×66 后，三枚的 x 仍是 400/596/792"
             "（间距 196 < 宽 300）→ **互相压盖 104px**。本轮改为 **x = 400 / 716 / 1032（step 316，间距 16）**，"
             "页签文字矩形与页签底**同矩形**（原先 y/高 各差 4px，居中会偏）。")


def img(eid, z, asset, x, y, w, h, note, source=SD, opacity=255, nine=None):
    e = {"id": eid, "kind": "image", "z": z, "visible_default": True, "asset": asset,
         "x": x, "y": y, "w": w, "h": h, "opacity": opacity, "source": source, "note": note}
    if nine is not None:
        e["nine"] = nine
    return e


def txt(eid, z, x, y, w, h, sample, size, note, align="center", valign="middle",
        wrap=False, max_lines=1, color="@palette.node_locked", bold=True, line_spacing=None):
    e = {"id": eid, "kind": "text", "z": z, "visible_default": True, "x": x, "y": y, "w": w, "h": h,
         "font": {"size": size, "bold": bold, "color": color, "shadow": False,
                  "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "align": align, "valign": valign, "wrap": wrap, "max_lines": max_lines}
    if line_spacing is not None:
        e["line_spacing"] = line_spacing
    e["sample"] = sample
    e["note"] = note
    return e


def rect(eid, z, x, y, w, h, color, opacity, note):
    return {"id": eid, "kind": "rect", "z": z, "visible_default": True, "x": x, "y": y,
            "w": w, "h": h, "color": color, "opacity": opacity, "note": note}


def hit(eid, z, x, y, w, h, action, label, note):
    return {"id": eid, "kind": "hit", "z": z, "visible_default": True, "x": x, "y": y,
            "w": w, "h": h, "action": action, "label": label,
            "font": {"size": 26, "bold": False, "color": "@palette.node_locked", "shadow": False,
                     "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            "align": "center", "note": note}


BG = "x_gen_sd_9-1_bg.png"


def bg_and_dim(dim):
    return [img("X.bg", 0, "ui/" + BG, 0, 0, 1920, 1080, "满幅底（本批片尾背景，浅冰蓝）"),
            rect("X.dim", 1, 0, 0, 1920, 1080, "@palette.backdrop", dim, "压暗遮罩")]


def with_ids(els, prefix):
    out = []
    for e in els:
        e = dict(e)
        e["id"] = prefix + e["id"][1:]
        out.append(e)
    return out


# ---------------------------------------------------------------- 20 sysmenu（★ M45 已废除）
# ★ M45（2026-09-23，用户裁定）：「现在废除『系统菜单 sysmenu』页，因为我们已有药丸按钮系统。」
#   ⇒ `sysmenu` 屏**已整体废除**：`layout/screens/20_sysmenu.json` 与 `_index.json` 条目已删除，
#     两端活引用（krkr `ui_screens.tjs` / HTML `replica.js` / 复核页导航 / 巡演白名单）已清理，
#     屏数据快照归档 `_工作\M45_旧素材归档\20_sysmenu.json.snapshot`。
#   ⇒ 本模块的 `build_sysmenu()` 与 `__main__` 里对应的 write 调用**一并删除**
#     （保留它只会让人以为还能重建该屏；且它产出的 `ui/x_gen_sd_*` 素材体系早已失效）。
#   ⇒ `工具\test_gen_sync.py` 的 GENERATORS 里 `("build_sysmenu", "20_sysmenu.json")` 条目同步移除。


# ---------------------------------------------------------------- 21 confirm
def build_confirm():
    els = with_ids(bg_and_dim(120), "cf")
    els.append(img("cf.panel", 10, "ui/x_gen_sd_3-1_panel.png", 510, 356, 900, 368,
                   "确认框面板（`SD-3-1` 拆件）。九宫格已去掉 —— 本件是**整块面板**（900×368 原尺寸 1:1），"
                   "与拆件后的实尺寸一致，不需要拉伸。"))
    els.append(txt("cf.msg", 20, 590, 420, 740, 120, "要退出游戏吗？", 32, "确认文案（引擎绘制）"))
    # 两键以面板中心 960 对称：总宽 202+58+202 = 462 → 左起 960-231 = 729
    for eid, ax, label, act in (("cf.yes", 729, "是", "confirm_yes"), ("cf.no", 989, "否", "confirm_no")):
        els.append(img(eid, 20, "ui/x_gen_sd_3-1_btn_%s.png" % ("yes" if act == "confirm_yes" else "no"),
                       ax, 570, 202, 62,
                       "「%s」按钮（`SD-3-1` 拆件，同族 2 件归一化为 202×62）。**两键以面板中心 960 对称**"
                       "（左 729–931 / 右 989–1191，间距 58）。" % label))
        els.append(txt(eid + "_tx", 25, ax, 570, 202, 62, label, 28, "按钮文字（引擎绘制）"))
        els.append(hit("cf.hit_" + ("yes" if act == "confirm_yes" else "no"), 95, ax, 570, 202, 62,
                       act, "", "「%s」热区" % label))
    return {"id": "confirm", "title_cn": "确认框", "owner": "M33", "note": HEAD, "elements": els}


# ---------------------------------------------------------------- 22 loading
def build_loading():
    els = with_ids(bg_and_dim(100), "ld")
    els.append(img("ld.plate", 10, "ui/x_gen_sd_4-1_plate.png", 705, 470, 420, 148,
                   "提示牌（`SD-4-1` 拆件，1:1）。**整组以画布中心 960 居中**："
                   "牌 705–1125 + 间隔 40 + 转圈 1165–1215 → 组宽 510，中心 960。"))
    els.append(txt("ld.text", 20, 705, 470, 420, 148, "加载中……", 32, "提示文字（引擎绘制）"))
    for k, f in (("a", "a"), ("b", "b"), ("c", "c")):
        els.append(img("ld.spin_%s" % k, 10, "ui/x_gen_sd_4-1_spin_%s.png" % f, 1165, 512, 50, 64,
                       "转圈指示第 %s 帧（`SD-4-1` 拆件）。**三帧同矩形**（1165,512）——"
                       "引擎轮播换图，位置不动；HTML 静态渲染时最上层一帧可见。"
                       "竖直中心 512+32 = 544 = 提示牌中心 470+74 ✓" % k.upper()))
    return {"id": "loading", "title_cn": "加载提示", "owner": "M33", "note": HEAD, "elements": els}


# ---------------------------------------------------------------- 23/24 save / load
def build_save(sid, title, tab_a, tab_b):
    els = with_ids(bg_and_dim(70), "sv")
    els.append(img("sv.tab_a", 10, "ui/x_gen_sd_6-1_tab_on.png", 80, 40, 188, 84,
                   "页签底·选中态（`SD-6-1` 拆件，同族 3 件归一化为 188×84）"))
    els.append(txt("sv.tab_a_tx", 20, 80, 40, 188, 84, tab_a, 30, "页签名（引擎绘制）"))
    els.append(img("sv.tab_b", 10, "ui/x_gen_sd_6-1_tab_off.png", 288, 40, 188, 84,
                   "页签底·常态（`SD-6-1` 拆件，同族归一化 188×84）。间距 20。"))
    els.append(txt("sv.tab_b_tx", 20, 288, 40, 188, 84, tab_b, 30, "页签名（引擎绘制）"))
    els.append(img("sv.frame", 5, "ui/x_gen_sd_1-3_panel_frame.png", 120, 190, 1680, 660,
                   "槽位区面板框（`SD-1-3` 通用面板边框，九宫格内缩 150）",
                   nine={"l": 150, "t": 150, "r": 150, "b": 150}))
    # 3 列 × 2 行，卡 380×204（= SD-5-1 归一化后的实尺寸，1:1）
    CW, CH = 380, 204
    COLS, ROWS = [170, 770, 1370], [256, 580]
    STATES = ["empty", "sel", "empty", "hover", "empty", "empty"]
    for i in range(6):
        cx, cy = COLS[i % 3], ROWS[i // 3]
        els.append(img("sv.slot%d" % (i + 1), 20, "ui/x_gen_sd_5-1_slot_%s.png" % STATES[i], cx, cy, CW, CH,
                       "存档槽位卡（`SD-5-1` 拆件，第 %d 槽）。**同族 3 态归一化为统一画布 380×204**"
                       "（原 empty 380×170 vs sel/hover 380×204 → 切态时卡片会长高 34px 跳动）；"
                       "元素矩形 = 素材实尺寸 1:1。" % (i + 1)))
        els.append(txt("sv.num%d" % (i + 1), 25, cx + 18, cy + 22, 140, 26, "第 %d 号" % (i + 1), 22,
                       "槽位号（引擎绘制）。**M33 移进卡内**：卡内可绘区为 y+17..y+187"
                       "（`SD-5-1` 归一化时把原 170 高的卡体居中放进 204 高的画布），"
                       "原 M31 把槽位号放在 y+8 会落到卡体上沿之外、与卡内信息重复。", align="left"))
        els.append(img("sv.thumb%d" % (i + 1), 21, "ui/x_gen_sd_5-2_thumb_frame.png",
                       cx + 18, cy + 48, 134, 134,
                       "槽位缩略图框（`SD-5-2` 拆件，源 300×300）。**整图等比缩小 0.447×** → 用 "
                       "`nine:{0,0,0,0}`（schema §六「全零九宫格 = 允许整图等比缩放」）。"
                       "**原 M31 把 300×300 直接塞进 380×170 的卡里 → 缩略图越出卡片下沿 146px**，本轮修正。",
                       nine={"l": 0, "t": 0, "r": 0, "b": 0}))
        els.append(txt("sv.info%d" % (i + 1), 25, cx + 170, cy + 58, 192, 110,
                       "2026-09-21 04:30\n第 1 章 前奏诗", 20,
                       "槽位信息（引擎绘制；真值由编程组填充）",
                       align="left", valign="top", wrap=True, max_lines=3))
        els.append(hit("sv.hit%d" % (i + 1), 95, cx, cy, CW, CH, "slot_%d" % (i + 1), "",
                       "槽位热区（矩形与卡片同矩形）"))
    for i, px in enumerate((855, 910, 965, 1020), 1):
        els.append(img("sv.pg%d" % i, 20, "ui/x_gen_sd_5-2_pg%d.png" % i, px, 880, 45, 46,
                       "页码键 %d（`SD-5-2` 拆件，同族归一化 45×46；间距 10）" % i))
    els.append(img("sv.back", 20, "ui/x_gen_sd_1-1_back_off.png", 1560, 940, 224, 64, "返回按钮（`SD-1-1` 归一化 224×64）"))
    els.append(hit("sv.hit_back", 95, 1560, 940, 224, 64, "close", "返回", "返回热区"))
    return {"id": sid, "title_cn": title, "owner": "M33", "note": HEAD, "elements": els}


# ---------------------------------------------------------------- 25 config
def build_config():
    els = with_ids(bg_and_dim(70), "cf")
    TABS = ["画面", "声音", "文字", "系统"]
    for i, t in enumerate(TABS):
        x = 100 + i * 250
        asset = "ui/x_gen_sd_6-1_tab_%s.png" % ("on" if i == 0 else "off")
        els.append(img("cfg.tab%d" % (i + 1), 10, asset, x, 40, 188, 84,
                       "页签底（`SD-6-1` 拆件，同族归一化 188×84）。**M33 修**：原 on 写 171、off 写 188，"
                       "归一化后一律 188×84，间距 250（原 250/250/250 不变）。"))
        els.append(txt("cfg.tab%d_tx" % (i + 1), 20, x, 40, 188, 84, t, 28, "页签名（引擎绘制）"))
    LB = ["背景音乐音量", "音效音量", "语音音量", "文字速度", "自动播放速度", "跳过未读文本"]
    for i, name in enumerate(LB):
        y = 220 + i * 110
        els.append(txt("cfg.lb%d" % (i + 1), 20, 140, y, 360, 60, name, 28,
                       "配置项名（引擎绘制）。**14 项标签仍为暂定中文（既有未决项 U6）**", align="left"))
        els.append(img("cfg.sl%d" % (i + 1), 20, "ui/x_gen_sd_6-2_slider.png", 540, y + 6, 300, 101,
                       "滑条（`SD-6-2` 拆件，1:1）"))
    els.append(img("cfg.chk_off", 20, "ui/x_gen_sd_6-2_check_off.png", 540, 776, 43, 44, "勾选框·未选（`SD-6-2`）"))
    els.append(img("cfg.chk_on", 20, "ui/x_gen_sd_6-2_check_on.png", 620, 776, 43, 44, "勾选框·已选（`SD-6-2`）"))
    els.append(img("cfg.arrow", 20, "ui/x_gen_sd_6-2_arrow.png", 720, 776, 43, 42, "下拉箭头（`SD-6-2`）"))
    els.append(img("cfg.vbar_a", 20, "ui/x_gen_sd_6-2_vbar_a.png", 1000, 240, 300, 110,
                   "音量条示例 A（`SD-6-2`，**M33 修**：归一化后 300×110，原写 101）"))
    els.append(img("cfg.vbar_b", 20, "ui/x_gen_sd_6-2_vbar_b.png", 1000, 360, 300, 110, "音量条示例 B（`SD-6-2`，1:1）"))
    els.append(img("cfg.back", 20, "ui/x_gen_sd_1-1_back_off.png", 60, 960, 224, 64, "返回按钮（`SD-1-1` 归一化 224×64）"))
    els.append(hit("cfg.hit_back", 95, 60, 960, 224, 64, "close", "返回", "返回热区"))
    return {"id": "config", "title_cn": "配置", "owner": "M33", "note": HEAD, "elements": els}


# ---------------------------------------------------------------- 26 backlog
def build_backlog():
    els = with_ids(bg_and_dim(60), "bl")
    els.append(img("bl.frame", 5, "ui/x_gen_sd_1-3_panel_frame.png", 8, 8, 1904, 1064,
                   "回想文本面板框（`SD-1-3` 九宫格内缩 150）。**M33 按用户要求放大**："
                   "原 1520×800（画布占比 79%×74%）→ **1904×1064（占比 99%×98.5%，近满屏）**。",
                   nine={"l": 150, "t": 150, "r": 150, "b": 150}))
    els.append(txt("bl.text", 20, 210, 150, 1460, 800,
                   "这里是回想文本区。\n\n引擎按行渲染已读台词。\n\n"
                   "字号 81 / 行距 1.4 → 单行高 floor(81×1.4)=113。\n\n"
                   "七行块高 7×113 = 791 ≤ 文本区高 800。\n\n"
                   "再多的台词由引擎向上滚动。",
                   81, "回想正文（引擎绘制，取自 scene_*.jsonl 已读台词）。"
                   "**行数按用户要求取 7**。**行高说明（偏离已上报）**：用户要求「每行文字高度 200px」，"
                   "但 7×200 = 1400px > 画布高 1080px，物理不可行 —— 故取**画布内能容下 7 行的最大行高**："
                   "面板放到近满屏（1904×1064）后，避开四角装饰（九宫格内缩 150 + 余量）得文本区 1460×800，"
                   "800÷7 = 114 → 字号 81 / 行距 1.4 → 行高 113 → 7 行共 791。"
                   "字号 81 是原 M31 字号 30 的 **2.7 倍**。",
                   align="left", valign="top", wrap=True, max_lines=7, line_spacing=1.4))
    els.append(img("bl.close", 20, "ui/x_gen_sd_1-2_close_off.png", 1745, 70, 50, 48,
                   "关闭键（`SD-1-2` 拆件，同族归一化 50×48）。★ **M33 修正错件**：M31 时 `1-2` 的九件"
                   "被按「行=控件、列=态」错命名（实测行=态、列=控件）→ 原名 `close_off` 其实是✕、"
                   "`close_on` 是▼、`close_over` 是▲。已由 `工具\\lyai-image-api\\fix_sd_transpose.py` 转置修正。"))
    els.append(img("bl.spk_off", 20, "ui/x_gen_sd_7-1_spk_off.png", 1747, 150, 46, 64,
                   "语音重播键·常态（`SD-7-1` 拆件，同族归一化 46×64）"))
    els.append(img("bl.spk_on", 20, "ui/x_gen_sd_7-1_spk_on.png", 1747, 150, 46, 64,
                   "语音重播键·亮（**与常态同矩形** —— 原 M31 把两态摆成上下两处，切态会跳）"))
    els.append(img("bl.up", 20, "ui/x_gen_sd_1-2_up_off.png", 1745, 720, 50, 48,
                   "滚动上·常态（`SD-1-2` 拆件，归一化 50×48；**已转置修正为 ▲**）"))
    els.append(img("bl.down", 20, "ui/x_gen_sd_1-2_down_off.png", 1745, 780, 50, 48,
                   "滚动下·常态（`SD-1-2`，归一化 50×48；**已转置修正为 ▼**）"))
    els.append(img("bl.pill_off", 20, "ui/x_gen_sd_7-1_pill_off.png", 130, 960, 157, 100,
                   "跳转按钮（`SD-7-1` 拆件，同族归一化 157×100）"))
    els.append(txt("bl.pill_tx", 25, 130, 960, 157, 100, "跳转", 28, "按钮文字（引擎绘制）"))
    els.append(hit("bl.hit_back", 95, 1560, 960, 260, 80, "close", "返回", "返回热区"))
    return {"id": "backlog", "title_cn": "回想", "owner": "M33", "note": HEAD, "elements": els}


# ---------------------------------------------------------------- 28 music
def build_music():
    els = with_ids(bg_and_dim(70), "mu")
    els.append(img("mu.frame", 5, "ui/x_gen_sd_1-3_panel_frame.png", 120, 80, 1680, 580,
                   "曲目列表面板框（`SD-1-3` 九宫格内缩 150）", nine={"l": 150, "t": 150, "r": 150, "b": 150}))
    # 播放中高亮（在面板框之上、文字之下）
    els.append(rect("mu.hl", 6, 290, 300, 1320, 100, "@palette.accent", 55,
                    "「播放中」行高亮（**程序化 rect**，随当前曲目移动）"))
    ROWS = [100, 200, 300, 400, 500]
    for i, ry in enumerate(ROWS, 1):
        els.append(txt("mu.row%d_tx" % i, 25, 310, ry, 1280, 100,
                       "第 %d 曲　—　曲名（取自资源组产物）" % i, 34,
                       "曲名行文字（引擎绘制）。**M33：曲目底图 `SD-8-1` 三态已从本屏撤下**（用户要求"
                       "「曲目框完全去掉，引擎画横线分割」）。行高 100，5 行 = 500。"
                       "行文字 x=310 / 宽 1280（右沿 1590）—— **避开面板框四角装饰**"
                       "（九宫格内缩 150，装饰区约占 x 120–290），并给右侧留位。", align="left"))
        els.append(rect("mu.sep%d" % i, 22, 300, ry + 98, 1320, 2, "@palette.panel_edge", 170,
                        "曲目分隔横线第 %d 条（**程序化 rect，2px**——原作《交汇协奏曲》的分隔线同样是现画的）。"
                        "x 300–1620，与行文字同起止，避开左右装饰角。" % i))
        els.append(hit("mu.hit%d" % i, 95, 150, ry, 1560, 100, "", "",
                       "曲目行热区。**action 留空**：schema §六「动作表未覆盖的控件（music 曲目行）允许写空串，"
                       "不得臆造 action 名」——待编程组定义。"))
    PB = [("play", "播放"), ("pause", "暂停"), ("stop", "停止"), ("repeat", "循环")]
    for i, (key, label) in enumerate(PB):
        x = 796 + i * 88
        els.append(img("mu.pb%d" % (i + 1), 20, "ui/x_gen_sd_8-2_%s.png" % key, x, 700, 64, 76,
                       "播放控制「%s」键（`SD-8-2` 拆件，同族归一化 64×76）。四键以画布中心 960 居中"
                       "（796–1124，间距 24）。" % label))
        els.append(hit("mu.hit_pb%d" % (i + 1), 95, x, 700, 64, 76, "", "",
                       "「%s」热区。action 留空（schema §六：music 播放控制 4 键允许空 action）" % label))
    els.append(img("mu.spec", 20, "ui/x_gen_sd_8-2_spectrum.png", 1620, 660, 191, 240,
                   "音谱装饰（`SD-8-2` 拆件，1:1）。摆右下，与返回键（y=940）不重叠。"))
    els.append(img("mu.back", 20, "ui/x_gen_sd_1-1_back_off.png", 1560, 940, 224, 64, "返回按钮（`SD-1-1` 归一化 224×64）"))
    els.append(hit("mu.hit_back", 95, 1560, 940, 224, 64, "close", "返回", "返回热区"))
    return {"id": "music", "title_cn": "音乐鉴赏", "owner": "M33", "note": HEAD, "elements": els}


# ---------------------------------------------------------------- 32 flowchart tabs
def patch_flowchart():
    p = os.path.join(SCR, "32_flowchart.json")
    d = json.load(open(p, encoding="utf-8"))
    d["note"] = d["note"] + "\n\n★ **M33（2026-09-21）· 页签重叠修复**：" + HEAD_FLOW.split("。", 1)[1]
    TAB_X = [400, 716, 1032]
    for i, x in enumerate(TAB_X, 1):
        for e in d["elements"]:
            if e["id"] == "flow.tab%d" % i:
                e["x"] = x
                e["y"] = 42
                e["w"] = 300
                e["h"] = 66
                e["note"] = ("页签底第 %d 枚（FC-4-3 三态之一）。页签名由引擎绘制。"
                             "**M33 修重叠**：原 x=400/596/792（间距 196 < 宽 300，互相压盖 104px）→ "
                             "改为 **400/716/1032（step 316，间距 16）**。" % i)
            elif e["id"] == "flow.tab%d_tx" % i:
                e["x"] = x
                e["y"] = 42
                e["w"] = 300
                e["h"] = 66
                e["note"] = "页签名（引擎绘制）。**矩形与页签底完全一致**（原 y=38/h=70，与底差 4px → 居中偏）。"
    for e in d["elements"]:
        if e["id"] == "flow.newmark":
            e["x"] = 1380
            e["note"] = "NEW 新内容标记（FC-4-2，80×25）。**M33 移出页签带**：原 x=1090 会被放大后的第 3 枚页签（1032–1332）压住。"
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("32_flowchart.json  页签 x -> %s" % TAB_X)


# ---------------------------------------------------------------- main
def write(name, obj):
    p = os.path.join(SCR, name)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("%-22s %2d 元素" % (name, len(obj["elements"])))


if __name__ == "__main__":
    # ★ M45（2026-09-23）：`write("20_sysmenu.json", build_sysmenu())` 已删除 —— 该屏已整体废除。
    write("21_confirm.json", build_confirm())
    write("22_loading.json", build_loading())
    write("23_save.json", build_save("save", "存档", "存档", "读档"))
    write("24_load.json", build_save("load", "读档", "读档", "存档"))
    write("25_config.json", build_config())
    write("26_backlog.json", build_backlog())
    write("28_music.json", build_music())
    patch_flowchart()