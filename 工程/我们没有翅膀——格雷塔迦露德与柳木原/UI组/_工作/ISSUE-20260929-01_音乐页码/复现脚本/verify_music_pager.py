# -*- coding: utf-8 -*-
r"""verify_music_pager.py —— 音乐鉴赏屏本批两处改动的**渲染级**取证

① 页码行 + 翻页键**整体下移 25px**（y 939 → 964；热区 931 → 956）
② `mu.pg_tx_2`/`mu.pg_tx_3` 字色与 `mu.pg_tx_1` 同步（`@palette.text_menu` #E8E8F0 → `@palette.node_locked` #4A4A56）

做法：把 `复刻\` 复制到临时栈，用**深链** `?flags=music_page:1|2|3` 各渲一帧（无头 Edge），
再从三帧里**量页码文本的墨迹色**（取该文本框内「与霜板底差异最大」的像素众数），并与 `mu.pg_tx_1` 逐通道比。
另把三帧拼一张对照图，便于人眼复核「下移后是否还在板内 / 与页脚有无压叠」。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260929-01_音乐页码/复现脚本/verify_music_pager.py"
"""
import io
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # …\UI组
assert os.path.basename(UI) == "UI组", UI
REP = os.path.join(UI, "复刻")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(ISSUE, "证据")
TMP = os.path.join(EVID, "_stack")
UD = r"E:/ZCode Workspace/Galgame/临时/edge_music29"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
COPY = ["index.html", "replica.css", "flow_data.js", "replica.js", "asset_index.js"]
BOX = (858, 964, 204, 56)          # 本批位移后的页码文本框（数据 858,964,204×56）
FONT = r"C:\Windows\Fonts\msyh.ttc"


def fileurl(p):
    p = os.path.abspath(p).replace("\\", "/")
    return "file:///" + (p[0].lower() + p[1:] if p[1:2] == ":" else p)


def build():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(TMP, f))
    shutil.copy2(os.path.join(REP, "ui_layout.js"), os.path.join(TMP, "ui_layout.js"))
    page = io.open(os.path.join(TMP, "index.html"), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    # ★ 与工程既有无头脚手架（`e3_title_contrast.py`）同款：**必须 setScale(1) 并把外壳复位**
    #   否则画布被整体缩放/偏移 ⇒ 按数据坐标裁剪会裁到别处（首版就踩了：量到的是页脚下方的深色背景）。
    page = page.replace("</body>",
                        "<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
                        ".shell-head,.shell-foot{display:none!important}"
                        "#stage-wrap{justify-content:flex-start!important;display:block!important}"
                        "#stage{box-shadow:none!important}</style>"
                        "<script>window.addEventListener('load',function(){"
                        "var R=window.UI_REPLICA; R&&R.setScale(1);});</script></body>")
    io.open(os.path.join(TMP, "index.html"), "w", encoding="utf-8").write(page)


def shot(page_no):
    out = os.path.join(EVID, "复刻_music_page%d.png" % page_no)
    url = (fileurl(os.path.join(TMP, "index.html"))
           + "?screen=music&chrome=0&flags=music_page:%d" % page_no)
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("截图失败：" + out)
    im = Image.open(out).convert("RGB")
    if im.width >= 1920 and im.height >= 1080:
        im = im.crop((0, 0, 1920, 1080))
    im.save(out)
    return out


def ink_color(png):
    """量页码文本墨迹色：框内亮度最低 3% 像素的中位（文字是深墨、底是浅霜板）。"""
    a = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
    x, y, w, h = BOX
    box = a[y:y + h, x:x + w].reshape(-1, 3)
    lum = 0.299 * box[:, 0] + 0.587 * box[:, 1] + 0.114 * box[:, 2]
    k = max(1, int(len(lum) * 0.03))
    idx = np.argsort(lum)[:k]
    return tuple(int(v) for v in np.median(box[idx], axis=0))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(EVID, exist_ok=True)
    build()
    shots, cols = [], []
    print("页码框（量测区）= x%dy%d %d×%d" % (BOX[0], BOX[1], BOX[2], BOX[3]))
    for pg in (1, 2, 3):
        p = shot(pg)
        c = ink_color(p)
        shots.append(p)
        cols.append(c)
        print("  music_page=%d ⇒ 墨迹色 RGB %s ｜ #%02X%02X%02X" % (pg, c, c[0], c[1], c[2]))
    same = all(c == cols[0] for c in cols)
    print("  三页墨迹色**逐通道相同** ⇒ %s" % ("✓ 与 mu.pg_tx_1 同步" if same else "✗ 不一致"))
    # 三帧并排对照（各裁页码行 + 周边）
    pad = 60
    crops = [Image.open(p).crop((BOX[0] - 240, BOX[1] - pad, BOX[0] + BOX[2] + 240, BOX[1] + BOX[3] + pad))
             for p in shots]
    W = max(c.width for c in crops); H = sum(c.height for c in crops) + 4 * 34
    canvas = Image.new("RGB", (W, H), (24, 26, 32))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 20, index=0)
    y = 0
    for i, c in enumerate(crops, 1):
        d.text((8, y + 6), "music_page=%d ｜ 墨迹色 #%02X%02X%02X" % (i, *cols[i - 1]), font=f, fill=(240, 240, 240))
        y += 34
        canvas.paste(c, (0, y)); y += c.height
    out = os.path.join(EVID, "对照_音乐页码三页.png")
    canvas.save(out)
    print("写出 %s" % out)
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
