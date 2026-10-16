# -*- coding: utf-8 -*-
r"""make_node_variant_a.py —— 流程图三类节点底图「方案 A」正式素材生成器（幂等）

Issue  : ISSUE-20260927-05（流程图节点「类型可区分」配色）
         ISSUE-20260927-07（**描边实现重写：修几何毛刺**——见下「描边实现」）
裁决   : 用户 2026-09-27 选定 **方案 A**（同族三档色相 + 选择支加粗描边）
依据   : `UI组\_工作\ISSUE-20260927-05_流程图实现\配色对比.md`（三方案实测 + 裁决）
         `…\复现脚本\mock_node_colors.py`（已批准效果图；本脚本逐字复用其 `recolor` /
          九宫格外的核心思路；`inner_stroke` 的**环带几何**已于 -07 重写，见下「描边实现」）

输入（**只读**）： UI组\_工作\ISSUE-20260927-05_流程图实现\原形备份\x_ui_node_{section,select,frag}_{off,on}.png
                  （6 件原件，二进制不动；改色一律从备份读，故本脚本可反复执行、结果恒定）
输出（**覆盖**）： UI组\krkr\assets\ui\x_ui_node_{section,select,frag}_{off,on}.png
证据（新出）    ： UI组\_工作\ISSUE-20260927-07_节点描边与系统按钮\取证\正式落地\节点素材_正式链_管线前后对照.png
                  （★ 本轮改写到 -07 的证据目录：不再覆盖 -05 的 `节点素材_方案A_前后对照.png`，
                   后者是 -05 的存档证据，按「不覆盖」原则保留）

管线顺序（2026-09-27 · ISSUE-20260927-07 解析化轮；**顺序不得调换**）
------------------------------------------------------------------
    原形备份原件
      ├─① 轮廓解析化（**新增**）  半径 r=16 统一；逐边柔光剖面表；**只改 alpha**，RGB 保持原件
      ├─② 方案 A 改色 recolor     section/select/frag 的 H/S/V 参数一字未改
      ├─③ `_on` 提亮档 ON_GAIN    参数一字未改
      ├─④ `select` 2px 内描边     既有 stroke_coverage()/inner_stroke()，**画在解析化后的轮廓上**
      └─⑤ 保存 PNG（optimize=True, compress_level=9；尺寸与原件相同）

① 轮廓解析化（本轮唯一新增环节；实现 import 复用 -07 候选档）
==========================================================
**用户裁决**：四角统一解析半径 **r=16**（2026-09-27）。
**依据**：`…\ISSUE-20260927-07_节点描边与系统按钮\取证\圆角候选\对比_轮廓解析化_四档.png`
        ＋ `…\轮廓解析化_数字证据.txt`（候选档实测）。

**为什么必须做**（-05 的描边「坑洼毛刺」的一半根因在原件的**边沿本身**）：

| 现象 | 实测数字 | 结论 |
| --- | --- | --- |
| 原件边沿**不是** box 覆盖度 | section 左边边界格：box 给 68、实测 **91**；顶边最后内部格 box 给 250、实测 **215** | 原件边沿自带 **2–3px 软肩** ⇒ 用 box 覆盖度会硬切 |
| 直边出现「外扩 0.5px + 硬边亮线」 | 给定式 `max(cov*255, glow)` 直边最大偏差 section **57** / select **98** / frag **113** | 必须换**同源径向剖面表**（边缘过渡与柔光同出一源） |
| 底边 1px 掩码缺口 ⇒ 描边鼓包 | `select_off` 底边 y=56 行 x=167 处 **alpha=229 < 230** ⇒ `solid=alpha>=230` 掩码在该列缺 1 格 | 不再调阈值，改**整条轮廓解析化** ⇒ 缺口不可能存在 |

**算法**（对给定式的保真化实现，逐字来自候选档 `make_node_contour_candidates.py`）：

    ① 锚点 rect = **该件自身** alpha 的 50% 覆盖交叉矩形（CROSS=127.5；sub-pixel）
    ② 半径 radii = (16, 16, 16, 16)          # 用户裁决；四角统一
    ③ 剖面表 prof = 逐边实测「alpha = f_s(到 rect 的有符号距离 t)」（外正内负，
       t∈[-6, 20]；直线带 = 去掉四角 (r+2) 后的中央区，逐格取均值抗噪）
    ④ alpha(p) = Σ_s w_s(p) · f_s(t(p))      # t(p) = 到解析圆角矩形的精确距离场；
                                             # w_s = 最近轮廓点的**外向法线**在该边上的分量（Σw=1）
       ⇒ 直边上逐像素与原件一致（零回归）；四角按法线方向做角向混合，弧上光滑无折线

**★ 锚点必须「逐件自锚」**（off 用 off 的 rect、on 用 **on 自身**的 rect）——
  `probe_on_rect_choice.py` 实测：若 on 沿用 off 的 rect，合成件的四角半径复测升到
  **16.8–17.7**（超验收 ±0.2）；逐件自锚则六件半径复测 ∈ **[15.89, 16.04]**。

**直边代价**（候选档实测，r=16 档）：直边 |Δalpha| max = section **13** / select **17** / frag **21**，
  ≥88% 的直边像素 |Δ|≤2；底边缺口行修后恒 235、描边全列 2.00（见自检 ⑧/⑨/⑩）。

改色口径（与 mock_node_colors.py 的 SCHEMES["A"] 逐字一致）

    kind      H        S      V倍    描边
    section   218°     0.20   ×1.00  无
    select    200°     0.55   ×0.86  2px 内描边 #2A5490
    frag      268°     0.28   ×1.00  无

  · RGB→HSV，**设定 H/S、乘 V**，**alpha 通道原样保留**；像素尺寸不变。
  · `_off` 与 `_on` 用同一套 H/S/V 基参数（两态原有的明暗差异保留在 V 上）。
  · 描边 = **4× 超采样 + 圆盘腐蚀 + BOX 降采样**得到的抗锯齿 2px 内描边（见下「描边实现」）；
    只改环带 RGB、alpha 逐字节沿用原件，不改外轮廓、不外扩画布。

_on 提亮档（2026-09-27 追加：悬停反馈修复）
------------------------------------------
问题（主代理实测）：方案 A 把 H/S 覆写后，`section` / `frag` 的两态差被抹平
（不透明区 ΔRGB 均 3.19 / 1.78，最大 7 / 6），而这一屏悬停是主要交互 ⇒ 缺陷。
成因：原件两态主要差在 H/S（`section` off S=0.091 → on S=0.101、V 245→249），覆写 H/S 后差消失。

修法：**只对 `_on` 追加一层乘法提亮，`_off` 一个字节不动**：

    ON_GAIN[kind] = (g, s)      S ← S*s ；V ← V*g   （都在 HSV 域乘、保留原件明暗结构）

| kind | g | s | V 是否有 headroom | 说明 |
| --- | --- | --- | --- | --- |
| section | 1.00 | 0.60 | 无（V≈250/255） | g>1 会把蓝通道大面积顶到 255（实测 g=1.015 → 10% 不透明像素 V=255，g=1.02 → 21%）⇒ g 留 1.00，提亮**走饱和度轴**（降 S ⇒ 最小通道抬升 ⇒ 亮度升） |
| frag | 1.00 | 0.65 | 无（V≈250/255） | 同上 |
| select | 1.04 | 0.95 | **有**（本作 select 的 V 已 ×0.86，V≈214） | 乘 V 不会顶 255 ⇒ 用 V 与 S 双轴提亮 |

> **口径说明**：本作节点底近似「冰蓝霜白」，体区 V 已到 255 的 96–98%，
> 唯一有意义的提亮轴是**降低饱和度**（让最小通道上升）。该轴同样是乘法、同样保住原件的明暗结构，
> 且正是原件两态实际差异所在的轴（off S=0.091 → on S=0.101），只是把幅度放大到肉眼可辨。

提亮后实测（复现主代理读数：掩码=两态 alpha 均 >211；均=逐像素三通道平均差；最大=逐像素单通道最大差）：

| kind | 均（改前 → 改后） | 最大（改前 → 改后） | 验收（均 ≥8 / 最大 ≥20） |
| --- | --- | --- | --- |
| section | 3.34 → 13.69 | 71 → 26 | PASS |
| select | 2.46 → 9.76 | 54 → 99 | PASS（-05 版为 13.79 / 103；-07 描边加宽到 2px 后，环带（两态同色）占了更多实体面像素 ⇒ 均差下降，仍 ≥8） |
| frag | 4.26 → 14.08 | 41 → 29 | PASS |

描边实现（2026-09-27 · ISSUE-20260927-07 重写；旧实现已废弃）
==========================================================
**用户报**：选择支节点「图形不标准、坑坑洼洼、带毛刺」。
**定位**（主代理）：`x_ui_node_select_off.png` 左端 4× 放大可见描边**阶梯状、粗细不均、圆角处有钩刺**；
不是 `nine` 拉伸造成（左右端 1:1 不拉），是**素材本身**。

**旧实现的两处根因**（旧代码：`alpha>128` 掩码 − `MinFilter(5)` 腐蚀，再叠原件 alpha）：
1. **阈值与核都错**：`alpha>128` 的等值线落在 plate 的**柔光渐变边**里，该处 alpha 逐像素缓变 ⇒
   等值线位置抖动、环带按像素跳变；`MinFilter` 是**方核**（Chebyshev 距离 2）⇒ 45° 圆角处
   法向厚度 = 2√2 ≈ 2.83px 而直边只有 2px ⇒ 圆角偏厚、钩刺。
   实测（`select_off` 顶边中段）：旧环带 1208 px 中 **44.5% 的 alpha < 230**、均值仅 207.5
   ⇒ 带宽名义 2px、**落在实体面上的只有 1px**，且随下方柔光边忽明忽暗 ⇒ 视觉上「坑洼」。
2. **1× 二值环带**：环带只有 0/255 两级 ⇒ 边缘无 AA，放大即见台阶。

**新实现**（本脚本 `inner_stroke()` / `stroke_coverage()`）：

    solid  = (alpha >= SOLID_THR=230)                 # ① 1×「实体区」判定（贴可见实体面内侧，
                                                      #    不与 plate 自身柔光边打架 ⇒ 修掉旧版发毛来源 2）
    solid4 = NEAREST 上采样 ×SS=4                      # ② 保持掩码形状，不引入插值
    eroded = min over {(dy,dx): dy²+dx² <= (STROKE_W*SS)²} of shift(solid4)
                                                      # ③ **圆盘**腐蚀（半径 = 2px × 4 = 8）
                                                      #    ⇒ 各法向厚度恒定，圆角不再偏厚（修掉来源 1）
    ring4  = solid4 AND NOT eroded
    ringA  = BOX 降采样 ring4 → 1×                     # ④ 每 1× 像素 = 4×4 子样本的覆盖比例
                                                      #    ⇒ 覆盖度 0..1、最多 17 级（天然 AA；修掉来源 2）
                                                      #    实测：外缘与 plate 实体边界重合（1× 对齐 ⇒ 0/1），
                                                      #    分数级出现在**环带内缘**（圆盘腐蚀的圆弧边界）——
                                                      #    select 实测 4 个非零取值 0.1875 / 0.6875 / 0.8125 / 1.0
    out_rgb   = ringA × #2A5490 + (1 − ringA) × src_rgb # ⑤ **只在 1× 上合成、只改 RGB**
    out_alpha = src_alpha（PIL band 原样并入，**逐字节不变**）

**为什么这样设计**：
- 覆盖度来自 4× 超采样的 BOX 降采样 ⇒ 环带**内缘**带分数覆盖（抗锯齿、视觉平滑，
  旧版是 0/255 二值 ⇒ 放大即见台阶）；环带**外缘**与 `alpha≥230` 实体边界重合（1× 对齐
  ⇒ 覆盖 0/1），该处本来就有 plate 自身的 alpha 渐变做混合 ⇒ 不需要额外 AA。
- **alpha 一字不动** ⇒ 满足本工程既有的「alpha 逐字节不变」验收（自检②），也不动 plate 的柔光边。
- `solid = alpha≥230` 让描边**贴在可见实体面内侧**，不再落进柔光渐变带 ⇒ 环带位置稳定。
- **不要**「整体上采样再整体降采样」——那会让 plate 本体像素也变；**只对掩码做 4×→1×**，
  合成在 1× 上进行，`ringA == 0` 的像素 `out_rgb` 与 `src_rgb` **逐字节相同**。

**回归锁（2026-09-27 · 解析化轮改口径）**
旧口径（-05～-07）是「非描边件必须逐字节不变」——因为那时 alpha 原样保留、只有 select 加描边。
**本轮 alpha 整体解析化 ⇒ 六件都变**，故回归锁改为：
- `GOLD_MD5` 锁**本轮产出**（六件新值）；`PREV_MD5` 锁**本轮开工前盘上的 -07 值**（六件旧值）；
- 自检⑤ 断言「六件 全部 ≠ PREV_MD5（解析化确实生效）且 == GOLD_MD5（可复现）」；
- 几何/柔光的**回归判据**改由自检⑦（RGB 与 `recolor(原件)` 预期一致）与自检⑩（直边 |Δalpha| 统计）承担。

**描边画在解析化后的轮廓上**：`inner_stroke()` 的 `stroke_coverage()` 读的是**第①步解析化之后的 alpha**
（`build()` 里 `recolor()` 保留该 alpha → `inner_stroke()` 直接取用）⇒ `solid=alpha>=230` 的等值线
落在解析曲线上，底边不再有 1px 缺口 ⇒ 环带不再鼓包（实测底边各列竖向径向宽度恒 **2.00**）。

**与 mock（`mock_node_colors.py`）的关系**：mock 用 `out.paste(color, (0,0), ring)`，paste **连 alpha 一起写**
（环带 alpha 被强制 255）；环带由 `alpha>128` 掩码 − `MinFilter(5)` 独立算得（实测 select_off 1208 px、
带内 alpha 均值 207.5）。本脚本 -07 起的口径与 mock**故意不同**：
  ① **只改 RGB**、alpha 用原 `A` band 并回（构造上保证逐字节不变；旧版的 `STROKE_KEEP_ALPHA` 开关已删除）；
  ② 掩码阈值 由 `alpha>128` 改为 `alpha≥230`（环带整体内移到实体面内）；
  ③ 核 由**方核 MinFilter(5)** 换成**圆盘**（半径 2px），并加 4× 超采样 ⇒ 法向厚度恒为 2px、
     覆盖度最多 17 级（select 实测 4 级：0.1875 / 0.6875 / 0.8125 / 1.0）。
相同点：内缩、不外扩、只改环带、不改外轮廓。

用法：

    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "/e/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
    python "_工作/ISSUE-20260927-05_流程图实现/复现脚本/make_node_variant_a.py"

退出码：0 = 全部自检通过；1 = 有验收项不通过（并打印明细）。
"""
import hashlib
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image, ImageDraw, ImageFont                              # noqa: E402

HERE = Path(__file__).resolve()
UI = HERE.parents[3]                     # …\UI组
ASSETS = UI / "krkr" / "assets" / "ui"
ISSUE = UI / "_工作" / "ISSUE-20260927-05_流程图实现"
BACKUP = ISSUE / "原形备份"
EVID = ISSUE / "取证"
# ★ 证据图改落 -07 目录（-05 的 `节点素材_方案A_前后对照.png` 是 -05 存档证据，不覆盖）
ISSUE7 = UI / "_工作" / "ISSUE-20260927-07_节点描边与系统按钮"
EVID7 = ISSUE7 / "取证" / "正式落地"
SHEET = EVID7 / "节点素材_正式链_管线前后对照.png"
REPRO7 = ISSUE7 / "复现脚本"

SAMPLE = (148, 10)          # 实测 fill 取样点（与 mock 一致）
TOL = 3                     # 取样点容差 ±3/255

# ★ 轮廓解析化：主代理定位的底边缺口列（自检⑧ 专项读数）
NOTCH_X = 167

# ★ 轮廓解析化常量（2026-09-27 · 解析化轮；见文件头「管线顺序 ①」）
RADIUS = 16.0               # 用户裁决：四角统一解析半径 r=16
CROSS = 127.5               # 轮廓定义：alpha 的 50% 覆盖交叉点（沿用候选档口径）

# ★ 描边几何常量（2026-09-27 · ISSUE-20260927-07 重写；见文件头「描边实现」）
STROKE_W = 2                # 描边**径向**宽度（1× px，内缩）
SOLID_THR = 230             # 「实体区」alpha 阈值（1×；贴可见实体面内侧，避开柔光渐变带）
SS = 4                      # 超采样倍率：掩码 NEAREST ×4 → 圆盘腐蚀 → BOX 降采样回 1× ⇒ 17 级 AA

# ★ 回归锁：本轮 alpha 整体解析化 ⇒ **六件都变**（见文件头「回归锁」）
#   GOLD_MD5 = 本轮产出（新值，自检⑤ 锁定可复现性）；PREV_MD5 = 开工前盘上的 -07 值（旧值）。
#   PIL 为工作区内置 12.3.0（`工具\pylibs`）⇒ PNG 编码恒定。若日后**有意**改动
#   解析化半径 / 剖面表 / recolor / 提亮口径，须同步更新本表。
GOLD_MD5 = {
    "x_ui_node_section_off.png": "15da4d894a39bd1e1f44d40890ac2021",
    "x_ui_node_section_on.png":  "b32f43bb0dd007f37b4310d91fded83f",
    "x_ui_node_select_off.png":  "16c7d5a7e13b89e328933cb2ac13be39",
    "x_ui_node_select_on.png":   "e0e01b18b979f4d5c4330c8bb7739809",
    "x_ui_node_frag_off.png":    "5ed971d28ec6e19c31fb814b8290b6bf",
    "x_ui_node_frag_on.png":     "c07469d399c726c2f8402406f06000a6",
}
# 开工前（ISSUE-20260927-07 上一版脚本产出）的 md5 —— 用于证明「六件都已解析化」
PREV_MD5 = {
    "x_ui_node_section_off.png": "f3e1d3b9c765d2deaec57ccde6128fef",
    "x_ui_node_section_on.png":  "f6aa12a31c53501e35e2a5499f2b1c82",
    "x_ui_node_select_off.png":  "0b5526d1cd502645c0c914ca3e994396",
    "x_ui_node_select_on.png":   "c0ae4c58af3d6cfca53270a7405f827a",
    "x_ui_node_frag_off.png":    "f724354b35c5cd1a585ccccc1ae86421",
    "x_ui_node_frag_on.png":     "d4b03394e248a97a232e2fbd27a48f89",
}
# 不带描边 ⇒ 只走 ①②③（几何/RGB 回归判据见自检⑦⑩）
NO_STROKE = ("section", "frag")
# 验收：半径实测（相切一维搜索口径）与 16 的容差
RADIUS_TOL = 0.2

# ★ 轮廓解析化的**直线带**统计（自检⑩，判据见 README 口径）：直边偏差与「≥85% 像素 |Δ|≤2」
STRAIGHT_MIN_LE2 = 0.85

_CN = None


def cn():
    """惰性 import -07 候选档 `make_node_contour_candidates`，复用其**已实测验证**的解析化实现
    （`rect_of` / `radius_corner` / `corner_diag_radius` / `shape_fields` / `collect_profiles` /
    `synth` / `ring_width_radial`），避免二份实现漂移（任务书明确允许直接 import 复用）。

    必须**惰性**：候选档在本模块顶层 `import make_node_variant_a as MF`（互相 import）——
    若本模块在常量定义完成前 import 它，会拿到半初始化的模块（其顶层 `SOLID = MF.SOLID_THR` 会崩）。
    """
    global _CN
    if _CN is None:
        if str(REPRO7) not in sys.path:
            sys.path.insert(0, str(REPRO7))
        import make_node_contour_candidates as mod
        _CN = mod
    return _CN


# ★ _on 提亮档（只作用于 on 件；见文件头「_on 提亮档」）
#   ON_GAIN[kind] = (g, s) —— S ← S*s、V ← V*g（均在 HSV 域乘，保留原件明暗结构）
ON_GAIN = {
    "section": (1.00, 0.60),   # V 无 headroom ⇒ 只走饱和度轴
    "select":  (1.04, 0.95),   # V 有 headroom（本作 select 的 V 已 ×0.86）⇒ V+S 双轴
    "frag":    (1.00, 0.65),   # V 无 headroom ⇒ 只走饱和度轴
}

# 态差验收口径（复现主代理读数）：掩码 = 两态 alpha 均 > 该阈值
#   mean = 逐像素 (|ΔR|+|ΔG|+|ΔB|)/3 的均值 ；max = 逐像素 max(|ΔR|,|ΔG|,|ΔB|) 的最大
STATE_THR = 211
STATE_MEAN_MIN = 8.0
STATE_MAX_MIN = 20

# kind -> (H, S, V倍, 描边色 or None)
SPEC = {
    "section": (218, 0.20, 1.00, None),
    "select":  (200, 0.55, 0.86, (42, 84, 144)),   # #2A5490
    "frag":    (268, 0.28, 1.00, None),
}
STATES = ("off", "on")
KINDS = ("section", "select", "frag")
KIND_CN = {"section": "章节点", "select": "选择支节点", "frag": "番外节点"}

# _off 的期望 fill（裁决书列出的实测值，带 ±TOL 容差）；_on 只如实报实测
EXPECT_OFF = {"section": (0xC4, 0xD6, 0xF5), "select": (0x60, 0xAD, 0xD5), "frag": (0xD1, 0xB1, 0xF5)}

BG = (24, 31, 46)           # 对照图底色（与实际流程图底色同量级）
FG = (232, 238, 246)
FG_DIM = (168, 180, 196)
HL = (255, 214, 140)
OK = (140, 214, 160)
BAD = (240, 130, 130)

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/msyhbd.ttc", 0), ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0), ("C:/Windows/Fonts/simsun.ttc", 0),
]
_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _fc:
        return _fc[key]
    cand = ([c for c in FONT_CANDIDATES if "bd" in c[0]] + FONT_CANDIDATES) if bold else FONT_CANDIDATES
    f = None
    for path, idx in cand:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size, index=idx)
                break
            except Exception:
                continue
    if f is None:
        f = ImageFont.load_default()
    _fc[key] = f
    return f


# ---------------------------------------------------------------- 改色 / 描边
def recolor(img, hue=None, sat=None, vmul=None):
    """（与 mock_node_colors.py 逐字一致）设 H/S、乘 V；保留原件 V 与 alpha。"""
    r, g, b, a = img.split()
    H, S, V = Image.merge("RGB", (r, g, b)).convert("HSV").split()
    if hue is not None:
        H = H.point(lambda _p: int(round(hue / 360.0 * 255)) & 0xFF)
    if sat is not None:
        S = S.point(lambda p: max(0, min(255, int(round(sat * 255)))))
    if vmul is not None:
        V = V.point(lambda p: max(0, min(255, int(round(p * vmul)))))
    rgb = Image.merge("HSV", (H, S, V)).convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), a))


_DISK_CACHE = {}


def disk_offsets(radius):
    """半径 radius 的**圆盘**结构元偏移集（含中心）：{(dy,dx) : dy²+dx² <= radius²}。

    ★ 不用 PIL 的 `ImageFilter.MinFilter`（方核 = Chebyshev 距离）——方核会让 45° 方向的
      法向厚度放大到 √2 倍（2px → 2.83px），这正是圆角处描边偏厚、有钩刺的原因。
      圆盘核（Euclidean）在每个法线方向的厚度都等于 radius ⇒ 描边粗细均匀。
    """
    if radius not in _DISK_CACHE:
        r2 = radius * radius
        _DISK_CACHE[radius] = [(dy, dx)
                               for dy in range(-radius, radius + 1)
                               for dx in range(-radius, radius + 1)
                               if dy * dy + dx * dx <= r2]
    return _DISK_CACHE[radius]


def stroke_coverage(alpha, width=STROKE_W, scale=SS, thr=SOLID_THR):
    """返回 1× 的描边**覆盖率**浮点掩码 ringA（0..1；天然 AA）。

    ① solid   = (alpha >= thr)                   1× 二值实体区（贴可见实体面内侧）
    ② solid_ss= NEAREST 上采样 ×scale            保持掩码形状，**不引入插值**
    ③ eroded  = min over 圆盘偏移（半径 width*scale）的 shift(solid_ss) ⇒ 圆盘腐蚀
    ④ ring_ss = solid_ss AND NOT eroded
    ⑤ ringA   = BOX 降采样 ring_ss（scale×scale 均值）⇒ 覆盖比例 0..1，共 scale²+1 级

    画布边界外视为**非实体**（shift 越界的部分取 0）——本作节点实体区（select_off: x[7..254]
    y[8..56]）离画布边 ≥7px，腐蚀半径 8（4× 上）不会触边，故无副作用。
    尺寸不是 scale 的倍数时右侧/底部补 0 到整数块再降采样（263×65 → 264×68，补的是空区）。
    """
    solid = (np.asarray(alpha) >= thr)
    ss = np.repeat(np.repeat(solid, scale, axis=0), scale, axis=1)
    h, w = ss.shape
    pad_h, pad_w = (-h) % scale, (-w) % scale
    if pad_h or pad_w:
        ss = np.pad(ss, ((0, pad_h), (0, pad_w)), constant_values=False)
        h, w = ss.shape
    eroded = np.ones_like(ss)
    r = width * scale
    for dy, dx in disk_offsets(r):                 # 偏移集对称 ⇒ 与「取 p+offset」等价
        shifted = np.zeros_like(ss)
        ys0, ys1 = max(0, dy), min(h, h + dy)
        xs0, xs1 = max(0, dx), min(w, w + dx)
        shifted[ys0:ys1, xs0:xs1] = ss[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        eroded &= shifted
    ring_ss = ss & ~eroded
    ringA = ring_ss.reshape(h // scale, scale, w // scale, scale).mean(axis=(1, 3))
    return ringA[:np.asarray(alpha).shape[0], :np.asarray(alpha).shape[1]]


def inner_stroke(img, color, width=STROKE_W):
    """抗锯齿的 width px **内**描边：只改环带 RGB，alpha 逐字节沿用原图。

    合成（**在 1× 上进行，不做整体上/下采样**）：
        out_rgb = ringA × color + (1 − ringA) × src_rgb
        out_alpha = src_alpha（原 `A` band 直接并回 ⇒ 逐字节不变）
    `ringA == 0` 的像素（含 plate 本体全部像素）⇒ `out_rgb == src_rgb` **逐字节相同**。
    """
    rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
    cov = stroke_coverage(img.getchannel("A"), width=width)[..., None]
    color = np.asarray(color, dtype=np.float64).reshape(1, 1, 3)
    out = np.clip(np.floor(cov * color + (1.0 - cov) * rgb + 0.5), 0, 255).astype(np.uint8)
    # alpha 用**原 band 对象**并回（不经 numpy 往返）⇒ 构造上保证 alpha 逐字节不变
    return Image.merge("RGBA", (*Image.fromarray(out, "RGB").split(), img.getchannel("A")))


def analytic_alpha(src):
    """① 轮廓解析化：返回 (alpha_uint8, rect, radii, prof) —— **只产出 alpha**，RGB 不动。

    · 锚点 rect = **该件自身** alpha 的 50% 覆盖交叉矩形（逐件自锚；理由见文件头「★ 锚点必须逐件自锚」）；
    · 半径 radii = (RADIUS, RADIUS, RADIUS, RADIUS)；
    · 剖面表 prof = 逐边实测「alpha = f_s(到 rect 的有符号距离 t)」（外正内负）——与边缘过渡同源；
    · alpha(p) = Σ_s w_s · f_s(t(p))（解析圆角矩形距离场 + 轮廓法线角向混合）。

    实现逐字复用 -07 候选档 `make_node_contour_candidates.py`（已实测验证；`cn()` 惰性 import）。
    """
    c = cn()
    a = np.asarray(src.getchannel("A")).astype(np.float64)
    rect = c.rect_of(a)                                    # 50% 交叉矩形（sub-pixel）
    prof, _band = c.collect_profiles(a, rect, RADIUS + 2)   # 直线带 = 去角 (r+2) 的中央区
    fields = c.shape_fields(src.size[0], src.size[1], rect, (RADIUS,) * 4)
    al = np.rint(np.clip(c.synth(prof, fields), 0, 255)).astype(np.uint8)
    assert al.shape == a.shape, (al.shape, a.shape)
    return al, rect, (RADIUS,) * 4, prof


def build(kind, state):
    """从 原形备份 读原件 → ① 轮廓解析化 → ② 改色 →（③ on 提亮档）→（④ select 描边）。

    不读 krkr 侧，故幂等；几何与柔光全部来自**该件自身**（自锚），与 -05/-07 的 `recolor` /
    `ON_GAIN` / `inner_stroke` 口径共用同一套函数，只在其**前面**插入第①步。
    返回 dict：src / shaped（仅 alpha 换过）/ base（无描边）/ out（最终）/ alpha / rect / radii / prof。
    """
    src = Image.open(BACKUP / f"x_ui_node_{kind}_{state}.png").convert("RGBA")
    hue, sat, vmul, stroke = params_of(kind, state)
    # ① 轮廓解析化（只改 alpha；RGB 保持原件）
    al, rect, radii, prof = analytic_alpha(src)
    shaped = Image.merge("RGBA", (*src.convert("RGB").split(), Image.fromarray(al, "L")))
    # ② 改色（③ 的 on 提亮档已折进 sat/vmul）
    base = recolor(shaped, hue=hue, sat=sat, vmul=vmul)
    # ④ select：2px 内描边（画在**解析化后**的 alpha 上）
    out = inner_stroke(base, stroke, STROKE_W) if stroke else base
    return {"src": src, "shaped": shaped, "base": base, "out": out,
            "alpha": al, "rect": rect, "radii": radii, "prof": prof,
            "stroke": stroke}



def state_delta(off_img, on_img, thr=STATE_THR):
    """两态差：掩码 = 两态 alpha 均 > thr；返回 (mean(逐像素三通道均差), max(逐像素单通道最大差), n)。"""
    po, pn = off_img.load(), on_img.load()
    W, H = off_img.size
    a3, mx = [], []
    for y in range(H):
        for x in range(W):
            r, g, b, a = po[x, y]
            r2, g2, b2, a2 = pn[x, y]
            if a > thr and a2 > thr:
                dr, dg, db = abs(r - r2), abs(g - g2), abs(b - b2)
                a3.append((dr + dg + db) / 3.0)
                mx.append(max(dr, dg, db))
    if not a3:
        return 0.0, 0, 0
    return sum(a3) / len(a3), max(mx), len(a3)


def params_of(kind, state):
    """该 (kind, state) 实际使用的 (hue, sat, vmul, stroke)——与 build() 逐字共用，避免口径漂移。"""
    hue, sat, vmul, stroke = SPEC[kind]
    if state == "on":
        g, s = ON_GAIN[kind]
        sat, vmul = sat * s, vmul * g
    return hue, sat, vmul, stroke


def straight_band(W, H, rect, radii):
    """直边带（与候选档同口径）：四条边中央区，去掉四角 (max(radii)+3)。"""
    x0, x1, y0, y1 = rect
    rmax = int(max(radii)) + 3
    X = (np.arange(W) + 0.5)[None, :]
    Y = (np.arange(H) + 0.5)[:, None]
    return (((X >= x0 + rmax) & (X <= x1 - rmax) & (Y >= y0 - 6) & (Y <= y1 + 6))
            | ((Y >= y0 + rmax) & (Y <= y1 - rmax) & (X >= x0 - 6) & (X <= x1 + 6)))


def bottom_solid_row(alpha, rect):
    """末端的「实体行」= 该行中央带 alpha 中位 >= SOLID_THR 的**最后一行**（底边所在行）。"""
    x0, x1 = int(rect[0]) + 20, int(rect[1]) - 19
    for y in range(alpha.shape[0] - 1, -1, -1):
        if np.median(alpha[y, x0:x1]) >= SOLID_THR:
            return y
    return None


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def md5_file(p):
    return md5_bytes(Path(p).read_bytes())


def hexof(rgb):
    return "#%02X%02X%02X" % rgb


# ---------------------------------------------------------------- 主流程
def main():
    if not BACKUP.is_dir():
        print("FATAL: 缺 原形备份 目录:", BACKUP)
        return 1
    EVID7.mkdir(parents=True, exist_ok=True)

    before = {}      # (kind,state) -> dict
    fails = []

    for kind in KINDS:
        for state in STATES:
            key = (kind, state)
            fn = f"x_ui_node_{kind}_{state}.png"
            b = build(kind, state)

            # 保存（RGBA 真彩、不做调色板量化）
            dst = ASSETS / fn
            b["out"].save(dst, optimize=True, compress_level=9)

            tgt = Image.open(BACKUP / fn).convert("RGBA")     # 原件（原形备份）
            back = Image.open(dst).convert("RGBA")            # 盘上读回
            b.update({
                "fn": fn, "m0": md5_file(BACKUP / fn), "m1": md5_file(dst),
                "size": (tgt.size, back.size), "out": back,
                "a0_md5": md5_bytes(tgt.getchannel("A").tobytes()),
                "a1_md5": md5_bytes(back.getchannel("A").tobytes()),
                "alpha_same": b["alpha"].tobytes() == back.getchannel("A").tobytes(),
                "alpha_orig_same": tgt.getchannel("A").tobytes() == back.getchannel("A").tobytes(),
                "fill0": tgt.convert("RGB").getpixel(SAMPLE),
                "fill1": back.convert("RGB").getpixel(SAMPLE),
                "orig_alpha": np.asarray(tgt.getchannel("A")).astype(np.float64),
            })
            before[key] = b

    # ---------------- 自检 ----------------
    print("=" * 78)
    print("自检 ① 像素尺寸（应与原件一致）")
    for key, d in before.items():
        ok = d["size"][0] == d["size"][1]
        if not ok:
            fails.append(f"{d['fn']} 尺寸变化 {d['size']}")
        print("   %-32s %s -> %s  %s" % (d["fn"], d["size"][0], d["size"][1], "OK" if ok else "FAIL"))

    print("自检 ② alpha 通道（① 六件 alpha == 轮廓解析化的解析结果；② 与原件 alpha 已不同）")
    for key, d in before.items():
        ok = d["alpha_same"]
        if not ok:
            fails.append(f"{d['fn']} alpha != 解析结果")
        print("   %-32s 解析 alpha md5 %s == 盘上 %s  %s  ｜ 与原件 alpha %s"
              % (d["fn"], md5_bytes(d["alpha"].tobytes())[:16], d["a1_md5"][:16],
                 "OK(逐字节一致)" if ok else "FAIL",
                 "已不同(解析化生效)" if not d["alpha_orig_same"] else "相同(!)"))

    print("自检 ③ _off 与 _on 仍不同（状态区分力）")
    for kind in KINDS:
        mo = before[(kind, "off")]["m1"]
        mn = before[(kind, "on")]["m1"]
        ok = mo != mn
        if not ok:
            fails.append(f"{kind}: off==on")
        print("   %-10s off %s / on %s  %s" % (kind, mo[:12], mn[:12], "OK(不同)" if ok else "FAIL(退化成同图)"))

    print("自检 ④ 实测 fill 色 @ %s（容差 ±%d，仅 _off 有期望值）" % (str(SAMPLE), TOL))
    for kind in KINDS:
        for state in STATES:
            d = before[(kind, state)]
            line = "   %-10s %-3s %s -> %s" % (kind, state, hexof(d["fill0"]), hexof(d["fill1"]))
            if state == "off":
                e = EXPECT_OFF[kind]
                dd = max(abs(e[i] - d["fill1"][i]) for i in range(3))
                if dd > TOL:
                    fails.append(f"{kind}_off fill 偏差 {dd}")
                line += "  期望 %s 偏差 %d/255  %s" % (hexof(e), dd, "OK" if dd <= TOL else "FAIL")
            print(line)

    print("自检 ⑤ md5：**六件都必须已变（解析化生效）**，并与 GOLD_MD5 锁定值一致")
    for key, d in before.items():
        fn = d["fn"]
        ok = d["m1"] != PREV_MD5[fn]              # 解析化必须真的生效
        if not ok:
            fails.append("%s md5 未变（解析化未生效）" % fn)
        gold = GOLD_MD5[fn]
        gold_ok = (gold == "PENDING") or (gold == d["m1"])
        if not gold_ok:
            fails.append("%s 与 GOLD_MD5 不一致" % fn)
        print("   %-32s 改前 %s  改后 %s  %s  | GOLD %s"
              % (fn, PREV_MD5[fn][:12], d["m1"][:12],
                 "OK" if ok else "FAIL", "待填" if gold == "PENDING" else ("OK" if gold_ok else "FAIL")))

    print("自检 ⑥ RGB 一致性 / 描边只改环带（口径：alpha 不参与 recolor ⇒ 两张同 RGB 不同 alpha 的图"
          " 必得同一 RGB）")
    for key, d in before.items():
        kind, state = key
        hue, sat, vmul, stroke = params_of(kind, state)
        # 独立复核路径：同 RGB、alpha 全 0 的图跑同一套 recolor ⇒ RGB 必须与「原件 → recolor」一致
        rgb_only = Image.merge("RGBA", (*d["src"].convert("RGB").split(),
                                        Image.new("L", d["src"].size, 0)))
        ref = recolor(rgb_only, hue=hue, sat=sat, vmul=vmul)
        got = np.asarray(d["out"].convert("RGB"), dtype=np.int16)
        exp = np.asarray(ref.convert("RGB"), dtype=np.int16)
        if stroke:
            cov = stroke_coverage(d["out"].getchannel("A"), width=STROKE_W)
            inside = cov > 0
            outside_bad = int((np.abs(got - exp)[~inside] > 0).sum())
            base_a = np.asarray(d["base"].getchannel("A")).tobytes()
            alpha_ok = (base_a == d["out"].getchannel("A").tobytes())
            ring_n = int(inside.sum())
            if not alpha_ok:
                fails.append("%s 描边改了 alpha" % d["fn"])
            if outside_bad:
                fails.append("%s 环带外 RGB 被改动 %d px" % (d["fn"], outside_bad))
            print("   %-32s 环带 %4d px ｜ 环带外 RGB 改动 %d px %s ｜ alpha == 同档无描边件 %s"
                  % (d["fn"], ring_n, outside_bad, "OK" if not outside_bad else "FAIL",
                     "OK(逐字节)" if alpha_ok else "FAIL"))
        else:
            bad = int((np.abs(got - exp) > 0).sum())
            if bad:
                fails.append("%s RGB != recolor(原件) 的 %d px" % (d["fn"], bad))
            print("   %-32s 无描边 ｜ RGB == recolor(原件) 第 %d px 不符 %s"
                  % (d["fn"], bad, "OK(逐字节)" if not bad else "FAIL"))

    print("自检 ⑦ 半径实测（相切一维搜索口径，非 45°）—— 四角应 ≈ %.1f（容差 ±%.1f）" % (RADIUS, RADIUS_TOL))
    for key, d in before.items():
        a = np.asarray(d["out"].getchannel("A")).astype(np.float64)
        c = cn()
        rm = c.rect_of(a)
        rr, r45 = {}, {}
        for cc in ("TL", "TR", "BR", "BL"):
            R, rms, n = c.radius_corner(a, rm, cc)
            rr[cc] = (R, rms, n)
            v = c.corner_diag_radius(a, rm, cc)
            r45[cc] = v if v else -1.0
        dev = max(abs(rr[cc][0] - RADIUS) for cc in rr)
        ok = dev <= RADIUS_TOL
        if not ok:
            fails.append("%s 半径偏差 %.3f > %.1f" % (d["fn"], dev, RADIUS_TOL))
        print("   %-32s r=%s ｜ 最大偏差 %.3f %s ｜ 45°(有偏仪器，仅相对比较) %s"
              % (d["fn"], " ".join("%s%.2f" % (cc, rr[cc][0]) for cc in ("TL", "TR", "BR", "BL")),
                 dev, "OK" if ok else "FAIL",
                 " ".join("%s%.2f" % (cc, r45[cc]) for cc in ("TL", "TR", "BR", "BL"))))

    print("自检 ⑧ 底边缺口：末端实体行（该行中央带 alpha 中位 >= %d 的最后一行）逐列无缺口" % SOLID_THR)
    for key, d in before.items():
        a = np.asarray(d["out"].getchannel("A")).astype(np.float64)
        a0 = d["orig_alpha"]
        x0, x1 = int(d["rect"][0]) + 20, int(d["rect"][1]) - 19
        row_o, row_n = bottom_solid_row(a0, d["rect"]), bottom_solid_row(a, d["rect"])
        seg0 = a0[row_o, x0:x1] if row_o is not None else np.array([0.0])
        seg = a[row_n, x0:x1] if row_n is not None else np.array([0.0])
        holes = np.where(seg < SOLID_THR)[0]
        if len(holes):
            fails.append("%s 底边 y=%d 仍有 %d 列缺口" % (d["fn"], row_n, len(holes)))
        line = ("   %-32s 改前 y=%s min=%.0f ｜ 改后 y=%s min=%.0f 缺口列=%d %s"
                % (d["fn"], row_o, seg0.min(), row_n, seg.min(), len(holes),
                   "OK" if not len(holes) else "FAIL"))
        if key == ("select", "off"):
            v0, v1 = int(a0[56, NOTCH_X]), int(a[56, NOTCH_X])
            line += " ｜ ★ x=%d：改前 %d ⇒ 改后 %d" % (NOTCH_X, v0, v1)
            if v1 < SOLID_THR:
                fails.append("select_off x=%d 仍 < %d" % (NOTCH_X, SOLID_THR))
        print(line)

    print("自检 ⑨ 解析化回归：直边带内 |Δalpha| 统计（带 = 去角 rmax+3 的中央区；应 ≥%.0f%% 像素 |Δ|≤2）"
          % (STRAIGHT_MIN_LE2 * 100))
    for key, d in before.items():
        a = np.asarray(d["out"].getchannel("A")).astype(np.float64)
        band = straight_band(a.shape[1], a.shape[0], d["rect"], d["radii"])
        dev = np.abs(a - d["orig_alpha"])[band]
        le2 = float((dev <= 2).sum()) / max(dev.size, 1)
        kat = np.argwhere((np.abs(a - d["orig_alpha"]) * band) >= dev.max())
        loc = (int(kat[0][1]), int(kat[0][0])) if len(kat) else (-1, -1)
        ok = le2 >= STRAIGHT_MIN_LE2
        if not ok:
            fails.append("%s 直边 |Δ|≤2 占比 %.1f%% < %.0f%%" % (d["fn"], le2 * 100, STRAIGHT_MIN_LE2 * 100))
        print("   %-32s |Δ|max=%3.0f@%s mean=%.2f ｜ >2 %4d / >4 %4d / >8 %3d / n=%5d ｜"
              " |Δ|≤2 占 %5.1f%% %s"
              % (d["fn"], dev.max(), loc, dev.mean(), int((dev > 2).sum()), int((dev > 4).sum()),
                 int((dev > 8).sum()), dev.size, le2 * 100, "OK" if ok else "FAIL"))

    print("自检 ⑩ 描边几何（select 件：覆盖率级数 / 实体面厚度 / 沿解析轮廓法线的径向宽度）")
    SEL_RECT = before[("select", "off")]["rect"]
    SEL_RADII = before[("select", "off")]["radii"]
    for state in STATES:
        o_img = before[("select", state)]["out"]
        cov = stroke_coverage(o_img.getchannel("A"))
        nz = cov[cov > 0]
        alpha = np.asarray(o_img.getchannel("A"))
        solid = alpha >= SOLID_THR
        runs = []
        for x in range(80, 181):
            ys = np.where(solid[:, x])[0]
            y0, n = ys.min(), 0
            while y0 + n < solid.shape[0] and cov[y0 + n, x] >= 0.5:
                n += 1
            runs.append(n)
        runs = np.array(runs)
        lv = len(np.unique(np.round(cov, 3)))
        rw = cn().ring_width_radial(o_img, before[("select", state)]["rect"], before[("select", state)]["radii"])
        stra, arc = rw["直边"], rw["圆角弧"]
        ok = (abs(stra["med"] - STROKE_W) <= 0.05 and arc["med"] <= 2.3
              and arc["max"] <= 3.0 and arc["n_gt3"] == 0 and stra["n_gt3"] == 0)
        if not ok:
            fails.append("select_%s 描边几何不符 %s / %s" % (state, stra, arc))
        print("   select_%-3s 覆盖率非零像素=%5d  取值级数=%3d  最大覆盖=%.2f ｜ 顶边中段（x80-180）实体面内带厚"
              " min=%d max=%d 极差=%d（目标 2/2/0）"
              % (state, len(nz), lv, cov.max(), runs.min(), runs.max(), runs.max() - runs.min()))
        print("              径向宽度 直边 p05/med/p95/max=%.3f/%.3f/%.3f/%.3f（>3 的 %d/%d）"
              " ｜ 圆角弧 %.3f/%.3f/%.3f/%.3f（>3 的 %d/%d）  %s"
              % (stra["p05"], stra["med"], stra["p95"], stra["max"], stra["n_gt3"], stra["n"],
                 arc["p05"], arc["med"], arc["p95"], arc["max"], arc["n_gt3"], arc["n"],
                 "OK" if ok else "FAIL"))
        if runs.min() < 2 or runs.max() > 3:
            fails.append("select_%s 描边厚度不均 %s" % (state, list(runs)))

    print("自检 ⑪ 两态差 ΔRGB（掩码：两态 alpha 均 >%d；均=逐像素三通道均差，最大=逐像素单通道最大差）"
          % STATE_THR)
    for kind in KINDS:
        o_src = before[(kind, "off")]["src"]      # 原件 _off（原形备份）
        n_src = before[(kind, "on")]["src"]       # 原件 _on（原形备份）
        o_new = before[(kind, "off")]["out"]      # 改后 _off（未受提亮档影响）
        n_new = before[(kind, "on")]["out"]       # 改后 _on
        m0, x0, c0 = state_delta(o_src, n_src)
        m1, x1, c1 = state_delta(o_new, n_new)
        ok = (m1 >= STATE_MEAN_MIN) and (x1 >= STATE_MAX_MIN)
        if not ok:
            fails.append("%s 两态差不足 均=%.2f 最大=%d" % (kind, m1, x1))
        print("   %-8s n=%5d  改前 %6.2f / %3d  →  改后 %6.2f / %3d   目标 均≥%.0f 且 最大≥%d  %s"
              % (kind, c1, m0, x0, m1, x1, STATE_MEAN_MIN, STATE_MAX_MIN, "OK" if ok else "FAIL"))
        before[(kind, "off")]["delta"] = (m0, x0, m1, x1)
        # V(单通道) 顶到 255 的像素占比（防过曝自证：g 会让亮底死白）
        pn = n_new.load()
        W, H = n_new.size
        tot = sum(1 for y in range(H) for x in range(W) if pn[x, y][3] > STATE_THR)
        sat255 = sum(1 for y in range(H) for x in range(W)
                     if pn[x, y][3] > STATE_THR and max(pn[x, y][:3]) == 255)
        print("            _on 不透明区单通道==255 的像素：%d/%d (%.2f%%)" % (sat255, tot, 100.0 * sat255 / max(tot, 1)))

    print("自检 ⑫ 幂等：重建一遍（仍从 原形备份 读，同一 PNG 编码参数）⇒ 六件应与本次落盘**逐字节相同**")
    for key, d in before.items():
        fn = d["fn"]
        buf = io.BytesIO()
        build(*key)["out"].save(buf, format="PNG", optimize=True, compress_level=9)
        again = buf.getvalue()
        ok = again == (ASSETS / fn).read_bytes()
        if not ok:
            fails.append("%s 重建结果与落盘不同（非幂等）" % fn)
        print("   %-32s 重建 PNG md5 %s == 落盘 md5 %s  %s"
              % (fn, md5_bytes(again)[:16], d["m1"][:16], "OK" if ok else "FAIL"))

    # ---------------- 对照图 ----------------
    make_sheet(before)
    print("对照图：", SHEET)

    print("=" * 78)
    if fails:
        print("结果：**不通过** %d 项" % len(fails))
        for f in fails:
            print("   -", f)
        return 1
    print("结果：**全部自检通过**")
    return 0


# ---------------------------------------------------------------- 对照图
def make_sheet(before):
    order = [(k, s) for k in KINDS for s in STATES]
    gap = 22
    margin = 22
    widths = [before[key]["src"].size[0] for key in order]
    total_w = margin * 2 + sum(widths) + gap * (len(order) - 1)
    col_h = max(before[key]["src"].size[1] for key in order)

    head_h = 78                      # 列头（类别 + 状态 + 文件名）
    band_title_h = 34                # 「改前 / 改后」带标题
    fill_h = 28                      # 每列下方的实测色值
    title_h = 76
    zoom_h = 0
    zoom_src = None
    for key in order:
        if key[0] == "select":
            zoom_src = key
            break
    zone = None
    if zoom_src:
        zone = before[zoom_src]
        zcrop = (0, 18, 46, 47)      # select 左边中段：含描边区
        zw, zh = zcrop[2] - zcrop[0], zcrop[3] - zcrop[1]
        zoom_scale = 5
        zoom_h = zh * zoom_scale + 72

    row_h = 96                        # 「态差对照」每类一行
    state_h = 62 + 3 * row_h + 30

    H = title_h + head_h + (band_title_h + col_h + fill_h + 26) * 2 + zoom_h + state_h + margin
    sheet = Image.new("RGB", (total_w, H), BG)
    d = ImageDraw.Draw(sheet)

    f_title = font(30, True)
    f_h = font(22, True)
    f_col = font(17)
    f_colb = font(17, True)
    f_note = font(16)

    y = margin
    d.text((margin, y), "流程图节点素材 · 方案 A ＋ 轮廓解析化（r=16）· 前后对照（1:1 原始像素）",
           font=f_title, fill=FG)
    d.text((margin, y + 38),
           "取样点 %s（容差 ±%d/255）｜ 底色 %s（与实际流程图同量级）｜ 改前取自 原形备份\\ 原件"
           "｜ 管线：原件 →① 轮廓解析化(r=16/逐边柔光剖面) →② 改色 →③ on 提亮 →④ select 描边"
           % (str(SAMPLE), TOL, str(BG)),
           font=f_note, fill=FG_DIM)
    y += title_h

    # 列头
    xs = []
    x = margin
    for i, key in enumerate(order):
        d_ = before[key]
        w = widths[i]
        xs.append(x)
        d.text((x, y), "%s · %s" % (KIND_CN[key[0]], key[1]), font=f_colb, fill=FG)
        d.text((x, y + 22), d_["fn"], font=f_col, fill=FG_DIM)
        x += w + gap
    y += head_h

    def band(label, sub, pick, y0):
        d.text((margin, y0), label, font=f_h, fill=HL)
        d.text((margin + ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(label, font=f_h) + 14, y0 + 4),
               sub, font=f_note, fill=FG_DIM)
        yy = y0 + band_title_h
        for i, key in enumerate(order):
            im = before[key][pick]
            sheet.paste(im, (xs[i], yy), im)
            d.rectangle([xs[i] - 1, yy - 1, xs[i] + im.size[0], yy + im.size[1]], outline=(70, 84, 104))
            col = before[key]["fill0" if pick == "src" else "fill1"]
            d.text((xs[i], yy + col_h + 6), hexof(col), font=f_col, fill=FG if pick != "src" else FG_DIM)
        return yy + col_h + fill_h + 26

    y = band("改前（原形备份 \\ 原件）", "三类几乎同色，肉眼不可辨", "src", y)
    y = band("改后（方案 A：设 H/S · 乘 V ＋ 选择支 2px 深蓝内描边）",
             "冰蓝实底 / 偏青蓝 + 描边 / 淡紫底", "out", y)

    # 描边放大带（5× 最近邻，只为看清 2px 描边）
    if zoom_src:
        d_ = zone
        d.text((margin, y), "描边放大（5× 最近邻，%s 左边中段）" % d_["fn"], font=f_h, fill=HL)
        y += 34
        zw = 46
        zh = 29
        for j, (lab, pick) in enumerate((("改前", "src"), ("改后", "out"))):
            src = before[zoom_src][pick]
            crop = src.crop((0, 18, 46, 47)).resize((zw * 5, zh * 5), Image.NEAREST)
            xx = margin + j * (zw * 5 + 40)
            sheet.paste(crop, (xx, y), crop)
            d.text((xx, y + zh * 5 + 6), lab, font=f_colb, fill=FG)
        y += zh * 5 + 40

    # ---- 态差对照（每类一行：左 _off 右 _on 1:1 并排，标出 ΔRGB 均/最大） ----
    d.text((margin, y), "态差对照（改后）· 悬停反馈必须有差别", font=f_h, fill=HL)
    d.text((margin, y + 30),
           "ΔRGB 掩码 = 两态 alpha 均 >%d ｜ 均 = 逐像素三通道均差 ｜ 最大 = 逐像素单通道最大差 ｜ 目标 均≥%.0f 且 最大≥%d"
           % (STATE_THR, STATE_MEAN_MIN, STATE_MAX_MIN), font=f_note, fill=FG_DIM)
    y += 62
    LW, CW, AW = 150, 292, 46
    x_off = margin + LW
    x_on = x_off + CW + AW
    for kind in KINDS:
        o = before[(kind, "off")]["out"]
        n = before[(kind, "on")]["out"]
        m0, x0, m1, x1 = before[(kind, "off")]["delta"]
        d.text((margin, y + 18), "%s · %s" % (KIND_CN[kind], kind), font=f_colb, fill=FG)
        for xx, im in ((x_off, o), (x_on, n)):
            sheet.paste(im, (xx, y), im)
            d.rectangle([xx - 1, y - 1, xx + im.size[0], y + im.size[1]], outline=(70, 84, 104))
        d.text((x_off, y + o.size[1] + 5), "_off（常态，未改）", font=f_col, fill=FG_DIM)
        d.text((x_on, y + n.size[1] + 5), "_on（悬停，已提亮）", font=f_col, fill=FG_DIM)
        d.text((x_off + o.size[0] + 8, y + 22), "→", font=f_h, fill=HL)
        d.text((x_on + n.size[0] + 22, y + 12),
               "ΔRGB 均 %.2f / 最大 %d" % (m1, x1), font=f_colb, fill=OK)
        d.text((x_on + n.size[0] + 22, y + 34),
               "(改前 %.2f / %d)" % (m0, x0), font=f_col, fill=FG_DIM)
        y += row_h

    sheet.save(SHEET)
    print("   对照图写出：%s  %s" % (SHEET, sheet.size))


if __name__ == "__main__":
    sys.exit(main())
