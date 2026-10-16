# -*- coding: utf-8 -*-
r"""_dump_ev.py <stage_dir> <scene_id> <seq_lo> <seq_hi> —— 打印区间内的 stage 事件（只读）。"""
import io, re, sys

RE_EV = re.compile(r'%\s*\[\s*seq:(-?\d+),\s*op:"([^"]*)",\s*slot:(-?\d+),\s*fam:"([^"]*)",'
                   r'\s*t:"([^"]*)",\s*x:(-?\d+),\s*y:(-?\d+),\s*w:(-?\d+),\s*h:(-?\d+),\s*z:(-?\d+)')


def main():
    d, sid, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    s = io.open("%s/scene_%s.tjs" % (d, sid), encoding="utf-8", errors="replace").read()
    print("### %s %s [%d,%d]" % (d, sid, lo, hi))
    for m in RE_EV.finditer(s):
        seq = int(m.group(1))
        if lo <= seq <= hi:
            print("  seq=%-4d op=%-10s slot=%-3s fam=%-4s x=%-5s w=%-5s t=%s"
                  % (seq, m.group(2), m.group(3), m.group(4), m.group(6), m.group(8),
                     m.group(5).split("/")[-1]))


if __name__ == "__main__":
    main()
