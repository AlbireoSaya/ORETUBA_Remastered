from PIL import Image
import numpy as np
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(n):
    im=Image.open(P+n).convert("RGBA"); a=np.array(im).astype(np.float64)
    rgb=a[...,:3]*(a[...,3:4]/255.0)
    return rgb
e2=load("E2_自证/E2_真实数据验收图_shot_84_flowchart.png")
e1=load("E1_13_屏2_巡演图_终版数据.png")
pts={
 "bg_canvas_mid":(640,140),
 "bg_canvas_between_nodes":(830,300),
 "node_normal_fill":(600,225),
 "node_iceblue_fill":(600,300),
}
for k,(x,y) in pts.items():
    print("E2",k,(x,y),e2[y,x].round(1))
print()
for k,(x,y) in {"bg":(640,140),"node_normal":(600,225),"node_iceblue_single":(600,505),"node_frag_pink":(1030,225),"link_v":(664,270)}.items():
    print("E1",k,(x,y),e1[y,x].round(1))
