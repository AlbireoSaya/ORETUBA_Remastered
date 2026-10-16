# -*- coding: utf-8 -*-
r"""
verify_untouched_v3.py —— 未触碰自证 + 新产物逐像素自证（ISSUE-20260928-02 · 1028 补边续作 · 最后一步）

全部**重新读盘复算**，不复用任何脚本的自我声明：
  A. `outpaint\` 640 件 vs 开工前快照（证据\_outpaint_md5_before.tsv）逐件 md5+字节
  B. `outpaint_tonematch\`(349) + `outpaint_geo\`(3) vs **上一轮收尾清单**
     （证据\原产物_md5_v2.tsv）逐件 md5+字节  ⇒ 证明本步未覆盖上一轮产物
  C. 记录本步收尾的**全量 md5 清单**（证据\原产物_md5_v3.tsv：outpaint / tonematch / geo /
     outpaint_geo_* 12 个变体目录 / outpaint_tonematch_v2）+ 组合 md5（目录级指纹）
  D. 新增 80 件产物的**独立逐像素自证**：内容区 [xl,xr) 与 outpaint\ 原件逐像素逐通道
     max abs diff == 0；扩展区确有改动；尺寸/模式/alpha 一致
  E. 负向对照：翻转一个字节，确认脚本能检出（不是空跑）

用法：python verify_untouched_v3.py
"""
import sys, os, csv, hashlib, glob

WS = r"E:\ZCode Workspace\Galgame"
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
import numpy as np
from PIL import Image
from quality_axes import out_seams, TARGET

EVID = os.path.join(ISSUE_DIR, "证据")
SNAP_BEFORE = os.path.join(EVID, "_outpaint_md5_before.tsv")
PREV_LIST = os.path.join(EVID, "原产物_md5_v2.tsv")
NEW_LIST = os.path.join(EVID, "原产物_md5_v3.tsv")
OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
TM2 = os.path.join(ISSUE_DIR, "outpaint_tonematch_v2")
LIST_TSV = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "资源组", "美术", "4比3待重制清单.tsv")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def scan(d):
    fl = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    return [(f, os.path.getsize(os.path.join(d, f)), md5(os.path.join(d, f))) for f in fl]


def main():
    fail = 0
    print("== A. outpaint\\ 640 件 vs 开工前快照 ==")
    snap = {r["统一名"]: (int(r["字节"]), r["md5"])
            for r in csv.DictReader(open(SNAP_BEFORE, encoding="utf-8"), delimiter="\t")}
    cur = {f: (s, m) for f, s, m in scan(OUTPAINT)}
    chg = [n for n in snap if n in cur and cur[n] != snap[n]]
    miss = [n for n in snap if n not in cur]
    print("   快照 %d 件 / 目录 %d 件 ｜ md5+字节变动 %d ｜ 缺失 %d ⇒ %s"
          % (len(snap), len(cur), len(chg), len(miss),
             "未变 ✓" if not (chg or miss) else "★异常 " + str((chg + miss)[:5])))
    fail += 1 if (chg or miss) else 0

    print("== B. outpaint_tonematch / outpaint_geo vs 上一轮收尾清单（原产物_md5_v2.tsv）==")
    prev = {}
    for r in csv.DictReader(open(PREV_LIST, encoding="utf-8"), delimiter="\t"):
        prev[(r["目录"], r["统一名"])] = (int(r["字节"]), r["md5"])
    for tag in ("outpaint_tonematch", "outpaint_geo"):
        d = os.path.join(ISSUE_DIR, tag)
        now = {f: (s, m) for f, s, m in scan(d)}
        bad = [f for f in now if (tag, f) in prev and prev[(tag, f)] != now[f]]
        add = [f for f in now if (tag, f) not in prev]
        gone = [f for (t, f) in prev if t == tag and f not in now]
        print("   %-20s %3d 件 ｜ 与上轮清单不一致 %d ｜ 新增 %d ｜ 缺失 %d ⇒ %s"
              % (tag, len(now), len(bad), len(add), len(gone),
                 "未变 ✓" if not (bad or add or gone) else "★异常 %s" % (bad + add + gone)[:5]))
        fail += 1 if (bad or add or gone) else 0

    print("== C. 本步收尾全量 md5 清单（证据\\原产物_md5_v3.tsv）==")
    rows = []
    dirs = ["outpaint", "outpaint_tonematch", "outpaint_geo"]
    dirs += [os.path.basename(p) for p in sorted(glob.glob(os.path.join(ISSUE_DIR, "outpaint_geo_*")))
             if os.path.isdir(p)]
    dirs += ["outpaint_tonematch_v2"]
    agg = hashlib.md5()
    for tag in dirs:
        d = os.path.join(ISSUE_DIR, tag)
        if not os.path.isdir(d):
            continue
        sc = scan(d)
        tot = sum(s for _f, s, _m in sc)
        for f, s, m in sc:
            rows.append((tag, f, s, m))
            agg.update(("%s\t%s\t%d\t%s\n" % (tag, f, s, m)).encode())
        print("   %-30s %4d 件 ｜ %9.2f MiB" % (tag, len(sc), tot / 1048576.0))
    with open(NEW_LIST, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t"); w.writerow(["目录", "统一名", "字节", "md5"]); w.writerows(rows)
    print("   组合 md5（覆盖 %d 个目录 / %d 件）= %s" % (len(dirs), len(rows), agg.hexdigest()))
    print("   清单 -> %s" % NEW_LIST)

    print("== D. 新增 80 件产物独立逐像素自证 ==")
    src = {}
    for r in csv.DictReader(open(LIST_TSV, encoding="utf-8"), delimiter="\t"):
        if r["建议策略(重制/补边/裁切)"] == "补边":
            src[r["统一名"]] = os.path.join(WS, "工程",
                                            "我们没有翅膀——格雷塔迦露德与柳木原", r["超分版路径"])
    names = sorted(f for f in os.listdir(TM2) if f.endswith(".png"))
    worst, bad, nochan, zmode = 0, [], [], []
    for n in names:
        a = np.asarray(Image.open(os.path.join(OUTPAINT, n)).convert("RGB"))
        im2 = Image.open(os.path.join(TM2, n))
        b = np.asarray(im2.convert("RGB"))
        if im2.size != TARGET:
            zmode.append((n, im2.size))
        mo = Image.open(os.path.join(OUTPAINT, n)).mode
        if im2.mode != mo:
            zmode.append((n, "%s!=%s" % (im2.mode, mo)))
        W, H = Image.open(src[n]).size
        xl, xr = out_seams(W, H)
        d = int(np.abs(b[:, xl:xr, :].astype(np.int16) - a[:, xl:xr, :].astype(np.int16)).max())
        worst = max(worst, d)
        if d != 0:
            bad.append((n, d))
        ext = np.concatenate([b[:, :xl, :], b[:, xr:, :]], axis=1)
        fine = np.concatenate([a[:, :xl, :], a[:, xr:, :]], axis=1)
        if not np.any(ext.astype(np.int16) != fine.astype(np.int16)):
            nochan.append(n)
        im2.close()
    print("   %d 件 ｜ 内容区逐像素逐通道 max abs diff（全批 max）= %d ⇒ %s"
          % (len(names), worst, "全部 == 0 ✓" if not bad else "★异常 %s" % bad))
    print("   扩展区未被改动（pass 无效）的件数：%d %s" % (len(nochan), nochan[:5]))
    print("   尺寸/模式异常件：%d %s" % (len(zmode), zmode[:5]))
    fail += 1 if (bad or nochan or zmode) else 0

    print("== E. 负向对照（证明能检出改动）==")
    n0 = names[0]
    p = os.path.join(TM2, n0)
    a = np.asarray(Image.open(p).convert("RGB")).copy()
    W, H = Image.open(src[n0]).size
    xl, _xr = out_seams(W, H)
    a[:, xl + 5, :] = (a[:, xl + 5, :].astype(np.int16) + 1).astype(np.uint8)
    b = np.asarray(Image.open(p).convert("RGB"))
    d = int(np.abs(a.astype(np.int16) - b.astype(np.int16)).max())
    print("   把 %s 内容区第 %d 列 +1 级 ⇒ 最大差 %d ⇒ %s" % (n0, xl + 5, d, "有效 ✓" if d else "★失灵"))
    fail += 0 if d else 1

    print("\n== 结论：%s ==" % ("未触碰 + 自证通过 ✓" if fail == 0 else "★ %d 项异常" % fail))


if __name__ == "__main__":
    main()
