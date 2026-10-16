# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
S=P+"vision_剪裁/"
e1=Image.open(P+"E1_13_屏2_巡演图_终版数据.png").convert("RGB")
e2=Image.open(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png").convert("RGB")
for tag,im in [("E2",e2),("E1",e1)]:
    c=im.crop((100,975,1250,1060)); c=c.resize((c.width*1,c.height*1)); c.save(S+"bot_%s.png"%tag)
    c2=im.crop((490,175,830,215)); c2=c2.resize((c2.width*3,c2.height*3),Image.NEAREST); c2.save(S+"top_%s.png"%tag)
    print("bot_"+tag+".png / top_"+tag+".png")
a=np.array(e2.convert("RGBA")).astype(float); a=a[...,:3]*(a[...,3:4]/255)
l=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
print("屏1 底缘 y=1005..1050 在 x=664 与 x=1040 的剖面：")
for y in range(1005,1051,1):
    print("   y=%d  664:%.1f  1040:%.1f  900:%.1f"%(y,l[y,664],l[y,1040],l[y,900]))
