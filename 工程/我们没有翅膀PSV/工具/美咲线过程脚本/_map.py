# -*- coding: utf-8 -*-
import re, os
base = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线"
lst = [l.strip() for l in open(base + r"\_cpklist\SystemData.cpk.txt", encoding="utf-8") if l.strip()]
ecb = [n for n in lst if re.match(r'^ec_bg\d+[A-Z]?\.png$', n)]
print("ec_bg file count:", len(ecb))
idx = {n:i for i,n in enumerate(ecb)}
rev = {i:n for i,n in enumerate(ecb)}
for i,n in enumerate(ecb): print("  idx %3d -> %s" % (i,n))
