# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一"
WANT = {"miy02a", "bg01", "bg01b", "bg41", "bg41a", "bg72", "bg72b", "ef05a"}
for f in ["清单_CG背景.tsv", "清单_立绘.tsv", "清单_系统UI.tsv"]:
    print("===", f)
    lines = open(os.path.join(BASE, f), encoding="utf-8").read().splitlines()
    print(lines[0])
    for ln in lines[1:]:
        c = ln.split("\t")
        if c[0].rsplit(".", 1)[0] in WANT:
            print(ln)
print("=== CG背景 dir ===")
print([x for x in os.listdir(os.path.join(BASE, "CG背景")) if x.rsplit(".", 1)[0] in WANT])
print("=== 立绘 dir miy ===")
print([x for x in os.listdir(os.path.join(BASE, "立绘")) if "miy02" in x])