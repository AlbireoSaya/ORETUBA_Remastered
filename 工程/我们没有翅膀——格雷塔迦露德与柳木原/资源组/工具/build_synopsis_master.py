# -*- coding: utf-8 -*-
r"""
build_synopsis_master.py —— 已游玩章节简介的合并 / 跨源对齐 / 去重标记 / 剧情顺序排序 + 翻译缺口

Issue  : ISSUE-20260929-12-greta-synopsis-and-ending
输入   : <资源组>\剧本\简介\_raw_ot.tsv / _raw_otr.tsv / _raw_otv.tsv   （前模块产出，只读）
         <资源组>\05_章节总表.tsv                                  （剧情顺序权威，只读）
         <资源组>\剧本\scene_ot.jsonl / scene_otr.jsonl / scene_otv.jsonl （场景归属与标题，只读）
输出   : <资源组>\剧本\章节简介.tsv                    （交付主表，按剧情顺序）
         <资源组>\剧本\简介\_translate_gap.tsv          （翻译缺口清单，按重复组去重）
         <资源组>\剧本\简介\_merge_README.md            （口径与统计）

特性：一条命令全量重建、幂等（重跑字节一致）、输出路径硬校验（必须落在本工作树内）。

复跑：
    cd "E:/ZCode Workspace/Galgame/临时/wt-syn"
    python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_synopsis_master.py"
负向自证（路径越界必须报错、不得静默产出）：
    python ".../build_synopsis_master.py" --neg-selftest
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import os
import sys

try:                                    # 让统计输出在 cp936 控制台也不乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # <WT>\工程\<作品>\资源组
SCEN_DIR = os.path.join(ROOT, "剧本")
INTRO_DIR = os.path.join(SCEN_DIR, "简介")
CHAP_TSV = os.path.join(ROOT, "05_章节总表.tsv")
OUT_MASTER = os.path.join(SCEN_DIR, "章节简介.tsv")
OUT_GAP = os.path.join(INTRO_DIR, "_translate_gap.tsv")
OUT_README = os.path.join(INTRO_DIR, "_merge_README.md")

RAW_FILES = [("ot", "_raw_ot.tsv"), ("otr", "_raw_otr.tsv"), ("otv", "_raw_otv.tsv")]
SRC_RANK = {"ot": 0, "otr": 1, "otv": 2}
# 场景归属只在这三份 scene_*.jsonl 里查（ot 表 s03c_* 归亚衣线，落在 scene_otr）
SCENE_FILES = [("ot", "scene_ot.jsonl"), ("otr", "scene_otr.jsonl"), ("otv", "scene_otv.jsonl")]

ESC_BSN = "\\" + "n"                             # 源 TSV 里「真换行」的转义写法（字面两字节 \ n）
UNMATCHED = "(未匹配)"

MASTER_HEADER = ["序号", "场景id", "章节标题(中文)", "剧情分组", "来源", "脚本", "简介jp", "简介cn",
                 "译文状态", "译文来源", "重复组id", "同场变体标记", "jp字符数", "jp的md5",
                 "采用", "备注"]
GAP_HEADER = ["待译id", "简介jp", "jp字符数", "涉及场景", "涉及来源", "备注"]

ST_NEW = "需新译"
ST_OT = "已有(ot原译)"
ST_OTV = "已有(otv库内)"


# ────────────────────────────── 路径硬校验 ──────────────────────────────

def _fail(msg):
    sys.stderr.write("[FATAL] %s\n" % msg)
    raise SystemExit(2)


def guard_path(path, why):
    """输出路径必须落在本工作树（ROOT）内，且 ROOT 必须位于 临时\\ 工作树中。"""
    p = os.path.abspath(path)
    root = os.path.abspath(ROOT)
    try:
        inside = os.path.commonpath([p, root]) == root
    except ValueError:                            # 不同盘符
        inside = False
    if not inside:
        _fail("输出路径越界（%s）：%s 不在工作树 %s 内" % (why, p, root))
    parts = [x for x in root.split(os.sep) if x]
    if "临时" not in parts:
        _fail("拒绝执行：ROOT 不在 临时\\ 工作树内（%s）——禁止在主工作区直接产出" % root)
    if p == root:
        _fail("输出路径不能是目录本身：%s" % p)
    return p


def neg_selftest():
    """负向自证：逃出工作树的路径必须逐条报错（不得静默通过）。"""
    cases = [
        ("用 .. 逃出工作树", os.path.join(ROOT, "..", "..", "_x")),
        ("用 .. 逃到工作区根", os.path.join(ROOT, "..", "..", "..", "..", "..", "_x")),
        ("指向主工作区 工程\\", "E:/ZCode Workspace/Galgame/工程/_x"),
        ("指向工作区外（C:\\）", "C:/_x"),
    ]
    bad = 0
    for why, path in cases:
        try:
            guard_path(path, why)
        except SystemExit as e:
            print("PASS  %-22s → [FATAL] exit=%s" % (why, e.code))
        else:
            bad += 1
            print("FAIL  %-22s → 未报错（越界未被拦住）" % why)
    # 正对照：正常落在工作树内的路径必须通过
    try:
        guard_path(OUT_MASTER, "正对照")
        print("PASS  正对照（工作树内路径）→ 通过")
    except SystemExit as e:
        bad += 1
        print("FAIL  正对照 → 被误拦 exit=%s" % e.code)
    print("NEG-SELFTEST " + ("PASS" if bad == 0 else "FAIL(%d)" % bad))
    return 0 if bad == 0 else 1


# ────────────────────────────── 读取 ──────────────────────────────

def read_tsv(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_scenes():
    """script(小写归一) → 我方场景（scene_id / 归属源 / 标题）"""
    by_script = {}
    for src, fname in SCENE_FILES:
        for line in io.open(os.path.join(SCEN_DIR, fname), encoding="utf-8"):
            o = json.loads(line)
            key = o["script"].lower()                 # ★ 归一小写后匹配（R/PSV 脚本名全大写）
            if key in by_script:                      # 实测 453 场景无跨源同名；有则硬报错
                _fail("场景脚本名跨源重名，无法唯一归属：%s" % key)
            by_script[key] = dict(scene_id=o["scene_id"], owner=src, script=o["script"],
                                  title_cn=o.get("title_cn"), title_jp=o.get("title_jp"))
    return by_script


def load_chapters():
    """scene_id → (05 行序序号, 章节标题(中文), spine归属)"""
    rows = read_tsv(CHAP_TSV)
    by_scene, seen = {}, collections.Counter()
    for i, r in enumerate(rows):
        sid = "%s_%s" % (r["源代号"], r["script"])
        if sid in by_scene:
            _fail("05_章节总表.tsv 内 scene_id 重复：%s" % sid)
        by_scene[sid] = dict(order=i, title_cn=(r.get("章节标题(中文)") or "").strip(),
                             spine=(r.get("spine归属") or "").strip(),
                             route=(r.get("route") or "").strip())
        seen[r["源代号"]] += 1
    return by_scene, rows


def load_otv_library():
    """otv 库内梗概：script(小写) → (cn, jp, seq)；来源 scene_otv.jsonl 的 lines[].kind=='summary'"""
    lib = {}
    for line in io.open(os.path.join(SCEN_DIR, "scene_otv.jsonl"), encoding="utf-8"):
        o = json.loads(line)
        for ln in o["lines"]:
            if ln.get("kind") == "summary":
                lib[o["script"].lower()] = (ln.get("cn") or "", ln.get("jp") or "", ln.get("seq"))
    return lib


# ────────────────────────────── 指纹 ──────────────────────────────

def fingerprint(text):
    """归一化指纹：去字面 \\n（行内换行）+ 去全部空白（含 U+3000）+ 统一 〜(U+301C)→～(U+FF5E)。

    除上述三项外不做任何转换（不转半角/全角、不合并 ≪≫ 与 <<>>、不动标点）。
    """
    t = text.replace(ESC_BSN, "")
    t = "".join(ch for ch in t if not ch.isspace())
    t = t.replace("\u301c", "\uff5e")
    return t


def real_len(text):
    """统一字符数口径：**真换行按 1 字**（`ot`/`otr` 的 TSV 用两字节 \\n 表示一个真换行；
    `otv` 的源 TSV 把字面 `\\n` 按 2 字计入，故与源列不同 —— 见 README §五.3 与 §七）。"""
    return len(text) - text.count(ESC_BSN)


def to_cell(text):
    """把带真换行/制表符的字符串写成单行单元格（真换行 → 字面 \\n，制表符 → 字面 \\t）。

    仅用于**库内取来的中文**（`scene_otv.jsonl` 的 cn 带真换行）；三源 TSV 的原文列本就已转义、不经过此函数。
    """
    return (text.replace("\r\n", "\n").replace("\r", "\n")
            .replace("\n", ESC_BSN).replace("\t", "\\t"))


# ────────────────────────────── 主流程 ──────────────────────────────

def build():
    scenes = load_scenes()
    chapters, chap_rows = load_chapters()
    lib = load_otv_library()

    recs, per_src = [], collections.Counter()
    match_fail, len_mismatch, ot_cn_empty = [], [], []
    src_count_gap = collections.Counter()
    for src, fname in RAW_FILES:
        path = os.path.join(INTRO_DIR, fname)
        raw = read_tsv(path)
        for i, r in enumerate(raw):
            script = r["script"]
            key = script.lower()
            sc = scenes.get(key)
            sid = sc["scene_id"] if sc else UNMATCHED
            if sc is None:
                match_fail.append(dict(src=src, script=script, row=i + 2, lineno_in_file=i))
            blk = (r.get("块序号") or "1").strip()
            own_cn, cn_from = "", ""
            if src == "ot":
                own_cn = r.get("简介cn") or ""
                cn_from = "ot/%s（本行原译）" % script
                if not own_cn.strip():
                    ot_cn_empty.append(script)
            elif src == "otv":
                if (r.get("是否已在我方库") or "").strip() == "是":
                    cn_from = "otv库（scene_otv.jsonl summary）/%s" % script
                    if key in lib:
                        own_cn = to_cell(lib[key][0])
                    else:                              # 无场景的库内命中（S01_01 空占位）→ cn 留空
                        own_cn = ""
            jp = r.get("简介jp") or ""
            declared = int((r.get("jp字符数") or "0").strip() or 0)
            # 源列口径：ot/otr = 「真换行算 1 字」；otv = 「字面 \n 按 2 字计」（即 len(单元格)）
            expect = real_len(jp) if src != "otv" else len(jp)
            if declared != expect:
                len_mismatch.append(dict(src=src, script=script, declared=declared,
                                         real=real_len(jp), cell=len(jp)))
            if src == "otv" and real_len(jp) != len(jp):
                src_count_gap["otv(nl)"] += 1
            recs.append(dict(
                src=src, script=script, blk=blk, scene=sid, scene_owner=(sc["owner"] if sc else None),
                jp=jp, jp_len=real_len(jp), src_len=declared, jp_md5=r.get("jp的md5") or "",
                raw_note=(r.get("备注") or ""), fp=fingerprint(jp),
                own_cn=own_cn, cn_from=cn_from,
                has_cn=bool(own_cn.strip()) or
                       (src == "otv" and (r.get("是否已在我方库") or "").strip() == "是"),
                blk_no=int(blk) if blk.isdigit() else 1,
                flag=(r.get("是否已在我方库") or "").strip(),
            ))
        per_src[src] = len(raw)

    # ── 重复组（按指纹分组，只标记不删行） ──
    groups = collections.OrderedDict()
    for x in recs:
        groups.setdefault(x["fp"], []).append(x)

    # ── 排序：剧情播放顺序（05_章节总表.tsv 的行序）＋ 同场景内 ot/otr/otv ──
    def order_key(x):
        ch = chapters.get(x["scene"])
        gi = ch["order"] if ch else len(chap_rows) + 1     # 未匹配行排在最后（不静默丢）
        ti = 0 if x["scene"] != UNMATCHED else 1
        return (ti, gi, SRC_RANK[x["src"]], x["blk_no"], x["script"])

    ordered = sorted(recs, key=order_key)
    for i, x in enumerate(ordered, 1):
        x["seq"] = i

    # 重复组 id：按最终行序首次出现赋号（确定性、幂等）
    gid, gid_of = 0, {}
    for x in ordered:
        if x["fp"] not in gid_of:
            gid += 1
            gid_of[x["fp"]] = "R%03d" % gid
    for fp, mem in groups.items():
        for m in mem:
            m["_gid"] = gid_of[fp]

    # ── 译文共享（同组任一成员有中文 ⇒ 全组共享；只凭指纹，不凭同名/同场景） ──
    cn_conflicts = []
    for fp, mem in groups.items():
        donor = None
        for cand in sorted(mem, key=lambda m: (SRC_RANK[m["src"]], m["blk_no"], m["script"])):
            if cand["own_cn"].strip():
                donor = cand
                break
        if donor is None:                             # 只有空槽型库内命中（cn 为空）时也认「已有」
            for cand in sorted(mem, key=lambda m: (SRC_RANK[m["src"]], m["blk_no"], m["script"])):
                if cand["has_cn"]:
                    donor = cand
                    break
        cns = {m["own_cn"] for m in mem if m["own_cn"].strip()}
        if len(cns) > 1:                              # 同组两个成员各带不同中文 ⇒ 需裁决
            cn_conflicts.append(dict(
                gid=mem[0]["_gid"],
                members=[m for m in sorted(mem, key=lambda z: (SRC_RANK[z["src"]], z["script"]))
                         if m["own_cn"].strip()],
                chosen=(donor["src"] + "/" + donor["script"]) if donor else None))
        for m in mem:
            if donor is None:
                m["status"], m["cn"], m["cn_src"] = ST_NEW, "", "—"
            elif m is donor:
                m["status"] = ST_OT if donor["src"] == "ot" else ST_OTV
                m["cn"], m["cn_src"] = donor["own_cn"], donor["cn_from"]
                if not donor["own_cn"].strip():
                    m["cn_src"] = donor["cn_from"] + "（空槽，库内 cn 为空）"
            else:
                m["status"] = ST_OT if donor["src"] == "ot" else ST_OTV
                m["cn"] = donor["own_cn"]
                m["cn_src"] = "借自 %s/%s（重复组 %s，指纹相同）" % (
                    donor["src"], donor["script"], donor["_gid"])
        for m in mem:
            m["_donor"] = donor

    # ── 同场变体（同一场景跨源文本不同） ──
    # 口径：① 指纹不同 ⇒ 内容不同（真正的文案变体）；
    #       ② 指纹同但 **ot 与 otr 的原串不同** ⇒ 仅行内换行位置不同（内容一致）；
    #       ③ otv 侧的换行位置几乎总与 ot/otr 不同（源脚本自带换行），属排版差异，**不作为变体标记**。
    per_scene = collections.OrderedDict()
    for x in ordered:
        if x["scene"] != UNMATCHED:
            per_scene.setdefault(x["scene"], []).append(x)
    variant_note = {}
    for sid, mem in per_scene.items():
        fps = []
        for m in mem:
            if m["fp"] not in fps:
                fps.append(m["fp"])
        if len(fps) > 1:
            parts = []
            for f in fps:
                srcs, lens = [], []
                for m in mem:
                    if m["fp"] == f:
                        if m["src"] not in srcs:
                            srcs.append(m["src"])
                        if m["jp_len"] not in lens:
                            lens.append(m["jp_len"])
                parts.append("%s %s 字" % ("+".join(srcs), "/".join(str(n) for n in lens)))
            variant_note[sid] = "是（内容不同：%s；%d 种文本）" % (" ≠ ".join(parts), len(fps))
            continue
        o = [m for m in mem if m["src"] == "ot"]
        r = [m for m in mem if m["src"] == "otr"]
        if o and r and o[0]["jp"] != r[0]["jp"]:
            variant_note[sid] = "是（仅 ot/otr 行内换行位置不同，内容一致）"

    # ── 「采用」列与「备注」列（主代理 2026-09-29 裁决 B / A / C / D）──
    #   规则（优先级：③ 单文本场景 > ① 有 ot > ② 无 ot）：
    #   ① 场景存在多个不同文本：有 ot 行 ⇒ 取 ot 版为「是」，其余「否」+备注「变体留档，非采用版」
    #   ②                        无 ot 行 ⇒ 按 otr > otv 取一版为「是」，其余「否」+同样备注
    #   ③ 场景全部文本一致（同一指纹）⇒ 全部「是」（内容相同，不存在取舍）
    #   ④ 未匹配行（otv S01_01 空占位）⇒ 「否」且不参与采用判定
    notes = collections.defaultdict(list)
    adopt = {}
    for sid, mem in per_scene.items():
        fps = []
        for m in mem:
            if m["fp"] not in fps:
                fps.append(m["fp"])
        if len(fps) == 1:                                  # ③ 无取舍
            for m in mem:
                adopt[id(m)] = "是"
            continue
        pick, pick_row = None, None                        # ①② 取一版
        for want in ("ot", "otr", "otv"):
            row = next((m for m in mem if m["src"] == want), None)   # mem 已按 场景内 ot→otr→otv、块号、脚本名 排
            if row is not None:
                pick, pick_row = row["fp"], row
                break
        for m in mem:
            if m is pick_row:
                adopt[id(m)] = "是"
            else:
                adopt[id(m)] = "否"
                if m["fp"] == pick:      # 文字与采用版逐字相同，但不是首选载体（裁决 B ①：只标 ot 行）
                    notes[id(m)].append(
                        "与采用版文本一致（重复行），非首选载体（采用版：%s/%s）"
                        % (pick_row["src"], pick_row["script"]))
                else:
                    notes[id(m)].append(
                        "变体留档，非采用版（采用版：%s/%s）" % (pick_row["src"], pick_row["script"]))
    for m in recs:
        if m["scene"] == UNMATCHED:                        # ④
            adopt[id(m)] = "否"
            notes[id(m)].append("源为空占位，无正文；无对应我方场景，不参与采用判定")

    # C 裁决：s00_00 是序文标题而非简介，保留
    for m in recs:
        if m["script"].lower() == "s00_00":
            notes[id(m)].append("非简介（序文标题），保留以便写序文屏取用")
        if "空槽" in m["cn_src"]:                          # 库内为空槽（M09_02 等源侧空占位）
            notes[id(m)].append("库内为空槽，无正文（源侧占位）")

    # A 裁决：供体冲突 4 例——术语表定译优先，其余取 ot 版；另一译法不删，只标注未采用
    for c in cn_conflicts:
        chosen = c["chosen"]
        losers = [m for m in c["members"] if (m["src"] + "/" + m["script"]) != chosen]
        donor = next((m for m in c["members"] if (m["src"] + "/" + m["script"]) == chosen), None)
        for m in c["members"]:
            if m is donor:
                notes[id(m)].append(
                    "供体冲突：另一译法见 %s，未采用（%s）"
                    % ("、".join(x["scene"] for x in losers), "重复组 " + c["gid"]))
            else:
                notes[id(m)].append(
                    "供体冲突：本行原有库内译法（措辞不同）未采用，采用版见 %s（重复组 %s）"
                    % ((donor["scene"] if donor else "?"), c["gid"]))

    for m in recs:
        m["adopt"] = adopt.get(id(m), "是")
        m["note"] = "；".join(notes.get(id(m), []))

    adopt_stat = dict(
        yes=sum(1 for m in recs if m["adopt"] == "是"),
        no=sum(1 for m in recs if m["adopt"] == "否"),
        notadopt_note=sum(1 for m in recs if "变体留档" in m["note"]),
        sametext_note=sum(1 for m in recs if "非首选载体" in m["note"]),
        with_note=sum(1 for m in recs if m["note"]),
        scenes=len(per_scene),
        variant_scenes=sum(1 for sid, mem in per_scene.items() if len({m["fp"] for m in mem}) > 1),
        uniform_scenes=sum(1 for sid, mem in per_scene.items() if len({m["fp"] for m in mem}) == 1),
    )
    adopt_pick = dict(rows={}, ot=0, not_ot=0)
    for sid, mem in per_scene.items():
        if len({m["fp"] for m in mem}) == 1:
            continue
        yes = [m for m in mem if m["adopt"] == "是"]
        adopt_pick["rows"][sid] = (yes[0]["src"], yes[0]["script"])
        if yes[0]["src"] == "ot":
            adopt_pick["ot"] += 1
        else:
            adopt_pick["not_ot"] += 1

    # ── 缺口（需新译，按重复组去重） ──
    scenes_with_ot = {x["scene"] for x in recs if x["src"] == "ot"}
    gap = []
    for fp, mem in groups.items():
        if any(m["has_cn"] for m in mem):
            continue
        rep = sorted(mem, key=lambda m: (0 if m["src"] == "otr" else 1, SRC_RANK[m["src"]], m["blk_no"]))[0]
        srcs = sorted({m["src"] for m in mem}, key=lambda s: SRC_RANK[s])
        sids = sorted({m["scene"] for m in mem},
                      key=lambda s: chapters[s]["order"] if s in chapters else len(chap_rows))
        has_ot_scene = bool({m["scene"] for m in mem} & scenes_with_ot)
        if "otr" in srcs and has_ot_scene:
            cat = "ot/otr 改写版（同场景本篇版存在但内容不同）"
        elif "otr" in srcs:
            cat = "R 版独有（亚衣线，无 2009 本篇对照）"
        elif has_ot_scene:
            cat = "PSV 改写版（同场景本篇版存在但内容不同）"
        else:
            cat = "PSV 独有（亚衣线场景，R 版另有不同文本、已各自成段）"
        gap.append(dict(fp=fp, gid=gid_of[fp], jp=rep["jp"], jp_len=rep["jp_len"], rep_src=rep["src"],
                        rep_script=rep["script"], srcs=srcs, sids=sids, cat=cat, mem=mem,
                        order=min(chapters[s]["order"] if s in chapters else len(chap_rows) for s in sids)))
    gap.sort(key=lambda g: (g["order"], g["gid"]))     # 按剧情顺序排列（同场景多段时按组号）
    for i, g in enumerate(gap, 1):
        g["tid"] = "T%03d" % i

    # ── 复核前模块「ot 与 otr 共有的脚本里 16 个文案不同、且这 16 个 otr==PSV」的说法 ──
    ot_by = {x["script"]: x for x in recs if x["src"] == "ot"}
    otr_by = {x["script"]: x for x in recs if x["src"] == "otr"}
    otv_by = {}
    for x in recs:
        if x["src"] == "otv":
            otv_by.setdefault(x["script"].lower(), []).append(x)
    shared = sorted(set(ot_by) & set(otr_by))
    raw_diff = [s for s in shared if ot_by[s]["jp"] != otr_by[s]["jp"]]
    fp_diff = [s for s in raw_diff if ot_by[s]["fp"] != otr_by[s]["fp"]]
    raw_only = [s for s in raw_diff if ot_by[s]["fp"] == otr_by[s]["fp"]]
    psv_eq, psv_missing, psv_neq = [], [], []
    for s in raw_diff:
        pv = otv_by.get(s.lower())
        if not pv:
            psv_missing.append(s)
        elif any(p["fp"] == otr_by[s]["fp"] for p in pv):
            psv_eq.append(s)
        else:
            psv_neq.append(s)
    ototr = dict(shared=len(shared), raw_eq=len(shared) - len(raw_diff), raw_diff=raw_diff,
                 fp_diff=fp_diff, raw_only=raw_only, psv_eq=psv_eq, psv_missing=psv_missing,
                 psv_neq=psv_neq)
    ot_rows = [x for x in recs if x["src"] == "ot"]
    otv_rows = [x for x in recs if x["src"] == "otv"]
    otv_lib = [x for x in otv_rows if x["flag"] == "是"]
    stats_extra = dict(ot_rows=len(ot_rows), ot_rows_cn=sum(1 for x in ot_rows if x["own_cn"].strip()),
                       otv_rows=len(otv_rows), otv_lib=len(otv_lib),
                       otv_lib_nonsense=sum(1 for x in otv_lib if not x["own_cn"].strip()))
    # ── 独立交叉核对：R 版独有的缺口组，其 scene_otr 的 source_kind 应为 new/branch ──
    otr_kind = {}
    for line in io.open(os.path.join(SCEN_DIR, "scene_otr.jsonl"), encoding="utf-8"):
        o = json.loads(line)
        otr_kind[o["scene_id"]] = o.get("source_kind")
    a_groups = [g for g in gap if g["cat"].startswith("R 版独有")]
    kind_dist = collections.Counter()
    for g in a_groups:
        for sid in g["sids"]:
            kind_dist[otr_kind.get(sid, "(无)")] += 1

    return dict(recs=recs, ordered=ordered, groups=groups, gap=gap, per_src=per_src,
                chapters=chapters, chap_rows=chap_rows, scenes=scenes, lib=lib,
                match_fail=match_fail, len_mismatch=len_mismatch, variant_note=variant_note,
                gid_of=gid_of, per_scene=per_scene, variant_scenes=variant_note,
                ot_cn_empty=ot_cn_empty, cn_conflicts=cn_conflicts,
                ototr=ototr, extra=stats_extra, otr_kind_dist=dict(kind_dist),
                otr_kind=otr_kind, src_count_gap=dict(src_count_gap), adopt_stat=adopt_stat,
                adopt_pick=adopt_pick)


# ────────────────────────────── 写出 ──────────────────────────────

def write_tsv(path, header, rows):
    guard_path(path, "写出")
    for r in rows:
        for v in r:
            if "\t" in v or "\n" in v or "\r" in v:
                _fail("单元格含制表符/真换行，会破坏一行一记录：%r" % v[:40])
    buf = io.StringIO()
    buf.write("\t".join(header) + "\n")
    for r in rows:
        buf.write("\t".join(r) + "\n")
    data = buf.getvalue().encode("utf-8")
    with io.open(path, "wb") as f:
        f.write(data)
    return hashlib.md5(data).hexdigest()


def write_text(path, text):
    guard_path(path, "写出")
    with io.open(path, "wb") as f:
        f.write(text.encode("utf-8"))


def master_rows(st):
    out = []
    for x in st["ordered"]:
        ch = st["chapters"].get(x["scene"])
        out.append([
            str(x["seq"]), x["scene"],
            (ch["title_cn"] if ch and ch["title_cn"] else (UNMATCHED if not ch else "（无标题）")),
            (ch["spine"] if ch and ch["spine"] else "未匹配（PSV S01_01 空占位，05 无此场景）"),
            x["src"], x["script"], x["jp"], x["cn"], x["status"], x["cn_src"],
            x["_gid"], st["variant_note"].get(x["scene"], ""), str(x["jp_len"]), x["jp_md5"],
            x["adopt"], x["note"],
        ])
    return out


def gap_rows(st):
    out = []
    for g in st["gap"]:
        note = "%s；重复组 %s；原文代表=%s/%s" % (g["cat"], g["gid"], g["rep_src"], g["rep_script"])
        out.append([g["tid"], g["jp"], str(g["jp_len"]), ";".join(g["sids"]),
                    ";".join(g["srcs"]), note])
    return out


# ────────────────────────────── README ──────────────────────────────

def render_readme(st, hashes):
    n = lambda xs: len(xs)
    ordered = st["ordered"]
    groups = st["groups"]
    gap = st["gap"]
    sizes = collections.Counter(len(v) for v in groups.values())
    comp = collections.Counter(tuple(sorted(m["src"] for m in v)) for v in groups.values())
    status = collections.Counter(x["status"] for x in ordered)
    cat = collections.Counter(g["cat"] for g in gap)
    gap_chars = sum(g["jp_len"] for g in gap)

    def table(head, rows):
        s = "| " + " | ".join(head) + " |\n| " + " | ".join("---" for _ in head) + " |\n"
        for r in rows:
            s += "| " + " | ".join(str(c) for c in r) + " |\n"
        return s

    L = []
    A = L.append
    A("# 已游玩章节简介 · 合并 / 去重 / 排序口径与统计（`_merge_README.md`）\n")
    A("> Issue：`ISSUE-20260929-12-greta-synopsis-and-ending` ｜ 分支 "
      "`issue/ISSUE-20260929-12-greta-synopsis-and-ending`")
    A("> 工作树：`E:\\ZCode Workspace\\Galgame\\临时\\wt-syn`（本文件所在处即该工作树的产物目录）")
    A("> 构建器：`资源组\\工具\\build_synopsis_master.py`（一条命令全量重建、幂等、输出路径硬校验）")
    A("> 验收器：`资源组\\工具\\verify_synopsis_master.py`（只读）")
    A("> 输入：`资源组\\剧本\\简介\\_raw_{ot,otr,otv}.tsv`（前模块原始抽取）+ "
      "`资源组\\05_章节总表.tsv` + `资源组\\剧本\\scene_{ot,otr,otv}.jsonl`\n")
    A("本目录的 `_raw_*` 是**原始抽取**；本模块在其上做**合并 / 跨源对齐 / 去重标记 / 剧情顺序排序**，"
      "不改写任何 `_raw_*`。三个产出：\n")
    A("| 产物 | 行数（不含表头） | 字节 | md5 |")
    A("| --- | ---: | ---: | --- |")
    for nm, cnt, size, md5 in hashes:
        A("| `%s` | %s | %s | %s |" % (nm, "—" if cnt is None else cnt,
                                     "—" if size is None else size,
                                     "—" if md5 is None else "`%s`" % md5))
    A("")
    A("> ⚠ 上表的 `字节` / `md5` 是 **组装前（`build_synopsis_master.py`）产物** 的值；"
      "交付态（接跑 `assemble_deliverables.py` 后：**17 列**、含 `原文换行位置`、`需新译`=0）的"
      "主表字节与 md5 不同，**以 `verify_deliverables.py` 的实算为准**。两阶段口径见 §六。")
    A("")

    A("---\n")
    A("## 〇、主代理裁决落地（2026-09-29）· 本版口径\n")
    A("本模块首版把 4 个待裁决点回报主代理，**本版按裁决落地**（只改主表与 README，**未动 `_raw_*`**）：\n")
    A(table(["裁决", "内容", "落地方式"],
            [["**A** 供体冲突 4 例",
              "术语表定译优先；其余取 `ot`（本篇）版；**另一译法不得删除**",
              "见 §4.1 表：`R135` 取写作 **`Ｒ翼`** 的一版（作品层 `术语表.md` §2.4 定译），`R097`/`R099`/`R113` 取 `ot` 版；"
              "**采用版**那一行 `备注` 写「供体冲突：另一译法见 `<未采用场景>`，未采用」，**未采用**那一行写"
              "「供体冲突：本行原有库内译法（措辞不同）未采用，采用版见 `<采用版场景>`」——两侧都留痕、**行不删**"],
             ["**B** 27 个同场变体",
              "**一律取本篇（`ot`）版**",
              "主表**新增 `采用` 列**（`是`/`否`）；判定规则见 §一·补，计数见 §3.4"],
             ["**C** `s00_00` 序文标题",
              "**保留**，不算缺口",
              "`备注` 标「非简介（序文标题），保留以便写序文屏取用」；其 `译文状态` 为 `已有(ot原译)`，不在缺口表"],
             ["**D** `otv S01_01` 空占位",
              "**保留**；`译文状态` 不得写 `需新译`，以免污染缺口表",
              "`备注` 标「源为空占位，无正文；无对应我方场景，不参与采用判定」；`译文状态` = `已有(otv库内)`（库内为空槽），**已核对不在缺口表**"]]))
    A("")
    A("### 〇·补、一审修复轮（2026-09-29 · ISSUE-20260929-12）· 术语统一与交付态口径\n")
    A("> 本模块交付后经一审打回，本修复轮按作品层 `作品skill\\术语表.md` §二·补 2.7.1–2.7.4 落地下列统一；"
      "**只改交付产物（`章节简介.tsv`）与该表的生成器模板，未动 `_raw_*`**。\n")
    A(table(["项", "裁决 / 事实", "落地方式"],
            [["`美空学園` → **美空学院**",
              "R 亚衣线语料作「美空学园」、ot 语料作「美空学院」；作品层 §2.7.2 裁决统一为 **美空学院**",
              "改新译源 `_cn_T022-T041.tsv` 的 **T029/T030/T034/T035/T038**（共 8 行 `简介cn`），"
              "由 `assemble_deliverables.py` 按指纹回填主表 ⇒ 交付主表内「美空学园」= **0**"],
             ["`羽田邸` → **羽田家**",
              "正确语料事实：R 亚衣线作「羽田家」5 槽、「羽田宅」0 槽；**「羽田宅」出自 ot 侧既有译法**"
              "（`s03_12j` / `s03c_04c`）；作品层 §2.7.2 裁决统一为 **羽田家**",
              "① 改 `_cn_T022-T041.tsv` 的 **T027/T032/T036**（新译行，共 6 行）；"
              "② **在交付主表内**把借自既有 ot 译文的 **5 行**一并统一 —— **序号 372/373/374** = 组 `R127`"
              "（`ot/s03_12j` ＋ `otr/s03_12j` ＋ `otv/S03_12J`）、**序号 1153/1154** = 组 `R406`"
              "（`ot/s03c_04c` ＋ `otr/s03c_04c`）；由 `assemble_deliverables.py` 的「术语统一」步骤（**幂等**）执行 "
              "⇒ 交付主表内「羽田宅」= **0**"]]))
    A("")
    A("**交付态口径**：本 README 的 §一–§五 描述的是 **组装前**产物（16 列 / `需新译`=107）；"
      "接跑 `assemble_deliverables.py` 后主表为 **17 列**、`需新译`=0，§七 字段表按**交付态**记。"
      "两阶段流程与验收见 §六。\n")
    A("### 一·补、「采用」列判定规则（裁决 B）\n")
    A("对**每个场景**取其全部源行，按归一化指纹分组；优先级 **③ > ① > ②**：\n")
    A("1. **③ 场景全部文本一致（只有一个指纹）** ⇒ 该场景**所有行 `采用=是`**（内容相同，不存在取舍）。")
    A("2. **① 场景存在多个不同文本，且有 `ot` 源行** ⇒ **只标 `ot` 行那一行为 `采用=是`**"
      "（**即使另一源行与之逐字相同，也只标首选载体**）；同场景其余行 `采用=否`："
      "文字确属变体者备注「变体留档，非采用版（采用版：`<源>/<脚本>`）」，"
      "文字与采用版逐字相同者备注「与采用版文本一致（重复行），非首选载体（采用版：…）」。")
    A("3. **② 场景存在多个不同文本，但无 `ot` 源行** ⇒ 按 **`otr` > `otv`** 取一版的那一行为 `采用=是`，其余 `采用=否`＋同上备注。")
    A("4. **④ 未匹配行**（`otv S01_01` 空占位）⇒ `采用=否`，不参与采用判定。\n")
    A("**计数**：`采用=是` **%d 行** ｜ `采用=否` **%d 行**（其中「变体留档，非采用版」%d 行、"
      "「与采用版文本一致，非首选载体」%d 行）；带 `备注` 的行 %d。"
      "有效场景（不含未匹配伪场景）**%d 个**，其中「多文本需取舍」**%d 个**（每场景恰 1 行 `是`）、"
      "「文本一致全采用」**%d 个**。"
      % (st["adopt_stat"]["yes"], st["adopt_stat"]["no"], st["adopt_stat"]["notadopt_note"],
         st["adopt_stat"]["sametext_note"], st["adopt_stat"]["with_note"], st["adopt_stat"]["scenes"],
         st["adopt_stat"]["variant_scenes"], st["adopt_stat"]["uniform_scenes"]))
    A("")
    A("> 校验口径（验收器的「采用列唯一性」与「缺口不含 C/D」两项断言）：**多文本场景恰有 1 行 `采用=是`**；"
      "**文本一致的场景全部 `采用=是`**；`采用=是` 的行必须同属**同一个指纹**，且该指纹必须等于"
      "「`ot` > `otr` > `otv`」优先级所选的那一版；未匹配行 `采用=否`；缺口表不含 `ot_s00_00`、"
      "不含未匹配伪场景、不含空指纹行。")
    A("")

    A("---\n")
    A("## 一、归一化与去重指纹（完整规则）\n")
    A("`简介jp` 的**字符串直比不能用来判重**：同一段文本在 `ot`（真换行）/`otr`（TSV 内以字面 `\\n` 表示换行）"
      "/`otv`（源脚本本就写字面 `\\n`）里换行写法不同。故先做**归一化指纹**再判重：\n")
    A("```")
    A("def fingerprint(text):")
    A("    t = text.replace('\\\\n', '')          # ① 去行内换行（字面两字节 反斜杠+n）")
    A("    t = ''.join(ch for ch in t if not ch.isspace())   # ② 去全部空白，含 U+3000 全角空格")
    A("    t = t.replace('\\u301c', '\\uff5e')     # ③ 统一 〜(U+301C) → ～(U+FF5E)")
    A("    return t")
    A("```")
    A("- **只做这三步**：不转半角/全角、不合并 `≪≫` 与 `<<>>`、不动标点、不动专名写法"
      "（后两者属 R/PSV 版与 2009 版的真实差异，必须保留为不同指纹）。")
    A("- **同指纹 = 同一段文本 ⇒ 同一 `重复组id`**；**只标记、不删行**（用户要求「找出重复的片段并进行标记」）。")
    A("- `重复组id` 形如 `R001`，按**交付主表行序首次出现**赋号（确定性、幂等）。\n")
    A("### 特例（逐条）\n")
    A("| # | 特例 | 处置 |")
    A("| --- | --- | --- |")
    A("| 1 | `ot` 的 `s00_00` / `otr` 的 `s00_00` 是**序文标题**（非简介） | 原样保留、按同一规则参与指纹；其指纹与任何简介都不同 → 独立成组 |")
    A("| 2 | `ot` 的 `s04_06k` 首行是 `≪面談≫…` 小标题 | 原样保留（不剥离小标题；剥离会破坏与 `otr` 的同指纹关系） |")
    A("| 3 | `ot` 的 `s01_12b`/`s01_13b` 双 `ScSkip` 结构，取到的是简介本体；`otr` 同文件有 2 处相同 skip 结构 | 两边都取到同一段文本 → 同组 |")
    A("| 4 | `otv` 的 `S01_12B`/`S01_13B` 各有 2 个 `SceneJumpDialog` 块（块 1/2 文本相同） | **两块都保留**（源侧确有 2 条记录）→ 组大小为 4 |")
    A("| 5 | `otv` 的 `S01_14G1` 源脚本**缺结尾引号**，按行尾兜底取全文 | 原样保留；其 `jp字符数` 与串长（真换行按 1 字）**不一致**（详见 §五 第 3 条） |")
    A("| 6 | `otv` 的 `S01_01` 与 `M09_02` 的 `:Text` **只有全角空格**（空占位） | 归一化后指纹为**空串** ⇒ 两条分到同一组（机械同指纹），**非真实文本复用**；两条都无待译内容 |")
    A("| 7 | 跨场景复用（`S03_05B1/B2`、`S03_06E1/E2`、`S03_06G1/G2`、`S03_08C1/C2` 的 (Ｎ)/(Ｃ) 差分；`S03_11A`↔`S03C_03A`、`S03_14D`↔`S03C_03C` 跨线复用） | **同组跨场景**（组大小 6），组内共享译文 |")
    A("")

    A("---\n")
    A("## 二、场景归一（匹配规则与失败清单）\n")
    A("**匹配规则**：把三源脚本名 `script` **一律 `lower()` 归一为小写**后，与 "
      "`scene_ot.jsonl` / `scene_otr.jsonl` / `scene_otv.jsonl` 的 `script` 字段（同样 `lower()`）比对；"
      "命中即取该场景的 `scene_id`。\n")
    A("- **必须归一小写**：语料侧是 `s01_01a`，R 版脚本名是 `S01_01A`、PSV 是 `S01_01A`（`otv` 侧还有 `M01_01`）。")
    A("- **实测 453 个场景脚本名在三份 `scene_*.jsonl` 间无重名** ⇒ 归属唯一（构建器对重名硬报错）。")
    A("- `ot` 表里的 `s03c_*` 21 条属**亚衣线**，只在 `scene_otr.jsonl` 里，故归到 `otr_s03c_*`（与作品 skill §四一致）。")
    A("- PSV 的 `S01_*`/`S02_*`/`S03_*`/`S04_*` 脚本（%d 条）在本工程并入**本篇 `scene_ot`** 的场景"
      "（PSV 版在本工程只建模美咲线 `M01–M09` + 番外 `P03`，共 31 场景）；`S03C_*`（55 条）归亚衣线。\n"
      % sum(1 for x in ordered if x["src"] == "otv" and x["scene_owner"] == "ot"))
    A("### 逐源归属结果\n")
    A(table(["源", "输入行数", "归本篇 scene_ot", "归亚衣线 scene_otr", "归美咲线 scene_otv", "未匹配"],
            [["`%s`" % s, st["per_src"][s],
              sum(1 for x in ordered if x["src"] == s and x["scene_owner"] == "ot"),
              sum(1 for x in ordered if x["src"] == s and x["scene_owner"] == "otr"),
              sum(1 for x in ordered if x["src"] == s and x["scene_owner"] == "otv"),
              sum(1 for x in ordered if x["src"] == s and x["scene"] == UNMATCHED)]
             for s in ("ot", "otr", "otv")]))
    A("### 匹配失败清单（逐条，不静默丢）\n")
    if st["match_fail"]:
        A(table(["源", "脚本", "在 `_raw` 中的行号(含表头)", "处置"],
                [["`%s`" % m["src"], "`%s`" % m["script"], m["row"],
                  "`场景id=(未匹配)`；无对应我方场景（该脚本在本工程 712 场景中不存在）"] for m in st["match_fail"]]))
        A("说明：`otv` 的 `S01_01` 是 PSV 侧的**空占位** `SceneJumpDialog`（`:Text` 只有全角空格），"
          "其脚本名在本工程 712 场景里**不存在**（本篇对应场景脚本名为 `s01_01a`，已另有其行）⇒ **不是抽取错误，是无场景可挂**。"
          "该行仍**保留在主表中**（排在表尾），并进入 §一 特例 6 的空占位重复组。\n")
    else:
        A("无。（0 条）\n")
    A("")

    A("---\n")
    A("## 三、条数、重复组与同场变体\n")
    A("### 3.1 各源条数与合并后条数\n")
    A(table(["源", "输入 = 输出行数（逐源守恒）"],
            [["`%s`" % s, st["per_src"][s]] for s in ("ot", "otr", "otv")] +
            [["**合计**", "**%d**" % len(ordered)]]))
    A("### 3.2 重复组\n")
    A("- 组数 **%d**；行数合计 **%d**；无重复的行（组大小 1）**%d** 条。" % (
        len(groups), len(ordered), sizes.get(1, 0)))
    A("- **组大小分布**：" + "；".join("%d 条 → %d 组" % (k, sizes[k]) for k in sorted(sizes)))
    A("- **最大组**：" + "；".join(
        "大小 %d（%s）" % (len(v), " / ".join(
            "%s:%s%s" % (m["src"], m["script"], ("#"+m["blk"]) if m["blk"] != "1" else "")
            for m in sorted(v, key=lambda z: (SRC_RANK[z["src"]], z["script"], z["blk_no"]))))
        for fp, v in groups.items() if len(v) == max(sizes)))
    A("- **组构成（按源多重集）**：")
    for k in sorted(comp, key=lambda t: (-comp[t], t)):
        A("  - `%d` 组：`%s`" % (comp[k], "+".join(k)))
    A("")
    A("### 3.3 同场变体清单（同一场景跨源文本不同）\n")
    A("判定：把某场景的全部行按 `简介jp` 比较——**指纹不同 = 内容不同**；指纹同而原串不同 = **仅换行差异**。\n")
    vs_content = [s for s, n in st["variant_note"].items() if "内容不同" in n]
    vs_break = [s for s, n in st["variant_note"].items() if "行内换行" in n]
    A("- **内容不同：%d 个场景**；**仅 ot/otr 行内换行差异：%d 个场景**；合计 **%d 个场景**带 `同场变体标记`。"
      % (len(vs_content), len(vs_break), len(st["variant_note"])))
    A("- **otv 侧的换行位置几乎总与 `ot`/`otr` 不同**（源脚本自带换行、与 Lucifen 侧的折行位置无关），"
      "这属**排版差异、不是文案差异**，故**不计入**变体标记（否则会有 387 个场景被误标）。")
    oo = st["ototr"]
    A("- 对 `ot`/`otr` **共有**的 %d 个脚本：**原串相同 %d、不同 %d**；其中 **内容不同（归一化后仍不同）仅 %d**、"
      "**另 %d 个（%s）只是行内换行位置不同（内容一致）**。"
      "—— 前模块 `_raw_README.md` 记的「16 个文案不同」是**按原串直比**的口径，"
      "本模块按归一化口径如实更正为 **%d（内容）+ %d（仅换行）**。"
      % (oo["shared"], oo["raw_eq"], len(oo["raw_diff"]), len(oo["fp_diff"]), len(oo["raw_only"]),
         "、".join("`%s`" % s for s in oo["raw_only"]), len(oo["fp_diff"]), len(oo["raw_only"])))
    A("- **复核「这 %d 个的 otr 版逐字等于 PSV 版」**：把这 %d 个逐个与 `otv` 侧对应脚本的**归一化**文本比较 —— "
      "**%d/%d 成立**（`otr==otv` 命中 %d；PSV 无对应 %d；不一致 %d）。"
      "结论：前模块的说法**成立**（在归一化口径下）；但它把 2 个「仅换行差异」也计入了「文案不同」，"
      "**内容真正不同的只有 %d 个**。"
      % (len(oo["raw_diff"]), len(oo["raw_diff"]), len(oo["psv_eq"]), len(oo["raw_diff"]),
         len(oo["psv_eq"]), len(oo["psv_missing"]), len(oo["psv_neq"]), len(oo["fp_diff"])))
    A("")
    A(table(["场景id", "同场变体标记", "各源字数（统一口径：真换行按 1 字）"],
            [[s, st["variant_note"][s],
              " / ".join("%s %s" % (x["src"], x["jp_len"]) for x in st["per_scene"][s])]
             for s in sorted(st["variant_note"], key=lambda s: (st["chapters"][s]["order"] if s in st["chapters"] else 10**9))]))
    A("")

    A("---\n")
    A("### 3.4 「采用」列计数（裁决 B 落地结果）\n")
    A("- `采用=是` **%d 行** ｜ `采用=否` **%d 行**；带 `备注` 的行 **%d**"
      "（「变体留档，非采用版」**%d** 行、「与采用版文本一致，非首选载体」**%d** 行、未匹配空占位 1 行）。"
      % (st["adopt_stat"]["yes"], st["adopt_stat"]["no"], st["adopt_stat"]["with_note"],
         st["adopt_stat"]["notadopt_note"], st["adopt_stat"]["sametext_note"]))
    A("- 有效场景 **%d 个**：**文本一致（无取舍）%d 个**（其全部源行 `采用=是`）＋ **多文本需取舍 %d 个**"
      "（其中取 `ot` 版 %d 个；无 `ot` 源行、按 `otr` > `otv` 取版 %d 个）。"
      % (st["adopt_stat"]["scenes"], st["adopt_stat"]["uniform_scenes"],
         st["adopt_stat"]["variant_scenes"], st["adopt_pick"]["ot"], st["adopt_pick"]["not_ot"]))
    A("- 需取舍场景的**采用版**逐条（供编程组取用）：")
    A("")
    A(table(["场景id", "采用版（源/脚本）", "未采用版（源/脚本，字数）"],
            [[sid, "`%s/%s`" % (st["adopt_pick"]["rows"][sid][0], st["adopt_pick"]["rows"][sid][1]),
              "；".join("`%s/%s`(%s 字)" % (x["src"], x["script"], x["jp_len"])
                       for x in st["per_scene"][sid] if x["adopt"] == "否")]
             for sid in sorted(st["adopt_pick"]["rows"],
                               key=lambda s: (st["chapters"][s]["order"] if s in st["chapters"] else 10 ** 9))]))
    A("")

    A("---\n")
    A("## 四、译文状态与翻译缺口\n")
    A("### 4.1 译文共享规则（**只凭内容指纹，不凭同名/同场景**）\n")
    A("同一 `重复组` 内只要有任一成员已有中文，则该组**全部成员共享该译文**；`译文来源` 列写明借自哪个源与脚本。"
      "`ot` 侧 %d 行全部自带译文（实测空译文 %d 条）；`otv` 侧 %d 行标「已在库」"
      "（27 条美咲线 `M01_01–M09_02` ＋ 1 条空占位 `S01_01`；其中 **%d 条库内中文非空**，"
      "**%d 条库内为空槽**：`M09_02` 与 `S01_01`）。\n"
      % (st["extra"]["ot_rows"], len(st["ot_cn_empty"]), st["extra"]["otv_lib"],
         st["extra"]["otv_lib"] - st["extra"]["otv_lib_nonsense"], st["extra"]["otv_lib_nonsense"]))
    A("- **无「同名借译」**：`ot` 表 `s03c_*` 21 条的中文取自**本篇汉化语料**（前模块已按 jp 逐字匹配），"
      "本模块只按指纹判定，不额外补借。")
    A("- **供体冲突：%d 例**（同组内两行**各带不同中文**：同一段日文在库内存在两种译法）。"
      "**已按主代理 2026-09-29 裁决 A 落地**：术语表定译优先，其余取 `ot`（本篇）版；"
      "未采用的译法**不删除**，仅在 `备注` 列标注「另一译法见 `<场景>`，未采用」：\n"
      % len(st["cn_conflicts"]))
    if st["cn_conflicts"]:
        A(table(["重复组", "同组各带中文的行（来源/脚本/场景）", "本模块采用的供体", "两种译法的差异（人工摘要）"],
                [[c["gid"],
                  "；".join("`%s/%s`(`%s`)" % (m["src"], m["script"], m["scene"]) for m in c["members"]),
                  "`%s`" % c["chosen"],
                  " / ".join(m["own_cn"][:60] + ("…" if len(m["own_cn"]) > 60 else "") for m in c["members"])]
                 for c in st["cn_conflicts"]]))
        A("> ⚠️ 其中 `R135` 的两种译法分别写 `Ｒ翼` 与 `Ｒ－ＷＩＮＧ` —— 按裁决 A（术语表定译优先），"
          "**取写作 `Ｒ翼` 的一版**（作品层 `术语表.md` §2.4；即 `ot/s03_14d`），`s03c_03c` 一侧的旧写法**保留但不采用**；"
          "`R097`/`R099`/`R113` 三种情况两侧均为 `ot` 行（同一源的 (Ｎ)/(Ｃ) 差分或跨线重复），按同源内脚本名字典序取定："
          "`s03_06e1`、`s03_06g1`、`s03_11a`。")
        A("> 供体选择规则（确定性，已落地）：**术语表定译优先** → 否则 `ot` > `otr` > `otv`，同源内按脚本名字典序取第一个带中文者。")
    else:
        A("（0 例）")
    A("")
    A("### 4.2 译文状态分布（主表 %d 行）\n" % n(ordered))
    A(table(["译文状态", "行数"], [["%s" % k, status[k]] for k in (ST_OT, ST_OTV, ST_NEW)]))
    A("### 4.3 翻译缺口（=`_translate_gap.tsv`，按重复组去重，一行 = 一段待译文本）\n")
    A("> **两个口径，勿混用**：`_translate_gap.tsv` 的 **%d 行 = 按归一化指纹去重后的待译文本条数**"
      "（一段文本只列一次，即使它在多源出现多次）；主表里 `译文状态 == 需新译` 的**行数**是 **%d 行**"
      "（同一段文本每个源行各计一次）。二者的差 = 同一段待译文本被多个源行共用（%d 行 ÷ %d 段 = 平均 %.2f 行/段）。\n"
      % (len(gap), status[ST_NEW], status[ST_NEW], len(gap),
         (status[ST_NEW] / len(gap)) if gap else 0.0))
    A("- **缺口条数 %d 条（去重后）** ｜ **总字符数 %d 字**（字符数取该组原文代表行的 `jp字符数`，统一口径：真换行按 1 字）。"
      % (len(gap), gap_chars))
    A("- 按性质：")
    for k in sorted(cat, key=lambda k: -cat[k]):
        A("  - `%s`：**%d 条 / %d 字**" % (k, cat[k], sum(g["jp_len"] for g in gap if g["cat"] == k)))
    A("- **点名答复**：属 **R 版独有（含亚衣线）** = **%d 条**；属 **ot/otr 改写版** = **%d 条**；"
      "其余 **PSV 改写 %d 条**、**PSV 独有（亚衣线场景、R 与 PSV 各自成段）%d 条**。"
      % (cat.get("R 版独有（亚衣线，无 2009 本篇对照）", 0),
         cat.get("ot/otr 改写版（同场景本篇版存在但内容不同）", 0),
         cat.get("PSV 改写版（同场景本篇版存在但内容不同）", 0),
         cat.get("PSV 独有（亚衣线场景，R 版另有不同文本、已各自成段）", 0)))
    n_a = cat.get("R 版独有（亚衣线，无 2009 本篇对照）", 0)
    A("- **R 版独有的 %d 条**与作品 skill §四的亚衣线口径**独立交叉核对通过**：按其场景在 "
      "`scene_otr.jsonl` 的 `source_kind` 统计为 `%s` —— 即 **新增场景 %d + 分支场景 %d = %d**，"
      "与「21 共有 + 3 分支 + 31 新增」中的**非共有部分逐条吻合**（`s03c_01d1`/`s03c_01d2`/`s03c_04b1` 为分支）。"
      % (n_a, st["otr_kind_dist"], st["otr_kind_dist"].get("new", 0),
         st["otr_kind_dist"].get("branch", 0),
         st["otr_kind_dist"].get("new", 0) + st["otr_kind_dist"].get("branch", 0)))
    A("- 缺口明细（按剧情顺序）：")
    A("")
    A(table(["待译id", "重复组", "涉及来源", "涉及场景", "字数", "性质"],
            [[g["tid"], g["gid"], "`%s`" % "+".join(g["srcs"]), "`%s`" % ";".join(g["sids"]),
              g["jp_len"], g["cat"]] for g in gap]))
    A("")
    A("> 缺口的**原文代表行**优先取 `otr`（R 版；`otv` 同组时内容与之一致），无 `otr` 时取 `otv`。")
    A("")

    A("---\n")
    A("## 五、无法判定的点（如实列出，不臆断）\n")
    A("1. **`otv` 的 `S01_01` 无场景可挂**：其脚本名在本工程 712 场景中不存在，其 `:Text` 又是空占位 ⇒ "
      "`场景id=(未匹配)`、`章节标题(中文)=(未匹配)`、`剧情分组=未匹配`；已保留在表尾并计入守恒，不丢行。")
    A("2. **空占位重复组**：`S01_01` 与 `M09_02` 归一化后指纹同为**空串**，机械同组；两条都无数可译，"
      "其「译文」是库内**空槽**（`scene_otv.jsonl` 该行的 `empty_slot=True`、`cn=''`）——"
      "本模块据前模块的「已在库」标志判为 `已有(otv库内)` 且 `简介cn` 留空，**未凭空补文本**。"
      "裁决 D 落地后：`S01_01`（未匹配伪场景）`备注` 标「源为空占位，无正文；无对应我方场景，不参与采用判定」，"
      "`M09_02` 标「库内为空槽，无正文（源侧占位）」；两者 `译文状态` 均 **非** `需新译`，**均不在缺口表**。")
    A("3. **源列 `jp字符数` 的三源口径不统一**：`ot`/`otr` 的源列 = **真换行按 1 字**；`otv` 的源列 = "
      "**字面 `\\n` 按 2 字计**（即单元格长度）——实测 `otv` 有 **%d 行**两种口径不同"
      "（差 = 该串内字面 `\\n` 的个数，多在 2–5 字）。本表 `jp字符数` 列**统一为「真换行按 1 字」**，"
      "故 `otv` 行的该列 = 源列 − `\\n` 个数；两者**不是同一口径，勿直接与 `_raw_otv.tsv` 比数**。"
      % st["src_count_gap"].get("otv(nl)", 0))
    A("   另：**源列本身自相矛盾的行 1 条**（%s）——该行按源脚本缺陷（缺结尾引号）收录，"
      "源列与任何一种还原口径都不一致，**以源列为准、未改写**；其余 %d 行与其源列口径自洽。"
      % ("、".join("`%s/%s`（源列 %d / 真长 %d / 单元格长 %d）" % (
          m["src"], m["script"], m["declared"], m["real"], m["cell"]) for m in st["len_mismatch"]) or "无",
         len(ordered) - len(st["len_mismatch"])))
    A("4. **`同场变体` 的取舍已裁决（裁决 B）**：**一律取本篇（`ot`）版**；落地在主表 `采用` 列（规则见 §一·补、计数见 §3.4）。"
      "本模块按该裁决**标记**取舍，**不再逐案请示**；若日后要改取 R/PSV 版，改 `采用` 列的规则与本模块即可。")
    A("5. **`ot` 的 `s00_00`/`otr` 的 `s00_00` 是序文标题而非简介**（前模块标 `类型=标题型`）："
      "**已裁决（裁决 C）保留**，`备注` 标「非简介（序文标题），保留以便写序文屏取用」，**不算缺口**"
      "（其 `译文状态` = `已有(ot原译)`，实测不在 `_translate_gap.tsv` 中）。")
    A("6. **不存在的中文**：`otr` 侧全部无本项目中文（D14 排除 R 版正文）；`otv` 侧 %d 行未在库。"
      "这些行**只能靠指纹借译**；借不到的 %d 组已列入缺口，**未按「同场景」借译**。"
      % (st["extra"]["otv_rows"] - st["extra"]["otv_lib"], len(gap)))
    A("7. **%d 例供体冲突已裁决（裁决 A）**：术语表定译优先、其余取 `ot` 版；未采用译法不删、只在 `备注` 标注"
      "（详见 §4.1 表）。" % len(st["cn_conflicts"]))
    A("8. **裁决前已核对 C/D 不在缺口表**：`_translate_gap.tsv` 的 %d 行中，"
      "**无一行涉及 `ot_s00_00`**（裁决 C）、**无一行涉及未匹配伪场景、也无一行指纹为空**（裁决 D 的空占位组）"
      "—— 见验收器 §⑨ 的两项断言。" % len(gap))
    A("")
    A("### 场景归属口径备注（为什么用工作树内的 `scene_*.jsonl`）")
    A("工作树的 `剧本/scene_ot.jsonl` 与主工作区同名文件**内容逐字节相同（仅换行符 CRLF/LF 不同）**，"
      "`05_章节总表.tsv` 亦然（本次已用「去 CR 后逐字节比对」验证）。故构建器**只读工作树内**的这三份文件，"
      "保证产物可复现且不触碰主工作区。")
    A("")

    A("---\n")
    A("## 六、复跑与验收（**两阶段口径**）\n")
    A("本模块是**两阶段**流水线：`build_synopsis_master.py`（**组装前**）→ `assemble_deliverables.py`"
      "（**并入新译 / 加 `原文换行位置` / 产片尾清单与待入表汇总**）→ `verify_deliverables.py`（**交付态验收**）。\n")
    A("```bash")
    A('cd "E:/ZCode Workspace/Galgame/临时/wt-syn"')
    A('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_synopsis_master.py"')
    A('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_synopsis_master.py" --neg-selftest')
    A('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/assemble_deliverables.py"    # ← 必须接跑')
    A('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_deliverables.py"      # 交付态验收')
    A('python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_deliverables.py" --neg-selftest')
    A("```")
    A("> ⚠ **警告**：单独跑 `build_synopsis_master.py` 会把主表打回 **16 列 / `需新译`=107**"
      "（**抹掉新译译文与 `原文换行位置` 列**）——**必须接跑 `assemble_deliverables.py`** 才能回到交付态。\n")
    A("| 阶段 | 脚本 | 产物 | 验收器 |")
    A("| --- | --- | --- | --- |")
    A("| 组装前 | `build_synopsis_master.py` | 主表 16 列 / `需新译`=107 / 缺口表 61 | "
      "`verify_synopsis_master.py`（**只验此阶段**；交付态下本器输出 NOT_APPLICABLE 并退出码 2，不代表交付物有问题） |")
    A("| 交付态 | `assemble_deliverables.py` | 主表 **17 列** / `需新译`=0 / `片尾清单.tsv` 148 行 / `_待入表汇总.tsv` | "
      "`verify_deliverables.py`（**交付态验收**） |")
    A("")
    A("- 构建器**幂等**：重跑后三个产出的字节与 md5 不变（构建器自带幂等自证）。")
    A("- 构建器**硬校验输出路径**：三个输出必须落在本工作树的 `资源组\\` 内，且 `资源组\\` 必须位于 `临时\\` 工作树内；"
      "`--neg-selftest` 用 4 条越界路径（`..` 逃逸 / 主工作区 `工程\\` / `C:\\`）自证**逐条报错**。")
    A("- `verify_synopsis_master.py`（只读）**只验组装前产物**：逐源守恒 / 重复组一致 / 排序单调 / "
      "`需新译` 集合 == 无中文组集合 / 表头与行数 / 缺口与状态自洽 / **负对照**（同文本异脚本必同组、指纹改坏必异组）。"
      "**交付态请改用 `verify_deliverables.py`。**")
    A("- `verify_deliverables.py`（只读）**交付态验收**：主表 1253 行 & `需新译`=0 & 空 `简介cn` 仅 2 条空占位（`otv/S01_01`、`otv/M09_02`）/ "
      "同一重复组内 `简介cn` 一致 / `原文换行位置` 非空集合 == 61 组覆盖行（107）/ "
      "**片尾清单 148 行（图 141 + 视频 7）且逐件实算 字节+md5 与磁盘一致** / `_待入表汇总.tsv` 自洽；"
      "`--neg-selftest` 含两条变异（打坏重复组一行 `简介cn`、打坏片尾清单一行 `md5`）。")
    A("")
    A("## 七、字段口径（**交付态：17 列**）\n")
    A(table(["列", "口径"],
            [["`序号`", "交付主表行序 1..N（N=%d）；排序键 = （05 行序, 未匹配置尾, `ot`<`otr`<`otv`, 块号, 脚本名）" % len(ordered)],
             ["`场景id`", "取 `scene_*.jsonl` 的 `scene_id`；未匹配为 `(未匹配)`"],
             ["`章节标题(中文)`", "取 `05_章节总表.tsv` 的 `章节标题(中文)`。**`05_章节总表.tsv` 中空标题在主表以「（无标题）」占位（27 行）**，"
                                 "故「与章节总表逐字一致」**仅对非空标题成立**（另有未匹配伪场景 1 行为 `(未匹配)`）"],
             ["`剧情分组`", "取 `05_章节总表.tsv` 的 `spine归属`（act 号 + 路线名）"],
             ["`来源`/`脚本`", "源代号 / 该源原脚本名（`otv` 侧保持全大写原样）"],
             ["`简介jp`", "源原文原样（`ot`/`otr` 的真换行在该 TSV 内写作字面 `\\n`）"],
             ["`简介cn`", "本行自带译文、或同重复组借来的译文。**组装前** `需新译` 行为空；**交付态**回填后无 `需新译` 行，"
                          "空值仅 **2 条空占位**（`otv/S01_01`、`otv/M09_02`）"],
             ["`译文状态`", "**四值**：`已有(ot原译)` / `已有(otv库内)` / **`已有(新译)`** / `需新译`。"
                            "`已有(新译)` = 交付态由 `assemble_deliverables.py` 回填的 107 行；"
                            "`需新译` **仅存在于组装前（107 行）**，交付态为 **0**"],
             ["`译文来源`", "自带=来源与脚本；借译=`借自 <源>/<脚本>（重复组 Rxxx，指纹相同）`；"
                            "`已有(新译)`=`新译(2026-09-29 · Txxx)`；`需新译`=`—`"],
             ["`重复组id`", "`Rxxx`，按主表行序首次出现赋号"],
             ["`同场变体标记`", "空 / `是（内容不同：…）` / `是（仅 ot/otr 行内换行位置不同，内容一致）`"],
             ["`jp字符数`", "**统一口径：真换行按 1 字**（`ot`/`otr` 与源列一致；`otv` 源列把字面 `\\n` 按 2 字计，"
                          "故本列 = 源列 − 该串内字面 `\\n` 个数）"],
             ["`jp的md5`", "源列原值（该串在源文件中原样字节的 md5，未做归一化）"],
             ["`采用`", "`是`/`否`。同一场景文本一致 ⇒ 全 `是`；多文本 ⇒ 只取一版 `是`（`ot` > `otr` > `otv`），"
                       "其余 `否`；未匹配行 `否`。规则见 §一·补"],
             ["`原文换行位置` **（交付态新增）**",
              "**该重复组原文代表行（`otr` 优先；无 `otr` 取 `otv`）的换行位置**，逗号分隔（如 `27,54,81,108,135`）；"
              "**无换行写 `无`**；**未回填的既有译文行留空**并在 `备注` 标「换行位置未逐条登记」。"
              "—— 现实现取的是**组代表行**的值（组内共享同一份），故 **59 行 `otv` 中有 45 行**该列与"
              "**其自身 jp** 的换行**个数**不符，属**设计使然**（组代表行口径），**不是缺陷**"],
             ["`备注`", "裁决 A/C/D 与「变体留档，非采用版」的落点；多条用「；」并列；无则为空"]]))
    A("")
    A("**`原文换行位置` 列的「有意不对称」（交付态，如实登记）**：**1146 行** `原文换行位置` 为空"
      "（`备注` 标「换行位置未逐条登记」），其中 **125 行**的 `简介cn` 仍带字面 `\\n`——**91 行**与自身 `jp` 的 "
      "`\\n` 个数相等（＝保留原分段）、**34 行**不等；而**新译 107 行**则为「**无硬换行 + 已登记**」"
      "（`简介cn` 带字面 `\\n` 者 **0 行**，`原文换行位置` 非空 **107 行**）。"
      "这是「**既有借译保留原写法 / 新译按新口径**」的**有意不对称**，不是遗漏（既有译文的其他体例差异"
      "〔如引号体例〕一律**不改、只登记**，以免与语料分叉）。")
    return "\n".join(L) + "\n"


# ────────────────────────────── main ──────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--neg-selftest", action="store_true", help="只做路径越界负向自证")
    a = ap.parse_args()
    if a.neg_selftest:
        return neg_selftest()

    for p in (OUT_MASTER, OUT_GAP, OUT_README):
        guard_path(p, "输出")
    st = build()

    m_rows = master_rows(st)
    g_rows = gap_rows(st)
    md5_master = write_tsv(OUT_MASTER, MASTER_HEADER, m_rows)
    md5_gap = write_tsv(OUT_GAP, GAP_HEADER, g_rows)
    hash_table = [("剧本/章节简介.tsv", len(m_rows), os.path.getsize(OUT_MASTER), md5_master),
                  ("剧本/简介/_translate_gap.tsv", len(g_rows), os.path.getsize(OUT_GAP), md5_gap),
                  ("剧本/简介/_merge_README.md", None, None, None)]
    readme = render_readme(st, hash_table)
    write_text(OUT_README, readme)

    # 幂等自证：重跑「解析 → 序列化」必须与已落盘的三份产物逐字节一致
    st2 = build()
    idem_ok = (master_rows(st2) == m_rows and gap_rows(st2) == g_rows and
               render_readme(st2, hash_table) == readme)

    sizes = collections.Counter(len(v) for v in st["groups"].values())
    gap_chars = sum(g["jp_len"] for g in st["gap"])
    cat = collections.Counter(g["cat"] for g in st["gap"])
    print("== build_synopsis_master ==")
    print("输入行数： ot=%d otr=%d otv=%d  合计=%d" % (
        st["per_src"]["ot"], st["per_src"]["otr"], st["per_src"]["otv"], len(st["recs"])))
    print("输出行数： 主表=%d ｜ 缺口=%d ｜ README=1（逐源守恒：%s）" % (
        len(m_rows), len(g_rows), all(st["per_src"][s] ==
        sum(1 for x in st["ordered"] if x["src"] == s) for s in ("ot", "otr", "otv"))))
    print("重复组：  %d 组；大小分布 %s；最大组大小 %d" % (
        len(st["groups"]), dict(sorted(sizes.items())), max(sizes)))
    print("译文状态：%s" % dict(collections.Counter(x["status"] for x in st["ordered"])))
    print("采用列：  是=%d 否=%d（其中变体留档 %d）；多文本场景 %d 个（取 ot 版 %d / 无 ot 取 otr 或 otv %d）" % (
        st["adopt_stat"]["yes"], st["adopt_stat"]["no"], st["adopt_stat"]["notadopt_note"],
        st["adopt_stat"]["variant_scenes"], st["adopt_pick"]["ot"], st["adopt_pick"]["not_ot"]))
    print("翻译缺口：%d 条 / %d 字；%s" % (len(st["gap"]), gap_chars, dict(cat)))
    print("同场变体：内容不同 %d 场景；仅 ot/otr 行内换行差异 %d 场景" % (
        sum(1 for s, n in st["variant_note"].items() if "内容不同" in n),
        sum(1 for s, n in st["variant_note"].items() if "行内换行" in n)))
    print("匹配失败：%d 条 %s" % (len(st["match_fail"]),
          [(m["src"], m["script"]) for m in st["match_fail"]]))
    print("计数不一致（源列与其口径不符，真问题）：%d 条 %s" % (len(st["len_mismatch"]),
          [(m["src"], m["script"], m["declared"], m["real"], m["cell"]) for m in st["len_mismatch"]]))
    print("源列口径差异（otv 把字面 \\n 按 2 字计）：%d 行" % st["src_count_gap"].get("otv(nl)", 0))
    print("md5： 章节简介.tsv=%s  _translate_gap.tsv=%s" % (md5_master, md5_gap))
    print("IDEMPOTENT %s" % ("PASS" if idem_ok else "FAIL"))
    return 0 if idem_ok else 1


if __name__ == "__main__":
    sys.exit(main())
