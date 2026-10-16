# -*- coding: utf-8 -*-
r"""_map_seq2line.py —— 把 (场, seq) 映射到「巡演行号」。
行号定义 = 场景 lines[] 数组中的 1 基下标（与 uiDialog 播放行一一对应）。
用法: python -X utf8 _map_seq2line.py <stage_dir> <scene_id> [seq ...]
只读。
"""
import io, re, sys

RE_LINE = re.compile(r'%\[ k:"([^"]*)", sp:"([^"]*)", tx:"(.*?)", vo:"([^"]*)", sq:(-?\d+) \]')


def parse_lines(path):
    s = io.open(path, encoding="utf-8", errors="replace").read()
    return [(m.group(5), m.group(1), m.group(3)) for m in RE_LINE.finditer(s)]


def main():
    d, sid = sys.argv[1], sys.argv[2]
    seqs = [int(x) for x in sys.argv[3:]]
    lines = parse_lines("%s/scene_%s.tjs" % (d, sid))
    print("scene=%s lines=%d" % (sid, len(lines)))
    if not seqs:
        for i, l in enumerate(lines, 1):
            print("  L%03d sq=%s k=%s tx=%s" % (i, l[0], l[1], l[2][:50]))
        return
    for q in seqs:
        hits = [i for i, l in enumerate(lines, 1) if int(l[0]) == q]
        print("  seq %d -> line %s  (tx=%s)" % (
            q, hits if hits else "NOT-IN-SCENE",
            lines[hits[0] - 1][2][:50] if hits else ""))


if __name__ == "__main__":
    main()
