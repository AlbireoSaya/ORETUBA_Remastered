# -*- coding: utf-8 -*-
r"""ISSUE-20260927-02 · F 组 · 取证图生成（幂等；只写本证据目录的 `取证/`）。

产出：
  ① `改前_四行左段_2x.png` / `改后_四行左段_2x.png`
     —— 每块左段（画布 x169..640、块内 y0..64）纵向叠放，2× 最近邻。按钮簇 + 文案首行都在内。
  ② `对照_块内视觉中线_改前改后_2x.png`
     —— 4 行 × 2 列（改前 | 改后），每格同①的左段 2×，并叠三条参考线：
        **红** = 文案首行**墨迹**中线（实测：窗口内深色像素首末的中点）
        **蓝** = 按钮**胶囊可见体**中线（口径：元素框顶 + 素材 alpha≥128 行 6..23 的中点 ⇒ +14.5px）
        **绿** = 按钮**标签墨迹**中线（实测：按钮矩形内深色像素首末的中点）
     三条线的**画布 y 值写在图上**（左上角小字），便于逐格复核。

用法（在 UI 组根目录跑）：python _工作\ISSUE-20260927-02_backlog收尾\复现脚本\make_crops.py
"""
import os
import json

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.abspath(os.path.join(HERE, "..", "取证"))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")
ASSUI = os.path.join(UI, "krkr", "assets", "ui")

X0, XW, YH = 169, 640, 64        # 取证窗：画布 x169..640、块内 y0..64
ZOOM = 2


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def spec():
    d = json.load(open(SCREEN, encoding="utf-8"))
    l = [e for e in d["elements"] if e["id"] == "bl.list"][0]
    bj = [b for b in l["item_buttons"] if b["key"] == "jump"][0]
    return l, bj


def cap_offset(bj):
    """胶囊可见体中线相对元素框顶的偏移（素材 alpha≥128 行首末中点的行号 + 0.5）"""
    im = Image.open(os.path.join(ASSUI, "x_ui_jump_off.png")).convert("RGBA")
    a = im.getchannel("A").load()
    W, H = im.size
    rows = [y for y in range(H) if max(a[x, y] for x in range(W)) >= 128]
    return (rows[0] + rows[-1]) / 2.0


def lines_for(px, lst, bj, i, pitch, btn_y):
    ry = lst["y"] + i * pitch
    it = lst["item_text"]
    ty0, ty1 = ry + it["y"], ry + it["y"] + 41
    tx0, tx1 = lst["x"] + it["x"], lst["x"] + it["x"] + it["w"] - 1
    wy0 = ty0 - 5
    vals = sorted(lum(px[x, y]) for y in range(wy0, ty1 + 1, 2) for x in range(tx0, tx1 + 1, 3))
    thr = vals[len(vals) // 2] - 60
    rows = [y for y in range(wy0, ty1 + 1) if sum(1 for x in range(tx0, tx1 + 1) if lum(px[x, y]) < thr) >= 2]
    text_mid = (rows[0] + rows[-1]) / 2.0
    jy = ry + btn_y                  # ★ 必须显式给「该图当时」的按钮 y（改前 26 / 改后 18）
    cap_mid = jy + cap_offset(bj)
    jx0, jx1 = lst["x"] + bj["x"], lst["x"] + bj["x"] + bj["w"] - 1
    lrows = [y for y in range(jy - 5, jy + bj["h"] + 5)
             if sum(1 for x in range(jx0, jx1 + 1) if lum(px[x, y]) < 175) >= 1]
    lab_mid = (lrows[0] + lrows[-1]) / 2.0
    return text_mid, cap_mid, lab_mid


def strip(src, lst, bj, btn_y):
    im = Image.open(src).convert("RGB")
    px = im.load()
    pitch = lst["item_h"] + lst["gap"]
    out = Image.new("RGB", ((XW - X0) * ZOOM, (YH * 4) * ZOOM), (255, 255, 255))
    ms = []
    for i in range(4):
        ry = lst["y"] + i * pitch
        p = im.crop((X0, ry, XW, ry + YH))
        out.paste(p.resize((p.width * ZOOM, p.height * ZOOM), Image.NEAREST),
                  (0, i * YH * ZOOM))
        ms.append(lines_for(px, lst, bj, i, pitch, btn_y))
    return out, ms


def annotate(im, lst, bj, ms, dy0=0):
    d = ImageDraw.Draw(im)
    pitch = lst["item_h"] + lst["gap"]
    for i, (t, c, l) in enumerate(ms):
        ry = lst["y"] + i * pitch
        for y, col in ((t, (220, 30, 30)), (c, (30, 90, 230)), (l, (20, 150, 60))):
            yy = int(round((y - ry) * ZOOM))
            d.line([(0, yy), (im.width, yy)], fill=col)
        d.text((4, i * YH * ZOOM + 4), "块%d  文案墨迹 %.1f ｜ 胶囊体 %.1f ｜ 标签墨迹 %.1f"
               % (i, t, c, l), fill=(0, 0, 0))
    return im


def main():
    lst, bj = spec()
    a_path = os.path.join(EV, "改前", "shot_29_backlog.png")
    b_path = os.path.join(EV, "改后", "shot_29_backlog.png")
    OLDY, NEWY = 26, 18          # 改前 / 改后 的 jump.y（replay 为 18 / 10，同步位移 8px）
    a_im, a_ms = strip(a_path, lst, bj, OLDY)
    b_im, b_ms = strip(b_path, lst, bj, NEWY)
    a_im.save(os.path.join(EV, "改前_四行左段_2x.png"))
    b_im.save(os.path.join(EV, "改后_四行左段_2x.png"))
    # 对照图：4 行 × 2 列
    gap = 8
    out = Image.new("RGB", (a_im.width * 2 + gap, a_im.height + 22), (245, 245, 248))
    out.paste(a_im, (0, 22))
    out.paste(b_im, (a_im.width + gap, 22))
    annotate(out.crop((0, 22, a_im.width, out.height)), lst, bj, a_ms)
    d = ImageDraw.Draw(out)
    d.text((6, 6), "改前（jump 28,26 / replay 154,18）", fill=(0, 0, 0))
    d.text((a_im.width + gap + 6, 6), "改后（jump 15,18 / replay 141,10）", fill=(0, 0, 0))
    out.save(os.path.join(EV, "对照_块内视觉中线_改前改后_2x.png"))
    for tag, ms in (("改前", a_ms), ("改后", b_ms)):
        print("【%s】块0..3  文案墨迹中线 / 胶囊体中线 / 标签墨迹中线：" % tag)
        for i, (t, c, l) in enumerate(ms):
            print("   块%d  %.1f  %.1f  %.1f   （文案−胶囊 %+.1f）" % (i, t, c, l, t - c))
    print("saved:", os.path.relpath(os.path.join(EV, "对照_块内视觉中线_改前改后_2x.png"), UI))


if __name__ == "__main__":
    main()
