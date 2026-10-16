# -*- coding: utf-8 -*-
r"""
W6e · scene_otv.jsonl 独立校验器（对 8 项验收标准逐条自证）

不依赖 build_scene_otv.py 的内存态：**从磁盘产物 scene_otv.jsonl 重新读取**，
与只读源（台词对照.json / 场景标题_中文化.tsv / 资源引用.tsv / 音频清单.tsv /
脚本解包 / 三张修正表）交叉核对。

**W11h 新增 A8「引用命名空间可解析」**：此前 7 项**均未覆盖**「引用可解析」——
A5 的 isfile 判的是原始 PSV 源路径（修复前 0/1737 与 0/941 在素材库命名空间下可解析，
却仍判过）。A8 改为逐条核对 `lines[].audio[]` 与 `assets[].out_relpath`：
必须以 `otv/` 开头、必须在 `krkr素材库\` 下 `isfile`、`hit` 必须与之一致、
`assets_missing[]` 必须如实。任一不满足 → A8 FAIL → ALL_PASS False。

路径根（W11h 读写分离）：产物读**本脚本所在 checkout**；PSV 语料与 `krkr素材库`
实体文件（被 .gitignore 排除，仅存在于主工作区）经 `DATA_ROOT` 读取。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_otv.py"
输出：子代理工作区\ISSUE-20260918-06\W6e\W6e验收.json + 控制台摘要
"""
import json, os, re, csv, collections, sys

# W10b：`phase` 值域统一来源（`资源组\剧本\schema.md` §三.5，八值闭集）
sys.dont_write_bytecode = True   # 禁止在工具目录留下 __pycache__（须在 import 兄弟模块之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_violations
import _term_unify                # ISSUE-20260930-12：`term_unify` 校验判据的唯一实现（词形级）

U3000 = "\u3000"                  # 全角空格：构建器 ②.5 删它 ⇒ 传入 ignore_u3000（非 later_layers_touched）

# ---- 路径根（W11h 读写分离）
# 产物 scene_otv.jsonl 读**本脚本所在 checkout**（issue 分支产物）；
# 大体积只读源（PSV 语料 / krkr素材库 实体文件）被 .gitignore 排除、仅存在于主工作区，
# 故经 DATA_ROOT 读取（可用环境变量 `GRETA_DATA_ROOT` 覆盖）。
HERE      = os.path.dirname(os.path.abspath(__file__))
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))
RES_LOCAL = os.path.join(PRJ_LOCAL, r"资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, r"修正")
OUT  = os.path.join(RES_LOCAL, r"剧本")
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6e")   # 写本 checkout
PSV  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀PSV")
SCR  = os.path.join(PSV, r"脚本解包")
HAN  = os.path.join(PSV, r"汉化")
LST  = os.path.join(PSV, r"美咲线清单")
OT   = os.path.join(DATA_ROOT, r"工程\我们没有翅膀\汉化\剧情汉化")
LIB_ROOT = os.path.join(RES, r"krkr素材库")        # 素材库根 = 引用命名空间基准

SCENE = os.path.join(OUT, "scene_otv.jsonl")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误读/误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))


_assert_in_checkout(SCENE, "scene_otv.jsonl")

OTV_FILE = "台词对照.json"          # otv 修正表 `file` 列取值（_README.md §二.1）
# 本模块允许的 cn_origin 取值（W10b：新增修正层 fix_table / retranslate）
ORIGIN_ALLOWED = {"otv", "fix_table", "retranslate", "empty"}

def read_tsv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

res = {}
scenes = [json.loads(l) for l in open(SCENE, encoding="utf-8")]
res["file_lines"] = len(scenes)

EXPECT = (["M01_01", "M01_02", "M01_03", "M01_04",
           "M02_01", "M02_02", "M02_03", "M02_04", "M02_05", "M02_06", "M02_07", "M02_08",
           "M03_01", "M03_02", "M04_01", "M04_02", "M04_03", "M05_01", "M05_02",
           "M06_01", "M06_02", "M06_03", "M07_01", "M07_02", "M08_01", "M09_01", "M09_02"]
          + ["P03_01A", "P03_01B", "P03_01C", "P03_01D"])
cmp_rows = json.load(open(os.path.join(HAN, "台词对照.json"), encoding="utf-8"))
cmp_by = collections.defaultdict(list)
for r in cmp_rows:
    cmp_by[r["脚本"]].append(r)

# ---- A1 场景数（31：M 27 + P03 4）
res["A1_expected_scripts"] = EXPECT
res["A1_actual_scripts"] = [s["script"] for s in scenes]
res["A1_M_count"] = sum(1 for s in scenes if s["script"].startswith("M"))
res["A1_P03_count"] = sum(1 for s in scenes if s["script"].startswith("P03"))
# 独立核对：脚本解包目录里存在这 31 个文件；本篇语料中不存在同名脚本（证明 source_kind=new）
res["A1_files_exist"] = all(os.path.isfile(os.path.join(SCR, s)) for s in EXPECT)
ot_files = set(os.listdir(OT)) if os.path.isdir(OT) else set()
res["A1_no_2009_counterpart"] = sorted(
    f for f in ot_files if os.path.splitext(f)[0] in EXPECT or os.path.splitext(f)[0].upper() in EXPECT)
res["A1_pass"] = (sorted(res["A1_actual_scripts"]) == sorted(EXPECT) and len(scenes) == 31
                  and res["A1_M_count"] == 27 and res["A1_P03_count"] == 4
                  and res["A1_files_exist"] and not res["A1_no_2009_counterpart"])

# ---- A2 行数守恒（4,931 = 台词 4,904 + 梗概 27，逐脚本对账）
res["A2_baseline_total"] = len(cmp_rows)
res["A2_baseline_by_cat"] = dict(collections.Counter(r["类别"] for r in cmp_rows))
res["A2_total"] = sum(s["line_count"] for s in scenes)
res["A2_line_count_eq_len"] = all(s["line_count"] == len(s["lines"]) for s in scenes)
res["A2_scene_diff"] = {s["script"]: (s["line_count"], len(cmp_by[s["script"]]))
                        for s in scenes if s["line_count"] != len(cmp_by[s["script"]])}
res["A2_missing_scripts"] = [s for s in EXPECT if s not in cmp_by]
res["A2_by_cat"] = dict(collections.Counter(
    "梗概" if l["kind"] == "summary" else "台词" for s in scenes for l in s["lines"]))
res["A2_pass"] = (res["A2_total"] == res["A2_baseline_total"] and not res["A2_scene_diff"]
                  and res["A2_line_count_eq_len"] and not res["A2_missing_scripts"]
                  and res["A2_by_cat"] == res["A2_baseline_by_cat"])

# ---- A3 修正表（W10b：范围内 1 条 source=otv → 命中 1 / 门控 0 / 未命中 0）
tables = {"修正表_B1B3.tsv": read_tsv(os.path.join(FIX, "修正表_B1B3.tsv")),
          "修正表_B1B3_扩展.tsv": read_tsv(os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
          "修正表_新增场景mig重译.tsv": read_tsv(os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
          "修正表_otv.tsv": read_tsv(os.path.join(FIX, "修正表_otv.tsv")),   # W10b 接入
          # ISSUE-20260930-12：2026-09-30 用户术语裁决表（fix_type=term_unify，词形级语义）
          "修正表_裁决20260930.tsv": read_tsv(os.path.join(FIX, "修正表_裁决20260930.tsv"))}
allrows = [(tn, r) for tn, rows in tables.items() for r in rows]
res["A3_table_total"] = len(allrows)
res["A3_by_source"] = dict(collections.Counter(r["source"] for _, r in allrows))
otv_rows = [(tn, r) for tn, r in allrows if r["source"] == "otv"]
res["A3_otv_rows"] = [{"table": tn, "file": r["file"], "locator": r["locator"],
                       "fix_type": r["fix_type"], "old_text": r["old_text"],
                       "new_text": r["new_text"]} for tn, r in otv_rows]
applied = [{"script": s["script"], "locator": fr["locator"], "table": fr["table"],
            "fix_type": fr["fix_type"], "cn_before": fr["cn_before"]}
           for s in scenes for l in s["lines"] for fr in l["fix_refs"]]
res["A3_applied"] = applied
_bs = os.path.join(STG, "_build_stats_otv.json")
_bsj = json.load(open(_bs, encoding="utf-8")) if os.path.isfile(_bs) else {}
gated = _bsj.get("corrections_gated_out", [])
unhit = _bsj.get("corrections_unhit", [])
res["A3_gated_out"] = gated
res["A3_unhit"] = unhit
res["A3_in_scope_total"] = len(otv_rows)
res["A3_hit"] = len(applied)
res["A3_accounted"] = (len(applied) + len(gated) == len(otv_rows))
# 独立旁证 1：otv 语料不含修正表所针对的三类缺陷（假名残留）
kana = re.compile(r"[\u3041-\u309F\u30A0-\u30FF]")
kana_lines = [{"script": s["script"], "seq": l["seq"], "cn": l["cn"]}
              for s in scenes for l in s["lines"] if kana.search(l["cn"] or "")]
res["A3_kana_residue_lines"] = kana_lines
# 独立旁证 2：B1 双向校验「原文含「」 ⇒ 译文须含“”」——修正生效后须为 0 行
quote_bad = [{"script": s["script"], "seq": l["seq"], "jp": l["jp"], "cn": l["cn"]}
             for s in scenes for l in s["lines"]
             if ("「" in (l["jp"] or "") or "」" in (l["jp"] or ""))
             and not ("“" in (l["cn"] or "") or "”" in (l["cn"] or ""))]
res["A3_quote_missing_lines"] = quote_bad
# 独立旁证 3：修正值确已落盘——逐条核对「命中行的 cn == 表内 new_text」且
#             「cn_before == 表内 old_text」且「old_text == 源语料 中文」
#             （term_unify 例外：`old_text` 是词形正则、`new_text` 是替换值，改用
#              `_term_unify.verify`，见 ISSUE-20260930-12）
otv_tab = {(r["file"], r["locator"]): r for _, r in otv_rows}
src_cn = {(r["脚本"], r["行序"]): (r["中文"] or "") for r in cmp_rows}
value_checks = []
term_later_waived = 0                      # `later_layers_touched=True` 兜底命中数（实测应为 0）
term_boundary = collections.Counter()      # 各 fix 层边界文本来源的分布（审计用）
for s in scenes:
    for l in s["lines"]:
        for fr in l["fix_refs"]:
            tab = otv_tab.get((OTV_FILE, fr["locator"]))
            if tab is not None and tab["fix_type"] == "term_unify":
                # 层边界文本优先取更早者：下一条 fix_ref 的 cn_before ＞ name_replaced[0].before ＞ 最终 cn
                _all, _nr = l["fix_refs"], (l.get("name_replaced") or [])
                _i = _all.index(fr)
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
                okv, _why = _term_unify.verify(fr["cn_before"], post,
                                               tab["old_text"], tab["new_text"], later,
                                               ignore_u3000=(U3000 in (fr["cn_before"] or "")))
                value_checks.append({
                    "script": s["script"], "seq": l["seq"], "locator": fr["locator"],
                    "fix_type": tab["fix_type"], "cn_after": l["cn"], "cn_before": fr["cn_before"],
                    "boundary": boundary, "post": post,
                    "table_new_text": tab["new_text"], "table_old_text": tab["old_text"],
                    "term_unify_ok": okv, "ok": bool(okv)})
                continue
            value_checks.append({
                "script": s["script"], "seq": l["seq"], "locator": fr["locator"],
                "fix_type": tab["fix_type"] if tab else None,
                "cn_after": l["cn"], "cn_before": fr["cn_before"],
                "table_new_text": tab["new_text"] if tab else None,
                "table_old_text": tab["old_text"] if tab else None,
                "src_corpus_cn": src_cn.get((s["script"], l["lineno"])),
                "cn_eq_new_text": bool(tab) and l["cn"] == tab["new_text"],
                "old_eq_cn_before": bool(tab) and fr["cn_before"] == tab["old_text"],
                "old_eq_src_corpus": bool(tab) and tab["old_text"] == src_cn.get((s["script"], l["lineno"])),
                "ok": bool(tab) and l["cn"] == tab["new_text"]
                      and fr["cn_before"] == tab["old_text"]
                      and tab["old_text"] == src_cn.get((s["script"], l["lineno"])),
            })
res["A3_value_checks"] = value_checks
res["A3_values_ok"] = bool(value_checks) and all(v["ok"] for v in value_checks)
res["A3_term_later_waived"] = term_later_waived
res["A3_term_boundary"] = dict(term_boundary)
res["A3_titles_from_table"] = all(
    (not s["title_variants"]) or all(t["cn"] for t in s["title_variants"]) for s in scenes)
# 账目由表内容推导：范围内条目 = 生效 + 门控排除 + 未命中（未命中必须为 0）；
# `A3_accounted` 已保证 `生效 + 门控 == 范围内`，故不再写死条数常量（ISSUE-20260930-12）。
res["A3_pass"] = (len(otv_rows) > 0 and len(gated) == 0
                  and not unhit and res["A3_accounted"] and not kana_lines
                  and not quote_bad and res["A3_values_ok"])

# ---- A4 取文来源可审计
od = collections.Counter(); base = collections.Counter(); ts = collections.Counter()
am = collections.Counter(); sk = collections.Counter(); ly = collections.Counter()
for s in scenes:
    ts[s["text_source"]] += 1
    sk[s["source_kind"]] += 1
    for l in s["lines"]:
        od[l["cn_origin"]] += 1
        base[l["cn_base"]] += 1
        am[l["align_method"]] += 1
        ly[tuple(l["layers"])] += 1
res["A4_cn_origin"] = dict(od)
res["A4_cn_base"] = dict(base)
res["A4_layers"] = {"|".join(k): v for k, v in ly.items()}
res["A4_text_source"] = dict(ts)
res["A4_source_kind"] = dict(sk)
res["A4_align_method"] = dict(am)
# 自洽：empty 行必须 empty_slot=True；非空行 layers[0] == cn_base
bad = [{"script": s["script"], "seq": l["seq"], "origin": l["cn_origin"], "base": l["cn_base"]}
       for s in scenes for l in s["lines"]
       if (l["empty_slot"] != (l["cn_origin"] == "empty")) or
       (not l["empty_slot"] and (not l["layers"] or l["layers"][0] != l["cn_base"]))]
res["A4_inconsistent"] = bad
samples = {}
for s in scenes:
    for l in s["lines"]:
        if l["cn_origin"] in ("otv", "empty") and l["cn_origin"] not in samples:
            samples[l["cn_origin"]] = {"script": s["script"], "seq": l["seq"], "kind": l["kind"],
                                       "speaker": l["speaker"], "voice": l["voice"],
                                       "jp": l["jp"], "cn": l["cn"], "layers": l["layers"]}
res["A4_samples"] = samples
res["A4_pass"] = (set(od) <= ORIGIN_ALLOWED and {"otv", "empty"} <= set(od)
                  and not bad and len(samples) == 2)

# ---- A5 素材命中率（语音 / 去重素材，逐类）
AUD = {}
for r in read_tsv(os.path.join(LST, "音频清单.tsv")):
    AUD[(r["类别"], r["编号"])] = r["输出文件"]
v_tot = sum(1 for s in scenes for l in s["lines"] if l["voice"])
v_hit = sum(1 for s in scenes for l in s["lines"] if l["voice"] and l["audio"])
v_ids = set(l["voice"] for s in scenes for l in s["lines"] if l["voice"])
res["A5_voice_refs"] = v_tot
res["A5_voice_hit"] = v_hit
res["A5_voice_ids"] = len(v_ids)
res["A5_voice_id_unmapped"] = sorted(v for v in v_ids if ("voice", v) not in AUD)
res["A5_voice_files_exist"] = sum(
    1 for s in scenes for l in s["lines"] for p in l["audio"]
    if os.path.isfile(os.path.join(LIB_ROOT, p.replace("/", os.sep))))
a_refs = [(s["script"], a) for s in scenes for a in s["assets"]]
distinct = {}
for sc, a in a_refs:
    distinct.setdefault(a["ref"], a)
d_kind = collections.Counter(a["kind"] for a in distinct.values())
d_hit = collections.Counter(a["kind"] for a in distinct.values() if a["hit"])
d_fileok = sum(1 for a in distinct.values()
               if a["out_relpath"] and os.path.isfile(os.path.join(LIB_ROOT, a["out_relpath"].replace("/", os.sep))))
res["A5_assets_scene_level"] = len(a_refs)
res["A5_assets_scene_hit"] = sum(1 for _, a in a_refs if a["hit"])
res["A5_distinct_total"] = len(distinct)
res["A5_distinct_hit"] = sum(1 for a in distinct.values() if a["hit"])
res["A5_distinct_by_kind"] = dict(d_kind)
res["A5_distinct_hit_by_kind"] = dict(d_hit)
res["A5_distinct_files_exist_on_disk"] = d_fileok
res["A5_missing"] = sorted(a["ref"] for a in distinct.values() if not a["hit"])
res["A5_se_ids"] = len(set(a["ref"].split("\\")[1] for a in distinct.values() if a["kind"] == "se"))
res["A5_bgm_ids"] = len(set(a["ref"].split("\\")[1] for a in distinct.values() if a["kind"] == "bgm"))
res["A5_movie_refs"] = sorted(a["ref"] for a in distinct.values() if a["kind"] == "movie")
res["A5_pass"] = (v_hit == v_tot and res["A5_voice_files_exist"] == v_hit
                  and not res["A5_voice_id_unmapped"]
                  and res["A5_distinct_hit"] == res["A5_distinct_total"]
                  and d_fileok == res["A5_distinct_total"])

# ---- A6 schema 自洽
REQ_SCENE = ["scene_id", "source", "script", "source_kind", "text_source", "phase", "route",
             "cast", "next", "next_kind", "choices", "line_count", "voice_count",
             "assets", "assets_missing", "stats", "lines"]
REQ_LINE = ["seq", "index", "lineno", "kind", "speaker", "speaker_jp", "voice", "jp", "cn",
            "cn_origin", "cn_base", "align_method", "layers", "fix_refs", "name_replaced",
            "empty_slot", "d14_exception", "audio"]
REQ_ASSET = ["ref", "kind", "out_relpath", "hit"]
bad = []
for s in scenes:
    for k in REQ_SCENE:
        if k not in s or s[k] is None:
            bad.append((s.get("scene_id"), "scene", k))
    for k in ("title_jp", "title_cn", "game_date"):        # 可空字段：必须存在
        if k not in s:
            bad.append((s.get("scene_id"), "scene", k))
    for l in s["lines"]:
        for k in REQ_LINE:
            if k not in l:
                bad.append((s["scene_id"], "line", k))
    for a in s["assets"]:
        for k in REQ_ASSET:
            if k not in a:
                bad.append((s["scene_id"], "asset", k))
    for i, l in enumerate(s["lines"], 1):
        if l["seq"] != i:
            bad.append((s["scene_id"], "seq_order", i))
res["A6_missing_fields"] = bad
res["A6_scene_id_unique"] = len(set(s["scene_id"] for s in scenes)) == len(scenes)
res["A6_scene_id_pattern"] = all(s["scene_id"] == "otv_" + s["script"] for s in scenes)
res["A6_choices_total"] = sum(len(s["choices"]) for s in scenes)
res["A6_next_end"] = sorted(s["script"] for s in scenes if s["next_kind"] == "end")
# W10b：phase 枚举校验（schema.md §三.5 八值域；越界即失败）
res["A6_phase_allowed"] = list(PHASE_ALLOWED)
res["A6_phase_dist"] = dict(collections.Counter(str(s["phase"]) for s in scenes))
res["A6_phase_enum_violations"] = phase_violations(scenes)
res["A6_pass"] = (not bad and res["A6_scene_id_unique"] and res["A6_scene_id_pattern"]
                  and res["A6_choices_total"] == 0
                  and not res["A6_phase_enum_violations"])

# ---- A7 不臆断（可空字段取值 + 未确证语义登记）
res["A7_game_date_set"] = {s["script"]: s["game_date"] for s in scenes if s["game_date"]}
res["A7_game_date_null"] = {s["script"]: None for s in scenes if not s["game_date"]}
res["A7_distinct_dates"] = sorted(set(res["A7_game_date_set"].values()))
res["A7_date_corroborated_in_text"] = [
    {"script": s["script"], "seq": l["seq"], "date": mm.group(0)}
    for s in scenes for l in s["lines"]
    for mm in [__import__("re").search(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日", l["jp"] or "")]
    if mm and l["kind"] != "summary"]
res["A7_empty_slots"] = [{"script": s["script"], "seq": l["seq"], "jp": l["jp"], "cn": l["cn"]}
                         for s in scenes for l in s["lines"] if l["empty_slot"]]
res["A7_index_null_all"] = all(l["index"] is None for s in scenes for l in s["lines"])
res["A7_d14_all_null"] = all(l["d14_exception"] is None for s in scenes for l in s["lines"])
res["A7_title_offset_semantics"] = "脚本内 SceneName 值起始的 0-based 字节偏移（otv 无 R 版 offset 概念）"
res["A7_pass"] = (len(res["A7_game_date_set"]) == 26 and len(res["A7_game_date_null"]) == 5
                  and len(res["A7_empty_slots"]) == 1 and res["A7_index_null_all"]
                  and res["A7_d14_all_null"] and res["A6_choices_total"] == 0)

# ---- A8 引用命名空间可解析（W11h 新增；此前 7 项均未覆盖「引用可解析」）
# 契约：`资源组\剧本\schema.md` §2.1 + `资源组\交接编程组\交接说明.md` C3 ——
# `lines[].audio[]` 与 `assets[].out_relpath` 必须是**素材库相对路径**（`otv/…`），
# 且必须能在 `krkr素材库\` 下 `isfile`。任一不满足即 FAIL。
# 背景：修复前这两类字段写的是原始 PSV 裸路径，在素材库命名空间下 0/1737、0/941
# 可解析，而 `hit` 却拿原始源路径判成 941/941 全 true、`assets_missing[]` 为空 —— 缺口被静默掩盖。
def _libpath(rel):
    return os.path.join(LIB_ROOT, rel.replace("/", os.sep))

lib_audio = [{"script": s["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
             for s in scenes for l in s["lines"] for p in l["audio"]]
lib_assets = [{"script": s["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for s in scenes for a in s["assets"] if a["out_relpath"]]
res["A8_lib_root"] = LIB_ROOT
res["A8_audio_refs"] = len(lib_audio)
res["A8_asset_refs"] = len(lib_assets)
res["A8_audio_not_in_namespace"] = [x for x in lib_audio if not x["out_relpath"].startswith("otv/")]
res["A8_asset_not_in_namespace"] = [x for x in lib_assets if not x["out_relpath"].startswith("otv/")]
res["A8_audio_missing_on_disk"] = [x for x in lib_audio if not os.path.isfile(_libpath(x["out_relpath"]))]
res["A8_asset_missing_on_disk"] = [x for x in lib_assets if not os.path.isfile(_libpath(x["out_relpath"]))]

def _hit_ok(a):
    """hit 必须严格等于「out_relpath 在素材库下存在」；无路径者 hit 必须为 False。"""
    if not a["out_relpath"]:
        return a["hit"] is False
    return bool(a["hit"]) == os.path.isfile(_libpath(a["out_relpath"]))

res["A8_hit_mismatch"] = [{"script": s["script"], "ref": a["ref"], "hit": a["hit"],
                           "out_relpath": a["out_relpath"]}
                          for s in scenes for a in s["assets"] if not _hit_ok(a)]
# assets_missing[] 必须如实 = 「hit=False 的 ref」（含无路径者）
res["A8_assets_missing_declared"] = sorted(r for s in scenes for r in s["assets_missing"])
res["A8_assets_missing_actual"] = sorted(a["ref"] for s in scenes for a in s["assets"] if not a["hit"])
res["A8_assets_missing_consistent"] = (res["A8_assets_missing_declared"] == res["A8_assets_missing_actual"])
res["A8_audio_zero_but_voice_nonempty"] = [
    {"script": s["script"], "seq": l["seq"], "voice": l["voice"]}
    for s in scenes for l in s["lines"] if l["voice"] and not l["audio"]]
res["A8_pass"] = (not res["A8_audio_not_in_namespace"] and not res["A8_asset_not_in_namespace"]
                  and not res["A8_audio_missing_on_disk"] and not res["A8_asset_missing_on_disk"]
                  and not res["A8_hit_mismatch"] and res["A8_assets_missing_consistent"])

res["ALL_PASS"] = all(res[k] for k in ["A1_pass", "A2_pass", "A3_pass", "A4_pass",
                                       "A5_pass", "A6_pass", "A7_pass", "A8_pass"])

os.makedirs(STG, exist_ok=True)
json.dump(res, open(os.path.join(STG, "W6e验收.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("A1 场景数=31(M27+P03 4)         :", res["A1_pass"],
      "| 无 2009 同名", res["A1_no_2009_counterpart"] == [])
print("A2 行数守恒                     :", res["A2_pass"], res["A2_total"], "/", res["A2_baseline_total"],
      "| 逐脚本差异", len(res["A2_scene_diff"]), "| 分类", res["A2_by_cat"])
print("A3 修正表(范围内)              :", res["A3_pass"], "| 全表", res["A3_table_total"],
      res["A3_by_source"], "| source=otv", res["A3_in_scope_total"], "命中", res["A3_hit"],
      "门控", len(res["A3_gated_out"]), "| 假名残留行", len(res["A3_kana_residue_lines"]),
      "| 引号遗漏行", len(res["A3_quote_missing_lines"]))
print("   A3 term_unify 层边界文本来源  :", res["A3_term_boundary"],
      "| later_layers_touched 豁免", res["A3_term_later_waived"], "处")
print("A4 取文可审计                   :", res["A4_pass"], res["A4_cn_origin"], res["A4_layers"],
      "| 不一致", len(res["A4_inconsistent"]))
print("A5 素材命中                     :", res["A5_pass"],
      "| 语音", res["A5_voice_hit"], "/", res["A5_voice_refs"], "（编号", res["A5_voice_ids"], "）",
      "| 去重素材", res["A5_distinct_hit"], "/", res["A5_distinct_total"],
      res["A5_distinct_by_kind"], "| 磁盘存在", res["A5_distinct_files_exist_on_disk"],
      "| SE/BGM 编号", res["A5_se_ids"], "/", res["A5_bgm_ids"], "| 缺失", res["A5_missing"])
print("A6 schema 自洽                  :", res["A6_pass"], "| 缺字段", len(bad),
      "| id 唯一", res["A6_scene_id_unique"], "| choices", res["A6_choices_total"],
      "| end 场景", res["A6_next_end"], "| phase 越界", len(res["A6_phase_enum_violations"]),
      res["A6_phase_dist"])
print("A7 不臆断                       :", res["A7_pass"], "| 有日期", len(res["A7_game_date_set"]),
      "无日期", len(res["A7_game_date_null"]), "| 不同日期", res["A7_distinct_dates"],
      "| 空槽", len(res["A7_empty_slots"]), "| index 全 null", res["A7_index_null_all"])
print("A8 引用命名空间可解析(W11h)     :", res["A8_pass"],
      "| 库根", res["A8_lib_root"],
      "| audio", res["A8_audio_refs"], "条 → 越界", len(res["A8_audio_not_in_namespace"]),
      "库内缺", len(res["A8_audio_missing_on_disk"]),
      "| assets", res["A8_asset_refs"], "条 → 越界", len(res["A8_asset_not_in_namespace"]),
      "库内缺", len(res["A8_asset_missing_on_disk"]),
      "| hit 不符", len(res["A8_hit_mismatch"]),
      "| assets_missing 一致", res["A8_assets_missing_consistent"],
      "| voice 非空但 audio=[]", len(res["A8_audio_zero_but_voice_nonempty"]))
print("ALL_PASS =", res["ALL_PASS"])
print("->", os.path.join(STG, "W6e验收.json"))