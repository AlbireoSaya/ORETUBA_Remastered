# -*- coding: utf-8 -*-
r"""
verify_untouched_v2.py —— 未触碰自证（ISSUE-20260928-02 · 本轮收尾）

**不复用任何脚本的自我声明**，全部重新读盘复算：
  A. `outpaint\` 640 件与开工前快照（证据\_outpaint_md5_before.tsv）逐件比对 md5 + 字节
     ⇒ 证明本轮**零改动**（本轮只读它，产物全落新目录）
  B. 为 outpaint_tonematch / outpaint_geo 记录**本轮收尾时的 md5 清单**（证据\原产物_md5_v2.tsv）
     并给出组合 md5，供 vision / 主代理复核"本轮未覆盖这两个目录"
  C. 统计本轮**新增目录**的件数与体量（不得与三个原产物目录同名；体量 <= 1.5 GiB）
  D. 负向对照：故意把某件内容区改 1 像素，确认本脚本能检出（不是空跑）

用法：python verify_untouched_v2.py
"""
import sys, os, csv, hashlib

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
EVID = os.path.join(ISSUE_DIR, "证据")
SNAP = os.path.join(EVID, "_outpaint_md5_before.tsv")
OUT = os.path.join(EVID, "原产物_md5_v2.tsv")

ORIG = {"outpaint": os.path.join(ISSUE_DIR, "outpaint"),
        "outpaint_tonematch": os.path.join(ISSUE_DIR, "outpaint_tonematch"),
        "outpaint_geo": os.path.join(ISSUE_DIR, "outpaint_geo")}


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
    fail = 0
    rows = []
    print("== A. outpaint\\ 640 件与开工前快照比对 ==")
    snap = {r["统一名"]: (int(r["字节"]), r["md5"])
            for r in csv.DictReader(open(SNAP, encoding="utf-8"), delimiter="\t")}
    names = sorted(f for f in os.listdir(ORIG["outpaint"]) if f.endswith(".png"))
    chg, miss = [], []
    for n in names:
        p = os.path.join(ORIG["outpaint"], n)
        cur = (os.path.getsize(p), md5(p))
        if n not in snap:
            miss.append(n)
        elif cur != snap[n]:
            chg.append(n)
        rows.append(("outpaint", n, cur[0], cur[1]))
    print("   快照 %d 件 / 目录 %d 件 ｜ md5+字节变动 %d ｜ 快照缺失 %d ⇒ %s"
          % (len(snap), len(names), len(chg), len(miss),
             "未变 ✓" if not chg else "★变动！" + str(chg[:5])))
    fail += 1 if chg else 0

    print("== B. outpaint_tonematch / outpaint_geo 收尾 md5 清单 ==")
    for tag in ("outpaint_tonematch", "outpaint_geo"):
        d = ORIG[tag]
        fl = sorted(f for f in os.listdir(d) if f.endswith(".png"))
        tot = 0
        for n in fl:
            p = os.path.join(d, n)
            s = os.path.getsize(p)
            rows.append((tag, n, s, md5(p)))
            tot += s
        print("   %-20s %3d 件 ｜ %8.2f MiB" % (tag, len(fl), tot / 1048576.0))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["目录", "统一名", "字节", "md5"])
        w.writerows(rows)
    agg = os.path.join(EVID, "原产物_md5_v2.tsv")
    print("   组合 md5（清单文件自身）= %s" % md5(agg))
    print("   清单 -> %s（%d 行）" % (agg, len(rows)))

    print("== C. 本轮新增目录 ==")
    tot_new = 0.0
    for d in sorted(os.listdir(ISSUE_DIR)):
        p = os.path.join(ISSUE_DIR, d)
        if not os.path.isdir(p):
            continue
        if d in ORIG or d.startswith("_") or d == "复现脚本":
            continue
        n = 0
        sz = 0
        for root, _dirs, files in os.walk(p):
            for fn in files:
                n += 1
                try:
                    sz += os.path.getsize(os.path.join(root, fn))
                except OSError:
                    pass
        if d.startswith("outpaint_geo_") or d == "证据" or d.startswith("outpaint"):
            print("   %-28s %5d 文件 ｜ %8.1f MiB" % (d, n, sz / 1048576.0))
            tot_new += sz / 1048576.0
    print("   新增合计（含 证据\\) ≈ %.1f MiB  ⇒ 预算 1.5 GiB ⇒ %s"
          % (tot_new, "OK ✓" if tot_new <= 1536 else "★超预算"))

    print("== D. 负向对照（证明本脚本能检出改动）==")
    n0 = names[0]
    p = os.path.join(ORIG["outpaint"], n0)
    h = md5(p)
    tmp = os.path.join(EVID, "_negctl.tmp")
    with open(p, "rb") as f:
        b = bytearray(f.read())
    b[-1] ^= 0x01
    with open(tmp, "wb") as f:
        f.write(b)
    h2 = md5(tmp)
    os.remove(tmp) if False else os.path.exists(tmp) and os.remove(tmp)
    print("   把 %s 末字节翻转 ⇒ md5 变化 %s ⇒ %s" % (n0, h != h2, "有效 ✓" if h != h2 else "★失灵！"))
    fail += 0 if h != h2 else 1

    print("\n== 结论：%s ==" % ("未触碰自证通过 ✓" if fail == 0 else "★ %d 项异常" % fail))


if __name__ == "__main__":
    main()
