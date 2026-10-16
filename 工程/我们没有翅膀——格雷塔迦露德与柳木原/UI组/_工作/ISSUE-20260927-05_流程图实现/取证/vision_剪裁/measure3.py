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
def analyse(lum,nd,factors=(0.50,0.60)):
    x0,y0,h=nd['x'],nd['y'],nd['h']; top,bot=PLATE[nd['kind']]
    inner=lum[y0:y0+h, x0+30:x0+266]     # 236 px, clear of rounded corners
    wide =lum[y0:y0+h, x0+10:x0+286]     # 276 px, for width
    med=np.median(inner,axis=1)
    res={}
    for f in factors:
        rows=[]
        for i in range(h):
            if med[i]>70 and (inner[i]<f*med[i]).any(): rows.append(i)
        grp=[]
        for r in rows:
            if grp and r-grp[-1][-1]<=2: grp[-1].append(r)
            else: grp.append([r])
        res[f]=(rows,grp)
    plate=float(np.median(med[top:bot+1]))
    rows,grp=res[0.55] if 0.55 in res else res[factors[0]]
    rows,grp=res[factors[0]]
    # widths using absolute threshold on plate
    W=[];SPAN=[]
    for g in grp:
        dark=np.zeros(wide.shape[1],bool)
        for j in range(g[0],g[-1]+1):
            dark |= (wide[j] < 0.5*plate)
        cols=np.where(dark)[0]
        if len(cols): W.append(int(cols.max()-cols.min()+1)); SPAN.append((int(cols.min())+x0+10,int(cols.max())+x0+10))
        else: W.append(0); SPAN.append(None)
    return dict(id=nd['id'],kind=nd['kind'],sample=nd['sample'],plate=plate,top=top,bot=bot,
                rows=rows,grp=grp,W=W,SPAN=SPAN,res=res)
for label,png,js in [("屏1 E2_shot_84",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png",UI+"layout/screens/32_flowchart.json"),
                     ("屏2 E1_13",P+"E1_13_屏2_巡演图_终版数据.png",P+"E1_07_屏2_flowchart.json")]:
    lum=load(png); nds=nodes_of(js)
    print("="*126); print(label,"| nodes",len(nds),"| 判据: 首行墨迹顶 >= plateTop+5 ; 末行墨迹底 <= plateBot-5")
    hdr="%-15s %-7s %-21s %3s %3s | %-9s | %-9s | %-9s | %s"%("id","kind","sample","pT","pB","f0.50 t/b","f0.60 t/b","上留/下留(f.60)","lines rows | widths")
    print(hdr)
    bad=[]
    for nd in nds:
        r=analyse(lum,nd)
        r50=r['res'][0.50][0]; r60=r['res'][0.60][0]
        t50=(r50[0],r50[-1]) if r50 else None
        t60=(r60[0],r60[-1]) if r60 else None
        m60=((t60[0]-r['top']),(r['bot']-t60[-1])) if t60 else None
        ok = m60 and m60[0]>=5 and m60[1]>=5
        if not ok: bad.append((nd['id'],nd['kind'],m60))
        print("%-15s %-7s %-21s %3d %3d | %-9s | %-9s | %-9s | %d %s | %s"%(
            nd['id'],nd['kind'],nd['sample'][:19],r['top'],r['bot'],t50,t60,
            ("%d/%d"%(m60[0],m60[1])) if m60 else "-",
            len(r['grp']),r['grp'],r['W']))
    print("  ✗ 不达(f=0.60):",bad or "无")
