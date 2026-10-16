# -*- coding: utf-8 -*-
import io, os
ROOT=r"E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
OUT=os.path.join(ROOT,"_工作","M34_资产盘点.md")

T = r"""# M34 资产盘点 —— UI 素材保留/弃用边界

> 任务：为「弃用现有全部 UI 素材，只保留标题 logo / CG 画廊页 / Fragment 页所需素材」做资产盘点。
> 素材目录：`UI组\krkr\assets\ui\`（**292 件 / 54.942 MB**，脚本实测 `os.path.getsize` 求和）
> 布局契约：`layout\_schema.md`（asset 串 = `ui/<文件名>.png`；物理文件名 = asset 串 basename）
> 引用矩阵（实测产物）：`_工作\M34_资产引用矩阵.tsv`（292 行，每件 → 引用屏 / 引用元素 / 字段）
> 生成脚本：`_工作\M34_refmatrix.py`（建矩阵）、`M34_analyze.py` / `M34_analyze2.py` / `M34_final.py`（统计）
> **本报告只盘点，不删任何素材。** 所有数字来自脚本实测，非估算。

---

## 〇、结论摘要（先看这里）

| 项 | 件数 | 体积 |
| --- | ---: | ---: |
| 素材总量 | **292** | **54.942 MB** |
| **必须保留**（标题屏 + gallery + fragment 引用并集） | **18** | **6.612 MB** |
| **可弃用**（未被这三屏引用） | **274** | **48.329 MB** |
| 其中「原版件（无 `x_` 前缀）」 | 83 | 19.484 MB |
| 其中「转场遮罩 `x_mask_*`」 | 36 | 14.533 MB |

- **保留屏与弃用屏之间不存在共用素材**（保留并集 ∩ 其它屏引用 = **0 件**）——即三屏所需素材都是各自专属的，整批弃用不会误伤保留屏。
- 但**弃用屏之间存在 14 件跨屏共用素材**（如系统屏通用底板 `x_gen_sd_9-1_bg.png` 被 8 屏共用），若主代理将来决定保留其中任一屏，这 14 件不能只删一半（见 §四）。
- **原版件（无前缀）83 件中，没有任何一件被保留屏（title/gallery/fragment）引用**（实测交集为空）——就保留屏而言，原版件可整体弃用；唯一被引用的是 `panel_frame.png`，只被 `chapter`/`dialog` 两屏用（且它其实是 UI 组自制件，非原版提取件）。
- **契约风险**：删文件不会让 krkr 崩溃（`ui_asset.tjs` 缺件登记 + 占位），但会 **破坏 `verify_ui.py` 的引用完整性检查**，且 `ui_layout.tjs` 仍引用全部 16 屏的素材。若只删素材不删屏，校验必挂（见 §五）。

---

## 一、logo 定位（题目要求先找）

- **标题 logo 物理文件 = `x_gen_logo.png`**（465,740 B / 0.444 MB）。
- 被 `01_title.json` 的 **`title.logo`** 元素引用：`kind=image`、`asset="ui/x_gen_logo.png"`、`x=60 y=45 w=900 h=317`、`source` 注明派生自 `生图入料\生成结果\游戏logo重置.png`。
- 旧 logo **`x_title_logo.png`**（74,118 B）已被 M20 取代，**全项目零引用**（矩阵中「零屏引用」），属可弃用件。

---

## 二、分组统计表（按前缀 / 实测）

| 前缀族 | 件数 | 体积 | 来源 | 用途 / 被引用屏 | 处置 |
| --- | ---: | ---: | --- | --- | --- |
| **`x_bg_system.png`** | 1 | 2.597 MB | AI 生图派生（资源组超分 `bg63.png` 派生） | 标题屏满幅背景，仅 `title` | **保留** |
| **`x_gen_logo.png`** | 1 | 0.444 MB | AI 生图派生（`游戏logo重置.png`） | 标题 logo，仅 `title` | **保留** |
| **`x_gen_menu*`** | 14 | 0.782 MB | AI 生图派生（`系统屏底图重置3.png`，M27 重切） | 标题底部 7 键 × 常态/悬停，仅 `title` | **保留** |
| **`x_gen_gallerypage.png`** | 1 | 1.323 MB | AI 生图派生 | CG 画廊满幅底图，仅 `gallery` | **保留** |
| **`x_gen_fragpage.png`** | 1 | 1.465 MB | AI 生图派生 | Fragment 页满幅底图，仅 `fragment` | **保留** |
| `x_gen_sd_*` | 71 | 5.201 MB | AI 生图派生（系统屏素材，M33 归一化） | 系统屏控件：导航/底图/存档槽/配置/音乐/确认/加载；被 `sysmenu,confirm,loading,save,load,config,backlog,music` 8 屏引用 | 弃用 |
| `x_gen_fc_*` | 57 | 4.486 MB | AI 生图派生（流程图控件） | 流程图控件（FC-1..4 系列：节点条、缩放、播放、筛选等），仅 `flowchart` | 弃用 |
| `x_gen_dialog*` | 2 | 1.654 MB | AI 生图派生 | 对话框整图（`x_gen_dialog.png` 零屏引用、`x_gen_dialog2.png` 被 `dialog`） | 弃用 |
| `x_gen_dicon_*` | 9 | 0.046 MB | AI 生图派生 | 对话框快捷图标（快速存读/跳过/关闭等），仅 `dialog` | 弃用 |
| `x_gen_ed_*` | 2 | 2.105 MB | AI 生图派生 | 片尾背景 + 角色层，仅 `ending` | 弃用 |
| `x_gen_flownode_*` | 4 | 0.416 MB | AI 生图派生（M22） | 流程图 4 种节点条（普通/BadEnd/重要/GoodEnd），仅 `flowchart` | 弃用 |
| `x_gen_icon_*` | 9 | 0.334 MB | AI 生图派生（M22） | 右键图标浮层 9 功能图标，仅 `sysicons` | 弃用 |
| `x_title_logo.png` | 1 | 0.071 MB | M9 自制（中文标题重绘） | 旧 logo，**零引用**（被 `x_gen_logo` 取代） | 弃用 |
| `x_mask_*` | 36 | 14.533 MB | UI 组自制（18 组 × `_1x`/`_full`） | 转场灰度遮罩，**零屏引用**；`startup.tjs` 硬编码默认用 `x_mask_rule000_full.png` | 弃用（**契约件，见 §五**） |
| **原版件（无 `x_` 前缀）** | **83** | **19.484 MB** | 原版《我们没有翅膀》提取贴图（A 类，逐字节 1:1） | 仅 `chapter`（`panel_frame`）、`dialog` 等引用；**无一被保留屏引用** | 弃用（**契约风险，见 §五**） |
| **合计** | **292** | **54.942 MB** | | | |

> 原版件按族细分（实测）：`sr_01..24` 24 件 / 10.649 MB（片尾角色卡，最大族）、`tl1_bg/tl1_bg1/tl1_bg2/tl2_bg1` 4 件 / 5.191 MB（原版标题背景）、`ec5_bg` 1.395 MB、缩略图族 6 件 / 1.155 MB、`dlg_bg_26..28` 0.684 MB、其余（粒子/名字框/九宫格原料/滚动条等）合计约 0.41 MB。

---

## 三、保留清单（18 件 / 6.612 MB）

### 3.1 标题屏（16 件 / 3.824 MB）
| 文件 | 体积 | 引用元素 |
| --- | ---: | --- |
| `x_gen_logo.png` | 0.444 MB | `title.logo`（**标题 logo 本体**） |
| `x_bg_system.png` | 2.597 MB | `title.bg`（满幅背景） |
| `x_gen_menu_{1..7}_*.png`（常态 7 + 悬停 7 = 14 件） | 合计 0.782 MB | `title.menu_img_*` 与 `title.menu_hit_*.state_assets` |

> 注：用户口径为「标题 **logo** 相关」。严格只算 logo 本体仅 `x_gen_logo.png` 1 件；但 `01_title.json` 同时依赖 `x_bg_system.png`（背景）与 14 件菜单按钮，**若整屏要能用，这 16 件应一并保留**。菜单按钮图上已烘焙中文（开始游戏/继续游戏/读取存档/流程图/鉴赏/设置/退出），删后标题屏无法重建（需重新生图）。

### 3.2 CG 画廊屏（1 件 / 1.323 MB）
- `x_gen_gallerypage.png`（`27_gallery.json` 的 `gallery.bg`，满幅 1920×1080）。
- 该屏的预览大框是动态层（`asset=null`，运行期由编程组填当前 CG），不依赖静态素材。

### 3.3 Fragment 屏（1 件 / 1.465 MB）
- `x_gen_fragpage.png`（`31_fragment.json` 的 `fragment.bg`，满幅 1920×1080，自带标题与 40 格面板）。
- 格内标题为引擎绘字（取自 `spine.json`），不依赖静态素材。

---

## 四、共用素材清单

### 4.1 保留屏 ∩ 弃用屏 —— **0 件（实测无交集）**
三屏（title/gallery/fragment）引用的 18 件素材，没有任何一件被其它 13 屏引用。**因此就「保留屏不被误伤」而言，其余 274 件可安全整批弃用。**

### 4.2 弃用屏之间的跨屏共用（14 件，**不可只删一半**）
若主代理日后决定保留其中任一屏，这些件必须保留；若整批弃用则不受影响。

| 文件 | 体积 | 被引用屏（数量） |
| --- | ---: | --- |
| `x_gen_sd_9-1_bg.png` | 1.734 MB | backlog, config, confirm, load, loading, music, save, sysmenu（**8 屏**，系统屏通用满幅底板） |
| `x_gen_sd_1-1_back_off.png` | 25,781 B | config, load, music, save, sysmenu（5 屏，返回键常态） |
| `x_gen_sd_1-3_panel_frame.png` | 1.071 MB | backlog, load, music, save（4 屏，通用面板框） |
| `x_gen_sd_6-1_tab_off.png` | 27,922 B | config, load, save（3 屏） |
| `x_gen_sd_6-1_tab_on.png` | 26,205 B | config, load, save（3 屏） |
| `x_gen_sd_5-1_slot_empty.png` | 119,635 B | load, save |
| `x_gen_sd_5-1_slot_hover.png` | 130,129 B | load, save |
| `x_gen_sd_5-1_slot_sel.png` | 123,425 B | load, save |
| `x_gen_sd_5-2_pg1.png` ~ `pg4.png` | 各约 4 KB | load, save（各 2 屏） |
| `x_gen_sd_5-2_thumb_frame.png` | 94,726 B | load, save |
| `panel_frame.png` | 1,755 B | chapter, dialog（2 屏，九宫格通用窗框，**UI 组自制件**） |

### 4.3 代码（非屏）引用的素材
- `x_mask_rule000_full.png`：被 `krkr\game\startup.tjs` 的常量 `UI_TRANS_RULE` **硬编码**为默认转场遮罩（缺件时 `ui_transition.tjs` 会降级为内建 crossfade，不崩）。
- `x_mask_rule000_1x.png`：`UI组交接编程组.md` §五.2 **点名**的转场遮罩对（与上件成套，1920 基线实测尺寸）。
- 全族 `x_mask_*` 36 件在 `layout\screens\*` 中**零引用**，仅经代码/交接文档消费。

---

## 五、契约影响提示

1. **命名契约（`UI清单.md` §〇）**：layout 的 asset 串为 `ui/<原名>.png`，物理文件名 = asset 串 basename。**改名 = 破坏编程组调用**；删除则 `ui_asset.tjs` 登记缺件并画占位（不崩，但功能缺失）。
2. **`layout\_schema.md` §七 约束 3**：`image` 的 `asset` 文件必须存在于 `krkr/assets/ui/`，由 `verify_ui.py` 检查。**删素材但保留屏 → `verify_ui.py` 引用完整性检查必挂。**
3. **`ui_layout.tjs` 是生成物**，当前仍含全部 16 屏、引用全部素材。删素材前需先决定这些屏是否从 `layout/screens/` 移除并重跑 `gen_layout.py`，否则三处数据与素材集不一致。
4. **`UI组交接编程组.md` 点名清单**（改名/删除会破坏契约）：
   - §五.2：`x_mask_rule000_full.png`、`x_mask_rule000_1x.png`（转场遮罩）。
   - §五.4：5 件 P 模式（索引色）PNG —— `cf_frm_a` `nm_frm_a` `nm_frm_g` `sel00a` `sel00g`（若加载异常须用 `make_assets.py` 重出为 RGBA）。这 5 件均为**原版件**、当前零屏引用，但文档留有契约记录。
   - §一：交付贴图集路径 `UI组\krkr\assets\ui\`（文档记载为「119 件 / 14.57 MB」，**已过期**；实测现为 292 件 / 54.942 MB）。
5. **`verify_ui.py` 体积预算 48 MB**（`UI清单.md` §〇）：当前 54.942 MB **已超预算 6.94 MB**；若弃用 274 件后仅剩 6.612 MB，则余量充足。
6. **`复刻\`（HTML 1:1 复刻）** 与 krkr 侧共用同一批贴图（实测引用集与 screens 一致），弃用素材会同步影响复刻页显示。
7. **原版件提示**：原版件 83 件 / 19.484 MB 中，`sr_01..24`（10.649 MB，片尾角色卡）与 `tl*_bg`（5.191 MB，原版标题背景）体积最大；`tl*_bg` 曾被 `title.bg_art` 使用，但 M13/M20 后标题屏已改用 `x_bg_system` + `x_gen_logo`，故**保留屏对原版件零依赖**（实测交集为空）。主代理可据此放心弃用原版件，但需知悉：若后续要复用原版片尾角色卡/标题风景，需另从资源组重取。

---

## 六、可弃用清单小计（274 件 / 48.329 MB）

| 子族 | 件数 | 体积 |
| --- | ---: | ---: |
| 原版件（无前缀） | 83 | 19.484 MB |
| `x_mask_*`（转场遮罩） | 36 | 14.533 MB |
| `x_gen_sd_*`（系统屏控件） | 71 | 5.201 MB |
| `x_gen_fc_*`（流程图控件） | 57 | 4.486 MB |
| `x_gen_ed_*`（片尾） | 2 | 2.105 MB |
| `x_gen_dialog*`（对话框） | 2 | 1.654 MB |
| `x_gen_flownode_*`（流程图节点条） | 4 | 0.416 MB |
| `x_gen_icon_*`（右键图标） | 9 | 0.334 MB |
| `x_title_logo.png`（旧 logo，零引用） | 1 | 0.071 MB |
| `x_gen_dicon_*`（对话快捷图标） | 9 | 0.046 MB |
| **合计** | **274** | **48.329 MB** |

> 逐件明细见 `_工作\M34_资产引用矩阵.tsv`（含每件的体积、引用屏数、引用屏、引用元素与字段）。
"""
with io.open(OUT,"w",encoding="utf-8") as f:
    f.write(T)
print("WROTE", OUT, os.path.getsize(OUT), "bytes")
