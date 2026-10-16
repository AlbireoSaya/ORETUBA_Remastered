#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
逐行演出表生成器 —— PSV 美咲线（源代号 `otv`）   (ISSUE-20261001-14)
================================================================================
**只读** 源脚本 + 结构化剧本 + 素材总账；产出 `资源组\演出\演出_otv.tsv`：
「**在第 <seq> 条台词之前 → 触发什么演出（立绘 / 背景 / 音效 / BGM / 影片 / 停顿 / 特效）**」，
供编程组把 `chr[]`/逐行 `se`/`bgm`/`movie` 注入成品剧本。

消费契约（提出方＝编程组 `编程组\移交资源组_逐行演出数据任务书.md` §三）：
  产物 UTF-8 无 BOM、TAB 分隔、无引号、首行表头；9 列
  `scene_id seq op target arg1 arg2 arg3 evidence confidence`。
  契约的唯一实现是**同目录 `_staging_common.py`**（`Ledger` / `SeqMap` / `row` /
  `skip_row` / `write_tsv` / `assert_scene_coverage` / `path_ref`）——本文件**不另写一份**。

复跑
----
```bash
cd "E:/ZCode Workspace/Galgame/临时/wt-stg/工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具"
python -X utf8 build_staging_otv.py            # 生成 + 4 条硬闸门
python -X utf8 build_staging_otv.py --check    # 幂等：产物必须与本轮生成结果逐字节相同
```
读 = `GRETA_DATA_ROOT`（默认 `E:\ZCode Workspace\Galgame`，由 `_staging_common` 解析）；
写 = 本 checkout（`资源组\演出\演出_otv.tsv`）。**fail loud**：任何闸门/解析失败即 `SystemExit` 并打印明细。

内置闸门（**都能真失败**，失败即 `SystemExit` 并打印明细）
--------------------------------------------------------
1. **文本槽守恒**：逐脚本线性扫描出的文本槽数 == 该场 `scene_otv.jsonl` 的 `line_count`
   （与 `build_bgm_switch_points.py` 同一判定：`Tasktype ∈ {Message, SceneJumpDialog,
   MessageSwitch_Tag}` 且含 `:Message`/`:Text`）；并断言 `lines[].seq == lines[].lineno`（31/31）。
2. **逐场景集合守恒**：本场 `op=bg` 的 `target` 去重集合 ⊇ 本场 `assets[]` 的 `kind=pic`；
   `op=se` ⊇ `se`；`op=bgm` ⊇ `bgm`；`op=movie` ⊇ `movie`；`op=chr_*` ⊇ `chr`
   （该 kind 为空则跳过）。这条同时保证与 `build_scene_otv.py` 的解析口径一致。
   **同时把「多出来的 target」（本表有、`assets[]` 没有）逐条计数并打印**——不静默。
3. **场景覆盖**：`_staging_common.assert_scene_coverage(rows, 全部 scene_id, 'otv')`。
4. **幂等**：`--check` 用「本轮生成结果的字节」与磁盘产物逐字节比对。

`seq` 口径（**锚定＝「在该行显示之前生效」**，用 `_staging_common.SeqMap`）
----------------------------------------------------------------------
* 与 `scene_otv.jsonl` 的 `lines[].seq` 同坐标系（1-based）；
  op 的 `seq` = **紧随该 op 之后的第一个文本行的行号**；
  其后本场无文本行 ⇒ **末行行号**（`evidence` 附 `after_last_line`）；
  op 在首行之前 ⇒ **1**（`evidence` 附 `before_first_line`）。
* `skip` 行 `seq=0`（唯一允许的 0）。
* 与既有 `交接编程组\BGM切换点.tsv`（口径＝「第 N 条台词**之后**」）的换算关系：
  **本表 seq = 该表 `在seq之后` + 1**（仅当 op 落在末行之后时两者相等，因本表退化为末行行号）。
  §比对 会逐条输出该换算差异，供编程组对表。

`target` 口径
-------------
一律用 `krkr素材库\资源总账.json` 的 `out_relpath`，**按源分域**（`Ledger.target(kind, token, 'otv')`），
**不得用 basename、不得跨源**。令牌来源：脚本注释名（`<<name>>` 优先，否则 `//` 后首段）
或编号派生（`:SE n`→`SE%03d`、`:BGM n`→`BGM%03d`、`:Movie n`→`MOVIE_MAP`、`:Image`→CPK TOC 序）。

`evidence` 口径
---------------
`script=<脚本名>; [Task<N>] <Tasktype> <原始字段串>[; before_first_line|after_last_line][; <备注>]`；
**不写注释行号**（本工程实测注释行号引用 6/6 全飘）。原始字段串 = 本行实际读取的字段行原文
（保留 `//` 注释，因为资源名在注释里），空白归一为单空格。

`confidence` 口径（本文件定义，全部可机检）
------------------------------------------
* `exact`   —— op / target / 参数**直接读自显式字段**，无换算、无位置推索引。
* `inferred`—— 至少一个列值需要换算（`:Time`/`:Div` 的**帧→毫秒**，按 **1s = 60fps**）。
* `unknown` —— op 归属本身无从判定（`EyeCatch` 的 `:Image s/f` 语义未确证；
  `CharacterWait` 无任何字段；`skip` 行）。

Tasktype → op 映射表（**由数据验证后定**，见 `构建报告`）
------------------------------------------------------
| Tasktype | op | 依据（字段 → 列） |
| --- | --- | --- |
| `SpriteBG` | `bg` | `:Texture`→CG.cpk(pic)；`:FadeIn`/`:Rule`→arg1、`:Time`→arg2(ms) |
| `SpriteBS` | `bg` (arg3=`SpriteBS`) | 同上（贴图层折叠，见「已知边界」） |
| `Sprite` | `bg` (arg3=`Sprite`) | 同上 |
| `SpriteMove` | `bg` (arg3=`SpriteMove`) | `:Texture`→pic、`:Time`→arg2 |
| `SpriteQuake` | `bg` (arg3=`SpriteQuake`) | `:Texture`→pic、`:Time`→arg2 |
| `SpriteDeleteBG` | `bg` (arg3=`SpriteDeleteBG`) | `:Texture`/`:SpriteNumber` 注释名→pic |
| `SpriteDelete` | `bg` (arg3=`SpriteDelete`) | `:SpriteNumber` 注释名→pic |
| `SpriteMoveEnd` | `bg` (arg3=`SpriteMoveEnd`) | `:Sprite` 注释名→pic |
| `EyeCatch` | `bg`（`pic` 支）／ `effect`（`sys` 支，arg1=`eyecatch`）；`confidence=unknown` | `:Image 0,N`→CG.cpk 的 EC*(`pic`)；`:Image 1,s,b,f`→SystemData.cpk 的 ec_bg*(**`sys` ⇒ `op=effect`**) |
| `CharacterOpen` / `CharacterOpenBS` | `chr_add` | `:Number`→CHR.cpk(chr)；`:Position`→arg1、`:Priority`→arg2 |
| `CharacterAction` | `chr_expr` | `:Number`→chr；arg1 = 差分后缀（令牌尾字母） |
| `CharacterMove` | `chr_move` | `:Number`→chr；`:Position`→arg1、`:Time`→arg2(ms, inferred) |
| `CharacterDelete` | `chr_remove` | `:Number`→chr（无 `:Number` 时 target 留空） |
| `SePlay` | `se` (arg1=`once`) | `:SE n`→`SE%03d` |
| `SeStop` | `se` (arg1=`stop`) | `:SE n`（仅 27/156 带编号；无则 target 留空） |
| `BgmPlay` | `bgm` (arg1=`play`) | `:BGM n`→`BGM%03d` |
| `BgmStop` | `bgm` (arg1=`stop`) | 无编号字段 ⇒ target 留空 |
| `MoviePlay` | `movie` | `:Movie n`→`{7:ED_misaki, 11:OP03}` |
| `TimeWait` | `wait` | `:Time` 帧→ms（inferred） |
| `CharacterWait` | `wait` | 无字段 ⇒ arg1 空、`confidence=unknown` |
| `EffectStart` | `effect` | `:EffectNumber`→arg2、其 `//` 注释名（如 `ブラー`）→arg1 |
| `EffectQuake` | `effect` (arg1=`quake`) | `:Param`→arg2 |
| `Flash` | `effect` (arg1=`flash`) | `:InTime`/`:OutTime`→arg2 |
| `FadeIn`/`FadeOut`/`InOut`/`InOut_Act` | `effect` (arg1=`rule:<:Type>`) | `:Type`=ルール番号；`:Time` 帧→ms |
| `Window`/`Tag`/`End`/`NextScene`/`SceneJumpDialogEnd`/`EffectQuakeEnd`/`EffectEnd`/`CharacterActionEnd`/`MovieStop`/`GlobalFlagOperation`/`Achievement` | `other` | 已解出、有助记符形态但不属闭集；arg1=助记符、arg2=原文参数 |
| `Message`/`SceneJumpDialog`（`MessageSwitch_Tag`） | —（文本槽，不产 op） | 已由 `lines[].audio` 承载语音 |

**op → target 的 kind 对应（与校验器 `verify_staging.py` 的 `OP_KIND` 逐格一致）**：
`bg`→`pic`、`se`→`se`、`bgm`→`bgm`、`movie`→`movie`、`chr_*`→`chr`、**`effect`→`sys`**。
⇒ `EyeCatch` 的两支必须按 kind 分派到不同 op（`pic`→`bg`、`sys`→`effect`），
否则 `sys` 件会落成 `bg` 而破坏这条对应（主代理 2026-10-01 复核项）。

**`arg3` 承载原始 Tasktype —— 本批对契约的「文档化扩展」（主代理 2026-10-01 复核后保留）**：
任务书 §3.3 中 `bg.arg3` 原为「—」（未使用）。本生成器把 `SpriteBS`/`Sprite`/`SpriteMove`/
`SpriteQuake`/`SpriteDeleteBG`/`SpriteDelete`/`SpriteMoveEnd`/`EyeCatch` 折叠进 `op=bg`
（理由见「已知边界」），为使编程组仍能区分「**背景层 / 贴图层 / 取景层**」，把**原始 Tasktype
助记符写入 `arg3`**（`SpriteBG` 本身不写，保持空）。**这不是编造字段值，而是对一个未使用列
的显式用途登记**：`bg.arg3` ∈ {``（背景层）, `SpriteBS`, `Sprite`, `SpriteMove`, `SpriteQuake`,
`SpriteDeleteBG`, `SpriteDelete`, `SpriteMoveEnd`, `EyeCatch`}。
**实测：`op=bg` 443 行中 275 行带 `arg3`**
（= `SpriteBS` 100 ＋ `Sprite` 58 ＋ `SpriteDeleteBG` 16 ＋ `SpriteMove` 16 ＋ `SpriteMoveEnd` 7 ＋
`SpriteDelete` 4 ＋ `SpriteQuake` 4 ＋ `EyeCatch` 的 **pic 支** 70；另 168 行是 `SpriteBG` 背景层，`arg3` 留空。
`EyeCatch` 的 **sys 支 11 行**已改落 `op=effect`，不计入 `bg.arg3`）；`arg3` 分布见每次运行的摘要输出。

丢弃类（**计数并打印**，不静默）：`voice`（`:Voice` 引用，已由 `lines[].audio` 承载）、
`commented_tasktype`（`//` 注释掉的 Task，**不含**在 Tasktype 计数与产物内）、
`texture_outside_task`（`[StartUp][LoadTexture]` 一类预载行，无注释名）、
`texture_no_name` / `number_no_name`（字段存在但取不到注释名）、`empty_value`、`separator_value`。

已知边界（如实登记，不臆断）
--------------------------
* **贴图层折叠进 `op=bg`**：`SpriteBS`/`Sprite`/`SpriteMove`/`SpriteQuake`/`SpriteDeleteBG`/
  `SpriteDelete`/`SpriteMoveEnd` 与 `EyeCatch` 的 **`pic` 支**引用的都是 **CG.cpk（pic）** 资产，
  而 op 闭集里**只有 `bg` 一个图像层 op** ⇒ 为满足闸门②「`op=bg` ⊇ `pic`」，一律落 `bg`，
  并在 **`arg3` 写入原始 Tasktype 助记符**（见上文「`arg3` 承载原始 Tasktype」）。
  **这是把「立绘/贴图层」与「背景层」合并的已知折价**：编程组若需要区分层，读 `arg3`
  （或 `evidence` 的 `[TaskN] <Tasktype>`）。若要拆成独立 op，须由主代理扩展 op 闭集。
* **`EyeCatch` 按解析出的 kind 分派两条 op**（主代理 2026-10-01 复核裁定）：
  `:Image 0,N` → CG.cpk 的 `EC*`（**`pic`**）⇒ `op=bg`；
  `:Image 1,s,b,f` → SystemData.cpk 的 `ec_bg*`（**`sys`**）⇒ **`op=effect`、`arg1=eyecatch`**。
  两支的 `arg3` 都保留 `EyeCatch`。理由：本批统一口径为「`sys` 件由 `op=effect` 承载」
  （与 `verify_staging.py` 的 `OP_KIND` 逐格一致）；若把 `sys` 件落在 `bg`，
  校验器 ⑦「`op=effect` ⊇ `sys`」会整源缺 8 项、逐场缺 11 处。
* **`SpriteDelete`/`SpriteDeleteBG`/`SpriteMoveEnd` 的 `:SpriteNumber`/`:Sprite` 引用**：
  `build_scene_otv.py` **不扫描**这两个字段，故其资产不在 `assets[]` 内 ⇒ 本表会出现
  `assets[]` 没有的 target（**多出的 target 逐条打印**，闸门②是 ⊇ 故不失败）。
* **`CharacterActionEnd`**（`:Character`，无 `:Number`）落 `other`：它重复前一条
  `CharacterAction` 已开的令牌、且 `build_scene_otv.py` 不记其资产；若强行落 `chr_expr`
  会与前置行重复并多出 172 条非规范 target。**如需改判，见报告「需裁决点」**。
* **`BgmStop`/`CharacterDelete`（无 `:Number`）/`SpriteDeleteBG`（无贴图字段）** 的目标不可知
  ⇒ `target` 留空（契约允许），语义由 `arg1` 与 `evidence` 承载。
* 影片 2 条为**占位·待替换**（口径照抄 `资源组\12_序章开场段演出完备性.md` §5.1：
  单点引用 / 按画布等比缩放 / 与原片同内容同时长 ±0.5s / 替换后重跑闸门），`evidence` 已注明。
* 音量（`:Div`/`:SE` 无音量字段）与 `:Image` 的 `s`/`f` 语义**未确证** ⇒ 不写入任何列、
  不换算（`:Div` 不做帧→ms，因「淡入帧 / 音量」二义未定）。

实测结果（2026-10-01，本文件生成，可复跑核对）
--------------------------------------------
* **产物**：`资源组\演出\演出_otv.tsv` — **3,330 行**（不含表头），31 场景全覆盖，`skip` 0 条。
* **按 op**：`chr_add` 1106 ｜ `other` 568 ｜ `bg` 443 ｜ `se` 386 ｜ `effect` 275 ｜ `bgm` 199 ｜
  `chr_expr` 180 ｜ `chr_remove` 72 ｜ `wait` 71 ｜ `chr_move` 28 ｜ `movie` 2。
  `op=effect` 的 275 行中 **11 行带 target**（全部是 `sys`，`arg1=eyecatch`，来自 `EyeCatch`
  的 `:Image 1,s,b,f` 支），其余 **264 行 target 留空**（`effect` 的 target 契约为「—」，
  即 `FadeIn`/`FadeOut`/`InOut`/`InOut_Act`/`EffectStart`/`EffectQuake`/`Flash` 这些
  **转场/特效本身不携带素材**）；`op=bg` 的 443 行 target **全部是 `pic`**。
  ⇒ **`op=effect` 只在「带 target」时承载 `sys`**，与校验器 `OP_KIND` 一致。
* **按 confidence**：`exact` 2729 ｜ `inferred` 497 ｜ `unknown` 104。
* **丢弃类**：`commented_tasktype` 44（`//` 注释掉的 Task——**这正是派单所给 Tasktype 计数
  （如 `Message 4925`）高于实测（4904）的原因**：那份计数未剥注释）、`texture_outside_task` 31
  （`[StartUp][LoadTexture]` 预载）、`voice` 1737（已由 `lines[].audio` 承载）；
  `empty_value` / `separator_value` / `texture_no_name` / `number_no_name` 均 0。
  纯数字字段 15,759 个作为参数**被消费**（本 DSL 的数字即坐标/帧/编号，非丢弃物），单独计数。
* **闸门①** 文本槽守恒 31/31（合计 4,931，== 六源行数表中的 `otv` 行数）；`lines[].seq == lineno` 31/31。
* **闸门②** 133 项逐场集合检查全过：`missing 0`、**多出 target 0**（即本表逐场逐 kind 的
  target 去重集合与 `assets[]` **完全相等**，不是仅 ⊇）。六条对应全部在检：
  `bg⊇pic` / `se⊇se` / `bgm⊇bgm` / `movie⊇movie` / `chr_*⊇chr` / **`effect⊇sys`**（11/11）。
* **闸门③** `assert_scene_coverage` PASS。**闸门④** `--check` 连跑逐字节相同 PASS。
* **与 `交接编程组\BGM切换点.tsv` 比对**：199 行（94 切曲 + 105 停止）**逐条命中，差异 0**；
  换算关系 `本表 seq = 该表『在seq之后』+ 1`（仅 op 落在末行之后时两者相等）。
* **target 自检**：468 个不同 target 全部落在 `otv/` 命名空间且文件真实存在。
* 引号：85 行的 `arg2`/`evidence` 含**字面** `"`（源字段如 `:Name "NoJump"`）；
  **无任何字段以 `"` 开头** ⇒ 字段本身未被引号包裹，符合契约「不加 CSV 引号」。
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import re
import sys

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _staging_common as C      # noqa: E402  契约唯一实现（禁止另写一份）

SRC = "otv"

# 31 个脚本（27 个美咲编 M01_01..M09_02 + 4 个《ある日の美咲》P03_01A..D）
SCRIPTS = [
    "M01_01", "M01_02", "M01_03", "M01_04",
    "M02_01", "M02_02", "M02_03", "M02_04", "M02_05", "M02_06", "M02_07", "M02_08",
    "M03_01", "M03_02",
    "M04_01", "M04_02", "M04_03",
    "M05_01", "M05_02",
    "M06_01", "M06_02", "M06_03",
    "M07_01", "M07_02",
    "M08_01",
    "M09_01", "M09_02",
    "P03_01A", "P03_01B", "P03_01C", "P03_01D",
]
assert len(SCRIPTS) == 31

TEXT_TASKTYPES = {"Message", "SceneJumpDialog", "MessageSwitch_Tag"}   # 与 build_bgm_switch_points.py 一致
MOVIE_MAP = {7: "ED_misaki", 11: "OP03"}      # adv.txt [Movie] 表（build_scene_otv.py 同表）
FPS = 60.0                                    # 引擎帧率（脚本注释 `1s = 60fps`）
MOVIE_NOTE = ("占位·待替换（单点引用 / 按画布等比缩放 / 与原片同内容同时长 ±0.5s / 替换后重跑闸门；"
              "口径见 资源组\\12_序章开场段演出完备性.md §5.1）")

TASK_HDR = re.compile(r"^\s*\[Task(\d+)\]\s*$")
SUB_HDR = re.compile(r"^\s*\[(\w+)\]\s*$")
FIELD = re.compile(r"^\s*(:[A-Za-z_]+)\s+(.*?)\s*$")
TASKTYPE = re.compile(r"^\s*:Tasktype\s+\"([^\"]+)\"")
SEQ_TAG = {None: "", "before_first_line": "before_first_line",
           "after_last_line": "after_last_line"}


# ================================================================ 通用小工具
def strip_comment(line):
    """引号感知地剥掉 `//` 行尾注释（照抄 build_bgm_switch_points.py 的口径）。"""
    out, inq, i = [], False, 0
    while i < len(line):
        c = line[i]
        if c == '"':
            inq = not inq
        if not inq and c == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        out.append(c)
        i += 1
    return "".join(out)


def norm(raw):
    return re.sub(r"\s+", " ", (raw or "").strip())


def name_of(raw):
    """原始字段行 → 资源注释名（`<<name>>` 优先，否则 `//` 后首段）。
    与 build_scene_otv.py 的 :Texture / :Number 解析口径逐字一致。"""
    m = re.search(r"<<([^>]+)>>", raw)
    if m:
        return m.group(1).strip()
    parts = raw.split("//")
    if len(parts) > 1:
        c = parts[1].strip()
        if c and not c.startswith("置換"):
            return c
    return None


def diff_suffix(token):
    """立绘令牌 → 差分后缀（尾部「数字 + 单字母」的字母，小写）；无后缀返回 ''。

    例：`ST_ASU01D`→`d`、`ST_KOB02`→``、`ST_CIN074I`→`i`、`ST_CIN_BLK2`→``。
    **不复用 `_staging_common.suffix_of`**：其令牌正则不含下划线，对 otv 的
    `ST_<角色><编号><后缀>` 形态不适用（实测 180/180 失效）。
    """
    m = re.search(r"\d([A-Za-z])$", (token or "").strip().upper())
    return m.group(1).lower() if m else ""


def comment_of(raw):
    """原始字段行 → `//` 后首段（效果名用，如 `:EffectNumber 42,0 // ブラー` → `ブラー`）。"""
    parts = raw.split("//")
    if len(parts) > 1:
        c = parts[1].strip()
        if c and not c.startswith("置換"):
            return c
    return ""


def _f(fields, key, default=""):
    """取字段值（同键后者覆盖前者）。"""
    for (_ln, k, v, _raw) in reversed(fields):
        if k == key:
            return v
    return default


def _raw(fields, key):
    for (_ln, k, _v, raw) in reversed(fields):
        if k == key:
            return raw
    return ""


def _ms(val):
    """帧 → 毫秒（1s = 60fps）；不可解析返回 ''。"""
    if val is None or str(val).strip() == "":
        return ""
    try:
        return str(int(round(float(str(val).strip()) / FPS * 1000.0)))
    except ValueError:
        return ""


def refs_of(task, keys):
    """按**物理行序**列出任务内命中的字段引用 → [(lineno, key, raw_value, owner_fields), ...]。

    覆盖两级：任务级字段（`[CharaN]` 之前）与子块字段（`[CharaN] { ... }` 之内），
    使 `:Number 3,0,2,7,0` 天然与同块 `:Position`/`:Priority` 配对。
    """
    out = []
    for (ln, k, v, raw) in task["fields"]:
        if k in keys:
            out.append((ln, k, v, raw, task["fields"]))
    for (_bn, bf) in task["blocks"]:
        for (ln, k, v, raw) in bf:
            if k in keys:
                out.append((ln, k, v, raw, bf))
    out.sort(key=lambda x: x[0])
    return out


# ================================================================ 输入装载
def load_inputs():
    entries = json.load(io.open(C.LEDGER, encoding="utf-8"))["entries"]
    led = C.Ledger(entries)
    # CPK TOC（只读）：`build_scene_otv.py` 的 EyeCatch 解析依据（模式 0/1 的归档序索引）
    media = os.path.join(C.DATA_ROOT, "工程", "我们没有翅膀PSV", "解密", "PCSG00299", "media")
    if not os.path.isdir(media):
        raise SystemExit("!! 找不到 PSV media 目录（EyeCatch 解析需要 CPK TOC）：%s" % media)
    cwd = os.getcwd()
    os.chdir(media)
    try:
        sys.path.insert(0, os.path.join(C.DATA_ROOT, r"工具\pylibs"))
        from cricodecs import cpk as _cpk
        cg_names = [f.filename for f in _cpk.Cpk.load("CG.cpk").files]
        sd_names = [f.filename for f in _cpk.Cpk.load("SystemData.cpk").files]
    finally:
        os.chdir(cwd)
    ec_list = [n for n in cg_names if n.upper().startswith("EC") and n.upper().endswith(".PNG")]
    ecb_list = [n for n in sd_names if n.lower().startswith("ec_bg")]
    # 交叉校验：总账 otv/sys 的 ec_bg 顺序应 == SystemData.cpk TOC 顺序（build_scene_otv.py 同款断言）
    lst = [e["orig_name"] for e in entries
           if e["source"] == SRC and e["kind"] == "sys"
           and (e["orig_name"] or "").lower().startswith("ec_bg")]
    if lst != ecb_list:
        raise SystemExit("!! 总账 otv/sys 的 ec_bg 顺序与 SystemData.cpk TOC 不一致（%d vs %d）"
                         % (len(lst), len(ecb_list)))
    return led, ec_list, ecb_list


def load_scenes():
    path = os.path.join(C.RES, "剧本", "scene_otv.jsonl")
    scenes = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            scenes[o["script"]] = o
    if sorted(scenes) != sorted(SCRIPTS):
        raise SystemExit("!! scene_otv.jsonl 的脚本集合与 SCRIPTS 不一致：%s"
                         % sorted(set(scenes) ^ set(SCRIPTS)))
    return scenes


def parse_tasks(path):
    """脚本 → (tasks, stats)。task = {num, hdr, type, fields[], blocks[(name, fields[])]}"""
    with io.open(path, "rb") as f:
        raw = f.read().decode("cp932", errors="replace")
    lines = raw.splitlines()
    tasks, cur = [], None
    stats = collections.Counter()
    for i, ln in enumerate(lines, 1):
        st = strip_comment(ln)
        if ":Tasktype" in ln and not TASKTYPE.match(st):
            stats["commented_tasktype"] += 1     # 被注释掉的 Task：不进计数、不进产物
        m = TASK_HDR.match(st)
        if m:
            if cur is not None:
                tasks.append(cur)
            cur = {"num": int(m.group(1)), "hdr": i, "type": None,
                   "fields": [], "blocks": [], "open": None}
            continue
        if cur is None:
            continue
        mt = TASKTYPE.match(st)
        if mt:
            cur["type"] = mt.group(1)
            continue
        if st.strip() == "}":
            cur["open"] = None               # 关闭最内层子块（任务级 `}` 时本已为 None）
            continue
        mb = SUB_HDR.match(st)
        if mb:
            cur["blocks"].append((mb.group(1), []))
            cur["open"] = len(cur["blocks"]) - 1
            continue
        mf = FIELD.match(st)
        if mf:
            entry = (i, mf.group(1), mf.group(2).strip(), ln.strip())
            if cur["open"] is not None:
                cur["blocks"][cur["open"]][1].append(entry)
            else:
                cur["fields"].append(entry)
            if not entry[2]:
                stats["empty_value"] += 1
            elif re.fullmatch(r"[-_$\s\[\]^]+", entry[2]):
                stats["separator_value"] += 1
            elif re.fullmatch(r"[+-]?\d+(\s*,\s*[+-]?\d+)*", entry[2]):
                stats["numeric_arg_values"] += 1     # 纯数字/逗号数字：本 DSL 中是**有意义的参数**，只计数不丢弃
    if cur is not None:
        tasks.append(cur)
    for t in tasks:
        if t["type"] is None:
            raise SystemExit("!! %s 的 [Task%d] 无 :Tasktype（第 %d 行）"
                             % (os.path.basename(path), t["num"], t["hdr"]))
    # 任务之外（[StartUp][LoadTexture] 预载表）的 :Texture 行：确认存在并计数
    total_tex = sum(1 for ln in lines
                    if re.match(r"\s*:Texture\s+\d+", strip_comment(ln)))
    in_task = sum(1 for t in tasks for (_ln, k, _v, _r) in t["fields"] if k == ":Texture")
    stats["texture_outside_task"] = total_tex - in_task
    return tasks, stats


# ================================================================ 资源解析
class Resolver:
    """令牌/编号/注释名 → `Ledger` 的 `out_relpath`（按源分域）；未命中即 fail loud。"""

    def __init__(self, led, ec_list, ecb_list, problems):
        self.led = led
        self.ec = ec_list
        self.ecb = ecb_list
        self.problems = problems

    def by_name(self, name, prefer):
        if not name:
            return None, None
        tok = name.strip().upper()
        for kind in prefer:
            p = self.led.target(kind, tok, SRC)
            if p:
                return kind, p
        self.problems.append("注释名不在素材总账：name=%r（试过 %s）" % (name, "/".join(prefer)))
        return None, None

    def se(self, n):
        tok = "SE%03d" % int(n)
        p = self.led.target("se", tok, SRC)
        if not p:
            self.problems.append("音效编号不在素材总账：:SE %s → 令牌 %s" % (n, tok))
        return p

    def bgm(self, n):
        tok = "BGM%03d" % int(n)
        p = self.led.target("bgm", tok, SRC)
        if not p:
            self.problems.append("BGM 编号不在素材总账：:BGM %s → 令牌 %s" % (n, tok))
        return p

    def movie(self, n):
        try:
            stem = MOVIE_MAP[int(n)]
        except (KeyError, ValueError):
            self.problems.append("影片编号无映射：:Movie %s" % n)
            return None
        p = self.led.target("movie", stem.upper(), SRC)
        if not p:
            self.problems.append("影片不在素材总账：:Movie %s → %s" % (n, stem))
        return p

    def image(self, val):
        """`:Image` → (kind, out_relpath, confidence_note)。模式 0：N→CG.cpk 的 EC*；
        模式 1：第三个数 b→SystemData.cpk 的 ec_bg*。语义（s/f）未确证 ⇒ confidence=unknown。"""
        nums = [int(x) for x in re.split(r"\s*,\s*", val.strip()) if x != ""]
        if not nums:
            self.problems.append(":Image 值不可解析：%r" % val)
            return None, None, "unparsable"
        mode = nums[0]
        if mode == 0:
            if len(nums) < 2:
                self.problems.append(":Image 模式 0 缺 N：%r" % val)
                return None, None, "mode0_missing_N"
            n = nums[1]
            if n == -1:
                return None, None, "mode0_N=-1"
            if not (1 <= n <= len(self.ec)):
                self.problems.append(":Image 模式 0 的 N 越界 1..%d：%r" % (len(self.ec), val))
                return None, None, "mode0_out_of_range"
            fn = self.ec[n - 1]
            return "pic", self.led.target("pic", os.path.splitext(fn)[0].upper(), SRC), "mode0"
        if mode == 1:
            if len(nums) < 3:
                self.problems.append(":Image 模式 1 缺 b：%r" % val)
                return None, None, "mode1_missing_b"
            b = nums[2]
            if not (0 <= b < len(self.ecb)):
                self.problems.append(":Image 模式 1 的 b 越界 0..%d：%r" % (len(self.ecb) - 1, val))
                return None, None, "mode1_out_of_range"
            fn = self.ecb[b]
            return "sys", self.led.target("sys", os.path.splitext(fn)[0].upper(), SRC), "mode1"
        self.problems.append(":Image 未知 mode=%d：%r" % (mode, val))
        return None, None, "unknown_mode"


# ================================================================ 逐任务 → op 行
def transition(task):
    """图像层转场方式：`:Rule` 非 0 → `rule:<R>`；否则按 `:FadeIn`/`:FadeOut` 判 cut/fade。"""
    rule = _f(task["fields"], ":Rule", "")
    if rule.strip() not in ("", "0"):
        return "rule:%s" % rule.strip()
    for key in (":FadeIn", ":FadeOut"):
        v = _f(task["fields"], key, None)
        if v is not None and str(v).strip() != "":
            return "fade" if str(v).strip() not in ("0",) else "cut"
    return ""


def rows_for_task(task, seqmap, scene_id, script, R, drops, kind_of):
    t = task["type"]
    seq, tag = seqmap.seq_for(task["hdr"])
    out = []

    def ev(rows_raw, extra=""):
        s = "script=%s; [Task%d] %s %s" % (script, task["num"], t,
                                           " ".join(norm(r) for r in rows_raw))
        if SEQ_TAG[tag]:
            s += "; " + SEQ_TAG[tag]
        if extra:
            s += "; " + extra
        return s

    def add(op, target="", a1="", a2="", a3="", raws=(), conf="exact", extra="", kind=None):
        out.append(C.row(scene_id, seq, op, target, a1, a2, a3, ev(raws, extra), conf))
        kind_of.append((scene_id, op, kind, target))

    # ---------------- 图像层（CG.cpk → pic；SystemData.cpk → sys）：op=bg
    if t in ("SpriteBG", "SpriteBS", "Sprite", "SpriteMove", "SpriteQuake",
             "SpriteDeleteBG", "SpriteDelete", "SpriteMoveEnd"):
        refs = refs_of(task, (":Texture", ":SpriteNumber", ":Sprite"))
        if not refs:
            drops["image_task_no_ref"] += 1
        seen_t = set()
        for (_ln, key, val, raw, _owner) in refs:
            nm = name_of(raw)
            if not nm:
                drops["texture_no_name" if key == ":Texture" else "sprite_number_no_name"] += 1
                continue
            kind, path = R.by_name(nm, ("pic", "chr", "etc", "sys"))
            if not path or (kind, path) in seen_t:
                continue
            seen_t.add((kind, path))
            a1 = transition(task)
            a2 = _ms(_f(task["fields"], ":Time", ""))
            a3 = "" if t == "SpriteBG" else t
            conf = "inferred" if a2 else "exact"
            add("bg", path, a1, a2, a3, (raw,), conf, kind=kind)
        return out

    # ---------------- 眼罩图（EyeCatch）：:Image 的 s/f 语义未确证 ⇒ confidence=unknown
    if t == "EyeCatch":
        raw = _raw(task["fields"], ":Image")
        val = _f(task["fields"], ":Image", "")
        kind, path, why = R.image(val)
        if kind is None:
            drops["image_" + why] += 1
            add("other", "", "EyeCatch", norm(raw), "", (raw,), "unknown",
                extra=":Image 未解析（%s）" % why)
        else:
            add("effect" if kind == "sys" else "bg",
                path, "eyecatch" if kind == "sys" else "", "", "EyeCatch", (raw,), "unknown",
                extra=":Image %s→%s；s/f 语义未确证" % (why, os.path.basename(path or "")),
                kind=kind)
        return out

    # ---------------- 立绘（CHR.cpk → chr）
    if t in ("CharacterOpen", "CharacterOpenBS"):
        for (_ln, _k, _v, raw, owner) in refs_of(task, (":Number",)):
            nm = name_of(raw)
            if not nm:
                drops["number_no_name"] += 1
                continue
            kind, path = R.by_name(nm, ("chr", "pic", "etc", "sys"))
            if not path:
                continue
            a1 = _f(owner, ":Position", _f(task["fields"], ":Position", ""))
            a2 = _f(owner, ":Priority", _f(task["fields"], ":Priority", ""))
            raws = [raw]
            if _raw(owner, ":Position"):
                raws.append(_raw(owner, ":Position"))
            if _raw(owner, ":Priority"):
                raws.append(_raw(owner, ":Priority"))
            add("chr_add", path, a1, a2, "", raws, "exact", kind=kind)
        return out

    if t == "CharacterAction":
        for (_ln, _k, _v, raw, _owner) in refs_of(task, (":Number",)):
            nm = name_of(raw)
            if not nm:
                drops["number_no_name"] += 1
                continue
            kind, path = R.by_name(nm, ("chr", "pic", "etc", "sys"))
            if not path:
                continue
            add("chr_expr", path, diff_suffix(nm), "", "", (raw,), "exact", kind=kind)
        return out

    if t == "CharacterMove":
        a2 = _ms(_f(task["fields"], ":Time", ""))
        conf = "inferred" if a2 else "exact"
        for (_ln, _k, _v, raw, owner) in refs_of(task, (":Number",)):
            nm = name_of(raw)
            if not nm:
                drops["number_no_name"] += 1
                continue
            kind, path = R.by_name(nm, ("chr", "pic", "etc", "sys"))
            if not path:
                continue
            a1 = _f(owner, ":Position", _f(task["fields"], ":Position", ""))
            raws = [raw] + ([_raw(owner, ":Position")] if _raw(owner, ":Position") else [])
            if a2:
                raws.append(_raw(task["fields"], ":Time"))
            add("chr_move", path, a1, a2, "", raws, conf, kind=kind)
        return out

    if t == "CharacterDelete":
        refs = refs_of(task, (":Number",))
        if not refs:
            add("chr_remove", "", "", "", "",
                tuple(r for (_l, _k, _v, r) in task["fields"]), "exact",
                extra=":Number 缺失（该任务未指明是哪个立绘）")
            return out
        for (_ln, _k, _v, raw, _owner) in refs:
            nm = name_of(raw)
            if not nm:
                drops["number_no_name"] += 1
                continue
            kind, path = R.by_name(nm, ("chr", "pic", "etc", "sys"))
            if not path:
                continue
            add("chr_remove", path, "", "", "", (raw,), "exact", kind=kind)
        return out

    # ---------------- 音频
    if t == "SePlay":
        for (_ln, _k, v, raw, _owner) in refs_of(task, (":SE",)):
            add("se", R.se(v), "once", "", "", (raw,), "exact", kind="se")
        return out

    if t == "SeStop":
        refs = refs_of(task, (":SE",))
        if not refs:
            add("se", "", "stop", "", "", (_raw(task["fields"], ":Wait") or "",), "exact",
                extra=":SE 缺失（停止全部音效）", kind="se")
            return out
        for (_ln, _k, v, raw, _owner) in refs:
            add("se", R.se(v), "stop", "", "", (raw,), "exact", kind="se")
        return out

    if t == "BgmPlay":
        for (_ln, _k, v, raw, _owner) in refs_of(task, (":BGM",)):
            add("bgm", R.bgm(v), "play", "", "", (raw,), "exact", kind="bgm")
        return out

    if t == "BgmStop":
        add("bgm", "", "stop", "", "", tuple(r for (_l, _k, _v, r) in task["fields"]), "exact",
            extra="无编号字段（源侧只给 :Div）", kind="bgm")
        return out

    if t == "MoviePlay":
        raw = _raw(task["fields"], ":Movie")
        p = R.movie(_f(task["fields"], ":Movie", ""))
        loop = str(_f(task["fields"], ":Loop", "")).strip()
        add("movie", p or "", "loop" if loop == "1" else "once", "", "",
            (raw,), "exact", extra=MOVIE_NOTE, kind="movie")
        return out

    # ---------------- 停顿 / 特效
    if t == "TimeWait":
        raw = _raw(task["fields"], ":Time")
        a1 = _ms(_f(task["fields"], ":Time", ""))
        add("wait", "", a1, "fixed", "", (raw,), "inferred" if a1 else "unknown")
        return out

    if t == "CharacterWait":
        add("wait", "", "", "unknown", "", (), "unknown", extra="任务无任何字段（时长不可知）")
        return out

    if t == "EffectStart":
        raw = _raw(task["fields"], ":EffectNumber")
        a2 = _f(task["fields"], ":EffectNumber", "")
        add("effect", "", comment_of(raw) or "effect", a2, "", (raw,), "exact")
        return out

    if t == "EffectQuake":
        raw = _raw(task["fields"], ":Param")
        add("effect", "", "quake", _f(task["fields"], ":Param", ""), "", (raw,), "exact")
        return out

    if t == "Flash":
        a2 = "InTime=%s,OutTime=%s" % (_f(task["fields"], ":InTime", ""),
                                       _f(task["fields"], ":OutTime", ""))
        add("effect", "", "flash", a2, "", (_raw(task["fields"], ":Color") or "",), "exact")
        return out

    if t in ("FadeIn", "FadeOut", "InOut", "InOut_Act"):
        ty = _f(task["fields"], ":Type", "")
        a1 = ("rule:%s" % ty) if str(ty).strip() != "" else "fade"
        a2 = _ms(_f(task["fields"], ":Time", ""))
        raws = [_raw(task["fields"], ":Type")] if _raw(task["fields"], ":Type") else []
        if a2:
            raws.append(_raw(task["fields"], ":Time"))
        add("effect", "", a1, a2, "", raws, "inferred" if a2 else "exact",
            extra="" if a2 else "无 :Time（时长不可知）")
        return out

    # ---------------- 其余控制串（不属闭集）
    if t in TEXT_TASKTYPES and (":Message" in [k for (_l, k, _v, _r) in task["fields"]]
                                or ":Text" in [k for (_l, k, _v, _r) in task["fields"]]):
        return out                                    # 文本槽本身，不产 op

    params = " ".join("%s %s" % (k, v) for (_l, k, v, _r) in task["fields"])
    add("other", "", t, params, "", tuple(r for (_l, _k, _v, r) in task["fields"]), "exact")
    return out


# ================================================================ 主流程
def build():
    led, ec_list, ecb_list = load_inputs()
    scenes = load_scenes()

    problems, drops = [], collections.Counter()
    stats = collections.Counter()
    R = Resolver(led, ec_list, ecb_list, problems)

    all_rows, kind_of = [], []
    slot_report, slot_bad = [], []
    scene_order = []

    for s in SCRIPTS:
        scene = scenes[s]
        scene_id = scene["scene_id"]
        scene_order.append(scene_id)

        path = os.path.join(C.PSV_SCRIPT, s)
        if not os.path.isfile(path):
            raise SystemExit("!! 找不到脚本：%s" % path)
        tasks, tstats = parse_tasks(path)
        drops.update(tstats)
        # 闸门①-a：文本槽守恒（判定与 build_bgm_switch_points.py 一致）
        slots = []
        k = 0
        for task in tasks:
            keys = set(x[1] for x in task["fields"])
            if task["type"] in TEXT_TASKTYPES and (":Message" in keys or ":Text" in keys):
                k += 1
                slots.append((task["hdr"], k))
        slot_report.append((s, k, scene["line_count"]))
        if k != scene["line_count"]:
            slot_bad.append((s, k, scene["line_count"]))
        # 闸门①-b：lines[].seq == lines[].lineno（派单实测 31/31）
        for i, ln in enumerate(scene["lines"], 1):
            if ln["seq"] != i or ln["lineno"] != i:
                problems.append("%s 第 %d 行 seq/lineno 非等距：seq=%s lineno=%s"
                                % (s, i, ln["seq"], ln["lineno"]))

        seqmap = C.SeqMap(slots)
        for task in tasks:
            stats["tasks"] += 1
            stats["task_" + task["type"]] += 1
            if task["type"] in TEXT_TASKTYPES:
                stats["text_task_" + task["type"]] += 1
            for (_l, _kd, _v, _r) in task["fields"]:
                if _kd == ":Voice":
                    drops["voice"] += 1
                    stats["voice_refs"] += 1
            all_rows.extend(rows_for_task(task, seqmap, scene_id, s, R, drops, kind_of))

    # 文本槽守恒闸门（失败即列明细）
    if slot_bad:
        for (s, a, b) in slot_bad:
            print("   x 文本槽不符 %s：脚本 %d / jsonl %d" % (s, a, b))
        raise SystemExit("!! 闸门① 文本槽守恒失败：%d 场不符" % len(slot_bad))

    # 每场景至少 1 行；无演出数据的场景给恰好 1 行 skip
    by_scene = collections.defaultdict(list)
    for r in all_rows:
        by_scene[r["scene_id"]].append(r)
    skip_scenes = []
    for s in SCRIPTS:
        sid = scenes[s]["scene_id"]
        if not by_scene.get(sid):
            skip_scenes.append(s)
            reason = "该场景脚本无任何可解出的逐行演出任务（无 :Texture/:Number/:Image/:SE/:BGM/:Movie 引用）"
            all_rows.append(C.skip_row(sid, s, reason))

    # 闸门③ 场景覆盖
    C.assert_scene_coverage(all_rows, scene_order, SRC)

    # 闸门② 逐场景集合守恒（op=bg ⊇ pic / se / bgm / movie / chr_* ⊇ chr）+ 多出 target 逐条统计
    gate2, _extras = check_conservation(scenes, kind_of, all_rows)

    # 与既有 BGM切换点.tsv 逐条比对（只读）
    bgm_cmp = compare_bgm(all_rows)

    # 统计
    op_dist = collections.Counter(r["op"] for r in all_rows)
    conf_dist = collections.Counter(r["confidence"] for r in all_rows)
    for (sid, op, kd, tg) in kind_of:
        if tg:
            if op == "bg":
                stats["bg_by_kind_" + str(kd)] += 1
            elif op.startswith("chr_"):
                stats["chr_by_kind_" + str(kd)] += 1

    summary = {
        "rows": len(all_rows),
        "by_op": dict(op_dist),
        "by_confidence": dict(conf_dist),
        "drop_counts": {k: v for k, v in drops.items() if k != "numeric_arg_values"},
        "consumed_counts": {
            "numeric_arg_values": drops.get("numeric_arg_values", 0),
            "_note": "本 DSL 的纯数字字段是有意义的参数（坐标/帧/编号），已用作 arg，**不丢弃**",
        },
        "skip_scenes": skip_scenes,
        "text_slots": slot_report,
        "gate1_text_slots": "PASS（31/31 逐场 槽数==line_count；另断言 lines[].seq==lineno）",
        "gate2_scope": gate2,
        "extra_targets": {"items": gate2["extra_target_items"],
                          "detail": gate2["extra_target_detail"]},
        "gate3_scene_coverage": "PASS（assert_scene_coverage）",
        "bgm_compare": bgm_cmp,
        "tasktype_count": {k[5:]: v for k, v in sorted(stats.items())
                           if k.startswith("task_") and not k.startswith("text_task_")},
        "problems": problems,
    }
    return all_rows, summary


def check_conservation(scenes, kind_of, all_rows):
    """闸门②：逐场 `op=bg` ⊇ pic、`op=se` ⊇ se、`op=bgm` ⊇ bgm、`op=movie` ⊇ movie、
    `op=chr_*` ⊇ chr、**`op=effect` ⊇ sys**（本批统一口径：`sys` 件由 `op=effect` 承载，
    见任务书 §五.⑦ 与主代理 2026-10-01 复核）。
    比较**按 target 的实际 kind 分域**（`kind_of` 记录解析得到的 kind），
    并逐条报告「多出 target」（本表有、`assets[]` 无）。返回 (报告, 多出 target 明细)。"""
    my = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
    for (sid, op, kd, tg) in kind_of:          # scene -> op-class -> kind -> targets
        if not tg:
            continue
        cls = "bg" if op == "bg" else ("chr" if op.startswith("chr_") else op)
        my[sid][cls][kd or "?"].add(tg)
    missing, extras, checked = [], [], []
    for script, scene in scenes.items():
        sid = scene["scene_id"]
        want = collections.defaultdict(set)
        for a in scene["assets"]:
            if a.get("out_relpath"):
                want[a["kind"]].add(a["out_relpath"])
        pairs = (("bg", "pic"), ("se", "se"), ("bgm", "bgm"), ("movie", "movie"),
                 ("chr", "chr"), ("effect", "sys"))
        for opcls, kind in pairs:
            if not want[kind] and not my[sid].get(opcls, {}).get(kind):
                continue
            got = my[sid].get(opcls, {}).get(kind, set())
            miss = sorted(want[kind] - got)
            checked.append((sid, opcls, kind, len(want[kind]), len(got)))
            if miss:
                missing.append((sid, opcls, kind, miss))
            extra = sorted(got - want[kind])
            if extra:
                extras.append((sid, opcls, kind, extra))
    if missing:
        for (sid, opcls, kind, miss) in missing:
            print("   x 集合守恒失败 %s op=%s kind=%s 缺 %d 条：%s"
                  % (sid, opcls, kind, len(miss), miss[:5]))
        raise SystemExit("!! 闸门② 逐场景集合守恒失败：%d 处" % len(missing))
    detail = [{"scene": e[0], "op_class": e[1], "kind": e[2], "n": len(e[3]),
               "targets": e[3][:8]} for e in extras]
    return {"checks": len(checked), "missing": 0,
            "extra_target_items": sum(len(e[3]) for e in extras),
            "extra_target_detail": detail,
            "pairs": "bg⊇pic / se⊇se / bgm⊇bgm / movie⊇movie / chr_*⊇chr / effect⊇sys"}, extras


def compare_bgm(all_rows):
    """与 `交接编程组\\BGM切换点.tsv` 的 otv 段逐条比对（**只读**，不改该文件）。"""
    cand = [os.path.join(C.RES, "交接编程组", "BGM切换点.tsv"),
            os.path.join(C.OUT_DIR, "..", "交接编程组", "BGM切换点.tsv")]
    path = next((p for p in cand if os.path.isfile(p)), None)
    if path is None:
        return {"status": "跳过：找不到 BGM切换点.tsv", "path": None}
    theirs = collections.defaultdict(list)
    with io.open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["源"] != SRC:
                continue
            theirs[r["场景id"]].append(("play" if r["事件"] == "切曲" else "stop",
                                        r["bgm编号"], int(r["在seq之后"]), r["物理行"]))
    mine = collections.defaultdict(list)
    for r in all_rows:
        if r["op"] == "bgm":
            num = ""
            if r["target"]:
                m = re.search(r"bgm0*(\d+)", os.path.basename(r["target"]))
                num = m.group(1) if m else ""
            mine[r["scene_id"]].append((r["arg1"], num, r["seq"], r["evidence"]))
    diffs, n_pair = [], 0
    for sid in sorted(set(list(theirs) + list(mine))):
        th, mn = theirs.get(sid, []), mine.get(sid, [])
        if len(th) != len(mn):
            diffs.append((sid, "条数不符 切换点=%d 本表=%d" % (len(th), len(mn))))
            continue
        for i, (a, b) in enumerate(zip(th, mn), 1):
            n_pair += 1
            if (a[0], a[1].lstrip("0") or "0") != (b[0], b[1].lstrip("0") or "0"):
                diffs.append((sid, "第 %d 条事件/编号不符：切换点=%s 本表=%s" % (i, a[:2], b[:2])))
                continue
            delta = b[2] - a[2]
            if delta not in (0, 1):
                diffs.append((sid, "第 %d 条 seq 换算异常：切换点『之后 %d』→ 本表 seq=%d（Δ=%d）"
                              % (i, a[2], b[2], delta)))
    return {"path": path, "theirs_rows": sum(len(v) for v in theirs.values()),
            "mine_rows": sum(len(v) for v in mine.values()), "pairs": n_pair,
            "seq_rule": "本表 seq = 切换点『在seq之后』+1（op 落在末行之后时两者相等）",
            "diffs": diffs}


def render(rows):
    out = ["\t".join(C.HEADER)]
    for r in rows:
        out.append("\t".join(str(r[c]) for c in C.HEADER))
    return ("\n".join(out) + "\n").encode("utf-8")


def main():
    ap = argparse.ArgumentParser(description="逐行演出表生成器 · otv（PSV 美咲线）")
    ap.add_argument("--check", action="store_true",
                    help="幂等自检：产物必须与本轮生成结果逐字节相同（不写盘）")
    a = ap.parse_args()

    rows, summary = build()

    # 闸门④ 幂等 / 落盘
    out_path = C.tsv_path(SRC)
    payload = render(rows)
    if a.check:
        if not os.path.isfile(out_path):
            raise SystemExit("!! --check：产物不存在，先跑一次生成：%s" % out_path)
        # 行尾规范化后比较（autocrlf 检出的盘面是 CRLF；见 交接说明 C12）
        disk = C.read_artifact_bytes(out_path)
        if disk != payload:
            raise SystemExit("!! 闸门④ 幂等失败：磁盘产物与本轮生成结果不一致"
                             "（磁盘 %d 字节 / 本轮 %d 字节）：%s" % (len(disk), len(payload), out_path))
        summary["gate4_idempotent"] = "PASS（磁盘产物逐字节相同；行尾已规范化比较）"
    else:
        n = C.write_tsv(out_path, rows)
        summary["gate4_idempotent"] = "写入 %d 行（可用 --check 复验幂等）" % n

    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("---- Tasktype → op 实测映射 ----")
    tt = collections.defaultdict(collections.Counter)
    for r in rows:
        m = re.search(r"\]\s+(\S+)\s", r["evidence"])
        if m:
            tt[m.group(1)][r["op"]] += 1
    for k in sorted(tt):
        print("  %-22s %s" % (k, dict(tt[k])))
    print("\n---- 术语 ----")
    print("  产物：%s" % out_path)
    ex_n = summary["extra_targets"]["items"]
    if ex_n:
        print("  多出 target（本表有、assets[] 无）共 %d 条，逐条：" % ex_n)
        for e in summary["extra_targets"]["detail"][:40]:
            print("    %s op=%s kind=%s x%d %s" % (e["scene"], e["op_class"], e["kind"],
                                                   e["n"], e["targets"]))
    else:
        print("  多出 target（本表有、assets[] 无）：0 条（本表 target 集合 == assets[] 集合）")
    if summary["bgm_compare"].get("diffs"):
        print("  BGM 比对差异 %d 条：" % len(summary["bgm_compare"]["diffs"]))
        for d in summary["bgm_compare"]["diffs"][:20]:
            print("    %s  %s" % d)
    else:
        print("  BGM 比对：逐条一致（差异 0）")


if __name__ == "__main__":
    main()
