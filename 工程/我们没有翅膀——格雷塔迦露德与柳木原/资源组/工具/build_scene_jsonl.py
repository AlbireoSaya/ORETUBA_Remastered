# -*- coding: utf-8 -*-
r"""
W6a/W6a2 · 结构化剧本 scene.jsonl 构建器（亚衣线 s03c · 55 场景）

契约：`资源组\修正\_README.md` §四/§八（取文顺序）与 **§四.5（修正表来源门控）**、
      `资源组\剧本\schema.md`（本模块 schema 定稿）。
只读：工程\我们没有翅膀\、工程\我们没有翅膀R\、资源组\修正\*、资源组\krkr素材库\*
只写：资源组\剧本\scene.jsonl、子代理工作区\ISSUE-20260918-06\W6a2\_build_stats.json

W6a2 修订（主代理裁决落地）：
  ① 修正表按 `source` ↔ 取文基准层 `cn_base` **通用门控**（非标题特例开关）——共享场景整场取本篇时，
     `source=otr` 的条目不再覆盖本篇译文；被门控条目逐条留痕（`corrections_gated_out`），不静默丢弃。
  ② `s03c_01d` 选择支 `黙る`/`拒否る` 补译（`沉默`/`拒绝`），标注 `cn_origin=fix_table`；
     `target` 仍为 `null`（配对未逆向，不猜）。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_jsonl.py"
"""
import json, os, re, csv, collections, sys, hashlib

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
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6a2")   # 写本 checkout
R    = os.path.join(DATA_ROOT, r"工程\我们没有翅膀R")
OT   = os.path.join(DATA_ROOT, r"工程\我们没有翅膀\汉化\剧情汉化")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

COMPARE = os.path.join(R, r"亜衣线资源\剧本\台词对照.json")
MANIFEST = os.path.join(R, r"亜衣线资源\清单\素材清单.json")
TOBDIR  = os.path.join(R, r"亜衣线资源\剧本")
AUDIT   = os.path.join(FIX, "s03c_行对齐审计.json")
LEDGER  = os.path.join(RES, r"krkr素材库\资源总账.json")

TABLES = [
    ("修正表_B1B3.tsv",        os.path.join(FIX, "修正表_B1B3.tsv")),
    ("修正表_B1B3_扩展.tsv",   os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    ("修正表_新增场景mig重译.tsv", os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260930-10：用户 2026-09-30 术语裁决（source 按行门控；field=cn，fix_type=term_unify）
    ("修正表_裁决20260930.tsv",    os.path.join(FIX, "修正表_裁决20260930.tsv")),
    # ISSUE-20261009-04：用户 2026-10-09 裁决「奈落」全量回改（source=otr，3 条，field=cn）。
    #   ★ 这 3 行 cn_base=ot（D14 共有场景整场取本篇）——`source=otr` 的整句条目会被 §四.5 来源门控
    #     排除，而本模块只按 (SOURCE=otr,file,locator) 查表、`source=ot` 条目无消费路径；
    #     故这 3 条用 `fix_type=term_unify`（词形级「地狱」→「奈落」，不受来源门控约束，_README §三.3）。
    ("修正表_奈落.tsv",            os.path.join(FIX, "修正表_奈落.tsv")),
]
TERM_TABLE = os.path.join(FIX, "译名替换表.tsv")

ROUTE = "s03c 亚衣线"
SOURCE = "otr"

# ---------------------------------------------------------------- 修正表来源门控（W6a2 · 通用规则）
# 契约：`资源组\修正\_README.md` §四.5（对后续所有源模块生效）。
# 裁决：**修正表条目只在其 `source` 与该行「取文基准层」(`cn_base`) 对应时才生效。**
#   理由：条目 `source` 标的是「这条修正所针对的语料层」；若该行实际取文并非来自该层
#   （如共有场景按 D14 整场取本篇），则该条修正无对象、不得覆盖——否则会用 R 版侧重译
#   顶掉本篇译文。规则对**所有 kind 一律适用**（非标题特例），逐条留痕可审计。
CORR_SOURCE_TO_BASE = {
    "otr": "otr_new",   # R 版语料（本项目新译 / mig 重译）→ 取文基准 otr_new
    "otp": "otp",       # 前奏诗（该源模块产出 scene.jsonl 时其取文基准层记作 otp）
    "ota": "ota",       # After Story（同上）
    "ot":  "ot",        # 本篇
    # 六源全覆盖（ISSUE-20260930-11 补齐 otv/np —— 缺项会让装载该表的本次运行直接 fail loud）
    "otv": "otv",
    "np":  "np",
}
GATED = []              # 被来源门控排除的条目（逐条留痕，不得静默丢弃）
TERM_NOOP = []          # `term_unify` 的幂等 no-op 留痕（ISSUE-20260930-12；构建期应为 0 条）

# s03c_01d 选择支补译（主代理裁决；W7 诊断口径）。
# 选择支串不在消息表中 → 语料无译文；此表为**唯一译文来源**，其余仍不得擅译。
CHOICE_CN = {
    "s03c_01d": {"黙る": "沉默", "拒否る": "拒绝"},
}

# ---------------------------------------------------------------- helpers

def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def w(s):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()

# ---------------------------------------------------------------- U+3000 归一化
# 规则出处：`.zcode\skills\galgame-translation\SKILL.md`
#   §七.6「**全角空格（U+3000）一律删除**，不得用于中文缩进」；
#   §八 自检项「**无 `　`（U+3000）残留**」。
# 背景（实测）：otr 的 U+3000 全部来自 R 版译文——`台词对照.json` 的 `cn`/`cn_full`
#   （D14：新场景取 R 版文本），原样带出段落缩进式全角空格。
# 归一化点选在「修正表层②之后、译名替换层③之前」：
#   ① 覆盖真正的携带者（取文层）与修正表注入（`new_text` 中亦存在 U+3000）；
#   ② 译名替换表的 `旧写法`/`新写法` 实测均不含 U+3000（0 条），故③不可能再引入；
#   ③ 归一化先于③，`name_replaced.after` 审计日志与最终 `cn` 逐字节一致，不产生假差异。
# 约束：**只删 U+3000，不改任何其它字符**（不碰标点、不碰其它空白）；
#   `jp` 为原文，**绝不归一化**。幂等：按字面删除，重复执行结果不变（无回扫副作用）。
U3000 = "\u3000"
U3000_STATS = {"body_slots": 0, "body_chars": 0, "title_slots": 0, "title_chars": 0}

def strip_u3000(s, kind="body"):
    """删除字符串中的全部 U+3000；返回新串并累计审计计数。"""
    if not s or U3000 not in s:
        return s
    n = s.count(U3000)
    U3000_STATS["%s_slots" % kind] += 1
    U3000_STATS["%s_chars" % kind] += n
    return s.replace(U3000, "")

# ---------------------------------------------------------------- load inputs

w("[1/8] 读取输入 ...")
compare = json.load(open(COMPARE, encoding="utf-8"))
scenes_raw = compare["scenes"]
meta_cmp = compare["meta"]
audit = json.load(open(AUDIT, encoding="utf-8"))
A = audit["meta"]
SHARED = list(A["shared_scenes"])            # 21
BRANCH = dict(A["branch_scenes"])            # {branch: parent}
NEW    = list(A["new_scenes"])               # 31
assert len(SHARED) + len(BRANCH) + len(NEW) == 55

audit_by = {}                                # (file, index) -> audit rec
for x in audit["lines"]:
    if x.get("index") is not None:
        audit_by[(x["file"], x["index"])] = x

# 本篇 s03c jsonl 的 jp->cn 兜底表（用于 audit 未覆盖的无 index 槽，如标题槽）
OT_DIR = OT
def load_ot_scene(script):
    p = os.path.join(OT_DIR, script + ".sob.jsonl")
    if not os.path.isfile(p):
        return {}
    m = collections.defaultdict(list)
    for ln in open(p, encoding="utf-8"):
        o = json.loads(ln)
        if (o.get("jp") or "").strip():
            m[o["jp"]].append(o.get("cn") or "")
    return m

manifest = json.load(open(MANIFEST, encoding="utf-8"))
ledger = json.load(open(LEDGER, encoding="utf-8"))

w("      场景 %d ｜ audit 行 %d ｜ 素材清单 per_file %d ｜ 总账 %d"
  % (len(scenes_raw), len(audit["lines"]), len(manifest["per_file"]), len(ledger["entries"])))

# ---------------------------------------------------------------- correction tables

w("[2/8] 装载修正表 ...")
corrections = {}          # (source,file,locator) -> row
corr_rows = []
for tname, tpath in TABLES:
    for r in read_tsv(tpath):
        r["_table"] = tname
        corr_rows.append(r)
        key = (r["source"], r["file"], r["locator"])
        if key in corrections:
            raise SystemExit("!! 修正表定位冲突: %s" % (key,))
        corrections[key] = r
w("      修正表合计 %d 条（B1B3=%d / 扩展=%d / 新增mig重译=%d）"
  % (len(corr_rows),
     sum(1 for r in corr_rows if r["_table"] == "修正表_B1B3.tsv"),
     sum(1 for r in corr_rows if r["_table"] == "修正表_B1B3_扩展.tsv"),
     sum(1 for r in corr_rows if r["_table"] == "修正表_新增场景mig重译.tsv")))
corr_hit = set()

# ---------------------------------------------------------------- 0x5C 切分缺陷（W7-4）
# 本模块的 `speaker_jp` / `voice` 取自 **R 版 TOB 串表**（`亜衣线资源\剧本\台词对照.json`
# ← `语料\R版台词.json` ← `tob_extract.py` 的 `parse_string`，长度前缀独立解码），
# **不经过** `extract_sob0.py` 的 `#<说话人>\<语音ID>$&` 字节切分 → **不受 0x5C 缺陷影响**，
# 故不消费 `修正表_0x5C.tsv`。共享场景从本篇取得的只有 `cn` 正文，与 speaker/voice 无关。
# 实证：s03c_03c.tob 说话人 `クソ長い髪の女`（含 `ソ`=cp932 0x835C）在本模块产物中完整无损。
# 以下为 fail-loud 防回归：若该表出现非 ot 条目（即落到本模块取文层），立即中止。
SPLIT_TABLE = os.path.join(FIX, "修正表_0x5C.tsv")
if os.path.isfile(SPLIT_TABLE):
    _sp = read_tsv(SPLIT_TABLE)
    _bad = [r for r in _sp if r["source"] != "ot"]
    if _bad:
        raise SystemExit("!! 修正表_0x5C 含非 ot 条目，本模块取文层可能受影响: %s"
                         % [r["locator"] for r in _bad])
    w("      修正表_0x5C：%d 条 source=ot（scene_ot 专属）；本模块 speaker/voice 取自 R 版 TOB 串表"
      "（字节安全）→ 不消费，不受 0x5C 切分缺陷影响" % len(_sp))

# ---------------------------------------------------------------- name replacement table

w("[3/8] 装载译名替换表 ...")
term_rows = read_tsv(TERM_TABLE)
TERM_RULES = []
for r in term_rows:
    new = r["新写法"].strip()
    old = r["旧写法"].strip()
    scope = r["适用范围(源代号)"].strip()
    if new.startswith("（") or old.startswith("（") or scope == "—":
        continue                      # 待裁决 / 非替换项 / 无旧写法残留
    if "/" in scope:
        src, stream = scope.split("/", 1)
    else:
        src, stream = scope, "body"
    if src == "全部":
        continue                      # 全源条目实测旧写法残留 0，无替换面
    stream = "name" if stream == "name" else "body"
    TERM_RULES.append({"jp": r["原词日文"].strip(), "old": old, "new": new,
                       "src": src, "stream": stream, "table_note": r["备注"].strip()})
w("      可用替换规则 %d 条（已剔除待裁决/非替换项/无旧写法残留/全源）" % len(TERM_RULES))

# §六 排除规则（正则），键 = (原词日文, 旧写法)
EXCL = {
    ("渡来さん", "渡来（裸名）"): re.compile(r"渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香)"),
    ("委員長", "委员长"):        re.compile(r"(?<!执行)委员长"),
    ("ハヤブサ", "隼"):          re.compile(r"(?<!游)隼(?!人)"),
    ("ソラ学", "空学"):          re.compile(r"(?<!美)空学(?!院|府)"),
    # W6a 实测补充 ①：裸「针生」→「针生同学」会在已含敬称处产生「针生同学同学」「针生同学前辈」等叠词
    # （s03c_12b 实测 2 处），故排除其后已跟敬称的情形。建议表维护方把本条补入 译名统一口径 §六。
    ("針生", "针生"):            re.compile(r"针生(?!同学|前辈|君|先生|小姐|老师|哥|姐)"),
    # W6a 实测补充 ②：`ガルーダ` 行会把「伊丹伽楼罗」（＝伽楼羅）误改成「伊丹伽鲁炟」
    # （s03c_03b#216 实测；jp 同时含 ガルーダ 与 伽楼羅）。按口径「必须先按日文原词拆分」，
    # 此处排除「伊丹伽楼罗」；行级 JP 门控无法消歧的，另见 JP_SKIP。
    ("ガルーダ", "伽楼罗"):      re.compile(r"(?<!伊丹)伽楼罗"),
}
# 行级 JP 门控无法消歧时整条跳过：jp 同时含这些串 → 该原词的正文出现属另一原词，不得替换
JP_SKIP = {
    "ガルーダ": ["伽楼羅"],
}
# 语境双轨、须人工复核的规则（照表执行，但逐处登记供复核）
CONTEXT_FLAGGED = {"ペガサス", "ドラさん"}

# ---------------------------------------------------------------- ledger index (otr)

w("[4/8] 建立素材总账 otr 索引 ...")
otr_index = collections.defaultdict(dict)     # kind -> lower(stem) -> out_relpath
for e in ledger["entries"]:
    if e["source"] != SOURCE:
        continue
    stem = os.path.splitext(e["orig_name"])[0].lower()
    otr_index[e["kind"]][stem] = e["out_relpath"]

DIR2KIND = {"CHR": "chr", "PIC": "pic", "SE": "se", "BGM": "bgm", "VOICE": "voice"}

def map_asset_ref(ref):
    """素材清单引用 'CHR\\AI_01.ELG' -> (kind, out_relpath|None)"""
    d, fn = ref.split("\\") if "\\" in ref else ("", ref)
    stem = os.path.splitext(fn)[0].lower()
    kind = DIR2KIND.get(d.upper(), "etc")
    return kind, otr_index.get(kind, {}).get(stem)

def map_voice(vid):
    info = manifest["voices"].get(vid)
    if not info:
        return None
    stem = os.path.splitext(info["file"])[0].lower()
    return otr_index["voice"].get(stem)

# ---------------------------------------------------------------- jump labels (next)

w("[5/8] 扫描跳转标签 ...")
LABEL_RE = re.compile(rb"S03C_[0-9A-Z]+")
next_map = {}
for fn in sorted(os.listdir(TOBDIR)):
    if not fn.endswith(".tob"):
        continue
    raw = open(os.path.join(TOBDIR, fn), "rb").read()
    labs = []
    for m in LABEL_RE.findall(raw):
        s = m.decode("ascii")
        if s not in labs:
            labs.append(s)
    # 跳转目标是无序集合（声明顺序不代表分支顺序），排序以保证确定性
    next_map[os.path.splitext(fn)[0]] = sorted(s.lower() for s in labs)

# 已确证的玩家选择支（脚本内选择支串 + 跳转标签），W6a 实测
CHOICE_JP = {"s03c_01d": ["黙る", "拒否る"]}

# ---------------------------------------------------------------- date scan

DATE_RE = re.compile(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日")
ZEN = {chr(0xFF10 + i): str(i) for i in range(10)}

def zen2han(s):
    return "".join(ZEN.get(c, c) for c in s)

def scan_dates(lines):
    out = []
    for l in lines:
        for m in DATE_RE.finditer(l["jp"] or ""):
            s = zen2han(m.group(0))
            mm, dd = s.split("月")
            d = "%02d/%02d" % (int(mm), int(dd.rstrip("日")))
            out.append({"date": d, "line_index": l["index"]})
    # 去重保序
    seen, res = set(), []
    for x in out:
        if x["date"] not in seen:
            seen.add(x["date"]); res.append(x)
    return res

# ---------------------------------------------------------------- resolve one line

ORIGIN_RANK = {"empty": 0, "ot": 1, "otr_new": 1, "name_replace": 2, "fix_table": 3, "retranslate": 4}

def apply_term(cn, jp, src, stream):
    """返回 (new_cn, [命中的替换记录])"""
    hits = []
    if not cn:
        return cn, hits
    for rule in TERM_RULES:
        if rule["src"] != src or rule["stream"] != stream:
            continue
        if rule["jp"] not in jp:
            continue                                   # JP 门控
        skip = JP_SKIP.get(rule["jp"])
        if skip and any(s in jp for s in skip):
            continue                                   # 行内两原词并存，无法消歧 → 整条跳过
        rx = EXCL.get((rule["jp"], rule["old"]))
        if rx is not None:
            new_cn = rx.sub(rule["new"], cn)
        else:
            new_cn = cn.replace(rule["old"], rule["new"])
        if new_cn != cn:
            hits.append({"原词日文": rule["jp"], "旧写法": rule["old"],
                         "新写法": rule["new"], "字段": stream,
                         "before": cn, "after": new_cn,
                         "context_flag": rule["jp"] in CONTEXT_FLAGGED})
            cn = new_cn
    return cn, hits

def build_scene(sc):
    script = sc["file"][:-4]                        # s03c_01a
    file_ = sc["file"]
    if script in SHARED:
        kind = "shared"
    elif script in BRANCH:
        kind = "branch"
    elif script in NEW:
        kind = "new"
    else:
        raise SystemExit("!! 未分类场景: " + script)

    ot_map = load_ot_scene(script) if kind in ("shared", "branch") else {}
    r_jp_count = collections.Counter((l["jp"] or "") for l in sc["lines"] if (l["jp"] or "").strip())

    lines_out = []
    cast = []
    dates = scan_dates(sc["lines"])
    voices = set()
    corrections_hit_scene = 0
    name_repl_scene = 0
    d14_exc_scene = 0
    empty_scene = 0
    by_origin = collections.Counter()
    by_src = collections.Counter()

    for i, l in enumerate(sc["lines"], 1):
        idx, off = l["index"], l["offset"]
        jp = l["jp"] or ""
        speaker_jp = l.get("speaker_jp") or ""
        speaker_cn = l.get("speaker_cn") or ""
        a = audit_by.get((file_, idx)) if idx is not None else None

        # ---- ① 取文
        d14_exc = None
        empty_slot = False
        fix_refs = []
        align = None
        if kind in ("shared", "branch") and a and (a.get("correct_cn_from_2009") or "").strip():
            cn = a["correct_cn_from_2009"]
            base = "ot"
            align = "audit"
        else:
            cn = l.get("cn_full") or l.get("cn") or ""
            base = "otr_new"
            align = "new_scene_direct" if kind == "new" else ("audit_empty" if (a is not None) else "no_audit_entry")
            # 兜底：audit 未覆盖的槽（无 index，如标题槽），按 jp 精确唯一匹配取本篇译文
            if kind in ("shared", "branch") and jp.strip() and cn:
                cand = ot_map.get(jp)
                if cand and len(cand) == 1 and r_jp_count[jp] == 1 and (cand[0] or "").strip():
                    cn = cand[0]
                    base = "ot"
                    align = "jp_exact_fallback"
        if not jp and not cn:
            empty_slot = True
            base = "empty"
            align = "empty_slot"
            empty_scene += 1
        layers = [] if base == "empty" else [base]

        # ---- ② 修正表（(source,file,locator) 三元组定位，再按 source↔cn_base 门控）
        # 除 `offset=<消息表地址>` 外，另支持 `idx=<语料 index>`：供**无出典地址的梗概槽**用
        # （`台词对照.json` 该槽 `offset=None`、`jp` 为空；本语料共 58 个，此前任何修正表都够不到）。
        # ISSUE-20260930-11 新增，additive：仅当表内确有该键时才改写定位串。
        loc = ("offset=%d" % off) if off is not None else None
        if loc is None and (SOURCE, file_, "idx=%d" % idx) in corrections:
            loc = "idx=%d" % idx
        row = corrections.get((SOURCE, file_, loc)) if loc else None
        if row is not None:
            want_base = CORR_SOURCE_TO_BASE.get(row["source"])
            if want_base is None:
                raise SystemExit("!! 修正表 source 未登记门控映射: %s @ %s/%s"
                                 % (row["source"], file_, loc))
            # `term_unify` 与取文层无关（术语统一对任何层的文本都成立）⇒ 不受来源门控约束：
            # D14 共有场景（取文本篇层，`cn_base=ot`）里的同一术语同样要统一。
            # 其余 fix_type 仍按 §四.5 门控（防用某层重译顶掉另一层译文）。
            if want_base == base or row["fix_type"] == "term_unify":
                cn_before = cn
                if row["fix_type"] == "term_unify":
                    # ISSUE-20260930-12：`term_unify` 是**词形级替换**——`old_text` = 词形正则、
                    # `new_text` = 替换值（**不是整句**）。命中即 re.sub；已是后态 ⇒ 幂等 no-op
                    # （不记 fix_refs、不计命中）；两者都不是 ⇒ fail loud。
                    cn, tu_state = _term_unify.apply(cn, row["old_text"], row["new_text"])
                else:
                    # 完整性断言：`old_text` 与源语料比对**忽略 U+3000**。理由：全角空格由本模块 ②.5
                    # 统一删除，是**流水线自己的规范化层**——otr 的 R 版译文带前导「　」，而成品语料与
                    # 修正表都按「删除后」的形态写值；若按原样比对，凡带前导全角空格的槽都会假失败。
                    # 其余字符仍逐字符相等 ⇒ 定位错位（如 `idx` 随行数漂移）依然 fail loud。
                    if row["old_text"].replace(U3000, "") != (cn or "").replace(U3000, ""):
                        raise SystemExit("!! 修正表 old_text 与源语料不符（%s / %s，已忽略 U+3000）:\n"
                                         "  期望=%r\n  实际=%r"
                                         % (file_, loc, row["old_text"], cn))
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
                # 来源门控：条目 source 与取文基准层不符 → 不生效（逐条留痕，不静默丢弃）
                GATED.append({
                    "table": row["_table"], "source": row["source"], "file": file_,
                    "locator": loc, "kind": row["kind"], "fix_type": row["fix_type"],
                    "script": script, "seq": i, "cn_base": base,
                    "jp": jp, "cn_kept": cn, "cn_gated": row["new_text"],
                    "old_text": row["old_text"],
                    "reason": "source_gate: 条目 source=%s 对应取文基准 %s，"
                              "而该行取文基准为 %s → 不生效（不得用该层重译覆盖现取文）"
                              % (row["source"], want_base, base),
                })

        # ---- ②.5 U+3000 归一化（通用 SKILL §七.6；见文件头注释）
        # 只删全角空格，不动 jp、不动其它字符；幂等。
        cn = strip_u3000(cn, "title" if l["kind"] == "title" else "body")

        # ---- ③ 译名替换（JP 门控；body 作用于 cn，name 作用于名字框）
        cn, h1 = apply_term(cn, jp, SOURCE, "body")
        speaker_cn, h2 = apply_term(speaker_cn, speaker_jp, SOURCE, "name")
        term_hits = h1 + h2
        if term_hits:
            layers.append("name_replace")
            name_repl_scene += len(term_hits)

        # D14 例外：文本仍来自 R 版且源为 mig（新米），且未被修正表修复
        if base == "otr_new" and l.get("source") == "mig" and not fix_refs:
            d14_exc = "mig_no_2009_counterpart"
            d14_exc_scene += 1

        # cn_origin = 生效层中优先级最高者（name_replace 不改变取文来源，仅记入 layers）
        origin = base
        for lay in layers:
            if lay == "name_replace":
                continue
            if ORIGIN_RANK.get(lay, -1) > ORIGIN_RANK.get(origin, -1):
                origin = lay
        if not layers:
            origin = "empty"
        by_origin[origin] += 1
        by_src[str(l.get("source"))] += 1

        # ---- 语音
        vid = l.get("voice") or ""
        audio = []
        if vid:
            voices.add(vid)
            p = map_voice(vid)
            if p:
                audio.append(p)

        # ---- cast
        if l["kind"] in ("dialogue", "narration"):
            name = speaker_cn if speaker_cn else "旁白"
            if name not in cast:
                cast.append(name)

        lines_out.append({
            "seq": i,
            "index": idx,
            "lineno": l["lineno"],
            "kind": l["kind"],
            "speaker": speaker_cn,
            "speaker_jp": speaker_jp,
            "voice": vid,
            "jp": jp,
            "cn": cn,
            "cn_origin": origin,
            "cn_base": base,
            "align_method": align,
            "layers": layers,
            "fix_refs": fix_refs,
            "name_replaced": term_hits,
            "empty_slot": empty_slot,
            "d14_exception": d14_exc,
            "audio": audio,
        })

    # ---- 标题
    titles = [l for l in lines_out if l["kind"] == "title"]
    prim = None
    for t in titles:
        if t["cn_origin"] in ("ot", "fix_table", "retranslate"):
            prim = t
    if prim is None:
        prim = titles[-1] if titles else None
    title_variants = [{"offset": sc["lines"][t["seq"] - 1]["offset"], "jp": t["jp"],
                       "cn": t["cn"], "cn_origin": t["cn_origin"]} for t in titles]

    # ---- 后继 / 选择支
    nxt = next_map.get(script, [])
    if not nxt:
        nk = "end"
    elif len(nxt) == 1:
        nk = "linear"
    else:
        nk = "branch"
    choices = []
    if script in CHOICE_JP:
        # 选择支串已在脚本内确证；但其与各跳转标签的**配对顺序未逆向**
        # （TOB0 分支语义未逆向，总纲 R1）→ target 一律留 null，不臆断配对。
        for tjp in CHOICE_JP[script]:
            cn_ch = CHOICE_CN.get(script, {}).get(tjp)
            choices.append({
                "text_jp": tjp,
                "text_cn": cn_ch,
                "cn_origin": "fix_table" if cn_ch else None,
                "target": None, "pairing_verified": False,
                "confirmed": True,
                "evidence": "%s.tob 选择支串实测存在；候选目标 %s；选项↔目标配对未逆向"
                            "（TOB0 分支语义未逆向，总纲 R1）；译文由主代理裁决补入（W6a2）"
                            % (script, "/".join(t.upper() for t in nxt))})

    # ---- 素材
    assets = []
    missing = []
    for ref in manifest["per_file"].get(file_, {}).get("assets", []):
        k, p = map_asset_ref(ref)
        if p:
            assets.append({"ref": ref, "kind": k, "out_relpath": p, "hit": True})
        else:
            assets.append({"ref": ref, "kind": k, "out_relpath": None, "hit": False})
            missing.append(ref)

    # ---- text_source（按取文基准层 layers[0] 汇总，不受修正/译名层影响）
    bases = set(t["layers"][0] for t in lines_out if t["layers"])
    has_ot = "ot" in bases
    has_otr = "otr_new" in bases
    if has_ot and has_otr:
        text_source = "mixed"
    elif has_ot:
        text_source = "ot"
    else:
        text_source = "otr_new"

    # ---- phase
    if script == "s03c_01a":
        phase = "序"
    elif script == "s03c_20a":
        phase = "结局"
    else:
        phase = "个人线"

    return {
        "scene_id": "%s_%s" % (SOURCE, script),
        "source": SOURCE,
        "script": script,
        "source_kind": kind,
        "text_source": text_source,
        "title_jp": prim["jp"] if prim else None,
        "title_cn": prim["cn"] if prim else None,
        "title_variants": title_variants,
        "game_date": dates[0]["date"] if dates else None,
        "game_dates": dates,
        "phase": phase,
        "route": ROUTE,
        "cast": cast,
        "next": nxt,
        "next_kind": nk,
        "choices": choices,
        "line_count": len(lines_out),
        "voice_count": len(voices),
        "assets": assets,
        "assets_missing": missing,
        "stats": {
            "lines_by_origin": dict(by_origin),
            "lines_by_source": dict(by_src),
            "corrections_hit": corrections_hit_scene,
            "name_replace_count": name_repl_scene,
            "empty_slots": empty_scene,
            "d14_exceptions": d14_exc_scene,
        },
        "lines": lines_out,
    }

# ---------------------------------------------------------------- build

w("[6/8] 组装 55 场景 ...")
scene_objs = [build_scene(sc) for sc in scenes_raw]

# ---------------------------------------------------------------- 校验

w("[7/8] 自检 ...")
in_scope = [r for r in corr_rows if r["source"] == SOURCE and r["file"].startswith("s03c")]
gated_full = set((g["source"], g["file"], g["locator"]) for g in GATED)
gated_in_scope = [g for g in GATED if g["file"].startswith("s03c")]
out_scope = [r for r in corr_rows if (r["source"], r["file"], r["locator"]) not in corr_hit
             and (r["source"], r["file"], r["locator"]) not in gated_full]
miss_corr = [(r["_table"], r["source"], r["file"], r["locator"], r["fix_type"]) for r in in_scope
             if (r["source"], r["file"], r["locator"]) not in corr_hit
             and (r["source"], r["file"], r["locator"]) not in gated_full]
tot_lines = sum(s["line_count"] for s in scene_objs)
orig_dist = collections.Counter()
src_dist = collections.Counter()
for s in scene_objs:
    for k, v in s["stats"]["lines_by_origin"].items():
        orig_dist[k] += v
    for k, v in s["stats"]["lines_by_source"].items():
        src_dist[k] += v
a_total = sum(len(s["assets"]) for s in scene_objs)
a_hit = sum(1 for s in scene_objs for a in s["assets"] if a["hit"])
a_miss = a_total - a_hit
v_ref = sum(1 for s in scene_objs for l in s["lines"] if l["voice"])
v_hit = sum(1 for s in scene_objs for l in s["lines"] if l["audio"])

report = {
    "scenes": len(scene_objs),
    "lines_total": tot_lines,
    "lines_baseline_compare_json": sum(len(sc["lines"]) for sc in scenes_raw),
    "orig_dist": dict(orig_dist),
    "src_dist": dict(src_dist),
    "corrections_total": len(corr_rows),
    "corrections_in_scope_s03c": len(in_scope),
    "corrections_hit_in_scope": len(in_scope) - len(miss_corr) - len(gated_in_scope),
    "corrections_hit_all_sources": len(corr_hit),
    "corrections_missing_in_scope": miss_corr,
    "corrections_gated_count": len(GATED),
    # ISSUE-20260930-12：`term_unify` 的幂等 no-op 留痕（构建期应为 0——每个目标槽都应命中词形）
    "term_unify_noop": TERM_NOOP,
    "corrections_gated_in_scope": len(gated_in_scope),
    "corrections_gated_out": GATED,
    "corrections_gated_by_table": collections.Counter(g["table"] for g in GATED).most_common(),
    "gated_titles_preserved_ot": [
        {"script": g["script"], "locator": g["locator"], "table": g["table"], "jp": g["jp"],
         "cn_kept": g["cn_kept"], "cn_gated": g["cn_gated"], "reason": g["reason"]}
        for g in GATED if g["kind"] == "title" and g["cn_base"] == "ot"],
    "choice_cn_supplied": [{"script": s["script"], "text_jp": c["text_jp"],
                            "text_cn": c["text_cn"], "cn_origin": c.get("cn_origin")}
                           for s in scene_objs for c in s["choices"]],
    "corrections_out_of_scope": collections.Counter(
        (r["source"] or "-", r["_table"]) for r in out_scope).most_common(),
    "corrections_out_of_scope_files": sorted(set(r["file"] for r in out_scope if r["source"] == SOURCE)),
    "assets_total": a_total, "assets_hit": a_hit, "assets_missing": a_miss,
    "voice_refs": v_ref, "voice_hit": v_hit,
    "term_hits": sum(s["stats"]["name_replace_count"] for s in scene_objs),
    "u3000_normalized": dict(U3000_STATS),
    "empty_slots": sum(s["stats"]["empty_slots"] for s in scene_objs),
    "d14_exceptions": sum(s["stats"]["d14_exceptions"] for s in scene_objs),
    "text_source_dist": dict(collections.Counter(s["text_source"] for s in scene_objs)),
    "source_kind_dist": dict(collections.Counter(s["source_kind"] for s in scene_objs)),
    "phase_dist": dict(collections.Counter(s["phase"] for s in scene_objs)),
    "next_kind_dist": dict(collections.Counter(s["next_kind"] for s in scene_objs)),
    "scenes_with_date": [s["script"] for s in scene_objs if s["game_date"]],
    "d14_exception_lines": [{"script": s["script"], "seq": l["seq"], "index": l["index"],
                             "kind": l["kind"], "src": s["stats"]["lines_by_source"].get("mig"),
                             "jp": l["jp"], "cn": l["cn"]}
                            for s in scene_objs for l in s["lines"] if l["d14_exception"]],
    "asset_missing_list": [{"script": s["script"], "ref": r} for s in scene_objs for r in s["assets_missing"]],
    "align_method_dist": dict(collections.Counter(
        l["align_method"] for s in scene_objs for l in s["lines"])),
    "title_overrides_ot_base": [{"script": s["script"], "offset": s["lines"][l["seq"] - 1]["index"],
                                 "table": l["fix_refs"][0]["table"], "locator": l["fix_refs"][0]["locator"],
                                 "cn_before_ot": l["fix_refs"][0]["cn_before"], "cn_after": l["cn"],
                                 "jp": l["jp"]}
                                for s in scene_objs for l in s["lines"]
                                if l["kind"] == "title" and l["cn_base"] == "ot" and l["fix_refs"]],
    "name_replace_examples": [{"script": s["script"], "seq": l["seq"], "field": h["字段"],
                               "原词日文": h["原词日文"], "旧写法": h["旧写法"], "新写法": h["新写法"],
                               "before": h["before"], "after": h["after"],
                               "context_flag": h["context_flag"], "cn": l["cn"], "speaker": l["speaker"]}
                              for s in scene_objs for l in s["lines"] for h in l["name_replaced"]],
    "per_scene": [{
        "script": s["script"], "source_kind": s["source_kind"], "text_source": s["text_source"],
        "line_count": s["line_count"], "voice_count": s["voice_count"],
        "title_jp": s["title_jp"], "title_cn": s["title_cn"],
        "game_date": s["game_date"], "next": s["next"], "next_kind": s["next_kind"],
        "choices": len(s["choices"]), "cast": s["cast"],
        "assets_total": len(s["assets"]), "assets_hit": sum(1 for a in s["assets"] if a["hit"]),
        "assets_missing": s["assets_missing"],
        "corrections_hit": s["stats"]["corrections_hit"],
        "name_replace_count": s["stats"]["name_replace_count"],
        "lines_by_origin": s["stats"]["lines_by_origin"],
        "empty_slots": s["stats"]["empty_slots"],
        "d14_exceptions": s["stats"]["d14_exceptions"],
    } for s in scene_objs],
}
report["lines_balanced"] = (tot_lines == report["lines_baseline_compare_json"])
report["corrections_all_in_scope_hit"] = (len(miss_corr) == 0)
report["scene_ids_unique"] = (len(set(s["scene_id"] for s in scene_objs)) == len(scene_objs))

# 抽样 10 行（各层实例）
samples = {}
for s in scene_objs:
    for l in s["lines"]:
        for o in ("ot", "otr_new", "fix_table", "retranslate"):
            if l["cn_origin"] == o and o not in samples and l["cn"]:
                samples[o] = {"script": s["script"], "seq": l["seq"], "index": l["index"],
                              "kind": l["kind"], "speaker": l["speaker"], "voice": l["voice"],
                              "jp": l["jp"], "cn": l["cn"], "cn_origin": l["cn_origin"],
                              "layers": l["layers"], "fix_refs": l["fix_refs"]}
report["samples"] = samples

os.makedirs(STG, exist_ok=True)
json.dump(report, open(os.path.join(STG, "_build_stats.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- write scene.jsonl

w("[8/8] 写出 scene.jsonl ...")
_assert_in_checkout(OUT, "剧本产物目录")
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "scene_otr.jsonl")
_assert_in_checkout(outpath, "scene_otr.jsonl")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    for s in scene_objs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

# 逐行 json.loads 校验
with open(outpath, encoding="utf-8") as f:
    n = sum(1 for ln in f if json.loads(ln))
w("      -> %s （%d 行，逐行 json.loads OK）" % (outpath, n))

# ---------------------------------------------------------------- 摘要

w("")
w("================ 摘要 ================")
w("场景数            : %d  (shared %d / branch %d / new %d)" % (
    report["scenes"], report["source_kind_dist"].get("shared", 0),
    report["source_kind_dist"].get("branch", 0), report["source_kind_dist"].get("new", 0)))
w("行数              : %d  (基线 台词对照 %d，守恒=%s)" % (
    report["lines_total"], report["lines_baseline_compare_json"], report["lines_balanced"]))
w("cn_origin 分布    : %s" % report["orig_dist"])
w("源 src 分布       : %s" % report["src_dist"])
w("text_source 分布  : %s" % report["text_source_dist"])
w("修正表            : 合计 %d ｜ s03c 范围内 %d ｜ 命中 %d ｜ 门控排除 %d ｜ 未命中 %d" % (
    report["corrections_total"], report["corrections_in_scope_s03c"],
    report["corrections_hit_in_scope"], report["corrections_gated_in_scope"],
    len(report["corrections_missing_in_scope"])))
w("  未命中(范围内)  : %s" % (report["corrections_missing_in_scope"] or "无"))
w("term_unify 幂等 no-op: %d 条（构建期应为 0）%s"
  % (len(TERM_NOOP), (" ← " + str(TERM_NOOP[:3])) if TERM_NOOP else ""))
w("  门控排除(逐条)  :")
for g in report["corrections_gated_out"]:
    w("      %s %s %s %s | %s -> 保留: %s" % (
        g["table"], g["file"], g["locator"], g["kind"], g["cn_gated"], g["cn_kept"]))
w("选择支补译        : %s" % report["choice_cn_supplied"])
w("  范围外(他源/他场景) 分布: %s" % report["corrections_out_of_scope"])
w("译名替换处数      : %d" % report["term_hits"])
w("U+3000 归一化     : 正文 %d 槽 / %d 字；标题 %d 槽 / %d 字（通用 SKILL §七.6）" % (
    U3000_STATS["body_slots"], U3000_STATS["body_chars"],
    U3000_STATS["title_slots"], U3000_STATS["title_chars"]))
w("素材命中          : %d/%d  (缺失 %d)" % (a_hit, a_total, a_miss))
w("语音命中          : %d/%d" % (v_hit, v_ref))
w("空槽 / D14 例外   : %d / %d" % (report["empty_slots"], report["d14_exceptions"]))
w("next_kind 分布    : %s" % report["next_kind_dist"])
w("有显式日期场景    : %s" % report["scenes_with_date"])
w("scene_id 唯一     : %s" % report["scene_ids_unique"])