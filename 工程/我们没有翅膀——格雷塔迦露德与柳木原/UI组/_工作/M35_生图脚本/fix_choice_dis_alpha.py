# -*- coding: utf-8 -*-
r"""修复 `x_ui_choice_dis.png` 的「整幅灰底」导出缺陷（M35 一审 Major-1）。

■ 缺陷（可复现的量化）
  `x_ui_choice_dis.png`（1135×105）四角像素 = **`(114,114,114,114)`**，`alpha==0` 占比 **0.00%**；
  而同批同尺寸的 `x_ui_choice_off.png` / `x_ui_choice_over.png` 四角 = `(0,0,0,0)`、`alpha==0` 占
  0.36% / 0.32%。三者的 **`alpha==255` 占比完全相同（72.40%）** ⇒ 胶囊美术本身一致，
  `dis` 只是多垫了一层**整幅半透明灰底** `(114,114,114,114)`。
  （全部 40 个 state_assets 涉及的 39 个 PNG 里，只有这一个是「零透明像素 + 四角同值」。）

  该缺陷来自 M34 的素材重映射，此前 `pressed` 从未被绘制故未显形；M35 打通按下态后，
  在选择题上会画出一块**硬边灰色矩形**（证据 `_工作\M35_证据\M35_按下态_探针A_整屏.png`）。

■ 修法：**反预乘还原**（不是简单抠掉灰底）
  模型：`C_out = C_art·a + P·(1-a)`，`A_out = a + p·(1-a)`，其中 `P=(114,114,114)`、`p = 114/255`。
  反解：`a = (A_out - p) / (1 - p)`，`C_art = (C_out - P·(1-a)) / a`（a=0 处直接置全透明）。
  这样**抗锯齿边也能精确还原**（若只用「颜色等于 (114,114,114) 就置透明」的掩码法，
  胶囊外缘一圈半混合像素会残留灰色描边）。

■ 验收（脚本自带断言）
  · 四角变为 (0,0,0,0)；`alpha==0` 占比回到 ~0.3%（与 off/over 同量级）；
  · `alpha==255` 像素数**必须保持不变**（= 86287），即胶囊本体一个像素都没动；
  · 输出仍是 RGBA、尺寸不变。
  ⚠️ 若日后确认这层灰底是**有意的「禁用」设计**，用 `git checkout` 回滚本文件即可
     （资产已入库，git 即备份）。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
PATH = os.path.join(UI, "krkr", "assets", "ui", "x_ui_choice_dis.png")
REF = [os.path.join(UI, "krkr", "assets", "ui", n)
       for n in ("x_ui_choice_off.png", "x_ui_choice_over.png")]

PLATE = np.array([114.0, 114.0, 114.0])
ALPHA_P = 114.0 / 255.0


def stats(a):
    al = a[..., 3]
    return dict(zero=float((al == 0).mean() * 100),
                full=int((al == 255).sum()),
                corners=[tuple(int(v) for v in a[y, x]) for y, x in ((0, 0), (-1, -1))])


def main():
    im = Image.open(PATH).convert("RGBA")
    a = np.array(im).astype(np.float64)
    before = stats(np.array(im))

    print("修复前：%s" % before)
    for r in REF:
        ra = np.array(Image.open(r).convert("RGBA"))
        print("  参照 %-22s alpha==0 %.2f%%  alpha==255 %d"
              % (os.path.basename(r), (ra[..., 3] == 0).mean() * 100, int((ra[..., 3] == 255).sum())))

    rgb = a[..., :3]
    A = a[..., 3] / 255.0
    art_a = np.clip((A - ALPHA_P) / (1.0 - ALPHA_P), 0.0, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        art_rgb = (rgb - PLATE * (1.0 - art_a)[..., None]) / np.where(art_a > 0, art_a, 1.0)[..., None]
    art_rgb = np.clip(art_rgb, 0.0, 255.0)
    art_rgb[art_a <= 0] = 0.0
    art_a[art_a <= 1e-6] = 0.0

    out = np.dstack([art_rgb, art_a * 255.0]).round().astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    img.save(PATH)
    after = stats(np.array(Image.open(PATH).convert("RGBA")))

    print("修复后：%s" % after)
    ok_corner = after["corners"] == [(0, 0, 0, 0), (0, 0, 0, 0)]
    ok_body = after["full"] == before["full"]
    ok_zero = 0.2 <= after["zero"] <= 0.6
    print("  四角归零：%s ｜ 胶囊本体未动（alpha==255 数不变）：%s ｜ alpha==0 量级回到 0.2–0.6%%：%s"
          % (ok_corner, ok_body, ok_zero))
    if not (ok_corner and ok_body and ok_zero):
        print("  ✗ 断言未过 —— 请勿提交，先查参数")
        return 1
    print("  ✓ 全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
