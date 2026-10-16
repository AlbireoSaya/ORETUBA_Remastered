# -*- coding: utf-8 -*-
r"""_pairs_report.py —— 汇总画面截图对：实际截取行号 + 逐像素比较 + 命名对照副本 + TSV。

每对给出：
  * 请求行 / 实测截取行（取 console 里「已存档 槽1（<scene> 行 N）」——该 save 紧接相位①截图、
    对话框行不变，故等于截图行；本版 driver 已把打字机改为即时完成 ⇒ 恒等于请求行）；
  * 逐像素：不同像素数、占比、包围盒、横向差异段（用于对照「差异区 = 该立绘占位」）；
  * 期望差异（人工登记，来源 stage 事件差分 + ui_staging 语义）。
"""
import io, os, re, shutil
from PIL import Image, ImageChops

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "验收", "画面")

# (scene, line, 期望差异)
PAIRS = [
    ("ot_s01_06d", 100, "mas(槽2) 1312→1132（tier1 补 seq100 chr_place mas 1132；off 停在 1312）"),
    ("ot_s02_03g", 144, "ten(槽0) 40→717（tier1 seq143 chr_place ten 792 + seq144 chr_expr 717）"),
    ("ot_s03_07b", 156, "nar(槽0) 40→666 且 men(槽1) 1404→1178（tier1 seq96/156 两条 chr_place）"),
    ("ot_s04_20a", 157, "kob(槽0) 42→839（tier1 seq155/157 chr_place kob；off 停在 42＝被左侧金发挡）"),
    ("ot_s04_20a", 334, "nar(槽2) 356→1448（tier1 seq334 chr_place nar 1448；由中央移到最右）"),
    ("ot_s03_06e1", 141, "sak(槽1) 1192 退场（tier1 seq141 chr_remove slot1 sak）"),
    ("ot_s01_06d", 8, "【反例】kur(槽1) 预测 556→292，但被全屏 asu(槽0,w1920) 遮挡 ⇒ 画面应无差"),
    ("ot_s01_12c2", 63, "【反例】kob(槽2) 预测退场，但渲染层未反映 chr_remove ⇒ 画面无差（见说明 §发现）"),
]


def pixdiff(p1, p2):
    a = Image.open(p1).convert("RGB"); b = Image.open(p2).convert("RGB")
    if a.size != b.size:
        return None
    W, H = a.size
    m = None
    for c in ImageChops.difference(a, b).split():
        t = c.point(lambda v: 255 if v > 0 else 0)
        m = t if m is None else ImageChops.lighter(m, t)
    bbox = m.getbbox()
    if bbox is None:
        return dict(W=W, H=H, n=0, bbox=None, segs=[])
    n = m.histogram()[255]
    x0, y0, x1, y1 = bbox
    px = m.load()
    colhas = [False] * W
    for x in range(x0, x1):
        for y in range(y0, y1):
            if px[x, y]:
                colhas[x] = True; break
    segs, s = [], None
    for x in range(W):
        if colhas[x] and s is None: s = x
        elif not colhas[x] and s is not None: segs.append((s, x - 1)); s = None
    if s is not None: segs.append((s, W - 1))
    segs.sort(key=lambda t: t[1] - t[0], reverse=True)
    return dict(W=W, H=H, n=n, bbox=(x0, y0, x1 - 1, y1 - 1), segs=segs[:3])


def captured_line(console):
    """实测截图行 = 自测最后一条对白日志的**标签值 + 2**。
    依据：uiStoryTestLogLine 打印的是自增前的 UIStoryTestLines（**0 基**，label = 行号-1），
    打印后 +1；收尾相位在「显示下一行」的那一拍触发，shot_901 即 label+2 那一行。
    （save 行与 save 语义相关，可能差 1，故不采用。）"""
    t = io.open(console, encoding="utf-8", errors="replace").read()
    ns = [int(m) for m in re.findall(r"\[STORYTEST\] (\d+) <", t)]
    return (max(ns) + 2) if ns else "?"


def main():
    cmp_dir = os.path.join(BASE, "对照")
    os.makedirs(cmp_dir, exist_ok=True)
    rows = []
    for scene, L, expect in PAIRS:
        d = os.path.join(BASE, "%s_L%d" % (scene, L))
        off = os.path.join(d, "off", "shot_901_dialog.png")
        t1 = os.path.join(d, "tier1", "shot_901_dialog.png")
        clo = captured_line(os.path.join(d, "off", "_console.txt"))
        clt = captured_line(os.path.join(d, "tier1", "_console.txt"))
        r = pixdiff(off, t1)
        shutil.copy2(off, os.path.join(cmp_dir, "%s_L%d_off.png" % (scene, L)))
        shutil.copy2(t1, os.path.join(cmp_dir, "%s_L%d_tier1.png" % (scene, L)))
        seg = ", ".join("[%d..%d]w%d" % (a, b, b - a + 1) for a, b in r["segs"])
        bb = "-" if r["bbox"] is None else "x[%d..%d] y[%d..%d]" % (r["bbox"][0], r["bbox"][2], r["bbox"][1], r["bbox"][3])
        verdict = "DIFF" if r["n"] > 0 else "SAME"
        rows.append((scene, L, clo, clt, "%dx%d" % (r["W"], r["H"]), r["n"],
                     "%.3f%%" % (100.0 * r["n"] / (r["W"] * r["H"])), verdict, bb, seg, expect))
        print("%-11s L%-4d cap(off=%s t1=%s) %-4s diff=%d (%s) bbox=%s segs=%s"
              % (scene, L, clo, clt, verdict, r["n"], rows[-1][6], bb, seg))
    out = os.path.join(BASE, "逐像素对照.tsv")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("scene\treq_line\tcap_off\tcap_tier1\tsize\tdiff_px\tdiff_pct\tverdict\tbbox\t横向差异段\t期望差异\n")
        for row in rows:
            f.write("\t".join(str(x) for x in row) + "\n")
    print("写入", out)


if __name__ == "__main__":
    main()
