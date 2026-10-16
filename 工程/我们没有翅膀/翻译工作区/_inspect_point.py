# -*- coding: utf-8 -*-
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, "语料", "批次")
DST = os.path.join(BASE, "译文")

# 建立 slot -> (batch, body) 全库索引
slot2batch, slot2body = {}, {}
for fn in sorted(os.listdir(SRC)):
    if not fn.startswith("batch_"): continue
    b = fn[:-4]
    with open(os.path.join(SRC, fn), encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            c = line.rstrip("\n").split("\t")
            if len(c) >= 7:
                slot2batch[c[1]] = b; slot2body[c[1]] = c[6]

print("== 定点槽所在批次 ==")
for s in ["s01_08d4.sob#654","s01_08d4.sob#962","s01_08d4.sob#972",
          "s01_04o.sob#280","s01_04o.sob#288","s01_04o.sob#324","s01_04o.sob#350",
          "s01_05b.sob#343","s04_24a.sob#673","s03_03e.sob#355",
          "s02_03a.sob#37","s01_14l.sob#204",
          "s02_02a.sob#241","s02_05d.sob#475","s02_14c.sob#281","s03_03b.sob#455"]:
    print("  %-24s -> %s" % (s, slot2batch.get(s, "未找到")))
    if s in slot2body:
        print("      原文: %s" % slot2body[s])

print()
print("== R41 タカシ：原文是否含 鷹志/鹰志 ==")
for s, b in sorted(slot2body.items(), key=lambda x: slot2batch.get(x[0], "")):
    if "タカシ" in b:
        has = "鷹志" in b
        if has:
            print("  !! %s [%s] 原文同时含 鷹志" % (s, slot2batch[s]))
            print("     %s" % b)

print()
print("== R30 ちんぽこ 门控逐槽 ==")
for s, b in sorted(slot2body.items(), key=lambda x: slot2batch.get(x[0], "")):
    if "ちんぽこ" in b:
        gate = ("おれ" in b) or ("ちんちん" in b)
        print("  %-22s [%s] gate=%s  (おれ=%s ちんちん=%s)" % (
            s, slot2batch[s], "PASS" if gate else "FAIL", "おれ" in b, "ちんちん" in b))