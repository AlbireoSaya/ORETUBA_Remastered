# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    c=a[...,:3]*(a[...,3:4]/255.0)
    return 0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2]
def nodes_of(jp):
    d=json.load(open(jp,encoding='utf-8')); els={e['id']:e for e in d['elements']}; out=[]
    for e in d['elements']:
        if e['kind']=='image' and str(e.get('asset','')).startswith('ui/x_ui_node_'):
            k=e['asset'].split('x_ui_node_')[1].split('_')[0]; tx=els.get(e['id']+'_tx')
            out.append(dict(id=e['id'],kind=k,x=e['x'],y=e['y'],w=e['w'],h=e['h'],
                            sample=(tx or {}).get('sample',''),size=(tx or {}).get('font',{}).get('size')))
    return out
PLATE={'section':(8,55),'select':(8,56),'frag':(8,55)}
def analyse(lum,nd):
    x0,y0,h=nd['x'],nd['y'],nd['h']; top,bot=PLATE[nd['kind']]
    band=lum[y0:y0+h, x0+8:x0+288]        # 280 wide: covers body + a bit past text box
    med=np.median(band,axis=1)
    ink=np.zeros(h,bool)
    for i in range(h):
        if med[i]>70 and (band[i]<0.5*med[i]).any(): ink[i]=True
    rows=[i for i in range(h) if ink[i]]
    groups=[]
    for r in rows:
        if groups and r-groups[-1][-1]<=2: groups[-1].append(r)
        else: groups.append([r])
    widths=[];wcols=[]
    for g in groups:
        sub=band[g[0]:g[-1]+1]
        m=np.median(band[g[0]:g[-1]+1],axis=0)
        # per-row relative threshold, take union of dark pixels
        dark=np.zeros(sub.shape[1],bool)
        for j in range(sub.shape[0]):
            t=0.5*np.median(sub[j]) if np.median(sub[j])>70 else 0.5*0.0
            dark |= (sub[j]<t) if np.median(sub[j])>70 else (sub[j]<60)
        cols=np.where(dark)[0]
        widths.append(int(cols.max()-cols.min()+1) if len(cols) else 0)
        wcols.append((int(cols.min())+x0+8,int(cols.max())+x0+8) if len(cols) else None)
    it=rows[0] if rows else None; ib=rows[-1] if rows else None
    return dict(id=nd['id'],kind=nd['kind'],sample=nd['sample'],size=nd['size'],
        plate=round(float(np.median(med[top:bot+1])),1),top=top,bot=bot,
        it=it,ib=ib,mtop=(it-top) if it is not None else None,mbot=(bot-ib) if ib is not None else None,
        lines=len(groups),widths=widths,groups=[[g[0],g[-1]] for g in groups],cols=wcols)
for label,png,js in [("屏1 E2_shot_84",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png",UI+"layout/screens/32_flowchart.json"),
                     ("屏2 E1_13",P+"E1_13_屏2_巡演图_终版数据.png",P+"E1_07_屏2_flowchart.json")]:
    lum=load(png); nds=nodes_of(js)
    print("="*118); print(label,"| nodes",len(nds),"| 判据 上留>=5 下留>=5 (plate top/bot)")
    print("%-15s %-8s %-22s %5s %5s %5s %5s %5s %5s %5s %5s %5s %5s | %s"%(
        "id","kind","sample","plate","pT","pB","iTop","iBot","上留","下留","A余","B余","","lines|widths|xspan"))
    badA=[];badB=[]
    for nd in nds:
        r=analyse(lum,nd)
        a_ok = r['mtop'] is not None and r['mtop']>=5
        b_ok = r['mbot'] is not None and r['mbot']>=5
        if not a_ok: badA.append((r['id'],r['mtop']))
        if not b_ok: badB.append((r['id'],r['mbot']))
        print("%-15s %-8s %-22s %5.1f %5d %5d %5s %5s %5s %5s %+5d %+5d | %d %s %s"%(
            r['id'],r['kind'],r['sample'][:20],r['plate'],r['top'],r['bot'],r['it'],r['ib'],
            r['mtop'],r['mbot'],(r['mtop']-5) if r['mtop'] is not None else 0,
            (r['mbot']-5) if r['mbot'] is not None else 0,r['lines'],r['widths'],r['cols']))
    print("  ✗A(首行上留<5):",badA or "无")
    print("  ✗B(末行下留<5):",badB or "无")
