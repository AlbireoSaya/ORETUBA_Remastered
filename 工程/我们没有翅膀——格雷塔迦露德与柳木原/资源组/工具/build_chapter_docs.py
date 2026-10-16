# -*- coding: utf-8 -*-
"""
build_chapter_docs.py —— 由 05_章节总表.tsv 生成两份章节级交付物

产物（只写这两个文件，均幂等、可复跑）：
  1. 资源组\06_章节总表.md   人读版章节总表（唯一归属口径，712 行逐章）
  2. 资源组\07_路线脉络.md   每条路线的完整章节脉络（沿 next[i] 的播放路径）

只读输入：
  资源组\05_章节总表.tsv
（不改语料、不改 schema、不改 spine、不改任何既有文档）

排序算法（§3 复用 章节提取说明.md 的 next 语义）：
  每条路线取其脚本集合，在集合内部做「Kahn 拓扑排序 + 章节序号(TSV 行序) 小者优先」，
  故收敛分支的两臂相邻列出、分支点先于两臂、汇合点后于两臂；孤立链回退 TSV 行序。

用法：
  python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_chapter_docs.py"
"""

import csv
import io
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                       # 资源组\
ROOT = os.path.dirname(RES)                       # 工程\我们没有翅膀...
TSV = os.path.join(RES, "05_章节总表.tsv")
OUT06 = os.path.join(RES, "06_章节总表.md")
OUT07 = os.path.join(RES, "07_路线脉络.md")

SRC_NAME = {"ot": "本篇", "ota": "AfterStory", "otp": "前奏诗",
            "otr": "R版亚衣线", "otv": "PSV美咲线", "np": "涅布明日香篇"}
SRC_ORDER = ["otp", "ot", "otr", "otv", "ota", "np"]

# ─────────────────────────── 读取 ───────────────────────────

def load():
    with io.open(TSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for i, r in enumerate(rows):
        r["_idx"] = i
    by = {r["script"]: r for r in rows}
    return rows, by


def nx(by, s):
    v = (by[s]["next"] or "").strip()
    if not v or v == "（无）":
        return []
    return [x for x in v.split("；") if x]


# ────────────── 路线内播放顺序：沿 next[] 的分支感知 DFS 展开 ──────────────
#
# 目标：分支点在前、各臂相邻、汇合点在后（不是 TSV 的 DFS 前序「先走到底再回溯」）。
# 算法：
#   1. reach(x) = x 在成员集合内沿 next 可达的节点集（含 x）
#   2. join(arms) = 各臂可达集的交集中「极小」的节点；若极小节点有多个（并列入口），
#      对它们递归再求 join（例：s03_03f 的两臂先并到 {04a1,04a2}，再并到 04b）
#   3. emit(u, stop)：遇到 stop 中的节点即停；分支处对每臂以 stop∪{join} 递归，
#      最后从 join 继续。这样各臂只展开到汇合点为止。
# 该展开保证：任一节点的全部成员内前驱必先于它出现（即严格沿 next 播放顺序）。

def _reach(by, members, u):
    seen, st = set(), [u]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x)
        for t in nx(by, x):
            if t in members:
                st.append(t)
    return seen


def _join(by, members, arms):
    if len(arms) < 2:
        return None
    common = None
    for a in arms:
        r = _reach(by, members, a)
        common = r if common is None else (common & r)
    if not common:
        return None
    mins = [v for v in common
            if not any(v in _reach(by, members, w) for w in common if w != v)]
    if len(mins) == 1:
        return mins[0]
    return _join(by, members, mins)


def play_order(by, members):
    """members: set(script) → 按 next[] 的播放顺序（分支感知 DFS）。"""
    members = set(members)
    out, visited = [], set()
    stop0 = frozenset()

    def emit(u, stop):
        if u in visited or u in stop:
            return
        visited.add(u)
        out.append(u)
        arms = [t for t in nx(by, u) if t in members]
        if not arms:
            return
        if len(arms) == 1:
            emit(arms[0], stop)
            return
        J = _join(by, members, arms)
        s2 = set(stop)
        if J is not None:
            s2.add(J)
        for t in arms:
            emit(t, frozenset(s2))
        if J is not None:
            emit(J, stop)

    # 入口：成员集合内无成员内前驱者，按 TSV 行序
    pred = set()
    for s in members:
        for t in nx(by, s):
            if t in members:
                pred.add(t)
    roots = sorted([s for s in members if s not in pred], key=lambda s: by[s]["_idx"])
    for r in roots:
        emit(r, stop0)
    if len(out) != len(members):          # 兜底：剩余节点（环/孤点）按行序补齐
        for s in sorted(members - visited, key=lambda s: by[s]["_idx"]):
            out.append(s)
    assert len(out) == len(members), ("play_order failed", len(out), len(members))
    return out


def topo(by, members):        # 兼容旧调用名
    return play_order(by, members)


def anc(by, members, t):
    """members 内可到达 t 的节点集合（不含 t）。"""
    pred = {}
    for s in members:
        for x in nx(by, s):
            if x in members:
                pred.setdefault(x, set()).add(s)
    seen, st = set(), [t]
    while st:
        u = st.pop()
        for v in pred.get(u, ()):
            if v not in seen:
                seen.add(v)
                st.append(v)
    return seen


def desc(by, members, u):
    seen, st = set(), [u]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x)
        for t in nx(by, x):
            if t in members:
                st.append(t)
    return seen


# ─────────────────────── 路线定义 ───────────────────────

def scripts_of(rows, pred):
    return {r["script"] for r in rows if pred(r)}


def build_routes(rows, by):
    ot = scripts_of(rows, lambda r: r["源代号"] == "ot")
    s01 = {s for s in ot if s.startswith("s01_")}
    s02 = {s for s in ot if s.startswith("s02_")}
    s03 = {s for s in ot if s.startswith("s03_")}
    s04 = {s for s in ot if s.startswith("s04_")}
    s00 = {s for s in ot if s.startswith("s00_")}

    # s01 内的分支归属（实测：s01_14g 三臂 / s01_14i 两臂为 SPLIT）
    JING = ["s01_14g1", "s01_14h", "s01_17a", "s01_18a"]      # 山科京支路
    BAD = ["s01_14g2", "s01_14j2"]                              # 鹰志线 Bad End 支
    ming_path = s01 - set(JING) - set(BAD)                      # 明日香主路 108
    # 京路径 = s00_00 + 鹰志线前半(s01_01a–s01_05) + 分支前共享段 + 京臂 + 解纜
    chain_a = anc(by, s01, "s01_05") | {"s01_05"}
    jing_common = anc(by, s01, "s01_14g") | {"s01_14g"}
    jing_path = set(s00) | chain_a | jing_common | set(JING) | {"s01_19a"}

    def ota_p(pref):
        return scripts_of(rows, lambda r: r["源代号"] == "ota" and r["script"].startswith(pref))

    R = []

    def add(rid, title, kind, src, members, note, stage_hint=None):
        R.append(dict(rid=rid, title=title, kind=kind, src=src,
                      members=set(members), note=note, stage_hint=stage_hint))

    # —— 本篇（女主线含 AfterStory 后日谈，按用户格式同节排列）——
    add(1, "渡来明日香", "本篇主线 ＋ AfterStory 后日谈",
        "ot+ota", s00 | ming_path | ota_p("11_"),
        "本篇《我们没有翅膀》鹰志线（s01）主线女主；山科京为其副线（s01_14g 分岐）。"
        "本篇含鹰志线前半（s01_01a–s01_05）与解缆后半（s01_05a–s01_19a）两段，"
        "后半经 s04_06k 汇入；AfterStory 由 11_* 承接后日谈（对决羽田鹰志篇）。", None)
    add(2, "山科京", "本篇副线",
        "ot", jing_path,
        "本篇鹰志线（s01）副女主线，自 s01_14g《五里霧中》的**臂 1**（`next[0]`）分岐。"
        "本线与渡来明日香线共用 s01_14g 之前的全部章节（标〔共用〕）；"
        "前半 s01_01a–s01_05 经 s02→s03→s04 的绕行后才回到本线，故与明日香线共用。", None)
    add(3, "玉泉日和子", "本篇主线 ＋ AfterStory 后日谈",
        "ot+ota", s02 | ota_p("12_"),
        "本篇鹫介线（s02）主线女主；含解缆后半 s02_10a–s02_17a（经 s04_06k 汇入）；"
        "AfterStory 由 12_* 承接后日谈（对决千岁鹫介篇）。", None)
    add(4, "凤鸣", "本篇主线 ＋ AfterStory 后日谈",
        "ot+ota", s03 | ota_p("13_"),
        "本篇隼人线（s03）主线女主；含解缆后半 s03_16a–s03_24（经 s04_06j1 臂 1 汇入）；"
        "s03_08b 的**臂 2**（`next[1]`）分岐出 R 版亚衣线；AfterStory 由 13_* 承接后日谈（对决成田隼人篇）。", None)
    add(5, "大路线（真相）", "本篇终章",
        "ot", s04,
        "本篇 s04 大路线（74 章 ＝ 真相 72 章 ＋ 结局 2 章）：多元世界真相 → 假统合 → 真·兄妹再会 → 不完全统合，"
        "收束全线的唯一真结局（s04_28b 真·兄妹再会 / s04_29a 解缆·真 END）。", None)
    add(6, "鹰志线 Bad End 支", "本篇副支",
        "ot", set(BAD),
        "鹰志线两个不归入任何女主线的死路分支（next 为空），如实保留。", None)

    # —— 跨作品 ——
    add(7, "香田亚衣", "R版亚衣线",
        "otr", scripts_of(rows, lambda r: r["源代号"] == "otr"),
        "R 版追加的亚衣线，入口为本篇 s03_09a2《なべて世は（Ｃ）》→ s03c_01a，"
        "是 s03 隼人线内的分支而非并列平行线。", None)
    add(8, "林田美咲", "PSV美咲线 ＋ AfterStory 后日谈",
        "otv+ota", scripts_of(rows, lambda r: r["源代号"] == "otv") | ota_p("21_"),
        "PSV 版追加的美咲线，承本篇鹰志线 Bad End（s01_14j2）的同期分支；"
        "AfterStory 由 21_* 承接后日谈。", None)
    add(9, "羽田小鸠（后日谈）", "AfterStory",
        "ota", ota_p("14_"),
        "AfterStory 对决羽田小鹰志篇，小鸠线后日谈（本篇无独立小鸠线）。", None)
    add(10, "最终统合线（后日谈）", "AfterStory",
        "ota", ota_p("24_"),
        "AfterStory 最终统合线：24_1a《仮統合の崩壊》→ 24_4e 分岐 → G-END / B-END。", None)
    add(11, "AfterStory 番外", "番外",
        "ota", {r["script"] for r in rows if r["源代号"] == "ota"
                and (r["章节作用"] == "番外" or r["script"] == "sr")},
        "AfterStory 的 52 章番外（22/23 群像、31–34 各线 after、41/42 新年行军、"
        "50–54 没翅剧场、61–64 与 sc_* おまけ）＋ 系统脚本 sr。", None)
    add(12, "渡来明日香（涅布追加）", "涅布明日香篇",
        "np", scripts_of(rows, lambda r: r["源代号"] == "np"),
        "涅布＊プラス 明日香篇：毕业后 2 月的子篇目菜单式短篇集，"
        "start_oretuba 为菜单脚本（34 条选择支全挂于此）。", None)

    # —— 前奏诗 ——
    def otp(pref):
        return scripts_of(rows, lambda r: r["源代号"] == "otp" and r["script"].startswith(pref))

    add(13, "前奏诗·明日香篇", "前奏诗",
        "otp", otp("p01_"), "前奏诗四角色短篇之一（p01，4 章）。", None)
    add(14, "前奏诗·山科京篇", "前奏诗",
        "otp", otp("p02_"), "前奏诗四角色短篇之一（p02，5 章）。", None)
    add(15, "前奏诗·美咲篇", "前奏诗",
        "otp", otp("p03_"), "前奏诗四角色短篇之一（p03，4 章）。", None)
    add(16, "前奏诗·轻部狩男篇", "前奏诗",
        "otp", otp("p04_"), "前奏诗四角色短篇之一（p04，5 章）。", None)
    add(17, "前奏诗·框架剧 buru", "前奏诗",
        "otp", otp("buru"), "火烈鸟三人＋ＡＤさん主持的剧场框架剧（buru01–04，4 章）。", None)
    add(18, "前奏诗·原型版 02/03（D15 已排除）", "前奏诗",
        "otp", otp("02_") | otp("03_"),
        "前奏诗 02《邂逅·鹫介》/ 03《邂逅·隼人》原型版，与本篇 s02/s03 99.2% 重合，"
        "D15 判定不入主干；如实保留以完成对账。", None)
    add(19, "前奏诗·系统脚本", "前奏诗",
        "otp", otp("gameinit") | otp("history") | otp("staff") | otp("title") | otp("title2"),
        "引擎初始化 / 回想 / 制作人员 / 标题画面，无剧情时序。", None)

    return R


# ─────────────────────── 标注 ───────────────────────

def tags_of(r):
    t = []
    if r["章节作用"] == "番外":
        t.append("【番外】")
    if r["章节作用"] == "短剧情":
        t.append("【短剧情】")
    if r["章节作用"] == "其他":
        t.append("【原型版·不入主干】")
    if r["章节作用"] == "系统":
        t.append("【系统】")
    if r["章节作用"] == "框架":
        t.append("【框架剧】")
    if not (r["章节标题(日文)"] or "").strip():
        t.append("【无标题】")
    return "".join(t)


EVIDENCE = {
    "ot_s03_08b": "next 两臂终点不同：臂1 继续鸣线至 s03_24，臂2 跨到 R 版亚衣线 s03c_01a。",
    "ot_s04_05i": "next 两臂终点不同：臂1（不带来救赎）走向分岐回收，臂2（带来救赎）直抵真 END s04_29a。",
    "ot_s04_06j1": "next 三臂终点不同：s03_16a→s03_24 / s04_06k→s03_24 / s04_06l 自身即终点。",
    "ot_s04_06k": "next 两臂终点不同：s01_05a→明日香解缆链、s02_10a→日和子解缆链。",
    "ot_s01_09c0": "选项点名 3 位女主（渡来／山科／针生），改变后续章节。",
    "ot_s01_09d": "共通线伏笔：提到 WING QUEST（「ウイングクエストって知ってるか」），后于 s04 大路线回收。",
    "ot_s01_14g": "next 三臂终点不同：臂1→京 END、臂2→Bad End（死路）、臂3→明日香解缆链。",
    "ot_s01_14i": "next 两臂终点不同：臂1→明日香 END，臂2→Bad End（死路）。",
    "ot_s02_10c": "选项点名多位女主（纪奈子／英里子），改变后续章节。",
    "ot_s04_25b": "共通线伏笔：提到 伊丹さん（「伊丹さんが何でも言うこと聞くと言ったとき…」），指向被封印的长兄人格。",
    "ot_s03_09a2": "跨源边 → s03c_01a（R 版亚衣线入口）。",
    "ota_11_3d0": "选项点名多位女主（京／渡来／山科／针生），改变后续章节。",
    "ota_24_4e": "next 两臂终点不同：24_5a→24_5b（G-END）／24_5c（B-END）。",
    "otp_02_03g": "选项已填 target（3 条，pairing_verified=部分 false）；该场景 D15 已排除，不入主干。",
    "otp_03_03b": "选项已填 target（2 条，pairing_verified=部分 false）；该场景 D15 已排除，不入主干。",
    "otp_03_03i": "选项已填 target（2 条，pairing_verified=部分 false）；该场景 D15 已排除，不入主干。",
    "np_a05_a0": "next 四臂终点不同（a05_b0／a05_c0／a05_d0 死路／a05_e0 死路）。",
    "np_start_oretuba": "菜单根：34 条选择支分别指向 a01–a06 各子篇目，next 26 臂终点不同。",
}


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


# ─────────────────────── 生成 06 ───────────────────────

def gen06(rows, by, routes):
    own = {}          # script -> (route_rid, group_label)
    groups = []       # (作品, 分组标题, 脚本有序列表)

    def emit_group(work, label, members, order=None):
        ms = set(members)
        if not ms:
            return
        seq = order if order is not None else topo(by, ms)
        groups.append((work, label, seq))
        for s in seq:
            own[s] = (len(groups), label)

    # 前奏诗
    otp = scripts_of(rows, lambda r: r["源代号"] == "otp")
    emit_group("前奏诗", "框架剧 buru（4 章）", {s for s in otp if s.startswith("buru")})
    emit_group("前奏诗", "四短篇 p01 明日香篇（4 章）【短剧情】", {s for s in otp if s.startswith("p01_")})
    emit_group("前奏诗", "四短篇 p02 山科京篇（5 章）【短剧情】", {s for s in otp if s.startswith("p02_")})
    emit_group("前奏诗", "四短篇 p03 美咲篇（4 章）【短剧情】", {s for s in otp if s.startswith("p03_")})
    emit_group("前奏诗", "四短篇 p04 轻部狩男篇（5 章）【短剧情】", {s for s in otp if s.startswith("p04_")})
    emit_group("前奏诗", "原型版 02 邂逅·鹫介（16 章）【原型版·不入主干】", {s for s in otp if s.startswith("02_")})
    emit_group("前奏诗", "原型版 03 邂逅·隼人（16 章）【原型版·不入主干】", {s for s in otp if s.startswith("03_")})
    emit_group("前奏诗", "系统脚本（5 章）【系统】",
               {"gameinit", "history", "staff", "title", "title2"})

    # 本篇
    ot = scripts_of(rows, lambda r: r["源代号"] == "ot")
    JING = ["s01_14g1", "s01_14h", "s01_17a", "s01_18a"]
    BAD = ["s01_14g2", "s01_14j2"]
    s01 = {s for s in ot if s.startswith("s01_")}
    emit_group("本篇", "序文 s00（1 章）【共通线】", {s for s in ot if s.startswith("s00_")})
    emit_group("本篇", "鹰志线 s01·明日香主路（108 章）", s01 - set(JING) - set(BAD))
    emit_group("本篇", "鹰志线 s01·山科京支路（4 章）", set(JING))
    emit_group("本篇", "鹰志线 s01·Bad End 支（2 章）", set(BAD))
    emit_group("本篇", "鹫介线 s02·玉泉日和子（83 章）", {s for s in ot if s.startswith("s02_")})
    emit_group("本篇", "隼人线 s03·凤鸣（95 章）", {s for s in ot if s.startswith("s03_")})
    emit_group("本篇", "大路线 s04·真相（74 章）", {s for s in ot if s.startswith("s04_")})

    # 其他源
    emit_group("R版亚衣线", "香田亚衣线 s03c（55 章）",
               scripts_of(rows, lambda r: r["源代号"] == "otr"))
    emit_group("PSV美咲线", "林田美咲线 M/P03（31 章）",
               scripts_of(rows, lambda r: r["源代号"] == "otv"))

    ota = scripts_of(rows, lambda r: r["源代号"] == "ota")
    emit_group("AfterStory", "对决羽田鹰志 11_*·明日香后日谈（21 章）", {s for s in ota if s.startswith("11_")})
    emit_group("AfterStory", "对决千岁鹫介 12_*·日和子后日谈（22 章）", {s for s in ota if s.startswith("12_")})
    emit_group("AfterStory", "对决成田隼人 13_*·鸣后日谈（19 章）", {s for s in ota if s.startswith("13_")})
    emit_group("AfterStory", "对决羽田小鹰志 14_*·小鸠后日谈（28 章）", {s for s in ota if s.startswith("14_")})
    emit_group("AfterStory", "美咲线 21_*·美咲后日谈（9 章）", {s for s in ota if s.startswith("21_")})
    emit_group("AfterStory", "最终统合线 24_*（20 章）", {s for s in ota if s.startswith("24_")})
    emit_group("AfterStory", "番外（52 章）＋ 系统脚本 sr（1 章）【番外】",
               {s for s in ota if by[s]["章节作用"] == "番外"} | {"sr"})

    emit_group("涅布明日香篇", "明日香篇 a01–a06（28 章）【短剧情】",
               scripts_of(rows, lambda r: r["源代号"] == "np"))

    # —— 校验 ——
    covered = sum(len(g[2]) for g in groups)
    assert covered == len(rows), ("06 覆盖数不符", covered, len(rows))
    assert len(own) == len(rows), ("06 唯一归属失败", len(own), len(rows))

    L = []
    W = L.append
    W("# 06 · 《我们没有翅膀——格雷塔迦露德与柳木原》全系列章节总表")
    W("")
    W("> 模块：`ISSUE-20260920-17` ｜ 生成器：`资源组\\工具\\build_chapter_docs.py`（只读 `05_章节总表.tsv`，幂等）")
    W("> 数据源：`资源组\\05_章节总表.tsv`（712 行）。**本表为「唯一归属」口径：712 章每章恰好出现一次，合计 = 712。**")
    W("> 标题栏 `日文标题` 与 `中文标题` 均逐字取自 `05_章节总表.tsv`；标题为空者照实写「（无标题）」。")
    W("> `是否影响后续剧情 = 是` 共 18 件，逐条在表内附一句依据；其余留空（窄口径，见 `章节提取说明.md` §5）。")
    W("> **播放序**为「本条路线内」的顺序号（沿 `next` 的分岐感知拓扑序：分支点在前、各臂相邻、汇合点在后）。")
    W("> **分岐臂口径**：`next` 第 i 项记作「臂 i」；「选项 i → `next[i]`」仅在选项数与 `next` 项数相等的 32 章成立，")
    W("> 其余 18 章（`24_*` 系列等）配对未确证，本表按「臂」表述、不臆称「选第 N 项」。")
    W("")
    W("## 一、总览")
    W("")
    W("### 1.1 作品 × 章节数")
    W("")
    W("| 作品 | 章节数 | 占全系列 |")
    W("| --- | ---: | ---: |")
    wc = {}
    for w, _, seq in groups:
        wc[w] = wc.get(w, 0) + len(seq)
    for w in SRC_ORDER and ["前奏诗", "本篇", "R版亚衣线", "PSV美咲线", "AfterStory", "涅布明日香篇"]:
        W("| %s | %d | %.1f%% |" % (w, wc[w], 100.0 * wc[w] / len(rows)))
    W("| **合计** | **%d** | **100%%** |" % len(rows))
    W("")
    W("### 1.2 章节作用分布（`章节作用` 逐取值计数，全 712 章）")
    W("")
    W("| 章节作用 | 件数 |")
    W("| --- | ---: |")
    rc = {}
    for r in rows:
        rc[r["章节作用"]] = rc.get(r["章节作用"], 0) + 1
    for k in sorted(rc, key=lambda k: (-rc[k], k)):
        W("| `%s` | %d |" % (esc(k), rc[k]))
    W("| **合计** | **%d** |" % len(rows))
    W("")
    W("### 1.3 分组 × 章数")
    W("")
    W("| 作品 | 分组 | 章数 |")
    W("| --- | --- | ---: |")
    for w, label, seq in groups:
        W("| %s | %s | %d |" % (w, esc(label), len(seq)))
    W("| **合计** | — | **%d** |" % covered)
    W("")
    W("### 1.4 特殊标注说明")
    W("")
    W("| 标记 | 含义 | 件数 |")
    W("| --- | --- | ---: |")
    W("| 【番外】 | `章节作用 = 番外` 的 AfterStory 追加短篇 | %d |" % rc.get("番外", 0))
    W("| 【短剧情】 | `章节作用 = 短剧情`（前奏诗四短篇 p01–p04 ＋ 涅布明日香篇） | %d |" % rc.get("短剧情", 0))
    W("| 【原型版·不入主干】 | `章节作用 = 其他`（前奏诗 02_*/03_*，D15 已排除） | %d |" % rc.get("其他", 0))
    W("| 【系统】 | `章节作用 = 系统`（引擎初始化／回想／制作人员／标题／菜单） | %d |" % rc.get("系统", 0))
    W("| 【框架剧】 | `章节作用 = 框架`（前奏诗 buru01–04） | %d |" % rc.get("框架", 0))
    W("| 【无标题】 | `title_jp` 为空（续章片段，如实保留） | %d |"
      % sum(1 for r in rows if not (r["章节标题(日文)"] or "").strip()))
    W("")
    W("---")
    W("")
    W("## 二、逐章总表（唯一归属，按 作品 → 路线 → 播放顺序）")
    W("")
    W("说明：`播放序` 为该章在**本条路线内**的顺序号（沿 `next` 的拓扑序；收敛分支的两臂相邻列出）。")
    W("`是否影响后续剧情` 列为「是」者，其后附一句依据。")
    W("")

    for gi, (w, label, seq) in enumerate(groups, 1):
        W("### 2.%d 【%s】%s" % (gi, w, esc(label)))
        W("")
        W("| 播放序 | script | 作品来源 | 日文标题 | 中文标题 | 章节作用 | 选项数 | 是否影响后续剧情 | 标记 |")
        W("| ---: | --- | --- | --- | --- | --- | ---: | --- | --- |")
        for i, s in enumerate(seq, 1):
            r = by[s]
            jp = (r["章节标题(日文)"] or "").strip() or "（无标题）"
            cn = (r["章节标题(中文)"] or "").strip() or "（无标题）"
            eff = (r["是否影响后续剧情"] or "").strip()
            if eff.startswith("是"):
                ev = EVIDENCE.get(r["_sid"] if "_sid" in r else r["源代号"] + "_" + s, "")
                eff = "**是**（%s）" % ev if ev else "**是**"
            W("| %d | `%s` | %s | %s | %s | %s | %s | %s | %s |"
              % (i, s, SRC_NAME[r["源代号"]], esc(jp), esc(cn), esc(r["章节作用"]),
                 (r["选项数"] or "0"), eff, tags_of(r)))
        W("")
    return "\n".join(L) + "\n", groups, own


# ─────────────────────── 生成 07 ───────────────────────

STAGE = {
    "共通线": "共通线", "共通线(影响后续剧情)": "共通线",
    "真相": "真相", "番外": "番外", "短剧情": "短剧情",
    "系统": "系统", "框架": "框架", "其他": "其他",
}


def stage_of(r):
    a = r["章节作用"]
    if a in STAGE:
        return STAGE[a]
    if a.startswith("个人线-"):
        return "个人线"
    if a.startswith("结局-"):
        return "结局"
    return a


def line_of(r):
    """用户标准格式 `阶段-作品《标题》`；《》内取**中文标题**（与用户示例一致），
    原文日文标题以 〔〕 附注（逐字取自 05_章节总表.tsv，供比对，不臆造）。
    两栏同时为空时只写「（无标题）」，不重复附注。"""
    jp = (r["章节标题(日文)"] or "").strip() or "（无标题）"
    cn = (r["章节标题(中文)"] or "").strip() or "（无标题）"
    body = "%s-%s《%s》" % (stage_of(r), SRC_NAME[r["源代号"]], cn)
    if jp != cn:
        body += "〔%s〕" % jp
    return body


# ── 每条路线的「分岐路径」注解（全部来自 05_章节总表.tsv 的 next 字段实测）──
# 口径：`next` 的第 i 项记作「臂 i」（i 从 1 起）。**「选项 i → next[i]」仅在
# 选项数与 next 项数相等的 32 章成立**（如 s01_02c 2 选项 2 臂、s01_09c0 3 选项 3 臂），
# 其余 18 章（如 24_* 系列 3 选项 1 臂、24_4e 3 选项 2 臂）配对未确证，
# 故本注解一律以「臂 N」表述，不臆称「选第 N 项」。
ROUTE_PATH = {
    1: "`s01_14g`《五里霧中》三臂中走**臂 3** → `s01_14i`；`s01_14i` 两臂中走**臂 1** → "
       "`s01_14j1 → s01_14k → s01_14l → s01_15a → s01_15b → s01_16a`（明日香 END）。"
       "解缆后半自大路线 `s04_06k` 两臂中走**臂 1** → `s01_05a` 汇入本线（其后 s01 主链全文见本节章表），"
       "终至 `s01_19a`《解纜》。（`s01_14g`／`s01_14i` 均无选项文本，为脚本级分岐。）",
    2: "`s01_14g`《五里霧中》三臂中走**臂 1** → `s01_14g1 → s01_14h → s01_17a → s01_18a`"
       "（京 END）→ `s01_19a`《解纜》。本线前半 `s01_01a–s01_05` 为与明日香线共用的鹰志线共通段。",
    3: "鹫介线 `s02` 主线；解缆后半自大路线 `s04_06k` 两臂中走**臂 2** → `s02_10a` 汇入本线"
       "（其后 s02 主链全文见本节章表），终至 `s02_16a`（日和子 END）→ `s02_17a`《解纜》。",
    4: "隼人线 `s03` 主线；`s03_08b` 两臂中走**臂 1** → `s03_08c1`（其后鸣线主链全文见本节章表）；"
       "解缆后半自大路线 `s04_06j1` 三臂中走**臂 1** → `s03_16a → s03_17a → s03_18a → s03_19a → "
       "s03_20a → s03_21a → s03_21b → s03_21c → s03_22a`（鸣 END）→ `s03_23a`《解纜》。",
    5: "`s04_05i` 两臂中走**臂 2**（带来救赎）→ `s04_06j2`（其后 s04 主链 45 章至 `s04_28b`，"
       "全文见本节章表）→ `s04_28b`（真·兄妹再会）→ `s04_29a`（解纜·真 END）；"
       "`s04_06j1` 三臂中走**臂 3** → `s04_06l`（s04 内部终点）。",
    6: "`s01_14g` 三臂中走**臂 2** → `s01_14g2`（`next=[]`，死路）；"
       "`s01_14i` 两臂中走**臂 2** → `s01_14j2`（`next=[]`，死路）。",
    7: "入口为本篇 `s03_08b`《ガード下の聖戦》两臂中走**臂 2** → `s03_08c2 → s03_09a2`"
       "（本篇侧）→ **跨源** `s03c_01a`（R 版亚衣线）。",
    8: "PSV 版自有链：`M01_01`《承前》→（M01–M09 主链，全文见本节章表）→ `M09_01`（美咲 END）→ `M09_02`《解纜》；"
       "AfterStory 侧由 `21_*` 承接后日谈，无跨源分岐。",
    9: "AfterStory 自有链：`14_1a`《再会》→（14_1a–14_8a 主链，全文见本节章表）→ `14_8a`《閉幕》，无跨源分岐。",
    10: "`24_1a` →（24_1a–24_4e 主链，全文见本节章表）→ `24_4e` 两臂：走**臂 1** → `24_5a → 24_5b`（G-END）；"
        "走**臂 2** → `24_5c`（B-END）。**注**：`24_4e` 有 3 个选项但仅 2 臂，"
        "「选项↔臂」配对未确证，故只按臂表述。",
    11: "各番外篇章独立成链（22/23/31–34/41/42/50–54/61–64/sc_*），"
        "彼此无 `next` 分岐，按脚本链与 TSV 行序列出。",
    12: "`start_oretuba` 为菜单根（34 个选项、26 臂），各臂进入 `a01–a06` 子篇目；"
        "子篇目内部各自成链，`a06_b1–b4`／`a06_c0` 为并列结局。",
    13: "无分岐（p01 单链 4 章）。",
    14: "无分岐（p02 单链 5 章）。",
    15: "无分岐（p03 单链 4 章）。",
    16: "无分岐（p04 单链 5 章）。",
    17: "无分岐（buru01–04 剧场框架，无 next 边）。",
    18: "`02_*`／`03_*` 原型版各自单链；与本篇 s02/s03 高度重合，D15 判定不入主干。",
    19: "无剧情时序（引擎初始化／回想／制作人员／标题）。",
}


def gen07(rows, by, routes, groups, own):
    # 唯一归属映射：script -> group index
    gidx = {}
    for i, (w, label, seq) in enumerate(groups, 1):
        for s in seq:
            gidx[s] = i

    L = []
    W = L.append
    W("# 07 · 《我们没有翅膀——格雷塔迦露德与柳木原》各路线完整章节脉络")
    W("")
    W("> 模块：`ISSUE-20260920-17` ｜ 生成器：`资源组\\工具\\build_chapter_docs.py`（只读 `05_章节总表.tsv`，幂等）")
    W("> **行格式＝用户标准格式** `阶段-作品《章节标题》`；《》内取**中文标题**（与用户示例「序章～美空学院的人们～」一致），")
    W("> 原文日文标题以 `〔〕` 附注，两栏均逐字取自 `05_章节总表.tsv`。标题为空者照实写「（无标题）」。")
    W("> **顺序依据＝沿 `next[i]` 走该路线的分岐臂**（`next` 第 i 项记作「臂 i」；**「选项 i → `next[i]`」仅在选项数与")
    W("> `next` 项数相等的 32 章成立**，其余 18 章配对未确证，故一律按「臂」表述，不臆称「选第 N 项」）。")
    W("> 收敛分支的两臂相邻列出（分支点在前、汇合点在后）；不按 `章节作用` 硬切。")
    W("> **共享章节口径**：同一章被多条路线播放时，在每条路线中**均完整列出**并标 `〔共用〕`，不省略、不用省略号；")
    W("> 章节的**唯一归属**（712 章每章一次）见 `06_章节总表.md`。")
    W("")
    W("## 零、路线划分与章数总账")
    W("")
    W("| # | 路线 | 定位 | 脚本来源 | 列出章数 | 其中独占 | 其中共用 |")
    W("| ---: | --- | --- | --- | ---: | ---: | ---: |")

    # 计算共用：某章若在多条 07 路线中出现，则非「首条出现」者为共用
    seen = set()
    rows07 = []
    for rt in routes:
        seq = topo(by, rt["members"])
        rows07.append(seq)
    dup_total = 0
    for rt, seq in zip(routes, rows07):
        ex = sum(1 for s in seq if s not in seen)
        sh = len(seq) - ex
        dup_total += sh
        seen.update(seq)
        W("| %d | %s | %s | `%s` | %d | %d | %d |"
          % (rt["rid"], esc(rt["title"]), esc(rt["kind"]), rt["src"], len(seq), ex, sh))
    W("| — | **合计（列出行数）** | — | — | **%d** | **%d** | **%d** |"
      % (sum(len(s) for s in rows07), len(seen), dup_total))
    W("")
    W("- **去重后唯一章节数 = %d**（＝ `05_章节总表.tsv` 的 712 行，无遗漏、无多余）。" % len(seen))
    W("- **列出行数 = %d**（＝ 712 ＋ %d 条共用重复；重复全部来自 (2)山科京 与 (1)渡来明日香 共用的鹰志线共通段）。"
      % (sum(len(s) for s in rows07), dup_total))
    W("- 712 章的唯一归属（每章一次）见 `06_章节总表.md`；本文件是「播放路径」视图。")
    W("")
    W("### 0.1 分岐点 × 臂 一览（`next` 第 i 项＝臂 i）")
    W("")
    W("**「选项 i → `next[i]`」的配对可信度**：仅当该章**选项数 = `next` 项数**时成立——")
    W("50 个含选项章节中 **32 章**满足（如 `s01_02c` 2 选项 2 臂、`s01_09c0` 3 选项 3 臂、`s02_10c` 3 选项 3 臂），")
    W("另 **18 章不满足**（`24_1b`–`24_5a` 系列 3 选项 1 臂、`24_4e` 3 选项 2 臂、`11_3d0` 4 选项 3 臂、")
    W("`12_4c0` 3 选项 2 臂、`s01_12b`／`s01_13b` 2 选项 3 臂、`start_oretuba` 34 选项 26 臂）。")
    W("故本表一律以「臂」表述；**未确证处不臆称「选第 N 项」**。分岐点若无选项文本，则为脚本级分岐（由前置 flag 决定）。")
    W("")
    W("| 分岐点 | 该章选项数 | 选项文本（中文） | 走的臂 | 该臂入口 | 该臂走向 | 归属路线 |")
    W("| --- | ---: | --- | ---: | --- | --- | --- |")
    CHOICE = [
        ("s01_14g", 0, "（无选项文本，脚本级分岐）", 1, "`s01_14g1`",
         "`s01_14g1 → s01_14h → s01_17a → s01_18a`（京 END）→ `s01_19a`", "(2)山科京"),
        ("s01_14g", 0, "（无选项文本，脚本级分岐）", 2, "`s01_14g2`", "死路（`next=[]`）", "(6)鹰志线 Bad End 支"),
        ("s01_14g", 0, "（无选项文本，脚本级分岐）", 3, "`s01_14i`",
         "`s01_14i → s01_14j1 → s01_14k → s01_14l → s01_15a → s01_15b → s01_16a`（明日香 END）", "(1)渡来明日香"),
        ("s01_14i", 0, "（无选项文本，脚本级分岐）", 1, "`s01_14j1`",
         "`s01_14j1 → s01_14k → s01_14l → s01_15a → s01_15b → s01_16a`", "(1)渡来明日香"),
        ("s01_14i", 0, "（无选项文本，脚本级分岐）", 2, "`s01_14j2`", "死路（`next=[]`）", "(6)鹰志线 Bad End 支"),
        ("s03_08b", 0, "（无选项文本，脚本级分岐）", 1, "`s03_08c1`",
         "`s03_08c1` → `s03_09a1` → `s03_09b` → （鸣线主链，全文见 (4) 章表）→ `s03_22a`", "(4)凤鸣"),
        ("s03_08b", 0, "（无选项文本，脚本级分岐）", 2, "`s03_08c2`",
         "`s03_08c2` → `s03_09a2` → **跨源** `s03c_01a`（R 版亚衣线）", "(7)香田亚衣"),
        ("s04_05i", 2, "不带来救赎 / 带来救赎", 1, "`s04_06j1`", "`s04_06j1` → `s04_06k` → `s01_05a` / `s02_10a`", "(1)(3)"),
        ("s04_05i", 2, "不带来救赎 / 带来救赎", 2, "`s04_06j2`",
         "`s04_06j2` → `s04_07a` → （s04 主链 45 章，全文见 (5) 章表）→ `s04_28b` → `s04_29a`（真 END）", "(5)大路线（真相）"),
        ("s04_06j1", 0, "（无选项文本，脚本级分岐）", 1, "`s03_16a`",
         "`s03_16a` → `s03_17a` → `s03_18a` → `s03_19a` → `s03_20a` → `s03_21a` → `s03_21b` → `s03_21c` → `s03_22a`（鸣解缆）", "(4)凤鸣"),
        ("s04_06j1", 0, "（无选项文本，脚本级分岐）", 2, "`s04_06k`", "`s04_06k` → `s01_05a` / `s02_10a`", "(1)(3)"),
        ("s04_06j1", 0, "（无选项文本，脚本级分岐）", 3, "`s04_06l`", "终点（`next=[]`）", "(5)大路线（真相）"),
        ("s04_06k", 0, "（无选项文本，脚本级分岐）", 1, "`s01_05a`",
         "`s01_05a` → `s01_05b` → `s01_06a` → （s01 主链，全文见 (1) 章表）→ `s01_16a`", "(1)渡来明日香"),
        ("s04_06k", 0, "（无选项文本，脚本级分岐）", 2, "`s02_10a`",
         "`s02_10a` → `s02_10b` → `s02_10c` → （s02 主链，全文见 (3) 章表）→ `s02_16a`", "(3)玉泉日和子"),
        ("ota_24_4e", 3, "隼人 / 迦楼罗 / 小鹰志", 1, "`24_5a`", "`24_5a → 24_5b`（G-END）", "(10)最终统合线"),
        ("ota_24_4e", 3, "隼人 / 迦楼罗 / 小鹰志", 2, "`24_5c`", "`24_5c`（B-END，终点）", "(10)最终统合线"),
    ]
    for a, n, b, c, entry, dest, e in CHOICE:
        W("| `%s` | %d | %s | %d | %s | %s | %s |" % (a, n, esc(b), c, entry, esc(dest), e))
    W("")
    W("---")
    W("")

    seen = set()
    for rt, seq in zip(routes, rows07):
        W("## (%d)%s" % (rt["rid"], rt["title"]))
        W("")
        W("- **定位**：%s" % rt["note"])
        W("- **脚本来源**：`%s` ｜ 列出 **%d** 章（独占 %d，共用 %d）"
          % (rt["src"], len(seq), sum(1 for s in seq if s not in seen), sum(1 for s in seq if s in seen)))
        W("- **选择支路径（本线走的臂）**：%s" % ROUTE_PATH.get(rt["rid"], "待判定"))
        W("")
        W("```")
        for s in seq:
            tag = "〔共用〕" if s in seen else ""
            W(line_of(by[s]) + tag)
        W("```")
        seen.update(seq)
        # 收束
        ends = [s for s in seq if by[s]["next_kind"] == "end" or (by[s]["章节作用"] or "").startswith("结局")]
        W("")
        W("- **收束**：" + ("；".join(
            "%s（`%s`，%s）" % (line_of(by[s]), s, (by[s]["章节作用"] or "结局"))
            for s in ends[:6]) or "（本线无显式结局章，为资料/系统分组）"))
        W("")
    return "\n".join(L) + "\n", rows07


# ─────────────────────── main ───────────────────────

def main():
    rows, by = load()
    for r in rows:
        r["_sid"] = r["源代号"] + "_" + r["script"]
    routes = build_routes(rows, by)

    md06, groups, own = gen06(rows, by, routes)
    md07, rows07 = gen07(rows, by, routes, groups, own)

    with io.open(OUT06, "w", encoding="utf-8", newline="\n") as f:
        f.write(md06)
    with io.open(OUT07, "w", encoding="utf-8", newline="\n") as f:
        f.write(md07)

    # 汇总
    uniq = set()
    for seq in rows07:
        uniq.update(seq)
    print("06 rows(unique) =", sum(len(g[2]) for g in groups))
    print("07 listed lines =", sum(len(s) for s in rows07), " unique =", len(uniq))
    print("routes =", len(routes))
    print("written:", OUT06)
    print("written:", OUT07)


if __name__ == "__main__":
    main()