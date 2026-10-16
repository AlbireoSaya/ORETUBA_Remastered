# UI 布局数据契约（`layout/` · **UI 组内部 + 对编程组的唯一布局数据源**）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：权威（机器可读契约 / 本组唯一布局数据源；本件被 `交付包校验收据.md` §⑥ 整文件 md5 覆盖——改本件须重跑 `工具\emit_delivery_manifest.py`） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> 建立：2026-09-19 ｜ Issue：`ISSUE-20260919-11` ｜ 建立者：UI 组（主代理）
> **本契约是三处产物的共同上游**：① krkr 侧 `krkr/game/ui_layout.tjs`；② HTML 复刻侧 `复刻/ui_layout.js`；③ 人读 `layout/ui_layout.json`。
> 三者**由 `工具/gen_layout.py` 从 `layout/screens/*.json` + `layout/palette.json` 自动生成**，**禁止手改生成物**——改布局只改 `screens/*.json`。

---

## 一、为什么要有这一层

用户要求「HTML 必须**和游戏内游玩的效果一模一样**」。保证 1:1 的唯一可靠办法是**两侧共用同一份布局数据**，而不是人工对齐两套代码。
因此：**任何坐标、尺寸、字号、颜色都不允许硬编码在 `.tjs` 或 `.html` 里**，一律从本数据读取。

---

## 二、文件组织（**按屏分文件，避免并行写冲突**）

```
UI组/layout/
├── _schema.md            ← 本文件
├── palette.json          ← 色板（M1 从原素材吸色实测写入；**唯一色值来源**）
├── screens/
│   ├── _index.json       ← 屏清单（id / 文件 / 中文名 / 归属模块 / 必需元素）
│   ├── 01_title.json     ← 标题画面（主代理样板）
│   ├── 10_dialog.json    ← 对话框 + 名字框 + 系统条 + 选择肢（主代理样板）
│   └── …                 ← 其余屏由各模块按 §五 归属新增
├── ui_layout.json        ← 【生成物】合并结果（人读 + 机器读）
```

**写权限**：每个模块**只写自己名下的 `screens/*.json`**；`_index.json` 由主代理维护（模块需新增屏时向主代理提请求）。
`palette.json` 由 M1 独占。

---

## 三、根对象

```jsonc
{
  "canvas": { "width": 1920, "height": 1080 },   // ← M13 更新：与 layout/_root.json 的 canvas_baseline 一致
  "content_boxes": {          // 各源画面区（★ D-04 2026-10-02：六源一律全画布；4:3 素材由消费方按宽高比 contain）
    "ot":  {"x":0,"y":0,"w":1920,"h":1080},
    "otr": {"x":0,"y":0,"w":1920,"h":1080},
    "ota": {"x":0,"y":0,"w":1920,"h":1080},
    "otp": {"x":0,"y":0,"w":1920,"h":1080},
    "otv": {"x":0,"y":0,"w":1920,"h":1080},
    "np":  {"x":0,"y":0,"w":1920,"h":1080}
  },  // ← 旧过渡期口径（ot/otr/ota/otp=360,90,1200,900、otv=240,132,1440,816）已作废：见根 content_box_rule 第四条修订注（2026-10-02，用户裁定 / 编程组移交单 D-04；素材本体不放大原则不变）
  "fonts": {                  // 字体与字号基线（不依赖特定字体；运行时 Font.getList() 探测回退）
    "fallback_faces": ["微软雅黑","Microsoft YaHei","黑体","SimHei","宋体","SimSun","MS Gothic"],
    "sizes": { "title":69, "subtitle":36, "name":30, "body":36, "menu":33, "small":24, "tag":27 },
    "line_spacing": { "body":1.4, "menu":1.2 }
  },
  "screens": { "<screen_id>": { …见 §四… } }
}
```

> **`fonts.sizes` 是全局基线**；元素可在自己的 `font.size` 覆盖。
> **画布基线（2026-09-20，M12/M13）**：设计画布 **1920×1080**，窗口化按 `setZoom(2,3)` 呈现 1280×720；上表数值与 `layout/_root.json` 一一对应，**以 `_root.json` 为准**（本块曾在 M12 前残留 1280×720 旧值，M13 已同步）。

---

## 四、屏对象

```jsonc
{
  "id": "dialog",
  "title_cn": "对话框",
  "owner": "M2",                       // 归属模块（写权限）
  "overlay": false,                    // 可省。true = 浮层屏（见下）
  "attach": "quickbar",                // 可省。M1：附加层 —— 本屏绘制后再叠画该屏的数据（见下）
  "flags_default": { "quickbar": "collapsed", "qbar_tip": "" },  // 可省。M1：屏级 flag 初值（见下）
  "reveal": { "flag":"quickbar", "in_x":1842, "out_x":1780,     // 可省。M1：竖条屏呼出/收起参数（见下）
              "delay_ms":400, "tip_flag":"qbar_tip" },
  "bg": { "kind":"image", "asset":"ui/…png", "x":0,"y":0,"w":1280,"h":720, "opacity":255 },
  "elements": [ … ]
}
```

**`overlay`（屏级字段，M13 新增）**：`true` 表示该屏是**叠在上一屏之上的浮层**（如 `sysicons` 右键图标浮层）。
本渲染器只画**栈顶屏**（不做整栈合成），故 `uiScreenDraw` 见到 `overlay:true` 时会**先把栈中它下面那一屏画出来**，再叠本屏 —— 这样屏内的「全屏压暗 `rect` 遮罩」压的才是**游戏画面**，而不是一张被清空的透明画面（实机表现为纯黑）。
限制：浮层只回溯**一层**（栈倒数第二屏）；栈底或独占时无下层可画，浮层即叠在空画面上。

### 屏级状态 flag（M1 新增，`ISSUE-20260922-28`）

**用途**：让元素按「当前屏的**运行时** flag 值」显示/隐藏 —— 系统菜单快捷条的收起/展开、按钮说明气泡、钉住指示等。**本层只提供机制**：贴边呼出、延时收起、钉住、动作派发由 M2/M3 实现。

**判定语义（唯一定义，两端必须逐字一致）**

> 元素**可见 / 可点击** ⟺ `el.visible_default !== false`
> 且（`el.vis_flag` **不存在** → 通过；**存在** → 当前 flag 值满足：
> `vis_when === "*"` 时要求**非空字符串**，否则要求**严格相等**）

| 字段 | 层级 | 类型 | 说明 |
| --- | --- | --- | --- |
| `flags_default` | 屏级 | object | flag 名 → **初值（字符串）**。仅「切换屏」时按新栈顶屏的此表重置；运行期改动不落回这里 |
| `reveal` | 屏级 | object | **仅竖条屏需要**（M2/M3 读它，M1 只写数据）。**全部 6 个键**（一个不少；两端一律读数据，**不得写死任何一个**，包括 flag 名）：<br>① `flag` — 整条开关的 flag 名（如 `"quickbar"`）；② `in_x` — 鼠标 x ≥ 此值 → 展开；③ `out_x` — x < 此值 → 起计时收起（**滞回**，避免边界抖动）；④ `delay_ms` — 收起延时（毫秒）；⑤ `tip_flag` — 说明气泡的 flag 名（写「当前悬停项 key」，空串 = 不显示气泡）；⑥ `pin_flag` — **钉住** flag 名（值为 `"1"` 即钉住；钉住时立即展开且不自动收起）。实例：`{ "flag":"quickbar", "in_x":1842, "out_x":1780, "delay_ms":400, "tip_flag":"qbar_tip", "pin_flag":"qbar_pin" }`。**这些数值即画布坐标/毫秒，脚本里一律不得写死**（`verify_ui.py` 检查 [4] 会判失败） |
| `attach` | 屏级 | string | **附加层**：该屏绘制时，其上**再叠画**此 id 的屏数据（如 dialog 屏 `"attach": "quickbar"`）。**附加层不改屏栈语义** —— 不 push/pop、不进历史、不影响 `overlay` 的一层回溯，只是「多画一层」。**flag 表处理（2026-09-22 订正，与两端实现一致）**：附加层**不切换、也不还原** flag 表，而是**并进同一张表**——承载屏入栈时即按**附加层自己的 `flags_default`** 为**承载屏未定义**的键铺初值（承载屏自己的 defaults 优先），此后附加层的运行期值（展开/气泡/钉住）持续被读写。**不重置运行值**：每帧叠画时只做「为尚未存在的键补默认」的幂等兜底，否则展开态会在下一次同步时被清空。两端实现：krkr `uiScreenFlagsEnsureFor()`（`ui_screens.tjs`）／ HTML `mergeAttachFlags()`（`replica.js`）。**原稿「由叠画方负责切换与还原」已作废**（那是切换式实现，与实际相反） |
| `vis_flag` | 元素级 | string | 该元素的开关 flag 名（与 `vis_when` **成对出现**） |
| `vis_when` | 元素级 | string | 需要的取值；**特殊值 `"*"` = 该 flag 非空即显示**。未给 `vis_flag` 时本字段无意义 |

**两端落点（同一语义，改一处必须改另一处）**

| 端 | 文件 | 表 / 接口 |
| --- | --- | --- |
| krkr | `krkr/game/ui_screens.tjs` | `var UIScrFlags` ｜ `uiScreenFlagSet(name,value)`（返回「是否变化」）｜ `uiScreenFlagGet(name)`（未设置返回 `""`）｜ `uiScreenFlagsInitFor(screenId)` ｜ `uiScreenElementVisible(el)` |
| HTML | `复刻/replica.js` | `state.svFlags` ｜ `setFlag/getFlag/initFlagsFor/elementVisible` ｜ **`applyFlagVisibility()`**（经 `window.UI_REPLICA` 导出） |

- **`applyFlagVisibility()` 是机制的两端落点之一**（HTML 侧，2026-09-22 主代理裁决 2 采纳）：flag 变化后它**只同步已渲染 DOM 的显隐，不重建 DOM** —— 保住 hover/press 台账与运行期节点引用（选择肢、打字机都不受惊）。它**只碰带 `vis_flag` 的元素**，绝不越权复位其它元素的 `display`（那些由对话框运行期自己管）。krkr 侧每帧由 ctx 重算，不需要对应物。
- **★ 铁律：`visible_default` 必须为 `true` 的场合** —— 靠 `vis_flag` 控制显隐的元素，`visible_default` **必须写 `true`（或省略）**。因为判定语义里 `visible_default !== false` 是**前置与条件**，写 `false` 的元素**永远不可见**，flag 再怎么也抬不起来（那就成了死件）。「默认不显示」由 `flags_default` 给空串初值表达，不由 `visible_default:false` 表达。实例：`quick.pin_mark`（`visible_default:true` + `vis_flag:qbar_pin` + `flags_default.qbar_pin:""`）。
- **四处可见性消费者统一走该谓词**（原先各自判 `visible_default`）：`ui_widget.tjs` 的 `uiWidgetElementVisible`（保留 `ctx.forceShow`/`ctx.hide` 覆盖后回落）、`ui_screens.tjs` 的 `uiScreenHoverAt` / `uiScreenClick` / `uiScreenKey`。
- **换屏即重置**：krkr 的 `uiScreenReset`/`uiScreenPush`/`uiScreenPop` 与 HTML 的 `renderScreen` 在切换后按新栈顶屏的 `flags_default` 重置（HTML 侧在清空 DOM 的那支里、浮层支各自复位）。
- **★ 铁律一：只在状态上互斥的重叠热区，必须靠 `vis_flag`，不得靠 z 排序**（2026-09-22 阻断项修复 A）：「命中取最高 z」只能决定**谁赢**，不能让被覆盖者**可达**。实例：`quick.hit_toggle`（x1842 y7 w78 h898，z=96）完整覆盖 12 个 `quick.hit_*`（x1845 w75，z=95）⇒ 两态都可见时展开态点竖条任何位置都派发把手动作、12 项全不可达；故二者**互斥可见**（把手 `vis_when=collapsed`、12 项 `vis_when=expanded`）。**压 z 不是解**：那会让展开态「项间缝隙」的点击穿透到承载屏（剧情推进），而收起态又必须有一条覆盖全高的把手热区。
- **★ 铁律二：同时可见的「整块区域热区 + 块内具体控件」→ 让具体控件赢（抬它的 z）**（2026-09-22 一审 G1/G2 修复）：区域热区是「整块可点」的便利层（`sv.hit_back` 320×68 —— 该处**无对应美术**；`cfg.it_facewindow_hit` 整行 256×59），块内的具体控件才是**精确交互矩形**（PSB `#rects/...`）。实例：`sv.cpy`（复制）原被 `sv.hit_back`（action=`close`）**100% 吞掉**（9516/9516 ⇒ 点「复制」直接关屏）、`sv.mov` 被吞 2379 px，修复后 `sv.del/mod/mov/cpy` z=97 > `hit_back` 96；`cfg.on_hit`/`cfg.off_hit` 原被 `cfg.it_facewindow_hit` 逐像素 100% 吞掉，修复后 z=96（`cfg.mute_hit` z=97，须同时高于 `off_hit`：二者矩形重叠且它声明更早，同 z 时会被 off_hit 抢走 63%）。**为什么是抬 z 而不是收窄区域热区**：区域热区的意图范围往往**无美术可量**（如 `sv.hit_back`），收窄等于凭空决定其边界、并把让出的区域变成死区（本屏点空不派发任何动作）；抬 z 则完整保留它在具体控件之外的全部面积。**统一表述**：重叠时**更具体者赢**；若二者只在某个 flag 状态下共存 → 走铁律一。
- **flag 名的枚举口径（两端相同）**：TJS2 的 `Dictionary` **没有枚举接口**（无 `for...in`、无 `count`，见 `kirikiri-unpack\引擎工作原理.md` §5.1/§5.4），故两端都按「**该屏元素的 `vis_flag` ∪ `reveal.flag` ∪ `reveal.tip_flag` ∪ `reveal.pin_flag`**」逐名取 `flags_default` 的初值；`flags_default` 里**未被引用**的键不参与任何可见性判定（无行为差异）。（两端读取实现随修复 C 一并补上 `pin_flag`；`qbar_pin` 目前另经 `quick.pin_mark` 的 `vis_flag` 被引用，故行为不受影响。）
- **默认状态不得改变现有画面**：屏不写 `flags_default` 时 flag 表为空，所有 `visible_default !== false` 的元素照常可见可点。

### ★ 第 2 步：流程图屏的 `fc_layer`（主干 / 番外独立层切换，`ISSUE-20260928-02`）

> ★★ **第 3 批订正（2026-09-28）：`fc_layer` 只作用于「图内容层」，外壳件不参与。**
> 冻结书 §二 原写「现有 117 件**全部**加 `vis_flag:"fc_layer"` + `vis_when:"main"`」**作废**。
> **理由（实测）**：外壳件（视口 `fc.scroll` / 缩放平移滚条 / 页签 / 标题牌 / 关闭 /
> 付箋 / 进入本章 / **右栏四段**）是**两种层共用的舞台**，只有「图内容」随层切换；
> 外壳件也挂 `vis_when:"main"` ⇒ 切到第 G 组独立层时外壳被**一并隐藏**，组名与网格被画到
> **没有底图的透明/黑画面**上（HTML 实测证据 `_工作\ISSUE-20260928-02_HTML\证据\E3_frag_frag1.png`：
> 深墨色组名几乎不可读）。⇒ **层旗标由图内容层独家持有**；外壳件**不写 `vis_flag`/`vis_when`**。
> 生成器对此刻意做**落盘前双向自检**（外壳件带旗标 ⇒ 拒；图内容件缺旗标 ⇒ 拒）。
> ★★ **第 11 批（`ISSUE-20260929-02`，2026-09-29）：新增具名豁免集 `STATIC_FLAG_EXEMPT = {"fc.pbkick", "fc.pbkick_pause"}`。**
> 右栏新增「播放键／暂停键」一对：**同矩形、同 z**，靠**屏级 flag `fc_replay`** 的 `"play"`／`"pause"`
> **互斥显示**（用户 2026-09-29 指令 1+3），故这两件**必须**带 `vis_flag`/`vis_when`。
> **为什么可以豁免**：`fc_replay` **不是层旗标** —— 它不参与 `fc_layer` 的切层，初值 `"play"`
> 在**任何层**都成立 ⇒ 播放键恒可见，本禁令要防的「切层丢外壳」风险**不存在**。
> ⇒ 生成器自检（载入处 `_dup` 与落盘前 `shell_flagged` 两处）**减去该豁免集**后再判；
> 闸门侧同步（`m01` ①b、`m03` ① 用同名常量），并带**豁免集过期检测**（集内件若不再带旗标 ⇒ 判失败）
> 与**反向自证**（打印原始谓词命中数 ⇒ 证明豁免是减法、判据未失效）。**集外仍严格拒绝。**

| 项 | 口径 |
| --- | --- |
| 屏级 flag | `screens/32_flowchart.json` 的 `flags_default` 新增 **`{"fc_layer": "main"}`** |
| 取值（**冻结 §二**） | `"main"`（主干）／ `"frag1"`…`"frag6"`（6 个番外组各自的独立层；组号来自 `spine.json` `side_stories[].group` 的首次出现序） |
| **谁持有旗标**（★ 第 3 批） | **仅图内容层**：`fc.node.*`（含 `_tx`/`_hit`/`_dim`/`_new`）、`fc.branch.*`、`fc.label.*`、`fc.entry.*`（含 `_hit`）、`fc.frag*`（独立层族）。生成器常量 `LAYER_OWNED_PREFIXES` 是唯一判据 |
| 主干件 | 上述图内容层里 `vis_when:"main"` 的那批＝**主干 57 件**（`fc.node.*` 39 ＋ **`fc.label.*_tx` 6** ＋ `fc.entry.*` 12；`fc.branch.*` 本屏 **0**）。★ 与独立层族（节点 135 ＋ 每组顶栏 30）合计 ⇒ **图内容层 222 件**；`screen1` 总数：外壳 **52** ＋ 图内容 **222** ＝ **总 274**（★ 第 12 批订正 · 2026-09-29：原写「主干 63 / 内容 228 / 总 280」＝第 11 批口径，**已作废**——6 件 `fc.label.<NNNN>` 底板退场、`fc.sysbar` 退场、`fc.bg` 新增；再早的「117 件/283 件/图内容 222（第 3 批）」「外壳 61 / 总 289」亦作废）<br>★ **第 13 批再订正（2026-09-29 · `ISSUE-20260929-05`）**：`screen1` ＝ **外壳 40 ＋ 图内容 222 ＝ 总 262**（`fc.mtab*` 12 件与 `fc.fusen_*` 6 件退场、`fc.mode_*` 6 件新增）<br>★★ **第 15 批（2026-09-30 · `ISSUE-20260930-02`；第 2 轮用户裁定 5/6/7 已并入）**：`screen1` ＝ **外壳 50 ＋ 图内容 222 ＝ 总 272**（章节详情加 **10 件**外壳元素：加号按钮 2 ＋ 详情浮层 **8**〔基座 6 ＋ 关闭件 `fc.intro_close`/`fc.intro_close_hit` 2〕；五档 ⇒ **272/116/95/109/128**，17 屏合计 **1401**）—— ⚠ **本读数已被第 16 批取代**<br>★★ **第 16 批现行（2026-09-30 · `ISSUE-20260930-06` · 用户裁定 5）：`screen1` ＝ 外壳 **50** ＋ 图内容 **246** ＝ 总 **296****（独立层改**纵向流水、组内全量产出** ⇒ 第 6 组 12 → **20 格**、独立层节点 **135 → 159**〔53 格×3〕；外壳 **50 不变**；五档 **296 / 116 / 95 / 109 / 128**，17 屏合计 **1422**〔★ 冻结 §7.1 勘误 4 定第 16 批终值 **1422**；中间值 1425 只作历史留痕〕（★ **D-01 2026-10-01**〔`ISSUE-20261001-11`〕：`title` 屏 18→24 ⇒ **17 屏合计现行 1428**））⇒ 本行上句的「**总 274**」「**总 262**」「**总 272**」**均已作废**，以 §六 第 16 批块与屏数据为准 |
| 独立层件 | `fc.frag<G>.*`／`fc.frag<G>_title`（+**`_title_bg` 标签底板**）／`fc.frag<G>_back`／`_back_tx`／`_back_hit` 用 **`vis_when:"frag<G>"`**（★ 第 3 批：返回键**按组**，因一个元素只允许一对 flag，一个键无法同时服务 6 层；★ 第 5 批：顶栏 = **标签底板 ＋ 文字**；★ 第 7 批：底板换 444×52 专用硬边件。⚠ **第 12 批（`ISSUE-20260929-04`）订正**：本行原写「与主图 `fc.label.<N>`/`_tx` 同惯例」——**主图那一侧的底板已在第 12 批被用户裁定删除**（改为「淡黄入口块 `fc.entry.<NNNN>` ＋ 其上的组名文字 `fc.label.<NNNN>_tx`」）⇒ 「同惯例」只剩**独立层这一侧**成立；独立层顶栏**仍需底板**（组名墨色 `@palette.psv_ink` 画在独立层舞台上要一块亮底）。★★ **同批：加背景后「组名墨色直画舞台只有 1.19:1」这条前提已作废** —— 舞台底座由「黑」改为 `fc.bg`（满幅背景）⇒ 合成色 ≈ **(151,161,171)**、对墨色 **6.045:1**（`m03` 实跑复算，见 §七 与 `_工作\ISSUE-20260929-04_流程图件\证据\`）；**底板保留不改、通过判据（≥4.5:1）不变**） |
| 外壳件 | **不写 `vis_flag`/`vis_when`**（两态共用舞台，任何层都绘制） |
| 连线 | `fc_layer != "main"` ⇒ **两端一律不画任何连线**（硬判据，冻结 §四.1）；数据侧表现＝**独立层不产 `links`** |
| 切换动作 | **`flow_layer`**（见 §六 动作表），带 `layer` 参数；把该 flag 置为目标层并重绘／重算命中 |
| 与逐节点状态 flag 的关系 | `fc.state.<NNNN>`（节点叠加件用）与 `fc_layer` 是**两组不同的旗标、落在不同元素上** —— 「一个元素只允许一对 `vis_flag`」仍是硬约束 |
| **交付样例闭环**（★ 第 3 批；★ 第 16 批改口径） | 无参 `screen1` 产**全部 6 组**独立层 ⇒「点入口 → 进该组独立层 → 点该组返回键 → 回主干」在交付样例上闭环（此前只有入口热区、没有独立层元素：点一下屏面变空且**回不来**，HTML 实测 1,510,027 差异像素、全黑）。★ **2026-09-30（`ISSUE-20260930-06`）：独立层改「纵向流水、组内全量产出」** ⇒ G6 组内 20 章由旧口径「只产前 12 格」改为**全产 20 格**（第 5–7 行 y＝1054/1246/1438）；**旧句「视口只容 12 格、超出者由 `--frag-report` 列明」已作废** —— 现行 `--frag-report` 逐组报「未产 = 0」 |
| **入口热区的作用域**（★ 第 4 批 · 裁决 4） | **`fc.entry.<NNNN>_hit` 只在该组的独立层确实在本档产出时才产**（`build()` 的 `skip_hit`）。未产出 ⇒ **不产热区**，入口块 `fc.entry.<NNNN>` 与组名文字件 `fc.label.<NNNN>_tx` **仍在**（主干层可见的**纯占位**、不可点；★ 第 12 批：原写「入口 image 与 `fc.label.<NNNN>`（底板）仍在」，底板已于该批删除）。落盘前**无条件**自检「存在 `fc.entry.*_hit` ⇒ 其 `layer` ∈ 本档产出层」。**各档入口热区数**：`screen1` **6/6** ｜ `frag` **1**（只产第 1 组）｜ `screen2`/`ref150`/`states` **0**（不产独立层）。逐预设机检自证 = `复现脚本\m05_entry_hit_layer_scope.py`（含两条反向自证） |

> ★★ **通用教训（`ISSUE-20260928-03` · 2026-09-28）：运行态叠层的「强度」由元素 `opacity` 控、「形状」由素材 alpha 控。**
> **方角 / 圆角必须由素材决定**，**不得**用元素矩形去「近似」带透明角的底图。反例（本次修的**真缺陷**）：
> 未解锁压暗件原为 `kind:"rect"` 的**方角矩形**（`x+6,y+8,284×48`、`#000000`、`opacity 110`），
> 而节点底图**可见实体面四角是 r=16 圆弧、弧外透明** ⇒ 矩形四角压在背景上，locked 节点**每角露出约 55px 暗方角**
> （实测方角处显示色 **(8,10,13)** vs 同型 available 节点 **(15,18,24)**）。修法＝改 `kind:"image"`（见命名表 `_dim` 行）。
> 同一条也适用于 `_read`（20×20 对勾）等一切运行态叠层。

### 元素类型（`kind`）

| kind | 用途 | 必需字段 |
| --- | --- | --- |
| `image` | 贴图（含九宫格拉伸） | `asset` `x` `y` `w` `h` `nine?` |
| `text` | 引擎绘制的文本 | `x` `y` `w` `h` `font` `align` `valign` `wrap` `sample` |
| `rect` | 纯色矩形（面板底/高亮/遮罩） | `x` `y` `w` `h` `color` `opacity` |
| `hit` | 可点击热区（按钮） | `x` `y` `w` `h` `action` `label` |
| `list` | 重复项列表（菜单/按钮条/存档槽/画廊格/曲目/节点） | `x` `y` `w` `item_h` `labels` `actions` `font`（横向另有 `item_w`/`max_cols`） |
| `anim` | 粒子/循环动画 | `asset_frames` `x` `y` `count` `period_ms` |
| `slider` | **滑块**（音量/速度/浓度；可拖动、可写设置）★ M47 | `x` `y` `w` `h` `min` `max` `step` `value` `rail` `handle` `setting?` |

#### `slider` 元素字段（★ M47 新增，2026-09-24）

```jsonc
{
  "id": "cfg.sl_winopac", "kind": "slider", "z": 22,
  "x": 307, "y": 681, "w": 364, "h": 24,          // 元素框；轨道以**垂直中心线**为轴
  "min": 0, "max": 100, "step": 5, "value": 90,    // value = **初值**（运行期值在内存仓）
  "setting": "dlg_winopac",                        // 可省；空串 = 纯视觉滑块（不写设置仓）
  "rail":   { "asset": "ui/x_ui_cfg_rail.png" },                    // 轨道（364×11，默认 1:1；给 nine 则九宫格拉伸）
  "handle": { "asset": "ui/x_ui_cfg_knob.png",                      // 手柄（29×29，不随元素框裁剪）
              "state_assets": { "normal": "ui/x_ui_cfg_knob.png", "hover": "ui/x_ui_cfg_knob_over.png" } }
}
```

**拖动契约（两端必须逐条一致）**

| 项 | 口径 |
| --- | --- |
| 命中 | 滑块**自己不参与** `uiScreenHoverAtIn` 的候选并集（判据不动、指纹不动）；拖动由**配对的热区**驱动 —— 热区（`kind:"hit"`）多一个字段 **`"slider": "<slider 元素 id>"`**，矩形按需覆盖轨道与手柄 |
| 按下 | 指针在带 `slider` 的热区上按下 ⇒ 进入拖动 + 立刻按 x 置值（`x → min..max`，`step` 取整） |
| 移动 | 拖动期间每次指针移动都按 x 更新；**越界 clamp；移出热区/轨道不取消拖动**（与「规则③ 指针移出即取消按下态」**语义不同**，注释里须写清） |
| 抬起/换屏 | 结束拖动（换屏即清） |
| 视觉 | 拖动中或悬停该滑块时手柄用 `hover` 图 |
| 值仓 | 屏幕级运行期仓 `id → 值`（初值取元素 `value`；**换屏返回保留运行期值**） |
| 写设置 | `setting != ""` ⇒ 值变化即写设置仓（clamp + step 对齐） |

### `slider.rail.nine` 的三种呈现口径（★ ISSUE-20260928-02 实测收口）

| `rail.nine` | 引擎 `uiWidgetDrawSlider:1435` | HTML（`复刻/replica.js::buildSlider`） | 等价条件 |
| --- | --- | --- | --- |
| 非全零 | `rh = el.h`，九宫格拉满元素框 | `border-image`（border-width = nine 四边） | 恒等价 |
| **全零 `{0,0,0,0}`** | `rh = el.h` ⇒ **整图拉伸到 `el.w × el.h`** | `background-size: 100% 100%` | 恒等价（2026-09-28 修正） |
| 无 `nine` | `rh = 素材高` ⇒ `el.w × 素材高` | `background-size: 100% auto` | **仅当 `el.w == 素材宽`** |

- **数据侧义务**：无 `nine` 的 `rail` 必须满足 `el.w == 素材宽`（本工程 **4 条**无 nine 滑轨：`cfg.sl_winopac/textspeed/autospeed` 均 360 == 360、**`mu.vol` 488 == 488**（`28_music.json`），实测等价；违反则 HTML 等比缩放、与引擎分叉）。
  > ★ **2026-09-28 订正（HTML 侧一审发现）**：本条原写「**3 条**」并只列 cfg 屏三条 —— 漏了 `28_music.json` 的 `mu.vol`（该处的证据头写「cfg 屏 slider 9 条」，属把 cfg 屏结论外推为全工程）。**已按全工程 9 条滑轨逐条复核**（4 条无 nine ＋ 6 条全零 nine，无非零 nine 情形），义务在 4 条无 nine 上全部成立。
- **2026-09-28 收口**：全零 nine 原先与「无 nine」共用 `100% auto`。本屏 6 条声音滑轨（素材 `x_ui_psv_rail_c2_0*.png` 360×30、元素 330×30）实绘盒 **27.5px** 而引擎 **30px**，**两端差 2.5px**。已按上表改为 `100% 100%`，改前/改后区域差异像素合计 **16,822**，对照组 **0**。

**设置仓（★ M47 新增）**

| 项 | 口径 |
| --- | --- |
| 定义表 | 唯一来源：`krkr/game/ui_settings.tjs` 的 `UISettingDef`（键 / min / max / 默认值）；HTML 端 `replica.js` 的 `SETTING_DEF` 与之同名同默认值 |
| 现有键 | `dlg_winopac`(0–100, 默认 90)｜`text_speed`(60)｜`auto_speed`(50)｜`vol_master`/`vol_bgm`/`vol_se`/`vol_sysse`/`vol_voice`/`vol_char`(80) |
| 实时生效 | **`dlg_winopac` 是唯一有渲染效果的键**：它同时驱动 `dlg.mask_bottom`（对话框底部渐变遮罩）与 `cfg.pv_mask`（设置屏预览遮罩）的**元素 opacity**，映射式 `opacity = floor(255 × value / 100)`（HTML 为 `style.opacity = 该值 / 255`）。实现落点：**两个 ctx 构造器都要补 `ctx.opacityOverride`**（`uiScreenCtx` 与 `uiDialogBuildCtx`；`ui_widget.tjs` 的 image 分支早已支持读它）。 |
| 音量类 | **只存值**（引擎当前无音频代码）⇒ 由编程组接线；不得声称已生效 |
| 持久化 | `savedata/ui_state.txt` 的 `settings=k:v,k:v` 行（`ui_state.tjs` 的 save/load 三处齐改） |

**分页与选中态（同屏内多页，复用既有 flag 机制，不新增机制）**

| 项 | 口径 |
| --- | --- |
| 页 | 屏级 `flags_default: { "cfg_page": "sys", "cfg_vchar": "<默认角色族>" }`；两页元素 `vis_flag:"cfg_page"` + `vis_when:"sys"|"snd"`，且**必须 `visible_default:true`**（铁律：靠 flag 控显隐写 false 会成死件） |
| 选中 | ON/OFF 当前值 = `vis_flag:"cfg_v_<key>"` + `vis_when:"on"|"off"`；角色列表选中项 = `vis_flag:"cfg_vchar"` + `vis_when:"<族名>"` |
| 动作 | `config_tab_1` / `config_tab_2`（切页）｜`config_char_<族>`（选角色）｜`config_set_<key>`（被点热区带 `"value":"on"|"off"`）｜`config_reset`（恢复设置默认值 + 回系统页） |

**值键的页归属是「算出来的」（★ M47；两端同口径，改这里前先读）**

`vis_flag` 一个元素只允许**一对**（§四）⇒ 值 / 选中元素带**值 flag**，**页归属写在同行的 `hit` 上**
（否则非本页的热区会跨页抢点击）。所以值元素的跨页显隐**必须**由「切页值标志派生」维持：
非本页的值键**置空串**、本页的按三级优先链取回（**设置仓 → 切页记忆 → `flags_default`**）。

| 派生出口（两端同名 / 同动作） | 触发时机 |
| --- | --- |
| `uiScreenConfigSyncPage` / `configDerivePageFlags` | 动作 `config_tab_1`·`config_tab_2`（切页）、`config_reset`（初始化）、`config_char_*`（选角色）、`config_set_*`（改值） |
| `uiScreenConfigFlagsInitFor` / `configFlagsInitFor` | 进屏 / 深链装点（**`captureMemo=false`**：进屏那刻 flag 刚被 `flags_default` 重置，捕获记忆＝用默认值冲掉用户的选择） |

> ⚠️ **派生挂在「动作」上，不挂在「写 flag」上** ⇒ **任何直接写 `cfg_page` 的 raw 路径**
> （自研观察器、调试脚本、`?flags=`）看到的是**未派生中间态**：另一页的值元素会显形。
> · 产品路径（引擎动作 / 复刻页进屏与深链）**已实测 0 残留**；
> · 编辑器「按 flag 预览」自 2026-09-24 起**同样派生**（切页 / 换屏 / 开预览 / 重载 / 深链都派生），
>   但**手选任何非页 flag（含 `cfg_vchar`）仍是 raw 逃逸口** —— 预览里会出现跨页残留，产品不可达该状态。
> 证据与断言机件：`_工作\ISSUE-20260924-03_跨页可见诊断\`（四条证据链 + `复现脚本\m47_pagescope_probe.py`，带退出码与 `--mutate`）。
> 数据侧义务：每个值键的页归属必须能从本屏数据导出（写在 `config_set_*` / `config_char_*` 热区的 `vis_when` 上）；
> **改键名、增删选项或改页归属时必须同步改这些 hit 的 `vis_when`**，否则派生会把该键判到错误的页上。

### `list` 元素字段（最常用，务必照此实现）

```jsonc
{
  "kind": "list",
  "orientation": "v",          // "v" 纵向（默认）｜"h" 横向
  "x": 456, "y": 426, "w": 368,
  "item_w": 88, "item_h": 26,  // 纵向只用 item_h；横向用 item_w + item_h
  "gap": 2, "max_rows": 6, "max_cols": 8,
  "stack_bottom": 470,         // 可省。给了则 y = stack_bottom - 本列表总高（选择肢用：由下往上堆）
  "labels": ["开始游戏", "…"],  // 中文标签，引擎绘制
  "actions": ["game_start", "…"],  // 与 labels 等长
  "font": { … }, "align": "center",
  // 可省：每项的背景框。★ M46 起可带 state_assets ⇒ **逐项三态换图**（缺省与旧版完全一致）
  "item_frame": { "asset":"ui/panel_frame.png", "nine":{…}, "opacity":210,
                  "state_assets": { "normal":"ui/x_ui_choice_off.png",     // 可省。给了就逐项换图
                                    "hover":"ui/x_ui_choice_over.png",
                                    "pressed":"ui/x_ui_choice_press.png" } },
  "highlight": { "kind":"rect", "color":"@palette.highlight", "opacity":"@palette.highlight_opa" },
  "highlight_font_color": "@palette.text_menu_sel",
  "scroll": { "mode":"page", "page_size":8 },   // 可省：超出 max_rows 时翻页

  // ★ M06 新增（都可省；缺省行为与旧版**逐字相同**）：
  // ① 逐块文案区：给了才走「折行 + 内缩 + 行距」，不给 = 旧路径（单行、无内缩、整项垂直居中）
  "item_text": { "x":219, "y":19, "w":1291, "h":168, "wrap":true, "max_lines":4,
                 "align":"left", "valign":"top" },
  // ② 逐块按钮（每个可见行各画一遍 ⇒ 天然随分页/滚动走；几何一律**块内局部坐标**）
  "item_buttons": [
    { "key":"jump", "x":15, "y":18, "w":94, "h":29,
      "asset":"ui/x_ui_jump_off.png", "nine":{ "l":13,"t":7,"r":13,"b":7 },
      "state_assets": { "normal":"ui/x_ui_jump_off.png", "hover":"ui/x_ui_jump_over.png",
                        "pressed":"ui/x_ui_jump_on.png" },
      "action":"backlog_jump:%row%", "label":"跳转",
      "font":{ "size":20, "bold":true, "color":"@palette.node_locked" }, "align":"center" },
    { "key":"replay", "x":141, "y":10, "w":44, "h":44, "asset":"ui/x_ui_spk2_off.png",
      "state_assets": {…}, "action":"backlog_replay:%row%" }      // 1:1 件、无 nine
  ]
}
```

> **标签墨迹口径（2026-09-27 · `ISSUE-20260927-03` 落地）**：`item_buttons[].label` 与带 `label` 的 `hit` 的文字，引擎端由 `ui_widget.tjs` 在**元素 y + 6px** 处建文本元素（补偿 `uiThemeRenderText` 把墨迹画在行盒顶、而 `valign:"middle"` 只居中行盒），HTML 端由 `replica.js` 以 `translateY(3 − 半行距)` 对齐；**两端墨迹均落在按钮/热区可见体中心，两端差 0.0px**（实测）。改这两类标签的纵向落点时必须两端同改。

#### `item_text` / `item_buttons`（★ M06 新增，2026-09-24 · `ISSUE-20260924-06_回想屏重排`）

> 由来：用户要求回想屏「每一块里都要有『跳转』与『重新播放』」。`list` 原先只能「整行一个 action +
> 一行居中标签」，而**静态元素做不到**（列表会分页滚动，静态件不随块走）⇒ 必须**逐项渲染 +
> 逐项子命中**，沿用 M46「列表逐项三态」的同一套路。**这两个字段只服务「行内还有子控件」的列表**
> （目前只有 `backlog` 的 `bl.list` 在用），普通列表一个键都不加、行为零变化。
>
> ★ ISSUE-20260928-07：`backlog` 的 `bl.list` **整体下移 5px**（`y 158 → 163`；底边 927 ≤ 板底 934）；该元素 note 里 canvas 绝对读数需 **+5** 换算。

| 项 | 口径 |
| --- | --- |
| `item_text` | 逐块**文案区**，块内局部矩形（相对项矩形左上）。**给了才走新口径**：`wrap` 折行（口径 = 既有 `text` 元素**同一条路径** `uiThemeLayoutText` / `uiThemeWrap`，含**行首/行尾禁则**与 `max_lines` 截断；HTML 侧为 `white-space` + `-webkit-line-clamp`）、按 `x/y` **内缩**、行距 = `font.size × line_spacing`（`item_text.line_spacing` 可省 ⇒ 沿用该 list 的）。**没给就必须与旧版逐字相同**（单行、无内缩、整项垂直居中）。`font` 可省 ⇒ 缺省沿用该 list 的 `font`。 |
| `item_buttons[]` | 逐块**按钮表**。字段：`key`（稳定标识，日志/探针用，**同一 list 内不得重复**）、`x/y/w/h`（**块内局部坐标**，不得出块）、`asset`、`nine?`（可省 ⇒ **必须 1:1**，`verify_ui [2]` 机器检查）、`state_assets?`、`action`（**不得为空**）、`label?`/`font?`/`align?`（可选文字，**引擎绘制**，单行居中 —— 铁律禁止把文字烘焙进图）、`opacity?`。 |
| `%row%` | `action` 串里的占位符 = **全局项序号**（含分页偏移，由 `uiWidgetListHit` 给出）。引擎 `uiScreenRowAction` ／ HTML `buildList` 各自替换；**机制里不得硬编码按钮几何**，一律由数据驱动。 |
| 命中优先级 | 指针落在**某按钮矩形内** ⇒ 该按钮**优先于整行**（按钮**吃掉**整行命中：krkr `uiScreenClick` 的 list 分支先问 `uiWidgetItemButtonAt`；HTML 的按钮 `mousedown`/`click` 一律 `stopPropagation`）。块内**其余区域**仍走既有 `actions[项]`。 |
| 逐按钮三态 | 与 M46 的逐项态**同一张规则表**，主语从「项」细化到「按钮」：①左键按下置 pressed（同一时刻至多一个）②抬起清除 ③指针移出**该按钮**清除 ④换屏/重渲染清除 ⑤`pressed > hover > normal > asset` 缺键**逐级回落**。**只认左键**。悬停/按下态**只影响被指到的那一个按钮的那一行**。 |
| 生效范围 | 逐块渲染 ⇒ **随分页/滚动走**（无需额外处理）。 |
| 守卫（**显式拒绝 + 打日志判词，不得静默**） | 结构非法 / 缺 `key` / `key` 重复 / 矩形零面积或**出块** / `action` 为空 / 既无 `asset` 又无 `state_assets` ⇒ 该按钮**不画、不可点**，并产出 `★M06ITEMBTN-REJECT★ <listId>[<key>] <理由>`（krkr `uiWidgetItemBtnReject` ／ HTML `itemBtnReject`，**判词串两端逐字相同**）；`item_text` 出块/零面积同款拒绝并**退回旧标签路径**。**绘制与命中共用同一个校验函数**（`uiWidgetItemButtonProblems`）⇒「画出来的」与「点得到的」永远同集。 |
| 两端实现 | krkr：`ui_widget.tjs` 的 `uiWidgetDrawList` / `uiWidgetItemButtonAt` / `uiWidgetItemButtonState` / `uiWidgetItemButtonAsset` / `uiWidgetItemText`，`ui_screens.tjs` 的 `uiScreenListItemBtnHit` / `uiScreenBtnTokenAt`（悬停令牌 `ctx.hoverBtn` / `ctx.pressBtn`）。HTML：`replica.js` 的 `buildList`（逐按钮 DOM + 逐按钮事件 + 全局 `pressHolder` 台账 + `data-ui-item-btn` / `data-ui-item-btn-index` 探针属性）。**改一处须改两处。** |
| 为什么**不**复用 `uiScreenHoverAtIn` | 那条判据的候选并集是「带 `state_assets` 的元素 ∪ 带**逐项**态图的 list ∪ 带非空 `state_group` 的 hit」，被 `test_state_targets.py` 的**判据指纹**盯着 ⇒ **不得放宽**。回想屏的 list 既无元素级 `state_assets`、`item_frame` 也没有逐项态图 ⇒ 按那条判据它永远选不中，按钮悬停态无从触发。故另立一条子命中（与 M47 给滑块另立 `uiScreenSliderHitEl` 同一先例）。 |
| 验收 | 引擎巡演 `kind:"itembtn"`（8 条：第 1..4 行两按钮中心各自命中自身 + 派发行号 = 所点行）、`kind:"itemrow"`（2 条负向：块内非按钮区必须命中整行）、`kind:"itemguard"`（1 条：`item_buttons` 5 种非法形态必须逐条 REJECT，**内存副本、不写磁盘**），另加 4 条 spec 守卫 REJECT（key 不存在 / 行号越界 / 非 list / 元素不存在）；判词 `★M06BTN★` / `★M06ROW★` / `★M06GUARD★`。HTML 自检 ⑳a–⑳m（含 ⑳k 旧路径回归、⑳l 合法数据零 REJECT、⑳m 守卫负向对照）。编辑器派生高度：`复刻\editor_core.js` 的 `listSpanH` / `derivedH`。探针：`_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_editor_probe.py`（含 `--mut` 变异对照）。 |
| 语义边界 | `backlog_jump` / `backlog_replay` 本轮 = **接口冻结/占位**：引擎无音频代码（M47 已登记）⇒ 只做「命中 → 派发 → 日志/状态可见」（krkr `UIScrBacklogLastRow` ／ HTML `state.backlog`），**音频接线与真正的跳转生效留给编程组**，不得声称已生效。 |

#### `item_frame.state_assets`（★ M46）：列表**逐项**三态

| 项 | 口径 |
| --- | --- |
| 语义 | 「悬停/按住**哪一项**，就只换**那一项**的图」（不是整条列表换图）。缺 `state_assets` 时**行为与旧版逐字相同**（单张 `asset` 固定图）。 |
| 回落链 | `pressed → hover → normal → asset`，缺键**逐级回落**（与元素级 `state_assets` 同一梯级）。 |
| 谁在管 | 引擎：`uiWidgetListItemState()` / `uiWidgetItemFrameAsset()`（`ui_widget.tjs`），项序号来自 `ctx.hoverIndex` / `ctx.pressIndex`（`uiScreenListItemIndexAt`，**全局序号**、含分页偏移）；HTML：`replica.js` 的 `buildList` 逐项 `mouseenter/mouseleave/mousedown/mouseup` + 全局 `pressHolder` 台账（项外抬起/失焦兜底）。 |
| 规则 | 与元素级三态**同一张规则表**（§四 按下态）：①左键按下置 pressed（同一时刻至多一个）②抬起清除 ③指针移出**该项**清除 ④换屏/重渲染清除 ⑤pressed > hover > normal。**只认左键**（右键不得置按下态）。按下态**锚定在被按的那一项**，不跟随指针。 |
| 与高亮块的关系 | 带逐项态图的 list **不再**叠「悬停高亮块 / 悬停文字变色」（HTML 侧已关）：krkr 的高亮块只跟 `focus`（选中项）走、不跟悬停走。 |
| 验收 | 巡演 `kind:"ptr"` 合成指针步骤（`ch.choices:1` / `ch.choices:2:press`，日志打 `★M46PTR★ PASS/FAIL`）+ 自检 ⑱a–⑱l + `test_state_targets.py` 的候选并集判据/指纹。 |
| 探针语法 | 引擎巡演 `kind:"ptr"` 用 **`<元素id>:<项序号>[:press]`**（冒号）；HTML 的 URL 探针 `?hover=` / `?press=` 用 **`<元素id>~<项序号>`**（波浪号；`#` 会被当 fragment 截断，故不用）。 |

#### `item_variants`（★ M1 / ISSUE-20260924-08 新增，2026-09-24）：列表**栏位内 `n/N` 差分翻页**

> 由来：用户要求鉴赏模式「**同场景差分合并为一栏**，栏位内用 `n/N` 翻差分」。`list` 原先只能
> 「整行一张静态图」，静态元素又做不到（列表会分页滚动，静态件不随块走）⇒ 必须**逐项渲染
> ＋ 逐项子命中**，沿用 M46「列表逐项三态」与 M06「逐块按钮」的同一套路。
> **只有需要「栏位内差分」的列表才加这个键**；普通列表一个键都不加、行为零变化。

**字段形状（接口冻结，不得改名）**

```jsonc
"item_variants": {
  // ① 每栏的差分素材列表 —— **按全局项序号索引**（与 labels/actions 同索引，含分页偏移）
  "frames": [
    ["ui/x_gal_c001_1.png", "ui/x_gal_c001_2.png"],   // 第 0 栏 2 张 ⇒ N=2
    ["ui/x_gal_c002_1.png"],                           // 第 1 栏 N=1（两键都钳制）
    []                                                 // 空数组 = 该栏留空（合法）
    // 索引 >= frames.count = 该栏留空（合法，用于「情景回想第二页其余留空」）
  ],
  // ② 缩略图绘制区（**块内局部矩形**，相对项矩形左上）。可省 ⇒ = 整个项矩形
  "thumb": { "x": 0, "y": 0, "w": 291, "h": 166 },     // nine 可省；给了 nine 则按九宫格拉伸
  // ③ 左/右差分翻页子按钮 —— **与 `item_buttons[]` 元素同字段形状**（块内局部矩形）
  "prev": { "key": "vprev", "x": 6, "y": 132, "w": 40, "h": 28,
            "asset": "ui/x_ui_gal_varprev.png",
            "state_assets": { "normal": "…", "hover": "…", "pressed": "…" },
            "action": "gallery_prev:%row%" },
  "next": { "key": "vnext", "x": 245, "y": 132, "w": 40, "h": 28, "asset": "…",
            "state_assets": { … }, "action": "gallery_next:%row%" },
  // ④ `n/N` 文本区（块内局部矩形；**引擎绘制**，禁止把文字烘焙进图）
  "text": { "x": 46, "y": 132, "w": 199, "h": 28, "align": "center", "valign": "middle",
            "font": { … } },                            // font 可省 ⇒ 沿用该 list 的 font
  // ⑤ 边界口径，可省 ⇒ "clamp"
  "edge": "clamp"
}
```

| 项 | 口径 |
| --- | --- |
| 语义 | 每个可见栏画：**当前差分的缩略图**（`frames[row][n-1]` 画进 `thumb` 区）＋ 左右两个翻页子按钮 ＋ `n/N` 文本（**引擎绘制**）。 |
| `frames` 索引 | **全局项序号**（含分页偏移，与 `labels`/`actions`/`item_buttons` 的 `%row%` 同索引）⇒ 翻页后同一栏仍是同一份差分表。 |
| **留空 vs 空素材** | `frames[row]` 为**空数组**、或 `row >= frames.count` ⇒ 该栏**留空**（合法）：不画缩略图/按钮/文本，也不参与命中。`frames[row]` **含空串或非字符串** ⇒ **非法**（REJECT，见下）。 |
| `n/N` 文本 | 内容固定为 **`<n>/<N>`**：`n` = 当前张（**1 基**）、`N` = `frames[row]` 长度。引擎绘制（`uiWidgetDrawText` 同一条路径）；HTML 侧为 `.ui-list-item-var-text`。 |
| 运行期序号 | 按 **(listId, 全局行号)** 存（krkr `UIScrVarIdx`／HTML `state.varIdx`），由 `ctx.variantIndex` 传给渲染器 ⇒ **换屏不串、翻页不串**；`gallery_tab_*` 换屏时清空该屏记录。 |
| **边界 = clamp（钳制）** | 到第 1 张 / 第 N 张时按钮**照常绘制、照常可点、照常派发**，但序号夹在 `[0, N-1]` ⇒ `n/N` 不变；`N=1` 时两键都钳制。**不采用 disable** —— 理由：不引入第二条「enabled/disabled」绘制轴，且「画出来的」与「点得到的」恒同集（同 M06 的守卫哲学）。`edge` 字段保留（当前唯一合法值 `"clamp"`，其它值 ⇒ REJECT）。 |
| 命中优先级 | `item_buttons`（声明序）→ `item_variants.prev` → `item_variants.next` → **整行**（`actions[项]`）。三者**可共存于同一行**（`item_frame.state_assets` / `item_buttons` / `item_variants` 互不冲突）。 |
| 逐按钮三态 | 与 M06 的逐块按钮**共用同一套令牌机制**（`ctx.hoverBtn`/`ctx.pressBtn`，令牌 = `<listId>:<全局行号>:<key>`）⇒ 规则表同 M46/M06：①左键按下置 pressed ②抬起清 ③移出该按钮清 ④换屏/重渲染清 ⑤`pressed > hover > normal > asset` 缺键逐级回落。**只认左键**。 |
| 守卫（**显式拒绝 + 打日志判词，不得静默**） | 非对象 / `frames` 非数组 / `frames[row]` 非数组 / **差分素材为空**（含空串或非字符串）/ 按钮缺 `key` / 按钮矩形零面积或**出块** / 按钮 `action` 为空 / 按钮既无 `asset` 又无 `state_assets` / `text` 零面积或出块 / `thumb` 零面积或出块 / `edge` 取值非法 ⇒ 该件**不画、不可点**，产出 `★M08VARIANT-REJECT★ <listId>[<key>] <理由>`（krkr `uiWidgetItemVariantReject` ／ HTML `variantReject`，**判词串两端逐字相同**）。**绘制、命中、巡演守卫共用同一个校验函数**（krkr `uiWidgetItemVariantProblems` / `uiWidgetItemVariantRowProblem`，HTML 同名对应物）⇒「画出来的」与「点得到的」永远同集。 |
| 两端实现 | krkr：`ui_widget.tjs` 的 `uiWidgetItemVariants` / `uiWidgetItemVariantProblems` / `uiWidgetItemVariantRowProblem` / `uiWidgetVariantRect` / `uiWidgetVariantIdx` / `uiWidgetItemVariantButtonAt` / `uiWidgetDrawList`（variants 段），`ui_screens.tjs` 的 `uiScreenVarIdxGet/Set` / `uiScreenVariantBtnTokenAt` / `uiScreenClick` 的 list 分支。HTML：`replica.js` 的 `buildList`（`item_variants` 段）+ `variantReject`。**改一处须改两处。** |
| 网格前提 | 栏位网格用 `orientation:"h"` + `max_cols`×`max_rows`（**多行网格**，逐行折行）：CG 6×4=24 栏/页、情景回想 5×5=25 栏/页。**数据须把 list 的 `w/h` 写成网格外框**（`w = max_cols×item_w + (max_cols-1)×gap`，`h = max_rows×item_h + (max_rows-1)×gap`）；两端渲染器按同一公式折行定位（★ M1 修正：krkr 侧原先 `orientation:"h"` 只支持单行，与 HTML 不一致，本轮统一）。 |
| 资产命名（**冻结**） | 每栏的差分图资产 = **`ui/x_gal_c<新ID三位>_<差分序号 1 基>.png`**；`frames[row]` 的顺序**必须与 `映射.tsv` 该栏「统一名列表」顺序一致**（主件在前、并入成员按规格顺序）。 |
| 验收 | 巡演 `kind:"galvar"`（翻到第 n 张 ⇒ 缩略图确实换图 + `n/N` 文本更新 + 派发 `gallery_prev/next:<行>`）、`kind:"galguard"`（非法 `item_variants` 逐条 REJECT，内存副本）、`kind:"galpage"`（页内翻页）、`kind:"galtab"`（切屏后上一屏不在栈里）；HTML 自检 ㉑a–㉑n。判词 `★M08VAR★` / `★M08GUARD★` / `★M08PAGE★` / `★M08TAB★`。 |

### 顶层键 `links`（连线 · ★ `ISSUE-20260927-05` 新增，**不走 `elements` 管道**）

> 由来：流程图屏的节点连线是**程序化描线**（krkr `layerExDraw` ／ HTML canvas），不是贴图，
> 套不进 `elements`（那是「元素」管道，`verify_ui [1][2]` 按 `asset`/`nine` 审）。故屏对象新增
> **顶层数组 `links`**，与 `elements` 平级；`工具\gen_layout.py` 的 `resolve_deep` 逐键递归、
> **原样透传**到三处产物（已实测 json / tjs / js 三侧同值，`verify_ui [3]` 通过）。
> 接口来源：`_工作\ISSUE-20260927-05_流程图实现\边与节点数据契约.md`（v1.2）§三
> ＋ `_工作\ISSUE-20260928-02_第2步\接口冻结.md`（第 2 步：`state` 取代 `kind`，§一.2）。

```jsonc
"links": [
  { "id": "fc.link.0001",
    "state": "normal",             // ★ 第 2 步冻结 §一.2：normal ／ visited ／ noroute 三档（**取代**第 1 步的 `kind`）
    "pts": [[638,223],[865,223],[865,285]],  // ≥2 点；**生成器算好的正交折线**（含首尾点、整数像素）
    "w": 4,                        // 线宽（整数），**由生成器按 state 解析后写死**：normal 4 / visited 4 / noroute 3
    "color": 4280705152,           // 0xAARRGGBB 整数，**必须能在 palette.json 里找到同值键**（禁止直写色值）。
                                   // 本行示例：`palette.edge_normal` = **#266080**（＝参照作 noroute/query 深蓝，用户 2026-09-27 二次裁决取代冰蓝）
                                   // ⇒ 0xFF266080 = 4280705152。逐档色见下表。
    "arrow": true }                // 由生成器按 state 解析后写死；**noroute 为 false**（不画箭头）。
                                   // true ⇒ 末段方向补实心三角（顶点＝末点，沿末段后退 2.0×w 为底边中点，底边半宽 1.5×w）
]
```

**逐档取值（★ 冻结 §一.2，**生成器解析、两端不做任何配色判断**）**

| `state` | palette 键 | 色 | `w` | `arrow` |
| --- | --- | --- | --- | --- |
| `normal`（缺省＝**交付样例现值，外观不变**） | `edge_normal` | `#266080` | 4 | `true` |
| `visited`（已走） | `edge_visited` | `#3580A8` | 4 | `true` |
| `noroute`（不可前往／未成立） | `edge_noroute` | **`#5A5A68`**（★ 第 7 批调暗，原 `#6A6A7A`） | **3** | **`false`** |

> ★ **第 7 批（2026-09-28 · 依 vision 实测调暗）`edge_noroute`：`#6A6A7A` → `#5A5A68`**：
> 实测原值在引擎深底 **(39,45,59)** 上 **2.59:1**，**反而比 `normal` 深蓝的 2.01:1 更亮** ⇒
> **语义层级与亮度层级相反**（最不重要的一档最亮）。调暗后三档亮度与语义同序
> （`normal` #266080 ／ `visited` #3580A8 ／ `noroute` #5A5A68）；`w=3`、`arrow=false` 一律不变。
> 只改 `layout\palette.json` 该键值（+ note），`test_flow_links.py` ⑥ 的「三档色两两不同」
> 与「色值可在 palette 找到同值键」两条断言仍过。**交付样例 `screen1` 连线全 `normal`**
> ⇒ 本项**不改动交付样例的屏幕数据**（`edge_noroute` 仅被 `--preset states` 的 noroute 边引用，
> 该演示档 md5 随之变化，属预期）。

> **`visited` 取 #3580A8 而不用参照作冰蓝 #65B1D4 的理由**：后者与「选择支节点」底色 `#5FABD2`
> 的 **ΔE76 仅 3.2**（肉眼不可分），正是**上一轮被用户否决的那一档**（同一理由把 `edge_normal`
> 定为 #266080）；`#3580A8` 是登记在案的备选深蓝（对深底对比度 ≈4.35:1），与 `edge_normal`
> 同色相、明度上调一档 ⇒ 两档可辨。线型分档本身照参照作 `图表加载器_未定名.txt:56-59`
> （`normal` 5×0.75 ／ `nojump` 3×0.75 **无箭头** ／ `noroute`·`query` 4×0.75）。
> **可推翻性**：改 `palette.json` 一个键 + 重跑生成链即全局生效。
>
> ★ **修正一处历史矛盾（2026-09-28）**：本节旧示例写 `"kind":"normal"`、`"color": 4284854740`，
> 注文又写「取 `palette.edge_normal` = #65B1D4」（0xFF65B1D4 = 4284854740）——
> 而盘上实际 `edge_normal` 早已是 **#266080**（2026-09-27 用户二次裁决），示例与注文双双过期。
> 上表与示例已按**盘上真值**改写；`kind` 字段废弃。


| 项 | 口径 |
| --- | --- |
| 谁算路由 | **生成器**（`工具\gen_flow_layout.py`）。两端只按 `pts` 顺序描线 + 画箭头 ⇒ 从根上排除「两端各自路由」的分叉 |
| 三种形态 | 直线（`tx==sx`）／VZ（Z 形，源节点 kind ∉ {`select`,`branch`}）／VL（侧出，源节点 kind ∈ {`select`,`branch`}）；`sx=ax+148`、`sy=ay+65`、`tx=bx+148`、`ty=by`，公式同契约 §三 |
| 描线 | 圆角连接 + 圆端帽（**不做半径圆弧**），线宽 = `w`；**不得**用引擎/浏览器的自动箭头（`AdjustableArrowCap` / SVG marker），两端统一画多边形 |
| 首末点 | 首点贴源节点锚点（底边中点；**VL 为朝目标一侧的侧边中点**）、末点贴目标顶边中点；**无端点内缩**（`padding=0`） |
| `pts` 取值 | **一律整数像素**（§三 末「取整」）：半像素端点会让两端抗锯齿各自铺 4–6px、逐像素比对失去判别力。`my=(sy+ty)/2` 取整落盘（例：`(635+950)/2=792.5 → 792`） |
| 画布约束 | **每点必须落在 `0≤x≤1920`、`0≤y≤1080` 内**（越界的边由生成器**丢弃不产**，不裁剪、不半画） |
| 闸门 | `工具\test_flow_links.py`（**七条断言**：① 点在画布内 ② 相邻点只有一维变化 ③ 首末锚点 ④ `arrow ⇒ 末段长 ≥ 2.0×w` ⑤ 无重复相邻点 ⑥ `state`↔`color`/`w`/`arrow` 逐条自洽（含「`kind` 键不得再出现」与「三档色两两不同」） ⑦ 独立层节点不得作端点；＋**四条自证**：⑧异参复跑 ⑨变异A（挪 1px）⑩变异B（state 与色宽箭头脱钩）⑪变异C（独立层端点）；EXIT=0 才算过。`--screen <路径>` 可查任意预设产出） |

**流程图屏的元素命名（`screens/32_flowchart.json` 专用 · ★ 同 issue 新增；第 2 步增补 `fc.frag*`/`fc.entry.*_hit`，第 2 批增补 `fc.pbk_panel`，第 3 批把返回键改为**按组** `fc.frag<G>_back*`；★ 第 11 批（`ISSUE-20260929-02`）右栏大改：删 12 件、增 3 件、改 8 件；**★ 第 12 批（`ISSUE-20260929-04`）：增 `fc.bg`、删 `fc.sysbar` 与 6 件 `fc.label.<NNNN>` 底板、`fc.entry.*` 改形制、`fc.zoom_knob` 换件删 nine、`fc.p_title`/`_tx` 三槽对齐 —— 见下方「第 12 批」块**；**★★ 第 13 批（`ISSUE-20260929-05`）：删 `fc.mtab1..4`（12 件）与 `fc.fusen_edit`/`fc.fusen_reset`（6 件）、增 6 件 `fc.mode_*`（两枚模式入口）—— 见下方「第 13 批」块**；**★★ 第 15 批（`ISSUE-20260930-02`）：增 10 件「章节详情」（加号按钮 `fc.p_plus`/`fc.p_plus_hit` ＋ 详情浮层 `fc.intro_*` **8 件**〔基座 6 ＋ 第 2 轮关闭件 `fc.intro_close`/`fc.intro_close_hit` 2〕）、并把 `fc.p_text_tx` 的 `w` 收窄 398→300；第 2 轮另改几何（浮层 1240×400、加号 y 618）—— 见下方「第 15 批」块**）**

| 元素 id | kind | 说明 |
| --- | --- | --- |
| `fc.node.<NNNN>` / `_tx` / `_hit` | image / text / hit | 章（`section`）／选择支（`select`）／番外（`frag`）统一**底图 296×65**；素材 <296 宽者用 `nine` 横向拉伸（`t=b=0`）；**文字 19px / 行距 1.0（元素级 `line_spacing`）/ 文字盒宽 240（居中于节点：`x_node+28`）/ `max_lines:2` / `wrap:true`**（§九.1 收紧后判据：任何一行墨迹 ≤263px、712/712 零截断；底图不动、只收窄文字盒——禁则并字按盒宽算，只缩字号无效）；`sample` = `DATA.nodes[].cn`，**`cn` 为空则回落 `script` 名**（§九 裁决 7）；热区 `action` 本轮留空。★ 第 2 步：`fc.node.<NNNN>` 可选带 **`flow_state`**（见 §元素通用字段表），**不写即外观不变**；带状态时另有叠加件 **`fc.node.<NNNN>_dim`**（**image**，`locked` 用）/ **`_new`**（`image ui/x_ui_new.png`，`new` 用）/ **`_read`**（`image ui/x_ui_read_check.png`，`visited` 用），`current` **不产元素**（两端程序化画环） |
| `fc.node.<NNNN>_dim` / `_new` / `_read` | image / image / image | **运行态叠加件**（★ 第 2 步；`_dim` 口径由 `ISSUE-20260928-03` **修正**、`_read` 由该 issue **新增**）：<br>**`_dim`**（未解锁压暗）= **`kind:"image"`**，引用**按节点种类派生**的压暗素材 —— section→`ui/x_ui_node_section_dim.png`（236×65）／select→`ui/x_ui_node_select_dim.png`（263×65）／frag→`ui/x_ui_node_frag_dim.png`（228×65，件名冻结）；**几何与 `nine` 与该节点的底图件逐字段一致**（沿用 `asset` 的 `x/y/w/h/nine`）；**强度由元素 `opacity` 控（110）**、形状由素材 alpha 控；`z`＝节点 `z+1`；`vis_flag:"fc.state.<NNNN>"`＋`vis_when:"locked"`。<br>**`_new`** = NEW 角标（`ui/x_ui_new.png` 50×17，位置优先 `(node.x, node.y−12)`、越出图表视口或画布则回落 `(node.x+6, node.y+8)` / `z`＝节点 `z+6`）。<br>**`_read`**（已读绿对勾，`ISSUE-20260928-03` 新增·用户裁决「丙方案」）= `ui/x_ui_read_check.png` **20×20（1:1、无 `nine`）**、`opacity 255`；落点＝节点**可见实体面**（`x+6, y+8, 284×48`）**左上角内缘** `(node.x+10, node.y+12)`（距实体面左/上沿各 4px）；`z`＝节点 `z+6`（与 `_new` 同档）；`vis_flag:"fc.state.<NNNN>"`＋`vis_when:"visited"`；备选件 `ui/x_ui_read_check_alt.png` **本轮不接线**。**三条落盘前机检**：① 完全落在可见实体面内；② 与 `_new` **不共存于同一节点**（`new`/`visited` 互斥）；③ 不越出图表视口与画布。<br>三者 `vis_flag` **同为** `fc.state.<NNNN>`（逐节点一对）、`vis_when` 分别为 `"locked"` / `"new"` / `"visited"`（**与节点自身的 `vis_flag:"fc_layer"` 是两对不同的旗标，落在不同元素上**）。**`current`（当前所在）不产元素**：只留两端程序化画的金环，**不加对勾**。 |
| `fc.branch.<NNNN>` | image | `DATA.kind=="branch"` 的节点**只出分支底座**（65×65），不出节点框；底座居中于 296 宽槽位 |
| ~~`fc.label.<NNNN>`~~ / `fc.label.<NNNN>_tx` | ~~image~~ / text | ★★ **第 12 批（`ISSUE-20260929-04` · 用户 2026-09-29 追加裁决）：底板 `fc.label.<NNNN>`（image 333×38）已删**（**只删元素**；素材 `ui/x_ui_label_off.png` 保留不删）—— 底板让位于**同矩形的淡黄入口块 `fc.entry.<NNNN>`**。**只保留文字件 `_tx`**（**文字方案不动**：16px / bold / `@palette.psv_ink` / `align:center` / `valign:middle`），其矩形改为**与新入口块同矩形**：`(60, y, 296×65)`，`y` ＝ **242/337/432/527/622/717**（＝原 `fc.label.<NNNN>` 的行位，行距 95 不变）。★ 文案＝经 `GROUP_CN_MAP`/`group_cn()` 处理后的 `spine.json` `side_stories[].group`（**番外组名中文化**，`ISSUE-20260927-06`）。★ **组名标签不进生成器的四判据**（四判据只跑 `DATA.nodes` 的节点标题）⇒ 其容量以**实测 + 视觉验收**为准 —— **第 12 批复算 6 条组名（16px / 盒宽 296 / `ui_theme_wrap`）全部单行**（最长「番外·群像（新年行军 / 格兰玛尼耶）」**265.0px** ≤ 296，且 ≤ 入口块**可见实体面**带宽 280）⇒ 维持 `wrap:true` + `max_lines:1`。 |
| `fc.entry.<NNNN>` | image | ★★ **第 12 批改形制**：**番外入口块** —— 由 86×48 付箋占位件改为 **296×65 淡黄节点形块**（＝与 `ui/x_ui_node_select_off(和on).png` **一样的形状**、底色换淡黄；素材 `ui/x_ui_entry_frag_{off,on}.png` **由 `x_ui_node_select_{off,on}.png` 派生**：alpha 逐字节同源、仅换色相）；`nine{l14,t0,r13,b0}`（**与 `fc.node.*` 完全一致**）、`z:20`、`state_assets{normal,hover}` 两态；`vis_flag:"fc_layer"` + `vis_when:"main"`。**职能＝「进入该 xx 番外章节」**（由同矩形热区承担）。旧描述「占位件、非最终美术」**已作废**；旧占位件 `x_ui_fusen_off.png` 退役为历史、**文件保留不删**。★ **第 13 批订正**：旧文括注「仍被 `fc.fusen_edit`/`fc.fusen_reset` 使用」**已作废** —— 该批删了这两键 ⇒ `x_ui_fusen_{off,over,on}.png`（及 `x_ui_ftab_*`）现**零功能引用**（仅素材库保留）。 |
| **`fc.entry.<NNNN>_hit`** | hit | ★ **第 2 步新增**：番外入口热区，矩形＝入口块同一矩形（第 12 批：`(60, y, 296×65)`）；`action:"flow_layer"` + **`layer:"frag<G>"`**（＝用户说的 `fc_layer - fragx`）⇒ 把屏级 flag `fc_layer` 置为该组独立层并重绘/重算命中。`vis_when:"main"`（入口本身属主干）。★ **第 4 批（裁决 4）：只在该组的独立层确实在本档产出时才产**（未产出 ⇒ 不产本热区，入口块/组名文字降级为纯占位、不可点）。★ 第 12 批：**`action`/`layer` 一字未改**，只有矩形随入口块改形制而变。 |
| **`fc.frag<G>.<NNNN>` / `_tx` / `_hit`** | image / text / hit | ★ **第 2 步新增：番外独立层节点**（G ＝ `spine.json` `side_stories[].group` 的分组序号 1–6）。底图 **296×65**、素材 `ui/x_ui_node_frag_{off,on}.png`（228×65 ⇒ 与主干 frag 节点同件同 `nine`）；文字口径与主干节点**完全一致**（19px / 行距 1.0 / 盒宽 240 / `x=x_node+28` / `max_lines:2`），**同样跑四条文字判据**。`vis_flag:"fc_layer"` + `vis_when:"frag<G>"`。**独立层不产连线**（冻结 §二；闸门断言 ⑦ 守着） |
| **`fc.frag<G>_title` / `fc.frag<G>_title_bg`** | text / image | ★ 第 2 步：独立层**顶栏组名**。`_title`（text）文案＝生成器 `group_cn()` 结果（与 `fc.label.*_tx` 同源）；★ **第 5 批**：新增 **`_title_bg` 标签底板**（image、`z=24`＝`_title` 的 z−1、与 `_title`/返回键**同组同 `vis_when:"frag<G>"`**），且 `_title` 改为**与底板同一矩形**（`align:center`/`valign:middle`）——**文字色（`@palette.psv_ink`）与字号（24）未动**。**理由**：组名墨色原直接画在近黑舞台（`fc.dim`＋`fc.scroll` 合成 ≈(14,17,22)）上，对比度仅 **1.19:1 ⇒ 不可读**。**独立层顶栏 = 「标签底板 ＋ 文字」，与主图 `fc.label.*` 同惯例**。★★ **第 7 批换件**：底板改**专用硬边件 `ui/x_ui_fragtitle_bg.png`**（**444×52**、硬边、霜白浅蓝底板、**不透明核心覆盖整张**）—— 第 5 批复用的 `x_ui_label_off.png`（355×60）**四边宽渐隐带**，零九宫格拉到 420×38 后真不透明区仅 rows 7..30 / cols 13..406，文字框与其同框 ⇒ 首末字与笔画上下沿压在渐隐带上、**字形核心像素 5 分位对比度仅 1.04:1**（HTML 实测，中位 12.98 达标）。新件与元素**等尺寸 ⇒ 1:1、不加 `nine`**；几何 **444×52 @(66,192)**（`x` 与网格原点同左沿；`y`= 顶栏带 196..240 垂直居中 ⇒ **文字墨迹行仍 206..229、文字中心仍 218**，与第 5 批同位）。落盘前自检：**最长组名墨迹 + 2×`FRAG_TITLE_BG_PAD`(12) ≤ 444** ⇒ 当前 396+24 = 420 ≤ 444 ⇒ **余量 24px、最长组名两侧实边距各 24px**（比第 5 批的 12px 更宽裕；**第 5 批那条「余量恰好为零」已随换件作废**）；另自检「24px 文字在 52 高板内上下各留 ≥10px」（当前 **14px**）。越界即拒绝落盘 |
| **`fc.frag<G>_back` / `_back_tx` / `_back_hit`** | image / text / hit | ★ **第 3 批（2026-09-28）**：独立层**「返回主干」键，按组拆** —— `vis_when` 只能取一个值，一个返回键无法同时服务 6 层 ⇒ 每组一套：`_back`（image，三态复用 `ui/x_ui_jumpfc_{off,over,on}.png`，与 `fc.jump` 同件同 `nine`，328×61 @ 视口右上 −(6,6)）；`_back_tx`（text，文案 **「返回主干」**，**字体/字号取该屏既有按键文字口径**＝`fc.jump_tx`：size 27 / bold / `@palette.node_locked` / align:center / valign:middle / wrap:false / max_lines:1，文字框＝按钮件矩形）；`_back_hit`（hit，`action:"flow_layer"` + **`layer:"main"`**）。三者同组同 `vis_when:"frag<G>"`。**替代**第 2 步的单件 `fc.fragback`/`fc.fragback_hit`（已删除） |
| ~~**`fc.pbk_panel`**~~ | ~~image~~ | ★ **第 2 批新增（2026-09-28 · 主代理裁决 二.1）**：**场景回放窗底板** `ui/x_ui_replay_panel.png` 426×241 @1422,493（参照作 `シーン再生` 426×241 @1422,493；`res58` / `UI布局规格.md:467`）。**z=5 ＝ `fc.p_player`(z=6) − 1**（作其底板）；`visible_default:false`（与 `fc.p_player` 的「M34 互斥态分组、与 minimap 重叠、默认隐藏」一致；由运行期 `ctx.forceShow` 抬起 —— `ui_widget.tjs:1499` 的 forceShow **优先于** `ui_screens.tjs:284` 的 `visible_default===false`，故**不是死件**）。426×241 与素材等尺寸 ⇒ **1:1、无 nine**。★ **第 3 批订正**：它是**外壳件** ⇒ **不再写 `vis_flag`/`vis_when`**（第 2 批曾加 `vis_flag:"fc_layer"`+`vis_when:"main"`，属该批口径，本批按「外壳不参与层旗标」删除）。**★★ 第 11 批（`ISSUE-20260929-02`）：本元素已删除**（用户裁决「场景回放组退场」；由 `fc.play_win` 承担）—— **素材 `ui/x_ui_replay_panel.png` 保留不删**（工程口径「旧素材一件不删」） |
| **`fc.mode_main_glow`/`_tx`/`_hit`** ／ **`fc.mode_frag_glow`/`_tx`/`_hit`** | image / text / hit | ★★ **第 13 批（`ISSUE-20260929-05`）新增：两枚模式入口**（取代已删的 4 个 `fc.mtabx` 页签）。**「本篇集合」/「番外故事」**：**`180×60`**（**`_glow`/`_hit` @y25**；**`_tx` @y33** ＝ ★ **E5 订正**「文字下移 8px」，用户 2026-09-29 裁决 —— 实测原墨迹 y31..63/中心 47 vs 框中心 55 ⇒ 偏高 8px）、x = **34 / 254**（等宽 180、**间距 40**）、z = **10 / 20 / 95**。<br>· `_glow`（image）：`asset` ＝ `state_assets.normal` ＝ **`ui/x_ui_modetab_off.png`**；`state_assets{normal,over,pressed}` ＝ **`ui/x_ui_modetab_{off,over,press}.png`**（**180×60 ×3，两入口共用同一套**）、**1:1 ⇒ 无 `nine`**；`state_group` ＝ **`mode_main`** / **`mode_frag`**。<br>· `_tx`（text）：`sample` ＝ **「本篇集合」/「番外故事」**；font `size 30` / **`bold:false`**（引擎默认字体族首位即**微软雅黑 Regular**）/ `@palette.text_primary` / `outline:true` + `#000000` + 宽 2 / `shadow:false`。**文字由引擎绘制、不参与换态**（schema 不支持文字带 `state_assets`）。<br>· `_hit`（hit）：`action` ＝ **`flow_mode_main` / `flow_mode_frag`**（**拟用名**，见 §六 动作表）；`state_group` 与同组 `_glow` 相同（**靠组绑定联动换三态**：指针落在 180×60 热区任意位置，z95 的 `_hit` 胜出 ⇒ `ctx.hoverGroup/pressGroup` ＝ 该组 ⇒ `_glow` 换 `over`/`press`）。<br>· **三态口径**：三态**全靠 `_glow` 底光图承载**（同一枚柔和白淡光的弱/强/实底三档；`_press` ＝ 半透明冰蓝实底胶囊 ＋ 1px 亮边、**整体下沉 1px**）。⚠ **「文字下移 1px」无法实现**（不支持文字逐态位移、`state_group` 只配对图片层）⇒ 以「**底沉 1px**」等价表达。<br>· 它们是**外壳件**（id 不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个独立层共用的舞台）。<br>· **落盘前自检**：两枚各 3 件同 x/w/h（**`_glow`/`_hit` 逐字段同框；`_tx` 的 `y = _glow.y + 8`**）、完整落在画布内、彼此零重叠、且与任何相邻元素零重叠（满幅层 `fc.bg`/`fc.dim` 视作画布底）；`--selfcheck-mode-entries` 是变异自证。★ **E5 后口径**：`_tx` 下沿 93 与下方标题牌 `fc.titleplate` 上沿 93 **贴边（间隙 0px，半开区间 ⇒ 零重叠）**；`_glow` 与标题牌间隙仍 **8px**。 |

| `<NNNN>` | — | 4 位零填充序号，按「先 `section`、后 `lane`、再 lane 内顺序」编号，**同输入必须同编号**；`fc.frag<G>.<NNNN>` 的 `<NNNN>` 是**该组内的序**（1 基） |

- **只有这一个屏用这套命名**；`fc.node/branch/label/entry/frag*` 之外的一切元素由生成器**原样透传**
  （**满幅背景 `fc.bg`**（★ 第 12 批新增）/ 视口 `fc.scroll` / 缩放平移滚条 / **模式入口 `fc.mode_*`**（★ 第 13 批新增）/ 标题牌 / 关闭 / 进入本章 / **右栏四段**），
  ★ **第 11 批（`ISSUE-20260929-02`）起右栏为「大播放窗 / 标题 / 说明 / 台词」四段**，原「迷你地图 / 回放窗」两组退场；
  ★ **第 12 批（`ISSUE-20260929-04`）**：新增 **`fc.bg`**（**满幅背景** 1920×1080、`z=0`、素材 `ui/x_bg_flowchart.png`，
  由 `资源组\美术统一_超分\CG背景\bg72.png` 2560×1440 **0.75× LANCZOS** 降采样、不调色/不裁切/不加字；
  它是**外壳件**，不写层旗标 ⇒ 主干与 6 个独立层共用的舞台）；
  删除 **`fc.sysbar`**（`sysbar` 屏删除后留在本屏的**遗留装饰条**，无文字无点击；**素材保留不删**）；
  `fc.zoom_knob` 换件（`x_ui_zoom_handle.png` 40×31 单一竖圆角胶囊手柄）并**删 `nine`**；
  `fc.p_title`/`fc.p_title_tx` 的 `x/w` 改为与 `fc.p_text`/`fc.p_message` 及其 `_tx` **逐字相同**（三槽底对齐）。
  ★ **第 13 批（`ISSUE-20260929-05`）**：**删 4 个模式页签 `fc.mtab1..4`（＋`_tx`/`_hit`，共 12 件）与
  备注键 `fc.fusen_edit`/`fc.fusen_reset`（＋`_tx`/`_hit`，共 6 件）**（用户 2026-09-29 裁定「删掉 4 个 `fc.mtabx`
  和对应 text」「不再需要备注功能」）；原位置改由**两枚模式入口 `fc.mode_*`（6 件）**承担（见上表该行与下方第 13 批块）。
  ⚠ 本句旧列的「**页签 / 付箋**」两族**本批已删** ⇒ 旧文「页签 / 付箋 原样透传」**已作废**；
  素材 `x_ui_ftab_{on,off,over}.png` 与 `x_ui_fusen_{off,over,on}.png` **文件保留不删**（现**零功能引用**）。
  id 与几何一字不改（用 `git diff` 可复核：diff 内不含任何 §一 点名元素）。
  ★ **第 3 批：外壳件不参与层旗标**（见 §四 `fc_layer` 节的订正框）—— 这批**外壳件一律不带
  `vis_flag`/`vis_when`**，它们在主干层与 6 个独立层里**照常绘制**（两种层共用的舞台）。
  ★ 第 11 批**唯一豁免**：播放/暂停键一对（见 §四 `fc_layer` 节的第 11 批订正块）。
  实测口径（**第 16 批现行 · `ISSUE-20260930-06`**）：`screen1` **总 296 件** ＝ 外壳 **50**（带 `vis_flag` **10 件 ＝ 豁免集**：播放/暂停键 2 ＋ 浮层 **8**；违规 **0 件**）＋ 图内容层 **246**（全部带 `vis_flag`）。
  （★ 第 16 批：独立层改**纵向流水、组内全量产出** ⇒ 第 6 组 12 → **20 格**、独立层节点 **135 → 159**、图内容 222 → **246**；**外壳 50 不变**。
  第 15 批口径「总 272 ＝ 外壳 50 ＋ 内容 222」、第 15 批首轮「总 270 ＝ 外壳 48 ＋ 内容 222」、
  第 13 批「总 262 ＝ 外壳 40 ＋ 内容 222」、再早的「总 274 ＝ 外壳 52 + 内容 222」「总 280 ＝ 外壳 52 + 内容 228」
  与「总 289 ＝ 外壳 61 + 内容 228」**均已作废**。）
  ★ **第 13 批 · 模式入口与删除项的全部改动（删 19 / 增 6）**：

  | 动作 | 元素 | 说明 |
  | --- | --- | --- |
  | 删 | `fc.mtab1`…`fc.mtab4` ＋ `_tx` ＋ `_hit`（**12**） | 4 个模式页签（序章／本篇／After Story／Fragment）；素材 `x_ui_ftab_{on,off,over}.png` **保留不删** |
  | 删 | `fc.fusen_edit`/`fc.fusen_reset` ＋ `_tx` ＋ `_hit`（**6**） | 备注功能键（用户点名 4 件，另两个 `_hit` 不删会留下指向空动作的死热区 ⇒ 一并删）；素材 `x_ui_fusen_{off,over,on}.png` **保留不删** |
  | 删 | `dlg.hint`（**1**，在 `layout/screens/10_dialog.json`） | 对话框页操作提示（用户「不需要操作提示」）；该屏**手工维护** |
  | 增 | `fc.mode_main_glow`/`_tx`/`_hit`（**3**） | 模式入口「本篇集合」：180×60 @(34,**25**)〔**`_tx` @(34,33)** ＝ ★ **E5 文字下移 8px**，用户 2026-09-29 裁决〕、z 10/20/95、`state_group:"mode_main"`、`action:"flow_mode_main"` |
  | 增 | `fc.mode_frag_glow`/`_tx`/`_hit`（**3**） | 模式入口「番外故事」：180×60 @(254,**25**)〔**`_tx` @(254,33)** ＝ ★ **E5 文字下移 8px**〕、z 10/20/95、`state_group:"mode_frag"`、`action:"flow_mode_frag"` |

  ★★ **第 15 批（`ISSUE-20260930-02` · 2026-09-30 · 章节详情：说明槽截断 ＋ 详情浮层 ＋ 加号按钮）** ★★
  用户 2026-09-30 裁定（接口冻结 `_工作\ISSUE-20260930-02_章节详情\接口冻结.md` §一 **7 条**）：
  ① 加号按钮**新做**一枚 44×44 三态小徽章（风格/配色对齐 `fc.pbkick`）；② 浮层内容＝**章节标题 ＋ 简介全文**；
  ③ 加号位置＝**「说明」框内右上角**、文字槽相应**收窄**；④ 字号**不下调**，**超出边框即省略为省略号 `……`**（不得用 `...`）；
  ⑤ **浮层关闭控件＝加一枚小「×」**（复用既有 `x_ui_close_*`、**零新素材**）**＋ 保留**「点浮层之外也关」；
  ⑥ **浮层尺寸 1240×400**（原 1240×652 过大）；⑦ **加号按钮外圈描边加深到 pbkick 同值**＋**垂直对齐到首行行盒中心**。
  **加 10 件 / 改 7 件**（**素材新出 3 件**；表内 10 件全部写进生成器 `工具\gen_flow_layout.py` 的静态快照）：

  | id | kind | 几何 | 字段（逐字段与冻结书一致） |
  | --- | --- | --- | --- |
  | `fc.p_plus` | image | **(1803, 618, 44×44)**〔第 2 轮：`y` 625→**618**，对齐首行行盒中心（裁定 7）〕 | `asset:"ui/x_ui_plusbtn_off.png"` ＋ `state_assets{normal:_off, hover:_over, pressed:_press}`（**44×44 ×3、1:1 ⇒ 无 `nine`**）；`state_group:"p_plus"`；`z 27`；`visible_default:true`；**外壳件**（不带旗标） |
  | `fc.p_plus_hit` | hit | 同矩形（y 618） | `action:"flow_intro_open"`；`state_group:"p_plus"`；`z 96`（本屏非浮层热区最高） |
  | `fc.intro_scrim` | rect | **(0,0,1920×1080)** | `color:"#000000"`、`opacity:150`、`z 200`；`vis_flag:"fc_intro"` ＋ `vis_when:"open"` |
  | `fc.intro_scrim_hit` | hit | **(0,0,1920×1080)** | `action:"flow_intro_close"`（＝**点浮层之外回主页**）；`z 210`；`vis_flag:"fc_intro"`/`vis_when:"open"` |
  | `fc.intro_bg` | image | **(340, 340, 1240×400)**〔第 2 轮：由 1240×652 @340,214 改为**版面中心**（裁定 6）〕 | `asset:"ui/x_ui_gal_cell_on.png"`（源 291×166）＋ **`nine:{l:4,t:4,r:4,b:4}`**（2px 硬边 #7AB0E8 ＋ 2px 渐变 ⇒ 取 4 保真）；`z 220`；`vis_flag:"fc_intro"`/`vis_when:"open"` |
  | `fc.intro_panel_hit` | hit | 同 `fc.intro_bg`（340,340,1240×400） | `action:""`（**空动作＝吞掉点击**，点面板内不关闭）；`z 230`；`vis_flag:"fc_intro"`/`vis_when:"open"` |
  | `fc.intro_title_tx` | text | **(372, 372, 1140×44)**〔第 2 轮：宽 1176→1140（给关闭件让位）、y 246→372〕 | `sample:"章节标题"`；24px / **`bold:true`** / `@palette.text_primary` / `outline:true`＋`#000000`＋宽 2；`align:"left"` / `valign:"middle"` / `wrap:false` / `max_lines:1`；`z 235`；`vis_flag:"fc_intro"`/`vis_when:"open"` |
  | `fc.intro_text_tx` | text | **(372, 432, 1176×276)**〔第 2 轮：y 306→432、h 528→276（面板底 740 − 32 留白 = 708）〕 | `sample:"章节简介全文"`（占位）；24px / **`bold:false`** / 白字＋黑描边 2px；`align:"left"` / `valign:"top"` / `wrap:true` / **`max_lines:6`**；`z 235`；`vis_flag:"fc_intro"`/`vis_when:"open"` |
  | `fc.intro_close` | image | **(1530, 364, 26×26)**〔**第 2 轮新增**（裁定 5）〕 | `asset:"ui/x_ui_close_off.png"` ＋ `state_assets{normal:_off, hover:_over, pressed:_on}`（**与 `fc.close` 同用法**）；`state_group:"intro_close"`；**`nine:{l:6,t:6,r:6,b:6}`（同 `fc.close`；素材实为 24×26，`verify_ui[2]` 要求「无 `nine` ⇒ w/h＝PNG 实尺寸」）**；`z 236`（**必须高于面板热区 230**）；`vis_flag:"fc_intro"`/`vis_when:"open"`；**零新素材** |
  | `fc.intro_close_hit` | hit | **(1520, 354, 46×46)**〔图标外扩 10px 便于点按〕 | `action:"flow_intro_close"`（**与遮罩热区同一动作** ⇒ 两条关闭路径共用语义）；`state_group:"intro_close"`；**`z 237`**（本屏最高点击候选；**必须高于 `fc.intro_panel_hit` 的 230**）；`vis_flag:"fc_intro"`/`vis_when:"open"` |
  | 改 `fc.p_text_tx` | text | w **398 → 300**（x1437/y623/h138 不变） | 其余字段（24px / bold / wrap / `max_lines:4` / `valign:top`）**一字不改**；终值槽宽 **300**（M4 几何定标：344 档超上限 384px＞354px，300 档 336px ✓） |

  - **屏级 flag `flags_default` 追加 `"fc_intro": "closed"`**（进屏默认关闭浮层）；既有 `fc_layer:"main"` / `fc_replay:"play"` **不动**。
  - **z 序硬约束**：浮层**基座 6 件**在区间 **200–235**；**关闭件 2 件逐件钉死 `z 236`／`237`**（区间之外，但**必须高于面板热区 `fc.intro_panel_hit` 的 230** —— 否则点关闭会被面板的「空动作＝吞点击」吃掉）。
    全族 8 件合计必须高于本屏**所有非浮层点击候选**（`kind ∈ {hit, list}`、`z` 按引擎口径**数值化**：节点/入口 `z=95`、`fc.p_plus_hit` 96、`fc.close_hit`、`fc.jump_hit`、`fc.pbkick_hit` …）
    ⇒ 浮层打开时其余热区**不可达**（由生成器 `intro_overlay_violations()` 落盘前断言 ＋ `--selfcheck-intro-overlay` **九条**变异自证；模态态亦已登记进 `工具\test_click_reach.py` 的 `MODAL_STATES`）。
    ⚠ **判据已对齐引擎**（第 2 轮 · 一审建议项）：候选集是 `kind ∈ {hit,list}`（不是只 `hit`）、`z` 走 `_z_num()` 数值化
    —— 旧的 `kind=="hit"` ＋ `isinstance(z,int)` 写法会被「`z` 写成字符串」或「`kind` 换成 `list`」骗过（一审用反例实测）。
  - **浮层族带旗标属「外壳件豁免集」**：`fc_intro` **不是层旗标**（不参与 `fc_layer` 切层），初值在任何层都成立
    ⇒ **8 件** `fc.intro_*`（基座 6 ＋ 关闭件 2）列入生成器 `STATIC_FLAG_EXEMPT`
    （与 `fc.pbkick`/`fc.pbkick_pause` 同款，理由同 §四 `fc_layer` 节第 11 批订正块；`m01`／`m03` 各持一份同名拷贝，须逐字相等）。
  - ⚠ **数据填充留编程组**：简介全文与章节标题的**取数**（按 `场景id`）、以及右栏摘要的截断内容，均由编程组接线 —— UI 组只交**容器 ＋ 几何 ＋ 状态 ＋ 动作名**，**不声称已接真实数据**。
  - ⚠ **一处与冻结书 §三.2 表内文字的偏离（已上报主代理）**：该表 `fc.intro_close` 行写「**无 `nine`**」，但同段又写「与 `fc.close` 同用法」，而 `fc.close` 正是靠 **`nine{6,6,6,6}`** 撑住 26×26（素材 `x_ui_close_off.png` 实为 **24×26**）；`工具\verify_ui.py` 的 [2] 判据是「`kind=image` 且**无** `nine` ⇒ `w/h` 必须**等于** PNG 实尺寸」⇒ 不写 `nine` 会**假失败**。本批按 **`fc.close` 同用法**落地（带 `nine`），几何 26×26 与素材复用均照冻结书。

  ★ **文本超框省略号的契约条款（第 15 批 · 冻结 §五）**：
  - **折行后行数 > `max_lines`** ⇒ 保留前 `max_lines` 行，并在**末行尾部**追加 **`……`（两个 U+2026）**；**不得用 `...`**。
  - 追加前从末行**逐字回退**，直到 `宽度(末行 + "……") ≤ maxW`（预算口径与既有 `uiThemeEllipsize` 一致）。
  - 若连 `……` 本身都放不下（`maxW - 宽度("……") ≤ 0`）⇒ **该行不画**（宁可少一行，也不许溢出）。
  - **纯渲染、不参与布局**（不改变行盒数量/位置 ⇒ 既有排版判据不变）。
  - **三处实现必须同判据**：① 引擎 `krkr/game/ui_theme.tjs`（`UIThemeEllipsisDots` ＋ `uiThemeWrap` 的截断分支收尾）；
    ② HTML `复刻/replica.js::wrapEllipsisLines`；③ Python 唯一实现 `工具/gen_flow_layout.py::apply_ellipsis`
    （`工具/test_text_ellipsis.py` 与 `_工作/ISSUE-20260930-02_章节详情/复现脚本/m57_intro_fit.py` 均**调用它**，不再各留一份）。
    三者由 `工具/test_text_ellipsis.py` 的**冻结期望表交叉闸门**对同一张表核对（含「两端返回的行逐字相同」＋ `--selfcheck` 变异自证）。
  - **引擎侧的上机判据（第 2 轮补）**：巡演新增步骤 `kind:"wrapellip"`（判词 **`★WRAPELLIP★ PASS|FAIL`**，另有 `★WRAPELLIP-REJECT★` 负向对照）
    —— 在 `krkr/game/ui_screens.tjs::uiScreenSyntheticWrapEllip` 里**直调 `uiThemeWrap`**（与 `uiThemeLayoutText` 同一支），
    用合成长串（按实测字宽反推字数）走完三个分支：长文本 ⇒ 4 行 ＋ 末行 `……` ＋ 末行实测宽 ≤ maxW ＋ 其余行无 `……`；
    短文本 ⇒ <4 行且无 `……`；极窄 maxW（`maxW − 宽度("……") ≤ 0`）⇒ **3 行**且无 `……`。
    ★ 补这支的起因：**此前引擎侧只有逻辑审阅**（交付样例各槽文字太短、巡演走不到该分支）⇒ 上机实现无机器判据。

  ★ **第 11 批 · 右栏静态件的全部改动（删 12 / 增 3 / 改 8）**：

  | 动作 | 元素 | 说明 |
  | --- | --- | --- |
  | 删 | `fc.mini1`…`fc.mini8`（8） | 迷你缩略图块（用户指令 2「我不需要小略缩图」） |
  | 删 | `fc.mapview` | 缩略图可视区框 380×300（其尺寸被沿用为大播放窗基准） |
  | 删 | `fc.pbk_panel` / `fc.p_player` / `fc.p_player_tx` | 旧「场景回放」组三件（→ 大播放窗） |
  | 增 | `fc.play_win` | 大播放窗底板 `ui/x_ui_playwin_bg.png` **380×300 @(1448,214)**、z6、1:1 无 `nine` |
  | 增 | `fc.play_view` | 大播放窗画面层 **368×288 @(1454,220)**、z7、**`asset:null` + `dynamic:"flow_scene_frames"`** |
  | 增 | `fc.pbkick_pause` | 暂停键 **119×119 @(1578,304)**、z20、三态 `ui/x_ui_pbkick_pause_{off,over,on}.png`、`vis_flag:"fc_replay"`/`vis_when:"pause"` |
  | 改 | `fc.p_title` / `fc.p_text` / `fc.p_message` | 三槽底 `y` 214→**534** / 309→**617** / 750→**777**；说明与台词槽 `h` 171→**150**（标题 `h` 73 不动；`x`/`w` 沿用 PSB 原样）。★ **第 3 轮定版**：`h` 收 171→150 是为**避让「进入本章」按钮 `fc.jump`(1474,943,328×61)** —— 上一稿台词槽下沿 995 与按钮（上沿 943）**重叠 52px**；定版台词底 **927** ⇒ 与按钮留 **16px**、按钮下沿 1004 距栏底 1019 留 15px |
  | 改 | `fc.p_title_tx` | `y` 224→**544** ＋ **白字黑描边**（`@palette.text_primary` + `outline`/`#000000`/宽 2）；仍一行 |
  | 改 | `fc.p_text_tx` / `fc.p_message_tx` | `y`→**623** / **783**、`h` 40→**138**、`valign`→`top`、`wrap`→**true**、`max_lines`→**4** ＋ 白字黑描边 |
  | 改 | `fc.pbkick` | `(1576,555)` → **`(1578,304)`**（大播放窗中央）＋ `vis_flag:"fc_replay"`/`vis_when:"play"` |
  | 改 | `fc.pbkick_hit` | `(1573,552)` → **`(1575,301,125×125)`** ＋ `action:""` → **`"flow_replay_toggle"`**（★ 第 3 轮起**两端已实现**翻转与换显，只剩画面播放属编程组） |

  ⚠ **`max_lines:4` 的由来（第 3 轮按 `h=138` 重算）**：`_tx` 盒高 **138** ÷ 行盒 **33px**
  （＝`floor(24 × 全局 fonts.line_spacing.body 1.4)`，`krkr/game/ui_theme.tjs:237`；元素级 `line_spacing` **未写** ⇒ 走全局）
  ＝ 4.18 ⇒ **4 行 132px ≤ 138 ✓**；**5 行 165px 越盒 ✗**。
  **双口径核算**（HTML 侧等效行盒按 `round(24 × 1.4) = 34`）⇒ 4×34 = **136 ≤ 138 ✓**（余 2px）—— **两端都容 4 行**。
  ⚠ 三个 `_tx` 的 `sample` **仍是占位词**（「标题／说明／台词」），运行期由编程组填。
  ⚠ **素材一律保留**：`ui/x_ui_replay_panel.png` 等旧件**一个文件都没删**（工程口径「旧素材一件不删」）。
  ★ **第 3 轮另修一处结构性缺陷**：动态层「占位标签」原先**只按高度判、没有横向钳位** ⇒
  `fc.play_view` 的第二行 `dynamic:flow_scene_frames` 墨迹实测 x1456..**1918**（戳出窗右边 1822、越过栏右边 1859、贴屏缘被切）。
  现已**两端同判据**按元素矩形宽度截断并追加 `…`：krkr `ui_theme.tjs` 新增 `uiThemeEllipsize()`（`Font.getTextWidth` 实测）
  ＋ `ui_widget.tjs` 的 `uiWidgetDrawPlaceholder` 逐行钳位；HTML `replica.js` 同规则（`ellipsizeTo` / `resolveDynLabelCands`
  ＋ `.ui-dynamic-label` 改 `white-space:pre`）。**占位底色的颜色与不透明度一字未改**。
  修后实机像素实测：两行墨迹 x∈[1456, 1800] ⊂ 窗 x[1454, 1821] ✓（右留 21px）。

  ★★ **第 12 批（`ISSUE-20260929-04` · 2026-09-29 · 流程图页四件收尾 ＋ 番外入口统一形制）** ★★
  用户 4 条指令 ＋ 1 条追问（原话见 `_工作\ISSUE-20260929-04_流程图件\接口冻结.md` §0）
  ＋ **2026-09-29 追加裁决**（形制变更的真正来源：「`fc.label.000x` 与 `fc.entry.000x` 一律删去，
  统一为**和章节素材 `ui/x_ui_node_select_off(和on).png` 一样的形状，只是底色换成淡黄（≈ `#FFFF99`）**；
  文字方案不动」）。全部改动（**素材一个不删**）：

  | 动作 | 元素 | 说明 |
  | --- | --- | --- |
  | 增 | `fc.bg` | **满幅背景** `(0,0,1920×1080)`、素材 `ui/x_bg_flowchart.png`（`bg72.png` 2560×1440 → **0.75× LANCZOS**）、**`z:0`**（在 `fc.dim` z1 之下）、`visible_default:true`、**无 `nine`**（1:1）；外壳件（不写层旗标）。**用户指令 4′** |
  | 删 | `fc.sysbar` | 遗留装饰条（`sysbar` 屏删除后留在本屏；无文字、无点击、无 `_hit`）。**素材 `ui/x_ui_sysbar.png` 保留不删**。用户裁定「删掉元素」 |
  | 删 | `fc.label.0001`…`fc.label.0006`（6） | **组名标签底板退役**（让位于同矩形的淡黄入口块）；**只删元素**，素材 `ui/x_ui_label_off.png` 保留不删；文字件 `_tx` **保留**（见下） |
  | 改 | `fc.entry.0001`…`0006`（6） | 86×48 付箋 → **296×65 淡黄节点形块**；`asset` → `ui/x_ui_entry_frag_off.png` ＋ `state_assets{normal,hover}`；**加 `nine{l14,t0,r13,b0}`**（与 `fc.node.*` 完全一致）；`z` 21→**20**；`x` 183→**60**、`y` → **242/337/432/527/622/717**。**用户追加裁决** |
  | 改 | `fc.entry.0001_hit`…`0006_hit`（6） | 矩形随入口块：`(60, y, 296×65)`（`action`/`layer` **一字未改**） |
  | 改 | `fc.label.0001_tx`…`0006_tx`（6） | 矩形改与入口块**同矩形** `(60, y, 296×65)`（`w` 333→296、`h` 38→65；**文字方案不动**） |
  | 改 | `fc.zoom_knob` | `asset` → `ui/x_ui_zoom_handle.png`（40×31 单一竖圆角胶囊手柄）＋ **删 `nine`**（旧件 29×16 内含横胶囊＋圆点两图形 ⇒ 实机「两坨」）；`(1174,112,40×31)`/`z:21`/`opacity` 不变。**用户指令 1** |
  | 改 | `fc.p_title` | `x/w` **1416/443 → 1425/422**（与 `fc.p_text`/`fc.p_message` 逐字相同）。**用户指令 4** |
  | 改 | `fc.p_title_tx` | `x/w` **1428/419 → 1437/398**（与两个 `_tx` 逐字相同）；`y/h/align/valign/wrap/max_lines/font` 不变 |

  ★ **容量实测（本工程铁律：判容量用真实语料 + 引擎折行算法）**：6 条组名在 **16px / 盒宽 296** 下经
  `ui_theme_wrap` 复刻复算**全部单行**（逐条墨迹：263.0 / 98.0 / 114.0 / **265.0** / 103.0 / 151.0 px；
  最长「番外·群像（新年行军 / 格兰玛尼耶）」265.0 ≤ 296）⇒ **维持 `wrap:true` + `max_lines:1`，未新增字段**。
  另以入口块**可见实体面**复算（`x_ui_entry_frag_off.png` 文字带 rows 24..40 的实心列映射到 296 空间为
  **7..287 ＝ 280px 宽**）⇒ 265 ≤ 280（两侧余 ≥6.5px）**仍在实体内**。证据
  `_工作\ISSUE-20260929-04_流程图件\证据\E2_文字容量实测.md`。
  ★ **相交复核（落盘前自检，真不变量）**：入口块**全部落进图表视口**且**彼此零重叠**（违反即拒绝落盘）；
  入口块右缘 **356** → 最左节点槽 **516** ＝ 横向间隙 **+160px** ⇒ 与节点道带零重叠；
  与右栏（`fc.smallmap` x1416 起）无交集。`fc.zoom_knob`/`fc.p_title` 的改动只影响右栏与缩放带，不改左栏图表区。
  ★ **行距较大的档**（`ref150` step_y=150、`screen2` 的个别锚点行）：+52 落点会越出视口下沿 ⇒
  入口块**回落到本行**（块高 65 < 行距 ⇒ 仍不压上一块）；实测 `ref150` y ＝ **242/392/542/692/842/940**、
  `screen2` ＝ **242/337/950/432/527/622**（均过「视口内 + 零重叠」自检）。
  ★ **闸门**：`m06_delivered_sample_ledger.py`（基线总账追认 **1 增 / 7 删 / 117 处字段改动**，含 `nine` 的删与增）；
  `m03_shell_and_delivery_loop.py`（**基坑口径重算**：`fc.bg` ＋ `fc.dim` ＋ `fc.scroll`；`states` 元素数 **111**）；
  `m02_states_frag_variants.py`（z 序补 `fc.bg` = 0 为**最低位**：`fc.bg` < `fc.dim` < 栏底 …）；
  `m01_screen1_appearance_diff.py`（消费同一总账）。

  ★ **静态件的素材接线改动（第 2 步那批，共 8 件）**——都是 `state_assets` 接线（不产新件），只有 `fc.zoom_minus` 改了矩形：

  | 元素 | 旧素材（HEAD） | 新素材（`normal`） | 几何 | 依据 |
  | --- | --- | --- | --- | --- |
  | ~~`fc.fusen_edit` / `fc.fusen_reset`~~ | `x_ui_fusen_off.png` | 同（补三态） | 145×48 不变 | 冻结 §三 · E1 接线。**★ 第 13 批（`ISSUE-20260929-05`）：这两件元素已删**（用户「不再需要备注功能」）；本行**仅作历史留痕**，不再描述现行屏数据 ⇒ **三态接线随元素退场而作废**（素材保留不删）。 |
  | `fc.pbkick` | `x_ui_branch_l.png`（**旧占位件**） | `x_ui_pbkick_off.png` | 119×119 不变；**删 `nine`**（★ 第 11 批位置改 (1578,304)，见上） | 主代理裁决 1 |
  | ~~**`fc.pbk_panel`**~~ | （新增） | `x_ui_replay_panel.png` | 426×241 @1422,493（★ **第 11 批元素已删、素材保留**） | 主代理裁决 二.1 |
  | `fc.zoom_minus` | `x_ui_arrow_left.png`（**旧占位件**） | `x_ui_zoomout_off.png` | **29×8 @1006,123 → 29×29 @1006,112**；删 `nine` | 主代理裁决 二.2 |
  | `fc.zoom_plus` | `x_ui_arrow_right.png`（**旧占位件**） | `x_ui_zoomin_off.png` | 29×29 不变；删 `nine` | 主代理裁决 二.2 |
  | `fc.shift_lf` / `fc.shift_rg` | `x_ui_arrow_{left,right}.png`（**旧占位件**） | `x_ui_shift_lf/rg_off.png` | 31×25 / 30×25 不变；删 `nine` | 主代理裁决 二.3 |
  | `fc.scr_up` / `fc.scr_dn` | `x_ui_arrow_{up,down}.png`（**旧占位件**） | `x_ui_scroll_up/dn_off.png` | 31×31 / 31×30 不变；删 `nine` | 主代理裁决 二.4 |

  ⇒ **7 件的静止态素材变了（本次要修的缺口）**；~~`fc.fusen_edit`/`fc.fusen_reset` 的 `normal` == 原 `asset` ⇒ 静止态同图~~（★ **第 13 批：该两件元素已删，本括注作废**）；
  其余字段逐项不变。逐条证据与「声明内 / 未声明」分离见
  `_工作\ISSUE-20260928-02_第2步\复现脚本\m01_screen1_appearance_diff.py`。
  ★ **删 `nine` 的口径**：7 件新件的 `normal` 素材与元素矩形**等尺寸（1:1）** ⇒ `nine` 只会是恒等变换；
  旧 `nine` 系继承自被替换的素材（`branch_l` / `arrow_*`）⇒ 按主代理裁决 1 一并删除，消除埋雷。
  ★ **`fc.zoom_minus` 是唯一改矩形的件**：旧 `29×8` 是参照作的**细减号字形盒**（`版式规范 §1.1` 抄自 PSB），
  新件是 29×29 圆形键（与 `fc.zoom_plus` 同规格）⇒ 取正为 1:1，并与 `fc.zoom_plus`(1321,112) / `fc.zoom_rail`(y112) 同带对齐。
  ★ 7 件的 `action` **一律保持空串**（缩放 / 平移 / 纵滚 / 回放的行为属编程组）。
  ★ **未接线登记（第 2 步时明确不做；★ 第 12 批部分更新）**：`fc.shift_knob` / `fc.scr_knob` / `fc.scr_rail`
  等滑块与轨道件 **素材组未出三态件** ⇒ 维持单态；`x_ui_zoom{out,in}_on`(41×41) 的「按下态放大」在本机制下**无法呈现**（缺口 G-2）。
  ★ **第 12 批更新**：`fc.zoom_knob` 已**换件**（`ui/x_ui_zoom_handle.png`，40×31 单一竖圆角胶囊手柄）并**删 `nine`**
  （用户指令 1「滑标应是一个指针形状，而不是现在的两个不明物体」）——但仍为**单态件**（素材组未出三态），
  故「未接线（无三态）」这一条**对它依然成立**；旧件 `ui/x_ui_zoom_knob.png` 退役、**文件保留不删**。
  ★ **`fc.pbkick`（★ 第 11 批改称「播放键」，位于大播放窗中央）已接线（★ 第 3 批登记，勿再按「未接线」理解）**：它的
  **`state_assets` 三态齐全** —— `normal` = `ui/x_ui_pbkick_off.png` / `hover` = `ui/x_ui_pbkick_over.png` /
  `pressed` = `ui/x_ui_pbkick_on.png`（均 **119×119**，与元素矩形**等尺寸 ⇒ 1:1、无 `nine`**）。
  **素材出处**：`ISSUE-20260928-02` C 组程序化产出（脚本 `m55_make_flow_assets.py`，登记于
  `流程图系统_版式规范.md` §45「场景回放窗 / 回放键」行，状态＝**素材已产**）；尺寸/位置依据参照作
  `res39/50/54/57/67/69`（`_工作\M34_交汇协奏曲UI布局规格.md:404-409` 的 `@pbkick:*` 四态 + ○/■ 两字形件）。
  ★★ **第 11 批（`ISSUE-20260929-02`）本件口径变更三处**：
  ① **位置**：`(1576,555)` → **`(1578,304)`**（大播放窗 380×300 @(1448,214) 的中央）；
  ② **与新增暂停键 `fc.pbkick_pause` 同位置、靠屏级 flag `fc_replay` 互斥显示**（本件 `vis_when:"play"`、
     暂停键 `vis_when:"pause"`；初值 `"play"`）—— 这两件是本屏**唯一获批带 `vis_flag` 的外壳件**
     （具名豁免集，理由见 §四 `fc_layer` 节第 11 批块）；
  ③ **`action` 不在本件上**（仍为空串）：播放/暂停的派发由**两件共用的热区 `fc.pbkick_hit`** 承担，
     `action` ＝ **`flow_replay_toggle`**（见 §六 动作表）。
  ⇒ 本屏**没有**任何「`fc.pbkick` 未接线 / 待裁决」的表述；若在别处见到，以本条为准。
- **`fc.sep` 不再透传**（收尾轮裁决 6）：它是旧样板的固定坐标章分隔线（`x60 y286 w1233 h2`），
  新布局节点自 `y=190` 起排、它横穿第二行节点。章分隔线应由生成器在**段边界**处产出（R2 的 1233×2），
  本轮样例只有一段 ⇒ 本屏不产。
- **具名预设 + 交付金标（★ 收尾轮 ⑪；第 2 步扩为五个屏预设 + 一个纯数据预设）**：流程图屏的生成器 `工具\gen_flow_layout.py` 有**具名预设**，
  **无参调用 = 预设 `screen1` = 交付样例**；参照作口径（`step_y=150`）保留为**显式**预设 `ref150`，
  第 2 步另加运行态演示 `states`、番外独立层演示 `frag`、以及**只交数据的** `full`；
  非交付样例的预设都明写「**不是交付样例**、跑它会把屏换成变体」：

  | 预设 | 命令行 | 规模 | 金标 md5 |
  | --- | --- | --- | --- |
  | `screen1`（**默认**·交付样例） | `python 工具\gen_flow_layout.py` | 13 节点（section 11/select 2）/ 13 连线（直线 11/VZ 1/VL 1，全 normal）/ **总 296 元素** ＝ **外壳 50** ＋ **图内容层 246**〔＝ 主干 **57**（`fc.node.*` 39 ＋ **`fc.label.*_tx` 6** ＋ `fc.entry.*` 12；`fc.branch.*` 0）＋ 独立层节点 **159**（53 格×3；★ 第 16 批：G6 12 → 20 格）＋ 每组顶栏 **30**（6 组 × `_title`/`_title_bg`/`_back`/`_back_tx`/`_back_hit`）＝ 246 ✓〕｜★ 裁决 4：**6/6 组入口热区**（无占位缺口）｜★ 第 12 批：入口块 296×65 淡黄节点形、6 件 `fc.label.<NNNN>` 底板退场 | `1c6496e7b3efff589c4fd09c613e3ef3`（content-sha256 `99b15674e782dc66…`）｜★ 第 9 批：`fc.frag6.0007_tx`（`62_1b`）按 `TITLE_HARD_BREAK` 断两行（旧单行 255px/左缘 +20.50 ⇒ 新 122/133px、左缘 +87）｜★ 第 10 批（`ISSUE-20260928-04`）：**不变量收紧 +30 ⇒ +34**（＝对勾右缘 +30 再留 ≥4px）＋ 8 条「零间隙边界簇」补硬断行 ⇒ 本档**再变 2 处**＝`fc.frag4.0008_tx`（`42_3`）与 `fc.frag4.0009_tx`（`42_4`）的 `sample` 各插一个硬换行；**该档三轮合计文字变更 3 处**（62_1b / 42_3 / 42_4）｜★ 第 12 批（`ISSUE-20260929-04`）：**1 增 / 7 删 / 117 处字段改动**（见下方第 12 批重钉块）｜★ **第 13 批：删 18 / 增 6 ⇒ 274 → 262、外壳 52 → 40**｜★ **第 15 批：加 10 ⇒ 262 → 272、外壳 40 → 50**（章节详情；第 2 轮并入用户裁定 5/6/7）｜★ **第 16 批：加 24（G6 的 13–20 格 ×3）⇒ 272 → 296、图内容 222 → 246、独立层节点 135 → 159、外壳 50 不变**（纵向流水；用户裁定 5）｜★ **冻结 §7.2（一审后返修）：G6 的 8 个溢出格 ×3 件一律 `visible_default:false`**（数据完整、默认不画；纵滚到位时由编程组置真） |
  | `screen2`（交付样例） | `… --preset screen2` | 18 节点（section 4/select 5/**frag 9**）/ 14 连线（直线 14）/ **116 元素**（★ 裁决 4：不产独立层 ⇒ **0 个入口热区**，6 个入口为纯占位）｜★ 第 12 批：124 → 118（−6 件 `fc.label.<NNNN>` 底板）；★ 第 13 批：118 → 106（−12）；★ **第 15 批：106 → 116**（+10） | `3cd4e92d91d197d2847e30442124860c`（content-sha256 `ce17b7955cfd69f1…`）｜★ 第 12 批：入口块 y ＝ **242/337/950/432/527/622**（第 3 组的 +52 落点越视口 ⇒ **回落本行** 950）；md5 与 content-sha256 都变；★ 第 16 批：md5 变（屏 note 共用）、**content-sha256 逐字不变** |
  | `ref150`（**非交付样例**） | `… --preset ref150` | 11 节点 / 10 连线（直线 9/VL 1，**无 VZ**）/ **95 元素**（★ 裁决 4：**0 个入口热区**）｜★ 第 12 批：103 → 97（−6）；★ 第 13 批：97 → 85（−12）；★ **第 15 批：85 → 95**（+10） | `43a5b40ab3bea83d57cbd053c895a535`（content-sha256 `15e50f1c4a8aadd4…`）｜★ 第 12 批：入口块 y ＝ **242/392/542/692/842/940**（step_y=150 ⇒ 末组 +52 越视口 ⇒ **回落本行** 940）；md5 与 content-sha256 都变；★ 第 16 批：md5 变（屏 note 共用）、**content-sha256 逐字不变** |
  | `states`（**非交付样例**·运行态演示） | `… --preset states` | 13 节点（同 screen1）/ 13 连线（**normal 5 / visited 4 / noroute 4 三档同屏**）/ **109 元素**（含 `_dim` 3（**image，按节点种类取件**）、`_new` 2、**`_read` 3**（已读绿对勾）；`current` 不产元素；★ 裁决 4：**0 个入口热区**）｜★ 第 11 批 126 → 117；★ 第 12 批 117 → 111（−6）；★ 第 13 批 111 → 99（−12；`_read` 仍 3）；★ **第 15 批：99 → 109**（+10） | `74392cc9b5d3f632cc693afa95b24a89`（content-sha256 `97fb4fd8a8753761…`）｜★ 第 12 批：md5 与 content-sha256 都变（−6 件底板）；★ 第 16 批：md5 变（屏 note 共用）、**content-sha256 逐字不变** |
  | `frag`（**非交付样例**·番外独立层演示） | `… --preset frag` | 主干同 screen1 ＋ **第 1 组**独立层 7/7 格 / 13 连线（全 normal，**独立层不产连线**）/ **128 元素**（★ 裁决 4：只产第 1 组 ⇒ **1 个入口热区**）｜★ 第 12 批：136 → 130（−6）；★ 第 13 批：130 → 118（−12）；★ **第 15 批：118 → 128**（+10） | `4ed7585a16ea700343328a962a9eb95a`（content-sha256 `b581b226459b48a2…`）｜★ 第 12 批：md5 与 content-sha256 都变（−6 件底板）；★ 第 16 批：md5 变（屏 note 共用）、**content-sha256 逐字不变** |
  | `full`（**非交付样例**·只交数据） | `… --preset full` | 6 段 / 19 道 / 712 lane 节点（section 579/select 77/frag 53/branch 3）；**不产 elements**，落 `_工作\ISSUE-20260928-02_第2步\全量布局.json` | —（无屏文件 ⇒ 无金标） |

  > ★ **2026-09-28 重钉（ISSUE-20260928-02 第 4 批/小收口）**：上表**前五行**为现行值。
  > 上一批（第 3 批）值 `8e7b4531…`／`ed0b065c…`／`39473905…`／`85414453…`／`db656468…`，
  > 以及更早各批全部值 **一律作废**。
  > **本批变化（裁决 4：入口热区只在「该组独立层确实产出」时才产）**：① `screen1` 产全部 6 组 ⇒ 6/6 热区（**不变**）；
  > ② `frag` 6 → **1** 个热区；③ `screen2`/`ref150`/`states` 各 6 → **0** 个热区（6 个入口降级为**纯占位**、不可点）。
  > 未产出组的入口 `fc.entry.<NNNN>` image 与 `fc.label.*` **仍在**（主干层可见的占位），只是不再产 `_hit`。
  > ⇒ **`screen1` 的主干视图与元素内容一律不变**：其 md5 由 `8e7b4531…` 变为 `42247f41…` **仅因 note 措辞**
  > （屏 note 补裁决 4 口径），**content-sha256 逐字不变**（`b050a6cfd4d19dfdd5a06af7e9bb7db07be28a959f52ff23948e3ccde4517fe3`）。其余四档元素内容随裁决 4 而变。
  > 逐预设机检自证见 `_工作\ISSUE-20260928-02_第2步\复现脚本\m05_entry_hit_layer_scope.py`
  > （五预设「存在热区 ⇒ 其 layer 在本档有元素」＋进出闭环＋`screen1` 6/6 ＋ 两条反向自证）。

  > ★ **2026-09-28 重钉（ISSUE-20260928-02 第 5 批/收口小修）**：上表**前五行**为现行值。
  > 上一批（第 4 批）值 `42247f41…`／`d9c7214e…`／`6cfa4c4f…`／`2f26fa4c…`／`a4162286…`，
  > 以及更早各批全部值 **一律作废**。**本批两件事**：
  > ① **独立层组名加「标签底板」**（真缺陷修复）：每组新增 `fc.frag<G>_title_bg`（image，素材复用主图标签
  > `ui/x_ui_label_off.png`、**零九宫格整图缩放**口径同 `fc.label.<NNNN>`、**420×38 @(66,199)**、
  > `z=24`＝标题 z−1、与标题/返回键**同组同 `vis_when`**）〔⚠ **本条所述件与几何已被第 7 批换成专用件 444×52，见下方第 7 批块**〕；标题文字件改为**与底板同矩形**
  > （`align:center`/`valign:middle`，同 `fc.label.<N>_tx` 惯例）——**文字色与字号未动**。
  > 起因：组名墨色 `@palette.psv_ink`(#16223A) 原直接画在近黑舞台（`fc.dim`＋`fc.scroll` 合成 ≈(14,17,22)）上，
  > **对比度仅 1.19:1 ⇒ 不可读**（HTML 组实测，本机复算一致）；加底托后 **≈13.5:1**（底板核心实色 (228,238,250)，WCAG 相对亮度比）。
  > ⇒ `screen1` **283 → 289 元素**（＋6 底托）、`frag` **144 → 145**（＋1）。
  > ② **静态件 `fc.zoom_minus`/`fc.zoom_plus` 的过期描述订正**：`source`/`note` 原写按下态 `_on` 为 **41×41**，
  > 实测三态**均为 29×29**（⇒ 按下不放大），已改为现况并补「『按下放大』登记为缺口 G-2」。
  > ⇒ `screen2`/`ref150`/`states` **元素数不变**，其 md5/`content-sha256` 变因**仅 `source` 订正**（五档共用同一静态件快照）。
  > 逐预设机检自证见 `_工作\ISSUE-20260928-02_第2步\复现脚本\m03_shell_and_delivery_loop.py`
  > （外壳 0 旗标＋**6 组底托齐备/同矩形/同 vis_when/z 关系＋逐组对比度 ≥4.5:1**＋进出闭环＋独立层无运行态＋每格文字四判据）。

  > ★ **2026-09-28 重钉（ISSUE-20260928-02 第 7 批/小修两处）**：上表**前五行**为现行值。
  > 上一批（第 5 批）值 `aa4be586…`／`c56ce544…`／`d4cd5447…`／`fb4d6e19…`／`8841c6a8…` 与更早各批全部值**作废**。
  > **① 组名底托换专用硬边件**：`fc.frag<G>_title_bg` 的 `asset` → `ui/x_ui_fragtitle_bg.png`（444×52、硬边、
  > **不透明核心覆盖整张**、**1:1 无 `nine`**）；几何 **444×52 @(66,192)**（文字墨迹行仍 206..229、中心仍 218）。
  > 落盘自检 **余量 24px**（396 + 2×12 = 420 ≤ 444）、文字上下各留 **14px**（≥10）。起因：复用件（355×60，四边宽渐隐带）
  > 拉到 420×38 后**字形核心像素 5 分位对比度仅 1.04:1**（HTML 实测；中位 12.98 达标）⇒ 首末字与笔画上下沿压在渐隐带上。
  > 实测新件：alpha==255 占 **99.93%**（仅 4 角抗锯齿像素），**墨迹区（含外扩 2px）非全不透明像素 0 个**；核心众数 (227,235,244)
  > ⇒ 对墨色 `#16223A` **13.18:1**（区域均值 12.41:1）。
  > **② `@palette.edge_noroute` 调暗 `#6A6A7A` → `#5A5A68`**（只改 `palette.json` 一个键）：原值在引擎深底 (39,45,59) 上
  > **2.59:1**、**反而比 `normal` 的 2.01:1 更亮** ⇒ 语义层级与亮度层级相反；调暗后三档与语义同序（`w=3` / 无箭头不变）。
  > ⇒ `screen1`（**连线全 `normal`、不含该色**）与 `frag` 的变化只来自**底托几何/素材 + note**（元素数不变：289 / 145）；
  > **`screen2`/`ref150` 的 `content-sha256` 逐字不变**（⇒ 只有 note 措辞变）；`states` md5 与 content-sha 均变（noroute 边内嵌色值）。
  > 机检见 `m03_shell_and_delivery_loop.py`（①b 第 7 批追加：1:1 / 无 `nine` / 板内墨迹区整片 alpha=255 / 底托宽度与纵向留白自检）。

  > ★ **2026-09-28 重钉（`ISSUE-20260928-03` / 第 8 批 · 节点运行态两处修正）**：上表**前五行**为现行值。
  > 上一批（第 7 批）值 `4c8f01c0…`／`51f58498…`／`e9df490e…`／`21ecd73e…`／`7f30a924…` 与更早各批全部值**一律作废**。本批两件事：
  > ① **修「未解锁压暗件方角」真缺陷**：`fc.node.<NNNN>_dim` 由 `kind:"rect"`（方角 284×48）改 **`kind:"image"`**
  >    —— 按节点种类取压暗件（`x_ui_node_{section,select,frag}_dim.png`，件名冻结）、
  >    **几何与 `nine` 与该节点底图件逐字段一致**、**强度仍由元素 `opacity` 控（110）**；`z` / `vis_flag` / `vis_when` 不变。
  >    根因：节点可见实体面**四角是 r=16 圆弧、弧外透明**，方角矩形四角压在背景上 ⇒ locked 节点每角露出约 **55px 暗方角**
  >    （实测 (8,10,13) vs 同型 available (15,18,24)）。
  > ② **新增「已读」绿对勾 `fc.node.<NNNN>_read`**（用户 2026-09-28 裁决「**丙方案**」）：
  >    `ui/x_ui_read_check.png` **20×20（1:1、无 `nine`）**、节点可见实体面左上角内缘 `(x+10, y+12)`、
  >    `z`＝节点 `z+6`（与 `_new` 同档）、`vis_when:"visited"`、`opacity 255`；备选件 `x_ui_read_check_alt.png` **不接线**；
  >    **`current` 不加对勾**（只留金环）。
  > ⇒ **只有 `states` 预设含运行态** ⇒ 元素数 **123 → 126**（＋3 `_read`）；其余四档**元素内容逐字不变**
  >    （`content-sha256` 与第 7 批同值 ⇒ 变因**仅屏 note 措辞**；五档 md5 全变的唯一原因即屏 note 追加）。
  > 逐条机检见 `复现脚本\m02_states_frag_variants.py`（【A】`_dim` image／按种类取件／几何与 nine 与底图件一致、
  > 【A】`_read` 20×20／落点在实体面内（给数值）／与 `_new` 不共存、【E】全库无 rect 版 `_dim`／`_read` 不出视口画布）。

> ★ **2026-09-28 重钉（ISSUE-20260928-02 第 9 批 · **vision 复核后的数据侧最后一处修复**）**：上表**前五行**为现行值。
> 上一批（第 8 批 `ISSUE-20260928-03`）值 `0527ae97…`／`2f76c5fd…`／`ac24df59…`／`bbac0fd5…`／`f8fb0ab6…`
> 与更早各批全部值 **作废**（`screen2`/`ref150`/`states`/`frag` 四档 md5 变因**仅屏 note 措辞**、
> **`content-sha256` 逐字不变**；只有 `screen1` 的内容变）。
> **① 新增落盘前自检（真不变量）**：所有含文字节点（主干 ＋ 独立层）的
> **首行墨迹左缘 ≥ x_node + 30**（＝已读对勾 `_read` 20×20 @(x+10,y+12) 的右缘 +30；等价「首行墨迹 ≤ 236px」）。
> 违反即**拒绝落盘**并逐条打印（节点 id / 标题 / 首行宽 / 左缘 / 行数）。实测 **712 条违规 0**、最紧 **+34.00**（`s01_02b`，第 10 批收紧后）。
> **② 新增常量表 `TITLE_HARD_BREAK`（第 9 批 12 条 ＋ 第 10 批 8 条 ＝ 20 条）**：在**自然断点**插硬换行（引擎 `uiThemeWrap` 与生成器 `ui_theme_wrap`
> 都按 `
` 分段，两端一致）。断点优先级：**A 全角开括号/引号/波浪之前**（`（`「“」「～」）＞ **B 句读标点之后**（`、`）＞
> **C 拉丁词界（空格）**；每条的拼接必须**逐字等于**源文本（`title_sample()` 内 `assert` 守住，源语料一改即报过期）。
> 断后**两行墨迹都 ≤ 230px**（实测最大 202）⇒ 左缘 ≥ +33，给对勾留 ≥4px 余量。
> **③ 交付样例的唯一外观变更**：`fc.frag6.0007_tx`（script `62_1b`）—— 旧「无论何时·棱镜（性的意义上）」**单行 255px**
> （左缘 +20.50，压对勾）⇒ 新「无论何时·棱镜」＋`
`＋「（性的意义上）」**122 / 133px（左缘 +87）**；
> 其余 11 条**不在交付样例四档里**。成因：字符串末尾是**行首禁则字符**（如 `）`）⇒ `ui_theme_wrap` 强行并入本行 ⇒ 单行 247–255px。
> **④ 机检**：`--title-check-report`（不变量实测 + 违规清单）／`--selfcheck-title-break`（**变异自证**：删一条硬断行必越线、
> 表清空须 ≥ 表内条数（现 20 条）据实报出）／`m03` 同批复算 ①不变量 ②四判据 ③外壳 61 件 0 旗标 ④`states` 126 元素。
> （★ 上句 ③④ 的 **61 / 126** 是第 10 批时点读数；**现行值为 50 / 109**——外壳 **50 件**（★ 第 15 批定值，此前第 13 批 40、更早 52）、`states` **109 元素**（★ 第 15 批：99 → 109；旧记 111 / 117 均已作废），见下方第 15/16 批块。）

> ★ **2026-09-29 重钉（`ISSUE-20260929-02` / 第 11 批 · **流程图右栏「章节详情」大改**）**：上表**前五行**为现行值。
> 上一批（第 10 批）值与 **第 11 批第 1/2 轮的中途值**（`b24cbcd6…`／`6e6f2185…`）一律作废；
> **权威现行值**＝~~上表五个 md5（`screen1 a84a1876…`／`screen2 a334aa56…`／`ref150 6ea4d018…`／`states 9a2adf60…`／`frag 19dab818…`）~~
> —— ★ **已被第 12 批重钉取代**（该批值 `screen1 1b0c2ba6…`／`screen2 7a37f9ef…`／
> `ref150 d013257e…`／`states 41db5009…`／`frag 899ee92b…`），★ **又已被第 13 批重钉取代**
> （该批值 `screen1 7fa46f2f…`／`screen2 642cf515…`／`ref150 5655e08a…`／`states d84014c5…`／`frag a1b92d6b…`），
> ★ **再已被第 15 批重钉取代**（第 15 批首轮值 `screen1 74e2fa73…` 等，**已作废**），
> ★ **又已被第 16 批重钉取代**（第 15 批值 `screen1 a41ffd35…`／`screen2 affd6dfc…`／
> `ref150 8a22d83c…`／`states e31ebb37…`／`frag 879f264a…` **已作废**；
> **现行值见本节末尾的「第 16 批重钉」表**：`screen1 61d514e5…`／`screen2 3d2f597e…`／
> `ref150 ce6698df…`／`states 247b1247…`／`frag c107a9aa…`）。
> ★ **同日第 4 轮（一审后收口 · note-only 重钉）**：上表已换为最新值 —— 该轮只订正**屏 note 里的过期数字**
> （「最宽行 255px」→**228.0px**、「最紧 +30.00（`s04_03f1`）」→**+34.00（`s01_02b`）**）与一处
> **算式笔误**（`(443−380)//2` 得 1447 ≠ 实值 1448 ⇒ 改 `ceil((443−380)/2)`）；四段几何**一字未动**。
> **自证**：五档 `content-sha256` 与第 3 轮**逐字不变**（`cd9aad7c…`/`9ff0626e…`/`4e51addf…`/`aa44bb21…`/`bd1d20e8…`），
> 变因**只在 note**（`content-sha256` 剥掉全部 note 后取摘要，正是用来分辨这件事的）。
> ★ **同日第 3 轮（收口）**：上表已换为第 3 轮真值 —— 该轮只改**几何**（三槽 `h` 171→**150**、`y` **534/617/777**、
> `_tx` `h` **138**、`y` **544/623/783**）与**动态层占位标签的两端钳位**；**元素数五档全不变**（280/124/103/117/136）。
> 动因：vision 复审实机渲染报出**两处真缺陷** ——
> ① **台词槽压住「进入本章」按钮**：上一稿台词槽下沿 995、按钮上沿 943 ⇒ **重叠 52px**（PSB 原稿台词槽下沿 921 本不冲突，是本批重排引入的）⇒ 定版台词底 **927**、与按钮留 **16px**；
> ② **动态层占位标签无横向钳位**：`fc.play_view` 的 `dynamic:flow_scene_frames` 墨迹实测 x1456..**1918**（戳出窗右边 1822、越过栏右边 1859、贴屏缘被切）。
> 两条均已修复并附**实机像素实测**（`_工作\ISSUE-20260929-02_右栏大改\证据\缺陷1_避让_前后几何.tsv`、`缺陷2_占位钳位.md`）。
> ②的修法：**两端同判据**按元素矩形宽度截断 + `…` —— krkr 新增 `uiThemeEllipsize()`（`Font.getTextWidth` 实测）＋
> `uiWidgetDrawPlaceholder` 逐行钳位；HTML `replica.js` 的 `ellipsizeTo` / `resolveDynLabelCands` ＋ `.ui-dynamic-label` 改 `white-space:pre`。
> **占位底色的颜色与不透明度一字未改**。修后实测 x∈[1456,1800] ⊂ 窗 x[1454,1821] ✓。
> **本批改的是右栏那一批「静态件」**（五档共用同一次静态快照 ⇒ **五档 md5 与 content-sha256 全变**，不同于以往「只 note 变」）：
> ① **删 12 件**（`fc.mini1..8`、`fc.mapview`、`fc.pbk_panel`、`fc.p_player`、`fc.p_player_tx`）—— **素材一个不删**；
> ② **增 3 件**（`fc.play_win` 380×300 底板 ／ `fc.play_view` 368×288 **动态层 `flow_scene_frames`** ／
>    `fc.pbkick_pause` 暂停键 119×119）—— 另**新增素材** `ui/x_ui_playwin_bg.png`、`ui/x_ui_pbkick_pause_{off,over,on}.png`；
> ③ **改 8 件**（三槽底 `y` 与说明/台词槽 `h`；三 `_tx` 白字黑描边与多行槽 `wrap`/`top`/`max_lines:4`；
>    `fc.pbkick` 移位 (1578,304)；`fc.pbkick_hit` 移位并接 `flow_replay_toggle`）；
> ④ **屏级 flag 新增 `fc_replay`（初值 `"play"`）**；⑤ **外壳件层旗标禁令新增具名豁免集**（播放/暂停键一对，见 §四）；
> ⑥ **`flow_replay_toggle` 两端已实现**（翻转 `fc_replay` + `applyFlagVisibility` 换显，**不重建 DOM**；只留画面播放属编程组）。
> ⇒ 元素数 **289 → 280**（−12＋3）；`states` **126 → 117**。用户 2026-09-29 六条指令，逐条出处见
> `UI组\会话交接_20260929-02_流程图右栏大改_开工前状态.md` §一 与 `_工作\ISSUE-20260929-02_右栏大改\接口冻结.md`。
> 逐条机检：`m06_delivered_sample_ledger.py`（固定基线总账：12 删 / 3 增 / 字段全部追认 + 屏级 `flags_default`）、
> `m01_screen1_appearance_diff.py`（①b 豁免集 + 反向自证）、`m03_shell_and_delivery_loop.py`（①外壳 52 件 / 违规 0 / 豁免 2）、
> `m39` 套 A/套 B（含 `dynamic.label-clamped` 与 `flow.replay-*` 新断言）、实机巡演（`★REPLAYTOGGLE★ PASS`、缺件 0、EXCEPTION 0）。

> ★★ **2026-09-29 重钉（`ISSUE-20260929-04` / 第 12 批 · 流程图页四件收尾 ＋ 番外入口统一形制）** ★★
> 上表**前五行**为现行值；本批之前各批的全部 md5 / content-sha256 值（含第 11 批五个 `a84a1876…`／
> `a334aa56…`／`6ea4d018…`／`9a2adf60…`／`19dab818…`）**一律作废**。
> **该批五组金标**（★ **已被第 13 批取代**，现行值见下方「第 13 批重钉」块与上表五行）：
>
> | 预设 | 元素数 | md5 | content-sha256 |
> | --- | ---: | --- | --- |
> | `screen1` | ~~**274**~~ | ~~`1b0c2ba681fcd603a0eae176c28aca00`~~ | ~~`89d9e8fcaa90ce99eed61c28677f65161f766347f0ded6cf3854b800050f632c`~~ |
> | `screen2` | ~~**118**~~ | ~~`7a37f9ef21620354f2495def102aa16b`~~ | ~~`fc2a72d82f3cc37b32812734e33c166c8748cbe980ec9140f48049e3428ff7e9`~~ |
> | `ref150` | ~~**97**~~ | ~~`d013257e4eb6f360ea0a13eac84eec70`~~ | ~~`301f6e503af0f7a402a1437360e0ccea122cdc8ee5b058a789def5ae03dbaae4`~~ |
> | `states` | ~~**111**~~ | ~~`41db5009af1bea8482242a884853a44e`~~ | ~~`c292c213b532a46aaef0b040a935dd5fab525531af138d789d316e91f093c009`~~ |
> | `frag` | ~~**130**~~ | ~~`899ee92b87f267e3869bd7809838bf51`~~ | ~~`ad8b0d116c610f1f1b0a370eaff10a549a8c65a4a30e00765b4e4a97dd3e0c87`~~ |
>
> 五档各 **−6 元素**（6 件 `fc.label.<NNNN>` 底板退场）；外壳 **52 不变**（`fc.sysbar` −1、`fc.bg` +1）。
> 逐条机检：`m06`（基线总账：1 增 / 7 删 / 117 处字段改动，**含 `nine` 的删与增**）、
> `m03`（基坑口径改 `fc.bg`＋`fc.dim`＋`fc.scroll`；`states` 111）、
> `m02`（z 序 `fc.bg`=0 最低位）、`m01`（消费同一总账）、实机巡演（见工程记录）。
> ⚠ **生成器侧修复（本批实测暴露）**：`refresh_golden()` 原先只同步**内存里的 `PRESET_TABLE`**、
> **漏了内存 `GOLDEN`** ⇒ `--refresh-golden` 末尾自证必然 FAIL（退出码 1，虽然文件已正确写盘）。
> 本批补 `GOLDEN.update(...)`（见该函数内注释）。

> ★★ **2026-09-29 重钉（`ISSUE-20260929-05` / 第 13 批 · 模式入口收敛 ＋ 删备注功能与对话框提示）** ★★
> **第 13 批当时的五组金标（⚠ 已被下方「第 15 批重钉」表取代，此处仅作历史留痕）**（`工具\gen_flow_layout.py` 的 `GOLDEN`，`--refresh-golden` 实跑真值）：
>
> | 预设 | 元素数 | md5 | content-sha256 |
> | --- | ---: | --- | --- |
> | `screen1` | **262** | `7fa46f2f1daa2614a345d8840c1ea24c` | `4453b8ca528e7088824445eccb931c6c6db30f833d7f467d48c43e8befb65653` |
> | `screen2` | **106** | `642cf5157a87e1445571f4c2e07bcc0c` | `f114914779214379385ebe01fa9389c0349a6a40474289b786c63cbd4aae99b2` |
> | `ref150` | **85** | `5655e08a03698bbad0a388bab97a0b74` | `6ecf17348e9e15e30a4b8f6e6de7cd93e3bcdcb1d7a48f3b8d6481a672d4af08` |
> | `states` | **99** | `d84014c56f757bc568114ca079ba1c20` | `90421f934f2c063598bb61d34d4c93463c2a8bc7b966a6a39657fdad7bfaef7c` |
> | `frag` | **118** | `a1b92d6bfac94aae4992bf5e6fc97e10` | `4f6d605ecc81e4af64af1d049773b6dfc9968566f8479b714de35b0bb6c0e1ee` |
>
> 五档各 **−12 元素**（删 12 件 `fc.mtab*` ＋ 6 件 `fc.fusen_*`、增 6 件 `fc.mode_*`）；外壳 **52 → 40**、图内容层 **222 不变**；
> `dialog` **10 → 9**（删 `dlg.hint`，该屏手工维护）；**17 屏合计 1404 → 1391**。〔⚠ **勘误**：接口冻结 §E 记的「`dialog` 18 → 17」是**绝对值笔误**（本屏实际只有 10 件），其 **−1** 的增量正确；实测：`layout/screens/10_dialog.json` HEAD 10 件 → 现行 9 件，17 屏合计 1404 → 1391 逐屏求和核对一致。〕
> 逐条机检：`m06`（基线总账：**18 删 / 6 增 / 新件载荷字段追认**；并把 **`state_group` 补进 `APPEARANCE_FIELDS`** ——
> 此前它不在清单里，属上一批遗留的**闸门盲区**）、`m03`（`states` 元素数 **111 → 99**，`_read` 仍 3）、
> `m02`（两件 `fc.fusen_*` 移出「九宫格件」名单 ⇒ 由三段**等强度新断言**接手：① 六件 `fc.mode_*` 的三态素材在库
> 且与元素 **1:1／无 `nine`**；② `fc.mode_*_hit` 的 `action` **非空且能在 §六 动作表查到**；③ 同 `state_group` 的
> `_glow` 与 `_hit` **配对**且三态齐；另加**反向断言**「18 件旧件均不在屏数据里」⇒ **只增不减覆盖**）、
> `m01`（消费同一总账）、实机巡演（`★MODESTATE★`，见工程记录与 `_工作\ISSUE-20260929-05_模式入口\证据\`）。

> ★ **E5 重钉（2026-09-29 · 同 `ISSUE-20260929-05` 的一审后订正轮）**：用户裁决「**两个模式入口的文字下移 8px**」
> ⇒ `fc.mode_main_tx` / `fc.mode_frag_tx` 的 `y` **25 → 33**（`x/w/h` 与 `font`/`align`/`valign`/`wrap`/
> `max_lines`/`sample` 一字未动；**`_glow`/`_hit` 仍 y25**）。依据：vision 实测原墨迹恒为 **y31..63（中心 47）**，
> 而元素框 `y25..85` 的中心是 **55** ⇒ 偏高 8px；下移后墨迹 **y≈39..71、中心 55 与框同心**（证据
> `_工作\ISSUE-20260929-05_模式入口\证据\E5_文字对中实测.md`）。
> ⇒ **五档 `md5` 与 `content-sha256` 全变**（`y` 是**被绘制的载荷字段**、不是 note ⇒ 两个摘要都该变；
> 若只有 md5 变而 content-sha 不变，才说明「只动了措辞」—— 本轮两个都变，正是预期）。
> **上表五行与本节末「第 13 批重钉」表已是本轮现行值。**
> 闸门同步：`m02`【F 的 `MODE_SPEC`】／`m06`（`MODE_NEW_SPEC` ＋「`_glow`/`_hit` 同框；`_tx` 同 x/w/h 且
> `y = _glow.y + 8`」判据）／生成器 `mode_entry_violations()`（同判据 ＋ 新增**变异 D**：
> 把 `_tx` 挪回 y25 必须被检出）。

> ★★ **第 15 批重钉（`ISSUE-20260930-02` · 2026-09-30 · 章节详情；含第 2 轮用户裁定 5/6/7）** ★★
> ⚠ **本节为「第 15 批当时的现行值」，已被下方「第 16 批重钉」取代**（第 15 批值一律作废，此处仅作历史留痕）：
>
> | 预设 | 元素数 | md5 | content-sha256 |
> | --- | ---: | --- | --- |
> | `screen1` | **272** | `a41ffd351cc9fe5a5b6fda1b570b5c53` | `bfbbe5a33537108f0961adddc3db994e5ebff8fe491bd04a7f38b851eb2a5fb6` |
> | `screen2` | **116** | `affd6dfc218b52fcdd0d17b4287e9f61` | `ce17b7955cfd69f1af95b8526b650a0b979db4b2c75a9ac6882e7c18e22e642b` |
> | `ref150` | **95** | `8a22d83cda1a8a253f6acd96a4b887e7` | `15e50f1c4a8aadd410319173d41ab7f746c883656961f3a3970a91f6262f2c80` |
> | `states` | **109** | `e31ebb37bc6a1f5dfcdfc19b82fcf9bd` | `97fb4fd8a87537614b05f690969338f776ab6dda9208bd88467650737237d5fe` |
> | `frag` | **128** | `879f264ad69c1c6d9c288a658b01f138` | `b581b226459b48a2bac0687765b375b91bab51c0e3e55d74a0a9c7145afc2cd3` |
>
> 五档各 **＋10 元素**（加号按钮 2 ＋ 详情浮层 8〔基座 6 ＋ 关闭件 2〕）；外壳 **40 → 50**、图内容层 **222 不变**；
> **17 屏合计 1391 → 1401**。⇒ **五档的 md5 与 content-sha256 全变**（几何与元素集合都变）。
> ★ **本批的作废值**：第 13 批五组（`7fa46f2f…`／`642cf515…`／`5655e08a…`／`d84014c5…`／`a1b92d6b…`）与
> **第 15 批首轮的 `74e2fa73…`／`a8c515a6…`／`d018e36b…`／`9277db40…`／`19904e95…`**（浮层 6 件、625/652 几何）
> **一律作废**。逐条机检：`m06`（`DECLARED_NEW_IDS` 追加 2 件关闭件、8 件描述随几何更新）、
> `m03`（`states` 元素数 **107 → 109**）、`m01`／`m03`（`SHELL_FLAG_EXEMPT` 逐字等于生成器 `STATIC_FLAG_EXEMPT`，各加 2 件）、
> `gen_flow_layout.py --selfcheck-intro-overlay`（变异自证 **6 → 9 条**）、
> `工具/test_delivery_index_sync.py`（《UI组_交付总纲.md》5 张表按 `--report` 回填）、
> 实机巡演（`★INTROOPEN★`／`★INTROCLOSE★`／**`★WRAPELLIP★`**，见 `_工作\ISSUE-20260930-02_章节详情\证据\E4_自检报告.md`）。

> ★★ **第 16 批重钉（`ISSUE-20260930-06` · 2026-09-30 · 番外独立层改纵向流水；用户裁定 5）** ★★
> **现行五组金标**（`工具\gen_flow_layout.py` 的 `GOLDEN`，`--refresh-golden` 实跑真值；上方表格五行同值；
> ⚠ 已含 **一审后返修**「冻结 §7.2 溢出格 `visible_default:false`」的第二次重钉值）：
>
> | 预设 | 元素数 | md5 | content-sha256 |
> | --- | ---: | --- | --- |
> | `screen1` | **296** | `1c6496e7b3efff589c4fd09c613e3ef3` | `99b15674e782dc66b05b2ebd6807fbe370546afda6adffa90cf11190e7799884` |
> | `screen2` | **116** | `3cd4e92d91d197d2847e30442124860c` | `ce17b7955cfd69f1af95b8526b650a0b979db4b2c75a9ac6882e7c18e22e642b` |
> | `ref150` | **95** | `43a5b40ab3bea83d57cbd053c895a535` | `15e50f1c4a8aadd410319173d41ab7f746c883656961f3a3970a91f6262f2c80` |
> | `states` | **109** | `74392cc9b5d3f632cc693afa95b24a89` | `97fb4fd8a87537614b05f690969338f776ab6dda9208bd88467650737237d5fe` |
> | `frag` | **128** | `4ed7585a16ea700343328a962a9eb95a` | `b581b226459b48a2bac0687765b375b91bab51c0e3e55d74a0a9c7145afc2cd3` |
>
> **本批只有 `screen1` 的元素集合变**：**＋24 件**（G6 的 13–20 格 ×3〔image/text/hit〕）⇒ `screen1` **272 → 296**、
> **图内容层 222 → 246**、**独立层节点 135 → 159**、**外壳 50 不变**；五档 **296 / 116 / 95 / 109 / 128**；
> **17 屏合计 1401 → 1422**（★ **D-01 2026-10-01**：`title` 18→24 ⇒ **现行 1428**）（★ 冻结 §7.1 勘误 4 定第 16 批终值 **1422**；中间值 **1425** ＝「flowchart 单项 +24」未减
> config 的 −3，**只作历史留痕**；`flowchart` **296** 与 `config` **467** 两个单项值不变）。
> **素材零新增**（1359 件 / 100,604,112 B 不变）。
> ⇒ `screen1` 的 md5 与 content-sha256 **都变**；其余四档**只有 md5 变**（**屏 note 措辞共用** ⇒ md5 变、
> 元素与连线未动 ⇒ content-sha256 **逐字不变**，正是两个摘要并存要分辨的形态）。
> · **裁剪口径（本批唯一的判据放松 · 有意偏离 §九 裁决 5）**：独立层元素只要求「`x` 完整落视口 **且** `y ≥ 视口顶 190`」
> ⇒ **允许纵向溢出**（下沿可超视口底 1017 / 画布 1080；第 6 组第 5–7 行 y＝1054/1246/1438、末行下沿 1503）；
> **主干节点判据一字未改**；层固定件（`_title_bg`/`_title`/`_back*`）**位置不变、不随滚**（可滚对象＝节点行）；
> **未滚到位时 y > 1017 的行不可见＝预期**，不得据此报缺件（呈现归编程组的独立层纵滚）。
> · ★★ **冻结 §7.2 可见性契约（一审后返修 · vision 打回的直修项）** ★★
>   起因：G6 第 5 行盒 y1054–1119 **无底部裁剪** ⇒ 画面底部 y1062–1080 露出半截节点与文字字头
>   （vision 实测 **7280 px**），且压在底部横移条（y1018–1043）之下。
>   修法：**元素盒下沿 `y + h > 视口底 1017` 的行**，其**全部三件**一律 **`visible_default: false`**
>   ⇒ **数据完整产出、默认不画**；**纵滚实现时置真**（属编程组）——与 config 屏既有「`visible_default:false`
>   ＝ 预留下但默认不画」**同源用法，不新造机制**。**只加字段、不减元素**（仍 296）。
>   ⇒ **产出 53 格 ＝ 数据完整；默认可见 12 格（4 行）；其余 8 格需纵滚置真**（以**唯一有溢出的第 6 组**为准；
>   全屏默认可见 ＝ G1–G5 共 33 格 ＋ G6 前 4 行 12 格 ＝ 45 格）。`--frag-report` 另报「默认可见格数 /
>   需纵滚置真格数」，「产出」列仍按**元素存在**计。落盘前**双向**自检（溢出却默认可画 / 未溢出却默认不画 ⇒ 拒）。
> · 逐条机检：`m02`（`check_frag()` 改 `rows=ceil(章数/3)` 口径 ＋ **变异自证**：删一格 / 几何偏 1px 各须被检出；
> 另加 **B3 §7.2** 对 `screen1` 的 G6 断言 24 件溢出件 `visible_default:false` ＋ **双向变异自证**）、
> `m06`（`DECLARED_NEW_IDS` 追认 **24 件新增**（含 `visible_default:false`）＋ `check_new_frag_cells()`
> 逐件**几何追认**、`visible_default` 断言、「G6 == 20 格 / 24 件 false」反向断言 ＋ **两条变异自证**）、
> `--frag-report`（逐组「未产 = 0」＋虚拟内容高度＋需纵滚的行清单＋默认可见/纵滚置真格数）、
> `--selfcheck-delivered`（金标反向自证，真值随 `--refresh-golden` 变）。
> ★ **本批的作废值**：第 15 批五组（`a41ffd35…`／`affd6dfc…`／`8a22d83c…`／`e31ebb37…`／`879f264a…`）
> 与第 16 批**首轮**五组（`26c5413f…`／`a2118ffb…`／`9083daab…`／`8966a1aa…`／`9150e17d…`，未含 §7.2 字段）
> **一律作废**。

  **落盘前自检**：写默认屏文件时，产出摘要必须 == 该预设的金标，否则**拒绝落盘并报错**
  （`--refresh-golden` 重钉；`--selfcheck-delivered` 是它的反向自证）——
  用来根治本工程反复出现的「生成器重跑即静默回退」缺陷（`build_backlog`/`build_config`/`build_music`/`build_dress` 同族）。
  金标同时记 `md5`（整文件）与 `content-sha256`（**剥掉全部 note 后**的规范化摘要，对措辞编辑免疫，
  用来分辨「这次变的是 note 还是内容」）。
- **文字参数（修正轮 V2，用户裁决）**：字号 **19px**、行距 **1.0**（元素级 `line_spacing`）、文字盒 **240**（`x_node+28` 居中）、`max_lines 2`。
  **四判据**（判据对准底图的**可见实体面** rows 8..55 ＝ 48px，**不是元素高 65**）：
  A 首行上留 ≥5px ｜ B 末行下留 ≥5px ｜ C 行墨迹 ≤263px（可见实体面宽实测 ≈282 ⇒ 左右各留 ≥9px） ｜ D 712/712 零截断。
  712 条实测最小值：**上留 5px / 下留 5px / 最宽行 228.0px / 截断 0**（★ 订正：原写「最宽行 255px」＝第 10 批收紧前的旧读数，**已作废**）；19px 是这四条下的**字号上限**（两行需 `2×lineH ≤ 39`，而 `lineH ≥ size`）。
  生成器把它做成**落盘前自检**（不达标即拒绝落盘），可用 `--text-fit-report` 复跑。
- **已知排版现象（非缺陷）**：19px 下每行可容 12 字 ⇒ 11–12 字标题变**单行**；孤字只出现在 **≥13 字**标题上。
- ★★ **第 9 批 · 「已读对勾」不变量 ＋ `TITLE_HARD_BREAK` 硬断行表**（`ISSUE-20260928-02`；
  由 vision 复核第 8 批的 `_read` 对勾后提出的**数据侧最后一处修复**）★★
  **不变量（落盘前自检，违反即拒绝落盘）**：所有含文字节点（**主干 `fc.node.*_tx` ＋ 独立层 `fc.frag<G>.<NNNN>_tx`**）
  的 **首行墨迹左缘 ≥ `x_node + 30`**。
  - 推导：已读对勾 `fc.node.<NNNN>_read` = 20×20 @ **`(x+10, y+12)`**（距可见实体面左上内缘各 4px）
    ⇒ 其**右缘在节点相对 +30**；标题文字盒左缘 = `x_node + 28`（盒宽 240、`x = x_node+(296−240)/2`）、
    标题**居中**渲染 ⇒ 首行墨迹左缘 = `28 + (240 − w0)/2`。两线相叠即压住首字左边。
  - 等价判据：**首行墨迹 ≤ 228px**（第 10 批收紧前为 ≤236px）；实测 **712 条违规 0、最紧 +34.00**（`s01_02b`）。
  - 复算口径：与四判据同一把尺（`width_fn(TEXT_SIZE)`＝PIL `msyhbd.ttc`；`ui_theme_wrap` 按 `\n` **分段**各自折行，
    与引擎 `uiThemeWrap` 同式）。
  **`TITLE_HARD_BREAK`（20 条，生成器常量表：第 9 批 12 ＋ 第 10 批 8）**：在**自然断点**处插硬换行 `\n`
  （引擎与生成器都把 `\n` 当硬换行 ⇒ 两端一致）。断点优先级：

  | 级 | 断点位置 | 本表实际取值（例） |
  | --- | --- | --- |
  | **A**（优先） | **全角开括号 / 引号 / 波浪之前**（`（`「“」「～」）＝ 题名 ＋ 括注/副题两行 | `62_1b`「无论何时·棱镜」/「（性的意义上）」；`s03_06d1`·`s03_06d2`「交错之箭的颜色与去向」/「（Ｎ）」·「（Ｃ）」；`02_01a`「“邂逅」/「～对抗：千岁鹫介～”」 |
  | **B** | **句读标点之后**（`、`——它本身是行首禁则字符，引擎本来也只能断它之后，此处只是**显式化**） | `s01_08f`「ＩＮ ＴＨＥ ＲＯＯＭ、」/「ＡＴ ＮＩＧＨＴ」 |
  | **C** | **拉丁词界（空格）** | `s03_03i`「ＵＮＤＥＲ ＴＨＥ 」/「ＳＭＯＫＩＮＧ ＳＫＹ」 |

  - 约束：① 断后**两行墨迹都 ≤ 230px**（实测最大 202 ⇒ 左缘 ≥ +33，给对勾留 ≥4px）；
    ② 第二行**不得以行首禁则字符开头**（A 类断点是有意的例外——括注独占一行）；
    ③ 每段单独折行必须**恰好 1 行**（否则引擎会再折 ⇒ 可能截断）；
    ④ 表内每条的拼接必须**逐字等于**源文本（`title_sample()` 内 `assert` 守住 ⇒ 源语料一改即报「表已过期」）。
  - **成因**（为何会有第 9 批这 12 条）：字符串**末尾是行首禁则字符**（如 `）`）⇒ `ui_theme_wrap` 把它强行并入本行
    ⇒ 单行 **247–255px（> 盒宽 240）**，左缘低至 **+20.50**。
  - **交付样例影响**：`screen1` 里只有 **`fc.frag6.0007_tx`（script `62_1b`）**受表影响（旧单行 255px ⇒ 新两行 122/133px）；
    其余 11 条不在交付样例四档（`screen2`/`ref150`/`states`/`frag` 的 `content-sha256` **逐字不变**）。
  - **机检**：`python 工具\gen_flow_layout.py --title-check-report`（不变量实测 + 违规清单）／
    `--selfcheck-title-break`（**变异自证**：删一条硬断行必越线、表清空须 ≥ 表内条数 ⇒ 非恒真）。
- ★★ **第 10 批 · 不变量收紧 `+30 ⇒ +34` ＋ 「零间隙边界簇」8 条补硬断行**（`ISSUE-20260928-04`；
  **用户 2026-09-28 看完实机对照图后裁决**）★★
  - **起因**：第 9 批只保证「与对勾零重叠」（≥+30），仍有 **8 条**标题余量只有 **0–2px** ——
    `42_3`/`42_4`/`s01_09c4`/`s02_10b`/`s04_03f1`/`s04_03f2`/`s04_03f3` 恰 **+30.00**（首行 236px）、
    `s03_17a` **+32.00**（232px）。其中 **4 条本来就是「236px 长行 + 2–3 字尾巴」的难看折行**，
    **`42_4` 还把 `ＦＡＬＣＯＮ` 从中间切断**（`ui_theme_wrap` 按**字符**折行、不认拉丁词界）。
  - **实机对照**（判据来源）：`run_autotour.bat frag4` 两变体帧 ⇒
    `_工作\ISSUE-20260928-03_标题边界簇\证据\对照_长标题与已读对勾_实机.png`（读数同目录 `读数.tsv`）：
    现状 `42_3` 间隙 **1px**、`42_4` **5px**（且 `（ＦＡＬＣ/ＯＮ）` 断词）；补断行后 **65px / 55px** 且两行均衡。
    ⚠ 该对照的**对勾是注入的「未来态」**：`_read` 只在主干节点产生（生成器里即 `fc.node.%s_read`），
    番外独立层按裁决 4 不写运行态 ⇒ 当前实现下对勾与这些长标题**不可能同框**；探针把对勾挂在**层旗标**上
    （巡演真实 flag 机制驱动）以呈现未来态。
  - **处置**：`TITLE_HARD_BREAK` **追加 8 条**（断点＝「（」前；「·」「，」后 —— 「，」属行首禁则，
    引擎只能断在其后）＋ 常量 **`TITLE_CHECK_GAP = 34`**（＝对勾右缘 +30 再留 **≥4px**）；
    等价判据随之变为**首行墨迹 ≤ 228px**。
  - **收紧后全量**：`--title-check-report` ⇒ **712 条 / 断行 20 条 / 违规 0 / 最紧 +34.00（`s01_02b`）/
    两行条数 105 / 全量最宽行 228.0px / 截断 0**；`--selfcheck-title-break` ⇒ 真表 0 违规、
    删 1 条必越线、**清空表 20 条违规**。
  - **交付样例影响**：这 8 条里**只有 2 条在交付样例里** ⇒ `fc.frag4.0008_tx`（`42_3`）与
    `fc.frag4.0009_tx`（`42_4`）的 `sample` 各插一个硬换行（元素数 289 不变、连线 13 条几何全同）；
    已在 `m06_delivered_sample_ledger.py` 的**基线总账**登记（该档三轮合计有意变更 3 处）。
- **番外入口列整列摆进图表视口**（收尾轮裁决 5，`--entry-side left|right`）：组名标签 333 宽 > 视口两侧空隙（各 282）
  ⇒ 只能整列占一条竖带，道带在**剩余宽度**里居中。本屏**全部产出元素**（不含 §一 冻结的静态件）
  整体落在 `x∈[60,1295]、y∈[190,1017]`，生成器对此**自证并在越界时拒绝落盘**。
- **番外组名中文化（★ ISSUE-20260927-06 新增）**：`fc.label.<NNNN>_tx` 的 `sample` **不再直接取**
  `spine.json` 的 `side_stories[].group`（该字段是我方组名元数据、只有日文/中文混写、**无 `group_cn`**），
  而是取 **`工具\gen_flow_layout.py` 的 `GROUP_CN_MAP` → `group_cn()`** 处理后的值：
  **只映射需要改的组，未命中者原样透传**；逐条来源注记（通用术语表行号 / 同语料既有译法 / 本次新定理由）
  写在该常量上方的注释里，并在元素 `note` 里回写「原文组名 + 依据」。
  **`spine.json` 属资源组数据，本模块只读不改** ⇒ 术语裁决只落在生成器这一处（改一行即改文案）。
  映射后仍有假名残留时生成器打印 `★ 残留日文假名 n 组`（自警，不阻断）。
  现行 3 条映射：`おっぱい系列`→`胸部系列`（援引通用层 `术语表.md:171` 叙述者轨）／
  `おれつば剧场`→`没翅剧场`（同语料 `title_cn` 5/5）／`おまけ`→`附赠`（两层术语表未收录，按通用层 `SKILL.md` §四 新定）。
  两端绘制与量测的都是 `sample`（`krkr/game/ui_theme.tjs` 的 `uiThemeRenderText` ↔ `复刻/replica.js`）⇒ 一处改、两端生效。

### `dynamic` 与 `anim`

| 字段 | 含义 |
| --- | --- |
| `"asset": null, "dynamic": "<name>"` | **运行期由调用方填充**的层。`story_background` = 当前场景背景；`story_chara` = 当前立绘；`slot_thumb` = 存档缩略图；**`flow_scene_frames` = 流程图右栏「大播放窗」要按顺序播放的该章节游戏内画面**（★ `ISSUE-20260929-02` 新增，用在 `screens/32_flowchart.json` 的 `fc.play_view`）。两侧渲染器都必须**保留该层并在未填充时画占位底色**，不得跳过 |
| `"content_box": "@auto"` | 该层的 x/y/w/h 由根 `content_boxes[源代号]` 决定（`@auto` 表示运行期定源） |
| `"anim": {"mode":"blink","period_ms":700}` | 循环动画。目前仅 `blink`（透明度 0/255 交替）；`mode":"scroll_x"/"scroll_y"` 预留（音乐条/长图滚动，见 美术规范 §6.2 R3、§6.3 H1–H4） |

### 元素通用字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | **全局唯一**，形如 `dlg.window`、`save.slot_list`。krkr 侧 `UiLayout.get("dlg.window")` 按此取 |
| `kind` | string | 见上表 |
| `z` | int | 绘制层序（小在下）。krkr 侧映射为子层 `order`；HTML 侧映射为 CSS `z-index` |
| `visible_default` | bool | 默认是否可见（krkr 子层 `visible` 默认 false，**必须显式置真**，见 `引擎工作原理.md`） |
| `vis_flag` | string | **M1 新增**（可选）：屏级状态 flag 名 —— 该元素仅在该 flag 取值满足 `vis_when` 时可见/可点。与 `vis_when` **成对出现**；判定语义见 §四「屏级状态 flag」 |
| `vis_when` | string | **M1 新增**（可选）：需要的取值；**`"*"` = 该 flag 非空即显示** |
| `flow_state` | string | **★ 第 2 步新增**（可选，目前只有 `screens/32_flowchart.json` 的 `fc.node.<NNNN>` 用）：该节点的**运行态**，取值 `"locked"`（未解锁）／`"available"`（可前往）／`"visited"`（已读）／`"current"`（当前）／`"new"`（已解锁未读）。**缺省（不写）＝ `"available"`** ⇒ **交付样例不写该字段时外观与文件内容一律不变**。**它只是数据**：`flow_state=="current"` 时由**两端程序化画环**（krkr `layerExDraw` ／ HTML canvas：圆角矩形描边 r=16、线宽 3、色 `@palette.node_current`、矩形＝节点元素矩形内缩 1px，**不产元素**）；`locked` / `new` / `visited` 的叠加件是**独立元素** `fc.node.<NNNN>_dim` / `_new` / `_read`，由 `vis_flag:"fc.state.<NNNN>"` + `vis_when:"locked"/"new"/"visited"` 控显隐（运行期由 `flow_layer` 动作一族改写 flag 值）。★ **`ISSUE-20260928-03` 修正/新增**：`_dim` 由 `rect` 改 **`image`**（按节点种类取压暗件、与底图件同几何同 `nine`、强度由 `opacity` 控）；**新增 `_read`**（已读绿对勾，用户裁决「丙方案」）；**`current` 不加对勾**（只留金环）。**示例档**：`--preset states` |
| `line_spacing` | number | 可省。**元素级行距系数**（行盒高 = 正文字号 × 该值；引擎式 `lineH = max(size, floor(size×系数))`）。缺省 ⇒ 用全局 `fonts.line_spacing.body`（当前 1.4）。**两端消费点**：krkr `krkr/game/ui_theme.tjs` 的 `uiThemeElementSpacing()`（由 `uiThemeApplyFont()` 调用、经 `uiThemeLayoutText()` 参与折行与定位）；HTML `复刻/replica.js` 的 `lineSpacing()`（`font.size × 该值` → `style.lineHeight`）。★ 流程图节点标签用它把行距从 1.4 压到 **1.0**，以便两行塞进底图的**可见实体面**（48px）。 |
| `nine` | object | 九宫格边距 `{"l":13,"t":5,"r":13,"b":5}`；**只在 `image` 上有效**，缺省表示不切片 |
| `opacity` | int 0–255 | |
| `color` | string | **`"@palette.<key>"` 引用**或 `"#RRGGBB"` 直写。**优先引用色板** |
| `note` | string | 中文用途说明（必写，供人读与清单生成） |
| `source` | string | **素材来源全路径**（如 `资源组\美术统一\系统UI\meswin.png`），必写，供溯源与清单 |

### `text` 附加字段

```jsonc
"font": { "size":24, "bold":false, "color":"@palette.text_primary", "shadow":true,
          "shadow_color":"#000000", "shadow_ofs":2,
          "outline":true, "outline_color":"#000000", "outline_width":2,
          "faces": ["DejaVu Sans Mono","DejaVu Sans"] },   // 可省：逐元素字体覆盖
"align": "left|center|right",
"valign": "top|middle|bottom",
"wrap": true, "max_lines": 3,
"sample": "演示占位文本（非剧情）"
```

#### `font.*` 阴影 / 描边三组字段（**渲染层，不参与布局**）

| 字段 | 类型 | 缺省 | 说明 |
| --- | --- | --- | --- |
| `shadow` | bool | `false` | **单向 offset 阴影**（既有机制）。真时用 `shadow_color` 在 `(+ofs,+ofs)` 方向画一层 |
| `shadow_color` | hex / `@palette.*` | `@palette.shadow` | 阴影色 |
| `shadow_ofs` | int px | `0` | 阴影偏移（x=y=该值；krkr 侧另把 shadowwidth 设为 `ofs+1`） |
| `outline` | bool | **`false`**（默认关，不影响任何既有元素） | **★ M38 新增：四向描边**。真时用 `outline_color` 在 **8 个方向**各画一次同文本，**最后画正文** |
| `outline_color` | hex / `@palette.*` | `@palette.shadow` | 描边色 |
| `outline_width` | int px | `1` | 描边边宽（= 8 个方向的偏移量大小） |

**★ 铁律三（M38）：`outline*` 只影响渲染，绝不参与布局。** 换行 / 截断 / 对齐 / 定位
（krkr `uiThemeWrap`｜`uiThemeLayoutText`，HTML `-webkit-line-clamp` / `e.w`）**一律只按正文**字形计算，
与既有 `shadow` 同款「渲染层的事」。加描边**不得**改变任何元素的行数与断行位置。

**★ 改一处须改两处（两端同实现，方向/宽度必须逐项一致）**

| 端 | 文件 | 落点 |
| --- | --- | --- |
| krkr | `krkr/game/ui_theme.tjs` | `uiThemeApplyFont()` 解析三字段 → `uiThemeDrawLine()` 调 `uiThemeDrawOutline()`（方向表 `UIThemeOutlineDirs`，缺省宽 `UIThemeOutlineDefaultWidth`） |
| HTML | `复刻/replica.js` | `textOutlineShadow()`（8 条 `text-shadow`，方向表与 krkr **同序同向**）→ 由 `textShadowAll()` 合成后交给 `buildText` / `buildHit` / `buildList` |

方向表（两端同序）：`(1,0) (-1,0) (0,1) (0,-1) (1,1) (-1,1) (1,-1) (-1,-1)`，偏移量 = 方向 × `outline_width`。
`outline` 与 `shadow` 可共存（CSS 侧 `textShadowAll` 会拼接），但**同一元素不建议同时开**
（双重发虚）；对话框屏即按用户裁决「只开描边、关掉 shadow」，见 `screens/10_dialog.json`。

> **`font.faces`（逐元素字体覆盖，2026-09-19 新增）**：给出则**优先于**根 `fonts.fallback_faces`，按顺序取**系统确实存在**的第一个 face（krkr 侧用 `Font.getList(0)` 查表，HTML 侧直接用 CSS 回退链）。
> 用途：某个屏要用特定字体（如标题菜单用 `DejaVu Sans Mono` 粗体），而全局链仍须保持中文字体。
> ⚠️ **`DejaVu Sans Mono` 不含 CJK 字形**——只可用于**拉丁字符**的界面（原版标题菜单本就是英文 START/LOAD/…）。中文字符用它会出现豆腐块，必须走中文字体。

### `hit` 附加字段

```jsonc
"action": "open_save",     // 动作名，由编程组/复刻层实现；见 §六 动作表
"label": "存档",           // 按钮中文标签（引擎绘制）
"state_assets": { "normal":"ui/…png", "hover":"ui/…png", "pressed":"ui/…png" }   // 可省
```

---

## 五、屏归属（写权限表）

| 屏 id | 中文名 | 归属 | 文件 |
| --- | --- | --- | --- |
| `title` | 标题画面 | **主代理**（样板） | `01_title.json` |
| `dialog` | 对话框/名字框/系统条/选择肢 | **主代理**（样板） | `10_dialog.json` |
| `confirm` `loading` `backlog` | 确认框/加载/回想 | M5 | `2x_*.json` |
| ~~`sysmenu`~~ | ~~系统菜单~~ | ~~M5~~ | ~~`20_sysmenu.json`~~ | **★ M45（2026-09-23）已废除**（用户裁定「现在废除『系统菜单 sysmenu』页，因为我们已有药丸按钮系统」）：屏文件 / `_index.json` 条目 / 巡演白名单 / 两端活引用 / 文档屏清单全清（19 → **18 屏**）；系统功能由右端竖排快捷条 `quickbar` 承担；屏数据快照归档 `_工作\M45_旧素材归档\`。**动作 `open_sysmenu` 保留**（语义自 M2 起＝「展开竖排快捷条（不钉住）」） |
| `save` `load` | 存档 / 读档 | M5 | `2x_*.json` |
| `config` | 配置 | M5 | `2x_*.json` |
| `gallery` `music` ~~`ending`~~ | CG 画廊 / 音乐鉴赏 / ~~片尾~~ | M5 | `2x_*.json` | **★ ISSUE-20260928-07（2026-09-28，用户裁定）：`ending`（片尾·STAFF/歌词）屏已整体删除**（用户：**未来改用一段视频代替**）：屏文件 `29_ending.json` 与 `_index.json` 条目已移除（**18 → 17 屏**）；屏内 7 件元素（`ed.bg` / `ed.shade` / `ed.char` / `ed.staff` / `ed.lyric_bar` / `ed.lyric` / `ed.hit_skip`）随之移除；**素材 `x_ui_ending_bg.png` / `x_gen_ed_char.png` 保留原处**（屏独占，作将来做视频的参考/来源） |
| `chapter` | 主线·章节选择 | M4 | `3x_*.json` | **★ M43（2026-09-23）已删除**（用户裁定「彻底删除主页·章节选择」）：屏文件 / `_index.json` 条目 / 巡演步表 / 两端代码 / HTML 复刻页全清；剧情入口改由 `flowchart` 屏的 `fc.jump_hit`（动作 `flow_enter`）承担 |
| ~~`fragment`~~ | ~~番外（Fragment）选择~~ | ~~M4~~ | ~~`31_fragment.json`~~ | **★ ISSUE-20260928-06（2026-09-28，用户裁定）已整体删除**：屏文件 `31_fragment.json` 与 `_index.json` 条目已移除（**19 → 18 屏**）；番外 6 组内容已由**流程图屏 `flowchart` 的独立层**（`action:"flow_layer"` ＋ `layer:"frag1".."frag6"`）承载 —— 实测原 Fragment 页 40 格 **⊂** 流程图层 45 格、**文案 40/40 一致（**37 格字节完全相同**；另 **3 格**在流程图侧含**我方注入的硬断行** `\n`：`42_3` / `42_4` / `62_1b` —— 无字符增删）**（删屏零内容丢失）。**动作 `open_fragment`/`fragment_enter`、素材 `x_gen_fragpage.png`、数据 `fragments`、模块 `ui_fragment.tjs` 一律保留**（用户裁定「只删屏、保留动作/素材」） |
| `flowchart` | 剧情流程图 | M4 | `3x_*.json` |
| `sysicons` | 右键图标浮层（9 功能图标） | **M13** | `33_sysicons.json` |

**M4 的 `fragment`/`flowchart` 与 M5 的系统屏必须在同一 `screens/` 目录下用不同文件前缀**（`3x_` vs `2x_`），互不覆盖。（★ ISSUE-20260928-06：`fragment` 屏已删除 ⇒ `3x_` 前缀现由 `flowchart` 使用。）

---

## 六、动作名表（`hit.action` 取值，**跨组契约**）

| action | 含义 | action | 含义 |
| --- | --- | --- | --- |
| `game_start` | 开始新游戏 | `open_save` | 打开存档 |
| `game_continue` | 继续（读最近存档） | `open_load` | 打开读档 |
| ~~`open_chapter`~~ | **★ M43（2026-09-23）已移除** —— `chapter` 屏整体删除，无数据再引用 | `do_save` / `do_load` | 执行存/读第 N 槽（`slot` 字段） |
| `open_fragment` | 打开番外选择 —— **★ ISSUE-20260928-06（2026-09-28，用户裁定）**：所指向的 `fragment` 屏**已整体删除**（番外改由流程图屏独立层承载）⇒ 本动作**保留**但**不再指向任何屏**（与 `sysmenu` 废除后 `open_sysmenu` 同口径）；krkr `ui_screens.tjs` 的屏映射与 HTML `replica.js` 的 NAV 条目**均保留** | `open_config` | 打开配置 |
| `open_gallery` | 打开 CG 画廊 | `open_backlog` | 打开回想 |
| `open_music` | 打开音乐鉴赏 | `open_flowchart` | 打开流程图 |
| `open_title` | 返回标题 | `quit_game` | 退出游戏 |
| `open_sysmenu` | **展开右端竖排快捷条（不钉住）** —— ★ **M45 起本名不再指任何屏**：`sysmenu` 屏已废除，动作语义自 M2 起即为「展开竖条」（`uiQuickbarOpen()` ／ `expandQuickbar()`），数据里已无元素指向它 ⇒ 现为**编程入口**（深链 / 附加层里 `action` 留空的 hit 兜底） | `open_flowchart` | 打开流程图 |
| `skip_on` | 快进 | `auto_on` | 自动播放 |
| `hide_window` | 隐藏/显示窗口 | `close` | 关闭当前层 |
| `page_prev` / `page_next` | 翻页 | `select_choice` | 选择第 N 项（`index`） |
| `fragment_enter` | 进入某番外（`fragment_id`）—— **★ ISSUE-20260928-06（2026-09-28，用户裁定）保留**：`fragment` 屏删除后成**无发出方的死分支**（原先唯一发出方＝该屏 40 格热区），按「只删屏、保留动作」**动作本身保留**（HTML `dispatch` 分支亦保留） | ~~`chapter_enter`~~ | **★ M43（2026-09-23）已移除** —— 随 `chapter` 屏删除；「进入剧情」能力迁到 **`flow_enter`**（见下表） |
| `confirm_yes` | 确认框「是」 | `confirm_no` | 确认框「否」 |
| **`flow_enter`** | **★ M43 新增**：流程图屏「进入本章」按钮（`fc.jump_hit`）—— 取当前光标节点 `UIFlowCursor`：未解锁 → 只提示解锁条件、不进剧情；已解锁 → 标记已读 + 置当前节点 + 存状态，然后 `uiDialogReset()` + `uiScreenPush("dialog")`。**无可进入节点时给明确提示，不得静默**。两端实现：krkr `ui_flow.tjs::uiFlowEnterCurrent()` ／ HTML `replica.js::flowEnter()` | | |

**★ 第 2 步追加（2026-09-28 · `ISSUE-20260928-02` · 接口冻结 §二）**

| action | 含义 | 附带字段 |
| --- | --- | --- |
| **`flow_layer`** | **切换流程图屏的「主干 / 番外独立层」**：把屏级 flag **`fc_layer`** 置为 `layer` 的值并重绘／重算命中。取值 `"main"`（回主干）／`"frag1"`…`"frag6"`（进第 G 组独立层） | **`layer: "main" \| "frag<G>"`**（`hit.layer`，必带） |
| **`flow_replay_toggle`** | ★ **`ISSUE-20260929-02`（2026-09-29）新增（★ 第 3 轮起为**已定稿**名：两端均已实现其 flag 翻转与两键换显）**：流程图右栏大播放窗的**播放/暂停切换**。发出方＝**唯一**热区 `fc.pbkick_hit`（播放键 `fc.pbkick` 与暂停键 `fc.pbkick_pause` 同矩形、共用此热区）。**实现方式＝翻转屏级 flag `fc_replay`**：`"play"` ⇄ `"pause"`（初值 `"play"`），两键靠 `vis_flag:"fc_replay"` + `vis_when` **互斥显示**（§四 铁律一：不得靠 z 排序）。★ **语义边界：命中即派发（含 flag 翻转与两键换显），播放本身 —— 画面帧序列、时序、音频、与 `fc.play_view`（`dynamic:"flow_scene_frames"`）的填充 —— 一律留编程组接线，本批不声称已生效**（与 `bgm_playpause`、`replay_play:<行号>` 同口径）。用户 2026-09-29 指令 3 | — |
| **`flow_mode_main`** ／ **`flow_mode_frag`** | ★★ **`ISSUE-20260929-05`（2026-09-29）新增（**拟用名**，用户 AskUserQuestion 裁决）**：流程图屏**两枚模式入口**的切集动作 —— **「本篇集合」**（序章／本篇／After Story 并入）与 **「番外故事」**（原 Fragment）。发出方＝**唯一**热区 `fc.mode_main_hit` / `fc.mode_frag_hit`（与同组底光图 `fc.mode_*_glow`、文字 `fc.mode_*_tx` 同矩形 180×60；`state_group` ＝ `mode_main`/`mode_frag`，指针落在热区任意位置即点亮同组底光图的三态）。★ **语义边界：命中即派发；切集 / 筛选（哪些节点属于「本篇集合」、哪些属于「番外故事」）的行为留编程组接线，本批不声称已生效**（与 `flow_replay_toggle` 同口径）。数据侧：**目标集名不写在数据里**（本轮无字段）—— 编程组实现时按需增字段并回填本表。 | — |
| **`flow_intro_open`** ／ **`flow_intro_close`** | ★★ **`ISSUE-20260930-02`（2026-09-30）新增（第 15 批 · 冻结 §四）**：流程图屏**章节详情浮层**的开／关。**发出方** —— `flow_intro_open`：`fc.p_plus_hit`（加号按钮热区，右栏「说明」框内右上角 44×44 @1803,**618**）；`flow_intro_close`：`fc.intro_scrim_hit`（浮层压暗层的满幅热区 1920×1080，＝**点浮层之外**）**＋ `fc.intro_close_hit`**（浮层右上角关闭 × 的热区 **46×46 @1520,354**、`z 237` —— ★ **第 2 轮**用户裁定 5 新增，**与遮罩热区同一动作** ⇒ 两条关闭路径共用语义）。**语义＝纯 flag 翻转**：命中 ⇒ 把屏级 flag **`fc_intro`** 置 **`"open"`**（显示浮层 **8 件**）／置 **`"closed"`**（关闭浮层）—— **两端本批已实现**（与 `flow_replay_toggle` 同口径：krkr `krkr/game/ui_screens.tjs::uiActionDispatch` 的 `flow_intro_*` 分支 ＋ HTML `复刻/replica.js::doAction` 分支；判据＝直接置值、不做其它副作用）。★ **语义边界：UI 组只交「容器／几何／状态／动作名」；简介全文与章节标题的取数（按 `场景id`）、以及右栏摘要的截断内容，一律留编程组接线，本批不声称已接真实数据**（冻结 §四）。面板热区 `fc.intro_panel_hit` 的 `action` 为**空串＝吞掉点击**（点面板内不关闭，故不给它动作名）。 | — |
| 落点 | 进独立层：`fc.entry.<NNNN>_hit`（`layer:"frag<G>"`；★ **第 4 批 · 裁决 4：该热区只在该组的独立层确实在本档产出时才产**，未产出则入口件为纯占位、不可点）；回主干：**按组**返回键 `fc.frag<G>_back_hit`（`layer:"main"`；★ 第 3 批：原单件 `fc.fragback_hit` 已退场） | |
| 数据侧 | 无需新字段 —— 目标层名写在热区的 `layer` 上；**两端机制不得写死层名**，一律从数据读 | |
| 语义边界 | 本动作**只切层**（显示哪一组）；「哪些节点已读 / 已解锁」属运行态（`flow_state` + `fc.state.<NNNN>` flag，交编程组接线）。**独立层的纵滚/横移**不在本轮（冻结 §五 ⇒ 编程组） | |

**M13 追加（2026-09-20，右键图标浮层 · 主代理裁决）**

| 追加项 | 说明 |
| --- | --- |
| `open_sysicons` | 打开/收起 `sysicons` 屏（右键图标浮层）。**右键的入口**：krkr 侧 `startup.tjs` 的 `onMouseDown(x,y,mb,flags)` 里 `mb == mbRight` 时调用（`mbLeft=0 / mbRight=1 / mbMiddle=2`，见 `base/ScriptMgnIntf.cpp:65` 与 `visual/tvpinputdefs.h:20-26`；**注意与任务书原述「1=左 2=右」不符，以源码为准**） |
| `do_quicksave` / `do_quickload` | 快速存/读（不走槽位选择，直接写/读当前状态） |
| `prev_choice` | 返回上一选择点 |
| `replay_voice` | 重复语音 |

**M06 追加（2026-09-24 · `ISSUE-20260924-06_回想屏重排` · 用户指令「每一块里都要有跳转与重新播放」）**

| 追加项 | 说明 |
| --- | --- |
| `backlog_jump:<行号>` | 回想屏**逐块「跳转」**按钮（`item_buttons[].action`）。`<行号>` = **全局项序号**（含分页偏移），由 `%row%` 在派发前替换。**本轮语义 = 接口冻结/占位**：只做「命中 → 派发 → 日志/状态可见」（krkr `UIScrBacklogLastAct/LastRow/ActCount` ／ HTML `state.backlog`）；**真正的跳转生效留给编程组**（不得声称已生效） |
| `backlog_replay:<行号>` | 回想屏**逐块「重新播放」**按钮。同上；**引擎与复刻层都无音频代码**（M47 已登记）⇒ 音频接线留给编程组 |
| 行号非法 | 非「**非负十进制整数字面量**」⇒ 显式拒绝并打 `★M06ACT-REJECT★ <动作串> 行号非法`（**不得用宽松解析**：`uiFlowAtoi("abc")` 返回 0、`Number('')` 也是 0，会把错误静默吞掉；两端同判据：`uiScreenRowNumber` ／ 正则 `^\d+$`） |

**M1 追加（2026-09-24 · `ISSUE-20260924-08_鉴赏模式` · 主代理跨模块裁决「页签 = 切屏」）**

> 架构：鉴赏模式 = **四个页屏**（`gallery` CG ／ `music` BGM ／ `dress` 立绘 ／ `replay` 情景回想）
> ＋ **一个共享外壳浮层屏 `gal_shell`**（`layout/screens/39_gal_shell.json`，页签条 + 标题 + 返回键）。
> 四个页屏各自声明 **`"attach": "gal_shell"`**（照 `dialog` → `quickbar` 的先例，一个浮层挂多个承载屏）。
> 两端实现：krkr `ui_screens.tjs` 的 `uiScreenMapGalleryTab` / `uiScreenReplace` /
> `uiScreenGalleryShellSyncFor` ／ HTML `replica.js` 的 `galleryMapTab` / `doGalleryAction` /
> `galleryShellSyncFor`。**改一处须改两处。**

| 追加项 | 说明 |
| --- | --- |
| `gallery_tab_1..4` | 鉴赏四页签 —— **切到对应屏**（1→`gallery`、2→`music`、3→`dress`、4→`replay`）。语义 = **同级换屏**：把**栈顶**替换成目标屏（`uiScreenReplace` ／ HTML `renderScreen(target,{noHistory:true})`）⇒ ① 上一页**完全不在栈里**；② 入口屏（标题/对话框）仍在栈中 ⇒ 外壳「返回」（`close`）能正常回到入口；③ 离开的页其 list 的**页码与差分序号归零**（`uiScreenPageVariantClearFor`）。**守卫**：当前屏必须挂了鉴赏外壳（`attach == "gal_shell"`），否则显式拒绝 `★M08TAB-REJECT★`（不得静默顶掉别的屏）；未知页签同款拒绝。 |
| `gallery_page_prev` / `gallery_page_next` | 鉴赏**页内翻页**（当前屏**第一个可见 list** 的页码 ±1，clamp 到 `[0, pages-1]`）。无可见 list ⇒ `★M08PAGE-REJECT★`。CG 页 286 栏 / 24 栏每页 = 12 页即靠它。 |
| `gallery_prev:<行号>` / `gallery_next:<行号>` | 鉴赏**栏位内差分翻页**（`list.item_variants`，见 §四 该节）。`<行号>` = **全局项序号**（含分页偏移），由 `%row%` 在派发前替换。**边界 = clamp**。行号非法 ⇒ `★M08ACT-REJECT★`；当前屏无带 `item_variants` 的可见 list / 该栏留空 ⇒ 同款拒绝。 |
| 外壳页签高亮（**唯一一处派生**） | 外壳屏 `flags_default.gal_tab` + 四个指示件的 `vis_flag:"gal_tab"` / `vis_when:"<承载屏 id>"`；**派生出口** `uiScreenGalleryShellSyncFor(承载屏 id)` 装在屏栈 reset/push/pop 三处（与 M47 的 `uiScreenConfigFlagsInitFor` 同位置、同款），把 `gal_tab` 置成承载屏 id。页签值集**从外壳自己的数据导出**（`vis_when` 取值）⇒ 承载屏不在值集里则返回 0（**别的屏零副作用**）。**一元素一对 flag** 硬约束照旧。 |
| 可观测状态（机检用） | krkr `UIScrGalLastAct` / `UIScrGalLastRow` / `UIScrGalActCount` / `UIScrGalLastTab` ／ HTML `state.gallery = { lastAct, lastRow, count, lastTab, rejects }`。 |
| `attach` 复用四承载屏（**实测结论**） | 机制上 `attach` 只读**承载屏自己的数据字段**（`uiScreenAttachId(host)`），绘制（`uiScreenDrawAttach`）、命中（`uiScreenAttachClick`，优先级高于承载屏）、flags 合并（`uiScreenFlagsInitFor` 并入附加层 `flags_default`）三条路径**都不依赖 host 是 dialog** ⇒ **四个承载屏复用同一 `gal_shell` 可行**。实测证据：巡演 `kind:"galattach"` 四步（`★M08ATTACH★` 全 PASS：attach 指向正确、外壳元素可见数 14/17、**每个热区在自身中心被真实命中链命中且派发自身 action 5/5**）+ 四屏导图的页签条区域非背景占比 0.44–0.63；HTML 侧 `m08_html_shots.py` 的 `attach.*` 四断言同结论。 |

**M8 追加（2026-09-24 · `ISSUE-20260924-08_鉴赏模式` 一审打回修复 · R2/R3 + 主代理追认项）**

| 追加项 | 说明 |
| --- | --- |
| **屏级 `page_flag`**（★ R3 新增字段） | 承载屏可声明的屏级字符串字段：该屏**页码 flag** 的名字。**语义**：动作 `gallery_page_prev` / `gallery_page_next` 写完运行期页码（krkr `UIScrPage[listId]` ／ HTML `state.listPage[listId]`）后，把 **1 基页号**写进该 flag（krkr `uiScreenFlagSet(page_flag, ""+(页号))` ／ HTML `setFlag(page_flag, String(页号))` + `applyFlagVisibility()`，**必须在 `renderScreen` 之后写**——换屏会按 `flags_default` 重置 flag 表）；`uiScreenPageVariantClearFor`（HTML `galleryPageVariantClearFor`）归零时**同步复位 `"1"`**。**消费者**：屏内互斥页码文本（`vis_flag` = 该名、`vis_when` = `"1"/"2"/…`），如 CG 页 `gal.page_tx_01..11`（★ **ISSUE-20260929-01** 订正：实测 **11** 件）、BGM 页 `mu.pg_tx_1/2/3`（★ **ISSUE-20260929-01** 订正：本屏实为 **3 页**、三件页码文本；旧记 `_1/2` 为笔误。另：music 屏的页码行与翻页键本批按用户指令**整体下移 25px**（`gallery`/`replay` 仍在 `y939` ⇒ 「四页统一」被有意打破，勿修回））、情景回想页 `rp.pg_tx_1..4`（★ **ISSUE-20260929-01** 订正：实测 **4** 件）。**不声明的屏**（如 `dress`，无 list 无页码）不参与，机制零副作用。**名字一律从数据读，两端机制不写死**（krkr `uiScreenPageFlagOf` ／ HTML `pageFlagOf`）。**重进归零**（主代理追认项⑥）：挂壳屏在**新鲜进入**（krkr `uiScreenReset`/`uiScreenPush`/`uiScreenPop` 三路径 ⇒ `uiScreenGalleryEntryResetFor`；HTML push 形进入 / 首进 / `popEntry`）时页码、差分序号、页码 flag 一并归零；页签切屏（replace）不用再清——离开页已在 `gallery_tab_*` 处理器里清过。两端实现：krkr `ui_screens.tjs` ／ HTML `replica.js`（`pageFlagOf` 已导出 `UI_REPLICA`）。**改一处须改两处。** |
| **`list.scroll.pager`**（★ R4 新增字段，可省） | `scroll` 对象的可选布尔字段。**`"pager": false` = 明确关闭 HTML 侧 `replica.js::buildList` 的自动 `ui-list-pager`**（超容量时自动生成的「◀ n/m ▶」补充 chrome）；缺省 / `true` = 照旧生成（既有数据零变化）。**为什么需要**：krkr 端本无此 chrome —— 屏数据自带页码控件（三件式 `*_pg_prev/next/pg_tx*`）的 list 若不关，HTML 会多出第二枚页码控件，两端不一致。当前使用方：`27_gallery`（`gal.list`）、`28_music`（`mu.list`）、`38_replay`（`rp.list`）。 |
| **`bgm_*` 动作八键（拟用名）** | `28_music` 播放控制条的动作名：`bgm_mode_none` / `bgm_mode_one` / `bgm_mode_all` / `bgm_mode_rnd`（播放模式四键）、`bgm_prev`、`bgm_playpause`、`bgm_stop`、`bgm_next`（走带四键）＝**合计 8 键**（★ 2026-09-30 订正：本行原写「七键」而枚举 8 个，**旧值作废**；`UI组_交付总纲.md` §4.2 第 3 行与 `交付包校验收据.md` §⑧ 均为「8 枚」）。★ **语义边界：全部为 UI 组拟用名，音频接线留编程组** —— 本作引擎当前无音频代码（M47 已登记）⇒ 本轮只做「命中 → 派发 → 状态可见」，**不得声称已生效**；编程组若另定名，改 `28_music.json` 的 `action` 并回填本表。 |
| **`replay_play:<行号>`** | 情景回想页第二页动画栏的动作（`38_replay.json` 的 `rp.list` 第二页行）。`<行号>` = 全局项序号（含分页偏移，`%row%` 派发前替换；非法行号 ⇒ `★M08ACT-REJECT★` 同款拒绝）。★ **语义边界：派发即止** —— 只做「命中 → 派发 → 日志/状态可见」，**不声称播放已生效**；真正的动画播放接线留编程组。 |
| 页签 3 文字 = **「立绘鉴赏」**（主代理追认） | 外壳页签 3 的 `gs.tab3_tx` 用「立绘鉴赏」（**用户指令原文**）；参考作全称「立绘鉴赏模式」（`エクストラ共通/#stand` 页签，实测部件图内文字）登记为**来源事实**，不作要求。四页签文字：`CG鉴赏 / BGM鉴赏 / 立绘鉴赏 / 情景回想`。 |

**字段语义补充（M13）**

| 项 | 说明 |
| --- | --- |
| `nine: {l:0,t:0,r:0,b:0}` | **全零九宫格 = 「允许整图等比缩放」的合法写法**。`uiWidgetNine` 在 l=t=r=b=0 时只画中格（`operateStretch(x,y,w,h, src,0,0,srcW,srcH)`），其余 8 格因宽/高为 0 被跳过 ⇒ 效果等价于「整图缩放到目标矩形」。用途：素材物理尺寸大于版面可用空间、又不允许新增派生件时，用它在 layout 层做等比缩放（`verify_ui.py` 检查 [2] 对带 `nine` 的 image 只要求 `w ≥ l+r`、`h ≥ t+b`，全零恒成立）。**代价**：`w/h` 不再等于 PNG 实际尺寸，溯源需靠 `source`/`note` 写清原始尺寸与缩放倍率（`sysicons` 屏即此法，0.5×） |
| `image` 含**透明边距** | 当 PNG 自带大片透明边距（如 `x_gen_dialog.png` 1680×946，可见内容仅 y=173..745）时，`w/h` **仍写 PNG 实际尺寸**（校验 [2] 硬要求），靠 `x/y` 把**可见部分**摆到位；允许元素矩形越出画布（越出部分 alpha=0，无视觉影响）。摆放前必须先实测 alpha 包围盒（PIL `getbbox` 分阈值），把阈值与结论写进 `note` 与报告 |
| 全屏「点击空白关闭」热区 | 浮层类屏（`sysicons`）用「全屏 `hit`（`action:"close"`，低 z）+ 各控件热区（高 z）」实现：命中判定取**最高 z**，故点控件不会误命中全屏热区。`hit.label` 允许空串（不画文字） |

**M5 实测后追加（主代理 2026-09-19 裁决）**

| 追加项 | 说明 |
| --- | --- |
| `confirm_yes` / `confirm_no` | `confirm` 屏两键必须有**可区分的返回值**（原先都写 `close`，无法区分） |
| `list.slot_base` | **`list` 无法按项传槽号**。新增字段：`slot_base`（int），该项的槽号 = `slot_base` + 项序号。`save.slots_a` 用 `slot_base=1`、`slots_b` 用 `slot_base=5`，即 1–8 槽 |
| **允许空 action** | 动作表未覆盖的控件（`config` 的值控件、`backlog` 行点击、`music` 曲目行与播放控制 4 键）**允许写空串 `""`**，并在 `note` 标注「待编程组定义」。**不得臆造 action 名** |
| `list.labels` 可为空数组 | 当槽位文字改用独立 `text` 元素精确定位时（`save`/`load` 槽内缩略图与文字需分列），`labels` 允许为空数组。**编程组实现不得假定 `list.labels` 非空** |
| `veil` 压暗层 | 多屏需要「底图压暗」，用 `kind:"rect"` + `opacity` 字面量即可（`opacity` 是 int，不走色板，属合规写法） |

**M1 追加（2026-09-22，系统菜单快捷条 12 项 · `ISSUE-20260922-28`）**

| 追加项 | 说明 |
| --- | --- |
| `quick_pin` | 快捷条第 1 项「锁定」= **钉住**（固定展开、不再自动收起），由 M2/M3 实现（`qbar_pin` flag） |
| `next_choice` | 前进到下一选择点；与既有 `prev_choice` 成对（既有项只有「返回上一选项」） |
| 复用既有名 | 快捷条其余 10 项直接用既有动作名：`do_quicksave` / `do_quickload` / `auto_on` / `skip_on` / `prev_choice` / `open_backlog` / `open_flowchart` / `open_config` / **`open_save`** / **`open_load`** —— **不新增同义名**。 |
| `quick.hit_save` / `quick.hit_load` = `open_save` / `open_load` | 这两项是「**打开**存/读档画面」（**修复 B**，2026-09-22）；原先误用 `do_save` / `do_load`（那是「执行存/读第 N 槽」）——本竖条里另有 快速存档/快速读档 两项承担 qsave/qload。 |
| `quick.hit_toggle` 的 action + 可见性 | ★ **M37 已退场**（整条带 → 一排独立圆形 icon，见下文「M37 追加」）：该元素**已从数据中删除**，其 `action=open_sysmenu` 由 `quick_pin` 等 12 个项热区取代；`open_sysmenu` 动作本身保留为**编程入口**（★ **M45**：它指向的 `sysmenu` 屏已废除，动作语义不变）。以下为 M1–M36 的历史口径：`action=open_sysmenu`：收起把手热区点一下即**展开竖条（不钉住）**；`open_sysmenu` 的语义由 M2/M3 **重定义**（不再是「打开传统系统菜单屏」）。自动收起由屏级 `reveal` 的 `in_x`/`out_x` 滞回 + `delay_ms` 驱动；「钉住」由 `quick_pin` / `reveal.pin_flag` 负责。**★ 该热区 `vis_when=collapsed`（仅收起态存在）** —— 修复 A：它与 12 项热区矩形重叠（w78 z96 覆盖 w75 z95），两态都可见会使 12 项全部不可达（见上文「重叠的覆盖式热区」铁律）。（主代理 2026-09-22 裁决 B、修复 A） |
| `pin_mark` 类元素的 `visible_default` | **必须为 `true`**（见 §四 铁律）：`quick.pin_mark` 靠 `qbar_pin` flag 控制显隐，写 `visible_default:false` 会使其永远不可见；「默认不显示」由 `flags_default.qbar_pin:""` 表达。（主代理 2026-09-22 裁决 A） |
| `quick.tgl` 的可见性 | ★ **M37 已退场**（连同 `quick.btn` / `quick.tips` 一起；素材移入 `_工作\M37_旧素材归档\`）。以下为 M1–M36 的历史口径：**仅收起态**（`vis_when=collapsed`，2026-09-22 一审 G3）：它是 `image`（无 action、不参与命中），与展开整条同矩形同区段，两态同显会让展开条透出 slim 把手残影（实测前 513 行美术差异 mean=34.4/255）。原 note 写「两态都要能**点到**它」不成立，已改。 |
| `sv.del/mod/mov/cpy`、`cfg.on_hit/off_hit`、`cfg.mute_hit` 的 z | 一审 G1/G2 修复：见 §四 **铁律二**（具体控件赢）。`sv.*` z=95→**97**（`sv.hit_back` 为 96）；`cfg.on_hit`/`cfg.off_hit` z=95→**96**、`cfg.mute_hit` z=95→**97**（`cfg.it_facewindow_hit` 整行为 95）。 |

**M37 追加（2026-09-23，快捷条**形态重构** · `ISSUE-20260923-01`，用户裁定）**

> 用户裁定原「整条带 + slim 把手」**太丑**，改为「**一排独立的圆形 icon 按钮**，悬停换材质并在左侧浮出中文名称；**平时完全隐藏**，鼠标贴右端才整列淡入」。
> **机制层零新增字段** —— 下面 6 条全部是**既有字段的新用法**，两端代码**未因本次改动而改判据**。

| # | 口径 | 说明 |
| --- | --- | --- |
| 1 | `state_group` **组绑定**的新用法：`image` ↔ `hit` 同组 | `quick.ic_<key>`（image，带 `state_assets`）+ `quick.hit_<key>`（hit，**无态图**、仅带 `state_group: "quick.<key>"`）同组。指针落在 **75×73 热区内的任何位置**（不只是圆形徽章本身）都会点亮徽章 —— 因为悬停层判据把「带非空 `state_group` 的 hit」也算候选（`uiScreenHoverAtIn`；★ M46 起该并集还有第三项「带**逐项**态图的 list」，与本条无关），胜出后 `ctx.hoverGroup` 指向该组，同组元素一起换态。**`hit` 不必持有态图**（那会在热区矩形上拉伸涂抹，正是 M35b 迁移要消除的）。 |
| 2 | **`hit` 的 z 必须高于同组 `image`** | 悬停/点击都取「最高 z」。icon z=90 < hit z=95 ⇒ ①悬停胜出者恒为 hit（组内一致，`test_state_targets.py` 的「中心胜出者须同组」成立）；②点击只认 `hit/list`，徽章不参与点击 ⇒ 点在圆面上仍派发该动作（HTML 侧走 `interactiveUnderPoint` 遮挡兜底，见 §六 规则⑦）。 |
| 3 | 药丸底用 **九宫格横向拉伸**（`nine: {l:25,t:0,r:25,b:0}` ★ P1 起） | `quick.pl_<key>`（image，**70×64 源、丸体 44 高居中**）：端点 25px（= 圆角半径 22 + 外晕 3）1:1 保留圆角与端部柔光，中段拉伸；**每条按字数各自定宽** `w = 字号 24×字数 + 2×内边距 26 + 2×透明边 4 = 24n + 60`（避免 2 字名顶着 4 字宽的药丸）。`t=b=0` **仍合法但有前提**：纵向 1:1 不缩放 ⇒ **元素高必须 == 源高**，故 `QUICK_PILL_H = 64`（P1 由 44 改 64；丸体仍 44，视觉位置不变）。宽度公式与全部几何常量的**唯一出处 = 生成器的 `pill_w()` / `pill_body_w()`**；守门脚本 `import m34_build_screens` 取用，**不复制公式**。 |
| 4 | 「**完全隐藏**」由 `flags_default` 的空/收起值表达 | 收起态（`quickbar="collapsed"`、`qbar_tip=""`）12 icon + 12 药丸 + 12 白字 + 12 项热区**全不绘制**（krkr 巡演实测 `实绘元素=0`）⇒ **右端不再有任何可点热区**（点空＝穿透到承载屏）。★ 不得用 `visible_default:false` 表达（那是死件，见 §四 铁律）。 |
| 5 | `qbar_tip` 仍只承载「当前悬停项 key」 | 12 药丸 + 12 白字挂在它上面（`vis_when=<key>`）；气泡 key 集算法不变（`vis_flag==tip_flag 且 vis_when != "*"`），**新增的药丸不改变集合**（同值去重）。收起时 `tip_flag` 被清空 ⇒ 无残留药丸。 |
| 6 | `open_sysmenu` 保留但**无数据落点** | 整条把手退场后，数据里没有元素再指向它 ⇒ 它成为**编程入口**（深链 / 附加层里 `action` 留空的热区兜底，`UIScrQuickToggleAct`）。展开的**唯一鼠标入口** = 指针移到 `x ≥ reveal.in_x`。Esc 不挂它（H1 裁决）。<br>★ **M45（2026-09-23）补记**：它曾指向的 `sysmenu` 屏**已整体废除**（用户裁定「已有药丸按钮系统」）⇒ 本动作**不再有任何屏语义**，仅剩上述编程入口；两端实现（`uiQuickbarOpen()` / `expandQuickbar()`）**一字未改**。 |

**L1 / L2 订正（2026-09-23，同 issue，主代理裁决 —— 覆盖上表两处取值）**

| # | 项 | 新口径（**旧值 → 新值**） | 理由 / 落点 |
| --- | --- | --- | --- |
| L1 | icon 画布尺寸 | **56×56 → 64×64**（圆径仍 56、保留圆外柔光、描边加粗到约 2px）。由 G1 按新规格重切素材 | 实际渲染下 56 画布「图标偏小偏苍白」。**圆心仍 = 热区矩形中心**，按 64 重算：`x = 1845 + (75−64)//2 = 1850`、`y = 7 + 75n + (73−64)//2 = 11 + 75n`（偏 (0.5,0.5)px）。落点：生成器 `QUICK_ICON`／元素 note；`工具\test_quickbar_reach.py` 的尺寸断言改为**读磁盘 PNG 实测尺寸**（不再写死数字） |
| L1 | 药丸与 icon 的间距 | **6 → 8**（`QUICK_GAP`） | 观感微调（画布变大后 6px 显得贴太近）。落点：生成器 `QUICK_GAP`＋元素 note；守门 `PILL_GAP = gen.QUICK_GAP`（**import 生成器，不再复制常量**，另加 `0 < gap ≤ 16` 区间断言）。★ 间距按**可见丸体右缘**量（元素左右各含 4px 透明边） |
| P1 | 药丸材质入「我方冰蓝族」 | **底**：纯平实色 → **竖向渐变 `#6FA8E8`→`#3F6FB4`**；**描边**：1px `#A0C9F7`；**外晕**：新增约 **3px 青蓝柔光**；**画布**：44 高 → **64 高**（丸体 44 居中、上下各 10 留白 ⇒ 外晕在画布内衰减到严格 0）；**九宫格**：`l=r=22` → **25**（= 半径 + 外晕） | vision 判定旧丸底（旧 `@palette.highlight #3A5A9A` ×0.85 的纯平实色 + 1px 浅边、无渐变/无磨砂/无外晕）与圆徽章**不是一套材质**。**不新增色板键**：这些色值直接烘进 PNG（layout 侧不引用；`palette.json` 未改）。落点：`_工作\M37_占位件与药丸生成.py::draw_pill()`（素材）+ 生成器 `QUICK_PILL_*` 常量与 note。★ 渐变在丸体**顶部 10px 内收敛**（`PILL_RAMP`）：完整线性渐变时白字**字带上沿**对比度仅 2.89:1（<4.5），收敛后整个字带 ≥5.07:1 —— 置 `PILL_RAMP = 0` 即回到严格线性版。★ 丸体左右各留 4px 透明边（外晕 3 + 1px 余量）⇒ 画布四缘 alpha 实测 = 0（柔光未被裁）。 |
| Q1 | 药丸白字加**深色描边** | `quick.tx_<key>` 的 `font` 增 `outline:true` / `outline_color:"#16305A"` / `outline_width:1`（四向/八向 1px） | vision 实测参照做法：参照药丸「白字对青底仅 ~2.1:1，可读性靠描边」；本工程白字对丸底已有 ~5:1，加 1px 藏青描边是为获得「印刷标签」式边缘锐度。**用 M38 的既有机制**（`font.outline*`，两端已通、纯渲染不参与布局，见 §六「铁律三」）；**不动引擎、不动主题、底色不提亮**。两端生效实测：krkr 侧药丸区域内接近描边色 `#16305A`(±26) 的像素 175 个；HTML 侧 `text-shadow` 8 方向 × 1px × 12 条（DOM 里 `rgb(22, 48, 90)` 出现 96 次） |
| Q2 | 药丸**调细一档** | 丸体高 **44 → 40**（画布仍 64、丸体居中于 y=12..51）；圆角半径 40/2=20；**九宫格端点 25 → 23**（= 半径 20 + 外晕 3）；字号 **24 → 21**（三标签墨高 21/22/21，最大 22 / 丸高 40 = **55%**，vision 要求 52–55%、参照 50%）；宽度公式 `24n + 60` → **`21n + 56`**（`QUICK_PILL_PAD` 仍 24，左右内边距天然对称且 24 > 半径 20 ⇒ 字不进圆角区） | vision：参照丸/徽高比 0.57（细标签），本工程原 0.93（与徽章"同重"）⇒ 收一档到 **0.74**（纯丸体 40 / 徽章 54；含外晕可视高 46/54 = 0.85）。资源侧：PNG 70×64 → **66×64**；`PILL_RAMP` 10 → **8**（丸体压到 40 后，字带上沿落在第 9 行 ⇒ ramp 须 ≤8 才能让**整个字带**保持 ≥5.07:1）。白字对比度实测：最深点 **5.21:1**、字带最差 **5.07:1**（均 ≥4.5） |
| P1 | 药丸文字 | **字号 28 → 24**（= CJK 字宽 1em）；白字框 = **丸体矩形**（不再等于元素框） | 墨迹高/丸高 **61% → 55%**（用户判定「字偏满、上下各仅 8.5px」；24px 时上下各 10px）。宽度公式随之 `34n + 44` → `24n + 60`（**左/右内边距各 26，天然对称**；26 > 圆角半径 22 ⇒ 字不进圆角区）。白字对比度实测：最深点 **5.21:1**、整个字带 **5.07:1**（要求 ≥4.5:1）。落点：生成器 `QUICK_PILL_CHAR_EM`/`QUICK_PILL_PAD`＋`pill_w()`；⓪ 守门改为**生成器公式驱动**并新加**素材实测**（PNG 尺寸 / 丸体 44 高居中 / 画布四缘 alpha=0） |
| L2 | `quick.pin_mark`（钉住叠层）的 `opacity` | **200 → 255** | 200 的半透明叠层压在常态徽章上会读作「被洗白的重影」而非「已激活」；两态几何已由 G1 归一化到逐像素同位 ⇒ 255 时该叠层**就是**该按钮的悬停材质，语义直给、无重影。**备选方案（钉住时用 `vis_when` 排除常态 icon）已评估未采纳**：要让 12 个 icon 各多带一套互斥 `vis_when`（数据 +12 件），而 255 叠层在同矩形下已等价于「只画 `_on` 图」，取更简者。 |

**M39（2026-09-23，对话框底部渐变遮罩 · `ISSUE-20260923-01`，**用户裁定·已定稿落地**）**

> 无框化（M38）后白字压在亮画面上，用户要求「加一层**黑色渐变透明遮罩**，文本显示效果更好」。
> **零引擎改动**：全部走既有的 `image` + `opacity`，两端渲染器一字未改。
> **定稿参数**：`dlg.mask_bottom` = `asset ui/x_ui_dlgmask_bottom_350.png` ｜ `x0 y730 w1920 h350` ｜
> `opacity 230`（= 不透明度 **90%**）｜ `z 15`。未采用的 400 版已归档 `_工作\M39_旧素材归档\`。

| # | 口径 | 说明 |
| --- | --- | --- |
| 1 | ★★ **通用做法一：素材上限保留 255，强度用元素 `opacity` 当旋钮** | 素材 `x_ui_dlgmask_bottom_350.png`（**1920×350** PNG-32，RGB 纯黑，`alpha = 255×t^1.0`，t = 素材内纵向进度 0..1；中线 α=128、末行 255）**本身做到 alpha 255**；运行时**只改元素 `opacity`（0–255）**即调深浅 ⇒ **改强度不必重出图**，一张素材可服务多档强度（本轮实测：70%→179 / 75%→191 / 85%→217 / 90%→230 / 100%→255 全部共用同一张素材）。**不得**把百分比烘进素材。 |
| 2 | ★★ **通用做法二：遮罩的「范围」与「曲线」必须按实测字形范围定，不能按数据框估** | 数据框只是**排版盒**。定稿过程实测：`dlg.name` 数据框 y747..803，但**实绘字形只有 y749..788**；`dlg.text` 框顶 806，**首行字形 y806..850**（一行的墨迹只占盒高的约 44/50）。口径：**同一档分两次渲染、把目标元素 `display:none` 再作差，差集即该元素的实绘像素**（比按框估可靠）。⇒ 曾试的贴底 **250px（y830..1080）会「盖不到角色名（y749..788）」且「横切台词首行（y806..850）」**，故改 **350px（y730..1080）**，两处均完整落罩。**引擎侧同口径复核**：名字带平均 \|Δ\| 由 250px 的 **0.000** 变为 350px 的 **3.855**（首行带 2.701 → 26.240）。 |
| 3 | 遮罩类 `image` 的 **z 必须「在画面之上、文字之下」** | `dlg.content`（画面）z=1 < `dlg.mask_bottom` z=15 < `dlg.name`/`dlg.text` z=22 < `dlg.choices` z=30。实测（满强度 opa=255 A/B）：**同排纯画面带内未被压的亮像素 0.00%，而文字矩形内 4.68%（最高 255）** ⇒ 遮罩只压画面、不压文字。**不得**把遮罩放到文字之上（那会连同墨迹一起压暗，白字发灰）。 |
| 4 | 无 `nine` 的遮罩 `image`：`w/h` == PNG 实尺寸 | 满幅宽 1920 + 高 350（覆盖 y 730..1080），故**不做纵向拉伸**、不需要 `nine`；`verify_ui.py` [2] 的「无 nine ⇒ w/h == PNG 实尺寸」直接成立。★ 遮罩覆盖到画布底，但**画面下沿是 990**（4:3 源 1200×900 居中）⇒ `y ≥ 990` 的 letterbox 纯黑**压黑不变**（Δ≡0），`y1020/1079` 的实测 Δ 为 0 属物理正确，不是遮罩失效。<br>★ **D-04（2026-10-02）后本段前提已变**：画面区改全画布（下沿 1080）⇒ 遮罩带（y730..1080）现在**压在真实画面上**——这正是它的用途（底部渐变提升文字可读性）；当时的「画面下沿 990 / Δ≡0」实测结论属**历史留痕**。 |
| 5 | 曲线形状的量化口径（供日后调档） | 用 `α_eff(y) = 255·t^γ·opacity/255` 预测、用「该行画面内容像素平均 \|Δ\| ÷ 平均亮度 × 255」实测反推，两者**逐点吻合**（本轮全档最大偏差 1.4/255）。选档看三件事：**视觉起点行**（逐行平均 \|Δ\| 首次 ≥ 0.5 / ≥ 2.0 的行号，阈值写明）、**整层留存 %**（固定分母区＝整个画面层）、**正文带留存 %**（固定 y806..1007）。定稿 350px 线性 90% 实测：起点 Δ≥2.0 → y735；整层留存 90.9%、正文带留存 56.2%、CR 5.57；被压行占 23.8%。 |
| 6 | 与参照的关系（**刻意差异，别当缺陷改**） | 参照《月影魅像》实测**无底板也无遮罩**（`_工作\M37_参照几何.md` §二）；本件是**用户 2026-09-23 的显式要求**，属我方增强。 |
| 7 | `opacity` 的**定义域契约**（与 `verify_ui.py` 第 7 项配套） | `opacity` 是 **0–255** 的字面量（见 §四「元素通用字段」）。**两端都不做范围校验**：HTML 端 `opa()` 会**静默钳到 255**，krkr 端把数值**原样透传**给 `Layer.operateStretch(..., omAlpha, opacity, …)` ⇒ 写 >255（如「300/400」）会**两端行为分叉**。要"更强"只有：① 贴上限 255（单层底部即纯黑）；② **叠层**（同素材同几何再加一个元素，合成 α = 255·[1−Π(1−aᵢ/255)]，会连带压中段、且底部上限降到 255·[1−(1−255·op/255/255)²]）；③ 改素材（本轮素材已到 255，无空间）。 |


---

## 七、生成物与校验

```bash
cd "工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\工具"
python gen_layout.py          # screens/*.json + palette.json -> ui_layout.json / ui_layout.tjs / ui_layout.js
python verify_ui.py           # 引用完整性 + 两侧常量一致性 + 素材尺寸匹配（M1 产出）
```

**数据级守门（M4 起，四道；改判据 / 可见性 / 声明序 / z 后必跑）**

| 脚本 | 守什么 | 反向自证 |
| --- | --- | --- |
| `test_verify_asset_refs.py` | `verify_ui` 的引用表覆盖 `state_assets`（含非字典异常） | — |
| `test_state_targets.py` | ①「带 `state_assets` 的任何元素」∪「带**逐项**态图（`item_frame.state_assets`）的 list」∪「带非空 `state_group` 的 hit」共 **227 件**在**自身几何中心**可达（★ 件数历经多次订正：原写 36 → M46 实测 55 → 2026-09-24 实测 97（M47 的 `state_assets` 批量落地后自然增长）→ M06 实测 95（删掉跨 3 块的静态 `bl.jump*`/`bl.spk*`）→ M08 各模块落地后实测 119 → **ISSUE-20260924-08 收尾（T2 名单 11→7 行）核对时实测 125 = 态图+组 72 ＋ 纯组热区 53**（M08 外壳/页签/差分按钮的 `state_group` 批量落地的自然增长）→ **ISSUE-20260926-06/-07 后实测 147 = 态图+组 94 ＋ 纯组热区 53**（`ISSUE-20260926-05` 复核者与 `-07` 一审各自独立实跑同一读数）→ **ISSUE-20260928-02 第 3 批后实测 220 = 态图+组 167 ＋ 纯组热区 53**（`screen1` 新增 6 组独立层的 45 个 `fc.frag<G>.<NNNN>` 态图件 ＋ 6 个按组返回键 `fc.frag<G>_back` 态图件，均带 `state_assets` 进候选并集）→ **`ISSUE-20260929-04` 第 12 批收尾实测 227 = 态图+组 174 ＋ 纯组热区 53**（增量 **+7** ＝ 第 11 批 `fc.pbkick_pause` 1 件 ＋ 第 12 批 `fc.entry.<NNNN>` 6 件新增 `state_assets`；佐证：基线 `ef68dcf` 实测「带 `state_assets` 元素」74 件 → 现行 81 件，差 7 ✓）；并集三项与前口径同；本行数字与**实跑**对齐，勿凭印象回填；★ `ISSUE-20260928-03` 注：该件数**随盘上屏变化**——交付样例 `screen1` **227**；`--preset states` 在盘上时 **176**（该档不产独立层，少了 45 件独立层 `state_assets` ＋ 6 件按组返回键）⇒ 读数不同属预期，**不是回归**）；②**判据指纹**（`uiScreenElementVisible` / `uiScreenHoverAtIn` 的 TJS 正文 hash + TJS↔python 成对令牌） | `--selfcheck`：注入 z=999 异组遮挡、放宽 TJS 判据、把 python 判据换回宽松版 —— 三项都必须 FAIL |
| `test_quickbar_reach.py` | `quickbar` 屏**端到端可达性**（复算 `uiScreenClick` 口径）：收起态把手独占 / 展开态 12 项各自可达且 `action` 与数据一致 | `--selfcheck`：把手改回可见、注入 z=999 异组遮挡 —— 两项都必须 FAIL |
| `test_gate_field_granularity.py` | 「编辑器导出入库守门」**按字段粒度**：任一元素丢 `state_group` **或** `state_assets` 即拒绝落盘 | 内置 C1/C2/C3 三例，并断言被审原文件 md5 前后不变 |

> ★ **M06（2026-09-24）与上述守门的关系（如实登记）**：
> · `uiScreenHoverAtIn` / `uiScreenElementVisible` **正文一字未改** ⇒ **判据指纹不需要更新**（实跑
>   `test_state_targets.py` 仍报「判据指纹一致 + **227** 件元素几何中心可达」（件数随实跑自然增长，口径见上表；第 3 批由 147 → 220、第 12 批由 220 → 227 的来源见该表）。
>   逐块按钮的悬停/按下**另走**一条子命中（`uiScreenListItemBtnHit`），**不进**那条候选并集 ——
>   这是有意设计，理由见 `item_buttons` 表末两行。
> · `verify_ui.py` 的 **[2] 尺寸一致性** 已扩到 `item_buttons[]`（判据与 `image` **逐字一致**：
>   无 `nine` ⇒ `w/h` 必须 = PNG 实尺寸；有 `nine` ⇒ `w ≥ l+r`、`h ≥ t+b`），计数行现在打印
>   「N 个 image（其中九宫格 M）＋K 个 item_buttons ＋J 条 slider rail」。
> · `test_click_reach.py` / `test_quickbar_reach.py` / `test_gen_sync.py` / `test_gate_field_granularity.py`
>   / `test_verify_asset_refs.py` **未因本轮改动而改判据**（复算口径与引擎一致：按钮是 list 的
>   **子命中**，不是独立的 `hit`/`list` 元素，故不进点击可达性的元素集合）。

> ★ **M1（2026-09-24 · `ISSUE-20260924-08_鉴赏模式`）与上述守门的关系（如实登记）**：
> · `uiScreenElementVisible` / `uiScreenHoverAtIn` **正文一字未改** ⇒ **判据指纹不需要更新**
>   （实跑 `test_state_targets.py` 仍报「判据指纹一致 + 119 件元素几何中心可达」；件数由
>   M2/M3 的新数据自然增长，`39_gal_shell.json` 自身**零候选件**：它的热区不带 `state_group`、
>   图片不带 `state_assets`。
>   ★ **M8 一审（2026-09-24）实测回填：119 → 124**（M2 CG 页 12 件页码互斥文本带
>   `vis_flag` 进「可见性消费」口径、M3/M4 的 `state_group` 组绑定件增长；M8 视觉修复
>   删 10 件 / 增 4 件引擎绘制文字不影响候选并集；本数 = 修后实跑输出，勿凭印象回填）。
> · `item_variants` 的悬停/按下**另走** M06 那条子命中（`uiScreenListItemBtnHit` 已扩到
>   `item_buttons ∪ item_variants`），**不进** `uiScreenHoverAtIn` 的候选并集 —— 同上，有意设计。
> · `verify_ui.py` 的 **[1] 引用表**已扩到 `item_variants.frames`（原先会**静默丢弃**这些引用，
>   与 M35 修 `state_assets` 同一类缺陷）；**[2] 尺寸一致性**已扩到 `item_variants`
>   （`frames` 按 `thumb` 区、`prev`/`next` 与 `item_buttons` 同一套判据）。
> · `ui_widget.tjs` 的 **`orientation:"h"` 网格几何**（`uiWidgetListCols` / `uiWidgetListGridH` /
>   `uiWidgetListPage` / `uiWidgetListItemRect`）与 `复刻/replica.js` 的 `listCols` / `listPerPage`
>   统一到同一公式（krkr 侧原先 `"h"` 只支持单行、且 `uiWidgetRect` 把主跨宽度误当高度写进 `r.h`）；
>   `工具/test_click_reach.py` 的 python 复算镜像**同步更新**（否则守门与引擎分叉）。
> · `test_click_reach.py` / `test_quickbar_reach.py` / `test_gate_field_granularity.py` /
>   `test_verify_asset_refs.py` 的**判据**未因本轮改动而变（`test_click_reach` 只更新了
>   「list 几何公式」这一处镜像）。
> · `test_gen_sync.py` 的 `NO_GEN` 追加一条 `39_gal_shell.json`（M1 新建屏，手工维护、无生成器）。

> ⚠️ **判据指纹是有意的强约束**：`ui_screens.tjs` 的 `uiScreenElementVisible` / `uiScreenHoverAtIn` 正文
> 一旦被改写（哪怕只是格式），`test_state_targets.py` 就会 FAIL 并打印新旧 hash —— 目的是逼人在改判据时
> **重新确认这道守门是否仍然成立**，再更新脚本里的 `JUDGE_FINGERPRINT` / `JUDGE_TOKENS`。
> `--print-fingerprint` 可打印当前 hash。

**约束（生成器会强制）**：
1. 元素 `id` 全局唯一；重复即报错退出。
2. 引用 `@palette.<key>` 的键必须存在于 `palette.json`。
3. `image` 元素的 `asset` 文件必须存在于 `krkr/assets/ui/`（**校验由 `verify_ui.py` 承担，生成器只做静态检查**）。
4. `kind=image` 且给了 `nine` 时，`w/h` 必须 ≥ `nine.l+nine.r` / `nine.t+nine.b`。
5. 未写 `z` 的元素按声明顺序自动编号。