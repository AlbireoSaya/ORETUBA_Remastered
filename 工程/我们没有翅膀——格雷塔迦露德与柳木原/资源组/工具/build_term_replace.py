#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W7-3 · D3 译名统一替换表 —— 实测统计脚本（可复跑、可审计）

用途
----
在六源语料的**正文**中统计：
  (A) 日文原词出现槽数（jp_count）——「替换影响面」的上界
  (B) 旧写法（中文旧译形）出现槽数（old_cn_count）——真正需要替换的槽数
**排除说话人标签**（引擎键，不得译、不得替换）；R 版 / PSV 的**名字框显示名**单独成流统计。

计数口径
--------
* 槽级命中：同一槽内同一 needle 出现多次仍计 1 槽（给出的是「受影响槽数」）。
* 边界规则：`隼` 须排除 `隼人`；`渡来` 须排除 `渡来同学/渡来明日香/渡来家/渡来屋`；
  `柳木原` 不计入 `ギバラ`（与城市名撞形，属「不可全局替换」项，见风险清单）。

纪律
----
* 只读源：六源工程目录一个字节都不改。
* 中间产物写 `子代理工作区\\ISSUE-20260918-06\\W7-3\\`。
* 本脚本不写任何术语表；只产出统计事实。

用法
----
    python build_term_replace.py
    python build_term_replace.py --json <path>
"""

import argparse
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

ROOT = r"E:\ZCode Workspace\Galgame"
OUT_DEFAULT = r"子代理工作区\ISSUE-20260918-06\W7-3\term_count_report.json"


def P(rel):
    return os.path.join(ROOT, rel)


# ---------------------------------------------------------------------------
# 1. 六源语料（正文流 / 名字框流 / 日文流）
# ---------------------------------------------------------------------------
SRC_OT    = r"工程\我们没有翅膀\汉化\剧情汉化\_总表.tsv"
SRC_OTR_B = r"工程\我们没有翅膀R\语料\重编码映射.json"     # 正文（GBK 字节）
SRC_OTR_N = r"工程\我们没有翅膀R\语料\新增译文映射.json"   # 正文（新译，utf-8）
SRC_OTR_MIG = r"工程\我们没有翅膀R\语料\R版迁移映射.json"  # ★ R 正文实测基准（jp+cn 对齐）
SRC_OTR_NAME = r"工程\我们没有翅膀R\语料\名字中文化.json"  # 名字框显示名
SRC_OTR_JP = r"工程\我们没有翅膀R\语料\R版台词.json"       # 日文正文
SRC_OTA = r"工程\我们没有翅膀 After Story\语料\译文.json"   # jp+cn 合一
SRC_OTP_DIR = r"工程\我们没有翅膀 前奏诗\汉化\剧情汉化"     # jsonl jp+cn
SRC_OTV = r"工程\我们没有翅膀PSV\汉化\台词对照.json"       # jp+cn
SRC_NP_CN = r"工程\涅布＊普拉斯\翻译工作区"                 # 分块N_译文.json
SRC_NP_JP = r"工程\涅布＊普拉斯\语料\明日香线_原文.json"


def iter_ot():
    """本篇 _总表.tsv：说话人列为引擎标签 → 排除。"""
    with open(P(SRC_OT), encoding="utf-8") as f:
        f.readline()
        for i, line in enumerate(f, start=2):
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                continue
            yield ("ot", "ot", f"{p[0]}#{i}", p[4], p[5], p[3])


def iter_otr():
    """R版：正文 = `R版迁移映射.json`（51,736 槽，含 jp 对齐，R 正文实测基准）；
    名字框 = `名字中文化.json`（32,512 槽，name-cn）。

    说明：`重编码映射.json` 的 35,647 条中 33,440 为 name-cn（与名字中文化同源），
    正文仅 1,517 条；`新增译文映射.json` 6,624 条为正文补译。二者均被迁移映射覆盖，
    故不重复读取（避免双计）。
    """
    for r in json.load(open(P(SRC_OTR_MIG), encoding="utf-8")):
        yield ("otr", "body", f'{r.get("file")}#{r.get("index")}',
               r.get("jp") or "", r.get("cn") or "", r.get("speaker") or "")
    for r in json.load(open(P(SRC_OTR_NAME), encoding="utf-8")):
        yield ("otr", "name", f'{r.get("file")}@{r.get("offset")}',
               "", r.get("text") or "", None)


def iter_otr_jp():
    for r in json.load(open(P(SRC_OTR_JP), encoding="utf-8")):
        yield ("otr", "jp", f'{r.get("file")}#{r.get("index")}',
               r.get("text") or "", "", r.get("speaker") or "")


def iter_ota():
    """AS：译文.json 内 messages[].jp / .cn；speaker 排除。"""
    for fname, rec in json.load(open(P(SRC_OTA), encoding="utf-8")).items():
        for m in rec.get("messages", []):
            yield ("ota", "body", f'{fname}#{m.get("index")}',
                   m.get("jp") or "", m.get("cn") or "", m.get("speaker") or "")


def iter_otp():
    for fn in sorted(os.listdir(P(SRC_OTP_DIR))):
        if not fn.endswith(".jsonl"):
            continue
        with open(os.path.join(P(SRC_OTP_DIR), fn), encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                yield ("otp", "body", f'{fn}#{r.get("seq")}',
                       r.get("jp") or "", r.get("cn") or "",
                       r.get("speaker") or "")


def iter_otv():
    """PSV：正文 日文/中文；说话人中文（adv.txt [Name]）单列为 name 流。"""
    for r in json.load(open(P(SRC_OTV), encoding="utf-8")):
        sid = f'{r.get("脚本")}#{r.get("行序")}'
        yield ("otv", "body", sid, r.get("日文") or "", r.get("中文") or "",
               r.get("说话人日文") or "")
    seen = set()
    for r in json.load(open(P(SRC_OTV), encoding="utf-8")):
        nm = r.get("说话人中文")
        if nm and nm not in seen:
            seen.add(nm)
            yield ("otv", "name", f'name:{nm}', "", nm, None)


def iter_np():
    for fn in sorted(os.listdir(P(SRC_NP_CN))):
        if not re.match(r"分块\d+_译文\.json$", fn):
            continue
        for r in json.load(open(os.path.join(P(SRC_NP_CN), fn), encoding="utf-8")):
            yield ("np", "body", f'{r.get("file")}#{r.get("idx")}',
                   "", r.get("text") or "", None)


def iter_np_jp():
    arr = json.load(open(P(SRC_NP_JP), encoding="utf-8"))
    for i, r in enumerate(arr):
        t = r.get("text") if isinstance(r, dict) else str(r)
        yield ("np", "jp", f'jp#{i}', t or "", "", None)


ALL_ITERS = [iter_ot, iter_otr, iter_otr_jp, iter_ota, iter_otp, iter_otv, iter_np, iter_np_jp]


# ---------------------------------------------------------------------------
# 2. 术语组（needle 支持正则）
# ---------------------------------------------------------------------------
# jp    : 日文原词（正文写形）
# old   : 旧写法 needle（str=子串；regex:前缀=正则）
# new   : 新写法（新米基准）
# cat   : 类别
TERMS = OrderedDict([
    ("ヨージ",   dict(jp=["ヨージ"], old=["洋治"], new="小鹰志", cat="人名")),
    ("イーグル", dict(jp=["イーグル"], old=["伊格尔"], new="伊库鲁尔", cat="特定名词")),
    ("ダヴ",     dict(jp=["ダヴ"], old=["达芙"], new="妲朴", cat="人名")),
    ("チケドン", dict(jp=["チケドン"], old=["千夏丼"], new="奇肯多", cat="人名")),
    ("羽田君",   dict(jp=["羽田君", "羽田くん"], old=["羽田君"], new="羽田同学", cat="称谓")),
    ("渡来さん", dict(jp=["渡来さん"], old=["regex:渡来(?!同学|明日香|家|屋)"],
                      new="渡来同学", cat="称谓")),
    ("ガルーダ", dict(jp=["ガルーダ"], old=[], new="伽鲁炟", cat="人名")),
    ("伽楼羅",   dict(jp=["伽楼羅"], old=["迦楼罗"], new="伽楼罗（待裁决）", cat="人名")),
    # ---- 全量比对发现的其它跨作不一致 ----
    ("パル",     dict(jp=["パル"], old=["帕露"], new="芳春", cat="人名")),
    ("プラチナ", dict(jp=["プラチナ"], old=["普拉琪娜"], new="普纳奇纳", cat="人名")),
    ("ファルコン", dict(jp=["ファルコン"], old=["法尔康"], new="法卢空", cat="人名")),
    ("ハリュー", dict(jp=["ハリュー"], old=["哈柳"], new="哈里", cat="人名")),
    ("ペガサス", dict(jp=["ペガサス"], old=["佩加索斯"], new="佩格萨斯", cat="特定名词")),
    ("ギバラ",   dict(jp=["ギバラ"], old=["吉巴拉", "歧原", "岐原"], new="岐原（待裁决）", cat="地名")),
    ("花水木通り", dict(jp=["花水木通り"], old=["花水木大道"], new="花水木大街", cat="地名")),
    ("風見ヶ丘", dict(jp=["風見ヶ丘"], old=["风见丘"], new="风见之丘", cat="地名")),
    ("蒼穹女学院", dict(jp=["蒼穹女学院"], old=["苍穹女学院"], new="苍穹女子学院", cat="组织")),
    ("アスカ姫", dict(jp=["アスカ姫"], old=["阿斯嘉公主"], new="明日香公主", cat="特定名词")),
    ("ロックバード", dict(jp=["ロックバード"], old=["洛克巴德"], new="ＲＯＣ－ＢＩＲＤ", cat="特定名词")),
    ("御影クリヤ", dict(jp=["御影クリヤ"], old=["御影克里亚", "御影栗也"], new="御影栗谷（待裁决）", cat="人名")),
    ("アルバトロス", dict(jp=["アルバトロス"], old=["阿尔巴特罗斯"], new="信天翁大厦", cat="地名")),
    ("ささやきマテリアル", dict(jp=["ささやきマテリアル"],
                                old=["《低语材料》", "《耳语材料》"], new="细语材质（待裁决）", cat="特定名词")),
    ("Ｒ－ウィング", dict(jp=["Ｒ－ウィング", "Ｒ－Ｗｉｎｇ", "Ｒ－ＷＩＮＧ"],
                          old=["Ｒ翼"], new="Ｒ－ＷＩＮＧ", cat="组织")),
    ("ロイヒテン・グレタ", dict(jp=["ロイヒテン・グレタ"], old=["洛伊希滕·格雷塔"],
                                new="罗伊希滕·格雷塔", cat="特定名词")),
    ("グロリアス", dict(jp=["グロリアス"], old=["古罗利亚斯"], new="GLORIOUS", cat="特定名词")),
    ("ハヤブサ", dict(jp=["ハヤブサ"], old=["regex:(?<!游)隼(?!人)"], new="游隼", cat="特定名词",
                     jp_gate=["ハヤブサ"])),
    ("奈落",     dict(jp=["奈落"], old=["地狱"], new="奈落", cat="特定名词",
                     jp_gate=["奈落"])),
    ("ソラ学",   dict(jp=["ソラ学", "ソラガク"], old=["regex:(?<!美)空学"], new="美空学院", cat="地名",
                     jp_gate=["ソラ学", "ソラガク"])),
    ("藤宮穂乃香", dict(jp=["藤宮穂乃香"], old=["藤城穗乃香"], new="藤宫穗乃香", cat="人名")),
    ("藤城穂乃香", dict(jp=["藤城穂乃香"], old=["藤宫穗乃香"], new="藤城穗乃香", cat="人名")),
    ("タカシ",   dict(jp=["タカシ"], old=["汰架示"], new="汰架示/鹰志（语境二分）", cat="人名")),
])


def hit(text, needle):
    if needle.startswith("regex:"):
        return re.search(needle[6:], text) is not None
    return needle in text


# ---------------------------------------------------------------------------
# 3. 统计
# ---------------------------------------------------------------------------
def run():
    agg = {k: {"jp": defaultdict(int), "old": defaultdict(int),
               "jp_samples": [], "cn_samples": []} for k in TERMS}
    corpus_slots = defaultdict(int)

    for it in ALL_ITERS:
        for src, corpus, sid, jp, cn, speaker in it():
            key = f"{src}/{corpus}"
            corpus_slots[key] += 1
            for tkey, spec in TERMS.items():
                a = agg[tkey]
                for n in spec["jp"]:
                    if jp and n in jp:
                        a["jp"][key] += 1
                        if len(a["jp_samples"]) < 5:
                            a["jp_samples"].append({"corpus": key, "slot": sid,
                                                    "hit": n, "jp": jp[:110],
                                                    "cn": (cn or "")[:110]})
                        break
                if cn:
                    for n in spec["old"]:
                        if not hit(cn, n):
                            continue
                        # 渡来さん 特殊门控：裸名渡来 仅当**日文原词确为 `渡来さん`** 时才算旧写法；
                        # 原文呼び捨て（裸姓）时「渡来」是正确译法，不得替换。
                        if tkey == "渡来さん" and jp:
                            if "渡来さん" not in jp:
                                continue
                        # 通用 JP 门控：旧写法中文形有同形/子串歧义时，仅当原文含指定原词才算
                        gate = spec.get("jp_gate")
                        if gate and jp:
                            if not any(g in jp for g in gate):
                                continue
                        a["old"][key] += 1
                        if len(a["cn_samples"]) < 5:
                            a["cn_samples"].append({"corpus": key, "slot": sid,
                                                    "hit": n, "jp": jp[:90],
                                                    "cn": cn[:110]})
                        break

    rep = OrderedDict()
    rep["_meta"] = {
        "script": "build_term_replace.py",
        "issue": "ISSUE-20260918-06 / W7-3",
        "basis": "D3 译名统一基准 = 新米写形（用户 2026-09-18 裁决）",
        "counting": "槽级命中；说话人标签排除；R版/PSV 名字框单列；边界规则见脚本头。",
    }
    rep["corpus_slots"] = dict(corpus_slots)
    rep["terms"] = OrderedDict()
    for tkey, spec in TERMS.items():
        a = agg[tkey]
        rep["terms"][tkey] = {
            "new": spec["new"], "cat": spec["cat"],
            "jp_by_corpus": dict(a["jp"]),
            "old_by_corpus": dict(a["old"]),
            "jp_total_slots": sum(a["jp"].values()),
            "old_total_slots": sum(a["old"].values()),
            "jp_samples": a["jp_samples"],
            "cn_samples": a["cn_samples"],
        }
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=OUT_DEFAULT)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    rep = run()
    out = a.json if os.path.isabs(a.json) else P(a.json)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if not a.quiet:
        print("== 语料槽数 ==")
        for k, v in rep["corpus_slots"].items():
            print(f"  {k:14s} {v:>7d}")
        print("\n== 术语命中（槽级） ==")
        print(f"  {'原词':<22}{'JP槽':>7}{'旧写法槽':>9}  新写法")
        for k, t in rep["terms"].items():
            print(f"  {k:<22}{t['jp_total_slots']:>7}{t['old_total_slots']:>9}  {t['new']}")
        print(f"\n报告已写：{out}")


if __name__ == "__main__":
    main()