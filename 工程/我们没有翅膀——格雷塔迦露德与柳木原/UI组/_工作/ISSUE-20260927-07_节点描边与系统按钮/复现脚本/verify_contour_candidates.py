# -*- coding: utf-8 -*-
"""回读复核（只读）：解析轮廓候选件的尺寸 / RGB 不变性 / 描边件 alpha 不变性 / 平台带 / 掩码连续性。

从**磁盘上的产出文件**回读，独立于生成器内部状态。
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image                                                    # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
OUT = UI / "_工作" / "ISSUE-20260927-07_节点描边与系统按钮" / "取证" / "圆角候选"
BACKUP = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "原形备份"
CUR = UI / "krkr" / "assets" / "ui"
KINDS = ("section", "select", "frag")
SPRITE = {"section": (236, 65), "select": (263, 65), "frag": (228, 65)}
TAGS = ("r原件", "r12", "r16", "r20")
SOLID = 230


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def main():
    print("=" * 112)
    print("回读复核：候选件（磁盘文件）")
    print("=" * 112)
    ok_all = True
    for k in KINDS:
        src = Image.open(BACKUP / ("x_ui_node_%s_off.png" % k)).convert("RGBA")
        rgb0 = np.asarray(src.convert("RGB"))
        for tag in TAGS:
            p = OUT / ("候选_解析轮廓_x_ui_node_%s_off_%s.png" % (k, tag))
            if not p.exists():
                print("  [缺] %s" % p.name)
                ok_all = False
                continue
            im = Image.open(p).convert("RGBA")
            a = np.asarray(im.getchannel("A"))
            rgb = np.asarray(im.convert("RGB"))
            size_ok = im.size == SPRITE[k]
            rgb_ok = bool((rgb == rgb0).all())
            mask = a >= SOLID
            # 掩码连续性：底边最下一行
            yb = int(round(0))
            ys = np.where(mask.any(axis=1))[0]
            last = ys.max()
            row = np.where(mask[last])[0]
            holes = [int(x) for x in range(row.min(), row.max() + 1) if not mask[last, x]]
            plat = int((a == 60).sum())
            ok_all &= size_ok and rgb_ok
            print("  %-8s %-6s size=%s mode=%s RGB==原件:%s ｜ alpha[%d..%d] alpha=60 的像素=%d "
                  "｜ 末实体行 y=%d 缺口=%s"
                  % (k, tag, im.size, size_ok, rgb_ok, int(a.min()), int(a.max()), plat,
                     int(last), holes[:6]))
    print("\n" + "=" * 112)
    print("回读复核：select 描边件（只应改环带 RGB；alpha 必须逐字节等于同档候选件）")
    print("=" * 112)
    sys.path.insert(0, str(UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "复现脚本"))
    import make_node_variant_a as MF
    for tag in TAGS:
        base = Image.open(OUT / ("候选_解析轮廓_x_ui_node_select_off_%s.png" % tag)).convert("RGBA")
        st = Image.open(OUT / ("候选_解析轮廓_x_ui_node_select_off_%s_描边.png" % tag)).convert("RGBA")
        efc = Image.open(OUT / ("候选_解析轮廓_x_ui_node_select_off_%s_生效色_描边.png" % tag)).convert("RGBA")
        aB, aS = np.asarray(base.getchannel("A")), np.asarray(st.getchannel("A"))
        rgbB = np.asarray(base.convert("RGB")).astype(int)
        rgbS = np.asarray(st.convert("RGB")).astype(int)
        rgbE = np.asarray(efc.convert("RGB")).astype(int)
        diff = np.abs(rgbS - rgbB).max(axis=2)
        cov = MF.stroke_coverage(base.getchannel("A"), width=MF.STROKE_W)
        outside = (diff > 0) & (cov <= 0)
        aE = np.asarray(efc.getchannel("A"))
        print("  %-6s alpha 逐字节相同=%s ｜ 描边改动像素 %d（全部落在环带 cov>0 内=%s，环带外改动 %d）"
              " ｜ 环带像素数 cov>0 = %d ｜ 生效色件 alpha 相同=%s"
              % (tag, bool((aB == aS).all()), int((diff > 0).sum()), bool(not outside.any()),
                 int(outside.sum()), int((cov > 0).sum()), bool((aB == aE).all())))
        _ = rgbE
    # 正式件的环带规模（同口径对照）
    for k in ("select",):
        p = CUR / ("x_ui_node_%s_off.png" % k)
        im = Image.open(p).convert("RGBA")
        cov = MF.stroke_coverage(im.getchannel("A"), width=MF.STROKE_W)
        print("  对照：正式件 %s 的环带像素数 cov>0 = %d" % (p.name, int((cov > 0).sum())))
    print("\n" + "=" * 112)
    print("对照：上一轮（min 削减式）与正式件的 md5（应与本轮前保持不变）")
    print("=" * 112)
    for k in KINDS:
        for tg in ("r8", "r12", "r16"):
            for suf in ("", "_描边", "_生效色_描边"):
                p = OUT / ("候选_x_ui_node_%s_off_%s%s.png" % (k, tg, suf))
                if p.exists():
                    print("  %-42s %s" % (p.name, md5(p)))
    for k in KINDS:
        p = CUR / ("x_ui_node_%s_off.png" % k)
        print("  %-42s %s  (正式件，只读)" % (p.name, md5(p)))
    print("\n全部候选件尺寸/RGB 检查：%s" % ("通过" if ok_all else "失败"))


if __name__ == "__main__":
    main()
