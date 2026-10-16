# -*- coding: utf-8 -*-
r"""m55_round2_evidence.py · ISSUE-20260928-02 素材**迭代轮**（第 2 轮）改前/改后对照证据

用途：为第 2 轮的 4 处裁决改动出**可复核**的对照证据（新值 vs 第 1 轮的旧值）。
**只读文件：写盘目标仅 `证据\`；不改任何资产、不改任何数据。**
（本脚本**不落盘任何 `krkr\assets\ui\` 件**；改前值一律用旧参数在**内存里重造**，不动磁盘。）

第 2 轮 4 处改动（主代理裁决）
  1. NEW 角标字形放大：字号搜索判据 44×11 → **48×15**（`build_new()`）
  2. 文档订正：参照件 res12 实测＝「纯 #A50000 字形 + 透明底 + alpha 柔晕」，**非满幅 / 无白描边 / 无实心底板**
  3. 缩放 −/＋ 按下态 41×41 → **29×29**（`PLATE_CASES`；元素矩形即 29×29）
  4. 小控件外发光加强：`PLATE_INSET 2.5→3.0`、`PLATE_GLOW_SIGMA 1.0→1.6`、
     `gain off/over/on 0.06/0.20/0.28 → 0.24/0.32/0.40`（★ off 由裁决值 0.18 上调到 0.24，理由见报告）

产物（全部落 `_工作\ISSUE-20260928-02_素材\证据\`）
  · 改前改后_小控件与缩放按下态.tsv          —— 逐件 改前/改后 尺寸 / 字节 / 剪前帧 / 剪后帧 / x=1 外发光
  · 对照_小控件外发光_改前vs改后.png         —— zoomout/shift_lf/scroll_up 三族 off/over/on，6× nearest
  · 对照_zoom_on_41x41降采vs29x29.png       —— 按下态「41×41 被 0.71× 重采样」发虚 vs 29×29 原生
  · 变异自证_3 条.txt                        —— 3 条变异实跑，证明断言非空转

运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260928-02_素材\复现脚本\m55_round2_evidence.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "证据")

# 第 1 轮（改前）的小方板外发光参数 —— 硬编码在此，作为对照基准
OLD = dict(inset=2.5, sigma=1.0, gains={"off": 0.06, "over": 0.20, "on": 0.28})
# 第 2 轮之前 zoom 按下态的件尺寸（元素矩形是 29×29）
OLD_ZOOM_ON_SIZE = (41, 41)


def load_m55():
    sp = importlib.util.spec_from_file_location(
        "m55", os.path.join(HERE, "m55_make_flow_assets.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def set_params(m, inset, sigma, gains):
    m.PLATE_INSET = inset
    m.PLATE_GLOW_SIGMA = sigma
    for st, g in gains.items():
        m.PLATE_STYLE[st]["gain"] = g


def png_len(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return len(b.getvalue())


def col_profile(im, n=6):
    """中列/中行方向的最外 n 列 α（取行中点，避开圆角）"""
    a = np.asarray(im.getchannel("A"))
    h = a.shape[0] // 2
    return [int(v) for v in a[h, :n]]


def semi_edge_count(im, band=2):
    """最外 `band` px 框内 **0 < α < 250** 的像素数（半透明「发虚」的量化指标）"""
    a = np.asarray(im.getchannel("A"))
    mask = np.zeros(a.shape, bool)
    mask[:band, :] = mask[-band:, :] = True
    mask[:, :band] = mask[:, -band:] = True
    return int(((a > 0) & (a < 250) & mask).sum())


def ring_start(im):
    """中行上首个 α≥128 的列号（板/环外沿落点）——重采样会让它与同键其它态错开"""
    a = np.asarray(im.getchannel("A"))
    r = a[a.shape[0] // 2]
    return next((i for i, v in enumerate(r) if v >= 128), -1)


def midrow(im, n=8):
    a = np.asarray(im.getchannel("A"))
    return [int(v) for v in a[a.shape[0] // 2, :n]]


def main():
    m = load_m55()
    fp = m.FONT_CANDIDATES[0]
    os.makedirs(EVID, exist_ok=True)

    # ── ① 逐件 改前 / 改后 表（小控件族 + 缩放按下态） ─────────────────────
    # 第 2 轮（改后）的 gain 一律取**模块现值**（m55 里写死的 0.24/0.32/0.40）
    NEW_GAINS = {st: m.PLATE_STYLE[st]["gain"] for st in ("off", "over", "on")}
    rows, glow_pair = [], []
    for nm, gl, _zo, _zv, zn in m.PLATE_CASES:
        for st, z in (("off", _zo), ("over", _zv), ("on", zn)):
            # 改前：同一元素尺寸、旧发光参数（zoom 按下态另按 41×41 造，见下）
            set_params(m, OLD["inset"], OLD["sigma"], OLD["gains"])
            old = m.build_plate_button(z[0], z[1], gl, st)
            old_raw = m.frame_max(m.build_unclipped(
                lambda: m.build_plate_button(z[0], z[1], gl, st)), 1)
            set_params(m, 3.0, 1.6, NEW_GAINS)
            new = m.build_plate_button(z[0], z[1], gl, st)
            new_raw = m.frame_max(m.build_unclipped(
                lambda: m.build_plate_button(z[0], z[1], gl, st)), 1)
            b = lambda im: int(max(np.asarray(im.getchannel("A"))[:1, :].max(),
                                   np.asarray(im.getchannel("A"))[-1:, :].max(),
                                   np.asarray(im.getchannel("A"))[:, :1].max(),
                                   np.asarray(im.getchannel("A"))[:, -1:].max()))
            rows.append(dict(name="x_ui_%s_%s.png" % (nm, st), size="%d×%d" % z,
                             before_size="%d×%d" % z, after_size="%d×%d" % z,
                             before_bytes=png_len(old), after_bytes=png_len(new),
                             before_raw=old_raw, after_raw=new_raw,
                             before_cut=b(old), after_cut=b(new),
                             before_x1=col_profile(old)[1], after_x1=col_profile(new)[1],
                             before_x2=col_profile(old)[2], after_x2=col_profile(new)[2]))
        if nm in ("zoomout", "shift_lf", "scroll_up"):
            glow_pair.append((nm, gl, _zo))

    # 缩放按下态：改前实为 41×41（元素 29×29 ⇒ 引擎 0.71× 重采样）
    set_params(m, OLD["inset"], OLD["sigma"], OLD["gains"])
    old_on41 = m.build_plate_button(OLD_ZOOM_ON_SIZE[0], OLD_ZOOM_ON_SIZE[1], "minus", "on")
    set_params(m, 3.0, 1.6, NEW_GAINS)
    new_on29 = m.build_plate_button(29, 29, "minus", "on")
    resamp = old_on41.resize((29, 29), Image.LANCZOS)      # 模拟引擎 0.71× 重采样

    with open(os.path.join(EVID, "改前改后_小控件与缩放按下态.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("# 改前＝第 1 轮参数（inset2.5/σ1.0/gain .06 .20 .28）**内存重造**；"
                "改后＝第 2 轮参数（inset3.0/σ1.6/gain .24 .32 .40）\n")
        f.write("# 「最外 1px 帧 α」剪前＝临时关闭 clip_low_alpha 量；剪后＝成品量（不变量要求 ==0）\n")
        f.write("文件\t尺寸\t改前字节\t改后字节\t净增字节\t改前剪前帧\t改后剪前帧\t"
                "改前剪后帧\t改后剪后帧\t改前x=1\t改后x=1\t改前x=2\t改后x=2\n")
        for r in rows:
            f.write("%s\t%s\t%d\t%d\t%+d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" % (
                r["name"], r["size"], r["before_bytes"], r["after_bytes"],
                r["after_bytes"] - r["before_bytes"], r["before_raw"], r["after_raw"],
                r["before_cut"], r["after_cut"], r["before_x1"], r["after_x1"],
                r["before_x2"], r["after_x2"]))

    # ── ② 小控件外发光 改前/改后 目视对照（6× nearest） ───────────────────
    def zoom(im, z=6):
        return im.resize((im.width * z, im.height * z), Image.NEAREST)

    def stack(items, title, bg=(246, 249, 254, 255)):
        f = ImageFont.truetype(fp, 17)
        probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        lx = int(max(300, max((probe.textlength(l, font=f) for l, _im in items),
                              default=0) + 30))
        W = max(lx + max(im.width for _l, im in items) + 20,
                int(probe.textlength(title, font=f)) + 24)
        H = 40 + sum(max(im.height, 26) + 14 for _l, im in items) + 10
        c = Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(c)
        d.text((10, 8), title, font=f, fill=(24, 44, 72, 255))
        y = 40
        for lab, im in items:
            d.text((10, y + im.height // 2 - 9), lab, font=f, fill=(24, 44, 72, 255))
            c.alpha_composite(im, (lx, y))
            y += im.height + 14
        return c.convert("RGB")

    items = []
    for nm, gl, z in glow_pair:
        for st in ("off", "over", "on"):
            set_params(m, OLD["inset"], OLD["sigma"], OLD["gains"])
            o = zoom(m.build_plate_button(z[0], z[1], gl, st))
            set_params(m, 3.0, 1.6, {s: m.PLATE_STYLE[s]["gain"] for s in ("off", "over", "on")})
            n = m.build_plate_button(z[0], z[1], gl, st)
            items.append(("%s %s 改前" % (nm, st), o))
            items.append(("%s %s 改后" % (nm, st), zoom(n)))
    stack(items, "小控件外发光 改前(inset2.5 σ1.0 gain .06/.20/.28) vs "
                 "改后(inset3.0 σ1.6 gain .24/.32/.40) · 6× nearest").save(
        os.path.join(EVID, "对照_小控件外发光_改前vs改后.png"))

    # ── ③ 缩放按下态 41×41（0.71× 重采样）vs 29×29 原生 ──────────────────
    z6 = lambda im: im.resize((im.width * 6, im.height * 6), Image.NEAREST)
    stack([("改前：41×41 原件（41 尺度，不与 29 直比）", z6(old_on41)),
           ("改前：41×41 → 29×29 LANCZOS（＝引擎 0.71× 重采样 ⇒ 发虚）", z6(resamp)),
           ("改后：29×29 原生（零重采样）", z6(new_on29))],
          "缩放按下态 zoomout_on：41×41 重采样 vs 29×29 原生 · 6× nearest ｜ "
          "外沿 2px 带半透明像素（0<α<250，29 尺度）：重采样 %d ｜ 原生 %d（%.2f×）｜ "
          "板/环外沿起点 x：重采样 %d ｜ 原生 %d"
          % (semi_edge_count(resamp), semi_edge_count(new_on29),
             semi_edge_count(resamp) / max(1.0, semi_edge_count(new_on29)),
             ring_start(resamp), ring_start(new_on29))
          ).save(os.path.join(EVID, "对照_zoom_on_41x41降采vs29x29.png"))

    # ── ④ NEW 角标：改后字形墨迹与板内边距 ──────────────────────────────
    new_img, meta = m.build_new(fp)
    na = np.asarray(new_img)
    ys, xs = np.nonzero((na[:, :, 3] > 140) & (na[:, :, 0] > 235)
                        & (na[:, :, 1] > 235) & (na[:, :, 2] > 235))
    ink = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    pads = (ink[0], 50 - 1 - ink[2], ink[1], 17 - 1 - ink[3])
    a = np.asarray(new_img.getchannel("A"))
    corners = [int(a[0, 0]), int(a[0, -1]), int(a[-1, 0]), int(a[-1, -1])]
    mid = 17 // 2
    sides = [int(a[0, mid]), int(a[-1, mid])]

    # ── ⑤ 变异自证：3 条断言是否真的会失败（全部 write=False，不写盘） ────
    muts = []

    class Capture:
        def __init__(self):
            self.buf = []
        def write(self, s):
            self.buf.append(s)
        def flush(self):
            pass

    def run_mut(label, prep, restore):
        cap = Capture()
        set_params(m, 3.0, 1.6, NEW_GAINS)
        prep()
        with contextlib.redirect_stdout(cap):
            rc = m.run(write=False)
        restore()
        txt = "".join(cap.buf)
        fails = [ln.strip() for ln in txt.splitlines() if ln.strip().startswith("!!")]
        muts.append((label, rc, fails[:4]))

    base_gains = dict(NEW_GAINS)
    run_mut("M1 剪前帧：off gain → 1.0（发光尾冲穿画布）",
            lambda: set_params(m, 3.0, 1.6, {"off": 1.0, "over": 0.32, "on": 0.40}),
            lambda: set_params(m, 3.0, 1.6, base_gains))
    run_mut("M2 剪后帧不变量：PLATE_INSET → 0.5（板面/发光触到画布边缘）",
            lambda: set_params(m, 0.5, 1.6, base_gains),
            lambda: set_params(m, 3.0, 1.6, base_gains))

    # M3：corners 类——NEW 盘面不再满铺（左右边中点 <250）
    _orig_rr = m.rr_mask

    def _small_plate(size, box, radius, scale=4):
        if size == (50, 17) and box == (0, 0, 50, 17):
            return _orig_rr(size, (4, 4, 46, 13), radius, scale)
        return _orig_rr(size, box, radius, scale)

    def prep3():
        m.rr_mask = _small_plate

    def rest3():
        m.rr_mask = _orig_rr
    run_mut("M3 corners 类：NEW 盘面改小（左右边中点 <250）", prep3, rest3)

    with open(os.path.join(EVID, "变异自证_3条.txt"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("# 变异自证：把参数/掩膜搅坏，确认断言**真的会失败**（非空转）；"
                "全部 write=False，不写任何资产。期望每条 rc=1。\n")
        for lab, rc, fails in muts:
            f.write("\n[%s] %s → rc=%d\n"
                    % ("符合预期" if rc == 1 else "!! 未失败", lab, rc))
            for x in fails:
                f.write("    %s\n" % x)

    # ── 报告 ────────────────────────────────────────────────────────────
    print("=" * 96)
    print("m55_round2_evidence.py · 素材迭代轮改前/改后对照（ISSUE-20260928-02）")
    print("-" * 96)
    print("%-30s %-9s %8s %8s %7s %8s %8s %8s %8s"
          % ("文件", "尺寸", "改前B", "改后B", "净增", "剪前帧前", "剪前帧后",
             "剪后帧前", "剪后帧后"))
    for r in rows:
        print("%-30s %-9s %8d %8d %+7d %8d %8d %8d %8d"
              % (r["name"], r["size"], r["before_bytes"], r["after_bytes"],
                 r["after_bytes"] - r["before_bytes"], r["before_raw"], r["after_raw"],
                 r["before_cut"], r["after_cut"]))
    print("-" * 96)
    print("x=1 外发光（剪后 α）改前 → 改后：")
    for r in rows:
        print("  %-30s %3d → %3d     （x=2: %3d → %3d）"
              % (r["name"], r["before_x1"], r["after_x1"], r["before_x2"], r["after_x2"]))
    print("-" * 96)
    print("zoom 按下态 29×29 边缘对照（中行前 8 px α）：")
    print("  41×41→29×29 重采样（＝引擎 0.71×，改前） %s" % midrow(resamp))
    print("  29×29 原生（改后）                      %s" % midrow(new_on29))
    print("  外沿 2px 带半透明像素 重采样 %d ｜ 原生 %d（%.2f× ⇒ 重采样把边摊开＝发虚）"
          % (semi_edge_count(resamp), semi_edge_count(new_on29),
             semi_edge_count(resamp) / max(1.0, semi_edge_count(new_on29))))
    print("  板/环外沿起点 x 重采样 %d ｜ 原生 %d ⇒ 重采样把按下态外沿挪了 %d px"
          "（与同键 off/over 的 29×29 原生件不一致）"
          % (ring_start(resamp), ring_start(new_on29),
             abs(ring_start(resamp) - ring_start(new_on29))))
    print("NEW 角标（改后）：字号 %d ｜ 墨迹 %.2f×%.2f（搜索上限 48×15）｜ 白字像素 bbox %s ｜ "
          "板内边距 左%d 右%d 上%d 下%d ｜ 四角 α=%s ｜ 左右边中点 α=%s"
          % (meta["size"], meta["ink_w"], meta["ink_h"], ink, pads[0], pads[1], pads[2],
             pads[3], corners, sides))
    print("-" * 96)
    print("变异自证（期望每条的 rc=1 且断言确实报错）：")
    for lab, rc, fails in muts:
        print("  [%s] %s → rc=%d" % ("OK" if rc == 1 else "!!", lab, rc))
        for x in fails:
            print("        %s" % x)
    print("-" * 96)
    tot_b = sum(r["before_bytes"] for r in rows)
    tot_a = sum(r["after_bytes"] for r in rows)
    print("小控件族合计：%d 件 ｜ %d → %d 字节（净增 %+d，即 %+.2f KB）"
          % (len(rows), tot_b, tot_a, tot_a - tot_b, (tot_a - tot_b) / 1024.0))
    print("证据：%s" % EVID)
    print("=" * 96)
    ok = all(r["after_cut"] == 0 and r["after_raw"] <= 10 for r in rows) \
        and all(rc == 1 for _l, rc, _f in muts) \
        and all(r["after_x1"] > 0 for r in rows)
    print("结果：**%s**" % ("全部符合预期" if ok else "存在不符项"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
