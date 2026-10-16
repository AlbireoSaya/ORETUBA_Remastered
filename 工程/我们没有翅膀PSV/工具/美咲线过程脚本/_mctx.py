# -*- coding: utf-8 -*-
import os, re
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
sites = [("M09_01",6968),("P01_01D",2570),("P02_01E",1711),("P03_01D",3471),("S01_01",131),("S01_01",146),
         ("S01_15B",986),("S01_17A",2337),("S02_15C",9145),("S03C_19A",3179),("S03_21C",1023),
         ("S04_06J2",439),("S04_27A",2282)]
out=[]
for f,ln in sites:
    lines = open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace').split('\n')
    out.append("=== %s : line %d ===" % (f,ln))
    for j in range(max(0,ln-8), min(len(lines), ln+7)):
        mark = ">>" if j==ln-1 else "  "
        out.append("%s %s" % (mark, lines[j].rstrip('\r')))
    out.append("")
open(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\_movie_sites.txt","w",encoding="utf-8").write("\n".join(out))
print("\n".join(out[:60]))
