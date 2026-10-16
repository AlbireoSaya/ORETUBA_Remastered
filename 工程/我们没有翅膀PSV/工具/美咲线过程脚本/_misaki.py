# -*- coding: utf-8 -*-
import os, re
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
mis = []
for f in sorted(os.listdir(SCRIPTS)):
    if re.match(r'^M\d\d_\d\d$', f): mis.append(f)
for f in sorted(os.listdir(SCRIPTS)):
    if re.match(r'^P03_01[A-D]$', f): mis.append(f)
print("Misaki-line scripts (%d): %s" % (len(mis), " ".join(mis)))
print()
for f in mis:
    lines = open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace').split('\n')
    hits=[]
    for i,ln in enumerate(lines):
        if re.match(r'^\s*:Image\b', ln.rstrip('\r')):
            args = ln.strip()[6:].split('//')[0].strip()
            legacy=''
            for j in range(i-1,max(-1,i-20),-1):
                m = re.search(r'//\s*(trans_bg|trans_cg|eyecatch|cg_in)\s*([^/]*)', lines[j])
                if m: legacy = m.group(1)+" "+m.group(2).strip(); break
            hits.append((i+1,args,legacy))
    print("%-10s %d hits" % (f, len(hits)))
    for ln,args,leg in hits:
        print("    L%-6d :Image %-14s  %s" % (ln,args,leg))
