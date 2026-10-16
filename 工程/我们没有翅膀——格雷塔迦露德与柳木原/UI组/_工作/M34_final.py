# -*- coding: utf-8 -*-
import os, csv
ROOT=r"E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
TSV=os.path.join(ROOT,"_工作","M34_资产引用矩阵.tsv")
rows=[]
with open(TSV,encoding="utf-8") as f:
    r=csv.reader(f,delimiter="\t"); next(r)
    for row in r:
        fn,size,ns,scs,det=row
        rows.append((fn,int(size),set(x for x in scs.split(",") if x)))
D={fn:s for fn,s,_ in rows}
KEEP={"title","gallery","fragment"}
keep=[(fn,s) for fn,s,sc in rows if sc&KEEP]
disc=[(fn,s) for fn,s,sc in rows if not (sc&KEEP)]
def mb(b): return b/1048576.0
print("KEEP %d件 %.3f MB"%(len(keep),mb(sum(s for _,s in keep))))
for sid in ["title","gallery","fragment"]:
    fs=[(fn,s) for fn,s,sc in rows if sid in sc]
    print("  %s: %d件 %.3f MB"%(sid,len(fs),mb(sum(s for _,s in fs))))
print("DISCARD %d件 %.3f MB"%(len(disc),mb(sum(s for _,s in disc))))
# original no-prefix
orig=[(fn,s) for fn,s,sc in rows if not fn.startswith("x_")]
print("原版(无x_前缀) %d件 %.3f MB"%(len(orig),mb(sum(s for _,s in orig))))
# original referenced by kept screens
print("原版件被保留屏引用:", [fn for fn,s,sc in rows if not fn.startswith("x_") and (sc&KEEP)])
# code-referenced (masks) total
masks=[(fn,s) for fn,s,sc in rows if fn.startswith("x_mask_")]
print("x_mask 全族 %d件 %.3f MB"%(len(masks),mb(sum(s for _,s in masks))))
# keep list exact
print("\nKEEP LIST:")
for fn,s in sorted(keep): print("  %-32s %9d %.3f MB"%(fn,s,mb(s)))
