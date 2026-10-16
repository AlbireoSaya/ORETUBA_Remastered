#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_chapter_markers.py —— 章节标记行清查（ISSUE-20261005-02）
================================================================================
背景：原版脚本里的「章节标记串」（ot 的 ScSkip 片头标题/简介、otr 的 .tob 声明串与场末
下一章题、ota/otr 的 k="title" 卡）被语料提取成了场景台词行，在游戏内以对话框裸文本出现
（用户 2026-10-05 实报）。修复＝引擎识别这些行改为**全屏过场卡**（见 `ui_story.tjs`
「章节过场卡」模块）。

本工具用**与运行时完全相同的判据**扫描全部构建场景：
    标记行 ⇔ tx != "" 且 sp == "" 且 vo == "" 且 (k == "title" 或 tx ∈ 标记串全集)
    标记串全集 = UIIntro 题/正文 ∪ UIAct 标签/首场题/幕简介（`story/_intro.tjs` 生成物）
                 ∪ 场景自身 title
输出：
  ① 控制台汇总（条数 / 按来源 / 按 k / 按池类型 / sq 分布）；
  ② TSV 明细（scene、sq、k、类型、长度、文本）——**覆盖运行时实际渲染的全部标记行**；
  ③ 负向自证：**真台词**（有说话人或带语音）命中标记串的行数（应 0；k=="title" 且
     sp/vo 空的行是合法标记，不计入负向）。

用法： python -X utf8 工具\\audit_chapter_markers.py [--story DIR] [--tsv OUT]
"""
import argparse
import io
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))

LINE_PAT = re.compile(r'%\[\s*k:"([^"]*)",\s*sp:"((?:[^"\\]|\\.)*)",\s*tx:"((?:[^"\\]|\\.)*)",'
                      r'\s*vo:"((?:[^"\\]|\\.)*)",\s*sq:(\d+)\s*\]')


def parse_tjs_str_array(txt, name):
    m = re.search(r'^' + name + r'\s*=\s*\[(.*?)\];', txt, re.M | re.S)
    if not m:
        return []
    return re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", default=os.path.join(PROJ, "编程组", "krkr", "game", "story"),
                    help="构建 story 目录（默认=源树 krkr/game/story）")
    ap.add_argument("--tsv", default=os.path.join(PROJ, "编程组", "章节标记行审计.tsv"))
    a = ap.parse_args()

    intro_p = os.path.join(a.story, "_intro.tjs")
    if not os.path.isfile(intro_p):
        print("[FATAL] 缺 _intro.tjs：%s（先跑 build_story）" % intro_p)
        return 2
    intro = io.open(intro_p, encoding="utf-8").read()
    n_keys = len(parse_tjs_str_array(intro, "UIIntroKeys"))
    titles = parse_tjs_str_array(intro, "UIIntroTitles")
    texts = parse_tjs_str_array(intro, "UIIntroTexts")
    act_labels = parse_tjs_str_array(intro, "UIActLabels")
    act_titles = parse_tjs_str_array(intro, "UIActTitles")
    act_intros = parse_tjs_str_array(intro, "UIActIntros")
    act_firsts = parse_tjs_str_array(intro, "UIActFirsts")
    print("[intro] 场景简介 %d 条 ｜ 幕 %d 个（标签 %d/题 %d/简介 %d）" % (
        n_keys, len(act_firsts), len(act_labels), len(act_titles), len(act_intros)))

    # 标记串全集 → 池类型（★ 空串剔除：语料有大量 tx:"" 占位行，会把空串撞成命中）
    pool = {}
    for s in titles:
        if s:
            pool.setdefault(s, "场景简介标题")
    for s in texts:
        if s:
            pool.setdefault(s, "场景简介正文")
    for s in act_labels:
        if s:
            pool.setdefault(s, "幕标签")
    for s in act_titles:
        if s:
            pool.setdefault(s, "幕首场标题")
    for s in act_intros:
        if s:
            pool.setdefault(s, "幕简介")

    rows = []
    n_scene = 0
    neg = []
    scenes = sorted(f for f in os.listdir(a.story) if re.match(r"^scene_.+\.tjs$", f))
    for fn in scenes:
        txt = io.open(os.path.join(a.story, fn), encoding="utf-8").read()
        mi = re.search(r'^\s*id:"([^"]+)"', txt, re.M)
        if not mi:
            continue
        sid = mi.group(1)
        mt = re.search(r'^\s*title:"((?:[^"\\]|\\.)*)"', txt, re.M)
        stitle = mt.group(1) if mt else ""
        hit = False
        for (k, sp, tx, vo, sq) in LINE_PAT.findall(txt):
            if tx == "":
                continue
            is_title_kind = (k == "title")
            in_pool = (tx in pool) or (stitle != "" and tx == stitle)
            if not (is_title_kind or in_pool):
                continue
            # ── 判据守卫（与运行时同一口径）──
            if sp != "" or vo != "":
                # 有说话人或带语音却命中标记串 ⇒ **真台词**，运行时也不会当标记（守卫拦下）
                neg.append((sid, sq, k, sp, vo, tx))
                continue
            kind = pool.get(tx, ("场景自身标题" if (stitle != "" and tx == stitle) else "—"))
            if is_title_kind:
                kind = kind + "｜k=title" if kind != "—" else "k=title 卡"
            rows.append((sid, int(sq), k, kind, len(tx), tx))
            hit = True
        if hit:
            n_scene += 1

    print("[scan] 场景 %d 个，命中标记行 %d 行 / %d 场景" % (len(scenes), len(rows), n_scene))
    byk = collections.Counter(r[2] for r in rows)
    for k in sorted(byk):
        print("   按 k：%-10s %d 行" % (k, byk[k]))
    bysrc = collections.Counter(r[0].split("_")[0] for r in rows)
    print("   按来源：" + " ｜ ".join("%s %d" % (s, n) for s, n in sorted(bysrc.items())))
    bypool = collections.Counter(r[3] for r in rows)
    for k in sorted(bypool):
        print("   按类型：%-24s %d 行" % (k, bypool[k]))
    sqc = collections.Counter(r[1] for r in rows)
    print("   sq 分布：" + " ｜ ".join("sq%d×%d" % (s, n) for s, n in sorted(sqc.items())[:8]))

    with io.open(a.tsv, "w", encoding="utf-8", newline="") as f:
        f.write("scene\tsq\tk\t类型\t长度\t文本\n")
        for (sid, sq, k, kind, ln, tx) in sorted(rows):
            f.write("%s\t%d\t%s\t%s\t%d\t%s\n" % (sid, sq, k, kind, ln, tx.replace("\t", " ")))
    print("[ok] 明细 → %s（%d 行，覆盖全部 k 的标记行）" % (a.tsv, len(rows)))

    print("[neg] 真台词（有说话人或带语音）命中标记串的行 = %d（应 0）" % len(neg))
    for (sid, sq, k, sp, vo, tx) in neg[:10]:
        print("   [WARN] %s sq=%s k=%s sp=%s vo=%s ｜ %s" % (sid, sq, k, sp, vo, tx[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
