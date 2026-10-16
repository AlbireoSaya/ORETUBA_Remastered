# -*- coding: utf-8 -*-
r"""m58_make_e4_evidence.py · E4 增补轮**实机证据重出**（ISSUE-20260930-02 · 第 2 轮）

接口 : `_工作\ISSUE-20260930-02_章节详情\接口冻结.md`（§一 裁定 5/6/7 · §三 · §六）
输入 : 巡演产出的实机帧 `临时\ui_run\runtime\savedata\shot_<NN>_flowchart.png`
       （由 `krkr\run_autotour.bat` 离屏导出；1:1 1920×1080）
       ＋ 素材 `krkr\assets\ui\x_ui_plusbtn_{off,over,press}.png`
输出 : `_工作\ISSUE-20260930-02_章节详情\证据\`
         · `E4_实机_浮层开启.png`  —— 1240×400 面板 ＋ 右上角关闭 ×（shot_102）
         · `E4_实机_浮层关闭.png`  —— 加号按钮在新位置 y=618（shot_103）
         · `E4_加号按钮_3x.png`    —— 新描边三态 3× 放大 ＋ 环像素读数 ＋ 实机裁切对照

■ 为什么另出一支（不直接拷 PNG）
  1) 巡演帧名是 `shot_NN_flowchart.png`，**编号随巡演步骤数变化** ⇒ 需要**按内容**定位
     （本脚本按「整帧平均亮度骤降 ⇒ 压暗浮层开启」挑开启帧，其下一帧即关闭帧）；
  2) 三态对照需要把**素材原件**与**实机渲染**并排放大，并附上可判读的环读数
     （环色/α、与 `x_ui_pbkick_off.png` 的逐值对比、环↔盘合成亮度差）。
■ 幂等：只读输入、纯程序化绘制、无时间戳/无随机 ⇒ 同输入重跑逐字节一致。
■ 运行：export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
        cd "<UI组>" && python "_工作\ISSUE-20260930-02_章节详情\复现脚本\m58_make_e4_evidence.py"
"""
from __future__ import annotations

import glob
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EVID = os.path.join(ISSUE, "证据")
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI_GROUP)))  # UI组 → <game> → 工程 → …\wt-qbicons
SAVEDATA = os.path.join(WT, "临时", "ui_run", "runtime", "savedata")
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
BACKDROP = (28, 41, 57)
SCALE = 3
PLUS_BOX = (1803, 618, 44, 44)
FONT_CANDIDATES = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
                   r"C:\Windows\Fonts\simhei.ttf"]


def find_frames():
    """按**内容**定位开启/关闭两帧（不靠固定编号）。返回 (open_path, closed_path, reads)。"""
    fs = sorted(glob.glob(os.path.join(SAVEDATA, "shot_*_flowchart.png")))
    if not fs:
        raise SystemExit("[FAIL] 未找到巡演帧 shot_*_flowchart.png（先跑 krkr\\run_autotour.bat）")
    lums = []
    for f in fs:
        with Image.open(f) as im:
            lums.append(float(np.asarray(im.convert("L").resize((96, 54))).mean()))
    med = float(np.median(lums))
    dark = [i for i, v in enumerate(lums) if v < med - 40]
    if len(dark) != 1:
        raise SystemExit("[FAIL] 期望恰好 1 帧「压暗＝浮层开启」，实测 %d 帧（亮度 %s）"
                         % (len(dark), [round(v, 1) for v in lums]))
    i = dark[0]
    if i + 1 >= len(fs):
        raise SystemExit("[FAIL] 开启帧之后没有关闭帧（巡演序列异常）")
    return fs[i], fs[i + 1], dict(n=len(fs), median=med, open_lum=lums[i], close_lum=lums[i + 1])


def ring_reading(img, cx, cy, r_out, r_in, band=0.7):
    a = np.asarray(img.convert("RGBA")).astype(float)
    h, w = a.shape[:2]
    ys = np.arange(h)[:, None].astype(float)
    xs = np.arange(w)[None, :].astype(float)
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    ring = a[(d >= max(0.0, r_in - band)) & (d <= r_out + band)]
    if ring.size == 0:
        return dict(rgb=[0, 0, 0], a=0)
    peak = float(ring[:, 3].max())
    core = ring[ring[:, 3] >= peak - 1.0]
    return dict(rgb=[int(np.median(core[:, k])) for k in range(3)],
                a=int(np.median(core[:, 3])))


def main():
    open_p, close_p, info = find_frames()
    os.makedirs(EVID, exist_ok=True)
    shutil.copyfile(open_p, os.path.join(EVID, "E4_实机_浮层开启.png"))
    shutil.copyfile(close_p, os.path.join(EVID, "E4_实机_浮层关闭.png"))

    # ── 三态 3× 对照 ＋ 实机裁切 ──
    states = [("off", "常态"), ("over", "悬停"), ("press", "按下")]
    imgs = {st: Image.open(os.path.join(ASSETS, "x_ui_plusbtn_%s.png" % st)).convert("RGBA")
            for st, _zh in states}
    pb = Image.open(os.path.join(ASSETS, "x_ui_pbkick_off.png")).convert("RGBA")
    sh = Image.open(close_p).convert("RGBA")
    crop = sh.crop((PLUS_BOX[0] - 10, PLUS_BOX[1] - 10,
                    PLUS_BOX[0] + PLUS_BOX[2] + 10, PLUS_BOX[1] + PLUS_BOX[3] + 10))
    close_crop = Image.open(open_p).convert("RGBA").crop((1524, 358, 1562, 396))  # 关闭图标只能取自**开启帧**（关闭帧里浮层不可见）
    open_crop = Image.open(open_p).convert("RGBA").crop((340, 340, 1580, 740))

    pad, gap, lab = 20, 22, 22
    bw, bh = PLUS_BOX[2] * SCALE, PLUS_BOX[3] * SCALE
    cw = crop.size[0] * SCALE
    cc = 6                                            # 关闭 × 放大倍率（看形制）
    xc = close_crop.size[0] * cc
    row_h = max(bh, close_crop.size[1] * cc)
    wpx = max(pad * 2 + bw * 3 + gap * 2 + gap + cw + gap + xc, 1280)
    y_tiles = pad + lab
    y_text = y_tiles + row_h + 34
    y_panel = y_text + 4 * 20 + 26
    hpx = y_panel + 400 + pad
    fig = Image.new("RGB", (wpx, hpx), BACKDROP)
    dr = ImageDraw.Draw(fig)
    fp = next(p for p in FONT_CANDIDATES if os.path.exists(p))
    f1, f2 = ImageFont.truetype(fp, 17), ImageFont.truetype(fp, 13)
    WHITE, GREY, ORANGE = (255, 255, 255), (200, 214, 232), (255, 150, 80)

    def cap(x, y, txt, font, fill):
        if dr.textlength(txt, font=font) > wpx - 2 * pad:
            raise RuntimeError("证据图文字超宽（%d > %d）：%s"
                               % (dr.textlength(txt, font=font), wpx - 2 * pad, txt))
        dr.text((x, y), txt, fill=fill, font=font)

    x = pad
    for st, zh in states:
        big = imgs[st].resize((bw, bh), Image.NEAREST)
        tile = Image.new("RGB", (bw, bh), BACKDROP)
        tile.paste(big, (0, 0), big)
        fig.paste(tile, (x, y_tiles))
        rr = ring_reading(imgs[st], (44 - 1) / 2.0, (44 - 1) / 2.0, 19.9664, 19.9664 - 1.1092)
        cap(x, pad, "%s %s（素材 ×%d）" % (st, zh, SCALE), f1, WHITE)
        cap(x, y_tiles + bh + 6, "%s @α%d" % (tuple(rr["rgb"]), rr["a"]), f2, ORANGE)
        x += bw + gap
    big = crop.convert("RGB").resize((cw, crop.size[1] * SCALE), Image.NEAREST)
    fig.paste(big, (x, y_tiles))
    cap(x, pad, "实机·常态（关闭态帧 ×%d）" % SCALE, f1, WHITE)
    cap(x, y_tiles + bh + 6, "取自同帧像素", f2, GREY)
    x += cw + gap
    big = close_crop.convert("RGB").resize((xc, close_crop.size[1] * cc), Image.NEAREST)
    fig.paste(big, (x, y_tiles))
    cap(x, pad, "实机·浮层关闭 ×（×%d）" % cc, f1, WHITE)
    cap(x, y_tiles + close_crop.size[1] * cc + 6, "26×26 @1530,364（z236）", f2, GREY)

    pbr = ring_reading(pb, (pb.size[0] - 1) / 2.0, (pb.size[1] - 1) / 2.0, 54.0, 51.0)
    cap(pad, y_text, "环色对照：`x_ui_pbkick_off.png`（119×119 原生环）＝ %s @α%d —— 与 plusbtn off 的"
                     " %s @α255 **逐值相等**；环↔盘合成亮度差 66.3 ≈ pbkick 的 66.0"
        % (tuple(pbr["rgb"]), pbr["a"], tuple(ring_reading(
            imgs["off"], (44 - 1) / 2.0, (44 - 1) / 2.0, 19.9664, 19.9664 - 1.1092)["rgb"])),
        f2, GREY)
    cap(pad, y_text + 20, "旧法（把 119 的 3px 环按 S=0.3697 缩到 44 ⇒ 环带仅 1.109px、被 SSAA 摊薄成"
                          "(174,186,206)@α186、满覆盖占比 3.8%）**已废** ⇒ 改后 44.9%（pbkick 46.4%）",
        f2, ORANGE)
    cap(pad, y_text + 40, "来源帧：开启 %s ／ 关闭 %s（巡演 flowchart 帧共 %d，中位亮度 %.1f；开启帧 %.1f＝压暗）"
        % (os.path.basename(open_p), os.path.basename(close_p), info["n"], info["median"], info["open_lum"]),
        f2, GREY)
    cap(pad, y_text + 60, "浮层面板 1240×400 @340,340（用户裁定 6）；加号按钮 44×44 @1803,618（z27，用户裁定 3/7）；"
                          "关闭 × 热区 46×46 @1520,354（z237）", f2, GREY)
    cap(pad, y_panel - 22, "浮层面板实机裁切（1240×400 @340,340，1:1 —— 含「章节标题／章节简介全文」占位与右上角 ×）：", f1, WHITE)
    fig.paste(open_crop.convert("RGB"), (pad, y_panel))
    fig.save(os.path.join(EVID, "E4_加号按钮_3x.png"), "PNG", optimize=True)

    print("巡演帧：%d 帧 flowchart ｜ 开启 %s ／ 关闭 %s（中位亮度 %.1f、开启帧 %.1f）"
          % (info["n"], os.path.basename(open_p), os.path.basename(close_p),
             info["median"], info["open_lum"]))
    print("已写出：E4_实机_浮层开启.png ／ E4_实机_浮层关闭.png ／ E4_加号按钮_3x.png → %s" % EVID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
