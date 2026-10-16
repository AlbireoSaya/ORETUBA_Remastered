from PIL import Image
import numpy as np, sys, json

P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"

def load(name):
    a=np.array(Image.open(P+name).convert("RGBA")).astype(np.float64)
    c=a[...,:3]*(a[...,3:4]/255.0)
    lum=0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2]
    return c,lum

def label(mask):
    H,W=mask.shape
    lab=np.zeros((H,W),np.int32)
    cur=0
    comps=[]
    ys,xs=np.nonzero(mask)
    for i in range(len(ys)):
        y,x=ys[i],xs[i]
        if lab[y,x]: continue
        cur+=1
        stack=[(y,x)]; lab[y,x]=cur
        miny=maxy=y; minx=maxx=x; n=0
        while stack:
            cy,cx=stack.pop(); n+=1
            if cy<miny:miny=cy
            if cy>maxy:maxy=cy
            if cx<minx:minx=cx
            if cx>maxx:maxx=cx
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<H and 0<=nx<W and mask[ny,nx] and lab[ny,nx]==0:
                    lab[ny,nx]=cur; stack.append((ny,nx))
        comps.append(dict(id=cur,n=n,x0=minx,x1=maxx,y0=miny,y1=maxy,w=maxx-minx+1,h=maxy-miny+1))
    return lab,comps

for name in ["E1_13_屏2_巡演图_终版数据.png","E2_自证/E2_真实数据验收图_shot_84_flowchart.png"]:
    c,lum=load(name)
    mask=lum>90
    # restrict to canvas region (exclude header y<180, right panel x>1330)
    m=np.zeros_like(mask); m[180:1055, 60:1335]=mask[180:1055,60:1335]
    lab,comps=label(m)
    cand=[cc for cc in comps if cc['n']>3000 and 40<=cc['h']<=80 and cc['w']>=200]
    cand.sort(key=lambda cc:(cc['x0']//200, cc['y0']))
    print("==",name,"components total",len(comps),"node candidates",len(cand))
    for cc in cand:
        print("   x0=%d..%d (w=%d) y0=%d..%d (h=%d) n=%d"%(cc['x0'],cc['x1'],cc['w'],cc['y0'],cc['y1'],cc['h'],cc['n']))
    np.save(("e1" if name.startswith("E1") else "e2")+"_lum.npy", lum)
