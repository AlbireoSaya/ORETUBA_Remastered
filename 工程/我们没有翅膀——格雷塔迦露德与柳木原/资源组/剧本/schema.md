# `scene.jsonl` schema 定稿（W6a ｜ 六源枚举同步 W10c / ISSUE-20260919-06）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：权威（接口 I2 的 `scene.jsonl` schema 定稿） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> **本文件是资源组 → 编程组接口 I2（总纲 §七）的正式 schema 定稿。**
> 定稿：2026-09-18（W6a）｜ **六源枚举同步：2026-09-19（W10c / `ISSUE-20260919-06`，分支 `issue/ISSUE-20260919-06-greta-delivery`）**
> 数据文件：`资源组\剧本\scene_<源>.jsonl`——**六源已全部落盘**：`scene_ot.jsonl`（本篇 367 场景）、
> `scene_otr.jsonl`（R 版亚衣线 55）、`scene_ota.jsonl`（After Story 172）、`scene_otp.jsonl`（前奏诗 59）、
> `scene_otv.jsonl`（PSV 美咲线 31）、`scene_np.jsonl`（涅布明日香篇 28），**合计 712 场景 / 96,755 行**。
> 构建器：`资源组\工具\build_scene_jsonl.py` / `build_scene_ot.py` / `build_scene_ota.py` / `build_scene_otp.py` /
> `build_scene_otv.py` / `build_scene_np.py`（均可复跑）
> 校验器：`资源组\工具\verify_scene_jsonl.py` 等六源校验器 ＋ **`资源组\工具\verify_schema_enums.py`**（枚举 × 数据一致性自检，`ALL_PASS`）

> ⚠️ **本次（W10c）修订的要点（必读）**：W6a 定稿时只有亚衣线（`s03c`）一源，原文写「其余源后续同构追加，
> schema 不变」——**该断言与事实不符**：六源落盘后，若干字段的实际取值集合**按源扩张**（`source_kind` 的 `ot`、
> `kind` 的 `other`/`summary`/`unknown`/`label`、`cn_base`/`cn_origin`/`text_source` 的源代号值、
> `align_method` 的 `ot_direct`/`otp_direct`/`np_*`）。本次**以数据为准修订契约**（不改任何 `scene_*.jsonl`），
> 并确立 **§二.0「枚举按源分域」** 这一根本事实：**同一字段在不同源取值集合不同**。
> 编程组校验/消费时必须按 §二.0 的「源 × 字段 × 取值」对照表分源处理，**不得用单一全局枚举硬校验**（否则会拒掉近半语料）。

---

## 〇、为什么是「一条记录 = 一个场景」

编程组要按剧情顺序串场景、配素材、装配选择支，**场景是编排的最小单位**；台词行是场景内部的数据。
若做成「一条记录 = 一行台词」，场景级字段（标题、后继、素材清单、选择支）会在每一行重复上千次，
且无法表达「选择支属于场景」这一结构。故定稿为 **JSONL 每行一个场景对象**，`lines[]` 内嵌台词行。

**JSONL 纪律**：每行一个完整 JSON 对象，可独立 `json.loads`；无外层数组、无行间依赖。

---

## 一、场景对象字段（必填/可空）

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | --- | --- |
| `scene_id` | string | 否 | `<源代号>_<脚本名>`，全局唯一。例 `otr_s03c_01a` |
| `source` | string | 否 | **结构来源**代号，固定 `otr`（R 版 `s03c` 是 55 场景的结构骨架） |
| `script` | string | 否 | 脚本名（无扩展名），如 `s03c_01a` |
| `source_kind` | enum | 否 | **按源分域**（§二.0）：`shared` / `branch` / `new`（R 版亚衣线等有 2009 对照的源）｜ **`ot`**（本篇自指标，367 场景；本篇即 2009，「与 2009 的关系」分类对其不适用）。见 §三.1 |
| `text_source` | enum | 否 | **按源分域**（§二.0）：本场景 `lines[].cn` **实际**取自哪一层（由行级 `cn_origin` 汇总，可审计）。取值＝**源代号集合** `ot`(376) / `otr_new`(31) / `mixed`(15) / `ota`(172) / `otp`(59) / `otv`(31) / `np`(28) |
| `title_jp` | string\|null | 是 | 场景标题日文 |
| `title_cn` | string\|null | 是 | 场景标题中文（经取文管线解析） |
| `title_variants` | array | 否 | 全部标题槽（含 `（Ａ）`/`（Ｃ）` 变体）；元素 `{offset, jp, cn, cn_origin}`。`title_jp/cn` 取「有 09 对照或有修正表的那个」，无则取最后一个（见 §三.4） |
| `game_date` | string\|null | 是 | 游戏内日期，格式 `MM/DD`。**仅当场景内日文出现显式 `○月○日` 时才填**，否则 `null`（不臆断，见 §四.3） |
| `game_dates` | array | 否 | 场景内出现的全部显式日期，元素 `{date, line_index}` |
| `phase` | enum\|null | 是 | **八值域**（W10b 定稿，见 §三.5）：`序` / `个人线` / `结局` / `真相` / `主线` / `框架` / `系统` / `null`。各源实际取值见 §三.5 表 |
| `route` | string\|null | **是**（仅 `ota`） | 线路名（各源取本源的线路标识，如 `otr` 为 `s03c 亚衣线`）。**可空**（W10c 实测修订）：`ota` 有 **15 个场景** `route=null`——`ota_22_1a`/`ota_22_2a`…`ota_22_2f`（7）＋`ota_23_1a`…`ota_23_2a`（7）＋`ota_sr`（1），正是 **D13 待裁决线（`22_*`/`23_*`）与系统场景**，归属未裁决故不臆断（见 §四.5）。其余五源一律非空 |
| `cast` | string[] | 否 | 出场角色（按首次出现排序）；旁白行计为 `旁白`；标题槽不计入 |
| `next` | string[] | 否 | 后继场景 `script` 名（来自脚本跳转标签，见 §三.3）；结局场景为 `[]` |
| `next_kind` | enum | 否 | `linear`(1 个) / `branch`(≥2 个) / `end`(0 个) |
| `choices` | array | 否 | 玩家选择支；元素见 §二.2。无则 `[]` |
| `line_count` | int | 否 | `lines[]` 长度 |
| `voice_count` | int | 否 | 本场景引用的不同语音 ID 数 |
| `assets` | array | 否 | 本场景引用的图像/音效（场景级，见 §三.6）；元素 `{ref, kind, out_relpath, hit}` |
| `assets_missing` | string[] | 否 | 未命中资源总账的引用（逐条列出） |
| `stats` | object | 否 | 本场景自证统计，见 §二.3 |
| `lines` | array | 否 | 台词行，见 §二.1 |

**「无空必填字段」口径**：上表「可空＝否」的字段一律非 `null`；数组字段允许 `[]`（表示确实无该项），
字符串字段允许 `""`（如空槽行的 `jp`/`cn`，那是**源数据本身为空**，非缺失）。

---

## 二、嵌套对象

### 2.0 「枚举按源分域」——本 schema 的根本事实（**编程组必读**）

六源（`ot`/`otr`/`ota`/`otp`/`otv`/`np`）的语料由**不同引擎、不同抽取器**产出，同一字段的**实际取值集合按源不同**。
W6a 定稿只覆盖 `s03c` 一源，故原文枚举是「s03c 专属」；六源落盘后各源构建器按**同字段、增补本源取值**的方式扩展
（字段名与类型未变，仅取值集合扩张，且各自在产出报告 §2 逐项说明理由）。

**机器可读的声明与自检**：`资源组\工具\verify_schema_enums.py`（只读、幂等）——声明集合＝本 schema 的副本，
逐字段核对「六源实际取值 ⊆ 声明集合」（全局越界 0）与「每源实际取值 ⊆ 该源登记取值域」（分源越界 0），
并反向列出「声明但当前不出现」的保留值。**改 schema 必须同步改该脚本**。

**源 × 字段 × 取值对照表（W10c 全量实测；括号内为该源计数）**：

| 字段 | `ot`（367） | `otr`（55） | `ota`（172） | `otp`（59） | `otv`（31） | `np`（28） |
| --- | --- | --- | --- | --- | --- | --- |
| `source_kind` | `ot`(367) | `shared`(21)/`branch`(3)/`new`(31) | `new`(172) | `shared`(36)/`new`(23) | `new`(31) | `new`(28) |
| `text_source` | `ot`(367) | `ot`(9)/`mixed`(15)/`otr_new`(31) | `ota`(172) | `otp`(59) | `otv`(31) | `np`(28) |
| `phase` | `序`1/`个人线`285/`结局`9/`真相`72 | `序`1/`个人线`53/`结局`1 | `序`4/`个人线`109/`结局`6/`null`53 | `序`1/`个人线`18/`结局`2/`主线`32/`框架`2/`系统`4 | `序`1/`个人线`28/`结局`2 | `序`2/`个人线`19/`结局`7 |
| `next_kind` | `linear`316/`branch`46/`end`5 | `linear`50/`branch`3/`end`2 | `linear`132/`branch`8/`end`32 | `linear`40/`branch`4/`end`15 | `linear`29/`end`2 | `linear`20/`branch`4/`end`4 |
| `lines[].kind` | `dialogue`33985/`other`21695 | `title`65/`dialogue`3743/`narration`3103 | `title`166/`dialogue`11667/`narration`6380 | `dialogue`5963/`other`3096 | `dialogue`2712/`narration`2192/`summary`27 | `dialogue`1077/`narration`767/`label`62/`unknown`55 |
| `lines[].cn_base` | `ot`55680 | `ot`2909/`otr_new`3962/`empty`40 | `ota`18179/`empty`34 | `otp`9059 | `otv`4930/`empty`1 | `np`1961 |
| `lines[].cn_origin` | `ot`55586/`fix_table`57/`retranslate`37 | `ot`2898/`otr_new`3851/`fix_table`46/`retranslate`76/`empty`40 | `ota`18167/`fix_table`12/`empty`34 | `otp`9043/`fix_table`16 | `otv`4916/`fix_table`14/`empty`1 | `np`1958/`retranslate`3 |
| `lines[].align_method` | `ot_direct`55680 | `audit`2889/`audit_empty`20/`jp_exact_fallback`20/`no_audit_entry`14/`new_scene_direct`3928/`empty_slot`40 | `new_scene_direct`18179/`empty_slot`34 | `otp_direct`9059 | `new_scene_direct`4930/`empty_slot`1 | `np_direct`1844/`np_engine_noise`27/`np_speaker_label`56/`np_menu_text`26/`np_option_string`8 |
| `choices[].cn_origin` | `ot`54 | `fix_table`2 | `ota`57 | `otp`9 | （无选择支） | `np`34 |

> **「同一字段在不同源取值集合不同」不是缺陷，是六源语料异构的如实反映。** 消费侧的正确做法：
> 按 `scene.source`（或文件名 `scene_<源>`）分派到该源的取值域，**不得跨源套用**。跨源统一枚举会在
> `kind`（`ot`/`otp` 的 `other`、`otv` 的 `summary`、`np` 的 `label`/`unknown`）与
> `align_method`（`ot_direct`/`otp_direct`/`np_*`）上直接拒掉 **24,935 行 `kind`** 与 **66,700 行 `align_method`**。
>
> ⚠️ **ISSUE-20260930-12 更新**：`lines[].cn_origin` 行的实测计数已按**六源语料重建后**（`fix_type=term_unify` 生效，见 §四.6 / `修正\_README.md` §三.3）刷新——`ot`/`otr` 侧新增 `fix_table`（由 `term_unify` 行产生），`ota`/`otp`/`otv` 的 `fix_table` 计数亦随该表并入而上升；行数守恒（`ot`55,680 / `otr`6,911 / `ota`18,213 / `otp`9,059 / `otv`4,931 / `np`1,961）。其余各行的计数在本次重建中未变。

### 2.1 `lines[]`（台词行）

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | --- | --- |
| `seq` | int | 否 | 场景内 1-based 序号（本模块自生成） |
| `index` | int\|null | 是 | 源 `台词对照.json` 的 `index`（标题槽等为 `null`） |
| `lineno` | int | 否 | 源 `台词对照.json` 的 `lineno`（1-based，用于回溯） |
| `kind` | enum | 否 | **按源分域**（§二.0）：`title` / `dialogue` / `narration` / **`other`** / **`summary`** / **`unknown`** / **`label`**（**源值，未改写**）。各值语义与来源见 §三.7 |
| `speaker` | string | 否 | 名字框中文（`speaker_cn`，已套用 `name` 流译名替换） |
| `speaker_jp` | string | 否 | 名字框日文（`speaker_jp`，译名替换的 JP 门控依据） |
| `voice` | string | 否 | 语音 ID（源值，可为 `""`） |
| `jp` | string | 否 | 日文原文（未截断、未改写） |
| `cn` | string | 否 | 中文（经取文管线：取文源 → 修正表 → 译名替换） |
| `cn_base` | enum | 否 | **取文基准层**（未受修正表与译名替换影响）。**取值集合 = `{ot, otr_new, ota, otp, otv, np, empty}`**——与 `修正\_README.md` §四.5 的「修正表来源门控映射」一一对应，见 §三.2.0 |
| `cn_origin` | enum | 否 | 该行 `cn` 的**主来源层**（取文基准层与修正层中优先级最高者）。**取值集合 = `{ot, otr_new, ota, otp, otv, np, fix_table, retranslate, empty}`**，见 §三.2 |
| `align_method` | enum | 否 | 该行取文的对齐方式，**按源分域**，见 §三.2.1 |
| `layers` | string[] | 否 | 实际生效的层（按应用顺序），如 `["ot","name_replace"]` |
| `fix_refs` | array | 否 | 命中的修正表条目；元素 `{table, locator, fix_type, cn_before}`。`fix_type` 枚举见 §四.6（含 `speaker_split`——**该值当前不进 `fix_refs`**，其生效须另比对 `speaker_jp`/`voice`）。⚠️ 原表条目的 **`old_text`/`new_text` 语义按 `fix_type` 分叉**——`term_unify` = 词形正则/替换值；其余 = 整句；见 `修正\_README.md` §三.3 |
| `name_replaced` | array | 否 | 命中的译名替换；元素 `{原词日文, 旧写法, 新写法, 字段}` |
| `empty_slot` | bool | 否 | 源为空槽（`jp` 与 `cn` 均空、`offset` 为 `null`） |
| `d14_exception` | string\|null | 是 | D14 例外标注，见 §四.2 |
| `audio` | string[] | 否 | 本行语音的素材相对路径（`资源总账.json` 的 `out_relpath`）；无语音则 `[]` |

> **与任务预设 schema 的差异（须说明）**：任务预设的 `lines[].assets`（**每行**引用的图像）
> **本模块不产出**。原因：Lucifen TOB0 的演出命令语义未逆向（总纲 §六 R1、流程图 §七.1），
> 图像/音效引用**无法与文本槽逐行对齐**——强行对齐即属臆断。故图像/音效一律挂到**场景级 `assets`**。
> 语音是消息表自带字段（`voice`），可逐行对齐，故保留 `lines[].audio`。

### 2.2 `choices[]`

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | --- | --- |
| `text_jp` | string | 否 | 选项原文（取自脚本字节码中的选择支串） |
| `text_cn` | string\|null | 是 | 选项中文。**为 `null` 表示语料中无该选项的译文**（选择支串不在消息表中），须补译 |
| `cn_origin` | enum\|null | 是 | **选项译文的来源层**（W6a2 新增）：`fix_table` / `retranslate` / `ot` / `otr_new` / `ota` / `otp` / `np`；语料无译文时为 `null`。取值口径同 §三.2 的行级枚举，`fix_table` = 由主代理裁决补入。**实测出现值**：`ot`54 / `fix_table`2 / `ota`57 / `otp`9 / `np`34（`otv` 无选择支） |
| `target` | string\|null | 是 | 目标场景 `script`。**为 `null` 表示选项↔目标的配对未逆向**。**实测非空 41 条**（`np` 34 ＋ `otp` 7），其余（`ot`/`otr`/`ota`）为 `null`。⚠️ **`target` 非空 ≠ 配对已确证**——是否确证**只看 `pairing_verified`**（`np` 34 条 `true`；`otp` 7 条 `false`）。见 §三.2.4 |
| `pairing_verified` | bool | 否 | 选项与目标场景的配对是否已确证。**这是配对的唯一权威标志**（`target` 非空不代表已确证） |
| `confirmed` | bool | 否 | 是否为**已确证的玩家选择支**（`true`）／仅为跳转分支（`false`） |
| `evidence` | string | 否 | 判定依据（文件 + 现象） |

> **`target = null` 的理由**：TOB0 的分支语义未逆向（总纲 R1）。`s03c_01d` 的选择支串
> `黙る`/`拒否る` 与跳转标签 `S03C_01D1`/`S03C_01D2` 均已实测存在，但**哪个选项跳哪个标签无法从字节码确证**
> （文件内 `S03C_01D2` 在 `S03C_01D1` 之前，仅能说明声明顺序，不足以断定分支配对）。
> 故 `target` 留 `null`、`pairing_verified=false`；两个候选目标记于场景级 `next`。
> 编程组实现分支时以 `next` 为准，配对可在实现/试玩阶段确定。

> ⚠️ **W10c 口径修订（「除涅布 34 条外一律 `null`」已过时）**：六源落盘后 `choices[].target` 实测非空
> **41 条 = `np` 34 ＋ `otp` 7**。`otp` 的 7 条（`otp_02_03g`→`02_03g1/g2/g3`、`otp_03_03b`→`03_03c1/c2`、
> `otp_03_03i`→`03_03j1/j2`）虽已填入目标 `script`，但 **`pairing_verified=false`**（配对依据是
> 「目标场景首条 `kind=other` 槽（＝该场景标题）的语义推定」，见 `前奏诗_产出报告.md` §五.7，**非字节码确证**）；
> `confirmed=true` 只表示「是已确证的玩家选择支」，**不等于配对已确证**。
> **消费侧铁律：判「配对是否可信」只看 `pairing_verified`，`target` 非空一律不得直接当作分支实现依据。**

### 2.3 `stats`

| 字段 | 说明 |
| --- | --- |
| `lines_by_origin` | `{cn_origin: 行数}` |
| `lines_by_source` | `{源 src: 行数}`（`mig`/`new`/`null`） |
| `corrections_hit` | 本场景命中的修正表条数 |
| `name_replace_count` | 本场景发生的译名替换处数 |
| `empty_slots` | 本场景空槽数 |
| `d14_exceptions` | 本场景 D14 例外行数 |

---

## 三、定稿规则与理由

### 3.1 `source_kind` 的判定（W7-1 已实测，直接采用）

| 类别 | 数量 | 判定 | 取文规则（D14） |
| --- | --- | --- | --- |
| `shared` | 21 | 与 2009 同名且 voice/jp 锚定验证通过 | 取**本篇**译文 |
| `branch` | 3 | 无同名 09 场景，但与父场景（`01d`/`04b`）jp 重合率 ≥50% | 重合行取**本篇**；非重合行取 **R 版** |
| `new` | 31 | 与任何 2009 场景 voice 重合 0、jp 重合 ≤6 | 取 **R 版**（本项目新译） |

**W10c 补记：`source_kind` 按源分域（§二.0），三值并非全局唯一取值。** 上表三值（21/3/31）是 **R 版亚衣线（`otr`）专属**的分类，判据是「R 版场景与 2009 本篇的关系」。其余源的实测口径：

| 源 | 取值 | 理由（各源产出报告 §2） |
| --- | --- | --- |
| `ot`（本篇） | **`ot`**(367) | 本篇**本身就是 2009**，「与 2009 的关系」分类对其无意义；故记**源代号自指标** `ot`（`build_scene_ot.py` 模块头注释明示） |
| `otr`（R 版亚衣线） | `shared`21 / `branch`3 / `new`31 | 上表原三值 |
| `ota`（After Story） | `new`(172) | 与 2009 无共有场景，语义＝「无对照源」，保持枚举封闭 |
| `otp`（前奏诗） | `shared`36 / `new`23 | 按**操作定义实测**：与 2009 同名脚本且 jp 重合率 ≥50% → `shared`；**`shared` 不改变取文**（前奏诗译文本身即独立翻译，D14 只排除 R 版正文） |
| `otv`（PSV 美咲线） | `new`(31) | 独立源，无 2009 对照 |
| `np`（涅布明日香篇） | `new`(28) | 2012 独立短篇集，与 2009 无共有场景 |

> **跨源未统一的口径（已如实登记，非缺陷）**：`ot` 用源代号、`ota`/`otv`/`np` 用 `new`、`otr`/`otp` 用 `shared`/`branch`/`new`。
> 这是各源构建器按自身「是否有 2009 对照」独立选择的结果，各自在产出报告 §2 说明理由。消费侧按 §二.0 分源处理；
> 若要跨源统一，须由主代理另定映射表（**不在本次 W10c 修订范围**）。

### 3.2.0 `cn_base` 的取值集合与 `修正\_README.md` §四.5 门控映射的一一对应（**W10c 新增，消歧义**）

**取文基准层（`cn_base`）的取值集合 = `{ot, otr_new, ota, otp, otv, np, empty}`。**

其中前六个**与 `资源组\修正\_README.md` §四.5「修正表来源门控映射」一一对应**（该表是修正表条目能否生效的唯一依据）：

| 取文基准层 `cn_base` | 对应条目 `source` | 取文语料（哪个源） | 实测行数 |
| --- | --- | --- | ---: |
| `ot` | `ot` | 本篇 `工程\我们没有翅膀\汉化\剧情汉化\<script>.sob.jsonl` | 58,589 |
| `otr_new` | `otr` | R 版 `台词对照.json` 的 `cn_full` | 3,962 |
| `ota` | `ota` | After Story 语料（`译文.json` / `台词.json`） | 18,179 |
| `otp` | `otp` | 前奏诗语料 | 9,059 |
| `otv` | `otv` | PSV 美咲线 `台词对照.json` | 4,930 |
| `np` | `np` | 涅布明日香篇语料 | 1,961 |
| `empty` | （无——空槽，不受门控） | 无文本槽 | 75 |

- **门控规则**（`_README.md` §四.5）：修正表条目**只在其 `source` 与该行 `cn_base` 对应时才生效**；
  被排除者逐条留痕（`corrections_gated_out`），未登记映射的 `source` 由构建器**报错中止**（fail loud）。
- **本条修正了 W6a 的自相矛盾**：W6a 的 `cn_base` 枚举只列 `ot`/`otr_new`/`empty`，与 §四.5 已预置的
  `otp→otp`/`ota→ota`/`otv→otv`/`ot→ot` 映射冲突（后者要求存在 `otp`/`ota`/`otv` 三个基准层值）。
  **本次以数据为准修订契约**：`cn_base` 取值集合补全为上述七值，与 §四.5 映射表**逐格对齐**。
- **各源构建器的门控映射常量**：并集 **6 项** = `{otr: otr_new, otp: otp, ota: ota, ot: ot, otv: otv, np: np}`，与 §四.5 映射表**逐格对齐**。
  （各源只声明本模块子集：`build_scene_ot.py:73` / `build_scene_otp.py:87` / `build_scene_ota.py:72` / `build_scene_otv.py:117` / `build_scene_np.py:78`；`otv→otv` 由 `build_scene_otv.py` 专表消费 `修正表_otv.tsv`，`np→np` 由 `build_scene_np.py` 消费 `修正表_np说话人译名.tsv`，ISSUE-20260919-06 新增）。

### 3.2 `cn_origin` 枚举与优先级（**本模块的核心可审计点**）

`cn_origin` 的**取文层部分与 `cn_base` 同集合**（`ot`/`otr_new`/`ota`/`otp`/`otv`/`np`），另加两个**修正层值**
（`fix_table`/`retranslate`）与 `empty`，合计 **9 值**。

| 值 | 含义 | 出现源 |
| --- | --- | --- |
| `ot` | 取自本篇 `工程\我们没有翅膀\汉化\剧情汉化\<script>.jsonl`（经 W7-1 行对齐审计的 `correct_cn_from_2009`，或 §三.2.1 的 jp 精确兜底） | `ot`、`otr` |
| `otr_new` | 取自 R 版 `台词对照.json` 的 `cn_full`（完整译文；`cn` 是等长截断形态，**不使用**） | `otr` |
| `ota` | 取自 After Story 语料（独立翻译，D14 合规） | `ota` |
| `otp` | 取自前奏诗语料（独立翻译，D14 合规） | `otp` |
| `otv` | 取自 PSV 美咲线 `台词对照.json` | `otv` |
| `np` | 取自涅布明日香篇语料 | `np` |
| `fix_table` | 被修正表覆盖，`fix_type ∈ {quote_add, quote_normalize, space_strip, marker_strip, **term_unify**}`（`term_unify` 为**词形级替换**，见 §四.6） | 行级：`ot`(57)/`otr`(46)/`otv`(14)/`ota`(12)/`otp`(16)＝**145**；选择支层：`otr`(2)（**ISSUE-20260930-12 更新**：`ot`/`otr` 侧行级由 `term_unify` 行产生——此前 `ot` 侧无 `fix_table` 取值） |
| `retranslate` | 被修正表覆盖，`fix_type = retranslate`（含 `かるら` 按场景世界分译 37 条、新增场景 76 条 mig 行重译、np 说话人标签 3 条补译） | `ot`（行级 37，`修正表_かるら.tsv`，ISSUE-20260919-09）/`otr`（行级 76）/`np`（行级 3） |
| `empty` | 空槽（无文本） | `otr`(40)/`ota`(34)/`otv`(1)＝**75** |

**优先级（高→低）**：`retranslate` > `fix_table` > 取文层（`ot`/`otr_new`/`ota`/`otp`/`otv`/`np`，**各源内互斥**） > `empty`。
`cn_origin` 取**生效层中优先级最高者**；取文基准层另记于 `cn_base`，全部生效层记于 `layers`，
故「每个字来自哪一层」可完整回溯。**译名替换不改变 `cn_origin`/`cn_base`**（它不改取文来源），
只在 `layers` 与 `name_replaced` 中记录。

> 实测（W6a2）：亚衣线范围内 83 条修正**全部为 `retranslate`**（无 `quote_add`/`quote_normalize`/`space_strip` 命中），
> 故本线路 `cn_origin` 分布中 `fix_table` 为 0 条——这是事实，非漏产。
> **其中 7 条被 §三.2.3 的来源门控排除**（`source=otr` 落在取文基准 `ot` 的共享场景标题上），
> 实际生效 **76 条**（全部来自 `修正表_新增场景mig重译.tsv`，落在取文基准 `otr_new` 的新增场景）。

#### 三.2.3 修正表来源门控（**W6a2 裁决；通用规则，对所有源模块生效**）

**规则：修正表条目只在其 `source` 与该行「取文基准层」`cn_base` 对应时才生效。**
被门控排除的条目**必须逐条留痕**（`_build_stats.json` 的 `corrections_gated_out`），不得静默丢弃。
契约见 `资源组\修正\_README.md` **§四.5**；映射表：`otr→otr_new`、`otp→otp`、`ota→ota`、`ot→ot`；
未登记映射的 `source` 由构建器**报错中止**（fail loud）。

- **理由**：条目 `source` 标的是「这条修正所针对的语料层」；若该行实际取文并非来自该层
  （典型：按 **D14** 共有场景整场取本篇），该条修正**无对象**，不得覆盖现取文。
- **实测（亚衣线）**：7 条 `source=otr` 标题条目落在共享场景（`cn_base=ot`）→ 不生效，标题取**本篇**译文；
  这 7 个场景的**日文标题在本篇与 R 版中逐字一致**，本篇译文即正确标题。
  排除前 `cn_origin` 分布 `retranslate` 83 / `ot` 2902；排除后 **`retranslate` 76 / `ot` 2909**（差额 7 条回归 `ot`）。
- **`source_kind` 与门控的关系**：`shared`/`branch` 场景中经审计或 jp 兜底取到本篇的行，`cn_base=ot`，
  一律不受 `source=otr` 条目覆盖；`new` 场景行 `cn_base=otr_new`，`source=otr` 条目照旧生效。

#### 三.2.1 `align_method` 取值（**按源分域**，§二.0）

**取值集合 = `{audit, audit_empty, jp_exact_fallback, no_audit_entry, new_scene_direct, empty_slot, ot_direct, otp_direct, np_direct, np_engine_noise, np_speaker_label, np_menu_text, np_option_string}`（13 值）。**

**（a）`otr` / `ota` / `otv` 用（跨源取文或直取本源的通用值）**：

| 值 | 含义 | 出现源 |
| --- | --- | --- |
| `audit` | W7-1 行对齐审计直接给出 `correct_cn_from_2009` | `otr`（2889） |
| `audit_empty` | 审计有该行记录但无 09 对照（→ 落 R 版文本） | `otr`（20） |
| `jp_exact_fallback` | 审计未覆盖（无 `index`，典型为标题槽），以 **jp 精确且两侧唯一** 匹配本篇行取译文 | `otr`（20） |
| `no_audit_entry` | 共有/分支场景中既无审计记录、jp 兜底也不适用（A/C 变体标题等） | `otr`（14） |
| `new_scene_direct` | 无跨源对齐动作，**直接取本源**译文（`ota`/`otv` 的正常直取；`otr` 的新增场景） | `otr`（3928）/`ota`（18179）/`otv`（4930） |
| `empty_slot` | 空槽 | `otr`（40）/`ota`（34）/`otv`（1） |

**（b）`ot` / `otp` / `np` 用（各源专属直取值，**命名沿用 `<源>_direct` 惯例**）**：

| 值 | 含义 | 来源（构建器） | 计数 |
| --- | --- | --- | ---: |
| `ot_direct` | **本篇专属**：直取本篇语料，**无任何对齐动作**（本篇即取文源本身） | `build_scene_ot.py`（模块头注释明示） | 55,680（`ot` 全量） |
| `otp_direct` | **前奏诗专属**：取本源译文、无跨源对齐；沿用兄弟模块 `ot_direct`/`np_direct` 命名（`前奏诗_产出报告.md` §2.1） | `build_scene_otp.py` | 9,059（`otp` 全量） |
| `np_direct` | **涅布专属**：正常直取本源译文 | `build_scene_np.py`（模块头注 4） | 1,844 |
| `np_engine_noise` | **涅布专属**：`jp` 等于引擎错误串 `指定されたラベルは見つかりませんでした。` 的行（引擎噪声，译文未翻译） | `build_scene_np.py` | 27 |
| `np_speaker_label` | **涅布专属**：说话人标签槽（`kind=label` 且非 `start_oretuba`，55 条 ＋ 承担标签功能的短 `unknown` 1 条＝56）；作品层规定标签不译 | `build_scene_np.py` | 56 |
| `np_menu_text` | **涅布专属**：`start_oretuba` 子篇目**菜单标题槽** | `build_scene_np.py` | 26 |
| `np_option_string` | **涅布专属**：`start_oretuba` 的**选择支选项串** | `build_scene_np.py` | 8 |

> **`np_*` 的判定优先级**（`build_scene_np.py:427-437`，按序）：`np_engine_noise` > `np_speaker_label`
> （`label` 非 start / 短 `unknown`）> `np_menu_text` / `np_option_string`（`start_oretuba` 非 34 号槽）> `np_direct`。
> 该组值标出**非正文槽**，便于编程组过滤（与 `kind` 的 `label`/`unknown` 交叉，见 §三.7 的 crosstab）。

**应用顺序**（严格按 `修正\_README.md` §八.4）：
```
① 按 source_kind 取文（本篇 / R版 cn_full）
② 套修正表（按 (source,file,locator) 三元组定位，不字符串匹配）
   └─ 先过 §三.2.3 来源门控：条目 source 与 cn_base 不符者不生效、逐条留痕
③ 套译名替换表（JP 门控 + 排除规则）
④ 组装
```

### 3.2.2 译名替换的排除规则（W6a 实测补充两条）

除 `译名统一口径.md` §六 的既有排除规则外，本模块实测发现两条**表外**风险并加了排除（键为 `(原词日文, 旧写法)`）：

| 规则 | 风险（实测） | 排除 |
| --- | --- | --- |
| `針生` → `针生同学` | 在已含敬称处产生 `针生同学同学` / `针生同学前辈`（`s03c_12b` 2 处） | `针生(?!同学\|前辈\|君\|先生\|小姐\|老师\|哥\|姐)` |
| `ガルーダ` → `伽鲁炟` | 把 `伊丹伽楼罗`（＝`伽楼羅`）误改为 `伊丹伽鲁炟`（`s03c_03b#216`，该行 jp 同时含 `ガルーダ` 与 `伽楼羅`） | 排除 `(?<!伊丹)伽楼罗`；且 `jp` 同时含 `伽楼羅` 时整条跳过（行级 JP 门控无法消歧） |

> **W6a2 已登记**：这两条排除规则已补入 `资源组\修正\译名统一口径.md` §六（只增不删）；
> `修正\*` 表本体仍未改（门控与排除均为**消费侧**规则）。
> 修复后亚衣线译名替换共 **63 处**，逐处 `before`/`after` 均记入行级 `name_replaced`，可审计。

#### 三.2.4 `choices[].target` 的实际口径与「配对是否确证」的判定（**W10c 实测修订**）

**实测（六源全量扫描 `choices[].target`）**：

| 源 | 选择支数 | `target` 非空 | `target=null` | `pairing_verified=true` | 备注 |
| --- | ---: | ---: | ---: | ---: | --- |
| `ot` | 54 | 0 | 54 | 0 | 选项串存在但分支配对未逆向 |
| `otr` | 2 | 0 | 2 | 0 | `s03c_01d` 的 `黙る`/`拒否る`（W6a2 补译） |
| `ota` | 57 | 0 | 57 | 0 | 同上口径 |
| `otp` | 9 | **7** | 2 | 0 | 见下 |
| `otv` | 0 | — | — | — | 无选择支 |
| `np` | 34 | **34** | 0 | **34** | `start_oretuba` 的 `_CallEx` 派发表 + 选项串配对（Tier A 字节码确证） |
| **合计** | **156** | **41** | **115** | **34** | — |

**`otp` 的 7 条非空 `target`（逐条）**：`otp_02_03g`→`02_03g1`/`02_03g2`/`02_03g3`（`はい`/`いいえ`/`どちらとも言えない`）、
`otp_03_03b`→`03_03c1`/`03_03c2`（`小娘のノリに合わせる`/`小娘のノリを断ちきる`）、
`otp_03_03i`→`03_03j1`/`03_03j2`（`それはあるかも`/`それはないだろ`）。
**这 7 条 `pairing_verified=false`、`confirmed=true`**——配对依据是「目标场景首条 `kind=other` 槽（＝该场景标题）的语义推定」
（`前奏诗_产出报告.md` §五.7），**非字节码确证**。

> ⚠️ **消费侧铁律**：**`target` 非空 ≠ 配对已确证。** 「配对是否可信」**只看 `pairing_verified`**：
> * `pairing_verified=true`（当前仅 `np` 34 条）→ 可作为分支实现依据；
> * `pairing_verified=false`（`otp` 7 条，以及所有 `target=null` 者）→ **不得直接实现**；编程组以场景级 `next` 为准，
>   配对留待实现/试玩阶段确定。
> `confirmed` 是「该串是否为已确证的玩家选择支」的独立标志，**与配对确证无关**，不可混用。

### 3.3 `next` 的来源

逐脚本扫描 R 版 `.tob` 字节码中的跳转标签串（形如 `S03C_01B`），映射为 `script` 名。
实测 53/55 场景恰有 1–2 个目标；`s03c_05a`、`s03c_20a` 为 0 个（路线终点/结局）。

- 1 个目标 → `next_kind = "linear"`
- 2 个目标 → `next_kind = "branch"`（`01d`、`02b`、`04b`）
- 0 个目标 → `next_kind = "end"`

**为何 `choices` 大多为 `[]`**：`01d` 的 `黙る`/`拒否る` 是**已确证的玩家选择支**（脚本内有选择支串 + 两个跳转标签）。
`02b`→`02c1/02c2`、`04b`→`04b1/04c` 虽有两个跳转目标，但**脚本内无选择支串**，
其触发条件（旗标？变体？）未判定（流程图 §九.3-4 亦列为待确认）→ **只记 `next`，不写 `choices`**，不臆断。

### 3.4 `title_jp`/`title_cn` 的取值

55 场景共 65 个 `kind=title` 槽（10 个场景有 `（Ａ）`/`（Ｃ）` 双标题）。
取值规则：优先取**有 09 对照或有修正表条目**的标题槽，否则取**最后一个**标题槽；全部槽记入 `title_variants`。
双标题场景的 A/C 语义（是否对应分支结果）未判定，**不作解释、不合并**。

### 3.5 `phase` 的取值（**W10b 定稿：由三值扩展为八值域**）

> **W6a 原状**：`phase` 只定 `序` / `个人线` / `结局` 三值（按亚衣线语境）。
> 实测六源产出后，`scene_ot` 用了 `真相`、`scene_otp` 用了 `主线`/`框架`/`系统`、`scene_ota` 用了 `null`，
> **均越出原三值且校验器未拦截**。W10b 扫描六源全部实际取值后**正式扩展枚举**（不改任何 `scene_*.jsonl` 数据），
> 六源校验器**统一按本值域校验，越界即报错**。

**值域（八值，闭集；消费方按此校验，不得放宽为「不校验」）**：

| 值 | 语义 | 使用源 |
| --- | --- | --- |
| `序` | 开篇 / 序文 | ot、otr、ota、otp、otv、np |
| `个人线` | 角色个人线正文 | 六源全部 |
| `结局` | 线路结局 / 尾声 | 六源全部 |
| `真相` | 真相 / 核心揭露层 | ot（`s04` 段 72 场景） |
| `主线` | 主线框架剧（非某一角色线） | otp（火烈鸟框架剧 32 场景） |
| `框架` | 元框架 / 剧场框架层 | otp（2 场景） |
| `系统` | 非剧情系统场景（引擎初始化 / 回想 / 制作人员 / 标题） | otp（4 场景） |
| `null` | **未归入以上任何层**（番外 / 待裁决 / 无剧情阶段证据）——**不臆断** | ota（53 场景：`22_*`/`23_*` D13 待裁决线 14 ＋ C/D/E 番外・劇場・おまけ层 39） |

**六源实际取值表（W10b 实测，扫描 `scene_*.jsonl` 的 `phase` 字段；合计 712 场景）**：

| 源 | `序` | `个人线` | `结局` | `真相` | `主线` | `框架` | `系统` | `null` | 合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ot`（本篇） | 1 | 285 | 9 | 72 | 0 | 0 | 0 | 0 | **367** |
| `otr`（R 版亚衣线） | 1 | 53 | 1 | 0 | 0 | 0 | 0 | 0 | **55** |
| `ota`（After Story） | 4 | 109 | 6 | 0 | 0 | 0 | 0 | 53 | **172** |
| `otp`（前奏诗） | 1 | 18 | 2 | 0 | 32 | 2 | 4 | 0 | **59** |
| `otv`（PSV 美咲线） | 1 | 28 | 2 | 0 | 0 | 0 | 0 | 0 | **31** |
| `np`（涅布明日香篇） | 2 | 19 | 7 | 0 | 0 | 0 | 0 | 0 | **28** |
| **合计** | **10** | **512** | **27** | **72** | **32** | **2** | **4** | **53** | **712** |

**为什么不归一化到三值（选项 B 被否）**：

1. `真相`（`ot` 的 `s04`）与 `个人线` 是**互斥的叙事层**，归入 `个人线` 会丢失「大路线真相章」这一编排信息（总纲 §六 将 `s04` 列为收束全线的最终章）。
2. `主线`/`框架`/`系统`（`otp`）**不是角色个人线**：`主线`＝火烈鸟框架剧、`框架`＝剧场元层、`系统`＝引擎初始化/回想/标题等**非剧情场景**。强行映射为 `序` 会把「非剧情系统脚本」与「剧情序文」混为一谈。
3. `null`（`ota`）承载的是「**尚未裁决/无阶段证据**」这一明确语义（D13 待裁决线、番外合集）；映射为任一实值都属**臆断**，违反 §四「不臆断」。
4. 归一化后信息不可逆恢复，而扩展枚举只需消费方多认 5 个值，**代价更低、信息无损**。

**本线路（`otr`）取值**：`s03c_01a` = `序`；`s03c_20a`（エピローグ）= `结局`；其余 = `个人线`（55 场景 = 1/53/1）。
亚衣线语料内**无「真相」层证据**（真相层在 `s04`），**未按剧情张力臆造**。

**校验落地**：值域常量集中在 `资源组\工具\_schema_enums.py`（`PHASE_ALLOWED`），
六源校验器（`verify_scene_jsonl.py` / `verify_scene_ot.py` / `verify_scene_ota.py` / `verify_scene_otp.py` /
`verify_scene_otv.py` / `verify_scene_np.py`）**一律 import 该常量**并逐场景校验，越界即计入验收失败。

### 3.6 `assets` 的口径

来源：`亜衣线资源\清单\素材清单.json` 的 `per_file[<脚本>].assets`（R 版提取时记录的图像/音效引用），
按 `out_relpath` 规则 `<源代号>_<原名>` 映射到 `krkr素材库\资源总账.json`。
`kind` 由原引用目录决定：`CHR`→`chr`、`PIC`→`pic`、`SE`→`se`、`BGM`→`bgm`。
**BGM 无法按场景挂接**：R 版 BGM 不按名引用（流程图 §7.2），素材清单亦无逐场景 BGM 字段 → 本模块不产出场景级 BGM，如实登记。

### 3.7 `lines[].kind` 的取值语义与来源（**W10c 新增；语义均取自构建器，非猜测**）

`schema` 对 `kind` 的口径是「**源值，未改写**」——即**由各源抽取器按其串形态分类后原样保留**。
故六源的取值集合**必然不同**（§二.0）。各值语义与来源如下：

| 值 | 语义 | 来源（哪个源的哪种槽） | 判定依据（构建器） | 计数 |
| --- | --- | --- | --- | ---: |
| `title` | 标题槽 | `otr`(65) / `ota`(166) | R 版 `台词对照.json` / After Story 语料的显式 `kind=title` 槽 | 231 |
| `dialogue` | 台词（说话人 + 语音标记） | 六源全部 | SOB0/TOB0/BGI/PSV 抽取器对含 `#<说话人>\<语音ID>$&` 标记的串分类 | 59,147 |
| `narration` | 旁白 / 地の文 | `otr`/`ota`/`otv`/`np` | 无说话人标记的正文串 | 12,442 |
| `other` | **非台词裸串** | `ot`(21,695) / `otp`(3,096) | SOB0 抽取器 `classify()` 按串形态分类：**含 `$&` → `dialogue`，否则 `other`（裸串）**（`本篇_产出报告.md` §2；`build_scene_ot.py` 模块头注释）。该值**涵盖标题 / 梗概 / 选项等**——`ot` 的章节标题即由「首条 `kind=other` 槽」承载（判据 `other 且 td=0 且 sel=0 且非梗概`，见 `build_scene_ot.py:363-372`）；`otp` 结构上无 `kind=title` 槽，篇章标题同样以**各脚本首条 `kind=other` 槽**表达（`build_scene_otp.py` 模块头注 3） | 24,791 |
| `summary` | **梗概**（非台词） | `otv`(27) | PSV `台词对照.json` 的 `类别 == "梗概"`（该语料 4,931 行 = 台词 4,904 + 梗概 27）；`build_scene_otv.py:467` 显式标 `kind = "summary"` | 27 |
| `label` | **说话人标签槽** | `np`(62) | BGI 语料 `明日香线_原文.json` 的 `kind=label`。62 条 = 说话人名 55（`鷹志`24/`明日香`24/`日和子`2/`明日香の後輩`・`アスカ姫`・`ホーク`・`幼女`・`老婆` 各 1）＋ `start_oretuba` 的 7 条菜单串。作品层规定**说话人标签不译**（`build_scene_np.py` 模块头注 2；`涅布明日香篇_产出报告.md` §4.5） | 62 |
| `unknown` | **未归类串**（菜单串 / 引擎错误串） | `np`(55) | BGI 语料 `kind=unknown`。细分：`np_engine_noise` 27（引擎错误串 `指定されたラベルは見つかりませんでした。`）、`np_menu_text` 21、`np_option_string` 6、`np_speaker_label` 1（承担说话人标签功能的短串 `侍女Ａ`）。见 §三.2.1（b）与下表 | 55 |

**`np` 的 `kind` × `align_method` 交叉表（实测，用于消费侧过滤非正文槽）**：

| `kind` \ `align_method` | `np_direct` | `np_speaker_label` | `np_menu_text` | `np_option_string` | `np_engine_noise` | 合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `dialogue` | 1,077 | 0 | 0 | 0 | 0 | 1,077 |
| `narration` | 767 | 0 | 0 | 0 | 0 | 767 |
| `label` | 0 | 55 | 5 | 2 | 0 | 62 |
| `unknown` | 0 | 1 | 21 | 6 | 27 | 55 |
| **合计** | **1,844** | **56** | **26** | **8** | **27** | **1,961** |

> **编程组的正确用法**：需要「正文台词」时，按源取 `kind ∈ {dialogue, narration}`（`ot`/`otp` 另含 `other` 中的正文），
> 并可用 `align_method` 排除 `np_engine_noise`/`np_speaker_label`/`np_menu_text`/`np_option_string` 与 `empty_slot`。
> **不得**把 `other`/`summary`/`label`/`unknown` 一律当台词——它们各自承载标题、梗概、说话人标签、菜单/错误串。

---

## 四、已知缺口（**不臆断，如实登记**）

### 4.1 每行图像/音效不可得
见 §2.1 说明（演出命令语义未逆向，总纲 R1）。

### 4.2 D14 例外（`d14_exception`）

| 值 | 含义 | 条数 |
| --- | --- | --- |
| `mig_no_2009_counterpart` | `src=mig`（新米来源）**且无 2009 对照行、亦未被修正表修复**，无法按 D14 用本篇替换 → 暂留 R 版文本并显式标注 | **12** |

> 实测 12 条：`s03c_01c#88`、`s03c_03c#226/228/231/243/264/267/271`（`Ｒ・Ｏ・Ｃ！` 等拟声/应援句）、
> `s03c_04c#36/37/38/39`（`…………。` 等省略号句）。**均为无实义的标点/喊话句**，
> R 版文本与原文形近（差异仅 `・`↔`、`），但仍属 `mig` 来源，故如实标注、不擅自改写。
> 新增场景的 76 条 `mig` 行已全部由 `修正表_新增场景mig重译.tsv` 重译（`cn_origin=retranslate`），**不构成例外**。

### 4.3 `game_date` 的证据口径
仅当场景内日文出现显式 `○月○日` 才填。实测 55 场景中**仅 `s03c_01c` 有显式日期**（`１１月２２日`–`１１月２６日`）。
其余场景只有 `日曜日` 等星期信息 → `game_date = null`（星期无法唯一确定日期，不臆断）。

### 4.4 选择支译文（W6a2 已补译）
`s03c_01d` 的 `黙る`/`拒否る` 不在消息表中，语料无译文。**W6a2 已按主代理裁决补译**：
`黙る` → **沉默**、`拒否る` → **拒绝**，并标 `cn_origin = "fix_table"`（见 §2.2）。
`target` 仍为 `null`、`pairing_verified = false`——TOB0 分支语义未逆向（总纲 R1），**不猜配对**。
（六源的 `target` 全量口径见 §三.2.4。）

### 4.5 `route` 可空：`ota` 15 个 `route=null`（**W10c 实测新增**）

W6a 原写 `route`「不可空」，但六源实测 `ota` 有 **15 个场景** `route=null`：

| 分组 | 场景 | 数量 | 成因 |
| --- | --- | ---: | --- |
| D13 待裁决线 `22_*` | `ota_22_1a`、`ota_22_2a`…`ota_22_2f` | 7 | 归属未裁决（`AfterStory_产出报告.md` §验收 7：`22_*`/`23_*` 的 `route`/`phase` **全为 `null`**，D13 待裁决） |
| D13 待裁决线 `23_*` | `ota_23_1a`…`ota_23_1f`、`ota_23_2a` | 7 | 同上 |
| 系统场景 | `ota_sr` | 1 | 系统 / 非剧情场景，无线路归属 |

> **本次以数据为准修订契约**：`route` 改为**可空**（仅 `ota`），并在 §一字段表注明。**成因＝D13 未裁决，非数据缺陷**；
> 其余五源 `route` 一律非空。映射为任一实值都属**臆断**（与 `phase=null` 同理，见 §三.5）。

### 4.6 `fix_refs[].fix_type` 枚举（**W10c 补全；含 `speaker_split`**）

**声明集合（8 值）= `{quote_add, quote_normalize, space_strip, marker_strip, retranslate, term_unify, speaker_split, speaker_translate}`。**

| 值 | 语义 | 是否进 `fix_refs` | 当前产物出现 |
| --- | --- | --- | --- |
| `quote_add` | 原文含 `「」` 但译文无任何引号 → 给译文加 `“…”` | 是 | **14**（`ota` 7 / `otp` 6 / `otv` 1） |
| `quote_normalize` | 译文用单引号 `‘…’` → 归一为双引号 `“…”` | 是 | **8**（`otp`） |
| `space_strip` | 仅删除前导全角空格 U+3000（`new_text = old_text.lstrip('　')`） | 是 | 0（保留值；本批无适用对象） |
| `marker_strip` | 剥离 `#说话人\语音ID$&` 与结尾 `$` 标记 | 是 | 0（保留值；本批无适用对象） |
| `retranslate` | 译文与原文不对应 → 按原文重译 | 是 | **116**（`ot` 37 `かるら` 按场景世界分译 / `otr` 76 新增场景 mig 重译 / `np` 3 说话人标签补译） |
| **`term_unify`** | **术语统一**（ISSUE-20260930-10/11 新增，**唯一出处 `修正表_裁决20260930.tsv`**）：把用户裁决定为「非采用变体」的**词形**统一成采用值。**该值的 `old_text`/`new_text` 语义与其余值不同**——`old_text` = 被替换**词形（正则）**、`new_text` = **替换值**（消费方 `re.sub` 词形替换，**非整槽覆盖**，见 `修正\_README.md` §三.3） | 是 | **123**（`ot` 57 / `otr` 46 / `otv` 13 / `ota` 5 / `otp` 2；`cn_origin=fix_table`；ISSUE-20260930-12 补记） |
| **`speaker_split`** | **修复 `#<说话人>\<语音ID>$&` 的 0x5C 误切**（cp932 中 `0x5C` 兼作「十/ソ/ク」等字尾字节，被抽取器 `classify()` 误当分隔符） | **否**（见下） | 表内 **70** 条，其中**生效 68**（`scene_ot` 范围） |
| **`speaker_translate`** | **补说话人标签的中文译名**（修 `speaker` 字段，`field=speaker`；`修正表_说话人译名.tsv`，source=`ot`） | **否**（见下） | 表内 **72** 条，**生效 72**（`scene_ot` 范围，`speaker` 中文标签补齐） |

> ⚠️ **`term_unify` 的 `old_text`/`new_text` 语义与其余 `fix_type` 不同（消费侧必须知道）**：其余值两者均是该槽**整句**（消费方整槽覆盖 `cn`）；`term_unify` 则是**被替换词形（正则）/替换值**（消费方 `re.sub` 词形级替换，只碰术语那几个字）。**`fix_refs`（记录 `{table, locator, fix_type, cn_before}`）本身不携带 `old_text`/`new_text`**，消费方须回原表按 `locator` 取用；语义分叉的权威说明见 `修正\_README.md` §三.3（ISSUE-20260930-12）。
>
> ⚠️ **`speaker_split` 与 `speaker_translate` 均不进 `fix_refs`（消费侧必须知道）**：`fix_refs` 记录的是**对 `cn` 字段的覆盖**；
> 而 `speaker_split` 修的是 **`speaker`/`voice` 两字段**（`field=speaker_voice`）、`speaker_translate` 修的是 **`speaker` 单字段**（`field=speaker`），二者**均不参与 `cn_base` 门控**
> （门控是「取文层」概念，`speaker`/`voice` 的取源与 `cn` 无关）。故它们**不出现在任何 `fix_refs` 中**——
> 实测：六源 `fix_refs[].fix_type` 出现 `{retranslate, term_unify, quote_add, quote_normalize}`（`term_unify` 由 ISSUE-20260930-12 补记，**进** `fix_refs`），**无 `speaker_split`/`speaker_translate`**。
>
> ⚠️ **2026-09-19 更正（ISSUE-20260919-09）**：上句原附注「且 `scene_ot.jsonl` 的 `fix_refs` **整体为空**」**已不再成立**——
> `修正表_かるら.tsv`（37 条，`field=cn`，`fix_type=retranslate`）接入后，`scene_ot.jsonl` 有 **37 行**的 `fix_refs`
> 记入该表（`cn_origin=retranslate`）；此前 `scene_ot` 的修正命中确为 0（`source` ∈ {otr, otp, ota} 与本模块 `cn_base=ot` 不符，全部门控排除）。
> 除这 37 行外，`scene_ot.jsonl` 其余行的 `fix_refs` 仍为空。
>
> **其生效须另比对 `speaker_jp`/`voice`**（比对方法，可复跑）：
> ```python
> # 表：资源组\修正\修正表_0x5C.tsv（source=ot，field=speaker_voice，70 条）
> # 定位：(script, lineno) 对应 scene_ot.jsonl 的 scene.script + lines[].lineno
> new_sp, new_v = row["new_text"].rsplit("\\", 1)   # 真说话人内不含 0x5C，末个反斜杠即分隔符
> assert line["speaker_jp"] == new_sp and line["voice"] == new_v
> ```
> **实测（W10c 复核）**：`修正表_0x5C.tsv` 70 条中 **68 条**落在 `scene_ot` 范围，
> 逐条比对 `speaker_jp`/`voice` **68/68 命中**（mismatch 0）；另 2 条落在 `s03c`（不由 `scene_ot` 消费）。
> 权威说明见 `资源组\修正\_README.md` §三.1。

### 4.7 六源消费侧必须知道的其它缺口（**W10c 汇总；不臆断，如实登记**）

| # | 缺口 | 实测 | 状态 |
| --- | --- | --- | --- |
| 1 | **`otv` 引用命名空间曾断裂** | `scene_otv.jsonl` 的 `assets[].out_relpath` 指向实际提取目录 `工程/我们没有翅膀PSV/素材/美咲线/…`（941 条），**非规范形态** `otv/<kind>/otv_<名>`（`PSV美咲线_产出报告.md` §4.2：美咲线 CG/立绘/音频不在 `资源总账.json` 中，强行写规范形态会 468 引用全 miss） | **由本次修复**（W10c 归一化 `out_relpath` 至 `otv/<kind>/otv_<名>` 并并入 `krkr素材库\otv\…`）；**最终落点与复跑结果见产出报告 / 由并行 editor 处理，本 schema 仅登记该缺口** |
| 2 | **`ota` 87 行 voice 无 audio** | `scene_ota.jsonl`：`voice` 非空但 `audio=[]` 共 **87** 行 | **源侧事实，非可修缺口**：After Story 源语料本身无对应音频（立绘 stem 被误判为语音）；`verify_scene_ota.py` A8 如实登记、不阻断 |
| 3 | **`np` 1,325 行 voice 无 audio** | `scene_np.jsonl`：`voice` 非空但 `audio=[]` 共 **1,325** 行（源侧 `语音缺失清单.tsv`，ASU 音库本机缺失，B5 无解） | 同上（源侧事实，以产出报告为准） |
| 4 | **`ot` 72 行中文 `speaker` 为空** | `scene_ot.jsonl`：`kind=dialogue` 且 `speaker_jp` 非空、`speaker`(cn) 为空——**原 72 行** | **已在本轮修复归零**：`修正表_说话人译名.tsv` 72 条已接入 `scene_ot.jsonl`；W10c 复算实测该口径 = **0** 行 |
| 5 | **`np` 两处 `next_kind="end"` 语义上非终点** | `涅布明日香篇_产出报告.md` §4.4：后继未确证，`next=[]`、`next_kind="end"` 是**枚举不足所致的如实降级**，候选登记于 `_build_stats_np.json.next_unknown` | 如实登记（schema 枚举 `linear/branch/end` 未扩展） |

> **状态口径**：缺口 1、3 的最终状态以对应产出报告为准；缺口 2 属**源侧事实、不可修**（措辞「并行修复」有误导，已更正）；
> 缺口 4 **已在本轮修复归零**（实测 0）。本 schema 只负责登记「消费侧必须知道」这一事实，**不代其它模块宣告修复完成**。

---

## 五、复现

**枚举 × 数据一致性自检（本 schema 的机器可读校验，只读、幂等、可复跑）**：

```bash
cd "E:/ZCode Workspace/Galgame"
python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_schema_enums.py"
# 预期输出末行：ALL_PASS = True（六源实际取值 ⊆ 声明集合，越界数 0；分源取值域越界 0）
```

**各源构建器 / 校验器**（六源已全部落盘）：

```bash
cd "E:/ZCode Workspace/Galgame"
# 亚衣线（W6a）：build_scene_jsonl.py / verify_scene_jsonl.py
# 本篇：build_scene_ot.py / verify_scene_ot.py ｜ After Story：build_scene_ota.py / verify_scene_ota.py
# 前奏诗：build_scene_otp.py / verify_scene_otp.py ｜ PSV 美咲线：build_scene_otv.py / verify_scene_otv.py
# 涅布：build_scene_np.py / verify_scene_np.py
python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_jsonl.py"
python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_jsonl.py"
```

**只读声明**：构建器对 `工程\我们没有翅膀\`、`工程\我们没有翅膀R\`、`资源组\修正\*`、
`资源组\krkr素材库\*` **一律只读**（含三张修正表与 `译名替换表.tsv` 本体）；只写 `资源组\剧本\`
与 `子代理工作区\ISSUE-20260918-06\W6a2\`（W6a2 起；W6a 产物保持原样）。

**W6a2 状态**：门控与选择支补译已落地，校验器 A3 逐条核对「生效 + 门控 + 未命中」三分类并独立复核门控落点；
`ALL_PASS = True`（7 项）。被门控的 7 条逐条见 `资源组\剧本\亚衣线_产出报告.md` §3.4。

**W10c 状态（2026-09-19，`ISSUE-20260919-06`）**：六源枚举已随数据同步——
`source_kind` / `text_source` / `kind` / `cn_base` / `cn_origin` / `align_method` / `choices[].cn_origin` /
`fix_refs[].fix_type` 全部补全为**实际取值集合**，新增 **§二.0「枚举按源分域」＋源 × 字段 × 取值对照表**，
`route` 修订为**可空**（`ota` 15 条 D13），`choices[].target` 修订为**实际口径**（41 条非空，含 `otp` 7 条 `pairing_verified=false`）。
**未改动任何 `scene_*.jsonl`**（`md5` 见工程记录）。自检脚本 `资源组\工具\verify_schema_enums.py` 输出 `ALL_PASS = True`。
本次修订的逐字段实测分布与验证命令见 `工程记录\2026-09-19_对于格雷塔迦露德与柳木原剧本契约的修改.md`。