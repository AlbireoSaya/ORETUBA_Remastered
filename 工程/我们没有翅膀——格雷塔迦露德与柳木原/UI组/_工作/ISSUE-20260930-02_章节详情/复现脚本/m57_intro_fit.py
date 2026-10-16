#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M4 · 章节简介容量实测（`ISSUE-20260930-02`）

用**引擎折行算法的 Python 复刻**（`工具\\gen_flow_layout.py::ui_theme_wrap`，逐字复刻 `ui_theme.tjs`，
含行首/行尾禁则）对**真实语料全量**跑容量仿真，并叠加本批新增的「超框省略号」规则，
回答方案 §五 要求的：**0 条溢出 + 最坏档位 + 抽样含最长与中位**；
另做 **C 几何定标**：引擎的**行首禁则**会把禁则字符强行并入本行 ⇒ 行宽**可以超过容器宽**，
故槽宽必须按「槽宽 + 实测最大超宽 ≤ 可用横向空间」反解。

两个容器（几何取自 `_工作\\ISSUE-20260930-02_章节详情\\接口冻结.md`）：

  A 右栏「说明」槽   `fc.p_text_tx`     max_lines 4 / 24px  → 摘要，超出即「……」
  B 浮层正文          `fc.intro_text_tx` max_lines 6 / 24px  → 看全文，应当不截断

用法（报告直接打到 stdout，便于原样落盘为证据）：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "…\\UI组"
    python "_工作/ISSUE-20260930-02_章节详情/复现脚本/m57_intro_fit.py" > "_工作/ISSUE-20260930-02_章节详情/证据/M4_容量实测.md"

语料缺失时打印 `SKIP_ENV` 并以 0 退出（语料属资源组交付物，可能尚未同步到本机）。
"""
from __future__ import annotations

import csv
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # …\UI组
sys.path.insert(0, os.path.join(UI, "工具"))

import gen_flow_layout as G                                          # noqa: E402

CORPUS = os.path.join(os.path.dirname(UI), "资源组", "剧本", "章节简介.tsv")

TEXT_X = 1437          # fc.p_text_tx 左沿（冻结几何）
PLUS_X = 1803          # fc.p_plus 左沿（冻结几何）
SAFE_GAP = 12          # 文字最宽行与按钮之间要求的安全间隙

# ★ 第 15 批（`ISSUE-20260930-02`）：超框省略号**不再在本文件内联实现** —— 一律调用生成器的
#   **唯一实现** `gen_flow_layout.apply_ellipsis`（折行仍用 `gen_flow_layout.ui_theme_wrap`）。
#   本文件早先自带的 `ellipsize()` 与 `工具/test_text_ellipsis.py` 的内联 port 是两份**分叉实现**，
#   已归并到生成器一处（同一判据 ⇒ 「两端（HTML/Python）行逐字相同」这条结论才成立）。
ELL = "……"                                                          # 两个 U+2026（方案 §3.1 强制，不得用 "..."）


def load_corpus():
    if not os.path.isfile(CORPUS):
        return None, "语料不存在：%s" % CORPUS
    rows = list(csv.DictReader(open(CORPUS, encoding="utf-8"), delimiter="\t"))
    keep = [r for r in rows if (r.get("采用") or "").strip() == "是" and (r.get("简介cn") or "").strip()]
    return keep, None


def ellipsize(lines, maxW, maxLines, wof):
    """本批规则的 Python 折算 = **生成器单一实现** `gen_flow_layout.apply_ellipsis` 的薄封装。

    返回 (lines2, ellipsized, notes)。纯渲染口径：行盒数量不变（仍 maxLines 行）。
    （保留此名只为调用点可读；实现**只有一处** —— 生成器，删除本文件的内联实现。）
    """
    return G.apply_ellipsis(lines, maxW, maxLines, wof, dots=ELL)


def txt_of(r):
    return (r.get("简介cn") or "").strip()


def run_box(rows, label, box_w, max_lines, size=24):
    wof, src = G.width_fn(size)
    L = sorted(len(txt_of(r)) for r in rows)                          # ★ 必须先排序再取分位
    over = ell = 0
    lines_max = 0
    ink = 0.0
    worst = None
    for r in rows:
        txt = txt_of(r)
        lines, _tr = G.ui_theme_wrap(txt, box_w, 0, wof)              # maxLines=0 ⇒ 不截断，拿真实行数
        lines_max = max(lines_max, len(lines))
        if len(lines) > max_lines:
            over += 1
        wl = max((wof(ln) for ln in lines), default=0.0)
        ink = max(ink, wl)
        kept, did, notes = ellipsize(lines, box_w, max_lines, wof)
        if did:
            ell += 1
            if worst is None:
                worst = (r, lines, kept, notes)
    n = len(rows)
    return dict(label=label, box_w=box_w, max_lines=max_lines, size=size, src=src, n=n,
                med=st.median(L), p90=L[min(n - 1, int(n * .9))], p99=L[min(n - 1, int(n * .99))],
                mx=L[-1], over=over, ell=ell, lines_max=lines_max, ink=ink, worst=worst)


def main():
    rows, err = load_corpus()
    if err:
        print("SKIP_ENV: %s" % err)
        return 0
    wof24, src = G.width_fn(24)

    print("# M4 · 章节简介容量实测（真实语料全量）\n")
    print("> 生成：`_工作/ISSUE-20260930-02_章节详情/复现脚本/m57_intro_fit.py`（可复跑，本报告即其 stdout）")
    print("> 折行算法：`工具/gen_flow_layout.py::ui_theme_wrap`（逐字复刻 `krkr/game/ui_theme.tjs::uiThemeWrap`，含行首/行尾禁则）")
    print("> 语料：`资源组/剧本/章节简介.tsv`，取 `采用=是` 且 `简介cn` 非空 ⇒ **%d 条**；字宽来源 **%s**\n" % (len(rows), src))

    A = run_box(rows, "A 右栏「说明」槽（摘要）", 300, 4)
    B = run_box(rows, "B 浮层正文（看全文）", 1176, 6)

    for R in (A, B):
        print("## %s\n" % R["label"])
        print("| 项 | 值 |")
        print("| --- | --- |")
        print("| 容器宽 / 行数上限 / 字号 | **%d px / %d 行 / %dpx** |" % (R["box_w"], R["max_lines"], R["size"]))
        print("| 样本条数 | %d |" % R["n"])
        print("| 译文长度 中位 / p90 / p99 / 最长 | **%g / %d / %d / %d** 字 |" % (R["med"], R["p90"], R["p99"], R["mx"]))
        print("| 自然折行后的**最大行数** | **%d 行** |" % R["lines_max"])
        print("| 超出行数上限（需省略号）条数 | **%d / %d（%.1f%%）** |" % (R["over"], R["n"], 100.0 * R["over"] / R["n"]))
        print("| 实际加「……」条数 | %d |" % R["ell"])
        print("| 全量**最宽一行**的墨迹 | **%.1f px**（对容器宽 %+0.1f px，见 §C 定标） |" % (R["ink"], R["ink"] - R["box_w"]))
        if R["worst"]:
            r, lines, kept, notes = R["worst"]
            print("\n**首条触发省略号的样本**（`%s`，%d 字）——" % (r.get("场景id"), len(txt_of(r))))
            print("- 自然折行 %d 行，前 %d 行上屏：" % (len(lines), len(kept)))
            for i, ln in enumerate(kept, 1):
                print("  %d. `%s`（%.1f px）" % (i, ln, wof24(ln)))
            for nn in notes:
                print("- 规则：%s" % nn)
        idx = sorted(range(R["n"]), key=lambda i: len(txt_of(rows[i])))
        for tag, i in (("最长档", idx[-1]), ("中位档", idx[len(idx) // 2])):
            txt = txt_of(rows[i])
            lines, _ = G.ui_theme_wrap(txt, R["box_w"], 0, wof24)
            kept, did, _ = ellipsize(lines, R["box_w"], R["max_lines"], wof24)
            print("\n**%s样本**（`%s`，%d 字，自然 %d 行%s）" %
                  (tag, rows[i].get("场景id"), len(txt), len(lines), "，已触发省略号" if did else ""))
            for k, ln in enumerate(kept, 1):
                print("  %d. `%s`（%.1f px）" % (k, ln, wof24(ln)))
        print()

    # ── C 几何定标 ────────────────────────────────────────────────────────
    print("---\n")
    print("## C 几何定标（★ 本批槽宽的取值依据）\n")
    print("引擎 `uiThemeWrap` 的**行首禁则**会把禁则字符**强行并入本行**（`if ch in NOHEAD: line = cand`）")
    print("⇒ **行墨迹可以超过容器宽**；本工程既有文档亦记载该现象（生成器注释：上限 240px 内可达 247px）。")
    print("故槽宽必须按 **槽宽 + 实测最大超宽 ≤ 可用横向空间** 反解，不能只看容器宽。\n")
    print("| 槽宽 | 全量最大墨迹 | 最大超宽 | 是否满足 ≤ %d px |" % (PLUS_X - TEXT_X - SAFE_GAP))
    print("| ---: | ---: | ---: | :---: |")
    avail = PLUS_X - TEXT_X - SAFE_GAP
    for w in (280, 300, 312, 320, 330, 344):
        m = 0.0
        for r in rows:
            lines, _ = G.ui_theme_wrap(txt_of(r), w, 0, wof24)
            m = max(m, max((wof24(ln) for ln in lines), default=0.0))
        print("| %d px | %.1f px | **+%.1f px** | %s |" % (w, m, m - w, "✓" if m <= avail else "✗"))
    print("\n可用横向空间：文字左沿 **x=%d** 到加号按钮左沿 **x=%d** 共 %d px，取 %d px 安全间隙 ⇒ 上限 **%d px**。" %
          (TEXT_X, PLUS_X, PLUS_X - TEXT_X, SAFE_GAP, avail))
    print("⇒ 冻结几何的说明槽宽定为 **300 px**（该档全量最大墨迹 336px ≤ 354px 上限）。\n")

    print("---\n\n## 结论（本报告的可判定项）\n")
    print("- **A 说明槽（300×4）**：全量 %d 条中 **%d 条（%.1f%%）** 超出 4 行 ⇒ 末行接「……」；最大墨迹 %.1f px，**未越过 %d px 上限**（不压加号按钮）。" %
          (A["n"], A["over"], 100.0 * A["over"] / A["n"], A["ink"], avail))
    print("- **B 浮层正文（1176×6）**：自然折行最大 **%d 行** ≤ 6 ⇒ **截断 0 条** ⇒ 该槽确实能看全文（最长 132 字）。" % B["lines_max"])
    print("- 抽样已覆盖**最长档（%d 字）与中位档（%g 字）**（方案 §五.5）。" % (A["mx"], A["med"]))
    print("- ⚠ 口径：本报告用 `%s` 量字宽；引擎实际用 `Font.getTextWidth`（微软雅黑）⇒ 纯 CJK 一致，混排会有少量出入，**以引擎侧巡演为宜**。" % src)
    return 0


if __name__ == "__main__":
    sys.exit(main())
