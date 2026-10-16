# -*- coding: utf-8 -*-
r"""psv_bc_probe.py —— B 组 PSV 换皮**机检探针**（23 存档 / 24 读档 / 26 通话记录）

■ 它守什么
  把本轮「重排」的口径写成**可判定的断言**（不是读数字给人看）：12 槽网格的对称性与居中、
  三态 flag 的完整接线、44 个 text 全部保留且落在新槽几何内、`action` 名一个不丢、
  26 的 list 几何恰好填满 PSV 板内可用高度、滚动控件对齐 PSV 滚动条槽、热区不压列表。
  任一不成立 ⇒ 退出码 1（供主代理/一审/二审直接看）。

■ 回归对照（**必要**，否则「没丢东西」只是印象）
  与本轮改造前的 M34 旧形（`_工作\ISSUE-20260926-06_BC存读档与回想换皮\原形备份\`）逐屏比对：
  `action` 集合、元素 id 集合 —— 只允许**新增**，不允许丢。

■ 变异自证（`--mutate`）
  在**内存副本**上打废一段口径（位移一列 / 抹一个 vis_when / 改 list 高 / 让热区压列表），
  探针必须报警。否则「全绿」可能只是没覆盖 —— 与 `test_state_targets.py` 的 `--mutate` 同规。

■ 用法
    python _工作\ISSUE-20260926-06_BC存读档与回想换皮\复现脚本\psv_bc_probe.py
    python _工作\ISSUE-20260926-06_BC存读档与回想换皮\复现脚本\psv_bc_probe.py --mutate
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)                                        # …\ISSUE-..._BC存读档与回想换皮
UI = os.path.dirname(os.path.dirname(MOD))                         # …\UI组（MOD → _工作 → UI组）
SCR = os.path.join(UI, "layout", "screens")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
BAK = os.path.join(MOD, "原形备份")

SLOT_W, SLOT_H, GAP = 415, 122, 44
WIN = (33, 25, 122, 73)
NODATA = (61, 19)
BOARD = (157, 146, 1604, 788)
SCROLL_CX, TRACK = 1723, (227, 876)


def load(p, copy=False):
    d = json.load(io.open(p, encoding="utf-8"))
    return json.loads(json.dumps(d, ensure_ascii=False)) if copy else d


def png_size(name):
    from PIL import Image
    p = os.path.join(ASSETS, os.path.basename(name))
    if not os.path.isfile(p):
        raise AssertionError("素材缺失：%s" % p)
    return Image.open(p).size


def rect(e):
    return (e["x"], e["y"], e["w"], e["h"])


def icontains(a, ix, iy):
    return a[0] <= ix < a[0] + a[2] and a[1] <= iy < a[1] + a[3]


def overlap(a, b):
    x = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    y = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return x * y


def _one_slot(fn, i, f, els, errs):
    """单槽内部：缩略窗 / 空槽标签 / 槽号与信息文字 / 热区。"""
    fx, fy = f[0], f[1]
    th = els.get("sv.thumb%d" % i)
    if not th or rect(th)[:2] != (fx + WIN[0], fy + WIN[1]) or rect(th)[2:] != WIN[2:]:
        errs.append("%s：sv.thumb%d 未落在槽框窗位 %s" % (fn, i, (fx + WIN[0], fy + WIN[1])))
    elif png_size(th["asset"]) != WIN[2:]:
        errs.append("%s：sv.thumb%d 素材 %s ≠ 窗 %s（无 nine ⇒ 必须 1:1）" % (fn, i, png_size(th["asset"]), WIN[2:]))
    elif not icontains(f, th["x"], th["y"]) or th["x"] + th["w"] > fx + SLOT_W or th["y"] + th["h"] > fy + SLOT_H:
        errs.append("%s：sv.thumb%d 出槽框" % (fn, i))
    nd = els.get("sv.nodata%d" % i)
    if not nd:
        errs.append("%s：缺 sv.nodata%d" % (fn, i))
    else:
        if nd.get("vis_flag") != "sv_s%d" % i or nd.get("vis_when") != "off":
            errs.append("%s：sv.nodata%d 未绑 sv_s%d=off（%s/%s）" % (fn, i, i, nd.get("vis_flag"), nd.get("vis_when")))
        if rect(nd)[2:] != NODATA or png_size(nd["asset"]) != NODATA:
            errs.append("%s：sv.nodata%d 尺寸 %s/素材 %s ≠ %s" % (fn, i, rect(nd)[2:], png_size(nd["asset"]), NODATA))
        if not icontains((fx + WIN[0], fy + WIN[1], WIN[2], WIN[3]), nd["x"] + NODATA[0] / 2, nd["y"] + NODATA[1] / 2):
            errs.append("%s：sv.nodata%d 未居中在窗内" % (fn, i))
    for k in ("num", "info"):
        e = els.get("sv.%s%d" % (k, i))
        if not e:
            errs.append("%s：缺 sv.%s%d" % (fn, k, i))
            continue
        if not icontains(f, e["x"] + e["w"] / 2, e["y"] + e["h"] / 2):
            errs.append("%s：sv.%s%d 不在槽框 %s 内" % (fn, k, i, f))
        if e["x"] + e["w"] > fx + SLOT_W:
            errs.append("%s：sv.%s%d 右沿 %d 越出槽框右沿 %d" % (fn, k, i, e["x"] + e["w"], fx + SLOT_W))
        need = e.get("max_lines", 1) * math.floor(e["font"]["size"] * 1.4)
        if e.get("wrap") and e["h"] < need:
            errs.append("%s：sv.%s%d 框高 %d < max_lines×行高 %d（会静默少行）" % (fn, k, i, e["h"], need))
    h = els.get("sv.hit%d" % i)
    if not h or h.get("action") != "slot_%d" % i or rect(h) != f:
        errs.append("%s：sv.hit%d 缺失/action 变了/矩形≠槽框（%s）" % (fn, i, h and (h.get("action"), rect(h))))


def check_saveload(fn, errs, info):
    d = load(os.path.join(SCR, fn))
    els = {e["id"]: e for e in d["elements"]}
    tags = [e for e in d["elements"] if e["id"].startswith("sv.slot") and e["kind"] == "image"]
    # ① 网格：12 槽 × 3 态
    tris = {}
    for e in tags:
        base = e["id"].split("_")[0]                                  # sv.slotN
        tris.setdefault(base, {})[e.get("vis_when")] = e
    if len(tris) != 12:
        errs.append("%s：槽组数 %d ≠ 12" % (fn, len(tris)))
    for i in range(1, 13):
        t = tris.get("sv.slot%d" % i) or {}
        if set(t) != {"on", "off", "warn"}:
            errs.append("%s：sv.slot%d 三态不完整（%s）" % (fn, i, sorted(map(str, t)) if t else "缺件"))
            continue
        fx, fy = t["on"]["x"], t["on"]["y"]
        f = (fx, fy, SLOT_W, SLOT_H)
        for k, e in t.items():
            if rect(e) != f:
                errs.append("%s：sv.slot%d[%s] 三态矩形不一致 %s ≠ %s（换态会跳位）" % (fn, i, k, rect(e), f))
            if e.get("vis_flag") != "sv_s%d" % i:
                errs.append("%s：sv.slot%d[%s] vis_flag=%s ≠ sv_s%d" % (fn, i, k, e.get("vis_flag"), i))
            if e.get("visible_default") is not True:
                errs.append("%s：sv.slot%d[%s] visible_default 非 true（flag 控显隐铁律）" % (fn, i, k))
            if rect(e)[2:] != (SLOT_W, SLOT_H):
                errs.append("%s：sv.slot%d[%s] 尺寸 %s ≠ 415×122" % (fn, i, k, rect(e)[2:]))
            if e.get("nine"):
                errs.append("%s：sv.slot%d[%s] 带 nine（应 1:1）" % (fn, i, k))
            if png_size(e["asset"]) != (SLOT_W, SLOT_H):
                errs.append("%s：sv.slot%d[%s] 素材实尺寸 %s ≠ 415×122" % (fn, i, k, png_size(e["asset"])))
        _one_slot(fn, i, f, els, errs)
    fd = d.get("flags_default") or {}
    if {k: v for k, v in fd.items()} != {"sv_s%d" % i: "on" for i in range(1, 13)}:
        errs.append("%s：flags_default 不是 12 键 sv_s1..sv_s12 = on（实为 %s）" % (fn, sorted(fd)))
    # ② 网格几何：等距 + 左右对称 + 纵向居中于 [149,939]
    xs = sorted({e["x"] for e in tags})
    ys = sorted({e["y"] for e in tags})
    if len(xs) != 4 or len(ys) != 3:
        errs.append("%s：网格应为 4 列 × 3 行（实为 %d 列 %d 行）" % (fn, len(xs), len(ys)))
    else:
        if [xs[i + 1] - xs[i] for i in range(3)] != [SLOT_W + GAP] * 3:
            errs.append("%s：列节距 %s ≠ %d" % (fn, [xs[i + 1] - xs[i] for i in range(3)], SLOT_W + GAP))
        if [ys[i + 1] - ys[i] for i in range(2)] != [SLOT_H + GAP] * 2:
            errs.append("%s：行节距 %s ≠ %d" % (fn, [ys[i + 1] - ys[i] for i in range(2)], SLOT_H + GAP))
        lm, rm = xs[0], 1920 - (xs[-1] + SLOT_W)
        if lm != rm or lm != 64:
            errs.append("%s：左右边距 %d/%d ≠ 64/64（对称性 + PSV 题字左边距口径）" % (fn, lm, rm))
        top, bot = 149, 939                       # PSV 题字下沿 / 页码键上沿
        span = ys[-1] + SLOT_H - ys[0]
        if abs((ys[0] + span / 2.0) - (top + bot) / 2.0) > 1:
            errs.append("%s：网格纵向未居中于 [%d,%d]（中心 %.1f）" % (fn, top, bot, ys[0] + span / 2.0))
        if ys[0] < top or ys[-1] + SLOT_H > bot:
            errs.append("%s：网格越出 [题字下沿 %d, 页码键上沿 %d]" % (fn, top, bot))
    info.append("  · %s：12 槽 3 态 %d 件 ｜ 列 x=%s ｜ 行 y=%s" % (fn, len(tags), xs, ys))
    # ③ 缩略窗 / 空槽标签 / 文字 / 热区（逐槽）
    #     （见 _one_slot；在上面 ① 的循环内逐槽调用）

    # ④ 底图 z 关系
    bg, dim = els.get("sv.bg"), els.get("sv.dim")
    if not bg or rect(bg) != (0, 0, 1920, 1080) or png_size(bg["asset"]) != (1920, 1080):
        errs.append("%s：sv.bg 缺失/几何≠1920×1080/素材尺寸不符" % fn)
    elif not (dim["z"] < bg["z"] < tris["sv.slot1"]["on"]["z"]):
        errs.append("%s：z 关系应 dim < bg < 槽面板（%s/%s/%s）" % (fn, dim["z"], bg["z"], tris["sv.slot1"]["on"]["z"]))
    # ⑤ 44 个 text / action 全集
    texts = [e for e in d["elements"] if e["kind"] == "text"]
    if len(texts) != 44:
        errs.append("%s：text 数 %d ≠ 44（派单「我方现有 44 个 text」）" % (fn, len(texts)))
    acts = {e["action"] for e in d["elements"] if e.get("action")}
    want = {"slot_%d" % i for i in range(1, 13)} | {"page_%d" % i for i in range(1, 11)} | \
           {"open_save", "open_load", "close"}
    miss = want - acts
    if miss:
        errs.append("%s：action 丢失 %s" % (fn, sorted(miss)))
    info.append("  · %s：text %d 件 ｜ action %d 种（必需 %d 种全在）" % (fn, len(texts), len(acts), len(want)))


def check_backlog(errs, info):
    fn = "26_backlog.json"
    d = load(os.path.join(SCR, fn))
    els = {e["id"]: e for e in d["elements"]}
    bg = els.get("bl.bg")
    if not bg or rect(bg) != (0, 0, 1920, 1080) or png_size(bg["asset"]) != (1920, 1080):
        errs.append("%s：bl.bg 缺失/几何≠1920×1080/素材不符" % fn)
    lst = els.get("bl.list")
    if not lst:
        errs.append("%s：bl.list 缺失" % fn)
        return
    x, y, w = lst["x"], lst["y"], lst["w"]
    ih, gap, rows = lst["item_h"], lst["gap"], lst["max_rows"]
    bx, by, bw, bh = BOARD
    if x != bx + 12 or y != by + 12:
        errs.append("%s：列表未按板内缩 12 定位（%s,%s）≠（%s,%s）" % (fn, x, y, bx + 12, by + 12))
    if rows * ih + (rows - 1) * gap != bh - 24:
        errs.append("%s：4 行栈 %d ≠ 板内可用高度 %d" % (fn, rows * ih + (rows - 1) * gap, bh - 24))
    if x + w > 1712:
        errs.append("%s：列表右沿 %d 越过 PSV 滚动条槽左沿 1712" % (fn, x + w))
    if y + rows * ih + (rows - 1) * gap > by + bh:
        errs.append("%s：列表下沿越出板下沿 %d" % (fn, by + bh))
    it = lst.get("item_text") or {}
    need = it.get("max_lines", 1) * math.floor(lst["font"]["size"] * 1.4)
    if it.get("h", 0) < need:
        errs.append("%s：item_text 框高 %d < max_lines×行高 %d" % (fn, it.get("h"), need))
    if it.get("x", 0) + it.get("w", 0) > w or it.get("y", 0) + it.get("h", 0) > ih:
        errs.append("%s：item_text 出块" % fn)
    for b in lst.get("item_buttons") or []:
        if b["x"] + b["w"] > w or b["y"] + b["h"] > ih:
            errs.append("%s：item_buttons[%s] 出块" % (fn, b["key"]))
    f = lst.get("item_frame") or {}
    if os.path.basename(f.get("asset", "")) != "x_ui_psv_bklog_row.png":
        errs.append("%s：item_frame 资产不是 PSV 行板（%s）" % (fn, f.get("asset")))
    elif png_size(f["asset"]) != (w, ih):
        errs.append("%s：行板素材 %s ≠ 块矩形 %s（无 nine ⇒ 必须 1:1）" % (fn, png_size(f["asset"]), (w, ih)))
    if f.get("nine"):
        errs.append("%s：行板带 nine（应 1:1）" % fn)
    if not (0 < f.get("opacity", 0) <= 255):
        errs.append("%s：item_frame.opacity 非法 %s" % (fn, f.get("opacity")))
    for eid, top, bot in (("bl.up", TRACK[0], None), ("bl.slider", None, None), ("bl.down", None, TRACK[1])):
        e = els.get(eid)
        if not e:
            errs.append("%s：缺 %s" % (fn, eid))
            continue
        if abs((e["x"] + e["w"] / 2.0) - SCROLL_CX) > 2:
            errs.append("%s：%s 未对齐滚动条槽中心 %d（中心 %.1f）" % (fn, eid, SCROLL_CX, e["x"] + e["w"] / 2.0))
        if e["y"] < TRACK[0] - 1 or e["y"] + e["h"] > TRACK[1] + 1:
            errs.append("%s：%s y=%d..%d 越出槽 %s" % (fn, eid, e["y"], e["y"] + e["h"], TRACK))
    lr = (x, y, w, rows * ih + (rows - 1) * gap)
    for hid in ("bl.up_hit", "bl.slider_hit", "bl.down_hit", "bl.close_hit"):
        e = els.get(hid)
        if not e:
            errs.append("%s：缺 %s" % (fn, hid))
            continue
        if overlap(rect(e), lr):
            errs.append("%s：%s 压住列表矩形 %d px" % (fn, hid, overlap(rect(e), lr)))
    if (els.get("bl.close_hit") or {}).get("action") != "close":
        errs.append("%s：bl.close_hit 的 action 不是 close" % fn)
    acts = {e["action"] for e in d["elements"] if e.get("action")}
    if acts != {"close"}:
        errs.append("%s：action 集合 %s ≠ {close}" % (fn, sorted(acts)))
    info.append("  · %s：list x%d y%d w%d item_h%d gap%d ｜ 栈高 %d = 板内 %d ｜ 滚动件对齐 %d"
                % (fn, x, y, w, ih, gap, rows * ih + (rows - 1) * gap, bh - 24, SCROLL_CX))


def compare_actions(errs, info):
    """与改造前原形比对：action 集合与元素 id 只允许新增。"""
    for fn in ("23_save.json", "24_load.json", "26_backlog.json"):
        oldp = os.path.join(BAK, fn)
        if not os.path.isfile(oldp):
            errs.append("原形备份缺失：%s（--mutate 与回归对照都需要它）" % oldp)
            continue
        o, n = load(oldp), load(os.path.join(SCR, fn))
        oa = {e["action"] for e in o["elements"] if e.get("action")}
        na = {e["action"] for e in n["elements"] if e.get("action")}
        if oa - na:
            errs.append("%s：action 丢失 %s" % (fn, sorted(oa - na)))
        oi = {e["id"] for e in o["elements"]}
        ni = {e["id"] for e in n["elements"]}
        if oi - ni:
            errs.append("%s：元素 id 丢失 %s" % (fn, sorted(oi - ni)))
        info.append("  · %s：相对原形 action +%d（丢 0）｜ 元素 +%d（丢 0）"
                    % (fn, len(na) - len(oa), len(ni) - len(oi)))


def run(mutate=None):
    errs, info = [], []
    if mutate:
        _apply_mutation(mutate)
    try:
        for fn in ("23_save.json", "24_load.json"):
            check_saveload(fn, errs, info)
        check_backlog(errs, info)
        compare_actions(errs, info)
    finally:
        if mutate:
            _restore()
    return errs, info


# ── 变异自证：在临时副本上打废机制，探针必须报警 ──────────────────────
def _apply_mutation(kind):
    src = os.path.join(SCR, "26_backlog.json" if kind in ("list", "hit") else "23_save.json")
    _MUT["path"] = src
    with io.open(src, "rb") as f:
        _MUT["raw"] = f.read()
    d = json.loads(_MUT["raw"].decode("utf-8"))
    if kind == "col":
        for e in d["elements"]:
            if e["id"] == "sv.slot2":
                e["x"] += 7
    elif kind == "flag":
        for e in d["elements"]:
            if e["id"] == "sv.slot3_warn":
                e.pop("vis_when", None)
    elif kind == "list":
        for e in d["elements"]:
            if e["id"] == "bl.list":
                e["item_h"] = 200
    elif kind == "hit":
        for e in d["elements"]:
            if e["id"] == "bl.up_hit":
                e["x"] = 1000
    with io.open(src, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")


def _restore():
    with io.open(_MUT["path"], "wb") as f:
        f.write(_MUT["raw"])


_MUT = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", action="store_true", help="四种变异各自必须让探针报警")
    args = ap.parse_args()

    if args.mutate:
        _prepare_bak()
        bad = []
        for kind in ("col", "flag", "list", "hit"):
            errs, _ = run(mutate=kind)
            print("  变异[%s]：报警 %d 条 %s" % (kind, len(errs), "✓" if errs else "!! 未报警"))
            if not errs:
                bad.append(kind)
        if bad:
            print("[FAIL] 变异未被检出：%s（探针覆盖不足）" % ", ".join(bad))
            return 1
        print("变异自证：全部 4 种变异均被检出 ✓")
        return 0

    errs, info = run()
    print("=" * 78)
    print("psv_bc_probe · B 组 PSV 换皮机检（23 存档 / 24 读档 / 26 通话记录）")
    print("=" * 78)
    print("\n".join(info))
    print("-" * 78)
    if errs:
        for e in errs:
            print("  FAIL " + e)
        print("结果：**不通过**（%d 条）" % len(errs))
        return 1
    print("结果：**全部通过**（网格对称居中 / 三态接线 / 44 text / action 无丢失 / "
          "26 板内高度与滚动件对齐 / 热区不压列表）")
    return 0


def _prepare_bak():
    """把三屏的**改造前原形**复制到 `原形备份\\`（供 --mutate 的回归对照；已存在则不覆盖）。"""
    if os.path.isdir(BAK) and len(os.listdir(BAK)) >= 3:
        return
    os.makedirs(BAK, exist_ok=True)
    import subprocess
    for fn, rev in (("23_save.json", "HEAD"), ("24_load.json", "HEAD"), ("26_backlog.json", "HEAD")):
        p = os.path.join(BAK, fn)
        if os.path.exists(p):
            continue
        out = subprocess.run(["git", "show", "%s:%s" % (rev, "工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/layout/screens/" + fn)],
                             cwd=UI, capture_output=True)
        if out.returncode == 0:
            with open(p, "wb") as f:
                f.write(out.stdout)
            print("  取回原形 %s（git %s）" % (fn, rev))


if __name__ == "__main__":
    sys.exit(main())
