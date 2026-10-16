# -*- coding: utf-8 -*-
"""一次性脚手架：产出 layout/screens/38_replay.json（此后该 JSON 手工维护）。"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)                           # ...\UI组

# ---- 几何（唯一真相源；取参考件 layers_75.json 实测矩形）----
# 参考作 idx75 §2.3（情景回想 19 条）：
#   Replay/caption (64,100,490,79)                 -> 归外壳（页签=切屏裁决），本屏不出
#   Replay/small/preview (57,187,575,715)          -> rp.preview
#   Replay/small/#sample (645,187,1218,715)        -> rp.list 网格外框
#   Replay/small/item:normal (645,187,234,133)     -> 栏位（item_w/h）
#   Replay/small/item:thumb (646,189,232,129)      -> thumb 区（内缩 2px，同 M2 口径）
#   Replay/page/*（885/975,939 53×53；879/969,933 65×65）-> 取 M2/M3 三件式（790/858/1074），有意差异
GRID_X, GRID_Y = 645, 187
CELL_W, CELL_H = 234, 133
GAP = 12
COLS, ROWS = 5, 5
GRID_W = COLS * CELL_W + (COLS - 1) * GAP            # 1218 == #sample 宽，恰好
GRID_H = ROWS * CELL_H + (ROWS - 1) * GAP            # 713（#sample 715，2px 余量）

N_PAGE = 25
N_MOVIE = 10          # 实测 movie 清单 10 件（派单 11 件之差 = ota_bg.txt 是 data 非 movie）
N_TOTAL = N_PAGE * 2  # 50 栏 = 2 页

labels, actions = [], []
for i in range(N_PAGE):
    labels.append("情景 %03d" % (i + 1))
    actions.append("")
# 第二页：10 件动画（全局行 25..34，0 基）——动作 = replay_play:<全局行号>（派发即止，留编程组）
MOVIES = [
    "np_makerlogo",    # np/涅布 MakerLogo.mpg
    "np_navelplusop",  # np/NavelPlus OP
    "ot_op1",          # ot/本篇 OP1
    "ot_op2",          # ot/本篇 OP2
    "ota_op",          # ota/AfterStory OP
    "ota_pv1",         # ota/AfterStory PV1
    "ota_pv2",         # ota/AfterStory PV2
    "otp_op",          # otp/OP
    "otv_op03",        # otv/PSV OP03
    "otv_ed_misaki",   # otv/PSV ED
]
for k in range(N_MOVIE):
    labels.append("动画 %02d" % (k + 1))
    actions.append("replay_play:%d" % (N_PAGE + k))
for i in range(N_TOTAL - N_PAGE - N_MOVIE):
    labels.append("")
    actions.append("")

frames = [[] for _ in range(N_PAGE)] + [["ui/x_ui_rp_mv_thumb.png"] for _ in range(N_MOVIE)]
# 行 35..49（15 空栏）**不写进 frames** = 越界留空（合法路径之二；与显式空数组并存演示）

FONT_LIST = {"size": 24, "bold": False, "color": "@palette.text_menu",
             "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_HIT = {"size": 24, "bold": False, "color": "@palette.node_locked",
            "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_PG = {"size": 24, "bold": True, "color": "@palette.text_menu",
           "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_VAR = {"size": 16, "bold": True, "color": "@palette.text_primary",
            "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0,
            "outline": True, "outline_color": "#000000", "outline_width": 2}

NOTE_LIST = (
    "★ **情景回想两页 5×5（逐项 list + 网格折行）** —— ISSUE-20260924-08 · M4（新建屏，`_index.json` 已登记）。\n"
    "★ 几何逐条取自参考作《交汇协奏曲》`locale_cn.xp3` idx75 情景回想页台账（`layers_75.json` 实测）："
    "网格外框 = `Replay/small/#sample` (645,187,1218,715)；栏位 = `item:normal` 234×133；"
    "`max_cols:5`×`max_rows:5` + `gap:12` ⇒ 外框宽 5×234+4×12 = **1218 恰好等于** #sample 宽、"
    "高 713（参考 715，2px 余量）。参考作选中位 `#pos11` (891,333) = 第 2 列第 2 行 ⇒ 列步进 246 与本屏一致、"
    "行步进 146（本屏 145，差 1px —— 参考作列/行步进本身不一致 246/146，本屏统一 gap 12，**登记为有意差异**）。\n"
    "★ **横向折行 = 网格**（M1 机制，行优先）：`orientation:\"h\"` + `max_cols:5` + `scroll.page_size:25` ⇒ "
    "每页 25 栏、共 **2 页 50 栏**（`gallery_page_prev/next` 翻页，翻页键/页码在屏内，同 M2/M3 口径）。\n"
    "★ **第一页（全局行 0..24）＝ 25 情景栏，内容全部占位**（用户明确「先做结构，内容占位」）："
    "`labels` = 占位文本「情景 001」…「情景 025」，`actions` 全空串（情景回放的跳转动作待编程组定义，"
    "按 M5 裁决「动作表未覆盖的控件允许空串 + note 标注」），`item_variants.frames` 该 25 行为**空数组**"
    "（合法留空：不画缩略图/差分键/`n/N`，只画栏位底板 + 标签）——**内容待填**，情景清单与跳转口径待主代理/编程组。\n"
    "★ **第二页（全局行 25..49）＝ 动画页（与参考作原版有意不同**：参考作该页只有 `big` 版式的 opmovie/edmovie "
    "两个大图位 + `small` 列表版式，本屏按冻结书统一为 25 栏网格）。\n"
    "　· **10 件动画**（全局行 25..34）：`frames` = 各 1 张占位缩略图 `ui/x_ui_rp_mv_thumb.png`（胶片齿孔 + ▶ "
    "纯图形占位标记；真缩略图待定）、`labels` = 占位文本「动画 01」…「动画 10」、"
    "`actions` = `replay_play:<全局行号>`（replay_play:25 … replay_play:34）。\n"
    "　· ★ **件数差异如实登记（需主代理裁决）**：派单/冻结书说「11 件动画（np 2 / ot 2 / ota 4 / otp 1 / otv 2）」，"
    "实测清单与物理文件只有 **10 件 movie**——`ota` 的 `movie/` 目录第 4 件 `ota_bg.txt` 在 `_清单.json` 里 "
    "`kind=\"data\"`（文本数据，非动画），不应占播放栏 ⇒ 本屏放 10 件、其余 15 栏留空。\n"
    "　· ★ **`replay_play:<行号>` 为本屏提出的新动作名（派单授权「之类」）**：语义 = **派发即止**——本作无音频/视频"
    "播放机制（M47 已登记），引擎 `uiActionDispatch` 对未实现动作返回 `handled:false` + 日志「未实现的动作：…」，"
    "**不臆造已生效**；真正的播放接线留编程组。**待 M1 把该动作名补进 `layout\\_schema.md` 动作名表**。\n"
    "　· 其余 15 栏（全局行 35..49）：`labels`/`actions` 空串，且**不写进 `frames`**（索引越界 = 留空，合法路径之二"
    "——与第一页的显式空数组并存，两条合法路径都有数据佐证）。\n"
    "★ **`item_variants`（M1 冻结契约）**：`thumb` = 块内局部 (2,2,230,129)（栏位内缩 2px，同 M2 口径）；"
    "`prev`/`next` = 复用 M2 的 `x_ui_gal_vprev/vnext_*`（26×34 三态，块内局部 (4,50)/(204,50)，纵向居中）"
    "——**只落在 10 个动画栏**（非空 frames 才画；N=1 ⇒ 两键按 `edge:\"clamp\"` 钳制、`n/N` 恒 1/1，不回绕）；"
    "`text` = `n/N` 区 (167,101,56,22)，引擎绘制（白字 + 2px 黑描边压画面）。\n"
    "★ **播放标记/缩略图口径**：参考作该页的「播放中」标记属运行期（参考件 §6.3-5 缺口已登记，容器内无对应件）"
    "⇒ 我方**自绘静态 ▶ 占位**（烘在 `x_ui_rp_mv_thumb.png` 上的图形，非文字）＝「这是可播项」的静态标记；"
    "「播放中」态标记与真缩略图（视频截帧）留编程组。\n"
    "★ **栏位底板** `ui/x_ui_rp_cell_{off,over,on}.png`（234×133，**直角**，冰蓝霜白族）走 "
    "`item_frame.state_assets` ⇒ 逐项三态（M46 机制）；素材由 `工具\\m52_make_replay_assets.py` 程序化生成。\n"
    "★ **页签条 / 大标题 / 返回键不在本屏** —— 主代理 2026-09-24 裁决「页签 = 切屏」，本屏 `attach` M1 的"
    "浮层屏 `39_gal_shell.json`（第 4 页「情景回想」）。本屏元素一律不带页 flag。\n"
    "★ **页码文本**：单件静态 `rp.pg_tx`（M3 同款），实际页码由机制/编程组写入 —— **未接线，如实登记**"
    "（参考作 `Replay/page` 本只有 2 个页码键无文本槽；本屏取 M2/M3 的「上一页 / x / 2 / 下一页」三件式，"
    "位置 790/858..1062/1074 —— **有意差异**，为四页统一）。")

NOTE_DIM = ("全屏压暗遮罩（与 gal.dim / mu.dim 同口径：系统屏为**透明浮层**，不铺底图，只留薄压暗保证栏位与文字可读）。")
NOTE_PREVIEW = ("**选中情景预览板**（几何 = 参考作 `Replay/small/preview` (57,187,575,715) 实测矩形；"
                "参考作为青底预览板 `p75_c059`，我方改冰蓝磨砂占位底板 `x_ui_rp_preview.png`，**配色差异属有意**——"
                "我方冰蓝霜白族）。**运行期由编程组贴选中情景的画面/播放器**，本版为空占位底板（内容占位口径的一部分）。")
NOTE_PGP = ("**页码控件**（屏内，非外壳）：与 M2/M3 同口径三件式（790/858..1062/1074，居中对齐 x=960）。"
            "键件 `ui/x_ui_rp_pgprev_*.png`（56×56 三态，1:1 无 nine，双三角字形——复用 m50 的 build_pg_btn 绘制）。"
            "★ 参考作 `Replay/page` 页码键在 (885,939)/(975,939) 且**无页码文本**；本屏按 M2/M3 口径左移到 790/1074 "
            "并加文本槽 ⇒ **有意差异（四页统一）**。热区 70×72 比键件大一圈（参考作 オン 65×65 > オフ 53×53 的"
            "「按到就大」意图），**热区带 `state_group`**（与同组 image 联动换三态，M3 的改良口径）。")
NOTE_PGN = NOTE_PGP.replace("pgprev", "pgnext").replace("上一页", "下一页")
NOTE_PGT = ("页码指示「1 / 2」（引擎绘制，M3 同款单件静态文本）：共 2 页（50 栏 / 每页 25）。"
            "★ 实际页码由机制/编程组写入——`gallery_page_prev/next` 目前不回写任何页码 flag（M2 的 gal_page 亦同），"
            "**本版恒显示 1 / 2，如实登记为未生效项，不声称已生效**。")

els = [
    {"id": "rp.dim", "kind": "rect", "z": 1, "visible_default": True,
     "x": 0, "y": 0, "w": 1920, "h": 1080, "color": "@palette.backdrop", "opacity": 70, "note": NOTE_DIM},
    {"id": "rp.preview", "kind": "image", "z": 10, "visible_default": True,
     "asset": "ui/x_ui_rp_preview.png", "x": 57, "y": 187, "w": 575, "h": 715, "opacity": 255,
     "source": "程序化生成：工具\\m52_make_replay_assets.py（冰蓝磨砂占位底板，575×715，1:1 无 nine）",
     "note": NOTE_PREVIEW},
    {"id": "rp.list", "kind": "list", "z": 20, "visible_default": True,
     "orientation": "h", "x": GRID_X, "y": GRID_Y, "w": GRID_W, "h": GRID_H,
     "item_w": CELL_W, "item_h": CELL_H, "gap": GAP, "max_cols": COLS, "max_rows": ROWS,
     "scroll": {"mode": "page", "page_size": N_PAGE},
     "labels": labels, "actions": actions,
     "font": FONT_LIST, "align": "center",
     "item_frame": {"asset": "ui/x_ui_rp_cell_off.png", "opacity": 255,
                    "state_assets": {"normal": "ui/x_ui_rp_cell_off.png",
                                     "hover": "ui/x_ui_rp_cell_over.png",
                                     "pressed": "ui/x_ui_rp_cell_on.png"}},
     "item_variants": {
         "frames": frames,
         "thumb": {"x": 2, "y": 2, "w": 230, "h": 129},
         "prev": {"key": "vprev", "x": 4, "y": 50, "w": 26, "h": 34,
                  "asset": "ui/x_ui_gal_vprev_off.png",
                  "state_assets": {"normal": "ui/x_ui_gal_vprev_off.png",
                                   "hover": "ui/x_ui_gal_vprev_over.png",
                                   "pressed": "ui/x_ui_gal_vprev_on.png"},
                  "action": "gallery_prev:%row%",
                  "note": "栏位内「上一张差分」键（复用 M2 的 x_ui_gal_vprev 三态件，26×34，1:1 无 nine）；"
                          "块内局部 (4,50) 纵向居中。仅落在 frames 非空的栏（本屏 = 10 个动画栏）；"
                          "N=1 ⇒ 按 edge:\"clamp\" 钳制、n/N 恒 1/1，不回绕。"},
         "next": {"key": "vnext", "x": 204, "y": 50, "w": 26, "h": 34,
                  "asset": "ui/x_ui_gal_vnext_off.png",
                  "state_assets": {"normal": "ui/x_ui_gal_vnext_off.png",
                                   "hover": "ui/x_ui_gal_vnext_over.png",
                                   "pressed": "ui/x_ui_gal_vnext_on.png"},
                  "action": "gallery_next:%row%",
                  "note": "栏位内「下一张差分」键（复用 M2 的 x_ui_gal_vnext 三态件）；块内局部 (204,50)。其余同 vprev。"},
         "text": {"x": 167, "y": 101, "w": 56, "h": 22, "align": "center", "valign": "middle",
                  "wrap": False, "max_lines": 1, "font": FONT_VAR,
                  "note": "n/N 计数区（引擎绘制，白字 + 2px 黑四向描边压画面）；N=1 时恒显示 1/1。"},
         "edge": "clamp"},
     "source": "栏位底板/占位缩略图/预览板 = 工具\\m52_make_replay_assets.py；差分键复用 M2 的 x_ui_gal_vprev/vnext_*",
     "note": NOTE_LIST},
    {"id": "rp.pg_prev", "kind": "image", "z": 30, "visible_default": True,
     "asset": "ui/x_ui_rp_pgprev_off.png", "x": 790, "y": 939, "w": 56, "h": 56, "opacity": 255,
     "state_assets": {"normal": "ui/x_ui_rp_pgprev_off.png",
                      "hover": "ui/x_ui_rp_pgprev_over.png",
                      "pressed": "ui/x_ui_rp_pgprev_on.png"},
     "state_group": "rp.pgprev",
     "source": "程序化生成：工具\\m52_make_replay_assets.py（复用 m50 的 build_pg_btn 绘制，56×56 三态，1:1 无 nine）",
     "note": NOTE_PGP},
    {"id": "rp.pg_prev_hit", "kind": "hit", "z": 32, "visible_default": True,
     "x": 783, "y": 931, "w": 70, "h": 72, "action": "gallery_page_prev", "label": "",
     "font": FONT_HIT, "align": "center", "state_group": "rp.pgprev",
     "note": "「上一页」热区（70×72，比键件大一圈）。动作 `gallery_page_prev`（冻结书 §5 冻结名）。"
             "带 `state_group`：与同组 image 一起换三态 ⇒ 按下态可达（M3 改良口径）。"},
    {"id": "rp.pg_next", "kind": "image", "z": 30, "visible_default": True,
     "asset": "ui/x_ui_rp_pgnext_off.png", "x": 1074, "y": 939, "w": 56, "h": 56, "opacity": 255,
     "state_assets": {"normal": "ui/x_ui_rp_pgnext_off.png",
                      "hover": "ui/x_ui_rp_pgnext_over.png",
                      "pressed": "ui/x_ui_rp_pgnext_on.png"},
     "state_group": "rp.pgnext",
     "source": "程序化生成：工具\\m52_make_replay_assets.py（56×56 三态，1:1 无 nine）",
     "note": NOTE_PGN},
    {"id": "rp.pg_next_hit", "kind": "hit", "z": 32, "visible_default": True,
     "x": 1067, "y": 931, "w": 70, "h": 72, "action": "gallery_page_next", "label": "",
     "font": FONT_HIT, "align": "center", "state_group": "rp.pgnext",
     "note": "「下一页」热区（70×72）。动作 `gallery_page_next`。带 `state_group`，同 `rp.pg_prev_hit`。"},
    {"id": "rp.pg_tx", "kind": "text", "z": 31, "visible_default": True,
     "x": 858, "y": 939, "w": 204, "h": 56, "font": FONT_PG,
     "align": "center", "valign": "middle", "wrap": False, "max_lines": 1, "sample": "1 / 2",
     "note": NOTE_PGT},
]

scr = {
    "id": "replay", "title_cn": "情景回想", "owner": "M4", "attach": "gal_shell",
    "note": ("**ISSUE-20260924-08 · M4 新建（2026-09-24）**：按主代理冻结的接口书新建**情景回想**页"
             "（用户指令「新建『情景回想』页，标准同参考作」；本作此前无此页）。\n"
             "★ **两页 5×5 = 50 栏**（`rp.list`，`orientation:\"h\"` + `max_cols:5` + `scroll.page_size:25`，M1 网格机制）："
             "第一页 25 情景栏**全部占位**（labels 占位文本 / actions 空串 / frames 空数组，**内容待填**）；"
             "第二页放 **10 件动画**（`replay_play:<行号>` 派发即止留编程组）+ 15 空栏。详见 `rp.list` note 的逐条口径。\n"
             "★ **结构照参考作 idx75 §2.3 情景回想 19 条**：caption → 归外壳（页签=切屏裁决）；preview 预览板 → `rp.preview`；"
             "#sample 网格 + item:normal 栏位 + item:thumb → `rp.list`（几何逐条取 `layers_75.json` 实测）；"
             "page 页码键 ×6 → `rp.pg_*`（取 M2/M3 三件式位置，有意差异）；**`big` 版式（opmovie/edmovie 大图位）不承接**"
             "—— 冻结书把第二页定为 25 栏动画网格，**有意差异**（参考件原版只有 OP/ED 两个大图位）。\n"
             "★ **如实登记**：①第一页内容占位待填（情景清单/跳转口径待主代理与编程组）；②动画实为 **10 件**"
             "（派单 11 件之差 = `ota_bg.txt` 是 data 文本非 movie，需主代理裁决）；③`replay_play` 动作名待 M1 补进 "
             "`_schema.md` 动作名表；④页码文本未接线（恒 1/2）；⑤「播放中」标记属运行期，本版为静态 ▶ 占位图形。\n"
             "★ 配色我方冰蓝霜白族（`layout\\palette.json` 唯一色值来源）；**文字一律引擎绘制**（本工程铁律）；"
             "素材 `ui/x_ui_rp_*.png` 11 件由 `工具\\m52_make_replay_assets.py` 程序化生成（幂等、自带自证）。\n"
             "★ **旧素材一件不删**；本屏为新增屏，`_index.json` 已登记（owner = M4）。"),
    "elements": els}

path = os.path.join(UI, "layout", "screens", "38_replay.json")
with io.open(path, "w", encoding="utf-8") as f:
    f.write(json.dumps(scr, ensure_ascii=False, indent=2) + "\n")
print("written", path, len(els), "elements,", len(labels), "labels")
