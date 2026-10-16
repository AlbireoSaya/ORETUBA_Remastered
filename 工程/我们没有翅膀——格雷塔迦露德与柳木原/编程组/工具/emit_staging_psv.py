# -*- coding: utf-8 -*-
"""emit_staging_psv.py —— PSV 明文 DSL → 逐场演出时间线（P1 取金标）

来源与依据
----------
- PSV 脚本：`工程\\我们没有翅膀PSV\\脚本解包\\`（498 份、Shift-JIS、无扩展名）
  结构 `[Section]{ :Key value }`，任务块 `[TaskN]{ :Tasktype "X" ... }`，立绘子块 `[CharaK]{...}`。
- 解析规则（**逐条实测**，见 `工程\\我们没有翅膀PSV\\美咲线资源与重构说明.md` §四 R1–R7）：
  R2 `:Texture N // NAME` / `置換しました<<NAME>>` —— **编号是场景内局部编号，必须按名解析**；
  R3 `:Number c,p,c,e,s // 置換しました<<ST_XXXX>>` —— 立绘贴图名；
  R4 `:SE/:BGM/:Voice N` —— PSV 归档内索引（`:BGM N` 的产件命名已由资源组确证为 `<源>_bgm{N:03d}`）；
  R7 `:Name N` —— 说话人显示名在 `adv.txt` 的 `[Name]` 表（本工具只用注释里的显示名做核对）。
- 我方语料：`资源组\\剧本\\scene_{ot,otv,otp}.jsonl`（`lines[].seq` 与 `lines[].jp`）。
- 素材三键：`资源组\\交接编程组\\素材库到统一名.tsv` → `交付路径`；`资源组\\美术统一_交付\\交付清单.tsv` 校验存在。
  立绘名 PSV 侧带 `st_` 前缀（`st_kaz01`），我方库为 `ot/chr/ot_kaz01.png` —— **两种键都登记**。

口径（禁止猜想）
----------------
- 未判读/未映射一律**留空并在 `note` 写明**，不编造。
- `msg_ord` = 该任务之前已出现的 `Message` 任务数（0-based）；`seq` = 对齐到语料 `lines[].seq` 的行号。
  对齐用 difflib 逐场比对正文（PSV 是审查版：个别词被和谐，另有 `<10>\\` 类控制码差异）——
  逐字相等率低的场**如实记入 `场景映射.tsv` 的 `align` 列**。

产物（`--out`，默认 `编程组\\PSV演出\\`）
----------------------------------------
- `时间线.tsv`     主表：每行一个演出事件（含层/参数/素材/时序/语料行）
- `场景映射.tsv`   PSV 文件 ↔ 我方 scene_id ↔ 对齐统计
- `对账_抽样.tsv`  抽样场的**逐任务原样行 ↔ 解析结果**并排（闸门证据）
- `_index.json`    汇总计数

用法
----
  python -X utf8 工具/emit_staging_psv.py --psv <PSV脚本解包> --res <资源组> --out <产出口>
  python -X utf8 工具/emit_staging_psv.py --check     # 幂等复核（盘面按 LF 归一后比；兼容 autocrlf 检出面）
"""
import argparse
import collections
import difflib
import io
import json
import os
import re
import sys

# ---------------------------------------------------------------- 路径默认值
DEFAULT_DATA_ROOT = r"E:\ZCode Workspace\Galgame"
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原")
PSV_REL = os.path.join("工程", "我们没有翅膀PSV", "脚本解包")

# 源 → 脚本文件名前缀
SRC_BY_PREFIX = {"S": "ot", "M": "otv", "P": "otp"}
SRC_ORDER = ["ot", "otv", "otp", "otr", "ota", "np"]

# ================================================================
# ★★ 层序（Priority）策略 —— 代码级声明（ISSUE-20261006-07 固化）
# ================================================================
# 铁律：**层序（Priority）唯一来源 = PSV 脚本的 `:Priority` 字段。**
#   · 依据 A（本工程实测）：PSV `:Priority` 值域恒为整数 1..10（全 498 份脚本
#     10,309 处 `:Priority`，无 0、无小数、无越域值）——见 `层序策略\说明.md`。
#   · 依据 B（R3 独立复核，`子代理工作区\ISSUE-20261006-07\R3\复核_R3_参数层与层序否定.md` §2.6/§2.8）：
#     **PC 侧无任何显式层序携带者**——`[8][v]`、装载序、命令节点 `k` 字段、`maps[0]`
#     四条候选通路穷尽否定（`ot` 413 个 `.sob` 里 `grep -i priority` = 0）；
#     唯一隐式候选「装载序 = 层序」被 `ot_s01_04l seq62` 证否。
#   ⇒ 下游要层序，**只能**按 PSV `priority` 生成；PC 侧任何来源都不得写入层序。
# 约束（本文件强制执行）：
#   ① `priority` 列**只允许**取 `:Priority` 原值（经 `layer_priority()` 读、带值域断言）；
#   ② **禁止**任何形式的合成 / 推估 / 回填 —— 取不到就**留空**（下游「无 PSV 覆盖则层序留空」）；
#   ③ 不在 PC 流里找层序、不用行序号 / 数组下标冒充层序。
# 机检闸门：`工具\audit_layer_source.py`（任何非 PSV 来源的层序写入 ⇒ FAIL）。
LAYER_SOURCE = "psv :Priority"     # 层序唯一来源（供审计与文档引用）
PRIORITY_FIELD = ":Priority"       # 唯一取值字段
PRIORITY_MIN, PRIORITY_MAX = 1, 10 # PSV 实测值域（R3 复核确认恒整数 1..10）

# Tasktype → (op, layer)  —— op 为归一卷标（闭集），layer 为演出层
#   layer ∈ {bg, sprite, chr, sound, movie, effect, ui, control, text}
OP_MAP = {
    "SpriteBG":            ("bg", "bg"),
    "SpriteBS":            ("bg", "sprite"),      # 背景贴图层（BS = back sprite）
    "Sprite":              ("bg", "sprite"),      # 前景/叠加贴图层
    "SpriteMove":          ("bg_move", "sprite"),
    "SpriteMoveEnd":       ("bg_move_end", "sprite"),
    "SpriteDelete":        ("bg_remove", "sprite"),
    "SpriteDeleteBG":      ("bg_remove", "bg"),
    "SpritePriority":      ("bg_priority", "sprite"),
    "SpriteQuake":         ("effect", "effect"),
    "CharacterOpen":       ("chr_add", "chr"),
    "CharacterOpenBS":     ("chr_add", "chr"),
    "CharacterDelete":     ("chr_remove", "chr"),
    "CharacterMove":       ("chr_move", "chr"),
    "CharacterAction":     ("chr_expr", "chr"),
    "CharacterActionEnd":  ("chr_expr_end", "chr"),
    "CharacterPriority":   ("chr_priority", "chr"),
    "CharacterWait":       ("chr_wait", "chr"),
    "CharacterStop":       ("chr_wait", "chr"),
    "CharacterQuake":      ("effect", "effect"),
    "SePlay":              ("se", "sound"),
    "SeStop":              ("se_stop", "sound"),
    "BgmPlay":             ("bgm", "sound"),
    "BgmStop":             ("bgm_stop", "sound"),
    "MoviePlay":           ("movie", "movie"),
    "MovieStop":           ("movie_stop", "movie"),
    "FadeIn":              ("effect", "effect"),
    "FadeOut":             ("effect", "effect"),
    "InOut":               ("effect", "effect"),
    "InOut_Act":           ("effect", "effect"),
    "Flash":               ("effect", "effect"),
    "EffectStart":         ("effect", "effect"),
    "EffectEnd":           ("effect", "effect"),
    "EffectQuake":         ("effect", "effect"),
    "EffectQuakeEnd":      ("effect", "effect"),
    "EyeCatch":            ("effect", "effect"),
    "EyeCatchEnd":         ("effect", "effect"),
    "Window":              ("ui", "ui"),
    "Message":             ("text", "text"),
    "BacklogMessage":      ("control", "control"),
    "Tag":                 ("control", "control"),
    "Jump_Tag":            ("control", "control"),
    "FlagSwitch_Tag":      ("control", "control"),
    "MessageSwitch_Tag":   ("control", "control"),
    "GlobalFlagSwitch_Tag": ("control", "control"),
    "GlobalFlagOperation": ("control", "control"),
    "FlagOperation":       ("control", "control"),
    "SceneJumpDialog":     ("control", "control"),
    "SceneJumpDialogEnd":  ("control", "control"),
    "SetSceneName":        ("control", "control"),
    "NextScene":           ("control", "control"),
    "End":                 ("control", "control"),
    "Achievement":         ("control", "control"),
    "TimeWait":            ("wait", "control"),
    "VoicePlay":           ("voice", "sound"),
    "VoiceStop":           ("voice", "sound"),
}

# 每个任务块内、参与时间线的行 → (列名, 说明)。未列出的键进 raw 备注。
TASK_KEYS = {
    ":Texture", ":SpriteNumber", ":Number", ":Position", ":Priority", ":Time",
    ":Rule", ":FadeIn", ":FadeWait", ":Fade", ":Div", ":SE", ":BGM", ":Voice",
    ":Image", ":Movie", ":Name", ":Message", ":Text", ":Visible", ":Action",
    ":Color", ":Scale", ":Curve", ":Wait", ":EndWait", ":Type", ":s", ":Priority",
}

RE_TASK = re.compile(r"^\s*\[Task(\d+)\]\s*$")
RE_CHARA = re.compile(r"^\s*\[(Chara\d+)\]\s*$")
RE_ANYBLOCK = re.compile(r"^\s*\[([A-Za-z_][\w]*)\]\s*$")
RE_CLOSE = re.compile(r"^\s*\}\s*$")
RE_BLOCK = re.compile(r"^\[([A-Za-z_][\w]*)\]\s*(\{)?$")
RE_CHARA_NAME = re.compile(r"^Chara\d+$")
RE_KEY = re.compile(r"^\s*(:[\w_]+)\s+(.*?)\s*$")
RE_BRACKET = re.compile(r"<<([^>]+)>>")
RE_POS3 = re.compile(r"^(-?[\d.]+)\s*,\s*(-?[\d.]+)(?:\s*,\s*(-?[\d.]+))?(?:\s*,\s*(-?[\d.]+))?")
RE_NUM = re.compile(r":\s*(-?\d+)")
RE_MSG = re.compile(r'^\s*:Message\s+"((?:[^"\\]|\\.)*)"')


def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def read_text(p):
    with open(p, "rb") as f:
        b = f.read()
    return b.decode("cp932", "replace")


def lf_norm(s):
    """文本按 **LF 规范化**（`core.autocrlf=true` 的上位检出面是 CRLF；先例
    ISSUE-20260930-02「闸门盘面 md5 改按 LF 规范化」）。只归一「行尾形态」，
    不动任何其它字节——非行尾内容差异仍会被 `--check` 判★不一致★。"""
    return s.replace("\r\n", "\n")


def layer_priority(kv):
    """层序（Priority）**唯一来源** = PSV `:Priority` 字段（见文件头层序策略声明）。

    ★ 强制约束（依据＝文件头「层序策略」声明的 A/B 两条，非用户裁定；ISSUE-20261006-07）：本函数是 `priority` 列的
      **唯一出口**，只读 `:Priority` **原值**；**禁止**合成 / 推估 / 回填 / 用下标冒充。
      取不到一律**留空**（下游「无 PSV 覆盖 ⇒ 层序留空，不得猜」）。
    值域断言：PSV 实测恒为整数 1..10（全 498 份脚本 10,309 处 `:Priority` 无越域）
      —— 越域或非整数即 **fail loud**，防脏数据 / 非 PSV 来源混入 `priority` 列。
    """
    v = ""
    if PRIORITY_FIELD in kv:
        parts = [p.strip() for p in kv[PRIORITY_FIELD][0].split(",")]
        v = parts[0] if parts else ""
    if v:
        try:
            iv = int(v)
        except ValueError:
            raise SystemExit("[layer] %s 非整数：%r（层序唯一来源＝PSV %s）"
                             % (PRIORITY_FIELD, v, PRIORITY_FIELD))
        if not (PRIORITY_MIN <= iv <= PRIORITY_MAX):
            raise SystemExit("[layer] %s 越域：%r（PSV 实测值域 %d..%d）"
                             % (PRIORITY_FIELD, v, PRIORITY_MIN, PRIORITY_MAX))
    return v


# ---------------------------------------------------------------- 解析
def strip_comment(val):
    """把 `值 // 注释` 切成 (值, 注释整串)。`//` 在引号内不算。"""
    inq = False
    for i in range(len(val) - 1):
        c = val[i]
        if c == '"':
            inq = not inq
        elif not inq and val[i] == "/" and val[i + 1] == "/":
            return val[:i].rstrip(), val[i + 2:].strip()
    return val.rstrip(), ""


def extract_names(val, comment):
    """按名解析 → (orig, repl)。

    - `orig`：**原版（PC）侧名字** —— 取首个 `//` 注释段且**整段就是一个 ASCII 词**者
      （`:SE 687 // SE049 // 置換しました<<se049l>>` → `SE049`；`:Texture 533 // EF01 // …` → `EF01`）。
    - `repl`：`置換しました<<X>>`（或裸 `<<X>>`）里的 **PSV 侧替换名**（`se049l` / `st_kaz01`）。
    两者不一致时以 `orig` 为准解析我方库（我方库是 PC 派生）——实测 SE 正是这种情形。
    统一 upper、剥扩展名、剥 `ST_` 前缀。
    """
    orig = ""
    first = (comment or "").split("//")[0].strip()
    if re.match(r"^[A-Za-z_][\w]*$", first):
        orig = first
    mb = RE_BRACKET.search(comment or "") or RE_BRACKET.search(val or "")
    repl = mb.group(1).strip() if mb else ""

    def nz(s):
        s = os.path.splitext(s)[0].upper()
        return s[3:] if s.startswith("ST_") else s

    return nz(orig), nz(repl)


def extract_name(val, comment, allow_plain=True):
    """兼容旧调用点：返回 (name, how)，`orig` 优先、否则 `repl`。"""
    o, r = extract_names(val, comment)
    return (o or r), ("orig" if o else ("repl" if r else ""))


def parse_script(text):
    """返回 (startup: dict, tasks: list[dict])。

    状态机：`[X]` 表头 → `{` 归属该表头（`pending_header`）；**孤儿 `{`**（`TaskList` 直属）视为匿名任务
    —— 源侧实测存在三种畸形：① 无标号的 `{ :Tasktype … }`（`S03C_03C` Task7700 之后）；
    ② `[TaskN]` 之后缺 `{`（`S04_13A` Task510）；③ 缺 `}` 导致下一表头嵌入。
    规则：**新 `[TaskN]` 一律开启新任务**（旧任务若无键则留空、随后被剔除），从而三种畸形都收敛到
    「`:Tasktype` 归最近的 `[TaskN]`」这一确定语义。
    task = {task,type,kv,charas,anon}
    """
    startup = {}
    tasks = []
    cur = None                 # 当前任务
    section = None             # 当前段名（StartUp / TaskList / LoadTexture / …）
    pending_header = None      # 刚见到的 [X]，其后的第一个 `{` 归它
    pending_chara = None       # 刚见到的 [CharaK]，其后的 `{` 开启子块
    subs_open = []             # [(brace_depth, sub)] —— 子块内的键要落到子块，不是任务
    depth = 0
    anon = 0

    for ln in text.split("\n"):
        st = ln.strip()
        if st.startswith("//"):
            continue
        m = RE_BLOCK.match(st)                     # [Name] 可紧跟 {
        if m:
            name, brace = m.group(1), m.group(2)
            if name.startswith("Task") and name[4:].isdigit():
                cur = {"task": name[4:], "type": "", "types": [], "kv": {},
                       "charas": [], "anon": False}
                tasks.append(cur)
                pending_header = name
            elif RE_CHARA_NAME.match(name):
                sub = {"kv": {}}
                if cur is None:                        # 极罕见：Chara 不在任何任务内
                    anon += 1
                    cur = {"task": "anon%04d" % anon, "type": "", "types": [],
                           "kv": {}, "charas": [], "anon": True}
                    tasks.append(cur)
                cur["charas"].append(sub)
                pending_chara = sub
                pending_header = name
            else:
                section = name
                cur = None
                pending_header = name
            if brace:
                pending_header = None
                depth += 1
                if pending_chara is not None:
                    subs_open.append((depth, pending_chara))
                    pending_chara = None
            continue
        if st == "{":
            if pending_header is not None:
                pending_header = None
            elif section == "TaskList":
                anon += 1
                cur = {"task": "anon%04d" % anon, "type": "", "types": [],
                       "kv": {}, "charas": [], "anon": True}
                tasks.append(cur)
            depth += 1
            if pending_chara is not None:
                subs_open.append((depth, pending_chara))
                pending_chara = None
            continue
        if st == "}":
            if subs_open and subs_open[-1][0] == depth:
                subs_open.pop()
            if depth > 0:
                depth -= 1
            if depth == 0:
                cur = None
                subs_open = []
            continue
        mk = RE_KEY.match(ln)
        if mk:
            key, rest = mk.group(1), mk.group(2)
            val, comment = strip_comment(rest)
            # 子块内的键（`:Number` / `:Position` / `:Priority` …）落到子块
            if subs_open and subs_open[-1][0] == depth:
                subs_open[-1][1]["kv"][key] = (val, comment)
                continue
            if cur is None:
                startup[key] = (val, comment)
                continue
            if key == ":Tasktype":
                mt = re.match(r'^"([^"]*)"', val)
                if mt:
                    cur["types"].append(mt.group(1))
                    if not cur["type"]:
                        cur["type"] = mt.group(1)
            cur["kv"][key] = (val, comment)
    return startup, tasks


# ---------------------------------------------------------------- 素材映射
class AssetMap(object):
    """(源, kind, 素材名) → 交付层路径。

    主表 `素材库到统一名.tsv`（8,052 行，含 `替代安全性`）；
    精修表 `素材引用映射.tsv`（1,903 行，含 `结论`：代表件/等价替代/**有差异替代**）。

    ★★ kind 感知（ISSUE-20261008-01 修正）：解析键**必须带 kind**。
      原实现键＝`(源, 统一名stem)`，`resolve()` 对非 se/bgm 的 kind **一律走同一张表**
      ⇒ **PSV 声明的 `kind`（pic/chr）不参与查表**，`SpriteBG`（背景，kind=pic）
      会命中同名的 **chr（立绘）** 行：实测 `ot_s03_03e` 的 `SpriteBG` 名 `AI_01`
      命中 `素材库到统一名.tsv:2542`（kind=chr → `立绘/ai_01.png`），
      而正确行是同表 `:85`（kind=pic → `CG背景/cg_ai_01.jpg`）。

    键里的「素材名」两套都登记（同一行、同 kind）：
      ① **统一名 stem**（去扩展名，如 `ai_01` / `cg_ai_01`）—— 原实现沿用的名字，保证既有命中不变；
      ② **源侧名 stem**＝`素材库文件` 去 `<源>_` 前缀（如 `ot_ai_01.png`→`ai_01`）——
         **这才是 PSV 侧引用的名字**（PSV 从 PC 派生的原版名）；对 pic 行两者常不同
         （`素材库文件=ot_ai_01.png`、`统一名=cg_ai_01.png`），只登记 ① 会让 kind=pic 查不到 pic 行。
      登记次序：统一名优先（`setdefault`），故既有命中优先级不变。
    """

    def __init__(self, res_dir):
        self.by_key = {}      # (源, kind, STEM) -> (交付路径, 替代安全性)
        self.by_key_any = {}  # STEM -> (源, 交付路径)
        self.repl = {}        # (源, STEM) -> (交付路径, 结论)
        self.n_rows = 0
        self.n_repl = 0
        self.deliv_ok = set()
        p1 = os.path.join(res_dir, "交接编程组", "素材库到统一名.tsv")
        if not os.path.isfile(p1):
            raise SystemExit("[fatal] 缺映射表：%s" % p1)
        with io.open(p1, "r", encoding="utf-8-sig") as f:
            head = f.readline().rstrip("\n").split("\t")
            ix = {h: i for i, h in enumerate(head)}
            for ln in f:
                c = ln.rstrip("\n").split("\t")
                if len(c) <= ix["交付路径"]:
                    continue
                src = c[ix["源"]]
                if src == "源":
                    continue
                # ★ 键＝(源, kind, 素材名 stem)：kind 必须参与（见类 docstring 的 kind 感知说明）。
                #   素材名两套都登记：① 统一名 stem（原实现沿用；既有命中不变）
                #                     ② 源侧名 stem＝素材库文件去 <源>_ 前缀（PSV 实际引用的名字）
                kind = c[ix["素材库kind"]] if "素材库kind" in ix and len(c) > ix["素材库kind"] else ""
                un_stem = os.path.splitext(c[ix["统一名"]])[0].upper()
                libfile = c[ix["素材库文件"]] if "素材库文件" in ix and len(c) > ix["素材库文件"] else ""
                lib_stem = os.path.splitext(libfile)[0]
                pre = src + "_"
                srcside = (lib_stem[len(pre):] if lib_stem.startswith(pre) else lib_stem).upper()
                deliv = c[ix["交付路径"]]
                safe = c[ix["替代安全性"]] if "替代安全性" in ix and len(c) > ix["替代安全性"] else ""
                self.n_rows += 1
                for kstem in (un_stem, srcside):          # 统一名优先，源侧名补登记
                    if kstem:
                        self.by_key.setdefault((src, kind, kstem), (deliv, safe))
                self.by_key_any.setdefault(un_stem, (src, deliv))
        p3 = os.path.join(res_dir, "交接编程组", "素材引用映射.tsv")
        if os.path.isfile(p3):
            with io.open(p3, "r", encoding="utf-8-sig") as f:
                head = f.readline().rstrip("\n").split("\t")
                ix3 = {h: i for i, h in enumerate(head)}
                for ln in f:
                    c = ln.rstrip("\n").split("\t")
                    if len(c) <= max(ix3.get("交付路径", 0), ix3.get("统一名", 0)):
                        continue
                    src = c[ix3["引用"]].split("/")[0]
                    stem = os.path.splitext(c[ix3["统一名"]])[0].upper()
                    self.n_repl += 1
                    self.repl.setdefault((src, stem), (c[ix3["交付路径"]], c[ix3["结论"]]))
        p2 = os.path.join(res_dir, "美术统一_交付", "交付清单.tsv")
        if os.path.isfile(p2):
            with io.open(p2, "r", encoding="utf-8-sig") as f:
                f.readline()
                for ln in f:
                    c = ln.rstrip("\n").split("\t")
                    if len(c) >= 5:
                        self.deliv_ok.add(c[4].replace("\\", "/").lower())
        # ---- se / bgm 不在「素材库到统一名」表内：直接扫库目录建索引（目录即事实）
        #      se 文件名为 `<源>_se<3位数字>.ogg`；PSV 侧名 `SE049` / `SE049L` 都归到 `SE049`
        #      bgm 只有 `otv` 用 `<源>_bgm<3位>.ogg` 的 PSV 归档序命名（资源组已确证）
        self.se = {}
        self.bgm = {}
        lib = os.path.join(res_dir, "krkr素材库")
        for src in SRC_ORDER:
            sd = os.path.join(lib, src, "se")
            if os.path.isdir(sd):
                for fn in os.listdir(sd):
                    m = re.match(r"^%s_se(\d+)\.(ogg|wav|mp3)$" % src, fn, re.I)
                    if m:
                        self.se.setdefault((src, "SE" + m.group(1)), "se/" + fn)
            bd = os.path.join(lib, src, "bgm")
            if os.path.isdir(bd):
                for fn in os.listdir(bd):
                    m = re.match(r"^%s_bgm(\d+)\.(ogg|wav|mp3)$" % src, fn, re.I)
                    if m:
                        self.bgm.setdefault((src, int(m.group(1))), "bgm/" + fn)

    def resolve(self, src, stem, kind):
        """返回 (delivery, status)。

        status ∈ {ok, sub-eq, sub-diff, ok-se, ok-bgm, ok-crosssrc(源), missing, empty}
        """
        if not stem:
            return "", "empty"
        if kind == "se":
            key = "SE" + re.sub(r"\D", "", stem)
            d = self.se.get((src, key))
            if d:
                return d, "ok-se"
            return "", "missing"
        if kind == "bgm":
            d = self.bgm.get((src, int(re.sub(r"\D", "", stem) or -1)))
            if d:
                return d, "ok-bgm"
            return "", "missing"
        ent = self.by_key.get((src, kind, stem))     # ★ kind 参与查表（见类 docstring）
        if ent:
            deliv, safe = ent
            r = self.repl.get((src, stem))
            concl = r[1] if r else ""
            if concl == "有差异替代" or safe == "有差异":
                return deliv, "sub-diff"
            if concl == "等价替代":
                return deliv, "sub-eq"
            return deliv, "ok"
        # 跨源同名兜底（`bg_black` 等：同名义在不同源、交付层只有一份）
        any_ = self.by_key_any.get(stem)
        if any_:
            return any_[1], "ok-crosssrc(%s)" % any_[0]
        return "", "missing"


# ---------------------------------------------------------------- 场景映射
def build_scene_index(corpus_dir):
    """suffix -> (源, scene_id)；suffix 大小写敏感与不敏感两份。"""
    exact, lower = {}, {}
    for src in SRC_ORDER:
        p = os.path.join(corpus_dir, "scene_%s.jsonl" % src)
        if not os.path.isfile(p):
            continue
        with io.open(p, "r", encoding="utf-8") as f:
            for ln in f:
                if not ln.strip():
                    continue
                d = json.loads(ln)
                sid = d["scene_id"]
                suf = sid.split("_", 1)[1] if "_" in sid else sid
                exact.setdefault(suf, (src, sid))
                lower.setdefault(suf.lower(), (src, sid))
    return exact, lower


def match_scene(psv_name, exact, lower):
    cands = [psv_name, psv_name.lower(), psv_name.upper()]
    if psv_name[:1].upper() == "P":
        cands.append(psv_name[1:])
        cands.append(psv_name[1:].lower())
    for c in cands:
        if c in exact:
            return exact[c]
    for c in cands:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


# ---------------------------------------------------------------- 对齐
def norm_txt(s):
    s = (s or "").replace("\u3000", " ").replace("\n", "")
    s = re.sub(r"<[^>]*>", "", s)
    s = s.replace("\\", "")
    return re.sub(r"\s+", "", s)


def align_msgs(pm, cor_jp):
    """difflib 对齐 → ({psv_idx: cor_idx}, n_exact, n_mapped, n_pm)

    `n_exact` = 逐字相等段命中数；`n_mapped` = 找到对应语料行的 PSV 条数（含 replace 段顺序配对）。
    """
    a = [norm_txt(x) for x in pm]
    b = [norm_txt(x) for x in cor_jp]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    m, n_eq = {}, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                m[i1 + d] = j1 + d
            n_eq += i2 - i1
        elif tag == "replace":
            for d in range(min(i2 - i1, j2 - j1)):
                m[i1 + d] = j1 + d
    return m, n_eq, len(m), len(a)


# ---------------------------------------------------------------- 主流程
def collect_rows(scene_id, script, text, tasks, cor_lines, amap, src):
    """产出一场的时间线行。`script`=脚本文件名，`text`=脚本文本。"""
    pm = [x.group(1).replace("\\n", "\n")
          for x in (RE_MSG.match(l) for l in text.split("\n")) if x]
    cor_jp = [(x.get("jp") or "") for x in cor_lines]
    seq_of = [x.get("seq") for x in cor_lines]
    amap_idx, n_eq, n_map, n_pm = align_msgs(pm, cor_jp)
    rows = []
    msg_ord = 0
    for t in tasks:
        # ★ 一任务可有多行 `:Tasktype`（实测 `S03_06E2` Task2790 同写 SpriteBG + Sprite）——
        #   逐个类型出一组行（参数共享），不丢任何一个演出语义。
        types = t.get("types") or [t["type"]]
        if "Message" in types:
            msg_ord += 1
        # 该任务触发点：其之前的 Message 条数（k=0 → 首行之前）
        k = msg_ord - 1 if "Message" in types else msg_ord
        ci = amap_idx.get(k)
        if ci is None and 0 <= k < n_pm:
            for kk in range(k, n_pm):          # 向后找最近有映射的台词
                if kk in amap_idx:
                    ci = amap_idx[kk]
                    break
        # ★ 尾随事件（k >= n_pm，即本场最后一句**之后**）与「找不到映射」的兜底：
        #   一律取**末条语料行的 seq**（与 资源组 `演出表说明.md` §1.1 的 `after_last_line` 同口径），
        #   绝不回落到场首行 —— 否则退场类事件会提前到开场（一审阻断项：实测 5,244 行 / 437 场）。
        if ci is None:
            seq = seq_of[-1] if seq_of else 1
        else:
            seq = seq_of[ci] if ci < len(seq_of) else (seq_of[-1] if seq_of else 1)
        kv = t["kv"]

        def g(key, idx=0):
            if key not in kv:
                return ""
            v, _ = kv[key]
            parts = [p.strip() for p in v.split(",")]
            return parts[idx] if idx < len(parts) else ""

        for ttype in types:
            op, layer = OP_MAP.get(ttype, ("other", "other"))
            # 资源与素材 —— 立绘任务**每个 [CharaK] 子块各出一行**（`:SpriteMax` 可 >1，实测最多 4 个子块）
            targets = []          # [(name, kind, cx, cy, cpri, sub)]
            if ttype in ("SpriteBG", "SpriteBS", "Sprite"):
                v, c = kv.get(":Texture", ("", ""))
                nm, _ = extract_name(v, c, True)
                targets.append((nm, "pic", "", "", "", None))
            elif ttype in ("SpriteMove", "SpriteMoveEnd", "SpriteDelete",
                           "SpriteDeleteBG", "SpritePriority", "SpriteQuake"):
                # ★ 键不固定：实测 `:SpriteNumber` / `:Texture` / `:Sprite` 三种都用过
                v, c = kv.get(":SpriteNumber", kv.get(":Texture", kv.get(":Sprite", ("", ""))))
                nm, _ = extract_name(v, c, True)
                targets.append((nm, "pic", "", "", "", None))
            elif ttype.startswith("Character") and ttype not in ("CharacterWait", "CharacterStop", "CharacterQuake"):
                subs = t["charas"] or [None]
                for sub in subs:
                    ck = dict(sub["kv"]) if sub else {}
                    if sub is None:
                        # ★ `CharacterActionEnd` 等把贴图放在**任务级** `:Character` / `:Number`
                        for kk in (":Character", ":Number"):
                            if kk in kv:
                                ck[":Number"] = kv[kk]
                                break
                        for kk in (":Position", ":Priority"):
                            if kk in kv:
                                ck[kk] = kv[kk]
                    v, c = ck.get(":Number", ("", ""))
                    nm, _ = extract_name(v, c, False)
                    px = py = pp = ""
                    if ":Position" in ck:
                        mm2 = RE_POS3.match(ck[":Position"][0])
                        if mm2:
                            px, py = mm2.group(1), mm2.group(2)
                    pp = ck.get(":Priority", ("", ""))[0]
                    targets.append((nm, "chr", px, py, pp, sub))
            elif ttype in ("SePlay", "SeStop"):
                v, c = kv.get(":SE", ("", ""))
                nm, _ = extract_name(v, c, True)
                targets.append((nm, "se", "", "", "", None))
            elif ttype in ("BgmPlay", "BgmStop"):
                # `:BGM N` 是 PSV 归档序（无名字）；仅当库里存在 `<源>_bgm<NNN>` 命名的件时才解析
                v = g(":BGM", 0)
                targets.append(("BGM%s" % (re.sub(r"\D", "", v) or ""), "bgm",
                                "", "", "", None) if v else
                               ("", "", "", "", "", None))
            elif ttype == "Message":
                v, c = kv.get(":Voice", ("", ""))
                nm, _ = extract_name(v, c, False)
                targets.append((nm, "voice", "", "", "", None))
            else:
                targets.append(("", "", "", "", "", None))

            for (name, kind, cx, cy, cpri, _sub) in targets:
                delivery = status = ""
                if name:
                    delivery, status = amap.resolve(src, name, kind)
                rows.append({
                    "scene_id": scene_id, "script": script, "src": src, "task": t["task"], "type": ttype,
                    "op": op, "layer": layer, "name": name, "kind": kind,
                    "delivery": delivery, "status": status,
                    "x": g(":Position", 0), "y": g(":Position", 1),
                    "cx": cx, "cy": cy, "cpri": cpri,
                    # ★ 层序唯一出口：layer_priority() 只读 PSV `:Priority`（见该函数与文件头声明）
                    "priority": layer_priority(kv), "time": g(":Time", 0),
                    "rule": g(":Rule", 0), "fade": g(":FadeIn", 0),
                    "se": g(":SE", 0), "bgm": g(":BGM", 0), "voice": g(":Voice", 0),
                    "image": kv.get(":Image", ("", ""))[0].strip(),
                    "movie": g(":Movie", 0), "nameid": g(":Name", 0),
                    "msg_ord": k, "seq": seq, "raw": ttype,
                })
    return rows, {"psv_msg": n_pm, "corpus_lines": len(cor_lines),
                  "aligned_eq": n_eq, "aligned_map": n_map,
                  "align": round(n_eq / n_pm, 4) if n_pm else 0.0,
                  "map_rate": round(n_map / n_pm, 4) if n_pm else 0.0,
                  "header": (len(cor_lines) - n_pm)}


COLS = ["scene_id", "script", "task", "type", "op", "layer", "name", "kind",
        "delivery", "status", "x", "y", "cx", "cy", "cpri", "priority", "time",
        "rule", "fade", "se", "bgm", "voice", "image", "movie", "nameid",
        "msg_ord", "seq"]


def to_tsv(rows):
    out = ["\t".join(COLS)]
    for r in rows:
        out.append("\t".join("" if r[c] is None else str(r[c]) for c in COLS))
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT)
    ap.add_argument("--psv", default=None)
    ap.add_argument("--res", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sample", default="ot_s01_01a,ot_s01_02a,ot_s01_02c,ot_s03_01a,otv_M01_01,otp_02_01a")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    root = a.data_root
    proj = os.path.join(root, PROJ_REL)
    psv_dir = a.psv or os.path.join(root, PSV_REL)
    res_dir = a.res or os.path.join(proj, "资源组")
    # ★ 产出口默认**跟脚本走**（本工具在 编程组\工具\ 下）：写进当前 checkout，
    #   避免从 worktree 运行时把产物误落进主工作树（§一 铁律 5）。
    out_dir = a.out or os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PSV演出"))
    corpus_dir = os.path.join(res_dir, "剧本")

    amap = AssetMap(res_dir)
    exact, lower = build_scene_index(corpus_dir)
    log("[psv] 映射表 %d 行；语料后缀 %d 条" % (amap.n_rows, len(exact)))

    # 载入语料
    corpus = {}
    for src in SRC_ORDER:
        p = os.path.join(corpus_dir, "scene_%s.jsonl" % src)
        if not os.path.isfile(p):
            continue
        with io.open(p, "r", encoding="utf-8") as f:
            for ln in f:
                if ln.strip():
                    d = json.loads(ln)
                    corpus[d["scene_id"]] = d

    files = [n for n in sorted(os.listdir(psv_dir)) if os.path.isfile(os.path.join(psv_dir, n))]
    all_rows, scene_rows, unmatched = [], [], []
    stat = {"files": 0, "mapped": 0, "unmapped": 0, "tasks": 0, "empty_task": 0,
            "name_rows": 0, "name_ok": 0, "name_se": 0, "name_bgm": 0,
            "name_sub_eq": 0, "name_sub_diff": 0,
            "name_cross": 0, "name_missing": 0, "voice_unmapped": 0}

    def flush(rows):
        if not rows:
            return
        for r in rows:
            all_rows.append(r)

    for fn in files:
        pref = fn[:1].upper()
        if pref not in SRC_BY_PREFIX:
            continue                      # adv.txt / CGMODE / chrn.txt 等全局表跳过
        m = match_scene(fn, exact, lower)
        if not m:
            unmatched.append(fn)
            continue
        src, scene_id = m
        d = corpus.get(scene_id)
        if d is None:
            unmatched.append(fn)
            continue
        text = read_text(os.path.join(psv_dir, fn))
        _startup, tasks = parse_script(text)
        # ★ 无 `:Tasktype` 的空壳任务（如 `[Task670]` 后面直接跟注释、无 `{}` 体）不是演出事件，剔除并计数
        n_empty = sum(1 for t in tasks if not t["type"])
        tasks = [t for t in tasks if t["type"]]
        stat["empty_task"] += n_empty
        cor_lines = d.get("lines", [])
        rows, info = collect_rows(scene_id, fn, text, tasks, cor_lines, amap, src)
        stat["files"] += 1
        stat["mapped"] += 1
        stat["tasks"] += len(tasks)
        for r in rows:
            if r["name"]:
                stat["name_rows"] += 1
                s = r["status"]
                if s in ("ok", "ok-se", "ok-bgm"):
                    stat["name_ok"] += 1
                    if s == "ok-se":
                        stat["name_se"] += 1
                    elif s == "ok-bgm":
                        stat["name_bgm"] += 1
                elif s == "sub-eq":
                    stat["name_sub_eq"] += 1
                elif s == "sub-diff":
                    stat["name_sub_diff"] += 1
                elif s.startswith("ok-crosssrc"):
                    stat["name_cross"] += 1
                else:
                    stat["name_missing"] += 1
        flush(rows)
        scene_rows.append({"scene_id": scene_id, "script": fn, "src": src,
                           "tasks": len(tasks), "psv_msg": info["psv_msg"],
                           "corpus_lines": info["corpus_lines"],
                           "header": info["header"], "align": info["align"],
                           "map_rate": info["map_rate"],
                           "aligned_eq": info["aligned_eq"],
                           "aligned_map": info["aligned_map"]})
        if a.limit and stat["files"] >= a.limit:
            break

    # 产物
    master = to_tsv(all_rows)
    srows = ["scene_id\tscript\tsrc\ttasks\tpsv_msg\tcorpus_lines\theader\talign\tmap_rate\taligned_eq\taligned_map"]
    for r in scene_rows:
        srows.append("\t".join(str(r[c]) for c in
                               ["scene_id", "script", "src", "tasks", "psv_msg",
                                "corpus_lines", "header", "align", "map_rate",
                                "aligned_eq", "aligned_map"]))
    scene_tsv = "\n".join(srows) + "\n"

    # 抽样对账（原样行 ↔ 解析行）
    samples = [s for s in a.sample.split(",") if s]
    acc = ["scene_id\tseq\ttask\ttype\top\tname\tdelivery\tparams\traw_line"]
    by_scene = {}
    for r in all_rows:
        by_scene.setdefault(r["scene_id"], []).append(r)
    for sid in samples:
        if sid not in by_scene:
            acc.append("%s\t\t\t\t\t\t\t\t（未匹配）" % sid)
            continue
        fn = by_scene[sid][0]["script"]
        raw = read_text(os.path.join(psv_dir, fn)).split("\n")
        rawmap = {}
        cur = None
        for ln in raw:
            m = RE_TASK.match(ln)
            if m:
                cur = m.group(1)
                continue
            if cur and RE_KEY.match(ln) and not ln.strip().startswith("//"):
                k = RE_KEY.match(ln).group(1)
                if k in (":Texture", ":SpriteNumber", ":Number", ":Position",
                         ":Priority", ":Time", ":Rule", ":SE", ":BGM", ":Message"):
                    rawmap.setdefault(cur, []).append(ln.strip()[:160])
        for r in by_scene[sid]:
            if r["op"] == "text":
                continue
            acc.append("\t".join([sid, str(r["seq"]), r["task"], r["type"], r["op"],
                                  r["name"], r["delivery"],
                                  "x=%s,y=%s,p=%s,t=%s,rule=%s" % (r["x"], r["y"], r["priority"], r["time"], r["rule"]),
                                  " | ".join(rawmap.get(r["task"], []))]))
    acc_tsv = "\n".join(acc) + "\n"

    # 缺口清单：我方交付层查不到的素材名（逐名统计引用次数与首现场景）
    gap = collections.Counter()
    gap_scene = {}
    gap_src = {}
    for r in all_rows:
        if r["name"] and r["status"] == "missing":
            if r["kind"] == "voice":
                # 语音名 PSV 侧自成一系（`misaki_000`），我方语音由**语料 lines[].audio** 承载
                # ⇒ 不参与交付层映射，仅计数（不当作缺口，避免淹没真正的缺口）
                stat["voice_unmapped"] += 1
                continue
            gap[(r["src"], r["name"], r["kind"])] += 1
            gap_scene.setdefault((r["src"], r["name"], r["kind"]), r["scene_id"])
            gap_src.setdefault((r["src"], r["name"], r["kind"]), r["src"])
    grows = ["源\tname\tkind\t引用次数\t首现场景"]
    for (src, nm, kd), n in sorted(gap.items(), key=lambda kv: -kv[1]):
        grows.append("%s\t%s\t%s\t%d\t%s" % (src, nm, kd, n, gap_scene[(src, nm, kd)]))
    gap_tsv = "\n".join(grows) + "\n"

    # ★ log 必须在缺口统计**之后**（否则「语音名另计」恒为 0 —— 一审 Minor 项）
    log("[psv] 场景 %d（未匹配 %d）｜任务 %d｜素材行 %d（直取 ok %d ＝ 图像 %d + SE %d + BGM %d）"
        "/ 等价替代 %d / ★有差异 %d / 跨源 %d / 缺 %d；语音名另计 %d 条不参与映射"
        % (stat["mapped"], len(unmatched), stat["tasks"], stat["name_rows"],
           stat["name_ok"], stat["name_ok"] - stat["name_se"] - stat["name_bgm"],
           stat["name_se"], stat["name_bgm"],
           stat["name_sub_eq"], stat["name_sub_diff"],
           stat["name_cross"], stat["name_missing"], stat["voice_unmapped"]))

    idx = {"files_seen": len(files), "scenes_mapped": stat["mapped"],
           "psv_unmatched": unmatched, "tasks_total": stat["tasks"],
           "asset_rows": stat["name_rows"], "asset_ok": stat["name_ok"],
           "asset_sub_eq": stat["name_sub_eq"], "asset_sub_diff": stat["name_sub_diff"],
           "asset_crosssrc": stat["name_cross"], "asset_missing": stat["name_missing"],
           "voice_names_not_mapped": stat["voice_unmapped"],
           "empty_task_dropped": stat["empty_task"],
           "timeline_rows": len(all_rows),
           "scene_map_rate_lt98": sum(1 for s in scene_rows if s["map_rate"] < 0.98),
           "scene_align_lt98": sum(1 for s in scene_rows if s["align"] < 0.98),
           "low_align": [s for s in scene_rows if s["align"] < 0.98][:200]}

    if a.check:
        ok = True
        chk = {"时间线.tsv": master, "场景映射.tsv": scene_tsv,
               "对账_抽样.tsv": acc_tsv, "缺口.tsv": gap_tsv}
        for nm, txt in chk.items():
            p = os.path.join(out_dir, nm)
            cur = io.open(p, "r", encoding="utf-8", newline="").read() if os.path.isfile(p) else None
            # ★ 两侧文本按 LF 归一后再比（见 lf_norm；先例 ISSUE-20260930-02）：
            #   库内为 LF、autocrlf=true 的检出面为 CRLF，直接比会在 CRLF 检出面上**假失败**
            #   （ISSUE-20261009-08）；**非**行尾差异照旧判★不一致★（不放宽、不跳过）。
            same = (cur is not None and lf_norm(cur) == lf_norm(txt))
            ok = ok and same
            log("[check] %-16s %s" % (nm, "一致" if same else "★不一致★"))
        log("[check] %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    os.makedirs(out_dir, exist_ok=True)
    for nm, txt in (("时间线.tsv", master), ("场景映射.tsv", scene_tsv),
                    ("对账_抽样.tsv", acc_tsv), ("缺口.tsv", gap_tsv)):
        with io.open(os.path.join(out_dir, nm), "w", encoding="utf-8", newline="") as f:
            f.write(txt)
    with io.open(os.path.join(out_dir, "_index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    log("[out] %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
