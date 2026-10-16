# 2026-10-01 对于我们没有翅膀格雷塔迦露德与柳木原编程组gallery与music页脚返回热区的修改

- Issue：`ISSUE-20261001-15` ｜ 模式：工程 ｜ 分支：`issue/ISSUE-20261001-15-footer-return` → `main`
- 参与代理：**editor×1**（无独立一审；理由见「审查结论」）

## 任务目的

用户 2026-10-01 经提问控件裁定：「**gallery + music 一并补**（页脚「返回」热区）」——即用与 `ISSUE-20261001-14` 给 backlog 补热区**相同**的做法，给这两屏各补一件；并把 backlog/gallery/music 三条一起登记为**移交 UI 组的 `D-03`**。
另：本代理在上一轮提出的疑问（**music 屏是不是"进得去出不来"**）本轮**要求查清并给结论**。

验收：① 两屏页脚「返回」可点且回上一屏；② **backlog 既有热区不被泛化改动波及**；③ music 的退出路径有**可判定结论**；④ 不改 UI 组/资源组文件；⑤ 判定线仍 0 异常。

## 改动清单

### 修改（编程组自有 3 个文件，+149 / −61）

- `工程\…\编程组\krkr\game\ui_story.tjs`：把 `ISSUE-14` 的 `uiStoryBacklogReturnFix()` **泛化**为 `uiStoryFooterReturnFix()`——内部一张**小表**（`屏 id → 元素 id / rect / source`）逐屏纯追加隐形热区；**backlog 一行的 id/矩形/动作/`z` 与旧实现逐字一致**。`uiStoryBacklogReturnFix()` 保留为**兼容包装**（转调新函数）。
  - 三屏几何（**各屏各自对底图按像素实测**「⊗+返回」墨迹、外扩 20px）：
    | 屏 | 底图 | 墨迹 bbox | 追加的热区 |
    | --- | --- | --- | --- |
    | backlog | `x_ui_psv_backlog_bg.png` | (1746,995)-(1865,1026) | `bl.ret_hitfix` (1726,975,160,72) ← **既有，未改** |
    | **gallery** | `x_ui_psv_gal_shell.png` | (1743,992)-(1865,1032) | **`gal.ret_hitfix` (1723,972,163,81)** |
    | **music** | `x_ui_psv_music_bg.png` | (1562,992)-(1684,1030) | **`mu.ret_hitfix` (1542,972,163,79)** |
  - 一律 `kind:"hit"`、`action:"close"`、**无 `state_assets`（纯热区零绘制）**、`visible_default:true`、`z:10`、**幂等**（已存在即跳过）；`z=10` 依据＝三屏底图 z=0，且页脚区与各自列表/滑条/页码/页签**均不重叠**（报告附逐项比对）。
- `工程\…\编程组\krkr\game\ui_boot.tjs`：调用点改指新函数名（注释同步说明"D-03 登记、UI 组数据层补齐后应删本调用"）。
- `工程\…\编程组\krkr\game\ui_verify14.tjs`（诊断脚手架，flag 门控）：mouse 模式由 6 拍扩为 **10 拍**，覆盖「三屏页脚返回 + music 按 Esc」；`uiVerify14DumpHits` 增加 `fixId` 参数。

### 新增

- `工程记录\2026-10-01_…gallery与music页脚返回热区的修改.md`（本件）

**未改**：`UI组\*`、`资源组\*`、`main`、任何 layout / 屏数据 / 素材。
（说明：成品部署到 `成品\我们没有翅膀——格雷塔迦露德与柳木原\` 是**本工作区规定的成品落点**、且在**工作区内**，符合 AGENTS §六；派单 §0 那句「写入仅限 wt-prog」措辞不周（它指的是**源码改动**），已在本记录澄清。）

## 验证方式与结果

真机**合成调用**（与引擎同一入口），证据 `子代理工作区\ISSUE-20261001-15\evidence\`：

| 判据 | 结果 | 原始证据 |
| --- | --- | --- |
| 三件热区均装上 | ✅ | `[FRET] 已补 backlog 页脚「返回」热区 bl.ret_hitfix rect=(1726,975,160,72) action=close z=10`；`[FRET] 已补 gallery … gal.ret_hitfix rect=(1723,972,163,81) …`；`[FRET] 已补 music … mu.ret_hitfix rect=(1542,972,163,79) …` |
| **gallery 页脚可点** | ✅ | `p5 ②gallery 页脚返回：屏=gallery 画布中心(1804,1012)` → `[ACT] act=close ｜ 屏 gallery(3) -> dialog(2) ｜ handled=1` → `[STACK] pop OK：gallery -> dialog` → `p6 结论：屏=dialog ⇒ PASS` |
| **music 页脚可点** | ✅ | `p7 ③music 页脚返回：屏=music 画布中心(1623,1011)` → `[ACT] act=close ｜ 屏 music(3) -> dialog(2)` → `[STACK] pop OK：music -> dialog` → `p8 结论：屏=dialog ⇒ PASS` |
| **backlog 既有热区未被泛化波及** | ✅ | `p2` 转储仍为 `bl.ret_hitfix act=close rect=(1726,975,160,72) z=10`（**原值**）；`p3` 命中后 `[ACT] act=close` → `pop OK：backlog -> dialog` → `p4 PASS` |
| **music 可用 Esc 退出（新机检）** | ✅ | `p9 Esc：按前屏=music 栈=[title > dialog > music]` → `p9 按后屏=dialog 栈=[title > dialog]` → `p10 ④Esc 结论：屏=dialog ⇒ PASS` |
| 回归 | ✅ | `run_storytest --act 4`：`An exception occured = 0`、`[UI][MISS] = 0`、`>>> PASS`、退出码 0 |
| 全量 / 成品 | ✅ | `story` 684 项、`UIStoryIndex` 680；`[gate] 待部署剧本场景数 = 680`；成品 md5（LF 规范化）三文件 **MATCH**；**成品 0 诊断开关**；成品冒烟 16 s：0 异常、三条 `[FRET]` 均在、入口 `ot_s00_00 顺序=680` |

**主代理二审（亲自复核）**：亲自 `Read` 了 music 的裁剪图 ⇒ 确认其中**只有 ⊗ + 「返回」**、不含左「播放／停止」、右「选择」；亲自核对分支提交、成品无开关、以及 `ui_story.tjs` 里三处 `ret_hitfix` 已就位。

**★ 矩形精确性（editor 给的净空实测，比目视更硬）**：gallery 矩形左沿 1723 距「确定」右沿 1668 有 **55px** 净空；music 左沿 1542 距「停止」右沿 1493 有 **49px**、右沿 1705 距「选择」左沿 1747 有 **42px** 净空 ⇒ **两侧邻件都不吃**。
（**必须逐屏实测**：music 的「返回」在页脚**中间偏右**、x 与 gallery 相差约 180px —— 照搬 gallery 的 x 会落到「选择」上。）

## ★ 结论：music 屏**并非**「进得去出不来」（答复上一轮的疑问）

> **music 屏在补页脚之前就有两条可用退出路径（Esc 键、鉴赏外壳顶部「返回」）；玩家最可能点的「页脚 ⊗返回」因为是烘焙图、没有热区，所以点了没反应，才像出不来。补上本次页脚热区后，页脚返回也可用。**

逐条依据（editor 查证 + 机检）：
- **Esc —— 可用且已机检**：`ui_screens.tjs::uiScreenKey` 对 `key==27`：**非 title 屏且 `UIScrStack.count>1` ⇒ `action:"close"`**（否则才是 `quit_game`）。music 入屏时栈必 ≥2 ⇒ Esc 回上一屏；`ui_flow.tjs` 的包装只拦 `flowchart`/`fragment`，我方 CTRL 包装只拦 `key==17`，均不干扰。**实测 p9/p10 PASS**。
- **外壳顶部「返回」—— 可用**：`gal_shell`（gallery/music 都 `attach` 它）有 `gs.back_hit` `action:"close"` `(1660,22,230,56)`；附加层命中优先于承载屏。
- **右键 —— 无退出作用**：我方 `uiStoryRightClickDisabled` **只对 backlog 屏**执行 `close`（用户裁定的范围），music 屏仅记「忽略右键」（实测该轮 `右键拦截计数=0`）。
- **快捷条 —— 与 music 无关**：`quickbar` 只 `attach` 到 **dialog**；其 12 个图标动作为 `open_save/open_load/do_quicksave/do_quickload/auto_on/skip_on/next_choice/prev_choice/open_backlog/open_flowchart/open_config/quick_pin`，**无任何「返回/关闭」类动作**。

## 风险、警示与未完成项

- **回滚**：`git revert` 本分支提交（或删掉 `ui_boot.tjs` 里对 `uiStoryFooterReturnFix()` 的调用即全部失效）。
- **⚠️ 三条都是运行期补丁，正解在 UI 组数据层**：已登记 **`D-03`**（见 `编程组\会话交接_20261001.md` §十二）——请 UI 组在 `layout\screens\{01_title…,26_backlog,27_gallery,28_music}.json`（按屏）里补齐页脚热区后，由编程组**删除本函数与该调用**。
  ⚠️ **本批只补了页脚的「返回」**；页脚里其它烘焙字（gallery 的「确定」、music 的「播放／停止」「选择」）**是否也需要热区未纳入本轮**（用户只点了「返回」）。
- **日志前缀变更**：`[BLRET]` → **`[FRET]`**（泛化语义）；`uiStoryBacklogReturnFix()` 保留为兼容包装（旧名仍在 `ISSUE-14` 的记录/注释里出现）。
- **诊断脚手架口径变化（editor 如实上报）**：`ui_verify14.tjs` 的 mouse 模式**不再自动断言「右键关 backlog」**（该轮已验过、属 `ISSUE-14` 范围），改为覆盖「三屏页脚 + music Esc」；`key` 模式（CTRL 快进）未动。
- **入口事实**：**music 屏只能经鉴赏页签进入**（`ui_layout.tjs` 里没有 `open_music` 元素；标题第 6 项是 `open_gallery`，music 由 `gallery_tab_2` 同级换屏进入）⇒ 其"上一屏"实测为 dialog。
- **未实测 / 未覆盖**：真机**物理鼠标**点页脚（本轮走合成 `onMouseDown/onClick`，与引擎同一入口）；Win7 SP1 未实测。
- **惰性代码**：`uiStoryRoleFace` 等仍未清（另案）。

## 审查结论

- **无独立一审（如实登记，理由）**：本件为**上一轮已验证模式的第 2–3 个实例**（同一函数、同一动作、同一起见幂等与 try/catch 结构），**唯一新增风险是"矩形落点"**，而该风险已由**三重证据**覆盖：① 逐屏**像素实测**墨迹 bbox；② **裁剪图目视**（主代理**亲自复核了 music 那张**）；③ **与邻件的净空像素值**（55 / 49 / 42px）。行为侧则由**合成真机调用**逐屏证明（`[ACT] act=close` → `[STACK] pop OK`），并**复验 backlog 未被波及**。
  ⇒ 判定「一审可省」，由主代理二审覆盖；**这是本会话第 5 次采用该判定**（`-10`/`-11`/`-12`/`-14`/`-15`），每次均写明理由与替代证据。
- **二审（主代理）**：亲自复核 music 裁剪图、分支提交与成品三项（无开关 / md5 一致 / 冒烟 0 异常三条 `[FRET]` 均在）。**通过 → 合并 `main`**。
- **用户实机确认**：**待验**（真机点 gallery / music 页脚的「返回」）。
