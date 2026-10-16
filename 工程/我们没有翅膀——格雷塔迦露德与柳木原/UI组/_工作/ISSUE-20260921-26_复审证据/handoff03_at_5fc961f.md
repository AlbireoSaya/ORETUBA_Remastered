# UI 组 · 会话交接（2026-09-22 · 03）· **按钮文字 与 图标↔文字组绑定**

> **本文件是接手的唯一入口。** 先读本文件 §〇–§四，再按 §七 读必读文件。
> 上一份：`会话交接_20260922-02_按钮文字素材交付.md`（**仍必读**：编辑器导出收件目录约定、组绑定初版、编辑器「居中」）
> 再上：`会话交接_20260922_按钮文字生成.md`（按钮文字的任务书 + 方框脚手架方案，**仍必读**）
> 再上：`会话交接_20260921_系统屏重置.md`（M31–M34 历史）
> 再上：`会话交接_20260920_UI组.md`（M1–M28 血泪教训）

---

## 〇、一句话状态与恢复入口

**《我们没有翅膀——格雷塔迦露德与柳木原》UI 组：标题菜单已做成「图标 + 中文文字」并完成悬停/按下**组绑定**（悬停任意一者两者同步换态），全库**三态素材口径统一**；期间按用户裁定做了**一次类级修复**（10 处「热区拉伸态图」→ 保热区 + 态图挪到 1:1 image）与**两轮独立审查的处置**（一审打回、二审打回，均已逐条处理）。**

| 项 | 值 |
| --- | --- |
| 分支 | `issue/ISSUE-20260921-26-greta-ui-rebuild` ｜ HEAD **`021d950`**（本分支自 `2b101cf` 起共 **38** 个提交） |
| `main` | **`4c1eb7c`** — **本分支未合并**（用户要求「先看 HTML 效果再决定」） |
| worktree | **`临时\wt-ui26`**（主工作树当时停在资源组的 `issue/ISSUE-20260918-06-greta-res-phase2`，故另开 worktree，**未切分支**） |
| 素材 | `UI组\krkr\assets\ui\` **435 件 / 39.64 MB**（预算 56） |
| 布局 | `UI组\layout\screens\` **21 个 json**（20 屏 + `_index.json`） |
| 校验 | `verify_ui.py` **六项全绿** ｜ 自测 A **17 条 ALL PASS** ｜ 自带套件 B **24 PASS / 1 SKIP / 0 FAIL = OK** |

### ★ 两条必须遵守的约定

1. **编辑器导出收件目录固定**：用户用 `复刻\editor.html` 摆版后导出到
   `工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\编辑器修改区\`。
   **用户说「应用我的修改」时只从这个目录取**（不得自己推断改动、不得从别处搜）。
2. **改完编辑器页面前必须刷新**：`state_group` / `state_assets` 是写进 `layout/screens/*.json` 的；
   若编辑器页面用的是**旧** `ui_layout.js`，导出会把这两项**静默抹掉**。
   入库工具已加守门（见 §三.8），但**请提醒用户先点「重载」或刷新页面**。

---

## 一、本轮做了什么（按工程记录）

| 记录 | 内容 |
| --- | --- |
| `-01` | 按钮文字**常态 35 件**（7 词 × 2 批次 × 3 层）。**方案 = 方框脚手架**：一张 1024×1536 竖版图，7 行 × 一行一词 × 每字一个方框，模型 `gpt-image-2.5-sunburst`；字高极差 13%–45% → **行带层 0px** |
| `-02` | 悬停/按下**两态 28 件**（程序化派生）+ `_工作\M35_悬停按下态_代码缺口诊断.md`（逐条 `文件:行` 取证） |
| `-03` | 悬停**调亮 + 加白色光晕**（实测查明：字形填充已 ~90% 白，**往白里混没有余量**，权重改压在白晕上）；用户取消「点击态图」⇒ 删 14 件 `_press`（配方保留在脚本，开关 `MAKE_PRESSED`） |
| `-04` | **悬停/按下态代码修复**（两端统一规则表 + `verify_ui` **静默缺陷** + 编辑器三态槽）；**一审回执** |
| `-05` | **应用用户标题屏导出** + **`state_group` 组绑定**（图标↔文字）+ 编辑器**「居中」**；顺带修掉**编辑器往返解析掉 `@palette.*`** 的缺陷（工具侧还原 + 守门） |
| `-06` | **一审打回处置**（组注册表泄漏 / 调色板真丢 2 处 / 12px 死区）+ **10 处热区拉伸态图类级迁移** + 补按下图；**二审回执处置**（见「补记二」） |

两次审查都判**打回**，都已逐条处置；**处置本身仍未再送一轮独立一审**（见 §五 待办 1）。

---

## 二、★ 当前数据契约：状态机（**改任何一端都必须同步另一端**）

### 2.1 规则表（7 条，krkr 与 HTML 复刻必须逐条一致）

| # | 规则 |
| --- | --- |
| ① | 左键在元素上按下 → 该元素进入按下态（**同一时刻至多一个**） |
| ② | 左键抬起（不论位置）→ 清除 |
| ③ | 指针移出该元素 → 清除 |
| ④ | 换屏 → 清除（HTML 侧**同屏重渲染也清**——DOM 重建，不清会留悬挂引用） |
| ⑤ | 绘制优先级 **pressed > hover > normal**，缺键**按段位向下逐级回落**（按下 → pressed/hover/normal；悬停 → hover/normal） |
| ⑥ | **组绑定**：带同一 `state_group` 的元素**共享** ①–③ 的结果（悬停/按下任一方 ⇒ **全组**换态） |
| ⑦ | HTML 侧另有**被遮挡交互元素兜底**：点击落在非交互元素上时，用命中栈找到被遮住的 `[data-ui-interactive]` 并派发（与 krkr 的几何扫描同口径） |

### 2.2 字段契约

```jsonc
{
  "kind": "image" | "hit",           // state_assets 不再只属于 hit —— image 也能带三态
  "state_assets": {                  // 缺键按 §2.1 ⑤ 逐级回落
    "normal": "ui/x.png",
    "hover":  "ui/x_on.png",
    "pressed":"ui/x_press.png"
  },
  "state_group": "title.menu_start"  // 同组元素共享悬停/按下；留空 = 不参与组
}
```

**参与状态检测的元素**（`uiScreenHoverAt` 的判据，**已收紧过一轮**）：
> 「**带 `state_assets` 的任何元素**」∪「**带非空 `state_group` 的 hit**」

- 前半句：`image` 也能带三态（文字按钮靠这个），且组绑定要求鼠标落在它上面也被检测到。
- 后半句：热区迁移后退回**纯热区**（不持有美术），但仍须是状态目标 —— 否则「悬停整条消息行」点不亮旁边的图标。
- **纯热区（既无态图又无组）不参与** —— 消掉「声明更晚的无组热区抢走有组热区」这类风险，也省掉无谓的整屏 redraw。
- `visible_default: false` 的元素**一律跳过**（本库配置屏 121 件里 35 件如此 —— 五组滑条 / 静音行 / 试听行是**整行关掉**的；审查曾据此误报一处「反馈丢失」，见 §三.6）。

### 2.3 两端实现位置（**改一处必改另一处**）

| 端 | 文件 | 关键函数 |
| --- | --- | --- |
| krkr | `krkr\game\ui_screens.tjs` | `uiScreenHoverAt`（判据 + 平票）、`uiScreenPressUpdate/Clear`、`uiScreenHoverUpdate`（规则③）、`uiScreenCtx`（`hoverHit/pressHit/hoverGroup/pressGroup`） |
| krkr | `krkr\game\ui_widget.tjs` | `uiWidgetStateGroup/StateFlags/StateAsset`（选图）、`uiWidgetDrawImage` 与 `uiWidgetDrawHit` **共用 picker** |
| krkr | `krkr\game\ui_dialog.tjs` | `uiDialogBuildCtx` **必须与 `uiScreenCtx` 同口径**（对话框屏不走 uiScreenCtx） |
| krkr | `krkr\game\startup.tjs` | `onMouseDown`（左键**只置状态、不做动作**）、`onClick`（**在早退之前**清按下态） |
| HTML | `复刻\replica.js` | `attachStates/attachStateEvents/stateImagePainer/stateNinePainer/pickState`、`resetStates`、`groupSync`、`interactiveUnderPoint` |
| HTML | `复刻\replica.css` | `:hover/:active` 叠色**只对无态图无组的热区**生效（`.ui-hit-hasstate` 排除） |

**模型差异（有意，结果必须相同）**：krkr 是**每帧由 ctx 重算**；HTML 是**DOM 事件 + 组内广播**（`ownHover/ownPress` 与生效态 `effHover/effPress` 分离，见 `groupSync`）。

---

## 三、★★ 本轮踩到的坑（**比结论更值钱，务必先看**）

1. **`.bat` 必须是 GBK + CRLF**：cmd 按 OEM 码页（936）读 .bat —— UTF-8 中文注释 → `'p' 不是内部或外部命令` 刷屏；LF-only 行尾 → 同样症状。与既有 `run_autotour.bat` 同口径。生成器：`工具\lyai-image-api\_mk_pressbat.py`。
2. **命令行参数在本引擎版本读不到**：对照实验（`-autotour=1` 并抽掉 `autotour.txt`）——引擎把它记入「已声明设置」，但 `System.getArgument` 返回 void ⇒ `autotour = OFF`。
   ⇒ **一切「外部开关」只能走项目根 flag 文件**（`autotour.txt` / `press_probe.tjs`）。README 里「方式① 命令行」已标注实测不可用。
3. **按下态验收探针**：`krkr\run_pressprobe.bat`（`set PROBE=<元素id>`，约 45 秒自行退出，**会开一个窗口**）→ 把 `UIScrPressProbe` 写进项目根 `press_probe.tjs`（用已验证的 `Scripts.execStorage`）。默认关闭、零影响。
4. **⚠️ 探针天然绕开 `uiScreenHoverAt`**（它直接写 pressHit）⇒ **「某个元素能不能被状态检测命中」这类缺陷，探针与截图都发现不了**。为此新增数据级守门 **`工具\test_state_targets.py`**（复算判据与平票规则，断言 25 个「态图+组」可见元素在自己几何中心都可达）。**改判据/z/声明序后必跑它。**
5. **`ImageFilter.MaxFilter(1)`（半径 0）会把 Python 解释器硬崩**（无输出、退出码 127）⇒ `btn_states.hover(im, 0, 0)` **不可用**；要「只提亮不扩光晕」请内联配方（见 `_工作\M35b_选择支悬停图.py`）。
6. **别把「看起来不对」当缺陷描述**：我曾把 `bl.spk_hit` 的 1222×224 说成「热区画错尺寸」，实为 **PSB 原值**（`#rects/speaker` = 整条消息行可点）⇒ 让用户基于错误事实做了裁决，实施时才发现并重新取得裁定。**给选项前先查清「这个值是从哪来的」。**
7. **同理：审查也会误报**。二审 Major-1（配置屏静音勾选框反馈被吃）**误报** —— 它没查 `visible_default`（那三件本就 `false`，整行关闭）。**收到审查意见要先用数据复算，再动手。**
8. **编辑器往返会解析掉 `@palette.*`**（`gen_layout.resolve_deep` 把引用解析后写进编辑器唯一数据源 `复刻\ui_layout.js`）⇒ 每次「导出→入库」都抹掉一层调色板间接层。**已在入库工具侧修**：`verify_editor_export.py` 的 `restore_palette_refs`（**按 `id` 配对**，不是下标）+ **守门**（`@palette.` 引用数只许持平/增加、元素不得丢 `state_group/state_assets`，违反即拒绝入库，`--allow-drop` 放行）。**根治仍待办**（让编辑器拿到未解析源）。
9. **两套自检都要跑**：
   - **A** `复刻\_selftest_states.html`（本轮维护，17 条覆盖规则①–⑦）—— 无头 `--dump-dom` 读 `SELFTEST`
   - **B** `复刻\index.html?selftest=1`（M15 期自带，24 条）—— 读 `RESULT=OK/NG`
   ⚠️ **只跑 A 不够**：本轮我为「纯热区不挂状态机」误写 `return d` 提前返回，**跳过了 `buildHit` 后半段的标签与 click 监听 ⇒ 所有纯热区点击失效**，正是 **B 当场报出 4 条 `sysicons.*`** 才发现。
10. **别写恒真断言**：B 里原有 `state.history.length === state.history.length`（自比永真，`h0` 从未使用）；**也别硬编码计数**（`=== 13` 这类 —— 数据一变就假失败，本轮正栽在这上面）。
11. **shell heredoc 引号地狱（本会话反复中招）**：`python - <<'PY'` 或 `python -c "..."` 里的 `\U`/`\M` 转义、嵌套引号、`%` 都会被搞坏（表现为无输出、rc=127、或断言神秘失败）。**写脚本一律用 Write 工具落文件再 `python <文件>`**，别在 shell 里内联长代码。
12. **krkr 的 `krkr.console.log` 是追加式**：从别处复制来的 runtime 会把**别人的启动块**一并带进来（本会话就在日志里遇到另一 worktree 的失败启动 + `-autotour=1` 尝试）。判读时按时间戳取自己那次。
13. **`临时\` 清理要确权**：只删本次任务自己创建的目录（本会话的 `临时\wt-ui26\临时\*`、`临时\edge_m35*`）。

---

## 四、验证基线（**改完必跑**）

```bash
cd "E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"

# 1) 生成 + 六项硬校验（唯一真相源 → 三处生成物）
cd 工具 && python gen_layout.py && python verify_ui.py        # 退出码须为 0
# 2) 两道数据级断言
python test_verify_asset_refs.py      # 引用表覆盖 state_assets（含非字典异常）
python test_state_targets.py          # 「态图+组」元素的悬停可达性（25 个全可达）
# 3) 两套浏览器自检（无头 Edge；--user-data-dir 用 临时\ 下自建目录，用完清）
EDGE="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
"$EDGE" --headless=new --disable-gpu --no-sandbox --user-data-dir=<临时> --hide-scrollbars \
  --window-size=1400,900 --virtual-time-budget=12000 --dump-dom "<UI组>/复刻/_selftest_states.html"   # SELFTEST ALL PASS
"$EDGE" --headless=new --disable-gpu --no-sandbox --user-data-dir=<临时> --hide-scrollbars \
  --window-size=1400,900 --virtual-time-budget=20000 --dump-dom "<UI组>/复刻/index.html?selftest=1"     # RESULT=OK
# 4) krkr 实机（会开窗口、约 45 秒自行退出；探针用元素 id）
cd ../krkr && set PROBE=title.menu_hit_1 && run_pressprobe.bat
#    日志在 <worktree>\临时\ui_run_press\runtime\savedata\krkr.console.log（UTF-16LE，追加式）
# 5) 编辑器导出入库（先备份→覆盖→生成→校验→结构 diff；含调色板还原与守门）
cd ../工具 && python verify_editor_export.py --from "../编辑器修改区"
```

**当前结果**：全部通过。素材 435 件 / 39.64 MB；`verify_ui` 770 引用 / 301 image（271 九宫格）/ 三处 17162 键一致。

---

## 五、本轮裁决与待办

### 已裁决（2026-09-22，用户经提问控件裁定 —— **不再需要重问，直接照此落地**）

| # | 事项 | 裁决 | 落地要点（接手照做） |
| --- | --- | --- | --- |
| 1 | **配置屏 4 个页签（画面/声音/文字/系统）的内容同屏全画**，真实可见重叠：「全部跳过」压「角色预览箭头」176×19、「文字速度」压「角色预览」131×31、「文字变色」压 char2 146×8 | **实现页签切换** | ①给 config 屏 **121 个元素逐一标「归属页签」**（下方 §五.1 有起点表，须按 PSB 组层核对定稿）；②krkr（`ui_screens.tjs`）与 HTML（`replica.js`）两端实现按页签的可见性；③`config_tab_1..4` 动作名已留在 `cfg.tabN_hit.action`，接线归编程组；④改后重跑巡演截图 |
| 2 | 「声音」页 **35 件**（背景音乐/音效/系统音/语音/自动播放速度/角色音量 **六组滑条** + 静音行 + 试听行）`visible_default:false` | **全部启用** | 随「声音」页出现；`visible_default` 改为随页签决定；**滑条需实现拖动**（krkr 侧拖拽语义见待办 4，本工程未实测，须先验证再写）；旋钮 `slN_knob` 行程＝`slN_rail`（sl1..sl5 x307..671、sl6 x1174..1538），`slN_bar` 是静态底图 |
| 3 | 标题菜单 **7 个图标**的 `state_assets.pressed` 直接复用悬停图（`x_ui_menuicon_*_on.png`），而 7 条文字已有专用 `_press.png` | **另出 7 张图标按下图** | 复用既有生图脚本与配方（`_工作\M35_生图提示词存档.md`）；产出后把 7 个 `title.menu_hit_N` 的 `pressed` 换成专用 `x_ui_menuicon_*_press.png`；入库后 `verify_ui` + 巡演复核 |
| 4 | `临时\` 累计占用（历次 `ui_run*` 整份复制 + 本会话 worktree） | **只清本会话创建的** | 已删 `临时\ui_run_press`；`临时\wt-ui26` 是本分支**唯一检出**（分支未合并），保留到合并或用户另行指示 |

### 五.1 配置屏页签归属（**起点表，须逐条与 PSB 组层核对后定稿**）

数据来源：`layout/ui_layout.json` 的 `screens.config.elements`（本轮实测）。PSB 侧权威依据＝
`_工作\M34_交汇协奏曲UI布局规格.md` §「idx 80 · 配置・设定」的组层表：`サウンド設定` / `システム設定` /
`キャラセット` / `タブ` / `slider` / `mute` / `再生`——**按组层定页签比按文字猜可靠**。

| 页签 | 元素（id 前缀） | 文字（`sample`） |
| --- | --- | --- |
| 画面 `tab1` | `cfg.window_*` `cfg.full_*` `cfg.on*` `cfg.off*` `cfg.it_facewindow*` `cfg.it_drama*` `cfg.it_effect*` `cfg.it_curhide*` `cfg.it_cfmovie*` | 窗口模式 / 全屏模式 / ON / OFF / 立绘窗口 / 演出效果 / 特效 / 隐藏光标 / 播放影片 |
| 声音 `tab2` | `cfg.sl1..sl6_*` `cfg.mute_*` `cfg.replay*` | 背景音乐 / 音效 / 系统音 / 语音 / 自动播放速度 / 角色音量 / 静音 /（试听，无文字） |
| 文字 `tab3` | `cfg.textspeed_*` `cfg.autospeed_*` `cfg.charset` `cfg.charrow` `cfg.char1..12` `cfg.preview` | 文字速度 / 自动播放速度 /（角色格 ×12，无文字） |
| 系统 `tab4` | `cfg.it_voicecut*` `cfg.it_savedialog*` `cfg.it_loaddialog*` `cfg.it_allskip*` `cfg.it_textcolchg*` `cfg.sys_game*` `cfg.sys_title*` `cfg.sys_end*` `cfg.hit_reset` | 语音截断 / 存档对话框 / 读档对话框 / 全部跳过 / 文字变色 / 返回游戏 / 返回标题画面 / 退出游戏 |
| 全页常驻 | `cfg.dim` `cfg.tab1..4*`（4 个页签本体与热区） | 画面 / 声音 / 文字 / 系统 |

⚠️ 三处**跨页冲突**正是登记的重叠根因，做页签时优先核对：`it_allskip`（系统页 y481）×
`charrow`（文字页 y261..）／`it_textcolchg`（系统页 y541）× `char2`（文字页 y592）／`textspeed_lb`
（文字页 y315）× `charrow`。**它们属不同页签 ⇒ 页签一切换即互不共存，坐标不用改。**

⚠️ 隐藏的 `sl1..sl5`（x244..864）与可见的 `it_*` 开关行（x619..875）**同带重叠**（如 `sl1` y298 与
`it_facewindow` y301、`sl5` y898 与 `it_loaddialog` y901）——同样由页签（声音页 vs 画面页）分开，改页签即解。

### 已裁决（续，2026-09-22）：系统菜单改为「右端呼出的竖排快捷条」

用户提问：「参照《月影魅像》和《交汇协奏曲》那样平时隐藏、鼠标放到屏幕右端呼出的竖排 icon 菜单，
而不是现在的传统式菜单，可以实现吗？」→ **可实现**。三项裁决（经提问控件）：

| # | 事项 | 裁决 |
| --- | --- | --- |
| 1 | 与现有传统菜单 `sysmenu` 的关系 | **竖条替换传统菜单**（游戏内改右端呼出；标题屏保留标题自己的菜单；旧 `sysmenu` 素材保留不删；需改动作接线与巡演步骤，并重跑 23 屏验收） |
| 2 | 竖条项目集 | **用现成 12 项**（锁定／存档／读档／快速存档／快速读档／自动播放／快进／下一选项／上一选项／回想／流程图／设置）——其中 10 项动作已有，**「锁定」「下一选项」需新增** |
| 3 | 展收形态 | **淡入淡出 + 收起留 slim 把手**（复用现有转场；素材现成） |

**已核实的事实（开工前不必重查）**：

- `quickbar` 屏（28 件）＝《交汇协奏曲》PSB idx 81「系统菜单快捷条」的 1:1 复刻：竖条 x=1845 w=63、
  标签列 x=1665 w=197、12 项热区 75×73（y 步 75）、`quick.hit_toggle`(1842,7,78×898) 已预留整条把手热区。
  **当前只有数据、无任何代码引用（未接线）**。
- 两态素材已在盘：`x_ui_quick_slim_{off,on,over}.png`(63×513) 收起把手／
  `x_ui_quick_full_{off,on,over}.png`(63×888) 展开条／`x_ui_quick_tips.png`(197×876)；
  原作 7 张原图在 `临时\cc_psb\81\`。**无需新生图**。
- 引擎能力齐备：`onMouseMove(x,y,flags)` 已给出**画布坐标**（`startup.tjs:575`）⇒ 贴边判定可做；
  Timer 有先例（必须持引用）；`sysicons` 是 `overlay:true` 屏，`uiScreenDraw` 已有「先画下层再画浮层」
  分支 ⇒ 竖条可浮在剧情画面上。
- **动作覆盖 10/12**：`do_save`／`do_load`／`do_quicksave`／`do_quickload`／`auto_on`／`skip_on`／
  `prev_choice`／`open_backlog`／`open_flowchart`／`open_config` 已有；
  **缺「锁定」（＝钉住不自动收起，正是本交互自带的新状态）与「下一选项」（现有只有 `prev_choice`）**。

**要新建的四项（与风险）**：

1. **「按状态显示/隐藏元素组」机制**——现有 `state_assets`/`state_group` 是**换贴图**语义；收起（slim 把手）
   与展开（full 条 + tips + 12 标签）切的是**可见性**，**本项目首次需要该机制**（layout 新字段 →
   `工具\gen_layout.py` → krkr `ui_layout.tjs` + 复刻 `ui_layout.js` 两端生成物）。
2. **边缘呼出状态机**：贴边呼出／离开延时收起／点击项后收起／换屏与剧情推进收起／标题屏禁用／「锁定」钉住。
   ⚠️ **右端热区不得注册成 `hit` 元素**（会吃掉剧情推进与自动播放的点击），只能在鼠标位置层面判定。
3. **逐项悬停高亮需小美术裁切**：`quick.btn` 是整条 63×888、12 个图标烘焙在一张图里；逐项高亮要么切件、
   要么叠一层高亮图。
4. **平滑滑动未采纳**（用户选淡入淡出）：若要改滑动，需新增逐帧节拍，本工程重画策略是「悬停目标变化才重画」。

**两条边界说明**：

- 《月影魅像-解放之羽》的 UI 层仍在**未解码容器**（`fe fe 01 ff fe`）内，拿不到它的坐标；能直接照的是
  《交汇协奏曲》的 idx 81（已 1:1 复刻）。若要以《月影魅像》为准，须先立项解其 UI 层。
- 巡演/自检需支持「无真实鼠标下强制展开」——复用 flag 文件 + `Scripts.execStorage`（同 `press_probe.tjs` 套路）。

### 待办（技术）

| # | 事项 |
| --- | --- |
| 1 | **两轮打回的处置本身仍未再送独立一审**（本会话两次都是「我实现 → 审查打回 → 我处置+自验」）→ 应补一轮 |
| 2 | 真实鼠标**视觉**确认：「按住拖出元素即取消」「图标与文字**同时**换态」（日志能证链路，镜头才能证观感） |
| 3 | 调色板往返缺陷**只在入库工具侧兜住**；根治 = 让编辑器拿到**未解析源**（如 `gen_layout` 增设 `复刻\screens_src.js`） |
| 4 | krkr 缺「失焦/抬起丢失」兜底（HTML 有 blur 兜底）——需本工程未实测的 API，未修 |
| 5 | 巡演若加 `mouse/left` 步骤会置按下态而无抬起（巡演不合成 `onClick`）→ 加步骤前须先处理 |
| 6 | 编辑器 `assetSelect` 每个槽 420 个 option（仅登记，未改） |
| 7 | `x_ui_choice_dis.png`（真"禁用"态美术）与 7 件正文层 `_press.png` 当前无引用（保留待用） |
| 8 | `dress` 屏 1 处既有文本截断 `[ed.staff]`（与本轮无关） |
| 9 | **Win7 SP1 x64 未实测**（每次都要如实登记） |
| 10 | `临时\` 已 3.2 GB（历次 `ui_run` 整份复制）+ 本会话 worktree → 待用户确权后清理 |

---

## 六、关键路径速查

```
UI组\
├─ layout\screens\*.json          ← **唯一真相源**（编辑器只写这里）
├─ 工具\
│  ├─ gen_layout.py verify_ui.py             六项硬校验
│  ├─ test_verify_asset_refs.py              state_assets 引用覆盖（含非字典异常）
│  ├─ test_state_targets.py                  ★ 悬停可达性守门（探针的盲区补丁）
│  ├─ verify_editor_export.py                导出件一键入库 + 调色板还原/守门
│  └─ emit_asset_index.py                    素材库索引（编辑器热重载用）
├─ 复刻\
│  ├─ index.html / replica.js / replica.css  1:1 复刻（**渲染内核**，编辑器也复用它）
│  ├─ editor.html / editor_core.js / editor_ui.js / editor.css   ★ 布局编辑器
│  ├─ _selftest_states.html                  ★ 自测 A（17 条，规则①–⑦）
│  └─ asset_index.js / screen_index.js / ui_layout.js            生成物
├─ krkr\
│  ├─ game\ *.tjs                 UI 库（ui_screens / ui_widget / ui_dialog / ui_startup…）
│  ├─ game\ui_layout.tjs          生成物
│  ├─ assets\ui\                  435 件素材
│  ├─ runtime\                    引擎运行时（*.exe/*.dll 被 gitignore，**每个 worktree 需本地铺一次**）
│  ├─ run_loose.bat               人工测试（非巡演；**给用户手测用这个**）
│  ├─ run_autotour.bat            自动巡演（27 屏 + 离屏 PNG，约 45 秒自退）
│  └─ run_pressprobe.bat          ★ 按下态验收探针（PROBE=<元素id>）
├─ _工作\
│  ├─ M34_风格锚点.md / M34_交汇协奏曲UI布局规格.md / M34_部件总表.tsv   ← 坐标权威
│  ├─ M35_生图提示词存档.md / M35_悬停按下态_代码缺口诊断.md
│  ├─ M35_生图脚本\              本轮工具链（btn_gen / btn_slice2 / btn_compose / btn_states /
│  │                              deploy_btn / fix_choice_dis_alpha / M35b_* 迁移与出图脚本）
│  ├─ M35_证据\                  ★ 全部验收证据（含**真人鼠标日志**与三态/迁移核对图）
│  └─ M35_编辑器回滚\<时间戳>\   编辑器导出入库前的版面备份（**逐层可回退**）
├─ 编辑器修改区\                  ★ 用户导出的收件目录（**只从这里取**）
└─ 会话交接_*.md                  历次交接（本文件是最新）
```

**素材命名**：`x_ui_btntxt2_<key>` 正文层 ｜ `.._on` / `.._press` 两态 ｜ `x_ui_btntxt2c_*` 合成层（羽毛+文字）｜ `x_ui_btntxtf_*` 独立羽毛层 ｜ `x_ui_menuicon_*` 圆形功能图标（旧）｜ `x_ui_choice_{off,over,press}.png` 选择支行 ｜ `x_ui_choice_dis.png` 禁用态（未用）。

---

## 七、开工必读（每次任务重读）

1. `AGENTS.md`（工作区铁律，**特别是 §一 铁律 8：需用户裁决的事项必须用 AskUserQuestion 发选项**）+ `Galgame.md`
2. `..\00_项目总纲.md` —— 工程唯一总参考文档
3. `M34_UI复刻总纲.md` —— 复刻的用户裁定记录（V1–V5）+ `_工作\M34_风格锚点.md`（实测配色）
4. `_工作\M35_生图提示词存档.md` —— 实际发出的提示词全文（**用户可能索要完整提示词**）
5. `.zcode\skills\kirikiri-unpack\引擎工作原理.md` —— krkr 类任务必读
6. 翻译类任务：`.zcode\skills\galgame-translation\{SKILL.md,术语表.md}` + `..\作品skill\{SKILL.md,术语表.md}`

---

## 八、工程记录

均在 `工程记录\`（本会话新增 6 份，全部**只新建不覆盖**）：

- `2026-09-22_对于我们没有翅膀格雷塔迦露德与柳木原UI组按钮文字素材的修改.md`（-01 常态 35 件）
- `..._修改-02.md`（两态 28 件 + 代码缺口诊断）
- `..._修改-03.md`（悬停调亮 + 取消点击态图）
- `..._修改-04.md`（悬停/按下态代码修复 + **一审回执**）
- `..._修改-05.md`（应用用户导出 + 组绑定 + 编辑器居中）
- `..._修改-06.md`（一审打回处置 + 热区迁移 + 补按下图 + **补记**（真人鼠标实测）+ **补记二**（二审打回处置））

另有工作区级：`2026-09-22_对于AGENTS决策提问规则的修改.md`（铁律 8，已合并 `main`）。
