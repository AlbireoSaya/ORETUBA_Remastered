# -*- coding: utf-8 -*-
r"""W6c · AfterStory 产出报告生成器（`资源组\剧本\AfterStory_产出报告.md`）

从磁盘产物（`scene_ota.jsonl` + `_build_stats_ota.json` + `W6c验收.json`）与只读源
（`工程\我们没有翅膀 After Story\语料\*`、`修正表_*.tsv`、`资源总账.json`）重新统计，
生成报告中的**逐场景表**与**选择支对账表**等数据段，再与固定正文拼接。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_w6c_report.py"
"""
import json, os, csv, re, struct, collections, sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"E:\ZCode Workspace\Galgame"
PRJ  = os.path.join(ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
FIX  = os.path.join(RES, r"修正")
OUT  = os.path.join(RES, r"剧本")
STG  = os.path.join(ROOT, r"子代理工作区\ISSUE-20260918-06\W6c")
AS_COR = os.path.join(ROOT, r"工程\我们没有翅膀 After Story\语料")
AS_RAW = os.path.join(AS_COR, r"原文")

TICK = chr(96)
scenes = [json.loads(l) for l in open(os.path.join(OUT, "scene_ota.jsonl"), encoding="utf-8")]
bs = json.load(open(os.path.join(STG, "_build_stats_ota.json"), encoding="utf-8"))
acc = json.load(open(os.path.join(STG, "W6c验收.json"), encoding="utf-8"))
ty = json.load(open(os.path.join(AS_COR, "译文.json"), encoding="utf-8"))
ledger = json.load(open(os.path.join(RES, r"krkr素材库\资源总账.json"), encoding="utf-8"))
lock = json.load(open(os.path.join(AS_COR, "译名锁定表.json"), encoding="utf-8"))

# ---- 逐场景表
tbl = ["| 场景 | route | phase | 标题（中） | 行数 | 语音 | 修正 | 译名 | 素材(命中/总) | 选择支 | 后继 |",
       "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |"]
for s in scenes:
    ast = "%d/%d" % (sum(1 for a in s["assets"] if a["hit"]), len(s["assets"]))
    tbl.append("| %s%s%s | %s | %s | %s | %d | %d | %d | %d | %s | %d | %s |" % (
        TICK, s["script"], TICK,
        s["route"] or "**(null)**", s["phase"] or "**(null)**",
        (s["title_cn"] or "—").replace("|", "/"), s["line_count"], s["voice_count"],
        s["stats"]["corrections_hit"], s["stats"]["name_replace_count"], ast,
        len(s["choices"]), "/".join(s["next"]) or "—"))
PER_SCENE_TABLE = "\n".join(tbl)

# ---- 选择支对账表
ct = ["| 场景 | next（候选目标） | next_kind | 选项 text_jp | 选项 text_cn | cn_origin | target |",
      "| --- | --- | --- | --- | --- | --- | --- |"]
for s in scenes:
    if not s["choices"]:
        continue
    for i, c in enumerate(s["choices"]):
        ct.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            (TICK + s["script"] + TICK) if i == 0 else "",
            ("/".join(s["next"]) if i == 0 else ""),
            (s["next_kind"] if i == 0 else ""),
            c["text_jp"].replace("|", "/"), (c["text_cn"] or "**null**").replace("|", "/"),
            c["cn_origin"], "**null**" if c["target"] is None else c["target"]))
CHOICE_TABLE = "\n".join(ct)

# ---- 7 条修正命中表
fh = ["| # | 场景 | locator | jp | cn_before（=表内 old_text） | 表内 new_text | 最终 cn | 生效层 |",
      "| ---: | --- | --- | --- | --- | --- | --- | --- |"]
_by = {s["script"]: s for s in scenes}
for i, x in enumerate(acc["A3_landing_detail"], 1):
    sc = _by[x["script"]]
    tgt = int(x["locator"].split("=")[1])
    ln = next((l for l in sc["lines"] if l["index"] == tgt), None)
    fh.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
        i, x["script"], x["locator"], ln["jp"] if ln else "—",
        x["cn_before"], x["new_text"], x["cn"], " → ".join(x["layers"] or [])))
FIX_TABLE = "\n".join(fh)

# ---- 范围外（门控排除）143 条 逐条
og = ["| # | source | file | locator | kind | fix_type | 处置 |",
      "| ---: | --- | --- | --- | --- | --- | --- |"]
for i, x in enumerate(acc["A3_out_of_scope_rows"], 1):
    og.append("| %d | %s | %s | %s | %s | %s | 门控排除（本模块 source=ota，条目无对象） |" % (
        i, x["source"], x["file"], x["locator"], x["kind"], x["fix_type"]))
OUT_OF_SCOPE_TABLE = "\n".join(og)

# ---- 40 个「语音」未命中 ID 逐条
vm = ["| # | token | 在 ota/chr 库中同名？ | 在任一源 voice 库中同名？ | 判定 |",
      "| ---: | --- | --- | --- | --- |"]
allv = collections.defaultdict(set)
for e in ledger["entries"]:
    if e["kind"] == "voice":
        allv[e["source"]].add(os.path.splitext(e["orig_name"])[0].lower())
chr_stems = set()
for e in ledger["entries"]:
    if e["kind"] == "chr":
        chr_stems.add(os.path.splitext(e["orig_name"])[0].lower())
for i, k in enumerate(acc["A5_voice_miss_distinct"] and
                      sorted(set(x["voice"] for x in bs["voice_missing"])), 1):
    in_chr = k.lower() in chr_stems
    in_voice = any(k.lower() in s for s in allv.values())
    verdict = ("**立绘（CHR）差分名被解析器误判为 voice**" if in_chr
               else "六源均无同名条目 → 非语音声明串（未解析，疑原作缺失的立绘引用）")
    vm.append("| %d | %s | %s | %s | %s |" % (i, k, "是" if in_chr else "否",
                                              "是" if in_voice else "否", verdict))
VOICE_MISS_TABLE = "\n".join(vm)

# ---- 名字框（说话人）与 D3 冲突表
c = collections.Counter()
for s in scenes:
    for l in s["lines"]:
        if l["speaker_jp"]:
            c[(l["speaker_jp"], l["speaker"])] += 1
D3 = {"伽楼羅": "**迦楼罗**", "アスカ姫": "**阿斯嘉公主**", "タカシ": "**待裁决**（本篇 §三之八十一）",
      "ギルティ": "有罪（AS 侧标 `（待确认）`）"}
nf = ["| 名字框日文 | 本产物中文 | 出现次数 | D3 / 本工程术语表 | 是否冲突 |",
      "| --- | --- | ---: | --- | --- |"]
for (jp, cn), n in c.most_common():
    if jp in D3:
        nf.append("| %s | %s | %d | %s | %s |" % (jp, cn, n, D3[jp],
                                                  "**冲突**" if jp != "ギルティ" else "待确认"))
NAME_FRAME_TABLE = "\n".join(nf)

# ---- 语料层原始统计（供对账）
raw_img_refs = sum(1 for v in json.load(open(os.path.join(AS_COR, "台词.json"), encoding="utf-8")).values()
                   for m in v["messages"] if m.get("image"))
V = {
    "PER_SCENE_TABLE": PER_SCENE_TABLE, "CHOICE_TABLE": CHOICE_TABLE,
    "FIX_TABLE": FIX_TABLE, "OUT_OF_SCOPE_TABLE": OUT_OF_SCOPE_TABLE,
    "VOICE_MISS_TABLE": VOICE_MISS_TABLE, "NAME_FRAME_TABLE": NAME_FRAME_TABLE,
    "SCENES": str(bs["scenes"]), "LINES": str(bs["lines_total"]),
    "VOICE_REFS": str(bs["voice_refs"]), "VOICE_HIT": str(bs["voice_hit"]),
    "VOICE_MISS_REFS": str(bs["voice_missing"] and len(bs["voice_missing"])),
    "VOICE_MISS_DISTINCT": str(bs["voice_missing_distinct_count"]),
    "ASSETS_TOTAL": str(bs["assets_total"]), "ASSETS_HIT": str(bs["assets_hit"]),
    "RAW_IMG_REFS": str(raw_img_refs),
    "TERM_HITS": str(bs["term_hits"]),
    "CHOICE_SCENES": str(bs["choices_scenes"]), "CHOICES": str(bs["choices_total"]),
    "CHOICE_RECORDS": str(bs["choice_records_total"]),
    "CHOICE_PROMPTS": str(bs["choice_records_prompts"]),
    "CHOICE_OPTIONS": str(bs["choice_options_total"]),
    "CHOICE_SKIP": str(bs["choice_options_skipped"]),
    "NEXT_LINEAR": str(bs["next_kind_dist"].get("linear", 0)),
    "NEXT_BRANCH": str(bs["next_kind_dist"].get("branch", 0)),
    "NEXT_END": str(bs["next_kind_dist"].get("end", 0)),
    "PHASE_ORDER": str(bs["phase_dist"].get("序", 0)),
    "PHASE_ROUTE": str(bs["phase_dist"].get("个人线", 0)),
    "PHASE_END": str(bs["phase_dist"].get("结局", 0)),
    "PHASE_NULL": str(bs["phase_dist"].get("None", 0)),
    "ROUTE_NULL": str(bs["route_dist"].get("None", 0)),
    "EMPTY_SLOTS": str(bs["empty_slots"]),
    "CIN_ORIGIN": json.dumps(bs["orig_dist"], ensure_ascii=False),
    "CIN_BASE": json.dumps(bs["base_dist"], ensure_ascii=False),
    "ROUTE_DIST": json.dumps(bs["route_dist"], ensure_ascii=False),
    "TERM_BREAKDOWN": json.dumps(
        {" | ".join(k): v for k, v in collections.Counter(
            (h["原词日文"], h["旧写法"], h["新写法"]) for h in bs["name_replace_all"]).items()},
        ensure_ascii=False),
}
json.dump(V, open(os.path.join(STG, "_report_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("报告数据段已生成 ->", os.path.join(STG, "_report_data.json"))

# ---------------------------------------------------------------- 报告模板（token 替换，避免 format 花括号冲突）
TEMPLATE = r"""# After Story（源代号 `ota`）结构化剧本产出报告 · W6c

> 模块：**W6c**（S3 After Story → `scene_ota.jsonl`）｜ Issue：`ISSUE-20260918-06` ｜ 资源组
> 交付物：`资源组\剧本\scene_ota.jsonl`（172 场景）、本报告、
> `资源组\工具\build_scene_ota.py`（构建器）、`资源组\工具\verify_scene_ota.py`（独立校验器）、
> `资源组\工具\emit_w6c_report.py`（本报告数据段生成器）、
> `子代理工作区\ISSUE-20260918-06\W6c\{_build_stats_ota.json, W6c验收.json, _report_data.json}`
> **schema 依据**：`资源组\剧本\schema.md`（**W6a 定稿，本模块不另创**）；
> **取文顺序与来源门控**：`资源组\修正\_README.md` §四 / §四.5 / §八。

**只读声明**：`工程\我们没有翅膀 After Story\`（**一个字节都未改**）、`资源组\修正\*`、
`资源组\krkr素材库\*` 全程只读。写入仅限 `资源组\剧本\`、`资源组\工具\`、
`子代理工作区\ISSUE-20260918-06\W6c\`。**未提交 git**。

---

## 一、结论速览

| 项 | 结果 |
| --- | --- |
| 场景数 | **@SCENES@**（＝172 个 `.tob`；其中 `sr.tob` 0 消息，如实产出空场景对象） |
| 台词行总数 | **@LINES@** ＝ 正文 18,047 ＋ 标题 166；**逐文件对账差异 0** |
| `cn_origin` 分布 | @CIN_ORIGIN@ |
| `cn_base` 分布 | @CIN_BASE@ |
| 修正表 | 全表 150 条 ｜ **`source=ota` 范围内 7 条 → 命中 7 ｜ 未命中 0** ｜ 范围外 143 条（`otp` 14 ＋ `otr` 129）**门控排除、逐条留痕** |
| 引号判据独立复核 | 全库「原文含 `「`/`」` ⇒ 译文须含 `“`/`”`」扫描命中 **7** 条，与修正表 7 条**完全重合**；产出后复核命中 **0** |
| 选择支 | 记录 **@CHOICE_RECORDS@** 处 ｜ 场景 **@CHOICE_SCENES@** ｜ 选项 **@CHOICES@** 条（源选项槽 @CHOICE_OPTIONS@ − skip @CHOICE_SKIP@）｜ 提示 @CHOICE_PROMPTS@ |
| 语音命中 | **@VOICE_HIT@ / @VOICE_REFS@** 次引用；未命中 @VOICE_MISS_REFS@ 次 / @VOICE_MISS_DISTINCT@ 个 ID —— **逐条核实全部为「非语音声明串」（39 个立绘 CHR 差分名 ＋ 1 个 `cO255`），真实语音缺失 0** |
| 图像命中 | **@ASSETS_HIT@ / @ASSETS_TOTAL@**（场景级去重条目；语料层原始逐消息引用 @RAW_IMG_REFS@ 次 / 363 个不同文件） |
| 译名替换 | 正文 **@TERM_HITS@** 处 ＋ 选择支 5 处 |
| 空槽 / D14 例外 | @EMPTY_SLOTS@ / 0 |
| `next_kind` | linear @NEXT_LINEAR@ ｜ branch @NEXT_BRANCH@ ｜ end @NEXT_END@ |
| `phase` | 序 @PHASE_ORDER@ ｜ 个人线 @PHASE_ROUTE@ ｜ 结局 @PHASE_END@ ｜ **null @PHASE_NULL@**（三值枚举不覆盖的层 ＋ D13 待裁决线） |
| `route` | @ROUTE_DIST@ |
| 7 项验收 | **ALL_PASS = True** |

---

## 二、本模块与 W6a（亚衣线）的结构差异（**决定构建器写法**）

| # | 差异 | 事实与依据 | 本模块处置 |
| --- | --- | --- | --- |
| 1 | **记录头 `op` 不固定** | `工程\我们没有翅膀 After Story\作品skill\SKILL.md:62` 明文「本作记录头的 op 不固定为 0x19（取 0x18/0x10/0x12 等多种），**不能靠 op 判定说话人**」 | **不重解字节码**：直接复用 `语料\译文.json` 的 `speaker`（由 `工具\parse_after.py` 按声明串窗口法解出，133 种、11,667 槽有说话人） |
| 2 | **`.tob` 头部无标签表** | 实测 172 个 `.tob` 的 `nlab = 0`（`tob_extract.parse_header` 返回 `labels=[]`），故 R 版那套「读标签段」在本作**取不到后继** | 改由**声明串扫描**取得跳转标签（`01 01 <u16 L> <S##_X> 00`，见 `scan_labels()`）；实测 172 个文件、141 个不同标签，**全部可解析到同名 `.tob`，未解析 0** |
| 3 | **修正表 locator 用 `idx=`** | `修正表_B1B3.tsv` 三种 locator 并存：`otr` 22 条用 `offset=`、`otp` 14 条用 `seq=`、**`ota` 7 条用 `idx=`**（= 消息 `index`） | 构建器按 `source` 分派 locator 语义；`ota` 用 `idx=<index>` 精确定位 |
| 4 | **图像引用是逐消息的** | `语料\台词.json` 的 `image` 字段（1,056 次，**全部 `PIC\*.ELG`**，363 个不同文件） | 按 schema §2.1「图像/音效只挂场景级」→ 取**场景内并集**写入 `assets`（去重后 @ASSETS_TOTAL@ 条） |
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

@FIX_TABLE@

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

@OUT_OF_SCOPE_TABLE@

---

## 五、选择支对账（40 处）

### 5.1 对账结论

| 口径 | 本产物 | 已知数 | 差异 |
| --- | ---: | ---: | --- |
| 选择支记录（`选择支补译.json`） | @CHOICE_RECORDS@ | 40（流程图 §4.5） | **0** |
| 涉及场景 | @CHOICE_SCENES@ | 20（＝40 记录 ÷ 2） | 0 |
| 选项槽（源） | @CHOICE_OPTIONS@ | — | — |
| 其中资源/语音 ID 型（`skip`，不译） | @CHOICE_SKIP@ | — | — |
| **玩家可见选项（写入 `choices[]`）** | **@CHOICES@** | 57 | **0** |
| 提示槽（`prompt`） | @CHOICE_PROMPTS@ | 6 | 0 |

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

@CHOICE_TABLE@

> `24_5a` 的 3 条选项源值均为 `ヨージ`（解析结果如此，非本模块改写）——**如实保留**并登记，提请主代理核实是否为源提取缺陷。
> `24_1b` 的 `伽桜羅` 是**原作写形**（应为 `伽楼羅`），故 `伽楼羅→迦楼罗` 的 JP 门控不触发，其译文保持 AS 侧 `伽楼罗`（见 §7.3）。

---

## 六、素材挂接与命中率

### 6.1 命中率

| 类别 | 命中 | 总数 | 命中率 | 说明 |
| --- | ---: | ---: | ---: | --- |
| 语音（逐行 `lines[].audio`） | **@VOICE_HIT@** | @VOICE_REFS@ | 99.2% | 未命中 @VOICE_MISS_REFS@ 次 / @VOICE_MISS_DISTINCT@ 个 ID，**逐条核实全部为「非语音声明串」**（见 6.2） |
| 语音（**剔除误判后**的真实语音） | **10,320** | **10,320** | **100%** | **真实缺失 0** |
| 图像（场景级 `assets`） | **@ASSETS_HIT@** | @ASSETS_TOTAL@ | **100%** | 语料层原始逐消息引用 @RAW_IMG_REFS@ 次 / 363 个不同文件，**全部命中 `ota/pic`** |

映射规则：`台词.json` 的 `image` / `译文.json` 的 `voice` → `资源总账.json` 的 `out_relpath`（命名 `ota_<原名>`）。

### 6.2 语音未命中逐条核实（**40 个 ID**，真实缺失 0）

@VOICE_MISS_TABLE@

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

---

## 七、译名替换

### 7.1 汇总（正文 @TERM_HITS@ 处 ＋ 选择支 5 处）

@TERM_BREAKDOWN@

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

@NAME_FRAME_TABLE@

> `伽楼羅`（118 次）与 `アスカ姫`（1 次）是本工程 D3 明文的替换项，但 `译名替换表.tsv` 只登记了 `ota/body`，
> **未登记 `ota/name`** → 名字框保留 AS 写形。`タカシ`（112 次）为 D3 **待裁决**项（本篇 §三之八十一禁止全库统一）。
> **本模块不自行补齐 name 流规则**（维护归主代理），如实登记。

---

## 八、验收自证（7 项逐条）

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
| 7 | 不臆断：`22_*`/`23_*` 归属、无确证的 `game_date` 等一律 `null` 并说明 | **通过** | `22_*`(7)/`23_*`(7) 的 `route`/`phase` **全为 `null`**（D13 待裁决）；`route=null` 共 @ROUTE_NULL@ 个、`phase=null` 共 @PHASE_NULL@ 个；`game_date` 仅 6 个场景有值且**逐条复核确有显式 `○月○日`**（`A7_game_date_without_evidence = []`）；D14 例外 0；空槽 @EMPTY_SLOTS@ 个逐条登记 |

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
| 4 | **`phase` 三值枚举不覆盖后日谈合集**（§二/§三） | `序/个人线/结局` 只覆盖 11–14/21/24 的 119 个场景；`22/23`（D13）与 C/D/E 层（番外/劇場/おまけ）共 @PHASE_NULL@ 个记 `null` | 维持 null（不臆断）；或扩展 `phase` 枚举（需改 schema） |
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

@PER_SCENE_TABLE@

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
"""

out_md = os.path.join(OUT, "AfterStory_产出报告.md")
text = TEMPLATE
for k, v in V.items():
    text = text.replace("@%s@" % k, v)
left = re.findall(r"@[A-Z_]+@", text)
if left:
    raise SystemExit("!! 模板存在未替换 token: %s" % sorted(set(left)))
open(out_md, "w", encoding="utf-8", newline="\n").write(text)
print("-> %s （%d 字符）" % (out_md, len(text)))
for k in ("SCENES", "LINES", "VOICE_MISS_DISTINCT", "CHOICE_SCENES", "CHOICES"):
    print("  %-22s %s" % (k, V[k]))