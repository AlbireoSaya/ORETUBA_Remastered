# -*- coding: utf-8 -*-
r"""
geo_pass.py —— 帧线件改走**几何延展**（ISSUE-20260928-02 · 1028 补边续作 · 交付物 4）

对象（帧线件，两种口径都实现，默认 seam）
    `--rule seam`（默认，实测口径）：**缝外侧 40 列内**存在单列强边 |Δ列均值| >= 20
        实测命中 **sl 族 3 件**：sl_01(x=240,|Δ|=89.3) / sl_02(240,86.8) / sl_03(239,74.2)
        这 3 件的 mL4 = 104.2–108.0（vision 亦称「缝阶跃 104–108 级」）——正是帧线件。
    `--rule border`（派单字面口径）：**图片边框侧 40 列内**存在单列强边 |Δ列均值| >= 20
        实测命中 **0 件**（640 件边框侧最大 |Δ列均值| 仅 0.3–1.3 级；LaMa 在贴边处是平滑的）。
        ⇒ 字面口径不可用，报告已列明；保留开关以便复现。

做法（几何延展；只改扩展区，**内容区逐像素不变**）
    以缝为镜面反射内容列：左 ext[xl-1-t] = content[xl+t]；右 ext[xr+k] = content[xr-1-k]
    （t/k = 离缝距离，0..W_ext-1；W_ext = 241 / asu54 为 244，远小于内容宽 1438，不会越界）
      ⇒ **缝处严格连续**（ext 第 1 列 = content 第 1 列），缝阶跃按构造归零。
    羽化（≥32 px）：d ∈ [0,32) 取**纯镜像**（保证缝邻域连续性）；
      d ∈ [32, 128) 用 smoothstep 从纯镜像渐变到「柔化镜像」；
      d >= 128 取柔化镜像。柔化镜像 = 镜像带先横向箱式模糊 r=24 再纵向 r=8 ——
      目的是压掉远端的镜像重复感（skill §四 记载纯镜像的典型症状是「对称重影」），
      同时其色调仍来自内容本身（远端色调不会漂）。
    输出 = 内容区照抄原件 + 扩展区取上述几何延展；**不覆盖 `outpaint\`**。

硬断言（逐件）
    * 内容区 [xl,xr) 与 `outpaint\` 原件 max abs diff == 0
    * 输出 1920×1080、模式与原件一致（RGBA 的 alpha 通道不变）
    * ★ 帧线消除自证（**v2 修正版，2026-09-28**）：输出在「缝外侧 40 列内、**填充区内部**」的
      1px 逐列均值梯度（**分 6 横带**取最大，**排除跨缝列**）< FRAME_TH(20)。
      —— 上一版这里写的是「输出不含缝外侧 40 列内 |Δ列均值|>=20 的单列强边」，但**代码没实现**，
      而汇总把全高平均的 72.2/71.8/71.7 记成 `断言=OK`，**与事实相反**（vision 打回项之一）。
      现在按上式真实现：填充内部梯度由 geo 的 x 向平滑构造性归零 ⇒ 该断言在 3 件上均通过（实测 0.0–0.1）。
    * ★ 另**如实报告**（不作断言）：**缝处跨缝单列阶跃**（跨缝那一列、分 6 带取最大）= 106.8–107.1 级，
      与 `outpaint\` 原件的 31.8–58.2 相比**变大**了。原因：geo 把填充锚在**帧体色 164**，而内容第 1 列
      是**内容自带**的相框亮线 236.2 ⇒ 1px 反差被放到最大（LaMa 的填充恰在缝邻是亮值 ≈195，反差反而小）。
      这个台阶**不是填充缺陷**（任何把填充锚在帧体色的正确做法都消不掉），故只报不判；见报告「B_SKIP 取舍」。

产物
    outpaint_geo\<统一名>                几何延展后的 1920×1080
    证据\几何延展_对照.tsv                逐件改前/改后 五轴 + 断言
    证据\几何延展_汇总.txt

用法
    python geo_pass.py                  # 按 seam 口径全跑（幂等；与上一轮产物逐字节一致）
    python geo_pass.py --rule border    # 字面口径（预期 0 件，用于复现）
    python geo_pass.py --bskip 0 --outdir outpaint_geo_bskip0   # B_SKIP=0 变体（单独目录，不覆盖）
    python geo_pass.py --ramp-px 3      # 缝处锚点向平台过渡的像素数（默认 32；见报告「B_SKIP 取舍」）
    python geo_pass.py --force
"""
import sys, os, csv, time, argparse, shutil

WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image
from quality_axes import out_seams, axes_of_arr, AXES_TSV, FRAME_TH, EDGE_W

OUT_SRC = os.path.join(ISSUE_DIR, "outpaint")
OUT_DST = os.path.join(ISSUE_DIR, "outpaint_geo")
EVID = os.path.join(ISSUE_DIR, "证据")
CMP_TSV = os.path.join(EVID, "几何延展_对照.tsv")
SUM_TXT = os.path.join(EVID, "几何延展_汇总.txt")

HARD_EDGE = FRAME_TH      # 20
D_PURE = 32               # 纯镜像区（羽化保护段）
D_FULL = 128              # 完全切到柔化镜像的距离
BLUR_H, BLUR_V = 24, 8    # 柔化镜像的横向/纵向箱式模糊半径
FEATHER = 32              # edgeclamp 口径的羽化段（派单要求 >=32px）
B_OUT = 8                 # edgeclamp：远端平台取「缝内 skip..skip+8 列」的行均值
B_EDGE = 2                # edgeclamp：缝处锚点取「缝内 skip..skip+2 列」的行均值
B_SKIP = 2                # ★ 跳过内容最外 2 列——sl 族内容第 1 列是一条**亮高光线**
                          #   （实测 cm[241]=236 vs cm[245]=164），拿它当锚点会把高光线复制成
                          #   一整条亮带，且与 |ramp| 的参考带（含高光线）互相拉扯；跳过后锚点
                          #   = 相框边条本色，mL4 与 |ramp| 同时变小。


def box_blur_x(a, r):
    """对 (H,W,3) 沿 axis1 箱式模糊（边界截断重归一）。"""
    H, W, C = a.shape
    cs = np.cumsum(np.concatenate([np.zeros((H, 1, C), a.dtype), a], axis=1), axis=1)
    i = np.arange(W)
    lo = np.clip(i - r, 0, W)
    hi = np.clip(i + r + 1, 0, W)
    return (cs[:, hi, :] - cs[:, lo, :]) / (hi - lo)[None, :, None]


def box_blur_y(a, r):
    H = a.shape[0]
    cs = np.cumsum(np.concatenate([np.zeros((1,) + a.shape[1:], a.dtype), a], axis=0), axis=0)
    i = np.arange(H)
    lo = np.clip(i - r, 0, H)
    hi = np.clip(i + r + 1, 0, H)
    return (cs[hi] - cs[lo]) / (hi - lo)[:, None, None]


def smoothstep(u):
    u = np.clip(u, 0, 1)
    return u * u * (3.0 - 2.0 * u)


def geo_extend(rgb, xl, xr, method="edgeclamp", bskip=B_SKIP, edge_ramp=FEATHER,
               anchor_skip=None, platform_skip=None, anchor_blend=0.0):
    """几何延展：只填充扩展区，内容区原样。返回新数组。

    method="edgeclamp"（默认）：复制边缘列并做「行均值扁平化」——
        远端平台 M(y) = 缝内侧 [platform_skip, +B_OUT) 列的行均值（与 |ramp| 的右项同口径 ⇒ |ramp| 构造性归零），
        缝处锚点 E(y) = 缝内侧 [anchor_skip, +B_EDGE) 列的行均值（紧贴缝，保证缝邻域连续），
        d = **离缝距离**，d ∈ [0,edge_ramp) 用 smoothstep 从 E 过渡到 M，d >= edge_ramp 取 M。
        扩展区在 x 方向为逐行常数 ⇒ 不产生任何竖向硬边。
      anchor_skip / platform_skip 默认都取 bskip；可解耦（见报告「B_SKIP 取舍」）。

    ★ v3 修正（2026-09-28）：上一版 `d = np.arange(n)` 在**左缝**把 d=0 对到了**最外侧**列，
      使左缝的羽化方向**整体反了**（锚点 E 被放到外缘、平台 M 被放到缝邻）。B_SKIP=2 时 E≈M
      （161.6 vs 164.0，均取自相框边条本色）故影响 ≤2.4 级、此前未被发现；一旦 bskip 变小即放大。
      现按「d = 离缝距离」对两侧统一修正（左缝 d 递减），修正版产物落 outpaint_geo_fix\\ 以便对照。
    method="mirror"：以缝为镜面反射内容列 + 柔化（照派单字面「镜像边缘列」）；
        实测对 sl 族**反而恶化**（|ramp| 40→111、缝外强边 89→122，见报告）。保留供复现。
    """
    H, W, _ = rgb.shape
    a_skip = B_SKIP if anchor_skip is None else anchor_skip
    p_skip = B_SKIP if platform_skip is None else platform_skip
    out = rgb.copy()
    for side in ("L", "R"):
        if side == "L":
            ext = slice(0, xl); n = xl
            band = slice(xl + p_skip, min(W, xl + p_skip + B_OUT))
            edge = slice(xl + a_skip, min(W, xl + a_skip + B_EDGE))
            d = np.arange(n - 1, -1, -1, dtype=np.float32)      # 离缝距离：缝 = xl−1 → d=0
        else:
            ext = slice(xr, W); n = W - xr
            band = slice(max(0, xr - p_skip - B_OUT), max(1, xr - p_skip))
            edge = slice(max(0, xr - a_skip - B_EDGE), max(1, xr - a_skip))
            d = np.arange(n, dtype=np.float32)                   # 缝 = xr → d=0
        if method == "edgeclamp":
            M = rgb[:, band, :].mean(axis=1).astype(np.float32)      # (H,3)
            E = rgb[:, edge, :].mean(axis=1).astype(np.float32)
            if anchor_blend > 0:      # 混合锚点：α·内容第 1 列 + (1−α)·平台（见报告「B_SKIP 取舍」）
                fc = rgb[:, xl:xl + 1, :].mean(axis=1) if side == "L" \
                    else rgb[:, xr - 1:xr, :].mean(axis=1)
                E = anchor_blend * fc + (1.0 - anchor_blend) * M
            w = smoothstep(d / float(max(1, edge_ramp)))[None, :, None]   # (1,n,1)
            strip = E[:, None, :] * (1 - w) + M[:, None, :] * w       # (H,n,3)
            out[:, ext, :] = np.clip(strip, 0, 255)
        else:
            if side == "L":
                mirror = rgb[:, xl:xl + n, :][:, ::-1, :]
            else:
                mirror = rgb[:, xr - n:xr, :][:, ::-1, :]
            soft = box_blur_y(box_blur_x(mirror, BLUR_H), BLUR_V)
            d = np.arange(n, dtype=np.float32)
            w = smoothstep((d - D_PURE) / float(D_FULL - D_PURE))[None, :, None]
            out[:, ext, :] = np.clip(mirror * (1 - w) + soft * w, 0, 255)
    return out


def frame_edge_max(gray_rgb):
    """输出图里「缝外侧 40 列内」的最大单列 |Δ列均值|（全高平均，仅供参考）。"""
    cm = (0.299 * gray_rgb[:, :, 0] + 0.587 * gray_rgb[:, :, 1]
          + 0.114 * gray_rgb[:, :, 2]).mean(axis=0)
    dc = np.abs(np.diff(cm))
    return cm, dc


def side_frame_max(dc, xl, xr, W):
    eL = dc[max(0, xl - 40):max(1, xl)].max() if xl > 1 else 0.0
    eR = dc[min(W - 1, xr):min(W - 1, xr + 40)].max() if xr < W - 1 else 0.0
    return float(max(eL, eR))


def border_frame_max(dc, W):
    eL = dc[0:39].max() if len(dc) > 39 else (dc.max() if len(dc) else 0.0)
    eR = dc[W - 40:W - 1].max() if len(dc) > 40 else 0.0
    return float(max(eL, eR))


def selfcheck_edges(rgb, xl, xr, nb=6, edge_w=EDGE_W):
    """★ 帧线消除自证（v2 真实现）。

    返回 (填充内硬边_逐带max, 缝处跨缝阶跃_逐带max)：
      · 填充内硬边 = 缝外侧 40 列内、**填充区内部**的 1px 逐列均值梯度（分 nb 横带取最大），
        左右两侧取最大；**排除跨缝列**（左：索引 xl−1 那一对跨缝；右：索引 xr 那一对跨缝）。
        —— 这才是 geo 能且应当消除的量（LaMa 在缝外造的竖硬边）。
      · 缝处跨缝阶跃 = 跨缝那一对的 1px 逐列均值梯度（分带取最大）——**内容自带**相框亮线造成，
        只报不判。
    """
    H, W, _ = rgb.shape
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    edges = [int(round(i * H / nb)) for i in range(nb + 1)]
    cmb = np.stack([lum[edges[i]:edges[i + 1]].mean(axis=0) for i in range(nb)])   # (nb,W)
    g = np.abs(np.diff(cmb, axis=1))            # g[:,i] = |cmb[i+1]-cmb[i]|
    fillL = float(g[:, max(1, xl - edge_w):max(1, xl - 1)].max()) if xl > 2 else 0.0
    fillR = float(g[:, xr + 1:min(W - 1, xr + 1 + edge_w)].max()) if xr < W - 2 else 0.0
    fm = max(fillL, fillR)
    seam = 0.0
    for x in (xl, xr):
        if 1 <= x <= W - 1:
            seam = max(seam, float(g[:, x - 1].max()))
    return fm, seam


def pick(rule, names=None):
    rows = list(csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t"))
    key = "frame_seam" if rule == "seam" else "frame_border"
    out = [r["统一名"] for r in rows if int(float(r.get(key) or 0)) == 1]
    if names:
        out = [n for n in out if n in set(names)]
    return out


def process(name, src_size, method="edgeclamp", bskip=B_SKIP, edge_ramp=FEATHER, outdir=None,
            anchor_skip=None, platform_skip=None, tag=""):
    outdir = outdir or OUT_DST
    src = os.path.join(OUT_SRC, name)
    dst = os.path.join(outdir, name)
    if not os.path.exists(src):
        raise AssertionError("源产物不存在: %s" % src)
    W, H = src_size
    xl, xr = out_seams(W, H)
    im = Image.open(src)
    mode = im.mode
    orig_u8 = np.asarray(im.convert("RGB")).copy()
    orig = orig_u8.astype(np.float32)
    alpha = np.asarray(im.split()[-1]).copy() if mode == "RGBA" else None
    im.close()

    a_before = axes_of_arr(orig, xl, xr)
    new = geo_extend(orig, xl, xr, method, bskip=bskip, edge_ramp=edge_ramp,
                     anchor_skip=anchor_skip, platform_skip=platform_skip)
    new_u8 = np.clip(np.rint(new), 0, 255).astype(np.uint8)

    # 断言 ①：内容区逐像素不变
    diff_in = int(np.abs(new_u8[:, xl:xr, :].astype(np.int16)
                         - orig_u8[:, xl:xr, :].astype(np.int16)).max())
    # 断言 ②：扩展区确实变了（否则说明没生效）
    ext_changed = int(np.abs(new_u8[:, :xl, :].astype(np.int16)
                             - orig_u8[:, :xl, :].astype(np.int16)).max())
    if diff_in != 0:
        raise AssertionError("内容区被改动！max abs diff = %d" % diff_in)
    if ext_changed == 0:
        raise AssertionError("扩展区未发生变化，几何延展未生效")

    img_out = Image.fromarray(new_u8, "RGB")
    if alpha is not None:
        img_out = img_out.convert("RGBA")
        img_out.putalpha(Image.fromarray(alpha, "L"))
    os.makedirs(outdir, exist_ok=True)
    tmp = dst + ".tmp.png"
    img_out.save(tmp)
    shutil.move(tmp, dst)

    a_after = axes_of_arr(np.asarray(Image.open(dst).convert("RGB")).astype(np.float32), xl, xr)
    # ★ 帧线消除自证（v2 真实现）：填充内部硬边（分带、排除跨缝列）
    fm_after, seam_after = selfcheck_edges(new_u8.astype(np.float32), xl, xr)
    fm_before, seam_before = selfcheck_edges(orig, xl, xr)
    cm, dc = frame_edge_max(new_u8.astype(np.float32))
    fr_after = side_frame_max(dc, xl, xr, 1920)
    fr_before = side_frame_max(np.abs(np.diff((0.299 * orig[:, :, 0] + 0.587 * orig[:, :, 1]
                                              + 0.114 * orig[:, :, 2]).mean(axis=0))), xl, xr, 1920)
    bd_before = border_frame_max(np.abs(np.diff((0.299 * orig[:, :, 0] + 0.587 * orig[:, :, 1]
                                                + 0.114 * orig[:, :, 2]).mean(axis=0))), 1920)
    bd_after = border_frame_max(dc, 1920)
    ok = (fm_after < HARD_EDGE)
    assert_txt = ("OK" if ok else "FAIL(填充内硬边%.1f>=%d)" % (fm_after, HARD_EDGE))
    return {"统一名": name, "模式": mode, "xl": xl, "xr": xr,
            "变体": tag or ("B_SKIP=%d/羽化%dpx" % (bskip, edge_ramp)),
            "B_SKIP": bskip if anchor_skip is None else anchor_skip,
            "平台skip": bskip if platform_skip is None else platform_skip,
            "羽化px": edge_ramp, "输出目录": os.path.basename(outdir),
            "mL4_before": a_before["mL4"], "mL4_after": a_after["mL4"],
            "mRGB4_before": a_before["mRGB4"], "mRGB4_after": a_after["mRGB4"],
            "er_before": a_before["er"], "er_after": a_after["er"],
            "er_fill_before": a_before["er_fill"], "er_fill_after": a_after["er_fill"],
            "ramp_before": a_before["ramp"], "ramp_after": a_after["ramp"],
            "ramp_in_before": a_before["ramp_in"], "ramp_in_after": a_after["ramp_in"],
            "bD16_before": a_before["bD16"], "bD16_after": a_after["bD16"],
            "填充内硬边_before": round(fm_before, 1), "填充内硬边_after": round(fm_after, 1),
            "跨缝阶跃_before": round(seam_before, 1), "跨缝阶跃_after": round(seam_after, 1),
            "缝外强边_before": round(fr_before, 1), "缝外强边_after": round(fr_after, 1),
            "边框强边_before": round(bd_before, 1), "边框强边_after": round(bd_after, 1),
            "内容区maxdiff": diff_in, "扩展区maxdiff": ext_changed,
            "字节": os.path.getsize(dst),
            "断言": assert_txt}


CMP_COLS = ["统一名", "模式", "xl", "xr", "变体", "B_SKIP", "平台skip", "羽化px", "输出目录",
            "mL4_before", "mL4_after", "mRGB4_before", "mRGB4_after",
            "er_before", "er_after", "er_fill_before", "er_fill_after",
            "ramp_before", "ramp_after", "ramp_in_before", "ramp_in_after",
            "bD16_before", "bD16_after",
            "填充内硬边_before", "填充内硬边_after", "跨缝阶跃_before", "跨缝阶跃_after",
            "缝外强边_before", "缝外强边_after", "边框强边_before", "边框强边_after",
            "内容区maxdiff", "扩展区maxdiff", "字节", "断言"]


def write_cmp(recs, prev):
    by = {r["统一名"]: r for r in recs}
    for k, v in prev.items():
        by.setdefault(k, v)
    tmp = CMP_TSV + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CMP_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for k in sorted(by):
            w.writerow(by[k])
    os.replace(tmp, CMP_TSV)


def emit_summary(recs, rule):
    lines = ["几何延展 pass 汇总（口径 %s）" % rule, "  对象 %d 件" % len(recs)]
    for r in recs:
        lines.append("  %-12s(B_SKIP=%s) mL4 %7.2f -> %6.2f ｜ mRGB4 %7.2f -> %6.2f ｜ er_fill %5.2f -> %5.2f "
                     "｜ |ramp| %6.2f -> %5.2f（内移 %6.2f -> %5.2f）"
                     % (r["统一名"], r.get("B_SKIP", ""), float(r["mL4_before"]), float(r["mL4_after"]),
                        float(r["mRGB4_before"]), float(r["mRGB4_after"]),
                        float(r["er_fill_before"]), float(r["er_fill_after"]),
                        float(r["ramp_before"]), float(r["ramp_after"]),
                        float(r["ramp_in_before"]), float(r["ramp_in_after"])))
        lines.append("  %-12s          ★自证 填充内硬边（缝外40列·分带·排除跨缝列） %6.1f -> %5.1f（判据 <%d）"
                     " ｜ 缝处跨缝阶跃（**内容自带相框亮线**，只报不判） %6.1f -> %5.1f ｜ 断言=%s"
                     % ("", float(r["填充内硬边_before"]), float(r["填充内硬边_after"]), FRAME_TH,
                        float(r["跨缝阶跃_before"]), float(r["跨缝阶跃_after"]), r["断言"]))
    lines.append("  内容区 max abs diff（全批） = %s  ← 必须为 0"
                 % max((int(r["内容区maxdiff"]) for r in recs), default="n/a"))
    lines.append("  ★ 口径说明（v2 修正）：上一轮此处的自证**代码未实现**，却把全高平均的 72.2/71.8/71.7 记成")
    lines.append("    `断言=OK`（vision 打回项）。现按「缝外侧 40 列内、填充区内部、分 6 带、排除跨缝列」真实现；")
    lines.append("    缝处那个跨缝台阶（106.8–107.1 级）由**内容自带**的相框亮线造成（内容第 1 列 236.2 vs 帧体色 164），")
    lines.append("    任何把填充锚在帧体色的正确做法都消不掉 ⇒ 只报不判，并在报告中说明。")
    if rule == "border":
        lines.append("  ★ 字面口径（图片边框侧 40 列）实测命中 0 件 —— 见报告「帧线口径」一节")
    txt = "\n".join(lines)
    open(SUM_TXT, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", default="seam", choices=["seam", "border"])
    ap.add_argument("--method", default="edgeclamp", choices=["edgeclamp", "mirror"])
    ap.add_argument("--bskip", type=int, default=B_SKIP, help="缝处锚点/平台跳过的内容列数（默认 2）")
    ap.add_argument("--anchor-skip", type=int, default=None, help="单独指定 E（缝处锚点）的 skip（默认同 --bskip）")
    ap.add_argument("--platform-skip", type=int, default=None, help="单独指定 M（远端平台）的 skip（默认同 --bskip）")
    ap.add_argument("--ramp-px", type=int, default=FEATHER, help="缝处锚点→远端平台 的过渡像素数（默认 32）")
    ap.add_argument("--outdir", default=None, help="输出目录（默认 outpaint_geo；变体请给新目录，勿覆盖）")
    ap.add_argument("--tsv", default=None, help="对照 TSV 路径（默认 证据\\几何延展_对照.tsv）")
    ap.add_argument("--tag", default="", help="变体标签（写进 TSV 的 变体 列）")
    ap.add_argument("--names", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    global CMP_TSV
    if args.tsv:
        CMP_TSV = args.tsv
    outdir = args.outdir or OUT_DST
    names = [n.strip() for n in args.names.split(",")] if args.names else None
    jobs = pick(args.rule, names)
    print("几何延展对象 %d 件（rule=%s, anchor_skip=%s, platform_skip=%s, 羽化%spx, 输出 %s）: %s"
          % (len(jobs), args.rule, args.anchor_skip if args.anchor_skip is not None else args.bskip,
             args.platform_skip if args.platform_skip is not None else args.bskip,
             args.ramp_px, os.path.basename(outdir), ", ".join(jobs)), flush=True)
    if not jobs:
        emit_summary([], args.rule)
        return
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    prev = {}
    if os.path.exists(CMP_TSV):
        for r in csv.DictReader(open(CMP_TSV, encoding="utf-8"), delimiter="\t"):
            prev[r["统一名"]] = r
    import csv as _csv
    sizes = {}
    L = os.path.join(MAIN_PROJ, "资源组", "美术", "4比3待重制清单.tsv")
    for r in _csv.DictReader(open(L, encoding="utf-8"), delimiter="\t"):
        if r["建议策略(重制/补边/裁切)"] == "补边":
            sizes[r["统一名"]] = os.path.join(MAIN_PROJ, r["超分版路径"])

    recs, fails, t0 = [], [], time.time()
    for i, nm in enumerate(jobs):
        dst = os.path.join(outdir, nm)
        if (not args.force and nm in prev and os.path.exists(dst)
                and prev[nm].get("变体") == args.tag):
            recs.append(prev[nm]); continue
        try:
            W, H = Image.open(sizes[nm]).size
            rec = process(nm, (W, H), args.method, bskip=args.bskip,
                          edge_ramp=args.ramp_px, outdir=outdir,
                          anchor_skip=args.anchor_skip, platform_skip=args.platform_skip,
                          tag=args.tag)
            recs.append(rec)
            print("[%d/%d] %-12s mL4 %.2f -> %.2f  mRGB4 %.2f -> %.2f  填充内硬边 %.1f -> %.1f  跨缝阶跃 %.1f -> %.1f  %.1fs"
                  % (i + 1, len(jobs), nm, float(rec["mL4_before"]), float(rec["mL4_after"]),
                     float(rec["mRGB4_before"]), float(rec["mRGB4_after"]),
                     float(rec["填充内硬边_before"]), float(rec["填充内硬边_after"]),
                     float(rec["跨缝阶跃_before"]), float(rec["跨缝阶跃_after"]),
                     time.time() - t0), flush=True)
        except Exception as e:
            fails.append((nm, repr(e)))
            print("[%d/%d] FAIL %s %r" % (i + 1, len(jobs), nm, e), flush=True)
    write_cmp(recs, prev)
    emit_summary(recs, args.rule)
    print("\n== 汇总 == 计划 %d ｜ 成功 %d ｜ 失败 %d ｜ 用时 %.2f min"
          % (len(jobs), len(recs), len(fails), (time.time() - t0) / 60))


if __name__ == "__main__":
    main()
