# -*- coding: utf-8 -*-
r"""M47 · 设置屏「视觉验收」：把我们的新屏两页与用户给的《交汇协奏曲》参考图并排

■ 用途
  用户 2026-09-24 要求的核心是**观感**（风格简单、透明背景、巨型方框、文字锚定、我们的配色）。
  本脚本给出两张并排对照图，供主代理目视 + 交用户裁决：
    对照_系统页.png = 左：参考作 系统设置.png ／ 右：我们 ?screen=config
    对照_声音页.png = 左：参考作 声音设置.png ／ 右：我们 ?screen=config&flags=cfg_page:snd

■ 口径
  · 参考截图实测 1442×862，游戏内容约 1440×810 ⇒ 缩放到 1920×1080 基准需 ×1.3333；
    为并排好看，**两边都缩到同宽**（左：参考按内容区裁掉窗口 chrome 再缩；右：我们的画布区裁出后缩）。
  · 我们的截图由无头 Edge 出（含 replica 的外壳 chrome），故按 DOM 报告的 `#canvas` transform 缩放比例
    与画布原点把画布区裁出来（同 M46 的做法），保证与参考**同尺度**比较。

■ 用法
    python _工作\M47_设置屏重设\复现脚本\m47_html_config_shots.py
"""
import io
import os
import re
import subprocess
import sys
import urllib.parse

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)                       # …/M47_设置屏重设
UI = os.path.dirname(os.path.dirname(EVID))        # …/UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_m47"
# 用户给的参考图在主工作树（本工作树那份目录是空的）
REF_DIR = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\用户临时文件区"

CANVAS_W, CANVAS_H = 1920, 1080


def url(query):
    p = os.path.join(REP, "index.html").replace("\\", "/")
    return "file:///" + urllib.parse.quote(p) + query


def shot_via_w4(query, out_png):
    """★ M47 定稿：不再自研裁切 —— 直接调 W4 的 1:1 截图入口（隐藏外壳 + setScale(1)，
    截图左上 1920×1080 就是画布本体）。W4 已实测该口径与画布逐像素对齐，且能处理
    中文绝对路径（Edge 的 --screenshot= 相对中文路径不落盘）。"""
    cli = os.path.join(UI, "_工作", "ISSUE-20260924-01_W4_证据", "复现脚本", "w4_html_config_shots.py")
    if not os.path.exists(cli):
        print("!! 找不到 W4 的截图脚本，回退到自研口径：" + cli)
        return shot(query, out_png, out_png + ".dom.html")
    r = subprocess.run([sys.executable, cli, "--shot", query, out_png],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        print(r.stdout.decode("utf-8", "replace")[-800:])
    return os.path.exists(out_png)


def shot(query, out_png, dump=None):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1920,1080", "--virtual-time-budget=9000",
           "--screenshot=" + out_png]
    if dump:
        cmd.append("--dump-dom")
    cmd.append(url(query))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dump:
        io.open(dump, "w", encoding="utf-8").write(r.stdout.decode("utf-8", "replace"))
    return os.path.exists(out_png)


def canvas_crop(png, dump):
    """按 DOM 的 #canvas transform 缩放比 + 原点，把画布区裁出来（1:1 于 1920×1080）。"""
    dom = io.open(dump, encoding="utf-8").read()
    m = re.search(r'id="canvas"[^>]*transform:\s*scale\(([0-9.]+)\)', dom)
    if not m:
        m = re.search(r'transform:\s*scale\(([0-9.]+)\)', dom)
    s = float(m.group(1)) if m else 1.0
    im = Image.open(png).convert("RGB")
    # 画布在页面里的左上角：由 #stage 的宽度推算（replica 里 stage 宽 = 画布宽×s，居中于视口）
    # 稳妥做法：直接按「缩放后的画布尺寸」在截图里找左上角（页面左右居中、header 之下）
    w, h = int(round(CANVAS_W * s)), int(round(CANVAS_H * s))
    # 扫描找到画布区域（非页面纯色背景）——简化：水平居中、垂直取 header 之下的最大可用
    x0 = max(0, (im.width - w) // 2)
    y0 = 0
    # 用一条水平线找画布左边界（画布有内容/背景色，页面外壳是另一色）
    px = im.load()
    row = im.height // 2
    # 从左往右找第一个明显不同于页面底色的像素（页面底色取 x=2 处的颜色）
    base = px[2, row]
    for x in range(im.width):
        if sum(abs(px[x, row][i] - base[i]) for i in range(3)) > 24:
            x0 = x
            break
    for y in range(im.height):
        if px[x0 + min(5, w - 1), y] != base and abs(px[x0 + min(5, w - 1), y][0] - base[0]) > 6:
            y0 = y
            break
    crop = im.crop((x0, y0, min(im.width, x0 + w), min(im.height, y0 + h)))
    return crop.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)


def ref_crop(name):
    """参考截图：裁掉窗口标题栏/菜单栏（约 y<52）与右侧滚动条，再缩到 1920 宽。"""
    im = Image.open(os.path.join(REF_DIR, name)).convert("RGB")
    # 实测：内容区 ≈ (1, 52) 起，1440×810
    box = (1, 52, min(im.width, 1 + 1440), min(im.height, 52 + 810))
    return im.crop(box).resize((CANVAS_W, CANVAS_H), Image.LANCZOS)


def side_by_side(ref_name, our_png, dump, out_name, label):
    ref = ref_crop(ref_name)
    our = Image.open(our_png).convert("RGB")   # 已是 1:1 画布
    W, H = 1180, 664          # 每边缩到这个尺寸再并排
    out = Image.new("RGB", (W * 2 + 16, H + 34), (18, 18, 18))
    out.paste(ref.resize((W, H), Image.LANCZOS), (0, 34))
    out.paste(our.resize((W, H), Image.LANCZOS), (W + 16, 34))
    from PIL import ImageDraw
    d = ImageDraw.Draw(out)
    d.text((8, 10), "REF  " + label, fill=(150, 220, 255))
    d.text((W + 24, 10), "OURS  " + label, fill=(255, 230, 160))
    dst = os.path.join(EVID, out_name)
    out.save(dst)
    print("->", dst)


def main():
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    ok = True
    for q, tag, ref, out in (("?screen=config", "系统页", "系统设置.png", "对照_系统页.png"),
                             ("?screen=config&flags=cfg_page:snd", "声音页", "声音设置.png", "对照_声音页.png")):
        png = os.path.join(EVID, "我们_%s.png" % tag)
        dump = os.path.join(EVID, "我们_%s.dom.html" % tag)
        ok = shot_via_w4(q, png) and ok
        if not os.path.exists(os.path.join(REF_DIR, ref)):
            print("缺参考图：", os.path.join(REF_DIR, ref))
            continue
        side_by_side(ref, png, None, out, tag)
    print("判定：" + ("两张对照图已生成" if ok else "**截图失败**"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
