# -*- coding: utf-8 -*-
r"""crop_grouplabels.py —— 从巡演导图裁出「番外组名标签」左栏并放大（目视判读用）

用法：python _工作\ISSUE-20260927-06_番外组名\crop_grouplabels.py <源PNG> <输出PNG>
只读源图、只写输出图（两个路径都由参数给出）。
"""
import sys

from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
# 入口列在左侧（entry-side=left）：col_x = 视口左缘 60，标签 333×38
# 标签 y = ey + 48 + 4（ey ∈ {190,285,380,475,570,665}）⇒ 覆盖 242..755
BOX = (30, 180, 420, 780)
SCALE = 3

im = Image.open(src).convert("RGB")
crop = im.crop(BOX)
crop = crop.resize((crop.width * SCALE, crop.height * SCALE), Image.NEAREST)
crop.save(dst)
print("源=%s %s -> 裁 %s ×%d -> %s %s"
      % (src, im.size, BOX, SCALE, dst, crop.size))
