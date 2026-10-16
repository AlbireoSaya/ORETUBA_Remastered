#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_value_stats.py —— 只读探针：从 解出_{ot,otr,otp}.tsv 的 evidence 列统计
每个候选 V 的 argc / 逐位值域（数字位：min/max/众数/去重数；串位：top 串）。

⚠️ 解析纪律（任务书点名的新坑）：`args=[…]` **不能用非贪婪正则**——
串实参可含 `]` 与 `,`（受影响 126 行）。正确口径：
  取 `args=[` 到 ` ctrl=` 的**全部内容** + **括号感知的顶层逗号切分** + **不 strip**。

复跑（只读）：
  python -X utf8 _probe_value_stats.py                       # 表内全部目标 V（ot+otr）
  python -X utf8 _probe_value_stats.py --src ot --V 0x1B040  # 单点
  python -X utf8 _probe_value_stats.py --emit                # 出 效果族参数位_值域.tsv
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

G = r"E:/ZCode Workspace/Galgame"
TSVDIR = G + "/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/SOB0解码"

TARGETS = ["0x1B888", "0x1B69C", "0x19D58", "0x1C330", "0x1BD8C", "0x1B040",
           "0x1AEA0", "0x1A96C", "0x19F9C", "0x7480", "0x10150", "0xFDF4",
           "0x10980", "0x12998", "0x12E94", "0x13300", "0x1107C", "0x2A150",
           "0x1AD18", "0x10428"]


def split_args(ev):
    """从 `args=[` 起做**括号感知**解析：`[` 后 depth=1，遇 depth 回 0 即列表结束；
    depth==1 处的顶层逗号切分。**不 strip**（保留串实参原样，含内部空格/`]`/`,`）。
    返回 None 或 list[str]。
    """
    k = ev.find("args=[")
    if k < 0:
        return None
    i = k + 6
    out, cur, depth = [], [], 1
    while i < len(ev):
        ch = ev[i]
        if ch == "]" and depth == 1:
            break
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 1:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    # 末元素为空（`args=[]`）或整体为空时，返回 []
    if len(out) == 1 and out[0] == "":
        return []
    return out


VAL_RE = re.compile(r"^([NSC]):(.*)$", re.S)


def classify(tok):
    m = VAL_RE.match(tok)
    if not m:
        return ("?", tok)
    t, v = m.group(1), m.group(2)
    if t == "N":
        try:
            return ("N", int(v))
        except Exception:
            return ("N!", v)
    return (t, v)


def scan(sources, targets):
    """-> {(src,V): {'argc':Counter,'pos':{i:{'N':Counter,'S':Counter}},'n':int}}"""
    res = {}
    for src in sources:
        p = os.path.join(TSVDIR, "解出_%s.tsv" % src)
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            head = f.readline().rstrip("\n").split("\t")
            ci = {c: n for n, c in enumerate(head)}
            for ln in f:
                p2 = ln.rstrip("\n").split("\t")
                if len(p2) <= ci["evidence"]:
                    continue
                ev = p2[ci["evidence"]]
                m = re.search(r"V=(0x[0-9A-Fa-f]+)", ev)
                if not m or m.group(1) not in targets:
                    continue
                args = split_args(ev)
                if args is None:
                    continue
                key = (src, m.group(1))
                d = res.setdefault(key, {"argc": Counter(), "pos": defaultdict(
                    lambda: {"N": Counter(), "S": Counter()}), "n": 0})
                d["argc"][len(args)] += 1
                d["n"] += 1
                for idx, tok in enumerate(args):
                    t, v = classify(tok)
                    if t == "N":
                        d["pos"][idx]["N"][v] += 1
                    else:
                        d["pos"][idx]["S"][v] += 1
    return res


def fmt_pos(rec, i, topn=5):
    n = rec["pos"].get(i)
    if not n:
        return "-"
    if sum(n["N"].values()) >= sum(n["S"].values()):
        vals = sorted(n["N"].items())
        if not vals:
            return "空"
        mn, mx = vals[0][0], vals[-1][0]
        mode, mc = n["N"].most_common(1)[0]
        return "N[%d,%d] 众%d(%d) 去重%d%s" % (
            mn, mx, mode, mc, len(n["N"]),
            (" +串%d" % sum(n["S"].values())) if n["S"] else "")
    tops = n["S"].most_common(topn)
    return "S " + " / ".join("%r×%d" % (k, c) for k, c in tops)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot,otr,otp")
    ap.add_argument("--V")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--topn", type=int, default=5)
    a = ap.parse_args()
    targets = [a.V] if a.V else TARGETS
    srcs = a.src.split(",")
    res = scan(srcs, set(targets))
    rows = []
    for src in srcs:
        for v in targets:
            key = (src, v)
            if key not in res:
                continue
            rec = res[key]
            acs = ",".join("%d×%d" % (k, c) for k, c in sorted(rec["argc"].items()))
            print("== %s %s  nodes=%d argc=%s" % (src, v, rec["n"], acs or "-"))
            for i in sorted(rec["pos"]):
                s = fmt_pos(rec, i, a.topn)
                print("   pos%d %s" % (i, s))
                rows.append({"src": src, "V": v, "argc": acs, "pos": i, "vals": s})
    if a.emit:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "效果族参数位_值域.tsv")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write("src\tV\targc\tpos\tvals\n")
            for r in rows:
                f.write("%s\t%s\t%s\t%d\t%s\n" % (r["src"], r["V"], r["argc"], r["pos"], r["vals"]))
        print("-> %s （%d 行）" % (p, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
