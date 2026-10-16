# -*- coding: utf-8 -*-
import os, re
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
MOV = {0:"OP00.usm",1:"OP01.usm",2:"OP02.usm",3:"ED_ai.usm",4:"ED_asuka.usm",5:"ED_hiyoko.usm",
       6:"ED_kobato.usm",7:"ED_misaki.usm",8:"ED_miyako.usm",9:"ED_naru.usm",10:"Poem.usm",11:"OP03.usm"}
files = sorted(f for f in os.listdir(SCRIPTS) if os.path.isfile(os.path.join(SCRIPTS,f)))
print("%-12s %-6s %-14s %-14s %s" % ("script","line","Movie","usm","SceneName / header comment"))
for f in files:
    txt = open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace')
    lines = txt.split('\n')
    for i,ln in enumerate(lines):
        m = re.match(r'^\s*:Movie\s+(\d+)\s*$', ln.rstrip('\r'))
        if not m: continue
        n = int(m.group(1))
        # scene name
        sn = ''
        for j in range(0, min(len(lines), 40)):
            m2 = re.search(r':SceneName\s+"?([^"\r\n]*)', lines[j])
            if m2: sn = m2.group(1).strip(); break
        print("%-12s L%-5d Movie%-2d %-16s %s" % (f, i+1, n, MOV.get(n,'?'), sn))
