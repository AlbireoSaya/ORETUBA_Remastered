# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
def rgb2lab(rgb):
    c=np.array(rgb)/255.0
    c=np.where(c<=0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
    M=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]])
    xyz=M@c; xyz/=np.array([0.95047,1.0,1.08883])
    f=np.where(xyz>0.008856, xyz**(1/3), 7.787*xyz+16/116)
    return np.array([116*f[1]-16, 500*(f[0]-f[1]), 200*(f[1]-f[2])])
def dE(a,b): return float(np.linalg.norm(rgb2lab(a)-rgb2lab(b)))
def dE76h(h1,h2):
    a=np.array([int(h1[i:i+2],16) for i in (0,2,4)],float)
    b=np.array([int(h2[i:i+2],16) for i in (0,2,4)],float)
    return dE(a,b)
def lum(rgb): return 0.299*rgb[0]+0.587*rgb[1]+0.114*rgb[2]
def contrast(rgb,bg=(14,16,21)):
    def rl(c):
        v=np.array(c)/255.0
        v=np.where(v<=0.03928, v/12.92, ((v+0.055)/1.055)**2.4)
        return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2]
    l1,l2=rl(rgb),rl(bg)
    if l1<l2: l1,l2=l2,l1
    return (l1+0.05)/(l2+0.05)

# --- node fills as rendered ---
def fill_of(img, x0,y0, pt=8, pb=55, kind='section'):
    # median over plate rows, interior cols, excluding ink (lum>0.6*plate)
    seg=img[y0+pt:y0+pb+1, x0+20:x0+276].reshape(-1,3)
    l=0.299*seg[:,0]+0.587*seg[:,1]+0.114*seg[:,2]
    m=l>np.percentile(l,60)
    return np.median(seg[m],axis=0)
E1=load(P+"E1_13_屏2_巡演图_终版数据.png")
E2=load(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png")
fills={}
fills['section']=fill_of(E1,516,190)        # 引言：假统合的崩溃
fills['select'] =fill_of(E1,516,285,pb=56)  # 晨间遭遇：小鸠
fills['frag']   =fill_of(E1,892,190)        # 没翅剧场
print("== 节点底图实测色（plate 中位色，已排除墨迹）==")
for k,v in fills.items():
    h='#%02X%02X%02X'%tuple(int(round(x)) for x in v)
    print("  %-8s %s  RGB=(%.1f,%.1f,%.1f)  lum=%.1f"%(k,h,v[0],v[1],v[2],lum(v)))
# select border: sample the outline: find darkest ring pixel per row at edge
seg=E1[285+8:285+57,516+8:516+288]
l=0.299*seg[...,0]+0.587*seg[...,1]+0.114*seg[...,2]
edge=[]
for r in range(seg.shape[0]):
    row=seg[r]; lr=l[r]
    i=int(np.argmin(lr))
    if lr[i]<110: edge.append(row[i])
if edge:
    b=np.median(np.array(edge),axis=0); print("  select 描边(最暗环)  #%02X%02X%02X  lum=%.1f"%(int(b[0]),int(b[1]),int(b[2]),lum(b)))
# --- link color as rendered ---
def link_color(img, x, y, r=4):
    win=img[y-r:y+r+1, x-r:x+r+1].reshape(-1,3)
    l=0.299*win[:,0]+0.587*win[:,1]+0.114*win[:,2]
    return win[int(np.argmin(l))]
for tag,img,x,y in [("E1 竖线 x=664 y=270",E1,664,270),("E2 竖线 x=664 y=270",E2,664,270)]:
    c=link_color(img,x,y); print("== 连线 %s -> #%02X%02X%02X  lum=%.1f"%(tag,int(c[0]),int(c[1]),int(c[2]),lum(c)))
# backdrop
print("== 背景（画布中缝 x=830 y=300）-> #%02X%02X%02X"%tuple(int(v) for v in E1[300,830]))
bg=np.median(E1[250:1050, 400:420].reshape(-1,3),axis=0)
print("   背景中位 #%02X%02X%02X lum=%.1f"%(int(bg[0]),int(bg[1]),int(bg[2]),lum(bg)))
print()
print("== 对比/ΔE ==")
LINK=np.array([38,96,128],float)   # #266080
SEL=fills['select']; SEC=fills['section']; FRG=fills['frag']
print("  ΔE76(#266080, 选择支底 #5FABD2标称) = %.1f"%dE76h('266080','5FABD2'))
print("  ΔE76(连线实测, 选择支底实测)        = %.1f"%dE(LINK,SEL))
print("  ΔE76(连线实测, 章节点底实测)        = %.1f"%dE(LINK,SEC))
print("  ΔE76(连线实测, 番外底实测)          = %.1f"%dE(LINK,FRG))
print("  ΔE76(选择支底, 章节点底)            = %.1f"%dE(SEL,SEC))
print("  ΔE76(选择支底, 番外底)              = %.1f"%dE(SEL,FRG))
print("  ΔE76(章节点底, 番外底)              = %.1f"%dE(SEC,FRG))
print("  ΔE76(旧连线色 #65B1D4, 选择支底)     = %.1f"%dE76h('65B1D4','5FABD2'))
print("  对比度 连线 vs 背景(14,16,21)        = %.2f:1"%contrast(LINK,(bg[0],bg[1],bg[2])))
print("  对比度 选择支描边 vs 选择支底         = %.2f:1"%contrast((30,60,90),SEL))
