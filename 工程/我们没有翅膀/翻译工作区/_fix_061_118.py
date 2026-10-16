# -*- coding: utf-8 -*-
"""二审回改：batch_061-118 规则 1-43 落盘（规则 44-47/49 的槽均不在本范围）"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, "语料", "批次")
DST = os.path.join(BASE, "译文")

LO, HI = 61, 118

def load():
    slot2b, body = {}, {}
    for n in range(LO, HI + 1):
        b = "batch_%03d" % n
        p = os.path.join(SRC, b + ".tsv")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                c = line.rstrip("\n").split("\t")
                if len(c) >= 7:
                    slot2b[c[1]] = b
                    body[c[1]] = c[6]
    return slot2b, body

slot2b, body = load()

# 读译文（按批）
tr = {}
for n in range(LO, HI + 1):
    b = "batch_%03d" % n
    p = os.path.join(DST, b + ".tsv")
    if not os.path.exists(p):
        continue
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            c = line.split("\t", 1)
            if len(c) == 2:
                tr[c[0]] = c[1]

# 需要写回的槽 -> 新译文
newtr = {}
log = []

def rep(slot, old, new, count=-1):
    t = newtr.get(slot, tr[slot])
    if old not in t:
        return 0
    n = t.count(old)
    if count >= 0:
        n = min(n, count)
    if n == 0:
        return 0
    if count == 1:
        i = t.rfind(old)
        t = t[:i] + new + t[i + len(old):]
        c = 1
    else:
        t = t.replace(old, new)
        c = t.count(new) if False else n
    newtr[slot] = t
    log.append((slot, old, new, c))
    return c

# --- R12 目潰しピース ---
R12_OLDS = ["插眼剪刀手", "戳眼剪刀手", "戳眼Ｖ字手势", "戳眼手势"]
# --- R21 ぱね ---
R21_TIAN = ["帕内达", "帕内田", "哈内达", "噗田"]
R21_YAMA = ["噗山", "帕内山"]

for slot in sorted(body, key=lambda s: slot2b[s]):
    jp = body[slot]
    t = tr.get(slot)
    if t is None:
        continue
    # R12
    if "目潰しピース" in jp:
        for o in R12_OLDS:
            rep(slot, o, "戳眼和平手势")
    # R14 パル姐さん
    if "パル" in jp and "帕露大姐" in t:
        rep(slot, "帕露大姐", "帕露姐")
    # R20 ドラキュラ
    if "ドラキュラ" in jp:
        rep(slot, "德拉古拉", "德古拉")
    # R21 ぱね
    if "ぱね田" in jp:
        for o in R21_TIAN:
            rep(slot, o, "牛田")
    if "ぱね山" in jp:
        for o in R21_YAMA:
            rep(slot, o, "牛山")
    # R22 ゲイ
    if "ゲイ" in jp:
        if "搞基之道" in t:
            rep(slot, "搞基之道", "男同之路")
        else:
            rep(slot, "基佬", "男同")
            rep(slot, "搞基", "男同")
    # R25 じいさん（排除 おじいさん / お祖父）
    if "じいさん" in jp and "おじいさん" not in jp and "お祖父" not in jp:
        rep(slot, "爷爷", "老爷子")
    # R26 ページアップ/ダウン
    if "ページアップ" in jp or "ページダウン" in jp:
        rep(slot, "Ｐａｇｅ Ｕｐ", "翻页")
        rep(slot, "Ｐａｇｅ Ｄｏｗｎ", "翻页")
    # R29 漫喫
    if "漫喫" in jp:
        if "漫画网吧" in t:
            rep(slot, "漫画网吧", "漫画咖啡厅")
        else:
            rep(slot, "网吧", "漫画咖啡厅")
    # R30 ちんぽこ（儿语轨门控：原文含 おれ 或 ちんちん）
    if "ちんぽこ" in jp and ("おれ" in jp or "ちんちん" in jp):
        rep(slot, "肉棒", "小鸡鸡")
    # R32 子持ちママチャリ団地妻
    if "子持ちママチャリ団地妻" in jp:
        rep(slot, "有孩子的妈妈自行车团地妻", "带娃主妇自行车团地妻")
    # R33 団地妻
    if "団地妻" in jp:
        rep(slot, "小区人妻", "团地妻")
    # R38 くすくす
    if "くすくす" in jp:
        for o in ["嗤嗤", "哧哧", "咯咯"]:
            rep(slot, o, "嘻嘻")
    # R41 タカシ
    if "タカシ" in jp:
        rep(slot, "汰架示", "鹰志")

# R28 コノヤロウ：仅真缺陷 s03_05a.sob#402（第 2 个「你这家伙」＝コノヤロウ）
s = "s03_05a.sob#402"
if s in tr and "コノヤロウ" in body.get(s, "") and tr[s].count("你这家伙") == 2:
    rep(s, "你这家伙", "你这混蛋", count=1)

# 输出变更
print("== 变更槽数：%d ==" % len(newtr))
by_batch = {}
for slot in sorted(newtr, key=lambda s: slot2b[s]):
    by_batch.setdefault(slot2b[slot], []).append(slot)
    print("[%s] %s" % (slot2b[slot], slot))
    print("  旧: %s" % tr[slot])
    print("  新: %s" % newtr[slot])
print()
print("== 按批次 ==")
for b in sorted(by_batch):
    print("  %s : %d 槽" % (b, len(by_batch[b])))

with open(os.path.join(BASE, "_fix_061_118_plan.json"), "w", encoding="utf-8") as f:
    json.dump({"newtr": newtr, "batches": sorted(by_batch)}, f, ensure_ascii=False, indent=1)

if "--apply" in sys.argv:
    for b in sorted(by_batch):
        p = os.path.join(DST, b + ".tsv")
        lines = open(p, encoding="utf-8").read().split("\n")
        out = []
        for line in lines:
            if line:
                c = line.split("\t", 1)
                if len(c) == 2 and c[0] in newtr:
                    out.append(c[0] + "\t" + newtr[c[0]])
                    continue
            out.append(line)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out))
    print("APPLIED to %d batches" % len(by_batch))