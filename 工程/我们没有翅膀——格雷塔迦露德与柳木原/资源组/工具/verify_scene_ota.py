# -*- coding: utf-8 -*-
r"""
W6c · `scene_ota.jsonl` 独立校验器（对 8 项验收标准逐条自证）

**不依赖构建器内存态**：从磁盘 `资源组\剧本\scene_ota.jsonl` 重新读取，
与只读源（`工程\我们没有翅膀 After Story\语料\*`、`修正表_*.tsv`、`资源总账.json`）交叉核对。

**W11h 新增 A8「引用命名空间可解析」**：此前 7 项**均未覆盖**「引用可解析」（A5 只比对
总账 stem 成员资格与 jsonl 自洽，未做文件系统 `isfile`）。A8 逐条核对
`lines[].audio[]` 与 `assets[].out_relpath` 是否落在 `ota/` 命名空间且在 `krkr素材库\`
下真实存在，并如实登记「voice 非空但 audio=[]」的行数/唯一 ID 数（无对应素材的已知缺口）。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_ota.py"
输出：`子代理工作区\ISSUE-20260918-06\W6c\W6c验收.json` + 控制台摘要
"""
import json, os, csv, re, struct, collections, sys

# W10b：`phase` 值域统一来源（`资源组\剧本\schema.md` §三.5，八值闭集）
sys.dont_write_bytecode = True   # 禁止在工具目录留下 __pycache__（须在 import 兄弟模块之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_violations
import _term_unify                # ISSUE-20260930-12：`term_unify` 校验判据的唯一实现（词形级）

U3000 = "\u3000"                  # 全角空格：构建器 ②.5 删它 ⇒ 传入 ignore_u3000（非 later_layers_touched）

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；产物 scene_ota.jsonl 与验收 JSON 读/写本 checkout。
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
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6c")   # 写本 checkout
AS_COR = os.path.join(DATA_ROOT, r"工程\我们没有翅膀 After Story\语料")
AS_RAW = os.path.join(AS_COR, r"原文")

SCENE = os.path.join(OUT, "scene_ota.jsonl")
LIB_ROOT = os.path.join(RES, r"krkr素材库")          # 素材库根 = 引用命名空间基准（W11h）
LEDGER = os.path.join(LIB_ROOT, "资源总账.json")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误读/误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))


_assert_in_checkout(SCENE, "scene_ota.jsonl")

DECL = re.compile(rb"\x01\x01(..)")
LBL  = re.compile(r"^\d{2}_[0-9A-Za-z]+$")
DATE_RE = re.compile(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日")


def read_tsv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


res = {}
scenes = [json.loads(l) for l in open(SCENE, encoding="utf-8")]
res["file_lines"] = len(scenes)

ty = json.load(open(os.path.join(AS_COR, "译文.json"), encoding="utf-8"))
choice_rows = json.load(open(os.path.join(AS_COR, "选择支补译.json"), encoding="utf-8"))
ledger = json.load(open(LEDGER, encoding="utf-8"))
led_idx = collections.defaultdict(dict)
for e in ledger["entries"]:
    if e["source"] == "ota":
        led_idx[e["kind"]][os.path.splitext(e["orig_name"])[0].lower()] = e["relpath"] if "relpath" in e else e["out_relpath"]

# ---- A1 场景数 = 172 个 .tob（含 0 消息的 sr.tob，如实标注）
tob = sorted(f[:-4] for f in os.listdir(AS_RAW) if f.endswith(".tob"))
res["A1_tob_count"] = len(tob)
res["A1_scene_scripts"] = [s["script"] for s in scenes]
res["A1_set_equal"] = (sorted(tob) == sorted(s["script"] for s in scenes))
res["A1_empty_msg_scenes"] = [f[:-4] for f in ty if not ty[f]["messages"]]
res["A1_pass"] = (len(scenes) == 172 and res["A1_set_equal"] and res["A1_empty_msg_scenes"] == ["sr"])

# ---- A2 行数守恒（逐文件）
base_tot = sum(len(v["messages"]) for v in ty.values())
base_line = sum(1 for v in ty.values() for m in v["messages"] if m["kind"] == "line")
base_title = sum(1 for v in ty.values() for m in v["messages"] if m["kind"] == "title")
tot = sum(s["line_count"] for s in scenes)
bym = {f[:-4]: len(v["messages"]) for f, v in ty.items()}
diff = {s["script"]: (s["line_count"], bym[s["script"]]) for s in scenes
        if s["line_count"] != bym[s["script"]]}
res["A2_baseline"] = base_tot
res["A2_baseline_body"] = base_line
res["A2_baseline_title"] = base_title
res["A2_total"] = tot
res["A2_scene_diff"] = diff
res["A2_kind_dist"] = dict(collections.Counter(l["kind"] for s in scenes for l in s["lines"]))
res["A2_pass"] = (tot == base_tot and not diff
                  and all(s["line_count"] == len(s["lines"]) for s in scenes)
                  and (res["A2_kind_dist"].get("title", 0) == base_title)
                  and (res["A2_kind_dist"].get("dialogue", 0) + res["A2_kind_dist"].get("narration", 0) == base_line))

# ---- A3 修正表：source=ota 全部命中；范围外逐条留痕；门控落点复核
tables = {
    "修正表_B1B3.tsv": read_tsv(os.path.join(FIX, "修正表_B1B3.tsv")),
    "修正表_B1B3_扩展.tsv": read_tsv(os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    "修正表_新增场景mig重译.tsv": read_tsv(os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260930-12：2026-09-30 用户术语裁决表（fix_type=term_unify，词形级语义）
    "修正表_裁决20260930.tsv": read_tsv(os.path.join(FIX, "修正表_裁决20260930.tsv")),
    # ISSUE-20261009-04：用户 2026-10-09「奈落」全量回改表（本模块消费其中 source=ota 1 条：11_5b.tob idx=155）
    "修正表_奈落.tsv": read_tsv(os.path.join(FIX, "修正表_奈落.tsv")),
}
for _tn, _rows in tables.items():          # 逐行标注来源表（term_unify 命中需按表定位 fix_ref）
    for _r in _rows:
        _r["_table"] = _tn
applied, applied_keys = collections.Counter(), set()
for s in scenes:
    for l in s["lines"]:
        for fr in l["fix_refs"]:
            applied[fr["table"]] += 1
            applied_keys.add((s["script"], fr["locator"]))
in_scope = [r for _, rows in tables.items() for r in rows if r["source"] == "ota"]
out_scope = [r for _, rows in tables.items() for r in rows if r["source"] != "ota"]
miss = [(r["file"], r["locator"], r["fix_type"]) for r in in_scope
        if (r["file"][:-4], r["locator"]) not in applied_keys]
res["A3_total_rows"] = sum(len(v) for v in tables.values())
res["A3_in_scope_ota"] = len(in_scope)
res["A3_applied_by_table"] = dict(applied)
res["A3_applied_total"] = sum(applied.values())
res["A3_missing_in_scope"] = miss
res["A3_out_of_scope_count"] = len(out_scope)
res["A3_out_of_scope_by_source"] = dict(collections.Counter(r["source"] for r in out_scope))
res["A3_out_of_scope_rows"] = [{"source": r["source"], "file": r["file"], "locator": r["locator"],
                                "kind": r["kind"], "fix_type": r["fix_type"]} for r in out_scope]
# 独立复核：7 条的落点确实被修正层覆盖（cn == new_text 且 cn_origin=fix_table）
by_script = {s["script"]: s for s in scenes}
landing, landing_ok = [], True
term_later_waived = 0                      # `later_layers_touched=True` 兜底命中数（实测应为 0）
term_boundary = collections.Counter()      # 各 fix 层边界文本来源的分布（审计用）
for r in in_scope:
    sc = by_script[r["file"][:-4]]
    tgt = int(r["locator"].split("=")[1])
    l = next((x for x in sc["lines"] if x["index"] == tgt), None)
    # 判据（逐条独立复核）：
    #   ① 定位命中该槽（index + fix_refs.locator）
    #   ② 修正前文本与表内 old_text 的关系：整句覆盖 ⇒ 逐字符相等；
    #      term_unify ⇒ 词形正则命中（`_term_unify.verify`，ISSUE-20260930-12）
    #   ③ 生效层为修正层（cn_origin=fix_table 且 layers 含 fix_table）
    #   ④ 最终 cn：整句覆盖 ⇒ == new_text（或其后过译名替换）；term_unify ⇒ 纯 re.sub 结果
    #      （或其后又过了别的层，如译名替换；U+3000 归一由 `ignore_u3000` 单独豁免）
    if r["fix_type"] == "term_unify":
        refs = l["fix_refs"] if l else []
        ref = next((fr for fr in refs
                    if fr.get("table") == r["_table"] and fr.get("locator") == r["locator"]), None)
        if l is not None and ref is not None:
            # 层边界文本优先取更早者：下一条 fix_ref 的 cn_before ＞ name_replaced 里首个 **body 流**条目的
            # before ＞ 最终 cn。
            # ISSUE-20261009-04 订正（与 verify_scene_jsonl.py 同口径）：`name_replaced` 含 **body / name 两条流**
            # （构建器 `term_hits = h1 + h2`，body 在前），本判据要的是 **body 流的边界文本**。原实现取 `_nr[0]`——
            # 当该行 ③ 只命中 name 流（说话人名框）而 body 未变时，会把**日文说话人**误当 body 边界文本
            # （第 1 例实测于 verify_scene_jsonl 的 `s03c_03b#248`；本器当前数据不触发，属同类潜在缺陷的保守对齐）。
            # 现改为**优先取首个 body 流条目**；若无 body 流条目 ⇒ body 在 ③ 未被改动 ⇒ 边界文本即最终 `cn`。
            _i = refs.index(ref)
            _nrb = [h for h in (l.get("name_replaced") or []) if h.get("字段") == "body"]
            if _i != len(refs) - 1:
                post, boundary = refs[_i + 1]["cn_before"], "next_fix_ref"
            elif _nrb:
                post, boundary = _nrb[0]["before"], "name_replaced[body].before"
            else:
                post, boundary = l["cn"], "cn"
            later = post is None
            if later:
                post, boundary = l["cn"], "waived"
                term_later_waived += 1
            term_boundary[boundary] += 1
        else:
            post, boundary, later = None, "no_slot", True
        okv, _why = _term_unify.verify((ref or {}).get("cn_before"), post,
                                       r["old_text"], r["new_text"], later,
                                       ignore_u3000=(U3000 in ((ref or {}).get("cn_before") or "")))
        ok = (l is not None and ref is not None
              and l["cn_origin"] == "fix_table" and "fix_table" in l["layers"] and okv)
        cn_before = (ref or {}).get("cn_before")
    else:
        ok = (l is not None
              and l["fix_refs"] and l["fix_refs"][0]["locator"] == r["locator"]
              and l["fix_refs"][0]["cn_before"] == r["old_text"]
              and l["cn_origin"] == "fix_table" and "fix_table" in l["layers"]
              and (l["cn"] == r["new_text"] or bool(l["name_replaced"])))
        cn_before = l["fix_refs"][0]["cn_before"] if (l and l["fix_refs"]) else None
    landing.append({"script": sc["script"], "locator": r["locator"],
                    "old_text": r["old_text"], "new_text": r["new_text"],
                    "cn_before": cn_before,
                    "cn": l["cn"] if l else None, "cn_origin": l["cn_origin"] if l else None,
                    "layers": l["layers"] if l else None,
                    "name_replaced": [h["旧写法"] + "→" + h["新写法"] for h in l["name_replaced"]] if l else None,
                    "old_text_matched": bool(okv) if r["fix_type"] == "term_unify"
                                        else bool(l and l["fix_refs"] and l["fix_refs"][0]["cn_before"] == r["old_text"]),
                    "verified": bool(ok)})
    landing_ok = landing_ok and ok
res["A3_landing_detail"] = landing
res["A3_landing_verified"] = landing_ok
res["A3_term_later_waived"] = term_later_waived
res["A3_term_boundary"] = dict(term_boundary)
res["A3_pass"] = (not miss and landing_ok and sum(applied.values()) == len(in_scope))

# ---- A4 选择支对账（40 处记录 / 20 场景 / 57 条选项 / 16 skip）
ch_scenes = [s for s in scenes if s["choices"]]
res["A4_choice_records_source"] = len(choice_rows)
res["A4_choice_scenes"] = len(ch_scenes)
res["A4_choices_total"] = sum(len(s["choices"]) for s in ch_scenes)
res["A4_options_source_total"] = sum(len(r["options"]) for r in choice_rows)
res["A4_options_skipped"] = sum(1 for r in choice_rows for o in r["options"] if o.get("skip"))
res["A4_prompts"] = sum(1 for r in choice_rows if r["prompt"])
res["A4_scene_set"] = sorted(s["script"] for s in ch_scenes)
res["A4_source_set"] = sorted(set(r["file"][:-4] for r in choice_rows))
res["A4_null_text_cn"] = sum(1 for s in ch_scenes for c in s["choices"] if c["text_cn"] is None)
res["A4_null_cn_origin"] = sum(1 for s in ch_scenes for c in s["choices"] if c.get("cn_origin") is None)
res["A4_target_nonnull"] = sum(1 for s in ch_scenes for c in s["choices"] if c["target"] is not None)
res["A4_choices_detail"] = [{"script": s["script"], "text_jp": c["text_jp"], "text_cn": c["text_cn"],
                             "cn_origin": c.get("cn_origin"), "target": c["target"],
                             "pairing_verified": c["pairing_verified"]}
                            for s in ch_scenes for c in s["choices"]]
res["A4_pass"] = (res["A4_choice_records_source"] == 40 and res["A4_scene_set"] == res["A4_source_set"]
                  and res["A4_choices_total"] == res["A4_options_source_total"] - res["A4_options_skipped"]
                  and res["A4_null_text_cn"] == 0 and res["A4_null_cn_origin"] == 0)

# ---- A5 素材命中率（逐条核实「真实缺失」）
# 语音：全部引用 → ota voice 库命中；未命中者须为立绘（CHR）误判，逐条核实
v_ref = v_hit = 0
v_miss = collections.Counter()
for s in scenes:
    for l in s["lines"]:
        if l["voice"]:
            v_ref += 1
            if l["audio"]:
                v_hit += 1
            else:
                v_miss[l["voice"]] += 1
res["A5_voice_refs"] = v_ref
res["A5_voice_hit"] = v_hit
res["A5_voice_miss_refs"] = sum(v_miss.values())
res["A5_voice_miss_distinct"] = len(v_miss)
# 「真实语音缺失」判据：该 token 在**任一源**的 voice 库中存在（即确为语音 ID）却不在 ota voice 库中。
all_voice_stems = collections.defaultdict(set)
for e in ledger["entries"]:
    if e["kind"] == "voice":
        all_voice_stems[e["source"]].add(os.path.splitext(e["orig_name"])[0].lower())
real_miss = sorted(k for k in v_miss
                   if any(k.lower() in s for s in all_voice_stems.values()))
res["A5_voice_real_missing"] = real_miss
# 其余未命中 = 解析器把**非语音声明串**判成了 voice：逐条给出它到底像什么
res["A5_voice_miss_classify"] = {
    k: ("ota/chr 同名条目存在（立绘差分）" if k.lower() in led_idx["chr"]
        else "六源素材库均无同名条目（非语音；未解析的立绘/资源声明串）")
    for k in sorted(v_miss)}
res["A5_voice_miss_is_chr_stem"] = sum(1 for k in v_miss if k.lower() in led_idx["chr"])
res["A5_voice_miss_unresolved"] = sorted(k for k in v_miss if k.lower() not in led_idx["chr"])
# 图像：场景级 assets 的 ref 必须命中 ota/pic
a_tot = sum(len(s["assets"]) for s in scenes)
a_hit = sum(1 for s in scenes for a in s["assets"] if a["hit"])
res["A5_assets_total"] = a_tot
res["A5_assets_hit"] = a_hit
res["A5_assets_missing"] = sorted(set(a["ref"] for s in scenes for a in s["assets"] if not a["hit"]))
res["A5_assets_missing_declared"] = sorted(set(r for s in scenes for r in s["assets_missing"]))
# 语料层原始图像引用数（逐消息）用于对账
raw_img = collections.Counter()
for f, v in ty.items():
    pass
raw_img_refs = 0
for f in ty:
    pass
tj = json.load(open(os.path.join(AS_COR, "台词.json"), encoding="utf-8"))
raw_img_refs = sum(1 for v in tj.values() for m in v["messages"] if m.get("image"))
res["A5_raw_image_refs"] = raw_img_refs
res["A5_pass"] = (not real_miss and not res["A5_assets_missing"])

# ---- A6 schema 自洽
REQ_SCENE = ["scene_id", "source", "script", "source_kind", "text_source", "title_variants",
             "game_dates", "cast", "next", "next_kind", "choices", "line_count", "voice_count",
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
res["A6_phase_route_null"] = [s["script"] for s in scenes if s["phase"] is None or s["route"] is None]
# W10b：phase 枚举校验（schema.md §三.5 八值域，`null` 合法；越界即失败）
res["A6_phase_allowed"] = list(PHASE_ALLOWED)
res["A6_phase_enum_violations"] = phase_violations(scenes)
res["A6_pass"] = (not bad and res["A6_scene_id_unique"]
                  and not res["A6_phase_enum_violations"])

# ---- A7 不臆断
res["A7_game_date_set"] = {s["script"]: s["game_date"] for s in scenes if s["game_date"]}
res["A7_game_date_null"] = sum(1 for s in scenes if s["game_date"] is None)
# 独立复核：有日期的场景，其日文里必须确有显式 ○月○日
gd_bad = []
for s in scenes:
    hits = [m.group(0) for l in s["lines"] for m in DATE_RE.finditer(l["jp"] or "")]
    if s["game_date"] and not hits:
        gd_bad.append(s["script"])
res["A7_game_date_without_evidence"] = gd_bad
res["A7_d14_exceptions"] = sum(1 for s in scenes for l in s["lines"] if l["d14_exception"])
res["A7_empty_slots"] = sum(1 for s in scenes for l in s["lines"] if l["empty_slot"])
res["A7_empty_slot_detail"] = [{"script": s["script"], "seq": l["seq"], "index": l["index"]}
                               for s in scenes for l in s["lines"] if l["empty_slot"]]
res["A7_phase_dist"] = dict(collections.Counter(str(s["phase"]) for s in scenes))
res["A7_route_dist"] = dict(collections.Counter(str(s["route"]) for s in scenes))
res["A7_pass"] = (not gd_bad and res["A7_d14_exceptions"] == 0)

# ---- A8 引用命名空间可解析（W11h 新增；此前 7 项均未覆盖「引用可解析」）
# 契约：`资源组\剧本\schema.md` §2.1 + `资源组\交接编程组\交接说明.md` C3 ——
# `lines[].audio[]` 与 `assets[].out_relpath` 必须是素材库相对路径（`ota/…`），
# 且必须能在 `krkr素材库\` 下 `isfile`。任一不满足即 FAIL。
def _libpath(rel):
    return os.path.join(LIB_ROOT, rel.replace("/", os.sep))

lib_audio = [{"script": s["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
             for s in scenes for l in s["lines"] for p in l["audio"]]
lib_assets = [{"script": s["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for s in scenes for a in s["assets"] if a["out_relpath"]]
res["A8_lib_root"] = LIB_ROOT
res["A8_audio_refs"] = len(lib_audio)
res["A8_asset_refs"] = len(lib_assets)
res["A8_audio_not_in_namespace"] = [x for x in lib_audio if not x["out_relpath"].startswith("ota/")]
res["A8_asset_not_in_namespace"] = [x for x in lib_assets if not x["out_relpath"].startswith("ota/")]
res["A8_audio_missing_on_disk"] = [x for x in lib_audio if not os.path.isfile(_libpath(x["out_relpath"]))]
res["A8_asset_missing_on_disk"] = [x for x in lib_assets if not os.path.isfile(_libpath(x["out_relpath"]))]

def _hit_ok(a):
    if not a["out_relpath"]:
        return a["hit"] is False
    return bool(a["hit"]) == os.path.isfile(_libpath(a["out_relpath"]))

res["A8_hit_mismatch"] = [{"script": s["script"], "ref": a["ref"], "hit": a["hit"],
                           "out_relpath": a["out_relpath"]}
                          for s in scenes for a in s["assets"] if not _hit_ok(a)]
res["A8_assets_missing_declared"] = sorted(r for s in scenes for r in s["assets_missing"])
res["A8_assets_missing_actual"] = sorted(a["ref"] for s in scenes for a in s["assets"] if not a["hit"])
res["A8_assets_missing_consistent"] = (res["A8_assets_missing_declared"] == res["A8_assets_missing_actual"])
# voice 非空但 audio=[] 的口径（ota：无对应素材，属已知缺口，如实登记，不伪造）
res["A8_voice_nonempty_audio_empty_rows"] = sum(1 for s in scenes for l in s["lines"]
                                                if l["voice"] and not l["audio"])
res["A8_voice_nonempty_audio_empty_ids"] = sorted({l["voice"] for s in scenes for l in s["lines"]
                                                   if l["voice"] and not l["audio"]})
res["A8_pass"] = (not res["A8_audio_not_in_namespace"] and not res["A8_asset_not_in_namespace"]
                  and not res["A8_audio_missing_on_disk"] and not res["A8_asset_missing_on_disk"]
                  and not res["A8_hit_mismatch"] and res["A8_assets_missing_consistent"])

res["ALL_PASS"] = all(res[k] for k in
                      ["A1_pass", "A2_pass", "A3_pass", "A4_pass", "A5_pass", "A6_pass", "A7_pass",
                       "A8_pass"])

os.makedirs(STG, exist_ok=True)
json.dump(res, open(os.path.join(STG, "W6c验收.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("A1 场景数=172 且与 172 个 .tob 一致 :", res["A1_pass"],
      "| .tob", res["A1_tob_count"], "| 0 消息场景", res["A1_empty_msg_scenes"])
print("A2 行数守恒                        :", res["A2_pass"],
      "|", tot, "/", base_tot, "（正文 %d + 标题 %d）" % (base_line, base_title),
      "| 逐场景差异", len(diff), "| kind 分布", res["A2_kind_dist"])
print("A3 修正表 source=ota 全命中        :", res["A3_pass"],
      "| 范围内", len(in_scope), "命中", sum(applied.values()), "未命中", len(miss),
      "| 落点复核", res["A3_landing_verified"],
      "| 全表", res["A3_total_rows"], "范围外", res["A3_out_of_scope_count"],
      res["A3_out_of_scope_by_source"])
print("   A3 term_unify 层边界文本来源     :", res["A3_term_boundary"],
      "| later_layers_touched 豁免", res["A3_term_later_waived"], "处")
print("A4 选择支对账                      :", res["A4_pass"],
      "| 记录", res["A4_choice_records_source"], "场景", res["A4_choice_scenes"],
      "选项", res["A4_choices_total"], "（源槽", res["A4_options_source_total"],
      "- skip", res["A4_options_skipped"], "）| 提示", res["A4_prompts"])
print("A5 素材命中                        :", res["A5_pass"],
      "| 语音", v_hit, "/", v_ref, "未命中", res["A5_voice_miss_refs"], "次 /",
      res["A5_voice_miss_distinct"], "个 ID（其中立绘 stem", res["A5_voice_miss_is_chr_stem"],
      "；未解析", res["A5_voice_miss_unresolved"], "；**真实语音缺失", res["A5_voice_real_missing"], "**）",
      "| 图像", a_hit, "/", a_tot, "（原始引用", raw_img_refs, "）")
print("A6 schema 自洽                     :", res["A6_pass"], "| 缺字段", len(bad),
      "| id 唯一", res["A6_scene_id_unique"],
      "| phase/route 为 null 的场景", len(res["A6_phase_route_null"]))
print("A7 不臆断                          :", res["A7_pass"],
      "| game_date 有值", len(res["A7_game_date_set"]), "无值", res["A7_game_date_null"],
      "| 无证据却填日期", gd_bad, "| 空槽", res["A7_empty_slots"],
      "| D14 例外", res["A7_d14_exceptions"])
print("A8 引用命名空间可解析(W11h)         :", res["A8_pass"],
      "| 库根", res["A8_lib_root"],
      "| audio", res["A8_audio_refs"], "条 → 越界", len(res["A8_audio_not_in_namespace"]),
      "库内缺", len(res["A8_audio_missing_on_disk"]),
      "| assets", res["A8_asset_refs"], "条 → 越界", len(res["A8_asset_not_in_namespace"]),
      "库内缺", len(res["A8_asset_missing_on_disk"]),
      "| hit 不符", len(res["A8_hit_mismatch"]),
      "| assets_missing 一致", res["A8_assets_missing_consistent"],
      "| voice 非空但 audio=[] 行", res["A8_voice_nonempty_audio_empty_rows"],
      "唯一 ID", len(res["A8_voice_nonempty_audio_empty_ids"]))
print("ALL_PASS =", res["ALL_PASS"])
print("->", os.path.join(STG, "W6c验收.json"))