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
PLATE={'section':(8,55),'select':(8,56),'frag':(8,55)}
# select 素材在 rows 55/56 有深色描边 → 文字搜索限定 row 10..54，另单独报描边带
def draw(img,jpng,tag):
    d=json.load(open(jpng,encoding='utf-8')); els={e['id']:e for e in d['elements']}
    L=lum(img); plat={}
    print("==",tag)
    print("  %-15s %-7s %-20s %6s %6s %6s %6s %6s %6s %6s"%(
        "id","kind","sample","上留","下留","墨顶","墨底","行数","最宽行","行距"))
    for e in d['elements']:
        if not (e['kind']=='image' and str(e.get('asset','')).startswith('ui/x_ui_node_')): continue
        k=e['asset'].split('x_ui_node_')[1].split('_')[0]; x0,y0=e['x'],e['y']
        pt,pb=PLATE[k]
        r0,r1=10,54              # 避开 select 的深色边框带
        inner=L[y0:y0+65, x0+30:x0+266]
        rows=[]
        for i in range(r0,r1+1):
            m=np.median(inner[i])
            if m>70 and (inner[i]<0.55*m).any(): rows.append(i)
        grp=[]
        for r in rows:
            if grp and r-grp[-1][-1]<=1: grp[-1].append(r)
            else: grp.append([r])
        # 最宽行
        wid=0
        for g in grp:
            sub=L[y0:y0+65, x0+16:x0+280][g[0]:g[-1]+1]
            dk=np.zeros(264,bool)
            for j in range(sub.shape[0]):
                m=np.median(sub[j])
                if m>70: dk |= (sub[j]<0.55*m)
            c=np.nonzero(dk)[0]
            if len(c): wid=max(wid,int(c.max()-c.min()+1))
        it,ib=grp[0][0],grp[-1][-1]
        pitch=(grp[1][0]-grp[0][0]) if len(grp)>1 else 0
        plat[e['id']]=(it-pt,pb-ib)
        sm=els.get(e['id']+'_tx',{}).get('sample','')
        print("  %-15s %-7s %-20s %6d %6d %6d %6d %6d %6d %6d"%(
            e['id'],k,sm[:18],it-pt,pb-ib,it,ib,len(grp),wid,pitch))
    badA=[k for k,(a,b) in plat.items() if a<5]
    badB=[k for k,(a,b) in plat.items() if b<5]
    print("  → 上留<5 的节点:",badA or "无"," ｜ 下留<5 的节点:",badB or "无")
E2=load(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png")
E1=load(P+"E1_13_屏2_巡演图_终版数据.png")
draw(E2,UI+"layout/screens/32_flowchart.json","屏一 E2_真实数据验收图_shot_84_flowchart.png")
draw(E1,P+"E1_07_屏2_flowchart.json","屏二 E1_13_屏2_巡演图_终版数据.png")
