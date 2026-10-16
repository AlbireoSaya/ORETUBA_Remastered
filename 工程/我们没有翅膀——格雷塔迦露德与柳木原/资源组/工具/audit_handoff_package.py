# -*- coding: utf-8 -*-
r"""
audit_handoff_package.py — 「资源组 → 编程组」交付包的**一致性自检**（ISSUE-20260930-08）

用途：交付前/上游变更后的**一道闸门**。回答三个问题：
  ① 人读文档里引用的**路径还在不在**？
  ② 文档里写的**计数口径与磁盘一致吗**？
  ③ 有没有**早已作废却仍可能被引用的口径**残留（如「消费基线＝美术统一_超分\」）？

检查项（都能真失败）
  A 引用路径存在性：扫 `编程组开工指南.md` / `交接说明.md` / `美术交付交接件.md` / `自检报告.md`
    里反引号路径 token，逐个解析（**git 检出树 → 主工作区**，两者都试）；缺失即失败（ALLOW 表可豁免并给理由）。
  B 计数口径：**独立复算**（不读生成器声明，直接读数据文件），并与期望值逐项比对。
  C 产物清单：`产物清单.tsv` 行数 == 期望，且**每行路径存在**。
  D 「图片化日文」处置不变量：629 = 132 + 91 + 406（91＝章节题卡/日期条族，2026-10-05 用户改判为保留）；片头 40 == 素材账 `op_*` 全集；片尾 92 == 全部 `CG背景`。
  E 序章开场段：42 行 / 96 步 / 40 字幕条 / 36 语音；影片 2 行均带「占位·待替换」。
  F 过期口径残留：入口文档中「消费基线」与「美术统一_超分」同现的行，必须同时出现
    作废/历史/取代/已改 之类标记，否则失败。
  G 语料残留（ISSUE-20260930-11 新增）：六源 `scene_*.jsonl` 中**非采用变体**（古罗利亚斯／游隼／
    美空学园／美空学府／独立空学院／独立空学／空学园／美空学截断／柳木原普利广场／柳波广场／
    柳木原广场／羽田宅／苍羽女学院）必须 **0 槽**，且不得出现畸形拼接。这是
    `修正表_裁决20260930.tsv` **真的生效**的端到端证据——只数表行数会漏掉「表在、消费方没挂／
    被来源门控吃掉／被后续层改回」这三类静默失效（2026-09-30 实测三类都真实发生过）。

用法
  python -X utf8 audit_handoff_package.py          # 人读输出；有问题 exit 1
  python -X utf8 audit_handoff_package.py --json    # 机读 JSON（同时仍打印摘要）

依赖：工作区内需存在**主工作区**（大体积只读源与 gitignore 产物只在主工作区，见 C13）。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

LF = chr(10)
CR = chr(13)
TB = chr(9)

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
PROJ = os.path.dirname(RES)
HANDOFF = os.path.join(RES, "交接编程组")


def workspace_roots():
    """解析顺序：本工程检出树 → 主工作区工程目录 → 各级含 Galgame.md 的祖先 → 工作区根。"""
    roots = [PROJ, r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原",
             r"E:\ZCode Workspace\Galgame"]
    d = PROJ
    while True:
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            roots.append(d)
    seen, out = set(), []
    for r in roots:
        if r and r not in seen:
            seen.add(r); out.append(r)
    return out


ROOTS = workspace_roots()


def _bases():
    """解析基目录：文档自身目录、工程目录、资源组各常用子目录、各级根。"""
    out = [PROJ, os.path.join(PROJ, "资源组"), HANDOFF]
    for sub in ("剧本", "修正", "美术", "审计", "工具", "片尾", "交接编程组", "语料", "审查件"):
        out.append(os.path.join(PROJ, "资源组", sub))
    for sub in ("作品skill", "编程组", "素材超分"):
        out.append(os.path.join(PROJ, sub))
    for r in ROOTS:
        out.append(r)
        out.append(os.path.join(r, "资源组"))
    seen, res = set(), []
    for x in out:
        if x and x not in seen:
            seen.add(x); res.append(x)
    return res


BASES = _bases()
_BASENAMES = None


def _basename_index():
    global _BASENAMES
    if _BASENAMES is None:
        idx = set()
        for base in (PROJ, r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原",
                     r"E:\ZCode Workspace\Galgame\.zcode\skills"):
            if not os.path.isdir(base):
                continue
            for dp, dns, fns in os.walk(base):
                dns[:] = [d for d in dns if d != ".git"]
                for fn in fns:
                    idx.add(fn)
        _BASENAMES = idx
    return _BASENAMES


def _expand_braces(rel: str):
    """`a\\{b,c}\\d` → ['a\\b\\d', 'a\\c\\d']；无花括号则原样返回。"""
    m = re.search(r"\{([^{}]*)\}", rel)
    if not m:
        return [rel]
    out = []
    for opt in m.group(1).split(","):
        out.extend(_expand_braces(rel[:m.start()] + opt + rel[m.end():]))
    return out


def resolve(rel: str):
    """精确解析（相对工程目录 / 资源组各子目录 / 各级根）。命中返回路径，否则 None。"""
    for cand in _expand_braces(rel):
        c = cand.rstrip("\\")
        for base in BASES:
            p = os.path.join(base, c)
            if os.path.exists(p):
                return p
    return None


def resolve_any(rel: str):
    """返回 (路径, 命中方式)：'exact' / 'basename' / None。"""
    p = resolve(rel)
    if p:
        return p, "exact"
    for cand in _expand_braces(rel):
        bn = cand.rstrip("\\").replace("/", "\\").split("\\")[-1]
        if bn and bn in _basename_index():
            return None, "basename"
    return None, None


def count_jsonl(path):
    """JSONL 无表头：非空行数即条数。"""
    with io.open(path, encoding="utf-8", newline="") as f:
        return len([l for l in f.read().split("\n") if l.strip() != ""])


def data_path(*rel):
    """数据文件定位（检出树优先，其次主工作区）。"""
    for base in (PROJ, *ROOTS):
        c = os.path.join(base, *rel)
        if os.path.isfile(c):
            return c
    raise SystemExit("自检无法定位数据文件：" + os.path.join(*rel))


def data_dir(*rel):
    """数据目录定位（检出树优先，其次主工作区）。"""
    for base in (PROJ, *ROOTS):
        c = os.path.join(base, *rel)
        if os.path.isdir(c):
            return c
    raise SystemExit("自检无法定位数据目录：" + os.path.join(*rel))


def read_tsv_rows(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        ls = [l for l in f.read().split("\n") if l.strip() != ""]
    return len(ls) - 1        # 去表头


def count_tsv_records(path):
    """CSV **记录数**（去表头）——每条修正 = 1 条，RFC4180 引号包裹的**多行字段按 1 条计**。

    ISSUE-20261009-04：`修正表_奈落.tsv` 含 2 条多行字段（`s04_05b`/`s04_05i` 的 `seq=3` 整句内含换行）
    ⇒ 物理行计数（`read_tsv_rows`）会多算 4 行（609 vs 605）。「修正表数据行」一律用本函数计。
    """
    import csv
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.reader(f, delimiter="\t")) - 1


def count_lines(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return len([l for l in f.read().split("\n") if l.strip() != ""]) - 1


# ---- G：非采用变体（术语统一必须已生效）----------------------------------------
# 仅列**非采用变体**（不应再出现在任何成品语料里）。注意「隼」不能直接查——它是 `隼人` 的子串。
RESIDUAL_PATTERNS = [
    ("古罗利亚斯", re.compile("古罗利亚斯")),
    ("游隼", re.compile("游隼")),
    ("美空学园", re.compile("美空学园")),
    ("美空学府", re.compile("美空学府")),
    ("独立空学院", re.compile(r"(?<!美)空学院")),
    ("独立空学", re.compile(r"(?<!美)空学(?!院|府|园)")),
    ("独立空学园", re.compile(r"(?<!美)空学园")),
    ("美空学截断", re.compile(r"美空学(?!院|府|园|生)")),
    ("柳木原普利广场", re.compile("柳木原普利广场")),
    ("柳波广场", re.compile("柳波广场")),
    ("柳木原广场", re.compile("柳木原广场")),
    ("羽田宅", re.compile("羽田宅")),
    ("苍羽女学院", re.compile("苍羽女学院")),
    ("畸形拼接", re.compile(r"美空学院(?:院|园|生|府)|羽田家(?:邸|宅)"
                            r"|柳警广场(?:广|场)|苍穹女子学院(?:学院|院)")),
]
SCENE_SRC = ["ot", "otp", "ota", "otr", "otv", "np"]


def count_corpus_residuals():
    """六源 `scene_*.jsonl` 的 `lines[].cn` 里，非采用变体与畸形拼接的出现次数（应为 0）。"""
    d = data_dir("资源组", "剧本")
    hits, per = 0, {}
    for src in SCENE_SRC:
        p = os.path.join(d, "scene_%s.jsonl" % src)
        if not os.path.isfile(p):
            raise SystemExit("自检无法定位语料：" + p)
        n = 0
        for ln in io.open(p, encoding="utf-8"):
            if not ln.strip():
                continue
            for L in (json.loads(ln).get("lines") or []):
                cn = L.get("cn") or ""
                for name, pat in RESIDUAL_PATTERNS:
                    if cn and pat.search(cn):
                        n += 1
                        per[name] = per.get(name, 0) + 1
        hits += n
    return hits, per


# ── A 引用路径存在性 ──
# ISSUE-20261001-14：把「逐行演出表」的两份人读件也纳入扫描（它们大量引用 `资源组\...` 路径）
DOCS = ["编程组开工指南.md", "交接说明.md", "美术交付交接件.md", "自检报告.md",
        r"..\演出\演出表说明.md", r"..\演出\回复编程组_逐行演出数据任务书回执.md"]
TOKEN_RE = re.compile(r"`([^`\n]+)`")
TOP = ("资源组", "交接编程组", "剧本", "修正", "美术", "美术统一", "美术统一_超分", "美术统一_交付",
       "审计", "工具", "片尾", "作品skill", "编程组", "工程记录", "krkr素材库", "BGM统一", "审查件",
       "00_项目总纲.md", "Galgame.md", "AGENTS.md")

# 允许缺失（带理由）——整段匹配 token
ALLOW = {
    "临时\\": "临时目录，本就不常驻",
    "子代理工作区\\": "子代理中间产物，属他目录且非交付件",
    "成品\\": "成品由编程组产出（尚未生成），属预期缺席",
    "成品说明.md": "随成品产出（尚未生成）",
    "scene.jsonl": "六源 `scene_<源代号>.jsonl` 的泛称（非实体文件）",
}


def check_paths():
    bad, warns = [], []
    for doc in DOCS:
        p = os.path.join(HANDOFF, doc)
        if not os.path.isfile(p):
            bad.append((doc, 0, "<文件缺失>", "")); continue
        for i, ln in enumerate(io.open(p, encoding="utf-8"), 1):
            for tok in TOKEN_RE.findall(ln):
                t = tok.strip()
                t = re.sub(r":\d+(-\d+)?$", "", t)          # 剥掉 `文件:642` 的行号后缀
                if not t or t.startswith((".", "_")):
                    continue                                   # 扩展名碎片 / 续名简写
                if "/" in t and not t.startswith("http"):
                    continue                                   # `a.json/.md` 这类简写与 URL
                if "@" in t or "*" in t or "…" in t or "<" in t or ">" in t:
                    continue
                if not (t.startswith(TOP) or t.endswith((".md", ".tsv", ".json", ".py", ".jsonl", ".txt", ".png", ".ogg", ".mpg", ".mp4"))):
                    continue
                if "\\" not in t and not t.endswith((".md", ".tsv", ".json", ".py", ".jsonl", ".txt")):
                    continue
                if any(t.startswith(k) for k in ALLOW):
                    continue
                cand = t.rstrip("\\")
                pth, mode = resolve_any(cand)
                if mode is None:
                    bad.append((doc, i, t, ln.strip()[:110]))
                elif mode == "basename":
                    # 带目录分隔符 ⇒ 必须精确命中（basename 降级只留给裸文件名）
                    if "\\" in cand:
                        bad.append((doc, i, t + "（路径不存在，仅同名文件在别处）", ln.strip()[:110]))
                    else:
                        warns.append((doc, i, t))
    return bad, warns


# ── B 计数口径（独立复算） ──
def compute():
    m = {}
    sc = sorted(os.path.join(data_dir("资源组", "剧本"), f)
                for f in os.listdir(data_dir("资源组", "剧本"))
                if re.match(r"scene_\w+\.jsonl$", f))
    m["场景数（六源合计）"] = sum(count_jsonl(f) for f in sc)
    tot = 0
    for f in sc:
        for ln in io.open(f, encoding="utf-8"):
            tot += json.loads(ln).get("line_count", 0)
    m["剧本行数"] = tot
    led = json.load(io.open(data_path("资源组", "krkr素材库", "资源总账.json"), encoding="utf-8"))
    m["素材库条目"] = led["meta"]["count"]
    ops = [e for e in led["entries"] if e["source"] == "ot" and e["kind"] == "sys"
           and re.match(r"^op_\w+\.elg$", e["orig_name"], re.I)]
    m["素材账 op_*.elg（片头字幕条）"] = len(ops)
    m["美术交付层件数（交付层 10 列清单）"] = read_tsv_rows(
        data_path("资源组", "美术统一_交付", "交付清单.tsv"))
    m["美术分类总表行数（母版层 13 列清单）"] = read_tsv_rows(
        data_path("资源组", "美术统一", "交付清单.tsv"))
    for k, f in (("挂接_立绘", "挂接_立绘.tsv"), ("挂接_BGM", "挂接_BGM.tsv"),
                 ("BGM曲名表", "BGM曲名表.tsv"), ("BGM切换点", "BGM切换点.tsv"),
                 ("素材引用映射", "素材引用映射.tsv"), ("素材库到统一名", "素材库到统一名.tsv"),
                 ("产物清单", "产物清单.tsv")):
        m[k] = read_tsv_rows(os.path.join(HANDOFF, f))
    m["BGM统一清单"] = read_tsv_rows(data_path("资源组", "BGM统一清单.tsv"))
    m["章节简介"] = read_tsv_rows(data_path("资源组", "剧本", "章节简介.tsv"))
    _ids = set()
    for f in sc:
        for ln in io.open(f, encoding="utf-8"):
            _ids.add(json.loads(ln)["scene_id"])
    _sr = [l.rstrip("\n").rstrip("\r").split("\t") for l in
           io.open(data_path("资源组", "剧本", "章节简介.tsv"), encoding="utf-8") if l.strip()]
    _si = _sr[0].index("场景id")
    m["章节简介去重场景（∩六源 712）"] = len({r[_si] for r in _sr[1:]} & _ids)
    m["片尾清单"] = read_tsv_rows(data_path("资源组", "片尾", "片尾清单.tsv"))
    m["图片化日文_处置清单"] = read_tsv_rows(data_path("资源组", "审计", "图片化日文_处置清单.tsv"))
    m["图片化日文_保留清单"] = read_tsv_rows(data_path("资源组", "审计", "图片化日文_保留清单.tsv"))
    m["序章开场段_清单"] = read_tsv_rows(data_path("资源组", "审计", "序章开场段_清单.tsv"))
    m["序章开场段_演出序列"] = read_tsv_rows(data_path("资源组", "审计", "序章开场段_演出序列.tsv"))
    # ISSUE-20261009-04：「修正表数据行」改用 `count_tsv_records`（csv 记录数，每条修正 = 1 条；
    #   多行字段按 1 条计）——物理行计数会被 `修正表_奈落.tsv` 的 2 条多行字段多算 4 行（609 vs 605）。
    #   口径与 `资源组\修正\_README.md` §一 的合计一致；闸门判据不变（仍为下面 EXPECT 的硬断言）。
    # ISSUE-20261009-10：10 张 605 → 11 张 629（新增 `修正表_鹰志简繁.tsv` 24 条）。
    #   去表头物理数据行 633（= 629 + 4）；`wc -l`（含表头）644。
    m["修正表数据行（11 张合计）"] = sum(
        count_tsv_records(f) for f in
        [os.path.join(data_dir("资源组", "修正"), x) for x in os.listdir(data_dir("资源组", "修正"))
         if re.match(r"修正表_.*\.tsv$", x)])
    m["译名替换表"] = read_tsv_rows(data_path("资源组", "修正", "译名替换表.tsv"))
    m["停用件·禁入成品清单"] = read_tsv_rows(
        os.path.join(HANDOFF, "停用件_禁入成品.tsv"))
    m["修正表_裁决20260930 行数"] = read_tsv_rows(data_path("资源组", "修正", "修正表_裁决20260930.tsv"))
    m["语料残留_非采用变体"], m["语料残留_明细"] = count_corpus_residuals()
    return m


EXPECT = {
    "场景数（六源合计）": 712,
    "剧本行数": 96755,
    "素材库条目": 51027,
    "素材账 op_*.elg（片头字幕条）": 40,
    "美术交付层件数（交付层 10 列清单）": 4415,
    "美术分类总表行数（母版层 13 列清单）": 4415,
    "章节简介去重场景（∩六源 712）": 449,
    "挂接_立绘": 1976,
    "挂接_BGM": 712,
    "BGM曲名表": 70,
    "BGM切换点": 248,
    "BGM统一清单": 462,
    "素材引用映射": 1903,
    "素材库到统一名": 8052,
    # ISSUE-20260930-12：99 → 101（新增 `_term_unify.py` 与 `selftest_term_unify.py` 两条产物行）
    # ISSUE-20261001-14：101 → 112（「逐行演出表」族 11 条：六源表/说明/回执/台账/头像族判读 + 4 工具
    #                     + 契约实现 + 行尾回归测试）
    "产物清单": 112,
    "修正表_裁决20260930 行数": 123,
    "章节简介": 1253,
    "片尾清单": 148,
    "图片化日文_处置清单": 629,
    "图片化日文_保留清单": 132,
    "序章开场段_清单": 42,
    "序章开场段_演出序列": 96,
    # ISSUE-20261009-04：9 张 456 → 10 张 605（新增 `修正表_奈落.tsv` 149 条）。度量＝csv 记录数
    #   （`count_tsv_records`），多行字段按 1 条计——物理行计数会多算 4 行（609）。
    # ISSUE-20261009-10：10 张 605 → 11 张 629（新增 `修正表_鹰志简繁.tsv` 24 条）。
    "修正表数据行（11 张合计）": 629,
    "译名替换表": 128,
    "停用件·禁入成品清单": 406,
    "语料残留_非采用变体": 0,
}


# ── D 处置不变量 ──
def check_disposition():
    p = data_path("资源组", "审计", "图片化日文_处置清单.tsv")
    with io.open(p, encoding="utf-8", newline="") as f:
        rows = [l.rstrip("\n").rstrip("\r").split("\t") for l in f if l.strip()]
    head, data = rows[0], rows[1:]
    i = {c: head.index(c) for c in ("类别", "统一名", "处置")}
    cnt = {}
    for r in data:
        cnt[r[i["处置"]]] = cnt.get(r[i["处置"]], 0) + 1
    errs = []
    if len(data) != 629:
        errs.append("处置表 %d 行 != 629" % len(data))
    if cnt.get("保留·片头字幕条") != 40:
        errs.append("保留·片头字幕条 %s != 40" % cnt.get("保留·片头字幕条"))
    if cnt.get("保留·片尾") != 92:
        errs.append("保留·片尾 %s != 92" % cnt.get("保留·片尾"))
    # ★ 2026-10-05 用户改判（ISSUE-20261005-03）：章节题卡/日期条族 91 件由「弃用」转为「保留」
    #   （游戏内章节过场卡改用原素材）⇒ 弃用 497 → 406；不变量变为 629 = 132 + 91 + 406。
    if cnt.get("弃用") != 406:
        errs.append("弃用 %s != 406" % cnt.get("弃用"))
    if cnt.get("保留") != 91:
        errs.append("保留（题卡族）%s != 91" % cnt.get("保留"))
    tail = [r for r in data if r[i["类别"]] == "CG背景"]
    if len(tail) != 92 or any(r[i["处置"]] != "保留·片尾" for r in tail):
        errs.append("CG背景 92 件未全数进「保留·片尾」")
    drop_ops = [r[i["统一名"]] for r in data if r[i["处置"]] == "弃用" and r[i["统一名"]].startswith("op_")]
    if drop_ops:
        errs.append("弃用集混入片头件：%s" % drop_ops[:4])
    # 停用件·禁入成品清单必须等于「弃用」集合（用户 2026-09-30 裁决：记录并禁入成品）
    p2 = os.path.join(HANDOFF, "停用件_禁入成品.tsv")
    if os.path.isfile(p2):
        with io.open(p2, encoding="utf-8", newline="") as f:
            _ls = [l for l in f.read().split(LF) if l.strip() != ""]
        _rows2 = [l.rstrip(LF).rstrip(CR).split(TB) for l in _ls]
        iu2 = _rows2[0].index("统一名")
        a = sorted(r[iu2] for r in _rows2[1:])
        b = sorted(r[i["统一名"]] for r in data if r[i["处置"]] == "弃用")
        if a != b:
            errs.append("停用清单 %d 行与处置表弃用集不等（仅清单有 %s / 仅处置表有 %s）"
                        % (len(a), sorted(set(a) - set(b))[:3], sorted(set(b) - set(a))[:3]))
    else:
        errs.append("缺停用件清单：交接编程组\\停用件_禁入成品.tsv")
    return errs


# ── E 序章段 ──
def check_prologue():
    p = data_path("资源组", "审计", "序章开场段_清单.tsv")
    with io.open(p, encoding="utf-8", newline="") as f:
        rows = [l.rstrip("\n").rstrip("\r").split("\t") for l in f if l.strip()]
    head, data = rows[0], rows[1:]
    it, im = head.index("类型"), head.index("备注")
    errs = []
    strips = [r for r in data if r[it] == "字幕条"]
    movies = [r for r in data if r[it] == "影片"]
    if len(strips) != 40:
        errs.append("序章字幕条 %d != 40" % len(strips))
    if len(movies) != 2:
        errs.append("序章影片 %d != 2" % len(movies))
    for r in movies:
        if "占位·待替换" not in r[im]:
            errs.append("影片行缺「占位·待替换」标注：%s" % r[4])
    # 演出序里的语音条数
    q = data_path("资源组", "审计", "序章开场段_演出序列.tsv")
    with io.open(q, encoding="utf-8", newline="") as f:
        srows = [l.rstrip("\n").rstrip("\r").split("\t") for l in f if l.strip()]
    st = srows[0].index("类型")
    nv = sum(1 for r in srows[1:] if r[st] == "语音")
    if nv != 36:
        errs.append("演出序列语音 %d != 36" % nv)
    return errs


# ── F 过期口径残留 ──
STALE_MARK = ("作废", "历史", "取代", "已改", "订正", "不再", "旧", "以本节为准")


def check_stale():
    errs = []
    for doc in ("编程组开工指南.md", "交接说明.md"):
        p = os.path.join(HANDOFF, doc)
        if not os.path.isfile(p):
            continue
        for i, ln in enumerate(io.open(p, encoding="utf-8"), 1):
            if "消费基线" in ln and "美术统一_超分" in ln:
                if not any(k in ln for k in STALE_MARK):
                    errs.append("%s:%d 「消费基线＋美术统一_超分」同现且无作废标记" % (doc, i))
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    fails = []

    bad, warns = check_paths()
    if bad:
        fails.append("A 引用路径缺失 %d 处" % len(bad))
    meas = compute()
    mism = {k: (EXPECT[k], meas.get(k)) for k in EXPECT if meas.get(k) != EXPECT[k]}
    if mism:
        fails.append("B 计数口径不符 %d 项" % len(mism))

    # C 产物清单每行路径存在
    mp = os.path.join(HANDOFF, "产物清单.tsv")
    with io.open(mp, encoding="utf-8", newline="") as f:
        mrows = [l.rstrip("\n").rstrip("\r").split("\t") for l in f if l.strip()]
    mh, md = mrows[0], mrows[1:]
    pi = mh.index("路径")
    missing = [r[pi] for r in md if resolve_any(r[pi])[1] is None]
    if missing:
        fails.append("C 产物清单有 %d 行路径不存在" % len(missing))

    e = check_disposition()
    if e:
        fails.append("D 处置不变量：" + "；".join(e))
    e = check_prologue()
    if e:
        fails.append("E 序章段：" + "；".join(e))
    e = check_stale()
    if e:
        fails.append("F 过期口径残留：" + "；".join(e))

    if a.json:
        print(json.dumps({"ok": not fails, "fails": fails,
                          "missing_paths": [{"doc": d, "line": l, "token": t} for d, l, t, _ in bad],
                          "basename_only": [{"doc": d, "line": l, "token": t} for d, l, t in warns],
                          "mismatch": mism, "missing_manifest_paths": missing},
                         ensure_ascii=False, indent=2))
    print("=" * 70)
    print("交付包自检：" + ("全部通过" if not fails else "发现 %d 类问题" % len(fails)))
    print("=" * 70)
    print("A 引用路径：扫描 %d 份文档，缺失 %d 处（另有 %d 处仅按文件名命中，非失败）"
          % (len(DOCS), len(bad), len(warns)))
    for d, l, t, ctx in bad[:15]:
        print("    - %s:%s  %s" % (d, l, t))
    print("B 计数口径：复算 %d 项，不符 %d 项" % (len(EXPECT), len(mism)))
    for k, (exp, got) in mism.items():
        print("    - %s：期望 %s，实测 %s" % (k, exp, got))
    print("C 产物清单：%d 行，路径缺失 %d 行" % (len(md), len(missing)))
    for m in missing[:10]:
        print("    -", m)
    print("D 处置不变量：%s" % ("PASS" if not check_disposition() else "FAIL"))
    print("E 序章段：%s" % ("PASS" if not check_prologue() else "FAIL"))
    print("F 过期口径：%s" % ("PASS" if not check_stale() else "FAIL"))
    _res = meas.get("语料残留_非采用变体")
    print("G 语料残留：%s（六源合计 %s 槽；明细 %s）"
          % ("PASS" if _res == 0 else "FAIL", _res, meas.get("语料残留_明细") or "{}"))
    if fails:
        print("\n[失败]")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("\n结论：交付包内部一致，可用于交付编程组。")


if __name__ == "__main__":
    main()
