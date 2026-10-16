# -*- coding: utf-8 -*-
"""测量 batch_061-118 各规则的命中槽数"""
import os, re, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, "语料", "批次")
DST = os.path.join(BASE, "译文")

def load_batches(lo, hi):
    src = {}
    dst = {}
    for n in range(lo, hi + 1):
        b = "batch_%03d" % n
        sp = os.path.join(SRC, b + ".tsv")
        dp = os.path.join(DST, b + ".tsv")
        if not os.path.exists(sp):
            continue
        with open(sp, encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.rstrip("\n")
                if i == 0:
                    continue
                cols = line.split("\t")
                if len(cols) >= 7:
                    src[cols[1]] = cols[6]
        if os.path.exists(dp):
            with open(dp, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    c = line.split("\t", 1)
                    if len(c) == 2:
                        dst[c[0]] = c[1]
    return src, dst

src, dst = load_batches(61, 118)
print("loaded src=%d dst=%d" % (len(src), len(dst)))

# 规则表：jp_need, olds(list), new, note
RULES = [
    (1,  "ブルマ", ["布鲁马"], "灯笼裤", ""),
    (2,  "トレーナー", ["培训员"], "教官", ""),
    (3,  "いづみ", ["多摩伊豆美", "多摩伊兹米"], "多摩泉", ""),
    (4,  "メンフリ", ["男冻"], "男士冻结", ""),
    (5,  "ワンさん", ["狗先生", "汪先生"], "王先生", ""),
    (6,  "ボダ子", ["傻丫头"], "波妲子", ""),
    (7,  "サマードレス", ["连衣裙"], "夏日连衣裙", ""),
    (8,  "いやっほう", ["呀嚯", "耶呼"], "呀吼——", ""),
    (9,  "ふぅーん", ["哦～"], "嗯～", ""),
    (10, "ハゲ", ["光头"], "秃子", "排除原文含 スキンヘッド"),
    (11, "フリファ", ["弗利粉"], "弗利奇", ""),
    (12, "目潰しピース", ["插眼剪刀手", "戳眼剪刀手", "戳眼Ｖ字手势", "戳眼手势"], "戳眼和平手势", ""),
    (13, "ヨネちゃん", ["米田酱"], "米酱", ""),
    (14, "パル", ["帕露大姐"], "帕露姐", "パル姐さん语境"),
    (15, "ギャル男", ["辣妹男"], "潮男", ""),
    (16, "モンキホーテ", ["孟吉可乌德"], "孟吉可德", ""),
    (17, "ヘテロ", ["异性什么"], "异色瞳", ""),
    (18, "ブルボンヌ", ["布尔邦努"], "波旁努", ""),
    (19, "オイィ", ["喂喂喂"], "喂～", ""),
    (20, "ドラキュラ", ["德拉古拉"], "德古拉", ""),
    (21, "ぱね", ["帕内达", "帕内田", "哈内达", "噗山", "噗田"], "牛田/牛山", "按原文"),
    (22, "ゲイ", ["基佬", "搞基"], "男同", ""),
    (23, "掲示板", ["讨论板", "讨论版"], "论坛", ""),
    (24, "ハヤブサ", ["哈雅布萨"], "游隼", ""),
    (25, "じいさん", ["爷爷"], "老爷子", "排除原文含 おじいさん/お祖父"),
    (26, "ページアップ", ["Ｐａｇｅ Ｕｐ", "Ｐａｇｅ Ｄｏｗｎ"], "翻页", ""),
    (27, "ポケベル", [], "寻呼机", "补译"),
    (28, "コノヤロウ", ["你这家伙"], "你这混蛋", ""),
    (29, "漫喫", ["网吧"], "漫画咖啡厅", ""),
    (30, "ちんぽこ", ["肉棒"], "小鸡鸡", "儿语轨"),
    (31, "ニート", ["无业游民"], "尼特族", ""),
    (32, "子持ちママチャリ団地妻", ["有孩子的妈妈自行车"], "带娃主妇自行车团地妻", ""),
    (33, "団地妻", ["小区人妻"], "团地妻", ""),
    (34, "成田っち", ["成田兄"], "成田酱", ""),
    (35, "左右田さん", ["左右田他们"], "左右田先生", ""),
    (36, "ミソッカス", ["没用的废物"], "丑八怪", ""),
    (37, "きっちー", ["累死了", "冷死了"], "真够呛", ""),
    (38, "くすくす", ["嗤嗤", "哧哧", "咯咯"], "嘻嘻", ""),
    (39, "ぷっぷっぷ", ["嘟、嘟、嘟、嘟"], "噗噗噗", ""),
    (40, "俺様", ["老子", "俺样"], "本大爷", "非引用型"),
    (41, "タカシ", ["汰架示"], "鹰志", ""),
    (42, "日ょ子", ["日ょ子"], "日和子", ""),
    (43, "俺", ["我"], "俺", "仅4槽定点"),
]

results = {}
for num, jp, olds, new, note in RULES:
    hits = []
    for slot, body in src.items():
        if jp not in body:
            continue
        if note and "排除" in note:
            if jp == "ハゲ" and "スキンヘッド" in body:
                continue
            if jp == "じいさん" and ("おじいさん" in body or "お祖父" in body):
                continue
        tr = dst.get(slot)
        if tr is None:
            continue
        for old in olds:
            if old in tr:
                hits.append((slot, old))
                break
    results[num] = hits
    print("#%-3d %-14s jp=%-12s hits=%d  %s" % (num, "".join(olds) or "(补译)", jp, len(hits), note))
    for s, o in hits[:20]:
        print("      %s | old=%s | tr=%s" % (s, o, dst[s][:60]))

with open(os.path.join(BASE, "_measure_061_118.json"), "w", encoding="utf-8") as f:
    json.dump({str(k): v for k, v in results.items()}, f, ensure_ascii=False, indent=1)