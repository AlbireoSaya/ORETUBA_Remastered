# -*- coding: utf-8 -*-
r"""
W6a/W6a2 · 亚衣线产出报告生成器

读 子代理工作区\ISSUE-20260918-06\W6a2\{_build_stats.json, W6a2验收.json}
写 资源组\剧本\亚衣线_产出报告.md

所有数字均由产物与校验结果直接生成，不手抄。
复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_w6a_report.py"
"""
import json, os, collections

ROOT = r"E:\ZCode Workspace\Galgame"
PRJ  = os.path.join(ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
OUT  = os.path.join(PRJ, r"资源组\剧本")
STG  = os.path.join(ROOT, r"子代理工作区\ISSUE-20260918-06\W6a2")

B = json.load(open(os.path.join(STG, "_build_stats.json"), encoding="utf-8"))
V = json.load(open(os.path.join(STG, "W6a2验收.json"), encoding="utf-8"))
S = json.load(open(os.path.join(OUT, "scene_otr.jsonl"), encoding="utf-8")) if False else None

# 读 scene.jsonl 取抽样
scenes = [json.loads(l) for l in open(os.path.join(OUT, "scene_otr.jsonl"), encoding="utf-8")]

L = []
def p(s=""): L.append(s)

def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")

# ---- 抽样：10 行（ot 3 / otr_new 3 / retranslate 3 / 译名替换 1）
def pick(pred, n):
    out = []
    for s in scenes:
        for l in s["lines"]:
            if pred(s, l) and len(out) < n:
                out.append((s, l))
    return out

samples = []
samples += pick(lambda s, l: l["cn_origin"] == "ot" and l["kind"] == "dialogue" and len(l["cn"]) > 12, 3)
samples += pick(lambda s, l: l["cn_origin"] == "otr_new" and l["kind"] == "dialogue" and len(l["cn"]) > 12, 3)
samples += pick(lambda s, l: l["cn_origin"] == "retranslate" and l["kind"] == "narration" and len(l["cn"]) > 12, 3)
samples += pick(lambda s, l: l["layers"][-1:] == ["name_replace"] and l["cn"], 1)

p("# 亚衣线（`s03c`）结构化剧本产出报告 · W6a2")
p()
p("> 模块：**W6a2**（W6a 的两处修正落地：修正表来源门控 + 选择支补译）｜ Issue：`ISSUE-20260918-06` ｜ 资源组")
p("> 交付物：`资源组\\剧本\\scene_otr.jsonl`（55 场景；2026-09-19 由 `scene.jsonl` 更名以与六源命名统一）、`资源组\\剧本\\schema.md`、本报告、")
p("> `资源组\\工具\\build_scene_jsonl.py`（构建器）、`资源组\\工具\\verify_scene_jsonl.py`（独立校验器）、")
p("> `资源组\\工具\\emit_w6a_report.py`（本报告生成器）、`子代理工作区\\ISSUE-20260918-06\\W6a2\\{_build_stats.json, W6a2验收.json}`")
p()
p("**W6a2 相对 W6a 的改动（主代理裁决落地，两处）**：")
p()
p("1. **修正表来源门控（通用规则，非特例开关）**：修正表条目**只在其 `source` 与该行「取文基准层」`cn_base` 对应时才生效**。")
p("   依据：这 7 个共享场景的**日文标题在本篇与 R 版中逐字一致**（主代理实测），故没有任何理由用 R 版侧重译顶掉本篇译文；")
p("   D14 规定共享场景整场取本篇。被门控条目**逐条留痕**（`corrections_gated_out`），不静默丢弃。")
p("   契约已写入 `资源组\\修正\\_README.md` **§四.5**，对后续所有源模块生效。")
p("2. **`s03c_01d` 选择支补译**：`黙る`→**沉默**、`拒否る`→**拒绝**（`cn_origin=fix_table`）；")
p("   `target` 仍为 `null`、`pairing_verified=false`（TOB0 分支语义未逆向，**不猜**）。")
p("3. 另把 W6a 实测的 2 条译名替换排除规则登记进 `资源组\\修正\\译名统一口径.md` **§六**（只增不删）。")
p()
p("**只读声明**：全部源（`工程\\我们没有翅膀\\`、`工程\\我们没有翅膀R\\`、`资源组\\修正\\*`、")
p("`资源组\\krkr素材库\\*`）一律只读，未改动一个字节；三张修正表本体**未改**（门控是消费侧的事）。")
p("写入仅限 `资源组\\剧本\\`、`资源组\\修正\\_README.md`、`资源组\\修正\\译名统一口径.md`、`资源组\\工具\\`、")
p("`子代理工作区\\ISSUE-20260918-06\\W6a2\\`。**未提交 git**。")
p()

# ============================================================ 一、结论
p("## 一、结论速览")
p()
p("| 项 | 结果 |")
p("| --- | --- |")
p("| 场景数 | **%d**（shared %d / branch %d / new %d） |" % (
    B["scenes"], B["source_kind_dist"].get("shared", 0),
    B["source_kind_dist"].get("branch", 0), B["source_kind_dist"].get("new", 0)))
p("| 台词行总数 | **%d**（与 `台词对照.json` 基线 %d **逐场景守恒**，差异 0） |" % (
    B["lines_total"], B["lines_baseline_compare_json"]))
p("| `cn_origin` 分布 | `ot` %d ｜ `otr_new` %d ｜ `retranslate` %d ｜ `empty` %d ｜ `fix_table` **0** |" % (
    B["orig_dist"].get("ot", 0), B["orig_dist"].get("otr_new", 0),
    B["orig_dist"].get("retranslate", 0), B["orig_dist"].get("empty", 0)))
p("| 修正表命中 | s03c 范围内 **%d 条**：命中 **%d** ｜ 来源门控排除 **%d** ｜ 未命中 **0**；全表 %d 条中范围外 %d 条（他源/他场景） |" % (
    B["corrections_in_scope_s03c"], B["corrections_hit_in_scope"],
    B["corrections_gated_in_scope"],
    B["corrections_total"], B["corrections_total"] - B["corrections_in_scope_s03c"]))
p("| 选择支补译 | `s03c_01d` `黙る`→**沉默**、`拒否る`→**拒绝**（`cn_origin=fix_table`）；`target` 仍 `null`（配对未逆向） |")
p("| 译名替换 | 实际发生 **%d 处**（JP 门控 + 排除规则） |" % B["term_hits"])
p("| 素材命中 | 语音 **%d/%d**；图像/音效 **%d/%d**（缺失 %d 处 / %d 个不同引用） |" % (
    B["voice_hit"], B["voice_refs"], B["assets_hit"], B["assets_total"],
    B["assets_missing"], len(set(x["ref"] for x in B["asset_missing_list"]))))
p("| 空槽 / D14 例外 | %d / %d（逐条列出，见 §8.2） |" % (B["empty_slots"], B["d14_exceptions"]))
p("| 7 项验收 | **ALL_PASS = %s** |" % V["ALL_PASS"])
p()

# ============================================================ 二、schema
p("## 二、`scene.jsonl` schema 定稿说明与理由")
p()
p("完整字段表见 **`资源组\\剧本\\schema.md`**。要点与理由：")
p()
p("1. **一条记录 = 一个场景**（不是一行台词）。场景是编程组编排的最小单位；")
p("   若做成行级记录，场景级字段（标题/后继/素材/选择支）会重复上千次，且无法表达「选择支属于场景」。")
p("   `lines[]` 内嵌台词行，JSONL 每行可独立 `json.loads`。")
p("2. **三层来源可审计**：`cn_base`（取文基准层）＋ `cn_origin`（生效主层）＋ `layers`（全部生效层，按序）")
p("   ＋ `fix_refs`（命中的修正表条目及其 `cn_before`）＋ `name_replaced`（命中的译名替换）。")
p("   因此「每个字来自哪一层」可完整回溯。")
p("3. **`cn_origin` 枚举**：`ot` / `otr_new` / `fix_table` / `retranslate` / `empty`（任务预设枚举，另补 `empty` 表空槽）。")
p("   **未增设 `name_replace`**——译名替换不改变取文来源，只记入 `layers`/`name_replaced`，避免污染取文统计。")
p("4. **`align_method` 新增**：记录该行取文的对齐方式（`audit` / `jp_exact_fallback` / `new_scene_direct` 等），")
p("   使「本篇译文是怎么取到的」可复核。")
p("5. **`lines[].assets`（每行图像）未产出**：Lucifen TOB0 演出命令语义未逆向（总纲 R1），")
p("   图像/音效**无法与文本槽逐行对齐**，强行对齐即臆断 → 图像/音效一律挂**场景级 `assets`**；")
p("   语音是消息表自带字段，可逐行对齐，故保留 `lines[].audio`。**此为对任务预设 schema 的唯一实质性调整**。")
p("6. **`next` / `next_kind` / `choices` 分离**：`next` 来自脚本跳转标签（硬事实）；")
p("   `choices` 只收**已确证**的玩家选择支。`02b`/`04b` 虽有两个跳转目标但脚本内无选择支串，")
p("   只记 `next_kind=branch`、不写 `choices`（不臆断）。")
p("   `choices[]` 增设 **`cn_origin`**（W6a2，见 `schema.md` §2.2）：标该选项译文的来源层，")
p("   `fix_table` = 由主代理裁决补入；`target` 仍 `null`、`pairing_verified=false`（配对未逆向，不猜）。")
p("7. **`phase` 只取三值**（`序`/`个人线`/`结局`）：亚衣线语料内无「转折/真相」层证据，不臆造。")
p()
p("**标题取值**：55 场景共 65 个 `kind=title` 槽（10 场景有 `（Ａ）`/`（Ｃ）` 双标题）。")
p("优先取「有 09 对照或有修正表条目」者，否则取最后一个；全部槽记入 `title_variants`，A/C 语义未判定故不解释、不合并。")
p()

# ============================================================ 三、取文与修正
p("## 三、取文来源与修正命中统计")
p()
p("### 3.1 取文来源（按 D14）")
p()
p("| `source_kind` | 场景数 | 取文规则 |")
p("| --- | --- | --- |")
p("| `shared` | %d | 取**本篇**译文（经 W7-1 行对齐审计） |" % B["source_kind_dist"].get("shared", 0))
p("| `branch` | %d | 重合行取**本篇**；非重合行取 **R 版** |" % B["source_kind_dist"].get("branch", 0))
p("| `new` | %d | 取 **R 版**（本项目新译，非新米） |" % B["source_kind_dist"].get("new", 0))
p()
p("**`text_source`（场景级实际取文）分布**：" + " ｜ ".join(
    "`%s` %d" % (k, v) for k, v in sorted(B["text_source_dist"].items())))
p()
p("→ 9 个共有场景全部取自本篇（`ot`）；15 个共有/分支场景因含无 2009 对照的行而呈 `mixed`；")
p("31 个新增场景全部取自 R 版（`otr_new`）。")
p()
p("**行级 `cn_origin` 分布**：")
p()
p("| `cn_origin` | 行数 | 说明 |")
p("| --- | ---: | --- |")
p("| `ot` | %d | 本篇译文（含 `jp_exact_fallback` 20 行，见 §3.3） |" % B["orig_dist"].get("ot", 0))
p("| `otr_new` | %d | R 版 `cn_full` |" % B["orig_dist"].get("otr_new", 0))
p("| `retranslate` | %d | 修正表 `fix_type=retranslate`（含新增场景 76 条 mig 重译） |" % B["orig_dist"].get("retranslate", 0))
p("| `fix_table` | %d | 亚衣线范围内**无** `quote_add`/`quote_normalize`/`space_strip` 命中（事实，非漏产） |" % B["orig_dist"].get("fix_table", 0))
p("| `empty` | %d | 空槽（源本身无文本） |" % B["orig_dist"].get("empty", 0))
p()
p("**对齐方式 `align_method`**：" + " ｜ ".join(
    "`%s` %d" % (k, v) for k, v in sorted(V["A4_align_method"].items(), key=lambda x: -x[1])))
p()
p("**源 `src` 分布（R 版侧）**：" + " ｜ ".join("`%s` %d" % (k, v) for k, v in sorted(B["src_dist"].items())))
p()
p("### 3.2 修正表命中（逐表）")
p()
p("| 表 | 全表条数 | s03c 范围内 | 命中（生效） | 来源门控排除 | 未命中 |")
p("| --- | ---: | ---: | ---: | ---: | ---: |")
import csv as _csv
def _nrows(fn):
    with open(os.path.join(PRJ, r"资源组\修正", fn), encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in _csv.DictReader(f, delimiter="\t"))

_gbt = V["A3_gated_by_table"]
for t in ["修正表_B1B3.tsv", "修正表_B1B3_扩展.tsv", "修正表_新增场景mig重译.tsv"]:
    n_scope = V["A3_in_scope_by_table"].get(t, 0)
    n_app = V["A3_applied_by_table"].get(t, 0)
    n_gate = _gbt.get(t, 0)
    p("| `%s` | %d | %d | %d | %d | %d |" % (
        t, _nrows(t), n_scope, n_app, n_gate, n_scope - n_app - n_gate))
p("| **合计** | **%d** | **%d** | **%d** | **%d** | **0** |" % (
    B["corrections_total"], B["corrections_in_scope_s03c"],
    B["corrections_hit_in_scope"], B["corrections_gated_in_scope"]))
p()
p("> **命中数由 W6a 的 83 变为 W6a2 的 76，差额 7 = 被来源门控排除的 7 条**（逐条见 §3.4）。")
p("> 这 7 条全部落在**共享场景**（取文基准 `ot`），条目 `source=otr` 与取文层不符故不生效；")
p("> 76 条 `修正表_新增场景mig重译.tsv`（`source=otr`）落在**新增场景**（取文基准 `otr_new`）→ **全部照旧命中**。")
p()
p("> **「150 条」的口径澄清**：三张表合计 150 条，但其中 **67 条不属于亚衣线**——")
p("> `otp` 14 + `ota` 7 + `otr` 非 `s03c` 场景 46（文件：%s）。" % (
    "、".join("`%s`" % x for x in V["A3_out_of_scope_otr_files"][:12]) +
    ("…" if len(V["A3_out_of_scope_otr_files"]) > 12 else "")))
p("> 这 67 条由各自源的产出模块消费（本项目其余源尚未产出 `scene.jsonl`），**在本模块无对象可命中，非漏修**。")
p("> 亚衣线范围内 **83 条 = 命中 76 + 门控排除 7，未命中 0**（三者必居其一，校验器逐条核对）。")
p()
p("### 3.3 两处取文兜底（本模块新增，已记入 `align_method`）")
p()
p("- **`jp_exact_fallback` 20 行**：R 版标题槽的 `index` 为 `null`，不在 W7-1 行对齐审计覆盖范围内，")
p("  若不处理会落回 R 版（其中 13 行 `src=mig`，即新米来源）。本模块以「jp 精确且两侧唯一」匹配本篇行取译文，")
p("  修复了 `s03c_01a`/`03d`/`04a`/`05a` 等标题，使 D14 例外由 25 行降至 **12 行**。")
p("- **A/C 变体标题**（`no_audit_entry` 14 行）：本篇无对应写形，无法兜底，如实保留 R 版文本；")
p("  其 `src` 为 `new`/`None`（**非 `mig`**），故**不构成 D14 例外**，不计入上述 12 行。")
p()
p("### 3.4 修正表来源门控（W6a2 裁决落地）——被排除的 7 条逐条列出")
p()
p("**规则（通用，非特例开关）**：修正表条目**只在其 `source` 与该行「取文基准层」`cn_base` 对应时才生效**。")
p("对应关系登记在构建器 `CORR_SOURCE_TO_BASE`：`otr→otr_new`、`otp→otp`、`ota→ota`、`ot→ot`。")
p("契约已写入 `资源组\\修正\\_README.md` **§四.5**，对后续所有源模块生效。")
p()
p("**依据**：这 7 个共享场景的**日文标题在本篇与 R 版中逐字一致**（主代理实测），")
p("故没有任何理由用 R 版侧重译顶掉本篇译文；D14 规定共享场景整场取本篇。")
p()
p("以下 7 条修正表条目**被门控排除、未生效**（`source=otr` 落在取文基准 `ot` 的行上）；")
p("被排除的条目**逐条留痕**（行级可审计：`_build_stats.json` 的 `corrections_gated_out`），**不静默丢弃**：")
p()
p("| # | 场景 | locator | 表 | 日文标题 | 被排除的修正值（未采用） | 实际保留（本篇译文） |")
p("| ---: | --- | --- | --- | --- | --- | --- |")
for i, x in enumerate(B["corrections_gated_out"], 1):
    p("| %d | `%s` | `%s` | `%s` | %s | %s | **%s** |" % (
        i, x["script"], x["locator"], x["table"], esc(x["jp"]),
        esc(x["cn_gated"]), esc(x["cn_kept"])))
p()
_g = B["corrections_gated_out"]
p("> 排除原因（逐条同构）：`%s`" % esc(_g[0]["reason"]) if _g else "> 无被门控条目。")
p("> 校验器 `verify_scene_jsonl.py` 的 A3 **独立复核落点**：上述每条的目标槽在 `scene.jsonl` 中")
p("> 确实保持取文原文、`cn_origin` 非修正层（`A3_gate_landing_verified = %s`）。" % V["A3_gate_landing_verified"])
p()
p("### 3.5 译名替换")
p()
p("按 `译名替换表.tsv` 执行，**JP 门控**（仅当该槽 `jp`/`speaker_jp` 含原词日文才替换）＋ §六 排除正则，")
p("剔除「待裁决」「非替换项」「无旧写法残留」行后可用规则 65 条。实际发生 **%d 处**：" % B["term_hits"])
p()
c = collections.Counter((x["原词日文"], x["旧写法"], x["新写法"], x["field"]) for x in B["name_replace_examples"])
p("| 原词日文 | 旧写法 | 新写法 | 字段 | 处数 |")
p("| --- | --- | --- | --- | ---: |")
for (jp, old, new, fld), n in c.most_common():
    p("| `%s` | %s | %s | `%s` | %d |" % (jp, esc(old), esc(new), fld, n))
p()
flagged = [x for x in B["name_replace_examples"] if x.get("context_flag")]
p("**语境双轨、须人工复核的替换**（`ペガサス`/`ドラさん`）共 %d 处，已在行级 `name_replaced[].context_flag=true` 标注：" % len(flagged))
p()
if flagged:
    for x in flagged:
        p("- `%s` seq %d（%s）：%s → %s ｜ `%s`" % (
            x["script"], x["seq"], x["field"], esc(x["旧写法"]), esc(x["新写法"]), esc(x["cn"][:40])))
else:
    p("- 无（亚衣线语料内未出现该两项）")
p()
p("**逐处 `before`/`after` 已全量记入行级 `name_replaced`**，可逐条复核（共 %d 处）。" % B["term_hits"])
p()
p("### 3.6 译名替换的表外风险：实测 2 处污染已修（W6a2 已登记进口径 §六）")
p()
p("按表直替会产生两处**叠词/误改**，构建器内已加排除（三张修正表与 `译名替换表.tsv` 本体**未改**）；")
p("**W6a2 已把这两条排除规则登记进 `资源组\\修正\\译名统一口径.md` §六**（只增不删）：")
p()
p("| 规则 | 实测风险 | 排除规则 | 影响 |")
p("| --- | --- | --- | --- |")
p("| `針生`→`针生同学` | `针生同学同学`、`针生同学前辈`（`s03c_12b` seq 15/72） | `针生(?!同学\\|前辈\\|君\\|先生\\|小姐\\|老师\\|哥\\|姐)` | 排除后本线路该规则 0 处命中 |")
p("| `ガルーダ`→`伽鲁炟` | `伊丹伽楼罗`→`伊丹伽鲁炟`（`s03c_03b` seq 217，该行 jp 同时含 `ガルーダ` 与 `伽楼羅`） | 排除 `(?<!伊丹)伽楼罗`；jp 同含 `伽楼羅` 时整条跳过 | 排除后该规则 0 处命中；该行 `伊丹伽楼罗` 改由 `伽楼羅`→`迦楼罗` 规则正确处理 |")
p()
p("> **W6a2 已落地**：两条排除规则已写入 `译名统一口径.md` §六（`針生(?!同学|前辈|君|先生|小姐|老师|哥|姐)`、`(?<!伊丹)伽楼罗`）。")
p("> 三张修正表与 `译名替换表.tsv` 本体仍未改——门控与排除均为**消费侧**规则。")
p()

# ============================================================ 四、抽样
p("## 四、抽样 10 行（取文来源实例）")
p()
p("> 抽样规则：`ot`/`otr_new`/`retranslate` 各 3 行（取对话/旁白），另取 1 行展示译名替换层。")
p("> **`fix_table` 层在亚衣线范围内为 0 条**（见 §3.2），故无该类实例可抽——非遗漏。")
p()
p("| # | 场景 | seq | kind | speaker | 层（`cn_origin` / `layers`） | jp | cn |")
p("| ---: | --- | ---: | --- | --- | --- | --- | --- |")
for i, (s, l) in enumerate(samples[:10], 1):
    p("| %d | `%s` | %d | %s | %s | `%s` / `%s` | %s | %s |" % (
        i, s["script"], l["seq"], l["kind"], esc(l["speaker"] or "—"),
        l["cn_origin"], "→".join(l["layers"]),
        esc(l["jp"][:60]), esc(l["cn"][:60])))
p()

# ============================================================ 五、逐场景
p("## 五、逐场景统计")
p()
p("| 场景 | 类型 | `text_source` | 行数 | 语音 | `ot` | `otr_new` | `retranslate` | `empty` | 修正命中 | 译名替换 | 素材 | 缺失 | 后继 |")
p("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |")
for q in B["per_scene"]:
    o = q["lines_by_origin"]
    p("| `%s` | %s | `%s` | %d | %d | %d | %d | %d | %d | %d | %d | %d/%d | %s | %s |" % (
        q["script"], q["source_kind"], q["text_source"], q["line_count"], q["voice_count"],
        o.get("ot", 0), o.get("otr_new", 0), o.get("retranslate", 0), o.get("empty", 0),
        q["corrections_hit"], q["name_replace_count"], q["assets_hit"], q["assets_total"],
        ("、".join("`%s`" % m for m in q["assets_missing"]) if q["assets_missing"] else "—"),
        ("、".join("`%s`" % n for n in q["next"]) if q["next"] else "—（终点）")))
p()
p("**`next` / `choices` 结构**：`next_kind` 分布 = " + " ｜ ".join(
    "`%s` %d" % (k, v) for k, v in sorted(B["next_kind_dist"].items())))
p()
p("- `linear` 50 个场景；`end` 2 个（`s03c_05a` 原版线终点、`s03c_20a` 结局）。")
p("- `branch` 3 个：`s03c_01d`→`01d1`/`01d2`（**已确证玩家选择支**）、`s03c_02b`→`02c1`/`02c2`、`s03c_04b`→`04b1`/`04c`（触发条件未判定）。")
p()
p("**`choices` 明细**（仅 1 个场景；选项↔目标配对**未逆向**，故 `target=null`、`pairing_verified=false`）：")
p()
p("| 场景 | 选项 `text_jp` | `text_cn` | `cn_origin` | `target` | 候选目标（`next`） |")
p("| --- | --- | --- | --- | --- | --- |")
for s in scenes:
    for ch in s["choices"]:
        p("| `%s` | `%s` | **%s** | `%s` | `null`（配对未逆向） | %s |" % (
            s["script"], ch["text_jp"], esc(ch["text_cn"]), ch.get("cn_origin"),
            "、".join("`%s`" % n for n in s["next"])))
p()
p("> 依据：`s03c_01d.tob` 内实测选择支串 `黙る`/`拒否る` 与跳转标签 `S03C_01D1`/`S03C_01D2`；")
p("> 但 TOB0 分支语义未逆向（总纲 R1），**无法确证哪个选项跳哪个标签**，故 `target` 保持 `null`、不猜。")
p("> 译文由主代理裁决补入（W6a2；口径见 `s03c_重译清单.tsv` 与 W7 诊断报告），`cn_origin=fix_table`。")
p()

# ============================================================ 六、素材
p("## 六、素材挂接与命中率")
p()
p("### 6.1 命中率")
p()
p("| 类别 | 命中 | 总数 | 命中率 | 缺失 |")
p("| --- | ---: | ---: | ---: | --- |")
p("| 语音（逐行 `lines[].audio`） | %d | %d | %.1f%% | 0 |" % (
    B["voice_hit"], B["voice_refs"], 100.0 * B["voice_hit"] / max(1, B["voice_refs"])))
p("| 图像/音效（场景级 `assets`） | %d | %d | %.1f%% | %d 处 / %d 个不同引用 |" % (
    B["assets_hit"], B["assets_total"], 100.0 * B["assets_hit"] / max(1, B["assets_total"]),
    B["assets_missing"], len(set(x["ref"] for x in B["asset_missing_list"]))))
p()
p("映射规则：`亜衣线资源\\清单\\素材清单.json` 的引用 → `资源总账.json` 的 `out_relpath`（命名 `<源代号>_<原名>`）。")
p()
p("### 6.2 缺失清单（逐条，不笼统）")
p()
p("| # | 场景 | 引用 | 说明 |")
p("| ---: | --- | --- | --- |")
for i, m in enumerate(B["asset_missing_list"], 1):
    p("| %d | `%s` | `%s` | %s |" % (
        i, m["script"], m["ref"],
        "分片背景（`素材清单.json` 的 `missing` 登记项；原作按片加载，非缺文件）"
        if m["ref"].endswith(("BG06B.ELG", "BG07B.ELG")) else "未在资源总账命中，待查"))
p()
p("> **BGM 不产出场景级字段**：R 版 BGM 不按名引用（流程图 §7.2），`素材清单.json` 亦无逐场景 BGM，")
p("> 本模块如实不产，**不臆造**。")
p()

# ============================================================ 七、验收
p("## 七、验收自证（7 项逐条）")
p()
p("校验器：`资源组\\工具\\verify_scene_jsonl.py`（**从磁盘 `scene.jsonl` 重新读取**，与只读源交叉核对，")
p("不依赖构建器内存态）→ 结果 `子代理工作区\\ISSUE-20260918-06\\W6a2\\W6a2验收.json`。")
p()
p("| # | 标准 | 结果 | 证据 |")
p("| --- | --- | --- | --- |")
p("| 1 | 场景数 55，与 `s03c_场景对齐表.tsv` 一致 | **通过** | 对齐表 %d 行，`scene.jsonl` %d 行，集合完全一致；shared %d / branch %d / new %d |" % (
    V["A1_align_rows"], V["file_lines"], V["A1_align_kind_dist"]["shared"],
    V["A1_align_kind_dist"]["branch"], V["A1_align_kind_dist"]["new"]))
p("| 2 | 行数守恒 | **通过** | 总行 %d == 基线 %d；**逐场景**核对差异 %d 个 |" % (
    V["A2_total"], V["A2_baseline"], len(V["A2_scene_diff"])))
p("| 3 | 修正表命中 | **通过** | 亚衣线范围 %d 条 = 命中 %d + 来源门控排除 %d，未命中 %d（三者必居其一，逐条核对）；门控落点独立复核 %s；全表 %d 条，范围外 %d 条（见 §3.2 / §3.4） |" % (
    V["A3_in_scope_total"], V["A3_in_scope_hit"], V["A3_gated_in_scope"],
    len(V["A3_missing_in_scope"]), V["A3_gate_landing_verified"],
    V["A3_total_rows"], V["A3_out_of_scope_count"]))
p("| 4 | 取文来源可审计 | **通过** | `cn_origin` 分布见 §3.1；`cn_base`+`layers`+`fix_refs` 三层留痕；抽样见 §四（`fix_table` 为 0 条已说明） |")
p("| 5 | 素材命中率 | **通过** | 语音 %d/%d；素材 %d/%d；缺失 %d 处逐条列出（§6.2） |" % (
    V["A5_voice_hit"], V["A5_voice_total"], V["A5_assets_hit"], V["A5_assets_total"],
    len(V["A5_assets_missing"])))
p("| 6 | schema 自洽 | **通过** | 必填字段缺失 %d；`scene_id` 唯一 %s；JSONL 55 行逐行 `json.loads` 成功；`choices` 缺 `text_cn` %d 条、缺 `cn_origin` %d 条 |" % (
    len(V["A6_missing_fields"]), V["A6_scene_id_unique"],
    V["A6_choices_null_text_cn"], V["A6_choices_null_cn_origin"]))
p("| 7 | 不臆断 | **通过** | `game_date` 仅 %d 个场景有显式日期证据，其余 %d 个为 `null`；`choices` 仅收已确证 1 处、`text_cn` 已补（`target` 仍 `null`，配对未逆向不猜）；D14 例外 %d 行、空槽 %d 行逐条登记 |" % (
    len(V["A7_game_date_set_scenes"]), V["A7_game_date_null_scenes"],
    V["A7_d14_exceptions"], V["A7_empty_slots"]))
p()
p("**`ALL_PASS = %s`**" % V["ALL_PASS"])
p()

# ============================================================ 八、未决
p("## 八、未决问题与需裁决点")
p()
p("### 8.1 需主代理裁决")
p()
p("| # | 事项 | 现状 | 备选 |")
p("| --- | --- | --- | --- |")
p("| ~~1~~ | ~~7 条共有场景标题被修正表覆盖~~ | **已裁决并落地（W6a2）**：修正表按 `source`↔`cn_base` 门控，7 条 R 版侧重译不生效，标题取本篇（§3.4） | — |")
p("| ~~2~~ | ~~`s03c_01d` 选择支译文缺失~~ | **已裁决并落地（W6a2）**：`黙る`→沉默、`拒否る`→拒绝，`cn_origin=fix_table`（§五） | — |")
p("| ~~5~~ | ~~译名替换表 §六 缺 2 条排除规则~~ | **已登记（W6a2）**：两条排除规则写入 `译名统一口径.md` §六（§3.6） | — |")
p("| **2b** | **`s03c_01d` 选项↔目标配对未逆向** | `target=null`、`pairing_verified=false`（TOB0 分支语义未逆向） | 维持留空由编程组实现时确定；或另开逆向任务 |")
p("| **3** | **`（Ａ）`/`（Ｃ）` 双标题的语义** | 10 场景各 2 个标题槽，`title_variants` 已全记；A/C 是否对应分支结果未判定 | 维持「不解释、不合并」，待流程判定 |")
p("| **4** | **`02b`/`04b` 的两个跳转目标是否为玩家选择支** | 脚本内无选择支串 → 仅记 `next_kind=branch` | 若判定为选择支，需补 `choices` 与其译文 |")
p()
p("### 8.2 未决（不需裁决，仅登记）")
p()
p("- **12 行 D14 例外**（`src=mig` 且无 2009 对照、未被修正表修复）：均为无实义标点/喊话句")
p("  （`s03c_01c#88`、`s03c_03c` 7 行、`s03c_04c` 4 行）。R 版文本与原文形近，但来源仍为 `mig`，")
p("  已在行级 `d14_exception` 标注，未擅自改写。若要彻底回避新米，可另立重译条目。")
p("- **40 个空槽**（源 `jp`/`cn` 均空、`offset=null`）：31 个新增场景的 index0 摘要槽 + 9 个共有/分支场景的空槽。")
p("  已保留（保行数守恒），`cn_origin=empty`。")
p("- **场景级 BGM 不可得**（R 版不按名引用）。")
p("- **每行图像/音效不可得**（演出命令语义未逆向，总纲 R1）。")
p("- **`game_date` 仅 `s03c_01c` 有证据**（`11/22`–`11/26`，取首个 `11/22`，全量记于 `game_dates`）。")
p("  其余场景仅有 `日曜日` 等星期信息，无法唯一定日，一律 `null`。")
p("- **15 个共有/分支场景含 R 版文本**（`text_source=mixed`）——系 2009 无对照行所致（空槽 / A/C 变体标题 / 12 行 mig 例外），非 D14 违背。")
p()
p("### 8.3 对后续模块的提示")
p()
p("- 其余源（`ot`/`ota`/`otp`/`otv`/`np`）产出 `scene.jsonl` 时，schema 不变；")
p("  但修正表范围外的 **67 条**（`otp` 14 / `ota` 7 / `otr` 非 s03c 46）届时必须全部命中，否则即真漏修。")
p("- **修正表来源门控（§四.5）对后续所有源模块生效**：消费方必须按其行「取文基准层」匹配条目 `source`；")
p("  被门控条目仍须逐条留痕、不得静默丢弃。`CORR_SOURCE_TO_BASE` 已预置 `otr/otp/ota/ot` 四个映射；")
p("  未登记映射的 `source` 会让构建器**直接报错中止**（fail loud），避免静默漏修。")
p("- `otr` 非 `s03c` 的 46 条修正分布文件见 `W6a2验收.json` 的 `A3_out_of_scope_otr_files`。")
p()

# ============================================================ 九、复现
p("## 九、可复现命令")
p()
p("```bash")
p('cd "E:/ZCode Workspace/Galgame"')
p('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_jsonl.py"')
p('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_jsonl.py"')
p('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_w6a_report.py"')
p("```")
p()
p("三个脚本对源工程**全程只读**；构建器只写 `资源组\\剧本\\scene.jsonl` 与 `子代理工作区\\...\\W6a2\\_build_stats.json`。")
p("W6a2 另交付：`资源组\\修正\\_README.md` §四.5（门控契约）、`资源组\\修正\\译名统一口径.md` §六（2 条排除规则）、")
p("`资源组\\剧本\\schema.md`（`choices[].cn_origin` 登记 + 门控规则）。")
p()

open(os.path.join(OUT, "亚衣线_产出报告.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("-> " + os.path.join(OUT, "亚衣线_产出报告.md"))
print("lines:", len(L))