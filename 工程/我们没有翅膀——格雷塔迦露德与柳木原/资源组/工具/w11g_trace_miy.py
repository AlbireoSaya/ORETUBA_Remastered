# -*- coding: utf-8 -*-
"""W11g · 溯源 miy02a：ot/pic 的巫女装 CG 候选去哪了？"""
import os, sys, hashlib
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
SRC = os.path.join(PROJ, "资源组", "krkr素材库")


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


targets = {
    "ot/pic/ot_miy02a.png": os.path.join(SRC, "ot", "pic", "ot_miy02a.png"),
    "ot/chr/ot_miy02a.png": os.path.join(SRC, "ot", "chr", "ot_miy02a.png"),
    "np/pic/np_miy02a.png": os.path.join(SRC, "np", "pic", "np_miy02a.png"),
}
tm = {}
for k, p in targets.items():
    tm[k] = md5(p)
    print("%-26s md5=%s  size=%dx%d" % (k, tm[k][:12], *Image.open(p).size))

print("\n--- 在三个产物目录中按 md5 搜索 ---")
for d in ["立绘", "CG背景", "系统UI"]:
    dp = os.path.join(UNI, d)
    for fn in sorted(os.listdir(dp)):
        fp = os.path.join(dp, fn)
        if not os.path.isfile(fp):
            continue
        m = md5(fp)
        for k, v in tm.items():
            if m == v:
                print("命中 %-26s -> %s\\%s" % (k, d, fn))

print("\n--- 待复核_立绘 miy02a ---")
for ln in open(os.path.join(UNI, "待复核_立绘.tsv"), encoding="utf-8").read().splitlines():
    if ln.startswith("miy02a"):
        print(ln)
print("\n--- 统一说明_CG背景 中 miy02a 相关 ---")
t = open(os.path.join(UNI, "统一说明_CG背景.md"), encoding="utf-8").read().splitlines()
for i, ln in enumerate(t):
    if "miy02a" in ln:
        print("%d: %s" % (i + 1, ln))