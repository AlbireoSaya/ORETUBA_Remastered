# -*- coding: utf-8 -*-
r"""m07 · 取证合成：存/读档屏右下方「说明条 `sv.help` + 编辑键条」簇（`ISSUE-20260926-07`）

输出（`_工作\ISSUE-20260926-07_svhelp\取证\`）：
  · `改前改后_右下1to1.png` —— 区域 x1000..1920 / y760..1080，改前（上）／改后（下）**1:1** 上下拼图
  · `改前改后_右下2x.png`   —— 同区域 **2×** 放大拼图
  · `改前_右下_1to1.png` / `改前_右下_2x.png` —— `--capture` 时的**改前单独**快照（留档）

合成口径（与 `复刻\replica.css` / 引擎 `ui_widget.tjs` 的 `image` 路径一致）：
  · 底图 = 元素 `sv.bg` 的 `asset`（`krkr\assets\ui\x_ui_psv_save_bg.png`），z=2，1:1 满屏；
  · 九宫格件按**真九宫格**贴（`uiWidgetNine` 等价：四角 1:1、四边单轴拉伸、中格双轴拉伸）；
  · `text` 元素按元素矩形 `align=center / valign=middle` 用 msyhbd（= 回退链首项 Microsoft YaHei Bold）
    画 `sample`，颜色取 `@palette.node_locked`（#4A4A56）——引擎绘字的等效近似（非逐字形一致）；
  · 每个受动元素画 1px 外框（改前红／改后绿），并在 y = 页脚带墨迹顶 处画虚线。

幂等：`改前` 一律取自 `原形备份\<屏文件>`（`--capture` 在改动前生成的一次性快照），`改后` 取现盘数据
⇒ **重跑结果一致**；快照缺失时给出显式警告并退回现盘（此时两图相同，不代表已改动）。

用法：
  python m07_composite.py --capture    # 改动**前**跑：快照现盘为「改前」+ 出改前单图
  python m07_composite.py              # 改动后跑：出 1:1 / 2× 改前改后拼图
"""
import sys, os, json, shutil, hashlib
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SCR = os.path.join(BASE, "layout", "screens")
UI = os.path.join(BASE, "krkr", "assets", "ui")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-07_svhelp")
BAK = os.path.join(WORK, "原形备份")
EV = os.path.join(WORK, "取证")
SCREEN = "23_save.json"
CROP = (1000, 760, 1920, 1080)      # 右下观察窗（含簇、页码键右端、页脚带、返回热区）
INK_TOP = 983                       # 底图实测页脚带墨迹顶（见 m07_geom_check.py [0]）
MOVED = ["sv.help", "sv.help_tx", "sv.edit",
         "sv.del_tx", "sv.del", "sv.mod_tx", "sv.mod",
         "sv.mov_tx", "sv.mov", "sv.cpy_tx", "sv.cpy"]
INK = (74, 74, 86)                  # @palette.node_locked
FB = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 26)
FS = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
for p in (BAK, EV):
    os.makedirs(p, exist_ok=True)


def flat(im):
    im = im.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")


def paste_nine(base, asset, x, y, w, h, nine):
    """九宫格贴图（等价 uiWidgetNine；l=t=r=b=0 ⇒ 整图双轴拉伸）。"""
    src = Image.open(os.path.join(UI, asset.split("/")[-1])).convert("RGBA")
    if not nine or not any(nine.values()):
        base.paste(flat(src.resize((w, h), Image.BILINEAR)), (x, y))
        return
    l, t, r, b = nine.get("l", 0), nine.get("t", 0), nine.get("r", 0), nine.get("b", 0)
    sw, sh = src.size
    for (sx, sy, sw_, sh_), (dx, dy, dw, dh) in (
            ((0, 0, l, t), (x, y, l, t)),
            ((sw - r, 0, r, t), (x + w - r, y, r, t)),
            ((0, sh - b, l, b), (x, y + h - b, l, b)),
            ((sw - r, sh - b, r, b), (x + w - r, y + h - b, r, b)),
            ((l, 0, sw - l - r, t), (x + l, y, w - l - r, t)),
            ((l, sh - b, sw - l - r, b), (x + l, y + h - b, w - l - r, b)),
            ((0, t, l, sh - t - b), (x, y + t, l, h - t - b)),
            ((sw - r, t, r, sh - t - b), (x + w - r, y + t, r, h - t - b)),
            ((l, t, sw - l - r, sh - t - b), (x + l, y + t, w - l - r, h - t - b)),
    ):
        if sw_ <= 0 or sh_ <= 0 or dw <= 0 or dh <= 0:
            continue
        base.paste(flat(src.crop((sx, sy, sx + sw_, sy + sh_)).resize((dw, dh), Image.BILINEAR)), (dx, dy))


def composite(scr):
    els = {e["id"]: e for e in scr["elements"]}
    img = flat(Image.open(os.path.join(UI, els["sv.bg"]["asset"].split("/")[-1])))
    for eid in ("sv.edit", "sv.help"):                     # z20 底条（先画）
        e = els[eid]
        paste_nine(img, e["asset"], e["x"], e["y"], e["w"], e["h"], e.get("nine"))
    d = ImageDraw.Draw(img)
    for eid in ("sv.help_tx", "sv.del_tx", "sv.mod_tx", "sv.mov_tx", "sv.cpy_tx"):
        e = els[eid]
        f = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", e["font"]["size"])
        tw = d.textlength(e["sample"], font=f)
        th = e["font"]["size"]
        d.text((e["x"] + (e["w"] - tw) / 2.0, e["y"] + (e["h"] - th) / 2.0 - 2), e["sample"], font=f, fill=INK)
    return img


def outline(img, scr, color):
    """在**整幅画布**上画框与页脚带虚线（必须先画再裁剪，否则坐标全错）。"""
    els = {e["id"]: e for e in scr["elements"]}
    d = ImageDraw.Draw(img)
    for eid in MOVED:
        e = els[eid]
        d.rectangle([e["x"], e["y"], e["x"] + e["w"] - 1, e["y"] + e["h"] - 1], outline=color, width=1)
    # 页脚带墨迹顶（虚线）
    x0, _, x1, _ = CROP
    for x in range(x0, x1, 12):
        d.line([(x, INK_TOP), (x + 6, INK_TOP)], fill=(200, 30, 120), width=1)


def panel(scr, color):
    img = composite(scr)
    outline(img, scr, color)
    return img.crop(CROP)


def geom_line(scr, tag):
    els = {e["id"]: e for e in scr["elements"]}
    return ("%s：sv.help y%d..%d ｜ sv.edit y%d..%d ｜ sv.del|mod|mov|cpy 各 y%d..%d"
            % (tag, els["sv.help"]["y"], els["sv.help"]["y"] + els["sv.help"]["h"],
               els["sv.edit"]["y"], els["sv.edit"]["y"] + els["sv.edit"]["h"],
               els["sv.del"]["y"], els["sv.del"]["y"] + els["sv.del"]["h"]))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:12]


def main():
    capture = "--capture" in sys.argv
    live_p = os.path.join(SCR, SCREEN)
    bak_p = os.path.join(BAK, SCREEN)
    live = json.load(open(live_p, encoding="utf-8"))

    if capture:
        if not os.path.exists(bak_p):
            shutil.copyfile(live_p, bak_p)
        print("[capture] 改前快照 %s（md5 %s）" % (bak_p, md5(bak_p)))
        a = panel(live, (192, 42, 50))
        a.save(os.path.join(EV, "改前_右下_1to1.png"))
        a.resize((a.width * 2, a.height * 2), Image.LANCZOS).save(os.path.join(EV, "改前_右下_2x.png"))
        print("   → 改前_右下_1to1.png / 改前_右下_2x.png", a.size)
        print("   " + geom_line(live, "改前(现盘)"))
        return 0

    if not os.path.exists(bak_p):
        print("!! 改前快照缺失 %s ⇒ 退用现盘（两图将相同，**不代表已改动**）" % bak_p)
        before = live
        stale = True
    else:
        before = json.load(open(bak_p, encoding="utf-8"))
        stale = False
    after = live

    Y0, Y1 = CROP[1], CROP[3]
    A = panel(before, (192, 42, 50))
    B = panel(after, (26, 122, 60))
    HDR, LH, GAP, BOT = 58, 52, 26, 48
    W = CROP[2] - CROP[0]
    H = CROP[3] - CROP[1]
    sh = Image.new("RGB", (W, HDR + (LH + H + GAP) * 2 + BOT), (236, 239, 246))
    d = ImageDraw.Draw(sh)
    d.text((8, 6), "观察窗 x%d..%d ｜ y%d..%d（1:1，画布坐标）" % (CROP[0], CROP[2], Y0, Y1), font=FB, fill=(30, 36, 60))
    d.text((8, 32), "虚线 = 底图实测页脚带墨迹顶 y%d ｜ 红框 = 改前 11 件 ｜ 绿框 = 改后 11 件" % INK_TOP,
           font=FS, fill=(60, 66, 84))
    y = HDR
    d.text((8, y), "改前（ISSUE-20260926-06 落地后的 S=122）", font=FB, fill=(150, 30, 40))
    d.text((8, y + 26), geom_line(before, "改前"), font=FS, fill=(90, 44, 48))
    sh.paste(A, (0, y + LH)); y += LH + H + GAP
    d.text((8, y), "改后（本次 ISSUE-20260926-07：簇上移量 122 → 60）", font=FB, fill=(20, 90, 40))
    d.text((8, y + 26), geom_line(after, "改后"), font=FS, fill=(44, 84, 56))
    sh.paste(B, (0, y + LH))
    y += LH + H
    d.text((8, y + 2), "上：编辑键条在说明条**之上**（与 PSV 原版相反，且编辑条远离页脚）", font=FS, fill=(60, 66, 84))
    d.text((8, y + 22), "下：说明条回到编辑条**之上**（PSB 原版顺序），编辑键条更贴页脚（簇底边 y965 距墨迹顶 y983 = 18px）",
           font=FS, fill=(60, 66, 84))
    p1 = os.path.join(EV, "改前改后_右下1to1.png"); sh.save(p1)
    print("→", p1, sh.size, "(stale=%s)" % stale)
    p2 = os.path.join(EV, "改前改后_右下2x.png")
    sh.resize((sh.width * 2, sh.height * 2), Image.LANCZOS).save(p2)
    print("→", p2)
    # 自证：两图的差异像素数（应为 > 0；为 0 说明没改动或快照=现盘）
    import numpy as np
    n = int((np.abs(np.asarray(A).astype(int) - np.asarray(B).astype(int)).max(axis=2) > 8).sum())
    print("   改前/改后差异像素 = %d（>0 表示确有改动）" % n)
    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
