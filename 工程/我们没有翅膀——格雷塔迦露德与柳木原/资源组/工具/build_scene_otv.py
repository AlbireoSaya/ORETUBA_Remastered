# -*- coding: utf-8 -*-
r"""
W6e · 结构化剧本构建器 —— PSV 美咲线（源代号 otv · 31 场景）

schema：`资源组\剧本\schema.md`（W6a 定稿；本模块**不改字段结构**，只对
        「源专属枚举取值」做必要扩展，逐项在产出报告 §2 说明）
契约：`资源组\修正\_README.md` §四.2（应用顺序）与 §四.5（修正表来源门控）

**W11h 修复（2026-09-19 · 最严重数据缺陷）**：本构建器此前把 `lines[].audio[]` 与
`assets[].out_relpath` 直接写成**原始 PSV 工程裸路径**
（如 `工程/我们没有翅膀PSV/素材/美咲线/audio/voice/16862_misaki_000.ogg`），
**不在素材库命名空间内** —— 编程组按 `资源组\剧本\schema.md` §2.1 与
`资源组\交接编程组\交接说明.md` C3 拼接 `krkr素材库\otv/…` 必然 100% 取不到文件
（实测 1,737/1,737 语音、941/941 素材均不可解析）；且 `hit` 是拿原始源路径判的
（941/941 全 true），`assets_missing[]` 为空 —— **缺口被静默掩盖**。
现改为在**取引用处**经 `lib_ref()` 映射到 `krkr素材库` 的 `out_relpath`
（`otv/<kind>/otv_<name>`，即 `资源总账.json` 的权威取值）；`hit` 改为
「该 out_relpath 在素材库下真实存在」；映射不到者记入 `MAP_FAILURES` 并**报错中止**
（fail loud，绝不静默放过）。映射规则与依据见「素材库命名空间映射」小节。

**W10b 变更（2026-09-19）**：本构建器此前**未装载 `修正表_otv.tsv`** → W4b 立的
`source=otv` 条目（`script=M01_04&lineno=216`，`fix_type=quote_add`）未生效。现按契约接入：
  · `修正表_otv.tsv` 已并入 `TABLES`，按 `(source, file, locator)` 三元组定位；
  · otv 的 `locator` 形态为 `script=<脚本名>&lineno=<行序>`（`_README.md` §二.1），
    `lineno` 为**每脚本内 1-based**，故以 `(script, lineno)` 复合键索引，**不做字符串匹配**；
  · 命中时先断言 `old_text` 逐字符等于源语料 `中文`，再按 §四.2 顺序
    （修正表 → 译名替换）覆盖 `cn`。

只读源（一个字节都不改）：
  工程\我们没有翅膀PSV\脚本解包\            31 个 Shift-JIS 纯文本 DSL 脚本
  工程\我们没有翅膀PSV\汉化\台词对照.json     4,931 行（台词 4,904 + 梗概 27）
  工程\我们没有翅膀PSV\汉化\{场景标题_中文化.tsv, 名字表_中文化.tsv}
  工程\我们没有翅膀PSV\美咲线清单\{资源引用.tsv, 音频清单.tsv, 映射结论.md}
  工程\我们没有翅膀PSV\解密\PCSG00299\media\{CG.cpk, SystemData.cpk}  ← 只读 TOC（解析 EyeCatch）
  资源组\修正\修正表_*.tsv, 译名替换表.tsv
  资源组\krkr素材库\资源总账.json

只写：资源组\剧本\scene_otv.jsonl（**写本 checkout**，见下「路径根」）
      子代理工作区\ISSUE-20260918-06\W6e\_build_stats_otv.json（写本 checkout）

路径根（W11h 读写分离）：
  大体积只读源（PSV 脚本解包 / 素材 / krkr素材库 实体文件 / 资源总账.json）被
  `.gitignore` 排除，**仅存在于主工作区**，故：
    · 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
      `GRETA_DATA_ROOT` 覆盖）；
    · 写 = 本脚本所在的 checkout（`OUT` 由 `__file__` 推导），issue 分支的产物因此
      落在本分支工作树内，不会误写主工作区。
  从主工作区运行本脚本时两者重合，行为与修复前一致。

复跑：
  python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_otv.py"
"""
import json, os, re, csv, sys, collections

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__（同 build_scene_otp.py）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _term_unify               # noqa: E402  同目录共享模块：`term_unify` 语义的唯一实现

# ---------------------------------------------------------------- 路径根（读写分离）
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, "资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, "修正")                            # 修正表：以本分支副本为准
OUT  = os.path.join(RES_LOCAL, "剧本")                            # 产物：写本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT                                                  # 兼容旧引用（工具\pylibs）
PRJ_DATA  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES_DATA  = os.path.join(PRJ_DATA, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6e")   # 写本 checkout
PSV  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀PSV")
SCR  = os.path.join(PSV, r"脚本解包")
HAN  = os.path.join(PSV, r"汉化")
LST  = os.path.join(PSV, r"美咲线清单")
ASSET_ROOT = os.path.join(PSV, r"素材\美咲线")          # 实际提取产物（273 MB）
LIB_ROOT = os.path.join(RES_DATA, r"krkr素材库")        # 素材库根 = 引用命名空间基准
LEDGER = os.path.join(LIB_ROOT, "资源总账.json")
MEDIA  = os.path.join(PSV, r"解密\PCSG00299\media")     # CPK（只读 TOC）


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

SOURCE = "otv"
ROUTE  = "M/P03 美咲线"

# 31 个脚本（27 个美咲编 M01_01..M09_02 + 4 个《ある日の美咲》P03_01A..D）
SCRIPTS = [
    "M01_01", "M01_02", "M01_03", "M01_04",
    "M02_01", "M02_02", "M02_03", "M02_04", "M02_05", "M02_06", "M02_07", "M02_08",
    "M03_01", "M03_02",
    "M04_01", "M04_02", "M04_03",
    "M05_01", "M05_02",
    "M06_01", "M06_02", "M06_03",
    "M07_01", "M07_02",
    "M08_01",
    "M09_01", "M09_02",
    "P03_01A", "P03_01B", "P03_01C", "P03_01D",
]
assert len(SCRIPTS) == 31

TABLES = [
    ("修正表_B1B3.tsv",            os.path.join(FIX, "修正表_B1B3.tsv")),
    ("修正表_B1B3_扩展.tsv",       os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    ("修正表_新增场景mig重译.tsv", os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    ("修正表_otv.tsv",             os.path.join(FIX, "修正表_otv.tsv")),   # W10b 接入（source=otv）
    # ISSUE-20260930-10：用户 2026-09-30 术语裁决（source 按行门控；field=cn，fix_type=term_unify）
    ("修正表_裁决20260930.tsv",    os.path.join(FIX, "修正表_裁决20260930.tsv")),
]
TERM_TABLE = os.path.join(FIX, "译名替换表.tsv")

# otv 取文语料文件名（修正表 `file` 列取值；`_README.md` §二.1）
OTV_FILE = "台词对照.json"
# 本模块可能的取文基准层（`cn_base`）；范围 = 其 source 映射到这些层的修正条目
MODULE_BASES = {"otv", "empty"}

# ---------------------------------------------------------------- 修正表来源门控
# 契约：`资源组\修正\_README.md` §四.5。otv 为新源，登记其映射（本模块取文基准层 = otv）。
# W10b：`修正表_otv.tsv` 已接入 → 本模块范围内 1 条 source=otv，命中 1。
# 六源全覆盖（ISSUE-20260930-11 补齐 np —— 缺项会让装载该表的本次运行直接 fail loud）
CORR_SOURCE_TO_BASE = {"otr": "otr_new", "otp": "otp", "ota": "ota", "ot": "ot",
                       "otv": "otv", "np": "np"}
GATED = []
TERM_NOOP = []    # `term_unify` 的幂等 no-op 留痕（ISSUE-20260930-12；构建期应为 0 条）

# ---------------------------------------------------------------- helpers

def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def w(s):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()

def zen2han(s):
    return "".join(chr(ord(c) - 0xFEE0) if 0xFF10 <= ord(c) <= 0xFF19 else c for c in s)

DATE_RE = re.compile(r"([０-９0-9]{1,2})月([０-９0-9]{1,2})日")

def parse_date(s):
    m = DATE_RE.search(zen2han(s))
    if not m:
        return None
    return "%02d/%02d" % (int(m.group(1)), int(m.group(2)))

# ---------------------------------------------------------------- load inputs

w("[1/8] 读取输入 ...")
rows = json.load(open(os.path.join(HAN, "台词对照.json"), encoding="utf-8"))
by_script = collections.OrderedDict((s, []) for s in SCRIPTS)
for r in rows:
    by_script[r["脚本"]].append(r)
assert sum(len(v) for v in by_script.values()) == len(rows) == 4931

titles = collections.defaultdict(list)          # script -> [(字段, jp, cn)]
for r in read_tsv(os.path.join(HAN, "场景标题_中文化.tsv")):
    titles[r["脚本"]].append((r["字段"], r["场景名日文"], r["场景名中文"]))

nametab = {r["编号"]: (r["显示名日文"], r["显示名中文"])
           for r in read_tsv(os.path.join(HAN, "名字表_中文化.tsv"))}

refrows = read_tsv(os.path.join(LST, "资源引用.tsv"))
REF = {}
for r in refrows:
    REF.setdefault(r["name"].strip().lower(), r)      # name -> {archive,index,filename,size}

audrows = read_tsv(os.path.join(LST, "音频清单.tsv"))
AUDIO = {}                                            # (类别, 编号) -> 输出文件
for r in audrows:
    AUDIO[(r["类别"], r["编号"])] = r["输出文件"]
VOICE_N = {k[1] for k in AUDIO if k[0] == "voice"}
BGM_N   = {k[1] for k in AUDIO if k[0] == "bgm"}
SE_N    = {k[1] for k in AUDIO if k[0] == "se"}

ledger = json.load(open(LEDGER, encoding="utf-8"))
otv_sys_order = [e for e in ledger["entries"] if e["source"] == "otv" and e["kind"] == "sys"]

w("      台词对照 %d 行 / %d 脚本 ｜ 场景标题 %d 条 ｜ 名字表 %d ｜ 资源引用 %d ｜ 音频 %d ｜ 总账 %d"
  % (len(rows), len(by_script), sum(len(v) for v in titles.values()), len(nametab),
     len(refrows), len(audrows), len(ledger["entries"])))

# ---------------------------------------------------------------- CPK TOC（EyeCatch 解析依据）

w("[2/8] 读取 CPK TOC（只读；EyeCatch 模式 0/1 的归档序索引）...")
sys.path.insert(0, os.path.join(ROOT, r"工具\pylibs"))
_cwd = os.getcwd()
os.chdir(MEDIA)
try:
    from cricodecs import cpk as _cpk
    CG_NAMES = [f.filename for f in _cpk.Cpk.load("CG.cpk").files]
    SD_NAMES = [f.filename for f in _cpk.Cpk.load("SystemData.cpk").files]
finally:
    os.chdir(_cwd)
EC_LIST = [n for n in CG_NAMES if n.upper().startswith("EC") and n.upper().endswith(".PNG")]
ECB_LIST = [n for n in SD_NAMES if n.lower().startswith("ec_bg")]
w("      CG.cpk %d 条目（EC*.png %d）｜ SystemData.cpk %d 条目（ec_bg*.png %d）"
  % (len(CG_NAMES), len(EC_LIST), len(SD_NAMES), len(ECB_LIST)))
# 交叉校验：总账 otv/sys 的条目顺序应与 SystemData.cpk TOC 顺序一致（W5 提取即按 TOC 序）
_lst_ledger = [e["orig_name"] for e in otv_sys_order if e["orig_name"].lower().startswith("ec_bg")]
assert _lst_ledger == ECB_LIST, "!! 总账 otv/sys 顺序与 SystemData.cpk TOC 不一致"
w("      交叉校验：总账 otv/sys 的 ec_bg 顺序 == SystemData.cpk TOC 顺序 ✓")

# ---------------------------------------------------------------- correction tables

w("[3/8] 装载修正表（并按 §四.5 门控）...")
corr_rows = []
for tname, tpath in TABLES:
    for r in read_tsv(tpath):
        r["_table"] = tname
        corr_rows.append(r)
CORR_BY_KEY = {}
for r in corr_rows:
    k = (r["source"], r["file"], r["locator"])
    if k in CORR_BY_KEY:
        raise SystemExit("!! 修正表定位冲突: %s" % (k,))
    CORR_BY_KEY[k] = r
# fail-loud：未登记门控映射的 source
for r in corr_rows:
    if r["source"] not in CORR_SOURCE_TO_BASE:
        raise SystemExit("!! 修正表 source 未登记门控映射: %s" % r["source"])

def parse_otv_locator(loc):
    """otv locator 形态 `script=<脚本名>&lineno=<行序>`（_README.md §二.1）。
    lineno 为每脚本内 1-based，故必须以 (script, lineno) 复合键定位。"""
    m = re.fullmatch(r"script=([^&]+)&lineno=(\d+)", loc)
    if not m:
        raise SystemExit("!! 非法 otv locator（应形如 script=X&lineno=N）: %s" % loc)
    return m.group(1), int(m.group(2))

corr_hit = set()
# 范围内条目 = source 映射到本模块取文基准层（otv / empty）者
CORR_OTV = [r for r in corr_rows if CORR_SOURCE_TO_BASE[r["source"]] in MODULE_BASES]
CORR_OTV_INDEX = {}
for r in CORR_OTV:
    if r["file"] != OTV_FILE:
        raise SystemExit("!! otv 条目 file 非 %s: %s" % (OTV_FILE, r["file"]))
    key = parse_otv_locator(r["locator"])
    if key in CORR_OTV_INDEX:
        raise SystemExit("!! 修正表定位冲突（otv）: %s" % (key,))
    CORR_OTV_INDEX[key] = r
CORR_OTV_OUT_OF_SCOPE = [r for r in corr_rows if r not in CORR_OTV]
w("      修正表合计 %d 条（%s）｜ 范围内（source=otv）%d 条 ｜ 范围外 %d 条"
  % (len(corr_rows), " / ".join("%s=%d" % (t, sum(1 for r in corr_rows if r["_table"] == t))
                                for t, _ in TABLES), len(CORR_OTV), len(CORR_OTV_OUT_OF_SCOPE)))

# ---------------------------------------------------------------- name replacement table

w("[4/8] 装载译名替换表（otv 适用规则）...")
TERM_RULES = []
for r in read_tsv(TERM_TABLE):
    new, old, scope = r["新写法"].strip(), r["旧写法"].strip(), r["适用范围(源代号)"].strip()
    if new.startswith("（") or old.startswith("（") or scope == "—":
        continue                                   # 待裁决 / 非替换项 / 无旧写法残留
    src, stream = (scope.split("/", 1) + ["body"])[:2] if "/" in scope else (scope, "body")
    if src != SOURCE:
        continue                                   # 本模块只消费 otv 条目
    TERM_RULES.append({"jp": r["原词日文"].strip(), "old": old, "new": new,
                       "stream": "name" if stream == "name" else "body",
                       "table_note": r["备注"].strip()})
w("      otv 可用替换规则 %d 条（已剔除待裁决/非替换项）" % len(TERM_RULES))

# §六 排除规则（正则），键 = (原词日文, 旧写法)；与 W6a 同一套消费侧规则
EXCL = {
    ("渡来さん", "渡来（裸名）"): re.compile(r"渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香)"),
    ("委員長", "委员长"):        re.compile(r"(?<!执行)委员长"),
    ("ハヤブサ", "隼"):          re.compile(r"(?<!游)隼(?!人)"),
    ("ソラ学", "空学"):          re.compile(r"(?<!美)空学(?!院|府)"),
    # W6e 实测补充（第三条表外风险）：`針生`→`针生同学` 在「姓+名」「姓+职称」处同样产生污染——
    #   M02_03#1  `針生蔵人` → `针生同学藏人`（应为「针生藏人」）
    #   M09_01#141 `針生提督` → `针生同学提督`（应为「针生提督」）
    # 故在既有敬称排除之外，再排除「后接任意汉字」的情形（本模块该规则由此 0 命中；
    # PSV 译文其余 52 处 針生 已自带「针生同学/前辈」，无需替换）。建议主代理补入 译名统一口径 §六。
    ("針生", "针生"):            re.compile(r"针生(?!同学|前辈|君|先生|小姐|老师|哥|姐|[\u4e00-\u9fff])"),
    ("ガルーダ", "伽楼罗"):      re.compile(r"(?<!伊丹)伽楼罗"),
}
JP_SKIP = {"ガルーダ": ["伽楼羅"]}
CONTEXT_FLAGGED = {"ペガサス", "ドラさん"}

def apply_term(cn, jp, stream):
    hits = []
    if not cn:
        return cn, hits
    for rule in TERM_RULES:
        if rule["stream"] != stream or rule["jp"] not in jp:
            continue
        skip = JP_SKIP.get(rule["jp"])
        if skip and any(s in jp for s in skip):
            continue
        rx = EXCL.get((rule["jp"], rule["old"]))
        new_cn = rx.sub(rule["new"], cn) if rx is not None else cn.replace(rule["old"], rule["new"])
        if new_cn != cn:
            hits.append({"原词日文": rule["jp"], "旧写法": rule["old"], "新写法": rule["new"],
                         "字段": stream, "before": cn, "after": new_cn,
                         "context_flag": rule["jp"] in CONTEXT_FLAGGED})
            cn = new_cn
    return cn, hits

# ---------------------------------------------------------------- 素材库命名空间映射
# 契约：`资源组\剧本\schema.md` §2.1 —— `lines[].audio[]` 与 `assets[].out_relpath`
#   必须是**素材相对路径**（即 `资源总账.json` 的 `out_relpath`，形如
#   `otv/voice/otv_xxx.ogg`）；`资源组\交接编程组\交接说明.md` C3 要求引用一律写
#   `otv/…` 全路径（编程组按 `krkr素材库\` + 该相对路径拼接取文件）。
#
# 映射规则（原始 PSV 裸路径 → krkr素材库 out_relpath）：
#   ① 素材库内一律分目录 `otv/<kind>/`，文件名统一加 `otv_` 前缀并整体小写：
#      PSV 侧 `素材/美咲线/images/cg/MIS71.png` → 库内 `otv/pic/otv_mis71.png`
#      （大小写归一 = `.lower()`；PSV 侧 `MIS71.png` / `mis71.png` 视为同一件）。
#   ② `kind` 由本构建器在**取引用处**判定，与 `assets[].kind` 同源：
#      `:Texture`/`:Number` 按归档 CG.cpk→pic ｜ CHR.cpk→chr ｜ 其余→etc
#      `:Image` mode 0（CG.cpk 的 EC*.png）→pic ｜ mode 1（SystemData.cpk 的 ec_bg*.png）→sys
#      `:BGM`→bgm ｜ `:SE`→se ｜ `:Movie`→movie ｜ 台词 `voice`→voice
#   ③ 以 `(kind, 文件名.lower())` 为键查 `资源总账.json` 中 `source=otv` 的条目，取
#      其 `out_relpath`。**不做目录拼接猜路径** —— 总账是唯一权威（撞名改号、
#      `otv_` 前缀、目录归属均已在其内裁决），故不会把 PSV 目录结构硬编码进来。
#   ④ 映射不到 → 记入 `MAP_FAILURES` 并在写出前**报错中止**（fail loud）。
LIB_INDEX = {}
for _e in ledger["entries"]:
    if _e["source"] != SOURCE:
        continue
    _k = (_e["kind"], (_e["orig_name"] or "").lower())
    if _k in LIB_INDEX and LIB_INDEX[_k] != _e["out_relpath"]:
        raise SystemExit("!! 素材总账 otv 条目键冲突: %s -> %s / %s"
                         % (_k, LIB_INDEX[_k], _e["out_relpath"]))
    LIB_INDEX[_k] = _e["out_relpath"]

MAP_FAILURES = []          # (kind, filename)：素材库命名空间下查无对应 out_relpath
MAP_OK = collections.Counter()

def lib_ref(kind, filename):
    """原始 PSV 文件名 → krkr素材库 out_relpath（命名空间相对路径）。
    映射不到返回 None 并记入 MAP_FAILURES（fail loud，绝不静默放过）。"""
    if not filename:
        return None
    p = LIB_INDEX.get((kind, os.path.basename(filename).lower()))
    if p is None:
        MAP_FAILURES.append({"kind": kind, "filename": filename})
    else:
        MAP_OK[kind] += 1
    return p

def lib_abspath(out_relpath):
    return os.path.join(LIB_ROOT, out_relpath.replace("/", os.sep))

ASSET_STATS = collections.Counter()
TEX_UNRESOLVED = []       # :Texture 注释名解析失败（必须为 0）
CHR_UNRESOLVED = []
IMG_UNRESOLVED = []       # :Image 未确证语义 / 越界
TEX_UNNAMED = []          # 无注释名的 :Texture（[StartUp][LoadTexture] 预载表）
IMAGE_LINES = []          # 全部 :Image 行（含 s / f 原值，供未确证语义留痕）
LEDGER_COVER = collections.Counter()   # 命中 资源总账 的引用（仅统计，供报告）

def add_asset(out, seen, ref, kind, out_relpath):
    if ref in seen:
        return
    seen.add(ref)
    # hit = 该 out_relpath 在 krkr素材库 下**真实存在**（W11h：不再拿原始源路径判）
    hit = bool(out_relpath) and os.path.isfile(lib_abspath(out_relpath))
    out.append({"ref": ref, "kind": kind, "out_relpath": out_relpath, "hit": hit})
    ASSET_STATS["total"] += 1
    ASSET_STATS["hit" if hit else "miss"] += 1
    ASSET_STATS["kind_" + kind] += 1
    stem = os.path.splitext(os.path.basename(out_relpath or ""))[0].lower()
    stem = re.sub(r"^otv_", "", stem)
    if any(e["source"] == "otv" and os.path.splitext(e["orig_name"])[0].lower() == stem
           for e in otv_sys_order) or _ledger_has(stem):
        LEDGER_COVER["hit"] += 1
    else:
        LEDGER_COVER["miss"] += 1

_LEDGER_STEMS = None
def _ledger_has(stem):
    global _LEDGER_STEMS
    if _LEDGER_STEMS is None:
        _LEDGER_STEMS = collections.defaultdict(set)
        for e in ledger["entries"]:
            _LEDGER_STEMS[e["source"]].add(os.path.splitext(e["orig_name"])[0].lower())
    return stem in _LEDGER_STEMS["otv"]

# ---------------------------------------------------------------- 逐脚本扫描

w("[5/8] 扫描 31 个脚本（任务/资源/跳转/日期）...")
SCRIPT_INFO = {}
for s in SCRIPTS:
    raw = open(os.path.join(SCR, s), "rb").read().decode("cp932")
    lines = raw.split("\r\n")
    assets, seen = [], set()
    nxt = []
    tex_lines = 0
    for ln in lines:
        code = ln.split("//")[0]                    # 先剥 // 注释（计数口径），但名字在注释里 → 另取全行
        cs = code.strip()
        if not cs:
            continue
        m = re.match(r":Texture\s+(\d+)\b", cs)
        if m:
            tex_lines += 1
            mm = re.search(r"<<([^>]+)>>", ln)
            name = mm.group(1).strip() if mm else None
            if name is None:
                parts = ln.split("//")
                if len(parts) > 1:
                    c = parts[1].strip()
                    if c and not c.startswith("置換"):
                        name = c
            if not name:
                TEX_UNNAMED.append((s, cs))
                continue
            r = REF.get(name.lower())
            if r is None:
                TEX_UNRESOLVED.append({"script": s, "name": name, "line": cs})
                continue
            _kind = ("pic" if r["archive"] == "CG.cpk"
                     else ("chr" if r["archive"] == "CHR.cpk" else "etc"))
            add_asset(assets, seen, "%s\\%s" % (r["archive"], r["filename"]), _kind,
                      lib_ref(_kind, r["filename"]))
            continue
        m = re.match(r":Number\s+([\d,\s]+)", cs)
        if m:
            mm = re.search(r"<<([^>]+)>>", ln)
            if not mm:
                CHR_UNRESOLVED.append({"script": s, "line": cs, "reason": "无 <<貼図名>> 注释"})
                continue
            name = mm.group(1).strip()
            r = REF.get(name.lower())
            if r is None:
                CHR_UNRESOLVED.append({"script": s, "name": name, "line": cs, "reason": "注释名不在资源引用表"})
                continue
            add_asset(assets, seen, "%s\\%s" % (r["archive"], r["filename"]), "chr",
                      lib_ref("chr", r["filename"]))
            continue
        m = re.match(r":Image\s+(-?\d+),(-?\d+)(?:,(-?\d+))?(?:,(-?\d+))?", cs)
        if m:
            mode, a2, a3, a4 = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            IMAGE_LINES.append({"script": s, "raw": cs, "mode": mode,
                                "N_or_s": a2, "b_or_f": a3, "f": a4})
            if mode == 0:
                n = a2
                if n == -1:
                    IMG_UNRESOLVED.append({"script": s, "raw": cs, "reason": "N=-1 语义未确证（疑「不显示/清除」）"})
                    add_asset(assets, seen, "CG.cpk\\EC[-1]", "pic", None)
                elif 1 <= n <= len(EC_LIST):
                    fn = EC_LIST[n - 1]
                    add_asset(assets, seen, "CG.cpk\\%s" % fn, "pic", lib_ref("pic", fn))
                else:
                    IMG_UNRESOLVED.append({"script": s, "raw": cs, "reason": "N 越界 1..%d" % len(EC_LIST)})
            elif mode == 1:
                b = int(a3) if a3 is not None else None
                if b is None or not (0 <= b < len(ECB_LIST)):
                    IMG_UNRESOLVED.append({"script": s, "raw": cs, "reason": "b 缺失或越界"})
                else:
                    fn = ECB_LIST[b]
                    add_asset(assets, seen, "SystemData.cpk\\%s" % fn, "sys", lib_ref("sys", fn))
                # s / f 语义未确证（映射结论 §A.3）→ 不参与解析、不臆断
            else:
                IMG_UNRESOLVED.append({"script": s, "raw": cs, "reason": "未知 mode"})
            continue
        m = re.match(r":SE\s+(\d+)", cs)
        if m:
            n = str(int(m.group(1)))            # 归一化：脚本存在 `:SE 08` 之类前导零写法
            rel = AUDIO.get(("se", n))
            if rel is None:
                add_asset(assets, seen, "SE.AWB\\%s" % n, "se", None)
            else:
                add_asset(assets, seen, "SE.AWB\\%s" % n, "se", lib_ref("se", rel))
            continue
        m = re.match(r":BGM\s+(\d+)", cs)
        if m:
            n = str(int(m.group(1)))            # 归一化：脚本存在 `:BGM 08` 之类前导零写法
            rel = AUDIO.get(("bgm", n))
            add_asset(assets, seen, "BGM.AWB\\%s" % n, "bgm",
                      lib_ref("bgm", rel) if rel else None)
            continue
        m = re.match(r":Movie\s+(\d+)", cs)
        if m:
            n = int(m.group(1))
            MOVIE = {7: "ED_misaki.mp4", 11: "OP03.mp4"}       # adv.txt [Movie] 表（12 项全确证）
            fn = MOVIE.get(n)
            add_asset(assets, seen, "data\\%s" % (fn or ("Movie%d" % n)), "movie",
                      lib_ref("movie", fn) if fn else None)
            continue
        m = re.match(r':NextScene\s+"([^"]+)"', cs)
        if m:
            if m.group(1) not in nxt:
                nxt.append(m.group(1))

    hdr = re.search(r"ゲーム内日時[：:]([^\r\n]*)", raw)
    hdr_txt = hdr.group(1) if hdr else ""
    scn_matches = [(mm.start(1), mm.group(1)) for mm in re.finditer(r':SceneName\s+"([^"]+)"', raw)]

    SCRIPT_INFO[s] = {"assets": assets, "next": nxt, "tex_lines": tex_lines,
                      "header_date": parse_date(hdr_txt), "header_raw": hdr_txt.strip(),
                      "scn_matches": scn_matches}

w("      :Texture 行 %d ｜ 注释名解析失败 %d ｜ :Number 解析失败 %d ｜ :Image 未解析 %d ｜ 无注释名 :Texture %d"
  % (sum(v["tex_lines"] for v in SCRIPT_INFO.values()), len(TEX_UNRESOLVED),
     len(CHR_UNRESOLVED), len(IMG_UNRESOLVED), len(TEX_UNNAMED)))

# ---------------------------------------------------------------- 组装场景

w("[6/8] 组装 31 场景 ...")
scenes = []
by_origin_all = collections.Counter()
for s in SCRIPTS:
    info = SCRIPT_INFO[s]
    trows = by_script[s]

    # ---- 标题槽（[StartUp] :SceneName + SetSceneName；offset = 值在脚本内的 0-based 字节偏移）
    tv = []
    for i, (field, jp, cn) in enumerate(titles.get(s, [])):
        off = info["scn_matches"][i][0] if i < len(info["scn_matches"]) else None
        tv.append({"offset": off, "jp": jp, "cn": cn, "cn_origin": SOURCE})
    title_jp = tv[-1]["jp"] if tv else None
    title_cn = tv[-1]["cn"] if tv else None

    # ---- 日期（脚本头 //ゲーム内日時 注释 + 正文显式 ○月○日）
    dates = {}
    if info["header_date"]:
        dates[info["header_date"]] = {"date": info["header_date"], "line_index": None}
    for r in trows:
        d = parse_date(r["日文"] or "")
        if d:
            dates[d] = {"date": d, "line_index": r["行序"]}     # 正文出处更精确，覆盖头部条目
    game_dates = [dates[k] for k in sorted(dates, key=lambda x: (x != info["header_date"], x))]
    game_date = game_dates[0]["date"] if game_dates else None

    # ---- 台词行
    lines_out, cast, voices = [], [], set()
    n_origin = collections.Counter()
    n_source = collections.Counter()
    empty_n = d14_n = corr_n = name_n = 0
    for i, r in enumerate(trows, 1):
        jp = r["日文"] or ""
        cn = r["中文"] or ""
        cat = r["类别"]
        sp_jp = r["说话人日文"] or ""
        sp_cn = r["说话人中文"] or ""

        if cat == "梗概":
            kind = "summary"                    # 枚举扩展，见产出报告 §2.2（源类别「梗概」，非台词）
        elif r["说话人ID"] is None:
            kind = "narration"
        else:
            kind = "dialogue"

        empty_slot = (not jp.strip() and not cn.strip())
        fix_refs, layers, align = [], [], None
        if empty_slot:
            base = "empty"
            align = "empty_slot"
            empty_n += 1
        else:
            base = SOURCE                        # 取文基准层 = otv（本模块为独立翻译，无第二层）
            align = "new_scene_direct"
            layers = [base]

        # ① 修正表（§四.2：先修正表；§四.5：按 (source,file,locator) 三元组定位 + 来源门控）
        #    otv locator = `script=<名>&lineno=<行序>`，以 (script, lineno) 复合键索引。
        cr = CORR_OTV_INDEX.get((s, r["行序"]))
        if cr is not None:
            tgt_base = CORR_SOURCE_TO_BASE[cr["source"]]
            # `term_unify` 与取文层无关 ⇒ 不受来源门控约束（见 `修正\_README.md` §四.5）
            if tgt_base != base and cr["fix_type"] != "term_unify":
                # 门控排除：条目 source 对应的取文层 ≠ 本行取文基准层 → 不覆盖，逐条留痕
                GATED.append({"table": cr["_table"], "file": cr["file"], "locator": cr["locator"],
                              "source": cr["source"], "fix_type": cr["fix_type"],
                              "原修正值": cr["new_text"],
                              "被排除原因": "source=%s → 取文基准层 %s ≠ 本行 cn_base=%s（§四.5）"
                                            % (cr["source"], tgt_base, base),
                              "实际保留值": cn})
            else:
                cn_before = cn
                if cr["fix_type"] == "term_unify":
                    # ISSUE-20260930-12：`term_unify` 是**词形级替换**——`old_text` = 词形正则、
                    # `new_text` = 替换值（**不是整句**）。命中即 re.sub；已是后态 ⇒ 幂等 no-op
                    # （不记 fix_refs、不计命中）；两者都不是 ⇒ fail loud。
                    cn, tu_state = _term_unify.apply(cn, cr["old_text"], cr["new_text"])
                else:
                    # 完整性断言：old_text 逐字符等于源语料（覆盖前断言，非字符串匹配定位）
                    if cr["old_text"] != cn_before:
                        raise SystemExit("!! 修正表 old_text 与源语料不符（%s / %s）:\n  期望=%r\n  实际=%r"
                                         % (cr["file"], cr["locator"], cr["old_text"], cn_before))
                    tu_state = _term_unify.APPLIED
                    cn = cr["new_text"]
                if tu_state == _term_unify.NOOP:
                    TERM_NOOP.append({"table": cr["_table"], "source": cr["source"],
                                      "file": cr["file"], "locator": cr["locator"],
                                      "old_text": cr["old_text"], "new_text": cr["new_text"]})
                else:
                    layer = "retranslate" if cr["fix_type"] == "retranslate" else "fix_table"
                    layers.append(layer)
                    fix_refs.append({"table": cr["_table"], "locator": cr["locator"],
                                     "fix_type": cr["fix_type"], "cn_before": cn_before})
                    corr_hit.add((cr["source"], cr["file"], cr["locator"]))
                    corr_n += 1

        # ② 译名替换（JP 门控；body → cn，name → 名字框）
        cn, h1 = apply_term(cn, jp, "body")
        sp_cn, h2 = apply_term(sp_cn, sp_jp, "name")
        hits = h1 + h2
        if hits:
            layers.append("name_replace")
            name_n += len(hits)

        # cn_origin = 生效层中优先级最高者（schema §三.2；译名替换不改来源，故不计入）
        _PRI = {"empty": 0, "otv": 1, "fix_table": 2, "retranslate": 3}
        _eff = [l for l in layers if l != "name_replace"]
        origin = max(_eff, key=lambda x: _PRI.get(x, 0)) if _eff else "empty"
        by_origin_all[origin] += 1
        n_origin[origin] += 1
        n_source["empty" if empty_slot else "otv"] += 1

        vid = "" if r["Voice"] is None else str(r["Voice"])
        audio = []
        if vid:
            voices.add(vid)
            rel = AUDIO.get(("voice", vid))
            if rel:
                p = lib_ref("voice", rel)       # W11h：映射到素材库命名空间
                if p:
                    audio.append(p)

        if kind in ("dialogue", "narration"):
            nm = sp_cn if sp_cn else "旁白"
            if nm not in cast:
                cast.append(nm)

        lines_out.append({
            "seq": i, "index": None, "lineno": r["行序"], "kind": kind,
            "speaker": sp_cn, "speaker_jp": sp_jp, "voice": vid,
            "jp": jp, "cn": cn, "cn_origin": origin, "cn_base": base,
            "align_method": align, "layers": layers, "fix_refs": fix_refs,
            "name_replaced": hits, "empty_slot": empty_slot, "d14_exception": None,
            "audio": audio,
        })

    # ---- 后继
    nxt = info["next"]
    nk = "end" if not nxt else ("linear" if len(nxt) == 1 else "branch")

    # ---- phase
    if s == "M01_01":
        phase = "序"
    elif s in ("M09_01", "M09_02"):
        phase = "结局"
    else:
        phase = "个人线"

    assets = info["assets"]
    scenes.append({
        "scene_id": "%s_%s" % (SOURCE, s),
        "source": SOURCE,
        "script": s,
        "source_kind": "new",            # PSV 美咲线在 2009 本篇/R 版中无同名场景（美咲为 PSV 独占）
        "text_source": SOURCE,
        "title_jp": title_jp,
        "title_cn": title_cn,
        "title_variants": tv,
        "game_date": game_date,
        "game_dates": game_dates,
        "phase": phase,
        "route": ROUTE,
        "cast": cast,
        "next": nxt,
        "next_kind": nk,
        "choices": [],
        "line_count": len(lines_out),
        "voice_count": len(voices),
        "assets": assets,
        "assets_missing": [a["ref"] for a in assets if not a["hit"]],
        "stats": {
            "lines_by_origin": dict(n_origin),
            "lines_by_source": dict(n_source),
            "corrections_hit": corr_n,
            "name_replace_count": name_n,
            "empty_slots": empty_n,
            "d14_exceptions": d14_n,
        },
        "lines": lines_out,
    })

# ---------------------------------------------------------------- 自检

w("[7/8] 自检 ...")
tot = sum(x["line_count"] for x in scenes)
v_ref = sum(1 for x in scenes for l in x["lines"] if l["voice"])
v_hit = sum(1 for x in scenes for l in x["lines"] if l["audio"])
a_tot = sum(len(x["assets"]) for x in scenes)
a_hit = sum(1 for x in scenes for a in x["assets"] if a["hit"])

# ---- W11h fail loud：素材库命名空间校验（不得静默放过任何一条引用）
# ① 每条 out_relpath 必须落在 `otv/` 命名空间内（schema §2.1 / 交接说明 C3）；
# ② 每条 out_relpath 必须在 krkr素材库 下真实存在；
# ③ 映射不到素材库条目的引用（MAP_FAILURES）必须为 0，否则报错中止。
NS_BAD = [{"script": x["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
          for x in scenes for a in x["assets"]
          if a["out_relpath"] and not a["out_relpath"].startswith(SOURCE + "/")]
NS_BAD += [{"script": x["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
           for x in scenes for l in x["lines"] for p in l["audio"]
           if not p.startswith(SOURCE + "/")]
NS_MISSING = [{"script": x["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for x in scenes for a in x["assets"]
              if a["out_relpath"] and not os.path.isfile(lib_abspath(a["out_relpath"]))]
NS_MISSING += [{"script": x["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
               for x in scenes for l in x["lines"] for p in l["audio"]
               if not os.path.isfile(lib_abspath(p))]
if MAP_FAILURES or NS_BAD or NS_MISSING:
    sys.stderr.write("!! 素材库命名空间校验失败（fail loud，中止写出）:\n")
    for m in MAP_FAILURES:
        sys.stderr.write("   [映射不到] kind=%s filename=%s\n" % (m["kind"], m["filename"]))
    for m in NS_BAD[:50]:
        sys.stderr.write("   [越出 otv/ 命名空间] %s\n" % (m,))
    for m in NS_MISSING[:50]:
        sys.stderr.write("   [库内不存在] %s\n" % (m,))
    raise SystemExit("!! 共 %d 条映射不到 + %d 条越界 + %d 条库内不存在，已中止（不产出静默掩盖缺口的数据）"
                     % (len(MAP_FAILURES), len(NS_BAD), len(NS_MISSING)))

# 去重口径（跨场景）：不同引用 / 不同编号的命中率（验收标准 4 的口径）
distinct = {}
for x in scenes:
    for a in x["assets"]:
        distinct.setdefault(a["ref"], a)
D_BY_KIND = collections.Counter(v["kind"] for v in distinct.values())
D_HIT_BY_KIND = collections.Counter(v["kind"] for v in distinct.values() if v["hit"])
distinct_voice = set(l["voice"] for x in scenes for l in x["lines"] if l["voice"])
voice_audio_ok = sum(1 for x in scenes for l in x["lines"] if l["voice"] and l["audio"])

report = {
    "scenes": len(scenes),
    "lines_total": tot,
    "lines_baseline_han_json": len(rows),
    "lines_balanced": tot == len(rows),
    "lines_by_category": dict(collections.Counter(
        "台词" if l["kind"] != "summary" else "梗概" for x in scenes for l in x["lines"])),
    "lines_by_kind": dict(collections.Counter(l["kind"] for x in scenes for l in x["lines"])),
    "orig_dist": dict(by_origin_all),
    "per_scene_counts": {x["script"]: x["line_count"] for x in scenes},
    "corrections_total": len(corr_rows),
    "corrections_by_source": dict(collections.Counter(r["source"] for r in corr_rows)),
    "corrections_otv_rows": len(CORR_OTV),
    "corrections_out_of_scope": [{"table": r["_table"], "source": r["source"], "file": r["file"],
                                  "locator": r["locator"]} for r in CORR_OTV_OUT_OF_SCOPE],
    "corrections_hit": len(corr_hit),
    "corrections_hit_detail": [{"table": r["_table"], "file": r["file"], "locator": r["locator"],
                                "fix_type": r["fix_type"]} for r in CORR_OTV
                               if (r["source"], r["file"], r["locator"]) in corr_hit],
    "corrections_gated_out": GATED,
    # ISSUE-20260930-12：`term_unify` 的幂等 no-op 留痕（构建期应为 0——每个目标槽都应命中词形）
    "term_unify_noop": TERM_NOOP,
    "corrections_unhit": [{"table": r["_table"], "file": r["file"], "locator": r["locator"]}
                          for r in CORR_OTV
                          if (r["source"], r["file"], r["locator"]) not in corr_hit
                          and not any(g["locator"] == r["locator"] for g in GATED)],
    "assets_total": a_tot, "assets_hit": a_hit, "assets_missing": a_tot - a_hit,
    "assets_by_kind": {k[5:]: v for k, v in ASSET_STATS.items() if k.startswith("kind_")},
    "assets_distinct_by_kind": dict(D_BY_KIND),
    "assets_distinct_hit_by_kind": dict(D_HIT_BY_KIND),
    "assets_distinct_total": len(distinct),
    "assets_distinct_hit": sum(1 for v in distinct.values() if v["hit"]),
    "voice_refs": v_ref, "voice_hit": v_hit,
    "voice_ids_distinct": len(VOICE_N),
    "voice_ids_used": len(set(l["voice"] for x in scenes for l in x["lines"] if l["voice"])),
    "se_ids_distinct": len(SE_N), "bgm_ids_distinct": len(BGM_N),
    "se_ids_used": len(set(a["ref"].split("\\")[1] for x in scenes for a in x["assets"] if a["kind"] == "se")),
    "bgm_ids_used": len(set(a["ref"].split("\\")[1] for x in scenes for a in x["assets"] if a["kind"] == "bgm")),
    "texture_lines": sum(v["tex_lines"] for v in SCRIPT_INFO.values()),
    "texture_unresolved": TEX_UNRESOLVED,
    "texture_unnamed_loadtexture": TEX_UNNAMED,
    "number_unresolved": CHR_UNRESOLVED,
    "image_unresolved": IMG_UNRESOLVED,
    "image_lines": IMAGE_LINES,
    "image_s_values": dict(collections.Counter(str(x["N_or_s"]) for x in IMAGE_LINES if x["mode"] == 1)),
    "image_f_values": dict(collections.Counter(str(x["f"]) for x in IMAGE_LINES if x["mode"] == 1)),
    "image_mode0_neg1_count": sum(1 for x in IMAGE_LINES if x["mode"] == 0 and x["N_or_s"] == -1),
    "ledger_coverage": dict(LEDGER_COVER),
    # W11h：素材库命名空间（引用可解析）自证
    "lib_root": LIB_ROOT,
    "lib_index_keys": len(LIB_INDEX),
    "lib_map_ok_by_kind": dict(MAP_OK),
    "lib_map_failures": MAP_FAILURES,
    "lib_namespace_violations": NS_BAD,
    "lib_missing_in_library": NS_MISSING,
    "term_hits": sum(x["stats"]["name_replace_count"] for x in scenes),
    "term_hit_detail": [{"script": x["script"], "seq": l["seq"], "field": h["字段"],
                         "原词日文": h["原词日文"], "旧写法": h["旧写法"], "新写法": h["新写法"],
                         "before": h["before"], "after": h["after"], "cn": l["cn"]}
                        for x in scenes for l in x["lines"] for h in l["name_replaced"]],
    "empty_slots": sum(x["stats"]["empty_slots"] for x in scenes),
    "empty_slot_detail": [{"script": x["script"], "seq": l["seq"], "lineno": l["lineno"],
                           "jp": l["jp"], "cn": l["cn"]} for x in scenes for l in x["lines"]
                          if l["empty_slot"]],
    "scenes_with_date": {x["script"]: x["game_date"] for x in scenes if x["game_date"]},
    "scenes_without_date": {x["script"]: SCRIPT_INFO[x["script"]]["header_raw"]
                            for x in scenes if not x["game_date"]},
    "distinct_dates": sorted(set(x["game_date"] for x in scenes if x["game_date"])),
    "next_kind_dist": dict(collections.Counter(x["next_kind"] for x in scenes)),
    "phase_dist": dict(collections.Counter(x["phase"] for x in scenes)),
    "scene_ids_unique": len(set(x["scene_id"] for x in scenes)) == len(scenes),
    "assets_missing_list": [{"script": x["script"], "ref": a["ref"]} for x in scenes
                            for a in x["assets"] if not a["hit"]],
    "samples": {},
}
# 抽样：otv / empty 两层各取实例
for x in scenes:
    for l in x["lines"]:
        for o in ("otv", "empty"):
            if l["cn_origin"] == o and o not in report["samples"]:
                report["samples"][o] = {"script": x["script"], "seq": l["seq"], "kind": l["kind"],
                                        "speaker": l["speaker"], "voice": l["voice"],
                                        "jp": l["jp"], "cn": l["cn"], "layers": l["layers"]}
report["ALL_OK"] = (report["lines_balanced"] and report["scene_ids_unique"]
                    and len(TEX_UNRESOLVED) == 0 and len(CHR_UNRESOLVED) == 0
                    and v_hit == v_ref
                    # W11h：引用必须全部落在素材库命名空间且库内真实存在
                    and not MAP_FAILURES and not NS_BAD and not NS_MISSING
                    and a_hit == a_tot
                    # 修正表三分类守恒：生效 + 门控排除 = 范围内；未命中须为 0
                    and len(report["corrections_unhit"]) == 0
                    and (len(corr_hit) + len(GATED)) == len(CORR_OTV))

os.makedirs(STG, exist_ok=True)
json.dump(report, open(os.path.join(STG, "_build_stats_otv.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 写出

w("[8/8] 写出 scene_otv.jsonl ...")
_assert_in_checkout(OUT, "剧本产物目录")
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "scene_otv.jsonl")
_assert_in_checkout(outpath, "scene_otv.jsonl")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    for x in scenes:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
with open(outpath, encoding="utf-8") as f:
    n = sum(1 for ln in f if json.loads(ln))
w("      -> %s （%d 行，逐行 json.loads OK）" % (outpath, n))

# ---------------------------------------------------------------- 摘要

w("")
w("================ 摘要 ================")
w("场景数          : %d" % len(scenes))
w("行数            : %d （基线 台词对照 %d，守恒=%s）" % (tot, len(rows), report["lines_balanced"]))
w("  按源类别      : %s" % report["lines_by_category"])
w("  按 kind       : %s" % report["lines_by_kind"])
w("cn_origin 分布  : %s" % report["orig_dist"])
w("修正表          : 合计 %d 条（%s）｜ 范围内 source=otv %d 条 → 命中 %d ｜ 门控排除 %d ｜ 未命中 %d"
  % (len(corr_rows), report["corrections_by_source"], len(CORR_OTV), len(corr_hit),
     len(GATED), len(report["corrections_unhit"])))
w("译名替换处数    : %d" % report["term_hits"])
w("term_unify 幂等 no-op: %d 条（构建期应为 0）%s"
  % (len(TERM_NOOP), (" ← " + str(TERM_NOOP[:3])) if TERM_NOOP else ""))
w("素材            : %d/%d 命中（缺 %d）｜ 分类 %s"
  % (a_hit, a_tot, a_tot - a_hit, report["assets_by_kind"]))
w("  去重口径      : %d/%d 命中 ｜ 分类 %s" % (report["assets_distinct_hit"],
      report["assets_distinct_total"], report["assets_distinct_by_kind"]))
w("  去重命中分类  : %s" % report["assets_distinct_hit_by_kind"])
w("  资源总账覆盖  : %s" % report["ledger_coverage"])
w("  素材库命名空间: 索引 %d 键 ｜ 映射 OK %s ｜ 映射不到 %d ｜ 越界 %d ｜ 库内不存在 %d"
  % (len(LIB_INDEX), dict(MAP_OK), len(MAP_FAILURES), len(NS_BAD), len(NS_MISSING)))
w("  素材库根      : %s" % LIB_ROOT)
w("语音            : %d/%d（不同编号 %d）" % (v_hit, v_ref, report["voice_ids_used"]))
w("SE / BGM 编号   : %d / %d（清单内 %d / %d）"
  % (report["se_ids_used"], report["bgm_ids_used"], len(SE_N), len(BGM_N)))
w(":Texture 解析   : 行 %d ｜ 失败 %d ｜ 无注释名（LoadTexture）%d"
  % (report["texture_lines"], len(TEX_UNRESOLVED), len(TEX_UNNAMED)))
w(":Number 解析失败: %d ｜ :Image 未解析 %d" % (len(CHR_UNRESOLVED), len(IMG_UNRESOLVED)))
w("空槽            : %d" % report["empty_slots"])
w("日期            : 有 %d 场景 / 无 %d 场景 ｜ 不同日期 %s"
  % (len(report["scenes_with_date"]), len(report["scenes_without_date"]), report["distinct_dates"]))
w("next_kind 分布  : %s ｜ phase 分布 %s" % (report["next_kind_dist"], report["phase_dist"]))
w("ALL_OK          : %s" % report["ALL_OK"])