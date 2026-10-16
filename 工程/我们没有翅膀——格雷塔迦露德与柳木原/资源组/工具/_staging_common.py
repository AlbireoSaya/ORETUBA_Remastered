# -*- coding: utf-8 -*-
r"""
`_staging_common.py` · 逐行演出表（`演出_<源>.tsv`）的**契约唯一实现**（ISSUE-20261001-14）

定位
    六源生成器（`build_staging_sob0.py` / `build_staging_otv.py` / `build_staging_np.py` /
    `build_staging_tob.py`）**必须**共用本模块的常量、`Ledger`、`SeqMap`、`write_tsv`，
    禁止各源各写一份（否则六张表会各自漂移）。独立校验器 `verify_staging.py` **刻意不共用
    本模块的判定实现**（只共用产物路径常量），以免「自己验自己」。

消费契约（提出方＝编程组，`编程组\移交资源组_逐行演出数据任务书.md` §三）
    产物：`资源组\演出\演出_<源>.tsv`，UTF-8 无 BOM、TAB 分隔、无引号、首行表头，9 列固定顺序。
    列：`scene_id seq op target arg1 arg2 arg3 evidence confidence`

`seq` 语义（**锚定＝「在该行显示之前生效」**）
    * 与 `资源组\剧本\scene_<源>.jsonl` 的 `lines[].seq` 同坐标系（1-based）。
    * 某 op 落在源槽/源位置 `p`：其 `seq` = **紧随 `p` 之后的第一个文本行的行号**；
      若 `p` 之后本场再无文本行 ⇒ 取**末行行号**（`evidence` 注 `after_last_line`）；
      若 `p` 在首行之前 ⇒ `seq=1`（`evidence` 注 `before_first_line`）。
    * `skip` 行：`seq=0`（唯一允许的 0）。
    * 同一 `seq` 可有多行（多个 op 在该行前依次触发），按**文件物理先后**为触发序。

`target` 口径
    一律用 `krkr素材库\资源总账.json` 的 `out_relpath`（`<源>/<kind>/<源>_<名>.<ext>`），
    **不得用 basename、不得跨源解析**。令牌→资产的唯一映射键 = `splitext(orig_name)[0].upper()`
    按 `kind` 分建（见 `Ledger`）。`chr_*` 查 `chr`、`bg` 查 `pic`、`se` 查 `se`、
    `bgm` 查 `bgm`、`movie` 查 `movie`。

`evidence` 口径
    写「哪个脚本 + 哪个位置」，**不写注释行号**（本工程实测注释行号引用 6/6 全飘）。
    统一形如 `script=<脚本名>; <定位串>`；各源定位串见各生成器文档头。

丢弃类别（不算 op，但**必须计数**并写入 `_index.json`）
    `empty`（空串槽）/ `numeric`（纯数字与带符号数字，参数）/ `separator`（`_` `$` `[` `]` `^`
    及其复写、`$ $` 之类分隔串）/ `scskip`（`ScSkip`/`SsSkip` 简介跳过标记）/ `voice`
    （`VOICE\*` 语音，已由 `lines[].audio` 承载）。
"""
from __future__ import annotations

import bisect
import collections
import io
import json
import os
import re
import sys

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__

# ================================================================ 契约常量
HEADER = ["scene_id", "seq", "op", "target", "arg1", "arg2", "arg3",
          "evidence", "confidence"]
NCOL = 9

OPS = ("chr_add", "chr_remove", "chr_move", "chr_expr",
       "bg", "se", "bgm", "movie", "wait", "effect", "other", "skip")
CONFIDENCES = ("exact", "inferred", "unknown")
DROP_KINDS = ("empty", "numeric", "separator", "scskip", "voice")

SOURCES = ("ot", "ota", "otp", "otr", "otv", "np")

# ================================================================ 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖；`工程/**/语料/` 等中间产物被 gitignore，只在主工作树存在）。
# 写 = 本脚本所在 checkout（由 `__file__` 推导）。
HERE = os.path.dirname(os.path.abspath(__file__))                 # <checkout>\...\资源组\工具
RES_LOCAL = os.path.dirname(HERE)                                 # <checkout>\...\资源组
PRJ_LOCAL = os.path.dirname(RES_LOCAL)                            # <checkout>\...\<作品>
WS_LOCAL = os.path.dirname(os.path.dirname(PRJ_LOCAL))            # <checkout> 根（PRJ_LOCAL = <checkout>\工程\<作品>）
OUT_DIR = os.path.join(RES_LOCAL, "演出")                          # 产物：写本 checkout

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
RES = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "资源组")
LEDGER = os.path.join(RES, "krkr素材库", "资源总账.json")
ART_INDEX = os.path.join(RES, "美术", "立绘差分索引.tsv")
SCENE_DIR = RES                                         # 源剧本由生成器自行定位；本项保留兼容

# 各源「字节码序流 / 原始脚本」的根（由各生成器按需引用）
OT_RAW = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "语料", "原文")
OTP_PROJ = os.path.join(DATA_ROOT, "工程", "我们没有翅膀 前奏诗")
PSV_SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀PSV", "素材", "美咲线", "script")
OTR_TOB = os.path.join(DATA_ROOT, "工程", "我们没有翅膀R", "亜衣线资源", "剧本")
OTA_TOB = os.path.join(DATA_ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")
NP_ARC = os.path.join(DATA_ROOT, "工程", "涅布＊普拉斯", "解包", "data01100.arc")


def assert_in_checkout(path, what="产物"):
    """边界断言：产物必须落在本 checkout 内（防止误写主工作区）。"""
    p = os.path.abspath(path)
    c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))
    return p


# 脚本内资源路径的**唯一前缀→kind 映射**（六源共用；`VOICE` 归 `voice`，由调用方决定是否丢弃）
PREFIX_KIND = {"PIC": "pic", "SE": "se", "SYS": "sys", "BGM": "bgm",
               "VOICE": "voice", "CHR": "chr", "MOVIE": "movie"}


def path_ref(body):
    """脚本路径串 → `(kind, TOKEN)`；非「已知前缀 + 路径」形态返回 `(None, None)`。

    `PIC\\BG01.ELG` → `('pic', 'BG01')`；`CHR\\AI_03A.ELG` → `('chr', 'AI_03A')`。
    反斜杠与正斜杠等价；大小写不敏感。
    """
    b = (body or "").strip()
    if not b:
        return None, None
    head = re.split(r"[\\/]", b, 1)[0].upper()
    kind = PREFIX_KIND.get(head)
    if kind is None or not re.search(r"[\\/]", b):
        return None, None
    return kind, os.path.splitext(os.path.basename(b.replace("/", os.sep)))[0].upper()


# ================================================================ 资源总账
# 令牌形态级联（**顺序敏感**，先专后泛）；每组**最后一个捕获组恒为差分后缀**
_FAM_RES = (
    re.compile(r"^([A-Za-z]+)_([A-Za-z])(\d+)([A-Za-z]?)$"),         # 形A `asu_a01l`（np）
    re.compile(r"^([A-Za-z]+(?:_[A-Za-z]+)?)_(\d+)([A-Za-z]?)$"),    # 形B `ai_03f`／`f_mis01l`
    re.compile(r"^([A-Za-z]+?)(\d+)([A-Za-z]?)$"),                   # 形C `kaz01a`／`lr201a`
    re.compile(r"^([A-Za-z]+)$"),                                    # 无数字 `cin_red`
)


def family_of(token):
    """裸差分令牌 → 立绘族代号（**启发式回退**；权威口径见 `ArtFamilies`）。

    级联顺序（敏感）：形A `ASU_A01L`（np 的 `<族>_<段><NN><后缀>`，**段字母不进族名**）／
    形B `AI_03F`／形C `KAZ01A`／无数字且无下划线的单词（如 `red`）。
    ⚠️ **多段下划线且无数字的名字（`cin_red`／`CIN_BLK2`／`F_MIS01L`）本函数返回 `None`**
    —— 这类一律走 `ArtFamilies.family(out_relpath)`（`立绘差分索引.tsv` 是 vetted 的权威表，
    能给到 `cin` / `f_mis`）；纯靠本函数的调用方须自己兜底（各生成器均已如此）。
    """
    t = (token or "").strip()
    for r in _FAM_RES:
        m = r.match(t)
        if m:
            return m.group(1).lower()
    return None


def suffix_of(token):
    """裸差分令牌 → 差分后缀（小写；无后缀返回 ''）。"""
    t = (token or "").strip()
    for r in _FAM_RES[:3]:
        m = r.match(t)
        if m:
            return (m.groups()[-1] or "").lower()
    return ""


class ArtFamilies:
    """**权威的**「立绘件 → 族」映射，来自 `资源组\\美术\\立绘差分索引.tsv`。

    键 = `out_relpath`（与 `Ledger` 的 target 同一命名空间），值 = `family` 列。
    之所以不按令牌正则推：`立绘差分索引.tsv` 是 vetted 的权威表，能正确处理
    `F_MIS01L`（族 `f_mis`）与 `CIN_BLK2`（族 `cin`）这类正则覆盖不到的名字。
    """

    def __init__(self, path=None):
        self.m = {}
        with io.open(path or ART_INDEX, encoding="utf-8") as f:
            head = f.readline().rstrip("\r\n").split("\t")
            ir, ifa = head.index("out_relpath"), head.index("family")
            for ln in f:
                p = ln.rstrip("\r\n").split("\t")
                if len(p) > max(ir, ifa) and p[ir]:
                    self.m[p[ir]] = p[ifa].lower()

    @classmethod
    def load(cls, path=None):
        return cls(path)

    def family(self, out_relpath):
        return self.m.get(out_relpath)

    def __len__(self):
        return len(self.m)



class Ledger:
    """`krkr素材库\\资源总账.json` 的**契约视图**：`(kind, source) -> {TOKEN: out_relpath}`。

    TOKEN = `splitext(orig_name)[0].upper()`，例如 ot 的 `ai_03f.elg` → `AI_03F`。
    **必须按源分域**：`AI_01` 在 ot/otr/ota 三源各有各的件（`ot/chr/ot_ai_01.png` 等），
    跨源取图是 `交接说明.md` C3/C4 明令禁止的。
    同 `(kind, source)` 同 TOKEN 多条时优先取 `dup_of is None` 者（去重主件），冲突计入
    `collisions`（生成器应把它写进 `_index.json`，不得静默）。
    """

    def __init__(self, entries):
        self._m = collections.defaultdict(dict)
        self._prefer = {}
        self.collisions = []
        for e in entries:
            kind = e.get("kind")
            src = e.get("source")
            on = e.get("orig_name") or ""
            rel = e.get("out_relpath")
            if not kind or not src or not on or not rel:
                continue
            tok = os.path.splitext(os.path.basename(on))[0].upper()
            key = (kind, src)
            cur = self._m[key].get(tok)
            if cur is None:
                self._m[key][tok] = rel
                self._prefer[(kind, src, tok)] = (e.get("dup_of") is None)
                continue
            if cur != rel:
                keep_new = (e.get("dup_of") is None) and not self._prefer[(kind, src, tok)]
                self.collisions.append((src, kind, tok, cur, rel,
                                        "取后者" if keep_new else "取前者"))
                if keep_new:
                    self._m[key][tok] = rel
                    self._prefer[(kind, src, tok)] = True

    @classmethod
    def load(cls, path=None):
        with io.open(path or LEDGER, encoding="utf-8") as f:
            d = json.load(f)
        return cls(d["entries"])

    def target(self, kind, token, source):
        """令牌 → 该源该 kind 的 `out_relpath`；未命中返回 None（调用方 fail loud 或记 skip）。"""
        return self._m.get((kind, source), {}).get((token or "").upper())

    def tokens(self, kind, source):
        return set(self._m.get((kind, source), {}))

    def keys(self):
        return sorted(self._m)


def load_known_families(path=None):
    """立绘族代号全集（来自 `立绘差分索引.tsv` 的 `family` 列，含非角色的 `cin` 等）。

    ⚠️ **本集合保留哨兵值 `UNPARSED`**（索引里 3 条 `cin_red`）——它是 `build_staging_tob.py`
    的「令牌是否算立绘」允许集，**去掉它会改变产物**（`CIN_RED` 行消失；本批实测：ota 会少 3 行）。
    校验器 `verify_staging.load_families` 则**滤掉**哨兵（那里是闸门，从严更对）。
    **两处口径的分歧是刻意的、已知的**：是否把 `CIN_RED`（红幕遮罩，`cin` 族的叠加层）记为
    `chr_add` 属**待裁决的语义问题**（见 `工程记录` 的未决项），**不得在本模块单方面改掉**。
    """
    fams = set()
    with io.open(path or ART_INDEX, encoding="utf-8") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        i = head.index("family")
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) > i and p[i]:
                fams.add(p[i].lower())
    return fams


# ================================================================ seq 锚定
class SeqMap:
    """把「原始位置下标」映射到 `lines[].seq`。

    锚定语义（契约 §3.5.3）：op 之后**第一个**文本行的行号；其后无文本行 ⇒ 末行行号。
    构造参数 `text_slots` = 有序 `[(raw_index, line_seq), ...]`（`raw_index` 单调递增）。
    """

    def __init__(self, text_slots):
        self.idx = [int(a) for a, _ in text_slots]
        self.seqs = [int(b) for _, b in text_slots]
        if any(self.idx[i] >= self.idx[i + 1] for i in range(len(self.idx) - 1)):
            raise SystemExit("!! SeqMap: raw_index 非严格递增")
        if not self.seqs:
            raise SystemExit("!! SeqMap: 场景无文本行")

    def seq_for(self, raw_index):
        """→ (seq, tag)；tag ∈ {None, 'before_first_line', 'after_last_line'}。"""
        i = bisect.bisect_right(self.idx, int(raw_index))
        if i >= len(self.seqs):
            return self.seqs[-1], "after_last_line"
        return self.seqs[i], ("before_first_line" if i == 0 else None)


# ================================================================ 行构造与落盘
def _clean(v):
    """字段清洗：TAB / CR / LF 一律换成空格（TAB 分隔 + 无引号 ⇒ 字段内不得含分隔符）。"""
    if v is None:
        return ""
    s = str(v)
    return s.replace("\t", " ").replace("\r", " ").replace("\n", " ")


def row(scene_id, seq, op, target="", arg1="", arg2="", arg3="",
        evidence="", confidence="unknown"):
    """构造一条 9 列记录（**唯一构造入口**，内置枚举与列数闸门）。"""
    if op not in OPS:
        raise SystemExit("!! op 越出闭集：%r" % (op,))
    if confidence not in CONFIDENCES:
        raise SystemExit("!! confidence 越出闭集：%r" % (confidence,))
    if not evidence.strip():
        raise SystemExit("!! evidence 不得为空（scene=%s op=%s）" % (scene_id, op))
    if op != "skip" and "script=" not in evidence:
        # 防「列错位」类缺陷：非 skip 行的 evidence 必须写明来源（生成器一律以 `script=<名>; …` 起头）。
        # 实测该闸门能拦住「位置参数少写一个空串 ⇒ evidence 被挤成常量」这种错位（本批曾发生）。
        raise SystemExit("!! 非 skip 行的 evidence 须含 `script=`（scene=%s op=%s evidence=%r）"
                         % (scene_id, op, evidence[:60]))
    if op == "skip":
        if int(seq) != 0:
            raise SystemExit("!! skip 行 seq 必须为 0（scene=%s）" % (scene_id,))
    elif int(seq) < 1:
        raise SystemExit("!! 非 skip 行 seq 必须 >= 1（scene=%s op=%s seq=%s）" % (scene_id, op, seq))
    return {"scene_id": _clean(scene_id), "seq": int(seq), "op": op,
            "target": _clean(target), "arg1": _clean(arg1), "arg2": _clean(arg2),
            "arg3": _clean(arg3), "evidence": _clean(evidence), "confidence": confidence}


def skip_row(scene_id, script, reason):
    return row(scene_id, 0, "skip", evidence="script=%s; %s" % (script, reason),
               arg1=reason, confidence="unknown")


def assert_scene_coverage(rows, scene_ids, src):
    """闸门④（生成侧）：每场景要么 ≥1 条非 skip 行，要么恰好 1 条 skip 行。"""
    by = collections.defaultdict(lambda: [0, 0])   # scene -> [非skip, skip]
    for r in rows:
        by[r["scene_id"]][0 if r["op"] != "skip" else 1] += 1
    problems = []
    for s in scene_ids:
        nz, sk = by.get(s, [0, 0])
        if nz == 0 and sk != 1:
            problems.append((s, "无非 skip 行且 skip 行 %d 条（须恰 1）" % sk))
        if nz > 0 and sk > 0:
            problems.append((s, "既有非 skip %d 条又有 skip %d 条" % (nz, sk)))
    extra = sorted(set(by) - set(scene_ids))
    if extra:
        problems.append(("<表外场景>", str(extra[:5])))
    if problems:
        raise SystemExit("!! [%s] 场景覆盖闸门失败：%s" % (src, problems[:8]))
    return True


def write_tsv(path, rows):
    """落盘：UTF-8 无 BOM、TAB、无引号、首行表头、LF 行尾（同族交付件口径）。"""
    assert_in_checkout(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for r in rows:
        if len(r) != NCOL or list(r) != HEADER:
            raise SystemExit("!! 记录列不符：%r" % (sorted(r),))
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(HEADER) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in HEADER) + "\n")
    return len(rows)


def tsv_path(src):
    return os.path.join(OUT_DIR, "演出_%s.tsv" % src)


# ================================================================ 幂等自检（行尾规范化）
def read_artifact_text(path):
    """读产物文本并把行尾**规范化成 LF**（一切幂等自检都必须走这里）。

    `core.autocrlf=true` 的检出盘面是 **CRLF**、而仓库 blob 是 **LF**（见 `交接说明.md` C12）——
    裸字节/裸文本比较会让**同一提交在 LF 检出通过、在 CRLF 检出必失败**。本批就是这么栽的：
    合并后从主工作树跑 `--check` 时，四个生成器与台账生成器全部 exit 1。
    """
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def read_artifact_bytes(path):
    """读产物字节并把行尾规范化成 LF（同 `read_artifact_text`，供按字节比较的生成器用）。"""
    with open(path, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")
