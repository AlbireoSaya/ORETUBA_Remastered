# -*- coding: utf-8 -*-
"""标题屏专用素材生成（UI 组 · ISSUE-20260919-11 · 主代理）

产出两件（写入 krkr/assets/ui/）：
  1) x_title_bg_1280.png   1280×720 标题背景
       中央 = 原版 tl2_bg1.png（800×600）**逐字节 1:1 原样**（D1：素材本体不缩放）
       四周 = 由该素材**边缘重度模糊**生成的氛围延展层（UI 组新建素材，非把素材放大当画面）
  2) x_title_logo.png      中文标题 logo（透明 PNG）
       装饰 = 从原版 tl1_logo.png 提取「浅色像素」（羽毛 + 雪花），去掉日文深色字
       文字 = 「我们没有翅膀」用楷体绘制（原版 logo 的蓝 + 白色描边）
       副题 = "under the innocent sky" 保留原版像素（该区域不参与去字）

只读源素材，只写 UI 组目录。可复跑（幂等）。
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一\系统UI"
OUT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\assets\ui"
WORK = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作\M9_证据"

CANVAS = (1280, 720)
BOX_4_3 = (240, 60, 800, 600)          # D1：4:3 源 1:1 居中

LOGO_BLUE = (26, 92, 168)              # 取自原版 logo 的深蓝（见 _工作/M9_证据/logo_probe.txt）
LOGO_HALO = (245, 250, 255)


def title_bg():
    """1280×720 标题背景。

    构成（三段，均不放大素材本体）：
      ① 中央 = 原版 tl2_bg1.png（800×600）**1:1 原字节**（D1）
      ② 四周 = 由**同一张素材**重度模糊 + 大幅压暗得到的**氛围填充层**（UI 组新建素材；
             不是把素材放大后当画面用——它不可辨认细节，只提供同源色调）
      ③ 中央四周一圈**柔和内阴影**（渐变，非描边线），让 1:1 画面与氛围层之间不出现硬切边
    曾试过「镜像延展」（1:1 像素），但该素材左右边缘有人物，镜像后出现**明显的人物重复**，
    故弃用——见 _工作/M9_证据/ 的两版预览对照。
    """
    art = Image.open(os.path.join(SRC, "tl2_bg1.png")).convert("RGB")
    assert art.size == (800, 600), art.size
    x, y, w, h = BOX_4_3
    W, H = CANVAS

    # ① 氛围层：重度模糊 + 压暗 + 提饱和
    amb = art.resize(CANVAS, Image.LANCZOS).filter(ImageFilter.GaussianBlur(72))
    amb = Image.blend(amb, Image.new("RGB", CANVAS, (0, 0, 0)), 0.62)
    amb = Image.blend(amb, amb.convert("L").convert("RGB"), -0.25)   # 负混合 = 提饱和

    # ③ 内阴影：中央区外一圈由暗到透明的渐变（先造一张"中心为 0、外为 1"的遮罩）
    canvas = amb.copy()
    shadow = Image.new("L", CANVAS, 0)
    ImageDraw.Draw(shadow).rectangle([x - 90, y - 90, x + w + 90, y + h + 90], fill=150)
    ImageDraw.Draw(shadow).rectangle([x - 26, y - 26, x + w + 26, y + h + 26], fill=0)
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    canvas = Image.composite(Image.new("RGB", CANVAS, (0, 0, 0)), canvas, shadow)

    # ② 中央 1:1 原图
    canvas.paste(art, (x, y))

    # 极轻的暗角
    vig = Image.new("L", CANVAS, 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.30, -H * 0.36, W * 1.30, H * 1.36], fill=90)
    vig = vig.filter(ImageFilter.GaussianBlur(140))
    canvas = Image.composite(Image.new("RGB", CANVAS, (0, 0, 0)), canvas, vig.point(lambda v: v // 3))

    p = os.path.join(OUT, "x_title_bg_1280.png")
    canvas.save(p)
    print("saved", p, canvas.size)
    return canvas


def title_logo():
    """中文标题 logo（透明 PNG）。

    原版 tl1_logo.png 的日文占据 y<118，**y>=118 是纯羽毛、无任何文字**（行最暗亮度 >=185，
    见 _工作/M9_证据/logo_diag.png 的亮度剖面）。故：
      装饰 = 原图 y>=118 的羽毛带（1:1 原像素，不缩放）
      文字 = 「我们没有翅膀」用楷体绘制（原版 logo 的深蓝 + 白色外沿）
      副题 = "under the innocent sky"（拉丁文，与系列英文副题一致）
    原版的日文与雪花**不参与**（雪花与文字交错，无法干净分离——如实登记）。
    """
    src = Image.open(os.path.join(SRC, "tl1_logo.png")).convert("RGBA")
    SW, SH = src.size                      # 482×165
    feather = src.crop((0, 118, SW, SH))   # 482×47 纯羽毛带

    CW, CH = 482, 168
    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

    font_title = None
    for cand in (r"C:\Windows\Fonts\simkai.ttf", r"C:\Windows\Fonts\simhei.ttf",
                 r"C:\Windows\Fonts\Dengb.ttf", r"C:\Windows\Fonts\msyhbd.ttc"):
        if os.path.exists(cand):
            font_title = ImageFont.truetype(cand, 72)
            face_used = cand
            break
    assert font_title is not None, "无可用中文字体"

    txt = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    title = "我们没有翅膀"
    tw = d.textlength(title, font=font_title)
    tx = int((CW - tw) / 2)
    ty = 8
    for ox, oy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3), (-2, 0), (2, 0)):
        d.text((tx + ox, ty + oy), title, font=font_title, fill=LOGO_HALO + (240,))
    d.text((tx, ty), title, font=font_title, fill=LOGO_BLUE + (255,))

    # 副题（拉丁）：用系统等宽斜体，与原版手写体同属「小字副题」层级
    tag_font = None
    for cand in (r"C:\Windows\Fonts\DejaVuSansMono-Oblique_0.ttf",
                 r"C:\Windows\Fonts\DejaVuSans-Oblique.ttf",
                 r"C:\Windows\Fonts\DejaVuSans.ttf"):
        if os.path.exists(cand):
            tag_font = ImageFont.truetype(cand, 17)
            break
    if tag_font is not None:
        TAG_TXT = "under the innocent sky"
        TAG_XY = (16, 96)
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            d.text((TAG_XY[0] + ox, TAG_XY[1] + oy), TAG_TXT, font=tag_font, fill=(16, 34, 62, 235))
        d.text(TAG_XY, TAG_TXT, font=tag_font, fill=(226, 238, 252, 255))

    canvas = Image.alpha_composite(canvas, txt)
    canvas.alpha_composite(feather, (0, CH - feather.size[1]))   # 羽毛带压在最上层

    p = os.path.join(OUT, "x_title_logo.png")
    canvas.save(p)
    print("saved", p, canvas.size, "| 字体 =", face_used, "| 标题宽 = %d" % tw)
    return canvas


def main():
    os.makedirs(WORK, exist_ok=True)
    bg = title_bg()
    lg = title_logo()
    # 证据：合成预览（把 logo 摆到背景左上，模拟标题屏）
    prev = bg.copy().convert("RGBA")
    prev.alpha_composite(lg, (40, 30))
    prev.convert("RGB").save(os.path.join(WORK, "title_preview_1280.png"))
    print("saved preview -> _工作/M9_证据/title_preview_1280.png")


if __name__ == "__main__":
    sys.exit(main())