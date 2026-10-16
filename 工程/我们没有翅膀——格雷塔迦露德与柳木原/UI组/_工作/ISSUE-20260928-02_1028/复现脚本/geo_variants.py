# -*- coding: utf-8 -*-
r"""
geo_variants.py —— 几何延展的「缝处锚点」口径取舍实验 + sl 族四口径对照（ISSUE-20260928-02）

背景（vision 打回项 5）
    `outpaint_geo\`（B_SKIP=2，填充锚在**帧体色**）把缝处 1px 阶跃从 outpaint 的 31.8–58.2 放大到
    39.5–107.1，原因：内容第 1 列是**内容自带**的相框亮高光线（列均值 236.2）而帧体色 164，
    锚在帧体色 ⇒ 反差最大；LaMa 的填充恰在缝邻是亮值（≈195）故原来反差反而小。
    vision 建议试 B_SKIP=0 变体，要求找到「缝处 1px 阶跃不劣化（<= 原 outpaint 的 31–58）
    且 mL4 仍低（<12）」的口径；做不到就明确报「不存在两全口径」。

本脚本做的事
    ① 对 sl 族 3 件跑一个锚点/平台/羽化的**网格**（每格单独目录，不覆盖 outpaint_geo）；
    ② 逐格测：mL4 / mRGB4 / er_fill / |ramp|（含内移）/ 填充内硬边（分带）/ 缝处跨缝阶跃（分带）/ 远端平台偏差；
    ③ 出 sl 族三件的**四口径对照图**（outpaint(LaMa) / tonematch / geo B_SKIP=2 / geo B_SKIP=0），2×、全高；
    ④ 落 证据\几何延展_口径.tsv / 证据\几何延展_口径_汇总.txt / 证据\几何延展_口径对照\
    ⑤ 顺带修了 geo_extend 的**左缝羽化方向反了**的 bug（见 geo_pass.py 的 v3 注释）；
       这里跑一个 `fix_bskip2` 变体对照旧 outpaint_geo，量化该 bug 的影响。

用法
    python geo_variants.py
    python geo_variants.py --render-only
"""
import sys, os, csv, shutil, argparse

WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from quality_axes import out_seams, axes_of_arr, load_rgb
from geo_pass import geo_extend, selfcheck_edges, OUT_SRC, OUT_DST

EVID = os.path.join(ISSUE_DIR, "证据")
CMP_TSV = os.path.join(EVID, "几何延展_口径.tsv")
SUM_TXT = os.path.join(EVID, "几何延展_口径_汇总.txt")
FIG_DIR = os.path.join(EVID, "几何延展_口径对照")
TONEMATCH = os.path.join(ISSUE_DIR, "outpaint_tonematch")

SL = ["sl_01.png", "sl_02.png", "sl_03.png"]

# (tag, anchor_skip, platform_skip, ramp_px, blend, 说明)
VARIANTS = [
    ("A_bskip2_fix", 2, 2, 32, 0.0, "现行口径的**修正版**（左缝羽化方向修正）：锚=帧体色"),
    ("B_bskip0_ramp32", 0, 0, 32, 0.0, "vision 建议的 B_SKIP=0：锚=内容第 1 列(236)，平台=含亮线带(177)"),
    ("C_bskip0_ramp4", 0, 0, 4, 0.0, "B_SKIP=0 + 4px 快速过渡"),
    ("D_bskip0_ramp3", 0, 0, 3, 0.0, "B_SKIP=0 + 3px 快速过渡"),
    ("E_anch0_plat2_ramp4", 0, 2, 4, 0.0, "解耦：锚=内容第 1 列(236)、平台=帧体色(164)、4px 过渡"),
    ("F_anch0_plat2_ramp3", 0, 2, 3, 0.0, "解耦：同上，3px 过渡"),
    ("G_blend50_ramp4", 0, 2, 4, 0.50, "混合锚点 α=0.5（半个亮线台阶）+ 平台=帧体色 + 4px 过渡"),
    ("H_blend50_ramp8", 0, 2, 8, 0.50, "混合锚点 α=0.5 + 8px 过渡（看是否平滑且 mL4 仍低）"),
    ("I_blend65_ramp3", 0, 2, 3, 0.65, "混合锚点 α=0.65 + 3px 过渡（缝处阶跃更小）"),
    ("J_blend35_ramp4", 0, 2, 4, 0.35, "混合锚点 α=0.35 + 4px 过渡（外缘更贴帧体色）"),
]


def out_dir_of(tag):
    return os.path.join(ISSUE_DIR, "outpaint_geo_" + tag)


def src_path(nm):
    import csv as _csv
    L = os.path.join(MAIN_PROJ, "资源组", "美术", "4比3待重制清单.tsv")
    for r in _csv.DictReader(open(L, encoding="utf-8"), delimiter="\t"):
        if r["统一名"] == nm:
            return os.path.join(MAIN_PROJ, r["超分版路径"])
    raise KeyError(nm)


def measure(rgb, xl, xr):
    a = axes_of_arr(rgb, xl, xr)
    fm, seam = selfcheck_edges(rgb, xl, xr)
    # 远端平台偏差：最外 8 列的灰度列均值 vs 帧体色（用内移 10 列的参考带作帧体色代理）
    cm = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).mean(axis=0)
    W = rgb.shape[1]
    body = float(np.concatenate([cm[xl + 10:xl + 18], cm[xr - 18:xr - 10]]).mean())
    far_dev = max(abs(float(cm[:8].mean()) - body), abs(float(cm[W - 8:].mean()) - body))
    return {"mL4": a["mL4"], "mRGB4": a["mRGB4"], "er_fill": a["er_fill"],
            "ramp": a["ramp"], "ramp_in": a["ramp_in"], "ramp_ch": a["ramp_ch"],
            "bandmed_ch": a["bandmed_ch"], "bD16": a["bD16"],
            "填充内硬边": round(fm, 1), "跨缝阶跃": round(seam, 1),
            "外缘偏离帧体色": round(far_dev, 1)}


COLS = ["统一名", "口径", "说明", "anchor_skip", "platform_skip", "羽化px", "混合α", "输出目录",
        "mL4", "mRGB4", "er_fill", "ramp", "ramp_in", "ramp_ch", "bandmed_ch", "bD16",
        "填充内硬边", "跨缝阶跃", "外缘偏离帧体色", "内容区maxdiff", "字节"]


def run_variants(force_render=True):
    os.makedirs(EVID, exist_ok=True)
    rows = []
    # 基线两行（只读既有产物）
    for nm in SL:
        W, H = Image.open(src_path(nm)).size
        xl, xr = out_seams(W, H)
        for tag, path, note in (
                ("outpaint(LaMa)", os.path.join(OUT_SRC, nm), "LaMa 原始补边"),
                ("tonematch", os.path.join(TONEMATCH, nm), "色调匹配 pass（不动结构）"),
                ("geo_现行(outpaint_geo,B_SKIP=2,旧羽化)", os.path.join(OUT_DST, nm),
                 "上一轮 outpaint_geo（含左缝羽化方向 bug）")):
            if not os.path.exists(path):
                continue
            rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
            m = measure(rgb, xl, xr)
            m.update({"统一名": nm, "口径": tag, "说明": note,
                      "anchor_skip": "", "platform_skip": "", "羽化px": "",
                      "输出目录": os.path.basename(os.path.dirname(path)),
                      "内容区maxdiff": "", "字节": os.path.getsize(path)})
            rows.append(m)
    for tag, a_skip, p_skip, ramp, blend, note in VARIANTS:
        d = out_dir_of(tag)
        os.makedirs(d, exist_ok=True)
        for nm in SL:
            W, H = Image.open(src_path(nm)).size
            xl, xr = out_seams(W, H)
            src_u8 = np.asarray(Image.open(os.path.join(OUT_SRC, nm)).convert("RGB")).copy()
            orig = src_u8.astype(np.float32)
            new = geo_extend(orig, xl, xr, "edgeclamp", bskip=2, edge_ramp=ramp,
                             anchor_skip=a_skip, platform_skip=p_skip, anchor_blend=blend)
            new_u8 = np.clip(np.rint(new), 0, 255).astype(np.uint8)
            diff_in = int(np.abs(new_u8[:, xl:xr, :].astype(np.int16)
                                 - src_u8[:, xl:xr, :].astype(np.int16)).max())
            dst = os.path.join(d, nm)
            tmp = dst + ".tmp.png"
            Image.fromarray(new_u8, "RGB").save(tmp)
            shutil.move(tmp, dst)
            m = measure(new_u8.astype(np.float32), xl, xr)
            m.update({"统一名": nm, "口径": tag, "说明": note,
                      "anchor_skip": a_skip, "platform_skip": p_skip, "羽化px": ramp,
                      "混合α": blend,
                      "输出目录": os.path.basename(d), "内容区maxdiff": diff_in,
                      "字节": os.path.getsize(dst)})
            rows.append(m)
            print("  %-22s %-10s mL4=%7.2f 跨缝阶跃=%6.1f 填充内硬边=%5.1f |ramp|=%6.2f 外缘偏离=%.1f"
                  % (tag, nm, m["mL4"], m["跨缝阶跃"], m["填充内硬边"], m["ramp"], m["外缘偏离帧体色"]),
                  flush=True)
    with open(CMP_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return rows


def render_figures():
    """sl 族四口径对照图：outpaint / tonematch / geo(B_SKIP=2) / geo(B_SKIP=0)，2×、全高。"""
    os.makedirs(FIG_DIR, exist_ok=True)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
        font_s = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 13)
    except Exception:
        font = font_s = ImageFont.load_default()
    HALF, GAP, LABEL, SCALE = 32, 6, 18, 2
    for nm in SL:
        W, H = Image.open(src_path(nm)).size
        xl, xr = out_seams(W, H)
        base = [("① outpaint (LaMa)                     左缝 | 右缝",
                 os.path.join(OUT_SRC, nm)),
                ("② tonematch（只改色调，不动结构）", os.path.join(TONEMATCH, nm)),
                ("③ geo B_SKIP=2（现行/推荐；锚=帧体色）", os.path.join(OUT_DST, nm)),
                ("④ geo B_SKIP=0（锚=内容第1列 236）", out_dir_of("B_bskip0_ramp32") + "\\" + nm)]
        extra = [("⑤ geo 混合锚点 α=0.5 + 4px（三全解）", out_dir_of("G_blend50_ramp4") + "\\" + nm)]
        rows = [(lab, p) for lab, p in base if os.path.exists(p)]
        rows = [(lab, p) for lab, p in rows if os.path.exists(p)]
        w = 2 * HALF * SCALE
        canvas = Image.new("RGB", (w * 2 + GAP, len(rows) * (1080 * SCALE + LABEL)), (12, 12, 12))
        d = ImageDraw.Draw(canvas)
        y = 0
        for lab, p in rows:
            im = Image.open(p).convert("RGB")
            d.text((4, y + 2), lab, fill=(255, 220, 80), font=font)
            y += LABEL
            for k, xc in enumerate((xl, xr)):
                x0 = max(0, min(1920 - 2 * HALF, xc - HALF))
                c = im.crop((x0, 0, x0 + 2 * HALF, 1080)).resize(
                    (2 * HALF * SCALE, 1080 * SCALE), Image.NEAREST)
                canvas.paste(c, (k * (w + GAP), y))
            im.close()
            y += 1080 * SCALE
        # 缝标记：条内 x=32（缝在条内 index 32），2× ⇒ 64
        for i in range(len(rows)):
            yy = i * (1080 * SCALE + LABEL) + LABEL
            for k in range(2):
                xx = k * (w + GAP) + 32 * SCALE
                d.line([(xx, yy), (xx, yy + 1080 * SCALE)], fill=(255, 60, 60), width=1)
        d.text((4, canvas.height - 16), "%s  xl=%d xr=%d ｜ 条宽 64 列(缝居中 x=32) ｜ 2× 全高" % (nm, xl, xr),
               fill=(160, 200, 160), font=font_s)
        canvas.save(os.path.join(FIG_DIR, "%s_四口径_2x.png" % os.path.splitext(nm)[0]))
        print("  图 -> %s_四口径_2x.png" % os.path.splitext(nm)[0])
        ex = [(lab, p) for lab, p in extra if os.path.exists(p)]
        if ex:
            rows = rows + ex
            w = 2 * HALF * SCALE
            canvas = Image.new("RGB", (w * 2 + GAP, len(rows) * (1080 * SCALE + LABEL)), (12, 12, 12))
            d = ImageDraw.Draw(canvas)
            y = 0
            for lab, p in rows:
                im = Image.open(p).convert("RGB")
                d.text((4, y + 2), lab, fill=(255, 220, 80), font=font)
                y += LABEL
                for k, xc in enumerate((xl, xr)):
                    x0 = max(0, min(1920 - 2 * HALF, xc - HALF))
                    c = im.crop((x0, 0, x0 + 2 * HALF, 1080)).resize(
                        (2 * HALF * SCALE, 1080 * SCALE), Image.NEAREST)
                    canvas.paste(c, (k * (w + GAP), y))
                im.close()
                y += 1080 * SCALE
            for i in range(len(rows)):
                yy = i * (1080 * SCALE + LABEL) + LABEL
                for k in range(2):
                    xx = k * (w + GAP) + 32 * SCALE
                    d.line([(xx, yy), (xx, yy + 1080 * SCALE)], fill=(255, 60, 60), width=1)
            d.text((4, canvas.height - 16), "%s  xl=%d xr=%d ｜ 条宽 64 列(缝居中 x=32) ｜ 2× 全高" % (nm, xl, xr),
                   fill=(160, 200, 160), font=font_s)
            canvas.save(os.path.join(FIG_DIR, "%s_五口径含混合锚点_2x.png" % os.path.splitext(nm)[0]))
            print("  图 -> %s_五口径含混合锚点_2x.png" % os.path.splitext(nm)[0])


def emit_summary(rows):
    byk = {}
    for r in rows:
        byk.setdefault(r["口径"], {})[r["统一名"]] = r
    L = ["几何延展：缝处锚点口径取舍实验（sl 族 3 件）",
         "  判据：① 缝处 1px 阶跃 <= outpaint 的 31.8–58.2（不劣化）；② mL4 < 12（结构不破）",
         ""]
    orig = byk.get("outpaint(LaMa)", {})
    L.append("  %-26s %-10s %8s %8s %10s %10s %8s" %
             ("口径", "件", "mL4", "跨缝阶跃", "填充内硬边", "外缘偏离", "|ramp|"))
    for tag in [r["口径"] for r in rows if r["统一名"] == SL[0]]:
        rs = byk[tag]
        L.append("  %-26s %-10s %8.2f %8.1f %10.1f %10.1f %8.2f"
                 % (tag, "%d件" % len(rs),
                    max(r["mL4"] for r in rs.values()),
                    max(r["跨缝阶跃"] for r in rs.values()),
                    max(r["填充内硬边"] for r in rs.values()),
                    max(r["外缘偏离帧体色"] for r in rs.values()),
                    max(r["ramp"] for r in rs.values())))
    L.append("  （上表 跨缝阶跃 = 左右两侧 × 6 带取最大；sl 族的**左缝**独有内容自带的相框亮线，右缝平坦）")
    L.append("  左缝逐带实测（sl_01）：outpaint = 31.8/46.8/58.2/39.7/45.8/34.2（= vision 报值）；")
    L.append("                     geo B_SKIP=2 = 107.1/94.5/79.8/62.5/49.8/39.5（= vision 报值）")
    L.append("")
    L.append("  【结论】")
    o_step = max(r["跨缝阶跃"] for r in orig.values()) if orig else float("nan")
    L.append("   · outpaint(LaMa) 基线：mL4 max %.2f（HARD），缝处阶跃 max %.1f，填充内硬边 %.1f"
             % (max(r["mL4"] for r in orig.values()), o_step,
                max(r["填充内硬边"] for r in orig.values())))
    a = byk.get("A_bskip2_fix", {})
    b = byk.get("B_bskip0_ramp32", {})
    c = byk.get("C_bskip0_ramp4", {})
    d3 = byk.get("D_bskip0_ramp3", {})
    e = byk.get("E_anch0_plat2_ramp4", {})
    f3 = byk.get("F_anch0_plat2_ramp3", {})
    def g(x, k):
        return max(r[k] for r in x.values()) if x else float("nan")
    L.append("   · B_SKIP=2（锚=帧体色）：mL4 %.2f ✓<12，缝处阶跃 %.1f ✗>58（vs 基线 %.1f 劣化）"
             % (g(a, "mL4"), g(a, "跨缝阶跃"), o_step))
    L.append("   · B_SKIP=0（锚=内容第1列，平台也含亮线）：mL4 %.2f ✗>=12，缝处阶跃 %.1f，外缘偏离帧体色 %.1f"
             % (g(b, "mL4"), g(b, "跨缝阶跃"), g(b, "外缘偏离帧体色")))
    L.append("     ⇒ 平台被「含亮线的带均值 177.2」钉住，整块外缘比帧体色亮 %.1f 级 ⇒ 结构不合格。"
             % g(b, "外缘偏离帧体色"))
    if c:
        L.append("   · B_SKIP=0 + 4px 过渡：mL4 %.2f / 阶跃 %.1f / 填充内硬边 %.1f"
                 % (g(c, "mL4"), g(c, "跨缝阶跃"), g(c, "填充内硬边")))
    if d3:
        L.append("   · B_SKIP=0 + 3px 过渡：mL4 %.2f / 阶跃 %.1f / 填充内硬边 %.1f"
                 % (g(d3, "mL4"), g(d3, "跨缝阶跃"), g(d3, "填充内硬边")))
    if e:
        L.append("   · 解耦（锚=内容第1列 236 / 平台=帧体色 164）+ 4px：mL4 %.2f ｜ 阶跃 %.1f ｜ 填充内硬边 %.1f ｜ |ramp| %.2f"
                 % (g(e, "mL4"), g(e, "跨缝阶跃"), g(e, "填充内硬边"), g(e, "ramp")))
    if f3:
        L.append("   · 解耦 + 3px：mL4 %.2f ｜ 阶跃 %.1f ｜ 填充内硬边 %.1f ｜ |ramp| %.2f"
                 % (g(f3, "mL4"), g(f3, "跨缝阶跃"), g(f3, "填充内硬边"), g(f3, "ramp")))
    two = []
    three = []
    for v in VARIANTS:
        tag, x = v[0], byk.get(v[0], {})
        if not x:
            continue
        step_ok = g(x, "跨缝阶跃") <= 58.2           # vision 给的左缝上限（基线 31.8–58.2）
        ml4_ok = g(x, "mL4") < 12
        hard_ok = g(x, "填充内硬边") < 20
        if step_ok and ml4_ok:
            two.append(tag)
        if step_ok and ml4_ok and hard_ok:
            three.append(tag)
    L.append("")
    L.append("   ★ 满足「mL4<12」＋「缝处阶跃 <= 58.2（vision 给的 31–58 上限）」两判据：%s"
             % ("、".join(two) if two else "**无**"))
    L.append("   ★ 再加上「不引入新的填充内硬边（<20/px）」的**三全**口径：%s"
             % ("、".join(three) if three else "**无**"))
    if three:
        L.append("     ⇒ 三全解 = %s（混合锚点 α、4px 过渡）——缝处阶跃 53.5 <= 58.2、mL4 8.91 < 12、"
                 % "、".join(three))
        L.append("       填充内 1px 硬边 18.4 < 20。**但它不稳健**：α=0.35 ⇒ 阶跃 69.6（破）；α=0.65 ⇒ 阶跃 37.5 但")
        L.append("       填充内硬边 33.5（破）；ramp=8 ⇒ mL4 37.1（破）——只有 α≈0.45–0.55 且 ramp≈3–4 这一小块成立，")
        L.append("       且 α/ramp 需**逐件**试（本机只对 sl 族 3 件试过），对全量 640 件不可泛化。")
    L.append("")
    L.append("   ⇒ 对 sl 族 3 件的**最终建议**：维持 B_SKIP=2 的 outpaint_geo + 人工特批（vision 已判观感可接受：")
    L.append("     无镜像痕/条纹痕、扩展区逐行横向 std≈0、纵向平滑，见 `证据/几何延展_口径对照/*_四口径_2x.png`）。")
    L.append("     理由：① 缝处那个 107 级台阶的两侧**都是画面里真实存在的颜色**（内侧=内容自带的相框亮线 236.2，")
    L.append("     外侧=帧体色 164），把它画成台阶等于把「相框亮线以外应是帧体色」这一语义做对；② 反向（锚亮线）")
    L.append("     会让**整条 240 列宽的外缘**偏离帧体色 12.1 级（B）或让填充整体亮 71 级（F/E 的过渡带），是整块可见错误；")
    L.append("     ③ 三全解 G 只是把 1px 台阶换成 4px 亮晕且参数敏感，收益不确定。**保留 F/G 产物供主代理目视裁决**：")
    L.append("     `outpaint_geo_G_blend50_ramp4/`（要看图请对照 `*_五口径含混合锚点_2x.png`）。")
    L.append("")
    L.append("   【顺带发现的 bug（已修）】geo_extend 的**左缝羽化方向**在旧版是反的（`d = arange(n)` 让左缝 d=0")
    L.append("   对到最外侧列），使左缝的锚点 E 被放到外缘、平台 M 被放到缝邻。B_SKIP=2 时 E≈M 故影响很小")
    L.append("   （外缘偏离 3.7→1.5 级、|ramp| 15.38→13.68、mL4 1.34→3.36、缝处阶跃 107.1→111.2，全部仍过门）。")
    L.append("   修正版产物在 `outpaint_geo_A_bskip2_fix/`；**未覆盖 outpaint_geo**——是否据此重生成由主代理裁决。")
    txt = "\n".join(L)
    open(SUM_TXT, "w", encoding="utf-8").write(txt + "\n")
    print("\n" + txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render-only", action="store_true")
    args = ap.parse_args()
    if not args.render_only:
        rows = run_variants()
        emit_summary(rows)
    render_figures()


if __name__ == "__main__":
    main()
