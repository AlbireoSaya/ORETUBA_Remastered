# -*- coding: utf-8 -*-
r"""
triage_rerun.py —— 640 件补边素材接缝复杂度分诊（复现侦察口径）

判据（与 `.zcode\skills\asset-outpaint\triage_outpaint.py` 逐字一致）：
    ratio = max( 左40列梯度能量, 右40列梯度能量 ) / 全图平均梯度能量
    energy(g) = mean|diff(axis=1)| + mean|diff(axis=0)|

口径说明（重要）：
  * **复现口径用 1× 原图**（`美术统一\<类别>\<统一名>`，800×600）——侦察那轮的 640 件
    就是在这套图上算的（40 列 = 5% 画宽），换 2× 会改变带的相对宽度从而不复现。
  * 侦察那轮把 4 件（`ld_bg` `ld_over` `sv_bg` `sv_over`）记为 MISSING，因为脚本只扫了
    `美术统一\CG背景\`；本轮**按清单 `原图路径` 取件**（这 4 件在 `美术统一\系统UI\`），
    因此 MISSING 归零，C/D 各 +2，与 §六 的复核值 A450/B152/C32/D6 对齐。
  * 另附 `边缘比_2x`（在 `美术统一_超分\` 2× 图上按同法计算）作交叉参考。

产物：
  分诊.tsv       逐件：统一名 / 档位 / 边缘比 / 档位判定 / 建议处置 (+ 参考列)
  须人工清单.tsv  C+D 共 38 件，按边缘比降序
"""
import sys, os, csv, collections

WS = r"E:\ZCode Workspace\Galgame"
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
import numpy as np
from PIL import Image

MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
LIST = os.path.join(MAIN_PROJ, "资源组", "美术", "4比3待重制清单.tsv")
OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAND = 40


def energy(g):
    gx = np.abs(np.diff(g, axis=1)).mean()
    gy = np.abs(np.diff(g, axis=0)).mean()
    return float(gx + gy)


def edge_ratio(path):
    g = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    e_all = energy(g)
    rl = energy(g[:, :BAND]) / max(e_all, 1e-6)
    rr = energy(g[:, -BAND:]) / max(e_all, 1e-6)
    return max(rl, rr), e_all, energy(g[:, :BAND]), energy(g[:, -BAND:])


def bucket(v):
    if v < 0.8:
        return "A", "A 低(<0.8) 边界比全图更平"
    if v < 1.2:
        return "B", "B 中(0.8-1.2)"
    if v < 1.8:
        return "C", "C 高(1.2-1.8) 边界偏复杂"
    return "D", "D 极高(>=1.8) 边界线稿密集"


ACTION = {
    "A": "可直接采用（必要时轻降噪）",
    "B": "轻度人工精修后可用",
    "C": "须人工重绘扩展区",
    "D": "须人工重绘扩展区（最高优先）",
}


def main():
    rows = [r for r in csv.DictReader(open(LIST, encoding="utf-8"), delimiter="\t")
            if r["建议策略(重制/补边/裁切)"] == "补边"]
    print("补边件数", len(rows), flush=True)
    out, miss = [], []
    for i, r in enumerate(rows):
        p1 = os.path.join(MAIN_PROJ, r["原图路径"])
        p2 = os.path.join(MAIN_PROJ, r["超分版路径"])
        if not os.path.exists(p1):
            miss.append((r["统一名"], r["原图路径"]))
            out.append([r["统一名"], r["建议档位(T1/T2/T3)"], "", "MISSING", "取源缺失",
                        r["判读类别"], "", "", "", "", "", p1])
            continue
        v1, e_all, e_l, e_r = edge_ratio(p1)
        v2 = ""
        if os.path.exists(p2):
            v2, *_ = edge_ratio(p2)
        b, blab = bucket(v1)
        out.append([r["统一名"], r["建议档位(T1/T2/T3)"], round(v1, 3), blab,
                    ACTION[b], r["判读类别"], round(e_all, 3), round(e_l, 3),
                    round(e_r, 3), round(v2, 3) if v2 != "" else "", ""])
        if (i + 1) % 100 == 0:
            print("  %d/%d" % (i + 1, len(rows)), flush=True)

    tp = os.path.join(OUT_DIR, "分诊.tsv")
    with open(tp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "档位", "边缘比", "档位判定", "建议处置",
                    "判读类别", "全图梯度", "左缘梯度", "右缘梯度", "边缘比_2x", "备注"])
        w.writerows(out)

    # 统计
    b = collections.Counter()
    for o in out:
        if o[3] == "MISSING":
            b["MISSING"] += 1
            continue
        b[bucket(o[2])[0]] += 1
    vals = sorted(o[2] for o in out if o[3] != "MISSING")

    def pct(q):
        return vals[int(q * (len(vals) - 1))]

    # 须人工清单：C+D，按边缘比降序
    hard = sorted([o for o in out if o[3] not in ("MISSING",)
                   and bucket(o[2])[0] in ("C", "D")], key=lambda o: -o[2])
    hp = os.path.join(OUT_DIR, "须人工清单.tsv")
    with open(hp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "档位", "边缘比", "档位判定", "建议处置", "判读类别"])
        for o in hard:
            w.writerow([o[0], o[1], o[2], o[3], o[4], o[5]])

    lines = ["补边件数: %d ｜ 取源缺失: %d" % (len(rows), len(miss)),
             "边缘比 max 分位: p10=%.2f p25=%.2f p50=%.2f p75=%.2f p90=%.2f max=%.2f"
             % (pct(.10), pct(.25), pct(.50), pct(.75), pct(.90), vals[-1]),
             "A 低(<0.8): %d ｜ B 中(0.8-1.2): %d ｜ C 高(1.2-1.8): %d ｜ D 极高(>=1.8): %d ｜ MISSING: %d"
             % (b["A"], b["B"], b["C"], b["D"], b["MISSING"]),
             "须人工(C+D): %d 件 -> 须人工清单.tsv" % len(hard)]
    txt = "\n".join(lines)
    open(os.path.join(OUT_DIR, "分诊_汇总.txt"), "w", encoding="utf-8").write(txt)
    print("\n" + txt)


if __name__ == "__main__":
    main()
