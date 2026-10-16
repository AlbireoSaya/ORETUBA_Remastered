#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W7-3b · 新米仲裁语料探查（一次性，可复跑）
仲裁语料：工程\\我们没有翅膀R\\参照\\中日对照表.json（57,820 槽）
口径：
  body : 槽 jp 含日文原词 needle → 统计 cn 中出现的候选写法槽数
  name : 槽 speaker(日文) 含 needle 或 speaker_cn 为候选 → 统计 speaker_cn 分布
只读，不改源。
"""
import json, os, re, sys
from collections import Counter, defaultdict

ROOT = r"E:\ZCode Workspace\Galgame"
CORPUS = os.path.join(ROOT, r"工程\我们没有翅膀R\参照\中日对照表.json")

TERMS = [
    ("ヨージ", ["ヨージ", "ヨッくん"], ["小鹰志", "洋治", "小约", "小鹰志君"]),
    ("イーグル", ["イーグル"], ["伊库鲁尔", "伊格尔"]),
    ("ダヴ", ["ダヴ"], ["妲朴", "达芙"]),
    ("チケドン", ["チケドン"], ["奇肯多", "千夏丼"]),
    ("羽田君", ["羽田君", "羽田くん"], ["羽田君", "羽田同学"]),
    ("渡来さん", ["渡来さん"], ["渡来同学", "渡来"]),
    ("ガルーダ", ["ガルーダ"], ["伽鲁炟", "迦楼罗", "伽楼罗"]),
    ("伽楼羅", ["伽楼羅"], ["伽楼罗", "迦楼罗"]),
    ("パル", ["パル"], ["芳春", "帕露"]),
    ("プラチナ", ["プラチナ"], ["普纳奇纳", "普拉琪娜"]),
    ("ファルコン", ["ファルコン"], ["法卢空", "法尔康"]),
    ("ハリュー", ["ハリュー"], ["哈里", "哈柳"]),
    ("ペガサス", ["ペガサス"], ["佩格萨斯", "佩加索斯", "天马"]),
    ("ギバラ", ["ギバラ"], ["岐原", "歧原", "吉巴拉", "柳木原"]),
    ("花水木通り", ["花水木通り"], ["花水木大街", "花水木大道"]),
    ("風見ヶ丘", ["風見ヶ丘"], ["风见之丘", "风见丘"]),
    ("蒼穹女学院", ["蒼穹女学院"], ["苍穹女子学院", "苍穹女学院"]),
    ("アスカ姫", ["アスカ姫", "プリンセス・アスカ"], ["明日香公主", "阿斯嘉公主"]),
    ("ロックバード", ["ロックバード"], ["ＲＯＣ－ＢＩＲＤ", "洛克巴德"]),
    ("御影クリヤ", ["御影クリヤ"], ["御影栗谷", "御影克里亚", "御影栗也"]),
    ("アルバトロス", ["アルバトロス"], ["信天翁大厦", "阿尔巴特罗斯"]),
    ("ささやきマテリアル", ["ささやきマテリアル"], ["细语材质", "低语材料", "耳语材料"]),
    ("Ｒ－ウィング", ["Ｒ－ウィング", "Ｒ－Ｗｉｎｇ", "Ｒ－ＷＩＮＧ", "Ｒ-ウィング"], ["Ｒ－ＷＩＮＧ", "Ｒ翼"]),
    ("ロイヒテン・グレタ", ["ロイヒテン・グレタ"], ["罗伊希滕·格雷塔", "洛伊希滕·格雷塔"]),
    ("グロリアス", ["グロリアス"], ["GLORIOUS", "古罗利亚斯"]),
    ("ハヤブサ", ["ハヤブサ"], ["游隼", "隼"]),
    ("奈落", ["奈落"], ["奈落", "地狱"]),
    ("ソラ学", ["ソラ学", "ソラガク"], ["美空学院", "空学", "空学院"]),
    ("藤宮穂乃香", ["藤宮穂乃香"], ["藤宫穗乃香", "藤城穗乃香"]),
    ("藤城穂乃香", ["藤城穂乃香"], ["藤城穗乃香", "藤宫穗乃香"]),
    ("タカシ", ["タカシ"], ["汰架示", "鹰志"]),
    ("ブルボンヌ冴子", ["ブルボンヌ冴子"], ["布尔邦努冴子", "布露波卢冴子"]),
    ("委員長", ["委員長"], ["委员长", "班长"]),
    ("メンマ", ["メンマ"], ["面魔", "笋干"]),
    ("春日春恵", ["春日春恵"], ["春惠", "春日春江"]),
    ("針生", ["針生"], ["针生同学", "针生"]),
    ("ドラ", ["ドラさん", "ドラ"], ["德拉", "德拉先生"]),
    ("キッカワ", ["キッカワ", "吉川"], ["吉川"]),
    ("鳳凰寺カケル", ["鳳凰寺カケル", "カケル", "鳳 翔"], ["凤凰寺翔", "翔"]),
]


def main():
    data = json.load(open(CORPUS, encoding="utf-8"))
    print("corpus slots:", len(data))
    # 全局中文串频次（body cn + speaker_cn）
    gbody = Counter()
    gname = Counter()
    for r in data:
        cn = r.get("cn") or ""
        if cn:
            gbody[cn] += 1
        sc = r.get("speaker_cn") or ""
        if sc:
            gname[sc] += 1

    out = {}
    for key, jpneedles, cands in TERMS:
        body_jp = 0
        body_hits = Counter()
        name_hits = Counter()
        samples = defaultdict(list)
        for r in data:
            jp = r.get("jp") or ""
            cn = r.get("cn") or ""
            sp = r.get("speaker") or ""
            scn = r.get("speaker_cn") or ""
            if any(n in jp for n in jpneedles):
                body_jp += 1
                for c in cands:
                    if c in cn:
                        body_hits[c] += 1
                        if len(samples[c]) < 3:
                            samples[c].append({"scene": r.get("scene"), "jp": jp[:90], "cn": cn[:110]})
            if any(n in sp for n in jpneedles):
                if scn:
                    name_hits[scn] += 1
        out[key] = {"body_jp_slots": body_jp, "body_hits": dict(body_hits),
                    "name_hits": dict(name_hits), "samples": {k: v for k, v in samples.items()}}
        print(f"\n== {key} ==  body_jp={body_jp}")
        print("   body:", dict(body_hits))
        print("   name:", dict(name_hits))

    outp = os.path.join(ROOT, r"子代理工作区\ISSUE-20260918-06\W7-3b\explore_arbitration.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    json.dump(out, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\nwrote", outp)


if __name__ == "__main__":
    main()