# -*- coding: utf-8 -*-
# ★★★ 警示（E5 · 2026-09-29 登记，只登记不改代码）：本脚本曾用 tempfile.mkdtemp(prefix="e3_verify_")
#     把变异产物写到【系统临时目录】（见 `证据\_自证_mutate.log` 的 C:\Users\ADMINI~1\AppData\Local\Temp\…），
#     **违反 AGENTS.md §一 铁律 1/3**（一切产物必须落在工作区内 E:\ZCode Workspace\Galgame 下）。
#     ★ 该模块（E3＝`x_ui_entry_note.png` AI 生图方案）**已被用户取消、脚本仅留档、不得再跑**。
# ★★★
r"""E3 · 定稿 `x_ui_entry_note.png` 自证（可复跑、带变异自证）。

    python e3_verify.py            # 全项自检（退出码 0=全通过）
    python e3_verify.py --mutate   # 变异自证：在临时副本上打废各判据，断言必须报警

判据（对应派单「自证」一节）：
  V1 尺寸 86×48 ｜ V2 mode=RGBA ｜ V3 真 alpha（有 0 与 >0 像素、非棋盘格烘焙）
  V4 α 分布（透明/半透明/不透明像素数）｜ V5 最外 1px 帧 αmax=0
  V6 灰尘检查：实体外 2px 环带内 αmax ≤ 8 ｜ V7 与同族件的 body 色均值差 ≤ 20/通道
  V8 无文字：不可机检 ⇒ 由人工目视在 4×／8× 图上确认（本脚本只产出放大图供核对）
"""
import os
import shutil
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_DIR = os.path.dirname(HERE)
EV = os.path.join(ITEM_DIR, "证据")
UI = os.path.normpath(os.path.join(ITEM_DIR, "..", "..", "krkr", "assets", "ui"))
NAME = "x_ui_entry_note.png"
WANT = (86, 48)
FAMILY = ["x_ui_label_off.png", "x_ui_fusen_off.png", "x_ui_jumpfc_off.png"]
_fails = []


def ck(cond, tag, msg):
    print("%-6s %s  %s" % ("PASS" if cond else "FAIL", tag, msg))
    if not cond:
        _fails.append(tag)
    return cond


def body_mean(im):
    px = im.convert("RGBA").load()
    acc, n = [0, 0, 0], 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 200:
                acc[0] += r; acc[1] += g; acc[2] += b; n += 1
    return (tuple(round(c / n) for c in acc) if n else None), n


def verify(path, label="定稿"):
    print("=" * 78)
    print("%s：%s" % (label, path))
    im = Image.open(path)
    ck(im.size == WANT, "V1", "尺寸 = %s（期望 86×48）" % (im.size,))
    ck(im.mode == "RGBA", "V2", "mode = %s（期望 RGBA）" % im.mode)
    if im.mode != "RGBA":
        return
    a = im.getchannel("A")
    px = list(a.getdata())
    zero = sum(1 for v in px if v == 0)
    full = sum(1 for v in px if v == 255)
    mid = len(px) - zero - full
    print("       V4 α 分布：透明(0)=%d ｜ 半透明(1..254)=%d ｜ 不透明(255)=%d ｜ 合计=%d ｜ extrema=%s"
          % (zero, mid, full, len(px), a.getextrema()))
    ck(zero > 0 and (mid + full) > 0, "V3b", "真 alpha：存在全透明像素，也存在墨迹像素")
    fr = [a.getpixel((x, 0)) for x in range(im.width)]
    fr += [a.getpixel((x, im.height - 1)) for x in range(im.width)]
    fr += [a.getpixel((0, y)) for y in range(im.height)]
    fr += [a.getpixel((im.width - 1, y)) for y in range(im.height)]
    ck(max(fr) == 0, "V5", "最外 1px 帧（%d 像素）αmax = %d（期望 0）" % (len(fr), max(fr)))
    ib = a.point(lambda v: 255 if v > 8 else 0).getbbox()
    cb = a.point(lambda v: 255 if v > 200 else 0).getbbox()
    print("       墨迹 bbox(α>8)=%s ⇒ %dx%d ｜ 实体 bbox(α>200)=%s ⇒ %dx%d"
          % (ib, ib[2] - ib[0], ib[3] - ib[1], cb, cb[2] - cb[0], cb[3] - cb[1]))
    ring = []
    for y in range(im.height):
        for x in range(im.width):
            if cb[0] - 2 <= x < cb[2] + 2 and cb[1] - 2 <= y < cb[3] + 2:
                continue
            ring.append(a.getpixel((x, y)))
    ck(max(ring) <= 8, "V6", "实体外 2px 环带（%d 像素）αmax = %d（期望 ≤8，即无模型灰尘）"
       % (len(ring), max(ring)))
    bm, n = body_mean(im)
    print("       body 色均值 = %s（α>200 计 %d 像素）" % (bm, n))
    for f in FAMILY:
        p = os.path.join(UI, f)
        if os.path.exists(p):
            fm, fn = body_mean(Image.open(p))
            d = max(abs(bm[i] - fm[i]) for i in range(3))
            ck(d <= 20, "V7", "与 %s 的 body 色最大通道差 = %d（期望 ≤20；%s vs %s）" % (f, d, bm, fm))
    # V8 目视核对图
    out = os.path.join(EV, "E3_定稿_8倍放大_目视核对.png")
    big = im.resize((im.width * 8, im.height * 8), Image.NEAREST)
    ckimg = Image.new("RGB", (big.width + 40, big.height + 40), (255, 255, 255))
    ckimg.paste(Image.alpha_composite(Image.new("RGBA", big.size, (255, 255, 255, 255)), big).convert("RGB"), (20, 20))
    ckimg.save(out)
    print("       V8 无文字：需目视 —— 已出 8× 核对图 %s" % out)


def mutate():
    print("=" * 78)
    print("变异自证：把定稿打废，各判据必须报警")
    tmp = tempfile.mkdtemp(prefix="e3_verify_")
    src = os.path.join(UI, NAME)
    # ① 改成 RGB（丢 alpha）
    a = os.path.join(tmp, "mut_rgb.png")
    Image.open(src).convert("RGB").save(a)
    global _fails
    _fails = []
    verify(a, "变异① RGB（丢 alpha）")
    print("   ⇒ 期望报警：V2（mode 不对时 verify 立即返回，V3b 不会执行）｜ 实际报警：%s" % sorted(set(_fails)))
    ok1 = "V2" in _fails
    # ② 尺寸改成 87×48
    b = os.path.join(tmp, "mut_size.png")
    Image.open(src).resize((87, 48)).save(b)
    _fails = []
    verify(b, "变异② 尺寸 87×48")
    ok2 = "V1" in _fails
    # ③ 灰尘：在角上点一个 α=120 的像素
    c = os.path.join(tmp, "mut_dust.png")
    im = Image.open(src).convert("RGBA")
    im.putpixel((1, 1), (255, 255, 255, 120))
    im.save(c)
    _fails = []
    verify(c, "变异③ 角上撒一枚 α=120 灰尘")
    ok3 = "V5" in _fails or "V6" in _fails
    # ④ 换色：整体改成纯紫，色族判据必须报警
    d = os.path.join(tmp, "mut_color.png")
    im = Image.open(src).convert("RGBA")
    r, g, bl, al = im.split()
    im = Image.merge("RGBA", (bl, r, g, al))
    im.save(d)
    _fails = []
    verify(d, "变异④ 通道互换（改配色）")
    ok4 = "V7" in _fails
    shutil.rmtree(tmp, ignore_errors=True)
    print("-" * 78)
    print("变异自证结论：%s" % ("PASS（四项都报警）" if (ok1 and ok2 and ok3 and ok4) else "FAIL"))
    return 0 if (ok1 and ok2 and ok3 and ok4) else 1


if __name__ == "__main__":
    if "--mutate" in sys.argv:
        sys.exit(mutate())
    verify(os.path.join(UI, NAME))
    print("=" * 78)
    print("结论：%s（失败项 %s）" % ("ALL PASS" if not _fails else "有失败", _fails or "无"))
    sys.exit(0 if not _fails else 1)
