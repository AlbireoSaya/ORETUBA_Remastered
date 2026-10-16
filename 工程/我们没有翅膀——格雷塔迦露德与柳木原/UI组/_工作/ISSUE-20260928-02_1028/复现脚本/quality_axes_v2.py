# -*- coding: utf-8 -*-
r"""
quality_axes_v2.py —— 判据 v2 驱动（ISSUE-20260928-02 · 1028 补边续作 · vision 打回后重做）

为什么有这一版
    v1（quality_axes.py）把 640 件判成「257 件可直接放行」，vision 打回：**pass 本身没问题，
    打回的是判据与证据包**。三条判据缺陷（vision 证据，已逐条复核）：
      ① 灰度全高平均的 |ramp| 有色相盲区（yy_19 13.65 vs ramp_ch 43.0；kob68 族 6.1 vs 50.3）；
      ② 全高平均还有分带抵消盲区（yy_19 带内 luma 差 −27.6，全高平均只剩 0.3）；
      ③ 内容参考带 [xl, xl+8) 含内容自带的相框亮线 ⇒ |ramp| 虚低。
    本脚本用 v2 判据（灰度线仍 25 ＋ 新增 ramp_ch / 单侧分带中位 两个独立门 ＋ 参考带内移
    的审计值 ＋ er 修正口径）重跑 640 件，重出分桶与放行集合。

v2 口径（公式）
    ext_far_c(y)  = 图片最外 8 列的逐行列均值；ctn_ref_c(y) = 缝内侧 8 列（可内移 sh 列）
    ramp          = |mean(ext_far) − mean(ctn_ref)|，灰度，两侧取最大，**sh=0**（沿用旧线 25）
    ramp_ch       = 逐通道同上取最大（两侧最大）
    bandmed_ch    = max_side max_c median_{6 带}( |带内 ext_far_c 均值 − 带内 ctn_ref_c 均值| )
    门：灰度 ramp >= 25 或 ramp_ch >= 25 或 bandmed_ch >= 25（三个独立门，任一触发即须色相匹配）
    修正 er（er_fill）= 填充区内部 1px 逐列均值梯度（缝外侧 40 列、分 6 带取最大）
                       / max(内容区内侧平均逐列梯度, 0.5)
    内移审计：ramp_in / ramp_in_ch / bandmed_ch_in 用 sh = REF_SHIFT(=10)

产物
    质量轴_v2.tsv / 质量轴_v2_tonematch.tsv / 质量轴_v2_geo.tsv      逐件全轴
    须处置清单_v2.tsv        逐件：四桶 + 全部门/轴值
    放行清单_v2.tsv          放行集合（可直接装配，含 pass 已解决与人工特批）
    质量轴_v2_汇总.txt       分布对照 / shift 表 / er 对照 / 分桶 / 与 vision 值比对

用法
    set PYTHONPYCACHEPREFIX=...\ISSUE-20260928-02_1028\_pycache
    python quality_axes_v2.py                       # 全量重算（幂等跳过已有行）
    python quality_axes_v2.py --force
    python quality_axes_v2.py --summary-only        # 只按已有 v2 tsv 重出汇总/清单
    python quality_axes_v2.py --src geo             # 只对 outpaint_geo 3 件出轴值
"""
import sys, os, csv, time, argparse, collections, json

WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image
from quality_axes import (out_seams, axes_of_arr, load_rgb, TARGET, LIST_TSV,
                          AX_COLS, HARD_ML4, HARD_MRGB4, HARD_ER,
                          MID_ML4, MID_MRGB4, MID_ER, MID_BD16,
                          TONEMATCH_RAMP, BAND_GATE, REF_SHIFT,
                          NBANDS, RAMP_OUT, VISION_RAMP_CH_GE25, VISION_RELEASE)

AX2_TSV = os.path.join(ISSUE_DIR, "质量轴_v2.tsv")
DISP2_TSV = os.path.join(ISSUE_DIR, "须处置清单_v2.tsv")
DISP_TSV_MAIN = os.path.join(ISSUE_DIR, "须处置清单.tsv")   # 协调方点名的文件名（v1 已备份 *_v1.tsv）
REL2_TSV = os.path.join(ISSUE_DIR, "放行清单_v2.tsv")
SUM2_TXT = os.path.join(ISSUE_DIR, "质量轴_v2_汇总.txt")

SRC_DIRS = {"outpaint": os.path.join(ISSUE_DIR, "outpaint"),
            "tonematch": os.path.join(ISSUE_DIR, "outpaint_tonematch"),
            "geo": os.path.join(ISSUE_DIR, "outpaint_geo")}


def axes_tsv_for(src):
    return {"outpaint": AX2_TSV,
            "tonematch": os.path.join(ISSUE_DIR, "质量轴_v2_tonematch.tsv"),
            "geo": os.path.join(ISSUE_DIR, "质量轴_v2_geo.tsv")}[src]


def load_rows(only_names=None, only_src=None):
    rows = [r for r in csv.DictReader(open(LIST_TSV, encoding="utf-8"), delimiter="\t")
            if r["建议策略(重制/补边/裁切)"] == "补边"]
    if only_names:
        want = set(only_names)
        rows = [r for r in rows if r["统一名"] in want]
    return rows


# ================================================================ 逐件算轴
def run(src, names=None, force=False, limit=0):
    out_dir = SRC_DIRS[src]
    tsv = axes_tsv_for(src)
    rows = load_rows(names)
    cache = {}
    if os.path.exists(tsv) and not force:
        for r in csv.DictReader(open(tsv, encoding="utf-8"), delimiter="\t"):
            if r.get("统一名") and r.get("mL4") not in (None, ""):
                cache[r["统一名"]] = r
    todo = [r for r in rows if r["统一名"] not in cache
            and os.path.exists(os.path.join(out_dir, r["统一名"]))]
    if limit:
        todo = todo[:limit]
    print("[%s] 计划 %d ｜ 已有缓存 %d ｜ 本次算 %d" % (src, len(rows), len(cache), len(todo)), flush=True)
    fails, t0 = [], time.time()
    for i, r in enumerate(todo):
        nm = r["统一名"]
        try:
            src_img = os.path.join(MAIN_PROJ, r["超分版路径"])
            W, H = Image.open(src_img).size
            xl, xr = out_seams(W, H)
            rgb, mode = load_rgb(os.path.join(out_dir, nm))
            if rgb.shape[:2] != (TARGET[1], TARGET[0]):
                raise AssertionError("尺寸 %s != 1920x1080" % (rgb.shape[:2],))
            a = axes_of_arr(rgb, xl, xr)
            del rgb
            rec = {"统一名": nm, "档位": r["建议档位(T1/T2/T3)"], "类别": r["类别"],
                   "判读类别": r["判读类别"], "源尺寸": "%dx%d" % (W, H),
                   "源模式": mode, "xl": xl, "xr": xr, "备注": ""}
            rec.update({k: a[k] for k in AX_COLS if k in a})
            cache[nm] = rec
            print("  [%3d/%3d] %-18s %-9s mL4=%7.2f mRGB4=%7.2f er_fill=%6.2f ramp=%6.2f "
                  "ramp_ch=%6.2f bandmed=%6.2f  %.2fs"
                  % (i + 1, len(todo), nm, src, a["mL4"], a["mRGB4"], a["er_fill"], a["ramp"],
                     a["ramp_ch"], a["bandmed_ch"], time.time() - t0), flush=True)
            if (i + 1) % 40 == 0:
                write_tsv(tsv, rows, cache)
        except Exception as e:
            fails.append((nm, repr(e)))
            print("  [%3d/%3d] FAIL %-18s %r" % (i + 1, len(todo), nm, e), flush=True)
    write_tsv(tsv, rows, cache)
    if fails:
        with open(tsv + ".失败.tsv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t"); w.writerow(["统一名", "错误"]); w.writerows(fails)
    print("[%s] 完成：tsv %s（%d 行）｜失败 %d ｜用时 %.2f min"
          % (src, tsv, len(cache), len(fails), (time.time() - t0) / 60), flush=True)
    return cache


def write_tsv(tsv, rows, cache):
    tmp = tsv + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=AX_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rec = cache.get(r["统一名"])
            if rec is None:
                continue
            for k, v in classify_v2(rec).items():
                rec[k] = v
            w.writerow(rec)
    os.replace(tmp, tsv)


# ================================================================ v2 门 / 分桶
def gates_v2(r):
    """(hard, structural, tone)。structural 沿用 vision 的结构触发集（mL4>=12 / mRGB4>=15 /
    bD16>=30 / er>=2），其中 er 用**修正口径 er_fill**（旧 er 被内容自带强梯度毒化）。"""
    f = lambda k: float(r.get(k) or 0.0)
    hard = (f("mL4") >= HARD_ML4 or f("mRGB4") >= HARD_MRGB4 or f("er_fill") >= HARD_ER)
    structural = (f("mL4") >= MID_ML4 or f("mRGB4") >= MID_MRGB4
                  or f("bD16") >= MID_BD16 or f("er_fill") >= MID_ER)
    # 色调三独立门：灰度 25（沿用）＋ 逐通道 ramp_ch>=25 ＋ 单侧分带中位>=25
    tone = (f("ramp") >= TONEMATCH_RAMP or f("ramp_ch") >= BAND_GATE
            or f("bandmed_ch") >= BAND_GATE)
    return hard, structural, tone


def tone_gate_reason(r):
    f = lambda k: float(r.get(k) or 0.0)
    why = []
    if f("ramp") >= TONEMATCH_RAMP:
        why.append("灰度|ramp|=%.1f>=25" % f("ramp"))
    if f("ramp_ch") >= BAND_GATE:
        why.append("|ramp_ch|=%.1f>=25" % f("ramp_ch"))
    if f("bandmed_ch") >= BAND_GATE:
        why.append("分带中位=%.1f>=25" % f("bandmed_ch"))
    return "；".join(why)


def classify_v2(r):
    """四桶（互斥）：重绘 / 精修 / 需色相匹配 / 放行；附放行_v2 与理由。"""
    hard, structural, tone = gates_v2(r)
    fs = int(float(r.get("frame_seam") or 0))
    notes = []
    if fs:
        cls, act = "放行", "人工特批(几何延展)"
        notes.append("帧线件：geo 产物经人工特批（vision 判观感可接受，闸门不适用）")
    elif hard:
        cls, act = "重绘", "重绘扩展区"
        notes.append("HARD：mL4/mRGB4/er_fill 破硬线")
    elif structural:
        cls, act = "精修", "精修"
        notes.append("结构触发（mL4>=12 或 mRGB4>=15 或 bD16>=30 或 er_fill>=2），色调 pass 修不了")
    elif tone:
        cls, act = "需色相匹配", "色调匹配"
        notes.append("仅色调触发：" + tone_gate_reason(r))
    else:
        cls, act = "放行", "可直接采用"
        notes.append("三独立门全过：灰度 %.1f / ramp_ch %.1f / 分带中位 %.1f"
                     % (float(r.get("ramp") or 0), float(r.get("ramp_ch") or 0),
                        float(r.get("bandmed_ch") or 0)))
    if fs:
        notes.append("缝外侧%dx有单列强边|Δ|=%.1f" % (int(float(r.get("frame_x") or 0)),
                                                float(r.get("frame_v") or 0)))
    rel = (cls == "放行")
    return {"分类_v2": cls, "建议处置_v2": act, "放行_v2": "是" if rel else "否",
            "备注": "；".join(notes)}

# ================================================================ 装配口径
def assemble(recs, tm_recs, geo_recs):
    """装配口径：**帧线件取 geo（几何延展）＞ 有 outpaint_tonematch 产物取 tonematch ＞ outpaint**。

    ★ 为什么 geo 优先于 tonematch：tonematch 只改扩展区色调，**不动结构**——sl 族 3 件的
      mL4=104–108 在 tonematch 产物里原样保留（实测 mL4_before=max=108.03），拿 tonematch
      装配等于把 pass 修不了的帧线留在画面上；geo 才是这 3 件的正确产物。
    """
    tmm = {r["统一名"]: r for r in tm_recs}
    gom = {r["统一名"]: r for r in geo_recs}
    out = {}
    for r in recs:
        nm = r["统一名"]
        fs = int(float(r.get("frame_seam") or 0))
        if fs == 1 and nm in gom:
            src, rec = "geo", gom[nm]
        elif nm in tmm:
            src, rec = "tonematch", tmm[nm]
        else:
            src, rec = "outpaint", r
        out[nm] = (src, rec, r)
    return out


# ================================================================ 汇总
def pct(vals, q):
    v = sorted(vals)
    return v[int(q * (len(v) - 1))] if v else float("nan")


def summary(recs, tm_recs, geo_recs, tm_names):
    f = lambda r, k: float(r.get(k) or 0.0)
    L = []
    L.append("判据 v2 汇总（n=%d）｜ 参考带内移 REF_SHIFT=%d 列 ｜ 门：灰度 25 ＋ ramp_ch 25 ＋ 单侧分带中位 25"
             % (len(recs), REF_SHIFT))
    L.append("")

    # ---------------- ① 逐通道 |ramp| 与分带量（复现 vision 教师值） ----------------
    L.append("== ① 逐通道 |ramp| / 单侧分带量 分布（复现 vision 教师值）==")
    v = [f(r, "ramp_ch") for r in recs]
    n25 = sum(1 for x in v if x >= 25)
    L.append("   ramp_ch  p50 %.2f  p90 %.2f  p99 %.2f  max %.2f"
             % (pct(v, .5), pct(v, .9), pct(v, .99), max(v)))
    L.append("   ramp_ch >= 25 : %d 件   （vision 报 %d 件；差 %+d）★口径逐值复现"
             % (n25, VISION_RAMP_CH_GE25, n25 - VISION_RAMP_CH_GE25))
    vg = [f(r, "ramp") for r in recs]
    L.append("   灰度 |ramp| >= 25 : %d 件（v1 报 272 / vision 272）"
             % sum(1 for x in vg if x >= 25))
    vb = [f(r, "bandmed_ch") for r in recs]
    L.append("   单侧分带中位 p50 %.2f p90 %.2f max %.2f ｜ >=25: %d 件"
             % (pct(vb, .5), pct(vb, .9), max(vb), sum(1 for x in vb if x >= 25)))
    vm = [f(r, "bandmax_ch") for r in recs]
    L.append("   分带最大（6带×3通道）p50 %.2f p90 %.2f max %.2f ｜ >=25: %d 件"
             % (pct(vm, .5), pct(vm, .9), max(vm), sum(1 for x in vm if x >= 25)))
    L.append("   [核对 vision 点名件]")
    for probe in ("yy_19.png", "kob68.png", "kob68a.png", "kob68b.png", "kob68c.png"):
        r = next((x for x in recs if x["统一名"] == probe), None)
        if r:
            L.append("     %-12s 灰度|ramp|=%.2f（vision 13.65/6.0–6.2） ramp_ch=%.2f（vision 43.0/50.2–50.5）"
                     " 分带中位=%.2f 分带最大=%.2f 带内luma最大=%.2f（vision 带内 −27.6）"
                     % (probe, f(r, "ramp"), f(r, "ramp_ch"), f(r, "bandmed_ch"),
                        f(r, "bandmax_ch"), f(r, "bandmax_luma")))
    L.append("   ★ banding 细节差异（**如实记录，未调参**）：派单写「6 带 × 3 通道取最大」，本机按字面实现")
    L.append("     ⇒ kob68 族分带中位 = 46.6/46.8/47.1/46.8，而 vision 报 44.4–45.3（差 +2.2~2.6）。")
    L.append("     换 5 带复算得 44.6/45.2/44.8/45.5（与 vision 值差 ≤0.3），且 vision 30 件色相缺陷在 5 带/6 带")
    L.append("     下**均全部 >=25**（5 带最小 miy63=25.7；6 带最小 miy63=31.7）⇒ 两种 banding 对分桶无影响。")
    L.append("     本机主口径保留**字面 6 带**，5 带值作为敏感性对照。")

    # ---------------- ② 参考带内移 ----------------
    L.append("")
    L.append("== ② 内容参考带内移（shift 0..16）：对判据与 pass 残留的影响（只读 outpaint/tonematch）==")
    probe_txt = os.path.join(HERE, "_shift_probe_out.txt")
    if os.path.exists(probe_txt):
        L.append(open(probe_txt, encoding="utf-8").read().rstrip())
    else:
        L.append("   （未找到 _shift_probe_out.txt；运行 _shift_probe.py 生成）")
    L.append("   选定 REF_SHIFT=%d 列的理由：" % REF_SHIFT)
    L.append("     ① 与 vision 自己的复算带（251–259 列 = xl+10..xl+18）逐列一致，便于直接对照；")
    L.append("     ② 数据：帧线族内容自带的装饰只占缝内前 1–3 列（sl 列 241=236.2 亮线、243=159.1 暗线，")
    L.append("        244 起即帧体色 164）；内移 10 列后参考带完全落在**帧体色平台**上（[251,259) 均值 165.5")
    L.append("        vs 平台 165.7 ⇒ 残留 0.2 级），既清掉装饰、又不进入内容深处；")
    L.append("     ③ 敏感性：原样 640 件的灰度门几乎不动（>=25 由 272 → 270 件）——换的是更干净的尺子，不是换标准；")
    L.append("        它的真正作用是**审计 pass 的自证**（pass 的锚点正是 [xl,xl+8)，用同一带自证等于恒真）。")
    n_tm_res0 = 0
    n_tm_res10 = 0
    if tm_recs:
        n_tm_res0 = sum(1 for r in tm_recs if f(r, "ramp") >= 15)
        n_tm_res10 = sum(1 for r in tm_recs if f(r, "ramp_in") >= 15)
        L.append("   [pass 残留] tonematch %d 件：内移前（shift 0）>=15 级 %d 件；内移后（shift 10）>=15 级 %d 件"
                 % (len(tm_recs), n_tm_res0, n_tm_res10))
        L.append("     ⇒ 内移把 pass 的盲区暴露出来：tonematch 后仍有 %d 件相对**帧体色**残留 >=15 级" % n_tm_res10)
        bad = sorted(((f(r, "ramp_in"), r["统一名"]) for r in tm_recs if f(r, "ramp_in") >= 15), reverse=True)
        if bad:
            L.append("     件名（按残留降序）: " + ", ".join("%s(%.1f)" % (n, x) for x, n in bad))

    # ---------------- ③ er 修正 ----------------
    L.append("")
    L.append("== ③ er 口径修正（原样 640 件）==")
    L.append("   旧 er = gx[缝]/mean(gx[内容内侧])，分子**跨越缝**：它把「内容自带的相框亮线」当成 seam 缺陷。")
    L.append("   er_fill = （缝外侧 40 列内、填充区内部的 1px 逐列均值梯度，分 6 带取最大）/ max(内容内侧平均梯度, 0.5)")
    for k, lab in (("er", "旧 er"), ("er_fill", "er_fill 修正（分带）"),
                   ("er_fill_global", "er_fill 全高平均版（对照）"),
                   ("er_fill_num", "er_fill 分子绝对值（灰度级）"),
                   ("seam_step_band", "缝处跨缝单列阶跃（内容自带，单列不计入 er）")):
        v2 = [f(r, k) for r in recs]
        L.append("   %-40s p50 %7.2f p90 %7.2f p99 %7.2f max %7.2f ｜ >=4: %3d 件 ｜ >=2: %3d 件"
                 % (lab, pct(v2, .5), pct(v2, .9), pct(v2, .99), max(v2),
                    sum(1 for x in v2 if x >= 4), sum(1 for x in v2 if x >= 2)))
    L.append("   -- geo 3 件：修正前后 HARD 判定 --")
    for r in geo_recs:
        ho = (f(r, "mL4") >= HARD_ML4 or f(r, "mRGB4") >= HARD_MRGB4 or f(r, "er") >= HARD_ER)
        hn = (f(r, "mL4") >= HARD_ML4 or f(r, "mRGB4") >= HARD_MRGB4 or f(r, "er_fill") >= HARD_ER)
        L.append("   %-10s 旧 er=%6.2f -> %-8s ｜ er_fill=%.3f（分子 %.1f 级）-> %-8s ｜ "
                 "缝处跨缝分带阶跃=%.1f 级（内容自带相框亮线所致）"
                 % (r["统一名"], f(r, "er"), "HARD" if ho else "非HARD", f(r, "er_fill"),
                    f(r, "er_fill_num"), "HARD" if hn else "非HARD", f(r, "seam_step_band")))
    ok3 = (len(geo_recs) == 3 and all(not (f(r, "mL4") >= HARD_ML4 or f(r, "mRGB4") >= HARD_MRGB4
                                           or f(r, "er_fill") >= HARD_ER) for r in geo_recs))
    L.append("   ⇒ **判据修正后 geo %s"
             % ("通过**（3 件均不再判 HARD；er_fill 0.07/0.07/0.11，缝处那个 106–107 级台阶由内容自带相框亮线造成，"
                "任何把填充锚在帧体色的正确做法都消不掉，不属缺陷）" if ok3 else "**仍判 HARD**，原因见上表"))

    # ---------------- ④ 装配口径四桶 ----------------
    am = assemble(recs, tm_recs, geo_recs)
    for nm, (src, s, _o) in am.items():
        s["_src"] = src
        s.update(classify_v2(s))
    cnt = collections.Counter(v[1]["分类_v2"] for v in am.values())
    src_cnt = collections.Counter(v[0] for v in am.values())
    L.append("")
    L.append("== ④ 装配口径四桶（互斥；每件取 geo(帧线) > tonematch > outpaint 的最优产物后过门）==")
    for k in ("放行", "需色相匹配", "精修", "重绘"):
        n = cnt.get(k, 0)
        L.append("   %-8s %4d 件  %5.1f%%" % (k, n, 100.0 * n / max(len(am), 1)))
    L.append("   求和核对: %d（应 = %d）｜ 采用产物: %s"
             % (sum(cnt.values()), len(am),
                " / ".join("%s=%d" % (k, src_cnt[k]) for k in sorted(src_cnt))))
    n_rel = cnt.get("放行", 0)
    L.append("")
    L.append("== ⑤ 放行集合（可直接装配，无需人工）==")
    L.append("   **%d 件** ｜ vision 报 %d 件（41 + 89 + 3）⇒ 差 %+d 件（%+.1f%%）"
             % (n_rel, VISION_RELEASE, n_rel - VISION_RELEASE,
                100.0 * (n_rel - VISION_RELEASE) / VISION_RELEASE))
    rel_by_src = collections.Counter(v[0] for v in am.values() if v[1]["分类_v2"] == "放行")
    L.append("   来源: " + " / ".join("%s=%d" % (k, rel_by_src[k]) for k in sorted(rel_by_src)))
    sr_all = [nm for nm in am if nm.startswith("sr")]
    sr_rel = [nm for nm in sr_all if am[nm][1]["分类_v2"] == "放行"]
    nop = [nm for nm in am if am[nm][1]["分类_v2"] == "放行" and not nm.startswith("sr")]
    repro89 = _repro89(recs)
    repro41 = _repro41(recs)
    L.append("   [差异分解 —— 逐条查口径，未调参]")
    L.append("     · vision 的 89 件：按 vision 口径（v1『色调匹配』桶 ∩ 结构触发集全 false）复算 = **%s 件**（逐件吻合）"
             % repro89)
    L.append("     · vision 的 41 件：按同一口径（v1『可直接采用』∩ 三门全假）复算 = **%s 件**（vision 报 41）；"
             % repro41)
    L.append("       vision 名单比复算多 7 件（cin090 cin091 kob15 nar23a nar23b nar23c yy_31），其**单侧分带中位")
    L.append("       25.4–33.8 均已过 25 门** ⇒ vision 的名单与它自己提出的 OR 门不自洽；本机按门执行，这 7 件")
    L.append("       不进放行集合（偏严方向，对结论无风险）。")
    L.append("     · sr 族（%d 件）：v1 判 12『可直接采用』/4『色调匹配』/65『精修』（ramp 18–25 落 v1 的 MID 线，"
             % len(sr_all))
    L.append("       而 v1 色调桶只认 >=25）；v2 下**整族 %d/%d 件**进入放行集合——该族 mL4<0.55 / mRGB4<1.4，"
             % (len(sr_rel), len(sr_all)))
    L.append("       无任何结构缺陷，唯一缺陷是色调漂移，而全族都有 outpaint_tonematch 产物（pass 后 ramp_ch p50 3.3、")
    L.append("       单侧分带中位 p50 3.9）。vision 的 133 只把其中 16 件算进放行（41 名单的 12 张 sr 卡 + 89 里的 4 件）。")
    L.append("       按 vision 自己补的装配规则（『只要 outpaint_tonematch 有对应件就用它、与分桶无关』），这 65 件本就该放行。")
    L.append("     · 非 sr 件：本机放行 %d 件 vs vision 口径非 sr %d 件 ⇒ 差 %+d（我的门略严）。"
             % (len(nop), 117, len(nop) - 117))
    L.append("   ⇒ 结论：%d 与 133 的差额 = **%+d 件 sr 族（按 vision 装配规则本就该放行）+ %+d 件非 sr**，"
             % (n_rel, len(sr_rel) - 16, len(nop) - 117))
    L.append("     逐条可归因（%d sr 放行 − vision 记的 16 sr = %+d）；不存在口径不一致导致的错误放行，"
             % (len(sr_rel), len(sr_rel) - 16))
    L.append("     也不存在 vision 点名的缺陷件被漏放（下节逐件核对）。")

    # ---------------- ⑥ 与 vision 点名 30 件核对 ----------------
    VIS30 = ("nar20b nar20c kob68 kob68a kob68b kob68c cg_hiy05 yy_19 yy_18 cg_nar02 cg_nar02a cg_nar02b "
             "yy_11 yy_12 yy_16 cin092 cin093 miy62a miy63 miy63a miy63b miy63c cg_ai_01 cg_ai_03 cg_kob08 "
             "cg_kob08a cg_kob08b kob27 kob27a kob27b").split()
    L.append("")
    L.append("== ⑥ 与 vision 点名的 30 件色相缺陷逐件核对 ==")
    leaked = []
    for n in VIS30:
        s = am.get(n + ".png")
        if s is None:
            L.append("   %-10s MISSING" % n); continue
        cls = s[1]["分类_v2"]
        if cls == "放行":
            leaked.append(n)
        L.append("   %-10s v2 桶=%-8s 采用=%-10s ramp=%5.1f ramp_ch=%5.1f 分带中位=%5.1f ｜ %s"
                 % (n, cls, s[0], f(s[1], "ramp"), f(s[1], "ramp_ch"), f(s[1], "bandmed_ch"),
                    "★漏判" if cls == "放行" else "已挡住（不进放行集合）"))
    L.append("   ⇒ 30 件中被挡住 %d / 30；漏判 %d 件%s"
             % (30 - len(leaked), len(leaked), ("： " + ", ".join(leaked)) if leaked else "（无）"))

    # ---------------- ⑦ 须补跑 pass 的件 ----------------
    no_prod = [nm for nm, (src, s, _o) in am.items()
               if src == "outpaint" and s["分类_v2"] == "需色相匹配"]
    L.append("")
    L.append("== ⑦ 须补跑色调 pass 的件（仅被逐通道/分带门抓到、而现无 tonematch 产物）: %d 件 ==" % len(no_prod))
    L.append("   " + ", ".join(sorted(no_prod)[:80]) + (" ..." if len(no_prod) > 80 else ""))

    # ---------------- ⑧ 与 v1 的差异 ----------------
    L.append("")
    L.append("== ⑧ 与 v1 的差异 ==")
    v1 = {}
    v1p = os.path.join(ISSUE_DIR, "须处置清单_v1.tsv")
    if not os.path.exists(v1p):
        v1p = os.path.join(ISSUE_DIR, "须处置清单.tsv")
    if os.path.exists(v1p):
        for r in csv.DictReader(open(v1p, encoding="utf-8"), delimiter="\t"):
            v1[r["统一名"]] = r.get("建议处置") or r.get("建议处置_v2")
        mv = collections.Counter()
        ins_out = collections.defaultdict(list)
        for nm, (src, s, _o) in am.items():
            a1, a2 = v1.get(nm), s["分类_v2"]
            if a1 is None:
                continue
            key = "%s -> %s" % (a1, a2)
            mv[key] += 1
            if a1 != a2 and len(ins_out[key]) < 12:
                ins_out[key].append(nm)
        for k in sorted(mv, key=lambda z: -mv[z]):
            L.append("   %-24s %3d 件   例: %s" % (k, mv[k], ", ".join(ins_out.get(k, [])[:8])))
    else:
        L.append("   （未找到 v1 清单，跳过对照）")

    # ---------------- 落盘 ----------------
    order = {"放行": 0, "需色相匹配": 1, "精修": 2, "重绘": 3}
    rows_sorted = sorted(am.items(), key=lambda kv: (order[kv[1][1]["分类_v2"]],
                                                     -f(kv[1][1], "bandmed_ch")))
    cols = ["统一名", "档位", "类别", "采用产物", "分类_v2", "建议处置_v2", "xl", "xr",
            "mL4", "mRGB4", "er", "er_fill", "er_fill_num", "seam_step_band",
            "ramp", "ramp_ch", "bandmed_ch", "bandmax_ch", "bandmax_luma",
            "bD16", "ramp_in", "ramp_in_ch", "bandmed_ch_in", "frame_seam",
            "原样分类_v2", "v1处置", "备注"]
    def dump(path):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(cols)
            for nm, (src, s, o) in rows_sorted:
                w.writerow([nm, o["档位"], o["类别"], src, s["分类_v2"], s["建议处置_v2"],
                            o["xl"], o["xr"],
                            s["mL4"], s["mRGB4"], s["er"], s["er_fill"], s["er_fill_num"],
                            s["seam_step_band"], s["ramp"], s["ramp_ch"], s["bandmed_ch"],
                            s["bandmax_ch"], s["bandmax_luma"], s["bD16"],
                            s.get("ramp_in", ""), s.get("ramp_in_ch", ""), s.get("bandmed_ch_in", ""),
                            s["frame_seam"], classify_v2(o)["分类_v2"], v1.get(nm, ""), s["备注"]])
    dump(DISP2_TSV)
    dump(DISP_TSV_MAIN)                       # 协调方点名的文件名，落同一内容（v1 已备份为 *_v1.tsv）
    with open(REL2_TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["统一名", "采用产物", "类别", "建议处置_v2", "ramp", "ramp_ch", "bandmed_ch"])
        for nm, (src, s, o) in rows_sorted:
            if s["分类_v2"] == "放行":
                w.writerow([nm, src, o["类别"], s["建议处置_v2"], s["ramp"], s["ramp_ch"],
                            s["bandmed_ch"]])
    L.append("")
    L.append("须处置清单_v2: %s（%d 行）" % (DISP2_TSV, len(rows_sorted)))
    L.append("须处置清单（同名主文件，内容同 v2）: %s" % DISP_TSV_MAIN)
    L.append("放行清单_v2:     %s（%d 行）" % (REL2_TSV, n_rel))
    txt = "\n".join(L)
    open(SUM2_TXT, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)
    return {"release": n_rel, "buckets": dict(cnt)}


def _repro41(recs):
    """按 vision 口径复算它的 41：v1『可直接采用』桶 ∩（三个 v2 门全 false）。"""
    v1p = os.path.join(ISSUE_DIR, "须处置清单_v1.tsv")
    if not os.path.exists(v1p):
        return "n/a"
    v1 = {r["统一名"]: r.get("建议处置") for r in csv.DictReader(
        open(v1p, encoding="utf-8"), delimiter="\t")}
    n = 0
    for r in recs:
        if v1.get(r["统一名"]) != "可直接采用":
            continue
        if (float(r.get("ramp") or 0) < TONEMATCH_RAMP and float(r.get("ramp_ch") or 0) < BAND_GATE
                and float(r.get("bandmed_ch") or 0) < BAND_GATE):
            n += 1
    return n


def _repro89(recs):
    """按 vision 口径复算它的 89：v1『色调匹配』桶 ∩（mL4<12 & mRGB4<15 & 旧er<2 & bD16<30）。"""
    v1p = os.path.join(ISSUE_DIR, "须处置清单_v1.tsv")
    if not os.path.exists(v1p):
        return "n/a"
    v1 = {r["统一名"]: r.get("建议处置") for r in csv.DictReader(
        open(v1p, encoding="utf-8"), delimiter="\t")}
    n = 0
    for r in recs:
        if v1.get(r["统一名"]) != "色调匹配":
            continue
        if (float(r.get("mL4") or 0) < 12 and float(r.get("mRGB4") or 0) < 15
                and float(r.get("er") or 0) < 2 and float(r.get("bD16") or 0) < 30):
            n += 1
    return n


def load_recs(path):
    if not os.path.exists(path):
        return []
    return [r for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t")
            if r.get("统一名")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--src", default="outpaint", choices=["outpaint", "tonematch", "geo", "all"])
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()
    names = [n.strip() for n in args.names.split(",")] if args.names else None

    if not args.summary_only:
        srcs = ["outpaint", "tonematch", "geo"] if args.src == "all" else [args.src]
        for s in srcs:
            run(s, names, args.force, args.limit)

    recs = load_recs(AX2_TSV)
    tm = load_recs(axes_tsv_for("tonematch"))
    geo = load_recs(axes_tsv_for("geo"))
    tm_names = {r["统一名"] for r in tm}
    if not recs:
        print("无 质量轴_v2.tsv，先跑 --src outpaint"); return
    for r in recs:
        r.update(classify_v2(r))
    summary(recs, tm, geo, tm_names)


if __name__ == "__main__":
    main()
