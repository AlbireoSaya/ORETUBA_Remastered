# -*- coding: utf-8 -*-
r"""psv_make_shell_strip.py —— 39 鉴赏外壳「页签条底板」拆件（PSV 横幅带）。

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮 · D 鉴赏四页）｜ 派单：`D 组换皮——27/28/37/38/39`。
依据：`PSV换皮_素材与文字处置清单.md` §七 用户裁决「换皮深度 = 深度换皮：底图换 PSV 件 ＋
      我方内容按 PSV 实测版式常量重新排版」；`layout\_schema.md`（无 nine 的 image ⇒ w/h 必须 = PNG 实尺寸）。

**做什么**：把已入库的 PSV 全屏件 `ui/x_ui_psv_gal_shell.png`（`otv_gm_bg1` 屏区，
1920×1080，含英文题 ALBUM ＋页脚）中那条**横贯全幅的横幅带**裁下来，作为 39 外壳
`gs.strip`（页签条底板）的新素材。

**为什么从已入库件裁、而不是回到参考区**：`x_ui_psv_gal_shell.png` 就是该屏区件的
1:1 入库副本（`工具\m53_psv_ui_assets.py`，`BOX_TOP_1080`），从它裁 ⇒ **只读参考区零触碰**
（参考区为只读，禁写），且裁出来的像素与参考区逐字节同源。

**裁切几何（实测口径）**：横幅带在源件中的可测边界 —— 逐行全幅平均亮度（脚本 `--measure` 可复现）：
  · y<230：霜白页（#F0+），带顶斜向雪花堆边（逐列顶界 150..380 不等）；
  · y 424..500：全幅最暗段（均值 ~197，`lum<215` 覆盖 99–100%）；
  · **y455 与 y601 是该区间内两条最清晰的水平边界**（逐行一阶跃变 1.53 / 1.27，
    其余行 |Δ|<1.2）⇒ 取 **y455 起、高 100**（100 是「页签条」观感所需的最小高度，
    且必须避开 28 页 PSV 播放条顶沿 y102 ⇒ 条带底必须 ≤100）。
  · 横向**从 x340 起**：x0..340 是英文题字区（ALBUM/MUSIC/MOVIE 实测 x64..~300），
    页签条不得压住英文题字（用户裁决：英文题字保留原样）。
  · 左缘 80px **alpha 线性淡入**（x340→420，α 0→255）：裁口落在浅底霜页上，
    硬切会出现一条竖直切口；淡入后与页面底自然接续。

**产出**：`krkr\assets\ui\x_ui_psv_shell_strip.png` = **1580×100**，PNG-32 真 alpha。
  摆放口径：元素 `gs.strip` 写在 **(340,0,1580,100)**，1:1 无 nine（`verify_ui [2]` 直接成立）。
  左缘淡入区（x340..420）与页面底（白霜页）融合 ⇒ 观感上是页面右上角伸出的横幅带。

**优化**（派单：`& 0xFC` ＋ `optimize=True, compress_level=9`，体积预算 96 MB / 当前 95.06 MB）：
  RGB 三通道各 `v & 0xFC`（每通道最大误差 3/255，8→6 bit），**alpha 逐像素原样保留**
  （不量化 ⇒ 淡入带平滑、透明区不被污染）。不做调色板量化（本资产集 0 件 P 模式）。

**幂等**：同一输入产出逐字节相同；`--check` 只校验不写盘。
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))       # <UI组>\工具
UI = os.path.dirname(HERE)                             # <UI组>
UI_ASSETS = os.path.join(UI, "krkr", "assets", "ui")
SRC = os.path.join(UI_ASSETS, "x_ui_psv_gal_shell.png")
OUT = os.path.join(UI_ASSETS, "x_ui_psv_shell_strip.png")

# ---- 实测几何（`--measure` 复算）----
CROP = (340, 455, 1920, 555)     # left, top, right, bottom ⇒ 1580×100
FADE_X0, FADE_X1 = 340, 420      # 左缘 alpha 线性淡入（源坐标）
BAND_ROWS_CRISP = (455, 601)     # 源件内该横幅带的两条清晰水平边界（证据）


def measure():
    """复算并打印横幅带的逐行证据（只读）。"""
    im = Image.open(SRC).convert("RGB")
    px = im.load()
    W, H = im.size
    print("源件 %s %dx%d" % (os.path.basename(SRC), W, H))
    xs = list(range(0, W, 4))
    means = {}
    for y in range(380, 660):
        s = 0
        for x in xs:
            r, g, b = px[x, y]
            s += (r + g + b) / 3
        means[y] = s / len(xs)
    print("  逐行一阶跃变 |Δ|>=1.0（380..660）：")
    for y in range(381, 660):
        d = means[y] - means[y - 1]
        if abs(d) >= 1.0:
            print("    y=%d  %.2f -> %.2f  (Δ%.2f)" % (y, means[y - 1], means[y], d))
    print("  取带 y=%d..%d（高 %d），横向 x=%d..%d（宽 %d）"
          % (CROP[1], CROP[3] - 1, CROP[3] - CROP[1], CROP[0], CROP[2] - 1, CROP[2] - CROP[0]))


def build():
    """裁切 + 左缘淡入 + 降色深 → 落盘；返回 (尺寸, 字节数)。"""
    im = Image.open(SRC).convert("RGBA")
    band = im.crop(CROP)
    w, h = band.size
    px = band.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            sx = CROP[0] + x
            if sx < FADE_X1:                       # 左缘线性淡入
                t = (sx - FADE_X0) / float(FADE_X1 - FADE_X0)
                a = int(round(a * t))
            px[x, y] = (r & 0xFC, g & 0xFC, b & 0xFC, a)
    band.save(OUT, "PNG", optimize=True, compress_level=9)
    return band.size, os.path.getsize(OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true", help="只复算并打印横幅带几何证据")
    ap.add_argument("--check", action="store_true", help="只校验现有产物（尺寸 / 边缘 alpha / md5）")
    a = ap.parse_args()
    if a.measure:
        measure()
        return 0
    if a.check:
        if not os.path.exists(OUT):
            print("FAIL 产物不存在：%s" % OUT)
            return 1
        im = Image.open(OUT)
        pxg = im.load()
        a_lt = pxg[0, im.size[1] // 2][3]
        a_rt = pxg[im.size[0] - 1, im.size[1] // 2][3]
        a_top = pxg[im.size[0] // 2, 0][3]
        a_bot = pxg[im.size[0] // 2, im.size[1] - 1][3]
        print("产物 %s %s mode=%s 字节=%d" % (os.path.basename(OUT), im.size, im.mode,
                                            os.path.getsize(OUT)))
        print("  边缘 alpha：左缘=0? %d ｜ 右缘=255? %d ｜ 顶=255? %d ｜ 底=255? %d"
              % (a_lt, a_rt, a_top, a_bot))
        print("  md5=%s" % hashlib.md5(open(OUT, "rb").read()).hexdigest())
        ok = (im.size == (CROP[2] - CROP[0], CROP[3] - CROP[1]) and im.mode == "RGBA"
              and a_lt == 0 and a_rt == 255 and a_top == 255 and a_bot == 255)
        print("结果：%s" % ("通过" if ok else "不通过"))
        return 0 if ok else 1
    before = os.path.getsize(OUT) if os.path.exists(OUT) else None
    size, nbytes = build()
    im2 = Image.open(OUT)
    print("落盘 %s  %dx%d  %d 字节 (%.1f KB)%s"
          % (os.path.relpath(OUT, UI), size[0], size[1], nbytes, nbytes / 1024.0,
             "" if before is None else ("  旧 %d 字节" % before)))
    tot = 0
    for f in os.listdir(UI_ASSETS):
        tot += os.path.getsize(os.path.join(UI_ASSETS, f))
    print("assets/ui 合计 %.2f MB / 预算 96.00 MB（余量 %.2f MB）"
          % (tot / 1048576.0, 96.0 - tot / 1048576.0))
    print("md5=%s" % hashlib.md5(open(OUT, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
