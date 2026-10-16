#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""args_promote.py —— SOB0 三源（ot/otr/otp）立绘族「32 位实参向量提列 + 方向 token 展开」。

做什么
======
1. 把 `编程组\\SOB0解码\\解出_<src>.tsv`（14 列）的**实参向量**从 `evidence` 的
   `args=[N:…,S:…]` 文本**提升为独立列** `args_json`（+ `argmap` 语义位表）。
2. 把立绘族控制串里的**方向 token 展开为屏幕位置**（`dir_token` / `x_est` / `pos_conf`），
   并把 token→位置的映射与**对 PSV 金标（`PSV演出\\立绘事件流.tsv`）的实测命中率**
   落成 `位置token映射.tsv`。
3. `slot` 列：原表只为 `chr_anime` 一族解出（`decode_sob0.SLOT_FAMILY`）；本批**原地扩展**
   到全部立绘族（对原已覆盖的行**逐行不变**，只填原先为空的格）。

产物（全部落在本脚本同目录）
============================
- `解出_ot_args.tsv` / `解出_otr_args.tsv` / `解出_otp_args.tsv`（★ **已剔出库**的可再生中间件：
  入库副本里可能不存在 ⇒ `--check` 对缺件打印 `SKIP`，**不算失败**；要复现请跑一次默认（生成）模式）
- `位置token映射.tsv`（**入库交付件**，`--check` 逐字节守护）

模式
====
- 无参                 ：生成上述 4 件产物（写盘），随后自动自检一次。
- `--check`            ：**严格只读**。重算全部产物并与磁盘逐字节比对；一致 `ALL_PASS=True`。
- `--selfcheck-mutate` ：**只读**变异自证。把内置映射表故意改坏一处后重跑比对，必须 `ALL_PASS=False`。
- `--ws-root <dir>`    ：显式指定工作区根（唯一根）；亦可用环境变量 `GRETA_WS_ROOT`。

运行前置（★ 2026-10-09 修复：不再按固定层数推路径）
=================================================
必需输入：`<工作区根>\\工程\\我们没有翅膀——格雷塔迦露德与柳木原\\编程组\\SOB0解码\\解出_{ot,otr,otp}.tsv`
（被 `.gitignore` 排除，须先跑 `编程组\\工具\\decode_sob0.py --out 编程组\\SOB0解码` 再生）
＋ `…\\编程组\\PSV演出\\立绘事件流.tsv`。工作区根多候选解析（`--ws-root`/`GRETA_WS_ROOT` ＞
向上搜索 `Galgame.md` 就近者 ＞ 其余祖先，worktree 嵌套时可命中真实工作区里已生成的中间件，只读）。
输入缺失 ⇒ 打印 `INPUT_MISSING` + 缺失路径，**退出码 3**（与 `--check` 失败的 1、变异自证的 0/1 可区分）。
`--verify` **另需**本目录已生成的 `解出_*_args.tsv`（★ 已剔出库的可再生中间件，见「产物」条）——
缺件同样报 `INPUT_MISSING` + 退出码 3（★ 2026-10-09 修复 RV-A R-2：此前直接抛未捕获
`FileNotFoundError`、退出码 1）。

口径与边界（详见 `说明.md`）
==========================
- `evidence` 的 `args=[...]` 文本**不可用非贪婪正则解析**：串实参可含 `]`、坐标串类实参可含 `,`。
  本脚本用「取 `args=[` 到 ` ctrl=` 之间的**全部**内容」+「**括号感知**的顶层逗号切分」，
  对全库 62,290 条带 `argc` 的行**逐行与 `argc` 对账 0 不符**。
- 立绘族的 V 号**每源本地**（`ot`/`otr` 共用一套，`otp` 另一套）；跨源不得搬用 V 号。
- 位置粒度：方向 token 只能给「档位」（中央/左槽/右槽/左外槽/右外槽/画外/半屏），**不是像素坐标**；
  `x_est` 给出的是**该档在 PSV 金标上的实测众数 ×1.5（1920 系）**；命中率逐 token 见 `位置token映射.tsv`。
- 未解的实参位一律写 `未证`，不猜。

只读声明：`--check` / `--selfcheck-mutate` 两条路径**不写任何文件**；只有默认生成模式写盘（只写上面 4 件）。
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ---- 工作区根：多候选解析（**不按固定层数硬编码**；与 PLACE/PAIR 同款，2026-10-09 修复）
# 原开发位置 `子代理工作区\ISSUE-20261008-09\SOB0ARGS\`（距工作区根 3 层）；入库后位于
# `工程\<译名>\编程组\新源侧\SOB0ARGS\`（5 层）。按固定 `HERE/../../..` 推根会在入库后
# 把路径重复拼成 `…\工程\<译名>\工程\<译名>\…` ⇒ 必崩 FileNotFoundError（2026-10-09 审核 RV-C E1）。
# 改为：① `GRETA_WS_ROOT` / `--ws-root <dir>` 显式覆盖（唯一根）；
#       ② 向上搜索含 `Galgame.md` 的目录（就近者）；③ 其余祖先（worktree 嵌套时命中真实
#       工作区里已生成的中间件；**只读，不写回**）。
_WS_ENV = "GRETA_WS_ROOT"


def _candidate_roots():
    env = os.environ.get(_WS_ENV)
    if env:
        return [os.path.abspath(env)]
    roots, d = [], HERE
    while True:
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            roots.append(d)
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
    if not roots:                     # 兜底：按入库位置（5 层）推导
        roots = [os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))]
    return roots


WS_ROOTS = _candidate_roots()
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")


def _resolve_input(rel_file, rel_dir):
    """按候选根顺序找输入文件；返回 (目录绝对路径, 是否命中)。未命中退回最近根的 rel_dir。"""
    for r in WS_ROOTS:
        p = os.path.join(r, rel_file)
        if os.path.isfile(p):
            return os.path.dirname(p), True
    return os.path.join(WS_ROOTS[0], rel_dir), False


SRC_DIR, _SRC_OK = _resolve_input(os.path.join(PROJ_REL, "SOB0解码", "解出_ot.tsv"),
                                  os.path.join(PROJ_REL, "SOB0解码"))
PSV_DIR, _PSV_OK = _resolve_input(os.path.join(PROJ_REL, "PSV演出", "立绘事件流.tsv"),
                                  os.path.join(PROJ_REL, "PSV演出"))

SOURCES = ["ot", "otr", "otp"]


def set_ws_root(root):
    """`--ws-root` 显式覆盖：**唯一根**（不再向上回退），并重算输入目录。"""
    global WS_ROOTS, SRC_DIR, PSV_DIR
    WS_ROOTS = [os.path.abspath(root)]
    SRC_DIR, _ = _resolve_input(os.path.join(PROJ_REL, "SOB0解码", "解出_ot.tsv"),
                                os.path.join(PROJ_REL, "SOB0解码"))
    PSV_DIR, _ = _resolve_input(os.path.join(PROJ_REL, "PSV演出", "立绘事件流.tsv"),
                                os.path.join(PROJ_REL, "PSV演出"))
    return SRC_DIR


def missing_inputs():
    """必需输入缺失清单（绝对路径）。非空 ⇒ 不得把「输入缺失」当「校验/变异失败」。"""
    miss = [os.path.join(SRC_DIR, "解出_%s.tsv" % s) for s in SOURCES
            if not os.path.isfile(os.path.join(SRC_DIR, "解出_%s.tsv" % s))]
    gold = os.path.join(PSV_DIR, "立绘事件流.tsv")
    if not os.path.isfile(gold):
        miss.append(gold)
    return miss


def missing_verify_inputs():
    """`--verify` 的**额外**前置：本目录已生成的 `解出_*_args.tsv`（已剔出库的可再生中间件）。
    缺件时不得以未捕获 FileNotFoundError 崩（2026-10-09 审核 RV-A R-2）⇒ 与缺源输入同款
    报 `INPUT_MISSING` + 退出码 3。"""
    return [os.path.join(HERE, "解出_%s_args.tsv" % s) for s in SOURCES
            if not os.path.isfile(os.path.join(HERE, "解出_%s_args.tsv" % s))]

# ---------------------------------------------------------------- 立绘族注册表
# 每源本地 V 号 → dict(argc=, role=, name=, ms=, slot=, ctrl=)
#   位置项 = 实参下标（0 基，None = 该族无此项）。
#   role 依据：`SOB0解码\说明.md` §5.1/§4.3（严口径 V→PSV Tasktype 众数）+ 本批复核。
#   role 含「未定」的族（0x14084/0x17514/0x11078/0x14534/0x10428）沿用项目既有结论，
#   本批**不给命令名**，仅按实参形态登记位置。
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
    "otr": {
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
# 各 V 允许的 PSV Tasktype 集（严口径「角色对拍」用；未登记 = 不设角色约束）
ROLE_ALLOW = {
    "0x18B74": {"CharacterMove", "CharacterAction"},
    "0x15BAC": {"CharacterMove", "CharacterAction"},
    "0x186C8": {"CharacterOpen", "CharacterOpenBS"},
    "0x156E8": {"CharacterOpen", "CharacterOpenBS"},
    "0x10428": {"SpriteMove", "SpriteBS", "SpriteBG"},
}
# 带方向 token 的族（严口径「PC 侧单节点」的分母只数这些族）
TOKEN_VS = {
    "ot": ["0x18B74", "0x186C8", "0x10428"],
    "otr": ["0x18B74", "0x186C8", "0x10428"],
    "otp": ["0x15BAC", "0x156E8"],
}

# ---------------------------------------------------------------- 主 token 抽取
TOKRE = re.compile(r"![clr]|[lr]?[<>]\d+|[clr][+-]\d+|[<>]|[clr]|[+-]\d+|[du]|[_$]")


def primary_token(ctrl):
    """取控制串里**第一个**方位 token（长优先）；无方位返回 ""。"""
    m = TOKRE.search(ctrl)
    return m.group(0) if m else ""


# token → (档位, map_cx(1280 系), 粒度类别, 判据)
#   粒度类别 ∈ {pixel, tier, range, hold, vert, unsolved}
#   判据 ∈ ("eq",v) | ("lt",v) | ("gt",v) | ("ge",v) | ("band",lo,hi) | ("none",)
TOKEN_MAP = {
    "c": ("中央", 640, "pixel", ("eq", 640)),
    "!c": ("中央", 640, "pixel", ("eq", 640)),
    "l": ("左槽", 336, "pixel", ("eq", 336)),
    "r": ("右槽", 944, "pixel", ("eq", 944)),
    "l<2": ("左外槽", 236, "pixel", ("eq", 236)),
    "r>2": ("右外槽", 1044, "pixel", ("eq", 1044)),
    "<2": ("左外槽", 236, "tier", ("band", -64, 236)),
    ">2": ("右外槽", 1044, "tier", ("band", 740, 1144)),
    "!l": ("画外左", None, "range", ("lt", 0)),
    "!r": ("画外右", None, "range", ("ge", 1500)),
    "_": ("无方位（姿态/动画控制）", None, "hold", ("none",)),
    "$": ("无方位（姿态/动画控制）", None, "hold", ("none",)),
    "d": ("纵向（不涉 x）", None, "vert", ("none",)),
    "u": ("纵向（不涉 x）", None, "vert", ("none",)),
}
OFFSET_RE = re.compile(r"^[clr]?[+-]\d+$")     # `c±N` / 裸 `±N`：E5 §4.2「基准仍中央」
LSLOT_RE = re.compile(r"^l<\d+$")
RSLOT_RE = re.compile(r"^r>\d+$")
LCOARSE_RE = re.compile(r"^<\d+$")             # 裸 `<N`（N≥1，**必须带数字**）
RCOARSE_RE = re.compile(r"^>\d+$")
# 裸 `<` / `>`（**不带数字**）实为「多步转场序列」的步记号（如 `<> <3 <2 b >5`、
# `<_ >_ <_ >_`、`+ <> + <> +`）⇒ **不给方向档**，标未证。

GRAN_LABEL = {
    "pixel": "像素档（档内固定值）",
    "tier": "档位（档内值域宽）",
    "range": "不等式（画外）",
    "hold": "保持（无位移）",
    "vert": "纵向（不涉 x）",
    "unsolved": "未证（无位置预测）",
}


def classify_token(tok):
    """token → (档位, map_cx, 粒度类别, 判据, 备注)。未证 token 走 unsolved。"""
    if tok == "":
        return ("无方位 token", None, "unsolved", ("none",), "控制串内无方位字符")
    if tok in TOKEN_MAP:
        t, cx, g, p = TOKEN_MAP[tok]
        return (t, cx, g, p, "")
    if OFFSET_RE.match(tok):
        return ("中央", 640, "tier", ("eq", 640), "相对位移式，基准＝中央（E5 §4.2）")
    if LSLOT_RE.match(tok):
        return ("左外槽", None, "tier", ("band", -64, 240), "N≥3：数字语义未证，仅档位")
    if RSLOT_RE.match(tok):
        return ("右外槽", None, "tier", ("band", 940, 1600), "N≥3：数字语义未证，仅档位")
    if LCOARSE_RE.match(tok):
        return ("左半屏", None, "tier", ("lt", 640), "裸 <N：仅由箭头给半屏档（数字语义未证）")
    if RCOARSE_RE.match(tok):
        return ("右半屏", None, "tier", ("gt", 640), "裸 >N：仅由箭头给半屏档（数字语义未证）")
    if tok in ("<", ">"):
        return ("未证", None, "unsolved", ("none",),
                "裸 </> 实为多步转场序列的步记号（如 `<> <3 <2 b >5`），不给方向档")
    return ("未证", None, "unsolved", ("none",), "方向/数字语义未证")


def pred_hit(pred, cx):
    k = pred[0]
    if k == "eq":
        return cx == pred[1]
    if k == "lt":
        return cx < pred[1]
    if k == "gt":
        return cx > pred[1]
    if k == "ge":
        return cx >= pred[1]
    if k == "band":
        return pred[1] <= cx <= pred[2]
    return None


# ---------------------------------------------------------------- 实参解析
ARGS_RE = re.compile(r"args=\[(.*)\]\s+ctrl=")


def split_top(s):
    """顶层逗号切分（括号内逗号不当分隔）。"""
    out, cur, d = [], [], 0
    for ch in s:
        if ch == "(":
            d += 1
        elif ch == ")":
            d -= 1
        if ch == "," and d == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def parse_args(evidence):
    """evidence → list[(kind, value, raw)] 或 None；kind ∈ {N,S,?}。

    `raw` = 该实参的**逐字原文**（**不 strip**：串实参可带尾随空格，
    `args_json` 必须逐字保真——全库实测 25 行有尾随空格）。
    """
    m = ARGS_RE.search(evidence)
    if not m:
        return None
    inner = m.group(1)
    if inner == "":
        return []
    out = []
    for p in split_top(inner):
        if p.startswith("N:"):
            try:
                out.append(("N", int(p[2:]), p))
            except ValueError:
                out.append(("?", p, p))
        elif p.startswith("S:"):
            out.append(("S", p[2:], p))
        else:
            out.append(("?", p, p))
    return out


def args_json_of(args):
    """实参向量 → JSON 数组（**逐 token 原文**：`N:n` / `S:<原串>`）。"""
    return json.dumps([t[2] for t in args], ensure_ascii=False, separators=(",", ":"))


def argmap_of(reg):
    """实参位语义表；已解位写语义名，**未解位写「未证」**。非立绘族返回 ""。"""
    if reg is None:
        return ""
    rev = {}
    for pos, key in ((reg["ms"], "ms"), (reg["name"], "chr_name"),
                     (reg["slot"], "slot"), (reg["ctrl"], "ctrl")):
        if pos is not None:
            rev[pos] = key
    out = collections.OrderedDict()
    for i in range(reg["argc"]):
        out[str(i)] = rev.get(i, "未证")
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------- 载入
def load_pc(src):
    path = os.path.join(SRC_DIR, "解出_%s.tsv" % src)
    with io.open(path, encoding="utf-8") as f:
        return path, list(csv.DictReader(f, delimiter="\t"))


def load_gold():
    """PSV 金标：{(scene_id, seq): [(task_type, cx), …]}（只收 cx 非空行）。"""
    gold = collections.defaultdict(list)
    with io.open(os.path.join(PSV_DIR, "立绘事件流.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["cx"].strip() != "":
                gold[(r["scene_id"], int(r["seq"]))].append((r["task_type"], int(r["cx"])))
    return gold


# ---------------------------------------------------------------- 计算
FIELDS_IN = ["scene_id", "seq", "op", "target", "arg1", "arg2", "arg3", "evidence",
             "confidence", "time_ms", "time_frame", "time_family", "time_conf", "slot"]
FIELDS_ADD = ["args_json", "argmap", "dir_token", "x_est", "pos_conf"]
FIELDS_OUT = FIELDS_IN + FIELDS_ADD
NCOL_IN = len(FIELDS_IN)


def _tsv(rows, fields):
    buf = io.StringIO()
    buf.write("\t".join(fields))
    buf.write("\n")
    for rec in rows:
        vals = []
        for f in fields:
            v = rec.get(f, "")
            v = "" if v is None else str(v)
            # TSV 安全性：字段内不得出现 TAB / LF
            v = v.replace("\t", " ").replace("\n", " ").replace("\r", " ")
            vals.append(v)
        buf.write("\t".join(vals))
        buf.write("\n")
    return buf.getvalue()


def compute(pc_by_src, gold, mutate=None):
    """→ (out_texts_by_src, token_table_text, token_summary)"""
    mutate = mutate or {}

    def classify(tok):
        if tok in mutate:
            t, cx, g, p = mutate[tok]
            return (t, cx, g, p, "MUTATED")
        return classify_token(tok)

    stats = {}                      # (src, tok) → dict
    rows_by_src = {}
    for src in SOURCES:
        _, rows = pc_by_src[src]
        fam = FAMILY[src]
        tv = set(TOKEN_VS[src])
        pcc = collections.Counter()          # PC 侧带 token 族的节点数（严口径分母）
        for r in rows:
            mv = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            if mv and mv.group(1) in tv:
                pcc[(r["scene_id"], int(r["seq"]))] += 1

        out = []
        for r in rows:
            mv = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            V = mv.group(1) if mv else None
            reg = fam.get(V)
            args = parse_args(r["evidence"] or "")
            rec = {}
            for k in FIELDS_IN:
                rec[k] = (r.get(k) or "")
            rec["args_json"] = "" if args is None else args_json_of(args)
            rec["argmap"] = argmap_of(reg)
            rec["dir_token"] = ""
            rec["x_est"] = ""
            rec["pos_conf"] = ""
            tok = None
            if reg is not None:
                if args is not None and reg["slot"] is not None and reg["slot"] < len(args) \
                        and args[reg["slot"]][0] == "N":
                    rec["slot"] = str(args[reg["slot"]][1])      # slot 原地扩展
                ci = reg["ctrl"]
                if args is not None and ci is not None and ci < len(args) and args[ci][0] == "S":
                    tok = primary_token(args[ci][1])
                    tier, mcx, gran, pred, note = classify(tok)
                    rec["dir_token"] = tok
                    if mcx is not None:
                        rec["x_est"] = str(int(round(mcx * 1.5)))
                    st = stats.setdefault((src, tok), dict(
                        cnt=0, strict_hit=0, strict_n=0, loose_hit=0, loose_n=0,
                        ce_strict=[], ce_loose=[], ce_n=0, ce_strict_n=0, ce_loose_n=0,
                        tier=tier, cx=mcx, gran=gran, note=note))
                    st["cnt"] += 1
                    st["tier"], st["cx"], st["gran"] = tier, mcx, gran
                    if note:
                        st["note"] = note
                    if gran == "hold":
                        rec["pos_conf"] = "hold"
                    elif gran == "vert":
                        rec["pos_conf"] = "vert"
                    elif gran == "unsolved":
                        rec["pos_conf"] = "unsolved"
                    else:
                        # 画外（不等式）同样**对拍**，只是 pos_conf 记 out
                        rec["pos_conf"] = "out" if pred[0] in ("lt", "ge") else "PENDING"
                        key = (r["scene_id"], int(r["seq"]))
                        g = gold.get(key)
                        if g:
                            st["loose_n"] += 1
                            if any(pred_hit(pred, cx) for _, cx in g):
                                st["loose_hit"] += 1
                            else:
                                st["ce_n"] += 1
                                st["ce_loose_n"] += 1
                                if len(st["ce_loose"]) < 20:
                                    st["ce_loose"].append("%s:%s(psv=%s)"
                                                          % (key[0], key[1],
                                                             ",".join(str(c) for _, c in g)))
                            allow = ROLE_ALLOW.get(V)
                            if pcc[key] == 1 and len(g) == 1 and (allow is None or g[0][0] in allow):
                                st["strict_n"] += 1
                                if pred_hit(pred, g[0][1]):
                                    st["strict_hit"] += 1
                                else:
                                    st["ce_n"] += 1
                                    st["ce_strict_n"] += 1
                                    if len(st["ce_strict"]) < 20:
                                        st["ce_strict"].append("%s:%s(psv=%d,strict)"
                                                               % (key[0], key[1], g[0][1]))
                else:
                    rec["pos_conf"] = "no_token"
            out.append(rec)
        rows_by_src[src] = out

    # 合并 token 统计（跨源）
    merged = {}
    for (src, tok), st in stats.items():
        m = merged.setdefault(tok, dict(counts={}, strict_hit=0, strict_n=0, loose_hit=0,
                                        loose_n=0, ce_strict=[], ce_loose=[], ce_n=0,
                                        ce_strict_n=0, ce_loose_n=0, tier=None, cx=None,
                                        gran=None, note=""))
        m["counts"][src] = st["cnt"]
        for k in ("strict_hit", "strict_n", "loose_hit", "loose_n", "ce_n",
                  "ce_strict_n", "ce_loose_n"):
            m[k] += st[k]
        m["ce_strict"].extend(st["ce_strict"])
        m["ce_loose"].extend(st["ce_loose"])
        m["tier"], m["cx"], m["gran"] = st["tier"], st["cx"], st["gran"]
        if st["note"]:
            m["note"] = st["note"]

    def conf_of(tok):
        m = merged.get(tok)
        if m is None:
            return "unsolved"
        g = m["gran"]
        if g == "hold":
            return "hold"
        if g == "vert":
            return "vert"
        if g == "unsolved":
            return "unsolved"
        if m["strict_n"] == 0:
            return "tier"
        rate = m["strict_hit"] / m["strict_n"]
        return "psv_ok" if rate >= 0.95 else ("psv_lo" if rate >= 0.5 else "psv_bad")

    # 回填 pos_conf（PENDING → 按全库命中率）
    for src in SOURCES:
        for rec in rows_by_src[src]:
            if rec["pos_conf"] == "PENDING":
                rec["pos_conf"] = conf_of(rec["dir_token"])

    out_texts = {s: _tsv(rows_by_src[s], FIELDS_OUT) for s in SOURCES}

    # 位置 token 映射表
    TW = ["token", "count_all", "count_ot", "count_otr", "count_otp",
          "tier", "map_cx1280", "map_x1920", "granularity",
          "strict_hit", "strict_n", "strict_rate",
          "loose_hit", "loose_n", "loose_rate",
          "ce_strict_n", "ce_loose_n", "counterexamples", "note"]
    trows = []
    for tok in sorted(merged, key=lambda t: (-sum(merged[t]["counts"].values()), t)):
        m = merged[tok]
        mcx = m["cx"]
        trows.append({
            "token": tok if tok != "" else "(无方位)",
            "count_all": sum(m["counts"].values()),
            "count_ot": m["counts"].get("ot", 0),
            "count_otr": m["counts"].get("otr", 0),
            "count_otp": m["counts"].get("otp", 0),
            "tier": m["tier"] or "",
            "map_cx1280": "" if mcx is None else mcx,
            "map_x1920": "" if mcx is None else int(round(mcx * 1.5)),
            "granularity": GRAN_LABEL[m["gran"]],
            "strict_hit": m["strict_hit"], "strict_n": m["strict_n"],
            "strict_rate": ("%.4f" % (m["strict_hit"] / m["strict_n"])) if m["strict_n"] else "",
            "loose_hit": m["loose_hit"], "loose_n": m["loose_n"],
            "loose_rate": ("%.4f" % (m["loose_hit"] / m["loose_n"])) if m["loose_n"] else "",
            "ce_strict_n": m["ce_strict_n"],
            "ce_loose_n": m["ce_loose_n"],
            "counterexamples": ";".join((m["ce_strict"] + m["ce_loose"])[:20]),
            "note": m["note"],
        })
    return out_texts, _tsv(trows, TW), merged


# ---------------------------------------------------------------- 主流程
def build_all(mutate=None):
    pc = {s: load_pc(s) for s in SOURCES}
    gold = load_gold()
    out_texts, tok_text, merged = compute(pc, gold, mutate)
    files = collections.OrderedDict()
    for s in SOURCES:
        files[os.path.join(HERE, "解出_%s_args.tsv" % s)] = out_texts[s]
    files[os.path.join(HERE, "位置token映射.tsv")] = tok_text
    return files, merged


def do_generate(mutate=None):
    files, merged = build_all(mutate)
    for path, text in files.items():
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    print("WROTE %d files:" % len(files))
    for path in files:
        sys.stdout.write("   %s  (%d bytes)\n" % (path, len(files[path].encode("utf-8"))))
    return files, merged


def do_check(mutate=None, tag=""):
    files, merged = build_all(mutate)
    all_pass, diffs = True, 0
    print("== CHECK%s ==" % ("(%s)" % tag if tag else ""))
    for path in files:
        want = files[path]
        name = os.path.basename(path)
        if not os.path.isfile(path):
            if name != "位置token映射.tsv":
                # 已剔出库的可再生中间件（见说明.md §三末）⇒ 与 PLACE 同款：SKIP 不算 MISS
                print("  SKIP     %-24s (已剔出库的可再生中间件；默认生成模式可重出)" % name)
                continue
            print("  MISSING  %s" % name)
            all_pass, diffs = False, diffs + 1
            continue
        with io.open(path, encoding="utf-8", newline="") as f:
            got = f.read()
        if got == want:
            print("  OK       %-24s %7d bytes  sha256=%s"
                  % (name, len(want.encode("utf-8")),
                     hashlib.sha256(want.encode("utf-8")).hexdigest()[:16]))
        else:
            gl, wl = got.split("\n"), want.split("\n")
            n = sum(1 for a, b in zip(gl, wl) if a != b) + abs(len(gl) - len(wl))
            print("  DIFF     %-24s %d 行不一致" % (name, n))
            all_pass, diffs = False, diffs + 1
    print("ALL_PASS=%s  files=%d  diff_files=%d" % (all_pass, len(files), diffs))
    print("READONLY=True（本模式不写任何文件）")
    return all_pass


def _ws_root_arg(argv):
    for i, a in enumerate(argv):
        if a == "--ws-root" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--ws-root="):
            return a.split("=", 1)[1]
    return None


def _guard_inputs(mode, need_args=False):
    """输入缺失 ⇒ 打印 `INPUT_MISSING` + 明确路径，返回退出码 3（≠ 校验 1 / 变异 FAIL 1）。
    `need_args=True`（`--verify`）时另查本目录 `解出_*_args.tsv`（已剔出库的可再生中间件）。"""
    miss = missing_inputs() + (missing_verify_inputs() if need_args else [])
    if not miss:
        return None
    print("== INPUT_MISSING（%s 无法执行：输入缺失，非「变异/校验失败」）==" % mode)
    for p in miss:
        print("   缺输入: %s" % p)
    print("  说明: `解出_*.tsv` 被 .gitignore 排除，须先跑：")
    print("        python -X utf8 编程组/工具/decode_sob0.py --out 编程组/SOB0解码")
    if need_args:
        print("  本模式（--verify）另需本目录已生成的 `解出_*_args.tsv`（已剔出库的可再生中间件），先跑：")
        print("        python -X utf8 args_promote.py    # 默认生成模式（只写本目录 4 件产物）")
    print("  再跑本命令，或用 `--ws-root <工作区根>` 指向已有输入的工作区（只读）。")
    print("CHECK_ERROR=INPUT_MISSING  files=%d" % len(miss))
    return 3


def main():
    ap = argparse.ArgumentParser(description="SOB0 立绘族实参提列 + 位置 token 展开")
    ap.add_argument("--check", action="store_true", help="严格只读：重算并逐字节比对")
    ap.add_argument("--verify", action="store_true",
                    help="严格只读：验收项 V1–V7（含 200 行抽样复核 + 全库参数对账）")
    ap.add_argument("--selfcheck-mutate", action="store_true",
                    help="只读变异自证：故意改坏映射表一处，必须 FAIL")
    ap.add_argument("--ws-root", metavar="DIR", default=None,
                    help="显式指定工作区根（唯一根；等价于环境变量 GRETA_WS_ROOT）")
    a = ap.parse_args()
    n = sum([a.check, a.selfcheck_mutate, a.verify])
    if n > 1:
        print("--check / --verify / --selfcheck-mutate 三选一")
        return 2
    if a.ws_root:
        set_ws_root(a.ws_root)
    rc = _guard_inputs("--check" if a.check else ("--verify" if a.verify else
                                                  ("--selfcheck-mutate" if a.selfcheck_mutate else "生成")),
                       need_args=a.verify)
    if rc is not None:
        if a.selfcheck_mutate:
            print("MUTATE_SELFTEST=INPUT_MISSING（输入缺失，未执行变异自证；≠ 变异通过/失败）")
        return rc
    if a.selfcheck_mutate:
        bad = {"l": ("左槽", 9999, "pixel", ("eq", 9999))}
        ok = do_check(mutate=bad, tag="MUTATE: 映射表 l(左槽)=336 → 9999")
        print("MUTATE_SELFTEST=%s（期望 False）" % ("PASS" if not ok else "FAIL"))
        return 0 if not ok else 1
    if a.check:
        return 0 if do_check() else 1
    if a.verify:
        return 0 if do_verify() else 1
    do_generate()
    print()
    ok = do_check()
    print()
    do_verify()
    return 0 if ok else 1


# ---------------------------------------------------------------- 验收自检（只读）
SEED = 20261008
N_SAMPLE = 200


def do_verify():
    import random
    ok_all = True
    print("== VERIFY（严格只读）==")
    # V1/V3：args_json ↔ evidence 逐行一致（全库 + 抽样 200）
    for src in SOURCES:
        rows = list(csv.DictReader(io.open(os.path.join(HERE, "解出_%s_args.tsv" % src),
                                          encoding="utf-8"), delimiter="\t"))
        bad_full = 0
        for r in rows:
            try:
                back = ",".join(str(x) for x in json.loads(r["args_json"])) if r["args_json"] else ""
            except Exception:
                bad_full += 1
                continue
            m = ARGS_RE.search(r["evidence"] or "")
            want = m.group(1) if m else ""
            if back != want:
                bad_full += 1
        rnd = random.Random(SEED)
        idx = sorted(rnd.sample(range(len(rows)), min(N_SAMPLE, len(rows))))
        bad_s = 0
        for i in idx:
            r = rows[i]
            back = ",".join(str(x) for x in json.loads(r["args_json"])) if r["args_json"] else ""
            m = ARGS_RE.search(r["evidence"] or "")
            want = m.group(1) if m else ""
            if back != want:
                bad_s += 1
        good = (bad_full == 0 and bad_s == 0)
        ok_all &= good
        print("  V1/V3 %-4s 全库 %6d 行 差异 %d ｜ 抽样 %d 行(seed=%d) 差异 %d  → %s"
              % (src, len(rows), bad_full, len(idx), SEED, bad_s, "PASS" if good else "FAIL"))
    # V2：表头/列数
    for src in SOURCES:
        with io.open(os.path.join(HERE, "解出_%s_args.tsv" % src), encoding="utf-8") as f:
            hdr = f.readline().rstrip("\n").split("\t")
        good = hdr[:NCOL_IN] == FIELDS_IN and len(hdr) == len(FIELDS_OUT)
        ok_all &= good
        print("  V2  %-4s 列数 %d（原 %d + 追加 %d）表头一致 → %s"
              % (src, len(hdr), NCOL_IN, len(FIELDS_OUT) - NCOL_IN, "PASS" if good else "FAIL"))
    # V4：slot 不变量（原表已填的 slot 值必须原样保留）
    for src in SOURCES:
        orig = list(csv.DictReader(io.open(os.path.join(SRC_DIR, "解出_%s.tsv" % src),
                                          encoding="utf-8"), delimiter="\t"))
        new = list(csv.DictReader(io.open(os.path.join(HERE, "解出_%s_args.tsv" % src),
                                         encoding="utf-8"), delimiter="\t"))
        bad = sum(1 for a, b in zip(orig, new)
                  if (a.get("slot") or "").strip() != "" and a["slot"] != b["slot"])
        good = (bad == 0)
        ok_all &= good
        print("  V4  %-4s 原 slot 非空行的值被改动：%d → %s" % (src, bad, "PASS" if good else "FAIL"))
    # V5：立绘族行数对账（argmap 非空行数 == 注册表各族行数之和）
    for src in SOURCES:
        fam = FAMILY[src]
        want = 0
        for r in csv.DictReader(io.open(os.path.join(SRC_DIR, "解出_%s.tsv" % src),
                                       encoding="utf-8"), delimiter="\t"):
            mv = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            if mv and mv.group(1) in fam:
                want += 1
        got = sum(1 for r in csv.DictReader(io.open(os.path.join(HERE, "解出_%s_args.tsv" % src),
                                                    encoding="utf-8"), delimiter="\t")
                  if r["argmap"].strip())
        good = (want == got)
        ok_all &= good
        print("  V5  %-4s 立绘族行数 期望 %d 实得 %d → %s" % (src, want, got, "PASS" if good else "FAIL"))
    # V6：位置 token 映射表自洽
    trows = list(csv.DictReader(io.open(os.path.join(HERE, "位置token映射.tsv"),
                                        encoding="utf-8"), delimiter="\t"))
    bad = 0
    for r in trows:
        try:
            if int(r["strict_hit"]) > int(r["strict_n"]) or int(r["loose_hit"]) > int(r["loose_n"]):
                bad += 1
            if not r["token"]:
                bad += 1
        except ValueError:
            bad += 1
    good = (bad == 0 and len(trows) > 0)
    ok_all &= good
    print("  V6  位置token映射.tsv %d 行 自洽违规 %d → %s" % (len(trows), bad, "PASS" if good else "FAIL"))
    # V7：逐行列数完整性（TSV 结构不破）
    for src in SOURCES:
        bad = 0
        tot = 0
        with io.open(os.path.join(HERE, "解出_%s_args.tsv" % src), encoding="utf-8") as f:
            next(f)
            for line in f:
                tot += 1
                if line.count("\t") != len(FIELDS_OUT) - 1:
                    bad += 1
        good = (bad == 0)
        ok_all &= good
        print("  V7  %-4s 逐行列数：%d 行，列数异常 %d → %s" % (src, tot, bad, "PASS" if good else "FAIL"))
    # V8：严格只读确认（本模式不写文件）
    print("  V8  READONLY=True（--verify 不写任何文件）")
    print("ALL_PASS=%s" % ok_all)
    return ok_all



if __name__ == "__main__":
    sys.exit(main())
