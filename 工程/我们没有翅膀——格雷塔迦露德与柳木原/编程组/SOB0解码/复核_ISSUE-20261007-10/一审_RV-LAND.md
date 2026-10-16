# 一审 · RV-LAND（软表落地：判据收紧 / Fade 载体 / V 定名 / Rule 命名）

**结论：通过。** 论断 1–6 全部由独立脚本（不 import 被审 `_landing_audit.py`）逐位复算成立；
新判据经变异自证**非空洞**；`decode_sob0.py --check` 回归 `ALL_PASS=True`；14 列契约与事件产生路径未被命名/载体表污染；
`V_NAMING`/`COMMAND_CARRIERS`/`RULE_NAMING` 无「未达阈值却写成定论」的条目。仅有若干非阻塞提示（见文末）。

被审文件：
- `E:\ZCode Workspace\Galgame\临时\wt-sob\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\工具\decode_sob0.py`
- `...\编程组\SOB0解码\落地_说明.md`、`_landing_audit.py`、`_landing_audit.json`
- `...\编程组\SOB0解码\软表解出_说明.md` §十三.1 / §十三.3 / §十三.4

审查方式：只读。独立脚本落在 `子代理工作区\ISSUE-20261007-10\RV-LAND\`；未 import 被审脚本，未改被审文件，未用 git。
注：命名的**数据根**为 `E:\ZCode Workspace\Galgame`（`decode_sob0.py` 的 `DATA_ROOT` 默认值，可用 `GRETA_DATA_ROOT` 覆盖），
输入语料/PSV 时间线均从**主工作区**读取（worktree 内 `编程组\SOB0解码` 只放产物）。

---

## A. 独立复算

### A1 · 判据收紧逐源数字（claim 1）——**命中**

命令：`python -X utf8 rv_t1_lib.py`（自写 SOB0 解析器，逐场语料口径）

| 源 | 语料场 | 旧判据 classic | 收紧后 kept | 剔除 | 被剔文件 |
| --- | ---: | ---: | ---: | ---: | --- |
| ot | 367 | 49741 | 49741 | **0** | — |
| otp | 59 | 9623 | 9595 | **28** | history 10 / title 9 / title2 9 |
| otr | 55 行（21 唯一脚本） | 2954 | 2954 | **0** | — |

与文档 §T1.2 表（49,741→49,741 / 9,623→9,595 / 2,954→2,954）**逐位一致**。

### A2 · 不变性（claim 2）——**命中**

命令：`decode_sob0.py --out out_new` 与 `decode_sob0.py --no-map3 --out out_legacy`（均真跑，写入 RV-LAND），
再 `python -X utf8 rv_invariance.py`（按 `(scene_id, 节点偏移#i)` 对齐，节点偏移从 `evidence` 的 `node code#<i>` 提取）。

| 源 | new 行 | legacy 行 | 公共 | removed | added | 14 列单元格差异 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ot | 49741 | 49741 | 49741 | 0 | 0 | **0** |
| otp | 9595 | 9623 | 9595 | 28 | 0 | **0** |
| otr | 2954 | 2954 | 2954 | 0 | 0 | **0** |

三源表头逐字相同，且 == 14 列契约
`scene_id seq op target arg1 arg2 arg3 evidence confidence time_ms time_frame time_family time_conf slot`。
被剔的 28 个 `(scene_id, node#)` 全在 `otp_history / otp_title / otp_title2`——与 A1、文档一致。

### A3 · 假阳性口径 785 vs 1,140（claim 3）——**命中，文档订正正确**

命令：`python -X utf8 rv_t1_lib.py`（ot 全库 412 文件口径）

```
classic = 53769   cmd(kept) = 52984   removed(classic & !backed) = 785
probe fake = no_backing(1108) + backed_other(32) = 1140
no_backing tail-kind breakdown = {empty: 785, code: 323}
identity: classic - cmd = 785 ; probe nb - (classic-cmd) = 323
top files by no_backing: gallery 342 | func_lib 236 | op 137 | sr_02 68 | sr_04 60 | ...
```

⇒ **785 = 旧判据（尾 REF→空串）自身假阳性**（`classic − cmd`），**1,140 是探针形态级 `fake`**
（1108 无背书 + 32 有背书但尾 REF 非串区；其中无背书的 1108 = 785 + 323 条尾 REF 落代码区、旧判据本就不收）。
文档 §T1.3「1,140 多算 355（323+32）；以 785 为准」**成立**。上游 `软表解出_说明.md` §13.1 的订正同此。

### A4 · 被剔 28 条（claim 4）——**命中**

独立复算的 28 条被剔节点：全部落在 `otp` 的 `history.sob(10)/title.sob(9)/title2.sob(9)`；
V 位高 12 位**全为 `0x018`**（页面引用字 CREF）。样例（文件, 偏移, node#, V, k, 尾 REF）与文档 §T1.2 前 12 行**逐行一致**：
`history.sob 0x5b14 2853 0x1806B58 8 22569`、`title.sob 0x5db8 3238 0x180DC90 20 20968` …

### A5 · V 定名 precision（claim 5）——**命中（含 1 否证）**

命令：`python -X utf8 rv_vnam.py`（N = 语料场 ∩ PSV 金标场；ot N=362）

| V | 候选 | 节点 | V 场 | T 场 | base | 命中 | precision | recall | 反例 | 复算判定 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `0x7480` | Window | 932 | 329 | 336 | .9282 | 328 | **.997** | .9762 | 1 | 采纳 ✓ |
| `0x1B040` | InOut_Act | 209 | 75 | 100 | .2762 | 73 | **.9733** | .73 | 2 | 采纳 ✓ |
| `0x1AD18` | EyeCatchEnd | 538 | 311 | 316 | .8729 | 310 | **.9968** | .981 | 1 | 采纳（族）✓ |
| `0x1C8D0` | SetSceneName | 367 | 362 | 2 | .0055 | 2 | **.0055** | 1.0 | **360** | **否证** ✓ |
| `0x1FAD4` | SceneJumpDialog | 335 | 312 | 362 | 1.0 | 312 | 1.0 | .8619 | 0 | 未定（base=1.0）✓ |
| `0x17514` | Tag | 4333 | 321 | 362 | 1.0 | 321 | 1.0 | .8867 | 0 | 未定 ✓ |
| `0x14084` | Tag | 4026 | 321 | 362 | 1.0 | 321 | 1.0 | .8867 | 0 | 未定 ✓ |
| `0x19A68` | BgmStop | 1115 | 324 | 339 | .9365 | 324 | 1.0 | .9558 | 0 | 弱候选 ✓ |

- 否证项 `0x1C8D0` precision **.0055 ≈ 文档 .006**、360 反例——**成立**。
- `0x1AD18`：复算 `EyeCatch` 与 `EyeCatchEnd` 两 type **场覆盖同为 316、与 0x1AD18 各交 310**（场级完全共现）⇒ 文档「只能定到 EyeCatch 族、不写死 End」**成立**。
- `0x19A68` base .9365 **< 0.95**：按文档自定规则本可判「采纳」，落地表却降格为「候选（弱）」——**比规则更保守**，非超采。

### A6 · Fade 载体（claim 6）——**命中**

| 源 | V | 载体场(全语料) | 金标载体场 | PSV `FadeOut(time>0)` 场 | 命中 | precision | recall | 载体场无 FadeOut |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ot | `0x19F9C` | **322** | 317 | **306** | 306 | 306/322=**0.950** | **1.00** | **16** |
| otp | `0x172BC` | 43 | 14 | 14 | 14 | 14/43=0.326 | 1.00 | 0 |

- 文档订正「322 是载体场数、FadeOut(time>0) 只有 306」**成立**（复算 `|FadeOut|` 恰为 306，`|FadeIn|`=8）。
- 附加复算：ot 载体 ms 主值 `{1200:296, 800:116, 1600:5, 1000:5, 500:4}`、`1200×0.06=72` 与 PSV FadeOut 主时长 72（289 例）一致；
  **全库**（412 文件）`0x19F9C` 463 节点、ms `{1200:316, 800:120, 1600:5, 1000:5, 500:4}`——与文档「全库口径 463 节点」逐位一致。
- otp `0x172BC`：**金标场 ms≠0 节点 13/13** 的 `round(ms×0.06)` ∈ 该场 PSV time 集合（复算 13/13）——成立。
- T2 落地实效：v4（主工作区旧版）otp time 行 **765 / 覆盖 46 场** → v5 **810 / 覆盖 51 场**（`fadeend` 贡献 45 行）。与文档 §T2「765→810、46→51」一致。

### A7 · T4 附加复算——**命中**

`func_lib.sob` 串区 **2,926 B / 316 条 ASCII 串**，`SYS\RULE%03d.ELG` 出现 ×2；
PSV 时间线 `rule` 列非空 **1,413 行 / 44 个不同值 / 值域 0–111`——三者均与文档 §T4 一致。

---

## B. 回归验证（--check + 14 列契约）——**通过**

> 注：复核任务给出的命令带 `--data-root`，**该选项在本工具不存在**，会直接 `error: unrecognized arguments: --data-root`。
> 正确复跑命令（即文档 §0 的写法）为去掉该参数；数据根由 `DATA_ROOT` 默认值 / `GRETA_DATA_ROOT` 指定。

命令：`python -X utf8 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/decode_sob0.py --check`

```
[--check] 只读模式：不写 解出_*.tsv / 对账_逐场.tsv / _stats.json
[ot] 解出表幂等 PASS（49741 行）
[otp] 解出表幂等 PASS（9595 行）
[otr] 解出表幂等 PASS（2954 行）
[_stats.json] 幂等 PASS
[时间] 行路径 = 节点路径（一致性自检 PASS；…）
ALL_PASS = True
```

- **14 列契约**：worktree 的 `HEADER` 与落地前（主工作区副本 `工程\…\工具\decode_sob0.py`）**逐字相同**，均 14 列同序。
- **事件产生路径未被命名/载体表污染**：`grep` 全文件，`V_NAMING` / `COMMAND_CARRIERS` / `RULE_NAMING` **仅出现在 `main()` 末尾的打印段（行 1349–1361）**，
  事件生成路径（`extract_scene` / `node_time` / `node_slot` / `command_nodes`）**不引用**这三张表。
  唯一进入事件路径的落地项是 `TIME_FAMILY` 新增的 `otp 0x172BC`（T2 的实质改动，见 A6），非命名/载体表所致。

---

## C. 变异自证（判据非空洞）——**通过**

命令：`python -X utf8 rv_mutate.py`
构造最小 `mutroot`（3 场子集语料 + 拷贝的 `.sob`，无 PSV），先跑基线，再把 `s00_00.sob` 的
`maps[3]` 中一个键 `540`（真命令节点 V 位站点，`V=0x19F9C`）改写为哨兵 `0x7FFFFFFC`（= 令该节点**失去背书**）：

```
baseline rows = 323
MUTATED s00_00.sob: kept node i=134 site=540 (V=0x19F9C) key -> 0x7FFFFFFC
=== after mutation, default --check ===
!! [ot] 解出表幂等失败
!! _stats.json 幂等失败
ALL_PASS = False
=== after mutation, --no-map3 --check ===
[ot] 解出表幂等 PASS（323 行）
```

- 默认判据下，改一个 `maps[3]` 键即令该节点被剔、`--check` **FAIL**；
- `--no-map3`（忽略背书）下同一变异文件的 TSV **PASS**。
⇒ **新判据非空洞、可失败**。（`--no-map3` 那次 `_stats.json` 报错仅因 `map3_backed` 标志位不同，属预期，TSV 行级 PASS 才是判据证据。）
附带发现：基线（无 PSV 数据根）在**输出全部写完后**的汇总打印崩溃，见提示 2。

---

## D. 命名/载体表阈值审查——**通过（无超采）**

- `V_NAMING` 8 条判定逐条复算（见 A5）：3 条「采纳」均满足 precision ≥ 0.67 且 base < 0.95；5 条「未定/否证/弱候选」均因不达阈值或全覆盖型 type。**无「未达阈值却写成定论」的条目。**
- `COMMAND_CARRIERS`：ot/otp 两条均标「不写『已解决』」，ot 明列 16 场反例、otp 明列「precision 0.326、反例不可测」。**未掩盖低 precision。**
- `RULE_NAMING`：`conversion` 明写「**不可推**：两条互斥假设并存 + 缺 `RULE###.ELG` 件本体」。**未越界定论。**
- `_landing_audit.json` 重跑（`--json`）与盘面既有产物**逐字节等价**（canonical 后 diff 为空）——可复跑证据成立。

---

## 打回项

**无。** A–D 全部满足；论断 1–6 与文档逐位一致；判据非空洞；回归 PASS；无超阈值定论。

## 提示（非阻塞，供主代理裁量）

1. **复核任务给的命令不可用**：`decode_sob0.py` **没有 `--data-root` 选项**（argparse 会报 `unrecognized arguments`）。正确的复跑命令是文档 §0 的写法（无该参数），数据根用 `GRETA_DATA_ROOT` 覆盖。文档本身写法正确，仅任务口径有误。
2. **汇总打印崩溃（既有缺陷，非本批引入）**：`decode_sob0.py:1347` `print("命令身份 V→Tasktype 自洽率 %.4f" % (sc["rate"], …))` 在 `V→Tasktype` 无数据（`rate is None`，如数据根缺 PSV 时间线）时抛 `TypeError: must be real number, not NoneType`，进程 `exit=1`。经比对，**落地前的主工作区副本同处（行 1195）同写法**，属既有缺陷；崩溃发生在**产物写盘之后**，且真实单源跑（`--src otp` / `--src otr`）rc=0，不触发。建议加 `None` 保护。
3. **`--limit` 是死选项**：`--limit` 已声明，但全文件无任何使用点（`grep` 无命中），与帮助文本「每源最多处理多少场（调试）」不符。
4. **文档自相矛盾**：`落地_说明.md` §未决问题 3 称「本批按『不覆盖既有文档』原则**未改上游文档**」，但 `软表解出_说明.md` 现含 §十三（标题明写「ISSUE-20261007-10 的订正与引擎侧发现」，§13.1 称「已全篇更正」）——上游文档**确已被本批改动**（mtime 22:26 晚于落地说明 22:18）。该「未改上游文档」表述已过期，请主代理校正或确认。
5. **两条阈值口径不一致（已披露）**：T3 定名用 precision ≥ 0.67，而 T2 登记的 `otp 0x172BC` Fade 载体 precision 仅 **0.326**（因 29 个载体场无金标）。文档与代码均如实标注，且其依据是 recall 1.00 + 金标 ms 13/13，可接受；但该载体**进入 `TIME_FAMILY` 会实际改变 otp 输出**（765→810 行），故此处低 precision 属功能性采纳，建议后续复核时留意口径差异。
6. **审计产物措辞过强**：`_landing_audit.json` 对 `0x1AD18` 的 `verdict` 写「采纳：EyeCatch(End)」，与落地表 `V_NAMING`（「EyeCatch / EyeCatchEnd（场级不可分）」）及文档「不写死 End」略有不一致；`0x19A68` 审计写「候选：BgmStop」，与落地表「候选（弱）」一致。仅机读产物措辞问题，需求侧以落地表为准。
7. **`软表解出_说明.md` §13.3 表头小瑕疵**：列头写「命中/载体场」，但表中填的是「V 场/T 场」（如 `0x7480` 填 `329/336`，实际命中 328）。数字无误，列名易误读。

## 补充说明（审查边界）

- 本审查未验证「V 是 func_lib 代码缓冲偏移 / 装载期重定位」这一逆向结论（需 capstone 反汇编 `ORE_TUBA.EXE`，超出本批落地范围）。
- `decode_sob0.py` 的输入（语料 jsonl、PSV 时间线、`.sob`）来自**主工作区** `DATA_ROOT`；worktree 内只产出 `解出_*.tsv`。若主工作区数据后续变动，worktree 产物可能与 `--check` 失配——现时 `ALL_PASS=True`。
- 未对 `对账_逐场.tsv` / `_stats.json` 做逐字段语义审查（仅以 `--check` 幂等与探针 `--check` 覆盖）。
