#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
np（涅布＊普拉斯 / BGI-Ethornell）· **剧情脚本指令级（instruction-level）演出提取器**
================================================================================
ISSUE-20261006-07 ｜ 由 `资源组\演出\演出_np.tsv`（旧，常量池「首次引用位」级，560 行，全 inferred）
升级为「**逐调用点：命令名 + 有序字面操作数 + 资源令牌 + `.bs5` 源码行号**」。
ISSUE-20261007-01 ｜ 增量：把已解出的**参数语义**（33 命令元数 + N3 位置判定）落成
`演出_np_IL_语义.tsv`（14 列，分级「已定 / 部分已定 / 只能定元数 / 未定」），**不改** 9 列 IL 表口径。

本模块**只读**游戏脚本、语料、资源总账；**只写**本 checkout 的
`资源组\演出\np_IL\{演出_np_IL.tsv, 演出_np_IL_语义.tsv, 命令清单.tsv, 说明.md}`。
**不改** `build_staging_np.py` / `演出_np.tsv` / 主工作树 / `main`。

--------------------------------------------------------------------------------
复跑
--------------------------------------------------------------------------------
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_np_il.py"
    python -X utf8 "…/build_staging_np_il.py" --check      # 幂等：不落盘，逐字节比对四份产物

读 = `GRETA_DATA_ROOT`（默认 `E:\ZCode Workspace\Galgame`，见 `_staging_common.py`）；写 = 本 checkout。

--------------------------------------------------------------------------------
BGI v1 剧情字节码结构（**实测，ISSUE-20261006-07**）
--------------------------------------------------------------------------------
* 头：`magic` + `u32@0x1C` → **`hdrsize = 0x1C + u32@0x1C`（公式，不硬编码 0x40）**。
  实测 26 剧情脚本 + `start_oretuba` 为 `0x24` ⇒ 代码起 **0x40**；**`end_oretuba` 为 `0x34` ⇒ 代码起 0x50**。
* 指令 = **规整 u32 LE 词流**：`opcode`（1 词）+ 固定个数 `operand`（各 1 词）。
  本作实测操作数宽度表 `WIDTHS`（**26 个剧情脚本全流精确落位、0 未知 opcode**）：

      opcode  宽度(词)  语义（仅记「已证实」部分）
      0x00     2        push_dword(i32)      —— 字面整数
      0x01     2        push（入口/引用，语义未定）
      0x03     2        push_string(off)     —— off 为 **code 相对**（文件 = code_start + off）
      0x18     1        语义未定（单脚本至多 1 次，疑似 jmp）
      0x19     2        语义未定（仅尾声模板出现）
      0x1A     1        语义未定
      0x1B     1        语义未定（ret?）
      0x1C     1        **命令调用标记**（紧随 `push_string <命令名>`）
      0x20     1        语义未定（疑似 add）
      0x21     1        语义未定（疑似 sub）
      0x3F     2        nargs（值恒为实参个数；**非**命令参数元数）
      0x7F     3        语义未定（line?）
      0x140    1        **文本显示**（紧随 `push_string <台词/旁白>`）
      0xF0     1        语义未定
      0xF4     1        halt
      0xF6     1        **转场调用标记**（紧随 `push_string <转场名>`）
      0xF7     3        语义未定（固定尾声模板）
      0xF9     1        语义未定（固定尾声模板）
      0xFE     1        调用（与 `nargs` 组成「定参调用」）

* **代码区结束 = 字符串池起点**（**三级锚点，全不命中返回 None，不静默回退整文件**）：
  ① 首个 `b"D:\WORK"` 串（27/28，恒 `== 最后一个 word-aligned 0xF4 + 4`）；
  ② fallback：首个池文件名 `.bsc/.bs5/.h` NUL 串（`end_oretuba` → `End_Oretuba.bsc` @0x70C）；
  ③ fallback：最后一个 word-aligned `0xF4` + 4。脚本在此之后为 NUL 结尾 cp932 串池，非指令。

--------------------------------------------------------------------------------
语句文法（**本报告的核心实测结论**：参数在命令名**之前**）
--------------------------------------------------------------------------------
每条语句后跟一个**源码位置调用**（`push_string <*.bs5 路径>; push_dword <行号>; nargs 2; 0xFE`），
它以「位置调用」把语句切成段；段内是**实参表达式**，段末是 `push_string <命令名>; 0x1C`：

    [位置调用: push_str "…\\A01_B0.bs5"; push 23; nargs 2; 0xFE]
    [实参:      push 0; push_str "SE768"; push 128; push 64; push 0; push 500]
    [调用点:    push_str "_PlaySE"; 0x1C]
    [位置调用: push_str "…\\A01_B0.bs5"; push 25; nargs 2; 0xFE]

**第二种调用形态（转场）**：`push_str <转场名>; <push 字面>; 0xF6; 0xF0`（名字在前、实参在后）——
`a01_a0` 的 `FadeSS`、`a06_c0` 的 `End_Oretuba`。全库复查（26 剧情脚本）确认**只有这两种调用形态**
（`push_str <名字>` 后继 opcode 仅 `0x1C`/`0x03`/`0x00` 三档），且 `0xFE` 全部是位置调用。

**证据**（决定性反例，推翻「参数在命令名之后」的假说）：
1. 语音令牌紧邻其命令名**之前**：`a01_b0` 44 处 `push_str "ASU300xx"; … ; push_str "_PlayVoice"; 0x1C`；
2. 音效令牌同理：`a01_b0 @0x128 push_str "SE768"; 128;64;0;500` 后紧跟 `@0x150 push_str "_PlaySE"; 0x1C`；
3. （旁证，非决定性）`.bs5` 行号紧随命令之后、单调递增（…20,21,23,25…）——两种读法都成立，
   真正一致的旁证是文本行稳定形态 `push_str(台词); 0x140; 位置调用(file,line)`。
⇒ 因此本模块把「命令的有序字面操作数」定义为**命令名之前、上一位置调用之后**的 push 字面序列；
转场调用则取「转场名之后、`0xF6` 之前」的 push 字面序列。

--------------------------------------------------------------------------------
可达级别
--------------------------------------------------------------------------------
**达**：命令名/转场名 + 有序字面操作数（int/string）+ 资源令牌 + `.bs5` 源码行号 + 逐调用点计数；
**参数语义（ISSUE-20261007-01 起）**：33 条命令的**元数**（N1 三路互证，1643/1643）与**部分位置语义**
（N3：`_DrawBS` 的 x/y/x2/y2/alpha/时长、`_ScrollBG` 的起终点 x 与时长〔n=2 推定〕；N1 的 ms 位置）
—— 落在**新文件** `演出_np_IL_语义.tsv`（14 列），**不并入** 9 列 IL 方言表。
**未达（仍须专门 RE）**：zoom / angle / anchor 位（本作数据恒 0 或零星非 0，无判别力 ⇒ **判未定、不填**）；
`_MoveBS` 的 arg3 及 0x10000000/0x20000000 tag 族（**曾误判为目标 x，现撤回**——18 条里 17 条是 tag 编码）；
`0x1C/0xF6/0xFE/nargs/…` 的语义；`0xF6` 转场的跳转目标绑定。
**未定项一律留空并标「未定」，不得猜。**

--------------------------------------------------------------------------------
输出（四份，均写本 checkout 的 `资源组\演出\np_IL\`）
--------------------------------------------------------------------------------
* `演出_np_IL.tsv` —— 9 列（沿用逐行演出表契约表头；**op/confidence 属 IL 方言，见 说明.md 文首声明**）：
    `scene_id seq op target arg1 arg2 arg3 evidence confidence`
    · `op` = **命令名**（如 `_DrawBS`）**或转场名**（`FadeSS`/`End_Oretuba`）；`skip` 行仍为 `skip`
    · `target` = 该调用点首个命中资源总账的操作数 → `out_relpath`；无则空
    · `arg1..arg3` = 有序字面操作数的前三个（int 原样 / string 原样）
    · `evidence` = `script=…; file_off=0x…; op=0x1C/0xF6[ (transition)]; .bs5 line N; args=[完整有序字面表]; ops=[…]; res=[令牌→ok/unmatched]`
      —— **完整操作数表在 evidence**（「超出的用扩展说明」，见 说明.md §2）；`args` 是**未折叠原始字面**，长度与元数不对齐
    · `confidence` = `exact`（调用点与字面操作数**逐指令直读**，非池序推定）/ `unknown`（skip）
* `演出_np_IL_语义.tsv` —— 14 列参数语义（与 IL 表逐行一一对应（非 skip））：
    `scene_id seq 命令名 元数 x y x2 y2 时长ms alpha 其他已定位置 未定位置占位 evidence confidence`
    · 数值取自**与元数 1:1 对齐的折叠实参**（N1 口径）；**未定的位置留空并记入「未定位置占位」**
* `命令清单.tsv` —— `command  count  first_offset  first_scene`（全 26 剧情脚本聚合）
* `说明.md` —— 方法、参数语义分级（§四）、未知 opcode 占比、与旧表逐场差异、下一步
* `seq` 口径与 `演出表说明.md` §1.1 完全一致（见 `_staging_common.SeqMap` 语义）。
"""
from __future__ import annotations

import argparse
import bisect
import collections
import io
import json
import os
import re
import struct
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _staging_common as C      # noqa: E402  契约（Ledger / HEADER / assert_in_checkout / write_tsv）

SRC = "np"
NP_ARC = C.NP_ARC
SCENE_JSONL = os.path.join(C.RES, "剧本", "scene_np.jsonl")
OLD_TSV = os.path.join(C.RES_LOCAL, "演出", "演出_np.tsv")
OUT_DIR = os.path.join(C.RES_LOCAL, "演出", "np_IL")
TSV_OUT = os.path.join(OUT_DIR, "演出_np_IL.tsv")
SEM_OUT = os.path.join(OUT_DIR, "演出_np_IL_语义.tsv")
CMD_OUT = os.path.join(OUT_DIR, "命令清单.tsv")
DOC_OUT = os.path.join(OUT_DIR, "说明.md")

# 语义表（新，ISSUE-20261007-01）14 列；**独立文件**，不动 `演出_np_IL.tsv` 的 9 列 IL 方言。
SEM_HEADER = ["scene_id", "seq", "命令名", "元数",
              "x", "y", "x2", "y2", "时长ms", "alpha",
              "其他已定位置", "未定位置占位", "evidence", "confidence"]

MAGIC = b"BurikoCompiledScriptVer1.00"
HDR_SIZE_OFF = 0x1C                                   # hdrsize = 0x1C + u32@0x1C（**公式，不硬编码 0x40**）
WORK_MARK = b"D:" + bytes([92]) + b"WORK"
POOL_NAME_RE = re.compile(rb"[A-Za-z0-9_./\\-]+\.(?:bsc|bs5|h)\x00")   # 池首文件名（fallback 锚点）

# 操作数宽度表（**词数** = 1 opcode + n operand）。仅含已由「全流精确落位」证实的 opcode。
# 26 剧情脚本 + start_oretuba 用 0x40 起；end_oretuba 的 u32@0x1C=0x34 ⇒ 代码起 0x50（用公式，不硬编码）。
WIDTHS = {
    0x00: 2,   # push_dword(i32)
    0x01: 2,   # push(引用/入口，语义未定)
    0x03: 2,   # push_string(code 相对偏移)
    0x18: 1, 0x19: 2, 0x1A: 1, 0x1B: 1, 0x1C: 1,      # 0x1C = 命令分派
    0x20: 1, 0x21: 1, 0x3F: 2, 0x7F: 3, 0x140: 1,
    0xF0: 1, 0xF4: 1, 0xF6: 1, 0xF7: 3, 0xF9: 1, 0xFE: 1,   # 0xF6 = 转场分派
}
PUSH_DWORD, PUSH_STRING, CMDCALL, TEXTDISP = 0x00, 0x03, 0x1C, 0x140
TRANSITION, NARGS, CALL, HALT = 0xF6, 0x3F, 0xFE, 0xF4
CMD_RE = re.compile(r"^_[A-Za-z][A-Za-z0-9_]+$")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")         # 命令名 / 转场名「形」
RES_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")     # 资源令牌「形」：纯 ASCII 标识符
NUM_RE = re.compile(r"^[+-]?\d+$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{3,8}$")


# ================================================================ 参数语义模型
# （ISSUE-20261007-01 落库；依据 = N1「命令参数表.tsv」元数三路互证 + N3「drawbs_positions.tsv」位置判定）
#
# 元数（N1）：33 条命令的**声明元数**由 framework 导出函数序言槽数确定，并由
#   A 序言槽数 / B 调用点栈深+常量折叠实参 / C 形参→系统调用定义-使用链 三路互证一致
#   （1643/1643 调用点，逐命令×逐位置 kind/值域/反例见 N1「命令参数表.tsv」）。
# 位置语义（N3，**不依赖图元名**）：靠「槽位—坐标相关性 + 物理约束（中心原点下命中画布 1280×720）」判定。
#   ⚠️ zoom / angle / anchor 位在本作数据里恒 0 或仅零星非 0 ⇒ **无判别力，一律判未定、不得填**。
#   ⚠️ 0x10000000(268435456) 不是 16.16 的 1.0，是 tag1/payload0 的「绝对 0 / 不变」哨兵（N3 更正 N2 旧推测）。
#
# N1 逐位置 kind 序列（1-based；命令名 → kind 列表）。'ms' = 时长毫秒集；'index' = 小整数(槽位/通道/模式)；
# 'const' = 全调用点同值；'int' = 余下整数（语义未定）；'bool'/'color'/'str'/'tagged' 见 bgi_param_report.py 判据。
N1_KINDS = {
    "_PlayVoice": ["index", "str", "const", "const"],
    "_DrawBS": ["index", "str", "const", "const", "int", "int", "const", "bool",
                "int", "int", "const", "const", "const", "int", "const", "int",
                "int", "ms", "bool"],
    "_DrawScene": ["str", "const", "const", "index", "index", "int", "const", "ms", "const"],
    "_PlaySE": ["index", "str", "const", "const", "index", "const"],
    "_SetBustshotForSynchronizedFaceDrawing": ["str", "str"],
    "_PlayBGM": ["bool", "str", "str", "const", "const", "ms"],
    "_FadeBGM": ["bool", "ms", "const"],
    "_EyeCatchIn": ["str", "const", "const", "const"],
    "_SetTimeZone": ["bool"],
    "_Font": ["int", "const", "const"],
    "_Wait": ["ms", "const"],
    "_MoveBS": ["index", "const", "int", "const", "const", "int", "const", "int", "ms", "bool"],
    "_Flash": ["const", "const", "const", "index", "ms"],
    "_Quake": ["int", "index", "index"],
    "_FadeBS": ["index", "const", "const", "const", "const", "const", "const", "ms", "bool"],
    "_DrawFilm": ["index", "color", "const", "const", "const", "const"],
    "_StopSE": ["index"],
    "_FadeFilm": ["ms"],
    "_FadeSE": ["index", "ms"],
    "_PlayStreamSE": ["const", "str", "str", "const", "int", "const"],
    "_FadeScene": ["const", "const", "ms"],
    "_RecipBS": ["index", "tagged", "const", "ms"],
    "_ShakeBS": ["index", "index", "index", "index", "const"],
    "_StopStreamSE": ["const"],
    "_DrawBG": ["str", "const", "const", "const", "const", "const", "const", "const"],
    "_WaveBG": ["const"] * 9,
    "_StopBGM": ["const"],
    "_ScrollBG": ["int", "int", "const", "const", "int", "const", "const"],
    "_WaitToFinishBGControlling": ["const"],
    "_FadeStreamSE": ["const", "const", "const"],
    "_QuakeEx": ["const"] * 6,
    "_StopQuakingEx": ["const", "const"],
    "_StopShakingBS": ["const", "const", "const"],
}

# 核心语义列已定的位置（1-based 位置 → 列名）。仅含**有判别力且经物理验证**的判定。
CORE_POS = {
    # N3：x=arg5 / y=arg6 / x2=arg9 / y2=arg10（移动目标）/ alpha=arg16 / 时长=arg18
    "_DrawBS": {5: "x", 6: "y", 9: "x2", 10: "y2", 16: "alpha", 18: "ms"},
    # N3 只覆盖 _DrawBS，对 _MoveBS **无正式判定**：arg3 虽是唯一变化位，但 18 条里 17 条是 tag 编码
    # （0x10000000 族 11 条、0x20000000 族 6 条，其中 4 条恰为哨兵本体 268435456），只有 1 条是普通坐标 1000
    # ⇒ **判定撤回，不作 x**（arg3 降级为「候选/未定」，原始 tag 值仍留在 evidence 的 args）；只保留 arg9=时长 ms。
    "_MoveBS": {9: "ms"},
    # N3：起/终点 x + 时长 ms（arg5 虽被判 int，值域 1500..4000 即毫秒时长）；n=2 样本偏小，见 CONF_OVERRIDE
    "_ScrollBG": {1: "x", 2: "x2", 5: "ms"},
}

# 小样本/推定命令的 confidence 覆写（不再标满格「已定」）
CONF_OVERRIDE = {
    "_ScrollBG": "部分已定(x/x2/时长;n=2,推定)",
}

# 其他**具名**已定位置（N3「drawbs_positions.tsv」）。未具名者按 kind 记入类型标签或未定。
NAMED_POS = {
    "_DrawBS": {1: "角色槽位", 2: "立绘令牌",
                3: "体型/模式组(恒0,推定)", 4: "体型/服装组(恒2,推定,低)",
                8: "移动标志", 19: "并行标志"},
}

# kind → 「其他已定位置」的类型标签（只表类型，不含坐标语义）
KIND_LABEL = {"index": "枚举索引(index)", "str": "令牌/名称(str)", "bool": "开关(bool)",
              "color": "颜色(color)", "tagged": "带符号偏移族(tagged)"}
# kind ∈ 此集合且非核心/具名 ⇒ **语义未定**（含 zoom/angle/anchor 候选、`_MoveBS` 的 tag/哨兵位）。
UNDET_KINDS = ("int", "const", "mixed")

# 时长位置（命令 → (1-based 位置, N1 实测值域)）；供 说明.md §4.3 表
MS_RANGE = {
    "_DrawBS": (18, "[0,500]"), "_DrawScene": (8, "[0,1000]"), "_PlayBGM": (6, "[0,2000]"),
    "_FadeBGM": (2, "[300,2000]"), "_Wait": (1, "[200,500]"), "_MoveBS": (9, "[50,500]"),
    "_Flash": (5, "[50,200]"), "_FadeBS": (8, "[0,300]"), "_FadeFilm": (1, "[0,1000]"),
    "_FadeSE": (2, "[100,1000]"), "_FadeScene": (3, "[1000,2000]"), "_RecipBS": (4, "[100,200]"),
    "_ScrollBG": (5, "[1500,4000]"),
}


def _roles(cmd, kinds):
    """→ (core{pos:col}, other{pos:label}, undet[pos])。"""
    core = dict(CORE_POS.get(cmd, {}))
    named = NAMED_POS.get(cmd, {})
    other, undet = collections.OrderedDict(), []
    for pos, k in enumerate(kinds, 1):
        if pos in core:
            continue
        if pos in named:
            other[pos] = named[pos]
            continue
        if k == "ms":
            core[pos] = "ms"          # N1 判据：取值 ⊆ 毫秒集 ⇒ 时长
            continue
        if k in KIND_LABEL:
            other[pos] = KIND_LABEL[k]
        else:
            undet.append(pos)
    return core, other, undet


def _sem_confidence(cmd, kind, core, other):
    if kind != "cmd":
        return "未定"
    if cmd in CONF_OVERRIDE:
        return CONF_OVERRIDE[cmd]
    cols = set(core.values())
    if "x" in cols:
        parts = [c for c in ("x", "y", "x2", "y2", "alpha") if c in cols]
        if "ms" in cols:
            parts.append("时长")
        return "已定(%s)" % "/".join(parts)
    if cols:                          # 仅时长
        return "部分已定(时长)"
    if other:
        return "部分已定(类型)"
    return "只能定元数"



def _z(v):
    """字段清洗：TAB/CR/LF → 空格（TAB 分隔 + 无引号 ⇒ 字段内不得含分隔符）。"""
    return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")


# ================================================================ 解码
def u32(d, off):
    return struct.unpack_from("<I", d, off)[0]


def s32(d, off):
    return struct.unpack_from("<i", d, off)[0]


def cstr(d, off, limit=None):
    """从 off 取 NUL 结尾串（cp932）；越界/空返回 None。"""
    n = len(d)
    if not (0 <= off < n - 1):
        return None
    end = d.find(b"\x00", off)
    if end <= off:
        return None
    try:
        return d[off:end].decode("cp932")
    except UnicodeDecodeError:
        return None


def code_start(d):
    """代码起点 = hdrsize = 0x1C + u32@0x1C（**公式**；`end_oretuba` 为 0x50，其余 0x40）。"""
    if d[:len(MAGIC)] != MAGIC:
        raise SystemExit("!! 非 BGI v1 脚本（magic 不符）")
    return HDR_SIZE_OFF + u32(d, HDR_SIZE_OFF)


def code_end(d, cs):
    """代码区结束 = 字符串池起点；**三级锚点**，全不命中返回 None（不静默回退整文件）。

    1. 首个 `b"D:\\WORK"` 串（27/28 脚本，恒 == 末 word-aligned `0xF4` + 4）；
    2. fallback：首个池文件名 `.bsc/.bs5/.h` NUL 串（`end_oretuba` → `End_Oretuba.bsc` @0x70C）；
    3. fallback：最后一个 word-aligned `0xF4`(halt) + 4。
    """
    n = len(d)
    ce = d.find(WORK_MARK, cs)
    if ce < 0:
        m = POOL_NAME_RE.search(d, cs)
        if m:
            ce = m.start()
    if ce < 0:
        last = None
        for pos in range(cs, n - 3, 4):
            if u32(d, pos) == HALT:
                last = pos
        ce = (last + 4) if last is not None else -1
    if ce < 0:
        return None
    ce = min(ce, n - 4)
    return cs + ((ce - cs) // 4) * 4


def decode(d):
    """指令流解码。返回 (instructions, unknown, code_start, code_end)。

    instruction = dict(off, op, args, string)
        off    —— 文件绝对偏移
        op     —— opcode 值
        args   —— 操作数原始 u32 列表
        string —— 若 op==0x03，code 相对偏移所指的 cp932 串
    unknown = [(off, opcode, [next3 words])]，**明确报出，不静默跳过**。
    code_end 无法锚定时返回 ([], [], cs, None)。
    """
    cs = code_start(d)
    ce = code_end(d, cs)
    if ce is None:
        return [], [], cs, None
    ins, unknown = [], []
    pos = cs
    while pos < ce:
        op = u32(d, pos)
        off = pos
        if op in WIDTHS:
            w = WIDTHS[op]
        else:
            unknown.append((pos, op, [u32(d, pos + 4 * k) if pos + 4 * k + 4 <= ce else 0
                                      for k in range(1, 4)]))
            w = 1
        args = [u32(d, pos + 4 * k) for k in range(1, w)]
        st = None
        if op == PUSH_STRING and args:
            st = cstr(d, cs + args[0])
        ins.append({"off": off, "op": op, "args": args, "string": st})
        pos += 4 * w
    return ins, unknown, cs, ce


def is_poscall(ins, b):
    """ins[b] 是否为『源码位置调用』末尾的 0xFE。位置调用 = push_str(*.bs5); push_dword; nargs; 0xFE。"""
    return (b >= 3 and ins[b]["op"] == CALL and ins[b - 1]["op"] == NARGS
            and ins[b - 2]["op"] == PUSH_DWORD and ins[b - 3]["op"] == PUSH_STRING
            and (ins[b - 3]["string"] or "").endswith(".bs5"))


def next_srcline(ins, start):
    """自 start 起，第一个『位置调用』的 `.bs5` 行号；无则 None。"""
    for m in range(start, len(ins) - 3):
        if (ins[m]["op"] == PUSH_STRING and (ins[m]["string"] or "").endswith(".bs5")
                and ins[m + 1]["op"] == PUSH_DWORD and ins[m + 2]["op"] == NARGS
                and ins[m + 3]["op"] == CALL):
            return struct.unpack("<i", struct.pack("<I", ins[m + 1]["args"][0]))[0]
    return None


# ---------------------------------------------------------------- 常量折叠取参（N1 口径）
# IL 表 9 列的 `args=[…]` 是**原始字面操作数**（0x21 之类的算子单独记 ops），长度与声明元数**不对齐**
# （如 _DrawBG 原始字面 10 个、声明 8 个）。参数语义表必须用**与元数 1:1 对齐的折叠实参**：
# 与 N1 `bgi_argvals.py::fold` 同口径（对实参段做常量折叠，sub/add… 折成单值），
# 实测与 N1 `_args_exact.json` **33 命令全部逐点相同**（见 说明.md §四）。
_EXPR = ({0x00, 0x01, 0x02, 0x03} | {0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x29, 0x2A, 0x2B}
         | {0x28, 0x3A} | {0x10, 0x11})
_BIN = {0x20: "add", 0x21: "sub", 0x22: "mul", 0x23: "div", 0x24: "mod",
        0x25: "and", 0x26: "or", 0x27: "xor", 0x29: "shl", 0x2A: "shr", 0x2B: "sar"}
_UN = {0x28: "not", 0x3A: "zero"}


def fold_operands(seg, d):
    """实参段（有序 ins）→ 与元数 1:1 对齐的折叠实参值表。非字面量以字符串标记。"""
    st = []
    for x in seg:
        op = x["op"]
        if op == PUSH_DWORD:
            st.append(s32(d, x["off"] + 4))
        elif op == PUSH_STRING:
            st.append(x["string"])
        elif op == 0x02:
            st.append("BASE+%d" % x["args"][0])
        elif op == 0x01:
            st.append("CODE@%d" % x["args"][0])
        elif op == 0x08:
            st.append("LOAD")
        elif op in _BIN:
            if len(st) >= 2:
                b, a, nm = st.pop(), st.pop(), _BIN[op]
                if isinstance(a, int) and isinstance(b, int):
                    if nm == "add":
                        st.append(a + b)
                    elif nm == "sub":
                        st.append(a - b)
                    elif nm == "mul":
                        st.append(a * b)
                    elif nm == "div":
                        st.append(a // b if b else 0)
                    elif nm == "mod":
                        st.append(a % b if b else 0)
                    elif nm == "and":
                        st.append(a & b)
                    elif nm == "or":
                        st.append(a | b)
                    elif nm == "xor":
                        st.append(a ^ b)
                    elif nm == "shl":
                        st.append(a << b)
                    else:                      # shr / sar
                        st.append(a >> b)
                else:
                    st.append("(%s %s %s)" % (a, nm, b))
            elif st:
                st.append("OP%s" % op)
        elif op in _UN:
            if st:
                a = st.pop()
                st.append(("~%s" % a) if _UN[op] == "not" else ("!%s" % a))
        elif op in (0x10, 0x11):
            st.append("BASE")
        else:
            st.append("?%X" % op)
    return st



# ================================================================ 资源令牌
class Resolver:
    """操作数串 → 分类：ok / path / cmd / nonres / unmatched。"""

    def __init__(self, ledger):
        self.led = ledger

    def classify(self, s):
        if not s:
            return ("nonres", None, None)
        if s.startswith("D:") or s.endswith(".bs5"):
            return ("path", None, None)
        if CMD_RE.match(s):
            return ("cmd", None, None)
        if NUM_RE.match(s) or COLOR_RE.match(s) or s in ("NULL", "Null"):
            return ("nonres", None, None)
        for kind in ("chr", "pic", "se", "bgm", "movie", "voice"):
            rel = self.led.target(kind, s, SRC)
            if rel:
                return ("ok", kind, rel)
        if RES_TOKEN_RE.match(s) and len(s) >= 2:
            return ("unmatched", None, None)
        return ("nonres", None, None)


# ================================================================ 提取
def _sem_row(sc, scene_id, seq, name, kind, anchor_off, srcline, seg, d):
    """构建语义表一行（14 列）。seg = 折叠实参所在的实参段（有序 ins）。"""
    line_txt = srcline if srcline is not None else "-"
    if kind != "cmd":
        return collections.OrderedDict([
            ("scene_id", _z(scene_id)), ("seq", int(seq)), ("命令名", _z(name)),
            ("元数", "未定"), ("x", ""), ("y", ""), ("x2", ""), ("y2", ""),
            ("时长ms", ""), ("alpha", ""), ("其他已定位置", ""),
            ("未定位置占位", "全部未定（0xF6 转场调用，元数与语义均未定）"),
            ("evidence", "script=%s; file_off=0x%06X; op=0xF6 (transition); .bs5 line %s"
                         % (sc, anchor_off, line_txt)),
            ("confidence", "未定"),
        ])
    kinds = N1_KINDS.get(name)
    if kinds is None:      # 未纳入 N1 模型的命令 ⇒ 不得静默编造元数/位置
        raise SystemExit("!! [%s] 命令 %s 不在 N1 参数模型内（元数未定），拒绝产出语义行" % (sc, name))
    folded = fold_operands(seg, d)
    if len(folded) != len(kinds):
        raise SystemExit("!! [%s] %s 折叠实参 %d 个 != N1 声明元数 %d（折叠口径漂移）"
                         % (sc, name, len(folded), len(kinds)))
    core, other, undet = _roles(name, kinds)
    out = collections.OrderedDict([("scene_id", _z(scene_id)), ("seq", int(seq)),
                                   ("命令名", _z(name)), ("元数", len(kinds))])
    for col, key in (("x", "x"), ("y", "y"), ("x2", "x2"), ("y2", "y2"),
                     ("时长ms", "ms"), ("alpha", "alpha")):
        pos = next((p for p, c in core.items() if c == key), None)
        out[col] = "" if pos is None else _z(folded[pos - 1])
    out["其他已定位置"] = "; ".join("arg%d=%s" % (p, r) for p, r in sorted(other.items()))
    out["未定位置占位"] = ",".join("arg%d" % p for p in undet)
    ev = ("script=%s; file_off=0x%06X; op=0x1C; .bs5 line %s; argc=%d; args=[%s]"
          % (sc, anchor_off, line_txt, len(kinds), ", ".join(_z(v) for v in folded)))
    out["evidence"] = _z(ev)
    out["confidence"] = _sem_confidence(name, kind, core, other)
    return out


def extract_scene(led, resolver, scene):
    """返回 (rows, stats)。rows 为该场景的 IL 行 / skip 行。"""
    sc = scene["script"]
    path = os.path.join(NP_ARC, sc)
    if not os.path.isfile(path):
        raise SystemExit("!! 脚本缺失：%s" % path)
    d = open(path, "rb").read()
    if d[:len(MAGIC)] != MAGIC:
        raise SystemExit("!! [%s] 非 BGI v1 脚本（magic 不符）" % sc)
    ins, unknown, cs, ce = decode(d)
    last = ins[-1] if ins else None
    landed = bool(last) and ce is not None and (last["off"] + 4 * WIDTHS.get(last["op"], 1) == ce)
    st = {"script": sc, "scene_id": scene["scene_id"], "instr": len(ins),
          "unknown": len(unknown), "landed": landed, "code_start": cs, "code_end": ce,
          "hdr_u32": u32(d, HDR_SIZE_OFF),
          "unknown_vals": collections.Counter(v for _o, v, _c in unknown),
          "unknown_ctx": unknown[:50]}
    if ce is None:
        rows = [_skip_row(scene, "code_end 无锚点（无 D:\\WORK、无池文件名 .bsc/.bs5/.h、无 word-aligned 0xF4）"
                                 "⇒ 代码区边界未定，不解码")]
        return rows, st

    jp = [l["jp"] for l in scene["lines"] if l.get("jp")]
    line_seq = [l["seq"] for l in scene["lines"] if l.get("jp")]
    idx = 0
    tslots = []          # [(instr_index, file_off, seq)]
    for i, x in enumerate(ins):
        if x["op"] == PUSH_STRING and idx < len(jp) and x["string"] == jp[idx]:
            tslots.append((i, x["off"], line_seq[idx]))
            idx += 1
    st["text_slots"] = idx
    if idx != len(jp):
        raise SystemExit("!! [%s] 文本槽守恒失败：指令序匹配 %d / 期望 %d" % (sc, idx, len(jp)))

    # 全库复查用：0xFE 计数、名字 push 的后继 opcode 分布（区分命令名/资源名）
    foll = collections.Counter()
    for i, x in enumerate(ins):
        if (x["op"] == PUSH_STRING and x["string"] and NAME_RE.match(x["string"])
                and not x["string"].endswith(".bs5")):
            nxt = ins[i + 1]["op"] if i + 1 < len(ins) else -1
            foll[(1 if CMD_RE.match(x["string"]) else 0, nxt)] += 1
    st["fe_count"] = sum(1 for x in ins if x["op"] == CALL)
    st["follow"] = foll

    anchors = [i for i, x in enumerate(ins)
               if x["op"] == PUSH_STRING and x["string"] and CMD_RE.match(x["string"])
               and i + 1 < len(ins) and ins[i + 1]["op"] == CMDCALL]
    st["anchors"] = len(anchors)

    # 转场调用：`push_str <转场名>; <push 字面>; 0xF6`（**非** 0x1C 分派；如 FadeSS / End_Oretuba）
    trans = []
    for i, x in enumerate(ins):
        if x["op"] != TRANSITION:
            continue
        j = i - 1
        while j >= 0 and ins[j]["op"] in (PUSH_DWORD, PUSH_STRING):
            if ins[j]["op"] == PUSH_STRING:
                break
            j -= 1
        if (j >= 0 and ins[j]["op"] == PUSH_STRING and ins[j]["string"]
                and NAME_RE.match(ins[j]["string"]) and not CMD_RE.match(ins[j]["string"])
                and not ins[j]["string"].endswith(".bs5")):
            trans.append((j, i))
    st["transitions"] = len(trans)

    callsites = ([(k, "cmd", k + 1) for k in anchors]
                 + [(j, "transition", i) for (j, i) in trans])
    callsites.sort()
    st["callsites"] = len(callsites)

    # 文本槽（按 file_off）供 seq 二分
    ts_off = [o for _i, o, _s in tslots]
    ts_seq = [s for _i, _o, s in tslots]
    last_seq = ts_seq[-1] if ts_seq else None

    def seq_for(off):
        if not ts_seq:
            return None, "no_text"
        j = bisect.bisect_right(ts_off, off)
        if j >= len(ts_seq):
            return last_seq, "after_last_line"
        return ts_seq[j], ("before_first_line" if j == 0 else None)

    rows = []
    if unknown:
        # 解析未完整（宽度表不覆盖本脚本的 opcode 族）⇒ 不产出可能错位的调用点，如实 skip 并登记未知量。
        rows.append(_skip_row(
            scene, "菜单/控制脚本；指令表不覆盖本脚本 opcode 族（未知 opcode %d 处），不产出可能错位的调用点"
                   % len(unknown)))
        return rows, st
    if not callsites:
        rows.append(_skip_row(scene, "脚本无命令/转场调用点（菜单/控制脚本）"))
        return rows, st
    if not tslots:
        rows.append(_skip_row(scene, "0 文本行（无 lines[].seq 可锚定）"))
        return rows, st

    for name_idx, kind, disp_idx in callsites:
        name = ins[name_idx]["string"]
        anchor_off = ins[name_idx]["off"]
        lits, ops, res = [], [], []
        if kind == "cmd":
            b = name_idx - 1
            while b >= 0 and not is_poscall(ins, b):
                b -= 1
            rng = range(b + 1, name_idx)
            seg = ins[(b + 1):name_idx]
        else:
            rng = range(name_idx + 1, disp_idx)
            seg = ins[(name_idx + 1):disp_idx]
        for m in rng:
            x = ins[m]
            if x["op"] == PUSH_STRING:
                lits.append(_z(x["string"]))
            elif x["op"] == PUSH_DWORD:
                lits.append(_z(s32(d, x["off"] + 4)))
            elif x["op"] in (0x20, 0x21):
                ops.append("add" if x["op"] == 0x20 else "sub")
            else:
                ops.append("0x%X" % x["op"])
        # 资源分类
        target = ""
        for s in lits:
            status, kind2, rel = resolver.classify(s)
            if status == "ok":
                res.append("%s->%s ok" % (s, kind2))
                if not target:
                    target = rel
            elif status == "unmatched":
                res.append("%s->unmatched" % s)
        srcline = next_srcline(ins, disp_idx + 1)
        seq, tag = seq_for(anchor_off)
        ev = "script=%s; file_off=0x%06X; op=0x%X%s; .bs5 line %s; args=[%s]" % (
            sc, anchor_off, CMDCALL if kind == "cmd" else TRANSITION,
            "" if kind == "cmd" else " (transition)", srcline if srcline is not None else "-",
            ", ".join(lits))
        if ops:
            ev += "; ops=[%s]" % ",".join(ops)
        if res:
            ev += "; res=[%s]" % "; ".join(res)
        if tag in ("before_first_line", "after_last_line"):
            ev += "; %s" % tag
        row = collections.OrderedDict([
            ("scene_id", _z(scene["scene_id"])), ("seq", int(seq)), ("op", _z(name)),
            ("target", _z(target)), ("arg1", lits[0] if len(lits) > 0 else ""),
            ("arg2", lits[1] if len(lits) > 1 else ""), ("arg3", lits[2] if len(lits) > 2 else ""),
            ("evidence", _z(ev)), ("confidence", "exact"),
        ])
        row["_sem"] = _sem_row(sc, scene["scene_id"], seq, name, kind, anchor_off,
                               srcline, seg, d)          # 语义表（14 列），build() 取出后另存
        rows.append(row)
    return rows, st


def _skip_row(scene, reason):
    sc = scene["script"]
    return collections.OrderedDict([
        ("scene_id", scene["scene_id"]), ("seq", 0), ("op", "skip"),
        ("target", ""), ("arg1", reason), ("arg2", ""), ("arg3", ""),
        ("evidence", "script=%s; %s" % (sc, reason)), ("confidence", "unknown"),
    ])


# ================================================================ 旧表对照
def load_old():
    """旧 演出_np.tsv → ({scene_id: 行数}, {scene_id: {target tokens}})。"""
    per, toks = collections.Counter(), collections.defaultdict(set)
    if not os.path.isfile(OLD_TSV):
        return per, toks
    with io.open(OLD_TSV, encoding="utf-8", newline="") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) != len(head):
                continue
            r = dict(zip(head, p))
            per[r["scene_id"]] += 1
            if r.get("target"):
                toks[r["scene_id"]].add(os.path.splitext(os.path.basename(r["target"]))[0].upper())
    return per, toks


# ================================================================ 构建
def build():
    ledger = C.Ledger.load()
    resolver = Resolver(ledger)
    scenes = [json.loads(ln) for ln in io.open(SCENE_JSONL, encoding="utf-8") if ln.strip()]
    all_rows, stats_scenes = [], []
    for scene in scenes:
        rows, st = extract_scene(ledger, resolver, scene)
        all_rows.extend(rows)
        stats_scenes.append(st)

    order = {o["scene_id"]: n for n, o in enumerate(scenes)}
    all_rows.sort(key=lambda r: (order[r["scene_id"]],
                                 r["seq"] if r["op"] != "skip" else -1,
                                 r["evidence"]))
    # 取出语义行（与 IL 表**同一排序**），并把 `_sem` 从 IL 行上摘除
    # —— IL 表 9 列是契约方言，`write_tsv` 的列闸门要求键集恰为 HEADER，故必须摘净。
    sem_rows = []
    for r in all_rows:
        s = r.pop("_sem", None)
        if s is not None:
            sem_rows.append(s)
    return all_rows, sem_rows, stats_scenes, ledger


# ================================================================ 序列化
def serialize_tsv(rows):
    out = ["\t".join(C.HEADER)]
    for r in rows:
        out.append("\t".join(str(r[c]) for c in C.HEADER))
    return ("\n".join(out) + "\n").encode("utf-8")


def serialize_cmd(cmds):
    out = ["command\tcount\tfirst_offset\tfirst_scene"]
    for name in sorted(cmds, key=lambda k: (-cmds[k]["count"], k)):
        c = cmds[name]
        out.append("%s\t%d\t0x%06X\t%s" % (name, c["count"], c["first_offset"], c["first_scene"]))
    return ("\n".join(out) + "\n").encode("utf-8")


def serialize_sem(sem_rows):
    out = ["\t".join(SEM_HEADER)]
    for r in sem_rows:
        out.append("\t".join(str(r[c]) for c in SEM_HEADER))
    return ("\n".join(out) + "\n").encode("utf-8")


def cmd_inventory(rows):
    cmds = collections.OrderedDict()
    for r in rows:
        if r["op"] == "skip":
            continue
        name = r["op"]
        if name not in cmds:
            off = int(re.search(r"file_off=0x([0-9A-F]+)", r["evidence"]).group(1), 16)
            cmds[name] = {"count": 0, "first_offset": off, "first_scene": r["scene_id"]}
        cmds[name]["count"] += 1
    return cmds


# ================================================================ 说明.md
def build_doc(rows, sem_rows, stats_scenes, ledger):
    old_per, old_toks = load_old()
    scenes = [json.loads(ln) for ln in io.open(SCENE_JSONL, encoding="utf-8") if ln.strip()]
    by_scene = collections.defaultdict(list)
    for r in rows:
        by_scene[r["scene_id"]].append(r)
    new_toks = collections.defaultdict(set)
    for r in rows:
        m = re.search(r"res=\[([^\]]*)\]", r["evidence"])
        if not m:
            continue
        for item in m.group(1).split("; "):
            mm = re.match(r"(\S+)->(\w+) ok$", item)
            if mm:
                rel = ledger.target(mm.group(2), mm.group(1), SRC)
                if rel:
                    new_toks[r["scene_id"]].add(
                        os.path.splitext(os.path.basename(rel))[0].upper())

    tot_instr = sum(s["instr"] for s in stats_scenes)
    tot_unk = sum(s["unknown"] for s in stats_scenes)
    tot_anchor = sum(s["anchors"] for s in stats_scenes)

    L = []
    A = L.append
    A("# np（涅布＊普拉斯 · BGI/Ethornell）· 剧情脚本**指令级**演出提取 · 说明")
    A("")
    A("- Issue：`ISSUE-20261006-07`（9 列 IL 表）→ 增量 `ISSUE-20261007-01`（参数语义表）"
      " ｜ 生成器：`资源组\\工具\\build_staging_np_il.py` ｜ 产物目录：`资源组\\演出\\np_IL\\`")
    A("- 定位：把旧 `资源组\\演出\\演出_np.tsv`（常量池**首次引用位**级，560 行、全 `inferred`）")
    A("  升级为**逐调用点指令级**：命令名 + 有序字面操作数 + 资源令牌 + `.bs5` 源码行号。")
    A("- **只读**游戏脚本 / 语料 / 资源总账；**只写**本目录；**不改** `build_staging_np.py` / `演出_np.tsv` / 主工作树。")
    A("- ISSUE-20261007-01 起**新增** `演出_np_IL_语义.tsv`（14 列，参数语义分级），与原 9 列 IL 表**逐行一一对应（非 skip）**；")
    A("  原 `演出_np_IL.tsv` 的 9 列口径**不变**（仍是 IL 方言）。")
    A("")
    A("> ## ⚠️ 方言声明（**请下游先读**）")
    A("> 本表**复用逐行演出表的 9 列表头**（`scene_id seq op target arg1 arg2 arg3 evidence confidence`），")
    A("> 但**不适用** `演出表说明.md` 的两处口径，属**指令级（IL）方言**，下游**不得按契约枚举校验**：")
    A("> 1. **`op` 不是契约 §1.3 的 12 值闭集**——本表 `op` ＝**原始命令名/转场名**（`_PlayVoice`…，共 %d 个），"
      % len(cmd_inventory(rows)))
    A(">    全在契约闭集之外；")
    A("> 2. **`confidence` 不是契约 §1.4 的 (scene_id,seq,target) 三元组证据强度**——本表 `confidence=exact`")
    A(">    仅指「调用点 + 字面操作数」**逐指令直读**（非池序推定）。")
    A("> 3. 契约件 `演出_np.tsv` 原样未动；本表是新文件 `演出_np_IL.tsv`，**不是**它的替代或覆盖。")
    A("> 4. **参数语义不在 9 列 IL 表**，而在新文件 `演出_np_IL_语义.tsv`（见 §四）——9 列 IL 表的")
    A(">    `args=[…]` 是**未折叠的原始字面操作数**（长度与元数**不对齐**），**不可**当元数对齐的实参读。")
    A("")
    A("---")
    A("")
    A("## 〇 一页速览")
    A("")
    A("| 指标 | 值 |")
    A("| --- | ---: |")
    A("| 场景 | %d（26 剧情 + 2 菜单 `skip`） |" % len(scenes))
    A("| 调用点（IL 行） | **%d**（含 **%d** 条 `0xF6` 转场调用） |"
      % (len(rows) - sum(1 for r in rows if r["op"] == "skip"),
         sum(s.get("transitions", 0) for s in stats_scenes)))
    A("| 唯一名字（命令 + 转场） | %d |" % len(cmd_inventory(rows)))
    A("| 解析指令总词数 | %d |" % tot_instr)
    A("| **未知 opcode 出现数 / 占比** | **%d / %.5f%%** |" % (tot_unk, 100.0 * tot_unk / max(tot_instr, 1)))
    A("| 旧表行数 | %d |" % sum(old_per.values()))
    _cc = collections.Counter(s["confidence"] for s in sem_rows)
    A("| **参数语义表行数**（`演出_np_IL_语义.tsv`） | **%d**（与 IL 非 skip 行一一对应） |" % len(sem_rows))
    A("| 语义级别分布 | %s |"
      % "；".join("%s %d" % (k, _cc[k]) for k in sorted(_cc, key=lambda x: -_cc[x])))
    A("| 含 x 列 / 含 y 列 的调用点 | %d / %d |"
      % (sum(1 for s in sem_rows if s["x"] != ""), sum(1 for s in sem_rows if s["y"] != "")))
    A("")
    A("**一句话**：26 个剧情脚本的指令流**全流精确落位、0 未知 opcode**，逐调用点产出 %d 行"
      "（含 2 条 `0xF6` 转场调用）；未知 opcode **全部落在 2 个菜单/控制脚本**，本表对这两场如实 `skip` 并登记"
      "（`start_oretuba` 为真实未覆盖 opcode 族；`end_oretuba` 的代码区已用公式+池锚点重新界定，其未知量见 §三.2）。"
      "**参数语义（旧称「未定」）已分级落库**于同目录 `演出_np_IL_语义.tsv`："
      "坐标（`_DrawBS`/`_MoveBS`/`_ScrollBG`）、时长、alpha 已定；zoom/angle/anchor 与哨兵位仍判**未定**（见 §四）。"
      % (len(rows) - sum(1 for r in rows if r["op"] == "skip")))
    A("")
    A("---")
    A("")
    A("## 一 方法（可复算）")
    A("")
    A("### 1.1 指令流解码")
    A("")
    A("BGI v1 剧情脚本 = `magic` + `u32@0x1C` → **`hdrsize = 0x1C + u32@0x1C`（公式，不硬编码）** → 规整 u32 词流。")
    A("实测：26 剧情脚本与 `start_oretuba` 的 `u32@0x1C = 0x24` ⇒ 代码起 **0x40**；")
    A("**`end_oretuba` 的 `u32@0x1C = 0x34` ⇒ 代码起 0x50**（此前误用 0x40 导致越界，见 §三.2）。")
    A("操作数宽度表（本报告实测，**26 剧情脚本全流精确落位**）：")
    A("")
    A("```")
    A("0x00 push_dword(i32) :2   0x01 push(未定) :2   0x03 push_string(code相对) :2")
    A("0x18 :1  0x19 :2  0x1A :1  0x1B :1  0x1C 命令分派 :1  0x20 :1  0x21 :1")
    A("0x3F nargs :2  0x7F :3  0x140 文本显示 :1  0xF0 :1  0xF4 halt :1")
    A("0xF6 转场分派 :1  0xF7 :3  0xF9 :1  0xFE 调用 :1")
    A("```")
    A("")
    A("**代码区结束 = 字符串池起点**（**三级锚点，全不命中则不解码，不静默回退整文件**）：")
    A("① 首个 `b\"D:\\WORK\"` 串偏移（27/28，恒 `== 最后一个 word-aligned 0xF4 + 4`）；")
    A("② fallback：首个池文件名 `.bsc/.bs5/.h` NUL 串——`end_oretuba` 由此得 `End_Oretuba.bsc` @0x70C ⇒ 代码区 `[0x50, 0x70C)`；")
    A("③ fallback：最后一个 word-aligned `0xF4` + 4。")
    A("落位校验：**每个剧情脚本解析器都精确停在 code_end**（见 §五 闸门）。")
    A("")
    A("### 1.2 语句文法（★ 核心实测结论：**实参在命令名之前**）")
    A("")
    A("```")
    A("[位置调用: push_str \"…\\A01_B0.bs5\"; push 23; nargs 2; 0xFE]")
    A("[实参:      push 0; push_str \"SE768\"; push 128; push 64; push 0; push 500]")
    A("[调用点:    push_str \"_PlaySE\"; 0x1C]")
    A("```")
    A("")
    A("位置调用 `push_str <*.bs5 路径>; push_dword <行号>; nargs 2; 0xFE` 把脚本切成语句段；")
    A("段内是实参表达式，段末是 `push_string <命令名>; 0x1C`。**证据**：")
    A("1. 语音令牌紧邻其命令名之前——`a01_b0` 44 处 `push_str \"ASU300xx\"; …; push_str \"_PlayVoice\"; 0x1C`；")
    A("2. 音效令牌同理——`a01_b0` `push_str \"SE768\"; 128;64;0;500` 后紧跟 `push_str \"_PlaySE\"; 0x1C`；")
    A("3. （旁证，非决定性）`.bs5` 行号紧随命令之后、单调递增（…20,21,23,25…）——单调递增与前置/后置两种读法都成立，")
    A("   真正一致的旁证是文本行稳定形态 `push_str(台词); 0x140; 位置调用(file,line)`（261/261）。")
    A("")
    A("> ⚠️ 侦察事实清单原述「命令名之后是资源令牌」系**方向误读**；本表按实测方向（实参在前）切分。")
    A("")
    A("**第二种调用形态：`0xF6` 转场调用**（`push_str <转场名>; <push 字面>; 0xF6; 0xF0`）——")
    A("**不由 `0x1C` 分派**，形态为「名字在前、实参在后」：")
    A("```")
    A("a01_a0 @0x98 : push_str \"FadeSS\";      push 0; 0xF6; 0xF0   （场景转场）")
    A("a06_c0 @0x694: push_str \"End_Oretuba\"; push 0; 0xF6; 0xF0   （跳转到 End_Oretuba）")
    A("```")
    A("本表把这两条也纳入采集（`op` = 转场名，`evidence` 记 `op=0xF6 (transition)`）。")
    _f = collections.Counter()
    for s in stats_scenes:
        if s["script"] not in ("start_oretuba", "end_oretuba"):
            _f.update(s.get("follow", {}))
    _fe = sum(s.get("fe_count", 0) for s in stats_scenes
              if s["script"] not in ("start_oretuba", "end_oretuba"))
    A("**全库复查**（26 剧情脚本）——所有 `push_str <名字>`（名字形 `^[A-Za-z_][A-Za-z0-9_]*$`，非路径）的后继 opcode 只有 **3 种**：")
    A("`0x1C`（命令调用，**%d** 处，名字均以 `_` 起头）、`0x03`（A/B 成对资源令牌，%d 处）、`0x00`（资源实参，%d 处）；"
      % (_f.get((1, CMDCALL), 0), _f.get((0, PUSH_STRING), 0), _f.get((0, PUSH_DWORD), 0)))
    A("其中 `0x00` 之内含上文 2 处转场（紧随其后第 2 个 opcode 为 `0xF6`）。")
    A("且 **%d 处 `0xFE` 全部是位置调用**（`push_str path; push; nargs; 0xFE`；非位置调用的 `0xFE` **0 处**）——" % _fe)
    A("⇒ 26 剧情脚本的调用形态**已穷举**：`0x1C` 命令调用 + `0xF6` 转场调用，无第三类。")
    A("")
    A("### 1.3 `seq` 对齐")
    A("")
    A("与 `演出表说明.md` §1.1 **完全一致**：调用点的 `seq` = **该调用点之后第一个文本行**的 `lines[].seq`；")
    A("其后无文本行 ⇒ 末行行号（`after_last_line`）；在其之前 ⇒ 1（`before_first_line`）。")
    A("文本行在指令流的出现序与 `lines[].jp` 逐条相等（**28/28 场景守恒**，见 §五）。")
    A("")
    A("### 1.4 资源令牌")
    A("")
    A("从操作数里挑形如 `BG55`/`SE768`/`ASU30001`/`ASU_D05S` 的 ASCII 令牌，按 `资源总账.json` 的 `(kind,'np')` 域解析：")
    A("命中 ⇒ `target` = `out_relpath`（标 `ok`）；未命中 ⇒ 记 `unmatched`（如**本机缺失的 ASU 音库语音 ID**）。")
    A("非资源串（说话人名、台词、`#RRGGBB`、纯数字）不计入。`target` 取该调用点**首个**达标操作数，故一条命令的其余资源令牌在 `evidence` 的 `args`/`res` 里。")
    A("")
    _ok = collections.Counter()
    _un = collections.Counter()
    for r in rows:
        for m in re.finditer(r"res=\[([^\]]*)\]", r["evidence"]):
            for item in m.group(1).split("; "):
                mm = re.match(r"([^\s]+)->(\w+) ok$", item)
                if mm:
                    _ok[mm.group(2)] += 1
                    continue
                um = re.match(r"([^\s]+)->unmatched$", item)
                if um:
                    _un[um.group(1)] += 1
    A("**本表资源解析统计**：")
    A("")
    A("| 资源种类 | 命中(`ok`) 操作数次 |")
    A("| --- | ---: |")
    for k in ("chr", "pic", "se", "bgm", "movie", "voice"):
        if _ok.get(k):
            A("| `%s` | %d |" % (k, _ok[k]))
    A("| **合计 `ok`** | **%d** |" % sum(_ok.values()))
    A("| **`unmatched`** | **%d**（%d 个唯一令牌）|" % (sum(_un.values()), len(_un)))
    A("")
    if _un:
        _p = collections.Counter(re.match(r"[A-Za-z]+", t).group(0) if re.match(r"[A-Za-z]+", t) else t[:3]
                                 for t in _un)
        A("`unmatched` 令牌前缀分布（前 6）：%s。"
          % "，".join("`%s*`×%d" % (p, n) for p, n in _p.most_common(6)))
        A("实测这些**全部是语音 ID**（`ASU3xxxx` 560 个 + `Y031xxxx` 2 个）——本机 np 的 **ASU / Y03 音库缺失**"
          "（`作品skill/SKILL.md` §二已登记「无解」：559 条台词无语音）；"
          "与之相对，`HIY3xxxx`（叙述者）语音 ID **全部命中（68/68）**。⇒ `unmatched` 是**源侧缺件**，非本表解析缺陷。")
    A("")
    A("---")
    A("")
    A("## 二 表列口径（**照此读表**）")
    A("")
    A("9 列，与逐行演出表契约同表头：`scene_id seq op target arg1 arg2 arg3 evidence confidence`。")
    A("**但 `op` / `confidence` 均不适用契约 §1.3/§1.4（见文首方言声明）。**")
    A("")
    A("| 列 | 本表口径 |")
    A("| --- | --- |")
    A("| `op` | **命令名**（如 `_DrawScene` / `_PlayVoice`）**或转场名**（`FadeSS` / `End_Oretuba`）；`skip` 行仍为 `skip`。"
      "**越出契约 §1.3 的 12 值闭集** |")
    A("| `target` | 该调用点**首个命中资源总账**的操作数 → `out_relpath`；无则空 |")
    A("| `arg1..arg3` | 有序字面操作数的**前三个**（`push_dword` 取 int、`push_string` 取串） |")
    A("| `evidence` | `script=…; file_off=0x…; op=0x1C/0xF6[ (transition)]; .bs5 line N; args=[完整有序字面表]; ops=[非 push 运算]; res=[令牌→ok/unmatched]` |")
    A("| `confidence` | `exact` = 调用点与字面操作数**逐指令直读**（非池序推定）；`skip` 行 `unknown`。"
      "**此 exact 非契约 §1.4 的 (scene,seq,target) 三元组强度** |")
    A("")
    A("**操作数超过 3 个时**：`arg1..arg3` 仍取前三个；**完整有序字面表在 `evidence` 的 `args=[…]`**（即「超出的用扩展说明」），")
    A("不新增第 10 列（保持契约 9 列）。求值型写法（`0x21` 疑似 sub）以 `ops=[sub]` 记在 evidence，**不解释其算术语义**。")
    A("")
    A("> `confidence=exact` 指的是**本层抽取**（命令名 + 字面操作数）为字节码直读；")
    A("> 参数语义（谁是 x / 时长 / alpha）**不在本表**，见 §四 与同目录 `演出_np_IL_语义.tsv`。")
    A("")
    A("### 2.1 姊妹表：`演出_np_IL_语义.tsv`（14 列，参数语义）")
    A("")
    A("与本表**逐行一一对应（非 skip）**（同 `scene_id`+`seq`+命令名排序，含 2 条转场行）。列：")
    A("`scene_id / seq / 命令名 / 元数 / x / y / x2 / y2 / 时长ms / alpha / 其他已定位置 / 未定位置占位 / evidence / confidence`。")
    A("")
    A("- 数值取自**与元数 1:1 对齐的折叠实参**（与 N1 `_args_exact.json` 33 命令逐点相同，见 §四.1）；")
    A("  **不是**本表 `args=[…]`（那是未折叠的原始字面，长度与元数不对齐）。")
    A("- **未定的位置一律留空**，并在「未定位置占位」列记 `argN`；**不得**把未定位填进 x/y/时长/alpha。")
    A("- `其他已定位置` 记非核心列的具名角色或类型（如 `_DrawBS` 的槽位/立绘令牌/移动标志/并行标志）。")
    A("")
    A("---")
    A("")
    A("## 三 未知 opcode 登记（**不静默跳过**）")
    A("")
    A("### 3.1 26 个剧情脚本 = 0")
    A("")
    A("`a01_a0 … a06_c0` 共 26 个脚本的指令流**全流精确落位，0 处未知 opcode**（解析器停在 code_end，无残余）。")
    A("")
    A("### 3.2 2 个菜单/控制脚本")
    A("")
    A("| 脚本 | `u32@0x1C` | 代码起 | 代码区 | 指令词数 | 未知 opcode | 成因 |")
    A("| --- | ---: | ---: | --- | ---: | ---: | --- |")
    for s in stats_scenes:
        if s["unknown"] or s["script"] in ("start_oretuba", "end_oretuba"):
            cs = s.get("code_start"); ce = s.get("code_end")
            cause = ("真实未覆盖 opcode 族（区间已双向锚定）" if s["script"] == "start_oretuba"
                     else "代码区经池锚点重新界定后仍含未被本表覆盖的 opcode（该区另含内嵌数据表，线性解码不成立）")
            A("| `%s` | 0x%X | 0x%X | [0x%X, 0x%X) | %d | %d | %s |"
              % (s["script"], s["hdr_u32"], cs, cs, ce, s["instr"], s["unknown"], cause))
    _e = [s for s in stats_scenes if s["script"] == "end_oretuba"]
    if _e:
        e = _e[0]
        A("")
        A("**`end_oretuba` 的成因（★ 一审 Major-1 的订正，此前误诊）**：")
        A("")
        A("- 该文件 `u32@0x1C = 0x%X` ⇒ **代码起点应为 0x%X**（非 0x40）；早期版本硬编码 0x40，越界后既无 `D:\\WORK`、"
          % (e["hdr_u32"], e["code_start"]))
        A("  也无 word-aligned `0xF4`，遂**回退整文件把串池当指令**，报出的 102 处「未知 opcode」里混入 `0x5F646E45`(`End_`)、")
        A("  `0x7465724F`(`Oret`)、`0x637362`(`bsc`) 等**串池字面**——那不是 opcode。")
        A("- 现版本：代码起点用公式（0x%X），`code_end` 用**池文件名 fallback**（首个 `.bsc/.bs5/.h` 串 = `End_Oretuba.bsc` @0x70C）"
          % e["code_start"])
        A("  界定为 `[0x%X, 0x%X)`，共 %d 词、未知 %d 处。**数字由 102 订正为 %d**（成因随之改正）。"
          % (e["code_start"], e["code_end"], e["instr"], e["unknown"], e["unknown"]))
        A("- 该区含内嵌数据表（`… FFFFFFFF, 0x22 …` 序列），故**线性指令解码不成立**；本场仍是 `skip`。")
    A("")
    A("未覆盖 opcode 值（出现次数）：")
    A("")
    for s in stats_scenes:
        if s["unknown_vals"]:
            A("- `%s`：%s" % (s["script"],
                            ", ".join("`0x%X`×%d" % (k, v) for k, v in s["unknown_vals"].most_common())))
    A("")
    A("⇒ 这两场按旧表惯例如实 `skip`（不产出可能错位/来自数据表的伪调用点），")
    A("并在此登记其未知 opcode——这是判「解析是否完整」的关键指标：**剧情脚本 100% 覆盖，菜单脚本留待另立 opcode 逆向**。")
    A("")
    A("---")
    A("")
    A("## 四 参数语义分级（**已定 / 部分已定 / 只能定元数 / 未定**）")
    A("")
    A("> 旧版「参数语义未定，本表不输出」已作废（ISSUE-20261007-01）。参数语义现落在同目录")
    A("> **`演出_np_IL_语义.tsv`**（14 列，与 9 列 IL 表逐行一一对应（非 skip））。")
    A("> 分级口径：`已定(…)`=核心列（x/y/x2/y2/alpha/时长）已定；`部分已定(时长|类型)`=核心列仅有")
    A("> 时长、或仅有类型标签；`只能定元数`=除元数外无语义；`未定`=0xF6 转场调用。")
    A("> **未定项一律留空并标「未定」**——尤以 zoom / angle / anchor 位、`_MoveBS` 的 0x10000000 哨兵位为禁填区。")
    A("")
    A("### 4.1 元数（N1 · 三路互证）")
    A("")
    A("33 条命令的**元数** = `framework` 导出函数序言槽数，由三路独立证据互证：")
    A("① **声明**：导出函数序言的 `push_base_offset; move_arg(2);` 对数；")
    A("② **实测**：26 剧情脚本逐调用点的实参段栈深 + 常量折叠后实参数；")
    A("③ **定义-使用**：形参被喂给哪个系统调用（`_argmap.json` Syscall 列）。")
    A("**1643/1643 调用点三路一致**（逐命令×逐位置的 kind/值域/反例见 N1 `命令参数表.tsv`）。")
    A("本生成器用与 N1 相同的**常量折叠**口径重算实参，并断言 `折叠数 == 声明元数`；")
    A("实测 33 命令 1643 调用点与 N1 `_args_exact.json` **逐点完全相同**（复算见 §五 闸门）。")
    A("")
    A("### 4.2 坐标 x / y（N3 · 槽位-坐标相关性 + 物理约束，**不依赖图元名**）")
    A("")
    A("坐标系：**原点 = 画面中心**（`screen = 中心 + 偏移`），画布 **1280×720**。判定只用「槽位↔符号相关」")
    A("（如 `slot3` 全为负值、`slot5` 全为 0/正值）加「中心原点下坐标须落在画布内」两条物理约束。")
    A("")
    A("| 命令 | 元数 | x | y | x2（移动目标） | y2 | 判据与验证 |")
    A("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
    A("| `_DrawBS` | 19 | **arg5** | **arg6** | **arg9** | **arg10** | x 槽位↔符号相关，640+x∈[0,1280] **283/284=99.6%**"
      "（唯一反例=刻意的出画入场）；y 360+y∈[0,720] **284/284=100%** |")
    A("| `_MoveBS` | 10 | **（撤回）** | — | — | — | ⚠️ arg3 虽为唯一变化位，但 18 条里 **17 条是 tag 编码**"
      "（0x10000000 族 11 条、0x20000000 族 6 条，其中 4 条为本体哨兵 268435456），**仅 1 条**普通坐标 `1000`"
      "⇒ **不作 x、判未定**（N3 对 `_MoveBS` 无正式判定，亦无物理验证） |")
    A("| `_ScrollBG` | 7 | **arg1**（起） | — | **arg2**（终） | — | 起/终点 x；arg5=时长 ms。**n=2，推定**（confidence 已降为 `部分已定(x/x2/时长;n=2,推定)`）|")
    A("")
    A("- `_DrawBS` 另：**arg8 = 移动标志**（{0:279,1:5}，=1 者均伴随移动目标非 0）；**arg18 = 时长 ms**；**arg19 = 并行标志**。")
    A("- **`_DrawScene` / `_DrawBG` / `_FadeBS` 无 x/y**（全屏背景 / 纯淡入淡出）——其坐标列一律留空。")
    A("- ⚠️ **`0x10000000`(268435456) 不是 16.16 的 1.0**，是 tag1/payload0 的「绝对 0 / 不变」哨兵"
      "（N3 更正 N2 旧推测）——哨兵位（含 `_MoveBS` arg3/4/5/7）语义未定，**不得当坐标像素**。")
    A("- `_MoveBS` arg3 的**原始 tag 值不丢**：仍逐点记在语义表 `evidence` 的 `args=[…]`，"
      "并在「未定位置占位」列记 `arg3`——只是**不进 x 列**。")
    A("")
    A("### 4.3 时长与 alpha")
    A("")
    A("时长 ms：由 N1 `kind=ms`（取值 ⊆ 毫秒集）判定，另加 `_ScrollBG` arg5（kind=int，值域 1500..4000 即毫秒）。")
    A("")
    A("| 命令 | 时长位置 | N1 实测值域 |")
    A("| --- | --- | --- |")
    for _cmd in sorted(MS_RANGE, key=lambda k: -cmd_inventory(rows).get(k, {}).get("count", 0)):
        _pos, _rng = MS_RANGE[_cmd]
        A("| `%s` | arg%d | %s ms |" % (_cmd, _pos, _rng))
    A("")
    A("alpha：`_DrawBS` **arg16**（{0:283, 256:1}，256=全透明）。其余命令无 alpha 位（或未定）。")
    A("")
    A("### 4.4 未定（**必须留空，不得填**）")
    A("")
    A("1. **zoom / 缩放 / 角度 / anchor 位**：`_DrawBS` **arg14**（仅 1 处非 0，CHI01I=20）、**arg17**"
      "（50 处=5、1 处=10、1 处=20）——本作数据里恒 0 或仅零星非 0 ⇒ **无判别力，判未定**；")
    A("   连同 arg7/arg11/arg12/arg13/arg15（恒 0 保留位）一并记入语义表「未定位置占位」。")
    A("2. **`_MoveBS` 的坐标/tag 族**：**arg3**（曾误判为目标 x，现撤回：18 条里 17 条是 tag 编码、"
      "4 条为哨兵本体；仅 1 条普通坐标）与 arg2/arg4/arg5/arg6/arg7/arg8 —— 语义未定（原始值仍存 evidence）。")
    A("3. **0xF6 转场调用**（`FadeSS` / `End_Oretuba`，各 1 处）：连元数都未定 ⇒ 语义表整行 `未定`。")
    A("4. 求值型实参（`0x21` sub 等）已由常量折叠求值；**未折叠的原始字面**仍只在 9 列 IL 表的 `args=[…]` 里。")
    A("")
    A("### 4.5 逐命令分级汇总")
    A("")
    _per = collections.OrderedDict()
    _unds = {}
    for _s in sem_rows:
        _d = _per.setdefault(_s["命令名"], collections.Counter())
        _d["n"] += 1
        for _col, _k in (("x", "x"), ("y", "y"), ("x2", "x2"), ("y2", "y2"),
                         ("时长ms", "ms"), ("alpha", "alpha")):
            if _s[_col] != "":
                _d[_k] += 1
        _d["conf"] = _s["confidence"]
        _d["nargs"] = _s["元数"]
        if _s["未定位置占位"]:
            _unds.setdefault(_s["命令名"], []).append(_s["未定位置占位"])
    A("| 命令 | 调用点 | 元数 | x | y | x2 | y2 | 时长ms | alpha | 未定位置（arg） | 语义级别 |")
    A("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for _cmd in sorted(_per, key=lambda k: -_per[k]["n"]):
        _d = _per[_cmd]
        A("| `%s` | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
          % (_cmd, _d["n"], _d["nargs"],
             ("%d/%d" % (_d["x"], _d["n"])) if _d["x"] else "—",
             ("%d/%d" % (_d["y"], _d["n"])) if _d["y"] else "—",
             ("%d/%d" % (_d["x2"], _d["n"])) if _d["x2"] else "—",
             ("%d/%d" % (_d["y2"], _d["n"])) if _d["y2"] else "—",
             ("%d/%d" % (_d["ms"], _d["n"])) if _d["ms"] else "—",
             ("%d/%d" % (_d["alpha"], _d["n"])) if _d["alpha"] else "—",
             _unds.get(_cmd, ["—"])[0],
             _d["conf"]))
    A("")
    A("**汇总**：%s。" % "；".join(
        "%s %d 个命令 / %d 调用点" % (k, sum(1 for c in _per if _per[c]["conf"] == k),
                                    sum(_per[c]["n"] for c in _per if _per[c]["conf"] == k))
        for k in sorted(_cc, key=lambda x: -_cc[x])))
    A("")

    A("---")
    A("")
    A("## 五 生成器内置闸门（**都能真失败**）")
    A("")
    A("1. **全流落位**：每个剧情脚本指令流精确停在 `code_end`（非 26 剧情脚本必 0 未知 opcode 才产出）；")
    A("2. **文本槽守恒**：每个场景指令序匹配到的文本槽 == `len([l.jp for l in lines if l.jp])`（28/28 通过）；")
    A("3. **调用点结构**：`push_string(命令名) + 0x1C`（命令调用）或 `push_string(转场名) + … + 0xF6`（转场调用）；"
      "未跟位置调用者（脚本末命令）允许 `srcline=-`；非 skip 行 `op` 须匹配 `^[A-Za-z_][A-Za-z0-9_]*$`；")
    A("4. **列契约**：9 列固定表头（`_staging_common.write_tsv` 的列/枚举闸门）；")
    A("5. **场景覆盖**：28 场每场要么 ≥1 条非 skip 行，要么恰 1 条 skip 行（复用 `_staging_common.assert_scene_coverage`）；")
    A("6. **语义对齐**：每个命令调用点 `折叠实参数 == N1 声明元数`（折叠口径漂移即 fail）；")
    A("   命令不在 N1 参数模型内即 fail loud（**拒绝编造元数**）；核心列非空值必须为整数；")
    A("7. **语义表一一对应**：语义表行数 == IL 非 skip 行数；`confidence` 取值在分级闭集内；")
    A("8. **幂等**：`--check` 下**四份产物**的重算字节与磁盘逐字节相同。")
    A("")
    A("---")
    A("")
    A("## 六 与旧 `演出_np.tsv` 的逐场差异")
    A("")
    A("旧表 = 常量池「首次引用位」级（同场重复调用不可见、无数值）。下表：旧行数 → 新调用点数（Δ）。")
    A("")
    A("| 场景 | 旧行数 | 新调用点 | Δ | 旧表 target 令牌在新表**完全缺席** |")
    A("| --- | ---: | ---: | ---: | --- |")
    old_total = new_total = 0
    for o in scenes:
        sid = o["scene_id"]
        o_row = old_per.get(sid, 0)
        o_il = sum(1 for r in by_scene.get(sid, []) if r["op"] != "skip")
        miss = sorted(old_toks.get(sid, set()) - new_toks.get(sid, set()))
        old_total += o_row
        new_total += o_il
        A("| `%s` | %d | %d | %+d | %s |" % (sid, o_row, o_il, o_il - o_row,
                                              ", ".join(miss) if miss else "—"))
    A("| **合计** | **%d** | **%d** | **%+d** | — |" % (old_total, new_total, new_total - old_total))
    A("")
    A("**读法**：旧表 560 行（含 2 skip）→ 新表 **%d 个调用点 + 2 skip = %d 行**。"
      "增量主要来自**同场重复调用**（同一命令/资源在旧表因池内 intern 去重而只计 1 次）。"
      % (new_total, len(rows)))
    A("末列比对的是**全表所有资源令牌**（新表把非 `target` 的实参令牌也算入），故为空即「旧表引用的每个令牌在新表都有落点」。")
    A("")
    A("---")
    A("")
    A("## 七 名字清单（命令 + 转场，前 20，完整见 `命令清单.tsv`）")
    A("")
    A("| 名字（命令 / 转场） | 调用次数 | 首次偏移 | 首次场景 |")
    A("| --- | ---: | ---: | --- |")
    cmds = cmd_inventory(rows)
    for name in sorted(cmds, key=lambda k: -cmds[k]["count"])[:20]:
        c = cmds[name]
        A("| `%s` | %d | 0x%06X | `%s` |" % (name, c["count"], c["first_offset"], c["first_scene"]))
    A("")
    A("---")
    A("")
    A("## 八 复跑")
    A("")
    A("```bash")
    A("python -X utf8 \"工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_np_il.py\"")
    A("python -X utf8 \"工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_np_il.py\" --check")
    A("```")
    A("")
    A("产出**四份**（全在本目录）：`演出_np_IL.tsv`（9 列 IL）、`演出_np_IL_语义.tsv`（14 列语义）、")
    A("`命令清单.tsv`、`说明.md`。`--check` 逐字节比对四份、不落盘。")
    A("")
    A("---")
    A("")
    A("## 九 风险、警示与未完成项")
    A("")
    A("1. **9 列 IL 表不含参数语义**；语义在同目录 `演出_np_IL_语义.tsv`（§四 分级）。")
    A("   语义表里**未定的位置已留空并标「未定」**（zoom/angle/anchor、`_MoveBS` 的 0x10000000 哨兵位等）")
    A("   ——**不得据空值反推**，也不得把 `0x10000000` 当 16.16 的 1.0（N3 已更正 N2 旧推测）。")
    A("2. **菜单脚本未解**（`start_oretuba` / `end_oretuba`）——其 opcode 族未被本表覆盖，如实 `skip`；"
      "`end_oretuba` 的代码区已按公式+池锚点重新界定（`[0x50,0x70C)`），未知量由早期的 102（越界串池字节）订正为真实区内的未覆盖量。")
    A("3. `unmatched` 令牌**全部为语音 ID**（`ASU3xxxx` 560 + `Y031xxxx` 2；后者含 1 个带字母后缀 `ASU30025A`）"
      "＝**本机缺失的音库**（np 音库缺失，旧 `作品skill` 已登记「无解」）——非本表缺陷；`HIY3xxxx` 68/68 命中。")
    A("4. 旧表对照仅比**行数**与 **target 令牌集**；两表口径不同（池序 vs 指令流），行数差**不代表旧表错误**。")
    A("5. **本表 `op`/`confidence` 为 IL 方言**，不适用契约 §1.3/§1.4（见文首方言声明）——下游接入前须按其自身口径处理。")
    A("")
    doc = "\n".join(L) + "\n"
    return doc


# ================================================================ 闸门
def gate(rows, sem_rows, stats_scenes, scenes):
    scene_ids = [o["scene_id"] for o in scenes]
    for s in stats_scenes:
        if s["script"] not in ("start_oretuba", "end_oretuba"):
            if s["unknown"]:
                raise SystemExit("!! 剧情脚本 %s 出现 %d 处未知 opcode（宽度表不完整）"
                                 % (s["script"], s["unknown"]))
            if not s["landed"]:
                raise SystemExit("!! 剧情脚本 %s 指令流未精确停在 code_end（宽度表错位）" % s["script"])
    C.assert_scene_coverage(rows, scene_ids, SRC)
    for r in rows:
        if r["op"] == "skip":
            continue
        if not NAME_RE.match(r["op"]):
            raise SystemExit("!! op 非命令/转场名：%r" % r["op"])
        if "file_off=0x" not in r["evidence"]:
            raise SystemExit("!! evidence 缺 file_off：%r" % r["evidence"][:80])
    # --- 语义表闸门 ---
    n_il = sum(1 for r in rows if r["op"] != "skip")
    if len(sem_rows) != n_il:
        raise SystemExit("!! 语义表行数 %d != IL 非 skip 行数 %d（应一一对应）" % (len(sem_rows), n_il))
    for s in sem_rows:
        conf = s["confidence"]
        if not (conf == "未定" or conf == "只能定元数"
                or conf.startswith("已定(") or conf.startswith("部分已定(")):
            raise SystemExit("!! 语义表 confidence 越界：%r" % conf)
        for col in ("x", "y", "x2", "y2", "时长ms", "alpha"):
            v = s[col]
            if v != "" and not re.match(r"^-?\d+$", str(v)):
                raise SystemExit("!! 语义表 %s 列非整数（%s=%r）——未定位不得进核心列"
                                 % (s["命令名"], col, v))
        # 未定位不得被反填进核心列：核心列非空 ⇔ 该位置被判为对应列（构造保证，这里再断言）
        if s["命令名"] in N1_KINDS:
            if int(s["元数"]) != len(N1_KINDS[s["命令名"]]):
                raise SystemExit("!! 语义表 %s 元数 %s != N1 模型 %d"
                                 % (s["命令名"], s["元数"], len(N1_KINDS[s["命令名"]])))


def sem_stats(sem_rows):
    """独立统计：按 confidence 分布、逐命令 x/y 覆盖、未定位置计数。"""
    conf = collections.Counter(s["confidence"] for s in sem_rows)
    per = collections.OrderedDict()
    undet_total = 0
    for s in sem_rows:
        d = per.setdefault(s["命令名"], {"n": 0, "x": 0, "y": 0, "undet": 0,
                                         "conf": s["confidence"], "nargs": s["元数"]})
        d["n"] += 1
        d["x"] += 1 if s["x"] != "" else 0
        d["y"] += 1 if s["y"] != "" else 0
        if s["未定位置占位"]:
            d["undet"] += len(s["未定位置占位"].split(","))
        undet_total += 0
    return {"by_confidence": dict(conf),
            "undetermined_positions_per_row": {k: v["undet"] for k, v in per.items() if v["undet"]},
            "per_command": per}


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="不落盘，仅逐字节比对四份产物")
    a = ap.parse_args()

    scenes = [json.loads(ln) for ln in io.open(SCENE_JSONL, encoding="utf-8") if ln.strip()]
    rows, sem_rows, stats_scenes, ledger = build()
    gate(rows, sem_rows, stats_scenes, scenes)
    cmds = cmd_inventory(rows)
    ss = sem_stats(sem_rows)

    payload = serialize_tsv(rows)
    payload_sem = serialize_sem(sem_rows)
    payload_cmd = serialize_cmd(cmds)
    payload_doc = build_doc(rows, sem_rows, stats_scenes, ledger).encode("utf-8")

    summary = {
        "scenes": len(scenes),
        "rows": len(rows),
        "il_rows": sum(1 for r in rows if r["op"] != "skip"),
        "skip_rows": sum(1 for r in rows if r["op"] == "skip"),
        "commands": len(cmds),
        "transition_calls": sum(s.get("transitions", 0) for s in stats_scenes),
        "instr_words": sum(s["instr"] for s in stats_scenes),
        "unknown_opcodes": sum(s["unknown"] for s in stats_scenes),
        "unknown_ratio": round(sum(s["unknown"] for s in stats_scenes)
                               / max(sum(s["instr"] for s in stats_scenes), 1), 6),
        "landed_story_scripts": sum(1 for s in stats_scenes
                                    if s.get("landed") and s["script"] not in ("start_oretuba", "end_oretuba")),
        "per_script_unknown": {s["script"]: s["unknown"] for s in stats_scenes if s["unknown"]},
        "ledger_collisions": len(ledger.collisions),
        "semantic_rows": len(sem_rows),
        "semantic_by_confidence": ss["by_confidence"],
        "semantic_x_rows": sum(1 for s in sem_rows if s["x"] != ""),
        "semantic_y_rows": sum(1 for s in sem_rows if s["y"] != ""),
        "semantic_commands_with_undetermined": len(ss["undetermined_positions_per_row"]),
    }

    if a.check:
        outs = [(TSV_OUT, payload), (SEM_OUT, payload_sem),
                (CMD_OUT, payload_cmd), (DOC_OUT, payload_doc)]
        bad = []
        for path, want in outs:
            if not os.path.isfile(path):
                bad.append(path + " (缺失)")
                continue
            if C.read_artifact_bytes(path) != want:
                bad.append(path + " (字节不同)")
        summary["check_bytes_equal"] = not bad
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        if bad:
            raise SystemExit("!! 幂等失败：\n  " + "\n  ".join(bad))
        print("[闸门] 幂等 PASS（四份产物逐字节相同；行尾规范化比较）")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    C.assert_in_checkout(TSV_OUT)
    n = C.write_tsv(TSV_OUT, rows)                       # 列/枚举闸门
    with open(SEM_OUT, "wb") as f:
        f.write(payload_sem)
    with open(CMD_OUT, "wb") as f:
        f.write(payload_cmd)
    with open(DOC_OUT, "wb") as f:
        f.write(payload_doc)
    summary["written"] = {"tsv": n, "sem": len(sem_rows), "cmd": len(cmds),
                          "doc_bytes": len(payload_doc)}
    summary["out_dir"] = OUT_DIR
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
