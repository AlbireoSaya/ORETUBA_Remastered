# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
for tag,f in [("屏2/E1",P+"E1_13_屏2_巡演图_终版数据.png"),("屏1/E2",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png")]:
    E=load(f); l=0.299*E[...,0]+0.587*E[...,1]+0.114*E[...,2]
    print("==",tag)
    sub=l[:,1296:1920]
    ys,xs=np.nonzero(sub>50)
    if len(xs): print("   x>=1296 亮像素 x 范围 %d..%d  y 范围 %d..%d  计数 %d"%(xs.min()+1296,xs.max()+1296,ys.min(),ys.max(),len(xs)))
    # per column coverage
    prof=(sub>50).mean(axis=0)
    nz=[i+1296 for i,v in enumerate(prof) if v>0.005]
    print("   有亮像素的列:", (nz[0],nz[-1]) if nz else None, " 列数",len(nz))
    # panel left edge: first col with coverage >0.3
    hi=[i+1296 for i,v in enumerate(prof) if v>0.3]
    print("   覆盖率>0.3 的列:", (hi[0],hi[-1]) if hi else None)
    # the vertical light bar (drag handle)
    for x in range(1300,1360):
        c=sub[:,x-1296]
        if (c>120).sum()>30:
            ys2=np.nonzero(c>120)[0]
            print("     竖亮条 x=%d  y %d..%d"%(x,ys2.min(),ys2.max()))
