# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
def label(mask):
    H,W=mask.shape; lab=np.zeros((H,W),np.int32); cur=0; out=[]
    ys,xs=np.nonzero(mask)
    for i in range(len(ys)):
        y,x=ys[i],xs[i]
        if lab[y,x]: continue
        cur+=1; st=[(y,x)]; lab[y,x]=cur; n=0
        miny=maxy=y; minx=maxx=x
        while st:
            cy,cx=st.pop(); n+=1
            if cy<miny:miny=cy
            if cy>maxy:maxy=cy
            if cx<minx:minx=cx
            if cx>maxx:maxx=cx
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<H and 0<=nx<W and mask[ny,nx] and lab[ny,nx]==0:
                    lab[ny,nx]=cur; st.append((ny,nx))
        out.append((n,minx,maxx,miny,maxy))
    return out
for tag,f in [("屏1/E2",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png"),("屏2/E1",P+"E1_13_屏2_巡演图_终版数据.png")]:
    img=load(f); l=0.299*img[...,0]+0.587*img[...,1]+0.114*img[...,2]
    # 只扫画布区（排除顶部页签、右栏面板、底部滚动条）
    m=np.zeros_like(l,bool)
    m[180:1060, 55:1300]= l[180:1060,55:1300]>150
    comps=label(m)
    small=[c for c in comps if 60<c[0]<6000]
    small.sort(key=lambda c:-c[0])
    print("==",tag," 组件数(全部)",len(comps)," 小组件(60..6000px)",len(small))
    for n,x0,x1,y0,y1 in small[:14]:
        print("    %5dpx  x %4d..%4d y %4d..%4d  (%dx%d)"%(n,x0,x1,y0,y1,x1-x0+1,y1-y0+1))
    big=[c for c in comps if c[0]>=6000]
    print("    大组件 %d 个：x %d..%d y %d..%d"%(len(big),min(c[1] for c in big),max(c[2] for c in big),min(c[3] for c in big),max(c[4] for c in big)))
