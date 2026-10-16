# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, io, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    c=a[...,:3]*(a[...,3:4]/255.0)
    return 0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2]

def nodes_of(jsonpath):
    d=json.load(open(jsonpath,encoding='utf-8'))
    els={e['id']:e for e in d['elements']}
    out=[]
    for e in d['elements']:
        if e['kind']=='image' and str(e.get('asset','')).startswith('ui/x_ui_node_'):
            k=e['asset'].split('x_ui_node_')[1].split('_')[0]
            tx=els.get(e['id']+'_tx')
            out.append(dict(id=e['id'],kind=k,x=e['x'],y=e['y'],w=e['w'],h=e['h'],
                            sample=(tx or {}).get('sample',''),
                            size=(tx or {}).get('font',{}).get('size')))
    return out

PLATE={'section':(8,55),'select':(8,56),'frag':(8,55)}

def analyse(lum,nd):
    x0,y0,w,h=nd['x'],nd['y'],nd['w'],nd['h']
    top,bot=PLATE[nd['kind']]
    band=lum[y0:y0+h, x0+30:x0+266]           # 236px interior band (text box 240 centred)
    bandf=lum[y0:y0+h, x0+6:x0+290]           # wider for width check
    med=np.median(band,axis=1)
    plate=np.median(med[top:bot+1])
    T=0.60*plate                               # ink threshold (plate~194 -> 116)
    rows_soft=[i for i in range(h) if band[i].min()<T]
    rows_hard=[i for i in range(h) if band[i].min()<70]
    # line grouping on soft rows
    groups=[]
    for r in rows_soft:
        if groups and r-groups[-1][-1]<=2: groups[-1].append(r)
        else: groups.append([r])
    widths=[]
    for g in groups:
        sub=bandf[g[0]:g[-1]+1]
        cols=np.where((sub<T).any(axis=0))[0]
        widths.append(int(cols.max()-cols.min()+1) if len(cols) else 0)
    ink_top = rows_soft[0] if rows_soft else None
    ink_bot = rows_soft[-1] if rows_soft else None
    dup = ink_top-(top+5) if ink_top is not None else None   # >=0 满足“首行上留>=5”
    dbot= (bot-5)-ink_bot if ink_bot is not None else None
    hard_top = rows_hard[0] if rows_hard else None
    hard_bot = rows_hard[-1] if rows_hard else None
    return dict(id=nd['id'],kind=nd['kind'],sample=nd['sample'],size=nd['size'],
                plate=plate,plate_top=top,plate_bot=bot,
                ink_top=ink_top,ink_bot=ink_bot,hard_top=hard_top,hard_bot=hard_bot,
                mtop=ink_top-top if ink_top is not None else None,
                mbot=bot-ink_bot if ink_bot is not None else None,
                nmargin_top=(ink_top-(top+5)) if ink_top is not None else None,
                nmargin_bot=((bot-5)-ink_bot) if ink_bot is not None else None,
                lines=len(groups),widths=widths,
                line_rows=[[g[0],g[-1]] for g in groups])

for label,png,js in [("屏1 E2_shot_84", P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png", UI+"layout/screens/32_flowchart.json"),
                     ("屏2 E1_13", P+"E1_13_屏2_巡演图_终版数据.png", P+"E1_07_屏2_flowchart.json")]:
    lum=load(png); nds=nodes_of(js)
    print("="*100); print(label,"| nodes",len(nds))
    print("%-16s %-8s %-24s %4s %4s %4s %4s | %5s %5s | %5s %5s | %s"%(
        "id","kind","sample","pTop","pBot","iTop","iBot","上留","下留","A余","B余","lines/widths"))
    badA=badB=[]
    for nd in nds:
        r=analyse(lum,nd)
        print("%-16s %-8s %-24s %4d %4d %4s %4s | %5d %5d | %+5d %+5d | %d %s  hard[%s..%s]"%(
            r['id'],r['kind'],r['sample'][:22],r['plate_top'],r['plate_bot'],
            r['ink_top'],r['ink_bot'],r['mtop'],r['mbot'],r['nmargin_top'],r['nmargin_bot'],
            r['lines'],r['widths'],r['hard_top'],r['hard_bot']))
        if r['nmargin_top'] is not None and r['nmargin_top']<0: badA.append(r['id'])
        if r['nmargin_bot'] is not None and r['nmargin_bot']<0: badB.append(r['id'])
    print("  判据A不达(<5px) :",badA or "无")
    print("  判据B不达(<5px) :",badB or "无")
