# -*- coding: utf-8 -*-
r"""
`decode_sob0.py` —— Lucifen **SOB0 首版解码器**（命令节点版）

**v5（2026-10-07，ISSUE-20261007-10「软表落地」）**——把 `软表解出_说明.md`
（ISSUE-20261007-09）的结论**落进本解码器**：
  1. **命令节点判据收紧（T1）**：在旧判据 `[04][V][0C][k][03][尾REF→空串]` 之上，
     增列 **V 位 ∈ `maps[3]` 键**（引擎自带的「立即数」真值位，恒等式
     `maps[3][k] == cells[k//4]`，全库 112,621/112,621）⇒ 默认**开启**，
     可用 `--no-map3` 关掉做对照。实测剔除量（**本批复跑**）：
     · ot 语料（367 场）49741 → **49741（剔 0）**；otr 语料 2954 → **2954（剔 0）**；
     · otp 语料（59 场）9623 → **9595（剔 28）**，全在 `history/title/title2` 三个系统脚本；
     · ot **全库**（412 文件）`classic` 53769 中无背书者 **785**（≠ `_probe_soft_tables`
       的 `fake=1140`——后者是**形态级**统计，含 323 条非 classic 者与 32 条 `backed_other`；
       口径订正见 `SOB0解码\落地_说明.md` §T1）。
  2. **Fade 载体登记（T2）**：`ot` `0x19F9C` / `otp` `0x172BC`（**本批新增**）写进
     `TIME_FAMILY`；载体表见 `COMMAND_CARRIERS`。**不写"已解决"**：ot 侧仍有 **16 场反例**
     （16 个载体场无 PSV `FadeOut(time>0)`；其中 5 场无金标、11 场为金标场）。
  3. **V 定名候选（T3）**：`V_NAMING` 只登记**经逐场 precision≥0.67 且 type 非全覆盖**的结论；
     达不到阈值的一律写「未定」（本批：`0x7480→Window`、`0x1B040→InOut_Act`、
     `0x1AD18→EyeCatch/EyeCatchEnd(场级不可分)` 采纳；`0x1C8D0`（非章节名）、`0x1FAD4`
     （type 场覆盖 1.0，判别力不足）未定）。
  4. **遮罩 Rule（T4）**：命名规则 `SYS\RULE%03d.ELG`（`func_lib.sob` 串区）登记于
     `RULE_NAMING`；`PSV :Rule 数值 → 编号` 的换算**不可推**（缺 `RULE###.ELG` 件本体）。

**v5.1（2026-10-07，一审 RV-LAND 提示处理）**：
  · **契约声明**：本文件的 14 列契约与**事件产生路径**（`extract_scene` → `command_nodes`/`node_args`）
    **未被 v5 新表污染**——`COMMAND_CARRIERS` / `V_NAMING` / `RULE_NAMING` **只出现在末尾汇总打印段**
    （`main()` 的 `print`），事件路径**不引用**它们；`SLOT_FAMILY`/`TIME_FAMILY` 是 v3/v4 既有表。
  · **已知缺陷已登记并修复（两处，同一汇总段）**：
    ① 当 **PSV 金标时间线缺失/为空**时（如数据根不含 `编程组\PSV演出\时间线.tsv`），
       `_self_consistency()` 的 `tot=0` ⇒ 返回 `rate=None`，旧代码 `"%.4f" % None` 抛 `TypeError`；
       已加 `None → "-"` 保护。
    ② 同段 `rp["heads"]` 在**数据根缺语料**（`replay` 只含 `err`）时抛 `KeyError`；
       已改用 `rp.get(..., 0)` 并打印「缺数据：…」。
    两者都在**写完产物之后**的汇总打印处，**影响的只是收尾打印、不影响已落盘产物的正确性**（本批修）。
  · **删除死选项** `--limit`（此前只声明未实现，`a.limit` 全文件零引用）。

**v6（2026-10-07，ISSUE-20261007-11「V 定名补齐」）**：
  把 `V`（= `func_lib.sob` 缓冲内偏移）补完到**可交付的定名表**（有阈值、可失败）。
  判据六条（R1 唯一 event 标签 / R1f 族 / R2 参数级 / R3 func_lib 内嵌串窗口敏感度 /
  R3b 实参=语料 title / R4 逐场计数签名），细则与阈值见 `SOB0解码\定名_说明.md`。
  实测（ot 全库 93 个 V）：**采纳 27 / 候选 15 / 未定 35 / 非命名命令形态 16**。
  ⚠️ **v6.1（2026-10-08，ISSUE-20261008-04 B2「未定 V / 非命名形态攻坚」）增补 9 条采纳**
  （判据 = E1「CFG 体级内嵌串」/ E1+不变式，强度全为「强」）⇒ **采纳 36 / 候选 15 / 未定 28 / 非命名命令形态 14**。
  其中 2 条名称来自**人工语义标签**（`0x2C3C` / `0x23270`，已在各条 `note` 注明）；4 条（`0x10980`/`0x1107C`/
  `0x12998`/`0x12E94`）与既有 `TIME_FAMILY` 族名**冲突、待主代理裁决**（**本版未改 `TIME_FAMILY`**）。
  ⚠️ **本版推翻旧口径两处**：① `0x1C8D0` 不再是「未定（非章节名）」——它的唯一实参
  就是**本场标题**（与语料 `title_variants` 逐场一致 358/367=0.9755），改判「采纳：场景标题设置」；
  ② 旧的**逐场共现 precision≥0.67** 口径**不足以定名**（全覆盖型 type 使近乎所有 V 都「P=1.0」），
  本版改以**唯一归属金标 / 计数签名**为主判据。**契约与事件输出一字未改**（`--check` 仍 PASS）。

**v7（2026-10-07，ISSUE-20261007-11「成果接进构建」T1）**：
  新增 `--emit-v-labels <path>`：把**已采纳**的 V 定名导出为**下游可消费**的 TSV
  （`V_LABEL_HEADER` 7 列，见 `build_v_labels()`）。**候选 15 / 未定（v6.1 后 28）一律不导出**
  ——导出表本身就是「不得把候选当已定名」的闸门；Fade 载体行由既有
  `COMMAND_CARRIERS` 合入（`otp` 无 `V_NAMING`，其载体只经此进入）。
  · **默认不导出**（不给该开关时行为与 v6 逐字节一致）；
  · `--check` 下忽略该开关（只读幂等复核绝不落盘）⇒ 既有产物与 `ALL_PASS` 不受影响。

**v8（2026-10-08，ISSUE-20261008-06 C1「挂账结清」）**——结清 ISSUE-20261008-04 遗留的两件 `TIME_FAMILY` 挂账：
  1. **补入 B3 已证的 3 条时长位**（PSV 旁证；证据见 `子代理工作区\ISSUE-20261008-04\M3\效果类参数_说明.md`）
     ⇒ `TIME_FAMILY["ot"]` 增 `0x1B69C ("quake", 5)`、`0x1B040 ("InOut_Act", 3)`、`0x1AEA0 ("InOut_Act", 2)`；
        `TIME_FAMILY["otr"]` 增 `0x1B69C ("quake", 5)`、`0x1B040 ("InOut_Act", 3)`。
        （`0x1A96C` 既有 `("rule_in", 2)` 的 pos2 与 B3 一致，**不动**；`otp` 侧这两个 V 节点数为 0，**不建**。）
  2. **「两套命名空间」口径落档**（`0x10428` 既有处置的同一口径，见下 §TIME_FAMILY 注释与 `说明.md` §5.3）：
     `TIME_FAMILY` 的**族名字段只是「ms 在第几位」的内部标签**，其唯一职责是给 `time_ms` **取参定位**；
     **命令名走定名线**（`V_NAMING` / 标签表）。故 `0x10980`(bg_zanime↔bg_zoom)、`0x1107C`(bg_ranime↔bg_rot)、
     `0x12998`(dash↔bg_blur)、`0x12E94`(mdash↔bg_blur)、`0x1A96C`(rule_in↔InOut) **两套名字并存、不构成冲突**，
     **键名不改**（改键会造成 `解出_*.tsv` 产物漂移、零收益）。

定位
    把 PC 侧 Lucifen `.sob` 字节码解成**逐 seq 演出事件**，并与 PSV 明文金标
    （`编程组\PSV演出\时间线.tsv`）**对拍**，回答「Lucifen 逆向到底能不能用」。
    本工具是本批（ISSUE-20261006-07）**唯一产物**；不依赖 `build_story.py` /
    `emit_staging_psv.py`，不改任何既有构建器。

依赖的**已解结论**（口径以 `编程组\移交资源组_Lucifen-opcode逆向任务书.md` /
`资源组\逆向\_调研小结_第一波.md` 的 E1/E2/E4/E5/E6 为准）
    1. 容器：`magic(SOB0|SOB1|SOB2) + u32 table_size + 6 表(各 u32 条数 + 条数×8B)
       + u32 strings_start + u32 strings_end`；`header_end = 8 + 六表字节长 + 8`；
       代码区 `[header_end, header_end+strings_start)`，4 字节一字；串区随后。
    2. 六表：`maps[1]` 单元 = 值+1（1 基索引）；`maps[3]` 单元 = 值（绝对地址）；
       `maps[4]` = 站址→本文件体内偏移（含**串引用**与**代码引用 CREF** 两类）；
       `maps[2]`/`maps[5]` 恒空。
    3. **命令节点**形态 `[04][V][0C][k][03][空串REF]`（`C` 恒 `0x0c`）——`V` 是命令标识，
       `k` 是实参字节数（`k == 4×实参数`，99.97%）；节点前的 `[08][arg]…` 是实参。
    4. **BASE 元数表**（本工具按「payload 个数」解释 ⇒ 项字数 = 值+1；缺省 1）：
       `{00:2, 01:0, 03:1, 04:1, 05:3, 06:1, 08:3, 0C:1, 0D:0, 13:0, 14:0,
         17:2, 1E:2, 1F:2, 20:2, 28:2, 2C:3, 2E:0}`
       —— 它**不是无条件解码器**：项首会落在引用字上，**同一现象按「文件集 × 刚性/自适应」有四个口径**
       （务必分别引用，不得混报；一审 §③ 已裁定）：
         · **全库刚性**（412 个 `*.sob`，含系统脚本，无回退）：`ot` **1.16%**、`otp` **2.46%**；
         · **剧情集刚性**（367 个场景引用脚本，无回退）：`ot` **0.0323%**；
         · **剧情集自适应**（加「首个矛盾点检测 + 局部回退」）：`ot` **0.0198%**（本工具默认跑法）。
       与 E4 十 tag 表比较时**必须同口径**：同一 367 文件上 E4 刚性 = **6.42%**。
       本工具实现 **「首个矛盾点检测 + 局部回退」**，逐次回退均记账（见 `--stats`）。
       ⚠️ `08` 的元数存在**两种自洽读法**（`payload=3` 见 BASE；`payload=1` 为对照）——两者都随
       `--stats` 报出，**不擅自改 BASE**（放宽/改动口径必须单独标注为「订正候选」，见 `说明.md` §三）。
       ⚠️ **BASE 的正确性与事件表无关**：`replay_items()` 只喂 `_stats.replay`，**不参与**事件生成；
       事件由独立的**命令节点探测** + `[08][arg]` **2 字实参**模型产生（与 BASE 的 `08=4 字`读法无关）。
    5. 控制串 → 命令**族**（本工具用作角色锚；数字 V **每源本地**，不得跨源搬用）：
       `!l`/`!c`/`!r`/`c`/`_`/`$`/`c_`/`l_`/`r_` → `0x18b74`（ot）／`0x15bac`（otp）；
       `l<2`/`r>2` → `0x186c8`／`0x156e8`；`d`/`u` → `0x10150`／`0xe784`；
       坐标串 `(x,y,p)(x,y,q)` → `0x12e94`。
    6. 参数：`PSV :Time(帧) = Lucifen 宏毫秒 × 0.06`；方向 token → `:Position.x`
       （`!l`→负、`!r`→≥1500、`c`→640、`l`→336、`r`→944、`<d`→236、`>d`→1044）；
       **时间（ms）** 见下条 8。
    7. 层序（Priority）在 PC 侧**无携带者** ⇒ 本工具**不输出层序**。
    8. **时间参数已解出**（v3，2026-10-07）：`[04][V][0C][k][03][空串REF]` 的实参按
       `node_args` 枚举序排开，**ms 所在位随「宏族」而异，绝不能统一取 `args[1]`**。
       `ms = args[TIME_FAMILY[源][V].idx]`（`args` 下标，缺省不写），`time_frame = round(ms×0.06)`。
       ⚠️ **V 号是每源本地的**（`ot`/`otr` 同 V，`otp` 另一套）⇒ 表按源分建，**不得跨源搬用**。
       ⚠️ 未定族**一律不写时间**（不猜：`otp` 仅 2 族、`otr` 仅 6 族有本地位）。
       ⚠️ PC ms 只能恢复约 **96–99%** 的 PSV 时长（余下是移植端改动，PC 侧无携带者）；
       `rule_in` 的 ms 位**有歧义**（pos0/pos2 **有时**同为 500，实测 ot 28.4%）⇒ 标 `read_ambig`。

产物（写本 checkout，落点可由 `--out` 覆盖）
    `编程组\SOB0解码\解出_<源>.tsv`   逐 seq 事件；**既有 9 列契约列序不变**
                                      （`演出表说明.md` §一），尾部**新增 4 列**时间
                                      （`time_ms`/`time_frame`/`time_family`/`time_conf`，
                                       定义见本文件 `HEADER` 与 说明.md §5.3）
                                      ＋**第 14 列** `slot`（v4，2026-10-07）：控制串
                                      （chr_anime）节点的**角色槽号**（`node_args[3]`），
                                      仅已登记族填、其余留空；槽号→族的归属见
                                      `资源组\演出\slot族映射.tsv`（不在本列内）
    `编程组\SOB0解码\对账_逐场.tsv`   逐场对拍汇总（PC 事件 / PSV 事件 / 命中分项）
    `编程组\SOB0解码\_stats.json`     机读统计（说明.md 的每个数字都由它复跑）

用法
    python -X utf8 decode_sob0.py --help
    python -X utf8 decode_sob0.py                      # 全量解码 + 对拍（默认 ot/otp/otr）
    python -X utf8 decode_sob0.py --src ot             # 单源
    python -X utf8 decode_sob0.py --check              # **只读**幂等复核（重算 vs 盘面，绝不落盘）
    python -X utf8 decode_sob0.py --stats              # 只打印统计 JSON，不落盘

边界（如实声明）
    * 只解 SOB0/SOB1/SOB2；`ota`/`otr` 的 `.tob`（TOB0）与 `np`（BGI）**不适用**。
    * 只覆盖「命令节点」族；`Window`/`EyeCatch(End)`/`FadeIn·Out`/`InOut(_Act)`/
      `TimeWait`/`Tag`/`SpriteBS`/`CharacterOpenBS` 在字符串层**无命令节点**（E2 已证
      0 例外）⇒ 解不出，`--stats` 单列「不在本方法可达范围」。
    * `chr_add`/`chr_expr` 的角色二分是**引用序启发式**，不是 opcode 语义。
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import io
import json
import os
import re
import struct
import sys

sys.dont_write_bytecode = True

# ================================================================ 路径（读写分离）
HERE = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\编程组\工具
PRG = os.path.dirname(HERE)                                  # <checkout>\...\编程组
OUT_DEFAULT = os.path.join(PRG, "SOB0解码")                   # 产物落本 checkout

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
PRJ_ROOT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
PSV_TIMELINE = os.path.join(PRJ_ROOT, "编程组", "PSV演出", "时间线.tsv")
PSV_MAP = os.path.join(PRJ_ROOT, "编程组", "PSV演出", "场景映射.tsv")
SCENE_DIR = os.path.join(PRJ_ROOT, "资源组", "剧本")
LEDGER = os.path.join(PRJ_ROOT, "资源组", "krkr素材库", "资源总账.json")

SOURCES = {
    "ot":  dict(dir=os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT"),
                scene="scene_ot.jsonl", prefix="", ext=".sob",
                note="本篇 2009（SOB0）"),
    "otp": dict(dir=os.path.join(DATA_ROOT, "工程", "我们没有翅膀 前奏诗", "解包", "SCRIPT"),
                scene="scene_otp.jsonl", prefix="", ext=".sob",
                note="前奏诗 2008（SOB0）"),
    "otr": dict(dir=os.path.join(DATA_ROOT, "工程", "我们没有翅膀R", "参照", "原版汉化SCRIPT_CHS"),
                scene="scene_otr.jsonl", prefix="s03c_", ext=".sob",
                note="R 版亚衣线 SOB0 版（CHS 重打包，21 个共有场景）"),
}

# ================================================================ 常量
MAGICS = (b"SOB0", b"SOB1", b"SOB2")
# 前 9 列是既有契约（`演出表说明.md` §一），**列序不得改动**；
# 第 10–13 列为本工具 v3 新增的**时间参数**列：
#   time_ms     源侧**直读**的宏毫秒（空缺 = 无时间）
#   time_frame  由 time_ms **换算**（`round(ms×0.06)`）的 PSV 帧；非源侧观测值
#   time_family 取到该 ms 的宏族名（如 `chr_anime`）
#   time_conf   `read`（直读）/ `read_ambig`（直读但位有歧义，`rule_in`）/ 空
HEADER = ["scene_id", "seq", "op", "target", "arg1", "arg2", "arg3",
          "evidence", "confidence",
          "time_ms", "time_frame", "time_family", "time_conf",
          "slot"]
NCOL = 14
BASE_NCOL = 9                 # 既有契约列数（下游只读前 9 列）

# 控制串节点 → 立绘**槽位（slot）** 的「族表」（v4，2026-10-07）。
# 源侧形如 `chr_anime <slot>,"<ctrl>",<ms>`，命令节点实参序 [flag, ms, ctrl, slot]
# ⇒ slot 位 = `node_args` 下标 3。**只登记已独立验证的族**（chr_anime）；
# 未登记族 / 位数不符 / 该位非数字 ⇒ slot 列留空（**不猜**）。
# ⚠️ 该 slot 是 **PC 引擎的角色槽号**；其「槽 → 族」归属**不在本列**（见
#    `资源组\演出\slot族映射.tsv` 与 `slot族身份_评估.md`）。
SLOT_FAMILY = {
    "ot":  {0x18B74: 3},      # chr_anime（CharacterAction/Move）
    "otr": {0x18B74: 3},
    "otp": {0x15BAC: 3},
}
SLOT_ARGC = 4                 # chr_anime 节点实参数；不符不填

# BASE 元数表（**payload 个数**；项字数 = 值+1；缺省 1 ⇒ 缺省 2 字项）
#
# ⚠️⚠️ **本表有 6 个 tag 与引擎真值不符，仅作文档化的启发式，请勿当引擎语义引用。** ⚠️⚠️
#   ISSUE-20261007-11 已从 exe 反汇编还原引擎解释器（47 opcode 栈式 VM：主循环 VA 0x433650、
#   分派表 VA 0x433B54），逐 op 读出操作数字数（= 项长 − 1），与下表的差异：
#     tag   本表 payload   引擎真值 payload
#     0x00      2             0
#     0x08      3             1     ← 即 `[08][arg]` 恰 2 字（本文件头 §4 的「两种读法」由此裁定为 payload=1）
#     0x0D      0             3
#     0x13      0             3
#     0x14      0             3
#     0x2E      0             3
#   其余 tag（01/03/04/05/06/0C/17/1E/1F/20/28/2C）与本表一致。
#   全库 412 个 SOB 线性走查：按引擎真值表 **非法 op 位置 = 0**；按下表 **= 4172**。
#   依据：逆向引擎\执行模型.md §4.4/§4.5；工具 逆向引擎\xwalk.py / xverify.py。
#   本表保留原值不改（下游 `replay_items` 等口径不变），仅作「事件生成无关」的文档化用途。
BASE = {0x00: 2, 0x01: 0, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1, 0x08: 3,
        0x0C: 1, 0x0D: 0, 0x13: 0, 0x14: 0, 0x17: 2, 0x1E: 2, 0x1F: 2,
        0x20: 2, 0x28: 2, 0x2C: 3, 0x2E: 0}
# 「订正候选」：08 的元数改按 payload=1（见文件头 §4；仅作对照，不改默认）
# ⟦RV-ENG-02 订正⟧ 该项已被引擎反汇编**证实**为 payload=1（见上方表）；保留此变量只为兼容旧口径。
BASE_ALT_08 = dict(BASE)
BASE_ALT_08[0x08] = 1

# 控制串 → 角色 / 期望位置（值来自 E5 + 任务书锚点；数字是 ot 本地，otp 另表见 --stats）
CTRL_STRINGS = {
    "!l", "!r", "!c", "c", "l", "r", "_", "$", "c_", "l_", "r_",
    "l<2", "r>2", "d", "u", "_ _", "$$",
    "a0 c", "a0 l", "a0 r", "a0 u", "a0 d", "a0 !l", "a0 !r", "a0 !c",
}
CTRL_BYTES = {s.encode("cp932") for s in CTRL_STRINGS}
CTRL_ROLE = {
    "!l": "CharacterMove", "!r": "CharacterMove", "!c": "CharacterMove",
    "c": "CharacterMove", "l": "CharacterMove", "r": "CharacterMove",
    "l<2": "CharacterOpen", "r>2": "CharacterOpen",
    "_": "CharacterAction", "$": "CharacterAction", "c_": "CharacterAction",
    "l_": "CharacterAction", "r_": "CharacterAction", "_ _": "CharacterAction",
    "$$": "CharacterAction",
    "d": "bg/sprite", "u": "bg/sprite",
}
POS_EXPECT = {"!l": ("neg",), "!r": ("ge", 1500), "c": ("eq", 640),
              "l": ("eq", 336), "r": ("eq", 944), "<d": ("eq", 236),
              ">d": ("eq", 1044)}
COORD_RE = re.compile(r"^(\(\d+,\d+,\d+\)){2,}$")

# 任务书 §「不在本方法可达范围」的无节点命令类（E2 已证 0 例外）
UNREACHABLE = ["Window", "EyeCatch", "EyeCatchEnd", "FadeIn", "FadeOut",
               "InOut", "InOutAct", "TimeWait", "Tag", "SpriteBS",
               "CharacterOpenBS"]

# V 锚点（任务书 §「可复现的锚点」，ot）
V_ANCHORS = {0x1f600: "BgmStop", 0x1b888: "Flash", 0x1c43c: "CharacterOpen",
             0x1c5b0: "CharacterDelete", 0x19808: "CharacterActionEnd/Wait",
             0x19d58: "EffectQuakeEnd", 0x18b74: "CharacterAction/Move",
             0x186c8: "control l<2/r>2"}

# ---- 时间参数（PC 宏毫秒）族表（v3；v8 补 B3 三条）-------------------------
# **每源本地**：`ot` 与 `otr` 共用同一套 V，`otp` 是另一套；**不得跨源搬用 V**。
# 值 = (宏族名, `node_args()` 下标)。位随族而异，**绝不能统一取 `args[1]`**。
# 未登记族 ⇒ **不写时间**（本轮未定的族一律留空，不猜）。
# 字节等价形式（便于实机核对）：argc=k//4、第 p 位字 = 节点 `[04]` 字索引 `i-1-2p`；
# `chr_anime` 的 ms 字 = 控制串字 + 2（文件偏移 +8）。
#
# ★★ 「两套命名空间」（2026-10-08 ISSUE-20261008-06 C1 落档；`0x10428` 既有处置的同一口径）★★
#   本表的 **值域（族名）只是「ms 在第几位」的内部标签**，其**唯一职责**是给 `time_ms` **取参定位**：
#     `ms = args[TIME_FAMILY[源][V].idx]`（见 `node_time()`）。它**不是命令名**，不进下游「命令身份」判断。
#   命令名走**另一条线**：`V_NAMING`（PSV 金标 / 引擎自证串，`--emit-v-labels` 导出）与构建侧标签表。
#   两条线的名字**可以不同而不构成冲突**（判据="离开取参定位，族名还有用吗？"——没有）：
#     · `0x10428`：族名 `bg_anime`（PSV 宏族）↔ 定名 `SpriteMove`（PSV `:Tasktype` 金标）；
#     · `0x10980`：族名 `bg_zanime`（PSV 宏族）↔ 定名 `bg_zoom`（CFG 体级内嵌串）；
#     · `0x1107C`：族名 `bg_ranime`（PSV 宏族）↔ 定名 `bg_rot`（内嵌串）；
#     · `0x12998`：族名 `dash`（PSV 宏族）↔ 定名 `bg_blur`（内嵌串）；
#     · `0x12E94`：族名 `mdash`（PSV 宏族）↔ 定名 `bg_blur`（内嵌串）；
#     · `0x1A96C`：族名 `rule_in`（PSV 宏族）↔ 定名 pending（B3 对 PSV `InOut` 对拍 0.931）。
#   族名出处（查证）：`chr_anime`/`bg_zanime`/`bg_anime`/`bg_ranime`/`fadeend`/`dash`/`mdash`/`rule_in`
#     均为 **PSV 脚本源码注释里的原 Lucifen 宏名**（真实宏调用，逐字可查，例 `//bg_zanime 400,900,2,1.5,1000`），
#     由 ISSUE-20261007-01（`资源组\逆向\_调研小结_第一波.md` §一之七）按「宏族 ⇒ ms 位」分组命名。
#   ⚠️ **不要改键名/族名去迁就定名线**：改键会让 `解出_*.tsv` 的 `time_family` 列漂移、并牵动 `--check` 盘面比对，
#      而**取参定位零收益**（两套名字本就不冲突）。
TIME_FAMILY = {
    "ot": {
        0x18B74: ("chr_anime", 1),
        0x10980: ("bg_zanime", 1),
        0x10428: ("bg_anime", 4),
        0x1107C: ("bg_ranime", 1),
        0x19F9C: ("fadeend", 0),
        0x12E94: ("mdash", 10),
        0x12998: ("dash", 10),
        0x1A96C: ("rule_in", 2),
        # v8（ISSUE-20261008-06 C1）：B3 时长位（PSV 旁证，见 M3\效果类参数_说明.md §二）
        0x1B69C: ("quake", 5),        # EffectQuake：非零 exact 23/23=1.000；otr scene 18/18=1.000
        0x1B040: ("InOut_Act", 3),    # InOut_Act：非零 exact 126/133=0.947；otr scene 32/32=1.000
        0x1AEA0: ("InOut_Act", 2),    # InOut_Act 第二载体：exact 74/74=1.000（ot；otr 仅 1 节点，未建）
    },
    "otp": {
        0x15BAC: ("chr_anime", 1),
        0x0E784: ("bg_anime", 4),
        0x172BC: ("fadeend", 0),        # v5 新增：Fade 载体（ISSUE-20261007-10 T2）
    },
    "otr": {
        0x18B74: ("chr_anime", 1),
        0x10980: ("bg_zanime", 1),
        0x10428: ("bg_anime", 4),
        0x19F9C: ("fadeend", 0),
        0x12998: ("dash", 10),
        0x1A96C: ("rule_in", 2),
        # v8（ISSUE-20261008-06 C1）：B3 时长位（otr 侧独立复现，见 M3\效果类参数_位表.tsv）
        0x1B69C: ("quake", 5),
        0x1B040: ("InOut_Act", 3),
    },
}
# 位有歧义的族：`rule_in` 的 pos0 / pos2 **有时**同为 500（实测 ot 28.4% / otr 18.4%）
# ⇒ 值虽可读，位的语义未定
TIME_FAMILY_AMBIG = {"rule_in"}
# 物理上界：超过 10 分钟的「ms」不是时长（多为无符号化的 -1 等），不写并单独记账
TIME_MS_MAX = 600000

# ---- 命令节点判据开关（v5，ISSUE-20261007-10 T1）----------------------------
# True（默认）= 要求 **V 位 ∈ maps[3] 键**（引擎自带真值位）⇒ 剔除形态假阳性
#                `[04][CREF][0C][k][03][空串REF]`（V 位是页引用字）。
# False        = 旧判据（只要求尾 REF→空串），仅用于对照（CLI `--no-map3`）。
MAP3_BACKED_DEFAULT = True
# 页引用字的高 12 位（用于说明假阳性为何「无 maps[3] 背书」）
PAGE_HIGH = (0x017, 0x018)

# ---- 命令载体登记（v5 T2）--------------------------------------------------
# 「命令族 → 载体 V」的**有金标佐证**登记（**每源本地**，V 号不得跨源搬用）。
# 口径：分母 = 该源语料场 ∩ PSV 金标场（ot 362 / otp 14）。
COMMAND_CARRIERS = {
    "ot": {
        0x19F9C: dict(
            name="FadeIn/FadeOut（时长载体）", ms_idx=0,
            evidence="PSV FadeOut(time>0) 306 场**全命中**该 V（recall 306/306=1.00）；"
                     "V 场 322，其中 306 场同场有 FadeOut(time>0)（precision 0.950）；"
                     "ms 主值 1200×296 ⇒ 1200×0.06=72 帧（= PSV 主时长）",
            precision=0.950, recall=1.0,
            adopt_basis="precision 0.950（≥0.67）+ recall 1.00 双高 ⇒ 采纳；16 场反例见下",
            counterexamples=16,
            counterexample_note="16 场 = 载体 V 出现但无 PSV FadeOut(time>0)："
                                "5 场无 PSV 金标（构建集）+ 11 场金标场；"
                                "**不得当「已解决」**（既有边界：PC 侧只能恢复源侧 96–99%）"),
    },
    "otp": {
        0x172BC: dict(
            name="FadeIn/FadeOut（时长载体）", ms_idx=0,
            evidence="otp 金标场 13/13「ms×0.06 ∈ PSV time 集合」=1.00；ms 主值 1200×39；"
                     "FadeOut(time>0) 14/14 场**全命中**（recall 1.00）",
            precision=0.326, recall=1.0, gold_ms_hit="13/13",
            adopt_basis="**低 precision、高 recall，按 recall 采纳**：precision 0.326 只因 otp 仅 14 场有金标"
                        "（另 29 个载体场无金标、不计入分母），非载体判错；采纳依据 = "
                        "① recall 14/14 = 1.00（金标场零漏）；② 金标场 ms 13/13「ms×0.06 ∈ PSV time」；"
                        "③ ms 主值 1200 → 72 帧 = PSV 主时长。",
            counterexamples=0,
            counterexample_note="otp 仅 14 场有金标，未覆及全部载体场 ⇒ 反例数不可测，非「已验证无例外」"),
    },
}

# ---- V 定名（v6，ISSUE-20261007-11）---------------------------------------
# 判据、阈值与逐条证据见 `SOB0解码\定名_说明.md` 与只读探针
# `SOB0解码\_v_naming_probe.py`（`--md` 出完整表）。
# **只登记，不改变 14 列契约与事件输出**（本表仅 main() 汇总段引用）。
V_NAMING = {
    # 判据（ISSUE-20261007-11；**多口径不得混报**）：
    #  R1   唯一 event 标签：某 seq 上 PC 命令节点恰 1 个 ∧ PSV 非 Message 事件恰 1 个
    #       ⇒ 该 PSV 行 type 即标签；阈值 purity≥0.90 ∧ D≥20 ∧ **基准率护栏 q(type)<0.90**。
    #       q(type) = 该 type 在「单事件 seq（恰 1 条非 Message 行）」中的占比（防基准率假通过）。
    #       实测 q_max = 0.6922（CharacterOpen 9560/13811）< 0.90 ⇒ **当前不触发**（探针 --json 的 r1_prior）。
    #  R1f  同 R1，但按「族」记（top1+top2 ≥ 0.95）。
    #  R2   参数级：实参串 == 同 seq PSV 行 name（样本≥100 ∧ 一致率≥0.90）。
    #  R3   func_lib 内嵌串：窗口 W∈{0x120,0x200,0x400} 首串不变（**敏感度测试**）。
    #  R3b  实参串 == 语料 title_variants（逐场一致率≥0.90；0x1C8D0）。
    #  R4   计数签名：逐场 n_V(sid) vs n_T(sid) 精确率≥0.60 ∧ sumAbsDiff/max(V,T)≤0.35
    #       ∧ type 场覆盖<0.95，且**只看 sad 最小的 3 个候选**。
    #       ⚠️ `0.35` 属**批次标定**、不是有理论依据的阈值：实测 rel 空档 = [0.3188, 0.4314]，
    #       0.35 恰是「能纳入 0x1B040(rel=0.3188)」的最小两位小数（详见 定名_说明.md §2.2）。
    #  ⚠️ 本表数值由 `_v_naming_probe.py` 复跑；一审（RV-NAME）复算：27 项逐条复现、
    #     四条反证全部未推翻（引用于 定名_说明.md §8）。
    #  R1-cand / R1b-cand = 达候选线（R1: D≥10∧pur≥0.80；R1b: D≥30∧pur≥0.95∧平均节点≤2.5）但未达采纳线。
    #  达不到阈值一律「未定」；nodes_cmd≥100 的未定者也登记，免被下游误当已定名。
    "ot": {
        0x1C43C: dict(name='CharacterOpen', rule='R1', verdict='采纳', v_nodes=11049, D=8731, purity=0.9921,
            note='唯一 event 标签 8662/8731'),
        0x19D58: dict(name='EffectQuakeEnd', rule='R1-cand', verdict='候选', v_nodes=7275, D=200, purity=0.8700,
            note='唯一 event 标签 174/200'),
        0x17514: dict(name='CharacterOpen', rule='R1b-cand', verdict='候选', v_nodes=4568,
            note='单事件标签众数 CharacterOpen 0.944(D=585, avg_nodes=4.137)；最佳计数签名 SePlay ex=0.119 sad=2666 rel=0.616 base=0.931；最佳场级 Tag P=1.000 base=1.000；位置均值 0.486'),
        0x14084: dict(name='CharacterOpen', rule='R1b-cand', verdict='候选', v_nodes=4249,
            note='单事件标签众数 CharacterOpen 0.944(D=585, avg_nodes=4.137)；最佳计数签名 CharacterAction ex=0.152 sad=2467 rel=0.613 base=0.674；最佳场级 Tag P=1.000 base=1.000；位置均值 0.486'),
        0x1A96C: dict(name='', rule='R1b-cand', verdict='未定', v_nodes=3116, best_cnt_type='SeStop', best_cnt_rel=0.622,
            note='单事件标签众数 CharacterOpen 0.709(D=781, avg_nodes=3.912)；最佳计数签名 SeStop ex=0.160 sad=1797 rel=0.622 base=0.909；最佳场级 Tag P=1.000 base=1.000；位置均值 0.477'),
        0x18B74: dict(name='CharacterAction/CharacterMove', rule='R1f', verdict='采纳', v_nodes=2363, D=93, purity=0.5914,
            note='族：CharacterAction 55 + CharacterMove 38 = 93/93'),
        0x19808: dict(name='CharacterActionEnd/CharacterWait', rule='R1f', verdict='采纳', v_nodes=2256, D=783, purity=0.7650,
            note='族：CharacterActionEnd 599 + CharacterWait 180 = 779/783'),
        0x1F600: dict(name='BgmPlay/BgmStop', rule='R1f', verdict='采纳', v_nodes=2115, D=269, purity=0.5502,
            note='族：BgmPlay 148 + BgmStop 121 = 269/269'),
        0xA5D0: dict(name='BG* 资源名表（247 项）', rule='E1', verdict='采纳', v_nodes=1342,
            note='E1 体级内嵌串（ISSUE-20261008-04 B2）：CFG 体内引用 BG01…BG81* 共 247 个不同背景名；'
                 '去 `op 0x07` 跳转表边 ⇒ 体缩到 46 条、247 个 BG 名全部消失（可失败自证）。'
                 '旧判据记「未定」；本批升为采纳（引擎自证，非窗口法）。'),
        0x19A68: dict(name='SpriteBG', rule='R1b-cand', verdict='候选', v_nodes=1206,
            note='单事件标签众数 SpriteBG 0.805(D=82, avg_nodes=3.744)；最佳计数签名 EyeCatch ex=0.337 sad=673 rel=0.606 base=0.873；最佳场级 BgmStop P=1.000 base=0.936；位置均值 0.693'),
        0x1FF58: dict(name='SePlay', rule='R1', verdict='采纳', v_nodes=1149, D=36, purity=1.0000,
            note='唯一 event 标签 36/36'),
        0x7480: dict(name='Window', rule='R4', verdict='采纳', v_nodes=991, sum_abs_diff=199, rel=0.188, base=0.928,
            note='计数签名：逐场精确率 0.724，sumAbsDiff 199/max=0.188，base 0.928'),
        0x1B69C: dict(name='EffectQuake', rule='R1', verdict='采纳', v_nodes=939, D=81, purity=0.9753,
            note='唯一 event 标签 79/81'),
        0x205D0: dict(name='SeStop', rule='R1', verdict='采纳', v_nodes=831, D=205, purity=1.0000,
            note='唯一 event 标签 205/205'),
        0x1A858: dict(name='SpriteBG', rule='R1', verdict='采纳', v_nodes=657, D=97, purity=0.9485,
            note='唯一 event 标签 92/97'),
        0x1C5B0: dict(name='CharacterDelete', rule='R1', verdict='采纳', v_nodes=644, D=311, purity=0.9807,
            note='唯一 event 标签 305/311'),
        0x1AD18: dict(name='EyeCatch/EyeCatchEnd', rule='R4', verdict='采纳', v_nodes=561, sum_abs_diff=99, rel=0.159, base=0.873,
            note='计数签名：逐场精确率 0.746，sumAbsDiff 99/max=0.159，base 0.873；'
                 '**EyeCatch 与 EyeCatchEnd 的计数签名完全相同**（sad=99 / ex=0.7459 / Vtot=535 / Ttot=624）'
                 '⇒ 仅字母序不同，**并列记名，不择一**'),
        0x1A730: dict(name='SpriteBG', rule='R1', verdict='采纳', v_nodes=538, D=28, purity=1.0000,
            note='唯一 event 标签 28/28'),
        0x1B888: dict(name='Flash', rule='R4', verdict='采纳', v_nodes=524, sum_abs_diff=62, rel=0.140, base=0.279,
            note='计数签名：逐场精确率 0.961，sumAbsDiff 62/max=0.140，base 0.279'),
        0x9B88: dict(name='SpriteBG', rule='R1b-cand', verdict='候选', v_nodes=519,
            note='单事件标签众数 SpriteBG 0.821(D=39, avg_nodes=3.615)；最佳计数签名 SpriteDeleteBG ex=0.459 sad=391 rel=0.806 base=0.304；最佳场级 BgmStop P=1.000 base=0.936；位置均值 0.509'),
        0x19F9C: dict(name='FadeOut', rule='R4', verdict='采纳', v_nodes=463, sum_abs_diff=43, rel=0.097, base=0.870,
            note='计数签名：逐场精确率 0.901，sumAbsDiff 43/max=0.097，base 0.870'),
        0x182A8: dict(name='CharacterOpen', rule='R1b-cand', verdict='候选', v_nodes=424,
            note='单事件标签众数 CharacterOpen 0.993(D=293, avg_nodes=4.133)；最佳计数签名 CharacterPriority ex=0.768 sad=402 rel=0.978 base=0.028；最佳场级 CharacterOpen P=1.000 base=0.895；位置均值 0.490'),
        0x1C8D0: dict(name='场景标题设置（章/场名）', rule='R3b', verdict='采纳', v_nodes=388,
            note='R3b 实参串=语料 title_variants（逐场一致率≥0.90）'),
        0x186C8: dict(name='sp_move', rule='R3', verdict='采纳', v_nodes=362, first_string='sp_move',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 362 节点'),
        0x1FAD4: dict(name='', rule='无', verdict='未定', v_nodes=360, best_cnt_type='SceneJumpDialog', best_cnt_rel=0.195,
            note='最佳计数签名 SceneJumpDialog ex=0.818 sad=71 rel=0.195 base=1.000；最佳场级 Window P=1.000 base=0.928；位置均值 0.973；'
                 '单事件标签 D=2 且**并列**（EffectQuakeEnd 1 / BgmPlay 1）⇒ 无众数'),
        0x20708: dict(name='SePlay', rule='R1', verdict='采纳', v_nodes=344, D=54, purity=0.9815,
            note='唯一 event 标签 53/54'),
        0x15A04: dict(name='CharacterOpen', rule='R1b-cand', verdict='候选', v_nodes=320,
            note='单事件标签众数 CharacterOpen 0.983(D=115, avg_nodes=4.148)；最佳计数签名 SetSceneName ex=0.823 sad=291 rel=0.993 base=0.005；最佳场级 SpriteBS P=1.000 base=0.829；位置均值 0.585'),
        0xECD4: dict(name='SpriteBG', rule='R1b-cand', verdict='候选', v_nodes=298,
            note='单事件标签众数 SpriteBG 0.889(D=36, avg_nodes=3.944)；最佳计数签名 EffectEnd ex=0.682 sad=253 rel=0.977 base=0.193；最佳场级 SePlay P=1.000 base=0.931；位置均值 0.513'),
        0x9EF4: dict(name='', rule='无', verdict='未定', v_nodes=263, best_cnt_type='SetSceneName', best_cnt_rel=1.000,
            note='最佳计数签名 SetSceneName ex=0.757 sad=235 rel=1.000 base=0.005；最佳场级 SpriteBG P=1.000 base=0.881；位置均值 0.560'),
        0x10150: dict(name='bg_move', rule='R3', verdict='采纳', v_nodes=249, first_string='bg_move',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 249 节点'),
        0x1B040: dict(name='InOut_Act', rule='R4', verdict='采纳', v_nodes=241, sum_abs_diff=95, rel=0.319, base=0.276,
            note='计数签名：逐场精确率 0.906，sumAbsDiff 95/max=0.319，base 0.276'),
        0x209A4: dict(name='SeStop', rule='R1', verdict='采纳', v_nodes=204, D=62, purity=1.0000,
            note='唯一 event 标签 62/62'),
        0x11678: dict(name='SpriteMoveEnd', rule='R1-cand', verdict='候选', v_nodes=177, D=14, purity=1.0000,
            note='唯一 event 标签 14/14'),
        0x11784: dict(name='', rule='R1b-cand', verdict='未定', v_nodes=158, best_cnt_type='EffectStart', best_cnt_rel=0.583,
            note='单事件标签众数 EffectStart 0.587(D=46, avg_nodes=4.826)；最佳计数签名 EffectStart ex=0.832 sad=95 rel=0.583 base=0.193；最佳场级 SpriteBG P=1.000 base=0.881；位置均值 0.506'),
        0x1AE2C: dict(name='', rule='无', verdict='未定', v_nodes=142, best_cnt_type='MovieStop', best_cnt_rel=1.007,
            note='最佳计数签名 MovieStop ex=0.746 sad=141 rel=1.007 base=0.014；最佳场级 CharacterOpen P=1.000 base=0.895；位置均值 0.497'),
        0x7720: dict(name='', rule='无', verdict='未定', v_nodes=135, best_cnt_type='MoviePlay', best_cnt_rel=0.954,
            note='最佳计数签名 MoviePlay ex=0.798 sad=125 rel=0.954 base=0.017；最佳场级 SpriteBG P=1.000 base=0.881；位置均值 0.566'),
        0x10428: dict(name='SpriteMove', rule='R1', verdict='采纳', v_nodes=126, D=25, purity=1.0000,
            note='唯一 event 标签 25/25'),
        0xEFF0: dict(name='', rule='R1b-cand', verdict='未定', v_nodes=121, best_cnt_type='Achievement', best_cnt_rel=1.030,
            note='单事件标签众数 EffectQuake 0.462(D=13, avg_nodes=2.231)；最佳计数签名 Achievement ex=0.909 sad=102 rel=1.030 base=0.014；最佳场级 SpriteBG P=1.000 base=0.881；位置均值 0.579'),
        0x1BD8C: dict(name='EffectQuake', rule='R1b-cand', verdict='候选', v_nodes=120,
            note='单事件标签众数 EffectQuake 1.000(D=18, avg_nodes=1.722)；最佳计数签名 SpriteQuake ex=0.843 sad=95 rel=0.833 base=0.094；最佳场级 SeStop P=1.000 base=0.909；位置均值 0.533'),
        0x17E88: dict(name='CharacterOpen', rule='R1b-cand', verdict='候选', v_nodes=112,
            note='单事件标签众数 CharacterOpen 1.000(D=61, avg_nodes=3.803)；最佳计数签名 SetSceneName ex=0.920 sad=110 rel=1.038 base=0.005；最佳场级 CharacterOpen P=1.000 base=0.895；位置均值 0.387'),
        0x1ABF0: dict(name='', rule='无', verdict='未定', v_nodes=110, best_cnt_type='Achievement', best_cnt_rel=1.028,
            note='最佳计数签名 Achievement ex=0.760 sad=112 rel=1.028 base=0.014；最佳场级 EyeCatchEnd P=1.000 base=0.873；位置均值 0.505'),
        0x1A15C: dict(name='SpriteBG', rule='R1', verdict='采纳', v_nodes=93, D=20, purity=1.0000,
            note='唯一 event 标签 20/20'),
        0x11B0C: dict(name='EffectStart', rule='R1b-cand', verdict='候选', v_nodes=52,
            note='单事件标签众数 EffectStart 0.875(D=24, avg_nodes=4.667)；最佳计数签名 SetSceneName ex=0.948 sad=55 rel=1.078 base=0.005；最佳场级 EffectStart P=1.000 base=0.193；位置均值 0.316'),
        0x1C330: dict(name='EffectQuakeEnd', rule='R1-cand', verdict='候选', v_nodes=52, D=10, purity=1.0000,
            note='唯一 event 标签 10/10'),
        0xFDF4: dict(name='bg_zoom', rule='R3', verdict='采纳', v_nodes=26, first_string='bg_zoom',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 26 节点'),
        0x2A150: dict(name='cross', rule='R3', verdict='采纳', v_nodes=21, first_string='cross',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 21 节点'),
        0x13300: dict(name='bg_blur', rule='R3', verdict='采纳', v_nodes=12, first_string='bg_blur',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 12 节点'),
        0x1E634: dict(name='SYS\\%s.ELG', rule='R3', verdict='采纳', v_nodes=11, first_string='SYS\\%s.ELG',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 11 节点'),
        0x1E45C: dict(name='SYS\\RULE%03d.ELG', rule='R3', verdict='采纳', v_nodes=6, first_string='SYS\\RULE%03d.ELG',
            note='R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 6 节点'),
        0x24F1C: dict(name='SYS/SM_BG2.GMP', rule='R3-cand', verdict='候选', v_nodes=0,
            note='R3 内嵌串稳定但命令节点样本 0 < 5，不足以定名'),
        0x2A4B4: dict(name='rule', rule='R3-cand', verdict='候选', v_nodes=0,
            note='R3 内嵌串稳定但命令节点样本 0 < 5，不足以定名'),

        # ★ 2026-10-08 新增 9 条（ISSUE-20261008-04 B2「未定 V / 非命名形态」攻坚；**全部 verdict=采纳**）。
        #   判据 = E1「CFG 体级内嵌串」/ E1+不变式；**强度全为「强」**（B2 §〇：强 9 / 中 20 / 弱 21 / 无 4）。
        #   ⚠️ 名称来源：`0x2C3C` / `0x23270` 两条的**可读名**来自**人工语义标签**（证据仍是体级不变式 / 串表），
        #      其余 7 条由规则从串表导出（`SOB0解码/_m2_v_forge.py` 的 `label_from_strings`）。
        #      （另一条 `0xA5D0` 已在上方原条目原地改判，不重复登记。）
        #   ⚠️ 需主代理裁决的 `TIME_FAMILY` 冲突（**本批未改 `TIME_FAMILY`**，只在此登记）：
        #      `0x10980` 本批 `bg_zoom` ↔ 既有 `TIME_FAMILY["ot"][0x10980] = bg_zanime`；
        #      `0x1107C` 本批 `bg_rot`  ↔ 既有 `bg_ranime`；
        #      `0x12998` 本批 `bg_blur` ↔ 既有 `dash`；
        #      `0x12E94` 本批 `bg_blur` ↔ 既有 `mdash`。
        #      详见 `子代理工作区\ISSUE-20261008-04\M2\命名冲突对账.tsv` 与 `M3\效果类参数_说明.md` §五。
        0x2C3C: dict(name='文本行推进门/消息渲染体', rule='E1+不变式', verdict='采纳', v_nodes=57859,
            note='**名称来源：人工语义标签（SEM_LABEL）**；证据=四条可失败不变式（尾随 op 恒 0x1E(JZ) 57859/57859、'
                 '实参 ∈ {0,1} 57859/57859、尾 REF 位移恒 +8 57859/57859、自改写条件分支）。'
                 '语义=「每句台词的行推进门」：`if (0x2C3C(arg)==0) 跳下一句 else RET 挂起`。详见 执行模型.md §十三。'),
        0x23270: dict(name='系统UI部件(IF_*)装载族', rule='E1', verdict='采纳', v_nodes=14,
            note='**名称来源：人工语义标签（SEM_LABEL）**；证据=CFG 体内 13 个 `SYS/IF_*.ELG` 内嵌串 + 体内 h228'
                 '(ELG 按名装载)。旧判据记「非命名形态 / 未定」。'),
        0x10980: dict(name='bg_zoom', rule='E1', verdict='采纳', v_nodes=62,
            note='E1 体级内嵌串：CFG 体内 `PUSH S:\'bg_zoom\'`（见 B2 §4.1）。'
                 '⚠️ 与既有 `TIME_FAMILY["ot"][0x10980] = bg_zanime` **冲突，待主代理裁决**；本批**未改 TIME_FAMILY**。'),
        0x1107C: dict(name='bg_rot', rule='E1', verdict='采纳', v_nodes=7,
            note='E1 体级内嵌串：CFG 体内 `bg_rot`。'
                 '⚠️ 与既有 `TIME_FAMILY["ot"][0x1107C] = bg_ranime` **冲突，待主代理裁决**；本批**未改 TIME_FAMILY**。'),
        0x12998: dict(name='bg_blur', rule='E1', verdict='采纳', v_nodes=63,
            note='E1 体级内嵌串：CFG 体内 `bg_blur`。'
                 '⚠️ 与既有 `TIME_FAMILY["ot"][0x12998] = dash` **冲突，待主代理裁决**；本批**未改 TIME_FAMILY**。'),
        0x12E94: dict(name='bg_blur', rule='E1', verdict='采纳', v_nodes=29,
            note='E1 体级内嵌串：CFG 体内 `bg_blur`。'
                 '⚠️ 与既有 `TIME_FAMILY["ot"][0x12E94] = mdash` **冲突，待主代理裁决**；本批**未改 TIME_FAMILY**。'),
        0x11EA0: dict(name='bg_haze/bg_rast', rule='E1', verdict='采纳', v_nodes=23,
            note='E1 体级内嵌串：CFG 体内 `bg_haze` 与 `bg_rast` 两串俱在。'),
        0x1AEA0: dict(name='scroll', rule='E1', verdict='采纳', v_nodes=86,
            note='E1 体级内嵌串：CFG 体内 `scroll`。'
                 '⚠️ B1 串归属重判：`0x1AD18`/`0x1AE2C`/`0x1ABF0` 读到的 `scroll` **实属本 V 的过程**'
                 '（旧窗口法误判；见 SOB0解码/定名_说明.md §1.2 订正）。'),
    },
}

# ---- 遮罩 Rule 命名规则（v5 T4）--------------------------------------------
RULE_NAMING = dict(
    pattern=r"SYS\RULE%03d.ELG",
    carrier="ot 0x1E45C（func_lib 内嵌串 `SYS\\RULE%03d.ELG`，窗口敏感度稳定；"
            "本批实测）；**「:Rule 数值 → 编号」仍不可推**",
    source="func_lib.sob 串区（本批复算：2,926 B / 316 条 ASCII 串，含该串 ×2）",
    psv_values="PSV 时间线 `rule` 列非空 1,413 行，44 个不同值，值域 0–111",
    conversion="**不可推**：① 两条互斥假设并存（直读 `N→RULE{N:03d}` vs 旧注 `0=Simple,"
               " 1=RULE000` 暗示 `N→RULE{N-1:03d}`）；② `RULE###.ELG` 件本体未提取"
               "（在 PSV `ETC.cpk` 内，现仅 `RULE000` 已提）⇒ 无对照物可验。"
               "**结论：命名规则已得，数值→编号换算缺件本体、不可推。**",
)

# ---- 可消费的「命令族标签」导出（v7，ISSUE-20261007-11 T1）------------------
# 目的：把**已采纳**的 V 定名（`V_NAMING` 中 `verdict == '采纳'` 者）从「解码器内部登记」
#       变成**下游可消费的表**（`build_story.py` 等按文件读取）。
#
# ★★ 铁律（本导出函数只做一件事：**过滤**）：
#   · **候选（15）与未定（v6.1 后 28）一律不导出**——不得让下游把「候选」当已定名用；
#   · 只导出 `verdict == '采纳'` 的行 + `COMMAND_CARRIERS` 的载体行
#     （载体行是 FadeIn/FadeOut 的唯一可消费来源；`otp` 无 `V_NAMING`，其载体靠此表进入）。
#   · `carrier` 列取自 `COMMAND_CARRIERS`（本文件既有登记，含 precision/recall/反例），
#     **不是新推断**。
# 列义：
#   src       源（V 号**每 build 组本地**，不得跨源搬用）
#   V         命令载体（`func_lib.sob` 缓冲内偏移），十六进制 `0x…`
#   name      已采纳的命令名（V_NAMING）/ 载体名（COMMAND_CARRIERS）
#   rule      定名判据（R1/R1f/R2/R3/R3b/R4；载体行 `/`）
#   verdict   `采纳`（**只可能有这一个值**）
#   v_nodes   V_NAMING 的节点数（载体行 `/`）
#   carrier   `FadeIn/FadeOut` 表示「该 V 是 Fade 时长载体」（否则空）
V_LABEL_HEADER = ["src", "V", "name", "rule", "verdict", "v_nodes", "carrier"]
FADE_CARRIER_TAG = "FadeIn/FadeOut"


def build_v_labels():
    """→ [row(dict)]：**只含已采纳**的命令族标签（∪ 载体登记），可复跑、可失败。

    预期行数（当前表）：ot V_NAMING 采纳 **36** ＋ otp 载体 1 ＝ **37**；
    若 V_NAMING 的采纳数或 COMMAND_CARRIERS 变动，行数随之变（调用方可断言）。
    （2026-10-08 ISSUE-20261008-04 B2 增补 9 条采纳 ⇒ 27→36；本函数**只过滤、不改语义**。）
    """
    rows = {}
    for src, tbl in V_NAMING.items():
        for V, d in tbl.items():
            if d.get("verdict") != "采纳":       # ★ 候选 / 未定 **一律不导出**
                continue
            rows[(src, V)] = dict(
                src=src, V="0x%X" % V, name=(d.get("name") or ""),
                rule=(d.get("rule") or ""), verdict="采纳",
                v_nodes=(d.get("v_nodes") if d.get("v_nodes") is not None else ""),
                carrier="")
    for src, tbl in COMMAND_CARRIERS.items():
        for V, d in tbl.items():
            k = (src, V)
            if k in rows:
                rows[k]["carrier"] = FADE_CARRIER_TAG
            else:
                rows[k] = dict(src=src, V="0x%X" % V, name=(d.get("name") or ""),
                               rule="/", verdict="采纳", v_nodes="",
                               carrier=FADE_CARRIER_TAG)
    return [rows[k] for k in sorted(rows, key=lambda x: (x[0], x[1]))]


def write_v_labels(path):
    """把 `build_v_labels()` 写成 TSV（LF、UTF-8）。返回 (行数, 路径)。"""
    rows = build_v_labels()
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(V_LABEL_HEADER) + "\n")
        for r in rows:
            f.write("\t".join(_clean(r[c]) for c in V_LABEL_HEADER) + "\n")
    return len(rows), os.path.abspath(path)


# ================================================================ 工具函数
def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def _clean(v):
    if v is None:
        return ""
    return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")


# ================================================================ 时间参数（v3）
def node_time(src, node):
    """命令节点 → `(ms, family, conf, status)`（无时间时 ms=None）。

    `status` ∈ `none`（非本族 / 该源无表 / 位越界）/ `nonnum`（该位不是数字实参）/
    `out_of_range`（负数或 > `TIME_MS_MAX`）/ `ok`。
    `conf` ∈ `read`（直读）/ `read_ambig`（直读但位有歧义）。
    """
    ent = TIME_FAMILY.get(src, {}).get(node.get("V"))
    if ent is None:
        return None, "", "", "none"
    name, idx = ent
    args = node.get("args") or []
    if idx >= len(args):
        return None, name, "", "none"
    kind, val = args[idx]
    if kind not in ("N", "A", "I") or not isinstance(val, int):
        return None, name, "", "nonnum"
    if val < 0 or val > TIME_MS_MAX:
        return None, name, "", "out_of_range"
    return val, name, ("read_ambig" if name in TIME_FAMILY_AMBIG else "read"), "ok"


def ms_to_frame(ms):
    """PC 宏毫秒 → PSV 帧（换算，非源侧观测值）。"""
    return int(round(ms * 0.06))


def node_slot(src, V, args):
    """命令节点 → 立绘槽位号（**仅对 `SLOT_FAMILY` 已登记族**；否则返回 ""）。

    命中条件：`src` 该族已登记 ∧ `len(args) == SLOT_ARGC` ∧ 该位为数字实参。
    其余（未登记族 / 位数不符 / 非数字）一律返回 ""——**不猜**。
    """
    idx = SLOT_FAMILY.get(src, {}).get(V)
    if idx is None or len(args) != SLOT_ARGC:
        return ""
    kind, val = args[idx]
    if kind not in ("N", "A", "I") or not isinstance(val, int):
        return ""
    return val


# ================================================================ SOB0 容器
class Sob0:
    """一个 `.sob` 的容器视图。"""

    def __init__(self, path, map3_backed=MAP3_BACKED_DEFAULT):
        with open(path, "rb") as f:
            self.path = path
            self.d = f.read()
        self.map3_backed = map3_backed
        d = self.d
        if d[:4] not in MAGICS:
            raise ValueError("非 SOB 容器：%s" % d[:4])
        self.magic = d[:4].decode()
        table_size = u32(d, 4)
        self.table_end = table_size + 8
        off = 8
        self.maps = []
        while off < self.table_end:
            n = u32(d, off)
            off += 4
            if n > 200000:
                raise ValueError("表条数异常 %d（非本布局）" % n)
            m = {}
            for _ in range(n):
                m[u32(d, off)] = u32(d, off + 4)
                off += 8
            self.maps.append(m)
        if len(self.maps) != 6:
            raise ValueError("表数 != 6（%d）" % len(self.maps))
        self.ss = u32(d, self.table_end)
        self.se = u32(d, self.table_end + 4)
        self.header_end = self.table_end + 8
        if self.header_end + self.se > len(d):
            raise ValueError("串区越界")
        self.cells = [u32(d, self.header_end + 4 * i)
                      for i in range(self.ss // 4)]
        # 引用站点（6 表键的并集，4 对齐）
        ref = set()
        for m in self.maps:
            ref |= set(m)
        self.ref_sites = {k for k in ref if k % 4 == 0}

    # ---- 串 ----
    def read_group(self, v):
        """按 extract_sob0.py 语义读一个「串组」（含选择支附加串）。"""
        d, p = self.d, self.header_end + v
        out = []
        if d[p] == 0:
            p += 3
        sel = 0
        if d[p] in (2, 3):
            sel = d[p] - 1
            p += 4
        e = d.find(b"\x00", p)
        out.append(d[p:e])
        p = e + 1
        for _ in range(sel):
            if d[p] == 0:
                p += 3
            e = d.find(b"\x00", p)
            out.append(d[p:e])
            p = e + 1
        return out

    def str_at(self, site_word_index):
        """站址（字索引）→ 首串文本；非串引用返回 None。"""
        v = self.maps[4].get(site_word_index * 4)
        if v is None or not (self.ss <= v < self.se):
            return None
        raw = self.read_group(v)[0]
        return raw.decode("cp932", "replace")

    def empty_offsets(self):
        return {v for k, v in self.maps[4].items()
                if self.ss <= v < self.se and self.d[self.header_end + v] == 0}

    # ---- 槽（复刻 build_staging_sob0.parse_sob0 的枚举顺序）----
    def slots(self):
        """按 `maps[4]` 登记顺序枚举**串引用**槽（复刻 extract_sob0 / build_staging_sob0）。

        只保留「引用字的页号 == 本文件串引用的众数页」的引用——**不写死 `0x018`**
        （A 路 §4.3 建议；本篇/前奏诗众数页 `0x018`、`s01_03c1` 为 `0x017`、
        R 版 CHS SOB0 为 `0x018`）。不加此过滤会把少量非文本页引用计入槽表，
        使 `lineno` 索引整体错位（本工具曾因此在 24 场退化为序数锚定）。
        """
        pk = collections.Counter()
        for addr, v in self.maps[4].items():
            if self.ss <= v < self.se and addr // 4 < len(self.cells):
                pk[self.cells[addr // 4] >> 20] += 1
        modal = pk.most_common(1)[0][0] if pk else None
        out = []
        for addr in range(0, max(0, self.ss), 4):
            v = self.maps[4].get(addr)
            if v is None or not (self.ss <= v < self.se):
                continue
            if modal is not None and (self.cells[addr // 4] >> 20) != modal:
                continue
            for raw in self.read_group(v):
                kind, body = self._classify(raw)
                out.append(dict(addr=addr, kind=kind, raw=raw, body=body))
        return out

    @staticmethod
    def _classify(raw):
        """复刻 `build_staging_sob0.classify`（dialogue 的 body = `$&` 后的正文，去尾 `$`）。

        `lineno`/`index`（源槽号）是对**这份槽表**而言的 ⇒ body 的取法必须与之一致，
        否则字段探测会把全部场景判为「不匹配」而退回序数锚定（本工具曾踩此坑）。
        """
        if b"$&" in raw:
            _head, body = raw.split(b"$&", 1)
            if body.endswith(b"$"):
                body = body[:-1]
            return "dialogue", body.decode("cp932", "replace")
        try:
            raw.decode("ascii")
            return "ascii", raw.decode("cp932", "replace")
        except UnicodeDecodeError:
            return "other", raw.decode("cp932", "replace")

    # ---- 命令节点 ----
    def command_nodes(self, map3_backed=None):
        """命中 `[04][V][0C][k][03][尾REF→空串]` 的字索引列表。

        `map3_backed`（v5，ISSUE-20261007-10 T1）：是否要求 **V 位 ∈ `maps[3]` 键**
        （引擎自带的「立即数」真值位）⇒ 剔除形态假阳性 `[04][CREF][0C][k][03][空串REF]`。
        默认取 `self.map3_backed`（构造时定，默认开）；`--no-map3` 时传 False 做对照。
        侧记：`self.n_classic_nodes`（旧判据命中数）/ `self.n_kept_nodes`（收紧后留存数）。
        """
        if map3_backed is None:
            map3_backed = self.map3_backed
        emp = self.empty_offsets()
        m3 = self.maps[3]
        c = self.cells
        out = []
        n_cls = 0
        for i in range(len(c) - 5):
            if not (c[i] == 4 and c[i + 2] == 0x0C and c[i + 4] == 3
                    and self.maps[4].get((i + 5) * 4) in emp):
                continue
            n_cls += 1
            if map3_backed and (i + 1) * 4 not in m3:
                continue                    # 无 maps[3] 背书 ⇒ 形态假阳性，剔除
            out.append(i)
        self.n_classic_nodes = n_cls
        self.n_kept_nodes = len(out)
        return out

    def decode_arg(self, wi):
        """实参字（字索引）→ (kind, value)。kind ∈ S(串)/C(代码引用)/A/I/P/N。"""
        w = self.cells[wi]
        site = wi * 4
        if site in self.maps[4]:
            v = self.maps[4][site]
            if self.ss <= v < self.se:
                return "S", self.read_group(v)[0].decode("cp932", "replace")
            return "C", w
        if site in self.maps[3]:
            return "A", self.maps[3][site]
        if site in self.maps[1]:
            return "I", self.maps[1][site] + 1
        if site in self.maps[0]:
            return "P", self.maps[0][site]
        return "N", w

    def node_args(self, wi):
        """命令节点（`[04]` 所在字索引）的实参列表 [(kind, value), ...]。"""
        k = self.cells[wi + 3]
        argc = k // 4
        return [self.decode_arg(wi - 1 - 2 * t) for t in range(argc)]


# ================================================================ 项流重放 + 局部回退
def replay_items(sob, base, defaults=1):
    """按 BASE 铺项；返回 (items, stats)。

    `items` = [(head_index, tag, nwords)]，`stats` = dict（矛盾点/回退/末对齐）。
    矛盾点判据（**本工具自定，写明**）：
        ① **项首落在引用字上**——引用字（6 表键）不可能是 tag（tag 恒为小整数）；
        ② **末字未对齐代码区**（walk 未恰好吃完 `ss/4` 个字）。
    局部回退策略：在矛盾点 `h` 处，把**上一个项**（起点 p）的元数在 1..4 内重试，
    取「令 `(p+L)` 不是引用字、且再走一步也不矛盾」的最小 `L`；找到则以新元数续走并记账；
    找不到则**跳过一个字**（保守前进）并记为 unresolved。
    """
    c = sob.cells
    ref = sob.ref_sites
    n = len(c)
    items = []
    stats = dict(heads=0, contradictions=0, rollbacks=0, unresolved=0,
                 end_ok=0, end_remainder=0)
    i = 0
    prev = None               # 上一项 (head, tag, nwords)
    guard = 0
    while i < n and guard < 10 * n:
        guard += 1
        is_bad = (i * 4) in ref
        if is_bad:
            stats["contradictions"] += 1
            fixed = False
            if prev is not None and prev[2] > 1:
                ph, pt = prev[0], prev[1]
                for L in range(1, 5):
                    j = ph + L
                    if j >= n:
                        continue
                    if (j * 4) in ref:
                        continue
                    # 再走一步不矛盾
                    t2 = c[j] & 0xffffffff
                    j2 = j + base.get(t2, defaults) + 1
                    if j2 <= n and (j2 == n or (j2 * 4) not in ref):
                        if L != prev[2]:
                            items.pop()
                            items.append((ph, pt, L))
                            stats["rollbacks"] += 1
                            i = j
                            prev = (ph, pt, L)
                            fixed = True
                        break
            if not fixed:
                stats["unresolved"] += 1
                i += 1
                prev = None
                continue
        t = c[i] & 0xffffffff
        L = base.get(t, defaults) + 1
        items.append((i, t, L))
        prev = (i, t, L)
        stats["heads"] += 1
        i += L
    if i == n:
        stats["end_ok"] = 1
    else:
        stats["end_remainder"] = i - n
    return items, stats


# ================================================================ seq 锚定
def build_seqmap(slots, lines):
    """复刻 build_staging_sob0 的 seq 锚定：先探字段（lineno/index），否则序数回退。

    返回 (smap_pairs, mode)。`smap_pairs` = [(slot_index, seq), ...]。
    """
    def norm(s):
        return re.sub(r"[\s\u3000]+", "", (s or "").rstrip("$"))

    for f in ("lineno", "index"):
        vals = [l.get(f) for l in lines]
        if any(not isinstance(v, int) for v in vals):
            continue
        if any(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)):
            continue
        if any(v < 0 or v >= len(slots) for v in vals):
            continue
        hit = sum(1 for l, v in zip(lines, vals)
                  if slots[v]["kind"] != "ascii"
                  and norm(slots[v]["body"]) == norm(l.get("jp")))
        if hit == len(lines):
            return list(zip(vals, [l["seq"] for l in lines])), ("field:" + f)
    # 序数回退
    text_idx = [i for i, s in enumerate(slots) if s["kind"] != "ascii"]
    pairs = [(i, lines[k]["seq"]) for k, i in enumerate(text_idx[:len(lines)])]
    return pairs, "ordinal"


class SeqMap:
    def __init__(self, pairs):
        self.idx = [int(a) for a, _ in pairs]
        self.seqs = [int(b) for _, b in pairs]

    def seq_for(self, raw_index):
        j = bisect.bisect_right(self.idx, int(raw_index))
        if j >= len(self.seqs):
            return self.seqs[-1], "after_last_line"
        return self.seqs[j], ("before_first_line" if j == 0 else None)


# ================================================================ 素材账（target 映射）
class Ledger:
    def __init__(self, path):
        self.m = collections.defaultdict(dict)
        if not os.path.isfile(path):
            return
        with io.open(path, encoding="utf-8") as f:
            d = json.load(f)
        for e in d.get("entries", []):
            kind, src = e.get("kind"), e.get("source")
            on, rel = e.get("orig_name"), e.get("out_relpath")
            if not (kind and src and on and rel):
                continue
            tok = os.path.splitext(os.path.basename(on))[0].upper()
            self.m[(kind, src)].setdefault(tok, rel)

    def target(self, kind, tok, src):
        return self.m.get((kind, src), {}).get((tok or "").upper())


PREFIX_KIND = {"PIC": "pic", "SE": "se", "SYS": "sys", "BGM": "bgm",
               "VOICE": "voice", "CHR": "chr", "MOVIE": "movie"}


def path_ref(body):
    b = (body or "").strip()
    if not b or not re.search(r"[\\/]", b):
        return None, None
    head = re.split(r"[\\/]", b, maxsplit=1)[0].upper()
    kind = PREFIX_KIND.get(head)
    if kind is None:
        return None, None
    return kind, os.path.splitext(os.path.basename(b.replace("/", os.sep)))[0].upper()


# ================================================================ 事件抽取
def extract_scene(src, scene, sob, slots, refmap, ledger):
    """一个场景 → (rows, info)。rows 为 9 列事件（`演出表说明.md` 契约）。"""
    lines = scene["lines"]
    sid, script = scene["scene_id"], scene["script"]
    addrs = [s["addr"] for s in slots]
    pairs, mode = build_seqmap(slots, lines)
    smap = SeqMap(pairs)
    nodes = sob.command_nodes()

    # 控制串槽 → 其后**第一个**命令节点（E2 口径）。一个控制串恰记一次；
    # 一个节点可被多个控制串指向（复合串），故**逐控制串**记账（不按节点去重）。
    # 控制串 = 已知助记符（CTRL_BYTES）或坐标串（`(x,y,p)(x,y,q)…`）。
    ctrl_at = [(s["addr"], s["body"]) for s in slots
               if s["raw"] in CTRL_BYTES or COORD_RE.match(s["body"])]
    ctrl_map = []          # (body, node_index)
    node_ctrl = {}         # node_index -> 最近的一个控制串（供 9 列输出用）
    for ca, cb in ctrl_at:
        pos = bisect.bisect_right(nodes, ca // 4)
        if pos < len(nodes):
            ni = nodes[pos]
            ctrl_map.append((cb, ni))
            node_ctrl[ni] = cb

    rows = []
    node_infos = []
    # `confidence` 只描述 (scene_id, seq) 的证据强度（契约 §1.4）：
    #   seq 由**源侧直证**（`lineno`/`index` 字段逐行命中）⇒ `exact`；
    #   seq 由**序数锚定推断**（第 k 槽 ↔ 第 k 行；字段探测不成立）⇒ `inferred`。
    seq_conf = "exact" if mode.startswith("field") else "inferred"
    seq_note = "" if mode.startswith("field") else " seq_ordinal=1"
    if not mode.startswith("field") and src == "otr":
        # otr 的序数映射已在 ≥11/21 场被证错位（见 说明.md §5.1）⇒ 表内显式标注
        seq_note += " seq_unreliable=1(otr-序数锚定,不得作为逐行seq依据)"
    for i in nodes:
        ctrl = node_ctrl.get(i)
        args = sob.node_args(i)
        # seq：节点末字（空串 REF）所在槽 → 其后第一个文本行
        a = (i + 5) * 4
        j = bisect.bisect_left(addrs, a)
        seq, tag = smap.seq_for(j)
        V = sob.cells[i + 1]
        kbytes = sob.cells[i + 3]
        if kbytes % 4 != 0:
            kf = "k%%4=%d" % (kbytes % 4)
        else:
            kf = ""

        # op 映射：实参里的资源路径优先；否则 other（控制串放 arg1）
        op, target, arg1, arg2 = "other", "", (ctrl or ""), ""
        for kind, val in args:
            if kind != "S":
                continue
            pk, tok = path_ref(val)
            if not pk:
                continue
            op = {"pic": "bg", "se": "se", "bgm": "bgm", "movie": "movie",
                  "chr": "chr_add", "sys": "effect"}.get(pk, "other")
            arg1 = val
            if ledger:
                t = ledger.target(pk, tok, src)
                target = t or ""
            arg2 = tok
            break
        if ctrl and ctrl in CTRL_ROLE:
            arg2 = arg2 or CTRL_ROLE[ctrl]
        ev = ("script=%s; SOB0 node code#%d V=0x%X k=%d argc=%d args=[%s] ctrl=%r"
              % (script, i, V, kbytes, kbytes // 4,
                 ",".join("%s:%s" % (kk, vv) for kk, vv in args), ctrl))
        if tag:
            ev += " " + tag
        if kf:
            ev += " " + kf
        ev += seq_note
        # 时间参数（v3）：族与位按**源本地**表取；未定族/该位非数字 ⇒ 四列留空
        tms, tfam, tconf, _tst = node_time(src, dict(V=V, args=args))
        if tms is None:
            trow = dict(time_ms="", time_frame="", time_family="", time_conf="")
        else:
            trow = dict(time_ms=tms, time_frame=ms_to_frame(tms),
                        time_family=tfam, time_conf=tconf)
        # 槽位（v4）：仅已登记族（chr_anime）填；未登记族 / 位数不符 ⇒ 空
        rows.append(dict(scene_id=sid, seq=seq, op=op, target=_clean(target),
                         arg1=_clean(arg1), arg2=_clean(arg2),
                         arg3="V=0x%X" % V, evidence=ev, confidence=seq_conf,
                         slot=node_slot(src, V, args), **trow))
        node_infos.append(dict(code=i, V=V, seq=seq, ctrl=ctrl, args=args))
    node_seq = {nd["code"]: nd["seq"] for nd in node_infos}
    node_V = {nd["code"]: nd["V"] for nd in node_infos}
    ctrl_resolved = [dict(ctrl=cb, code=ni, V=node_V.get(ni), seq=node_seq.get(ni))
                     for cb, ni in ctrl_map]
    return rows, dict(mode=mode, nodes=node_infos, ctrl_map=ctrl_resolved,
                      script=script, sid=sid)


# ================================================================ PSV 金标
def load_psv_timeline():
    """→ (by_scene, scene_ids)。by_scene[sid] = list of row dict。"""
    by = collections.defaultdict(list)
    if not os.path.isfile(PSV_TIMELINE):
        return by, []
    with io.open(PSV_TIMELINE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            by[row["scene_id"]].append(row)
    return by, sorted(by)


def psv_events_by_seq(rows):
    """PSV 行 → {seq(str): [非 text 行]}。`Message` 视为文本行，不计入演出事件。"""
    out = collections.defaultdict(list)
    for r in rows:
        if r.get("type") == "Message":
            continue
        out[str(r.get("seq"))].append(r)
    return out


# ================================================================ 对拍
def run_compare(per_source, psv_by_scene):
    """核心对拍。返回 stats dict（含逐场明细 per_scene）。"""
    st = dict(
        by_source={},
        per_scene=collections.defaultdict(dict),
        v_task=collections.Counter(),          # (src,V)->Tasktype  单任务 seq
        v_task_total=collections.Counter(),
        ctrl_v=collections.defaultdict(collections.Counter),   # 控制串 -> V（全量）
        ctrl_psv=collections.defaultdict(collections.Counter),  # 控制串 -> PSV type（单任务）
        time_argpos=collections.defaultdict(lambda: [0, 0]),    # 参数位 -> [hit, total]
        time_nodes=[0, 0],                     # 时间参数：命中节点数 / 有 time 的节点数
        # ---- 时间参数（v3）：族表命中 / 覆盖 ----
        # time_family[src][族] = dict(nodes, ok, nonnum, out_of_range,
        #                             seq=[hit,total], scene=[hit,total], scenes=set)
        time_family=collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: dict(nodes=0, ok=0, nonnum=0, out_of_range=0,
                             seq=[0, 0], scene=[0, 0], scenes=set()))),
        time_rows=collections.defaultdict(lambda: dict(rows=0, scenes=set())),
        pos_strict=collections.defaultdict(lambda: [0, 0]),     # 控制串 -> [hit, total]
        unreachable=collections.Counter(),
    )
    for src, scenes in per_source.items():
        s = dict(scenes=0, scenes_with_psv=0, seq_both=0, seq_single=0,
                 nodes=0, control_hits=0, control_total=0, seq_modes=collections.Counter())
        for sid, (rows, info) in scenes.items():
            s["scenes"] += 1
            s["seq_modes"][info["mode"]] += 1
            s["nodes"] += len(info["nodes"])
            psdet = dict(psv=False, psv_events=0, seq_both=0, seq_single=0,
                         pc_events=len(rows), nodes=len(info["nodes"]),
                         ctrl_nodes=sum(1 for nd in info["nodes"] if nd["ctrl"]))
            st["per_scene"][src][sid] = psdet
            psv_rows = psv_by_scene.get(sid) or []
            pev = psv_events_by_seq(psv_rows) if psv_rows else {}
            psv_times = set()
            for r in psv_rows:
                if r.get("type") == "Message":
                    continue
                t = r.get("time", "")
                if t:
                    try:
                        psv_times.add(int(t))
                    except ValueError:
                        pass
            # ---- 时间参数族统计（**全场景**，不限于有金标场；族表按源本地）----
            #   nodes/ok/nonnum/out_of_range 为该族节点数（源侧）；
            #   seq  = 该节点 seq 上有 PSV `time` 时，`round(ms×0.06)` 命中该 seq
            #          任一 PSV time 的比例（**同 seq 口径**）；
            #   scene= `round(ms×0.06)` ∈ 本场 PSV time 集合的比例（**同场口径**）。
            for nd in info["nodes"]:
                ent = TIME_FAMILY.get(src, {}).get(nd["V"])
                if ent is None:
                    continue
                cell = st["time_family"][src][ent[0]]
                cell["nodes"] += 1
                cell["scenes"].add(sid)
                ms, _fam, _conf, status = node_time(src, nd)
                if status == "ok":
                    cell["ok"] += 1
                elif status in ("nonnum", "out_of_range"):
                    cell[status] += 1
                if ms is None:
                    continue
                a = st["time_rows"][src]
                a["rows"] += 1
                if sid not in a["scenes"]:
                    a["scenes"].add(sid)
                if not psv_rows:
                    continue
                fr = ms_to_frame(ms)
                ts = [int(p["time"]) for p in pev.get(str(nd["seq"]), [])
                      if p.get("time", "").isdigit()]
                if ts:
                    cell["seq"][1] += 1
                    if fr in ts:
                        cell["seq"][0] += 1
                if psv_times:
                    cell["scene"][1] += 1
                    if fr in psv_times:
                        cell["scene"][0] += 1
            if not psv_rows:
                continue
            s["scenes_with_psv"] += 1
            psdet["psv"] = True
            psdet["psv_events"] = sum(1 for r in psv_rows if r.get("type") != "Message")
            pc_by_seq = collections.defaultdict(list)
            for nd in info["nodes"]:
                pc_by_seq[nd["seq"]].append(nd)
            # ---- 控制串归属（逐控制串；与 seq 上的 PSV 金标比对）----
            for ce in info["ctrl_map"]:
                body, V, cseq = ce["ctrl"], ce["V"], ce["seq"]
                st["ctrl_v"][body][(src, V)] += 1
                s["control_total"] += 1
                ps = pev.get(str(cseq))
                if not ps or len(ps) != 1:
                    continue
                st["ctrl_psv"][body][ps[0].get("type", "")] += 1
                if body in POS_EXPECT and CTRL_ROLE.get(body) == ps[0].get("type"):
                    cx = ps[0].get("cx", "")
                    try:
                        cxv = int(float(cx))
                    except (ValueError, TypeError):
                        cxv = None
                    if cxv is not None:
                        exp = POS_EXPECT[body]
                        cell = st["pos_strict"][body]
                        cell[1] += 1
                        ok = (exp[0] == "neg" and cxv < 0) or \
                             (exp[0] == "ge" and cxv >= exp[1]) or \
                             (exp[0] == "eq" and abs(cxv - exp[1]) <= 2)
                        if ok:
                            cell[0] += 1
            # ---- 命令身份 + 时间参数（单任务且单节点 seq）----
            for seq, nds in pc_by_seq.items():
                ps = pev.get(str(seq))
                if not ps:
                    continue
                s["seq_both"] += 1
                psdet["seq_both"] += 1
                single = (len(ps) == 1 and len(nds) == 1)
                if single:
                    s["seq_single"] += 1
                    psdet["seq_single"] += 1
                    nd, prow = nds[0], ps[0]
                    st["v_task"][(src, nd["V"], prow.get("type", ""))] += 1
                    st["v_task_total"][(src, nd["V"])] += 1
                    # 时间参数（取该 seq 唯一 PSV 行的 time；PC 侧逐个实参位试 `ms×0.06`）
                    if prow.get("time", ""):
                        try:
                            tf = int(prow["time"])
                        except ValueError:
                            tf = None
                        if tf is not None:
                            st["time_nodes"][1] += 1
                            anyhit = False
                            for pi, (kk, vv) in enumerate(nd["args"]):
                                if kk not in ("N", "A", "I") or not isinstance(vv, int):
                                    continue
                                if not (0 <= vv <= 20000):
                                    continue
                                st["time_argpos"][pi][1] += 1
                                if round(vv * 0.06) == tf:
                                    st["time_argpos"][pi][0] += 1
                                    anyhit = True
                            if anyhit:
                                st["time_nodes"][0] += 1
        st["by_source"][src] = s
    return st


# ================================================================ 主流程
def collect(src, ledger, map3_backed=MAP3_BACKED_DEFAULT):
    """→ (scenes: {sid: (rows, info)}, stats)。"""
    spec = SOURCES[src]
    scene_path = os.path.join(SCENE_DIR, spec["scene"])
    scenes = {}
    if not os.path.isfile(scene_path):
        return scenes, dict(err="缺场景语料 %s" % scene_path)
    nfile = nnon = 0
    n_classic = n_kept = 0
    replay_stats = []
    with io.open(scene_path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            script = o["script"]
            if spec["prefix"] and not script.lower().startswith(spec["prefix"]):
                continue
            p = os.path.join(spec["dir"], script + spec["ext"])
            if not os.path.isfile(p):
                continue
            try:
                sob = Sob0(p, map3_backed=map3_backed)
            except ValueError:
                continue
            nfile += 1
            slots = sob.slots()
            rows, info = extract_scene(src, o, sob, slots, None, ledger)
            scenes[o["scene_id"]] = (rows, info)
            n_classic += sob.n_classic_nodes
            n_kept += sob.n_kept_nodes
            _, rs = replay_items(sob, BASE)
            replay_stats.append(rs)
            nnon += 1
    agg = dict(files=nfile,
               heads=sum(r["heads"] for r in replay_stats),
               contradictions=sum(r["contradictions"] for r in replay_stats),
               rollbacks=sum(r["rollbacks"] for r in replay_stats),
               unresolved=sum(r["unresolved"] for r in replay_stats),
               end_ok=sum(r["end_ok"] for r in replay_stats),
               end_bad=sum(1 for r in replay_stats if r["end_ok"] == 0),
               nodes_classic=n_classic, nodes_kept=n_kept,
               nodes_removed=n_classic - n_kept)
    return scenes, agg


def write_tsv(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(HEADER) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in HEADER) + "\n")


def read_norm(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def build_all(srcs, out_dir, ledger, map3_backed=MAP3_BACKED_DEFAULT):
    per_source = {}
    replay = {}
    for src in srcs:
        scenes, agg = collect(src, ledger, map3_backed=map3_backed)
        per_source[src] = scenes
        replay[src] = agg
    psv_by_scene, psv_ids = load_psv_timeline()
    cmpst = run_compare(per_source, psv_by_scene)
    return per_source, replay, cmpst


def _self_consistency(cmpst, src=None):
    """V→Tasktype 自洽率（单任务 seq）：各 V 的众数 Tasktype 命中数 / 总数。"""
    tot = agree = 0
    for (s, V), n in cmpst["v_task_total"].items():
        if src is not None and s != src:
            continue
        c = collections.Counter()
        for (s2, V2, t), m in cmpst["v_task"].items():
            if s2 == s and V2 == V:
                c[t] += m
        best = c.most_common(1)
        if best:
            agree += best[0][1]
        tot += n
    return dict(total=tot, agree=agree, rate=round(agree / tot, 4) if tot else None)


def render_stats(per_source, replay, cmpst, map3_backed=MAP3_BACKED_DEFAULT):
    """→ 可 JSON 化的统计（说明.md 的数字来源）。"""
    out = dict(
        sources={},
        v_task_table={},
        ctrl_v={},
        ctrl_psv={},
        time_argpos={},
        pos_strict={},
        anchors={},
        unreachable=UNREACHABLE,
    )
    for src, scenes in per_source.items():
        rows_total = 0
        opc = collections.Counter()
        confc = collections.Counter()
        node_total = 0
        time_rows_n = 0
        slot_rows_n = 0
        slot_vals = collections.Counter()
        time_scenes = set()
        time_confc = collections.Counter()
        time_famc = collections.Counter()
        for sid, (rows, info) in scenes.items():
            rows_total += len(rows)
            node_total += len(info["nodes"])
            for r in rows:
                opc[r["op"]] += 1
                confc[r["confidence"]] += 1
                if r.get("slot", "") != "":
                    slot_rows_n += 1
                    slot_vals[int(r["slot"])] += 1
                if r.get("time_ms", "") != "":
                    time_rows_n += 1
                    time_scenes.add(sid)
                    time_confc[r.get("time_conf", "")] += 1
                    time_famc[r.get("time_family", "")] += 1
        out["sources"][src] = dict(
            scenes=len(scenes), events=rows_total, nodes=node_total,
            op=dict(sorted(opc.items())), confidence=dict(sorted(confc.items())),
            replay=replay[src],
            compare=cmpst["by_source"].get(src, {}),
            v_task_self_consistency=_self_consistency(cmpst, src),
            psv_uncovered=sorted(sid for sid in scenes
                                 if not cmpst["per_scene"].get(src, {}).get(sid, {}).get("psv")),
            # 时间参数（v3）：**由已生成的行**统计（与 TSV 逐行一致），
            # 与 cmpst["time_rows"]（节点路径）互为独立复算。
            time=dict(rows=time_rows_n, scenes=len(time_scenes),
                      cover=round(len(time_scenes) / len(scenes), 4) if scenes else None,
                      conf=dict(sorted(time_confc.items())),
                      family=dict(sorted(time_famc.items()))),
            slot=dict(rows=slot_rows_n,
                      dist={str(k): v for k, v in sorted(slot_vals.items())}),
            # 命令节点判据收紧（v5 T1）：旧判据命中数 vs 收紧后留存数（差值 = 剔除量）
            map3=dict(nodes_classic=replay[src].get("nodes_classic", node_total),
                      nodes_kept=node_total,
                      nodes_removed=replay[src].get("nodes_classic", node_total) - node_total,
                      map3_backed=map3_backed),
        )
        # V→Tasktype 单源表
        rows = []
        for (s, V), n in cmpst["v_task_total"].items():
            if s != src:
                continue
            c = collections.Counter()
            for (s2, V2, t), m in cmpst["v_task"].items():
                if s2 == s and V2 == V:
                    c[t] += m
            top, topn = c.most_common(1)[0]
            rows.append(dict(V="0x%X" % V, n=n, task=top, hit=topn,
                             rate=round(topn / n, 4),
                             dist=dict(c.most_common(4))))
        rows.sort(key=lambda r: -r["n"])
        out["v_task_table"][src] = rows
    # 无 PSV 金标场的可操作覆盖（该 V 是否已在金标场上定名）+ 序数锚定统计
    named_by_src = collections.defaultdict(set)
    for (s, V), _n in cmpst["v_task_total"].items():
        named_by_src[s].add(V)
    for src, scenes in per_source.items():
        named = named_by_src.get(src, set())
        unc = {sid: info for sid, (r, info) in scenes.items()
               if not cmpst["per_scene"].get(src, {}).get(sid, {}).get("psv")}
        n_nodes = sum(len(i["nodes"]) for i in unc.values())
        n_named = sum(1 for i in unc.values() for nd in i["nodes"] if nd["V"] in named)
        n_ctrl = sum(1 for i in unc.values() for nd in i["nodes"] if nd["ctrl"])
        ord_scenes = [sid for sid, (r, info) in scenes.items()
                      if not info["mode"].startswith("field")]
        ord_rows = sum(len(scenes[sid][0]) for sid in ord_scenes)
        out["sources"][src]["uncovered_coverage"] = dict(
            scenes=len(unc), nodes=n_nodes, v_named=n_named,
            v_named_rate=round(n_named / n_nodes, 4) if n_nodes else None,
            nodes_with_control=n_ctrl,
            control_rate=round(n_ctrl / n_nodes, 4) if n_nodes else None)
        out["sources"][src]["seq_ordinal"] = dict(scenes=len(ord_scenes), rows=ord_rows)
    # 控制串
    for ctrl, c in cmpst["ctrl_v"].items():
        agg2 = {}
        for (s, V), n in c.items():
            k = "0x%X" % V
            agg2[k] = agg2.get(k, 0) + n      # 同 V 跨源要**求和**，不得覆盖
        out["ctrl_v"][ctrl] = agg2
    for ctrl, c in cmpst["ctrl_psv"].items():
        n = sum(c.values())
        out["ctrl_psv"][ctrl] = dict(n=n, top=dict(c.most_common(3)))
    for pi, cell in cmpst["time_argpos"].items():
        out["time_argpos"][str(pi)] = dict(hit=cell[0], total=cell[1],
                                           rate=round(cell[0] / cell[1], 4) if cell[1] else None)
    tn = cmpst["time_nodes"]
    out["time_nodes"] = dict(hit=tn[0], total=tn[1],
                             rate=round(tn[0] / tn[1], 4) if tn[1] else None)
    # ---- 时间参数（v3）族表命中 / 覆盖（说明.md §5.3 的数字来源）----
    #   口径：`seq` = 节点 seq 上有 PSV `time` 时，换算帧命中该 seq 任一 PSV time 的比例；
    #         `scene` = 换算帧 ∈ 本场 PSV time 集合的比例；`scenes` = 该族出现场数。
    tf_out = {}
    for src, fams in cmpst["time_family"].items():
        tf_out[src] = {}
        for name, c in sorted(fams.items()):
            tf_out[src][name] = dict(
                nodes=c["nodes"], ok=c["ok"], nonnum=c["nonnum"],
                out_of_range=c["out_of_range"], scenes=len(c["scenes"]),
                seq=dict(hit=c["seq"][0], total=c["seq"][1],
                         rate=round(c["seq"][0] / c["seq"][1], 4) if c["seq"][1] else None),
                scene=dict(hit=c["scene"][0], total=c["scene"][1],
                           rate=round(c["scene"][0] / c["scene"][1], 4) if c["scene"][1] else None))
    out["time_family"] = tf_out
    out["time_rows"] = {src: dict(rows=a["rows"], scenes=len(a["scenes"]))
                        for src, a in cmpst["time_rows"].items()}
    # 一致性自检（行路径 vs 节点路径）：两者必须一致，否则 `--check` 报错。
    # ⚠️ 两条路径**共用同一 `TIME_FAMILY`** ⇒ 对「族表本身写错」无鉴别力（只查两路是否同步）。
    out["time_rows_crosscheck"] = {
        src: dict(rows_from_rows=out["sources"][src]["time"]["rows"],
                  rows_from_nodes=out["time_rows"].get(src, {}).get("rows", 0),
                  agree=(out["sources"][src]["time"]["rows"]
                         == out["time_rows"].get(src, {}).get("rows", 0)))
        for src in out["sources"]}
    for ctrl, cell in cmpst["pos_strict"].items():
        out["pos_strict"][ctrl] = dict(hit=cell[0], total=cell[1],
                                       rate=round(cell[0] / cell[1], 4) if cell[1] else None)
    # 锚点
    for src in per_source:
        tbl = {int(r["V"], 16): r for r in out["v_task_table"].get(src, [])}
        aa = {}
        for v, nm in V_ANCHORS.items():
            r = tbl.get(v)
            aa["0x%X" % v] = dict(name=nm, n=(r["n"] if r else 0),
                                  task=(r["task"] if r else None),
                                  rate=(r["rate"] if r else None))
        out["anchors"][src] = aa
    # 全局自洽率
    out["v_task_self_consistency"] = _self_consistency(cmpst)
    return out


def main():
    ap = argparse.ArgumentParser(
        prog="decode_sob0.py",
        description="Lucifen SOB0 解码器（v5：容器 / 项流重放 / 命令节点识别（+maps[3] 背书）/ "
                    "控制串角色 / 时间参数族表 / Fade 载体 / V 定名 / PSV 金标对拍；"
                    "ISSUE-20261006-07 + v3 时间 + v5 落地）")
    ap.add_argument("--src", default="ot,otp,otr",
                    help="源（逗号分隔；可选 ot,otp,otr；默认全部）")
    ap.add_argument("--out", default=OUT_DEFAULT, help="产物目录（默认 编程组\\SOB0解码）")
    ap.add_argument("--stats", action="store_true", help="只打印统计 JSON，不落盘")
    ap.add_argument("--check", action="store_true",
                    help="只读幂等复核：重算与**盘面既有产物**逐字节比，绝不落盘")
    ap.add_argument("--no-emit", action="store_true", help="不写 解出_<源>.tsv")
    ap.add_argument("--no-map3", action="store_true",
                    help="关闭 maps[3] 背书（回到旧判据；**仅用于对照**，默认开启）")
    # ★ v7（ISSUE-20261007-11 T1）：导出**下游可消费**的「命令族标签」（只含已采纳 36＋载体）。
    #   与 `--check` 互斥：`--check` 是只读幂等复核，**绝不落盘**（本开关在 --check 下被忽略）。
    ap.add_argument("--emit-v-labels", default="",
                    help="额外导出「命令族标签」TSV（只含 verdict=采纳 的 V ＋ Fade 载体）；"
                         "默认不导出（不影响既有产物与 --check）")
    a = ap.parse_args()

    srcs = [s.strip() for s in a.src.split(",") if s.strip()]
    for s in srcs:
        if s not in SOURCES:
            raise SystemExit("!! 未知源 %r（可选 %s）" % (s, list(SOURCES)))

    ledger = Ledger(LEDGER)
    map3_backed = not a.no_map3
    per_source, replay, cmpst = build_all(srcs, a.out, ledger, map3_backed=map3_backed)
    st = render_stats(per_source, replay, cmpst, map3_backed=map3_backed)
    st["map3_backed"] = map3_backed

    if a.stats:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(st, ensure_ascii=False, indent=1))
        return 0

    if not a.check:
        os.makedirs(a.out, exist_ok=True)
    emitted = {}
    for src, scenes in per_source.items():
        all_rows = []
        for sid in sorted(scenes):
            all_rows.extend(scenes[sid][0])
        emitted[src] = all_rows
        # `--check` **只读**：绝不落盘（否则会「先写后比」变成空洞自检）
        if not a.no_emit and not a.check:
            write_tsv(os.path.join(a.out, "解出_%s.tsv" % src), all_rows)

    # 对账_逐场.tsv
    lines = ["scene_id\tsrc\tseq_mode\tpc_events\tnodes\tpc_ctrl_nodes\t"
             "psv_covered\tpsv_events\tseq_both\tseq_single\tverdict"]
    for src, scenes in per_source.items():
        psdet = cmpst["per_scene"].get(src, {})
        for sid in sorted(scenes):
            _, info = scenes[sid]
            d = psdet.get(sid, {})
            verdict = ("no_psv" if not d.get("psv")
                       else ("ok" if d.get("nodes") else "no_nodes"))
            lines.append("\t".join(map(str, [
                sid, src, info["mode"], d.get("pc_events", len(scenes[sid][0])),
                d.get("nodes", len(info["nodes"])), d.get("ctrl_nodes", ""),
                "1" if d.get("psv") else "0", d.get("psv_events", 0),
                d.get("seq_both", 0), d.get("seq_single", 0), verdict])))
    body = "\n".join(lines) + "\n"

    if a.check:
        # 幂等复核（**只读**：不写任何产物，未落盘时不 makedirs）：
        # 拿「内存重算结果」与**盘面既有产物**逐字节比（行尾规范化）。
        print("[--check] 只读模式：不写 解出_*.tsv / 对账_逐场.tsv / _stats.json")
        ok = True
        for src in per_source:
            p = os.path.join(a.out, "解出_%s.tsv" % src)
            if not os.path.isfile(p):
                print("!! [%s] 缺产物 %s" % (src, p))
                ok = False
                continue
            exp = "\t".join(HEADER) + "\n" + "".join(
                "\t".join(str(r[c]) for c in HEADER) + "\n"
                for r in emitted[src])
            if read_norm(p) != exp:
                print("!! [%s] 解出表幂等失败" % src)
                ok = False
            else:
                print("[%s] 解出表幂等 PASS（%d 行）" % (src, len(emitted[src])))
        with io.open(os.path.join(a.out, "_stats.json"), encoding="utf-8") as f:
            if json.load(f) != st:
                print("!! _stats.json 幂等失败")
                ok = False
            else:
                print("[_stats.json] 幂等 PASS")
        cc_bad = [src for src, cc in st["time_rows_crosscheck"].items()
                  if not cc["agree"]]
        if cc_bad:
            print("!! 时间行数 行路径 ≠ 节点路径：%s" % ",".join(cc_bad))
            ok = False
        else:
            print("[时间] 行路径 = 节点路径（一致性自检 PASS；"
                  "注意：两条路径共用同一 TIME_FAMILY，非独立复算）")
        print("ALL_PASS =", ok)
        return 0 if ok else 1

    # `对账_逐场.tsv` 使用自定义列头（非 9 列契约），故直接写文本
    with io.open(os.path.join(a.out, "对账_逐场.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write(body)
    with io.open(os.path.join(a.out, "_stats.json"), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)

    # ★ v7（ISSUE-20261007-11 T1）：导出「命令族标签」（只含已采纳 36 ＋ 载体 1）。
    #   这是**下游可消费**的形式（`build_story.py --fade-source lucifen` 读它定位 Fade 载体）。
    #   候选/未定**不在表内**——表本身就是「不得把候选当已定名」的闸门。
    _vl_rows = None
    if a.emit_v_labels:
        _n, _p = write_v_labels(a.emit_v_labels)
        _vl_rows = (_n, _p)

    sys.stdout.reconfigure(encoding="utf-8")
    print("=== 解码汇总（来源：解出_<源>.tsv / _stats.json）===")
    for src, s in st["sources"].items():
        print("[%s] %s" % (src, SOURCES[src]["note"]))
        print("   场 %d  事件 %d  命令节点 %d  op=%s"
              % (s["scenes"], s["events"], s["nodes"], s["op"]))
        rp = s["replay"]
        # 防御（v5.1）：数据根缺语料时 `replay` 只含 `err`，旧写法 `rp["heads"]` 会 KeyError。
        print("   项流：heads %d 矛盾 %d 回退 %d 未决 %d 末对齐 %d/%d"
              % (rp.get("heads", 0), rp.get("contradictions", 0),
                 rp.get("rollbacks", 0), rp.get("unresolved", 0),
                 rp.get("end_ok", 0), rp.get("files", 0)))
        if rp.get("err"):
            print("   （缺数据：%s）" % rp["err"])
        cm = s["compare"]
        print("   对拍：有金标场 %d  seq同时有PC+PSV %d  单任务seq %d"
              % (cm.get("scenes_with_psv", 0), cm.get("seq_both", 0),
                 cm.get("seq_single", 0)))
        tm = s["time"]
        print("   时间：行 %d  覆盖场 %d/%d（%s）  conf=%s"
              % (tm["rows"], tm["scenes"], s["scenes"], tm["cover"], tm["conf"]))
        sl = s.get("slot") or {}
        print("   槽位(slot)：行 %d  分布=%s" % (sl.get("rows", 0), sl.get("dist", {})))
        mg = s.get("map3") or {}
        print("   判据：classic %d → 留存 %d（maps[3] 剔除 %d）"
              % (mg.get("nodes_classic", 0), mg.get("nodes_kept", 0),
                 mg.get("nodes_removed", 0)))
        tf = st["time_family"].get(src, {})
        if tf:
            print("   族命中：" + "  ".join(
                "%s %d行 seq=%s scene=%s"
                % (nm, c["nodes"],
                   (c["seq"]["rate"] if c["seq"]["rate"] is not None else "-"),
                   (c["scene"]["rate"] if c["scene"]["rate"] is not None else "-"))
                for nm, c in sorted(tf.items())))
    sc = st["v_task_self_consistency"]
    # 保护（v5.1，一审 RV-LAND 提示②）：无 PSV 数据时 `rate` 为 None，
    # 旧写法 `"%.4f" % None` 会抛 TypeError。改为 None 时打印 "-"。
    print("命令身份 V→Tasktype 自洽率 %s（%d/%d）"
          % (("%.4f" % sc["rate"]) if sc["rate"] is not None else "-",
             sc["agree"], sc["total"]))
    print("命令节点判据：maps[3] 背书 = %s" % map3_backed)
    print("--- 命令载体登记 COMMAND_CARRIERS（v5 T2；不写「已解决」）---")
    for src, tbl in COMMAND_CARRIERS.items():
        for V, d in tbl.items():
            print("  [%s] 0x%X %s（ms 位 %d，precision %s / recall %s，反例 %d 场）"
                  % (src, V, d["name"], d["ms_idx"], d.get("precision"),
                     d.get("recall"), d["counterexamples"]))
            if d.get("adopt_basis"):
                print("       采纳依据：%s" % d["adopt_basis"])
    print("--- V 定名 V_NAMING（v6；未达阈值一律「未定」）---")
    for src, tbl in V_NAMING.items():
        n_add = sum(1 for d in tbl.values() if d.get("verdict") == "采纳")
        n_cand = sum(1 for d in tbl.values() if d.get("verdict") == "候选")
        print("  [%s] 登记 %d 项：采纳 %d / 候选 %d / 未定 %d"
              % (src, len(tbl), n_add, n_cand,
                 sum(1 for d in tbl.values() if d.get("verdict") == "未定")))
        for V, d in tbl.items():
            print("   0x%-6X %-32s [%s/%s] nodes=%s"
                  % (V, (d.get("name") or "(未定名)"), d.get("verdict"),
                     d.get("rule"), d.get("v_nodes")))
    print("--- 遮罩 Rule RULE_NAMING（v5 T4）---")
    print("  %s ← %s" % (RULE_NAMING["pattern"], RULE_NAMING["source"]))
    print("  数值→编号换算：%s" % RULE_NAMING["conversion"][:40] + "…")
    if _vl_rows is not None:
        _n, _p = _vl_rows
        _add = sum(1 for r in build_v_labels() if r["verdict"] == "采纳")
        print("--- 命令族标签导出（v7 T1；**只含已采纳**，候选/未定不导出）---")
        print("  行 %d（全部 verdict=采纳）→ %s" % (_add, _p))
        print("  其中 Fade 载体：%s"
              % "、".join("%s %s" % (r["src"], r["V"])
                          for r in build_v_labels() if r["carrier"]))
    print("产物目录 =", os.path.abspath(a.out))
    return 0


def _parse_tsv_lines(lines):
    return []


if __name__ == "__main__":
    sys.exit(main())
