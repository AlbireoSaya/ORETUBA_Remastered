# 复现脚本 · `ISSUE-20260928-02` 第 2 步（模块 E1 · 数据层与生成器）

> 落盘：2026-09-28（**第 3 批 + 第 4 批 + 第 5 批 + 第 6 批订正 + 第 7 批小修 + 第 8 批（`ISSUE-20260928-03`）已并入**）｜ 作业 worktree：`临时\wt-qbicons` ｜ 本目录属 `_工作\`（不参与任何闸门的屏扫描）
> 接口：`_工作\ISSUE-20260928-02_第2步\接口冻结.md`（§一 运行态 / §二 番外独立层 / §五 全量）
> 上一轮：`_工作\ISSUE-20260927-05_流程图实现\边与节点数据契约.md`（v1.2，仍有效）

## 一键跑

```bash
export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
cd "/e/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
python "_工作/ISSUE-20260928-02_第2步/复现脚本/run_all.py"     # 34 步；EXIT=0 = 全绿
```

`run_all.py` 会：产三档预设（screen1→states→frag）→ 出三处产物 → **在 frag 产出态**跑**六道**闸门
→ 跑本目录六个自证脚本（m01/m02/m03/m04/m05 + **m06 交付样例基线总账**）→ 用 `test_flow_links --screen` 查 states/frag 变体 → **还原 screen1**
→ 再跑六道闸门（交付样例态）→ 跑 m01 外观自证 → 另跑 screen2/ref150/full ＋ `--frag-report`（未产格清单）→ **最后再还原一次交付样例**。
（六道闸门 = 原五道 ＋ `test_verify_asset_refs.py`，后者为第 2 批主代理要求。）
全程幂等，不改动屏数据以外的任何东西（`ui_flow_data.tjs` 由 m04 幂等重生成）。

## 本目录文件

| 文件 | 作用 | 幂等性 |
| --- | --- | --- |
| `run_all.py` | **34 步**一键复现 + 全闸门（见上；含第 9 批「标题首行左缘不变量」实测与变异自证两步、第 10 批 `m06` 基线总账一步）。★ 第 10 批起 `m01` **直接消费 `m06` 的总账**，故**未提交窗口内也能全绿**（此前会因「本批改动尚未提交」而确定性红） | 是（末步还原交付样例） |
| `m01_screen1_appearance_diff.py` | ★ **第 8 批重钉**（批次自证；旧声明表已归档、本批声明为空 ＋ **③c 变异自证**）｜ **外观变更自证（声明内 / 意外分离）**：`git HEAD` vs 盘上现值的逐元素 21 个外观/行为字段比对；**每一处差异都必须在脚本内的 `DECLARED_CHANGES` / `DECLARED_NEW_ELEMENTS` / `DECLARED_NEW_PATTERNS`（元素族）声明表里**（声明了却没变 ⇒ 判「声明表过期」）；另有【①b】可见性旗标核对（**外壳件零旗标** / 图内容层全带旗标）与外观变化清单 | 幂等：会先确认盘上是 `screen1`，**不是就先跑一次无参生成还原**（故可能写屏文件，但只写金标值）；另往 `_out/` 落预设产物 |
| `m02_states_frag_variants.py` | ★ **第 8 批更新**：【A】`_dim` 改 image 口径（按种类取件／与底图件同几何同 nine）、新增 `_read` 判据；**新增【E】全库机检**（无 rect 版 `_dim`／`_read` 与 `_new` 不共存／`_read` 不出视口画布）｜ **运行态 / 番外独立层数据自证**（冻结 §一/§二）＋ **裁决 6**（`fc.state.*`/`flow_state` 只允许出现在 states 预设）＋ **第 2 批接线自证**（7 件 1:1＋删 nine＋action 空；付箋两件 nine 边距 ≤ 素材短边一半）；★ 第 3 批：返回键改**按组** `fc.frag<G>_back[_tx/_hit]`（文案/字号/同组 vis_when 逐条核对）；`fc.pbk_panel` 改为「外壳件 ⇒ **不带**层旗标」；★ 第 4 批：`frag` 档的入口热区由 6 个降为 **1 个**（裁决 4，见 m05） | 只写 `_out/`（可覆盖再生） |
| `m03_shell_and_delivery_loop.py` | ★ **第 3 批四条机检自证 ＋ 第 5 批组名底托**：① 外壳件**零**层旗标（逐 id 清单 + 计数）＋ 图内容层**全带**旗标；**①b ★ 第 5 批：6 组组名标签底板齐备**（与 title **同矩形**、**同层 `vis_when`**、**z 关系**正确）**＋逐组对比度 ≥4.5:1**（WCAG 复算 + 基坑对照 1.19:1）；② 交付样例 6 个入口 × 对应独立层 × 按组返回键的**进出闭环**；③ 独立层元素不带 `flow_state`/`_dim`/`_new`（裁决 4）；④ 独立层**每格过文字四判据**（复用生成器 `check_text_criteria` 复算 45 格） | 只写 `_out/`（可覆盖再生） |
| `m04_regen_flow_data_tjs.py` | ★ **第 8 批修正两处自身过期前提**（判别力自证改**变异式**；`复刻/flow_data.js` 比对补**换行归一**判据）｜ ★ **第 3 批旧元素寻址退场**：只重生成 `krkr/game/ui_flow_data.tjs`（`复刻/flow_data.js` 改道到 `_out/`，**不动 `复刻/`**）；核对旧 id 清零（git HEAD 57 处 → 0）、退场字段登记、拓扑齐备、`box_png` 无缺图、二次生成字节相同 | 幂等（生成器是纯函数；写 1 个产物 + `_out/`） |
| `m05_entry_hit_layer_scope.py` | ★ **第 4 批 · 裁决 4 机检自证：入口热区作用域闭环** —— 五预设逐一实跑复算「存在 `fc.entry.*_hit` ⇒ 其 `layer` 在该档确有元素」＋「每个已产层进出闭环」＋ `screen1` 6/6；含两条**反向自证**（注入悬空热区 / 删返回键，必须被拦下） | 只写 `_out/`（可覆盖再生） |
| `_out/` | ★ 第 8 批另存 `states_head.json`（**HEAD 版生成器**产出的 `states` 基线，做逐件 diff 证据）｜ `m02`/`m03`/`m05` 与手工跑 `--out` 落下的变体屏 JSON（`32_flowchart.{states,frag,screen1,screen2,ref150}.json`）＋ `flow_data.gen.js`（改道的 JS 产物） | 生成物，可删 |
| `_gate_logs/` | 派单命令 + 还原后复跑的**实跑输出存档**（逐条 .log，第 3/4/5 批已刷新） | 可删 |

## 第 8 批（`ISSUE-20260928-03` · 节点运行态两处修正）落点小结

| 项 | 出处 | 变化 |
| --- | --- | --- |
| **修「未解锁压暗件方角」真缺陷** | 派单 ①（主代理已定改法） | `fc.node.<NNNN>_dim` 由 `kind:"rect"`（方角 284×48 / `#000000` / `opacity 110`）改 **`kind:"image"`** —— 按节点种类取压暗件（`ui/x_ui_node_{section,select,frag}_dim.png`，件名冻结）、**几何与 `nine` 与该节点底图件逐字段一致**、**强度仍由元素 `opacity` 控（110）**、`z`／`vis_flag`／`vis_when` 不变。**根因（实测）**：节点可见实体面**四角是 r=16 圆弧、弧外透明**，方角矩形四角压在背景上 ⇒ locked 节点每角露出约 **55px 暗方角**（实测方角处 (8,10,13) vs 同型 available (15,18,24)）。**通用教训**已写进 `layout/_schema.md` 的 `fc_layer` 节：**强度由元素 `opacity` 控、形状由素材 alpha 控** |
| **新增「已读」绿对勾 `_read`** | 派单 ②（用户 2026-09-28 裁决「**丙方案**」） | `fc.node.<NNNN>_read`：`ui/x_ui_read_check.png` **20×20（1:1、无 `nine`）**、节点可见实体面左上角内缘 `(x+10, y+12)`、`z`＝节点 `z+6`（与 `_new` 同档）、`vis_flag:"fc.state.<NNNN>"`＋`vis_when:"visited"`、`opacity 255`；**三条落盘前机检**（完全落在实体面内 / 与 `_new` 不共存 / 不越出视口画布）。**`current` 不加对勾**（只留金环）；备选件 `x_ui_read_check_alt.png` **不接线** |
| **金标重钉** | 同上 | **只有 `states` 的元素内容变**（123 → **126**，＋3 `_read`）；五档 md5 全变，但 `screen1`/`screen2`/`ref150`/`frag` 的 **`content-sha256` 逐字不变** ⇒ 变因**仅屏 note 措辞**（本批口径追加到屏 note；`note` 不进 content-sha256）。`PRESET_TABLE` 与 `layout/_schema.md` 金标表已手改同步，`--refresh-golden` 真跑 |
| **`m02` 判据更新** | 同上 | 【A】`_dim` 改为「`kind=="image"` ＋ `asset` 按种类 ＋ 几何/`nine` 与同 tag 节点底图件逐字段一致 ＋ `opacity==110` ＋ 无 `color` 键」；新增 `_read` 全套判据（含落点余量数值）；**新增【E】全库机检**：① 全库无 `kind:"rect"` 的 `_dim`；② `_read` 与同 tag `_new` 不共存；③ `_read` 不越出图表视口/画布 |
| **`m01` 重钉（派单：给出新声明）** | ★ 既存缺陷（被本次实跑暴露） | `m01` 是**批次自证**，更新制说明其对象是「本批相对 `git HEAD`」；此前各批变更**已并入 main** ⇒ 旧声明表整体过期（③b 逐条报「声明了却没变」、`unused_pat` 报「一条都没命中」）⇒ `run_all` 第 25 步**恒红**。⇒ 按本批事实**重新声明为空**（本批 `screen1` 外观/行为字段一处未动），并**新增 ③c 变异自证**（内存副本注入 2 处字段变异 ⇒ 必须被检出）证明「未声明差异 0 处」不是恒真 |
| **`m04` 修正两处自身过期前提** | ★ 既存缺陷（同上） | ① 「判别力自证」原要求「`git HEAD` 版旧 id 必须 >0」——第 2 步修复并入 main 后 HEAD 本已 0 处 ⇒ 该守卫**必然误报**、卡住 `run_all` 第 13 步；改为**变异式**（内存注入 1 条旧 id ⇒ 必须检出），`git HEAD` 计数降为参考信息。② 末尾对 `复刻/flow_data.js` 的比对：本仓库 `core.autocrlf=true` ⇒ **工作区文本一律 CRLF**、生成器产物为 LF ⇒「逐字节」**必然 False**（差 = 行数个 CR），属**检出假象**；已补「**换行归一后**等价性」判据（实测 True ⇒ 内容同步） |
| **`verify_ui [3]` 解析器补齐** | ★ 既存缺陷（同上） | `_parse_dict` 原先**只认** `key: value` 一种字典元素形式；而 `gen_layout.py` 对**非标识符键**（如屏级 `flags_default` 的带点键 `fc.state.0001`）按 TJS2 文法发射**逗号式** `"fc.state.0001", "locked"` ⇒ 只要 `--preset states` 在盘上，`verify_ui [3]` 就误报「解析失败」（**判据未放宽**：解析结果照旧与 json/js 逐键比对；真语法错仍抛错，已用变异对照验证）。此前从未在「states 在盘上」跑过 `verify_ui` ⇒ 潜伏至今 |
| **`_schema.md`** | 同上 | 命名表 `_dim` 行改 image 口径（素材件名／同几何同 nine／opacity 110）＋**新增 `_read` 行**（20×20、位置、z、vis 口径、用户裁决）；`fc_layer` 节补**通用教训**（强度 by opacity、形状 by 素材 alpha）；`flow_state` 行同步；金标表五档重钉＋第 8 批重钉块 |
| **屏 `note`** | 同上 | **只追加**第 8 批两段（两处修正的口径与根因、为什么不用甲/乙案、`current` 不加对勾、本批数据面影响），**不改写旧句** |
| **证据** | 同上 | `_out/states_head.json` = **HEAD 版生成器**产出的 `states` 基线（md5 `21ecd73e…`，与第 7 批金标一致）⇒ 与现行逐件 diff：3 件 `_dim` 的 `kind/asset/nine/x/y/w/h/color` 变、**新增 3 件 `_read`**、**无删除**、`_new` 与 `opacity`/`z`/flag 一字未动 |

## 第 9 批（数据侧最后一处修复 · 「已读对勾」不变量）落点小结

> 起因：主代理第 8 批（`ISSUE-20260928-03`）新增「已读」绿对勾 `fc.node.<NNNN>_read`（20×20 @ **(x+10, y+12)**）；
> vision 复核实测：其**右缘在节点相对 +30**，而节点标题文字盒左缘 = `x_node+28`、**居中**渲染 ⇒
> 首行墨迹左缘 = `28 + (240 − w0)/2`。全量 712 条里有 **12 条**首行墨迹 < +29（最小 **+20.50**），会被对勾压住首字左边。

| 项 | 出处 | 变化 |
| --- | --- | --- |
| **新增落盘前自检（真不变量）** | vision 复核（本批 item ①） | 所有含文字节点（主干 ＋ 独立层）**首行墨迹左缘 ≥ x_node+30**（等价「首行墨迹 ≤ 236px」）；违反即**拒绝落盘**并逐条打印（id/标题/首行宽/左缘/行数）。实测 **712 条违规 0、最紧 +30.00**（`s04_03f1`） |
| **新增常量表 `TITLE_HARD_BREAK`（12 条）** | 本批 item ② | 在**自然断点**插硬换行 `
`（引擎/生成器都按 `
` 分段）；优先级 **A 全角开括号·引号·波浪之前** ＞ **B 句读标点之后** ＞ **C 拉丁空格**；每条的拼接**必须逐字等于**源文本（`assert` 守住）；断后**两行 ≤230px**（实测最大 202）。成因＝末尾**行首禁则字符**（如 `）`）被 `ui_theme_wrap` 强行并入本行 ⇒ 单行 247–255px |
| **变异自证** | 同上 | `--selfcheck-title-break`：① 真表 0 违规；② **删一条硬断行必越线**（`62_1b` 回到 +20.50）；③ **表清空 ⇒ 12 条违规**（与 vision 全量复算一致）⇒ 非恒真 |
| **交付样例唯一外观变更** | 同上 | `fc.frag6.0007_tx`（`62_1b`）：旧「无论何时·棱镜（性的意义上）」**单行 255px** ⇒ 新「无论何时·棱镜」/「（性的意义上）」**122/133px（左缘 +87）**；其余 11 条不在交付样例四档（`screen2`/`ref150`/`states`/`frag` 的 `content-sha256` **逐字不变**） |
| **金标重钉** | 同上 | `screen1` → `e07afbe3…`；其余四档 md5 变因**仅屏 note 措辞**（`content-sha256` 逐字不变）。`PRESET_TABLE` 与 `layout/_schema.md` 金标表已手改同步 |
| **`_schema.md`** | 同上 | 新增条目「**第 9 批 · 「已读对勾」不变量 ＋ `TITLE_HARD_BREAK` 硬断行表**」（含推导、A/B/C 断点优先级表、四条约束、成因与机检） |
| **`m01` 声明表恢复 ＋ 基线闸门** | 同上 | ★ **发现**：`git HEAD` 里那份屏文件实测是 **`--preset states` 的产出**（126 元素、含 `fc.state.*`、无 `fc.frag*`）⇒ 主代理第 8 批「历史各批已并入 main ⇒ 声明表重钉为空」的**前提不成立**。⇒ m01 新增 **⓪ HEAD 基线健全性闸门**（不健全时 ①②③③b④⑤ **大声警告并跳过**，仍跑 ①b/⑥/⑦）＋**恢复**声明表（8 条元素族 ＋ 1 条第 9 批 `sample` 变更）⇒ 基线修好后自动恢复全量比对。**处置项留主代理：把该提交的 `32_flowchart.json` 还原为 screen1** |
| **`m03` ⓪ 节** | 同上 | 新增机检：不变量（712 条 0 违规）／断行表逐条两行 ≤230／`fc.frag6.0007_tx.sample` 与表**逐字一致**／`screen1` 内带硬断行的文字件恰 **1 个**／`--preset states` **126 元素**（含 `_read` 3 件） |
| **`run_all`** | 同上 | 31 → **34 步**（第 9 批 +`--title-check-report`/`--selfcheck-title-break` 两步；第 10 批 +`m06` 基线总账一步） |

## 第 7 批（小修）落点小结

| 项 | 出处 | 变化 |
| --- | --- | --- |
| **组名底托换专用硬边件** | vision 复测加严（第 7 批 item 1） | `fc.frag<G>_title_bg` 的 `asset` 由复用的 `ui/x_ui_label_off.png`（355×60，**四边宽渐隐带**）改为**专用件 `ui/x_ui_fragtitle_bg.png`（444×52、硬边、不透明核心覆盖整张）**；几何 **444×52 @(66,192)**、**1:1、无 `nine`**（零九宫格缩放这条路退场）。起因：复用件拉到 420×38 后真不透明区仅 rows 7..30 / cols 13..406，文字框与其同框 ⇒ 首末字与笔画上下沿压在渐隐带上，**字形核心像素 5 分位对比度仅 1.04:1**（HTML 实测；中位 12.98 达标）。实测新件：`alpha==255` 占 **99.93%**（仅 4 角各几像素抗锯齿），**墨迹区（含外扩 2px）非全不透明像素 0 个**；核心众数 (227,235,244) ⇒ 对墨色 `#16223A` **13.18:1**（区域均值 12.41:1）。落盘自检：最长墨迹 396 + 2×12 = 420 ≤ 444 ⇒ **余量 24px**（两侧实边距各 24px，第 5 批那条「余量恰好为零」作废）；文字上下各留 **14px**（≥10） |
| **`edge_noroute` 调暗** | vision 实测（第 7 批 item 2） | `#6A6A7A` → **`#5A5A68`**（只改 `layout/palette.json` 该键值 + note）：原值在引擎深底 (39,45,59) 上 **2.59:1**，**比 `normal` 的 2.01:1 更亮** ⇒ 语义层级与亮度层级相反。调暗后三档与语义同序；`w=3`/无箭头不变；`test_flow_links` ⑥ 两条断言仍过。**交付样例 `screen1` 连线全 `normal` ⇒ 不改动其屏幕数据**（`--preset states` 的 noroute 边使其 md5 变化，属预期） |
| **金标重钉** | 同上 | `screen1` **289 元素**（元素数不变，几何/素材变）｜`frag` **145**（同上）｜`screen2`/`ref150` **元素数与 md5 均不变**（全 normal、无底托）｜`states` md5 变（noroute 色值内嵌） |
| **`_schema.md`** | 同上 | `fc.frag<G>_title`/`_title_bg` 行改准（新件名/444×52/1:1 无 nine/新余量 + 换件理由）；§links 逐档表 `noroute` 值改 `#5A5A68` + 第 7 批说明；金标表五组重钉 |
| **屏 `note`** | 同上 | **只追加**第 7 批两段（换件口径与理由、noroute 调暗口径）；第 5 批段内指向旧件的两处已加「已被第 7 批取代」标注 |

## 第 5 批（收口小修）落点小结

| 项 | 出处 | 变化 |
| --- | --- | --- |
| **独立层组名加「标签底板」**（真缺陷修复） | 主代理第 5 批 item 1 | 每组新增 **`fc.frag<G>_title_bg`**（image，素材复用主图标签 `ui/x_ui_label_off.png`、**零九宫格整图缩放**口径同 `fc.label.<N>`、**420×38 @(66,199)**、`z=24`＝标题 z−1、与标题/返回键**同组同 `vis_when`**）；标题文字件改为**与底板同一矩形**（`align:center`/`valign:middle`）—— **文字色 `@palette.psv_ink` 与字号 24 未动**。起因：组名墨色直画近黑舞台（`fc.dim`＋`fc.scroll` 合成 **(14,17,22)**）⇒ 对比度 **1.19:1 不可读**（HTML 实测；本机复算一致）；加底托后 **13.53:1**（底板核心实色 (228,238,250)）。落盘前自检「最长组名墨迹 + 2×12 ≤ 420」，违者拒绝落盘 |
| **`fc.zoom_minus`/`fc.zoom_plus` 过期描述订正** | 主代理第 5 批 item 2 | `source`/`note` 原写按下态 `_on` 为 **41×41**，实测三态**均为 29×29** ⇒ 改为现况（**按下不放大**）并补「『按下放大』登记为**缺口 G-2**（`state_assets` 无逐态几何）」 |
| **金标重钉** | 同上 | `screen1` **283 → 289 元素**（＋6 底托）｜`frag` **144 → 145**（＋1）｜`screen2`/`ref150`/`states` 元素数不变（md5/`content-sha256` 变因**仅 `source` 订正**）。`PRESET_TABLE` 与 `layout/_schema.md` 金标表已手改同步 |
| **`_schema.md`** | 同上 | 命名表 `fc.frag<G>_title` 行扩为 `_title` / `_title_bg` 两件；§四 `fc_layer` 节「独立层件」行补「顶栏 = 标签底板 ＋ 文字，与主图 `fc.label.*` 同惯例」 |
| **屏 `note`** | 同上 | **只追加**第 5 批段（底托口径 + 理由 + 复算对比度），不改写旧句 |
| **`_工作\ISSUE-20260928-02_第2步\接口冻结.md`** | — | **未动**（主代理自己的文件，由主代理同步） |

## 第 4 批（小收口 · 裁决 4）落点小结

| 项 | 出处 | 变化 |
| --- | --- | --- |
| **入口热区作用域** | 主代理第 4 批（裁决 4 落地） | `build()` 产 `fc.entry.<NNNN>_hit` 时**检查该组的独立层是否在本档产出**（`gi in frag_groups`）；未产出 ⇒ **不产热区**（入口 image/组名标签仍在，作**纯占位**、不可点）。生成器每次跑打印一行可判读说明（哪个档、哪几组因此不产热区）。落盘前自检由第 3 批的「按全量档/非全量档分叉」改为**无条件**：「存在 `fc.entry.*_hit` ⇒ 其 `layer` ∈ 本档产出层」 |
| **各档入口热区数** | 同上 | `screen1` **6/6**（不变）｜`frag` **1**（原 6）｜`screen2`/`ref150`/`states` **0**（原各 6）⇒ 元素数 283／144／133／112／123 |
| **金标重钉** | 同上 | 五预设 md5 全变；`screen1` 的 **content-sha256 逐字不变**（`b050a6cf…`，证明**只改 note 措辞**、内容未动）；其余四档元素内容随裁决 4 而变。`PRESET_TABLE` 与 `layout/_schema.md` 金标表已手改同步 |
| **`--frag-report` / 屏 note** | 同上 | 各补一句裁决 4 口径（`fc.entry.*_hit` 仅当该组独立层在本档产出时才产；未产出为纯占位） |

## 第 3 批（收口）落点小结

| 项 | 出处 | 变化 |
| --- | --- | --- |
| **外壳件不参与层旗标** | 主代理第 3 批 item 1（冻结书 §二 原写「117 件全部加」**作废**） | 61 件外壳**不再写** `vis_flag`/`vis_when`；层旗标由**图内容层**（`LAYER_OWNED_PREFIXES`）独家持有。生成器**落盘前双向自检**（外壳带旗标 ⇒ 拒；图内容缺旗标 ⇒ 拒） |
| **交付样例含 6 组独立层** | item 2 | `screen1` 的 `frag_groups` 由 `None` → `[1..6]`；G1–G5 全格、G6 12/20（超出者 `--frag-report` 列明）⇒ 入口→独立层→返回键闭环。元素数 124 → **283** |
| **按组返回键** | item 3 | 单件 `fc.fragback`/`fc.fragback_hit` **退场** → `fc.frag<G>_back` / `_back_tx`（文案**「返回主干」**，字号 27 / bold / `@palette.node_locked`，取 `fc.jump_tx` 口径）/ `_back_hit`（`action:flow_layer` + `layer:main`），与 `fc.frag<G>_title` 同组同 `vis_when` |
| **旧寻址退场** | item 4 | `工具/gen_flow_data.py` 删 `nodes[].el`/`branches[].el`/`edges[].els`/`buses[].el`/`links[].el`/`layout.wrap_elements`/`layout.bypass_elements`；退场说明由生成器写入**两个产物**文件头（`RETIRED_NOTE_LINES`）；并回写 `BOX_PNG`（原指向 4 个已不存在的 M18 期素材，属静默回退隐患 G-5） |
| **引号字典键防回归闸门** | item 5 | `工具/test_gen_sync.py` 新增 `GENERATED_ARTIFACTS` 登记表 + `check_tjs_quoted_keys()`（三条自证）+ `check_flow_data_no_legacy_ids()`（含非空自证/退场登记核对），**均计入退出码** |

## `m02` 机检清单（逐条都要过）

**A · `--preset states`（冻结 §一）**
- `flow_state` 五档（locked/available/visited/current/new）**全部出现**，且逐节点写出
- `locked` ⇒ 必有 `_dim`：rect / 色 `#000000` / `opacity 110` / 矩形＝节点**可见实体面** `x+6,y+8,284,48` / `z`＝节点 `z+1` / `vis_flag:"fc.state.<NNNN>"`+`vis_when:"locked"`
- `new` ⇒ 必有 `_new`：50×17 / 落点＝参照作 `(x,y−12)` 或回落 `(x+6,y+8)` / `z`＝节点 `z+6` / `vis_when:"new"`
- `available`/`visited` ⇒ **不得**产出叠加件；`current` ⇒ **不产元素**（两端程序化画环）
- 屏级 `flags_default` 的逐节点 `fc.state.<NNNN>` 与节点 `flow_state` **一一对应**；另有 `{"fc_layer":"main"}`
- 连线 **三档同屏**（normal/visited/noroute 各 ≥1）

**B · `--preset frag`（冻结 §二）**
- 独立层节点网格：**每行 3 个 / 横步 375 / 纵步 192 / 行首纵向偏移 90 / 原点＝图表视口左上 +(6,6)**
- 文字口径与主干节点**逐字段一致**（19px / 元素级 `line_spacing` 1.0 / 盒宽 240 / `x=x_node+28` / `max_lines 2` / 有 `sample`）
- **独立层不产连线**（无任何 `links` 端点落在独立层节点锚点上）
- `fc.entry.<NNNN>_hit` 的 `action=="flow_layer"` 且 `layer` 指向 `frag<G>`；**按组**返回键 `fc.frag<G>_back_hit` 的 `layer=="main"`
  （★ 第 3 批：单件 `fc.fragback_hit` 已退场；并核对 `_back_tx` 文案「返回主干」与 27px 口径、三者同组 `vis_when`）
- `fc_layer` 的 `vis_when` 取值集恰为 `["frag1","main"]`（主干件 vs 独立层件）

## 落盘要点（本轮数据面）

| 项 | 值 |
| --- | --- |
| 屏文件 | `layout/screens/32_flowchart.json`（生成器产出，禁手改） |
| 五预设金标 | 见 `工具/gen_flow_layout.py` 的 `GOLDEN` / `PRESET_TABLE` 与 `layout/_schema.md` 的金标表 |
| 全量数据 | `_工作/ISSUE-20260928-02_第2步/全量布局.json`（**无 `elements` 键**；元素化交编程组） |
| 色板新增键 | `layout/palette.json` 的 `edge_visited`(#3580A8) / `edge_noroute`（第 2 步 #6A6A7A；★ **第 7 批依 vision 实测调暗为 #5A5A68**） |
| 动作新增 | `flow_layer`（带 `layer`；两端把屏级 flag `fc_layer` 置为目标层） |

## 第 2 批（补接线）落点小结

| 元素 | 旧素材（HEAD） | 新素材（`normal`） | 几何 | 依据 |
| --- | --- | --- | --- | --- |
| `fc.fusen_edit` / `fc.fusen_reset` | `x_ui_fusen_off.png` | 同（补三态） | 145×48 不变（nine 保留） | 冻结 §三 · E1 接线 |
| `fc.pbkick` | `x_ui_branch_l.png`（占位） | `x_ui_pbkick_off.png` | 119×119 不变；**删 nine** | 裁决 1 |
| **`fc.pbk_panel`**（新增） | — | `x_ui_replay_panel.png` | 426×241 @1422,493；z=5 | 裁决 二.1 |
| `fc.zoom_minus` | `x_ui_arrow_left.png`（占位） | `x_ui_zoomout_off.png` | **29×8@1006,123 → 29×29@1006,112** | 裁决 二.2 |
| `fc.zoom_plus` | `x_ui_arrow_right.png`（占位） | `x_ui_zoomin_off.png` | 29×29 不变 | 裁决 二.2 |
| `fc.shift_lf` / `fc.shift_rg` | `x_ui_arrow_{left,right}.png`（占位） | `x_ui_shift_lf/rg_off.png` | 31×25 / 30×25 不变 | 裁决 二.3 |
| `fc.scr_up` / `fc.scr_dn` | `x_ui_arrow_{up,down}.png`（占位） | `x_ui_scroll_up/dn_off.png` | 31×31 / 31×30 不变 | 裁决 二.4 |

- 7 件的 `action` **一律空串**（行为属编程组）；7 件新件的 `normal` 与元素矩形**等尺寸** ⇒ **删 `nine`**；
  未与元素等尺寸的 2 件付箋保留 nine（边距 max 21 ≤ 素材短边 86×48 的一半 24）。
- `--frag-report` 打印 6 个番外组的**视口容量（3×4=12 格）与未产格清单**；
  ★ 第 3 批：交付样例 `screen1` 已产**全部 6 组**，故该清单＝「已产格上限的说明」——
  现仅第 6 组（20 章）溢出，**未产 8 格**（`sc_04…sc_10`、`sr`）。
- `全量布局.json` 的 `meta.known_gaps` 登记 4 条缺口（独立层运行态未定义 / `state_assets` 无逐态几何 /
  独立层 12 格上限 / 主干运行态只有声明）。
- ★ 第 3 批未决项 —— **以下为「第 5/6 批逐条订正后的现况」**（上一版三条已过期，逐条标注作废）：
  · `复刻/flow_data.js` —— **已同步**（2026-09-28 收口时**由主代理亲手**跑 `python 工具/gen_flow_data.py` 完成，
    **不是 E1 越权**）：盘上文件与生成器输出**逐字节相同**（md5 `fa4a16957837e8d7c82dfd0f0e0725d5c`，43,872 B），
    正文**无** `"el"`/`"els"`、**无**旧 `"flow.*"` 值（实测 0 处），`retired_addressing` 标记齐备。
    ⇒ 上一版「本轮未同步 / 仍含旧字段」**作废**；后续 agent **不要再跑一次去「修一个已修的东西」**
    （重跑是幂等的、结果字节相同，但没有必要）。
  · **G-5（`box_png` 缺图隐患）—— 已修**：生成器的 `BOX_PNG` 已回写为盘上**存在**的 4 件
    （`ui/x_ui_node_section_off.png` / `x_ui_node_select_off.png` / `x_ui_node_frag_off.png` / `x_ui_label_off.png`）；
    连跑两次产出的**两个产物**（`.tjs` 与 `.js`）里 **box_png 引用 4 种、缺件 0**，且 `x_gen_flownode`
    仅出现在**头部注释的订正句**里（**不是**任何字段的值）。⇒ 上一版「直接跑会把 `box_png` 静默回退成缺图引用」**作废**
    （该判断在写下的当批次成立，第 5 批已修）。
  · 非全量层档（`states`/`screen2`/`ref150`，以及只含第 1 组的 `frag`）的入口热区 —— **本条已由第 4 批「裁决 4」根治**：
    `fc.entry.<NNNN>_hit` 只在该组独立层**确实在本档产出**时才产 ⇒ 未产出的组**根本不产热区**
    （入口 image / 组名标签仍在，为**纯占位、不可点**），**不存在**「指向未产层」的悬空热区
    （机检 `m05_entry_hit_layer_scope.py`：五预设逐一复算 + 两条反向自证）。
    ⇒ 上一版「入口热区指向未产层（既知演示档行为、生成器每次跑打印 ⚠）」**作废**。
  · `_工作\ISSUE-20260928-02_第2步\E2_自证\` 下的 HTML 侧证据快照仍是**旧版本**（含已退场的 `fc.fragback`）——
    **引擎侧巡演由 krkr 组在带组名底托的数据上跑一次默认巡演**（第 5 批之后）。
