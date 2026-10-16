# UI 组 → 编程组 · 交接说明

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（UI→编程组的逐功能交接手册；含历代回执与就地订正） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> 交接方：**UI 美术组**（M0–M8 模块） ｜ 接收方：**编程组**
> Issue：`ISSUE-20260919-11` ｜ 分支：`issue/ISSUE-20260919-11-greta-ui` ｜ 日期：2026-09-19
> 总纲依据：`..\00_项目总纲.md` §七 **I3**（UI 组 → 编程组的交付契约）、§一（三组边界）
> **本文件是编程组消费 UI 组成果的唯一入口**（配合 `UI清单.md` 与 `layout/_schema.md`）

---

## 一、你拿到了什么（5 类）

| # | 交付物 | 路径 | 说明 |
| --- | --- | --- | --- |
| 1 | **krkr 可用 UI 贴图集** | `UI组\krkr\assets\ui\` | **1359 件 / 100,604,112 B（95.94 MiB）**（★ **第 16 批 `ISSUE-20260930-06`（2026-09-30）现行实测**：本批**零新增素材** ⇒ 件数与字节不变，`verify_ui [6]` **通过**；下面保留的第 15 批读数「100,605,247 B / 余量 58,049 B ≈ 56.7 KiB」**已作废**）。★ **第 15 批留痕（历史）**：本批 ➜ 净增 **3 件 / +5,855 B**＝`x_ui_plusbtn_{off,over,press}.png`（44×44 RGBA ×3）；上句「1356 件 / 100,599,392 B / 余量 63,904 B」为**第 13 批读数**，已被第 15 批改写。全部 krkr 可直接 `loadImages` 加载。**体积预算**：`工具\verify_ui.py [6]` 上限 96 MB、实测 100,604,112 B（95.94 MiB）⇒ **余量 59,184 B ≈ 57.8 KiB**（**后续批次不得再增素材**）。
| 2 | **布局数据（唯一数据源）** | `UI组\layout\screens\*.json` → 生成 `krkr\game\ui_layout.tjs` | **17 屏 / 1428 元素**（★ **D-01 2026-10-01**〔`ISSUE-20261001-11`〕：`title` 屏补 6 件文字区热区 18→24 ⇒ **17 屏合计现行 1428**）（★★ **第 16 批 `ISSUE-20260930-06` 现行实测（2026-09-30）**：`flowchart` 屏因**番外独立层改纵向流水**净增 8 节点 × 3 件 ＝ **+24**，`config` 屏**删死行「播放影片」3 件** ⇒ 第 15 批的 **1401 → 1422**、`flowchart` 的 **272 → 296**、`config` 的 **470 → 467**；下句「第 15 批…＋10…1391 → 1401」为**上一批留痕（已作废）**）；五档＝**`screen1` 296 / `screen2` 116 / `ref150` 95 / `states` 109 / `frag` 128**（`screen1` 与第 15 批的 272 相比 **+24**）；`fc.p_text_tx.w` 398 → 300；浮层 1240×400、加号 y 618。**本行其余处的「1399 / 270 / 262 / 106 / 85 / 99 / 118 / 1404 / 274 / 111 / 130」均为第 12/13 批与第 15 批首轮读数，已作废；「272 / 1401」为第 15 批第 2 轮读数，本批亦已作废**）。★ **计法**：对 `layout/screens/_index.json` 列出的 17 屏逐屏 `len(elements)` 求和；`工具/gen_layout.py` 对该列表**原样透传**（只在缺 `z` 时补号、不改件数）⇒ `layout/ui_layout.json` 应为 **1428**〔★ D-01 2026-10-01：`title` 18→24〕）。⚠ **实测到的中间态**：三处产物在 `run_all.py` 中途会是 `states`/`frag` 预设态（`flowchart` **109/128** 件）—— 那是中间产物、**不是交付样例**；**以末尾「还原 screen1 ⇒ 最终三处产物」两步的落盘为准**（届时合计 **1428**、`flowchart` **296**）。改布局只改 `screens/*.json` 后重跑 `工具\gen_layout.py` | ★ **二审更正（ISSUE-20260928-07）**：上面的枚举**不全** —— 还漏了 `复刻\screen_index.js`（**编辑器用**屏清单，来源 `layout/screens/_index.json`）⇒ **删屏后必须重跑 `工具\emit_asset_index.py`**。本批首版就因漏跑它，导致编辑器屏选择器为空并抛 `TypeError`（一审抓出 Critical）；已修，并已把该步纳入 `run_all.py` 作常驻闸门。 |
| 3 | **TJS2 UI 组件库 + 可运行演示** | `UI组\krkr\game\*.tjs` | **16 个 `.tjs`**（★ **订正（2026-09-30 · `ISSUE-20260930-06`）**：原记「13 个」为陈旧读数；现为 **16 个**＝自动生成 3〔`ui_layout`／`ui_flow_data`／`ui_demo_script`〕＋ 手写 13，见 `UI组_交付总纲.md` §2.4）；**实机跑通**（`krkr.console.log` 无异常、**17 屏**全可见 —— ★ ISSUE-20260928-06 原记「15 屏」为陈旧读数；★ ISSUE-20260928-07 删 `ending` 后屏数以 `layout/screens/_index.json` 为准＝ **17 屏**） |
| 4 | **UI 清单（I3 契约）** | `UI组\UI清单.md` | 文件名 / 尺寸 / 九宫格或锚点 / 在 krkr 中的加载方式 / 对应原版 UI 元素，五列齐全 |
| 5 | **1:1 HTML 复刻** | `UI组\复刻\index.html`（+ **2 个专题页**：`flow.html`、`editor.html`） | 离线可双击；与 krkr 侧**逐屏一致**（同一份布局数据 + 同一批贴图）。★ ISSUE-20260928-06：原「+ 3 个专题页」中的 `fragment.html` **已随该屏删除**（`_selftest_states.html` 是自检页，不计入专题页） |

> ★★ **ISSUE-20260928-06（2026-09-28，用户裁定）：`fragment`（番外·Fragment 选择）屏已整体删除**（`layout/screens/_index.json` 屏数 **19 → 18**）。**编程组必读三点**：
> ① **番外入口改从流程图进** —— 番外 6 组内容已由**流程图屏 `flowchart` 的独立层**承载（动作 **`flow_layer`** ＋ `layer:"frag1".."frag6"`）。实测原 Fragment 页 40 格 **⊂** 流程图层 45 格、**文案 40/40 一致（**37 格字节完全相同**；另 **3 格**在流程图侧含**我方注入的硬断行** `\n`：`42_3` / `42_4` / `62_1b` —— 无字符增删）** ⇒ 删屏**零内容丢失**。
> ② **动作保留** —— `open_fragment`（krkr `ui_screens.tjs` 屏映射 ／ HTML `replica.js` 的 NAV 条目）与 `fragment_enter`（HTML dispatch 分支）**一律保留**，但**不再指向任何屏**（与 `sysmenu` 废除后 `open_sysmenu` 同口径）。
> ③ **素材与模块保留** —— 素材 `ui/x_gen_fragpage.png`（1920×1080 整页底图）、数据 `fragments`（`krkr\game\ui_flow_data.tjs` ／ `复刻\flow_data.js`；`工具\test_gen_sync.py` 的 **G-3b 闸门硬要求该 token 存在**）、模块 `krkr\game\ui_fragment.tjs` 及其在 `startup.tjs` 的加载行**一律保留** —— **不得删除**（删文件会致启动 FATAL）；该模块现**无触发路径**（屏永不为 current）。
> 依据＝用户裁定「**只删屏、保留动作/素材**」；巡演步 `open_fragment` 与白名单里的 `"fragment"` 已移除，全链复跑 **34/34 绿**。
>
> ★★ **ISSUE-20260928-07（2026-09-28，用户裁定）：`ending`（片尾·STAFF/歌词）屏已整体删除**（`layout/screens/_index.json` 屏数 **18 → 17**；用户：**未来改用一段视频代替**）。**编程组必读**：① 屏文件 `29_ending.json` 与 `_index.json` 条目已移除，屏内 7 件元素（`ed.bg`/`ed.shade`/`ed.char`/`ed.staff`/`ed.lyric_bar`/`ed.lyric`/`ed.hit_skip`）随之移除；② 该屏**原本就没有模块、没有 `open_ending` 类动作、没有 `startup.tjs` 加载行，也没有任何跨屏入口** ⇒ **编程组无需改接线**（巡演白名单 / 步表、`复刻\replica.js` 的 `SCREEN_CATALOG`、`工具\test_gen_sync.py` 的 NO_GEN 条目、`工具\make_demo_sheets.py` 的 sheet5 已一并同步）；③ **素材 `x_ui_ending_bg.png` / `x_gen_ed_char.png` 保留原处**（屏独占，作将来做视频的参考/来源）。 ★ **二审更正（ISSUE-20260928-07）**：上面的枚举**不全** —— 还漏了 `复刻\screen_index.js`（**编辑器用**屏清单，来源 `layout/screens/_index.json`）⇒ **删屏后必须重跑 `工具\emit_asset_index.py`**。本批首版就因漏跑它，导致编辑器屏选择器为空并抛 `TypeError`（一审抓出 Critical）；已修，并已把该步纳入 `run_all.py` 作常驻闸门。

---

## 二、怎么跑起来

```bat
:: 双击即可（纯 ASCII 注释；会自动同步到 ASCII 运行目录）
工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\run_loose.bat       :: 交互模式
工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\run_autotour.bat    :: 自动巡演（无人值守，跑完自动退出）
```

**为什么必须用运行脚本而不是直接双击 exe**：krkr 的素材解析只认「项目根内的 `ui/` 或 `assets/ui/`」两种候选名，而正式布局里素材在 `krkr\assets\`（项目根的兄弟目录）——脚本会先把 `game\` 与 `assets\` 同步到一个 ASCII 路径下再启动。
详见 `krkr\README_运行方式.md`。

**日志**：`<运行目录>\runtime\savedata\krkr.console.log`（UTF-16LE）。
**截图**：巡演模式会**离屏导出每屏 PNG** 到同一目录（`shot_NN_<屏id>.png`）——这是 UI 组的实机自证手段，编程组可直接复用做回归。

---

## 三、TJS2 UI 组件库的调用方式

| 文件 | 职责 | 你要用到的 |
| --- | --- | --- |
| `startup.tjs` | 入口：建窗口、设标题（含署名串）、探测字体、装载布局与资产、装界面栈、绑输入、巡演 | 改 `UI_TITLE_MAIN` 等常量；**你的游戏入口可另写 `startup.tjs` 复用其余模块** |
| `ui_theme.tjs` | 色板/透明度工具、字体回退链探测与度量 | `uiThemeCanvasW/H()`、字体度量 |
| `ui_layout.tjs` | **【自动生成，禁止手改】** 布局数据 | `UILayoutData.screens[<屏id>].elements[]` |
| `ui_asset.tjs` | 贴图加载与缓存；缺件**不崩**（登记 + 占位） | `uiAssetLoad(layoutAssetString)` |
| `ui_widget.tjs` | **五种 kind 的通用渲染器**：`image`（含九宫格）/`text`/`rect`/`hit`/`list`/`anim` | `uiWidgetDraw…` 系列；**所有屏都由它渲染** |
| `ui_dialog.tjs` | 对话框屏：名字框、正文、**打字机**、光标闪烁、选择肢 | `uiDialogDraw`、台词推进 API |
| `ui_screens.tjs` | 其余屏的通用渲染 + **界面栈导航** + `hit.action` 分派 | `uiScreenDraw`、`uiActionDispatch`、`uiScreenKey` |
| `ui_state.tjs` | 持久化（绝对存储名 `file://./<盘符>/…`，跨启动读回） | `uiStateSave/Load` |
| `ui_transition.tjs` | 遮罩转场（**实测可用**，见 §五.2）｜★ **D-02 2026-10-01 已改为乒乓双缓冲**（旧 `uiTransSnapshot`/`uiTransSetPending`/`uiTransAfterDraw` 三个函数**已撤除**） | `uiTransStart()` / `uiTransInFlight()` / `uiTransMarkSettled()` / `uiTransSummary()`；层的结算在 `startup.tjs::uiTransSettle()`（见 §十 10.2） |
| `ui_flow.tjs` / `ui_fragment.tjs` / `ui_flow_data.tjs` | 流程图 / 番外 Fragment / 章节选择（**M4 模块**） | 通过 `uiFlowInstall()` 包装上面三个入口，**必须先于使用执行**。<br>★ **ISSUE-20260928-06**：`fragment` 屏已删除 ⇒ `ui_fragment.tjs` **保留但无触发路径**；**不得删该文件**（`startup.tjs` 会加载它，删之即启动 FATAL） |
| `ui_demo_script.tjs` | **演示台词**（真实语料，非剧情实现） | **编程组应整体替换为剧本驱动** |

**装载顺序（`startup.tjs` 已按此实现，改动时勿打乱）**：
```
ui_layout → ui_theme → ui_asset → ui_widget → ui_demo_script → ui_dialog → ui_state
→ ui_transition → ui_screens → ui_flow_data → ui_flow → ui_fragment
```
（`ui_flow*` 必须排在 `ui_screens` **之后**——它包装 `ui_screens` 的三个入口。**不要**同时改 `ui_screens.tjs` 的分派，否则会双重包装。）

---

## 四、编程组要做的事（**替换/接入点**）

| # | 事项 | 怎么做 |
| --- | --- | --- |
| 1 | **剧本驱动** | `ui_demo_script.tjs` 的台词数组整体替换为按 `资源组\剧本\scene_<源>.jsonl` 顺序推进的剧情播放器（**消费顺序**见 `..\资源组\交接编程组\交接说明.md` §二：定取文源 → 套修正表（**按 source 门控**）→ 套译名替换 → 组装） |
| 2 | **背景/立绘层** | 布局里 `dynamic:"story_background"` 的层（**现仅 `dlg.content` 一处**，见下）由你填真实素材，框位取根 `content_boxes[源代号]`（**唯一来源 `layout\_root.json`**：★ **D-04 2026-10-02 起 `ot/otr/ota/otp/otv/np` 六源一律 `0,0,1920,1080` 全画布**；旧值 `ot/otr/ota/otp`→`360,90,1200,900`、`otv`→`240,132,1440,816` 已作废——见根 `content_box_rule` 第四条修订注）。★ 你的 `ui_story.tjs` 选框判据 `dFull < dSrc` 在六源同框后**退化为恒真**，请按 D-04 移交单简化为恒用全画布。**不得缩放素材本体**。<br>★ **`story_chara` 现无数据落点**：它只出现在 `10_dialog.json` 的 `dlg.face` 的 `note` 里（作为接入契约），**候选元素＝`dlg.face`（现为静态件 `asset: face/mis01.png`）**。全 17 屏里带**非空 `dynamic`** 的元素**只有 2 个**：`dlg.content`（`story_background`）与 `fc.play_view`（`flow_scene_frames`）。<br>★ **旧值作废**：本行原写 1280 基线框位（`ot/otr/ota/otp→240,60,800,600`；`otv→160,88,960,544`；`np→0,0,1280,720`）—— 那是 1280 时代的旧值，**已作废**（以 `_root.json` 为准） |
| 3 | **存档缩略图** | ★ **落点 id 订正（2026-09-30 一审实证）**：缩略窗元素**两屏各 12 个、id 同名 `sv.thumb1..12`**（`23_save.json` 与 `24_load.json`）——**没有 `ld.thumb*`**（旧记「`sv.thumb1..12`／`ld.thumb1..12`」**已作废**；`grep '"ld\.' layout/screens/` 只命中 `22_loading.json` 的 `ld.dim`/`ld.text`）。<br>★ **现状**：这些元素现为 `kind:"image"` 的**静态占位件**（`asset: ui/x_ui_psv_slot_thumbwin.png`），**`dynamic:"slot_thumb"` 目前只写在它们的 `note` 里**作为接入契约 ⇒ 接入时按 `layout\_schema.md` §四 把元素改为 `dynamic:"slot_thumb"`（**元素矩形即落点**）。<br>★ **口径**：两屏合计 **24 个缩略窗元素**；`grep -c "slot_thumb"` 为 **24 处/屏**（每元素 1 条 `asset` 行含 `_slot_thumbwin.png` ＋ 1 条 `note`），**不是 24 个动态层**。原记「16 处」＝「8 槽 × 2 页」的**旧基数**，已作废 |
| 4 | **动作实现** | `hit.action` / `list.actions` 的动作名表见 `layout\_schema.md` §六。**未定义动作一律写空串**，不得臆造。`list` 的槽号用 `slot_base` + 项序号 |
| 5 | **音频/视频** | 无内建 MP3；OGG 走 `wuvorbis.dll`、Opus 走 `kropus.dll`。视频格式**未确认**（总纲 G3），属你的缺口 |
| 6 | **字体缺口** | 总纲 **G2**：krkr 不自带字体、无中文字体内嵌方案。UI 组已做到「不依赖特定字体 + `Font.getList()` 探测回退」，**但目标机若没有中文字体仍需你解决**（`Font.faceIsFileName` 是内嵌 TTF 的唯一入口，**UI 组未实测**） |
| 7 | **KAG3 路线** | 总纲 **G1**：工作区无 KAG3/KAGEX 框架。UI 组按**自研 TJS2** 交付（POC 已实机闭环）。**你若改用 KAG3，UI 库需重写为 `.ks`——请先与 UI 组对齐** |
| 8 | **署名** | 窗口标题须含 `来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode`（AGENTS.md §六）。`startup.tjs` 已写入，你换入口时**不要漏** |

---

## 四·补　流程图右栏「章节详情」四段重排（`flowchart` 屏 · `ISSUE-20260929-02`）

> **本节是用户指令 5 的落点**（「必须在说明文档里详细介绍它们的用法，好让编程组能够高效运用」）。
> **数值唯一依据**＝`UI组/_工作/ISSUE-20260929-02_右栏大改/接口冻结.md` §B／§C（主代理 2026-09-29 冻结）。本屏由 `工具/gen_flow_layout.py` 生成（右栏这些件是该脚本内嵌的**静态元素快照**）⇒ **要改就改生成器，不要手改 JSON**。
> ✅ **落盘状态（2026-09-29 · E3 交付时实测：**全部到位**）**：① **素材** `krkr/assets/ui/x_ui_playwin_bg.png`（380×300 RGBA）与 `x_ui_pbkick_pause_{off,over,on}.png`（119×119 RGBA）**已在库**；② **生成器** `工具/gen_flow_layout.py` 已含本节全部元素契约（`STATIC_FLAG_EXEMPT = {"fc.pbkick","fc.pbkick_pause"}`、`flags_default = {fc_layer:"main", fc_replay:"play"}`）；③ **屏数据** `layout/screens/32_flowchart.json` **已重跑**（本节交付时 **280 件元素**；★ **`ISSUE-20260929-04` 第 12 批已再重跑为 274 件**，★ **`ISSUE-20260929-05` 第 13 批已再重跑为 262 件**，⚠ **已被第 15 批取代** ⇒ ~~**现行 272 件**~~（`ISSUE-20260930-02` · 第 2 轮 2026-09-30：＋10 件章节详情）**已作废**；**本批（`ISSUE-20260930-06`，2026-09-30）再改 ⇒ 现行 296 件**（独立层纵向流水，＋8 节点 × 3 件）—— 本节数值（id/几何/素材/动作）在后两批**一字未改**，只有 `fc.p_title`/`fc.p_title_tx` 的 `x/w`、4 个模式页签与 2 个备注键的退场、以及元素总数变，见 §四·补 2 与 §四·补 3；`fc.play_win`/`fc.play_view`/`fc.pbkick`/`fc.pbkick_pause` 仍在、**12 件退场件零残留**）。**本节数值已与屏数据逐字段核对一致**，并附「生成器 ↔ 屏数据」两源一致性断言（共 **139 条断言全绿、PENDING 0**，证据在 `_工作/ISSUE-20260929-02_右栏大改/证据/`）。**若日后屏数据再变，以屏数据为准并回报 UI 组。** ★ **第 2 轮追加（2026-09-29 主代理裁决）**：两个多行槽的 **`max_lines` 由 5 改定为 4**（依据见 4·补.4 之 2）；**该改动 E2 第二轮已落盘** —— 实测 `工具/gen_flow_layout.py` 与 `layout/screens/32_flowchart.json` 两源**均为 4**，本节写 4、**三方一致**（`verify_e3.py` 另有 `--probe-maxlines5` 变异自证：强制成 5 时必须报出，见 `E3_verify_变异自证.txt`）。
> ★ **总口径（先读这条）**：UI 组本轮只交「**元素 + 几何 + 状态位 + 动作名**」。**画面时序／帧序列／音频的播放本身，以及一切运行期文字填充，均属编程组接线 —— 本批一律未生效，本文不声称任何功能已生效**（与既有 `bgm_playpause`、`replay_play:<行号>` 同口径）。

### 4·补.1　右栏四段（栏底 `fc.smallmap` 一个字段未改）

| 段 | 件 | 几何 (x, y, w×h) | z | 说明 |
| --- | --- | --- | --- | --- |
| ① 大播放窗 | `fc.play_win` | (1448, 214, 380×300) | 6 | 底板；y **214–514** |
| | `fc.play_view` | (1454, 220, 368×288) | 7 | **动态画面层**（四周内缩 6px） |
| ② 标题 | `fc.p_title` | (1425, 534, 422×73) | 6 | 底槽；y **534–607**｜★ **第 12 批（`ISSUE-20260929-04` · 用户指令 4）：`x/w` 改 1425/422**（与 ③④ 两槽底**逐字相同**；旧值 1416/443 已作废） |
| | `fc.p_title_tx` | (1437, 544, 398×40) | 25 | 一行标题（`y = 槽顶 + 10`）｜★ 第 12 批：`x/w` 改 **1437/398**（与两个 `_tx` 逐字相同；旧值 1428/419 已作废） |
| ③ 说明 | `fc.p_text` | (1425, 617, 422×150) | 6 | 底槽；y **617–767** |
| | `fc.p_text_tx` | (1437, 623, 398×138) | 25 | 多行说明（`y = 槽顶 + 6`） |
| ④ 台词 | `fc.p_message` | (1425, 777, 422×150) | 6 | 底槽；y **777–927** |
| | `fc.p_message_tx` | (1437, 783, 398×138) | 25 | 多行台词（`y = 槽顶 + 6`） |
| 栏底（**不动**） | `fc.smallmap` | (1416, 190, 443×829) | 5 | 整栏底，本批**零改动** |

- **边距/段距（★ 第 3 轮现行值）**：栏内上边距 **24**（214−190）、**段间 20 / 10 / 10**、**台词底 927 → 按钮 `fc.jump` 上沿 943 ＝ 16px（无重叠）**、按钮下沿 1004 → 栏底 1019 ＝ **15px**（536−514＝22 等旧数字已被第 3 轮改排作废）。
- **修正留痕（第 3 轮 · vision 实机复审后）**：第 11 批首版的台词槽 `y824 h171` ⇒ 下沿 **995**，与「进入本章」按钮 `fc.jump`/`fc.jump_hit`（`(1474,943,328,61)`）上沿 **943** **竖直重叠 52px**（vision 实测按钮可见区 y953..996 落在槽内）。⇒ 三槽高度 **171 → 150**、四段改排为「**窗与三槽分离、三槽彼此紧凑**」。★ **口径限定（第 12 批订正）**：句末「三槽的 `x`/`w` 一字未改、`fc.jump*` 一字未改」**仅指第 3 轮**——该轮确未动三槽 `x`/`w`，`fc.jump*` 至今一字未改；**第 12 批（`ISSUE-20260929-04` · 用户指令 4）只动了标题槽 `fc.p_title`/`fc.p_title_tx` 的 `x/w`**（另两槽底 `fc.p_text`/`fc.p_message` 与其两个 `_tx` 一字未改），见 §四·补 2 与下表。
- **横向（★ 第 12 批现行值 · `ISSUE-20260929-04` 用户指令 4「三槽对齐」）**：三槽底**现逐字相同**（`x=1425`、`w=422`，即 `fc.p_title` ＝ `fc.p_text` ＝ `fc.p_message`）；三 `_tx` **现逐字相同**（`x=1437`、`w=398`）。⇒ 标题底/文字框与另两槽**不再有 21px / 9px 的差**。
  - **历史留痕（已作废）**：PSB 原稿的标题槽底 **`1416/443`**、文字框 **`1428/419`** —— 那是**参照作原样**（标题文字框曾比另两槽宽 21px），**第 12 批按用户指令 4 起作废**，原「请勿自行对齐」的告诫随之失效（本批正是**对齐**）。依据＝冻结书 §B 与 `layout/screens/32_flowchart.json` 实测（见 §四·补 2）。
- 大播放窗在 **443 栏宽内居中**：`x = 1416 + ceil((443 − 380)/2) = 1416 + 32 = 1448`（左留 32 / 右留 31）。

### 4·补.2　大播放窗（`fc.play_win` + `fc.play_view`）＝ 按顺序播放该章节的游戏内画面

| 件 | 角色 | 字段要点 |
| --- | --- | --- |
| `fc.play_win` | **底板** | `kind:"image"`；`asset:"ui/x_ui_playwin_bg.png"`（**380×300**，程序化合成：霜白竖向渐变＋2px 细蓝边＋外沿柔光＋上沿内侧白高光带；**盘面不烘焙任何文字**）；**与素材等尺寸 ⇒ 1:1、无 `nine`** |
| `fc.play_view` | **画面层**（368×288） | `kind:"image"`；**`asset: null` ＋ `dynamic: "flow_scene_frames"`** —— 与 `dlg.content`（`story_background`）、存档缩略图（`slot_thumb`）**同一机制**的**运行期填充层** |

1. **未填充时两端画占位底色 —— 这是正常状态，不是缺件。** `layout/_schema.md` §四 `dynamic` 条明文要求：「两侧渲染器都必须**保留该层并在未填充时画占位底色**，不得跳过」。⇒ 刚进屏时窗内是一块素色，属预期。
2. ⚠ **比例适配（本件唯一的坑）**：窗 **380×300 ≈ 1.267:1**，而游戏内画面是 **16:9（1.778:1）** ⇒ 必须 **`contain` 居中适配**：按宽贴合 ⇒ 画面实占 **368×207**，**上下各留约 40px 边**（属正常）。写成 `cover`／直接拉伸会**裁掉左右**或**拉变形**。
3. **最小用法示例**（伪代码，两条路二选一；与 `dlg.face` 的既有登记同口径）：

```tjs
// 路 A（推荐 · 走 dynamic 填充）：你们按顺序把该章节的帧喂给这个动态层
//   `flow_scene_frames` 是本批登记的名字（与 story_background / story_chara / slot_thumb 同族）
//   var lay = uiElLayer("fc.play_view");            // 取该层绘制对象（ui_widget 的 dynamic 分支）
//   fillContain(lay, frames[i], 368, 288);          // ← 你实现：16:9 → 368×207 居中，上下留边
//
// 路 B（单张静态图）：改的是**数据**，不是代码
//   UILayoutData.screens.flowchart.elements["fc.play_view"].asset = "ui/xxx.png";
```

4. 帧序列、播放推进、缓存、音量等**全部属编程组**；UI 组只保证「层在、几何在、机制在」。

### 4·补.3　播放键／暂停键（**同一位置 · 互斥显示**）

| 件 | 角色 | 几何 | 素材（三态） | 显示条件 |
| --- | --- | --- | --- | --- |
| `fc.pbkick` | 播放键 | (1578, 304, 119×119) z20 | `ui/x_ui_pbkick_{off,over,on}.png` | 屏级 flag `fc_replay == "play"` |
| **`fc.pbkick_pause`** | 暂停键 | (1578, 304, 119×119) z20 | `ui/x_ui_pbkick_pause_{off,over,on}.png` | 屏级 flag `fc_replay == "pause"` |
| `fc.pbkick_hit` | 热区（透明） | (1575, 301, 125×125) z95 | — | 恒常；`action:"flow_replay_toggle"` |

1. **同一位置、同一时刻只有一个可见**：靠既有 `vis_flag:"fc_replay"` ／ `vis_when:"play"|"pause"` 机制（**两端已实现**）—— **不得靠 z 排序、也不要在运行期手动隐藏**（`layout/_schema.md` §四 铁律一）。
2. **初值**：屏级 `flags_default` 新增 **`"fc_replay": "play"`**（与既有 `"fc_layer": "main"` 并列）⇒ **进屏默认显示播放键**。
3. **热区与按键同轴**（119×119 外扩 6px ⇒ 125×125）**且两键共用同一条热区**（两键同位置 ⇒ 一条即够）：点它就是派发 **`flow_replay_toggle`**（动作名**已定稿**，非「拟用名」），语义＝「**播放/暂停切换**」。
   ★ **语义边界（现行）**：**命中即派发**；**画面时序／帧序列的播放本身留你们接线，UI 组不声称其已生效**（与 `bgm_playpause`、`replay_play:<行号>` 同口径）。
   ★★ **订正（2026-09-29 · 模块 E4 落盘后实测口径）**：原句「`fc_replay` 的翻转与两键换显**由你们在分派里完成**」**已作废** ——
     **UI 组已在两端实现该动作**（纯 UI 状态变更），你们**不需要再实现翻 flag / 换显**：
       · krkr：`krkr/game/ui_flow.tjs` 的 `uiActionDispatch` 包装器新增分支（`act == UIFlowReplayActName` ⇒ `uiFlowReplayToggle()`）；判据 = `fc_replay == "pause"` ⇒ 置 `"play"`，否则 ⇒ 置 `"pause"`；写回走既有 `uiScreenFlagSet`，两键显隐由既有 `uiScreenElementVisible` 谓词自动同步（绘制与命中同一谓词）；重绘由调用方（`startup.tjs` 的 `handleClick` / 巡演 `uiTourStep` 派发后 `redraw()`）。
       · HTML：`复刻/replica.js` 的 `doAction` 新增 `case 'flow_replay_toggle'`（`flowReplayToggle`）；**同一判据**，走既有 `setFlag` ＋ `applyFlagVisibility()`（**不重建 DOM**）。
       · 机检：巡演判词 `★REPLAYTOGGLE★ PASS`（含负向对照 `★REPLAYTOGGLE-REJECT★`×3）+ HTML 自检（套 A ㉕a–㉕c、套 B `flow.replay-one-visible` / `flow.replay-toggle` / `flow.replay-toggle-idempotent`）；证据 `UI组\_工作\ISSUE-20260929-02_右栏大改\证据\replaytoggle_*`。
     ⇒ **编程组要做的只剩「画面播放本身」**：① 填充 `fc.play_view`（`dynamic:"flow_scene_frames"`，见 4·补.2）；② 帧序列／时序／音频；③ 若需要「暂停时真的停帧」，在你们自己的播放器里读 `fc_replay` 的当前值即可（**它是屏级 flag，用 `uiScreenFlagGet("fc_replay")` 读**）。
4. **三态语义（易误读，务必按此实现）**：两件都用既有的 **`state_assets{normal, hover, pressed}` 三槽**口径，**不是「开/关」两态**。其中 **`pressed`（按下态）用的就是 `_on` 件**：播放键的 `_on` 是 **■**、暂停键的 `_on` 是 **‖** —— 它们是**按住时的高亮图形**，**不是**「正在播放／已暂停」的状态指示。**「当前是播放还是暂停」只由 `fc_replay` 决定**（哪个键可见）。
5. 暂停键素材由播放键三态**派生**（盘面／羽化／描边与同态播放键逐像素同源，只替换中央字形掩膜），落 `krkr/assets/ui/x_ui_pbkick_pause_{off,over,on}.png`（119×119、**真 alpha / PNG-32**）。

### 4·补.4　三个文字槽怎么用（用户点名要求写清）

| 件 | 语义 | 几何 | 排版字段 | `sample`（现为占位） |
| --- | --- | --- | --- | --- |
| `fc.p_title_tx` | 章节**标题**（一行） | (1437, 544, 398×40) ★ 第 12 批：`x/w` 改 **1437/398**（与两个 `_tx` 逐字相同；旧值 `1428/419` 已作废） | `h:40`；`valign:"middle"`；`wrap:false`；`max_lines:1` | `"标题"` |
| `fc.p_text_tx` | 章节**说明**（多行） | (1437, 623, 398×138) | `valign:"top"`；`wrap:true`；`max_lines:4` | `"说明"` |
| `fc.p_message_tx` | **台词**（多行） | (1437, 783, 398×138) | `valign:"top"`；`wrap:true`；`max_lines:4` | `"台词"` |

1. **样式（三件一致）**：**白字（`@palette.text_primary` ＝ `#FFFFFF`）＋ 黑描边**（`outline:true` / `outline_color:"#000000"` / `outline_width:2`；`shadow:false`）；`font.size` **24**、`bold:true` **不变**。这是 **M38 既有机制**（krkr 侧八向描边 ／ HTML 侧 `text-shadow` 八向，**两端已通**），**纯渲染、不参与布局** ⇒ 描边既不挤字、也不改变折行与容量判据。
2. **★ 容量依据（多行槽 · 2026-09-29 主代理裁决，值＝`max_lines:4`）**：**第 3 轮槽高 138px** ÷ 行盒：**krkr 口径** 行盒 **33px**（＝ `floor(24 × 全局 fonts.line_spacing.body 1.4)`；依据 `krkr/game/ui_theme.tjs` 的 `lineH = Math.floor(size × uiThemeElementSpacing(el))`，元素级优先／否则全局见同文件 `uiThemeElementSpacing`；`layout/_root.json` 的 `fonts.line_spacing.body = 1.4`）⇒ **138 ÷ 33 ＝ 4.18** ⇒ **`max_lines:4`**；**HTML 口径** 行盒 `24 × 1.4 ＝ 33.6px`（`复刻/replica.js::buildText` 的 `size * lineSpacing(...)`，不取整），按**保守取整** `Math.round(24 × 1.4) ＝ 34` 算 ⇒ 4×34 ＝ **136 ≤ 138**。
   - **为何仍 4**：**4 行块高 krkr 132px / HTML 136px ✓**（盒高 138）；**5 行 krkr 165px / HTML 170px ✗**。⇒ **138 盒高下双口径都只容 4 行**，故 `max_lines` **保持 4**（第 11 批首版按「1.3 行距」推得 5.09⇒5 的乘数**是错的**；第 2 轮已定 4，第 3 轮按 138 盒高复核仍 4）。
   - **不加元素级 `line_spacing`**：三槽一律**沿用全局基线 1.4**（`_root.json` 不改，元素**不写** `line_spacing`）。
   ⚠ **提醒：别写超过 4 行。** 超出部分按 `max_lines` **截断**（不绘第 5 行、也不打省略号），折行/行首行尾禁则走引擎自己的算法（krkr `ui_theme.tjs::uiThemeWrap`／`uiThemeLayoutText`；HTML 复刻侧按 `e.w / e.max_lines` 同判据实现，见 `复刻/replica.js`）。本批三槽**都不是滚动槽**；确需更长请缩短文案或回报 UI 组重排。
3. **运行期怎么填**（与 `dlg.name` / `dlg.text` 同一契约）：
   - **krkr 侧**：文本来源＝`ctx.textOverride[<元素id>]`（有则优先），否则取元素 `sample`（`krkr/game/ui_widget.tjs::uiWidgetDrawText` → `ui_theme.tjs::uiThemeLayoutText`）。ctx 在 `krkr/game/ui_screens.tjs:1906` 建；既有用法见 `krkr/game/ui_dialog.tjs:283/291/312`（说话人、正文、状态标签）—— **照这套填 `fc.p_*_tx` 即可**。
   - **HTML 复刻侧**：直接取 `e.sample`（`复刻/replica.js:3051`）⇒ 要在 HTML 侧看到真实文案，改数据里的 `sample`（或按同一 override 思路补）。
   - `sample` 现为**占位词**（「标题／说明／台词」），**不是给玩家看的文案**；接上驱动后请整体替换。**别只改 `sample` 而忘了驱动源、也别只改驱动源而留着占位 `sample`** —— 两端量测与绘制都读 `sample`。
4. **内容来源（供参考，不在 UI 组范围）**：章节标题／说明／台词来自章节级数据（`资源组/05_章节总表.tsv`、`资源组/08_全系列章节流程图.html` 的节点字段）。**具体取哪几个字段由你们定**，UI 组不预设。

### 4·补.5　已退场（**勿再接线**）：12 件元素已删除，素材一个不删

| 已删除元素 | 原用途 | 现由谁承担 |
| --- | --- | --- |
| `fc.mini1` / `fc.mini2` / `fc.mini3` / `fc.mini4` / `fc.mini5` / `fc.mini6` / `fc.mini7` / `fc.mini8`（8 件） | 8 张缩略图块 | **无**（用户「我不需要小略缩图」）⇒ 由 ① 大播放窗承担 |
| `fc.mapview` | 缩略图可视区框（380×300） | **无**（其 380×300 被沿用为大播放窗的**尺寸基准**） |
| `fc.pbk_panel` | 场景回放窗底板（426×241） | **`fc.play_win`**（新底板 380×300） |
| `fc.p_player` | 回放组内容底（rect） | **`fc.play_view`**（动态画面层） |
| `fc.p_player_tx` | 「场景回放」占位标签 | **无**（不再需要标签） |

- **素材一律保留、一个文件都没删**：`ui/x_ui_replay_panel.png` 等仍在 `krkr/assets/ui/`（工程口径「旧素材一件不删」）。
- ⚠ **旧代码若引用左列 id，请改到右列新件**。**已核现状**：`krkr/game/*.tjs` 与 `复刻/*.js` 中**没有任何活引用**指向这 12 件 —— 唯一出现处是 `krkr/game/ui_flow.tjs:478` 的**注释**（列举详情面板四槽时写了 `fc.p_player_tx`）。旧「场景回放组／迷你地图组」的互斥显示逻辑本就不存在（`ui_flow.tjs` 原文：「详情面板与滚动指示：**本轮不接线**（属编程组）」）。
- `fc.smallmap` 保留**元素与 id**，本批**未**给它任何运行态。★ **订正（2026-09-30 · `ISSUE-20260930-06`，用户裁定 1）：迷你地图功能正式废弃** —— **不再补回** `fc.mapview`／`fc.mini1..8`／回放组 3 件（共 12 件）；`fc.smallmap` 的**用途现为右栏底板**（右栏四段叠于其上），不再是迷你地图承载。详见 §九.2。

### 4·补.6　载入屏（`loading`）：`ld.bg` 已删除

- `layout/screens/22_loading.json` 的**满幅底元素 `ld.bg` 已删除**（用户指令 6）；该屏由 **3 件 → 2 件**：`ld.dim`（满幅压暗 rect，`@palette.backdrop` `#000000` ×100）与 `ld.text`（引擎绘「载入中…」，白字 + 蓝描边）—— **这两件一个字段都没改**（`ld.bg` 删前 z=0，删后 `ld.dim` z=1 成为本屏最底层；该屏实际下衬什么由你们的屏栈决定，UI 组未改机制）。
- **素材 `ui/x_ui_backlog_bg.png` 保留不删**（1916×1080，md5 `5d05e6e90ce7b5080b7f040b3571a42f`）—— **保留依据＝工程口径「旧素材一件不删」**（2026-09-29 主代理裁决追认），**不是**「共用链」。★ **勘误**：原记「该素材仍被 `26_backlog` 引用、删文件即断链」**不成立** —— `26_backlog` 自 PSV 换皮（`ISSUE-20260926-06` · B 组）起底图已改引 `ui/x_ui_psv_backlog_bg.png`；删 `ld.bg` 后 `x_ui_backlog_bg.png` 在**全 17 屏屏数据中零元素引用**（仅 `复刻/asset_index.js` 素材清单仍列出它）。冻结书 §C 的理由句已由主代理就地改为口径式表述。
- ⇒ 若你们的 loading 呈现需要“压死背景”，请在屏栈／过渡里处理，**不要回加满幅底图**（那是用户明确要求删除的）。

---

## 四·补 2　流程图页四件收尾 ＋ 番外入口统一形制（`flowchart` 屏 · `ISSUE-20260929-04`）

> **编程组必读（本批唯一需要你知道的接线变化）**：**没有新增任何需要你接线的动作或机制** ——
> 本批全部是**画面与形制**的改动：新增 1 件满幅背景、删 1 件遗留装饰条、换 1 件缩放滑块、
> 右栏标题槽与另两槽对齐、番外入口由「付箋占位」改成「淡黄节点形块」。
> 入口热区 `fc.entry.<NNNN>_hit` 的 **`action:"flow_layer"` ＋ `layer:"frag<G>"` 一字未改**
> （语义仍是「进入该 xx 番外章节」＝你说的 `fc_layer - fragx`）。

### 4·补2.1　新增满幅背景 `fc.bg`（**你无需接线**）

| 件 | 几何 | 素材 | 要点 |
| --- | --- | --- | --- |
| `fc.bg` | `(0, 0, 1920×1080)` | `ui/x_bg_flowchart.png`（**1920×1080 RGB**） | `kind:"image"`、**`z:0`**（在 `fc.dim` z1 **之下**）、`visible_default:true`、**无 `nine`**（1:1）。**纯背景、无交互、无动作** ⇒ 你只要照常渲染 `elements` 即可。它是**外壳件**（不写 `vis_flag`/`vis_when`）⇒ 主干层与 6 个番外独立层**都画它**（两态共用舞台） |

- **素材来源**：`资源组\美术统一_超分\CG背景\bg72.png`（2560×1440）→ **0.75× LANCZOS** 降采样（**不调色 / 不裁切 / 不加字**）。该目录被 `.gitignore` 排除 ⇒ 仓库里只有降采样成品。
- **叠加次序（务必保持）**：`fc.bg`(z0) → `fc.dim`(z1，全屏黑 60/255 ≈ 23.5% 压暗) → `fc.scroll`(z5，视口 `@palette.panel_edge` 40) → 节点/连线（z19+）。**若你把 `fc.bg` 放到 `fc.dim` 之上，整屏会被照片糊住**（`m02` 的 z 序断言即守此：`fc.bg` < `fc.dim` < 栏底 …）。
- **亮度**：加背景后「舞台」由近黑变成亮色（合成 ≈**(151,161,171)**，对墨色 `@palette.psv_ink` **6.05:1** ⇒ 比以前的 1.19:1 更易读）。**强度旋钮＝`fc.dim` 的 `opacity`**（想更暗就加大，**不要**新增遮罩元素）。

### 4·补2.2　番外入口改形制：`fc.entry.<NNNN>` = **淡黄节点形块**（**接线不变**）

| 件 | 几何 | 素材 | 要点 |
| --- | --- | --- | --- |
| `fc.entry.<NNNN>`（0001–0006） | `(60, y, 296×65)`，`y` ＝ **242/337/432/527/622/717** | `ui/x_ui_entry_frag_off.png`（normal）／`ui/x_ui_entry_frag_on.png`（hover），均 **263×65** | `kind:"image"`、`nine{l14,t0,r13,b0}`（**与 `fc.node.*` 完全一致**）、`z:20`、`state_assets{normal,hover}`；`vis_flag:"fc_layer"`/`vis_when:"main"` |
| `fc.entry.<NNNN>_hit` | 同矩形 `(60, y, 296×65)`；`z:95` | — | **`action:"flow_layer"` ＋ `layer:"frag<G>"`（未改）**；`vis_when:"main"` |
| `fc.label.<NNNN>_tx` | 同矩形 `(60, y, 296×65)`；`z:25` | — | 组名文字（引擎绘制，16px / bold / `@palette.psv_ink`），**落在入口块上** |

- **已删**：`fc.label.<NNNN>`（6 件**标签底板 image**）—— **只删元素，素材 `x_ui_label_off.png` 保留**。
  ⇒ **本屏不再有「标签底板」这个元素族**（独立层的组名底板 `fc.frag<G>_title_bg` **仍在**，勿混淆）。
- **形制来源**：用户 2026-09-29 追加裁决「`fc.label.000x` 与 `fc.entry.000x` 一律删去，统一为**和章节素材
  `ui/x_ui_node_select_off(和on).png` 一样的形状、只是底色换成淡黄**；文字方案不动」。新素材由
  `x_ui_node_select_{off,on}.png` **派生**（alpha 逐字节同源、仅换色相）。
- **文字容量已实测**：6 条组名在 16px / 盒宽 296 下**全部单行**（最长 265.0px）⇒ 无需你处理折行。
- **命中与外观同集**：入口块（z20）与热区（z95）同矩形；热区无 `state_group`/`state_assets` ⇒
  **悬停态只会点亮入口块本身**（命中取最高 z 的候选并集，热区不参与该并集）。

### 4·补2.3　`fc.zoom_knob` 换件（**用户指令 1**）＋ `fc.sysbar` 删元素

- `fc.zoom_knob`：`asset` → **`ui/x_ui_zoom_handle.png`（40×31 单一竖圆角胶囊手柄）**、**删 `nine`**；
  几何 `(1174,112,40×31)`、`z:21`、`opacity:255` **不变**；旧件 `x_ui_zoom_knob.png`（29×16，内含横胶囊＋圆点两个图形）**退役、文件保留**。**仍为单态**（无三态件）⇒ **拖动/缩放行为照旧属你**。
- `fc.sysbar`：**元素已删**（`sysbar` 屏删除后留下的装饰条，无文字/无点击/无 `_hit`）——**素材 `x_ui_sysbar.png` 保留不删**。
  ⇒ 若你此前按「右上有一条系统共通条」做过任何占位/命中，**可以删掉**。
- `fc.p_title` / `fc.p_title_tx`：`x/w` 改为与另两槽 **逐字相同**（见 §4·补.1 表）。**字段语义未变**，你无需改代码。

---

## 四·补 3　流程图**模式入口**（两枚文字入口）＋ 删备注功能与对话框提示（`flowchart` / `dialog` 屏 · `ISSUE-20260929-05`）

> 用户 2026-09-29 指令：**流程图页** ① 删 4 个 `fc.mtabx` 与其 text（序章／本篇／After Story／Fragment）；
> ② 在原位置用**两枚文字入口**取代，只保留 **「本篇集合」**（序章／本篇／After Story 并入）与
> **「番外故事」**（原 Fragment）；③ **不再需要备注功能** ⇒ 删 `fc.fusen_edit`/`fc.fusen_reset`（＋`_tx`/`_hit`）。
> **对话框页**：删除 `dlg.hint`（不需要操作提示）。**共删 19 件元素、加 6 件**（**素材一个不删**）。

### 4·补3.1　两枚模式入口怎么用（**编程组必读**）

| 项 | 值 |
| --- | --- |
| 元素（每枚 3 件） | `fc.mode_main_glow`／`fc.mode_main_tx`／`fc.mode_main_hit`（本篇集合）；`fc.mode_frag_glow`／`fc.mode_frag_tx`／`fc.mode_frag_hit`（番外故事） |
| 几何 | **180×60**；`fc.mode_main_*` @**x34**、`fc.mode_frag_*` @**x254**（**等宽 180、间距 40**）。**`_glow`/`_hit` 的 `y` ＝ 25**（60 高居中于旧页签带中线 55 ⇒ 占 25..85）；★ **`_tx`（文字）的 `y` ＝ 33** —— 用户 2026-09-29 裁决「**两个模式入口的文字下移 8px**」（E5 订正：实测原墨迹 y31..63/中心 47、而框中心 55 ⇒ 偏高 8px；下移后墨迹 y39..71、中心 55 与框同心）。**即三件不再逐字段同矩形**：同 `x/w/h`，`_tx.y = _glow.y + 8`。 |
| `z` | `_glow` **10** ／ `_tx` **20** ／ `_hit` **95**（热区最高 ⇒ 指针落在按钮任意位置都由它胜出） |
| `state_group` | `mode_main` ／ `mode_frag`（**`_glow` 与 `_hit` 同组** ⇒ 指针进热区即点亮底光图，换态由**既有**组绑定机制驱动，你无需写代码） |
| `state_assets` | `{normal: ui/x_ui_modetab_off.png, hover: ui/x_ui_modetab_over.png, pressed: ui/x_ui_modetab_press.png}`（**180×60 ×3，两枚入口共用同一套**）；**1:1 ⇒ 无 `nine`** |
| **动作（你要接的）** | `_hit.action` ＝ **`flow_mode_main`** / **`flow_mode_frag`**（**拟用名**，用户裁决）；**语义边界＝命中即派发** —— **切集 / 筛选**（哪些章节算「本篇集合」、哪些算「番外故事」）的**行为留你实现**，本批**不声称已生效**（与 `flow_replay_toggle` 同口径）。已登记进 `layout/_schema.md` §六 动作表。 |
| 文字 | 引擎绘制：`size 30` / **`bold:false`**（引擎默认字体族首位即**微软雅黑 Regular**）/ `@palette.text_primary` 白字 ＋ `outline:true`+`#000000`+宽 2 黑描边；`_tx.sample` ＝ 「本篇集合」/「番外故事」 |

- ★ **三态口径（勿误解）**：**三态全靠 `_glow` 底光图承载**（同一枚柔和白淡光的**弱 / 强 / 实底**三档；
  `_press` ＝ 半透明冰蓝实底胶囊 ＋ 1px 亮边）。**文字由引擎画、不参与换态** —— schema **不支持文字带
  `state_assets`**（只有 `image` / `list.item_frame` / `item_buttons` 有），所以「悬停＝文字整体发亮」是
  靠**底光图变亮**实现的。
- ⚠ **限制（如实交接）**：用户原话含「**文字下移 1px**」，但 schema **不支持文字逐态位移**、
  `state_group` **只配对图片层** ⇒ 本轮以「**底沉 1px**」等价表达「按进去」（`_press` 的胶囊整体
  比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。
- ★ **实机已实测三态真的被换用**（不是只写在数据里）：巡演新增 `kind:"modestate"` 合成指针步
  （走 `uiScreenHoverUpdate`/`uiScreenPressUpdate` 同一批入口），日志 `★MODESTATE★ PASS`：
  悬停取 `x_ui_modetab_over.png`、按下取 `x_ui_modetab_press.png`、指针移开回
  `x_ui_modetab_off.png`；并有**交叉负向对照**（悬停 main 时 frag 的底光图仍为 normal ⇒ 不串组）。

### 4·补3.2　已删除（**勿再接线**）

| 删了什么 | 说明 |
| --- | --- |
| `fc.mtab1`…`fc.mtab4` ＋ `_tx` ＋ `_hit`（**12 件**） | 4 个模式页签（序章／本篇／After Story／Fragment）。**素材 `x_ui_ftab_{on,off,over}.png` 保留不删**，但**现零功能引用** |
| `fc.fusen_edit`/`fc.fusen_reset` ＋ `_tx` ＋ `_hit`（**6 件**） | 备注功能键（用户点名 4 件，另两个 `_hit` 一并删 —— 否则留下**指向空动作的死热区**）。**素材 `x_ui_fusen_{off,over,on}.png` 保留不删**，**现零功能引用** |
| `dlg.hint`（**1 件**，在 `layout/screens/10_dialog.json`） | 对话框页左上操作提示文本（「右键：功能图标 空格：快进 …」）。**该屏手工维护**，本批只删这一件，其余元素一字未动 |

⇒ 若你此前按「4 个模式页签」或「备注编辑/初始化两键」做过任何占位、命中或状态，**可以删掉**；
全库实测对这 19 件**零「按 id 取值后解引用」**（巡演按屏与 `action` 选点、HTML 自检对 flowchart 是数据驱动遍历）。

---

## 四·补 4　流程图「章节详情」浮层 ＋ 加号按钮（`flowchart` 屏 · `ISSUE-20260930-02`）

> 用户 2026-09-30 裁定：「说明」框内右上角**加一枚加号按钮**，点它弹出**章节标题 ＋ 简介全文**的详情浮层；
> 加号占位处文字槽相应**收窄**（398 → **300**）；字号**不下调**，**超出边框即省略为 `……`**。
> **数值唯一依据**＝`UI组/_工作/ISSUE-20260930-02_章节详情/接口冻结.md` §一/§三/§四/§五。本屏由 `工具/gen_flow_layout.py` 生成
> ⇒ **要改就改生成器，不要手改 JSON**。落盘状态：素材 3 件（`x_ui_plusbtn_{off,over,press}.png` 44×44）**已在库**、
> 屏数据**已重跑**（`flowchart` **现 296 件**〔本节交付时 270 → 第 2 轮 272 → 本批 `ISSUE-20260930-06` **296**，270/272 已作废〕）。

### 4·补4.1　**本批唯一需要你接线的两件事**（其余都是 UI 组已交付的容器/几何/状态/动作）

| # | 事项 | 怎么做 |
| --- | --- | --- |
| 1 | **浮层正文/标题的取数（按 `场景id`）** | 浮层两件文字 `fc.intro_title_tx`（`sample:"章节标题"`）与 `fc.intro_text_tx`（`sample:"章节简介全文"`）现为**占位词**。运行期填充方式与 `dlg.name`/`dlg.text` **同一契约**：krkr 走 `ctx.textOverride[<元素id>]`（`krkr/game/ui_widget.tjs::uiWidgetDrawText` → `ui_theme.tjs::uiThemeLayoutText`），HTML 读 `e.sample`（`复刻/replica.js`）。**取数键＝`场景id`**（`资源组/剧本/章节简介.tsv`，`采用=是` 且 `简介cn` 非空共 **1199 条**）。 |
| 2 | **节点 ↔ 场景的粒度映射** | 右栏「说明」槽（`fc.p_text_tx`，现 **300px × 4 行**）的**摘要内容**、以及浮层的全文，都应来自**当前光标节点/场景**对应的那一条简介 —— 而**流程图节点是「幕/分歧点」粒度（**交付样例 13 节点**；**全量 712 节点的几何数据**已交 `_工作\ISSUE-20260928-02_第2步\全量布局.json`，**只交几何、不含 `elements`，元素化渲染归编程组**），简介语料是「场景」粒度（1199 条）** ⇒ 二者不是一对一。**这个映射（哪条简介属于哪个节点）由你定**，UI 组不预设（冻结 §四明写）。 |

### 4·补4.2　两条动作：**两端已实现，只是没数据**

| 动作 | 发出方 | 语义（**现行**） |
| --- | --- | --- |
| **`flow_intro_open`** | `fc.p_plus_hit`（加号按钮热区，44×44 @1803,**618**、z96） | 命中 ⇒ 把**屏级 flag `fc_intro`** 置 **`"open"`**（浮层 **8 件**可见）。**纯 flag 翻转**，与 `flow_replay_toggle` 同口径。 |
| **`flow_intro_close`** | `fc.intro_scrim_hit`（浮层压暗层的满幅热区，z210）**＋ `fc.intro_close_hit`**（浮层右上角关闭 × 的热区 46×46 @1520,354、z237 —— ★ 第 2 轮用户裁定 5 新增，**同一动作**） | 命中 ⇒ 置回 **`"closed"`**（＝**点浮层之外** ／ **点右上角 ×**，两条路径共用语义）。 |

- ★★ **你不需要再实现「翻 flag / 换显」** —— **UI 组已在两端实现**：krkr `krkr/game/ui_screens.tjs::uiActionDispatch` 的 `flow_intro_*` 分支 ／ HTML `复刻/replica.js::doAction` 分支（同判据、直接置值）。
  面板热区 **`fc.intro_panel_hit`**（z230）的 `action` 是**空串＝吞掉点击** ⇒ 点面板内**不关闭**（这是「点浮层外才关」的实现方式，**不要给它加动作**）。
  ★ 关闭件 2 件（`fc.intro_close` 按钮 z236 ／ `fc.intro_close_hit` 热区 z237）的 z **必须高于面板热区 230**，否则点关闭会被面板吞掉 —— 该硬前提由生成器落盘前自检专条断言 ＋ 变异自证 G 守住；**若你要改 z，务必同步跑 `python 工具\gen_flow_layout.py --selfcheck-intro-overlay`**。
- ⚠ **本批不声称任何「真实数据已接」**：浮层里现在是占位词、右栏摘要也还没有真实截断内容 —— 那正是上表第 1/2 项要你做的。
  （机检侧：巡演判词 `★INTROOPEN★` / `★INTROCLOSE★` 各有 PASS ＋ 各一条 `-REJECT★` 负向对照，证明 flag 翻转与浮层显隐**确实生效**；
  另有 **`★WRAPELLIP★`** 直调引擎 `uiThemeWrap` 的省略号判词 —— 补上「引擎侧此前只有逻辑审阅」的证据缺口。）

### 4·补4.3　元素与几何（**你不要改这些**，改了就与生成器/闸门脱钩）

| 件 | 几何 (x, y, w×h) ｜ z | 要点 |
| --- | --- | --- |
| `fc.p_plus` | (1803, **618**, 44×44) ｜ 27 | image；三态 `ui/x_ui_plusbtn_{off,over,press}.png`、`state_group:"p_plus"`、**1:1 无 `nine`**（★ 第 2 轮：`y` 625→**618**，对齐首行行盒中心） |
| `fc.p_plus_hit` | 同矩形（y 618） ｜ 96 | hit；`action:"flow_intro_open"`、`state_group:"p_plus"`（指针落热区即点亮按钮三态） |
| `fc.intro_scrim` | (0,0,1920×1080) ｜ 200 | rect `#000000`×150（整屏压暗）；`vis_flag:"fc_intro"`/`vis_when:"open"` |
| `fc.intro_scrim_hit` | 满幅 ｜ 210 | hit；`action:"flow_intro_close"` |
| `fc.intro_bg` | (340, **340**, 1240×**400**) ｜ 220 | image `ui/x_ui_gal_cell_on.png`（源 291×166）、**`nine{l:4,t:4,r:4,b:4}`**（★ 第 2 轮：由 1240×652 @340,214 改为**版面中心**） |
| `fc.intro_panel_hit` | 同 `fc.intro_bg` ｜ 230 | hit；**`action:""` 吞点击** |
| `fc.intro_title_tx` | (372, **372**, **1140**×44) ｜ 235 | text；24px **bold**、白字＋黑描边 2px、`max_lines:1`（★ 第 2 轮：宽 1176→1140 给关闭件让位） |
| `fc.intro_text_tx` | (372, **432**, 1176×**276**) ｜ 235 | text；24px 常规、白字＋黑描边 2px、**`max_lines:6`**（M4 实测 1199 条自然折行最大 **3 行 ⇒ 截断 0**，能看全文；★ 第 2 轮：h 528→276 ＝ 面板底 740 − 32 留白） |
| **`fc.intro_close`** | (**1530, 364, 26×26**) ｜ **236** | image；复用既有 `x_ui_close_*`（`state_assets{normal:_off, hover:_over, pressed:_on}`、`state_group:"intro_close"`）；★ **带 `nine{6,6,6,6}`（同 `fc.close`；素材实为 24×26 ⇒ 无 `nine` 会被 `verify_ui[2]` 判假失败）**；**零新素材** |
| **`fc.intro_close_hit`** | (**1520, 354, 46×46**) ｜ **237** | hit；`action:"flow_intro_close"`、`state_group:"intro_close"`；**z 必须 > 面板热区 230**（本屏最高点击候选） |
| 改 `fc.p_text_tx` | (1437, 623, **300**×138) ｜ 25 | 「说明」摘要槽；`w` 398 → **300**；其余字段不变 |

- **屏级 flag `flags_default` 追加 `"fc_intro":"closed"`**（进屏默认关闭浮层；既有 `fc_layer`/`fc_replay` 不动）。
- **超框省略号**（本批新增规则，两端＋Python 三处同判据）：折行超 `max_lines` ⇒ 保留前 N 行、**末行接 `……`（两个 U+2026）**；
  连 `……` 都放不下 ⇒ 该行不画；**纯渲染、不参与布局**。实现落在引擎/HTML 里，**你无需处理**（但若你自己的驱动往槽里塞超长文本，行为就是「截断＋省略号」）。

---

## 五、UI 组的实测硬结论（**省你踩坑**）

### 5.1 TJS2 语义级坑（**静态查不出，必须实机跑**）
| # | 坑 | 后果 |
| --- | --- | --- |
| 1 | **无 `String.lastIndexOf`** | `ui_flow.tjs` 曾因此抛异常 → **流程图全黑 + 异常外溢把对话框也打黑** |
| 2 | **无全局 `parseInt`、无 `charCodeAt`** | 静默失败或抛异常 |
| 3 | **`Array.load` 是实例方法**（静态调用抛「无效的 object context」，被 catch 后静默失败） | 存档**看似保存了其实读不回** |
| 4 | 标识符**大小写敏感**，未定义标识符报的是**「未找到 Member」**（不是「未定义变量」） | 误导排错方向 |
| 5 | Dictionary **读缺键返回 void 不抛** | `void → Object` 转换在**下一处**才炸（UI 组曾在 `ui_dialog.tjs:267` 炸） |
| 6 | **异常即使被 catch，引擎仍打整段 dump** | 日志噪音大；缺文件要先 `isExistentStorage` |
| 7 | `e.trace` 首帧是「调用者+调用行」；**抛错点看 `==== An exception occured at` 那一行** | 定位错文件 |
| 8 | 语法错误**没有行号** | 用「前缀夹逼法」（二分注释）定位 |
| 9 | 子层 `visible` **默认 false**，只有 primary 自动置真 | 子层不显式置真就什么都不显示 |
| 10 | `Timer` **必须被引用持有**（局部变量会被回收静默停止） | 打字机/动画莫名停住 |
| 11 | `-assetdir=<绝对路径>` **实测未生效** | 素材要靠项目根内的 `ui/` 或 `assets/ui/` |

> ✅ **已办（2026-09-30 · `ISSUE-20260930-06`，用户裁定 12）**：这 11 条已回写**本分支 worktree** 的 **`临时\wt-qbicons\.zcode\skills\kirikiri-unpack\SKILL.md` §9.1**（与既有同条**合并去重**后落表；§9 顶部交叉引用句已同步为「11 条 —— 逐条见下方 §9.1；早期摘要：…」）。
> ★ **教训（一审阻断项 B1，必须记牢）**：本条的「已办」首版**不成立** —— 当时落点是**另一分支的 worktree**（派单曾写主工作树绝对路径 `E:\ZCode Workspace\Galgame\.zcode\…`），**本分支根本没有该 §9.1**。⇒ **落点路径必须按本分支 worktree 的相对路径引用**（本分支＝`临时\wt-qbicons\.zcode\skills\kirikiri-unpack\SKILL.md`）；派单给绝对路径时，**先确认它属于本分支 worktree**，否则产物落错树、本分支缺失。

### 5.2 转场遮罩：**可用**（实测）
```tjs
// ★ D-02 订正（2026-10-01）：transsrc 是**终点**（装新画面的那层），不是起点。
//   正确形态＝乒乓双缓冲：stageLayer 留旧画面，snapLayer 装新画面。
stageLayer.beginTransition("universal", true, snapLayer, %[ time: 420, vague: 64,
    rule: "assets/ui/x_mask_rule000_full.png" ]);
//   结束后引擎会**互换这两层** ⇒ 调用方必须互换自己的两个引用（见 §十 10.2）
```
- ★★ **旧写法（首版，已作废）**：`beginTransition("universal", true, snapshot, …)` 且 `snapshot` 装的是**旧**画面 —— 当时以为「transsrc＝起始画面」。**该前提错**：内建淡入类报 `ttExchange`（`visual/TransIntf.cpp:502`）且混合方向是「Phase 0 显示目标层自己的内容 → PhaseMax 显示 transsrc 的内容」，结束时还把两层整体互换 ⇒ 旧写法方向反、且结束后可见的仍是旧画面（**画面恒停旧屏**）。详见 §十 10.2。
- 19/19 成功、**0 降级**。
- 引擎把遮罩按 **8bpp 灰度**载入当阈值表，**alpha 不参与**——所以 UI 组产出的 RGBA 遮罩（灰度已转 alpha）**不会因此失败**。
- 兜底：`crossfade` 降级路径保留，本次一次未触发。
- 素材：`x_mask_rule000_1x.png`(1440×816) 与 `x_mask_rule000_full.png`(1920×1080) 两套（共 18 组 36 件）。**其余 93 张原遮罩**在 `资源组\美术统一\系统UI\rule*.png`（960×544 L 灰度），需要时按同法转换。
  ★ M17 更名：满屏遮罩件原名后缀为 1280 基线时代遗留（实际已 1920×1080），现统一为 `_full`；上列尺寸为 1920 基线实测值。

### 5.3 字体与字号
- 实测 `Font.getList(0)` → 236 个 face，`微软雅黑` 命中。
- 字号基线（1280×720）：标题 46 / 副标题 24 / 名字 20 / 正文 24 / 菜单 22 / 小字 16；正文行距 1.4。
- **正文 24px × 1.4 × 3 行 = 100.8px，容于 118px 文本区**（已实测无截断）。
- ★ **2026-10-09 校准**：以上为 **1280×720 基线**；现行画布 1920×1080，字号 ×1.5 ＝ **标题 69 / 副标题 36 / 名字 30 / 正文 36 / 菜单 33 / 小字 24 / 标签 27**（行距 `body 1.4` / `menu 1.2` 不变）；权威值＝`layout\_root.json` 的 `fonts.sizes`。

### 5.4 素材层的硬事实（**必须知道**）
- **系统UI 交付集中「功能性文字」子族 **537 件**的日文烘焙进像素**（**全量 629 件** ＝ 系统UI **537** ＋ CG背景片尾 STAFF **92**）——**任何中文界面文字都不得依赖图片**。★ **订正（2026-09-30 · `ISSUE-20260930-06`）**：原记「约 250 件（16%）」为**低估**，已作废；逐族穷举实测 **537 件**（口径＝「功能性文字」子族：菜单／按钮／标签／曲名／页号／日期／消息条）。逐族登记见 `素材裁决与图片化日文风险上报.md` §四。
- 具体后果：**选项文本**（原版 `op_*` 40 件是整句日文图）必须来自 `scene_*.jsonl` 的 `choices[].text_cn`；**曲名/章名/日期/配置项标签**在素材里**没有可编辑字串**（原版烘焙成图），数据源见该文件 §六。
- ★ **订正（2026-09-30 · `ISSUE-20260930-06`）**：~~`krkr/assets/ui/` 的 5 件 P 模式（索引色）PNG：`cf_frm_a` `nm_frm_a` `nm_frm_g` `sel00a` `sel00g`~~ ⇒ **本资产集内「无」P 模式 PNG**（`工具\verify_ui.py [5]` 实跑报「P 模式（索引色）清单：**无**」；`ls`/`find`/`git ls-files` 三重 **0 命中**）。**旧指引所指 5 件已随 M34 素材重映射退场**，故不再需要「改存 RGBA 重出」的处置。（另注：`00_UI组认知与接口契约.md` 的「进资产集的 5 件」为 M1 当时口径，同属历史留痕。）

---

## 六、一致性校验（**改完必须跑**）

```bash
cd "工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\工具"
python gen_layout.py     # screens/*.json -> ui_layout.json / ui_layout.tjs / ui_layout.js
python verify_ui.py      # 6 项检查，退出码 0 才算通过
```
`verify_ui.py` 会查：① 引用完整性（layout 引用的贴图是否存在）② 尺寸一致性（无 `nine` 的 `image` 的 `w/h` 必须等于 PNG 实尺寸 → **防止误缩放**）③ 三处数据一致（`.json`/`.tjs`/`.js` 逐键比对）④ **`krkr/game/*.tjs` 硬编码坐标扫描**（可疑清单须为空）⑤ PNG 合法性 ⑥ 体积预算。

**你改 `krkr/game/*.tjs` 后请务必重跑 ④** —— 布局数字必须留在 `ui_layout.tjs` 里，不得散进代码。

---

## 七、UI 组的未完成项 / 待办（**如实交接**）

| # | 事项 | 状态 |
| --- | --- | --- |
| 1 | **一审未派独立 reviewer** | ⚠️ **流程缺口**（本组模块由主代理亲自跑实机验收，但未派独立 reviewer 出结论）——详见工程记录「风险、警示与未完成项」 |
| 2 | TJS2 踩坑清单回写 `.zcode\skills\kirikiri-unpack\` | ✅ **已办（2026-09-30 · `ISSUE-20260930-06`）**：§五.1 的 11 条已回写**本分支 worktree** 的 `临时\wt-qbicons\.zcode\skills\kirikiri-unpack\SKILL.md` **§9.1**（与既有同条合并去重）。★ **落点路径须按本分支 worktree 相对路径引用**（首版误落另一分支 worktree，见 §五.1 末注，一审阻断项 B1） |
| 3 | `config` 屏标签 | ✅ **已定稿（2026-09-30 · `ISSUE-20260930-06`，用户裁定 10/11）**：现行＝系统／声音**两页**、**枚举行 12**（本批删死行「播放影片」3 件）＋ **滑条 9** ＋ 声音页**静音 toggle 6**；行标签**直接写在屏数据里**，并与 `krkr\game\ui_settings.tjs` 的 **25 键 `label` 逐条同名** ⇒ **不是**「按 `cf_*` 件名推断的暂定值」。原 M5 的「14 项／按件名推断」表**已被 M47（`ISSUE-20260924-01`）整体重设取代**。两向差异（原版有本屏无 8 项等）**只登记不补**（详见 `_工作\ISSUE-20260930-06_收尾交接\config_标签定稿.md`） |
| 4 | Fragment（番外）系统**内容与解锁条件留空** | 数据源 `spine.json` 的 `side_stories[]`（53 条 / 6 组）**只取了组名与条数**。<br>★ **ISSUE-20260928-06（2026-09-28，用户裁定）**：独立 `fragment` 屏**已整体删除**，番外 6 组改由**流程图屏独立层**承载；`ui_fragment.tjs` 空壳模块**保留**（无触发路径）。<br>★ **订正（2026-09-30 · `ISSUE-20260930-06`）**：番外 6 组现由流程图屏 **6 组独立层**承载，且**组内全量产出**（53 章全产，G6 **20/20**，改前 12/20）—— 原「**只有空壳**」的表述**不再成立**；**内容与解锁条件仍留编程组** |
| 5 | 流程图节点是**幕/分歧点粒度**（**交付样例 13 节点**） | **全量 712 节点的几何数据**已交 `_工作\ISSUE-20260928-02_第2步\全量布局.json`（**只交几何与数据、不含 `elements`**），**元素化渲染归编程组**；50 个分歧点只上屏 2 个有明确脚本证据者 |
| 6 | 缩略窗元素**两屏各 12 个、id 同名 `sv.thumb1..12`**（`23_save`＋`24_load` 合计 **24 个**；**无 `ld.thumb*`**；旧记「`sv.thumb1..12`／`ld.thumb1..12`」**已作废**）；`dynamic:"slot_thumb"` **仅见于 `note` 契约** | 现为**静态占位件**（`asset: ui/x_ui_psv_slot_thumbwin.png`）；接入时把元素改为 `dynamic:"slot_thumb"`（**元素矩形即落点**），口径见 §四 第 3 项 |
| 7 | `素材裁决与图片化日文风险上报.md` 的 N1–N3 | 已上报资源组，**未改上游文档**（边界规则），**不阻塞** |
| 8 | `ui_demo_script.tjs` 末尾有 `★ M8 追加段` | 该文件是生成物，重跑生成器会覆盖；编程组替换它时请注意 |

---

## 八、交接后维护批（登记，未做）

> 登记于 `ISSUE-20260930-06`（2026-09-30 · 用户裁定 7：闸门加固**本轮不做**）。**下列三项均未执行**，留待交接后 / 编程组接数据时排期；其中第 1、3 项**同步登记在 `UI组_交付总纲.md` §4.3**。

| # | 项 | 现状与风险 |
| --- | --- | --- |
| 1 | **基线总账 `m06` 从 1 屏扩到 17 屏** | `_工作\ISSUE-20260928-02_第2步\复现脚本\m06_delivered_sample_ledger.py` 现只指 `layout\screens\32_flowchart.json`（`SCREEN_REL`）⇒ 其余 16 屏**没有「与交付基线逐字段比」的闸门** |
| 2 | **补「`layout\screens\*.json` 源 ↔ 三处产物」闸门** | `verify_ui [3]` 只做三处产物（`.json`/`.tjs`/`.js`）互比；**数据源改动本身**靠 `工具\test_gen_sync.py`（只见生成器覆盖的屏）⇒ 源与产物之间**缺一道直连闸门** |
| 3 | **清理 `m34_build_screens.build_flowchart()` 的旧字面量** | 该函数含 `fc.mtab*`／`x_ui_ftab_*`／`x_ui_fusen_off.png` 等**旧字面量**，**已登记「实质退休、不得再运行」**；**误跑会整体回退流程图屏**（覆盖当前 296 件交付态） |
| 4 | **`m06` 的 §7.2 可见性变异只有「前向」** | `m02` 的 B3 是**双向**（溢出件改回 `true`、未溢出件改成 `false` 各一条变异）；`m06` 只有前向一条 —— 反向由「G6 带 `visible_default:false` 件数 == 24」的**计数断言**守住，**判据本身是双向的**，仅**变异覆盖面**略窄（一审 Minor，不阻断） |
| 5 | **`layout\screens\_index.json:143` 的金标括注表述** | 现写「（**LF 规范化值**；盘面 CRLF 因 `core.autocrlf=true`）」；实测 `32_flowchart.json` 在 LF 工作副本里 **CRLF=0**、原始字节 md5 即等于金标 ⇒ 该括注是「checkout 后」的**条件性**说明，字面与某些工作副本矛盾，易误读（一审 Minor，不阻断） |
| 6 | **`_工作\ISSUE-20260930-06_收尾交接\接口冻结.md:96` 的旧验收句** | §3.2 原句「改完全库 grep『主音量（语音）』应为 0 命中」已被**§七 §7.3 #2** 取代为「**活跃字段（`sample`／`label`）0 命中**」（24 处历史 `note` 按「历史留痕不改写」保留）；旧句**仍在原位**，先读到 §3.2 的人可能困惑（一审 Minor，不阻断） |
| 7 | **两行节点首行上留白 4px（vs 自订判据 ≥5px）** | vision 实测：`fc.frag6.<NNNN>` 的两行节点 `r3c1`「无论何时·棱镜（性的意义上）」文字 ink `y682–719` 落在节点 ink 带 `678–726` 内 ⇒ **上留白 4px / 下留白 7px**，比布局自订 A 判据「上留白 ≥5px」**少 1px**（字形完整、未触边；本批未动该行）。与既往「引擎实测 4px vs 模型判据 5px 差 1px 已登记」**同源**（`gen_flow_layout.py` 的 `--text-fit-report` 分档表可复核） |
| 8 | **「现行合计」散文数字不在任何闸门内**（★ D-01 2026-10-01 实测暴露） | `17 屏合计`／`N 件` 这类**散文副本**散落在本文件 §一、`作品skill/SKILL.md` 的「★ 现行状态」行、`layout/screens/_index.json` 的 `required[]`、`layout/_schema.md` 等；而 `工具/test_delivery_index_sync.py` **只校验 `UI组_交付总纲.md` 里 5 张 `<!-- GATE: -->` 表** ⇒ 本轮 D-01（`title` 18→24）实测**漏改 3 处「现行 1422」**（`交接编程组.md` §一、`作品skill/SKILL.md`、`_index.json`），**全部由一审人工 grep 抓出、闸门零报警**。建议：把「17 屏合计」接入总纲 GATE，或把 `m06` 总账扩到 17 屏并覆盖这三处散文 |

---

## 九、交接口径补充（用户 2026-09-30 裁定 · 现行）

### 9.1 流程图交互模型（控件几何与态图归 UI 组，逻辑归编程组）

- **滚轮 ＝ 缩放**；**按住拖动 ＝ 上下左右平移**；**右侧滑标 ＝ 纵滚**。
- **缩放条 / 底部横移条 / 右侧纵滚条——三组控件确定保留、待编程组接线**：这三组控件的 `hit` 元素 **`action` 现均为空串**（UI 组只交「元素 + 几何 + 态图」；动作名/接线点见 `layout\_schema.md` §六）。**原「拟删缩放/横移」的旧口径已作废**。
- 依据＝用户 2026-09-30 裁定：「流程图系统需要缩放功能」「顶部缩放条和底部横移条都是有用的」；全量几何**横向超出视口 915px 不处理**（「用户缩放后就能看到超出视口的节点」）。

### 9.2 迷你地图功能正式废弃（不再补回）

- **迷你地图功能正式废弃**：**不补回** `fc.mapview` / `fc.mini1..8` / 回放组 3 件（共 **12 件**）。
- 栏底 `fc.smallmap`（1416,190,443×829）**保留元素与 id**，其用途现为**右栏底板**（右栏四段叠于其上），**不再是迷你地图承载**。
- 与 §四·补.5、§四·补2.1 同口径；规范侧见 `流程图系统_版式规范.md` §〇.6。

### 9.3 `layerExDraw.dll` 的合规口径（用户已接受）

- **用户 2026-09-30 裁定：接受 `layerExDraw.dll`** —— 原「合规签字待办」**关闭**。
- **随包附许可文本**：`krkr\plugin\license_layerExDraw.txt`（与该 dll 同目录，`.gitignore` 精确反忽略）。
- **来源**：本机商业 Steam 版标准构建，sha256 `fe7760906b4ffa0ede8c840b76e8e5b8798131ae7cee4d05ccb13e138a8b5c7d`（32 位、VS2008 静态 CRT、导入仅 `KERNEL32/GDI32/ole32/gdiplus`、导出 `V2Link/V2Unlink`）。
- ⚠ **「与上游 `github.com/wamsoft/layerExDraw` 未改版」（即该哈希对应未改上游源）为推断，非实测** ⇒ **须写进 `成品说明.md`**；**Win7 SP1 未实测**（同 §七 第 5 项与 §五.2）。

### 9.4 ✅ ~~开口项~~ **已闭环**：真实鼠标事件的坐标口径（第 16 批发现，2026-10-01 由编程组 `ISSUE-20261001-06` 实测结清）

> **结论：现行换算正确，四处无需改动。** 编程组源码取证（`environ/win32/TVPWindow.cpp:89` 的 `TranslateWindowToDrawArea` 只在**全屏**时减 letterbox 偏移）＋探针实测 **`kx = ky = 1.5`**（＝画布 1920 / 客户区 1280）。标题屏点不动的真实原因是**文字区热区缺失**（＝ D-01，见 §十 10.1），与本条无关。
> 以下为原开口项描述，保留作历史留痕。

- **事实**：现行配置＝**窗口化** `setInnerSize(1280,720)` ＋ **`setZoom(2,3)`**（`krkr\game\startup.tjs` 的 `:186-198`）⇒ **客户区尺寸（1280×720）≠ 画布尺寸（1920×1080）**。
  而 `startup.tjs` 的 `onMouseMove` / `onClick` 与 `ui_screens.tjs` 的 `uiScreenClick` / `uiScreenHoverClear` **直接把引擎传入的 `x,y` 当画布坐标**（**不由调用方乘 1.5**）。
- **为什么是开口项**：**巡演（`run_autotour.bat`）与全部闸门走的都是「合成指针」**（`kind:"ptr"` 直接按画布坐标调命中路径），**从不经过 Window 事件** ⇒ 这条路径**没有任何自动化证据**。旧注释曾以「用 `setInnerSize(1920,1080)` 且未调用 `setZoom`、客户区 = 画布」为前提为该做法背书，**该前提与 `startup.tjs:187` 的实际代码相反**（注释已于第 16 批订正为如实陈述）。
- **判定方法（约 1 分钟）**：窗口化模式下把鼠标移到任一按钮上（如标题菜单、流程图两枚模式入口），看 **hover 高亮 / 按下态是否跟手**。
- **若不跟手（＝引擎给的是客户区像素）**：`startup.tjs` 的 `onMouseMove`/`onClick` 与 `ui_screens.tjs` 的 `uiScreenClick`/`uiScreenHoverClear` 必须**一起**改为按 zoom 换算（两处不得分叉），**属编程组的活**。
- **若跟手**：本条可关闭，并把「实测跟手」一句补回上述两处注释。
- **影响面**：只影响**真实鼠标**；巡演/闸门/HTML 复刻（canvas 自带坐标换算）均不受影响。

### 9.5 ★ 番外独立层「纵向流水」的接口契约（第 16 批 · **编程组必读**）

**数据现状**：独立层 6 组共 **53 格全部产出**（`fc.frag<G>.<NNNN>` 三件套 ×53 ＝ 159 件）；默认可见 **45 格**，**G6 有 8 格默认不可见**（`fc.frag6.0013…0020`）。
**不可见的 8 格＝溢出视口底的行**（元素盒下沿 `y+h` 分别为 1119 / 1311 / 1503 > 视口底 **1017**）：其**三件全部**带 **`visible_default: false`**（＝数据完整、默认不画）。
**为什么是 `visible_default` 而不是别的**：两端可见性谓词的短路顺序是 **`visible_default !== false` 优先于 flag 判断**（引擎 `krkr\game\ui_screens.tjs:284`；HTML `复刻\replica.js:1721`）⇒ 置 `false` 即「在该层里也默认不画」。
**纵滚实现怎么让它们显示（★ 这是本条的落点，别用 `visible_default`）**：运行期用现成的
 **`ctx.forceShow[el.id]`**（引擎 `krkr\game\ui_widget.tjs:1502`，**优先于** `visible_default === false`）；HTML 侧同名的覆盖表在 `replica.js`。**该机制已有先例**（`fc.pbk_panel`，见 `layout\_schema.md:449`），**不需要给引擎加新接口**。
- **实现要点**：纵滚量 `S` 到位时，把该组**应当可见的行的 id 放进 `forceShow`**（不滚则清空）；**只对 `vis_when == "frag<G>"` 的元素生效**，不得影响主干/外壳。
- **已交付的几何与照此实现的滚量语义**：行 `y = 286 + row*192`（`FRAG_STEP_Y=192`，首行 286）；视口带 `y ∈ [190, 1017]`；**层固定件**（`fc.frag<G>_title_bg`(66,192,444×52)／`_title`／`_back*`(961,196,328×61)）**不随滚**（属外壳语义）。
- **验收（UI 侧已做，编程组接完请复跑）**：巡演 127 张引擎导出 PNG 在 **`y ≥ 1018` 区域节点色像素 = 0**（修复前 G6 第 5 行曾露出半截、实测 **7280 px**）；`--frag-report` 报「产出 53 ／ 未产 **0** ／ 默认可见 45 ／ 纵滚置真 **8**」；`m02`/`m06` 各带**双向**变异自证（溢出件改回 `true`、未溢出件改成 `false`，都必须被检出）。
- ⚠ **巡演断言的限定**：底部横移条（y1018–1043）等**外壳件**仍照常绘制 ⇒ 断言只能写「**独立层节点像素** 0」，**不能**写成「y>1017 全区域 0 像素」。
- ⚠ **另登记（属编程组）**：右侧纵滚条的**高亮段长度不随内容高度变化**（main 9 行 / frag1 3 行 / frag6 7 行三态实测逐像素相同、高亮段恒为 y564–616）⇒ 滚动的**量程**需要按当前层内容高度派生。

---

## 十、★ D-01 / D-02 修复回执（2026-10-01 · `ISSUE-20261001-11`）

> 上游＝编程组交接 `编程组\会话交接_20261001.md` §十二「移交 UI 组的缺陷清单」。**两件均已在 UI 组侧修复。**
> **你方要做的有三件**：① 删 D-01 的 4 个运行期补丁函数 ＋ 2 行调用；② 删 D-02 的 `UI_TRANS_ENABLE = false;` 一行；③ 顺手订正 `编程组\krkr\game\ui_diag.tjs:164-165` 的**陈旧注释**（仍写「`transsrc`＝旧画面快照，目标＝当时的新内容」，与 §10.2 订正后的语义**相反**）。
>
> ★ **2026-10-09 校准：三件均已执行完毕** —— `ISSUE-20261001-13`（`397be72`）拆除 D-01 补丁、恢复 420ms 转场（采纳本组 D-02 真根因）；`ui_diag.tjs` 注释已按 §10.2 语义订正。本回执闭环。

### 10.1 D-01 · 标题屏 6/7 个菜单项缺「文字区热区」

| 项 | 内容 |
| --- | --- |
| 现象 | 标题屏点菜单**文字**判「空区域」、进不去对应界面；只有「鉴赏」正常（用户 2026-10-01 报）。 |
| 正解（已落） | `layout\screens\01_title.json` **18 → 24 件**：补 `title.menu_hit_{1,2,3,4,5,7}_txt` 六件 `kind:"hit"`，**逐条照你方指出的参照件 `title.menu_hit_6_txt`**——几何＝对应 `title.menu_txt_*` 的 `x/y/w/h`；`action` 与 `title.menu_hit_N` 相同；`state_group` 同组；**不带 `state_assets`**（纯热区、零绘制）；`z = 95`。 |
| 三产物 | 已重跑 `工具\gen_layout.py` ⇒ `layout/ui_layout.json` / `krkr/game/ui_layout.tjs` / `复刻/ui_layout.js` 三处同步（md5 见 `UI组_交付总纲.md` §2.3）。 |
| **你方要做** | 删 `编程组\krkr\game\ui_boot.tjs` 的 `uiStoryTitleHitRepair` / `uiStoryTitleHitCheck` / `uiStoryTitleHitCovers` / `uiStoryTitleHitActAt` **四个函数** ＋ `uiStoryWindowInit` 里那 **2 行**调用。你方的几何判据（文字件中心是否已被既有 hit 矩形覆盖）现在会命中本组这 6 件 ⇒ 不删也**补 0 件、自检仍 PASS**（三重幂等），但属冗余代码。 |
| 验证 | `工具\test_click_reach.py`（套件内）逐屏复算「可点元素在自己的几何中心可达」；标题屏 7 项文字区现均落在同组热区内。 |

### 10.2 D-02 · 屏转场被清屏重画 ⇒ 画面恒停旧屏

**★★ 根因与你方原判不同（请以此为准）**：你方判「转场进行中的 120ms 清屏重画」是主因——**实测不是**。那只是**次要**缺陷（会让快速切屏时 `beginTransition` 抛「在使用新的 Transition 之前需要先停止之前的」，用户 11:51 日志里那 2 条；本次修复顺带消掉）。**真正的主因是转场语义被用反**：

1. 内建淡入类处理器（`universal` / `crossfade`）一律报 **`TransType = ttExchange`**（`visual/TransIntf.cpp:502`）；
2. 混合方向由 `tTVPCrossFadeTransHandler::Process` 写死：**Phase 0 显示目标层自己的内容 → PhaseMax 显示 `transsrc` 的内容**；
3. 结束时 `InternalStopTransition` → **`Exchange(TransSrc)`**：把目标层与 `transsrc` **整体互换**（换节点、换 `left/top`、**并交换两者 `visible`**）。

⇒ **`transsrc` 是终点**（要显示出来的新画面），不是起点。旧实现把**旧**画面拷进 `snap`、再把 `snap` 当 `transsrc` ⇒ **方向反** ＋ 结束后**可见的仍是旧画面** ＋ 我们还在往那层（已变**不可见**）上清屏重画 ⇒ **画面恒停旧屏**——正是你方记录的用户现象。
实机探针（修复前巡演，`临时\probe_trans`）：**每次转场结束后 `stageLayer.visible 1→0` / `snapLayer.visible 0→1`**。

**本组已落的正解＝乒乓双缓冲**（`krkr\game\startup.tjs` ＋ `ui_transition.tjs`）：

- 前层 `stageLayer` ＝屏上正显示的**旧**画面（转场**起点**，转场期间**一律不碰**）；后层 `snapLayer` ＝把**新**画面画进去（**终点**，不可见）；
- `stageLayer.beginTransition("universal", true, snapLayer, …)` ⇒ 动画 **旧→新**；结束后按引擎可观测的交换事实**互换两个成员引用** ⇒
  `stageLayer` 恒为「可见且装当前画面」的那一层 ⇒ **你方 `UISaveWin.stageLayer` / `UIStoryWin.stageLayer` 的既有用法照旧成立**（修复前它其实每轮会指向不可见层）；
- 结算有**两条路**：引擎事件 `onTransitionCompleted`（**两层各自**挂——因为会互换，只挂一层则隔轮收不到）+ **超时兜底**（时长 + 120ms，防事件不到时永久冻住重画）；转场仍在场而屏又变了 ⇒ 先 `stopTransition()`（引擎立刻做交换）再切下一屏；
- **不再需要快照拷贝**：`uiTransSnapshot` / `uiTransSetPending` / `uiTransAfterDraw` **整组撤除**，改用一次到位的 `uiTransStart(stage, snap, ruleAsset, timeMs, vague)`（全仓 grep：除**注释**外零引用）。

| 项 | 内容 |
| --- | --- |
| **你方要做** | 删 `编程组\krkr\game\ui_boot.tjs` 里的 **`UI_TRANS_ENABLE = false;`** 一行，恢复 420ms 遮罩转场。 |
| **你方顺手要改** | `编程组\krkr\game\ui_diag.tjs:164-165` 注释仍写「`transsrc`＝旧画面快照，目标＝当时的新内容」——**与订正后的语义相反**（`transsrc` 是**终点**）⇒ 请同步订正，免得下一位读注释再踩同一个坑。 |
| ★ 一处**可选**跟改 | `uiStoryFontSetFile()` 只对 `stageLayer` / `primLayer` 置了 `faceIsFileName = true`。乒乓交换后**新前层**需同样置位，否则内嵌字体兜底（无系统中文字体那条路）在该层失效 ⇒ 中文方块。本组已在 `uiTransSettle()` 内做**镜像**（新前层未置位且后层已置位时补置）⇒ **不改也能跑**；若要显式覆盖，请对**两层都置**（`win.stageLayer` ＋ `win.snapLayer`）。 |
| 自证 | 新增巡演判词 **`★TRANSOSC★`**（现共 7 组，`UI组_交付总纲.md` §3.6 判定线已更新）：断言「转场结束后可见层＝`stageLayer`」。**判据能失败**——把结算函数改成直接 `return false` ⇒ 实测 **PASS 7 / FAIL 12**（如实报「引擎已交换但未结算 ⇒ 画面会恒停旧屏」）。 |
| 实测（**日志已存档**） | 本机 Win10 x64 巡演 **127 屏**（`krkrz 1.4.0.8`，窗口化 1280×720 + `setZoom(2,3)`）：`★TRANSOSC★` **PASS 127 / FAIL 0**；其余六组判词全 PASS；转场 成功 32 / 失败 0 / 降级 0，**起转 32 / 交换结算 32 / 超时放行 0**；`EXCEPTION 0`；缺件 0；PNG 导出 127/127。**证据**：`_工作\ISSUE-20261001-11_证据\判定线汇总.md` ＋ `巡演_正常态_20261001_2015_krkr.console.utf8.txt`（UTF-16LE 原日志转 UTF-8 存档；巡演每跑一次都会清空运行目录，故本轮**首次把日志转存为可追踪证据**）。**窗口实拍**（computer-use，本机）依次显示「读档」→「回想」等不同屏 ⇒ **画面随巡演推进**。 |
| 自证 · `faceIsFileName` 镜像分支（一审指出「只写逻辑、未走过」） | 该分支服务内嵌字体兜底，而 UI 组自建工程里没有编程组的 `ui_boot.tjs` ⇒ 巡演天然走不到。已用**探针演练**造条件（只在**前层**置 `faceIsFileName=true`，＝编程组现状）实跑一次：交换结算 9 次 / **镜像命中 1 次** / 异常 0（命中 1 次正是设计意图：第一次交换后新前层补置一次，此后两层都带标记 ⇒ 幂等）。证据：`_工作\ISSUE-20261001-11_证据\镜像分支演练.md` ＋ 同名日志。⚠ 真机字体加载仍建议编程组用 `forcefilefont.txt` 在**组装后的游戏**里跑一次。 |

---

## 十一、★ D-04 回执：`content_boxes` 画面区改全画布（2026-10-02 · `ISSUE-20261002-06`）

> 上游＝你方移交单 `编程组\移交UI组_D04_画面区改全画布.md`（用户 2026-10-02 裁定）。
> **时序：本批只改数据 + 验证，停在 issue 分支上；未合并、未部署** —— 与资源组 46 件补边背景**同批落地**（移交单 §时序约束）。
> ⚠ 因此 **主工作树（你方 `--data-root` 读的落点）此刻仍是旧值**；落地合并后你方 `ui_story.tjs` / `build_story.py` 自动生效。
>
> ★ **2026-10-09 校准：本回执已落地闭环** —— D-04 已合并进 `main`（`546e9ce`，2026-10-03，与资源组 46 件 16:9 补边同批），成品已带全画布 + 46 件（`03206f8` 更新成品说明）；上文「未合并、未部署 / 主工作树仍是旧值」为**当时留痕**。**残留待办（属本组代码文件，本轮文档校准未动）**：① `krkr\game\ui_demo_script.tjs:83` 的 `Debug.message` 串仍写「（1:1，未缩放）」（D-04 后素材是**拉伸进矩形**，该串已为假话）；② `复刻\replica.js:1029-1035` 注释仍写「与 content_boxes.ot（360,90,1200,900）同尺寸 ⇒ 1:1」。两处均已实测核对、登记待办。

| 项 | 内容 |
| --- | --- |
| 改了什么 | `layout\_root.json`：`content_boxes` 的 `ot/otr/ota/otp/otv` 五源 → **`0,0,1920,1080`**（`np` 原本就是，不动）；`content_box_rule` 改写为**第四条修订注**（注明取代第三条修订注的过渡期口径、裁定出处、素材本体不放大原则不变、时序约束）。 |
| 连带核对 ①（`@auto` 层） | 全 17 屏引用 `content_box` 的**只有 `10_dialog.json::dlg.content` 一处**（`@auto`）。其**静态几何** `360,90,1200,900` → `0,0,1920,1080` 同步改（★ **krkr 端没有 content_box 解析器**，静态几何就是引擎/演示态实际用框；HTML 复刻端由 `resolveBox` 按 `@auto` 取根表覆盖）⇒ 两端同判据。 |
| 连带核对 ②（其它屏写死的 4:3 框） | 全 17 屏扫描 `w,h == (1200,900)`／`(1440,816)`：**0 处**（除 `dlg.content` 外无任何元素用这两个尺寸）⇒ 无遗漏。 |
| 连带核对 ③（HTML 端） | `复刻\replica.js` 的 `BOXES = L.content_boxes`（读生成物）⇒ 重跑 `gen_layout.py` 即同步，**replica.js 零改动**；`resolveBox` 的 `@auto` 语义与 krkr 端（编程组运行期改写 / 演示静态值）等价。 |
| 三产物 | `layout/ui_layout.json` ／ `krkr/game/ui_layout.tjs` ／ `复刻/ui_layout.js` 已重生成（md5 见 `UI组_交付总纲.md` §2.3，**LF 规范化口径**）。 |
| 验证 | `verify_ui` 七项、`gen_layout --check-only`、`test_gen_sync`、`test_state_targets`、`test_click_reach`、总纲 65 项、收据 414 项、`run_all` 41 步、`m39` HTML 双套 —— 全绿（数字见工程记录）。 |
| 逐屏差异 | 巡演 ×2（改前/改后）＋ HTML 无头渲染 ×2，各 17 屏：**数据上只 `dialog` 受影响；`sysicons` 因浮层回溯一层随之变化；其余 15 屏两端各自逐像素一致（mean=0）**。⚠ UI 演示态视觉变化小的真因（一审订正）：**演示态的 `dlg.content` 被 M43 观察白底 `dlg.canvas_white`（z=2）整体盖住** ⇒ 框变化在内容层上不可见；改前/改后唯一可见差＝krkr 演示角标 `dlg.bg_tag` 随框右上角移动（bbox x1504..1919, y0..102），HTML 的 1px 列差是**页面级截图画布右缘的 AA 伪影**（确定性、非内容差异）。**真实素材的落位变化才是本体**：16:9 素材 1200×675 → 1920×1080 满幅；4:3 素材 1200×900 → 1440×1080（左右 240px）——见 `_工作\ISSUE-20261002-06_D04_证据\逐屏差异解读.md`（含量表/并排图/落位示意图 ×2）。 |
| **你方顺手要改（下批）** | ① `krkr\game\ui_demo_script.tjs` 头注释仍停留 800×600 时代、`Debug.message` 固定输出「（1:1，未缩放）」——D-04 后素材被拉伸进 1920×1080 矩形，该日志串已是假话；② `复刻\replica.js:1029-1035` 注释仍写「与 content_boxes.ot（360,90,1200,900）同尺寸 ⇒ 1:1」；③ `dlg.mode_tag`（右上状态标签）note 的「黑边带内、不需要描边」前提已消失，等 46 件亮背景下右上角可读性须复验。 |
