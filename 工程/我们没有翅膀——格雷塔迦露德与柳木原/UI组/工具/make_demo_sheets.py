# -*- coding: utf-8 -*-
r"""
make_demo_sheets.py —— M21「生图示范图」生成器（可复跑、幂等）
================================================================================
产物（6 张 1920×1080 PNG）→  ..\生图入料\示范图\
    示范_1_系统屏专属背景.png
    示范_2_图标扩展集.png
    示范_3_加载图与错误提示.png
    示范_4_章节卡与成就图标.png
    示范_5_片尾背景与角色卡.png
    示范_6_UI无字底纹.png

用途：**不是生图产物**，而是给用户看的「这一类要生成什么」的带标注示意稿——
底是 krkr 实机画面（真实布局 + 真实资产 + 真实引擎绘字），
要生成的部分用橙色虚线占位框标出，规格写在右侧标注栏。

数据来源（全部只读；**不手绘示意**）
  · 布局坐标 ：layout/screens/*.json       —— 元素 x/y/w/h 逐条读取（占位框位置唯一依据）
  · 色板     ：layout/palette.json         —— @palette.* 解析为真实色值
  · 底图     ：_工作/M15_证据/krkr/png_m15/shot_*.png
                （krkr 实机巡演导出，1920×1080；M18/M19 后于 2026-09-20 05:39 重跑）
  · 贴图     ：krkr/assets/ui/*.png        —— 真实资产（如 x_gen_icon_01..09）
  · 规格文本 ：可AI生图替代素材评估.md §二 / 生图补图任务书.md §1–§7 / UI清单.md §一.2

写权限：仅 `生图入料\示范图\**`（本脚本）。不改 layout / krkr / 复刻 / 资源组 / 用户素材。

复跑
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python "工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/工具/make_demo_sheets.py"
幂等：同输入必得同输出（无随机、无时间戳）。

⚠ 已知耦合（见 _工作\M21_报告.md「规格缺口」）：底图取自 M15 巡演快照。
  若 layout 或资产再变，需重跑巡演刷新 shot_*.png 后再跑本脚本，否则底图与占位框会不同步。
"""

from __future__ import annotations

import io
import json
import os

from PIL import Image, ImageDraw, ImageFont

# ── 路径 ────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))          # …\UI组\工具
UI = os.path.dirname(HERE)                                 # …\UI组
SCREENS_DIR = os.path.join(UI, "layout", "screens")
PALETTE = os.path.join(UI, "layout", "palette.json")
SHOTS = os.path.join(UI, "_工作", "M15_证据", "krkr", "png_m15")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
OUT = os.path.join(UI, "生图入料", "示范图")

# ── 画布与版式 ──────────────────────────────────────────────────────────────
W, H = 1920, 1080
HEAD_H = 104
LEFT = (28, 116, 1264, 892)          # 左：实机画面区 (x, y, w, h)
RX, RY, RW, RH = 1312, 116, 588, 892  # 右：标注栏
FOOT_Y = 1016

# ── 配色（本脚本自身的标注配色，非工程色板） ────────────────────────────────
BG = (10, 18, 30)
PANEL = (18, 28, 45)
PANEL_EDGE = (44, 62, 88)
GOLD = (255, 214, 120)
BODY = (224, 233, 245)
DIM = (152, 166, 186)
ACCENT = (122, 176, 232)
ORANGE = (255, 138, 40)
ORANGE_LT = (255, 196, 120)
CYAN = (96, 220, 230)

# ── 字体 ────────────────────────────────────────────────────────────────────
_F_REG = "C:/Windows/Fonts/msyh.ttc"
_F_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
_fc: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(sz: int, bold: bool = False):
    key = (sz, bold)
    if key not in _fc:
        try:
            _fc[key] = ImageFont.truetype(_F_BOLD if bold else _F_REG, sz)
        except Exception:
            _fc[key] = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", sz)
    return _fc[key]


# ── 数据装载（只读） ────────────────────────────────────────────────────────
def load_screen(sid: str) -> dict:
    """读 layout/screens/*.json：按 id 匹配文件名（文件名前缀为编号）。"""
    for fn in sorted(os.listdir(SCREENS_DIR)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        d = json.load(io.open(os.path.join(SCREENS_DIR, fn), encoding="utf-8"))
        if d.get("id") == sid:
            return d
    raise KeyError("layout 中找不到屏 id=%s" % sid)


def elem(screen: dict, eid: str) -> dict:
    """取元素原始 dict（占位框位置的唯一依据，不手填坐标）。"""
    for e in screen["elements"]:
        if e["id"] == eid:
            return e
    raise KeyError("屏 %s 无元素 %s" % (screen["id"], eid))


def box(screen: dict, eid: str) -> tuple[int, int, int, int]:
    """取元素 (x, y, w, h)；list 元素无 h/w 时回退 item_h / item_w。"""
    e = elem(screen, eid)
    if "x" not in e or "y" not in e:
        raise KeyError("元素 %s 缺少 x/y" % eid)
    w = e.get("w", e.get("item_w"))
    h = e.get("h", e.get("item_h"))
    if w is None or h is None:
        raise KeyError("元素 %s 缺少 w/h 与 item_w/item_h" % eid)
    return int(e["x"]), int(e["y"]), int(w), int(h)


def pal() -> dict:
    d = json.load(io.open(PALETTE, encoding="utf-8"))
    return {k: v["value"] for k, v in d["colors"].items()}


PAL = pal()


def shot(name: str) -> Image.Image:
    p = os.path.join(SHOTS, "shot_%s.png" % name)
    return Image.open(p).convert("RGBA")


def asset(name: str) -> Image.Image:
    return Image.open(os.path.join(ASSETS, name)).convert("RGBA")


# ── 绘图基元 ────────────────────────────────────────────────────────────────
def dash_rect(d, bx, color, width=3, dash=16, gap=10):
    """虚线矩形（占位框用）。"""
    x, y, w, h = bx
    x2, y2 = x + w, y + h
    for x0 in range(x, x2, dash + gap):
        d.line([(x0, y), (min(x0 + dash, x2), y)], fill=color, width=width)
        d.line([(x0, y2), (min(x0 + dash, x2), y2)], fill=color, width=width)
    for y0 in range(y, y2, dash + gap):
        d.line([(x, y0), (x, min(y0 + dash, y2))], fill=color, width=width)
        d.line([(x2, y0), (x2, min(y0 + dash, y2))], fill=color, width=width)


def hatch(d, bx, color=(180, 190, 210, 46), step=12):
    """斜纹填充（表示「会被盖住」的区域）。"""
    x, y, w, h = bx
    for i in range(-h, w, step):
        d.line([(x + i, y), (x + i + h, y + h)], fill=color, width=1)


def wrap(text: str, f, maxw: int) -> list[str]:
    """按像素宽度贪心折行（CJK 逐字、ASCII 尽量不拆词）。"""
    out, line = [], ""
    for ch in text:
        if ch == "\n":
            out.append(line)
            line = ""
            continue
        if f.getlength(line + ch) > maxw and line:
            out.append(line)
            line = ch
        else:
            line += ch
    if line:
        out.append(line)
    return out


def chip(d, cx, cy, lines, size=15, pad=8, fg=ORANGE_LT, bg=(12, 8, 2, 210), bold=True):
    """居中文字块（带底色，保证压在画面上也读得清）。"""
    f = font(size, bold)
    lh = int(size * 1.35)
    tw = max(f.getlength(t) for t in lines)
    th = lh * len(lines)
    x, y = cx - tw / 2 - pad, cy - th / 2 - pad / 2
    d.rounded_rectangle([x, y, x + tw + pad * 2, y + th + pad], 6, fill=bg)
    for i, t in enumerate(lines):
        d.text((cx, y + pad / 2 + lh * i + lh / 2), t, font=f, fill=fg, anchor="mm")


def swatches(d, x, y, items, size=15):
    """色值锚点行：小色块 + 十六进制 + 来源。返回下一行 y。"""
    f = font(size - 2)
    for hexv, src in items:
        hexv = hexv.lstrip("#")
        rgb = tuple(int(hexv[i:i + 2], 16) for i in (0, 2, 4))
        d.rectangle([x, y + 2, x + 20, y + 20], fill=rgb, outline=(90, 104, 126))
        d.text((x + 28, y + 3), "#" + hexv, font=font(size - 2, True), fill=BODY)
        d.text((x + 28 + f.getlength("#" + hexv) + 10, y + 3), src, font=f, fill=DIM)
        y += 26
    return y


# ── 版式骨架 ────────────────────────────────────────────────────────────────
class Sheet:
    """一张示范图的画布：页眉 / 左侧画面区 / 右侧标注栏 / 页脚。"""

    def __init__(self, no: int, title: str, subtitle: str, base_note: str):
        self.im = Image.new("RGBA", (W, H), BG + (255,))
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.no, self.title = no, title
        self.y = RY
        self.maxy = RY

        d = self.d
        d.rectangle([0, 0, W, HEAD_H], fill=(14, 22, 36, 255))
        d.line([(0, HEAD_H), (W, HEAD_H)], fill=PANEL_EDGE, width=2)
        d.text((28, 16), "示范 %d ｜ %s" % (no, title), font=font(34, True), fill=GOLD)
        d.text((28, 60), subtitle, font=font(17), fill=DIM)
        d.text((W - 28, 22), base_note, font=font(16, True), fill=ACCENT, anchor="ra")
        d.text((W - 28, 50), "橙虚框＝此处生成　斜纹＝会被盖住　青细框＝目标满幅范围",
               font=font(15), fill=DIM, anchor="ra")

        d.rectangle([RX - 14, RY - 12, RX + RW, RY + RH], fill=PANEL + (255,))
        d.rectangle([RX - 14, RY - 12, RX + RW, RY + RH], outline=PANEL_EDGE, width=2)

    # —— 画面区 ——
    def place(self, img: Image.Image, scale: float, cx: int, cy: int):
        """把实机画面等比缩放放到 (cx, cy)（左上角），返回 (box, scale)。"""
        w, h = int(img.width * scale), int(img.height * scale)
        self.im.alpha_composite(img.resize((w, h), Image.LANCZOS), (cx, cy))
        self.d.rectangle([cx - 1, cy - 1, cx + w, cy + h], outline=PANEL_EDGE, width=1)
        return (cx, cy, w, h), scale

    def ph(self, sbox, scale, lbox, text, size=15, sub=None, fill=(255, 138, 40, 64),
           label_cy=None, label=True):
        """占位框：lbox 为 layout 坐标 (x,y,w,h)，按 scale 映射到 sbox 上。
        label_cy 可指定标签中心的屏幕 y（默认框中心）；label=False 则不画框内标签
        （用于框内会被后续图层覆盖、标签另置他处的情形）。"""
        x0, y0 = sbox[0], sbox[1]
        x, y, w, h = (int(lbox[0] * scale) + x0, int(lbox[1] * scale) + y0,
                      max(2, int(lbox[2] * scale)), max(2, int(lbox[3] * scale)))
        if fill is not None:
            self.d.rectangle([x, y, x + w, y + h], fill=fill)
        dash_rect(self.d, (x, y, w, h), ORANGE, 3)
        if label:
            lines = wrap(text, font(size), max(60, w - 14))
            if sub:
                lines.append(sub)
            chip(self.d, x + w / 2, label_cy if label_cy is not None else y + h / 2, lines, size=size)
        return (x, y, w, h)

    # —— 标注栏 ——
    def h(self, t: str):
        self.d.text((RX, self.y), t, font=font(19, True), fill=GOLD)
        self.d.line([(RX, self.y + 27), (RX + RW - 6, self.y + 27)], fill=PANEL_EDGE, width=1)
        self.y += 36
        self.maxy = max(self.maxy, self.y)

    def p(self, t: str, color=BODY, size=15):
        for ln in wrap(t, font(size), RW - 6):
            self.d.text((RX, self.y), ln, font=font(size), fill=color)
            self.y += int(size * 1.32)
        self.y += 5
        self.maxy = max(self.maxy, self.y)

    def kv(self, k: str, v: str, size=15):
        f = font(size, True)
        self.d.text((RX, self.y), k, font=f, fill=ACCENT)
        kw = f.getlength(k)
        for ln in wrap(v, font(size), RW - kw - 10):
            self.d.text((RX + kw + 6, self.y), ln, font=font(size), fill=BODY)
            self.y += int(size * 1.32)
        self.y += 3
        self.maxy = max(self.maxy, self.y)

    def li(self, t: str, color=BODY, size=15, mark="· "):
        for i, ln in enumerate(wrap(t, font(size), RW - 18)):
            self.d.text((RX + (0 if i else 0), self.y), (mark + ln) if i == 0 else ("  " + ln),
                        font=font(size), fill=color)
            self.y += int(size * 1.32)
        self.y += 2
        self.maxy = max(self.maxy, self.y)

    def gap(self, n=10):
        self.y += n

    def footer(self, text: str):
        self.d.line([(0, FOOT_Y - 6), (W, FOOT_Y - 6)], fill=PANEL_EDGE, width=2)
        self.d.text((28, FOOT_Y + 8), text, font=font(16), fill=DIM)

    def save(self, name: str):
        os.makedirs(OUT, exist_ok=True)
        if self.maxy > RY + RH:
            print("  !! WARN 右栏内容溢出 %d px（%s）：需精简文本或缩小字号"
                  % (self.maxy - (RY + RH), name))
        p = os.path.join(OUT, name)
        self.im.convert("RGB").save(p, "PNG", optimize=True)
        print("  -> %s  (%d×%d)" % (os.path.basename(p), W, H))
        return p


# ═══════════════════════════════════════════════════════════════════════════
# 示范 1 · 系统屏专属背景
# ═══════════════════════════════════════════════════════════════════════════
def sheet1():
    sc = load_screen("save")
    bg = box(sc, "save.bg_art")          # (60,225,1800,675) —— 当前底图位置
    veil = box(sc, "save.veil")
    pn = box(sc, "save.panel_frame")     # 面板：会盖住底图中部
    ft = box(sc, "save.footer")
    pg = box(sc, "save.page")

    s = Sheet(1, "系统屏专属背景",
              "底 = krkr 实机 save 屏（_工作/M15_证据 巡演导出 1920×1080）；橙虚框＝要生成的位置",
              "底图：save 屏实机画面")
    sbox, k = s.place(shot("08_save"), LEFT[2] / W, LEFT[0], LEFT[1] + (LEFT[3] - int(H * LEFT[2] / W)) // 2)

    # 底图占位框（当前底图所在区域）——先画，标签贴顶（中心留给下方遮挡标注）
    s.ph(sbox, k, bg, "此处生成：本屏专属背景", size=17,
         sub="目标 1920×1080 满幅（当前底图位置 %d×%d @ %d,%d）" % (bg[2], bg[3], bg[0], bg[1]),
         label=False)

    # 面板遮挡区（斜纹 + 压暗，画在占位框之上；标签贴底，避免与上方标签打架）
    hx, hy, hw, hh = (int(pn[0] * k) + sbox[0], int(pn[1] * k) + sbox[1],
                      int(pn[2] * k), int(pn[3] * k))
    s.d.rectangle([hx, hy, hx + hw, hy + hh], fill=(4, 8, 14, 96))
    hatch(s.d, (hx, hy, hw, hh))
    dash_rect(s.d, (hx, hy, hw, hh), (200, 210, 230, 170), 2, 12, 8)
    chip(s.d, hx + hw / 2, hy + hh - 42,
         ["面板 + 8 个槽框 + 按钮会盖住此区（%d×%d @ %d,%d）" % (pn[2], pn[3], pn[0], pn[1]),
          "→ 这 %d×%d 里画什么都不重要" % (pn[2], pn[3])], size=17, fg=(232, 238, 250),
         bg=(6, 10, 18, 225))

    # 目标满幅细框
    dash_rect(s.d, (sbox[0] + 2, sbox[1] + 2, sbox[2] - 4, sbox[3] - 4), CYAN, 2, 26, 16)
    chip(s.d, sbox[0] + 148, sbox[1] + 22, ["目标：满幅 1920×1080"], size=15, fg=CYAN, bg=(4, 16, 20, 200))
    # 主标签放在上方黑边带（橙框中部被面板斜纹覆盖，标签放那里会被压住）
    chip(s.d, sbox[0] + sbox[2] / 2, sbox[1] + 40,
         ["橙框＝本屏底图区域　此处生成：本屏专属背景",
          "目标 1920×1080 满幅（当前底图位置 %d×%d @ %d,%d）" % (bg[2], bg[3], bg[0], bg[1])],
         size=17)

    # 底图可见区（左右两条竖带）
    vis_l = (sbox[0] + int(bg[0] * k), sbox[1] + int(bg[1] * k),
             int((pn[0] - bg[0]) * k), int(bg[3] * k))
    vis_r = (sbox[0] + int((pn[0] + pn[2]) * k), sbox[1] + int(bg[1] * k),
             int((bg[0] + bg[2] - pn[0] - pn[2]) * k), int(bg[3] * k))
    for vb in (vis_l, vis_r):
        dash_rect(s.d, vb, (120, 255, 160, 190), 2, 12, 8)
    chip(s.d, vis_l[0] + vis_l[2] / 2, vis_l[1] + 26,
         ["实际可见带", "%d px 宽" % (pn[0] - bg[0])], size=13, fg=(150, 255, 180), bg=(6, 22, 12, 200))
    chip(s.d, vis_r[0] + vis_r[2] / 2, vis_r[1] + 26,
         ["实际可见带", "%d px 宽" % (bg[0] + bg[2] - pn[0] - pn[2])], size=13, fg=(150, 255, 180),
         bg=(6, 22, 12, 200))

    # —— 标注栏 ——
    s.h("这一批要生成什么")
    s.p("每屏一张「专属满幅背景」，替代现在 6 屏共用的一张底图。无人物、无文字，题材按屏各自的舞台定。")
    s.kv("张数：", "8 张（任务书 §3 A1–A8 已逐屏点名：存档/读档/配置/回想/画廊/音乐/章节/番外）")
    s.kv("尺寸：", "1920×1080 满幅（16:9），JPG 或 PNG 均可")
    s.gap(6)

    s.h("必须 / 禁止")
    s.li("必须：16:9 满幅；画得比最终效果略亮一档（会被压暗层吃暗）", BODY)
    s.li("禁止：任何文字（汉字/假名/拉丁字母/数字）、任何人物（含剪影与远景小人）、logo、水印", ORANGE_LT)
    s.li("禁止：把重要细节放在四角与正下方——面板与按钮会盖住", ORANGE_LT)
    s.gap(6)

    s.h("面板会盖住哪些区域（实测算得）")
    s.li("底图位置 %d×%d @ (%d,%d)" % (bg[2], bg[3], bg[0], bg[1]))
    s.li("面板 panel_frame %d×%d @ (%d,%d) → 底图中部整条被盖死" % (pn[2], pn[3], pn[0], pn[1]))
    s.li("真正露出来的只有左右两条竖带：左 %d px 宽、右 %d px 宽（高 %d）"
         % (pn[0] - bg[0], bg[0] + bg[2] - pn[0] - pn[2], bg[3]))
    s.li("页脚按钮条 %d×%d @ (%d,%d)、页码 @ (%d,%d) 在底图之外（画布黑区）"
         % (ft[2], ft[3], ft[0], ft[1], pg[0], pg[1]))
    s.gap(6)

    s.h("生成后放到哪")
    s.li("接入位置：各屏 layout 的 *.bg_art（本屏为 save.bg_art）；目标改为满幅 (0,0,1920,1080)")
    s.li("压暗层 *.veil 保留（本屏 %d×%d，@palette.backdrop 不透明度 %d）"
         % (veil[2], veil[3], int(PAL["backdrop_opa"])))
    s.li("由 UI 组改 layout → gen_layout.py + verify_ui.py → krkr 实机验收")
    s.gap(6)

    s.h("参考现有同类件")
    s.li("x_bg_system.png（1920×1080，title 屏在用，由 bg63.png 中心裁 16:9）")
    s.li("tl1_bg1.png（1800×675，本屏现用；原版幻想侧城镇风景）")
    s.gap(8)

    s.h("风格锚点（实测取色）")
    s.y = swatches(s.d, RX, s.y, [
        ("#081828", "UI 主色 · sm_base.png"),
        ("#485858", "幻想侧风景 · tl1_bg1.png"),
        ("#587898", "幻想侧风景 · tl1_bg1.png"),
        ("#486858", "幻想侧风景 · tl1_bg1.png"),
        ("#D8E8F8", "现实侧都市 · tl1_bg2.png"),
        ("#98A8C8", "现实侧都市 · tl1_bg2.png"),
    ])
    s.maxy = max(s.maxy, s.y)
    s.footer("对应：可AI生图替代素材评估.md §二#1 ／ 生图补图任务书.md §3 批次 A ｜ 接入：UI 组改 layout *.bg_art ｜ 参考件：x_bg_system.png、tl1_bg1.png")
    return s.save("示范_1_系统屏专属背景.png")


# ═══════════════════════════════════════════════════════════════════════════
# 示范 2 · 图标扩展集
# ═══════════════════════════════════════════════════════════════════════════
IMPL = [("x_gen_icon_01_qsave.png", "快速存档 Q.SAVE"),
        ("x_gen_icon_02_qload.png", "快速读档 Q.LOAD"),
        ("x_gen_icon_03_skip.png", "快进 SKIP"),
        ("x_gen_icon_04_prev.png", "回想/上一页 PREV"),
        ("x_gen_icon_05_save.png", "存档 SAVE"),
        ("x_gen_icon_06_load.png", "读档 LOAD"),
        ("x_gen_icon_07_config.png", "配置 CONFIG"),
        ("x_gen_icon_08_close.png", "关闭 CLOSE"),
        ("x_gen_icon_09_repeat.png", "自动/循环 REPEAT")]

TODO = ["上一页 page_prev", "下一页 page_next", "返回 back", "隐藏窗口 hide", "回想 backlog",
        "系统菜单 menu", "播放 play", "暂停 pause", "上一曲 prev_track", "下一曲 next_track",
        "停止 stop"]


def sheet2():
    s = Sheet(2, "图标扩展集",
              "底 = 纯色底（本类不贴实机屏，只有图标资产）；左侧 5×4＝20 格：9 格实图 + 11 格占位",
              "底：纯色（无实机画面）")
    d = s.d
    d.rectangle([LEFT[0], LEFT[1], LEFT[0] + LEFT[2], LEFT[1] + LEFT[3]], fill=(12, 20, 34, 255))
    d.rectangle([LEFT[0], LEFT[1], LEFT[0] + LEFT[2], LEFT[1] + LEFT[3]], outline=PANEL_EDGE, width=2)
    d.text((LEFT[0] + 20, LEFT[1] + 14), "20 格 = 已实现 9（真图，来自 krkr/assets/ui/）＋ 待生成 11（橙虚框）",
           font=font(18, True), fill=BODY)

    cols, rows = 5, 4
    cw, ch, gx, gy = 200, 200, 28, 20
    tw = cols * cw + (cols - 1) * gx
    th = rows * ch + (rows - 1) * gy
    ox = LEFT[0] + (LEFT[2] - tw) // 2
    oy = LEFT[1] + 52 + (LEFT[3] - 52 - th) // 2

    items = [("real", a, n) for a, n in IMPL] + [("todo", t, None) for t in TODO]
    for i, (kind, a, n) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = ox + c * (cw + gx), oy + r * (ch + gy)
        d.rectangle([x, y, x + cw, y + ch], fill=(18, 28, 44, 255), outline=(40, 56, 80), width=1)
        if kind == "real":
            ic = asset(a)
            k = min((cw - 30) / ic.width, (ch - 62) / ic.height)
            iw, ih = max(1, int(ic.width * k)), max(1, int(ic.height * k))
            s.im.alpha_composite(ic.resize((iw, ih), Image.LANCZOS),
                                 (x + (cw - iw) // 2, y + 8 + (ch - 62 - ih) // 2))
            d.text((x + cw / 2, y + ch - 40), n, font=font(14, True), fill=(150, 255, 180), anchor="mm")
            d.text((x + cw / 2, y + ch - 20), a.replace(".png", ""), font=font(12), fill=DIM, anchor="mm")
        else:
            dash_rect(d, (x + 6, y + 6, cw - 12, ch - 12), ORANGE, 3)
            chip(d, x + cw / 2, y + ch / 2 - 12, ["此处生成", a], size=17)
            d.text((x + cw / 2, y + ch - 26), "待生成", font=font(13, True), fill=ORANGE_LT, anchor="mm")

    # —— 标注栏 ——
    s.h("这一批要生成什么")
    s.p("功能图标。现状是「纯文字按钮」，加图标是观感提升/成本比最高的一项。")
    s.kv("张数：", "11 张缺口（本图）；任务书 §4 全表为 20 张（B01–B20），已实现 9 张")
    s.kv("尺寸：", "512×512 生成、透明底 → 入库 64×64 → UI 内按 24×24 用")
    s.gap(6)

    s.h("已实现的 9 张（真图，可直接对照风格）")
    s.li("x_gen_icon_01_qsave … _09_repeat（192 px 宽，图上烘焙英文标签）")
    s.gap(6)

    s.h("待生成的 11 张（按任务书 §4 语义）")
    for t in TODO:
        s.li(t, ORANGE_LT, 14)
    s.li("另有 config 屏需要的音量/全屏/文字速度/已读跳过 4 个", DIM, 14)
    s.gap(6)

    s.h("必须 / 禁止")
    s.li("必须：与已有 9 张同一套视觉语言——单色线描、白/浅蓝 #DCE8F5、线宽饱满、形状极简、无底框无阴影", BODY)
    s.li("禁止：任何文字（汉字/假名/拉丁字母/数字）、人物、logo、水印", ORANGE_LT)
    s.li("禁止：多色渐变、写实渲染、3D 质感", ORANGE_LT)
    s.gap(6)

    s.h("做法建议")
    s.li("一次出总表（如 4×5）再切；批内同 seed 家族")
    s.li("透明底必须真 alpha（PNG-32）——用导出，不要用「透明预览」截图（棋盘格会烘焙进像素）")
    s.gap(6)

    s.h("生成后放到哪")
    s.li("krkr/assets/ui/x_gen_icon_XX_<语义>.png（前缀 x_gen_）")
    s.li("接入点：dlg.sysbar 8 键、各屏 footer / page_btns、music 控制条、ending 跳过、confirm 是/否")
    s.gap(8)

    s.h("风格锚点")
    s.y = swatches(s.d, RX, s.y, [("#081828", "图标所衬的深底 · sm_base.png"),
                           ("#DCE8F5", "图标线色（任务书 §4）")])
    s.maxy = max(s.maxy, s.y)
    s.footer("对应：可AI生图替代素材评估.md §二#2 ／ 生图补图任务书.md §4 批次 B ｜ 接入：UI 组加图标层 ｜ 参考件：x_gen_icon_01..09")
    return s.save("示范_2_图标扩展集.png")


# ═══════════════════════════════════════════════════════════════════════════
# 示范 3 · 加载图与错误提示
# ═══════════════════════════════════════════════════════════════════════════
def sheet3():
    ld = load_screen("loading")
    cf = load_screen("confirm")
    lbox = box(ld, "loading.box_frame")
    cbox = box(cf, "confirm.panel_frame")
    ctxt = box(cf, "confirm.text")
    cby = box(cf, "confirm.btn_yes_frame")
    cbn = box(cf, "confirm.btn_no_frame")

    s = Sheet(3, "加载图与错误提示 / 确认框装饰",
              "底 = krkr 实机 loading 屏（上）与 confirm 屏（下），均 1920×1080 等比 0.40×",
              "底：loading + confirm 实机画面")
    k = 0.40
    y0 = LEFT[1] + 8
    sb1, _ = s.place(shot("18_loading"), k, LEFT[0] + (LEFT[2] - int(W * k)) // 2, y0)
    sb2, _ = s.place(shot("20_confirm"), k, LEFT[0] + (LEFT[2] - int(W * k)) // 2, y0 + int(H * k) + 20)
    s.d.text((sb1[0], sb1[1] - 24), "loading 屏（实机）", font=font(16, True), fill=ACCENT)
    s.d.text((sb2[0], sb2[1] - 24), "confirm 屏（实机）", font=font(16, True), fill=ACCENT)

    s.ph(sb1, k, lbox, "此处生成：加载图", size=13, sub="%d×%d" % (lbox[2], lbox[3]))
    s.ph(sb2, k, cbox, "此处生成：确认框装饰", size=13, sub="%d×%d" % (cbox[2], cbox[3]))

    for bx, tag in ((ctxt, "提示文本（引擎绘字）"), (cby, "「是」按钮（引擎绘字）"), (cbn, "「否」按钮（引擎绘字）")):
        x = int(bx[0] * k) + sb2[0]
        y = int(bx[1] * k) + sb2[1]
        w = int(bx[2] * k)
        h = int(bx[3] * k)
        dash_rect(s.d, (x, y, w, h), (150, 255, 180, 170), 1, 8, 6)

    # —— 标注栏 ——
    s.h("这一批要生成什么")
    s.p("小面积的装饰件：加载提示框、确认框装饰角、错误提示框。可复用同一背景族，成本低。")
    s.kv("张数：", "5–10 张（评估文档 §二#3）")
    s.gap(6)

    s.h("① 加载图 / 错误提示框")
    s.li("尺寸：%d×%d（= 现有 loading.box_frame，layout 实测）" % (lbox[2], lbox[3]))
    s.li("位置：居中 %d,%d（画布中心偏上，下方留进度条 %d px 高）" % (lbox[0], lbox[1], 6))
    s.li("禁止含文字——「加载中…」由引擎绘字（原版 dm00…dm11 的 320×120 日文提示图不可复用）",
         ORANGE_LT)
    s.gap(6)

    s.h("② 确认框装饰")
    s.li("尺寸：%d×%d（= 现有 confirm.panel_frame）" % (cbox[2], cbox[3]))
    s.li("禁止含文字——「要返回标题画面吗？」与「是 / 否」按钮文字全部引擎绘字"
         "（原版 if_ok/yes/no/cancl 五件是日文烘焙图，不可复用）", ORANGE_LT)
    s.li("装饰只做角与花边；中心必须留透明/低对比，否则文字读不清")
    s.gap(6)

    s.h("必须 / 禁止（两类通用）")
    s.li("必须：低对比、可压在任意背景上；边缘干净", BODY)
    s.li("禁止：任何文字、任何人物、logo、水印；不要做全屏遮罩与纯色面板（引擎画即可）", ORANGE_LT)
    s.li("禁止：可拉伸边框——krkr 无图片遮罩 API、无 stretch，生图边框一拉就断纹（见示范 6）", ORANGE_LT)
    s.gap(6)

    s.h("生成后放到哪")
    s.li("接入位置：loading.box_frame / confirm.panel_frame 的贴图位")
    s.li("loading 现有实现＝全屏遮罩 rect + 九宫格框 + 引擎文字 + 进度条 rect")
    s.gap(8)

    s.h("风格锚点")
    s.y = swatches(s.d, RX, s.y, [("#081828", "UI 主色 · sm_base.png"),
                           ("#585898", "对话窗蓝紫 · meswin.png"),
                           ("#88A8D8", "对话窗蓝紫 · meswin.png"),
                           ("#A8B8F8", "幻想侧浅蓝 · dlg_bg_26.png")])
    s.maxy = max(s.maxy, s.y)
    s.footer("对应：可AI生图替代素材评估.md §二#3 ／ 生图补图任务书.md §6 E2/E3 ｜ 接入：UI 组改 layout 贴图位 ｜ 参考件：panel_frame.png（九宫格）")
    return s.save("示范_3_加载图与错误提示.png")


# ═══════════════════════════════════════════════════════════════════════════
# 示范 4 · 章节卡与成就图标
# ═══════════════════════════════════════════════════════════════════════════
def sheet4():
    # ★ M43（2026-09-23，用户裁定）：「主页·章节选择 chapter」屏已**整体删除**
    #   ⇒ 本示范图（章节卡与成就图标）**失去对象**。原实现（M21 时点，读 `chapter` 屏的
    #   `chapter.list` / `chapter.detail_*` 摆版）已**整体删除**，不留悬空引用；
    #   历史产出的 `生图入料\示范图\示范_4_章节卡与成就图标.png` **保留不删**（证据），
    #   其说明见 `生图入料\示范图\README.md` 与 `_工作\M43_旧素材归档\说明.md`。
    print("  [跳过] 示范 4「章节卡与成就图标」—— chapter 屏已于 2026-09-23 删除（用户裁定）")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# 示范 5 · 片尾背景与角色卡
# ═══════════════════════════════════════════════════════════════════════════
def sheet5():   # ★ 已退役（见 main 里的注记）：屏已删 + 元素 id 自 M32 起过期，不得直接调用
    en = load_screen("ending")
    c1 = box(en, "ending.card_1")
    c2 = box(en, "ending.card_2")
    c3 = box(en, "ending.card_3")
    sf = box(en, "ending.scroll_frame")
    lb = box(en, "ending.lyric_bar")

    s = Sheet(5, "片尾背景与角色卡",
              "底 = krkr 实机 ending 屏（现用原版 sr_01/02/03 三张角色卡）；本类允许画角色",
              "底：ending 屏实机画面")
    sbox, k = s.place(shot("17_ending"), LEFT[2] / W, LEFT[0],
                      LEFT[1] + (LEFT[3] - int(H * LEFT[2] / W)) // 2)

    # 背景占位：满幅 1920×1080（青框）；标签放在画面上方空白带，避免压住歌词条
    dash_rect(s.d, (sbox[0] + 2, sbox[1] + 2, sbox[2] - 4, sbox[3] - 4), CYAN, 2, 26, 16)
    chip(s.d, sbox[0] + sbox[2] / 2, sbox[1] - 34, ["此处生成：片尾背景 1920×1080 满幅（青框）"],
         size=16, fg=CYAN, bg=(4, 16, 20, 220))

    # 角色卡位：卡 1 为占位（要生成的），卡 2/3 为现有参考件
    s.ph(sbox, k, c1, "此处生成：角色卡", size=15, sub="%d×%d" % (c1[2], c1[3]))
    for bx, nm in ((c2, "现有参考件 sr_02.png"), (c3, "现有参考件 sr_03.png")):
        x = int(bx[0] * k) + sbox[0]
        y = int(bx[1] * k) + sbox[1]
        w, h = int(bx[2] * k), int(bx[3] * k)
        dash_rect(s.d, (x, y, w, h), (120, 255, 160, 190), 2, 12, 8)
        chip(s.d, x + w / 2, y + h / 2, [nm, "%d×%d（原版真实素材）" % (bx[2], bx[3])],
             size=14, fg=(150, 255, 180), bg=(6, 22, 12, 200))

    # 引擎绘字区提示
    for bx, tag in ((sf, "STAFF 滚动区（引擎绘字）"), (lb, "歌词条（引擎绘字）")):
        x = int(bx[0] * k) + sbox[0]
        y = int(bx[1] * k) + sbox[1]
        w, h = int(bx[2] * k), int(bx[3] * k)
        dash_rect(s.d, (x, y, w, h), (200, 210, 230, 120), 1, 10, 8)
        chip(s.d, x + w / 2, y + 14, [tag], size=13, fg=(226, 234, 248), bg=(6, 10, 18, 200))

    # —— 标注栏 ——
    s.h("这一批要生成什么")
    s.p("片尾（STAFF/ED）的满幅背景，以及片尾角色卡。角色卡是本批唯一「允许画人物」的一类。")
    s.kv("张数：", "5–15 张（背景 1 + 角色卡若干）")
    s.kv("背景尺寸：", "1920×1080 满幅（无字无人）")
    s.kv("角色卡尺寸：", "%d×%d（= 现有 sr_01..24 原版素材实测尺寸，卡内 1:1 不拉伸）" % (c1[2], c1[3]))
    s.gap(6)

    s.h("⚠ 角色一致性是难点（本批核心风险）")
    s.li("同一角色的脸 / 发型 / 服装必须与原版一致——纯文生图做不到，"
         "需要参考图注入（img2img / ControlNet / LoRA）", ORANGE_LT)
    s.li("强烈建议：先做 1 张，与原版 sr_01..24 并排目视通过后再放量", ORANGE_LT)
    s.li("现有 sr_01..24（612×462，原版片尾角色 CG，目视确认无烘焙文字）即风格基准",
         BODY)
    s.gap(6)

    s.h("必须 / 禁止")
    s.li("背景：必须满幅 16:9；禁止任何文字、logo、水印", BODY)
    s.li("角色卡：允许画角色（本类唯一例外）；但仍禁止在图内写任何文字", BODY)
    s.li("禁止：与原版 2008 水彩感冲突的高饱和 / 3D / 写实质感", ORANGE_LT)
    s.li("与任务书 §7 红线 2「不要画人物」冲突 → 需主代理裁决（见报告「规格缺口」）", ORANGE_LT)
    s.gap(6)

    s.h("生成后放到哪")
    s.li("背景：ending 屏 backdrop/bg_art（现为纯黑 letterbox rect，无背景图）")
    s.li("角色卡：替换 ending.card_1..3 的 sr_0x 引用")
    s.li("STAFF 滚动区与歌词条一律引擎绘字（原版 sr2_t01..t07 歌词条含日文烘焙，不可复用）")
    s.gap(6)

    s.h("做法建议")
    s.li("分两批：先出 1 背景 + 1 角色卡验证，通过再放量", BODY)
    s.li("角色卡用参考图注入（img2img / ControlNet）而非纯文生图", BODY)
    s.gap(6)

    s.h("风格锚点")
    s.y = swatches(s.d, RX, s.y, [("#081828", "UI 主色 · sm_base.png"),
                           ("#A8B8F8", "幻想侧浅蓝 · dlg_bg_26.png"),
                           ("#D8E8F8", "现实侧都市 · tl1_bg2.png"),
                           ("#7888A8", "现实侧都市 · tl1_bg2.png")])
    s.maxy = max(s.maxy, s.y)
    s.y += 8

    # 现有 sr_01..24 风格基准（真图接触印相，任取 6 张）
    s.d.text((RX, s.y), "现有 sr_01..24 风格基准（真图，任取 6 张示意）", font=font(16, True), fill=GOLD)
    s.y += 26
    th_w, th_h = 84, 63
    for i in range(6):
        t = asset("sr_%02d.png" % (i + 1)).resize((th_w, th_h), Image.LANCZOS)
        x = RX + i * (th_w + 10)
        s.im.alpha_composite(t, (x, s.y))
        s.d.rectangle([x, s.y, x + th_w, s.y + th_h], outline=(90, 104, 126), width=1)
    s.y += th_h + 8
    s.li("同一角色的脸/发型/服装必须与这些一致——这是本批的验收核心", DIM, 14)
    s.maxy = max(s.maxy, s.y)
    s.footer("对应：可AI生图替代素材评估.md §二#5、§三.3 ／ 生图补图任务书.md §6 E4 ｜ 接入：ending 屏 bg_art + card_1..3 ｜ 参考件：sr_01..24.png")
    return s.save("示范_5_片尾背景与角色卡.png")


# ═══════════════════════════════════════════════════════════════════════════
# 示范 6 · UI 无字底纹
# ═══════════════════════════════════════════════════════════════════════════
def sheet6():
    cf = load_screen("config")
    pn = box(cf, "config.panel_frame")
    df = box(cf, "config.desc_frame")
    ia = [e for e in cf["elements"] if e["id"] == "config.items_a"][0]

    s = Sheet(6, "UI 无字底纹（满铺贴图）",
              "底 = krkr 实机 config 屏；面板区＝要生成的无字底纹满铺范围（不是可拉伸边框）",
              "底：config 屏实机画面")
    sbox, k = s.place(shot("10_config"), LEFT[2] / W, LEFT[0],
                      LEFT[1] + (LEFT[3] - int(H * LEFT[2] / W)) // 2)

    # 九宫格边框本身（保留原版件，不生成）
    x = int(pn[0] * k) + sbox[0]
    y = int(pn[1] * k) + sbox[1]
    w, h = int(pn[2] * k), int(pn[3] * k)
    dash_rect(s.d, (x, y, w, h), (150, 255, 180, 200), 2, 12, 8)
    chip(s.d, x + w / 2, y + 20, ["边框保留原版 panel_frame.png（九宫格，不生成）"],
         size=14, fg=(150, 255, 180), bg=(6, 22, 12, 205))

    # 满铺底纹占位（面板内缘，内缩九宫格 l=20/t=8/r=20/b=8）
    ins = (pn[0] + 20, pn[1] + 8, pn[2] - 40, pn[3] - 16)
    ix = int(ins[0] * k) + sbox[0]
    iy = int(ins[1] * k) + sbox[1]
    iw, ih = int(ins[2] * k), int(ins[3] * k)
    s.d.rectangle([ix, iy, ix + iw, iy + ih], fill=(255, 138, 40, 58))
    dash_rect(s.d, (ix, iy, iw, ih), ORANGE, 3)
    chip(s.d, ix + iw / 2, iy + ih / 2,
         ["此处生成：无字底纹（低对比、可满铺）",
          "面板内缘 %d×%d @ (%d,%d)｜满铺，不拉伸" % (ins[2], ins[3], ins[0], ins[1])],
         size=17)

    # 说明栏面板同样处理
    dx = int(df[0] * k) + sbox[0]
    dy = int(df[1] * k) + sbox[1]
    dw, dh = int(df[2] * k), int(df[3] * k)
    dash_rect(s.d, (dx, dy, dw, dh), ORANGE, 2, 12, 8)
    chip(s.d, dx + dw / 2, dy + dh / 2, ["说明栏同族底纹 %d×%d" % (df[2], df[3])],
         size=13, fg=ORANGE_LT, bg=(12, 8, 2, 200))

    # 1:1 满铺贴图示例
    tw = 256
    tx, ty = RX + 4, s.y
    s.d.rectangle([tx, ty, tx + tw, ty + tw], fill=(20, 30, 48, 255))
    dash_rect(s.d, (tx, ty, tw, tw), ORANGE, 3)
    chip(s.d, tx + tw / 2, ty + tw / 2, ["此处生成", "满铺贴图", "示例 512×512", "（1:1 像素）"], size=14)
    s.d.text((tx + tw + 20, ty + 8), "「满铺」＝引擎按 1:1", font=font(16, True), fill=BODY)
    s.d.text((tx + tw + 20, ty + 32), "平铺/裁切整张图，", font=font(16), fill=BODY)
    s.d.text((tx + tw + 20, ty + 54), "不需要四边可无缝", font=font(16), fill=BODY)
    s.d.text((tx + tw + 20, ty + 76), "衔接、不需要中心透明。", font=font(16), fill=BODY)
    s.d.text((tx + tw + 20, ty + 106), "所以四边纹理不连续", font=font(16), fill=ORANGE_LT)
    s.d.text((tx + tw + 20, ty + 128), "也没关系——这是本类", font=font(16), fill=ORANGE_LT)
    s.d.text((tx + tw + 20, ty + 150), "与「可拉伸边框」的关键区别。", font=font(16), fill=ORANGE_LT)
    s.y = ty + tw + 10

    s.h("这一批要生成什么")
    s.p("面板的无字底纹（叠加用）。只要「无字、低对比、可满铺」，不要求九宫格可拉伸。")
    s.kv("张数：", "3–8 张（评估文档 §二#6）")
    s.kv("尺寸：", "可满铺即可（如 512×512 / 1024×1024 平铺，或 1920×1080 满幅）")
    s.gap(4)

    s.h("⚠ 这一类只做「底纹」，不做「可拉伸边框」")
    s.li("krkr 没有图片遮罩 API、没有 stretch 属性；边框只能九宫格拉伸", ORANGE_LT)
    s.li("生图边框四边不等宽、纹理不连续，一拉伸就断纹", ORANGE_LT)
    s.li("现有边框 panel_frame.png（41×17，九宫格 l=20,t=8,r=20,b=8）是原版 if_* 八件拼的，"
         "风格本来就对，保留不换", BODY)
    s.li("任务书 §6 E5「可拉伸九宫格边框」建议跳过（除非出图后手工修成四角固定 + 四边可无缝平铺 + 中心透明）",
         DIM)
    s.gap(4)

    s.h("必须 / 禁止")
    s.li("必须：低对比（面板上还要压 %d px 菜单文字）、无字、可满铺" % ia["font"]["size"])
    s.li("禁止：任何文字、任何人物、logo、水印", ORANGE_LT)
    s.li("禁止：高对比花纹、强边框线、居中大图案（会与文字打架）", ORANGE_LT)
    s.li("禁止：做「全屏遮罩 / 纯色面板 / 进度条」——引擎画纯色即可", ORANGE_LT)
    s.gap(4)

    s.h("生成后放到哪")
    s.li("krkr/assets/ui/x_gen_paneltile_*.png；接入各屏 *_panel_fill（现为纯色 rect @palette.panel_fill）之上")
    s.li("另有任务书 §6 E1「标题 logo 无字底纹 482×168」同属本类")
    s.gap(6)

    s.h("风格锚点")
    s.y = swatches(s.d, RX, s.y, [("#081828", "UI 主色 · sm_base.png"),
                           ("#141824", "面板填充底 @palette.panel_fill"),
                           ("#5A6A8A", "面板边框 @palette.panel_edge")])
    s.maxy = max(s.maxy, s.y)
    s.footer("对应：可AI生图替代素材评估.md §二#6、§〇.2 ／ 生图补图任务书.md §6 E1/E5 ｜ 接入：各屏 *_panel_fill ｜ 参考件：panel_frame.png、sm_base.png")
    return s.save("示范_6_UI无字底纹.png")


if __name__ == "__main__":
    print("M21 生图示范图 →", OUT)
    # ★ ISSUE-20260928-07（2026-09-28，用户裁定）：`sheet5`（片尾背景与角色卡）**已退役出调度** ——
    #   ① 该屏（`ending`）已整体删除（用户：未来改用一段视频代替片尾）；
    #   ② 且 `sheet5` 引用的 `ending.card_1..3`/`scroll_frame`/`lyric_bar` **自 M32 重做该屏起就不存在**
    #      （现屏 id 是 `ed.*`）⇒ 它在本批之前**已经跑不通**，留着会连带整个工具失败。
    #   函数体保留（不删）以便追溯；若要重启用，须先按现屏 id 改写。
    for fn in (sheet1, sheet2, sheet3, sheet4, sheet6):
        fn()
    print("done: 5 sheets")   # ★ ISSUE-20260928-07：sheet5 已退役出调度（见上注记）