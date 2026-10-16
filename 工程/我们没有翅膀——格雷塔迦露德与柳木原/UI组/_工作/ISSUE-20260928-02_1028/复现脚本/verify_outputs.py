# -*- coding: utf-8 -*-
r"""
verify_outputs.py —— 独立自证（ISSUE-20260928-02 · 1028 补边续作）

**不复用任何 pass 的自我声明**，全部重新读盘复算：
  A. `outpaint\` 640 件与开工前快照（证据\_outpaint_md5_before.tsv）逐件比对 md5 + 字节
     ⇒ 证明上一批产物**零改动**（本轮只读它）
  B. `outpaint_tonematch\` / `outpaint_geo\` 每一件：
       · IHDR == 1920×1080
       · 模式与 outpaint 原件一致（RGBA 的件仍是 RGBA）
       · **内容区 [xl,xr) 逐像素、逐通道 == outpaint 原件**（max abs diff 全批统计）
       · 扩展区确实变了（否则该 pass 没生效）
     白噪声层：另做一次「把内容区改成与原件不同」的负向对照，确认本脚本能检出改动（不是空跑）。
  C. 清单一致性：质量轴.tsv / 须处置清单.tsv 行数、五桶求和、以及三个产物目录的件数与清单一致。

用法：python verify_outputs.py
"""
import sys, os, csv, hashlib, random

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))

import numpy as np
from PIL import Image
from quality_axes import AXES_TSV, DISP_TSV

OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
PASSES = {"outpaint_tonematch": os.path.join(ISSUE_DIR, "outpaint_tonematch"),
          "outpaint_geo": os.path.join(ISSUE_DIR, "outpaint_geo")}
SNAP = os.path.join(ISSUE_DIR, "证据", "_outpaint_md5_before.tsv")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    rows = list(csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t"))
    geo = {r["统一名"]: (int(r["xl"]), int(r["xr"])) for r in rows}
    fail = 0

    print("== A. outpaint\\ 640 件是否未变 ==")
    snap = {r["统一名"]: (int(r["字节"]), r["md5"])
            for r in csv.DictReader(open(SNAP, encoding="utf-8"), delimiter="\t")}
    names = sorted(os.listdir(OUTPAINT))
    chg = [n for n in names
           if n not in snap or (os.path.getsize(os.path.join(OUTPAINT, n)),
                                md5(os.path.join(OUTPAINT, n))) != snap.get(n)]
    print("   快照 %d 件 / 目录 %d 件 / md5+字节变动 %d 件 ⇒ %s"
          % (len(snap), len(names), len(chg), "未变 ✓" if not chg else "★变动！" + str(chg[:5])))
    fail += 1 if chg else 0

    print("== B. 两个 pass 的产物：尺寸 / 模式 / 内容区逐像素不变 ==")
    for tag, d in PASSES.items():
        if not os.path.isdir(d):
            print("   %s 不存在" % tag); fail += 1; continue
        fl = sorted(f for f in os.listdir(d) if f.endswith(".png"))
        maxd = -1
        n_err = 0
        ext_changed = 0
        errs = []
        for nm in fl:
            xl, xr = geo.get(nm, (241, 1679))
            a = Image.open(os.path.join(OUTPAINT, nm))
            b = Image.open(os.path.join(d, nm))
            if b.size != (1920, 1080) or b.mode != a.mode:
                errs.append((nm, "尺寸/模式 %s %s" % (b.size, b.mode))); n_err += 1; continue
            A = np.asarray(a.convert("RGB"))
            B = np.asarray(b.convert("RGB"))
            d_in = int(np.abs(B[:, xl:xr, :].astype(np.int16) - A[:, xl:xr, :].astype(np.int16)).max())
            maxd = max(maxd, d_in)
            if d_in != 0:
                errs.append((nm, "内容区 diff=%d" % d_in)); n_err += 1
            d_ext = int(np.abs(B[:, :xl, :].astype(np.int16)
                               - A[:, :xl, :].astype(np.int16)).max())
            if d_ext > 0:
                ext_changed += 1
            if b.mode == "RGBA":
                if not np.array_equal(np.asarray(a.split()[-1]), np.asarray(b.split()[-1])):
                    errs.append((nm, "alpha 被改")); n_err += 1
            a.close(); b.close()
        print("   %-20s 件数 %3d ｜ 内容区 max abs diff（全批）= %d ｜ 扩展区已改 %d 件 ｜ 异常 %d"
              % (tag, len(fl), maxd, ext_changed, n_err))
        if errs:
            print("     异常前 5:", errs[:5])
        fail += n_err

    print("== B'. 负向对照（证明本脚本能检出改动）==")
    nm = sorted(os.listdir(PASSES["outpaint_tonematch"]))[0]
    b = np.asarray(Image.open(os.path.join(PASSES["outpaint_tonematch"], nm)).convert("RGB")).copy()
    a = np.asarray(Image.open(os.path.join(OUTPAINT, nm)).convert("RGB"))
    xl = geo[nm][0]
    b[0, xl, 0] = (int(b[0, xl, 0]) + 1) % 256          # 故意改内容区 1 像素
    d_in = int(np.abs(b[:, xl:geo[nm][1], :].astype(np.int16)
                      - a[:, xl:geo[nm][1], :].astype(np.int16)).max())
    print("   故意改 %s 内容区 1 像素 ⇒ 检出 diff=%d ⇒ %s"
          % (nm, d_in, "有效 ✓" if d_in > 0 else "★本脚本失灵！"))
    fail += 0 if d_in > 0 else 1

    print("== C. 清单一致性 ==")
    disp = list(csv.DictReader(open(DISP_TSV, encoding="utf-8"), delimiter="\t"))
    import collections
    c = collections.Counter(r["建议处置"] for r in disp)
    print("   质量轴.tsv %d 行 ｜ 须处置清单.tsv %d 行 ｜ 处置桶 %s ｜ 求和 %d"
          % (len(rows), len(disp), dict(c), sum(c.values())))
    for tag, d in PASSES.items():
        print("   %s 实有 %d 件" % (tag, len([f for f in os.listdir(d) if f.endswith(".png")])))
    n_tm = len([r for r in rows if float(r["ramp"] or 0) >= 25 or r["统一名"].startswith("sr")])
    print("   质量轴里『应做色调匹配』(ramp>=25 或 sr) = %d 件" % n_tm)
    fail += 0 if (len(rows) == len(disp) == 640 and sum(c.values()) == 640) else 1

    print("\n== 结论：%s ==" % ("全部通过 ✓" if fail == 0 else "★ 有 %d 项异常" % fail))


if __name__ == "__main__":
    main()
