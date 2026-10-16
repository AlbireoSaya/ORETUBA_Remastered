# -*- coding: utf-8 -*-
"""W11g · 复核「160/38」划分：把 门控未拆候选_W11f.tsv 的 198 组按
「是否 4:3 vs 16:9 跨平台画幅」分类。只读，只 print 摘要。"""
import os, re, sys

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
SRC = os.path.join(PROJ, "资源组", "krkr素材库")
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")

GATE = os.path.join(UNI, "门控未拆候选_W11f.tsv")

# 4:3 侧与 16:9 侧的画布 ar（PC 800x600=1.3333 / 1200x600=2.0；PSV 960x544=1.7647 / 960x540=1.7778 / 1440x544=2.6471）
FOUR3 = {1.3333, 2.0}
WIDE = {1.7647, 1.7778, 2.6471}


def ar_class(a):
    if a in FOUR3:
        return "4:3"
    if a in WIDE:
        return "16:9"
    return "other"


def main():
    with open(GATE, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n")]
    hdr = lines[0].split("\t")
    rows = [ln.split("\t") for ln in lines[1:]]
    print("总组数:", len(rows))
    print("表头:", hdr)

    pat_ok, pat_no, details = [], [], []
    for r in rows:
        cat, name, n, diff, cands = r[0], r[1], r[2], float(r[3]), r[4]
        # 解析候选: "ot:ot_x.png 800x600 ar=1.3333 ; np:np_x.png 1280x720 ar=0.6084"
        items = [c.strip() for c in cands.split(";")]
        ars = []
        for it in items:
            m = re.search(r"ar=([\d.]+)", it)
            if m:
                ars.append(float(m.group(1)))
        classes = set(ar_class(a) for a in ars)
        # 判据: 所有 ar 只落在 {4:3 侧} 与 {16:9 侧}，且两侧都出现，且无 other
        is_43_169 = (classes == {"4:3", "16:9"}) and all(ar_class(a) != "other" for a in ars)
        diff_ok = abs(diff - 0.2500) <= 0.006  # 0.2500 或 0.2444
        if is_43_169 and diff_ok:
            pat_ok.append((cat, name, n, diff, sorted(set(ars))))
        else:
            pat_no.append((cat, name, n, diff, sorted(set(ars))))
            details.append((cat, name, n, diff, cands))

    print("\n=== 判据: 全部候选 ar ∈ {1.3333,2.0}(4:3侧) ∪ {1.7647,1.7778,2.6471}(16:9侧) 且两侧齐 且 diff≈0.2500 ===")
    print("符合「4:3 vs 16:9」:", len(pat_ok))
    print("不符合(需目视):", len(pat_no))
    print("\n--- 不符合组明细 ---")
    for cat, name, n, diff, cands in details:
        print("%s\t%s\tn=%s\tdiff=%.4f\t%s" % (cat, name, n, diff, cands))

    # 子统计: 仅因 diff 不符 vs 仅因 ar 不符
    print("\n--- 不符原因分解 ---")
    for cat, name, n, diff, ars in pat_no:
        reasons = []
        if abs(diff - 0.2500) > 0.006:
            reasons.append("diff=%.4f≠0.25" % diff)
        cls = set(ar_class(a) for a in ars)
        if cls != {"4:3", "16:9"}:
            reasons.append("ar=%s" % (",".join("%.4f" % a for a in ars)))
        print("%-6s %-18s n=%s  %s" % (cat, name, n, " | ".join(reasons)))


if __name__ == "__main__":
    main()