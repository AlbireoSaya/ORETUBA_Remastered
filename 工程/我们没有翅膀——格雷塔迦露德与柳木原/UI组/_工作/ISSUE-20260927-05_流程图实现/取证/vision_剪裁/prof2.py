from PIL import Image
import numpy as np
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(n):
    a=np.array(Image.open(P+n).convert("RGBA")).astype(np.float64)
    c=a[...,:3]*(a[...,3:4]/255.0)
    return c, 0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2]
c1,l1=load("E1_13_屏2_巡演图_终版数据.png")
# select node (fc.node.0002) x=516 y=285 : profile at x0+22=538 and x0+274=790
print("=== E1 select node x=516 y=285 : col 538 / col 790 ===")
for y in range(288,356):
    print(y, y-285, round(l1[y,538],1), round(l1[y,790],1))
