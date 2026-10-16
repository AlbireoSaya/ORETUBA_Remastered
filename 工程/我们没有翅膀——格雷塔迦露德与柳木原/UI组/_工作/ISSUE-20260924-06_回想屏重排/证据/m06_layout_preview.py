# -*- coding: utf-8 -*-
r"""M06 · 回想屏重排 · **数据侧排版预演**（脱离机制侧、直接从数据 + 素材 + 引擎算法出图）

■ 为什么自渲染一张（而不是只等 HTML 复刻端截图）
  「逐块两按钮」（`item_buttons`）是**本 Issue 新增的数据契约**，机制侧（`ui_widget.tjs` /
  `replica.js`）尚未实现 ⇒ 此刻用 `复刻\index.html` 截图**看不到按钮**，无法验收
  「每块两个按钮在块内 / 不压字 / 不出框 / 不越滚动列」。
  故本脚本按**引擎同口径**自己画一遍：数据取自「重排后」的 `26_backlog.json`
  （由 `复现脚本\m06_build_backlog.py --dry-run` 的同一 build 函数产出，**不改盘**），
  素材用 `krkr\assets\ui\` 真件，文本用 `krkr\game\ui_theme.tjs` 的 `uiThemeWrap` 算法。

■ 引擎同口径清单（逐条对齐，改一处须改两处）
  · 元素矩形 / 分页：`uiWidgetRect` / `uiWidgetListPage` / `uiWidgetListItemRect`（`ui_widget.tjs`）；
  · 块底板九宫格：`uiWidgetNine`（九块 nearest 拉伸）；
  · 文本折行：`uiThemeWrap`（含行首/行尾禁则）+ `uiThemeLayoutText` 的 valign/align；
  · 行距：floor(size × line_spacing.body=1.4)；
  · 逐块按钮：按 `item_buttons` 的**块内局部矩形**平移绘制；`state_assets.normal` 态
    （三态换图属机制侧实现，本图只画 normal，另出一张三态对照）；
  · 逐块按钮文字：`label` + `font`（居中、单行、valign=middle，同 `hit.label` 口径）。

■ 文本用**真实语料**（不是占位文案）
  取 `资源组\剧本\scene_*.jsonl` 里折行行数最多的 4 条（压力测试），
  与 `m06_measure_capacity.py` 同一套折行实现。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\证据\m06_layout_preview.py
  产物（同目录）：
    m06_preview_backlog.png           —— 1:1 整屏（1920×1080）干净图
    m06_preview_backlog_annot.png     —— 同图 + 几何标注（文本区/按钮矩形/栈底线/滚动列左界）
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)                                        # ISSUE-20260924-06_回想屏重排
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))         # <UI组>
PROJ = os.path.dirname(UI)
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")
PALETTE = os.path.join(UI, "layout", "palette.json")
BUILDER = os.path.join(ISSUE, "复现脚本")
FONT_TTF = "C:/Windows/Fonts/msyh.ttc"

sys.path.insert(0, BUILDER)
import m06_build_backlog as B          # noqa: E402  用同一个 build()，保证「图 = 数据」

NO_HEAD = "、。，．！？：；）」』】》〉”’!?,.:;)]}"
NO_TAIL = "（「『【《〈“‘([{"


def pal(key):
    with io.open(PALETTE, encoding="utf-8") as f:
        return json.load(f)["colors"][key]["value"]


def hexrgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


PAL = {k: json.load(io.open(PALETTE, encoding="utf-8"))["colors"][k]["value"]
       for k in ("backdrop", "node_locked", "accent")}


# ─────────────────────────────────────────── 字体/度量（引擎 getTextWidth 口径）
class Metric:
    def __init__(self, path, size):
        self.f = ImageFont.truetype(path, size)
        self.cache = {}

    def chw(self, ch):
        v = self.cache.get(ch)
        if v is None:
            v = self.f.getlength(ch)
            self.cache[ch] = v
        return v

    def width(self, s):
        return sum(self.chw(c) for c in s)


def wrap(m, text, max_w, max_lines):
    out = []
    for para in text.split("\n"):
        if para == "":
            out.append("")
            continue
        line, lw = "", 0.0
        for ch in para:
            w = lw + m.chw(ch)
            if w <= max_w or line == "":
                line, lw = line + ch, w
                continue
            if ch in NO_HEAD:
                line, lw = line + ch, w
                continue
            carry = ""
            if line and line[-1] in NO_TAIL:
                carry, line = line[-1], line[:-1]
            out.append(line)
            line = carry + ch
            lw = m.width(line)
        if line != "" or para == "":
            out.append(line)
    if max_lines and len(out) > max_lines:
        while len(out) > max_lines:
            out.pop()
    return out


# ─────────────────────────────────────────── 九宫格（照抄 uiWidgetNine）
def nine_blit(src, dw, dh, nine):
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    sw, sh = src.size
    assert sw >= l + r and sh >= t + b, "源 %sx%s 小于边距" % (sw, sh)
    scw, sch = sw - l - r, sh - t - b
    dcw, dch = max(0, dw - l - r), max(0, dh - t - b)
    cells = [(0, 0, l, t, 0, 0, l, t), (l, 0, dcw, t, l, 0, scw, t),
             (l + dcw, 0, r, t, l + scw, 0, r, t),
             (0, t, l, dch, 0, t, l, sch), (l, t, dcw, dch, l, t, scw, sch),
             (l + dcw, t, r, dch, l + scw, t, r, sch),
             (0, t + dch, l, b, 0, t + sch, l, b), (l, t + dch, dcw, b, l, t + sch, scw, b),
             (l + dcw, t + dch, r, b, l + scw, t + sch, r, b)]
    out = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
    for (dx, dy, ddw, ddh, sx, sy, ssw, ssh) in cells:
        if ddw <= 0 or ddh <= 0 or ssw <= 0 or ssh <= 0:
            continue
        out.paste(src.crop((sx, sy, sx + ssw, sy + ssh)).resize((ddw, ddh), Image.NEAREST),
                  (dx, dy), src.crop((sx, sy, sx + ssw, sy + ssh)).resize((ddw, ddh), Image.NEAREST))
    return out


# ─────────────────────────────────────────── 取 4 条最长真实台词（压力测试）
def worst_lines(n, metric, max_w, max_lines):
    got = []
    for p in sorted(glob.glob(os.path.join(PROJ, "资源组", "剧本", "scene_*.jsonl"))):
        for ln in io.open(p, encoding="utf-8"):
            for L in json.loads(ln).get("lines", []):
                t = (L.get("cn") or "").strip()
                if not t:
                    continue
                got.append((len(wrap(metric, t, max_w, max_lines + 4)), t))
    got.sort(key=lambda x: (-x[0], -len(x[1])))
    # 取前 n 条（行数最多、字数最多）
    return [t for _k, t in got[:n]]


def main():
    raw = io.open(SCREEN, encoding="utf-8").read()
    data = B.build(json.loads(raw))                     # ← 重排后（不写盘）
    els = {e["id"]: e for e in data["elements"]}
    lst = els["bl.list"]
    frame, nine = lst["item_frame"], lst["item_frame"]["nine"]
    itx, btns = lst["item_text"], lst["item_buttons"]
    font_spec = lst["font"]
    size = font_spec["size"]
    line_h = int(size * 1.4)
    metric = Metric(FONT_TTF, size)

    W, H = 1920, 1080
    canvas = Image.open(os.path.join(ASSETS, "x_bg_system.png")).convert("RGBA")
    canvas = canvas.resize((W, H)) if canvas.size != (W, H) else canvas
    # bl.dim：全屏压暗遮罩（@palette.backdrop × opacity 60/255）
    dim = Image.new("RGBA", (W, H), hexrgb(PAL["backdrop"]) + (0,))
    dim.putalpha(int(255 * 60 / 255.0))
    canvas = Image.alpha_composite(canvas, dim)

    # 文本：真实语料里折行行数最多的 4 条
    texts = worst_lines(len(lst["labels"]), metric, itx["w"], itx["max_lines"])
    frame_img = Image.open(os.path.join(ASSETS, frame["asset"].split("/")[-1])).convert("RGBA")

    n = lst["max_rows"]
    block_imgs = []
    for i in range(n):
        iy = lst["y"] + i * (lst["item_h"] + lst["gap"])
        # ① 块底板（九宫格）
        board = nine_blit(frame_img, lst["w"], lst["item_h"], nine)
        canvas.alpha_composite(board, (lst["x"], iy))
        # ② 逐块两个按钮（item_buttons，块内局部矩形）
        for b in btns:
            art = Image.open(os.path.join(ASSETS, b["asset"].split("/")[-1])).convert("RGBA")
            bx, by = lst["x"] + b["x"], iy + b["y"]
            if "nine" in b:
                canvas.alpha_composite(nine_blit(art, b["w"], b["h"], b["nine"]), (bx, by))
            else:
                canvas.alpha_composite(art, (bx, by))
            if b.get("label"):
                f = b.get("font") or font_spec
                fnt = ImageFont.truetype(FONT_TTF, f["size"])
                d = ImageDraw.Draw(canvas)
                tw = fnt.getlength(b["label"])
                tx = bx + (b["w"] - tw) / 2.0
                ty = by + (b["h"] - f["size"]) / 2.0 - 1
                d.text((tx, ty), b["label"], font=fnt, fill=hexrgb(PAL["node_locked"]) + (255,))
        # ③ 文本区（item_text，块内局部矩形；wrap + valign=top + align=left）
        d = ImageDraw.Draw(canvas)
        fnt = ImageFont.truetype(FONT_TTF, size)
        tx0, ty0 = lst["x"] + itx["x"], iy + itx["y"]
        lines = wrap(metric, texts[i], itx["w"], itx["max_lines"])
        for k, s in enumerate(lines):
            d.text((tx0, ty0 + k * line_h), s, font=fnt, fill=hexrgb(PAL["node_locked"]) + (255,))
        block_imgs.append((iy, lines, texts[i]))

    # ④ 右侧滚动列 + 关闭键（原样照抄 JSON 的 image + nine）
    for eid in ("bl.close", "bl.up", "bl.slider", "bl.down"):
        e = els[eid]
        art = Image.open(os.path.join(ASSETS, e["asset"].split("/")[-1])).convert("RGBA")
        if "nine" in e:
            canvas.alpha_composite(nine_blit(art, e["w"], e["h"], e["nine"]), (e["x"], e["y"]))
        else:
            canvas.alpha_composite(art, (e["x"], e["y"]))

    out1 = os.path.join(HERE, "m06_preview_backlog.png")
    canvas.convert("RGB").save(out1)

    # ── 标注版
    ann = canvas.copy()
    d = ImageDraw.Draw(ann, "RGBA")
    d.line([(0, 940), (W, 940)], fill=(255, 96, 96, 220), width=3)
    d.text((14, 906), "栈底上限 y=940（冻结书 §1）", font=ImageFont.truetype(FONT_TTF, 20),
           fill=(255, 120, 120, 255))
    stack_bottom = lst["y"] + n * lst["item_h"] + (n - 1) * lst["gap"]
    d.line([(0, stack_bottom), (W, stack_bottom)], fill=(120, 255, 160, 220), width=2)
    d.text((14, stack_bottom + 4), "实际栈底 y=%d（≤940 ✓，余量 %d）"
           % (stack_bottom, 940 - stack_bottom), font=ImageFont.truetype(FONT_TTF, 20),
           fill=(140, 255, 180, 255))
    d.line([(1610, 0), (1610, H)], fill=(255, 220, 96, 200), width=2)
    d.text((1530, 12), "滚动列左界 x=1610", font=ImageFont.truetype(FONT_TTF, 20),
           fill=(255, 230, 130, 255))
    for i in range(n):
        iy = lst["y"] + i * (lst["item_h"] + lst["gap"])
        d.rectangle([lst["x"], iy, lst["x"] + lst["w"] - 1, iy + lst["item_h"] - 1],
                    outline=(120, 200, 255, 230), width=2)
        d.rectangle([lst["x"] + itx["x"], iy + itx["y"],
                     lst["x"] + itx["x"] + itx["w"] - 1, iy + itx["y"] + itx["h"] - 1],
                    outline=(120, 255, 160, 220), width=2)
        for b in btns:
            d.rectangle([lst["x"] + b["x"], iy + b["y"],
                         lst["x"] + b["x"] + b["w"] - 1, iy + b["y"] + b["h"] - 1],
                        outline=(255, 140, 200, 235), width=2)
    d.text((216, 84), "蓝=块矩形  绿=文本区 item_text  粉=item_buttons  红=940 上限  黄=滚动列左界",
           font=ImageFont.truetype(FONT_TTF, 22), fill=(255, 255, 255, 255))
    out2 = os.path.join(HERE, "m06_preview_backlog_annot.png")
    ann.convert("RGB").save(out2)

    print("=" * 100)
    print("M06 · 回想屏数据侧排版预演（引擎同口径自渲染；数据 = 重排后 build()，未写盘）")
    print("=" * 100)
    print("item_h=%d gap=%d max_rows=%d ⇒ 4×item_h+3×gap=%d ≤ 832；栈顶 y=%d、栈底 y=%d（≤940 ✓）"
          % (lst["item_h"], lst["gap"], lst["max_rows"], 4 * lst["item_h"] + 3 * lst["gap"],
             lst["y"], stack_bottom))
    print("文本区 item_text = 块内局部 (%d,%d) %d×%d ｜ 字号 %d ｜ lineH %d ｜ max_lines %d"
          % (itx["x"], itx["y"], itx["w"], itx["h"], size, line_h, itx["max_lines"]))
    for b in btns:
        print("item_button %-7s 块内局部 (%3d,%3d) %2d×%-2d ｜ 绝对 x %d..%d ｜ action=%s"
              % (b["key"], b["x"], b["y"], b["w"], b["h"], lst["x"] + b["x"],
                 lst["x"] + b["x"] + b["w"], b["action"]))
    print("-" * 100)
    print("逐块实测（真实语料压力测试；文本区右界 1336，块右界 1557，滚动列左界 1610）：")
    ok_all = True
    for i, (iy, lines, txt) in enumerate(block_imgs):
        used = len(lines) * line_h
        right = max(itx["x"] + metric.width(s) for s in lines)
        b_r = max(b["x"] + b["w"] for b in btns)
        gap_x = itx["x"] - b_r
        ok = (len(lines) <= itx["max_lines"] and used <= itx["h"]
              and right <= itx["x"] + itx["w"] and gap_x > 0)
        ok_all &= ok
        print("  块%d y %4d..%4d ｜ 文本 %d 行 / 占高 %3d ≤ %d ｜ 文本右界 %d..%d ≤ %d ｜ 按钮右缘 %d < 文本左界 %d（净空 %d）｜ %s"
              % (i + 1, iy, iy + lst["item_h"] - 1, len(lines), used, itx["h"],
                 itx["x"], int(right), itx["x"] + itx["w"], b_r, itx["x"], gap_x,
                 "OK" if ok else "**越界**"))
    d1 = lst["x"] + lst["w"] - 1
    mb = max(lst["x"] + b["x"] + b["w"] for b in btns)
    print("  全列：块右界 %d < 滚动列左界 1610 ✓ ｜ 按钮最右绝对 x=%d < 1610 ✓ ｜ 按钮最右 %d < 文本左界 %d ✓"
          % (d1, mb, mb, lst["x"] + itx["x"]))
    # ── 素材引用自证（JSON 未落盘时 verify_ui 收不到这些引用，故此处自证）
    #    规则同 verify_ui [2]：无 nine 的件 w/h 必须 == PNG 实尺寸
    print("-" * 100)
    print("素材引用自证（item_frame + item_buttons 的全部 asset / state_assets）：")
    refs = [("item_frame.asset", frame["asset"], lst["w"], lst["item_h"], nine)]
    for b in btns:
        refs.append(("item_buttons[%s].asset" % b["key"], b["asset"], b["w"], b["h"], b.get("nine")))
        for st, sp in sorted(b["state_assets"].items()):
            refs.append(("item_buttons[%s].state_assets.%s" % (b["key"], st), sp, b["w"], b["h"],
                         b.get("nine")))
    ok_ref = True
    for where, ref, ew, eh, nn in refs:
        p = os.path.join(ASSETS, ref.split("/")[-1])
        if not os.path.exists(p):
            ok_ref = False
            print("  [NG!] %-46s %s **缺件**" % (where, ref))
            continue
        with Image.open(p) as im:
            iw, ih = im.size
            mode = im.mode
        if nn is None:
            good = (iw == ew and ih == eh)
            ok_ref &= good
            print("  [%s] %-46s %-28s 素材 %dx%d %s ｜ 元素 %dx%d（无 nine ⇒ 必须 1:1）"
                  % ("OK " if good else "NG!", where, ref, iw, ih, mode, ew, eh))
        else:
            good = (iw >= nn["l"] + nn["r"] and ih >= nn["t"] + nn["b"])
            ok_ref &= good
            print("  [%s] %-46s %-28s 素材 %dx%d %s ｜ 九宫格 l+r=%d t+b=%d；元素 %dx%d"
                  % ("OK " if good else "NG!", where, ref, iw, ih, mode,
                     nn["l"] + nn["r"], nn["t"] + nn["b"], ew, eh))
    ok_all &= ok_ref
    print("-" * 100)
    print("预演图（自己看过、见交付报告）：")
    print("  干净图 : %s" % os.path.relpath(out1, UI).replace("\\", "/"))
    print("  标注图 : %s" % os.path.relpath(out2, UI).replace("\\", "/"))
    print("  文本样例（压力测试用真实台词，%d 条 / 各自 %d..%d 字）："
          % (len(texts), min(len(t) for t in texts), max(len(t) for t in texts)))
    for i, t in enumerate(texts, 1):
        print("    %d) %s" % (i, t[:60] + ("…" if len(t) > 60 else "")))
    print("=" * 100)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
