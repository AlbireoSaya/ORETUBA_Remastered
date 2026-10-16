# After Story（源代号 `ota`）结构化剧本产出报告 · W6c

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：历史快照（W6c 结构化剧本产出记录） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> 模块：**W6c**（S3 After Story → `scene_ota.jsonl`）｜ Issue：`ISSUE-20260918-06` ｜ 资源组
> 交付物：`资源组\剧本\scene_ota.jsonl`（172 场景）、本报告、
> `资源组\工具\build_scene_ota.py`（构建器）、`资源组\工具\verify_scene_ota.py`（独立校验器）、
> `资源组\工具\emit_w6c_report.py`（本报告数据段生成器）、
> `子代理工作区\ISSUE-20260918-06\W6c\{_build_stats_ota.json, W6c验收.json, _report_data.json}`
> **schema 依据**：`资源组\剧本\schema.md`（**W6a 定稿，本模块不另创**）；
> **取文顺序与来源门控**：`资源组\修正\_README.md` §四 / §四.5 / §八。
> **W11h 修订（2026-09-19）**：校验器新增第 8 项「引用命名空间可解析」——
> 逐条核对 `lines[].audio[]` 与 `assets[].out_relpath` 是否落在 `ota/` 命名空间且在
> `krkr素材库\` 下 `isfile`（此前 7 项只比对总账 stem 成员资格与 jsonl 自洽，**未做文件系统实测**）。
> 并如实登记「`voice` 非空但 `audio=[]`」的准确口径：**87 行 / 40 个唯一 ID，无对应素材，属已知缺口**
> （见 §6.4、§八-8）。本模块的 `scene_ota.jsonl` **本次未重跑、未改动**。

**只读声明**：`工程\我们没有翅膀 After Story\`（**一个字节都未改**）、`资源组\修正\*`、
`资源组\krkr素材库\*` 全程只读。写入仅限 `资源组\剧本\`、`资源组\工具\`、
`子代理工作区\ISSUE-20260918-06\W6c\`。**未提交 git**。

---

## 一、结论速览

| 项 | 结果 |
| --- | --- |
| 场景数 | **172**（＝172 个 `.tob`；其中 `sr.tob` 0 消息，如实产出空场景对象） |
| 台词行总数 | **18213** ＝ 正文 18,047 ＋ 标题 166；**逐文件对账差异 0** |
| `cn_origin` 分布 | {"ota": 18172, "empty": 34, "fix_table": 7} |
| `cn_base` 分布 | {"ota": 18179, "empty": 34} |
| 修正表 | 全表 150 条 ｜ **`source=ota` 范围内 7 条 → 命中 7 ｜ 未命中 0** ｜ 范围外 143 条（`otp` 14 ＋ `otr` 129）**门控排除、逐条留痕** |
| 引号判据独立复核 | 全库「原文含 `「`/`」` ⇒ 译文须含 `“`/`”`」扫描命中 **7** 条，与修正表 7 条**完全重合**；产出后复核命中 **0** |
| 选择支 | 记录 **40** 处 ｜ 场景 **20** ｜ 选项 **57** 条（源选项槽 73 − skip 16）｜ 提示 6 |
| 语音命中 | **10320 / 10407** 次引用；未命中 87 次 / 40 个 ID —— **逐条核实全部为「非语音声明串」（39 个立绘 CHR 差分名 ＋ 1 个 `cO255`），真实语音缺失 0** |
| 图像命中 | **722 / 722**（场景级去重条目；语料层原始逐消息引用 1056 次 / 363 个不同文件） |
| 译名替换 | 正文 **182** 处 ＋ 选择支 5 处 |
| 空槽 / D14 例外 | 34 / 0 |
| `next_kind` | linear 132 ｜ branch 8 ｜ end 32 |
| `phase` | 序 4 ｜ 个人线 109 ｜ 结局 6 ｜ **null 53**（未归入任何已定义剧情阶段层的层 ＋ D13 待裁决线；**W10b 起 `null` 为 `schema.md` §三.5 八值域内的合法值**） |
| `route` | {"AS 对决羽田鹰志": 21, "AS 对决千岁鹫介": 22, "AS 对决成田隼人": 19, "AS 对决羽田小鹰志": 28, "AS 美咲线": 9, "None": 15, "AS 最终统合线": 20, "AS 各线 after": 4, "AS 番外群像": 10, "AS おれつば剧场": 5, "AS おまけ": 19} |
| 7 项验收 | **ALL_PASS = True** |

---

## 二、本模块与 W6a（亚衣线）的结构差异（**决定构建器写法**）

| # | 差异 | 事实与依据 | 本模块处置 |
| --- | --- | --- | --- |
| 1 | **记录头 `op` 不固定** | `工程\我们没有翅膀 After Story\作品skill\SKILL.md:62` 明文「本作记录头的 op 不固定为 0x19（取 0x18/0x10/0x12 等多种），**不能靠 op 判定说话人**」 | **不重解字节码**：直接复用 `语料\译文.json` 的 `speaker`（由 `工具\parse_after.py` 按声明串窗口法解出，133 种、11,667 槽有说话人） |
| 2 | **`.tob` 头部无标签表** | 实测 172 个 `.tob` 的 `nlab = 0`（`tob_extract.parse_header` 返回 `labels=[]`），故 R 版那套「读标签段」在本作**取不到后继** | 改由**声明串扫描**取得跳转标签（`01 01 <u16 L> <S##_X> 00`，见 `scan_labels()`）；实测 172 个文件、141 个不同标签，**全部可解析到同名 `.tob`，未解析 0** |
| 3 | **修正表 locator 用 `idx=`** | `修正表_B1B3.tsv` 三种 locator 并存：`otr` 22 条用 `offset=`、`otp` 14 条用 `seq=`、**`ota` 7 条用 `idx=`**（= 消息 `index`） | 构建器按 `source` 分派 locator 语义；`ota` 用 `idx=<index>` 精确定位 |
| 4 | **图像引用是逐消息的** | `语料\台词.json` 的 `image` 字段（1,056 次，**全部 `PIC\*.ELG`**，363 个不同文件） | 按 schema §2.1「图像/音效只挂场景级」→ 取**场景内并集**写入 `assets`（去重后 722 条） |
| 5 | **语音字段含立绘误判** | 解析器判据 `^[A-Za-z]{2,4}\d{3,5}$` 把 39 个 **CHR 立绘差分名**（`CIN###`/`CIT###`/`LR2##`）与 1 个 `cO255` 判成了语音 | **保留源值**于 `lines[].voice`、`audio=[]`，**逐条列出**（§6），**不臆断回收** |
| 6 | **语料源 `kind` 只有 `line`/`title`** | 实测 18,047 `line` ＋ 166 `title`，**无 `dialogue`/`narration` 之分** | 按 schema 枚举**机械映射**：`title`→`title`；`line` 且说话人非空→`dialogue`；无说话人→`narration`（源值语义在 `speaker`/`speaker_jp` 完整保留，映射无损可逆） |

---

## 三、schema 落地说明（**未另创 schema**；下列为多源化必需的口径标注）

1. **字段集合与 `schema.md` 完全一致**（场景 22 字段 / 行 18 字段），**未增删任何字段**。
2. **枚举值 `ota`**：`source` / `cn_base` / `cn_origin` / `text_source` 取 `ota`。
   依据：`资源组\修正\_README.md` §四.5 **明文登记**了映射表 `ota → ota`（「After Story；该源模块产出时其取文基准记作 `ota`」），
   故 `ota` 是**契约内既有的取文层名**，非本模块新造。
   - `text_source` 恒为 `ota`（**本模块单一取文源，无 `mixed`**）。
3. **`source_kind` 一律 `new`**：schema 的三值（`shared`/`branch`/`new`）是 R 版 D14 分类口径；
   AS 是**独立翻译**、无 2009 对照源 → 全部场景归 `new`（语义＝「无对照源、本模块独立取文」）。**提请主代理确认该口径命名**。
4. **`align_method`**：正常行 `new_scene_direct`（＝本模块直接取 `ota` 语料，无跨源对齐）、空槽 `empty_slot`。
5. **`kind`** 见 §二.6；**`d14_exception` 全为 `null`**（AS 无 D14 跨源替换问题）。
6. **`choices[].cn_origin = ota`**：选项译文取自本模块自身的 `语料\选择支补译.json`；
   选项译文**同样过译名替换层**（JP 门控用 `text_jp`），替换明细记入 `choices[].evidence`（schema 无专用字段）。

---

## 四、修正表命中（`source=ota` 7 条全命中）

### 4.1 范围对账

| 表 | 全表条数 | `source=ota` 范围内 | 命中 | 未命中 |
| --- | ---: | ---: | ---: | ---: |
| `修正表_B1B3.tsv` | 43 | 7 | **7** | 0 |
| `修正表_B1B3_扩展.tsv` | 31 | 0 | 0 | 0 |
| `修正表_新增场景mig重译.tsv` | 76 | 0 | 0 | 0 |
| **合计** | **150** | **7** | **7** | **0** |

**独立复核（校验器 A3）**：7 条逐条核对「定位命中 ＋ 修正前文本逐字符等于表内 `old_text` ＋ 生效层为修正层 ＋ 最终 `cn` 一致」→ `A3_landing_verified = True`。
其中 3 条在修正层之后**又经过译名替换层**（`羽田同学`→`羽田君`），故最终 `cn` 与表内 `new_text` 不同，属**预期叠加**（`layers = [ota, fix_table, name_replace]`）。

### 4.2 7 条命中逐条证据

| # | 场景 | locator | jp | cn_before（=表内 old_text） | 表内 new_text | 最终 cn | 生效层 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11_5b | idx=17 | 「羽田君、友達？」 | 羽田同学、朋友？ | “羽田同学、朋友？” | “羽田君、朋友？” | ota → fix_table → name_replace |
| 2 | 11_5b | idx=45 | 「羽田君、話題」 | 羽田同学、话题。 | “羽田同学、话题。” | “羽田君、话题。” | ota → fix_table → name_replace |
| 3 | 11_5c | idx=65 | 「羽田君！」 | 羽田同学！ | “羽田同学！” | “羽田君！” | ota → fix_table → name_replace |
| 4 | 21_2c | idx=55 | 「佐久間君？」 | 佐久间同学？ | “佐久间同学？” | “佐久间同学？” | ota → fix_table |
| 5 | 21_2c | idx=57 | 「佐久間君……？」 | 佐久间同学……？ | “佐久间同学……？” | “佐久间同学……？” | ota → fix_table |
| 6 | 22_2d | idx=87 | 「どの子？」 | 哪个孩子？ | “哪个孩子？” | “哪个孩子？” | ota → fix_table |
| 7 | 24_2c | idx=15 | 「奥？」 | 里面？ | “里面？” | “里面？” | ota → fix_table |

### 4.3 独立引号判据复核（**先复核条数，再落表**）

判据：**原文含 `「` 或 `」` ⇒ 译文须含 `“` 或 `”`**，全库（18,213 槽）扫描：

- `jp` 含 `「`/`」` 的槽：**11,739**；其中译文**无任何中文引号**的：**7**。
- 这 7 条的 `(file, index)` 与修正表 `source=ota` 的 7 条**逐一对应、无一遗漏、无一多余** →
  **未发现第 8 条**（判据未发现新缺陷）。
- 应用修正表后再复核：命中 **0**（7 条全部已修复）。
- 附注：AS 全库译文用**中文引号 `“”`**（与 R 版全库用日式 `「」` 的约定不同），
  故本判据在 AS 上**安全可用**（不会像 R 版那样误报约 3 万条）——这是本模块与 W6a 的又一处差异。

### 4.4 范围外 143 条（门控排除，**逐条留痕**）

规则：`_README.md` §四.5——**条目只在其 `source` 与该行取文基准层一致时生效**；
本模块取文基准层恒为 `ota`，故 `otr`（129 条）与 `otp`（14 条）**在本模块无对象**，
由各自源模块消费（W6b/W6d 等）。**非漏修**。

| # | source | file | locator | kind | fix_type | 处置 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | otp | 02_03a.sob.jsonl | seq=17 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 2 | otp | 02_03a.sob.jsonl | seq=21 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 3 | otp | 02_03b.sob.jsonl | seq=73 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 4 | otp | 02_03b.sob.jsonl | seq=270 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 5 | otp | 02_03b.sob.jsonl | seq=409 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 6 | otp | 02_03e.sob.jsonl | seq=131 | dialogue | quote_add | 门控排除（本模块 source=ota，条目无对象） |
| 7 | otp | 02_03e.sob.jsonl | seq=135 | dialogue | quote_add | 门控排除（本模块 source=ota，条目无对象） |
| 8 | otp | 02_03e.sob.jsonl | seq=139 | dialogue | quote_add | 门控排除（本模块 source=ota，条目无对象） |
| 9 | otp | 02_03e.sob.jsonl | seq=371 | dialogue | quote_add | 门控排除（本模块 source=ota，条目无对象） |
| 10 | otp | 02_03e.sob.jsonl | seq=681 | dialogue | quote_add | 门控排除（本模块 source=ota，条目无对象） |
| 11 | otp | 02_03e.sob.jsonl | seq=831 | dialogue | quote_add | 门控排除（本模块 source=ota，条目无对象） |
| 12 | otp | 03_02a.sob.jsonl | seq=322 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 13 | otp | 03_02a.sob.jsonl | seq=1361 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 14 | otp | 03_02b.sob.jsonl | seq=369 | other | quote_normalize | 门控排除（本模块 source=ota，条目无对象） |
| 15 | otr | s01_03d.tob | offset=470 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 16 | otr | s01_08c0.tob | offset=558 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 17 | otr | s01_08f.tob | offset=666 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 18 | otr | s01_09b.tob | offset=1274 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 19 | otr | s01_14h.tob | offset=322 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 20 | otr | s01_18a.tob | offset=346 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 21 | otr | s02_03g.tob | offset=1622 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 22 | otr | s02_05c.tob | offset=462 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 23 | otr | s02_05d.tob | offset=706 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 24 | otr | s02_09e.tob | offset=438 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 25 | otr | s02_10c.tob | offset=906 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 26 | otr | s02_10d1.tob | offset=214 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 27 | otr | s02_14d.tob | offset=826 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 28 | otr | s03_03h.tob | offset=690 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 29 | otr | s03_08a.tob | offset=290 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 30 | otr | s03_14b.tob | offset=518 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 31 | otr | s03c_01c.tob | offset=614 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 32 | otr | s03c_01e.tob | offset=670 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 33 | otr | s03c_02c1.tob | offset=202 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 34 | otr | s03c_02c2.tob | offset=210 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 35 | otr | s04_03g.tob | offset=974 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 36 | otr | s04_22a.tob | offset=462 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 37 | otr | s01_04l.tob | offset=458 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 38 | otr | s01_05a.tob | offset=494 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 39 | otr | s02_03c.tob | offset=130 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 40 | otr | s02_10e.tob | offset=850 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 41 | otr | s02_11b.tob | offset=514 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 42 | otr | s03_05c.tob | offset=598 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 43 | otr | s03_05d1.tob | offset=198 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 44 | otr | s03_05d2.tob | offset=190 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 45 | otr | s03_06d1.tob | offset=526 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 46 | otr | s03_06e1.tob | offset=986 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 47 | otr | s03_06e2.tob | offset=1054 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 48 | otr | s03_09b.tob | offset=790 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 49 | otr | s03_14c.tob | offset=690 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 50 | otr | s03_18a.tob | offset=1526 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 51 | otr | s03c_01b.tob | offset=714 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 52 | otr | s03c_01d.tob | offset=486 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 53 | otr | s03c_03e.tob | offset=142 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 54 | otr | s04_05b.tob | offset=610 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 55 | otr | s04_08c.tob | offset=410 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 56 | otr | s04_10b.tob | offset=422 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 57 | otr | s04_26c.tob | offset=862 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 58 | otr | s01_14f2.tob | offset=450 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 59 | otr | s03_03c1.tob | offset=270 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 60 | otr | s03_03c2.tob | offset=222 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 61 | otr | s03_06d2.tob | offset=510 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 62 | otr | s03_11c.tob | offset=894 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 63 | otr | s03_12a.tob | offset=798 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 64 | otr | s04_27a.tob | offset=694 | title | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 65 | otr | s02_15b1.tob | offset=522 | title | space_strip | 门控排除（本模块 source=ota，条目无对象） |
| 66 | otr | s02_15c.tob | offset=1498 | title | space_strip | 门控排除（本模块 source=ota，条目无对象） |
| 67 | otr | s03_12i.tob | offset=726 | title | space_strip | 门控排除（本模块 source=ota，条目无对象） |
| 68 | otr | s03c_06a.tob | offset=2377 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 69 | otr | s03c_06a.tob | offset=2439 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 70 | otr | s03c_06a.tob | offset=2515 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 71 | otr | s03c_06a.tob | offset=2637 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 72 | otr | s03c_06a.tob | offset=2683 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 73 | otr | s03c_06a.tob | offset=2721 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 74 | otr | s03c_06a.tob | offset=3561 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 75 | otr | s03c_06a.tob | offset=4172 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 76 | otr | s03c_06a.tob | offset=4339 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 77 | otr | s03c_06a.tob | offset=4446 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 78 | otr | s03c_06a.tob | offset=4529 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 79 | otr | s03c_06a.tob | offset=4937 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 80 | otr | s03c_06a.tob | offset=5778 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 81 | otr | s03c_06a.tob | offset=6561 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 82 | otr | s03c_06b.tob | offset=2913 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 83 | otr | s03c_06b.tob | offset=12798 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 84 | otr | s03c_07a.tob | offset=5732 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 85 | otr | s03c_07a.tob | offset=7242 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 86 | otr | s03c_07a.tob | offset=7716 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 87 | otr | s03c_08a.tob | offset=2943 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 88 | otr | s03c_08a.tob | offset=6222 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 89 | otr | s03c_08a.tob | offset=12054 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 90 | otr | s03c_08a.tob | offset=12833 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 91 | otr | s03c_08b.tob | offset=6411 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 92 | otr | s03c_08b.tob | offset=9572 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 93 | otr | s03c_08b.tob | offset=15282 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 94 | otr | s03c_09a.tob | offset=5814 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 95 | otr | s03c_09a.tob | offset=8202 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 96 | otr | s03c_09b.tob | offset=10139 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 97 | otr | s03c_09b.tob | offset=15297 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 98 | otr | s03c_09b.tob | offset=16110 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 99 | otr | s03c_10a.tob | offset=4304 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 100 | otr | s03c_10a.tob | offset=8090 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 101 | otr | s03c_10a.tob | offset=11304 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 102 | otr | s03c_10a.tob | offset=13592 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 103 | otr | s03c_10b.tob | offset=12371 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 104 | otr | s03c_11a.tob | offset=10814 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 105 | otr | s03c_11a.tob | offset=11679 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 106 | otr | s03c_11a.tob | offset=12535 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 107 | otr | s03c_11a.tob | offset=12923 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 108 | otr | s03c_11b.tob | offset=7906 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 109 | otr | s03c_11c.tob | offset=6044 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 110 | otr | s03c_11c.tob | offset=45003 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 111 | otr | s03c_12a.tob | offset=7162 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 112 | otr | s03c_12a.tob | offset=11598 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 113 | otr | s03c_12b.tob | offset=9627 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 114 | otr | s03c_12b.tob | offset=10791 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 115 | otr | s03c_12c.tob | offset=4099 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 116 | otr | s03c_12c.tob | offset=13403 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 117 | otr | s03c_12c.tob | offset=27363 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 118 | otr | s03c_12c.tob | offset=30060 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 119 | otr | s03c_12c.tob | offset=30467 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 120 | otr | s03c_13a.tob | offset=8253 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 121 | otr | s03c_13a.tob | offset=28260 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 122 | otr | s03c_13a.tob | offset=33265 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 123 | otr | s03c_14a.tob | offset=21078 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 124 | otr | s03c_14a.tob | offset=34972 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 125 | otr | s03c_15a.tob | offset=12077 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 126 | otr | s03c_16a.tob | offset=2575 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 127 | otr | s03c_16a.tob | offset=15864 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 128 | otr | s03c_16b.tob | offset=11401 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 129 | otr | s03c_16b.tob | offset=13071 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 130 | otr | s03c_16c.tob | offset=7934 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 131 | otr | s03c_17a.tob | offset=4336 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 132 | otr | s03c_17b.tob | offset=3329 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 133 | otr | s03c_17c.tob | offset=11688 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 134 | otr | s03c_17c.tob | offset=23354 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 135 | otr | s03c_17c.tob | offset=25217 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 136 | otr | s03c_17c.tob | offset=25492 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 137 | otr | s03c_18a.tob | offset=7847 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 138 | otr | s03c_18a.tob | offset=8232 | line | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 139 | otr | s03c_18a.tob | offset=18361 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 140 | otr | s03c_18a.tob | offset=19306 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 141 | otr | s03c_18a.tob | offset=23707 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 142 | otr | s03c_19a.tob | offset=22469 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |
| 143 | otr | s03c_19a.tob | offset=22774 | dialogue | retranslate | 门控排除（本模块 source=ota，条目无对象） |

---

## 五、选择支对账（40 处）

### 5.1 对账结论

| 口径 | 本产物 | 已知数 | 差异 |
| --- | ---: | ---: | --- |
| 选择支记录（`选择支补译.json`） | 40 | 40（流程图 §4.5） | **0** |
| 涉及场景 | 20 | 20（＝40 记录 ÷ 2） | 0 |
| 选项槽（源） | 73 | — | — |
| 其中资源/语音 ID 型（`skip`，不译） | 16 | — | — |
| **玩家可见选项（写入 `choices[]`）** | **57** | 57 | **0** |
| 提示槽（`prompt`） | 6 | 6 | 0 |

**「标签为 `選択肢１/選択肢２/合流` 等 37 种」无法复现**：对 172 个 `.tob` 的全部
**13,459 个不同声明串**做穷举扫描，**不存在**任何含 `選択肢`/`合流` 的声明串；
AS 语料中 `選択肢`/`合流` 仅作为普通正文词出现（`11_1b#188`、`13_3c0#3`、`41_5#12` 等 6 处）。
`語料\选择支补译.json` 的实际构成是 **40 记录 / 6 提示 / 73 选项槽**。→ **提请主代理核实流程图 §4.5 该行口径**。

**分支结构**：8 个场景有 ≥2 个后继（`next_kind=branch`）——7 个是**选择支分支**（`11_3b0`/`11_3d0`/`12_3a0`/`12_4c0`/`13_3c0`/`14_6a0`/`14_6c0`），
第 8 个是 **`24_4e` → `24_5a` / `24_5c`（G-END / B-END，AS 双结局）**，其脚本内**无选择支串**（同 W6a 的 `02b`/`04b` 情形）→ 只记 `next`、不写 `choices`。
其余 12 个选择支场景（`24_1b`–`24_5a`）**只有 1 个后继**：选项不改变跳转目标（应是通过旗标影响后续内容），故 `next_kind=linear`。

### 5.2 `target` / `pairing_verified` 的口径（**不臆断**）

全部 57 条选项的 `target = null`、`pairing_verified = false`：TOB0 分支语义未逆向（总纲 §六 R1），
**无法从字节码确证「哪个选项跳哪个标签」**。编程组实现分支时以场景级 `next` 为准。

### 5.3 选择支逐条

| 场景 | next（候选目标） | next_kind | 选项 text_jp | 选项 text_cn | cn_origin | target |
| --- | --- | --- | --- | --- | --- | --- |
| `11_3b0` | 11_3b1/11_3b2 | branch | 胸パッドちゃんとは？ | 胸垫妹是怎么回事？ | ota | **null** |
|  |  |  | リンダリンダとは？ | 琳达琳达是怎么回事？ | ota | **null** |
| `11_3d0` | 11_3d1/11_3d2/11_3d3 | branch | 京 | 京 | ota | **null** |
|  |  |  | 渡来さんと組む | 跟渡来同学一组 | ota | **null** |
|  |  |  | 山科さんと組む | 跟山科同学一组 | ota | **null** |
|  |  |  | 針生さんと組む | 跟针生同学一组 | ota | **null** |
| `12_3a0` | 12_3a1/12_3a2 | branch | 日和子も誘ってみる | 也去邀请日和子 | ota | **null** |
|  |  |  | 明日香と二人で帰る | 和明日香两个人回家 | ota | **null** |
| `12_4c0` | 12_4c1/12_4c2 | branch | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | クリスマスを一緒に過ごします | 一起过圣诞节 | ota | **null** |
|  |  |  | 年越しを一緒に過ごします | 一起过年 | ota | **null** |
| `13_3c0` | 13_3c1/13_3c2 | branch | 学校はどんなカンジ？ | 学校怎么样？ | ota | **null** |
|  |  |  | 休日はどんなカンジ？ | 休息日怎么样？ | ota | **null** |
| `14_6a0` | 14_6a1/14_6a2/14_6a3 | branch | 『水上痴漢法』 | ‘水上色狼法’ | ota | **null** |
|  |  |  | 『ハイスクールロック「校内精巣編」』 | ‘高校摇滚“校内精巢篇”’ | ota | **null** |
|  |  |  | 『援交娘緊縛遊戯編～火遊びの代償は未熟なカラダ～』 | ‘援交妹紧缚游戏篇～玩火的代价是稚嫩的身体～’ | ota | **null** |
| `14_6c0` | 14_6c1/14_6c2 | branch | 高内さんと一緒に帰る | 跟高内同学一起回家 | ota | **null** |
|  |  |  | アニメ観たいから急ぐ | 想赶回去看动画 | ota | **null** |
| `24_1b` | 24_2a | linear | タカシ | 鹰志 | ota | **null** |
|  |  |  | ヨージ | 小鹰志 | ota | **null** |
|  |  |  | 伽桜羅 | 伽楼罗 | ota | **null** |
| `24_2b` | 24_2c | linear | タカシ | 鹰志 | ota | **null** |
|  |  |  | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | 隼人 | 隼人 | ota | **null** |
| `24_2c` | 24_2d | linear | タカシ | 鹰志 | ota | **null** |
|  |  |  | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | 隼人 | 隼人 | ota | **null** |
| `24_2d` | 24_2e | linear | タカシ | 鹰志 | ota | **null** |
|  |  |  | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | 隼人 | 隼人 | ota | **null** |
| `24_3b` | 24_3c | linear | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | 隼人 | 隼人 | ota | **null** |
|  |  |  | 伽楼羅 | 迦楼罗 | ota | **null** |
| `24_3c` | 24_3d | linear | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | タカシ | 鹰志 | ota | **null** |
|  |  |  | 隼人 | 隼人 | ota | **null** |
| `24_3d` | 24_3e | linear | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | タカシ | 鹰志 | ota | **null** |
|  |  |  | ヨージ | 小鹰志 | ota | **null** |
| `24_3e` | 24_4a | linear | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | タカシ | 鹰志 | ota | **null** |
|  |  |  | 伽楼羅 | 迦楼罗 | ota | **null** |
| `24_4b` | 24_4c | linear | 隼人 | 隼人 | ota | **null** |
|  |  |  | タカシ | 鹰志 | ota | **null** |
|  |  |  | ヨージ | 小鹰志 | ota | **null** |
| `24_4c` | 24_4d | linear | 隼人 | 隼人 | ota | **null** |
|  |  |  | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | 伽楼羅 | 迦楼罗 | ota | **null** |
| `24_4d` | 24_4e | linear | 隼人 | 隼人 | ota | **null** |
|  |  |  | 鷲介 | 鹫介 | ota | **null** |
|  |  |  | 伽楼羅 | 迦楼罗 | ota | **null** |
| `24_4e` | 24_5a/24_5c | branch | 隼人 | 隼人 | ota | **null** |
|  |  |  | 伽楼羅 | 迦楼罗 | ota | **null** |
|  |  |  | ヨージ | 小鹰志 | ota | **null** |
| `24_5a` | 24_5b | linear | ヨージ | 小鹰志 | ota | **null** |
|  |  |  | ヨージ | 小鹰志 | ota | **null** |
|  |  |  | ヨージ | 小鹰志 | ota | **null** |

> `24_5a` 的 3 条选项源值均为 `ヨージ`（解析结果如此，非本模块改写）——**如实保留**并登记，提请主代理核实是否为源提取缺陷。
> `24_1b` 的 `伽桜羅` 是**原作写形**（应为 `伽楼羅`），故 `伽楼羅→迦楼罗` 的 JP 门控不触发，其译文保持 AS 侧 `伽楼罗`（见 §7.3）。

---

## 六、素材挂接与命中率

### 6.1 命中率

| 类别 | 命中 | 总数 | 命中率 | 说明 |
| --- | ---: | ---: | ---: | --- |
| 语音（逐行 `lines[].audio`） | **10320** | 10407 | 99.2% | 未命中 87 次 / 40 个 ID，**逐条核实全部为「非语音声明串」**（见 6.2） |
| 语音（**剔除误判后**的真实语音） | **10,320** | **10,320** | **100%** | **真实缺失 0** |
| 图像（场景级 `assets`） | **722** | 722 | **100%** | 语料层原始逐消息引用 1056 次 / 363 个不同文件，**全部命中 `ota/pic`** |

映射规则：`台词.json` 的 `image` / `译文.json` 的 `voice` → `资源总账.json` 的 `out_relpath`（命名 `ota_<原名>`）。

### 6.2 语音未命中逐条核实（**40 个 ID**，真实缺失 0）

| # | token | 在 ota/chr 库中同名？ | 在任一源 voice 库中同名？ | 判定 |
| ---: | --- | --- | --- | --- |
| 1 | CIN002 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 2 | CIN005 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 3 | CIN021 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 4 | CIN022 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 5 | CIN031 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 6 | CIN046 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 7 | CIN048 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 8 | CIN051 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 9 | CIN053 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 10 | CIN054 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 11 | CIN062 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 12 | CIN065 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 13 | CIN068 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 14 | CIN070 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 15 | CIN071 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 16 | CIN151A | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 17 | CIN155B | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 18 | CIN201 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 19 | CIN203 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 20 | CIN205 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 21 | CIN221 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 22 | CIN222 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 23 | CIN224 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 24 | CIN225 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 25 | CIN234 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 26 | CIN235 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 27 | CIN236 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 28 | CIN237 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 29 | CIN238 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 30 | CIT006 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 31 | CIT023 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 32 | CIT028 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 33 | CIT030 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 34 | CIT052 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 35 | CIT061 | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 36 | LR201A | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 37 | LR201D | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 38 | LR201E | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 39 | LR201F | 是 | 否 | **立绘（CHR）差分名被解析器误判为 voice** |
| 40 | cO255 | 否 | 否 | 六源均无同名条目 → 非语音声明串（未解析，疑原作缺失的立绘引用） |

**判定结论**：40 个 ID 中 **39 个在 `ota/chr` 库中确有同名条目**（立绘差分名），
第 40 个 `cO255` 在**六源全部素材库中均无同名条目**（既非语音也非已提取立绘）——
实测其原始字节形态为声明串 `01 01 06 00 63 4F 32 35 35 00`（`24_1b.tob@5611` 等 3 处），
属**立绘类声明串**，非语音 ID。→ **真实语音缺失 = 0**。
本模块**保留源值**（`lines[].voice` 原样、`audio=[]`），**不臆断回收为 `assets`**。

### 6.3 不产出项（如实登记，不臆造）

- **SE / BGM 未产出**：`parse_after.py` 只抽取 `PIC\*.ELG` 为 `image`，未抽取 `SE\*.OGG` / BGM 引用；
  原始声明串中确有 `SE\SE809.OGG`（310 次）等引用，但**未结构化到消息级** → 本模块不产出场景级 SE/BGM（同 W6a 对 BGM 的处置口径）。
- **每行图像/音效不产出**：schema §2.1 已定稿「图像/音效只挂场景级」（TOB0 演出命令语义未逆向，总纲 §六 R1）。
- **9 个场景无任何图像引用**（如实为空 `assets: []`）。

### 6.4 W11h 复核：引用可解析 + 「voice 非空但 audio=[]」口径（**如实登记，不伪造**）

W11h 为六源统一新增了「引用可解析」校验（各源校验器 A8：`lines[].audio[]` 与
`assets[].out_relpath` 必须以 `<源代号>/` 开头且能在 `krkr素材库\` 下 `isfile`）。ota 复核结果：

| 项 | 实测 |
| --- | ---: |
| `lines[].audio[]` 引用 → 落在 `ota/` 且库内存在 | **10,320 / 10,320**（越界 0 ｜ 库内缺 0） |
| `assets[].out_relpath` 引用 → 落在 `ota/` 且库内存在 | **722 / 722**（越界 0 ｜ 库内缺 0） |
| `hit` 与库内存在性不符 | **0** |
| `assets_missing[]` 与「`hit=false` 的 ref 集合」一致 | **True** |
| **`voice` 非空但 `audio=[]`** | **87 行 / 40 个唯一 ID** |

**口径（W11h 明确定稿）**：这 **87 行 / 40 个唯一 ID**（`CIN*` / `CIT*` / `LR201*` / `cO255`）的
`voice` 值**在 `资源总账.json` 的 `ota` 源中查无对应 `orig_name`**（§6.2 已逐条核实：39 个是
`ota/chr` 立绘差分名被解析器误判为 `voice`，1 个 `cO255` 六源均无同名条目）——
**即「无对应素材」，故 `audio=[]`，属已知缺口**。处置：**保留源值、不伪造语音文件、不把 voice ID 当路径**
（`lines[].audio` 保持空数组，`lines[].voice` 原样保留以存证）。此 87 行**不计入「真实语音缺失」**
（真实语音缺失 = 0），但**计入「voice 非空但 audio=[]」的已知缺口**——两者口径不同，不可混用。

---

## 七、译名替换

### 7.1 汇总（正文 182 处 ＋ 选择支 5 处）

{"羽田君 | 羽田同学 | 羽田君": 107, "奈落 | 奈落 | 地狱": 17, "ロックバード | 洛克巴德 | ＲＯＣ－ＢＩＲＤ": 6, "ドラさん | 德拉 | 德拉先生": 26, "伽楼羅 | 伽楼罗 | 迦楼罗": 9, "風見ヶ丘 | 风见丘 | 风见之丘": 1, "プリンセス・ダヴ | 妲朴公主 | 妲朴小公主": 11, "ブルボンヌ冴子 | 布尔邦努冴子 | 布露波卢冴子": 2, "委員長 | 委员长 | 班长": 1, "アスカ姫 | 明日香公主 | 阿斯嘉公主": 1, "ペガサス | 天马 | 佩格萨斯": 1}

> `ota` 可用规则 **15 条**（`ota/body`；**`ota/name` 0 条**）；4 条 `（待裁决）` 规则（`ヨッくん`/`ハヤブサ`/`ソラ学`/`タカシ`）按表过滤不执行。

### 7.2 W6c 实测补充的排除规则（**消费侧，待主代理登记**）

沿用 W6a 的做法（构建器内加排除、逐处留痕、**不改表本体**）。本轮实测发现 **3 类共 16 处误替**，
已在构建器 `EXCL` 中补排除，**并复核未引入漏替（0 处）**：

| # | 原词 | 误替现象（实测） | 新增排除 | 修复处数 |
| --- | --- | --- | --- | ---: |
| 1 | `針生` → `针生同学` | **全名 `針生蔵人` 被替成「针生同学藏人」**；`針生長官` → 「针生同学长官」 | `针生(?!同学\|前辈\|君\|先生\|小姐\|老师\|哥\|姐\|藏人\|长官\|長官\|，\|、\|。\|！\|？\|—\|…)` | 14 |
| 2 | `渡来さん` → `渡来同学` | `私も渡来だから渡来さん` → 「我姓**渡来同学**，所以是渡来同学」（把姓氏陈述也替了） | `渡来(?!同学\|明日香\|家\|屋\|前辈\|学姐\|Ｓ香\|，\|、\|。\|！\|？\|—\|…\|是)` | 1 |
| 3 | `委員長` → `班长` | `審査委員長` → 「审查**班长**」（正当复合词被替） | `(?<!执行\|審査\|审查)委员长` | 1 |

实测样本（修复前 → 修复后）：

| 场景 | jp | 修复前 | 修复后 |
| --- | --- | --- | --- |
| `11_3d2#28` | `針生蔵人` | 针生**同学**藏人本人 | 针生藏人本人 |
| `11_4b#9` | `針生蔵人` | 针生**同学**藏人 | 针生藏人 |
| `11_3d3#71` | `針生長官` | 针生**同学**长官 | 针生长官 |
| `11_5b#76` | `私も渡来だから渡来さん` | 我姓渡来**同学**，所以是渡来同学 | 我姓渡来，所以是渡来同学 |
| `51_1#48` | `審査委員長` | 审查**班长** | 审查委员长 |

> **提请主代理裁决**：上表 3 条排除规则是否登记进 `资源组\修正\译名统一口径.md` §六（或作品层 `术语表.md` §六）。
> 未登记前，本模块的产物已按此排除生成；若主代理否决，改回 `EXCL` 常量重跑即可（影响面 16 处）。

### 7.3 未解决的译名一致性问题（**提请裁决**）

| # | 事项 | 现状 | 影响 |
| --- | --- | --- | --- |
| A | **`译名替换表.tsv` 无 `ota/name` 行** | **名字框（说话人）不经过任何替换**，保留 AS 侧写形 | 见下表 4 项与 D3 冲突 |
| B | `委員長`/`班長` 撞形 | `41_3#16` jp 同句含 `班長` 与 `委員長`，D3 规定 `委員長→班长` → 译文成「作为班长作为班长」 | 1 处；属 D3 口径的连带结果，非构建器缺陷 |
| C | `伽桜羅`（原作写形） | `24_1b` 选项 jp 为 `伽桜羅`（非 `伽楼羅`）→ JP 门控不触发 → 保持 `伽楼罗` | 1 处选择支；与同场景其他选项的 `迦楼罗` 不一致 |

**名字框（说话人）与 D3 冲突逐条**：

| 名字框日文 | 本产物中文 | 出现次数 | D3 / 本工程术语表 | 是否冲突 |
| --- | --- | ---: | --- | --- |
| 伽楼羅 | 伽楼罗 | 118 | **迦楼罗** | **冲突** |
| タカシ | 鹰志 | 112 | **待裁决**（本篇 §三之八十一） | **冲突** |
| ギルティ | 有罪 | 63 | 有罪（AS 侧标 `（待确认）`） | 待确认 |
| アスカ姫 | 明日香公主 | 1 | **阿斯嘉公主** | **冲突** |

> `伽楼羅`（118 次）与 `アスカ姫`（1 次）是本工程 D3 明文的替换项，但 `译名替换表.tsv` 只登记了 `ota/body`，
> **未登记 `ota/name`** → 名字框保留 AS 写形。`タカシ`（112 次）为 D3 **待裁决**项（本篇 §三之八十一禁止全库统一）。
> **本模块不自行补齐 name 流规则**（维护归主代理），如实登记。

---

## 八、验收自证（8 项逐条；第 8 项为 W11h 新增）

校验器：`资源组\工具\verify_scene_ota.py`（**从磁盘 `scene_ota.jsonl` 重新读取**，与只读源交叉核对，
不依赖构建器内存态）→ 结果 `子代理工作区\ISSUE-20260918-06\W6c\W6c验收.json`。

| # | 标准 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | 场景数：172 个 `.tob` 全部产出（`sr.tob` 0 消息如实标注） | **通过** | `A1_tob_count=172`，产物 172 行，集合完全一致；0 消息场景 = `['sr']`（`A1_empty_msg_scenes`） |
| 2 | 行数守恒：18,213 槽逐文件对账差异 0 | **通过** | 总行 18,213 == 语料基线 18,213（正文 18,047 ＋ 标题 166）；`A2_scene_diff = {}`；`kind` 分布 title 166 / dialogue 11,667 / narration 6,380 |
| 3 | 修正命中：`source=ota` 7 条全命中；门控排除项逐条列出 | **通过** | 范围内 7 = 命中 7 ＋ 未命中 0；`A3_landing_verified = True`（逐条落点复核）；范围外 143 条（`otp` 14 ＋ `otr` 129）**逐条列出**（§4.4） |
| 4 | 选择支：40 处是否全部抓到？与本作已知数对账 | **通过** | 记录 40 / 场景 20 / 选项 57（源槽 73 − skip 16）/ 提示 6，与源集合完全一致；**「37 种标签」无法复现**（已列证据，§5.1） |
| 5 | 素材命中率：语音 10,407 次 / 10,308 个 ID，逐条核实真实缺失 | **通过** | 语音命中 10,320/10,407；未命中 87 次 / 40 个 ID **全部为立绘类声明串**（39 个 CHR stem ＋ `cO255`）；**真实语音缺失 = `[]`**；图像 722/722（原始 1,056 次 / 363 文件） |
| 6 | schema 自洽：必填缺失 0、`scene_id` 唯一、逐行 `json.loads` 通过 | **通过** | `A6_missing_fields = []`；`A6_scene_id_unique = True`；172 行逐行 `json.loads` 成功；`seq` 连续校验通过 |
| 7 | 不臆断：`22_*`/`23_*` 归属、无确证的 `game_date` 等一律 `null` 并说明 | **通过** | `22_*`(7)/`23_*`(7) 的 `route`/`phase` **全为 `null`**（D13 待裁决）；`route=null` 共 15 个、`phase=null` 共 53 个；`game_date` 仅 6 个场景有值且**逐条复核确有显式 `○月○日`**（`A7_game_date_without_evidence = []`）；D14 例外 0；空槽 34 个逐条登记 |
| **8** | **引用命名空间可解析（W11h 新增）**：`lines[].audio[]` 与 `assets[].out_relpath` 必须以 `ota/` 开头、必须在 `krkr素材库\` 下 `isfile`、`hit` 须与库内存在性一致、`assets_missing[]` 须如实 | **通过** | audio **10,320/10,320**、assets **722/722** 全部落在 `ota/` 下且库内存在；越界 0、库内缺 0、`hit` 不符 0、`assets_missing` 一致 True；`voice` 非空但 `audio=[]` **87 行 / 40 个唯一 ID**（无对应素材，已知缺口，见 §6.4） |

**`ALL_PASS = True`**

**复现命令**：

```bash
cd "E:/ZCode Workspace/Galgame"
python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ota.py"
python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_ota.py"
python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_w6c_report.py"
```

---

## 九、未决问题与需主代理裁决点

### 9.1 需主代理裁决

| # | 事项 | 现状 | 备选 |
| --- | --- | --- | --- |
| 1 | **3 条新增译名排除规则是否登记**（§7.2） | 已在构建器 `EXCL` 内生效（修复 16 处误替，未引入漏替） | 登记进 §六（推荐）；或否决并回退（影响 16 处） |
| 2 | **`译名替换表.tsv` 缺 `ota/name` 行**（§7.3A） | 名字框保留 AS 写形：`伽楼羅→伽楼罗`(118)、`アスカ姫→明日香公主`(1) 与 D3 冲突；`タカシ→鹰志`(112) 属待裁决项 | 补登记 `ota/name` 规则后由主代理重跑；或接受名字框与正文双轨 |
| 3 | **`source_kind` 对 AS 的取值命名**（§三.3） | 全部 172 场景记 `new`（语义＝无对照源） | 维持 `new`（保持枚举封闭）；或另立源专属值（需改 schema） |
| 4 | **`phase` 三值枚举不覆盖后日谈合集**（§二/§三） | `序/个人线/结局` 只覆盖 11–14/21/24 的 119 个场景；`22/23`（D13）与 C/D/E 层（番外/劇場/おまけ）共 53 个记 `null` | **W10b（2026-09-19）已裁决：扩展 `phase` 枚举**——`schema.md` §三.5 定稿八值域并把 `null` 列为合法值（语义＝未归入任何已定义层，不臆断）；本模块 53 个 `null` **保持原值**，校验器按新值域校验（越界 0）。**不映射为实值**（映射即臆断） |
| 5 | **流程图 §4.5「37 种选择支标签」**（§5.1） | 全库 13,459 个声明串穷举，**不存在** `選択肢N`/`合流` 标签 | 更正流程图该行；或指出该数的真实出处 |
| 6 | **`24_5a` 3 条选项源值相同**（§5.3） | 源 `选择支补译.json` 记为 `ヨージ`×3 | 提请核实是否为源提取缺陷，必要时回修 AS 源工程（D9：不回修源成品 → 本工程内修正表覆盖） |
| 7 | **`cO255`（1 处）**（§6.2） | 六源素材库均无同名条目；为立绘类声明串，非语音 | 维持保留源值；或另立条目登记该缺失立绘引用 |

### 9.2 未决（仅登记，不需裁决）

- **7 个选择支提示槽的 `jp` 在语料中为空**（`11_3b0#79`、`12_3a0#191`、`13_3c0#63`、`14_6a0#32`、`14_6c0#18`、`24_1b#5`、`24_5a#4`）：
  其中 **6 个的日文可由 `选择支补译.json` 的 `prompt` 字段回收**（带字节坐标，实测解码一致），
  但 **`24_1b#5` 的日文未在任何提取产物中**（实测原文位于 `24_1b.tob` 偏移 ≈1740–1800 区的
  `　うーん……相手が小鳩となると、とりあえず適任はこの三人辺りか？　あの選択は末っ子よ、おまえに任せよう。ふたたび俺たちを導いてくれ。`）。
  **本模块不回收**（避免把「非语料来源」写入 `jp` 字段而破坏 `源值` 语义），如实登记；如主代理要求回收，可另开条目。
- **`24_5a#4` 的译文缺失**：`jp`（`どの俺が追いかけますか？`）可回收，但**语料中无对应中文**——
  `工具\apply_choices.py` 的 `PROMPT` 表只含 6 条，**漏了 `24_5a#4`**。本模块**不擅译**，如实登记为**漏译 1 处**，待主代理裁决补译。
- **34 个空槽**：全部是**选择支的选项记录**（`kind=line`、`jp`/`cn` 均空），选项串本身已写入 `choices[]`，故空槽不构成漏译。
- **6 个场景无标题**（`sc_04`/`sc_07`–`sc_10`/`sr`）：源语料确无 `kind=title` 槽 → `title_jp`/`title_cn` 为 `null`，`title_variants = []`。
- **AS 的 `jp`/`cn` 取自 `语料\译文.json`（`cn` 为完整译文，非等长截断形态）**：
  AS 收尾统计的「等长截断 805」是**旧引擎建包**时的产物，本工程迁 krkr 后无等长约束（总纲 §3.4），故直接用完整 `cn`。
- **SE/BGM 未产出**（§6.3）。

### 9.3 对后续模块的提示

- `otp`（前奏诗）模块可**直接复用**本构建器的骨架：其修正表 locator 用 `seq=`（14 条），
  且前奏诗是 SOB0 脚本，跳转标签与说话人机制需另解（不能照搬本模块的声明串扫描）。
- `otr` 的 129 条修正**不在本模块范围**，其中 `s03c` 以外的 46 条已在 W6a2 登记（见 `W6a2验收.json` 的 `A3_out_of_scope_otr_files`）；
  本次统计显示 `otr` 修正共 129 条，其余 83 条属 `s03c` 范围（已由 W6a 消费）。
- **本模块新增的 3 条排除规则（§7.2）若获登记，`ot`/`otp`/`otr`/`otv`/`np` 模块需同步采用**——
  尤其 `針生蔵人` 类全名误替与 `審査委員長` 类复合词误替，属**跨源同根风险**。

---

## 十、逐场景统计（172 场景）

| 场景 | route | phase | 标题（中） | 行数 | 语音 | 修正 | 译名 | 素材(命中/总) | 选择支 | 后继 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `11_1a` | AS 对决羽田鹰志 | 序 | 重逢～对决羽田鹰志～ | 20 | 19 | 0 | 0 | 2/2 | 0 | 11_1b |
| `11_1b` | AS 对决羽田鹰志 | 个人线 | 近况～羽田君与渡来同学～ | 272 | 170 | 0 | 4 | 8/8 | 0 | 11_2a |
| `11_2a` | AS 对决羽田鹰志 | 个人线 | 家人～鸽与鹰～ | 101 | 47 | 0 | 1 | 3/3 | 0 | 11_2b |
| `11_2b` | AS 对决羽田鹰志 | 个人线 | 最近的学院生活 | 146 | 81 | 0 | 2 | 8/8 | 0 | 11_2c |
| `11_2c` | AS 对决羽田鹰志 | 个人线 | 被冷落的公主 | 158 | 104 | 0 | 3 | 10/10 | 0 | 11_3a |
| `11_3a` | AS 对决羽田鹰志 | 个人线 | 美咲酱绽放（里篇） | 76 | 20 | 0 | 0 | 5/5 | 0 | 11_3b0 |
| `11_3b0` | AS 对决羽田鹰志 | 个人线 | 汰架示与咲夜 | 82 | 45 | 0 | 3 | 3/3 | 2 | 11_3b1/11_3b2 |
| `11_3b1` | AS 对决羽田鹰志 | 个人线 | 关于香田亚衣 | 57 | 34 | 0 | 0 | 8/8 | 0 | 11_3c |
| `11_3b2` | AS 对决羽田鹰志 | 个人线 | 关于女学生Ａ | 43 | 33 | 0 | 1 | 0/0 | 0 | 11_3c |
| `11_3c` | AS 对决羽田鹰志 | 个人线 | 还是想成为谁的助力 | 113 | 64 | 0 | 3 | 1/1 | 0 | 11_3d0 |
| `11_3d0` | AS 对决羽田鹰志 | 个人线 | 停不住的男人 | 61 | 42 | 0 | 1 | 3/3 | 4 | 11_3d1/11_3d2/11_3d3 |
| `11_3d1` | AS 对决羽田鹰志 | 个人线 | 打工ｗｉｔｈ明日香 | 101 | 62 | 0 | 0 | 2/2 | 0 | 11_4a |
| `11_3d2` | AS 对决羽田鹰志 | 个人线 | 打工ｗｉｔｈ京 | 81 | 55 | 0 | 5 | 3/3 | 0 | 11_4a |
| `11_3d3` | AS 对决羽田鹰志 | 个人线 | 打工ｗｉｔｈ藏人 | 103 | 67 | 0 | 4 | 3/3 | 0 | 11_4a |
| `11_4a` | AS 对决羽田鹰志 | 个人线 | 美咲酱起飞（里） | 67 | 25 | 0 | 0 | 3/3 | 0 | 11_4b |
| `11_4b` | AS 对决羽田鹰志 | 个人线 | 回来了，针生同学 | 93 | 76 | 0 | 7 | 6/6 | 0 | 11_5a |
| `11_5a` | AS 对决羽田鹰志 | 个人线 | 母亲渡来化女儿 | 120 | 54 | 0 | 2 | 6/6 | 0 | 11_5b |
| `11_5b` | AS 对决羽田鹰志 | 个人线 | 慰劳 | 210 | 133 | 2 | 4 | 9/9 | 0 | 11_5c |
| `11_5c` | AS 对决羽田鹰志 | 个人线 | 提升男人味 | 120 | 86 | 1 | 8 | 2/2 | 0 | 11_5d |
| `11_5d` | AS 对决羽田鹰志 | 个人线 | 和明日香同学卿卿我我 | 320 | 140 | 0 | 1 | 12/12 | 0 | 11_6a |
| `11_6a` | AS 对决羽田鹰志 | 结局 | 闭幕～对决羽田鹰志～ | 68 | 38 | 0 | 0 | 4/4 | 0 | 51_1 |
| `12_1a` | AS 对决千岁鹫介 | 序 | 重逢～对决千岁鹫介～ | 16 | 15 | 0 | 0 | 2/2 | 0 | 12_1b |
| `12_1b` | AS 对决千岁鹫介 | 个人线 | 近况～鹫介同学与日和子酱～ | 246 | 119 | 0 | 0 | 14/14 | 0 | 12_1c |
| `12_1c` | AS 对决千岁鹫介 | 个人线 | 引领的男人 | 65 | 41 | 0 | 0 | 2/2 | 0 | 12_1d |
| `12_1d` | AS 对决千岁鹫介 | 个人线 | 怀着感激之情 | 131 | 71 | 0 | 0 | 2/2 | 0 | 12_1e |
| `12_1e` | AS 对决千岁鹫介 | 个人线 | 黏黏糊糊日和子同学 | 406 | 151 | 0 | 0 | 14/14 | 0 | 12_2a |
| `12_2a` | AS 对决千岁鹫介 | 个人线 | 家人～妲朴＆伊库鲁尔～ | 80 | 44 | 0 | 1 | 4/4 | 0 | 12_2b |
| `12_2b` | AS 对决千岁鹫介 | 个人线 | 美咲酱的心碎（里） | 128 | 58 | 0 | 0 | 4/4 | 0 | 12_2c |
| `12_2c` | AS 对决千岁鹫介 | 个人线 | 学院伊库鲁尔 | 132 | 72 | 0 | 10 | 4/4 | 0 | 12_2d |
| `12_2d` | AS 对决千岁鹫介 | 个人线 | 结成！空荡荡☆透亮亮 | 96 | 59 | 0 | 3 | 2/2 | 0 | 12_2e |
| `12_2e` | AS 对决千岁鹫介 | 个人线 | 伊库鲁尔的整人（秘）报告 | 157 | 97 | 0 | 1 | 4/4 | 0 | 12_2f |
| `12_2f` | AS 对决千岁鹫介 | 个人线 | 午后的一对情侣 | 177 | 105 | 0 | 0 | 5/5 | 0 | 12_3a0 |
| `12_3a0` | AS 对决千岁鹫介 | 个人线 | 约定的放学后（Ｔａｋｅ２） | 194 | 115 | 0 | 10 | 5/5 | 2 | 12_3a1/12_3a2 |
| `12_3a1` | AS 对决千岁鹫介 | 个人线 | 和日和子同学回去 | 36 | 20 | 0 | 0 | 0/0 | 0 | 12_3b |
| `12_3a2` | AS 对决千岁鹫介 | 个人线 | 和明日香同学回去 | 39 | 23 | 0 | 1 | 0/0 | 0 | 12_3b |
| `12_3b` | AS 对决千岁鹫介 | 个人线 | 续·旗子折断的天使 | 190 | 96 | 0 | 8 | 9/9 | 0 | 12_4a |
| `12_4a` | AS 对决千岁鹫介 | 个人线 | 总是匆匆而过的亚历山大 | 143 | 89 | 0 | 0 | 3/3 | 0 | 12_4b |
| `12_4b` | AS 对决千岁鹫介 | 个人线 | 忘记时间男人 | 147 | 87 | 0 | 0 | 6/6 | 0 | 12_4c0 |
| `12_4c0` | AS 对决千岁鹫介 | 个人线 | 嫉妒骚动的始末 | 127 | 87 | 0 | 0 | 3/3 | 3 | 12_4c1/12_4c2 |
| `12_4c1` | AS 对决千岁鹫介 | 个人线 | 圣夜、与她 | 22 | 14 | 0 | 0 | 0/0 | 0 | 12_4d |
| `12_4c2` | AS 对决千岁鹫介 | 个人线 | 新年、与她 | 30 | 22 | 0 | 0 | 0/0 | 0 | 12_4d |
| `12_4d` | AS 对决千岁鹫介 | 个人线 | 迷途的王子 | 103 | 67 | 0 | 0 | 3/3 | 0 | 12_5a |
| `12_5a` | AS 对决千岁鹫介 | 结局 | 闭幕～对决千岁鹫介～ | 109 | 66 | 0 | 0 | 8/8 | 0 | 52_1 |
| `13_1a` | AS 对决成田隼人 | 序 | 重逢～对决成田隼人～ | 22 | 20 | 0 | 0 | 2/2 | 0 | 13_1b |
| `13_1b` | AS 对决成田隼人 | 个人线 | 近况～隼人先生与鸣～ | 236 | 134 | 0 | 0 | 12/12 | 0 | 13_2a |
| `13_2a` | AS 对决成田隼人 | 个人线 | 贤惠的妻子与不规矩的丈夫 | 141 | 94 | 0 | 0 | 5/5 | 0 | 13_2b |
| `13_2b` | AS 对决成田隼人 | 个人线 | 和鸣小姐卿卿我我 | 372 | 157 | 0 | 0 | 18/18 | 0 | 13_3a |
| `13_3a` | AS 对决成田隼人 | 个人线 | 艾七的委托 | 82 | 23 | 0 | 0 | 6/6 | 0 | 13_3b |
| `13_3b` | AS 对决成田隼人 | 个人线 | 小千哥哥的世界 | 175 | 114 | 0 | 0 | 3/3 | 0 | 13_3c0 |
| `13_3c0` | AS 对决成田隼人 | 个人线 | 稍微换个形象 | 66 | 12 | 0 | 0 | 10/10 | 2 | 13_3c1/13_3c2 |
| `13_3c1` | AS 对决成田隼人 | 个人线 | 平日小香田 | 14 | 4 | 0 | 0 | 1/1 | 0 | 13_3d |
| `13_3c2` | AS 对决成田隼人 | 个人线 | 休日小香田 | 30 | 11 | 0 | 0 | 1/1 | 0 | 13_3d |
| `13_3d` | AS 对决成田隼人 | 个人线 | 新一代 | 168 | 111 | 0 | 1 | 2/2 | 0 | 13_4a |
| `13_4a` | AS 对决成田隼人 | 个人线 | 家人～妲朴与法卢空～ | 48 | 24 | 0 | 0 | 3/3 | 0 | 13_4b |
| `13_4b` | AS 对决成田隼人 | 个人线 | 虽然不能大声说 | 172 | 65 | 0 | 0 | 8/8 | 0 | 13_4c |
| `13_4c` | AS 对决成田隼人 | 个人线 | 绝赞举办Ｙ１大奖赛 | 136 | 101 | 0 | 0 | 6/6 | 0 | 13_4d |
| `13_4d` | AS 对决成田隼人 | 个人线 | 皇帝与吉普赛与暗黑街之王 | 101 | 63 | 0 | 1 | 4/4 | 0 | 13_4e |
| `13_4e` | AS 对决成田隼人 | 个人线 | 压轴的画室 | 107 | 67 | 0 | 0 | 6/6 | 0 | 13_4f |
| `13_4f` | AS 对决成田隼人 | 个人线 | 急转 | 325 | 155 | 0 | 1 | 7/7 | 0 | 13_4g |
| `13_4g` | AS 对决成田隼人 | 个人线 | 收束 | 167 | 76 | 0 | 0 | 4/4 | 0 | 13_5a |
| `13_5a` | AS 对决成田隼人 | 个人线 | 而今天他们也 | 101 | 51 | 0 | 0 | 3/3 | 0 | 13_5b |
| `13_5b` | AS 对决成田隼人 | 结局 | 闭幕～对决成田隼人～ | 123 | 79 | 0 | 0 | 3/3 | 0 | 53_1 |
| `14_1a` | AS 对决羽田小鹰志 | 序 | 重逢～对决羽田小鹰志～ | 29 | 28 | 0 | 2 | 4/4 | 0 | 14_1b |
| `14_1b` | AS 对决羽田小鹰志 | 个人线 | 近况～哥哥与小鸠～ | 313 | 121 | 0 | 0 | 18/18 | 0 | 14_2a |
| `14_2a` | AS 对决羽田小鹰志 | 个人线 | 节日的创作活动 | 195 | 103 | 0 | 0 | 13/13 | 0 | 14_3a |
| `14_3a` | AS 对决羽田小鹰志 | 个人线 | 决心、我们来谈恋爱吧 | 118 | 63 | 0 | 0 | 6/6 | 0 | 14_3b |
| `14_3b` | AS 对决羽田小鹰志 | 个人线 | 同班同学这个选项 | 185 | 109 | 0 | 2 | 6/6 | 0 | 14_3c |
| `14_3c` | AS 对决羽田小鹰志 | 个人线 | 打工伙伴这个选项 | 195 | 138 | 0 | 0 | 5/5 | 0 | 14_3d |
| `14_3d` | AS 对决羽田小鹰志 | 个人线 | 美女与野兽们（１） | 56 | 36 | 0 | 0 | 2/2 | 0 | 14_4a |
| `14_4a` | AS 对决羽田小鹰志 | 个人线 | 归来的神秘销售女 | 34 | 29 | 0 | 0 | 1/1 | 0 | 14_4b |
| `14_4b` | AS 对决羽田小鹰志 | 个人线 | 玫瑰色的便当时光 | 139 | 97 | 0 | 1 | 2/2 | 0 | 14_4c |
| `14_4c` | AS 对决羽田小鹰志 | 个人线 | 朋友的妹妹这个选项 | 104 | 71 | 0 | 9 | 2/2 | 0 | 14_4d |
| `14_4d` | AS 对决羽田小鹰志 | 个人线 | 兄妹吵架连布蒙加都不吃 | 128 | 77 | 0 | 0 | 2/2 | 0 | 14_4e |
| `14_4e` | AS 对决羽田小鹰志 | 个人线 | 美女与野兽们（２） | 30 | 14 | 0 | 0 | 2/2 | 0 | 14_5a |
| `14_5a` | AS 对决羽田小鹰志 | 个人线 | 神秘销售女再度登场 | 54 | 34 | 0 | 0 | 1/1 | 0 | 14_5b |
| `14_5b` | AS 对决羽田小鹰志 | 个人线 | 玉泉日和子疑似弗利法疑惑 | 115 | 98 | 0 | 1 | 3/3 | 0 | 14_5c |
| `14_5c` | AS 对决羽田小鹰志 | 个人线 | 少女这个选项 | 73 | 35 | 0 | 0 | 2/2 | 0 | 14_5d |
| `14_5d` | AS 对决羽田小鹰志 | 个人线 | 美女与野兽们（３） | 82 | 55 | 0 | 0 | 2/2 | 0 | 14_6a0 |
| `14_6a0` | AS 对决羽田小鹰志 | 个人线 | 土特产·摇滚 | 35 | 26 | 0 | 0 | 1/1 | 3 | 14_6a1/14_6a2/14_6a3 |
| `14_6a1` | AS 对决羽田小鹰志 | 个人线 | 色狼（笑） | 4 | 3 | 0 | 0 | 0/0 | 0 | 14_6b |
| `14_6a2` | AS 对决羽田小鹰志 | 个人线 | 灯笼裤（笑） | 4 | 3 | 0 | 0 | 0/0 | 0 | 14_6b |
| `14_6a3` | AS 对决羽田小鹰志 | 个人线 | 野合（笑） | 5 | 4 | 0 | 0 | 0/0 | 0 | 14_6b |
| `14_6b` | AS 对决羽田小鹰志 | 个人线 | 羽田班就是这种感觉 | 83 | 67 | 0 | 0 | 1/1 | 0 | 14_6c0 |
| `14_6c0` | AS 对决羽田小鹰志 | 个人线 | 高内昌子出现了！ | 21 | 11 | 0 | 0 | 1/1 | 2 | 14_6c1/14_6c2 |
| `14_6c1` | AS 对决羽田小鹰志 | 个人线 | 没想到是昌子 | 136 | 90 | 0 | 0 | 3/3 | 0 | 14_6d |
| `14_6c2` | AS 对决羽田小鹰志 | 个人线 | 传感器无反应 | 117 | 85 | 0 | 0 | 2/2 | 0 | 14_6d |
| `14_6d` | AS 对决羽田小鹰志 | 个人线 | 黄昏时分的天使们 | 130 | 66 | 0 | 1 | 9/9 | 0 | 14_6e |
| `14_6e` | AS 对决羽田小鹰志 | 个人线 | 决战前夜 | 59 | 33 | 0 | 0 | 4/4 | 0 | 14_7a |
| `14_7a` | AS 对决羽田小鹰志 | 个人线 | 小丑的基因 | 231 | 104 | 0 | 0 | 10/10 | 0 | 14_8a |
| `14_8a` | AS 对决羽田小鹰志 | 结局 | 闭幕～对决羽田小鹰志～ | 91 | 38 | 0 | 0 | 5/5 | 0 | — |
| `21_1a` | AS 美咲线 | 个人线 | 美咲酱继续 | 240 | 156 | 0 | 0 | 7/7 | 0 | 21_2a |
| `21_2a` | AS 美咲线 | 个人线 | 美咲酱绽放 | 97 | 26 | 0 | 0 | 4/4 | 0 | 21_2b |
| `21_2b` | AS 美咲线 | 个人线 | 美咲酱上下颠倒 | 64 | 24 | 0 | 0 | 3/3 | 0 | 21_2c |
| `21_2c` | AS 美咲线 | 个人线 | 美咲酱校园日常 | 119 | 94 | 2 | 0 | 1/1 | 0 | 21_2d |
| `21_2d` | AS 美咲线 | 个人线 | 美咲酱危机 | 61 | 28 | 0 | 0 | 6/6 | 0 | 21_2e |
| `21_2e` | AS 美咲线 | 个人线 | 美咲酱相思病 | 59 | 35 | 0 | 0 | 1/1 | 0 | 21_2f |
| `21_2f` | AS 美咲线 | 个人线 | 美咲酱轰动 | 90 | 58 | 0 | 0 | 3/3 | 0 | 21_3a |
| `21_3a` | AS 美咲线 | 个人线 | 美咲酱起飞 | 143 | 64 | 0 | 0 | 8/8 | 0 | 21_3b |
| `21_3b` | AS 美咲线 | 个人线 | 美咲酱永恒 | 53 | 35 | 0 | 0 | 4/4 | 0 | — |
| `22_1a` | **(null)** | **(null)** | 如今我们的胸部再度开始 | 72 | 70 | 0 | 0 | 2/2 | 0 | 22_2a |
| `22_2a` | **(null)** | **(null)** | 回归招牌女孩 | 138 | 137 | 0 | 0 | 5/5 | 0 | 22_2b |
| `22_2b` | **(null)** | **(null)** | 超级·上等·帮手 | 60 | 59 | 0 | 0 | 3/3 | 0 | 22_2c |
| `22_2c` | **(null)** | **(null)** | 忙碌女编辑的烦恼 | 83 | 82 | 0 | 0 | 3/3 | 0 | 22_2d |
| `22_2d` | **(null)** | **(null)** | 恐怖！怪人黑内裤大猩猩的逆袭 | 122 | 99 | 1 | 0 | 3/3 | 0 | 22_2e |
| `22_2e` | **(null)** | **(null)** | 不平安的平安夜 | 151 | 150 | 0 | 0 | 2/2 | 0 | 22_2f |
| `22_2f` | **(null)** | **(null)** | 我们的奶子啊直到永远 | 74 | 68 | 0 | 0 | 8/8 | 0 | — |
| `23_1a` | **(null)** | **(null)** | ４天前：今日的苍女 | 179 | 82 | 0 | 0 | 4/4 | 0 | 23_1b |
| `23_1b` | **(null)** | **(null)** | ３天前：放学后萨满 | 164 | 76 | 0 | 0 | 5/5 | 0 | 23_1c |
| `23_1c` | **(null)** | **(null)** | ２天前：没有回报的努力 | 106 | 52 | 0 | 0 | 4/4 | 0 | 23_1d |
| `23_1d` | **(null)** | **(null)** | ２天前：黄昏忧郁 | 98 | 50 | 0 | 0 | 3/3 | 0 | 23_1e |
| `23_1e` | **(null)** | **(null)** | １天前：彷徨的低年级生 | 122 | 85 | 0 | 0 | 3/3 | 0 | 23_1f |
| `23_1f` | **(null)** | **(null)** | １天前：去问问阿基米德 | 150 | 107 | 0 | 0 | 2/2 | 0 | 23_2a |
| `23_2a` | **(null)** | **(null)** | Ｘ日：蹦跳的小姑娘们 | 72 | 48 | 0 | 0 | 4/4 | 0 | — |
| `24_1a` | AS 最终统合线 | 个人线 | 引言：假统合的崩溃 | 118 | 50 | 0 | 3 | 9/9 | 0 | 24_1b |
| `24_1b` | AS 最终统合线 | 个人线 | 晨间遭遇：小鸠 | 113 | 82 | 0 | 2 | 2/2 | 3 | 24_2a |
| `24_2a` | AS 最终统合线 | 个人线 | 间奏：从自宅到学校 | 18 | 0 | 0 | 1 | 3/3 | 0 | 24_2b |
| `24_2b` | AS 最终统合线 | 个人线 | 午间遭遇：明日香 | 120 | 81 | 0 | 11 | 2/2 | 3 | 24_2c |
| `24_2c` | AS 最终统合线 | 个人线 | 午间遭遇：京 | 113 | 67 | 1 | 8 | 6/6 | 3 | 24_2d |
| `24_2d` | AS 最终统合线 | 个人线 | 午间遭遇：高内 | 78 | 50 | 0 | 0 | 2/2 | 3 | 24_2e |
| `24_2e` | AS 最终统合线 | 个人线 | 午间遭遇：美咲 | 7 | 5 | 0 | 0 | 1/1 | 0 | 24_3a |
| `24_3a` | AS 最终统合线 | 个人线 | 间奏：从学校到打工 | 4 | 0 | 0 | 1 | 1/1 | 0 | 24_3b |
| `24_3b` | AS 最终统合线 | 个人线 | 傍晚遭遇：日和子 | 144 | 102 | 0 | 0 | 5/5 | 3 | 24_3c |
| `24_3c` | AS 最终统合线 | 个人线 | 傍晚遭遇：纪奈子 | 101 | 75 | 0 | 0 | 2/2 | 3 | 24_3d |
| `24_3d` | AS 最终统合线 | 个人线 | 傍晚遭遇：英里子 | 100 | 80 | 0 | 0 | 2/2 | 3 | 24_3e |
| `24_3e` | AS 最终统合线 | 个人线 | 傍晚遭遇：吉川 | 155 | 93 | 0 | 1 | 7/7 | 3 | 24_4a |
| `24_4a` | AS 最终统合线 | 个人线 | 间奏：从打工到夜晚的街道 | 5 | 0 | 0 | 0 | 1/1 | 0 | 24_4b |
| `24_4b` | AS 最终统合线 | 个人线 | 夜晚遭遇：鸣 | 115 | 89 | 0 | 15 | 2/2 | 3 | 24_4c |
| `24_4c` | AS 最终统合线 | 个人线 | 夜晚遭遇：亚衣 | 96 | 37 | 0 | 0 | 4/4 | 3 | 24_4d |
| `24_4d` | AS 最终统合线 | 个人线 | 夜晚遭遇：春惠 | 81 | 57 | 0 | 0 | 2/2 | 3 | 24_4e |
| `24_4e` | AS 最终统合线 | 个人线 | 夜间遭遇：爱丽丝 | 131 | 76 | 0 | 2 | 3/3 | 3 | 24_5a/24_5c |
| `24_5a` | AS 最终统合线 | 个人线 | 最终遭遇：和马 | 47 | 35 | 0 | 0 | 2/2 | 3 | 24_5b |
| `24_5b` | AS 最终统合线 | 结局 | Ｇ－ＥＮＤ：太好了哥哥 | 65 | 33 | 0 | 1 | 4/4 | 0 | — |
| `24_5c` | AS 最终统合线 | 结局 | Ｂ－ＥＮＤ：我的泪啊，传达给谁 | 64 | 33 | 0 | 4 | 5/5 | 0 | — |
| `31_1` | AS 各线 after | **(null)** | 那天的思念禁止覆盖 | 143 | 90 | 0 | 3 | 4/4 | 0 | — |
| `32_1` | AS 各线 after | **(null)** | 每天都是浪漫书店篇 | 123 | 61 | 0 | 1 | 7/7 | 0 | — |
| `33_1` | AS 各线 after | **(null)** | 归来的成田工务店 | 122 | 53 | 0 | 0 | 5/5 | 0 | — |
| `34_1` | AS 各线 after | **(null)** | 公主·滚动雷霆 | 131 | 70 | 0 | 5 | 6/6 | 0 | — |
| `41_1` | AS 番外群像 | **(null)** | 羽田部队１２３１新年行军 | 26 | 14 | 0 | 2 | 2/2 | 0 | 41_2 |
| `41_2` | AS 番外群像 | **(null)** | 身高１４０厘米的世界 | 80 | 44 | 0 | 1 | 5/5 | 0 | 41_3 |
| `41_3` | AS 番外群像 | **(null)** | 山科队员的脱离 | 72 | 36 | 0 | 4 | 5/5 | 0 | 41_4 |
| `41_4` | AS 番外群像 | **(null)** | 狮子心王即将出阵 | 156 | 86 | 0 | 1 | 5/5 | 0 | 41_5 |
| `41_5` | AS 番外群像 | **(null)** | ＶＳ生剥鬼世纪对决特别篇 | 93 | 50 | 0 | 0 | 4/4 | 0 | — |
| `42_1` | AS 番外群像 | **(null)** | 没有面对的报应 | 108 | 52 | 0 | 3 | 7/7 | 0 | 42_2 |
| `42_2` | AS 番外群像 | **(null)** | 格兰·玛尼耶（ＨＡＷＫ） | 84 | 43 | 0 | 0 | 2/2 | 0 | 42_3 |
| `42_3` | AS 番外群像 | **(null)** | 格兰·玛尼耶（ＥＡＧＬＥ） | 50 | 33 | 0 | 1 | 3/3 | 0 | 42_4 |
| `42_4` | AS 番外群像 | **(null)** | 格兰玛·露尼耶（ＦＡＬＣＯＮ） | 109 | 60 | 0 | 0 | 4/4 | 0 | 42_5 |
| `42_5` | AS 番外群像 | **(null)** | 大家和和气气八等分 | 58 | 27 | 0 | 0 | 9/9 | 0 | — |
| `50_1` | AS おれつば剧场 | **(null)** | 没翅剧场～开幕篇～ | 112 | 100 | 0 | 0 | 13/13 | 0 | — |
| `51_1` | AS おれつば剧场 | **(null)** | 没翅剧场～女人们的决战～ | 78 | 75 | 0 | 0 | 1/1 | 0 | — |
| `52_1` | AS おれつば剧场 | **(null)** | 没翅剧场～小丑们的喜剧～ | 75 | 73 | 0 | 0 | 3/3 | 0 | — |
| `53_1` | AS おれつば剧场 | **(null)** | 没翅剧场～笨蛋们的友情～ | 54 | 49 | 0 | 1 | 1/1 | 0 | — |
| `54_1` | AS おれつば剧场 | **(null)** | 没翅剧场～终幕篇～ | 20 | 19 | 0 | 2 | 3/3 | 0 | — |
| `61_1a` | AS おまけ | **(null)** | 在宾馆街的一角 | 85 | 26 | 0 | 1 | 1/1 | 0 | 61_1b |
| `61_1b` | AS おまけ | **(null)** | 第一次的休息 | 112 | 51 | 0 | 3 | 4/4 | 0 | 61_1c |
| `61_1c` | AS おまけ | **(null)** | 不是澡堂却摆出战斗架势 | 123 | 31 | 0 | 3 | 3/3 | 0 | — |
| `61_2a` | AS おまけ | **(null)** | 近况～鹰志君与小京～ | 95 | 51 | 0 | 0 | 5/5 | 0 | 61_2b |
| `61_2b` | AS おまけ | **(null)** | 和京同学卿卿我我 | 22 | 12 | 0 | 0 | 1/1 | 0 | — |
| `62_1a` | AS おまけ | **(null)** | 情书·来自小日和 | 125 | 44 | 0 | 0 | 3/3 | 0 | 62_1b |
| `62_1b` | AS おまけ | **(null)** | 无论何时·棱镜（性的意义上） | 16 | 6 | 0 | 0 | 1/1 | 0 | — |
| `63_1a` | AS おまけ | **(null)** | 去泡温泉吧！ | 44 | 26 | 0 | 0 | 3/3 | 0 | 63_1b |
| `63_1b` | AS おまけ | **(null)** | 在那之前先去了吧！ | 72 | 20 | 0 | 0 | 3/3 | 0 | — |
| `64_1a` | AS おまけ | **(null)** | 梦ＡＶ·桃色乘车高峰 | 35 | 6 | 0 | 0 | 1/1 | 0 | — |
| `64_2a` | AS おまけ | **(null)** | 梦ＡＶ·桃色运动服 | 102 | 30 | 0 | 0 | 4/4 | 0 | — |
| `64_3a` | AS おまけ | **(null)** | 梦ＡＶ·桃色圣夜 | 75 | 27 | 0 | 0 | 4/4 | 0 | — |
| `sc_04` | AS おまけ | **(null)** | — | 112 | 49 | 0 | 0 | 5/5 | 0 | — |
| `sc_05` | AS おまけ | **(null)** | 日和子附加Ｈ（后） | 176 | 66 | 0 | 0 | 9/9 | 0 | — |
| `sc_06` | AS おまけ | **(null)** | 在那之前先去了吧！ | 181 | 84 | 0 | 0 | 8/8 | 0 | — |
| `sc_07` | AS おまけ | **(null)** | — | 87 | 34 | 0 | 0 | 4/4 | 0 | — |
| `sc_08` | AS おまけ | **(null)** | — | 71 | 35 | 0 | 0 | 3/3 | 0 | — |
| `sc_09` | AS おまけ | **(null)** | — | 113 | 47 | 0 | 0 | 4/4 | 0 | — |
| `sc_10` | AS おまけ | **(null)** | — | 143 | 66 | 0 | 0 | 8/8 | 0 | — |
| `sr` | **(null)** | **(null)** | — | 0 | 0 | 0 | 0 | 0/0 | 0 | — |

---

## 十一、抽样 10 行（取文来源实例）

| # | 场景 | seq | kind | speaker | 层（`cn_origin` / `layers`） | jp | cn |
| ---: | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `11_1a` | 2 | narration | — | `ota` / `ota` | 　自分が普通だってことに気付いたのは、最近の話だ。 | 意识到自己不过是个普通人、是最近的事了。 |
| 2 | `11_5b` | 19 | dialogue | 明日香 | `fix_table` / `ota→fix_table→name_replace` | 「羽田君、友達？」 | “羽田君、朋友？” |
| 3 | `11_2a` | 80 | narration | — | `ota` / `ota→name_replace` | 　……僕は半分嘘をついた。いまは千歳さんや成田さんとひとつになっているけれど、小鷹志はまだ奈落の底で膝を抱えているはずだ。 | 我说了一半的谎。即使如今千岁同学和成田同学已经和我合为一体、小鹰志应该还在地狱的底层抱着膝盖。 |
| 4 | `12_2c` | 75 | narration | — | `ota` / `ota→name_replace` | 　もっとも蔵人君はすでに成田隼人や伊丹伽楼羅とも面識がありましたし…… | 不过藏人君本来就与成田隼人、伊丹迦楼罗打过照面…… |
| 5 | `14_6d` | 2 | narration | — | `ota` / `ota→name_replace` | 　とまあ色々あったものの、アレキサンダーを出てからはまっすぐ風見ヶ丘まで帰ってきた。 | 总之虽然发生了各种事、出了亚历山大之后我就直接回到了风见之丘。 |
| 6 | `21_2c` | 55 | dialogue | 日和子 | `fix_table` / `ota→fix_table` | 「佐久間君？」 | “佐久间同学？” |
| 7 | `24_5b` | 17 | narration | — | `ota` / `ota→name_replace` | 　ハッ！　これはまさか、俺を奈落へと誘う魔性の罠か！？ | 哈！难道这是、引诱我堕入地狱的魔性陷阱吗！？ |
| 8 | `24_5a` | 4 | narration | — | `empty` / `（空槽）` | （源语料为空；日文可回收：`どの俺が追いかけますか？`） | **（译文缺失，待裁决）** |
| 9 | `41_3` | 62 | narration | — | `ota` / `ota→name_replace` | 　冷眼の殺戮者は、意外や逆らわなかった。アスカ姫の前に立ちはだかる黒衣の影が、陽炎のように揺らめいた。 | 冷眼的杀戮者、竟然没有反抗。挡在阿斯嘉公主面前的黑衣之影、像阳炎一样摇晃着。 |
| 10 | `11_2c` | 109 | dialogue | — | `ota` / `ota→name_replace`（`context_flag=true`） | 「あ〜、ドラさん彼女連れてきたんだ、熱い熱い、ひゅーひゅー」 | “啊～、德拉先生你带女朋友来啦——、好火热好火热，咻——咻——” |


---

## 附：ISSUE-20260919-06 修正（2026-09-19，editor）

### 改动

| 项 | 内容 | 槽数 |
| --- | --- | ---: |
| `译名替换表.tsv` 新增 scope 行 | `伽楼羅`→`迦楼罗`（**scope `ota/name`**，After Story 名字框此前缺行） | 118 |
| `译名替换表.tsv` 新增 scope 行 | `アスカ姫`→`阿斯嘉公主`（scope `ota/name`） | 1 |
| `译名替换表.tsv` 新增写法变体行 | `Ｒ－ＷＩＮＧ`（jp 原样写形）→`Ｒ翼`（scope `ota/body`） | 1 |
| `译名替换表.tsv` 新增写法变体行 | `伽桜羅`→`迦楼罗`（scope `ota/body`，`楼`→`桜` 写法变体） | 1 |

### 验证（实测）

| 项 | 改前 | 改后 |
| --- | ---: | ---: |
| 名字框 `speaker='伽楼罗'` | 118 | **0** |
| `明日香公主` 名字框残留 | 1 | **0** |
| `Ｒ－ＷＩＮＧ` 残留 | 1 | **0** |
| `伽楼罗` 正文残留 | 1 | **0** |
| 行数守恒 | 18,213 | 18,213（正文 18,047 + 标题 166） |
| 场景数 | 172 | 172 |

**校验器**：`verify_scene_ota.py` **ALL_PASS = True**。

### 未决

- `ダヴ姫`（ot 2 / ota 3，旧写形 `妲朴公主`）、`プリンセス明日香さま`（ota 1）、`春日春江`（ota 1）：
  写法变体，D3 证据不足或内部不一致 → 待裁决，详见 `待入表术语_补充.md` §B。
- 合法跳过（**未改**）：`審査委員長`→`审查委员长`（ota `51_1#48`，`委員長` 规则的既有排除项）。
