# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
REF={'section':(195,213,244),'select':(96,171,211),'frag':(208,176,244)}
for tag,png,js in [("屏1/E2",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png",UI+"layout/screens/32_flowchart.json"),
                   ("屏2/E1",P+"E1_13_屏2_巡演图_终版数据.png",P+"E1_07_屏2_flowchart.json")]:
    img=load(png); d=json.load(open(js,encoding='utf-8')); els={e['id']:e for e in d['elements']}
    print("==",tag); bad=0
    for e in d['elements']:
        if e['kind']=='image' and str(e.get('asset','')).startswith('ui/x_ui_node_'):
            k=e['asset'].split('x_ui_node_')[1].split('_')[0]
            seg=img[e['y']+10:e['y']+54, e['x']+30:e['x']+266].reshape(-1,3)
            l=0.299*seg[:,0]+0.587*seg[:,1]+0.114*seg[:,2]
            med=np.median(seg[l>np.percentile(l,60)],axis=0)
            dist={kk:float(np.linalg.norm(med-np.array(vv))) for kk,vv in REF.items()}
            best=min(dist,key=dist.get)
            ok = best==k
            if not ok: bad+=1
            tx=els.get(e['id']+'_tx',{}).get('sample','')
            print("   %-15s 声明 %-7s 实测最接近 %-7s (d=%.1f/%.1f/%.1f) %s  %s"%(
                e['id'],k,best,dist['section'],dist['select'],dist['frag'],"OK" if ok else "✗不一致",tx[:20]))
    print("   类型与素材不一致节点数 =",bad)
