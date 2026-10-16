# -*- coding: utf-8 -*-
r"""
W11d / ISSUE-20260918-06 · 任务3：W9 文档事实更正（`otv` 无 `pic` → 实有 119）
================================================================================
W9 的 `资源组\美术\pic族索引.tsv` 与 `背景CG编目.md` 声称「`otv` 无 `pic`」，
实测错误：`krkr素材库\otv\pic\` 有 119 个 PNG（W9 跑在 W4b 补齐 PSV 素材之前）。

本脚本：
  1. 向 `pic族索引.tsv` **追加 119 行** `otv` 记录（按与 W9 同一 `class` 规则归类），
     `usage` 列注明「W11d补录」；行内保持与原表同列同格式。
  2. 打印 `otv` bg 族统计，供 `背景CG编目.md` §2.1 更正引用。
只读源；只写 `资源组\美术\pic族索引.tsv`。幂等（先剔除已有 otv 行再追加）。
"""
import os, re, csv, collections

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
KRKR = os.path.join(BASE, "krkr素材库")
PICIDX = os.path.join(BASE, "美术", "pic族索引.tsv")

from PIL import Image


def cls(s):
    if re.match(r"^bg", s):
        return "bg"
    if re.match(r"^ec", s):
        return "ec"
    if re.match(r"^ef\d", s):
        return "ef"
    if re.match(r"^cin", s):
        return "cin"
    if re.match(r"^wipe", s):
        return "wipe"
    return "other"


def main():
    d = os.path.join(KRKR, "otv", "pic")
    rows = []
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".png"):
            continue
        stem = fn[4:-4]
        im = Image.open(os.path.join(d, fn))
        w, h, m = im.size[0], im.size[1], im.mode
        im.close()
        rows.append(["otv", cls(stem), stem, str(w), str(h), m,
                     "otv/pic/" + fn, str(os.path.getsize(os.path.join(d, fn))),
                     "CG/背景|W11d补录"])
    print("otv/pic PNG =", len(rows))
    print("class 分布:", dict(collections.Counter(r[1] for r in rows)))

    # bg 族编号统计（供 背景CG编目.md §2.1 更正）
    nums = sorted(set(int(re.match(r"^bg(\d+)", r[2]).group(1))
                      for r in rows if re.match(r"^bg\d", r[2])))
    print("bg 编号: 范围 bg%02d–bg%02d, 不同编号 %d 个, 明细 %s" % (
        nums[0], nums[-1], len(nums), ["bg%02d" % n for n in nums]))
    print("bg 非编号件:", [r[2] for r in rows if r[1] == "bg" and not re.match(r"^bg\d", r[2])])

    # 读原表（保留表头与既有行，剔除任何既有 otv 行以保证幂等）
    with open(PICIDX, encoding="utf-8") as f:
        allrows = list(csv.reader(f, delimiter="\t"))
    hdr, body = allrows[0], allrows[1:]
    assert hdr == ["source", "class", "stem", "w", "h", "mode", "out_relpath", "bytes", "usage"], hdr
    body = [r for r in body if r[0] != "otv"]
    print("原表行数（去 otv 后）= %d" % len(body))
    body += rows
    body.sort(key=lambda r: (r[0], r[2]))
    with open(PICIDX, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(hdr)
        w.writerows(body)
    print("pic族索引.tsv 新行数 = %d（含表头 %d）" % (len(body), len(body) + 1))
    print("逐源:", dict(collections.Counter(r[0] for r in body)))


if __name__ == "__main__":
    main()