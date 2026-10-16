# -*- coding: utf-8 -*-
"""7 张「无 YES/NO」板（20–24/42/45）+ 我方按钮的接触印相表（离线复算，非引擎渲染）。
每格 = 该板素材 + 该板的按钮底/文字（按 21_confirm.json 的数据坐标贴）+ 热区绿框。"""
import json, io, os
from PIL import Image, ImageDraw, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__))
UI=os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCR=os.path.join(UI,'layout','screens'); AST=os.path.join(UI,'krkr','assets','ui')
PAL=json.load(io.open(os.path.join(UI,'layout','palette.json'),encoding='utf-8'))['colors']
els=json.load(io.open(os.path.join(SCR,'21_confirm.json'),encoding='utf-8'))['elements']
PANEL_Y=270; BOARDS=['20','21','22','23','24','42','45']
def load(a): return Image.open(os.path.join(AST,os.path.basename(a))).convert('RGBA')
def font(s):
    try: return ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', s)
    except Exception: return ImageFont.load_default()
tiles=[]
for nn in BOARDS:
    W,H=1044,(540 if nn not in ('25','43','44','01','02','03','04','05','06','07','08','09','10','11','12') else 602)
    tile=Image.new('RGBA',(1044,540))
    # 板体（板内 y0..534 落在画布 276..804 ⇒ 画布 y=270 时板体把 y6..534 画到 276..804）
    p=[e for e in els if e['id']=='cf.panel_%s'%nn][0]
    tile.alpha_composite(load(p['asset']),(0,0))
    d=ImageDraw.Draw(tile)
    for e in els:
        if e.get('vis_when')!=nn or e['kind']=='image' or e['kind']!='text':
            if e.get('vis_when')==nn and e['kind']=='image':
                tile.alpha_composite(load(e['asset']).resize((e['w'],e['h']),Image.NEAREST),(e['x']-438,e['y']-270))
            continue
        f=font(e['font']['size']); tb=d.textbbox((0,0),e['sample'],font=f)
        d.text((e['x']-438+(e['w']-(tb[2]-tb[0]))/2-tb[0], e['y']-270+(e['h']-(tb[3]-tb[1]))/2-tb[1]),
               e['sample'],font=f,fill=(40,40,80,255))
    for e in els:
        if e['id'] in ('cf.hit_yes','cf.hit_no'):
            d.rectangle([e['x']-438,e['y']-270,e['x']-438+e['w']-1,e['y']-270+e['h']-1],outline=(0,220,0,255),width=3)
    d.text((8,8),'板 %s  （绿=共用热区；按钮底=我方件，板内 y=%d）'%(nn,[e for e in els if e['id']=='cf.yes_b%s'%nn][0]['y']-270),font=font(20),fill=(20,20,60,255))
    tiles.append(tile)
cols=3; rows=3
sheet=Image.new('RGB',(cols*1044+ (cols-1)*8, rows*540+(rows-1)*8),(230,230,235))
for i,t in enumerate(tiles):
    sheet.paste(t.convert('RGB'),((i%cols)*(1044+8),(i//cols)*(540+8)))
sheet=sheet.resize((sheet.width//2, sheet.height//2), Image.LANCZOS)
sheet.save(os.path.join(HERE,'preview_21_typeB_sheet.png'))
print('-> preview_21_typeB_sheet.png', sheet.size)
