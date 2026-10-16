# -*- coding: utf-8 -*-
r"""m09_selfcheck.py —— ISSUE-20260926-09 三项自证（几何 / 资产 / 删除合并）· **含第二轮订正①②**

输出同时落盘 `_工作\ISSUE-20260926-09_config\取证\几何自证.txt`，并打印到 stdout。
任一项 FAIL ⇒ 退出码 2。

期望值（第二轮终态）：
  · 位移集合 **126 件，全部 +30**（第一轮 103 ＋ 订正②首行 5 ＋ 订正①滑条族 18）
  · 收窄 **17 件**：订正② 首行 5（221→195）／订正① 轨 6（360→330）／订正① 热区 6（380→350）
  · 订正① MAX 端点（`sl_*_end_hi` 6 件）**不动**（x=1046，右沿 1092 = 轨右沿）
  · 药丸右沿 726 ↔ 轨左沿 **762 = 36px**；`sl_*_end_hi` 右沿 = 轨右沿 = 1092
  · `tag_snd_0N × sl_*_hit` 相交 **= 0**；与角色列/banner（x=1110）**新增相交 = 0**（可见件与 hit 双 0）

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python "_工作\ISSUE-20260926-09_config\复现脚本\m09_selfcheck.py"
"""
import glob
import hashlib
import io
import json
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(UI, "_工作", "ISSUE-20260926-09_config")
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
BAK = os.path.join(EV, "原形备份", "25_config.json")
ARCH = os.path.join(UI, "_工作", "ISSUE-20260926-09_药丸底图", "旧素材归档")
UI_ASSETS = os.path.join(UI, "krkr", "assets", "ui")
AE = os.path.join(UI, "_工作", "ISSUE-20260926-09_药丸底图", "取证", "_ai_fit.png")
BLANK = os.path.join(UI_ASSETS, "x_ui_psv_pill_blank.png")
GEN = [os.path.join(UI, "layout", "ui_layout.json"),
       os.path.join(UI, "krkr", "game", "ui_layout.tjs"),
       os.path.join(UI, "复刻", "ui_layout.js")]
SHOTS = os.path.abspath(os.path.join(UI, "..", "..", "..", "临时", "ui_run", "runtime", "savedata"))

PANEL_INNER = 160
RIGHT_COL = 1180
COL_1110 = 1110            # 右邻「角色语音设定」一列 / banner 的左沿（订正① 的碰撞参照）
PILL_IDS = ["cfg.tag_sys_%02d" % n for n in range(1, 9)] + ["cfg.tag_snd_%02d" % n for n in range(1, 7)]
SEC_IDS = ["cfg.sec_picture", "cfg.sec_volume", "cfg.sec_voice"]
DELETED = ["cfg.title_sys", "cfg.title_snd", "cfg.sec_confirm", "cfg.tab1_tx_sel", "cfg.tab2_tx_sel"]
TABTX = ["cfg.tab1_tx", "cfg.tab2_tx"]
ROWS = ["display", "facewindow", "drama", "effect", "voicecut", "curhide", "savedialog", "loaddialog"]
SLD_ROWS = ["master", "bgm", "se", "sysse", "voice", "char"]
MARK2A = "ISSUE-20260926-09·订正①·移+30并收窄"
DISPLAY_IDS = ["cfg.o_display_off%s" % s for s in ("", "_hit", "_sel", "_tx", "_tx_sel")]
RIGHT_SLD = ["cfg.sl_%s%s" % (k, s) for k in ("winopac", "textspeed", "autospeed")
             for s in ("", "_hit", "_end_lo", "_end_hi")]
# 订正① 期望：# id -> (旧x, 新x, 旧w, 新w 或 None 表示不变)
SLD_EXP = {}
for _r in SLD_ROWS:
    SLD_EXP["cfg.sl_%s" % _r] = (732, 762, 360, 330)
    SLD_EXP["cfg.sl_%s_hit" % _r] = (722, 752, 380, 350)
    SLD_EXP["cfg.sl_%s_end_lo" % _r] = (732, 762, 46, None)
    SLD_EXP["cfg.sl_%s_end_hi" % _r] = (1046, 1046, 46, None)

out = []
FAIL = []
WARN = []


def p(s=""):
    out.append(s)
    print(s)


def md5(p_):
    with open(p_, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def rect(e):
    return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])


def page_of(eid):
    if eid == "cfg.dim" or eid.startswith(("cfg.tab1_", "cfg.tab2_", "cfg.btn_", "cfg.reset_")):
        return "both"
    if eid.startswith(("cfg.page1_bg", "cfg.tag_sys", "cfg.sec_picture", "cfg.cover_c1",
                       "cfg.pv_bg", "cfg.pv_frame", "cfg.pv_mask", "cfg.pv_text", "cfg.pv_note",
                       "cfg.pv_note_x", "cfg.sec_text", "cfg.sec_preview", "cfg.title_sys",
                       "cfg.sec_confirm")):
        return "sys"
    if eid.startswith("cfg.o_") and not eid.startswith("cfg.o_mute_vol_"):
        if any(eid.startswith("cfg.o_%s_" % r) for r in ROWS):
            return "sys"
    if eid.startswith("cfg.row_"):
        return "sys"
    if any(eid.startswith("cfg.sl_%s" % r) for r in ("winopac", "textspeed", "autospeed")):
        return "sys"
    if eid.startswith(("cfg.page2_bg", "cfg.tag_snd", "cfg.sec_volume", "cfg.sec_voice",
                       "cfg.snd_vol_", "cfg.cover_c2_", "cfg.banner_frame", "cfg.ch_",
                       "cfg.pv_face_", "cfg.pv_name_", "cfg.title_snd")):
        return "snd"
    if eid.startswith("cfg.sl_") or eid.startswith("cfg.o_mute_vol_"):
        return "snd"
    return "both"


def same_page(a, b):
    pa, pb = page_of(a), page_of(b)
    return pa == "both" or pb == "both" or pa == pb


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if (w > 0 and h > 0) else 0


def load(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    return d, {e["id"]: e for e in d["elements"]}


def sys_shot():
    for f in sorted(glob.glob(os.path.join(SHOTS, "shot_*_config.png"))):
        im = Image.open(f).convert("RGB")
        px = list(im.crop((1540, 250, 1760, 480)).getdata())
        red = sum(1 for r, g, b in px if r > 140 and r - g > 50 and r - b > 50)
        if red <= 3000:
            return f
    return None


def main():
    d_now, now = load(SCREEN)
    d_bak, bak = load(BAK)

    p("=" * 96)
    p("m09 三项自证 ｜ ISSUE-20260926-09（含第二轮订正①「移 +30 并收窄」／订正②「移 +30 并收窄」）")
    p("=" * 96)
    p("被检数据：%s  (md5=%s)" % (SCREEN, md5(SCREEN)))
    p("改前快照：%s  (md5=%s)" % (BAK, md5(BAK)))

    # ══════════════════════════════════════════════════════════════════
    # 【1】位移自证
    # ══════════════════════════════════════════════════════════════════
    p()
    p("─" * 96)
    p("【1】位移自证")
    p("─" * 96)
    movers = [i for i in now if i in bak and now[i]["x"] != bak[i]["x"]]
    d_map = {}
    for i in movers:
        d_map.setdefault(now[i]["x"] - bak[i]["x"], []).append(i)
    p("  位移档位：%s" % {k: len(v) for k, v in sorted(d_map.items())})
    p("  位移件数合计 = %d（期望 **126 = 第一轮 103 ＋ 订正②首行 5 ＋ 订正①滑条族 18**）" % len(movers))
    ok = (len(movers) == 126 and set(d_map) == {30})
    p("  ⇒ %s（全部 +30，无任何例外档位）" % ("PASS" if ok else "FAIL"))
    if not ok:
        FAIL.append("位移件数/档位不符")

    # 订正① 逐类核（含 w 与「不动」件）
    p()
    p("  【订正①】声音页左列滑条族 24 件逐件核（轨 / 热区 / MIN 位移并收窄；MAX 不动）：")
    ok1 = True
    for i, (ox, nx, ow, nw) in sorted(SLD_EXP.items()):
        e, b = now[i], bak[i]
        good = (b["x"] == ox and e["x"] == nx)
        if nw is not None:
            good &= (b["w"] == ow and e["w"] == nw)
        else:
            good &= (b["w"] == ow == e["w"])
        ok1 &= good
        p("    %-26s x %4d → %4d ｜ w %3d → %3d ｜ 右沿 %4d → %4d  %s"
          % (i, b["x"], e["x"], b["w"], e["w"], b["x"] + b["w"], e["x"] + e["w"],
             "✓" if good else "✗"))
    n_sld_moved = sum(1 for i in SLD_EXP if now[i]["x"] != bak[i]["x"])
    n_sld_wide = sum(1 for i in SLD_EXP if now[i]["w"] != bak[i]["w"])
    p("  滑条族：位移 %d 件（期望 18）｜ 收窄 %d 件（期望 12）｜ MAX 端点不动 6 件" % (n_sld_moved, n_sld_wide))
    ok1 &= (n_sld_moved == 18 and n_sld_wide == 12)
    hi_ok = all(now[i]["x"] == 1046 and now[i]["w"] == 46 for i in SLD_EXP if i.endswith("_end_hi"))
    p("  ⇒ %s（MAX 端点 `_end_hi` 6 件 x=1046/w=46 全部未动：%s）"
      % ("PASS" if ok1 and hi_ok else "FAIL", "是" if hi_ok else "否"))
    if not (ok1 and hi_ok):
        FAIL.append("订正① 滑条族几何不符")
    # ★ 配套：轨的 rail.nine 必须为全零（使 w=330 合法、不计「缩放元素」）
    ZERO_NINE = {"l": 0, "t": 0, "r": 0, "b": 0}
    n_nine = sum(1 for r_ in SLD_ROWS if now["cfg.sl_%s" % r_]["rail"].get("nine") == ZERO_NINE)
    p("  轨 `rail.nine` 全零（{l:0,t:0,r:0,b:0}）= %d/6 件 —— 依据：`verify_ui.py` [2]"
      "「slider 的 rail **无 nine** ⇒ 元素 w 必须 = rail PNG 实宽(=360)」，"
      "而引擎仅在 `nine` 缺失时登记「缩放元素」；全零 nine 在 `uiWidgetNine` 里退化为"
      "**唯一一块整图 blit**（其余 8 块 dw/dh=0 被跳过）⇒ 与「按原样缩放」渲染一致。"
      "HTML 侧 `replica.js` 有 `isZeroNine` 分支。" % n_nine)
    if n_nine != 6:
        FAIL.append("轨 rail.nine 未设为全零（w=330 将导致 verify_ui 尺寸失败/缩放登记）")
    n_note_sld = sum(1 for i in SLD_EXP if MARK2A in (now[i].get("note") or ""))
    p("  滑条族订正 note = %d/24 处 ｜ 屏级 note 含 `%s`：%s"
      % (n_note_sld, MARK2A, "是" if MARK2A in d_now["note"] else "否"))
    if n_note_sld != 24 or MARK2A not in d_now["note"]:
        FAIL.append("订正① note 缺失")

    bad_right = [i for i in RIGHT_SLD if i in now and now[i]["x"] != bak[i]["x"]]
    p()
    p("  右列滑条三支（winopac / textspeed / autospeed）共 %d 件：被误动 %d 件（期望 0）"
      % (len(RIGHT_SLD), len(bad_right)))
    for i in RIGHT_SLD:
        p("      %-26s x=%4d w=%3d（未动）" % (i, now[i]["x"], now[i]["w"]))
    if bad_right:
        FAIL.append("右列滑条被误动：%s" % bad_right)
    ex20 = [i for i in movers if now[i]["x"] - bak[i]["x"] == 20]
    p("  旧「+20 例外」残留件数 = %d（期望 0）" % len(ex20))

    # 未动集合（含静音族、右列、页签、角色列、按钮族）
    must_not_move = (["cfg.tab1_on", "cfg.tab1_off", "cfg.tab1_tx_sel", "cfg.tab1_tx", "cfg.tab1_hit",
                      "cfg.tab2_on", "cfg.tab2_off", "cfg.tab2_tx_sel", "cfg.tab2_tx", "cfg.tab2_hit"]
                     + [i for i in bak if i.startswith("cfg.pv") or i.startswith("cfg.ch_")
                        or i.startswith("cfg.btn_") or i.startswith("cfg.reset")
                        or i.startswith("cfg.banner")]
                     + ["cfg.row_allskip_lb", "cfg.row_autospeed_lb", "cfg.sec_text", "cfg.sec_preview",
                        "cfg.row_winopac_lb", "cfg.row_textspeed_lb", "cfg.row_textcolchg_lb",
                        "cfg.row_cfmovie_lb", "cfg.o_mute_vol_bgm_on", "cfg.o_mute_vol_bgm_off",
                        "cfg.o_mute_vol_bgm_on_hit", "cfg.o_mute_vol_bgm_off_hit",
                        "cfg.snd_vol_bgm_mute_lb", "cfg.cover_c1", "cfg.cover_c2_01", "cfg.cover_c2_02",
                        "cfg.cover_c2_03", "cfg.cover_c2_04"] + RIGHT_SLD)
    bad = [i for i in must_not_move if i in now and i in bak and now[i]["x"] != bak[i]["x"]]
    p()
    p("  未动集合抽查：%d 件（页签 10 ＋ 右列/滑条三支/角色列/按钮族/静音族 %d）"
      % (len(must_not_move), len(must_not_move) - 10))
    p("  被误动件数 = %d（期望 0）" % len(bad))
    p("  ⇒ %s" % ("PASS" if not bad else "FAIL"))
    if bad:
        FAIL.append("未动集合被误动：%s" % bad)

    rows = [(i, now[i]["x"], now[i]["x"] + now[i]["w"]) for i in PILL_IDS + SEC_IDS]
    bad166 = [r for r in rows if r[1] != 166]
    cross = [r for r in rows if r[1] < PANEL_INNER]
    p()
    p("  tag_*/sec_* 左沿：%s（17 件）｜ 与面板内沿 x=%d 相交 = %d 件（期望 0）"
      % ("全部 = 166" if not bad166 else "异常 %s" % bad166, PANEL_INNER, len(cross)))
    ok = (not bad166 and not cross)
    p("  ⇒ %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        FAIL.append("tag_*/sec_* 左沿不符或与面板内沿相交")

    # 值按钮对与药丸间距
    p()
    p("  「药丸右沿 ↔ window 值按钮左沿」：")
    gaps_ok = True
    for r in ROWS:
        tag, btn = "cfg.tag_sys_%02d" % (ROWS.index(r) + 1), "cfg.o_%s_on" % r
        g_now = now[btn]["x"] - (now[tag]["x"] + now[tag]["w"])
        g_bak = bak[btn]["x"] - (bak[tag]["x"] + bak[tag]["w"])
        gaps_ok &= (g_now == g_bak == 20)
        p("    %-14s %2d → %2d px ｜ 药丸右沿 %4d ↔ 按钮左沿 %4d %s"
          % (r, g_bak, g_now, now[tag]["x"] + now[tag]["w"], now[btn]["x"],
             "✓" if g_now == g_bak == 20 else "✗"))
    p("  ⇒ %s（8/8 行恒 20px）" % ("PASS" if gaps_ok else "FAIL"))
    if not gaps_ok:
        FAIL.append("药丸↔值按钮相对间距改变")

    # ★ 订正① 验收：36px 左间距 + 轨/_hit 右沿不变 + MAX 对齐
    p()
    p("  【订正① 验收】「药丸右沿 ↔ 滑条轨左沿」逐行（期望 = 改前 36px）：")
    rail_ok = True
    for r in SLD_ROWS:
        tag, rail = "cfg.tag_snd_%02d" % (SLD_ROWS.index(r) + 1), "cfg.sl_%s" % r
        g_now = now[rail]["x"] - (now[tag]["x"] + now[tag]["w"])
        g_bak = bak[rail]["x"] - (bak[tag]["x"] + bak[tag]["w"])
        rail_ok &= (g_now == g_bak == 36)
        p("    %-8s 药丸右沿 %4d ｜ 轨左沿 %4d → %4d ｜ 间距 %2d → %2d %s"
          % (r, now[tag]["x"] + now[tag]["w"], bak[rail]["x"], now[rail]["x"], g_bak, g_now,
             "✓" if g_now == g_bak == 36 else "✗"))
    p("  ⇒ %s（6/6 行 = 36px ⇒ 恢复改前口径）" % ("PASS" if rail_ok else "FAIL"))
    if not rail_ok:
        FAIL.append("药丸↔轨左沿间距未恢复 36px")

    p()
    p("  【订正① 验收】轨 / `_hit` **右沿不变**（收窄后仍与改前相同；`_end_hi` 右沿 = 轨右沿对齐）：")
    edge_ok = True
    for r in SLD_ROWS:
        rail, hit, hi = "cfg.sl_%s" % r, "cfg.sl_%s_hit" % r, "cfg.sl_%s_end_hi" % r
        r_now, r_bak = now[rail]["x"] + now[rail]["w"], bak[rail]["x"] + bak[rail]["w"]
        h_now, h_bak = now[hit]["x"] + now[hit]["w"], bak[hit]["x"] + bak[hit]["w"]
        c11, c12 = (r_now == r_bak == 1092), (h_now == h_bak == 1102)
        c13 = (now[hi]["x"] + now[hi]["w"] == r_now)     # MAX 右沿与轨右沿对齐
        c14 = (now[hit]["x"] < now[rail]["x"]) and (now[hit]["x"] + now[hit]["w"] > r_now)
        edge_ok &= (c11 and c12 and c13 and c14)
        p("    %-8s 轨右沿 %4d → %4d %s ｜ _hit 右沿 %4d → %4d %s ｜ _end_hi 右沿 %4d = 轨右沿 %s ｜"
          " _hit 完整覆盖轨 %s"
          % (r, r_bak, r_now, "✓" if c11 else "✗", h_bak, h_now, "✓" if c12 else "✗",
             now[hi]["x"] + now[hi]["w"], "✓" if c13 else "✗", "✓" if c14 else "✗"))
    p("  ⇒ %s（6/6 行：轨右沿 1092 不变、_hit 右沿 1102 不变、_end_hi 右沿 1092 与轨右沿对齐、"
      "热区仍完整覆盖轨）" % ("PASS" if edge_ok else "FAIL"))
    if not edge_ok:
        FAIL.append("轨/_hit 右沿或 MAX 对齐不符")

    p()
    p("  【订正① 验收】`cfg.tag_snd_0N × cfg.sl_*_hit` 相交面积（**断言 = 0**）：")
    hit_ok = True
    for r in SLD_ROWS:
        tag, h = "cfg.tag_snd_%02d" % (SLD_ROWS.index(r) + 1), "cfg.sl_%s_hit" % r
        a_b, a_n = inter(rect(bak[tag]), rect(bak[h])), inter(rect(now[tag]), rect(now[h]))
        hit_ok &= (a_n == 0)
        p("    %-8s 改前 %4d px² → 改后 %4d px² %s" % (r, a_b, a_n, "✓" if a_n == 0 else "✗"))
    p("  ⇒ %s（6/6 行侵入 = 0）" % ("PASS" if hit_ok else "FAIL"))
    if not hit_ok:
        FAIL.append("药丸×滑条热区相交不为 0")

    p()
    p("  【订正① 验收】与**右邻 x=%d 一列**（`cfg.banner_frame` ＋ `cfg.ch_*` 名条列）新增相交 "
      "（**断言 可见件 = 0 且 hit 层 = 0**）：" % COL_1110)
    col_ids = [i for i in now if i in bak and
               (i == "cfg.banner_frame" or i.startswith("cfg.ch_"))]
    new_vis_col, new_hit_col = [], []
    sld_movers = [i for i in SLD_EXP if now[i]["x"] != bak[i]["x"]]
    for i in sld_movers:
        for j in col_ids:
            a_b = inter(rect(bak[i]), rect(bak[j]))
            a_n = inter(rect(now[i]), rect(now[j]))
            if a_n > a_b and a_n > 0:
                rec = (i, j, a_b, a_n)
                (new_hit_col if "hit" in now[i]["kind"] else new_vis_col).append(rec)
    p("    参照列件数 = %d（banner_frame ＋ ch_* 全部）｜ 订正① 位移件 = %d" % (len(col_ids), len(sld_movers)))
    p("    新增相交 — 可见件：%d 对 ｜ hit 层：%d 对" % (len(new_vis_col), len(new_hit_col)))
    for i, j, a0, a1 in (new_vis_col + new_hit_col)[:12]:
        p("      · %s × %s ：%d → %d px" % (i, j, a0, a1))
    ok = (not new_vis_col and not new_hit_col)
    p("  ⇒ %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        FAIL.append("与 x=1110 一列新增相交不为 0")

    # ★ 订正② 验收
    p()
    p("  【订正② 验收】首行「全屏模式」组：")
    ok2 = all(now[i]["x"] == 967 and now[i]["w"] == 195 for i in DISPLAY_IDS)
    p("    5 件全部 x=967 / w=195：%s ｜ 右沿 %d（期望 1162 < %d）"
      % ("是" if ok2 else "否", now["cfg.o_display_off"]["x"] + now["cfg.o_display_off"]["w"], RIGHT_COL))
    pairs_ok = True
    for r in ROWS:
        onb, offb = "cfg.o_%s_on" % r, "cfg.o_%s_off" % r
        g_now = now[offb]["x"] - (now[onb]["x"] + now[onb]["w"])
        pairs_ok &= (g_now == 16)
        p("      %-14s _on 右沿 %4d ↔ _off 左沿 %4d = %2dpx %s"
          % (r, now[onb]["x"] + now[onb]["w"], now[offb]["x"], g_now, "✓" if g_now == 16 else "✗"))
    wl = "cfg.row_winopac_lb"
    a_off_wl = inter(rect(now["cfg.o_display_off"]), rect(now[wl]))
    p("    ⇒ 8/8 行 = 16px：%s ｜ 与 `%s` 相交 = %d px²（期望 0）"
      % ("PASS" if pairs_ok else "FAIL", wl, a_off_wl))
    cen_ok = True
    for i in ("cfg.o_display_off_tx", "cfg.o_display_off_tx_sel"):
        same_align = (now[i].get("align") == bak[i].get("align") == "center"
                      and now[i].get("valign") == bak[i].get("valign") == "middle")
        cen_ok &= same_align
        p("    %-30s align=%s valign=%s（未改）｜ 新框中心 %.1f"
          % (i, now[i].get("align"), now[i].get("valign"), now[i]["x"] + now[i]["w"] / 2.0))
    p("    居中检查方式：① 断言 `align=center`/`valign=middle` 与改前逐值相同（未改左对齐）；"
      "② 几何：文字框中心 = x + w/2 = 1064.5；③ 实机墨迹中心像素级实测（下）。")
    sfile = sys_shot()
    if sfile:
        im = Image.open(sfile).convert("RGB")
        box = (967, 262, 1162, 321)
        reg = im.crop(box)
        w_, h_ = reg.size
        px = reg.load()
        xs, ys = [], []
        for y in range(h_):
            for x in range(w_):
                r, g, b = px[x, y]
                if 0.299 * r + 0.587 * g + 0.114 * b < 130:
                    xs.append(x)
                    ys.append(y)
        if xs:
            icx = box[0] + (min(xs) + max(xs)) / 2.0
            icy = box[1] + (min(ys) + max(ys)) / 2.0
            dcen = icx - 1064.5
            p("    ③ 实机墨迹中心（%s，区域 %s，暗像素 %d 个）：x = %.1f ｜ 框中心 1064.5 ｜ 偏差 %+.1f px"
              " ｜ y = %.1f（框中心 291.5）" % (os.path.basename(sfile), box, len(xs), icx, dcen, icy))
            cen_ok &= (abs(dcen) <= 6)
        else:
            p("    ③ 实机墨迹：区域 %s 内未找到暗像素 —— SKIP" % (box,))
    else:
        p("    ③ 实机墨迹中心：未找到巡演截图 ⇒ SKIP")
    ok_all2 = ok2 and pairs_ok and a_off_wl == 0 and cen_ok
    p("  ⇒ %s" % ("PASS" if ok_all2 else "FAIL"))
    if not ok_all2:
        FAIL.append("订正② 自证失败")

    # 全屏相交体检
    p()
    p("  相交体检（位移件 %d × **同页**其余全部元素；改前几何取原形备份）：" % len(movers))
    map_bad = [i for i, e in now.items()
               if e.get("vis_flag") == "cfg_page" and e.get("vis_when") in ("sys", "snd")
               and page_of(i) not in (e["vis_when"], "both")]
    p("    页归属映射核对（与 `vis_flag=cfg_page` 的 `vis_when` 冲突件数）= %d（期望 0）" % len(map_bad))
    new_vis, grew_vis, shrunk_vis, grew_hit, right_cross = [], [], [], [], []
    base_pairs = now_pairs = skipped = 0
    for i in movers:
        a_now, a_bak = rect(now[i]), rect(bak[i])
        if a_now[2] > RIGHT_COL:
            right_cross.append((i, a_now[2]))
        for j in now:
            if j == i or j not in bak:
                continue
            if not same_page(i, j):
                skipped += 1
                continue
            s_now, s_bak = inter(a_now, rect(now[j])), inter(a_bak, rect(bak[j]))
            base_pairs += 1 if s_bak > 0 else 0
            now_pairs += 1 if s_now > 0 else 0
            if s_now == s_bak:
                continue
            hitpair = "hit" in (now[i]["kind"], now[j]["kind"])
            if s_now > s_bak:
                if hitpair:
                    grew_hit.append((i, j, s_bak, s_now))
                elif s_bak == 0:
                    new_vis.append((i, j, s_bak, s_now))
                else:
                    grew_vis.append((i, j, s_bak, s_now))
            elif not hitpair and s_now == 0:
                shrunk_vis.append((i, j, s_bak))
    p("    已跳过跨页对：%d 对" % skipped)
    p("    同页相交对总数：改前 %d → 改后 %d（含既有设计性重叠：药丸⊃自身行名、热区⊃其底板、"
      "轨⊃静音簇等）" % (base_pairs, now_pairs))
    p("    A. **新增**相交对 — 可见件：%d 对" % len(new_vis))
    for i, j, s0, s1 in new_vis:
        p("      · %s × %s ：%d → %d px" % (i, j, s0, s1))
    p("    B. 既有相交**面积变大** — 可见件：%d 对（改前已相交 ⇒ 非新增）" % len(grew_vis))
    for i, j, s0, s1 in grew_vis:
        p("      · %s × %s ：%d → %d px" % (i, j, s0, s1))
    p("    C. 相交**消失** — 可见件：%d 对" % len(shrunk_vis))
    for i, j, s0 in shrunk_vis[:10]:
        p("      · %s × %s ：%d → 0 px" % (i, j, s0))
    p("    D. 新增/变大相交 — 含 hit 热区（不可见覆盖层）：新增 %d 对 / 变大 %d 对"
      % (len([r for r in grew_hit if r[2] == 0]), len([r for r in grew_hit if r[2] > 0])))
    for i, j, s0, s1 in grew_hit:
        p("      · %s × %s ：%d → %d px" % (i, j, s0, s1))
    p("    E. 右沿越过右列左沿 x=%d 的位移件：%d 件（期望 0）" % (RIGHT_COL, len(right_cross)))
    for i, r in right_cross[:8]:
        p("      · %s 右沿 %d" % (i, r))
    ok = (not new_vis and not right_cross)
    p("  ⇒ %s（同页可见件**零新增**相交、零越过右列；变大 %d 对与 hit 层 %d 对均为"
      "「改前已相交 / 不可见层」）" % ("PASS" if ok else "FAIL", len(grew_vis), len(grew_hit)))
    if not ok:
        FAIL.append("位移引入同页可见件新增相交或越过右列")

    # ══════════════════════════════════════════════════════════════════
    # 【2】资产自证
    # ══════════════════════════════════════════════════════════════════
    p()
    p("─" * 96)
    p("【2】资产自证")
    p("─" * 96)
    src = Image.open(AE)
    new = Image.open(BLANK)
    sa, na = src.getchannel("A").tobytes(), new.getchannel("A").tobytes()
    maxd = 0
    for ch in range(3):
        sb, nb = src.getchannel(ch).tobytes(), new.getchannel(ch).tobytes()
        maxd = max(maxd, max(abs(x - y) for x, y in zip(sb, nb)))
    lowbits = set()
    for ch in range(3):
        lowbits |= set(v & 3 for v in new.getchannel(ch).tobytes())
    p("  新件：%s" % BLANK)
    p("    尺寸 %dx%d（期望 560×72）｜ 模式 %s ｜ md5 %s"
      % (new.size[0], new.size[1], new.mode, md5(BLANK)))
    p("    alpha 与源件 `_ai_fit.png` 逐字节一致：%s" % ("是" if sa == na else "否"))
    p("    RGB 逐像素 max|Δ|（&0xFC 量化前→后）= %d（要求 ≤ 4）｜ RGB 低 2bit 集合 = %s"
      % (maxd, sorted(lowbits)))
    ok = (new.size == (560, 72) and sa == na and maxd <= 4 and lowbits == {0} and src.size == (560, 72))
    p("  ⇒ %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        FAIL.append("新药丸件自证失败")

    rd = io.open(os.path.join(ARCH, "README.md"), encoding="utf-8").read()
    names = ["x_ui_psv_pill_c1_%02d.png" % n for n in range(1, 9)] + \
            ["x_ui_psv_pill_c2_%02d.png" % n for n in range(1, 7)]
    miss = [n for n in names if not os.path.isfile(os.path.join(ARCH, n))]
    md5_bad = [n for n in names if md5(os.path.join(ARCH, n)) not in rd]
    leftovers = [f for f in os.listdir(UI_ASSETS) if f.startswith("x_ui_psv_pill_c")]
    p("  旧件归档：14 件齐备 = %s ｜ md5 与 README 登记一致 = %s ｜ assets/ui 残留 = %d 件（期望 0）"
      % ("是" if not miss else "否", "是" if not md5_bad else "否", len(leftovers)))
    ok = (not miss and not md5_bad and not leftovers)
    p("  ⇒ %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        FAIL.append("旧件归档/残留检查失败")

    # ══════════════════════════════════════════════════════════════════
    # 【3】删除 / 合并自证
    # ══════════════════════════════════════════════════════════════════
    p()
    p("─" * 96)
    p("【3】删除 / 合并自证")
    p("─" * 96)
    allok = True
    for i in DELETED:
        hits = []
        for f in [SCREEN] + GEN:
            n = len(re.findall(r'"%s"' % re.escape(i), io.open(f, encoding="utf-8").read()))
            if n:
                hits.append("%s×%d" % (os.path.basename(f), n))
        ok = not hits
        allok &= ok
        p("    %-22s 屏 JSON ＋ 三处生成物残留：%s  %s" % (i, "无" if not hits else " ".join(hits),
                                                          "✓" if ok else "✗"))
    for i in TABTX:
        e = now[i]
        ok = "vis_when" not in e and "vis_flag" not in e
        allok &= ok
        p("    %-22s vis_when=%s  vis_flag=%s  %s"
          % (i, e.get("vis_when", "（无）"), e.get("vis_flag", "（无）"), "✓" if ok else "✗"))
    col_ok = all(now[i]["font"]["color"] == "@palette.psv_ink" for i in TABTX)
    allok &= col_ok
    p("  页签名颜色保持 @palette.psv_ink：%s ｜ 元素总数 %d → %d（删除 5 件）"
      % ("是" if col_ok else "否", len(bak), len(now)))
    allok &= (len(bak) - len(now) == 5)
    p("  ⇒ %s" % ("PASS" if allok else "FAIL"))
    if not allok:
        FAIL.append("删除/合并自证失败")

    p()
    p("=" * 96)
    p("汇总：%s" % ("**三项自证全部 PASS（含第二轮订正①②）**" if not FAIL
                  else "**FAIL**：" + "；".join(FAIL)))
    p("=" * 96)
    os.makedirs(os.path.join(EV, "取证"), exist_ok=True)
    with io.open(os.path.join(EV, "取证", "几何自证.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return 2 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
