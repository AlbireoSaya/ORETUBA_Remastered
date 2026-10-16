# -*- coding: utf-8 -*-
r"""M49 · 回想（backlog）屏重排 · 素材模块 —— 程序化生成「重新播放」按钮三态

Issue : ISSUE-20260924-06（回想屏重排 · 数据 + 素材模块）
契约  : `_工作\ISSUE-20260924-06_回想屏重排\方案.md` §3 素材契约（**接口冻结书**）
        用户原话：「重新播放按钮有点太小了，你需要考虑对其进行处理或重做」

■■ 产出的 3 件（`krkr\assets\ui\`，**新名，旧件一律保留不删**）
    x_ui_spk2_off.png     44×44  常态    —— 霜白磨砂底 + 淡冰蓝环 + 冰蓝喇叭字形
    x_ui_spk2_over.png    44×44  悬停    —— 底色偏冰蓝 + accent 环加亮 + accent 柔外发光
    x_ui_spk2_on.png      44×44  按下    —— 冰蓝底 + accent 实环 + 强外发光 + **霜白**字形

    · 旧件 `x_ui_spk_{off,over,on}.png`（25×27 / 37×40）**保留不删**：`krkr\README_运行方式.md`
      记明「保留不删」，且新件另起 `spk2` 名，互不影响；本脚本**绝不写这三个文件**（见 main 的自证）。
    · 尺寸依据：冻结书 §3「建议画布 ≥ 40×44」⇒ 取 44×44（线性 1.63×、面积 2.9× 于旧 25×27）。
      **1:1 件（无 nine）** ⇒ `item_buttons` 里的 `w/h` 必须 = 44×44（与 verify_ui [2] 同口径）。

■ 风格口径（冰蓝霜白族，与既有 UI 同源）
    配色**一律取自 `layout\palette.json`**（唯一色值来源，运行时读；缺键报错、不静默回落）。
    用到的键：accent / panel_edge / panel_edge_opa / text_menu。
    · 字形（喇叭：箱体 + 喇叭口 + 两道声波弧）是**图形**、不是文字 —— 本工程铁律禁止的是
      「文字烘焙进图」，喇叭图标与既有 `x_ui_spk_*` 同款，属允许范围。
    · 「按钮文字」不在本件内：跳转键的文字由**引擎绘制**（沿用既有 `bl.jump_tx` 口径），
      故 `item_buttons` 的 jump 项带 `label`；重播键为纯图标键（同参照作スピーカー）。
    · 程序化绘制、4× 超采样降采样（真 alpha、无 8-bit 噪声、无棋盘格/白底烘焙）。

■ 为什么是程序化而不是 AI 生图
    ① 三态必须**几何完全对齐**（只有配色/环/发光不同）——AI 生图做不到逐像素同形；
    ② 可复现、可回归（无随机、无时间戳 ⇒ 同版本脚本重跑逐字节一致）；
    ③ 与 M47（设置屏）同一条工程路线：`工具\m47_make_config_assets.py`。

■ 运行
    python 工具\m49_make_backlog_assets.py
  退出码 0 = 3 件全部写出且全部自证通过。**本脚本只产 PNG、绝不写任何 JSON**
  （`layout\screens\26_backlog.json` 才是几何真相源）。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))                 # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                                  # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")

SIZE = (44, 44)                 # 键盘面（1:1，无 nine）
INSET = 1.5                     # 形体外缩（给柔外发光留位置）
RADIUS = 11.5                   # 圆角（＜ l/r 边带口径不重要：本件无 nine，整图 1:1）
RIM_W = 2.0                     # 环宽
OLD = ("x_ui_spk_off.png", "x_ui_spk_over.png", "x_ui_spk_on.png")   # 只读、只为自证存在


# ──────────────────────────────────────────────────────────────── 调色板
def load_palette(path=PALETTE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["colors"]


PAL = load_palette()


def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    return hex2rgb(PAL[key]["value"])


def OPA(key):
    return int(PAL[key]["value"])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# 合成色（palette.json 无此键，推导来源已注明；不新增独立色号）
FROST = (244, 248, 255)      # 合成色（推导自 @palette.accent 向白 78%）：霜白 —— 与 M47 同口径


# ──────────────────────────────────────────────────────────────── 基础工具（与 M47 同源）
def tint(mask, rgb, alpha=255):
    m = mask
    if alpha != 255:
        m = m.point(lambda v: v * alpha // 255)
    im = Image.new("RGBA", m.size, tuple(rgb) + (0,))
    im.putalpha(m)
    return im


def aa(size, draw_fn, scale=4):
    w, h = size
    m = Image.new("L", (w * scale, h * scale), 0)
    draw_fn(ImageDraw.Draw(m), scale)
    return m.resize((w, h), Image.LANCZOS)


def rr_mask(size, box, radius, scale=4):
    """圆角矩形掩膜（**半开区间**语义，与 M47 同规：顶底/左右对称、末行不半透明）"""
    def _d(d, s):
        d.rounded_rectangle([v * s for v in box], radius=radius * s, fill=255)
    return aa(size, _d, scale)


def glow_of(mask, sigma, gain):
    g = mask.filter(ImageFilter.GaussianBlur(sigma))
    return g.point(lambda v: min(255, int(v * gain)))


def clip_low_alpha(img, thr=3):
    """α ≤ thr 的抗锯齿残影归零（圆角外必须是 α=0 —— 逐像素可验证）"""
    a = img.getchannel("A").point(lambda v: 0 if v <= thr else v)
    out = img.copy()
    out.putalpha(a)
    return out


def speaker_glyph_mask(size, alpha=255, scale=4):
    """喇叭字形掩膜：箱体 + 喇叭口 + 两道声波弧（全体几何中心对齐画布中心）"""
    W, H = size
    cx, cy = W / 2.0, H / 2.0            # 22.0 / 22.0
    bx0, bx1 = cx - 11.0, cx - 6.0       # 箱体 x 11..16
    by0, by1 = cy - 4.5, cy + 4.5        # 箱体 y 17.5..26.5
    px_ = cx + 1.5                       # 喇叭口右缘 x 23.5
    ty0, ty1 = cy - 11.0, cy + 11.0      # 喇叭口上下 y 11..33

    def _d(d, s):
        d.rectangle([bx0 * s, by0 * s, bx1 * s, by1 * s], fill=255)
        d.polygon([(bx1 * s, by0 * s), (px_ * s, ty0 * s), (px_ * s, ty1 * s), (bx1 * s, by1 * s)],
                  fill=255)
        for r in (5.5, 9.5):
            d.arc([(px_ - r) * s, (cy - r) * s, (px_ + r) * s, (cy + r) * s],
                  -55, 55, fill=255, width=int(round(2 * s)))
    return aa(size, _d, scale).point(lambda v: v * alpha // 255)


def build_spk2(state):
    """三态之底 + 字形。state ∈ {off, over, on}"""
    W, H = SIZE
    accent = C("accent")
    edge = C("panel_edge")
    body_rgb = {
        "off": mix(FROST, accent, 0.24),
        "over": mix(FROST, accent, 0.34),
        "on": mix(FROST, accent, 0.66),      # ★ 与 `over` 拉开一个明显档（自证：B−R 均值差 > 20）
    }[state]
    body_a = {"off": 242, "over": 246, "on": 252}[state]
    rim_rgb = edge if state == "off" else accent
    rim_a = {"off": 130, "over": 215, "on": 255}[state]
    glow_gain = {"off": 0.0, "over": 0.50, "on": 0.72}[state]
    glyph_col = FROST if state == "on" else mix(accent, FROST, 0.25)
    glyph_a = {"off": 235, "over": 255, "on": 255}[state]

    outer = rr_mask(SIZE, (INSET, INSET, W - INSET, H - INSET), RADIUS)
    inner = rr_mask(SIZE, (INSET + RIM_W, INSET + RIM_W,
                           W - INSET - RIM_W, H - INSET - RIM_W), RADIUS - RIM_W)
    ring = ImageChops.subtract(outer, inner)

    img = tint(outer, body_rgb, body_a)                     # 底铺满圆角（环随后压上）
    if glow_gain > 0:
        img = Image.alpha_composite(img, tint(glow_of(ring, 2.6, glow_gain), accent))
    # 顶内 1px 霜白高光（族语言：玻璃质感；水平直线 ⇒ 后续无拉伸问题）
    hl = Image.new("L", SIZE, 0)
    ImageDraw.Draw(hl).rectangle([0, int(INSET + RIM_W), W, int(INSET + RIM_W) + 1], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, inner), FROST, 150))
    img = Image.alpha_composite(img, tint(ring, rim_rgb, rim_a))   # 环最后压上
    img = Image.alpha_composite(img, tint(speaker_glyph_mask(SIZE), glyph_col, glyph_a))
    return clip_low_alpha(img, 3)


ASSETS = [("x_ui_spk2_off.png", "off"), ("x_ui_spk2_over.png", "over"), ("x_ui_spk2_on.png", "on")]


# ──────────────────────────────────────────────────────────────── 自证
def _say(ok, name, detail):
    print("  [%s] %-40s %s" % ("OK " if ok else "NG!", name, detail))
    return bool(ok)


def verify(name, img):
    ok = True
    ok &= _say(img.mode == "RGBA", name + " · 模式 RGBA（真 alpha）", img.mode)
    ok &= _say(img.size == SIZE, name + " · 尺寸 = %dx%d（1:1 件，无 nine）" % SIZE,
               "%dx%d" % img.size)
    px = img.load()
    W, H = img.size
    cs = [px[0, 0][3], px[W - 1, 0][3], px[0, H - 1][3], px[W - 1, H - 1][3]]
    ok &= _say(max(cs) == 0, name + " · 四角完全透明 α=0", str(cs))
    peak = max(px[x, y][3] for y in range(H) for x in range(W))
    ok &= _say(peak >= 240, name + " · 峰值 α ≥ 240（形体不透明、不是半透明残影）", "αmax=%d" % peak)
    # 字形存在：中心 24×24 内存在与底色差异明显的像素
    c = px[W // 2, H // 2]
    n_glyph = sum(1 for y in range(10, 34) for x in range(10, 34)
                  if max(abs(px[x, y][i] - c[i]) for i in range(3)) > 18)
    ok &= _say(n_glyph > 60, name + " · 中心区有字形（与底色差异 > 18 的像素数）", "%d px" % n_glyph)
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 96)
    print("M49 · 回想屏重排 · 素材模块（重新播放键 `x_ui_spk2_*` 三态，44×44 程序化生成）")
    print("  输出目录 : %s" % OUT)
    print("  调色板   : %s（唯一色值来源，运行时读取）" % os.path.relpath(PALETTE, UI_GROUP))
    print("  参考键值 : accent=%s  panel_edge=%s/%d  text_menu=%s"
          % (PAL.get("accent", {}).get("value"), PAL.get("panel_edge", {}).get("value"),
             OPA("panel_edge_opa"), PAL.get("text_menu", {}).get("value")))
    print("=" * 96)

    # 旧件：**只读自证存在**（本脚本绝不写它们；冻结书 §3 要求旧件保留不删）
    print("旧件只读自证（本脚本不写这三个文件）：")
    for n in OLD:
        p = os.path.join(OUT, n)
        if os.path.exists(p):
            with open(p, "rb") as f:
                b = f.read()
            with Image.open(p) as im:
                sz, mode = im.size, im.mode
            print("  [OK ] %-24s 存在 %s %s %8d B  md5=%s"
                  % (n, "%dx%d" % sz, mode, len(b), hashlib.md5(b).hexdigest()))
        else:
            print("  [NG!] %-24s **不存在**（冻结书要求「旧件保留不删」）" % n)

    rows, ok_all = [], True
    for name, state in ASSETS:
        img = build_spk2(state)
        assert img.size == SIZE
        p = os.path.join(OUT, name)
        img.save(p, optimize=True, compress_level=9)
        b = os.path.getsize(p)
        rows.append((name, state, b))
        print("-" * 96)
        print("【%s】%s态" % (name, {"off": "常态", "over": "悬停", "on": "按下"}[state]))
        ok_all &= verify(name, img)

    # 三态互异 + 「on 明显更蓝」的族语言自证
    print("-" * 96)
    imgs = {s: build_spk2(s) for _n, s in ASSETS}
    d_off_over = d_off_on = 0
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            a, b2, c2 = imgs["off"].load()[x, y], imgs["over"].load()[x, y], imgs["on"].load()[x, y]
            if max(abs(a[i] - b2[i]) for i in range(4)) > 8:
                d_off_over += 1
            if max(abs(a[i] - c2[i]) for i in range(4)) > 8:
                d_off_on += 1
    ok_all &= _say(d_off_over > 100, "三态互异：off↔over 差异像素 > 100", "%d px" % d_off_over)
    ok_all &= _say(d_off_on > 100, "三态互异：off↔on 差异像素 > 100", "%d px" % d_off_on)

    def mean_bias(im):
        p = im.load()
        vals = [(p[x, y][2] - p[x, y][0]) for y in range(SIZE[1]) for x in range(SIZE[0])
                if p[x, y][3] > 200]
        return sum(vals) / float(len(vals))

    bo, bn = mean_bias(imgs["off"]), mean_bias(imgs["on"])
    ok_all &= _say(bn > bo + 20, "族语言：on 比 off 明显更蓝（α>200 像素的 B−R 均值）",
                   "off %.1f → on %.1f" % (bo, bn))

    print("=" * 96)
    print("生成清单（文件名 / 尺寸 / 模式 / 字节）：")
    W = SIZE[0]
    for name, state, b in rows:
        print("  %-24s %dx%d %-5s %7d B   %s" % (name, W, SIZE[1], "RGBA", b,
                                                {"off": "常态", "over": "悬停", "on": "按下"}[state]))
    print("  合计 %d 件 ｜ %d B" % (len(rows), sum(b for _n, _s, b in rows)))
    print("  ★ 无 nine ⇒ 元素/`item_buttons` 的 w/h 必须 = %dx%d（1:1）" % (W, SIZE[1]))
    print("  md5（逐件，供数据侧与审查对账）：")
    for name, _state, _b in rows:
        with open(os.path.join(OUT, name), "rb") as f:
            print("    %-24s %s" % (name, hashlib.md5(f.read()).hexdigest()))
    print("=" * 96)
    print("RESULT=%s" % ("OK 3 件全部写出且自证通过" if ok_all else "NG 有自证未过（见上）"))
    print("★ 提醒：`layout\\screens\\26_backlog.json` 才是几何真相源；本脚本重跑只覆盖这 3 张 PNG。")
    print("=" * 96)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
