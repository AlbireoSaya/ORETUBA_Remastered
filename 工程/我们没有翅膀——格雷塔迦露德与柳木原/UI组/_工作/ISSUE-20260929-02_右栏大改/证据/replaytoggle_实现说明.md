# 播放/暂停切换（`flow_replay_toggle`）实现说明

- 模块：**E4** ｜ Issue：`ISSUE-20260929-02` ｜ 日期：2026-09-29
- 范围：**只做「纯 UI 状态变更」** —— 翻屏级 flag `fc_replay` + 两键换显（两端同实现）+ 机检。
- **不做**（留给编程组，不得声称已生效）：`fc.play_view` 的 `dynamic:"flow_scene_frames"` 填充、帧序列/时序、音频。
- 关联契约：`_工作/ISSUE-20260929-02_右栏大改/接口冻结.md` §B.2/§B.3/§B.5；`layout/_schema.md` §四「屏级状态 flag」、§六 动作名表。
- 形制对标：`flow_layer`（`ui_flow.tjs` 的 `uiActionDispatch` 包装器分支 + `ui_flow_layer.tjs::uiFlowLayerApply`；HTML 侧 `replica.js::flowLayerSet`）。

---

## 一、同判据（两端同一句话）

| 项 | 值 | 出处 |
| --- | --- | --- |
| 屏级 flag 名 | `fc_replay` | 冻结 §B.5（**具名常量**：krkr `UIFlowReplayFlag` / HTML `FLOW_REPLAY.flag`） |
| 取值 | `"play"` = 显示播放键 `fc.pbkick`；`"pause"` = 显示暂停键 `fc.pbkick_pause` | 冻结 §B.5（`UIFlowReplayPlayVal`/`UIFlowReplayPauseVal`；`FLOW_REPLAY.play/pause`） |
| 动作名 | `flow_replay_toggle` | 冻结 §B.5；唯一发出者＝唯一热区 `fc.pbkick_hit` |
| 默认值 | 数据 `flags_default.fc_replay = "play"`（**机制不另立默认**） | `layout/screens/32_flowchart.json` |
| **判据** | `fc_replay == "pause"` ⇒ 置 `"play"`；**否则** ⇒ 置 `"pause"` | 两端同一句；未设置（`""`）也落进「否则 ⇒ pause」分支，因此默认「play」语义只由 `flags_default` 提供 |
| 显隐 | 两键靠既有 `vis_flag`/`vis_when` 互斥；命中与绘制**同一谓词** ⇒ 自动「恰好一键可见」 | `ui_screens.tjs::uiScreenElementVisible` / `replica.js::elementVisible` |
| 重绘 | **由调用方**（`startup.tjs::handleClick` 派发后 `redraw()`；巡演 `uiTourStep` 下一步统一 redraw）；HTML 侧 `applyFlagVisibility()` **不重建 DOM** | 与 `flow_layer` 同款 |

两端均**不写死**素材名、坐标、可见件 id：可见性完全由 pass 进数据的 `vis_flag`/`vis_when` 决定；机制只碰 flag 名与两个取值（冻结接口，走具名常量）。

---

## 二、krkr 端

### 2.1 `krkr/game/ui_flow.tjs`（`uiActionDispatch` 包装器）

**新增（模块级常量与函数，插在「安装：包装 M2 的三个入口」之前）**

| 行 | 内容 |
| --- | --- |
| 597–600 | `UIFlowReplayFlag / UIFlowReplayPlayVal / UIFlowReplayPauseVal / UIFlowReplayActName` —— flag 名、两个取值、动作名（冻结接口的**唯一出处**，不散落魔法串） |
| 602–605 | `UIFlowReplayLast / UIFlowReplayCount / UIFlowReplayErrCount` —— 诊断与巡演可读状态（**不入存档文件**：`uiFlowSaveState` 只写既有 `key=value` 行） |
| 609–612 | `uiFlowReplayLog(s)` —— 日志出口，前缀 `[UI][REPLAY]`，**行内只用 ASCII**（`->` / `:` / `|`），全程 `try/catch`（日志失败不影响主流程） |
| 615–635 | `uiFlowReplayValues(screen, flag)` —— 本屏该 flag 的取值集合（**从数据推**：带该 flag 的元素的 `vis_when` 去重） |
| 638–646 | `uiFlowReplayFlagDeclared(screen, flag)` —— 数据侧自证：flag 是否声明在 `flags_default` 里 |
| 650–665 | `uiFlowReplayVisibleIds(screen, flag)` —— 用**引擎自己的谓词** `uiScreenElementVisible` 复算「此刻可见的件」 |
| **670–715** | **`uiFlowReplayToggle()`** —— 动作本体（下方「三处守卫 + 主流程」） |

**新增（派发分支，`flow_layer` 分支旁）** — 第 800 行：

```tjs
				// ★ ISSUE-20260929-02（本批）：新动作 `flow_replay_toggle` —— 播放/暂停切换。
				//   唯一发出方 = 流程图屏唯一热区 `fc.pbkick_hit`（冻结 §B.5）；
				//   只翻屏级 flag `fc_replay`（重绘由调用方），**不碰画面播放本身**。
				//   动作名走具名常量 `UIFlowReplayActName`（冻结接口，不散落魔法串）。
				if(act == UIFlowReplayActName) return uiFlowReplayToggle();
```

**`uiFlowReplayToggle()` 主体（逐条）**

1. 屏未登记 ⇒ 拒绝（`REFUSE ... screen not registered` + 中文 msg）。
2. `flags_default` 未声明 `fc_replay` ⇒ 拒绝（机制与数据不同版）。
3. 该 flag 的取值不足 2 个 ⇒ 拒绝（屏上没有互斥的两键，翻了也没东西可换显）。
4. `before = uiScreenFlagGet("fc_replay")`；`after = (before == "pause") ? "play" : "pause"`。
5. `uiScreenFlagSet(flag, after)` 写回；`UIFlowReplayLast/Count` 记账。
6. `uiFlowReplayVisibleIds()` **复算**并打进日志（不是复述实现，而是同一谓词的读数）。
7. 日志形制（实测样张）：

```
[UI][REPLAY] flow_replay_toggle : fc_replay play -> pause (changed) | screen=flowchart | visible=fc.pbkick_pause (1) | redraw=caller (handleClick / uiTourStep) | playback=not implemented (programming group)
```

**「在任何 JSON 序列化场景下不崩」的具体保证**

- 日志行**纯 ASCII**、由字符串 `+` 拼接而成，不含 Dictionary / `void` / 引号 / 换行 ⇒ 按行消费（含 JSON 包装）不会被转义打断。
- 函数返回的 Dictionary **只含 `handled`(bool) / `effect`(string) / `msg`(string)**，无嵌套对象、无 `void`，`Dictionary.saveStruct` / JSON 序列化均安全。
- 日志自身 `try/catch` 包裹（`uiFlowReplayLog`），即使日志通道异常也不影响翻转与重绘。
- ⚠ 未写任何 Timer、未触碰 `fc.play_view`、未触碰音频——**「播放本身」在本模块内不存在**，不存在序列化到未实现对象的路径。

### 2.2 `krkr/game/ui_screens.tjs`（巡演验收件）

| 行 | 内容 |
| --- | --- |
| 3214–3217 | `UIScrReplayActFallback / FlagFallback / PlayFallback / PauseFallback` —— `ui_flow.tjs` **未装载时**的同值兜底 |
| 3219–3240 | `uiScreenReplayConst()` —— 常量来源：**优先读 ui_flow.tjs 的具名常量**（逐条 `!== void` 守卫后再 `"" + x`，避免 TJS2 的 `void` 转字符串异常），读不到才用兜底 |
| 3242–3253 | `uiScreenReplayFindHit(sc, spec, C)` —— `"auto"` ⇒ 数据推（`action == C.act` 的第一个 hit）；否则按 id 取 |
| **3255–3400** | **`uiScreenSyntheticReplayToggle(spec)`** —— 四断言 + 三态判词（见下） |
| 4944–4948 | `uiTourStep` 注册新步骤类型 `kind:"replaytoggle"` |
| 4747–4758 | 步骤表：正向 1 步 + 负向 3 步 + 两态截图 2 步（`kind:"action"`） |
| 4775–4778 | 步骤表：**SKIP 分支实测步**（前台屏换成 `loading` 后跑一步） |

**判词三态（实测样张见 `replaytoggle_巡演摘录.txt`）**

- `★REPLAYTOGGLE★ PASS|FAIL` —— 四断言逐条打印**实际值**：
  ① 点击前 `fc_replay` 的值；② 走**真实点击入口**（`uiScreenPressUpdate`→`uiScreenPressClear`→`uiScreenClick`（顶部命中 → `UIScrHitLayer`）→`uiActionDispatch`，与 `handleClick` 同批）后已翻转且等于按判据算出的期望值；③ 用 `uiScreenElementVisible` 复算两键可见性，**恰好 1 件可见且与 flag 相符**；④ 再点一次翻回原值（幂等闭环）。
- `★REPLAYTOGGLE-REJECT★ <id> <理由>` —— 三条负向对照（元素不存在 / 不是 hit / 是 hit 但不是本动作热区），**任何状态变更之前**判定，拒绝时不改状态。
- `★REPLAYTOGGLE-SKIP★ <理由>` —— 前台屏非 `flowchart`、或本屏数据无 `action == flow_replay_toggle` 的热区 ⇒ 明确跳过、零状态变更。
- ⚠ 巡演每步 2s 定时器驱动：本步**全部同步完成**，不依赖额外延时。
- ⚠ 两态截图步用**既有** `kind:"action"` 步骤派发同一动作（只产图），并在 label 里注明「画面播放未接」；功能正确性由四断言负责。

---

## 三、HTML 端

### 3.1 `复刻/replica.js`

| 行 | 内容 |
| --- | --- |
| 1433 | `state.flowReplay = { lastReplay, count, flag, flagValue, rejects }` —— 可观测状态（照 `flowLayer` 的 `lastAct/lastLayer/count` 形制） |
| **2538** | `var FLOW_REPLAY = { flag:'fc_replay', play:'play', pause:'pause', action:'flow_replay_toggle' }`（冻结接口具名常量） |
| 2541–2547 | `flowReplayReject(act, reason)` —— 判词出口 `★E3REPLAY-REJECT★`（去重 + `console.warn`），与 E3LAYER/M06/M08 同款 |
| 2550–2562 | `flowReplayKeys(def, flag)` —— 数据侧事实（带该 flag 的件 id/vis_when），守卫与自检共用 |
| **2565–2610** | **`flowReplayToggle(actStr)`** —— 与 krkr 同判据：`pause ⇒ play`，否则 ⇒ `pause`；`setFlag()` + `applyFlagVisibility()`（**不重建 DOM**）；`state.flowReplay` 记账；返回 `true/false` |
| 4658 | `doAction` 新增 `case 'flow_replay_toggle': flowReplayToggle(action); return;` |
| 2742–2746 | 换屏台账复位（与 `flowLayer` 同款；`renderScreen` 内） |
| 6764–6771 | 导出 `flowReplayToggle / flowReplayState / flowReplayKeys / FLOW_REPLAY`（供自检与探针） |

### 3.2 HTML 自检

- **套 A** `复刻/_selftest_states.html`：新增 **㉕** 块（2854 起）——数据侧守卫（flag 已声明 / 两键取值互斥 / 素材在清单内 / 两键常态素材互异）＋ ㉕a 两取值各复算「恰好一键可见」＋ ㉕b **合成 `click()` 走真实入口** ⇒ flag 翻转且可见键互换（并核台账 `lastReplay`/`count`）＋ ㉕c 再点翻回（幂等闭环）。主语与期望值**全部从 `ui_layout.js` 数据推**（热区＝`action=="flow_replay_toggle"` 的唯一 hit；两键＝该热区矩形中心覆盖到的「带 `vis_when` 的 image」），不写死 id/素材名。负向对照 `?mut=fold`（内存折叠两键 `vis_when`）⇒ ㉕a/b/c 必须报警。
- **套 B** `复刻/index.html?selftest=1`（实现在 `replica.js::runSelfTestChecks`，6213 起）：新增 `flow.replay-guard` / `flow.replay-one-visible` / `flow.replay-toggle` / `flow.replay-toggle-idempotent` 四条，判据与套 A 同。

---

## 四、本次实现中发现并已修的**断言自身缺陷**（如实登记）

两处都是「断言假失败」，与产品代码无关，但都是本工程登记过的同类坑，值得留痕：

1. **陈旧 DOM**：㉕ 块首版未先 `renderScreen('flowchart')`，而上一块（㉔）收尾停在 `title` 屏 ⇒ `shown()` 一律 `null`、可见集恒空，「恰好一键可见」假失败。
2. **活引用自比**：㉕b 首版写 `var st0 = RPC.flowReplayState();` 后比较 `st1.count === st0.count + 1` —— `flowReplayState()` 返回的是 `state.flowReplay` **对象本身**，点击后 `st0.count` 也变成新值 ⇒ `1 === 1+1` 恒不成立。改为读**数值副本**（`var c0 = ...count`）。与 ⑧ 里 `h0` 那条「同一表达式自比」的坑同源。

修后：套 A `ALL PASS`、套 B `RESULT=OK`。

---

## 五、明确未做 / 留给编程组

- `fc.play_view` 的 `dynamic:"flow_scene_frames"` 填充（当前实机导图上该窗内是引擎画出的 `[占位] 动态层` 文本 —— 见 `replaytoggle_切换两态.png` 上半部）。
- 帧序列 / 时序 / 音频；「暂停时真的停帧」。
- 编程组若需要「当前是播放还是暂停」：**读屏级 flag `fc_replay`** 即可（`uiScreenFlagGet("fc_replay")`；值 `"play"`／`"pause"`）。
