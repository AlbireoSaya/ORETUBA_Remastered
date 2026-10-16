# -*- coding: utf-8 -*-
r"""
W6d · `scene_otp.jsonl` 独立校验器（7 项验收自证）

原则：**从磁盘重新读取 `scene_otp.jsonl`**，并与**只读源**交叉核对，不依赖构建器内存态。
只读：`工程\我们没有翅膀 前奏诗\汉化\剧情汉化\*.jsonl`、`工程\我们没有翅膀 前奏诗\汉化\SCRIPT_CN\*.sob`、
      `工程\我们没有翅膀 前奏诗\汉化\交付说明.md`、`资源组\修正\*`、`资源组\krkr素材库\资源总账.json`、
      `工程\我们没有翅膀\汉化\剧情汉化\*.jsonl`
只写：`子代理工作区\ISSUE-20260918-06\W6d\W6d验收.json`

复跑：python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_otp.py"
"""
import os, re, json, csv, glob, struct, collections, sys

# W10b：`phase` 值域统一来源（`资源组\剧本\schema.md` §三.5，八值闭集）
sys.dont_write_bytecode = True   # 禁止在工具目录留下 __pycache__（须在 import 兄弟模块之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_violations
import _term_unify                # ISSUE-20260930-12：`term_unify` 校验判据的唯一实现（词形级）

U3000 = "\u3000"                  # 全角空格：构建器 ②.5 删它 ⇒ 传入 ignore_u3000（非 later_layers_touched）

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；产物 scene_otp.jsonl 与验收 JSON 读/写本 checkout。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, r"资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, r"修正")                            # 修正表：以本分支副本为准
SCENE = os.path.join(RES_LOCAL, r"剧本", "scene_otp.jsonl")        # 产物读本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6d")   # 写本 checkout

OTP_PROJ = os.path.join(DATA_ROOT, r"工程\我们没有翅膀 前奏诗")
CN_DIR   = os.path.join(OTP_PROJ, r"汉化\剧情汉化")
SOB_DIR  = os.path.join(OTP_PROJ, r"汉化\SCRIPT_CN")
OT_CN    = os.path.join(DATA_ROOT, r"工程\我们没有翅膀\汉化\剧情汉化")
LEDGER   = os.path.join(RES, r"krkr素材库\资源总账.json")
LIB_ROOT = os.path.join(RES, r"krkr素材库")          # 素材库根 = 引用命名空间基准（W11h）


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误读/误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))


_assert_in_checkout(SCENE, "scene_otp.jsonl")

TABLES = [("修正表_B1B3.tsv", os.path.join(FIX, "修正表_B1B3.tsv")),
          ("修正表_B1B3_扩展.tsv", os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
          ("修正表_新增场景mig重译.tsv", os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
          # ISSUE-20260930-12：2026-09-30 用户术语裁决表（fix_type=term_unify，词形级语义）
          ("修正表_裁决20260930.tsv", os.path.join(FIX, "修正表_裁决20260930.tsv"))]

R = {}
RES_RE = re.compile(r"^(?:CHR|PIC|SYS|SE|BGM|VOICE|DATA)\\[A-Za-z0-9_.\-]+\.(?:ELG|OGG|MPG|GMP|LAG)$", re.I)
DIR2KIND = {"CHR": "chr", "PIC": "pic", "SYS": "sys", "SE": "se", "BGM": "bgm", "VOICE": "voice", "DATA": "movie"}


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def parse_sob0(d):
    table_size = u32(d, 4); table_end = table_size + 8; off = 8; maps = []
    while off < table_end:
        n = u32(d, off); off += 4; m = {}
        for _ in range(n):
            m[u32(d, off)] = u32(d, off + 4); off += 8
        maps.append(m)
    ss, se = u32(d, off), u32(d, off + 4)
    return maps, ss, se, off + 8


def read_ref_string(d, p):
    c = d[p]; p = p + 3 if c == 0 else p
    f = d[p] if p < len(d) else 0
    if f in (2, 3):
        p += 4
    e = d.find(b"\x00", p)
    return d[p:e]


# ================================================================ 读产物
objs = []
with open(SCENE, encoding="utf-8") as f:
    raw_lines = f.readlines()
json_ok = True
for ln in raw_lines:
    objs.append(json.loads(ln))
R["scene_file"] = SCENE
R["scene_lines"] = len(objs)
R["A6_jsonl_loads_ok"] = json_ok

# ================================================================ 读源
src = {}
for p in sorted(glob.glob(os.path.join(CN_DIR, "*.jsonl"))):
    sc = os.path.basename(p)[:-len(".sob.jsonl")]
    src[sc] = [json.loads(l) for l in open(p, encoding="utf-8")]
corr_rows = []
for tname, tpath in TABLES:
    for r in csv.DictReader(open(tpath, encoding="utf-8-sig", newline=""), delimiter="\t"):
        r["_table"] = tname; corr_rows.append(r)
ledger = json.load(open(LEDGER, encoding="utf-8"))
idx = collections.defaultdict(dict)
for e in ledger["entries"]:
    if e["source"] == "otp":
        idx[e["kind"]][os.path.splitext(e["orig_name"])[0].lower()] = e["out_relpath"]
ot_jp = collections.defaultdict(set)
for p in glob.glob(os.path.join(OT_CN, "*.jsonl")):
    osc = os.path.basename(p)[:-len(".sob.jsonl")]
    for ln in open(p, encoding="utf-8"):
        o = json.loads(ln)
        if (o.get("jp") or "").strip():
            ot_jp[o["jp"]].add(osc)

# ================================================================ A1 场景数
scripts_out = [o["script"] for o in objs]
A1 = {"scene_count": len(objs), "unique": len(set(scripts_out)) == len(objs),
      "match_source_scripts": set(scripts_out) == set(src.keys()),
      "source_script_count": len(src)}
R["A1_scene_count"] = A1

# ================================================================ A2 行数守恒（逐脚本）
diffs = []
for o in objs:
    n_src = len(src[o["script"]])
    if n_src != o["line_count"]:
        diffs.append({"script": o["script"], "src": n_src, "out": o["line_count"]})
R["A2_line_conservation"] = {
    "src_total": sum(len(v) for v in src.values()),
    "out_total": sum(o["line_count"] for o in objs),
    "per_scene_diffs": diffs,
    "balanced": not diffs and sum(len(v) for v in src.values()) == sum(o["line_count"] for o in objs),
}
# 逐槽 jp / kind / 源槽序号 保真
jp_bad, kind_bad, idx_bad = [], [], []
for o in objs:
    s = src[o["script"]]
    for i, l in enumerate(o["lines"]):
        if l["jp"] != (s[i].get("jp") or ""):
            jp_bad.append((o["script"], l["seq"]))
        if l["kind"] != (s[i].get("kind") or ""):
            kind_bad.append((o["script"], l["seq"]))
        if l["index"] != s[i]["seq"]:
            idx_bad.append((o["script"], l["seq"]))
R["A2_jp_verbatim_mismatch"] = jp_bad
R["A2_kind_mismatch"] = kind_bad
R["A2_src_seq_mismatch"] = idx_bad

# ================================================================ A3 修正命中（逐条三分类）
otp_rows = [r for r in corr_rows if r["source"] == "otp"]
other_rows = [r for r in corr_rows if r["source"] != "otp"]
# 建产物定位索引：(script, index) -> line
line_by = {}
for o in objs:
    for l in o["lines"]:
        line_by[(o["script"], l["index"])] = (o, l)


def file2script(fn):
    return fn[:-len(".sob.jsonl")] if fn.endswith(".sob.jsonl") else os.path.splitext(fn)[0]


hit, miss, wrong = [], [], []
term_later_waived = 0                      # `later_layers_touched=True` 兜底命中数（实测应为 0）
term_boundary = collections.Counter()      # 各 fix 层边界文本来源的分布（审计用）
for r in otp_rows:
    sc = file2script(r["file"])
    seq = int(r["locator"].split("=")[1])
    t = line_by.get((sc, seq))
    if t is None:
        miss.append((r["_table"], r["file"], r["locator"])); continue
    o, l = t
    refs = [x for x in l["fix_refs"] if x["locator"] == r["locator"] and x["table"] == r["_table"]]
    if r["fix_type"] == "term_unify":
        # 词形级：`_term_unify.verify`（校验器专用）——① cn_before 命中词形；
        # ② 「该 fix 层的输出文本」（层边界文本）== re.sub(old_text, new_text, cn_before)；
        #    边界优先取更早者：下一条 fix_ref 的 cn_before ＞ name_replaced[0].before ＞ 最终 cn。
        #    U+3000 归一由 `ignore_u3000` 单独豁免，不算「别的层」（ISSUE-20260930-12 补）
        if not refs:
            wrong.append({"table": r["_table"], "file": r["file"], "locator": r["locator"],
                          "expect": r["new_text"], "got": l["cn"], "layers": l["layers"],
                          "why": "fix_refs 未记该表"})
            continue
        ref = refs[0]
        _all, _nr = l["fix_refs"], (l.get("name_replaced") or [])
        _i = _all.index(ref)
        if _i != len(_all) - 1:
            post, boundary = _all[_i + 1]["cn_before"], "next_fix_ref"
        elif _nr:
            post, boundary = _nr[0]["before"], "name_replaced[0].before"
        else:
            post, boundary = l["cn"], "cn"
        later = post is None
        if later:
            post, boundary = l["cn"], "waived"
            term_later_waived += 1
        term_boundary[boundary] += 1
        okv, why = _term_unify.verify(ref.get("cn_before"), post, r["old_text"], r["new_text"],
                                      later,
                                      ignore_u3000=(U3000 in (ref.get("cn_before") or "")))
        if okv and l["cn_base"] == "otp":
            hit.append({"table": r["_table"], "file": r["file"], "locator": r["locator"],
                        "fix_type": r["fix_type"], "cn": l["cn"], "cn_before": ref["cn_before"],
                        "layers": l["layers"], "cn_origin": l["cn_origin"]})
        else:
            wrong.append({"table": r["_table"], "file": r["file"], "locator": r["locator"],
                          "expect": r["new_text"], "got": l["cn"], "layers": l["layers"],
                          "why": why or "cn_base != otp"})
    elif l["cn"] == r["new_text"] and refs and l["cn_base"] == "otp":
        hit.append({"table": r["_table"], "file": r["file"], "locator": r["locator"],
                    "fix_type": r["fix_type"], "cn": l["cn"], "cn_before": refs[0]["cn_before"],
                    "layers": l["layers"], "cn_origin": l["cn_origin"]})
    else:
        wrong.append({"table": r["_table"], "file": r["file"], "locator": r["locator"],
                      "expect": r["new_text"], "got": l["cn"], "layers": l["layers"]})
# 非 otp 源：必须一条都没生效
leaked = []
for r in other_rows:
    sc = file2script(r["file"])
    seq = int(r["locator"].split("=")[1]) if r["locator"].startswith("seq=") else None
    if seq is None:
        continue
    t = line_by.get((sc, seq))
    if t and any(x["locator"] == r["locator"] for x in t[1]["fix_refs"]):
        leaked.append((r["source"], r["file"], r["locator"]))
# 产物内不得出现非 otp 的 fix_ref
bad_fix = [(o["script"], l["seq"], x) for o in objs for l in o["lines"] for x in l["fix_refs"]
           if not x["locator"].startswith("seq=")]
R["A3_corrections"] = {
    "total_rows": len(corr_rows),
    "otp_scope": len(otp_rows),
    "hit": len(hit), "missing": miss, "mismatch": wrong,
    "otp_hit_detail": hit,
    "other_source_rows": len(other_rows),
    "other_source_leaked": leaked,
    "non_otp_locator_in_output": bad_fix,
    "all_otp_hit": len(hit) == len(otp_rows) and not miss and not wrong,
    "term_later_waived": term_later_waived, "term_boundary": dict(term_boundary),
}
R["A3_other_source_by_table_source"] = collections.Counter(
    (r["_table"], r["source"]) for r in other_rows).most_common()

# ================================================================ A4 选择支
src_sel = {}
for sc, rows in src.items():
    s = [(r["seq"], r["sel"], r["idx"], r["jp"], r["cn"]) for r in rows if r.get("sel", 0) != 0]
    if s:
        src_sel[sc] = s
out_sel = {o["script"]: o["choices"] for o in objs if o["choices"]}
sel_cmp = []
for sc in sorted(set(src_sel) | set(out_sel)):
    a = src_sel.get(sc, [])
    b = out_sel.get(sc, [])
    sel_cmp.append({"script": sc, "src_slots": len(a), "out_slots": len(b),
                    "jp_match": [x[3] for x in a] == [c["text_jp"] for c in b],
                    "cn_match": [x[4] for x in a] == [(c["text_cn"] or "") for c in b],
                    "targets": [c["target"] for c in b],
                    "pairing_verified": [c["pairing_verified"] for c in b]})
R["A4_choices"] = {
    "src_points": len(src_sel), "src_slots": sum(len(v) for v in src_sel.values()),
    "out_points": len(out_sel), "out_slots": sum(len(v) for v in out_sel.values()),
    "detail": sel_cmp,
    "sel_hist_src": dict(collections.Counter(x[1] for v in src_sel.values() for x in v)),
    "all_caught": sum(len(v) for v in src_sel.values()) == sum(len(v) for v in out_sel.values())
                  and set(src_sel) == set(out_sel),
    "any_pairing_verified": any(c["pairing_verified"] for v in out_sel.values() for c in v),
}

# ================================================================ A5 素材
# 独立重扫 .sob 的 maps[4] 引用
refs = {}
for f in glob.glob(os.path.join(SOB_DIR, "*.sob")):
    sc = os.path.splitext(os.path.basename(f))[0]
    d = open(f, "rb").read()
    maps, ss, se, he = parse_sob0(d)
    s = set()
    for addr, v in maps[4].items():
        if not (ss <= v < se):
            continue
        try:
            t = read_ref_string(d, v + he).decode("ascii")
        except UnicodeDecodeError:
            continue
        if RES_RE.match(t):
            s.add(t)
    refs[sc] = s
asset_bad, asset_missing, asset_total = [], [], 0
for o in objs:
    exp = refs.get(o["script"], set())
    got = set(a["ref"] for a in o["assets"])
    if exp != got:
        asset_bad.append({"script": o["script"], "src": sorted(exp), "out": sorted(got)})
    for a in o["assets"]:
        asset_total += 1
        d0, fn = a["ref"].split("\\", 1)
        k = DIR2KIND.get(d0.upper(), "etc")
        p = idx.get(k, {}).get(os.path.splitext(fn)[0].lower())
        if p != a["out_relpath"] or (p is None) != (not a["hit"]):
            asset_bad.append({"script": o["script"], "ref": a["ref"], "out_relpath": a["out_relpath"],
                              "expect": p})
        if not a["hit"]:
            asset_missing.append({"script": o["script"], "ref": a["ref"]})
# 语音
vm = idx["voice"]
v_ref = v_hit = 0
v_missing = []
for o in objs:
    s = src[o["script"]]
    for l, sl in zip(o["lines"], s):
        v = sl.get("voice") or ""
        if not v:
            if l["audio"]:
                v_missing.append({"script": o["script"], "seq": l["seq"], "why": "无 voice 却有 audio"})
            continue
        v_ref += 1
        p = vm.get(v.lower())
        if p:
            if l["audio"] != [p]:
                v_missing.append({"script": o["script"], "seq": l["seq"], "voice": v, "audio": l["audio"]})
            else:
                v_hit += 1
        else:
            v_missing.append({"script": o["script"], "seq": l["seq"], "voice": v, "why": "总账未命中"})
R["A5_assets"] = {
    "assets_total": asset_total, "assets_hit": asset_total - len(asset_missing),
    "assets_missing": asset_missing, "asset_ref_mismatch": asset_bad,
    "voice_refs": v_ref, "voice_hit": v_hit, "voice_missing": v_missing,
    "by_kind": dict(collections.Counter(a["kind"] for o in objs for a in o["assets"])),
    "source_of_assets": "otp（唯一源；本模块只挂 otp 素材）",
}

# ================================================================ A6 schema 自洽
TOP_REQ = ["scene_id", "source", "script", "source_kind", "text_source", "title_variants",
           "game_dates", "phase", "route", "cast", "next", "next_kind", "choices",
           "line_count", "voice_count", "assets", "assets_missing", "stats", "lines"]
LINE_REQ = ["seq", "lineno", "kind", "speaker", "speaker_jp", "voice", "jp", "cn",
            "cn_base", "cn_origin", "align_method", "layers", "fix_refs", "name_replaced",
            "empty_slot", "audio"]
missing_top, missing_line, type_bad = [], [], []
for o in objs:
    for k in TOP_REQ:
        if k not in o or o[k] is None:
            missing_top.append((o.get("scene_id"), k))
    for k in ("title_jp", "title_cn", "game_date"):
        if k not in o:
            missing_top.append((o.get("scene_id"), k))
    for l in o["lines"]:
        for k in LINE_REQ:
            if k not in l or l[k] is None:
                missing_line.append((o["scene_id"], l.get("seq"), k))
    # 类型
    if not isinstance(o["cast"], list) or not isinstance(o["next"], list) or not isinstance(o["choices"], list):
        type_bad.append(o["scene_id"])
    if o["line_count"] != len(o["lines"]):
        type_bad.append((o["scene_id"], "line_count"))
    if o["next_kind"] not in ("linear", "branch", "end"):
        type_bad.append((o["scene_id"], "next_kind"))
    for c in o["choices"]:
        if "pairing_verified" not in c or "confirmed" not in c or "evidence" not in c:
            type_bad.append((o["scene_id"], "choice-fields"))
R["A6_schema"] = {
    "required_missing_top": missing_top, "required_missing_line": missing_line,
    "type_or_count_bad": type_bad,
    "scene_id_unique": len(set(o["scene_id"] for o in objs)) == len(objs),
    "all_scene_id_prefixed": all(o["scene_id"] == "otp_" + o["script"] for o in objs),
    "ok": not missing_top and not missing_line and not type_bad,
}

# ================================================================ A7 不臆断
A7 = {}
A7["game_date_all_null"] = all(o["game_date"] is None for o in objs)
A7["game_dates_all_empty"] = all(o["game_dates"] == [] for o in objs)
A7["scenes_with_date"] = [o["script"] for o in objs if o["game_date"]]
# 源中确实无显式日期
DRE = re.compile(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日")
A7["src_has_explicit_date"] = {sc: [m.group(0) for r in rows for m in DRE.finditer(r.get("jp") or "")]
                               for sc, rows in src.items()
                               if any(DRE.search(r.get("jp") or "") for r in rows)}
A7["pairing_verified_all_false"] = all(not c["pairing_verified"] for o in objs for c in o["choices"])
A7["d14_exception_all_null"] = all(l["d14_exception"] is None for o in objs for l in o["lines"])
A7["d14_exceptions_count"] = sum(1 for o in objs for l in o["lines"] if l["d14_exception"])
A7["empty_slots"] = sum(1 for o in objs for l in o["lines"] if l["empty_slot"])
A7["src_empty_slots"] = sum(1 for rows in src.values() for r in rows
                            if not (r.get("jp") or "") and not (r.get("cn") or ""))
A7["source_kind_recheck"] = []
for o in objs:
    sc = o["script"]
    cp = sc if sc in ("gameinit", "history", "title", "title2", "staff") else ("s" + sc if sc[0].isdigit() else None)
    jps = [r.get("jp") or "" for r in src[sc]]
    n = sum(1 for j in jps if j.strip())
    same = sum(1 for j in jps if j.strip() and cp and cp in ot_jp.get(j, ()))
    rate = 100.0 * same / n if n else 0
    exp = "shared" if (cp and rate >= 50) else "new"
    A7["source_kind_recheck"].append({"script": sc, "counterpart": cp, "jp": n, "same": same,
                                      "rate_pct": round(rate, 1), "expect": exp, "got": o["source_kind"],
                                      "ok": exp == o["source_kind"]})
A7["source_kind_all_ok"] = all(x["ok"] for x in A7["source_kind_recheck"])
A7["phase_values"] = dict(collections.Counter(o["phase"] for o in objs))
# W10b：phase 值域改由 schema.md §三.5（八值闭集，含 主线/框架/系统）统一校验，越界即报错
A7["phase_allowed"] = list(PHASE_ALLOWED)
A7["phase_out_of_schema_enum"] = phase_violations(objs)
A7["route_values"] = dict(collections.Counter(o["route"] for o in objs))
# 说话人：speaker_jp 必须逐槽等于源标签；speaker 非空
spk_bad = []
for o in objs:
    for l, sl in zip(o["lines"], src[o["script"]]):
        if l["speaker_jp"] != (sl.get("speaker") or ""):
            spk_bad.append((o["script"], l["seq"], "speaker_jp≠源标签"))
        elif l["speaker_jp"] and not l["speaker"]:
            spk_bad.append((o["script"], l["seq"], "有标签但 speaker 为空"))
        elif not l["speaker_jp"] and l["speaker"]:
            spk_bad.append((o["script"], l["seq"], "无标签却有 speaker"))
R["A7_speaker_jp_verbatim_mismatch"] = spk_bad
R["A7_no_fabrication"] = A7

# 标题复核
t_bad = []
for o in objs:
    sc = o["script"]
    is_story = sc.startswith(("p01_", "p02_", "p03_", "p04_", "02_", "03_", "buru"))
    if is_story:
        if o["title_jp"] != src[sc][0]["jp"] or o["title_cn"] != src[sc][0]["cn"]:
            t_bad.append({"script": sc, "out": (o["title_jp"], o["title_cn"]),
                          "src_first": (src[sc][0]["jp"], src[sc][0]["cn"])})
        if len(o["title_variants"]) != 1:
            t_bad.append({"script": sc, "variants": len(o["title_variants"])})
    else:
        if o["title_jp"] is not None or o["title_cn"] is not None or o["title_variants"]:
            t_bad.append({"script": sc, "why": "系统脚本应无标题", "title_jp": o["title_jp"]})
R["A7_title_check_bad"] = t_bad

# ================================================================ A8 引用命名空间可解析
# 契约：`资源组\剧本\schema.md` §2.1 —— `lines[].audio[]` 与 `assets[].out_relpath`
# 必须是**素材库相对路径**（本源前缀 `otp/`），且必须能在 `krkr素材库\` 下 `isfile`。
# 此前 A5 只比对「重算路径 == jsonl 值」，未做文件系统 isfile → 本项补齐。


def _libpath(rel):
    return os.path.join(LIB_ROOT, rel.replace("/", os.sep))


lib_audio = [{"script": o["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
             for o in objs for l in o["lines"] for p in l["audio"]]
lib_assets = [{"script": o["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for o in objs for a in o["assets"] if a["out_relpath"]]
a8_audio_ns = [x for x in lib_audio if not x["out_relpath"].startswith("otp/")]
a8_asset_ns = [x for x in lib_assets if not x["out_relpath"].startswith("otp/")]
a8_audio_disk = [x for x in lib_audio if not os.path.isfile(_libpath(x["out_relpath"]))]
a8_asset_disk = [x for x in lib_assets if not os.path.isfile(_libpath(x["out_relpath"]))]


def _hit_ok(a):
    if not a["out_relpath"]:
        return a["hit"] is False
    return bool(a["hit"]) == os.path.isfile(_libpath(a["out_relpath"]))


a8_hit_mismatch = [{"script": o["script"], "ref": a["ref"], "hit": a["hit"],
                    "out_relpath": a["out_relpath"]}
                   for o in objs for a in o["assets"] if not _hit_ok(a)]
a8_missing_declared = sorted(r for o in objs for r in o["assets_missing"])
a8_missing_actual = sorted(a["ref"] for o in objs for a in o["assets"] if not a["hit"])
a8_missing_ok = (a8_missing_declared == a8_missing_actual)
A8 = (not a8_audio_ns and not a8_asset_ns and not a8_audio_disk and not a8_asset_disk
      and not a8_hit_mismatch and a8_missing_ok)
R["A8_assets"] = {"pass": A8, "lib_root": LIB_ROOT,
                  "audio_refs": len(lib_audio), "asset_refs": len(lib_assets),
                  "audio_not_in_namespace": a8_audio_ns, "asset_not_in_namespace": a8_asset_ns,
                  "audio_missing_on_disk": a8_audio_disk, "asset_missing_on_disk": a8_asset_disk,
                  "hit_mismatch": a8_hit_mismatch,
                  "assets_missing_declared": a8_missing_declared,
                  "assets_missing_actual": a8_missing_actual,
                  "assets_missing_consistent": a8_missing_ok,
                  "audio_zero_but_voice_nonempty": [
                      {"script": o["script"], "seq": l["seq"], "voice": l["voice"]}
                      for o in objs for l in o["lines"] if l["voice"] and not l["audio"]]}

# ================================================================ 汇总
R["ALL_PASS"] = bool(
    A1["scene_count"] == 59 and A1["unique"] and A1["match_source_scripts"]
    and R["A2_line_conservation"]["balanced"] and not jp_bad and not kind_bad and not idx_bad
    and R["A3_corrections"]["all_otp_hit"] and not leaked and not bad_fix
    and R["A4_choices"]["all_caught"] and not R["A4_choices"]["any_pairing_verified"]
    and not asset_bad and not asset_missing and not v_missing and v_ref == v_hit
    and R["A6_schema"]["ok"]
    and A7["game_date_all_null"] and A7["pairing_verified_all_false"]
    and A7["source_kind_all_ok"] and not spk_bad and not t_bad
    and not A7["phase_out_of_schema_enum"]        # W10b：phase 值域（schema.md §三.5）
    and A8                                        # W11h：引用命名空间可解析
)
R["SUMMARY"] = {
    "A1_scene_count": "%d（源 %d 脚本，唯一 %s）" % (A1["scene_count"], A1["source_script_count"], A1["unique"]),
    "A2_lines": "%d == %d（逐场景差异 %d）" % (R["A2_line_conservation"]["out_total"],
                                               R["A2_line_conservation"]["src_total"], len(diffs)),
    "A3_corrections": "otp %d 条 → 命中 %d / 未命中 %d / 不符 %d；非 otp 源 %d 条全部门控排除（泄漏 %d）"
                      % (len(otp_rows), len(hit), len(miss), len(wrong), len(other_rows), len(leaked)),
    "A4_choices": "%d 个选择点 / %d 个选项槽（源 %d / %d）"
                  % (R["A4_choices"]["out_points"], R["A4_choices"]["out_slots"],
                     R["A4_choices"]["src_points"], R["A4_choices"]["src_slots"]),
    "A5_assets": "素材 %d/%d；语音 %d/%d" % (asset_total - len(asset_missing), asset_total, v_hit, v_ref),
    "A6_schema": "必填缺失 %d / 逐行类型错 %d；scene_id 唯一 %s"
                 % (len(missing_top) + len(missing_line), len(type_bad), R["A6_schema"]["scene_id_unique"]),
    "A7_no_fabrication": "game_date 全 null %s；源显式日期场景 %d；pairing_verified 全 false %s；"
                         "speaker_jp 逐槽一致 %s；标题 %s"
                         % (A7["game_date_all_null"], len(A7["src_has_explicit_date"]),
                            A7["pairing_verified_all_false"], not spk_bad, not t_bad),
}

os.makedirs(STG, exist_ok=True)
json.dump(R, open(os.path.join(STG, "W6d验收.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

print("================ W6d 验收（独立复核） ================")
for k in ("A1_scene_count", "A2_lines", "A3_corrections", "A4_choices", "A5_assets",
          "A6_schema", "A7_no_fabrication"):
    print("%-20s %s" % (k, R["SUMMARY"][k]))
print("A3 otp 命中逐条:")
for h in hit:
    print("   %-26s %-22s %-11s %s" % (h["table"], h["file"], h["locator"], h["cn"][:44]))
print("A3 非 otp 源分布:", R["A3_other_source_by_table_source"])
print("A3 term_unify 层边界文本来源:", R["A3_corrections"]["term_boundary"],
      "| later_layers_touched 豁免", term_later_waived, "处")
print("A4 明细:")
for d in sel_cmp:
    print("   %-8s src=%d out=%d jp=%s cn=%s targets=%s" % (d["script"], d["src_slots"], d["out_slots"],
                                                            d["jp_match"], d["cn_match"], d["targets"]))
print("A5 by kind:", R["A5_assets"]["by_kind"])
print("A7 源显式日期场景:", R["A7_no_fabrication"]["src_has_explicit_date"] or "无")
print("A7 phase 值:", R["A7_no_fabrication"]["phase_values"], "越出 schema 枚举:", R["A7_no_fabrication"]["phase_out_of_schema_enum"])
print("A8 引用命名空间可解析：库根 %s ｜ audio %d 条 → 越界 %d 库内缺 %d ｜ assets %d 条 → 越界 %d 库内缺 %d ｜ hit 不符 %d ｜ assets_missing 一致 %s ｜ voice 非空但 audio=[] %d : %s"
      % (R["A8_assets"]["lib_root"], R["A8_assets"]["audio_refs"],
         len(R["A8_assets"]["audio_not_in_namespace"]), len(R["A8_assets"]["audio_missing_on_disk"]),
         R["A8_assets"]["asset_refs"], len(R["A8_assets"]["asset_not_in_namespace"]),
         len(R["A8_assets"]["asset_missing_on_disk"]), len(R["A8_assets"]["hit_mismatch"]),
         R["A8_assets"]["assets_missing_consistent"],
         len(R["A8_assets"]["audio_zero_but_voice_nonempty"]), R["A8_assets"]["pass"]))
print("ALL_PASS =", R["ALL_PASS"])