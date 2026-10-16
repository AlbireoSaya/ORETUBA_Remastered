# -*- coding: utf-8 -*-
"""W11g-schema · 文档路径引用存在性抽检（只读）。

扫描 5 份交付文档里出现的路径 token，逐个解析并报告存在性，用于确认
「相对路径前缀缺失 / 路径写错」已修完、没有遗漏。

分类规则：
  ABS     盘符绝对路径（`E:\\...`）→ 直接判定
  SRCREL  `{ot,ota,otp,otr,otv,np}\\{chr,pic,sys,etc,movie}\\…` → 在 `资源组\\krkr素材库\\` 下判定
  REL     其余含反斜杠 token → 依次用四个基准目录解析（工作区根 / 工程根 / 资源组 / 美术统一）
  SKIP    正则片段（`\\d` `\\x00` `\\n` …）、通配/占位（`*` `<` `…`）——非路径引用
  ELIDED  含 `\\...\\` 省略写法的路径 —— **本身就是缺陷**，单列报告

用法：
    cd 资源组\\工具
    python w11g_check_doc_paths.py            # 列 BAD / ELIDED / AMBIGUOUS 与统计
    python w11g_check_doc_paths.py --all      # 再列全部 token 与解析结果
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ALL = "--all" in sys.argv

ROOT = r"E:\ZCode Workspace\Galgame"
PROJ = os.path.join(ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
RES = os.path.join(PROJ, "资源组")
BASES = [("工作区根", ROOT), ("工程根", PROJ), ("资源组", RES),
         ("美术统一", os.path.join(RES, "美术统一"))]
SRCROOT = os.path.join(RES, "krkr素材库")
SRCS = {"ot", "ota", "otp", "otr", "otv", "np"}
SUBS = {"chr", "pic", "sys", "etc", "movie"}
DOCS = [
    (os.path.join(RES, "美术统一_规格.md"), "规格"),
    (os.path.join(RES, "美术统一", "README_交付超分.md"), "README"),
    (os.path.join(RES, "美术统一", "统一说明_立绘.md"), "统一说明_立绘"),
    (os.path.join(RES, "美术统一", "统一说明_CG背景.md"), "统一说明_CG背景"),
    (os.path.join(RES, "美术统一", "统一说明_系统UI.md"), "统一说明_系统UI"),
]

ABSTOK = re.compile(r"[A-Za-z]:\\[^\n`\"'（）()，。；、|]+")
RELTOK = re.compile(r"[A-Za-z0-9_\u4e00-\u9fff.\-—]+\\[A-Za-z0-9_\u4e00-\u9fff.\-—\\*/]*")
REGEXFRAG = re.compile(r"\\[dxwsnrtvf0]|\{\}|YYY|XXX|<\w+>|[*<>…～]")
ELIDED = re.compile(r"\\\.\.\.")
# 模块证据目录：`vis\xxx.png` 之类相对写法默认相对本模块的 W11f\vis\
VISBASE = os.path.join(ROOT, "子代理工作区", "ISSUE-20260918-06", "W11f")


def classify(tok):
    t = tok.strip("\\")
    if REGEXFRAG.search(t):
        return "SKIP", []
    if ELIDED.search(t):
        return "ELIDED", []
    parts = t.split("\\")
    if parts[0] in SRCS and len(parts) > 1 and parts[1] in SUBS:
        return "SRCREL", ["krkr素材库" if os.path.exists(os.path.join(SRCROOT, *parts)) else ""]
    if parts[0] == "vis":
        return "REL", (["W11f\\vis"] if os.path.exists(os.path.join(VISBASE, *parts)) else [])
    hits = [bn for bn, b in BASES if os.path.exists(os.path.join(b, *parts))]
    return "REL", hits


def main():
    rows = []
    for p, tag in DOCS:
        for ln, line in enumerate(open(p, encoding="utf-8").read().split("\n"), 1):
            spans = []
            for m in ABSTOK.finditer(line):
                tok = m.group(0).strip("\\").rstrip("。，、,;；)")
                if len(tok) < 6:
                    continue
                spans.append((m.start(), m.end()))
                ok = os.path.exists(tok)
                rows.append((tag, ln, tok, "ABS", ["存在"] if ok else []))
            for m in RELTOK.finditer(line):
                if any(s <= m.start() < e for s, e in spans):
                    continue
                tok = m.group(0).strip("\\")
                if len(tok) < 4 or "\\" not in tok:
                    continue
                kind, hits = classify(tok)
                if kind == "SKIP":
                    continue
                if kind == "SRCREL" and hits == [""]:
                    hits = []
                rows.append((tag, ln, tok, kind, hits))
    # 去重
    seen, uniq = set(), []
    for r in rows:
        k = (r[0], r[1], r[2])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)

    bad = [r for r in uniq if r[3] in ("REL", "ABS", "SRCREL") and not r[4]]
    elided = [r for r in uniq if r[3] == "ELIDED"]
    amb = [r for r in uniq if len(r[4]) > 1]
    print("扫描 %d 份文档，路径 token（去重后）%d 个" % (len(DOCS), len(uniq)))
    print("\n=== A. 不存在（前缀缺失 / 路径写错）===")
    for tag, ln, tok, kind, _ in bad:
        print("  [%s:%d] (%s) %s" % (tag, ln, kind, tok))
    if not bad:
        print("  无")
    print("\n=== B. 省略写法 `\\...\\`（本身即缺陷）===")
    for tag, ln, tok, _, _ in elided:
        print("  [%s:%d] %s" % (tag, ln, tok))
    if not elided:
        print("  无")
    print("\n=== C. 多重命中（相对路径有歧义）===")
    for tag, ln, tok, _, h in amb:
        print("  [%s:%d] %-52s -> %s" % (tag, ln, tok, " / ".join(h)))
    if not amb:
        print("  无")
    if ALL:
        print("\n=== 全部 token ===")
        cur = None
        for tag, ln, tok, kind, h in uniq:
            if tag != cur:
                cur = tag
                print("\n--- %s ---" % tag)
            st = " / ".join(h) if h else ("**不存在**" if kind != "ELIDED" else "省略写法")
            print("  L%-4d [%-6s] %-56s -> %s" % (ln, kind, tok, st))
    print("\nA_BAD = %d   B_ELIDED = %d   C_AMBIGUOUS = %d" % (len(bad), len(elided), len(amb)))


if __name__ == "__main__":
    main()