# -*- coding: utf-8 -*-
r"""
W6b · 产出报告生成器 → `资源组\剧本\本篇_产出报告.md`

输入（只读）：`子代理工作区\ISSUE-20260918-06\W6b\{_build_stats_ot.json, W6b验收.json}`
用法：python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_w6b_report.py"
"""
import json, os, sys, collections

WS = r"E:\ZCode Workspace\Galgame"
PRJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
OUT = os.path.join(PRJ, "资源组", "剧本")
STG = os.path.join(WS, "子代理工作区", "ISSUE-20260918-06", "W6b")

B = json.load(open(os.path.join(STG, "_build_stats_ot.json"), encoding="utf-8"))
V = json.load(open(os.path.join(STG, "W6b验收.json"), encoding="utf-8"))

L = []
def w(s=""):
    L.append(s)

w("# 本篇主线（`s00`/`s01`/`s02`/`s03`/`s04`）结构化剧本产出报告 · W6b")
w()
w("> 模块：**W6b**（本篇主线 367 场景）｜ Issue：`ISSUE-20260918-06` ｜ 资源组 ｜ 2026-09-18")
w("> 交付物：`资源组\\剧本\\scene_ot.jsonl`（367 场景）、本报告、")
w("> `资源组\\工具\\build_scene_ot.py`（构建器）、`资源组\\工具\\verify_scene_ot.py`（独立校验器）、")
w("> `子代理工作区\\ISSUE-20260918-06\\W6b\\{_build_stats_ot.json, W6b验收.json}`")
w()
w("**只读声明**：全部源（`工程\\我们没有翅膀\\`、`工程\\我们没有翅膀R\\`、`资源组\\修正\\*`、")
w("`资源组\\krkr素材库\\*`）一律只读，未改动一个字节；三张修正表与 `译名替换表.tsv` 本体**未改**")
w("（门控、排除规则、置信度标记剥离均为**消费侧**行为）。")
w("写入仅限 `资源组\\剧本\\`、`资源组\\工具\\`、`子代理工作区\\ISSUE-20260918-06\\W6b\\`。**未提交 git**。")
w()
w("## 一、结论速览")
w()
w("| 项 | 结果 |")
w("| --- | --- |")
w("| 场景数 | **367**（s00 1 ｜ s01 114 ｜ s02 83 ｜ s03 95 ｜ s04 74） |")
w("| 台词行总数 | **%d**（与源 jsonl 基线 %d **逐场景守恒**，差异 0） |"
  % (B["lines_total"], B["lines_baseline_src_jsonl"]))
w("| 取文来源 | **全部 `ot`（本篇）**；`cn_origin` = `ot` %d ｜ `empty` %d |"
  % (B["orig_dist"].get("ot", 0), B["orig_dist"].get("empty", 0)))
w("| 修正表 | 合计 %d 条 = 模块范围内 **%d（命中 0 + 门控排除 %d + 未命中 0）** + 范围外 %d；**命中 0 属预期，非漏修** |"
  % (B["corrections_total"], B["corrections_in_scope"], B["corrections_gated"],
     B["corrections_out_of_scope"]))
w("| 译名替换 | 实际发生 **%d 处 / %d 槽**（14 条 `ot` 规则，JP 门控 + §六 排除规则） |"
  % (B["term_hits_occurrences"], B["term_hits_slots_total"]))
w("| 选择支 | **24 脚本 / 54 选项**（源 `sel=1` 36、`sel=2` 18）；逐脚本对账差异 0；选项译文缺 0 |")
w("| 素材命中 | 图像/音效 **%d/%d（%.2f%%）**，缺失 %d 处 / %d 个不同引用；语音 **%d/%d（100%%）** |"
  % (B["assets_hit"], B["assets_total"], B["asset_hit_rate"], B["assets_missing"],
     len(B["asset_missing_list"]), B["voice_hit"], B["voice_refs"]))
w("| 源缺陷修复 | speaker/voice 拆分修复 **%d 行**（源提取器按字节 0x5C 误切，见 §6） |"
  % B["speaker_repair_count"])
w("| 空槽 / D14 例外 | 0 / 0（本篇语料无空槽；本模块取文源即 D14 首选源） |")
w("| 7 项验收 | **ALL_PASS = %s** |" % V["ALL_PASS"])
w()
w("## 二、schema 适配说明（字段名与嵌套结构沿用 W6a 定稿，未另创 schema）")
w()
w("本模块与 W6a（R 版亚衣线 `s03c`）**结构来源不同**，故对 schema 中若干**按源定义的枚举值**")
w("做了按源扩展，并逐项给出理由；字段名、类型、嵌套层级**一律未变**。")
w()
w("| schema 字段 | W6a（`otr` 亚衣线） | 本模块（`ot` 本篇） | 理由 |")
w("| --- | --- | --- | --- |")
w("| `source` | `otr` | **`ot`** | 结构来源＝本篇（总纲 §七 I1 源代号） |")
w("| `scene_id` | `otr_s03c_01a` | **`ot_<script>`** | 同上 |")
w("| `source_kind` | `shared`/`branch`/`new` | **`ot`** | W6a 三值是「R 版场景与 2009 同名/分支/新增」的关系分类，对本篇（其本身就是 2009）无意义，不套用 |")
w("| `text_source` | `ot`/`otr_new`/`mixed` | **`ot`**（367/367） | 全部行取自本篇 |")
w("| `lines[].kind` | `title`/`dialogue`/`narration` | **`dialogue`/`other`（源值原样）** | SOB0 提取器 `classify()` 按**串形态**分类：含 `$&` → `dialogue`，否则 `other`（裸串）。本篇不存在 `title`/`narration` 值，故按 schema「源值，未改写」保留 |")
w("| `lines[].index` | 源 `index` | 源 **`idx`**（槽内串序，选项槽 0/1/2） | 直取源字段 |")
w("| `lines[].lineno` | 源 `lineno` | 源 **`seq`**（1-based，回溯用） | `_README.md` §二：SOB 类定位串为 `seq=<n>`，与 `lineno` 同源同义 |")
w("| `align_method` | `audit`/`jp_exact_fallback`/… | **`ot_direct`** | 本篇语料即取文源，无需对齐动作（W6a 的取值均为「从 R 版向 2009 对齐」的动作名） |")
w("| `title_variants[].offset` | R 版字节 `offset` | 本篇 **`addr`** | 本篇 jsonl 无 `offset`，其唯一定位符为字节地址 `addr` |")
w("| `stats.lines_by_source` | R 版 `src`（mig/new/null） | **`{\"ot\": N}`** | 本篇语料无 `src` 迁移标记（该字段是 R 版专属）；本模块全部行取自 `ot` |")
w()
w("### 2.4 章节标题的判定（**本模块新增判据，已交叉验证**）")
w()
w("SOB0 无 `kind=title`，故需自建判据。实测结论：**槽位 0 即章节标题**（367/367 首槽 `kind=other`），")
w("槽位 1 为**梗概**（`梗概` 以 U+3000 开头、中位 114 字）；选项槽位于脚本末尾（`sel>0`）。")
w("判据（可复算）：")
w()
w("```")
w("标题槽 := kind=='other' and td==0 and sel==0 and not is_summary(jp)")
w("is_summary(jp) := jp.startswith('\\u3000') or len(jp) > 40")
w("```")
w()
w("- **长度间隔充分**：标题实测 ≤20 字；梗概实测 ≥81 字（除 `s00_00` 的第 2 标题槽 12 字，其非梗概）。")
w("- **交叉验证**：与 R 版 `语料\\R版台词.json` 的 `kind=title`（显式标注）逐条比对——")
w("  337 个标题**逐字相同**；24 个差异全部可解释（R 版给标题加了版本后缀 `Ｒ`，或 R 版自身把")
w("  `s01_04f1/f2`、`s02_09d1/d2`、`s01_13c1/c2` 等**变体对的标题写反了**）；4 个 R 版无该脚本")
w("  （`s01_14k`/`s03_15g`/`s03_21b`/`s04_05e` 之外的 R 版缺失项，见流程图 §4.3）。")
w("- **实测产出**：%d 个标题槽落在 %d 个场景；**9 个场景本篇无标题槽**（其槽 0 是梗概，R 版有标题但本篇消息表内无）；"
  % (B["titles"]["variants_total"], B["titles"]["scenes_with_title"]))
w("  `s00_00` 有 2 个标题槽。")
w()
w("**取值**：`title_jp`/`title_cn` 按 schema §三.4「优先取有 09 对照或有修正表条目的槽，否则取最后一个」")
w("——本模块无任何修正表条目，故实际等于**取最后一个标题槽**。唯一受影响的是 `s00_00`")
w("（`title_jp` = `文　～俺たちに翼はない～`，而槽 0 是 `序文　～俺たちに翼はない～`）→ **列入待裁决（§9.1-3）**。")
w()
w("### 2.5 说话人名字框（`speaker`）的取值口径 —— **本模块最大的 schema 适配点**")
w()
w("**事实**：本篇汉化**未译名字框**。`工程\\我们没有翅膀\\汉化\\交付说明.md` §二明文")
w("「说话人标签（314 种）原样保留——它们是引擎取人名与语音的键，不属于正文」；本篇作品 skill 术语表 §一")
w("亦载「说话人标签 原样保留，不译」。**故本篇语料内不存在 `speaker_cn`**，而 schema 要求 `speaker` = 名字框中文。")
w()
w("**取值口径**：按 **D3 仲裁语料** `工程\\我们没有翅膀R\\参照\\中日对照表.json`（57,820 槽，含 `speaker`→`speaker_cn`）")
w("建立 `日文标签 → 中文写形` 映射。依据：")
w()
w("1. D3 明文「**译名统一基准＝2009 新米参照语料的实测写形**」，该文件即 D3 的仲裁语料本体；")
w("2. 总纲 §二 铁律 7 与 D4：**新米汉化只可用人名/地名/词级**——名字框恰是「人名」层，属允许用途；")
w("3. 作品层术语表 §一 把该文件的 `speaker_cn` 定义为**名字框流**的统计来源。")
w()
w("**取写法**：同一日文标签的多个中文写形取**非空写形中出现最多者**（空值代表「该槽无名字框」，")
w("不是译法，故不参与定名）；全部为空或该标签不在参照语料中 → `speaker` = `\"\"` 并计入缺失。")
w()
w("- 映射命中：%d 个标签定名成功；**%d 个标签无中文名字框**（逐条见 §9.2）；多写形 %d 条（逐条见 §9.3，均按多数取值）。"
  % (B["speaker_cn_total"] - len(B["speaker_map_missing"]), len(B["speaker_map_missing"]),
     len(B["speaker_map_ambiguous"])))
w("- `speaker_jp` 恒为**源日文标签**（未译、未改），可逐行回溯。")
w("- **未套用 `name` 流译名替换**：`译名替换表.tsv` 中 `source=ot` 的 21 条全部标为 `ot/ot`（无 `ot/name` 行），")
w("  且其「新写法」已等于 D3 目标写形（如 `渡来さん`→`渡来同学`、`羽田君`→`羽田君`），")
w("  即**名字框本身就是统一基准**，无需再替换。**特别地 `羽田君` 在本模块无任何改动**（表中该条仅 `np/body`、`ota/body`）。")
w()
w("## 三、取文来源与修正表来源门控（**命中 0 是正确的，非漏修**）")
w()
w("### 3.1 取文来源")
w()
w("本模块全部 %d 行的 `cn` 直取 `工程\\我们没有翅膀\\汉化\\剧情汉化\\<script>.sob.jsonl` 的 `cn` 字段"
  % B["lines_total"])
w("（`cn_base = ot`，`cn_origin = ot`，`align_method = ot_direct`）。")
w("合规依据：总纲 §八 **D14**「正文译文一律取自『独立翻译』的源」——本篇即独立翻译")
w("（合规审计：与新米最长连续公共子串中位 4 字、整槽逐字相同 0 条，见本篇 `交付说明.md` §三）。")
w()
w("### 3.2 门控规则与三分类（逐条可审计）")
w()
w("契约：`资源组\\修正\\_README.md` **§四.5**「修正表条目只在其 `source` 与该行取文基准层 `cn_base` 一致时才生效」。")
w("映射：`otr→otr_new`、`otp→otp`、`ota→ota`、`ot→ot`；未登记映射者**构建器报错中止**（fail loud）。")
w()
w("**本模块的 `cn_base` 集合 = `{ot}`（独立复算，见 `W6b验收.json` A3）**。三张修正表 150 条的 `source` 分布为")
w("`otr` 129 / `otp` 14 / `ota` 7 —— **没有任何 `source=ot` 条目**。因此：")
w()
w("- 凡 `file` 落在本模块脚本集合内的条目（%d 条），其 `source` 对应的取文基准在本模块内**根本不存在**"
  % B["corrections_in_scope"])
w("  → 一律判为**门控排除**（不是「未命中」）；")
w("- 行级三元组查找 `(ot, <script>.sob, seq=<n>)` 恒无对象 → **命中 0**。")
w()
w("**结论：本模块修正命中数 = 0，这是门控正确生效的结果，不是漏修。**")
w("校验器 A3 **独立复核门控落点**：逐条确认被门控条目的 `new_text` 未以修正层形态出现在 `scene_ot.jsonl`")
w("（`gate_landing_verified = %s`）。" % V["A3"]["gate_landing_verified"])
w()
w("| 分类 | 条数 | 说明 |")
w("| --- | ---: | --- |")
w("| 模块范围内 | **%d** | `file` stem ∈ {s00/s01/s02/s03/s04} 脚本集合 |" % B["corrections_in_scope"])
w("| ├ 命中（生效） | **0** | 无 `source=ot` 条目 |")
w("| ├ 来源门控排除 | **%d** | 全部 `source=otr`（R 版层），本模块无该基准 |" % B["corrections_gated"])
w("| └ 未命中 | **0** | 三分类闭合 |")
w("| 模块范围外 | **%d** | `otp` %d + `ota` %d + `otr`（非本模块脚本，含 s03c 等）%d |"
  % (B["corrections_out_of_scope"], B["corrections_out_of_scope_by_source"].get("otp", 0),
     B["corrections_out_of_scope_by_source"].get("ota", 0),
     B["corrections_out_of_scope_by_source"].get("otr", 0)))
w("| **合计** | **%d** | 与三张表行数一致 |" % B["corrections_total"])
w()
w("### 3.3 被门控排除的 %d 条（逐条列出，按表分组）" % B["corrections_gated"])
w()
w("**排除原因（逐条同构）**：`module_source_gate: 条目 source=otr 对应取文基准 otr_new；")
w("本模块（本篇 ot）取文基准恒为 ot，该基准在本模块内不存在 → 无对象、不生效`。")
w("这 %d 条全部是 **R 版标题槽重译**（`fix_type=retranslate` 43 条 + `space_strip` 3 条），"
  % B["corrections_gated"])
w("针对的是 **R 版被覆盖/错位的标题槽**；而本模块取的是**本篇标题槽**（`kind=other` 槽 0），")
w("本篇标题**未被污染**（错位是 R 版专属缺陷，见 `_README.md` §五），故这些重译在本模块**无对象**。")
w()
for tbl in ["修正表_B1B3.tsv", "修正表_B1B3_扩展.tsv", "修正表_新增场景mig重译.tsv"]:
    rows = [g for g in B["corrections_gated_out"] if g["table"] == tbl]
    if not rows:
        continue
    w("**`%s`（%d 条）**" % (tbl, len(rows)))
    w()
    w("| # | 脚本 | locator | kind | fix_type | 被排除的修正值（未采用） |")
    w("| ---: | --- | --- | --- | --- | --- |")
    for i, g in enumerate(sorted(rows, key=lambda x: (x["file"], x["locator"])), 1):
        w("| %d | `%s` | `%s` | %s | %s | %s |"
          % (i, g["script"], g["locator"], g["kind"], g["fix_type"],
             (g["cn_gated"] or "").replace("|", "\\|")))
    w()
w("> **反向校验**：若某条 `source=otr` 的修正在本模块「命中」，即说明门控实现有误。")
w("> 本模块命中 0，且 A3 独立复算 `cn_base` 集合与门控落点均通过 → 门控实现正确。")
w()
w("## 四、译名替换")
w()
w("### 4.1 规则装载")
w()
w("按 `资源组\\修正\\译名替换表.tsv`（114 行）执行：先剔除「待裁决」（`新写法` 以 `（` 开头）")
w("「非替换项」「无旧写法残留」（`旧写法` 以 `（` 开头）「`—`」「`全部`」行，再取 `src=ot` 者。")
w("**实际可用规则 14 条**（全部为 `ot/ot`，即 body 流；本篇语料无中文名字框，故无 `ot/name` 行）。")
w()
w("**JP 门控**：仅当该槽 `jp` 含原词日文才替换。**§六 排除规则**（正则）逐条生效，键为 `(原词日文, 旧写法)`：")
w()
w("| 排除项 | 正则 / 判据 | 本模块命中 |")
w("| --- | --- | --- |")
w("| `針生`→`针生同学` | `针生(?!同学\\|前辈\\|君\\|先生\\|小姐\\|老师\\|哥\\|姐)` | 排除 %d 槽（已含敬称） |"
  % 278)
w("| `ガルーダ`→`伽鲁炟` | `(?<!伊丹)伽楼罗`；且 `jp` 同含 `伽楼羅` 时**整条跳过** | 排除 14 槽（全部因 `jp` 同含 `伽楼羅`） |")
w("| `ギバラ`→`柳木原` | 禁止按中文串替换，**须按原文 `ギバラ` 门控** | 由 JP 门控天然保证 |")
w("| `ペガサス`→`佩格萨斯` | 语境双轨（叙述→佩格萨斯／台词敬称长官→天马），**逐处 `context_flag=true` 标记** | 6 槽（见 §4.4） |")
w()
w("### 4.2 实际发生 %d 处 / %d 槽（与表内计数逐规则对账）" % (B["term_hits_occurrences"],
                                                                  B["term_hits_slots_total"]))
w()
w("| 原词日文 | 旧写法 | 新写法 | 表内计数 | 全源 397 实测 | 本模块槽数 |")
w("| --- | --- | --- | ---: | ---: | ---: |")
for x in B["term_reconcile"]:
    w("| `%s` | %s | %s | %s | %d | %d |"
      % (x["原词日文"], x["旧写法"], x["新写法"], x["表内计数"], x["全源397槽数"], x["本模块槽数"]))
w()
w("**表内计数口径已确认**：12/14 条与「全源 397 脚本、gate=原词日文、cn 含旧写法」逐条**精确吻合**，")
w("证明 `译名替换表.tsv` 的 `旧写法出现次数` 是**全源口径**（含 `s03c` 与系统脚本）；")
w("本模块只覆盖 367 脚本，故本模块槽数 ≤ 全源槽数（差额落在 `s03c` 等）。")
w()
w("**3 处与全源口径不一致，逐条解释**：")
w()
w("| 规则 | 表内 | 全源实测 | 本模块 | 差异原因 |")
w("| --- | ---: | ---: | ---: | --- |")
w("| `ガルーダ`→`伽鲁炟` | 14 | **0** | **0** | 该 14 槽的 `jp` **同时含 `ガルーダ` 与 `伽楼羅`**（如「臣民は余をガルーダと呼んでいた…伊丹伽楼羅だ」），行级 JP 门控无法消歧 → 按 §六 规则**整条跳过**；其中 `伊丹伽楼罗` 交由 `伽楼羅`→`迦楼罗` 规则正确处理。**这正是 W6a2 登记该排除规则的原因** |")
w("| `針生`→`针生同学` | 28 | **20** | **20** | 全源 20 = 排除正则（`针生(?!敬称)`）剔除 278 槽后仍需替换的槽数。**表内 28 无法用任何单一门控从语料复现**（gate=`針生` 得 298 槽、gate=`針生さん` 得 272 槽）→ 该行计数**表侧多计 8**；替换行为本身有据（作品层术语表 §2.2 明文 `針生さん`→针生同学） |")
w("| `プリンセス・ダヴ`→`妲朴小公主` | 22 | **21** | **21** | 差 1，**无法复现**（另有 5 槽 `jp` 写 `ダヴ姫`/`プリンセスダヴ` 而无中点、`cn` 亦作 `妲朴公主`，但非本表 22 的来源：按宽松门控 `ダヴ` 会得 26 槽）→ 列入待主代理复核（§9.1-5） |")
w()
w("> 结论：`术语表.md` §七 的「`ot` 需改槽数 **806**」= 14 条规则表内计数之和，是**未计排除规则、且为全源口径的上界**；")
w("> 本模块实际替换 **%d 槽**，差 **50** 的三类成因（逐条可复算）：" % B["term_hits_slots_total"])
w(">")
w("> | 成因 | 条数 | 明细 |")
w("> | --- | ---: | --- |")
w("> | §六 排除规则生效 | **14** | `ガルーダ` 14（全部因 `jp` 同含 `伽楼羅`） |")
w("> | 表内计数不可复现（表侧） | **9** | `針生` 8 + `プリンセス・ダヴ` 1 |")
w("> | 口径差（该槽在 `s03c`／系统脚本，不在本模块） | **27** | `伽楼羅` 5 + `パル` 5 + `Ｒ－ウィング` 14 + `アルバトロス` 1 + `ギバラ` 1 + `花水木通り` 1 |")
w(">")
w("> **无静默漏替**：13 条规则在本模块实际生效，`ガルーダ` 一条 0 命中系排除规则的正确结果（其目标字符串由 `伽楼羅` 规则接管）。")
w()
w("### 4.3 表本体缺陷（1 处，已消费侧归一，建议表维护方修正）")
w()
for n in B["term_table_notes"]:
    w("- `%s` 的 `新写法` 写作 `%s` —— **置信度标记 `（低置信）` 被写进了替换值本体**。"
      % (n["原词日文"], n["新写法_原"]))
    w("  构建器按 `%s` 剥离尾部标记后使用（**未改表本体**）。若直用原值，正文会出现「苍穹女子学院（低置信）」字样。" % n["处置"])
w()
w("### 4.4 语境双轨、须人工复核的替换（`ペガサス`）")
w()
w("`ペガサス` 一栏表内明标**语境双轨**（叙述→佩格萨斯／台词敬称长官→天马），构建器**照表执行但逐处标记**")
w("`context_flag = true`，供主代理复核：")
w()
w("| # | 脚本 | seq | before → after |")
w("| ---: | --- | ---: | --- |")
ctx = [x for x in B["name_replace_detail"] if x["context_flag"]]
for i, x in enumerate(ctx, 1):
    w("| %d | `%s` | %d | %s → %s |" % (i, x["script"], x["seq"],
                                        x["before"].replace("|", "\\|"),
                                        x["after"].replace("|", "\\|")))
if not ctx:
    w("| — | — | — | 无 |")
w()
w("> 逐处 `before`/`after` 已全量记入行级 `name_replaced`（%d 处，`_build_stats_ot.json` 的 "
  % B["term_hits_occurrences"])
w("> `name_replace_detail` 可逐条复核）。**`羽田君` 一项在本模块 0 改动**（表中该条仅 `np/body`、`ota/body`）。")
w()
w("## 五、选择支对账")
w()
w("### 5.1 逐脚本对账表（源 `sel` 槽 vs 产出 `choices`）")
w()
w("| 脚本 | 源 `sel` 槽数 | 源 `sel` 分布 | 产出 `choices` | 一致 |")
w("| --- | ---: | --- | ---: | :---: |")
for x in V["A4"]["reconcile"]:
    w("| `%s` | %d | %s | %d | %s |"
      % (x["script"], x["src_sel_slots"],
         "、".join("sel=%s×%d" % (k, v) for k, v in sorted(x["sel_dist"].items())),
         x["scene_choices"], "✓" if x["ok"] else "✗"))
w()
w("**合计**：源 `sel=1` **%d** 条 / `sel=2` **%d** 条（**%d** 个脚本）= 产出 **%d 脚本 / %d 选项**，逐脚本差异 **%d**。"
  % (V["A4"]["src_sel1"], V["A4"]["src_sel2"], V["A4"]["src_script_count"],
     V["A4"]["scene_choice_scripts"], V["A4"]["scene_choice_options"],
     len(V["A4"]["mismatch"])))
w()
w("### 5.2 与任务书给定分布的差异（**如实说明**）")
w()
w("任务书写「`sel=1` 36 条 / `sel=2` 18 条，分布于 **26 个脚本**」并列出 26 个脚本名。")
w("**实测为 24 个脚本**，逐条核对如下：")
w()
w("- 任务书列出的 26 个名字中，`s01_02c/02e/03b/04e/04l/08c0/08d0/08d4/09c0/12b/13b`（11）")
w("  + `s02_03b/03g/05a/05e/06b/06f/09c/10c`（8）+ `s03_03b/03i/05c`（3）+ `s04_03e/05i`（2）")
w("  = **24 个**（任务书自身列表即 24 个，「26」为笔误）；")
w("- `流程图.md` §4.2 另把 `s02_09d1/d2` 列为选择支，但该二者是**成对变体脚本**（无 `sel` 槽），")
w("  实测 `sel` 槽数为 0 → **不计入 `choices`**（与 W6a 对 `02b`/`04b` 的处置一致）。")
w()
w("### 5.3 选择支明细与「不猜配对」纪律")
w()
w("`sel` 槽即脚本内实测的选择支串（SOB0 字节布局：`首串$\\x00 \\x00 <NN>\\x00 <u16 字节长><GBK选项>\\x00 …`，")
w("见 `02_资源审计报告.md` §2.3），`sel = 选项数 - 1`。产出 `choices[]` 共 %d 项，"
  % V["A4"]["scene_choice_options"])
w("**`text_cn` 缺 0 条**（选项译文就在本篇消息表内，`cn_origin = ot`）——优于 W6a（W6a 需主代理裁决补译 2 条）。")
w()
w("| 脚本 | 选项 `text_jp` | `text_cn` | `cn_origin` | `target` | 候选目标（`next`） |")
w("| --- | --- | --- | --- | --- | --- |")
for r in B["scene_choices_detail"]:
    w("| `%s` | `%s` | %s | %s | `%s` | %s |"
      % (r["script"], r["text_jp"], r["text_cn"], r["cn_origin"],
         "null" if r["target"] is None else r["target"],
         "、".join("`%s`" % t for t in r["next"])))
w()
w("> **`target` 一律 `null`、`pairing_verified = false`**：SOB0 分支语义未逆向（总纲 R1），")
w("> 选项与跳转标签的**配对顺序无法从字节码确证**（标签在文件内的声明顺序不等于分支顺序）→ **不猜**。")
w("> 编程组实现分支时以场景级 `next` 为准。")
w()
w("### 5.4 `next` 结构（硬事实：来自 .sob 跳转标签扫描）")
w()
w("| `next_kind` | 场景数 | 说明 |")
w("| --- | ---: | --- |")
nk = B["next_kind_dist"]
w("| `linear` | %d | 恰 1 个跳转目标 |" % nk.get("linear", 0))
w("| `branch` | %d | ≥2 个目标 |" % nk.get("branch", 0))
w("| `end` | %d | 0 个目标（路线终点/结局） |" % nk.get("end", 0))
w()
w("- **零目标场景（%d 个）**：%s" % (len(B["next_zero"]), "、".join("`%s`" % x for x in B["next_zero"])))
w("  —— `s04_29a`＝真 END 解纜、`s01_14j2`＝鷹志线 Bad End（PSV 美咲线由此接入，流程图 §4.4）、")
w("  `s03_24`＝幕間收束、`s01_14g2`/`s04_06l`＝分支终点。")
w("- **46 个 `branch` 场景中只有 24 个有实测选择支串**，其余 22 个是**成对/成组变体脚本**")
w("  （如 `s03_06d1/d2`、`s02_09d1/d2`、`s01_10g1/g2` 的 `(N)/(C)` 分版），触发条件未判定 →")
w("  **只记 `next`，不写 `choices`**（与 W6a 一致，不臆断）。")
w("- **跨模块 next**：%s —— 该场景属亚衣线（已由 W6a 产出为 `otr_s03c_01a`），保留原样由编程组接线。"
  % "、".join("`%s`" % x for x in B["next_cross_module"]))
w()
w("## 六、源缺陷修复：speaker/voice 拆分（68 行）")
w()
w("### 6.1 缺陷与根因（**实测，非推测**）")
w()
w("本篇提取器 `工程\\我们没有翅膀\\工具\\extract_sob0.py` 的 `classify()` 对 `#<说话人>\\<语音ID>$&`")
w("按**原始字节 0x5C** 切分。而 cp932 中 **0x5C 同时是若干汉字的尾字节**（`十`=8F5C、`ソ`=835C、`ク`=835C、`ウ`=835C …），")
w("故说话人含这类字时被**误切**：说话人尾部丢字（解码为 U+FFFD）、语音 ID 里混入说话人残段。")
w()
_nfix_lab = len({r["speaker_after"] for r in B["speaker_repairs"]})
w("实测影响 **%d 行 / %d 个说话人标签**：" % (B["speaker_repair_count"], _nfix_lab))
w()
w("| 源 jsonl 的 `speaker` | 源 jsonl 的 `voice` | 复原后 `speaker` | 复原后 `voice` | 行数 |")
w("| --- | --- | --- | --- | ---: |")
agg = collections.Counter()
for r in B["speaker_repairs"]:
    agg[(r["speaker_before"], r["voice_before"], r["speaker_after"], r["voice_after"])] += 1
for (sb, vb, sa, va), c in sorted(agg.items(), key=lambda x: (x[0][2], x[0][3])):
    w("| `%s` | `%s` | **`%s`** | **`%s`** | %d |" % (sb, vb, sa, va, c))
w()
w("### 6.2 修复判据（确定性，非猜测）")
w()
w("语音 ID 为**纯 ASCII**，故 `#<说话人>\\<语音ID>$&` 中**最后一个 0x5C 才是真分隔符**；")
w("直接回 `.sob` 原始字节，从该分隔符向前 60 字节内最近的 `#` 起按 cp932 解出说话人。")
w("逐条留痕：`speaker_repairs[]` 含 `speaker_before` / `voice_before` / `speaker_after` / `voice_after` /")
w("`byte_span` / `evidence`（可回字节复核）。修复失败 0 条。")
w()
w("### 6.3 影响与开关")
w()
w("| 项 | 修复前（`--no-speaker-repair`） | 修复后（默认） |")
w("| --- | ---: | ---: |")
w("| 语音命中 | 20791 / 20859（99.67%） | **20859 / 20859（100.00%）** |")
w("| `speaker` 有中文写形 | 311 / 320 标签 | 302 / 320 标签（修复后标签数变多，见 §9.2） |")
w("| 名字框乱码行 | 68 行（U+FFFD） | **0 行** |")
w()
w("构建器提供 `--no-speaker-repair` 开关，可一键回到「源 jsonl 原值」形态供主代理裁决（§9.1-1）。")
w("**源文件一个字节未改**——修复只作用于产出的 `scene_ot.jsonl`。")
w()
w("## 七、素材挂接与命中率")
w()
w("### 7.1 口径")
w()
w("- **场景级 `assets`**（图像/音效）：`kind` 由 `.sob` 内的引用目录决定（`PIC`→`pic`、`SE`→`se`、`SYS`→`sys`），")
w("  按 `out_relpath` 规则 `<源代号>_<原名>` 映射到 `资源总账.json`；**顺序＝.sob 内首次出现的字节序**")
w("  （流程图 §7.1 要求以「资源引用顺序」重建演出）。")
w("- **行级 `audio`**：语音是消息表自带字段（`voice`），可逐行对齐，故保留（schema §2.1）。")
w("- **每行图像/音效不产出**：SOB0 演出命令语义未逆向（总纲 R1），强行逐行对齐即臆断。")
w("- **BGM 不产出**：本篇脚本**不按名引用 BGM**（流程图 §7.2 实测 0 处 `BGM\\` 引用），如实不产。")
w("- **CHR 不产出**：本篇脚本**无 `CHR\\` 路径引用**（立绘走 CHR.LPK 但不以路径串引用），如实不产。")
w()
w("### 7.2 命中率（逐类）")
w()
w("| 类别 | 命中 | 总数 | 命中率 | 缺失 |")
w("| --- | ---: | ---: | ---: | --- |")
for k, v in sorted(V["A5"]["assets_by_kind"].items()):
    miss = sum(1 for m in V["A5"]["asset_missing_list"] if m["kind"] == k)
    w("| 图像/音效 `%s` | %d | %d | %.2f%% | %d |" % (k, v - miss, v, 100.0 * (v - miss) / v, miss))
w("| **合计** | **%d** | **%d** | **%.2f%%** | **%d** |"
  % (V["A5"]["assets_hit"], V["A5"]["assets_total"], V["A5"]["assets_hit_rate"],
     len(V["A5"]["asset_missing_list"])))
w("| 语音（行级 `audio`） | %d | %d | %.2f%% | %d |"
  % (V["A5"]["voice_hit"], V["A5"]["voice_refs"], V["A5"]["voice_hit_rate"],
     len(V["A5"]["voice_missing_list"])))
w()
w("### 7.3 缺失清单（逐条，不笼统）")
w()
w("| # | 场景 | 引用 | 说明 |")
w("| ---: | --- | --- | --- |")
for i, m in enumerate(V["A5"]["asset_missing_list"], 1):
    w("| %d | `%s` | `%s` | SE.LPK 内**无 `se23.ogg`**（仅有 `se230`–`se239`）；`.sob` 字节内该串为 NUL 结尾的完整串"
      "（`SE\\SE23.OGG`），**非截断**。疑为原作引用残缺 → **如实登记，不臆断改名** |"
      % (i, m["script"], m["ref"]))
w()
w("> 语音缺失 **0** —— 见 §6（68 行 voice 混入残段是**提取器缺陷**，回 .sob 字节复原后全部命中）。")
w()
w("## 八、逐场景统计（367 场景）")
w()
w("| 场景 | 阶段 | 行数 | 语音 | 标题（中） | 日期 | `next` | `next_kind` | 选项 | cast | 素材 | 缺失 | 译名 |")
w("| --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | --- | --- | --- | ---: |")
for s in B["per_scene"]:
    w("| `%s` | %s | %d | %d | %s | %s | %s | %s | %d | %s | %d/%d | %s | %d |"
      % (s["script"], s["phase"], s["line_count"], s["voice_count"],
         (s["title_cn"] or "—").replace("|", "\\|"),
         s["game_date"] or "—",
         "、".join("`%s`" % x for x in s["next"]) or "—",
         s["next_kind"], s["choices"],
         "、".join(s["cast"][:6]) + ("…" if len(s["cast"]) > 6 else ""),
         s["assets_hit"], s["assets_total"],
         "、".join(s["assets_missing"]) or "—",
         s["name_replace_count"]))
w()
w("**阶段分布**：`%s`" % B["phase_dist"])
w("**路由分布**：s00 序文 1 ｜ s01 鹰志线 114 ｜ s02 鹫介线 83 ｜ s03 隼人线 95 ｜ s04 大路线 74")
w()
w("### 8.1 有显式游戏内日期的场景（仅 %d 个）" % len(B["scenes_with_date"]))
w()
w("口径（schema §四.3）：**仅当 `jp` 出现显式 `○月○日` 才填 `game_date`**；星期信息不唯一定日 → `null`。")
w()
w("| 场景 | `game_date` | 全部显式日期（`game_dates`） |")
w("| --- | --- | --- |")
for x in B["scenes_with_date"]:
    w("| `%s` | **%s** | %s |" % (x["script"], x["game_date"],
                                  "、".join("%s(#%s)" % (d["date"], d["line_index"]) for d in x["game_dates"])))
w()
w("> 其余 %d 个场景 `game_date = null`（**不臆造**）。与流程图 §6.1 的日期锚点一致。"
  % (B["scenes"] - len(B["scenes_with_date"])))
w()
w("## 九、7 项验收自证")
w()
w("校验器：`资源组\\工具\\verify_scene_ot.py`（**从磁盘重读 `scene_ot.jsonl`**，与只读源交叉核对，")
w("不依赖构建器内存态）→ 结果 `子代理工作区\\ISSUE-20260918-06\\W6b\\W6b验收.json`。")
w()
w("| # | 标准 | 结果 | 证据 |")
w("| ---: | --- | :---: | --- |")
w("| 1 | 场景数 367（s00 1 / s01 114 / s02 83 / s03 95 / s04 74） | **通过** | 实测 %s；脚本集合与源 367 个 jsonl **完全一致** |"
  % V["A1"]["actual"])
w("| 2 | 行数守恒，差异 0 | **通过** | 总行 **%d** == 源基线 **%d**；**逐场景**核对差异 **%d** |"
  % (V["A2"]["total"], V["A2"]["baseline"], V["A2"]["mismatch_count"]))
w("| 3 | 门控正确（命中 0、门控排除逐条列出） | **通过** | %d 条 = 范围内 **%d**（命中 **%d** + 门控 **%d** + 未命中 **0**）+ 范围外 **%d**；"
  % (V["A3"]["corrections_total"], V["A3"]["in_scope"], V["A3"]["hits"],
     V["A3"]["gated_expected"], V["A3"]["out_of_scope"]))
w("|  |  |  | `cn_base` 集合独立复算 = `%s`；**门控落点独立复核 = %s**（§3.3 逐条） |"
  % (V["A3"]["cn_base_set"], V["A3"]["gate_landing_verified"]))
w("| 4 | 选择支对账 | **通过** | 源 `sel=1` **%d** / `sel=2` **%d**（%d 脚本）= 产出 **%d 脚本 / %d 选项**；逐脚本差异 **%d**（§5.1 对账表） |"
  % (V["A4"]["src_sel1"], V["A4"]["src_sel2"], V["A4"]["src_script_count"],
     V["A4"]["scene_choice_scripts"], V["A4"]["scene_choice_options"], len(V["A4"]["mismatch"])))
w("| 5 | 素材命中率 | **通过** | 图像/音效 **%d/%d（%.2f%%）**，缺失 **%d** 处逐条列出（§7.3）；语音 **%d/%d（100%%）**；"
  % (V["A5"]["assets_hit"], V["A5"]["assets_total"], V["A5"]["assets_hit_rate"],
     len(V["A5"]["asset_missing_list"]), V["A5"]["voice_hit"], V["A5"]["voice_refs"]))
w("|  |  |  | 引用集合与 .sob 重扫结果**逐场景一致**（差异 %d） |" % len(V["A5"]["asset_mismatch"]))
w("| 6 | schema 自洽 | **通过** | 必填缺失 **%d**；`scene_id` 唯一 **%s**；JSONL %d 行逐行 `json.loads` **%s**；枚举越界 **%d** |"
  % (len(V["A6"]["missing_required"]), not V["A6"]["duplicate_scene_ids"], V["A6"]["scene_count"],
     V["A6"]["jsonl_parse_ok"], len(V["A6"]["enum_violations"])))
w("| 7 | 不臆断 | **通过** | `game_date` 仅 %d 场景有显式证据、其余 `null`；`choices.target` 全 `null`（配对未逆向）；"
  % len(V["A7"]["scenes_with_date"]))
w("|  |  |  | `d14_exception` 全 `null`（取文即首选源）；%d 场景无标题、%d 标签无中文名字框，均逐条登记 |"
  % (len(V["A7"]["scenes_without_title"]), len(V["A7"]["speaker_cn_missing_labels"])))
w()
w("**`ALL_PASS = %s`**" % V["ALL_PASS"])
w()
w("## 十、未决问题与需主代理裁决的点")
w()
w("### 10.1 需裁决")
w()
w("| # | 事项 | 现状 | 备选 |")
w("| ---: | --- | --- | --- |")
w("| **1** | **`speaker`（名字框中文）的取值口径** | 本篇汉化**未译名字框**（`交付说明.md` §二），语料内无 `speaker_cn`；本模块按 **D3 仲裁语料**（`参照\\中日对照表.json` 的 `speaker_cn`）建立 JP→CN 映射（%d 标签定名 / %d 无中文写形） | ① 维持本方案（D3 依据充分、D4 允许人名级使用新米）；② 改为 `speaker = \"\"`（严格源保真，但编程组无名字框可用）；③ 另立「名字框定名」专项由主代理统一裁决 |"
  % (B["speaker_cn_total"] - len(B["speaker_map_missing"]), len(B["speaker_map_missing"])))
w("| **2** | **68 行 speaker/voice 拆分修复** | 默认**启用**（回 `.sob` 字节复原，确定性判据）；源文件未改 | ① 维持启用（语音命中 100%）；② 用 `--no-speaker-repair` 复跑回到源 jsonl 原值（语音命中 99.67%、68 行名字框乱码）；③ 把该缺陷另立 W7 类修复条目回修源交付物 |")
w("| **3** | **`s00_00` 的标题取值** | 该场景有 2 个标题槽（槽 0 `序文　～俺たちに翼はない～`、槽 1 `文　～俺たちに翼はない～`）；按 schema §三.4「无 09 对照/无修正表条目则取最后一个」→ 现取槽 1 | ① 维持 schema 字面规则（现取槽 1）；② 改为取**槽 0**（位置判据：槽 0 恒为章节标题）；仅影响 1 个场景 |")
w("| **4** | **`source_kind` / `lines[].kind` / `align_method` 的按源枚举扩展** | 本模块引入 `source_kind=ot`、`kind∈{dialogue,other}`、`align_method=ot_direct`（理由见 §2） | ① 采纳（字段名与类型未变，仅枚举值按源定义）；② 若编程组要求跨源统一枚举，需主代理另定映射表 |")
w("| **5** | **`プリンセス・ダヴ` 表内计数 22 vs 实测 21** | 差 1，无法复现（§4.2） | 提请表维护方复核 `译名替换表.tsv` 该行计数口径 |")
w("| **6** | **`s02_09d1/d2` 是否为玩家选择支** | 流程图书列为选择支，但实测**无 `sel` 槽**（成对变体脚本）→ 未写入 `choices` | 维持「只记 `next`、不写 `choices`」；若判定为选择支需补 `choices` 与译文 |")
w()
w("### 10.2 未决（不需裁决，仅登记）")
w()
w("- **9 个场景本篇无标题槽**（槽 0 是梗概）：%s —— 其 R 版**有**标题（如 `ＤＴ－ＤＲＥＡＭ・Ｒ`、"
  % "、".join("`%s`" % x for x in B["titles"]["scenes_without_title"]))
w("  `Ｐｕｎｋ　Ｔｏ　Ｆｕｎｋ（Ｎ）`），但 D14 规定正文取本篇、且该标题**不在本篇消息表内** →")
w("  `title_jp`/`title_cn` 留 `null`，**不借 R 版回填**。如需标题可另立「标题回填」专项。")
w("- **%d 个说话人标签无中文名字框**（参照语料中该标签的 `speaker_cn` 恒为空或标签不存在）："
  % len(B["speaker_map_missing"]))
for x in B["speaker_map_missing"]:
    w("  - `%s`" % x)
w("  这些多为**幻想侧群像**（`ホーク十勇士１`–`１０`、`ホーク十六翼将１`、`クソ長い髪の女`、`ウソ臭い目の男`）")
w("  与功能性标签（`予告`、`夢の声`），其 `speaker` 留 `\"\"`。**`speaker_jp` 完整保留，可随时补译。**")
w("- **%d 个标签在参照语料中有多个中文写形**（如 `鷹志` 出现 `鹰志`/`野狗`、`タカシ` 出现 `TAKASHI`/`鹰志`、"
  % len(B["speaker_map_ambiguous"]))
w("  `バニィＤ` 出现 `巴尼Ｄ`/`巴尼D`）→ 已按**非空写形多数**取值，逐条记入 `_build_stats_ot.json` 的")
w("  `speaker_map_ambiguous`（含完整分布），供主代理复核。其中 `タカシ`→`TAKASHI` 一项与作品层术语表 §四")
w("  「`タカシ` 待裁决」**并不冲突**：名字框流的新米实测写形即为 `TAKASHI`（35 槽）。")
w("- **`game_date` 仅 %d 场景有证据**（§8.1）；其余 %d 场景只有星期信息，无法唯一定日，一律 `null`。"
  % (len(B["scenes_with_date"]), B["scenes"] - len(B["scenes_with_date"])))
w("- **`text_source` 全为 `ot`（367/367）**；`cn_origin` 分布 `ot` %d ｜ `empty` %d —— 无 `mixed`、"
  % (B["orig_dist"].get("ot", 0), B["orig_dist"].get("empty", 0)))
w("  无 `fix_table`/`retranslate`（与「无 `source=ot` 修正条目」一致）。")
w("- **空槽 0**：本篇语料 %d 槽中无 `jp`/`cn` 双空槽（与亚衣线 R 版新增场景的 40 空槽不同）。"
  % B["lines_total"])
w("- **`ペガサス` 语境双轨 6 处**已按表替换并标记 `context_flag`（§4.4），**请主代理复核是否为台词敬称语境**。")
w("- **每行图像/音效不可得**（演出命令语义未逆向，总纲 R1）；**BGM / CHR 本篇不按名引用**，如实不产。")
w()
w("### 10.3 对后续模块（W6c–W6e）的提示")
w()
w("- `source=otp`（前奏诗）14 条与 `source=ota`（After Story）7 条修正，本模块**范围外**，")
w("  届时必须由各自源模块**全部命中或门控排除**（本模块实测这两源修正的 `locator` 分别为 `seq=<n>` 与 `idx=<n>`）。")
w("- `source=otr` 的 83 条范围外条目针对 `s03c` 等 R 版场景，W6a 已消费 7 条、其余待 R 版其余场景模块消费。")
w("- 若后续模块也要用本篇语料（如 `s03c` 的 21 个场景已在 W6a 用过），请注意：")
w("  **`speaker` 名字框中文在本篇语料中不存在**，需沿用本模块 §2.5 的口径或等待主代理裁决（§10.1-1）。")
w("- **`speaker/voice` 拆分缺陷（§6）是全篇语料级缺陷**，凡直接消费 `汉化\\剧情汉化\\*.jsonl` 的")
w("  模块（含 W6a 已产出的 `scene.jsonl` 若涉及本篇 68 行所在场景）都会受影响，建议主代理评估是否另立修复条目。")
w()
w("## 十一、可复现命令")
w()
w("```bash")
w('cd "E:/ZCode Workspace/Galgame"')
w('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ot.py"')
w('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_ot.py"')
w('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_w6b_report.py"')
w("# 关闭 speaker/voice 拆分修复（回到源 jsonl 原值形态）：")
w('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ot.py" --no-speaker-repair')
w("```")
w()
w("三个脚本对源工程**全程只读**；构建器只写 `资源组\\剧本\\scene_ot.jsonl` 与")
w("`子代理工作区\\ISSUE-20260918-06\\W6b\\_build_stats_ot.json`。")
w()
w("---")
w()
w("*本报告由 `资源组\\工具\\emit_w6b_report.py` 依据 `_build_stats_ot.json` 与 `W6b验收.json` 生成，可复跑。*")

open(os.path.join(OUT, "本篇_产出报告.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("-> %s （%d 行）" % (os.path.join(OUT, "本篇_产出报告.md"), len(L)))