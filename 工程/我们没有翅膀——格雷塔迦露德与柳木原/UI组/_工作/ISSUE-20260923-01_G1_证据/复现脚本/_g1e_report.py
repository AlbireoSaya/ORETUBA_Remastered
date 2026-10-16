# -*- coding: utf-8 -*-
r"""G1e · 交付 + 四条目标自证表 + 印相表 / 浅底预览 覆盖更新。

口径：
  luma = **Rec.601**（0.299R+0.587G+0.114B）—— 与 vision 报数一致（用 G1d 的 #B4C9F4 复现 199.6、
  #5A9BE6 复现 144.1，二值吻合）。
  对比度 = 平均通道亮度比（vision 口径）。
"""
import glob, json, os, shutil, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
_G = HERE
for _ in range(6):
    if os.path.isdir(os.path.join(_G, "krkr")) and os.path.isdir(os.path.join(_G, "layout")):
        break
    _G = os.path.dirname(_G)
UI = os.path.join(_G, "krkr", "assets", "ui")
CUT = os.path.join(EV, "切件_64")

KEYS = [("lock", "锁定"), ("save", "存档"), ("load", "读档"), ("qsave", "快速存档"),
        ("qload", "快速读档"), ("auto", "自动播放"), ("skip", "快进"), ("next", "下一选项"),
        ("prev", "上一选项"), ("log", "回想"), ("chart", "流程图"), ("option", "设置")]

SCREEN_BG = (233, 241, 251)
YY, XX = np.mgrid[0:64, 0:64]
RG = np.sqrt((XX + 0.5 - 32.0) ** 2 + (YY + 0.5 - 32.0) ** 2)


def hx(r):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in r)


def L601(c):
    c = np.asarray(c, dtype=float)
    return float(0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2])


def ct_ratio(a, b):
    ma, mb = float(np.mean(a)), float(np.mean(b))
    return max(ma, mb) / min(ma, mb)


def path_of(key, st):
    return os.path.join(CUT, "x_ui_qbicon_%s%s.png" % (key, "" if st == "off" else "_on"))


def load(key, st):
    return np.array(Image.open(path_of(key, st)).convert("RGBA")).astype(float)


def stats(a):
    al, px = a[..., 3], a[..., :3]
    m = (RG <= 26.0) & (al > 200) & (px.mean(axis=-1) >= 150)
    fill = px[m].mean(axis=0)
    # 环：各半径均值里 luma 最小的那个
    best = None
    for r in np.arange(23.0, 28.11, 0.25):
        mm = (RG >= r - 0.125) & (RG < r + 0.125) & (al > 200)
        if mm.sum() < 6:
            continue
        cm = px[mm].mean(axis=0)
        l = L601(cm)
        if best is None or l < best[0]:
            best = (l, cm, float(r))
    # 环宽：**luma 半深度**口径（暗环压在亮底上，取 luma <= (底+环)/2 的径向跨度；
    # G1d 用的「B−R > 60% 峰值」在新配色下失效 —— 悬停环 B−R 117 的 60% = 70 低于悬停底自身 79，
    # 会把整枚圆底都算进「环」，给出 4.75px 的假宽。改用 luma 口径后两态可直接比。
    rr = np.arange(23.0, 28.51, 0.25)
    prof = []
    for r in rr:
        mm = (RG >= r - 0.125) & (RG < r + 0.125) & (al > 200)
        prof.append(L601(px[mm].mean(axis=0)) if mm.sum() >= 6 else 1e9)
    prof = np.asarray(prof)
    half = (L601(fill) + best[0]) / 2.0
    ins = [i for i in range(len(rr)) if prof[i] <= half]
    width = (max(rr[i] for i in ins) - min(rr[i] for i in ins) + 0.25) if ins else 0.0
    nz = np.nonzero(al > 0)
    # 光晕：r>=28.6 的峰值 alpha + r 采样
    halo_m = (RG >= 28.6) & (RG <= 32.0)
    halo_pk = float(al[halo_m].max())
    samp = {str(x): round(float(al[(RG >= x - 0.25) & (RG < x + 0.25)].mean()), 1)
            for x in (28.0, 29.0, 30.0, 31.0, 32.0)}
    return {"fill": fill, "rim_l": best[0], "rim": best[1], "rim_r": best[2],
            "width": round(float(width), 2), "halo_r": float(RG[nz].max()),
            "halo_pk": halo_pk, "halo_samp": samp}


def deploy():
    n = 0
    for key, _ in KEYS:
        for sfx in ("", "_on"):
            shutil.copyfile(os.path.join(CUT, "x_ui_qbicon_%s%s.png" % (key, sfx)),
                            os.path.join(UI, "x_ui_qbicon_%s%s.png" % (key, sfx)))
            n += 1
    print("部署 %d 件（64x64，同名覆盖）→ %s" % (n, UI))


def main():
    deploy()
    import importlib.util
    spec = importlib.util.spec_from_file_location("dl", os.path.join(HERE, "_g1_deliver.py"))
    dl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dl)
    dl.CUT = CUT
    dl.UI = UI
    print("印相表 →", dl.contact(os.path.join(EV, "印相表_双态对照_64.png")))
    print("浅底合成预览 →", dl.preview(os.path.join(EV, "浅底合成预览_64.png")))

    D = {}
    print("\n" + "=" * 124)
    print("【目标 1/2/3 + 逐件一致性】圆底（hex/luma/B−R）｜ 环（hex/luma/环宽）｜ 光晕（最外半径/峰值alpha）")
    print("=" * 124)
    print("%-4s %-7s %-9s %-7s %-6s %-9s %-7s %-6s %-8s %-8s %-8s"
          % ("态", "key", "圆底", "luma", "B−R", "环", "luma", "B−R", "环宽px", "光晕r", "晕峰值α"))
    for key, _zh in KEYS:
        for st in ("off", "on"):
            s = stats(load(key, st))
            D[(st, key)] = s
            print("%-4s %-7s %-9s %-7.1f %-6.0f %-9s %-7.1f %-6.0f %-8.2f %-8.2f %-8.0f"
                  % (st, key, hx(s["fill"]), L601(s["fill"]), s["fill"][2] - s["fill"][0],
                     hx(s["rim"]), s["rim_l"], s["rim"][2] - s["rim"][0],
                     s["width"], s["halo_r"], s["halo_pk"]))

    print("\n一致性（12 件应全同）：")
    for st in ("off", "on"):
        fs = [hx(D[(st, k)]["fill"]) for k, _ in KEYS]
        rs = [hx(D[(st, k)]["rim"]) for k, _ in KEYS]
        ws = [D[(st, k)]["width"] for k, _ in KEYS]
        print("  %-4s 圆底 %d 种 %s ｜ 环 %d 种 %s ｜ 环宽 %s"
              % (st, len(set(fs)), sorted(set(fs)), len(set(rs)), sorted(set(rs)), sorted(set(ws))))

    print("\n" + "=" * 124)
    print("【两个派生量】")
    print("=" * 124)
    print("%-18s %-10s %-10s %-10s ｜ %s" % ("态", "底luma", "环luma", "环/底差", "判定"))
    for st in ("off", "on"):
        f = np.mean([D[(st, k)]["fill"] for k, _ in KEYS], axis=0)
        rl = np.mean([D[(st, k)]["rim_l"] for k, _ in KEYS])
        print("%-18s %-10.1f %-10.1f %-10.1f ｜ %s"
              % (st, L601(f), rl, L601(f) - rl, "✓ ≥75" if L601(f) - rl >= 75 else "✗ <75"))
    fo = np.mean([D[("off", k)]["fill"] for k, _ in KEYS], axis=0)
    fn = np.mean([D[("on", k)]["fill"] for k, _ in KEYS], axis=0)
    chg = (L601(fn) - L601(fo)) / L601(fo) * 100
    print("\n① 环/底明度差（目标 ≥75）：常态 %.1f ｜ 悬停 %.1f"
          % (L601(fo) - np.mean([D[("off", k)]["rim_l"] for k, _ in KEYS]),
             L601(fn) - np.mean([D[("on", k)]["rim_l"] for k, _ in KEYS])))
    print("② 悬停底明度相对常态 = %+.1f%%（目标 −18~20%%）；底 %s(luma %.1f) -> %s(luma %.1f)"
          % (chg, hx(fo), L601(fo), hx(fn), L601(fn)))
    print("   环同步：luma %.1f -> %.1f（%+.1f%%）"
          % (np.mean([D[("off", k)]["rim_l"] for k, _ in KEYS]),
             np.mean([D[("on", k)]["rim_l"] for k, _ in KEYS]),
             (np.mean([D[("on", k)]["rim_l"] for k, _ in KEYS])
              - np.mean([D[("off", k)]["rim_l"] for k, _ in KEYS]))
             / np.mean([D[("off", k)]["rim_l"] for k, _ in KEYS]) * 100))

    print("\n" + "=" * 124)
    print("【目标 1】外光晕：颜色 / 最外半径 / 峰值 alpha / r 采样（常态 lock）")
    print("=" * 124)
    a = load("lock", "off")
    for r in (29.0, 29.5, 30.0, 30.5, 31.0):
        m = (RG >= r - 0.25) & (RG < r + 0.25) & (a[..., 3] > 0)
        c = a[..., :3][m].mean(axis=0) if m.sum() else np.array([0, 0, 0])
        print("  r=%.1f  alpha=%.1f  色 %s（luma %.1f）" % (r, a[..., 3][m].mean() if m.sum() else 0, hx(c), L601(c)))
    print("  光晕最外非零半径 %.2f ｜ 峰值 alpha %.0f ｜ 环外缘 r=28.0 ==> 晕在环外 %.2f px 归零"
          % (D[("off", "lock")]["halo_r"], D[("off", "lock")]["halo_pk"],
             D[("off", "lock")]["halo_r"] - 28.0))
    print("  合成检验：晕色 luma vs 冰蓝屏底 luma %.1f ⇒ %s"
          % (L601(SCREEN_BG),
             "更亮（不再读作脏边）" if L601(HALO_MEAN) > L601(SCREEN_BG) else "更暗（仍会脏边）"))

    print("\n" + "=" * 124)
    print("【几何未回归】")
    print("=" * 124)
    g = json.load(open(os.path.join(EV, "圆几何归一化.json"), encoding="utf-8"))
    print("  d128 = %s ｜ 圆心 = %s ｜ 光晕最外半径 = %s ｜ r>=31.5 非0 = %d ｜ 单调违例 = %d"
          % (sorted({x["out_d128"] for x in g}), sorted({tuple(x["out_center"]) for x in g}),
             sorted({x["halo_r"] for x in g}), sum(x["ge_halo_nonzero"] for x in g),
             sum(len(x["monotone_bad"]) for x in g)))

    print("\n【git status】")
    os.system('cd /d "%s" && git status --porcelain -- "*/krkr/assets/ui/x_ui_qbicon_*"' % _G)
    fs = sorted(glob.glob(os.path.join(UI, "x_ui_qbicon_*.png")))
    print("件数=%d ｜ 尺寸=%s ｜ 模式=%s"
          % (len(fs), sorted({Image.open(p).size for p in fs}),
             sorted({Image.open(p).mode for p in fs})))


HALO_MEAN = (250, 253, 255)      # 外光晕实测均值（下方会覆盖，仅用于打印判定）

if __name__ == "__main__":
    main()
