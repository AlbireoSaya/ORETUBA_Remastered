# -*- coding: utf-8 -*-
r"""M06 · **两端一致**证据（冻结书 §4 第 4 条）：引擎巡演导出的 PNG ↔ HTML 无头截图。

■ 做法
  引擎侧：私有巡演目录 `临时\ui_run_pagescope\runtime\savedata\shot_29_backlog.png`
          （= 进入回想屏、无合成指针的那一帧；shot_29 与巡演末尾的 shot_45 逐字节相同，
           说明该帧就是「无指针基线」）。
  HTML 侧：`证据\m06_html_backlog.png`（`w4_html_config_shots.py --shot "?screen=backlog"`，
           1920×1080 画布，与引擎同为左上原点）。
  比对：取 `bl.list` 及其按钮所在的**列表区**（x 208..1557、y 108..940）逐像素求差，
       产三张证据图：并排（引擎左 / HTML 右）、放大按钮列、差值热力图。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_two_ends_compare.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE))
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))   # UI组 -> <game> -> 工程 -> wt-qbicons
ENGINE = os.path.join(WT, "临时", "ui_run_pagescope", "runtime", "savedata", "shot_29_backlog.png")
EVID = os.path.join(ISSUE, "证据")
HTML = os.path.join(EVID, "m06_html_backlog.png")

# 列表区（`bl.list` x208 y108 w1349，可见 4 块 ⇒ 栈底 928）
BOX = (208, 108, 208 + 1349, 108 + 820)
# 按钮列放大区（左栏：跳转 x28..122、replay x154..198 ⇒ 画布 x236..406）
BTN_BOX = (236, 108, 406, 928)


def load(p):
    from PIL import Image
    im = Image.open(p).convert("RGB")
    if im.size != (1920, 1080):
        # 引擎导图可能带 alpha/不同尺寸：统一取左上 1920×1080
        im = im.crop((0, 0, min(1920, im.size[0]), min(1080, im.size[1])))
    return im


def main():
    from PIL import Image, ImageChops, ImageFilter
    if not os.path.exists(ENGINE):
        print("缺引擎导图：", ENGINE)
        return 2
    if not os.path.exists(HTML):
        print("缺 HTML 截图：", HTML)
        return 2
    a = load(ENGINE).crop(BOX)
    b = load(HTML).crop(BOX)
    if a.size != b.size:
        print("尺寸不一致：引擎 %s vs HTML %s" % (a.size, b.size))
        return 1

    diff = ImageChops.difference(a, b).convert("L")
    px = diff.load()
    w, h = diff.size
    bad = 0
    tot = 0
    for i in range(0, w):
        for j in range(0, h):
            tot += 1
            if px[i, j] > 8:
                bad += 1
    print("列表区 %dx%d：严格逐像素 |Δ|>8 = %d / %d = %.2f%%（含字形/边缘抗锯齿，两端光栅器不同）"
          % (w, h, bad, tot, 100.0 * bad / tot))

    # ---- 结构一致性（对**墨迹掩码**比对，容忍 ±2px 位移）----
    #   墨迹 = 明显比该图自身背景暗/亮的像素；两端掩码互相在 2px 内能找到对应 ⇒ 结构一致。
    #   这一步排除字形抗锯齿与九宫格边缘插值，只回答「按钮/文案/卡片边界在不在同一处」。
    def ink(im):
        g = im.convert("L")
        # 以「与中位数灰度差 > 24」当墨迹（卡片底 vs 文字/按钮）
        hist = g.histogram()
        n = sum(hist)
        acc = 0
        med = 128
        for v in range(256):
            acc += hist[v]
            if acc >= n / 2:
                med = v
                break
        return g.point(lambda v: 255 if abs(v - med) > 24 else 0)

    ia = ink(a)
    ib = ink(b)
    # 各掩码向外膨胀 2px 再求交：只要一端有墨、另一端 2px 内有墨即算命中
    da = ia.filter(ImageFilter.MaxFilter(5))
    db = ib.filter(ImageFilter.MaxFilter(5))
    pa, pb, pda, pdb = ia.load(), ib.load(), da.load(), db.load()
    only_a = only_b = both = 0
    for i in range(w):
        for j in range(h):
            va, vb = pa[i, j] > 0, pb[i, j] > 0
            if va and vb:
                both += 1
            elif va and pdb[i, j] == 0:
                only_a += 1
            elif vb and pda[i, j] == 0:
                only_b += 1
    union = both + only_a + only_b
    agree = 100.0 * both / union if union else 100.0
    print("结构（墨迹掩码，容忍 ±2px）：共有墨迹 %d ｜ 仅引擎 %d ｜ 仅 HTML %d ⇒ 一致率 %.2f%%"
          % (both, only_a, only_b, agree))
    print("  说明：一致率 <100%% 的余量来自两端字体光栅（字形粗细/抗锯齿）与九宫格边缘插值的像素级差异，")
    print("        几何（按钮矩形、文案内缩与折行行数）由两端各自对**同一份数据**复算并已机检：")
    print("        引擎 = 巡演 ★M06BTN★（中心坐标 + 命中令牌），HTML = 自检 ⑳b（几何 = 数据局部矩形）。")

    # ① 并排
    side = Image.new("RGB", (w * 2 + 8, h), (20, 20, 20))
    side.paste(a, (0, 0))
    side.paste(b, (w + 8, 0))
    side.save(os.path.join(EVID, "m06_two_ends_backlog_side.png"))

    # ② 按钮列放大（左 引擎 / 右 HTML）
    ab = load(ENGINE).crop(BTN_BOX)
    bb = load(HTML).crop(BTN_BOX)
    Z = 3
    ab = ab.resize((ab.size[0] * Z, ab.size[1] * Z), Image.NEAREST)
    bb = bb.resize((bb.size[0] * Z, bb.size[1] * Z), Image.NEAREST)
    zs = Image.new("RGB", (ab.size[0] * 2 + 8, ab.size[1]), (20, 20, 20))
    zs.paste(ab, (0, 0))
    zs.paste(bb, (ab.size[0] + 8, 0))
    zs.save(os.path.join(EVID, "m06_two_ends_buttons_zoom.png"))

    # ③ 差值热力图
    hm = Image.new("RGB", (w, h))
    hp = hm.load()
    for i in range(w):
        for j in range(h):
            d = px[i, j]
            hp[i, j] = (255, 0, 0) if d > 8 else (d, d, d)
    hm.save(os.path.join(EVID, "m06_two_ends_diff.png"))
    print("证据图：m06_two_ends_backlog_side.png / m06_two_ends_buttons_zoom.png / m06_two_ends_diff.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())