# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
import sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
S=P+"vision_剪裁/"
items=[("E1_13_屏2_巡演图_终版数据.png",892,665,"E1_2line"),
       ("E2_自证/E2_真实数据验收图_shot_84_flowchart.png",516,760,"E2_2line")]
for f,x0,y0,tag in items:
    im=Image.open(P+f).convert("RGB")
    cr=im.crop((x0-4,y0-6,x0+300,y0+71))
    z=8; cr=cr.resize((cr.width*z,cr.height*z),Image.NEAREST)
    d=ImageDraw.Draw(cr)
    def hline(off,col,lab):
        y=(off+6)*z
        d.line([(0,y),(cr.width,y)],fill=col,width=2)
        d.text((4,y+2),lab,fill=col)
    hline(8,(255,0,0),"plate top 8")
    hline(13,(255,140,0),"criterion top 13 (8+5)")
    hline(50,(255,140,0),"criterion bot 50 (55-5)")
    hline(55,(255,0,0),"plate bot 55")
    cr.save(S+"ann_%s.png"%tag); print("ann_%s.png"%tag, cr.size)
