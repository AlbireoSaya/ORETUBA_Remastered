# -*- coding: utf-8 -*-
r"""
verify_pilot.py —— pilot 产物的可判定核验 + pilot_实测.tsv

逐件核验：
  A1/A2 IHDR 尺寸 == 1920×1080、w/h 与 16/9 偏差 < 0.01（大纲 V1）
  A7  不透明/边界：RGB 全屏件的最外 2 列/行不得是纯黑带（S9）；
      源带 alpha 的件输出仍为 RGBA、且内容区 alpha 与原图一致（内容区 0 未改动）
  V3-几何 内容区保真：content 区(seams)与「2× 源 LANCZOS 重采样到同尺寸」的平均/最大绝对差
      —— 用于证明「未拉伸、未位移、主体逐像素保留」（S7）
  接缝  接缝列处的列均值阶跃 + 局部横向梯度峰值倍率（客观化的「有没有硬断线」）

产物：
  证据\pilot_实测.tsv      件名/输入尺寸/输出字节/耗时/峰值内存/…（派单要求的四列 + 核验列）
  证据\pilot_核验.txt      汇总
"""
import sys, os, csv, json, struct

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
sys.path.insert(0, os.path.join(WS, "工具", "outpaint", "pylibs"))
sys.path.insert(0, HERE)

import numpy as np                                       # noqa: E402
from PIL import Image                                    # noqa: E402
from run_outpaint import out_seams, canvas_geom, TARGET   # noqa: E402

FIG_DIR = os.path.join(ISSUE_DIR, "证据", "pilot_对照图")
OUT_DIR = os.path.join(ISSUE_DIR, "outpaint")
TRIAGE = os.path.join(ISSUE_DIR, "分诊.tsv")


def ihdr(path):
    with open(path, "rb") as f:
        head = f.read(33)
    w, h = struct.unpack(">II", head[16:24])
    return w, h, head[24], head[25]      # bitdepth, colortype


def colmean_stats(g):
    """按列均值（灰阶）与其差分，用于接缝阶跃与梯度倍率。"""
    cm = g.mean(axis=0)
    d1 = np.abs(np.diff(cm))
    return cm, d1


def main():
    tri = {r["统一名"]: r for r in csv.DictReader(open(TRIAGE, encoding="utf-8"),
                                                 delimiter="\t")}
    met = json.load(open(os.path.join(ISSUE_DIR, "证据", "_last_run_metrics.json"),
                         encoding="utf-8"))
    rows_out = []
    notes = []
    for m in met:
        name = m["name"]
        dst = os.path.join(OUT_DIR, name)
        src = os.path.join(MAIN_PROJ, "资源组", "美术统一_超分",
                           "系统UI" if m["cat"] == "系统UI" else "CG背景", name)
        # 源定位（走清单）
        s_w, s_h, _, _ = ihdr(src)
        w, h, bd, ct = ihdr(dst)
        l, r = out_seams(s_w, s_h)
        im_out = Image.open(dst)
        out_mode = im_out.mode
        im_rgb = im_out.convert("RGB")

        # --- 内容区保真 ---
        with Image.open(src) as s:
            ref = s.convert("RGB").resize((r - l, h), Image.LANCZOS)
        got = im_rgb.crop((l, 0, r, h))
        A = np.asarray(ref).astype(np.float32)
        B = np.asarray(got).astype(np.float32)
        mg = 6
        Ai, Bi = A[mg:-mg, mg:-mg], B[mg:-mg, mg:-mg]
        mean_abs = float(np.abs(Ai - Bi).mean())
        max_abs = float(np.abs(Ai - Bi).max())

        # --- 接缝阶跃 / 硬断线 ---
        g = np.asarray(im_rgb.convert("L")).astype(np.float32)
        cm, d1 = colmean_stats(g)
        med = float(np.median(d1))
        def step(x):
            a = float(np.abs(cm[x - 4] - cm[x + 4]))
            loc = float(d1[max(0, x - 3):x + 3].max())
            return a, loc / max(med, 1e-6)
        sl, rl = step(l), step(r)

        # --- 结构连续性（线稿是否在接缝处硬断）：缝两侧各 30 px 带的横向梯度能量比 ---
        #     生成带/原带 ≪ 1 且原带本身不平坦 ⇒ 原图线条在缝处断掉、扩展区糊化
        B = 30
        def struct(x):
            gl = float(np.abs(np.diff(g[:, max(0, x - B):x], axis=1)).mean())   # 生成侧
            gr = float(np.abs(np.diff(g[:, x:x + B], axis=1)).mean())           # 原图侧
            return gl, gr, (gl / gr if gr > 1e-6 else float("nan"))
        stl, str_ = struct(l), struct(r)

        # --- 糊化程度：缝两侧各 30 px 带的高频（二阶差分）能量比（生成侧/原图侧）---
        #     远小于 1 ⇒ 扩展区被糊化（LaMa 补边的典型症状）
        def sharp(x):
            gl = float(np.abs(np.diff(np.diff(g[:, max(0, x - B):x], axis=1), axis=1)).mean())
            gr = float(np.abs(np.diff(np.diff(g[:, x:x + B], axis=1), axis=1)).mean())
            return (gl / gr) if gr > 1e-6 else float("nan")
        shl, shr = sharp(l), sharp(r)

        # --- S9 边界：最外 2 列/行均值（纯黑带 = 0） ---
        arr = np.asarray(im_rgb).astype(np.float32)
        edge = [float(arr[:, :2].mean()), float(arr[:, -2:].mean()),
                float(arr[:2, :].mean()), float(arr[-2:, :].mean())]

        # --- alpha 一致性（源带 alpha 时） ---
        a_note = "—"
        if np.asarray(im_out.split()[-1]).shape[:2] == (h, w) and out_mode == "RGBA":
            with Image.open(src) as s:
                asrc = s.split()[-1].resize((r - l, h), Image.LANCZOS)
            agot = im_out.split()[-1].crop((l, 0, r, h))
            d = float(np.abs(np.asarray(asrc).astype(np.float32) -
                             np.asarray(agot).astype(np.float32))[6:-6, 6:-6].mean())
            a_note = "内容区 alpha 平均差 %.2f" % d

        rec = {
            "件名": name, "档位": m["tier"], "判读类别": m["cat"],
            "边缘比": tri.get(name, {}).get("边缘比", ""),
            "档位判定": tri.get(name, {}).get("档位判定", "")[:2],
            "源尺寸": "%dx%d" % (s_w, s_h),
            "输出尺寸": "%dx%d" % (w, h), "输出模式": out_mode,
            "输出字节": m["bytes"],
            "推理秒": m["infer_s"], "总秒": m["total_s"],
            "峰值内存MB": m["peak_ws_mb"],
            "接缝L x": l, "接缝R x": r,
            "列均值阶跃L": round(sl[0], 2), "梯度倍率L": round(sl[1], 1),
            "列均值阶跃R": round(rl[0], 2), "梯度倍率R": round(rl[1], 1),
            "缝侧梯度L生成": round(stl[0], 3), "缝侧梯度L原图": round(stl[1], 3),
            "结构比L": round(stl[2], 2) if stl[2] == stl[2] else "n/a(平坦)",
            "缝侧梯度R生成": round(str_[0], 3), "缝侧梯度R原图": round(str_[1], 3),
            "结构比R": round(str_[2], 2) if str_[2] == str_[2] else "n/a(平坦)",
            "锐度比L": round(shl, 2) if shl == shl else "n/a(平坦)",
            "锐度比R": round(shr, 2) if shr == shr else "n/a(平坦)",
            "内容区平均绝对差": round(mean_abs, 3), "内容区最大绝对差": round(max_abs, 1),
            "四边最外2px均值": "/".join("%.1f" % x for x in edge),
            "alpha核验": a_note,
        }
        rows_out.append(rec)
        # 判据：尺寸/画幅合规 + 内容区保真（max 阈值 24：整画布 LANCZOS 与「先裁后缩」的
        #       相位差在锐利边缘可达 ~20 级，属重采样误差而非构图改动）
        ok = (w, h) == TARGET and abs(w / h - 16 / 9) < 0.01 and max_abs <= 24.0
        notes.append("%-12s %s mode=%-4s bytes=%-8d 内容区avg=%.3f 阶跃L/R=%.1f/%.1f 结构比L/R=%-9s 锐度比L/R=%s"
                     % (name, "PASS" if ok else "CHECK", out_mode, m["bytes"], mean_abs,
                        sl[0], rl[0],
                        ("%.2f/%.2f" % (stl[2], str_[2])) if stl[2] == stl[2] else "n/a",
                        ("%.2f/%.2f" % (shl, shr)) if shl == shl else "n/a(平坦)"))

    tp = os.path.join(ISSUE_DIR, "证据", "pilot_实测.tsv")
    with open(tp, "w", encoding="utf-8", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()), delimiter="\t")
        wtr.writeheader()
        wtr.writerows(rows_out)
    txt = "\n".join(notes)
    open(os.path.join(ISSUE_DIR, "证据", "pilot_核验.txt"), "w", encoding="utf-8").write(txt)
    print(txt)
    print("\n-> %s" % tp)
    bs = [r["输出字节"] for r in rows_out]
    ts = [r["总秒"] for r in rows_out]
    print("单件 字节 min/mean/max = %d / %.0f / %d ｜ 总秒 mean=%.2f" %
          (min(bs), sum(bs) / len(bs), max(bs), sum(ts) / len(ts)))
    print("目录实测体积 = %.2f MiB（%d 件）" %
          (sum(os.path.getsize(os.path.join(OUT_DIR, n)) for n in os.listdir(OUT_DIR)) / 1048576.0,
           len(os.listdir(OUT_DIR))))


if __name__ == "__main__":
    main()
