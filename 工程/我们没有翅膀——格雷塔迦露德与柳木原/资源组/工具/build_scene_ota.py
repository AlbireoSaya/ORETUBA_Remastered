# -*- coding: utf-8 -*-
r"""
W6c · 结构化剧本 `scene_ota.jsonl` 构建器（S3 After Story / 源代号 `ota` · 172 场景）

契约：
  * `资源组\剧本\schema.md`（**W6a 定稿 schema，本模块不另创**）
  * `资源组\修正\_README.md` §四 / §四.5（取文顺序 + **修正表来源门控**）/ §八（D14）
只读：`工程\我们没有翅膀 After Story\`（**一个字节都不许改**）、`资源组\修正\*`、
      `资源组\krkr素材库\资源总账.json`
只写：`资源组\剧本\scene_ota.jsonl`、`子代理工作区\ISSUE-20260918-06\W6c\_build_stats_ota.json`

本作与 R 版（W6a）的结构差异（**决定本构建器的写法**）：
  1. **记录头 op 不固定**（0x18/0x10/0x12 等）→ 说话人**不能靠 op 判定**；
     `语料\译文.json` 的 `speaker` 字段已由 `工具\parse_after.py` 按「记录区内最后一个
     非资源类声明串 `01 01 <u16 L> <名> 00`」解出，本模块**直接复用**，不重解。
  2. `.tob` 头部**无标签表**（`nlab=0`）→ 跳转标签改由**声明串扫描**取得（见 `scan_labels`）。
  3. 修正表 `source=ota` 的 `locator` 用 **`idx=<消息 index>`**（不是 `offset=`）；
     `otp` 用 `seq=`、`otr` 用 `offset=`（`修正表_B1B3.tsv` 三种并存）。
  4. 图像引用是**逐消息**的（`台词.json` 的 `image` 字段，全部 `PIC\*.ELG`），
     本模块取**场景内并集**挂到场景级 `assets`（schema §2.1 明确「图像/音效只挂场景级」）。
  5. 语音引用中有 **40 个 立绘（CHR）名被解析器误判为 voice**（`CIN###`/`CIT###`/`LR2##`/`cO255`），
     本模块**保留源值**于 `lines[].voice`、`audio=[]`，并在报告中逐条列出（不静默丢弃、不臆断回收）。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ota.py"
"""
import json, os, re, csv, struct, collections, sys

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__（同 build_scene_otp.py）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _term_unify               # noqa: E402  同目录共享模块：`term_unify` 语义的唯一实现

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；写 = 本脚本所在 checkout（由 `__file__` 推导）。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, r"资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, r"修正")                            # 修正表：以本分支副本为准
OUT  = os.path.join(RES_LOCAL, r"剧本")                            # 产物：写本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6c")   # 写本 checkout

AS     = os.path.join(DATA_ROOT, r"工程\我们没有翅膀 After Story")
AS_COR = os.path.join(AS, r"语料")
AS_RAW = os.path.join(AS_COR, r"原文")

TRANSLATION = os.path.join(AS_COR, "译文.json")          # jp / cn / speaker / voice / index / kind / off
DIALOGUE    = os.path.join(AS_COR, "台词.json")          # image（逐消息）
CHOICES     = os.path.join(AS_COR, "选择支补译.json")     # 40 处选择支块
NAMELOCK    = os.path.join(AS_COR, "译名锁定表.json")     # 说话人 / 专名 中文定名
LEDGER      = os.path.join(RES, r"krkr素材库\资源总账.json")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

TABLES = [
    ("修正表_B1B3.tsv",          os.path.join(FIX, "修正表_B1B3.tsv")),
    ("修正表_B1B3_扩展.tsv",     os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    ("修正表_新增场景mig重译.tsv", os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260930-10/11：用户 2026-09-30 术语裁决（source 按行门控；field=cn，fix_type=term_unify）。
    #   本模块此前未挂载该表 ⇒ 表内 3 条 source=ota 的行（独立「空学」→「美空学院」）**静默不生效**，
    #   2026-09-30 由 `build_rulings_fixtable.py` 的 G7「消费方挂接」闸门抓出并修复。
    ("修正表_裁决20260930.tsv",  os.path.join(FIX, "修正表_裁决20260930.tsv")),
    # ISSUE-20261009-04：用户 2026-10-09 裁决「奈落」全量回改。本模块新增挂载该表——
    #   表内 source=ota 1 条（11_5b.tob idx=155，jp「奈落の底」CN「深渊」→「奈落」，fix_type=retranslate，
    #   old_text 为源译文整句、逐字符断言）；其余 source 条目在本模块无对象（走既有范围对账留痕）。
    ("修正表_奈落.tsv",          os.path.join(FIX, "修正表_奈落.tsv")),
]
TERM_TABLE = os.path.join(FIX, "译名替换表.tsv")

SOURCE = "ota"

# ---------------------------------------------------------------- 修正表来源门控（W6a2 通用契约）
# `资源组\修正\_README.md` §四.5：条目只在其 `source` 与该行「取文基准层」`cn_base` 一致时生效。
# 本模块全部有效行取文基准层 = `ota`；`otr`/`otp` 条目在本模块**一律被门控排除**（逐条留痕）。
CORR_SOURCE_TO_BASE = {
    "otr": "otr_new",
    "otp": "otp",
    "ota": "ota",
    "ot":  "ot",
    # 六源全覆盖（ISSUE-20260930-11 补齐 otv/np —— 缺项会让装载该表的本次运行直接 fail loud）
    "otv": "otv",
    "np":  "np",
}
GATED = []
TERM_NOOP = []    # `term_unify` 的幂等 no-op 留痕（ISSUE-20260930-12；构建期应为 0 条）

# ---------------------------------------------------------------- 结构分层（依据 `资源组\01_剧情流程图.md` §4.5 五层结构）
# `route`：脚本名前缀 → 路线/系列名。**22/23 两条线归属未定（总纲 §八 待裁决 D13）→ null，不臆断。**
ROUTE_BY_PREFIX = {
    "11": "AS 对决羽田鹰志",      # 再会/閉幕　～バーサス羽田タカシ～
    "12": "AS 对决千岁鹫介",      # 再会/閉幕　～バーサス千歳鷲介～
    "13": "AS 对决成田隼人",      # 再会/閉幕　～バーサス成田隼人～
    "14": "AS 对决羽田小鹰志",    # 再会/閉幕　～バーサス羽田ヨージ～
    "21": "AS 美咲线",
    "22": None,                   # D13 待裁决（おっぱい系列归属未定）
    "23": None,                   # D13 待裁决（蒼穹女学院 Xデー 归属未定）
    "24": "AS 最终统合线",
    "31": "AS 各线 after", "32": "AS 各线 after",
    "33": "AS 各线 after", "34": "AS 各线 after",
    "41": "AS 番外群像", "42": "AS 番外群像",
    "50": "AS おれつば剧场", "51": "AS おれつば剧场", "52": "AS おれつば剧场",
    "53": "AS おれつば剧场", "54": "AS おれつば剧场",
    "61": "AS おまけ", "62": "AS おまけ", "63": "AS おまけ", "64": "AS おまけ",
    "sc": "AS おまけ",
    "sr": None,                   # 0 消息（无文本）
}
# `phase`：schema 只给 `序 / 个人线 / 结局` 三值（为单条恋爱路线设计）。
# 本作是**多 arc 后日谈合集**，故按**标题里的显式标记**机械判定，三值覆盖不到的层一律 null（不臆断）。
PHASE_PREFIXES = {"11", "12", "13", "14", "21", "24"}   # 剧情 arc（可归入三值）
PHASE_ORDER = {"11_1a", "12_1a", "13_1a", "14_1a"}       # 标题「再会　～バーサス…～」= 各 arc 开篇
PHASE_END   = {"11_6a", "12_5a", "13_5b", "14_8a",      # 标题「閉幕　～バーサス…～」= 各 arc 收束
               "24_5b", "24_5c"}                         # 标题「Ｇ－ＥＮＤ」/「Ｂ－ＥＮＤ」

# ---------------------------------------------------------------- 译名替换（同 W6a 消费侧口径）
# §六 排除规则（正则），键 = (原词日文, 旧写法)
# ⚠️ 后三条为 **W6c 实测补充的表外风险排除**（W6a 同款做法：构建器内加排除、逐处留痕、
#    报主代理登记进 `译名统一口径.md` / 作品层术语表 §六；**表本体不改**）。实测证据见产出报告 §6。
EXCL = {
    ("渡来さん", "渡来（裸名）"): re.compile(
        r"渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香|，|、|。|！|？|—|…|是)"),
    ("委員長", "委员长"):        re.compile(r"(?<!执行|審査|审查)委员长"),
    ("ハヤブサ", "隼"):          re.compile(r"(?<!游)隼(?!人)"),
    ("ソラ学", "空学"):          re.compile(r"(?<!美)空学(?!院|府)"),
    ("針生", "针生"):            re.compile(
        r"针生(?!同学|前辈|君|先生|小姐|老师|哥|姐|藏人|长官|長官|，|、|。|！|？|—|…)"),
    ("ガルーダ", "伽楼罗"):      re.compile(r"(?<!伊丹)伽楼罗"),
}
# 行级 JP 门控无法消歧时整条跳过
JP_SKIP = {"ガルーダ": ["伽楼羅"]}
# 语境双轨、须人工复核的规则（照表执行，逐处登记）
CONTEXT_FLAGGED = {"ペガサス", "ドラさん"}

DIR2KIND = {"PIC": "pic", "CHR": "chr", "SE": "se", "BGM": "bgm"}

# `lines[].kind`：schema 枚举为 `title` / `dialogue` / `narration`。
# **本作语料的源 kind 只有 `line` / `title`**（无 dialogue/narration 之分），
# 故按 schema 枚举**机械映射**：`title`→`title`；`line` 且说话人非空→`dialogue`；`line` 且无说话人→`narration`。
# （源值 `line` 的语义在 `speaker`/`speaker_jp` 字段中完整保留，映射无损、可逆。）
KIND_MAP = {"title": "title"}


def map_kind(src_kind, speaker_jp):
    if src_kind == "title":
        return "title"
    return "dialogue" if speaker_jp else "narration"

# 修正表范围内判定：本模块只消费 `source=ota`（其余 source 一律门控排除，逐条留痕）
SCOPE_SOURCE = "ota"

DECL = re.compile(rb"\x01\x01(..)")
LBL  = re.compile(r"^\d{2}_[0-9A-Za-z]+$")
DATE_RE = re.compile(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日")
ZEN = {chr(0xFF10 + i): str(i) for i in range(10)}


def w(s):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()


def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def zen2han(s):
    return "".join(ZEN.get(c, c) for c in s)


# ---------------------------------------------------------------- 跳转标签（本作 .tob 无标签表 → 声明串扫描）
def scan_labels(path):
    raw = open(path, "rb").read()
    labs = []
    for m in DECL.finditer(raw):
        L = struct.unpack("<H", m.group(1))[0]
        if L == 0 or L > 64:
            continue
        d = raw[m.start() + 4:m.start() + 4 + L]
        if len(d) != L or d[-1] != 0:
            continue
        try:
            s = d[:-1].decode("cp932")
        except UnicodeDecodeError:
            continue
        if LBL.match(s) and s not in labs:
            labs.append(s)
    return labs


# ---------------------------------------------------------------- load
w("[1/7] 读取 AS 语料 ...")
ty = json.load(open(TRANSLATION, encoding="utf-8"))
tj = json.load(open(DIALOGUE, encoding="utf-8"))
assert set(ty) == set(tj), "译文.json 与 台词.json 文件集合不一致"
assert len(ty) == 172, "剧本数应为 172，实为 %d" % len(ty)
for f in ty:
    a, b = ty[f]["messages"], tj[f]["messages"]
    assert len(a) == len(b), "消息数不一致: %s" % f
    for x, y in zip(a, b):
        assert (x["kind"], x["index"], x["off"]) == (y["kind"], y["index"], y["off"]), \
            "消息对齐失败: %s idx=%s" % (f, x["index"])
TOT = sum(len(v["messages"]) for v in ty.values())
TOT_LINE = sum(1 for v in ty.values() for m in v["messages"] if m["kind"] == "line")
TOT_TITLE = sum(1 for v in ty.values() for m in v["messages"] if m["kind"] == "title")
w("      剧本 %d ｜ 槽 %d（正文 %d + 标题 %d）" % (len(ty), TOT, TOT_LINE, TOT_TITLE))

choice_rows = json.load(open(CHOICES, encoding="utf-8"))
namelock = json.load(open(NAMELOCK, encoding="utf-8"))
SPK_CN = namelock["speakers"]
ledger = json.load(open(LEDGER, encoding="utf-8"))

# ---------------------------------------------------------------- 修正表
w("[2/7] 装载修正表 ...")
corrections = {}
corr_rows = []
for tname, tpath in TABLES:
    for r in read_tsv(tpath):
        r["_table"] = tname
        corr_rows.append(r)
        key = (r["source"], r["file"], r["locator"])
        if key in corrections:
            raise SystemExit("!! 修正表定位冲突: %s" % (key,))
        corrections[key] = r
w("      合计 %d 条；source 分布 %s" % (len(corr_rows), dict(collections.Counter(r["source"] for r in corr_rows))))
corr_hit = set()

# ---------------------------------------------------------------- 译名替换表
w("[3/7] 装载译名替换表 ...")
TERM_RULES = []
for r in read_tsv(TERM_TABLE):
    new, old = r["新写法"].strip(), r["旧写法"].strip()
    scope = r["适用范围(源代号)"].strip()
    if new.startswith("（") or old.startswith("（") or scope == "—":
        continue                                    # 待裁决 / 非替换项 / 无旧写法残留
    if "/" in scope:
        src, stream = scope.split("/", 1)
    else:
        src, stream = scope, "body"
    if src == "全部":
        continue
    stream = "name" if stream == "name" else "body"
    TERM_RULES.append({"jp": r["原词日文"].strip(), "old": old, "new": new,
                       "src": src, "stream": stream})
w("      可用规则 %d 条（ota/body %d、ota/name %d）"
  % (len(TERM_RULES),
     sum(1 for x in TERM_RULES if x["src"] == "ota" and x["stream"] == "body"),
     sum(1 for x in TERM_RULES if x["src"] == "ota" and x["stream"] == "name")))


def apply_term(cn, jp, src, stream):
    hits = []
    if not cn:
        return cn, hits
    for rule in TERM_RULES:
        if rule["src"] != src or rule["stream"] != stream:
            continue
        if rule["jp"] not in jp:
            continue                                 # JP 门控
        skip = JP_SKIP.get(rule["jp"])
        if skip and any(s in jp for s in skip):
            continue                                 # 行内两原词并存，无法消歧 → 整条跳过
        rx = EXCL.get((rule["jp"], rule["old"]))
        new_cn = rx.sub(rule["new"], cn) if rx is not None else cn.replace(rule["old"], rule["new"])
        if new_cn != cn:
            hits.append({"原词日文": rule["jp"], "旧写法": rule["old"], "新写法": rule["new"],
                         "字段": stream, "before": cn, "after": new_cn,
                         "context_flag": rule["jp"] in CONTEXT_FLAGGED})
            cn = new_cn
    return cn, hits


# ---------------------------------------------------------------- 素材总账 ota 索引
w("[4/7] 建立素材总账 ota 索引 ...")
idx = collections.defaultdict(dict)          # kind -> lower(stem) -> out_relpath
for e in ledger["entries"]:
    if e["source"] == SOURCE:
        idx[e["kind"]][os.path.splitext(e["orig_name"])[0].lower()] = e["out_relpath"]
w("      ota 素材 %d 条 ｜ voice %d ｜ pic %d ｜ chr %d"
  % (sum(len(v) for v in idx.values()), len(idx["voice"]), len(idx["pic"]), len(idx["chr"])))

VOICE_MISJUDGED = set()      # 被解析器误判为 voice 的立绘/其它声明串（逐条留痕）


def map_image(ref):
    parts = ref.replace("/", "\\").split("\\")
    d = parts[0] if len(parts) > 1 else ""
    stem = os.path.splitext(parts[-1])[0].lower()
    kind = DIR2KIND.get(d.upper(), "etc")
    return kind, idx[kind].get(stem)


def map_voice(vid):
    """ota 语音库命中判定；未命中者记入 VOICE_MISJUDGED（不静默丢弃）。"""
    p = idx["voice"].get(vid.lower())
    if p is None:
        VOICE_MISJUDGED.add(vid)
    return p


# ---------------------------------------------------------------- 选择支索引
CHOICE_BY_FILE = collections.defaultdict(list)
for r in choice_rows:
    CHOICE_BY_FILE[r["file"]].append(r)

# ---------------------------------------------------------------- 构建
w("[5/7] 组装 %d 场景 ..." % len(ty))
scene_objs = []
choice_term_hits = []
for file_ in sorted(ty):
    script = file_[:-4]
    prefix = script.split("_")[0]
    msgs_t = ty[file_]["messages"]
    msgs_d = tj[file_]["messages"]

    lines_out, cast, dates, voices = [], [], [], set()
    by_origin, by_base = collections.Counter(), collections.Counter()
    corrections_hit_scene = name_repl_scene = empty_scene = 0
    assets, missing = [], []
    seen_asset = set()

    for i, (mt, md) in enumerate(zip(msgs_t, msgs_d), 1):
        idx_ = mt["index"]
        jp = mt["jp"] or ""
        cn = mt["cn"] or ""
        speaker_jp = mt["speaker"] or ""
        speaker_cn = SPK_CN.get(speaker_jp, speaker_jp)
        voice = mt["voice"] or ""

        # ---- ① 取文（本模块单一取文源 = ota 语料本身，无跨源对齐）
        empty_slot = (not jp and not cn)
        base = "empty" if empty_slot else SOURCE
        align = "empty_slot" if empty_slot else "new_scene_direct"
        if empty_slot:
            empty_scene += 1
        layers = [] if empty_slot else [base]

        # ---- ② 修正表（(source,file,locator) 三元组定位 + source↔cn_base 门控）
        fix_refs = []
        if idx_ is not None:
            loc = "idx=%d" % idx_
            row = corrections.get((SOURCE, file_, loc))
            if row is not None:
                want = CORR_SOURCE_TO_BASE.get(row["source"])
                if want is None:
                    raise SystemExit("!! 修正表 source 未登记门控映射: %s @ %s/%s"
                                     % (row["source"], file_, loc))
                # `term_unify` 与取文层无关 ⇒ 不受来源门控约束（见 `修正\_README.md` §四.5）
                if want == base or row["fix_type"] == "term_unify":
                    cn_before = cn
                    if row["fix_type"] == "term_unify":
                        # ISSUE-20260930-12：`term_unify` 是**词形级替换**——`old_text` = 词形正则、
                        # `new_text` = 替换值（**不是整句**）。命中即 re.sub；已是后态 ⇒ 幂等 no-op
                        # （不记 fix_refs、不计命中）；两者都不是 ⇒ fail loud。
                        cn, tu_state = _term_unify.apply(cn, row["old_text"], row["new_text"])
                    else:
                        # old_text 逐字符断言（与其余构建器同口径）：不符即 fail loud
                        if (row.get("old_text") or "") != (cn_before or ""):
                            raise SystemExit("!! 修正表 old_text 与源译文不符: %s/%s（源=%r 表=%r）"
                                             % (file_, loc, cn_before, row.get("old_text")))
                        tu_state = _term_unify.APPLIED
                        cn = row["new_text"]
                    if tu_state == _term_unify.NOOP:
                        TERM_NOOP.append({"table": row["_table"], "source": row["source"],
                                          "file": row["file"], "locator": loc,
                                          "old_text": row["old_text"], "new_text": row["new_text"]})
                    else:
                        o = "retranslate" if row["fix_type"] == "retranslate" else "fix_table"
                        layers.append(o)
                        fix_refs.append({"table": row["_table"], "locator": loc,
                                         "fix_type": row["fix_type"], "cn_before": cn_before})
                        corrections_hit_scene += 1
                        corr_hit.add((SOURCE, file_, loc))
                else:
                    GATED.append({
                        "table": row["_table"], "source": row["source"], "file": file_,
                        "locator": loc, "kind": row["kind"], "fix_type": row["fix_type"],
                        "script": script, "seq": i, "cn_base": base, "jp": jp,
                        "cn_kept": cn, "cn_gated": row["new_text"], "old_text": row["old_text"],
                        "reason": "source_gate: 条目 source=%s 对应取文基准 %s，而该行取文基准为 %s "
                                  "→ 不生效（不得用该层覆盖现取文）" % (row["source"], want, base)})
        # 范围外 source（otr/otp）的条目在本模块无对象 → 统一在 [6/7] 范围对账里逐条留痕

        # ---- ③ 译名替换（JP 门控；body 作用于 cn，name 作用于名字框）
        cn, h1 = apply_term(cn, jp, SOURCE, "body")
        speaker_cn, h2 = apply_term(speaker_cn, speaker_jp, SOURCE, "name")
        term_hits = h1 + h2
        if term_hits:
            layers.append("name_replace")
            name_repl_scene += len(term_hits)

        # ---- cn_origin：生效层中优先级最高者（name_replace 不改变取文来源）
        if not layers:
            origin = "empty"
        else:
            origin = base
            if "fix_table" in layers:
                origin = "fix_table"
            if "retranslate" in layers:
                origin = "retranslate"
        by_origin[origin] += 1
        by_base[base] += 1

        # ---- 语音
        audio = []
        if voice:
            voices.add(voice)
            p = map_voice(voice)
            if p:
                audio.append(p)

        # ---- 图像（逐消息 image → 场景级并集）
        img = md.get("image")
        if img and img not in seen_asset:
            seen_asset.add(img)
            k, p = map_image(img)
            assets.append({"ref": img, "kind": k, "out_relpath": p, "hit": bool(p)})
            if not p:
                missing.append(img)

        # ---- cast
        if mt["kind"] != "title":
            nm = speaker_cn if speaker_cn else "旁白"
            if nm not in cast:
                cast.append(nm)

        lines_out.append({
            "seq": i, "index": idx_, "lineno": i,
            "kind": map_kind(mt["kind"], speaker_jp),
            "speaker": speaker_cn, "speaker_jp": speaker_jp, "voice": voice,
            "jp": jp, "cn": cn, "cn_origin": origin, "cn_base": base,
            "align_method": align, "layers": layers, "fix_refs": fix_refs,
            "name_replaced": term_hits, "empty_slot": empty_slot,
            "d14_exception": None, "audio": audio,
        })

    # ---- 标题
    titles = [l for l in lines_out if l["kind"] == "title"]
    prim = titles[-1] if titles else None
    title_variants = [{"offset": msgs_t[t["seq"] - 1]["off"], "jp": t["jp"],
                       "cn": t["cn"], "cn_origin": t["cn_origin"]} for t in titles]

    # ---- 日期（仅显式 ○月○日）
    for l in lines_out:
        for m in DATE_RE.finditer(l["jp"] or ""):
            s = zen2han(m.group(0))
            mm, dd = s.split("月")
            d = "%02d/%02d" % (int(mm), int(dd.rstrip("日")))
            if d not in [x["date"] for x in dates]:
                dates.append({"date": d, "line_index": l["index"]})

    # ---- 后继（声明串扫描）
    labs = scan_labels(os.path.join(AS_RAW, file_))
    nxt = sorted(l.lower() for l in labs)
    nk = "end" if not nxt else ("linear" if len(nxt) == 1 else "branch")

    # ---- 选择支（`语料\选择支补译.json`；资源/语音 ID 型选项 skip）
    # 选项译文同样过**译名替换层**（JP 门控用 `text_jp`），以保 D3 口径与正文一致；
    # 译名替换不改取文来源层，故 `cn_origin` 仍为 `ota`，替换明细记入 `evidence`（schema 无专用字段）。
    choices = []
    for r in CHOICE_BY_FILE.get(file_, []):
        for o in r["options"]:
            if o.get("skip"):
                continue
            t_cn = o.get("cn")
            t_cn, t_hits = apply_term(t_cn, o["jp"], SOURCE, "body")
            ev = ("%s#idx%d 选项标签声明串实测存在（off=%s）；候选目标 %s；"
                  "选项↔目标配对未逆向（TOB0 分支语义未逆向，总纲 §六 R1）"
                  % (file_, r["idx"], o.get("off"), "/".join(x.upper() for x in nxt) or "无"))
            if t_hits:
                ev += "；译名替换：" + "、".join("%s→%s" % (h["旧写法"], h["新写法"]) for h in t_hits)
                choice_term_hits.extend(
                    {"script": script, "text_jp": o["jp"], "old": h["旧写法"], "new": h["新写法"]}
                    for h in t_hits)
            choices.append({
                "text_jp": o["jp"], "text_cn": t_cn, "cn_origin": SOURCE if t_cn else None,
                "target": None, "pairing_verified": False, "confirmed": True,
                "evidence": ev})

    # ---- phase / route
    route = ROUTE_BY_PREFIX.get(prefix, None)
    if script in PHASE_ORDER:
        phase = "序"
    elif script in PHASE_END:
        phase = "结局"
    elif prefix in PHASE_PREFIXES:
        phase = "个人线"
    else:
        phase = None

    scene_objs.append({
        "scene_id": "%s_%s" % (SOURCE, script),
        "source": SOURCE, "script": script,
        "source_kind": "new",              # 本模块单一类别：AS 独立翻译，无 2009 对照（见报告）
        "text_source": SOURCE,             # 单一取文源 ota → 恒为 ota，无 mixed
        "title_jp": prim["jp"] if prim else None,
        "title_cn": prim["cn"] if prim else None,
        "title_variants": title_variants,
        "game_date": dates[0]["date"] if dates else None,
        "game_dates": dates,
        "phase": phase, "route": route,
        "cast": cast, "next": nxt, "next_kind": nk, "choices": choices,
        "line_count": len(lines_out),
        "voice_count": len(voices),
        "assets": assets, "assets_missing": missing,
        "stats": {
            "lines_by_origin": dict(by_origin),
            "lines_by_source": dict(by_base),
            "corrections_hit": corrections_hit_scene,
            "name_replace_count": name_repl_scene,
            "empty_slots": empty_scene,
            "d14_exceptions": 0,
        },
        "lines": lines_out,
    })

# ---------------------------------------------------------------- 范围对账
w("[6/7] 自检 / 范围对账 ...")
in_scope = [r for r in corr_rows if r["source"] == SCOPE_SOURCE]
out_scope = [r for r in corr_rows if r["source"] != SCOPE_SOURCE]
gated_full = set((g["source"], g["file"], g["locator"]) for g in GATED)
miss = [(r["_table"], r["source"], r["file"], r["locator"], r["fix_type"]) for r in in_scope
        if (r["source"], r["file"], r["locator"]) not in corr_hit
        and (r["source"], r["file"], r["locator"]) not in gated_full]
# 范围外条目必须逐条留痕（本模块不消费，非漏修）
out_rows = [{"table": r["_table"], "source": r["source"], "file": r["file"],
             "locator": r["locator"], "kind": r["kind"], "fix_type": r["fix_type"],
             "reason": "本模块 source=%s，该条目 source=%s → 由对应源模块消费，本模块无对象"
                       % (SOURCE, r["source"])} for r in out_scope]

tot_lines = sum(s["line_count"] for s in scene_objs)
orig_dist, base_dist = collections.Counter(), collections.Counter()
for s in scene_objs:
    for k, v in s["stats"]["lines_by_origin"].items():
        orig_dist[k] += v
    for k, v in s["stats"]["lines_by_source"].items():
        base_dist[k] += v
a_tot = sum(len(s["assets"]) for s in scene_objs)
a_hit = sum(1 for s in scene_objs for a in s["assets"] if a["hit"])
v_ref = sum(1 for s in scene_objs for l in s["lines"] if l["voice"])
v_hit = sum(1 for s in scene_objs for l in s["lines"] if l["audio"])

# 独立引号判据复核（「原文含「」 ⇒ 译文须含“”」）
quote_hits = []
for s in scene_objs:
    for l in s["lines"]:
        if ("「" in (l["jp"] or "") or "」" in (l["jp"] or "")) and \
           ("“" not in (l["cn"] or "") and "”" not in (l["cn"] or "")):
            quote_hits.append({"script": s["script"], "index": l["index"], "kind": l["kind"],
                               "jp": l["jp"], "cn": l["cn"]})

# 语音误判（立绘名被当作 voice）
voice_missing = [{"script": s["script"], "seq": l["seq"], "voice": l["voice"],
                  "is_chr_stem": l["voice"].lower() in idx["chr"]}
                 for s in scene_objs for l in s["lines"]
                 if l["voice"] and not l["audio"]]

report = {
    "module": "W6c", "source": SOURCE,
    "scenes": len(scene_objs),
    "lines_total": tot_lines,
    "lines_baseline_as_corpus": TOT,
    "lines_baseline_body": TOT_LINE,
    "lines_baseline_title": TOT_TITLE,
    "orig_dist": dict(orig_dist),
    "base_dist": dict(base_dist),
    "corrections_total": len(corr_rows),
    "corrections_in_scope_ota": len(in_scope),
    "corrections_hit_in_scope": len(in_scope) - len(miss) - len([g for g in GATED if g["source"] == SCOPE_SOURCE]),
    "corrections_missing_in_scope": miss,
    "corrections_gated_count": len(GATED),
    "corrections_gated_out": GATED,
    # ISSUE-20260930-12：`term_unify` 的幂等 no-op 留痕（构建期应为 0——每个目标槽都应命中词形）
    "term_unify_noop": TERM_NOOP,
    "corrections_out_of_scope": out_rows,
    "corrections_out_of_scope_by_source": dict(collections.Counter(r["source"] for r in out_scope)),
    "quote_gate_hits": quote_hits,
    "quote_gate_hit_count": len(quote_hits),
    "assets_total": a_tot, "assets_hit": a_hit,
    "voice_refs": v_ref, "voice_hit": v_hit,
    "voice_missing": voice_missing,
    "voice_missing_distinct": sorted(set(x["voice"] for x in voice_missing)),
    "voice_missing_distinct_count": len(set(x["voice"] for x in voice_missing)),
    "term_hits": sum(s["stats"]["name_replace_count"] for s in scene_objs),
    "empty_slots": sum(s["stats"]["empty_slots"] for s in scene_objs),
    "next_kind_dist": dict(collections.Counter(s["next_kind"] for s in scene_objs)),
    "phase_dist": dict(collections.Counter(str(s["phase"]) for s in scene_objs)),
    "route_dist": dict(collections.Counter(str(s["route"]) for s in scene_objs)),
    "choices_scenes": sum(1 for s in scene_objs if s["choices"]),
    "choices_total": sum(len(s["choices"]) for s in scene_objs),
    "choice_records_total": len(choice_rows),
    "choice_records_prompts": sum(1 for r in choice_rows if r["prompt"]),
    "choice_options_total": sum(len(r["options"]) for r in choice_rows),
    "choice_options_skipped": sum(1 for r in choice_rows for o in r["options"] if o.get("skip")),
    "choice_term_hits": choice_term_hits,
    "scenes_with_date": [{"script": s["script"], "date": s["game_date"]} for s in scene_objs if s["game_date"]],
    "empty_scene_scripts": [s["script"] for s in scene_objs if not s["lines"]],
    "align_method_dist": dict(collections.Counter(
        l["align_method"] for s in scene_objs for l in s["lines"])),
    "name_replace_all": [{"script": s["script"], "seq": l["seq"], "field": h["字段"],
                          "原词日文": h["原词日文"], "旧写法": h["旧写法"], "新写法": h["新写法"],
                          "before": h["before"], "after": h["after"],
                          "context_flag": h["context_flag"], "jp": l["jp"]}
                         for s in scene_objs for l in s["lines"] for h in l["name_replaced"]],
    "per_scene": [{
        "script": s["script"], "route": s["route"], "phase": s["phase"],
        "title_jp": s["title_jp"], "line_count": s["line_count"],
        "voice_count": s["voice_count"], "next": s["next"], "next_kind": s["next_kind"],
        "choices": len(s["choices"]), "cast": s["cast"],
        "assets_total": len(s["assets"]), "assets_hit": sum(1 for a in s["assets"] if a["hit"]),
        "corrections_hit": s["stats"]["corrections_hit"],
        "name_replace_count": s["stats"]["name_replace_count"],
        "lines_by_origin": s["stats"]["lines_by_origin"],
        "empty_slots": s["stats"]["empty_slots"],
    } for s in scene_objs],
}
report["lines_balanced"] = (tot_lines == TOT)
report["scene_ids_unique"] = (len(set(s["scene_id"] for s in scene_objs)) == len(scene_objs))
report["corrections_all_in_scope_hit"] = (len(miss) == 0)
report["quote_gate_all_hit"] = (len(quote_hits) == 0)

os.makedirs(STG, exist_ok=True)
json.dump(report, open(os.path.join(STG, "_build_stats_ota.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 写出
w("[7/7] 写出 scene_ota.jsonl ...")
_assert_in_checkout(OUT, "剧本产物目录")
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "scene_ota.jsonl")
_assert_in_checkout(outpath, "scene_ota.jsonl")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    for s in scene_objs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
with open(outpath, encoding="utf-8") as f:
    n = sum(1 for ln in f if json.loads(ln))
w("      -> %s （%d 行，逐行 json.loads OK）" % (outpath, n))

# ---------------------------------------------------------------- 摘要
w("")
w("================ 摘要 ================")
w("场景数            : %d" % report["scenes"])
w("行数              : %d  (AS 语料基线 %d；正文 %d + 标题 %d；守恒=%s)"
  % (tot_lines, TOT, TOT_LINE, TOT_TITLE, report["lines_balanced"]))
w("cn_origin 分布    : %s" % report["orig_dist"])
w("cn_base 分布      : %s" % report["base_dist"])
w("修正表            : 合计 %d ｜ source=ota 范围内 %d ｜ 命中 %d ｜ 门控排除 %d ｜ 未命中 %d"
  % (len(corr_rows), len(in_scope),
     report["corrections_hit_in_scope"], len([g for g in GATED if g["source"] == SCOPE_SOURCE]), len(miss)))
w("  未命中(范围内)  : %s" % (miss or "无"))
w("term_unify 幂等 no-op: %d 条（构建期应为 0）%s"
  % (len(TERM_NOOP), (" ← " + str(TERM_NOOP[:3])) if TERM_NOOP else ""))
w("  范围外(逐条)    : %s" % report["corrections_out_of_scope_by_source"])
w("引号判据复核      : 命中 %d（应为 7，全部由修正表覆盖）" % report["quote_gate_hit_count"])
w("选择支            : %d 场景 / %d 条选项（记录 %d、提示 %d、选项槽 %d、skip %d）"
  % (report["choices_scenes"], report["choices_total"], report["choice_records_total"],
     report["choice_records_prompts"], report["choice_options_total"],
     report["choice_options_skipped"]))
w("素材命中          : 图像 %d/%d" % (a_hit, a_tot))
w("语音命中          : %d/%d ｜ 未命中 %d 个不同 ID（立绘误判）"
  % (v_hit, v_ref, report["voice_missing_distinct_count"]))
w("译名替换处数      : %d" % report["term_hits"])
w("空槽              : %d ｜ 0 消息场景 %s" % (report["empty_slots"], report["empty_scene_scripts"]))
w("next_kind 分布    : %s" % report["next_kind_dist"])
w("phase 分布        : %s" % report["phase_dist"])
w("有显式日期场景    : %s" % report["scenes_with_date"])
w("scene_id 唯一     : %s" % report["scene_ids_unique"])