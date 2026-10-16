# -*- coding: utf-8 -*-
r"""
tonematch_pass.py —— 扩展区色调对齐（ISSUE-20260928-02 · 1028 补边续作 · 交付物 3）

对象
    补边输出中「扩展区与内容区整体色调不一致」的件：|ramp| >= 25（派单触发线，272 件）
    **外加整个 sr 族**（81 件白底片尾卡）——派单点名 sr 族「否则全屏边缘露 12–35 级灰晕」，
    但实测 sr 族的 |ramp| 只有 10.8–26.5（p50 20.7），按 25 的线只能召回 4/81；
    而 sr 族 81 件的缝本身是**完美**的（mL4 max 0.52 / mRGB4 max 1.35 / bD16 max 3.28），
    唯一的缺陷就是这条色调漂移 ⇒ 用 --include-sr 把整族纳入（默认开）。

做法（只改扩展区，**内容区逐像素不变**）
    逐侧看三条统计带：
        缝外远带  ext_far = mean_cols(图片最外 8 列)      （逐行 y、逐通道 c）
        内容参考  ctn_ref = mean_cols(缝内侧 8 列)        （**与 |ramp| 的右项同口径**）
    偏移斜坡  off(y) = ctn_ref(y) − ext_far(y)   → 夹在 ±80 → 沿 y 箱式平滑(半径 16)
    沿 x 的距离权重 u = smoothstep(d / (W_ext−1))，d = 离缝距离（缝处 0、最外列 W_ext−1）
    输出 = clip(原值 + u(y 无关) ⊗ off(y,c))      ⇒ **缝处 u=0 ⇒ 缝邻域逐位不变**
    残差归零：量化/夹紧/平滑后若最外 8 列灰度均值仍有差，补一个 u 加权的灰色偏置（三通道同量，
    不引入色偏），把 |ramp| 精确压到 ≈0。
    ⇒ 外缘与内容同色调（|ramp|→0）、缝邻域零改动（mL4/mRGB4 逐位不变）、羽化 241 px ≫ 32 px。

★ gain 为何关掉（`--gain` 可开，默认关；**这是对派单「gain/offset 校正」的一处偏离，附证据**）
    实测两种 gain 都病态：① std 比值（缝外 std / 内容 std）对 640 件**几乎全部顶到夹紧边界**
    （同一件同时出现 0.906 与 1.111）——伪信号；② 换成「缝外远带逐行剖面 → 内容参考带逐行剖面」
    的最小二乘斜率，`kob64` 三通道同顶下界 0.9，使 raw offset 达 81 级、**1756 个元素被 ±80 夹掉**，
    外缘只从 164.4 补到 189.5（目标 206.1），残留 |ramp| = 16.6 级。
    关掉 gain（g≡1）后锚点代数精确 ⇒ |ramp| 落到 0.15–4.6 级。故本轮以**纯 offset 斜坡 + 残差归零**
    实现，gain 仅作开关保留。

硬断言（逐件）
    * 内容区 [xl,xr) 与 `outpaint\` 原件 **max abs diff == 0**（逐像素、逐通道）
    * 输出尺寸 1920×1080、模式与原件一致（RGBA 件的 alpha 通道不变）
    * 改后 |ramp| < 改前 |ramp|（否则记 WARN 并保留）
    * **不覆盖 `outpaint\`**：只读、只写 `outpaint_tonematch\`

产物
    outpaint_tonematch\<统一名>            色调对齐后的 1920×1080（不覆盖 outpaint\）
    证据\色调匹配_对照.tsv                 逐件改前/改后 |ramp| / mL4 / mRGB4 / bD16 + 断言结果
    证据\色调匹配_汇总.txt                 含 81 件 sr 族分组汇总

用法
    python tonematch_pass.py                       # 全量（幂等跳过已完成）
    python tonematch_pass.py --names a.png,b.png
    python tonematch_pass.py --ramp-min 25 --no-sr # 严格按派单（只 272 件）
    python tonematch_pass.py --force               # 重算覆盖
    python tonematch_pass.py --limit 5             # 试跑
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
from quality_axes import (out_seams, axes_of_arr, load_rgb, AXES_TSV,
                          TONEMATCH_RAMP, TARGET)

OUT_SRC = os.path.join(ISSUE_DIR, "outpaint")
OUT_DST = os.path.join(ISSUE_DIR, "outpaint_tonematch")
EVID = os.path.join(ISSUE_DIR, "证据")
CMP_TSV = os.path.join(EVID, "色调匹配_对照.tsv")
SUM_TXT = os.path.join(EVID, "色调匹配_汇总.txt")

NEAR, FAR, REF = 8, 8, 8        # 缝外近带 8 列 / 缝外远带 8 列 / 内容参考 8 列
                                # REF=8 与 |ramp| 的「缝内 8 列」口径一致 ⇒ 校正后 |ramp|→≈0
GAIN_LO, GAIN_HI = 0.90, 1.111
SMOOTH_R = 16                  # 沿 y 箱式平滑半径
OFF_CLAMP = 80.0               # 偏移绝对值上限（灰度级）


def box_smooth_cols(a, r):
    """对 (H,3) 沿 axis0 做半径 r 的箱式平滑（边缘用 'same' 方式重归一）。"""
    H = a.shape[0]
    if r <= 0:
        return a
    cs = np.cumsum(np.vstack([np.zeros((1, a.shape[1]), a.dtype), a]), axis=0)
    idx = np.arange(H)
    lo = np.clip(idx - r, 0, H)
    hi = np.clip(idx + r + 1, 0, H)
    return (cs[hi] - cs[lo]) / (hi - lo)[:, None]


def smoothstep(u):
    return u * u * (3.0 - 2.0 * u)


def _luma(a):
    return 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]


def tonematch(rgb, xl, xr, use_gain=False):
    """rgb (1080,1920,3) float32。返回 (新数组, info)。
    内容区逐像素**照抄原值**（校正场在缝处严格为 0，u(0)=0）。"""
    H, W, _ = rgb.shape
    out = rgb.copy()
    info = {}
    for side in ("L", "R"):
        if side == "L":
            ext = slice(0, xl)
            far = slice(0, FAR)
            ref = slice(xl, min(W, xl + REF))
            width = xl
        else:
            ext = slice(xr, W)
            far = slice(max(0, W - FAR), W)
            ref = slice(max(0, xr - REF), xr)
            width = W - xr
        n_ext = ext.stop - ext.start
        if n_ext < 8:
            continue
        ext_far = rgb[:, far, :].mean(axis=1).astype(np.float32)      # (H,3)
        ctn_ref = rgb[:, ref, :].mean(axis=1).astype(np.float32)

        # gain（默认关，见文件头「gain 为何关掉」）：把缝外远带的逐行剖面线性映射到内容参考带
        g = np.ones(3, dtype=np.float32)
        if use_gain:
            for c in range(3):
                xs, ys = ext_far[:, c], ctn_ref[:, c]
                vx = float(xs.var())
                if xs.std() >= 2.0 and vx > 1e-3:
                    g[c] = np.clip(float(((xs - xs.mean()) * (ys - ys.mean())).mean() / vx),
                                   GAIN_LO, GAIN_HI)

        off_far = np.clip(ctn_ref - ext_far * g, -OFF_CLAMP, OFF_CLAMP)
        off_far = box_smooth_cols(off_far, SMOOTH_R)

        # 校正场：缝处 u=0（严格不动缝邻域 ⇒ mL4/mRGB4 逐位不变），最外列 u=1
        t = np.arange(n_ext, dtype=np.float32)
        d = (n_ext - 1 - t) if side == "L" else t
        u = smoothstep(np.clip(d / max(n_ext - 1, 1), 0, 1))[None, :, None]   # (1,n_ext,1)
        gv = 1.0 + u * (g[None, None, :] - 1.0)
        out[:, ext, :] = np.clip(rgb[:, ext, :] * gv + u * off_far[:, None, :], 0, 255)

        # ★ 残差归零：clamp / 平滑 / 量化都可能让最外 8 列的灰度均值差一点，
        #   这里按「目标 = 内容参考带灰度均值（即 |ramp| 的右侧项）」补一个 u 加权的灰色偏置，
        #   把 |ramp| 精确压到 ~0（同时不引入色偏：三通道同量）。
        tgt = float(_luma(rgb[:, ref, :]).mean())
        cur = float(_luma(out[:, far, :]).mean())
        resid = tgt - cur
        if abs(resid) > 1e-6:
            out[:, ext, :] = np.clip(out[:, ext, :] + u * resid, 0, 255)
        info[side] = {"gain": [round(float(v), 4) for v in g],
                      "off_far_mean": round(float(np.abs(off_far).mean()), 3),
                      "resid_before": round(cur - tgt, 3)}
    return out, info


def process(name, src_size, use_gain=False):
    src = os.path.join(OUT_SRC, name)
    dst = os.path.join(OUT_DST, name)
    if not os.path.exists(src):
        raise AssertionError("源产物不存在: %s" % src)
    W, H = src_size
    xl, xr = out_seams(W, H)
    im = Image.open(src)
    mode = im.mode
    orig_u8 = np.asarray(im.convert("RGB")).copy()
    orig_rgb = orig_u8.astype(np.float32)
    alpha = np.asarray(im.split()[-1]).copy() if mode == "RGBA" else None
    im.close()

    a_before = axes_of_arr(orig_rgb, xl, xr)
    new_rgb, info = tonematch(orig_rgb, xl, xr, use_gain=use_gain)

    # ① 硬断言：内容区逐像素不变
    content_before = orig_u8[:, xl:xr, :]
    new_u8 = np.clip(np.rint(new_rgb), 0, 255).astype(np.uint8)
    content_after = new_u8[:, xl:xr, :]
    diff = int(np.abs(content_after.astype(np.int16) - content_before.astype(np.int16)).max())
    if diff != 0:
        raise AssertionError("内容区被改动！max abs diff = %d（必须为 0）" % diff)

    # ② 写盘（RGBA 保留原 alpha）
    img_out = Image.fromarray(new_u8, "RGB")
    if alpha is not None:
        img_out = img_out.convert("RGBA")
        img_out.putalpha(Image.fromarray(alpha, "L"))
    os.makedirs(OUT_DST, exist_ok=True)
    tmp = dst + ".tmp.png"
    img_out.save(tmp)
    shutil.move(tmp, dst)

    # ③ 改后指标
    a_after = axes_of_arr(np.asarray(Image.open(dst).convert("RGB")).astype(np.float32), xl, xr)
    ok_ramp = a_after["ramp"] < a_before["ramp"]
    return {"统一名": name, "模式": mode, "xl": xl, "xr": xr,
            "ramp_before": a_before["ramp"], "ramp_after": a_after["ramp"],
            "mL4_before": a_before["mL4"], "mL4_after": a_after["mL4"],
            "mRGB4_before": a_before["mRGB4"], "mRGB4_after": a_after["mRGB4"],
            "bD16_before": a_before["bD16"], "bD16_after": a_after["bD16"],
            "er_before": a_before["er"], "er_after": a_after["er"],
            "gain_L": info.get("L", {}).get("gain", ""), "gain_R": info.get("R", {}).get("gain", ""),
            "off_far_L": info.get("L", {}).get("off_far_mean", ""),
            "off_far_R": info.get("R", {}).get("off_far_mean", ""),
            "内容区maxdiff": diff, "字节": os.path.getsize(dst),
            "断言": "OK" if ok_ramp else "WARN(ramp未降)"}


CMP_COLS = ["统一名", "模式", "xl", "xr", "ramp_before", "ramp_after",
            "mL4_before", "mL4_after", "mRGB4_before", "mRGB4_after",
            "bD16_before", "bD16_after", "er_before", "er_after",
            "gain_L", "gain_R", "off_far_L", "off_far_R",
            "内容区maxdiff", "字节", "断言"]

SRC_SIZE_CACHE = None


def src_sizes():
    global SRC_SIZE_CACHE
    if SRC_SIZE_CACHE is None:
        import csv as _csv
        SRC_SIZE_CACHE = {}
        L = os.path.join(MAIN_PROJ, "资源组", "美术", "4比3待重制清单.tsv")
        for r in _csv.DictReader(open(L, encoding="utf-8"), delimiter="\t"):
            if r["建议策略(重制/补边/裁切)"] == "补边":
                SRC_SIZE_CACHE[r["统一名"]] = os.path.join(MAIN_PROJ, r["超分版路径"])
    return SRC_SIZE_CACHE


def pick(ramp_min, include_sr, names=None):
    rows = list(csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t"))
    out = []
    for r in rows:
        ramp = float(r["ramp"] or 0)
        take = ramp >= ramp_min
        if include_sr and r["统一名"].startswith("sr"):
            take = True
        if take:
            out.append(r["统一名"])
    if names:
        out = [n for n in out if n in set(names)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ramp-min", type=float, default=TONEMATCH_RAMP)
    ap.add_argument("--include-sr", dest="include_sr", action="store_true", default=True)
    ap.add_argument("--no-sr", dest="include_sr", action="store_false")
    ap.add_argument("--names", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--gain", action="store_true", help="开 gain 段（默认关，见文件头）")
    args = ap.parse_args()

    names = [n.strip() for n in args.names.split(",")] if args.names else None
    jobs = pick(args.ramp_min, args.include_sr, names)
    if args.limit:
        jobs = jobs[:args.limit]
    sizes = src_sizes()
    print("色调匹配对象 %d 件（ramp>=%.0f%s%s）"
          % (len(jobs), args.ramp_min, " + 全部 sr 族" if args.include_sr else "",
             "，指定 --names" if names else ""), flush=True)

    os.makedirs(OUT_DST, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    prev = {}
    if os.path.exists(CMP_TSV):
        for r in csv.DictReader(open(CMP_TSV, encoding="utf-8"), delimiter="\t"):
            prev[r["统一名"]] = r

    recs, fails, skip = [], [], 0
    t0 = time.time()
    for i, nm in enumerate(jobs):
        dst = os.path.join(OUT_DST, nm)
        if not args.force and nm in prev and os.path.exists(dst):
            recs.append(prev[nm]); skip += 1
            continue
        try:
            srcp = sizes.get(nm)
            if srcp is None or not os.path.exists(srcp):
                raise AssertionError("清单/源缺失: %s" % srcp)
            W, H = Image.open(srcp).size
            rec = process(nm, (W, H), use_gain=args.gain)
            recs.append(rec)
            print("[%3d/%3d] %-18s ramp %6.2f -> %5.2f  mL4 %6.2f -> %5.2f  "
                  "mRGB4 %6.2f -> %5.2f  内容区diff=%d  %s  %.1fs"
                  % (i + 1, len(jobs), nm, rec["ramp_before"], rec["ramp_after"],
                     rec["mL4_before"], rec["mL4_after"], rec["mRGB4_before"],
                     rec["mRGB4_after"], rec["内容区maxdiff"], rec["断言"],
                     time.time() - t0), flush=True)
        except Exception as e:
            fails.append({"统一名": nm, "错误": repr(e)})
            print("[%3d/%3d] FAIL %-18s %r" % (i + 1, len(jobs), nm, e), flush=True)
        if (i + 1) % 25 == 0:
            write_cmp(jobs, recs, prev)

    write_cmp(jobs, recs, prev)
    emit_summary(recs, fails, skip, jobs)
    print("\n== 汇总 == 计划 %d ｜ 新做 %d ｜ 跳过 %d ｜ 失败 %d ｜ 用时 %.1f min"
          % (len(jobs), len(recs) - skip, skip, len(fails), (time.time() - t0) / 60))


def write_cmp(jobs, recs, prev):
    by = {r["统一名"]: r for r in recs}
    for nm, r in prev.items():
        by.setdefault(nm, r)
    tmp = CMP_TSV + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CMP_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for nm in jobs:
            if nm in by:
                w.writerow(by[nm])
    os.replace(tmp, CMP_TSV)


def emit_summary(recs, fails, skip, jobs):
    if not recs:
        return
    def f(r, k):
        try:
            return float(r[k])
        except Exception:
            return float("nan")
    rb = [f(r, "ramp_before") for r in recs]
    ra = [f(r, "ramp_after") for r in recs]
    sr = [r for r in recs if r["统一名"].startswith("sr")]
    n_ok = sum(1 for r in recs if r["断言"].startswith("OK"))
    n_warn = sum(1 for r in recs if r["断言"].startswith("WARN"))
    md = max((int(r["内容区maxdiff"]) for r in recs), default=-1)
    lines = ["色调匹配 pass 汇总",
             "  对象 %d 件（计划 %d；失败 %d；复用已有 %d）" % (len(recs), len(jobs), len(fails), skip),
             "  |ramp| 改前 mean %.2f / max %.2f  ⇒  改后 mean %.2f / max %.2f"
             % (np.nanmean(rb), np.nanmax(rb), np.nanmean(ra), np.nanmax(ra)),
             "  |ramp| 下降件数 %d/%d（未下降 %d 件，见 断言 列 WARN）" % (n_ok, len(recs), n_warn),
             "  内容区逐像素 max abs diff（全批） = %d  ← 必须为 0" % md,
             "  mL4  改前 max %.2f ⇒ 改后 max %.2f" % (max(f(r, "mL4_before") for r in recs),
                                                       max(f(r, "mL4_after") for r in recs)),
             "  mRGB4 改前 max %.2f ⇒ 改后 max %.2f" % (max(f(r, "mRGB4_before") for r in recs),
                                                        max(f(r, "mRGB4_after") for r in recs))]
    if sr:
        srb = [f(r, "ramp_before") for r in sr]
        sra = [f(r, "ramp_after") for r in sr]
        lines += ["", "  【sr 族白底片尾卡 %d 件】" % len(sr),
                  "    |ramp| 改前 p50 %.2f / max %.2f ⇒ 改后 p50 %.2f / max %.2f"
                  % (float(np.percentile(srb, 50)), max(srb),
                     float(np.percentile(sra, 50)), max(sra)),
                  "    内容区 max abs diff = %d" % max(int(r["内容区maxdiff"]) for r in sr)]
    fails_txt = "" if not fails else "\n  失败件: " + ", ".join(x["统一名"] for x in fails)
    txt = "\n".join(lines) + fails_txt
    open(SUM_TXT, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)


if __name__ == "__main__":
    main()
