# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一"
WANT = ["tl_galry", "tl_cfg", "tl_exit", "tl_load", "tl_chk", "ec2_name", "ec3_name",
        "ss_bg1", "ss_bg5", "tl_01", "tl_04", "ec1_bg", "ec2_bg", "ec3_bg", "ec4_bg", "ec6_bg",
        "tl_new", "gl_music", "gl_chr1", "gl_chr2", "gl_chrbg", "gl_scene", "tl_logo"]
W = set(WANT)
for f in ["清单_系统UI.tsv", "待复核_系统UI.tsv"]:
    print("=" * 20, f)
    lines = open(os.path.join(BASE, f), encoding="utf-8").read().splitlines()
    print(lines[0])
    for ln in lines[1:]:
        c = ln.split("\t")
        if c[0].rsplit(".", 1)[0] in W:
            print(ln)