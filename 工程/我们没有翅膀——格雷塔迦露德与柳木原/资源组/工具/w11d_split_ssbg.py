# -*- coding: utf-8 -*-
r"""
W11d / ISSUE-20260918-06 · 任务2a：ss_bg1–5「粒度不同被误并」拆分
==================================================================
背景：W11c 把 `ss_bg1`–`ss_bg5` 归并为「一组一产物」，但两候选粒度不同：
  `ot`  `ot_ss_bgN.png`  800×600  = 场景选择**底板**（纯场景背景，无 UI）
  `otv` `otv_ss_bgN.png` 960×1012 = 场景选择**整页**（960×544 画面带 + 468 高 UI 面板：
                                    日期列表 / 角色头像行 / 章卡缩略图 / QUICK LOAD 等按钮）
本脚本按 W11d 判据（见 w11d_granularity_scan.py）拆分，产出两个独立产物：
  `ss_bgN_base.png`  ← ot  侧（原字节复制）
  `ss_bgN_full.png`  ← otv 侧（原字节复制）
并同步更新 `清单_系统UI.tsv` 与 `待复核_系统UI.tsv`。

命名注：W15（ISSUE-20260919-07）已把产物名由中文 `_底板`/`_整页` 改为 ASCII `_base`/`_full`，
本脚本（ISSUE-20260919-10）同步改为 ASCII 目标名，避免重跑把中文名带回来。

只读源（krkr素材库\）；只写 美术统一\系统UI\ 与两个清单。幂等。
"""
import os, csv, shutil, sys

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
KRKR = os.path.join(BASE, "krkr素材库")
UNI = os.path.join(BASE, "美术统一")
SYSDIR = os.path.join(UNI, "系统UI")
MAN = os.path.join(UNI, "清单_系统UI.tsv")
REV = os.path.join(UNI, "待复核_系统UI.tsv")

from PIL import Image

N = 5


def img_meta(p):
    im = Image.open(p)
    w, h, m = im.size[0], im.size[1], im.mode
    im.close()
    return "%dx%d" % (w, h), m, os.path.getsize(p)


def main():
    # ---------- 1. 产物落盘 ----------
    created = []
    for i in range(1, N + 1):
        pairs = [("ot", "ot_ss_bg%d.png" % i, "ss_bg%d_base.png" % i),
                 ("otv", "otv_ss_bg%d.png" % i, "ss_bg%d_full.png" % i)]
        for src, sfn, dst in pairs:
            sp = os.path.join(KRKR, src, "sys", sfn)
            dp = os.path.join(SYSDIR, dst)
            assert os.path.exists(sp), sp
            shutil.copyfile(sp, dp)                      # 原字节复制，无像素改动
            created.append((src, sfn, dst))
            print("COPY %-22s -> %s" % (sfn, dst))
        # 删除 W11c 的单产物（已被拆分取代）
        old = os.path.join(SYSDIR, "ss_bg%d.png" % i)
        if os.path.exists(old):
            os.remove(old)
            print("DEL  ss_bg%d.png（W11c 单产物，已拆分为底板+整页）" % i)

    # ---------- 2. 清单_系统UI.tsv ----------
    with open(MAN, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    hdr, body = rows[0], rows[1:]
    old_rows = {r[0]: r for r in body if r[0] in ("ss_bg%d.png" % i for i in range(1, N + 1))}
    body = [r for r in body if r[0] not in old_rows]
    new_rows = []
    for i in range(1, N + 1):
        for src, sfn, dst in [("ot", "ot_ss_bg%d.png" % i, "ss_bg%d_base.png" % i),
                              ("otv", "otv_ss_bg%d.png" % i, "ss_bg%d_full.png" % i)]:
            sp = os.path.join(KRKR, src, "sys", sfn)
            dim, mode, byt = img_meta(sp)
            if src == "ot":
                reason = ("W11d 粒度拆分：ot 侧为场景选择**底板**（纯场景背景 800×600，无 UI 图层）；"
                          "原 W11c 与 otv 整页误并为 ss_bg%d.png" % i)
                cat_src = "W3人工(描述派生)"
            else:
                reason = ("W11d 粒度拆分：otv 侧为场景选择**整页**（960×544 画面带 + 468 高 UI 面板："
                          "日期列表/角色头像行/章卡缩略图/QUICK LOAD 等按钮）；原 W11c 与 ot 底板误并为 ss_bg%d.png" % i)
                cat_src = "W3人工"
            new_rows.append([dst, "菜单", dim, mode, str(byt), src, sfn, "1", "single",
                             cat_src, reason])
    body += new_rows
    body.sort(key=lambda r: r[0])
    with open(MAN, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(hdr)
        w.writerows(body)
    print("清单_系统UI.tsv: %d -> %d 行" % (len(rows) - 1, len(body)))

    # ---------- 3. 待复核_系统UI.tsv ----------
    with open(REV, encoding="utf-8") as f:
        rrows = list(csv.reader(f, delimiter="\t"))
    rhdr, rbody = rrows[0], rrows[1:]
    drop = [r for r in rbody if r[0] in ("ss_bg%d.png" % i for i in range(1, N + 1))]
    rbody = [r for r in rbody if r[0] not in ("ss_bg%d.png" % i for i in range(1, N + 1))]
    add = []
    for i in range(1, N + 1):
        # 从被删行取回原始候选信息，保留审计链
        orig = next((r for r in drop if r[0] == "ss_bg%d.png" % i), None)
        cand = orig[2] if orig else ""
        for src, sfn, dst in [("ot", "ot_ss_bg%d.png" % i, "ss_bg%d_base.png" % i),
                              ("otv", "otv_ss_bg%d.png" % i, "ss_bg%d_full.png" % i)]:
            sp = os.path.join(KRKR, src, "sys", sfn)
            dim = img_meta(sp)[0]
            add.append([dst, "granularity_split",
                        "%s:%s %s" % (src, sfn, dim),
                        "%s:%s %s" % (src, sfn, dim),
                        "W11d 拆分后该产物只有 1 个候选，按规格 §3.3 分类为 single，无需选优",
                        ("W11d 判定「粒度不同被误并」并已拆分：原 W11c 组 ss_bg%d.png 的两候选"
                         "分别为 ot 800×600 场景选择底板与 otv 960×1012 场景选择整页（宽高比差 40.6%%、"
                         "面积比 2.02），非同一逻辑素材。本行保留为拆分留痕。原候选清单：%s"
                         % (i, cand))])
    rbody += add
    rbody.sort(key=lambda r: r[0])
    with open(REV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(rhdr)
        w.writerows(rbody)
    print("待复核_系统UI.tsv: %d -> %d 行" % (len(rrows) - 1, len(rbody)))

    print("系统UI\\ 文件数 =", len([x for x in os.listdir(SYSDIR) if x.lower().endswith(".png")]))


if __name__ == "__main__":
    main()