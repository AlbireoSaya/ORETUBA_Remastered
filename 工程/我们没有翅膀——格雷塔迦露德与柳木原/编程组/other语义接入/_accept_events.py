# -*- coding: utf-8 -*-
r"""_accept_events.py —— off vs tier1 的 **stage 事件级**差分（补充 PNG 的回归口径）。

PNG 走 `--no-story-assets` + 固定截图行（1–6/200/400/末），立绘多不渲染 ⇒ 不便直接看落位差。
本器从两份已构建的 `scene_*.tjs` 的 `stage[]` 解析事件，按 **`(seq, op, slot, fam)` 折叠**
（同键的 x 不同视为「x 迁移」，不计入新增/删除），输出：

  · `added`   ：tier1 有、off 无的事件（＝接入直接新发 + 真正新增的次生）
  · `removed` ：off 有、tier1 无的事件（正常应为 0）
  · `x_shift` ：同键但 x 变了（＝既有 `chr_expr`/`chr_place` 因在场集合变化被重排）

用法：
  python -X utf8 编程组/other语义接入/_accept_events.py \
      --off 编程组/other语义接入/验收/_stage_off \
      --tier1 编程组/other语义接入/验收/_stage_tier1 \
      --out 编程组/other语义接入/验收/stage事件差分.tsv
"""
from __future__ import annotations

import argparse
import collections
import io
import os
import re

RE_EV = re.compile(r'%\s*\[\s*seq:(-?\d+),\s*op:"([^"]*)",\s*slot:(-?\d+),\s*fam:"([^"]*)",'
                   r'\s*t:"[^"]*",\s*x:(-?\d+),\s*y:(-?\d+),\s*w:(-?\d+),\s*h:(-?\d+),\s*z:(-?\d+)')


def parse_scene(path):
    return [(int(m.group(1)), m.group(2), int(m.group(3)), m.group(4), int(m.group(5)))
            for m in RE_EV.finditer(io.open(path, encoding="utf-8", errors="replace").read())]


def read_dir(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        if fn.startswith("scene_") and fn.endswith(".tjs"):
            out[fn[len("scene_"):-len(".tjs")]] = parse_scene(os.path.join(d, fn))
    return out


def fold(evs):
    m = collections.defaultdict(list)
    for seq, op, slot, fam, x in evs:
        m[(seq, op, slot, fam)].append(x)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--off", required=True)
    ap.add_argument("--tier1", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    off, t1 = read_dir(a.off), read_dir(a.tier1)
    rows = []
    for sid in sorted(set(off) | set(t1)):
        o, n = fold(off.get(sid, [])), fold(t1.get(sid, []))
        for k in n:
            if k not in o:
                for x in n[k]:
                    rows.append([sid, sid.split("_", 1)[0], "added", k[0], k[1], k[2], k[3], x])
            elif sorted(n[k]) != sorted(o[k]):
                rows.append([sid, sid.split("_", 1)[0], "x_shift", k[0], k[1], k[2], k[3], n[k][0]])
        for k in o:
            if k not in n:
                rows.append([sid, sid.split("_", 1)[0], "removed", k[0], k[1], k[2], k[3], o[k][0]])

    with io.open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(["scene_id", "src", "delta", "seq", "op", "slot", "fam", "x"]) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")

    for kind in ("added", "removed", "x_shift"):
        sel = [r for r in rows if r[2] == kind]
        print("%-8s %4d 条  %s" % (kind, len(sel), dict(collections.Counter(r[4] for r in sel))))


if __name__ == "__main__":
    main()
