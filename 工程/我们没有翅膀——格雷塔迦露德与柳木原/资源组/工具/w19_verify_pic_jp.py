# -*- coding: utf-8 -*-
"""W19 验证：图片化日文补标后的 6 项核对（只读）。"""
import os
import re
import sys
import csv
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 资源组\
ART = os.path.join(ROOT, "美术统一")
SUP = os.path.join(ROOT, "美术统一_超分")
PROJ = os.path.dirname(ROOT)          # 工程\我们没有翅膀——格雷塔迦露德与柳木原\
WT = os.path.dirname(os.path.dirname(PROJ))  # worktree 根（PROJ 的上一级是 工程\，再上一级即根）

FILES = [
    (os.path.join(ART, "交付清单.tsv"), "交付清单.tsv"),
    (os.path.join(ART, "清单_CG背景.tsv"), "清单_CG背景.tsv"),
    (os.path.join(ART, "清单_系统UI.tsv"), "清单_系统UI.tsv"),
    (os.path.join(SUP, "超分清单.tsv"), "超分清单.tsv"),
]


def rel_git(p):
    return os.path.relpath(p, WT).replace("\\", "/")


def git_show(p):
    """HEAD 版本写到临时文件再读，避开 Windows 下中文路径的 subprocess 编码问题。"""
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "w19_head_" + os.path.basename(p))
    with open(tmp, "wb") as fh:
        r = subprocess.run(["git", "show", "HEAD:" + rel_git(p)],
                           cwd=WT, stdout=fh, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return None
    with open(tmp, "rb") as fh:
        data = fh.read()
    os.remove(tmp)
    return data.decode("utf-8")


def rows(text):
    # git blob 为 LF（.gitattributes text=auto），工作区文件为 CRLF；比较前统一去掉 \r
    return [l.rstrip("\r") for l in text.split("\n") if l.strip("\r") != ""]


def main():
    print("### 1) 逐表 图片化日文==是 计数（总表 / 三张分表 / 超分清单）")
    sets = {}
    for path, label in FILES:
        with open(path, encoding="utf-8", newline="") as f:
            rd = list(csv.DictReader(f, delimiter="\t"))
        yes = [r["统一名"] for r in rd if r["图片化日文"] == "是"]
        sets[label] = set(yes)
        kinds = {}
        for r in rd:
            if r["图片化日文"] == "是":
                kinds[r["类别"]] = kinds.get(r["类别"], 0) + 1
        print("  %-16s 行数=%-5d  是=%-4d  %s" % (label, len(rd), len(yes), kinds))

    print()
    print("### 2) 四表该列一致性（总表 vs 分表 vs 超分清单）")
    base = sets["交付清单.tsv"]
    with open(os.path.join(ART, "交付清单.tsv"), encoding="utf-8", newline="") as f:
        allrows = list(csv.DictReader(f, delimiter="\t"))
    by_kind = {}
    for r in allrows:
        by_kind.setdefault(r["类别"], set()).add(r["统一名"])
    for label, kind in [("清单_CG背景.tsv", "CG背景"), ("清单_系统UI.tsv", "系统UI")]:
        want = base & by_kind[kind]
        s = sets[label]
        print("  %-16s 分表==总表∩%s ? %s  (差集 %s)"
              % (label, kind, s == want, sorted(s ^ want)[:5]))
    print("  %-16s 超分清单==总表 ? %s  (差集 %s)"
          % ("超分清单.tsv", sets["超分清单.tsv"] == base, sorted(sets["超分清单.tsv"] ^ base)[:5]))

    print()
    print("### 3) 其余列逐行未变 + 行数守恒（对比 git HEAD）")
    for path, label in FILES:
        old = git_show(path)
        if old is None:
            print("  %-16s [skip] 不在 HEAD" % label); continue
        with open(path, encoding="utf-8", newline="") as f:
            new = f.read()
        ro, rn = rows(old), rows(new)
        hdr = ro[0].split("\t")
        ci = hdr.index("图片化日文")
        diff_cells = 0
        bad = []
        for a, b in zip(ro, rn):
            ca, cb = a.split("\t"), b.split("\t")
            if len(ca) != len(cb):
                bad.append("列数不同"); continue
            for i, (x, y) in enumerate(zip(ca, cb)):
                if x != y:
                    if i == ci:
                        if not (x == "" and y == "是"):
                            bad.append("非空→是 的改动: %r→%r" % (x, y))
                    else:
                        diff_cells += 1
                        if len(bad) < 5:
                            bad.append("第%d列变化 %r→%r" % (i, x, y))
        print("  %-16s 行数 %d→%d (差 %d) ｜ 非目标列差异单元格=%d ｜ 异常=%s"
              % (label, len(ro), len(rn), len(rn) - len(ro), diff_cells, bad[:5] or "无"))

    print()
    print("### 4) 清单 ↔ 磁盘 双向一致（系统UI / CG背景）")
    PNGROOT = os.environ.get("W19_PNG_ROOT",
                             r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一")
    for sub, label, tsv in [("系统UI", "系统UI", os.path.join(ART, "清单_系统UI.tsv")),
                            ("CG背景", "CG背景", os.path.join(ART, "清单_CG背景.tsv"))]:
        d = os.path.join(PNGROOT, sub)
        disk = set(os.listdir(d))
        with open(tsv, encoding="utf-8", newline="") as f:
            rd = list(csv.DictReader(f, delimiter="\t"))
        listed = set(r["统一名"] for r in rd)
        miss = sorted(listed - disk)
        extra = sorted(disk - listed)
        print("  %-8s 磁盘=%-5d 清单=%-5d 缺失=%d 多余=%d %s"
              % (label, len(disk), len(listed), len(miss), len(extra),
                 (miss[:4] + extra[:4]) or ""))

    print()
    print("### 5) 逐族 是 计数（系统UI）")
    with open(os.path.join(ART, "清单_系统UI.tsv"), encoding="utf-8", newline="") as f:
        rd = list(csv.DictReader(f, delimiter="\t"))

    def pref(n):
        m = re.match(r"^([a-zA-Z_]+?)(\d|_)", n)
        return m.group(1) if m else n
    from collections import Counter
    c = Counter()
    for r in rd:
        if r["图片化日文"] == "是":
            c[pref(r["统一名"])] += 1
    print("  " + "  ".join("%s=%d" % (k, v) for k, v in sorted(c.items(), key=lambda x: -x[1])))

    print()
    print("### 6) 逐族 是 计数（CG背景）")
    with open(os.path.join(ART, "清单_CG背景.tsv"), encoding="utf-8", newline="") as f:
        rd = list(csv.DictReader(f, delimiter="\t"))
    c = Counter()
    for r in rd:
        if r["图片化日文"] == "是":
            n = r["统一名"]
            g = re.match(r"^(sr[0-4])_", n)
            c[g.group(1) if g else (n.split("_")[0] if "_" in n else n)] += 1
    print("  " + "  ".join("%s=%d" % (k, v) for k, v in sorted(c.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())