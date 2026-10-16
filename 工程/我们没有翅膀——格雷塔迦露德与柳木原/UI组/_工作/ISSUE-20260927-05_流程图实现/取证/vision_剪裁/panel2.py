# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
E1=load(P+"E1_13_屏2_巡演图_终版数据.png")
l=0.299*E1[...,0]+0.587*E1[...,1]+0.114*E1[...,2]
print("列剖面 y=300..1000，x=1180..1400 (亮像素>50 占比)")
for x in range(1180,1400,2):
    c=l[300:1000,x]; print("  x=%4d  %.2f  (median %.0f, max %.0f)"%(x,(c>50).mean(),np.median(c),c.max()))
print()
print("流程图面板右边框：列剖面 x=1280..1305, y=200..1050 (亮>40)")
for x in range(1280,1306):
    c=l[200:1050,x]; print("  x=%4d %.2f median %.0f"%(x,(c>40).mean(),np.median(c)))
