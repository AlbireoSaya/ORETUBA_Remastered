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
for tag,img in [("屏2/E1",E1),("屏1/E2",E2)]:
    l=lum(img)
    print("==",tag)
    # horizontal profile at y=500 (mid canvas) : find bright structural elements
    y=500
    row=l[y]
    br=np.where(row>120)[0]
    # group
    grp=[]
    for x in br:
        if grp and x-grp[-1][-1]<=3: grp[-1].append(x)
        else: grp.append([x])
    print("   y=500 亮区(x>120):",[(g[0],g[-1]) for g in grp if len(g)>2])
    # vertical scrollbar: find tall thin bright column near x 1280..1340
    for x in range(1270,1350):
        col=l[250:1050,x]
        if (col>120).mean()>0.5:
            print("      竖条 x=%d 亮覆盖 %.2f"%(x,(col>120).mean()))
    # right panel left edge
    for x in range(1290,1400):
        col=l[200:1050,x]
        if (col>60).mean()>0.6:
            print("      右面板候选左沿 x=%d 覆盖 %.2f"%(x,(col>60).mean())); break
    # panels: find the dark panel edges by scanning for the panel border (lighter than backdrop)
    prof=(l[300:1000,:]>40).mean(axis=0)
    edges=[x for x in range(1,1920) if abs(prof[x]-prof[x-1])>0.5]
    print("   面板竖直边沿候选:",edges[:20])
# node/entry/label extents from json
for tag,js in [("屏1",UI+"layout/screens/32_flowchart.json"),("屏2",P+"E1_07_屏2_flowchart.json")]:
    d=json.load(open(js,encoding='utf-8'))
    xs=[(e['x'],e['x']+e['w']) for e in d['elements'] if e['kind'] in ('image','text') and e.get('visible_default',True)]
    nd=[(e['x'],e['x']+e['w']) for e in d['elements'] if str(e.get('asset','')).startswith('ui/x_ui_node_')]
    ent=[(e['x'],e['x']+e['w'],e['id']) for e in d['elements'] if str(e.get('asset','')).startswith('ui/x_ui_fusen')]
    lab=[(e['x'],e['x']+e['w'],e['id'],e.get('sample','')) for e in d['elements'] if e['id'].startswith('fc.label') and e['kind']=='text']
    print("==",tag," 节点 x 范围:",(min(a for a,b in nd),max(b for a,b in nd)))
    print("   入口标记:",ent)
    print("   组名标签 x 范围:",(min(a for a,b,c,d in lab),max(b for a,b,c,d in lab)),"| 文本盒宽:",sorted({b-a for a,b,c,d in lab}))
    for a,b,c,dd in lab: print("      %-18s x %d..%d  %s"%(c,a,b,dd))
    # right edge of all elements
    print("   全部元素 x+w max =",max(b for a,b in xs))
