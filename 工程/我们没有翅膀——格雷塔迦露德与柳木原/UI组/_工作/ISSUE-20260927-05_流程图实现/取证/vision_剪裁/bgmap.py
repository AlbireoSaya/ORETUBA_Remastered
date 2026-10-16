# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
for tag,f in [("屏1/E2",P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png"),("屏2/E1",P+"E1_13_屏2_巡演图_终版数据.png")]:
    E=load(f); l=0.299*E[...,0]+0.587*E[...,1]+0.114*E[...,2]
    print("==",tag)
    for (x,y) in [(680,270),(760,270),(680,500),(1090,340),(1250,500),(830,300),(1250,1005),(900,1010),(680,1010),(1200,200),(640,1050),(600,1017),(640,1017)]:
        c=E[y,x]; print("   (%4d,%4d) lum=%5.1f  #%02X%02X%02X"%(x,y,l[y,x],int(c[0]),int(c[1]),int(c[2])))
    # 连线两侧 5px 背景
    for (x,y) in [(672,270),(656,270),(1048,340),(1032,340)]:
        c=E[y,x]; print("   邻近连线 (%4d,%4d) lum=%5.1f"%(x,y,l[y,x]))
