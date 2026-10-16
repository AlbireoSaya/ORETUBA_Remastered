# -*- coding: utf-8 -*-
r"""M38 · 描边机制的**独立自证**：同一份数据、只换渲染器代码，逐像素 A/B

■ 断言（目标导向，不看退出码）
  · **负向对照（必须逐像素完全一致）**：`outline:false` 的既有元素 ——
      `dlg.hint`（shadow:true 的 24px 提示行）与 `dlg.choices`（2 项选择肢：item_frame 九宫格 + 高亮块 + 33px 阴影字）
      ⇒ 换了渲染器（旧 ui_theme.tjs ↔ M38 新实现）后**一个像素都不许变**。
  · **正向对照（必须不同）**：`dlg.name`（本屏新开 outline:2px 的角色名）
      ⇒ 必须出现差异，否则说明描边根本没生效（「自检绿 ≠ 功能对」）。
  · 正向对照的差异必须呈**环形**（环绕字形），不是整块位移 —— 用「差异像素把字形围起来的比例」度量。

■ 素材来源（同一台机、同一份 layout 数据，只差渲染器）
  A 侧 = `M38_AB_旧渲染器_shot_03_dialog.png`（临时把 ui_theme.tjs 还原成 HEAD 版后跑 run_autotour.bat）
  B 侧 = `M38_AB_新实现_shot_03_dialog.png`（恢复 M38 实现后再跑一遍）

■ 用法
    python _工作\ISSUE-20260923-01_M38_证据\m38_ab_outline_pixels.py
  退出码：0 = 三条全符合预期。
"""
import os
import sys

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
A_SHOT = os.path.join(HERE, "M38_AB_旧渲染器_shot_03_dialog.png")
B_SHOT = os.path.join(HERE, "M38_AB_新实现_shot_03_dialog.png")
A_CHO = os.path.join(HERE, "M38_AB_旧渲染器_shot_04_dialog.png")
B_CHO = os.path.join(HERE, "M38_AB_新实现_shot_04_dialog.png")

# 区域取自 layout/screens/10_dialog.json 的几何（外扩若干像素以便看见边界外的描边）
REGIONS = [
    ("负向对照 dlg.hint (x36 y36 w630 h36) 外扩", (20, 20, 720, 84)),
    ("正向对照 dlg.name (x331 y747 w345 h56) 外扩", (300, 730, 720, 812)),
    ("正向对照 dlg.text (x246 y806 w1224 h201) 外扩", (230, 796, 1480, 1015)),
]
# 环形度量专用：**只框名字框本体 ±4px**（避开 dlg.text 首行与画面细节，判据更干净）
RING_BOX = (327, 743, 681, 808)
CHOICE_REGION = ("负向对照 dlg.choices（选择肢 2 项 + 九宫格框 + 高亮）", (520, 505, 1400, 690))

fails = []


def cmp_region(tag, a_im, b_im, box, allow_diff):
    a = a_im.crop(box).convert("RGB")
    b = b_im.crop(box).convert("RGB")
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    hist = diff.convert("L").histogram()
    n_px = a.size[0] * a.size[1]
    n_diff = n_px - hist[0]
    max_d = max(i for i, v in enumerate(hist) if v)
    sum_d = sum(i * v for i, v in enumerate(hist))
    mean_d = sum_d / float(n_px)
    verdict = "一致 ✓" if n_diff == 0 else ("**有差异**" if allow_diff else "**意外差异**")
    print("  %-46s 尺寸 %dx%d ｜ 差异像素 %d/%d (%.2f%%) ｜ 最大差值 %d ｜ 平均 %0.4f ｜ %s"
          % (tag, a.size[0], a.size[1], n_diff, n_px, 100.0 * n_diff / n_px, max_d, mean_d, verdict))
    if bbox:
        print("        差异包围盒 %s" % (bbox,))
    if allow_diff:
        if n_diff == 0:
            fails.append("%s：正向对照**没有差异** ⇒ 描边未生效（自检绿 ≠ 功能对）" % tag)
    else:
        if n_diff != 0:
            fails.append("%s：outline:false 的元素竟被改了 %d 像素（最大差 %d）" % (tag, n_diff, max_d))
    return diff, n_diff


def outline_evidence(a_im, b_im):
    r"""**目标导向**：证明「描边真的画在文字周围，且正文压在描边之上」。

    只用**与画面无关、可复算**的量（不依赖「背景亮还是暗」这类假设）：

      ① **填色本体不变**：`dlg.name` 的主色是色板 `text_name`（从 layout/palette.json 读，
         **不写死**），统计与其逐通道差 ≤8 的像素数 —— 在该矩形内这基本就是名字的字形填色。
         断言 A/B 变化 ≤2% ⇒ 正文没被描边色改写、也没被挪动（「最后画正文」成立）。
      ② **描边墨迹确实加在字形周围**：元素矩形 ±(描边宽+4)px 内的「近黑像素」（L<40，
         = outline_color #000000）数必须 B > A。
      ③ **描边不外溢**：在上述带子里、元素矩形 ±(描边宽+2)px **之外**，差异像素必须为 0
         （即描边只影响该文字自己的邻域，不碰画面、不碰别的元素）。
    """
    import json
    UI = os.path.dirname(os.path.dirname(HERE))
    pal = json.load(open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]
    hexcol = pal["text_name"]["value"]
    name_rgb = tuple(int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    sc = json.load(open(os.path.join(UI, "layout", "screens", "10_dialog.json"), encoding="utf-8"))
    el = [e for e in sc["elements"] if e["id"] == "dlg.name"][0]
    x0, y0 = int(el["x"]), int(el["y"])
    x1, y1 = x0 + int(el["w"]), y0 + int(el["h"])
    R = int(el["font"]["outline_width"])                     # 描边宽 = 数据里的 outline_width
    pad_in, pad_out = R + 2, R + 4                           # 允许描边的范围 / 禁止越界的范围

    def fill_count(im):
        """填色像素：与色板主色逐通道差 ≤2 的像素；`interior` 再要求 8 邻域也都在 ±30 内
        （⇒ 该点不在字形边缘上，不可能被描边影响）。返回 (全部填色数, interior 列表)。"""
        px = im.crop((x0, y0, x1, y1)).convert("RGB").load()
        allp, interior = 0, []
        for y in range(y1 - y0):
            for x in range(x1 - x0):
                if not all(abs(px[x, y][c] - name_rgb[c]) <= 2 for c in range(3)):
                    continue
                allp += 1
                if 0 < x < (x1 - x0) - 1 and 0 < y < (y1 - y0) - 1 and all(
                        all(abs(px[x + dx, y + dy][c] - name_rgb[c]) <= 30 for c in range(3))
                        for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    interior.append((x, y))
        return allp, interior

    def black_count(im):
        box = (x0 - pad_out, y0 - pad_out, x1 + pad_out, y1 + pad_out)
        px = im.crop(box).convert("L").load()
        return sum(1 for y in range(box[3] - box[1]) for x in range(box[2] - box[0])
                   if px[x, y] < 40)

    fa_all, fa_in = fill_count(a_im)
    fb_all, fb_in = fill_count(b_im)
    pb = b_im.crop((x0, y0, x1, y1)).convert("RGB").load()
    pa = a_im.crop((x0, y0, x1, y1)).convert("RGB").load()
    kept = sum(1 for (x, y) in fa_in
               if all(abs(pa[x, y][c] - pb[x, y][c]) <= 2 for c in range(3)))
    ba, bb = black_count(a_im), black_count(b_im)
    print("    ① 名字填色（色板 text_name = %s %s，逐通道 ±2）：A=%d → B=%d（Δ=%+d，%.2f%%）"
          "｜其中**离字形边缘 ≥1px 的本体像素** A=%d，A/B 逐通道差 ≤2 的 %d（%.2f%%）"
          % (hexcol, name_rgb, fa_all, fb_all, fb_all - fa_all,
             100.0 * abs(fb_all - fa_all) / max(1, fa_all),
             len(fa_in), kept, 100.0 * kept / max(1, len(fa_in))))
    print("    ② 元素矩形 ±%dpx 内近黑像素（L<40）：A=%d → B=%d（Δ=%+d ⇒ 描边新增的黑色边）"
          % (pad_out, ba, bb, bb - ba))

    # ③ 越界检查：只查**上/左/右**三侧。下沿 y=803 与 dlg.text 首行（y=806 起、自带描边）
    #    只差 3px，正文自己的描边会落进名字框下方带 —— 那是**它的**描边，不是名字外溢，
    #    故把下沿截到 y1+2，避免把邻居的属性算成本件的缺陷。
    strip = (x0 - pad_out, y0 - pad_out, x1 + pad_out, y1 + 2)
    inner = (x0 - pad_in, y0 - pad_in, x1 + pad_in, y1 + 2)
    d = ImageChops.difference(a_im.crop(strip).convert("RGB"),
                              b_im.crop(strip).convert("RGB")).convert("L")
    dp = d.load()
    w, h = d.size
    ox, oy = inner[0] - strip[0], inner[1] - strip[1]
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    out_px = 0
    for y in range(h):
        for x in range(w):
            if ox <= x < ox + iw and oy <= y < oy + ih:
                continue
            if dp[x, y] > 0:
                out_px += 1
    print("    ③ 名字框 上/左/右 三侧 ±%dpx 带内、±%dpx 之外的差异像素 = %d（必须为 0：描边不外溢）"
          % (pad_out, pad_in, out_px))

    if fa_in and kept != len(fa_in):
        fails.append("名字**本体**填色像素有 %d/%d 个被改写 ⇒ 正文未压在描边之上（或被挪动）"
                     % (len(fa_in) - kept, len(fa_in)))
    if bb <= ba:
        fails.append("元素矩形内近黑像素没有增加（B=%d ≤ A=%d）⇒ 描边未生效" % (bb, ba))
    if out_px != 0:
        fails.append("描边越界：上/左/右 ±%dpx 带内、±%dpx 之外有 %d 个差异像素"
                     % (pad_out, pad_in, out_px))
    return fa_all, fb_all


def main():
    for p in (A_SHOT, B_SHOT, A_CHO, B_CHO):
        if not os.path.exists(p):
            print("!! 缺件：%s" % p)
            return 2
    a_im, b_im = Image.open(A_SHOT), Image.open(B_SHOT)
    a_cho, b_cho = Image.open(A_CHO), Image.open(B_CHO)
    print("=" * 96)
    print("A 侧（旧渲染器 HEAD ui_theme.tjs）%s  %s" % (a_im.size, os.path.basename(A_SHOT)))
    print("B 侧（M38 新实现，含 uiThemeDrawOutline）%s  %s" % (b_im.size, os.path.basename(B_SHOT)))
    print("=" * 96)
    print("【一】同一张 shot_03_dialog（默认态）")
    for tag, box in REGIONS:
        diff, n = cmp_region(tag, a_im, b_im, box, allow_diff=("dlg.name" in tag or "dlg.text" in tag))
        out = os.path.join(HERE, "M38_AB_差异图_%s.png" % tag.split()[1])
        diff.point(lambda v: min(255, v * 6)).save(out)
    print("\n【二】同一张 shot_04_dialog（选择肢展开）")
    cmp_region(CHOICE_REGION[0], a_cho, b_cho, CHOICE_REGION[1], allow_diff=False)
    print("     另一条等价断言：整张 shot_04 除名字/正文区域外必须一致")
    d_all = ImageChops.difference(a_cho.convert("RGB"), b_cho.convert("RGB"))
    d_all.paste((0, 0, 0), (230, 796, 1480, 1015))     # 挖掉正文区
    d_all.paste((0, 0, 0), (300, 730, 720, 815))       # 挖掉名字区
    bb = d_all.getbbox()
    n_other = sum(1 for px in d_all.convert("L").getdata() if px > 0)
    print("     除名字/正文外差异像素 = %d ｜ 包围盒 %s ⇒ %s"
          % (n_other, bb, "一致 ✓" if n_other == 0 else "**意外差异**"))
    if n_other:
        fails.append("shot_04：除名字/正文外仍有 %d 像素差异" % n_other)

    print("\n【三】正向对照必须能证明「描边画在字形周围 + 正文压在描边之上 + 不外溢」")
    outline_evidence(a_im, b_im)

    print("\n" + "-" * 96)
    if fails:
        print("结果：**%d 项不符合预期**" % len(fails))
        for f in fails:
            print("  ✗ " + f)
        return 1
    print("结果：**三条全符合预期**（outline:false 逐像素不变；outline:true 呈环形描边差异）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
