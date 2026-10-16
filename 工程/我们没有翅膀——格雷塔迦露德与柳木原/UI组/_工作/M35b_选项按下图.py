# -*- coding: utf-8 -*-
r"""选项（choices）**专用按下图**（用户 2026-09-22 裁定「另出一版专用按下图」）。

■ 背景
  `ch.hit_1/2/3` 原来的 `state_assets.pressed` 指向 `x_ui_choice_dis.png`（**"禁用"美术**），
  于是「按下选项」看起来像「被禁用」——语义错了（这是 M34 素材重映射时按手上素材填的）。
  用户裁定：另出一版真正的按下图。

■ 配方（与标题菜单按下图**同一口径**：从**常态版**派生）
  复用 ``_工作\M35_生图脚本\btn_states.py`` 的 ``pressed()``：
      RGB ×0.80 ｜ alpha ×1.00（保留原 alpha，不降——降了会发灰透底）｜ 整体缩 0.96（居中，画布不变）
      ＋ 亮白 2px 描边（``P_RING=2 / P_RING_BLUR=0.6``）
  派生基准 = **常态版** `x_ui_choice_off.png`（**不是**悬停版）。
  （初版曾从悬停版派生，实测**读不出"按下"**——悬停版已提亮 30%，再 ×0.80 正好抵消回常态亮度；
    详见 `btn_states.py` 的 ``PRESS_FROM_HOVER`` 注释。本 docstring 曾与此相反，已订正。）

■ ★ M4 修 import（Minor-6）——**为什么必须显式指向仓内那份**
  本脚本原来只 ``import btn_states``，而 ``_工作\`` 下**没有**这个模块：它能跑通纯属
  ``工具\lyai-image-api\`` 这个**未入库（`.gitignore` 忽略）**目录恰好存在于本机。
  干净检出（新 worktree / 别人机器）下 `工具\` 不存在 ⇒ `ModuleNotFoundError`，
  「可复现管线」这条路径**按原样跑不起来**。
  更糟的是那份副本当时**更新于仓内副本**（白晕/描边/`PRESS_FROM_HOVER` 都在它那边）——
  即仓内 `M35_生图脚本\btn_states.py` 是旧的，用它重算**与盘上素材 md5 全不同**。
  M4 处置：①把出图那份**逐字节同步入仓**（同步后 `_工作\M35_生图脚本\btn_states.py` 重算
  `_on`/`_press` 全部 14/14 逐字节相同）；②本脚本改为**显式把仓内 `M35_生图脚本` 插到
  `sys.path` 最前**，并断言解析到的 `btn_states.__file__` 就在该目录 —— 指向别处即拒跑。

■ 产物
  `krkr/assets/ui/x_ui_choice_press.png`（与 off/over 同为 1135×105，画布不变）
  接线：把 `ch.hit_1/2/3` 的 `state_assets.pressed` 由 `x_ui_choice_dis.png` 改为它。
        `x_ui_choice_dis.png` **保留**（它确实是"禁用"态美术，日后选择支禁用会用到，不删）。

■ 用法
  python M35b_选项按下图.py           # 出图并写盘
  python M35b_选项按下图.py --dry     # 只重算 + 比对盘上 md5，**不写盘**（可复现性自证）
"""
import os, sys, io, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))              # ...\UI组\_工作
UI = os.path.dirname(HERE)                                     # ...\UI组
SCRIPTS = os.path.join(HERE, "M35_生图脚本")                    # ★ 仓内配方所在目录（tracked）

# ★ 仓内配方目录插到最前（先于 `工具\lyai-image-api\`，后者是未入库副本）
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image
import btn_states as B          # 复用同一份 pressed() 配方，避免两处各写一套

A = os.path.join(UI, "krkr", "assets", "ui")


def _check_module():
    r"""断言 btn_states 解析到**仓内** `_工作\M35_生图脚本\`，否则拒跑。"""
    got = os.path.abspath(getattr(B, "__file__", "") or "")
    if os.path.dirname(got) != os.path.abspath(SCRIPTS):
        print("✗ btn_states 解析到了非仓内副本：%s" % (got or "(未知)"))
        print("  期望：%s" % os.path.join(SCRIPTS, "btn_states.py"))
        print("  （未入库的 `工具\\lyai-image-api\\` 副本不得再承载独有改动——见本文件 docstring）")
        return False
    return True


def main():
    dry = "--dry" in sys.argv
    if not _check_module():
        return 1
    print("配方模块：%s（md5 %s）" % (
        os.path.abspath(B.__file__),
        hashlib.md5(io.open(B.__file__, "rb").read()).hexdigest()))
    print("  MAKE_PRESSED=%s ｜ PRESS_FROM_HOVER=%s ｜ P_RGB=%s P_ALPHA=%s P_SCALE=%s P_RING=%s"
          % (getattr(B, "MAKE_PRESSED", "?"), getattr(B, "PRESS_FROM_HOVER", "?"),
             getattr(B, "P_RGB", "?"), getattr(B, "P_ALPHA", "?"),
             getattr(B, "P_SCALE", "?"), getattr(B, "P_RING", "?")))

    off = os.path.join(A, "x_ui_choice_off.png")
    over = os.path.join(A, "x_ui_choice_over.png")
    dst = os.path.join(A, "x_ui_choice_press.png")
    if not os.path.exists(off):
        print("✗ 缺基准图 %s" % off); return 1
    # ★ 从**常态**（x_ui_choice_off）派生，与标题菜单按下图同一口径（见 btn_states.py 的 PRESS_FROM_HOVER）。
    base = Image.open(off).convert("RGBA")
    src = "x_ui_choice_off.png"
    out = B.pressed(base)

    def png_bytes(im):
        bio = io.BytesIO(); im.save(bio, format="PNG"); return bio.getvalue()

    def stat(p):
        a = np.array(Image.open(p).convert("RGBA"))
        return (a.shape[1], a.shape[0], int((a[..., 3] == 255).sum()), float((a[..., 3] == 0).mean() * 100))

    b, c = stat(off), stat(over)
    d = stat(dst) if os.path.exists(dst) else None
    print("  %-26s %dx%d  alpha255=%6d  alpha0=%.2f%%" % (("常态 " + src,) + b))
    print("  %-26s %dx%d  alpha255=%6d  alpha0=%.2f%%" % (("悬停 x_ui_choice_over.png",) + c))
    if d:
        print("  %-26s %dx%d  alpha255=%6d  alpha0=%.2f%%" % (("按下（盘上现值）",) + d))

    ok = out.size == base.size and (np.array(out)[..., 3] == 255).sum() > 0
    print("  画布一致：%s ｜ 非空：%s" % (out.size == base.size, (np.array(out)[..., 3] == 255).sum() > 0))

    if dry:
        if not os.path.exists(dst):
            print("  （--dry：盘上无 %s，无法比对）" % os.path.basename(dst)); return 0
        same = hashlib.md5(png_bytes(out)).hexdigest() == hashlib.md5(io.open(dst, "rb").read()).hexdigest()
        print("  --dry：重算结果与盘上 %s **%s**（md5 %s）"
              % (os.path.basename(dst), "逐字节相同" if same else "不同",
                 hashlib.md5(io.open(dst, "rb").read()).hexdigest()))
        return 0 if same else 1

    out.save(dst)
    print("  ✓ 产出 %s（由 %s 派生）" % (dst, src))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
