# UI 1:1 HTML 复刻 · 使用说明

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（HTML 复刻使用说明；含历代就地订正） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> 模块：**M3 建立 · M15 扩展**（画布 1920×1080 · 16 屏 · 右键图标浮层） ｜ ★ 屏数为 M15 时点口径；**★ ISSUE-20260928-07（2026-09-28）删 `ending` 后现行 17 屏**，一律以 `layout/screens/_index.json` 为准
> Issue：`ISSUE-20260919-11` ｜ 分支：`issue/ISSUE-20260919-11-greta-ui`
> 用途：**给人类用户复核 UI 组的美术成果**（用户原话：「将你的工作成果 1:1 复刻为 HTML 文件（要求可读/可动/和游戏内游玩的效果一模一样），让人类用户来复核/评价」；
> 本轮追加：「生成一个类似于实机游玩的 html，让我看看新素材的效果」）。

---

## 一、怎么打开

**双击 `index.html` 即可**（`file://` 协议直接可用）。

- **不依赖网络、不依赖 CDN、不使用 `fetch()`/`XMLHttpRequest`**（`file://` 下会被 CORS 拦，故布局数据用 `<script src>` 加载）。
- 贴图用相对路径 `../krkr/assets/ui/*.png` 引用 —— **与 krkr 侧是同一份资产，没有复制第二份**。因此**不要把 `index.html` 单独拷走**，它与 `..\krkr\assets\ui\` 是同一条链。

### 本轮（M15）变化的速览

| 项 | M3 时 | **M15（现在）** |
| --- | --- | --- |
| 设计画布 | 1280×720 | **1920×1080**（总纲 D1 修订注·第三条；页面里不写死，从 `ui_layout.js` 读） |
| 屏数 | 15 | **16**（新增 `sysicons` 右键图标浮层） |
| 画面右键 | 打开「回想」 | **呼出 / 收起 9 图标功能浮层**（与实机一致） |
| 素材 | M1 资产集 | 追加 9 功能图标 / 新对话窗 / 流程图四种方框 / Fragment 整页底图 / 鉴赏整页底图 / 系统屏满幅背景 |

---

## 二、1:1 是怎么保证的（**核心机制**）

三处产物**由同一个生成器从同一份数据产出**，不存在人工对齐：

```
UI组/layout/screens/*.json + layout/palette.json + layout/_root.json
        │  工具/gen_layout.py
        ├─→ layout/ui_layout.json      人读 + 机器读
        ├─→ krkr/game/ui_layout.tjs    krkr 侧（TJS2 Dictionary 字面量）
        └─→ 复刻/ui_layout.js          HTML 侧（window.UI_LAYOUT）
```

- krkr 侧 `ui_widget.tjs` 与 HTML 侧 `replica.js` **都只从各自那份数据读坐标/尺寸/字号/颜色**，两侧代码里**都没有硬编码坐标**（由 `工具/verify_ui.py` 的检查 [4] 扫描，当前可疑清单为空；本页 HTML 侧同样零硬编码坐标，连画布尺寸都从 `UI_LAYOUT.canvas` 读）。
- `verify_ui.py` 的检查 [3] 还会**逐键比对** `.json` / `.tjs` / `.js` 三份数据（★ 2026-10-09 校准：现行实测 **28143 键 × 3 份全等** —— `verify_ui [3]`；原「7324 键」为早期读数），任何一侧被改动都会被查出。
- **M15 逐屏像素对照**：krkr 实机巡演导出 23 张 1920×1080 截图（`_工作/M15_证据/krkr/`），与本页无头截图**逐屏并排比对 + 差异度量**，结果见 `_工作/M15_证据/compare_sheet.png` 与 `compare_metrics.txt`。16 屏平均绝对差（MAD，0–255）**0.30 … 10.65**，其中 `loading` 0.30、`confirm` 1.18、`sysicons` 2.43、`dialog` 3.29、`gallery` 3.29 —— 差异集中在文字栅格化与「演示内容不同」，几何完全一致（下文 §五 逐条列出）。

---

## 三、支持的操作

### 顶栏
| 控件 | 作用 |
| --- | --- |
| **1:1 原始尺寸 / 适应窗口** | 缩放切换（`transform: scale`，**不改内部坐标系**） |
| **content_box 演示源** | 切换 `ot / otr / ota / otp / otv / np`，对话框的 `story_background` 层按所选源的框位摆放（★ **D-04 2026-10-02 起六源一律全画布 `0,0,1920,1080`**，旧「4:3/otv 居中留黑边」口径已作废——见根 `content_box_rule` 第四条修订注） |
| **返回上一屏** | 界面栈回退（浮层打开时 = 收起浮层） |
| **重播对话演示** | 重置打字机与台词进度 |
| **隐藏面板** | 隐藏顶栏与页脚，只留 1920×1080 画布（**便于与 krkr 截图逐像素对照**） |
| **界面**（第二行 **16** 个按钮） | 直接跳到任一界面 |

### 键盘 / 鼠标
| 操作 | 效果 |
| --- | --- |
| 点击画面 / `空格` / `Enter` | 推进台词（打字机逐字显示） |
| 按住 `Ctrl` | 快进 |
| `A` | 自动播放 |
| `H` | 隐藏 / 恢复对话窗 |
| `Esc` | **返回上一层／退出（与 krkr 一致）**：浮层打开 → 先收起浮层；否则还能返回上一层 → 返回上一层；已无上一层（栈底）→ 复刻端退到标题屏并给一行提示（真机是 `quit_game`，见 §五.20）。**不再触发 `open_sysmenu`** |
| `Backspace` | 返回上一屏（浮层打开时 = 收起浮层） |
| **画面右键** | **呼出 9 图标功能浮层**；浮层内**再按右键**或**左键点空白处**收起 |
| **鼠标移到画布右端**（M3 新增） | **展开右端竖排快捷条**；指针离开有效区后经 `reveal.delay_ms` 自动收起。★ **M37 起这是唯一的鼠标呼出入口**（收起态整列不绘制、无可点热区） |
| **点竖条把手**（M3 新增） | ~~展开竖条~~ ★ **M37 已作废**：整条把手 `quick.hit_toggle` 随「整条带」退场（收起态不再有任何可点热区）；`open_sysmenu` 动作**保留**为编程入口（深链等），不挂 Esc |
| **悬停某个圆形 icon**（M37 新增） | 该 icon 换 `_on` 材质（组绑定：指针落在 75×73 热区内的**任何位置**都点亮 56×56 的徽章），并在其**左侧**浮出中文名称药丸 + 白字；移出即复位（`state_assets{normal,hover}` + `state_group` + `qbar_tip`） |
| **点竖条第 1 项「锁定」**（M3 新增） | **钉住**（固定展开、不再自动收起）；再点一次解除 |

### 右键图标浮层（`sysicons`，本轮新增）

- **入口**：仅在**对话框屏**上按右键呼出（与实机 `krkr/game/startup.tjs` 的 `toggleSysIcons()` 逐条一致：浮层已开→收起；当前屏非 `dialog`→不支持并给出提示）。
- **9 个图标（3×3，标签是图上烘焙的英文）**：`Q.SAVE 快速存档` / `Q.LOAD 快速读档` / `SKIP 快进` / `PREV 返回上一选项` / `SAVE 存档` / `LOAD 读档` / `CONFIG 设置` / `CLOSE 隐藏对话框` / `REPEAT 重复语音`。
- **收起**：点图标 → 先收起浮层再执行该图标的动作；点空白处或再按右键 → 收起。
- **下层画面**：浮层会**先把对话框画出来再叠上去**，屏内的全屏压暗遮罩压的是游戏画面（不是空画面 → 纯黑）。这是 `overlay` 屏的契约，见 §四.2。

### 深链（给复核与自动截图用）
`index.html?screen=<屏id>` 或 `index.html#<屏id>` 可直接打开指定界面。
屏 id 见 `layout/screens/_index.json`：
`title / dialog / sysicons / confirm / loading / save / load / config / backlog / gallery / music / flowchart`（★ M45：`sysmenu` 已从本列表移除；★ **ISSUE-20260928-06**：`fragment` 亦随该屏整体删除而移除；★ **ISSUE-20260928-07**（2026-09-28，用户裁定）：`ending` 亦随该屏整体删除而移除）。
★ **M43（2026-09-23，用户裁定）**：`chapter`（主线·章节选择）屏**已删除** ⇒ 深链不再有该屏；
剧情入口改由 `flowchart` 屏的既有按钮 `fc.jump_hit`（动作 **`flow_enter`**，文案「进入本章」）承担。
本页因此新增加载 `flow_data.js`（流程图节点数据），顶栏「界面（N 屏）」的 N 改为按目录实测（不再硬编码）。
★ **M45（2026-09-23，用户裁定）**：`sysmenu`（系统菜单）屏**已整体废除**（「已有药丸按钮系统」）⇒
深链不再有该屏，本页复核工具条的 `SCREEN_CATALOG` 条目与导航按钮亦已移除；
`open_sysmenu` **动作保留**（语义＝「展开竖排快捷条（不钉住）」，不是换屏动作）。
快照归档 `_工作\M45_旧素材归档\`。

### 两个诊断模式（M15 新增，供复核与自证）

| 参数 | 作用 |
| --- | --- |
| `index.html?selftest=1` | **DOM 级自检**：**36 条**断言（画布 1920、浮层开合、下层 DOM 保留、全零 nine 走 `<img>`、dynamic 占位、切屏不泄漏 DOM 节点、**M3 的附加层/屏级 flag/动态动作** …），结果写成纯文本页。当前 **35 PASS + 1 SKIP + 0 FAIL（fail=0，RESULT=OK）**（**M8 实测重算，2026-09-22**；本条原写「32 条 / 32-32 PASS」已过期；SKIP 的那条主语 `save.slot1_thumb` 已被 M34 重建移除） |
| `index.html?bench=5` | **渲染性能基准**：16 屏逐屏计时 + 渲染后 DOM 节点数。当前最重的 `fragment`（83 元素）**0.8 ms / 169 节点**、`flowchart`（92 元素）**0.8 ms / 143 节点**（`_工作/M15_证据/bench.txt`；★ **ISSUE-20260928-06**：`fragment` 屏已删除 ⇒ 该读数与「16 屏」均为 M15 时点口径，现行屏数以 `layout/screens/_index.json` 为准） |
| `index.html?screen=<屏>&flags=<名>:<值>[,<名>:<值>…]` | **M3 新增**：渲染完指定屏后**覆盖屏级 flag** 并同步显隐，供无头单帧截图验收收起/展开/钉住/气泡等状态。例：`?screen=dialog&flags=quickbar:expanded,qbar_tip:lock,qbar_pin:1`（值里的 `:` 与 `,` 为分隔符；裸 `名` 等价于置空串）。覆盖只作用于本次渲染，换屏后仍按新屏 `flags_default` 重置 |
| `index.html?…&chrome=0` | **M3 新增（C2）**：**纯净截图开关**。关掉画布内 **HTML 侧独有**的 chrome —— 纯热区（无态图/无组，全库 300 件）的 hover / active / 点击瞬闪叠色，以及画布内的动作反馈 toast（krkr 侧都没有这些东西；默认它们会进 1:1 截图，与本页「不参与游戏画面 1:1 渲染」的自述矛盾）。规则见 `replica.css` 的 `#canvas.chrome-off`。**默认（不传）= 现状**；**静态画面上该开关逐像素无影响**（实测 title/save/dialog 各 0/2 800 000 差异），只对悬停/按下/toast 生效。`index.html?selftest=1` 的 `chrome.*`、`_selftest_states.html` 的 ⑰ 有对应断言 |

---

## 四、本轮新素材与它们各自的界面

| 素材 | 用在哪一屏 | 说明 |
| --- | --- | --- |
| `x_gen_icon_01_qsave … 09_repeat`（9 件） | **`sysicons`** 右键图标浮层 | 3×3 网格、**原生 1:1 摆放**（M17 已把派生图标宽由 384 收到 192，不再需要缩放）；标签是图上烘焙的英文，故本屏不叠引擎文字 |
| `x_gen_dialog.png`（1680×946）/ `x_gen_dialog2.png`（1628×319） | **零屏引用**（★ M38 起） | 对话窗底图（含名字框）。★ **M38 用户裁决「完全无框」**：`dialog` 屏不再有窗口底图，`x_gen_dialog2.png` 已移入 `_工作\M38_旧素材归档\`（`x_gen_dialog.png` 更早即零引用）。文字改由**两端绘制的 8 向描边**承担可读性（见 §十）。同批退役的还有右下 9 功能图标九宫格（9 `dlg.icon_0*` image + 9 `dlg.icon_hit_0*` hit，素材同样入档） |
| `x_gen_flownode_1_normal / 2_badend / 3_important / 4_goodend`（4 件） | **`flowchart`** 13 个节点 | 四种方框图，**`nine:{l:0,t:0,r:0,b:0}` 全零九宫格 = 整图等比 0.4785× 缩放**（见 §四.3） |
| `x_gen_fragpage.png`（1920×1080） | **~~`fragment`~~ 番外选择（★ ISSUE-20260928-06 该屏已整体删除）** | 满幅底图（自带标题与面板边框），其上摆 **40 个格子**（每格一热区 + 一标题文本）。★ 屏删后本件**零屏引用**，但**素材保留原位不删**（用户「只删屏、保留动作/素材」） |
| `x_gen_gallerypage.png`（1920×1080） | **`gallery`** CG 画廊 | 满幅底图；左侧 4 个选择框、右侧预览大框（`dynamic:gallery_preview`）、章节名条、4 条简介、页码、返回 |
| `x_bg_system.png`（1920×1080，来自 `bg63.png`） | **`title`** 标题画面 | 系统屏满幅背景（取代 M9 的「中央 1:1 + 四周延展」构造） |

### 4.1 `overlay` 屏：浮层必须先把下层屏画出来

`layout/_schema.md` §四 的屏级字段 `overlay: true` 表示该屏是**叠在上一屏之上的浮层**。

本页的 `replica.js` 有**两个同尺寸容器**：

```
#canvas
 ├─ .ui-layer-base     （z-index 0）  ← 下层屏
 └─ .ui-layer-overlay  （z-index 1）  ← 浮层屏（overlay:true）
```

渲染 `overlay` 屏时**先把下层屏画进 base 容器**，再把浮层画进 overlay 容器。若不做这一步，屏内那条全屏压暗 `rect`（`sysicons.veil`，色 `@palette.backdrop`、不透明度 `@palette.backdrop_opa`）压的是一张被清空的透明画面 → **实机表现为纯黑**。krkr 侧 `ui_screens.tjs:175-216` 有同一分支，HTML 侧照此对齐。

> 两个容器的 `z-index` 必须**显式**给：否则两容器的子元素 z-index 会在同一层叠上下文里互相穿插，浮层的 `veil`（z=0）会被下层屏的高 z 元素（`dialog` 最高 z = 30，`dlg.choices`；★ M38 前是 `dlg.window` z=20）盖住，压暗遮罩失效。

**下层 DOM 原地保留**：呼出浮层时下层屏不重建（等同 krkr 的 `uiScreenPush`），对话框的打字机进度、已弹出的选择肢都不会丢。收起浮层时下层 DOM 也原地保留（等同 `uiScreenPop`）。
（M15 自检在这里抓到过一个真缺陷：下层 DOM 原地保留时元素引用仍留在「顶层」表里，浮层打开期间运行期改写会取不到元素 → 打字机静默停更。已修，见 `?selftest=1` 的 `sysicons.base-DOM-preserved`。）

### 4.2 全零 `nine` = 整图缩放，**不能**用 `border-image`

`nine:{l:0,t:0,r:0,b:0}` 在 krkr 侧是合法的「允许整图等比缩放」（`uiWidgetNine` 在四边为 0 时只画中格 = 整图 `operateStretch` 到目标矩形）。

**HTML 侧的 `border-image` 表达不了它**：`border-width` 全为 0 时 `border-image` **不绘制任何像素**，图会整块消失。
（M18 已在 `复刻/flow.html` 实测踩到并修好，见 `_工作/M18_报告.md` §5.2；本轮 `replica.js` 用同一个判断 `isZeroNine()` 一并处理 `image` 与 `list.item_frame`。）

⇒ **全零 `nine` 走普通 `<img>`**（`.ui-image-img{width:100%;height:100%}` 正是整图拉伸）；非全零 `nine` 仍走 `border-image`（与 M3/M14 口径一致）。
并且：该写法下 **`w/h` 与 PNG 实尺寸本就不同**（flowchart 方框：PNG 实宽 1152、元素宽 552，0.4785×），故**不做尺寸校验、不画占位**。`?selftest=1` 的 `zeronine.stretched-to-element-box` / `zeronine.size-differs-from-png-still-rendered` 两条断言专门守这个不变量。

### 4.3 `dynamic` 层（运行期填充）的占位

`layout/_schema.md` §四 规定：`asset:null` + `dynamic:<名>` 的层**必须保留并在未填充时画占位底色**，不得跳过。本页处理三个名字：

| dynamic | 出现在 | 本页行为 |
| --- | --- | --- |
| `story_background` | `dialog` 的 `dlg.content` | 用**真实素材**占位演示：`ui/tl2_bg1.png`（实测 1200×900；★ D-04 后元素＝全画布 1920×1080，素材**拉伸进元素矩形**，旧「与 content_boxes.ot 同尺寸 ⇒ 1:1」口径已作废）。**与 krkr 侧演示脚本用的是同一张**（`krkr/game/ui_demo_script.tjs` 的 `UIDemoBgAsset`） |
| `slot_thumb` | `save` / `load` 各 12 处（★ 2026-10-09 校准：旧记「各 8 处」作废 —— 现行为 `sv.thumb1..12`、合计 24 件静态占位件） | 画占位底色 + 标注（本页无真实存档截图可填） |
| `gallery_preview` | `gallery` 的预览大框 | 同上（**M14 新增层，本轮补上**） |

**占位画法与 krkr 逐条对齐**（`ui_widget.tjs:454` `uiWidgetDrawPlaceholder`）：底色 `@palette.node_locked`、不透明度 `@palette.panel_fill_opa`（只作用于底色层）、文字色 `@palette.text_small`、**左上对齐**、两行「`[占位] 动态层`」+「`dynamic:<名>`」（框高不足两行时只画第一行）。
**关键**：占位色块是**半透明**的，必须叠在**它下面真正的画面**上（画廊底图 / 面板填充…），故本页**不给该层铺任何不透明底色** —— 否则混合结果会明显偏暗（M15 实测预览区采样 `(62,63,74)` vs krkr `(108,110,122)`，已修）。

### 4.4 大屏渲染性能与 DOM 清理

~~`fragment`（83 元素）~~ / `flowchart`（92 元素）/ `sysicons`（20 元素，浮层）这些屏（★ ISSUE-20260928-06：`fragment` 屏已删除）：

- **切屏时整容器清空重建**（`layerEl.innerHTML=''` / `overlayEl.innerHTML=''`），不做增量 diff、不逐帧重建；
- 实测单屏渲染耗时 **0.1 – 2.1 ms**、渲染后 DOM 节点数 **10 – 182**（`?bench=5`，`_工作/M15_证据/bench.txt`）；
- `?selftest=1` 的 `dom.no-leak` 断言：**★ ISSUE-20260928-06 起主语由 `fragment` 换成 `flowchart`**（前者屏已删除；`flowchart` 元素最多且会建连线 canvas，判别力更强）—— `flowchart` 连切 1 次与再切 3 次后节点数**相同**，证明无残留累积。

---

## 五、已知差异（**如实登记**）

> 表中「MAD」= 与 krkr 实机截图（1920×1080）的平均绝对差（0–255），取自 `_工作/M15_证据/compare_metrics.txt`。

| # | 差异 | 说明 |
| --- | --- | --- |
| 1 | **本页不参与 krkr 运行** | 它是复核件；游戏本体由编程组基于 `krkr/game/*.tjs` 构建 |
| 2 | **AI 新 logo 与菜单按钮不可用，仍用 M9 文字方案** | 用户 AI 生成的 `俺翼logo.png` / `系统屏底图.png` 是 **RGB 无 alpha、棋盘格烘焙进像素**（假透明），原画的半透明白与棋盘白在像素层已混合、信息已丢失，主代理已试 5 种去背算法全部失败（`UI清单.md` §一.2 与 `生图入料/README.md`）。⇒ **标题 logo 沿用 M9 的 `x_title_logo.png`（中文标题重绘 + 羽毛带）**，**标题菜单仍是引擎绘制的英文文字菜单（START/LOAD/…）而非 AI 按钮图**。要换成图片按钮必须**重新导出真 alpha（PNG-32）**的素材 |
| 3 | **演示台词与 krkr 侧不是同一批** | krkr 侧 `ui_demo_script.tjs` 用 28 条**跨场景**台词（`ot_s01_01a … ot_s04_17b`）；本页 `replica.js` 内嵌的 `DEMO_SCRIPT` 是 M3 注入的**单场景** `ot_s01_08c0` 共 121 条（含 3 个选择肢与分支目标）。两侧都是**真实中文台词、非自造**，但**内容不同** —— 这是 `dialog` 屏 MAD 3.29 的主要来源。若要完全一致，需把两侧改为同一次抽取 |
| 4 | **流程图三态色环按静态 layout 渲染** | `32_flowchart.json` 里 13 个色环**都声明为 `@palette.node_locked`（灰）**；krkr 实机会由 `ui_flow.tjs` 按「已读/可前往/当前节点」**运行期改色**（巡演截图中 N01 黄、N02/N03 蓝）。本页无流程状态模型，故 13 环恒为灰。**节点方框、标签、连线、图例、返回键的几何与 krkr 完全一致**（这是 `flowchart` 屏 MAD 7.31 的主要来源）。`复刻/flow.html` 专题页有节点态演示 |
| 5 | ~~**`chapter` 屏的「（已读）」标注**~~ | **★ M43（2026-09-23）：`chapter` 屏已删除，本条作废。**（历史内容：krkr 实机在页码后追加运行期标注「第 1 / 11 幕　（已读）」，本页只画 layout 里的「第 1 / 11 幕」） |
| 6 | **文字纵向落点残留 ≤ 6 px** | 本页已按 krkr 的算法复刻文字纵向定位（见下），但「同一字号的墨迹内边距」TJS 与浏览器不同：实测 size 24 的文本残留 **2 px**、size 45 的标题残留 **6 px**。属字体栅格化差异，已无法在不引入字体度量魔法常数的前提下继续收敛 |
| 7 | **字体依赖系统** | 用 CSS `font-family` 回退链（`Microsoft YaHei / 微软雅黑 / SimHei / 黑体 / SimSun / 宋体 / sans-serif`）；与 krkr 侧同一条回退链，但两侧字体栅格化引擎不同，字形会有细微差别（`title` 屏英文菜单的 `DejaVu Sans Mono` 尤其明显，MAD 5.31） |
| 8 | **无音效** | UI 音效属编程组（`wuvorbis.dll` 提供 OGG）；`REPEAT 重复语音` 等动作在本页只给文字反馈 |
| 9 | **存档缩略图仍是占位** | `dynamic:"slot_thumb"` 无真实存档截图可填（★ 2026-10-09 校准：现行＝两屏各 12 件、合计 **24** 处；旧记「16 处」作废），已按「未填充 → 占位底色 + 标注」处理（与 krkr 同规则；**krkr 在 168×95 的小框里按全局字号画、文字越出框外，本页按框高收敛字号不复制该溢出**） |
| 10 | **进度只存内存** | 本页刷新即重置（krkr 侧有真实持久化，见 `krkr/README_运行方式.md`） |
| 11 | **转场为简化版** | krkr 侧已实测可用 `rule` 灰度遮罩转场（20/20 成功）；本页用 CSS 淡入淡出近似 |
| 12 | **`loading` 屏为全屏遮罩** | 原版 19 张 `dm00..dm11` 提示图**含日文「ロード中…」烘焙**，不可用；故改为全屏遮罩 + 引擎绘字「加载中…」（该屏 MAD 0.30，与 krkr 几乎逐像素一致） |
| 13 | **`save` / `load` 的槽位文字为演示值** | 日期 `2026-09-19 15:27`、摘要「存档摘要（演示）」等取自 layout 的 `sample`，非真实存档 |
| 14 | **未做 OS 级交互实测** | 本模块禁止 GUI 自动化，右键呼出等交互用 **DOM 级合成事件（`el.click()`）** 与直接 API 调用做了 **36 条**断言（`?selftest=1`，**35 PASS + 1 SKIP（失效主语：`save.slot1_thumb` 已被 M34 重建移除）+ 0 FAIL**，`RESULT=OK`；**M8 实测重算，2026-09-22**，本节原写「25 条 / 25-25 PASS」已过期），**但不能替代**真人在浏览器里的点击手感，建议主代理人工点一次确认 |
| 15 | **krkr 演示背景角标未复刻** | krkr 的 `ui_demo_script.tjs` 会在演示背景右上角画一行小字「演示背景」标明这是演示素材；本页未画（该角标是 krkr 侧的演示夹具，不在 layout 数据里） |
| 16 | ~~**系统菜单屏本轮不可达（M3，有意为之）**~~ → **★ M45：该屏已整体废除，不再存在** | 历史口径（M3–M44）：**`open_sysmenu`** ＝「展开右端快捷条」，不再进入 `sysmenu` 屏（`Esc` 见 §五.20，已改为「返回上一层／退出」）。★ **M37 起该动作在数据里无落点**（整条把手退场）⇒ 只剩**深链**这一入口；`20_sysmenu.json` 数据与素材**保留不删**，复核页仍可用第二行「系统菜单」按钮直接查看该屏。<br>★ **M45（2026-09-23，用户裁定：「现在废除『系统菜单 sysmenu』页，因为我们已有药丸按钮系统」）**：该屏**已废除** —— `20_sysmenu.json` 与 `_index.json` 条目已删除、复核页的 `SCREEN_CATALOG` 条目与导航按钮已移除 ⇒ **深链与复核页都不再有该屏**（「数据保留不删」的旧口径作废；快照归档 `_工作\M45_旧素材归档\`）。`open_sysmenu` **动作保留**（语义＝展开竖条，非换屏） |
| 17 | ~~**12 项快捷条动作在当前数据下不可达（数据冲突）**~~ → **已修复（2026-09-22 主代理裁决 A，数据层）** | 整条把手 `quick.hit_toggle`（w78 z96）曾包住 12 项热区（w75 z95）⇒ 点第 N 项派发的是把手动作。现其 `vis_when=collapsed`（**仅收起态存在**）。**两端独立复核**：本页 `_selftest_states.html` ⑭c 展开态 12 项 × 5 点（中心 + 四角内缩 1px）**60/60 全部命中该项自己**、⑭d 收起态同一批点 0/60 命中项。★ **M37 订正 ⑭d 的期望值**：M36 时「0/60 命中项、60/60 命中整条把手」；M37 整条把手退场 ⇒ 现在是「**0/60 命中项、且命中任何快捷条元素的也是 0**（整列完全不绘制）」，断言已按新结构改写（⑭ 另加一条「12 项中心处无任何 `quick.*` 命中」）。动作层见 `index.html?selftest=1` 的 `flags.item-N-click-dispatch-N`（12/12：命中该项且该 action 的可辨副作用出现）。M1 的 1px 全扫描见 `_工作\ISSUE-20260922-28_M1_证据\reach_check_result.txt`；M37 的展开态 1px 分布见 `_工作\ISSUE-20260923-01_G2_证据\M37_展开态点击分布.txt` |
| 18 | **指针移出画布时的收起时机：两端不同（M3 已知差异，裁决 D2）** | HTML 有 `mouseleave`：指针移出画布即视作 `x < out_x`，启动 `delay_ms` 收起计时（`replica.js` 的 `onRevealLeave`）。**krkr 无等价事件**（引擎不派发鼠标离开），故实机下指针移出窗口后**不会**自动启动计时——用户只要再在窗口内移动一次指针即恢复。本页**保留** leave 行为（不删）；此差异不影响画布内容 |
| 19 | **纯热区在 HTML 有蓝色悬停/按下反馈，krkr 无（M3 已知差异，C2）** | 全库 **300 件**纯热区（无 `state_assets` 且无 `state_group`）在 HTML 走 CSS `:hover` / `:active` / 点击瞬闪（`rgba(122,176,232,.18/.34)`），krkr 侧什么都不画；该叠色**在 `#canvas` 内、会进 1:1 截图**。故新增 `?chrome=0` 纯净截图开关（见 §三）；默认保持现状。像素证据：夹具给两件纯热区加点击瞬闪类，默认态与 `?chrome=0` 在热区矩形内差 **12 397 px**（最大灰度差 56），`?chrome=0` 后 computedStyle 由 `rgba(122,176,232,0.34)` 变 `rgba(0,0,0,0)`（`_selftest_states.html` ⑰ 断言） |
| 20 | **栈底按 `Esc`：真机 `quit_game` / 复刻端退到标题屏 + 一行提示（必然差异）** | krkr 侧 `uiScreenKey`（`ui_screens.tjs:1340-1345`）：`UIScrStack.count > 1` → `close`（返回上一层）；否则 → `quit_game`（退出进程）。**复刻端是网页、没有进程可退**，故栈底分支改为「退到标题屏 + 提示『复刻端无进程可退出：已返回标题』」。三层语义（浮层 → 返回上一层 → 栈底）其余部分逐条与 krkr 相同；断言 `esc.closes-overlay` / `esc.back-to-previous-screen` / `esc.bottom-goes-title-with-toast`（`index.html?selftest=1`），截图 `_工作\ISSUE-20260922-28_M3_证据\m3_esc_{before,after,bottom}.png` |

---

## 六、演示台词来源（**非自造**）

对话演示的台词取自工程的结构化剧本 `资源组\剧本\scene_ot.jsonl`（本篇，**独立翻译**来源，符合 D14），逐条带 `speaker`（中文说话人）与 `cn`（中文台词）。**没有一条是自造的**。具体场景 id 与行号见 `krkr/README_运行方式.md` §演示台词来源。
（注意：与 krkr 侧当前用的演示台词集**不是同一批**，见 §五.3。）

---

## 七、复核建议路径

1. 双击 `index.html` → 点「隐藏面板」→ 与 `_工作/M15_证据/krkr/png_m15/*.png` 里的 krkr 截图对照（同尺寸 1920×1080，可直接叠图）。
2. **在对话框画面上按右键**，看 9 图标浮层是否呼出、下层对话框是否被压暗、再按右键或点空白是否收起、点 SAVE 图标是否收起并进入存档屏。
3. 点第二行 16 个界面按钮，确认都能进能出；重点看 `sysicons`（9 图标 3×3）、`dialog`（★ M38 **无框**：角色名 + 正文直接压在游戏画面上、黑描边白字；右下不再有九宫格）、`gallery`（左 4 框 / 预览 / 名条 / 简介条）、`flowchart`（13 节点一屏、四种方框、图例）。
4. 用「content_box 演示源」逐个切换 `ot → otv → np`，确认各源摆放符合现行口径（★ D-04 2026-10-02 起六源**一律全画布**；旧「4:3 居中留边 / PSV 居中 / 涅布满幅」三种摆放的表述已随第四条修订注作废）。
5. 点「重播对话演示」，确认打字机、光标闪烁、选择肢弹出与点选。
6. 打开 `flow.html` 复核流程图专题页（M4 产出）。（★ M43：`chapter.html` 已随该屏删除；★ **ISSUE-20260928-06**：`fragment.html` 已随 `fragment` 屏整体删除）
7. 想快速自证：地址栏加 `?selftest=1`（**36 条**断言：35 PASS + 1 SKIP + 0 FAIL）或 `?bench=5`（渲染耗时）。
8. **M3 快捷条**：在对话框屏把鼠标移到画布右端（x ≥ 1842）看是否展开；移开约 0.4 秒后应自动收起；
   点第 1 项「锁定」应钉住且不再自动收起；悬停各项时左侧应出现该项说明气泡。
   无头复核可用 `?screen=dialog&flags=quickbar:expanded,qbar_tip:lock,qbar_pin:1` 直接出「展开+钉住+气泡」态。

---

## 八、M15 改了什么（文件 → 行为）

| 文件 | 行为变化 |
| --- | --- |
| `复刻/replica.js` | **扩展**（不重写）：① 画布尺寸只从 `UI_LAYOUT.canvas` 读；② 双容器 `overlay` 屏机制（浮层先画下层、下层 DOM 原地保留）；③ 右键改为呼出/收起 `sysicons`，新增 `open_sysicons` 动作与 M13 的 4 个动作（`do_quicksave`/`do_quickload`/`prev_choice`/`replay_voice`）的反馈；④ `isZeroNine()` 全零 nine 走普通 `<img>`（`image` 与 `list.item_frame` 两处）；⑤ `dynamic` 占位按 krkr 的 `uiWidgetDrawPlaceholder` 重写（色板取色、左上对齐、两行、不铺不透明底）；⑥ 文字纵向定位按 krkr 公式复刻 + **显式 `\n` 用 `white-space:pre-line` 保留**（共 17 处文本受影响）；⑦ 屏清单补第 16 屏；⑧ 新增 `?selftest=1` 与 `?bench=<n>` 两个自证模式 |
| `复刻/index.html` | 顶栏「界面」行补第 16 屏与右键提示；页脚更新（1920×1080、右键=功能图标、本轮新素材、dynamic 占位说明）；标题副标改 M15 |
| `复刻/replica.css` | 去掉写死的 1280×720（改由 JS 从数据写入）；新增 `.ui-layer` 与 `.ui-dynamic-label` / `.ui-dynamic-empty` |
| `复刻/README_复刻说明.md` | 本文件 |

**未改动**：`layout/**`、`krkr/**`、`工具/**`、`UI清单.md`、`生图入料/**`、`复刻/{ui_layout.js, flow.html, fragment.html, flow.css, flow_data.js}`。（★ M43：清单里的 `chapter.html` 已删除，故不在本行；★ **ISSUE-20260928-06**：清单里的 `fragment.html` 亦已随该屏删除）

---

## 九、M3（`ISSUE-20260922-28`）· 右端竖排快捷条

> 需求：把系统菜单改成「鼠标贴屏幕右端呼出、平时收起」的竖排快捷条（数据 `layout/screens/35_quickbar.json`）。
> **M1 已落地机制层**（`layout/_schema.md` §四「屏级状态 flag」：`flags_default` / `reveal` / `vis_flag` /
> `vis_when` / `attach` 与 `elementVisible` 判定语义）；**M3 补 HTML 复刻端的运行时行为**；
> krkr 侧同一套行为由 **M2** 实现，**两端必须逐字一致**。
>
> ★★ **M37（2026-09-23，`ISSUE-20260923-01`）形态重构 —— 本节按新结构改写了「形态」相关描述**：
> 用户裁定「整条带太丑」⇒ 由「整条带 + slim 把手」改为**一排独立圆形 icon 徽章**
> （`quick.ic_<key>`，56×56，`state_assets{normal,hover}` + `state_group`；悬停时在图标**左侧**浮出
> **中文名称药丸** `quick.pl_<key>`（九宫格按字数各自定宽）+ 白字 `quick.tx_<key>`（28px））；
> **平时完全隐藏**（收起态整列不绘制、右端无可点热区），鼠标贴到 x ≥ `reveal.in_x` 才整列淡入。
> 退场四件：`quick.btn` / `quick.tgl` / `quick.tips` / `quick.hit_toggle`（7 件素材已归档到
> `_工作\M37_旧素材归档\`）。**机制层未新增任何字段**，故 9.1 的契约①③⑤⑥⑦**原样有效**，
> 只有契约②的描述与契约④的入口变了（见下表括注）。

### 9.1 行为契约（HTML 侧落点）

| # | 契约 | 落点（`复刻/replica.js`） |
| --- | --- | --- |
| 1 | **附加层**：承载屏（`dialog.attach="quickbar"`）画完后再叠画附加屏元素；**不改当前屏语义**；点击/悬停优先级高于承载屏 | `renderAttachLayer()`（叠画 + `state.attachId`）、`mergeAttachFlags()`（node 与承载屏**共用一张 flag 表**）、`zIndex()` 的 `curZBase`（附加层 z-index 整体上移到承载屏最大 z-index 之上，保证「压在上层」成立） |
| 2 | **初始态 `collapsed`**：★ **M37 后「整列不绘制」**（12 icon + 12 药丸 + 12 白字 + 12 项热区全隐藏）；M36 及以前是「只显示把手 `quick.tgl` 与 `quick.hit_toggle`」 | `renderElement()` 走 `elementVisible()`（M1）+ 换屏时 `initFlagsFor()` / `mergeAttachFlags()` |
| 3 | **呼出 / 收起**：x ≥ `in_x` 展开；x < `out_x` 起 `delay_ms` 计时后收起；回到 `≥ out_x` 撤销计时；钉住时不自动收起；离开画布按 `x < out_x` 处理；展开中 `tip_flag` = 指针所在项 key；**不重建 DOM** | `canvasPoint()` + `bindCanvas()` 新增的 **画布级 `mousemove` / `mouseleave`** → `onRevealMove()` / `onRevealLeave()` / `startRevealTimer()` / `cancelRevealTimer()` / `tipKeyAt()`，改完一律 `applyFlagVisibility()` |
| 4 | **动作**：`open_sysmenu` 改为「展开竖条」（撤销计时、不钉住）；新增 `quick_pin`（钉住切换）与 `next_choice`（`prev_choice` 的镜像）；其余 10 项走既有实现 | `doAction()` 的 `switch` 前置三个 case；`NAV` 删除 `open_sysmenu`；`expandQuickbar()` / `toggleQuickPin()`。**`open_sysmenu` 动作本身保留**（★ M37 后数据里**已无元素指向它** —— 整条把手退场 ⇒ 它成为**编程入口**：附加层里 action 留空的 hit 兜底；★ **M45 补注**：它曾指向的 `sysmenu` 屏**已废除** ⇒ 「深链进该屏」这一入口随之消失，动作语义不变），且 **Esc 不挂该动作** —— Esc 改为「返回上一层／退出」（主代理 2026-09-22 裁决 H1，见 `escBack()` 与 §五.20） |
| 5 | **`?flags=` 深链** | `applyFlagParam()`（boot 内、渲染之后调用） |
| 6 | **自检扩写** | `_selftest_states.html` 第 ⑧–⑯ 条；`index.html?selftest=1` 的 `flags.*` 断言 |
| 7 | **编辑器两态预览** | `editor.html` 操作栏「按 flag 预览」+ 每个 flag 的下拉；`editor_core.js` 的 `isVisible()` / `applyFlagsMode()` / `syncFlagVals()` |

### 9.2 两端必须一致的两处「由数据推出」的口径（**重要**）

1. **气泡项 key 的判定**（★ 主代理 2026-09-22 裁决 **D1**，两端以此为准）：
   ① 候选 key 集 = 该屏内 `vis_flag == reveal.tip_flag 且 vis_when != "*"` 的元素取值
      （本数据即 `quick.tx_*` 的 `lock/save/load/qsave/qload/auto/skip/next/prev/log/chart/option` 共 12 个）；
   ② 命中候选 = `kind=hit` 且 **`vis_flag` 非空** 且 id 尾段形如 `hit_<key>`（key 在 ① 内）且当前可见；
   ③ 矩形判定用**半开区间** `[x, x+w)` × `[y, y+h)`；
   ④ 多点命中取 **z 最高**，z 相同时**声明在后者胜**。
   ⇒ **不带 `vis_flag` 的热区天然不产生气泡**（② 要求 `vis_flag` 非空）——M36 之前的整条把手
   `quick.hit_toggle`（key `toggle` 不在 ① 内）即靠这一条排除；★ M37 后该元素已不存在，
   本屏里带 `vis_flag=quickbar` 的 `hit_*` 恰好只有 12 项，本判据仍按同一算法把它们精确筛出。
   本页实现：`replica.js` 的 `tipKeyAt()`；断言：`flags.tip-follows-item` 与
   `flags.tip-halfopen-boundary`（项右/下缘 `w-1`/`h-1` 命中本项、`w`/`h` 落空）。
2. **钉住 flag 名**：**一律读 `reveal.pin_flag`**（`layout/_schema.md` §四 ⑥，修复 C 已入数据
   `"pin_flag":"qbar_pin"`）——本页 `pinFlagOf(reveal)`；`reveal` 缺该键时该屏视为**无钉住功能**
   （`toggleQuickPin()` 给可读反馈并空操作，不写死任何 flag 名）。`flagNamesOf()` 的键集同样含 `reveal.pin_flag`。

### 9.3 原「把手吞点击」阻断项 —— **已修复（数据层）+ 复核结论**

> ★ **M37 状态**：整条把手 `quick.hit_toggle` **已随「整条带」整体退场** ⇒ 本节的阻断项
> **从根上消失**（不存在「谁吞谁」的问题了）。下表数值中**只有 ⑭d 的期望值随 M37 改变**
> （不再是「60/60 命中把手」，而是「0/60 命中任何快捷条元素」——整列不绘制），已在条目里标注。

原问题：`quick.hit_toggle`（`x1842 y7 w78 h898`，`z=96`）**完整包住** 12 项热区（`w75`，`z=95`），
按两端一致的「命中取 z 最高」规则，展开态点任一真实位置派发的都是把手动作 ⇒ 12 项不可达。

**修复**（2026-09-22 主代理裁决 A，★ 数据层，非代码）：把手改为 `vis_flag=quickbar` / `vis_when=collapsed`
（**仅收起态存在**）。**本页独立复核结论（通过）**：

- 展开态：12 项 × 5 点（中心 + 四角内缩 1px）= **60/60 点命中栈顶就是该项自己**（⑭c）；
- 收起态：同一批点 **0/60 命中项**；M36 时为「60/60 命中把手」，★ **M37 后为「命中任何
  `quick.*` 元素 0/60」**（断言已改写，⑭d）；
- 动作层：`flags.item-N-click-dispatch-N` = **12/12**（每项都命中该项且其 action 的可辨副作用出现）；
- 与 M1 的 1px 全扫描（65 700 像素全归 12 项、把手 0 像素）互证，
  证据 `_工作\ISSUE-20260922-28_M1_证据\reach_check_result.txt`。
- 顺带：`quick.hit_save`/`hit_load` 的 action 已由 `do_save`/`do_load` 改为 `open_save`/`open_load`
  （与右键浮层 9 图标同源，避免「无槽位直接存/读」的语义歧义）；C4 断言按数据读 action，不写死该项是什么。

### 9.4 编辑器的「按 flag 预览」

`editor.html` 操作栏：`按 flag 预览：开/关`（**默认关**）+ 该屏 `flags_default` 里每个 flag 的下拉
（取值候选 = 该屏元素里出现过的 `vis_when`，含空串；附加层的 flag 一并列出，因为运行期两屏共用一张 flag 表）。

- **关（默认）**：忽略 flag —— 渲染与编辑口径都只看 `visible_default`，带 `vis_flag` 的元素在 DOM 上
  被强制恢复显示 ⇒ **编辑快捷条时不会因为它默认收起而看不见/选不中元素**（等同既有编辑体验）。
- **开**：按所选取值套用 §四 可见性谓词（`isVisible()`、命中测试、元素树灰显、勾选框一并跟着走）。
- 深链（供无头截图）：`editor.html?screen=quickbar&fp=1&flags=quickbar:expanded,qbar_tip:lock,qbar_pin:1`
  （`fp=1` 开预览；`flags=` 与复刻页同格式）。
- **不写回 layout**：预览态只在编辑器内存里，导出 JSON 不受影响。

### 9.5 主代理追加修复（2026-09-22 二审后）逐条落地

| 项 | 内容 | 落点 / 证据 |
| --- | --- | --- |
| **A** | 复核「把手吞点击」修复（数据层 `hit_toggle.vis_when=collapsed`） | `_selftest_states.html` ⑭c（展开态 60/60 命中该项）/⑭d（收起态 0/60 命中项）；`index.html?selftest=1` 的 `flags.item-N-click-dispatch-N`（12/12）。结论：**通过**（见 §9.3） |
| **B** | `reveal.pin_flag` 已入数据 ⇒ 不得写死 | `replica.js` 的 `pinFlagOf(reveal)` / `isPinned(reveal)`；断言 `flags.pin-toggle` 的 detail 打印实际读到的 flag 名 |
| **D1** | tip 口径以本页为准（非空 `vis_flag` + 半开区间 + 同 z 后者胜） | `replica.js` 的 `tipKeyAt()`；断言 `flags.tip-halfopen-boundary` |
| **D2** | drop 差异：krkr 无 `mouseleave` 等价事件 | 保留本页 leave 行为；登记 §五.18 |
| **C1** | 两处自检缺陷（自指恒真 / 硬编码 13） | `replica.js` 的 ⑤ 与 ⑨ 异步段：主语**由数据推导**（save 屏 `nine` 全零的 image 元素，现 15 件）、计数主语为**推导出的全集**；新增 `zeronine.subject-nonempty`、`zeronine.all-subjects-stretched-to-element-box`。**反向验证**（`_工作\ISSUE-20260922-28_M3_证据\rev.html` + `make_rev_fixture.py`，故意改坏）：渲染器退化时新断言 FAIL（14/15）而**旧写法 `stretched === znImgs.length` 实测 PASS（假通过）**；数据退化时新断言仍 PASS、旧写法硬编码 13 FAIL |
| **C2** | 纯热区蓝叠色会进 1:1 截图 | `?chrome=0`（`replica.css` 的 `#canvas.chrome-off` + `replica.js` boot 加类）；断言 `_selftest_states.html` ⑰（computedStyle：`rgba(122,176,232,0.34)` → `rgba(0,0,0,0)`）；像素证据 `m3_c2_chrome_on.png` vs `m3_c2_chrome_off.png`（热区矩形内差 12 397 px）；登记 §五.19 |
| **C3** | §4.5 正文口径订正 | `replica.js` §4.5 正文改为「共用同一张表、只为未定义键补初值、不重置运行值」（与 `_schema.md` §四、M2 的 `uiScreenFlagsEnsureFor` 一致） |
| **H1** | Esc 两端统一为「返回上一层／退出」 | `replica.js` 新增 `escBack()`（浮层 → 返回上一层 → 栈底退标题+提示）；keydown 的 Esc 分支改调 `escBack()`，**不再调 `doAction('open_sysmenu')`**；`open_sysmenu` 动作保留（把手仍指向它）。README 键位表与 §五.20 同步；断言 `esc.closes-overlay` / `esc.back-to-previous-screen` / `esc.bottom-goes-title-with-toast`（3 条，全部走真实 `keydown` 路径） |
| **H3** | Esc 断言的反向验证 | `make_rev_fixture.py` 追加生成 `replica_rev_esc.js`（把 Esc 映射换回旧行为 `doAction('open_sysmenu')`）+ `rev_esc.html`；跑同一套 `?selftest=1` ⇒ **三条 `esc.*` 全部 FAIL**（实测：`screen=save` 未返回、并弹出"当前屏没有快捷条"提示），证明断言不是恒真 |

---

## 十、M38（`ISSUE-20260923-01`）· 对话框「完全无框」+ 文字「8 向描边」

> 用户裁决（2026-09-23）：对话框改为《月影魅像》式**半透明画布方案**；实测该作对话框**本质是「没有框」**
> （底部亮度是场景自身衰减、无半透明遮罩台阶），故本作取**完全无框**：① 删窗口底图；② 角色名一并去框；
> ③ 删右下 9 功能图标九宫格（功能已由右端竖排快捷条覆盖）。

**数据层（`layout/screens/10_dialog.json`，该屏无生成器，`test_gen_sync.py` 的 NO_GEN 已登记）**
：`dialog` 屏 26 → **7 件**（删 `dlg.window` + 9 `dlg.icon_0*` + 9 `dlg.icon_hit_0*`）；
`dlg.text` / `dlg.name` 加 `outline:true` / `outline_color:"#000000"` / `outline_width:2`，并把 `shadow` 关掉
（理由：单向阴影在亮画面上不构成闭合轮廓，且与描边同开会叠出双重发虚的重影边）；
几何**未动**（正文 `x246 y806 w1224 h201`、名字 `x331 y747 w345 h56`）；
~~`dlg.hint` 文案订正为「右键：功能图标　空格：快进　Esc：返回　右缘：快捷条」（实测 612px ≤ 框宽 630）。~~
> ⚠ **作废（历史留痕，2026-09-29 · `ISSUE-20260929-05`）**：**`dlg.hint` 元素已整体删除**（用户「对话框页：删除 `dlg.hint`（不需要操作提示）」）
> ⇒ 本行所述的文案订正**随元素退场而失效**（对话框屏 10 → **9 件**）。该屏仍由 `10_dialog.json` **手工维护**
> （`test_gen_sync.py` 的 `NO_GEN`／superseded 登记不变）。

**★ 视觉验收第一轮追修（同一轮内，vision 子代理独立验收）**：`dlg.choices`（`list` 选择肢）原先只有单向投影、
**无描边**，第 2 条未高亮项的白字 `@palette.text_menu`（#E8E8F0）压在**白色羽翼**上时「阿斯嘉」三字几乎消失
（实测：该条白字 2px 邻域内有暗像素的比例仅 13.9%）；且第 1 条（highlight 填充 + 暖金 `text_menu_sel`）与
第 2 条（无填充 + 白字）反差过大。**修法**：`dlg.choices.font` 改为与 `dlg.text` / `dlg.name` **完全同参数**
（`outline:true` / `outline_color:"#000000"` / `outline_width:2` + `shadow:false`）。
**高亮项不特殊处理** —— `buildList` 只按 `highlight_font_color` 换 `color`，`text-shadow` 来自同一个 `listFont`
⇒ 高亮金字自动同得描边（`_工作\ISSUE-20260923-01_M38_证据\m38_html_outline_probe.py` 已断言
`dlg.choices` 的 `.ui-list-item-label` 实得 8 条描边阴影，与 krkr 同表同宽）。
量化（同一口径脚本 `m38_choices_contrast.py`，容差 TOL=16 由 vision 的 13.9% 反向标定）：
**标签排版盒** 20.0% → **67.3%**（高于对话正文同级）；整条矩形（含透过半透明面板的背景）13.9% → 25.3%；
反向自证＝只把 `outline` 关掉、其余同修后 ⇒ 标签排版盒掉回 **16.9%**（证明指标随 `outline` 而变）。

**机制层（HTML 侧落点，与 krkr 必须逐项一致）**

| # | 契约 | 落点（`复刻/replica.js`） |
| --- | --- | --- |
| 1 | `font.outline` 为真 ⇒ 用 `outline_color` 在 **8 个方向**各画一次同文本、**最后画正文** | `textOutlineShadow(f)`：8 条 `text-shadow`（方向表与 krkr `UIThemeOutlineDirs` **同序同向**，偏移 = 方向 × `outline_width`）；`textShadowAll(f)` 合成后交给 `buildText` / `buildHit` / `buildList` |
| 2 | **描边只影响渲染，绝不参与布局** | 不进任何度量路径：换行 / 截断仍按 `e.w` / `e.max_lines` 与正文字形算（`-webkit-line-clamp` 那支一字未改）；krkr 侧同理（`uiThemeWrap` / `uiThemeLayoutText` 不看 outline 字段） |
| 3 | `outline:false` 的元素**行为与改动前一模一样** | `textOutlineShadow()` 首行即 `if (!f || !f.outline) return null`；`textShadowAll()` 在两者都关时返回 `null`（不写 `text-shadow`） |

**目标导向证据**（`_工作\ISSUE-20260923-01_M38_证据\`）
：`m38_html_outline_probe.py` 直接从 DOM 读回 `dlg.text` / `dlg.name` 的 `text-shadow`，解析出
`[(2,0),(-2,0),(0,2),(0,-2),(2,2),(-2,2),(2,-2),(-2,-2)]`（= krkr 同表 × `outline_width`=2，全黑），
并断言 ~~`dlg.hint`（`outline:false`）仍是**单条** offset 阴影~~；截图 `M38_HTML复刻_对话框屏_chrome0.png`。
> ⚠ **该断言的「主语」已不存在（2026-09-29 · `ISSUE-20260929-05`）**：`dlg.hint` 元素**已被删除**（见上）
> ⇒ 本句**仅作 M38 轮的历史留痕**，不可再复跑；「`outline:false` 仍是单条阴影」这条结论现可改用
> 对话框屏其余既有 `shadow:true` 文本（现为 **`dlg.mode_tag`** —— 本批删 `dlg.hint` 后，该屏唯一 `shadow:true` 的文本件）复核。
krkr 侧的对照见 `krkr\README_运行方式.md` §九（同数据、只换渲染器代码的逐像素 A/B：`outline:false` 的元素
**0 像素差异**，名字/正文呈环形描边）。
