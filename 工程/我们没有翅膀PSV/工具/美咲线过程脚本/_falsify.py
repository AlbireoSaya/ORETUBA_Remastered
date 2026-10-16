# -*- coding: utf-8 -*-
import os, re, collections
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
base = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线"
lst = [l.strip() for l in open(base+r"\_cpklist\SystemData.cpk.txt",encoding="utf-8") if l.strip()]
ecb = [n for n in lst if re.match(r'^ec_bg\d+[A-Z]?\.png$', n)]
lst2 = [l.strip() for l in open(base+r"\_cpklist\CG.cpk.txt",encoding="utf-8") if l.strip()]
ecf = [n for n in lst2 if re.match(r'^EC\d+\.png$', n, re.I)]

bs=collections.Counter(); Ns=collections.Counter(); ss=collections.Counter(); fs=collections.Counter()
for f in sorted(os.listdir(SCRIPTS)):
    p=os.path.join(SCRIPTS,f)
    if not os.path.isfile(p): continue
    for ln in open(p,'rb').read().decode('shift_jis',errors='replace').split('\n'):
        if not re.match(r'^\s*:Image\b', ln.rstrip('\r')): continue
        a=[int(x) for x in ln.strip()[6:].split('//')[0].strip().split(',')]
        if a[0]==0: Ns[a[1]]+=1
        else:
            ss[a[1]]+=1; bs[a[2]]+=1
            if len(a)>3: fs[a[3]]+=1
print("[FALSIFY 1] mode-1 field3 (b) range: min=%d max=%d distinct=%d" % (min(bs), max(bs), len(bs)))
bad=[b for b in bs if not (0<=b<len(ecb))]
print("   out-of-range b:", bad if bad else "NONE  -> every b resolves to an existing ec_bg file")
print("   resolved files:", ", ".join(sorted(ecb[b] for b in bs)))
print("[FALSIFY 2] mode-0 field2 (N) range: min=%d max=%d distinct=%d" % (min(Ns), max(Ns), len(Ns)))
print("   N values:", sorted(Ns))
print("   EC list size:", len(ecf), " -> valid 1-based range 1..%d" % len(ecf))
bad2=[n for n in Ns if not (1<=n<=len(ecf)) and n!=-1]
print("   out-of-range N:", bad2 if bad2 else "NONE (except N=-1 x%d which has no file)" % Ns.get(-1,0))
print("[INFO] mode-1 field2 (s):", sorted(ss))
print("[INFO] mode-1 field4 (f):", sorted(fs))
