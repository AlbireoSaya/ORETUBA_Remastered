# -*- coding: utf-8 -*-
r"""
M23_gen.py —— UI 美术组 · M23（压缩素材统一缩放成果应用 + 新对话框）
==================================================================
把 M22 重建的「整图统一倍率缩放」素材**应用进 layout**（不缩放、1:1 摆放）：

  ① 01_title.json   7 个菜单按钮（439×122，k=0.7）**按内容包围盒右边缘居右**对齐屏幕右边
  ② 33_sysicons.json 9 个功能图标（351×234，k=0.685547）3×3 网格 **1:1**
  ③ 32_flowchart.json 4 种方框（562–584×108–112，k=0.491228）**1:1 居中于 584×112 槽位**（取消 nine 缩放）
  ④ 10_dialog.json  对话窗换 ui/x_gen_dialog2.png（1628×319，k=1.0），贴底居中、下留 36 px
  ⑤ _index.json     四行 required 同步

几何来源：`_工作/M22_生成几何.json`（M22 实测，**直接消费，不得自己估**）。

用法（幂等）：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
    python _工作/M23_gen.py
"""

import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))          # <UI组>/_工作
ROOT = os.path.dirname(HERE)                               # <UI组>
SCREENS = os.path.join(ROOT, "layout", "screens")
GEO = os.path.join(HERE, "M22_生成几何.json")

# ------------------------------------------------------------------ 画布
CANVAS_W = 1920
CANVAS_H = 1080

# ------------------------------------------------------------------ 工具


def load(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, o):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)
        f.write("\n")


GEO_D = load(GEO)


# ================================================================== ① 标题
def build_title():
    p = os.path.join(SCREENS, "01_title.json")
    t = load(p)

    RIGHT = 1904          # 屏幕右边 1920 − 16 px 边距（可调；依据见 M23 报告）
    ROW_H = 122           # 按钮图高 = 格高（M22 统一行高）
    N = 7
    top = (CANVAS_H - N * ROW_H) // 2          # (1080 − 854)/2 = 113

    ACTIONS = {
        "start": "game_start",
        "continue": "game_continue",
        "load": "open_load",
        "flowchart": "open_flowchart",
        "extra": "open_gallery",
        "config": "open_config",
        "exit": "quit_game",
    }

    items = GEO_D["menu"]["items"]
    new_els = []
    xs = []
    for i, it in enumerate(items):
        idx = it["index"]
        sem = it["semantic"]
        label_cn = it["label_cn"]
        label_en = it["label_en"]
        nb = it["normal"]["content_bbox_in_cell"]
        hb = it["hover"]["content_bbox_in_cell"]
        content_right = nb[0] + nb[2]
        hover_right = hb[0] + hb[2]
        x = RIGHT - content_right
        y = top + i * ROW_H
        xs.append((sem, x, y, content_right, hover_right))

        new_els.append({
            "id": "title.menu_img_%d" % idx,
            "kind": "image",
            "z": 20,
            "visible_default": True,
            "asset": "ui/%s" % it["normal"]["file"],
            "x": x,
            "y": y,
            "w": 439,
            "h": 122,
            "opacity": 255,
            "source": "M22 派生（工具/prep_generated.py）：生图入料\\生成结果\\系统屏底图重置.png（1254×1254 RGBA）整图按 k=0.7 缩放一次 → 878×878 → 2 列 × 7 行统一网格切分（格 439×122，行原点 y=8）→ 第 %d 行左列（常态）" % idx,
            "note": "菜单第 %d 项「%s / %s」常态图（银白）。图上已烘焙中英文，故不叠引擎文字。**1:1 摆放**：w/h=439×122 = PNG 实际尺寸（无 nine、无缩放）。**右边缘对齐**：图内内容包围盒右缘 = %d（M22 实测 content_bbox_in_cell = %s），故 x = %d − %d = %d，使小翅膀右尖端落在画布 x=%d。" % (
                idx, label_cn, label_en, content_right, nb, RIGHT, content_right, x, RIGHT),
        })

    for i, it in enumerate(items):
        idx = it["index"]
        sem = it["semantic"]
        nb = it["normal"]["content_bbox_in_cell"]
        hb = it["hover"]["content_bbox_in_cell"]
        content_right = nb[0] + nb[2]
        hover_right = hb[0] + hb[2]
        x = RIGHT - content_right
        y = top + i * ROW_H
        new_els.append({
            "id": "title.menu_hit_%d" % idx,
            "kind": "hit",
            "z": 30,
            "visible_default": True,
            "x": x,
            "y": y,
            "w": 439,
            "h": 122,
            "action": ACTIONS[sem],
            "label": "",
            "state_assets": {
                "normal": "ui/%s" % it["normal"]["file"],
                "hover": "ui/%s" % it["hover"]["file"],
            },
            "source": "M22 派生：系统屏底图重置.png 第 %d 行（左常态 / 右高亮），两态同格 439×122" % idx,
            "note": "热区「%s / %s」（action=%s）。hover 为金色高亮态，由 krkr 侧 UIScrHoverHit 驱动。label 为空串（图上已烘焙文字，不叠引擎文字）。**几何与 title.menu_img_%d 完全一致**（x=%d, y=%d, 439×122）。⚠ 源图两态内容右缘略有差（常态 %d / 高亮 %d，差 %d px）：本屏按**常态**定位（M22 报告建议），故悬停时高亮内容右缘会较常态左移 %d px —— 这是源图两态自身的内容偏移，非本屏缩放造成。" % (
                it["label_cn"], it["label_en"], ACTIONS[sem], idx, x, y,
                content_right, hover_right, content_right - hover_right, content_right - hover_right),
        })

    # 保留 bg / logo / text_copyright，插入菜单组
    out = []
    for e in t["elements"]:
        if e["id"].startswith("title.menu_"):
            continue
        out.append(e)
        if e["id"] == "title.logo":
            out.extend(new_els)

    t["elements"] = out
    # 幂等：先剥掉上一次运行追加的 M23 段，再重新追加（否则连跑会重复累积）
    base = t["note"].split("\n\n★ M23 应用（2026-09-20）：")[0]
    t["note"] = (
        base
        + "\n\n★ M23 应用（2026-09-20）：菜单 7 项改用 M22 重建的 439×122 按钮图（**整图统一倍率 k=0.7** 的产物，14 件含 `_on` 同尺寸、件内倍率一致）。"
        + "**菜单按钮按内容右边缘居右对齐（用户要求）**：x = 1904 − content_bbox_in_cell 右缘（RIGHT=1920−16=1904，留 16 px 边距，可调），"
        + "使 7 项的小翅膀右尖端落在同一条竖线 x=1904 上；纵向 7×122=854 在 1080 内垂直居中（首项 y=113）。"
        + "image(z=20) 与 hit(z=30) 各 7 个，坐标完全一致；**image 的 w/h=439×122 = PNG 实尺寸（无 nine、不缩放）**。"
    )
    save(p, t)
    return xs


# ================================================================ ② 图标浮层
def build_sysicons():
    p = os.path.join(SCREENS, "33_sysicons.json")
    t = load(p)

    grid = GEO_D["icons"]["grid"]
    cw, ch = grid["cell"]                       # 351 × 234
    gw, gh = grid["grid_size"]                  # 1053 × 702
    ox = (CANVAS_W - gw) // 2                   # 433
    oy = (CANVAS_H - gh) // 2                   # 189

    ACTIONS = [
        ("01_qsave", "do_quicksave", "Q.SAVE（快速存档）"),
        ("02_qload", "do_quickload", "Q.LOAD（快速读档）"),
        ("03_skip", "skip_on", "SKIP（快进）"),
        ("04_prev", "prev_choice", "PREV（返回上一选项）"),
        ("05_save", "open_save", "SAVE（存档）"),
        ("06_load", "open_load", "LOAD（读档）"),
        ("07_config", "open_config", "CONFIG（设置）"),
        ("08_close", "hide_window", "CLOSE（隐藏对话框）"),
        ("09_repeat", "replay_voice", "REPEAT（重复语音）"),
    ]

    cells = []
    for i in range(9):
        r, c = divmod(i, 3)
        cells.append((ox + c * cw, oy + r * ch))
    assert ox + gw <= CANVAS_W and oy + gh <= CANVAS_H

    new_els = []
    for i, (suffix, action, human) in enumerate(ACTIONS):
        idx = i + 1
        x, y = cells[i]
        item = GEO_D["icons"]["items"][i]
        f = item["file"]
        new_els.append({
            "id": "sysicons.icon_%s" % suffix,
            "kind": "image",
            "z": 10 + i,
            "visible_default": True,
            "asset": "ui/%s" % f,
            "x": x,
            "y": y,
            "w": cw,
            "h": ch,
            "opacity": 255,
            "source": "M22 派生（工具/prep_generated.py）：生图入料\\生成结果\\功能图标.png（1536×1024）整图按 k=0.685547 缩放一次 → 1053×702 → 3×3 等分（格 351×234）→ 第 %d 格" % idx,
            "note": "图标 %d/9 = %s。**1:1 摆放**：w/h=351×234 = PNG 实际尺寸（**不带 nine**，M22 未决 #4 明确要求）；x/y = 3×3 网格第 (行 %d, 列 %d) 格左上角（网格整体 1053×702 居中于 1920×1080，起点 %d,%d；列步 351、行步 234）。" % (
                idx, human, i // 3, i % 3, ox, oy),
        })
        new_els.append({
            "id": "sysicons.hit_%s" % suffix,
            "kind": "hit",
            "z": 30 + i,
            "visible_default": True,
            "x": x,
            "y": y,
            "w": cw,
            "h": ch,
            "action": action,
            "label": "",
            "source": "UI 组自制：图标 %d 的点击热区（不画图，矩形 = 该格矩形）" % idx,
            "note": "%s 热区（action=%s）。矩形 = 该格矩形（351×234），格与格相邻不重叠。" % (human.split("（")[0], action),
        })

    # 保留 veil / dismiss
    out = [e for e in t["elements"] if not e["id"].startswith("sysicons.icon_") and not e["id"].startswith("sysicons.hit_")]
    out.extend(new_els)

    t["elements"] = out
    t["note"] = (
        "M13 新建（2026-09-20）／**M23 应用 M22 统一缩放成果（2026-09-20）**。**右键呼出的图标浮层**：9 图标来自用户 AI 生成的 生图入料\\生成结果\\功能图标.png。"
        "★ M23：9 图标为**整图统一倍率 k=0.685547 的产物，件内倍率一致**（1536×1024 → 1053×702 → 3×3 等分），**9 件同为 351×234**；"
        "本屏按 **3×3 网格 1:1 摆放**（网格 1053×702 居中于 1920×1080，起点 433,189；列步 351、行步 234），"
        "每个 image 的 w/h=351×234 = PNG 实尺寸、**不带 nine**，hit 矩形 = 该格矩形。**标签为图上烘焙的英文**（Q.SAVE / Q.LOAD / SKIP / PREV / SAVE / LOAD / CONFIG / CLOSE / REPEAT），故本屏**不叠任何引擎文字、不设 item_frame**。"
        "结构 = 全屏压暗 rect 遮罩 + 3×3 网格 9 个 image + 每项一个 hit（外加热区「点击空白处关闭」）。呼出方式：对话框屏内按鼠标右键（krkr 侧 startup.tjs 的 onMouseDown，mb=1=右键）；屏内左键点图标执行其动作、点空白处或再按右键收起。"
        "★ 旧版（M13/M17）用 `nine:{l:0,t:0,r:0,b:0}` 把 192×192…280 的图标整图缩放并绕开 1:1 防线；**M23 已改为 1:1 无 nine**（M22 未决 #4）。"
    )
    save(p, t)
    return cells


# ================================================================ ③ 流程图
SLOT_W, SLOT_H = 584, 112
COL_X = [300, 1068]
ROW_Y = [110 + r * 120 for r in range(7)]
LABEL_MARGIN = 96
LABEL_W = SLOT_W - 2 * LABEL_MARGIN          # 392

TYPES = {
    "normal": ("x_gen_flownode_1_normal.png", 562, 108, "一般剧情",
               "方框类型判定依据：一般剧情 —— 开篇/框架/短篇集，§五 结局矩阵无其结局"),
    "badend": ("x_gen_flownode_2_badend.png", 584, 112, "BAD END / 普通结局",
               "方框类型判定依据：BAD END / 普通结局 —— 幕内含明确 Ｂ－ＥＮＤ"),
    "important": ("x_gen_flownode_3_important.png", 577, 112, "重要章节（影响后续剧情发展）",
                  "方框类型判定依据：重要章节 —— 关键分歧点，影响后续剧情发展"),
    "goodend": ("x_gen_flownode_4_goodend.png", 572, 110, "GOOD END（包括女主角非坏结局的结尾）",
                "方框类型判定依据：GOOD END —— 幕内含女主角非坏结局 / 真结局"),
}

# (el, node_id, type, col, row, sample, 来源句)
NODES = [
    ("flow.n01", "N01", "normal", 0, 0, "前奏诗·框架剧与四短篇\notp · 22 场景 / 3531 行",
     "spine.json acts[0]（幕 1）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n02", "N02", "normal", 0, 1, "前奏诗·系统脚本\notp · 5 场景 / 92 行",
     "spine.json acts[1]（幕 2）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n03", "N03", "normal", 0, 2, "本篇·序文\not · 1 场景 / 2 行",
     "spine.json acts[2]（幕 3）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n04", "N04", "goodend", 0, 3, "本篇·s01 鹰志线\not · 114 场景 / 13969 行",
     "spine.json acts[3]（幕 4）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.b01", "B01", "important", 0, 4, "分歧点 s01 鹰志线\n2 选项 · ot_s01_02c",
     "spine.json branch_points[]（scene_id=ot_s01_02c，选项 2 条）：选项数与场景 id 取自数据，未自造。"),
    ("flow.n08", "N08", "goodend", 0, 5, "PSV 美咲线（同期分支）\notv · 31 场景 / 4931 行",
     "spine.json acts[7]（幕 8）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n05", "N05", "goodend", 0, 6, "本篇·s02 鹫介线\not · 83 场景 / 12327 行",
     "spine.json acts[4]（幕 5）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n06", "N06", "goodend", 1, 0, "本篇·s03 隼人线\not · 95 场景 / 17389 行",
     "spine.json acts[5]（幕 6）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.b02", "B02", "important", 1, 1, "分歧点 s03_09a\n0 选项 · s03_09a",
     "spine.json branch_points[]（scene_id=s03_09a，选项 0 条）：选项数与场景 id 取自数据，未自造。"),
    ("flow.n07", "N07", "goodend", 1, 2, "亚衣线·s03c（R 版 55 场景版）\notr · 55 场景 / 6911 行",
     "spine.json acts[6]（幕 7）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n09", "N09", "goodend", 1, 3, "大路线 s04（最终章）\not · 74 场景 / 11993 行",
     "spine.json acts[8]（幕 9）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n10", "N10", "badend", 1, 4, "After Story·主线\nota · 119 场景 / 13139 行",
     "spine.json acts[9]（幕 10）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
    ("flow.n11", "N11", "normal", 1, 5, "涅布＊プラス 明日香篇\nnp · 28 场景 / 1961 行",
     "spine.json acts[10]（幕 11）：幕名逐字取自 acts[].name，未自造；规模取自 acts[].scenes 与 acts[].line_count。"),
]


def _node_geom(col, row, w, h):
    sx, sy = COL_X[col], ROW_Y[row]
    dx, dy = (SLOT_W - w) // 2, (SLOT_H - h) // 2
    return sx + dx, sy + dy


def build_flowchart():
    p = os.path.join(SCREENS, "32_flowchart.json")
    old = load(p)
    old_by_id = {}
    for e in old["elements"]:
        old_by_id[e["id"]] = e

    els = []
    els.append(old_by_id["flow.bg"])

    col_cx = [COL_X[c] + SLOT_W // 2 for c in range(2)]     # 592 / 1360
    gap_l, gap_r = COL_X[0] + SLOT_W, COL_X[1]              # 884 / 1068
    bus_x = (gap_l + gap_r) // 2 - 2                        # 976 − 2 = 974
    wrap_x = 1024
    row_cy = [y + SLOT_H // 2 for y in ROW_Y]               # 166 286 406 526 646 766 886

    # ---- 纵向连接条（同列相邻行）11 条，id 与 ui_flow_data.tjs 的 E01..E16 对应不变
    seq_pairs = [
        ("flow.seq01", 0, 0, "N01", "N02"), ("flow.seq02", 0, 1, "N02", "N03"),
        ("flow.seq03", 0, 2, "N03", "N04"), ("flow.seq04", 0, 3, "N04", "B01"),
        ("flow.seq05", 0, 4, "B01", "N08"), ("flow.seq06", 0, 5, "N08", "N05"),
        ("flow.seq07", 1, 0, "N06", "B02"), ("flow.seq08", 1, 1, "B02", "N07"),
        ("flow.seq09", 1, 2, "N07", "N09"), ("flow.seq10", 1, 3, "N09", "N10"),
        ("flow.seq11", 1, 4, "N10", "N11"),
    ]
    for eid, c, r, a, b in seq_pairs:
        x = col_cx[c] - 2
        y = ROW_Y[r] + SLOT_H
        els.append({
            "id": eid, "kind": "rect", "z": 11, "visible_default": True,
            "x": x, "y": y, "w": 4, "h": 8,
            "color": "@palette.edge_line", "opacity": 255,
            "note": "纵向连接条：%s → %s（同一列、相邻行）。几何依据：x = 槽位水平中线 − 半条宽（%d + 292 − 2 = %d），y = 上一行槽位底（%d），高 = 行间距 8。★ M23：按 584 宽槽位重算（旧为 552 宽方框，中线 576/1344）。" % (
                a, b, COL_X[c], x, y),
        })

    # ---- 跨列续接线 N05 → N06（三段）
    els.append({
        "id": "flow.wrap_a", "kind": "rect", "z": 11, "visible_default": True,
        "x": gap_l, "y": row_cy[6] - 2, "w": wrap_x - gap_l, "h": 4,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "跨列续接线第 1 段（横）：从 N05 所在槽位右边界（x=%d）右行到纵向通道 x=%d。★ M23 重排（旧从 852 起）。" % (gap_l, wrap_x),
    })
    els.append({
        "id": "flow.wrap_b", "kind": "rect", "z": 11, "visible_default": True,
        "x": wrap_x - 2, "y": 140, "w": 4, "h": 746,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "跨列续接线第 2 段（纵）：沿 x=%d 从 N06 的接入高度 y=140 下到 N05 的垂直中线 y=%d。接入高度取 140 而非行中线 %d，是为避开同一条 N06 左边上的汇流短横条（y=%d）。★ M23 重排（旧 x=1022，未变）。" % (wrap_x, row_cy[6], row_cy[0], 190),
    })
    els.append({
        "id": "flow.wrap_c", "kind": "rect", "z": 11, "visible_default": True,
        "x": wrap_x, "y": 138, "w": gap_r - wrap_x, "h": 4,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "跨列续接线第 3 段（横）：从纵向通道 x=%d 接到 N06 所在槽位左边界（x=%d）。★ 该段**不对应任何真实边**（叙事顺序里 N05→N06 是两条平行线 s02/s03 的并列），只表示「阅读顺序在第 2 列顶部继续」。★ M23 重排（旧 1024→1068，未变）。" % (wrap_x, gap_r),
    })

    # ---- 左侧旁路 E02（N01 → N03）
    n01_box_x = _node_geom(0, 0, 562, 108)[0]
    n03_box_x = _node_geom(0, 2, 562, 108)[0]
    chan = 250
    els.append({
        "id": "flow.e02_a", "kind": "rect", "z": 12, "visible_default": True,
        "x": chan, "y": row_cy[0] - 2, "w": n01_box_x - chan, "h": 4,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "左侧旁路第 1 段（横）：N01 方框左边界（x=%d）→ 旁路通道 x=%d（对应真实边 E02：N01→N03，主线顺序 1→3）。★ M23：终点由槽位左边界 300 改为方框实左边界 %d（新方框在 584 槽位内居中，内缩 11 px）。" % (n01_box_x, chan, n01_box_x),
    })
    els.append({
        "id": "flow.e02_b", "kind": "rect", "z": 12, "visible_default": True,
        "x": chan - 2, "y": row_cy[0], "w": 4, "h": row_cy[2] - row_cy[0],
        "color": "@palette.edge_line", "opacity": 255,
        "note": "左侧旁路第 2 段（纵）：沿 x=%d 从 N01 的垂直中线 y=%d 下到 N03 的垂直中线 y=%d。通道取 %d，在第 1 列槽位左边界 %d 之外 50 px，故不压到任何方框。" % (chan, row_cy[0], row_cy[2], chan, COL_X[0]),
    })
    els.append({
        "id": "flow.e02_c", "kind": "rect", "z": 12, "visible_default": True,
        "x": chan, "y": row_cy[2] - 2, "w": n03_box_x - chan, "h": 4,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "左侧旁路第 3 段（横）：旁路通道 x=%d → N03 方框左边界（x=%d）。三段合起来即边 E02 的屏上表达。★ M23：终点改为方框实左边界。" % (chan, n03_box_x),
    })

    # ---- 汇流总线
    els.append({
        "id": "flow.bus_c", "kind": "rect", "z": 13, "visible_default": True,
        "x": bus_x, "y": 140, "w": 4, "h": 746,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "**汇流总线（五线汇入 s04）**：纵线画在列间空隙的中线 x=%d，y 从最高源（140）到最低源（%d）。四个远端源（N06 / N04 / N08 / N05）各用一条短横条接到本线；N07→N09 与 N09 同列相邻，由纵向连接条 flow.seq09 表达，故不进总线。★ M23：中线由 x=960 改为 %d（列间空隙 %d–%d 的中线）。" % (bus_x + 2, row_cy[6], bus_x + 2, gap_l, gap_r),
    })
    for eid, y, note in [
        ("flow.cv1_a", 190, "汇流短横条：N06 → 总线（x=%d → %d，位于该节点垂直中线下方 y=190；N06 同时是跨列续接线的落点，故错开到 190）。★ M23 重排。" % (bus_x, gap_r)),
        ("flow.cv2_a", row_cy[3] - 2, "汇流短横条：N04 → 总线（x=%d → %d，位于该节点垂直中线 y=%d）。★ M23 重排。" % (gap_l, bus_x + 4, row_cy[3])),
        ("flow.cv3_a", row_cy[5] - 2, "汇流短横条：N08 → 总线（x=%d → %d，位于该节点垂直中线 y=%d）。★ M23 重排。" % (gap_l, bus_x + 4, row_cy[5])),
        ("flow.cv4_a", row_cy[6] - 2, "汇流短横条：N05 → 总线（x=%d → %d，位于该节点垂直中线 y=%d）。★ M23 重排。" % (gap_l, bus_x + 4, row_cy[6])),
    ]:
        left = bus_x if y == 190 else gap_l
        w = (gap_r - bus_x) if y == 190 else (bus_x + 4 - gap_l)
        els.append({
            "id": eid, "kind": "rect", "z": 13, "visible_default": True,
            "x": left, "y": y, "w": w, "h": 4,
            "color": "@palette.edge_line", "opacity": 255, "note": note,
        })
    els.append({
        "id": "flow.cv_n09", "kind": "rect", "z": 13, "visible_default": True,
        "x": bus_x, "y": row_cy[3] - 2, "w": gap_r - bus_x, "h": 4,
        "color": "@palette.edge_line", "opacity": 255,
        "note": "汇流总线 → N09 左边界的引入段（y=%d，与 N04 的短横条同高，二者连起来即边 E10 的直线表达）。★ M23 重排。" % (row_cy[3]),
    })

    # ---- 13 个节点
    for i, (el, nid, typ, col, row, sample, src) in enumerate(NODES):
        f, w, h, type_cn, type_reason = TYPES[typ]
        bx, by = _node_geom(col, row, w, h)
        sx, sy = COL_X[col], ROW_Y[row]
        z0 = 20 + i * 5
        lx = sx + LABEL_MARGIN
        short = nid.lower()
        els.append({
            "id": el + "_fill", "kind": "rect", "z": z0, "visible_default": True,
            "x": bx - 3, "y": by - 3, "w": w + 6, "h": h + 6,
            "color": "@palette.node_locked", "opacity": 235,
            "note": "节点 %s 的**三态色环**（运行期由 ui_flow.tjs 改写：已读=@palette.node_visited / 可前往=@palette.node_available / 未解锁=@palette.node_locked）。位置 = 方框外扩 3 px 的一圈（x=%d, y=%d, w=%d, h=%d），画在方框图**之下**，故表现为彩色描边环 —— 既保住三态着色机制（uiFlowSyncFlowchart 仍只写 _fill.color），又不遮挡方框美术。★ M23：按新方框尺寸（%d×%d）重算（旧版按 552×104–112 外扩 3）。行间距 8 px > 2×3，故相邻行的色环不重叠。" % (
                nid, bx - 3, by - 3, w + 6, h + 6, w, h),
        })
        els.append({
            "id": el + "_box", "kind": "image", "z": z0 + 1, "visible_default": True,
            "asset": "ui/%s" % f,
            "x": bx, "y": by, "w": w, "h": h, "opacity": 255,
            "source": "生图入料\\生成结果\\流程图的章节方框.png → 工具\\prep_generated.py（M22：整图按 k=0.491228 缩放一次后按源条带 alpha 包围盒切分）",
            "note": "节点 %s 的**方框图**（%s）。asset=ui/%s，**w/h=%d×%d = PNG 实际尺寸（1:1，无缩放、不带 nine）**。★ M23：M22 已把四个方框重建为「整图统一倍率 k=0.491228」的产物，尺寸天然各异（562×108 / 584×112 / 577×112 / 572×110）；旧版用 `nine:{l:0,t:0,r:0,b:0}` 把 1152 宽等比缩到 552 的做法**已取消** —— 那会二次缩放、破坏 M22 的统一倍率成果（M22 未决 #4）。本节点图在 **584×112 槽位**内居中：x = %d + (584−%d)/2 = %d，y = %d + (112−%d)/2 = %d。%s" % (
                nid, type_cn, f, w, h, sx, w, bx, sy, h, by, type_reason),
        })
        els.append({
            "id": el + "_label", "kind": "text", "z": z0 + 2, "visible_default": True,
            "x": lx, "y": sy, "w": LABEL_W, "h": SLOT_H,
            "font": {"size": 22, "bold": True, "color": "@palette.node_locked",
                     "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            "align": "center", "valign": "middle", "wrap": True, "max_lines": 2,
            "line_spacing": 1.25, "sample": sample,
            "note": "节点 %s 标签（幕名/分歧点名 + 来源·规模）。%s★ M23 重算：文字区 x=%d…%d（w=%d）＝ **槽位内居中、两侧各留 %d px**；依据 = 对四个新方框 PNG 逐列实测「列方差 ≥40」的装饰带：左装饰占 box-local 0–13、右装饰占 box-local 514–584（重要章节的雪花最宽），取边距 %d 后文字区 slot-local %d–%d，完整避开装饰。字号 22：最长一行「亚衣线·s03c（R 版 55 场景版）」实测 311 px ≤ %d，不折行不溢出；2 行 × 22 × 1.25 = 55 px ≤ 槽高 112。颜色取深色键：方框图是浅色，@palette.text_menu（近白）在新方框上不可见，故用 @palette.node_locked。" % (
                nid, src, lx, lx + LABEL_W - 1, LABEL_W, LABEL_MARGIN, LABEL_MARGIN,
                LABEL_MARGIN, LABEL_MARGIN + LABEL_W - 1, LABEL_W),
        })
        els.append({
            "id": el + "_hit", "kind": "hit", "z": z0 + 3, "visible_default": True,
            "x": bx, "y": by, "w": w, "h": h,
            "action": "flow_node_%s" % nid, "label": "",
            "font": {"size": 27, "bold": False, "color": "@palette.text_menu",
                     "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            "align": "center",
            "note": "节点 %s 热区（action=flow_node_%s，由 ui_flow.tjs 处理）。label 置空以免与 flow.%s_label 重复绘制。矩形 = 方框图矩形（1:1，%d×%d）。★ M23：命中区改贴方框实矩形（旧为 552 宽）。" % (
                nid, nid, short, w, h),
        })

    # ---- 页眉 / 标题 / 副标题 / 页脚
    els.append(old_by_id["flow.hdr_band"])
    els.append(old_by_id["flow.title"])
    info = dict(old_by_id["flow.info"])
    info["sample"] = "节点 13（幕 11 + 关键分歧点 2）｜ 方框 4 型：一般剧情 / BAD END / 重要章节 / GOOD END ｜ 一屏总览：2 列 × 7 行，方框 1:1（562–584 × 108–112），统一倍率 k=0.491228"
    info["note"] = "副标题：节点/连线规模 + 四种方框语义 + 版式与倍率。节点数 = spine.json 11 幕 + 2 个关键分歧点；方框 4 型的语义由用户 2026-09-20 定义。★ M23：倍率说明由「等比 0.478 缩放（552×112）」改为「1:1（562–584×108–112），统一倍率 k=0.491228」（方框不再做二次缩放）。"
    els.append(info)
    els.append(old_by_id["flow.ftr_band"])
    for eid in ["flow.legend_fill", "flow.legend_frame", "flow.lg1_sw", "flow.lg1_tx",
                "flow.lg2_sw", "flow.lg2_tx", "flow.lg3_sw", "flow.lg3_tx",
                "flow.lg4_sw", "flow.lg4_tx", "flow.detail", "flow.hit_back"]:
        els.append(old_by_id[eid])

    old["elements"] = els
    old["note"] = (
        "**M18 改造（2026-09-20）＋ M23 应用（2026-09-20）**：流程图**单屏总览**：13 个节点按 **2 列 × 7 行**（列优先填充）全部落在一屏内，**无需滚动**。\n\n"
        "★ **M23 应用 M22 统一缩放成果**：四个方框改用 M22 重建的 **562×108 / 584×112 / 577×112 / 572×110**（**整图统一倍率 k=0.491228** 的产物，件内倍率一致、尺寸天然各异）。\n"
        "   · 节点图**全部 1:1 摆放（无 nine、无二次缩放）** —— 旧版用 `nine:{0,0,0,0}` 把 1152 宽等比缩到 552 的做法**已取消**（那会把 M22 的统一缩放成果再次破坏，见 M22 未决 #4）。\n"
        "   · 统一**槽位** SLOT = **584×112**（取四者最大值），节点图在槽内**居中**：x = 槽位x + (584−w)/2，y = 槽位y + (112−h)/2。\n"
        "   · 槽位排 **2 列 × 7 行**：列起点 x = 300 / 1068（沿用）；行起点 y = 110 + n×120（7 行，末行槽底 942 ≤ 视口下沿 950）。**13 节点全部一屏可见，无需滚动**。\n"
        "   · 三态色环按新方框尺寸重算（方框外扩 3 px）；连线按新槽位重排（列中线 592 / 1360，列间总线中线 976）。\n"
        "   · 标签区按新 584 宽方框重算：槽位内居中、两侧各留 96 px → w=392（依据见各 `_label` 的 note）。\n\n"
        "★ **坐标依据**：视口高 = 页脚带顶 950 − 页眉带底 110 = 840 px；7 行 → 行槽 112 + 行间距 8 = 120 px；槽高 112 ≥ 四者最高 112 ⇒ 1:1 直接落格。\n\n"
        "★ **连线（单屏下的简化）**：① 同列相邻节点用纵向连接条（flow.seq01…seq11）；② 跨列用三段折线 flow.wrap_a/b/c（N05 → N06，走列间空隙的纵向通道 x=1024）；③ 真实边 E02（N01→N03，同列跨一行）用左侧旁路 flow.e02_a/b/c 表达；④ 五线汇入 s04 用列间空隙中线 x=976 的汇流总线 flow.bus_c + 四条短横条表达（N07→N09 与 N09 同列相邻，由 seq09 表达，不进总线）。\n\n"
        "★ **已知信息损失（如实登记）**：**E04（N03→N05）与 E05（N03→N06）两条跨行边不再有屏上元素**（`els` 为空数组）——它们在 2×7 网格里要横跨 3–4 行，画出来会与总线/续接线大量交叠；M14 的 `bus_a` 同样无法表达。**拓扑本身完整保留在 复刻\\flow_data.js / krkr\\game\\ui_flow_data.tjs 的 edges[] / buses[] 里**（供编程组与数据对账），只有屏上元素做了简化。\n\n"
        "★ **节点 → 方框类型判定表**（依据 spine.json acts[].note + 资源组\\01_剧情流程图.md §五 结局矩阵）：一般剧情 = N01/N02/N03/N11；BAD END = N10；重要章节 = B01/B02；GOOD END = N04/N05/N06/N07/N08/N09。逐条判定理由写在每个 `_box` 元素的 note 中。\n\n"
        "★ **可读性**：标签字号 22、最长行实测 311 px ≤ 文字区 392 px；窗口按 setZoom(2,3) 呈现 1280×720 时约合屏幕 14.7 px。\n\n"
        "★ 配色：方框图为浅色 → 节点文字用色板深色键 @palette.node_locked（三态信息由方框外色环承担）。页眉/页脚带为黑底，其上文字用浅色键。**未新增 palette 键**。生成器：_工作/M23_gen.py（幂等可复跑）。"
    )
    save(p, old)


# ================================================================ ④ 对话框
DIALOG_IMG = "ui/x_gen_dialog2.png"
DIALOG_W, DIALOG_H = 1628, 319
DLG_X = (CANVAS_W - DIALOG_W) // 2            # 146
DLG_BOTTOM_MARGIN = 36
DLG_Y = CANVAS_H - DIALOG_H - DLG_BOTTOM_MARGIN      # 725

NAMEBOX = GEO_D["dialog2"]["namebox"]["inner"]   # [x, y, w, h] = 185,22,345,56
TEXTBOX = GEO_D["dialog2"]["text"]["inner"]      # [x, y, w, h] = 100,80,940,210


def build_dialog():
    p = os.path.join(SCREENS, "10_dialog.json")
    t = load(p)
    by_id = {e["id"]: e for e in t["elements"]}

    # 对话窗
    win = by_id["dlg.window"]
    win["asset"] = DIALOG_IMG
    win["x"], win["y"], win["w"], win["h"] = DLG_X, DLG_Y, DIALOG_W, DIALOG_H
    win["source"] = "M22 派生（工具/prep_generated.py build_dialog2）：生图入料\\生成结果\\暂定对话框.png（1672×941 RGBA）alpha>64 包围盒 (20,598,1648,917) 裁紧 → 1628×319，**k=1.0（不做任何缩放）**"
    win["note"] = "对话窗底（**用户新提供的「暂定对话框.png」**，含左上内接圆角名字框；名字框是图的一部分，故不叠 nm_frm_b.png）。**1:1 摆放**：w/h=1628×319 = PNG 实际尺寸（无 nine、不缩放）。水平居中 x=(1920−1628)/2=146；**贴底但下方留空间** y=1080−319−36=725（36 px 下边距，可调），窗体底沿 = 1044。高度 319 **落在用户要求的 290–320 内**（M22 未做缩放，k=1.0）。★ 旧件 ui/x_gen_dialog.png（1680×946，含大片透明边距）**保留在资产目录但不被本屏引用**。"

    # 名字框文字
    nm = by_id["dlg.name"]
    nx, ny = DLG_X + NAMEBOX[0], DLG_Y + NAMEBOX[1]
    nm["x"], nm["y"], nm["w"], nm["h"] = nx, ny, NAMEBOX[2], NAMEBOX[3]
    nm["font"]["size"] = 36
    nm["note"] = "角色名（取自 scene_*.jsonl 的 lines[].speaker 中文）。几何 = M22_生成几何.json 的 dialog2.namebox.inner（裁切图内 [x=%d, y=%d, w=%d, h=%d]）换算到画布：x=%d+%d=%d，y=%d+%d=%d，w=%d，h=%d。字号 36（名字框内高 56，行高 36×1.2=43 < 56，不溢出）。空说话人时隐藏（名字框图形本身是窗体贴图的一部分，无法单独隐藏）。" % (
        NAMEBOX[0], NAMEBOX[1], NAMEBOX[2], NAMEBOX[3],
        DLG_X, NAMEBOX[0], nx, DLG_Y, NAMEBOX[1], ny, NAMEBOX[2], NAMEBOX[3])

    # 正文
    tx, ty = DLG_X + TEXTBOX[0], DLG_Y + TEXTBOX[1]
    te = by_id["dlg.text"]
    te["x"], te["y"], te["w"], te["h"] = tx, ty, TEXTBOX[2], TEXTBOX[3]
    te["note"] = ("对话正文区。几何 = M22_生成几何.json 的 dialog2.text.inner（裁切图内 [x=%d, y=%d, w=%d, h=%d]）换算到画布：x=%d+%d=%d，y=%d+%d=%d，w=%d，h=%d。"
                  "**该区是实测的「可写区」**：左界 %d 避开窗体左侧羽毛装饰（右沿 ≈85），右界 %d 避开右侧雪花装饰（列剖面实测 x≈1050 起有臂尖）—— 故 w=%d 是**在 1920 画布上不压雪花装饰的最大宽度**。"
                  "字号 40：%d px/行 ⇒ 约 23 字/行；3 行所需高 = floor(40×1.4)×3 = 168 ≤ %d。★ M23：任务书建议的「w 扩到 1200+」经实测**不可行** —— 那会把右界推到裁切图 x≈1300，压进雪花臂尖（证据见 M23_证据/dialog2_rightprobe.txt 与 M22 overlay_dialog2.png）。") % (
        TEXTBOX[0], TEXTBOX[1], TEXTBOX[2], TEXTBOX[3],
        DLG_X, TEXTBOX[0], tx, DLG_Y, TEXTBOX[1], ty, TEXTBOX[2], TEXTBOX[3],
        TEXTBOX[0], TEXTBOX[0] + TEXTBOX[2], TEXTBOX[2], TEXTBOX[2], TEXTBOX[3])

    # 光标
    cu = by_id["dlg.cursor"]
    cu["x"] = tx + TEXTBOX[2] - 207
    cu["y"] = ty + TEXTBOX[3] - 17 - 6
    cu["note"] = "文本推进光标（原版贴图 1:1，闪烁）。随新窗体重定：贴在正文区右下（正文右沿 %d+%d=%d，故 x=%d−207=%d；正文底沿 %d，故 y=%d−17−6=%d），落在可见窗体内（窗体 725–1044）。" % (
        tx, TEXTBOX[2], tx + TEXTBOX[2], tx + TEXTBOX[2], cu["x"], ty + TEXTBOX[3], ty + TEXTBOX[3], cu["y"])

    # 系统条
    sb = by_id["dlg.sysbar"]
    sb["y"] = 680
    sb["note"] = sb["note"].split("**系统条本身仍用文字**")[0] + "**系统条本身仍用文字**（图标走 33_sysicons.json 的右键浮层）。总宽 9×190 + 8×6 = 1758，居中 x=(1920-1758)/2=81；★ M23：新窗体顶沿 = 725，系统条改为**贴在窗体上方** y=680..724（与名字框外沿顶 737 留 13 px 间隙，与窗体顶 725 留 1 px 间隙）。字号 24：最长标签「返回上一选项」6 字 = 144px，九宫格内宽 190-40=150px，不溢出。原版 sm_* 612×26 菜单条内**烘焙日文**，故不用其贴图。"

    # 选择肢
    ch = by_id["dlg.choices"]
    ch["stack_bottom"] = 667
    ch["note"] = ch["note"].split("由 1280 基线")[0] + "由 1280 基线 ×1.5 迁移并重定 stack_bottom：★ M23 改为由下往上堆到 y=667（即系统条顶 680 之上），6 项满高 = 6×62+5×12 = 432 → 顶沿 235，容于画布；超过 6 项按 max_rows 翻页。原版 op_* 40 件为**选项文本图**（日文烘焙），不可复用。示例选项文本取自 资源组\\剧本\\主线编排方案.md:257-286 的 ot_s01_02c。"

    t["note"] = ("M13 重做（2026-09-20）／**M23 换新对话框（2026-09-20）**。"
                 "**对话窗 = 用户新提供的 暂定对话框.png**（alpha>64 裁切 1628×319，**k=1.0**）；高度 319 在用户要求的 **290–320** 内；水平居中 x=146，贴底 y=725、**下边距 36 px**（窗体底沿 1044）。"
                 "名字框文字与正文区均按 M22_生成几何.json 的 dialog2.namebox.inner / dialog2.text.inner 实测矩形换算（名字框 [185,22,345,56]→画布 331,747,345,56；正文 [100,80,940,210]→画布 246,805,940,210）。"
                 "★ 旧件 ui/x_gen_dialog.png（1680×946）**保留在资产目录但不被本屏引用**；旧版曾用 nm_frm_b.png 作名字框，早已删除（本屏确认无名字框图片元素）。"
                 "系统条 9 键上移到 y=680（新窗体上方），光标贴正文区右下，选择肢 stack_bottom=667。")
    save(p, t)


# ================================================================ ⑤ 屏清单
def build_index():
    p = os.path.join(SCREENS, "_index.json")
    d = load(p)
    req = {
        "title": ["满幅背景图（x_bg_system，不留黑边）", "标题 logo",
                  "主菜单 7 项（图上烘焙中英文，439×122 的 image + hit 各 7，按内容右边缘居右对齐）", "署名行"],
        "dialog": ["留黑底（letterbox）", "剧情背景层（dlg.content，dynamic:story_background）",
                   "对话窗底（x_gen_dialog2，含名字框，1628×319 整图 1:1 贴底居中、下留 36 px）",
                   "角色名文本", "正文文本区（打字机）", "文本光标（闪烁）",
                   "系统条 9 键（快速存档/快速读档/快进/返回上一选项/存档/读档/设置/隐藏对话框/重复语音）",
                   "选择肢列表", "自动·快进状态标签", "右键功能提示行"],
        "flowchart": ["13 个节点方框图（562–584×108–112，1:1 无缩放、无 nine，居中于 584×112 槽位）",
                      "节点标签（幕名/分歧点名 + 来源·规模）", "节点热区（action=flow_node_<id>）",
                      "三态色环（已读/可前往/未解锁）", "当前节点标记 + 键盘选中框",
                      "连线（同列纵向连接条 / 跨列续接线 / E02 左侧旁路 / 汇流总线与短横条）",
                      "4 行方框类型图例", "节点详情行", "返回"],
        "sysicons": ["全屏压暗遮罩", "点击空白收起热区",
                     "9 个功能图标（qsave/qload/skip/prev/save/load/config/close/repeat；统一 351×234，3×3 网格 1:1）",
                     "每项点击热区"],
    }
    for s in d["screens"]:
        if s["id"] in req:
            s["required"] = req[s["id"]]
    save(p, d)


if __name__ == "__main__":
    xs = build_title()
    cells = build_sysicons()
    build_flowchart()
    build_dialog()
    build_index()
    print("[OK] M23 layout 应用完成")
    print("  标题按钮（语义, x, y, 常态内容右缘, 高亮内容右缘）：")
    for sem, x, y, cr, hr in xs:
        print("    %-10s x=%-5d y=%-4d content_right=%-4d hover_right=%-4d" % (sem, x, y, cr, hr))
    print("  图标网格左上角：", cells)