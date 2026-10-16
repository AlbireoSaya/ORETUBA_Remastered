# -*- coding: utf-8 -*-
import os, re, collections, json
SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"
img_lines = json.load(open(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\_img_lines.json"))

# global positional stats
print("=== 2-field: field2 histogram ===")
c = collections.Counter()
for f,ln,tt,args,ec in img_lines:
    a=[x.strip() for x in args.split(',')]
    if len(a)==2: c[int(a[1])]+=1
for k,v in sorted(c.items()): print("  f2=%-4d %d" % (k,v))

print("\n=== 3-field: (f2,f3) histogram ===")
c3 = collections.Counter()
for f,ln,tt,args,ec in img_lines:
    a=[x.strip() for x in args.split(',')]
    if len(a)==3: c3[(int(a[1]),int(a[2]))]+=1
for k,v in sorted(c3.items()): print("  %s %d" % (k,v))

print("\n=== 4-field: (f1,f2,f3,f4) histogram ===")
c4 = collections.Counter()
for f,ln,tt,args,ec in img_lines:
    a=[x.strip() for x in args.split(',')]
    if len(a)==4: c4[tuple(int(x) for x in a)]+=1
for k,v in sorted(c4.items()): print("  %-22s %d" % (str(k),v))

print("\n=== eyecatch-comment vs actual args pairs ===")
pairs=[]
for f,ln,tt,args,ec in img_lines:
    if ec: pairs.append((f,ln,ec,args))
for p in sorted(pairs, key=lambda x:(x[2],x[0])): print("  %-14s L%-7d comment=%-8s args=%s" % p)
