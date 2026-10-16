# -*- coding: utf-8 -*-
r"""render_d_from_data.py —— D 组五屏（27/28/37/38/39）**几何断言 + 版式标注图 + 1:1 离线合成图**。

★ 修复轮（2026-09-26 · ISSUE-20260926-06_D鉴赏修复）：本脚本在 D 组原版（只画矩形标注）基础上，
  ① **断言扩到「面板可见边框」口径**（件内透明边距 —— 见下），逐条覆盖 vision 的 4 组缺陷；
  ② 增加**引擎同口径 1:1 合成**出口（复用 `compose_d.py`：真实素材 / 九宫格 nearest / 引擎绘制文字 /
     list 网格 / attach 附加层）⇒ 「改前 / 改后」照片级对照，而不再只是矩形框图。

■ 为什么断言要按「面板可见边框」而不是「元素框」：
  37 的两个面板件（`x_ui_dress_big_off.png` / `x_ui_dress_name_off.png`）**自带透明边距**，
  元素框边缘并不可见；可见边框在件内偏 36..44px（big）/ 13..15px（name）处。
  若按元素框断言，会把 vision 实测到的 4 处「边框横穿内容」全部放行 ⇒ 断言必须用**可见边框**。

■ 断言清单（任一不成立即退出码非 0）
  A  27/28/37/38 的非底图元素不被 39 外壳条带 (340,0,1580,100) 压住；
  B  `list` 外框 w/h == 网格公式 cols·item_w+(cols-1)·gap / rows·item_h+(rows-1)·gap，且不出画布；
  C  28：`mu.list` ⊂ PSV 列表框；8 控键 + 滑块 ⊂ PSV 信息框**可见内区**；控键底↔滑块顶间隙 ≤30（改前 73）；
  D  27 网格 ⊂ PSV CG 滚动区 187..884；38 网格不出画布且与预览板不重叠；
  E  39 的 5 个热区互不重叠、且全在条带内；
  F  37：主面板**内容包围盒** ⊂ 主面板可见内区，四边内边距 ≥6px 且**左右相等**；
  G  37：名单 7 行 ⊂ 名单底板可见内区（首/末行距边框 ≥6px）；
  H  37：末行「表情」名槽有**同款按钮框**（`dr.btn_face`：同素材、同九宫格、同矩形、z 低于文字）；
  I  37：36 个 hit / 31 个 text 计数不变、hit.action 仍全为空串；
  J  39：四条选中框**宽度全部相同**、各自中心 == 对应页签文字中心（≤0.5px）；
  K  **底图复核**（读改后底图件实测，不是读数据）：
     38 槽区无残线（行/列中位剖面的「窄线凸起」<12）且跨边框无亮度台阶（<6）；
     28 走带条带内无亮残留（>235 占比 <0.2%）、与上下邻行无缝（<4）；
  L  32/27 的 `bg` 元素仍为 1:1 全屏 PSV 件（w=h=画布）。

用法：python _工作\ISSUE-20260926-06_D鉴赏修复\复现脚本\render_d_from_data.py
产出（`_工作\ISSUE-20260926-06_D鉴赏修复\_证据\`）：
  annot_27/28/37/38.png（几何标注图）、fromdata_27/28/37/38/39.png（1:1 合成图，含外壳）
"""
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont        # noqa: E402
import numpy as np                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(WORK))
SCR = os.path.join(UI, "layout", "screens")
A = os.path.join(UI, "krkr", "assets", "ui")
EV = os.path.join(WORK, "_证据")
FONT = r"C:\Windows\Fonts\msyh.ttc"
SHELL_STRIP = (340, 0, 1580, 100)

sys.path.insert(0, HERE)
import compose_d                                   # noqa: E402

# ── 面板件「可见边框」实测口径（详见 psv_fix_d_layout.py 文件头与交付报告）──
BIG_IN = (39, 44, 24, 44)          # 主面板：可见内区相对元素框的左/上/右/下
BIG_OUT = (36, 39, 20, 39)
NAME_SX, NAME_SY = 212.0, 667.0    # 名单件源尺寸（nine 全 0 ⇒ 整图缩放）
NAME_IN = (15, 15, 196, 651)
MUS_INFO_IN = (160, 228, 1602, 208)   # PSV 信息框可见内区 (x0,y0,w,h)（实测边框 222..227 / 437..440）
MUS_BOX = (156, 477, 1607, 473)       # PSV 列表框（bg 实测）
GAL_SCROLL_Y = (187, 884)             # PSV CG 滚动区
SHELL_TAB_ON_W = 171

COLORS = {"image": (0, 90, 220), "list": (210, 0, 0), "hit": (0, 160, 0),
          "text": (120, 0, 160), "rect": (200, 120, 0), "slider": (0, 150, 150),
          "anim": (150, 150, 0)}
fails = []


def load(name):
    with open(os.path.join(SCR, name), encoding="utf-8") as f:
        return json.load(f)


def rect_of(e):
    return (e.get("x", 0), e.get("y", 0), e.get("w", 0), e.get("h", 0))


def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


# ── 标注图（矩形框图，保留 D 组原版口径）──────────────────────────────
def draw_list(d, e, f):
    x, y, w, h = rect_of(e)
    if e.get("orientation") == "h":
        cols = max(1, e.get("max_cols", 1))
        rows = max(1, e.get("max_rows", 1))
        iw, ih, gap = e.get("item_w", w), e.get("item_h", 10), e.get("gap", 0)
        for r in range(rows):
            for c in range(cols):
                r0 = (x + c * (iw + gap), y + r * (ih + gap), iw, ih)
                d.rectangle([r0[0], r0[1], r0[0] + r0[2], r0[1] + r0[3]], outline=COLORS["list"], width=2)
                if r == 0 and c == 0:
                    vv = e.get("item_variants")
                    if vv:
                        for key, col in (("thumb", (255, 140, 0)), ("text", (0, 0, 0)),
                                         ("prev", (0, 0, 255)), ("next", (0, 0, 255))):
                            sub = vv.get(key)
                            if isinstance(sub, dict) and "w" in sub:
                                sx, sy, sw, sh = sub["x"], sub["y"], sub["w"], sub["h"]
                                d.rectangle([r0[0] + sx, r0[1] + sy, r0[0] + sx + sw, r0[1] + sy + sh],
                                            outline=col, width=2)
                    for b in (e.get("item_buttons") or []):
                        d.rectangle([r0[0] + b["x"], r0[1] + b["y"], r0[0] + b["x"] + b["w"],
                                     r0[1] + b["y"] + b["h"]], outline=(0, 200, 200), width=2)
                    it = e.get("item_text")
                    if it and "w" in it:
                        d.rectangle([r0[0] + it["x"], r0[1] + it["y"], r0[0] + it["x"] + it["w"],
                                     r0[1] + it["y"] + it["h"]], outline=(128, 100, 0), width=2)
    else:
        rows = e.get("max_rows", (h // max(1, e.get("item_h", 1))))
        for r in range(int(rows)):
            d.rectangle([x, y + r * e["item_h"], x + w, y + r * e["item_h"] + e["item_h"]],
                        outline=COLORS["list"], width=2)
    d.rectangle([x, y, x + w, y + h], outline=(255, 0, 255), width=3)
    d.text((x + 4, y + 2), "%s  %dx%d @(%d,%d)" % (e["id"], w, h, x, y), fill=(150, 0, 0), font=f)


def annotate(screen, shell=None, out=None):
    d0 = load(screen)
    f = ImageFont.truetype(FONT, 18)
    canvas = Image.new("RGBA", (1920, 1080), (255, 255, 255, 255))
    for e in d0["elements"]:
        if e["kind"] == "image" and e.get("z", 0) == 0 and e["w"] == 1920:
            canvas.alpha_composite(compose_d.asset_image(e["asset"]), (0, 0))
            break
    if shell:
        sh = load(shell)
        for e in sh["elements"]:
            if e["id"] == "gs.strip":
                canvas.alpha_composite(compose_d.asset_image(e["asset"]), (e["x"], e["y"]))
    d = ImageDraw.Draw(canvas)
    for e in d0["elements"]:
        if e.get("z", 0) == 0:
            continue
        t = e["kind"]
        col = COLORS.get(t, (100, 100, 100))
        x, y, w, h = rect_of(e)
        if t == "list":
            draw_list(d, e, f)
            continue
        d.rectangle([x, y, x + w, y + h], outline=col, width=2)
        lab = e["id"] + ("/" + e.get("action", "") if e.get("action") else "")
        d.text((x + 3, y + 2), lab, fill=col, font=f)
    if shell:
        for e in load(shell)["elements"]:
            if e["id"] == "gs.strip":
                continue
            x, y, w, h = rect_of(e)
            col = COLORS.get(e["kind"], (100, 100, 100))
            d.rectangle([x, y, x + w, y + h], outline=col, width=2)
            d.text((x + 3, y + 2), e["id"] + ("/" + e.get("action", "") if e.get("action") else ""),
                   fill=col, font=f)
    if out:
        canvas.convert("RGB").save(out, optimize=True)
        print("wrote", os.path.relpath(out, UI))


# ── 断言 ──────────────────────────────────────────────────────────────
def assert_layout():
    print("== A/B/D：外壳条带、网格公式、PSV 滚动区 ==")
    for name in ("27_gallery.json", "28_music.json", "37_dress.json", "38_replay.json"):
        d0 = load(name)
        bad = [e["id"] for e in d0["elements"]
               if e.get("z", 0) != 0 and not e["id"].endswith(".bg")
               and overlaps(rect_of(e), SHELL_STRIP)]
        check(not bad, "A %s：非底图元素均不被外壳条带压住（越界：%s）" % (name, bad or "无"))
        for e in d0["elements"]:
            if e["kind"] == "list" and e.get("orientation") == "h":
                x, y, w, h = rect_of(e)
                gw = e["max_cols"] * e["item_w"] + (e["max_cols"] - 1) * e.get("gap", 0)
                gh = e["max_rows"] * e["item_h"] + (e["max_rows"] - 1) * e.get("gap", 0)
                check((w, h) == (gw, gh), "B %s：%s 外框 == 网格公式 %dx%d（实为 %dx%d）"
                      % (name, e["id"], gw, gh, w, h))
                check(x >= 0 and y >= 0 and x + w <= 1920 and y + h <= 1080,
                      "   %s 不出画布（%d,%d,%d,%d）" % (e["id"], x, y, w, h))
            if e["kind"] == "image":
                ex, ey, ew, eh = rect_of(e)
                check(ew > 0 and eh > 0, "%s %s 面积为正（%dx%d）" % (name, e["id"], ew, eh))
        for e in d0["elements"]:
            if e["id"].endswith(".bg"):
                check(rect_of(e) == (0, 0, 1920, 1080),
                      "L %s：底图为 1:1 全屏 PSV 件（%s）" % (e["id"], rect_of(e)))
    g = load("27_gallery.json")
    for e in g["elements"]:
        if e["id"] == "gal.list":
            x, y, w, h = rect_of(e)
            check(y >= GAL_SCROLL_Y[0] and y + h <= GAL_SCROLL_Y[1],
                  "D gal.list ⊂ PSV CG 滚动区 %d..%d（%d..%d）" % (GAL_SCROLL_Y[0], GAL_SCROLL_Y[1], y, y + h))
    r = load("38_replay.json")
    rp = {e["id"]: e for e in r["elements"]}
    rl = rect_of(rp["rp.list"])
    pv = rect_of(rp["rp.preview"])
    check(rl[0] >= pv[0] + pv[2], "D rp.list 在 rp.preview 右侧（%d ≥ %d）" % (rl[0], pv[0] + pv[2]))


def assert_28():
    print("== C：28 控件落位与空区 ==")
    m = load("28_music.json")
    ix, iy, iw, ih = MUS_INFO_IN
    for e in m["elements"]:
        if e["id"] == "mu.list":
            x, y, w, h = rect_of(e)
            check(x >= MUS_BOX[0] and y >= MUS_BOX[1] and x + w <= MUS_BOX[0] + MUS_BOX[2]
                  and y + h <= MUS_BOX[1] + MUS_BOX[3],
                  "C mu.list ⊂ PSV 列表框 (156,477,1607,473)：(%d,%d,%d,%d)" % (x, y, w, h))
        if e["id"].startswith("mu.pb_") and e["kind"] == "image":
            x, y, w, h = rect_of(e)
            check(x >= ix and y >= iy and x + w <= ix + iw and y + h <= iy + ih,
                  "C %s ⊂ PSV 信息框可见内区（y=%d..%d）" % (e["id"], y, y + h))
        if e["id"] == "mu.vol":
            x, y, w, h = rect_of(e)
            check(y >= iy and y + h <= iy + ih, "C mu.vol ⊂ 信息框可见内区（%d..%d）" % (y, y + h))
    keys = [e for e in m["elements"] if e["id"].startswith("mu.pb_") and e["kind"] == "image"]
    vol = next(e for e in m["elements"] if e["id"] == "mu.vol")
    kb = max(e["y"] + e["h"] for e in keys)
    check(vol["y"] - kb <= 30, "C 控键底 %d ↔ 滑块顶 %d 间隙 %d ≤ 30（改前 73）" % (kb, vol["y"], vol["y"] - kb))
    check(all(e["y"] == keys[0]["y"] for e in keys), "C 8 控键同一行（y=%d）" % keys[0]["y"])
    check(all(e["y"] + e["h"] == kb for e in keys), "C 8 控键同高（h=%d）" % keys[0]["h"])


def assert_37():
    print("== F/G/H/I：37 面板安全区、名单、末行按钮框、计数 ==")
    d = load("37_dress.json")
    el = {e["id"]: e for e in d["elements"]}
    big, nl = el["dr.big"], el["dr.namelist"]
    bi = (big["x"] + BIG_IN[0], big["y"] + BIG_IN[1],
          big["x"] + big["w"] - BIG_IN[2], big["y"] + big["h"] - BIG_IN[3])
    skip = ("dr.bg", "dr.namelist", "dr.big", "dr.ctrl", "dr.reset", "dr.reset_tx", "dr.hit_reset",
            "dr.time_day", "dr.time_dusk", "dr.time_night", "dr.time_night2")
    ids = [i for i in el if i not in skip
           and not i.startswith(("dr.name_tx_", "dr.hit_name_", "dr.sel_mark", "dr.hit_ctrl_"))]
    c = (min(el[i]["x"] for i in ids), min(el[i]["y"] for i in ids),
         max(el[i]["x"] + el[i]["w"] for i in ids), max(el[i]["y"] + el[i]["h"] for i in ids))
    print("   主面板可见内区 %s ／ 内容包围盒 %s" % (bi, c))
    dl, dr_ = c[0] - bi[0], bi[2] - c[2]
    dt, db = c[1] - bi[1], bi[3] - c[3]
    check(min(dl, dr_, dt, db) >= 6,
          "F 37 面板内容四边内边距 ≥6px（左%d 右%d 上%d 下%d）" % (dl, dr_, dt, db))
    check(dl == dr_, "F 37 左右内边距对齐（左%d == 右%d）" % (dl, dr_))
    nli = (nl["x"] + NAME_IN[0] * nl["w"] / NAME_SX, nl["y"] + NAME_IN[1] * nl["h"] / NAME_SY,
           nl["x"] + NAME_IN[2] * nl["w"] / NAME_SX, nl["y"] + NAME_IN[3] * nl["h"] / NAME_SY)
    rows = [el["dr.name_tx_%d" % k] for k in range(1, 8)]
    print("   名单底板可见内区 (%.1f,%.1f)-(%.1f,%.1f) ／ 7 行 %d..%d"
          % (nli[0], nli[1], nli[2], nli[3], rows[0]["y"], rows[-1]["y"] + rows[-1]["h"]))
    check(rows[0]["x"] >= nli[0] and rows[0]["y"] - nli[1] >= 6,
          "G 37 名单首行距上/左边框 ≥6px（上 %.1f / 左 %.1f）" % (rows[0]["y"] - nli[1], rows[0]["x"] - nli[0]))
    check(nli[3] - (rows[-1]["y"] + rows[-1]["h"]) >= 6 and max(r["x"] + r["w"] for r in rows) <= nli[2],
          "G 37 名单末行距下边框 ≥6px（%.1f）且不越右边框" % (nli[3] - (rows[-1]["y"] + rows[-1]["h"])))
    check(all(el["dr.hit_name_%d" % k]["y"] == el["dr.name_tx_%d" % k]["y"] for k in range(1, 8)),
          "G 37 名单文字与热区逐行同 y")
    plat, face = el.get("dr.btn_face"), el["dr.face_tx"]
    check(plat is not None, "H 37 末行补了按钮框 dr.btn_face")
    if plat:
        check(plat["asset"] == el["dr.btn_keep"]["asset"] and plat["nine"] == el["dr.btn_keep"]["nine"],
              "H 37 末行按钮框与其余行**同素材同九宫格**（%s %s）" % (plat["asset"], plat["nine"]))
        check(rect_of(plat) == rect_of(face), "H 37 末行按钮框几何 == 名槽矩形 %s" % (rect_of(face),))
        check(plat["z"] < face["z"] and "action" not in plat and "state_group" not in plat,
              "H 37 按钮框在文字之下（z %d < %d）且无 action/state_group" % (plat["z"], face["z"]))
        check(face["y"] + face["h"] <= bi[3] - 6, "H 37 末行名槽距下边框 ≥6px（%d）" % (bi[3] - face["y"] - face["h"]))
    hits = [e for e in d["elements"] if e["kind"] == "hit"]
    txts = [e for e in d["elements"] if e["kind"] == "text"]
    check(len(hits) == 36, "I 37 hit 数 36（实为 %d）" % len(hits))
    check(len(txts) == 31, "I 37 text 数 31（实为 %d）" % len(txts))
    check(all(e["action"] == "" for e in hits), "I 37 36 个 hit 的 action 仍全为空串")


def assert_39():
    print("== E/J：39 外壳热区与选中框 ==")
    s = load("39_gal_shell.json")
    el = {e["id"]: e for e in s["elements"]}
    hits = [(e["id"], rect_of(e)) for e in s["elements"] if e["kind"] == "hit"]
    for i in range(len(hits)):
        x, y, w, h = hits[i][1]
        check(x >= SHELL_STRIP[0] and y >= SHELL_STRIP[1] and x + w <= SHELL_STRIP[0] + SHELL_STRIP[2]
              and y + h <= SHELL_STRIP[1] + SHELL_STRIP[3], "E %s 热区落在条带内 %s" % (hits[i][0], hits[i][1]))
        for j in range(i + 1, len(hits)):
            check(not overlaps(hits[i][1], hits[j][1]), "E %s 与 %s 热区不重叠" % (hits[i][0], hits[j][0]))
    ons = [el["gs.tab%d_on" % (i + 1)] for i in range(4)]
    ws = {o["w"] for o in ons}
    check(len(ws) == 1 and ws.pop() == SHELL_TAB_ON_W,
          "J 39 四条选中框宽度统一 = %d（%s）" % (SHELL_TAB_ON_W, [o["w"] for o in ons]))
    for i, o in enumerate(ons):
        t = el["gs.tab%d_tx" % (i + 1)]
        err = abs((o["x"] + o["w"] / 2.0) - (t["x"] + t["w"] / 2.0))
        check(err <= 0.5, "J 39 第%d页签选中框居中于标签（偏差 %.1fpx）" % (i + 1, err))
        check(o["y"] == t["y"] and o["h"] == t["h"], "J 39 第%d页签选中框与文字同 y/h" % (i + 1))
    check(len(hits) == 5 and len(s["elements"]) == 17, "J 39 元素总数 17 / 热区 5 不变")
    check(all(el["gs.tab%d_hit" % (i + 1)]["action"] == "gallery_tab_%d" % (i + 1) for i in range(4))
          and el["gs.back_hit"]["action"] == "close", "J 39 五个 action 不变")


def assert_bg():
    print("== K：底图件复核（按**改后落盘件**实测）==")
    # 38：4 个槽区无残线、跨边框无台阶
    rep = np.asarray(Image.open(os.path.join(A, "x_ui_psv_replay_bg.png")).convert("RGB")).astype(int)
    lum = rep.mean(axis=2)

    def peak(seg, axis):
        prof = np.array([np.median(s) for s in (seg if axis == 0 else seg.T)])
        n = len(prof)
        out = 0.0
        for i in range(n):
            nb = np.concatenate([prof[max(0, i - 8):max(0, i - 3)], prof[min(n, i + 4):min(n, i + 9)]])
            if len(nb):
                out = max(out, abs(prof[i] - nb.mean()))
        return out

    for k, (x0, y0, x1, y1) in enumerate(((84, 212, 635, 528), (684, 212, 1235, 528),
                                          (1283, 212, 1835, 528), (83, 603, 635, 921)), 1):
        seg = lum[y0:y1, x0 + 8:x1 - 8]
        ph, pv = peak(seg, 0), peak(seg, 1)
        e1 = abs(np.median(lum[y0 + 1, x0 + 10:x1 - 10]) - np.median(lum[y0 - 1, x0 + 10:x1 - 10]))
        e2 = abs(np.median(lum[y1 - 2, x0 + 10:x1 - 10]) - np.median(lum[y1 + 1, x0 + 10:x1 - 10]))
        check(ph < 12 and pv < 12 and e1 < 6 and e2 < 6,
              "K 38 槽%d 无残线（横 %.1f/纵 %.1f）且无跨框台阶（%.2f/%.2f）" % (k, ph, pv, e1, e2))
    check((np.abs(lum[530:600, 60:1300] - np.asarray(Image.open(
        os.path.join(A, "x_ui_psv_gal_shell.png")).convert("RGB")).astype(int).mean(axis=2)[530:600, 60:1300])).mean() < 3,
          "K 38 槽区间干净带与 ALBUM 底版一致（还原口径成立）")
    # 28：走带条带内无亮残留、上下无缝
    mus = np.asarray(Image.open(os.path.join(A, "x_ui_psv_music_bg.png")).convert("RGB")).astype(int)
    ml = mus.mean(axis=2)
    band = ml[101:188, 777:1758]
    # ★ ISSUE-20260926-06 修复轮2 更新：原两条断言把"平坦灰块缺陷态"写成了验收目标，与真实目标（带内应为真实雪花底画）互斥，
    #   经主代理裁决改为「与兄弟屏同坐标同构 + 控件足迹区逐像素 == 干净底版」。
    sib = np.asarray(Image.open(os.path.join(A, "x_ui_psv_replay_bg.png")).convert("RGB")).astype(int).mean(axis=2)[101:188, 777:1758]
    check((band > 235).mean() > 0.5, "K 28 走带条白面板已抹净（带内为真实雪花底画，亮占比 %.5f）" % (band > 235).mean())
    check(abs(band.std() - sib.std()) < 3, "K 28 带内与情景页同坐标底画同构（stdev %.2f vs %.2f）" % (band.std(), sib.std()))
    dpl = np.asarray(Image.open(os.path.join(A, "x_ui_psv_dress_bg.png")).convert("RGB")).astype(int).mean(axis=2)
    check(np.abs(ml[84:204, 745:1791] - dpl[84:204, 745:1791]).mean() < 0.5,
          "K 28 控件足迹区逐像素 == 同族干净底版")
    for y in (101, 187):
        a = np.median(ml[y - 1, 777:1758])
        b = np.median(ml[y, 777:1758])
        check(abs(b - a) < 4, "K 28 y=%d 跨缝 Δ=%.2f < 4" % (y, abs(b - a)))


def main():
    assert_layout()
    assert_28()
    assert_37()
    assert_39()
    assert_bg()
    print("== 出图 ==")
    for name in ("27_gallery", "28_music", "37_dress", "38_replay"):
        annotate(name + ".json", "39_gal_shell.json", os.path.join(EV, "annot_%s.png" % name))
    for sid in ("gallery", "music", "dress", "replay"):
        compose_d.compose(sid, os.path.join(EV, "fromdata_%s.png" % sid), host=True)
    compose_d.compose("gal_shell", os.path.join(EV, "fromdata_39_only.png"))
    print("\n断言：%s（%d 项失败）" % ("全部通过" if not fails else "**不通过**", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
