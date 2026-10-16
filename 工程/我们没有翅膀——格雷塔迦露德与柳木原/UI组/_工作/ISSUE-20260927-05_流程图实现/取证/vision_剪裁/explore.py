from PIL import Image
import numpy as np
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
for name in ["E2_自证/E2_真实数据验收图_shot_84_flowchart.png","E1_13_屏2_巡演图_终版数据.png"]:
    im=Image.open(P+name).convert("RGBA")
    a=np.array(im)
    print("==",name, a.shape)
    alpha=a[...,3]
    print("  alpha min/max/uniq:",alpha.min(),alpha.max(),len(np.unique(alpha)))
    rgb=a[...,:3]
    lum=(0.299*rgb[...,0]+0.587*rgb[...,1]+0.114*rgb[...,2])
    print("  lum min/max:",lum.min(),lum.max())
    # histogram of unique colors count
    # sample specific pixel: canvas backdrop around y=100 x=... ; node fill
    # find bright pixels
    br=lum>170
    print("  bright px:",br.sum())
