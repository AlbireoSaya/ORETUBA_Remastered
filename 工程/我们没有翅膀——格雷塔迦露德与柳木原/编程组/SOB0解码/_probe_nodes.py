# -*- coding: utf-8 -*-
"""_probe_nodes.py — 只读探针：dump 某脚本的命令节点（V/argc/args），用于 slot 归属研究。

用法：
  python -X utf8 _probe_nodes.py --src ot --script s01_06d [--max 400]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "工具"))
sys.dont_write_bytecode = True
import decode_sob0 as D  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, choices=list(D.SOURCES))
    ap.add_argument("--script", required=True)
    ap.add_argument("--max", type=int, default=400)
    a = ap.parse_args()
    spec = D.SOURCES[a.src]
    p = os.path.join(spec["dir"], a.script + spec["ext"])
    sob = D.Sob0(p)
    nodes = sob.command_nodes()
    print("nodes=%d" % len(nodes))
    emp = sob.empty_offsets()
    ctrl_bytes = D.CTRL_BYTES
    for i in nodes[:a.max]:
        V = sob.cells[i + 1]
        k = sob.cells[i + 3]
        args = sob.node_args(i)
        astr = ",".join("%s:%s" % (kk, vv) for kk, vv in args)
        mark = ""
        for kk, vv in args:
            if kk == "S" and vv.encode("cp932", "replace") in ctrl_bytes:
                mark = " <CTRL>"
        print("#%d V=0x%X k=%d argc=%d args=[%s]%s" % (i, V, k, k // 4, astr, mark))


if __name__ == "__main__":
    main()
