# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
S=P+"vision_剪裁/"
e1=Image.open(P+"E1_13_屏2_巡演图_终版数据.png").convert("RGB")
e2=Image.open(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png").convert("RGB")
a1=np.array(e1.convert("RGBA")).astype(float); a1=a1[...,:3]*(a1[...,3:4]/255)
a2=np.array(e2.convert("RGBA")).astype(float); a2=a2[...,:3]*(a2[...,3:4]/255)
def ink_at(a,x,y,r=5):
    w=a[y-r:y+r+1,x-r:x+r+1].reshape(-1,3)
    l=0.299*w[:,0]+0.587*w[:,1]+0.114*w[:,2]
    return l.min(), l.max()
print("== 折角/端点处可见性 ==")
for tag,a,x,y in [("屏1 link.0001 折角 (1040,223)",a2,1040,223),
                  ("屏1 link.0013 折角 (1040,792)",a2,1040,792),
                  ("屏1 link.0013 折角 (664,792)",a2,664,792),
                  ("屏2 竖线 x=1040 y=680",a1,1040,680)]:
    mn,mx=ink_at(a,x,y); print("   %-32s 窗口 lum min=%.1f max=%.1f  %s"%(tag,mn,mx,"有深色(线/节点墨迹)" if mn<100 else "无深色"))
# 可见 stub: 屏1 y=223 横段 x 812..892
print("== 屏1 link.0001 横段 y=223 沿线 ==")
for x in range(806,900,6):
    print("    x=%d lum=%.1f"%(x, 0.299*a2[223,x,0]+0.587*a2[223,x,1]+0.114*a2[223,x,2]))
print("== 屏1 link.0013 横段 y=792 沿线 ==")
for x in range(806,900,6):
    print("    x=%d lum=%.1f"%(x, 0.299*a2[792,x,0]+0.587*a2[792,x,1]+0.114*a2[792,x,2]))
jobs=[("L1_vert_arrow",e1,(630,235,700,310),4),
      ("L1_arrow_zoom",e1,(648,262,682,300),10),
      ("L1_elbow_1040",e1,(1010,330,1075,400),5),
      ("L2_elbow_stub",e2,(790,200,920,300),4),
      ("L2_link13",e2,(640,770,1180,830),2),
      ("L2_nodes3types",e2,(500,180,1200,470),1),
      ("L1_leftcol",e1,(40,180,420,780),1),
      ("L1_rightedge",e1,(1150,180,1340,1030),1),
      ("L1_3types",e1,(500,180,1200,470),1)]
for tag,im,box,z in jobs:
    cr=im.crop(box); cr=cr.resize((cr.width*z,cr.height*z),Image.NEAREST)
    cr.save(S+"c_%s.png"%tag); print("c_%s.png"%tag, box, "->", cr.size)
