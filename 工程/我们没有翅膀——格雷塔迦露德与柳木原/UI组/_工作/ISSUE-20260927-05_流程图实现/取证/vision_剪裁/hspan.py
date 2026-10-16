# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
def lum(r): return 0.299*r[...,0]+0.587*r[...,1]+0.114*r[...,2]
def nodes_of(jp):
    d=json.load(open(jp,encoding='utf-8')); els={e['id']:e for e in d['elements']}; out=[]
    for e in d['elements']:
        if e['kind']=='image' and str(e.get('asset','')).startswith('ui/x_ui_node_'):
            tx=els.get(e['id']+'_tx'); out.append((e['id'],e['x'],e['y'],(tx or {}).get('sample',''),(tx or {}).get('x')))
    return out
for tag,png,js,boxw in [("屏1/E2",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png",UI+"layout/screens/32_flowchart.json",240),
                        ("屏2/E1",P+"E1_13_屏2_巡演图_终版数据.png",P+"E1_07_屏2_flowchart.json",240)]:
    L=lum(load(png)); print("==",tag)
    mx=[]
    for nid,x0,y0,sm,tx in nodes_of(js):
        inner=L[y0:y0+65, x0+30:x0+266]; med=np.median(inner,axis=1)
        ink=[i for i in range(65) if med[i]>70 and (inner[i]<0.55*med[i]).any()]
        if not ink: continue
        # per-row relative threshold over the whole node width
        sub=L[y0:y0+65, x0:x0+296]
        dark=np.zeros(296,bool)
        for j in ink:
            r=sub[j]; m=np.median(r)
            if m>70: dark |= (r<0.55*m)
        cols=np.nonzero(dark)[0]
        lo,hi=int(cols.min()),int(cols.max())
        bx0,bx1=(tx or x0+28), (tx or x0+28)+boxw
        ov_l=bx0-lo; ov_r=hi-(bx0+boxw-1)
        mx.append((hi-lo+1,nid,sm,lo,hi,ov_l,ov_r))
    mx.sort(reverse=True)
    print("   %-16s %-22s %5s %5s %5s %6s %6s"%("id","sample","宽","左缘","右缘","越左","越右"))
    for w,nid,sm,lo,hi,ol,orr in mx[:6]:
        print("   %-16s %-22s %5d %5d %5d %6d %6d"%(nid,sm[:20],w,lo,hi,ol,orr))
    print("   最宽行 %d px（文字盒 240px，余 %d px；越出文字盒的节点数 = %d）"%(
        mx[0][0],240-mx[0][0],sum(1 for w,*_ in mx if w>240)))
