# -*- coding: utf-8 -*-
"""
M15 证据：krkr 实机截图 与 HTML 复刻截图 **逐屏并排对照** + 像素差异度量。

· krkr 侧：_工作/M15_证据/krkr/png_m15/shot_*.png（1920×1080，M15_run_autotour.sh 导出）
· HTML 侧：_工作/M15_证据/html_*.png（2000×1400 整页截图，按画布 bbox 裁到 1920×1080）
· 输出：_工作/M15_证据/compare_sheet.png（krkr | HTML 并排）+ 控制台差异度量表

差异度量的已知噪声（不是缺陷）：
  · 两侧字体栅格化不同（krkr 用系统字体 + 自有绘制，HTML 用浏览器 CSS 渲染）；
  · 对话框打字机进度不同（截图时机不同）；
  · dynamic 层占位画法不同（slot_thumb / gallery_preview / story_background）；
  · krkr 截图带 UI 转场遮罩的可能性（本巡演每步导出时转场已结束，实测无）。
"""
import io, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, "M15_证据")
KR = os.path.join(EV, "krkr", "png_m15")

# screen -> krkr 截图文件名（取巡演中该屏的第一次出现）
PAIRS = [
    ("title",     "shot_01_title.png"),
    ("dialog",    "shot_03_dialog.png"),
    ("sysicons",  "shot_05_sysicons.png"),
    ("sysmenu",   "shot_07_sysmenu.png"),
    ("save",      "shot_08_save.png"),
    ("load",      "shot_09_load.png"),
    ("config",    "shot_10_config.png"),
    ("backlog",   "shot_11_backlog.png"),
    ("gallery",   "shot_12_gallery.png"),
    ("music",     "shot_13_music.png"),
    ("chapter",   "shot_14_chapter.png"),
    ("fragment",  "shot_15_fragment.png"),
    ("flowchart", "shot_16_flowchart.png"),
    ("ending",    "shot_17_ending.png"),
    ("loading",   "shot_18_loading.png"),
    ("confirm",   "shot_20_confirm.png"),
]

CANVAS_BOX = (255, 219, 1720, 1042)   # 由 M15_mk_contact.py 实测（同一次截图会话恒定）


def load_font(size):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def diff_metrics(a, b):
    """返回 (平均绝对差, 差异像素占比>32, 差异像素占比>96)。"""
    if a.size != b.size:
        b = b.resize(a.size, Image.LANCZOS)
    pa, pb = a.convert("RGB"), b.convert("RGB")
    w, h = pa.size
    da = pa.tobytes()
    db = pb.tobytes()
    n = w * h
    tot = 0
    c32 = 0
    c96 = 0
    for i in range(0, len(da), 3):
        d = abs(da[i] - db[i]) + abs(da[i + 1] - db[i + 1]) + abs(da[i + 2] - db[i + 2])
        tot += d
        if d > 32 * 3 // 3 * 3:
            pass
        if d > 96:      # 三通道合计 > 96
            c96 += 1
        if d > 32:
            c32 += 1
    return tot / (n * 3.0), c32 * 100.0 / n, c96 * 100.0 / n


def main():
    rows = []
    for sid, kf in PAIRS:
        kp = os.path.join(KR, kf)
        hp = os.path.join(EV, "html_%s.png" % sid)
        if not (os.path.exists(kp) and os.path.exists(hp)):
            print("MISSING", sid, kp, hp)
            continue
        k = Image.open(kp).convert("RGB")
        h = Image.open(hp).convert("RGB").crop(CANVAS_BOX).resize((1920, 1080), Image.LANCZOS)
        m = diff_metrics(k, h)
        rows.append((sid, kf, k, h, m))
        print("%-10s krkr=%-20s MAD=%6.2f/255  像素差>32 占比=%5.2f%%  >96 占比=%5.2f%%"
              % (sid, kf, m[0], m[1], m[2]))

    TW = 372
    TH = int(TW * 1080 / 1920)
    LAB = 22
    GAP = 8
    PAIRS_PER_ROW = 2
    TILES_PER_ROW = PAIRS_PER_ROW * 2
    nrow = (len(rows) + PAIRS_PER_ROW - 1) // PAIRS_PER_ROW
    W = TILES_PER_ROW * TW + (TILES_PER_ROW + 1) * GAP
    H = nrow * (TH + LAB + GAP) + GAP
    sheet = Image.new("RGB", (W, H), (12, 14, 20))
    dr = ImageDraw.Draw(sheet)
    fb = load_font(15)
    fsm = load_font(13)

    for i, (sid, kf, k, h, m) in enumerate(rows):
        pr, pc = divmod(i, PAIRS_PER_ROW)
        for j, (im, tag) in enumerate(((k, "krkr"), (h, "HTML"))):
            x = GAP + (pc * 2 + j) * (TW + GAP)
            y = GAP + pr * (TH + LAB + GAP)
            sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
            dr.rectangle([x - 1, y - 1, x + TW, y + TH], outline=(70, 84, 106))
            dr.text((x + 2, y + TH + 2), "%s · %s" % (tag, sid), fill=(200, 214, 232), font=fb)
            if j == 1:
                dr.text((x + 2, y + TH + 2 + 15),
                        "MAD %.1f/255 · >32 %.1f%%" % (m[0], m[1]),
                        fill=(150, 166, 190), font=fsm)
    out = os.path.join(EV, "compare_sheet.png")
    sheet.save(out)
    print("WROTE", out, sheet.size, "pairs =", len(rows))


if __name__ == "__main__":
    main()