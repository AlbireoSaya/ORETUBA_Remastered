# UI 组 → 编程组 · 交接说明

> 交接方：**UI 美术组**（M0–M8 模块） ｜ 接收方：**编程组**
> Issue：`ISSUE-20260919-11` ｜ 分支：`issue/ISSUE-20260919-11-greta-ui` ｜ 日期：2026-09-19
> 总纲依据：`..\00_项目总纲.md` §七 **I3**（UI 组 → 编程组的交付契约）、§一（三组边界）
> **本文件是编程组消费 UI 组成果的唯一入口**（配合 `UI清单.md` 与 `layout/_schema.md`）

---

## 一、你拿到了什么（5 类）

| # | 交付物 | 路径 | 说明 |
| --- | --- | --- | --- |
| 1 | **krkr 可用 UI 贴图集** | `UI组\krkr\assets\ui\` | **1345 件 / 94.92 MiB**（＝99,533,701 B ≈ 99.5 MB；★ ISSUE-20260928-06 实测重钉；原记「119 件 / 14.57 MB」为早期里程碑读数），全部 krkr 可直接 `loadImages` 加载 |
| 2 | **布局数据（唯一数据源）** | `UI组\layout\screens\*.json` → 生成 `krkr\game\ui_layout.tjs` | **17 屏 / 1420 元素**（★ ISSUE-20260928-07 实测重钉：删 `ending` 屏后 18 屏/1427 元素 → 17 屏/1420 元素；原记「15 屏 / 5991 键」为陈旧读数）。改布局只改 `screens/*.json` 后重跑 `工具\gen_layout.py` | ★ **二审更正（ISSUE-20260928-07）**：上面的枚举**不全** —— 还漏了 `复刻\screen_index.js`（**编辑器用**屏清单，来源 `layout/screens/_index.json`）⇒ **删屏后必须重跑 `工具\emit_asset_index.py`**。本批首版就因漏跑它，导致编辑器屏选择器为空并抛 `TypeError`（一审抓出 Critical）；已修，并已把该步纳入 `run_all.py` 作常驻闸门。
| 3 | **TJS2 UI 组件库 + 可运行演示** | `UI组\krkr\game\*.tjs` | 13 个 `.tjs`；**实机跑通**（`krkr.console.log` 无异常、**17 屏**全可见 —— ★ ISSUE-20260928-06 原记「15 屏」为陈旧读数；★ ISSUE-20260928-07 删 `ending` 后屏数以 `layout/screens/_index.json` 为准＝ **17 屏**） |
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
| `ui_transition.tjs` | 遮罩转场（**实测可用**，见 §五.2） | `uiTransition…` |
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
| 2 | **背景/立绘层** | 布局里 `dynamic:"story_background"` / `"story_chara"` 的层由你填真实素材，框位取根 `content_boxes[源代号]`（D1：`ot/otr/ota/otp`→`240,60,800,600`；`otv`→`160,88,960,544`；`np`→`0,0,1280,720`）。**不得缩放素材本体** |
| 3 | **存档缩略图** | `dynamic:"slot_thumb"` 的 16 处由你填真实存档截图 |
| 4 | **动作实现** | `hit.action` / `list.actions` 的动作名表见 `layout\_schema.md` §六。**未定义动作一律写空串**，不得臆造。`list` 的槽号用 `slot_base` + 项序号 |
| 5 | **音频/视频** | 无内建 MP3；OGG 走 `wuvorbis.dll`、Opus 走 `kropus.dll`。视频格式**未确认**（总纲 G3），属你的缺口 |
| 6 | **字体缺口** | 总纲 **G2**：krkr 不自带字体、无中文字体内嵌方案。UI 组已做到「不依赖特定字体 + `Font.getList()` 探测回退」，**但目标机若没有中文字体仍需你解决**（`Font.faceIsFileName` 是内嵌 TTF 的唯一入口，**UI 组未实测**） |
| 7 | **KAG3 路线** | 总纲 **G1**：工作区无 KAG3/KAGEX 框架。UI 组按**自研 TJS2** 交付（POC 已实机闭环）。**你若改用 KAG3，UI 库需重写为 `.ks`——请先与 UI 组对齐** |
| 8 | **署名** | 窗口标题须含 `来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode`（AGENTS.md §六）。`startup.tjs` 已写入，你换入口时**不要漏** |

---

## 四·补　流程图右栏「章节详情」四段重排（`flowchart` 屏 · `ISSUE-20260929-02`）

> **本节是用户指令 5 的落点**（「必须在说明文档里详细介绍它们的用法，好让编程组能够高效运用」）。
> **数值唯一依据**＝`UI组/_工作/ISSUE-20260929-02_右栏大改/接口冻结.md` §B／§C（主代理 2026-09-29 冻结）。本屏由 `工具/gen_flow_layout.py` 生成（右栏这些件是该脚本内嵌的**静态元素快照**）⇒ **要改就改生成器，不要手改 JSON**。
> ✅ **落盘状态（2026-09-29 · E3 交付时实测：**全部到位**）**：① **素材** `krkr/assets/ui/x_ui_playwin_bg.png`（380×300 RGBA）与 `x_ui_pbkick_pause_{off,over,on}.png`（119×119 RGBA）**已在库**；② **生成器** `工具/gen_flow_layout.py` 已含本节全部元素契约（`STATIC_FLAG_EXEMPT = {"fc.pbkick","fc.pbkick_pause"}`、`flags_default = {fc_layer:"main", fc_replay:"play"}`）；③ **屏数据** `layout/screens/32_flowchart.json` **已重跑**（**280 件元素**；`fc.play_win`/`fc.play_view`/`fc.pbkick`/`fc.pbkick_pause` 已在、**12 件退场件零残留**）。**本节数值已与屏数据逐字段核对一致**，并附「生成器 ↔ 屏数据」两源一致性断言（共 **134 条断言全绿**，证据在 `_工作/ISSUE-20260929-02_右栏大改/证据/`）。**若日后屏数据再变，以屏数据为准并回报 UI 组。**
> ★ **总口径（先读这条）**：UI 组本轮只交「**元素 + 几何 + 状态位 + 动作名**」。**画面时序／帧序列／音频的播放本身，以及一切运行期文字填充，均属编程组接线 —— 本批一律未生效，本文不声称任何功能已生效**（与既有 `bgm_playpause`、`replay_play:<行号>` 同口径）。

### 4·补.1　右栏四段（栏底 `fc.smallmap` 一个字段未改）

| 段 | 件 | 几何 (x, y, w×h) | z | 说明 |
| --- | --- | --- | --- | --- |
| ① 大播放窗 | `fc.play_win` | (1448, 214, 380×300) | 6 | 底板；y **214–514** |
| | `fc.play_view` | (1454, 220, 368×288) | 7 | **动态画面层**（四周内缩 6px） |
| ② 标题 | `fc.p_title` | (1416, 536, 443×73) | 6 | 底槽；y **536–609** |
| | `fc.p_title_tx` | (1428, 546, 419×40) | 25 | 一行标题（`y = 底 + 10`） |
| ③ 说明 | `fc.p_text` | (1425, 631, 422×171) | 6 | 底槽；y **631–802** |
| | `fc.p_text_tx` | (1437, 637, 398×159) | 25 | 多行说明（`y = 底 + 6`） |
| ④ 台词 | `fc.p_message` | (1425, 824, 422×171) | 6 | 底槽；y **824–995** |
| | `fc.p_message_tx` | (1437, 830, 398×159) | 25 | 多行台词（`y = 底 + 6`） |
| 栏底（**不动**） | `fc.smallmap` | (1416, 190, 443×829) | 5 | 整栏底，本批**零改动** |

- **边距/段距**：栏内上边距 24、下边距 24、段间 22 ⇒ 四段 + 边距 **恰 829**，与栏底等高（214−190＝24；536−514＝22；631−609＝22；824−802＝22；1019−995＝24）。
- **横向**：三槽底的 **x/w 一律沿用 PSB 原样**（标题底 `1416/443`；说明与台词底 `1425/422`）⇒ 标题文字框比另两槽宽 21px（`1428` 起 / `419` 宽 ⤳ 对比 `1437` 起 / `398` 宽）。**这是参照作原样，不是错位**，请勿自行对齐。
- 大播放窗在 **443 栏宽内居中**：`x = 1416 + (443 − 380) // 2 = 1448`（左留 32 / 右留 31）。

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
3. **热区与按键同轴**（119×119 外扩 6px ⇒ 125×125）**且两键共用同一条热区**（两键同位置 ⇒ 一条即够）：点它就是派发 **`flow_replay_toggle`（拟用名）**，语义＝「**播放/暂停切换**」。
   ★ **语义边界**：**命中即派发**；**画面时序／帧序列的播放本身留你们接线，本批不声称已生效**（与 `bgm_playpause`、`replay_play:<行号>` 同口径）。`fc_replay` 的翻转与两键换显由你们在分派里完成（数据侧只登记「谁发、发什么」）。
4. **三态语义（易误读，务必按此实现）**：两件都用既有的 **`state_assets{normal, hover, pressed}` 三槽**口径，**不是「开/关」两态**。其中 **`pressed`（按下态）用的就是 `_on` 件**：播放键的 `_on` 是 **■**、暂停键的 `_on` 是 **‖** —— 它们是**按住时的高亮图形**，**不是**「正在播放／已暂停」的状态指示。**「当前是播放还是暂停」只由 `fc_replay` 决定**（哪个键可见）。
5. 暂停键素材由播放键三态**派生**（盘面／羽化／描边与同态播放键逐像素同源，只替换中央字形掩膜），落 `krkr/assets/ui/x_ui_pbkick_pause_{off,over,on}.png`（119×119、**真 alpha / PNG-32**）。

### 4·补.4　三个文字槽怎么用（用户点名要求写清）

| 件 | 语义 | 几何 | 排版字段 | `sample`（现为占位） |
| --- | --- | --- | --- | --- |
| `fc.p_title_tx` | 章节**标题**（一行） | (1428, 546, 419×40) | `h:40`；`valign:"middle"`；`wrap:false`；`max_lines:1` | `"标题"` |
| `fc.p_text_tx` | 章节**说明**（多行） | (1437, 637, 398×159) | `valign:"top"`；`wrap:true`；`max_lines:5` | `"说明"` |
| `fc.p_message_tx` | **台词**（多行） | (1437, 830, 398×159) | `valign:"top"`；`wrap:true`；`max_lines:5` | `"台词"` |

1. **样式（三件一致）**：**白字（`@palette.text_primary` ＝ `#FFFFFF`）＋ 黑描边**（`outline:true` / `outline_color:"#000000"` / `outline_width:2`；`shadow:false`）；`font.size` **24**、`bold:true` **不变**。这是 **M38 既有机制**（krkr 侧八向描边 ／ HTML 侧 `text-shadow` 八向，**两端已通**），**纯渲染、不参与布局** ⇒ 描边既不挤字、也不改变折行与容量判据。
2. **容量依据（多行槽）**：槽净高 **159px** ÷（24px × **1.3** 行距 ＝ 31.2px）≈ **5.09** ⇒ `max_lines:5`（**冻结书口径**；行距取全局基线，元素**不写** `line_spacing`）。
   ⚠ **提醒：别写超过 5 行。** 超出部分按 `max_lines` **截断**（不绘第 6 行、也不打省略号），折行/行首行尾禁则走引擎自己的算法（krkr `ui_theme.tjs::uiThemeWrap`／`uiThemeLayoutText`；HTML 复刻侧按 `e.w / e.max_lines` 同判据实现，见 `复刻/replica.js`）。本批三槽**都不是滚动槽**；确需更长请缩短文案或回报 UI 组重排。
   ⚠ **待复核（E3 实测提醒，非冻结书内容）**：`layout/_root.json` 的全局 `fonts.line_spacing.body` 实为 **1.4**（`ui_theme.tjs` 的 `lineH = Math.floor(size × 行距)` ⇒ `floor(24 × 1.4) = 33px`）；按 33px 算，**5 行块高 165px > 槽净高 159px**（差 6px）。⇒ 填 **5 行**时请留意第 5 行是否越出槽底；**填 ≤4 行在任何口径下都安全**。以实机导出 PNG 为准。
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
- `fc.smallmap` 仅作**栏底**保留，本批**未**给它任何运行态。

### 4·补.6　载入屏（`loading`）：`ld.bg` 已删除

- `layout/screens/22_loading.json` 的**满幅底元素 `ld.bg` 已删除**（用户指令 6）；该屏由 **3 件 → 2 件**：`ld.dim`（满幅压暗 rect，`@palette.backdrop` `#000000` ×100）与 `ld.text`（引擎绘「载入中…」，白字 + 蓝描边）—— **这两件一个字段都没改**（`ld.bg` 删前 z=0，删后 `ld.dim` z=1 成为本屏最底层；该屏实际下衬什么由你们的屏栈决定，UI 组未改机制）。
- **素材 `ui/x_ui_backlog_bg.png` 保留不删**（1916×1080，md5 `5d05e6e90ce7b5080b7f040b3571a42f`）。★ **勘误**：原记「该素材仍被 `26_backlog` 引用、删文件即断链」**不成立** —— `26_backlog` 自 PSV 换皮（`ISSUE-20260926-06` · B 组）起底图已改引 `ui/x_ui_psv_backlog_bg.png`；删 `ld.bg` 后 `x_ui_backlog_bg.png` 在**全 17 屏屏数据中零元素引用**（仅 `复刻/asset_index.js` 素材清单仍列出它）。
- ⇒ 若你们的 loading 呈现需要“压死背景”，请在屏栈／过渡里处理，**不要回加满幅底图**（那是用户明确要求删除的）。

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

> 建议 UI 组把这 11 条回写 `.zcode\skills\kirikiri-unpack\`（见 §七 待办）。

### 5.2 转场遮罩：**可用**（实测）
```tjs
layer.beginTransition("universal", true, snapshot, %[ time: 420, vague: 64,
    rule: "assets/ui/x_mask_rule000_full.png" ]);
```
- 19/19 成功、**0 降级**。
- 引擎把遮罩按 **8bpp 灰度**载入当阈值表，**alpha 不参与**——所以 UI 组产出的 RGBA 遮罩（灰度已转 alpha）**不会因此失败**。
- 兜底：`crossfade` 降级路径保留，本次一次未触发。
- 素材：`x_mask_rule000_1x.png`(1440×816) 与 `x_mask_rule000_full.png`(1920×1080) 两套（共 18 组 36 件）。**其余 93 张原遮罩**在 `资源组\美术统一\系统UI\rule*.png`（960×544 L 灰度），需要时按同法转换。
  ★ M17 更名：满屏遮罩件原名后缀为 1280 基线时代遗留（实际已 1920×1080），现统一为 `_full`；上列尺寸为 1920 基线实测值。

### 5.3 字体与字号
- 实测 `Font.getList(0)` → 236 个 face，`微软雅黑` 命中。
- 字号基线（1280×720）：标题 46 / 副标题 24 / 名字 20 / 正文 24 / 菜单 22 / 小字 16；正文行距 1.4。
- **正文 24px × 1.4 × 3 行 = 100.8px，容于 118px 文本区**（已实测无截断）。

### 5.4 素材层的硬事实（**必须知道**）
- **系统UI 交付集约 250 件（16%）的日文烘焙进像素**——**任何中文界面文字都不得依赖图片**。逐族登记见 `素材裁决与图片化日文风险上报.md`。
- 具体后果：**选项文本**（原版 `op_*` 40 件是整句日文图）必须来自 `scene_*.jsonl` 的 `choices[].text_cn`；**曲名/章名/日期/配置项标签**在素材里**没有可编辑字串**（原版烘焙成图），数据源见该文件 §六。
- `krkr/assets/ui/` 的 5 件 P 模式（索引色）PNG：`cf_frm_a` `nm_frm_a` `nm_frm_g` `sel00a` `sel00g` —— 若 krkr 加载异常，用 `工具\make_assets.py` 改存为 RGBA 重出即可（**先实测**）。

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
| 2 | TJS2 踩坑清单回写 `.zcode\skills\kirikiri-unpack\` | 待办（§五.1 的 11 条） |
| 3 | `config` 屏 14 项标签是**暂定中文** | 待用户/编程组确认（依据为 `cf_*` 件名推断，置信度已逐条标注，见 `_工作\M5_布局报告.md` §2.6） |
| 4 | Fragment 系统**只有空壳** | 内容与解锁条件按用户要求留空；数据源 `spine.json` 的 `side_stories[]`（53 条 / 6 组）**只取了组名与条数**。<br>★ **ISSUE-20260928-06（2026-09-28，用户裁定）**：独立 `fragment` 屏**已整体删除**，番外 6 组改由**流程图屏独立层**承载；`ui_fragment.tjs` 空壳模块**保留**（无触发路径） |
| 5 | 流程图节点是**幕/分歧点粒度**（13 节点） | 非 712 场景级；50 个分歧点只上屏 2 个有明确脚本证据者 |
| 6 | `dynamic:"slot_thumb"` 16 处 | 占位，待真实存档截图 |
| 7 | `素材裁决与图片化日文风险上报.md` 的 N1–N3 | 已上报资源组，**未改上游文档**（边界规则），**不阻塞** |
| 8 | `ui_demo_script.tjs` 末尾有 `★ M8 追加段` | 该文件是生成物，重跑生成器会覆盖；编程组替换它时请注意 |