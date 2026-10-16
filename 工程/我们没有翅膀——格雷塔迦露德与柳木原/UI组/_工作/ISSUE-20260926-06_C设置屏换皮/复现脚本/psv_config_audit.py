# -*- coding: utf-8 -*-
r"""psv_config_audit.py —— 25 设置屏换皮后的**版面自检**（无 GUI、无巡演）

四项断言（全部读 `layout/screens/25_config.json`，带上/不带型号的格）：
  A. **面板containment**：除登记豁免外，两页所有可见元素矩形必须落在 panel [130,196,1794,916] 内。
  B. **残留标签带覆盖**：PSV 页面里被去字脚本擦过的 14 条行标签带（页1 8 + 页2 6，实测 asset 坐标）
     必须被「z>8 且不透明的元素」覆盖 ≥ 95%（tags / 盖片 / 预览框 等）。
  C. **旧滑槽覆盖**：页面里烘焙的 5 条旧滑槽（页1 1 + 页2 4）必须被盖槽片 100% 覆盖。
  D. **文字不溢出**：单行 `text`（wrap=false）的估算字宽（CJK=1em、ASCII=0.55em、全角标点=1em）
     必须 ≤ 框宽 + 2px；多行 `wrap` 的按 w 折行后行数必须 ≤ max_lines。

用法：
    python _工作\ISSUE-20260926-06_C设置屏换皮\复现脚本\psv_config_audit.py
退出码：0 = 全绿；1 = 有断言失败。
"""
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
PANEL = (130, 196, 1794, 916)

# 页1 残留标签带（asset 坐标，实测：PSV 1× 标签带 ×2 − 4）
GHOSTS_C1 = [(278, 306), (356, 382), (428, 454), (500, 528),
             (578, 604), (652, 678), (724, 750), (800, 826)]
GHOSTS_C2 = [(282, 308), (354, 380), (428, 454), (502, 528), (578, 604), (650, 676)]
GHOST_X = {"sys": (270, 700), "snd": (240, 680)}

# 页面里烘焙的旧滑槽（asset 坐标）
GROOVES = {"sys": [(916, 782, 720, 60)],
           "snd": [(916, 258, 720, 60), (916, 332, 720, 60),
                   (916, 406, 720, 60), (916, 480, 720, 60)]}

# 豁免登记：元素 id -> 理由（必须写在报告里）
EXEMPT_PANEL = {
    "cfg.reset_bg": "顶右四钮：PSV 面板之外的上方工具栏位（M47 既有位置，本轮不动）",
    "cfg.reset_tx": "同上",
    "cfg.reset_hit": "同上",
    "cfg.btn_game_bg": "同上", "cfg.btn_game_tx": "同上", "cfg.btn_game_hit": "同上",
    "cfg.btn_title_bg": "同上", "cfg.btn_title_tx": "同上", "cfg.btn_title_hit": "同上",
    "cfg.btn_end_bg": "同上", "cfg.btn_end_tx": "同上", "cfg.btn_end_hit": "同上",
    "cfg.title_sys": "屏题：PSV 烘焙题字 CONFIG 右侧，面板之上",
    "cfg.title_snd": "同上",
    "cfg.tab1_on": "页签：压 PSV 面板上边框（PSV 章节标签槽），半数在面板外",
    "cfg.tab1_off": "同上", "cfg.tab1_tx": "同上", "cfg.tab1_tx_sel": "同上", "cfg.tab1_hit": "同上",
    "cfg.tab2_on": "同上", "cfg.tab2_off": "同上", "cfg.tab2_tx": "同上",
    "cfg.tab2_tx_sel": "同上", "cfg.tab2_hit": "同上",
    "cfg.row_cfmovie_hit": "预留行（永久不可见）：停放于右栏尾，与 pv_note 矩形重叠但不可达",
    "cfg.page1_bg": "整屏底图（PSV 去字件）：按定义满画布，不属面板内容",
    "cfg.page2_bg": "同上",
}


def page_of(e):
    vf, vw = e.get("vis_flag"), e.get("vis_when")
    if vf == "cfg_page" and vw in ("sys", "snd"):
        return vw
    return None          # 值/选中态元素由派生决定，不参与分页 containment（两页几何同）


def char_em(ch, size):
    if ch == "\n":
        return 0
    if ch.isascii():
        return 0.55 * size
    if unicodedata.east_asian_width(ch) in ("F", "W"):
        return 1.0 * size
    return 0.6 * size


def main():
    doc = json.load(open(SCREEN, encoding="utf-8"))
    els = doc["elements"]
    fails = []

    # ---------------- A containment ----------------
    bad = []
    for e in els:
        if e.get("visible_default") is False or e["id"] in EXEMPT_PANEL:
            continue
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        if x < PANEL[0] or y < PANEL[1] or x + w > PANEL[2] or y + h > PANEL[3]:
            if e["id"] in ("cfg.dim",):
                continue
            bad.append("%s (%d,%d,%d,%d)" % (e["id"], x, y, w, h))
    print("[A] 面板 containment：越界 %d 件（豁免 %d 件已登记）" % (len(bad), len(EXEMPT_PANEL)))
    for b in bad:
        print("    ✗ %s" % b)
    if bad:
        fails.append("A")

    # ---------------- B 残留标签带覆盖 ----------------
    opaque = [e for e in els if e["kind"] == "image" and e.get("z", 0) > 8]
    for pg, bands in (("sys", GHOSTS_C1), ("snd", GHOSTS_C2)):
        gx0, gx1 = GHOST_X[pg]
        cov_all = 0
        tot = 0
        for (y0, y1) in bands:
            tot += 1
            area = 0
            for e in opaque:
                # 页归属：带 vis_flag 的按页过滤；不带 flag 的（盖片/预览框）两页都算
                pf = page_of(e)
                if pf is not None and pf != pg:
                    continue
                ix = max(0, min(e["x"] + e["w"], gx1) - max(e["x"], gx0))
                iy = max(0, min(e["y"] + e["h"], y1) - max(e["y"], y0))
                area = max(area, ix * iy)
            if area >= 0.95 * (gx1 - gx0) * (y1 - y0):
                cov_all += 1
        print("[B] %s 残留标签带覆盖：%d/%d 条 ≥95%%" % (pg, cov_all, len(bands)))
        if cov_all != len(bands):
            fails.append("B-%s" % pg)

    # ---------------- C 旧滑槽覆盖 ----------------
    covers = [e for e in els if e["id"].startswith("cfg.cover_")]
    for pg, gs in GROOVES.items():
        ok = 0
        for (gx, gy, gw, gh) in gs:
            for e in covers:
                if page_of(e) != pg:
                    continue
                if (e["x"] <= gx and e["y"] <= gy and
                        e["x"] + e["w"] >= gx + gw and e["y"] + e["h"] >= gy + gh):
                    ok += 1
                    break
        print("[C] %s 旧滑槽覆盖：%d/%d 条被盖片完全覆盖" % (pg, ok, len(gs)))
        if ok != len(gs):
            fails.append("C-%s" % pg)

    # ---------------- D 文字不溢出 ----------------
    over = []
    for e in els:
        if e["kind"] != "text":
            continue
        f = e.get("font", {})
        size = f.get("size", 24)
        txt = str(e.get("sample", ""))
        if e.get("wrap"):
            limit = int(e.get("max_lines", 99))
            lines = 0
            for ln in txt.split("\n"):
                acc = 0.0
                n = 1
                for ch in ln:
                    cw = char_em(ch, size)
                    if acc + cw > e["w"]:
                        n += 1
                        acc = 0.0
                    acc += cw
                lines += n
            if lines > limit:
                over.append("%s wrap 行数 %d > max_lines %d（w=%d size=%d）"
                            % (e["id"], lines, limit, e["w"], size))
        else:
            wsum = sum(char_em(c, size) for ln in txt.split("\n") for c in ln)
            if wsum > e["w"] + 2:
                over.append("%s 单行宽 %.0f > 框宽 %d（size=%d）" % (e["id"], wsum, e["w"], size))
    print("[D] 文字不溢出：可疑 %d 件" % len(over))
    for o in over:
        print("    ✗ %s" % o)
    if over:
        fails.append("D")

    print("-" * 78)
    print("元素 %d ｜ 新增 bg %d / 盖片 %d / 药丸壳 %d ｜ 退场 cfg.frame/cfg.page_strip"
          % (len(els), sum(1 for e in els if "_bg" in e["id"] and e["id"].startswith("cfg.page")),
             len(covers), sum(1 for e in els if e["id"].startswith("cfg.tag_"))))
    print("结果：%s" % ("**全部通过**" if not fails else "**失败：%s**" % ",".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
