# UI 组交付总纲（给编程组的唯一入口）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：权威（UI 组交付索引 + 接口与验收；被 `<!-- GATE: -->` 包住的 5 张表由 `工具\test_delivery_index_sync.py` 守门） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> **本文件是 UI 美术组交付物的总索引**：先读它，再按需跳到细节文档。
> 定位＝**索引级 + 接口与验收**：只给「东西在哪、怎么用、怎么验、缺什么」，不写教学式教程。
> Issue：`ISSUE-20260929-07` ｜ 用户 2026-09-29 裁定：落点＝`UI组\` 下新增本文件；深度＝索引级 + 接口与验收。
> ★ **数字分两类**：被 `<!-- GATE:name -->` 标记的 **5 张表**（§2.1 资源族、§2.2 头像集、§2.3 三处产物、§3.2 逐屏元素、§4.3 预算）由
> `python 工具/test_delivery_index_sync.py` 与磁盘逐格对账（改了资源/数据请一并重跑）；**散文里的其它数字**（脚本支数、`_工作` 规模、动作计数…）
> **闸门覆盖不到**，属人工核对 ⇒ 以闸门与磁盘为准，发现出入请改本文。

---

## 〇、30 秒版

- 本作 UI **全部是自研 TJS2**（**不是 KAG3**）：代码在 `krkr\game\*.tjs`，贴图在 `krkr\assets\ui\*.png`。
- **数据只有一个上游**：`layout\screens\*.json`（配 `layout\_root.json` / `layout\palette.json` / `layout\_schema.md`）
  → 生成器 `工具\gen_layout.py` → 三处同源产物 `layout\ui_layout.json` / `krkr\game\ui_layout.tjs` / `复刻\ui_layout.js`。
- **不要手改任何生成物**（三个 `ui_layout.*`、`复刻\asset_index.js`、`复刻\screen_index.js`、`复刻\flow_data.js`、`krkr\game\ui_flow_data.tjs`）。
  改数据 → 跑生成器 → 跑闸门，最小清单见 §3.5。
- 1:1 HTML 复刻与可视化编辑器在 `复刻\`，**双击即用**（`file://`，不依赖网络/CDN，也不 `fetch()`）；
  贴图是**相对引用** `../krkr/assets/ui/`，所以 `复刻\` **不能单独拷走**。
- 画布基线 **1920×1080**；窗口化按 `setZoom(2,3)` 呈现 1280×720，全屏 1:1。
- 现状：动作分三类（§3.4）——**A 类＝两端已实现**、**B 类＝仅派发/占位**、**C 类＝两端均无分支（留编程组；逐条列在 §4.2）**；**动态层**：4 类契约中**已挂载 2 类**（`story_background` @ `dlg.content`、`flow_scene_frames` @ `fc.play_view`）**均未填充**、另 2 类（`story_chara`／`slot_thumb`）**尚无数据落点**（详见 §4.2 第 5 行）—— 这些（C 类动作 ＋ 动态层填充 ＋ B 类的实效）是编程组的活。★ **三类的计数不在本纲写死**，一律以 `UI组\交付包校验收据.md` 为权威（§五 第 4 条）。
- **编程组接手请直接看 §六「编程组上手清单（按优先级）」** —— 按「不接就跑不起来 → 接了才完整」排好的单一待办表。
- ★ **本件只覆盖「UI 组交付面」**；**资源组侧的交付入口**＝`..\资源组\交接编程组\编程组开工指南.md`（一页版）＋ `..\资源组\交接编程组\交接说明.md`（细节手册，含 C1–C20），其**全包自检**＝`..\资源组\工具\audit_handoff_package.py`。**剧情文本、素材来源与统一、美术统一集的取数以资源组为准**（本件 §4.1 已列归属）。两个组的入口互相独立、**都按用户 2026-09-30 的口径「只给指针、不搬文件」**。

---

## 一、什么时候读哪份（文档分工）

| 文档 | 管什么 | 什么时候读 |
| --- | --- | --- |
| **本文件**（`UI组_交付总纲.md`） | 总索引：东西在哪 / 怎么用 / 怎么验 / 缺什么 | **先读它**，然后按下面的指路跳转 |
| `UI组交接编程组.md` | 编程组消费 UI 成果的**散文入口**：逐批增量说明、机制口径、动作语义边界、待办 | 要接某一个具体功能（动作/机制）时读对应小节 |
| **本文件 §六 编程组上手清单** ＋ `UI组\交付包校验收据.md` | **编程组按优先级开工的单一待办表**（做什么／落点／怎么验／详见）；校验收据＝交付物的**可复跑**逐件清单（路径／件数／字节／md5） | 编程组接手时**先读 §六**；要核对「A/B/C 三类计数、占位动作处数」或查交付物指纹时读校验收据 |
| `layout\_schema.md` | **机器可读契约**：屏对象字段、7 个 `kind`、列表/滑块/动态层字段、§六 动作名表、生成物与守门 | 要改数据、要写代码读数据时**必读** |
| `UI清单.md` | **资产契约**（★ 2026-10-09 校准：本表为 M1–M22 期逐件表；现行 1359 件的族级计数见 §2.1、逐件文件索引见 `复刻\asset_index.js`）：逐件命名/尺寸/九宫格参数/加载方式/对应原版元素 | 要加载某张贴图、核对尺寸或九宫格参数时读 |
| `流程图系统_版式规范.md` | 流程图专项：几何/排版/连线/番外独立层规范与终值参数 | 只做流程图相关改动时读 |
| `M34_UI复刻总纲.md` | 风格总纲（弃旧素材、按参照作结构重绘的裁决） | 要判断「这个素材/配色该长什么样」时读 |
| `00_UI组认知与接口契约.md` | 本组的开工认知与三组间接口契约 | 想了解「为什么这么分工」时读 |
| `头像素材清单.md` | 361 张对话框头像的几何口径与再生链 | 要用头像（`face/` 命名空间）时读 |
| `素材裁决与图片化日文风险上报.md` / `PSV换皮_素材与文字处置清单.md` | 素材可用性裁决、图片化日文风险、PSV 换皮口径 | 要判断某素材能否直接用/是否含日文时读 |
| `to-do-list.md`、`会话交接_*.md`（多份） | 组任务清单与逐会话状态快照（**接手先读最新一份**） | 接手本组工作时读 |

**一句话分工**：**接口看 `_schema.md`，逐功能看 `UI组交接编程组.md`，取件看 `UI清单.md`，风格看 `M34_UI复刻总纲.md`。**

---

## 二、交付物地图（资源面）

### 2.1 资产集 `krkr\assets\ui\`（1359 件 / 95.94 MiB）

<!-- GATE:asset_families -->
| 族 | 件数 | 字节 | 用途 |
| --- | ---: | ---: | --- |
| x_gal | 703 | 50,602,143 | CG 鉴赏缩略图（程序化生成） |
| x_ui | 590 | 21,068,084 | 通用 UI 件（面板/按钮/图标/PSV 换皮/配置/回想/鉴赏/快捷条…，约 83 个子族） |
| x_mask | 36 | 15,239,157 | 转场遮罩（`_full`＝满幅 1920×1080；`_1x`＝旧 4:3 内容区 1440×816——★ **D-04 后已无对应框，18 件 `_1x` 为休眠资产、无消费方**（转场常量取 `_full`）） |
| x_gen | 26 | 8,196,219 | AI 生图/派生整页件（对话框无框前素材、番外/鉴赏整页、logo） |
| x_bg | 2 | 3,746,346 | 满幅背景（`x_bg_system` / `x_bg_flowchart`） |
| tl2 | 1 | 1,750,408 | 标题底（历史族） |
| panel_frame.png | 1 | 1,755 | 九宫格边框（由 `if_*` 八件拼合，无前缀） |
| 合计 | 1,359 | 100,604,112 | — |
<!-- /GATE:asset_families -->

- **命名规则**：原版取件沿用原物理名（**不加 `ui_` 前缀**，目录已承载 `ui/` 语义）；本组自制/重制件一律 `x_<语义>.png`，
  子族用 `x_<域>_<对象>_<态>.png`，态后缀 `_off/_on/_over` 或 `normal/hover/pressed`。
- 改动注意：**增删素材后必须重跑** `工具\emit_asset_index.py`（否则 `复刻\asset_index.js` 与编辑器看不到新件）。
- ⚠ **体积预算很紧**：见 §4.3。

### 2.2 对话框头像集 `krkr\assets\face\`（**不入库，可再生**）

<!-- GATE:face_set -->
| 项 | 值 |
| --- | ---: |
| 件数 | 361 |
| 字节 | 52,218,374 |
<!-- /GATE:face_set -->

- 它被根 `.gitignore` 排除（`…/UI组/krkr/assets/face/*.png`），**克隆仓库后没有这些文件**；
  再生：`_工作\M44_头像裁切方案\复现脚本\m44_make_faces.py`（口径见 `头像素材清单.md`）。
- 引擎/HTML 以 `face/<族>.png` 的 **`face/` 命名空间**引用（asset 串首段为 `face/`）。
- ⚠ **已知文档缺陷**：`头像素材清单.md` 写「合计 83.0 MB」是 M44 早期口径，**实测为 52,218,374 B**；以本表为准。

### 2.3 布局数据源与三处产物

- **上游（唯一数据源）**：`layout\screens\*.json`（17 屏）、`layout\_root.json`（画布 1920×1080、内容框、字体回退链）、
  `layout\palette.json`（唯一色值来源，layout 里一律写 `@palette.<key>`）、`layout\_schema.md`（契约）。
- **产物（禁止手改，由 `工具\gen_layout.py` 生成）**：

<!-- GATE:products -->
| 产物 | md5 |
| --- | --- |
| `layout/ui_layout.json` | `8159c97cf81df11024cbde3b68370431` |
| `krkr/game/ui_layout.tjs` | `27e25a2e53e63380ee1cc93392d68ead` |
| `复刻/ui_layout.js` | `e3176b2d2f3355816a3a5d01ec996f09` |
<!-- /GATE:products -->
- **口径（★ 2026-10-01 统一，`ISSUE-20261001-11`）**：上表 md5 与 `交付包校验收据.md` 的 ⑥ 一致，一律**先把 `\r\n` 折成 `\n` 再算**（`core.autocrlf=true` ⇒ 同一份 blob 在不同 worktree / 不同检出时机会以 CRLF 或 LF 落盘；按原始字节算 md5 会让**同一份内容得到两个值**，使「口径副本 vs 磁盘真值」的闸门在**换检出面**时报假失败——本工程已踩三次：`m06` 总账、本闸门、2026-10-01 合并后主工作树上的收据闸门）。实现见 `工具\test_delivery_index_sync.py::md5_of`（唯一实现，两处闸门共用）。

- 三处顶层键相同（11 个：`_comment/canvas/content_boxes/content_box_rule/fonts/font_rule/asset_root/signature/canvas_baseline/palette/screens`），`screens` 均为 17 屏。
- 另有自动生成物：`复刻\flow_data.js`（`gen_flow_data.py`）、`krkr\game\ui_flow_data.tjs`、
  `复刻\asset_index.js` + `复刻\screen_index.js`（`emit_asset_index.py`）、`krkr\game\ui_demo_script.tjs`（演示台词，**含手写追加段，重跑会丢**）。

### 2.4 引擎侧代码 `krkr\game\`（16 个 `.tjs`）与插件

| 类别 | 文件 | 说明 |
| --- | --- | --- |
| **自动生成（勿手改）** | `ui_layout.tjs` / `ui_flow_data.tjs` / `ui_demo_script.tjs` | 分别由 `gen_layout.py` / `gen_flow_data.py` / `_工作\M2_证据\extract_demo_lines.py` 产出 |
| 手写 | `startup` | 工程入口：窗口/图层/装载/输入/巡演驱动 |
| 手写 | `ui_asset` | 贴图加载与缓存、缺件兜底、装载摘要 |
| 手写 | `ui_widget` | 五种渲染器（image/text/rect/hit/list/anim）与逐项渲染、滑块 |
| 手写 | `ui_screens` | 屏级 flag、绘制调度、**动作派发 `uiActionDispatch`**（未实现动作的回落入口在此） |
| 手写 | `ui_dialog` | 打字机、说话人、场景切换 |
| 手写 | `ui_theme` | palette/字号/行距解析、**折行与禁则**、文字八向描边 |
| 手写 | `ui_settings` | 设置项读写与 25 键设置仓 |
| 手写 | `ui_state` | 存档/已读 |
| 手写 | `ui_transition` | 转场快照与规则 |
| 手写 | `ui_flow` | 流程图主逻辑（含 `flow_enter` 包装器） |
| 手写 | `ui_flow_layer` | 番外独立层切换与 `current` 高亮环 |
| 手写 | `ui_flow_links` | 连线绘制（顶点由生成器算好，本文件只描线） |
| 手写 | `ui_fragment` | 番外屏本体已删，动作与素材保留（**无触发路径**） |

- 插件 `krkr\plugin\layerExDraw.dll`（sha256 `fe776090…`，附 `license_layerExDraw.txt`；本目录 `.gitignore` 精确反忽略它）。
  **连线与 `current` 环依赖它**：`Plugins.link` 失败即 try/catch 降级 ⇒ **一条连线都不画**（不崩、不抛），`flow_layer` 返回「切层不可用」。
  ⚠ 它**不在 `verify_ui` 的体积预算内**（预算只算 `assets\ui`），但**必须随包分发**。

### 2.5 HTML 复刻与编辑器 `复刻\`

| 文件 | 作用 |
| --- | --- |
| `index.html` | **人工验收用的 1:1 复刻入口**（`?screen=<id>` 深链；`?hover=<action|id>` 悬停探针；`?selftest=1` 跑自检） |
| `editor.html` | 可视化布局编辑器（拖拽/吸附/撤销；导出下载同名 `screens\*.json`，**不直接写盘**） |
| `flow.html` | 流程图 1:1 复刻 |
| `_selftest_states.html` | 状态自检页（套 A） |
| `replica.js` / `replica.css` | 数据驱动渲染内核（与引擎同判据） |
| `editor_core.js` / `editor_ui.js` / `editor.css` / `flow.css` | 编辑器内核与界面、流程图样式 |

### 2.6 工具链 `工具\`

| 类别 | 脚本 | 何时跑 |
| --- | --- | --- |
| **生成器** | `gen_layout.py`、`gen_flow_data.py`、`gen_flow_layout.py`、`emit_asset_index.py` | **改了对应数据就必须跑**（§3.5） |
| **闸门** | `verify_ui.py`、`verify_editor_export.py`、`test_flow_links.py`、`test_gen_sync.py`、`test_state_targets.py`、`test_click_reach.py`、`test_quickbar_reach.py`、`test_verify_asset_refs.py`、`test_gate_field_granularity.py`、`test_screen_index_sync.py`、**`test_text_ellipsis.py`**（省略号三处同判据交叉闸门）、**`test_delivery_index_sync.py`**（本文件数字） | 验收时跑；**不改数据** |
| 一次性素材生成器（约 26 支，`m33_*`/`m47_*`…/`psv_*`） | 各批素材已交付 | 通常**不再重跑**；重跑须先读该文件头契约（部分重跑会回退已交付素材） |

### 2.7 `_工作\`（证据与复现脚本区，**大部分不入库**）

- 111 个子目录 / 约 10,500 个文件 / 约 3.9 GB；每个批次一个目录，内含 `证据\`、`复现脚本\`、`接口冻结.md`、`方案.md`。
- 按根 `.gitignore` 排除：`_工作/**/*.png`、`**/*.jpg`、`**/*.npy`、若干 dump HTML（另有少量显式反忽略的证据图）。
  ⇒ **克隆后 `_工作\` 里只剩文本类证据**；要复现图片证据请跑各目录的 `复现脚本\`。
- 例外：`_工作\ISSUE-20260929-05_模式入口\证据\一审_复核报告.md` 等**审查报告属正式证据，入库**。

---

## 三、接口：数据模型、机制与验收

### 3.1 元素模型（`layout\_schema.md` 为唯一权威）

- **7 个 `kind`**：`image` / `text` / `rect` / `hit` / `list` / `anim` / `slider`。
- **通用字段**：`id`、`kind`、`z`、`visible_default`、`vis_flag`、`vis_when`、`nine`、`opacity`、`color`、`note`、`source` 等。
- **`text`**：`font{size,bold,color,shadow,shadow_color,shadow_ofs,outline,outline_color,outline_width}`、`align/valign/wrap/max_lines/line_spacing/sample`。
  铁律：**文字元素不得带 `state_assets`** —— 需要三态就由图（底光/底图）承载，文字本身不参与换态。
- **`hit`**：`action`（动作名，见 §3.4）、`label`、`state_assets`、`state_group`（组绑定换态）。
- **`list`**：`orientation/x/y/w/item_w/item_h/gap/max_rows/max_cols/stack_bottom/labels/actions/item_frame/highlight/scroll`；
  子结构 `item_frame.state_assets`（**逐项三态**）、`item_text`（逐项台词，折行）、`item_buttons[]`（逐项按钮，动作串可带 `%row%` 行号）、`item_variants`（同栏位多差分）。
- **`slider`**：`x/y/w/h/min/max/step/value/setting/rail/handle`；`setting` 指向**设置仓**（`UISettingDef`，9 数值 + 16 枚举 = 25 键）。
  其中「文本窗口的不透明度」滑块**实时改变对话框遮罩浓度**（`dlg_winopac` → `ctx.opacityOverride`）。
- 屏级机制见 §3.2；连线 `links[]` 在屏数据顶层（`state/pts/w/color/arrow`，顶点由生成器算好）。
- ⚠ **生成物里不要出现硬编码坐标**：`verify_ui [4]`（白名单 W1–W6）会扫 `krkr\game\*.tjs`，清单非空即失败。

### 3.2 屏与叠层（17 屏）

<!-- GATE:screen_elements -->
| 屏 id | 文件 | 件数 |
| --- | --- | ---: |
| title | `01_title.json` | 24 |
| dialog | `10_dialog.json` | 9 |
| confirm | `21_confirm.json` | 53 |
| loading | `22_loading.json` | 2 |
| save | `23_save.json` | 165 |
| load | `24_load.json` | 165 |
| config | `25_config.json` | 467 |
| backlog | `26_backlog.json` | 11 |
| gallery | `27_gallery.json` | 17 |
| music | `28_music.json` | 27 |
| flowchart | `32_flowchart.json` | 296 |
| sysicons | `33_sysicons.json` | 20 |
| quickbar | `35_quickbar.json` | 49 |
| choices | `36_choices.json` | 1 |
| dress | `37_dress.json` | 94 |
| replay | `38_replay.json` | 11 |
| gal_shell | `39_gal_shell.json` | 17 |
| 合计 | — | 1,428 |
<!-- /GATE:screen_elements -->
- ★ **D-01（2026-10-01 · `ISSUE-20261001-11`）**：`title` 屏 **18 → 24 件**（补 6 件文字区热区`title.menu_hit_{1,2,3,4,5,7}_txt`；原先只有第 6 项「鉴赏」有这件 ⇒ 点菜单**文字**判「空区域」）。上表与 §2.3 的 md5 表、`交付包校验收据.md` 三处同步。

- **屏清单权威**：`layout\screens\_index.json`（`id/file/title_cn/owner/required`），由 `test_screen_index_sync.py` 与 `复刻\screen_index.js` 双向守。
- **叠层与显隐**（全部数据驱动，两端同一谓词）：
  - `vis_flag` + `vis_when`：屏级 flag 决定元素何时可见；**一个元素只允许一对 `vis_flag`**。
  - `flags_default`：进屏时重置该屏 flag；`attach`：附加层（如 `quickbar` 挂在 `dialog` 上、`gal_shell` 挂在四个鉴赏页上）。
  - `reveal`：竖排快捷条的「贴右缘呼出 / 平时收起」（六键：`flag/in_x/out_x/delay_ms/tip_flag/pin_flag`）。
  - `overlay`：右键图标浮层（`sysicons`）只画栈顶并回溯一层。
  - `page_flag`：页码（1 基页号），翻页时写入，互斥的页码文本据此显隐。
- ⚠ **删屏 ≠ 删动作 ≠ 删素材**：`sysmenu` / `sysbar` / `fragment` / `ending` / `chapter` 屏已先后删除，
  但对应**素材一件未删**（共用）、部分**动作保留**（如 `open_sysmenu`＝展开竖排快捷条）。

### 3.3 机制索引（每条都有「引擎落点 / HTML 落点」两侧实现）

| 机制 | 引擎（`krkr\game\`） | HTML（`复刻\replica.js`） |
| --- | --- | --- |
| 屏级 flag 与可见性派生 | `ui_screens.tjs`：`uiScreenFlagSet/Get`、`uiScreenFlagsInitFor/EnsureFor`、`uiScreenElementVisible` | `setFlag/getFlag/initFlagsFor/elementVisible/applyFlagVisibility` |
| `attach` 附加层（绘制/命中/flags 三路并层） | `uiScreenAttachId`、`uiScreenDrawAttach`、`uiScreenAttachClick` | `mergeAttachFlags` |
| `reveal` 竖条呼出（滞回 + pin） | `uiScreenRevealScreen` | `expandQuickbar` / `toggleQuickPin` |
| `state_group` 组绑定换态 | `ui_widget.tjs` + `hoverGroup/pressGroup`、`uiScreenStateGroupOf` | 组绑定段 |
| 列表逐项三态（回落 `pressed>hover>normal>asset`） | `uiWidgetListItemState`、`uiWidgetItemFrameAsset` | `buildList` |
| 逐项按钮/文本/差分「绘制与命中共用同一几何」 | `uiWidgetItemButtonProblems/At`、`uiWidgetItemVariants/…Problems` | `buildList` + `itemBtnReject` / `variantReject` |
| `slider` + 设置仓 | `uiWidgetDrawSlider`、`ui_settings.tjs` | `buildSlider` |
| `page_flag` 页码 | `uiScreenPageFlagOf` | `pageFlagOf` |
| `dynamic` 动态层（未填充画占位底色、不跳过） | `ui_widget.tjs` dynamic 分支、`uiWidgetDrawPlaceholder` | 占位 + `ellipsizeTo` |
| 文字八向描边（**纯渲染，不参与布局**） | `ui_theme.tjs`：`UIThemeOutlineDirs`、`uiThemeDrawOutline` | `textOutlineShadow` |
| 折行/禁则/省略（**引擎算法唯一**） | `uiThemeWrap` / `uiThemeEllipsize` / `uiThemeLayoutText` | 同判据 |
| 连线与 `current` 环 | `ui_flow_links.tjs`、`ui_flow_layer.tjs`（走 `layerExDraw`） | canvas 自绘 |

### 3.4 动作表三类（`layout\_schema.md` §六 为权威）

- **A 类：两端已实现** —— 菜单与导航（`game_start/game_continue/open_*/close/quit_game/hide_window`）、存读档（`do_save/do_load`）、
  选择支与推进（`select_choice/advance_dialog/open_choices/next_choice/prev_choice`）、配置（`config_tab_*/config_char_*/config_set_*/config_reset`）、
  鉴赏（`gallery_tab_1..4` / `gallery_page_prev|next` / `gallery_prev|next:<行>`）、快捷条（`quick_pin/skip_on/auto_on/replay_voice/open_sysicons/do_quicksave/do_quickload`）、
  流程图（`flow_enter` / `flow_layer` / `flow_replay_toggle` / **`flow_intro_open`／`flow_intro_close`**〔`ISSUE-20260930-02` 新增，两端已实现**纯旗标翻转**〕）。
  ⇒ **计数以 `UI组\交付包校验收据.md` 为准**（本纲不写死件数）。
- **B 类：仅派发或占位** —— `backlog_jump:<行>`、`backlog_replay:<行>`（本作**无音频代码**，重播/跳转的实生效留编程组）。
- **C 类：两端均无分支、留编程组** —— **逐条列在 §4.2**（计数以 `UI组\交付包校验收据.md` 为准）。
- **未实现动作的回落**（编程组的接线落点）：引擎 `ui_screens.tjs` 的 `uiActionDispatch` 末尾返回
  `%[handled:false, effect:"", msg:"未实现的动作："+act]`；HTML `replica.js` 的 dispatch `default:` 分支弹提示。**两者都不抛异常**。
- 反例登记：`open_fragment` / `fragment_enter` 为**保留的死分支**（屏已删）；`open_chapter` / `chapter_enter` 已随 M43 移除。

### 3.5 改数据后的最小重跑清单（★最常用）

改**屏数据 / palette**：
```bash
export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
cd "…\UI组"
python 工具/gen_layout.py          # 重出三处产物
python 工具/verify_ui.py           # 引用/尺寸/三处一致/硬编码/PNG/预算/opacity
python 工具/test_gen_sync.py       # 屏 JSON ↔ 生成器 同步
```
增删**素材**：再跑 `python 工具/emit_asset_index.py`（并重跑上面的 `verify_ui`）。
改**流程图**：用 `工具/gen_flow_layout.py`（禁手工摆放），随后 `python "_工作\ISSUE-20260928-02_第2步\复现脚本\run_all.py"`。
改**本总纲的数字**：`python 工具/test_delivery_index_sync.py`（不一致会指到具体哪一项）。
改**任何被「交付包校验收据」覆盖的文件**（**屏数据 `layout\screens\*.json`**／**素材 `krkr\assets\ui\**`（按族计数与字节）／`layout\_schema.md`／`_root.json`／`palette.json`／`screens\_index.json`／`复刻\replica.js`／16 个 `krkr\game\*.tjs`／`工具\gen_layout.py`／`gen_flow_layout.py`／`verify_ui.py`）：**重跑无参 `python 工具/emit_delivery_manifest.py` 生成收据**，再 `python 工具/emit_delivery_manifest.py --check`。★ 该收据里记的是**整文件 md5**（改一个字就会差）；`--check` 已接进 `run_all.py` 的末步 ⇒ 忘了重生成，套件会红。

### 3.6 验收命令全清单

**① 一键套件（最省事；**步数以 `run_all.py` 启动行自报为准，本文不写死该数**）**
```bash
python "_工作\ISSUE-20260928-02_第2步\复现脚本\run_all.py"     # 末步会把盘上 32_flowchart.json 还原成交付样例
```
覆盖：三档生成 → `gen_layout` 三产物 → 7 道闸门 → 自证（m02/m03/标题不变量/模式入口几何/旧寻址退场/入口热区）×含**变异自证** → 变体闸门 → 交付样例还原与闸门复跑 → 基线总账 `m01`/`m06` → screen2/ref150/全量几何/最终还原。

**② 单件闸门**
- `工具\verify_ui.py`（退出码 0/1/2）：`[1]` 引用完整性｜`[2]` 尺寸一致性（无 `nine` 则须等于 PNG 实尺寸；有 `nine` 则须 ≥ 九宫格和）｜`[3]` 三处数据一致（json/tjs/js）｜`[4]` 硬编码坐标扫描｜`[5]` PNG 合法性｜`[6]` **体积预算 ≤96 MB**｜`[7]` opacity ∈ 0–255。
- `工具\test_*.py` **10 支**（见 §2.6）——各自防一类静默分叉，**多数带 `--selfcheck` 变异自证**。
- `工具\gen_flow_layout.py --selfcheck-mode-entries / --selfcheck-title-break / --title-check-report / --frag-report`。

**③ 实机巡演（引擎侧，最接近真实）**
```bash
cd krkr && cmd //c "run_autotour.bat"
```
- **判定线**：`缺件 0` / `EXCEPTION 0` / 转场失败 0 / **七组判词全 PASS**：`★FLOWLAYER★` / `★REPLAYTOGGLE★` / `★MODESTATE★` / `★INTROOPEN★` / `★INTROCLOSE★` / `★WRAPELLIP★` / **`★TRANSOSC★`**（★ D-02 新增：转场结束后**可见层必须是 `stageLayer`** —— 引擎 `ttExchange` 会互换两层，不结算则画面恒停旧屏；**判据能失败**，见 §4.4）。★ **负向对照的口径不是「六组各一条」**：**五组**带 `-REJECT★` 负向对照（`★REPLAYTOGGLE★` 另含 **3 条**负向步；`★INTROOPEN★`／`★INTROCLOSE★`／`★WRAPELLIP★`／`★MODESTATE★` 各若干）；**`★FLOWLAYER★` 的负向路径是 `★FLOWLAYER-SKIP★`**（语义＝「本屏无该层元素 ⇒ 跳过」，**不是注入式对照**）⇒ **不得**按「六组各一条 REJECT」判。
- 产物：`…\临时\<worktree>\临时\ui_run\runtime\savedata\`，其中 `krkr.console.log` 是 **UTF-16LE**，`shot_NN_<屏id>.png` 是**引擎自己导出的截图**（看实机画面用它们，别用抓屏）。
- ⚠ 日志里的 `★M06ITEMBTN-REJECT★` 是**故意注入的负向对照**，不是缺陷。

**④ HTML 双套自检**
```bash
python "_工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_run_html_selftests.py"   # 套 A 期望 SELFTEST ALL PASS；套 B 期望 RESULT=OK
```

---

## 四、交付边界与缺口

### 4.1 谁负责什么

| 事项 | 归属 |
| --- | --- |
| 界面「长什么样、怎么算出来」：屏数据、贴图、机制与动作接线点、1:1 复刻与编辑器 | **UI 组（本组）** |
| 「数据 + 状态」：剧情驱动、画面/音频播放、存档读写、切集筛选、KAG/字体/视频三项引擎缺口 | **编程组** |
| 剧情文本、素材来源与统一、美术统一集 | 资源组 |

### 4.2 未接线清单（C 类动作 + 动态层，都是编程组的活）

| # | 项 | 现状 |
| --- | --- | --- |
| 1 | `flow_mode_main` / `flow_mode_frag`（流程图两枚模式入口「本篇集合」/「番外故事」） | **命中即派发已就绪**；**哪些节点算哪个集**＝行为留编程组；数据侧本轮无字段（要加就加字段并回填 `_schema.md` §六） |
| 2 | `confirm_yes` / `confirm_no`（确认框） | 两端均无分支 |
| 3 | `bgm_mode_none\|one\|all\|rnd` / `bgm_prev` / `bgm_playpause` / `bgm_stop` / `bgm_next`（BGM 鉴赏） | 拟用名，两端均无分支（本作无音频代码） |
| 4 | `replay_play:<行>`（情景回想第 2 页） | 派发即止 |
| 5 | `dynamic` **四类动态层契约**中，**已挂载 2 类**：`story_background`（`dlg.content`）／`flow_scene_frames`（`fc.play_view`）—— **均未填充、现画占位底色**；另 2 类 `story_chara`／`slot_thumb` | **尚无数据落点**（`story_chara` 候选＝`dlg.face`、`slot_thumb` 候选＝两屏 `sv.thumb1..12`，**现均为 `kind:"image"` 静态件**；接入时按 `layout\_schema.md` §四 `dynamic` 契约改） |
| 6 | `flow_replay_toggle` 的**画面播放**本身 | flag 翻转与两键互斥已实现，播放留编程组 |
| 7 | **数据里已写了名字、两端都没有分支的占位动作**（reviewer 独立 grep 复核）：`slot_1`…`slot_12`（存/读档屏槽位，共 24 处）、`page_1`…`page_10`（同两屏页码，共 20 处）、`bgm_play:%row%`（BGM 鉴赏逐曲播放，1 处） | 合计 **45 处**，均落「未实现的动作」回落；编程组接线时请把命名一并对齐回 `layout\_schema.md` §六 |
| 8 | **番外独立层纵滚置真**（★ 本批硬接口） | 溢出视口底（元素盒下沿 `y+h` > **1017**）的行的**三件**（`image`/`_tx`/`_hit`）现一律 `visible_default:false`（＝**数据完整、默认不画**）；**纵滚到位时须用现成的 `ctx.forceShow[el.id]` 抬起**（**不是**改静态字段，也不需要给引擎加新接口）。行 `y = 286 + row*192`、视口带 `y ∈ [190,1017]`、层固定件（`fc.frag<G>_title_bg`/`_title`/`_back*`）**不随滚**；右侧纵滚条的**量程需按当前层内容高度派生**（高亮段恒 y564–616 的现状不算通过）。详见 `UI组交接编程组.md` §9.5 |
| 9 | **真实鼠标事件坐标口径**（★ ~~开口项，从未实测~~ **已闭环 2026-10-01**，见行末） | 现行＝窗口化 `setInnerSize(1280,720)` ＋ `setZoom(2,3)`（`krkr\game\startup.tjs:186-198`）⇒ **客户区尺寸（1280×720）≠ 画布尺寸（1920×1080）**，而 `startup.tjs` 的 `onMouseMove`/`onClick` 与 `ui_screens.tjs` 的 `uiScreenClick`/`uiScreenHoverClear` **直接把引擎传入的 x,y 当画布坐标**。判定法（约 1 分钟）＝窗口化下把鼠标移到任一按钮上看 hover/按下态**是否跟手**；**若不跟手**，上述**四处必须一起**改为按 zoom 换算（不得分叉）。巡演/闸门/HTML 复刻均不受影响。详见 `UI组交接编程组.md` §9.4。★ **已闭环（2026-10-01 · 编程组 `ISSUE-20261001-06`）**：源码取证（`environ/win32/TVPWindow.cpp:89` 的 `TranslateWindowToDrawArea` 只在**全屏**时减 letterbox 偏移）＋探针实测**换算系数 `kx=ky=1.5`**（＝画布 1920 / 客户区 1280）⇒ 窗口化下引擎事件坐标 ↔ 画布坐标的换算**成立**，四处**无需改动**；标题屏点不动的真实原因是**文字区热区缺失**（见 §4.4 D-01），与本条无关 |

### 4.3 已知缺口与余量

<!-- GATE:budget -->
| 项 | 值 |
| --- | ---: |
| 预算（MB） | 96 |
| 余量（字节） | 59,184 |
<!-- /GATE:budget -->

- **素材预算余量仅 57.8 KiB（59,184 B）** ⇒ **再增素材前必须先决定是否上调预算**（`verify_ui [6]` 按 96 MB 判）。
- **Win7 SP1 未实测**（巡演在 Win10/11 + krkrz 1.4.0.8 上完成；本工程未引入新 API，但**未验证**）。
- **`layerExDraw.dll`：用户已接受（★ 订正 2026-09-30 · `ISSUE-20260930-06`，用户裁定 8）** —— 随包附许可文本 `krkr\plugin\license_layerExDraw.txt`（许可文件已在本目录）；来源＝本机商业 Steam 版标准构建，sha256 `fe776090…`；**「即上游未改版」为推断**，**须写进 `成品说明.md`**。（原「合规签字待办」**已关闭**。）
- **总账只覆盖 1 屏**：基线总账 `m06` 只指 `32_flowchart.json`，其余 16 屏没有「与交付基线逐字段比」的闸门。★ **已登记为「交接后维护批」第 1 项**（`UI组交接编程组.md` §八；**本批未做**）。
- **缺「`screens` 源 ↔ 三产物」闸门**：`verify_ui [3]` 只做三产物互比，数据源改动本身靠 `test_gen_sync`（只见生成器覆盖的屏）。★ **已登记为「交接后维护批」第 2 项**（**本批未做**）。
- **`m34_build_screens.build_flowchart()` 仍持旧字面量**：已登记「实质退休、不得再运行」，**误跑会整体回退流程图屏**。★ **已登记为「交接后维护批」第 3 项**（**本批未做**）。
- 其他登记项（占位标签两端 1px、`fc.zoom_knob` 单态与缺口 G-2、**`config` 屏标签已定稿**〔两页／12 枚举行 ＋ 9 滑条 ＋ 6 静音〕、**番外已由流程图 6 组独立层全量承载**、**流程图交付样例 13 节点**而其**全量 712 节点几何数据**已交 `_工作\ISSUE-20260928-02_第2步\全量布局.json`、**元素化渲染归编程组**）见 `会话交接_20260929-05_模式入口收敛.md` §四 与 `UI组交接编程组.md` §七／§八。

---

### 4.4 ★ D-01 / D-02 修复回执（2026-10-01 · `ISSUE-20261001-11`）

> 上游＝编程组交接 `编程组\会话交接_20261001.md` §十二（移交两件上游缺陷）。**本文只做索引，全文见 `UI组交接编程组.md` §十。**

| # | 缺陷 | 现象 | 正解（本组已落） | 编程组须做 |
| --- | --- | --- | --- | --- |
| **D-01** | `title` 屏 6/7 个菜单项缺**文字区热区** | 点菜单文字判「空区域」，进不去对应界面（用户 2026-10-01 报） | `layout/screens/01_title.json` 补 6 件 `kind:"hit"`（几何＝对应文字图、`action`/`state_group` 同项、**不带 state_assets**、z=95）⇒ 24 件；三产物已重生成 | 删除 `ui_boot.tjs` 的 4 个函数 `uiStoryTitleHitRepair`/`uiStoryTitleHitCheck`/`uiStoryTitleHitCovers`/`uiStoryTitleHitActAt` ＋ `uiStoryWindowInit` 里的 2 行调用 |
| **D-02** | 屏转场被清屏重画 ⇒ **画面恒停旧屏** | 点开始游戏有 BGM、状态全对、零异常，但画面停在标题屏，新屏「闪一瞬就消失」 | **★ 根因与编程组原判不同**：引擎 `universal`/`crossfade` 报 `ttExchange` —— 转场结束时把目标层与 `transsrc` **整体互换**，而旧实现把**旧**画面当 `transsrc`、**新**画面画在目标层 ⇒ 方向反 + 结束后可见的仍是旧画面 + 还在往已变不可见的层上重画。改为**乒乓双缓冲**（新画面画进后层 → 前层保持旧画面 → 转场 旧→新 → 结束后按引擎可观测交换事实互换两个成员引用）| 删除 `ui_boot.tjs` 里的 **`UI_TRANS_ENABLE = false;`** 一行（恢复 420ms 遮罩转场） |

- ★ **2026-10-09 校准：上表「编程组须做」两项均已执行完毕** —— `ISSUE-20261001-13`（`397be72`）拆除 D-01 运行期补丁、恢复 420ms 转场（采纳本组 D-02 真根因）；`ui_diag.tjs` 陈旧注释亦已订正。本回执闭环，无需再办。
- 新增巡演判词 **`★TRANSOSC★`**（共 7 组）：断言「转场结束后可见层＝`stageLayer`」。**自证能失败**：把结算函数改成直接 `return false` ⇒ 实测 `PASS 7 / FAIL 12`（判词如实报「引擎已交换但未结算 ⇒ 画面会恒停旧屏」）。
- 实机巡演（本机 Win10 x64，127 屏）：`★TRANSOSC★` **PASS 127 / FAIL 0**；起转 32 / 交换结算 32 / 超时 0；`EXCEPTION 0`；缺件 0；PNG 导出 127/127。**日志已转存为可追踪证据**：`_工作\ISSUE-20261001-11_证据\`（`判定线汇总.md` ＋ 原始日志 UTF-8 档）。
- **窗口实拍**（computer-use，本机）：巡演中窗口依次显示「读档」→「回想」等不同屏，**画面随巡演推进**（旧版恒停标题屏）。

## 五、本总纲的维护规则

1. **数字不许手编**：§2.1 / §2.2 / §2.3 / §3.2 / §4.3 里的表都被 `<!-- GATE:<name> -->` 包住，
   跑 `python 工具/test_delivery_index_sync.py` 即校验；不一致时它会指名到「哪一项、文档写什么、磁盘是什么」。
   修表就用 `--report` 打印的现成行，别自己数。
2. **改完资源/数据后**：按 §3.5 重跑生成器与闸门，并**重跑本文件的数字闸门**。
3. **内容同步**：本文件只承载「索引 + 全局口径 + 验收 + 缺口」；机制细节改在 `layout\_schema.md`、
   逐功能说明改在 `UI组交接编程组.md`——**改那两处时回看本文件是否还成立**（尤其 §3.4 动作三类的计数与 §4.2 的清单）。
4. **编程组上手清单与校验收据**：**§六「编程组上手清单（按优先级）」**是本文件交给编程组的部分（做什么／落点／怎么验／详见）。
   其中一切**计数**（A/B/C 三类动作、占位动作处数、件数/字节）**不在本文件写死**，一律以 `UI组\交付包校验收据.md` 为权威 ——
   该文件由 `工具\emit_delivery_manifest.py` 生成，其 `--check` 已接进 `run_all.py` 作常驻闸门（改了数据/资源后请一并重跑生成器与 `--check`）。

---

## 六、编程组上手清单（按优先级）

> **本节是编程组的开工入口**：单一待办表，按「**不接就跑不起来 → 接了才完整**」排序。
> 四列固定为 **做什么｜落点（文件 · 动作名 · 字段）｜怎么验｜详见**。
> ★ **计数一律不写死**：A/B/C 三类动作数、占位动作处数等以 **`UI组\交付包校验收据.md`** 为权威
> （该文件由 `工具\emit_delivery_manifest.py` 生成、`--check` 已接进 `run_all.py`）。

| # | 做什么 | 落点（文件 · 动作名 · 字段） | 怎么验 | 详见 |
| ---: | --- | --- | --- | --- |
| 1 | **剧本驱动与剧情播放器**（最优先：没有它游戏不成戏） | `krkr\game\ui_demo_script.tjs` 的台词数组 → 改为按 `..\资源组\剧本\scene_<源>.jsonl` 顺序推进的剧情播放器；**消费顺序**＝定取文源（D14）→ 套修正表（**按 source 门控**）→ 套译名替换 → 组装。⚠ 该文件**含手写追加段（`★ M8 追加段`），重跑生成器会丢** | 巡演 `run_autotour.bat` 日志 `EXCEPTION 0`；剧本行数 ↔ 台词数对账（无漏译）；HTML `复刻\index.html` 深链 | `UI组交接编程组.md` §四 第 1 项、§七 第 8 项；`..\资源组\交接编程组\交接说明.md` §二 |
| 2 | **背景 / 立绘动态层** | **`story_background` 落在 `dlg.content`**（`10_dialog.json`，带非空 `dynamic` 字段的元素之一）；**`story_chara` 现无数据落点** —— 候选元素＝**`dlg.face`**（现为静态件 `asset: face/mis01.png`，`story_chara` 只写在其 `note` 里作接入契约），接入时按 `layout\_schema.md` §四 `dynamic` 契约改（`asset:null` + `dynamic:"story_chara"`）。**框位取根 `content_boxes[源代号]`**（唯一来源 `layout\_root.json`，键 `ot/otr/ota/otp/otv/np`；★ **D-04 2026-10-02 起六源一律全画布 `0,0,1920,1080`**，旧过渡期框值作废——见根 `content_box_rule` 第四条修订注与 `UI组交接编程组.md` §十一）。**不得缩放素材本体** | 切换源代号看框位；巡演导图 `shot_NN_<屏id>.png` 与 HTML 复刻并排比对 | `UI组交接编程组.md` §四 第 2 项 |
| 3 | **存档缩略图** | **两屏各 12 个缩略窗元素，两屏 id 同名 `sv.thumb1..12`**（`23_save.json`／`24_load.json`；★ **不存在 `ld.` 前缀的缩略窗 id** —— 按 `sv.thumb` 检索，别照屏名猜前缀）。现为 `kind:"image"` 静态占位件（`asset: ui/x_ui_psv_slot_thumbwin.png`）；**接入真实缩略图时按 `layout\_schema.md` §四 的 `dynamic` 契约改成 `dynamic:"slot_thumb"`**（元素矩形即落点）。★ 「全文字面命中 24 处/屏、合计 48 处」的口径＝每屏 12 条 `asset` 文件名含 `_slot_thumbwin.png` ＋ 12 条 `note` 含 `slot_thumb`（**不是 24 个动态层**） | 存档 → 回读，缩略图非空且对应槽位；巡演/HTML 复刻 | `UI组交接编程组.md` §四 第 3 项、§七 第 6 项 |
| 4 | **章节简介与标题取数** | 右栏摘要 `fc.p_text_tx`（`sample` 现占位）＋ 浮层 `fc.intro_title_tx`／`fc.intro_text_tx`（全文）。**取数键＝`场景id`**（`..\资源组\剧本\章节简介.tsv`，**只取 `采用=是` 且 `简介cn` 非空**）；填充走 `ctx.textOverride[<元素id>]`（krkr）／`e.sample`（HTML）。**节点↔场景的粒度映射由编程组定** | 浮层开合巡演判词 `★INTROOPEN★`／`★INTROCLOSE★` PASS（flag 翻转两端已实现）；逐条核对简介文本与 `章节简介.tsv` 一致 | `UI组交接编程组.md` §四·补 4（4·补4.1）；`..\资源组\交接编程组\交接说明.md` §五 C15 |
| 5 | **流程图切集筛选** | `flow_mode_main` / `flow_mode_frag`（发出方 `fc.mode_main_hit` / `fc.mode_frag_hit`）。**命中即派发已就绪**；**「哪些节点算哪个集」＝行为留编程组**（数据侧本轮无字段；要加就加字段并回填 `layout\_schema.md` §六） | 巡演 `★MODESTATE★` PASS（三态已实测）；筛选行为由编程组自验（无既有判词） | `UI组交接编程组.md` §四·补 3；`layout\_schema.md` §六 |
| 6 | **画面播放** | `fc.play_view` 的 `dynamic:"flow_scene_frames"`（`flowchart` 屏 368×288 层；源 16:9 须 **`contain` 居中** ⇒ 实占 368×207、上下各留约 40px 边）＋ `flow_replay_toggle` 的**播放本身**（flag 翻转与两键互斥**已实现**；暂停与否用 `uiScreenFlagGet("fc_replay")` 读） | 巡演 `★REPLAYTOGGLE★` PASS（含 `-REJECT★`×3）；帧序列/时序由编程组自验 | `UI组交接编程组.md` §四·补 2（4·补.2／4·补.3） |
| 7 | **番外独立层纵滚**（★ 本批硬接口） | 溢出视口底（元素盒下沿 `y+h` > **1017**）的行三件现为 `visible_default:false`，**纵滚到位时用 `ctx.forceShow[el.id]` 抬起**（**不是**改静态字段，也不需要加新接口）；行 `y = 286 + row*192`、视口带 `y ∈ [190,1017]`、层固定件不随滚；右侧纵滚**量程需按当前层内容高度派生** | 巡演 127 张引擎导出 PNG 在 **`y ≥ 1018` 区域「独立层节点像素 = 0」**（外壳件仍绘制 ⇒ **不能**写成「y>1017 全区域 0 像素」）；`--frag-report` 报「产出 53／未产 0／默认可见 45／纵滚置真 8」 | `UI组交接编程组.md` §9.5；`layout\_schema.md` §四 `fc_layer` 节 |
| 8 | **真实鼠标事件坐标口径核对**（★ 开口项 → ★ **已闭环 2026-10-01**：编程组 `ISSUE-20261001-06` 实测换算成立、四处无需改动——见 §4.2 第 9 行与 `UI组交接编程组.md` §9.4） | 窗口化 `setInnerSize(1280,720)` ＋ `setZoom(2,3)`（`krkr\game\startup.tjs:186-198`）下引擎事件坐标**是否已按 zoom 换算从未实测**；**若不跟手**，`startup.tjs` 的 `onMouseMove`/`onClick` 与 `ui_screens.tjs` 的 `uiScreenClick`/`uiScreenHoverClear` **四处必须一起**改（不得分叉） | **窗口化下把鼠标移到任一按钮上看 hover/按下态是否跟手**（约 1 分钟；标题菜单、流程图两枚模式入口任选）；跟手则本条可关闭、并把「实测跟手」补回注释 | `UI组交接编程组.md` §9.4 |
| 9 | **引擎三项缺口**（总纲 G1/G2/G3） | 音频/视频/字体缺口；含 BGM 鉴赏 **8 枚动作**（`bgm_mode_none／one／all／rnd`、`bgm_prev`、`bgm_playpause`、`bgm_stop`、`bgm_next`，**拟用名**；★ 枚数当前值见校验收据的「动作计数」项）、`replay_play:<行>`、`backlog_jump:<行>`／`backlog_replay:<行>`、`confirm_yes`/`confirm_no`（`21_confirm.json` 两键须有**可区分的返回值**）。音频：OGG 走 `wuvorbis.dll`、Opus 走 `kropus.dll`，**无内建 MP3**；**视频格式未确认** | 逐动作实测生效；巡演/HTML 自检；走带四键与播放模式四键各自可听可见 | `UI组交接编程组.md` §四 第 5–7 项；`..\资源组\交接编程组\交接说明.md` §四（C5） |
| 10 | **占位动作的命名对齐** | 数据里**已写名字、两端都没有分支**的占位动作：`slot_1..12`（存/读档屏槽位，24 处）、`page_1..10`（同两屏页码，20 处）、`bgm_play:%row%`（BGM 鉴赏逐曲播放，1 处）＝ **合计 45 处**（★ 处数当前值见校验收据的「动作计数」项），现均落「未实现的动作」回落；接线时**命名一并对齐回 `layout\_schema.md` §六** | 接线后全库 grep 这三个占位名应为 **0 命中**；`layout\_schema.md` §六 **现无定义行**，接线时补进 | 本文件 §4.2 第 7 行；`layout\_schema.md` §六 |
| 11 | **随包须知**（不发就装不起来） | `krkr\plugin\layerExDraw.dll` **必须随包**且附 `license_layerExDraw.txt`（连线与 `current` 环依赖它，缺失即 try/catch 降级、一条线都不画）；「**即上游未改版**」为**推断**，**须写入 `成品说明.md`**；`krkr\assets\face\`（361 件）**不入库、需再生**（`_工作\M44_头像裁切方案\复现脚本\m44_make_faces.py`）；`复刻\` 的贴图是**相对引用** `../krkr/assets/ui/` ⇒ **不能单独拷走** | 随包清单核对（dll ＋ 许可）；克隆后跑再生脚本；`verify_ui` 七项全绿 | 本文件 §2.2／§2.4／§2.5；`UI组交接编程组.md` §9.3 |

**计数（A/B/C 三类动作、占位动作处数）以 `UI组\交付包校验收据.md` 为权威** —— 该文件由 `工具\emit_delivery_manifest.py` 生成、`--check` 已接进 `run_all.py`；**本纲不写死这些数字**。
