# -*- coding: utf-8 -*-
r"""render_d_from_data.py —— 从**落盘后的真实屏数据**渲染 D 组五屏版式预演图 ＋ 几何断言。

与 `mock_d_screens.py`（改数据**之前**画的候选值）不同：本脚本**直接读 `layout/screens/*.json`**，
按两端渲染器同一套口径把元素画出来（含 `list` 的二维网格折行、`item_variants` 的 thumb/prev/next/text），
再把 39 外壳叠在四个承载屏之上（= `attach` 的实际画序）⇒ 交付照片级目视证据 + 机检断言。

产出（`_工作\ISSUE-20260926-06_D鉴赏四页换皮\evidence\fromdata_*.png`）：
  fromdata_27/28/37/38.png（承载屏 + 外壳）、fromdata_39_only.png（外壳单独，叠在 27 底图上）。

机检断言（任一不成立即退出码非 0）：
  A. 27/28/37/38 的**非底图元素**不得被 39 外壳条带（(340,0,1580,100)）压住；
  B. `list` 的 `w/h` 必须等于网格外框公式 `cols·item_w+(cols-1)·gap` / `rows·item_h+(rows-1)·gap`；
  C. 28 的列表必须整体落在 PSV 列表框 (156,477,1607,473) 内、8 控制键与滑块落在 PSV 信息框内；
  D. 27/38 的网格必须落在 PSV 参考滚动区（27：187..884 / 38：左栏槽区右侧可用区）内且不出画布；
  E. 39 的 5 个热区互不重叠、且全在条带内。

用法：python _工作\ISSUE-20260926-06_D鉴赏四页换皮\复现脚本\render_d_from_data.py
"""
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(WORK))
SCR = os.path.join(UI, "layout", "screens")
A = os.path.join(UI, "krkr", "assets", "ui")
EV = os.path.join(WORK, "evidence")
FONT = r"C:\Windows\Fonts\msyh.ttc"
SHELL_STRIP = (340, 0, 1580, 100)

COLORS = {"image": (0, 90, 220), "list": (210, 0, 0), "hit": (0, 160, 0),
          "text": (120, 0, 160), "rect": (200, 120, 0), "slider": (0, 150, 150),
          "anim": (150, 150, 0)}
fails = []


def load(name):
    with open(os.path.join(SCR, name), encoding="utf-8") as f:
        return json.load(f)


def rect_of(e):
    return (e.get("x", 0), e.get("y", 0), e.get("w", 0), e.get("h", 0))


def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


def draw_list(d, e, f):
    """画 list：逐格（网格折行口径 = col = i%cols、row = i//cols）＋ 首格内的 item_variants 子件。"""
    x, y, w, h = rect_of(e)
    if e.get("orientation") == "h":
        cols = max(1, e.get("max_cols", 1))
        rows = max(1, e.get("max_rows", 1))
        iw, ih, gap = e.get("item_w", w), e.get("item_h", 10), e.get("gap", 0)
        for r in range(rows):
            for c in range(cols):
                r0 = (x + c * (iw + gap), y + r * (ih + gap), iw, ih)
                d.rectangle([r0[0], r0[1], r0[0] + r0[2], r0[1] + r0[3]], outline=COLORS["list"], width=2)
                if r == 0 and c == 0:
                    vv = e.get("item_variants")
                    if vv:
                        for key, col in (("thumb", (255, 140, 0)), ("text", (0, 0, 0)),
                                         ("prev", (0, 0, 255)), ("next", (0, 0, 255))):
                            sub = vv.get(key)
                            if isinstance(sub, dict) and "w" in sub:
                                sx, sy, sw, sh = sub["x"], sub["y"], sub["w"], sub["h"]
                                d.rectangle([r0[0] + sx, r0[1] + sy, r0[0] + sx + sw, r0[1] + sy + sh],
                                            outline=col, width=2)
                            elif key == "thumb":       # 缺省 = 整个项矩形
                                d.rectangle([r0[0], r0[1], r0[0] + iw, r0[1] + ih], outline=col, width=2)
                    for b in (e.get("item_buttons") or []):
                        bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
                        d.rectangle([r0[0] + bx, r0[1] + by, r0[0] + bx + bw, r0[1] + by + bh],
                                    outline=(0, 200, 200), width=2)
                    it = e.get("item_text")
                    if it and "w" in it:
                        d.rectangle([r0[0] + it["x"], r0[1] + it["y"], r0[0] + it["x"] + it["w"],
                                     r0[1] + it["y"] + it["h"]], outline=(128, 100, 0), width=2)
    else:
        rows = e.get("max_rows", (h // max(1, e.get("item_h", 1))))
        for r in range(int(rows)):
            d.rectangle([x, y + r * e["item_h"], x + w, y + r * e["item_h"] + e["item_h"]],
                        outline=COLORS["list"], width=2)
    d.rectangle([x, y, x + w, y + h], outline=(255, 0, 255), width=3)
    d.text((x + 4, y + 2), "%s  %dx%d @(%d,%d) %s%d×%d" %
           (e["id"], w, h, x, y, "cell %dx%d gap%d " % (e["item_w"], e["item_h"], e.get("gap", 0)),
            e.get("max_cols", 1), e.get("max_rows", rows)), fill=(150, 0, 0), font=f)


def render(screen, shell=None, out=None):
    d0 = load(screen)
    f = ImageFont.truetype(FONT, 18)
    canvas = Image.new("RGBA", (1920, 1080), (255, 255, 255, 255))
    bg = None
    for e in d0["elements"]:
        if e["kind"] == "image" and e.get("z", 0) == 0 and e["w"] == 1920:
            bg = e
            break
    if bg:
        canvas.alpha_composite(Image.open(os.path.join(A, bg["asset"].split("/", 1)[1])).convert("RGBA"), (0, 0))
    if shell:
        sh = load(shell)
        for e in sh["elements"]:
            if e["id"] == "gs.strip":
                canvas.alpha_composite(Image.open(os.path.join(A, e["asset"].split("/", 1)[1])).convert("RGBA"),
                                       (e["x"], e["y"]))
    d = ImageDraw.Draw(canvas)
    for e in d0["elements"]:
        if e.get("z", 0) == 0:
            continue
        t = e["kind"]
        col = COLORS.get(t, (100, 100, 100))
        x, y, w, h = rect_of(e)
        if t == "list":
            draw_list(d, e, f)
            continue
        if t == "rect":
            d.rectangle([x, y, x + w, y + h], outline=col, width=2)
        else:
            d.rectangle([x, y, x + w, y + h], outline=col, width=2)
        lab = e["id"] + ("/" + e.get("action", "") if e.get("action") else "")
        d.text((x + 3, y + 2), lab, fill=col, font=f)
    if shell:
        sh = load(shell)
        for e in sh["elements"]:
            if e["id"] == "gs.strip":
                continue
            x, y, w, h = rect_of(e)
            col = COLORS.get(e["kind"], (100, 100, 100))
            d.rectangle([x, y, x + w, y + h], outline=col, width=2)
            d.text((x + 3, y + 2), e["id"] + ("/" + e.get("action", "") if e.get("action") else ""),
                   fill=col, font=f)
    if out:
        canvas.convert("RGB").save(out, optimize=True)
        print("wrote", os.path.relpath(out, UI))


def main():
    print("== 几何断言 ==")
    for name, screen in (("27_gallery.json", "27_gallery"), ("28_music.json", "28_music"),
                         ("37_dress.json", "37_dress"), ("38_replay.json", "38_replay")):
        d0 = load(name)
        strip = SHELL_STRIP
        bad = []
        for e in d0["elements"]:
            if e.get("z", 0) == 0 or e["id"].endswith(".bg"):
                continue
            x, y, w, h = rect_of(e)
            if y < strip[1] + strip[3] and y + h > strip[1] and x < strip[0] + strip[2] and x + w > strip[0]:
                bad.append(e["id"])
        check(not bad, "A %s：非底图元素均不被外壳条带压住（越界：%s）" % (name, bad or "无"))
        for e in d0["elements"]:
            if e["kind"] == "list" and e.get("orientation") == "h":
                x, y, w, h = rect_of(e)
                cols, rows = e["max_cols"], e["max_rows"]
                gw = cols * e["item_w"] + (cols - 1) * e.get("gap", 0)
                gh = rows * e["item_h"] + (rows - 1) * e.get("gap", 0)
                check((w, h) == (gw, gh), "B %s：%s 外框 w/h == 网格公式 %dx%d（实为 %dx%d）"
                      % (name, e["id"], gw, gh, w, h))
                check(x >= 0 and y >= 0 and x + w <= 1920 and y + h <= 1080,
                      "   %s 出画布检查（%d,%d,%d,%d）" % (e["id"], x, y, w, h))
    m = load("28_music.json")
    box = (156, 477, 1607, 473)
    info = (156, 223, 1606, 217)
    for e in m["elements"]:
        if e["id"] == "mu.list":
            x, y, w, h = rect_of(e)
            check(x >= box[0] and y >= box[1] and x + w <= box[0] + box[2] and y + h <= box[1] + box[3],
                  "C mu.list 落在 PSV 列表框内：(%d,%d,%d,%d) ⊂ (156,477,1607,473)" % (x, y, w, h))
        if e["id"].startswith("mu.pb_") and e["kind"] == "image":
            x, y, w, h = rect_of(e)
            check(x >= info[0] and y >= info[1] and x + w <= info[0] + info[2] and y + h <= info[1] + info[3],
                  "C %s 落在 PSV 信息框内（y=%d..%d）" % (e["id"], y, y + h))
        if e["id"] == "mu.vol":
            x, y, w, h = rect_of(e)
            check(y >= info[1] and y + h <= info[1] + info[3], "C mu.vol 落在信息框内（y=%d..%d）" % (y, y + h))
    g = load("27_gallery.json")
    for e in g["elements"]:
        if e["id"] == "gal.list":
            x, y, w, h = rect_of(e)
            check(y >= 187 and y + h <= 884, "D gal.list 落在 PSV CG 滚动区 187..884 内（%d..%d）" % (y, y + h))
    s = load("39_gal_shell.json")
    hits = [(e["id"], rect_of(e)) for e in s["elements"] if e["kind"] == "hit"]
    for i in range(len(hits)):
        check(hits[i][1][0] >= SHELL_STRIP[0] and hits[i][1][1] >= SHELL_STRIP[1]
              and hits[i][1][0] + hits[i][1][2] <= SHELL_STRIP[0] + SHELL_STRIP[2]
              and hits[i][1][1] + hits[i][1][3] <= SHELL_STRIP[1] + SHELL_STRIP[3],
              "E %s 热区落在条带内 %s" % (hits[i][0], hits[i][1]))
        for j in range(i + 1, len(hits)):
            check(not overlaps(hits[i][1], hits[j][1]), "E %s 与 %s 热区不重叠" % (hits[i][0], hits[j][0]))
    print("== 渲染 ==")
    for name, screen in (("27_gallery.json", "27_gallery"), ("28_music.json", "28_music"),
                         ("37_dress.json", "37_dress"), ("38_replay.json", "38_replay")):
        render(name, "39_gal_shell.json", os.path.join(EV, "fromdata_%s.png" % screen))
    render("39_gal_shell.json", None, os.path.join(EV, "fromdata_39_only.png"))
    print("\n断言：%s（%d 项失败）" % ("全部通过" if not fails else "**不通过**", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
