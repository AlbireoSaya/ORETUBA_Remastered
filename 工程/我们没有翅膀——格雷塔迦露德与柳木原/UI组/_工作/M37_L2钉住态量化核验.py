# -*- coding: utf-8 -*-
r"""M37 · L2 核验：钉住叠层（opacity 255）是否**等于**该 icon 的悬停材质（无重影）

■ 判据（量化，不靠肉眼）
  引擎导出的 quickbar 屏 PNG 里，锁定 icon 所在矩形（64×64，从**数据**读出 x/y/w/h）：
    · 钉住态（`qbar_pin=1`，`quick.pin_mark` 叠在常态徽章之上）
    · 悬停态（同 icon 的 `_on` 材质 —— 用按压探针 `UIScrPressProbe=quick.hit_save`
      那一轮的 save icon 作对照，两态几何已由 G1 归一化）
  分别与该 icon 的两张素材（`_on` / 常态）逐像素比：
    MSE(钉住态, lock_on)  应 ≈ 0（叠层 = 悬停材质本身）
    MSE(钉住态, lock_normal) 应远大于前者（否则说明叠层没盖住常态图）
  并且把「与 `_on` 的差异图」的最大差分框打印出来 —— 若存在**半像素错位/双线**，
  差异会集中在描边上（最大差分与差异像素占比明显大于 0）。

■ 前置（两轮引擎巡演产物，缺一则本脚本报「缺截图」退出码 2）
  1. `krkr\run_quickbar.bat`（强制 quickbar=expanded / qbar_tip=lock / **qbar_pin=1**）
     → `临时\ui_run_quickbar\runtime\savedata\shot_24_quickbar.png`（= 钉住态）
  2. 复制上一轮目录为 `临时\ui_run_qbpress`，把 `game\quick_flags.tjs` 的 `qbar_pin` 置空、
     `qbar_tip` 置 `save`，再写 `game\press_probe.tjs` = `UIScrPressProbe = "quick.hit_save";`
     → `临时\ui_run_qbpress\runtime\savedata\shot_24_quickbar.png`（= 悬停态对照）

■ 用法
    python _工作\M37_L2钉住态量化核验.py
"""
import io
import json
import os
import sys

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))          # …\UI组\_工作
UI = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
EV = os.path.join(HERE, "ISSUE-20260923-01_G2_证据")

RUNS = {
    "钉住态": os.path.join(WT, "临时", "ui_run_quickbar", "runtime", "savedata", "shot_24_quickbar.png"),
    "悬停态": os.path.join(WT, "临时", "ui_run_qbpress", "runtime", "savedata", "shot_24_quickbar.png"),
}


def cell(im, x, y, w, h):
    return im.crop((x, y, x + w, y + h)).convert("RGB")


def mse(a, b):
    d = ImageChops.difference(a, b).convert("L")
    px = list(d.getdata())
    return sum(v * v for v in px) / float(len(px)), max(px), sum(1 for v in px if v > 8) / float(len(px))


def main():
    d = json.load(io.open(os.path.join(UI, "layout", "screens", "35_quickbar.json"),
                          encoding="utf-8"))
    idx = {e["id"]: e for e in d["elements"]}
    boxes = {}
    for name, key in (("lock", "lock"), ("save", "save")):
        ic = idx["quick.ic_%s" % key]
        boxes[name] = (ic["x"], ic["y"], ic["w"], ic["h"])
    art = {k: Image.open(os.path.join(ASSETS, "x_ui_qbicon_%s.png" % k)).convert("RGB")
           for k in ("lock", "lock_on", "save", "save_on")}

    print("=" * 78)
    print("L2 核验：钉住叠层 vs 悬停材质（几何取自 layout 数据，逐像素）")
    print("=" * 78)
    ok = True
    for tag, path in RUNS.items():
        if not os.path.exists(path):
            print("!! 缺截图：%s" % path)
            return 2
        im = Image.open(path)
        print("\n[%s] %s" % (tag, os.path.basename(path)))
        for key, want_on in (("lock", True), ("save", True)):
            x, y, w, h = boxes[key]
            c = cell(im, x, y, w, h)
            m_off, mx_off, frac_off = mse(c, art["%s_on" % key])
            m_nor, mx_nor, frac_nor = mse(c, art[key])
            verdict = ("= 悬停材质（_on）" if m_off < 8 and m_off < m_nor / 4 else
                       "= 常态图" if m_nor < 8 and m_nor < m_off / 4 else "两者都不像（需查）")
            print("   %-6s icon(%d,%d,%d,%d)：MSE vs _on=%8.1f(max %3d, 差像素 %.1f%%) ｜ "
                  "MSE vs 常态=%8.1f(max %3d, 差像素 %.1f%%)  ⇒ %s"
                  % (key, x, y, w, h, m_off, mx_off, 100 * frac_off, m_nor, mx_nor, 100 * frac_nor,
                     verdict))
            if tag == "钉住态" and key == "lock":
                ok &= (m_off < 8 and frac_off < 0.02)
            if tag == "悬停态" and key == "save":
                ok &= (m_off < 8 and frac_off < 0.02)
            if tag == "悬停态" and key == "lock":
                ok &= (m_nor < 8)
        # 放大裁切（4×），供人眼与 vision 复核
        crop = im.crop((boxes["lock"][0] - 140, boxes["lock"][1] - 10, 1920, 160)).convert("RGB")
        crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
        out = os.path.join(EV, "G2_%s_锁定项放大_halo64.png" % ("钉住态" if tag == "钉住态" else "悬停态对照"))
        crop.save(out)
        print("   放大裁切 -> %s" % os.path.basename(out))
    print("\n结论：%s" % ("钉住态 = 悬停材质、无重影 ✓" if ok else "**有异常，见上表** ✗"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
