# -*- coding: utf-8 -*-
r"""
`tob_parse.py` —— **After Story（`ota`）TOB0 逐行演出解析器**（ISSUE-20261008-09 · A 层）

一句话
    把 172 个 `.tob`（TOB0 容器）里 **72,822 条记录**的实参**真正解出来**，落成
    「新源侧」19 列表 `演出新源_ota.tsv`，供 `build_story.py` 之类的下游消费。

复跑（读写分离：读 `GRETA_DATA_ROOT`（默认 `E:\ZCode Workspace\Galgame`））
    python -X utf8 tob_parse.py                     # 生成 演出新源_ota.tsv + _stats.json + _records_ota.tsv + op名表.tsv
    python -X utf8 tob_parse.py --stats             # 只打印统计（不写盘）
    python -X utf8 tob_parse.py --names             # 只打印 op 名表（不写盘）
    python -X utf8 tob_parse.py --check             # **严格只读**幂等自检：把本轮重算的字节与磁盘产物逐字节比对
    python -X utf8 tob_parse.py --check --mutate 0x22   # 变异自证：改坏 op 名表一处，--check 必须 FAIL
    python -X utf8 tob_parse.py --out <路径>         # 改产物落点

需用户裁决前须知（**本模块的全部结论边界**）
    * `op`（闭集，12 值）与 `fam`（TOB0 记录头 op 的族名，能定的定名、定不下的写 `tob_0xNN`）分列；
      **未证 op 一律 `param_ok=0`**（严禁猜测定名）。
    * `param_ok=1` ⟺ 「该行是演出事件**且**其实参已解出」。纯行边界标记（`line_end`/`line_begin`）、
      对话记录（`dialog`）、未证 op、项流未能切分的记录 ⇒ `param_ok=0`。
    * `layer` 恒空 —— **PC 侧层序无携带者**（层序唯一来源＝PSV `:Priority`，见作品 skill §四·补）；
      本模块**不合成、不外推**层序。
    * `x`/`y` 仅在 op=0x32（背景关键帧坐标串）有源侧直证，且为**源画布 800×600 整数坐标**（未换算）；
      其余行的 `x`/`y` 恒空（PC 侧立绘只有方向 token，见 `x_src`）。

产物（默认落本脚本所在目录）
    `演出新源_ota.tsv`（19 列，见 `HEADER`）
    `_records_ota.tsv`（**逐记录审计档**：全 72,822 条一条不落，供验收标准①对账）
    `_stats.json`（机读汇总；`--check` 下**不写**）

文法（每条结论的 hex 证据见 `TOB0文法_说明.md`）
    记录头 `5b 20 <op u8> 00 00 00 01`，紧接 `<u32 L>`；**记录长 = L + 7**（body = L-4 字节）。
    记录之间可有**原文岛**（纯 SJIS 对话正文，不含 0x00）——扫描器按「头部特征」逐条推进。
    body = `<u8 count>` + count 个 item；item = `<u8 tag>` + 载荷：
        tag 0x00 → 0 字节（占位）
        tag 0x01 → `<u8 sel>`；sel 0x00 → u32；sel 0x01 → `<u16 n>` + n 字节（声明串，末字节 NUL）
        tag 0x02 → u32
      （未证：tag 0x03（op=0x04 专用）/ tag 0xff（24_* 的 op=0x08 变体）——逐条列出、`param_ok=0`）
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
import re
import struct
import sys

sys.dont_write_bytecode = True        # 严禁在只读源目录（资源组\工具）留下 __pycache__

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
TOB_DIR = os.path.join(DATA_ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")
TALK_JSON = os.path.join(DATA_ROOT, "工程", "我们没有翅膀 After Story", "语料", "台词.json")
SCENE_OTA = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原",
                         "资源组", "剧本", "scene_ota.jsonl")
SC_TOOL_DIR = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原",
                           "资源组", "工具")

SRC = "ota"
OUT_TABLE = os.path.join(HERE, "演出新源_ota.tsv")
OUT_RECORDS = os.path.join(HERE, "_records_ota.tsv")
OUT_STATS = os.path.join(HERE, "_stats.json")
OUT_NAMES = os.path.join(HERE, "op名表.tsv")

HEADER = ["scene_id", "src", "seq", "ord", "op", "fam", "tgt", "slot", "x", "y",
          "x_src", "dur_ms", "kind", "args", "argmap", "param_ok", "conf", "layer", "evidence"]
NCOL = len(HEADER)
OPS = ("chr_add", "chr_remove", "chr_move", "chr_expr",
       "bg", "se", "bgm", "movie", "wait", "effect", "other", "skip")
CONFS = ("exact", "inferred", "unknown")

REC_HDR0 = b"\x5b\x20"
TAIL_OP = 0x0C          # 行尾锚点（值 = 消息序号 k）
LINE_BEGIN_OP = 0x10    # 行首标记（body count=0）
TITLE_OP = 0x12         # 场景标题声明（单声明串）

# ================================================================ op 名表（能定的定名，定不下的 未证）
# 值 = (fam, op_closed, kind, note)
#   fam    : TOB0 记录头 op 的族名；`tob_0xNN` = 未证
#   op     : 闭集 12 值之一（下游契约）
#   kind   : 细分（效果/转场/移动走这里）
#   note   : 定名依据（一句话，逐字进 evidence）
NAMED = {
    0x07: ("label_sc",    "other", "label",     "声明串 'SC_<NN>'（脚本标签，非资源）"),
    0x08: ("jump_label",  "other", "label",     "声明串 '<NN>_<XX>'（跳转标签，形态同场名）"),
    0x0C: ("line_end",    "other", "marker",    "单 u32 = 消息序号 k（与台词.json 的 index 逐条一致）"),
    0x0D: ("choice",      "other", "choice",    "声明串 = 人名/选项文本（选项菜单）"),
    0x10: ("line_begin",  "other", "marker",    "body count=0（每条 line_end 后恒跟一条）"),
    0x12: ("scene_title", "other", "title",     "单声明串，内容 == 台词.json 的 title 文本"),
    0x14: ("ms",          "wait",  "ms_single", "单 u32，值域 100..1000 的整百毫秒（邻 SE 记录）"),
    0x18: ("dialog",      "other", "dialog",    "声明串 = 話者名 + 语音 ID（对白记录本体）"),
    0x22: ("bg_set",      "bg",    "path_pic",  "声明串 = `PIC\\*.ELG`（背景/贴图件）"),
    0x2F: ("sprite_move", "other", "ctrl",      "声明串 = 控制串（r/l/d/u/<N/+N/-N）+ ms 位"),
    0x30: ("sprite_move", "other", "ctrl",      "声明串 = 控制串（d/r/c/l/u/+N）"),
    0x32: ("bg_keyframe", "effect", "coord_800x600", "声明串 = 坐标串 `(x,y,p)(x,y,q)`（背景关键帧）"),
    0x3B: ("ms_vector",   "wait",  "ms_vector", "多 u32 值向量（100/200/4000… 毫秒）"),
    0x49: ("chr_ref_a",   "chr_add", "chr",     "声明串 = 裸立绘差分名（KOB01H/CIN051…）"),
    0x51: ("chr_action",  "chr_expr", "ctrl",   "声明串 = 控制串（`_`/`c`/`!l`/`l<2`/`]`…）+ ms 位"),
    0x52: ("chr_pos",     "chr_place", "ctrl",  "声明串 = 位置 token（`l<2`/`r>2`/`!l`/`!r`…）"),
    0x5D: ("ms",          "wait",  "ms_single", "单 u32，值域 50..1000 毫秒（跟随其前的 bg/chr 记录）"),
    0x61: ("ms",          "wait",  "ms_single", "单 u32，主值 1200 毫秒（跟随其前的 op=0x73 记录）"),
    0x63: ("bg_set_fx",   "bg",    "path_pic",  "声明串 = `PIC\\*.ELG` + ms 位"),
    0x64: ("bg_set_fx",   "bg",    "path_pic",  "声明串 = `PIC\\*.ELG` + ms/幅值位"),
    0x65: ("bg_set_fx",   "bg",    "path_pic",  "声明串 = `PIC\\*.ELG` + ms/幅值位（含 EC 卡面）"),
    0x66: ("chr_ref_b",   "chr_add", "chr",     "声明串 = 裸立绘差分名（ASU02I/NAR01…）"),
    0x76: ("se_play",     "se",    "path_se",   "声明串 = `SE\\*.OGG`"),
    0x77: ("se_play_fx",  "se",    "path_se",   "声明串 = `SE\\*.OGG` + ms 位"),
    0x7D: ("chr_ref_sp",  "chr_add", "chr",     "声明串 = 裸立绘名 + `_SP` 后缀（NAR_SP15…）"),
    # ---- 本批（ISSUE-20261008-09 二轮）新增定名：判据 = 量化邻接/共现（见 TOB0文法_说明 §十二）----
    0x09: ("scene_end",   "other", "marker",
           "body count=2 全空（无参）；11 场各 1 次，其后恒为「下一场转场块（0x04/0x73）或文件末」⇒ 脚本段终止标记"),
    0x0E: ("choice_begin", "other", "choice_marker",
           "body count=0（无参）；与 0x0d(choice) **同场且每场恰 1 次**（20/20），恒在 0x0d **之前**那条 line_end 之前 ⇒ 选择块开始"),
    0x11: ("choice_end",  "other", "choice_marker",
           "body count=0（无参）；与 0x0d/0x0e **同场且每场恰 1 次**（20/20），恒在 0x0d **之后**那条 line_end 之后、跳转 0x08 之前 ⇒ 选择块结束"),
    0x74: ("scene_close", "other", "marker",
           "单 u32=1；prev **恒** 0x5b（76/76）、next **恒** 0x50（76/76），50/76 落在场末 3 条内 ⇒ 收场序列 0x5b→0x74→0x50 的中段标记（并列候选 close_marker）"),
}
# 已知但**不产出主线行**的纯行边界标记（仍逐条落 `_records_ota.tsv`）
BOUNDARY_ONLY = (TAIL_OP, LINE_BEGIN_OP)

# ================================================================ 候选名表（**不计入定名**）
# 载荷/邻接只支持「结构角色」，语义名不唯一 ⇒ 一律多名并列（验收标准③），fam 仍写 `tob_0xNN`、`param_ok=0`。
# 值 = (并列候选名（`|` 分隔）, 判据一句话)
CAND = {
    0x04: ("trans_ref|call_ref",
           "定长模板 + 3 字节句柄 + flags；sel=0x03 未证编码；330/363 后邻 0x22(bg_set)"),
    0x23: ("screen_color|filter_color",
           "值域仅 {0xFFFFFF(白), 0}(黑) 的 24 位色 + flag；103/153 前邻 0x72(i0)"),
    0x26: ("layer_flag|bit_flag",
           "位掩码值域 {2,4,8,16} + flag；恒邻 0x22(bg_set)"),
    0x31: ("bg_effect|bg_transform",
           "11 操作数，含数值串模式选择（'1'..'4'/'0.5'/'0.3'/'0.7'/'−1'）"),
    0x50: ("layer_slot|fade_flag",
           "恒 [1, 0xFFFFFFFF]（0xFFFFFFFF=null 哨兵）；常随 bg/chr 设定后出现"),
    0x55: ("line_pre|msg_slot",
           "行首前置（prev 恒 0x10 840/1050）；首操作数 0..4"),
    0x56: ("line_pre_b|msg_slot_b",
           "行首前置（prev 恒 0x10 23/34）；首操作数 0..3（= 0x55 去尾部 flag）"),
    0x5A: ("chr_open_pre|staging_clear",
           "0 参；767/824 后邻 0x49(chr_add)、505/824 前邻 0x10(line_begin)"),
    0x5B: ("frame_sync|display_flush",
           "恒 [1]；行首（1112/2747 前邻 0x10）与效果/等待后（0x5e/0x5d/0x65/0x60）"),
    0x5E: ("effect_ms_a|flash",
           "三整参 (A, 500, 500|255)；A∈40..65；441/529 后邻 0x5b"),
    0x5F: ("scene_effect|filter_default",
           "恒定 (86, 500, 1)；94 场中 79 场恰 1 次；next 恒 0x5b（109/110）"),
    0x60: ("effect_ms_b",
           "(mode, ms, a, 64|128|550, 768) 5 操作数；195/229 后邻 0x5b"),
    0x68: ("line_pre_c|ruby",
           "恒定 (_, 0xFFFFFFFF, 32, 0xFFFFFFFF)；32=0x20（空格）；146/214 前邻 0x10"),
    0x6F: ("flash|fade_color|screen_tint",
           "(ms, 24 位色)；ms∈{10,100,200,300}、色∈{0xFFFFFF,0x6C24AD,0xE6B0E2}；43 次自邻=连续变色"),
    0x72: ("bg_prepare|layer_reset",
           "恒 [0]；先于 bg 切换 0x22/0x65/0x04 共 648/915"),
    0x73: ("effect_ms|scene_effect",
           "(A, [ms], 1)；A=0 时给 ms（332/386），A≠0 时无 ms；63 条落场首 3 条、70 条落场末 3 条"),
    0x79: ("line_pre_d|page_wait",
           "0 参（883/979）；618/979 前邻 0x10、42 条落场末 3 条内"),
}

# 位置 token → slot（与 SOB0 §12.4 同一套词表；作品 skill §四·补「PC 侧立绘只有方向 token」）
POS_TOKEN_RULES = (
    (("l<", "!l"), "left"),
    (("r>", "!r"), "right"),
)
COORD_RE = re.compile(r"^\((\d+),\s*(\d+),\s*(-?\d+)\)")


def fam_of(op: int) -> tuple[str, str, str, str]:
    """→ (fam, op_closed, kind, note)；未证 op 返回 `tob_0xNN` + `other` + `unproven`。"""
    e = NAMED.get(op)
    if e is None:
        return "tob_0x%02x" % op, "other", "unproven", "未证"
    if op in MUTATE:
        # 变异自证用：只改内存中的名表（绝不落盘）
        return (e[0] + "_MUT", e[1], e[2], e[3] + "（MUTATED）")
    return e


MUTATE: set[int] = set()

# ================================================================ 记录与项流
class TobError(Exception):
    pass


def parse_tob_header(d: bytes) -> int:
    """TOB0 头部 → code_start。magic + u32 size + u32 标签数 B + [u8 名长][名][0x00][u32 偏移]×B"""
    if d[:4] != b"TOB0":
        raise TobError("magic 不是 TOB0")
    nlab = struct.unpack_from("<I", d, 8)[0]
    p = 0x0C
    for _ in range(nlab):
        if p >= len(d):
            raise TobError("标签段越界")
        ln = d[p]
        if p + 1 + ln > len(d):
            raise TobError("标签长度非法")
        p += 1 + ln
    if p + 8 > len(d):
        raise TobError("缺少映射段")
    A = struct.unpack_from("<I", d, p)[0]
    B = struct.unpack_from("<I", d, p + 4)[0]
    if A != 8 + 4 * B:
        raise TobError("映射段自述大小不符 A=%d B=%d" % (A, B))
    return p + 8 + 4 * B


def is_rec_header(d: bytes, i: int) -> bool:
    return (i + 11 <= len(d) and d[i:i + 2] == REC_HDR0
            and d[i + 3:i + 6] == b"\x00\x00\x00" and d[i + 6] == 0x01)


def scan_records(d: bytes, code_start: int):
    """→ (records, islands)。

    records = [(off, op, L, body)]（按偏移升序）；
    islands = [(lo, hi)] —— 记录之间被跳过的**原文岛**（纯 SJIS 对话正文）。
    推进规则：在 `i` 处是合法记录头 ⇒ 取该记录（长 `L+7`）；否则 `i += 1`（扫过原文岛）。
    """
    recs, islands = [], []
    i, n, isl_lo = code_start, len(d), None
    while i + 11 <= n:
        if is_rec_header(d, i):
            if isl_lo is not None:
                islands.append((isl_lo, i))
                isl_lo = None
            op = d[i + 2]
            L = struct.unpack_from("<I", d, i + 7)[0]
            if L < 4 or i + 7 + L > n:
                raise TobError("记录长度越界 @0x%x op=0x%02x L=%d" % (i, op, L))
            recs.append((i, op, L, d[i + 11:i + 7 + L]))
            i += 7 + L
        else:
            if isl_lo is None:
                isl_lo = i
            i += 1
    if isl_lo is None and i < n:
        isl_lo = i        # 尾部残余（不足 11 字节，装不下记录头）也算正文岛
    if isl_lo is not None:
        islands.append((isl_lo, n))
    return recs, islands


class Item:
    __slots__ = ("tag", "sel", "val", "raw", "ok")

    def __init__(self, tag, sel, val, raw, ok=True):
        self.tag, self.sel, self.val, self.raw, self.ok = tag, sel, val, raw, ok


def split_items(body: bytes):
    """body → (ok, items, err)。ok=False 表示**项流未能切分**（未知 tag/sel 或余字节 ≠ 0）。"""
    if not body:
        return False, [], "empty body"
    cnt = body[0]
    p, items = 1, []
    for _ in range(cnt):
        if p >= len(body):
            return False, items, "truncated at item header p=%d len=%d" % (p, len(body))
        tag = body[p]
        p += 1
        if tag == 0x00:
            items.append(Item(0x00, None, None, b""))
        elif tag == 0x01:
            if p >= len(body):
                return False, items, "trunc tag01 sel"
            sel = body[p]
            p += 1
            if sel == 0x00:
                if p + 4 > len(body):
                    return False, items, "trunc tag01/00 u32"
                items.append(Item(0x01, sel, struct.unpack_from("<I", body, p)[0], b""))
                p += 4
            elif sel == 0x01:
                if p + 2 > len(body):
                    return False, items, "trunc tag01/01 len"
                n = struct.unpack_from("<H", body, p)[0]
                p += 2
                if p + n > len(body):
                    return False, items, "trunc tag01/01 body n=%d rem=%d" % (n, len(body) - p)
                raw = body[p:p + n]
                items.append(Item(0x01, sel, raw, raw))
                p += n
            else:
                items.append(Item(0x01, sel, body[p:], body[p:], ok=False))
                return False, items, "unknown sel 0x%02x" % sel
        elif tag == 0x02:
            if p + 4 > len(body):
                return False, items, "trunc tag02 u32"
            items.append(Item(0x02, None, struct.unpack_from("<I", body, p)[0], b""))
            p += 4
        else:
            items.append(Item(tag, None, body[p:], body[p:], ok=False))
            return False, items, "unknown tag 0x%02x" % tag
    if p != len(body):
        return False, items, "remainder %d" % (len(body) - p)
    return True, items, ""


def s32(v: int) -> int:
    return v - 0x100000000 if v >= 0x80000000 else v


def item_str(it: Item):
    if it.tag == 0x00:
        return "()"
    if it.tag == 0x01 and it.sel == 0x00:
        return "i%d" % s32(it.val)
    if it.tag == 0x01 and it.sel == 0x01:
        try:
            return '"%s"' % it.val[:-1].decode("cp932")
        except Exception:                                   # noqa: BLE001
            return '"<non-cp932:%s>"' % it.val.hex()
    if it.tag == 0x02:
        return "u%d" % it.val
    return "?tag%02x<%s>" % (it.tag, (it.raw or b"").hex())


def fmt_args(items) -> str:
    return "|".join(item_str(it) for it in items)


def decl_text(it: Item):
    """声明串（tag01/sel01）→ 文本；否则 None。"""
    if it.tag == 0x01 and it.sel == 0x01:
        try:
            return it.val[:-1].decode("cp932")
        except Exception:                                   # noqa: BLE001
            return None
    return None


# ================================================================ seq 锚定
def load_seq_maps():
    """`scene_ota.jsonl` → ({scene_id: {消息 index: seq}}, {scene_id: 标题行 seq},
                            {scene_id: 末行 seq}, [重复 index 的场景])。

    **口径 = 既有生成器 `build_staging_tob.py` 的 `SeqMap`**（键 = 记录区边界位置、值 =
    `lines[].seq`）：文件里 `line_end`（`op=0x0c`）携带的 u32 = **消息 index**，与
    `scene_ota.jsonl` 的 `lines[].index` 同坐标系 ⇒ `seq = idx2seq[index]`。
    末条 `line_end` **之后**的记录区（`after_last_line`）⇒ `seq = 末行 seq`、`conf=inferred`
    （旧表同口径；实测 `24_*` 的尾声属此类——若不特判，末段 4 处会错标为末条对白的 seq）。
    ⚠️ `24_*` 等场景的消息 index 是**置换**（`24_1b` 实测 = 0,1,2,3,4,7,…,111,5,6）⇒
    `seq ≠ index + 2`；但 `index → seq` 实测**单射**（无重复 index，`dup_seq_index` 为空），
    故字典口径成立。
    """
    idx2seq, titles, lastseq, dups = {}, {}, {}, []
    with io.open(SCENE_OTA, encoding="utf-8") as f:
        for ln in f:
            o = json.loads(ln)
            sid = o["scene_id"]
            m, seen, mx = {}, [], 0
            for l in o["lines"]:
                mx = max(mx, l["seq"])
                if l.get("index") is None:
                    if l.get("kind") == "title":
                        titles[sid] = l["seq"]
                else:
                    if l["index"] in m:
                        seen.append(l["index"])
                    m[l["index"]] = l["seq"]
            idx2seq[sid], lastseq[sid] = m, mx
            if seen:
                dups.append({"scene_id": sid, "dup_index": sorted(set(seen))})
    return idx2seq, titles, lastseq, dups


def load_ledger():
    """只读载入 `资源总账.json` 的契约视图（读 `资源组\\工具\\_staging_common`，**绝不改它**）。"""
    if SC_TOOL_DIR not in sys.path:
        sys.path.insert(0, SC_TOOL_DIR)
    import _staging_common as SC          # noqa: E402
    led = SC.Ledger.load()
    return led, SC


# ================================================================ 分类
def path_kind(SC, s):
    return SC.path_ref(s)


def slot_of_ctrl(s: str):
    """控制串 → slot（左/右）；判不出返回 None（**不猜**）。"""
    up = s
    for keys, slot in POS_TOKEN_RULES:
        for k in keys:
            if k in up:
                return slot
    return None


def build_rows(led, SC, lseqmap, titles, lastseqmap, files_stats):
    rows, audit = [], []
    per_op = collections.Counter()
    param_ok_cnt = collections.Counter()
    conf_cnt = collections.Counter()
    class_cnt = collections.Counter()
    fails = []
    island_total_bytes = 0
    record_bytes = 0
    data_bytes = 0
    tail_hits = 0
    rec_total = 0
    seq_anomalies = []
    noline_scenes = []

    for fn in sorted(f for f in os.listdir(TOB_DIR) if f.lower().endswith(".tob")):
        script = fn[:-4]
        scene_id = "%s_%s" % (SRC, script)
        d = open(os.path.join(TOB_DIR, fn), "rb").read()
        try:
            cs = parse_tob_header(d)
        except TobError as e:
            fails.append({"file": fn, "off": None, "reason": "header: %s" % e})
            continue
        recs, islands = scan_records(d, cs)
        island_total_bytes += sum(hi - lo for lo, hi in islands)
        record_bytes += sum(7 + r[2] for r in recs)
        data_bytes += len(d) - cs
        rec_total += len(recs)
        idx2seq = lseqmap.get(scene_id, {})
        tseq = titles.get(scene_id)
        last_seq = lastseqmap.get(scene_id, 1)
        if last_seq <= 0:
            noline_scenes.append(scene_id)

        # ---- 逐条：`line_end` 携带的 u32 = **消息 index** ⇒ seq = idx2seq[index]
        #      （**与既有生成器 `build_staging_tob.py` 的 SeqMap 同口径**；见 load_seq_maps）
        #      `24_*` 等场景的 index 是置换（seq ≠ index+2），但映射是单射。
        tails = [j for j, r in enumerate(recs) if r[1] == TAIL_OP]
        seq_of_rec = [None] * len(recs)
        for ti, j in enumerate(tails):
            k, ok_k = tail_k(recs[j])
            if ok_k:
                tail_hits += 1
            else:
                seq_anomalies.append({"file": fn, "off": "0x%x" % recs[j][0],
                                      "reason": "line_end 的 u32 未能解出", "val": k})
            nxt = tails[ti + 1] if ti + 1 < len(tails) else len(recs)
            seq = idx2seq.get(k, last_seq)
            for jj in range(0 if ti == 0 else tails[ti - 1] + 1, nxt):
                seq_of_rec[jj] = (seq, "exact", k)
        if not tails:
            for jj in range(len(recs)):
                seq_of_rec[jj] = (last_seq, "inferred", None)

        # ---- 每 seq 的位置 token 收集（用于 chr 行 slot 派生）
        slot_by_seq = collections.defaultdict(set)
        for j, (off, op, L, body) in enumerate(recs):
            if op not in (0x51, 0x52, 0x2F, 0x30):
                continue
            ok, items, _err = split_items(body)
            for it in items:
                t = decl_text(it)
                if t:
                    sl = slot_of_ctrl(t)
                    if sl:
                        slot_by_seq[seq_of_rec[j][0]].add(sl)

        per_scene_ord = collections.Counter()
        for j, (off, op, L, body) in enumerate(recs):
            per_op[op] += 1
            ok, items, err = split_items(body)
            fam, oc, kind, note = fam_of(op)

            rec_str = body[:64].hex()
            audit.append((scene_id, "0x%x" % off, op, L, fam, 1 if ok else 0,
                          len(items), fmt_args(items) if items else "", rec_str, err))

            if op in BOUNDARY_ONLY:
                continue        # 纯行边界标记：不入主线表（仍在审计档）

            seq, conf, k = seq_of_rec[j]
            noline = last_seq <= 0
            if seq is None:
                # 无法定位（无 tail 且无 lines）⇒ 挂末行，conf=unknown
                seq = last_seq
                conf = "unknown"
            if op == TITLE_OP and tseq is not None:
                seq, conf = tseq, "exact"
            elif tails and j > tails[-1]:
                # 末条 line_end 之后 ⇒ after_last_line（旧表同口径：seq=末行、conf=inferred）
                seq, conf = last_seq, "inferred"
            if noline:
                # 该场 0 条文本行（实测仅 `ota_sr`）：无 lines[].seq 可锚定 ⇒ seq=0、
                # param_ok 强制 0（下游不得当演出消费）。与既有表的 `skip` 口径同义。
                seq, conf = 0, "unknown"
            if conf is None:
                conf = "unknown"
            ordn = per_scene_ord[seq] + 1        # 1-based：同一 (scene, seq) 内的触发序
            per_scene_ord[seq] += 1

            tgt = ""
            slot = ""
            x = y = ""
            x_src = ""
            dur = ""
            amap = {}
            pok = 0
            ev_extra = ""

            if not ok:
                kind = "unproven_item_stream"
                note = "项流未能切分（%s）⇒ 实参未解" % err
                fails.append({"file": fn, "off": off, "op": "0x%02x" % op,
                              "L": L, "reason": err, "body_hex": body.hex()})

            # ---------- 类①：ms 时间
            if ok and fam in ("ms", "ms_vector"):
                ms = [s32(it.val) for it in items if it.tag in (0x01, 0x02)
                      and it.sel in (None, 0x00)]
                ms = [m for m in ms if m >= 0]
                if op == 0x3B:
                    # 向量：**未定位到唯一 ms 位**（向量内混有 flag），故 `dur_ms` 留空、
                    # 候选值进 argmap（诚实边界，不硬取一个位当 ms）
                    amap = {"ms_vector": ms}
                    pok = 1 if ms else 0
                else:
                    dur = ms[0] if ms else ""
                    amap = {"ms": dur} if str(dur) != "" else {}
                    pok = 1 if str(dur) != "" else 0
                class_cnt["ms"] += 1

            # ---------- 类②：控制串内联
            elif ok and kind == "ctrl":
                ctrl = ""
                for it in items:
                    t = decl_text(it)
                    if t is not None and t != "":
                        ctrl = t
                        break
                x_src = ctrl
                ms = [s32(it.val) for it in items
                      if it.tag == 0x01 and it.sel == 0x00 and s32(it.val) >= 50]
                if ms:
                    dur = ms[0]
                if op == 0x52:
                    sl = slot_of_ctrl(ctrl)
                    if sl:
                        slot = sl
                    amap = {"ctrl": ctrl}
                else:
                    amap = {"ctrl": ctrl}
                    if dur != "":
                        amap["ms"] = dur
                pok = 1 if ctrl else 0
                class_cnt["ctrl"] += 1

            elif ok and kind == "coord_800x600":
                cstr = ""
                for it in items:
                    t = decl_text(it)
                    if t and COORD_RE.match(t):
                        cstr = t
                        break
                x_src = cstr
                m = COORD_RE.match(cstr) if cstr else None
                if m:
                    x, y = m.group(1), m.group(2)
                    amap = {"coord": cstr, "p": m.group(3)}
                    pok = 1
                else:
                    amap = {"coord": ""}
                class_cnt["coord"] += 1

            # ---------- 类③：裸角色名 + u32（-1 = null 哨兵）
            elif ok and kind == "chr":
                name = ""
                for it in items:
                    t = decl_text(it)
                    if t:
                        name = t
                        break
                nums = [s32(it.val) for it in items if it.tag in (0x01, 0x02)
                        and it.sel in (None, 0x00)]
                rel = led.target("chr", name, SRC) if (led and name) else None
                tgt = rel or name
                amap = {"name": name, "nums": nums}
                if rel is None and name:
                    ev_extra = "; ref_missing(总账无此件)"
                sl = slot_by_seq.get(seq) or set()
                if len(sl) == 1:
                    slot = next(iter(sl))
                elif len(sl) > 1:
                    ev_extra += "; slot_ambiguous(同 seq 多方向 token)"
                pok = 1 if name else 0
                class_cnt["chr"] += 1

            # ---------- 路径类（bg / se）
            elif ok and kind in ("path_pic", "path_se"):
                path = ""
                for it in items:
                    t = decl_text(it)
                    if t and ("\\" in t or "/" in t):
                        path = t
                        break
                k2, tok = (path_kind(SC, path) if path else (None, None))
                rel = led.target(k2, tok, SRC) if (led and k2) else None
                tgt = rel or tok or ""
                if rel is None and tok:
                    ev_extra = "; ref_missing(总账无此件)"
                ms = [s32(it.val) for it in items
                      if it.tag == 0x01 and it.sel == 0x00 and s32(it.val) >= 50]
                if ms:
                    dur = ms[0]
                amap = {"path": path}
                if dur != "":
                    amap["ms"] = dur
                pok = 1 if path else 0
                class_cnt["bg" if kind == "path_pic" else "se"] += 1

            elif ok and fam in ("scene_title", "label_sc", "jump_label", "choice", "dialog"):
                txt = ""
                for it in items:
                    t = decl_text(it)
                    if t:
                        txt = t
                        break
                if op == 0x18:
                    names = [decl_text(it) for it in items if decl_text(it)]
                    amap = {"speaker": names[0] if names else "",
                            "voice": names[1] if len(names) > 1 else ""}
                else:
                    amap = {"text": txt}
                pok = 0        # 非演出事件：不给下游当演出消费
                class_cnt["meta"] += 1

            elif ok and kind in ("marker", "choice_marker"):
                # 本批新增的结构标记（scene_end / choice_begin / choice_end / scene_close）：
                # **无实参、非演出事件** ⇒ `param_ok=0`，只登记形态
                nums = [s32(it.val) for it in items if it.tag in (0x01, 0x02)
                        and it.sel in (None, 0x00)]
                if nums:
                    amap["nums"] = nums
                pok = 0
                class_cnt["meta"] += 1

            elif not ok:
                pok = 0
            else:
                # 未证 op
                nums = [s32(it.val) for it in items if it.tag in (0x01, 0x02)
                        and it.sel in (None, 0x00)]
                strs = [decl_text(it) for it in items if decl_text(it)]
                if nums:
                    amap["nums"] = nums
                if strs:
                    amap["strs"] = strs
                pok = 0
                class_cnt["unproven"] += 1

            if noline:
                pok = 0
                ev_extra += "; no_line_anchor（该场 0 条文本行，无 lines[].seq 可锚定）"
            param_ok_cnt[1 if pok else 0] += 1
            conf_cnt[conf] += 1

            ev = ("script=%s; 记录@0x%x L=%d op=0x%02x fam=%s (%s); args=%s"
                  % (script, off, L, op, fam, note, fmt_args(items) if items else "-"))
            if ev_extra:
                ev += ev_extra
            ev += "; layer 无源侧携带者 ⇒ 留空"

            rows.append({
                "scene_id": scene_id, "src": SRC, "seq": seq, "ord": ordn,
                "op": oc, "fam": fam, "tgt": tgt, "slot": slot, "x": x, "y": y,
                "x_src": x_src, "dur_ms": dur, "kind": kind,
                "args": fmt_args(items) if items else "",
                "argmap": json.dumps(amap, ensure_ascii=False, sort_keys=True),
                "param_ok": pok, "conf": conf, "layer": "",
                "evidence": ev,
            })

    files_stats.update({
        "records_total": rec_total,
        "island_bytes": island_total_bytes,
        "record_bytes": record_bytes,
        "bytes_after_header": data_bytes,
        "bytes_accounting_delta": data_bytes - record_bytes - island_total_bytes,
        "tail_anchors": tail_hits,
        "per_op": {("0x%02x" % k): v for k, v in sorted(per_op.items())},
        "op_distinct": len(per_op),
        "param_ok": dict(param_ok_cnt),
        "conf": dict(conf_cnt),
        "classes": dict(class_cnt),
        "fails": fails,
        "seq_anomalies": seq_anomalies,
        "no_line_scenes": noline_scenes,
    })
    return rows, audit


def tail_k(rec):
    """line_end 记录的 u32 = 消息序号 k → (k, ok)。"""
    _off, op, _L, body = rec
    ok, items, _err = split_items(body)
    if ok and len(items) == 1 and items[0].tag == 0x01 and items[0].sel == 0x00:
        return s32(items[0].val), True
    return None, False


# ================================================================ 序列化
def _clean(v):
    if v is None:
        return ""
    return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def table_bytes(rows) -> bytes:
    buf = ["\t".join(HEADER)]
    for r in rows:
        if len(r) != NCOL:
            raise SystemExit("!! 记录列数不符：%d" % len(r))
        buf.append("\t".join(_clean(r[c]) for c in HEADER))
    return ("\n".join(buf) + "\n").encode("utf-8")


RECHEADER = ["scene_id", "off", "op_dec", "L", "fam", "parsed_ok", "n_items",
             "items", "body_hex64", "err"]


def records_bytes(audit) -> bytes:
    buf = ["\t".join(RECHEADER)]
    for a in audit:
        buf.append("\t".join(_clean(x) for x in a))
    return ("\n".join(buf) + "\n").encode("utf-8")


# ================================================================ op 名表（机器可读，供一审/下游）
NAMES_HEADER = ["op", "名", "判据类别", "证据(文件:偏移:hex)", "conf", "反例数", "备注"]
# 本批新增定名的置信度（未列 = 既有定名「高」）
CONF_OVERRIDE = {"0x09": "高", "0x0e": "高", "0x11": "高", "0x74": "中"}


def _citations(audit, op_dec, k=2):
    """该 op 的前 k 条**跨文件**引用 → ['11_1a.tob:0x5a1:<hex>', ...]。"""
    out, seen = [], set()
    for a in audit:
        if a[2] != op_dec:
            continue
        script = a[0][len("ota_"):]
        if script in seen:
            continue
        seen.add(script)
        out.append("%s.tob:%s:%s" % (script, a[1], a[8]))
        if len(out) >= k:
            break
    return out


def _counterexamples(audit, op_dec):
    """统一反例口径 = 记录数 − 「(prev,next) 恰等于该 op 最频 (prev,next) 对」的记录数。

    (prev,next) 按 `scene_id` 内相邻记录头 op 计（`START`/`END` 为场边界）。
    该口径**可复算**（见 `_prof_context.py`），用于给「邻接型判据」一个统一、可失败的量化反例数。
    """
    by = {}
    for a in audit:
        by.setdefault(a[0], []).append(a)
    pair = collections.Counter()
    n = 0
    for seq in by.values():
        for j, a in enumerate(seq):
            if a[2] != op_dec:
                continue
            n += 1
            p = seq[j - 1][2] if j > 0 else "START"
            x = seq[j + 1][2] if j + 1 < len(seq) else "END"
            pair[(p, x)] += 1
    if n == 0:
        return 0
    return n - pair.most_common(1)[0][1]


def names_bytes(audit) -> bytes:
    per_op = sorted(set(a[2] for a in audit))
    buf = ["\t".join(NAMES_HEADER)]
    for op in per_op:
        key = "0x%02x" % op
        if op in NAMED:
            name, category, conf, note = NAMED[op][0], "", "高", NAMED[op][3]
            if op in BOUNDARY_ONLY:
                category = "行边界标记（不产出主线行）"
            elif NAMED[op][2] in ("marker", "choice_marker"):
                category = "结构标记（邻接/共现量化）"
            else:
                category = "既有定名（载荷自证）"
            conf = CONF_OVERRIDE.get(key, conf)
        elif op in CAND:
            name, note, conf = CAND[op][0], CAND[op][1], "候选"
            category = "候选（结构角色，语义名不唯一 ⇒ 并列）"
        else:
            name, note, conf = "未证", "载荷不足以自证（判据尝试见 TOB0文法_说明 §4.2 / §十三）", "—"
            category = "—"
        cites = " | ".join(_citations(audit, op, 2))
        buf.append("\t".join(_clean(x) for x in
                             [key, name, category, cites, conf,
                              str(_counterexamples(audit, op)), note]))
    return ("\n".join(buf) + "\n").encode("utf-8")


def read_artifact_bytes(path):
    with open(path, "rb") as f:
        b = f.read()
    return b.replace(b"\r\n", b"\n")       # 行尾规范化（autocrlf 检出差异不参与判据）


def print_stats(st):
    w = sys.stdout.write
    w("\n================ ota TOB0 解析统计 ================\n")
    w("文件数            : %d\n" % st["files"])
    w("记录总数          : %d（op 值 %d 种）\n" % (st["records_total"], st["op_distinct"]))
    w("项流切分失败      : %d（逐条见 _stats.json.fails）\n" % len(st["fails"]))
    w("原文岛字节        : %d（记录之间的 SJIS 对话正文，非记录）\n" % st["island_bytes"])
    w("line_end 锚点数   : %d\n" % st["tail_anchors"])
    w("产出主线行数      : %d\n" % st["rows"])
    w("param_ok 分布     : %s\n" % st["param_ok"])
    w("conf 分布         : %s\n" % st["conf"])
    w("三类实参命中      : %s\n" % st["classes"])
    cat = st["families"]
    w("能定名的 op       : %s\n" % cat["named"])
    w("候选名 op         : %s\n" % cat.get("candidates", []))
    w("未证的 op         : %s\n" % cat["unproven"])
    w("op 直方图         : %s\n" % st["per_op"])


def main():
    ap = argparse.ArgumentParser(description="After Story TOB0 逐行演出解析器（ISSUE-20261008-09）")
    ap.add_argument("--check", action="store_true", help="严格只读幂等自检（不写任何文件）")
    ap.add_argument("--stats", action="store_true", help="只打印统计（不写盘）")
    ap.add_argument("--names", action="store_true", help="只打印 op 名表（不写盘）")
    ap.add_argument("--out", default=None, help="主线表落点（默认本目录 演出新源_ota.tsv）")
    ap.add_argument("--mutate", default=None,
                    help="变异自证：改坏 op 名表一处（如 0x22），配合 --check 必须 FAIL")
    a = ap.parse_args()
    if a.mutate:
        MUTATE.add(int(a.mutate, 0))

    files = sorted(f for f in os.listdir(TOB_DIR) if f.lower().endswith(".tob"))
    st = {"files": len(files)}
    led = SC = None
    if os.path.isfile(os.path.join(SC_TOOL_DIR, "_staging_common.py")):
        try:
            led, SC = load_ledger()
        except Exception as e:                              # noqa: BLE001
            sys.stdout.write("!! 资源总账不可用（%s）⇒ tgt 记原始令牌\n" % e)
    lseqmap, titles, lastseqmap, dup_idx = load_seq_maps()
    rows, audit = build_rows(led, SC, lseqmap, titles, lastseqmap, st)
    st["dup_seq_index"] = dup_idx
    st["rows"] = len(rows)
    named = sorted(k for k in NAMED if k not in BOUNDARY_ONLY)
    st["families"] = {
        "named": ["0x%02x=%s" % (k, NAMED[k][0]) for k in named],
        "candidates": ["0x%02x=%s" % (k, CAND[k][0]) for k in sorted(CAND)],
        "unproven": ["0x%02x" % k for k in sorted(
            int(k, 16) for k in st["per_op"]
            if int(k, 16) not in NAMED and int(k, 16) not in CAND)],
        "boundary_only": ["0x%02x=%s" % (k, NAMED[k][0]) for k in BOUNDARY_ONLY],
    }
    st["md5_records_audit"] = hashlib.md5(records_bytes(audit)).hexdigest()

    if a.names:
        sys.stdout.write(names_bytes(audit).decode("utf-8"))
        return

    if a.stats:
        print_stats(st)
        return

    payload = table_bytes(rows)
    rec_payload = records_bytes(audit)
    names_payload = names_bytes(audit)
    out = a.out or OUT_TABLE

    if a.check:
        for path, want, what in ((out, payload, "主线表"), (OUT_RECORDS, rec_payload, "审计档"),
                                 (OUT_NAMES, names_payload, "op名表"),
                                 (OUT_STATS, None, "_stats.json")):
            if want is None:
                if not os.path.isfile(path):
                    raise SystemExit("!! --check：缺产物 %s" % path)
                continue
            if not os.path.isfile(path):
                raise SystemExit("!! --check：缺产物 %s（先跑一次生成）" % path)
            got = read_artifact_bytes(path)
            if got != want:
                raise SystemExit("!! --check FAIL：%s 磁盘 %d 字节 ≠ 本轮重算 %d 字节（%s）"
                                 % (what, len(got), len(want), path))
        with io.open(OUT_STATS, encoding="utf-8") as f:
            disk_st = json.load(f)
        if disk_st.get("records_total") != st["records_total"]:
            raise SystemExit("!! --check FAIL：_stats.json records_total 不符")
        sys.stdout.write("--check ALL_PASS=True（主线表 %d 行 / 审计档 %d 行 / op名表 %d 行，逐字节相同）\n"
                         % (len(rows), len(audit), len(names_payload.splitlines()) - 1))
        return

    for path, data in ((out, payload), (OUT_RECORDS, rec_payload), (OUT_NAMES, names_payload)):
        with io.open(path, "wb") as f:                       # newline 无关：显式 LF 字节
            f.write(data.replace(b"\r\n", b"\n"))
        if read_artifact_bytes(path) != data:
            raise SystemExit("!! 落盘自证失败：%s" % path)
    with io.open(OUT_STATS, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True))
    print_stats(st)
    sys.stdout.write("\n产物：\n  %s（%d 行）\n  %s（%d 行）\n  %s（%d 行）\n  %s\n"
                     % (out, len(rows), OUT_RECORDS, len(audit),
                        OUT_NAMES, len(names_payload.splitlines()) - 1, OUT_STATS))


if __name__ == "__main__":
    main()
