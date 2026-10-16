# -*- coding: utf-8 -*-
# 批次04 自检：逐条比对原文/译文的标点计数与禁用字符
import json, os, sys, collections

base = os.path.dirname(os.path.abspath(__file__))
o = json.load(open(os.path.join(base, "批次04_原文.json"), encoding="utf-8"))["lines"]
t = json.load(open(os.path.join(base, "批次04_译文.json"), encoding="utf-8"))["tr"]
assert len(o) == len(t), (len(o), len(t))

PUNCT = ["、", "。", "…", "！", "？", "～", "※"]
MAP = [("♪","☆"),("・","·")]
BAD = ["，", "\u3000", "「", "」", "『", "』", "〜", "・", "♪", "―", "\u2015", "…?", "\u2500"]
bad_lines = collections.Counter()
punct_mismatch = []
for a, b in zip(o, t):
    jp, cn = a["jp"] or "", b["cn"]
    if a["i"] != b["i"]:
        print("ID MISMATCH", a["i"], b["i"])
    pairs = [(p,p) for p in PUNCT] + MAP
    for p,q in pairs:
        if False: pass
        if jp.count(p) != cn.count(q):
            punct_mismatch.append((a["i"], a["file"], p, jp.count(p), cn.count(q), jp, cn))
    for ch in BAD:
        if ch in cn:
            bad_lines[(a["i"], ch)] += 1
    try:
        cn.encode("gbk")
    except UnicodeEncodeError as e:
        print("GBK FAIL", a["i"], e)

print("=== 标点计数不一致：%d 条" % len(punct_mismatch))
for m in punct_mismatch:
    print("i=%d %s [%s] jp=%d cn=%d\n   jp: %s\n   cn: %s" % m)
print("=== 禁用字符命中：")
for k, v in sorted(bad_lines.items()):
    print("i=%d char=%r" % (k[0], k[1]))
