# -*- coding: utf-8 -*-
"""verify_delivery_readback.py —— 「正式落地」六件素材的**独立复核**（只读，不写素材）。

与生产脚本 `make_node_variant_a.py` 的 `build()` **不走同一段代码**：
  · alpha：直接调候选档 CN 的 `rect_of / collect_profiles / shape_fields / synth` 重算；
  · RGB ：用「同 RGB、alpha 全 0」的图跑 `recolor`（证明 alpha 不参与改色）后逐像素比；
  · 描边：用 CN 的 `stroke_coverage` 取环带，环带外必须零改动、alpha 必须逐字节等于无描边件；
  · 半径：CN 的 `radius_corner`（相切一维搜索口径）。

用法：
    python verify_delivery_readback.py
退出码 0 = 全通过。
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image                                                    # noqa: E402

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
REPRO5 = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "复现脚本"
BACKUP = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "原形备份"
ASSETS = UI / "krkr" / "assets" / "ui"
sys.path.insert(0, str(REPRO5))
import make_node_variant_a as MF                                          # noqa: E402
import make_node_contour_candidates as CN                                 # noqa: E402

KINDS = ("section", "select", "frag")
STATES = ("off", "on")
fails = []


def analytic(src):
    a = np.asarray(src.getchannel("A")).astype(np.float64)
    rect = CN.rect_of(a)
    prof, _ = CN.collect_profiles(a, rect, MF.RADIUS + 2)
    f = CN.shape_fields(src.size[0], src.size[1], rect, (MF.RADIUS,) * 4)
    return np.rint(np.clip(CN.synth(prof, f), 0, 255)).astype(np.uint8), rect


print("=" * 100)
print("独立复核 · 六件正式素材（只读；实现路径与 build() 不同）")
print("=" * 100)
for kind in KINDS:
    for state in STATES:
        fn = "x_ui_node_%s_%s.png" % (kind, state)
        src = Image.open(BACKUP / fn).convert("RGBA")
        disk = Image.open(ASSETS / fn).convert("RGBA")
        md5 = hashlib.md5((ASSETS / fn).read_bytes()).hexdigest()

        # ① alpha == CN 重算的解析结果
        al, rect = analytic(src)
        a_disk = np.asarray(disk.getchannel("A")).astype(np.uint8)
        alpha_ok = al.tobytes() == a_disk.tobytes()
        if not alpha_ok:
            fails.append("%s alpha != 独立重算" % fn)

        # ② 半径（相切一维搜索）
        rm = CN.rect_of(a_disk.astype(np.float64))
        rr = {}
        for c in ("TL", "TR", "BR", "BL"):
            R, _rms, _n = CN.radius_corner(a_disk.astype(np.float64), rm, c)
            rr[c] = R
        rdev = max(abs(rr[c] - MF.RADIUS) for c in rr)
        if rdev > MF.RADIUS_TOL:
            fails.append("%s 半径偏差 %.3f" % (fn, rdev))

        # ③ RGB == recolor(原件)（同 RGB、alpha 全 0 的图跑同一套 recolor）
        hue, sat, vmul, stroke = MF.params_of(kind, state)
        rgb_only = Image.merge("RGBA", (*src.convert("RGB").split(),
                                        Image.new("L", src.size, 0)))
        exp = np.asarray(MF.recolor(rgb_only, hue=hue, sat=sat, vmul=vmul).convert("RGB"), dtype=np.int16)
        got = np.asarray(disk.convert("RGB"), dtype=np.int16)

        extra = ""
        if stroke:
            cov = MF.stroke_coverage(disk.getchannel("A"), width=MF.STROKE_W)
            inside = cov > 0
            outside_bad = int((np.abs(got - exp)[~inside] > 0).sum())
            # ④ 描边：alpha 逐字节 == 无描边件；环带外零改动
            base = MF.recolor(Image.merge("RGBA", (*src.convert("RGB").split(),
                                                   Image.fromarray(al, "L"))), hue=hue, sat=sat, vmul=vmul)
            alpha_eq = base.getchannel("A").tobytes() == disk.getchannel("A").tobytes()
            if outside_bad:
                fails.append("%s 环带外 RGB 改动 %d px" % (fn, outside_bad))
            if not alpha_eq:
                fails.append("%s 描边改了 alpha" % fn)
            extra = ("｜ 环带 %4d px ｜ 环带外 RGB 改动 %d px ｜ alpha==无描边件 %s"
                     % (int(inside.sum()), outside_bad, "OK" if alpha_eq else "FAIL"))
        else:
            bad = int((np.abs(got - exp) > 0).sum())
            if bad:
                fails.append("%s RGB 与 recolor(原件) 差 %d px" % (fn, bad))
            extra = "｜ 无描边 ｜ RGB==recolor(原件) 差 %d px" % bad

        # ⑤ 底边：末端实体行无缺口
        x0, x1 = int(rect[0]) + 20, int(rect[1]) - 19
        row = MF.bottom_solid_row(a_disk.astype(np.float64), rect)
        seg = a_disk[row, x0:x1]
        holes = int((seg < MF.SOLID_THR).sum())
        if holes:
            fails.append("%s 底边 y=%d 缺口 %d 列" % (fn, row, holes))
        notch = ""
        if kind == "select" and state == "off":
            piece = "｜ ★ 原缺口列 x=%d：原件 %d ⇒ 现 %d" % (
                MF.NOTCH_X, int(np.asarray(src.getchannel("A"))[56, MF.NOTCH_X]), int(a_disk[56, MF.NOTCH_X]))
            notch = piece

        print("%-30s %s %s ｜ r=%s 最大偏差 %.3f ｜ alpha==解析 %s%s ｜ 底边 y=%d min=%d 缺口 %d%s"
              % (fn, str(disk.size), md5[:12],
                 " ".join("%s%.2f" % (c, rr[c]) for c in ("TL", "TR", "BR", "BL")), rdev,
                 "OK" if alpha_ok else "FAIL", extra, row, int(seg.min()), holes, notch))

print("=" * 100)
if fails:
    print("结果：**不通过** %d 项" % len(fails))
    for f in fails:
        print("   -", f)
    sys.exit(1)
print("结果：**独立复核全通过**（六件 alpha==解析结果、RGB==recolor(原件)、半径≈%.1f、底边无缺口）" % MF.RADIUS)
sys.exit(0)
