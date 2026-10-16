# -*- coding: utf-8 -*-
"""W11g · 复现用户「160/38」划分，并输出需目视终裁的组清单。
判据（用户原话）：「内容宽高比差≈0.2500 且两方为 1.3333 ↔ 1.7778/1.7647」。
即：组内候选的画布 ar 去重后恰为 {1.3333, 1.7778} 或 {1.3333, 1.7647}（"两方"）。
只读，print 摘要。"""
import os, re, json

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")
GATE = os.path.join(UNI, "门控未拆候选_W11f.tsv")

PAIRS = [frozenset({1.3333, 1.7778}), frozenset({1.3333, 1.7647})]


def main():
    with open(GATE, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n")]
    rows = [ln.split("\t") for ln in lines[1:]]

    two_side, other = [], []
    for r in rows:
        cat, name, n, diff, cands = r[0], r[1], int(r[2]), float(r[3]), r[4]
        ars = []
        for it in [c.strip() for c in cands.split(";")]:
            m = re.search(r"ar=([\d.]+)", it)
            if m:
                ars.append(float(m.group(1)))
        st = frozenset(ars)
        if st in PAIRS:
            two_side.append((cat, name, n, diff, sorted(st)))
        else:
            other.append((cat, name, n, diff, sorted(st), cands))

    print("总组数:", len(rows))
    print("恰为 4:3↔16:9 两方:", len(two_side))
    print("其余(需目视终裁):", len(other))
    print()
    for cat, name, n, diff, ars, cands in other:
        print("%s\t%s\tn=%d\tdiff=%.4f\tar=%s" % (cat, name, n, diff, ",".join("%.4f" % a for a in ars)))
    # 导出
    out = [{"类别": c, "统一名": n, "候选数": k, "diff": d, "ar": a, "候选": cd}
           for c, n, k, d, a, cd in other]
    p = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g"))
    os.makedirs(p, exist_ok=True)
    assert p.startswith(r"E:\ZCode Workspace\Galgame")
    tmp = os.path.join(p, "_38组清单.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(p, "_38组清单.json"))
    print("\n写出:", os.path.join(p, "_38组清单.json"))


if __name__ == "__main__":
    main()