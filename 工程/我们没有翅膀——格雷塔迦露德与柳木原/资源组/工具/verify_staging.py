# -*- coding: utf-8 -*-
r"""
`verify_staging.py` · 逐行演出表**独立机检**（ISSUE-20261001-14，只读、幂等、可复跑）

定位
    对六张 `资源组\演出\演出_<源>.tsv` 做机器可检验收，输出 `ALL_PASS`（照
    `verify_schema_enums.py` 的做法）。**刻意不 import 生成器的任何实现**：本文件的
    TSV 解析、枚举集合、总账读取、族别推导**全部自持一份**，故「生成器写错、校验器跟着错」
    不会同时发生；生成器与校验器若不一致，说明至少一方有缺陷，必须查明。

判据（对应任务书 §五 的可机检项）
    ① 外键守恒：非 `skip` 行 `scene_id` ∈ `scene_<源>.jsonl` 的场景集，且 `seq` ∈ 该场景
       `lines[].seq` 集合；`skip` 行 `seq` 必须为 0
    ② 素材存在：非空 `target` 必须能在 `krkr素材库\资源总账.json` 的 `out_relpath` 中查到，
       且该文件在盘上存在（`isfile`）
    ③ 角色名封闭：`chr_*` 行的 `target` 必须属于**本源 chr 条目集合**（⇒ 族别必在库内），
       且推导出的族代号 ∈ 已登记集合（`审计\立绘族矩阵.tsv` 的代号 ∪ `美术\立绘差分索引.tsv`
       的 family ∪ otv 侧 `st_<族>` 去前缀）；**不得出现剧本里没有的角色族**
    ④ 行数守恒/可解释：每场景要么 ≥1 条非 `skip` 行，要么恰好 1 条 `skip` 行；
       `skip` 行的 `arg1`/`evidence` 必须逐行给出原因（不得空白）
    ⑤ 枚举封闭：`op` ∈ 12 值闭集、`confidence` ∈ 3 值、列数恒 9、TAB 分隔、
       字段不以 `"` 包裹、无 CR、UTF-8 无 BOM
    ⑦ 集合守恒（**整源**）：`op=bg` 的 target 去重集合 ⊇ 该源 `assets[kind=pic]` 集合；
       `op=se` ⊇ `kind=se`；`op=bgm` ⊇ `kind=bgm`；`op=movie` ⊇ `kind=movie`；
       `op=chr_*` ⊇ `kind=chr`；`op=effect` ⊇ `kind=sys`
       （另附**逐场**同款检查作为更强反证，逐场结果单独统计）
    ⑥ 实机抽查对照：**不做**（需运行态，不属可机检项；由编程组按任务书 §五.⑥ 执行）

复跑
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_staging.py"
"""
from __future__ import annotations

import collections
import csv
import io
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                                     # 本 checkout 的资源组\（产物落点）
PRJ = os.path.dirname(RES)
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
# 只读输入树：`资源总账.json` / `立绘差分索引.tsv` / 素材库二进制均被 gitignore，只在共享数据树里
RES_DATA = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "资源组")

OUT_DIR = os.path.join(RES, "演出")
LEDGER = os.path.join(RES_DATA, "krkr素材库", "资源总账.json")
LIB_ROOT = os.path.join(RES_DATA, "krkr素材库")
ART_IDX = os.path.join(RES_DATA, "美术", "立绘差分索引.tsv")
FAM_MATRIX = os.path.join(RES_DATA, "审计", "立绘族矩阵.tsv")
SCENE_DIR = os.path.join(RES_DATA, "剧本")
SOURCES = ("ot", "ota", "otp", "otr", "otv", "np")

# ⑤ 枚举闭集（独立于生成器常量各写一份）
OPS = frozenset(("chr_add", "chr_remove", "chr_move", "chr_expr",
                 "bg", "se", "bgm", "movie", "wait", "effect", "other", "skip"))
CONF = frozenset(("exact", "inferred", "unknown"))
HEADER = ["scene_id", "seq", "op", "target", "arg1", "arg2", "arg3",
          "evidence", "confidence"]
NCOL = 9
# op → 该 op 的 target 所属 kind（⑦ 用）
OP_KIND = {"bg": "pic", "se": "se", "bgm": "bgm", "movie": "movie",
           "effect": "sys", "chr_add": "chr", "chr_expr": "chr",
           "chr_move": "chr", "chr_remove": "chr"}
# 立绘差分索引的哨兵族名（`cin_red` 三条记 `UNPARSED`）——不是族，判定时须滤掉
SENTINEL_FAMS = frozenset(("unparsed",))


def read_tsv(path):
    """自持解析：UTF-8 无 BOM、TAB、无引号包裹。→ `(header, rows, raw_bytes, line_ending)`

    **行尾口径**（交接说明 C12）：仓库版（blob）为 **LF**；`core.autocrlf=true` 的检出
    （如主工作树）盘面为 **CRLF**，字节数会比 LF 版恰好多出行数。故本校验器**两种都接受**，
    但**不接受裸 `CR`**（`CR` 后不接 `LF`）；解析前统一规范化为 LF。
    """
    raw = open(path, "rb").read()
    name = os.path.basename(path)
    if raw[:3] == b"\xef\xbb\xbf":
        raise SystemExit("!! %s 带 BOM" % name)
    bare = re.search(rb"\r(?!\n)", raw)
    if bare:
        raise SystemExit("!! %s 含裸 CR（非 CRLF 行尾）@byte %d" % (name, bare.start()))
    nl = "CRLF" if b"\r\n" in raw else "LF"
    txt = raw.decode("utf-8").replace("\r\n", "\n")
    lines = txt.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    head = lines[0].split("\t")
    rows = [dict(zip(head, ln.split("\t"))) for ln in lines[1:]]
    return head, rows, raw, nl


def load_scenes(src):
    p = os.path.join(SCENE_DIR, "scene_%s.jsonl" % src)
    out = {}
    for ln in io.open(p, encoding="utf-8"):
        o = json.loads(ln)
        out[o["scene_id"]] = o
    return out


def load_ledger():
    d = json.load(io.open(LEDGER, encoding="utf-8"))
    by_kind_src = collections.defaultdict(set)          # (kind,src) -> {out_relpath}
    allrel = set()
    for e in d["entries"]:
        if e.get("out_relpath"):
            allrel.add(e["out_relpath"])
            by_kind_src[(e.get("kind"), e.get("source"))].add(e["out_relpath"])
    return allrel, by_kind_src


def load_families():
    """已登记族代号：立绘族矩阵 ∪ 立绘差分索引 ∪ 各族的 `st_<族>` 变体（otv 用 `ST_` 前缀）。

    ⚠️ 哨兵值 `UNPARSED`（索引里 3 条 `cin_red`）**不算族名**，会被滤掉——`cin_red` 的族别
    由 `fam_from_name` 回退推为 `cin`（已登记），故过滤哨兵不影响判定。
    """
    fams = set()
    with io.open(FAM_MATRIX, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            v = (r.get("代号") or "").strip()
            if v:
                fams.add(v.lower())
    with io.open(ART_IDX, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            v = (r.get("family") or "").strip()
            if v:
                fams.add(v.lower())
    fams -= SENTINEL_FAMS
    for v in list(fams):
        fams.add("st_" + v)
    return fams


def load_art_fam():
    """**权威**「立绘件 → 族」：`美术\\立绘差分索引.tsv` 的 `out_relpath → family`。

    该表比令牌正则可靠：`blk2/red/red2` 归 `cin`，正则推不出。**覆盖 5 个源**
    （`ot 989 / ota 1264 / otp 591 / otr 353 / np 291`）；`otv`（253 件）不在表内，
    由 `fam_from_name` 的正则回退处理（`st_<族>` → 剥前缀）。
    哨兵值 `UNPARSED` 视为无值，交回退处理。
    """
    m = {}
    with io.open(ART_IDX, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            fam = (r.get("family") or "").lower()
            if r.get("out_relpath") and fam and fam not in SENTINEL_FAMS:
                m[r["out_relpath"]] = fam
    return m


def canon_family(fam, fams_reg):
    """族代号规范化：推导出的 `cin_blk` 之类（多段下划线）取**最长的已登记前缀段**。

    依据：`otv` 的令牌是 `st_cin_blk2`（`ST_CIN_BLK2`），其族在资源侧就是 `cin`；
    而 `cin_blk` 不是已登记族。逐段回退到第一个已登记前缀。
    """
    if not fam:
        return fam
    if fam in fams_reg:
        return fam
    parts = fam.split("_")
    for k in range(len(parts) - 1, 0, -1):
        cand = "_".join(parts[:k])
        if cand in fams_reg:
            return cand
    return parts[0] if parts[0] in fams_reg else fam


TOK_RE = re.compile(r"^st_([a-z]+(?:_[a-z]+)*)_?(\d+)([a-z]?)$", re.I)
TOK_RE2 = re.compile(r"^([a-z]+(?:_[a-z]+)*)_?(\d+)([a-z]?)$", re.I)


def fam_from_name(stem):
    """文件名 stem → 族代号（可选 `st_` 前缀）。

    级联：形A `st_mis01a`／`st_asu01a` → `mis`/`asu`；形B `ai_03f` → `ai`；
    形C `kaz01a` → `kaz`；**兜底**取首个下划线前的字母串（`cin_red`→`cin`、`cin_blk2`→`cin_blk`，
    后者再由 `canon_family` 回退到已登记前缀 `cin`）。
    """
    s = stem.lower()
    m = TOK_RE.match(s)
    if m:
        return m.group(1).lower()
    m = TOK_RE2.match(s)
    if m:
        return m.group(1).lower()
    m = re.match(r"^([a-z]+)", s)
    return m.group(1) if m else None


def lib_chr_families(by_kind_src):
    out = {}
    for (kind, src), rels in by_kind_src.items():
        if kind != "chr":
            continue
        out[src] = {fam_from_name(os.path.splitext(os.path.basename(r))[0]
                                  .replace(src + "_", "", 1)) for r in rels}
        out[src].discard(None)
    return out


def main():
    allrel, by_kind_src = load_ledger()
    fams_reg = load_families()
    art_fam = load_art_fam()
    lib_fams = lib_chr_families(by_kind_src)

    print("=" * 86)
    print("逐行演出表 独立机检（只读）  DATA_ROOT=%s" % DATA_ROOT)
    print("=" * 86)

    fails = []
    total = dict(rows=0, scenes=0)
    for src in SOURCES:
        p = os.path.join(OUT_DIR, "演出_%s.tsv" % src)
        if not os.path.isfile(p):
            fails.append((src, "缺产物 %s" % os.path.basename(p)))
            print("[%s] !! 缺产物" % src)
            continue
        head, rows, _raw, nl = read_tsv(p)
        scenes = load_scenes(src)
        c = collections.Counter()
        bad = collections.Counter()
        detail = collections.defaultdict(list)

        # ⑤ 表头与列数
        if head != HEADER:
            bad["⑤表头"] += 1
            detail["⑤表头"].append(head)
        for i, r in enumerate(rows, 2):
            if len(r) != NCOL:
                bad["⑤列数"] += 1
                detail["⑤列数"].append(i)
            if r.get("op") not in OPS:
                bad["⑤op"] += 1
                detail["⑤op"].append((i, r.get("op")))
            if r.get("confidence") not in CONF:
                bad["⑤confidence"] += 1
                detail["⑤confidence"].append((i, r.get("confidence")))
            for k, v in r.items():
                if isinstance(v, str) and v.startswith('"'):
                    bad["⑤引号"] += 1
                    detail["⑤引号"].append((i, k))

        # ① 外键守恒
        seqsets = {sid: {l["seq"] for l in o["lines"]} for sid, o in scenes.items()}
        per_scene = collections.defaultdict(lambda: [0, 0])
        for i, r in enumerate(rows, 2):
            sid, op, seq = r["scene_id"], r["op"], r["seq"]
            if not sid:
                # 契约 §3.2 规定 scene_id 不可空；空值会绕过 ①②③⑦，故必须自身即判违规
                bad["⑤空scene_id"] += 1
                detail["⑤空scene_id"].append(i)
                continue
            if op == "skip":
                per_scene[sid][1] += 1
                if seq != "0":
                    bad["①skip_seq"] += 1
                    detail["①skip_seq"].append((i, seq))
                if not (r.get("arg1") or "").strip() or not (r.get("evidence") or "").strip():
                    bad["④skip空原因"] += 1
                    detail["④skip空原因"].append(i)
                continue
            per_scene[sid][0] += 1
            if sid not in scenes:
                bad["①场景不在表"] += 1
                detail["①场景不在表"].append((i, sid))
                continue
            if not seq.isdigit() or int(seq) not in seqsets[sid]:
                bad["①seq越界"] += 1
                detail["①seq越界"].append((i, sid, seq))
            # ② 素材存在
            t = r.get("target") or ""
            if t:
                if t not in allrel:
                    bad["②不在总账"] += 1
                    detail["②不在总账"].append((i, t))
                elif not os.path.isfile(os.path.join(LIB_ROOT, t.replace("/", os.sep))):
                    bad["②盘上不存在"] += 1
                    detail["②盘上不存在"].append((i, t))
                # ③ chr_* 必须属本源 chr 条目；族别须已登记
                if op.startswith("chr_"):
                    if t not in by_kind_src.get(("chr", src), set()):
                        bad["③非本源chr"] += 1
                        detail["③非本源chr"].append((i, t))
                    fam = art_fam.get(t) or fam_from_name(
                        os.path.splitext(os.path.basename(t))[0].replace(src + "_", "", 1))
                    fam = canon_family(fam, fams_reg)
                    if not fam:
                        bad["③族不可推导"] += 1
                        detail["③族不可推导"].append((i, t))
                    elif fam not in fams_reg:
                        bad["③族未登记"] += 1
                        detail["③族未登记"].append((i, t, fam))
            c["op:" + op] += 1

        # ④ 逐场景覆盖
        for sid in scenes:
            nz, sk = per_scene.get(sid, [0, 0])
            if nz == 0 and sk != 1:
                bad["④覆盖"] += 1
                detail["④覆盖"].append((sid, nz, sk))
            if nz > 0 and sk > 0:
                bad["④覆盖"] += 1
                detail["④覆盖"].append((sid, "既非skip又有skip", nz, sk))
        for sid in per_scene:
            if sid not in scenes:
                bad["④表外场景"] += 1
                detail["④表外场景"].append(sid)

        # ⑦ 集合守恒（整源 + 逐场）。**豁免 `skip` 场景**——契约 §3.5.5/§八.2 允许「无逐行数据
        # 的场景只交 1 行 skip」；这类场景的 `assets[]` 天然无法覆盖，单列统计、不计失败。
        skip_scenes = {sid for sid, v in per_scene.items() if v[0] == 0 and v[1] >= 1}
        want = collections.defaultdict(set)
        skip_uncovered = 0
        for sid, o in scenes.items():
            for a in o.get("assets", []):
                if not (a.get("kind") and a.get("out_relpath")):
                    continue
                if sid in skip_scenes:
                    if a["kind"] in OP_KIND.values():
                        skip_uncovered += 1
                else:
                    want[a["kind"]].add(a["out_relpath"])
        got = collections.defaultdict(set)
        for r in rows:
            k = OP_KIND.get(r["op"])
            if k and r.get("target"):
                got[k].add(r["target"])
        for kind in sorted(want):
            miss = want[kind] - got.get(kind, set())
            if miss:
                bad["⑦整源缺失"] += len(miss)
                detail["⑦整源缺失"].append((kind, sorted(miss)[:4], len(miss)))
        # 逐场（同样豁免 skip 场景）
        scene_miss = 0
        gs = collections.defaultdict(lambda: collections.defaultdict(set))
        for r in rows:
            k = OP_KIND.get(r["op"])
            if k and r.get("target"):
                gs[r["scene_id"]][k].add(r["target"])
        for sid, o in scenes.items():
            if sid in skip_scenes:
                continue
            for a in o.get("assets", []):
                k, rel = a.get("kind"), a.get("out_relpath")
                if k and rel and rel not in gs.get(sid, {}).get(k, set()):
                    scene_miss += 1
                    if len(detail["⑦逐场缺失"]) < 20:
                        detail["⑦逐场缺失"].append((sid, k, rel))
        if scene_miss:
            bad["⑦逐场缺失"] += scene_miss

        total["rows"] += len(rows)
        total["scenes"] += len(scenes)
        print("[%s] 行 %d ｜ 场景 %d ｜ 行尾 %s ｜ op 分布 %s"
              % (src, len(rows), len(scenes), nl,
                 dict(sorted((k[3:], v) for k, v in c.items() if k.startswith("op:")))))
        if bad:
            print("   !! 违规：", dict(sorted(bad.items())))
            for k in sorted(bad):
                print("      %-14s %s" % (k, detail[k][:4]))
            fails.append((src, dict(bad)))
        else:
            print("   ①②③④⑤⑦ 全绿（逐场守恒缺失 %d）" % scene_miss)
        print("   skip 场景 %d ｜ bgm 行 %d ｜ chr_* 行 %d ｜ skip 场景未覆盖资产 %d（豁免，见 ⑦ 口径）"
              % (sum(1 for s in per_scene if per_scene[s][0] == 0 and per_scene[s][1]),
                 c["op:bgm"], sum(v for k, v in c.items() if k.startswith("op:chr")),
                 skip_uncovered))

    print()
    print("合计：六源 %d 行 / %d 场景" % (total["rows"], total["scenes"]))
    ok = not fails
    if fails:
        print("失败源：%s" % [f[0] for f in fails])
    print("⑥ 实机抽查对照：**本校验器不做**（需运行态；由编程组按任务书 §五.⑥ 执行）")
    print("ALL_PASS = %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
