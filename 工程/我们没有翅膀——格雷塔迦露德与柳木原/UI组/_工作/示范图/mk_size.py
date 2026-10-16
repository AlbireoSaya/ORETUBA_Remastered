# -*- coding: utf-8 -*-
"""批次 C/D/B 各件「真实像素尺寸」对照（1:1）。"""
from PIL import Image, ImageDraw, ImageFont
import os
OUT = os.path.dirname(os.path.abspath(__file__))
def font(sz, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/simhei.ttf", sz)
NAVY=(8,24,40); WHITE=(240,246,255); DIM=(150,165,185); GOLD=(216,168,60); PUR=(150,120,200); GRN=(120,200,140); BLU=(120,170,230)
im = Image.new("RGB",(1280,780),NAVY); d=ImageDraw.Draw(im)
d.text((24,14),"批次 C / D / B 各件「真实像素尺寸」对照",font=font(20),fill=WHITE)
d.text((24,42),"下面每个框都是按 1:1 真实像素画出来的，不是缩放示意——你能直接看出它在屏幕上占多大",font=font(14),fill=DIM)

# ── 上：章节主图（最大的一件）──
d.rectangle([60,90,60+504,90+284],fill=(30,42,60),outline=GOLD,width=3)
d.text((600,110),"C · 章节主图",font=font(18,True),fill=GOLD)
d.text((600,140),"504 × 284 px  ·  每幕一张，共 11 张  ·  JPG",font=font(15),fill=WHITE)
d.text((600,168),"放在章节选择屏右侧的「当前幕详情」面板里，是那一屏最大的一块视觉。",font=font(14),fill=DIM)
d.text((600,192),"题材按每幕的剧情舞台走（现实侧都市 / 幻想侧王国 / 双世界交汇）。",font=font(14),fill=DIM)
d.text((600,216),"画面里不能有文字、不能有人物。",font=font(14),fill=(230,180,180))
d.text((600,252),"※ 列表每行左边的小缩略图（64×36）由这张主图缩小派生，",font=font(13),fill=DIM)
d.text((600,272),"   所以你只需要出 11 张主图，不用另出缩略图。",font=font(13),fill=DIM)

# ── 下：小件（底对齐，便于比大小）──
d.line([(60,600),(1220,600)],fill=(70,90,120),width=1)
BASE=600
items=[(64,36,GOLD,"C 行内缩略图","64×36","由主图缩小派生"),
       (42,56,PUR,"D 碎片·显示","42×56","UI 内实际显示"),
       (126,168,PUR,"D 碎片·生成","126×168","按此生成，我再缩小"),
       (40,40,GRN,"D 组图标·显示","40×40","UI 内实际显示"),
       (96,96,GRN,"D 组图标·生成","96×96","按此生成，我再缩小"),
       (24,24,BLU,"B 图标·显示","24×24","系统条等处")]
x=60
for w,h,col,name,dim,note in items:
    top=BASE-h
    d.rectangle([x,top,x+w,top+h],fill=(30,42,60),outline=col,width=2)
    d.text((x, BASE+10), name, font=font(13,True), fill=col)
    d.text((x, BASE+30), dim,  font=font(14), fill=WHITE)
    d.text((x, BASE+50), note, font=font(11), fill=DIM)
    x += max(w,150) + 34
d.text((60,720),"说明：碎片与图标的「生成尺寸」比「显示尺寸」大，是为了让生图模型画出可辨认的细节；我再按 LANCZOS 缩小入库（缩小合规，放大禁止）。",font=font(13),fill=DIM)
d.text((60,744),"碎片三态（未解锁 / 可进入 / 已收集）必须是同一个形状，只是填色与描边不同——见「示范2_Fragment屏.png」底部图例。",font=font(13),fill=DIM)
im.save(os.path.join(OUT,"示范3_真实尺寸对照.png")); print("saved 示范3")
