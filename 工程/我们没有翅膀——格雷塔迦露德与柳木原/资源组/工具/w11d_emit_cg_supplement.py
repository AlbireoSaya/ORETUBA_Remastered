# -*- coding: utf-8 -*-
r"""
W11d / ISSUE-20260918-06 · 任务1附：`CG背景\` 补充分组建议表
=============================================================
输入：子代理工作区\...\W11d\_crosskind.json（w11d_crosskind.py 产出）
产出：资源组\美术统一\_补充分组建议_CG背景_W11d.tsv
只读源；不改 `美术统一\CG背景\` 的任何文件（W11b 产物）。
"""
import os, json, csv

W = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20260918-06\W11d"
UNI = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一"
OUT = os.path.join(UNI, "_补充分组建议_CG背景_W11d.tsv")

recs = json.load(open(os.path.join(W, "_crosskind.json"), encoding="utf-8"))
cg = [r for r in recs if r["verdict"] == "CG"]

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["文件名", "所在kind", "判定", "W11b 现状", "建议动作", "撞名情况", "尺寸",
                "内容bbox", "与同名立绘的MAD/IoU", "判定依据"])
    for r in cg:
        coll = ("⚠ 与 立绘\\%s 撞名（MAD=%s IoU=%s，经比对**非同画**，"
                "属不同资产同名）" % (r["uni"], r.get("mad_vs_chrprod"), r.get("iou_vs_chrprod"))
                if r.get("name_collision") else "无")
        w.writerow([r["orig"] + ".png", r["kind"] + "\\pic\\", "CG",
                    "已收录（类别=CG，选中源 %s，统一名 %s）" % (r["kind"], r["uni"]),
                    "无需并入动作（W11b 已收录）；仅需处理撞名/命名歧义",
                    coll, r["size"], r["bbox"], "", r["reason"]])
print("CG 行数 =", len(cg), "->", OUT)
print("其中撞名 =", sum(1 for r in cg if r.get("name_collision")))