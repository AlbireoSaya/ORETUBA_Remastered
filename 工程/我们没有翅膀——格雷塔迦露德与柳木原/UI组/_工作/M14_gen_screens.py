# -*- coding: utf-8 -*-
r"""M14_gen_screens.py —— 生成 M14 三屏的 layout JSON（可复跑、幂等）
==========================================================================
Issue : UI 美术组 · M14（Fragment 页 + 鉴赏模式 + 剧情流程图）
写权限: layout/screens/31_fragment.json、layout/screens/27_gallery.json、
        layout/screens/32_flowchart.json（本脚本是这三份文件的**生成器**）

为什么用生成器而不是手写 JSON
------------------------------
任务书要求「番外标题取自 spine.json、数据不得手写」；三屏的格子 / 方框坐标又
必须**逐条消费** `_工作\M11_生成几何.json` 的实测几何。手抄 40 个标题 + 40 组
坐标既易错又不可复跑，故本脚本把「数据源 → layout JSON」固化为确定性变换。

数据源（只读）
--------------
  A `_工作\M11_生成几何.json`   —— M11 实测几何（fragpage.cells / gallerypage.* / flownode）
  B `资源组\剧本\spine.json`    —— side_stories[53]（番外标题）、acts[11]（幕名/规模）
  C `krkr\assets\ui\*.png`      —— 尺寸以 PNG 实际像素为准（image 必须 1:1）

复跑
----
    cd "工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作"
    python M14_gen_screens.py
然后回到 `工具\` 跑 `python gen_layout.py` 与 `python verify_ui.py`。

配色口径（**重要**）
--------------------
M11 交来的三张底图（fragpage / gallerypage）与四种方框 PNG **都是浅色**，
故这三屏的文字一律用色板里的**深色键**（不新增 palette 键 —— palette.json 归 M1）：
  · 正文/标签   @palette.node_locked   #4A4A56（色板中最深的中性色）
  · 强调/计数   @palette.highlight     #3A5A9A
  · 次级说明    @palette.edge_line     #6A6A7A
  · 未解锁文字  @palette.text_disabled #8A8A96（运行期由 ui_flow.tjs / ui_fragment.tjs 改写）
流程图屏的页眉/页脚带是黑底，故其上文字仍用浅色键（text_title / text_menu / text_hint）。
"""

from __future__ import annotations

import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))            # …\UI组\_工作
UI = os.path.dirname(HERE)                                   # …\UI组
PROJ = os.path.dirname(UI)                                   # …\我们没有翅膀——…
RES = os.path.join(PROJ, "资源组")
SCREENS = os.path.join(UI, "layout", "screens")

GEO = json.load(io.open(os.path.join(HERE, "M11_生成几何.json"), encoding="utf-8"))
SPINE = json.load(io.open(os.path.join(RES, "剧本", "spine.json"), encoding="utf-8"))

# ── 色板键（全部来自 layout/palette.json，不新增）────────────────────
C_TEXT_DARK = "@palette.node_locked"      # 浅底上的正文（深中性灰）
C_ACCENT_DK = "@palette.highlight"        # 浅底上的强调（深蓝）
C_SUB_DARK = "@palette.edge_line"         # 浅底上的次级说明
C_DIM_DARK = "@palette.text_disabled"     # 浅底上的弱化文字
C_TEXT_LT = "@palette.text_menu"          # 黑底上的按钮文字
C_HINT_LT = "@palette.text_hint"          # 黑底上的说明
C_TITLE_LT = "@palette.text_title"        # 黑底上的标题
C_SMALL_LT = "@palette.text_small"        # 黑底上的小字
C_EDGE = "@palette.edge_line"
C_FILL = "@palette.panel_fill"
C_FILL_OPA = "@palette.panel_fill_opa"
C_LETTERBOX = "@palette.letterbox"
C_SHADOW = "@palette.shadow"

# 方框 PNG 尺寸（几何实测，image 必须 1:1 → w/h 等于此值）
BOX_H = {f["semantic"]: f["size"][1] for f in GEO["flownode"]}
BOX_W = GEO["flownode"][0]["size"][0]
BOX_ASSET = {f["semantic"]: "ui/" + f["file"] for f in GEO["flownode"]}
BOX_CN = {
    "normal":    "一般剧情",
    "badend":    "BAD END / 普通结局",
    "important": "重要章节（影响后续剧情发展）",
    "goodend":   "GOOD END（包括女主角非坏结局的结尾）",
}
# 图例色块：借用色板里与四种方框色调最接近的键
#   （色板无粉色键 → GOOD END 用 @palette.text_name 的暖色近似，已在报告中登记为色板缺口）
BOX_SWATCH = {
    "normal":    "@palette.accent",          # 浅蓝
    "badend":    "@palette.edge_line",       # 银灰
    "important": "@palette.node_available",  # 亮蓝
    "goodend":   "@palette.text_name",       # 暖色近似（粉：色板无此键）
}

# 节点 → 方框类型（判定依据见 工具\gen_flow_data.py 的 NODE_BOX，逐条含出处）
NODE_BOX = {
    "N01": "normal", "N02": "normal", "N03": "normal",
    "N04": "goodend", "N05": "goodend", "N06": "goodend",
    "N07": "goodend", "N08": "goodend", "N09": "goodend",
    "N10": "badend", "N11": "normal",
    "B01": "important", "B02": "important",
}
# 纵排行序（与 gen_flow_data.py 的 FLOW_ORDER 一致）
FLOW_ORDER = ["N01", "N02", "N03", "N04", "B01", "N08", "N05", "N06", "B02", "N07",
              "N09", "N10", "N11"]
NODE_EL = {
    "N01": "flow.n01", "N02": "flow.n02", "N03": "flow.n03", "N04": "flow.n04",
    "N05": "flow.n05", "N06": "flow.n06", "N07": "flow.n07", "N08": "flow.n08",
    "N09": "flow.n09", "N10": "flow.n10", "N11": "flow.n11",
    "B01": "flow.b01", "B02": "flow.b02",
}
NODE_ACT = {"N01": 1, "N02": 2, "N03": 3, "N04": 4, "N05": 5, "N06": 6, "N07": 7,
            "N08": 8, "N09": 9, "N10": 10, "N11": 11}
BRANCH_SCENE = {"B01": "ot_s01_02c", "B02": "s03_09a"}

# 流程图的版面常量（**M18「一屏看全」的坐标依据，逐条在报告里给出**）
#
#   M18（2026-09-20）把 M14 的「纵向长图 + 视口滚动」改为**单屏 2 列 × 7 行网格**：
#   13 个节点全部落在一屏内，无需滚动。方框用 `nine:{l:0,t:0,r:0,b:0}` 做**等比缩放**
#   （该写法是 _schema.md §六 明文允许的「整图缩放」语义，主代理已授权）。
#
#   缩放倍率的推导（唯一自由变量是「7 行要塞进多高的视口」）：
#     视口高 = 页脚带顶 FLOW_FTR_Y(950) − 页眉带底 FLOW_TOP(110) = 840 px
#     行槽高 + 行间距 = 840 / 7 = 120 px  →  取槽 112 + 间距 8
#     方框最高者 goodend 234 px 必须 ≤ 112  →  s ≤ 112/234 = 0.4786
#     取 s = 0.4785 → 宽 1152×s = 551.7 → 552；四种方框高 111 / 104 / 106 / 112
#     （逐项 int(h×s+0.5)；与 552/1152=0.4792 的最大偏差 0.3%，视觉上等比）
FLOW_SCALE     = 0.4785
FLOW_BOX_W     = 552        # int(1152 × FLOW_SCALE + 0.5)
FLOW_SLOT_H    = 112        # 行槽高 = 缩放后最高方框（goodend 234×0.4785 = 112）
FLOW_ROW_GAP   = 8          # 行间距（= 同列相邻节点之间的纵向连接条长度）
FLOW_ROW_PITCH = FLOW_SLOT_H + FLOW_ROW_GAP          # 120
FLOW_TOP       = 110        # 第 1 行槽顶 = 页眉带底（视口上沿）
FLOW_COL_X     = (300, 1068)  # 两列方框左边界；2×552 = 1104，两侧各留 300、列间留 216
FLOW_BUS_X     = 960        # 汇流总线 x（列间空隙 852…1068 的中线）
FLOW_WRAP_X    = 1024       # 跨列续接线的纵向通道 x（贴第 2 列一侧，减少与总线短横条的交点）
FLOW_WRAP_IN_Y = 140        # 跨列续接线进入 N06 左边界的 y（避开同一边上的汇流短横条 192）
FLOW_CV_N06_Y  = 192        # N06 汇流短横条在 N06 左边界的 y
FLOW_BYPASS_X  = 250        # N01→N03 左侧旁路通道 x（在第 1 列方框之外 300−50）
FLOW_EDGE_T    = 4          # 连线细条厚度（M14 的 6 px × 0.4785 ≈ 2.9；取 4 以在缩放下仍可辨）
FLOW_RING_PAD  = 3          # 三态色环相对方框的外扩（M14 的 8 px × 0.4785 ≈ 3.8 → 3）
FLOW_LABEL_OFF = 74         # 标签左缩进：方框「无装饰区」起点 154×0.4785 ≈ 74
FLOW_LABEL_W   = 355        # 标签宽：方框「无装饰区」154…896 → 74…429（宽 355）
FLOW_LABEL_FS  = 22         # 标签字号（实测：最长一行 20 字 = 311 px ≤ 355，见 _工作\M18_证据\measure_flowtext.txt）
FLOW_HDR_H     = 110        # 页眉固定带高（标题 + 副标题）
FLOW_FTR_Y     = 950        # 页脚固定带 y（图例 + 详情 + 返回）

# 节点在网格里的 (列, 行)：**列优先**填充（先填满第 1 列再填第 2 列），
# 列内自上而下 = 叙事顺序（FLOW_ORDER 的顺序保持不变）。
FLOW_GRID = {
    "N01": (0, 0), "N02": (0, 1), "N03": (0, 2), "N04": (0, 3),
    "B01": (0, 4), "N08": (0, 5), "N05": (0, 6),
    "N06": (1, 0), "B02": (1, 1), "N07": (1, 2), "N09": (1, 3),
    "N10": (1, 4), "N11": (1, 5),
}
# 汇流总线（五线汇入 s04）的四个**远端**源：N07 与 N09 同列相邻，其边由纵向连接条表达，
# 故不进总线。顺序 = 生成短横条的顺序。
FLOW_CONV_SRC = ["N06", "N04", "N08", "N05"]

FRAG_LABEL_PAD_L = 74      # 格内文字左缩进（避开格子左侧羽饰）
FRAG_LABEL_PAD_R = 10

GAL_TEXT_DEMO = "（演示数据）"

# 缩放后的方框高（int(h×s+0.5)），供流程图使用
BOX_H_S = {bt: int(h * FLOW_SCALE + 0.5) for bt, h in BOX_H.items()}


# ── 小工具 ──────────────────────────────────────────────────────────
def txt(el_id, x, y, w, h, size, color, sample, note, *, align="left",
        valign="middle", wrap=False, max_lines=1, bold=False, shadow=False,
        line_spacing=None, z=0, source=None, visible=True):
    el = {
        "id": el_id, "kind": "text", "z": z, "visible_default": visible,
        "x": x, "y": y, "w": w, "h": h,
        "font": {"size": size, "bold": bold, "color": color,
                 "shadow": shadow, "shadow_color": C_SHADOW, "shadow_ofs": 0},
        "align": align, "valign": valign, "wrap": wrap, "max_lines": max_lines,
        "sample": sample, "note": note,
    }
    if line_spacing is not None:
        el["line_spacing"] = line_spacing
    if source:
        el["source"] = source
    return el


def rect(el_id, x, y, w, h, color, opacity, note, z=0, visible=True):
    return {"id": el_id, "kind": "rect", "z": z, "visible_default": visible,
            "x": x, "y": y, "w": w, "h": h, "color": color, "opacity": opacity,
            "note": note}


def img(el_id, asset, x, y, w, h, note, z=0, source=None, nine=None,
        opacity=255, visible=True, dynamic=None):
    el = {"id": el_id, "kind": "image", "z": z, "visible_default": visible,
          "asset": asset, "x": x, "y": y, "w": w, "h": h, "opacity": opacity,
          "note": note}
    if nine is not None:
        el["nine"] = nine
    if source:
        el["source"] = source
    if dynamic:
        el["dynamic"] = dynamic
    return el


def hit(el_id, x, y, w, h, action, label, note, z=0, size=27, color=C_TEXT_LT,
        align="center", source=None, bold=False, visible=True):
    el = {"id": el_id, "kind": "hit", "z": z, "visible_default": visible,
          "x": x, "y": y, "w": w, "h": h, "action": action, "label": label,
          "font": {"size": size, "bold": bold, "color": color,
                   "shadow": False, "shadow_color": C_SHADOW, "shadow_ofs": 0},
          "align": align, "note": note}
    if source:
        el["source"] = source
    return el


def split_lines(s, n, width):
    """把一段中文按「句读优先」切成 n 行（每行目标宽度 width 字，行末保留标点）。
    先按 。；，、！？／/ 切成段，再贪心装箱成 n 行；不足补空串、超出并入末行。"""
    s = " ".join(str(s).split())
    if n <= 1:
        return [s]
    segs, cur = [], ""
    for ch in s:
        cur += ch
        if ch in "。；，、！？／/":
            segs.append(cur)
            cur = ""
    if cur:
        segs.append(cur)
    lines, cur = [], ""
    for seg in segs:
        if cur and len(cur) + len(seg) > width and len(lines) < n - 1:
            lines.append(cur)
            cur = seg
        else:
            cur += seg
    if cur:
        lines.append(cur)
    while len(lines) > n:                       # 末段并入上一段，保证段数恰好 n
        lines[n - 1] = "".join(lines[n - 1:])
        lines = lines[:n]
    while len(lines) < n:
        lines.append("")
    return lines


# ==================================================================
# ① 31_fragment.json —— Fragment 番外页（重写）
# ==================================================================
def build_fragment():
    fp = GEO["fragpage"]
    cells = fp["cells"]
    stories = SPINE["side_stories"]
    assert len(cells) == 40, "M11 几何的格子数应为 40，实为 %d" % len(cells)

    els = []
    els.append(img(
        "fragment.bg", "ui/x_gen_fragpage.png", 0, 0,
        fp["image_size"][0], fp["image_size"][1], z=0,
        source="生图入料\\生成结果\\Fragment.png → 工具\\prep_generated.py（整幅缩到 1920×1080，放大 1.1483×，用户明确授权）",
        note="Fragment 番外页底图（**满幅 1:1**）。标题「Fragment 碎片故事」、面板外框与 40 个格子边框均为底图自带，"
             "故本屏**不再叠引擎标题、不再叠九宫格边框**（用户 2026-09-20 明确要求）。"
             "40 个格子的矩形取自 _工作\\M11_生成几何.json 的 fragpage.cells（5 列 × 8 行，行优先）。"))

    for i in range(40):
        x, y, w, h = cells[i]
        st = stories[i]
        z = 20 + i * 2
        els.append(hit(
            "fragment.c%d_hit" % i, x, y, w, h, "fragment_enter", "",
            "第 %d 格热区（第 %d 行第 %d 列；矩形逐条取自 M11 几何 fragpage.cells[%d]）。"
            "action=fragment_enter —— 用户原话「每一个矩形框都是一段剧情，可以被点击进入」；"
            "本屏只更新收集进度并持久化，**不跳转剧情**（跳转属编程组）。"
            "label 置空以免与 fragment.c%d_title 重复绘制。"
            "★ 元素 id 用**无补零**编号（c%d）以便 TJS2 侧字符串拼接（TJS2 无 sprintf）。"
            % (i + 1, i // 5 + 1, i % 5 + 1, i, i, i),
            z=z + 1))
        els.append(txt(
            "fragment.c%d_title" % i, x + FRAG_LABEL_PAD_L, y,
            w - FRAG_LABEL_PAD_L - FRAG_LABEL_PAD_R, h,
            27, C_TEXT_DARK, st["title_cn"],
            "第 %d 格番外标题：**逐字取自** 资源组\\剧本\\spine.json 的 side_stories[%d].title_cn"
            "（原文 title_jp=%s ｜ scene_id=%s ｜ 组=%s）。"
            "字号 27 依据格高 %d px（2 行 × 27 × 1.2 = 64.8 < %d）；"
            "文字区宽 %d px → 每行约 %d 字，2 行容量 %d 字 ≥ 本屏最长标题 15 字，已实测不溢出。"
            % (i + 1, i, st["title_jp"], st["scene_id"], st["group"],
               h, h, w - FRAG_LABEL_PAD_L - FRAG_LABEL_PAD_R,
               (w - FRAG_LABEL_PAD_L - FRAG_LABEL_PAD_R) // 27,
               2 * ((w - FRAG_LABEL_PAD_L - FRAG_LABEL_PAD_R) // 27)),
            align="center", valign="middle", wrap=True, max_lines=2,
            line_spacing=1.2, z=z))

    els.append(txt(
        "fragment.count", 70, 944, 1120, 58, 27, C_ACCENT_DK,
        "已收集 0 / 40（本期上屏）｜ 番外总 53 条 / 6 组",
        "收集计数（保留：Fragment 系统的核心反馈）。**不遮挡任何格子** —— 位于面板底部空白带 y=944–1002"
        "（格子最低 y=930，面板底 1026）。运行期由 ui_fragment.tjs 改写已收集数；"
        "分母 40 = 本期上屏格数，53 = spine.json side_stories[] 总条数。",
        align="left", valign="middle", z=110))

    els.append(hit(
        "fragment.hit_back", 1520, 944, 320, 58, "close", "返回",
        "返回键（action=close，由 M2 界面栈弹栈）。底图无按钮件，故仅引擎绘字，不叠九宫格边框。",
        z=112, size=30, color=C_TEXT_DARK))

    return {
        "id": "fragment",
        "title_cn": "番外（Fragment）选择",
        "owner": "M4",
        "note": "**M14 重写（2026-09-20）**：背景改用 AI 生图底图 ui/x_gen_fragpage.png（1920×1080 满幅，"
                "自带标题「Fragment 碎片故事」与面板边框，故不再叠引擎标题/九宫格边框）。"
                "**40 个格子**的坐标**逐条取自** _工作\\M11_生成几何.json 的 fragpage.cells"
                "（5 列 × 8 行，行优先），每格一个 hit（action=fragment_enter）+ 一个 text（番外标题）。"
                "标题**逐字取自** 资源组\\剧本\\spine.json 的 side_stories[].title_cn，**无自造**。"
                "旧版 M4 的「6 组格阵 + 详情栏 + 进入键」设计已废止（用户 2026-09-20 要求彻底换用新素材与新交互）。"
                "★ **53 条番外 vs 40 个格子**：本期只上屏前 40 条（= 底图实测格数）；"
                "余 13 条（第 41–53 条，全部属「番外·おまけ（成人向）」组）的呈现方式"
                "（第 2 页 / 格内滚动 / 另开一屏）**待定**，需主代理裁决 —— 见 _工作\\M14_报告.md「未决项」。"
                "★ 配色：底图为浅色，故文字一律取色板深色键（node_locked / highlight / text_disabled），"
                "未新增 palette 键（palette.json 归 M1）。"
                "生成器：_工作\\M14_gen_screens.py（幂等可复跑）。",
        "elements": els,
    }


# ==================================================================
# ② 27_gallery.json —— 鉴赏模式（重写）
# ==================================================================
def build_gallery():
    gp = GEO["gallerypage"]
    boxes = gp["left_boxes"]
    pv = gp["preview"]
    nb = gp["namebar"]
    bars = gp["intro_bars"]
    acts = SPINE["acts"]

    els = []
    els.append(img(
        "gallery.bg", "ui/x_gen_gallerypage.png", 0, 0,
        gp["image_size"][0], gp["image_size"][1], z=0,
        source="生图入料\\生成结果\\鉴赏UI.png → 工具\\prep_generated.py（整幅缩到 1920×1080，放大 1.1483×，用户明确授权）",
        note="鉴赏模式底图（**满幅 1:1**）。左侧 4 个选择框、右侧预览大框、深色章节名条、4 条浅色简介条"
             "均为底图自带，矩形逐条取自 _工作\\M11_生成几何.json 的 gallerypage。"
             "用户原话：「左边四个框用来选择要观看的场景/图片，可以上下滑动。"
             "右边上面大框是场景预览图，下面深色条是章节名字，浅色条是章节剧情简介」。"))

    # 左侧 4 个选择框：hit + text（可视窗口，4 条/页 → 11 幕共 3 页）
    for k in range(4):
        x, y, w, h = boxes[k]
        a = acts[k]
        els.append(hit(
            "gallery.sel%d_hit" % k, x, y, w, h, "", "",
            "左侧选择框 %d 热区（第 %d / 3 页第 %d 条；矩形取自 M11 几何 gallerypage.left_boxes[%d]）。"
            "**动作名待编程组定义**（选择某场景/图片并刷新右侧预览与名条/简介；"
            "动作表 §六 未覆盖该动作，故按 M5 裁决写空串 action，**不臆造动作名**）。"
            % (k + 1, 1, k + 1, k), z=10 + k * 2))
        els.append(txt(
            "gallery.sel%d_name" % k, x + 100, y, w - 130, h, 30, C_TEXT_DARK, a["name"],
            "左侧选择框 %d 的场景/图片名。**演示数据** —— 取 资源组\\剧本\\spine.json 的 acts[%d].name"
            "（幕名，非自造）；**真值由编程组从素材库按场景/CG 条目填充**（本屏为「可视窗口」，"
            "4 条/页，共 3 页；翻页见 gallery.hit_prev / gallery.hit_next）。"
            % (k + 1, k), align="left", valign="middle", wrap=True, max_lines=2,
            line_spacing=1.2, z=11 + k * 2))

    # 右侧预览大框：动态层
    els.append(img(
        "gallery.preview", None, pv[0], pv[1], pv[2], pv[3], z=30,
        dynamic="gallery_preview",
        note="**右侧场景预览大框（动态层）**：asset=null + dynamic=\"gallery_preview\"，"
             "运行时由编程组填入当前选中的场景图（矩形取自 M11 几何 gallerypage.preview）。"
             "按 schema §四，两侧渲染器**必须保留该层**，未填充时画占位底色（不得跳过）；"
             "写法与 10_dialog.json 的 dlg.content（asset=null + dynamic=\"story_background\"）一致。"))

    # 深色章节名条
    els.append(txt(
        "gallery.chapter_name", nb[0], nb[1] - 4, 700, nb[3] + 8, 30, C_ACCENT_DK,
        acts[0]["name"],
        "深色条上的**章节名**（用户原话「下面深色条是章节名字」）。矩形取自 M11 几何 gallerypage.namebar"
        "（x=%d y=%d w=%d h=%d）；文字框向右延伸到 x=%d 以容纳长幕名（如「亚衣线·s03c（R 版 55 场景版）」20 字），"
        "条右侧的细装饰线（namebar_line）为底图自带。**演示值**：取 acts[0].name，真值由编程组按选中项填充。"
        % (nb[0], nb[1], nb[2], nb[3], nb[0] + 700),
        align="left", valign="middle", wrap=False, max_lines=1, z=31))

    # 4 条浅色简介条：每条的 y 取 M11 实测，文字盒高 44（居中压在 22 px 的浅色条上）
    intro = split_lines(acts[0]["note"], 3, 24)
    intro_lines = ["来源 %s ｜ %d 场景 ｜ %d 行"
                   % ("/".join(acts[0]["source"]), len(acts[0]["scenes"]), acts[0]["line_count"])] + intro
    for k in range(4):
        bx, by, bw, bh = bars[k]
        els.append(txt(
            "gallery.intro%d" % k, bx, by - 11, bw, 44, 27, C_SUB_DARK, intro_lines[k],
            "浅色简介条第 %d 行的正文（用户原话「浅色条是章节剧情简介」）。"
            "**选择「4 个 text（每行一条）」而非「1 个 text 跨 4 条」**，理由："
            "4 条浅色条是底图上**物理分离**的 4 条色带（y=%d/%d/%d/%d，各高 %d–%d），"
            "且每条左端各有一枚菱形项目符号；用一个 text 块跨 4 条需把行距设成 %.2f 倍才能对齐，"
            "而 krkr 的 Font 行高与 HTML 的 line-height 口径不同，极易在两侧产生累积漂移；"
            "逐条元素则每条**必然**落在自己的色带上，1:1 由几何保证。"
            "**演示值**：第 0 行取 acts[0] 的来源/规模，第 1–3 行取 acts[0].note 的三段切分；"
            "真值由编程组按选中项填充。"
            % (k + 1, bars[0][1], bars[1][1], bars[2][1], bars[3][1], min(b[3] for b in bars),
               max(b[3] for b in bars), (bars[1][1] - bars[0][1]) / 27.0),
            align="left", valign="middle", wrap=False, max_lines=1, z=40 + k))

    # 翻页：两个 hit + 页码（选择理由见 note）
    els.append(txt(
        "gallery.page", 65, 978, 380, 56, 27, C_TEXT_DARK,
        "第 1 / 3 页（演示）",
        "页码指示。页数 = ceil(11 幕 / 每页 4 条) = 3；**演示值**，真值由编程组按素材库条目数计算。"
        "文本刻意保持短（不写「11 幕 / 每页 4 条」等推导过程）—— 原写法右端到 x≈445，"
        "与「上一页」按钮（x=470）视觉上贴在一起；推导过程改记在本 note 里。",
        align="left", valign="middle", z=50))
    els.append(hit(
        "gallery.hit_prev", 470, 978, 190, 56, "page_prev", "上一页",
        "**翻页方式选择**：用「上一页/下一页」两个 hit（动作取动作表已有的 page_prev / page_next），"
        "**不用 list 的 scroll 字段**。理由：① 左侧 4 个框是 M11 实测的**逐框不等宽矩形**"
        "（787 宽 × 207/203/205/206 高，x 相同但高不同），`list` 只能表达等尺寸重复项，"
        "改成 list 就必须放弃实测几何；② 每个框要显示**不同的场景/图片名**，"
        "而 list 的 item_frame/highlight 无法承载逐项文本样式差异；"
        "③ 用户原话是「可以上下滑动」，本屏以 4 条/页翻页等价实现（每页 4 条 = 可视窗口高度）。",
        z=52, size=27, color=C_TEXT_DARK))
    els.append(hit(
        "gallery.hit_next", 672, 978, 190, 56, "page_next", "下一页",
        "下一页（page_next，理由同 gallery.hit_prev）。", z=52, size=27, color=C_TEXT_DARK))
    els.append(hit(
        "gallery.hit_back", 1540, 972, 320, 68, "close", "返回",
        "返回键（action=close）。底图无按钮件，仅引擎绘字，不叠九宫格边框。",
        z=54, size=30, color=C_TEXT_DARK))

    return {
        "id": "gallery",
        "title_cn": "CG 画廊",
        "owner": "M5",
        "note": "**M14 重写（2026-09-20）**：背景改用 AI 生图底图 ui/x_gen_gallerypage.png（1920×1080 满幅）。"
                "元素坐标**逐条取自** _工作\\M11_生成几何.json 的 gallerypage："
                "左侧 4 框 left_boxes / 预览大框 preview / 深色章节名条 namebar / 4 条浅色简介条 intro_bars。"
                "用户原话：「左边四个框用来选择要观看的场景/图片，可以上下滑动。"
                "右边上面大框是场景预览图，下面深色条是章节名字，浅色条是章节剧情简介」。"
                "旧版 M5 的「3×3 缩略图网格 + 页码滑条」设计已废止（用户 2026-09-20 要求彻底换用新素材）。"
                "★ 预览大框为**动态层**（asset=null + dynamic=\"gallery_preview\"），运行时由编程组填当前选中场景图。"
                "★ 左侧 4 框的**选择动作**动作表未覆盖 → 写空串 action + note「待编程组定义」（不臆造动作名）；"
                "翻页用动作表已有的 page_prev / page_next。"
                "★ 配色：底图为浅色，文字取色板深色键（node_locked / highlight / edge_line）。"
                "生成器：_工作\\M14_gen_screens.py（幂等可复跑）。",
        "elements": els,
    }


# ==================================================================
# ③ 32_flowchart.json —— 剧情流程图（M18：单屏 2 列 × 7 行总览）
# ==================================================================
def build_flowchart():
    acts = {a["act"]: a for a in SPINE["acts"]}
    bp = {b["scene_id"]: b for b in SPINE["branch_points"]}
    T = FLOW_EDGE_T
    H2 = T // 2

    def row_top(r):
        return FLOW_TOP + r * FLOW_ROW_PITCH

    def row_mid(r):
        return row_top(r) + FLOW_SLOT_H // 2

    # ── 节点几何（列优先网格；方框在行槽内垂直居中）────────────────────
    geo = {}
    for nid in FLOW_ORDER:
        c, r = FLOW_GRID[nid]
        bt = NODE_BOX[nid]
        bh = BOX_H_S[bt]
        geo[nid] = {
            "col": c, "row": r, "box": bt,
            "x": FLOW_COL_X[c], "y": row_top(r) + (FLOW_SLOT_H - bh) // 2,
            "w": FLOW_BOX_W, "h": bh,
        }

    els = []
    els.append(rect("flow.bg", 0, 0, 1920, 1080, C_LETTERBOX, 255,
                    "画布底色（黑）。节点方框为浅色贴图，黑底提供对比。", z=0))

    # ── 连线（z=10 起，画在方框之下）────────────────────────────────────
    # ① 同列相邻节点的纵向连接条（12 个相邻对里除跨列那一对之外的 11 对）
    seq_no = 0
    seq_of_pair = {}
    for i in range(len(FLOW_ORDER) - 1):
        a, b = FLOW_ORDER[i], FLOW_ORDER[i + 1]
        if geo[a]["col"] != geo[b]["col"]:
            continue                      # 跨列 → 由 ② 的续接线表达
        seq_no += 1
        el_id = "flow.seq%02d" % seq_no
        seq_of_pair[(a, b)] = el_id
        x = geo[a]["x"] + FLOW_BOX_W // 2 - H2
        y = row_top(geo[a]["row"]) + FLOW_SLOT_H
        els.append(rect(
            el_id, x, y, T, FLOW_ROW_GAP, C_EDGE, 255,
            "纵向连接条：%s → %s（同一列、相邻行）。几何依据：x = 方框水平中线 − 半条宽"
            "（%d + %d − %d = %d），y = 上一行行槽底（%d），高 = 行间距 %d。"
            "它表达「叙事顺序相邻」；其中与真实边重合的那些在 工具\\gen_flow_data.py 的 "
            "EDGE_ELEMENT 里被登记为该边的屏上元素。" % (a, b, geo[a]["x"], FLOW_BOX_W // 2, H2, x, y, FLOW_ROW_GAP),
            z=10 + seq_no))

    # ② 跨列续接线（N05 → N06）：三段折线，走列间空隙靠第 2 列一侧的纵向通道
    a, b = FLOW_ORDER[6], FLOW_ORDER[7]           # N05, N06
    y0 = row_mid(geo[a]["row"])
    els.append(rect(
        "flow.wrap_a", geo[a]["x"] + FLOW_BOX_W, y0 - H2, FLOW_WRAP_X - (geo[a]["x"] + FLOW_BOX_W), T, C_EDGE, 255,
        "跨列续接线第 1 段（横）：从 N05 右边界的垂直中线右行到纵向通道 x=%d。" % FLOW_WRAP_X, z=11))
    els.append(rect(
        "flow.wrap_b", FLOW_WRAP_X - H2, FLOW_WRAP_IN_Y, T, y0 - FLOW_WRAP_IN_Y, C_EDGE, 255,
        "跨列续接线第 2 段（纵）：沿 x=%d 从 N06 的接入高度 y=%d 下到 N05 的垂直中线 y=%d。"
        "接入高度取 %d 而非行中线 %d，是为避开同一条 N06 左边上的汇流短横条（y=%d）。"
        % (FLOW_WRAP_X, FLOW_WRAP_IN_Y, y0, FLOW_WRAP_IN_Y, row_mid(geo[b]["row"]), FLOW_CV_N06_Y), z=11))
    els.append(rect(
        "flow.wrap_c", FLOW_WRAP_X, FLOW_WRAP_IN_Y - H2, geo[b]["x"] - FLOW_WRAP_X, T, C_EDGE, 255,
        "跨列续接线第 3 段（横）：从纵向通道接到 N06 的左边界（x=%d）。"
        "★ 该段**不对应任何真实边**（叙事顺序里 N05→N06 是两条平行线 s02/s03 的并列），"
        "只表示「阅读顺序在第 2 列顶部继续」，已在屏 note 与 M18 报告中登记。"
        % geo[b]["x"], z=11))

    # ③ 左侧旁路：N01 → N03（真实边 E02；同列跨一行，纵向连接条表达不了）
    n01, n03 = geo["N01"], geo["N03"]
    y01, y03 = row_mid(n01["row"]), row_mid(n03["row"])
    els.append(rect(
        "flow.e02_a", FLOW_BYPASS_X, y01 - H2, n01["x"] - FLOW_BYPASS_X, T, C_EDGE, 255,
        "左侧旁路第 1 段（横）：N01 左边界 → 旁路通道 x=%d（对应真实边 E02：N01→N03，"
        "主线顺序 1→3）。" % FLOW_BYPASS_X, z=12))
    els.append(rect(
        "flow.e02_b", FLOW_BYPASS_X - H2, y01, T, y03 - y01, C_EDGE, 255,
        "左侧旁路第 2 段（纵）：沿 x=%d 从 N01 的垂直中线 y=%d 下到 N03 的垂直中线 y=%d。"
        "通道取 %d，在第 1 列方框左边界 %d 之外 50 px，故不压到任何方框。"
        % (FLOW_BYPASS_X, y01, y03, FLOW_BYPASS_X, n01["x"]), z=12))
    els.append(rect(
        "flow.e02_c", FLOW_BYPASS_X, y03 - H2, n03["x"] - FLOW_BYPASS_X, T, C_EDGE, 255,
        "左侧旁路第 3 段（横）：旁路通道 → N03 左边界。三段合起来即边 E02 的屏上表达。", z=12))

    # ④ 汇流总线（五线汇入 s04 的远端四源）＋ 短横条
    cv_ys = [row_mid(geo[s]["row"]) for s in FLOW_CONV_SRC]
    bus_top = min(cv_ys + [FLOW_WRAP_IN_Y])
    bus_bot = max(cv_ys)
    els.append(rect(
        "flow.bus_c", FLOW_BUS_X - H2, bus_top, T, bus_bot - bus_top, C_EDGE, 255,
        "**汇流总线（五线汇入 s04）**：纵线画在列间空隙的中线 x=%d，y 从最高源（%d）到最低源（%d）。"
        "四个远端源（N06 / N04 / N08 / N05）各用一条短横条接到本线；N07→N09 与 N09 同列相邻，"
        "由纵向连接条 flow.seq09 表达，故不进总线。"
        % (FLOW_BUS_X, bus_top, bus_bot), z=13))
    for k, s in enumerate(FLOW_CONV_SRC):
        g = geo[s]
        if g["col"] == 0:      # 第 1 列：短横条从方框右边界向右接到总线
            x0, w0 = g["x"] + FLOW_BOX_W, FLOW_BUS_X - (g["x"] + FLOW_BOX_W)
        else:                  # 第 2 列：短横条从方框左边界向左接到总线
            x0, w0 = FLOW_BUS_X, g["x"] - FLOW_BUS_X
        yy = FLOW_CV_N06_Y if s == "N06" else row_mid(g["row"])
        els.append(rect(
            "flow.cv%d_a" % (k + 1), x0, yy - H2, w0, T, C_EDGE, 255,
            "汇流短横条：%s → 总线（x=%d → %d，位于该节点垂直中线 y=%d%s）。"
            % (s, x0, x0 + w0, yy,
               "；N06 同时是跨列续接线的落点，故错开到 y=%d" % FLOW_CV_N06_Y if s == "N06" else ""),
            z=13))
    # 总线 → N09 的引入段（与 N04 的短横条同 y，二者连成 N04→N09 的直线）
    g9 = geo["N09"]
    y9 = row_mid(g9["row"])
    els.append(rect(
        "flow.cv_n09", FLOW_BUS_X, y9 - H2, g9["x"] - FLOW_BUS_X, T, C_EDGE, 255,
        "汇流总线 → N09 左边界的引入段（y=%d，与 N04 的短横条同高，二者连起来即边 E10 的直线表达）。" % y9,
        z=13))

    # ── 13 个节点（状态环 → 方框图 → 标签 → 热区）──────────────────────
    for i, nid in enumerate(FLOW_ORDER):
        g = geo[nid]
        bt, x0, y0, h = g["box"], g["x"], g["y"], g["h"]
        el = NODE_EL[nid]
        z = 20 + i * 5
        if nid in NODE_ACT:
            a = acts[NODE_ACT[nid]]
            label = a["name"]
            sub = "%s · %d 场景 / %d 行" % ("/".join(a["source"]), len(a["scenes"]), a["line_count"])
            src_note = ("spine.json acts[%d]（幕 %d）：幕名逐字取自 acts[].name，未自造；"
                        "规模取自 acts[].scenes 与 acts[].line_count。" % (NODE_ACT[nid] - 1, NODE_ACT[nid]))
        else:
            b = bp.get(BRANCH_SCENE[nid], {})
            label = "分歧点 " + (b.get("route", "") or BRANCH_SCENE[nid])
            sub = "%d 选项 · %s" % (b.get("option_count", 0), BRANCH_SCENE[nid])
            src_note = ("spine.json branch_points[]（scene_id=%s，选项 %d 条）：选项数与场景 id 取自数据，未自造。"
                        % (BRANCH_SCENE[nid], b.get("option_count", 0)))

        els.append(rect(
            el + "_fill", x0 - FLOW_RING_PAD, y0 - FLOW_RING_PAD,
            FLOW_BOX_W + 2 * FLOW_RING_PAD, h + 2 * FLOW_RING_PAD, "@palette.node_locked", 235,
            "节点 %s 的**三态色环**（运行期由 ui_flow.tjs 改写：已读=@palette.node_visited / "
            "可前往=@palette.node_available / 未解锁=@palette.node_locked）。"
            "位置=方框外扩 %d px 的一圈（M14 的 8 px × 缩放 %s ≈ 3），画在方框图**之下**，"
            "故表现为彩色描边环 —— 既保住三态着色机制（uiFlowSyncFlowchart 仍只写 _fill.color），"
            "又不遮挡方框美术。行间距 %d px > 2×%d，故相邻行的色环不重叠。"
            % (nid, FLOW_RING_PAD, FLOW_SCALE, FLOW_ROW_GAP, FLOW_RING_PAD), z=z))
        els.append(img(
            el + "_box", BOX_ASSET[bt], x0, y0, FLOW_BOX_W, h,
            "节点 %s 的**方框图**（%s）。asset=%s，w/h=%d×%d = PNG 实际尺寸 %d×%d × **等比 %s**，"
            "用 `nine:{l:0,t:0,r:0,b:0}` 表达「整图缩放」（该写法是 _schema.md §六 明文允许的合法语义，"
            "主代理 2026-09-20 授权；代价是 w/h 不再等于 PNG 实尺寸，溯源靠本 note）。"
            "缩放倍率的推导：7 行须落进视口 840 px → 行槽 112；方框最高 goodend 234 px → s ≤ 112/234 = 0.4786。"
            "方框类型判定依据：%s"
            % (nid, BOX_CN[bt], BOX_ASSET[bt], FLOW_BOX_W, h, BOX_W, BOX_H[bt], FLOW_SCALE,
               {"normal": "一般剧情 —— 开篇/框架/短篇集，§五 结局矩阵无其结局",
                "badend": "BAD END / 普通结局 —— 幕内含明确 Ｂ－ＥＮＤ",
                "important": "重要章节 —— 关键分歧点，影响后续剧情发展",
                "goodend": "GOOD END —— 幕内含女主角非坏结局 / 真结局"}[bt]),
            z=z + 1, nine={"l": 0, "t": 0, "r": 0, "b": 0},
            source="生图入料\\生成结果\\流程图的章节方框.png → 工具\\prep_generated.py（裁紧后缩到宽 1152）"))
        els.append(txt(
            el + "_label", x0 + FLOW_LABEL_OFF, y0, FLOW_LABEL_W, h,
            FLOW_LABEL_FS, C_TEXT_DARK, label + "\n" + sub,
            "节点 %s 标签（幕名/分歧点名 + 来源·规模）。%s"
            "文字区 x=%d…%d = 方框「无装饰区」（box-local 154…896 × 缩放 %s）内缩后的区间，"
            "两侧各留 %d px，避开左侧羽饰与右侧雪花/心/血滴。"
            "字号 %d：实测最长一行（N07「亚衣线·s03c（R 版 55 场景版）」20 字）宽 311 px ≤ %d px，"
            "最长副行（N10「ota · 119 场景 / 13139 行」）宽 261 px，均在区内（证据 _工作\\M18_证据\\measure_flowtext.txt）；"
            "2 行 × %d × 1.25 = 55 px ≤ 方框高 %d。"
            "颜色取深色键：方框图是浅色，旧版的 @palette.text_menu（近白）在新方框上不可见，故用 @palette.node_locked。"
            % (nid, src_note, x0 + FLOW_LABEL_OFF, x0 + FLOW_LABEL_OFF + FLOW_LABEL_W, FLOW_SCALE,
               FLOW_LABEL_OFF, FLOW_LABEL_FS, FLOW_LABEL_W, FLOW_LABEL_FS, h),
            align="center", valign="middle", wrap=True, max_lines=2, line_spacing=1.25,
            bold=True, z=z + 2))
        els.append(hit(
            el + "_hit", x0, y0, FLOW_BOX_W, h, "flow_node_" + nid, "",
            "节点 %s 热区（action=flow_node_%s，由 ui_flow.tjs 处理）。"
            "label 置空以免与 %s_label 重复绘制。" % (nid, nid, el), z=z + 3))

    # ── 页眉固定带 ────────────────────────────────────────────────────
    els.append(rect("flow.hdr_band", 0, 0, 1920, FLOW_HDR_H, C_LETTERBOX, 255,
                    "**页眉带**：黑底，覆盖 y=0–%d。ui_flow.tjs 以本元素的底边（y+h=%d）"
                    "作为**视口上沿**，不硬编码数字。" % (FLOW_HDR_H, FLOW_HDR_H), z=90))
    els.append(txt(
        "flow.title", 0, 10, 1920, 48, 42, C_TITLE_LT, "剧情流程图",
        "屏标题（引擎绘制）。", align="center", valign="middle", bold=True,
        shadow=True, z=91))
    els.append(txt(
        "flow.info", 0, 62, 1920, 30, 19, C_SMALL_LT,
        "节点 13（幕 11 + 关键分歧点 2）｜ 方框 4 型：一般剧情 / BAD END / 重要章节 / GOOD END ｜ "
        "一屏总览：2 列 × 7 行，方框等比 0.478 缩放（%d×%d）" % (FLOW_BOX_W, BOX_H_S["goodend"]),
        "副标题：节点/连线规模 + 四种方框语义 + 版式与缩放倍率。"
        "节点数 = spine.json 11 幕 + 2 个关键分歧点；方框 4 型的语义由用户 2026-09-20 定义。",
        align="center", valign="middle", z=92))

    # ── 页脚固定带：4 行图例 + 详情 + 返回键 ───────────────────────────
    els.append(rect("flow.ftr_band", 0, FLOW_FTR_Y, 1920, 1080 - FLOW_FTR_Y, C_LETTERBOX, 255,
                    "**页脚带**：黑底，覆盖 y=%d–1080。ui_flow.tjs 以本元素的顶边（y=%d）"
                    "作为**视口下沿**，不硬编码数字。" % (FLOW_FTR_Y, FLOW_FTR_Y), z=90))
    els.append(rect("flow.legend_fill", 60, 956, 720, 118, C_FILL, C_FILL_OPA,
                    "图例面板填充。宽 720（60…780）：四种方框的中文说明最长一条为 "
                    "「4. GOOD END（包括女主角非坏结局的结尾）」，字号 19 → 实测不溢出文本区 650 px。",
                    z=91))
    els.append(img(
        "flow.legend_frame", "ui/panel_frame.png", 60, 956, 720, 118,
        "图例面板边框（九宫格）。", z=92,
        source="UI 组自制：九宫格边框件 ui/panel_frame.png",
        nine={"l": 20, "t": 8, "r": 20, "b": 8}, opacity=235))
    for k, bt in enumerate(["normal", "badend", "important", "goodend"]):
        els.append(rect(
            "flow.lg%d_sw" % (k + 1), 80, 962 + k * 28, 24, 24, BOX_SWATCH[bt], 255,
            "图例色块 %d：%s 的代表色。**说明**：色板（palette.json，M1 独占）无粉色键，"
            "GOOD END 的粉色方框以 @palette.text_name（暖色）近似，已作为**色板缺口**登记进报告；"
            "其余三色分别取 accent（浅蓝）/ edge_line（银灰）/ node_available（亮蓝），与方框实际色调对应。"
            % (k + 1, BOX_CN[bt]), z=93))
        els.append(txt(
            "flow.lg%d_tx" % (k + 1), 114, 960 + k * 28, 650, 28, 19, C_HINT_LT,
            "%d. %s" % (k + 1, BOX_CN[bt]),
            "图例文字 %d：四种方框各配一行中文说明（用户 2026-09-20 定义，从上到下顺序一致）。"
            "字号 19 → 最长一行 28 字实测 394 px < 650 px，不溢出面板。"
            "对应的 PNG 文件名写在 flow.%s_box 的 note 里，不占图例版面。"
            % (k + 1, ["n01", "n10", "b01", "n04"][k]), align="left", valign="middle", z=94))

    els.append(txt(
        "flow.detail", 800, 958, 420, 110, 19, C_HINT_LT,
        "当前节点：N01 前奏诗·框架剧与四短篇\n已读 1 / 13 节点",
        "节点详情/提示行（运行期由 ui_flow.tjs 改写：当前节点、已读计数、未解锁原因）。"
        "x=800 w=420（图例面板右边界 780 + 20 留白；右边界 1220 < 返回键 1548）——"
        "M14 原为 w=330，实测最长一行「当前节点：N01 前奏诗·框架剧与四短篇」会折行并把"
        "「四短篇」拆成「四短/篇」，故加宽到 420（该行约 300 px，420 下不折）。",
        align="left", valign="top", wrap=True, max_lines=4, line_spacing=1.2, z=95))
    els.append(hit(
        "flow.hit_back", 1548, 990, 310, 64, "close", "返回",
        "返回键（action=close，由 M2 界面栈弹栈）。", z=96, size=27, color=C_TEXT_LT))

    note = (
        "**M18 改造（2026-09-20）**：流程图由 M14 的「纵向长图 + 视口滚动（4 页、一屏约见 3 个节点）」"
        "改为**单屏总览**：13 个节点按 **2 列 × 7 行**（列优先填充）全部落在一屏内，**无需滚动**。\n\n"
        "★ **为什么可以缩放（主代理授权）**：M14 不缩放的理由是「image 的 w/h 必须等于 PNG 实尺寸」，"
        "但 `_schema.md` §六 明文允许 `nine:{l:0,t:0,r:0,b:0}` 表达「整图等比缩放」"
        "（`uiWidgetNine` 在 l=t=r=b=0 时只画中格 ⇒ 等价整图缩放；`verify_ui.py` 检查 [2] 对带 nine 的 image "
        "只要求 w ≥ l+r、h ≥ t+b，全零恒成立）。主代理 2026-09-20 授权本屏使用该写法，"
        "故方框从 1152 宽等比缩到 %d 宽（倍率 %s）。\n\n"
        "★ **坐标依据**：视口高 = 页脚带顶 950 − 页眉带底 110 = 840 px；7 行 → 行槽 %d + 行间距 %d = %d px；"
        "方框最高者 goodend 234 px → 缩放上限 112/234 = 0.4786，取 **%s**。"
        "两列左边界 x = %d / %d（2×%d = %d，两侧各留 %d、列间留 %d）。"
        "行槽顶 = %d + 行号 × %d；末行（第 7 行）槽底 = %d ≤ 视口下沿 %d。\n\n"
        "★ **连线（单屏下的简化）**：① 同列相邻节点用纵向连接条（flow.seq01…seq11）；"
        "② 跨列用三段折线 flow.wrap_a/b/c（N05 → N06，走列间空隙的纵向通道 x=%d）；"
        "③ 真实边 E02（N01→N03，同列跨一行）用左侧旁路 flow.e02_a/b/c 表达；"
        "④ 五线汇入 s04 用列间空隙中线 x=%d 的汇流总线 flow.bus_c + 四条短横条表达"
        "（N07→N09 与 N09 同列相邻，由 seq09 表达，不进总线）。\n\n"
        "★ **已知信息损失（如实登记）**：**E04（N03→N05）与 E05（N03→N06）两条跨行边不再有屏上元素**"
        "（`els` 为空数组）——它们在 2×7 网格里要横跨 3–4 行，画出来会与总线/续接线大量交叠；"
        "M14 的 `bus_a`（N03 之后三条平行线的汇流）同样无法表达，`el` 置空串。"
        "**拓扑本身完整保留在 复刻\\flow_data.js / krkr\\game\\ui_flow_data.tjs 的 edges[] / buses[] 里**"
        "（供编程组与数据对账），只有屏上元素做了简化。相比 M14，本次**多表达了一条真实边 E02**"
        "（M14 纵排时 E02 也归为损失），且汇流总线的源从「按行近似」改为「按节点精确取四条短横条」。\n\n"
        "★ **节点 → 方框类型判定表**（依据 spine.json acts[].note + 资源组\\01_剧情流程图.md §五 结局矩阵）：\n"
        "   一般剧情（_1_normal）  ：N01 前奏诗·框架剧与四短篇 / N02 前奏诗·系统脚本 / N03 本篇·序文 / N11 涅布＊プラス 明日香篇\n"
        "   BAD END（_2_badend）  ：N10 After Story·主线（幕内含 24_5c「Ｂ－ＥＮＤ」，亦含 24_5b「Ｇ－ＥＮＤ」）\n"
        "   重要章节（_3_important）：B01 分歧点 ot_s01_02c / B02 分歧点 s03_09a（关键分歧点，影响后续剧情发展）\n"
        "   GOOD END（_4_goodend） ：N04 s01 鹰志线 / N05 s02 鹫介线 / N06 s03 隼人线 / N07 亚衣线 s03c / "
        "N08 PSV 美咲线 / N09 大路线 s04（真 END）\n"
        "   逐条判定理由写在每个 `_box` 元素的 note 与 工具\\gen_flow_data.py 的 NODE_BOX 中。\n\n"
        "★ **可读性取舍**：方框缩到 %d×%d 后标签字号取 %d（实测最长行 311 px ≤ 可用宽 %d px）。"
        "窗口按 setZoom(2,3) 呈现 1280×720 时，%d 号字约合屏幕 14.7 px —— 与正文小字同级，"
        "可辨但不再是「大字标题」。这是「一屏看全」必然付出的代价，已实测登记（见 _工作\\M18_报告.md）。\n\n"
        "★ 配色：方框图为浅色 → 节点文字用色板深色键 @palette.node_locked（未解锁时运行期改写为 "
        "@palette.text_disabled）；页眉/页脚带为黑底，其上文字仍用浅色键。**未新增 palette 键**。"
        "生成器：_工作\\M14_gen_screens.py（幂等可复跑）。"
        % (FLOW_BOX_W, FLOW_SCALE, FLOW_SLOT_H, FLOW_ROW_GAP, FLOW_ROW_PITCH, FLOW_SCALE,
           FLOW_COL_X[0], FLOW_COL_X[1], FLOW_BOX_W, FLOW_BOX_W * 2, FLOW_COL_X[0],
           FLOW_COL_X[1] - (FLOW_COL_X[0] + FLOW_BOX_W), FLOW_TOP, FLOW_ROW_PITCH,
           FLOW_TOP + 6 * FLOW_ROW_PITCH + FLOW_SLOT_H, FLOW_FTR_Y,
           FLOW_WRAP_X, FLOW_BUS_X,
           FLOW_BOX_W, BOX_H_S["goodend"], FLOW_LABEL_FS, FLOW_LABEL_W, FLOW_LABEL_FS)
    )
    return {"id": "flowchart", "title_cn": "剧情流程图", "owner": "M4",
            "note": note, "elements": els}


# ── 输出 ────────────────────────────────────────────────────────────
def selfcheck(obj):
    """生成后自检（M18 新增）：正尺寸 + 节点互不重叠 + 全屏元素落在画布内。
    返回错误清单（空 = 通过）。流程图屏的连线/色环允许与方框交叠（设计如此），
    故重叠检查只做「方框 vs 方框」「色环 vs 色环」两组。"""
    errs = []
    els = obj["elements"]
    by = {}
    for e in els:
        by[e["id"]] = e
        if e["kind"] in ("rect", "image", "text", "hit"):
            if e.get("w", 0) <= 0 or e.get("h", 0) <= 0:
                errs.append("%s：非正尺寸 w=%s h=%s" % (e["id"], e.get("w"), e.get("h")))
            x, y, w, h = e.get("x", 0), e.get("y", 0), e.get("w", 0), e.get("h", 0)
            # 带 nine 的 image 允许越出画布（透明边距，见 _schema.md §六）
            if e["kind"] != "image":
                if x < 0 or y < 0 or x + w > 1920 or y + h > 1080:
                    errs.append("%s：越出画布 (%d,%d,%d,%d)" % (e["id"], x, y, w, h))

    def ov(a, b):
        return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                    or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])

    for suffix, label in (("_box", "方框"), ("_fill", "三态色环")):
        g = [e for e in els if e["id"].endswith(suffix)]
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if ov(g[i], g[j]):
                    errs.append("%s 重叠：%s ↔ %s" % (label, g[i]["id"], g[j]["id"]))
    return errs


def dump(name, obj):
    p = os.path.join(SCREENS, name)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2))
        f.write("\n")
    n = len(obj["elements"])
    size = os.path.getsize(p)
    print("[OK] %-20s 元素 %3d ｜ %6d 字节" % (name, n, size))
    errs = selfcheck(obj)
    if errs:
        print("     [FAIL] 自检未通过：")
        for e in errs:
            print("        - " + e)
    else:
        print("     [OK]   自检通过（正尺寸 / 节点不重叠 / 元素在画布内）")
    return errs


def main():
    bad = 0
    bad += len(dump("31_fragment.json", build_fragment()))
    bad += len(dump("27_gallery.json", build_gallery()))
    bad += len(dump("32_flowchart.json", build_flowchart()))
    if bad:
        print("[FAIL] 三屏自检共 %d 处问题（见上）" % bad)
    else:
        print("[OK] 三屏已生成且自检通过（下一步：cd ../工具 && python gen_layout.py && python verify_ui.py）")


if __name__ == "__main__":
    main()