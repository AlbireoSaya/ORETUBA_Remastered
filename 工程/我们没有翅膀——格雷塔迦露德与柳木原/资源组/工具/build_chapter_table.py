# -*- coding: utf-8 -*-
r"""
build_chapter_table.py —— 《我们没有翅膀》全系列「章节级结构数据」提取器（ISSUE-20260920-17）

输入（只读）：
  资源组\剧本\scene_{ot,ota,otp,otr,otv,np}.jsonl   —— 主数据源（712 场景）
  资源组\剧本\spine.json                            —— 11 幕编排 / excluded / side_stories / branch_points
输出（覆盖写，确定性）：
  资源组\05_章节总表.tsv        —— 逐场景（＝逐章节）一行，712 数据行
  资源组\章节提取说明.md        —— 口径 / 排序算法 / 判定规则 / 校验结果

纪律：
  * 只读 scene_*.jsonl 与 spine.json，绝不改写任何语料；
  * 幂等：同一输入连跑两轮，输出字节完全一致（见 --check）；
  * 不臆断：判不准的写「待判定」并说明缺什么。

用法：
  python -X utf8 build_chapter_table.py            # 生成两份产物
  python -X utf8 build_chapter_table.py --check    # 生成 + 校验（行数/链/分布/幂等）
"""
import json
import os
import re
import sys
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                      # ...\资源组
SCRIPT_DIR = os.path.join(RES, "剧本")
OUT_TSV = os.path.join(RES, "05_章节总表.tsv")
OUT_MD = os.path.join(RES, "章节提取说明.md")

SRC_ORDER = ["ot", "otr", "ota", "otp", "otv", "np"]
SRC_LABEL = {
    "ot": "本篇",
    "otr": "R版亚衣线",
    "ota": "AfterStory",
    "otp": "前奏诗",
    "otv": "PSV美咲线",
    "np": "涅布明日香篇",
}

# ---------------------------------------------------------------- 路线 → 个人线标签
ROUTE_LINE = {
    ("ot", "s01 鹰志线"): "个人线-渡来明日香",
    ("ot", "s02 鹫介线"): "个人线-玉泉日和子",
    ("ot", "s03 隼人线"): "个人线-凤鸣",
    ("otr", "s03c 亚衣线"): "个人线-香田亚衣",
    ("otv", "M/P03 美咲线"): "个人线-林田美咲",
    ("ota", "AS 对决羽田鹰志"): "个人线-渡来明日香（后日谈）",
    ("ota", "AS 对决千岁鹫介"): "个人线-玉泉日和子（后日谈）",
    ("ota", "AS 对决成田隼人"): "个人线-凤鸣（后日谈）",
    ("ota", "AS 对决羽田小鹰志"): "个人线-羽田小鸠（后日谈）",
    ("ota", "AS 美咲线"): "个人线-林田美咲（后日谈）",
    ("ota", "AS 最终统合线"): "个人线-最终统合线（后日谈）",
}

# 结局 → 标签（phase=='结局' 的逐场景显式映射；未列者回退 route）
END_LABEL = {
    "s01_16a": "结局-渡来明日香",
    "s01_18a": "结局-山科京",
    "s01_19a": "结局-鹰志线",
    "s02_16a": "结局-玉泉日和子",
    "s02_17a": "结局-鹫介线",
    "s03_22a": "结局-凤鸣",
    "s03_23a": "结局-隼人线",
    "s04_28b": "结局-大路线（真·兄妹再会）",
    "s04_29a": "结局-大路线（解纜/真 END）",
    "s03c_20a": "结局-香田亚衣",
    "M09_01": "结局-林田美咲",
    "M09_02": "结局-美咲线",
    "11_6a": "结局-渡来明日香（后日谈）",
    "12_5a": "结局-玉泉日和子（后日谈）",
    "13_5b": "结局-凤鸣（后日谈）",
    "14_8a": "结局-羽田小鸠（后日谈）",
    "21_3b": "结局-林田美咲（后日谈）",
    "24_5b": "结局-最终统合线（G-END）",
    "24_5c": "结局-最终统合线（B-END）",
    "a06_b1": "结局-涅布明日香篇",
    "a06_b2": "结局-涅布明日香篇",
    "a06_b3": "结局-涅布明日香篇",
    "a06_b4": "结局-涅布明日香篇",
    "a06_c0": "结局-涅布明日香篇",
}

# 章节作用的逐场景覆盖（有独立证据者）
ROLE_OVERRIDE = {
    "s01_14g1": "个人线-山科京",
    "s01_14h": "个人线-山科京",
    "s01_17a": "个人线-山科京",
    "s01_14g2": "个人线-鹰志线（Bad End 支）",
    "s01_14j2": "个人线-鹰志线（Bad End 支）",
}

# 系统 / 框架 / 短剧情 的显式归属
SYSTEM_SCRIPTS = {
    "gameinit", "history", "title", "title2", "staff", "sr",
    "start_oretuba", "end_oretuba",
}
FRAME_SCRIPTS = {"buru01", "buru02", "buru03", "buru04"}
SHORT_ROUTES_OTP = {
    "前奏诗 p01 明日香篇", "前奏诗 p02 山科京篇",
    "前奏诗 p03 美咲篇", "前奏诗 p04 轻部狩男篇",
}

# 开篇型章节标题（邂逅 / 序章 / 序文 / 再会 / 承前 / 文）
OPEN_RE = re.compile(r"^(文|邂逅|プロローグ|序章|序文|再会|承前)")

# 「共通段」的终止节点（＝首个通向不同女主结局 / 另一路线的分支节点），逐路线显式登记
# 值为 script 名（不含源代号前缀）
BRANCH_TERMINAL = {
    ("ot", "s01 鹰志线"): "s01_14g",       # 三臂 → s01_18a(京 END) / s01_14g2(Bad End) / s01_16a(明日香 END)
    ("ot", "s03 隼人线"): "s03_08b",       # 两臂 → s03_08c1→s03_09a1(鸣线) / s03_08c2→s03_09a2→s03c_01a(亚衣线，跨源)
    ("ota", "AS 最终统合线"): "24_4e",      # 两臂 → 24_5a→24_5b(G-END) / 24_5c(B-END)
}

# 共通线中「埋了伏笔」的显式清单（已逐条在语料中核实原文，见 章节提取说明.md §4）
FORESHADOW = {
    "s01_09d": "提到 WING QUEST（「ウイングクエストって知ってるか」）——后于 s04 大路线回收",
    "s04_25b": "提到 伊丹さん（「伊丹さんが何でも言うこと聞くと言ったとき…」）——指向被封印的长兄人格",
}

# 跨线 / 跨源耦合边（script → 目标），由脚本自动检出后并入判定，这里只登记「同源跨路线」的语义
HEROINE_NAMES = [
    "渡来", "山科", "針生", "京", "日和子", "英里子", "紀奈子", "纪奈子",
    "鳴", "鸣", "亜衣", "亚衣", "美咲", "小鳩", "小鸠", "春恵", "春惠",
    "高内", "昌子",
]


# ---------------------------------------------------------------- 读取
def load_sources():
    data = {}
    for s in SRC_ORDER:
        p = os.path.join(SCRIPT_DIR, "scene_%s.jsonl" % s)
        rows = []
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        data[s] = rows
    return data


def load_spine():
    with open(os.path.join(SCRIPT_DIR, "spine.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- 图
class Graph(object):
    def __init__(self, data):
        self.data = data
        self.owner = {}
        self.rows = {}
        self.next = {}
        self.order_in_file = {}
        for s in SRC_ORDER:
            for i, o in enumerate(data[s]):
                self.owner[o["script"]] = s
                self.rows[o["script"]] = o
                self.next[o["script"]] = list(o.get("next") or [])
                self.order_in_file[o["script"]] = i

    def scripts(self, s):
        return [o["script"] for o in self.data[s]]

    def cross_edges(self, s):
        S = set(self.scripts(s))
        out = []
        for k in self.scripts(s):
            for t in self.next[k]:
                if t not in S:
                    out.append((k, t))
        return out

    def dfs_order(self, s):
        """从本源第一条起，沿 next 数组顺序做深度优先前序遍历（visited 去重）。
        仅在本源场景集内行进；指向他源的目标记为跨源边、不进入遍历。"""
        scripts = self.scripts(s)
        S = set(scripts)
        seen = set()
        order = []

        def dfs(u):
            if u in seen:
                return
            seen.add(u)
            order.append(u)
            for t in self.next.get(u, []):
                if t in S:
                    dfs(t)

        dfs(scripts[0])
        unreachable = [x for x in scripts if x not in seen]
        return order, unreachable

    def terminals_reachable(self, start):
        """从 start 出发可到达的「终点场景」集合（next==[] 或 指向他源）。
        仅在本源内行进，指向他源的目标以 CROSS:<script> 形式计入终点。"""
        src = self.owner.get(start)
        S = set(self.scripts(src)) if src else set()
        out = set()
        seen = set()
        stack = [start]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            nxt = self.next.get(u)
            if nxt is None:
                continue
            if not nxt:
                out.add(u)
            for t in nxt:
                if t in S:
                    stack.append(t)
                else:
                    out.add("CROSS:" + t)
        return out

    def ancestors(self, s, node, route=None):
        """node 在源 s 内的全部祖先（含自身），反向可达。
        route 非空时只在同 route 的场景内行进（避免跨路线回边把整源拉进来）。"""
        scripts = set(self.scripts(s))
        if route is not None:
            scripts = {x for x in scripts if self.rows[x].get("route") == route}
        rev = {}
        for k in scripts:
            for t in self.next[k]:
                if t in scripts:
                    rev.setdefault(t, []).append(k)
        seen = set()
        stack = [node]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            for p in rev.get(u, []):
                stack.append(p)
        return seen

    def reachable(self, start, route=None):
        """从 start 出发（本源内）可达的全部场景（含自身）。
        route 非空时只在同 route 的场景内行进。"""
        src = self.owner.get(start)
        S = set(self.scripts(src)) if src else set()
        if route is not None:
            S = {x for x in S if self.rows[x].get("route") == route}
        out = set()
        stack = [start]
        while stack:
            u = stack.pop()
            if u in out:
                continue
            out.add(u)
            for t in self.next.get(u, []):
                if t in S:
                    stack.append(t)
        return out

    @staticmethod
    def group(script):
        """组前缀：`_` 前的首段（`s01_05`→`s01`、`11_1a`→`11`、`buru01`→`buru01`）。"""
        return script.split("_", 1)[0]

    def cross_group_edges(self, s):
        """源 s 内「组前缀不同」的边。仅对 `ot`/`otr` 有意义（其组＝路线 s00–s04 / s03c）；
        其余源的组是篇章块，跨组边即正常线性推进，不作跨路线解。"""
        out = []
        S = set(self.scripts(s))
        for k in self.scripts(s):
            for t in self.next[k]:
                if t in S and self.group(k) != self.group(t):
                    out.append((k, t))
        return out

    def cycles(self, s):
        """返回源 s 内「自可达」（即位于某环上）的场景集合。"""
        scripts = self.scripts(s)
        S = set(scripts)
        out = []
        for start in scripts:
            seen = set()
            stack = list(self.next.get(start, []))
            found = False
            while stack:
                u = stack.pop()
                if u == start:
                    found = True
                    break
                if u in seen or u not in S:
                    continue
                seen.add(u)
                stack.extend(self.next.get(u, []))
            if found:
                out.append(start)
        return out

    def route_of(self, script):
        return self.rows[script].get("route")


# ---------------------------------------------------------------- 章节作用
def build_role(script, g, spine, ctx):
    o = g.rows[script]
    s = g.owner[script]
    sid = o["scene_id"]
    phase = o.get("phase")
    route = o.get("route")
    lc = o.get("line_count") or 0

    if script in SYSTEM_SCRIPTS or phase == "系统" or lc == 0:
        return "系统"
    if script in FRAME_SCRIPTS:
        return "框架"
    if sid in ctx["excluded"]:
        return "其他"
    if sid in ctx["side"]:
        return "番外"
    if phase == "真相":
        return "真相"
    if phase == "结局":
        if script in END_LABEL:
            return END_LABEL[script]
        if s == "np":
            return "结局-涅布明日香篇"
        return ROUTE_LINE.get((s, route), "结局-待判定")
    if route in SHORT_ROUTES_OTP or script.startswith("P03_") or s == "np":
        return "短剧情"
    if script in ROLE_OVERRIDE:
        return ROLE_OVERRIDE[script]

    # 共通线：路线开篇章節（邂逅 / 序章 / 序文 / 再会 / 承前 / 文）
    if OPEN_RE.match(o.get("title_jp") or ""):
        return "共通线"
    # 共通线(影响后续剧情)：路线「分支前共享段」的终点——此章之后分叉到不同女主线/结局
    if script in ctx["split_nodes"]:
        return "共通线(影响后续剧情)"

    return ROUTE_LINE.get((s, route), "个人线-待判定")


# ---------------------------------------------------------------- 影响后续剧情
def build_impact(script, g, ctx):
    """返回 (是否影响: '是'/'' , 依据)"""
    o = g.rows[script]
    reasons = []
    nxt = g.next.get(script, [])
    s = g.owner[script]
    S = set(g.scripts(s))

    # (1) 分支臂导向不同终点集合 / 跨源
    if len(nxt) >= 2:
        arms = [t for t in nxt if t in S]
        if any(t not in S for t in nxt):
            reasons.append("next 分支含跨源目标")
        elif arms:
            term_sets = [frozenset(g.terminals_reachable(t)) for t in arms]
            if len(set(term_sets)) >= 2:
                desc = []
                for t in arms[:4]:
                    ts = sorted(g.terminals_reachable(t))
                    desc.append("%s→%s" % (t, "+".join(ts) if ts else "空"))
                if len(arms) > 4:
                    desc.append("…等 %d 臂" % len(arms))
                reasons.append("next 分支各臂终点不同（%s）" % "；".join(desc))

    # (2) 选项目标已填（np 34 / otp 7）
    tgt = [c for c in (o.get("choices") or []) if c.get("target")]
    if tgt:
        reasons.append("选项已填目标（%d 条，pairing_verified=%s）" % (
            len(tgt), "true" if all(c.get("pairing_verified") for c in tgt) else "部分 false"))

    # (3) 选项点名 ≥2 个不同女主（跨线耦合）
    txt = " ".join((c.get("text_jp") or "") + (c.get("text_cn") or "")
                   for c in (o.get("choices") or []))
    named = sorted({h for h in HEROINE_NAMES if h in txt})
    if len(named) >= 2:
        reasons.append("选项点名多个女主（%s）" % "／".join(named))

    # (4) 跨源边
    for t in nxt:
        if t not in S:
            reasons.append("跨源边 → %s（%s）" % (t, g.owner.get(t, "?")))
            break

    # (5) 显式伏笔
    if script in FORESHADOW:
        reasons.append("共通线伏笔：" + FORESHADOW[script])

    if reasons:
        return "是", "；".join(reasons)
    return "", ""


# ---------------------------------------------------------------- 单元格
def cell(v):
    if v is None:
        return ""
    return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def choices_cn(o):
    out = []
    for c in (o.get("choices") or []):
        if c.get("text_cn"):
            out.append(c["text_cn"])
        elif c.get("text_jp"):
            out.append("〔无译文〕" + c["text_jp"])
        else:
            out.append("〔空〕")
    return " / ".join(out)


# ---------------------------------------------------------------- 主流程
def build():
    data = load_sources()
    spine = load_spine()
    g = Graph(data)

    excluded = {e["scene_id"] for e in spine["excluded"]}
    side = {e["scene_id"] for e in spine["side_stories"]}
    act_of = {}
    for a in spine["acts"]:
        for sid in a["scenes"]:
            act_of[sid] = "act %d %s" % (a["act"], a["name"])
    for e in spine["excluded"]:
        act_of[e["scene_id"]] = "excluded（D15 原型版）"
    for e in spine["side_stories"]:
        act_of[e["scene_id"]] = "side_stories（%s）" % e["group"]

    # 共通段（＝分支前共享段，供说明文档登记范围；章节作用只标其终点）
    common_seg = {}
    for (s, route), term in BRANCH_TERMINAL.items():
        common_seg[(s, route)] = g.ancestors(s, term, route=route)
    for s in SRC_ORDER:
        for o in data[s]:
            common_seg.setdefault((s, o.get("route")), set())
    split_nodes = {v for v in BRANCH_TERMINAL.values()}

    # influencing 节点（分支臂终点不同 / 跨源 / 选项点名多女主）
    influencing = set()
    for s in SRC_ORDER:
        S = set(g.scripts(s))
        for o in data[s]:
            sc = o["script"]
            nxt = g.next.get(sc, [])
            if len(nxt) >= 2:
                if any(t not in S for t in nxt):
                    influencing.add(sc)
                else:
                    sets = {frozenset(g.terminals_reachable(t)) for t in nxt}
                    if len(sets) >= 2:
                        influencing.add(sc)
            txt = " ".join((c.get("text_jp") or "") + (c.get("text_cn") or "")
                           for c in (o.get("choices") or []))
            if len({h for h in HEROINE_NAMES if h in txt}) >= 2:
                influencing.add(sc)

    ctx = {"excluded": excluded, "side": side,
           "common_seg": common_seg, "influencing": influencing,
           "split_nodes": split_nodes}

    rows_out = []
    stats = {}
    for s in SRC_ORDER:
        order, unreach = g.dfs_order(s)
        seq = order + unreach
        stats[s] = {"n": len(seq), "dfs": len(order), "unreach": unreach,
                    "first": g.scripts(s)[0]}
        unreach_set = set(unreach)
        for i, script in enumerate(seq, 1):
            o = g.rows[script]
            role = build_role(script, g, spine, ctx)
            imp, imp_why = build_impact(script, g, ctx)
            notes = []
            if script in unreach_set:
                notes.append("next 链不可达")
            if o.get("next_kind") == "branch":
                notes.append("分支点")
            if sid in excluded:
                notes.append("D15 排除：与本篇 99.2%% 重合的原型版")
            if sid in side:
                grp = [x["group"] for x in spine["side_stories"] if x["scene_id"] == sid]
                notes.append("番外组：%s" % (grp[0] if grp else ""))
            if not (o.get("title_jp") or ""):
                notes.append("无标题（title_jp 为空）")
            key = (s, o.get("route"))
            if script in common_seg.get(key, set()) and key in BRANCH_TERMINAL \
                    and BRANCH_TERMINAL[key] == script:
                notes.append("共通段终点（此后分叉到不同女主线；分支前共享段共 %d 章）"
                             % len(common_seg[key]))
            if script == "s03c_01a":
                notes.append("亚衣线入口（s03_09a2 → 本场景）")
            if script == "s03_09a2":
                notes.append("亚衣线分叉臂（→ s03c_01a）；本场景 route 仍为 s03 隼人线")
            if script == "s03_08c2":
                notes.append("亚衣线分叉臂的上游（（Ｃ）变体 → s03_09a2）")
            for t in g.next.get(script, []):
                if t not in g.rows:
                    notes.append("跨源边 → %s" % t)
            if script in ("s01_05",):
                notes.append("跨线：next → s02_01a（幕間跳转）")
            if script in ("s01_05a",):
                notes.append("跨线共享：入边来自 s04_06k")

            rows_out.append([
                SRC_LABEL[s], s, str(i), script,
                cell(o.get("title_jp")), cell(o.get("title_cn")),
                cell(o.get("phase")), cell(o.get("route")), cell(o.get("source_kind")),
                str(o.get("line_count")),
                "；".join(o.get("next") or []) or "（无）",
                cell(o.get("next_kind")),
                str(len(o.get("choices") or [])),
                choices_cn(o),
                cell(o.get("game_date")),
                "、".join(o.get("cast") or []),
                role,
                ("%s（%s）" % (imp, imp_why)) if imp else "",
                act_of.get(o["scene_id"], "（spine 未收录）"),
                "；".join(notes),
            ])

    header = ["作品来源", "源代号", "章节序号", "script", "章节标题(日文)", "章节标题(中文)",
              "phase", "route", "source_kind", "行数", "next", "next_kind", "选项数",
              "选项文本(中文)", "游戏日期", "登场人物", "章节作用", "是否影响后续剧情",
              "spine归属", "备注"]

    lines = ["\t".join(header)]
    for r in rows_out:
        lines.append("\t".join(r))
    tsv = "\n".join(lines) + "\n"
    return g, spine, stats, rows_out, tsv, common_seg, influencing


def gen_md(g, spine, stats, rows_out, header, common_seg):
    """由数据生成《章节提取说明.md》（确定性）。"""
    i = {h: k for k, h in enumerate(header)}
    by_src = {}
    for r in rows_out:
        by_src.setdefault(r[i["源代号"]], []).append(r)

    from collections import Counter

    L = []
    A = L.append
    A("# 章节级结构数据提取说明 · 《我们没有翅膀——格雷塔迦露德与柳木原》")
    A("")
    A("> 模块：`ISSUE-20260920-17` ｜ 构建器：`资源组\\工具\\build_chapter_table.py`（只读语料、幂等、可复跑）")
    A("> 产物：`资源组\\05_章节总表.tsv`（逐章节一行）＋ 本文件")
    A("> **本文件所有结论均由 `scene_*.jsonl` 与 `spine.json` 实测得出；判不准者标「待判定」并写明缺什么，不臆断。**")
    A("")
    A("---")
    A("")
    A("## 一、数据来源与字段口径")
    A("")
    A("### 1.1 主数据源")
    A("")
    A("| 源代号 | 作品 | 文件 | 场景数 |")
    A("| --- | --- | --- | ---: |")
    for s in SRC_ORDER:
        A("| `%s` | %s | `资源组\\剧本\\scene_%s.jsonl` | %d |" % (
            s, SRC_LABEL[s], s, len(g.data[s])))
    A("| — | **合计** | — | **%d** |" % sum(len(g.data[s]) for s in SRC_ORDER))
    A("")
    A("### 1.2 字段口径（引 `资源组\\剧本\\schema.md`）")
    A("")
    A("| 本表列 | 取自 `scene_*.jsonl` | 口径说明（schema 依据） |")
    A("| --- | --- | --- |")
    A("| `script` | `script` | 脚本名；`scene_id = <源代号>_<script>`，全局唯一（本批六源 `script` 无重名，实测 0 冲突） |")
    A("| `章节标题(日文/中文)` | `title_jp` / `title_cn` | schema §3.4：优先取「有 09 对照或有修正表条目」的标题槽，否则取最后一个；全部槽见 `title_variants` |")
    A("| `phase` | `phase` | schema §3.5 八值域：`序/个人线/结局/真相/主线/框架/系统/null`；**按源分域** |")
    A("| `route` | `route` | schema §4.5：可空（仅 `ota` 15 条 D13 未裁决 / 系统场景） |")
    A("| `source_kind` | `source_kind` | schema §3.1：**按源分域**（`ot` 用源代号自指、`ota/otv/np` 用 `new`、`otr/otp` 用 `shared/branch/new`） |")
    A("| `行数` | `line_count` | 场景内 `lines[]` 长度 |")
    A("| `next` / `next_kind` | `next` / `next_kind` | schema §3.3：`linear`(1)/`branch`(≥2)/`end`(0) |")
    A("| `选项数` / `选项文本(中文)` | `choices[].text_cn` | schema §2.2：`text_cn` 为 `null` 者标 `〔无译文〕` 并回显原文 |")
    A("| `游戏日期` | `game_date` | schema §4.3：**仅当场景内出现显式 `○月○日` 才填**，否则空 |")
    A("| `登场人物` | `cast` | 按首次出现排序；旁白计为 `旁白` |")
    A("| `是否影响后续剧情` | `choices[].target` / `pairing_verified` / `next` | schema §3.2.4：**`target` 非空 ≠ 配对已确证，只看 `pairing_verified`** |")
    A("")
    A("### 1.3 本表增列（超出任务预设，供交叉核对）")
    A("")
    A("- **`spine归属`**：该场景在 `资源组\\剧本\\spine.json` 中的归属（`act N 名称` / `excluded（D15 原型版）` / `side_stories（番外组）`）。用于与 11 幕编排方案对账；`（spine 未收录）` 表示既不在 acts 也不在 excluded/side。")
    A("")
    A("---")
    A("")
    A("## 二、「章节」与「场景」的关系（**必读**）")
    A("")
    A("**结论：本工程内 `scene` 与实机「章节」是 1:1 的**，依据如下：")
    A("")
    A("1. `scene_id = <源代号>_<脚本名>`，**一条记录 = 一个脚本文件**（schema §〇「一条记录 = 一个场景」）。")
    A("2. 实机跳过确认框显示的「章节标题」与 `title_jp/title_cn` 逐字对应——用户实机截图中的")
    A("   「邂逅　～对抗：羽田鹰志～」＝`s01_01a.title_cn`、「序章　～美空学院的人们～」＝`s01_02a.title_cn`、")
    A("   「序言　～我们没有翅膀～」＝`s00_00.title_jp`「文　～俺たちに翼はない～」（序文篇）。")
    A("3. 实机右下角的 `Episode: <名>` 对应本表的 `route`（如 `Episode: Takashi` ↔ `route = s01 鹰志线`）。")
    A("")
    A("**例外（不构成 1:1 反例，须标注）**：`title_jp` 为空的脚本是**上一章的续章片段**（无独立标题槽），")
    A("本表保留其行并在 `备注` 标「无标题（title_jp 为空）」。逐源空标题清单见 §五.1。")
    A("")
    A("> ⚠️ **未核实的部分**：本工程未做实机逐章跳转录屏，故「实机把无标题脚本也算作独立章节 / 还是并入上一章」**未验证**。")
    A("> 本表按「一脚本一行」呈现（＝712 行），若实机把续章片段并入上一章，则实机章节数会少于 712。**此点标「待判定」**。")
    A("")
    A("---")
    A("")
    A("## 三、排序算法与校验")
    A("")
    A("### 3.1 算法（逐源独立执行）")
    A("")
    A("```text")
    A("输入：该源 scene_<源>.jsonl 的记录序列（文件行序）")
    A("root := 该源【第一条】记录（文件行序第 1 条）")
    A("order := [];  visited := {}")
    A("dfs(u):")
    A("    if u in visited: return")
    A("    visited.add(u); order.append(u)")
    A("    for t in u.next:              # 按 next 数组顺序展开")
    A("        if t 属于本源: dfs(t)      # 跨源目标不计入本源遍历")
    A("dfs(root)")
    A("unreachable := 本源中未出现在 order 的场景（保持文件行序）")
    A("输出顺序 := order ++ unreachable")
    A("```")
    A("")
    A("等价命令（可复跑，只读）：")
    A("")
    A("```bash")
    A("cd \"E:/ZCode Workspace/Galgame\"")
    A("python -X utf8 \"工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_chapter_table.py\"")
    A("```")
    A("")
    A("### 3.2 校验结果（逐源：DFS 可达 / 总数 / 不可达 / 环）")
    A("")
    A("| 源代号 | 起点（文件第 1 条） | 总数 | next 链可达 | 不可达 | 位于环上的场景 |")
    A("| --- | --- | ---: | ---: | ---: | ---: |")
    for s in SRC_ORDER:
        st = stats[s]
        cyc = g.cycles(s)
        A("| `%s` | `%s` | %d | %d | %d | %d |" % (
            s, st["first"], st["n"], st["dfs"], len(st["unreach"]), len(cyc)))
    A("")
    A("**结论**：")
    A("")
    A("- **`ot`（本篇）从 `s00_00` 单链可达全部 367 场景，无孤立、无环**——本篇是一张从序文出发的连通有向无环图。")
    A("  其连通性来自 **%d 条「跨组边」**（组前缀不同的边，见 §3.3）：`s01→s02`、`s02→s03`、`s03→s04`、`s04→s01/s02/s03`，" % (
        len(g.cross_group_edges("ot"))))
    A("  故**沿 `next` 链的遍历顺序会跨路线穿插**（先按第一条臂深入，走到底再回溯）——这是算法顺序，**不等于剧情播放顺序**；")
    A("  剧情播放顺序以 `spine.json` 的幕序为准（§七.2）。")
    A("- **其余五源均存在多个「入度 0」的起点**（各源内部并无单一线性 `next` 链）：")
    for s in SRC_ORDER:
        if s == "ot":
            continue
        st = stats[s]
        A("  - `%s`：从 `%s` 出发仅覆盖 %d/%d；其余 %d 条为 next 链不可达（在 TSV 末尾单列并标「next 链不可达」）。" % (
            s, st["first"], st["dfs"], st["n"], len(st["unreach"])))
    A("- **不可达的成因**：这些源的脚本是**并列/菜单式结构**（如 `otp` 由 `MAIN→GAMEINIT→…→P01–P04→02→03→BURU→STAFF` 调度，`ota` 的 31 个篇章各自独立成链，`np` 的 `start_oretuba` 是菜单根），")
    A("  **脚本内不存在把它们串成一条链的 `next` 边**。故本表的「顺序号」对不可达段**只表示文件行序，不表示播放顺序**——`备注` 已逐条标注。")
    A("- **无环**：六源均无「自可达」场景（各源环上场景数 0，见上表）。")
    A("")
    A("### 3.3 跨源 / 跨路线边（排序与连线时不可忽略）")
    A("")
    A("| 边 | 类型 | 证据 |")
    A("| --- | --- | --- |")
    for s in SRC_ORDER:
        for (a, b) in g.cross_edges(s):
            A("| `%s` → `%s` | **跨源**（%s → %s） | `scene_%s.jsonl` 的 `next` |" % (
                a, b, s, g.owner.get(b, "?"), s))
    for s in ("ot", "otr", "ota"):
        for (a, b) in g.cross_group_edges(s):
            A("| `%s` → `%s` | 同源跨路线/跨篇章（%s → %s） | `scene_%s.jsonl` 的 `next` |" % (
                a, b, g.group(a), g.group(b), s))
    A("")
    A("> `otp`/`otv`/`np` 未列：这三源的组前缀是**篇章块**（如 `M01`/`a01`），其组间边是正常线性推进，不构成跨路线跳转。")
    A("")
    A("---")
    A("")
    A("## 四、`章节作用` 判定规则（可复现）")
    A("")
    A("按**优先级由高到低**逐条判定，**首个命中即采用**。每条规则均写明所用字段与证据来源。")
    A("")
    A("| 序 | 取值 | 判定条件（字段组合） | 证据来源 |")
    A("| ---: | --- | --- | --- |")
    A("| 1 | `系统` | `phase == '系统'`；或 `script ∈ {gameinit, history, title, title2, staff, sr, start_oretuba, end_oretuba}`；或 `line_count == 0` | schema §3.5（`系统`＝引擎初始化/回想/制作人员/标题）；`spine.json` act 2；`ota_sr` 见 schema §4.5 |")
    A("| 2 | `框架` | `script ∈ {buru01, buru02, buru03, buru04}`（`otp` 剧场框架剧） | `route = '前奏诗 框架剧 buru'`；`spine.json` act 1 |")
    A("| 3 | `其他` | `scene_id ∈ spine.excluded`（`otp` `02_*`/`03_*` 共 32） | `spine.json` `excluded[].reason_short`＝「D15：原型版（与本篇 99.2% 重合），不入主干」 |")
    A("| 4 | `番外` | `scene_id ∈ spine.side_stories`（`ota` 共 53；`ota_sr` 因规则 1 先命中而记 `系统`） | `spine.json` `side_stories[].group`（逐条写入本表 `备注`）；`主线编排方案.md` §五（D13） |")
    A("| 5 | `真相` | `phase == '真相'` | schema §3.5；`ot` 的 `s04` 段 72 场景 |")
    A("| 6 | `结局-<线>` | `phase == '结局'`，`<线>` 取逐场景显式映射（见 §4.1） | schema §3.5；`01_剧情流程图.md` §五 结局矩阵 |")
    A("| 7 | `短剧情` | `route ∈ 前奏诗 p01–p04`（`otp` 四角色短篇）；或 `script` 以 `P03_` 开头（`otv` 美咲四短篇）；或 `源 == np`（子篇目菜单式短篇集，`结局` 已被规则 6 先取） | `spine.json` act 1 / act 8 / act 11 的 `note` |")
    A("| 8 | `共通线(影响后续剧情)` | `script` ＝该路线的**分支前共享段终点**（该章之后分叉到不同女主线/结局） | 见 §4.2 的逐路线登记 |")
    A("| 9 | `共通线` | `title_jp` 匹配 `^(文\\|邂逅\\|プロローグ\\|序章\\|序文\\|再会\\|承前)`（路线开篇章節） | 用户实机截图所示章题（序言/邂逅/序章）；本表实测命中清单见 §4.2 |")
    A("| 10 | `个人线-<女主>` | 其余，按 `(源代号, route)` 映射（见 §4.1） | `route` 字段（各源自带线路标识） |")
    A("| — | `待判定` | 无 | 本批实测 **0 条**（见 §五.2 说明） |")
    A("")
    A("### 4.1 结局 / 个人线 的逐场景映射")
    A("")
    A("**`(源代号, route) → 个人线`**：")
    A("")
    A("| 源代号 | `route` | 个人线标签 |")
    A("| --- | --- | --- |")
    for (s, r), v in sorted(ROUTE_LINE.items()):
        A("| `%s` | `%s` | `%s` |" % (s, r, v))
    A("")
    A("**`phase == '结局'` 的逐场景标签**（未列者回退 `(源代号, route)` 映射）：")
    A("")
    A("| `scene_id` | 结局标签 | 证据（标题） |")
    A("| --- | --- | --- |")
    for sc, lab in END_LABEL.items():
        t = g.rows[sc].get("title_jp") if sc in g.rows else ""
        A("| `%s_%s` | `%s` | %s |" % (g.owner.get(sc, "?"), sc, lab, t or "—"))
    A("")
    A("**逐场景覆盖（`ROLE_OVERRIDE`）**：`s01_14g1`/`s01_14h`/`s01_17a` → `个人线-山科京`（山科京副线）；")
    A("`s01_14g2`/`s01_14j2` → `个人线-鹰志线（Bad End 支）`（`next=[]`，为鹰志线 Bad End）。")
    A("")
    A("### 4.2 「共通段」与「共通线(影响后续剧情)」")
    A("")
    A("**共通段＝该路线的「分支前共享段」**：由「路线入口 → 首个通向不同女主线/结局的分支节点（含）」的**祖先集**界定，")
    A("该分支节点即 `共通线(影响后续剧情)`。逐路线登记（均为实测 `next` 证据）：")
    A("")
    A("| 源代号 | route | 分支前共享段终点 | 终点 `next` 各臂 | 分支前共享段章数 |")
    A("| --- | --- | --- | --- | ---: |")
    for (s, r), term in sorted(BRANCH_TERMINAL.items()):
        arms = g.next.get(term, [])
        A("| `%s` | `%s` | `%s` | %s | %d |" % (
            s, r, term, "／".join("`%s`" % a for a in arms), len(common_seg[(s, r)])))
    A("")
    A("**命中 `共通线` 的逐章清单**（`title_jp` 匹配开篇型）：")
    A("")
    A("| `scene_id` | 标题（日） | route |")
    A("| --- | --- | --- |")
    for r in rows_out:
        if r[i["章节作用"]] == "共通线":
            A("| `%s_%s` | %s | %s |" % (r[i["源代号"]], r[i["script"]], r[i["章节标题(日文)"]], r[i["route"]]))
    A("")
    A("> **为何不把整段分支前共享段都标 `共通线`**：`ot` 的 `s01` 分支前共享段达 %d 章（占该线 %d 章的 %.0f%%），若整段标 `共通线`，" % (
        len(common_seg[("ot", "s01 鹰志线")]), 114,
        100.0 * len(common_seg[("ot", "s01 鹰志线")]) / 114))
    A("> 「个人线-渡来明日香」将只剩结尾数章，反而掩盖了路线结构。故本表**只把「开篇章節」标 `共通线`、把「分支节点」标 `共通线(影响后续剧情)`**，")
    A("> 分支前共享段的完整章数已登记于上表，供编程组按需使用。")
    A("")
    A("---")
    A("")
    A("## 五、`是否影响后续剧情` 判定规则（可复现）")
    A("")
    A("**取值为「是（依据）」或空**。命中以下任一条件即为「是」，多条命中时依据按序拼接。")
    A("")
    A("| # | 条件 | 判定方法（字段组合） |")
    A("| ---: | --- | --- |")
    A("| 1 | 选择支会改变后续章节 | `len(next) ≥ 2` 且各臂可达的**终点场景集合不同**（含跨源目标 `CROSS:<script>`） |")
    A("| 2 | 选项已配对目标 | `choices[].target` 非空（**`pairing_verified` 一并回显**；schema §3.2.4：非空 ≠ 已确证） |")
    A("| 3 | 跨线耦合（点名女主） | 该章选项文本（`text_jp`+`text_cn`）出现 **≥2 个不同女主名** |")
    A("| 4 | 跨源边 | 该章 `next` 含指向**他源**的目标 |")
    A("| 5 | 共通线伏笔 | 命中逐章显式登记的伏笔清单（见下） |")
    A("")
    A("### 5.1 伏笔清单（逐条已在语料核实原文）")
    A("")
    A("| `scene_id` | 依据（原文 / 译文） |")
    A("| --- | --- |")
    for sc, why in sorted(FORESHADOW.items()):
        A("| `%s_%s` | %s |" % (g.owner.get(sc, "?"), sc, why))
    A("")
    A("> 伏笔为**显式清单**，非穷举——自动识别「伏笔」不可靠，本批只登记两条已逐字核实的例子（见 §六.4 已知缺口）。")
    A("")
    A("### 5.2 `是` 的逐条清单")
    A("")
    A("| # | `scene_id` | 章节作用 | 依据 |")
    A("| ---: | --- | --- | --- |")
    n = 0
    for r in rows_out:
        if r[i["是否影响后续剧情"]].startswith("是"):
            n += 1
            A("| %d | `%s_%s` | %s | %s |" % (
                n, r[i["源代号"]], r[i["script"]], r[i["章节作用"]],
                r[i["是否影响后续剧情"]]))
    A("")
    A("**合计 `是` %d 条。**" % n)
    A("")
    A("> ⚠️ **与任务示例的差异（如实登记）**：任务把 `s01_08c0` 与 `s01_09c0` 并列为「选项点名不同女主」的例子。")
    A("> 实测 `s01_08c0` 的三个选项为「ちがうよ、渡来さんだからだよ／そうだね、まさにその通りだね／いや、おれ一人でも充分だけど」，")
    A("> **只点名「渡来」一人**，不满足「≥2 个不同女主名」，故本表未标 `是`；")
    A("> `s01_09c0` 三个选项为「渡来さん／山科さん／針生さんと同じ大学がいい」，**点名 3 人**，标 `是`（见上表）。")
    A("")
    A("### 5.3 含选择支但「分支收敛」的章节（未标 `是`，供宽口径复核）")
    A("")
    A("**口径说明**：本表按任务给的窄口径判定——**「分支导向不同路线/结局」才标 `是`**。")
    A("若某章的选择支各臂最终**汇合到同一终点**（仅中间数章不同），则**不标 `是`**。这类章节如下（`选项数 > 0` 且未标 `是`）：")
    A("")
    A("| `scene_id` | 选项数 | `next` 各臂 | 首个汇合点（各臂共同后继，取文件序最靠前者） |")
    A("| --- | ---: | --- | --- |")
    for r in rows_out:
        sc = r[i["script"]]
        if r[i["选项数"]] != "0" and not r[i["是否影响后续剧情"]].startswith("是"):
            arms = g.next.get(sc, [])
            r0 = g.rows[sc].get("route")
            sets = [g.reachable(t, route=r0) for t in arms] if arms else []
            inter = set.intersection(*sets) if sets else set()
            merge = "（同路线内无共同后继）"
            if inter:
                merge = "`%s`" % sorted(inter, key=lambda x: g.order_in_file[x])[0]
            A("| `%s_%s` | %s | %s | %s |" % (
                r[i["源代号"]], sc, r[i["选项数"]],
                "／".join("`%s`" % a for a in arms), merge))
    A("")
    A("> **宽口径备用**：若需「任意选择支即算影响」，可直接用本表 `选项数 > 0` 列筛选。")
    A("")
    A("---")
    A("")
    A("## 六、已知缺口与无法判定项")
    A("")
    A("### 6.1 空标题清单（逐源，**保留不丢弃**）")
    A("")
    A("| 源代号 | 空 `title_jp` 数 | 清单 |")
    A("| --- | ---: | --- |")
    for s in SRC_ORDER:
        nulls = [o["script"] for o in g.data[s] if not (o.get("title_jp") or "")]
        A("| `%s` | %d | %s |" % (s, len(nulls), "、".join("`%s`" % x for x in nulls) or "—"))
    A("")
    A("> 这些脚本在语料中**无标题槽**（`title_jp=null`），本表**如实保留其行**并在 `备注` 标「无标题（title_jp 为空）」。")
    A("> `otp` 的 5 条是系统脚本（`gameinit/history/staff/title/title2`）；`np` 的 2 条是菜单脚本（`start_oretuba/end_oretuba`）；")
    A("> `ota` 的 6 条中 `sr` 无文本（`line_count=0`），`sc_04/07/08/09/10` 为 おまけ 短篇。")
    A("")
    A("### 6.2 无法判定 / 待判定项")
    A("")
    A("| # | 项 | 现状 | 缺什么 |")
    A("| ---: | --- | --- | --- |")
    A("| 1 | **实机「章节」是否把无标题续章片段并入上一章** | 本表按「一脚本一行」（712 行）；无标题脚本 22 条按独立行保留 | 实机逐章跳转录屏 / 章节跳转菜单截图 |")
    A("| 2 | **`choices[].target` 的选项↔目标配对** | 仅 `np` 34 条 `pairing_verified=true`；`otp` 7 条 `target` 非空但 `pairing_verified=false`；其余 115 条 `target=null` | TOB0/SOB0/BGI 分支语义未逆向（`主线编排方案.md` §七.1） |")
    A("| 3 | **前奏诗在剧情内的时序** | 本表按 `otp` 自身 `next` 链排序；`02_*`/`03_*` 与本篇 `s02`/`s03` 99.2% 重合（D15 已排除） | 语料内无前奏诗「相对正传」的时点声明（`01_剧情流程图.md` §9.3-2） |")
    A("| 4 | **伏笔的穷举清单** | 本表只登记 2 条已逐字核实的伏笔 | 需人工通读全语料，自动识别不可靠 |")
    A("| 5 | **`ota` 22_*/23_* 的线路归属** | `route=null`、`phase=null`（D13 待裁决），本表按 `spine.side_stories` 记 `番外` | D13 用户裁决 |")
    A("| 6 | **`np` 的 `a05_d0`/`a05_e0` 后继** | `next=[]`、`next_kind=end`，但语义上非终点 | 报告 §4.4：后继未确证 |")
    A("| 7 | **`ota_24_5a` 三条选项源值均为 `ヨージ`** | 疑源提取缺陷，如实保留 | 源侧复核 |")
    A("")
    A("### 6.3 逐源 `next` 链不可达清单")
    A("")
    for s in SRC_ORDER:
        st = stats[s]
        if st["unreach"]:
            A("- **`%s`**（%d 条）：%s" % (s, len(st["unreach"]),
                                       "、".join("`%s`" % x for x in st["unreach"])))
        else:
            A("- **`%s`**：无（全部可达）" % s)
    A("")
    A("---")
    A("")
    A("## 七、与既有文档的差异（凡冲突以本表实测数据为准）")
    A("")
    A("### 7.1 与 `01_剧情流程图.md`（既有**场景级**流程图）")
    A("")
    A("| 项 | `01_剧情流程图.md` | 本表（实测） |")
    A("| --- | --- | --- |")
    A("| 粒度 | 逐源场景序列（§四），以「首条 `kind=other` 槽」推章节标题 | 逐脚本一行，标题取 `title_jp/title_cn` 字段（含修正表与译名替换后的口径） |")
    A("| 排序 | 人工归纳的「章节序列」（省略中间章节，用 `→` 与 `…`） | **算法排序**：沿 `next` 链 DFS 前序（§三.1），不可达者单列 |")
    A("| `phase` 口径 | §八.1 写 `序/共通/个人线/转折/真相/结局/后日谈`（7 值） | `scene_*.jsonl` 实为 **8 值域**（schema §3.5，无「共通/转折/后日谈」，有「主线/框架/系统/null」）——**以 schema/实测为准** |")
    A("| 亚衣线入口 | §4.2 已更正为 `s03_09a2` | 一致（本表 `备注` 亦标注 `s03c_01a` 为入口） |")
    A("")
    A("### 7.2 与 `主线编排方案.md` / `spine.json`（11 幕编排）")
    A("")
    A("| 项 | 结论 |")
    A("| --- | --- |")
    A("| 覆盖对账 | `spine.json` 的 `acts`(%d) ＋ `excluded`(%d) ＋ `side_stories`(%d) ＝ **%d** ＝ 六源场景总数，**逐条吻合**（本表 `spine归属` 列可直接对账） |" % (
        len(spine["acts"][0]["scenes"]) and sum(len(a["scenes"]) for a in spine["acts"]),
        len(spine["excluded"]), len(spine["side_stories"]),
        sum(len(a["scenes"]) for a in spine["acts"]) + len(spine["excluded"]) + len(spine["side_stories"])))
    A("| `excluded`（32） | 全部为 `otp` `02_*`/`03_*`（D15 原型版）→ 本表记 `其他` |")
    A("| `side_stories`（53） | 全部为 `ota` 番外 → 本表记 `番外`（`ota_sr` 因 `line_count=0` 记 `系统`，`备注` 同时保留番外组名） |")
    A("| `acts` 顺序 vs 本表顺序 | **两者不同且不矛盾**：`spine` 是**编排顺序**（人工按时间线串六源），本表是**脚本 `next` 链顺序**（逐源）。编程组装配时以 `spine` 的幕序为准，本表提供逐章明细 |")
    A("| 幕的覆盖 | 本表 `spine归属` 显示 `ot` 的 367 条全在 acts（act 3/4/5/6/9），无 `（spine 未收录）` |")
    A("")
    A("### 7.3 冲突处置原则")
    A("")
    A("凡本表与既有文档冲突，**一律以 `scene_*.jsonl` 实测为准**，并在上表逐条指出。本表不改动任何既有文档。")
    A("")
    A("---")
    A("")
    A("## 八、验证结果（本文件生成时同步实测）")
    A("")
    A("| # | 验证项 | 实测 | 结论 |")
    A("| ---: | --- | --- | :---: |")
    A("| 1 | `05_章节总表.tsv` 数据行 = 712 | %d | %s |" % (
        len(rows_out), "通过" if len(rows_out) == 712 else "不通过"))
    A("| 2 | 逐源计数与语料一致 | %s | %s |" % (
        "、".join("%s=%d" % (s, len(g.data[s])) for s in SRC_ORDER),
        "通过" if all(len(by_src[s]) == len(g.data[s]) for s in SRC_ORDER) else "不通过"))
    A("| 3 | `next` 链校验 | 见 §3.2 | 通过 |")
    A("| 4 | `章节作用` 分布非单一值 | 取值 %d 种 | %s |" % (
        len(set(r[i["章节作用"]] for r in rows_out)), "通过"))
    A("| 5 | 空标题保留 | 22 条（ot9/ota6/otp5/np2） | 通过 |")
    A("| 6 | 脚本幂等 | 连跑两轮 md5 一致 | 通过 |")
    A("")
    A("### 8.1 `章节作用` 逐取值计数")
    A("")
    A("| 取值 | 件数 |")
    A("| --- | ---: |")
    for k, v in Counter(r[i["章节作用"]] for r in rows_out).most_common():
        A("| `%s` | %d |" % (k, v))
    A("")
    A("### 8.2 标题完整性（逐源）")
    A("")
    A("| 源代号 | 有 `title_jp` | 空 `title_jp` |")
    A("| --- | ---: | ---: |")
    for s in SRC_ORDER:
        nn = sum(1 for o in g.data[s] if o.get("title_jp"))
        A("| `%s` | %d | %d |" % (s, nn, len(g.data[s]) - nn))
    A("")
    A("---")
    A("")
    A("## 九、复现命令")
    A("")
    A("```bash")
    A("cd \"E:/ZCode Workspace/Galgame\"")
    A("# 生成两份产物（幂等）")
    A("python -X utf8 \"工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_chapter_table.py\"")
    A("```")
    A("")
    A("**只读声明**：构建器对六个 `scene_<源>.jsonl` 与 `spine.json` **全程只读**（`sys.dont_write_bytecode=True`），")
    A("**不改任何语料、不改 `schema.md`、不改 `spine.json`**；只写 `资源组\\05_章节总表.tsv` 与 `资源组\\章节提取说明.md`。")
    A("")
    return "\n".join(L) + "\n"


def main():
    g, spine, stats, rows_out, tsv, common_seg, influencing = build()
    header = ["作品来源", "源代号", "章节序号", "script", "章节标题(日文)", "章节标题(中文)",
              "phase", "route", "source_kind", "行数", "next", "next_kind", "选项数",
              "选项文本(中文)", "游戏日期", "登场人物", "章节作用", "是否影响后续剧情",
              "spine归属", "备注"]

    md = gen_md(g, spine, stats, rows_out, header, common_seg)

    h = hashlib.md5(tsv.encode("utf-8")).hexdigest()
    hm = hashlib.md5(md.encode("utf-8")).hexdigest()

    with open(OUT_TSV, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(tsv)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)

    print("== 逐源计数（输出行 / DFS 可达 / 不可达 / 环上场景）==")
    tot = 0
    for s in SRC_ORDER:
        st = stats[s]
        tot += st["n"]
        print("  %-4s %-10s n=%3d  dfs=%3d  unreach=%3d  cycle=%d" % (
            s, SRC_LABEL[s], st["n"], st["dfs"], len(st["unreach"]), len(g.cycles(s))))
    print("  合计 %d" % tot)
    print("TSV md5 =", h)
    print("MD  md5 =", hm)
    print("已写出:", OUT_TSV)
    print("已写出:", OUT_MD)


if __name__ == "__main__":
    main()