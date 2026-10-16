# -*- coding: utf-8 -*-
r"""m08 · 标题菜单第 6 项文字位图「画廊」→「鉴赏模式」重出三态（ISSUE-20260924-08 收尾 · T2）

背景（用户 2026-09-24 裁决「现在改」）：
  鉴赏模式重构后，外壳标题已是「鉴赏模式」，但标题菜单第 6 项的文字是 M35 的 AI 烘焙位图
  `ui/x_ui_btntxt2c_gallery{,_on,_press}.png`（读作「画廊」）⇒ 需重出为「鉴赏模式」。

为什么是程序化直出、不再走 AI 生图：
  M35 原管线 = `btn_gen.py`（gpt-image-2.5-sunburst 7 行方框图）→ `btn_slice2.py` 切字 →
  `btn_compose.py` 铺羽毛 → `btn_states.py` 派生 `_on/_press`。AI 生图**不幂等**（同一 prompt
  两次跑图不同），且原 7 行图 / out_btn 中间产物已清理。⇒ 本脚本把**前半段换成字体直出**
  （风格按盘上素材实测复刻），后半段**原样复用** btn_compose 的确定性羽毛层与 btn_states 的
  三态派生配方 ⇒ 全链路幂等、可复现。

■ 盘上素材实测（`krkr/assets/ui/x_ui_btntxt2c_*.png`，本脚本的复刻依据）
  画布公式：合成层 = (48n+4(n-1)+48)×96（n=字数；2 字 148 / 3 字 200 / 4 字 252），字身带 y24..71，
  字格 x24+i*52、每格 48×48、格距 4px。
  字体：**粗黑体**（AI 按 "clean bold Chinese gothic" 生成）——实测竖笔宽/字身宽 ≈ 0.21–0.23
  （开 @bare y30：runs 10/47）。本机无 Heavy 字重 ⇒ 用 **Noto Sans SC Bold**（简体全覆盖；
  项目旧字体 GenJyuuGothicXPB 为日文子集、缺「鉴/赏」两字会出豆腐块 —— 首跑实测踩坑，已弃）
  + 600px 渲染时 stroke_width=18 加粗，实测笔画比 ≈ 0.19（盘上对拍见 收尾证据\实测_*.png）。
  填充：纵向渐变（字身核心色实测：顶 (252,253,253) → 中 (235,247,253) → 底 (222,240,253)）。
  描边：亮天蓝环 **#63BDFB**（edge ring 实测均值 (99,189,251)），宽 ≈2px。
  羽毛：M35 独立羽毛层配方（FEATHER_sheet.png 切精灵；density=1.1，同 batch2）。

■ 产物（覆盖写 `krkr/assets/ui/`；旧件先存档 `收尾证据\旧件存档\`）
  x_ui_btntxt2c_gallery.png       常态（252×96）
  x_ui_btntxt2c_gallery_on.png    悬停 = btn_states.hover(常态, 3, 8)（同族半径）
  x_ui_btntxt2c_gallery_press.png 按下 = btn_states.pressed(常态)（×0.80 压暗 + 缩 96% + 2px 亮环）
  ★ 命名沿用 gallery：动作名 `open_gallery` 与 state_group `title.menu_gallery` 不变，
    且全库检索确认旧件仅 01_title.json（及其生成产物）引用、无别屏共用。

■ 自证（缺一即非零退出）
  ① 输入指纹：FEATHER 表 md5、字体 md5 与本文件内记录值一致；
  ② 幂等：内存中独立渲染两遍，三态 md5 逐字节一致；
  ③ 画布：3 件均 252×96；字身带 bbox 落在 x[24,228) y[20,76)；
  ④ 渐变方向：字身上 1/4 核心 R 均值 > 下 1/4（白→冰蓝向下）；
  ⑤ 描边：蓝边像素（B−R>40）计数 > 500；
  ⑥ 与盘上旧件比对，输出 CHANGED / IDENTICAL。

用法：
  python m08_make_btntxt_appmode.py            # 渲染 + 自证 + 写入 krkr/assets/ui/
  python m08_make_btntxt_appmode.py --dry      # 只渲染自证出预览，不写 assets
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
EVID = os.path.join(HERE, "..", "收尾证据")
M35_DIR = os.path.join(UI, "_工作", "M35_生图脚本")

# ── 输入指纹（变更即拒绝，保证复现口径） ──
FEATHER_PATH = os.path.join(HERE, "_输入_FEATHER_sheet.png")
FEATHER_MD5 = "aea416f285da8654738a428893beacb7"
FONT_PATH = r"C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf"
FONT_MD5 = "9c8cb849cb0041912ec77c9c59725a2a"

# ── 几何（与 btntxt2c 族公式一致） ──
TEXT = "鉴赏模式"
KEY = "gallery"
N = len(TEXT)                       # 4
CH, GAP, PAD = 48, 4, 24            # 字身 48、格距 4、羽毛层四周留白 24
BARE_W = CH * N + GAP * (N - 1)     # 204
COMP_W, COMP_H = BARE_W + 2 * PAD, 96   # 252 × 96
GLYPH_Y = PAD                       # 字身带顶 y=24

SS = 8                              # 超采样：字格按 384px 渲染后缩回
SRC = 600                           # 字体渲染基准 px
STROKE = 21                         # 600px 下加粗描边（对拍档位见 收尾证据\实测_参数档位对拍.png：
                                    #   AI 笔画比 0.21–0.23，s18 偏细、s21 最接近，s23+ 「鉴/赏」并笔）
BODY_DOM = 45                       # 字身主导边目标（native px；AI 字身+描边实测 ≈45，
                                    #   故 45 + 描边 1.5px ≈ AI 字身带总高）
EDGE_R = 12                         # SS 下描边膨胀半径 = 1.5px native（AI 描边 1.5–2px）
EDGE_RGB = (99, 189, 251)           # #63BDFB（盘上 edge ring 实测均值）
GRAD_TOP = (252, 253, 253)          # 字身核心渐变（实测三档）
GRAD_MID = (238, 248, 253)
GRAD_BOT = (219, 239, 253)

DENSITY = 1.1                       # 羽毛密度（同 M35 batch2）

OUT = {
    "normal": "x_ui_btntxt2c_%s.png" % KEY,
    "hover": "x_ui_btntxt2c_%s_on.png" % KEY,
    "pressed": "x_ui_btntxt2c_%s_press.png" % KEY,
}


def md5f(path):
    return hashlib.md5(io.open(path, "rb").read()).hexdigest()


def check_inputs():
    for p, want, what in ((FEATHER_PATH, FEATHER_MD5, "羽毛表"),
                          (FONT_PATH, FONT_MD5, "字体")):
        if not os.path.exists(p):
            raise SystemExit("[FAIL] %s 不存在：%s" % (what, p))
        got = md5f(p)
        if got != want:
            raise SystemExit("[FAIL] %s md5 变化：%s ≠ %s（复现口径失效，先核对再改指纹）"
                             % (what, got, want))


def char_mask(ch):
    """渲染单字 → 裁 bbox → 主导边缩放到 BODY_DOM*SS → 返回 L 掩码。

    自带**豆腐块守卫**：字体缺字时 PIL 画的是「方框 + 叉」的 tofu，其四条 bbox 边几乎全实。
    命中即拒（首跑在 GenJyuuGothicXPB 上实测踩过：缺「鉴/赏」→ 两只豆腐块）。
    """
    f = ImageFont.truetype(FONT_PATH, SRC)
    pad = SRC // 3
    cv = Image.new("L", (SRC + 2 * pad, SRC + 2 * pad), 0)
    ImageDraw.Draw(cv).text((pad, pad), ch, font=f, fill=255,
                            stroke_width=STROKE, stroke_fill=255)
    cv = cv.crop(cv.getbbox())
    a = np.array(cv) > 128
    edges = [a[0, :], a[-1, :], a[:, 0], a[:, -1]]
    fr = [e.mean() for e in edges]
    if min(fr) >= 0.85:
        raise SystemExit("[FAIL] 字体缺字（豆腐块守卫）：字「%s」四边实心率 %s —— 换字体"
                         % (ch, ["%.2f" % v for v in fr]))
    w, h = cv.size
    k = (BODY_DOM * SS) / float(max(w, h))
    nw, nh = max(1, int(round(w * k))), max(1, int(round(h * k)))
    return cv.resize((nw, nh), Image.LANCZOS)


def build_bare_ss():
    """SS 级裸字层：1632×384，逐字贴 x=i*52*8（含描边与渐变填充）。"""
    W, H = BARE_W * SS, CH * SS
    body_all = Image.new("L", (W, H), 0)
    boxes = []
    for i, ch in enumerate(TEXT):
        m = char_mask(ch)
        x0 = i * (CH + GAP) * SS + ((CH + GAP) * SS - m.width) // 2
        y0 = (CH * SS - m.height) // 2
        body_all.paste(m, (x0, y0))
        boxes.append((x0, y0, m))
    # 描边 = 联合字身膨胀 − 字身（画在字身之下）
    edge_m = body_all.filter(ImageFilter.MaxFilter(2 * EDGE_R + 1))
    edge = Image.new("RGBA", (W, H), EDGE_RGB + (0,))
    edge.putalpha(edge_m)
    ea = np.array(edge)[..., 3]
    ea[...] = np.where(np.array(body_all) > 0, 0, ea)   # 字身处抠掉描边
    edge.putalpha(Image.fromarray(ea))
    # 渐变填充（顶白 → 底冰蓝，三段线性）
    grad = np.zeros((H, W, 3), dtype=np.uint8)
    ys = np.linspace(0.0, 1.0, H)[:, None]
    for c, (t, m, b) in enumerate(zip(GRAD_TOP, GRAD_MID, GRAD_BOT)):
        v = np.where(ys < 0.45,
                     t + (m - t) * (ys / 0.45),
                     m + (b - m) * ((ys - 0.45) / 0.55))
        grad[..., c] = np.repeat(v, W, axis=1).astype(np.uint8)
    fill = Image.fromarray(grad, "RGB").convert("RGBA")
    fill.putalpha(body_all)
    bare = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bare.alpha_composite(edge)
    bare.alpha_composite(fill)
    return bare


def build_states():
    """返回 {normal/hover/pressed: PIL RGBA 252×96}（渲染两遍自证幂等）。"""
    sys.path.insert(0, M35_DIR)
    import btn_compose
    import btn_states

    # 羽毛表指向本目录的指纹受控副本（btn_compose 默认查它的 out_btn，已清理）
    _real = btn_compose.feather_sprites
    _cache = {}

    def _patched(path=None):
        if path is None:
            path = FEATHER_PATH
        return _real(path)

    btn_compose.feather_sprites = _patched

    outs = {}
    for run_id in (0, 1):                      # ② 幂等自证：独立渲染两遍
        bare_ss = build_bare_ss()
        bare = bare_ss.resize((BARE_W, CH), Image.LANCZOS)
        fl = btn_compose.feather_layer(COMP_W, COMP_H, KEY, DENSITY)
        comp = fl.copy()
        comp.alpha_composite(bare, (PAD, PAD))
        trio = {
            "normal": comp,
            "hover": btn_states.hover(comp, 3, 8),     # 同族 2c 半径（btn_states.GLOW）
            "pressed": btn_states.pressed(comp),
        }
        outs[run_id] = {k: hashlib.md5(_png_bytes(v)).hexdigest() for k, v in trio.items()}
        if run_id == 0:
            keep = trio
    for k in OUT:
        if outs[0][k] != outs[1][k]:
            raise SystemExit("[FAIL] 幂等自证失败：%s 两遍渲染 md5 不同" % k)
    return keep, outs[0]


def _png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def selfcheck(trio):
    """③④⑤ 数据自证 + ⑥ 与盘上旧件比对。返回待写 dict。"""
    ok = True
    for k, name in OUT.items():
        im = trio[k]
        if im.size != (COMP_W, COMP_H):
            print("  ✗ %s 画布 %s ≠ (252,96)" % (name, im.size)); ok = False
    a = np.array(trio["normal"].convert("RGBA")).astype(int)
    al = a[..., 3]
    band = al[GLYPH_Y - 4:GLYPH_Y + CH + 4, PAD:PAD + BARE_W]
    ys, xs = np.nonzero(band >= 160)
    if len(ys) == 0:
        print("  ✗ 字身带为空"); ok = False
    else:
        y0, y1 = ys.min() + GLYPH_Y - 4, ys.max() + GLYPH_Y - 4
        x0, x1 = xs.min() + PAD, xs.max() + PAD
        inside = (20 <= y0 and y1 < 76 and 24 <= x0 and x1 < 24 + BARE_W + 4)
        print("  字身带 bbox x%d..%d y%d..%d（预期 x24..%d y20..75）%s"
              % (x0, x1, y0, y1, 24 + BARE_W - 1, "✓" if inside else "✗"))
        ok = ok and inside
        top = a[GLYPH_Y:GLYPH_Y + 12, PAD:PAD + BARE_W]
        bot = a[GLYPH_Y + CH - 12:GLYPH_Y + CH, PAD:PAD + BARE_W]
        tr = top[:, :, 0][top[:, :, 3] >= 220].mean()
        br = bot[:, :, 0][bot[:, :, 3] >= 220].mean()
        print("  渐变方向：上 1/4 核心 R=%.0f > 下 1/4 R=%.0f %s" % (tr, br, "✓" if tr > br else "✗"))
        ok = ok and tr > br
    blue = ((a[..., 2] - a[..., 0]) > 40).sum()
    print("  蓝边像素（B−R>40）n=%d %s" % (blue, "✓" if blue > 500 else "✗"))
    ok = ok and blue > 500
    for k, name in OUT.items():
        p = os.path.join(ASSETS, name)
        if os.path.exists(p):
            same = md5f(p) == hashlib.md5(_png_bytes(trio[k])).hexdigest()
            print("  与盘上旧件比对 %s：%s" % (name, "IDENTICAL" if same else "CHANGED"))
        else:
            print("  与盘上旧件比对 %s：盘上不存在（首次生成）" % name)
    if not ok:
        raise SystemExit("[FAIL] 自证未通过，拒绝写盘")
    print("  自证：全部通过")


def preview(trio):
    """验收预览：三态并排 + 全 7 项菜单行假拼（第 6 项换新图），衬真实标题底。"""
    os.makedirs(EVID, exist_ok=True)
    bg = Image.open(os.path.join(ASSETS, "x_bg_system.png")).convert("RGBA")
    # 三态并排（4×）
    K = 4
    strip_w = COMP_W * K
    cv = Image.new("RGB", (strip_w + 20, (COMP_H * K + 14) * 3 + 14), (24, 27, 34))
    y = 14
    for k in ("normal", "hover", "pressed"):
        crop = bg.crop((340, 860, 340 + COMP_W, 860 + COMP_H)).copy()
        crop.alpha_composite(trio[k])
        cv.paste(crop.convert("RGB").resize((strip_w, COMP_H * K), Image.NEAREST), (10, y))
        y += COMP_H * K + 14
    p1 = os.path.join(EVID, "T2_鉴赏模式_三态4x_衬标题底.png")
    cv.save(p1)
    # 全菜单 7 行假拼（1×，第 6 项用新图与 252 宽）
    keys = ["start", "continue", "load", "flowchart", "config", "gallery", "exit"]
    rows = []
    for kk in keys:
        icon = Image.open(os.path.join(ASSETS, "x_ui_menuicon_%s.png" % kk)).convert("RGBA")
        if kk == KEY:
            txt = trio["normal"]
        else:
            txt = Image.open(os.path.join(ASSETS, "x_ui_btntxt2c_%s.png" % kk)).convert("RGBA")
        row = bg.crop((240, 350, 700, 1080)).crop((0, 0, 0, 0)) if False else None
        rows.append((kk, icon, txt))
    W, H = 660, 700
    canvas = bg.crop((0, 300, W, 300 + H)).copy()
    for i, (kk, icon, txt) in enumerate(rows):
        yy = 60 + i * 100            # 对齐 menu_hit_y 360+100i −300
        canvas.alpha_composite(icon, (256, yy))
        canvas.alpha_composite(txt, (340, yy))
    p2 = os.path.join(EVID, "T2_菜单并排假拼_第6项换新.png")
    canvas.convert("RGB").save(p2)
    print("  预览 → %s\n  预览 → %s" % (p1, p2))


def main():
    dry = "--dry" in sys.argv
    print("=" * 78)
    print("m08 · 标题菜单第 6 项文字位图重出「鉴赏模式」（程序化、幂等）")
    print("=" * 78)
    check_inputs()
    print("  输入指纹：羽毛表/字体 md5 ✓")
    trio, _ = build_states()
    selfcheck(trio)
    preview(trio)
    if dry:
        print("  --dry：未写 assets")
        return
    # 旧件存档（只存档一次；回滚依据）
    arc = os.path.join(EVID, "旧件存档")
    os.makedirs(arc, exist_ok=True)
    for name in OUT.values():
        src = os.path.join(ASSETS, name)
        dst = os.path.join(arc, name)
        if os.path.exists(src) and not os.path.exists(dst):
            with open(src, "rb") as f:
                open(dst, "wb").write(f.read())
            print("  旧件已存档 → %s" % dst)
    for k, name in OUT.items():
        trio[k].save(os.path.join(ASSETS, name))
        print("  写入 → krkr/assets/ui/%s  md5=%s" % (name, md5f(os.path.join(ASSETS, name))))
    print("完成")


if __name__ == "__main__":
    main()
