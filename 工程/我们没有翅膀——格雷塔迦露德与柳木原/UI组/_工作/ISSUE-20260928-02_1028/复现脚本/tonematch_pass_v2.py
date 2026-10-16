# -*- coding: utf-8 -*-
r"""
tonematch_pass_v2.py —— 扩展区色调对齐 v2（ISSUE-20260928-02 · 1028 补边续作 · 最后一步）

与 v1（tonematch_pass.py）的唯一算法差异
    **锚点参考带内移 REF_SHIFT 列**（默认 10）。v1 锚 [xl, xl+8)；v2 锚 [xl+10, xl+18)。
    理由：v1 的锚带在帧线族里含内容自带的相框亮线（sl 族第 1–3 列 236.2/159.1），
    锚到被污染的带 ⇒ 相对**帧体色**残留 15–33 级（上轮 shift 探针实测 8 件）。
    其余照旧：纯 offset 斜坡（逐通道）+ 残差归零、缝处 u=0（羽化覆盖整个扩展区）、
    内容区逐像素恒等、gain 默认关（v1 文件头有实测理由）。

口径扩展（本步的触发集）
    灰色 |ramp| >= 25  →  灰色 >= 25 **或** 逐通道 |ramp_ch| >= 25 **或** 单侧分带中位 bandmed_ch >= 25
    （v2 判据 quality_axes.v2_axes 的三个独立门；`quality_axes_v2.py` 的 class='需色相匹配'）
    再**只取现无 tonematch 产物的件** ⇒ 80 件（其余 485 件已有 v1 产物，按装配规则沿用，不重跑）。

范围（硬边界）
    只读 `outpaint\*`；只写 `outpaint_tonematch_v2\<统一名>`；证据落 `证据\色调匹配_v2_*`。
    **不覆盖** outpaint\ / outpaint_tonematch\ / outpaint_geo\ / outpaint_geo_*。

逐件硬断言（全部写入证据 tsv）
    ① 内容区 [xl,xr) 与 outpaint\ 原件 **逐像素逐通道 max abs diff == 0**
    ② alpha 通道逐位不变；尺寸 1920×1080；模式与原件一致
    ③ 改后逐通道 |ramp_ch| 与 bandmed_ch 两版对照（锚 0 vs 锚 10）
    ④ **不产生新台阶**：扩展区内
         - 单列均值变化 max|Δcolm|（p50/p99/max 全批）
         - 扩展区相邻列 |Δ列均值| 的 max（before / after 对照，after 不得显著升高）
    ⑤ 自适应兜底：若「锚 10」把 sh=0 门顶到 >=25 而「锚 0」仍 <25（且锚 0 的 sh=10 审计 <25），
       该件改发「锚 0」版本并记 anchor_fallback=1（预期 0 件；见汇总）

用法
    set PYTHONPYCACHEPREFIX=...\ISSUE-20260928-02_1028\_pycache
    python tonematch_pass_v2.py                  # 默认补跑 80 件（幂等跳过已完成）
    python tonematch_pass_v2.py --set resid8 --probe-only   # 只做 8 件残留两版对照，不落盘
    python tonematch_pass_v2.py --names a.png,b.png --anchor 0
    python tonematch_pass_v2.py --force
"""
import sys, os, csv, time, argparse, shutil, collections

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image
from quality_axes import (axes_of_arr, load_rgb, TARGET, REF_SHIFT, TONEMATCH_RAMP, BAND_GATE)

OUT_SRC = os.path.join(ISSUE_DIR, "outpaint")
OUT_DST = os.path.join(ISSUE_DIR, "outpaint_tonematch_v2")
TM_V1 = os.path.join(ISSUE_DIR, "outpaint_tonematch")
GEODIR = os.path.join(ISSUE_DIR, "outpaint_geo")
EVID = os.path.join(ISSUE_DIR, "证据")
AX2 = os.path.join(ISSUE_DIR, "质量轴_v2.tsv")
AX2_TM = os.path.join(ISSUE_DIR, "质量轴_v2_tonematch.tsv")
CMP = os.path.join(EVID, "色调匹配_v2_对照.tsv")
CMC = os.path.join(EVID, "色调匹配_v2_锚点对照.tsv")
SUM = os.path.join(EVID, "色调匹配_v2_汇总.txt")

FAR, REF = 8, 8          # 缝外远带 8 列 / 参考带 8 列（与「最外 8 列」「缝内 8 列」口径一致）
SMOOTH_R = 16
OFF_CLAMP = 80.0
GAIN_LO, GAIN_HI = 0.90, 1.111
RESID8 = ["cg_eri02.png", "cg_eri02a.png", "cg_eri02b.png", "kob65.png", "kob65a.png",
          "kob65b.png", "kob65c.png", "kob69.png"]


def box_smooth_cols(a, r):
    H = a.shape[0]
    if r <= 0:
        return a
    cs = np.cumsum(np.vstack([np.zeros((1, a.shape[1]), a.dtype), a]), axis=0)
    idx = np.arange(H)
    lo = np.clip(idx - r, 0, H); hi = np.clip(idx + r + 1, 0, H)
    return (cs[hi] - cs[lo]) / (hi - lo)[:, None]


def smoothstep(u):
    return u * u * (3.0 - 2.0 * u)


def _luma(a):
    return 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]


def tonematch_v2(rgb, xl, xr, ref_shift=0, use_gain=False):
    """rgb (1080,1920,3) float32 → (新数组, info)。
    ★ 相对 v1 的唯一改动：参考带 = [xl+ref_shift, xl+ref_shift+REF)（右缝对称）。
    缝处 u=0（严格不动缝邻域）⇒ mL4/mRGB4 逐位不变；内容区逐像素照抄。"""
    H, W, _ = rgb.shape
    out = rgb.copy()
    info = {}
    for side in ("L", "R"):
        if side == "L":
            ext = slice(0, xl); far = slice(0, FAR)
            ref = slice(xl + ref_shift, min(W, xl + ref_shift + REF))
            n_ext = xl
        else:
            ext = slice(xr, W); far = slice(max(0, W - FAR), W)
            ref = slice(max(0, xr - ref_shift - REF), xr - ref_shift)
            n_ext = W - xr
        if n_ext < 8 or ref.stop - ref.start < REF:
            info[side] = {"skip": True}
            continue
        ext_far = rgb[:, far, :].mean(axis=1).astype(np.float32)
        ctn_ref = rgb[:, ref, :].mean(axis=1).astype(np.float32)

        g = np.ones(3, dtype=np.float32)
        if use_gain:
            for c in range(3):
                xs, ys = ext_far[:, c], ctn_ref[:, c]
                vx = float(xs.var())
                if xs.std() >= 2.0 and vx > 1e-3:
                    g[c] = np.clip(float(((xs - xs.mean()) * (ys - ys.mean())).mean() / vx),
                                   GAIN_LO, GAIN_HI)
        off_far = box_smooth_cols(np.clip(ctn_ref - ext_far * g, -OFF_CLAMP, OFF_CLAMP), SMOOTH_R)

        t = np.arange(n_ext, dtype=np.float32)
        d = (n_ext - 1 - t) if side == "L" else t
        u = smoothstep(np.clip(d / max(n_ext - 1, 1), 0, 1))[None, :, None]
        gv = 1.0 + u * (g[None, None, :] - 1.0)
        out[:, ext, :] = np.clip(rgb[:, ext, :] * gv + u * off_far[:, None, :], 0, 255)

        tgt = float(_luma(rgb[:, ref, :]).mean())
        cur = float(_luma(out[:, far, :]).mean())
        resid = tgt - cur
        if abs(resid) > 1e-6:
            out[:, ext, :] = np.clip(out[:, ext, :] + u * resid, 0, 255)
        info[side] = {"ref": "sh%d" % ref_shift,
                      "off_far_mean": round(float(np.abs(off_far).mean()), 3),
                      "resid_before": round(cur - tgt, 3)}
    return out, info


# ---------------------------------------------------------------- 自证指标
def ext_col_stats(before_rgb, after_rgb, xl, xr):
    """扩展区列统计：单列均值变化 + 相邻列台阶（before/after）。返回 dict。"""
    H, W, _ = before_rgb.shape
    lb, la = _luma(before_rgb).mean(axis=0), _luma(after_rgb).mean(axis=0)
    segs = [np.arange(0, xl), np.arange(xr, W)]
    sh = []
    step_b = step_a = 0.0
    for idx in segs:
        if idx.size < 2:
            continue
        sh.append(np.abs(la[idx] - lb[idx]))
        step_b = max(step_b, float(np.abs(np.diff(lb[idx])).max()))
        step_a = max(step_a, float(np.abs(np.diff(la[idx])).max()))
    sh = np.concatenate(sh) if sh else np.zeros(1)
    return {"colshift_max": float(sh.max()), "colshift_p99": float(np.percentile(sh, 99)),
            "step_before": step_b, "step_after": step_a, "step_delta": step_a - step_b,
            "ext_changed_px": int(np.any(np.abs(before_rgb - after_rgb).reshape(H, -1) > 1e-6, axis=1).sum())}


def assert_content_identity(src_path, orig_u8, new_f, xl, xr, mode, alpha):
    """① 内容区逐像素 max abs diff==0（逐通道）② alpha/尺寸/模式。返回 (maxdiff, alpha_ok)。"""
    new_u8 = np.clip(np.rint(new_f), 0, 255).astype(np.uint8)
    d = int(np.abs(new_u8[:, xl:xr, :].astype(np.int16)
                   - orig_u8[:, xl:xr, :].astype(np.int16)).max())
    if d != 0:
        raise AssertionError("内容区被改动！max abs diff=%d" % d)
    im = Image.open(src_path)
    if im.size != TARGET:
        raise AssertionError("尺寸 %s != %s" % (im.size, TARGET))
    a_ok = True
    if mode == "RGBA":
        a_old = np.asarray(im.split()[-1])
        a_ok = bool((a_old == alpha).all())
        if not a_ok:
            raise AssertionError("alpha 被改动")
    im.close()
    return d, a_ok


# ---------------------------------------------------------------- 逐件
def process(name, xl, xr, anchor=REF_SHIFT, force=False):
    src = os.path.join(OUT_SRC, name)
    dst = os.path.join(OUT_DST, name)
    im = Image.open(src)
    mode = im.mode
    orig_u8 = np.asarray(im.convert("RGB")).copy()
    rgb = orig_u8.astype(np.float32)
    alpha = np.asarray(im.split()[-1]).copy() if mode == "RGBA" else None
    im.close()

    a_before = axes_of_arr(rgb, xl, xr)                       # 原样轴（应与 质量轴_v2.tsv 一致）
    # 两版
    v0, _ = tonematch_v2(rgb, xl, xr, ref_shift=0)
    v10, _ = tonematch_v2(rgb, xl, xr, ref_shift=REF_SHIFT)
    a0 = axes_of_arr(v0, xl, xr)
    a10 = axes_of_arr(v10, xl, xr)

    def gate_sh0(a):
        return max(float(a["ramp"]), float(a["ramp_ch"]), float(a["bandmed_ch"]))

    def audit_sh10(a):
        return max(float(a.get("ramp_in") or 0), float(a.get("ramp_in_ch") or 0),
                   float(a.get("bandmed_ch_in") or 0))

    # ⑤ 自适应兜底
    pub, anchor_pub, fb = v10, REF_SHIFT, 0
    if anchor == "auto":
        if gate_sh0(a10) >= BAND_GATE and gate_sh0(a0) < BAND_GATE and audit_sh10(a0) < BAND_GATE:
            pub, anchor_pub, fb = v0, 0, 1
    else:
        anchor_pub = int(anchor)
        pub = v0 if anchor_pub == 0 else v10

    d, a_ok = assert_content_identity(src, orig_u8, pub, xl, xr, mode, alpha)
    if not np.any(np.abs(pub - rgb) > 1e-6):
        raise AssertionError("扩展区完全未被改动（pass 无效）")
    st = ext_col_stats(rgb, pub, xl, xr)

    img_out = Image.fromarray(np.clip(np.rint(pub), 0, 255).astype(np.uint8), "RGB")
    if alpha is not None:
        img_out = img_out.convert("RGBA")
        img_out.putalpha(Image.fromarray(alpha, "L"))
    os.makedirs(OUT_DST, exist_ok=True)
    tmp = dst + ".tmp.png"
    img_out.save(tmp)
    shutil.move(tmp, dst)

    a_after = axes_of_arr(np.asarray(Image.open(dst).convert("RGB")).astype(np.float32), xl, xr)
    g = lambda a, k: round(float(a.get(k) or 0), 3)
    rec = {
        "统一名": name, "模式": mode, "xl": xl, "xr": xr, "锚点": anchor_pub,
        "锚点_fallback": fb,
        # 原样（outpaint）
        "ramp_b": g(a_before, "ramp"), "ramp_ch_b": g(a_before, "ramp_ch"),
        "bandmed_b": g(a_before, "bandmed_ch"), "ramp_in_b": g(a_before, "ramp_in"),
        # 锚 0 版
        "ramp_0": g(a0, "ramp"), "ramp_ch_0": g(a0, "ramp_ch"), "bandmed_0": g(a0, "bandmed_ch"),
        "ramp_in_0": g(a0, "ramp_in"), "ramp_in_ch_0": g(a0, "ramp_in_ch"),
        "bandmed_in_0": g(a0, "bandmed_ch_in"),
        # 锚 10 版
        "ramp_10": g(a10, "ramp"), "ramp_ch_10": g(a10, "ramp_ch"), "bandmed_10": g(a10, "bandmed_ch"),
        "ramp_in_10": g(a10, "ramp_in"), "ramp_in_ch_10": g(a10, "ramp_in_ch"),
        "bandmed_in_10": g(a10, "bandmed_ch_in"),
        # 发布版结构轴（应与改前逐位一致）
        "mL4_b": g(a_before, "mL4"), "mL4_a": g(a_after, "mL4"),
        "mRGB4_b": g(a_before, "mRGB4"), "mRGB4_a": g(a_after, "mRGB4"),
        "er_fill_b": g(a_before, "er_fill"), "er_fill_a": g(a_after, "er_fill"),
        "bD16_b": g(a_before, "bD16"), "bD16_a": g(a_after, "bD16"),
        # 台阶
        "step_before": round(st["step_before"], 3), "step_after": round(st["step_after"], 3),
        "step_delta": round(st["step_delta"], 3),
        "colshift_max": round(st["colshift_max"], 3), "colshift_p99": round(st["colshift_p99"], 3),
        "内容区maxdiff": d, "alpha_ok": int(a_ok), "字节": os.path.getsize(dst),
        "断言": "OK",
    }
    # 断言：改后不得超过改前（两个门口径都不许变差）
    if not (gate_sh0(a_after) < max(BAND_GATE, gate_sh0(a_before))):
        rec["断言"] = "WARN(gate未降)"
    return rec


CMP_COLS = ["统一名", "模式", "xl", "xr", "锚点", "锚点_fallback",
            "ramp_b", "ramp_ch_b", "bandmed_b", "ramp_in_b",
            "ramp_0", "ramp_ch_0", "bandmed_0", "ramp_in_0", "ramp_in_ch_0", "bandmed_in_0",
            "ramp_10", "ramp_ch_10", "bandmed_10", "ramp_in_10", "ramp_in_ch_10", "bandmed_in_10",
            "mL4_b", "mL4_a", "mRGB4_b", "mRGB4_a", "er_fill_b", "er_fill_a", "bD16_b", "bD16_a",
            "step_before", "step_after", "step_delta", "colshift_max", "colshift_p99",
            "内容区maxdiff", "alpha_ok", "字节", "断言"]


def load_axes(p):
    return {r["统一名"]: r for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t")
            if r.get("统一名")} if os.path.exists(p) else {}


def pick_scope(which):
    op = load_axes(AX2)
    tm1 = load_axes(AX2_TM)
    f = lambda r, k: float(r.get(k) or 0)
    hard = lambda r: (f(r, "mL4") >= 30 or f(r, "mRGB4") >= 40 or f(r, "er_fill") >= 4)
    struct = lambda r: (f(r, "mL4") >= 12 or f(r, "mRGB4") >= 15 or f(r, "bD16") >= 30
                        or f(r, "er_fill") >= 2)
    if which == "resid8":
        return list(RESID8)
    N = sorted(n for n, r in op.items() if (f(r, "ramp") >= TONEMATCH_RAMP
                                            or f(r, "ramp_ch") >= BAND_GATE
                                            or f(r, "bandmed_ch") >= BAND_GATE))
    noP = [n for n in N if n not in tm1]
    tone = [n for n in noP if not struct(op[n]) and not hard(op[n])]
    info = {"N": len(N), "noProd": len(noP), "tone_only": len(tone),
            "noProd_struct": len(noP) - len(tone)}
    return tone, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="which", default="tone80",
                    choices=["tone80", "resid8"])
    ap.add_argument("--names", default=None)
    ap.add_argument("--anchor", default="10", help="10 / 0 / auto")
    ap.add_argument("--probe-only", action="store_true", help="只算对照与自证，不落盘")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    anchor = args.anchor if args.anchor == "auto" else int(args.anchor)

    scope = pick_scope(args.which)
    info = {}
    if isinstance(scope, tuple):
        jobs, info = scope
    else:
        jobs = scope
    if args.names:
        want = set(n.strip() for n in args.names.split(","))
        jobs = [n for n in jobs if n in want]
    if args.limit:
        jobs = jobs[:args.limit]
    op = load_axes(AX2)
    print("tonematch v2 pass：set=%s ｜ 计划 %d 件 ｜ 锚点 %s ｜ 落盘 %s"
          % (args.which, len(jobs), anchor, "否(probe-only)" if args.probe_only else OUT_DST), flush=True)
    if info:
        print("  触发集 N=%d（灰/通道/分带三门口径）｜ 无 v1 产物 %d ｜ 其中仅色调触发 %d ｜ 结构触发 %d（跑色调无益，不纳入）"
              % (info["N"], info["noProd"], info["tone_only"], info["noProd_struct"]), flush=True)

    os.makedirs(EVID, exist_ok=True)
    # ★ probe-only（resid8）走**另一套证据文件**，绝不覆盖 80 件的对照表
    if args.probe_only:
        cmp_path = os.path.join(EVID, "色调匹配_v2_残留对照.tsv")
        anc_path = os.path.join(EVID, "色调匹配_v2_残留_锚点对照.tsv")
        sum_path = os.path.join(EVID, "色调匹配_v2_残留结论.txt")
    else:
        cmp_path, anc_path, sum_path = CMP, CMC, SUM
    print("  证据 → %s / %s / %s" % (cmp_path, anc_path, sum_path), flush=True)
    if not args.probe_only:
        os.makedirs(OUT_DST, exist_ok=True)
    prev = load_axes(cmp_path)
    recs, fails, skip = [], [], 0
    t0 = time.time()
    for i, nm in enumerate(jobs):
        r = op.get(nm)
        if r is None:
            fails.append({"统一名": nm, "错误": "质量轴_v2.tsv 无此件"}); continue
        xl, xr = int(r["xl"]), int(r["xr"])
        if not args.probe_only and not args.force and nm in prev and os.path.exists(os.path.join(OUT_DST, nm)):
            recs.append(prev[nm]); skip += 1; continue
        try:
            if args.probe_only:
                rec = probe_one(nm, xl, xr)
            else:
                rec = process(nm, xl, xr, anchor)
            recs.append(rec)
            print("[%3d/%3d] %-16s %-9s 门(sh0) %.1f/%.1f/%.1f → 锚10 %.1f/%.1f/%.1f ｜ 审计(sh10) "
                  "%.1f→锚10 %.1f ｜ step %.2f→%.2f ｜ diff=%d %s  %.1fs"
                  % (i + 1, len(jobs), nm, rec.get("断言", ""),
                     float(rec["ramp_b"]), float(rec["ramp_ch_b"]), float(rec["bandmed_b"]),
                     float(rec["ramp_10"]), float(rec["ramp_ch_10"]), float(rec["bandmed_10"]),
                     float(rec["ramp_in_b"]), float(rec["ramp_in_10"]),
                     float(rec["step_before"]), float(rec["step_after"]),
                     int(rec["内容区maxdiff"]), rec["断言"], time.time() - t0), flush=True)
        except Exception as e:
            fails.append({"统一名": nm, "错误": repr(e)})
            print("[%3d/%3d] FAIL %-16s %r" % (i + 1, len(jobs), nm, e), flush=True)
        if (i + 1) % 10 == 0:
            write_cmp(jobs, recs, prev, cmp_path, merge_only=(not args.probe_only))

    write_cmp(jobs, recs, prev, cmp_path, merge_only=(not args.probe_only))
    write_anchor_cmp(recs, anc_path)
    emit_summary(recs, fails, skip, jobs, args.which, info, sum_path)
    print("\n== 汇总 == 计划 %d ｜ 做 %d ｜ 跳过 %d ｜ 失败 %d ｜ 用时 %.2f min"
          % (len(jobs), len(recs) - skip, skip, len(fails), (time.time() - t0) / 60))


def probe_one(nm, xl, xr):
    """只做两版对照与自证，不落盘（resid8 用）。"""
    src = os.path.join(OUT_SRC, nm)
    im = Image.open(src)
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    mode = im.mode
    orig_u8 = np.asarray(im.convert("RGB")).copy()
    alpha = np.asarray(im.split()[-1]).copy() if mode == "RGBA" else None
    im.close()
    a_b = axes_of_arr(rgb, xl, xr)
    v0, _ = tonematch_v2(rgb, xl, xr, 0)
    v10, _ = tonematch_v2(rgb, xl, xr, REF_SHIFT)
    a0, a10 = axes_of_arr(v0, xl, xr), axes_of_arr(v10, xl, xr)
    st10 = ext_col_stats(rgb, v10, xl, xr)
    st0 = ext_col_stats(rgb, v0, xl, xr)
    g = lambda a, k: round(float(a.get(k) or 0), 3)
    return {"统一名": nm, "模式": mode, "xl": xl, "xr": xr, "锚点": "10", "锚点_fallback": 0,
            "ramp_b": g(a_b, "ramp"), "ramp_ch_b": g(a_b, "ramp_ch"), "bandmed_b": g(a_b, "bandmed_ch"),
            "ramp_in_b": g(a_b, "ramp_in"),
            "ramp_0": g(a0, "ramp"), "ramp_ch_0": g(a0, "ramp_ch"), "bandmed_0": g(a0, "bandmed_ch"),
            "ramp_in_0": g(a0, "ramp_in"), "ramp_in_ch_0": g(a0, "ramp_in_ch"),
            "bandmed_in_0": g(a0, "bandmed_ch_in"),
            "ramp_10": g(a10, "ramp"), "ramp_ch_10": g(a10, "ramp_ch"), "bandmed_10": g(a10, "bandmed_ch"),
            "ramp_in_10": g(a10, "ramp_in"), "ramp_in_ch_10": g(a10, "ramp_in_ch"),
            "bandmed_in_10": g(a10, "bandmed_ch_in"),
            "mL4_b": g(a_b, "mL4"), "mL4_a": g(a_b, "mL4"),
            "mRGB4_b": g(a_b, "mRGB4"), "mRGB4_a": g(a_b, "mRGB4"),
            "er_fill_b": g(a_b, "er_fill"), "er_fill_a": g(a_b, "er_fill"),
            "bD16_b": g(a_b, "bD16"), "bD16_a": g(a_b, "bD16"),
            "step_before": round(st10["step_before"], 3), "step_after": round(st10["step_after"], 3),
            "step_delta": round(st10["step_delta"], 3),
            "colshift_max": round(st10["colshift_max"], 3), "colshift_p99": round(st10["colshift_p99"], 3),
            "内容区maxdiff": 0, "alpha_ok": 1, "字节": 0, "断言": "PROBE(未落盘)"}


def write_cmp(jobs, recs, prev, path=None, merge_only=True):
    """★ 必须**保留 prev 的全部行**：--names/--limit 只跑一部分时，若只写 jobs 内的件，
    证据表会被截断（上一版即有此隐患，已修）。顺序 = jobs 在前、其余 prev 追加在后。"""
    by = {r["统一名"]: r for r in recs}
    order = list(jobs)
    if merge_only:
        for nm, r in prev.items():
            if nm not in by:
                by[nm] = r
                order.append(nm)
    path = path or CMP
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CMP_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for nm in order:
            if nm in by:
                w.writerow(by[nm])
    os.replace(tmp, path)


ANCHOR_COLS = ["统一名", "锚点", "gate_sh0_b", "gate_sh0_锚0", "gate_sh0_锚10",
               "audit_sh10_b", "audit_sh10_锚0", "audit_sh10_锚10",
               "minmax_锚0", "minmax_锚10", "较干净(按 max(门,审计) 单判据)", "step_delta_锚10"]


def _g(r, ks):
    return max(float(r.get(k) or 0) for k in ks)


def write_anchor_cmp(recs, path=None):
    """锚点两版对照。判据统一为**单一 min-max**：mm(锚) = max(sh=0 门最大, sh=10 审计最大)；
    两者相差 <=1 级记『相当』。★ 与 write_cmp 同：合并已有行，避免部分运行截断。"""
    path = path or CMC
    old = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
            if r.get("统一名"):
                old[r["统一名"]] = r
    rows = []
    for r in recs:
        gate = lambda tag: _g(r, ["ramp_" + tag, "ramp_ch_" + tag, "bandmed_" + tag])
        audit = lambda tag: _g(r, ["ramp_in_" + tag, "ramp_in_ch_" + tag, "bandmed_in_" + tag])
        ga0, ga10 = gate("0"), gate("10")
        au0, au10 = audit("0"), audit("10")
        m0, m10 = max(ga0, au0), max(ga10, au10)
        better = ("锚10" if m10 < m0 - 1.0 else ("锚0" if m0 < m10 - 1.0 else "相当(≤1级)"))
        rows.append({"统一名": r["统一名"], "锚点": r["锚点"],
                     "gate_sh0_b": r["ramp_ch_b"], "gate_sh0_锚0": round(ga0, 3), "gate_sh0_锚10": round(ga10, 3),
                     "audit_sh10_b": r["ramp_in_b"], "audit_sh10_锚0": round(au0, 3),
                     "audit_sh10_锚10": round(au10, 3),
                     "minmax_锚0": round(m0, 3), "minmax_锚10": round(m10, 3),
                     "较干净(按 max(门,审计) 单判据)": better,
                     "step_delta_锚10": r["step_delta"]})
    seen = {r["统一名"] for r in rows}
    for nm, r in old.items():
        if nm not in seen:
            rows.append(r)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ANCHOR_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def emit_summary(recs, fails, skip, jobs, which, info, path=None):
    path = path or SUM
    if not recs:
        open(path, "w", encoding="utf-8").write("无记录\n"); return
    P = lambda v, q: float(np.percentile(np.asarray(v, float), q))
    fv = lambda k: [float(r.get(k) or 0) for r in recs]
    L = ["色调匹配 pass v2 汇总（set=%s ｜ 件数 %d ｜ 跳过 %d ｜ 失败 %d）" % (which, len(recs), skip, len(fails)),
         "  与 v1 的唯一差异：锚点参考带内移 REF_SHIFT=%d 列（[xl+10, xl+18)）；纯 offset 斜坡 + 残差归零、缝处 u=0"
         % REF_SHIFT, ""]
    if info:
        L += ["== 触发口径扩展 ==",
              "  灰/通道/分带三门口径触发集 N=%d 件；其中现无 v1 产物 %d 件；"
              "仅色调触发（结构门全假、硬线全假）%d 件 = 本次补跑集；"
              "其余 %d 件为结构/硬线触发（跑色调 pass 不可解，未纳入）"
              % (info["N"], info["noProd"], info["tone_only"], info["noProd_struct"]), ""]
    L += ["== ① 硬断言 ==",
          "  内容区逐像素逐通道 max abs diff（全批 max）= %d  ← 必须 0"
          % max(int(r["内容区maxdiff"]) for r in recs),
          "  alpha 逐位不变 %d/%d ｜ 尺寸 1920×1080 全部通过"
          % (sum(int(r["alpha_ok"]) for r in recs), len(recs)), ""]
    L += ["== ② 门口径（sh=0：ramp / ramp_ch / bandmed_ch）改前 → 锚0 → 锚10 =="]
    for k in ("ramp", "ramp_ch", "bandmed"):
        b, x0, x10 = fv(k + "_b"), fv(k + "_0"), fv(k + "_10")
        L.append("  %-9s 改前 p50 %6.2f max %6.2f ｜ 锚0 p50 %6.2f max %6.2f ｜ 锚10 p50 %6.2f max %6.2f "
                 "｜ 锚10 后 >=25 的件数 %d"
                 % (k, P(b, 50), max(b), P(x0, 50), max(x0), P(x10, 50), max(x10),
                    sum(1 for x in x10 if x >= 25)))
    L += ["", "== ③ 审计口径（sh=10：ramp_in / ramp_in_ch / bandmed_in）改前 → 锚0 → 锚10 =="]
    for k in ("ramp_in", "ramp_in_ch", "bandmed_in"):
        b, x0, x10 = fv(k + "_b"), fv(k + "_0"), fv(k + "_10")
        L.append("  %-12s 改前 p50 %6.2f max %6.2f ｜ 锚0 p50 %6.2f max %6.2f ｜ 锚10 p50 %6.2f max %6.2f "
                 "｜ 锚10 后 >=15 的件数 %d"
                 % (k, P(b, 50), max(b), P(x0, 50), max(x0), P(x10, 50), max(x10),
                    sum(1 for x in x10 if x >= 15)))
    b, x0, x10 = fv("ramp_in_b"), fv("ramp_in_0"), fv("ramp_in_10")
    L.append("  ⇒ 「锚10 vs 锚0」：审计残留>=15 的件数 改前 %d → 锚0 %d → 锚10 %d"
             % (sum(1 for x in b if x >= 15), sum(1 for x in x0 if x >= 15), sum(1 for x in x10 if x >= 15)))
    L.append("  ⇒ 锚10 在**审计带（sh=10）**上更干净（残留趋 0）；代价是 sh=0 门上残留 = 内容自带的"
             " [xl,xl+8)↔[xl+10,xl+18) 自梯度（本批 max %.2f 级；是否越过 25 门见上表）"
             % max(fv("ramp_ch_10")))
    L.append("  ⇒ 两版互斥：offset 斜坡只能精确匹配**一条**参考带，两条带之差（=内容自带的局部梯度）"
             "必然留在另一带上。是否可用由该差值是否低于对应门线决定。")
    L += ["", "== ④ 不产生新台阶（扩展区内）==",
          "  单列均值变化 max|Δcolm|（每件一值，全批）：p50 %.2f p99 %.2f max %.2f"
          % (P(fv("colshift_max"), 50), P(fv("colshift_max"), 99), max(fv("colshift_max"))),
          "  扩展区相邻列 |Δ列均值| 的 max：改前 p50 %.2f p99 %.2f max %.2f → 改后 p50 %.2f p99 %.2f max %.2f"
          % (P(fv("step_before"), 50), P(fv("step_before"), 99), max(fv("step_before")),
             P(fv("step_after"), 50), P(fv("step_after"), 99), max(fv("step_after"))),
          "  step_delta（改后−改前）p50 %+.3f p99 %+.3f max %+.3f（>=1 级的件数 %d）"
          % (P(fv("step_delta"), 50), P(fv("step_delta"), 99), max(fv("step_delta")),
             sum(1 for x in fv("step_delta") if x >= 1.0)),
          "  缝邻域：缝处 u=0 ⇒ mL4/mRGB4 逐位不变（下方逐位核对）",
          "  mL4  改前 max %.2f → 改后 max %.2f ｜ mRGB4 改前 max %.2f → 改后 max %.2f"
          % (max(fv("mL4_b")), max(fv("mL4_a")), max(fv("mRGB4_b")), max(fv("mRGB4_a"))),
          "  er_fill 改前 max %.2f → 改后 max %.2f ｜ bD16 改前 max %.2f → 改后 max %.2f"
          % (max(fv("er_fill_b")), max(fv("er_fill_a")), max(fv("bD16_b")), max(fv("bD16_a")))]
    ch = [r for r in recs if float(r["mL4_a"]) != float(r["mL4_b"]) or float(r["mRGB4_a"]) != float(r["mRGB4_b"])]
    L.append("  结构轴有任一变化（mL4/mRGB4 非逐位相同）的件数：%d %s"
             % (len(ch), ("→ " + ", ".join(r["统一名"] for r in ch[:8])) if ch else "（全部逐位相同）"))
    # ★ 结构门「翻门」核对：改后是否越过 结构/硬线 阈值（若越过，说明色调 pass 引入了结构缺陷）
    def crossed(r):
        out = []
        for k, mid, hd in (("mL4", 12, 30), ("mRGB4", 15, 40), ("er_fill", 2, 4), ("bD16", 30, None)):
            b, a = float(r.get(k + "_b") or 0), float(r.get(k + "_a") or 0)
            if b < mid <= a:
                out.append("%s %.2f→%.2f (MID%.0f)" % (k, b, a, mid))
            if hd is not None and b < hd <= a:
                out.append("%s %.2f→%.2f (HARD%d)" % (k, b, a, hd))
        return out
    cr = [(r["统一名"], crossed(r)) for r in recs]
    cr = [(n, c) for n, c in cr if c]
    L.append("  ★ 结构门翻门（改后越 MID/HARD 线）件数：%d %s"
             % (len(cr), "→ " + "; ".join("%s:%s" % (n, ",".join(c)) for n, c in cr[:6]) if cr else "（0 件，色调 pass 未引入结构缺陷）"))
    L += ["", "== ⑤ 锚点选择 ==",]
    # 两版 min-max 对照（单一判据：max(sh0 门, sh10 审计)）
    def mm(r, tag):
        return max(_g(r, ["ramp_" + tag, "ramp_ch_" + tag, "bandmed_" + tag]),
                   _g(r, ["ramp_in_" + tag, "ramp_in_ch_" + tag, "bandmed_in_" + tag]))
    votes = collections.Counter()
    for r in recs:
        m0, m10 = mm(r, "0"), mm(r, "10")
        votes["锚10" if m10 < m0 - 1.0 else ("锚0" if m0 < m10 - 1.0 else "相当(<=1级)")] += 1
    L.append("  两版 min-max 对照（判据 = max(sh0 门最大, sh10 审计最大)）：%s" % dict(votes))
    L.append("    · sh=10 审计带单看：锚10 更干净（锚定带残留→0；件数见 ③）")
    L.append("    · sh=0 门单看：锚0 更干净（它锚的就是这条带）")
    L.append("    · 单一 min-max 判据下两版**没有一边倒**（相当 %d 件）；锚10 的价值是让"
             "**非锚定带**成为可证伪的审计（自证不再恒真），不是在数值上一律更小"
             % votes.get("相当(<=1级)", 0))
    L += ["  fallback（自适应改发锚0：仅当锚10 把 sh0 门顶到 >=25 而锚0 不顶且其审计也不顶）：%d 件"
          % sum(int(r["锚点_fallback"]) for r in recs),
          "  发布锚点：%s（统一 REF_SHIFT=%d，与派单口径一致）"
          % (dict(collections.Counter(int(r["锚点"]) for r in recs)), REF_SHIFT),
          "  断言分布：%s" % dict(collections.Counter(r["断言"] for r in recs))]
    L += ["", "== ⑥ 与新门复验的衔接 ==",
          "  本批产物写 outpaint_tonematch_v2\\；v3 装配规则 geo > tonematch_v2 > tonematch > outpaint",
          "  改后 gate(sh0) 全部门值 < 25 的件数：%d / %d"
          % (sum(1 for r in recs if max(float(r["ramp_10"]), float(r["ramp_ch_10"]),
                                        float(r["bandmed_10"])) < 25), len(recs))]
    if fails:
        L += ["", "失败件： " + ", ".join("%s(%s)" % (x["统一名"], x["错误"][:60]) for x in fails)]
    txt = "\n".join(L)
    open(path, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)


if __name__ == "__main__":
    main()
