# -*- coding: utf-8 -*-
r"""UI 组 · M11 —— 资产集按 1920×1080 画布基线重建（可复跑、幂等）

依据
----
- `..\00_项目总纲.md`「D1 修订注·画布基线（第三条）」：设计画布 1280×720 → **1920×1080**
  （窗口化以 setZoom(2,3) 呈现为 1280×720）。
- `..\资源组\04_1920画布与双分辨率方案.md` §九.3 迁移对照表（×1.5）：
  「119 件贴图 → 改用 `资源组\美术统一_超分\系统UI\` 的 **2× 版**，按 **×1.5 呈现**
   （2× 素材显示为 1.5× = **0.75 倍下采样，更锐**）」。

本脚本做什么
------------
把 `UI组\krkr\assets\ui\` 里现有的每一件资产，**保持文件名不变**（asset 串不变，
M12/M13/M14 的 layout 引用不受影响），替换为 **×1.5 呈现尺寸**的版本：

  1. **常规件**（119 件里非自制的那批）：
     源 = `资源组\美术统一_超分\系统UI\<同名>`（2×），`Image.LANCZOS` 缩到
     `(round1_5(w), round1_5(h))` = 源 × **0.75**（下采样，合规）。
  2. **`panel_frame.png`**（九宫格拼合件）：源不在超分集（是自制件），
     从 **2× 的 `if_*` 八件**重新拼合（2× 版 54×22）→ LANCZOS 缩到 41×17。
  3. **`x_mask_ruleNNN_1x.png`**（自制件）：从 `ruleNNN.png` 的 **2× 版**
     （1920×1088 L 灰度）重做「alpha=灰度、RGB 置白」→ 缩到 1440×816（**0.75×**）。
  4. **`x_mask_ruleNNN_full.png`**（自制件）：同上源 → 缩到 **1920×1080**
     （1920×1088 → 1920×1080，**垂直 0.9926× 下采样**；源 1920/1088=1.7647 非 16:9，
     与旧 1280×720 版同一处理口径）。★ M17 更名：该族满屏件原名后缀 `_1280`
     （1280 基线时代遗留，实际已 1920×1080，名实不符）→ 现为 `_full`。
     `x_mask_ruleNNN_1x.png`（18 件）**不改名**：1× = 1440×816 是 4:3 内容区尺寸，名字仍对。
  5. **`x_title_logo.png`**（自制件）：从 `tl1_logo.png` 的 2× 版（964×330）重做——
     羽毛带 0.75× 下采样；中文标题**按 108px 字号重绘**（不是把 72px 像素放大）。
     ★ M17 删除：原标题屏满幅背景件已无任何引用（M13 标题屏背景改用 `x_bg_system.png`），
     **本脚本不再产出**，资产文件亦已从 `krkr/assets/ui/` 删除（原记录「下采样 0.75×」
     方向标注亦有误，实为放大；该件已删，不再追述）。

纪律
----
- **源素材只读**：`资源组\**` 全程零写入。
- **不放大既有素材**：每一件的目标尺寸都 ≤ 其 2× 源的尺寸（逐件断言校验）。
- 文件名一律不变；仅覆盖 `UI组\krkr\assets\ui\` 内的同名文件。

复跑：`export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" && python 工具/build_assets_1920.py`
"""
from __future__ import annotations

import os
import sys
import json

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
SRC2 = os.path.join(ROOT, "资源组", "美术统一_超分", "系统UI")   # 2× 消费基线
SRC1 = os.path.join(ROOT, "资源组", "美术统一", "系统UI")        # 1× 溯源基准
OUT = os.path.join(UI, "krkr", "assets", "ui")
WORK = os.path.join(UI, "_工作")
EVID = os.path.join(WORK, "M11_证据")

CANVAS = (1920, 1080)
BOX_4_3 = (360, 90, 1200, 900)          # §九.3：原 (240,60,800,600) ×1.5

LOGO_BLUE = (26, 92, 168)
LOGO_HALO = (245, 250, 255)

MASK_RULES = ["000", "001", "002", "003", "004", "005", "006", "008", "009", "013",
              "026", "047", "061", "065", "067", "071", "076", "097"]
IF8 = ["if_lt", "if_rt", "if_lb", "if_rb", "if_tbar", "if_bbar", "if_lbar", "if_rbar"]

LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


def r15(v):
    """×1.5 取整口径：四舍五入（.5 进位），全程统一，写入报告。"""
    return int(v * 1.5 + 0.5)


def fit(img, target):
    """把 img 缩到 target；若 target 与源同尺寸则原样返回。返回 (图, 方向字符串)。"""
    tw, th = target
    sw, sh = img.size
    if (tw, th) == (sw, sh):
        return img, "同尺寸"
    if tw <= sw and th <= sh:
        direction = "下采样 %.4f×%.4f" % (tw / sw, th / sh)
    elif tw >= sw and th >= sh:
        direction = "**放大** %.4f×%.4f" % (tw / sw, th / sh)
    else:
        direction = "混合 %.4f×%.4f" % (tw / sw, th / sh)
    return img.resize((tw, th), Image.LANCZOS), direction


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p)
    return os.path.getsize(p)


def convert_for_resize(img):
    """P 模式（调色板）无法参与 LANCZOS 重采样 → 转 RGBA；其余模式原样。"""
    if img.mode == "P":
        return img.convert("RGBA")
    return img


def build_regular(orig_sizes):
    """常规件：源 = 超分集 2× 同名件，缩到「1× 原图集尺寸 ×1.5」。

    `orig_sizes` 取自 **1× 溯源基准** `资源组\美术统一\系统UI\`（不随输出变动），
    即任务书 `target_w = round(orig_w * 1.5)` 里的 orig_w；
    取源而非取上一次的输出，是为了让本脚本**幂等可复跑**。
    """
    rows = []
    names = sorted(f for f in os.listdir(OUT)
                   if not f.startswith("x_") and f != "panel_frame.png")
    for name in names:
        src_p = os.path.join(SRC2, name)
        if not os.path.exists(src_p):
            rows.append((name, "MISSING in 超分集", "-", "-", "-", 0))
            log("!! %s 在超分集内缺失" % name)
            continue
        src = convert_for_resize(Image.open(src_p))
        ow, oh = orig_sizes[name]
        tw, th = r15(ow), r15(oh)
        out, direction = fit(src, (tw, th))
        size = save(out, name)
        rows.append((name, "%dx%d" % src.size, "%dx%d" % (tw, th), direction, out.mode, size))
        log("%-26s 源 %4dx%-4d -> 目标 %4dx%-4d  [%s]  %s  %d B"
            % (name, src.size[0], src.size[1], tw, th, direction, out.mode, size))
    return rows


def build_panel_frame():
    """panel_frame.png：由 2× 的 if_* 八件重新拼合。

    1× 口径：27×11 = 左中右 13/1/13、上中下 5/1/5（中心 1×1 透明）。
    2× 口径：54×22 = 左中右 26/2/26、上中下 10/2/10 → LANCZOS 缩到 41×17（×1.5）。
    """
    parts = {n: Image.open(os.path.join(SRC2, n + ".png")).convert("RGBA") for n in IF8}
    cw, ch = parts["if_lt"].size          # 2× 角 = 26×10
    bw = parts["if_tbar"].size[0]         # 2× 上/下边宽 = 2
    bh = parts["if_lbar"].size[1]         # 2× 左/右边高 = 2
    SW, SH = cw * 2 + bw, ch * 2 + bh     # 54×22
    canvas = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    canvas.paste(parts["if_lt"], (0, 0))
    canvas.paste(parts["if_rt"], (SW - cw, 0))
    canvas.paste(parts["if_lb"], (0, SH - ch))
    canvas.paste(parts["if_rb"], (SW - cw, SH - ch))
    canvas.paste(parts["if_tbar"].resize((bw, ch), Image.LANCZOS), (cw, 0))
    canvas.paste(parts["if_bbar"].resize((bw, ch), Image.LANCZOS), (cw, SH - ch))
    canvas.paste(parts["if_lbar"].resize((cw, bh), Image.LANCZOS), (0, ch))
    canvas.paste(parts["if_rbar"].resize((cw, bh), Image.LANCZOS), (SW - cw, ch))
    out, direction = fit(canvas, (r15(27), r15(11)))     # 41×17
    size = save(out, "panel_frame.png")
    log("%-26s 2× 拼合 %dx%d -> 目标 %dx%d  [%s]  %s  %d B"
        % ("panel_frame.png", SW, SH, out.size[0], out.size[1], direction, out.mode, size))
    return [("panel_frame.png", "%dx%d" % (SW, SH), "%dx%d" % out.size,
             direction, out.mode, size)]


def mask_rgba(rule):
    """ruleNNN.png 2× (L 灰度) -> RGBA（alpha=灰度，RGB 置白）。"""
    g = Image.open(os.path.join(SRC2, "rule%s.png" % rule)).convert("L")
    white = Image.new("RGB", g.size, (255, 255, 255))
    out = white.convert("RGBA")
    out.putalpha(g)
    return out, g.size


def build_masks():
    rows = []
    for rule in MASK_RULES:
        rgba, gsize = mask_rgba(rule)
        # ① 1x 版：960×544 → ×1.5 = 1440×816
        o1, d1 = fit(rgba, (r15(960), r15(544)))
        n1 = "x_mask_rule%s_1x.png" % rule
        s1 = save(o1, n1)
        log("%-30s 源 rule%s 2× %4dx%-5d -> %4dx%-4d [%s] %d B"
            % (n1, rule, gsize[0], gsize[1], o1.size[0], o1.size[1], d1, s1))
        # ② 满屏版：1280×720 → ×1.5 = 1920×1080（源 1920×1088 垂直下采样）
        #    ★ M17：文件名后缀 _1280 -> _full（原后缀名实不符，实际已 1920×1080）
        o2, d2 = fit(rgba, CANVAS)
        n2 = "x_mask_rule%s_full.png" % rule
        s2 = save(o2, n2)
        log("%-30s 源 rule%s 2× %4dx%-5d -> %4dx%-4d [%s] %d B"
            % (n2, rule, gsize[0], gsize[1], o2.size[0], o2.size[1], d2, s2))
        rows.append((n1, "%dx%d" % gsize, "%dx%d" % o1.size, d1, o1.mode, s1))
        rows.append((n2, "%dx%d" % gsize, "%dx%d" % o2.size, d2, o2.mode, s2))
    return rows


# ★ M17 删除：build_title_bg()（产出标题屏满幅背景件）已整体移除。
#   原因：M13 标题屏背景改用 ui/x_bg_system.png，该件已零引用，
#   资产文件已从 krkr/assets/ui/ 删除，本脚本不再产出（避免复跑又生成）。

def build_title_logo():
    """x_title_logo.png：723×252（原 482×168 ×1.5）。

    - 羽毛带：tl1_logo.png 2× 版（964×330）的 y>=236 带（964×94）→ **0.75× 下采样** 到 723×71；
    - 中文标题「我们没有翅膀」：**按 108px 字号重绘**（不是把 72px 像素放大）；
    - 副题 "under the innocent sky"：按 26px 重绘。
    """
    src = Image.open(os.path.join(SRC2, "tl1_logo.png")).convert("RGBA")
    assert src.size == (964, 330), src.size
    feather2 = src.crop((0, 236, 964, 330))                    # 964×94 纯羽毛带（2×）
    CW, CH = r15(482), r15(168)                                # 723×252
    fw, fh = r15(482), r15(47)                                 # 723×71
    feather, d = fit(feather2, (fw, fh))

    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    font_title = None
    for cand in (r"C:\Windows\Fonts\simkai.ttf", r"C:\Windows\Fonts\simhei.ttf",
                 r"C:\Windows\Fonts\Dengb.ttf", r"C:\Windows\Fonts\msyhbd.ttc"):
        if os.path.exists(cand):
            font_title = ImageFont.truetype(cand, 108)
            face_used = cand
            break
    assert font_title is not None, "无可用中文字体"

    txt = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d_ = ImageDraw.Draw(txt)
    title = "我们没有翅膀"
    tw = d_.textlength(title, font=font_title)
    tx, ty = int((CW - tw) / 2), 12
    for ox, oy in ((-6, 0), (6, 0), (0, -6), (0, 6), (-5, -5), (5, -5), (-5, 5), (5, 5),
                   (-3, 0), (3, 0)):
        d_.text((tx + ox, ty + oy), title, font=font_title, fill=LOGO_HALO + (240,))
    d_.text((tx, ty), title, font=font_title, fill=LOGO_BLUE + (255,))

    tag_font = None
    for cand in (r"C:\Windows\Fonts\DejaVuSansMono-Oblique_0.ttf",
                 r"C:\Windows\Fonts\DejaVuSans-Oblique.ttf",
                 r"C:\Windows\Fonts\DejaVuSans.ttf"):
        if os.path.exists(cand):
            tag_font = ImageFont.truetype(cand, 26)
            break
    if tag_font is not None:
        TAG_TXT, TAG_XY = "under the innocent sky", (24, 144)
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            d_.text((TAG_XY[0] + ox, TAG_XY[1] + oy), TAG_TXT, font=tag_font,
                    fill=(16, 34, 62, 235))
        d_.text(TAG_XY, TAG_TXT, font=tag_font, fill=(226, 238, 252, 255))

    canvas = Image.alpha_composite(canvas, txt)
    canvas.alpha_composite(feather, (0, CH - fh))
    size = save(canvas, "x_title_logo.png")
    log("%-26s 羽毛带 964x94 -> %dx%d [%s]；标题 108px 重绘；输出 %dx%d %d B"
        % ("x_title_logo.png", fw, fh, d, CW, CH, size))
    return [("x_title_logo.png", "964x330", "%dx%d" % canvas.size, d, canvas.mode, size)]


def contact_sheet(rows):
    """证据：全部资产的尺寸对照接触印相表（缩略图）。"""
    cols, cell = 8, 150
    n = len(rows)
    r_ = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, r_ * (cell + 18)), (24, 28, 36))
    d_ = ImageDraw.Draw(sheet)
    for i, (name, *_rest) in enumerate(rows):
        p = os.path.join(OUT, name)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        im.thumbnail((cell - 10, cell - 10), Image.LANCZOS)
        bg = Image.new("RGBA", (cell - 10, cell - 10), (0, 0, 0, 0))
        bg.alpha_composite(im, ((cell - 10 - im.size[0]) // 2, (cell - 10 - im.size[1]) // 2))
        cx, cy = (i % cols) * cell + 5, (i // cols) * (cell + 18) + 5
        sheet.paste(bg.convert("RGB"), (cx, cy))
        d_.text((cx, cy + cell - 8), name[:22], fill=(200, 210, 230))
    p = os.path.join(EVID, "sheet_assets_1920.png")
    sheet.save(p)
    log("证据 -> %s" % p)


def main():
    os.makedirs(EVID, exist_ok=True)
    log("=" * 78)
    log("M11 · build_assets_1920.py —— 资产集按 1920×1080 基线重建")
    log("源（2× 消费基线）: %s" % SRC2)
    log("输出（文件名不变）: %s" % OUT)
    log("=" * 78)

    before = {}
    orig_sizes = {}
    for f in os.listdir(OUT):
        p = os.path.join(OUT, f)
        before[f] = os.path.getsize(p)
        # 1× 尺寸一律取自 1× 溯源基准（幂等：不受上一次输出影响）
        ref = os.path.join(SRC1, f)
        if not f.startswith("x_") and f != "panel_frame.png" and os.path.exists(ref):
            with Image.open(ref) as im:
                orig_sizes[f] = im.size
    before_total = sum(before.values())

    rows = []
    log("\n--- ① 常规件（超分集 2× -> ×1.5，0.75× 下采样）---")
    rows += build_regular(orig_sizes)
    log("\n--- ② panel_frame.png（2× if_* 拼合 -> ×1.5）---")
    rows += build_panel_frame()
    log("\n--- ③ x_mask_*（rule*.png 2× -> ×1.5 / 满屏 1920×1080）---")
    rows += build_masks()
    log("\n--- ④ x_title_logo.png（从 2× 原版件重新派生；x_title_bg 已由 M17 删除）---")
    rows += build_title_logo()

    # 断言：不得放大既有素材
    bad = [r for r in rows if "放大" in r[3]]
    log("\n--- 断言：无「放大既有素材」---")
    log("违规件数 = %d %s" % (len(bad), [b[0] for b in bad] if bad else "（全部合规）"))

    after_total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    rebuilt_total = sum(os.path.getsize(os.path.join(OUT, r[0])) for r in rows)
    log("\n--- 体积 ---")
    log("重建前资产集总体积 = %.2f MB (%d 件)" % (before_total / 1048576, len(before)))
    log("本脚本重建的 %d 件合计 = %.2f MB" % (len(rows), rebuilt_total / 1048576))
    log("资产集目录**合计**（含 M11 的 x_gen_* / x_bg_system） = %.2f MB (%d 件)"
        % (after_total / 1048576, len(os.listdir(OUT))))
    if after_total > 40 * 1048576:
        log("!! 目录合计超过 40 MB —— 需报主代理")

    contact_sheet(rows)

    manifest = os.path.join(EVID, "build_assets_1920_manifest.json")
    with open(manifest, "w", encoding="utf-8") as fh:
        json.dump({"files": [{"name": r[0], "src_size": r[1], "dst_size": r[2],
                              "transform": r[3], "mode": r[4], "bytes": r[5]} for r in rows],
                   "total_bytes": after_total, "total_files": len(os.listdir(OUT))},
                  fh, ensure_ascii=False, indent=1)
    log("清单 -> %s" % manifest)

    lp = os.path.join(EVID, "build_assets_1920.log")
    with open(lp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(LOG) + "\n")
    log("日志 -> %s" % lp)
    return 0


if __name__ == "__main__":
    sys.exit(main())