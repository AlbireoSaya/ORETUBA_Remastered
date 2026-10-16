#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""emit_delivery_manifest.py —— UI 组**交付包校验收据**生成器 / 闸门。

产物：`UI组\交付包校验收据.md`（**脚本产物，禁止手改表中数值**）。

为什么需要它：交付面散落在 `krkr\assets\ui\`（1359 件素材）、`krkr\assets\face\`（不入库、可再生）、
17 屏 JSON、三处同源产物、`krkr\game\*.tjs`、插件 dll、生成器脚本……编程组拿到的**副本**若少一件、
旧一版，光看目录结构看不出来。**本文件是「给人核对副本完整性的单一表」**：一张表列出每一类东西的
**路径 / 件数 / 字节 / md5（或 sha256）**，并把口径（每个数字怎么算、排除了什么）写在旁注。

**已验证的口径副本必须有闸门盯着**（本工程既有通例）：本收据里的数字全部**从盘上机算**（源码里
没有任何一个被硬编码的件数/字节/md5），并配 `--check`：

  python 工具/emit_delivery_manifest.py            # 重算并写盘（生成）
  python 工具/emit_delivery_manifest.py --check    # 重算并与盘上该 md **逐格比对**；不一致 ⇒ 非 0 退出并指名差异
  python 工具/emit_delivery_manifest.py --report   # 只把会写盘的内容打到 stdout（不写盘）
  python 工具/emit_delivery_manifest.py --selfcheck# 变异自证：改坏一格必须被 --check 抓到（证明它真在校验）

★ **维护规则（必读，踩过一次）**：收据里记录了**被覆盖文件的整文件 md5**（`layout\_schema.md`、`_root.json`、
`palette.json`、`screens\_index.json`、`复刻\replica.js`、16 个 `krkr\game\*.tjs`、三个生成器/闸门脚本）。
**只要改了其中任何一个**（哪怕只改一句注释/散文），**必须重跑一次无参 `emit_delivery_manifest.py` 生成**，
否则 `--check`（已接进 `run_all.py` 末步）会红 —— 这不是缺陷，是「副本会被改旧」的真实信号。
（本条适用于**所有**改动，包括文档措辞：`_schema.md` 改了 1 个字符，收据里的字节数就会差。）

★ **`--check` 已接进一键套件**：`_工作\ISSUE-20260928-02_第2步\复现脚本\run_all.py` 的末步即它
  （排在「还原交付样例」之后 ⇒ 校验的是**交付态**，不被中间态污染）。

比对范围：只比对 md 里被 `<!-- GATE:<name> -->` … `<!-- /GATE:<name> -->` 包住的表
（**表外**的标题、生成时间、口径散文、附录都不参与比对；生成时间每次都会变，故有意留在闸门之外）。

口径来源（**复用而非自创**）：
  · 素材族划分、逐屏元素数、三处产物 md5、扫描/md5 工具 —— 一律复用 `工具\test_delivery_index_sync.py`
    （与《UI组_交付总纲.md》§2.1/§2.2/§2.3/§3.2 同源的**唯一**机算口径）。
  · flowchart 五组金标 md5 —— 从 `工具\gen_flow_layout.py` 的 `GOLDEN` 字面量解析（不另抄一份）。
  · 动作计数 —— 从 `layout\screens\*.json` 的 `action`/`actions[]` 实例出发，分类判据取自
    `layout\_schema.md` 的**登记状态标注**（见收据 §⑧ 的口径行）。
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # …\UI组\工具
UI = os.path.dirname(HERE)                                  # …\UI组

# ── 复用《交付总纲》的数字闸门：族划分 / 扫描 / md5 / markdown 表解析（口径唯一来源）──
sys.path.insert(0, HERE)
import test_delivery_index_sync as sync                      # noqa: E402

OUT_MD = os.path.join(UI, "交付包校验收据.md")

GEN_FLOW = os.path.join(HERE, "gen_flow_layout.py")
RUN_ALL = os.path.join(UI, "_工作", "ISSUE-20260928-02_第2步", "复现脚本", "run_all.py")
PLUGIN_DIR = os.path.join(UI, "krkr", "plugin")
PLUGIN_DLL = os.path.join(PLUGIN_DIR, "layerExDraw.dll")
PLUGIN_LIC = os.path.join(PLUGIN_DIR, "license_layerExDraw.txt")
SCREENS_DIR = os.path.join(UI, "layout", "screens")
GAME_DIR = os.path.join(UI, "krkr", "game")

# ⑥ 手写关键文件（**逐条列全**；`krkr\game\*.tjs` 用 glob 全收，见 build_files）
HANDWRITTEN = [
    os.path.join(UI, "layout", "_schema.md"),
    os.path.join(UI, "layout", "_root.json"),
    os.path.join(UI, "layout", "palette.json"),
    os.path.join(UI, "layout", "screens", "_index.json"),
    os.path.join(UI, "复刻", "replica.js"),
    os.path.join(HERE, "gen_layout.py"),
    os.path.join(HERE, "gen_flow_layout.py"),
    os.path.join(HERE, "verify_ui.py"),
]

# ⑧ A/B/C 分类判据（在 `layout\_schema.md` 里逐名找「定义行」，按行内标注判类）。
#    ★ 优先级：先看 A 标注（两端已实现）—— 一条目文里既写「两端已实现」又写「（简介取数）留编程组」时，
#      留编程组说的是**数据侧**、不是这个动作，故 A 优先，避免误判（如 `flow_intro_open`）。
A_MARK = ("两端本批已实现", "两端均已实现", "两端实现", "两端已实现")
C_MARK = ("拟用名", "派发即止", "两端均无分支", "留编程组", "无触发路径", "无数据落点")
B_MARK = ("接口冻结/占位", "占位")

# ★★ 覆写表（**启发式判类的已知例外**）——出处：《UI组_交付总纲.md》**§4.2「未接线清单」**
#   （那张表逐条写明「两端均无分支 / 派发即止」）。而 `layout\_schema.md` 的**定义行没有**相应标注
#   （它只写「两键必须有可区分的返回值」之类的机制口径）⇒ 启发式会把它们当「契约登记即默认 A」。
#   **必须覆写为 C**：编程组若按启发式结果读表，会以为确认框已经可用（实际两端均无分支）。
#   维护规则：以后凡 §4.2 明列「两端均无分支/派发即止」而 `_schema.md` 未标注者，在此逐条登记；
#             新增条目**必须带出处注释**（哪一行、原文怎么写的）。
OVERRIDE = {
    # §4.2 第 2 行：「`confirm_yes` / `confirm_no`（确认框） | 两端均无分支」
    "confirm_yes": ("C", "§4.2 明列两端无分支（覆写启发式判类）"),
    "confirm_no": ("C", "§4.2 明列两端无分支（覆写启发式判类）"),
}
# 逐条复核过、**与 §4.2 一致故无需覆写**的名（留档说明，防止日后误以为漏核）：
#   · §4.2 第 1 行 `flow_mode_main`/`flow_mode_frag` ⇒ 启发式已判 C（`拟用名`）。
#   · §4.2 第 3 行 BGM 8 枚（4 档模式 + 4 走带键）（`bgm_mode_none|one|all|rnd`/`bgm_prev`/`bgm_playpause`/`bgm_stop`/`bgm_next`，
#     共 8 名）⇒ 启发式已判 C（`_schema.md` 该条目写「拟用名」）。
#   · §4.2 第 4 行 `replay_play:<行>` ⇒ 启发式已判 C（`派发即止`）。
#   · §4.2 第 6 行说的是 `flow_replay_toggle` 的**画面播放本身**留编程组，动作本身两端已实现
#     （`_schema.md` 写「两端均已实现」）⇒ 判 A 正确，**不覆写**。
#   · §4.2 第 7 行的占位三族（`slot_*`/`page_*`/`bgm_play`）⇒ 本表按「占位族」**单列、不计入 A/B/C**
#     （与 §4.2 把「45 处」单列、不并入其 C 类 13 个同口径）。
OVERRIDE_REVIEWED_OK = (
    "flow_mode_main", "flow_mode_frag",
    "bgm_mode_none", "bgm_mode_one", "bgm_mode_all", "bgm_mode_rnd",
    "bgm_prev", "bgm_playpause", "bgm_stop", "bgm_next",
    "replay_play", "flow_replay_toggle",
)


# ── 小工具 ──────────────────────────────────────────────────────────────────
def fmt(n):
    return format(int(n), ",")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def size_norm(path):
    r"""**LF 规范化字节数**（与 `sync.md5_of` 同口径；理由见该函数 docstring）。

    ⚠ 本函数只用于**文本文件**行；二进制件（如 `layerExDraw.dll`）仍用原始 `os.path.getsize`。
    """
    with open(path, "rb") as fh:
        return len(fh.read().replace(b"\r\n", b"\n"))


def sha256_norm(path):
    r"""文本文件的 sha256（LF 规范化，与 `size_norm` 同口径）。"""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


# ── 各节机算 ────────────────────────────────────────────────────────────────
def build_families():
    r"""① `krkr\assets\ui\` 按族件数/字节（族划分复用 sync.FAMILIES，与总纲 §2.1 同源）。"""
    rows, cnt, total, orphans = sync.disk_families()
    use_of = {f[0]: f[2] for f in sync.FAMILIES}
    out = [[lab, fmt(c), fmt(b), use_of.get(lab, "—")] for lab, c, b in rows]
    out.append(["合计", fmt(cnt), fmt(total), "—"])
    out.append(["未归类（应 0）", fmt(len(orphans)), "—", "—"])
    return out, orphans


def build_face():
    r"""② `krkr\assets\face\`（**不入库、可再生**；副本可能合法缺失 ⇒ 缺失时记「—」并由 --check 放行）。"""
    present = os.path.isdir(sync.FACE)
    if not present:
        return [["件数", "—（未随副本分发）"], ["字节", "—（未随副本分发）"]], False
    cnt, total, _names = sync.scan_tree(sync.FACE)
    return [["件数", fmt(cnt)], ["字节", fmt(total)]], True


def build_screens():
    r"""③ 17 屏逐屏元素数（读 `layout\screens\*.json`，排除 `_index.json`）；复用 sync.disk_screens。"""
    rows, total = sync.disk_screens()
    out = [[sid, fn, fmt(n)] for sid, fn, n in rows]
    out.append(["合计", "—", fmt(total)])
    return out, len(rows)


def build_products():
    r"""④ 三处同源产物 md5（复用 sync.PRODUCTS ⇒ 与总纲 §2.3 同源口径）。"""
    return [[rel, sync.md5_of(path)] for rel, path in sync.PRODUCTS]


def parse_golden():
    r"""从 `工具\gen_flow_layout.py` 解析 `GOLDEN`（五组）与 `DEFAULT_OUT`（交付样例文件）。"""
    src = read_text(GEN_FLOW)
    m = re.search(r"^GOLDEN = \{(.*?)^\}", src, re.S | re.M)
    if not m:
        raise RuntimeError("在 %s 里找不到 GOLDEN 字面量块（改名了？请同改本闸门）" % GEN_FLOW)
    pairs = re.findall(r'"(\w+)":\s*\("([0-9a-f]{32})",\s*"([0-9a-f]{64})"\)', m.group(1))
    if not pairs:
        raise RuntimeError("GOLDEN 块里没解析到任何 (md5, sha256) 对：%s" % GEN_FLOW)
    order = re.search(r"^GOLDEN_ORDER = \(([^)]*)\)", src, re.M)
    names = re.findall(r'"(\w+)"', order.group(1)) if order else [p[0] for p in pairs]
    ordered = [(n, dict((p[0], p[1:]) for p in pairs)[n]) for n in names]
    m2 = re.search(r'^DEFAULT_OUT = os\.path\.join\(SCREENS, "([^"]+)"\)', src, re.M)
    if not m2:
        raise RuntimeError("在 %s 里找不到 DEFAULT_OUT（改名了？请同改本闸门）" % GEN_FLOW)
    return ordered, m2.group(1)


def build_golden():
    """⑤ flowchart 五组金标 md5 ＋ 盘上交付样例比对（交付样例＝DEFAULT_OUT 指向的屏文件）。"""
    ordered, sample_fn = parse_golden()
    sample_path = os.path.join(SCREENS_DIR, sample_fn)
    sample_md5 = sync.md5_of(sample_path)
    out = []
    for name, (g_md5, g_sha) in ordered:
        if name == "screen1":
            ok = "是" if sample_md5 == g_md5 else "否"
            out.append([name, g_md5, sample_md5, ok, g_sha])
        else:
            out.append([name, g_md5, "—（非持久化预设）", "—", g_sha])
    return out, sample_fn


def build_files():
    r"""⑥ 手写关键文件 md5（含 16 个 `krkr\game\*.tjs`）。"""
    tjs = sorted(os.path.join(GAME_DIR, f) for f in os.listdir(GAME_DIR)
                 if f.endswith(".tjs"))
    paths = list(HANDWRITTEN) + tjs
    out = []
    for p in paths:
        rel = os.path.relpath(p, UI).replace("\\", "/")
        out.append([rel, fmt(size_norm(p)), sync.md5_of(p)])   # ★ 字节与 md5 同取 LF 规范化口径
    return out, len(tjs)


def build_plugin():
    """⑦ 插件 sha256 ＋ 许可文件（含 sha256）。"""
    out = [
        ["layerExDraw.dll · 字节（二进制，原始）", fmt(os.path.getsize(PLUGIN_DLL))],
        ["layerExDraw.dll · sha256", sha256_of(PLUGIN_DLL)],
        ["license_layerExDraw.txt", "存在"],
        ["license_layerExDraw.txt · sha256（LF 规范化）", sha256_norm(PLUGIN_LIC)],
    ]
    return out


def family_of(action):
    """动作名归并到「族名」：`slot_1`→`slot_*`、`config_char_aki`→`config_char_*`、剥掉 `:<行>` 参数。"""
    n = action.split(":")[0]
    m = re.match(r"^(slot|page)_\d+$", n)
    if m:
        return m.group(1) + "_*"
    m = re.match(r"^(config_char|config_set|config_tab|gallery_tab)_\w+$", n)
    if m:
        return m.group(1) + "_*"
    return n


def collect_actions():
    r"""从 `layout\screens\*.json` 收集全部 action 实例（`action` 字段 + `actions[]`）。"""
    hits = []

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "action" and isinstance(v, str):
                    hits.append(v)
                elif k == "actions" and isinstance(v, list):
                    hits.extend(x for x in v if isinstance(x, str))
                else:
                    walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)

    for fn in sorted(os.listdir(SCREENS_DIR)):
        if not fn.endswith(".json") or fn == "_index.json":
            continue
        with open(os.path.join(SCREENS_DIR, fn), encoding="utf-8") as fh:
            walk(json.load(fh))
    return hits


def classify_actions():
    r"""按 `layout\_schema.md` 的**定义行**标注，给每个（族归并后的）动作名判 A/B/C。

    判据（原样写进收据 §⑧ 的口径行，供人复核）：
      1. **定义行**的取法（按优先级）：
         a) 表格行的**第一格**里出现「反引号包住的该名、名后不是 `[a-z0-9_]`」的行；
         b) 第一格里出现该名的**族形**（取名字首个 `_` 之前的部分 + `*`，如 `bgm_playpause`→`bgm_*`）的行；
         c) 兜底：文档里**首次**出现该名（反引号内、词边界）的行。
         ⇒ 优先「定义行」而非「被别处交叉引用的行」（`bgm_playpause` 只在 `flow_replay_toggle` 条目里
            被顺带提到，若不区分就会误判成 A）。
      2. 判类（定义行内含标注词即命中，**实现优先**）：
         · 含 `两端已实现` 类词 ⇒ **A**
         · 含 `拟用名 / 派发即止 / 留编程组 / 无分支` ⇒ **C**
         · 含 `占位 / 接口冻结` ⇒ **B**
         · 无任何标注 ⇒ **A**（契约登记即默认两端已实现）
      3. `slot_*` / `page_*` / `bgm_play` 是任务书点名的**占位动作**（进「未实现的动作」回落）⇒ **占位族**。
      4. 文档里找不到定义行者 ⇒ `未登记`（单列，**不并入 A**）。
      5. ★ **启发式不是结论**：凡《UI组_交付总纲.md》§4.2 明列「两端均无分支/派发即止」而上面判成 A 者，
         一律按 `OVERRIDE` 表**覆写为 C**，并把「改前 → 改后」逐条记进返回值 `diffs`。
         返回值 = (names, cls, diffs)。
    """
    txt = read_text(os.path.join(UI, "layout", "_schema.md"))
    lines = txt.split("\n")
    names = sorted({family_of(h) for h in collect_actions() if h})

    def first_cell(line):
        s = line.strip()
        if not s.startswith("|"):
            return ""
        return s.strip("|").split("|")[0]

    def exact_pat(n):
        return re.compile(r"`[^`]*" + re.escape(n) + r"(?![a-z0-9_])")

    def fam_pat(n):
        base = n.split("_", 1)[0] + "_"
        return re.compile(re.escape(base) + r"\*")

    def find_line(n):
        if n.endswith("_*"):
            base = n[:-1]
            strong = re.compile(re.escape(base) + r"(?=[<*:|`\s0-9])")
        else:
            strong = None
        weak = re.compile(r"`[^`]*" + re.escape(n[:-1] if n.endswith("_*") else n) + r"(?![a-z0-9_])")
        for l in lines:
            if strong is not None and strong.search(l):
                return l
            if strong is None and exact_pat(n).search(first_cell(l)):
                return l
        if not n.endswith("_*"):
            fp = fam_pat(n)
            for l in lines:
                if fp.search(first_cell(l)):
                    return l
        for l in lines:
            if weak.search(l):
                return l
        return None

    def expand_same_as(line):
        """含义列写「同上」的条目（如 `backlog_replay`）⇒ 把**上一行**的标注并进来一起判。"""
        if line is None or "同上" not in line:
            return line
        i = lines.index(line)
        return (lines[i - 1] + "\n" + line) if i > 0 else line

    cls = {}
    for n in names:
        if re.match(r"^(slot|page)_\*$|^bgm_play$", n):
            cls[n] = ("占位", "占位动作（无分支，进「未实现的动作」回落；单列，不计入 A/B/C）")
            continue
        line = find_line(n)
        if line is None:
            cls[n] = ("未登记", "契约无定义行")
            continue
        line = expand_same_as(line)
        if any(m in line for m in A_MARK):
            cls[n] = ("A", next(m for m in A_MARK if m in line))
        elif any(m in line for m in C_MARK):
            cls[n] = ("C", next(m for m in C_MARK if m in line))
        elif any(m in line for m in B_MARK):
            cls[n] = ("B", next(m for m in B_MARK if m in line))
        else:
            cls[n] = ("A", "契约登记即默认两端已实现")

    # ★ 覆写（已知例外）＋ 逐条差异留档
    diffs = []
    for n, (k, why) in OVERRIDE.items():
        if n not in cls:
            continue
        before = cls[n][0]
        if before != k:
            diffs.append((n, before, k, why))
            cls[n] = (k, why)
    return names, cls, diffs


def build_actions():
    """⑧ 动作计数（实例数 / 占位处数 grep / A/B/C 三类）。"""
    hits = collect_actions()
    nonempty = [h for h in hits if h]
    named = [family_of(h) for h in nonempty]
    n_before = len({h.split(":")[0] for h in nonempty})
    n_after = len(set(named))

    def cnt(pred):
        return sum(1 for h in nonempty if pred(h))

    slot = cnt(lambda h: re.match(r"^slot_\d+$", h) is not None)
    page = cnt(lambda h: re.match(r"^page_\d+$", h) is not None)
    bgm_play = cnt(lambda h: h.startswith("bgm_play:"))
    replay_play = cnt(lambda h: h.startswith("replay_play:"))
    backlog_jump = cnt(lambda h: h.startswith("backlog_jump:"))
    backlog_replay = cnt(lambda h: h.startswith("backlog_replay:"))

    _names, cls, diffs = classify_actions()
    order = ("A", "B", "C", "占位", "未登记")
    tally = {k: 0 for k in order}
    for _n, (k, _why) in cls.items():
        tally[k] = tally.get(k, 0) + 1

    rows = [
        ["动作实例总数（含空串）", fmt(len(hits))],
        ["空 action 实例（`\"\"`，允许空/吞点击）", fmt(len(hits) - len(nonempty))],
        ["非空 action 实例", fmt(len(nonempty))],
        ["去重动作名（族归并前）", fmt(n_before)],
        ["去重动作名（族归并后）", fmt(n_after)],
        ["占位 · `slot_1`…`slot_12`", fmt(slot)],
        ["占位 · `page_1`…`page_10`", fmt(page)],
        ["占位 · `bgm_play:%row%`", fmt(bgm_play)],
        ["占位小计（§4.2 口径：slot+page+bgm_play）", fmt(slot + page + bgm_play)],
        ["占位 · `replay_play:<行>`（派发即止）", fmt(replay_play)],
        ["占位 · `backlog_jump:%row%`（接口冻结/占位）", fmt(backlog_jump)],
        ["占位 · `backlog_replay:%row%`（接口冻结/占位）", fmt(backlog_replay)],
        ["A 类（启发式：契约登记且未被标注/覆写；含明写「两端已实现」）", fmt(tally["A"])],
        ["B 类（明写「占位/接口冻结」）", fmt(tally["B"])],
        ["C 类（明写「拟用名/派发即止/留编程组」，**含 §4.2 覆写项**）", fmt(tally["C"])],
        ["占位族（`slot_*`/`page_*`/`bgm_play`，**单列、不计入 A/B/C**）", fmt(tally["占位"])],
        ["未登记（数据用了、契约无定义行）", fmt(tally["未登记"])],
        ["★ 被 §4.2 覆写的动作名数（启发式判 A → 覆写 C）", fmt(len(diffs))],
    ]
    detail = [[n, cls[n][0], cls[n][1]] for n in sorted(cls)]
    diff_rows = [[n, before, after, why] for n, before, after, why in sorted(diffs)]
    return rows, detail, diff_rows


def count_run_all_steps():
    """⑨ 套件步骤数：加载 run_all.py 读它自报的 `len(STEPS)`（其启动行打印的就是这个数）。"""
    if not os.path.isfile(RUN_ALL):
        raise RuntimeError("套件脚本不存在：%s" % RUN_ALL)
    spec = importlib.util.spec_from_file_location("_manifest_probe_run_all", RUN_ALL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                       # 只建 STEPS 列表，不跑任何步骤
    static = len(re.findall(r"^step\(", read_text(RUN_ALL), re.M))
    return len(mod.STEPS), static, os.path.relpath(RUN_ALL, UI).replace("\\", "/")


# ── 组装 / 渲染 ─────────────────────────────────────────────────────────────
def build(mutate=None):
    """机算全部节，返回 (sections, notes)。mutate=(sid,row,col,fn) 供变异自证。"""
    notes = []
    sections = []

    fam, orphans = build_families()
    if orphans:
        notes.append("!! 素材族「未归类」件数 = %d（族划分漏登记）：%s" % (len(orphans), orphans[:8]))
    sections.append(dict(
        id="manifest_families", title="① 素材集 `krkr\\assets\\ui\\`（按族）",
        header=["族", "件数", "字节", "用途"], rows=fam,
        note="口径：`os.walk` 全树 → 按**文件名前缀**归族（族划分＝`工具\\test_delivery_index_sync.py` 的 "
             "`FAMILIES`，与《UI组_交付总纲.md》§2.1 同源）；`合计`＝目录内全部文件；"
             "`未归类` 必须为 0（否则说明新增了前缀族却没登记）。"))

    face, face_present = build_face()
    notes.append("face/ 目录%s（**不入库、可再生**：`.gitignore` 排除 `…/UI组/krkr/assets/face/*.png`；"
                 "再生见 `头像素材清单.md`）。" % ("在" if face_present else "不在（副本合法缺失，--check 放行）"))
    sections.append(dict(
        id="manifest_face", title="② 对话框头像集 `krkr\\assets\\face\\`（**不入库、可再生**）",
        header=["项", "值"], rows=face, optional=not face_present,
        note="口径：`os.walk` 计数；**该目录不入库**（根 `.gitignore` 排除 `…/UI组/krkr/assets/face/*.png`）"
             "⇒ 克隆/副本里可能没有，`--check` 遇缺失**放行并提示**，不算副本不完整。"))

    scr, n_scr = build_screens()
    sections.append(dict(
        id="manifest_screens", title="③ 屏与叠层（17 屏）逐屏元素数",
        header=["屏 id", "文件", "件数"], rows=scr,
        note="口径：读 `layout\\screens\\*.json`，`件数 = len(elements)`，**排除 `_index.json`**；"
             "复用 `test_delivery_index_sync.py::disk_screens`（与总纲 §3.2 同源）。"))

    sections.append(dict(
        id="manifest_products", title="④ 三处同源产物 md5",
        header=["产物", "md5"], rows=build_products(),
        note="口径：复用 `test_delivery_index_sync.py::PRODUCTS`（与总纲 §2.3 同源）；整文件 md5、小写十六进制。"))

    gold, sample_fn = build_golden()
    sections.append(dict(
        id="manifest_golden", title="⑤ flowchart 五组金标（`gen_flow_layout.py::GOLDEN`）与交付样例比对",
        header=["预设", "金标 md5", "交付样例盘上 md5", "一致", "金标 content-sha256"], rows=gold,
        note="口径：金标 md5 **从 `工具\\gen_flow_layout.py` 的 `GOLDEN` 字面量解析**（不另抄一份）；"
             "「交付样例盘上 md5」＝ `layout\\screens\\%s`（`DEFAULT_OUT`）实际 md5 —— "
             "五组里**只有 `screen1` 是持久化的交付样例**（其余四组是跑套件时才生成、跑完即被还原，"
             "属过程态、不成交付物），故只有它有一列盘上值可比。`content-sha256`＝剥掉 note 后的内容摘要，"
             "用于区分「只改了措辞」与「内容真变了」。" % sample_fn))

    files, n_tjs = build_files()
    if n_tjs != 16:
        notes.append("!! `krkr\\game\\*.tjs` 实测 %d 支（文档口径称 16 支）⇒ 请核对 §2.4。" % n_tjs)
    sections.append(dict(
        id="manifest_files", title="⑥ 手写关键文件 md5（含 `krkr\\game\\*.tjs` %d 支）" % n_tjs,
        header=["路径（相对 UI组/）", "字节", "md5"], rows=files,
        note="口径：`krkr\\game\\*.tjs` 用 `os.listdir` 全收（按名排序）；其余 8 条为显式清单"
             "（`layout\\_schema.md`/`_root.json`/`palette.json`/`screens\\_index.json`、`复刻\\replica.js`、"
             "`工具\\gen_layout.py`/`gen_flow_layout.py`/`verify_ui.py`）。整文件 md5。"))

    sections.append(dict(
        id="manifest_plugin", title="⑦ 插件 `krkr\\plugin\\layerExDraw.dll` 与许可",
        header=["项", "值"], rows=build_plugin(),
        note="口径：`sha256` 整文件（连接线与 `current` 环依赖该插件；**不在** `verify_ui` 体积预算内，"
             "但**必须随包分发**）。许可文本 `license_layerExDraw.txt` 必须存在。"))

    act, detail, diff_rows = build_actions()
    pre_actions = [
        "**判类口径（★ 启发式，可能与本总纲 §4.2 不同）**：A/B/C 由本脚本在 `layout\\_schema.md` 的"
        "**定义行**上机算 —— ① 在 §六 动作表**有登记**者**默认判 A**；② 定义行明写"
        "`拟用名`/`派发即止`/`留编程组` 者判 C、明写 `占位/接口冻结` 者判 B；"
        "③ `slot_*`/`page_*`/`bgm_play` 归「占位族」单列。",
        "★ **判 A ≠「两端真有分支」**：判 A 只说明「**契约动作表里有这个名字**」。"
        "本表口径是「表里有没有名」（**启发式**），《UI组_交付总纲.md》**§4.2** 的口径是"
        "「**两端是否真有分支**」（**契约枚举**）—— **两者不是同一件事**。",
        "⚠ **凡 §4.2 明列「两端均无分支 / 派发即止」而启发式判成 A 者，一律由生成器里的 `OVERRIDE` 表"
        "覆写为 C，并把「改前 → 改后 → 依据」逐条记在下面 §⑧·与 §4.2 的差异**；"
        "编程组**请以本表 + §4.2 共同为准**，不要只看 §⑧·明细 的判类列。",
    ]
    sections.append(dict(
        id="manifest_actions", title="⑧ 动作计数（数据实例 / 占位处数 / A·B·C 三类）",
        pre=pre_actions, header=["计数项", "值"], rows=act,
        note="口径：① 实例数＝`layout\\screens\\*.json` 里全部 `action` 字段与 `actions[]` 元素（含空串 `\"\"`）；"
             "② 去重名＝剥掉 `:<行号>`、族名归并（`slot_1`→`slot_*`、`config_char_*` 等）；"
             "③ 占位处数＝**按实际匹配计数**（正则 `^slot_\\d+$` 等），不是手写；"
             "④ A/B/C 判类＝在 `layout\\_schema.md` 找该名的「**定义行**」（优先表格第一格；"
             "避免被别处的交叉引用误导），按行内标注判定 —— `两端已实现`⇒A、`占位/接口冻结`⇒B、"
             "`拟用名/派发即止/留编程组`⇒C；**无标注者归 A**（登记即默认两端已实现）；"
             "含义列写「同上」的条目（如 `backlog_replay`）沿用上一行标注；"
             "`slot_*`/`page_*`/`bgm_play` 归「**占位族**」（单列、**不计入 A/B/C**）；"
             "文档里找不到定义行者归「未登记」（**单列，不并入 A**）；"
             "⑤ **A/B/C 计入的是覆写后的值**（差异见 §⑧·与 §4.2 的差异）。"
             "★ **本表只统计数据里实际引用到的动作名**（契约列举但数据未用的不计，"
             "如 `open_music`/`do_save`/`do_load`），故 A 数不等于 §3.4 的「契约枚举」口径。"
             "逐名结果见 §⑧·明细。"))
    sections.append(dict(
        id="manifest_actions_diff",
        title="⑧·与 §4.2 的差异（本次覆写清单）",
        header=["动作名", "启发式判类（改前）", "覆写后（改后）", "依据"], rows=diff_rows,
        note="口径：**这就是两种口径的分叉点**。判据出处＝《UI组_交付总纲.md》**§4.2「未接线清单」**"
             "（该表逐条写明「两端均无分支 / 派发即止」），而 `layout\\_schema.md` 的定义行**没有**相应标注"
             "⇒ 启发式会判成 A。生成器 `OVERRIDE` 表把 `confirm_yes`/`confirm_no` 覆写为 C"
             "（依据 §4.2 第 2 行）⇒ **A/B/C 合计已按覆写后计**。"
             "另逐条复核过、**与 §4.2 一致故不覆写**者：§4.2 第 1 行 `flow_mode_main`/`flow_mode_frag`、"
             "第 3 行 BGM 8 枚（4 档模式 `bgm_mode_none/one/all/rnd` ＋ 4 个走带键 `bgm_prev/playpause/stop/next`）、第 4 行 `replay_play:<行>`（启发式已判 C）；"
             "第 6 行说的是 `flow_replay_toggle` 的**画面播放本身**（动作本身两端已实现 ⇒ 判 A 正确）；"
             "第 7 行占位三族按「占位族」单列（与 §4.2 把「45 处」单列同口径）。"))
    sections.append(dict(
        id="manifest_actions_detail", title="⑧·明细 动作名逐名判类（按 §六 定义行标注）",
        header=["动作名（族归并后）", "判类", "判据"], rows=detail,
        note="口径：与 §⑧ 同一次机算的结果展开，供人逐名复核（判据列＝命中的标注词）。"))

    n_steps, static, suite_rel = count_run_all_steps()
    sections.append(dict(
        id="manifest_suite", title="⑨ 一键套件步骤数（`run_all.py` 启动行自报）",
        header=["项", "值"], rows=[
            ["套件步骤数（`len(STEPS)`，启动行打印的就是它）", fmt(n_steps)],
            ["`run_all.py` 里 `^step(` 静态出现次数", fmt(static)],
            ["套件脚本（相对 UI组/）", suite_rel],
        ],
        note="口径：加载 `run_all.py` 读它自报的 `len(STEPS)`（含 `for t in GATES` 循环展开的步）；"
             "静态 `step(` 行数与之不等属预期（循环展开）。**文档里不写死步数**——以本表为准。"))

    if mutate:
        sid, ri, ci, fn = mutate
        for s in sections:
            if s["id"] == sid:
                s["rows"][ri][ci] = fn(s["rows"][ri][ci])
    return sections, notes


def render(sections, notes):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L = []
    L.append("# UI 组交付包校验收据")
    L.append("")
    L.append("> **用途**：给人核对**副本完整性**的单一表。编程组拿到 UI 组交付副本后跑")
    L.append("> `python 工具/emit_delivery_manifest.py --check` —— 与本表**逐格比对**，"
             "不一致即非 0 退出并指名差异。")
    L.append("> **本文件是脚本产物**（`工具\\emit_delivery_manifest.py`）：**禁止手改表中数值**，"
             "改数据后重跑生成器。")
    L.append("> ★ 本文件的数字闸门**已接进一键套件**"
             "（`_工作\\ISSUE-20260928-02_第2步\\复现脚本\\run_all.py` 末步 `--check`）。")
    L.append("")
    L.append("- 生成时间：%s（本地时区；**不参与 --check 比对**）" % now)
    L.append("- 生成命令：`python 工具/emit_delivery_manifest.py`")
    L.append("- 工程根：`…\\我们没有翅膀——格雷塔迦露德与柳木原\\UI组`")
    L.append("- 法规：`--check` **只比对**被 `GATE:<名>` 注释包住的那些表；表外的散文/附录/时间戳不参与比对。")
    L.append("")
    if notes:
        L.append("**生成时的告警**：")
        for n in notes:
            L.append("- %s" % n)
        L.append("")
    for s in sections:
        L.append("## %s" % s["title"])
        L.append("")
        for line in s.get("pre", []):
            L.append(line)
            L.append("")
        L.append("<!-- GATE:%s -->" % s["id"])
        L.append("| " + " | ".join(s["header"]) + " |")
        L.append("|" + "|".join(["---"] * len(s["header"])) + "|")
        for row in s["rows"]:
            L.append("| " + " | ".join(str(c) for c in row) + " |")
        L.append("<!-- /GATE:%s -->" % s["id"])
        L.append("")
        L.append("- %s" % s["note"])
        L.append("")
    L.append("---")
    L.append("")
    L.append("## 怎么用")
    L.append("")
    L.append("1. **编程组拿到副本后**：`cd UI组 && python 工具/emit_delivery_manifest.py --check`")
    L.append("   —— 退出码 0 ⇒ 副本与本表逐格一致；非 0 ⇒ 逐条列出「哪一格、收据写什么、副本是什么」，"
             "按路径补齐/换新即可。")
    L.append("2. **UI 组改完数据/素材后**：`python 工具/emit_delivery_manifest.py` 重出本表，"
             "再跑 `--check` 自证；套件末尾那步会自动替你再跑一次。")
    L.append("3. **不要把本表当数据源**：它只是**校验副本**的对照表；真正的数据源永远是上面各节的「路径」列。")
    L.append("")
    return "\n".join(L)


# ── 解析 / 比对 ─────────────────────────────────────────────────────────────
def parse_md(text, ids):
    """把盘上收据解析成 {sid: rows}（复用总纲闸门的 block/data_rows，口径一致）。

    整张表缺失（被人删了/改坏了）时该项记 None，由 `compare` 报成「收据缺此表」（**不崩**）。
    """
    out = {}
    for sid in ids:
        try:
            out[sid] = sync.data_rows(sync.block(text, sid))
        except RuntimeError:
            out[sid] = None
    return out


def norm(v):
    return str(v).strip().strip("`").strip()


def compare(sections, parsed):
    """逐格比对；返回 (checks, bad, skipped)。"""
    checks, bad, skipped = [], [], []
    for s in sections:
        sid = s["id"]
        if s.get("optional"):
            skipped.append(sid)
            continue
        rows = parsed.get(sid)
        if rows is None:
            bad.append((sid, "（整表）", "收据缺此表", "（盘上无）"))
            continue
        if len(rows) != len(s["rows"]):
            bad.append((sid, "行数", len(rows), len(s["rows"])))
        for ri in range(min(len(rows), len(s["rows"]))):
            want, got = s["rows"][ri], rows[ri]
            label = norm(got[0]) if got else ("第 %d 行" % (ri + 1))
            for ci in range(max(len(want), len(got))):
                w = norm(want[ci]) if ci < len(want) else "（缺列）"
                g = norm(got[ci]) if ci < len(got) else "（缺列）"
                checks.append((sid, "%s · 第%d 列" % (label, ci + 1), g, w))
                if g != w:
                    bad.append((sid, "%s · 第%d 列" % (label, ci + 1), g, w))
    return checks, bad, skipped


# ── main ────────────────────────────────────────────────────────────────────
def main():
    argv = sys.argv[1:]

    if "--selfcheck" in argv:
        # 变异自证：把「① 素材族合计件数」改 +1，--check 必须抓到；不改则必须全绿。
        try:
            sections, _n = build()
        except Exception as exc:                              # noqa: BLE001
            print("环境错误：%s" % exc)
            return 2
        ids = [s["id"] for s in sections]
        # 找 ① 的「合计」行
        fam = next(s for s in sections if s["id"] == "manifest_families")
        ri = next(i for i, r in enumerate(fam["rows"]) if r[0] == "合计")
        mut, _n2 = build(mutate=("manifest_families", ri, 1, lambda v: str(int(v.replace(",", "")) + 1)))
        text = render(sections, [])
        _c, bad, _s = compare(mut, parse_md(text, ids))
        hit = [b for b in bad if b[0] == "manifest_families"]
        print("[selfcheck] 变异「① 素材族合计件数 +1」⇒ 不一致 %d 条（命中 ① %d 条）" % (len(bad), len(hit)))
        for b in hit:
            print("    FAIL %s · %s：收据写 %r ｜ 机算得 %r" % b)
        if not hit:
            return 1
        _c2, bad2, _s2 = compare(sections, parse_md(text, ids))
        print("[selfcheck] 未变异 ⇒ 不一致 %d 条（应为 0）" % len(bad2))
        return 0 if not bad2 else 1

    try:
        sections, notes = build()
    except Exception as exc:                                  # noqa: BLE001
        print("环境错误：%s" % exc)
        return 2

    body = render(sections, notes)

    if "--check" in argv:
        if not os.path.isfile(OUT_MD):
            print("环境错误：收据不存在，请先跑 `python 工具/emit_delivery_manifest.py` 生成：%s" % OUT_MD)
            return 2
        ids = [s["id"] for s in sections]
        parsed = parse_md(read_text(OUT_MD), ids)
        checks, bad, skipped = compare(sections, parsed)
        print("=== 交付包校验收据闸门（%d 项断言）===" % len(checks))
        for sid in skipped:
            print("  NOTE 跳过（副本可合法缺失）：%s" % sid)
        for sid, label, got, want in bad:
            print("  FAIL [%s] %s：收据写 %r ｜ 机算得 %r" % (sid, label, got, want))
        print("-" * 78)
        print("结果：%s（不一致 %d 项）" % ("**全部通过**" if not bad else "**失败**", len(bad)))
        return 0 if not bad else 1

    if "--report" in argv:
        sys.stdout.write(body)
        return 0

    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("已写出交付包校验收据：%s" % OUT_MD)
    for n in notes:
        print("  · %s" % n)
    for s in sections:
        print("  %-46s %d 行" % (s["title"], len(s["rows"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
