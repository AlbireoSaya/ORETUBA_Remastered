# -*- coding: utf-8 -*-
r"""
`build_staging_sob0.py` · 逐行演出表生成器 —— **SOB0 系（`ot` 本篇 / `otp` 前奏诗）**（ISSUE-20261001-14）

产物（写本 checkout）
    `资源组\演出\演出_ot.tsv`、`资源组\演出\演出_otp.tsv`

原理（**源侧直证**，非推断）
    SOB0 的 `maps[4]`（字符串指针表）登记了**全部**「引用字符串的指令」——实测其 opcode
    高 12 位**恒为 `0x018`**（`TEXT_CMDS` 过滤不漏任何一条：`ot s01_02a` 1198/1198、
    `otp 02_01a` 92/92、`otp 02_02a` 1475/1475；见 `临时\probe\probe_opcodes.py`）。
    按字节码地址升序遍历即得该脚本的**完整执行序槽流**；每槽字符串按 `extract_sob0.py` 的
    `classify()` 分三档：`dialogue`（含 `$&`）／`ascii`（**演出命令串**）／`other`。
    非 `ascii` 槽的第 N 个 ↔ 该场景 `lines[].seq = N`（1-based）。

    ⚠️ 本生成器**自持 SOB0 扫描器**（不依赖 `语料\原文` 中间产物），故在任何 checkout 都可复跑；
    对 `ot` 另做 **G3** 与既有 `语料\原文\<script>.sob.jsonl` 的逐槽复核（证明扫描器保真）。

`seq` 语义（契约）：op 的 `seq` = **紧随其后第一个文本行的行号**；其后无文本行 ⇒ 末行行号
    （`evidence` 注 `after_last_line`）；在首行之前 ⇒ 1（注 `before_first_line`）。

分类口径
    `PIC\X`→`bg` ｜ `SE\X`→`se` ｜ `BGM\X`→`bgm` ｜ `MOVIE\X`→`movie`
    `SYS\RULE*`·`SYS\WIPE*`→`effect`（`arg1=rule:<编号>`）｜ 其它 `SYS\X`→`other`
    `CHR\X` 与**裸差分令牌**（命中 `Ledger.target('chr',…)`）→ `chr_add`（**同族首次引用**）／
    `chr_expr`（**同族后续引用**，`arg1`=差分后缀）；族别取**权威表** `ArtFamilies`
    （`美术\立绘差分索引.tsv` 的 `out_relpath→family`）。
    ⚠️ `chr_add`/`chr_expr` 的二分是**文档化启发式**（引用序推定），**不体现在 `confidence`**；
    `confidence` 描述的是 `(scene_id, seq, target)` 三元组的证据强度（本源＝字节码序直证 ⇒ `exact`）。
    其余有助记符形态但不属闭集的控制串 → `other`（`arg1`=原始串）。

丢弃（计数写进 `_index.json`）：空串槽 / 纯数字与带符号小数 / 分隔串（`_ $ [ ] ^` 及其复写）/
    `ScSkip`·`SsSkip` / `VOICE\*`（语音，已由 `lines[].audio` 承载）。

闸门（都能真失败）
    G1 源槽链接可解：`lines[].lineno`（ot）或 `lines[].index`（otp）中必有一个字段是**源槽号**——
       逐行满足「该槽非 ascii 且正文 == 本行 `jp`」，命中数须 == `line_count`（自动探测，不写死字段名）
    G2 源槽链接逐行成立（同上命中数；不成立则退回序数锚定并逐条登记）
    G3 扫描器保真（仅 `ot`）：扫出的槽流与 `语料\原文\<script>.sob.jsonl` 逐槽一致
    G4 逐场景集合守恒：`op=bg` ⊇ `assets[pic]`、`op=se` ⊇ `assets[se]`、
       `op=chr_*` ⊇ `assets[chr]`、`op=bgm`/`op=movie` 同理（该 kind 为空则跳过）
    G5 场景覆盖（`_staging_common.assert_scene_coverage`）
    G6 幂等（`--check`）

复跑
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_sob0.py"
    python -X utf8 "…/build_staging_sob0.py" --check
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _staging_common as SC   # noqa: E402

TEXT_CMDS = (0x01800000, 0x01700000)
CHECK = "--check" in sys.argv

SOB_PROJ = os.path.join(SC.DATA_ROOT, "工程", "我们没有翅膀")
OTP_PROJ = os.path.join(SC.DATA_ROOT, "工程", "我们没有翅膀 前奏诗")

SPECS = {
    "ot": dict(proj=SOB_PROJ, raw=os.path.join(SOB_PROJ, "语料", "原文")),
    "otp": dict(proj=OTP_PROJ, raw=None),
}

NUM_RE = re.compile(r"^[+-]?\d+(\.\d+)?$")
SEP_RE = re.compile(r"""^[_$\[\]^ "'\u2018\u2019\u201c\u201d]+$""")
SYSEFFECT_RE = re.compile(r"^(RULE|WIPE)", re.I)
TOKLIKE_RE = re.compile(r"^[A-Za-z]+_?\d+[A-Za-z]?$")


# ================================================================ SOB0 解析
def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def _read_nul(d, p):
    e = d.find(b"\x00", p)
    if e < 0:
        e = len(d)
    return d[p:e], e + 1


def classify(raw):
    """复刻 `工程\\我们没有翅膀\\工具\\extract_sob0.py:classify`（G3 会逐槽复核，故须一致）。"""
    if b"$&" in raw:
        head, body = raw.split(b"$&", 1)
        if body.endswith(b"$"):
            body = body[:-1]
        spk = ""
        if head.startswith(b"#"):
            h = head[1:]
            spk = h.split(b"\\", 1)[0].decode("cp932", "replace")
        return "dialogue", spk, body
    try:
        raw.decode("ascii")
        return "ascii", "", raw
    except UnicodeDecodeError:
        pass
    return "other", "", raw


def parse_sob0(d):
    """→ `(slots, info)`；`slots` = 有序 `dict(addr, kind, speaker, body)`（body 已 cp932 解码）。"""
    if d[:4] != b"SOB0":
        return None, {"err": "not SOB0"}
    table_end = _u32(d, 4) + 8
    off, maps = 8, []
    while off < table_end:
        n = _u32(d, off)
        off += 4
        m = {}
        for _ in range(n):
            m[_u32(d, off)] = _u32(d, off + 4)
            off += 8
        maps.append(m)
    if len(maps) < 5:
        return None, {"err": "maps<5 (%d)" % len(maps)}
    sstart, send = _u32(d, off), _u32(d, off + 4)
    header_end = off + 8
    code_end = sstart + header_end
    strmap = maps[4]

    slots = []
    for addr in range(0, max(0, code_end - header_end), 4):
        v = strmap.get(addr)
        if v is None or not (sstart <= v < send):
            continue
        cmd = _u32(d, header_end + addr)
        if (cmd & 0xFFF00000) not in TEXT_CMDS:
            continue
        p = v + header_end
        if p >= len(d):
            continue
        if d[p] == 0:
            p += 3
        sel = 0
        if p < len(d) and d[p] in (2, 3):
            sel = d[p] - 1
            p += 4
        raw, p = _read_nul(d, p)
        raws = [raw]
        for _ in range(sel):
            p += 2
            raw, p = _read_nul(d, p)
            raws.append(raw)
        for raw in raws:
            kind, spk, body = classify(raw)
            slots.append(dict(addr=addr, kind=kind, speaker=spk,
                              body=body.decode("cp932", "replace")))
    return slots, dict(maps=len(maps), strings=(sstart, send), header_end=header_end,
                       entries=len(strmap))


def load_sob(proj, script):
    """优先级：`解包\\SCRIPT`（原始 JP）→ `汉化\\SCRIPT_CN`（中文构建，仅结构等价）。"""
    for sub in (("解包", "SCRIPT"), ("汉化", "SCRIPT_CN")):
        p = os.path.join(proj, *sub, script + ".sob")
        if os.path.isfile(p):
            return open(p, "rb").read(), p
    return None, None


# ================================================================ 单槽 → op
def _norm(s):
    return re.sub(r"[\s\u3000]+", "", (s or "").rstrip("$"))


def _ev(script, idx, body, tag):
    e = "script=%s; SOB0 槽#%d kind=ascii %s" % (script, idx, body)
    return e + (" " + tag if tag else "")


def slot_to_row(ctx, i, slot):
    """一个 `ascii` 槽 → 一行记录（`None` = 丢弃，已计数）。"""
    sid, script, src = ctx["sid"], ctx["script"], ctx["src"]
    body = (slot["body"] or "").strip()
    if not body:
        ctx["drops"]["empty"] += 1
        return None

    kind, tok = SC.path_ref(body)
    if kind:
        # `path_ref` 已知 kind；`VOICE` 由 lines[].audio 承载 → 丢弃
        if kind == "voice":
            ctx["drops"]["voice"] += 1
            return None
        tgt = ctx["ledger"].target(kind, tok, src)
        seq, tag = ctx["smap"].seq_for(i)
        ev = _ev(script, i, body, tag)
        if tgt:
            if kind == "pic":
                # PIC\ 一律 pic（CSV/遮罩/特效层合并进 bg；见交付文档 §口径）
                return SC.row(sid, seq, "bg", tgt, "", "unknown", "", ev, "exact")
            if kind == "se":
                return SC.row(sid, seq, "se", tgt, "", "unknown", "", ev, "exact")
            if kind == "bgm":
                return SC.row(sid, seq, "bgm", tgt, "play", "unknown", "", ev, "exact")
            if kind == "movie":
                return SC.row(sid, seq, "movie", tgt, "play", "", "", ev, "exact")
            if kind == "sys":
                if SYSEFFECT_RE.match(tok):
                    return SC.row(sid, seq, "effect", tgt, "rule:%s" % tok, "", "", ev, "exact")
                return SC.row(sid, seq, "other", "", body, "系统覆盖层", "", ev, "exact")
            if kind == "chr":
                return chr_row(ctx, i, tok, tgt, ev)
        return SC.row(sid, seq, "other", "", body, "资源路径串未在总账命中", "",
                      ev + " 未在总账命中", "unknown")

    u = body.upper()
    if NUM_RE.match(u):
        ctx["drops"]["numeric"] += 1
        return None
    if SEP_RE.match(u):
        ctx["drops"]["separator"] += 1
        return None
    if u in ("SCSKIP", "SSSKIP"):
        ctx["drops"]["scskip"] += 1
        return None

    seq, tag = ctx["smap"].seq_for(i)
    ev = _ev(script, i, body, tag)
    tgt = ctx["ledger"].target("chr", u, src)
    if tgt:
        return chr_row(ctx, i, u, tgt, ev)
    if TOKLIKE_RE.match(u):
        return SC.row(sid, seq, "other", "", body, "形似差分令牌但未在总账命中", "",
                      ev + " 未在总账命中", "unknown")
    return SC.row(sid, seq, "other", "", body, "", "", ev, "exact")


def chr_row(ctx, i, tok, tgt, ev):
    """立绘行：同族首次引用 → `chr_add`；后续 → `chr_expr`（可机检的文档化启发式）。"""
    fam = ctx["fam"].family(tgt) or SC.family_of(tok) or "?"
    ctx["seen_fam"][fam] += 1
    n = ctx["seen_fam"][fam]
    seq, _ = ctx["smap"].seq_for(i)
    if n == 1:
        return SC.row(ctx["sid"], seq, "chr_add", tgt, "", "", "",
                      ev + " 族=%s 同族第1次引用" % fam, "exact")
    return SC.row(ctx["sid"], seq, "chr_expr", tgt, SC.suffix_of(tok), "", "",
                  ev + " 族=%s 同族第%d次引用（op 名由引用序推定）" % (fam, n), "exact")


def detect_source_index(lines, slots):
    """在 `lineno` / `index` 中自动探测**真正的源槽号字段**。

    判据（逐行、全量成立才算命中）：`slots[f_k]` 存在且**非 ascii**，且其正文（去尾部 `$` 与
    空白/U+3000）== 该行 `jp`。实测：`ot` 用 `lineno`（`s01_03b` 98/98、`s01_04n` 159/159），
    `otp` 用 `index`（`lineno` 在该源是「显示序数」而非源槽号）。
    不写死字段名，避免 `ot`/`otp` 两源的 schema 漂移；两者皆不成立时返回 `(None, None, 0)`。
    """
    best = (None, None, 0)
    for f in ("lineno", "index"):
        vals = [l.get(f) for l in lines]
        if any(not isinstance(v, int) for v in vals):
            continue
        if any(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)):
            continue
        if any(v < 0 or v >= len(slots) for v in vals):
            continue
        hit = sum(1 for l, v in zip(lines, vals)
                  if slots[v]["kind"] != "ascii"
                  and _norm(slots[v]["body"]) == _norm(l.get("jp")))
        if hit == len(lines):
            return f, vals, hit
        if hit > best[2]:
            best = (f, vals, hit)
    return best


# ================================================================ 逐源构建
def build_source(src):
    spec = SPECS[src]
    scenes = [json.loads(l) for l in
              io.open(os.path.join(SC.RES, "剧本", "scene_%s.jsonl" % src), encoding="utf-8")]
    ledger = SC.Ledger.load()
    fam = SC.ArtFamilies.load()

    rows = []
    drops = collections.Counter()
    diag = dict(scenes=0, text_slots=0, extra_nonascii=0, slot_link_hit=0,
                slot_link_total=0, g3_checked=0,
                slot_index_field=collections.Counter())
    problems = []

    for sc in scenes:
        diag["scenes"] += 1
        script, sid, lines = sc["script"], sc["scene_id"], sc["lines"]
        data, _path = load_sob(spec["proj"], script)
        if data is None:
            problems.append((sid, "缺源脚本 %s.sob" % script))
            rows.append(SC.skip_row(sid, script, "源脚本缺失，无逐行演出数据"))
            continue
        slots, info = parse_sob0(data)
        if slots is None:
            problems.append((sid, "非 SOB0：%s" % info))
            rows.append(SC.skip_row(sid, script, "源脚本非 SOB0（%s）" % info.get("err")))
            continue

        text_idx = [i for i, s in enumerate(slots) if s["kind"] != "ascii"]
        _extra = max(0, len(text_idx) - len(lines))
        diag["extra_nonascii"] += _extra
        if _extra:
            # 非 ascii 但**不是剧情行**的槽（实测为省略号条 `…………。` 与标签条 `ＤＴ－ＤＲＥＡＭ` 之类）
            drops["extra_nonascii_slot"] += _extra

        # 源槽链接：自动探测真源槽号字段（ot=lineno / otp=index）；不成立则退序数锚定并登记
        field, vals, hit = detect_source_index(lines, slots)
        diag["slot_link_hit"] += hit
        diag["slot_link_total"] += len(lines)
        diag["slot_index_field"][field or "<序数回退>"] += 1
        if hit == len(lines):
            smap_pairs = list(zip(vals, [l["seq"] for l in lines]))
        else:
            smap_pairs = [(i, lines[k]["seq"]) for k, i in enumerate(text_idx[:len(lines)])]
            problems.append((sid, "G1/G2 源槽链接命中 %d/%d（字段=%s，已退序数锚定）"
                             % (hit, len(lines), field)))

        rawp = os.path.join(spec["raw"], script + ".sob.jsonl") if spec["raw"] else None
        if rawp and os.path.isfile(rawp):
            diag["g3_checked"] += 1
            ref = [json.loads(l) for l in io.open(rawp, encoding="utf-8")]
            ok = len(ref) == len(slots) and all(
                r["kind"] == s["kind"]
                and (r["body"] or "").rstrip("$") == (s["body"] or "").rstrip("$")
                for r, s in zip(ref, slots))
            if not ok:
                problems.append((sid, "G3 与 语料\\原文 槽流不一致（ref %d / scan %d）"
                                 % (len(ref), len(slots))))
        diag["text_slots"] += len(text_idx)

        ctx = dict(sid=sid, script=script, src=src, ledger=ledger, fam=fam,
                   smap=SC.SeqMap(smap_pairs),
                   seen_fam=collections.Counter(), drops=drops)
        scene_rows = []
        for i, s in enumerate(slots):
            if s["kind"] != "ascii":
                continue
            r = slot_to_row(ctx, i, s)
            if r is not None:
                scene_rows.append(r)
        if not scene_rows:
            scene_rows.append(SC.skip_row(
                sid, script, "脚本无 PIC/SE/CHR 路径引用（ascii 槽 %d 个，可解析 0 个）"
                % sum(1 for x in slots if x["kind"] == "ascii")))
        rows.extend(scene_rows)
        problems.extend(_conservation(sid, sc, scene_rows))

    SC.assert_scene_coverage(rows, [s["scene_id"] for s in scenes], src)
    return rows, drops, diag, problems


def _conservation(sid, sc, scene_rows):
    """G4：本场各 kind 的 target 集合须覆盖 `assets[]` 对应 kind（该 kind 为空则跳过）。"""
    want = collections.defaultdict(set)
    for a in sc.get("assets", []):
        if a.get("kind") and a.get("out_relpath"):
            want[a["kind"]].add(a["out_relpath"])
    got = collections.defaultdict(set)
    for r in scene_rows:
        if r["op"] == "bg":
            got["pic"].add(r["target"])
        elif r["op"] == "se":
            got["se"].add(r["target"])
        elif r["op"] in ("bgm", "movie"):
            got[r["op"]].add(r["target"])
        elif r["op"] == "effect":
            got["sys"].add(r["target"])
        elif r["op"].startswith("chr_"):
            got["chr"].add(r["target"])
    return [(sid, kind, sorted(ws - got.get(kind, set()))[:3], len(ws - got.get(kind, set())))
            for kind, ws in want.items() if ws - got.get(kind, set())]


def main():
    for src in ("ot", "otp"):
        rows, drops, diag, problems = build_source(src)
        path = SC.tsv_path(src)
        body = "\t".join(SC.HEADER) + "\n" + "".join(
            "\t".join(str(r[c]) for c in SC.HEADER) + "\n" for r in rows)
        if CHECK:
            # 行尾规范化后比较：autocrlf 检出的盘面是 CRLF、本模块产出是 LF（见 交接说明 C12）
            if SC.read_artifact_text(path) != body:
                raise SystemExit("!! [%s] G6 幂等失败：重算结果与磁盘产物不同" % src)
            print("[%s] G6 幂等 PASS（行尾已规范化比较）" % src)
        else:
            SC.write_tsv(path, rows)
            print("[%s] 写入 %d 行 -> %s" % (src, len(rows), path))
        print("   op   :", dict(sorted(collections.Counter(r["op"] for r in rows).items())))
        print("   conf :", dict(sorted(collections.Counter(r["confidence"] for r in rows).items())))
        print("   drop :", dict(sorted(drops.items())))
        print("   diag :", diag)
        if problems:
            print("   !! 问题 %d 条：" % len(problems))
            for p in problems[:12]:
                print("      ", p)
        else:
            print("   G1/G2/G3/G4/G5 全绿（G4 逐场守恒 0 违约）")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
