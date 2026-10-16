# -*- coding: utf-8 -*-
import os, json

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, "语料", "批次")
DST = os.path.join(BASE, "译文")

def load(lo, hi):
    src, dst, batch_of = {}, {}, {}
    for n in range(lo, hi + 1):
        b = "batch_%03d" % n
        with open(os.path.join(SRC, b + ".tsv"), encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0: continue
                c = line.rstrip("\n").split("\t")
                if len(c) >= 7:
                    src[c[1]] = c[6]; batch_of[c[1]] = b
        p = os.path.join(DST, b + ".tsv")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line: continue
                    c = line.split("\t", 1)
                    if len(c) == 2: dst[c[0]] = c[1]
    return src, dst, batch_of

src, dst, bo = load(61, 118)

def show(title, slots, jp=None):
    print("==== %s ====" % title)
    for s in slots:
        b = src.get(s, "")
        t = dst.get(s, "<无译文>")
        print("[%s] %s" % (bo.get(s, "?"), s))
        print("  原文: %s" % b)
        print("  译文: %s" % t)

# 规则10 ハゲ 排除スキンヘッド
r10 = [s for s in src if "ハゲ" in src[s] and "光头" in dst.get(s, "")]
show("R10 ハゲ(含光头)", r10)

# 规则21 ぱね
r21 = [s for s in src if "ぱね" in src[s] and any(o in dst.get(s, "") for o in ["帕内达","帕内田","哈内达","噗山","噗田"])]
show("R21 ぱね", r21)

# 规则25 じいさん
r25 = [s for s in src if "じいさん" in src[s] and "爷爷" in dst.get(s, "")]
show("R25 じいさん(含爷爷)", r25)

# 规则30 ちんぽこ
r30 = [s for s in src if "ちんぽこ" in src[s] and "肉棒" in dst.get(s, "")]
show("R30 ちんぽこ(含肉棒)", r30)

# 规则41 タカシ
r41 = [s for s in src if "タカシ" in src[s] and "汰架示" in dst.get(s, "")]
show("R41 タカシ(含汰架示)", r41)