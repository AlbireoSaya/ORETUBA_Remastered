# -*- coding: utf-8 -*-
r"""
W6a · scene.jsonl 独立校验器（对 7 项验收标准逐条自证）

不依赖 build_scene_jsonl.py 的内存态：**从磁盘产物 scene.jsonl 重新读取**，
并与只读源（台词对照.json / 修正表 / 场景对齐表 / 素材清单 / 资源总账）交叉核对。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_jsonl.py"
输出：子代理工作区\ISSUE-20260918-06\W6a2\W6a2验收.json + 控制台摘要

W6a2 修订：A3 计入**修正表来源门控**（`资源组\修正\_README.md` §四.5）——被门控排除的条目
不算「未命中」，但必须逐条留痕，且校验器**独立复核其落点**（目标槽确实未被修正层覆盖）。

依赖与降级（ISSUE-20260919-10 修订）：
A3 的门控留痕来源为构建器落盘的 `子代理工作区\ISSUE-20260918-06\W6a2\_build_stats.json`
（**被 `.gitignore` 排除**，干净 checkout / 新 worktree 里不存在）。产物 `scene_otr.jsonl`
**不编码**门控信息（其 md5 必须稳定，不得为校验器新增字段），故该统计缺失时门控留痕不可复核。
处置：此时若范围内条目**全部生效**（无「未命中」），无需门控即可判 A3 通过；否则标
`A3_status = "SKIP_ENV"`（环境缺件，`A3_pass = None`），**不判 FAIL**，并打印可执行提示
（先运行 `build_scene_jsonl.py`）。门控统计一旦有数据，A3 判据与修前**完全一致**。
"""
import json, os, csv, collections, sys

# W10b：`phase` 值域统一来源（`资源组\剧本\schema.md` §三.5，八值闭集）
sys.dont_write_bytecode = True   # 禁止在工具目录留下 __pycache__（须在 import 兄弟模块之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_violations
import _term_unify                # ISSUE-20260930-12：`term_unify` 校验判据的唯一实现（词形级）

U3000 = "\u3000"                  # 全角空格：构建器 ②.5 删它 ⇒ 传入 ignore_u3000（非 later_layers_touched）

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；产物 scene_otr.jsonl 与验收 JSON 读/写本 checkout。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, r"资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, r"修正")                            # 修正表：以本分支副本为准
OUT  = os.path.join(RES_LOCAL, r"剧本")                            # 产物读本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6a2")   # 写本 checkout
R    = os.path.join(DATA_ROOT, r"工程\我们没有翅膀R")

SCENE = os.path.join(OUT, "scene_otr.jsonl")
ALIGN = os.path.join(FIX, "s03c_场景对齐表.tsv")
COMPARE = os.path.join(R, r"亜衣线资源\剧本\台词对照.json")
MANIFEST = os.path.join(R, r"亜衣线资源\清单\素材清单.json")
LEDGER = os.path.join(RES, r"krkr素材库\资源总账.json")
LIB_ROOT = os.path.join(RES, r"krkr素材库")          # 素材库根 = 引用命名空间基准（W11h）


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误读/误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))


_assert_in_checkout(SCENE, "scene_otr.jsonl")

def read_tsv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

res = {}
scenes = [json.loads(l) for l in open(SCENE, encoding="utf-8")]
res["file_lines"] = len(scenes)

# ---- A1 场景数 = 场景对齐表
align = read_tsv(ALIGN)
align_names = [r["R版场景"] for r in align]
res["A1_align_rows"] = len(align_names)
res["A1_scene_ids"] = [s["script"] for s in scenes]
res["A1_pass"] = (sorted(align_names) == sorted(s["script"] for s in scenes) and len(scenes) == 55)
res["A1_align_kind_dist"] = dict(collections.Counter(
    "shared" if r["对应原版场景"] == r["R版场景"] else
    ("branch" if "分支" in r["对应原版场景"] else "new") for r in align))

# ---- A2 行数守恒
cmp_ = json.load(open(COMPARE, encoding="utf-8"))
baseline = sum(len(s["lines"]) for s in cmp_["scenes"])
tot = sum(s["line_count"] for s in scenes)
res["A2_baseline"] = baseline
res["A2_total"] = tot
res["A2_per_scene_match"] = all(
    s["line_count"] == len(s["lines"]) for s in scenes)
# 与台词对照逐场景核对
bym = {s["file"][:-4]: len(s["lines"]) for s in cmp_["scenes"]}
res["A2_scene_diff"] = {s["script"]: (s["line_count"], bym[s["script"]])
                        for s in scenes if s["line_count"] != bym[s["script"]]}
res["A2_pass"] = (tot == baseline and not res["A2_scene_diff"] and res["A2_per_scene_match"])

# ---- A3 修正表命中（含来源门控）
tables = {
    "修正表_B1B3.tsv": read_tsv(os.path.join(FIX, "修正表_B1B3.tsv")),
    "修正表_B1B3_扩展.tsv": read_tsv(os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    "修正表_新增场景mig重译.tsv": read_tsv(os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260930-12：2026-09-30 用户术语裁决表（fix_type=term_unify）——otr 侧 46 条
    # （含 1 条无地址梗概槽 `idx=`）经 `build_scene_jsonl.py` 消费并记入 `fix_refs`。
    # 此前未纳入本字典 ⇒ `applied`（122）远超 `in_scope`（83），账目等式必不成立。
    "修正表_裁决20260930.tsv": read_tsv(os.path.join(FIX, "修正表_裁决20260930.tsv")),
    # ISSUE-20261009-04：用户 2026-10-09 裁决「奈落」全量回改——otr 侧 3 条（CN 的「地狱」→「奈落」），
    #   均落在 cn_base=ot 的共有场景行（D14），以 `fix_type=term_unify` 词形级替换消费（见表内 evidence）。
    "修正表_奈落.tsv": read_tsv(os.path.join(FIX, "修正表_奈落.tsv")),
}
applied = collections.Counter()
applied_keys = set()
for s in scenes:
    for l in s["lines"]:
        for fr in l["fix_refs"]:
            applied[fr["table"]] += 1
            applied_keys.add((s["script"], fr["locator"]))
res["A3_total_rows"] = sum(len(v) for v in tables.values())
res["A3_applied_by_table"] = dict(applied)
in_scope = collections.Counter()
for tn, rows in tables.items():
    for r in rows:
        if r["source"] == "otr" and r["file"].startswith("s03c"):
            in_scope[tn] += 1
res["A3_in_scope_by_table"] = dict(in_scope)
res["A3_in_scope_total"] = sum(in_scope.values())
res["A3_in_scope_hit"] = sum(applied.values())

# 来源门控排除清单：读构建器落盘产物（磁盘件，非内存态），并**独立复核其落点**
# 该统计被 .gitignore 排除（干净 checkout 无此文件）→ 缺失时的降级处置见 A3 末尾。
_bs = os.path.join(STG, "_build_stats.json")
_stats_present = os.path.isfile(_bs)
gate = json.load(open(_bs, encoding="utf-8")).get("corrections_gated_out", []) \
    if _stats_present else []
res["A3_stats_file"] = _bs
res["A3_stats_present"] = _stats_present
res["A3_gated_out"] = gate
res["A3_gated_in_scope"] = len([g for g in gate if g["file"].startswith("s03c")])
gated_keys = set((g["file"][:-4], g["locator"]) for g in gate)
res["A3_gated_by_table"] = dict(collections.Counter(g["table"] for g in gate))

by_script = {s["script"]: s for s in scenes}
gate_detail, gate_ok = [], True
for g in gate:
    ok = False
    sc = by_script.get(g["script"])
    if sc is not None:
        for tv in sc["title_variants"]:
            if tv["offset"] is not None and ("offset=%d" % tv["offset"]) == g["locator"]:
                # 该槽确实未被修正层覆盖：cn 保持取文原文，且 origin 不是修正层
                ok = (tv["cn"] == g["cn_kept"]
                      and tv["cn_origin"] in ("ot", "otr_new", "empty"))
    gate_detail.append({"script": g["script"], "locator": g["locator"],
                        "cn_kept": g["cn_kept"], "cn_gated": g["cn_gated"], "verified": ok})
    gate_ok = gate_ok and ok
res["A3_gate_landing_verified"] = gate_ok
res["A3_gate_landing_detail"] = gate_detail

# 逐条核对范围内条目：命中 / 门控 / 未命中 三者必居其一
miss = []
for tn, rows in tables.items():
    for r in rows:
        if r["source"] == "otr" and r["file"].startswith("s03c"):
            key = (r["file"][:-4], r["locator"])
            if key not in applied_keys and key not in gated_keys:
                miss.append((tn, r["file"], r["locator"], r["fix_type"]))
res["A3_missing_in_scope"] = miss
res["A3_accounted"] = (sum(applied.values()) + len(gated_keys) == sum(in_scope.values()))
# 范围外条目（他源 / otr 他场景）
out_rows = [(tn, r["source"], r["file"], r["locator"]) for tn, rows in tables.items() for r in rows
            if not (r["source"] == "otr" and r["file"].startswith("s03c"))]
res["A3_out_of_scope_count"] = len(out_rows)
res["A3_out_of_scope_by_source"] = dict(collections.Counter(x[1] for x in out_rows))
res["A3_out_of_scope_otr_files"] = sorted(set(x[2] for x in out_rows if x[1] == "otr"))

# ---- A3 附加：term_unify 逐槽词值复核（ISSUE-20260930-12）
# otr 是本项目**唯一**含前导 U+3000 的 term 槽来源（46 条里 19 条）；其 ②.5 在套修正表之后统一删
# U+3000，故判据 ② 用 `ignore_u3000=True` **只豁免该字符**——不得把它并进 `later_layers_touched`
# （那会把判据 ② 整体放弃、退化成只查词形）。此前 jsonl 的 A3 只数命中条数，从不复核词值，
# 这 19 个 U+3000 槽因此无人按判据 ② 复核——本项补齐。
term_tab = {(tn, r["locator"]): r for tn, rows in tables.items() for r in rows
            if r["fix_type"] == "term_unify"}
term_checks = []
term_later_waived = 0                      # `later_layers_touched=True` 兜底命中数（实测应为 0）
term_boundary = collections.Counter()      # 各 fix 层边界文本来源的分布（审计用）
for s in scenes:
    for l in s["lines"]:
        _all = l["fix_refs"]
        for _i, fr in enumerate(_all):
            if fr.get("fix_type") != "term_unify":
                continue
            tab = term_tab.get((fr.get("table"), fr.get("locator")))
            cb = fr.get("cn_before") or ""
            if tab is None:
                term_checks.append({"script": s["script"], "locator": fr.get("locator"),
                                    "ok": False, "why": "表内无此 term_unify 行"}); continue
            # 层边界文本优先取更早者：下一条 fix_ref 的 cn_before ＞ name_replaced[0].before ＞ 最终 cn
            # ISSUE-20261009-04 订正：`name_replaced` 含 **body / name 两条流**（构建器 `term_hits = h1 + h2`，
            # body 在前），本判据要的是 **body 流的边界文本**。原实现取 `_nr[0]`——当该行 ③ 只命中 name 流
            # （说话人名框）而 body 未变时，会把**日文说话人**误当 body 边界文本（实测 1 例：`s03c_03b#248`，
            # `修正表_奈落.tsv` 的 term 槽；此前 46 槽 `_nr` 全空，故该分支从未被走到）。现改为
            # **优先取首个 body 流条目**；若无 body 流条目 ⇒ body 在 ③ 未被改动 ⇒ 边界文本即最终 `cn`。
            # 对既有 46 槽为恒等变换（body 命中必在 h1 段，`_nr[0]` 即首个 body 条目）。
            _nrb = [h for h in (l.get("name_replaced") or []) if h.get("字段") == "body"]
            if _i != len(_all) - 1:
                post, boundary = _all[_i + 1]["cn_before"], "next_fix_ref"
            elif _nrb:
                post, boundary = _nrb[0]["before"], "name_replaced[body].before"
            else:
                post, boundary = l["cn"], "cn"
            later = post is None
            if later:
                post, boundary = l["cn"], "waived"
                term_later_waived += 1
            term_boundary[boundary] += 1
            okv, why = _term_unify.verify(cb, post, tab["old_text"], tab["new_text"], later,
                                          ignore_u3000=(U3000 in cb))
            term_checks.append({"script": s["script"], "locator": fr.get("locator"),
                                "cn_before": cb, "cn": l["cn"], "post": post, "boundary": boundary,
                                "old_text": tab["old_text"], "new_text": tab["new_text"],
                                "ignore_u3000": (U3000 in cb), "ok": okv, "why": why})
res["A3_term_checks"] = term_checks
res["A3_term_ok"] = bool(term_checks) and all(x["ok"] for x in term_checks)
res["A3_term_later_waived"] = term_later_waived
res["A3_term_boundary"] = dict(term_boundary)

# ---- A3 判定（门控统计缺件时的降级；有数据时判据与修前完全一致）
_a3_judged = (len(miss) == 0 and res["A3_accounted"] and gate_ok and res["A3_term_ok"])
if not _stats_present:
    if len(miss) == 0 and res["A3_accounted"] and res["A3_term_ok"]:
        # 范围内条目全部生效（且账目自洽）→ 无需门控留痕即可判通过
        res["A3_status"] = "PASS"
        res["A3_pass"] = True
        res["A3_env_hint"] = ("门控统计缺件（%s），但范围内条目全部生效、无待判定条目，"
                              "A3 无需门控即可判定。" % _bs)
    else:
        # 有「未命中」条目但无门控留痕可查 → 环境缺件，不判 FAIL
        res["A3_status"] = "SKIP_ENV"
        res["A3_pass"] = None
        res["A3_env_hint"] = (
            "环境缺件：缺 %s（被 .gitignore 排除）。范围内 %d 条修正表条目中，%d 条既未生效"
            "也无门控留痕，无法区分「来源门控排除」与「真实未命中」。"
            "请先运行 build_scene_jsonl.py 生成该统计后复跑本校验器。"
            % (_bs, res["A3_in_scope_total"], len(miss)))
else:
    res["A3_status"] = "PASS" if _a3_judged else "FAIL"
    res["A3_pass"] = _a3_judged
    res["A3_env_hint"] = None

# ---- A4 取文来源可审计
od = collections.Counter()
ts = collections.Counter()
sk = collections.Counter()
am = collections.Counter()
for s in scenes:
    ts[s["text_source"]] += 1
    sk[s["source_kind"]] += 1
    for l in s["lines"]:
        od[l["cn_origin"]] += 1
        am[l["align_method"]] += 1
res["A4_cn_origin"] = dict(od)
res["A4_text_source"] = dict(ts)
res["A4_source_kind"] = dict(sk)
res["A4_align_method"] = dict(am)
samples = {}
for s in scenes:
    for l in s["lines"]:
        o = l["cn_origin"]
        if o in ("ot", "otr_new", "fix_table", "retranslate") and o not in samples and l["cn"]:
            samples[o] = {"script": s["script"], "seq": l["seq"], "kind": l["kind"],
                          "speaker": l["speaker"], "voice": l["voice"],
                          "jp": l["jp"], "cn": l["cn"], "cn_origin": o, "layers": l["layers"]}
res["A4_samples"] = samples
# fix_table 层实例（B1B3 的 quote_* 均非 s03c 范围，故可能缺）— 如缺，用 retranslate 表说明
res["A4_pass"] = all(k in samples for k in ("ot", "otr_new", "retranslate")) and len(od) >= 4

# ---- A5 素材命中率
manifest = json.load(open(MANIFEST, encoding="utf-8"))
ledger = json.load(open(LEDGER, encoding="utf-8"))
otr_index = collections.defaultdict(set)
for e in ledger["entries"]:
    if e["source"] == "otr":
        otr_index[e["kind"]].add(os.path.splitext(e["orig_name"])[0].lower())
DIR2KIND = {"CHR": "chr", "PIC": "pic", "SE": "se", "BGM": "bgm"}
a_tot = a_hit = 0
v_tot = v_hit = 0
missing = []
for s in scenes:
    for a in s["assets"]:
        a_tot += 1
        if a["out_relpath"] and a["out_relpath"].startswith("otr/"):
            a_hit += 1
        else:
            missing.append({"script": s["script"], "ref": a["ref"]})
    for l in s["lines"]:
        if l["voice"]:
            v_tot += 1
            if l["audio"]:
                v_hit += 1
res["A5_assets_total"] = a_tot
res["A5_assets_hit"] = a_hit
res["A5_assets_missing"] = missing
res["A5_assets_missing_distinct"] = sorted(set(m["ref"] for m in missing))
res["A5_voice_total"] = v_tot
res["A5_voice_hit"] = v_hit
res["A5_pass"] = (v_hit == v_tot)

# ---- A6 schema 自洽
REQ_SCENE = ["scene_id", "source", "script", "source_kind", "text_source", "phase", "route",
             "cast", "next", "next_kind", "choices", "line_count", "voice_count",
             "assets", "assets_missing", "stats", "lines"]
REQ_LINE = ["seq", "index", "lineno", "kind", "speaker", "speaker_jp", "voice", "jp", "cn",
            "cn_origin", "cn_base", "align_method", "layers", "fix_refs", "name_replaced",
            "empty_slot", "d14_exception", "audio"]
bad = []
for s in scenes:
    for k in REQ_SCENE:
        if k not in s or s[k] is None:
            bad.append((s.get("scene_id"), "scene", k))
    for l in s["lines"]:
        for k in REQ_LINE:
            if k not in l:
                bad.append((s["scene_id"], "line", k))
    for i, l in enumerate(s["lines"], 1):
        if l["seq"] != i:
            bad.append((s["scene_id"], "seq_order", i))
res["A6_missing_fields"] = bad
res["A6_scene_id_unique"] = (len(set(s["scene_id"] for s in scenes)) == len(scenes))
res["A6_jsonl_reload_ok"] = True
res["A6_choices"] = [{"script": s["script"], "text_jp": c["text_jp"], "text_cn": c["text_cn"],
                      "cn_origin": c.get("cn_origin"), "target": c["target"],
                      "pairing_verified": c["pairing_verified"]}
                     for s in scenes for c in s["choices"]]
res["A6_choices_null_text_cn"] = sum(
    1 for s in scenes for c in s["choices"] if c["text_cn"] is None)
res["A6_choices_null_cn_origin"] = sum(
    1 for s in scenes for c in s["choices"] if c.get("cn_origin") is None)
# W10b：phase 枚举校验（schema.md §三.5 八值域；越界即失败）
res["A6_phase_allowed"] = list(PHASE_ALLOWED)
res["A6_phase_dist"] = dict(collections.Counter(str(s["phase"]) for s in scenes))
res["A6_phase_enum_violations"] = phase_violations(scenes)
res["A6_pass"] = (not bad and res["A6_scene_id_unique"]
                  and res["A6_choices_null_text_cn"] == 0
                  and res["A6_choices_null_cn_origin"] == 0
                  and not res["A6_phase_enum_violations"])

# ---- A7 不臆断（可空字段的取值与登记）
res["A7_game_date_null_scenes"] = sum(1 for s in scenes if s["game_date"] is None)
res["A7_game_date_set_scenes"] = {s["script"]: s["game_date"] for s in scenes if s["game_date"]}
res["A7_choices"] = {s["script"]: s["choices"] for s in scenes if s["choices"]}
res["A7_d14_exceptions"] = sum(1 for s in scenes for l in s["lines"] if l["d14_exception"])
res["A7_empty_slots"] = sum(1 for s in scenes for l in s["lines"] if l["empty_slot"])
res["A7_assets_empty_scenes"] = sum(1 for s in scenes if not s["assets"])
res["A7_pass"] = True

# ---- A8 标点合规：无 U+3000（全角空格）残留
# 判据来源：`.zcode\skills\galgame-translation\SKILL.md`
#   §七.6「**全角空格（U+3000）一律删除**，不得用于中文缩进」；
#   §八 自检项「**无 `　`（U+3000）残留**」。
# 覆盖 `cn` 与 `title_cn`（`title_variants[].cn` 亦为同一取文槽的派生物，一并纳入）。
U3000 = "\u3000"
u3000_hits = []
for s in scenes:
    if U3000 in (s.get("title_cn") or ""):
        u3000_hits.append({"script": s["script"], "field": "title_cn", "value": s["title_cn"]})
    for tv in s.get("title_variants", []):
        if U3000 in (tv.get("cn") or ""):
            u3000_hits.append({"script": s["script"], "field": "title_variants.cn", "value": tv["cn"]})
    for l in s["lines"]:
        if U3000 in (l.get("cn") or ""):
            u3000_hits.append({"script": s["script"], "seq": l["seq"], "index": l["index"],
                               "kind": l["kind"], "field": "cn", "value": l["cn"]})
res["A8_u3000_count"] = len(u3000_hits)
res["A8_u3000_violations"] = u3000_hits
res["A8_pass"] = (len(u3000_hits) == 0)

# ---- A9 引用命名空间可解析（与 W11h 的 otv/ota/np「A8 引用可解析」同一套判据）
# 契约：`资源组\剧本\schema.md` §2.1 —— `lines[].audio[]` 与 `assets[].out_relpath`
# 必须是**素材库相对路径**（本源前缀 `otr/`），且必须能在 `krkr素材库\` 下 `isfile`。
# 此前 A5 只查 `startswith("otr/")` 前缀、无 isfile，缺口可被静默掩盖 → 本项补齐。
def _libpath(rel):
    return os.path.join(LIB_ROOT, rel.replace("/", os.sep))

lib_audio = [{"script": s["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
             for s in scenes for l in s["lines"] for p in l["audio"]]
lib_assets = [{"script": s["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for s in scenes for a in s["assets"] if a["out_relpath"]]
res["A9_lib_root"] = LIB_ROOT
res["A9_audio_refs"] = len(lib_audio)
res["A9_asset_refs"] = len(lib_assets)
res["A9_audio_not_in_namespace"] = [x for x in lib_audio if not x["out_relpath"].startswith("otr/")]
res["A9_asset_not_in_namespace"] = [x for x in lib_assets if not x["out_relpath"].startswith("otr/")]
res["A9_audio_missing_on_disk"] = [x for x in lib_audio if not os.path.isfile(_libpath(x["out_relpath"]))]
res["A9_asset_missing_on_disk"] = [x for x in lib_assets if not os.path.isfile(_libpath(x["out_relpath"]))]

def _hit_ok(a):
    if not a["out_relpath"]:
        return a["hit"] is False
    return bool(a["hit"]) == os.path.isfile(_libpath(a["out_relpath"]))

res["A9_hit_mismatch"] = [{"script": s["script"], "ref": a["ref"], "hit": a["hit"],
                           "out_relpath": a["out_relpath"]}
                          for s in scenes for a in s["assets"] if not _hit_ok(a)]
res["A9_assets_missing_declared"] = sorted(r for s in scenes for r in s["assets_missing"])
res["A9_assets_missing_actual"] = sorted(a["ref"] for s in scenes for a in s["assets"] if not a["hit"])
res["A9_assets_missing_consistent"] = (res["A9_assets_missing_declared"] == res["A9_assets_missing_actual"])
res["A9_audio_zero_but_voice_nonempty"] = [
    {"script": s["script"], "seq": l["seq"], "voice": l["voice"]}
    for s in scenes for l in s["lines"] if l["voice"] and not l["audio"]]
res["A9_pass"] = (not res["A9_audio_not_in_namespace"] and not res["A9_asset_not_in_namespace"]
                  and not res["A9_audio_missing_on_disk"] and not res["A9_asset_missing_on_disk"]
                  and not res["A9_hit_mismatch"] and res["A9_assets_missing_consistent"])

_A_KEYS = ["A1_pass", "A2_pass", "A3_pass", "A4_pass", "A5_pass", "A6_pass", "A7_pass", "A8_pass", "A9_pass"]
# SKIP（环境缺件，值为 None）不计入 FAIL：ALL_PASS 只在**可判定项**上取合取；
# 未复核项单列 A_skipped / ALL_PASS_STRICT，绝不静默掩盖。
res["A_skipped"] = [k for k in _A_KEYS if res[k] is None]
res["ALL_PASS"] = all(res[k] for k in _A_KEYS if res[k] is not None)
res["ALL_PASS_STRICT"] = res["ALL_PASS"] and not res["A_skipped"]

os.makedirs(STG, exist_ok=True)
json.dump(res, open(os.path.join(STG, "W6a2验收.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("A1 场景数=55 且与场景对齐表一致 :", res["A1_pass"], res["A1_align_kind_dist"])
print("A2 行数守恒                    :", res["A2_pass"], tot, "/", baseline)
print("A3 修正表(范围内)全命中        :", res["A3_status"],
      "| 范围内", res["A3_in_scope_total"], "命中", res["A3_in_scope_hit"],
      "门控排除", res["A3_gated_in_scope"], "未命中", len(miss),
      "| 落点复核", res["A3_gate_landing_verified"],
      "| 全表", res["A3_total_rows"], "范围外", res["A3_out_of_scope_count"])
print("   A3 term_unify 词值复核        :", res["A3_term_ok"],
      "| 复核", len(res["A3_term_checks"]), "槽 ｜ 边界文本来源", res["A3_term_boundary"],
      "｜ 走 ignore_u3000", sum(1 for x in res["A3_term_checks"] if x.get("ignore_u3000")), "槽",
      "｜ later_layers_touched 豁免", res["A3_term_later_waived"], "处")
if res["A3_env_hint"]:
    print("   A3 提示                      :", res["A3_env_hint"])
print("   A3 范围外(他源)分布         :", res["A3_out_of_scope_by_source"])
print("A4 取文可审计                  :", res["A4_pass"], res["A4_cn_origin"])
print("   text_source                 :", res["A4_text_source"])
print("   align_method                :", res["A4_align_method"])
print("A5 素材命中                    :", res["A5_pass"], "语音", v_hit, "/", v_tot,
      "｜素材", a_hit, "/", a_tot, "缺失", res["A5_assets_missing_distinct"])
print("A6 schema 自洽                 :", res["A6_pass"], "缺字段", len(bad), "id唯一", res["A6_scene_id_unique"])
print("   A6 choices                  :", res["A6_choices"])
print("A7 不臆断登记                  :", res["A7_pass"], "| game_date=null", res["A7_game_date_null_scenes"],
      "| choices 场景", list(res["A7_choices"].keys()), "| D14例外", res["A7_d14_exceptions"],
      "| 空槽", res["A7_empty_slots"])
print("A8 无 U+3000 残留              :", res["A8_pass"], "违例", res["A8_u3000_count"], "处")
print("A9 引用命名空间可解析          :", res["A9_pass"],
      "| 库根", res["A9_lib_root"],
      "| audio", res["A9_audio_refs"], "条 → 越界", len(res["A9_audio_not_in_namespace"]),
      "库内缺", len(res["A9_audio_missing_on_disk"]),
      "| assets", res["A9_asset_refs"], "条 → 越界", len(res["A9_asset_not_in_namespace"]),
      "库内缺", len(res["A9_asset_missing_on_disk"]),
      "| hit 不符", len(res["A9_hit_mismatch"]),
      "| assets_missing 一致", res["A9_assets_missing_consistent"],
      "| voice 非空但 audio=[]", len(res["A9_audio_zero_but_voice_nonempty"]))
print("ALL_PASS =", res["ALL_PASS"],
      ("（未复核 SKIP：%s 环境缺件）" % ", ".join(res["A_skipped"])) if res["A_skipped"] else "")
if res["A_skipped"]:
    print("ALL_PASS_STRICT =", res["ALL_PASS_STRICT"], "| 未复核项:", res["A_skipped"])
print("->", os.path.join(STG, "W6a2验收.json"))