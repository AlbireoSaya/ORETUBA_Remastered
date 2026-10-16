# 运行方式 · UI 演示工程（M2/M4 + M8 修复）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（UI 演示工程运行方式；含历代批注） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

适用：`工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\`
Issue：`ISSUE-20260919-11-greta-ui`（UI 美术组）　｜　最后更新：**2026-10-02（D-04 批）**（★ 2026-10-09 校准：原记「M8」为建立期口径；历轮增量见各节就地注）

---

## 一、怎么跑（双击即可，不依赖 bash / WSL）

| 脚本 | 用途 | 行为 |
| --- | --- | --- |
| `krkr\run_loose.bat` | **普通演示** | 同步运行副本 → 删掉巡演触发文件 → 启动引擎，人工操作 |
| `krkr\run_autotour.bat` | **自动巡演** | 同步运行副本 → 放 `autotour.txt` → 启动引擎，无人值守逐屏切换后自动退出 |
| `krkr\run_pressprobe.bat` | **按下态导出** | 同巡演，但额外汇出一行 `press_probe.tjs`（`UIScrPressProbe = "<元素id>"`，见 §四）→ 该元素在截图里呈**按下态**；运行目录独立为 `临时\ui_run_press`（不覆盖巡演产物）。`set PROBE=<元素id>` 可换目标，默认 `title.menu_hit_1`（M46 修：原默认 `ch.hit_1` 随 M45f 的 list 化消失）；⚠️ 该探针只吃**元素 id、不吃项序号** ⇒ 逐项按下态请用巡演的 `ptr` 步骤 |
| `krkr\run_quickbar.bat` | **竖排快捷条·强制展开导出** | 同巡演，但额外汇出一行 `quick_flags.tjs`（`UIScrFlagForce["quickbar"]="expanded"; ["qbar_tip"]="lock"; ["qbar_pin"]="1";`，见 §四）→ 竖条以**展开态**出图。★ **M37（2026-09-23，`ISSUE-20260923-01`）形态重构后：展开态实绘 = 27**（12 圆形 icon + 12 项热区 + 1 个 tip 药丸 `quick.pl_lock` + 1 条白字 `quick.tx_lock` + 1 个钉住叠层 `quick.pin_mark`），**收起态实绘 = 0**（整列不绘制）；实测 `[UI][TOUR] 屏=quickbar 实绘元素=27 / 0`。把 `qbar_pin` 置空则 26（实测已验证）；运行目录独立为 `临时\ui_run_quickbar` |

四个 bat 的注释是纯 ASCII，只有 `临时` 一个中文路径片段（bat 以 **GBK + CRLF** 保存，首行 `chcp 936`）。
**不要**用文本编辑器另存为 UTF-8，否则 cmd 会读错那两个字（**2026-09-22 实际踩过**：
UTF-8 注释 → `'p' 不是内部或外部命令` 刷屏；LF-only 行尾 → 同样症状）。

### 两个 bat 实际做的事

```
UIROOT = <...>\UI组\krkr\                 （bat 所在目录，%~dp0）
WTROOT = UIROOT\..\..\..\..\              （= 临时\wt-ui，git worktree 根）
RUN    = WTROOT\临时\ui_run               （运行副本，叶子目录名全 ASCII）

1) 建 RUN
2) 清 RUN\game 与 RUN\runtime\savedata
3) xcopy krkr\game   -> RUN\game
   xcopy krkr\assets -> RUN\game\assets    ← 关键：让素材候选名 ②「assets/ui/…」命中
4) RUN\runtime 不存在时才从 krkr\runtime 复制（含 tvpwin32.exe / license.txt / plugin\）
5) run_autotour.bat 写 RUN\game\autotour.txt；run_loose.bat 反而删掉它
6) 启动： tvpwin32.exe "<RUN>\game"
```

- 日志与截图落点：`RUN\runtime\savedata\`（即 `<wt-ui>\临时\ui_run\runtime\savedata\`）
- 退出：普通模式按 `Q` 或关窗口；巡演模式约 45 秒后自己退出
- 手动收尾（只在巡演卡住时需要）：`taskkill /IM tvpwin32.exe /F`

### `krkr\runtime\` 不入库

`runtime\` 里是 `tvpwin32.exe`（二进制，约 4.3 MB）、`license.txt`、`plugin\*.dll`。
`.gitignore` 已忽略 `*.exe` / `*.dll`，**确认过不需要额外规则**；若要从零搭建，
从工作区工具链只读复制：`工具\krkrz\krkrz_20171225\` 的 `tvpwin32.exe` + `license.txt` + `plugin\*.dll`。

### ★★ 新 worktree 必读：引擎二进制不会被带过来（2026-09-23 实际踩过）

**症状**：在一个新建的 worktree 里双击 `run_autotour.bat` / `run_quickbar.bat`，
cmd 打印 `系统找不到文件 tvpwin32.exe。`，`.bat` 仍打印「Tour runs ~45 s …」并返回 0，
但**没有任何窗口、`savedata\` 里也没有 `krkr.console.log` / `shot_*.png`**——
看起来像「巡演跑完了但没出图」，实际是**引擎根本没启动**。

**成因**：`*.exe` / `*.dll` 全被 `.gitignore` 忽略 ⇒ **git worktree 检出里根本没有**
`krkr\runtime\tvpwin32.exe` 与 `krkr\runtime\plugin\*.dll`（只有 `license.txt` 与空的 `savedata\`）。
主工作树里有，worktree 里没有。

**处置（缺什么补什么，一次即可）**：从主工作树只读复制这两样进当前 worktree 的 `krkr\runtime\`：

```
copy "E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\runtime\tvpwin32.exe"  <当前 worktree>\...\UI组\krkr\runtime\
xcopy "E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\runtime\plugin"  <当前 worktree>\...\UI组\krkr\runtime\plugin\  /E /I /Y
```

**另一个坑（同时踩过）**：`.bat` 只在 `%RUN%\runtime` **不存在**时才从 `krkr\runtime` 复制运行副本
（见「两个 bat 实际做的事」第 4 步）。若上一次运行留下的 `%RUN%\runtime` 里刚好**没有** exe
（早期失败运行的残留），下一次运行**不会补**——仍报同一个错。⇒ 症状复现时先
`rd /s /q %RUN%`（或让 Python 删掉 `临时\ui_run*`）再跑。

---

## 二、跑起来能看什么

**17 类界面**（布局数据 `layout/screens/_index.json` 登记，`ui_layout.tjs` 生成）：
★ M43（2026-09-23，用户裁定）：「主页·章节选择 `chapter`」屏**已删除**（主列表 19 类 → 18 类）。
★ M45（2026-09-23，用户裁定）：「系统菜单 `sysmenu`」屏**已废除**（用户原话「现在废除『系统菜单
sysmenu』页，因为我们已有药丸按钮系统」）⇒ 上句「另有 `sysmenu`（数据保留、已不可达）」的旧口径
**已作废**：屏文件 / `_index.json` 条目 / 两端活引用 / 文档清单全部清理（快照归档 `_工作\M45_旧素材归档\`）。
系统功能由右端竖排快捷条 `quickbar` 承担。
★ M46（2026-09-23，用户裁定）：「系统条 `sysbar`」屏**已删除**（18 类 → **17 类**；用户原话
「把系统条 sysbar 页删了，**但底条素材保留（防冲突）**」）⇒ 屏文件（`34_sysbar.json`）/ `_index.json`
条目 / 巡演白名单 / 两端活引用 / 文档清单全部清理（快照归档 `_工作\M46_旧素材归档\`）。
★ **本屏 4 组素材一律保留原位、不归档、不删除**：`x_ui_sysbar.png` —— ★ **ISSUE-20260929-04 订正（2026-09-29）**：`sysbar` 屏与流程图屏的 `fc.sysbar` **均已退场**（流程图屏的 `fc.sysbar` 元素已删），**素材保留不删（防冲突）**（旧记「与流程图屏 `fc.sysbar` 共用」**已作废**）；
`x_ui_snap_*` / `x_ui_hide_*` / `x_ui_spk_*` 同理留在 `krkr\assets\ui\`。
★ M06（2026-09-24）**订正**：`x_ui_spk_*` **已不再被任何屏引用** —— 回想屏原静态元素 `bl.spk`
已随本轮「逐块按钮」重排**删除**（`bl.jump` / `bl.jump_tx` / `bl.jump_hit` / `bl.spk` /
`bl.spk_hit` 一并退场，改用逐块按钮 + 新件 `x_ui_spk2_{off,over,on}.png`，见
`layout\screens\26_backlog.json` 的 `item_buttons`）。旧件按冻结书 §3「旧件保留不删」留在原位，
**仅作历史素材**。

`title` 标题 / `dialog` 对话框（★ **M38 无框方案**：角色名 + 正文 + 打字机 + 选择肢，文字为**黑描边白字**；窗口底图与 9 功能图标九宫格已退役）/ `save` 存档 /
`load` 读档 / `config` 环境设置 / `backlog` 回想 / `gallery` CG 画廊 / `music` 音乐鉴赏 /
~~`fragment`~~ 番外（Fragment）选择（**★ ISSUE-20260928-06 已整体删除**，番外改由 `flowchart` 独立层承载）/ `flowchart` 剧情流程图 /
~~`ending`~~ 片尾（**★ ISSUE-20260928-07 已整体删除**，用户：未来改用一段视频代替）/ `loading` 加载提示 / `confirm` 确认框 / `sysicons` 右键 9 图标浮层 /
`quickbar` 系统菜单快捷条 / `choices` 选择支 / `dress` 立绘鉴赏·换装
（★ M45：`sysmenu` 系统菜单**已废除**，不再是「保留不删」；`open_sysmenu` **动作**保留，
语义自 M2 起＝「展开竖排快捷条」，且从未在巡演白名单里；见 §八
★ M46：`sysbar` 底部系统条**已删除**，也不再在巡演白名单里）
★ **ISSUE-20260928-06（2026-09-28，用户裁定）：`fragment`（番外·Fragment 选择）屏已整体删除**（19 类 → **18 类**）—— 屏文件 / `_index.json` 条目 / 巡演步 `open_fragment` / 白名单里的 `"fragment"` 均已移除；番外 6 组内容已由**流程图屏的独立层** `flow_layer`（`layer:"frag1".."frag6"`）承载。**动作 `open_fragment`/`fragment_enter`、素材 `x_gen_fragpage.png`、数据 `fragments`、模块 `ui_fragment.tjs`（含 `startup.tjs` 加载行）一律保留**（用户「只删屏、保留动作/素材」）。
★ **ISSUE-20260928-07（2026-09-28，用户裁定）：`ending`（片尾·STAFF/歌词）屏已整体删除**（用户：**未来改用一段视频代替**）—— 屏文件 `29_ending.json` / `_index.json` 条目 / 巡演步 / 白名单里的 `"ending"` 均已移除（**18 类 → 17 类**）；屏内 7 件元素（`ed.bg`/`ed.shade`/`ed.char`/`ed.staff`/`ed.lyric_bar`/`ed.lyric`/`ed.hit_skip`）随之移除。**该屏原本就没有模块、没有 `open_ending` 类动作、没有 `startup.tjs` 加载行、也没有任何跨屏入口**⇒ 编程组无需改接线。★ 另：`复刻\screen_index.js`（**编辑器用**屏清单）也须**重跑 `工具\emit_asset_index.py`** 才同步 —— 本批首版曾漏跑它、导致编辑器屏选择器为空并抛 `TypeError`（一审抓出 Critical，已修 + 已把该步纳入 `run_all.py`）。

自动巡演按固定顺序走 **20 步**（含 2 次合成右键 + **3 次合成指针**），再把「layout 里存在但没列到」的屏追加进去。
★ ISSUE-20260928-06 实测的**步表精确变化**：`UIScrTourSteps` 条目 **101 → 100**（`kind:"action"` **15 → 14**，即去掉 `open_fragment` 一步），其余各类（`screen` 16 / `flowclick` 14 / `itembtn` 12 / `galtab` 6 / `galpage*` 10 / `drag` 3 / `ptr` 3 …）**一件未动**。
（★ ISSUE-20260928-07：上一段 `seen=18` 系**删 `fragment` 时点**的口径、尚含 `ending`；删 `ending` 后最新读数见 §本次实测的重跑记录 —— 现行屏数一律以 `layout/screens/_index.json` 为准＝ **17 类**。）
**本次实测（2026-09-28，删 `fragment` 屏后重跑）：107 张 PNG
｜缺件 0 ｜缺件元素 0 处 ｜转场 成功 33 / 失败 0 / 降级 0 ｜`EXCEPTION` 0 ｜`frames=1991` ｜
`seen=18[title,dialog,choices,sysicons,save,load,config,backlog,gallery,music,dress,replay,flowchart,
ending,loading,confirm,quickbar,gal_shell]`**
——**序列里没有 `fragment`**；全日志里 `fragment` 只剩 **3 行「模块装载」**（`ui_fragment.tjs` 按裁定保留、`startup.tjs` 仍加载它），**无任何屏切换/绘制**。
（日志证据 `_工作\ISSUE-20260928-06_删屏\证据\krkr.console.utf8.txt`。）
历史：M46 实测 27 张 PNG / `seen=17`（含 `fragment`、无 `sysbar`）/ 转场 21 / 降级 0；
M46 删屏轮 24 屏记账 / 23 步 / 24 张 PNG；M45 实测 25 屏记账 / 24 步 / 25 张 PNG、`seen=18`（含 `sysbar`）；M2 实测 26 屏记账 / 25 步 / 26 张 PNG；移除 `sysmenu` 步之前为 27 屏。

```
title → dialog → 选择肢（对话框内联展开）→ 选择支屏（全屏列表）
→ 合成指针：悬停第 2 项 → 合成指针：按住第 3 项
→ 合成右键（呼出 sysicons 浮层）→ 合成右键（收起浮层）→ save
→ load → config → backlog → gallery → music → 剧情流程图占位（★ ISSUE-20260928-06：原「番外 Fragment 占位」步**已移除**，番外现由流程图独立层承载）
→ ~~ending~~（★ ISSUE-20260928-07：该屏已删除、巡演步一并移除）→ loading → title
→ 合成指针：负向对照（标题屏 `title.menu_hit_1`，非 list 必须被守卫挡下、打出 `★M46PTR-REJECT★`）
→ 追加：confirm → flowchart → sysicons → quickbar → dress（★ ISSUE-20260928-06：原 `fragment` 步**已移除**）
```

★ **`kind: "ptr"` 合成指针**（M46 新增，见 `ui_screens.tjs` 的 `uiScreenSyntheticPointer`）：
把指针**置到某个 list 的具体一项上**（spec = `<元素id>:<项序号>[:press]`，项序号是**全局序号**），
走的是与真实鼠标移动**同一批入口**（`uiScreenHoverUpdate` / `uiScreenPressUpdate`），
日志打 `★M46PTR★ PASS|FAIL` 判词（命中项序号 / 锁存按下项序号 / hover 变化 / 选出的态图 vs 期望）；
守卫挡下时打 `★M46PTR-REJECT★`。用途＝「列表逐项三态」的**目标级机检**（比「日志无 error」强）。
⚠️ HTML 复刻端的探针分隔符是 **`~`**（`?hover=ch.choices~1`）——两端语法不同，别混。

巡演每屏停留 2 秒（`startup.tjs` 的 `UI_TOUR_STEP_MS`），并在**切换前**给当前屏记账 + 导出一张 PNG。

### 每屏怎么切

- **巡演模式**：自动，无需操作（巡演期间键盘/鼠标输入被显式忽略并记日志）。
- **普通模式**（`run_loose.bat`）：
  - 鼠标点击列表项 / 系统条 / 正文区（正文区点击 = 推进对话）
  - `↑` `↓` 移动当前列表高亮，`Enter` 触发高亮项
  - 对话框屏：`空格` / `Enter` / `↓` 推进（打字机中按一次 = 整行显示）；`C` 展开选择肢；选择肢展开时 `↑` `↓` 移动、`Enter` 点选
  - `Esc`：非标题屏关闭当前层；标题屏退出
  - `Q`：直接退出
  - 滚轮：列表翻页
  - 启动后有 **8 秒输入静默期**（防"窗口恰在鼠标下弹出被顺手点关"），期间输入被忽略并记日志

---

## 三、为什么要另建运行副本（**不是**因为非 ASCII 路径）

### 结论（M8 实测）

运行副本固定放 `<worktree>\临时\ui_run`。**唯一真正的理由是「让素材候选名 ② 命中」**（见下第 1 条）；
叶子目录名恰好全 ASCII 只是顺带结果，**不是引擎的硬性要求**。两条理由：

1. **素材候选名 ② 才会命中。** `ui_asset.tjs` 只试三个候选名：
   `ui/…`（项目根内）、`assets/ui/…`（项目根内）、`-assetdir` 绝对路径。
   把 `krkr\assets` 复制成 `RUN\game\assets` 后，`assets/ui/panel_frame.png` 直接命中——
   本次巡演日志为 `已载入 17 件 / 缺件 0 件`，`[UI][MISS]` **0 条**。
2. **与主代理的验收环境一致**，PNG / 日志落点固定，便于逐轮对比。

### 实测记录（含一处**与主代理原述不符**，如实列出）

- **主代理原述**：krkr 存储层不能处理项目路径里的非 ASCII 字符，非 ASCII 路径下报
  `不能找到文件 …ui组/krkr/game`。
- **M8 复测**：直接以**工程内**的非 ASCII 目录启动
  `tvpwin32.exe "<...>\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\game"`，
  **未能重现**该报错——13 个 `.tjs` 全部 `execStorage OK`，`canvas = 1280x720`，
  窗口正常建立。引擎日志里项目目录被小写化为
  `file://./e/zcode workspace/galgame/临时/wt-ui/工程/我们没有翅膀——格雷塔迦露德与柳木原/ui组/krkr/game/`
  仍然命中（Windows 路径大小写不敏感）。
- **真正失败的是素材解析**：该次启动出现
  `[UI][MISS] ui/tl1_bg1.png (三个候选名都不存在)`、`[UI][MISS] ui/panel_frame.png (三个候选名都不存在)`
  ——因为 `krkr\assets\` 是 `game\` 的**兄弟目录**，候选名 ①②都指不到它。
  M8 另试了命令行 `-assetdir=<绝对路径>`（放在路径参数前/后各一次），
  `System.getArgument("assetdir")` 均返回 void，未生效；**未继续深挖**（超出本次缺陷范围）。
- 因此 README 把 ASCII 运行副本写成**工程约定 + 素材命中需要**，
  而**不**写成"引擎硬限制"。该分歧留给主代理裁决（见 `_工作\M8_报告.md` §未决问题）。

---

## 四、巡演触发方式（`startup.tjs` 的 `uiDetectTour()`，按序判定）

| # | 触发方式 | 说明 |
| --- | --- | --- |
| ① | ~~命令行 `-autotour=1`~~ | **⚠️ 实测不可用（2026-09-22 / M35）**：见下方「关于命令行参数」 |
| ② | `<datapath>\autotour.flag` 存在 | datapath = `RUN\runtime\savedata\`；**未实测** |
| ③ | **项目根 `autotour.txt` 存在** | `run_autotour.bat` 用的就是这条，**唯一已实测可用** |

### 关于命令行参数（2026-09-22 实测，M35）

本轮做按下态验收探针时做的对照实验：命令行传 `-autotour=1` 并**抽掉** `autotour.txt`，
引擎日志确实把它记入「已声明设置： -autotour=1」，**但脚本里 `System.getArgument("autotour")`
返回 void** ⇒ 日志打出 `autotour = OFF`，巡演根本没起来。

⇒ **本 krkrz 1.4.0.8 构建下，脚本读不到命令行参数**（`-about` 之类引擎自身参数除外）。
**本工程一切「外部开关」只能走 flag 文件**（`autotour.txt` 即此法，已验证）。

因此按下态验收探针也改用 flag 文件：项目根存在 `press_probe.tjs` → `startup.tjs` 的
`uiInitPressProbe()` 用 `Scripts.execStorage` 执行它（内容一行：`UIScrPressProbe = "<元素id>";`）。
入口脚本 `krkr\run_pressprobe.bat`（**GBK + CRLF**，与 `run_autotour.bat` 同口径——
cmd.exe 按 OEM 码页 936 读 .bat，UTF-8 注释或 LF-only 行尾都会让它崩，两者本轮都实际踩到过）。

竖排快捷条的**强制展开**用同一机制（M2，见 `startup.tjs` 的 `uiInitQuickFlags()`）：项目根
`quick_flags.tjs`（一行 `UIScrFlagForce["quickbar"]="expanded"; UIScrFlagForce["qbar_tip"]="lock";
UIScrFlagForce["qbar_pin"]="1";`）由 `run_quickbar.bat` 生成；强制值在 `uiScreenFlagsInitFor`
填完 `flags_default` 后套用（**换屏不被冲掉**），且强制期间竖条的自动收起倒计时被抑制。

---

## 五、日志与截图落点

`<wt-ui>\临时\ui_run\runtime\savedata\`

| 文件 | 说明 |
| --- | --- |
| `krkr.console.log` | **UTF-16LE** 日志。看中文：`iconv -f UTF-16LE -t UTF-8 krkr.console.log` |
| `shot_NN_<屏id>.png` | 每屏一张（巡演模式）。**krkr 侧离屏导出**（`copyToBitmapFromMainImage` + `Bitmap.save`），不是屏幕截图，不依赖窗口是否在前台 |
| `ui_state.txt` | M2 状态（`tour_runs` / `last_screen` / `dialog_line` / `seen`） |
| `ui_flow_state.txt` | M4 流程图状态（`current` / `visited` / `collected`） |

### 判定"这一轮是否干净"的三个关键字

```
An exception occured    应为 0（引擎对**已 catch** 的异常也会打整段 dump，所以必须为 0）
redraw EXCEPTION        应为 0
[UI][MISS]              应为 0（缺件）
```

M8 修复后实测：以上三项均为 **0**，且 `截断文本 0 处`、`未知 kind 0 处`、`缩放元素 0 处`、
`包装器异常=0`、`转场 成功 17 / 失败 0 / 降级 0`。

### 转场（M8 实测结论）

- 规则遮罩用 **`ui/x_mask_rule000_full.png`（1920×1080，RGBA 带 alpha）**；
  `startup.tjs` 的 `UI_TRANS_RULE` 已由不存在的 `ui/rule000.png` 改成它。
  ★ M17 更名：满屏遮罩件原名后缀为 1280 基线时代遗留（实际已 1920×1080），现统一为 `_full`。
- 调用形式：`stage.beginTransition("universal", true, snap, %[ time: 420, vague: 64, rule: loc.name ])`
  （★ 2026-10-09 校准：**该语义已被 D-02 订正** —— `transsrc` 是**终点**（装新画面的那层），正确形态＝乒乓双缓冲 `stageLayer.beginTransition("universal", true, snapLayer, …)`，结束后引擎互换两层、由 `startup.tjs::uiTransSettle()` 结算；详见 `UI组交接编程组.md` §10.2。原句「`snap` = 旧画面快照层；目标层当前内容 = 新画面」已作废）。
- **实测：带 alpha 的 RGBA 遮罩可用**——19 次转场全部
  `[UI][TRANS] universal+rule OK : assets/ui/x_mask_rule000_full.png time=420 vague=64`，
  `失败 0 / 降级 0`，**crossfade 降级一次都没触发**。
  （引擎把 rule 图按 8bpp 灰度载入当阈值表，alpha 通道不参与；不会因 RGBA 而失败。）

---

## 六、演示台词来源（场景 id + 行号）

对话框屏的 28 条台词**全部是原版真实中文语料**，未自造。
数据源 `资源组\剧本\scene_ot.jsonl`（只读），由 `_工作\M2_证据\extract_demo_lines.py` 生成
`krkr\game\ui_demo_script.tjs`。下表即该文件里的 `UIDemoSceneId` / `UIDemoLineno`：

| # | 说话人 | scene_id | 行号 |
| --- | --- | --- | --- |
| 1 | 鹰志 | `ot_s01_01a` | 31 |
| 2 | 鹰志 | `ot_s01_01a` | 33 |
| 3 | 鹰志 | `ot_s01_01a` | 89 |
| 4 | 声音 | `ot_s01_02a` | 156 |
| 5 | 和马 | `ot_s01_02a` | 176 |
| 6 | 明日香 | `ot_s01_02a` | 1118 |
| 7 | 圣骑士霍克 | `ot_s01_02c` | 46 |
| 8 | 王女阿斯嘉 | `ot_s01_02c` | 97 |
| 9 | 独眼的库劳斯 | `ot_s01_02e` | 90 |
| 10 | 小鸠 | `ot_s01_03a` | 386 |
| 11 | 报道员 | `ot_s01_04a` | 671 |
| 12 | 京 | `ot_s01_04b1` | 121 |
| 13 | 车站广播 | `ot_s01_04c` | 10 |
| 14 | 藏人 | `ot_s01_04c` | 245 |
| 15 | 高内 | `ot_s01_04g` | 41 |
| 16 | 恩田 | `ot_s01_04i` | 68 |
| 17 | 温柔的声音 | `ot_s01_05a` | 22 |
| 18 | 鹫介 | `ot_s01_05b` | 77 |
| 19 | 电视播音员 | `ot_s01_13a` | 51 |
| 20 | 满夜 | `ot_s01_17a` | 58 |
| 21 | 狩男 | `ot_s02_02a` | 64 |
| 22 | 纪奈子 | `ot_s02_02a` | 341 |
| 23 | 泉 | `ot_s02_03b` | 460 |
| 24 | 三泽 | `ot_s02_11b` | 53 |
| 25 | 隼人 | `ot_s03_01a` | 15 |
| 26 | 艾七 | `ot_s03_02a` | 44 |
| 27 | 金发少女 | `ot_s03_03a` | 135 |
| 28 | 渡来 | `ot_s04_17b` | 459 |

选择肢文本（`dlg.choices.labels`）出自 `资源组\剧本\主线编排方案.md:257-286` 的 `ot_s01_02c`：
「为了国家与民众」「为了阿斯嘉公主」。

### 对话框屏的「演示背景」

`dlg.content` 是 layout 声明的**动态层**（`asset: void, dynamic: "story_background"`，静态框位 `0,0,1920,1080` = `content_boxes.ot`——★ D-04 2026-10-02 起六源一律全画布；krkr 端**没有** content_box 解析器，静态几何即引擎实际用框，真游戏由编程组 `ui_story.tjs` 运行期改写）。
留空时 `ui_widget.tjs` 会画「[占位] 动态层 dynamic:story_background」方块。
M8 起由 `ui_demo_script.tjs` 末尾的追加段填**真实素材**：

- 素材：`ui/tl2_bg1.png`（实测 800×600，与 ot 框位**逐像素 1:1**，不缩放）
- 角标：`dlg.bg_tag`，右上角小字「演示背景」（size 14，取自 `palette.text_small`）
- 备选：`ui/tl1_bg.png` 同为 800×600，但该图实测约 86% 是纯黑，视觉上只有顶部一条星空带；
  `ui/tl1_bg1.png` 是 1200×450，与任何 `content_box` 都不等，1:1 摆会越出框位。**不得自造图片。**

---

## 七、已知缺口（M8 结束时仍存在，非本次 6 项缺陷）

1. **存档 / 读档屏的槽位缩略图仍是占位**：`dynamic: "slot_thumb"` 的占位层没有真实缩略图（★ 2026-10-09 校准：旧记「16 处」作废 —— 现行＝两屏各 12 件 `sv.thumb1..12`、合计 **24** 个静态占位件；`dynamic` 仅见于 `note` 契约，见 `UI组_交付总纲.md` §六 第 3 项），
   屏上显示「[占位] 动态层 … 空」。演示工程里没有真实存档截图，需要编程组决定填什么。
2. **列表项文字贴左边框**：`save` / `load` / `config` / `music` 的列表项（★ M43：原列的 `chapter` 屏已删除），
   标签起点 = 项框左边缘（`uiWidgetDrawList` 里 `align:"left"` 时 `tx = ir2.x`），
   与九宫格左边框（13px）重叠，1:1 放大看首字仍完整，但缩略看像被切掉。
   要改得动 `layout\**` 的排版参数或 `uiWidgetDrawList` 的排版策略，超出本次范围。
   ★ M06（2026-09-24）**订正**：`backlog` 屏**已不在此列** —— 本轮该屏列表新增 `item_text`
   逐块文案区（块内局部 `x=219`，见 `layout\screens\26_backlog.json`），文字**已有内缩**，
   不再贴九宫格左边框。（`item_text` 缺省时仍走旧口径，故其余四屏不变。）
3. **音乐鉴赏的碟片框是灰色占位**：layout 里就是占位声明（"真值由编程组从素材库填充"）。
4. **`-assetdir` 未生效**（见 §三实测记录），所以素材必须复制进项目根。
5. 片尾歌词条 / 设置项数值等仍是「演示占位」文本，属布局层的既定占位。（★ ISSUE-20260928-07：`ending` 屏已删除 ⇒「片尾歌词条」占位不再存在；设置项数值仍为占位。）

---

## 八、已知行为：竖排快捷条的「展开态」两处代价

> ★ **M37（2026-09-23，`ISSUE-20260923-01`）已按新形态重算本节**：整条带 → 一排独立圆形 icon，
> 整条把手退场 ⇒ 两条的**数字与入口都变了**（原文的 4 344 px / 「点条体收起」已不适用）。
> 复算脚本：`_工作\M37_展开态点击分布.py`（1px 全扫描，可重跑；口径复用 `工具\test_click_reach.py`）。

**① 展开态仍有 1 650 px「点击穿透带」（M36 为 4 344 px，缩小 62%）** —— 点在带内会
**穿透到承载屏**（对话屏即「推进对话」，其它屏按各自热区），不触发竖条任何动作。

- 来源：项热区仍按 **75×73** 排布（x 从 1845 起 —— M34 的 1:1 复刻几何，M37 未改），
  12 项合计覆盖 **65 700** px；整列区域 `(1845, 7, 75×898)` = **67 350** px。
- 构成（实测分解，无零散余量）：**只剩 11 条项间缝（共 22 行 × 2 px）× 75 宽 = 1 650**。
  M36 的「左带 x1842..1844 × 898 行 = 2 694 px」**已随整条把手退场而消失**。
- 数据侧的代价已被 schema 承认（项热区与内容同尺寸、不额外扩张），**当前无守门校验**；
  实测分布见 `_工作\ISSUE-20260923-01_G2_证据\M37_展开态点击分布.txt`
  （12 项各 5 475 px、穿透带 1 650 px、**跨项吞并 0 px**）。
- ★ **处置结论（2026-09-23，主代理裁决）：保留现状，不修。** 要动它就得改**项热区几何**
  （扩高合并项间缝 / 抬 z / 加隐形补缝热区），而 75×73 是《交汇协奏曲》PSB `#rects` 的
  **1:1 复刻值**（M34 定的复刻口径），改它属**设计取舍**而非缺陷修复；且当前 1 650 px
  只占整列 2.45%，行为是「点缝＝剧情推进」，与「平时完全隐藏」的用户裁决不冲突。

**② 展开态没有「点条体收起」入口（M37 后更彻底）** —— M36 由 `vis_when=collapsed` 的整条把手
挡住；M37 起**整条把手已不存在**，且**收起态不再有任何可点热区**（点右端 = 穿透到承载屏的剧情推进）。
收起只能靠：指针移出 `out_x` 等 `delay_ms` 自动收起，或先解除钉住再移出
（`quick_pin` 切换 `reveal.pin_flag`）。**呼出的唯一鼠标入口 = 指针移到 x ≥ `reveal.in_x`（1842）**；
`open_sysmenu` 动作本身保留为**编程入口**（深链 / 附加层里 action 留空的 hit 兜底），
但数据里已无元素指向它，Esc 也不挂它（§七 H1 裁决）。
★ **M45（2026-09-23，用户裁定）**：`open_sysmenu` 曾指向的传统系统菜单屏 `sysmenu`
**已整体废除**（「已有药丸按钮系统」）⇒ 本动作**不再有任何屏语义**，只剩上述编程入口；
两端实现（`uiQuickbarOpen()` / `expandQuickbar()`）**一字未改**，快捷条行为不受影响
（M45 实测：收起态巡演 `quickbar 实绘元素=0`、展开态 `实绘元素=27`，缺件 0 / 转场失败 0）。

---

## 九、M38（`ISSUE-20260923-01`）· 对话框「完全无框」+ 文字「8 向描边」

> 用户裁决（2026-09-23）：对话窗按《月影魅像》式**无框**处理（实测该作对话框本质就是「没有框」，
> 文字直接压在画面上）。三项：① 完全无框；② 角色名一并去框；③ 删右下 9 功能图标九宫格
> （功能已由右端竖排快捷条覆盖）。工程记录与逐条证据见 `_工作\ISSUE-20260923-01_M38_证据\`。

### 9.1 新增字段（`layout/_schema.md` §四「`font.*` 阴影/描边三组字段」）

| 字段 | 缺省 | 语义 |
| --- | --- | --- |
| `font.outline` | `false`（默认关，**不影响任何既有元素**） | 真 ⇒ 用 `outline_color` 在 **8 个方向**各画一次同文本，**最后画正文** |
| `font.outline_color` | `@palette.shadow` | 描边色（本屏 `#000000`） |
| `font.outline_width` | `1` | 边宽 px（本屏 `2`）⇒ 8 向偏移 = 方向 × 该值 |

**落点**：`krkr/game/ui_theme.tjs` —— `uiThemeApplyFont()` 解析三字段（返回字典新增
`outline/outlineColor/outlineW`）→ `uiThemeDrawLine()` 在画正文前调 `uiThemeDrawOutline()`；
方向表 `UIThemeOutlineDirs`、缺省宽 `UIThemeOutlineDefaultWidth`。
**两端同实现**：HTML 侧 `复刻/replica.js` 的 `textOutlineShadow()`（8 条 `text-shadow`）**同序同向**，
改一处必须改两处。

**消费者（3 处，全部与正文同参数 `outline:2` + `outline_color:#000000` + `shadow:false`）**：
`dlg.text`（正文）、`dlg.name`（角色名）、★ `dlg.choices`（选择肢）。第三处是**视觉验收第一轮打回**后补的：
该件原只有单向投影，未高亮项白字压在白色羽翼上几乎消失（2px 邻域暗像素比例仅 13.9%）⇒
按同一判断改用描边；**高亮项的暖金字不特殊处理**（`uiWidgetDrawList` 只替换 `f.color`，outline 字段原样透传
⇒ 高亮项自动同得描边）。实测（同一口径脚本 `_工作\ISSUE-20260923-01_M38_证据\m38_choices_contrast.py`，
TOL=16 由 13.9% 反向标定）：标签排版盒 **20.0% → 67.3%**；只关掉 `outline` 的反向跑 ⇒ **16.9%**。

### 9.2 ★ 铁律：描边只影响渲染，绝不参与布局

`uiThemeWrap` / `uiThemeLayoutText`（折行、截断、对齐、定位）**完全不看** outline 字段 ——
与既有 `shadow` 同款「渲染层的事」。故 M25 的实测结论（w=1224 / size=42 / line_spacing=1.2 ⇒
4 行 0 溢出）在加 2px 描边后**逐字不变**。

### 9.3 验证（**同一份数据、只换渲染器代码**的逐像素 A/B）

做法：把 `ui_theme.tjs` 临时还原成 HEAD 版跑一次 `run_autotour.bat`，恢复 M38 实现后再跑一次；
两次的 `shot_03/04_dialog.png` 用 `_工作\ISSUE-20260923-01_M38_证据\m38_ab_outline_pixels.py` 比对
（A 侧 = 旧渲染器、B 侧 = M38 新实现）：

| 断言 | 实测 |
| --- | --- |
| ~~`dlg.hint`（既有 `shadow:true` 文本）逐像素不变~~ | 差异 **0 / 44 800 px**（最大差值 0）。**⚠ 该断言的「主语」已不存在**：**`ISSUE-20260929-05`（2026-09-29 · 用户「对话框页：删除 `dlg.hint`（不需要操作提示）」）已把该元素整体删除** ⇒ 本行**仅作 M38 轮的历史留痕**，不可再复跑（欲复核 M38 的描边隔离结论，请改用同表其余行，或选该屏现存的 `shadow:true` 文本 **`dlg.mode_tag`** 作对照） |
| `dlg.choices`（既有 `item_frame` 九宫格框 + 高亮块 + 阴影字）逐像素不变 | 差异 **0 / 162 800 px** |
| `shot_04` **除名字/正文矩形外**全图不变 | 差异 **0 px**（包围盒 None） |
| `dlg.name`（本屏新开 `outline:2`）出现差异 | 差异 2 978 px，最大差 255 ⇒ 描边确实生效 |
| 正文压在描边之上（本体不被改写） | 离字形边缘 ≥1px 的填色像素 **100%** 逐通道一致；外侧抗锯齿带 11 px 并入描边（2.1%，属描边渲染的固有代价） |
| 描边不外溢 | 名字框 上/左/右 ±6px 带内、±4px 之外差异 **0 px** |
| 全 26 屏巡演 | `EXCEPTION` **0**；dialog 屏 元素数 27 → **8**（7 件 + 演示脚本注入的 `dlg.bg_tag`）、实绘 16 → **6**（选择肢展开态 7）；缺件 0、占位 0、未知 kind 0；PNG 导出 26/26 |

> ⚠️ 判据取舍两条（写在脚本里，避免误报）：① 填色比较用逐通道 ±2（±8 会把外侧抗锯齿带算进来，
> 虚报 3%）；② 越界检查只看**上/左/右**三侧 —— 名字框下沿 y=803 与 `dlg.text` 首行（y=806 起、
> 自带描边）只差 3px，正文自己的描边落在名字框下方带里，那是**它的**描边，不是名字外溢。
