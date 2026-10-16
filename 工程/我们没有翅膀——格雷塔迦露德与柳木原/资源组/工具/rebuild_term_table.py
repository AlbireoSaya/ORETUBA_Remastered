#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W7-3b · 按新米基准重建译名替换表（可复跑、可审计）

仲裁基准（用户 2026-09-18 复裁 D3 修订版）
------------------------------------------
`工程\\我们没有翅膀R\\参照\\中日对照表.json`（57,820 槽，2009 新米参照语料）中
**实际出现的写法**为唯一仲裁。凡四份作品层术语表分歧，一律取新米实测写法。

计数口径
--------
* 新米仲裁（body）：槽 `jp` 含日文原词 needle → 统计该槽 `cn` 含候选写法的**槽数**。
  即「原文出现该词时，译文用了哪个写法」。这是方向判定的主证据。
* 新米仲裁（name）：槽 `speaker`(日文) 含 needle → 统计 `speaker_cn` 分布（名字框流）。
* 旧写法实测：六源语料逐源统计候选写法槽数，分 body / name 两流。
* 槽级命中：同槽同串多次仍计 1。
* 说话人标签（引擎键）不计；R 版 / PSV 名字框单列为 name 流。

纪律
----
* 只读源：六源工程目录一个字节都不改。
* 中间产物写 `子代理工作区\\ISSUE-20260918-06\\W7-3b\\`。
* 本脚本不写任何术语表正文；只产出统计事实与 TSV。

用法
----
    python rebuild_term_table.py
    python rebuild_term_table.py --tsv <path> --json <path>
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

ROOT = r"E:\ZCode Workspace\Galgame"
CORPUS = os.path.join(ROOT, r"工程\我们没有翅膀R\参照\中日对照表.json")
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import build_term_replace as btr  # 复用六源迭代器（只读）

TSV_DEFAULT = r"工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\修正\译名替换表.tsv"
JSON_DEFAULT = r"子代理工作区\ISSUE-20260918-06\W7-3b\arbitration_report.json"


def P(rel):
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


# ---------------------------------------------------------------------------
# 术语规格
#   jp     : 日文原词 needle（jp 门控）
#   cands  : 候选中文写法（含旧写法与新米写法）
#   cat    : 类别
#   note   : 备注（待裁决 / 不可全局替换等）
# ---------------------------------------------------------------------------
TERMS = OrderedDict([
    # ---- D3 六组 ----
    ("ヨージ",      dict(jp=["ヨージ"], cands=["小鹰志", "洋治"], cat="人名",
                         note="cross_compare 误配「艾七」：艾七＝エージ（中介人），与ヨージ无关，已剔除")),
    ("ヨッくん",    dict(jp=["ヨッくん"], cands=["小鹰志君", "小约"], cat="人名")),
    ("イーグル",    dict(jp=["イーグル"], cands=["伊库鲁尔", "伊格尔"], cat="特定名词")),
    ("ダヴ",        dict(jp=["ダヴ"], cands=["妲朴", "达芙"], cat="人名")),
    ("プリンセス・ダヴ", dict(jp=["プリンセス・ダヴ", "プリンセスダヴ"], cands=["妲朴公主", "妲朴小公主"], cat="人名")),
    ("チケドン",    dict(jp=["チケドン"], cands=["奇肯多", "千夏丼"], cat="人名")),
    ("羽田君",      dict(jp=["羽田君", "羽田くん"], cands=["羽田君", "羽田同学"], cat="称谓")),
    ("渡来さん",    dict(jp=["渡来さん"], cands=["渡来同学", "regex:渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香)"], cat="称谓",
                         labels={"regex:渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香)": "渡来（裸名）"})),
    ("ガルーダ",    dict(jp=["ガルーダ"], cands=["伽鲁炟", "迦鲁炟", "迦楼罗", "伽楼罗"], cat="人名",
                         name_exclude=["伽楼罗", "迦楼罗"],
                         note="新米正文另有异体「迦鲁炟」（伽/迦 混用），名字框统一为「伽鲁炟」；名字框「伽楼罗 189」属伽楼羅，已排除")),
    ("伽楼羅",      dict(jp=["伽楼羅"], cands=["伽楼罗", "迦楼罗"], cat="人名")),
    # ---- 跨表不一致（cross_compare 30 条）----
    ("パル",        dict(jp=["パル"], cands=["芳春", "帕露"], cat="人名")),
    ("プラチナ",    dict(jp=["プラチナ"], cands=["普纳奇纳", "普拉琪娜"], cat="人名")),
    ("ファルコン",  dict(jp=["ファルコン"], cands=["法卢空", "法尔康"], cat="人名")),
    ("ハリュー",    dict(jp=["ハリュー"], cands=["哈里", "哈柳"], cat="人名")),
    ("ペガサス",    dict(jp=["ペガサス"], cands=["佩格萨斯", "佩加索斯", "天马"], cat="特定名词",
                         note="涅布术语表记双轨（叙述→佩格萨斯／台词敬称长官→天马）；新米实测佩格萨斯 29、天马 11，须按语境门控")),
    ("ギバラ",      dict(jp=["ギバラ"], cands=["岐原", "歧原", "吉巴拉", "柳木原"], cat="地名",
                         note="「柳木原」与主舞台城市名撞形，禁止按中文串全局替换")),
    ("花水木通り",  dict(jp=["花水木通り"], cands=["花水木大街", "花水木大道"], cat="地名")),
    ("風見ヶ丘",    dict(jp=["風見ヶ丘"], cands=["风见之丘", "风见丘"], cat="地名")),
    ("蒼穹女学院",  dict(jp=["蒼穹女学院"], cands=["苍穹女子学院", "苍穹女学院"], cat="组织")),
    ("アスカ姫",    dict(jp=["アスカ姫", "プリンセス・アスカ"], cands=["明日香公主", "阿斯嘉公主"], cat="特定名词")),
    ("ロックバード", dict(jp=["ロックバード"], cands=["ＲＯＣ－ＢＩＲＤ", "洛克巴德"], cat="特定名词")),
    ("御影クリヤ",  dict(jp=["御影クリヤ"], cands=["御影栗谷", "御影栗也", "御影克里亚"], cat="人名")),
    ("アルバトロス", dict(jp=["アルバトロス"], cands=["信天翁大厦", "阿尔巴特罗斯"], cat="地名")),
    ("ささやきマテリアル", dict(jp=["ささやきマテリアル"], cands=["细语材质", "低语材料", "耳语材料"], cat="特定名词")),
    ("Ｒ－ウィング", dict(jp=["Ｒ－ウィング", "Ｒ－Ｗｉｎｇ", "Ｒ－ＷＩＮＧ"], cands=["Ｒ－ＷＩＮＧ", "Ｒ翼"], cat="组织")),
    ("ロイヒテン・グレタ", dict(jp=["ロイヒテン・グレタ"], cands=["罗伊希滕·格雷塔", "洛伊希滕·格雷塔"], cat="特定名词")),
    ("グロリアス",  dict(jp=["グロリアス"], cands=["GLORIOUS", "古罗利亚斯"], cat="特定名词")),
    ("ハヤブサ",    dict(jp=["ハヤブサ"], cands=["游隼", "regex:(?<!游)隼(?!人)"], cat="特定名词",
                         labels={"regex:(?<!游)隼(?!人)": "隼"},
                         force_pending=True,
                         force_reason="新米以「隼」为主（24 槽）但与本篇 §三之三十三「代号→游隼」裁决冲突，须主代理确认")),
    ("奈落",        dict(jp=["奈落"], cands=["奈落", "地狱"], cat="特定名词",
                         note="按原文 奈落 门控，不可按中文串全局替换")),
    ("ソラ学",      dict(jp=["ソラ学", "ソラガク"], cands=["美空学院", "美空学府", "regex:(?<!美)空学院", "regex:(?<!美)空学(?!院|府)"], cat="地名",
                         labels={"regex:(?<!美)空学院": "空学院", "regex:(?<!美)空学(?!院|府)": "空学"},
                         force_pending=True,
                         force_reason="新米内部三种写法并存（美空学府 2／美空学院 1／空学院 1），无单一实测写形，须主代理确认")),
    ("ブルボンヌ冴子", dict(jp=["ブルボンヌ冴子"], cands=["布尔邦努冴子", "布露波卢冴子"], cat="人名")),
    ("バニィＤ",    dict(jp=["バニィＤ", "バニィD"], cands=["巴尼Ｄ"], cat="人名")),
    ("高内",        dict(jp=["高内"], cands=["高内"], cat="人名",
                         skip=True, skip_reason="中日同形，四表分歧系合并单元格产物，无需替换")),
    ("鴨志田",      dict(jp=["鴨志田"], cands=["鸭志田"], cat="人名",
                         skip=True, skip_reason="中日同形（鸭志田），无需替换")),
    ("山科",        dict(jp=["山科"], cands=["山科"], cat="人名",
                         skip=True, skip_reason="中日同形，且与京都地名撞形，无需替换")),
    ("成田 鷲介",   dict(jp=["成田 鷲介", "成田鷲介", "軽部鷲介"], cands=["成田鹫介", "轻部鹫介"], cat="人名")),
    ("男子Ａ",      dict(jp=["男子Ａ", "男子生徒Ａ", "男性生徒Ａ"], cands=["男生Ａ", "男学生Ａ"], cat="称谓",
                         name_exact=True, skip=True, skip_reason="路人群体名，四表分歧系表格合并单元格产物，非术语项")),
    ("女子Ａ",      dict(jp=["女子Ａ", "女子生徒Ａ", "女性生徒Ａ"], cands=["女生Ａ", "女学生Ａ"], cat="称谓",
                         name_exact=True, skip=True, skip_reason="路人群体名，四表分歧系表格合并单元格产物，非术语项")),
    ("一同",        dict(jp=["一同"], cands=["众人", "全员"], cat="称谓",
                         name_exact=True, skip=True, skip_reason="全体同称，四表无实质分歧")),
    ("瑠樺",        dict(jp=["瑠樺"], cands=["榴桦", "瑠桦"], cat="人名")),
    ("アニキ",      dict(jp=["アニキ"], cands=["大哥", "老哥"], cat="称谓")),
    ("委員長",      dict(jp=["委員長"], cands=["班长", "regex:(?<!执行)委员长"], cat="人名",
                         labels={"regex:(?<!执行)委员长": "委员长"},
                         note="排除「実行委員長→执行委员长」（同形两义，正当拆分）")),
    ("メンマ",      dict(jp=["メンマ"], cands=["面魔", "笋干"], cat="人名")),
    ("春日春恵",    dict(jp=["春日春恵"], cands=["春惠", "春日春江"], cat="人名")),
    ("針生",        dict(jp=["針生"], cands=["针生同学", "regex:针生(?!同学)"], cat="称谓",
                         labels={"regex:针生(?!同学)": "针生"})),
    ("ドラさん",    dict(jp=["ドラさん"], cands=["德拉先生", "regex:德拉(?!先生)"], cat="称谓",
                         labels={"regex:德拉(?!先生)": "德拉"},
                         note="语境相关：学生/亲昵语境→德拉，社会敬称→德拉先生；新米两者并存")),
    ("キッカワ",    dict(jp=["キッカワ", "吉川"], cands=["吉川"], cat="人名",
                         skip=True, skip_reason="中日同形（吉川），无需替换")),
    ("店員",        dict(jp=["店員"], cands=["小姐", "先生", "女士", "店员"], cat="称谓",
                         skip=True, skip_reason="敬称口径项（○○小姐/○○先生 vs ○小姐/○女士），属通用层规则，非专名替换")),
    ("鳳凰寺カケル", dict(jp=["鳳凰寺カケル"], cands=["凤凰寺翔", "regex:翔"], cat="人名",
                         labels={"regex:翔": "翔（略称）"},
                         skip=True, skip_reason="同一角色两写形（全名→凤凰寺翔／略称→翔），按语境保留，不作替换")),
    ("タカシ",      dict(jp=["タカシ"], cands=["汰架示", "鹰志"], cat="人名",
                         name_exclude=["鹰志"],
                         force_pending=True,
                         force_reason="新米以「鹰志」为主（167 槽）但与本篇 §三之八十一「网名/人格并提→汰架示、禁止全库统一」裁决冲突，须主代理确认")),
    ("藤宮穂乃香",  dict(jp=["藤宮穂乃香"], cands=["藤宫穗乃香", "藤城穗乃香"], cat="人名")),
    ("藤城穂乃香",  dict(jp=["藤城穂乃香"], cands=["藤城穗乃香", "藤宫穗乃香"], cat="人名")),
])


def cand_match(text, cand):
    if cand.startswith("regex:"):
        return re.search(cand[6:], text) is not None
    return cand in text


def cand_display(cand, spec=None):
    if spec and spec.get("labels") and cand in spec["labels"]:
        return spec["labels"][cand]
    return cand[6:] if cand.startswith("regex:") else cand


def arbitrate():
    """新米仲裁：返回 {term: {cands:..., body:{cand:n}, name:{cand:n}, jp_slots, samples}}"""
    data = json.load(open(CORPUS, encoding="utf-8"))
    out = OrderedDict()
    for key, spec in TERMS.items():
        body = Counter()
        name = Counter()
        jp_slots = 0
        samples = defaultdict(list)
        for r in data:
            jp = r.get("jp") or ""
            cn = r.get("cn") or ""
            sp = r.get("speaker") or ""
            scn = r.get("speaker_cn") or ""
            if any(n in jp for n in spec["jp"]):
                jp_slots += 1
                for c in spec["cands"]:
                    if cn and cand_match(cn, c):
                        body[c] += 1
                        if len(samples[cand_display(c, spec)]) < 3:
                            samples[cand_display(c, spec)].append(
                                {"scene": r.get("scene"), "jp": jp[:90], "cn": cn[:120]})
            if sp and any(n in sp for n in spec["jp"]) and scn:
                if any(x in scn for x in spec.get("name_exclude", [])):
                    continue
                if spec.get("name_exact"):
                    if scn in spec["cands"]:
                        name[scn] += 1
                else:
                    name[scn] += 1
        out[key] = {"jp_slots": jp_slots, "body": dict(body), "name": dict(name),
                    "samples": dict(samples)}
    return out


def iter_otr_body():
    """R 版正文（仅 body 流；名字框改由现行态文件提供）。"""
    for rec in btr.iter_otr():
        if rec[1] == "body":
            yield rec


def iter_otr_name_current():
    """R 版**现行**名字框：`重编码映射.json` 中 src=='name-cn' 的 33,440 条。
    注意：W7-3 曾误用 `名字中文化.json`（32,512 条，2026-09-15 改名**前**快照，
    仍含「迦楼罗/普拉琪娜/达芙/千夏丼/伊格尔」），本脚本改用现行态。"""
    for r in json.load(open(os.path.join(ROOT, r"工程\我们没有翅膀R\语料\重编码映射.json"),
                             encoding="utf-8")):
        if r.get("src") == "name-cn":
            yield ("otr", "name", f'{r.get("file")}@{r.get("offset")}',
                   "", r.get("text") or "", None)


def count_sources():
    """六源候选写法槽数（body / name 分列）。返回 {term: {srcstream: {cand:n}}}"""
    iters = [btr.iter_ot, iter_otr_body, iter_otr_name_current, btr.iter_ota,
             btr.iter_otp, btr.iter_otv, btr.iter_np]
    out = {k: defaultdict(Counter) for k in TERMS}
    for it in iters:
        for src, corpus, sid, jp, cn, speaker in it():
            if not cn:
                continue
            for key, spec in TERMS.items():
                # JP 门控：有日文原文的源，仅当原文含该术语原词时才计入（区分ガルーダ/伽楼羅）
                if jp and not any(n in jp for n in spec["jp"]):
                    continue
                # 渡来さん 的裸名仅在原文含 渡来さん 时才算旧写法
                for c in spec["cands"]:
                    if not cand_match(cn, c):
                        continue
                    if corpus == "name" and c in spec.get("name_exclude", []):
                        continue
                    if key == "渡来さん" and c.startswith("regex:") and jp and "渡来さん" not in jp:
                        continue
                    out[key][f"{src}/{corpus}"][c] += 1
    return {k: {s: dict(c) for s, c in v.items()} for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", default=TSV_DEFAULT)
    ap.add_argument("--json", default=JSON_DEFAULT)
    a = ap.parse_args()

    arb = arbitrate()
    src = count_sources()

    # 判定新米写形
    report = OrderedDict()
    report["_meta"] = {
        "script": "rebuild_term_table.py",
        "issue": "ISSUE-20260918-06 / W7-3b",
        "basis": "用户 2026-09-18 复裁 D3（修订版）：译名统一基准 = 2009 新米参照语料实测写形",
        "corpus": CORPUS,
        "corpus_slots": 57820,
        "counting": "body=jp 含原词槽内 cn 命中候选槽数；name=speaker(日文)含原词时 speaker_cn 分布；槽级；只读",
    }
    report["terms"] = OrderedDict()
    for key, spec in TERMS.items():
        A = arb[key]
        # 新米写法 = body 命中最多者；body 全 0 时看 name
        body_items = sorted(A["body"].items(), key=lambda kv: -kv[1])
        name_items = sorted(A["name"].items(), key=lambda kv: -kv[1])
        if body_items and body_items[0][1] > 0:
            winner = cand_display(body_items[0][0], spec)
            win_count = body_items[0][1]
            win_stream = "body"
        elif name_items and name_items[0][1] > 0:
            winner = cand_display(name_items[0][0], spec)
            win_count = name_items[0][1]
            win_stream = "name"
        else:
            winner = None
            win_count = 0
            win_stream = None
        report["terms"][key] = {
            "cat": spec["cat"],
            "jp_slots": A["jp_slots"],
            "new_writing": winner,
            "new_count": win_count,
            "new_stream": win_stream,
            "body": A["body"],
            "name": A["name"],
            "sources": src[key],
            "samples": A["samples"],
            "note": spec.get("note", ""),
            "skip": spec.get("skip", False),
            "skip_reason": spec.get("skip_reason", ""),
            "force_pending": spec.get("force_pending", False),
            "force_reason": spec.get("force_reason", ""),
            "pending": winner is None or spec.get("force_pending", False),
            "confidence": ("none" if winner is None else
                           "low" if (A["jp_slots"] < 5 or
                                     (win_count / max(1, sum(
                                         (A["body"] if win_stream == "body" else A["name"]).values()))) < 0.6)
                           else "ok"),
        }
        print(f"{key:<20} jp={A['jp_slots']:>4}  body={A['body']}  name={A['name']}  -> {winner}")

    os.makedirs(os.path.dirname(P(a.json)), exist_ok=True)
    json.dump(report, open(P(a.json), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\nwrote", P(a.json))

    # ---- TSV ----
    rows = ["原词日文\t旧写法\t新写法\t类别\t适用范围(源代号)\t旧写法出现次数\t证据出处\t备注"]
    for key, spec in TERMS.items():
        t = report["terms"][key]
        neww = t["new_writing"]
        if t["skip"]:
            rows.append(f"{key}\t（非替换项）\t{neww or '（不适用）'}\t{spec['cat']}\t—\t0\t{t['skip_reason']}\t{t['note']}")
            continue
        base = neww
        if t["force_pending"]:
            neww = "（待裁决）"
            ev = f"新米语料 jp 门控 {t['new_stream']} {t['new_count']} 槽；{t['force_reason']}"
            base = None
        elif neww is None:
            neww = "（待裁决）"
            ev = "新米语料实测 0 槽，无据可依"
            base = None
        else:
            ev = f"新米语料 jp 门控 {t['new_stream']} {t['new_count']} 槽"
            if t["confidence"] == "low":
                neww = f"{neww}（低置信）"
                ev += "；证据弱/新米内部不一致，须主代理确认"
        # 找出各源中与 winner 不同的写法（=旧写法）
        srcrows = []
        for stream, cmap in sorted(t["sources"].items()):
            for c, n in sorted(cmap.items(), key=lambda kv: -kv[1]):
                cd = cand_display(c, spec)
                if base is not None and cd == base:
                    continue
                srcrows.append((stream, cd, n))
        if not srcrows:
            rows.append(f"{key}\t（无旧写法残留）\t{neww}\t{spec['cat']}\t全部\t0\t{ev}\t{t['note']}")
        else:
            for stream, cd, n in srcrows:
                rows.append(f"{key}\t{cd}\t{neww}\t{spec['cat']}\t{stream}\t{n}\t{ev}\t{t['note']}")
    open(P(a.tsv), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print("wrote", P(a.tsv), f"({len(rows)-1} rows)")


if __name__ == "__main__":
    main()