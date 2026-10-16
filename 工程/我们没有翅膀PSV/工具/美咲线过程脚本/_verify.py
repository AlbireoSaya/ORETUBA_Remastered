# -*- coding: utf-8 -*-
import os, re, collections
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
base = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线"

# --- ec_bg list in CPK TOC order ---
lst = [l.strip() for l in open(base+r"\_cpklist\SystemData.cpk.txt",encoding="utf-8") if l.strip()]
ecb = [n for n in lst if re.match(r'^ec_bg\d+[A-Z]?\.png$', n)]
ecb_idx = {n:i for i,n in enumerate(ecb)}

# --- EC list in CPK TOC order (1-based index) ---
lst2 = [l.strip() for l in open(base+r"\_cpklist\CG.cpk.txt",encoding="utf-8") if l.strip()]
ecf = [n for n in lst2 if re.match(r'^EC\d+\.png$', n, re.I)]
ecf_1b = {n:i+1 for i,n in enumerate(ecf)}
print("EC files (1-based idx):")
for n in ecf: print("   %2d -> %s" % (ecf_1b[n], n))
print()

files = sorted(f for f in os.listdir(SCRIPTS) if os.path.isfile(os.path.join(SCRIPTS,f)))
m0 = collections.Counter(); m1 = collections.Counter()
m0ex = []; m1ok = 0; m1bad = []
for f in files:
    lines = open(os.path.join(SCRIPTS,f),'rb').read().decode('shift_jis',errors='replace').split('\n')
    for i,ln in enumerate(lines):
        if not re.match(r'^\s*:Image\b', ln.rstrip('\r')): continue
        args = ln.strip()[6:].split('//')[0].strip()
        a = [int(x) for x in args.split(',')]
        legacy = None
        for j in range(i-1, max(-1,i-20), -1):
            mm = re.search(r'//\s*(?:trans_bg|trans_cg)\s+([^/]*)', lines[j])
            if mm: legacy = mm.group(1).strip(); break
            mm = re.search(r'//\s*eyecatch\s*([0-9,\s]+)', lines[j])
            if mm: legacy = "eyecatch "+mm.group(1).strip(); break
        if a[0]==0:
            n = a[1]
            if legacy:
                mm = re.search(r'EC(\d+)', legacy)
                if mm:
                    m0[(int(mm.group(1)), n)] += 1
                    pred = None
                    for k,v in ecf_1b.items():
                        if v==n: pred = k
                    ok = (pred == "EC%02d.png"%int(mm.group(1)))
                    m0ex.append((f,i+1,int(mm.group(1)),n,pred,ok))
        else:
            s,b,ff = a[1],a[2],(a[3] if len(a)>3 else None)
            fn = ecb[b] if 0<=b<len(ecb) else None
            m1[(legacy, fn)] += 1
            if legacy and legacy.startswith("eyecatch"):
                want = int(re.match(r'eyecatch\s*(\d+)', legacy).group(1))
                got = int(re.match(r'ec_bg(\d+)', fn).group(1)) if fn else -1
                if got==want: m1ok+=1
                else: m1bad.append((f,i+1,legacy,args,fn))
print("=== mode 0: (legacy EC number, :Image N) ===")
for k,v in sorted(m0.items()): print("   EC%-3d -> N=%-3d  x%d" % (k[0],k[1],v))
print("\n=== mode 0 verification (rule: N = 1-based index of EC file in CG.cpk TOC order) ===")
for f,l,ecn,n,pred,ok in sorted(m0ex, key=lambda x:x[2]):
    print("   %-10s L%-6d EC%-3d -> N=%-3d  predicted=%-6s %s" % (f,l,ecn,n,pred,"OK" if ok else "MISMATCH"))
print("\nmode0 samples:", len(m0ex), " ok:", sum(1 for x in m0ex if x[5]))
print("\n=== mode 1 verification (rule: field3 = 0-based index into ec_bg list in SystemData.cpk order) ===")
print("mode1 lines with eyecatch comment:", m1ok+len(m1bad), " base-number agreed:", m1ok, " disagreed:", len(m1bad))
for x in m1bad: print("   MISMATCH", x)
print("\n=== mode 1: (comment, resolved ec_bg file) ===")
for (leg,fn),v in sorted(m1.items(), key=lambda x: (str(x[0][0]), x[0][1] or "")):
    print("   %-20s -> %-16s x%d" % (str(leg), str(fn), v))
