# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np, json, sys
sys.stdout.reconfigure(encoding='utf-8')
UI="E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
P=UI+"_工作/ISSUE-20260927-05_流程图实现/取证/"
def load(p):
    a=np.array(Image.open(p).convert("RGBA")).astype(np.float64)
    return a[...,:3]*(a[...,3:4]/255.0)
def lum(r): return 0.299*r[...,0]+0.587*r[...,1]+0.114*r[...,2]
L=lum(load(P+"E2_自证/E2_真实数据验收图_shot_84_flowchart.png"))
d=json.load(open(UI+"layout/screens/32_flowchart.json",encoding='utf-8'))
print("== 左栏组名标签 墨迹范围（盒 x60..393 w333；plate 由 label_off 素材行范围决定）==")
for e in d['elements']:
    if e['id'].startswith('fc.label') and e['kind']=='text':
        x0,y0,w,h=e['x'],e['y'],e['w'],e['h']
        sub=L[y0:y0+h, x0:x0+w]
        med=np.median(sub,axis=1)
        ink=[i for i in range(h) if med[i]>70 and (sub[i]<0.55*med[i]).any()]
        if not ink: print("  %s 无墨迹"%e['id']); continue
        rr=sub[ink[0]:ink[-1]+1]
        dark=np.zeros(w,bool)
        for j in range(rr.shape[0]):
            m=np.median(rr[j])
            if m>70: dark |= (rr[j]<0.55*m)
        cols=np.nonzero(dark)[0]
        lo,hi=int(cols.min()),int(cols.max())
        print("  %-18s 墨迹 x %d..%d (宽 %d) | 盒内左余 %d 右余 %d | 行 %d..%d | %s"%(
            e['id'],x0+lo,x0+hi,hi-lo+1,lo,w-1-hi,ink[0],ink[-1],e.get('sample','')[:26]))
print()
print("== 入口标记 视觉状态（x=183..269 y 如下）==")
for e in d['elements']:
    if e['id'].startswith('fc.entry'):
        x0,y0,w,h=e['x'],e['y'],e['w'],e['h']
        sub=L[y0:y0+h, x0:x0+w]
        print("  %-14s y=%d  平均 lum=%.1f  min=%.1f max=%.1f  暗像素(<80)占比 %.2f"%(
            e['id'],y0,sub.mean(),sub.min(),sub.max(),(sub<80).mean()))
