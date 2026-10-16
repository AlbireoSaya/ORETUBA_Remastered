# -*- coding: utf-8 -*-
r"""_sim_stage.py —— 按 ui_staging.tjs 语义离线模拟「某行时各槽位状态」，用于挑选
真正会渲染出差异的截图行。

语义（对照 krkr/game/ui_staging.tjs）：
  · 槽位 0..5 才存在（STAGE_MAX_SLOTS=6）；slot<0 或 slot>=6 的事件被运行期丢弃
    （所以 build 里的 slot:99 事件实际不渲染）。
  · 每行应用 seq <= 行号 的事件（行号 == lines[].sq）。
  · chr_add/chr_expr → 设 asset/x/y/w/h/z、visible=true
  · chr_place       → 仅设 x/y（槽为空则无效果）
  · chr_remove slot>=0 → 隐藏该槽；slot<0 → 清空全部
  · bg/se 忽略（背景不参与立绘比对，且 bg 是另一元素）
输出每行的槽位状态；带 --diff 时并列 off/tier1 并只打印有差异的行。
用法:
  python -X utf8 _sim_stage.py --off <dir> --tier1 <dir> --scene <id> --diff
  python -X utf8 _sim_stage.py --stage <dir> --scene <id> --line <L>
"""
import argparse, io, os, re

RE_EV = re.compile(r'%\s*\[\s*seq:(-?\d+),\s*op:"([^"]*)",\s*slot:(-?\d+),\s*fam:"([^"]*)",'
                   r'\s*t:"([^"]*)",\s*x:(-?\d+),\s*y:(-?\d+),\s*w:(-?\d+),\s*h:(-?\d+),\s*z:(-?\d+)')
RE_LINE = re.compile(r'%\[ k:"[^"]*", sp:"[^"]*", tx:"(.*?)", vo:"[^"]*", sq:(-?\d+) \]')
MAXSLOT = 6


def parse_scene(path):
    s = io.open(path, encoding="utf-8", errors="replace").read()
    evs = []
    for m in RE_EV.finditer(s):
        evs.append(dict(seq=int(m.group(1)), op=m.group(2), slot=int(m.group(3)),
                        fam=m.group(4), t=m.group(5), x=int(m.group(6)), y=int(m.group(7)),
                        w=int(m.group(8)), h=int(m.group(9)), z=int(m.group(10))))
    lines = [(m.group(1), int(m.group(2))) for m in RE_LINE.finditer(s)]
    return evs, lines


def apply_upto(evs, line):
    st = [None] * MAXSLOT   # slot -> dict(asset,x,y,w,h,z,fam) or None
    for e in evs:
        if e["seq"] > line:
            break
        op, sl = e["op"], e["slot"]
        if op in ("bg", "se"):
            continue
        if op == "chr_remove":
            if sl < 0:
                st = [None] * MAXSLOT
            elif 0 <= sl < MAXSLOT:
                st[sl] = None
        elif op == "chr_place":
            if 0 <= sl < MAXSLOT and st[sl] is not None:
                st[sl]["x"] = e["x"]; st[sl]["y"] = e["y"]
        elif op in ("chr_add", "chr_expr", "chr_move"):
            if 0 <= sl < MAXSLOT:
                st[sl] = dict(asset=e["t"].split("/")[-1], x=e["x"], y=e["y"],
                              w=e["w"], h=e["h"], z=e["z"], fam=e["fam"])
    return st


def fmt(st):
    out = []
    for i, v in enumerate(st):
        if v is None:
            out.append("s%d:-" % i)
        else:
            out.append("s%d:%s@%d(w%d)" % (i, v["fam"], v["x"], v["w"]))
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage")
    ap.add_argument("--off")
    ap.add_argument("--tier1")
    ap.add_argument("--scene", required=True)
    ap.add_argument("--line", type=int)
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()

    def load(d):
        return parse_scene(os.path.join(d, "scene_%s.tjs" % a.scene))

    if a.diff:
        oe, ol = load(a.off)
        te, tl = load(a.tier1)
        n = max(len(ol), len(tl))
        print("scene=%s off_ev=%d t1_ev=%d lines off=%d t1=%d" % (a.scene, len(oe), len(te), len(ol), len(tl)))
        shown = 0
        prev = None
        for L in range(1, n + 1):
            so = apply_upto(oe, L)
            st = apply_upto(te, L)
            key = (fmt(so), fmt(st))
            if so != st:
                # 只在「差异首次出现或发生变化」时打印，减少噪声
                if key != prev:
                    print("  L%03d  off[%s]" % (L, fmt(so)))
                    print("        t1 [%s]" % fmt(st))
                    shown += 1
                prev = key
        print("差异行数(状态变化点)=%d" % shown)
    else:
        evs, lines = load(a.stage)
        for L in ([a.line] if a.line else range(1, len(lines) + 1)):
            print("L%03d sq=%s  %s" % (L, lines[L - 1][1] if L <= len(lines) else "?", fmt(apply_upto(evs, L))))


if __name__ == "__main__":
    main()
