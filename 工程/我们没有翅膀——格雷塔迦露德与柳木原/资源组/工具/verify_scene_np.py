# -*- coding: utf-8 -*-
r"""
W6f · `scene_np.jsonl` 独立校验器（S6 涅布＊プラス「渡来明日香篇」· 28 场景）

**从磁盘重新读取 `资源组\剧本\scene_np.jsonl`**，与只读源交叉核对，不依赖构建器内存态。
对照 W6a 的 7 项验收口径（本源适配项在报告 §七 逐条说明）。

只读：`工程\涅布＊普拉斯\**`、`资源组\修正\*`、`资源组\krkr素材库\资源总账.json`
只写：`子代理工作区\ISSUE-20260918-06\W6f\W6f验收.json`

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_np.py"
"""
import json, os, re, csv, sys, collections

# W10b：`phase` 值域统一来源（`资源组\剧本\schema.md` §三.5，八值闭集）
sys.dont_write_bytecode = True   # 禁止在工具目录留下 __pycache__（须在 import 兄弟模块之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_violations
import _term_unify                # ISSUE-20260930-12：`term_unify` 校验判据的唯一实现（词形级）

U3000 = "\u3000"                  # 全角空格：构建器 ②.5 删它 ⇒ 传入 ignore_u3000（非 later_layers_touched）

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；产物 scene_np.jsonl 与验收 JSON 读/写本 checkout。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, r"资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, r"修正")                            # 修正表：以本分支副本为准
SCENE = os.path.join(RES_LOCAL, r"剧本\scene_np.jsonl")            # 产物读本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6f")   # 写本 checkout
NP   = os.path.join(DATA_ROOT, r"工程\涅布＊普拉斯")
CORPUS = os.path.join(NP, r"语料\明日香线_原文.json")
TRANS = [os.path.join(NP, r"翻译工作区\分块%d_译文.json" % i) for i in (1, 2, 3)]
REFS = os.path.join(NP, r"素材提取\明日香线_引用清单.json")
VOICE_MISS = os.path.join(NP, r"素材提取\音频\语音缺失清单.tsv")
BP_DIR = os.path.join(NP, r"解包\data01100.arc")
LEDGER = os.path.join(RES, r"krkr素材库\资源总账.json")
LIB_ROOT = os.path.join(RES, r"krkr素材库")          # 素材库根 = 引用命名空间基准（W11h）


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误读/误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))


_assert_in_checkout(SCENE, "scene_np.jsonl")
TABLES = [os.path.join(FIX, f) for f in ("修正表_B1B3.tsv", "修正表_B1B3_扩展.tsv",
                                         "修正表_新增场景mig重译.tsv",
                                         "修正表_np说话人译名.tsv",
                                         # ISSUE-20260930-12：2026-09-30 用户术语裁决表
                                         #（fix_type=term_unify；本表当前无 np 行，纳入以便
                                         # 未来出现 np 行时按词形级判据复核，而非误判为泄漏）
                                         "修正表_裁决20260930.tsv",
                                         # ISSUE-20261009-10：`鷹志`（繁）→`鹰志`（简）词形级归一
                                         #（24 条，source=np，fix_type=term_unify）
                                         "修正表_鹰志简繁.tsv")]
SOURCE = "np"
ENGINE_ERR = "指定されたラベルは見つかりませんでした。"
ALL_SCRIPTS = ["a01_a0","a01_b0","a01_c0","a02_a0","a02_b0","a03_a0","a03_b0",
               "a04_a0","a04_a1","a04_a2","a04_a3","a04_a4","a04_b0",
               "a05_a0","a05_b0","a05_b1","a05_c0","a05_c1","a05_d0","a05_e0",
               "a06_a0","a06_b1","a06_b2","a06_b3","a06_b4","a06_c0",
               "start_oretuba","end_oretuba"]
REQUIRED_SCENE = ["scene_id","source","script","source_kind","text_source","title_jp","title_cn",
                  "title_variants","game_date","game_dates","phase","route","cast","next",
                  "next_kind","choices","line_count","voice_count","assets","assets_missing",
                  "stats","lines"]
REQUIRED_LINE = ["seq","index","lineno","kind","speaker","speaker_jp","voice","jp","cn",
                 "cn_base","cn_origin","align_method","layers","fix_refs","name_replaced",
                 "empty_slot","d14_exception","audio"]

def read_tsv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def w(s):
    sys.stdout.write(s + "\n"); sys.stdout.flush()

R = {}

# ---------------------------------------------------------------- 载入
scenes = [json.loads(ln) for ln in open(SCENE, encoding="utf-8") if ln.strip()]
corpus = json.load(open(CORPUS, encoding="utf-8"))
trans = {}
for p in TRANS:
    for x in json.load(open(p, encoding="utf-8")):
        trans[(x["file"], x["idx"])] = x["text"]
refs = json.load(open(REFS, encoding="utf-8"))
ledger = json.load(open(LEDGER, encoding="utf-8"))
np_voice = {e["orig_name"].rsplit(".", 1)[0].lower(): e["out_relpath"]
            for e in ledger["entries"] if e["source"] == SOURCE and e["kind"] == "voice"}
np_by_kind = collections.defaultdict(dict)
for e in ledger["entries"]:
    if e["source"] == SOURCE:
        np_by_kind[e["kind"]][e["orig_name"].rsplit(".", 1)[0].lower()] = e["out_relpath"]
voice_miss = {r["语音ID"] for r in read_tsv(VOICE_MISS)}
corr_rows = []
for _t in TABLES:
    for _r in read_tsv(_t):
        _r["_table"] = os.path.basename(_t); corr_rows.append(_r)

by_file = collections.OrderedDict()
for x in corpus:
    by_file.setdefault(x["file"], []).append(x)

# ---------------------------------------------------------------- A1 场景数
w("=== A1 场景数 ===")
got = [s["script"] for s in scenes]
a1_missing = sorted(set(ALL_SCRIPTS) - set(got))
a1_extra = sorted(set(got) - set(ALL_SCRIPTS))
a1 = (len(scenes) == 28 and not a1_missing and not a1_extra
      and len(set(s["scene_id"] for s in scenes)) == 28)
w("  场景 %d（预期 28）｜缺 %s ｜多 %s ｜scene_id 唯一 %s"
  % (len(scenes), a1_missing or "无", a1_extra or "无",
     len(set(s["scene_id"] for s in scenes)) == 28))
R["A1_scenes"] = {"pass": a1, "count": len(scenes), "missing": a1_missing, "extra": a1_extra}
w("  A1 = %s" % a1)

# ---------------------------------------------------------------- A2 行数守恒（逐脚本）
w("=== A2 行数守恒 ===")
base = {f: len(v) for f, v in by_file.items()}
base["end_oretuba"] = 0
out = {s["script"]: s["line_count"] for s in scenes}
diff = {f: base.get(f, 0) - out.get(f, 0) for f in set(base) | set(out)}
diff_nz = {k: v for k, v in diff.items() if v != 0}
tot = sum(out.values())
kind_base = collections.Counter(x["kind"] for x in corpus)
kind_out = collections.Counter(l["kind"] for s in scenes for l in s["lines"])
a2 = (tot == len(corpus) == 1961 and not diff_nz and kind_base == kind_out)
w("  总行 %d（语料 %d）｜逐脚本差异 %s｜kind 分布 %s vs 语料 %s"
  % (tot, len(corpus), diff_nz or "全 0", dict(kind_out), dict(kind_base)))
R["A2_lines"] = {"pass": a2, "total": tot, "baseline": len(corpus),
                 "per_script_diff_nonzero": diff_nz, "kind_out": dict(kind_out),
                 "kind_baseline": dict(kind_base)}
w("  A2 = %s" % a2)

# ---------------------------------------------------------------- A3 修正表（命中/门控/未命中）
w("=== A3 修正表 ===")
np_rows = [r for r in corr_rows if r["source"] == SOURCE]
np_file_rows = [r for r in corr_rows if os.path.splitext(r["file"])[0] in set(ALL_SCRIPTS)]
hits = [(fr["table"], s["script"], fr["locator"])
        for s in scenes for l in s["lines"] for fr in l["fix_refs"]]
NP_TABLE = "修正表_np说话人译名.tsv"
np_hits = [h for h in hits if h[0] == NP_TABLE]
other_hits = [h for h in hits if h[0] != NP_TABLE]
# ISSUE-20260930-12：账目改为**表派生**——范围内 = `file` 指向 np 脚本的条目（含未来的
# term_unify np 行）；判据 = 范围内条目全部命中 ＋ scene_np 的 fix_refs 不得指向范围外条目。
# 不再写死「总条数 == 153」这类常量（加入裁决表后必然失效）。
in_scope_rows = [r for r in corr_rows if os.path.splitext(r["file"])[0] in set(ALL_SCRIPTS)]
applied_keys = [(s["script"], fr["locator"], fr.get("table"))
                for s in scenes for l in s["lines"] for fr in l["fix_refs"]]
miss = [(r["_table"], r["file"], r["locator"]) for r in in_scope_rows
        if (os.path.splitext(r["file"])[0], r["locator"], r["_table"]) not in applied_keys]
outside = [k for k in applied_keys
           if not any(os.path.splitext(r["file"])[0] == k[0] and r["locator"] == k[1]
                      and r["_table"] == k[2] for r in in_scope_rows)]
# ISSUE-20260930-12：若 np 范围内出现 `fix_type=term_unify` 的修正行，按其**词形级**判据复核
# （`_term_unify.verify`），而非整句覆盖判据。当前 0 条 ⇒ 本循环不执行（防御性，防未来误判）。
in_scope_files = set(ALL_SCRIPTS)
term_bad = []
term_later_waived = 0                      # `later_layers_touched=True` 兜底命中数（实测应为 0）
term_boundary = collections.Counter()      # 各 fix 层边界文本来源的分布（审计用）
for s in scenes:
    for l in s["lines"]:
        _all = l["fix_refs"]
        for _i, fr in enumerate(_all):
            if fr.get("fix_type") != "term_unify":
                continue
            tab = next((r for r in corr_rows
                        if r["_table"] == fr.get("table") and r["locator"] == fr["locator"]
                        and os.path.splitext(r["file"])[0] in in_scope_files), None)
            if tab is None:
                term_bad.append((s["script"], fr["locator"], "表内无此 term_unify 行")); continue
            # 层边界文本优先取更早者：下一条 fix_ref 的 cn_before ＞ name_replaced[0].before ＞ 最终 cn
            _nr = l.get("name_replaced") or []
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
            okv, why = _term_unify.verify(fr.get("cn_before"), post,
                                          tab["old_text"], tab["new_text"], later,
                                          ignore_u3000=(U3000 in (fr.get("cn_before") or "")))
            if not okv:
                term_bad.append((s["script"], fr["locator"], why))
a3 = (len(in_scope_rows) > 0 and not miss and not outside and not term_bad
      and len(hits) == len(in_scope_rows))
w("  六表合计 %d 条（按 source：%s）" % (len(corr_rows),
    dict(by_src := collections.Counter(r["source"] for r in corr_rows))))
w("  范围内(file→np 脚本) %d 条 ｜ source=np 条目 %d ｜ scene_np.jsonl 内命中 %d（np 表 %d / 他表 %d）"
  % (len(in_scope_rows), len(np_rows), len(hits), len(np_hits), len(other_hits)))
w("  结论：范围内条目全部命中、无范围外泄漏（未命中 %d、范围外 %d）" % (len(miss), len(outside)))
R["A3_corrections"] = {"pass": a3, "total_rows": len(corr_rows), "by_source": dict(by_src),
                       "source_np_rows": len(np_rows), "in_scope_rows": len(in_scope_rows),
                       "file_match_np_rows": len(np_file_rows),
                       "hits_in_scene_np": len(hits), "np_table_hits": len(np_hits),
                       "other_table_hits": len(other_hits),
                       "missing_in_scope": miss, "out_of_scope_applied": outside,
                       "term_unify_bad": term_bad,
                       "term_later_waived": term_later_waived,
                       "term_boundary": dict(term_boundary),
                       "out_of_scope_count": len([r for r in corr_rows if r["source"] != SOURCE]),
                       "out_of_scope_by_source": dict(by_src),
                       "out_of_scope_files": sorted({r["file"] for r in corr_rows})}
w("  A3 = %s" % a3)

# ---------------------------------------------------------------- A4 分支结构 + 取文来源可审计
w("=== A4 分支结构 / 取文可审计 ===")
sc = {s["script"]: s for s in scenes}
menu_titles = [c for c in sc["start_oretuba"]["choices"]
               if c["evidence"].startswith("子篇目菜单条目")]
a04_opts = [c for c in sc["start_oretuba"]["choices"]
            if c["evidence"].startswith("a04 选择支选项")]
a05_opts = [c for c in sc["start_oretuba"]["choices"]
            if c["evidence"].startswith("a05 选择支选项")]
# 独立复核：菜单条目集合 == 26 个剧情脚本（每个恰好一条），且顺序与脚本名一一对应
menu_targets = [c["target"] for c in menu_titles]
menu_bijective = (sorted(menu_targets) == sorted(ALL_SCRIPTS[:26])
                  and len(menu_targets) == len(set(menu_targets)) == 26)
# ISSUE-20260919-06：3 条 np 说话人标签槽经 `修正表_np说话人译名.tsv` retranslate 覆盖
# （cn_origin=retranslate）；ISSUE-20261009-10：24 条 `鷹志` 标签槽经 `修正表_鹰志简繁.tsv`
# term_unify 归一（cn_origin=fix_table）；其余仍为 np；cn_base 必须全为 np。
cn_bases = {s["cn_base"] for s2 in scenes for s in s2["lines"]}
cn_origs = collections.Counter(s["cn_origin"] for s2 in scenes for s in s2["lines"])
cn_origin_ok = (cn_bases == {SOURCE} and set(cn_origs) <= {SOURCE, "retranslate", "fix_table"}
                and cn_origs["retranslate"] == 3 and cn_origs["fix_table"] == 24)
a4 = (len(menu_titles) == 26 and len(a04_opts) == 4 and len(a05_opts) == 4 and menu_bijective
      and sc["a04_a0"]["next"] == ["a04_a1","a04_a2","a04_a3","a04_a4"]
      and sc["a05_a0"]["next"] == ["a05_b0","a05_c0","a05_d0","a05_e0"]
      and sc["a06_a0"]["next"] == ["a06_b1","a06_b2","a06_b3","a06_b4"]
      and all(a["pairing_verified"] for a in a04_opts + a05_opts + menu_titles)
      and cn_origin_ok)
w("  子篇目菜单条目 %d（预期 26，与 26 剧情脚本一一对应 %s）｜a04 选项 %d｜a05 选项 %d｜配对确证 %s"
  % (len(menu_titles), menu_bijective, len(a04_opts), len(a05_opts),
     all(a["pairing_verified"] for a in a04_opts + a05_opts + menu_titles)))
w("  a04_a0.next=%s ｜ a05_a0.next=%s ｜ a06_a0.next=%s"
  % (sc["a04_a0"]["next"], sc["a05_a0"]["next"], sc["a06_a0"]["next"]))
w("  next_kind 分布 %s" % dict(collections.Counter(s["next_kind"] for s in scenes)))
w("  cn_base 全为 np：%s ｜ cn_origin 分布：%s（retranslate=3 为说话人标签槽补译；"
  "fix_table=24 为 `鷹志`→`鹰志` 词形级归一）"
  % (cn_bases == {SOURCE}, dict(cn_origs)))
R["A4_branch"] = {"pass": a4, "menu_entries": len(menu_titles), "a04_options": len(a04_opts),
                  "a05_options": len(a05_opts),
                  "next_kind_dist": dict(collections.Counter(s["next_kind"] for s in scenes)),
                  "choices_total": sum(len(s["choices"]) for s in scenes),
                  "choices_target_null": sum(1 for s in scenes for c in s["choices"] if c["target"] is None),
                  "next_unknown_scripts": [s["script"] for s in scenes
                                           if not s["next"] and s["script"] not in ("a06_c0","end_oretuba")]}
w("  A4 = %s" % a4)

# ---------------------------------------------------------------- A5 素材命中率（逐类）
w("=== A5 素材命中率 ===")
# 独立重扫（口径同 route_refs.py），与 scene_np.jsonl 的 assets 交叉核对
route_re = re.compile(r"^a0[1-6]_|^start_oretuba$|^end_oretuba$")
tok_re = re.compile(rb"[A-Za-z_][A-Za-z0-9_]{2,20}")
SKIP = ("Buriko","DSC","BGV","ASC","SGC","ASD","_Set","_Play","_Get","_Fade","_Wait","_Exec",
        "_Call","_Jump","_If","_Loop","_End","_Msg","_Text","_Win","_Obj","_Sys","_BG","_Chara",
        "_Se","_Bgm","_Voice","_Anime","_Save","_Load","_Return","_Select","_Sound","_Movie",
        "_Quake","_Shake","_Flash","_Def","_Var","_Draw","_Quit","_Stop","_Init","_Bustshot")
def classify_ref(s):
    l = s.lower()
    if re.fullmatch(r"(asu|hiy|skr|tub|ore|sak|y)\d{5}", l): return "voice_id"
    if re.match(r"(asu_|hiy_|skr_|tub_|sak_)", l): return "sprite"
    if l.startswith("bgm"): return "bgm"
    if l.startswith("se"): return "se"
    if l.startswith("bg"): return "bg"
    if re.match(r"^(ore|tub|skr|sak|aki|ec|ef|cin|wipe|end|sec|tn|ban|chi|kaz|kob|kur|mas|mis|miy|sp_)", l):
        return "cg_fx"
    return "other"
per_file = collections.defaultdict(lambda: collections.defaultdict(set))
for fn in sorted(os.listdir(BP_DIR)):
    if not route_re.match(fn): continue
    raw = open(os.path.join(BP_DIR, fn), "rb").read()
    for m in tok_re.finditer(raw):
        s = m.group().decode("ascii")
        if not re.search(r"[0-9_]", s) or s.startswith(SKIP): continue
        per_file[fn][classify_ref(s)].add(s)
tot = collections.defaultdict(set)
for f, d in per_file.items():
    for k, v in d.items(): tot[k] |= v
rescan_ok = {k: len(v) for k, v in tot.items()} == refs["counts"]

REF2KIND = {"sprite": "chr", "cg_fx": "pic", "bg": "pic", "bgm": "bgm", "se": "se", "voice_id": "voice"}
class_res = {}
for cat in ("sprite", "cg_fx", "bg", "bgm", "se", "voice_id"):
    kind = REF2KIND[cat]
    hit = [r for r in sorted(tot[cat]) if r.lower() in np_by_kind.get(kind, {})]
    miss = sorted(set(tot[cat]) - set(hit))
    class_res[cat] = {"total": len(tot[cat]), "hit": len(hit), "missing": miss}
# 与 jsonl 的 assets 交叉
jsonl_refs = {(s["script"], a["ref"]) for s in scenes for a in s["assets"]}
rescan_refs = {(f, r) for f, d in per_file.items() for cat in ("sprite","cg_fx","bg","bgm","se")
               for r in d.get(cat, set())}
assets_consistent = jsonl_refs == rescan_refs
# 语音
v_ids_lines = {l["voice"] for s in scenes for l in s["lines"] if l["voice"]}
v_missing_lines = {l["voice"] for s in scenes for l in s["lines"] if l["voice"] and not l["audio"]}
v_miss_ok = v_missing_lines == voice_miss & v_ids_lines
a5 = (rescan_ok and assets_consistent and class_res["voice_id"]["hit"] == 68
      and len(class_res["voice_id"]["missing"]) == 559 and v_miss_ok)
for cat in ("sprite", "cg_fx", "bg", "bgm", "se", "voice_id"):
    d = class_res[cat]
    w("  %-9s %d/%d 缺失 %d %s" % (cat, d["hit"], d["total"], len(d["missing"]),
                                    d["missing"] if len(d["missing"]) <= 5 else d["missing"][:3] + ["..."]))
w("  重扫与 引用清单.json 一致 %s ｜ jsonl.assets 与重扫一致 %s ｜ 缺失语音与源侧清单一致 %s"
  % (rescan_ok, assets_consistent, v_miss_ok))
R["A5_assets"] = {"pass": a5, "class": class_res, "rescan_matches_manifest": rescan_ok,
                  "jsonl_assets_match_rescan": assets_consistent,
                  "voice_missing_matches_source": v_miss_ok,
                  "voice_ids_referenced": len(tot["voice_id"]),
                  "voice_ids_missing": len(class_res["voice_id"]["missing"]),
                  "voice_ids_present": class_res["voice_id"]["hit"]}
w("  A5 = %s" % a5)

# ---------------------------------------------------------------- A6 schema 自洽
w("=== A6 schema 自洽 ===")
missing_scene, missing_line, bad_json = [], [], 0
for ln in open(SCENE, encoding="utf-8"):
    if not ln.strip(): continue
    try: json.loads(ln)
    except Exception: bad_json += 1
for s in scenes:
    for k in REQUIRED_SCENE:
        if k not in s: missing_scene.append((s.get("script"), k))
    for l in s["lines"]:
        for k in REQUIRED_LINE:
            if k not in l: missing_line.append((s["script"], l.get("seq"), k))
seq_ok = all([l["seq"] for l in s["lines"]] == list(range(1, len(s["lines"]) + 1)) for s in scenes)
lc_ok = all(s["line_count"] == len(s["lines"]) for s in scenes)
vc_ok = all(s["voice_count"] == len({l["voice"] for l in s["lines"] if l["voice"]}) for s in scenes)
phase_bad = phase_violations(scenes)     # W10b：phase 值域（schema.md §三.5 八值闭集）
enum_ok = all(s["next_kind"] in ("linear","branch","end") for s in scenes) and \
          all(l["kind"] in ("dialogue","narration","label","unknown") for s in scenes for l in s["lines"]) and \
          all(c["pairing_verified"] in (True, False) for s in scenes for c in s["choices"]) and \
          not phase_bad
a6 = (not missing_scene and not missing_line and bad_json == 0 and seq_ok and lc_ok and vc_ok and enum_ok)
w("  必填缺失 场景 %d / 行 %d ｜ JSONL 解析失败 %d ｜ seq 连续 %s ｜ line_count 自洽 %s ｜ voice_count 自洽 %s ｜ 枚举合法 %s"
  % (len(missing_scene), len(missing_line), bad_json, seq_ok, lc_ok, vc_ok, enum_ok))
R["A6_schema"] = {"pass": a6, "missing_scene_fields": missing_scene,
                  "missing_line_fields": missing_line, "bad_json_lines": bad_json,
                  "seq_ok": seq_ok, "line_count_ok": lc_ok, "voice_count_ok": vc_ok,
                  "enum_ok": enum_ok,
                  "phase_allowed": list(PHASE_ALLOWED),
                  "phase_enum_violations": phase_bad}
w("  A6 = %s" % a6)

# ---------------------------------------------------------------- A7 不臆断
w("=== A7 不臆断 ===")
dates = [(s["script"], s["game_date"], s["game_dates"]) for s in scenes if s["game_date"]]
# 独立复核：只有 a02_a0 的日文含 ○月○日
date_ev = []
for f, xs in by_file.items():
    for x in xs:
        for m in re.finditer(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日", x["text"]):
            date_ev.append((f, x["idx"], m.group(0)))
null_targets = [(s["script"], c["text_jp"]) for s in scenes for c in s["choices"] if c["target"] is None]
unverified = [(s["script"], c["text_jp"]) for s in scenes for c in s["choices"] if not c["pairing_verified"]]
empty = sum(1 for s in scenes for l in s["lines"] if l["empty_slot"])
d14 = sum(1 for s in scenes for l in s["lines"] if l["d14_exception"])
noise = [(s["script"], l["seq"]) for s in scenes for l in s["lines"] if l["jp"] == ENGINE_ERR]
a7 = (len(dates) == 1 and dates[0][0] == "a02_a0" and dates[0][1] == "02/11"
      and not null_targets and not unverified and empty == 0 and d14 == 0
      and len(noise) == 27)
w("  game_date 有值场景 %s（独立复核 ○月○日 证据：%s）" % (dates, date_ev))
w("  choices target=null %d ｜ pairing_verified=false %d ｜ 空槽 %d ｜ D14 例外 %d"
  % (len(null_targets), len(unverified), empty, d14))
w("  引擎错误串行（%s）共 %d 行，逐条登记于 _build_stats_np.json" % (ENGINE_ERR[:8] + "…", len(noise)))
w("  未确证后继（next=[] 且非终点）: %s"
  % [s["script"] for s in scenes if not s["next"] and s["script"] not in ("a06_c0","end_oretuba")])
R["A7_no_guess"] = {"pass": a7, "game_date_scenes": dates,
                    "date_evidence_from_corpus": date_ev,
                    "choices_target_null": len(null_targets),
                    "choices_unverified": len(unverified),
                    "empty_slots": empty, "d14_exceptions": d14,
                    "engine_noise_lines": len(noise),
                    "next_empty_non_terminal": [s["script"] for s in scenes
                                                if not s["next"] and s["script"] not in ("a06_c0","end_oretuba")]}
w("  A7 = %s" % a7)

# ---------------------------------------------------------------- A8 引用命名空间可解析（W11h 新增）
w("=== A8 引用命名空间可解析 ===")
# 契约：`资源组\剧本\schema.md` §2.1 + `资源组\交接编程组\交接说明.md` C3 ——
# `lines[].audio[]` 与 `assets[].out_relpath` 必须是素材库相对路径（`np/…`），
# 且必须能在 `krkr素材库\` 下 `isfile`。任一不满足即 FAIL。
def _libpath(rel):
    return os.path.join(LIB_ROOT, rel.replace("/", os.sep))

lib_audio = [{"script": s["script"], "seq": l["seq"], "voice": l["voice"], "out_relpath": p}
             for s in scenes for l in s["lines"] for p in l["audio"]]
lib_assets = [{"script": s["script"], "ref": a["ref"], "out_relpath": a["out_relpath"]}
              for s in scenes for a in s["assets"] if a["out_relpath"]]
a8_audio_ns = [x for x in lib_audio if not x["out_relpath"].startswith("np/")]
a8_asset_ns = [x for x in lib_assets if not x["out_relpath"].startswith("np/")]
a8_audio_miss = [x for x in lib_audio if not os.path.isfile(_libpath(x["out_relpath"]))]
a8_asset_miss = [x for x in lib_assets if not os.path.isfile(_libpath(x["out_relpath"]))]

def _hit_ok(a):
    if not a["out_relpath"]:
        return a["hit"] is False
    return bool(a["hit"]) == os.path.isfile(_libpath(a["out_relpath"]))

a8_hit_bad = [{"script": s["script"], "ref": a["ref"], "hit": a["hit"],
               "out_relpath": a["out_relpath"]}
              for s in scenes for a in s["assets"] if not _hit_ok(a)]
declared = sorted(r for s in scenes for r in s["assets_missing"])
actual = sorted(a["ref"] for s in scenes for a in s["assets"] if not a["hit"])
a8_missing_ok = (declared == actual)
# voice 非空但 audio=[] 的口径（np：无对应素材，属已知缺口，如实登记，不伪造）
a8_v_rows = sum(1 for s in scenes for l in s["lines"] if l["voice"] and not l["audio"])
a8_v_ids = sorted({l["voice"] for s in scenes for l in s["lines"] if l["voice"] and not l["audio"]})
a8 = (not a8_audio_ns and not a8_asset_ns and not a8_audio_miss and not a8_asset_miss
      and not a8_hit_bad and a8_missing_ok)
w("  库根 %s" % LIB_ROOT)
w("  audio %d 条 → 越界 %d ｜ 库内缺 %d ；assets %d 条 → 越界 %d ｜ 库内缺 %d"
  % (len(lib_audio), len(a8_audio_ns), len(a8_audio_miss),
     len(lib_assets), len(a8_asset_ns), len(a8_asset_miss)))
w("  hit 与库内存在性不符 %d ｜ assets_missing 一致 %s" % (len(a8_hit_bad), a8_missing_ok))
w("  voice 非空但 audio=[] ：%d 行 / %d 个唯一 ID（无对应素材，属已知缺口）"
  % (a8_v_rows, len(a8_v_ids)))
w("  A8 = %s" % a8)
R["A8_reference_resolvable"] = {
    "pass": a8, "lib_root": LIB_ROOT,
    "audio_refs": len(lib_audio), "asset_refs": len(lib_assets),
    "audio_not_in_namespace": a8_audio_ns, "asset_not_in_namespace": a8_asset_ns,
    "audio_missing_on_disk": a8_audio_miss, "asset_missing_on_disk": a8_asset_miss,
    "hit_mismatch": a8_hit_bad,
    "assets_missing_declared": declared, "assets_missing_actual": actual,
    "assets_missing_consistent": a8_missing_ok,
    "voice_nonempty_audio_empty_rows": a8_v_rows,
    "voice_nonempty_audio_empty_ids": a8_v_ids,
}

R["ALL_PASS"] = all(R[k]["pass"] for k in R if k.startswith("A"))
os.makedirs(STG, exist_ok=True)
json.dump(R, open(os.path.join(STG, "W6f验收.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
w("")
w("================ ALL_PASS = %s ================" % R["ALL_PASS"])