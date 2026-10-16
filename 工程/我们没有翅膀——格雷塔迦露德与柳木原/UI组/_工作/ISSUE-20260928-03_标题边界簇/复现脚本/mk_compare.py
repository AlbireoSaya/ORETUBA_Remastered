# -*- coding: utf-8 -*-
r"""mk_compare.py —— 把 A（现状＝零间隙）与 B（补硬断行）两帧合成一张**实机对照图**

判据（实测，不是目测）：
  · **对勾右缘** = 节点 x + 10 + 20 = 节点 x + 30（对勾 20×20 @ 节点 +10/+12）
  · **首行墨迹左缘** = 标题盒内**第一行**文字像素的最小 x。做法：标题盒内取「与底板色的距离 > 60」
    的像素为墨迹（文字是深蓝 `@palette.psv_ink`、底板是浅紫面），按行统计墨迹数 → 切出行带 →
    取第一行带的最小 x。
  · **间隙** = 首行墨迹左缘 − 对勾右缘（<0 即压住、=0 即紧贴、>0 即有空隙）

输出：
  · `对照_长标题与已读对勾_实机.png` —— 4 面板（2 节点 × 2 变体）＋两条标尺线 ＋ 间隙读数
  · `读数.tsv` —— 逐节点的 对勾右缘 / 首行墨迹左缘 / 间隙 / 行数
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))          # …\复现脚本
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # …\UI组（HERE 已是目录 ⇒ 上三级）
assert os.path.basename(UI) == "UI组", UI
EVID = os.path.join(os.path.dirname(HERE), "证据")
A_PNG = os.path.join(EVID, "A", "shot_77_flowchart.png")
B_PNG = os.path.join(EVID, "B", "shot_77_flowchart.png")
OUT_PNG = os.path.join(EVID, "对照_长标题与已读对勾_实机.png")
OUT_TSV = os.path.join(EVID, "读数.tsv")

NODES = [("fc.frag4.0008", "42_3", 441, 670, 296, 65),
         ("fc.frag4.0009", "42_4", 816, 670, 296, 65)]
INK_LUM_MAX = 120        # 判「墨迹」：亮度 < 本值（底板亮度约 193、文字约 33 ⇒ 分离干净）
#   早先用「与底板色的距离 > 60」会把底板自身的斜面/描边也算成墨迹 ⇒ 首行左缘恒等于盒左缘（假测量）
ZOOM = 5
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"


def font(sz):
    return ImageFont.truetype(FONT_PATH, sz, index=0)


def rgb_over_black(p):
    a = np.asarray(Image.open(p).convert("RGBA")).astype(np.int16)
    al = a[:, :, 3:4].astype(np.float32) / 255.0
    return (a[:, :, :3] * al).astype(np.uint8), a[:, :, 3]


def line_bands(ink):
    r"""按行统计墨迹，切出连续行带（行间允许 1 行空隙）。"""
    rows = ink.sum(axis=1)
    bands, cur = [], None
    gap = 0
    for y, n in enumerate(rows):
        if n > 0:
            if cur is None:
                cur = [y, y]
            else:
                cur[1] = y
            gap = 0
        else:
            if cur is not None:
                gap += 1
                if gap >= 1:          # 出现**整行空白**即切行（`> 1` 会把只隔 1 空行的两行并成一行）
                    bands.append(tuple(cur))
                    cur = None
                    gap = 0
    if cur is not None:
        bands.append(tuple(cur))
    return bands


def measure(img_rgb, node):
    nid, script, x, y, w, h = node
    box = img_rgb[y:y + h, x + 28:x + 28 + 240]
    plate = np.median(box.reshape(-1, 3), axis=0)
    lum = (0.299 * box[:, :, 0] + 0.587 * box[:, :, 1] + 0.114 * box[:, :, 2])
    ink = lum < INK_LUM_MAX
    # ★ 三处「非标题墨迹」必须剔掉（都是实测踩过的坑）：
    #   ① 底板**上/下描边**：rows 0..6 与 58..62 全列皆暗 ⇒ 是框线不是字；可用文字区＝生成器登记的 plate rows 8..55
    #   ② 已读对勾落在**标题盒内**的右缘（对勾 x 10..30、盒从节点 +28 起 ⇒ 盒内 col 0..2；它的深绿牌亮度≈72 < 120）
    #   ③ 由此「间隙」口径＝**首列墨迹 − 对勾右缘(+30)**：col 0..2 全剔 ⇒ 首次检出必 ≥ +31
    ink[0:8, :] = False
    ink[56:, :] = False
    ink[:, 0:3] = False
    bands = line_bands(ink)
    first = bands[0] if bands else None
    ink_left = (x + 28 + int(np.argmax(ink[first[0]:first[1] + 1].any(axis=0)))) if first else None
    return dict(id=nid, script=script, node_x=x, plate=tuple(int(v) for v in plate),
                lines=len(bands), bands=bands,
                check_right=x + 30, ink_left=ink_left,
                gap=(ink_left - (x + 30)) if ink_left is not None else None)


def panel(img_rgb, node, m, label, lines_data):
    _nid, _s, x, y, w, h = node
    pad = 8
    crop = Image.fromarray(img_rgb[y - pad:y + h + pad, x - pad:x + w + pad])
    crop = crop.resize((crop.width * ZOOM, crop.height * ZOOM), Image.NEAREST)
    d = ImageDraw.Draw(crop)
    # 两条标尺线（节点坐标系 → 面板像素）
    ck = (x + 30 - (x - pad)) * ZOOM
    d.line([(ck, 0), (ck, crop.height)], fill=(255, 90, 90), width=2)
    if m["ink_left"] is not None:
        ik = (m["ink_left"] - (x - pad)) * ZOOM
        d.line([(ik, 0), (ik, crop.height)], fill=(90, 220, 120), width=2)
    for b in m["bands"][1:]:
        pass
    d.rectangle([0, 0, crop.width - 1, 26], fill=(0, 0, 0))
    d.text((8, 3), label, font=font(18), fill=(255, 255, 255))
    g = m["gap"]
    tag = "紧贴（0px 间隙）" if g == 0 else ("压住 %dpx" % -g if g < 0 else "留 %dpx 空隙" % g)
    d.text((8, 30), "对勾右缘 +30 ｜ 首行墨迹 +%d ｜ 间隙 %s ｜ 标题 %d 行（按数据）"
           % (m["ink_left"] - x, tag, lines_data), font=font(17), fill=(255, 235, 140))
    return crop


def rendered_lines(txts):
    r"""用生成器**自己的折行函数**复算渲染行数（`ui_theme_wrap` 是 `uiThemeWrap` 的逐字复刻）。

    为什么不用像素行带：紧凑的两行（`line_spacing 1.0`）与「单行内偶然出现的空行」只有 1 行之差，
    像素分不开；而行数是**数据的函数**，直接算最准（也与四判据里的截断判据同源）。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_gfl", os.path.join(UI, "工具", "gen_flow_layout.py"))
    G = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(G)
    wof, _ = G.width_fn(19)                      # 节点标题字号 19
    return {nid: len(G.ui_theme_wrap(t, 240, 2, wof)[0]) for nid, t in txts.items()}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    A, _ = rgb_over_black(A_PNG)
    B, _ = rgb_over_black(B_PNG)
    rows = [measure(A, n) for n in NODES], [measure(B, n) for n in NODES]
    # 两条标题在「未断行 / 补硬断行」两种写法下的**渲染行数**（按数据算，见 rendered_lines）
    TXT_A = {"fc.frag4.0008": "格兰·玛尼耶（ＥＡＧＬＥ）",
             "fc.frag4.0009": "格兰玛·露尼耶（ＦＡＬＣＯＮ）"}
    TXT_B = {k: v.replace("（", "\n（", 1) for k, v in TXT_A.items()}
    LINES = [rendered_lines(TXT_A), rendered_lines(TXT_B)]

    with io.open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("# 口径：间隙＝首行墨迹左缘 − 对勾右缘(+30)；行数＝生成器 `ui_theme_wrap` 复算的**渲染行数**\n")
        f.write("# 说明：这两个节点都在**番外独立层**；番外层目前不产 `_read`（对勾只在主干节点产生），\n")
        f.write("#       故对勾是本探针注入的**未来态**（挂在层旗标 `fc_layer` 上，由巡演真实 flag 机制驱动）。\n")
        f.write("变体\t节点\tscript\t对勾右缘(节点相对)\t首行墨迹左缘(节点相对)\t间隙px\t渲染行数\n")
        for vi, (tag, ms) in enumerate((("A 现状", rows[0]), ("B 补硬断行", rows[1]))):
            for m in ms:
                f.write("%s\t%s\t%s\t+30\t+%d\t%d\t%d\n"
                        % (tag, m["id"], m["script"], m["ink_left"] - m["node_x"], m["gap"],
                           LINES[vi][m["id"]]))
                print("%-12s %-14s 首行墨迹 +%-4d 间隙 %+d  渲染行数 %d"
                      % (tag, m["id"], m["ink_left"] - m["node_x"], m["gap"], LINES[vi][m["id"]]))

    panels = []
    for vi, (tag, ms) in enumerate((("A｜现状：标题未断行", rows[0]),
                                    ("B｜补硬断行：标题两行", rows[1]))):
        panels.append([panel(A if vi == 0 else B, n, m,
                             "%s — %s（%s）" % (tag, n[1], n[0]), LINES[vi][n[0]])
                       for n, m in zip(NODES, ms)])
    pw = max(p.width for row in panels for p in row)
    ph = max(p.height for row in panels for p in row)
    HEAD = 92
    W = pw * 2 + 30
    H = HEAD + (ph + 16) * 2 + 12
    canvas = Image.new("RGB", (W, H), (24, 26, 32))
    d = ImageDraw.Draw(canvas)
    d.text((14, 10), "长标题 × 已读对勾：现状 vs 补硬断行（实机帧｜krkr 自建版 · 对勾＝注入的未来态）",
           font=font(26), fill=(255, 255, 255))
    d.text((14, 44), "红＝对勾右缘(+30)　绿＝首行墨迹左缘　·　两个**零间隙边界簇**节点"
                     "（42_3 / 42_4）—— 当前不变量要求 +30 以上，这两条恰好 = +30（即 0px 余量）",
           font=font(16), fill=(200, 205, 215))
    ga = [rows[0][i]["gap"] for i in range(2)]
    gb = [rows[1][i]["gap"] for i in range(2)]
    d.text((14, 66), "A 现状：间隙 %d／%d px（紧贴、不压字）　　　B 补硬断行：间隙 %d／%d px"
           % (ga[0], ga[1], gb[0], gb[1]), font=font(16), fill=(150, 230, 170))
    for r, prow in enumerate(panels):
        for c, p in enumerate(prow):
            x = 10 + c * (pw + 10)
            y = HEAD + r * (ph + 16)
            canvas.paste(p, (x, y))
    canvas.save(OUT_PNG)
    print("\n写出 %s（%d×%d）" % (OUT_PNG, W, H))
    print("写出 %s" % OUT_TSV)


if __name__ == "__main__":
    main()
