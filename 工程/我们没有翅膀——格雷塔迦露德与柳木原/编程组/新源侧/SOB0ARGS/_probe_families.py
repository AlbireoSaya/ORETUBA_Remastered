# -*- coding: utf-8 -*-
"""只读探针：按 V 统计实参画像，判定立绘族。

用法: python -X utf8 _probe_families.py
"""
import csv, collections, re, os, sys

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\SOB0解码"

TOKRE = re.compile(r"^(?:[a-z]+\s+)?(?:!?[clr]|[<>]\d+|[clr][<>]\d+|\d+[<>]\d*)$")
NAMERE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")


def parse_args(ev):
    m = re.search(r"args=\[(.*?)\]", ev)
    if not m:
        return None
    out = []
    if m.group(1) == "":
        return out
    for p in m.group(1).split(","):
        p = p.strip()
        if p.startswith("N:"):
            out.append(("N", int(p[2:])))
        elif p.startswith("S:"):
            out.append(("S", p[2:]))
        else:
            out.append(("?", p))
    return out


def main():
    for src in ["ot", "otp", "otr"]:
        path = os.path.join(BASE, "解出_%s.tsv" % src)
        rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))
        by = collections.defaultdict(list)
        for r in rows:
            m = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            if m:
                by[m.group(1)].append(r)
        print("#####", src, "distinct V =", len(by))
        for v, sub in sorted(by.items(), key=lambda x: -len(x[1])):
            if len(sub) < 20:
                continue
            argc = collections.Counter()
            lastslot = 0
            nmc = 0
            tkc = 0
            signed = 0
            for r in sub:
                a = parse_args(r["evidence"])
                if a is None:
                    continue
                argc[len(a)] += 1
                if a and a[-1][0] == "N" and 0 <= a[-1][1] <= 7:
                    lastslot += 1
                if any(t == "S" and NAMERE.match(s) for t, s in a):
                    nmc += 1
                if any(t == "S" and TOKRE.match(s) for t, s in a):
                    tkc += 1
                if any(t == "N" and s == 4294967295 for t, s in a):
                    signed += 1
            n = len(sub)
            print("  %-9s n=%-6d argc=%-8s lastslot=%6d(%3d%%) name=%6d(%3d%%) tok=%6d(%3d%%) minus1=%6d(%3d%%)"
                  % (v, n, argc.most_common(1)[0][0] if argc else "?", lastslot, 100 * lastslot // n,
                     nmc, 100 * nmc // n, tkc, 100 * tkc // n, signed, 100 * signed // n))


if __name__ == "__main__":
    main()
