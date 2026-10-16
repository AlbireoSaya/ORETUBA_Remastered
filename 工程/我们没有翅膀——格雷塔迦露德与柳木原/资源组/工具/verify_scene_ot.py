# -*- coding: utf-8 -*-
r"""
W6b · `scene_ot.jsonl` 独立校验器（7 项验收自证）

**独立性**：从磁盘重新读取 `scene_ot.jsonl`，与**只读源**（本篇 jsonl / SCRIPT_CN .sob /
三张修正表 / 译名替换表 / 资源总账）交叉核对，**不依赖构建器内存态**。

用法：python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_ot.py"
输出：子代理工作区\ISSUE-20260918-06\W6b\W6b验收.json
"""
import json, os, re, csv, sys, glob, collections

# W10b：`phase` 值域统一来源（`资源组\剧本\schema.md` §三.5，八值闭集）
sys.dont_write_bytecode = True   # 禁止在工具目录留下 __pycache__（须在 import 兄弟模块之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_violations
import _term_unify                # ISSUE-20260930-12：`term_unify` 校验判据的唯一实现（词形级，非整句）

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；产物 scene_ot.jsonl 与验收 JSON 读/写本 checkout。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, "资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, "修正")                             # 修正表：以本分支副本为准
SCENE = os.path.join(RES_LOCAL, "剧本", "scene_ot.jsonl")          # 产物读本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
WS = DATA_ROOT
PRJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
RES = os.path.join(PRJ, "资源组")
STG = os.path.join(WS_LOCAL, "子代理工作区", "ISSUE-20260918-06", "W6b")   # 写本 checkout
OTJ = os.path.join(WS, "工程", "我们没有翅膀", "汉化", "剧情汉化")
SOBD = os.path.join(WS, "工程", "我们没有翅膀", "汉化", "SCRIPT_CN")
LEDGER = os.path.join(RES, "krkr素材库", "资源总账.json")
LIB_ROOT = os.path.join(RES, "krkr素材库")          # 素材库根 = 引用命名空间基准（W11h）


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误读/误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))


_assert_in_checkout(SCENE, "scene_ot.jsonl")

MODULE_GROUPS = ("s00", "s01", "s02", "s03", "s04")
EXCLUDE = ("s03c",)
GROUP_EXPECT = {"s00": 1, "s01": 114, "s02": 83, "s03": 95, "s04": 74}
CORR_SOURCE_TO_BASE = {"otr": "otr_new", "otp": "otp", "ota": "ota", "ot": "ot",
                       "otv": "otv", "np": "np"}
BS = chr(92)
U3000 = "\u3000"                  # 全角空格：构建器 ②.5 删它 ⇒ 传入 ignore_u3000（非 later_layers_touched）

R = {}
def w(s):
    sys.stdout.write(s + "\n"); sys.stdout.flush()

# ---------------------------------------------------------------- 读 scene_ot.jsonl
scenes, nlines = [], 0
with open(SCENE, encoding="utf-8") as f:
    for i, ln in enumerate(f, 1):
        ln = ln.strip()
        if not ln:
            continue
        scenes.append(json.loads(ln)); nlines += 1
w("读入 scene_ot.jsonl：%d 行" % nlines)

# ---------------------------------------------------------------- 源基线
allf = sorted(os.path.basename(p)[:-10] for p in glob.glob(os.path.join(OTJ, "*.jsonl")))
mod = [n for n in allf if n.startswith(MODULE_GROUPS) and not n.startswith(EXCLUDE)]
modset = set(mod)
SRC = {n: [json.loads(l) for l in open(os.path.join(OTJ, n + ".sob.jsonl"), encoding="utf-8")]
       for n in mod}

def file_stem(f):
    for suf in (".tob", ".sob.jsonl", ".sob"):
        if f.endswith(suf):
            return f[:-len(suf)]
    return f

# ================================================================ A1 场景数
w("\n[A1] 场景数 ...")
got = collections.Counter(s["script"].split("_")[0] for s in scenes)
a1_detail = {"expected": GROUP_EXPECT, "actual": dict(got)}
A1 = (len(scenes) == len(mod) == 367 and dict(got) == GROUP_EXPECT
      and {s["script"] for s in scenes} == modset)
a1_detail["scene_set_equal_src"] = ({s["script"] for s in scenes} == modset)
R["A1"] = {"pass": A1, **a1_detail}

# ================================================================ A2 行数守恒
w("[A2] 行数守恒 ...")
bad = []
for s in scenes:
    exp = len(SRC[s["script"]])
    if s["line_count"] != exp or len(s["lines"]) != exp:
        bad.append({"script": s["script"], "scene_line_count": s["line_count"],
                    "lines_len": len(s["lines"]), "src": exp})
tot = sum(s["line_count"] for s in scenes)
base = sum(len(v) for v in SRC.values())
A2 = (not bad) and tot == base
R["A2"] = {"pass": A2, "total": tot, "baseline": base, "mismatch": bad,
           "mismatch_count": len(bad)}

# ================================================================ A3 修正表门控
w("[A3] 修正表来源门控 ...")
corr_rows = []
# ISSUE-20260919-09：新增 `修正表_かるら.tsv`（source=ot，37 条，field=cn，fix_type=retranslate）——
# 本表 `source=ot` 与 `cn_base` 一致 → **应命中**（非门控排除），故 A3 口径由「命中恒为 0」改为
# 「命中数 == 范围内 source=ot 条数」；`source≠ot` 的条目仍按 §四.5 门控排除。
# ISSUE-20260930-12：先加入 2026-09-30 用户术语裁决表（`fix_type=term_unify`，词形级语义）
for tn in ["修正表_B1B3.tsv", "修正表_B1B3_扩展.tsv", "修正表_新增场景mig重译.tsv",
           "修正表_かるら.tsv", "修正表_裁决20260930.tsv",
           # ISSUE-20261009-04：用户 2026-10-09 裁决「奈落」全量回改（source=ot，139 条，retranslate）
           "修正表_奈落.tsv"]:
    for r in csv.DictReader(open(os.path.join(FIX, tn), encoding="utf-8-sig", newline=""),
                            delimiter="\t"):
        # ISSUE-20261009-04b（E3）：与 build_scene_ot.py 同口径——CSV **单元格内换行**归一
        # （`\r\n`→`\n`）。`修正表_奈落.tsv` 有 2 条记录内含换行（RFC4180 引号包裹）；
        # `core.autocrlf=true` 的检出会把单元格内换行一并转成 `\r\n`，不归一会在
        # `cn != new_text` 处误报（对无多行字段的表为恒等变换）。
        r["old_text"] = r["old_text"].replace("\r\n", "\n")
        r["new_text"] = r["new_text"].replace("\r\n", "\n")
        r["_table"] = tn; corr_rows.append(r)
in_scope = [r for r in corr_rows if file_stem(r["file"]) in modset]
out_scope = [r for r in corr_rows if file_stem(r["file"]) not in modset]


def _is_term(r):
    """ISSUE-20260930-12：`term_unify` 是**词形级**替换，判据与整句覆盖类不同。"""
    return r["fix_type"] == "term_unify"


# 独立复算：本模块所有行的 cn_base 集合（应恒为 {'ot'}）
bases = set(l["cn_base"] for s in scenes for l in s["lines"])
hit = [(s["script"], l["lineno"], l["fix_refs"]) for s in scenes for l in s["lines"] if l["fix_refs"]]
hit_refs = sum(len(l["fix_refs"]) for s in scenes for l in s["lines"])
# 门控应排除：范围内、**非 term_unify**、且 source 对应基准 ∉ bases 的条目
# （term_unify 不受 §四.5 来源门控约束，见 `修正\_README.md` §三.3）
gated_expect = [r for r in in_scope
                if not _is_term(r) and CORR_SOURCE_TO_BASE[r["source"]] not in bases]
# 应命中：范围内且（term_unify 一律生效）或（source 对应基准 ∈ bases）的条目
hit_expect = [r for r in in_scope
              if _is_term(r) or CORR_SOURCE_TO_BASE[r["source"]] in bases]
# 独立复算命中落点：逐条核对产物
product = {(s["script"], l["lineno"]): l for s in scenes for l in s["lines"]}
hit_bad = []
term_later_waived = 0                      # `later_layers_touched=True` 兜底命中数（实测应为 0）
term_boundary = collections.Counter()      # 各 fix 层边界文本来源的分布（审计用）
for r in hit_expect:
    m = re.fullmatch(r"script=(.+?)&seq=(\d+)", r["locator"])
    if not m:
        hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "locator 非 ot 形态"})
        continue
    key = (m.group(1), int(m.group(2)))
    l = product.get(key)
    if l is None:
        hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "产物无此槽"}); continue
    cn, org, refs = l["cn"], l["cn_origin"], l["fix_refs"]
    if _is_term(r):
        # 词形级：`_term_unify.verify`（校验器专用）——① cn_before 命中词形；
        # ② 「该 fix 层的输出文本」（**层边界文本**）== re.sub(old_text, new_text, cn_before)。
        #    边界文本优先取**更早**的一个：下一条 fix_ref 的 cn_before（修正表之间），
        #    否则 name_replaced 里首个 **body 流**条目的 before（套完修正表、译名替换之前），否则就是最终 cn。
        #    只有三者皆无边界时才允许 `later_layers_touched=True`（本工程实测 0）。
        #    U+3000 归一由 `ignore_u3000` 单独豁免，不算「别的层」（ISSUE-20260930-12 补）
        ref = next((fr for fr in refs
                    if fr.get("table") == r["_table"] and fr.get("locator") == r["locator"]), None)
        if ref is None:
            hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "fix_refs 未记该表"})
            continue
        _i = refs.index(ref)
        # ISSUE-20261009-04 订正（与 verify_scene_jsonl.py 同口径）：`name_replaced` 含 **body / name 两条流**
        # （构建器 `term_hits = h1 + h2`，body 在前），本判据要的是 **body 流的边界文本**。原实现取 `_nr[0]`——
        # 当该行 ③ 只命中 name 流（说话人名框）而 body 未变时，会把**日文说话人**误当 body 边界文本
        # （第 1 例实测于 verify_scene_jsonl 的 `s03c_03b#248`；本器当前数据不触发，属同类潜在缺陷的保守对齐）。
        # 现改为**优先取首个 body 流条目**；若无 body 流条目 ⇒ body 在 ③ 未被改动 ⇒ 边界文本即最终 `cn`。
        # 对既有数据为恒等变换（body 命中必在 h1 段）。
        _nrb = [h for h in (l.get("name_replaced") or []) if h.get("字段") == "body"]
        if _i != len(refs) - 1:
            post, boundary = refs[_i + 1]["cn_before"], "next_fix_ref"
        elif _nrb:
            post, boundary = _nrb[0]["before"], "name_replaced[body].before"
        else:
            post, boundary = cn, "cn"
        later = post is None                   # 理论兜底：三者皆无边界文本（本工程实测 0 处）
        if later:
            post, boundary = cn, "waived"
            term_later_waived += 1
        term_boundary[boundary] += 1
        okv, why = _term_unify.verify(ref.get("cn_before"), post, r["old_text"], r["new_text"],
                                      later,
                                      ignore_u3000=(U3000 in (ref.get("cn_before") or "")))
        if not okv:
            hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "term_unify: " + why,
                            "boundary": boundary, "cn": cn, "post": post,
                            "want": re.sub(r["old_text"], r["new_text"], ref.get("cn_before") or "")})
            continue
    else:
        # 整句覆盖：原判据，逐字符不变
        if cn != r["new_text"]:
            hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "cn != new_text",
                            "got": cn, "want": r["new_text"]}); continue
    if org not in ("fix_table", "retranslate"):
        hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "cn_origin 未标修正层",
                        "got": org}); continue
    if not any(fr.get("table") == r["_table"] for fr in refs):
        hit_bad.append({"file": r["file"], "locator": r["locator"], "why": "fix_refs 未记该表"})
# 独立复算门控落点：被门控条目的目标脚本在 scene_ot.jsonl 中确实未采用该 new_text
landing_ok = True
landing_bad = []
for r in gated_expect:
    sc = file_stem(r["file"])
    obj = next((s for s in scenes if s["script"] == sc), None)
    if obj is None:
        landing_ok = False; landing_bad.append({"file": r["file"], "why": "场景缺失"}); continue
    # 被门控条目的 new_text 不得出现在该场景任一行的 cn 中作为修正结果
    if any(l["cn"] == r["new_text"] and l["cn_origin"] in ("fix_table", "retranslate")
           for l in obj["lines"]):
        landing_ok = False
        landing_bad.append({"file": r["file"], "locator": r["locator"], "why": "门控条目竟生效"})
A3 = (hit_refs == len(hit_expect) and bases == {"ot"}
      and len(in_scope) == len(gated_expect) + len(hit_expect)
      and len(in_scope) + len(out_scope) == len(corr_rows)
      and landing_ok and not hit_bad)
R["A3"] = {"pass": A3, "corrections_total": len(corr_rows),
           "in_scope": len(in_scope), "out_of_scope": len(out_scope),
           "hits": len(hit), "hit_refs": hit_refs,
           "hit_expected": len(hit_expect), "gated_expected": len(gated_expect),
           "cn_base_set": sorted(bases), "gate_landing_verified": landing_ok,
           "gate_landing_bad": landing_bad, "hit_landing_bad": hit_bad,
           "term_later_waived": term_later_waived, "term_boundary": dict(term_boundary),
           "in_scope_list": [{"table": r["_table"], "source": r["source"], "file": r["file"],
                              "locator": r["locator"], "kind": r["kind"],
                              "fix_type": r["fix_type"], "new_text": r["new_text"],
                              "gate": ("source_gate: 本模块 cn_base 恒为 ot，条目 source=%s 对应 %s"
                                       % (r["source"], CORR_SOURCE_TO_BASE[r["source"]]))
                                      if CORR_SOURCE_TO_BASE[r["source"]] not in bases
                                      else "生效：source=%s 对应 %s ∈ cn_base"
                                           % (r["source"], CORR_SOURCE_TO_BASE[r["source"]])}
                             for r in in_scope],
           "out_of_scope_by_source": dict(collections.Counter(r["source"] for r in out_scope))}

# ================================================================ A4 选择支核对
w("[A4] 选择支核对 ...")
sel_slots = collections.Counter()
sel_scripts = collections.defaultdict(lambda: collections.Counter())
for n in mod:
    for r in SRC[n]:
        if r["sel"]:
            sel_slots[r["sel"]] += 1
            sel_scripts[n][r["sel"]] += 1
ch_scripts = sorted(s["script"] for s in scenes if s["choices"])
ch_opts = sum(len(s["choices"]) for s in scenes)
# 逐脚本对账
recon, bad_ch = [], []
for n in sorted(set(list(sel_scripts.keys()) + ch_scripts)):
    exp = sum(sel_scripts[n].values())
    got_ = len(next((s["choices"] for s in scenes if s["script"] == n), []))
    recon.append({"script": n, "src_sel_slots": exp, "scene_choices": got_,
                  "sel_dist": dict(sel_scripts[n]), "ok": exp == got_})
    if exp != got_:
        bad_ch.append(n)
A4 = (sel_slots[1] == 36 and sel_slots[2] == 18 and len(sel_scripts) == 24
      and ch_opts == 54 and len(ch_scripts) == 24 and not bad_ch)
R["A4"] = {"pass": A4, "src_sel1": sel_slots[1], "src_sel2": sel_slots[2],
           "src_script_count": len(sel_scripts), "scene_choice_scripts": len(ch_scripts),
           "scene_choice_options": ch_opts, "mismatch": bad_ch,
           "task_claim": {"scripts": 26, "sel1": 36, "sel2": 18,
                          "note": "任务书写 26 个脚本；实测 24 个（多出的 2 个见报告 §5.2）"},
           "reconcile": recon}

# ================================================================ A5 素材命中率
w("[A5] 素材命中率 ...")
led = json.load(open(LEDGER, encoding="utf-8"))
idx = collections.defaultdict(dict)
for e in led["entries"]:
    if e["source"] == "ot":
        idx[e["kind"]][os.path.splitext(e["orig_name"])[0].lower()] = e["out_relpath"]
D2K = {"PIC": "pic", "SE": "se", "SYS": "sys", "CHR": "chr", "BGM": "bgm", "VOICE": "voice"}
# 独立复算引用（重扫 .sob）
REF_RE = re.compile(rb"([A-Za-z_]{2,6})[\\/]([A-Za-z0-9_]+)\.(ELG|OGG)")
exp_refs, miss_refs = {}, []
per_kind = collections.Counter()
for n in mod:
    raw = open(os.path.join(SOBD, n + ".sob"), "rb").read()
    seen, order = set(), []
    for m in REF_RE.finditer(raw):
        k = (m.group(1).decode(), m.group(2).decode(), m.group(3).decode())
        if k not in seen:
            seen.add(k); order.append(k)
    exp_refs[n] = order
    for d, stem, ext in order:
        kd = D2K.get(d.upper(), "etc")
        per_kind[kd] += 1
        if not idx.get(kd, {}).get(stem.lower()):
            miss_refs.append({"script": n, "ref": "%s%s%s.%s" % (d, BS, stem, ext), "kind": kd})
asset_mismatch = []
a_tot = a_hit = 0
for s in scenes:
    exp = exp_refs[s["script"]]
    if len(exp) != len(s["assets"]):
        asset_mismatch.append({"script": s["script"], "expected": len(exp),
                               "got": len(s["assets"])})
    a_tot += len(s["assets"])
    a_hit += sum(1 for a in s["assets"] if a["hit"])
    if s["assets_missing"] != [x["ref"] for x in miss_refs if x["script"] == s["script"]]:
        asset_mismatch.append({"script": s["script"], "why": "assets_missing 不一致"})
# 语音
v_ref = v_hit = 0
v_miss = []
for s in scenes:
    for l in s["lines"]:
        if l["voice"]:
            v_ref += 1
            if l["audio"]:
                v_hit += 1
            else:
                v_miss.append({"script": s["script"], "seq": l["seq"], "voice": l["voice"]})
A5 = (not asset_mismatch and len(miss_refs) == sum(len(s["assets_missing"]) for s in scenes))
R["A5"] = {"pass": A5, "assets_total": a_tot, "assets_hit": a_hit,
           "assets_hit_rate": round(100.0 * a_hit / a_tot, 4) if a_tot else 0.0,
           "assets_by_kind": dict(per_kind),
           "asset_missing_list": miss_refs, "asset_mismatch": asset_mismatch,
           "voice_refs": v_ref, "voice_hit": v_hit,
           "voice_hit_rate": round(100.0 * v_hit / v_ref, 4) if v_ref else 0.0,
           "voice_missing_list": v_miss}

# ================================================================ A6 schema 自洽
w("[A6] schema 自洽 ...")
SCENE_REQ = ["scene_id", "source", "script", "source_kind", "text_source", "title_jp",
             "title_cn", "title_variants", "game_date", "game_dates", "phase", "route",
             "cast", "next", "next_kind", "choices", "line_count", "voice_count",
             "assets", "assets_missing", "stats", "lines"]
LINE_REQ = ["seq", "index", "lineno", "kind", "speaker", "speaker_jp", "voice", "jp", "cn",
            "cn_base", "cn_origin", "align_method", "layers", "fix_refs", "name_replaced",
            "empty_slot", "d14_exception", "audio"]
STATS_REQ = ["lines_by_origin", "lines_by_source", "corrections_hit", "name_replace_count",
             "empty_slots", "d14_exceptions"]
missing = []
for s in scenes:
    for k in SCENE_REQ:
        if k not in s:
            missing.append({"scene": s["script"], "field": k})
    for k in STATS_REQ:
        if k not in s.get("stats", {}):
            missing.append({"scene": s["script"], "field": "stats." + k})
    for l in s["lines"]:
        for k in LINE_REQ:
            if k not in l:
                missing.append({"scene": s["script"], "seq": l.get("seq"), "field": k})
    # 必填非空口径：数组可 []，字符串可 ""
    for k in ("scene_id", "source", "script", "source_kind", "text_source", "phase", "route",
              "next_kind", "line_count", "voice_count", "assets", "assets_missing", "stats",
              "title_variants", "game_dates", "cast", "next", "choices", "lines"):
        if s[k] is None:
            missing.append({"scene": s["script"], "field": k, "why": "必填为 null"})
    for l in s["lines"]:
        for k in ("seq", "lineno", "kind", "speaker", "speaker_jp", "voice", "jp", "cn",
                  "cn_base", "cn_origin", "align_method", "layers", "fix_refs",
                  "name_replaced", "empty_slot", "audio"):
            if l[k] is None:
                missing.append({"scene": s["script"], "seq": l["seq"], "field": k,
                                "why": "必填为 null"})
# 逐行 json.loads
jsonl_ok = True
with open(SCENE, encoding="utf-8") as f:
    for ln in f:
        if ln.strip():
            json.loads(ln)
ids = [s["scene_id"] for s in scenes]
dup_ids = [k for k, v in collections.Counter(ids).items() if v > 1]
# 枚举合法性
ENUM = {"source_kind": {"ot"}, "text_source": {"ot", "mixed", "otr_new"},
        "next_kind": {"linear", "branch", "end"}}
enum_bad = []
for s in scenes:
    for k, allowed in ENUM.items():
        if s[k] not in allowed:
            enum_bad.append({"scene": s["script"], "field": k, "value": s[k]})
# W10b：phase 值域改由 schema.md §三.5（八值闭集）统一校验，越界即报错
enum_bad += [{"scene": sid, "field": "phase", "value": v}
             for sid, v in phase_violations(scenes)]
LINE_ENUM = {"kind": {"dialogue", "other"}, "cn_base": {"ot", "empty"},
             "cn_origin": {"ot", "fix_table", "retranslate", "empty"},
             "align_method": {"ot_direct", "empty_slot"}}
for s in scenes:
    for l in s["lines"]:
        for k, allowed in LINE_ENUM.items():
            if l[k] not in allowed:
                enum_bad.append({"scene": s["script"], "seq": l["seq"], "field": k,
                                 "value": l[k]})
A6 = (not missing and not dup_ids and jsonl_ok and not enum_bad
      and all(s["line_count"] == len(s["lines"]) for s in scenes))
R["A6"] = {"pass": A6, "missing_required": missing, "duplicate_scene_ids": dup_ids,
           "jsonl_parse_ok": jsonl_ok, "enum_violations": enum_bad,
           "scene_count": len(scenes)}

# ================================================================ A7 不臆断
w("[A7] 不臆断 ...")
DATE_RE = re.compile("[０-９0-9]{1,2}月[０-９0-9]{1,2}日")
date_bad, date_ok = [], []
for s in scenes:
    exp = []
    for r in SRC[s["script"]]:
        for m in DATE_RE.finditer(r["jp"] or ""):
            exp.append(r["seq"])
    if bool(s["game_dates"]) != bool(exp):
        date_bad.append({"script": s["script"], "game_dates": s["game_dates"], "src_dates": exp})
    if s["game_date"] is not None and not s["game_dates"]:
        date_bad.append({"script": s["script"], "why": "game_date 有值但 game_dates 空"})
    if s["game_dates"]:
        date_ok.append({"script": s["script"], "game_date": s["game_date"],
                        "game_dates": s["game_dates"]})
# choices 的 target/pairing
ch_bad = [{"script": s["script"], "text_jp": c["text_jp"], "target": c["target"]}
          for s in scenes for c in s["choices"] if c["target"] is not None
          or c["pairing_verified"] is not False or c["confirmed"] is not True]
# d14 例外恒 null（本模块取文即 D14 首选源）
d14_bad = [{"script": s["script"], "seq": l["seq"]} for s in scenes for l in s["lines"]
           if l["d14_exception"] is not None]
# speaker 缺失（映射不到中文名字框）
sp_miss = collections.Counter(l["speaker_jp"] for s in scenes for l in s["lines"]
                              if l["speaker_jp"] and not l["speaker"])
# 标题缺失
no_title = [s["script"] for s in scenes if not s["title_jp"]]
# 零目标
zero_next = [s["script"] for s in scenes if not s["next"]]
A7 = (not date_bad and not ch_bad and not d14_bad)
R["A7"] = {"pass": A7, "game_date_bad": date_bad, "scenes_with_date": date_ok,
           "choices_target_null": len(ch_bad) == 0, "choices_bad": ch_bad,
           "d14_exception_non_null": d14_bad,
           "speaker_cn_missing_labels": dict(sp_miss),
           "scenes_without_title": no_title,
           "next_zero": zero_next,
           "next_cross_module": sorted({t for s in scenes for t in s["next"] if t not in modset})}

# ================================================================ A8 引用命名空间可解析
# 契约：`资源组\剧本\schema.md` §2.1 —— `lines[].audio[]` 与 `assets[].out_relpath`
# 必须是**素材库相对路径**（本源前缀 `ot/`），且必须能在 `krkr素材库\` 下 `isfile`。
# 此前 A5 只比对总账 stem 成员资格、无 isfile，缺口可被静默掩盖 → 本项补齐。
w("[A8] 引用命名空间可解析 ...")


def _libpath(rel):
    return os.path.join(LIB_ROOT, rel.replace("/", os.sep))


lib_audio = [{"script": s["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
             for s in scenes for l in s["lines"] for p in l["audio"]]
lib_assets = [{"script": s["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for s in scenes for a in s["assets"] if a["out_relpath"]]
a8_audio_ns = [x for x in lib_audio if not x["out_relpath"].startswith("ot/")]
a8_asset_ns = [x for x in lib_assets if not x["out_relpath"].startswith("ot/")]
a8_audio_disk = [x for x in lib_audio if not os.path.isfile(_libpath(x["out_relpath"]))]
a8_asset_disk = [x for x in lib_assets if not os.path.isfile(_libpath(x["out_relpath"]))]


def _hit_ok(a):
    if not a["out_relpath"]:
        return a["hit"] is False
    return bool(a["hit"]) == os.path.isfile(_libpath(a["out_relpath"]))


a8_hit_mismatch = [{"script": s["script"], "ref": a["ref"], "hit": a["hit"],
                    "out_relpath": a["out_relpath"]}
                   for s in scenes for a in s["assets"] if not _hit_ok(a)]
a8_missing_declared = sorted(r for s in scenes for r in s["assets_missing"])
a8_missing_actual = sorted(a["ref"] for s in scenes for a in s["assets"] if not a["hit"])
a8_missing_ok = (a8_missing_declared == a8_missing_actual)
A8 = (not a8_audio_ns and not a8_asset_ns and not a8_audio_disk and not a8_asset_disk
      and not a8_hit_mismatch and a8_missing_ok)
R["A8"] = {"pass": A8, "lib_root": LIB_ROOT,
           "audio_refs": len(lib_audio), "asset_refs": len(lib_assets),
           "audio_not_in_namespace": a8_audio_ns, "asset_not_in_namespace": a8_asset_ns,
           "audio_missing_on_disk": a8_audio_disk, "asset_missing_on_disk": a8_asset_disk,
           "hit_mismatch": a8_hit_mismatch,
           "assets_missing_declared": a8_missing_declared,
           "assets_missing_actual": a8_missing_actual,
           "assets_missing_consistent": a8_missing_ok,
           "audio_zero_but_voice_nonempty": [
               {"script": s["script"], "seq": l["seq"], "voice": l["voice"]}
               for s in scenes for l in s["lines"] if l["voice"] and not l["audio"]]}

# ================================================================ 汇总
R["ALL_PASS"] = all(R[k]["pass"] for k in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"))
os.makedirs(STG, exist_ok=True)
json.dump(R, open(os.path.join(STG, "W6b验收.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

w("")
w("================ W6b 验收（7 项） ================")
w("A1 场景数 367（s00 1 / s01 114 / s02 83 / s03 95 / s04 74） : %s  %s"
  % (R["A1"]["pass"], R["A1"]["actual"]))
w("A2 行数守恒 %d == %d，逐脚本差异 %d            : %s"
  % (R["A2"]["total"], R["A2"]["baseline"], R["A2"]["mismatch_count"], R["A2"]["pass"]))
w("A3 修正表：合计 %d = 范围内 %d（命中 %d + 门控 %d + 未命中 %d）+ 范围外 %d : %s"
  % (R["A3"]["corrections_total"], R["A3"]["in_scope"], R["A3"]["hits"],
     R["A3"]["gated_expected"],
     R["A3"]["in_scope"] - R["A3"]["hits"] - R["A3"]["gated_expected"],
     R["A3"]["out_of_scope"], R["A3"]["pass"]))
w("     cn_base 集合 %s ｜ 门控落点复核 %s" % (R["A3"]["cn_base_set"],
                                              R["A3"]["gate_landing_verified"]))
w("     term_unify 层边界文本来源 %s ｜ later_layers_touched 豁免 %d 处"
  % (R["A3"]["term_boundary"], R["A3"]["term_later_waived"]))
w("A4 选择支：源 sel=1 %d / sel=2 %d（%d 脚本）；产出 %d 脚本 / %d 选项；差异 %d : %s"
  % (R["A4"]["src_sel1"], R["A4"]["src_sel2"], R["A4"]["src_script_count"],
     R["A4"]["scene_choice_scripts"], R["A4"]["scene_choice_options"],
     len(R["A4"]["mismatch"]), R["A4"]["pass"]))
w("A5 素材 %d/%d（%.2f%%，缺失 %d）｜ 语音 %d/%d（%.2f%%，缺失 %d） : %s"
  % (R["A5"]["assets_hit"], R["A5"]["assets_total"], R["A5"]["assets_hit_rate"],
     len(R["A5"]["asset_missing_list"]), R["A5"]["voice_hit"], R["A5"]["voice_refs"],
     R["A5"]["voice_hit_rate"], len(R["A5"]["voice_missing_list"]), R["A5"]["pass"]))
w("A6 schema：必填缺失 %d ｜ scene_id 唯一 %s ｜ 逐行 json.loads %s ｜ 枚举越界 %d : %s"
  % (len(R["A6"]["missing_required"]), not R["A6"]["duplicate_scene_ids"],
     R["A6"]["jsonl_parse_ok"], len(R["A6"]["enum_violations"]), R["A6"]["pass"]))
w("A7 不臆断：日期不符 %d ｜ choices target 非 null %d ｜ d14 非 null %d : %s"
  % (len(R["A7"]["game_date_bad"]), len(R["A7"]["choices_bad"]),
     len(R["A7"]["d14_exception_non_null"]), R["A7"]["pass"]))
w("     speaker 无中文标签 %d ｜ 无标题场景 %d ｜ 零目标 %d ｜ 跨模块 next %s"
  % (len(R["A7"]["speaker_cn_missing_labels"]), len(R["A7"]["scenes_without_title"]),
     len(R["A7"]["next_zero"]), R["A7"]["next_cross_module"]))
w("A8 引用命名空间可解析：库根 %s ｜ audio %d 条 → 越界 %d 库内缺 %d ｜ assets %d 条 → 越界 %d 库内缺 %d ｜ hit 不符 %d ｜ assets_missing 一致 %s ｜ voice 非空但 audio=[] %d : %s"
  % (R["A8"]["lib_root"], R["A8"]["audio_refs"], len(R["A8"]["audio_not_in_namespace"]),
     len(R["A8"]["audio_missing_on_disk"]), R["A8"]["asset_refs"],
     len(R["A8"]["asset_not_in_namespace"]), len(R["A8"]["asset_missing_on_disk"]),
     len(R["A8"]["hit_mismatch"]), R["A8"]["assets_missing_consistent"],
     len(R["A8"]["audio_zero_but_voice_nonempty"]), R["A8"]["pass"]))
w("")
w("ALL_PASS = %s" % R["ALL_PASS"])