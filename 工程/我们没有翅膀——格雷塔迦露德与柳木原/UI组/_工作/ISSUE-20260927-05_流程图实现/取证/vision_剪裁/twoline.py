# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    c=a[...,:3]*(a[...,3:4]/255.0)
    return 0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2]
cases=[("E1 frag 恐怖…逆袭",P+"E1_13_屏2_巡演图_终版数据.png",892,665,8,55),
       ("E2 sec 我果然…（略）",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png",516,760,8,55)]
for tag,png,x0,y0,pt,pb in cases:
    lum=load(png)
    print("="*110); print(tag," element=(%d,%d) plate=%d..%d"%(x0,y0,pt,pb))
    for nm,rng in [("TOP",range(6,18)),("BOTTOM",range(44,58))]:
        print("--",nm)
        for off in rng:
            row=lum[y0+off, x0+30:x0+266]
            dk=np.where(row<96)[0]
            print("  off %2d | min %6.1f | med %6.1f | ink px %3d | cols %s"%(
                off,row.min(),np.median(row),len(dk),
                (str(dk[:24]+30).replace(' ','')) if len(dk) else "-"))
