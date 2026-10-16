# -*- coding: utf-8 -*-
r"""
W6b · 结构化剧本 scene_ot.jsonl 构建器（本篇主线 s00/s01/s02/s03/s04 · 367 场景）

契约：
  * `资源组\剧本\schema.md`（W6a 定稿 schema —— 字段名/类型/嵌套结构一律沿用，**不另创 schema**）
  * `资源组\修正\_README.md` §四.5（**修正表来源门控**，对所有源模块生效）
  * `资源组\修正\译名统一口径.md` §六 / 作品层 `作品skill\术语表.md` §六（排除规则）
  * `资源组\修正\修正表_0x5C.tsv`（W7-4：0x5C 切分缺陷修正，`fix_type=speaker_split`，覆盖 speaker/voice）
  * `00_项目总纲.md` §八 D14（正文取「独立翻译」源；本篇 = ot 即取文源）

取文来源（本模块）：**全部 `ot`（本篇 `汉化\剧情汉化\<script>.sob.jsonl` 的 `cn`）**。
  → 修正表门控：条目 `source` 与 `cn_base` 不符者不生效。本模块 `cn_base` 恒为 `ot`；
    `修正表_B1B3.tsv` / `修正表_B1B3_扩展.tsv` / `修正表_新增场景mig重译.tsv` 的
    `source` ∈ {otr, otp, ota}（**无 `source=ot` 条目**）→ 三者在本模块**命中恒为 0**（非漏修）。
  → **ISSUE-20260919-09 新增**：`修正表_かるら.tsv`（`source=ot`，37 条，`field=cn`，
    `fix_type=retranslate`）——`かるら` 按**场景世界**分译（グレタガルド幻想侧→伽鲁炟／现实侧→迦楼罗，
    用户 2026-09-19 裁决）。本表 `source=ot`，**在本模块内生效**（非门控排除）。
    locator 采用 `_README.md` §2.2 的 ot 形态：`file=<script>.sob.jsonl`、`locator=script=<n>&seq=<k>`
    （`k` = 源 `seq` = `scene_ot.jsonl` 的 `lines[].lineno`）；命中前断言 `old_text` 逐字符等于
    该行取文基准层 `cn`，不符即 fail loud。

只读：`工程\我们没有翅膀\`、`工程\我们没有翅膀R\`、`资源组\修正\*`、`资源组\krkr素材库\*`
只写：`资源组\剧本\scene_ot.jsonl`、`子代理工作区\ISSUE-20260918-06\W6b\_build_stats_ot.json`

schema 适配（逐项理由见 `资源组\剧本\本篇_产出报告.md` §2）：
  * `source` = `ot`（本模块结构来源＝本篇；W6a 的 `otr` 是 R 版亚衣线专属）
  * `scene_id` = `ot_<script>`
  * `source_kind` = `ot`（枚举按源扩展：W6a 的 shared/branch/new 是 R 版场景与 2009 的关系分类，对本篇不适用）
  * `lines[].kind` = 源值原样（SOB0 只有 `dialogue` / `other` 两值，无 `title`/`narration`）
  * `lines[].index` ← 源 `idx`；`lines[].lineno` ← 源 `seq`（SOB 类定位串为 `seq=<n>`，见 _README §二；
    `修正表_かるら.tsv` 的 ot 形态定位串为 `script=<n>&seq=<k>`，`k` 即此 `lineno`，见 _README §2.2）
  * `align_method` = `ot_direct`（直取本篇语料，无对齐动作）/ `empty_slot`
  * `title_variants[].offset` = 该标题槽在 .sob 中的字节地址 `addr`（本篇无 `offset` 字段）
  * `game_date` 仅当 jp 出现显式 `○月○日`；`phase` 见 §phase 规则

复跑：python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ot.py"
     （可选 --no-speaker-repair 关闭 speaker/voice 拆分修复，见 §speaker 修复）
"""
import json, os, re, csv, sys, glob, collections

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__（同 build_scene_otp.py）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _term_unify               # noqa: E402  同目录共享模块：`term_unify` 语义的唯一实现

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；写 = 本脚本所在 checkout（由 `__file__` 推导）。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, "资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, "修正")                             # 修正表：以本分支副本为准
OUT  = os.path.join(RES_LOCAL, "剧本")                             # 产物：写本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, "资源组")
STG  = os.path.join(WS_LOCAL, "子代理工作区", "ISSUE-20260918-06", "W6b")   # 写本 checkout
LEDGER = os.path.join(RES, "krkr素材库", "资源总账.json")

OTJ  = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "汉化", "剧情汉化")
SOBD = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "汉化", "SCRIPT_CN")
REF  = os.path.join(DATA_ROOT, "工程", "我们没有翅膀R", "参照", "中日对照表.json")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

SOURCE = "ot"
MODULE_GROUPS = ("s00", "s01", "s02", "s03", "s04")
EXCLUDE_GROUPS = ("s03c",)                 # 亚衣线已由 W6a 产出（R 版 55 场景）

TABLES = [
    ("修正表_B1B3.tsv",            os.path.join(FIX, "修正表_B1B3.tsv")),
    ("修正表_B1B3_扩展.tsv",       os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    ("修正表_新增场景mig重译.tsv", os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260919-09：`かるら` 按场景世界分译（source=ot，37 条，field=cn）
    ("修正表_かるら.tsv",          os.path.join(FIX, "修正表_かるら.tsv")),
    # ISSUE-20260930-10：用户 2026-09-30 术语裁决（source 按行门控；field=cn，fix_type=term_unify）
    ("修正表_裁决20260930.tsv",    os.path.join(FIX, "修正表_裁决20260930.tsv")),
    # ISSUE-20261009-04：用户 2026-10-09 裁决「奈落」全量回改（source=ot，139 条，field=cn，
    #   fix_type=retranslate；locator 用 §2.2 的 ot 形态 `script=<n>&seq=<k>`，走 [5b] CORR_OT_FORM 索引）
    ("修正表_奈落.tsv",            os.path.join(FIX, "修正表_奈落.tsv")),
]
TERM_TABLE = os.path.join(FIX, "译名替换表.tsv")

# 修正表来源门控映射（_README §四.5；未登记 source 一律 fail loud）
# 六源全覆盖（ISSUE-20260930-11 补齐 otv/np —— 缺项会让装载该表的本次运行直接 fail loud）
CORR_SOURCE_TO_BASE = {"otr": "otr_new", "otp": "otp", "ota": "ota", "ot": "ot",
                       "otv": "otv", "np": "np"}
GATED = []                     # 被来源门控排除的条目（逐条留痕）
TERM_NOOP = []                 # `term_unify` 的幂等 no-op 留痕（ISSUE-20260930-12；构建期应为 0 条）

NO_REPAIR = "--no-speaker-repair" in sys.argv

# ---------------------------------------------------------------- helpers
def read_tsv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def w(s):
    sys.stdout.write(s + "\n"); sys.stdout.flush()

BS = chr(92)   # 反斜杠

# ---------------------------------------------------------------- [1] 装载源
w("[1/9] 读取本篇语料 ...")
all_jsonl = sorted(os.path.basename(p)[:-10] for p in glob.glob(os.path.join(OTJ, "*.jsonl")))
mod = [n for n in all_jsonl
       if n.startswith(MODULE_GROUPS) and not n.startswith(EXCLUDE_GROUPS)]
modset = set(mod)
sys_scripts = [n for n in all_jsonl if n not in modset and not n.startswith(EXCLUDE_GROUPS)]
w("      本篇脚本 %d ｜ 本模块 %d ｜ s03c（W6a 已产）%d ｜ 系统脚本 %d"
  % (len(all_jsonl), len(mod), sum(1 for n in all_jsonl if n.startswith(EXCLUDE_GROUPS)),
     len(sys_scripts)))

SRC = {}          # script -> [row, ...]（源 jsonl 逐行，只读）
for n in mod:
    rows = [json.loads(l) for l in open(os.path.join(OTJ, n + ".sob.jsonl"), encoding="utf-8")]
    SRC[n] = rows
base_lines = sum(len(v) for v in SRC.values())
w("      本模块源槽数 %d（行数守恒基线）" % base_lines)

# ---------------------------------------------------------------- [2] speaker/voice 拆分修复
# 源缺陷（实测 68 行）：`extract_sob0.py` 的 classify() 按**原始字节 0x5C** 切分
# `#<说话人>\<语音ID>$&`；而 cp932 中 0x5C 同时是若干汉字的**尾字节**（十=8F5C、ソ=835C…），
# 故说话人含这类字时被误切 → 说话人尾部丢字（U+FFFD）、语音 ID 里混入说话人残段。
# 修复判据（确定性，非猜测）：语音 ID 为纯 ASCII，故**最后一个 0x5C 才是真分隔符**；
# 直接回 .sob 原始字节，从 `#` 起按 cp932 解出说话人。默认启用；--no-speaker-repair 可关闭。
w("[2/9] speaker/voice 拆分修复（源缺陷，回 .sob 字节级复原） ...")
REPAIRS = []
REPAIR_FAIL = []
speaker_map_raw = {}
if not NO_REPAIR:
    for n in mod:
        rows = SRC[n]
        broken = [(i, r) for i, r in enumerate(rows) if BS in (r.get("voice") or "")]
        if not broken:
            continue
        raw = open(os.path.join(SOBD, n + ".sob"), "rb").read()
        for i, r in broken:
            vid = r["voice"].rsplit(BS, 1)[-1]
            if not re.fullmatch(r"[A-Za-z0-9_]+", vid):
                continue
            sep_pat = re.compile(re.escape(BS.encode()) + re.escape(vid.encode()) + rb"\$&")
            seps = list(sep_pat.finditer(raw))
            if not seps:
                continue
            # 取 `\vid$&` 之前最近的 `#`（窗口 60 字节）——说话人标签短，不会越界；
            # 不用「首个 # 起非贪婪匹配」：SOB0 指针表里存在裸 `#` 字节，会跨表误配。
            done = False
            for m in seps:
                st = m.start()
                h = raw.rfind(b"#", max(0, st - 60), st)
                if h < 0:
                    continue
                spk_bytes = raw[h + 1:st]
                if not spk_bytes or b"\x00" in spk_bytes:
                    continue
                try:
                    spk = spk_bytes.decode("cp932")
                except UnicodeDecodeError:
                    continue
                if not spk or BS in spk or "\ufffd" in spk:
                    continue
                REPAIRS.append({"script": n, "seq": r["seq"], "addr": r["addr"],
                                "speaker_before": r["speaker"], "voice_before": r["voice"],
                                "speaker_after": spk, "voice_after": vid,
                                "byte_span": [h, m.end()],
                                "evidence": "%s.sob 字节 @%d-%d 按 cp932 复解（末个 0x5C 为真分隔符）"
                                            % (n, h, m.end())})
                speaker_map_raw[(n, i)] = (spk, vid)
                done = True
                break
            if not done:
                REPAIR_FAIL.append({"script": n, "seq": r["seq"],
                                    "speaker": r["speaker"], "voice": r["voice"]})
w("      修复 %d 行（--no-speaker-repair %s）" % (len(REPAIRS), "启用" if NO_REPAIR else "未启用"))

# ---------------------------------------------------------------- [2b] 消费 修正表_0x5C.tsv（W7-4）
# 表由 `资源组\工具\rescan_0x5c.py` 产出：source=ot，locator=`script=<n>&seq=<k>`，
# field=speaker_voice，old_text/new_text = `<说话人>\<语音ID>`（即 classify 切分后的 `#` 后标记头）。
# 消费口径：以表为准覆盖 speaker/voice；逐条与 [2] 的字节复原结果交叉断言，冲突即 fail loud。
SPLIT_TABLE = os.path.join(FIX, "修正表_0x5C.tsv")
SPLIT_APPLIED = []      # 生效（script 属本模块）
SPLIT_GATED = []        # 门控排除（script 不属本模块，如 s03c_* —— 由 scene_otr 覆盖）
SPLIT_CONFLICT = []
seq2idx = {}            # script -> {seq: row_index}
if os.path.isfile(SPLIT_TABLE):
    for r in read_tsv(SPLIT_TABLE):
        if r["source"] != SOURCE:
            raise SystemExit("!! 修正表_0x5C 出现未登记 source: %s" % r["source"])
        m = re.fullmatch(r"script=(.+?)&seq=(\d+)", r["locator"])
        if not m:
            raise SystemExit("!! 修正表_0x5C locator 形态非法: %s" % r["locator"])
        n, seq = m.group(1), int(m.group(2))
        # 门控：script 不属本模块（如 s03c_*，由 scene_otr 覆盖）→ 不生效，但仍须校验 old_text 后留痕
        if n not in modset:
            gp = os.path.join(OTJ, n + ".sob.jsonl")
            if not os.path.isfile(gp):
                raise SystemExit("!! 修正表_0x5C 定位越界（无此脚本）: %s" % r["locator"])
            grow = {x["seq"]: x for x in (json.loads(l) for l in open(gp, encoding="utf-8"))}.get(seq)
            if grow is None:
                raise SystemExit("!! 修正表_0x5C 定位越界（无此 seq）: %s" % r["locator"])
            if r["old_text"] != (grow.get("speaker") or "") + BS + (grow.get("voice") or ""):
                raise SystemExit("!! 修正表_0x5C old_text 与源语料不符: %s" % r["locator"])
            SPLIT_GATED.append((n, seq, r["new_text"]))
            continue
        # 注意：源 `seq` 是抽取器**未过滤列表**的序号，与行索引不等（过滤掉 ascii 行）→ 需查表
        if n not in seq2idx:
            seq2idx[n] = {x["seq"]: i for i, x in enumerate(SRC[n])}
        i = seq2idx[n].get(seq)
        if i is None:
            raise SystemExit("!! 修正表_0x5C 定位越界（无此 seq）: %s" % r["locator"])
        row = SRC[n][i]
        if r["old_text"] != (row.get("speaker") or "") + BS + (row.get("voice") or ""):
            raise SystemExit("!! 修正表_0x5C old_text 与源语料不符: %s" % r["locator"])
        spk_after, vid_after = r["new_text"].rsplit(BS, 1)
        prev = speaker_map_raw.get((n, i))
        if prev is not None and prev != (spk_after, vid_after):
            SPLIT_CONFLICT.append({"locator": r["locator"], "inline": list(prev),
                                   "table": [spk_after, vid_after]})
            continue
        speaker_map_raw[(n, i)] = (spk_after, vid_after)
        SPLIT_APPLIED.append((n, seq, spk_after, vid_after))
    # 完整性：字节复原出的行必须全部见于表（表过期即 fail loud）
    if not NO_REPAIR:
        tbl_keys = {(n, s) for n, s, _, _ in SPLIT_APPLIED}
        inline_keys = {(r["script"], r["seq"]) for r in REPAIRS}
        if inline_keys - tbl_keys:
            raise SystemExit("!! 字节复原行未见于修正表_0x5C: %s" % sorted(inline_keys - tbl_keys))
w("      修正表_0x5C：生效 %d ｜ 门控排除 %d ｜ 冲突 %d ｜ 字节复原 %d ｜ 复原失败 %d"
  % (len(SPLIT_APPLIED), len(SPLIT_GATED), len(SPLIT_CONFLICT), len(REPAIRS), len(REPAIR_FAIL)))
if SPLIT_CONFLICT:
    raise SystemExit("!! 修正表_0x5C 与字节复原冲突: %s" % SPLIT_CONFLICT)

# ---------------------------------------------------------------- [2c] 消费 修正表_说话人译名.tsv（ISSUE-20260919-06）
# 缺陷：部分次要角色标签（含 0x5C 修正后）在 D3 参照语料（`参照\中日对照表.json`）里
# **无 speaker→speaker_cn 映射** → `speaker_cn()` 返回 ""，名字框渲染为空。
# 表形态与 `修正表_0x5C.tsv` 同构：source=ot，locator=`script=<n>&seq=<k>`，
# field=`speaker`，old_text=<真说话人（0x5C 修正后）>，new_text=<中文名字框>，
# fix_type=`speaker_translate`。**与 speaker_split 同类：修的是 speaker 字段，不进 `fix_refs`**
# （schema §4.6：`fix_refs` 只记对 `cn` 的覆盖）。
SPK_TR_TABLE = os.path.join(FIX, "修正表_说话人译名.tsv")
SPK_TR = {}                 # (script, seq) -> (speaker_jp, speaker_cn)
SPK_TR_ROWS = 0
SPK_TR_APPLIED = set()      # 实际生效的 (script, seq)
if os.path.isfile(SPK_TR_TABLE):
    for r in read_tsv(SPK_TR_TABLE):
        if r["source"] != SOURCE:
            raise SystemExit("!! 修正表_说话人译名 出现未登记 source: %s" % r["source"])
        if r["field"] != "speaker" or r["fix_type"] != "speaker_translate":
            raise SystemExit("!! 修正表_说话人译名 field/fix_type 非法: %s" % r["locator"])
        m = re.fullmatch(r"script=(.+?)&seq=(\d+)", r["locator"])
        if not m:
            raise SystemExit("!! 修正表_说话人译名 locator 形态非法: %s" % r["locator"])
        n, seq = m.group(1), int(m.group(2))
        if n not in modset:
            raise SystemExit("!! 修正表_说话人译名 定位越界（script 不属本模块）: %s" % r["locator"])
        if n not in seq2idx:
            seq2idx[n] = {x["seq"]: i for i, x in enumerate(SRC[n])}
        i = seq2idx[n].get(seq)
        if i is None:
            raise SystemExit("!! 修正表_说话人译名 定位越界（无此 seq）: %s" % r["locator"])
        row = SRC[n][i]
        # old_text 断言对象 = **0x5C 修正后的真说话人**（含 0x5C 尾字节的标签源值被截断，不可直接比）
        spk_eff = speaker_map_raw.get((n, i), (row.get("speaker") or "", row.get("voice") or ""))[0]
        if spk_eff != r["old_text"]:
            raise SystemExit("!! 修正表_说话人译名 old_text 与源语料（0x5C 修正后）不符: %s（源=%r 表=%r）"
                             % (r["locator"], spk_eff, r["old_text"]))
        SPK_TR[(n, seq)] = (r["old_text"], r["new_text"])
        SPK_TR_ROWS += 1
w("      修正表_说话人译名：装载 %d 条（%s）" % (SPK_TR_ROWS, SPK_TR_TABLE))

# ---------------------------------------------------------------- [3] 素材总账 ot 索引
w("[3/9] 建立素材总账 ot 索引 ...")
led = json.load(open(LEDGER, encoding="utf-8"))
ot_idx = collections.defaultdict(dict)
for e in led["entries"]:
    if e["source"] != SOURCE:
        continue
    ot_idx[e["kind"]][os.path.splitext(e["orig_name"])[0].lower()] = e["out_relpath"]
w("      ot 各类条数 %s" % {k: len(v) for k, v in sorted(ot_idx.items())})

D2K = {"PIC": "pic", "SE": "se", "SYS": "sys", "CHR": "chr", "BGM": "bgm", "VOICE": "voice"}
REF_RE = re.compile(rb"([A-Za-z_]{2,6})[\\/]([A-Za-z0-9_]+)\.(ELG|OGG)")
LAB_RE = re.compile(rb"\b(S[0-9]{2}[A-Z]?_[0-9A-Z]+)\b")

def map_ref(d, stem, ext):
    k = D2K.get(d.upper(), "etc")
    return k, ot_idx.get(k, {}).get(stem.lower())

def map_voice(vid):
    return ot_idx.get("voice", {}).get((vid or "").lower())

# ---------------------------------------------------------------- [4] 逐脚本扫 .sob（标签 / 素材引用）
w("[4/9] 扫描 .sob：跳转标签 + 素材引用顺序 ...")
next_map, asset_map, raw_labels = {}, {}, {}
for n in mod:
    raw = open(os.path.join(SOBD, n + ".sob"), "rb").read()
    labs = []
    for m in LAB_RE.findall(raw):
        s = m.decode("ascii")
        if s not in labs:
            labs.append(s)
    raw_labels[n] = labs
    next_map[n] = sorted({s.lower() for s in labs} - {n})
    seen, order = set(), []
    for m in REF_RE.finditer(raw):
        key = (m.group(1).decode(), m.group(2).decode(), m.group(3).decode())
        if key not in seen:
            seen.add(key); order.append(key)
    asset_map[n] = order

# ---------------------------------------------------------------- [5] 修正表 / 译名替换表
w("[5/9] 装载修正表与译名替换表 ...")
corrections, corr_rows = {}, []
for tn, tp in TABLES:
    for r in read_tsv(tp):
        r["_table"] = tn
        # ISSUE-20261009-04b（E3）：CSV **单元格内换行**归一（`\r\n` → `\n`）。
        # `修正表_奈落.tsv` 有 2 条记录的 old_text/new_text 内含换行（RFC4180 引号包裹）；
        # 作者态与取文基准层均为 `\n`，但 `core.autocrlf=true` 的检出会把单元格内换行一并
        # 转成 `\r\n`（git 不解析 CSV）⇒ 不归一会令 old_text 断言在 CRLF 检出下误报、
        # 且 new_text 直写会把 `\r\n` 嵌进产物。对无多行字段的表为恒等变换。
        r["old_text"] = r["old_text"].replace("\r\n", "\n")
        r["new_text"] = r["new_text"].replace("\r\n", "\n")
        corr_rows.append(r)
        key = (r["source"], r["file"], r["locator"])
        if key in corrections:
            raise SystemExit("!! 修正表定位冲突: %s" % (key,))
        corrections[key] = r
for r in corr_rows:
    if r["source"] not in CORR_SOURCE_TO_BASE:
        raise SystemExit("!! 修正表 source 未登记门控映射: %s @ %s/%s"
                         % (r["source"], r["file"], r["locator"]))
w("      修正表合计 %d 条（%s）"
  % (len(corr_rows), " / ".join("%s=%d" % (t, sum(1 for r in corr_rows if r["_table"] == t))
                                for t, _ in TABLES)))

# ---------------------------------------------------------------- [5c] 奈落表 new_text 闸门
# ISSUE-20261009-04b（E3 / 一审 A2-N2）：`new_text` 侧原无机器约束——改一个与奈落
# 无关的字仍 EXIT=0 并静默进语料。本闸门对 `修正表_奈落.tsv` 的
# `retranslate` + `field=cn` 行在装载期逐行 fail loud（**不移除/不放宽任何既有断言**）：
#   ① 差异白名单：`new_text` 相对 `old_text` 的改动只允许——
#      · 「地狱→奈落」（本表本义）；
#      · 下表 `NR_WRITE_ALLOW` 逐行登记的 ③ 写形（② 直写后 ③ 不再命中，净效果为零；
#        与表内 evidence 列的 E3 登记一一对应）。
#      其余任何字符改动 ⇒ SystemExit（防 N2 类静默篡改）。
#   ② JP 门控：奈落增量 == 该行 JP 的「奈落＋ならく」出现数。
#   ③ 登记防腐烂：白名单的新写形必须真的出现在该行 `new_text` 中。
# 实现：先按本行白名单把 ③ 写形回退（新→旧），再断言「奈落」逆替换后逐字符等于 `old_text`。
NR_WRITE_ALLOW = {
    # ISSUE-20261009-04b（E3 / 方案 b）：14 行 new_text 已含 ③ 译名替换的当期结果（净效果为零）。
    # 键 = locator；值 = 需回退的（旧写形, 新写形）对。改动本表须同步该行 evidence 登记。
    "script=s04_01a&seq=3": [("伽楼罗", "迦楼罗")],
    "script=s04_01b1&seq=3": [("伽楼罗", "迦楼罗")],
    "script=s04_01b2&seq=3": [("伽楼罗", "迦楼罗")],
    "script=s04_01b2&seq=71": [("妲朴公主", "妲朴小公主")],
    "script=s04_02a&seq=3": [("伽楼罗", "迦楼罗")],
    "script=s04_03b&seq=13": [("伽楼罗", "迦楼罗")],
    "script=s04_03i&seq=688": [("伽楼罗", "迦楼罗")],
    "script=s04_04a&seq=176": [("洋治", "小鹰志")],
    "script=s04_05a&seq=3": [("伽楼罗", "迦楼罗"), ("洋治", "小鹰志")],
    "script=s04_05b&seq=3": [("洋治", "小鹰志")],
    "script=s04_05h&seq=3": [("洋治", "小鹰志")],
    "script=s04_05i&seq=3": [("伽楼罗", "迦楼罗"), ("洋治", "小鹰志")],
    "script=s04_05i&seq=437": [("妲朴公主", "妲朴小公主")],
    "script=s04_06j1&seq=3": [("伽楼罗", "迦楼罗"), ("洋治", "小鹰志")],
}
JP_BY_KEY = {(n, x["seq"]): (x.get("jp") or "") for n, rows_ in SRC.items() for x in rows_}
NR_GATE_ROWS = 0
for r in corr_rows:
    if not (r["_table"] == "修正表_奈落.tsv"
            and r["fix_type"] == "retranslate" and r["field"] == "cn"):
        continue
    NR_GATE_ROWS += 1
    u = r["new_text"]
    for old_f, new_f in NR_WRITE_ALLOW.get(r["locator"], []):
        if new_f not in u:
            raise SystemExit("!! 修正表_奈落 白名单写形未出现在 new_text（登记腐烂）: %s %s→%s"
                             % (r["locator"], old_f, new_f))
        u = u.replace(new_f, old_f)
    if u.replace("奈落", "地狱") != r["old_text"]:
        raise SystemExit("!! 修正表_奈落 new_text 含未登记改动"
                         "（只允许 地狱→奈落 ＋ NR_WRITE_ALLOW 白名单写形）: %s" % r["locator"])
    m = re.fullmatch(r"script=(.+?)&seq=(\d+)", r["locator"])
    if m:
        jp = JP_BY_KEY.get((m.group(1), int(m.group(2))))
        if jp is not None:
            n_inc = r["new_text"].count("奈落") - r["old_text"].count("奈落")
            n_jp = jp.count("奈落") + jp.count("ならく")
            if n_inc != n_jp:
                raise SystemExit("!! 修正表_奈落 奈落增量(%d) != JP 奈落/ならく 数(%d): %s"
                                 % (n_inc, n_jp, r["locator"]))
w("      [5c] 奈落表 new_text 闸门：%d 行通过 ｜ 白名单登记 %d 行"
  % (NR_GATE_ROWS, len(NR_WRITE_ALLOW)))

corr_hit = set()

def file_stem(f):
    for suf in (".tob", ".sob.jsonl", ".sob"):
        if f.endswith(suf):
            return f[:-len(suf)]
    return f

def in_module(f):
    return file_stem(f) in modset

# ---------------------------------------------------------------- [5b] ot 形态定位索引（_README §2.2）
# `修正表_かるら.tsv`（source=ot）用 `file=<script>.sob.jsonl` + `locator=script=<n>&seq=<k>`；
# 而本模块通用路径的定位串是 `file=<script>.sob` + `locator=seq=<k>`（见 [8] ②）。两者形态不同，
# 故另建 `(script, seq)` 索引（`seq` = 源 seq = `scene_ot.jsonl` 的 `lines[].lineno`），
# **不改动通用路径的定位语义**；两路命中结果在 [8] ② 合流，门控与 `old_text` 断言口径一致。
CORR_OT_FORM = {}     # (script, seq) -> row
for r in corr_rows:
    if r["source"] != SOURCE:
        continue
    m = re.fullmatch(r"script=(.+?)&seq=(\d+)", r["locator"])
    if not m:
        raise SystemExit("!! 修正表 source=ot 条目的 locator 非 ot 形态（_README §2.2）: %s @ %s"
                         % (r["locator"], r["file"]))
    if file_stem(r["file"]) != m.group(1):
        raise SystemExit("!! 修正表 source=ot 条目 file 与 locator 的 script 不一致: %s @ %s"
                         % (r["locator"], r["file"]))
    k = (m.group(1), int(m.group(2)))
    if k in CORR_OT_FORM:
        raise SystemExit("!! 修正表 ot 形态定位冲突: %s" % (k,))
    CORR_OT_FORM[k] = r
w("      ot 形态（script=&seq=）条目 %d 条" % len(CORR_OT_FORM))

term_rows = read_tsv(TERM_TABLE)
TERM_RULES, TERM_NOTE = [], []
for r in term_rows:
    new, old = r["新写法"].strip(), r["旧写法"].strip()
    scope = r["适用范围(源代号)"].strip()
    if new.startswith("（") or old.startswith("（") or scope == "—":
        continue
    if "/" in scope:
        src, stream = scope.split("/", 1)
    else:
        src, stream = scope, "body"
    if src == "全部":
        continue
    stream = "name" if stream == "name" else "body"
    if src != SOURCE or stream != "body":
        continue                        # 本模块只消费 src=ot 的 body 规则（ot 语料无中文名字框）
    # 表本体缺陷：row 43 的「新写法」把置信度标记写进了替换值（`苍穹女子学院（低置信）`）
    if new.endswith("（低置信）"):
        TERM_NOTE.append({"原词日文": r["原词日文"], "旧写法": old,
                          "新写法_原": new, "新写法_用": new[:-len("（低置信）")],
                          "处置": "剥离尾部置信度标记（该标记是注释，非写形本体）"})
        new = new[:-len("（低置信）")]
    TERM_RULES.append({"jp": r["原词日文"].strip(), "old": old, "new": new,
                       "旧写法出现次数": r["旧写法出现次数"].strip(),
                       "table_note": r["备注"].strip()})
w("      src=ot/body 可用替换规则 %d 条（表本体注记 %d 条）" % (len(TERM_RULES), len(TERM_NOTE)))

# §六 排除规则（正则），键 = (原词日文, 旧写法)
EXCL = {
    ("渡来さん", "渡来（裸名）"): re.compile(r"渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香)"),
    ("委員長", "委员长"):        re.compile(r"(?<!执行)委员长"),
    ("ハヤブサ", "隼"):          re.compile(r"(?<!游)隼(?!人)"),
    ("ソラ学", "空学"):          re.compile(r"(?<!美)空学(?!院|府)"),
    ("針生", "针生"):            re.compile(r"针生(?!同学|前辈|君|先生|小姐|老师|哥|姐)"),
    ("ガルーダ", "伽楼罗"):      re.compile(r"(?<!伊丹)伽楼罗"),
}
JP_SKIP = {"ガルーダ": ["伽楼羅"]}
CONTEXT_FLAGGED = {"ペガサス", "ドラさん"}

# ---------------------------------------------------------------- [6] 说话人名字框中文映射
# 本模块事实：本篇汉化**未译名字框**（`交付说明.md` §二「说话人标签（314 种）原样保留」；
# 本篇 作品skill 术语表 §一「说话人标签 原样保留，不译」）→ 本篇语料内**不存在 speaker_cn**。
# schema 要求 `speaker` = 名字框中文，故按 **D3 仲裁语料**（`参照\中日对照表.json` 的 speaker→speaker_cn）
# 取值——D3 明文「译名统一基准＝新米实测写形」，且 D4 允许新米用于**人名/地名/词级**。
w("[6/9] 建立说话人名字框映射（D3 仲裁语料 speaker→speaker_cn） ...")
refmap = collections.defaultdict(collections.Counter)
for x in json.load(open(REF, encoding="utf-8")):
    s, c = (x.get("speaker") or ""), (x.get("speaker_cn") or "")
    if s:
        refmap[s][c] += 1
SPEAKER_CN, SPEAKER_MISS, SPEAKER_AMB = {}, [], []
def speaker_cn(jp):
    if not jp:
        return ""
    if jp in SPEAKER_CN:
        return SPEAKER_CN[jp]
    c = refmap.get(jp)
    if not c:
        SPEAKER_MISS.append(jp); SPEAKER_CN[jp] = ""; return ""
    # 取「非空写形」中出现最多者：参照语料里同一标签的空值代表「该槽无名字框」（旁白槽），
    # 不是译法；故空值不参与定名，仅当全部为空时才落 ""（并计入缺失）。
    ne = {k: v for k, v in c.items() if k}
    if not ne:
        SPEAKER_MISS.append(jp); SPEAKER_CN[jp] = ""; return ""
    best = max(ne.items(), key=lambda kv: (kv[1], kv[0]))
    if len(ne) > 1 or len(c) > 1:
        SPEAKER_AMB.append({"日文标签": jp, "分布": dict(c), "取值": best[0],
                            "非空写形数": len(ne)})
    SPEAKER_CN[jp] = best[0]
    return best[0]

# ---------------------------------------------------------------- [7] 日期 / 标题 / 阶段
DATE_RE = re.compile("[０-９0-9]{1,2}月[０-９0-9]{1,2}日")
ZEN = {chr(0xFF10 + i): str(i) for i in range(10)}
def zen2han(s):
    return "".join(ZEN.get(c, c) for c in s)

def scan_dates(rows):
    out = []
    for r in rows:
        for m in DATE_RE.finditer(r["jp"] or ""):
            s = zen2han(m.group(0)); mm, dd = s.split("月")
            out.append({"date": "%02d/%02d" % (int(mm), int(dd.rstrip("日"))), "line_index": r["seq"]})
    seen, res = set(), []
    for x in out:
        if x["date"] not in seen:
            seen.add(x["date"]); res.append(x)
    return res

# 章节标题判据（实测 + 交叉验证，见报告 §2.4）：
#   kind='other' 且 sel=0 且 td=0 的槽 = 标题 / 梗概 / 选项；再排除
#   ① 选项槽（sel>0 已在上一条件排除）
#   ② 梗概槽：jp 以 U+3000 开头，或 len(jp) > 40（实测标题 ≤20 字、梗概 ≥81 字，间隔 61 字）
def is_summary(jp):
    return jp.startswith("\u3000") or len(jp) > 40

def title_slots(rows):
    return [r for r in rows if r["kind"] == "other" and r["td"] == 0 and r["sel"] == 0
            and not is_summary(r["jp"])]

# 结局 / 收束脚本（依据 `01_剧情流程图.md` §五 结局矩阵）
END_SCRIPTS = {"s01_16a", "s01_18a", "s01_19a", "s02_16a", "s02_17a",
               "s03_22a", "s03_23a", "s04_28b", "s04_29a"}
ROUTE = {"s00": "s00 序文", "s01": "s01 鹰志线", "s02": "s02 鹫介线",
         "s03": "s03 隼人线", "s04": "s04 大路线"}

def phase_of(n):
    g = n.split("_")[0]
    if g == "s00":
        return "序"
    if n in END_SCRIPTS:
        return "结局"
    if g == "s04":
        return "真相"
    return "个人线"

# ---------------------------------------------------------------- [8] 逐场景组装
w("[7/9] 组装 %d 场景 ..." % len(mod))

ORIGIN_RANK = {"empty": 0, "ot": 1, "fix_table": 3, "retranslate": 4}

def apply_term(cn, jp, stream):
    hits = []
    if not cn:
        return cn, hits
    for rule in TERM_RULES:
        if rule["jp"] not in jp:
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

def build_scene(n):
    rows = SRC[n]
    file_ = n + ".sob"
    out_lines, cast = [], []
    voices = set()
    by_origin, by_src = collections.Counter(), collections.Counter()
    corr_scene = repl_scene = empty_scene = fix_repair = spk_tr_fix = 0

    for i, r in enumerate(rows, 1):
        idx, seq, addr = r["idx"], r["seq"], r["addr"]
        jp = r["jp"] or ""
        cn = r["cn"] or ""
        spk_jp, vid = r["speaker"], r["voice"] or ""
        if (n, i - 1) in speaker_map_raw:
            spk_jp, vid = speaker_map_raw[(n, i - 1)]
            fix_repair += 1

        # ① 取文：本篇 jsonl 的 cn 直取
        empty_slot = (not jp and not cn)
        base = "empty" if empty_slot else "ot"
        align = "empty_slot" if empty_slot else "ot_direct"
        layers = [] if empty_slot else [base]

        # ② 修正表：(source,file,locator) 三元组定位 → §四.5 来源门控
        #    通用路径的 SOB 类定位串为 `seq=<n>`（_README §二）；
        #    source=ot 的 ot 形态（_README §2.2）为 `script=<n>&seq=<k>`，走 [5b] 的 CORR_OT_FORM 索引。
        fix_refs = []
        loc = "seq=%d" % seq
        row = corrections.get((SOURCE, file_, loc))
        if row is None:
            row = CORR_OT_FORM.get((n, seq))
        if row is not None:
            # `term_unify` 与取文层无关（术语统一对任何层的文本都成立）⇒ 不受来源门控约束；
            # 其余 fix_type 仍按 §四.5 门控（防用某层重译顶掉另一层译文）。
            # 见 `资源组\修正\_README.md` §四.5（ISSUE-20260930-11 补充）。
            want = CORR_SOURCE_TO_BASE[row["source"]]
            if want == base or row["fix_type"] == "term_unify":
                cn_before = cn
                if row["fix_type"] == "term_unify":
                    # ISSUE-20260930-12：`term_unify` 是**词形级替换**——`old_text` = 词形正则、
                    # `new_text` = 替换值（**不是整句**）。命中即 re.sub（只碰术语那几个字）；
                    # 已是后态 ⇒ 幂等 no-op（**不记 fix_refs、不计命中**）；两者都不是 ⇒ fail loud。
                    cn, tu_state = _term_unify.apply(cn, row["old_text"], row["new_text"])
                else:
                    # old_text 逐字符断言（与 `修正表_0x5C` / `修正表_说话人译名` 同口径）：
                    # 断言对象 = 该行**取文基准层 cn**（修正前、译名替换前）——不符即 fail loud。
                    if row["old_text"] != cn_before:
                        raise SystemExit(
                            "!! 修正表 old_text 与取文基准层 cn 不符: %s %s（源=%r 表=%r）"
                            % (row["_table"], row["locator"], cn_before, row["old_text"]))
                    tu_state = _term_unify.APPLIED
                    cn = row["new_text"]
                if tu_state == _term_unify.NOOP:
                    TERM_NOOP.append({"table": row["_table"], "source": row["source"],
                                      "file": row["file"], "locator": row["locator"],
                                      "old_text": row["old_text"], "new_text": row["new_text"]})
                else:
                    o = "retranslate" if row["fix_type"] == "retranslate" else "fix_table"
                    layers.append(o)
                    fix_refs.append({"table": row["_table"], "locator": row["locator"],
                                     "fix_type": row["fix_type"], "cn_before": cn_before})
                    corr_scene += 1
                    # 只记「条目自身的 (source,file,locator)」——`corrections_hit` 是**条目计数**，
                    # 不得因 ot 形态另记一份通用键（会重复计数）；通用路径下 row["file"]==file_、
                    # row["locator"]==loc，故与旧口径逐格一致。
                    corr_hit.add((row["source"], row["file"], row["locator"]))
            else:
                GATED.append({"table": row["_table"], "source": row["source"], "file": row["file"],
                              "locator": row["locator"], "kind": row["kind"], "fix_type": row["fix_type"],
                              "script": n, "seq": seq, "cn_base": base, "jp": jp,
                              "cn_kept": cn, "cn_gated": row["new_text"],
                              "old_text": row["old_text"],
                              "reason": "source_gate: 条目 source=%s 对应取文基准 %s，"
                                        "而该行取文基准为 %s → 不生效" % (row["source"], want, base)})

        # ③ 译名替换（JP 门控 + §六 排除规则）
        cn, hits = apply_term(cn, jp, "body")
        if hits:
            layers.append("name_replace")
            repl_scene += len(hits)

        if empty_slot:
            empty_scene += 1
        origin = base
        for lay in layers:
            if lay == "name_replace":
                continue
            if ORIGIN_RANK.get(lay, -1) > ORIGIN_RANK.get(origin, -1):
                origin = lay
        if not layers:
            origin = "empty"
        by_origin[origin] += 1
        by_src[SOURCE] += 1

        spk_cn = speaker_cn(spk_jp)
        # [2c] 说话人译名补充（D3 参照语料无该标签时）——只填空，不覆盖已有中文名字框
        if not spk_cn:
            tr = SPK_TR.get((n, seq))
            if tr is not None:
                spk_cn = tr[1]
                spk_tr_fix += 1
                SPK_TR_APPLIED.add((n, seq))
        if vid:
            voices.add(vid)
        p = map_voice(vid) if vid else None

        # cast：仅计「台词/旁白」行；标题槽与梗概槽不计入（schema §一）
        is_body_text = (r["kind"] == "dialogue") or (r["kind"] == "other" and r["td"] == 1)
        if is_body_text:
            nm = spk_cn if spk_cn else "旁白"
            if nm not in cast:
                cast.append(nm)

        out_lines.append({
            "seq": i, "index": idx, "lineno": seq, "kind": r["kind"],
            "speaker": spk_cn, "speaker_jp": spk_jp, "voice": vid,
            "jp": jp, "cn": cn,
            "cn_origin": origin, "cn_base": base, "align_method": align,
            "layers": layers, "fix_refs": fix_refs,
            "name_replaced": hits, "empty_slot": empty_slot,
            "d14_exception": None,
            "audio": [p] if p else [],
        })

    # ---- 标题
    ts = title_slots(rows)
    tmap = {t["seq"]: l for t, l in zip(ts, [x for x in out_lines if x["kind"] == "other"
                                             and x["index"] == 0])}  # 占位，下面重算
    tl = [(r, l) for r, l in zip(rows, out_lines)
          if r["kind"] == "other" and r["td"] == 0 and r["sel"] == 0 and not is_summary(r["jp"])]
    prim = tl[-1][1] if tl else None
    for _, l in tl:
        if l["cn_origin"] in ("ot", "fix_table", "retranslate"):
            prim = l
    title_variants = [{"offset": r["addr"], "jp": l["jp"], "cn": l["cn"],
                       "cn_origin": l["cn_origin"]} for r, l in tl]

    # ---- 后继
    nxt = next_map[n]
    nk = "end" if not nxt else ("linear" if len(nxt) == 1 else "branch")

    # ---- 选择支（sel>0 的槽 = 脚本内实测的选择支串；本篇仅这些算「已确证玩家选择支」）
    choices = []
    grp = collections.defaultdict(list)
    for r, l in zip(rows, out_lines):
        if r["sel"] > 0:
            grp[r["addr"]].append((r, l))
    for addr in sorted(grp):
        opts = sorted(grp[addr], key=lambda x: x[0]["idx"])
        for r, l in opts:
            choices.append({
                "text_jp": l["jp"], "text_cn": l["cn"] or None,
                "cn_origin": "ot" if l["cn"] else None,
                "target": None, "pairing_verified": False, "confirmed": True,
                "evidence": "%s.sob 选择支串实测存在（sel=%d, addr=%d, idx=%d）；候选目标 %s；"
                            "选项↔目标配对未逆向（SOB0 分支语义未逆向，总纲 R1）；"
                            "译文取自本篇语料（cn_origin=ot）"
                            % (n, r["sel"], addr, r["idx"],
                               "/".join(t.upper() for t in nxt) or "无"),
            })

    # ---- 素材（场景级；按 .sob 内首次出现顺序）
    assets, missing = [], []
    for d, stem, ext in asset_map[n]:
        k, p = map_ref(d, stem, ext)
        ref = "%s%s%s.%s" % (d, BS, stem, ext)
        assets.append({"ref": ref, "kind": k, "out_relpath": p, "hit": bool(p)})
        if not p:
            missing.append(ref)

    bases = {l["layers"][0] for l in out_lines if l["layers"]}
    text_source = "ot" if (not bases or bases == {"ot"}) else "mixed"

    return {
        "scene_id": "%s_%s" % (SOURCE, n),
        "source": SOURCE,
        "script": n,
        "source_kind": "ot",
        "text_source": text_source,
        "title_jp": prim["jp"] if prim else None,
        "title_cn": prim["cn"] if prim else None,
        "title_variants": title_variants,
        "game_date": None,
        "game_dates": [],
        "phase": phase_of(n),
        "route": ROUTE[n.split("_")[0]],
        "cast": cast,
        "next": nxt,
        "next_kind": nk,
        "choices": choices,
        "line_count": len(out_lines),
        "voice_count": len(voices),
        "assets": assets,
        "assets_missing": missing,
        "stats": {
            "lines_by_origin": dict(by_origin),
            "lines_by_source": dict(by_src),
            "corrections_hit": corr_scene,
            "name_replace_count": repl_scene,
            "empty_slots": empty_scene,
            "d14_exceptions": 0,
        },
        "_speaker_split_repairs": fix_repair,
        "_spk_tr_fix": spk_tr_fix,
        "lines": out_lines,
    }

scene_objs = [build_scene(n) for n in mod]

# 日期回填
for s in scene_objs:
    d = scan_dates(SRC[s["script"]])
    s["game_dates"] = d
    s["game_date"] = d[0]["date"] if d else None

# ---------------------------------------------------------------- [9] 自检
w("[8/9] 自检 ...")
tot_lines = sum(s["line_count"] for s in scene_objs)
per_scene_ok = all(s["line_count"] == len(SRC[s["script"]]) for s in scene_objs)
orig_dist, src_dist = collections.Counter(), collections.Counter()
for s in scene_objs:
    for k, v in s["stats"]["lines_by_origin"].items():
        orig_dist[k] += v
    for k, v in s["stats"]["lines_by_source"].items():
        src_dist[k] += v

in_scope_corr = [r for r in corr_rows if in_module(r["file"])]
gated_keys = {(g["source"], g["file"], g["locator"]) for g in GATED}

# 模块范围门控（§四.5 的模块级适用）：
# 条目 `file` 落在本模块脚本集合内，但**本模块取文基准恒为 `ot`**；
# 凡 `source≠ot` 者，其对应基准（otr_new / otp / ota）在本模块内**根本不存在** → 该条目无对象，
# 一律判为「门控排除」并逐条留痕（不得计作「未命中」——否则会被误读成漏修）。
# `source=ot` 条目才走行级查找（`(ot, <script>.sob, seq=<n>)`），未命中即真漏修。
for r in corr_rows:
    if not in_module(r["file"]):
        continue
    key = (r["source"], r["file"], r["locator"])
    if key in corr_hit or key in gated_keys:
        continue
    want = CORR_SOURCE_TO_BASE[r["source"]]
    if want == "ot":
        continue
    GATED.append({"table": r["_table"], "source": r["source"], "file": r["file"],
                  "locator": r["locator"], "kind": r["kind"], "fix_type": r["fix_type"],
                  "script": file_stem(r["file"]), "seq": None, "cn_base": None,
                  "jp": None, "cn_kept": None, "cn_gated": r["new_text"],
                  "old_text": r["old_text"],
                  "reason": "module_source_gate: 条目 source=%s 对应取文基准 %s；"
                            "本模块（本篇 ot）取文基准恒为 ot，该基准在本模块内不存在 → 无对象、不生效"
                            % (r["source"], want)})
    gated_keys.add(key)

miss_corr = [r for r in in_scope_corr
             if (r["source"], r["file"], r["locator"]) not in corr_hit
             and (r["source"], r["file"], r["locator"]) not in gated_keys]
out_scope_corr = [r for r in corr_rows if not in_module(r["file"])]

# ---- 译名替换：与 `译名替换表.tsv` 的「旧写法出现次数」逐规则对账
# 表内计数为**全源口径**（本篇 397 脚本）；本模块只覆盖 367 脚本，故需分口径核对。
w("      译名替换逐规则对账（本模块 / 全源 397 脚本 / 表内计数） ...")
ALLSRC = {}
for n in all_jsonl:
    try:
        ALLSRC[n] = [json.loads(l) for l in open(os.path.join(OTJ, n + ".sob.jsonl"), encoding="utf-8")]
    except Exception:
        pass

def count_rule(rule, scripts):
    """JP 门控 + 排除规则下，含旧写法的槽数"""
    rx = EXCL.get((rule["jp"], rule["old"]))
    skip = JP_SKIP.get(rule["jp"])
    slots = 0
    for n in scripts:
        for r in ALLSRC.get(n, SRC.get(n, [])):
            jp, cn = r.get("jp") or "", r.get("cn") or ""
            if rule["jp"] not in jp or not cn:
                continue
            if skip and any(s in jp for s in skip):
                continue
            hit = rx.search(cn) if rx is not None else (rule["old"] in cn)
            if hit:
                slots += 1
    return slots

term_recon = []
for rule in TERM_RULES:
    try:
        spec = int(rule["旧写法出现次数"])
    except Exception:
        spec = None
    term_recon.append({
        "原词日文": rule["jp"], "旧写法": rule["old"], "新写法": rule["new"],
        "表内计数": spec,
        "本模块槽数": count_rule(rule, mod),
        "全源397槽数": count_rule(rule, all_jsonl),
    })

a_total = sum(len(s["assets"]) for s in scene_objs)
a_hit = sum(1 for s in scene_objs for a in s["assets"] if a["hit"])
v_ref = sum(1 for s in scene_objs for l in s["lines"] if l["voice"])
v_hit = sum(1 for s in scene_objs for l in s["lines"] if l["audio"])
term_slots = collections.Counter()
for s in scene_objs:
    per = collections.defaultdict(set)
    for l in s["lines"]:
        for h in l["name_replaced"]:
            per[(h["原词日文"], h["旧写法"])].add(l["lineno"])
    for k, v in per.items():
        term_slots[k] += len(v)

choice_scripts = sorted({s["script"] for s in scene_objs if s["choices"]})
sel1 = sum(1 for s in scene_objs for c in s["choices"]
           for r in SRC[s["script"]] if r["sel"] == 1 and r["jp"] == c["text_jp"])
sel1 = sum(1 for n in choice_scripts for r in SRC[n] if r["sel"] == 1)
sel2 = sum(1 for n in choice_scripts for r in SRC[n] if r["sel"] == 2)

title_check = []
for s in scene_objs:
    tt = s["title_jp"]
    if tt and ("エピローグ" in tt or "解纜" in tt) and s["phase"] != "结局":
        title_check.append({"script": s["script"], "title": tt, "phase": s["phase"],
                            "flag": "标题含 エピローグ/解纜 但 phase≠结局"})
    if s["phase"] == "结局" and not (tt and ("エピローグ" in tt or "解纜" in tt)):
        title_check.append({"script": s["script"], "title": tt, "phase": s["phase"],
                            "flag": "phase=结局 但标题不含 エピローグ/解纜"})

report = {
    "module": "W6b", "source": SOURCE, "scenes": len(scene_objs),
    "scripts_by_group": dict(collections.Counter(n.split("_")[0] for n in mod)),
    "lines_total": tot_lines, "lines_baseline_src_jsonl": base_lines,
    "lines_balanced": tot_lines == base_lines,
    "per_scene_line_conserved": per_scene_ok,
    "orig_dist": dict(orig_dist), "src_dist": dict(src_dist),
    "text_source_dist": dict(collections.Counter(s["text_source"] for s in scene_objs)),
    "source_kind_dist": dict(collections.Counter(s["source_kind"] for s in scene_objs)),
    "phase_dist": dict(collections.Counter(s["phase"] for s in scene_objs)),
    "next_kind_dist": dict(collections.Counter(s["next_kind"] for s in scene_objs)),
    "align_method_dist": dict(collections.Counter(l["align_method"] for s in scene_objs
                                                 for l in s["lines"])),
    "corrections_total": len(corr_rows),
    "corrections_in_scope": len(in_scope_corr),
    "corrections_hit": len(corr_hit),
    "corrections_gated": len(GATED),
    # ISSUE-20260930-12：`term_unify` 的幂等 no-op 留痕（构建期应为 0——每个目标槽都应命中词形）
    "term_unify_noop": TERM_NOOP,
    "corrections_missing_in_scope": [(r["_table"], r["source"], r["file"], r["locator"],
                                      r["fix_type"]) for r in miss_corr],
    "corrections_out_of_scope": len(out_scope_corr),
    "corrections_out_of_scope_by_source": dict(collections.Counter(
        r["source"] for r in out_scope_corr)),
    "corrections_gated_out": GATED,
    "corrections_in_scope_list": [{"table": r["_table"], "source": r["source"], "file": r["file"],
                                   "locator": r["locator"], "kind": r["kind"],
                                   "fix_type": r["fix_type"], "new_text": r["new_text"]}
                                  for r in in_scope_corr],
    "term_rules_applied": [{"原词日文": r["jp"], "旧写法": r["old"], "新写法": r["new"],
                            "表旧写法出现次数": r["旧写法出现次数"]} for r in TERM_RULES],
    "term_table_notes": TERM_NOTE,
    "term_hits_occurrences": sum(s["stats"]["name_replace_count"] for s in scene_objs),
    "term_hits_slots": {("%s|%s" % k): v for k, v in sorted(term_slots.items())},
    "term_hits_slots_total": sum(term_slots.values()),
    "term_reconcile": term_recon,
    "speaker_repair_fail": REPAIR_FAIL,
    "name_replace_detail": [{"script": s["script"], "seq": l["seq"], "lineno": l["lineno"],
                             "原词日文": h["原词日文"], "旧写法": h["旧写法"], "新写法": h["新写法"],
                             "before": h["before"], "after": h["after"],
                             "context_flag": h["context_flag"]}
                            for s in scene_objs for l in s["lines"] for h in l["name_replaced"]],
    "speaker_repairs": REPAIRS,
    "speaker_repair_count": len(REPAIRS),
    "speaker_translate_table": "修正表_说话人译名.tsv",
    "speaker_translate_rows": SPK_TR_ROWS,
    "speaker_translate_applied": sum(s["_spk_tr_fix"] for s in scene_objs),
    "speaker_translate_not_applied": [{"script": n, "seq": k, "speaker_jp": v[0]}
                                      for (n, k), v in sorted(SPK_TR.items())
                                      if (n, k) not in SPK_TR_APPLIED],
    "speaker_cn_missing_after": sorted(set(
        l["speaker_jp"] for s in scene_objs for l in s["lines"]
        if l["speaker_jp"] and not l["speaker"])),
    "speaker_split_table": "修正表_0x5C.tsv",
    "speaker_split_table_applied": len(SPLIT_APPLIED),
    "speaker_split_table_gated": [{"script": n, "seq": k, "new_text": t} for n, k, t in SPLIT_GATED],
    "speaker_split_table_conflict": SPLIT_CONFLICT,
    "speaker_map_missing": sorted(set(SPEAKER_MISS)),
    "speaker_map_ambiguous": SPEAKER_AMB,
    "speaker_cn_total": len(SPEAKER_CN),
    "assets_total": a_total, "assets_hit": a_hit, "assets_missing": a_total - a_hit,
    "asset_missing_list": [{"script": s["script"], "ref": r} for s in scene_objs
                           for r in s["assets_missing"]],
    "voice_refs": v_ref, "voice_hit": v_hit, "voice_missing": v_ref - v_hit,
    "voice_missing_list": sorted({l["voice"] for s in scene_objs for l in s["lines"]
                                  if l["voice"] and not l["audio"]}),
    "empty_slots": sum(s["stats"]["empty_slots"] for s in scene_objs),
    "d14_exceptions": 0,
    "choices": {"scripts": choice_scripts, "script_count": len(choice_scripts),
                "options_total": sum(len(s["choices"]) for s in scene_objs),
                "sel1_slots": sel1, "sel2_slots": sel2,
                "option_text_cn_missing": [{"script": s["script"], "text_jp": c["text_jp"]}
                                           for s in scene_objs for c in s["choices"]
                                           if not c["text_cn"]]},
    "scene_choices_detail": [{"script": s["script"], "text_jp": c["text_jp"],
                              "text_cn": c["text_cn"], "cn_origin": c["cn_origin"],
                              "target": c["target"], "pairing_verified": c["pairing_verified"],
                              "next": s["next"], "evidence": c["evidence"]}
                             for s in scene_objs for c in s["choices"]],
    "titles": {"scenes_with_title": sum(1 for s in scene_objs if s["title_jp"]),
               "scenes_without_title": [s["script"] for s in scene_objs if not s["title_jp"]],
               "variants_total": sum(len(s["title_variants"]) for s in scene_objs)},
    "next_zero": [s["script"] for s in scene_objs if not s["next"]],
    "next_cross_module": sorted({t for s in scene_objs for t in s["next"] if t not in modset}),
    "scenes_with_date": [{"script": s["script"], "game_date": s["game_date"],
                          "game_dates": s["game_dates"]} for s in scene_objs if s["game_date"]],
    "phase_title_check": title_check,
    "scene_ids_unique": len({s["scene_id"] for s in scene_objs}) == len(scene_objs),
    "per_scene": [{
        "script": s["script"], "phase": s["phase"], "route": s["route"],
        "title_jp": s["title_jp"], "title_cn": s["title_cn"],
        "line_count": s["line_count"], "voice_count": s["voice_count"],
        "game_date": s["game_date"], "next": s["next"], "next_kind": s["next_kind"],
        "choices": len(s["choices"]), "cast": s["cast"],
        "assets_total": len(s["assets"]), "assets_hit": sum(1 for a in s["assets"] if a["hit"]),
        "assets_missing": s["assets_missing"],
        "corrections_hit": s["stats"]["corrections_hit"],
        "name_replace_count": s["stats"]["name_replace_count"],
        "empty_slots": s["stats"]["empty_slots"],
        "speaker_split_repairs": s["_speaker_split_repairs"],
        "lines_by_origin": s["stats"]["lines_by_origin"],
    } for s in scene_objs],
}
report["asset_hit_rate"] = round(100.0 * a_hit / a_total, 4) if a_total else 0.0
report["voice_hit_rate"] = round(100.0 * v_hit / v_ref, 4) if v_ref else 0.0

os.makedirs(STG, exist_ok=True)
json.dump(report, open(os.path.join(STG, "_build_stats_ot.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 写 scene_ot.jsonl
w("[9/9] 写出 scene_ot.jsonl ...")
for s in scene_objs:
    s.pop("_speaker_split_repairs", None)
    s.pop("_spk_tr_fix", None)
_assert_in_checkout(OUT, "剧本产物目录")
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "scene_ot.jsonl")
_assert_in_checkout(outpath, "scene_ot.jsonl")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    for s in scene_objs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
with open(outpath, encoding="utf-8") as f:
    n_ok = sum(1 for ln in f if json.loads(ln))
w("      -> %s （%d 行，逐行 json.loads OK）" % (outpath, n_ok))

# ---------------------------------------------------------------- 摘要
w("")
w("================ 摘要（W6b · 本篇主线） ================")
w("场景数            : %d  %s" % (report["scenes"], report["scripts_by_group"]))
w("行数              : %d  (源基线 %d，守恒=%s；逐场景守恒=%s)"
  % (tot_lines, base_lines, report["lines_balanced"], per_scene_ok))
w("cn_origin 分布    : %s" % report["orig_dist"])
w("align_method 分布 : %s" % report["align_method_dist"])
w("修正表            : 合计 %d ｜ 模块范围内 %d ｜ 命中 %d ｜ 门控排除 %d ｜ 未命中 %d ｜ 范围外 %d"
  % (report["corrections_total"], report["corrections_in_scope"], report["corrections_hit"],
     report["corrections_gated"], len(report["corrections_missing_in_scope"]),
     report["corrections_out_of_scope"]))
w("term_unify 幂等 no-op: %d 条（构建期应为 0；非 0 即目标槽已是他态，须查 %s）"
  % (len(TERM_NOOP), TERM_NOOP[:3]))
w("译名替换          : 处数 %d ｜ 槽数 %d（表内 ot 计数合计 806）"
  % (report["term_hits_occurrences"], report["term_hits_slots_total"]))
w("  spec_hits       : %s" % report["term_hits_slots"])
w("  逐规则对账      :")
for x in term_recon:
    w("      %-14s %-12s 表内=%-5s 本模块=%-5d 全源397=%-5d %s"
      % (x["原词日文"], x["旧写法"], x["表内计数"], x["本模块槽数"], x["全源397槽数"],
         "" if x["表内计数"] == x["全源397槽数"] else "← 与全源口径不一致"))
w("素材命中          : %d/%d (%.2f%%)  缺失 %d" % (a_hit, a_total, report["asset_hit_rate"],
                                                   report["assets_missing"]))
w("语音命中          : %d/%d (%.2f%%)  缺失 %d" % (v_hit, v_ref, report["voice_hit_rate"],
                                                   report["voice_missing"]))
w("speaker 拆分修复  : %d 行 ｜ 名字框映射缺失标签 %d ｜ 多写形 %d"
  % (report["speaker_repair_count"], len(report["speaker_map_missing"]),
     len(report["speaker_map_ambiguous"])))
w("speaker 译名补充  : 表 %d 条 ｜ 生效 %d ｜ 未生效 %d ｜ 仍缺中文标签 %d"
  % (report["speaker_translate_rows"], report["speaker_translate_applied"],
     len(report["speaker_translate_not_applied"]), len(report["speaker_cn_missing_after"])))
w("选择支            : %d 脚本 / %d 选项（sel=1 %d、sel=2 %d）；缺译文 %d"
  % (report["choices"]["script_count"], report["choices"]["options_total"],
     sel1, sel2, len(report["choices"]["option_text_cn_missing"])))
w("标题              : %d 场景有标题 / %d 无标题 ｜ 标题槽 %d"
  % (report["titles"]["scenes_with_title"], len(report["titles"]["scenes_without_title"]),
     report["titles"]["variants_total"]))
w("phase 分布        : %s" % report["phase_dist"])
w("next_kind 分布    : %s" % report["next_kind_dist"])
w("零目标（终点）    : %s" % report["next_zero"])
w("跨模块 next       : %s" % report["next_cross_module"])
w("空槽              : %d" % report["empty_slots"])
w("scene_id 唯一     : %s" % report["scene_ids_unique"])
w("phase/标题交叉核对: %d 处待看" % len(title_check))
for x in title_check:
    w("      %s" % x)