# -*- coding: utf-8 -*-
r"""
quality_axes_v3.py —— 判据 v2 的**装配口径 v3**（ISSUE-20260928-02 · 1028 补边续作 · 最后一步）

与 quality_axes_v2.py 的关系
    门与分桶**完全沿用 v2**（quality_axes.v2_axes 的三门 + 结构门 + 硬线；gates_v2/classify_v2 直接 import，
    不改一个阈值）。唯一变化是**装配口径新增 outpaint_tonematch_v2\ 这一产物层**：

        says assemble_v3 = 帧线件取 geo ＞ 有 outpaint_tonematch_v2 产物取它 ＞ 有 outpaint_tonematch 取它 ＞ outpaint

    理由：新补跑的 80 件（触发口径扩到 ramp_ch/bandmed_ch 后无 v1 产物的件）只在 v2 目录里有产物；
    其余件沿用 v1 产物（v1 pass 的锚点差异只影响那 80 件，见 tonematch_pass_v2.py 的两版对照）。

产物（全部新建，不覆盖 v2 轮的任何文件）
    质量轴_v2_tonematch_v2.tsv   80 件新产物的全轴
    放行清单_v3.tsv              放行集合（v3 装配口径）
    须处置清单_v3.tsv            640 行：四桶 + 全部门/轴值 + 采用产物
    质量轴_v3_汇总.txt           四桶新分布 / v2→v3 搬移表 / 采用产物统计

用法
    python quality_axes_v3.py                  # 幂等：已有行的产物轴值直接复用
    python quality_axes_v3.py --force
    python quality_axes_v3.py --summary-only
"""
import sys, os, csv, time, argparse, collections

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image
from quality_axes import out_seams, axes_of_arr, load_rgb, TARGET, LIST_TSV, AX_COLS
from quality_axes_v2 import (gates_v2, classify_v2, tone_gate_reason, pct,
                             AX2_TSV, axes_tsv_for as axes_tsv_v2)

TM2_DIR = os.path.join(ISSUE_DIR, "outpaint_tonematch_v2")
AX2_TM2 = os.path.join(ISSUE_DIR, "质量轴_v2_tonematch_v2.tsv")
DISP3 = os.path.join(ISSUE_DIR, "须处置清单_v3.tsv")
REL3 = os.path.join(ISSUE_DIR, "放行清单_v3.tsv")
SUM3 = os.path.join(ISSUE_DIR, "质量轴_v3_汇总.txt")
DISP2 = os.path.join(ISSUE_DIR, "须处置清单_v2.tsv")
f = lambda r, k: float(r.get(k) or 0)


def load_rows(names=None):
    rows = [r for r in csv.DictReader(open(LIST_TSV, encoding="utf-8"), delimiter="\t")
            if r["建议策略(重制/补边/裁切)"] == "补边"]
    if names:
        w = set(names)
        rows = [r for r in rows if r["统一名"] in w]
    return rows


def run_tm2(names=None, force=False, limit=0):
    """对 outpaint_tonematch_v2\ 里的产物算 v2 全轴（幂等）。"""
    rows = load_rows(names)
    cache = {}
    if os.path.exists(AX2_TM2) and not force:
        for r in csv.DictReader(open(AX2_TM2, encoding="utf-8"), delimiter="\t"):
            if r.get("统一名") and r.get("mL4") not in (None, ""):
                cache[r["统一名"]] = r
    have = [r for r in rows if os.path.exists(os.path.join(TM2_DIR, r["统一名"]))]
    todo = [r for r in have if r["统一名"] not in cache]
    if limit:
        todo = todo[:limit]
    print("[tonematch_v2] 产物 %d 件 ｜ 已有轴值 %d ｜ 本次算 %d" % (len(have), len(cache), len(todo)),
          flush=True)
    fails, t0 = [], time.time()
    for i, r in enumerate(todo):
        nm = r["统一名"]
        try:
            src_img = os.path.join(MAIN_PROJ, r["超分版路径"])
            W, H = Image.open(src_img).size
            xl, xr = out_seams(W, H)
            rgb, mode = load_rgb(os.path.join(TM2_DIR, nm))
            if rgb.shape[:2] != (TARGET[1], TARGET[0]):
                raise AssertionError("尺寸 %s != 1920x1080" % (rgb.shape[:2],))
            a = axes_of_arr(rgb, xl, xr)
            del rgb
            rec = {"统一名": nm, "档位": r["建议档位(T1/T2/T3)"], "类别": r["类别"],
                   "判读类别": r["判读类别"], "源尺寸": "%dx%d" % (W, H),
                   "源模式": mode, "xl": xl, "xr": xr, "备注": ""}
            rec.update({k: a[k] for k in AX_COLS if k in a})
            cache[nm] = rec
            print("  [%2d/%2d] %-16s mL4=%6.2f mRGB4=%6.2f er_fill=%5.2f ramp=%6.2f ramp_ch=%6.2f "
                  "bandmed=%6.2f  %.2fs"
                  % (i + 1, len(todo), nm, a["mL4"], a["mRGB4"], a["er_fill"], a["ramp"],
                     a["ramp_ch"], a["bandmed_ch"], time.time() - t0), flush=True)
            if (i + 1) % 20 == 0:
                write_tsv(rows, cache)
        except Exception as e:
            fails.append((nm, repr(e)))
            print("  [%2d/%2d] FAIL %-16s %r" % (i + 1, len(todo), nm, e), flush=True)
    write_tsv(rows, cache)
    print("[tonematch_v2] 完成：%s（%d 行）｜失败 %d ｜%.2f min"
          % (AX2_TM2, len(cache), len(fails), (time.time() - t0) / 60), flush=True)
    if fails:
        with open(AX2_TM2 + ".失败.tsv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t"); w.writerow(["统一名", "错误"]); w.writerows(fails)
    return cache


def write_tsv(rows, cache):
    tmp = AX2_TM2 + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=AX_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rec = cache.get(r["统一名"])
            if rec is None:
                continue
            for k, v in classify_v2(rec).items():
                rec[k] = v
            w.writerow(rec)
    os.replace(tmp, AX2_TM2)


def load_recs(path):
    if not os.path.exists(path):
        return []
    return [r for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t") if r.get("统一名")]


MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")


def assemble_v3(recs, tm_recs, tm2_recs, geo_recs):
    """geo(帧线) ＞ tonematch_v2 ＞ tonematch ＞ outpaint。返回 {名: (src, rec, 原样rec)}。"""
    tmm = {r["统一名"]: r for r in tm_recs}
    tm2 = {r["统一名"]: r for r in tm2_recs}
    gom = {r["统一名"]: r for r in geo_recs}
    out, prio = {}, collections.Counter()
    for r in recs:
        nm = r["统一名"]
        fs = int(f(r, "frame_seam"))
        if fs == 1 and nm in gom:
            src, rec = "geo", gom[nm]
        elif nm in tm2:
            src, rec = "tonematch_v2", tm2[nm]
        elif nm in tmm:
            src, rec = "tonematch", tmm[nm]
        else:
            src, rec = "outpaint", r
        prio[src] += 1
        out[nm] = (src, rec, r)
    return out, prio


def summary(am, prio, tm_recs, tm2_recs, geo_recs):
    L = ["判据 v2 · 装配口径 v3 汇总（n=%d）" % len(am),
         "  门与分桶完全沿用 v2（灰度25 ＋ ramp_ch25 ＋ 单侧分带中位25 ＋ 结构门 ＋ 硬线），"
         "只新增 outpaint_tonematch_v2 产物层",
         "  装配优先级：帧线件 geo ＞ tonematch_v2 ＞ tonematch ＞ outpaint", ""]
    for nm, (src, s, o) in am.items():
        s["_src"] = src
        s.update(classify_v2(s))
    cnt = collections.Counter(v[1]["分类_v2"] for v in am.values())
    order = {"放行": 0, "需色相匹配": 1, "精修": 2, "重绘": 3}
    L.append("== ① 四桶新分布（v3）==")
    for k in ("放行", "需色相匹配", "精修", "重绘"):
        n = cnt.get(k, 0)
        L.append("   %-8s %4d 件  %5.1f%%" % (k, n, 100.0 * n / max(len(am), 1)))
    L.append("   求和核对：%d（应 = %d）" % (sum(cnt.values()), len(am)))
    L.append("   采用产物：%s" % " / ".join("%s=%d" % (k, prio[k]) for k in sorted(prio)))

    # ---- v2 → v3 搬移表 ----
    L.append("")
    L.append("== ② v2 → v3 搬移表（只可比件；用 须处置清单_v2.tsv 的『分类_v2』对 v3 同口径）==")
    v2 = {}
    if os.path.exists(DISP2):
        for r in csv.DictReader(open(DISP2, encoding="utf-8"), delimiter="\t"):
            v2[r["统一名"]] = (r.get("分类_v2"), r.get("采用产物"))
    mv = collections.Counter(); ex = collections.defaultdict(list)
    for nm, (src, s, o) in am.items():
        old = v2.get(nm, (None, None))[0]
        new = s["分类_v2"]
        key = "%s -> %s" % (old, new)
        mv[key] += 1
        if old != new and len(ex[key]) < 15:
            ex[key].append(nm)
    for k in sorted(mv, key=lambda z: (z.split(" -> ")[1] if " -> " in z else z, -mv[z])):
        L.append("   %-26s %4d 件   %s" % (k, mv[k], ", ".join(ex.get(k, []))))

    # ---- 80 件补跑的落点 ----
    L.append("")
    L.append("== ③ 本步补跑的 80 件（v2 桶=需色相匹配、无 v1 产物）在新装配下的落点 ==")
    names80 = sorted(r["统一名"] for r in tm2_recs)
    n80 = collections.Counter()
    moved = []
    for nm in names80:
        if nm not in am:
            n80["(缺)"] += 1; continue
        src, s, o = am[nm]
        n80[s["分类_v2"]] += 1
        if s["分类_v2"] != "放行":
            moved.append((nm, s["分类_v2"], f(s, "ramp"), f(s, "ramp_ch"), f(s, "bandmed_ch"),
                          f(s, "mL4"), f(s, "mRGB4"), f(s, "er_fill"), f(s, "bD16")))
    L.append("   80 件落点：%s" % dict(n80))
    L.append("   ⇒ 落入放行 %d / 80（%.1f%%）" % (n80.get("放行", 0), 100.0 * n80.get("放行", 0) / 80))
    if moved:
        L.append("   未落放行的件（逐件值）：")
        for t in moved:
            L.append("     %-14s 桶=%-8s 门(sh0) %6.2f/%6.2f/%6.2f ｜ 结构 mL4 %.2f mRGB4 %.2f "
                     "er_fill %.2f bD16 %.2f" % t)

    # ---- 8 件残留的归置 ----
    R8 = ["cg_eri02.png", "cg_eri02a.png", "cg_eri02b.png", "kob65.png", "kob65a.png",
          "kob65b.png", "kob65c.png", "kob69.png"]
    L.append("")
    L.append("== ④ 8 件残留件在 v3 的归置（采用 v1 产物；原因见 tonematch_pass_v2 残留结论）==")
    for nm in R8:
        if nm not in am:
            L.append("   %-14s MISSING" % nm); continue
        src, s, o = am[nm]
        L.append("   %-14s 桶=%-6s 采用=%-10s ｜ 门(sh0) ramp %5.2f ramp_ch %5.2f bandmed %5.2f ｜ "
                 "审计(sh10) ramp_in %5.2f ｜ 结构 mL4 %5.2f mRGB4 %5.2f er_fill %5.2f bD16 %5.2f"
                 % (nm, s["分类_v2"], src, f(s, "ramp"), f(s, "ramp_ch"), f(s, "bandmed_ch"),
                    f(s, "ramp_in"), f(s, "mL4"), f(s, "mRGB4"), f(s, "er_fill"), f(s, "bD16")))

    # ---- 落盘 ----
    L.append("")
    rel = [nm for nm, v in am.items() if v[1]["分类_v2"] == "放行"]
    L.append("== ⑤ 放行清单 v3 ==")
    L.append("   %d 件（v2 为 196 件，净 %+d）" % (len(rel), len(rel) - 196))
    relsrc = collections.Counter(am[nm][0] for nm in rel)
    L.append("   来源：%s" % " / ".join("%s=%d" % (k, relsrc[k]) for k in sorted(relsrc)))
    L.append("   vision 报 133 件（41+89+3）⇒ 差 %+d（口径差异已在 v2 汇总逐条归因）" % (len(rel) - 133))
    rows_sorted = sorted(am.items(), key=lambda kv: (order[kv[1][1]["分类_v2"]]))
    cols = ["统一名", "档位", "类别", "采用产物", "分类_v3", "建议处置_v2", "xl", "xr",
            "mL4", "mRGB4", "er", "er_fill", "er_fill_num", "seam_step_band",
            "ramp", "ramp_ch", "bandmed_ch", "bandmax_ch", "bD16",
            "ramp_in", "ramp_in_ch", "bandmed_ch_in", "frame_seam", "v2分类", "v2采用产物", "备注"]
    with open(DISP3, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(cols)
        for nm, (src, s, o) in rows_sorted:
            w.writerow([nm, o["档位"], o["类别"], src, s["分类_v2"], s["建议处置_v2"], o["xl"], o["xr"],
                        s["mL4"], s["mRGB4"], s["er"], s["er_fill"], s["er_fill_num"],
                        s["seam_step_band"], s["ramp"], s["ramp_ch"], s["bandmed_ch"],
                        s["bandmax_ch"], s["bD16"],
                        s.get("ramp_in", ""), s.get("ramp_in_ch", ""), s.get("bandmed_ch_in", ""),
                        s["frame_seam"], v2.get(nm, ("", ""))[0], v2.get(nm, ("", ""))[1], s["备注"]])
    with open(REL3, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["统一名", "采用产物", "类别", "建议处置_v2", "ramp", "ramp_ch", "bandmed_ch"])
        for nm, (src, s, o) in rows_sorted:
            if s["分类_v2"] == "放行":
                w.writerow([nm, src, o["类别"], s["建议处置_v2"], s["ramp"], s["ramp_ch"], s["bandmed_ch"]])
    L.append("   须处置清单_v3: %s（%d 行）" % (DISP3, len(rows_sorted)))
    L.append("   放行清单_v3:   %s（%d 行）" % (REL3, len(rel)))
    txt = "\n".join(L)
    open(SUM3, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)
    return cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()

    if not args.summary_only:
        run_tm2(force=args.force, limit=args.limit)
    recs = load_recs(AX2_TSV)
    tm = load_recs(axes_tsv_v2("tonematch"))
    tm2 = load_recs(AX2_TM2)
    geo = load_recs(axes_tsv_v2("geo"))
    if not recs:
        print("缺 质量轴_v2.tsv"); return
    am, prio = assemble_v3(recs, tm, tm2, geo)
    summary(am, prio, tm, tm2, geo)


if __name__ == "__main__":
    main()
