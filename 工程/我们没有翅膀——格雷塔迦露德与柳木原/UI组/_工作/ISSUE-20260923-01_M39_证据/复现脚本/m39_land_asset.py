# -*- coding: utf-8 -*-
r"""M39 落地 · 素材搬运与**重新实测**（不沿用上一轮结论）

1. 归档未采用的 400 版：`krkr/assets/ui/x_ui_dlgmask_bottom.png` → `_工作\M39_旧素材归档\`（**不删**）
2. 落新素材：证据目录 `剖面实验\x_ui_dlgmask_bottom_350.png` → `krkr/assets/ui/x_ui_dlgmask_bottom_350.png`
3. **对落盘后的正式素材重新实测**：模式 / 尺寸 / RGB / alpha 首末 / 单调性 / max / 中线值 / 剖面抽样 / md5

用法：
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_land_asset.py
"""
import hashlib
import io
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
SRC = os.path.join(EVID, "剖面实验", "x_ui_dlgmask_bottom_350.png")
DST = os.path.join(UI, "krkr", "assets", "ui", "x_ui_dlgmask_bottom_350.png")
OLD = os.path.join(UI, "krkr", "assets", "ui", "x_ui_dlgmask_bottom.png")
ARCH = os.path.join(UI, "_工作", "M39_旧素材归档")
LINES = []


def say(s=""):
    print(s)
    LINES.append(s)


def main():
    say("=" * 84)
    say("M39 落地 · 素材搬运与重新实测")
    say("=" * 84)
    ok = True

    # ① 归档 400 版（不删）
    os.makedirs(ARCH, exist_ok=True)
    if os.path.exists(OLD):
        shutil.move(OLD, os.path.join(ARCH, "x_ui_dlgmask_bottom.png"))
        say("  [OK] 已归档（不删）：krkr\\assets\\ui\\x_ui_dlgmask_bottom.png → _工作\\M39_旧素材归档\\")
    else:
        say("  [ - ] 400 版已不在原位（%s 不存在，视作已归档）" % os.path.relpath(OLD, UI))
    say("      归档目录现有：%s" % sorted(os.listdir(ARCH)))

    # ② 落新素材
    assert os.path.exists(SRC), "源素材不存在：%s" % SRC
    shutil.copyfile(SRC, DST)
    say("  [OK] 已落盘：krkr\\assets\\ui\\x_ui_dlgmask_bottom_350.png（%d 字节）"
        % os.path.getsize(DST))

    # ③ ★ 对**落盘后的正式素材**重新实测（不沿用上一轮结论）
    say("\n■ 落盘素材重新实测（读的就是 %s）" % os.path.relpath(DST, UI))
    im = Image.open(DST)
    im.load()
    r, g, b, a = im.split()
    aa = [a.getpixel((0, y)) for y in range(im.height)]
    row_uniform = all(len(set(a.crop((0, y, im.width, y + 1)).getdata())) == 1
                      for y in range(im.height))
    checks = [
        ("模式 = RGBA（PNG-32）", im.mode == "RGBA", im.mode),
        ("尺寸 = 1920×350", im.size == (1920, 350), str(im.size)),
        ("RGB 全为纯黑 #000000", r.getextrema() == (0, 0) and g.getextrema() == (0, 0)
         and b.getextrema() == (0, 0),
         "R%s G%s B%s" % (r.getextrema(), g.getextrema(), b.getextrema())),
        ("alpha 逐行同值（无横向条纹）", row_uniform, str(row_uniform)),
        ("alpha 首行 = 0", aa[0] == 0, str(aa[0])),
        ("alpha 末行 = 255", aa[-1] == 255, str(aa[-1])),
        ("alpha 纵向单调不减", all(aa[i] <= aa[i + 1] for i in range(len(aa) - 1)),
         "最小步进 %d / 最大步进 %d" % (min(aa[i + 1] - aa[i] for i in range(len(aa) - 1)),
                                      max(aa[i + 1] - aa[i] for i in range(len(aa) - 1)))),
        ("素材上限保留 255（强度交给 opacity）", max(aa) == 255, "max=%d" % max(aa)),
        ("是渐变而非硬边（中线既非 0 也非 255）", 0 < aa[len(aa) // 2] < 255,
         "中线 alpha=%d（t^1.0 理论 255×175/349=128）" % aa[len(aa) // 2]),
    ]
    for nm, cond, detail in checks:
        ok &= bool(cond)
        say("  [%s] %-34s %s" % ("OK " if cond else "NG!", nm, detail))
    say("  alpha 剖面抽样（行号 → α）：")
    for y in [0, 25, 50, 87, 175, 262, 300, 325, 349]:
        say("     y=%3d  t=%.3f  α=%3d" % (y, y / 349.0, aa[y]))
    md5 = hashlib.md5(open(DST, "rb").read()).hexdigest()
    md5s = hashlib.md5(open(SRC, "rb").read()).hexdigest()
    say("  md5（落盘）= %s" % md5)
    say("  md5（源件）= %s  ⇒ 与源件逐字节一致 = %s" % (md5s, md5 == md5s))
    ok &= (md5 == md5s)

    say("\n  结果：%s" % ("**全部通过**" if ok else "**有未通过项**"))
    io.open(os.path.join(EVID, "M39_落地_素材重新实测_原始输出.txt"), "w",
            encoding="utf-8").write("\n".join(LINES) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
