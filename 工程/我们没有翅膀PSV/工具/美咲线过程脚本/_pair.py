# -*- coding: utf-8 -*-
import os, re, collections
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
files = sorted(f for f in os.listdir(SCRIPTS) if os.path.isfile(os.path.join(SCRIPTS,f)))
pairs = collections.Counter()
detail = []
for f in files:
    lines = open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace').split('\n')
    for i,ln in enumerate(lines):
        if re.match(r'^\s*:Image\b', ln.rstrip('\r')):
            args = ln.split(':',2)[2] if False else ln.strip()[6:].strip()
            args = args.split('//')[0].strip()
            # legacy comments: nearest preceding trans_bg / trans_cg / cg_in / ec_in / eyecatch
            legacy = None
            for j in range(i-1, max(-1,i-20), -1):
                s = lines[j]
                m = re.search(r'//\s*(trans_bg|trans_cg)\s+([^/]*)', s)
                if m:
                    legacy = m.group(1)+" "+m.group(2).strip(); break
                m = re.search(r'//\s*(cg_in|ec_in|eyecatch|cg_out)\s*\(?([^/]*)', s)
                if m: 
                    legacy = m.group(1)+" "+m.group(2).strip(); break
            pairs[(legacy, args)] += 1
            detail.append((f,i+1,legacy,args))
print("=== (legacy comment, :Image args) ===")
for (leg,args),v in sorted(pairs.items(), key=lambda x:-x[1]):
    print("  %-32s -> %-14s  %d" % (str(leg), args, v))
