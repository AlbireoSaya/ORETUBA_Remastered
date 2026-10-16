# -*- coding: utf-8 -*-
r"""
`build_staging_tob.py` —— **otr（R 版亚衣线）/ ota（After Story）逐行演出表生成器**
（ISSUE-20261001-14 ｜ 提出方＝编程组，见 `编程组\移交资源组_逐行演出数据任务书.md` §三）

一句话
    从 Lucifen **TOB0** 剧情脚本的**记录区**里，把「第几行出现什么演出（立绘/背景/音效）」
    解出来，按契约落 `资源组\演出\演出_otr.tsv` 与 `演出_ota.tsv`，用 `scene_id` + `seq`
    与既有 `资源组\剧本\scene_<源>.jsonl` 的 `lines[].seq` 严格对齐。

复跑命令（读写分离：读 `GRETA_DATA_ROOT`（默认 `E:\ZCode Workspace\Galgame`），写本 checkout）
    cd "E:\ZCode Workspace\Galgame"
    python -X utf8 "工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\工具\build_staging_tob.py"
    # 幂等自检（闸门④；**不写盘**，只把本轮重算的字节与磁盘产物逐字节比对）：
    python -X utf8 "…\build_staging_tob.py" --check
    # 预期末段：`[otr] 闸门④幂等 : PASS（逐字节相同，N 字节）` / 同式 `[ota]`

两个源共用同一个「记录区扫描器」，只用两个**源适配器**区分方言
    见 `SOURCES`：OTR（55 个 `.tob`）／OTA（172 个 `.tob`）。二者 TOB0 方言差异：
      * `otr`：立绘按 `CHR\*.ELG` **路径**引用；BGM/MOVIE 路径引用 **0 次**（实测）。
      * `ota`：立绘按**裸差分名**（无 `CHR\` 路径，如 `CIN051`/`KOB01B`/`LR201A`）引用；
        `CHR\` 路径引用 **0 次**、BGM/MOVIE 路径引用 **0 次**（实测）。
      * 共同点：PIC/SE 均按 `PIC\*.ELG` / `SE\*.OGG` 路径引用；记录头 op **不固定**。

记录区模型（**既有实现**，本模块按其逻辑自持一份，见 `工程\我们没有翅膀R\工具\tob_extract.py`
与 `工程\我们没有翅膀 After Story\工具\parse_after.py`）
    消息表 `T[k]` 给出第 k 条消息的「结束地址」；消息结构恒为
        <正文原始 SJIS 字节>  5b 20 0c 00 00 00 01 0b 00 00 00 01 01 00 <u32 k>   （尾部 18 字节）
    去掉尾部 18 字节即正文结束 `text_end`；正文起点 `text_start` 由「窗口内最早能恰好解析到
    `text_end` 的可显示 SJIS 起点」给出（`find_text_start`）。
    ⇒ **第 k 条消息的记录区 = `[prev, text_start_k)`**，`prev` = 上一条消息尾部结束地址
      （第 0 条从 `code_start` 起）。记录区里的声明串**都在正文 k 显示之前生效** ⇒ `seq` 锚定第 k 行。
    记录头形态：`5b 20 <op> 00 00 00 01 <u32 arg> <u8 typ> <载荷...>`；声明串形态
    `01 01 <u16 L> <bytes> 00`（**末字节必须 NUL**）。
    末条消息之后到文件尾的**尾区**（`[prev_last, EOF)`）同样扫描，归属记 `after_last_line`。

`seq` 口径（契约 §三.5「锚定＝在该行显示之前生效」，用 `_staging_common.SeqMap`）
    槽键＝**记录区边界**（第 k 条消息记录区的结束地址，= 第 k+1 条记录区起点 `prev_{k+1}` 的
    文件内偏移），槽值＝第 k 行 `lines[].seq`。`SeqMap.seq_for(op 的字节偏移 X)`：
    落在记录区 j（`prev_j ≤ X < prev_{j+1}`）⇒ `bisect_right` 落位 j ⇒ **seq_j**（第 j 行）。
    * **为何不用「行内正文字节偏移」作键**：`offset=None`（空槽 / 关联失败）的行会缺槽，
      会使其后记录区的 op 被错误前抛到首行（实测 `otr` 105 处）；而记录区边界对**每一条**消息
      （含空槽）都存在且单调递增，无此缺陷。
    * `ota` 另把**标题行**（`index=None`，其 `off` 参与流序）按 offset 插入槽中；
      `otr` 的标题被构建器追加到 `lines[]` 行尾、其 offset 不在流序内 ⇒ **不入槽**。
    * `p` 在首行之前（`i==0`）⇒ `seq=1`（`evidence` 注 `before_first_line`）；
      `p` 在末行之后（尾区）⇒ `seq=该场行数`（`evidence` 注 `after_last_line`）。
      （`SeqMap.seq_for` 对这两个边界返回 `seqs[0]` / `seqs[-1]` + tag；本模块按契约把
       tag 映射为 1 / 行数。）
    * `skip` 行：`seq=0`（唯一允许的 0）。
    * **0 文本行的场景**（实测 `ota_sr`）：无 `lines[].seq` 可锚定 ⇒ 该场只出 1 行 `skip`，
      其未能挂行的 op 数记入丢弃类 `no_line_anchor`（不静默）。

`target` 口径（契约 §3.2/§3.7）
    一律 `krkr素材库\资源总账.json` 的 `out_relpath`，**按源分域**（`Ledger.target(kind, tok, src)`）；
    **不得按 basename 跨源解析**。`CHR\AI_03.ELG`→`('chr','AI_03')`；`PIC\BG03B.ELG`→`('pic','BG03B')`；
    `SE\SE054.OGG`→`('se','SE054')`。**裸差分名**（无 `\` 的 token）按 `chr` 查，并用
    `family_of()`（族代号 ∈ `立绘差分索引.tsv`）交叉校验；命中 `chr` 且族有效 ⇒ 立绘。

`op` 口径（闭集，不得自造值）
    `bg`（PIC 路径）｜ `se`（SE 路径）｜ `chr_add`/`chr_expr`（立绘引用）｜ `other`（已解出的
    控制串助记符）｜ `skip`（该场无逐行演出数据）。**本两源实测无 BGM/MOVIE 引用 ⇒ 不产出该 op**
    （扫描若发现相反结论，见 `assert_no_bgm_movie` fail loud）。`wait`/`effect` 无时长/特效名证据 ⇒ 不产出。
    立绘 op 的判定（**文档化启发式**，非 opcode 语义推定）：token 带差分后缀 ⇒ `chr_expr`
    （`arg1`=后缀）；无后缀的基础立绘 ⇒ `chr_add`。后缀**取权威源 `美术\立绘差分索引.tsv` 的
    `suffix` 列**（按 `out_relpath` 挂；见 `IndexSuffix`），仅当该件不在索引时回退
    `_staging_common.suffix_of()`。理由：声明串直证的是「某个**具体差分件**在此刻被引用」，
    而闭集里 `chr_expr` 恰是「立绘表情/差分切换」；`suffix_of()` 的「形B」要求数字前有 `_`，
    认不出 `F_MIS04F`（族 `f_mis`）这类「两段族名直接接数字」的形态（会把 193 处真差分误判为
    `chr_add`）。**该依据逐行写进 `evidence` 尾注**（含后缀与出处），便于消费侧过滤或另裁。
    **不对 `chr_remove`/`chr_move` 作任何声称**（无逐行证据）。
    裸名立绘的族交叉校验以 **`_staging_common.ArtFamilies.family(out_relpath)`**（`美术\立绘差分索引.tsv`）
    **为权威**，`family_of()` 仅作启发式回退——前者能正确处理 `F_MIS01L`（族 `f_mis`）、
    `CIN_BLK2`（族 `cin`）这类令牌正则覆盖不到的名字。

`evidence` 口径（不写注释行号）
    `script=<脚本名>; TOB0 记录 @0x<hex> op=0x<op> 声明串 '<原始串>'（归属消息 index=<k>）`
    末可追加 `; before_first_line` / `; after_last_line`。`@0x<hex>` = 该声明串所属**记录头**偏移。

`confidence` 口径
    `exact`  = 声明串源侧直证且记录区归属由 T 表边界唯一确定（`k>=0`）；
    `inferred` = 尾区（`k=-1`，`after_last_line`）——op 不属于任何消息，seq 锚定末行属推定。

丢弃类（**不算 op，但全部计数**，见 `--stats`）
    `empty` 空串 ｜ `numeric` 纯数字/带符号数 ｜ `separator` 分隔串（`_` `$` `^` `[` `]` 及复写）
    ｜ `scskip`（`ScSkip`/`SsSkip`）｜ `voice`（`VOICE\*` 路径与裸语音 ID）｜ `speaker`（名字框/日文标签，
    非资源、非控制串）｜ `label`（跳转标签）｜ `ref_missing`（资源路径但总账未命中）｜ `ref_prefix_unknown`。

生成器内置闸门（都能真失败，见 `--stats` 输出）
    ① **逐场景集合守恒**：本场 `op=bg` 的 target 去重集合 ⊇ 本场 `assets[]` 中 `kind=pic` 的
       **可解析项**（`out_relpath` 非空）；`op=se` ⊇ `kind=se`；`op=chr_*` ⊇ `kind=chr`；`op=bgm` ⊇ `kind=bgm`。
    ② **场景覆盖**：`SC.assert_scene_coverage(rows, 全部 scene_id, '<源>')`（每场要么 ≥1 非 skip 行，
       要么恰 1 行 skip）。
    ③ **令牌可解析**：所有非 skip 行的 `target` 必须能在 `Ledger` 命中（fail loud 列出未命中项）。
    ④ **幂等（`--check`）**：`--check` 下**不写盘**，把本轮重算的字节（`tsv_bytes()`，与
       `write_tsv` 同式）与磁盘产物逐字节比对，不同即 `SystemExit`；相同打印 `闸门④幂等 : PASS`。
       非 `--check` 落盘后亦**自证**磁盘字节 == 重算字节（使两条序列化路径不可能漂移）。
    另：TOB0 尾部签名（`5a 20 0c … <u32 k>`）逐消息命中率**必须 100%**，否则 fail loud；
    BGM/MOVIE 路径引用必须为 0（`assert_no_bgm_movie`，否则 fail loud）。

已知边界（如实登记）
    * `otr` 的 `PIC\BG06B.ELG`（2 次）/ `PIC\BG07B.ELG`（1 次）在 `资源总账.json` 的 `otr/pic` **无对应件**
      ⇒ 不可为 `target`（闸门①只对可解析项成立；这 3 处与既有 `scene_otr.jsonl` 的 `assets[].hit=false`
      一致）。
    * 立绘的**出现/退场/移动**语义未逆向 ⇒ 只产出 `chr_add`/`chr_expr`，不产出 `chr_remove`/`chr_move`。
    * 转场方式/时长（`bg` 的 arg1/arg2）、音效播放方式（`se` 的 arg1）无证据 ⇒ 留空。
    * `ota` 裸名立绘判定：`Ledger.target('chr',…)` 命中 + 族经 **`ArtFamilies.family(out_relpath)`**
      （权威；回退 `family_of()`）判得且 ∈ 已知族 + **不是** `voice`（两源 `chr`/`voice` 令牌集实测
      **零交集**）⇒ 立绘；命中 `voice` ⇒ 语音（丢弃）；族不可判 ⇒ 落 `other` 并计 `chr_family_underived`。
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import struct
import sys

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _staging_common as SC          # noqa: E402  契约唯一实现（Ledger/SeqMap/row/skip_row/write_tsv/…）

# ================================================================ TOB0 记录区扫描器（共用）
# 模型来源：`工程\我们没有翅膀R\工具\tob_extract.py`（记录头/尾部签名/正文起点）
#           `工程\我们没有翅膀 After Story\工具\parse_after.py`（记录头实测 100% 命中）
REC_HDR = b"\x5b\x20"
TAIL_PREFIX = b"\x5b\x20\x0c\x00\x00\x00\x01\x0b\x00\x00\x00\x01\x01\x00"
DECL_RE = re.compile(rb"\x01\x01(..)")
SJIS_LEAD = set(range(0x81, 0xA0)) | set(range(0xE0, 0xFD))

NUMERIC_RE = re.compile(r"[+-]?\d+(?:\.\d+)?$")
SEPARATOR_RE = re.compile(r"[_\s$^\[\]]+$")
LABEL_RE = re.compile(r"(?:S03C|[0-9]{2})_[0-9A-Za-z]+$")
SCSKIP = {"SCSKIP", "SSSKIP"}


class TobFormatError(Exception):
    pass


def _decode(raw, enc="cp932"):
    try:
        return raw.decode(enc)
    except Exception:                                   # noqa: BLE001
        return None


def valid_sjis_plain(b):
    """宽松 SJIS 校验（允许控制字符；供串池 / 正文起点扫描）。"""
    i, n = 0, len(b)
    while i < n:
        c = b[i]
        if c <= 0x7F:
            i += 1
        elif 0xA1 <= c <= 0xDF:
            i += 1
        elif c in SJIS_LEAD:
            if i + 1 >= n:
                return False
            t = b[i + 1]
            if not (0x40 <= t <= 0x7E or 0x80 <= t <= 0xFC):
                return False
            i += 2
        else:
            return False
    return True


def _forward_parse_end(d, start, limit):
    i, n = start, min(limit, len(d))
    while i < n:
        c = d[i]
        if 0x20 <= c <= 0x7E:
            i += 1
        elif 0xA1 <= c <= 0xDF:
            i += 1
        elif c in SJIS_LEAD:
            if i + 1 >= n:
                return i
            t = d[i + 1]
            if not (0x40 <= t <= 0x7E or 0x80 <= t <= 0xFC):
                return i
            i += 2
        else:
            return i
    return i


def _plausible_text(raw):
    if not raw:
        return False
    if any(b >= 0x80 for b in raw):
        return True
    return len(raw) >= 6


def find_text_start(d, lo, text_end):
    """正文起点：窗口内「最早能恰好解析到 text_end 的可显示 SJIS 起点」。"""
    for p in range(lo, text_end):
        if _forward_parse_end(d, p, text_end) == text_end:
            raw = d[p:text_end]
            if _plausible_text(raw):
                return p, raw
    return None, None


def parse_header(d):
    """TOB0 头部：labels / T（消息结束地址表）/ code_start。"""
    if d[:4] != b"TOB0":
        raise TobFormatError("magic 不是 TOB0")
    nlab = struct.unpack_from("<I", d, 8)[0]
    p = 0x0C
    for _ in range(nlab):
        if p >= len(d):
            raise TobFormatError("标签段越界")
        ln = d[p]
        if ln < 5 or p + 1 + ln > len(d):
            raise TobFormatError("标签长度非法")
        p += 1 + ln
    if p + 8 > len(d):
        raise TobFormatError("缺少映射段")
    A = struct.unpack_from("<I", d, p)[0]
    B = struct.unpack_from("<I", d, p + 4)[0]
    if A != 8 + 4 * B:
        raise TobFormatError("映射段自述大小不符: A=%d B=%d" % (A, B))
    T = list(struct.unpack_from("<%dI" % B, d, p + 8))
    return {"T": T, "B": B, "code_start": p + 8 + 4 * B}


def scan_regions(raw, strict=True):
    """→ (info, regions, tail_hit, tail_total)。

    regions = [(k, lo, hi), …]，`k=-1` 表示末条消息之后的**尾区** [prev_last, EOF)。
    `hi` = 正文起点（找不到时退化为 `text_end`）。尾部 18 字节签名逐消息校验。
    """
    info = parse_header(raw)
    T, cs = info["T"], info["code_start"]
    n = len(raw)
    regions = []
    prev = cs
    hit = total = 0
    for k, t in enumerate(T):
        p = t + cs
        total += 1
        if p + 2 <= n and raw[p:p + 2] == REC_HDR and p + 6 <= n and raw[p + 3:p + 6] == b"\x00\x00\x00":
            tail = raw[p - 18:p]
            if (len(tail) == 18 and tail[:14] == TAIL_PREFIX
                    and struct.unpack_from("<I", tail, 14)[0] == k):
                hit += 1
            elif strict:
                raise SystemExit("!! TOB0 尾部签名/序号不符 @0x%x (k=%d)" % (p, k))
        elif strict:
            raise SystemExit("!! TOB0 记录头特征缺失 @0x%x (k=%d)" % (p, k))
        text_end = p - 18
        ts, _body = find_text_start(raw, prev, text_end)
        regions.append((k, prev, ts if ts is not None else text_end))
        prev = p
    regions.append((-1, prev, n))
    return info, regions, hit, total


def decls_in(raw, lo, hi):
    """`01 01 <u16 L> <bytes 00>` 声明串 → [(字符串数据偏移, 串)]（按偏移升序）。"""
    out = []
    for m in DECL_RE.finditer(raw, lo, hi):
        L = struct.unpack("<H", m.group(1))[0]
        if L == 0 or L > 200:
            continue
        d = raw[m.start() + 4:m.start() + 4 + L]
        if len(d) != L or d[-1] != 0:
            continue
        s = _decode(d[:-1], "cp932")
        if s is None:
            continue
        out.append((m.start() + 4, s))
    return out


def rec_headers(raw, lo, hi):
    """`5b 20 <op> 00 00 00 01` 记录头 → [(头偏移, op)]（按偏移升序）。"""
    out = []
    for m in re.finditer(re.escape(REC_HDR), raw[lo:hi]):
        j = lo + m.start()
        if j + 12 <= len(raw) and raw[j + 3:j + 6] == b"\x00\x00\x00" and raw[j + 6] == 0x01:
            out.append((j, raw[j + 2]))
    return out


def nearest_header(headers, off):
    """声明串之前最近的记录头 → (头偏移, op)；无则 (None, None)。"""
    h = None
    for j, op in headers:
        if j <= off:
            h = (j, op)
        else:
            break
    return h if h is not None else (None, None)


# ================================================================ 源适配器
OTR_RES = os.path.join(SC.DATA_ROOT, "工程", "我们没有翅膀R", "亜衣线资源")
OTA_AS = os.path.join(SC.DATA_ROOT, "工程", "我们没有翅膀 After Story")
SCENE_DIR = os.path.join(SC.DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原",
                         "资源组", "剧本")


class OtrAdapter:
    """R 版亚衣线：55 个 `s03c_*.tob`；`index`/`offset` 取 `台词对照.json` 的 `lines[]`。"""
    src = "otr"
    include_titles_in_seqmap = False   # R 版标题被构建器追加到行尾，offset 不在流序内

    def __init__(self):
        self.cmp = json.load(io.open(os.path.join(OTR_RES, "剧本", "台词对照.json"),
                                     encoding="utf-8"))
        self.tob_dir = os.path.join(OTR_RES, "剧本")

    def scenes(self):
        for sc in self.cmp["scenes"]:
            fname = sc["file"]                                  # s03c_01a.tob
            script = fname[:-4]
            lines = [{"seq": i, "index": l["index"], "kind": l["kind"], "offset": l["offset"]}
                     for i, l in enumerate(sc["lines"], 1)]
            yield "otr_%s" % script, script, os.path.join(self.tob_dir, fname), lines


class OtaAdapter:
    """After Story：172 个 `.tob`；`index`/`offset` 取 `台词.json` 的 `messages[]`（已按 off 排序）。"""
    src = "ota"
    include_titles_in_seqmap = True    # After Story 标题按 off 参与流序

    def __init__(self):
        self.tj = json.load(io.open(os.path.join(OTA_AS, "语料", "台词.json"),
                                    encoding="utf-8"))
        self.tob_dir = os.path.join(OTA_AS, "语料", "原文")

    def scenes(self):
        for fname in sorted(self.tj):
            script = fname[:-4]
            lines = [{"seq": i, "index": m["index"], "kind": m["kind"], "offset": m["off"]}
                     for i, m in enumerate(self.tj[fname]["messages"], 1)]
            yield "ota_%s" % script, script, os.path.join(self.tob_dir, fname), lines


ADAPTERS = {"otr": OtrAdapter, "ota": OtaAdapter}


# ================================================================ 判定
def build_seqmap(adapter, lines, regions):
    """构造 `SeqMap`（**记录区边界键**，非行内字节偏移键）。

    槽键 = 第 k 条消息**记录区的结束地址**（= 第 k+1 条记录区起点 `prev_{k+1}`），
    槽值 = 第 k 行 `lines[].seq`。这样「落在记录区 k 的 op」经 `SeqMap.seq_for`
    恰好命中第 k 行的 seq（`prev_k <= X < prev_{k+1}` ⇒ `bisect_right` 落位 = k）。

    为什么不用「行内正文字节偏移」作键：`offset=None`（空槽 / 关联失败）的行会缺槽，
    使**其后**记录区的 op 被错误前抛到首行（实测 otr 105 处）。记录区边界对**每一条**
    消息（含空槽）都存在且单调，故无此缺陷。
    `ota` 另把标题行（`index=None`，按 `off` 参与流序）按其 offset 插入槽中；
    `otr` 标题被构建器追加到行尾、offset 不在流序内 ⇒ 不入槽（`include_titles_in_seqmap=False`）。
    """
    seq_by_index = {l["index"]: l["seq"] for l in lines if l["index"] is not None}
    B = len(regions) - 1                       # regions[-1] 为尾区，不是消息
    slots = []
    for k in range(B):
        if k in seq_by_index:
            slots.append((regions[k + 1][1], seq_by_index[k]))     # 记录区 k 的结束地址
    if adapter.include_titles_in_seqmap:
        for l in lines:
            if l["index"] is None and l["offset"] is not None:
                slots.append((l["offset"], l["seq"]))
    slots.sort()
    idxs = [a for a, _ in slots]
    if any(idxs[i] >= idxs[i + 1] for i in range(len(idxs) - 1)):
        raise SystemExit("!! SeqMap 槽键非严格递增（%s）: %s" % (adapter.src, idxs[:8]))
    return SC.SeqMap(slots), len(lines)


def chr_op_for(suffix):
    """立绘 op 的文档化启发式：带差分后缀 ⇒ chr_expr，无后缀（基础立绘）⇒ chr_add。"""
    return "chr_expr" if suffix else "chr_add"


def chr_evidence_suffix(suffix, suf_src, op):
    """立绘行的 `evidence` 尾注：逐行注明 add/expr 二分的依据（文档化启发式 + 后缀出处）。"""
    if op == "chr_expr":
        return ("; chr 后缀='%s'（出处 %s）⇒ chr_expr"
                "（文档化启发式：带差分后缀即差分/表情切换）" % (suffix, suf_src))
    return ("; 无差分后缀（出处 %s）⇒ chr_add"
            "（文档化启发式：基础立绘出现）" % suf_src)


class IndexSuffix:
    """`美术\\立绘差分索引.tsv` 的 `suffix` 列 → `{out_relpath: 差分后缀}`（**权威后缀**）。

    **为何不能只用 `_staging_common.suffix_of()`**：其令牌形态级联的「形B」
    （`^([A-Za-z]+(?:_[A-Za-z]+)?)_(\\d+)([A-Za-z]?)$`）要求数字前有 `_`（`ai_03f` 成立），
    但 `F_MIS04F` 这类「**两段族名直接接数字**」的形态没有该下划线 ⇒ 级联返回 `''`，
    会把 **193 处真差分误判为 `chr_add`**（实测）。索引的 `suffix` 列是 vetted 数据，
    直接给出 `f`（`F_MIS04F` → base `mis04` + suffix `f`）。
    `_staging_common` 目前只暴露 `ArtFamilies.family(out_relpath)`、**未暴露 suffix 访问器**
    ⇒ 此处按同一 `out_relpath` 命名空间本地读取（建议上游补 `ArtFamilies.suffix()`）。
    """

    def __init__(self, path=None):
        self.m = {}
        with io.open(path or SC.ART_INDEX, encoding="utf-8") as f:
            head = f.readline().rstrip("\r\n").split("\t")
            ir, isu = head.index("out_relpath"), head.index("suffix")
            for ln in f:
                p = ln.rstrip("\r\n").split("\t")
                if len(p) > max(ir, isu) and p[ir]:
                    self.m[p[ir]] = p[isu].lower()

    @classmethod
    def load(cls, path=None):
        return cls(path)

    def suffix(self, out_relpath, token):
        """→ (后缀, 出处)；索引无该件时回退 `_staging_common.suffix_of()`。"""
        if out_relpath in self.m:
            return self.m[out_relpath], "立绘差分索引.suffix"
        return SC.suffix_of(token), "suffix_of()"

    def __len__(self):
        return len(self.m)


def chr_family(token, relpath, af, fams):
    """裸差分令牌 → 立绘族代号；不可判返回 None（调用方落 `other` 并计数）。

    判定次序（**权威在前**）：
      ① `_staging_common.ArtFamilies.family(out_relpath)` —— 来自 `美术\\立绘差分索引.tsv` 的
         **权威族**，正确处理 `F_MIS01L`（族 `f_mis`）与 `CIN_BLK2`（族 `cin`）这类正则覆盖不到的
         名字（旧版 `family_of` 的令牌正则认不出，会误丢 217 处立绘）；
      ② `_staging_common.family_of(token)` —— 令牌形态级联（启发式回退）。
    族代号须 ∈ `load_known_families()` 的已知族集合，否则视为不可判。
    """
    fam = af.family(relpath) if relpath else None
    if fam is None:
        fam = SC.family_of(token)
    return fam if (fam and fam in fams) else None


def classify(s, led, fams, src, af, idxsuf):
    """声明串 → ('row', op, target, arg1, token, 后缀, 后缀出处) | ('drop', 丢弃类)。"""
    if not s:
        return ("drop", "empty")
    if "\\" in s or "/" in s:
        kind, tok = SC.path_ref(s)
        if kind is None:
            return ("drop", "ref_prefix_unknown")
        if kind == "voice":
            return ("drop", "voice")
        if kind == "sys":
            return ("drop", "sys")
        tgt = led.target(kind, tok, src)
        if tgt is None:
            return ("drop", "ref_missing")
        if kind == "pic":
            return ("row", "bg", tgt, "", tok, "", "")
        if kind == "se":
            return ("row", "se", tgt, "", tok, "", "")
        if kind == "chr":
            suf, ssrc = idxsuf.suffix(tgt, tok)
            return ("row", chr_op_for(suf), tgt, suf, tok, suf, ssrc)
        if kind == "bgm":
            return ("row", "bgm", tgt, "", tok, "", "")
        if kind == "movie":
            return ("row", "movie", tgt, "", tok, "", "")
        return ("drop", "ref_prefix_unknown")
    # ---- 裸令牌
    U = s.upper()
    relp = led.target("chr", U, src)
    if relp is not None:
        if chr_family(U, relp, af, fams) is None:
            return ("drop", "chr_family_underived")   # 总账命中但族不可判 → 不臆断
        suf, ssrc = idxsuf.suffix(relp, U)
        return ("row", chr_op_for(suf), relp, suf, U, suf, ssrc)
    if led.target("voice", U, src) is not None:
        return ("drop", "voice")
    if U in SCSKIP:
        return ("drop", "scskip")
    if any(ord(c) > 0x7F for c in s):
        return ("drop", "speaker")                 # 名字框 / 日文标签（非资源、非控制串）
    if LABEL_RE.match(s):
        return ("drop", "label")                   # 跳转标签
    if NUMERIC_RE.match(s):
        return ("drop", "numeric")
    if SEPARATOR_RE.match(s):
        return ("drop", "separator")
    return ("row", "other", "", s, s, "", "")      # 已解出的控制串助记符


def evidence(script, hoff, opb, raw_str, k, tag):
    ev = ("script=%s; TOB0 记录 @%s op=%s 声明串 '%s'（归属消息 index=%s）"
          % (script,
             ("0x%x" % hoff) if hoff is not None else "n/a",
             ("0x%02x" % opb) if opb is not None else "n/a",
             raw_str,
             str(k) if k >= 0 else "after_last"))
    if tag == "before_first_line":
        ev += "; before_first_line"
    elif tag == "after_last_line":
        ev += "; after_last_line"
    return ev


# ================================================================ 构建
def load_scene_assets(src):
    """`scene_<src>.jsonl` → {scene_id: {kind: set(可解析 out_relpath)}} 与未解析项。"""
    by = {}
    unresolved = collections.defaultdict(list)
    path = os.path.join(SCENE_DIR, "scene_%s.jsonl" % src)
    with io.open(path, encoding="utf-8") as f:
        for ln in f:
            o = json.loads(ln)
            d = collections.defaultdict(set)
            for a in o.get("assets", []):
                if a.get("out_relpath"):
                    d[a["kind"]].add(a["out_relpath"])
                else:
                    unresolved[o["scene_id"]].append((a["kind"], a.get("ref")))
            by[o["scene_id"]] = d
    return by, unresolved


KIND_OF_OP = {"bg": "pic", "se": "se", "bgm": "bgm", "movie": "movie"}
CONS_PAIRS = (("pic", "bg"), ("se", "se"), ("chr", "chr"), ("bgm", "bgm"), ("movie", "movie"))


def _group_of(op):
    return "chr" if op.startswith("chr_") else op


def assert_no_bgm_movie(src_root):
    """实测闸门：本两源**不得**出现 BGM/MOVIE 路径引用（任务书 §一 实测 otr=0/ota=0）。

    若扫描发现相反结论，fail loud（不许静默按「没有」处理）。
    """
    n_bgm = n_mov = 0
    for dirpath, _dirs, files in os.walk(src_root):
        for fn in files:
            if not fn.lower().endswith(".tob"):
                continue
            raw = open(os.path.join(dirpath, fn), "rb").read()
            n_bgm += raw.count(b"BGM" + b"\\")
            n_mov += raw.count(b"MOVIE" + b"\\")
    if n_bgm or n_mov:
        raise SystemExit("!! 与实测不符：BGM/MOVIE 路径引用 %d/%d（预期 0/0）" % (n_bgm, n_mov))
    return n_bgm, n_mov


def collect(src):
    """生成该源的 `rows`（**不落盘**）并跑闸门①②③；返回 `(rows, stats)`。

    落盘/幂等比对由 `main()` 负责（`--check` 下不写盘，只逐字节比对磁盘产物）。
    """
    adapter = ADAPTERS[src]()
    assert_no_bgm_movie(adapter.tob_dir)         # 实测闸门：本两源无 BGM/MOVIE（否则 fail loud）
    led = SC.Ledger.load()
    fams = SC.load_known_families()
    af = SC.ArtFamilies.load()                   # 权威「立绘件 → 族」（立绘差分索引.tsv）
    idxsuf = IndexSuffix.load()                  # 权威「立绘件 → 差分后缀」（同表 suffix 列）
    scene_assets, unresolved = load_scene_assets(src)

    relpaths = {}

    def relset(kind):
        """该源该 kind 的全部 out_relpath（闸门③用）。"""
        if kind not in relpaths:
            relpaths[kind] = set(
                t for t in (led.target(kind, tok, src) for tok in led.tokens(kind, src)) if t)
        return relpaths[kind]

    rows = []
    drops = collections.Counter()
    ops = collections.Counter()
    confs = collections.Counter()
    per_scene_targets = collections.defaultdict(lambda: collections.defaultdict(set))
    scene_ids = []
    tail_viol = []
    tail_hit = tail_tot = 0
    no_line = []

    for sid, script, tob_path, lines in adapter.scenes():
        scene_ids.append(sid)
        nlines = len(lines)
        raw = open(tob_path, "rb").read()
        _info, regions, hit, tot = scan_regions(raw)
        tail_hit += hit
        tail_tot += tot
        if hit != tot:
            tail_viol.append((script, hit, tot))

        if nlines == 0:
            # 无文本行 ⇒ 无 lines[].seq 可锚定（契约要求非 skip 行的 seq ∈ lines[].seq）
            nops = sum(1 for _k, lo, hi in regions
                       for _o, s in decls_in(raw, lo, hi)
                       if classify(s, led, fams, src, af, idxsuf)[0] == "row")
            drops["no_line_anchor"] += nops
            rows.append(SC.skip_row(
                sid, script,
                "该场景 0 条文本行（无 lines[].seq 可锚定）；%d 处演出声明串无法挂行" % nops))
            no_line.append((sid, nops))
            continue

        sm, nlines = build_seqmap(adapter, lines, regions)
        n_scene = 0
        for k, lo, hi in regions:
            hdrs = rec_headers(raw, lo, hi)
            for soff, s in decls_in(raw, lo, hi):
                res = classify(s, led, fams, src, af, idxsuf)
                if res[0] == "drop":
                    drops[res[1]] += 1
                    continue
                _r, op, target, arg1, token, suf, ssrc = res
                seq, tag = sm.seq_for(soff)
                if tag == "before_first_line":
                    seq = 1
                elif tag == "after_last_line":
                    seq = nlines
                conf = "inferred" if k == -1 else "exact"
                hoff, opb = nearest_header(hdrs, soff)
                ev = evidence(script, hoff, opb, s, k, tag)
                if op.startswith("chr_"):
                    ev += chr_evidence_suffix(suf, ssrc, op)
                rows.append(SC.row(sid, seq, op, target, arg1, "", "", ev, conf))
                ops[op] += 1
                confs[conf] += 1
                n_scene += 1
                per_scene_targets[sid][_group_of(op)].add(target)
        if n_scene == 0:
            rows.append(SC.skip_row(
                sid, script,
                "脚本无 PIC/SE/CHR/BGM/MOVIE 路径引用且无已解出的控制串 → 无逐行演出数据"))

    # ---------------- 闸门① 逐场景集合守恒（对「可解析项」out_relpath 非空）
    cons = []
    cov = collections.Counter()
    want_tot = collections.Counter()
    for sid in scene_ids:
        want = scene_assets.get(sid, {})
        have = per_scene_targets.get(sid, {})
        for kind, grp in CONS_PAIRS:
            for rel in want.get(kind, set()):
                want_tot[kind] += 1
                if rel in have.get(grp, set()):
                    cov[kind] += 1
            w = want.get(kind, set())
            if not w:
                continue
            miss = sorted(w - have.get(grp, set()))
            if miss:
                cons.append((sid, kind, grp, miss))

    # ---------------- 闸门② 场景覆盖
    SC.assert_scene_coverage(rows, scene_ids, src)

    # ---------------- 闸门③ 令牌可解析
    bad = []
    for r in rows:
        if r["op"] == "skip":
            continue
        grp = _group_of(r["op"])
        if grp == "other":
            continue
        kind = KIND_OF_OP.get(grp, "chr")
        if not r["target"] or r["target"] not in relset(kind):
            bad.append((r["scene_id"], r["seq"], r["op"], r["target"]))
    if bad:
        raise SystemExit("!! 闸门③ 令牌可解析失败（%d 条）: %s" % (len(bad), bad[:8]))

    # ---------------- TOB0 尾部签名（100% 命中为硬要求）
    for script, h, tot2 in tail_viol:
        raise SystemExit("!! TOB0 尾部签名闸门失败: %s %d/%d" % (script, h, tot2))

    st = {
        "src": src, "rows": len(rows), "scenes": len(scene_ids), "out": SC.tsv_path(src),
        "ops": dict(ops), "confidence": dict(confs), "drops": dict(drops),
        "skip_scenes": [r["scene_id"] for r in rows if r["op"] == "skip"],
        "no_line_scenes": no_line,
        "tob_tail_signature": "%d/%d" % (tail_hit, tail_tot),
        "conservation": {k: "%d/%d" % (cov[k], want_tot[k]) for k in want_tot},
        "conservation_violations": cons,
        "unresolved_assets": dict(unresolved),
        "gate_set_conservation": (len(cons) == 0),
    }
    return rows, st


def tsv_bytes(rows):
    """与 `_staging_common.write_tsv` **完全同式**的字节串（供 `--check` 逐字节比对，不落盘）。

    同式依据：`write_tsv` 以 `io.open(..., "w", encoding="utf-8", newline="")` 写出
    `HEADER` + 每条记录（`"\\t".join(str(r[c]) for c in HEADER)`）+ `"\\n"`。
    `newline=""` ⇒ 无换行翻译；`encoding="utf-8"` ⇒ 无 BOM。故下述构造字节等价。
    """
    buf = ["\t".join(SC.HEADER)]
    for r in rows:
        if len(r) != SC.NCOL or list(r) != SC.HEADER:
            raise SystemExit("!! 记录列不符：%r" % (sorted(r),))
        buf.append("\t".join(str(r[c]) for c in SC.HEADER))
    return ("\n".join(buf) + "\n").encode("utf-8")


def _print_stats(st, extra=None):
    w = sys.stdout.write
    w("\n================ %s ================\n" % st["src"].upper())
    w("产物            : %s\n" % st["out"])
    w("行数            : %d（场景 %d）\n" % (st["rows"], st["scenes"]))
    w("op 分布         : %s\n" % st["ops"])
    w("confidence 分布 : %s\n" % st["confidence"])
    w("丢弃类计数      : %s\n" % st["drops"])
    w("skip 场景数     : %d %s\n" % (len(st["skip_scenes"]), st["skip_scenes"][:8]))
    w("TOB0 尾部签名   : %s（100%% 命中）\n" % st["tob_tail_signature"])
    w("闸门①集合守恒   : %s ｜ 覆盖 %s ｜ 违规 %d\n"
      % ("PASS" if st["gate_set_conservation"] else "FAIL",
         st["conservation"], len(st["conservation_violations"])))
    for v in st["conservation_violations"][:20]:
        w("    ! %s %s(%s) 缺 %s\n" % (v[0], v[1], v[2], v[3]))
    w("闸门②场景覆盖   : PASS\n")
    w("闸门③令牌可解析 : PASS\n")
    if extra:
        w(extra + "\n")
    if st["unresolved_assets"]:
        w("总账不可解析引用（与既有 assets[].hit=false 同源，不可作 target）:\n")
        for sid2, items in sorted(st["unresolved_assets"].items()):
            w("    %s -> %s\n" % (sid2, items))


def main():
    ap = argparse.ArgumentParser(
        description="otr/ota 逐行演出表生成器（ISSUE-20261001-14）")
    ap.add_argument("--check", action="store_true",
                    help="幂等自检：**不写盘**，把本轮重算的字节与磁盘产物逐字节比对")
    a = ap.parse_args()

    for src in ("otr", "ota"):
        rows, st = collect(src)
        payload = tsv_bytes(rows)
        out = st["out"]
        if a.check:
            if not os.path.isfile(out):
                raise SystemExit("!! --check：产物不存在，先跑一次生成：%s" % out)
            # 行尾规范化后比较（autocrlf 检出的盘面是 CRLF；见 交接说明 C12）
            on_disk = SC.read_artifact_bytes(out)
            if on_disk != payload:
                raise SystemExit(
                    "!! 闸门④ 幂等失败：磁盘产物与本轮重算不一致（%s）\n"
                    "   磁盘 %d 字节 / 重算 %d 字节"
                    % (out, len(on_disk), len(payload)))
            _print_stats(st, extra="闸门④幂等      : PASS（逐字节相同，%d 字节；行尾已规范化比较）"
                                   % len(payload))
        else:
            n = SC.write_tsv(out, rows)
            # 落盘后自证：磁盘字节 == 重算字节（使 tsv_bytes 与 write_tsv 不可能漂移）
            if SC.read_artifact_bytes(out) != payload:
                raise SystemExit("!! tsv_bytes 与 write_tsv 输出不一致（%s）" % out)
            _print_stats(st, extra="闸门④幂等      : 已写入 %d 行（可用 --check 复验）" % n)


if __name__ == "__main__":
    main()
