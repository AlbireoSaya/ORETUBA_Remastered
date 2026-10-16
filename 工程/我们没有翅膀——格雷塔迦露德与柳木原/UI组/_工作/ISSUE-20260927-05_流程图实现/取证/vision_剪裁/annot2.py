# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
import sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
S=P+"vision_剪裁/"
def strip(f,x0,y0,off0,off1,tag,zoom=8):
    im=Image.open(P+f).convert("RGB")
    cr=im.crop((x0+60,y0+off0,x0+240,y0+off1+1))
    cr=cr.resize((cr.width*zoom,cr.height*zoom),Image.NEAREST)
    d=ImageDraw.Draw(cr)
    for off in range(off0,off1+1):
        y=(off-off0)*zoom
        col=(255,0,0) if off in (8,55) else ((255,140,0) if off in (13,50) else ((80,255,80) if off in (11,12,29,30,31,49,48) else None))
        if col: d.line([(0,y),(cr.width,y)],fill=col,width=1)
    d.text((3,3),"rows %d..%d | red=plate(8/55) orange=crit(13/50) green=ink(11,12,29,31,49)"%(off0,off1),fill=(255,255,0))
    cr.save(S+"st_%s.png"%tag); print("st_%s.png"%tag, cr.size)
strip("E1_13_屏2_巡演图_终版数据.png",892,665,5,16,"E1_top")
strip("E1_13_屏2_巡演图_终版数据.png",892,665,45,58,"E1_bot")
strip("E2_自证/E2_真实数据验收图_shot_84_flowchart.png",516,760,5,16,"E2_top")
strip("E2_自证/E2_真实数据验收图_shot_84_flowchart.png",516,760,45,58,"E2_bot")
