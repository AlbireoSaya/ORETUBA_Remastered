# -*- coding: utf-8 -*-
r"""按钮文字「悬停态 / 按下态」——**由常态程序化派生**（用户 2026-09-22 选定）。

★ **本文件是产出盘上素材的那一份（唯一可复现配方）**。
  M4（`ISSUE-20260922-28`，2026-09-22）订正：本文件曾长期落后于实际出图用的那份
  （旧版 `hover(im)` 只提亮 18%、无白晕、`P_ALPHA=0.90`、无描边、无 `PRESS_FROM_HOVER`），
  结果「配方可复现」在仓内**不成立**：用它重算 14 件 `_on` / 14 件 `_press` 与盘上 md5 全不同，
  而真正能逐字节复现的版本当时只存在于**未入库**的 `工具\lyai-image-api\btn_states.py`。
  现已把该版本**逐字节同步入仓**，并经 md5 复核：本文件重算 `_on` 14/14、`_press` 14/14、
  选择支 `x_ui_choice_press.png` 全部**逐字节相同**。
  ★ **判据是「能不能复现」，不是「md5 是否等于某个历史值」**（M8 订正，2026-09-22）：
    入仓副本与"产出时所用那份"是否等价，以 **`M35b_选项按下图.py --dry` 的重算结果与盘上素材
    md5 相同**为准 —— 2026-09-22 实测：本文件重算 `x_ui_choice_press.png` 与盘上**逐字节相同**。
    ⚠️ 本文件的 md5 与**同步当时那份源文件**的 md5（`437cd89656168a163f848eebb2f34e7b`）
    **已不相等** —— 因为入仓后头部又经过修订（M4 的订正说明、M35b 的 `PRESS_FROM_HOVER` 注释等）。
    **两者不相等是正常的，不代表配方不一致**；配方一致性只由上面的「重算 → 比 md5」判定。
  ⇒ 后续一律以本文件为准；`工具\lyai-image-api\` 下那份是副本，**不应再有独有改动**。

用户 2026-09-22 的两次要求：
  ①「悬停态不够亮，让它再亮一点并加上白色光晕。」
  ②「既然如此，就不做点击态的图了……」（随后**当晚改口**：另出 7 张图标按下图 ⇒ `MAKE_PRESSED = True`）

■ 悬停配方（只动 RGB/alpha + 叠加一层白色光晕，**不改字形**）

  hover = **提亮**（RGB 向白混合 30% ｜ alpha ×1.25）
        + **白色光晕**：字身掩码（alpha≥160）→ 向外膨胀 → 高斯柔化 → 铺纯白，合成在字形**下方**
          紧晕（core）＋ 宽晕（wide）两层取较亮者，形成「贴字亮环 + 外扩柔晕」

  ★ **为什么"更亮"必须靠白晕而不是继续往白里混**：字形填充本身已是近白的冰蓝渐变
    （#DCEBFB→#FFFFFF，约 90% 白），往白里再混几乎**没有提亮余量**（实测第一版混到 32% 时肉眼仍看不出差别）。
    真正能读出"亮起来"的是**白晕**，故把权重压在光晕上。
  ★ **光晕半径按档做过实底比对**（`_证据/hover_on_real_titlebg.png`，贴真实标题底 `x_bg_system.png`）：
      旧档 R7/G0.60 偏弱 → 用户判"不够亮"；R16/G0.90 在深底上**糊成一片白**（整条被冲掉）；
      **R3/G1.00 + R8/G0.45 最合适**（明显更亮、白晕贴字，不糊底）。本文件即采用后者。
  ★ **画布留白决定可用半径**（实测）：
      正文层  (48n+4(n-1))×48   —— 字身 44–47 塞在 48 里，**垂直只剩 0–2px 余量** ⇒ 只能用紧晕 R1+R2
      合成层  (48n+4(n-1)+48)×96 —— 四周 24px 留白 ⇒ 可用 R3+R8
    故半径按族给值（`GLOW`）。**想要完整白晕就用合成层**；正文层那版只是"亮一点 + 贴字微晕"。

■ 适用对象（`MAKE_PRESSED = True` ⇒ 两族都出 `_on` + `_press`）
  正文层  x_ui_btntxt2_<key>.png   → _on（悬停）/ _press（按下）
  合成层  x_ui_btntxt2c_<key>.png  → _on / _press
  （羽毛层 x_ui_btntxtf_ 是静态层，不随态变化）

  产物画布与常态**完全一致**（krkr 的 hit 会把 state_assets **拉伸进热区**，
  画布一致才能保证三态切换时不受拉伸影响）。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
EVID = os.path.join(UI, "_工作", "M35_证据")

KEYS = ["start", "continue", "load", "flowchart", "config", "gallery", "exit"]

MAKE_PRESSED = True         # ★ M35b：用户 2026-09-22 晚裁定「补上 7 张按下图」→ 开启
PRESS_FROM_HOVER = False    # ★ **从常态版**派生—— 实测订正：
                            #   悬停版已「向白混 30%」，再 ×0.80 正好抵消回常态亮度 ⇒ 按下图
                            #   看上去只是「常态 + 白晕」，既不比常态暗也不比悬停亮，读不出“按下”
                            #   （实机目视确认）。改为从常态派生后，按下 = 常态 ×0.80 = 明确更暗，
                            #   与悬停（明亮的白）形成清楚的第三态。

# ── 悬停配方（2026-09-22 第二次调档，实底比对后定稿）──
H_WHITE, H_ALPHA = 0.30, 1.25          # 提亮：RGB 向白 30% ＋ alpha ×1.25
# 族 → (紧晕半径, 宽晕半径)；强度固定 core 1.00 / wide 0.45
GLOW = {"x_ui_btntxt2_%s.png": (1, 2),      # 正文层：画布只剩 0–2px 余量
        "x_ui_btntxt2c_%s.png": (3, 8)}     # 合成层：四周 24px 留白
GLOW_CORE_G, GLOW_WIDE_G = 1.00, 0.45
BODY_THR = 160                          # 字身掩码阈值（与切分阶段同一口径）

# ── 按下配方（`MAKE_PRESSED=True` ⇒ 已启用；`PRESS_FROM_HOVER=False` ⇒ **从常态版**派生）──
P_RGB, P_ALPHA, P_SCALE = 0.80, 1.00, 0.96   # 压暗 + 缩 96%
                            # ★ P_ALPHA 由 0.90 改 1.00（实测订正）：降 alpha 会让字在
                            #   花哨背景上“发灰透底”、更像褪色而不是按下；保留原 alpha 才是“实心压暗”。
P_RING, P_RING_BLUR = 2, 0.6                 # 亮白 2px 描边


def body_mask(im):
    """字身掩码（L 模式，0/255）——不含外围柔光。"""
    return im.split()[3].point(lambda v: 255 if v >= BODY_THR else 0)


def white_layer(size, mask_l):
    w = Image.new("RGBA", size, (255, 255, 255, 255))
    w.putalpha(mask_l)
    return w


def hover(im, core_r, wide_r):
    """提亮 + 白色光晕（紧晕 + 宽晕取较亮者，合成在字形下方）。"""
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = Image.blend(rgb, Image.new("RGB", im.size, (255, 255, 255)), H_WHITE)
    r2, g2, b2 = rgb.split()
    a2 = a.point(lambda v: max(0, min(255, int(round(v * H_ALPHA)))))
    glyph = Image.merge("RGBA", (r2, g2, b2, a2))

    m = body_mask(im)
    core = (m.filter(ImageFilter.MaxFilter(2 * core_r + 1))
             .filter(ImageFilter.GaussianBlur(max(0.5, core_r * 0.7)))
             .point(lambda v: min(255, int(round(v * GLOW_CORE_G)))))
    wide = (m.filter(ImageFilter.MaxFilter(2 * wide_r + 1))
             .filter(ImageFilter.GaussianBlur(max(0.5, wide_r * 0.6)))
             .point(lambda v: min(255, int(round(v * GLOW_WIDE_G)))))
    gm = ImageChops.lighter(core, wide)

    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(white_layer(im.size, gm))     # 白晕在下
    out.alpha_composite(glyph)                        # 字形在上
    return out


def pressed(im, ring=P_RING):
    """压暗 + 光晕收缩 + 整体缩 96% + 亮白 2px 描边。**默认不执行**（用户 2026-09-22 取消点击态图）。"""
    r, g, b, a = im.split()
    r = r.point(lambda v: int(round(v * P_RGB)))
    g = g.point(lambda v: int(round(v * P_RGB)))
    b = b.point(lambda v: int(round(v * P_RGB)))
    a = a.point(lambda v: max(0, min(255, int(round(v * P_ALPHA)))))
    base = Image.merge("RGBA", (r, g, b, a))

    w, h = base.size
    nw, nh = max(1, int(round(w * P_SCALE))), max(1, int(round(h * P_SCALE)))
    small = base.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(small, ((w - nw) // 2, (h - nh) // 2))

    m = body_mask(out)
    dil = m.filter(ImageFilter.MaxFilter(2 * ring + 1))
    ringm = ImageChops.subtract(dil, m)
    if P_RING_BLUR:
        ringm = ringm.filter(ImageFilter.GaussianBlur(P_RING_BLUR))
    out.alpha_composite(white_layer(out.size, ringm))
    return out


FAMILIES = [("x_ui_btntxt2_%s.png", "x_ui_btntxt2_%s_on.png", "x_ui_btntxt2_%s_press.png"),
            ("x_ui_btntxt2c_%s.png", "x_ui_btntxt2c_%s_on.png", "x_ui_btntxt2c_%s_press.png")]


def main():
    n = 0
    for pat, pat_on, pat_pr in FAMILIES:
        cr, wr = GLOW.get(pat, (2, 5))
        for k in KEYS:
            src = os.path.join(ASSETS, pat % k)
            if not os.path.exists(src):
                print("  缺 %s" % src); continue
            im = Image.open(src).convert("RGBA")
            hv = hover(im, cr, wr)
            hv.save(os.path.join(ASSETS, pat_on % k))
            if MAKE_PRESSED:
                pressed(hv if PRESS_FROM_HOVER else im).save(os.path.join(ASSETS, pat_pr % k))
            n += 1
            print("  %-24s 悬停：提亮 %.2f ｜ 白晕 R%d+R%d ｜ %dx%d"
                  % (pat % k, H_WHITE, cr, wr, im.size[0], im.size[1]))
    print("\n共 %d 件基准 → 派生悬停 %d 件（按下态%s）"
          % (n, n, "已出" if MAKE_PRESSED else "**按用户要求不做**"))

    # 验收证据：常态 vs 悬停，贴**真实标题底**（x_bg_system.png 的菜单落点区域）
    K = 4
    base = Image.open(os.path.join(ASSETS, "x_bg_system.png")).convert("RGB")
    rows = []
    for k in KEYS:
        strip = []
        for pat in (FAMILIES[1][0], FAMILIES[1][1]):
            s = Image.open(os.path.join(ASSETS, pat % k)).convert("RGBA")
            bgc = base.crop((44, 360, 44 + s.width, 360 + s.height)).convert("RGBA")
            bgc.alpha_composite(s)
            strip.append(bgc.convert("RGB"))
        W = sum(x.width for x in strip) + 12
        H = max(x.height for x in strip)
        row = Image.new("RGB", (W, H), (30, 34, 40))
        x = 0
        for s in strip:
            row.paste(s, (x, 0)); x += s.width + 12
        rows.append(row.resize((W * K, H * K), Image.NEAREST))
    Wc = max(x.width for x in rows) + 16
    Hc = sum(x.height for x in rows) + 12 * (len(rows) + 1)
    cv = Image.new("RGB", (Wc, Hc), (30, 34, 40))
    y = 12
    for x in rows:
        cv.paste(x, (8, y)); y += x.height + 12
    p = os.path.join(EVID, "M35_按钮文字_悬停对照_真实标题底4x.png")
    cv.save(p)
    print("证据 → %s  %s（每行左=常态 右=悬停）" % (p, cv.size))


if __name__ == "__main__":
    main()

