# -*- coding: utf-8 -*-
r"""assert_21_confirm_geometry.py —— 21 确认框：22 板「板 + 按钮/烘焙文字 + 热区」几何自证 + 接触印相表

Issue：`ISSUE-20260926-06` · **A 基础组修复轮**（本轮派单 ① 的「离线自证」要求）。
只读：仅读 `layout/screens/21_confirm.json` 与 `krkr/assets/ui/x_ui_psv_cfm_*.png`，**不改任何数据**。
产出：`_工作\ISSUE-20260926-06_A基础组修复\取证\sheet_21_confirm_22.png`（22 板接触印相表）。

■ 逐板断言（全部逐条打印 PASS/FAIL，任一条 FAIL ⇒ 退出码 1）
  A 板矩形 ⊂ 画布 1920×1080；且 22 板矩形**完全同一**（438,270,1044,540）⇒ 两型板板体同位、不跳位。
  B 素材尺寸 == 元素 w/h（1044×540），且与「板内安全区」（素材 α>128 包围盒映射到画布）相容。
  C 该板的**是/否可点带** ⊂ 板内安全区（各留 ≥2px 余量）：
      · 15 张含烘焙 YES/NO 的板 ⇒ 可点带 = 板内烘焙文字带（画布 853..923 / 972..1018 × 606..638）；
      · 7 张无 YES/NO 的板      ⇒ 可点带 = 我方按钮矩形（画布 788..928 / 942..1082 × 642..684）。
  D 热区覆盖：`cf.hit_yes ⊇ 各板的是可点带`、`cf.hit_no ⊇ 各板的否可点带`（22 板全 100% 覆盖）。
  E `vis_when` 集合：`cf_which` 取值集合 == 22 板号（严格相等、无重无缺）；按钮/文字件取值 ⊆ 该集合；
    热区 `vis_when == "*"`（有板在位才生效）。
  F 无重叠：两热区互不重叠（0 px）；任一 `cf_which` 取值下**可见板恰 1 张**（22 态逐一枚举）。
用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_A基础组修复\复现脚本\assert_21_confirm_geometry.py
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image, ImageDraw         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "21_confirm.json")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
EVID = os.path.join(UI, "_工作", "ISSUE-20260926-06_A基础组修复", "取证")

CANVAS = (1920, 1080)
BAKED_YESNO = {                          # 15 张板的板内烘焙 YES/NO（画布坐标，实测）
    "yes": (853, 606, 923, 638),
    "no": (972, 606, 1018, 638),
}
BTN = {"yes": (788, 642, 140, 42), "no": (942, 642, 140, 42)}
EXPECT_PANEL = (438, 270, 438 + 1044, 270 + 540)      # 画布坐标 (x0,y0,x1,y1)：438..1482 / 270..810


def rect(el):
    return (el["x"], el["y"], el["x"] + el["w"], el["y"] + el["h"])


def contains(outer, inner, margin=0):
    return (outer[0] + margin <= inner[0] and outer[1] + margin <= inner[1]
            and inner[2] <= outer[2] - margin and inner[3] <= outer[3] - margin)


def overlap_px(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def asset_path(asset):
    """元素里的 `ui/xxx.png` → 磁盘路径。"""
    return os.path.join(ASSETS, os.path.basename(asset))


def safe_area(asset):
    """素材内「板体」包围盒（α>128）→ 画布坐标。"""
    a = np.array(Image.open(asset_path(asset)).convert("RGBA"))[:, :, 3]
    ys, xs = np.nonzero(a > 128)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def main():
    d = json.load(io.open(SCREEN, encoding="utf-8"))
    els = {e["id"]: e for e in d["elements"]}
    hits = {k: rect(els["cf.hit_%s" % k]) for k in ("yes", "no")}
    panels = [e for e in d["elements"] if e["id"].startswith("cf.panel_")]
    ids = sorted(e["vis_when"] for e in panels)
    fails, lines = [], []

    def chk(ok, msg):
        lines.append(("  PASS  " if ok else "  FAIL  ") + msg)
        if not ok:
            fails.append(msg)

    # ── A 板矩形 ⊂ 画布 + 22 板矩形同一 ──
    rects = set()
    for e in panels:
        r = rect(e)
        rects.add(r)
        chk(contains((0, 0, CANVAS[0], CANVAS[1]), r) and r == EXPECT_PANEL,
            "A %s 矩形 %s == %s 且 ⊂ 画布" % (e["id"], r, EXPECT_PANEL))
    chk(len(rects) == 1, "A 22 板矩形完全同一（实测 %d 种）" % len(rects))

    # ── B/C/D 逐板 ──
    for e in panels:
        nn = e["vis_when"]
        pr = rect(e)
        w0, h0 = Image.open(asset_path(e["asset"])).size
        chk((w0, h0) == (e["w"], e["h"]), "B %s 素材 %dx%d == 元素 w/h %dx%d"
            % (e["id"], w0, h0, e["w"], e["h"]))
        bx = safe_area(e["asset"])
        sa = (pr[0] + bx[0], pr[1] + bx[1], pr[0] + bx[2], pr[1] + bx[3])
        baked = nn in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
                       "25", "43", "44")
        bands = {"yes": BAKED_YESNO["yes"] if baked else (BTN["yes"][0], BTN["yes"][1],
                                                          BTN["yes"][0] + BTN["yes"][2],
                                                          BTN["yes"][1] + BTN["yes"][3]),
                 "no": BAKED_YESNO["no"] if baked else (BTN["no"][0], BTN["no"][1],
                                                        BTN["no"][0] + BTN["no"][2],
                                                        BTN["no"][1] + BTN["no"][3])}
        for k in ("yes", "no"):
            chk(contains(sa, bands[k], 2),
                "C %s 的%s可点带 %s ⊂ 板内安全区 %s（留 2px）" % (e["id"], "是" if k == "yes" else "否",
                                                                bands[k], sa))
            chk(contains(hits[k], bands[k]),
                "D cf.hit_%s %s ⊇ %s 的%s可点带 %s（覆盖率 %.0f%%）"
                % (k, hits[k], e["id"], "是" if k == "yes" else "否", bands[k],
                   100.0 * overlap_px(hits[k], bands[k]) / float((bands[k][2] - bands[k][0]) *
                                                                 (bands[k][3] - bands[k][1]))))

    # ── E vis_when 集合 ──
    exp = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
           "20", "21", "22", "23", "24", "25", "42", "43", "44", "45"]
    chk(ids == sorted(exp), "E 板件 vis_when 集合 == 22 板号（实测 %d 个：%s）" % (len(ids), ",".join(ids)))
    flag_vals = set()
    for e in d["elements"]:
        if e.get("vis_flag") == "cf_which" and e.get("vis_when") != "*":
            flag_vals.add(str(e["vis_when"]))
    chk(flag_vals == set(exp),
        "E `cf_which` 取值集合 == 22 板号（实测 %d 个，无重无缺）" % len(flag_vals))
    btn = [e for e in d["elements"] if e["id"].startswith("cf.yes_b") or e["id"].startswith("cf.no_b")]
    chk(len(btn) == 14 and all(str(e["vis_when"]) in exp for e in btn),
        "E 我方按钮底 %d 件（7 板 × 2）且 vis_when ⊆ 22 板号" % len(btn))
    chk(all(els["cf.hit_%s" % k].get("vis_flag") == "cf_which"
            and els["cf.hit_%s" % k].get("vis_when") == "*" for k in ("yes", "no")),
        "E 两热区 vis_flag=cf_which / vis_when=\"*\"（有板在位才生效）")
    chk(all(e.get("visible_default") is True for e in d["elements"]),
        "E 全部元素 visible_default:true（§四铁律：靠 flag 控显隐不得写 false）")

    # ── F 无重叠 + 每态恰 1 板 ──
    chk(overlap_px(hits["yes"], hits["no"]) == 0,
        "F 两热区互不重叠（实测重叠 %d px，间隙 %d px）"
        % (overlap_px(hits["yes"], hits["no"]), hits["no"][0] - hits["yes"][2]))
    bad = []
    for v in exp:
        vis = [e["id"] for e in panels if str(e["vis_when"]) == v]
        if len(vis) != 1:
            bad.append("%s→%d 张" % (v, len(vis)))
    chk(not bad, "F 22 个 cf_which 取值下可见板**恰 1 张**（异常：%s）" % (", ".join(bad) or "无"))

    print("=" * 100)
    print("21 确认框 · 22 板几何自证（板 + 可点带 + 热区 + 可见性）")
    print("=" * 100)
    for x in lines:
        print(x)
    print("-" * 100)
    print("断言：%d 条，失败 %d 条 ⇒ %s" % (len(lines), len(fails), "**全部通过**" if not fails else "**不通过**"))

    # ── 接触印相表：22 板缩略 + 按钮/热区矩形叠加 ──
    Z = 0.20
    tw, th = int((EXPECT_PANEL[2] - EXPECT_PANEL[0]) * Z), int((EXPECT_PANEL[3] - EXPECT_PANEL[1]) * Z)
    cols, pad, label_h = 4, 10, 18
    rows = (len(exp) + cols - 1) // cols
    W = cols * tw + (cols + 1) * pad
    H = rows * (th + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (24, 24, 30))
    dr = ImageDraw.Draw(sheet)
    for i, nn in enumerate(exp):
        e = els["cf.panel_%s" % nn]
        im = Image.open(asset_path(e["asset"])).convert("RGBA").resize((tw, th), Image.LANCZOS)
        cx, cy = pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + label_h + pad)
        bg = Image.new("RGB", (tw, th), (18, 18, 24))
        bg.paste(im, (0, 0), im)
        d2 = ImageDraw.Draw(bg)

        def mk(r, color):
            x0 = (r[0] - EXPECT_PANEL[0]) * Z
            y0 = (r[1] - EXPECT_PANEL[1]) * Z
            return [x0, y0, x0 + (r[2] - r[0]) * Z, y0 + (r[3] - r[1]) * Z]

        baked = nn in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
                       "25", "43", "44")
        for k, col in (("yes", (0, 220, 60)), ("no", (0, 220, 60))):
            d2.rectangle(mk(hits[k], col), outline=(255, 60, 60))
            b = BAKED_YESNO[k] if baked else (BTN[k][0], BTN[k][1], BTN[k][0] + BTN[k][2],
                                              BTN[k][1] + BTN[k][3])
            d2.rectangle(mk(b, col), outline=col)
        sheet.paste(bg, (cx, cy))
        # 标签用 ASCII：PIL 默认位图字体无中日韩字形（写中文会渲染成方框）
        dr.text((cx, cy + th + 2), "P%s  %s" % (nn, "baked YES/NO + hit" if baked else "our btn + hit"),
                fill=(210, 210, 230))
    os.makedirs(EVID, exist_ok=True)
    out = os.path.join(EVID, "sheet_21_confirm_22.png")
    sheet.save(out)
    print("接触印相表：%s（%dx%d，红框 = 共用热区 cf.hit_yes/no，绿框 = 该板可点带）"
          % (out.replace(UI + os.sep, ""), W, H))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
