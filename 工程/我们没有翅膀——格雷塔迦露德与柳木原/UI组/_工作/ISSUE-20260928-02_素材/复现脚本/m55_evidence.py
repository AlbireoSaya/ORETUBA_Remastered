# -*- coding: utf-8 -*-
r"""m55_evidence.py · ISSUE-20260928-02 C 组素材 · 证据生成（**只读资产目录**）

用途：对 `krkr\assets\ui\` 里 m55 产出的 **23 件**做**独立回读实测**并出可视证据，
供 reviewer / vision 复核。**不写任何资产、不改任何数据**（唯一写入目标是 `证据\`）。

产物（全部落 `_工作\ISSUE-20260928-02_素材\证据\`）
  · 逐件实测_回读.tsv      —— 从磁盘 PNG 回读的 尺寸 / mode / 字节 / α 极值 / 非透明占比 /
                              主色 / md5，并与生成器 `md5清单.tsv` **交叉比对**（不一致即非 0 退出）
  · 预览_白底_每件一行.png  —— **主证据**：白底，1:1，一件一行（供 vision 目视）
  · 预览_深底_每件一行.png  —— 深底对照（验「真 alpha、无白底/棋盘格烘焙」）
  · 放大6x_小控件.png       —— 18 件小控件 6× nearest 放大（验边缘 AA 与字形）
  · 放大6x_回放键三态.png   —— 回放键三态 4× nearest 放大
  · NEW_对照_冻结书版vs参照件形制.png —— 三版对照（**裁决用**）：① 我方规格件（#A50000 实心板 + 白字）
                               ② 自造对照件 build_new_alt_letters()（**自造，不是参照件**）
                               ③ 参照件 res12 原图（实测＝纯 #A50000 字形 + 透明底 + alpha 柔晕）

运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260928-02_素材\复现脚本\m55_evidence.py
"""
from __future__ import annotations

import hashlib
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "证据")

FONT = next((p for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
                         r"C:\Windows\Fonts\arial.ttf") if os.path.exists(p)), None)

# 表驱动的件名（**只列 m55 的 23 件**，不扫全目录 ⇒ 脚本与产出严格一一对应）
GROUPS = [
    ("必交 · NEW 角标", ["x_ui_new.png"]),
    ("必交 · 回放窗底板", ["x_ui_replay_panel.png"]),
    ("必交 · 场景回放键（3 态）", ["x_ui_pbkick_off.png", "x_ui_pbkick_over.png", "x_ui_pbkick_on.png"]),
    ("可选 · 缩放 −（3 态）", ["x_ui_zoomout_off.png", "x_ui_zoomout_over.png", "x_ui_zoomout_on.png"]),
    ("可选 · 缩放 ＋（3 态）", ["x_ui_zoomin_off.png", "x_ui_zoomin_over.png", "x_ui_zoomin_on.png"]),
    ("可选 · 横移 ◀（3 态）", ["x_ui_shift_lf_off.png", "x_ui_shift_lf_over.png", "x_ui_shift_lf_on.png"]),
    ("可选 · 横移 ▶（3 态）", ["x_ui_shift_rg_off.png", "x_ui_shift_rg_over.png", "x_ui_shift_rg_on.png"]),
    ("可选 · 纵滚 ▲（3 态）", ["x_ui_scroll_up_off.png", "x_ui_scroll_up_over.png", "x_ui_scroll_up_on.png"]),
    ("可选 · 纵滚 ▼（3 态）", ["x_ui_scroll_dn_off.png", "x_ui_scroll_dn_over.png", "x_ui_scroll_dn_on.png"]),
]
NAMES = [n for _g, ns in GROUPS for n in ns]


def font(sz):
    return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()


def readback(name):
    p = os.path.join(ASSETS, name)
    raw = open(p, "rb").read()
    with Image.open(p) as im:
        w, h, mode = im.size[0], im.size[1], im.mode
        im = im.convert("RGBA")
    arr = np.asarray(im).reshape(-1, 4)
    al = arr[:, 3]
    nz = arr[al > 16]
    cnt = Counter(map(tuple, nz[:, :3].tolist()))
    top, topn = (cnt.most_common(1)[0] if cnt else ((0, 0, 0), 0))
    return dict(name=name, w=w, h=h, mode=mode, bytes=len(raw),
                amin=int(al.min()), amax=int(al.max()),
                cov=round(100.0 * len(nz) / len(arr), 2),
                top="#%02X%02X%02X" % tuple(top), topn=int(topn),
                md5=hashlib.md5(raw).hexdigest(), img=im)


def sheet(rows_spec, bg, out, pad=10, title=None):
    """rows_spec = [(label, sub, im, meta)] —— **一件一行**（行高 = max(件高, 文字块) + pad）"""
    tsz, lsz, ssz = 20, 18, 15
    W = 660 + 470 + 2 * pad
    H = (36 if title else 0) + sum(max(im.height, 34) + pad for _l, _s, im, _m in rows_spec) + pad
    c = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(c)
    dark = bg[0] < 128
    fg = (222, 234, 250, 255) if dark else (26, 44, 70, 255)
    fg2 = (150, 172, 200, 255) if dark else (96, 116, 142, 255)
    y = 0
    if title:
        d.text((pad, 8), title, font=font(tsz), fill=fg)
        y = 36
    for label, sub, im, meta in rows_spec:
        rh = max(im.height, 34) + pad
        d.text((pad, y + rh // 2 - 22), label, font=font(lsz), fill=fg)
        d.text((pad, y + rh // 2 + 2), sub, font=font(ssz), fill=fg2)
        d.text((pad + 300, y + rh // 2 + 2), meta, font=font(ssz), fill=fg2)
        c.alpha_composite(im, (660, y + (rh - im.height) // 2))
        if not dark:
            d.line([(0, y + rh - 1), (W, y + rh - 1)], fill=(212, 222, 236, 255))
        else:
            d.line([(0, y + rh - 1), (W, y + rh - 1)], fill=(48, 56, 70, 255))
        y += rh
    c.convert("RGB").save(out)
    return out, c.size


def zoom_sheet(rows_spec, z, out, cols=1, bg=(255, 255, 255, 255)):
    tsz, lsz = 20, 18
    # 左栏宽度**按最长标签自适应**（基线 250）——裁决对照图的标签较长，固定 250 会与图重叠
    f = font(lsz)
    _probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lx = int(max(250, max((_probe.textlength(l, font=f) for l, _im in rows_spec), default=0) + 30))
    cell_w = max(im.width * z for _l, im in rows_spec) + 260 + (lx - 250)
    cell_h = sum(im.height * z + 16 for _l, im in rows_spec) + 40
    c = Image.new("RGBA", (cell_w, cell_h), bg)
    d = ImageDraw.Draw(c)
    d.text((10, 8), "nearest %d× 放大（左：件名；右：像素级边缘）" % z, font=font(tsz), fill=(30, 50, 80, 255))
    y = 40
    for label, im in rows_spec:
        big = im.resize((im.width * z, im.height * z), Image.NEAREST)
        d.text((10, y + big.height // 2 - lsz // 2), label, font=f, fill=(30, 50, 80, 255))
        c.alpha_composite(big, (lx, y))
        y += big.height + 16
    c.convert("RGB").save(out)
    return out, c.size


def main():
    os.makedirs(EVID, exist_ok=True)
    rows, imgs = [], {}
    for name in NAMES:
        r = readback(name)
        imgs[name] = r.pop("img")
        rows.append(r)

    # ── 与生成器的 md5 清单交叉比对 ────────────────────────────────
    gen = {}
    gp = os.path.join(EVID, "md5清单.tsv")
    if os.path.exists(gp):
        for line in open(gp, encoding="utf-8"):
            if line.startswith("#") or "\t" not in line:
                continue
            md5, n = line.rstrip("\n").split("\t", 1)
            gen[n] = md5
    bad = [(r["name"], r["md5"], gen.get(r["name"], "(缺)")) for r in rows
           if gen.get(r["name"]) != r["md5"]]

    # ── tsv ───────────────────────────────────────────────────────
    with open(os.path.join(EVID, "逐件实测_回读.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 独立回读：直接从 krkr\\assets\\ui\\ 的 PNG 读回（**不看生成器内存值**）\n")
        f.write("文件\t尺寸(w×h)\tmode\t字节\talpha_min\talpha_max\t非透明占比%\t主色\t主色像素数\tmd5\t与生成器md5一致\n")
        for r in rows:
            f.write("%s\t%d×%d\t%s\t%d\t%d\t%d\t%.2f\t%s\t%d\t%s\t%s\n"
                    % (r["name"], r["w"], r["h"], r["mode"], r["bytes"], r["amin"], r["amax"],
                       r["cov"], r["top"], r["topn"], r["md5"],
                       "是" if gen.get(r["name"]) == r["md5"] else "否"))

    # ── 预览图 ────────────────────────────────────────────────────
    # 行标签一律用**中日文与 ASCII**，不用 ◀▶▲▼（U+25C0 等在 msyh 下会渲染成豆腐块，实测踩到）
    ZH = {"x_ui_new.png": ("FIG-4-2 NEW 角标", "必交"),
          "x_ui_replay_panel.png": ("场景回放窗底板（FIG-5-3）", "必交"),
          "x_ui_pbkick_off.png": ("场景回放键 · off（常态：右三角）", "必交"),
          "x_ui_pbkick_over.png": ("场景回放键 · over（悬停：右三角）", "必交"),
          "x_ui_pbkick_on.png": ("场景回放键 · on（按下/播放中：方块）", "必交"),
          "x_ui_zoomout_off.png": ("缩放 「−」 · off", "可选"),
          "x_ui_zoomout_over.png": ("缩放 「−」 · over", "可选"),
          "x_ui_zoomout_on.png": ("缩放 「−」 · on（29×29，三态同尺寸）", "可选"),
          "x_ui_zoomin_off.png": ("缩放 「＋」 · off", "可选"),
          "x_ui_zoomin_over.png": ("缩放 「＋」 · over", "可选"),
          "x_ui_zoomin_on.png": ("缩放 「＋」 · on（29×29，三态同尺寸）", "可选"),
          "x_ui_shift_lf_off.png": ("横移 「左三角」 · off", "可选"),
          "x_ui_shift_lf_over.png": ("横移 「左三角」 · over", "可选"),
          "x_ui_shift_lf_on.png": ("横移 「左三角」 · on", "可选"),
          "x_ui_shift_rg_off.png": ("横移 「右三角」 · off", "可选"),
          "x_ui_shift_rg_over.png": ("横移 「右三角」 · over", "可选"),
          "x_ui_shift_rg_on.png": ("横移 「右三角」 · on", "可选"),
          "x_ui_scroll_up_off.png": ("纵滚 「上三角」 · off", "可选"),
          "x_ui_scroll_up_over.png": ("纵滚 「上三角」 · over", "可选"),
          "x_ui_scroll_up_on.png": ("纵滚 「上三角」 · on", "可选"),
          "x_ui_scroll_dn_off.png": ("纵滚 「下三角」 · off", "可选"),
          "x_ui_scroll_dn_over.png": ("纵滚 「下三角」 · over", "可选"),
          "x_ui_scroll_dn_on.png": ("纵滚 「下三角」 · on", "可选")}
    meta = {r["name"]: "%d×%d  %s  %d B  α[%d,%d]  %s" %
                      (r["w"], r["h"], r["mode"], r["bytes"], r["amin"], r["amax"], r["top"])
            for r in rows}
    rows_one = [(ZH[n][1], ZH[n][0], imgs[n], meta[n]) for n in NAMES]
    out = []
    out.append(sheet(rows_one, (255, 255, 255, 255),
                     os.path.join(EVID, "预览_白底_每件一行.png"),
                     title="ISSUE-20260928-02 C 组素材 · 白底 1:1 · 一件一行（23 件）"))
    out.append(sheet(rows_one, (20, 24, 32, 255),
                     os.path.join(EVID, "预览_深底_每件一行.png"),
                     title="ISSUE-20260928-02 C 组素材 · 深底 1:1（验真 alpha：无白底 / 棋盘格烘焙）"))
    small = [n for n in NAMES if n.startswith(("x_ui_zoom", "x_ui_shift", "x_ui_scroll"))]
    out.append(zoom_sheet([(n, imgs[n]) for n in small], 6,
                          os.path.join(EVID, "放大6x_小控件.png")))
    out.append(zoom_sheet([(n, imgs[n]) for n in
                           ("x_ui_pbkick_off.png", "x_ui_pbkick_over.png", "x_ui_pbkick_on.png")],
                          4, os.path.join(EVID, "放大4x_回放键三态.png")))

    # NEW 对照（规格件 vs 参照件形制）——现造参照形制版，只入证据
    sys.path.insert(0, HERE)
    import importlib.util
    sp = importlib.util.spec_from_file_location("m55", os.path.join(HERE, "m55_make_flow_assets.py"))
    m55 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m55)
    alt = m55.build_new_alt_letters(m55.FONT_CANDIDATES[0])
    ref = None
    rp = r"E:\ZCode Workspace\Galgame\工程\交汇协奏曲\解包\flowchart\pimg72\img\res12_blocks__fragment__NEW.png"
    if os.path.exists(rp):
        ref = Image.open(rp).convert("RGBA")
        if ref.size != (50, 17):
            ref = ref.resize((50, 17), Image.LANCZOS)
    cmp_rows = [("① 我方规格件（冻结书 §三：#A50000 实心板 + 白字 NEW，字号 18）", imgs["x_ui_new.png"]),
                ("② 自造对照件 build_new_alt_letters()（红字透明底 + 白描边）"
                 "—— **自造形制，不是参照件**", alt)]
    if ref is not None:
        cmp_rows.append(("③ 参照件 res12 原图（交汇协奏曲，仅供比对）"
                         "—— 实测：纯 #A50000 字形 + 透明底 + alpha 柔晕；无白描边 / 无实心底板 / 非满幅", ref))
    out.append(zoom_sheet(cmp_rows, 6, os.path.join(EVID, "NEW_对照_冻结书版vs参照件形制.png"), bg=(240, 244, 250, 255)))

    # ── 装配预览：回放窗底板 + 回放键三态（按冻结书 §1.1 的坐标关系摆放） ──
    # 回放窗 426×241 @1422,493 ｜ 回放键 119×119 @1576,555 ⇒ 键相对窗左上 = (+154, +62)
    PW, PH, GAP, KX, KY = 426, 241, 40, 154, 62
    asm = Image.new("RGBA", (GAP + 3 * PW + 2 * GAP + GAP, GAP + PH + GAP), (28, 34, 46, 255))
    for k, st in enumerate(("off", "over", "on")):
        px_ = GAP + k * (PW + GAP)
        asm.alpha_composite(imgs["x_ui_replay_panel.png"], (px_, GAP))
        asm.alpha_composite(imgs["x_ui_pbkick_%s.png" % st], (px_ + KX, GAP + KY))
    pth = os.path.join(EVID, "装配预览_回放窗+回放键三态.png")
    asm.convert("RGB").save(pth)
    out.append((pth, asm.size))

    # ── 引擎实机证据（若巡演产物在场；缺失则跳过并如实登记） ────────
    # 巡演运行目录 = `<krkr>\..\..\..\..\临时\ui_run`（见 `krkr\run_autotour.bat` 的 WTROOT 推导）
    #   ⇒ 从本脚本（<UI组>\_工作\...\复现脚本）算 = UI组/../.. /.. /临时/ui_run
    run_dir = os.path.abspath(os.path.join(UI_GROUP, "..", "..", "..", "临时", "ui_run",
                                           "runtime", "savedata"))
    shots = sorted(f for f in os.listdir(run_dir)
                   if f.endswith("_flowchart.png")) if os.path.isdir(run_dir) else []
    engine_note = "巡演产物不在场（%s）⇒ 跳过" % run_dir if not shots else ""
    if shots:
        shot = Image.open(os.path.join(run_dir, shots[0])).convert("RGBA")
        bgd = Image.new("RGBA", shot.size, (22, 26, 34, 255))
        bgd.alpha_composite(shot)
        c = bgd.crop((1400, 470, 1860, 730))
        c = c.resize((c.width * 2, c.height * 2), Image.NEAREST)
        pth = os.path.join(EVID, "引擎实机_%s_回放键区域2x.png"
                           % shots[0].replace("_flowchart.png", ""))
        c.convert("RGB").save(pth)
        out.append((pth, c.size))
        engine_note = "取自 %s" % shots[0]

    # ── 报告 ──────────────────────────────────────────────────────
    print("=" * 92)
    print("m55_evidence.py · C 组素材独立回读与证据（ISSUE-20260928-02）")
    print("-" * 92)
    print("%-30s %-9s %-5s %8s %4s %4s %7s %9s %s" %
          ("文件", "尺寸", "mode", "字节", "amin", "amax", "覆盖%", "主色", "md5一致"))
    for r in rows:
        print("%-30s %-9s %-5s %8d %4d %4d %7.2f %9s %s"
              % (r["name"], "%d×%d" % (r["w"], r["h"]), r["mode"], r["bytes"], r["amin"],
                 r["amax"], r["cov"], r["top"],
                 "是" if gen.get(r["name"]) == r["md5"] else "**否**"))
    print("-" * 92)
    tot = sum(r["bytes"] for r in rows)
    print("合计 %d 件 / %d 字节（%.2f KB）" % (len(rows), tot, tot / 1024.0))
    for p, sz in out:
        print("  证据 %s  (%d×%d)" % (os.path.basename(p), sz[0], sz[1]))
    print("-" * 92)
    print("非 RGBA 件：%d ｜ αmax≠255 件：%d ｜ αmin≠0 件：%d ｜ md5 与生成器不一致：%d"
          % (sum(1 for r in rows if r["mode"] != "RGBA"),
             sum(1 for r in rows if r["amax"] != 255),
             sum(1 for r in rows if r["amin"] != 0), len(bad)))
    for b in bad:
        print("  !! %s：回读 %s vs 生成器 %s" % b)
    ok = (not bad) and all(r["mode"] == "RGBA" and r["amax"] == 255 and r["amin"] == 0 for r in rows)
    print("结果：**%s**" % ("全部通过" if ok else "存在失败项"))
    print("=" * 92)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
