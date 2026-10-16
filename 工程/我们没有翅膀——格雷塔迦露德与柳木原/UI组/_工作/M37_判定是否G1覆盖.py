# -*- coding: utf-8 -*-
r"""M37（ISSUE-20260923-01）· 「24 件 icon 是否已被 G1 覆盖」的**像素统计**判定

■ 为什么必须用像素统计（不能看 mtime）
  G1 的 24 件 AI 件与 G2 的 24 件占位件**同名同尺寸**，落盘顺序不确定；
  mtime 会被复制/校验/巡演镜像等无关操作改写（`run_quickbar.bat` 每次整份 xcopy），
  只有**像素内容**能稳定区分两者。

  ⚠️ M38 追修（2026-09-23）：本脚本原先在告警行里**写死「56×56」**，而 L1 起 G1 的规格已改为
  **64×64**（圆径仍 56、留圆外柔光），于是每跑一次都吐一条**陈旧告警**（「尺寸不是 56×56」），
  与盘上现状无关。现改为**由磁盘实测推导尺寸基准**（取 24 件里出现次数最多的方形尺寸，
  并额外打印与基准不一致的件）——基准随素材自动跟随，不会再自我过期。

■ 判据（占位件的构造性特征，见 `M37_占位件与药丸生成.py`）
  占位件 = 硬边（无抗锯齿）纯色：不透明像素 alpha 恒为 255，且 RGB 只取 3 个既有色板色
  （@palette.accent #7AB0E8 / @palette.highlight #3A5A9A / @palette.text_primary #FFFFFF）。
  ⇒ unique RGB ≤ 3 且「不透明像素全属这 3 色」 ⇒ 占位件。
  G1 的 AI 直出件含渐变/抗锯齿/多色，**不可能**满足（数百至数万 unique RGB）。

■ 用法
    python _工作\M37_判定是否G1覆盖.py
  退出码：0 = 结论已给出（占位/覆盖均不视为失败）；2 = 有缺件（须先补件再谈判定）
"""
import glob
import io
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
ASSETS = os.path.join(UI, "krkr", "assets", "ui")

KEYS = ["lock", "save", "load", "qsave", "qload", "auto",
        "skip", "next", "prev", "log", "chart", "option"]

PAL = json.load(io.open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]


def rgb(v):
    v = v.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


PH_RGB = {rgb(PAL["accent"]["value"]), rgb(PAL["highlight"]["value"]),
          rgb(PAL["text_primary"]["value"])}


def stats(p):
    with Image.open(p) as im:
        size = im.size
        im = im.convert("RGBA")
        cols = im.getcolors(maxcolors=1 << 24) or []
    opq, rgbs, solid = 0, set(), True
    for cnt, (r, g, b, a) in cols:
        if a == 0:
            continue
        opq += cnt
        rgbs.add((r, g, b))
        if a != 255 or (r, g, b) not in PH_RGB:
            solid = False
    return size, opq, len(rgbs), solid


def main():
    print("=" * 78)
    print("H1 判定：24 件 x_ui_qbicon_* 是否已被 G1 覆盖（像素统计，非 mtime）")
    print("  占位件特征：不透明像素 alpha≡255 且 RGB ⊆ {#7AB0E8, #3A5A9A, #FFFFFF}")
    print("=" * 78)
    ph, g1, missing, wrong_size = [], [], [], []
    sizes = {}                                   # ★ M38：收集实测尺寸，用于**推导**基准（不写死）
    n = 0
    for k in KEYS:
        for sfx in ("", "_on"):
            n += 1
            name = "x_ui_qbicon_%s%s.png" % (k, sfx)
            p = os.path.join(ASSETS, name)
            if not os.path.exists(p):
                missing.append(name)
                print("  %-30s **缺件**" % name)
                continue
            size, opq, nrgb, solid = stats(p)
            sizes[name] = size
            is_ph = bool(opq) and solid and nrgb <= len(PH_RGB)
            tag = "占位件" if is_ph else "★G1 覆盖"
            (ph if is_ph else g1).append(name)
            if size[0] != size[1]:
                wrong_size.append("%s(%dx%d) 非方形" % (name, size[0], size[1]))
            print("  %-30s %-9s size=%dx%d  uniqueRGB=%-6d 不透明像素=%-5d"
                  % (name, tag, size[0], size[1], nrgb, opq))
    # ★ M38：尺寸基准 = 24 件里出现次数最多的方形尺寸（并列时取较大者）；全部由磁盘实测推导。
    expect = None
    if sizes:
        cnt = {}
        for s in sizes.values():
            cnt[s] = cnt.get(s, 0) + 1
        expect = max(cnt.items(), key=lambda kv: (kv[1], kv[0]))[0]
    print("-" * 78)
    print("占位件 %d 件 ｜ 已被 G1 覆盖 %d 件 ｜ 缺件 %d 件 ｜ 共 %d 件"
          % (len(ph), len(g1), len(missing), n))
    if expect:
        print("尺寸基准（由磁盘实测推导，出现最多者）：%dx%d ｜ 实测尺寸集合：%s"
              % (expect[0], expect[1],
                 "、".join("%dx%d×%d件" % (s[0], s[1], c) for s, c in
                           sorted({s: sum(1 for v in sizes.values() if v == s) for s in sizes.values()}.items(),
                                  key=lambda kv: -kv[1]))))
    if wrong_size:
        print("!! 非方形件：%s" % "、".join(wrong_size))
    if expect:
        off = ["%s(%dx%d)" % (nm, s[0], s[1]) for nm, s in sorted(sizes.items()) if s != expect]
        if off:
            print("!! 与尺寸基准 %dx%d 不一致的件：%s" % (expect[0], expect[1], "、".join(off)))
        else:
            print("尺寸一致性：全部 %d 件 = %dx%d ✓（基准随素材实测，无陈旧告警）"
                  % (len(sizes), expect[0], expect[1]))
    if missing:
        print("结论：**无法判定** —— 有 %d 件缺失（先补件）" % len(missing))
        return 2
    if len(g1) == 0:
        print("结论：**24 件全部仍是 G2 占位件 ⇒ G1 尚未落盘**（收尾交付物不得当作成品 icon）")
    elif len(ph) == 0:
        print("结论：**24 件已全部被 G1 覆盖**（占位件已被替换，可视为成品 icon）")
    else:
        print("结论：**混合态** —— 已有 %d 件被 G1 覆盖，仍有 %d 件是占位件（G1 未全部落盘）"
              % (len(g1), len(ph)))
        print("  仍为占位：%s" % "、".join(ph))
    return 0


if __name__ == "__main__":
    sys.exit(main())
