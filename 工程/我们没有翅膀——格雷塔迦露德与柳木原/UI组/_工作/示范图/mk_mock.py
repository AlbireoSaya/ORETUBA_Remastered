# -*- coding: utf-8 -*-
"""批次 C / D 的版式示意（占位 mockup，非生图产物）。只读布局数值，只写本目录。"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))
F = "C:/Windows/Fonts/simhei.ttf"
def font(sz, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc" if bold else F, sz)

NAVY=(8,24,40); PANEL=(16,32,52); EDGE=(120,160,220); WHITE=(240,246,255)
DIM=(150,165,185); GOLD=(216,168,60); BLUE=(122,176,232); GREY=(74,74,86)

def shard(d, box, fill=None, outline=GREY, w=2):
    x,y,bw,bh = box
    pts=[(x+bw*0.24,y+bh*0.03),(x+bw*0.72,y+bh*0.11),(x+bw*0.92,y+bh*0.46),
         (x+bw*0.66,y+bh*0.97),(x+bw*0.26,y+bh*0.83),(x+bw*0.06,y+bh*0.44)]
    d.polygon(pts, fill=fill, outline=outline)
    if w>1: d.line(pts+[pts[0]], fill=outline, width=w, joint="curve")

def label(d,xy,txt,sz=15,color=WHITE,anchor="la"):
    d.text(xy,txt,font=font(sz),fill=color,anchor=anchor)

def dashbox(d,box,color=DIM,w=1):
    x,y,bw,bh=box
    step=8
    for i in range(x,x+bw,step*2):
        d.line([(i,y),(min(i+step,x+bw),y)],fill=color,width=w)
        d.line([(i,y+bh),(min(i+step,x+bw),y+bh)],fill=color,width=w)
    for j in range(y,y+bh,step*2):
        d.line([(x,j),(x,min(j+step,y+bh))],fill=color,width=w)
        d.line([(x+bw,j),(x+bw,min(j+step,y+bh))],fill=color,width=w)

# ══════════════ 图 1 · 章节选择屏 ══════════════
im = Image.new("RGB",(1280,720),NAVY); d=ImageDraw.Draw(im)
label(d,(24,14),"章节选择屏 · 版式示意（占位图，非生图产物）",20,WHITE)
label(d,(24,42),"蓝框 = 已有元素（原版九宫格边框 / 引擎文字）    黄框 = 批次 C 要生成的图",15,GOLD)

# 左面板
d.rounded_rectangle([96,132,96+560,132+512],8,fill=PANEL,outline=EDGE,width=2)
label(d,(96,108),"左：11 幕列表（面板已有）",14,EDGE)
rows=["前奏诗·框架剧与四短篇","前奏诗·系统脚本","本篇·序文","本篇·s01 鹰志线","本篇·s02 鹫介线",
      "本篇·s03 隼人线","亚衣线·s03c（R 版 55 场景版）","PSV 美咲线（同期分支）","大路线 s04（最终章）",
      "After Story·主线","涅布＊プラス 明日香篇"]
for i,t in enumerate(rows):
    y=148+i*44
    sel = (i==3)
    if sel: d.rounded_rectangle([112,y,112+528,y+38],4,fill=(58,90,154))
    # 行内缩略图 64x36（由章节主图缩小派生）
    d.rectangle([118,y+1,118+64,y+37],fill=(70,80,100),outline=GOLD,width=2)
    label(d,(150,y+11),"缩略",12,(200,200,210),anchor="mm")
    label(d,(194,y+19),t,16,WHITE if sel else DIM,anchor="lm")
label(d,(96,652),"↑ 每行左侧黄框 = 行内缩略图 64×36，由右侧主图缩小派生，不用你另出",13,GOLD)

# 右面板 + 主图
d.rounded_rectangle([680,132,680+504,132+512],8,fill=PANEL,outline=EDGE,width=2)
label(d,(680,108),"右：当前幕详情（面板已有）",14,EDGE)
d.rectangle([696,164,696+504,164+284],fill=(48,58,78),outline=GOLD,width=3)
d.line([(696,164),(1200,448)],fill=(90,100,125),width=2)
d.line([(1200,164),(696,448)],fill=(90,100,125),width=2)
label(d,(948,300),"批次 C · 章节主图",22,GOLD,anchor="mm")
label(d,(948,330),"504 × 284 px",17,WHITE,anchor="mm")
label(d,(948,356),"每幕一张，共 11 张 · JPG",14,DIM,anchor="mm")
label(d,(696,466),"幕名 / 场景数 / 行数 / 剧情梗概（引擎绘字，非图片）",14,DIM)
label(d,(696,492),"11 幕幕名取自 资源组\剧本\主线编排方案.md，不得改写",13,DIM)
d.rounded_rectangle([680,660,924,704],6,fill=PANEL,outline=EDGE,width=1); label(d,(802,682),"进入本幕",15,WHITE,anchor="mm")
d.rounded_rectangle([940,660,1184,704],6,fill=PANEL,outline=EDGE,width=1); label(d,(1062,682),"返回",15,WHITE,anchor="mm")
im.save(os.path.join(OUT,"示范1_章节选择屏.png"))

# ══════════════ 图 2 · Fragment 屏 ══════════════
im2 = Image.new("RGB",(1280,720),NAVY); d2=ImageDraw.Draw(im2)
label(d2,(24,14),"番外（Fragment）选择屏 · 版式示意（占位图，非生图产物）",20,WHITE)
label(d2,(24,42),"绿框 = 批次 D 组图标（96×96→显示 40×40）    紫框 = 批次 D 碎片三态（126×168→显示 42×56）",15,(150,220,160))

groups=[("阿雷克桑德平安夜",7),("苍女Ｘ日",7),("各线 after",4),("群像（新年行军/格兰玛尼耶）",10),("おれつば剧场",5),("おまけ",20)]
gy=100
for gi,(gname,cnt) in enumerate(groups):
    y=gy+gi*72
    d2.rounded_rectangle([56,y,56+1168,y+64],6,fill=PANEL,outline=(60,80,110),width=1)
    d2.rectangle([72,y+12,72+40,y+52],fill=(40,54,74),outline=(120,200,140),width=2)
    label(d2,(92,y+32),"组",14,(160,230,180),anchor="mm")
    label(d2,(128,y+32),"%d. %s"%(gi+1,gname),16,WHITE,anchor="lm")
    for c in range(cnt):
        x=372+c*40
        if c<max(1,int(cnt*0.15)):      # 已收集
            shard(d2,(x,y+4,42,56),fill=GOLD,outline=(255,233,168),w=2)
        elif c<max(2,int(cnt*0.4)):     # 可进入
            shard(d2,(x,y+4,42,56),fill=None,outline=BLUE,w=3)
        else:                            # 未解锁
            shard(d2,(x,y+4,42,56),fill=(34,42,58),outline=GREY,w=2)
label(d2,(372,gy-18),"碎片格阵：42×56，gap 3",13,(190,180,230))
d2.rectangle([356,gy+6,356+900,gy+64],outline=(150,120,200),width=1)

# 三态图例
lg=[("D7 未解锁：暗色剪影",(34,42,58),GREY,2),("D8 可进入：亮色描边",None,BLUE,3),("D9 已收集：暖色实心",GOLD,(255,233,168),2)]
for i,(t,fill,ol,w) in enumerate(lg):
    x=80+i*250; y=600
    shard(d2,(x,y,42,56),fill=fill,outline=ol,w=w)
    label(d2,(x+56,y+28),t,15,WHITE,anchor="lm")
label(d2,(80,672),"三态必须是同一个形状（这里示意为「羽翼碎片」），否则收集感不成立",14,(190,180,230))
d2.rounded_rectangle([1004,640,1232,684],6,fill=PANEL,outline=EDGE,width=1); label(d2,(1118,662),"返回",15,WHITE,anchor="mm")
im2.save(os.path.join(OUT,"示范2_Fragment屏.png"))

# ══════════════ 图 3 · 真实尺寸对照 ══════════════
im3 = Image.new("RGB",(1280,760),NAVY); d3=ImageDraw.Draw(im3)
label(d3,(24,14),"批次 C / D 各件「真实像素尺寸」对照（1:1 画出来，不是缩放示意）",20,WHITE)
label(d3,(24,42),"这样你能直观知道每张图在屏幕上占多大",14,DIM)
items=[("C 章节主图",504,284,GOLD,"每幕一张 ×11 · JPG"),
       ("C 行内缩略图",64,36,GOLD,"由主图缩小派生，不用另出"),
       ("D 碎片·显示尺寸",42,56,(150,120,200),"UI 内实际显示大小"),
       ("D 碎片·生成尺寸",126,168,(150,120,200),"按此比例生成，我再缩小"),
       ("D 组图标·显示",40,40,(120,200,140),"UI 内实际显示大小"),
       ("D 组图标·生成",96,96,(120,200,140),"按此生成，我再缩小"),
       ("B 图标·显示",24,24,(120,170,230),"系统条 8 键等处的图标大小")]
x=40; y=90
for name,w,h,col,note in items:
    d3.rectangle([x,y,x+w,y+h],fill=(30,42,60),outline=col,width=3)
    label(d3,(x,y+h+8),"%s"%name,14,col)
    label(d3,(x,y+h+28),"%d×%d"% (w,h),15,WHITE)
    label(d3,(x,y+h+48),note,12,DIM)
    x += w + 46
    if x > 1150: x=40; y+=250
label(d3,(40,700),"说明：碎片/图标的「生成尺寸」比「显示尺寸」大，是为了让生图模型画出可辨认的细节，我再按 LANCZOS 缩小入库（缩小合规，放大禁止）。",13,DIM)
im3.save(os.path.join(OUT,"示范3_真实尺寸对照.png"))
print("saved 3 mockups ->", OUT)
