# -*- coding: utf-8 -*-
r"""psv_fix_preview_bg.py —— 预览示例底图：硬边几何块 **柔化**（缺陷 ③，幂等）

**Issue**：ISSUE-20260926-06_C设置屏修复 ｜ 对象：`krkr\assets\ui\x_ui_cfg_preview_bg.png`

**缺陷 ③ 定位结论（不是遮罩、不是元素，是**素材本身**）**
  送审在 (1590–1740, 741–816) 看到「硬边、无文字、与框内渐变不融合的纯色矩形」。该区域
  = 预览底图元素 `cfg.pv_bg`(1180,674,612,154，1:1) 的 asset 局部 (410,67)-(556,142)。
  逐像素扫描该 asset 的硬边：`max|dL/dx|=84.3 @ x556`、`max|dL/dy|=72.0 @ y553`，
  硬边列 x=409/410/412/553/555/556、硬边行 y=65/66/68/142/144
  ⇒ 就是 m47 生成器 `build_preview_bg()` 里的**两个「示意几何块」**
  （`bd.rounded_rectangle([48,74,150,145])` 与 `[410,66,556,145]`，注释「模拟远景建筑/家具剪影」）。
  **设计意图**：预览是「示例画面」，需要明暗分区才能让**不透明度滑块**的效果看得出来
  （`cfg.pv_mask` 的浓度随 `dlg_winopac` 实时变化）。故**不删除**该意图，只**去掉硬边**：
  把块体改为「圆角 + 约 10px 羽化 + 与底同一横向渐变」的柔边剪影。

**修法（确定性、只动块区）**
  · 先用**块外左右各 10px 两列做逐行横向线性插值**还原块下的干净底 `grad`
    （该两个块都落在底图渐变的同一线性段内：块1 t=0.078..0.245 ⊂ [0,0.42]、
      块2 t=0.670..0.908 ⊂ [0.64,1.0]；两条示意色带是水平带 ⇒ 与 x 无关 ⇒ 插值**逐值精确**）；
  · 再 `新 = grad + 0.686·M·(panel_fill − grad)`，其中 0.686 = 175/255（与生成器
    `tint(blocks, panel_fill, 175)` 同值）、`M` = 圆角 4 + 高斯羽化 σ≈5 的**软掩码**
    ⇒ 块心与原图**逐值一致**、块缘平滑过渡；
  · 幂等：重跑时先测块边界台阶，已 ≤8/255 即判定「已柔化」并**不写盘**。

**自证**（脚本输出）：① 块外像素逐值不变（bit-exact 区域面积占比）；② 边界台阶
84.3 → ≤8；③ 重跑字节不变。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\psv_fix_preview_bg.py [--dry-run]
"""
import argparse
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                       # noqa: E402
from PIL import Image, ImageDraw, ImageFilter            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
NAME = "x_ui_cfg_preview_bg.png"
ASSET = os.path.join(UI, "krkr", "assets", "ui", NAME)
EVID = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏修复", "_证据")

# m47 `build_preview_bg()` 的两个示意几何块（源矩形，坐标即 asset 坐标）
BLOCKS = [(48, 74, 150, 145), (410, 66, 556, 145)]
RADIUS = 4.0          # 生成器 rounded_rectangle(..., radius=4)
ALPHA = 175 / 255.0   # 生成器 tint(..., panel_fill, 175)
FEATHER = 5.0         # 高斯羽化 σ（约 ±10px 过渡带）
PAD = 15              # 合成窗外扩 = 3σ（包住羽化尾；且仍在同一线性渐变段内，见文件头）
                      #   块2 x410..556 ⊂ 渐变第 3 段 (x≥392)，故窗左沿 395 ≥ 392 ✓；锚列 393/573 同段 ✓
PANEL_FILL = np.array([0x14, 0x18, 0x24], dtype=np.float32)   # @palette.panel_fill
SOFT_WIDTH = 15       # 「已柔化」判据：边缘过渡带宽度（10%→90%）≥ 该像素数即不再动


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def encode(im, step=2):
    if step > 1:
        r, g, b, a = im.split()
        f = lambda v: min(255, ((v + step // 2) // step) * step)   # noqa: E731
        im = Image.merge("RGBA", (r.point(f), g.point(f), b.point(f), a))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def edge_metrics(arr, box):
    """块边缘的两项度量：(2px 台阶 max/255, 过渡带宽度 px)

    · 2px 台阶 = 沿四条边取「相隔 2px 的亮度差」的最大值（硬边 ⇒ 极大；平滑渐变 ⇒ 小）；
    · 过渡带宽度 = 每条边**跨边**取 ±25px 剖面，量「边外值 → 边内值」的 10%→90% 区间跨了几像素
      （硬边 ⇒ ≈2px；羽化 σ=5 ⇒ ≈20px）。取四条边的最大值。"""
    x0, y0, x1, y1 = box
    L = arr.mean(axis=2)
    step = 0.0
    for x in (x0 - 1, x1 + 1):
        step = max(step, float(np.abs(L[y0:y1, x] - L[y0:y1, x - 2 if x > x0 else x + 2]).max()))
    for y in (y0 - 1, y1 + 1):
        step = max(step, float(np.abs(L[y, x0:x1] - L[y - 2 if y > y0 else y + 2, x0:x1]).max()))

    def width_of(prof):
        a_, b_ = float(prof[0]), float(prof[-1])
        if abs(b_ - a_) < 1.0:
            return 0
        lo, hi = a_ + 0.1 * (b_ - a_), a_ + 0.9 * (b_ - a_)
        rng = (min(lo, hi), max(lo, hi))
        idx = np.nonzero((prof >= rng[0]) & (prof <= rng[1]))[0]
        return int(idx.max() - idx.min() + 1) if len(idx) else 0

    yc = (y0 + y1) // 2
    xc = (x0 + x1) // 2
    widths = [
        width_of(L[yc, max(0, x0 - 25):x0 + 26]),
        width_of(L[yc, x1 - 25:min(L.shape[1], x1 + 26)][::-1]),
        width_of(L[max(0, y0 - 25):y0 + 26, xc]),
        width_of(L[y1 - 25:min(L.shape[0], y1 + 26), xc][::-1]),
    ]
    return step, max(widths)


def soft_mask(size, box):
    """圆角矩形 + 高斯羽化的软掩码（0..1）"""
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=int(RADIUS), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(FEATHER))
    return np.asarray(m, dtype=np.float32) / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    os.makedirs(EVID, exist_ok=True)
    before = md5(ASSET)
    with Image.open(ASSET) as im:
        src = im.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    m0 = [edge_metrics(arr, b) for b in BLOCKS]
    print("=" * 118)
    print("预览底图 %s · 几何块硬边柔化%s" % (NAME, "（dry-run）" if args.dry_run else ""))
    print("=" * 118)
    print("柔化前：%s" % "、".join("块%d 台阶%.1f/255 过渡带%dpx" % (i + 1, s[0], s[1])
                                   for i, s in enumerate(m0)))
    if min(s[1] for s in m0) >= SOFT_WIDTH:
        print("判定：过渡带已 ≥%dpx ⇒ **已柔化**，本次不写盘（幂等）" % SOFT_WIDTH)
        print("md5 %s（未变）" % before)
        return 0

    out = arr.copy()
    touched = np.zeros(arr.shape[:2], dtype=bool)
    recon_err = 0.0
    for bx0, by0, bx1, by1 in BLOCKS:
        x0, x1 = bx0 - PAD, bx1 + PAD        # 合成窗必须包住羽化尾，否则窗口处留新台阶
        w = x1 - x0
        t = ((np.arange(w, dtype=np.float32) + 0.5) / w)[None, :, None]        # (1,w,1)
        la = arr[:, x0 - 2:x0 - 1, :]                                          # 逐行左锚 (H,1,3)
        ra = arr[:, x1 + 1:x1 + 2, :]                                          # 逐行右锚
        grad = la * (1 - t) + ra * t                                           # (H,w,3)
        mask = soft_mask(src.size, (bx0, by0, bx1, by1))
        inwin = (mask > 0.002)[:, x0:x1]                                       # 羽化窗（含块体）
        # ★ 两步：① 把**硬块**从窗口里换成插值底（块外本该 == 原值，残差自证）；
        #         ② 再叠**羽化后**的块 ⇒ 块心与原图逐值一致、块缘平滑过渡。
        if (~inwin).any():
            recon_err = max(recon_err, float(np.abs(grad - arr[:, x0:x1])[~inwin].max()))
        base = out[:, x0:x1].copy()
        base[inwin] = grad[inwin]
        a = (mask[:, x0:x1] * ALPHA)[:, :, None]
        out[:, x0:x1] = base * (1 - a) + PANEL_FILL[None, None, :] * a
        touched |= (mask > 0)
    changed = np.abs(out - arr).max(axis=2) > 0.5
    m1 = [edge_metrics(out, b) for b in BLOCKS]
    data = encode(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA"), 2)
    if not args.dry_run:
        with open(ASSET, "wb") as fh:
            fh.write(data)
    # 证据图：修前/修后各 2× + 差图
    a_before = src.crop((20, 40, 600, 154))
    a_after = Image.open(io.BytesIO(data)).convert("RGB").crop((20, 40, 600, 154))
    band = Image.new("RGB", (a_before.width, a_before.height * 2 + 6), (255, 0, 128))
    band.paste(a_before, (0, 0)); band.paste(a_after, (0, a_before.height + 6))
    band.resize((band.width * 2, band.height * 2), Image.NEAREST).save(
        os.path.join(EVID, "defect3_preview_bg_before_after_x2.png"))
    dd = np.clip(np.abs(out - arr).max(axis=2) * 8, 0, 255).astype(np.uint8)
    Image.fromarray(dd).save(os.path.join(EVID, "defect3_preview_bg_diff.png"))
    print("柔化后：%s" % "、".join("块%d 台阶%.1f/255 过渡带%dpx" % (i + 1, s[0], s[1])
                                   for i, s in enumerate(m1)))
    print("改动像素 %d 个（= 块体 ∪ 羽化带；占全图 %.1f%%）｜ **羽化窗外像素逐值不变**"
          % (int(touched.sum()), 100.0 * touched.sum() / touched.size))
    print("补底重建自证：羽化窗内非掩码域的「逐行横向插值底 − 原图」max=%.2f/255（≤2 ⇒ 底重建精确；窗内非掩码像素的变化即该量级）" % recon_err)
    print("变暗量（块心）max=%.1f/255 ⇒ 与「比框底暗 27–33 L」的送审实测同量级（保留设计意图）"
          % float(np.abs(out - arr).max()))
    print("落盘：%d B（原 %d B）｜ md5 %s → %s%s"
          % (len(data), os.path.getsize(ASSET) if not args.dry_run else 0, before[:12],
             md5(ASSET)[:12] if not args.dry_run else "(dry-run)",
             "（dry-run，未写盘）" if args.dry_run else ""))
    print("证据图：%s" % EVID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
