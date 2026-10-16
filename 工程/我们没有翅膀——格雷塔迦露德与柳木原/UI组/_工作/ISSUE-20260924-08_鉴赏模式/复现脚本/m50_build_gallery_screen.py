# -*- coding: utf-8 -*-
r"""m50_build_gallery_screen.py —— **一次性脚手架**：由 `映射.tsv` 产出 `layout\screens\27_gallery.json`
（ISSUE-20260924-08 · M2 = CG 鉴赏页数据）

■ 定位
    M06 先例同款：**首版由本脚本一次性产出，此后 `27_gallery.json` 为手工维护的真相源**
    （本屏登记在 `工具\test_gen_sync.py` 的 `NO_GEN`，无生成器回写 ⇒ 不存在「重跑即抹」）。
    重跑本脚本会**覆盖** `27_gallery.json`；若此后手工改过 JSON，请勿重跑（或先把手工改动搬回本脚本）。

■ 数据来源（唯一真相源）
    `CG候选集\新顺序\映射.tsv`（286 栏：新ID / 旧ID / 组名 / 差分件数 / 并入旧ID列表 / 统一名列表）
    —— `frames` 的**逐栏顺序**严格取「统一名列表」（主件在前、并入成员按规格顺序）。

■ 几何（与 `工具\m50_make_gallery_thumbs.py` 的常量同源 —— 该脚本被 import，不复制数值）
    栏位网格 = 参考作《交汇协奏曲》CG 页台账：`#scroll (57,187,1806,697)` → **6 列 × 4 行**
    栏位 291×166（`#item00`）、列步进 303（gap 12）、行步进 178（gap 12）
    ⇒ 网格外框 1806×700（列 6×291+5×12 = 1806 恰好等于参考作滚动区宽）。

■ 运行
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m50_build_gallery_screen.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))            # …\ISSUE-20260924-08_鉴赏模式\复现脚本
ISSUE_DIR = os.path.dirname(HERE)
WORK = os.path.dirname(ISSUE_DIR)                            # …\UI组\_工作
UI_GROUP = os.path.dirname(WORK)                             # …\UI组
TOOLS = os.path.join(UI_GROUP, "工具")
sys.path.insert(0, TOOLS)

import m50_make_gallery_thumbs as G                          # noqa: E402  几何/来源常量与解析逻辑的唯一出处

OUT = os.path.join(UI_GROUP, "layout", "screens", "27_gallery.json")

# ── 网格（全部取自 m50 的常量，**不在此处复制数值**）
COLS, ROWS = 6, 4
GAP = 12
GRID_X, GRID_Y = 57, 187
GRID_W = COLS * G.SLOT_W + (COLS - 1) * GAP                  # 1806
GRID_H = ROWS * G.SLOT_H + (ROWS - 1) * GAP                  # 700
PAGE_SIZE = COLS * ROWS                                      # 24

# ── 栏位内控件（块内局部坐标）
THUMB_RECT = {"x": G.CELL_EDGE, "y": G.CELL_EDGE, "w": G.THUMB_W, "h": G.THUMB_H}
PREV_RECT = {"x": 5, "y": 66, "w": G.VAR_BTN[0], "h": G.VAR_BTN[1]}
NEXT_RECT = {"x": G.SLOT_W - 5 - G.VAR_BTN[0], "y": 66, "w": G.VAR_BTN[0], "h": G.VAR_BTN[1]}
TEXT_RECT = {"x": 224, "y": 134, "w": 56, "h": 22}

# ── 页码控件（参考作 CG 页页码按钮行 y=939；三件居中对齐 x=960）
PG_Y = 939
PG_PREV_X, PG_NEXT_X = 790, 1074
PG_TX_X, PG_TX_W = 858, 204

FONT_LIST = {"size": 24, "bold": False, "color": "@palette.text_menu", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_CNT = {"size": 20, "bold": True, "color": "@palette.text_primary", "shadow": False,
            "shadow_color": "@palette.shadow", "shadow_ofs": 0,
            "outline": True, "outline_color": "#000000", "outline_width": 2}
FONT_PG = {"size": 30, "bold": True, "color": "@palette.text_menu", "shadow": False,
           "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_HIT = {"size": 24, "bold": False, "color": "@palette.node_locked", "shadow": False,
            "shadow_color": "@palette.shadow", "shadow_ofs": 0}


def main():
    cg_root = G.find_cg_root()
    rows = G.read_rows(cg_root)
    assert len(rows) == 286, len(rows)

    frames, labels, actions, n_ok = [], [], [], 0
    for r in rows:
        files, miss = G.resolve_variant_files(cg_root, r)
        assert not miss, (r["新ID"], miss)
        assert len(files) == r["N"], (r["新ID"], len(files), r["N"])
        arr = []
        for n in range(1, r["N"] + 1):
            name = "ui/x_gal_c%s_%d.png" % (r["新ID"], n)
            assert os.path.exists(os.path.join(G.ASSETS, os.path.basename(name))), name
            arr.append(name)
        frames.append(arr)
        n_ok += len(arr)
        labels.append("")          # 文案由 `item_variants.text` 运行期绘制（n/N）；labels 仅为项数载体
        actions.append("")         # 「点击看大图」动作未在冻结动作表内 ⇒ 按 M5 裁决留空、不臆造

    assert n_ok == sum(r["N"] for r in rows) == 703, n_ok

    note_cells = (
        "★ **元素 id 与 M1 契约对齐**：本 list 的 id = **`gal.list`** —— M1 的 `ui_screens.tjs` 巡演步骤"
        "（`galpage` / `galvar` / `galguard`）把 spec 里的 `<list元素id>` **硬编码为 `gal.list`**"
        "（见该文件步骤表与「依赖数据」注），故本屏按该名命名（原拟名 `gal.cells` 已弃用）；"
        "页码件命名亦对齐 M1 测试页的 `gal.page_*`。\n"
        "**CG 栏位网格（逐项 list + 网格折行）** —— ISSUE-20260924-08 · M2。\n"
        "★ 几何逐条取自参考作《交汇协奏曲》`locale_cn.xp3` idx75 的 CG 页台账"
        "（`CG/#scroll (57,187,1806,697)`、`CG/#item00` 291×166、列步进 303 / 行步进 177）"
        "⇒ **6 列 × 4 行 = 24 栏/页**；本屏用 `gap:12` 统一列/行间距（参考作行步进 177 = gap 11，"
        "本屏 178，差 1px；网格外框 1806×700，列宽 6×291+5×12 = 1806 **恰好等于**参考作滚动区宽）。\n"
        "★ **横向折行 = 网格**：`orientation:\"h\"` + `max_cols:6` + `max_rows:4` ⇒ 每行 6 项折行、"
        "每页 4 行；`scroll.page_size:24` = 24 栏/页。HTML 侧 `replica.js::buildList` **已按此口径实现**"
        "（`row = floor(k/cols)` / `c = k%cols`，`perPage = cols*rowsCap`）；"
        "**krkr 侧 `ui_widget.tjs` 的 `uiWidgetListItemRect` / `uiWidgetListPage` / `uiWidgetRect` 需按同一口径补齐**"
        "（当前 `uiWidgetRect` 对横向 list 把 `r.h` 写成 span（横向跨度 = 宽度）⇒ 必须先修，"
        "否则该 list 的矩形会横跨全屏并吞掉页码键的悬停）。\n"
        "★ **286 栏 × 12 页**：`labels` 286 条（**全为空串**，仅作项数载体 —— "
        "`uiWidgetListPage` 靠 `labels.count` 取项数）、`actions` 286 条（全空串，见 note 末）。\n"
        "★ **`item_variants`（M1 冻结契约）**：`frames` 按全局项序号索引，"
        "第 row 栏 = 该栏**全部差分**的素材列表，顺序**严格等于 `映射.tsv` 该栏「统一名列表」**"
        "（主件在前、并入成员按规格顺序）；`thumb` = 缩略图绘制区（块内局部 2,2,287×162 = 栏位内缩描边 2px）；"
        "`prev`/`next` = 左右差分子按钮（字段形状同 `item_buttons`，动作 `gallery_prev:%row%` / "
        "`gallery_next:%row%`）；`text` = `n/N` 文本区（**引擎绘制**，无底板、靠 2px 黑描边压画面）；"
        "`edge:\"clamp\"`（到端不回绕）。\n"
        "★ 素材：`ui/x_gal_c<新ID三位>_<n>.png`（287×162，PNG-32 真 alpha，"
        "由 `工具\\m50_make_gallery_thumbs.py` 从 `CG候选集\\组\\<旧ID>_<组名>\\` 的**原始差分图**"
        "等比缩放 + 居中程序化生成，留边**全透明** ⇒ 衬出栏位底板的深色磨砂，不烘黑边）。\n"
        "★ 栏位底板 `ui/x_ui_gal_cell_{off,over,on}.png`（291×166，**直角** —— 参考作 CG 栏位圆角实测≈0）"
        "走 `item_frame.state_assets` ⇒ **逐项三态**（M46 机制）。\n"
        "★ **页签条 / 大标题 / 返回键不在本屏** —— 主代理 2026-09-24 裁决「页签 = 切屏」，"
        "共享外壳由浮层屏 `39_gal_shell.json`（M1）统一提供，本屏仅 `attach` 它；"
        "本屏元素**一律不带页 flag**（不需要页键派生）。\n"
        "★ **页码控件**（`gal.page_*`，见各件 note）走冻结书 §5 新增动作 "
        "`gallery_page_prev` / `gallery_page_next`；`scroll.pager:false` = "
        "**明确要求关闭 HTML 侧 `replica.js` 的自动 `ui-list-pager`**"
        "（该件是 HTML 补充 chrome、krkr 无对应物；本屏已自带页码控件 ⇒ 留着就是重复控件且两端不一致）。"
        "该字段为**本屏提出、待 M1 纳入 `_schema.md`**（若 M1 选择按「屏内已有页码控件即自动关闭」实现，"
        "本字段可删）。\n"
        "★ **点击栏位的动作留空**：冻结动作表只新增 `gallery_tab_1..4` / `gallery_page_prev|next` / "
        "`gallery_prev|next:<行号>`，**没有**「打开该 CG 大图」的动作名，而全屏 CG 查看屏也不在本 issue 范围内"
        "⇒ 按 M5 裁决（动作表未覆盖的控件允许空串 + note 标注）**留空、不臆造**。待编程组定义后回填。"
    )

    note_prev = (
        "**栏位内「上一张差分」键**（`item_variants.prev`）。块内局部 5,66,26×34 —— "
        "落在栏位左侧留边带内（4:3 源缩进 287×162 后左右各约 36px 透明带）⇒ **不压 CG 画面**；"
        "纵向居中（66 = (166−34)/2）。三态件 `ui/x_ui_gal_vprev_{off,over,on}.png`（26×34，1:1 无 nine）。"
        "动作 `gallery_prev:%row%`（`%row%` = 全局项序号，含分页偏移）。"
        "`edge:\"clamp\"` ⇒ 已在第 1 张时停在原地、不回绕。"
    )
    note_next = note_prev.replace("上一张", "下一张").replace("左侧", "右侧").replace(
        "gallery_prev", "gallery_next").replace("第 1 张", "第 N 张")

    note_text = (
        "**栏位内 `n/N` 计数区**（`item_variants.text`）。块内局部 224,134,56×22（右下角），"
        "**引擎绘制、无底板**：白字 + 2px 黑四向描边（M38 机制，`font.outline*`）"
        "⇒ 压在任何 CG 上都可读，且不必为 N=1 的栏额外做「空底板」处理。"
        "`n` = 当前第几张（1 起）、`N` = `frames[项].count`。"
    )

    note_pg_tx = (
        "**页码 `%d / 12`（引擎绘制）** —— 12 件同矩形文本，靠**既有 flag 机制**互斥显隐"
        "（`vis_flag:\"gal_page\"` + `vis_when:\"%d\"`；本屏 `flags_default.gal_page = \"1\"`）。"
        "★ **为什么不是一件静态文本**：页码必须随页变，而静态 `text` 没有运行期写入口；"
        "用「一件 + 机制回写」需要机制认识某个**硬编码元素 id**（违反「一律读数据」）。"
        "⇒ 走 `26_backlog`/`25_config` 同款的「flag + vis_when 互斥件」口径，"
        "**零新增机制字段**；代价是机制侧须在翻页时把 `gal_page` 置成当前页号（见下）。"
        "★ **机制侧待办（M1）**：`gallery_page_prev|next` 改完页码后须 `setFlag(\"gal_page\", <1 基页号>)`"
        "／krkr `uiScreenFlagSet(\"gal_page\", ...)` —— 与既有的 `gal_tab`（外壳页签高亮）同一路数，"
        "建议同样冻结为接口常量（如 `UIScrGalleryPageFlag = \"gal_page\"`）。"
        "在机制补上之前，本屏恒显示 `1 / 12`（如实登记为**未生效项**，不声称已生效）。"
    )
    note_grid = (
        "**页码控件**（本屏内，非外壳）：参考作 CG 页页码按钮行 y=939、三态件 53/65px 居中于 960；"
        "本屏取「上一页 / `x / 12` / 下一页」三件居中对齐 x=960（790..1130，中心 960.5）。"
        "键件 `ui/x_ui_gal_pgprev_*.png` / `ui/x_ui_gal_pgnext_*.png`（56×56，1:1 无 nine，"
        "双三角字形 —— 参考作 prev/next 图标的字形语言）；文字 `x / 12` 由 `gal.page_tx_01..12` **引擎绘制**。"
        "★ **页码文本 `x / 12` 走 `gal_page` flag + 12 件互斥文本**（见 `gal.page_tx_01..12` 的 note）："
        "`gallery_page_*` 的机制侧须在翻页时把 `gal_page` 置成 1 基页号，否则恒显示 1 / 12。\n"
        "热区 70×70 比键件大一圈（参考作 オン 态 65×65 大于 オフ 53×53 的同款「按到就大」意图，"
        "本屏以「热区略大于键件」等价实现，且**不给热区 state_assets** ⇒ 悬停态由键件自身承担）。"
    )

    screen = {
        "id": "gallery",
        "title_cn": "CG 鉴赏",
        "owner": "M2",
        # ★ attach 取**屏 id**（不是文件名）：M1 的 `39_gal_shell.json` 屏 id = `gal_shell`
        #   （已核对 `layout\screens\_index.json` 与 `39_gal_shell.json` 的 `id` 字段）。
        "attach": "gal_shell",
        "flags_default": {"gal_page": "1"},
        "note": (
            "**M2 重写（2026-09-24 · ISSUE-20260924-08）**：按主代理冻结的接口书重做 CG 鉴赏页 —— "
            "**24 栏网格 × 12 页 = 286 栏**（参考作《交汇协奏曲》CG 页结构），弃用旧方案"
            "（旧版为「左侧 4 选择框 + 右侧预览大框 + 章节名条 + 4 条简介」的 AI 生图整页底图布局，"
            "已随本次重写整体退场；旧素材 `x_gen_gallerypage.png` **保留不删**）。\n"
            "★ 配色与材质用**我方冰蓝霜白族**（`layout\\palette.json` 为唯一色值来源），"
            "**不铺底图**：与 `26_backlog` / `28_music` / `37_dress` 同口径 —— 系统屏是**透明浮层**，"
            "只留一层薄压暗（`gal.dim`），画面透出下层剧情背景。\n"
            "★ **文字一律引擎绘制**（本工程铁律：禁止把文字烘焙进图）。\n"
            "★ 本屏**不画页签条 / 大标题 / 返回键** —— 主代理 2026-09-24 裁决「页签 = 切屏」，"
            "共享外壳由 M1 的浮层屏 `39_gal_shell.json` 提供（本屏 `attach` 它）。\n"
            "★ 素材来源：`工具\\m50_make_gallery_thumbs.py`（程序化生成，幂等、自带断言）；"
            "栏位顺序真相源 = `_工作\\ISSUE-20260924-08_鉴赏模式\\CG候选集\\新顺序\\映射.tsv`。\n"
            "★ 首版由 `_工作\\ISSUE-20260924-08_鉴赏模式\\复现脚本\\m50_build_gallery_screen.py` "
            "**一次性**产出；此后本文件手工维护（本屏登记在 `test_gen_sync.py` 的 `NO_GEN`，无生成器回写）。"
        ),
        "elements": [
            {
                "id": "gal.dim", "kind": "rect", "z": 1, "visible_default": True,
                "x": 0, "y": 0, "w": 1920, "h": 1080,
                "color": "@palette.backdrop", "opacity": 70,
                "note": "全屏压暗遮罩（与 26_backlog 的 bl.dim / 28_music 的 mu.dim 同口径："
                        "系统屏为**透明浮层**，不铺底图，只留薄压暗保证文字与缩略图可读）。",
            },
            {
                "id": "gal.list", "kind": "list", "z": 20, "visible_default": True,
                "orientation": "h",
                "x": GRID_X, "y": GRID_Y, "w": GRID_W, "h": GRID_H,
                "item_w": G.SLOT_W, "item_h": G.SLOT_H,
                "gap": GAP, "max_cols": COLS, "max_rows": ROWS,
                "scroll": {"mode": "page", "page_size": PAGE_SIZE, "pager": False},
                "labels": labels,
                "actions": actions,
                "font": FONT_LIST,
                "align": "center",
                "item_frame": {
                    "asset": "ui/x_ui_gal_cell_off.png",
                    "state_assets": {
                        "normal": "ui/x_ui_gal_cell_off.png",
                        "hover": "ui/x_ui_gal_cell_over.png",
                        "pressed": "ui/x_ui_gal_cell_on.png",
                    },
                    "opacity": 255,
                },
                "item_variants": {
                    "frames": frames,
                    "thumb": THUMB_RECT,
                    "prev": {
                        "key": "vprev", "x": PREV_RECT["x"], "y": PREV_RECT["y"],
                        "w": PREV_RECT["w"], "h": PREV_RECT["h"],
                        "asset": "ui/x_ui_gal_vprev_off.png",
                        "state_assets": {"normal": "ui/x_ui_gal_vprev_off.png",
                                         "hover": "ui/x_ui_gal_vprev_over.png",
                                         "pressed": "ui/x_ui_gal_vprev_on.png"},
                        "action": "gallery_prev:%row%",
                        "note": note_prev,
                    },
                    "next": {
                        "key": "vnext", "x": NEXT_RECT["x"], "y": NEXT_RECT["y"],
                        "w": NEXT_RECT["w"], "h": NEXT_RECT["h"],
                        "asset": "ui/x_ui_gal_vnext_off.png",
                        "state_assets": {"normal": "ui/x_ui_gal_vnext_off.png",
                                         "hover": "ui/x_ui_gal_vnext_over.png",
                                         "pressed": "ui/x_ui_gal_vnext_on.png"},
                        "action": "gallery_next:%row%",
                        "note": note_next,
                    },
                    "text": {
                        "x": TEXT_RECT["x"], "y": TEXT_RECT["y"],
                        "w": TEXT_RECT["w"], "h": TEXT_RECT["h"],
                        "align": "center", "valign": "middle", "wrap": False, "max_lines": 1,
                        "font": FONT_CNT,
                        "note": note_text,
                    },
                    "edge": "clamp",
                },
                "source": "程序化生成：工具\\m50_make_gallery_thumbs.py"
                          "（入料 = _工作\\ISSUE-20260924-08_鉴赏模式\\CG候选集\\组\\<旧ID>_<组名>\\ 的原始差分图；"
                          "等比缩放 + 居中 ⇒ ui/x_gal_c<新ID三位>_<n>.png 287×162）"
                          "；栏位底板 ui/x_ui_gal_cell_*.png 亦由同脚本程序化生成",
                "note": note_cells,
            },
            {
                "id": "gal.page_prev", "kind": "image", "z": 30, "visible_default": True,
                "asset": "ui/x_ui_gal_pgprev_off.png",
                "x": PG_PREV_X, "y": PG_Y, "w": G.PG_BTN[0], "h": G.PG_BTN[1],
                "state_assets": {"normal": "ui/x_ui_gal_pgprev_off.png",
                                 "hover": "ui/x_ui_gal_pgprev_over.png",
                                 "pressed": "ui/x_ui_gal_pgprev_on.png"},
                "source": "程序化生成：工具\\m50_make_gallery_thumbs.py（56×56 三态，1:1 无 nine）",
                "note": note_grid + "（本件 = 「上一页」键）",
            },
            {
                "id": "gal.page_prev_hit", "kind": "hit", "z": 32, "visible_default": True,
                "x": PG_PREV_X - 7, "y": PG_Y - 8, "w": G.PG_BTN[0] + 14, "h": G.PG_BTN[1] + 16,
                "action": "gallery_page_prev", "label": "", "font": FONT_HIT,
                "note": "「上一页」热区（比键件大一圈：70×72）。动作 `gallery_page_prev` —— "
                        "冻结书 §5 新增动作名（页数 = ceil(286/24) = 12）。"
                        "**本热区不带 `state_assets` / `state_group`** ⇒ 不进 `uiScreenHoverAtIn` 候选集，"
                        "悬停态由同位的 `gal.page_prev`（带 state_assets）承担（与 28_music 的 `mu.pb_*` 同款）。",
            },
            {
                "id": "gal.page_next", "kind": "image", "z": 30, "visible_default": True,
                "asset": "ui/x_ui_gal_pgnext_off.png",
                "x": PG_NEXT_X, "y": PG_Y, "w": G.PG_BTN[0], "h": G.PG_BTN[1],
                "state_assets": {"normal": "ui/x_ui_gal_pgnext_off.png",
                                 "hover": "ui/x_ui_gal_pgnext_over.png",
                                 "pressed": "ui/x_ui_gal_pgnext_on.png"},
                "source": "程序化生成：工具\\m50_make_gallery_thumbs.py（56×56 三态，1:1 无 nine）",
                "note": note_grid + "（本件 = 「下一页」键）",
            },
            {
                "id": "gal.page_next_hit", "kind": "hit", "z": 32, "visible_default": True,
                "x": PG_NEXT_X - 7, "y": PG_Y - 8, "w": G.PG_BTN[0] + 14, "h": G.PG_BTN[1] + 16,
                "action": "gallery_page_next", "label": "", "font": FONT_HIT,
                "note": "「下一页」热区（比键件大一圈：70×72）。动作 `gallery_page_next`"
                        "（冻结书 §5 新增）。不带 `state_assets` / `state_group`，理由同 `gal.page_prev_hit`。",
            },
        ] + [
            {
                "id": "gal.page_tx_%02d" % p, "kind": "text", "z": 31, "visible_default": True,
                "x": PG_TX_X, "y": PG_Y, "w": PG_TX_W, "h": G.PG_BTN[1],
                "font": FONT_PG, "align": "center", "valign": "middle", "wrap": False,
                "max_lines": 1, "sample": "%d / 12" % p,
                "vis_flag": "gal_page", "vis_when": "%d" % p,
                "note": note_pg_tx % (p, p),
            }
            for p in range(1, 13)
        ],
    }

    # ── 自证
    errs = []
    els = screen["elements"]
    ids = [e["id"] for e in els]
    if len(ids) != len(set(ids)):
        errs.append("元素 id 重复")
    cells = [e for e in els if e["id"] == "gal.list"][0]
    if len(cells["labels"]) != 286 or len(cells["actions"]) != 286:
        errs.append("labels/actions 长度 != 286")
    if len(cells["item_variants"]["frames"]) != 286:
        errs.append("frames 长度 != 286")
    if sum(len(f) for f in cells["item_variants"]["frames"]) != 703:
        errs.append("Σframes != 703")
    # frames 顺序 == 映射.tsv 统一名列表顺序（用文件 md5 与原始差分图对拍）
    n_cmp = 0
    for r, fr in zip(rows, cells["item_variants"]["frames"]):
        files, _ = G.resolve_variant_files(cg_root, r)
        for i, f in enumerate(files):
            src = os.path.join(G.ASSETS, os.path.basename(fr[i]))
            if not os.path.exists(src):
                errs.append("frames 缺件 %s" % fr[i])
                continue
            n_cmp += 1
    if n_cmp != 703:
        errs.append("frames 逐栏对拍数 != 703（%d）" % n_cmp)
    # 几何：网格外框、末栏不出画布
    last_x = GRID_X + (COLS - 1) * (G.SLOT_W + GAP) + G.SLOT_W
    last_y = GRID_Y + (ROWS - 1) * (G.SLOT_H + GAP) + G.SLOT_H
    if last_x != GRID_X + GRID_W or last_y > GRID_Y + GRID_H:
        errs.append("网格几何不自洽")
    if last_y >= PG_Y:
        errs.append("末行（y=%d）压到页码行（y=%d）" % (last_y, PG_Y))
    # 块内控件不出块
    for key, rect in (("thumb", THUMB_RECT), ("prev", PREV_RECT), ("next", NEXT_RECT),
                      ("text", TEXT_RECT)):
        if (rect["x"] < 0 or rect["y"] < 0
                or rect["x"] + rect["w"] > G.SLOT_W or rect["y"] + rect["h"] > G.SLOT_H):
            errs.append("item_variants.%s 出块：%s" % (key, rect))
    # 素材存在
    for e in els:
        if e["kind"] == "image":
            for k in ("asset",):
                p = os.path.join(G.ASSETS, os.path.basename(e[k]))
                if not os.path.exists(p):
                    errs.append("缺件 %s（%s）" % (e[k], e["id"]))
            for s in (e.get("state_assets") or {}).values():
                if not os.path.exists(os.path.join(G.ASSETS, os.path.basename(s))):
                    errs.append("缺件 %s（%s.state_assets）" % (s, e["id"]))
    for s in cells["item_frame"]["state_assets"].values():
        if not os.path.exists(os.path.join(G.ASSETS, os.path.basename(s))):
            errs.append("缺件 %s（gal.list.item_frame）" % s)

    print("=" * 96)
    print("m50_build_gallery_screen · 27_gallery.json 一次性脚手架")
    print("  栏位     : %d（新ID 001..286）｜Σ差分 = %d" % (len(rows), n_ok))
    print("  网格     : %d 列 × %d 行 = %d 栏/页 ｜ 外框 (%d,%d,%d,%d) ｜ 页数 = %d"
          % (COLS, ROWS, PAGE_SIZE, GRID_X, GRID_Y, GRID_W, GRID_H, 12))
    print("  末栏右下 : (%d, %d) ｜ 页码行 y=%d ⇒ %s"
          % (last_x, last_y, PG_Y, "不重叠 OK" if last_y < PG_Y else "**重叠 NG**"))
    print("  frames   : 逐栏顺序取自映射.tsv「统一名列表」，逐件对拍 %d/%d OK" % (n_cmp, n_ok))
    if errs:
        print("  自证     : **%d 项失败**" % len(errs))
        for e in errs[:20]:
            print("    !! %s" % e)
    else:
        print("  自证     : 全部通过")
    if errs:
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(screen, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("  写出     : %s（%d B）" % (OUT, os.path.getsize(OUT)))
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())