#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_layer_source.py —— 「层序（Priority）来源」机检闸门（编程组）
================================================================================
闸门口径（用户 2026-10-06 裁定 · ISSUE-20261006-07 固化；2026-10-09 扩第二来源）：
    **层序（Priority）唯一来源 = PSV 脚本的 `:Priority` 字段。**
    任何**非 PSV 来源**的层序写入 ⇒ **FAIL**。
    ★ 2026-10-09 扩展（ISSUE-20261009-07，用户裁决「新源侧接线」）：
      **第二授权来源 = 新源侧 `z_rank`**（`编程组\新源侧\PAIR\立绘落位_{ot,otr,otp}_v2.tsv`
      的 `z_rank` 列，PC 源侧重建），**且只允许在 `--newsrc-place non-gold` 的非金标场**；
      其换算点为 `build_story.layer_z_from_rank`（`z = STAGE_Z + z_rank`，与 PSV 同基准同极性）。
      新来源由 **[D5]（源码方向）+ [E3]（产物独立复算：z 必须逐行等于 STAGE_Z+z_rank，
      且该行 conf 必须属「采用」档、所在场不得是金标场）** 单独把关；
      **金标场（`立绘事件流.tsv` 有行的场）仍只允许 PSV 来源**（E3 反向校验）。

依据（两路独立证据，见 `编程组\层序策略\说明.md`）
--------------------------------------------------
· 实测：PSV 全 498 份脚本 10,309 处 `:Priority` 恒为整数 1..10（无 0 / 无小数 / 无越域）。
· R3 独立复核（`子代理工作区\ISSUE-20261006-07\R3\复核_R3_参数层与层序否定.md` §2.6/§2.8）：
  **PC 侧无任何显式层序携带者** —— `[8][v]`、装载序、命令节点 `k`、`maps[0]` 四路穷尽否定；
  「装载序 = 层序」被 `ot_s01_04l seq62` 证否。⇒ 下游要层序只能按 PSV `priority` 生成。

本器只读，十一项检查（任一不成立即 FAIL 并打印证据行；**缺输入一律 FAIL，不静默通过**）
--------------------------------------------------
  A · 时间线生成侧（源码）：`emit_staging_psv.py` 的 `priority` 列只允许读 `:Priority`
      （RHS 必须引用 `:Priority` 或走 `layer_priority()`）。
  B · 时间线数据（值域）：`时间线.tsv` 每行 `priority` ∈ {"", 1..10}（整数）。
  C · 时间线数据（出处交叉验证，**独立复算**）：每场的每个非空 `priority` 值，
      必须出现在**该场 PSV 脚本**的 `:Priority` 值集合里（注入的合成值即被此捕获）；
      **PSV 脚本缺失 ⇒ FAIL**（不得静默跳过）。
  D · 构建侧（源码）：`build_story.py` 的 stage `z` 只允许来自
      {默认常量 `STAGE_Z`、家族继承 `st["z"]`／`_st["z"]`、常量 0/1、
      **单调递减**的 `layer_z_from_pri(e["pri"])`（otv）／`layer_z_from_pri(e["cpri"])`（金标 gold）、
      本地别名 `_zz`（其**定义侧**亦被本节收紧）}；
      且 `layer_z_from_pri(e["pri"])` 必须由 `src == "otv"` 守卫、
      `layer_z_from_pri(e["cpri"])` 必须由 `cpri` 在场守卫。
      ★ 旧式**递增**表达式 `STAGE_Z + int(e["pri"])` / `STAGE_Z + int(e["cpri"])`
        （＝反极性口径）**已从白名单移除** ⇒ 极性被改回递增时此处立即 FAIL。
      D2 · 构建侧输入（数据）：`演出_otv.tsv` 中 `chr_add` 行 `arg2`（＝喂给 z 的 Priority）
      **必须同时满足** ① 值域 ∈ 1..10；② **出处** ∈ 该场 PSV `:Priority` 值集
      （空串允许＝该行不喂 z）；**PSV 脚本缺失 ⇒ FAIL**。「值域通过、出处失败」者＝域内伪造，
      由 ② 抓住 —— 这是本闸门对「非 PSV 来源」的正面拦截点。
      D3 · 构建侧输入（数据）：`立绘事件流.tsv`（金标）的 `cpri` / `priority`
      （＝喂给 gold 分支 z 的 `:Priority` 值）**必须逐场 ⊆ 该场 PSV `:Priority` 值集**
      （空串允许＝该行不喂 z）；**PSV 脚本缺失 ⇒ FAIL**。
      ★ [打回项 Critical，复审后补] 旧实现只白名单 gold 分支的 z 表达式、却**不校验其数据出处**
      ⇒ 为 4,836 条非空 `cpri` 行重开了「域内伪造」洞；D3 把它重新堵上。
      D4 · **层序极性（源码方向）** [ISSUE-20261008-03 A3 新增]：换算函数 `layer_z_from_pri`
      必须存在、声明 `PRIORITY_MAX = 10`，且函数体含**单调递减**式 `PRIORITY_MAX - int(...)`
      （源义 0＝最前 ⇒ 大 pri 必须小 z）；出现递增式 `STAGE_Z + int(...)` ⇒ FAIL。
      ★ 为什么必须：A/B/C/D2/D3 只验「值来自 PSV 且值域合规」，**不验方向**——极性写反时它们全绿。
      D5 · **新源侧层序来源（源码）** [ISSUE-20261009-07 新增]：`layer_z_from_rank` 必须存在、
      函数体为**单调递增** `STAGE_Z + int(...)`（rank 0＝背 ⇒ 基准层；rank 越大越前）
      且**不得**出现 `STAGE_Z - int(`（反极性）。D 的白名单同时新增 `layer_z_from_rank(_zr)`
      （须由 `newsrc_conf_class(...) == "adopt"` 守卫）与 `_zr` 的定义侧收紧（RHS 须含 `z_rank`）
      ——⇒ 任何「拿别的整数冒充 z_rank」的写法在源码层即被拦下。
  E · 构建物数据：生成的 `krkr\game\story\scene_*.tjs` 里 stage `z` 必须落在允许集
      —— 立绘类 op ∈ [STAGE_Z, STAGE_Z+10]；`se`/`chr_remove` z==0；`bg` z==1；
      **story 缺失/无产物 ⇒ FAIL**（fail loud，不再静默失明）。
      E2 · **层序极性（构建物反推）** [ISSUE-20261008-03 A3 新增]：从构建物 z 反推
      `pri_rec = STAGE_Z + PRIORITY_MAX - z`，须逐场 ∈ 该场 PSV `:Priority` 值集
      （正确极性下必成立；极性写反时 `pri_rec = PRIORITY_MAX - pri` 通常落空 ⇒ FAIL）。
      `z == STAGE_Z` 的行不计（默认层与 `pri==10` 的翻转层不可分）；对称场是已知盲区。
  E3 · 新源侧落位产物（`story\_newsrc_place.tsv`）**独立复算** [ISSUE-20261009-07 新增]：
      逐行由 `(scene_id, seq, name)` 两点式**重查 v2 表**（本器自实现，不复用构建器代码），
      要求：① 命中行 conf ∈「采用」档（DSL已解 / UNP-7 / 源类比 / UNP-1——UNP-1 为
      2026-10-09 采用并打标档）；② `z == STAGE_Z + z_rank`（该行 `z_rank`）；③ 该场**不得**
      是金标场（`立绘事件流.tsv` 有行 ⇒ FAIL）；④ `(x,y)` 与 v2 行 `x1920/y1920` 反算一致。
      回执缺失 ⇒ **跳过（非 FAIL）**——`--newsrc-place off` 的构建本就不产生该文件；
      E2 对回执所覆盖的场**跳过**（其层序出处由本条把关，避免用 PSV 口径误判新来源）。
      `--mutate newsrc-z`（回执某行 z 改坏）⇒ 本条必须 FAIL（可失败性自证）。

数据根口径（修一审 ①）：项目内数据（`时间线.tsv`/`场景映射.tsv`/`演出_otv.tsv`）默认取
**脚本所在 checkout**（worktree），不再默认指向 main；PSV 脚本目录优先取 checkout 树下的
`工程\我们没有翅膀PSV\脚本解包`，缺失时回落 `DEFAULT_DATA_ROOT`。可用 `--data-root`/`--psv-dir`
显式覆盖。运行首行会打印实际校验的数据根与 PSV 目录（显式提示）。

变异自证（`--mutate <kind>`，在**内存**注入非 PSV 层序 / 反极性，不落盘、不改金标数据）
    priority-domain        时间线 priority="77"（越域）                → B FAIL
    priority-provenance    时间线 priority=域内但该场 PSV 无此值        → C FAIL
    otv-arg2-provenance    演出_otv chr_add arg2=域内但该场 PSV 无此值  → D2 FAIL
    gold-cpri-provenance   立绘事件流 cpri/priority=域内但该场 PSV 无此值 → D3 FAIL
    story-z                某立绘 z=77（越域）                          → E FAIL
    build-static           伪源码 `z = fam_index`                      → D FAIL
    gen-static             伪源码 `"priority": k`                      → A FAIL
    polarity-source        `layer_z_from_pri` 函数体改成递增式（反极性）  → D4 FAIL
    polarity-product       构建物某 chr 行 z 镜像成旧极性值              → E2 FAIL
    rank-polarity-source   `layer_z_from_rank` 函数体改成递减式（反极性） → D5 FAIL
    newsrc-z               新源侧回执某行 z 改坏（值域内）              → E3 FAIL
  `--self-test` 依次跑上述十一类变异，逐一断言闸门确实报 FAIL。

退出码：0 ＝ 全部 PASS（或 --self-test 十一类变异全被检出）；1 ＝ 有违规。
用法：
  python -X utf8 工具/audit_layer_source.py [--proj <checkout proj>] [--data-root <根>]
                                            [--psv-dir <PSV脚本解包>] [--timeline <时间线.tsv>]
                                            [--mutate <kind>] [--self-test]
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

DEFAULT_DATA_ROOT = r"E:\ZCode Workspace\Galgame"
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原")
PSV_REL = os.path.join("工程", "我们没有翅膀PSV", "脚本解包")

# ---- 层序策略常量（与 emit_staging_psv.py / build_story.py 同步；改其一必改全部）----
LAYER_SOURCE = "psv :Priority"       # 层序唯一来源
PRIORITY_MIN, PRIORITY_MAX = 1, 10   # PSV 实测值域
STAGE_Z = 10                         # build_story.py 的默认立绘层序
PRIORITY_COL = "priority"
# ★ 层序极性（ISSUE-20261008-03 A3）：源义 **0＝最前**（PSV `:Priority` 自证注释
#   `// [前] 0 <-> 10 [後]`，4,917 行 / 463 文件模板级盖印）⇒ 换算须**关于 pri 单调递减**。
#   唯一换算函数名（构建侧定义；D4 校验其**方向**、E2 校验其**产物反推**）。
LAYER_Z_FN = "layer_z_from_pri"
# ★★ 新源侧层序来源（ISSUE-20261009-07，第二授权来源；**只限非金标场**）：
#   · 换算函数（构建侧定义；D5 校验方向、E3 校验产物逐行复算）；
#   · v2 主表相对 checkout 的路径；conf 的「采用」档（与 build_story.NEWSRC_* 同步，改其一必改全部）。
LAYER_Z_RANK_FN = "layer_z_from_rank"
NEWSRC_TABLE_REL = os.path.join("编程组", "新源侧", "PAIR", "立绘落位_%s_v2.tsv")
NEWSRC_SRCS = ("ot", "otr", "otp")
NEWSRC_ACCEPT_CONF = {"DSL已解", "弱推断(UNP-7)", "默认值未证(UNP-1)",
                      "源类比未对拍(otp)", "源类比未对拍(otr)"}
NEWSRC_PLACE_TSV = "_newsrc_place.tsv"      # 构建物：逐事件回执（story\ 下）

# PSV 脚本里 `:Priority <值>` 的值（值取逗号前第一段；`//` 注释不算）
RE_PSV_PRIORITY = re.compile(r":Priority\s+([^\s/]+)")

_PSV_PRI_CACHE = {}


def read_cp932(p):
    with open(p, "rb") as f:
        return f.read().decode("cp932", "replace")


def read_utf8(p):
    return io.open(p, "r", encoding="utf-8", newline="").read()


def psv_priority_set(psv_dir, script):
    """**独立复算**该 PSV 脚本里出现的全部 `:Priority` 值 → set(str)。
    注意：本函数不复用 emit_staging_psv 的解析实现（刻意换一条解析路径）。"""
    key = (psv_dir, script)
    if key in _PSV_PRI_CACHE:
        return _PSV_PRI_CACHE[key]
    p = os.path.join(psv_dir, script)
    s = set()
    if os.path.isfile(p):
        txt = read_cp932(p)
        for m in RE_PSV_PRIORITY.finditer(txt):
            v = m.group(1).strip().split(",")[0]
            if v:
                s.add(v)
    _PSV_PRI_CACHE[key] = s
    return s


# ================================================================
# 检查 A · 时间线生成侧（源码）
# ================================================================
def check_gen_source(gen_path, src_text=None):
    """`emit_staging_psv.py` 的 priority 列必须引用 `:Priority`（层序唯一来源）。"""
    bad = []
    txt = src_text if src_text is not None else (read_utf8(gen_path) if os.path.isfile(gen_path) else None)
    if txt is None:
        return ["缺生成器源码：%s" % gen_path]
    # 声明常量必须在（代码级声明，ISSUE-20261006-07）
    if 'LAYER_SOURCE' not in txt or 'PRIORITY_FIELD' not in txt:
        bad.append("缺层序策略声明常量（LAYER_SOURCE / PRIORITY_FIELD）")
    # priority 列的写出点：`"priority": <RHS>` / `'priority': <RHS>`
    rhss = re.findall(r"""["']priority["']\s*:\s*([^\n,]+)""", txt)
    if not rhss:
        bad.append('未找到 priority 列写出点（"priority": …）')
    for rhs in rhss:
        r = rhs.strip().lstrip("(").strip()      # 容忍括号包裹（Minor-M6）
        if (":Priority" in r) or r.startswith("layer_priority("):
            continue
        bad.append('priority 列 RHS 未引用 :Priority：%r（层序只能来自 PSV :Priority）' % rhs.strip())
    return bad


# ================================================================
# 检查 B / C · 时间线数据（值域 + 出处）
# ================================================================
def load_timeline(path):
    if not os.path.isfile(path):
        return None
    raw = read_utf8(path)
    lines = raw.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    head = lines[0].split("\t")
    return [dict(zip(head, r.split("\t"))) for r in lines[1:]]


def check_timeline_domain(rows):
    """B：每行 priority ∈ {"", 1..10}。"""
    bad = []
    cnt = Counter()
    for i, r in enumerate(rows):
        v = (r.get(PRIORITY_COL) or "").strip()
        cnt[v if v else "(empty)"] += 1
        if not v:
            continue
        if not re.fullmatch(r"\d+", v) or not (PRIORITY_MIN <= int(v) <= PRIORITY_MAX):
            bad.append("行%d %s priority=%r 越域（PSV 实测值域 %d..%d）"
                       % (i + 2, r.get("scene_id", "?"), v, PRIORITY_MIN, PRIORITY_MAX))
    return bad, cnt


def check_timeline_provenance(rows, psv_dir):
    """C：每场每个非空 priority 值 ∈ 该场 PSV 脚本的 `:Priority` 值集（独立复算）。"""
    bad = []
    per_scene = defaultdict(list)
    script_of = {}
    for r in rows:
        v = (r.get(PRIORITY_COL) or "").strip()
        if not v:
            continue
        sid = (r.get("scene_id") or "").strip()
        per_scene[sid].append(v)
        script_of[sid] = (r.get("script") or "").strip()
    checked = 0
    missing_scripts = 0
    for sid, vals in per_scene.items():
        sc = script_of.get(sid, "")
        if not sc or not os.path.isfile(os.path.join(psv_dir, sc)):
            # ★ [Major-2] 缺 PSV 脚本 ⇒ 出处无法核实，**判 FAIL**（不得静默 OK）
            missing_scripts += 1
            bad.append("%s 的 PSV 脚本缺失（script=%r）⇒ 出处无法核实（fail loud，不静默通过）"
                       % (sid, sc))
            continue
        s = psv_priority_set(psv_dir, sc)
        for v in vals:
            checked += 1
            if v not in s:
                bad.append("%s priority=%r 不在该场 PSV `:Priority` 值集 %s 内（非 PSV 来源）"
                           % (sid, v, sorted(s, key=lambda x: (len(x), x))[:12]))
    return bad, dict(checked=checked, scenes=len(per_scene), missing_scripts=missing_scripts)


# ================================================================
# 检查 D / D2 · 构建侧（源码 + 输入）
# ================================================================
# 允许的 z 表达式（归一化后逐一匹配）：常量 / 继承 / 派生自 PSV :Priority
# ★ [打回项 Critical · 复审后补] gold 分支引入的形态（本地别名 `_zz` ＝ `STAGE_Z + int(e["cpri"])`、
#   家族继承的本地别名 `_st["z"]`）此前未列入白名单 ⇒ D 由 OK 变 ✗（5 条误报）。
#   `_zz` / `_st` 不是「任意可写变量」：`check_build_source()` 另对**定义侧**收紧
#   （`_zz` 的赋值 RHS 必须引用 `cpri`；`_st` 的赋值 RHS 必须取自 `gold_state.get(...)`），
#   故此处白名单**不是放水**——别名一旦被赋成非 PSV 来源，仍在 D 被拦下。
# ✓ 正确的 PSV 派生形态＝**单调递减**的 `layer_z_from_pri(...)`（D4 另校验其方向）；
#   旧式 `STAGE_Z + int(e["pri"])` / `STAGE_Z + int(e["cpri"])`（**递增＝反极性**）**已从白名单移除**
#   —— 一旦有人把极性改回递增，D 立即 FAIL（源码层方向护栏）。
_Z_ALLOW = [
    re.compile(r"^0$"),
    re.compile(r"^1$"),
    re.compile(r"^z$"),
    re.compile(r'^st\["z"\]$'),
    re.compile(r'^_st\["z"\]$'),
    re.compile(r'^state\[.+\]\["z"\]$'),
    re.compile(r"^STAGE_Z$"),
    re.compile(r'^layer_z_from_pri\(e\["pri"\]\)$'),
    re.compile(r'^layer_z_from_pri\(e\["cpri"\]\)$'),
    re.compile(r"^_zz$"),
    re.compile(r'^0\s*\+\s*state\[.+\]\["z"\]$'),
    # ★ 新源侧（ISSUE-20261009-07）：唯一允许形态＝ `layer_z_from_rank(_zr)`（结果存 `_zn`）；
    #   `_zr` / `_zn` 的定义侧由 _Z_ALIAS_DEF 收紧（RHS 必须分别含 `z_rank` / `layer_z_from_rank(`），
    #   调用点须由 `newsrc_conf_class(...)`（conf 采用档）守卫（见 check_build_source）。
    re.compile(r'^layer_z_from_rank\(_zr\)$'),
    re.compile(r"^_zn$"),
]

# 别名定义侧收紧规则：别名 → 赋值 RHS 必须命中的正则（归一化后）
_Z_ALIAS_DEF = [
    (re.compile(r"^_zz$"), re.compile(r'layer_z_from_pri\([^)]*cpri'),
     "_zz 只能由含 `cpri` 的 PSV 派生式（layer_z_from_pri）赋值"),
    (re.compile(r"^_st$"), re.compile(r"^gold_state\.get\("), "_st 只能取自 gold_state.get(...)"),
    # ★ 新源侧（ISSUE-20261009-07）：`_zr`（喂给 layer_z_from_rank 的名次）只能取自 v2 行的
    #   `z_rank` 列；`_zn`（换算结果）只能由 `layer_z_from_rank` 派生 ⇒ 赋成别的整数即 D FAIL
    #   （杜绝「拿下标/序号冒充 z_rank」与「拿别的整数冒充层序」）。
    (re.compile(r"^_zr$"), re.compile(r"z_rank"), "_zr 只能取自 v2 行 `z_rank` 列（新源侧名次）"),
    (re.compile(r"^_zn$"), re.compile(r"layer_z_from_rank\("),
     "_zn 只能由 `layer_z_from_rank(...)` 赋值（新源侧名次 → z 的唯一换算）"),
]


def _norm(expr):
    return re.sub(r"\s+", " ", expr.strip())


def extract_z_exprs(line):
    """扫描一行里所有 `z=<expr>` 的 RHS（**按括号配平切**，故 `int(e["pri"])` 不会被
    逗号/右括号截断）。返回 [expr, ...]。"""
    out = []
    for m in re.finditer(r"\bz\s*=", line):
        i = m.end()
        depth = 0
        start = i
        while i < len(line):
            c = line[i]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif c == "," and depth == 0:
                break
            i += 1
        out.append(line[start:i].strip())
    return out


def check_build_source(build_path, src_text=None):
    """D：`build_story.py` 的 stage `z` 只允许来自允许集；PSV 分支须 otv 守卫。"""
    bad = []
    txt = src_text if src_text is not None else (read_utf8(build_path) if os.path.isfile(build_path) else None)
    if txt is None:
        return ["缺构建器源码：%s" % build_path]
    if not re.search(r"^\s*STAGE_Z\s*=\s*10\s*$", txt, re.M):
        bad.append("未找到默认层序常量 `STAGE_Z = 10`（默认值必须显式声明）")
    lines = txt.split("\n")
    n_hits = 0
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("#"):
            continue
        for expr0 in extract_z_exprs(ln):
            expr = _norm(expr0)
            n_hits += 1
            if not any(p.match(expr) for p in _Z_ALLOW):
                bad.append("%s:%d z=%r 非允许来源（层序只能＝默认 STAGE_Z / 家族继承 / PSV :Priority）"
                           % (os.path.basename(build_path), i + 1, expr))
            # PSV 派生分支必须由 otv 守卫（窗口放宽到 ±12 行；兼容 e["src"] / source 写法，Minor-M8）
            if re.match(r'^layer_z_from_pri\(e\["pri"\]\)$', expr):
                ctx = "\n".join(lines[max(0, i - 12):i + 1])
                if not re.search(r'(?:src|source)\s*\]?\s*==\s*["\']otv["\']', ctx):
                    bad.append("%s:%d `layer_z_from_pri(e[\"pri\"])` 前 12 行无 otv 守卫"
                               % (os.path.basename(build_path), i + 1))
            # ★ [打回项 Critical] gold 分支的 PSV 派生式须由 `cpri` 在场守卫（同 otv 口径）
            #   注意：**只查本行之前**——本行表达式自带 `"cpri"`，带本行查会恒真（失明）。
            if re.match(r'^layer_z_from_pri\(e\["cpri"\]\)$', expr):
                ctx = "\n".join(lines[max(0, i - 4):i])
                if not re.search(r'"cpri"', ctx):
                    bad.append("%s:%d `layer_z_from_pri(e[\"cpri\"])` 前 4 行无 cpri 在场守卫"
                               % (os.path.basename(build_path), i + 1))
            # ★ 新源侧（ISSUE-20261009-07）：rank ⇒ z 的换算必须由 **conf 采用档守卫**
            #   （`newsrc_conf_class(...) == "adopt"`）；否则等于「未采用的 conf 行也喂 z」。
            if re.match(r'^layer_z_from_rank\(_zr\)$', expr):
                ctx = "\n".join(lines[max(0, i - 14):i])
                if not (re.search(r"newsrc_conf_class\(", ctx) and re.search(r'["\']adopt["\']', ctx)):
                    bad.append("%s:%d `layer_z_from_rank(_zr)` 前 14 行无 `newsrc_conf_class` 采用档守卫"
                               % (os.path.basename(build_path), i + 1))
    # ★ 别名定义侧收紧：白名单里的 `_zz` / `_st` 不得被赋成非 PSV 来源
    #   （否则「白名单别名」会成为绕过 D 的后门）
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", ln)
        if not m:
            continue
        name, rhs = m.group(1), _norm(m.group(2))
        for npat, rpat, msg in _Z_ALIAS_DEF:
            if npat.match(name) and not rpat.search(rhs):
                bad.append("%s:%d %s（实际 RHS=%r）"
                           % (os.path.basename(build_path), i + 1, msg, rhs))
    if n_hits == 0:
        bad.append("未找到任何 stage z 写出点（闸门失明，请核对 build_story.py）")
    return bad


# ================================================================
# 检查 D4 · 层级极性（源码方向，ISSUE-20261008-03 A3）
# ================================================================
def check_polarity_source(build_path, src_text=None):
    """D4：构建侧 PSV `:Priority` → z 的换算必须**关于 pri 单调递减**（源义 0＝最前）。

    判据（结构，可失败）：① 声明 `PRIORITY_MAX = 10`；② 换算函数 `layer_z_from_pri` 必须存在，
    且其**函数体**内出现 `PRIORITY_MAX - int(`（＝「大 pri ⇒ 小 z」的方向标记）。
    若把函数体改成递增式（`STAGE_Z + int(s)`）或改常数，本检查 FAIL。
    ★ 为什么需要本条：A/B/C/D2/D3 只验「值来自 PSV 且值域合规」，**不验方向**——
      极性被改反时它们仍全绿。本检查即源码层的方向护栏（产物层另有 `[E2]`）。
    """
    bad = []
    txt = src_text if src_text is not None else (read_utf8(build_path) if os.path.isfile(build_path) else None)
    if txt is None:
        return ["缺构建器源码：%s" % build_path]
    if not re.search(r"^\s*PRIORITY_MAX\s*=\s*10\s*(?:#.*)?$", txt, re.M):
        bad.append("未找到源侧标度上界常量 `PRIORITY_MAX = 10`（极性换算的标度不得缺失）")
    lines = txt.split("\n")
    di = next((i for i, ln in enumerate(lines)
               if re.match(r"^\s*def\s+%s\s*\(" % re.escape(LAYER_Z_FN), ln)), None)
    if di is None:
        bad.append("未找到唯一换算函数 `def %s(...)`（PSV :Priority → z 的换算点）" % LAYER_Z_FN)
        return bad
    indent = len(lines[di]) - len(lines[di].lstrip())
    body = []
    for ln in lines[di + 1:]:
        if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
            break
        body.append(ln)
    body_txt = "\n".join(body)
    # 方向标记：PRIORITY_MAX - int(<pri>) —— 单调递减
    if not re.search(r"PRIORITY_MAX\s*-\s*int\s*\(", body_txt):
        bad.append("%s 的函数体未见**单调递减**式 `PRIORITY_MAX - int(...)`"
                   "（源义 0＝最前 ⇒ 大 pri 必须小 z；递增式＝极性写反）" % LAYER_Z_FN)
    # 反向显式拦截：递增式 `+ int(<pri>)`（防止有人改回旧口径）
    if re.search(r"STAGE_Z\s*\+\s*int\s*\(", body_txt):
        bad.append("%s 的函数体出现**递增**式 `STAGE_Z + int(...)`（＝把 pri 越大放越前，与源义相反）"
                   % LAYER_Z_FN)
    return bad


# ================================================================
# 检查 D5 · 新源侧层序换算（源码方向，ISSUE-20261009-07）
# ================================================================
def check_rank_polarity_source(build_path, src_text=None):
    """D5：新源侧 `z_rank` → z 的换算必须**关于 rank 单调递增**（rank 0＝背；越大越前）。

    判据（结构，可失败）：① 换算函数 `layer_z_from_rank` 必须存在；
    ② 其**函数体**内出现递增式 `STAGE_Z + int(`（＝「rank 越大 ⇒ z 越大」的方向标记）；
    ③ 出现递减式 `STAGE_Z - int(` ⇒ FAIL（方向写反）。
    ★ 为什么需要本条：D 只白名单表达式、不验方向；把 rank 乘 -1 或改成 `STAGE_Z - rank`
      时 D/E 仍可能全绿（z 仍在 [10,20] 值域内）。
    """
    bad = []
    txt = src_text if src_text is not None else (read_utf8(build_path) if os.path.isfile(build_path) else None)
    if txt is None:
        return ["缺构建器源码：%s" % build_path]
    lines = txt.split("\n")
    di = next((i for i, ln in enumerate(lines)
               if re.match(r"^\s*def\s+%s\s*\(" % re.escape(LAYER_Z_RANK_FN), ln)), None)
    if di is None:
        bad.append("未找到换算函数 `def %s(...)`（新源侧 z_rank → z 的换算点缺失）" % LAYER_Z_RANK_FN)
        return bad
    indent = len(lines[di]) - len(lines[di].lstrip())
    body = []
    for ln in lines[di + 1:]:
        if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
            break
        body.append(ln)
    body_txt = "\n".join(body)
    if not re.search(r"STAGE_Z\s*\+\s*int\s*\(", body_txt):
        bad.append("%s 的函数体未见**递增**式 `STAGE_Z + int(...)`"
                   "（rank 0＝背 ⇒ rank 越大 z 越大；缺此式＝方向不明）" % LAYER_Z_RANK_FN)
    if re.search(r"STAGE_Z\s*-\s*int\s*\(", body_txt):
        bad.append("%s 的函数体出现**递减**式 `STAGE_Z - int(...)`（＝把 rank 越大放越后，与源义相反）"
                   % LAYER_Z_RANK_FN)
    return bad


# ================================================================
# 检查 E3 · 新源侧落位产物（story\_newsrc_place.tsv）独立复算（ISSUE-20261009-07）
# ================================================================
def load_newsrc_tables(proj):
    """读 v2 三表 → {scene_id: dict(named=…, lastof=…)}（与构建器**同一取数口径**，本器自实现）。"""
    out = {}
    for src in NEWSRC_SRCS:
        p = os.path.join(proj, NEWSRC_TABLE_REL % src)
        if not os.path.isfile(p):
            continue
        raw = read_utf8(p).split("\n")
        while raw and raw[-1] == "":
            raw.pop()
        if not raw:
            continue
        head = raw[0].split("\t")
        ci = {k: i for i, k in enumerate(head)}
        for ln in raw[1:]:
            c = ln.split("\t")
            if len(c) < len(head):
                continue
            sid = c[ci["scene_id"]].strip()
            seq = c[ci["seq"]].strip()
            slot = c[ci["slot"]].strip()
            nm = c[ci["name"]].strip().upper()
            if not sid:
                continue
            idx = out.setdefault(sid, dict(named={}, lastof={}))
            if nm and slot != "":
                idx["named"][(seq, nm)] = slot
            if slot != "":
                idx["lastof"][(seq, slot)] = {
                    "x1920": c[ci["x1920"]].strip(), "y1920": c[ci["y1920"]].strip(),
                    "z_rank": c[ci["z_rank"]].strip(), "conf": c[ci["conf"]].strip()}
    return out


def load_content_boxes(proj):
    """`UI组\\layout\\_root.json` 的 content_boxes（与构建器同源；缺 ⇒ 全画布兜底）。"""
    p = os.path.join(proj, "UI组", "layout", "_root.json")
    boxes = {}
    if os.path.isfile(p):
        try:
            o = json.loads(read_utf8(p))
            boxes = o.get("content_boxes") or {}
        except Exception:
            boxes = {}
    return boxes


def _num(s):
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return None


def load_newsrc_place_rows(story_dir):
    """读构建物回执 `story\\_newsrc_place.tsv` → [dict(row), ...]；缺文件 ⇒ None（跳过语义）。"""
    p = os.path.join(story_dir, NEWSRC_PLACE_TSV)
    if not os.path.isfile(p):
        return None
    raw = read_utf8(p).split("\n")
    while raw and raw[-1] == "":
        raw.pop()
    if not raw:
        return []
    head = raw[0].split("\t")
    return [dict(zip(head, r.split("\t"))) for r in raw[1:] if "\t" in r]


def check_newsrc_product(story_dir, proj, gold_scenes, rows=None):
    """E3：构建物回执 `story\\_newsrc_place.tsv` 逐行独立复算（口径见文件头）。

    返回 (bad, stats, covered_scenes)。回执缺失（rows=None）⇒ bad=[]、note=跳过（**非 FAIL**）。
    """
    st = dict(rows=0, scenes=0, skipped=0, note="")
    if rows is None:
        st["note"] = ("无 %s（未启用 `--newsrc-place` 的构建；跳过）" % NEWSRC_PLACE_TSV)
        return [], st, set()
    tabs = load_newsrc_tables(proj)
    boxes = load_content_boxes(proj)
    bad = []
    covered = set()
    z_ok = {}          # (scene, runtime_slot) -> {由 z_rank 换算出的 z}（供「继承」判据）
    # 按 (场景, seq 数值) 复算——「同槽 z 继承」判据依赖场内 seq 递增序。
    def _seqnum(d):
        return _num(d.get("seq")) or 0
    for c in sorted(rows, key=lambda d: ((d.get("scene_id") or ""), _seqnum(d))):
        sid = (c.get("scene_id") or "").strip()
        seq = (c.get("seq") or "").strip()
        slot = (c.get("slot") or "").strip()
        name = (c.get("name") or "").strip().upper()
        z = _num(c.get("z"))
        x = _num(c.get("x"))
        y = _num(c.get("y"))
        w = _num(c.get("w"))
        h = _num(c.get("h"))
        st["rows"] += 1
        covered.add(sid)
        # ③ 金标场绝不进本路径
        if sid in gold_scenes:
            bad.append("%s 是金标覆盖场却在 _newsrc_place.tsv 内（金标场只允许 PSV 来源）" % sid)
            continue
        idx = tabs.get(sid)
        if idx is None:
            bad.append("%s 不在新源侧 v2 表内（回执无出处）" % sid)
            continue
        sl = idx["named"].get((seq, name))
        row = idx["lastof"].get((seq, sl)) if sl is not None else None
        if row is None:
            bad.append("%s#%s name=%s 在 v2 表内查无该 (seq,name)→(seq,slot) 行（回执不可复算）"
                       % (sid, seq, name))
            continue
        # ① conf 必须属采用档
        if row["conf"] not in NEWSRC_ACCEPT_CONF:
            bad.append("%s#%s name=%s 的 v2 行 conf=%r 非采用档（不得喂 z）"
                       % (sid, seq, name, row["conf"]))
            continue
        # ② z == STAGE_Z + z_rank；`z_rank` 空 ⇒ 该行不给新层序 ⇒ z 只能是「同场同槽先前
        #    由 z_rank 换算出的值」或默认 STAGE_Z（＝继承语义，不得凭空给第三个数）。
        zr = row["z_rank"]
        zrn = _num(zr)
        if zr != "":
            if zrn is None:
                bad.append("%s#%s name=%s 的 v2 行 z_rank=%r 非整数" % (sid, seq, name, zr))
            elif z != STAGE_Z + zrn:
                bad.append("%s#%s name=%s z=%s ≠ STAGE_Z+z_rank=%d（v2 z_rank=%s）"
                           % (sid, seq, name, c.get("z"), STAGE_Z + zrn, zr))
            else:
                z_ok.setdefault((sid, slot), set()).add(STAGE_Z + zrn)
        else:
            allowed = set(z_ok.get((sid, slot), set())) | {STAGE_Z}
            if z is not None and z not in allowed:
                bad.append("%s#%s name=%s z=%s 但 v2 行 z_rank 为空（既非 STAGE_Z 也未继承"
                           "同场同槽已由 z_rank 换算的层序 %s ⇒ 凭空给层序）"
                           % (sid, seq, name, c.get("z"), sorted(allowed)))
        # ④ (x,y) 反算一致：gx = round(cb.x + x1920*cb.w/1920 − w/2)；gy = round(cb.y + y1920*cb.h/1080 − h)
        src = sid.split("_")[0]
        cb = boxes.get(src) or dict(x=0, y=0, w=1920, h=1080)
        vx, vy = _num(row["x1920"]), _num(row["y1920"])
        if None not in (vx, vy, x, y, w, h):
            gx = int(round(cb["x"] + vx * cb["w"] / 1920.0 - w / 2.0))
            gy = int(round(cb["y"] + vy * cb["h"] / 1080.0 - h))
            if (x, y) != (gx, gy):
                bad.append("%s#%s name=%s (x,y)=(%d,%d) ≠ 由 v2 行 x1920=%s/y1920=%s 反算 (%d,%d)"
                           % (sid, seq, name, x, y, row["x1920"], row["y1920"], gx, gy))
        st["scenes"] = len(covered)
    return bad, st, covered


def load_otv_rows(otv_tsv):
    """读 `演出_otv.tsv` → [dict(row), ...]（内存态，供变异自证）。缺文件返回 []。"""
    if not os.path.isfile(otv_tsv):
        return []
    with io.open(otv_tsv, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# 金标立绘事件流里承载「层序（:Priority）」的两列（其余列不喂 z）
GOLD_PRIORITY_COLS = ("cpri", "priority")


def load_gold_events(path):
    """读 `立绘事件流.tsv`（金标，20 列）→ [dict(row), ...]。缺文件返回 None（fail loud）。"""
    if not os.path.isfile(path):
        return None
    raw = read_utf8(path).split("\n")
    while raw and raw[-1] == "":
        raw.pop()
    head = raw[0].split("\t")
    return [dict(zip(head, r.split("\t"))) for r in raw[1:]]


def load_scene_script(*paths):
    """scene_id → PSV 脚本名。来源优先级：① `场景映射.tsv`；② `时间线.tsv` 的 scene_id/script 列。
    再兜底：由 scene_id 后缀推（`otv_M01_01` → `M01_01`，与 PSV 文件名同形）。"""
    m = {}
    for p in paths:
        if not p or not os.path.isfile(p):
            continue
        try:
            rows = list(csv.DictReader(io.open(p, "r", encoding="utf-8-sig", newline=""),
                                       delimiter="\t"))
        except Exception:
            continue
        for r in rows:
            sid = (r.get("scene_id") or "").strip()
            sc = (r.get("script") or "").strip()
            if sid and sc:
                m.setdefault(sid, sc)
    return m


def scene_script_of(sid, scene_script):
    """取某场的 PSV 脚本名：映射表优先，否则按 scene_id 后缀推。"""
    sc = scene_script.get(sid, "")
    if sc:
        return sc
    return sid.split("_", 1)[1] if "_" in sid else ""


def check_otv_staging(rows, scene_script, psv_dir):
    """D2：`演出_otv.tsv` 中喂给 z 的 `chr_add` 行 arg2（＝Priority）必须
    ① 值域 ∈ 1..10；② **出处** ∈ 该场 PSV 脚本 `:Priority` 值集。
    空串允许（该行不喂 z）。PSV 脚本缺失 ⇒ FAIL。
    `chr_expr`/`chr_move` 不喂 z（chr_expr 恒空、chr_move 的 arg2 是 Time ms、走继承分支），故不检。
    ★ [打回项 Critical] 旧实现只查①，导致「域内伪造」（arg2=7 而该场 PSV 值集={1,2,10}）整体漏检；
      本实现补上②，把「非 PSV 来源」正面拦下。"""
    bad = []
    n_ok = 0
    n_checked = 0
    n_missing_script = 0
    for i, r in enumerate(rows):
        if (r.get("op") or "").strip() != "chr_add":
            continue
        a2 = (r.get("arg2") or "").strip()
        if not a2:
            continue
        sid = (r.get("scene_id") or "").strip()
        # ① 值域
        if not re.fullmatch(r"\d+", a2) or not (PRIORITY_MIN <= int(a2) <= PRIORITY_MAX):
            bad.append("行%d %s chr_add arg2=%r 非 PSV 层序值域" % (i + 2, sid, a2))
            continue
        # ② 出处
        sc = scene_script_of(sid, scene_script)
        if not sc or not os.path.isfile(os.path.join(psv_dir, sc)):
            n_missing_script += 1
            bad.append("%s chr_add arg2=%r 的 PSV 脚本缺失（script=%r）⇒ 出处无法核实（fail loud）"
                       % (sid, a2, sc))
            continue
        s = psv_priority_set(psv_dir, sc)
        n_checked += 1
        if a2 not in s:
            bad.append("%s chr_add arg2=%r 不在该场 PSV `:Priority` 值集 %s 内（非 PSV 来源）"
                       % (sid, a2, sorted(s, key=lambda x: (len(x), x))[:12]))
        else:
            n_ok += 1
    return bad, dict(ok=n_ok, checked=n_checked, missing_script=n_missing_script)


def check_gold_cpri_provenance(rows, scene_script, psv_dir):
    """D3：`立绘事件流.tsv`（金标）的 `cpri` / `priority`（＝喂给 gold 分支 z 的 `:Priority`）
    **必须逐场 ⊆ 该场 PSV `:Priority` 值集**。空串允许（该行不喂 z）；PSV 脚本缺失 ⇒ FAIL。
    ★ [打回项 Critical] gold 分支的 z 来自 `cpri`，旧闸门只白名单表达式、不校验数据出处
      ⇒ 4,836 条非空 `cpri` 行的「域内伪造」无人拦截；本检查即补此缺口（复用 psv_priority_set）。
    """
    bad = []
    per_scene = defaultdict(list)
    script_of = {}
    for r in rows:
        sid = (r.get("scene_id") or "").strip()
        if sid and sid not in script_of:
            script_of[sid] = scene_script_of(sid, scene_script)
        for col in GOLD_PRIORITY_COLS:
            v = (r.get(col) or "").strip()
            if v:
                per_scene[sid].append((col, v))
    checked = 0
    missing_scripts = 0
    for sid, vals in per_scene.items():
        sc = script_of.get(sid, "")
        if not sc or not os.path.isfile(os.path.join(psv_dir, sc)):
            missing_scripts += 1
            bad.append("%s 的 PSV 脚本缺失（script=%r）⇒ cpri/priority 出处无法核实（fail loud）"
                       % (sid, sc))
            continue
        s = psv_priority_set(psv_dir, sc)
        for col, v in vals:
            checked += 1
            if v not in s:
                bad.append("%s %s=%r 不在该场 PSV `:Priority` 值集 %s 内（非 PSV 来源）"
                           % (sid, col, v, sorted(s, key=lambda x: (len(x), x))[:12]))
    return bad, dict(checked=checked, scenes=len(per_scene), missing_scripts=missing_scripts)


# ================================================================
# 检查 E · 构建物数据（best-effort）
# ================================================================
RE_STAGE_ROW = re.compile(r'op:"([^"]*)"[^\]]*?\bz:(-?\d+)')
# ★ [打回项] `chr_z`（金标 `CharacterPriority` ⇒ 只改该槽 z，新 op，ISSUE-20261008-03）
#   此前不在白名单 ⇒ 该 op 的 z **完全不被 E 校验**（闸门对新 op 失明）；补入后其 z 受
#   [STAGE_Z, STAGE_Z+PRIORITY_MAX] 约束。
ALLOWED_CHR_OPS = {"chr_add", "chr_expr", "chr_move", "chr_place", "chr_z"}
ALLOWED_ZERO_OPS = {"se", "chr_remove"}


def check_story(story_dir, rows=None):
    """E：生成物 scene_*.tjs 的 stage z 值域。
    `rows` 传入时用**内存行**（供变异自证），否则现读盘面。
    ★ [Major-3] story 目录缺失 / 无 `scene_*.tjs` ⇒ **判 FAIL**（fail loud），不再静默失明。
    返回 (bad, present, n)：present=False 表示未取到产物（此时 bad 非空）。"""
    if not os.path.isdir(story_dir):
        return (["未找到 story 目录：%s（构建物层序无法校验，fail loud）" % story_dir], False, 0)
    files = [x for x in sorted(os.listdir(story_dir)) if re.match(r"scene_.+\.tjs$", x)]
    if not files:
        return (["story 目录无 `scene_*.tjs` 产物：%s（构建物层序无法校验，fail loud）" % story_dir],
                False, 0)
    if rows is None:
        rows = parse_story_rows(story_dir)
    bad = []
    for row in rows:
        op, z, fn = row["op"], row["z"], row.get("file", "?")
        if op in ALLOWED_CHR_OPS:
            if not (STAGE_Z <= z <= STAGE_Z + PRIORITY_MAX):
                bad.append("%s op=%s z=%d 越域（立绘层序须 ∈ [%d,%d]＝STAGE_Z+PSV priority）"
                           % (fn, op, z, STAGE_Z, STAGE_Z + PRIORITY_MAX))
        elif op in ALLOWED_ZERO_OPS:
            if z != 0:
                bad.append("%s op=%s z=%d（须为 0）" % (fn, op, z))
        elif op == "bg":
            if z != 1:
                bad.append("%s op=bg z=%d（须为 1）" % (fn, z))
    return bad, True, len(rows)


# ================================================================
# 检查 E2 · 层序极性（构建物反推 pri ∈ 源 `:Priority` 值集，ISSUE-20261008-03 A3）
# ================================================================
def check_polarity_product(story_dir, rows, scene_script, psv_dir, skip_scenes=None):
    """E2：从**构建产物**反推 `pri`，校验「z 与源 pri 方向一致」。
    `skip_scenes` ＝ 由 [E3] 单列把关的场（新源侧 z_rank 来源，ISSUE-20261009-07）⇒ 跳过，
    避免拿 PSV 口径误判第二授权来源（其出处/方向由 E3 逐行独立复算）。

    换算既定为 `z = STAGE_Z + (PRIORITY_MAX - pri)`（D4 已证源码方向）⇒ 反推
    `pri_rec = STAGE_Z + PRIORITY_MAX - z`。**正确的极性下** `pri_rec` 必等于该行的源 pri
    （cpri 或 otv pri），而 D2/D3 已证源值 ⊆ 该场 PSV `:Priority` 值集
    ⇒ `pri_rec` 必须 ∈ 该场 PSV 值集。**极性写反**时 `pri_rec = PRIORITY_MAX - pri`
    （如源 pri=9 ⇒ 反推 1）通常落不到该场值集 ⇒ FAIL。

    ★ 可判定边界（如实登记）：
      · `z == STAGE_Z` 的行**不计**——缺 pri 的默认层与 `pri==PRIORITY_MAX` 的翻转层在 z 上不可分；
      · 该场 PSV 脚本缺失 / 无 `:Priority` ⇒ 跳过（出处类检查已由 C/D3 fail loud）；
      · **对称场盲区**：若某场用到的 pri 集合在 `p ↔ PRIORITY_MAX-p` 下自封闭，反极性也可能蒙混过关
        ⇒ 由 `--self-test` 的 `polarity-product` 变异（取非对称场景）证明本检查**确实能 FAIL**。
    返回 (bad, stats)。"""
    bad = []
    if not rows:
        return (["无构建物行（E2 无从校验）"], dict(checked=0, scenes=0, skipped=0))
    per_scene = defaultdict(list)
    for row in rows:
        if row["op"] not in ALLOWED_CHR_OPS:
            continue
        z = row["z"]
        if z == STAGE_Z:
            continue
        m = re.match(r"^scene_(.+)\.tjs$", row.get("file", ""))
        if not m:
            continue
        per_scene[m.group(1)].append(z)
    checked = 0
    scenes = 0
    skipped = 0
    for sid, zs in per_scene.items():
        if skip_scenes and sid in skip_scenes:
            skipped += 1
            continue
        sc = scene_script_of(sid, scene_script)
        if not sc or not os.path.isfile(os.path.join(psv_dir, sc)):
            skipped += 1
            continue
        s = psv_priority_set(psv_dir, sc)
        if not s:
            skipped += 1
            continue
        scenes += 1
        for z in zs:
            checked += 1
            rec = STAGE_Z + PRIORITY_MAX - z
            if str(rec) not in s:
                if len(bad) < 20:
                    bad.append("scene_%s.tjs z=%d 反推 pri=%d 不在该场 PSV `:Priority` 值集 %s 内"
                               "（z 与源 pri 方向不一致？源义 0＝最前 ⇒ 大 pri 须小 z）"
                               % (sid, z, rec, sorted(s, key=lambda x: (len(x), x))[:12]))
    return bad, dict(checked=checked, scenes=scenes, skipped=skipped)


# ================================================================
# 变异自证
# ================================================================
def apply_mutation(kind, data):
    """在**内存**注入非 PSV 来源的层序（不改盘面金标数据）。返回可读描述。"""
    tl = data["timeline_rows"]
    if kind == "priority-domain":
        for r in tl:
            if (r.get(PRIORITY_COL) or "").strip():
                r[PRIORITY_COL] = "77"          # 越域值
                return '时间线 priority 注入 "77"（越域 → 非 PSV 来源）'
        return None
    if kind == "priority-provenance":
        for r in tl:
            sid = (r.get("scene_id") or "").strip()
            sc = (r.get("script") or "").strip()
            s = psv_priority_set(data["psv_dir"], sc)
            if not s:
                continue
            for cand in ("6", "7", "8", "9", "5", "4", "3", "2", "77"):
                if cand not in s and (r.get(PRIORITY_COL) or "").strip():
                    old = r[PRIORITY_COL]
                    r[PRIORITY_COL] = cand
                    return ('时间线 %s priority 注入 %r（1..10 但该场 PSV `:Priority` 无此值：%s → 出处失败）'
                            % (sid, cand, old))
        return None
    if kind == "otv-arg2-provenance":
        # ★ [打回项] 域内伪造：把某 chr_add 行的 arg2 改成 1..10 内、但该场 PSV `:Priority` 无的值
        for r in data.get("otv_rows", []):
            if (r.get("op") or "").strip() != "chr_add":
                continue
            sid = (r.get("scene_id") or "").strip()
            a2 = (r.get("arg2") or "").strip()
            if not sid or not a2:
                continue
            sc = scene_script_of(sid, data.get("scene_script", {}))
            s = psv_priority_set(data["psv_dir"], sc) if sc else set()
            if not s:
                continue
            for cand in ("6", "7", "8", "9", "5", "4", "3", "2"):
                if cand not in s:
                    r["arg2"] = cand
                    return ('演出_otv %s chr_add arg2 注入 %r（1..10 但该场 PSV `:Priority` 值集 %s 无此值：%s → 出处失败）'
                            % (sid, cand, sorted(s, key=lambda x: (len(x), x))[:12], a2))
        return None
    if kind == "gold-cpri-provenance":
        # ★ [打回项] 域内伪造：把某 gold 行的 cpri/priority 改成 1..9 内、但该场 PSV `:Priority` 无的值
        for r in data.get("gold_rows", []):
            sid = (r.get("scene_id") or "").strip()
            sc = scene_script_of(sid, data.get("scene_script", {}))
            s = psv_priority_set(data["psv_dir"], sc) if sc else set()
            if not s:
                continue
            for col in GOLD_PRIORITY_COLS:
                old = (r.get(col) or "").strip()
                if not old:
                    continue
                for cand in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    if cand not in s:
                        r[col] = cand
                        return ('立绘事件流 %s %s 注入 %r（1..9 域内但该场 PSV `:Priority` 值集 %s 无此值：%s → 出处失败）'
                                % (sid, col, cand, sorted(s, key=lambda x: (len(x), x))[:12], old))
        return None
    if kind == "story-z":
        for row in data["story_rows"]:
            if row["op"] in ALLOWED_CHR_OPS:
                row["z"] = 77
                return "生成物 %s op=%s z 注入 77（越域 → 非 PSV 来源）" % (row["file"], row["op"])
        return None
    if kind == "polarity-source":
        # ★ 极性方向变异（ISSUE-20261008-03 A3）：把换算函数体改成**递增**式（旧口径＝反极性）。
        src = data.get("build_src") or ""
        new = re.sub(r"STAGE_Z\s*\+\s*\(\s*PRIORITY_MAX\s*-\s*int\(s\)\s*\)",
                     "STAGE_Z + int(s)", src, count=1)
        if new == src:
            # 兜底：把函数体里任何 `PRIORITY_MAX - int(` 改成 `+ int(`
            new = re.sub(r"PRIORITY_MAX\s*-\s*int\(", "PRIORITY_MAX + int(", src, count=1)
        if new == src:
            return None
        data["build_src"] = new
        return "把 `layer_z_from_pri` 函数体改成**递增**式（`STAGE_Z + int(s)`＝反极性）→ 方向写反"
    if kind == "rank-polarity-source":
        # ★ 新源侧换算方向变异（ISSUE-20261009-07）：把 `layer_z_from_rank` 函数体改成**递减**式。
        src = data.get("build_src") or ""
        new = re.sub(r"STAGE_Z\s*\+\s*int\(", "STAGE_Z - int(", src, count=1)
        if new == src:
            return None
        data["build_src"] = new
        return "把 `layer_z_from_rank` 函数体改成**递减**式（`STAGE_Z - int(s)`＝反极性）→ 方向写反"
    if kind == "polarity-product":
        # ★ 极性方向变异：把某构建物 chr 行 z 镜像成**旧极性值**（等价于旧式 STAGE_Z+pri）。
        for row in data["story_rows"]:
            if row["op"] not in ALLOWED_CHR_OPS:
                continue
            z = row["z"]
            if z == STAGE_Z:
                continue
            m = re.match(r"^scene_(.+)\.tjs$", row.get("file", ""))
            if not m:
                continue
            sid = m.group(1)
            sc = scene_script_of(sid, data.get("scene_script", {}))
            s = psv_priority_set(data["psv_dir"], sc) if sc else set()
            if not s:
                continue
            inv = 2 * STAGE_Z + PRIORITY_MAX - z          # ＝旧极性 z（30 - z）
            if str(STAGE_Z + PRIORITY_MAX - inv) not in s:
                row["z"] = inv
                return ("生成物 %s op=%s z=%d 反转为 %d（反推 pri=%d 不在该场 PSV 值集内 → 极性方向失败）"
                        % (row["file"], row["op"], z, inv, STAGE_Z + PRIORITY_MAX - inv))
        return None
    if kind == "newsrc-z":
        # ★ 新源侧（ISSUE-20261009-07）：把回执里某行的 z 改坏（+1，仍在 [10,20] 值域内）
        #   ⇒ 期望 [E3] 检出「z ≠ STAGE_Z + z_rank」（值域检查抓不到 ⇒ 必须由 E3 复算抓）。
        nr = data.get("newsrc_rows")
        if not nr:
            return None
        for r in nr:
            z = (r.get("z") or "").strip()
            if z:
                old = z
                r["z"] = str(int(z) + 1)
                return ('新源侧回执 %s#%s z：%s → %s（回执被改坏 ⇒ z ≠ STAGE_Z+z_rank）'
                        % (r.get("scene_id"), r.get("seq"), old, r["z"]))
        return None
    if kind == "build-static":
        data["build_src"] = data["build_src"] + '\n        z = fam_index  # MUTANT: 用下标冒充层序\n'
        return "向 build_story.py 伪源码注入 `z = fam_index`（行下标冒充层序）"
    if kind == "gen-static":
        data["gen_src"] = (data["gen_src"] or "") + '\n        "priority": k,  # MUTANT: 用台词序号冒充层序\n'
        return '向 emit_staging_psv.py 伪源码注入 `"priority": k`（台词序号冒充层序）'
    return None


def parse_story_rows(story_dir):
    rows = []
    if not os.path.isdir(story_dir):
        return rows
    for fn in sorted(os.listdir(story_dir)):
        if not re.match(r"scene_.+\.tjs$", fn):
            continue
        txt = read_utf8(os.path.join(story_dir, fn))
        for m in RE_STAGE_ROW.finditer(txt):
            rows.append(dict(file=fn, op=m.group(1), z=int(m.group(2))))
    return rows


# ================================================================
# 主流程
# ================================================================
def resolve(args):
    """解析数据根（修一审 ①）。
    · 项目内数据（时间线/场景映射/演出_otv）默认取**脚本所在 checkout**（worktree），
      不再默认指向 main —— 避免「从 worktree 跑、却校验主树金标」。
    · PSV 脚本目录：优先 checkout 树下的 `工程\\我们没有翅膀PSV\\脚本解包`，缺失时回落 DEFAULT_DATA_ROOT。
    · `--data-root` 显式给出时，项目内数据与 PSV 目录都按该根解析（旧口径）。
    · `--psv-dir` 可直接覆盖 PSV 目录。
    """
    code_proj = args.proj
    if args.data_root:
        data_proj = os.path.join(args.data_root, PROJ_REL)
        psv_dir = args.psv_dir or os.path.join(args.data_root, PSV_REL)
    else:
        data_proj = code_proj
        if args.psv_dir:
            psv_dir = args.psv_dir
        else:
            cands = [os.path.normpath(os.path.join(data_proj, "..", "我们没有翅膀PSV", "脚本解包")),
                     os.path.join(DEFAULT_DATA_ROOT, PSV_REL)]
            psv_dir = next((c for c in cands if os.path.isdir(c)), cands[0])
    # ★ `立绘事件流.tsv` 是**尚未合并的 checkout 本地产物**（同 build_story.py gold 分支，两者必须配套）；
    #   故先按脚本所在 checkout 解析，缺失再回落 data-root（否则 `--data-root` 指向主树时，
    #   闸门会因「主树无此未合并文件」而误判 D3 FAIL）。
    gold_rel = os.path.join("编程组", "PSV演出", "立绘事件流.tsv")
    gold_cands = [os.path.join(code_proj, gold_rel), os.path.join(data_proj, gold_rel)]
    gold_events = next((c for c in gold_cands if os.path.isfile(c)), gold_cands[0])
    return dict(
        code_proj=code_proj, data_proj=data_proj, psv_dir=psv_dir,
        gen=os.path.join(code_proj, "编程组", "工具", "emit_staging_psv.py"),
        build=os.path.join(code_proj, "编程组", "工具", "build_story.py"),
        timeline=args.timeline or os.path.join(data_proj, "编程组", "PSV演出", "时间线.tsv"),
        scene_map=os.path.join(data_proj, "编程组", "PSV演出", "场景映射.tsv"),
        otv=os.path.join(data_proj, "资源组", "演出", "演出_otv.tsv"),
        gold_events=gold_events,
        story=os.path.join(code_proj, "编程组", "krkr", "game", "story"),
    )


def run_all(paths, mutate=None, quiet=False):
    """返回 (ok, lines, evidence)。所有检查集中在此，供 main 与 --self-test 复用。"""
    L = []
    ev = []
    rows = load_timeline(paths["timeline"])
    story_rows = parse_story_rows(paths["story"])
    otv_rows = load_otv_rows(paths["otv"])
    gold_rows = load_gold_events(paths.get("gold_events", ""))
    scene_script = load_scene_script(paths.get("scene_map", ""), paths["timeline"])
    build_src = read_utf8(paths["build"]) if os.path.isfile(paths["build"]) else None
    gen_src = read_utf8(paths["gen"]) if os.path.isfile(paths["gen"]) else None
    # ★ E3 输入：新源侧落位回执（缺 ⇒ None ⇒ 跳过；`--mutate newsrc-z` 在内存改坏它）
    newsrc_rows = load_newsrc_place_rows(paths["story"])
    data = dict(timeline_rows=rows or [], story_rows=story_rows, otv_rows=otv_rows,
                gold_rows=gold_rows or [], scene_script=scene_script, psv_dir=paths["psv_dir"],
                build_src=build_src, gen_src=gen_src, newsrc_rows=newsrc_rows)

    mut_desc = None
    if mutate:
        mut_desc = apply_mutation(mutate, data)
        rows = data["timeline_rows"]
        story_rows = data["story_rows"]
        otv_rows = data["otv_rows"]
        gold_rows = data["gold_rows"]
        build_src = data["build_src"]
        gen_src = data["gen_src"]
        newsrc_rows = data.get("newsrc_rows")

    L.append("=" * 72)
    L.append("层序来源自检（ISSUE-20261006-07）｜层序唯一来源 = %s" % LAYER_SOURCE)
    L.append("数据根(checkout)：%s" % paths.get("data_proj", "?"))
    L.append("PSV 脚本目录：%s" % paths["psv_dir"])
    if mut_desc:
        L.append("★ 变异自证：%s" % mut_desc)
    L.append("-" * 72)

    # A
    a = check_gen_source(paths["gen"], src_text=gen_src)
    L.append("[A] 时间线生成侧源码（priority 列须读 :Priority）：%s" % ("OK" if not a else "✗"))
    for x in a:
        L.append("        " + x)
    ev += a

    # B
    if rows is None:
        b = ["缺时间线：%s" % paths["timeline"]]
        dist = Counter()
    else:
        b, dist = check_timeline_domain(rows)
    L.append("[B] 时间线 priority 值域（须 ∈ {∅,1..10}）：%s ｜ 分布 %s"
             % ("OK" if not b else "✗", dict(dist.most_common(12))))
    for x in b[:8]:
        L.append("        " + x)
    ev += b

    # C
    if rows is None:
        c, cs = ["缺时间线"], {}
    else:
        c, cs = check_timeline_provenance(rows, paths["psv_dir"])
    L.append("[C] 时间线 priority 出处（须 ∈ 该场 PSV `:Priority` 值集）：%s ｜ 核对 %d 值 / %d 场 / 缺脚本 %d"
             % ("OK" if not c else "✗", cs.get("checked", 0), cs.get("scenes", 0),
                cs.get("missing_scripts", 0)))
    for x in c[:8]:
        L.append("        " + x)
    ev += c

    # D
    d = check_build_source(paths["build"], src_text=build_src)
    L.append("[D] 构建侧源码（stage z 来源）：%s" % ("OK" if not d else "✗"))
    for x in d[:8]:
        L.append("        " + x)
    ev += d

    # D2
    if not otv_rows:
        d2bad, d2st = ["缺 `演出_otv.tsv` 或无 chr_add 行：%s（fail loud）" % paths["otv"]], {}
    else:
        d2bad, d2st = check_otv_staging(otv_rows, scene_script, paths["psv_dir"])
    L.append("[D2] 构建侧输入 `演出_otv.tsv` chr_add arg2（须 ∈1..10 且 ∈ 该场 PSV `:Priority` 值集）：%s"
             " ｜ 命中 %d / 核对 %d / 缺脚本 %d"
             % ("OK" if not d2bad else "✗", d2st.get("ok", 0), d2st.get("checked", 0),
                d2st.get("missing_script", 0)))
    for x in d2bad[:8]:
        L.append("        " + x)
    ev += d2bad

    # D3
    if not gold_rows:
        d3bad, d3st = ["缺 `立绘事件流.tsv` 或无金标事件行：%s（fail loud）"
                       % paths.get("gold_events", "?")], {}
    else:
        d3bad, d3st = check_gold_cpri_provenance(gold_rows, scene_script, paths["psv_dir"])
    L.append("[D3] 构建侧输入 `立绘事件流.tsv` cpri/priority（须逐场 ∈ 该场 PSV `:Priority` 值集）：%s"
             " ｜ 核对 %d 值 / %d 场 / 缺脚本 %d"
             % ("OK" if not d3bad else "✗", d3st.get("checked", 0), d3st.get("scenes", 0),
                d3st.get("missing_scripts", 0)))
    for x in d3bad[:8]:
        L.append("        " + x)
    ev += d3bad

    # D4（极性 · 源码方向）
    d4 = check_polarity_source(paths["build"], src_text=build_src)
    L.append("[D4] 层序极性·源码方向（`layer_z_from_pri` 须关于 pri **单调递减**，源义 0＝最前）：%s"
             % ("OK" if not d4 else "✗"))
    for x in d4[:8]:
        L.append("        " + x)
    ev += d4

    # E
    e, present, nrows = check_story(paths["story"], story_rows)
    if not present:
        L.append("[E] 构建物数据：✗ 缺失（未找到 `krkr\\game\\story\\scene_*.tjs`）—— fail loud")
    else:
        L.append("[E] 构建物数据（stage z 值域）：%s ｜ 扫描 %d 行" % ("OK" if not e else "✗", nrows))
    for x in e[:8]:
        L.append("        " + x)
    ev += e

    # D5（新源侧换算 · 源码方向）
    d5 = check_rank_polarity_source(paths["build"], src_text=build_src)
    L.append("[D5] 新源侧层序来源·源码方向（`layer_z_from_rank` 须**单调递增** STAGE_Z+rank，"
             "只服务非金标场）：%s" % ("OK" if not d5 else "✗"))
    for x in d5[:8]:
        L.append("        " + x)
    ev += d5

    # E3（新源侧落位产物 · 独立复算）——先跑，E2 据此跳过其覆盖场
    gold_scene_set = {r.get("scene_id", "").strip() for r in (data.get("gold_rows") or [])}
    e3, e3st, e3cov = check_newsrc_product(paths["story"], paths.get("data_proj", ""), gold_scene_set,
                                           rows=newsrc_rows)
    if e3st.get("note"):
        L.append("[E3] 新源侧落位产物：跳过（%s）" % e3st["note"])
    else:
        L.append("[E3] 新源侧落位产物 `story\\%s` 独立复算（z==STAGE_Z+z_rank ∧ conf 采用档 ∧ "
                 "非金标场 ∧ (x,y) 反算一致）：%s ｜ 回执 %d 行 / %d 场"
                 % (NEWSRC_PLACE_TSV, "OK" if not e3 else "✗", e3st.get("rows", 0), e3st.get("scenes", 0)))
    for x in e3[:8]:
        L.append("        " + x)
    ev += e3

    # E2（极性 · 构建物反推 pri）
    if not present:
        L.append("[E2] 层序极性·构建物反推：✗ 缺失（随 [E] 一并 fail loud；需先定点构建 story）")
    else:
        e2, e2st = check_polarity_product(paths["story"], story_rows, scene_script, paths["psv_dir"],
                                          skip_scenes=e3cov)
        L.append("[E2] 层序极性·构建物反推（z ⇒ pri_rec=STAGE_Z+PRIORITY_MAX-z 须 ∈ 该场 PSV `:Priority` 值集；"
                 "其中 [E3] 覆盖的 %d 场另行把关）：%s ｜ 核对 %d 行 / %d 场 / 跳过 %d"
                 % (len(e3cov), "OK" if not e2 else "✗", e2st.get("checked", 0), e2st.get("scenes", 0),
                    e2st.get("skipped", 0)))
        for x in e2[:8]:
            L.append("        " + x)
        ev += e2

    ok = not ev
    L.append("-" * 72)
    L.append(">>> %s" % ("PASS" if ok else "FAIL"))
    if not quiet:
        print("\n".join(L))
    return ok, L, ev


def main():
    ap = argparse.ArgumentParser(description="层序来源闸门（Priority 只能来自 PSV）")
    ap.add_argument("--proj", default=os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))                     # 工具/ → 编程组/ → <译名>/
    # ★ 默认空 ⇒ 项目内数据取「脚本所在 checkout」（修一审 ①，不再默认指向 main）；
    #   传入 --data-root 才切到该根（旧口径）。
    ap.add_argument("--data-root", default="")
    ap.add_argument("--psv-dir", default="")
    ap.add_argument("--timeline", default="")
    ap.add_argument("--mutate", default="", choices=["", "priority-domain",
                                                     "priority-provenance", "otv-arg2-provenance",
                                                     "gold-cpri-provenance",
                                                     "story-z", "build-static", "gen-static",
                                                     "polarity-source", "polarity-product",
                                                     "newsrc-z", "rank-polarity-source"])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    paths = resolve(args)

    if args.self_test:
        kinds = ["priority-domain", "priority-provenance", "otv-arg2-provenance",
                 "gold-cpri-provenance", "story-z", "build-static", "gen-static",
                 "polarity-source", "polarity-product",
                 "newsrc-z", "rank-polarity-source"]
        print("=" * 72)
        print("变异自证：逐一注入非 PSV 层序 / 反极性，闸门必须 FAIL")
        print("-" * 72)
        allok = True
        for k in kinds:
            ok, _L, ev = run_all(paths, mutate=k, quiet=True)
            detected = (not ok)
            allok = allok and detected
            print("  %-20s 注入后闸门=%s  %s" % (k, "FAIL(已检出)" if detected else "PASS(漏检!)",
                                                (ev[0][:70] if ev else "")))
        print("-" * 72)
        print(">>> %s（%d 类变异 %s）" % ("PASS" if allok else "FAIL", len(kinds),
                                        "均被检出" if allok else "有漏检"))
        return 0 if allok else 1

    ok, _L, _ev = run_all(paths, mutate=args.mutate)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
