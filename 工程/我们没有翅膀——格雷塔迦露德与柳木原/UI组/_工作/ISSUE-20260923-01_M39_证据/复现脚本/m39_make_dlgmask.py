# -*- coding: utf-8 -*-
r"""M39 · 生成对话框底部渐变遮罩素材（**程序化生成，不走 AI**）

产物：`krkr/assets/ui/x_ui_dlgmask_bottom.png`
  · 尺寸 **1920×400**（满幅宽；高 400 便于覆盖 y 680..1080 而**不必**用 nine 纵向拉伸，
    故 `verify_ui.py` 检查 [2]「无 nine 的 image，w/h 必须等于 PNG 实际尺寸」直接成立）
  · **PNG-32**（RGBA）；RGB 纯黑 `#000000`；alpha 自顶 0 平滑升到底 255
  · 纵向剖面 `a = 255 * t^1.6`（t = 行号 / (H-1)，0..1）——**略偏底**：
    t^1.6 < t（t<1），即上半段比线性更透，避免"上半段就压暗画面"
  · 素材本身做到最大 255 ⇒ **强度旋钮 = 元素的 `opacity`**，改深浅不必重出图

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_make_dlgmask.py
  退出码 0 = 已写出并通过自证（尺寸 / 模式 / RGB / 单调性 / 首末行 / 幂等 md5）
"""
import hashlib
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # …\UI组
OUT = os.path.join(UI, "krkr", "assets", "ui", "x_ui_dlgmask_bottom.png")

W = 1920
H = 400
GAMMA = 1.6


def alpha_at(y):
    """t = y/(H-1) → a = round(255 * t^GAMMA)。首行 0、末行 255（t=1 ⇒ 恰为 255）。"""
    t = y / float(H - 1)
    a = int(round(255.0 * (t ** GAMMA)))
    return 0 if a < 0 else (255 if a > 255 else a)


def main():
    vals = [alpha_at(y) for y in range(H)]

    raw = bytearray()
    for y in range(H):
        raw += bytes((0, 0, 0, vals[y])) * W     # 逐行铺开：RGB 恒 0，alpha 取该行值
    img = Image.frombytes("RGBA", (W, H), bytes(raw))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    md5a = hashlib.md5(open(OUT, "rb").read()).hexdigest()

    # ---------------- 自证 ----------------
    print("=" * 78)
    print("M39 遮罩素材生成：" + OUT)
    print("=" * 78)
    chk = Image.open(OUT)
    chk.load()
    ok = True
    ok &= _say("模式 = RGBA（PNG-32）", chk.mode == "RGBA", chk.mode)
    ok &= _say("尺寸 = 1920×400", chk.size == (W, H), str(chk.size))
    r, g, b, a = chk.split()
    ok &= _say("RGB 全为纯黑 #000000", r.getextrema() == (0, 0)
               and g.getextrema() == (0, 0) and b.getextrema() == (0, 0),
               "R%s G%s B%s" % (r.getextrema(), g.getextrema(), b.getextrema()))
    aa = list(a.getdata())[::W]          # 每行首像素 = 该行 alpha（逐行同值）
    ok &= _say("alpha 自顶 0 → 底 255", aa[0] == 0 and aa[-1] == 255,
               "%d → %d" % (aa[0], aa[-1]))
    ok &= _say("alpha 纵向单调不减（平滑剖面，无台阶）",
               all(aa[i] <= aa[i + 1] for i in range(H - 1)),
               "最小步进 %d / 最大步进 %d" % (min(aa[i + 1] - aa[i] for i in range(H - 1)),
                                             max(aa[i + 1] - aa[i] for i in range(H - 1))))
    ok &= _say("是**渐变**而非硬边矩形（中段既非 0 也非 255）",
               0 < aa[H // 2] < 255, "中段 alpha=%d" % aa[H // 2])
    # t^1.6 比线性偏底：中线处应低于线性 127.5
    lin = int(round(255.0 * (0.5 ** 1.0)))
    ok &= _say("剖面偏底（中线处 < 线性）", aa[H // 2] < lin,
               "t^1.6 中线 %d < 线性 %d（低 %d）" % (aa[H // 2], lin, lin - aa[H // 2]))
    ok &= _say("素材本身做到最大 255（强度交给 opacity）", max(aa) == 255, "max=%d" % max(aa))

    print("\n  剖面采样（行号 → alpha）：")
    for y in [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 399]:
        print("    y=%3d  t=%.3f  alpha=%3d" % (y, y / float(H - 1), aa[y]))

    print("\n  对照线性剖面（t^1.0）在同点位的值，量化「偏底」程度：")
    for y in [0, 100, 200, 300, 399]:
        t = y / float(H - 1)
        print("    y=%3d  线性=%3d  本素材=%3d  差=%+d"
              % (y, int(round(255.0 * t)), aa[y], aa[y] - int(round(255.0 * t))))

    print("\n  md5 = %s" % md5a)
    print("\n%s" % ("RESULT=OK 全部自证通过" if ok else "RESULT=NG 有自证未过（见上）"))
    return 0 if ok else 1


def _say(name, cond, detail):
    print("  [%s] %-46s %s" % ("OK " if cond else "NG!", name, detail))
    return bool(cond)


if __name__ == "__main__":
    sys.exit(main())
