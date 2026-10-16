# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 任务 4 顺带核一条：**主干组名标签** `fc.label.<N>` 用同一把 p5 尺子量一次

■ 背景（本轮只需事实，不改它）
  独立层组名的底板本轮换成了专用硬边件 `x_ui_fragtitle_bg.png`（444×52，α≥200 占 99.948%）；
  而**主干**的组名标签 `fc.label.<N>` 仍是**同一个旧件** `x_ui_label_off.png`（素材 355×60，
  元素 333×38，`nine` 全零 ⇒ 整图拉伸）。旧件四边是宽渐隐带 ⇒ 形制上与上一轮的缺陷同源。
  本脚本用**与 `e3_title_contrast.py` 完全同一把尺子**（同层两张图取字形像素 → 字形核心像素
  逐像素 WCAG 对比度 → 取 5 分位）量主干 6 个标签，给出数值与裁图，作登记依据。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_label_contrast.py
"""
import importlib.util
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
EVID = os.path.join(HTML_DIR, "证据")
ASSETS = os.path.join(UI, "krkr", "assets")
PREFIX = os.environ.get("E3_LABEL_PREFIX", "E3_label_v1_")
LOGNAME = os.environ.get("E3_LABEL_LOG", "E3_主干标签可读性_日志.txt")
N = 6


def load_tc():
    """复用 `e3_title_contrast.py` 的**同一套**度量与截图函数（保证两处是同一把尺子）。"""
    spec = importlib.util.spec_from_file_location("e3_tc", os.path.join(HERE, "e3_title_contrast.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def plate_facts(bg_e):
    """底托件「素材 → 元素」映射与渐隐带（可复算）。"""
    ap = os.path.join(ASSETS, str(bg_e.get("asset", "")).replace("/", os.sep))
    img = Image.open(ap).convert("RGBA")
    al = np.asarray(img)[:, :, 3]
    nine = bg_e.get("nine")
    zero = bool(nine) and all(int(nine.get(k, 0)) == 0 for k in ("l", "t", "r", "b"))
    H, W, hh, ww = img.height, img.width, int(bg_e["h"]), int(bg_e["w"])
    rows = [int(al[i].max()) for i in range(H)]
    cols = [int(al[:, i].max()) for i in range(W)]
    dst_r = [rows[min(H - 1, int(round(r * H / float(hh))))] for r in range(hh)]
    dst_c = [cols[min(W - 1, int(round(c * W / float(ww))))] for c in range(ww)]
    sr = [r for r, a in enumerate(dst_r) if a >= 200]
    sc = [c for c, a in enumerate(dst_c) if a >= 200]
    return {"asset": os.path.basename(ap), "asset_size": [W, H], "el": [ww, hh], "nine": nine, "zero_nine": zero,
            "alpha_ge200_pct": round(float((al >= 200).mean()) * 100.0, 3), "alpha_lt200_px": int((al < 200).sum()),
            "solid_rows": (sr[0], sr[-1]) if sr else None, "fade_rows": hh - len(sr),
            "solid_cols": (sc[0], sc[-1]) if sc else None, "fade_cols": ww - len(sc)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tc = load_tc()
    sc = tc.screen_of()
    els = {e["id"]: e for e in sc.get("elements", [])}
    ids = [i for i in ("fc.label.%04d" % n for n in range(1, N + 1)) if i in els]
    txt_ids = [i + "_tx" for i in ids if (i + "_tx") in els]
    print("主干组名标签：%d 件（%s）｜ 屏数据 = %s" % (len(txt_ids), "、".join(txt_ids), tc.SCREEN_JSON))
    if not txt_ids:
        print("★ 数据里没有 fc.label.*_tx")
        return 2

    full_p = tc.shot("lab_full", None, None, os.path.join(tc.TMP, "lab_full.png"))
    ref_p = tc.shot("lab_ref", None, txt_ids, os.path.join(tc.TMP, "lab_ref.png"))
    full = np.asarray(Image.open(full_p).convert("RGB"))
    ref = np.asarray(Image.open(ref_p).convert("RGB"))

    rows, bad = [], []
    for tid in txt_ids:
        t = els[tid]
        rect = (t["x"], t["y"], t["w"], t["h"])
        st = tc.glyph_stats(full, ref, rect)
        if not st:
            bad.append("%s：字形带无差异" % tid); continue
        p5 = st["core_p5"] if st["core_p5"] is not None else None
        rec = {"id": tid, "text": t.get("sample", ""), "rect": rect, "glyph_px": st["n"], "core_n": st["core_n"],
               "bg": st["bg"], "ink": st["ink"], "contrast": st["contrast"],
               "core_p5": p5, "core_min": st["core_min"], "core_lt45": st["core_lt45"], "core_bg_uniq": st["core_bg_uniq"]}
        rows.append(rec)
        tc.crop_save(full, ref, rect, os.path.join(EVID, PREFIX + "%s.png" % tid))
        if st["bad_mask"].any():
            tc.crop_save_annot(full, st["bad_mask"], rect, os.path.join(EVID, PREFIX + "%s_未达标像素标注.png" % tid))
        if p5 is not None and p5 < 4.5:
            bad.append("%s：核心 p5 %.2f:1 < 4.5（中位 %.2f，min %.2f，核心 %d px 中 %d px <4.5；核心底托色种 %d）"
                       % (tid, p5, st["contrast"], st["core_min"], st["core_n"], st["core_lt45"], st["core_bg_uniq"]))

    print("\n  %-16s %-30s %-8s %-8s %-9s %s" % ("件", "文案", "中位", "核心p5", "核心min", "<4.5 核心px"))
    for r in rows:
        print("  %-16s %-30s %-8.2f %-8s %-9s %d"
              % (r["id"], r["text"][:28], r["contrast"],
                 ("%.2f" % r["core_p5"]) if r["core_p5"] is not None else "-",
                 ("%.2f" % r["core_min"]) if r["core_min"] is not None else "-",
                 r["core_lt45"] if r["core_lt45"] is not None else -1))
    p5s = [r["core_p5"] for r in rows if r["core_p5"] is not None]
    print("\n  p5 六件：%s ⇒ %s" % ("、".join("%.2f" % c for c in p5s),
                                  "全部 ≥4.5" if p5s and min(p5s) >= 4.5 else "存在 <4.5"))
    facts = plate_facts(els[ids[0]])
    print("\n  ★ 事实（本轮不改）：主干标签底托件 %s ← 素材 %s（%dx%d）⇒ 元素 %dx%d ｜ nine=%s%s"
          % (ids[0], facts["asset"], facts["asset_size"][0], facts["asset_size"][1],
             facts["el"][0], facts["el"][1], facts["nine"], "（全零 ⇒ 整图拉伸）" if facts["zero_nine"] else ""))
    print("    素材独立复量：α≥200 占比 %.3f%%（α<200 像素 %d 个）｜ 渲染后不透明行 %s（渐隐 %d 行）、不透明列 %s（渐隐 %d 列）"
          % (facts["alpha_ge200_pct"], facts["alpha_lt200_px"], facts["solid_rows"], facts["fade_rows"],
             facts["solid_cols"], facts["fade_cols"]))

    txt = ["E3 主干组名标签可读性（ISSUE-20260928-02 · HTML 侧 · 任务 4 顺带核）",
           "尺子：与 e3_title_contrast.py **同一套**（同层两张图取字形像素 → 字形核心逐像素 WCAG → 5 分位）",
           "屏数据 = %s" % tc.SCREEN_JSON, ""]
    for r in rows:
        txt.append("%-16s 中位%.2f:1 核心p5=%s 核心min=%s 核心%dpx <4.5=%s 核心底托色种%d 底板%s 文案=%s"
                   % (r["id"], r["contrast"],
                      ("%.2f" % r["core_p5"]) if r["core_p5"] is not None else "-",
                      ("%.2f" % r["core_min"]) if r["core_min"] is not None else "-",
                      r["core_n"], r["core_lt45"], r["core_bg_uniq"], r["bg"], r["text"]))
    txt += ["", "p5 六件：%s ⇒ %s" % ("、".join("%.2f" % c for c in p5s),
                                     "全部 ≥4.5" if p5s and min(p5s) >= 4.5 else "存在 <4.5"),
            "★ 事实（本轮不改）：底托件 %s ← 素材 %s（%dx%d）⇒ 元素 %dx%d ｜ nine=%s%s"
            % (ids[0], facts["asset"], facts["asset_size"][0], facts["asset_size"][1],
               facts["el"][0], facts["el"][1], facts["nine"], "（全零 ⇒ 整图拉伸）" if facts["zero_nine"] else ""),
            "  素材独立复量：α≥200 %.3f%%（α<200 %d px）｜ 不透明行 %s（渐隐 %d）／不透明列 %s（渐隐 %d）"
            % (facts["alpha_ge200_pct"], facts["alpha_lt200_px"], facts["solid_rows"], facts["fade_rows"],
               facts["solid_cols"], facts["fade_cols"]),
            "未达 4.5 项：" + ("；".join(bad) if bad else "无")]
    io.open(os.path.join(EVID, LOGNAME), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    print("\n裁图：%s<件>[_未达标像素标注].png ｜ 日志：%s" % (PREFIX, LOGNAME))
    import shutil
    shutil.rmtree(tc.UD, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
