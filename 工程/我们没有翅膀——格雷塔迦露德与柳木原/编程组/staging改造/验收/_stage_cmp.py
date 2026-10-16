# -*- coding: utf-8 -*-
"""_stage_cmp.py —— 「立绘尺寸/摆位改造」（ISSUE-20261007-05）前后对照器（只读）

从两份 `scene_*.tjs` 目录解出逐场 stage 事件，产出：
  · 逐场对照.tsv      scene/op/slot/fam/before(x,y,w,h)/after(x,y,w,h)（按 (op,slot,fam) 首见折叠）
  · 立绘高与x对照.tsv  抽 N 场的「改前 vs 改后」立绘高与 x（逐族首见）
  · 尺寸分布对照      chr_add/chr_expr 的 h、x 分布（改前 vs 改后）

用法：python -X utf8 _stage_cmp.py --before <dir> --after <dir> [--scenes s1,s2,...] [--out <dir>]
"""
import argparse, csv, os, re, sys
from collections import Counter, OrderedDict

ROW_RE = re.compile(
    r'%\s*\[\s*seq:(-?\d+)\s*,\s*op:"([^"]*)"\s*,\s*slot:(-?\d+)\s*,\s*fam:"([^"]*)"\s*,'
    r'\s*t:"([^"]*)"\s*,\s*x:(-?\d+)\s*,\s*y:(-?\d+)\s*,\s*w:(-?\d+)\s*,\s*h:(-?\d+)\s*,'
    r'\s*z:(-?\d+)([^\]]*)\]')


def parse_dir(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        m = re.match(r"scene_(.+)\.tjs$", fn)
        if not m:
            continue
        txt = open(os.path.join(d, fn), encoding="utf-8").read()
        rows = []
        for g in ROW_RE.finditer(txt):
            extra = g.group(11)
            dur = re.search(r'dur:(-?\d+)', extra)
            dirn = re.search(r'dir:"([^"]*)"', extra)
            rows.append(dict(seq=int(g.group(1)), op=g.group(2), slot=int(g.group(3)),
                             fam=g.group(4), t=g.group(5), x=int(g.group(6)), y=int(g.group(7)),
                             w=int(g.group(8)), h=int(g.group(9)), z=int(g.group(10)),
                             dur=(int(dur.group(1)) if dur else None),
                             dir=(dirn.group(1) if dirn else "")))
        out[m.group(1)] = rows
    return out


def first_by_fam(rows):
    """(op∈chr_add/chr_expr) 逐族**首次**出现的几何（(x,y,w,h)）。"""
    seen = OrderedDict()
    for r in rows:
        if r["op"] in ("chr_add", "chr_expr") and r["fam"] not in seen:
            seen[r["fam"]] = r
    return seen


def last_by_fam(rows):
    """(op∈chr_add/chr_expr) 逐族**末次**出现的几何（＝稳态摆位）+ 该族出现的最大 h。"""
    seen = OrderedDict()
    for r in rows:
        if r["op"] in ("chr_add", "chr_expr"):
            seen[r["fam"]] = r
    out = {}
    for fam in seen:
        hmax = max(r["h"] for r in rows if r["op"] in ("chr_add", "chr_expr") and r["fam"] == fam)
        out[fam] = (seen[fam], hmax)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--scenes", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    B = parse_dir(a.before)
    A = parse_dir(a.after)
    sids = sorted(set(B) | set(A))
    if a.scenes:
        want = [s.strip() for s in a.scenes.split(",") if s.strip()]
        sids = [s for s in want if s in (set(B) | set(A))]

    # ---- 1) 逐场/逐族 稳态对照（末次摆位 + 最大高）----
    with open(os.path.join(a.out, "逐场立绘对照.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("scene\tfam\tb_last_x\tb_last_cx\tb_hmax\ta_last_x\ta_last_cx\ta_hmax\td_hmax\td_cx\n")
        for sid in sids:
            lb = last_by_fam(B.get(sid, []))
            la = last_by_fam(A.get(sid, []))
            for fam in sorted(set(lb) | set(la)):
                b, x2 = lb.get(fam), la.get(fam)
                bcx = (round(b[0]["x"] + b[0]["w"] / 2) if b else "")
                acx = (round(x2[0]["x"] + x2[0]["w"] / 2) if x2 else "")
                f.write("\t".join(str(v) for v in [
                    sid, fam,
                    (b[0]["x"] if b else ""), bcx, (b[1] if b else ""),
                    (x2[0]["x"] if x2 else ""), acx, (x2[1] if x2 else ""),
                    ((x2[1] - b[1]) if (b and x2) else ""),
                    ((acx - bcx) if (b and x2) else ""),
                ]) + "\n")

    # ---- 2) 全量 chr_add/chr_expr 的 h / x 分布对照 ----
    def dist(D, key):
        c = Counter()
        for rows in D.values():
            for r in rows:
                if r["op"] in ("chr_add", "chr_expr"):
                    c[r[key]] += 1
        return c

    def summarize(D):
        hs = [r["h"] for rows in D.values() for r in rows
              if r["op"] in ("chr_add", "chr_expr") and r["h"] > 0]
        xs = [r["x"] for rows in D.values() for r in rows
              if r["op"] in ("chr_add", "chr_expr") and r["w"] > 0]
        hs.sort()
        return (len(hs), (min(hs) if hs else 0), (hs[len(hs) // 2] if hs else 0), (max(hs) if hs else 0),
                (round(sum(hs) / len(hs), 1) if hs else 0))

    with open(os.path.join(a.out, "尺寸分布对照.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("项\t改前\t改后\n")
        sb, sa = summarize(B), summarize(A)
        for i, label in enumerate(["chr_add/chr_expr 行数", "h 最小", "h 中位", "h 最大", "h 均值"]):
            f.write("%s\t%s\t%s\n" % (label, sb[i], sa[i]))
        cb, ca = dist(B, "h"), dist(A, "h")
        f.write("\n最高的 12 个 h 值（改前）\t%s\n" % "、".join("%d×%d" % (h, c) for h, c in cb.most_common(12)))
        f.write("最高的 12 个 h 值（改后）\t%s\n" % "、".join("%d×%d" % (h, c) for h, c in ca.most_common(12)))

    # ---- 3) 命令行场景的详细对照（stdout，供报告直接引用） ----
    print("=== 立绘「稳态摆位 + 最大高」对照（改前 → 改后）===")
    print("scene\tfam\t改前末x/中心\t改前hMax\t改后末x/中心\t改后hMax")
    for sid in sids:
        lb = last_by_fam(B.get(sid, []))
        la = last_by_fam(A.get(sid, []))
        for fam in sorted(set(lb) | set(la)):
            b, x2 = lb.get(fam), la.get(fam)
            bc = ("%d/%d" % (b[0]["x"], round(b[0]["x"] + b[0]["w"] / 2))) if b else "-"
            ac = ("%d/%d" % (x2[0]["x"], round(x2[0]["x"] + x2[0]["w"] / 2))) if x2 else "-"
            print("%s\t%s\t%s\t%s\t%s\t%s" % (sid, fam, bc, (b[1] if b else "-"),
                                              ac, (x2[1] if x2 else "-")))
    print()
    print("=== 全量 h 分布（改前 → 改后）===")
    sb, sa = summarize(B), summarize(A)
    print("行数 %d→%d ｜ h min %d→%d ｜ 中位 %d→%d ｜ max %d→%d ｜ 均值 %.1f→%.1f"
          % (sb[0], sa[0], sb[1], sa[1], sb[2], sa[2], sb[3], sa[3], sb[4], sa[4]))
    # dur/dir 统计
    for tag, D in (("改前", B), ("改后", A)):
        n = sum(1 for rows in D.values() for r in rows if r["op"] == "chr_remove" and r["dur"] is not None)
        dirs = Counter(r["dir"] for rows in D.values() for r in rows
                       if r["op"] == "chr_remove" and r["dur"] is not None)
        print("[%s] chr_remove 带 dur/dir：%d 条 ｜ dir 分布 %s" % (tag, n, dict(dirs)))


if __name__ == "__main__":
    main()
