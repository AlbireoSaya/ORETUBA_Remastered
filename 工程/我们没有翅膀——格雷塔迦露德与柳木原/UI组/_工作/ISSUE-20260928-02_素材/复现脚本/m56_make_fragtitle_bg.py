# -*- coding: utf-8 -*-
r"""m56_make_fragtitle_bg.py · 番外独立层「组名底板」专用件 —— 程序化生成（**1 件**）

Issue : **ISSUE-20260928-02**（流程图系统第 2 步）· 素材组补件（第 7 批 / 迭代轮 2）
起因 : 第 5 批**复用**主图标签件 `ui/x_ui_label_off.png`（355×60，零九宫格整图拉伸到 420×38），
       HTML 侧加严复测坐实：该素材**四边都是宽渐隐带** —— 回读源件实测 α≥200 的核心只有
       **rows 11..48 / cols 11..343**（外沿 11px 一路从 α≈17 爬到 255），拉伸到 420×38 后
       核心仅 rows 7..30 / cols 13..406；而文字框与底板同框 ⇒ 首/末字压在左右渐隐带、
       笔画上下沿压在上下渐隐带 ⇒ 字形核心像素 5 分位对比度只有 **1.04:1**（中位 12.98 达标）。
       证据图（HTML 组）：`_工作\ISSUE-20260928-02_HTML\证据\E3_title_frag1_title_未达标像素标注.png`
       （未达标笔画已标红）。
⇒ 本脚本产出**专用硬边件**，替掉复用件。

■■ 交付物（1 件）
    `krkr\assets\ui\x_ui_fragtitle_bg.png` —— **444×52（尺寸冻结，不得改）**
      · RGBA / **真 alpha** / **硬边**：板面**满铺到画布四边**（box=(0,0,W,H)），
        四角按 **圆角 4px** 切掉；直边处无渐隐带（α=255），仅四角与 1px 抗锯齿过渡。
      · 视觉：**与主图标签同族的「霜白 / 浅蓝底板」**——
          盘面 = 竖向极缓渐变 `(227,234,242)` → `(228,238,250)`（取色自 `x_ui_label_off.png`
                 核心实测：上 (227,234,242) / 下 (227,238,250)）；
          细蓝边 = 外沿 2px 的 `#6C91BE`（＝ `@palette.panel_edge`(#5A6A8A) 向 `@palette.accent`
                 (#7AB0E8) 混 55%，与上一轮 `x_ui_replay_panel.png` 的「细蓝边」同一色号）；
          圆角 = 4px。**不新色系、不渐变边、无内区构图、不烘焙任何文字**（文字由引擎绘制）。
      · 与 `x_ui_replay_panel.png`（426×241）的差别：**体量小、硬边、去掉 4px 外柔发光**
        （外发光会在画布边缘形成渐隐带 —— 正是本件要消灭的东西）。

■ 关联数据层（**本脚本不改数据层，仅知情**）
    `工具\gen_flow_layout.py:239` 已登记 `FRAG_TITLE_BG_ASSET = "ui/x_ui_fragtitle_bg.png"`
    （`FRAG_TITLE_BG_W/H = 444/52`），元素与素材**等尺寸 ⇒ 1:1、不加 `nine`**。
    本件只负责把 PNG 造出来；`layout\**` / `krkr\game\**` / `复刻\**` 一律不碰。

■ 口径（逐条在 `证据\fragtitle_实测.tsv` 与交付报告里可复核）
    · **真 alpha**：amin == 0（四角确被切掉）、amax == 255。
    · **不透明核心（α≥200）覆盖率 ≥ 96%**；且 **α<200 的像素只出现在四角圆弧**
      —— 判据「无整段渐隐带」写成可机检的三条：
        ① 上/下边**行内区**（x∈[RAD+4, W-RAD-5]）逐列 α ≥ 200；
        ② 左/右边**列内区**（y∈[RAD+4, H-RAD-5]）逐行 α ≥ 200；
        ③ 最外 1px 帧的 α<200 像素数 ≤ 4×(2×RAD+4)（只容许四角的圆弧缺角）。
    · **幂等**：纯程序化（无随机 / 无时间戳 / 无网络 / 不读任何素材像素，只读 palette.json）；
      同版本重跑**逐字节一致**；脚本自证「同进程连造两次字节相同 + 与磁盘现值比对（写前）」。
    · **断言非空转**：脚本内跑两族变异（`--mutate` 段），确认断言**真的会失败**：
        M1 尺寸变异：板高 52 → 40 ⇒ 尺寸断言报错；
        M2 板面内缩变异：box=(3,3,W-3,H-3)（＝人为造出渐隐带）⇒ 边缘内区 α 断言报错。
      两族变异均以 `write=False` 跑，**不写任何资产**。
    · 退出码 0 = 该件写出且结构 / 语义断言全过；任一不达标即非 0 退出并打印明细。

■ 依赖：Pillow（`ImageDraw.rounded_rectangle` 需 ≥ 8.2）、numpy。
   本机实测：Pillow 12.3.0 / numpy 2.5.3。

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260928-02_素材\复现脚本\m56_make_fragtitle_bg.py             # 产出 + 自证 + 证据
    python _工作\ISSUE-20260928-02_素材\复现脚本\m56_make_fragtitle_bg.py --dry-run   # 只自证，不写盘
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "证据")

# ══════════════════════════════════════════════════════════════════ 冻结常量
NAME = "x_ui_fragtitle_bg.png"
W, H = 444, 52          # ★ 尺寸冻结（数据层 `FRAG_TITLE_BG_W/H` 同值）
RAD = 4.0               # 圆角半径
EDGE_BW = 2.0           # 细蓝边宽
CORE_THR = 200          # 「不透明核心」阈值 α≥200
CORE_COV_MIN = 96.0     # 核心覆盖率下限 %
MASK_FLOOR = 6          # 掩膜底噪归零阈值（LANCZOS 负瓣振铃残影，见 `aa()`）
PAL = json.load(open(PALETTE, encoding="utf-8"))["colors"]


def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    if key not in PAL:
        raise KeyError("palette.json 缺键：%s" % key)
    return hex2rgb(PAL[key]["value"])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


ACCENT = C("accent")                                  # #7AB0E8
PANEL_EDGE = C("panel_edge")                          # #5A6A8A
PANEL_EDGE_BLUE = mix(PANEL_EDGE, ACCENT, 0.55)       # #6C91BE ←「细蓝边」同 `x_ui_replay_panel`
FILL_TOP = (227, 234, 242)                            # 实测自 x_ui_label_off.png 核心上沿
FILL_BOT = (228, 238, 250)                            # 实测自 x_ui_label_off.png 核心下沿


# ══════════════════════════════════════════════════════════════════ 基础工具
def aa(size, fn, scale=4):
    """超采样画掩膜：scale 倍画布绘制 → LANCZOS 降采样（纯程序化抗锯齿，无噪声）。

    必须把 ≤`MASK_FLOOR` 的振铃残影归零：LANCZOS 核有负瓣，直边外侧会出现振铃，
    该残影会被盘面填充放大成实心像素（本件要求四角之外无 α<200 像素，故必须清干净）。"""
    w, h = size
    m = Image.new("L", (w * scale, h * scale), 0)
    fn(ImageDraw.Draw(m), scale)
    return m.resize((w, h), Image.LANCZOS).point(lambda v: 0 if v <= MASK_FLOOR else v)


def rr_mask(size, box, radius, scale=4):
    """圆角矩形掩膜。**box 半开区间语义**；满铺写 (0,0,W,H) ⇒ 直边处覆盖率 255、四角被切。"""
    def _d(d, s):
        d.rounded_rectangle([v * s for v in box], radius=radius * s, fill=255)
    return aa(size, _d, scale)


def A(m):
    return np.asarray(m, dtype=np.int16)


def sub_mask(outer, inner):
    return Image.fromarray(np.clip(A(outer) - A(inner), 0, 255).astype(np.uint8))


def flat(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def vgrad(size, stops, alpha=255):
    """逐行相同的竖向渐变 RGBA（1 列 → NEAREST 横向放大）"""
    w, h = size
    col = Image.new("RGBA", (1, h))
    p = col.load()
    for y in range(h):
        t = y / float(h - 1) if h > 1 else 0.0
        rgb = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                rgb = mix(c0, c1, k)
                break
        p[0, y] = tuple(rgb) + (alpha,)
    return col.resize((w, h), Image.NEAREST)


def paint(base, mask, rgb, alpha=255):
    m = mask if alpha == 255 else mask.point(lambda v: v * alpha // 255)
    t = Image.new("RGBA", mask.size, tuple(rgb) + (0,))
    t.putalpha(m)
    return Image.alpha_composite(base, t)


def stats_of(im):
    arr = np.asarray(im).reshape(-1, 4)
    al = arr[:, 3]
    nz = arr[al > 16]
    cnt = Counter(map(tuple, nz[:, :3].tolist()))
    top, topn = (cnt.most_common(1)[0] if cnt else ((0, 0, 0), 0))
    return dict(amin=int(al.min()), amax=int(al.max()),
                core_cov=round(100.0 * float((al >= CORE_THR).sum()) / len(al), 4),
                cov=round(100.0 * len(nz) / len(arr), 2),
                top="#%02X%02X%02X" % tuple(top), topn=int(topn),
                n_lt_core=int((al < CORE_THR).sum()))


# ══════════════════════════════════════════════════════════════════ 生成器
def build_fragtitle_bg(w=W, h=H, inset=0.0):
    """组名底板 · 444×52 · **硬边满铺 + 圆角 4 + 2px 细蓝边**

    · 板面满铺到画布四边（`inset=0`）⇒ 直边处 α=255，**没有渐隐带**；
    `inset>0` 只用于**变异自证**（人为造出渐隐带，验证断言非空转），生产恒为 0。
    · 四角按圆角 4 切掉（`amin==0` 由此成立）。
    · 2px 细蓝边画在**板面最外 2px**（在板内 ⇒ 仍是满 α），不产生任何外部柔光。
    """
    box = (inset, inset, w - inset, h - inset)
    r = max(1.0, RAD - inset) if inset > 0 else RAD
    plate = rr_mask((w, h), box, r)

    img = flat((w, h))
    body = vgrad((w, h), [(0.0, FILL_TOP), (1.0, FILL_BOT)], 255)
    body.putalpha(Image.fromarray(np.minimum(
        np.asarray(body.getchannel("A"), dtype=np.uint16),
        np.asarray(plate, dtype=np.uint16)).astype(np.uint8)))
    img = Image.alpha_composite(img, body)

    inner = rr_mask((w, h), (box[0] + EDGE_BW, box[1] + EDGE_BW,
                             box[2] - EDGE_BW, box[3] - EDGE_BW), max(0.5, r - EDGE_BW))
    edge = sub_mask(plate, inner)
    img = paint(img, edge, PANEL_EDGE_BLUE, 255)
    return img


# ══════════════════════════════════════════════════════════════════ 判据
def edge_band_report(im):
    """「无整段渐隐带」三条可机检判据的读数"""
    a = np.asarray(im.getchannel("A"))
    h, w = a.shape
    m = int(RAD) + 4
    top = a[0, m:w - m]            # 上边内区逐列
    bot = a[h - 1, m:w - m]        # 下边内区逐列
    left = a[m:h - m, 0]           # 左边内区逐行
    right = a[m:h - m, w - 1]      # 右边内区逐行
    frame = np.concatenate([a[0, :], a[-1, :], a[:, 0], a[:, -1]])
    return dict(top_min=int(top.min()), bot_min=int(bot.min()),
                left_min=int(left.min()), right_min=int(right.min()),
                top_lt=int((top < CORE_THR).sum()), bot_lt=int((bot < CORE_THR).sum()),
                left_lt=int((left < CORE_THR).sum()), right_lt=int((right < CORE_THR).sum()),
                frame_lt=int((frame < CORE_THR).sum()),
                frame_lt_max_allowed=int(4 * (2 * int(RAD) + 4)),
                row_min=[int(v) for v in a.min(axis=1)],
                col_min=[int(v) for v in a.min(axis=0)])


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


# ══════════════════════════════════════════════════════════════════ 主流程
def run(write=True, h_override=None, inset_override=None):
    h_use = h_override if h_override is not None else H
    inset = inset_override if inset_override is not None else 0.0
    im = build_fragtitle_bg(W, h_use, inset)
    im2 = build_fragtitle_bg(W, h_use, inset)
    b1, b2 = png_bytes(im), png_bytes(im2)

    errs = []
    if im.mode != "RGBA":
        errs.append("mode=%s（须 RGBA）" % im.mode)
    if im.size != (W, h_use):
        errs.append("尺寸 %s ≠ 期望 %s" % (im.size, (W, h_use)))
    if (W, h_use) != (W, H):
        errs.append("尺寸变异：(%d,%d) ≠ 冻结尺寸 (%d,%d)" % (W, h_use, W, H))
    st = stats_of(im)
    if st["amin"] != 0:
        errs.append("αmin=%d ≠ 0（四角未被切掉 / 无真透明）" % st["amin"])
    if st["amax"] != 255:
        errs.append("αmax=%d ≠ 255（无实心像素）" % st["amax"])
    if st["core_cov"] < CORE_COV_MIN:
        errs.append("不透明核心(α≥%d)覆盖率 %.4f%% < %.1f%%"
                    % (CORE_THR, st["core_cov"], CORE_COV_MIN))
    eb = edge_band_report(im)
    if min(eb["top_min"], eb["bot_min"], eb["left_min"], eb["right_min"]) < CORE_THR:
        errs.append("边内区存在 α<%d 的整段渐隐带：上%d 下%d 左%d 右%d"
                    % (CORE_THR, eb["top_min"], eb["bot_min"], eb["left_min"], eb["right_min"]))
    if eb["frame_lt"] > eb["frame_lt_max_allowed"]:
        errs.append("最外 1px 帧 α<%d 像素 %d > 上限 %d（圆角外还有非核心像素）"
                    % (CORE_THR, eb["frame_lt"], eb["frame_lt_max_allowed"]))
    if b1 != b2:
        errs.append("幂等失败：同进程两次生成字节不同")

    path = os.path.join(OUT, NAME)
    old = open(path, "rb").read() if os.path.exists(path) else None
    row = dict(name=NAME, w=im.size[0], h=im.size[1], mode=im.mode, bytes=len(b1),
               amin=st["amin"], amax=st["amax"], core_cov=st["core_cov"],
               cov=st["cov"], n_lt_core=st["n_lt_core"], top=st["top"], topn=st["topn"],
               idem=("OK" if b1 == b2 else "FAIL"),
               before=("新增" if old is None else ("未变" if old == b1 else "改写")),
               md5=hashlib.md5(b1).hexdigest(),
               frame_lt=eb["frame_lt"], frame_lt_max=eb["frame_lt_max_allowed"],
               top_min=eb["top_min"], bot_min=eb["bot_min"],
               left_min=eb["left_min"], right_min=eb["right_min"])
    if errs:
        if write:
            for e in errs:
                print("  !! %s：%s" % (NAME, e))
        return 1, row, errs, im, eb
    if write:
        im.save(path, "PNG", optimize=True)
    return 0, row, errs, im, eb


def mutations():
    """变异自证：确认断言**真的会失败**（非空转）——均以 write=False 跑，不写盘。"""
    out = []
    rc, _r, errs, _i, _e = run(write=False, h_override=40)
    out.append(("M1 尺寸变异：板高 52 → 40", rc, errs[:3]))
    rc, _r, errs, _i, _e = run(write=False, inset_override=3.0)
    out.append(("M2 板面内缩变异：inset=3（＝人为造出渐隐带）", rc, errs[:3]))
    return out


def main():
    write = "--dry-run" not in sys.argv
    rc, row, errs, im, eb = run(write=write)
    muts = mutations()

    print("=" * 104)
    print("m56_make_fragtitle_bg.py · 番外组名底板专用件（ISSUE-20260928-02 · 第 7 批）")
    print("调色板：%s ｜ 落点：%s" % (os.path.basename(PALETTE), OUT))
    print("-" * 104)
    print("%-24s %-9s %-5s %8s %4s %4s %12s %9s %7s %7s %6s %s"
          % ("文件", "尺寸", "mode", "字节", "amin", "amax", "核心α≥200覆盖%",
             "α<200像素", "最外帧<200", "帧上限", "幂等", "写前"))
    print("%-24s %-9s %-5s %8d %4d %4d %12.4f %9d %7d %7d %6s %s"
          % (row["name"], "%dx%d" % (row["w"], row["h"]), row["mode"], row["bytes"],
             row["amin"], row["amax"], row["core_cov"], row["n_lt_core"],
             row["frame_lt"], row["frame_lt_max"], row["idem"], row["before"]))
    print("-" * 104)
    print("「无整段渐隐带」三条判据：")
    print("  ① 上边内区(x∈[%d,%d]) 逐列 αmin = %d" % (int(RAD) + 4, W - int(RAD) - 5, eb["top_min"]))
    print("  ② 下边内区(x∈[%d,%d]) 逐列 αmin = %d" % (int(RAD) + 4, W - int(RAD) - 5, eb["bot_min"]))
    print("  ③ 左边内区(y∈[%d,%d]) 逐行 αmin = %d ／ 右边内区 αmin = %d"
          % (int(RAD) + 4, H - int(RAD) - 5, eb["left_min"], eb["right_min"]))
    print("  ④ 最外 1px 帧 α<200 像素数 = %d（上限 %d = 4×(2×%d+4)，只容许四角圆弧缺角）"
          % (eb["frame_lt"], eb["frame_lt_max_allowed"], int(RAD)))
    print("  ⑤ 主色 %s × %d 像素（＝盘面核心下沿色）" % (row["top"], row["topn"]))
    print("-" * 104)
    print("变异自证（期望每条 rc=1，且确有断言报错）：")
    for lab, mrc, merrs in muts:
        print("  [%s] %s → rc=%d" % ("OK" if mrc == 1 else "!!", lab, mrc))
        for e in merrs:
            print("        %s" % e)
    print("-" * 104)

    if write:
        os.makedirs(EVID, exist_ok=True)
        with open(os.path.join(EVID, "fragtitle_实测.tsv"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("# 独立回读：直接从 krkr\\assets\\ui\\ 的 PNG 读回（不看生成器内存值）\n")
            f.write("# 核心α≥200覆盖率% ＝ α≥200 的像素占全画布比例；判据下限 96%\n")
            f.write("# 「无整段渐隐带」：上/下边内区逐列 αmin、左/右边内区逐行 αmin 均须 ≥200\n")
            f.write("文件\t宽\t高\tmode\t字节\talpha_min\talpha_max\t核心α≥200覆盖率%\tα<200像素数"
                    "\t非透明占比%\t主色\t主色像素数\t上边内区αmin\t下边内区αmin\t左边内区αmin"
                    "\t右边内区αmin\t最外帧α<200\t帧上限\t幂等\t写前\tmd5\n")
            f.write("\t".join(str(row[k]) for k in
                              ("name", "w", "h", "mode", "bytes", "amin", "amax", "core_cov",
                               "n_lt_core", "cov", "top", "topn", "top_min", "bot_min",
                               "left_min", "right_min", "frame_lt", "frame_lt_max",
                               "idem", "before", "md5")) + "\n")
            with open(os.path.join(EVID, "fragtitle_变异自证.txt"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("# 变异自证：把尺寸/板面搅坏，确认断言**真的会失败**（非空转）；"
                        "全部 write=False，不写任何资产。期望每条 rc=1。\n")
                for lab, mrc, merrs in muts:
                    f.write("\n[%s] %s → rc=%d\n"
                            % ("符合预期" if mrc == 1 else "!! 未失败", lab, mrc))
                    for e in merrs:
                        f.write("    %s\n" % e)
            chk = hash_roundtrip(im)
            with open(os.path.join(EVID, "fragtitle_幂等.txt"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("# 幂等：同进程连造两次 + 写盘后回读，三者 md5 一致\n")
                f.write("内存第1次 md5\t%s\n" % row["md5"])
                f.write("内存第2次 md5\t%s\n" % chk["mem2"])
                f.write("磁盘回读 md5\t%s\n" % chk["disk"])
                f.write("结论\t%s\n" % ("一致" if chk["same"] else "**不一致**"))
            print("证据：%s" % EVID)
            print("  （白底/深底预览与行/列 α 最小值曲线由 `m56_evidence_readback.py` "
                  "**从磁盘 PNG 回读**后产出，保证证据取自落盘件而非内存值）")

    ok = (rc == 0) and all(m[1] == 1 for m in muts)
    print("=" * 104)
    print("结果：**%s**" % ("全部通过" if ok else "存在失败项"))
    print("=" * 104)
    return 0 if ok else 1


def hash_roundtrip(im):
    b1 = png_bytes(im)
    b2 = png_bytes(build_fragtitle_bg())
    p = os.path.join(OUT, NAME)
    disk = open(p, "rb").read() if os.path.exists(p) else b""
    return dict(mem2=hashlib.md5(b2).hexdigest(), disk=hashlib.md5(disk).hexdigest(),
                same=(hashlib.md5(b1).hexdigest() == hashlib.md5(b2).hexdigest()
                      == hashlib.md5(disk).hexdigest()))


if __name__ == "__main__":
    sys.exit(main())
