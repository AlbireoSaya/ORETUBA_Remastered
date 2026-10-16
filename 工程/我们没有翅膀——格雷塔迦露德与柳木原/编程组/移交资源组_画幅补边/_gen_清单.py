#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""_gen_清单.py —— 生成「移交资源组·画幅补边」工作包 v2（**按用途分拣后的**素材副本 + 清单.tsv）

★ v2（2026-10-02 用户纠偏后重做）：v1 把「被显示且宽高比≠16:9 的 200 件」一律当"待补边背景"——**这是错的**。
   经与资源组母版层 `美术统一\交付清单.tsv` 的 **判读类别** 交叉比对 + 代表样本目视（两张接触印相表），
   200 件里真正的全屏 4:3 背景只有 **46 件**；另有 114 件事件 CG（是否处理待用户裁决）、
   13 件特效图（`ef*` 闪光／`bld*` 血溅）、5 件章节题卡（`ec*`）、2 件插入图（`cin*`）＝**不该碰的 20 件**，
   以及 20 件**滚动/全景背景**（2:1／超宽／2:3 竖，原版要平移显示，补边或裁切都会毁掉用途）。

输入：`..\画幅审计\超分候选_背景A类.tsv`（200 件）
     `资源组\美术统一\交付清单.tsv`（判读类别 · 权威）＋ `资源组\美术统一_交付\交付清单.tsv`（交付相对路径→统一名）
输出：`清单.tsv`（200 行，含 **判读类别 / 处置** 列）＋ `输入素材\背景4比3\`（**只复制 46 件真背景**）

纪律：**只复制，不改写、不重采样**；被排除的 40+20 件**绝不复制**，避免资源组误碰。
"""
import io
import os
import re
import shutil
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))          # <proj>（=我们没有翅膀——格雷塔迦露德与柳木原）
MAIN = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
AUD = os.path.join(PROJ, "编程组", "画幅审计", "超分候选_背景A类.tsv")
ART_LOCAL = os.path.join(PROJ, "资源组", "美术统一_交付")
ART_MAIN = os.path.join(MAIN, "资源组", "美术统一_交付")
MST_LOCAL = os.path.join(PROJ, "资源组", "美术统一", "交付清单.tsv")
MST_MAIN = os.path.join(MAIN, "资源组", "美术统一", "交付清单.tsv")

CLS_DIR = {"4:3": "4比3", "2:3竖": "2比3竖", "2:1": "2比1",
           "超宽>2.2": "超宽", "竖图": "竖图", "1:1": "1比1"}


def rd(p):
    t = io.open(p, encoding="utf-8-sig", newline="").read().replace("\r\n", "\n").replace("\r", "\n")
    rows = [l.split("\t") for l in t.split("\n") if l.strip()]
    return rows[0], rows[1:]


def first(*paths):
    for p in paths:
        if os.path.isfile(p):
            return p
    return ""


def disposition(cat, cls, base):
    """(判读类别, 比例类, 文件名) → (处置, 是否纳入副本)"""
    stem = base.rsplit(".", 1)[0]
    if re.match(r"^ec[0-9]", stem):
        return "不处理：章节题卡（标题/章节卡，本就 4:3，显示它是挑图兜底）", False
    if re.match(r"^(cin|cg_cin)", stem):
        return "不处理：插入图/道具图（cut-in，小图）", False
    if cat == "其他" and re.match(r"^(ef|bld)", stem):
        return "不处理：特效图（ef=闪光/速度线，bld=血溅）", False
    if cat == "背景" and cls in ("2:1", "超宽>2.2", "2:3竖", "竖图"):
        return ("不处理：滚动/全景背景（原版 800×600 画面放不下 ⇒ 是平移用的，"
                "补边或裁切都会毁掉用途；要满屏需引擎平移支持或逐场景裁切窗）"), False
    if cat == "背景" and cls == "4:3":
        return "纳入：全屏 4:3 背景 ⇒ 补边候选（路线待用户裁决：补左右 / 裁上下）", True
    if cat == "CG" and cls == "4:3":
        return "待用户裁决：事件 CG（补边＝在关键美术周围生成内容；不做则保留留边）", False
    return "待判读：判读类别=%s / 比例类=%s（需逐件人工看）" % (cat, cls), False


def main():
    _hA, _a = rd(AUD)
    rows = [dict(zip(_hA, r)) for r in _a]      # A 表按列名取用（rd 本身返回位置行）
    dpath = first(os.path.join(PROJ, "资源组", "美术统一_交付", "交付清单.tsv"),
                  os.path.join(ART_MAIN, "交付清单.tsv"))
    mpath = first(MST_LOCAL, MST_MAIN)
    if not dpath or not mpath:
        print("[FATAL] 找不到交付/母版清单：%s / %s" % (dpath, mpath)); return 1
    hD, rD = rd(dpath)
    hM, rM = rd(mpath)
    iD = [i for i, c in enumerate(hD) if "交付相对路径" in c][0]
    iDN = [i for i, c in enumerate(hD) if c == "统一名"][0]
    d2u = {r[iD]: r[iDN] for r in rD if len(r) > max(iD, iDN)}
    iN = [i for i, c in enumerate(hM) if c == "统一名"][0]
    iC = [i for i, c in enumerate(hM) if c == "判读类别"][0]
    iS = [i for i, c in enumerate(hM) if c == "尺寸(w,h)"][0]
    u2 = {r[iN]: (r[iC], r[iS]) for r in rM if len(r) > max(iN, iC)}
    print("[join] 交付→统一名 %d 条；母版判读 %d 条（%s / %s）" % (len(d2u), len(u2),
          os.path.basename(os.path.dirname(dpath)), os.path.basename(os.path.dirname(mpath))))

    out, n_copy, tot, n_in = [], 0, 0, 0
    cnt = Counter()
    for i, r in enumerate(rows, 1):
        cls = r["ratio_class"]
        base = os.path.basename(r["deliv"])
        u = d2u.get(r["deliv"])
        if not u:
            print("[FATAL] 交付清单里没有这条：%s" % r["deliv"]); return 1
        cat, msize = u2.get(u, ("?", "?"))
        disp, take = disposition(cat, cls, base)
        cnt[disp.split("：")[0] + "：" + disp.split("：")[1][:14]] += 1
        src = ""
        for root in (ART_LOCAL, ART_MAIN):
            p = os.path.normpath(os.path.join(root, r["deliv"].replace("/", os.sep)))
            if os.path.isfile(p):
                src = p; break
        if not src:
            print("[FATAL] 取不到实件：%s" % r["deliv"]); return 1
        sz = os.path.getsize(src); tot += sz
        rel = ""
        if take:
            d = os.path.join(HERE, "输入素材", "背景4比3")
            os.makedirs(d, exist_ok=True)
            dp = os.path.join(d, base)
            if not (os.path.isfile(dp) and os.path.getsize(dp) == os.path.getsize(src)):
                shutil.copy2(src, dp); n_copy += 1
            rel = "输入素材/背景4比3/" + base
            n_in += 1
        aw, ah = int(r["aw"]), int(r["ah"])
        ow = int(round(ah * 16.0 / 9.0)); oh = int(round(aw * 9.0 / 16.0))
        lr = ("补左右 +%d" % (ow - aw)) if ow >= aw else ("裁左右 -%d" % (aw - ow))
        tb = ("补上下 +%d" % (oh - ah)) if oh >= ah else ("裁上下 -%d" % (ah - oh))
        scenes = (r.get("scenes") or "")
        out.append([str(i), cls, r["primary_src"], r["deliv"], base,
                    "%dx%d" % (aw, ah), r["ar"], "%s → %dx%d ｜ %s → %dx%d" % (lr, ow, ah, tb, aw, oh),
                    cat, msize, disp, str(len([x for x in scenes.split(",") if x])),
                    scenes[:400], str(sz), rel])

    with io.open(os.path.join(HERE, "清单.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(["序号", "比例类", "源", "交付层路径", "文件名", "输入尺寸", "宽高比",
                           "16:9 两条路线", "母版判读类别", "母版原始尺寸", "处置",
                           "影响场景数", "影响场景样例", "字节数", "副本相对路径"]) + "\n")
        for o in out:
            f.write("\t".join(o) + "\n")

    print("[ok] 清单.tsv  %d 行 ｜ 新复制 %d 件（均为「纳入」） ｜ 200 件合计 %.2f MiB"
          % (len(out), n_copy, tot / 1048576.0))
    print("[ok] 纳入副本（真·全屏 4:3 背景）= %d 件" % n_in)
    print("[chk] 处置分布：")
    for k, v in cnt.most_common():
        print("   %4d  %s" % (v, k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
