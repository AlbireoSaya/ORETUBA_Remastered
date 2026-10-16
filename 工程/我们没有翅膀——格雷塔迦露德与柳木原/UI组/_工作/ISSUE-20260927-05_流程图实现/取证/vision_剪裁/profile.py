from PIL import Image
import numpy as np
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
e1=np.array(Image.open(P+"E1_13_屏2_巡演图_终版数据.png").convert("RGBA")).astype(np.float64)
e1c=e1[...,:3]*(e1[...,3:4]/255.0)
lum1=0.299*e1c[...,0]+0.587*e1c[...,1]+0.114*e1c[...,2]
# screen2 node1: x=516..812, y=190..255 (single line "引言：假统合的崩溃")
# vertical profile at x=530 (inside node, left of text) region
print("=== E1 node fc.node.0001 (y=190,h=65) column profiles ===")
print("row | lum@x=560 | lum@x=805 | lum@x=518 | lum@x=811")
for y in range(184,262):
    print(y, y-190, round(lum1[y,560],1), round(lum1[y,805],1), round(lum1[y,518],1), round(lum1[y,811],1))
