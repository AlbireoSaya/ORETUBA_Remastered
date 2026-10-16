# -*- coding: utf-8 -*-
r"""ISSUE-20260926-04 · 批量验收+超分+审阅表
1) 逐件 100% 前后对照（原图超分2× vs AI中文2×）拼审阅表（每组 ≤4 对）
2) upscayl 2× 全部 1× 成品（dm 家族只超分代表件，2× 复制到同族文件名）
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC  = os.path.join(BASE_DIR, "PSV系统UI参考")
AI1  = os.path.join(SRC, "AI中文化", "1x")
AI2  = os.path.join(SRC, "AI中文化", "2x")
S2   = os.path.join(SRC, "超分2x")
RV   = os.path.join(SRC, "AI中文化", "_审阅")
os.makedirs(AI2, exist_ok=True); os.makedirs(RV, exist_ok=True)
UPSCAYL = r"E:\ZCode Workspace\Galgame\工具\upscayl\app\resources\bin\upscayl-bin.exe"
MODELS  = r"E:\ZCode Workspace\Galgame\工具\upscayl\app\resources\models"
TMP     = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\临时\ups_in4"
font  = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)
fonts = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)

# 每件的 100% 抽查区（1× 坐标；None=整件就是小图）
SPOTS = {
 "otv_dm00.png": [(0,0,320,120)],
 "otv_saving.png": [(0,0,320,120)],
 "otv_save_bg.png": [(430,470,960,544),(0,0,560,120)],
 "otv_load_bg.png": [(430,470,960,544)],
 "otv_quick_load_bg.png": [(430,470,960,544)],
 "otv_gm_bg1.png": [(0,540,960,659)],
 "otv_title_bg.png": [(0,540,960,965)],
 "otv_ec1_bg.png": [(0,0,1013,658)],
 "otv_ec2_bg.png": [(0,0,1013,658)],
 "otv_ec3_bg.png": [(0,0,1013,658)],
 "otv_ec4_bg.png": [(0,0,1013,658)],
 "otv_ec5_1_bg.png": [(180,40,1013,360)],
 "otv_ec5_2_bg.png": [(180,40,1013,360)],
}

def upscayl_all():
    os.makedirs(TMP, exist_ok=True)
    import shutil
    for f in os.listdir(AI1):
        shutil.copy2(os.path.join(AI1, f), os.path.join(TMP, f))
    n = len(os.listdir(TMP))
    r = subprocess.run([UPSCAYL, "-i", TMP, "-o", AI2, "-n", "upscayl-lite-4x", "-s", "2",
                        "-m", MODELS, "-f", "png"], capture_output=True, text=True, timeout=1800)
    ok = r.stdout.count("Successfully")
    print("upscayl: %d/%d" % (ok, n))
    # QA
    bad = []
    for f in os.listdir(AI2):
        s = Image.open(os.path.join(AI1, f)); o = Image.open(os.path.join(AI2, f))
        if o.size != (s.width*2, s.height*2): bad.append((f, o.size))
    print("QA:", bad if bad else "all 2x ok")

def sheets():
    import re as _re
    files = sorted(f.replace("_cn.png", ".png") for f in os.listdir(AI1) if f.endswith("_cn.png"))
    per = 6
    groups = [files[i:i+per] for i in range(0, len(files), per)]
    for gi, grp in enumerate(groups):
        cells = []
        for name in grp:
            tag = name.replace("otv_", "").replace(".png", "")
            orig = name.replace("bgc01", "otv_bg_config_01").replace("bgc02", "otv_bg_config_02")
            o2p = os.path.join(S2, orig)
            o2 = Image.open(o2p).convert("RGBA") if os.path.exists(o2p) else None
            c2 = Image.open(os.path.join(AI2, name.replace(".png", "_cn.png"))).convert("RGBA")
            spots = SPOTS.get(name)
            if name.startswith("otv_dlg_bg_"):
                spots = [(0,0,522,301) if "dlg_bg_2" in name or name in ("otv_dlg_bg_42.png","otv_dlg_bg_43.png","otv_dlg_bg_44.png","otv_dlg_bg_45.png") else (0,0,522,301)]
            if spots:
                for (x0,y0,x1,y1) in spots:
                    a = o2.crop((x0*2,y0*2,x1*2,y1*2)) if o2 else None
                    b = c2.crop((x0*2,y0*2,x1*2,y1*2))
                    cells.append((tag+" (%d,%d)"%(x0,y0), a, b))
            else:
                cells.append((tag, o2, c2))
        W = 1460
        H = sum((c[2].height if c[2].width<=W//2-10 else int(c[2].height*(W//2-10)/c[2].width)) + 40 for c in cells) + 10
        sheet = Image.new("RGBA", (W+20, H), (24,26,32,255)); dr = ImageDraw.Draw(sheet)
        y = 5
        for label, a, b in cells:
            half = W//2 - 10
            if a.width > half:
                a = a.resize((half, int(a.height*half/a.width)), Image.LANCZOS)
            if b.width > half:
                b = b.resize((half, int(b.height*half/b.width)), Image.LANCZOS)
            sheet.paste(a, (10, y), a); sheet.paste(b, (10+a.width+14, y), b)
            dr.text((10, y+max(a.height,b.height)+3), label+"  左=原图(超分2×) / 右=AI中文(超分2×)", fill=(220,230,240,255), font=fonts)
            y += max(a.height,b.height) + 40
        out = os.path.join(RV, "全量审阅_%02d.png" % (gi+1))
        sheet.convert("RGB").save(out)
        print("->", out, len(cells), "对")

if __name__ == "__main__":
    if "--upscale" in sys.argv:
        upscayl_all()
    sheets()
