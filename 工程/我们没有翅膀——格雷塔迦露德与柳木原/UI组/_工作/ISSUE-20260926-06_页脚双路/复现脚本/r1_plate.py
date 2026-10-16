# -*- coding: utf-8 -*-
r"""r1 · 精确背景底板（plate）—— 页脚除字的新底源
原理：页脚背景在 10 件 PSV 屏间逐像素完全一致（r0_extra_src.py 实测 max diff = 0）。
      10 件中「该像素不在字足迹内」的屏取中位 → 该像素的真背景（雪晶一并精确保留）。
      仅当 10 件在该像素都在字足迹内时底板无效（只可能出现在右端 ⊗戻る／✿選択 文字框，
      因为该按钮在全部 10 件同位同字）。
注：字足迹 = 蓝笔画掩码 (b-r>20 且 lum<246) 膨胀 FOOT_DIL；
    膨胀已覆盖「近白字心 / 白外晕 / 蓝辉光」，故不再做洞填充
    （Pillow 12.3 的 ImageDraw.floodfill 实测为 no-op，且此处无需）。
输出：_证据\r_plate\plate.npy / plate.png / plate_valid.npy / plate_invalid.png / snow_mask.npy
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据", "r_plate"); os.makedirs(EV, exist_ok=True)

BX0, BX1, BY0, BY1 = 850, 1910, 930, 1088

SRCS10 = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
          "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png",
          "otv_gm_bg.png", "otv_bg_config_01.png", "otv_bg_config_02.png"]

BTH = 20        # 蓝饱和度阈值 b-r
FOOT_DIL = 16   # 字足迹膨胀半径（覆盖 蓝辉光 + 白外晕 + 字心）


def dilate_bool(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im) > 51


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im))
    return a.astype(np.float32)[BY0:BY1, BX0:BX1, :3]


def diffuse_fill(a, valid, radius=4, iters=900):
    """无效区用归一化盒式扩散填满（背景为平滑霜面，扩散值即真值）。
    num = BoxBlur(a*valid) / den = BoxBlur(valid)，逐次把有效值向无效区推进。"""
    out = a.copy()
    ok = valid.astype(np.float32)
    out[~valid] = 0
    for _ in range(iters):
        if valid.all():
            break
        num = np.asarray(Image.fromarray(out.astype(np.uint8)).filter(ImageFilter.BoxBlur(radius)),
                         np.float32)
        den = np.asarray(Image.fromarray((ok * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(radius)),
                         np.float32) / 255.0
        new = (den > 0) & (~valid)
        if not new.any():
            break
        nv = num[new] / den[new][:, None]
        # 限制推进量，避免跨大空洞取到远处值
        out[new] = np.clip(nv, 0, 255)
        valid = valid | new
        ok = valid.astype(np.float32)
    return out, valid


if __name__ == "__main__":
    B = np.stack([band(n) for n in SRCS10])
    N, H, W = B.shape[0], B.shape[1], B.shape[2]
    print("band", B.shape)

    foot = np.zeros((N, H, W), bool)
    for i in range(N):
        br = B[i, :, :, 2] - B[i, :, :, 0]
        lum = B[i].mean(axis=2)
        ink = (br > BTH) & (lum < 246)
        foot[i] = dilate_bool(ink, FOOT_DIL)
        print("  %-24s ink=%6d foot=%6d" % (SRCS10[i], int(ink.sum()), int(foot[i].sum())))

    free = ~foot
    nfree = free.sum(axis=0)
    valid0 = nfree >= 1
    print("有 ≥1 件无字足迹的像素 = %.2f%%" % (100.0 * valid0.mean()))
    plate = np.zeros((H, W, 3), np.float32)
    # 逐像素取「无字足迹屏」的中位
    for y in range(H):
        for x in range(W):
            f = free[:, y, x]
            if f.any():
                plate[y, x] = np.median(B[f, y, x], axis=0)

    if (~valid0).any():
        ys, xs = np.nonzero(~valid0)
        print("底板无效区 bbox x %d-%d  y %d-%d  px=%d" %
              (xs.min() + BX0, xs.max() + BX0, ys.min() + BY0, ys.max() + BY0, int((~valid0).sum())))
    plate, valid_filled = diffuse_fill(plate, valid0)
    valid = valid_filled

    # 置信度：无字足迹屏中与 plate 逐像素一致（各通道差<=1）的屏数；>=2 视作 plate 为真背景
    agree_n = np.zeros((H, W), np.int16)
    for i in range(N):
        d = np.abs(B[i] - plate).max(axis=2)
        agree_n += (free[i] & (d <= 1.0)).astype(np.int16)
    conf = (agree_n >= 2) & valid0
    print("plate 置信像素(>=2 屏一致) = %.2f%%" % (100.0 * conf.mean()))

    # 校验：每件「无字足迹」像素上 plate 应与原图完全一致
    for i, n in enumerate(SRCS10):
        m = (~foot[i]) & valid0
        d = np.abs(plate - B[i]).max(axis=2)[m]
        print("  %-24s 校验(无字足迹像素,%7d) max=%.1f mean=%.3f px>1=%d" %
              (n, int(m.sum()), d.max(), d.mean(), int((d > 1).sum())))

    br = plate[:, :, 2] - plate[:, :, 0]
    lum = plate.mean(axis=2)
    snow = (br >= 6) & (lum <= 252) & valid0
    print("\n底板淡蓝装饰 (b-r>=6 & lum<=252) px=%d" % int(snow.sum()))

    np.save(os.path.join(EV, "plate.npy"), plate)
    np.save(os.path.join(EV, "plate_valid.npy"), valid0)
    np.save(os.path.join(EV, "snow_mask.npy"), snow)
    np.save(os.path.join(EV, "free_count.npy"), nfree.astype(np.int16))
    np.save(os.path.join(EV, "conf_count.npy"), agree_n)
    Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).save(os.path.join(EV, "plate.png"))
    vis = np.clip(plate, 0, 255).astype(np.uint8).copy()
    vis[~valid0] = (255, 60, 60)
    Image.fromarray(vis).save(os.path.join(EV, "plate_invalid.png"))
    sv = np.clip(plate, 0, 255).astype(np.uint8).copy()
    sv[snow] = (255, 0, 0)
    Image.fromarray(sv).save(os.path.join(EV, "plate_snow_mask.png"))
    print("saved ->", EV)
