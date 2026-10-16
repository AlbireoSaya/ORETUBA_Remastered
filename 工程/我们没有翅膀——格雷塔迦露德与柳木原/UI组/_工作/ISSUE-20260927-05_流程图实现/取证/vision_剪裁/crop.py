from PIL import Image, ImageDraw
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
S="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/vision_剪裁/"
e1=Image.open(P+"E1_13_屏2_巡演图_终版数据.png").convert("RGB")
e2=Image.open(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png").convert("RGB")
jobs=[("E1_section(r0)",e1,(516,190,812,255)),
      ("E1_select(r1)", e1,(516,285,812,350)),
      ("E1_frag(r0)",   e1,(892,190,1188,255)),
      ("E1_frag_2line", e1,(892,665,1188,730)),
      ("E1_section_2l", e1,(892,665,1188,730)),
      ("E2_section_n1", e2,(516,190,812,255)),
      ("E2_2line",      e2,(516,760,812,825)),
      ]
for tag,im,box in jobs:
    cr=im.crop(box)
    z=cr.resize((cr.width*3,cr.height*3),Image.NEAREST)
    # add ruler lines every 5 px of original
    d=ImageDraw.Draw(z)
    for k in range(0,cr.height+1,5):
        col=(255,0,0) if k%10==0 else (0,255,0)
        d.line([(0,k*3),(6,k*3)],fill=col)
    z.save(S+"zoom_%s.png"%tag)
    print("zoom_%s.png"%tag, cr.size)
# masonry: all nodes stacked with 5px grid
