# -*- coding: utf-8 -*-
r"""m57_make_state_assets.py · 未解锁压暗件（随形 alpha ×3）＋ 已读对勾件（×2）
                             —— 程序化生成（**5 件**，件名与尺寸冻结）

Issue : **ISSUE-20260928-03**（「未解锁压暗件方角修复 + 已读绿对勾」）
上一轮 : `ISSUE-20260928-02` 第 2 步（接口冻结 `_工作\ISSUE-20260928-02_第2步\接口冻结.md`
         §一.1 表 `locked` 行 / §四.4）。**本轮是该接口的两处修正**（见下「修什么」）。
参照脚本 : `_工作\ISSUE-20260928-02_素材\复现脚本\m55_make_flow_assets.py` /
         `m56_make_fragtitle_bg.py`（照其写法：程序化合成 + 逐件断言 + 幂等 + 变异自证 + 证据）

■■ 修什么（真实缺陷，2026-09-28 实测坐实）
------------------------------------------------------------------
① **未解锁压暗件是方角矩形**：`fc.node.<NNNN>_dim` 现为 `kind:"rect"`（284×48 / `#000000` /
   `opacity:110` / 落在节点可见实体面 `x+6,y+8`）—— 而节点底图**四角是半径 16 的圆弧、圆弧外透明**，
   方角矩形的四个角压在**背景**上、把背景也压暗 ⇒ 四角各露出一块约 55–70px 的暗方角
   （locked 节点在方角处实测 (8,10,13) vs 同型 available 节点 (15,18,24)）。
② **缺「已读（visited）」的视觉记号**：`flow_state=="visited"` 现无任何叠加件
   （§一.1 表只给了 `locked`/`new` 的叠加件与 `current` 的程序化环）。

修法（已定，本轮只产素材；数据层接线由另一代理并行完成）
  ① 压暗件**逐像素跟随底图轮廓** —— 从每类节点底图件**派生**（RGB 全 0 ＋
     **alpha 与源件逐像素相等**），元素改成 `kind:"image"`（与底图**同几何同 `nine`**），
     强度仍由元素 `opacity` 控制（现值 110）。⇒ 压暗的支撑集 ≡ 底图支撑集，
     **背景一个像素都不被压**（这正是「圆角完全贴合、无方角」的可机检表述）。
  ② 新增**已读对勾件**（绿底白勾），接线后作 `fc.node.<NNNN>_read` 一类叠加件。

■■ 交付物（5 件；`krkr\assets\ui\`，**件名与尺寸冻结，不得改**）
------------------------------------------------------------------
    x_ui_node_section_dim.png   236×65   RGB 全 0，alpha ≡ `x_ui_node_section_off.png`
    x_ui_node_select_dim.png    263×65   RGB 全 0，alpha ≡ `x_ui_node_select_off.png`
    x_ui_node_frag_dim.png      228×65   RGB 全 0，alpha ≡ `x_ui_node_frag_off.png`
    x_ui_read_check.png          20×20   **主版**：深绿实心小圆牌（Ø18 居中，`#255E34`）
                                          ＋ 白色对勾字形；真 alpha、硬边、无渐隐边
    x_ui_read_check_alt.png      20×20   **备选版**：绿对勾字形（同色 `#255E34`）＋ 白色 1px 描边、透明底

  ★ 三件 dim 的尺寸**必须与源件相等**（下游 `nine` 要沿用源件口径，`t=b=0` 要求源高 == 元素高 65）；
    **不得缩放 / 不得重绘轮廓**；alpha 逐像素 `src == dim`（脚本内断言）。
  ★ dim 件取 `_off` 版源件（非 `_on`）：压暗是「未解锁」记号，与悬停态无关；且数据层元素
    用的就是 `x_ui_node_*_off.png` 作底图（`layout\screens\32_flowchart.json` 实测）。

■ 圆角随形的**九宫格**（读自 `layout\screens\32_flowchart.json`，本脚本只读该屏数据）
    section `{l:14,t:0,r:16,b:0}` ｜ select `{l:14,t:0,r:13,b:0}` ｜ frag `{l:14,t:0,r:15,b:0}`
    ⇒ dim 件与底图**同 `nine`、同元素矩形 296×65**；由于 alpha 逐像素相同，拉伸后二者
      支撑集**逐像素重合**（本脚本按落盘 `nine` 真拉一遍做断言，不是纸上推导）。

■ 对勾件取色（★ **一审打回修复：适用范围** —— 判据必须对**三种节点面同时**成立）
    **缺陷**：对勾**永远画在节点面左上角**，而三类节点的可见实体面颜色不同
    （section 浅蓝 / select 中蓝 / frag 浅紫）——上一版按**单面** `#C4D7F6` 把绿压到 `#3F8A5A`，
    对 select 面只有 **1.71:1**、对 frag 面 **2.32:1**；`states` 演示档恰好把 3 个 `visited`
    全排在 section 节点 ⇒ 演示图上看不出来，真实数据里 visited 落到 select/frag 就会显形。
    **修法（数值求解，不试色）**：
      · 面值取两组 —— **交付清单给定色**（section `#C4D7F6` / select `#61AED6` / frag `#D3B3F8`）
        ＋ **底图件实测中位色**（α≥250 实体逐通道中位：`#C3D6F4` / `#60ACD4` / `#D2B2F6`）。
      · 绑定面 = 最暗的 **select**（实测 L 0.36745 / 给定 L 0.37669）
        ⇒ `T=3.0` 的亮度上界 `L ≤ (0.36745+0.05)/3 − 0.05 = 0.089151`；取上界 ×0.97 = **0.086477**。
      · 在「HSL 色相 ∈ [110,155]° 且 饱和度 ∈ [0.60,0.85]」内穷举整数 RGB 取 **L 最大**者
        （＝约束边界上最亮的绿），同 L 并列取色相最接近 palette 原值 133.7° 者
        ⇒ **`#255E34`**（色相 **135.8°** / 饱和 0.606 / L 0.08647）。
      · 实测（底图实测中位面 / 给定面 两组↔三面）：
          section **5.219 / 5.275** ｜ select **3.059 / 3.127** ｜ frag **4.191 / 4.240**
          ⇒ **三面全部 ≥3.0**（硬门槛 2.5 ✅，目标 3.0 ✅）；最差面（select）**3.059**。
      · 白勾对绿牌 **7.694:1**（目标 ≥4.5 ✅）。
      · 色相 135.8° ∈ [110,155] ⇒ 仍是「绿」（非墨绿黑）。
      · 求解器：`复现脚本\m57_solve_green.py`（穷举 256³ + 明写选定规则 ⇒ 可复现、可复核）。
    **备选版**：勾绿取**同一值**（同一条判据一并满足 → 三面同样达标）；
      但其**白 1px 描边在浅色节点面上只有 1.46:1，不起轮廓作用** ——
      ⇒ **备选件在浅色节点面上完全靠「勾绿与面的对比」成立**（已如实登记）。
      两版均**不新增 palette 键**（色值烘进 PNG；`layout\**` 属禁止触碰区，本脚本**只读**）。

■ 对勾字形（程序化、确定性；**不烘焙任何文字 / 除字形描边以外的装饰**）
    · 折线三点（画布连续坐标，20×20）：`(5.6,10.4) → (8.8,13.6) → (14.4,6.8)`，笔宽 2.2px。
      臂长比 ≈1:1.93（常见对勾比例），字形（含笔宽）落在半径 9 的圆牌内、四周留 ≥2.4px 余量。
    · 笔形 = **逐段平行四边形 ＋ 关节/端点圆**（圆端帽 / 圆接合）⇒ 不依赖字体、不依赖绘图库的
      line-joint 实现（不同 Pillow 版本表现不一）⇒ 完全确定性。
    · 主版合成：`RGB = mix(牌绿, 白, 字形覆盖率)`、`alpha = 圆牌掩膜`（**alpha 完全由圆牌决定**
      ⇒ 字形不可能把不透明度带到牌外）。
    · 备选版合成：`RGB = mix(白, 绿, 字形覆盖率)`、`alpha = 外扩 1px 描边掩膜`（透明底）。
    · 抗锯齿口径：**SSAA ×8 ＋ BOX 降采样 = 精确面积覆盖率**（硬边、1px 过渡带、无振铃）。
      ⚠️ 不用 LANCZOS：其 3σ 核在 8× 降采样下过渡带宽达数像素（本件实测最大径向偏差 2.48px）
      ⇒ 会构成真实存在的「渐隐带」，正是硬要求要避免的东西。

■ 幂等
    · 纯程序化：**无随机、无时间戳、无网络、无 AI 生图**；只读 palette.json 与三件源 PNG 的
      **像素**（dim 必须逐像素相等 ⇒ 只能读源件；读的是「素材输入」而非「生成器产物」）。
    · 同版本重跑**逐字节一致**；脚本自证「同进程连造两次字节相同 ＋ 与磁盘现值比对（写前）」。

■ 断言非空转（**6 族变异**，全部 `write=False`、不写任何资产）
    M1 dim alpha ＋1                        ⇒ alpha 逐像素相等断言报错
    M2 对勾画布/牌径改 21                    ⇒ 尺寸断言报错
    M3 dim RGB 改成 (1,1,1)                  ⇒ RGB 全 0 断言报错
    M4 绿牌调回上一版 `#3F8A5A`              ⇒ **「select 面不达标」报错**（正是本次一审的缺陷）
    M4b 绿牌用 palette 原值 `#5AA06A`        ⇒ 三面全不达标
    M5 dim alpha 改成「源 alpha 的**外接矩形**填充」（＝方角矩形的等价物）
                                            ⇒ **角落断言报错**（证明该断言对本次真实缺陷非空转）

■ 依赖：Pillow、numpy。本机实测：Pillow 12.3.0 / numpy 2.5.3。

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python "_工作/ISSUE-20260928-03_素材/复现脚本/m57_solve_green.py"                 # 绿牌数值求解
    python "_工作/ISSUE-20260928-03_素材/复现脚本/m57_make_state_assets.py"            # 产出 + 自证
    python "_工作/ISSUE-20260928-03_素材/复现脚本/m57_make_state_assets.py" --dry-run  # 只自证，不写盘
    python "_工作/ISSUE-20260928-03_素材/复现脚本/m57_evidence.py"                      # 独立回读 + 证据图
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-03_素材", "证据")

# ══════════════════════════════════════════════════════════════════ 冻结常量
# (源件, 产出件, 源尺寸＝产出尺寸, nine<读自 32_flowchart.json 的节点元素>)
NODE_SRC = [
    ("x_ui_node_section_off.png", "x_ui_node_section_dim.png", (236, 65),
     {"l": 14, "t": 0, "r": 16, "b": 0}),
    ("x_ui_node_select_off.png", "x_ui_node_select_dim.png", (263, 65),
     {"l": 14, "t": 0, "r": 13, "b": 0}),
    ("x_ui_node_frag_off.png", "x_ui_node_frag_dim.png", (228, 65),
     {"l": 14, "t": 0, "r": 15, "b": 0}),
]
NODE_DESIGN_W, NODE_DESIGN_H = 296, 65     # 节点元素矩形（nine 拉伸后）
DIM_OPACITY = 110                          # 元素 opacity 现值（冻结书 §一.1 locked 行）
OLD_RECT = (6, 8, 284, 48)                 # 旧 `kind:"rect"` 的矩形（可见实体面）——仅作对照
NODE_FACE_R = 16.0                         # 节点可见实体面的圆角半径（用户 2026-09-27 裁决）
# 旧做法的「方角」几何面积：圆角切掉的那块 = r² − πr²/4（每角 55.02 px，四角 220.1 px）
CORNER_CUT_THEORY = NODE_FACE_R ** 2 - math.pi * NODE_FACE_R ** 2 / 4.0

CK_NAME = "x_ui_read_check.png"
CK_ALT_NAME = "x_ui_read_check_alt.png"
CK_W = CK_H = 20                           # 尺寸冻结
CK_CX = CK_CY = CK_W / 2.0                 # 圆心（连续坐标＝画布中心）
CK_R = 9.0                                 # 圆牌半径（直径 18，居中，四边各留 1px）
CK_STROKE = 2.2                            # 对勾笔宽
CK_PTS = ((5.6, 10.4), (8.8, 13.6), (14.4, 6.8))
CK_OUTLINE_W = 1.0                         # 备选版白描边宽

# ★ 一审打回修复（适用范围）：对勾**永远画在节点面左上角**，而三类节点的可见实体面颜色**不同**
#   ⇒ 「对某一面达标」不成立；判据必须**对三面同时**成立。
#   面值取两组：**交付清单给定色** ＋ **底图件实测中位色**（α≥250 实体的逐通道中位），
#   对照度断言对**两组都算**（取更苛刻者）。
FACE_GIVEN = {"section": (0xC4, 0xD7, 0xF6), "select": (0x61, 0xAE, 0xD6),
              "frag": (0xD3, 0xB3, 0xF8)}
FACE_SRC = {"section": "x_ui_node_section_off.png", "select": "x_ui_node_select_off.png",
            "frag": "x_ui_node_frag_off.png"}
FACE_CN = {"section": "章节点", "select": "选择支", "frag": "番外"}

SS = 8                                     # 超采样倍率（BOX 降采样 ⇒ 精确覆盖率，1/64 级）
CK_BAND = 1.15                             # 「硬边」判据：过渡带半宽上限（px）
CK_CORE_ALPHA = 250                        # 「不透明核心」阈值
CK_CORE_COV_MIN = 45.0                     # 核心覆盖率下限 %（硬边理论 ≈ π·8²/400 = 50.3%）
CK_ZERO_COV_MIN = 20.0                     # α=0 占比下限 %（硬边理论 ≈ 1 − π·10²/400 = 21.5%）
CONTRAST_GLYPH_MIN = 4.5                   # 白勾对绿牌 ≥4.5:1（一审抬高的目标）
CONTRAST_PLATE_MIN = 2.5                   # 绿牌对**每一面** ≥2.5:1（硬判据）
CONTRAST_PLATE_GOAL = 3.0                  # 争取对**最差面** ≥3.0:1
HUE_LO, HUE_HI = 110.0, 155.0              # 「仍是绿」：HSL 色相区间（不得变墨绿黑）

PAL = json.load(open(PALETTE, encoding="utf-8"))["colors"]


# ══════════════════════════════════════════════════════════════════ 调色板 / 对比度
def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    """@palette.<key> → (r,g,b)。缺键即报错，不做静默回落。"""
    if key not in PAL:
        raise KeyError("palette.json 缺键：%s" % key)
    return hex2rgb(PAL[key]["value"])


def hexof(rgb):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb)


def _lin(c):
    c = float(c) / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(rgb):
    r, g, b = (_lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG 相对亮度对比度（1..21）"""
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


GREEN_PAL = C("node_visited")               # #5AA06A（palette 原值；对分节点面无一面达标）
GREEN_PREV = (0x3F, 0x8A, 0x5A)             # #3F8A5A（上一版：按**单面** #C4D7F6 选的 —— 已作废）
# ★ 本版绿牌 = **数值求解**所得（脚本 `m57_solve_green.py`，非试色）：
#   绑定面 = 三面中最暗者 `select`（底图实测中位 #60ACD4 / L 0.36745；给定 #61AED6 / L 0.37669）
#   ⇒ T=3.0 的亮度上界 L ≤ 0.089151，取上界 ×0.97 = 0.086477；
#   在「HSL 色相 ∈ [110,155]° 且 饱和度 ∈ [0.60,0.85]」内取 **L 最大**（边界上最亮的绿），
#   同 L 并列取色相最接近 palette 原值 133.7° 者 ⇒ **#255E34**（色相 135.8° / 饱和 0.606 / L 0.08647）。
#   实测：三面 5.219 / 3.059 / 4.191（section/select/frag，门槛 2.5、目标 3.0 全部达成）、
#        白勾对绿牌 7.694（≥4.5）。
SOLVED_GREEN = (0x25, 0x5E, 0x34)
CK_PLATE = SOLVED_GREEN                     # 主版圆牌绿（最终）
CK_ALT_GREEN = SOLVED_GREEN                 # 备选版对勾绿（同一条判据；见文件头「取色」）
CK_GLYPH = (255, 255, 255)                  # 白勾（主版）／白描边（备选版）


_FACE_CACHE = {}


def face_colors():
    """两组面值：`given`（交付清单给定色）／`med`（底图件实测中位色）。带缓存。"""
    if not _FACE_CACHE:
        _FACE_CACHE["given"] = dict(FACE_GIVEN)
        med = {}
        for k, fn in FACE_SRC.items():
            a = np.asarray(Image.open(os.path.join(OUT, fn)).convert("RGBA")).astype(np.int64)
            sel = a[:, :, 3] >= 250
            med[k] = tuple(int(np.median(a[:, :, i][sel])) for i in range(3))
        _FACE_CACHE["med"] = med
    return _FACE_CACHE


def plate_contrasts(rgb, faces=None):
    """绿牌对三面的对比度：返回 {面: (实测中位面值, 给定面值)}"""
    f = faces or face_colors()
    return {k: (contrast(rgb, f["med"][k]), contrast(rgb, f["given"][k])) for k in FACE_GIVEN}


def hue_of(rgb):
    """HSL 色相（度）"""
    r, g, b = (v / 255.0 for v in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0
    if mx == r:
        h = 60.0 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60.0 * ((b - r) / d + 2)
    else:
        h = 60.0 * ((r - g) / d + 4)
    return h % 360.0


# ══════════════════════════════════════════════════════════════════ 基础工具
def split_scale(size):
    """(w,h) → scale（相对 20×20 的等比）—— 仅变异自证用（画布 21×21）"""
    return size[0] / float(CK_W)


def disc_mask(size, sub=SS):
    """圆牌掩膜 —— **解析覆盖率**（每 1× 像素用 sub×sub 子样本点做「在圆内」判测 → 覆盖比例）。

    ⚠️ 不用 `ImageDraw.ellipse`：其光栅化会把圆弧最外一列/行并进画布**最外 1px 帧**
      （实测 bottom / right 各 3 px、α≤32），而下批判据要求「最外 1px 帧 α 只允许圆角的抗锯齿」
      （本件是纯圆 ⇒ 该帧应恒 0）。解析式按几何精确定位，且**四边严格对称**。"""
    w, h = size
    k = w / float(CK_W)
    cx, cy, r = CK_CX * k, CK_CY * k, CK_R * k
    ys = (np.arange(h)[:, None] + (np.arange(sub) + 0.5) / sub).reshape(-1)
    xs = (np.arange(w)[:, None] + (np.arange(sub) + 0.5) / sub).reshape(-1)
    ins = (((ys - cy) ** 2)[:, None] + ((xs - cx) ** 2)[None, :]) <= r * r
    cov = ins.reshape(h, sub, w, sub).mean(axis=(1, 3)) * 255.0
    return Image.fromarray(np.clip(np.round(cov), 0, 255).astype(np.uint8), "L")


def poly_stroke_mask(size, pen_w, scale=SS):
    """圆头折线掩膜（笔宽 `pen_w`，px）：逐段**平行四边形** ＋ 关节/端点**圆**。

    不依赖字体、不依赖 `ImageDraw.line` 的 joint（不同 Pillow 版本表现不一）⇒ 完全确定性。
    降采样用 **BOX**（精确覆盖率）⇒ 边缘 1px 过渡、无 LANCZOS 振铃。"""
    w, h = size
    k = w / float(CK_W)
    pts = [(x * k, y * k) for (x, y) in CK_PTS]
    hw = pen_w * k / 2.0

    def _d(d):
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
            nx, ny = -uy * hw, ux * hw
            d.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                       (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=255)
        for (x, y) in pts:
            d.ellipse([x - hw, y - hw, x + hw, y + hw], fill=255)

    m = Image.new("L", (w * scale, h * scale), 0)
    d = ImageDraw.Draw(m)
    _d(_Scaler(d, scale))
    return m.resize((w, h), Image.BOX)


class _Scaler(object):
    """把绘制坐标整体放大 scale 倍（只用 polygon / ellipse 两个接口）"""

    def __init__(self, d, s):
        self._d, self._s = d, s

    def polygon(self, pts, fill):
        self._d.polygon([(x * self._s, y * self._s) for (x, y) in pts], fill=fill)

    def ellipse(self, box, fill):
        self._d.ellipse([v * self._s for v in box], fill=fill)


def merge_rgb_alpha(rgb, alpha):
    """(r,g,b) 常值 ＋ alpha（L 掩膜）→ RGBA（RGB 逐像素常值 ⇒ 编码极省、且 α=0 处也写该值）"""
    a = alpha if isinstance(alpha, Image.Image) else Image.fromarray(
        np.asarray(alpha, dtype=np.uint8), "L")
    w, h = a.size
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, :] = np.asarray(rgb, dtype=np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    im.putalpha(a)
    return im


def blend_rgb(base_rgb, over_rgb, cov):
    """RGB 线性混合：`out = over×cov + base×(1−cov)`（cov 为 0..255 掩膜）"""
    c = np.asarray(cov, dtype=np.float64)
    if c.max() > 1.0:
        c = c / 255.0
    base = np.asarray(base_rgb, dtype=np.float64).reshape(1, 1, 3)
    over = np.asarray(over_rgb, dtype=np.float64).reshape(1, 1, 3)
    return np.clip(np.floor(c[..., None] * over + (1.0 - c[..., None]) * base + 0.5),
                   0, 255).astype(np.uint8)


def flat(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def frame_max(im, n=1):
    """最外 n px 帧的 α 最大值（n=0 ⇒ 0）"""
    if n <= 0:
        return 0
    a = np.asarray(im.getchannel("A"))
    return int(max(a[:n, :].max(), a[-n:, :].max(), a[:, :n].max(), a[:, -n:].max()))


def stats_of(im):
    arr = np.asarray(im).reshape(-1, 4)
    al = arr[:, 3]
    nz = arr[al > 16]
    cnt = Counter(map(tuple, nz[:, :3].tolist()))
    top, topn = (cnt.most_common(1)[0] if cnt else ((0, 0, 0), 0))
    return dict(amin=int(al.min()), amax=int(al.max()),
                zero_cov=round(100.0 * float((al == 0).sum()) / len(al), 4),
                core_cov=round(100.0 * float((al >= CK_CORE_ALPHA).sum()) / len(al), 4),
                cov=round(100.0 * len(nz) / len(arr), 2),
                top=hexof(top), topn=int(topn))


def nine_stretch(src, w, h, nine):
    """九宫格拉伸（与引擎 `uiWidgetNine` 同口径：四边 1:1、中格拉伸）。
    本批 `t=b=0` ⇒ 纵向 1:1（源高 == 元素高 65）。中格用 NEAREST；角块恒 1:1 原样贴
    ⇒ 角部几何不受重采样影响。"""
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    sw, sh = src.size
    dst = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs_s, xs_d = [0, l, sw - r, sw], [0, l, w - r, w]
    ys_s, ys_d = [0, t, sh - b, sh], [0, t, h - b, h]
    for i in range(3):
        for j in range(3):
            sx0, sx1, dx0, dx1 = xs_s[j], xs_s[j + 1], xs_d[j], xs_d[j + 1]
            sy0, sy1, dy0, dy1 = ys_s[i], ys_s[i + 1], ys_d[i], ys_d[i + 1]
            if sx1 <= sx0 or sy1 <= sy0 or dx1 <= dx0 or dy1 <= dy0:
                continue
            piece = src.crop((sx0, sy0, sx1, sy1))
            if piece.size != (dx1 - dx0, dy1 - dy0):
                piece = piece.resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            dst.paste(piece, (dx0, dy0))
    return dst


def opacity_layer(img, opa):
    """元素 `opacity` 语义：α ← round(α × opa/255)"""
    out = img.copy()
    out.putalpha(out.getchannel("A").point(lambda v: (v * opa + 127) // 255))
    return out


def premul(arr):
    """α 预乘（int32）：**视觉上真正可比**的像素表示。

    ⚠️ 必须用它而不是裸 RGB 比较：RGBA 图的 α=0 处**仍可携带非零 RGB**（PNG 允许），
      合成后该处 RGB 会变成 0 ⇒ 裸比 RGB 会把「两边都完全透明」误判成「画面变了」
      （本轮实测踩到：假阳性 264 px 与对照组同数）。"""
    a = arr[:, :, 3:4].astype(np.int32)
    return np.concatenate([arr[:, :, :3].astype(np.int32) * a // 255, a], axis=2)


_QUIET = [False]


def say(*a):
    """报告输出（变异自证时静音，避免 5 份报告刷屏）"""
    if not _QUIET[0]:
        print(*a)


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


# ══════════════════════════════════════════════════════════════════ ① 压暗件
def build_dim(src_img, mutate=None):
    """从节点底图派生压暗件：**RGB 全 0 ＋ alpha ≡ 源件 alpha**。

    `mutate`（仅供变异自证，生产恒 None）：
      "alpha_plus1" —— alpha 全部 +1（应被 alpha 逐像素断言拦下）
      "rgb1"        —— RGB 写 (1,1,1)（应被 RGB 全 0 断言拦下）
      "bbox"        —— alpha 改成「源 alpha 支撑集的外接矩形」填充（＝**方角矩形的等价物**，
                       应被角落断言拦下）
    """
    src = src_img.convert("RGBA")
    a = np.asarray(src.getchannel("A")).astype(np.int16)
    if mutate == "alpha_plus1":
        a = np.clip(a + 1, 0, 255)
    elif mutate == "bbox":
        sup = a > 0
        ys, xs = np.nonzero(sup)
        hull = np.zeros_like(sup)
        hull[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
        a = np.where(hull, 255, a)
    rgb = 1 if mutate == "rgb1" else 0
    return merge_rgb_alpha((rgb, rgb, rgb), Image.fromarray(a.astype(np.uint8), "L"))


# ══════════════════════════════════════════════════════════════════ ② 已读对勾件
def build_read_check(size=(CK_W, CK_H), plate_rgb=None, mutate=None):
    """主版 · 20×20 · 绿实心小圆牌（Ø18 居中）+ 白色对勾；真 alpha、硬边、无渐隐边。

    · `alpha` **完全由圆牌掩膜决定** ⇒ 字形无论多宽都不可能把不透明度带到牌外。
    · `RGB = mix(牌绿, 白, 字形覆盖率)`：牌是**实心**的，字形抗锯齿在**不透明层内**做 RGB 混合
      ⇒ 边缘锐利、无半透明毛边。
    · 变异：`size=(21,21)`（尺寸断言应报错）；`plate_rgb=#3F8A5A`／`#5AA06A`
      （对三面的对比度门槛断言应报错 —— 见变异 M4/M4b）。
    """
    w, h = size
    k = w / float(CK_W)
    plate = disc_mask(size)
    glyph = poly_stroke_mask(size, CK_STROKE) if mutate != "noglyph" else Image.new("L", size, 0)
    rgb = blend_rgb(plate_rgb or CK_PLATE, CK_GLYPH, glyph)
    im = Image.fromarray(rgb, "RGB").convert("RGBA")
    im.putalpha(plate)
    return im


def build_read_check_alt(size=(CK_W, CK_H), green_rgb=None):
    """备选版 · 20×20 · 绿对勾字形 + 白色 1px 描边、透明底。

    · `alpha` = **外扩 `CK_OUTLINE_W` 的描边掩膜**（＝折线笔宽 `CK_STROKE + 2×OUTLINE`）；
      绿字形与其**逐像素包含**在同一形状内 ⇒ 白描边沿法向恒为 `CK_OUTLINE_W`。
    · `RGB = mix(白, 绿, 字形覆盖率)`：描边区为白、字形核心为绿，字形边缘在不透明区内过渡。
    · 透明底（牌外 α=0），**不烘焙任何装饰**。
    """
    glyph = poly_stroke_mask(size, CK_STROKE)
    outline = poly_stroke_mask(size, CK_STROKE + 2.0 * CK_OUTLINE_W)
    rgb = blend_rgb(CK_GLYPH, green_rgb or CK_ALT_GREEN, glyph)
    im = Image.fromarray(rgb, "RGB").convert("RGBA")
    im.putalpha(outline)
    return im


# ══════════════════════════════════════════════════════════════════ ③ 几何 / 语义读数
def dist_to_polyline(px, py, pts):
    """点 (px,py) 到折线的最短距离（逐段点到线段距离取 min）"""
    best = None
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
        dd = math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
        best = dd if best is None else min(best, dd)
    return best


def shape_field(size, which):
    """每像素的**有符号形状距离** s（>0 在形状内、单位 px）—— 与生成路径无关的独立几何口径。

    which="disc"  ⇒ 圆牌：s = `CK_R` − 到圆心距离
    which="alt"   ⇒ 备选描边形状：s = (`CK_STROKE`/2 + `CK_OUTLINE_W`) − 到折线距离
    """
    w, h = size
    k = w / float(CK_W)
    ys, xs = np.mgrid[0:h, 0:w]
    px, py = xs + 0.5, ys + 0.5
    if which == "disc":
        return CK_R * k - np.hypot(px - CK_CX * k, py - CK_CY * k)
    pts = [(x * k, y * k) for (x, y) in CK_PTS]
    d = np.empty((h, w), dtype=np.float64)
    for j in range(h):
        for i in range(w):
            d[j, i] = dist_to_polyline(px[j, i], py[j, i], pts)
    return (CK_STROKE / 2.0 + CK_OUTLINE_W) * k - d


def hard_edge_report(im, which, band=CK_BAND):
    """「真 alpha、硬边、无渐隐边」的可机检读数（判据对准**独立算出的形状边界**，非生成路径）：

      · `outside_alpha_max` = s ≤ −band 处（形状外 ≥band）的 α 最大值 —— **必须 == 0**（无外晕/渐隐）
      · `inside_alpha_min`  = s ≥ +band 处（形状内 ≥band）的 α 最小值 —— **必须 == 255**（实心无渐隐）
      · `outer_dev` = α>0 的像素里，形状外的最大超出量（= max(−s)）—— ≤ band
      · `inner_dev` = α<255 的像素里，形状内的最大占有量（= max(+s)）—— ≤ band
      ⇒ 过渡带总宽 ≤ 2×band，即「1px 级硬边」。
    """
    a = np.asarray(im.getchannel("A")).astype(np.int64)
    s = shape_field(im.size, which)
    out_m = s <= -band
    in_m = s >= band
    return dict(n_out=int(out_m.sum()), n_in=int(in_m.sum()),
                outside_alpha_max=int(a[out_m].max()) if out_m.any() else 0,
                inside_alpha_min=int(a[in_m].min()) if in_m.any() else 0,
                outer_dev=round(float(max(0.0, (-s[a > 0]).max())) if (a > 0).any() else 0.0, 3),
                inner_dev=round(float(max(0.0, s[a < 255].max())) if (a < 255).any() else 0.0, 3),
                corners=[int(a[0, 0]), int(a[0, -1]), int(a[-1, 0]), int(a[-1, -1])])


def measured_color(im, mask, label, want, tol=0):
    """在掩膜内取「实测唯一色」并核对 —— 返回 (色, 像素数, 是否通过, 说明)"""
    arr = np.asarray(im.convert("RGB"))
    sel = arr[np.asarray(mask) > 0]
    if sel.size == 0:
        return None, 0, False, "%s：掩膜内 0 像素（无法实测）" % label
    cnt = Counter(map(tuple, sel.tolist()))
    col, n = cnt.most_common(1)[0]
    uniq = len(cnt)
    ok = (abs(col[0] - want[0]) <= tol and abs(col[1] - want[1]) <= tol and abs(col[2] - want[2]) <= tol)
    return col, n, ok, ("%s：实测主色 %s ×%d（唯一色种类 %d，期望 %s%s）"
                        % (label, hexof(col), n, uniq, hexof(want),
                           "" if tol == 0 else " ±%d" % tol))


def corner_support_report(node_img, dim_img, nine, old_rect=OLD_RECT, opa=DIM_OPACITY):
    """★ 本次真实缺陷的判据：「压暗件绝不压到底图未覆盖的像素」。

    做法（按**落盘 `nine`** 真拉一遍，不做纸上推导）：
      ① base = nine 拉伸后的底图（296×65）
      ② new  = 拉伸后的 dim 按元素 `opacity` 叠在 base 上
      ③ old  = 旧 `kind:"rect"`（`old_rect` 的 #000000、opacity=opa）叠在 base 上（**对照组**）
    比较用 **α 预乘**（见 `premul` 的注释）。
    读数：
      · `new_outside` / `new_maxdelta_outside` —— 底图 α==0 处的改动像素数 / 最大通道差 ⇒ **必须 0**
      · `old_outside` / `old_maxdelta_outside` —— 同口径对照组 ⇒ **必须 >0**（否则判据空转）
      · `dim_support_mismatch` —— dim 与底图拉伸后 α 不等 的像素数 ⇒ **必须 0**
      · 逐角（24×24）对照读数 —— 用于报告「旧做法四角各露出多少」
    """
    b = nine_stretch(node_img.convert("RGBA"), NODE_DESIGN_W, NODE_DESIGN_H, nine)
    d = nine_stretch(dim_img.convert("RGBA"), NODE_DESIGN_W, NODE_DESIGN_H, nine)
    ba = np.asarray(b.getchannel("A"))
    outside = (ba == 0)

    cont = Image.new("RGBA", b.size, (0, 0, 0, 0))
    old = Image.new("RGBA", b.size, (0, 0, 0, 0))
    x, y, w, h = old_rect
    rect_a = Image.new("L", b.size, 0)
    ImageDraw.Draw(rect_a).rectangle([x, y, x + w - 1, y + h - 1], fill=opa)
    old.putalpha(rect_a)

    new_comp = Image.alpha_composite(Image.alpha_composite(cont, b), opacity_layer(d, opa))
    old_comp = Image.alpha_composite(Image.alpha_composite(cont, b), old)

    pm_n = premul(np.asarray(new_comp))
    pm_o = premul(np.asarray(old_comp))
    pm_b = premul(np.asarray(b))
    dn = np.abs(pm_n - pm_b).max(axis=2)
    do = np.abs(pm_o - pm_b).max(axis=2)

    corners = {}
    for name, (cx0, cy0) in (("TL", (0, 0)), ("TR", (NODE_DESIGN_W - 24, 0)),
                             ("BL", (0, NODE_DESIGN_H - 24)),
                             ("BR", (NODE_DESIGN_W - 24, NODE_DESIGN_H - 24))):
        sl = (slice(cy0, cy0 + 24), slice(cx0, cx0 + 24))
        sel0 = outside[sl]
        soft = (ba < 230)[sl]            # 未成实体（含柔光边）
        part = (ba < 250)[sl]            # 非全不透明
        dirty = (do > 0)[sl]
        corners[name] = dict(old=int((dirty & sel0).sum()),
                             old_max=int(do[sl][sel0].max()) if sel0.any() else 0,
                             old_soft=int((dirty & soft).sum()),
                             old_part=int((dirty & part).sum()),
                             new=int(((dn > 0)[sl] & sel0).sum()))
    return dict(
        canvas="%dx%d" % (NODE_DESIGN_W, NODE_DESIGN_H),
        new_outside=int(((dn > 0) & outside).sum()),
        new_maxdelta_outside=int(dn[outside].max()),
        old_outside=int(((do > 0) & outside).sum()),
        old_maxdelta_outside=int(do[outside].max()),
        old_soft_all=int(((do > 0) & (ba < 230)).sum()),
        old_part_all=int(((do > 0) & (ba < 250)).sum()),
        dim_support_mismatch=int((np.asarray(d.getchannel("A")) != ba).sum()),
        corners=corners,
        base=b, dim=d, new_comp=new_comp, old_comp=old_comp, outside=outside,
        diff_old=(do > 0) & outside,
    )


# ══════════════════════════════════════════════════════════════════ 主流程
def build_all(mutate=None):
    """返回 ([(名字, 期望尺寸, 图, 源件名 or None, 备注)], 源件缓存) —— 顺序即报告顺序"""
    src_cache, out = {}, []
    for src_name, dim_name, size, nine in NODE_SRC:
        src = Image.open(os.path.join(OUT, src_name)).convert("RGBA")
        src_cache[src_name] = (src, size, nine)
        m = mutate if (mutate in ("alpha_plus1", "rgb1", "bbox")
                       and dim_name.endswith("section_dim.png")) else None
        out.append((dim_name, size, build_dim(src, m), src_name,
                    "alpha ≡ %s；nine %s" % (src_name, json.dumps(nine, separators=(",", ":")))))
    out.append((CK_NAME, (CK_W, CK_H),
                build_read_check(size=(21, 21) if mutate == "chk21" else (CK_W, CK_H),
                                 plate_rgb=(GREEN_PREV if mutate == "prevgreen"
                                            else (GREEN_PAL if mutate == "palgreen" else None))),
                None, "绿牌 %s（Ø18 居中）+ 白勾" % hexof(CK_PLATE)))
    out.append((CK_ALT_NAME, (CK_W, CK_H), build_read_check_alt(), None,
                "绿勾 %s + 白 %gpx 描边、透明底" % (hexof(CK_ALT_GREEN), CK_OUTLINE_W)))
    return out, src_cache


def run(write=True, mutate=None, quiet=False):
    _QUIET[0] = quiet
    items, src_cache = build_all(mutate)
    rows, fails, sc = [], [], []

    for name, size, im, src_name, note in items:
        b1 = png_bytes(im)
        it2, _ = build_all(mutate)                       # 幂等：同进程再走一次完整构建
        b2 = png_bytes(next(i[2] for i in it2 if i[0] == name))
        errs = []
        if im.mode != "RGBA":
            errs.append("mode=%s（须 RGBA）" % im.mode)
        if im.size != size:
            errs.append("尺寸 %s ≠ 冻结尺寸 %s" % (im.size, size))
        st = stats_of(im)
        if st["amin"] != 0:
            errs.append("αmin=%d ≠ 0（无真透明）" % st["amin"])
        if st["amax"] != 255:
            errs.append("αmax=%d ≠ 255（无实心像素）" % st["amax"])

        if src_name:                                     # ── 压暗件
            src, _ssize, _nine = src_cache[src_name]
            sa = np.asarray(src.getchannel("A"))
            da = np.asarray(im.getchannel("A"))
            if im.size != src.size:
                errs.append("尺寸 %s ≠ 源件 %s（尺寸必须相等，下游 nine 沿用源件口径）"
                            % (im.size, src.size))
            n_ne = int((da != sa).sum())
            if n_ne:
                errs.append("alpha 与源件不等：%d 个像素不同（max |Δ|=%d）"
                            % (n_ne, int(np.abs(da.astype(int) - sa.astype(int)).max())))
            rgb_max = int(np.asarray(im)[:, :, :3].max())
            if rgb_max != 0:
                errs.append("RGB 最大通道值 %d ≠ 0（须全 0，含 α=0 处）" % rgb_max)
            src_zero = round(100.0 * float((sa == 0).sum()) / sa.size, 4)
            if st["zero_cov"] != src_zero:
                errs.append("α=0 占比 %.4f%% ≠ 源件 %.4f%%" % (st["zero_cov"], src_zero))
            sc.append(("%s：尺寸 == 源件 %s ／ α 与源件逐像素相等（差异 0 px）／ RGB 全 0"
                       % (name, "%dx%d" % src.size), "%dx%d" % im.size, n_ne == 0 and rgb_max == 0))
        else:                                            # ── 对勾件
            which = "disc" if name == CK_NAME else "alt"
            he = hard_edge_report(im, which)
            if he["corners"] != [0, 0, 0, 0]:
                errs.append("四角 α=%s ≠ [0,0,0,0]（画布角在形状外 ≥1.15px）" % he["corners"])
            if he["outside_alpha_max"] != 0:
                errs.append("形状外 ≥%.2fpx 处仍有 α=%d 的像素（存在外晕 / 渐隐带）"
                            % (CK_BAND, he["outside_alpha_max"]))
            if he["inside_alpha_min"] != 255:
                errs.append("形状内 ≥%.2fpx 处仍有 α=%d 的像素（非实心 / 渐隐带）"
                            % (CK_BAND, he["inside_alpha_min"]))
            if max(he["outer_dev"], he["inner_dev"]) > CK_BAND:
                errs.append("过渡带超宽：外 %.3fpx / 内 %.3fpx > %.2fpx"
                            % (he["outer_dev"], he["inner_dev"], CK_BAND))
            sc.append(("%s：硬边——形状外 ≥%.2fpx 处 αmax=%d（==0）／形状内 ≥%.2fpx 处 αmin=%d（==255）／"
                       "过渡带 外%.2fpx+内%.2fpx"
                       % (name, CK_BAND, he["outside_alpha_max"], CK_BAND, he["inside_alpha_min"],
                          he["outer_dev"], he["inner_dev"]), he["outer_dev"] + he["inner_dev"],
                       he["outside_alpha_max"] == 0 and he["inside_alpha_min"] == 255))

            if name == CK_NAME:
                plate_col, plate_n, ok_p, msg_p = measured_color(im, disc_mask(im.size), "牌面", CK_PLATE)
                glyph_col, glyph_n, ok_g, msg_g = measured_color(
                    im, poly_stroke_mask(im.size, CK_STROKE * 0.55), "勾心", CK_GLYPH)
                sc.append((msg_p, hexof(plate_col) if plate_col else "—", ok_p and (plate_n > 120)))
                sc.append((msg_g, hexof(glyph_col) if glyph_col else "—", ok_g and (glyph_n > 6)))
                pc = plate_col or CK_PLATE
                gc = glyph_col or CK_GLYPH
                ct3 = plate_contrasts(pc)
                bad = [(k, m, g) for k, (m, g) in ct3.items()
                       if min(m, g) < CONTRAST_PLATE_MIN]
                if bad:
                    errs.append("实测牌绿 %s 对节点面不达标（<%.1f）：%s"
                                % (hexof(pc), CONTRAST_PLATE_MIN,
                                   "；".join("%s 实测%.3f/给定%.3f" % (k, m, g) for k, m, g in bad)))
                ct2 = contrast(gc, pc)
                if ct2 < CONTRAST_GLYPH_MIN:
                    errs.append("实测白勾对牌绿 = %.3f:1 < %.1f" % (ct2, CONTRAST_GLYPH_MIN))
                hue = hue_of(pc)
                if not (HUE_LO <= hue <= HUE_HI):
                    errs.append("牌绿色相 %.1f° 不在 [%.0f,%.0f]°（已不是「绿」）"
                                % (hue, HUE_LO, HUE_HI))
                worst = min(min(m, g) for m, g in ct3.values())
                sc.append(("实测：牌绿 %s 对三面（实测中位/给定）＝ %s ｜ 最差 %.3f（门槛 %.1f／目标 %.1f%s）"
                           "｜ 白勾对牌绿 %.3f（≥%.1f）｜ 色相 %.1f° ∈ [%.0f,%.0f]"
                           % (hexof(pc),
                              " ／ ".join("%s %.3f/%.3f" % (FACE_CN[k], m, g)
                                          for k, (m, g) in ct3.items()),
                              worst, CONTRAST_PLATE_MIN, CONTRAST_PLATE_GOAL,
                              " 已达成" if worst >= CONTRAST_PLATE_GOAL else " **未达成**",
                              ct2, CONTRAST_GLYPH_MIN, hue, HUE_LO, HUE_HI),
                           round(worst, 3),
                           not bad and ct2 >= CONTRAST_GLYPH_MIN and HUE_LO <= hue <= HUE_HI))
                if worst < CONTRAST_PLATE_GOAL:
                    sc.append(("!! 目标未达成：最差面对比度 %.3f < %.1f（硬门槛 %.1f 仍成立）"
                               % (worst, CONTRAST_PLATE_GOAL, CONTRAST_PLATE_MIN), round(worst, 3),
                               False))
                fr = frame_max(im, 1)
                if fr != 0:
                    errs.append("最外 1px 帧 αmax=%d ≠ 0（圆牌无直边 ⇒ 该帧应全透明）" % fr)
                sc.append(("%s：最外 1px 帧 αmax = %d（圆牌无直边 ⇒ 应为 0）" % (name, fr), fr, fr == 0))
                if st["core_cov"] < CK_CORE_COV_MIN:
                    errs.append("不透明核心(α≥%d)覆盖率 %.4f%% < %.1f%%"
                                % (CK_CORE_ALPHA, st["core_cov"], CK_CORE_COV_MIN))
                if st["zero_cov"] < CK_ZERO_COV_MIN:
                    errs.append("α=0 占比 %.4f%% < %.1f%%" % (st["zero_cov"], CK_ZERO_COV_MIN))
                sc.append(("%s：α=0 占比 %.2f%%（≥%.1f）／ α≥%d 核心占比 %.2f%%（≥%.1f）"
                           % (name, st["zero_cov"], CK_ZERO_COV_MIN, CK_CORE_ALPHA,
                              st["core_cov"], CK_CORE_COV_MIN), st["zero_cov"],
                           st["zero_cov"] >= CK_ZERO_COV_MIN and st["core_cov"] >= CK_CORE_COV_MIN))
            else:
                # 备选版：勾心应为绿、描边带应为白（取「勾心」与「仅描边环带」两块区域实测）
                g_col, g_n, ok_g, msg_g = measured_color(
                    im, poly_stroke_mask(im.size, CK_STROKE * 0.55), "勾心", CK_ALT_GREEN)
                ring = np.asarray(poly_stroke_mask(im.size, CK_STROKE + 2.0 * CK_OUTLINE_W), dtype=np.int16) \
                    - np.asarray(poly_stroke_mask(im.size, CK_STROKE), dtype=np.int16)
                ring = np.clip(ring - 20, 0, 255).astype(np.uint8)
                w_col, w_n, ok_w, msg_w = measured_color(im, Image.fromarray(ring, "L"),
                                                         "描边带", CK_GLYPH)
                sc.append((msg_g, hexof(g_col) if g_col else "—", ok_g and g_n > 6))
                sc.append((msg_w, hexof(w_col) if w_col else "—", ok_w and w_n > 6))
                gc = g_col or CK_ALT_GREEN
                ct3 = plate_contrasts(gc)
                bad = [(k, m, g) for k, (m, g) in ct3.items() if min(m, g) < CONTRAST_PLATE_MIN]
                if bad:
                    errs.append("备选版实测勾绿 %s 对节点面不达标：%s"
                                % (hexof(gc), "；".join("%s 实测%.3f/给定%.3f" % (k, m, g)
                                                        for k, m, g in bad)))
                wc = w_col or CK_GLYPH
                ct_o = contrast(wc, gc)
                if ct_o < CONTRAST_GLYPH_MIN:
                    errs.append("备选版实测白描边对勾绿 = %.3f:1 < %.1f" % (ct_o, CONTRAST_GLYPH_MIN))
                hue = hue_of(gc)
                worst = min(min(m, g) for m, g in ct3.values())
                sc.append(("备选版实测：勾绿 %s 对三面（实测/给定）＝ %s ｜ 最差 %.3f（门槛 %.1f／目标 %.1f%s）"
                           "｜ 白描边对勾绿 %.3f（≥%.1f）｜ 色相 %.1f°"
                           % (hexof(gc), " ／ ".join("%s %.3f/%.3f" % (FACE_CN[k], m, g)
                                                     for k, (m, g) in ct3.items()),
                              worst, CONTRAST_PLATE_MIN, CONTRAST_PLATE_GOAL,
                              " 已达成" if worst >= CONTRAST_PLATE_GOAL else " **未达成**",
                              ct_o, CONTRAST_GLYPH_MIN, hue), round(worst, 3),
                           not bad and ct_o >= CONTRAST_GLYPH_MIN))
                ct_w = {k: (contrast(wc, face_colors()["med"][k]), contrast(wc, face_colors()["given"][k]))
                        for k in FACE_GIVEN}
                worst_w = min(min(m, g) for m, g in ct_w.values())
                sc.append(("备选版：白描边对三面＝%s ｜ 最差 %.3f ⇒ 描边在浅面上**不构成可靠轮廓**"
                           "（section/frag 明确低于 2.5）⇒ 备选件的可辨认性**完全由勾绿承担**"
                           "（勾绿与主版同值 ⇒ 三面同样达标）"
                           % (" ／ ".join("%s 实测%.3f/给定%.3f" % (FACE_CN[k], m, g)
                                          for k, (m, g) in ct_w.items()), worst_w),
                           round(worst_w, 3), True))
                fr = frame_max(im, 1)
                if fr != 0:
                    errs.append("备选版最外 1px 帧 αmax=%d ≠ 0" % fr)

        if b1 != b2:
            errs.append("幂等失败：同进程两次构建字节不同")
        path = os.path.join(OUT, name)
        old_b = open(path, "rb").read() if os.path.exists(path) else None
        rows.append(dict(name=name, size="%dx%d" % im.size, mode=im.mode, bytes=len(b1),
                         amin=st["amin"], amax=st["amax"], zero_cov=st["zero_cov"],
                         core_cov=st["core_cov"], cov=st["cov"], top=st["top"], topn=st["topn"],
                         src=src_name or "—", note=note,
                         idem=("OK" if b1 == b2 else "FAIL"),
                         before=("新增" if old_b is None else ("未变" if old_b == b1 else "改写")),
                         md5=hashlib.md5(b1).hexdigest()))
        if errs:
            fails.append((name, errs))
        elif write:
            im.save(path, "PNG", optimize=True)

    # ── 语义断言：角落随形（按落盘 nine 真拉；dim 用内存图 ⇒ 变异也走同一条路） ──
    dim_section = next(i[2] for i in items if i[0] == NODE_SRC[0][1])
    ck = corner_support_report(src_cache["x_ui_node_section_off.png"][0], dim_section, NODE_SRC[0][3])
    if ck["dim_support_mismatch"] != 0:
        fails.append(("角落随形", ["dim 与底图拉伸后 α 支撑集不重合 %d px" % ck["dim_support_mismatch"]]))
    if ck["new_outside"] != 0 or ck["new_maxdelta_outside"] != 0:
        fails.append(("角落随形", ["压暗件压到底图未覆盖像素 %d 个（最大通道差 %d）⇒ 露方角"
                                  % (ck["new_outside"], ck["new_maxdelta_outside"])]))
    if ck["old_outside"] <= 0:
        fails.append(("角落随形", ["对照组（旧 rect）在底图外 0 个差异像素 ⇒ 判据空转，不可信"]))
    sc += [
        ("角落随形：dim 与底图拉伸后 α 支撑集不重合像素数（==0）", ck["dim_support_mismatch"],
         ck["dim_support_mismatch"] == 0),
        ("角落随形：新 dim 在底图 α==0 处改动的像素数（==0；最大通道差 %d）"
         % ck["new_maxdelta_outside"], ck["new_outside"], ck["new_outside"] == 0),
        ("角落随形 · 对照组（旧 rect 284×48 @6,8 opa110）在底图 α==0 处改动的像素数（**>0** ⇒ 判据非空转）",
         ck["old_outside"], ck["old_outside"] > 0),
        ("角落随形 · 旧「方角」的几何面积 = 可见实体面 r=16 的切角 r²−πr²/4（**每角**）",
         "%.2f px/角（四角合计 %.1f px）" % (CORNER_CUT_THEORY, 4 * CORNER_CUT_THEORY), True),
        ("角落随形 · 对照组实测：压到底图**未成实体**（α<230）／**非全不透明**（α<250）的像素数",
         "%d / %d" % (ck["old_soft_all"], ck["old_part_all"]), ck["old_soft_all"] > 0),
        ("角落随形 · 对照组分角读数 角序 TL/TR/BL/BR（24×24 内：压到 α==0 ／ α<230 ／ α<250）",
         " ／ ".join("%s %d/%d/%d" % (k, ck["corners"][k]["old"], ck["corners"][k]["old_soft"],
                                     ck["corners"][k]["old_part"])
                    for k in ("TL", "TR", "BL", "BR")), True),
        ("对勾取色：palette 原值 %s 对三面＝%s（对 select 仅 %.3f ⇒ 对分节点面不达标，必须压深）"
         % (hexof(GREEN_PAL), " ／ ".join(
             "%s 实测%.3f/给定%.3f" % (FACE_CN[k], m, g)
             for k, (m, g) in plate_contrasts(GREEN_PAL).items()),
             min(min(m, g) for m, g in plate_contrasts(GREEN_PAL).values())),
         hexof(GREEN_PAL), True),
        ("对勾取色：上一版 `#3F8A5A`（按**单面**选的，已作废）对三面＝%s ⇒ **select 面不达标**"
         % " ／ ".join("%s 实测%.3f/给定%.3f" % (FACE_CN[k], m, g)
                       for k, (m, g) in plate_contrasts(GREEN_PREV).items()),
         hexof(GREEN_PREV), True),
        ("对勾取色：**最终绿 %s**（数值求解所得）对三面＝%s ｜ 最差 %.3f（门槛 %.1f／目标 %.1f）"
         % (hexof(CK_PLATE),
            " ／ ".join("%s 实测%.3f/给定%.3f" % (FACE_CN[k], m, g)
                        for k, (m, g) in plate_contrasts(CK_PLATE).items()),
            min(min(m, g) for m, g in plate_contrasts(CK_PLATE).values()),
            CONTRAST_PLATE_MIN, CONTRAST_PLATE_GOAL), hexof(CK_PLATE),
         min(min(m, g) for m, g in plate_contrasts(CK_PLATE).values()) >= CONTRAST_PLATE_MIN),
        ("对勾取色：白勾对最终绿牌 %.3f:1（**目标 ≥%.1f**）"
         % (contrast(CK_GLYPH, CK_PLATE), CONTRAST_GLYPH_MIN), hexof(CK_GLYPH),
         contrast(CK_GLYPH, CK_PLATE) >= CONTRAST_GLYPH_MIN),
        ("对勾取色：最终绿色相 %.1f° ∈ [%.0f,%.0f]（仍是「绿」，未变墨绿黑）"
         % (hue_of(CK_PLATE), HUE_LO, HUE_HI), "%.1f°" % hue_of(CK_PLATE),
         HUE_LO <= hue_of(CK_PLATE) <= HUE_HI),
        ("备选版：白描边对**浅色 select 面** %.3f:1 ⇒ 描边在浅面上不起轮廓作用；"
         "备选件对浅面的可辨认性**完全由勾绿承担**（勾绿与主版同值 ⇒ 三面同样达标）"
         % contrast(CK_GLYPH, face_colors()["med"]["select"]),
         round(contrast(CK_GLYPH, face_colors()["med"]["select"]), 3), True),
    ]

    # ── 报告 ───────────────────────────────────────────────────────
    say("=" * 122)
    say("m57_make_state_assets.py · 未解锁压暗件（随形 alpha ×3）＋ 已读对勾件（×2）"
        "（ISSUE-20260928-03）")
    say("调色板：%s ｜ 落点：%s" % (os.path.basename(PALETTE), OUT))
    say("对勾取色（一审打回：判据须对**三种节点面**同时成立）：")
    for tag, g in (("palette 原值", GREEN_PAL), ("上一版（单面选，作废）", GREEN_PREV),
                   ("**最终（数值求解）**", CK_PLATE)):
        ct3 = plate_contrasts(g)
        say("   %-22s %s 色相 %.1f° ｜ 三面 %s ｜ 最差 %.3f ｜ 白勾对牌 %.3f"
            % (tag, hexof(g), hue_of(g),
               " / ".join("%.3f" % min(m, gg) for m, gg in ct3.values()),
               min(min(m, gg) for m, gg in ct3.values()), contrast(CK_GLYPH, g)))
    say("-" * 122)
    say("%-30s %-9s %-5s %8s %4s %4s %10s %12s %9s %6s %s"
          % ("文件", "尺寸", "mode", "字节", "amin", "amax", "α=0占比%", "核心α≥250%", "主色",
             "幂等", "写前"))
    for r in rows:
        say("%-30s %-9s %-5s %8d %4d %4d %10.4f %12.4f %9s %6s %s"
              % (r["name"], r["size"], r["mode"], r["bytes"], r["amin"], r["amax"],
                 r["zero_cov"], r["core_cov"], r["top"], r["idem"], r["before"]))
    say("-" * 122)
    for lab, val, ok in sc:
        say("  [%s] %s = %s" % ("OK" if ok else "!!", lab, val))
    say("-" * 122)
    tot = sum(r["bytes"] for r in rows)
    say("合计：%d 件 / %d 字节（%.2f KB）" % (len(rows), tot, tot / 1024.0))
    say("幂等 %d/%d ｜ 结构 / 语义失败 %d 件 ｜ 语义断言失败 %d 项"
          % (sum(1 for r in rows if r["idem"] == "OK"), len(rows), len(fails),
             sum(1 for _, _, o in sc if not o)))
    for n, e in fails:
        say("  !! %s：%s" % (n, "; ".join(e)))
    if write:
        os.makedirs(EVID, exist_ok=True)
        with open(os.path.join(EVID, "素材实测.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# m57 产出 5 件（ISSUE-20260928-03）｜ 由生成器写出；"
                    "`m57_evidence.py` 另有**独立回读**版（本文件不作交付依据）\n")
            f.write("文件\t尺寸\tmode\t字节\talpha_min\talpha_max\tα=0占比%\t核心α≥250占比%"
                    "\t非透明占比%\t主色\t主色像素数\t源件\t备注\t幂等\t写前状态\tmd5\n")
            for r in rows:
                f.write("\t".join(str(r[k]) for k in
                                  ("name", "size", "mode", "bytes", "amin", "amax", "zero_cov",
                                   "core_cov", "cov", "top", "topn", "src", "note", "idem",
                                   "before", "md5")) + "\n")
    ok_all = not fails and all(o for _, _, o in sc)
    say("结果：**%s**" % ("全部通过" if ok_all else "存在失败项"))
    say("=" * 122)
    return (0 if ok_all else 1), rows, sc, fails, ck


# ══════════════════════════════════════════════════════════════════ 变异自证
MUTATIONS = (("alpha_plus1", "M1 dim alpha ＋1（alpha 逐像素相等断言应报错）"),
             ("rgb1", "M3 dim RGB → (1,1,1)（RGB 全 0 断言应报错）"),
             ("bbox", "M5 dim alpha → 源支撑集**外接矩形**填充（＝方角矩形等价物；角落断言应报错）"),
             ("chk21", "M2 对勾画布 / 牌径 → 21（尺寸断言应报错）"),
             ("prevgreen", "M4 绿牌调回**上一版 `#3F8A5A`**（按单面选的）⇒ 必须报「select 面不达标」"),
             ("palgreen", "M4b 绿牌用 palette 原值 `#5AA06A` ⇒ 三面全不达标"))


def mutations():
    """6 族变异（全部 write=False，不写任何资产）：确认断言**真的会失败**（非空转）。"""
    out = []
    for tag, label in MUTATIONS:
        rc, _rows, _sc, fails, _ck = run(write=False, mutate=tag, quiet=True)
        errs = [e for _n, es in fails for e in es]
        out.append((tag, label, rc, errs))
    return out


def write_evidence(rows, sc, ck, muts):
    """证据落盘（`_工作\\ISSUE-20260928-03_素材\\证据\\`）。`素材实测.tsv` 由 `run()` 写。"""
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, "对比度.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 对勾件取色与 WCAG 相对亮度对比度（ISSUE-20260928-03）\n")
        f.write("# ★ 一审打回修复：判据必须对**三种节点面同时**成立（对勾永远画在节点面左上角，\n")
        f.write("#   三类节点面颜色不同）。门槛 ① 对每面 ≥2.5:1（硬）② 争取对最差面 ≥3.0:1 "
                "③ 白勾对绿牌 ≥4.5:1 ④ 色相 ∈ [110,155]°\n")
        f.write("# 面值两组：**底图件实测中位色**（α≥250 实体的逐通道中位）与**交付清单给定色**；"
                "对照度对两组都算。\n")
        fc = face_colors()
        f.write("# 面色：%s\n" % " ｜ ".join(
            "%s 实测中位 %s（L=%.5f）／给定 %s（L=%.5f）"
            % (FACE_CN[k], hexof(fc["med"][k]), rel_lum(fc["med"][k]),
               hexof(fc["given"][k]), rel_lum(fc["given"][k])) for k in FACE_GIVEN))
        f.write("绿牌\t色值\tHSL色相°\tWCAG L\t白勾对牌\t" +
                "\t".join("%s(实测面)" % FACE_CN[k] for k in FACE_GIVEN) +
                "\t" + "\t".join("%s(给定面)" % FACE_CN[k] for k in FACE_GIVEN) +
                "\t最差(取两组更苛刻)\t结论\n")
        for lab, g in (("palette 原值", GREEN_PAL),
                       ("上一版（按单面选，作废）", GREEN_PREV),
                       ("**最终（数值求解）**", CK_PLATE),
                       ("备选版勾绿（最终）", CK_ALT_GREEN)):
            ct3 = plate_contrasts(g, fc)
            worst = min(min(m, gg) for m, gg in ct3.values())
            f.write("%s\t%s\t%.1f\t%.5f\t%.4f\t%s\t%s\t%.4f\t%s\n"
                    % (lab, hexof(g), hue_of(g), rel_lum(g), contrast(CK_GLYPH, g),
                       "\t".join("%.4f" % ct3[k][0] for k in FACE_GIVEN),
                       "\t".join("%.4f" % ct3[k][1] for k in FACE_GIVEN),
                       worst,
                       ("三面全 ≥2.5 ✔ 且全 ≥3.0 ✔" if worst >= CONTRAST_PLATE_GOAL
                        else ("三面全 ≥2.5 ✔（未全达 3.0）" if worst >= CONTRAST_PLATE_MIN
                              else "**有面 <2.5 ✘**"))))
        f.write("\n# 其余比对项\n项\t前景\t背景\t对比度:1\t门槛\t结论\n")
        crow = (("白勾（主版）对牌绿", CK_GLYPH, CK_PLATE, CONTRAST_GLYPH_MIN),
                ("白描边（备选版）对勾绿", CK_GLYPH, CK_ALT_GREEN, CONTRAST_GLYPH_MIN),
                ("白描边（备选版）对 select 实测面", CK_GLYPH, fc["med"]["select"], None))
        for lab, fg, bg, thr in crow:
            ct = contrast(fg, bg)
            f.write("%s\t%s\t%s\t%.4f\t%s\t%s\n"
                    % (lab, hexof(fg), hexof(bg), ct, "—" if thr is None else "%.1f" % thr,
                       "仅登记：白描边在浅面上不起轮廓作用，备选件的可辨认性由**勾绿**承担"
                       if thr is None else ("达标" if ct >= thr else "**不达标**")))
        f.write("# 求解脚本：`复现脚本\\m57_solve_green.py`（穷举 + 选定规则，非试色）\n")

    with open(os.path.join(EVID, "角落自证.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 角落随形判据：把 x_ui_node_section_dim.png 按落盘 nine %s 拉到 %dx%d，"
                "按元素 opacity %d 叠在 x_ui_node_section_off.png 上（同画布）\n"
                % (json.dumps(NODE_SRC[0][3], separators=(",", ":")),
                   NODE_DESIGN_W, NODE_DESIGN_H, DIM_OPACITY))
        f.write("# 比较用 α 预乘（裸 RGB 在 α=0 处可携带非零值 ⇒ 会假阳性）\n")
        f.write("# 读数：底图 α==0 的像素处，叠加前后有差异的像素数\n")
        f.write("项\t读数\t期望\n")
        f.write("dim 与底图拉伸后 α 支撑集不重合像素数\t%d\t0\n" % ck["dim_support_mismatch"])
        f.write("新 dim 在底图 α==0 处改动像素数 / 最大通道差\t%d / %d\t0 / 0\n"
                % (ck["new_outside"], ck["new_maxdelta_outside"]))
        f.write("对照组（旧 rect 284×48 @6,8 opa%d）改动像素数 / 最大通道差\t%d / %d\t>0（证明判据非空转）\n"
                % (DIM_OPACITY, ck["old_outside"], ck["old_maxdelta_outside"]))
        f.write("旧「方角」几何面积 = 可见实体面 r=%g 的切角 r²−πr²/4（每角 / 四角合计）\t%.2f / %.1f\t—（与任务书「约 55px 暗方角」对应）\n"
                % (NODE_FACE_R, CORNER_CUT_THEORY, 4 * CORNER_CUT_THEORY))
        f.write("对照组实测：压到底图未成实体(α<230) / 非全不透明(α<250) 的像素数\t%d / %d\t>0\n"
                % (ck["old_soft_all"], ck["old_part_all"]))
        for k in ("TL", "TR", "BL", "BR"):
            c = ck["corners"][k]
            f.write("对照组角读数 %s（24×24 内：压到 α==0 / α<230 / α<250 / 最大通道差）\t%d / %d / %d / %d\t—\n"
                    % (k, c["old"], c["old_soft"], c["old_part"], c["old_max"]))
            f.write("新 dim 角读数 %s（24×24 内压到 α==0 的像素数）\t%d\t0\n" % (k, c["new"]))

    with open(os.path.join(EVID, "变异自证.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 变异自证：搅坏输入，确认断言**真的会失败**（非空转）；全部 write=False、"
                "不写任何资产。期望每条 rc=1 且确有断言报错。\n")
        for tag, label, mrc, merrs in muts:
            f.write("\n[%s] %s\n    rc=%d；触发断言 %d 条：\n"
                    % ("符合预期" if (mrc == 1 and merrs) else "!! 未失败", label, mrc, len(merrs)))
            for e in merrs:
                f.write("      %s\n" % e)

    with open(os.path.join(EVID, "语义断言.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("判据\t读数\t结论\n")
        for lab, val, ok in sc:
            f.write("%s\t%s\t%s\n" % (lab, val, "PASS" if ok else "FAIL"))

    with open(os.path.join(EVID, "md5清单.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# ISSUE-20260928-03 产出 5 件 md5（m57_make_state_assets.py）\n")
        for r in rows:
            f.write("%s\t%s\t%s\n" % (r["md5"], r["name"], r["size"]))
    say("证据：%s" % EVID)


if __name__ == "__main__":
    do_write = "--dry-run" not in sys.argv
    rc, rows, sc, fails, ck = run(write=do_write)
    muts = mutations()
    print("变异自证（期望每条 rc=1 且确有断言报错；全部 write=False、不写盘）：")
    for tag, label, mrc, merrs in muts:
        print("  [%s] %-64s → rc=%d  触发断言 %d 条"
              % ("OK" if (mrc == 1 and merrs) else "!!", label, mrc, len(merrs)))
        for e in merrs:
            print("        %s" % e)
    bad = [t for t, _l, mrc, merrs in muts if mrc != 1 or not merrs]
    print("变异自证结果：%s" % ("**%d/%d 全部按预期失败**" % (len(muts), len(muts)) if not bad
                                else "**以下变异未失败：%s**" % bad))
    if do_write:
        write_evidence(rows, sc, ck, muts)
    print("=" * 122)
    sys.exit(0 if (rc == 0 and not bad) else 1)
