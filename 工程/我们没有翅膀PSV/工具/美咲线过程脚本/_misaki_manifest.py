# -*- coding: utf-8 -*-
import os, re, collections
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
base = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线"
lst = [l.strip() for l in open(base+r"\_cpklist\SystemData.cpk.txt",encoding="utf-8") if l.strip()]
ecb = [n for n in lst if re.match(r'^ec_bg\d+[A-Z]?\.png$', n)]
lst2 = [l.strip() for l in open(base+r"\_cpklist\CG.cpk.txt",encoding="utf-8") if l.strip()]
ecf = [n for n in lst2 if re.match(r'^EC\d+\.png$', n, re.I)]
mis = sorted([f for f in os.listdir(SCRIPTS) if re.match(r'^M\d\d_\d\d$', f)]) + \
      sorted([f for f in os.listdir(SCRIPTS) if re.match(r'^P03_01[A-D]$', f)])
tot = collections.Counter(); per = {}
for f in mis:
    for ln in open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace').split('\n'):
        if not re.match(r'^\s*:Image\b', ln.rstrip('\r')): continue
        args = ln.strip()[6:].split('//')[0].strip()
        tot[args]+=1; per.setdefault(args,[]).append(f)
print("total :Image in Misaki line:", sum(tot.values()))
for a,v in sorted(tot.items(), key=lambda x:-x[1]):
    x=[int(t) for t in a.split(',')]
    fl = ("EC%02d.png"%x[1]) if x[0]==0 and x[1]>0 else ("(none)" if x[1]==-1 else "?")
    if x[0]==1: fl = ecb[x[2]]
    print("  %-14s x%-4d -> %-16s  files: %s" % (a, v, fl, ",".join(per[a]) if v<20 else "%d files"%len(per[a])))
print("\n[0,27] count:", tot.get("0,27"))
