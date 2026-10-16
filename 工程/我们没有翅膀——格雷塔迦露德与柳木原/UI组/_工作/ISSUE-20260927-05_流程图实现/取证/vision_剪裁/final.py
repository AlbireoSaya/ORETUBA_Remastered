# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
P="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
def lum(r): return 0.299*r[...,0]+0.587*r[...,1]+0.114*r[...,2]
def rgb2lab(rgb):
    c=np.array(rgb,float)/255.0
    c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
    M=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]])
    xyz=M@c/np.array([0.95047,1.0,1.08883])
    f=np.where(xyz>0.008856,xyz**(1/3),7.787*xyz+16/116)
    return np.array([116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])])
def dE(a,b): return float(np.linalg.norm(rgb2lab(a)-rgb2lab(b)))
LINK=np.array([38,96,128.]); SEL=np.array([95.6,171.3,211.2]); BORD=np.array([31,53,67.])
BG=np.array([14.,16.,21.])
print("ΔE76 连线 vs 选择支描边 #1F3543 = %.1f"%dE(LINK,BORD))
print("ΔE76 连线 vs 画布底 #0E1015     = %.1f"%dE(LINK,BG))
print("ΔE76 画布底 vs 选择支底色        = %.1f"%dE(BG,SEL))
print("ΔE76 画布底 vs 章节点底色        = %.1f"%dE(BG,np.array([195.2,213.2,244.])))
print("ΔE76 连线 vs 章节点墨迹(深灰)     = %.1f"%dE(LINK,np.array([33.,33.,33.])))
# ---- 两行节点 逐行分组 ----
E1=load(P+"E1_13_屏2_巡演图_终版数据.png"); E2=load(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png")
for tag,img,x0,y0 in [("屏2/E1 恐怖！怪人黑内裤大猩猩的逆袭",E1,892,665),("屏1/E2 我果然也是个少女呢。呐（略）",E2,516,760)]:
    l=lum(img); Y=slice(y0,y0+65)
    inner=l[Y, x0+30:x0+266]
    med=np.median(inner,axis=1)
    ink=np.array([(med[i]>70 and (inner[i]<0.55*med[i]).any()) for i in range(65)])
    rows=np.nonzero(ink)[0]
    grp=[]
    for r in rows:
        if grp and r-grp[-1][-1]<=1: grp[-1].append(r)
        else: grp.append([r])
    print("== %s  (plate 8..55)"%tag)
    for i,g in enumerate(grp):
        sub=l[Y, x0+10:x0+286][g[0]:g[-1]+1]
        dk=(sub<0.5*193).any(axis=0); cols=np.nonzero(dk)[0]
        print("   行%d ink rows %d..%d (高 %d)  横向 %d..%d 宽 %d"%(
            i+1,g[0],g[-1],g[-1]-g[0]+1,cols.min()+x0+10,cols.max()+x0+10,cols.max()-cols.min()+1))
    print("   上留=%d 下留=%d  行距=%d"%(grp[0][0]-8, 55-grp[-1][-1], grp[1][0]-grp[0][0] if len(grp)>1 else 0))
# ---- 单行节点 上/下留 统计 ----
print("== 单行节点 上留/下留 统计（plate 8..55/56）==")
def scan(img,nds):
    l=lum(img); out=[]
    for x0,y0,pb,sm in nds:
        inner=l[y0:y0+65, x0+30:x0+266]; med=np.median(inner,axis=1)
        ink=[i for i in range(65) if med[i]>70 and (inner[i]<0.55*med[i]).any()]
        out.append((sm,ink[0]-8,pb-ink[-1],ink[0],ink[-1]))
    return out
for tag,img,nds in [
  ("屏1/E2",E2,[(516,190,56,'五里雾中'),(516,285,56,'在世界底层仓皇逃窜'),(516,380,55,'鹰振翅高飞'),(516,475,55,'现实的联系'),(516,570,55,'请·渡来化·我'),(516,665,55,'做得太过火的明日香大人'),(516,855,55,'终章～羽田君和渡来同学～'),(516,950,55,'解缆～对抗：羽田鹰志～'),(892,285,55,'互相爱抚伤口的折翼天使们'),(892,380,55,'s01_14h'),(892,475,55,'近视眼们在恋爱'),(892,570,55,'终章～鹰志君和小京～')]),
  ("屏2/E1",E1,[(516,190,55,'引言：假统合的崩溃'),(516,285,56,'晨间遭遇：小鸠'),(516,380,55,'间奏：从自宅到学校'),(892,190,55,'没翅剧场～女人们的决战～'),(892,285,55,'如今我们的胸部再度开始'),(892,380,55,'回归招牌女孩')])]:
    print(" ",tag)
    for sm,a,b,t,bt in scan(img,nds):
        print("    %-24s 上留 %2d  下留 %2d   (ink %d..%d)"%(sm,a,b,t,bt))
# ---- 素材边缘锯齿（九宫格横向非整数放大）----
print("== 节点底板左右边缘规整度（section 前 3 节点，逐行左缘 x 位置）==")
l=lum(E1)
for y0 in (190,380,760):
    xs=[]
    for off in range(10,54):
        row=l[y0+off, 505:535]
        idx=np.nonzero(row>150)[0]
        xs.append(idx[0]+505 if len(idx) else -1)
    print("    y0=%d 左缘 x: min %d max %d 唯一值 %s"%(y0,min(xs),max(xs),sorted(set(xs))))
