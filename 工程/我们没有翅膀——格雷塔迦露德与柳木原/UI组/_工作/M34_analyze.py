# -*- coding: utf-8 -*-
import os, collections, csv

ROOT = r"E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
ASSETS = os.path.join(ROOT, "krkr", "assets", "ui")
TSV = os.path.join(ROOT, "_工作", "M34_资产引用矩阵.tsv")

# load matrix
refs = {}   # fn -> set(screens)
rows = []
with open(TSV, encoding="utf-8") as f:
    r = csv.reader(f, delimiter="\t")
    hdr = next(r)
    for row in r:
        fn, size, ns, scs, det = row
        size = int(size)
        scset = set(x for x in scs.split(",") if x)
        refs[fn] = scset
        rows.append((fn, size, scset, det))

def bucket(fn):
    if fn.startswith("x_gen_sd_"): return "x_gen_sd_*"
    if fn.startswith("x_gen_fc_"): return "x_gen_fc_*"
    if fn.startswith("x_gen_menu"): return "x_gen_menu*"
    if fn.startswith("x_gen_dicon"): return "x_gen_dicon_*"
    if fn.startswith("x_gen_icon"): return "x_gen_icon_*"
    if fn.startswith("x_gen_flownode"): return "x_gen_flownode_*"
    if fn.startswith("x_gen_ed_"): return "x_gen_ed_*"
    if fn.startswith("x_gen_dialog"): return "x_gen_dialog*"
    if fn.startswith("x_gen_gallerypage"): return "x_gen_gallerypage"
    if fn.startswith("x_gen_fragpage"): return "x_gen_fragpage"
    if fn.startswith("x_gen_logo"): return "x_gen_logo"
    if fn.startswith("x_title_logo"): return "x_title_logo"
    if fn.startswith("x_bg_system"): return "x_bg_system"
    if fn.startswith("x_mask_"): return "x_mask_*"
    if fn.startswith("x_"): return "x_other"
    return "原版件(无前缀)"

groups = collections.defaultdict(lambda: [0,0,set(),set()])
for fn, size, scset, det in rows:
    b = bucket(fn)
    g = groups[b]
    g[0]+=1; g[1]+=size
    for s in scset: g[2].add(s)
    if scset: g[3].add(fn)

print("=== 分组统计 (按前缀) ===")
tot=0; totb=0
for b in sorted(groups, key=lambda x:-groups[x][1]):
    n,by,scs,used = groups[b]
    tot+=n; totb+=by
    print("%-22s %4d件 %10.3f MB  引用屏: %s" % (b, n, by/1048576.0, ",".join(sorted(scs)) if scs else "(无)"))
print("TOTAL %d件 %.3f MB" % (tot, totb/1048576.0))

KEEP_SCREENS = {"title","gallery","fragment"}
print("\n=== 保留屏引用统计 ===")
for sid in ["title","gallery","fragment"]:
    fs = [fn for fn,size,scs,det in rows if sid in scs]
    b = sum(dict((f,s) for f,s,_,_ in rows)[fn] for fn in fs)
    print("%s: %d件 %.3f MB" % (sid, len(fs), b/1048576.0))
    for fn in sorted(fs): print("    ", fn)

# union keep
keep = set(fn for fn,size,scs,det in rows if scs & KEEP_SCREENS)
print("\n保留屏并集: %d件" % len(keep))

# shared: in keep and also referenced by non-keep screen
shared = []
for fn,size,scs,det in rows:
    if fn in keep and (scs - KEEP_SCREENS):
        shared.append((fn,size,sorted(scs),det))
print("\n=== 共用(保留屏 ∩ 弃用屏) %d件 ===" % len(shared))
for fn,size,scs,det in sorted(shared):
    print("%-40s %8d  %s" % (fn,size,",".join(scs)))

# unreferenced by any screen
unref = [fn for fn,size,scs,det in rows if not scs]
print("\n=== 零屏引用 %d件 %.3f MB ===" % (len(unref), sum(dict((f,s) for f,s,_,_ in rows)[f] for f in unref)/1048576.0))
for fn in sorted(unref): print("   ", fn)

# discard = phys - keep
disc = [(fn,size,scs) for fn,size,scs,det in rows if fn not in keep]
print("\n=== 可弃用(未被保留屏引用) %d件 %.3f MB ===" % (len(disc), sum(s for _,s,_ in disc)/1048576.0))
