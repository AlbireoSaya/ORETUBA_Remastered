# replaytoggle · 自检报告（模块 E4）

- Issue：`ISSUE-20260929-02`（分支 `issue/ISSUE-20260929-02-flowchart-pane-rework`）｜ 日期：2026-09-29
- 模块：E4 —— 流程图右栏「播放/暂停切换」（`fc.pbkick_hit` → 动作 `flow_replay_toggle`）**纯 UI 状态变更**，两端同实现 + 机检。
- 结论：**四条验收命令全部通过**；`★REPLAYTOGGLE★ PASS` 实测在册；两态 PNG 已目视确认。
- ⚠ 本文件名的说明：指定的交付名是 `自检报告.md`，但该目录下**已存在 E3 的同名文件**（`证据\自检报告.md`）。按工作区「不得覆盖/删除既有产物」的规矩，本模块的交付改名为 **`replaytoggle_自检报告.md`**，不改动 E3 的那一份。请主代理裁决是否需要统一改名。

---

## 一、验收命令与实测输出

### 1) HTML 两套自检 —— `python _工作/ISSUE-20260923-01_M39_证据/复现脚本/m39_run_html_selftests.py`

命令（逐字，`PYTHONPATH` 已设为 `E:/ZCode Workspace/Galgame/工具/pylibs`）：

```
cd "E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
python "_工作/ISSUE-20260923-01_M39_证据/复现脚本/m39_run_html_selftests.py"
rc = 0
```

完整输出留档：`证据\_m39_full_run.txt`。本模块相关的实测行（**逐字**）：

```
  SELFTEST OK   ㉕ 数据侧守卫：flag 已声明、两键取值互斥、素材在清单内且常态互异  —— fc.pbkick=play / fc.pbkick_pause=pause（flag=fc_replay，素材 x_ui_pbkick_off.png ≠ x_ui_pbkick_pause_off.png）
  SELFTEST OK   ㉕a 两个取值各自复算：**恰好一键可见**（fc_replay=play ⇒ 只 fc.pbkick；fc_replay=pause ⇒ 只 fc.pbkick_pause）  —— fc_replay=play ⇒ 可见[fc.pbkick]（应 [fc.pbkick]）；fc_replay=pause ⇒ 可见[fc.pbkick_pause]（应 [fc.pbkick_pause]）
  SELFTEST OK   ㉕b 合成点击热区 ⇒ fc_replay 翻转，可见键**随之互换**（真实入口，非直调内部函数）  —— fc_replay play→pause；可见 [fc.pbkick]→[fc.pbkick_pause]（应 [fc.pbkick]→[fc.pbkick_pause]）；台账 lastReplay=pause、count 0→1
  SELFTEST OK   ㉕c 再点一次 ⇒ 翻回原值、可见键复位（幂等闭环）  —— fc_replay pause→play（应回 play）；可见 [fc.pbkick]（应 [fc.pbkick]）
  判定：ALL PASS ｜ 原始 dump：…\_工作\ISSUE-20260923-01_M39_证据\M39_selftest_A_dump.html ｜ edge rc=0

  PASS	flow.replay-guard	fc.pbkick=play / fc.pbkick_pause=pause（flag=fc_replay；素材 x_ui_pbkick_off.png ≠ x_ui_pbkick_pause_off.png；清单 已动态装载｜asset_index.js）
  PASS	flow.replay-one-visible	fc_replay=play ⇒ 可见[fc.pbkick]（应 [fc.pbkick]）；fc_replay=pause ⇒ 可见[fc.pbkick_pause]（应 [fc.pbkick_pause]）
  PASS	flow.replay-toggle	fc_replay play→pause（真实 click）；可见 [fc.pbkick]→[fc.pbkick_pause]（应 [fc.pbkick]→[fc.pbkick_pause]）；lastReplay=pause、count 0→1
  PASS	flow.replay-toggle-idempotent	再点一次 pause→play（应回 play），可见[fc.pbkick]（应 [fc.pbkick]）
  判定：RESULT=OK ｜ 原始 dump：…\_工作\ISSUE-20260923-01_M39_证据\M39_selftest_B_dump.html ｜ edge rc=0
```

⇒ 套 A `ALL PASS`、套 B `RESULT=OK`、`rc=0`（与派单要求一致）。

**负向对照（证明断言有牙齿）**：`?mut=fold` 在内存里把两键 `vis_when` 折叠成同一个值 ⇒

```
  SELFTEST FAIL ㉕a … —— fc_replay=play ⇒ 可见[fc.pbkick,fc.pbkick_pause]（应 [fc.pbkick]）；fc_replay=pause ⇒ 可见[]（应 [fc.pbkick_pause]）
  SELFTEST FAIL ㉕b … —— fc_replay play→play；可见 [fc.pbkick,fc.pbkick_pause]→[fc.pbkick,fc.pbkick_pause]…
  SELFTEST FAIL ㉕c …
  判定：FAILED 3 项
```

⇒ 「恰好一键可见」这条断言确实能报警（不是恒真）。命令：无头 Edge `--dump-dom` 直开 `复刻/_selftest_states.html?mut=fold`，`rc=0`。

### 2) 点击可达性 —— `python 工具/test_click_reach.py`

```
── 32_flowchart.json OK  元素 280（可点  79）｜ 状态 15 ｜ 重叠对 0 ｜ 中心检查 294
------------------------------------------------------------------------------
合计：屏 17 ｜ 重叠对 11 ｜ 中心可达性检查 31740 次 ｜ 豁免命中 1 条
结果：**全部通过**（无未登记的可达性缺陷；豁免项均已在表中写明理由）
```

⇒ 新增的 4 件（`fc.play_win` / `fc.play_view` / `fc.pbkick_pause` / `fc.pbkick_hit`）**没有引入任何未被登记的重叠**；流程图屏 `重叠对 0`、`状态 15`（两键按 `fc_replay` 的两态分别计入 ⇒ 不计为重叠）。
（17 屏合计的 11 对重叠与 1 条豁免全部来自 `33_sysicons.json`，是 M13 起就登记在册的「浮层全屏 dismiss 热区 + 9 图标」，与本模块无关。）

### 3) 实机巡演 —— `cmd //c "run_autotour.bat"`（无参，每步 2s）

产物落点（本 worktree 的实际路径）：`E:\ZCode Workspace\Galgame\临时\wt-qbicons\临时\ui_run\runtime\savedata\`
（`krkr.console.log` 为 **UTF-16LE**，用 Python `encoding="utf-16"` 解码；`shot_NN_<屏>.png` 同目录。）

**本模块判词（逐字，完整摘录见 `证据\replaytoggle_巡演摘录.txt`）**

```
03:39:48 [UI][REPLAY] flow_replay_toggle : fc_replay play -> pause (changed) | screen=flowchart | visible=fc.pbkick_pause (1) | redraw=caller (handleClick / uiTourStep) | playback=not implemented (programming group)
03:39:48 [UI][REPLAY] flow_replay_toggle : fc_replay pause -> play (changed) | screen=flowchart | visible=fc.pbkick (1) | redraw=caller (handleClick / uiTourStep) | playback=not implemented (programming group)
03:39:48 [UI][TOUR] -> 下一步：★REPLAYTOGGLE★ …  屏=flowchart  说明=★REPLAYTOGGLE★ PASS  目标=fc.pbkick_hit[auto(数据推:action)] 中心=1637,363
        ①点击前 fc_replay=play  ②点击=flow_replay_toggle -> pause（期望 pause，命中参数 layer=(空)）
        ③引擎谓词复算 fc.pbkick(play)=x fc.pbkick_pause(pause)=V ⇒ 可见 1 件、与 flag 相符=是
        ④再点=flow_replay_toggle -> play（应回 play）  键数=2 flag=fc_replay  重绘=下一步 tourTick…  播放实现=未接（编程组）
03:39:50 [UI][TOUR] -> 下一步：★REPLAYTOGGLE-REJECT★ 负向①…  说明=★REPLAYTOGGLE-REJECT★ fc.pbkick_hit__no_such__ 不在当前屏 flowchart 的元素表里（『元素不存在』守卫）
03:39:52 [UI][TOUR] -> 下一步：★REPLAYTOGGLE-REJECT★ 负向②…  说明=★REPLAYTOGGLE-REJECT★ fc.pbkick 不是 hit（kind=image）⇒ 它没有派发入口，点不出动作
03:39:54 [UI][TOUR] -> 下一步：★REPLAYTOGGLE-REJECT★ 负向③…  说明=★REPLAYTOGGLE-REJECT★ fc.jump_hit 的 action=flow_enter，不是 flow_replay_toggle 热区
03:40:05 [UI][TOUR] -> 下一步：★REPLAYTOGGLE-SKIP★ 前台屏=loading（无该机制）⇒ …  屏=loading  说明=★REPLAYTOGGLE-SKIP★ 当前屏=loading（本步骤只在流程图屏有效，跳过）
```

**总账（收官行，逐字）**

```
03:40:23 [UI][TOUR] ===== 巡演结束 =====
03:40:23 [UI][TOUR] 共记录 113 屏 | 已载入 203 件 / 缺件 0 件
03:40:23 [UI][TOUR] 缺件元素 0 处 | 缩放元素 0 处 | 截断文本 0 处 | 未知 kind 0 处 | item_buttons/item_text 拒绝 5 处 [★M06ITEMBTN-REJECT★ …]
03:40:23 [UI] quit (autotour done) : frames=2119 | gal_shell | 已载入 203 件 / 缺件 0 件 | …
```

关键词计数（对同一份日志）：`EXCEPTION = 0`、`[UI][FLOW][ERR] = 0`、`转场失败 = 0`、`缺件 0 = 2`（两处总账行）、
`★REPLAYTOGGLE★ PASS = 1`、`★REPLAYTOGGLE-REJECT★ = 9`（3 条判词 × 3 处出现：派发行 + 步骤标签 + 计划回显）、`★REPLAYTOGGLE-SKIP★ = 3`（1 条 × 3 处）。

⚠ 那 5 处 `★M06ITEMBTN-REJECT★` 是 **M06 轮登记在册的预期输出**：`UIScrTourSteps` 里那一步（`回想·负向⑦：item_buttons 5 种非法形态（内存副本）⇒ 机制守卫必须逐条 REJECT`）**故意**在内存副本里注入 5 种非法形态，**逐条被守卫拒斥**（`action 为空` / `矩形出块（局部 1300,190 200×60 不在 1526×188 内）` / `矩形零/负面积（0×0）` / `第 0 项缺 key` / `第 0 项不是对象`），5 条正好逐个对应。本批**未触碰**回想屏。收官行的 `转场 成功 32 / 失败 0 / 降级 0` 亦为 0 失败。

### 4) PNG 目视确认（本工程铁律：日志无 error ≠ 功能正确）

巡演逐帧导出的 PNG 在同一目录。**两态的判据先量化、再目视**：

量化（按钮矩形内、字形 bbox `(1608,337)-(1668,390)`，字形判别式 `B − R > 40`；`midcol` = 字形中央竖列 `x=1636` 的墨迹高度）

| 文件 | 墨迹像素 | midcol | 判定 | mtime |
| --- | ---: | ---: | --- | --- |
| `shot_99_flowchart.png` | 1326 | 35 | **PLAY（▶，三角；中央有实体）** | 03:39:56 |
| `shot_100_flowchart.png` | 1560 | 0 | **PAUSE（‖，两竖条；中央是空隙）** | 03:39:58 |
| `shot_101_flowchart.png` | 1326 | 35 | PLAY（复位自证） | 03:40:00 |

⇒ **play 态 = `shot_99_flowchart.png`；pause 态 = `shot_100_flowchart.png`**（相邻两帧，除那个字形外右栏内容一致）。

目视结论（`证据\replaytoggle_切换两态.png`，右栏裁切 `x∈[1416,1859] y∈[190,1019]` 并排）：
两张图的**大播放窗内托盘上，只有一枚圆形键**，其余一切相同 —— 左（play）**只见 ▶**，右（pause）**只见 ‖**；窗下三段（标题/说明/台词）与底部「进入本章」完全一致。窗内是引擎画的 `[占位] 动态层 dynamic:flow_scene_fra…` 占位文本（`fc.play_view` 未填充，属编程组，**与设计一致**）。

⚠ **一格偏移（既有约定，非本批缺陷）**：`shot_NN` 的像素 = 第 `NN−1` 步之后的状态（`startup.tjs` 的 E2d 注已登记同一口径）。所以「切到暂停态」那一帧落在 `shot_100`（日志行号是 99/112）。上面的量化与 mtime 是**独立于日志**的判据，结论不受该偏移影响。

---

## 二、我改了什么（本次改动全部在本模块范围内）

| 文件 | 改动 |
| --- | --- |
| `krkr/game/ui_flow.tjs` | 新增 `flow_replay_toggle`：具名常量（597–605）+ 日志/取值/声明/可见性四个 helper（609–665）+ `uiFlowReplayToggle()`（670–715）+ `uiActionDispatch` 分支（800） |
| `krkr/game/ui_screens.tjs` | 新增巡演验收件：兜底常量与 `uiScreenReplayConst/FindHit`（3214–3253）+ `uiScreenSyntheticReplayToggle`（3255–3400）+ 步骤类型注册（4944）+ 步骤表 7 步（4747–4758 正向/负向/两态截图、4775 SKIP 实测步） |
| `复刻/replica.js` | `state.flowReplay`（1433）+ `FLOW_REPLAY`/`flowReplayReject`/`flowReplayKeys`/`flowReplayToggle`（2538–2610）+ `doAction` 分支（4658）+ 换屏台账复位（2742–2746）+ 导出（6764–6767）+ 套 B 自检四条（6213–6300） |
| `复刻/_selftest_states.html` | 新增 ㉕ 块（2854 起）：数据侧守卫 + ㉕a/㉕b/㉕c + `?mut=fold` 负向对照 |
| `UI组交接编程组.md` | §四·补 4·补.3 第 3 条**订正**：删「`fc_replay` 的翻转与两键换显由你们在分派里完成」，改为「UI 组已两端实现」并列出落点与机检；动作名「拟用名」→「已定稿」 |
| `流程图系统_版式规范.md` | §〇.2 ③ 动作名去「拟用名」；§三 R7 追加【订正之二】：翻转/换显已两端实现，只剩画面播放属编程组 |
| `_工作/ISSUE-20260929-02_右栏大改/证据/` | 新增 `replaytoggle_实现说明.md`、`replaytoggle_巡演摘录.txt`、`replaytoggle_切换两态.png`、`replaytoggle_自检报告.md`（本文件）、`_m39_full_run.txt` |

**没有跑过生成器**：本次**未执行** `工具\gen_layout.py`、`工具\gen_flow_layout.py`、`emit_asset_index.py` —— 本模块只改机制脚本与自检脚本，**未触碰任何布局/屏数据/素材**，故三处产物保持 E1/E2/E3 落盘时的真值（`fc_replay` 等字段早已在其中）。也**未改** `layout/_schema.md`（主代理补「两端已实现」）、`layout/screens/32_flowchart.json`、`layout/ui_layout.json`、`krkr/game/ui_layout.tjs`、`复刻/ui_layout.js`、`工具/gen_flow_layout.py`。未 `git commit` / 未切分支。

---

## 三、未决问题与请主代理裁决

1. **交付文件名**：`自检报告.md` 与 E3 既有文件同名 ⇒ 本模块用 `replaytoggle_自检报告.md`。若要统一命名，请裁决（我不删 E3 的文件）。
2. **巡演表新增 7 步**：正向 1 + 负向 3 + 两态截图 2 + SKIP 实测 1 ⇒ 巡演总步数 112 → **113 记录**、耗时约 +12s（实测一轮约 230s）。若主代理希望缩短巡演，可只保留正向 1 步 + SKIP 1 步（负向 3 步与两态截图 2 步是「守卫有牙齿」与「两态目视」的证据，建议保留）。
3. **`fc.play_view` 的占位文本**：实机导图里大播放窗内是引擎画的 `[占位] 动态层 dynamic:flow_scene_fra…`（加粗占位字压在托盘上）。这属**编程组未填充**的正常表现（`layout/_schema.md` §四 `dynamic` 条要求未填充时画占位）。若用户希望正式游玩前**不显示占位文本**，需编程组接填充或另议（**本模块不碰**）。
4. **`?mut=fold` 新增了一个负向对照档位**：既有 `?mut=` 的档位表（`missing/foldhover/swap/drift/expect`）在本工程文档里是否有清单需要同步，请主代理确认（我只在 `_selftest_states.html` 的 ㉕ 注释与本报告里写明）。
5. **未实测 SKIP 的另一条路径**：`★REPLAYTOGGLE-SKIP★` 已由「前台屏=`loading`」实测触发；「前台屏=flowchart 但数据无该热区」这条分支（`uiScreenReplayFindHit` 返回 null）**未实测** —— 它需要把屏数据里的 `fc.pbkick_hit` 拿掉才成立，属**改数据**，本批不做（已如实登记，不声称已验）。
6. **两端一致性的验证边界**：krkr 与 HTML 的翻转/换显各自有独立机检（巡演 + 自检），但**未做两端同屏逐像素对比**（两态是大播放窗+托盘这种小件，像素对比收益低）。若主代理要求，可另派 vision 复核 `replaytoggle_切换两态.png`。
