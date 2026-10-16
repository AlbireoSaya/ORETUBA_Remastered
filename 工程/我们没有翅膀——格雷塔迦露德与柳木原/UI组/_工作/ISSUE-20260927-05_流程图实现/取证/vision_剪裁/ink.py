from PIL import Image
import numpy as np
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(n):
    a=np.array(Image.open(P+n).convert("RGBA")).astype(np.float64)
    c=a[...,:3]*(a[...,3:4]/255.0)
    return c, 0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2]
c1,l1=load("E1_13_屏2_巡演图_终版数据.png")
x0,y0=892,665   # frag 2-line
print("=== frag 2-line node x=892 y=665 : rows, col-profile stats ===")
print("off | bodywidth(lum>0.5*pl) | darkcount(lum<70) | minlum | maxlum")
for off in range(-3,69):
    y=y0+off
    seg=l1[y, x0+20:x0+276]
    full=l1[y, x0+6:x0+290]
    pl=np.median(full[full>100]) if (full>100).any() else 0
    bw=int((seg>60).sum())
    dk=int((seg<70).sum())
    print("%4d | %4d | %4d | %6.1f | %6.1f"%(off,bw,dk,seg.min(),seg.max()))
