# -*- coding: utf-8 -*-
import os, csv, collections
ROOT = r"E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
TSV = os.path.join(ROOT, "_工作", "M34_资产引用矩阵.tsv")
rows=[]
with open(TSV,encoding="utf-8") as f:
    r=csv.reader(f,delimiter="\t"); next(r)
    for row in r:
        fn,size,ns,scs,det=row
        rows.append((fn,int(size),set(x for x in scs.split(",") if x),det))

# 原版件 (no x_ prefix)
orig=[(fn,s,sc,det) for fn,s,sc,det in rows if not fn.startswith("x_")]
print("=== 原版件(无 x_ 前缀) %d件 %.3f MB ===" % (len(orig), sum(s for _,s,_,_ in orig)/1048576.0))
for fn,s,sc,det in sorted(orig):
    print("  %-16s %9d  %s" % (fn,s,",".join(sorted(sc)) if sc else "(零屏引用)"))

print("\n=== 被 >=2 屏共用的素材 ===")
multi=[(fn,s,sc,det) for fn,s,sc,det in rows if len(sc)>=2]
for fn,s,sc,det in sorted(multi, key=lambda x:-len(x[2])):
    print("  %-40s %9d  %d屏: %s" % (fn,s,len(sc),",".join(sorted(sc))))
print("共用件数:",len(multi))

# assets referenced only by code (masks) - list group
print("\n=== 原版件中按族 ===")
fams=collections.defaultdict(lambda:[0,0])
for fn,s,sc,det in orig:
    if fn.startswith("sr_"): k="sr_01..24(片尾角色卡)"
    elif fn.startswith("paper_"): k="paper_0..7(纸屑粒子)"
    elif fn.startswith("snow_"): k="snow_0..4(雪粒子)"
    elif fn.startswith("if_"): k="if_*(九宫格原料)"
    elif fn.startswith("sel"): k="sel*(选择高亮条)"
    elif fn.startswith("sv_f"): k="sv_f1..5(F键帽)"
    elif fn.startswith("dlg_bg"): k="dlg_bg_26..28(对话窗备选)"
    elif fn.startswith("nm_frm"): k="nm_frm_a/b/g(名字框)"
    elif fn.startswith("th_") or fn.startswith("ui_bg") or fn.startswith("gc_") or fn.startswith("ec_bg"): k="th_*/ui_bg01/gc_*/ec_bg(缩略图)"
    elif fn.startswith("tl1_bg") or fn.startswith("tl2_bg"): k="tl*_bg(原版标题背景)"
    elif fn.startswith("cf_"): k="cf_*(配置滚动条)"
    else: k=fn
    fams[k][0]+=1; fams[k][1]+=s
for k in sorted(fams,key=lambda x:-fams[x][1]):
    print("  %-38s %3d件 %.3f MB" % (k,fams[k][0],fams[k][1]/1048576.0))
