# -*- coding: utf-8 -*-
"""
M15 证据：把 16 屏无头截图拼成一张 contact sheet（缩略图网格 + 文件名标注）。

· 自动定位画布 bbox：画布底色为纯黑 #000000，页面外壳为 #0b0d12 / #2a323f，
  故「纯黑像素的外接矩形」即画布区域（无需硬编码窗口内偏移）。
· 只读 _工作/M15_证据/html_*.png，输出 html_contact_sheet.png。
"""
import io, os, sys

from PIL import Image, ImageDraw, ImageFont

EV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "M15_证据")

SCREENS = ["title", "dialog", "sysicons", "sysmenu", "save", "load", "config",
           "backlog", "gallery", "music", "chapter", "fragment", "flowchart",
           "ending", "loading", "confirm"]


def canvas_bbox(im):
    """纯黑像素外接矩形 = 画布。找不到则回退整图。"""
    px = im.convert("RGB")
    w, h = px.size
    # 逐行/逐列扫描纯黑（阈值极窄，避免把深灰外壳算进来）
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(0, h, 2):
        row = [px.getpixel((x, y)) for x in range(0, w, 2)]
        for i, c in enumerate(row):
            if c[0] <= 4 and c[1] <= 4 and c[2] <= 4:
                x = i * 2
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx < 0:
        return None          # 画布被贴图铺满、无纯黑像素 → 无有效测量
    return (max(0, minx - 1), max(0, miny - 1), min(w, maxx + 2), min(h, maxy + 2))


def load_font(size):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
              r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def main():
    # ① 逐屏测「纯黑像素」外接矩形；画布全被贴图覆盖的屏（title/gallery/fragment）
    #    测不到黑边，故取**面积最大者**作为统一画布矩形（同一次截图会话里窗口尺寸
    #    与 fitScale 恒定，画布矩形必然一致）。
    ims = {}
    boxes = {}
    for s in SCREENS:
        p = os.path.join(EV, "html_%s.png" % s)
        if not os.path.exists(p):
            print("MISSING", p)
            continue
        im = Image.open(p).convert("RGB")
        ims[s] = im
        bb = canvas_bbox(im)
        boxes[s] = bb
        print("%-10s src=%s raw_bbox=%s" % (s, im.size, bb))

    valid = {k: v for k, v in boxes.items() if v}
    best = max(valid.items(), key=lambda kv: (kv[1][2] - kv[1][0]) * (kv[1][3] - kv[1][1]))
    CANVAS_BOX = best[1]
    print("CANVAS_BOX (取自最大者 %s；有效测量 %d/%d 屏) = %s"
          % (best[0], len(valid), len(boxes), CANVAS_BOX))

    tiles = []
    for s in SCREENS:
        if s not in ims:
            continue
        tiles.append((s, ims[s].crop(CANVAS_BOX)))
        print("%-10s crop->%s" % (s, CANVAS_BOX))

    TW = 460                       # 缩略图宽
    th_h = int(TW * 1080 / 1920)   # 按画布比例
    COLS, PAD, LABEL = 4, 10, 26
    rows = (len(tiles) + COLS - 1) // COLS
    W = COLS * TW + (COLS + 1) * PAD
    H = rows * (th_h + LABEL) + (rows + 1) * PAD
    sheet = Image.new("RGB", (W, H), (12, 14, 20))
    dr = ImageDraw.Draw(sheet)
    f = load_font(18)
    fb = load_font(20)

    for i, (name, im) in enumerate(tiles):
        r, c = divmod(i, COLS)
        x = PAD + c * (TW + PAD)
        y = PAD + r * (th_h + LABEL + PAD)
        th = im.resize((TW, th_h), Image.LANCZOS)
        sheet.paste(th, (x, y))
        dr.rectangle([x - 1, y - 1, x + TW, y + th_h], outline=(70, 84, 106))
        dr.text((x + 2, y + th_h + 3), "html_%s.png" % name, fill=(200, 214, 232), font=fb)

    dr.text((PAD, 0), "", fill=(255, 255, 255), font=f)
    out = os.path.join(EV, "html_contact_sheet.png")
    sheet.save(out)
    print("WROTE", out, sheet.size, "tiles =", len(tiles))


if __name__ == "__main__":
    main()