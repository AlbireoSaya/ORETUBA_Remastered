#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
place_dsl.py —— 立绘「位置 token DSL」运行期求值器（ISSUE-20261008-09 / PLACE 模块）

输入（只读）:  <工作区根>\\工程\\我们没有翅膀——格雷塔迦露德与柳木原\\编程组\\SOB0解码\\解出_{ot,otr,otp}.tsv
               （14 列，evidence 含 args=[...]；`解出_*.tsv` 被 .gitignore 排除，须先跑
                `编程组\\工具\\decode_sob0.py --out 编程组\\SOB0解码` 再生）
               **工作区根由「向上搜索 Galgame.md」多候选解析**（可 `--ws-root <dir>` 或环境变量
               `GRETA_WS_ROOT` 覆盖）⇒ 入库到 `新源侧\\PLACE\\` 后原位可跑，不再依赖固定层数。
可选交叉核对:  ① 入库后同树兄弟 `<工作区根>\\工程\\<译名>\\编程组\\新源侧\\SOB0ARGS\\解出_{src}_args.tsv`
               （**优先**；该件属已剔出库的可再生中间件）→ ② 旧开发位置
               `<工作区根>\\子代理工作区\\ISSUE-20261008-09\\SOB0ARGS\\`（⚠️ 历史副本，仅兜底）；仅 `--crosscheck` 用

依据（均引自本 Issue 已核实的机制事实，不自行发明；结论强度与未证边界见 `会话交接_20261009.md` §二/§三）:
  * 位置 = 原生 token DSL 运行期求值。实现链：
      sp_move 实现 0x4033A0 → token 解析器 0x402970 → 方位处理器 0x402B42 → call [obj_vtbl+0x38]
    （见入库后**同树兄弟** `..\\EXE_POS\\k人排布表_结论.md` §2.2 / 任务书 §8.6；旧开发位置
     `子代理工作区\\ISSUE-20261008-09\\EXE_POS\\` 为**历史副本，勿用**（与入库件 md5 不同），仅存档）
  * 坐标空间: 引擎内部 640x480。折算 1920 画布 = 内部值 x3（640→1920）；1280 系 = 内部 x2。
      C(中心) = 320(内部) → 960(1920)；W/4 = 152(内部) → 456(1920)
      l = C - W/4 = 168 → 504 ;  r = C + W/4 = 472 → 1416
      步长 25(内部) → 75(1920)
  * 锚点 = 立绘位图中心（非 ELG offset_x）；y 默认底边对齐（任务书 §8.6 实机逐像素已证 底边 598@800x600）。
  * 所有方位 token 都是「相对当前位写增量」（"绝对"档由 dx = 目标 - 当前 实现）。
    求值有两种口径，由模块级 `MODE` 选择：
      **`static`（本批交付采用）**——每行只解**本行控制串内**的锚点序列（`c l r !c !l !r` 及其后的 `<N />N` 步进）；
                                    锚点后无跨行依赖 ⇒ 与 D 模块金标严口径命中率 **0.9616**。
      `state`  —— 逐 (scene_id, slot) 累积状态（覆盖纯相对/保持档 `>N <N _ $ [ ] ^ % u d +N -N`），
                  但**槽号会被不同角色先后复用**（例：`ot_s01_08d4` 槽 0 依次为 MIY04A/B/H/…/E/M）
                  ⇒ 跨行状态会漂移；其独有行命中率 0.7458，整体 0.9386。详见交付报告 §五。
      `auto`   —— 有自身锚点者取 static，其余取 state。

纪律（对应任务书 §八 与本次验收标准 4「不许猜」）:
  * 解析 evidence **不用非贪婪正则**（串实参可含 ] / , / 尾空格，受影响 126 行）：
    取 `args=[` 到 ` ctrl=` 的全部内容 + 括号感知顶层逗号切分 + **不 strip**。
  * 控制串取自**该族 ctrl 实参位**（`FAMILY[src][V]["ctrl"]`），**不是** evidence 里那个 `ctrl=` 字段
    （后者在 0x18B74 等族恒为 `None`，实测 1,696 行不一致；见 --crosscheck）。
  * DSL 表里没有的 token 一律 **unresolved**，逐条列出并统计语料出现次数；**不静默当成 c**。

CLI:
  python -X utf8 place_dsl.py --emit               # 生成 位置DSL实现表.tsv / 未覆盖token清单.tsv
                                                   #        f_b前缀行.tsv / place_dsl_rows_{src}.tsv
  python -X utf8 place_dsl.py --check              # 严格只读幂等复核（不写盘）
  python -X utf8 place_dsl.py --selfcheck-mutate   # 变异自证：改坏一个 token 映射 ⇒ 校验必须 FAIL
  python -X utf8 place_dsl.py --crosscheck         # 与 SOB0ARGS 的 args_json / slot / dir_token 逐行对账
  python -X utf8 place_dsl.py --stats              # 只读统计（token 覆盖 / f,b 计数 / unresolved）
"""
import collections
import csv
import hashlib
import json
import os
import sys

# ------------------------------------------------------------------ 路径（稳健解析：不按固定层数硬编码）
HERE = os.path.dirname(os.path.abspath(__file__))
# 本脚本原开发位置 `子代理工作区\ISSUE-20261008-09\PLACE\`（距工作区根 3 层；⚠️ **历史副本，勿用**），
# 入库后位于 `工程\<译名>\编程组\新源侧\PLACE\`（5 层）。按固定层数推「工作区根」入库即错
# （表现为找不到输入、或 import place_dsl 失败）。故改为多候选解析（就近优先）：
#   ① 环境变量 `GRETA_WS_ROOT` / `--ws-root <dir>` 显式覆盖（最高优先）；
#   ② 自脚本目录向上搜索含 `Galgame.md` 的目录（就近者 = worktree 根）；
#   ③ 继续向上把其余含 `Galgame.md` 的祖先列为候选（worktree 嵌套在工作区内时，
#      可命中真实工作区里已生成、被 `.gitignore` 的中间件；**只读，不写回**）。
_WS_ENV = "GRETA_WS_ROOT"


def _candidate_roots():
    env = os.environ.get(_WS_ENV)
    if env:
        return [os.path.abspath(env)]        # 显式指定 ⇒ 唯一根（不再向上回退）
    roots = []
    d = HERE
    while True:
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            roots.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    seen, out = set(), []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    if not out:                     # 兜底：按入库位置（5 层）推导
        out = [os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))]
    return out


WS_ROOTS = _candidate_roots()
WS = WS_ROOTS[0]
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
_SOB0_REL = os.path.join(PROJ_REL, "SOB0解码")
# SOB0ARGS 的**可选对账件** `解出_*_args.tsv`（仅 `--crosscheck` 用；该件属已剔出库的可再生中间件）：
#   ① 入库后同树兄弟 `工程\<译名>\编程组\新源侧\SOB0ARGS\`（**优先**）；
#   ② 旧开发位置 `子代理工作区\ISSUE-20261008-09\SOB0ARGS\`（⚠️ **历史副本，勿用**，仅兜底）。
_ARGS_CANDS = [os.path.join(PROJ_REL, "新源侧", "SOB0ARGS"),
               os.path.join("子代理工作区", "ISSUE-20261008-09", "SOB0ARGS")]


def _resolve_input(rel_file, rel_dir):
    """按候选根顺序找输入文件；返回 (目录绝对路径, 是否命中)。未命中退回最近根的 rel_dir。"""
    for r in WS_ROOTS:
        p = os.path.join(r, rel_file)
        if os.path.isfile(p):
            return os.path.dirname(p), True
    return os.path.join(WS_ROOTS[0], rel_dir), False


def _resolve_args_dir():
    """按「新源侧兄弟 → 旧开发位置」顺序找 SOB0ARGS 对账件所在目录。"""
    for rel in _ARGS_CANDS:
        for r in WS_ROOTS:
            p = os.path.join(r, rel, "解出_ot_args.tsv")
            if os.path.isfile(p):
                return os.path.dirname(p)
    return os.path.join(WS_ROOTS[0], _ARGS_CANDS[1])


SOB0_DIR, SOB0_OK = _resolve_input(os.path.join(_SOB0_REL, "解出_ot.tsv"), _SOB0_REL)
ARGS_DIR = _resolve_args_dir()
SRCS = ("ot", "otr", "otp")


def set_ws_root(root):
    """`--ws-root` 显式覆盖：**唯一根**（不再向上回退），并重算输入目录（就地改模块全局）。"""
    global WS_ROOTS, WS, SOB0_DIR, SOB0_OK, ARGS_DIR
    root = os.path.abspath(root)
    WS_ROOTS = [root]
    WS = root
    SOB0_DIR, SOB0_OK = _resolve_input(os.path.join(_SOB0_REL, "解出_ot.tsv"), _SOB0_REL)
    ARGS_DIR = _resolve_args_dir()
    return SOB0_DIR


def missing_inputs():
    """返回缺失的必需输入（绝对路径）。非空 ⇒ 不得把「输入缺失」当「校验失败」。"""
    return [os.path.join(SOB0_DIR, "解出_%s.tsv" % s)
            for s in SRCS if not os.path.isfile(os.path.join(SOB0_DIR, "解出_%s.tsv" % s))]

# ------------------------------------------------------------------ 1920 画布常量
CENTER_X = 960          # c / !c  : 内部 C=320 x3
LEFT_X = 504            # l       : 内部 C-W/4=168 x3
RIGHT_X = 1416          # r       : 内部 C+W/4=472 x3
STEP_X = 75             # <N / >N : 内部 25N x3
STEP_Y = 75             # -N / +N : 内部 25N x3
BOTTOM_Y = 1076         # d / 默认 : 底边对齐基准（实机 800x600 底边 598 → 1080*598/600 ≈ 1076）
TOP_Y = 0               # u       : 顶对齐
OFFSCREEN_LEFT = "!l"   # x = -W（W=容器宽，未跟踪）⇒ 本批只给类别不给像素
OFFSCREEN_RIGHT = "!r"  # x = +W
# 画外判据（1920 系）: 金标 `!l` → cx<0 → x1920<0 ; 金标 `!r` → cx>=1500 → x1920>=2250
OFF_LEFT_PRED = ("lt", 0)
OFF_RIGHT_PRED = ("ge", 2250)

# ------------------------------------------------------------------ DSL 表（唯一真值源；变异自证会改写它）
#   token 形态 → (类别, 数据)  类别 ∈ abs / off / stepx / stepy / yabs / hold / flag / arg / unk
DSL = {
    "c":   ("abs", CENTER_X),
    "l":   ("abs", LEFT_X),
    "r":   ("abs", RIGHT_X),
    "!c":  ("abs", CENTER_X),      # EXE_POS §2.2: `!c` → x = V（绝对）；实测映射恰为 640=中央
    "!l":  ("off", "left"),
    "!r":  ("off", "right"),
    "<N":  ("stepx", -STEP_X),     # x -= 75N
    ">N":  ("stepx", +STEP_X),     # x += 75N
    "-N":  ("stepy", -STEP_Y),     # y -= 75N
    "+N":  ("stepy", +STEP_Y),     # y += 75N
    "u":   ("yabs", TOP_Y),        # 顶对齐
    "d":   ("yabs", BOTTOM_Y),     # 底边对齐
    "$":   ("hold", None),
    "%":   ("hold", None),
    "[":   ("hold", None),
    "]":   ("hold", None),
    "^":   ("hold", None),
    "_":   ("hold", None),
    " ":   ("hold", None),         # 分隔符，不动位置
    "f":   ("flag", "fb"),         # Front 标志（置 [esp+0x38]=1）：**层序规则未覆盖**
    "b":   ("flag", "fb"),         # Back  标志（置 [esp+0x38]=2）
    "i":   ("flag", "io"),         # 置 [esp+0x28]=0xFF（疑 In）
    "o":   ("flag", "io"),         # 置 [esp+0x28]=0（疑 Out）
    "a":   ("arg", "float"),       # 吞「可选符号 + 浮点」，不动位置
}
# **未覆盖**（DSL 表里没有）：显式 unresolved，绝不猜
UNRESOLVED_TOKENS = {
    "<":   "裸 `<`（无数字）：EXE_POS §2.2 有「无数字 sub esi,0x19」分支（⇒ -25），"
           "但 SOB0ARGS §八 项9 实测其出现在多步转场序列（`<>`/`<_ >_ ...`）中，两说不合 ⇒ 标 unresolved",
    ">":   "裸 `>`（无数字）：同上（EXE_POS 有 add esi,0x19 分支，SOB0ARGS 判为步记号）",
    "-":   "裸 `-`（无数字）：EXE_POS 未给 `-`/`+` 的无数字分支，标 unresolved",
    "+":   "裸 `+`（无数字）：同上",
    "L":   "字符 `L`（0x402E97 单字符处理器）：语义未跟踪",
    "DIG": "顶层裸数字（idx8 处理器 0x402E74；字符类含 0-9）：语义未跟踪（疑为 ms 时长，未证）",
    "CHR": "idx8 字符类内的其它字符（\"#&'()*,./:;=?@A-Z\\`eghjkmnpqst）：语义未跟踪",
    "!X":  "`!` 后接非 l/r/c：未覆盖",
}
# 注: `$ % [ ] ^ _` 之后的「可选数字」由该处理器自身吞掉（EXE_POS §2.2）⇒ 不算顶层裸数字。

# ------------------------------------------------------------------ 立绘族注册表
#   与 `SOB0ARGS\\args_promote.py` 的 FAMILY 逐字一致（值 = 实参下标，None = 该族无此项）。
#   V 号每源本地（ot/otr 共用一套，otp 另一套）。
FAMILY = {
    "ot": {
        "0x1C43C": dict(argc=6, role="CharacterOpen", name=4, ms=3, slot=5, ctrl=None),
        "0x1C5B0": dict(argc=3, role="CharacterDelete", name=None, ms=2, slot=None, ctrl=None),
        "0x18B74": dict(argc=4, role="CharacterAction/Move", name=None, ms=1, slot=3, ctrl=2),
        "0x19808": dict(argc=3, role="CharacterActionEnd", name=None, ms=None, slot=2, ctrl=None),
        "0x186C8": dict(argc=3, role="CharacterOpen(chr_in)", name=None, ms=None, slot=2, ctrl=1),
        "0x10428": dict(argc=6, role="未定（说明§5.3 曾记 bg_anime）", name=None, ms=4, slot=None, ctrl=5),
        "0x14084": dict(argc=3, role="未定（高频，CharacterOpen 候选）", name=1, ms=None, slot=2, ctrl=None),
        "0x17514": dict(argc=4, role="未定（高频，与 0x14084 恒相邻）", name=None, ms=None, slot=3, ctrl=None),
    },
    "otp": {
        "0x1A618": dict(argc=4, role="CharacterOpen", name=2, ms=1, slot=3, ctrl=None),
        "0x11078": dict(argc=3, role="未定（高频，0x14084 对应族）", name=1, ms=None, slot=2, ctrl=None),
        "0x14534": dict(argc=4, role="未定（高频，0x17514 对应族）", name=None, ms=None, slot=3, ctrl=None),
        "0x15BAC": dict(argc=4, role="CharacterAction/Move", name=None, ms=1, slot=3, ctrl=2),
        "0x16828": dict(argc=3, role="CharacterActionEnd", name=None, ms=None, slot=2, ctrl=None),
        "0x156E8": dict(argc=4, role="CharacterOpen(chr_in)", name=None, ms=None, slot=3, ctrl=2),
        "0x1A970": dict(argc=1, role="CharacterDelete", name=None, ms=None, slot=None, ctrl=None),
    },
}
FAMILY["otr"] = FAMILY["ot"]

# fam 短名（输出列 fam 用）
FAM_SHORT = {
    "CharacterOpen": "open",
    "CharacterDelete": "del",
    "CharacterAction/Move": "anime",
    "CharacterActionEnd": "end",
    "CharacterOpen(chr_in)": "in",
}


def fam_short(role):
    if role in FAM_SHORT:
        return FAM_SHORT[role]
    # 未定族：用 V 号做稳定短名
    return "unk"


# ------------------------------------------------------------------ evidence 解析（★ 不得用非贪婪正则）
def split_top(body, depth_chars=("(", ")")):
    """括号感知的顶层逗号切分。**不 strip**（逐字保真）。"""
    out, cur, depth = [], [], 0
    for ch in body:
        if ch == depth_chars[0]:
            depth += 1
        elif ch == depth_chars[1]:
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def parse_args_from_evidence(ev):
    """`args=[` 到 ` ctrl=` 的全部内容 → 实参原文数组。无 args= 段返回 None。"""
    i = ev.find("args=[")
    if i < 0:
        return None
    j = ev.find(" ctrl=", i)
    if j < 0:
        j = len(ev)
    body = ev[i + len("args=["):j]
    if body.endswith("]"):
        body = body[:-1]
    if body == "":
        return []
    return split_top(body)


def parse_ctrl_from_evidence(ev):
    """`ctrl=` 之后的控制串原文。`None` → 返回 None。"""
    i = ev.rfind("ctrl=")
    if i < 0:
        return None
    tail = ev[i + len("ctrl="):]
    if tail.startswith("'"):
        k = tail.find("'", 1)
        return tail[1:k] if k >= 0 else tail[1:]
    tok = tail.split(" ", 1)[0]
    if tok == "None":
        return None
    if tok.startswith("'"):
        return tok
    return tok


def arg_uint(raw):
    """`N:123` → 123（无符号 32 位十进制）；非 N: 返回 None。`N:4294967295` → -1 哨兵保留原值。"""
    if raw.startswith("N:"):
        try:
            return int(raw[2:])
        except ValueError:
            return None
    return None


def arg_str(raw):
    """`S:xxx` → xxx（逐字，不 strip）。"""
    if raw.startswith("S:"):
        return raw[2:]
    return None


# ------------------------------------------------------------------ DSL 词法/求值
class Unk(object):
    """未覆盖项。"""
    __slots__ = ("form", "reason", "pos")

    def __init__(self, form, reason, pos):
        self.form, self.reason, self.pos = form, reason, pos

    def __repr__(self):
        return "Unk(%r@%d)" % (self.form, self.pos)


def tokenize_ctrl(s, dsl=None):
    """控制串 → (ops, unks)。
    ops: list of (kind, data, raw, pos)   kind ∈ abs/off/stepx/stepy/yabs/hold/flag/arg
    unks: list of Unk
    """
    dsl = DSL if dsl is None else dsl
    ops, unks = [], []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "!":
            if i + 1 < n and s[i + 1] in "lrc":
                form = "!" + s[i + 1]
                ent = dsl.get(form)
                if ent is None:
                    unks.append(Unk(form, "DSL 表中无此 token", i))
                else:
                    ops.append((ent[0], ent[1], form, i))
                i += 2
                continue
            unks.append(Unk("!", UNRESOLVED_TOKENS["!X"], i))
            i += 1
            continue
        if ch in ("<", ">"):
            j = i + 1
            num = ""
            while j < n and s[j].isdigit():
                num += s[j]
                j += 1
            if num == "":
                unks.append(Unk(ch, UNRESOLVED_TOKENS[ch], i))
                i = j
                continue
            key = ch + "N"
            ent = dsl.get(key)
            if ent is None:
                unks.append(Unk(ch + num, "DSL 表中无此 token", i))
            else:
                ops.append((ent[0], ent[1] * int(num), ch + num, i))
            i = j
            continue
        if ch in ("-", "+"):
            j = i + 1
            num = ""
            while j < n and s[j].isdigit():
                num += s[j]
                j += 1
            if num == "":
                unks.append(Unk(ch, UNRESOLVED_TOKENS[ch], i))
                i = j
                continue
            key = ch + "N"
            ent = dsl.get(key)
            if ent is None:
                unks.append(Unk(ch + num, "DSL 表中无此 token", i))
            else:
                ops.append((ent[0], ent[1] * int(num), ch + num, i))
            i = j
            continue
        if ch == "a":                       # 吞「可选符号 + 浮点」
            j = i + 1
            if j < n and s[j] in "+-":
                j += 1
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            ops.append(("arg", s[i:j], s[i:j], i))
            i = j
            continue
        if ch.isdigit():                    # 顶层裸数字 = idx8，未跟踪
            j = i
            while j < n and s[j].isdigit():
                j += 1
            unks.append(Unk(s[i:j], UNRESOLVED_TOKENS["DIG"], i))
            i = j
            continue
        ent = dsl.get(ch)
        if ent is None:
            unks.append(Unk(ch, UNRESOLVED_TOKENS["CHR"], i))
            i += 1
            continue
        kind, data = ent
        if ch in "$%[]^_ ":
            # `$ % [ ] ^ _` 只吞可选数字（EXE_POS §2.2）；空格为分隔符
            j = i + 1
            if ch != " ":
                while j < n and s[j].isdigit():
                    j += 1
            ops.append((kind, data, s[i:j], i))
            i = j
            continue
        ops.append((kind, data, ch, i))
        i += 1
    return ops, unks


# 位置状态: x 为 None | ("num", v) | ("off", "left"/"right")；y 为数值
UNANCHORED = None
# "state"  = 逐 (scene_id, slot) 累积（引擎「所有方位 token 写增量」的语义；覆盖纯相对/保持档，
#             但槽号会被**不同角色先后复用** ⇒ 跨行状态会漂移，见报告 §五）
# "static" = 每行只用**本行控制串内**的锚点求值（无锚则未解）—— **本批交付采用**
# "auto"   = 有自身锚点者取 static，其余取 state
MODE = "static"


def new_state():
    return {"x": UNANCHORED, "y": BOTTOM_Y}


def apply_ops(ops, st):
    """把 ops 施加到状态 st（原地）。返回 st。"""
    for kind, data, raw, pos in ops:
        if kind == "abs":
            st["x"] = ("num", data)
        elif kind == "off":
            st["x"] = ("off", data)
        elif kind == "stepx":
            if st["x"] and st["x"][0] == "num":
                st["x"] = ("num", st["x"][1] + data)
            elif st["x"] and st["x"][0] == "off":
                pass                    # 画外后相对步进的落点需 W（未跟踪）⇒ 保持画外类别
            else:
                pass                    # 未锚定 ⇒ 仍未锚定（不算锚）
        elif kind == "stepy":
            st["y"] = st["y"] + data
        elif kind == "yabs":
            st["y"] = data
        # hold / flag / arg 不动位置
    return st


def static_eval(ctrl, dsl=None):
    """无前序状态（锚点只来自本串）时求值 → (x, y, anchored, unks)。"""
    ops, unks = tokenize_ctrl(ctrl, dsl)
    st = new_state()
    apply_ops(ops, st)
    return st["x"], st["y"], st["x"] is not None, unks


# ------------------------------------------------------------------ 行装载
def load_src_rows(src):
    """读 编程组\\SOB0解码\\解出_<src>.tsv，解析 evidence，返回全部行（含非立绘族）。"""
    p = os.path.join(SOB0_DIR, "解出_%s.tsv" % src)
    out = []
    with open(p, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f, delimiter="\t")
        base_cols = rd.fieldnames
        for idx, row in enumerate(rd):
            ev = row["evidence"]
            args = parse_args_from_evidence(ev)
            ctrl = parse_ctrl_from_evidence(ev)
            out.append(dict(
                file_idx=idx, scene_id=row["scene_id"], seq=int(row["seq"]),
                op=row["op"], arg3=row["arg3"], evidence=ev,
                args=args, ctrl=ctrl, base_cols=base_cols,
                slot_raw=row.get("slot") or "",
            ))
    return out


def family_of(src, arg3):
    v = (arg3 or "").replace("V=", "")
    fam = FAMILY.get(src, {})
    if v in fam:
        return v, fam[v]
    return v, None


def row_fields(src, r, dsl=None):
    """对一行立绘族行解出 name / slot / ctrl / 位置。返回 dict。"""
    v, fdef = family_of(src, r["arg3"])
    d = dict(v=v, fdef=fdef, name=None, slot=None, ctrl=None)
    if fdef is None:
        return d
    args = r["args"] or []
    if fdef["name"] is not None and fdef["name"] < len(args):
        s = arg_str(args[fdef["name"]])
        if s:
            d["name"] = s
    if fdef["slot"] is not None and fdef["slot"] < len(args):
        n = arg_uint(args[fdef["slot"]])
        if n is not None:
            d["slot"] = n
    if fdef["ctrl"] is not None and fdef["ctrl"] < len(args):
        s = arg_str(args[fdef["ctrl"]])
        if s is not None:
            d["ctrl"] = s
    return d


# ------------------------------------------------------------------ 主构建（状态机）
def build_rows(src, dsl=None, mode=None):
    """返回该源的立绘族行（含 x1920 / y1920 / conf 等中间量）。
    mode: None → 用模块级 MODE；"state" → 逐 (scene_id, slot) 累积；"static" → 仅用本行串内锚点。
    """
    dsl = DSL if dsl is None else dsl
    mode = MODE if mode is None else mode
    raw = load_src_rows(src)
    fam_rows = []
    for r in raw:
        v, fdef = family_of(src, r["arg3"])
        if fdef is None:
            continue
        f = row_fields(src, r, dsl)
        fam_rows.append((r, f))
    # ord = 同一 (scene_id, seq) 内立绘族行的 0 基序号（文件序）
    counter = collections.Counter()
    for r, f in fam_rows:
        k = (r["scene_id"], r["seq"])
        f["ord"] = counter[k]
        counter[k] += 1
    # 两次求值：
    #   static —— 只用**本行控制串内**的绝对锚点（c/l/r/!c/!l/!r 及其后的 <N/>N 步进），
    #             与引擎「绝对档由 dx = 目标 - 当前 实现」逐条对应，**不依赖任何前序状态**。
    #   state  —— 逐 (scene_id, slot) 累积（引擎「所有方位 token 写增量」的语义），
    #             覆盖纯相对 / 保持档（`>N` `<N` `_ $ [ ] ^ % u d +N -N`），但会被前序误差污染。
    # mode: static / state / auto（默认: auto = 有自身锚点者取 static，其余取 state）
    def _ok(ctrl):
        if ctrl is None:
            return None
        ops, unks = tokenize_ctrl(ctrl, dsl)
        if unks:
            return None
        return ops

    sres = {}
    for r, f in fam_rows:
        ops = _ok(f["ctrl"])
        if ops is None:
            continue
        st = new_state()
        apply_ops(ops, st)
        if st["x"] is None:
            continue
        if st["x"][0] == "num":
            xv, cls = st["x"][1], "num"
        else:
            xv, cls = None, st["x"][0] + "_" + st["x"][1]
        sres[r["file_idx"]] = dict(x=xv, x_class=cls, y=st["y"], pos_from="static",
                                   has_fb=("f" in f["ctrl"]) or ("b" in f["ctrl"]))

    qres = {}
    states = {}
    for r, f in sorted(fam_rows, key=lambda t: (t[0]["scene_id"], t[0]["seq"], t[1]["ord"])):
        if f["slot"] is None:
            continue
        key = (r["scene_id"], f["slot"])
        st = states.setdefault(key, new_state())
        ops = _ok(f["ctrl"])
        if ops is None:
            continue
        apply_ops(ops, st)
        if st["x"] is None:
            continue
        if st["x"][0] == "num":
            xv, cls = st["x"][1], "num"
        else:
            xv, cls = None, st["x"][0] + "_" + st["x"][1]
        qres[r["file_idx"]] = dict(x=xv, x_class=cls, y=st["y"], pos_from="state",
                                   has_fb=("f" in f["ctrl"]) or ("b" in f["ctrl"]))

    if mode == "static":
        pick = lambda fi: sres.get(fi)
    elif mode == "state":
        pick = lambda fi: qres.get(fi)
    else:
        pick = lambda fi: (sres.get(fi) or qres.get(fi))

    for r, f in fam_rows:
        fi = r["file_idx"]
        ctrl = f["ctrl"]
        has_fb = bool(ctrl) and (("f" in ctrl) or ("b" in ctrl))
        f["has_fb"] = has_fb
        unks = []
        if ctrl is not None:
            _, unks = tokenize_ctrl(ctrl, dsl)
        f["unks"] = unks
        got = pick(fi)
        if f["slot"] is None:
            f["conf"] = "slot缺"
        elif unks:
            f["conf"] = "token未覆盖"
        elif got is None:
            f["conf"] = "token未覆盖"
        elif has_fb:
            f["conf"] = "fb待定"
        else:
            f["conf"] = "DSL已解"
        if got is None:
            f.update(x=None, y=None, x_class=None, pos_from="")
        else:
            f.update(x=got["x"], x_class=got["x_class"], y=got["y"],
                     pos_from=got.get("pos_from", ""))
    # 恢复文件序
    fam_rows.sort(key=lambda t: t[0]["file_idx"])
    return fam_rows


# ------------------------------------------------------------------ 词表统计
def token_stats(dsl=None):
    """统计全语料控制串里的 token 形态出现次数（按行的控制串计）。"""
    dsl = DSL if dsl is None else dsl
    cnt = collections.Counter()      # 形态 → 行数
    occ = collections.Counter()      # 形态 → 出现次数
    unkcnt = collections.Counter()   # 未覆盖形态 → 出现次数
    fb_rows = collections.Counter()  # src → f/b 前缀行数
    fb_letter = collections.Counter()  # (src, 首字符) → 行数
    ctrl_rows = collections.Counter()
    unresolved_rows = collections.Counter()
    for src in SRCS:
        for r in load_src_rows(src):
            v, fdef = family_of(src, r["arg3"])
            if fdef is None:
                continue
            f = row_fields(src, r, dsl)
            ctrl = f["ctrl"]
            if ctrl is None:
                continue
            ctrl_rows[src] += 1
            ops, unks = tokenize_ctrl(ctrl, dsl)
            seen = set()
            for kind, data, rawt, pos in ops:
                occ[rawt] += 1
                seen.add(rawt)
            for u in unks:
                occ[u.form] += 1
                unkcnt[u.form] += 1
                seen.add(u.form)
            for t in seen:
                cnt[t] += 1
            if unks:
                unresolved_rows[src] += 1
            if ctrl[:1] in ("f", "b"):
                fb_rows[src] += 1
                fb_letter[(src, ctrl[:1])] += 1
    return dict(cnt=cnt, occ=occ, unkcnt=unkcnt, fb_rows=fb_rows,
                fb_letter=fb_letter, ctrl_rows=ctrl_rows,
                unresolved_rows=unresolved_rows)


# ------------------------------------------------------------------ 产物写出
OUT_IMPL = "位置DSL实现表.tsv"
OUT_UNK = "未覆盖token清单.tsv"
OUT_FB = "f_b前缀行.tsv"
OUT_ROWS = "place_dsl_rows_%s.tsv"

IMPL_HEADER = ["形态", "类别", "展开式(1920)", "值", "依据", "状态",
               "语料出现次数(次)", "语料出现行数(行)"]

IMPL_ROWS = [
    ("c",   "abs",   "x := 960",                       "960",  "EXE_POS §2.2: dx = C - x；C=320(内部)x3", "已解"),
    ("l",   "abs",   "x := 504",                       "504",  "EXE_POS §2.2: dx = (C-W/4) - x；168x3",   "已解"),
    ("r",   "abs",   "x := 1416",                      "1416", "EXE_POS §2.2: dx = (C+W/4) - x；472x3",   "已解"),
    ("!c",  "abs",   "x := 960",                       "960",  "EXE_POS §2.2: dx = V - x；实测 V=640(1280)", "已解"),
    ("!l",  "off",   "x := -W（画外左）",               "(类别)", "EXE_POS §2.2: dx = -(x+W)；W 未跟踪",      "已解(无像素)"),
    ("!r",  "off",   "x := +W（画外右）",               "(类别)", "EXE_POS §2.2: dx = W - x；W 未跟踪",       "已解(无像素)"),
    ("<N",  "stepx", "x -= 75N",                       "75/单位", "EXE_POS §2.2: esi += -25N；25x3",         "已解"),
    (">N",  "stepx", "x += 75N",                       "75/单位", "EXE_POS §2.2: esi += +25N",               "已解"),
    ("-N",  "stepy", "y -= 75N",                       "75/单位", "EXE_POS §2.2: 改 edi（y）",                "已解"),
    ("+N",  "stepy", "y += 75N",                       "75/单位", "EXE_POS §2.2: 改 edi（y）",                "已解"),
    ("u",   "yabs",  "y := 0",                         "0",    "EXE_POS §2.2: edi = -y（顶端）",            "已解"),
    ("d",   "yabs",  "y := 1076（底边）",               "1076", "EXE_POS §2.2: edi = V2-H-y；实机底边 598@800x600", "已解"),
    ("$",   "hold",  "不动位置（吞可选数字）",           "—",    "EXE_POS §2.2: 六字符合一分支只 call 0x402920", "已解"),
    ("%",   "hold",  "不动位置（吞可选数字）",           "—",    "同上",                                     "已解"),
    ("[",   "hold",  "不动位置（吞可选数字）",           "—",    "同上",                                     "已解"),
    ("]",   "hold",  "不动位置（吞可选数字）",           "—",    "同上",                                     "已解"),
    ("^",   "hold",  "不动位置（吞可选数字）",           "—",    "同上",                                     "已解"),
    ("_",   "hold",  "不动位置（吞可选数字）",           "—",    "同上",                                     "已解"),
    ("(空格)", "hold", "不动位置（分隔符）",             "—",    "字符分派 idx0 ' ' → 0x402B2E",              "已解"),
    ("f",   "flag",  "不动位置；置 Front 标志",          "—",    "EXE_POS §2.2: [esp+0x38]=1（疑 Front/Back）", "层序未覆盖"),
    ("b",   "flag",  "不动位置；置 Back 标志",           "—",    "EXE_POS §2.2: [esp+0x38]=2",                "层序未覆盖"),
    ("i",   "flag",  "不动位置；置 [esp+0x28]=0xFF",     "—",    "EXE_POS §2.2（疑 In）",                     "已解(不涉位置)"),
    ("o",   "flag",  "不动位置；置 [esp+0x28]=0",        "—",    "EXE_POS §2.2（疑 Out）",                    "已解(不涉位置)"),
    ("a",   "arg",   "不动位置；吞可选符号+浮点",         "—",    "EXE_POS §2.2",                              "已解(不涉位置)"),
    ("<",   "unk",   "unresolved",                     "—",    "EXE_POS 有「无数字 -25」分支，SOB0ARGS 判为步记号，两说不合", "unresolved"),
    (">",   "unk",   "unresolved",                     "—",    "同上",                                     "unresolved"),
    ("-",   "unk",   "unresolved",                     "—",    "EXE_POS 未给无数字分支",                     "unresolved"),
    ("+",   "unk",   "unresolved",                     "—",    "同上",                                     "unresolved"),
    ("L",   "unk",   "unresolved",                     "—",    "0x402E97 单字符处理器语义未跟踪",             "unresolved"),
    ("(顶层裸数字)", "unk", "unresolved",                "—",    "idx8 0x402E74，语义未跟踪（疑 ms 时长）",     "unresolved"),
    ("(idx8 其它字符)", "unk", "unresolved",             "—",    "idx8 0x402E74 字符类内其它字符",             "unresolved"),
]


import re as _re

_HANDLER_CHARS = set("clrud$%[]^_fbioa!L<>+-") | set(" ")


NL = chr(10)
TAB = chr(9)


def _pat():
    return {
        "<N": lambda k: _re.fullmatch(r"<[0-9]+", k) is not None,
        ">N": lambda k: _re.fullmatch(r">[0-9]+", k) is not None,
        "-N": lambda k: _re.fullmatch(r"-[0-9]+", k) is not None,
        "+N": lambda k: _re.fullmatch(r"[+][0-9]+", k) is not None,
        "a": lambda k: k.startswith("a") and _re.fullmatch(r"a[+-]?[0-9.]*", k) is not None,
        "(顶层裸数字)": lambda k: k.isdigit(),
    }


def _is_idx8_other(k):
    """既不是已登记 token 形态、也不是顶层裸数字的其余形态（idx8 处理器字符类）。"""
    if not k or k.isdigit():
        return False
    for _key, pred in _pat().items():
        if pred(k):
            return False
    return k[0] not in _HANDLER_CHARS


def _count_for(form, occ, cnt):
    if form == "(idx8 其它字符)":
        pred = _is_idx8_other
    else:
        pred = _pat().get(form)
        if pred is None:
            key = " " if form == "(空格)" else form
            return occ.get(key, 0), cnt.get(key, 0)
    return (sum(v for k, v in occ.items() if pred(k)),
            sum(v for k, v in cnt.items() if pred(k)))


def write_impl_table(stats):
    occ, cnt = stats["occ"], stats["cnt"]
    out = [TAB.join(IMPL_HEADER)]
    for form, kind, expr, val, src, status in IMPL_ROWS:
        o, c = _count_for(form, occ, cnt)
        out.append(TAB.join([form, kind, expr, val, src, status, str(o), str(c)]))
    return NL.join(out) + NL


def write_unk_table(stats):
    head = ["形态", "unresolved 原因", "语料出现次数(次)", "语料出现行数(行)"]
    out = [TAB.join(head)]
    occ, cnt = stats["occ"], stats["cnt"]
    rows = []
    for k, v in stats["unkcnt"].items():
        if k.isdigit():
            reason = UNRESOLVED_TOKENS["DIG"]
            disp = "(顶层裸数字)"
        elif k in UNRESOLVED_TOKENS:
            reason = UNRESOLVED_TOKENS[k]
            disp = k
        else:
            reason = UNRESOLVED_TOKENS["CHR"]
            disp = k
        o, c = v, cnt.get(k, 0)
        rows.append((k, reason, o, c))
    rows.sort(key=lambda t: -t[2])
    for k, reason, o, c in rows:
        out.append(TAB.join([k, reason, str(o), str(c)]))
    dg_o = sum(v for k, v in stats["unkcnt"].items() if k.isdigit())
    dg_c = sum(v for k, v in cnt.items() if k.isdigit())
    out.append(TAB.join(["(顶层裸数字 合计)", UNRESOLVED_TOKENS["DIG"], str(dg_o), str(dg_c)]))
    tot_c = sum(stats["unresolved_rows"].values())
    out.append(TAB.join(["(unresolved 行合计)", "含任一无覆盖 token 的行数（跨源）", "", str(tot_c)]))
    return NL.join(out) + NL

def write_fb_table(src, dsl=None):
    """f/b 前缀行单独成表（层序规则未覆盖）。"""
    head = ["scene_id", "src", "seq", "ord", "fam", "name", "slot", "ctrl",
            "dir_head", "x1920", "y1920", "conf", "层序"]
    lines = ["\t".join(head)]
    for r, f in build_rows(src, dsl):
        if not f.get("has_fb"):
            continue
        ctrl = f.get("ctrl") or ""
        ops, unks = tokenize_ctrl(ctrl)
        # 去掉 f/b 标志后的首个方位 token（供人读）
        stripped = ctrl.replace("f", "").replace("b", "")
        head_tok = ""
        for kind, data, rawt, pos in ops:
            if kind in ("abs", "off", "stepx", "stepy"):
                head_tok = rawt
                break
        lines.append("\t".join([
            r["scene_id"], src, str(r["seq"]), str(f["ord"]),
            fam_short(f["fdef"]["role"]), f.get("name") or "",
            "" if f.get("slot") is None else str(f["slot"]),
            ctrl, head_tok,
            "" if f.get("x") is None else str(f["x"]),
            "" if f.get("y") is None else str(f["y"]),
            f.get("conf") or "", "层序规则未覆盖(f/b 标志)",
        ]))
    return "\n".join(lines) + "\n"


def write_rows_tsv(src, dsl=None):
    """中间产物：逐行位置（供 C 模块合并层序）。"""
    head = ["scene_id", "src", "seq", "ord", "V", "fam", "name", "slot", "ctrl",
            "x1920", "y1920", "x_class", "pos_from", "conf", "unks", "evidence"]
    lines = ["\t".join(head)]
    for r, f in build_rows(src, dsl):
        unk = ";".join(u.form for u in f.get("unks") or [])
        lines.append("\t".join([
            r["scene_id"], src, str(r["seq"]), str(f["ord"]), f["v"],
            fam_short(f["fdef"]["role"]), f.get("name") or "",
            "" if f.get("slot") is None else str(f["slot"]),
            f.get("ctrl") if f.get("ctrl") is not None else "",
            "" if f.get("x") is None else str(f["x"]),
            "" if f.get("y") is None else str(f["y"]),
            f.get("x_class") or "", f.get("pos_from") or "", f.get("conf") or "",
            unk, r["evidence"],
        ]))
    return "\n".join(lines) + "\n"


def artifacts(dsl=None):
    """返回 {文件名: 内容}（全部由当前 DSL 决定）。"""
    stats = token_stats(dsl)
    out = {
        OUT_IMPL: write_impl_table(stats),
        OUT_UNK: write_unk_table(stats),
    }
    # f_b 表按源分别生成后再合并（保留一份表头）
    fb_lines = None
    for src in SRCS:
        t = write_fb_table(src, dsl)
        if fb_lines is None:
            fb_lines = t
        else:
            fb_lines += "\n".join(t.split("\n")[1:])
    out[OUT_FB] = fb_lines
    for src in SRCS:
        out[OUT_ROWS % src] = write_rows_tsv(src, dsl)
    return out


# ------------------------------------------------------------------ 校验
def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]


# 已剔出库的可再生中间件（见 `..\说明.md` §三）：缺席不算失败，`--emit` 可重出。
OPTIONAL_ARTS = tuple(OUT_ROWS % s for s in SRCS)


def do_check(mutate=None, quiet=False):
    dsl = dict(DSL)
    if mutate:
        dsl[mutate[0]] = mutate[1]
    arts = artifacts(dsl)
    allpass, ndiff = True, 0
    for name in sorted(arts):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            if name in OPTIONAL_ARTS:
                print("  SKIP     %-28s (已剔出库的可再生中间件；--emit 可重出)" % name)
                continue
            print("  MISS     %-28s (磁盘缺文件)" % name)
            allpass, ndiff = False, ndiff + 1
            continue
        with open(p, "rb") as f:
            ondisk = f.read()
        new = arts[name].encode("utf-8")
        if sha_bytes(ondisk) == sha_bytes(new):
            print("  OK       %-28s %d bytes  sha256=%s" % (name, len(ondisk), sha_bytes(ondisk)))
        else:
            # 行级差异数
            a = ondisk.decode("utf-8").splitlines()
            b = arts[name].splitlines()
            d = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            print("  DIFF     %-28s %d 行不一致" % (name, d))
            allpass, ndiff = False, ndiff + 1
    print("ALL_PASS=%s  files=%d  diff_files=%d" % (allpass, len(arts), ndiff))
    print("READONLY=True（本模式不写任何文件）")
    return allpass


def do_emit():
    arts = artifacts()
    for name in sorted(arts):
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(arts[name])
    for name in sorted(arts):
        b = arts[name].encode("utf-8")
        print("  WROTE %-28s %d bytes  sha256=%s" % (name, len(b), sha_bytes(b)))
    return True


def do_crosscheck():
    """与 SOB0ARGS 的 args_json / slot / dir_token 逐行对账（只读）。"""
    import re as _re
    TOKRE = _re.compile(r"![clr]|[lr]?[<>]\d+|[clr][+-]\d+|[<>]|[clr]|[+-]\d+|[du]|[_$]")
    grand = 0
    grand_diff = 0
    for src in SRCS:
        p = os.path.join(ARGS_DIR, "解出_%s_args.tsv" % src)
        n = 0
        d_args = d_slot = d_tok = 0
        if not os.path.exists(p):
            print("  SKIP %s (缺 %s)" % (src, p))
            continue
        with open(p, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                ev = row["evidence"]
                mine = parse_args_from_evidence(ev)
                theirs = json.loads(row["args_json"])
                n += 1
                if mine != theirs:
                    d_args += 1
                fdef = family_of(src, row["arg3"])[1]
                if fdef is None:
                    continue
                # slot 逐行对账（仅原表 slot 非空行 + 注册表族）
                fld = row_fields(src, dict(arg3=row["arg3"], evidence=ev,
                                           args=mine, ctrl=None))
                my_slot = fld["slot"]
                th_slot = row["slot"]
                if th_slot != "" and my_slot is not None and str(my_slot) != th_slot:
                    d_slot += 1
                # dir_token 逐行对账（控制串取自**该族的 ctrl 实参位**，不是 evidence 的 ctrl= 字段）
                ctrl = fld["ctrl"]
                my_tok = ""
                if ctrl:
                    m = TOKRE.search(ctrl)
                    if m:
                        my_tok = m.group(0)
                if my_tok != (row["dir_token"] or ""):
                    d_tok += 1
        print("  %-4s 行数=%d  args 差异=%d  slot 差异=%d  dir_token 差异=%d"
              % (src, n, d_args, d_slot, d_tok))
        grand += n
        grand_diff += d_args + d_slot + d_tok
    print("CROSSCHECK rows=%d total_diff=%d" % (grand, grand_diff))
    return grand_diff == 0


def do_stats():
    st = token_stats()
    print("== 控制串行数（立绘族内有字符串控制串）==")
    tot = 0
    for src in SRCS:
        print("  %-4s %d" % (src, st["ctrl_rows"][src]))
        tot += st["ctrl_rows"][src]
    print("  合计 %d" % tot)
    print()
    print("== 未覆盖行数（控制串含 unresolved token）==")
    ut = 0
    for src in SRCS:
        print("  %-4s %d" % (src, st["unresolved_rows"][src]))
        ut += st["unresolved_rows"][src]
    print("  合计 %d" % ut)
    print()
    print("== f / b 前缀行（任务书要求统计：控制串**以 f 或 b 开头**）（按源）==")
    ft = 0
    for src in SRCS:
        print("  %-4s %d" % (src, st["fb_rows"][src]))
        ft += st["fb_rows"][src]
    print("  合计 %d" % ft)
    print("  分字母前缀行数：%s"
          % ", ".join("%s/%s=%d" % (src, ch, st["fb_letter"][(src, ch)])
                      for src in SRCS for ch in ("f", "b")))
    tot_l = collections.Counter()
    for (src, ch), v in st["fb_letter"].items():
        tot_l[ch] += v
    print("  全语料合计：f=%d 行，b=%d 行" % (tot_l["f"], tot_l["b"]))
    print()
    print("== 含 f/b 标志的行（标志出现在**任一位置**；conf=fb待定 与 f_b前缀行.tsv 用此口径）==")
    ft2 = 0
    for src in SRCS:
        n = sum(1 for r, f in build_rows(src) if f.get("has_fb"))
        print("  %-4s %d" % (src, n))
        ft2 += n
    print("  合计 %d" % ft2)
    print()
    print("== token 形态出现次数（前 40）==")
    for k, v in st["occ"].most_common(40):
        tag = "UNK" if (k in UNRESOLVED_TOKENS or k.isdigit()
                        or k in ("<", ">", "-", "+", "L")) else ""
        print("  %6d  %-8r %s" % (v, k, tag))
    print()
    print("== 未覆盖形态清单（全部）==")
    for k, v in sorted(st["unkcnt"].items(), key=lambda t: -t[1]):
        print("  %6d  %r" % (v, k))
    fb = 0
    for k, v in st["occ"].items():
        if k in ("f", "b"):
            fb += v
            print("  f/b 标志出现次数 %r = %d" % (k, v))
    # f/b 前缀行 = 控制串以 f 或 b 开头
    return True


def _ws_root_arg(argv):
    """取 `--ws-root <dir>` / `--ws-root=<dir>`；无则 None。"""
    for i, a in enumerate(argv):
        if a == "--ws-root" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--ws-root="):
            return a.split("=", 1)[1]
    return None


def _guard_inputs(argv, mode):
    """输入缺失 ⇒ 打印 `INPUT_MISSING` + 明确路径，退出码 3（≠ 校验/变异失败）。"""
    miss = missing_inputs()
    if not miss:
        return None
    print("== INPUT_MISSING（%s 无法执行）==" % mode)
    for p in miss:
        print("   缺输入: %s" % p)
    print("  说明: `解出_*.tsv` 被 .gitignore 排除，须先跑")
    print("        python -X utf8 编程组/工具/decode_sob0.py --out 编程组/SOB0解码")
    print("INPUT_MISSING=True  files=%d" % len(miss))
    return 3


def main(argv):
    root = _ws_root_arg(argv)
    if root:
        set_ws_root(root)
    if "--emit" in argv:
        rc = _guard_inputs(argv, "--emit")
        if rc is not None:
            return rc
        do_emit()
        return 0
    if "--check" in argv:
        rc = _guard_inputs(argv, "--check")
        if rc is not None:
            return rc
        ok = do_check()
        return 0 if ok else 1
    if "--selfcheck-mutate" in argv:
        rc = _guard_inputs(argv, "--selfcheck-mutate")
        if rc is not None:
            print("MUTATE_SELFTEST=INPUT_MISSING（输入缺失，未执行变异自证；≠ 变异通过/失败）")
            return rc
        mut = ("l", ("abs", 9999))
        print("== CHECK(MUTATE: DSL['l'] 504 -> 9999) ==")
        ok = do_check(mutate=mut)
        print("MUTATE_SELFTEST=%s（期望 check FAIL）" % ("PASS" if not ok else "FAIL"))
        return 0 if not ok else 1
    if "--crosscheck" in argv:
        ok = do_crosscheck()
        return 0 if ok else 1
    if "--stats" in argv:
        rc = _guard_inputs(argv, "--stats")
        if rc is not None:
            return rc
        do_stats()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
