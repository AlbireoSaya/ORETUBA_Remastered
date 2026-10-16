# -*- coding: utf-8 -*-
r"""ISSUE-20260926-02 · LaMa 对照路：用与程序化路完全相同的掩膜跑 lama-manga-dynamic.onnx（DML）
输出：去字件\1x\bgcN_page_lama.png + _证据\lama_compare.png（原图/程序化/LaMa 三路同区域对比）
"""
import os, sys
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\outpaint\pylibs_dml")
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\outpaint\pylibs")
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC  = os.path.join(BASE, "PSV系统UI参考")
EV   = os.path.join(BASE, "_工作", "ISSUE-20260926-02_PSVconfig去字", "_证据")
OUT1 = os.path.join(BASE, "PSV系统UI参考", "去字件", "1x")

sess = ort.InferenceSession(r"E:\ZCode Workspace\Galgame\工具\outpaint\models\lama-manga-dynamic.onnx",
                            providers=["DmlExecutionProvider"])

def lama(img_rgb_f32, mask):
    """img (H,W,3) 0..255 float, mask (H,W) {0,1} → (H,W,3) 0..255"""
    h, w = mask.shape
    x = np.transpose(img_rgb_f32 / 255.0, (2, 0, 1))[None].astype(np.float32)
    m = mask[None, None].astype(np.float32)
    out = sess.run(["inpainted"], {"image": x, "mask": m})[0][0]
    if out.max() > 1.6: out = out / 255.0          # 兼容 0..255 导出
    out = np.clip(np.transpose(out, (1, 2, 0)), 0, 1) * 255.0
    return out

regs = [(500,130,780,215),(415,315,880,350),(120,135,330,170),(55,80,230,130)]
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)
cells = []
for name, tag in [("otv_bg_config_01.png","bgc01"), ("otv_bg_config_02.png","bgc02")]:
    page = np.asarray(Image.open(os.path.join(SRC, name)).convert("RGB")).astype(np.float32)[:544]
    mask = (np.asarray(Image.open(os.path.join(EV, tag + "_mask.png")).convert("L")) > 127)
    out = lama(page, mask)
    # 只替换掩膜像素（LaMa 对非掩膜区可能有轻微数值漂移）
    blend = page.copy(); blend[mask] = out[mask]
    Image.fromarray(blend.astype(np.uint8)).save(os.path.join(OUT1, tag + "_page_lama.png"))
    print(tag, "lama done, hole px:", int(mask.sum()))
    cells.append((tag, page, blend, mask))

# 对比表：c1 的四个区域 × (原图/程序化/LaMa)
tag, page, blend, mask = cells[0]
prog = np.asarray(Image.open(os.path.join(OUT1, "bgc01_page.png")).convert("RGB"))
Z = 2
rows = []
for (x0,y0,x1,y1) in regs:
    a = Image.fromarray(page[y0:y1, x0:x1].astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z), Image.NEAREST)
    b = Image.fromarray(prog[y0:y1, x0:x1]).resize(a.size, Image.LANCZOS)
    c = Image.fromarray(blend[y0:y1, x0:x1].astype(np.uint8)).resize(a.size, Image.LANCZOS)
    rows.append((a,b,c))
Wc = max(r[0].width for r in rows)
sheet = Image.new("RGB", (Wc*3+40, sum(r[0].height+30 for r in rows)+10), (24,26,32))
dr = ImageDraw.Draw(sheet)
y = 5
for a,b,c in rows:
    for i,im in enumerate([a,b,c]): sheet.paste(im, (8+i*(Wc+12), y))
    dr.text((8, y+a.height+4), "原图            程序化(Laplace)     LaMa", fill=(220,230,240), font=font)
    y += a.height+30
sheet.save(os.path.join(EV, "lama_compare.png"))
print("compare sheet saved")
