# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
E1=load(P+"E1_13_屏2_巡演图_终版数据.png"); E2=load(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png")
def lum(r): return 0.299*r[...,0]+0.587*r[...,1]+0.114*r[...,2]
def linkstats(img,pts,name):
    out=[]
    for (x,y) in pts:
        w=img[y-6:y+7, x-6:x+7].reshape(-1,3)
        l=lum(w)
        # link pixel = farthest from local bg (the most common color)
        bgc=w[int(np.argmin(l))]
        dist=np.linalg.norm(w-bgc,axis=1)
        c=w[int(np.argmax(dist))]
        out.append((x,y,tuple(int(v) for v in c),float(lum(c))))
    print(name)
    for x,y,c,L in out: print("   (%4d,%4d) #%02X%02X%02X lum=%.1f"%(x,y,c[0],c[1],c[2],L))
    arr=np.array([o[3] for o in out]); print("   min/max lum %.1f / %.1f"%(arr.min(),arr.max()))
    return out
# E1 vertical links at x=664 between nodes (node pitch 95, element h=65) -> gap y 255..285
linkstats(E1,[(664,262),(664,270),(664,278),(664,500),(664,700)],"E1 竖线 x=664（节点间 30px 缝隙）")
# E2: which links? read json
d=json.load(open(UI+"layout/screens/32_flowchart.json",encoding='utf-8'))
print("E2/屏1 links:")
for l in d['links']:
    print("   %s pts=%s w=%s color=#%08X arrow=%s"%(l['id'],l['pts'],l['w'],l['color'],l['arrow']))
d2=json.load(open(P+"E1_07_屏2_flowchart.json",encoding='utf-8'))
print("E1/屏2 links:")
for l in d2['links']:
    print("   %s pts=%s w=%s color=#%08X arrow=%s"%(l['id'],l['pts'],l['w'],l['color'],l['arrow']))
