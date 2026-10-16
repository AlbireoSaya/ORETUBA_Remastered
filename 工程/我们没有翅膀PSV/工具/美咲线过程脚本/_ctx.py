# -*- coding: utf-8 -*-
import os, re, json
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
files = sorted(f for f in os.listdir(SCRIPTS) if os.path.isfile(os.path.join(SCRIPTS,f)))
out = open(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\_image_ctx.txt","w",encoding="utf-8")
for f in files:
    lines = open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace').split('\n')
    for i,ln in enumerate(lines):
        if re.match(r'^\s*:Image\b', ln.rstrip('\r')):
            out.write("=== %s:%d  %s\n" % (f, i+1, ln.strip()))
            for j in range(max(0,i-14), i):
                s = lines[j].rstrip('\r')
                if s.strip() and s.strip() not in ('{','}'):
                    out.write("      | %s\n" % s)
out.close()
print("done")
