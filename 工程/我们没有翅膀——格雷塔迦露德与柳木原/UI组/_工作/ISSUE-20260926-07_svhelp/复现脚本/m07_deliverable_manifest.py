# -*- coding: utf-8 -*-
r"""ISSUE-20260926-07（模块 B）· 生成「AI 中文化交付集清单」（入库基线）

用途：为 `PSV系统UI参考\AI中文化\`（该目录整目录被 `.gitignore` 排除、不入库）的
**交付集**建立一份可入库的收货凭据与基线——层级 / 文件名 / 宽 / 高 / md5。

产出：`UI组\PSV系统UI参考\AI中文化_交付集清单.tsv`（UTF-8，制表符分隔）
      header：层级 \t 文件名 \t 宽 \t 高 \t md5
      数据行：1x 47 行 + 2x 47 行 = 94 行

只读输入，不写 AI中文化\ 内的任何文件。可重复运行（幂等：同输入同输出）。
用法：
  python _工作/ISSUE-20260926-07_svhelp/复现脚本/m07_deliverable_manifest.py
"""
import hashlib
import os

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "AI中文化")
OUT = os.path.join(BASE, "PSV系统UI参考", "AI中文化_交付集清单.tsv")

from PIL import Image  # noqa: E402


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    lines = ["层级\t文件名\t宽\t高\tmd5"]
    counts = {}
    for layer in ("1x", "2x"):
        d = os.path.join(SRC, layer)
        files = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
        counts[layer] = len(files)
        for name in files:
            p = os.path.join(d, name)
            w, h = Image.open(p).size
            lines.append("%s\t%s\t%d\t%d\t%s" % (layer, name, w, h, md5_of(p)))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote %s" % OUT)
    print("data rows = %d (1x=%d, 2x=%d)" % (len(lines) - 1, counts["1x"], counts["2x"]))


if __name__ == "__main__":
    main()
