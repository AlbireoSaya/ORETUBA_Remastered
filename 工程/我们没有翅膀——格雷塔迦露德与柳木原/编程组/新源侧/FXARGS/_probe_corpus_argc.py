#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""_probe_corpus_argc.py —— 只读探针：用**项目自带解码器**（`编程组\工具\decode_sob0.py`）
对**全库 412 个 .sob**（含系统脚本）做命令节点扫描，得每个目标 V 的
**argc 分布 + 逐位值域**。

为什么要这一步：
  * `解出_{ot,otp,otr}.tsv` 只覆盖**剧情语料**（367+59+21 场），系统脚本里的节点不在其中；
    `cross(0x2A150)` 的 21 个节点**全在系统脚本**（config1/config2/gallery/history/saveload）
    ⇒ 只跑 解出_*.tsv 会得到「argc 未知」，无法判「是否读到 argc 之外」。
  * 本探针给出**独立于 M3** 的全库口径（同一项目解码器、同一判据），用于交叉核对 argc。

复跑（只读）：
  python -X utf8 _probe_corpus_argc.py            # 摘要打印
  python -X utf8 _probe_corpus_argc.py --emit     # 出 效果族参数位_全库.tsv
"""
import argparse
import os
import sys
from collections import Counter, defaultdict

G = r"E:/ZCode Workspace/Galgame"
TOOLDIR = G + "/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具"
SCRIPTDIR = G + "/工程/我们没有翅膀/解包/SCRIPT"
sys.path.insert(0, TOOLDIR)
import decode_sob0 as D  # noqa: E402

TARGETS = ["0x1B888", "0x1B69C", "0x19D58", "0x1C330", "0x1BD8C", "0x1B040",
           "0x1AEA0", "0x1A96C", "0x19F9C", "0x7480", "0x10150", "0xFDF4",
           "0x10980", "0x12998", "0x12E94", "0x13300", "0x1107C", "0x2A150",
           "0x1AD18", "0x10428"]
TS = set(int(v, 16) for v in TARGETS)


def scan(root):
    res = defaultdict(lambda: {"argc": Counter(), "pos": defaultdict(
        lambda: {"N": Counter(), "S": Counter()}), "files": Counter()})
    bad = 0
    files = []
    for dirpath, _, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith(".sob"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    for p in files:
        try:
            sob = D.Sob0(p)
        except Exception:
            bad += 1
            continue
        try:
            for wi in sob.command_nodes():
                V = sob.cells[wi + 1]
                if V not in TS:
                    continue
                args = sob.node_args(wi)
                key = "0x%X" % V
                r = res[key]
                r["argc"][len(args)] += 1
                r["files"][os.path.basename(p)] += 1
                for i, (kind, val) in enumerate(args):
                    if kind == "N":
                        v = val & 0xFFFFFFFF
                        r["pos"][i]["N"][v] += 1
                    else:
                        r["pos"][i]["S"][str(val)] += 1
        except Exception:
            bad += 1
    return res, len(files), bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    a = ap.parse_args()
    res, nf, bad = scan(SCRIPTDIR)
    print("== 全库扫描（%s）==  文件 %d（跳过 %d）" % (SCRIPTDIR, nf, bad))
    rows = []
    for v in TARGETS:
        r = res.get(v)
        if not r:
            print("%-9s 节点 0" % v)
            continue
        n = sum(r["argc"].values())
        acs = ",".join("%d×%d" % (k, c) for k, c in sorted(r["argc"].items()))
        print("%-9s 节点 %-6d argc=%s  文件 %d" %
              (v, n, acs, len(r["files"])))
        for i in sorted(r["pos"]):
            nnum = sum(r["pos"][i]["N"].values())
            nstr = sum(r["pos"][i]["S"].values())
            if nnum >= nstr:
                vals = sorted(r["pos"][i]["N"].items())
                if vals:
                    mode, mc = Counter(dict(vals)).most_common(1)[0]
                    desc = "N[%d,%d] 众%d(%d) 去重%d" % (
                        vals[0][0], vals[-1][0], mode, mc, len(vals))
                else:
                    desc = "空"
            else:
                desc = "S " + " / ".join("%r×%d" % (k, c)
                                        for k, c in r["pos"][i]["S"].most_common(5))
            print("     pos%-2d %s" % (i, desc))
            rows.append({"V": v, "n": n, "argc": acs, "pos": i, "vals": desc,
                         "n_files": len(r["files"]),
                         "files": ",".join(sorted(r["files"])[:8])})
    if a.emit:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "效果族参数位_全库.tsv")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write("V\tn_nodes\targc\tpos\tvals\tn_files\tfiles_top\n")
            for r in rows:
                f.write("%s\t%d\t%s\t%d\t%s\t%d\t%s\n" % (
                    r["V"], r["n"], r["argc"], r["pos"], r["vals"], r["n_files"], r["files"]))
        print("-> %s （%d 行）" % (p, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
