# -*- coding: utf-8 -*-
r"""
`verify_schema_enums.py` · 六源 `scene_*.jsonl` 枚举 × 数据一致性自检（只读、幂等、可复跑）

用途
    把 `资源组\剧本\schema.md` 声明的**全部枚举**与六源产物的**实际取值**逐字段对照：
      ① 全局：六源实际取值 ⊆ schema 声明集合（越界即报错）；
      ② 分源：每个源的实际取值 ⊆ 该源在 schema 中登记的取值域（跨源越界即报错）；
      ③ 反向：声明集合中「当前产物不出现」的值逐条列出（保留值 / 待用值，仅提示不报错）。
    退出码 0 = ALL_PASS；非 0 = 有越界（打印逐条越界明细）。

依据
    `资源组\剧本\schema.md` §一（场景字段）/ §二.1（行字段）/ §二.2（选择支）/ §三.2 / §三.2.1
    （`cn_origin` / `align_method`）/ §三.5（`phase`）/ §四.4（`fix_refs[].fix_type`）。
    `资源组\修正\_README.md` §四.5（修正表来源门控映射：取文基准层取值集合的来源）。

设计原则
    * **只读**：不写任何文件、不改任何 `scene_*.jsonl`、不重跑构建器；无副作用、可反复执行。
    * **常量与 schema 同源**：本文件的枚举集合是 `schema.md` 声明的机器可读副本；
      改 schema 时必须同步改本文件（`verify_scene_*.py` 的 `phase` 走 `_schema_enums.py`，本文件覆盖其余字段）。
      **交接点（ISSUE-20260930-12）**：本文件与 `资源组\剧本\schema.md` **§四.6**（`fix_refs[].fix_type`，
      新增 `term_unify`）与 **§三.2**（`cn_origin`，`ot` 侧新增取值 `fix_table`）已同步；
      **schema.md 侧由他人负责**，两侧须保持同一提交内一致——若 schema.md 侧尚未落地，以本文件为准并在
      工程记录中注明差异。
    * **fail loud**：越界不静默、不降级；逐条打印 `源 / 字段 / 值 / 计数 / 首次出现 scene_id`。

复跑：
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_schema_enums.py"
"""
import json
import os
import sys
import collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 资源组\
SCENE_DIR = os.path.join(BASE, "剧本")
SOURCES = ("ot", "otr", "ota", "otp", "otv", "np")

# ---------------------------------------------------------------- 声明集合（= schema.md 的机器可读副本）
# 场景级字段
SCENE_ENUMS = {
    # §三.1 + ot/otp 的按源扩展：`ot` 是本篇自指标（本篇即 2009，shared/branch/new 关系分类不适用）
    "source_kind": {"shared", "branch", "new", "ot"},
    # 取文层代号：s03c 用 ot/otr_new/mixed；其余源用其源代号
    "text_source": {"ot", "otr_new", "mixed", "ota", "otp", "otv", "np"},
    # §三.5 八值域（None = null 合法）
    "phase": {"序", "个人线", "结局", "真相", "主线", "框架", "系统", None},
    "next_kind": {"linear", "branch", "end"},
}
# 行级字段
LINE_ENUMS = {
    # 「源值，未改写」：s03c=title/dialogue/narration；ot/otp=other；otv=summary；np=label/unknown
    "kind": {"title", "dialogue", "narration", "other", "summary", "unknown", "label"},
    # 取文基准层（= _README §四.5 门控映射的右列，加 `empty`）
    "cn_base": {"ot", "otr_new", "ota", "otp", "otv", "np", "empty"},
    "cn_origin": {"ot", "otr_new", "ota", "otp", "otv", "np", "fix_table", "retranslate", "empty"},
    "align_method": {
        "audit", "audit_empty", "jp_exact_fallback", "no_audit_entry", "new_scene_direct", "empty_slot",
        "ot_direct", "otp_direct", "np_direct", "np_engine_noise", "np_speaker_label",
        "np_menu_text", "np_option_string",
    },
}
# 选择支字段（None 合法）
CHOICE_ENUMS = {
    "cn_origin": {"fix_table", "retranslate", "ot", "otr_new", "ota", "otp", "np", None},
}
# 修正引用（当前产物实际出现的 + 声明保留值）
# 注：`speaker_split` / `speaker_translate` 声明于 schema.md §4.6，但**均不进 `fix_refs`**
# （前者修 speaker/voice，后者修 speaker），故在此登记为「声明但当前不出现」的保留值。
FIX_REF_ENUMS = {
    # `term_unify`（ISSUE-20260930-10 / -11 新增，见 schema.md §四.6）：唯一出处
    # `资源组\修正\修正表_裁决20260930.tsv`（123 行 ＝ 第一组 92 ＋ §2.7.4 整族 31）。
    # ★ 该值的 `old_text`/`new_text` **语义与其余 `fix_type` 不同**——
    #   其余值：`old_text`/`new_text` = 该槽整句（整槽覆盖 `cn`）；
    #   `term_unify`：`old_text` = 被替换**词形（正则）**、`new_text` = **替换值**，
    #   消费方式 = `re.sub(old_text, new_text, cn)`（见 `修正\_README.md` §三.3）。
    "fix_type": {"quote_add", "quote_normalize", "space_strip", "marker_strip",
                 "retranslate", "term_unify", "speaker_split", "speaker_translate"},
}

# ---------------------------------------------------------------- 分源取值域（源 × 字段 → 该源合法取值集合）
# 说明：本表是「枚举按源分域」事实的机器可读登记；某源出现本表外的值即报错。
SOURCE_DOMAIN = {
    "source_kind": {
        "ot": {"ot"},
        "otr": {"shared", "branch", "new"},
        "ota": {"new"},
        "otp": {"shared", "new"},
        "otv": {"new"},
        "np": {"new"},
    },
    "text_source": {
        "ot": {"ot"}, "otr": {"ot", "mixed", "otr_new"}, "ota": {"ota"},
        "otp": {"otp"}, "otv": {"otv"}, "np": {"np"},
    },
    "kind": {
        "ot": {"dialogue", "other"},
        "otr": {"title", "dialogue", "narration"},
        "ota": {"title", "dialogue", "narration"},
        "otp": {"dialogue", "other"},
        "otv": {"dialogue", "narration", "summary"},
        "np": {"dialogue", "narration", "label", "unknown"},
    },
    "cn_base": {
        "ot": {"ot"}, "otr": {"ot", "otr_new", "empty"}, "ota": {"ota", "empty"},
        "otp": {"otp"}, "otv": {"otv", "empty"}, "np": {"np"},
    },
    "cn_origin": {
        # ot：`修正表_かるら.tsv`（ISSUE-20260919-09，37 条，fix_type=retranslate）生效
        # → cn_origin=retranslate（`かるら` 按场景世界分译；此前 ot 无修正层取值）
        # ot：`修正表_裁决20260930.tsv`（123 行，fix_type=term_unify）生效
        # → cn_origin=fix_table（ISSUE-20260930-12 补：term_unify 不受 §四.5 来源门控约束，
        #   在 ot 侧同样生效 ⇒ 此前 ot 无 fix_table 取值）
        "ot": {"ot", "fix_table", "retranslate"},
        "otr": {"ot", "otr_new", "fix_table", "retranslate", "empty"},
        "ota": {"ota", "fix_table", "empty"}, "otp": {"otp", "fix_table"},
        "otv": {"otv", "fix_table", "empty"},
        # np：`修正表_np说话人译名.tsv`（3 条，fix_type=retranslate）生效 → cn_origin=retranslate
        # np：`修正表_鹰志简繁.tsv`（ISSUE-20261009-10，24 条，fix_type=term_unify）生效
        #   → cn_origin=fix_table（词形级替换，不受 §四.5 来源门控约束）
        "np": {"np", "retranslate", "fix_table"},
    },
    "align_method": {
        "ot": {"ot_direct"},
        "otr": {"audit", "audit_empty", "jp_exact_fallback", "no_audit_entry",
                "new_scene_direct", "empty_slot"},
        "ota": {"new_scene_direct", "empty_slot"},
        "otp": {"otp_direct"},
        "otv": {"new_scene_direct", "empty_slot"},
        "np": {"np_direct", "np_engine_noise", "np_speaker_label", "np_menu_text", "np_option_string"},
    },
    "phase": {
        "ot": {"序", "个人线", "结局", "真相"},
        "otr": {"序", "个人线", "结局"},
        "ota": {"序", "个人线", "结局", None},
        "otp": {"序", "个人线", "结局", "主线", "框架", "系统"},
        "otv": {"序", "个人线", "结局"},
        "np": {"序", "个人线", "结局"},
    },
    "next_kind": {
        "ot": {"linear", "branch", "end"}, "otr": {"linear", "branch", "end"},
        "ota": {"linear", "branch", "end"}, "otp": {"linear", "branch", "end"},
        "otv": {"linear", "end"}, "np": {"linear", "branch", "end"},
    },
    "choices.cn_origin": {
        "ot": {"ot"}, "otr": {"fix_table"}, "ota": {"ota"}, "otp": {"otp"}, "np": {"np"},
    },
}

# 可空字段的「允许为 null 的源」（数据事实，非缺陷）
NULLABLE_BY_SOURCE = {
    "route": {"ota": "D13 待裁决线 22_*/23_* 共 14 场景 + ota_sr 系统场景，共 15 条 route=null"},
}


def load(src):
    p = os.path.join(SCENE_DIR, "scene_%s.jsonl" % src)
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                yield json.loads(ln)


def norm(v):
    return "<null>" if v is None else v


def main():
    problems = []          # 越界明细
    global_seen = {f: collections.Counter() for f in
                   list(SCENE_ENUMS) + list(LINE_ENUMS) + ["choices.cn_origin", "fix_refs.fix_type"]}
    per_source = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    first_seen = {}
    counts = collections.Counter()

    for src in SOURCES:
        for o in load(src):
            counts[src] += 1
            for fld in SCENE_ENUMS:
                raw = o.get(fld)
                v = norm(raw)
                global_seen[fld][v] += 1
                per_source[src][fld][v] += 1
                first_seen.setdefault((fld, v), "%s:%s" % (src, o.get("scene_id")))
                if raw not in SCENE_ENUMS[fld]:
                    problems.append((src, "scene.%s" % fld, v, o.get("scene_id")))
            for c in o.get("choices", []):
                raw = c.get("cn_origin")
                v = norm(raw)
                global_seen["choices.cn_origin"][v] += 1
                per_source[src]["choices.cn_origin"][v] += 1
                if raw not in CHOICE_ENUMS["cn_origin"]:
                    problems.append((src, "choices[].cn_origin", v, o.get("scene_id")))
            for l in o.get("lines", []):
                for fld in LINE_ENUMS:
                    raw = l.get(fld)
                    v = norm(raw)
                    global_seen[fld][v] += 1
                    per_source[src][fld][v] += 1
                    first_seen.setdefault((fld, v), "%s:%s#%s" % (src, o.get("scene_id"), l.get("seq")))
                    if raw not in LINE_ENUMS[fld]:
                        problems.append((src, "lines[].%s" % fld, v, "%s#%s" % (o.get("scene_id"), l.get("seq"))))
                for fr in l.get("fix_refs", []):
                    raw = fr.get("fix_type")
                    v = norm(raw)
                    global_seen["fix_refs.fix_type"][v] += 1
                    per_source[src]["fix_refs.fix_type"][v] += 1
                    if raw not in FIX_REF_ENUMS["fix_type"]:
                        problems.append((src, "fix_refs[].fix_type", v, "%s#%s" % (o.get("scene_id"), l.get("seq"))))

    # ---- 分源取值域核对
    domain_problems = []
    for fld, bysrc in SOURCE_DOMAIN.items():
        for src, allowed in bysrc.items():
            actual = set(per_source[src][fld])
            extra = actual - {norm(x) for x in allowed}
            for v in sorted(extra):
                domain_problems.append((src, fld, v))

    # ---- 输出
    print("=" * 78)
    print("六源枚举 × 数据一致性自检（只读）")
    print("=" * 78)
    print("场景数：%s ｜ 合计 %d" % (dict(counts), sum(counts.values())))
    print()
    print("-- 逐字段实际取值分布（全局）--")
    declared_lookup = dict(SCENE_ENUMS)
    declared_lookup.update(LINE_ENUMS)
    declared_lookup["choices.cn_origin"] = CHOICE_ENUMS["cn_origin"]
    declared_lookup["fix_refs.fix_type"] = FIX_REF_ENUMS["fix_type"]
    for fld in list(SCENE_ENUMS) + list(LINE_ENUMS) + ["choices.cn_origin", "fix_refs.fix_type"]:
        declared = declared_lookup[fld]
        d = global_seen[fld]
        miss = [norm(x) for x in declared if norm(x) not in d]
        print("  %-22s %s" % (fld, dict(sorted(d.items(), key=lambda kv: -kv[1]))))
        if miss:
            print("  %-22s 声明但当前不出现（保留值）: %s" % ("", sorted(miss)))
    print()
    print("-- 逐字段实际取值分布（分源）--")
    for fld in list(SCENE_ENUMS) + list(LINE_ENUMS) + ["choices.cn_origin"]:
        print("  [%s]" % fld)
        for src in SOURCES:
            d = dict(per_source[src][fld])
            if d:
                print("     %-4s %s" % (src, dict(sorted(d.items(), key=lambda kv: -kv[1]))))
    print()
    print("-- 分源取值域越界 --")
    if domain_problems:
        for src, fld, v in domain_problems:
            print("   [X] %s.%s = %r" % (src, fld, v))
    else:
        print("   无（每个源的实际取值均落在 schema 登记的该源取值域内）")
    print()
    print("-- 全局枚举越界 --")
    if problems:
        for src, fld, v, where in problems[:50]:
            print("   [X] %s %s = %r @ %s" % (src, fld, v, where))
        if len(problems) > 50:
            print("   ... 另有 %d 条" % (len(problems) - 50))
    else:
        print("   无（六源实际取值 ⊆ schema 声明集合，越界数 = 0）")
    print()
    ok = not problems and not domain_problems
    print("ALL_PASS = %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())