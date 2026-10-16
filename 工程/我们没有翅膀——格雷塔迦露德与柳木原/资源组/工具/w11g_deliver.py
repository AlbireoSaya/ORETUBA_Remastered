# -*- coding: utf-8 -*-
"""W11g · 交付包：交付清单.tsv（三类程序化合并）+ 交付统计.md。

列构成（2026-09-19 修订 · W11g-schema；2026-09-19 再修订 · W13 消费侧标记）：
    `类别 判读类别 图片化日文 统一名 尺寸(w,h) 内容bbox(w,h) 内容面积 模式 字节 选中源 选中原名 分类 分片角色`
  - `类别`     = 纯大类（立绘 / CG背景 / 系统UI），由本脚本按分表来源固定写入；
  - `判读类别` = 子分类（立绘/头像/未识别、CG/背景/未判定/其他、存档/图标/…），
                 取自分表的 `判读类别` 列；若分表为旧版（无该列）则回退取旧 `类别` 列
                 —— 故本脚本对新旧两版分表都能跑。
  - `图片化日文` = `是` / 空，取自 `清单_CG背景.tsv` 的同名列（W13 新增）；分表无该列时留空。
  - `分片角色` = `分片成员` / `独立`，取自 `清单_CG背景.tsv` 的同名列（W13 新增）；
                 其余两分表无该列 → 一律 `独立`。
     ⚠ 若分表尚未经 W13 处理，本脚本产出的这两列为空/默认值 —— 请随后运行
       `资源组\\工具\\w13_add_consumption_flags.py`（幂等、自愈：会重算并补正这两列）。

分表由 `w11g_fix_schema.py` 迁移（幂等，只搬列不动行、不动 PNG）。
本脚本按**自身所在位置**推导工程目录（不再硬编码单一 worktree 路径）。
"""
import os, sys, json, hashlib
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")
PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UNI = os.path.join(PROJ, "资源组", "美术统一")
assert os.path.isdir(UNI), UNI

CATS = [("立绘", "清单_立绘.tsv", "立绘"), ("CG背景", "清单_CG背景.tsv", "CG背景"), ("系统UI", "清单_系统UI.tsv", "系统UI")]
HEADER = ["类别", "判读类别", "图片化日文", "统一名", "尺寸(w,h)", "内容bbox(w,h)", "内容面积",
          "模式", "字节", "选中源", "选中原名", "分类", "分片角色"]


def atomic_write(path, text):
    tmp = path + ".tmp_w11g"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def read_tsv(p):
    lines = [ln.rstrip("\n") for ln in open(p, encoding="utf-8") if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def content_bbox(p):
    im = Image.open(p)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bb = im.getbbox()  # 非零 alpha/颜色 的包围盒
        if bb is None:
            return im.width, im.height, 0, 0
        return bb[2] - bb[0], bb[3] - bb[1], bb[0], bb[1]
    return im.width, im.height, 0, 0


def main():
    rows = ["\t".join(HEADER)]
    stat = {}
    for cat, fn, d in CATS:
        hdr, rr = read_tsv(os.path.join(UNI, fn))
        ix = {c: i for i, c in enumerate(hdr)}
        subkey = "判读类别" if "判读类别" in ix else "类别"  # 兼容旧版分表
        jpkey = "图片化日文" if "图片化日文" in ix else None   # W13 列（旧版分表则缺）
        spkey = "分片角色" if "分片角色" in ix else None       # W13 列（仅 CG背景 有）
        n = 0
        for r in rr:
            sub = r[ix[subkey]]
            name = r[ix["统一名"]]
            size = r[ix["尺寸(w,h)"]]
            mode = r[ix["模式"]]
            by = r[ix["字节"]]
            src = r[ix["选中源"]]
            onm = r[ix["选中原名"]]
            cls = r[ix["分类"]]
            jp = r[ix[jpkey]] if jpkey else ""
            sp = r[ix[spkey]] if spkey else "独立"
            if cat == "立绘":
                bb = r[ix["内容bbox(w,h)"]]
                area = r[ix["内容面积"]]
            else:
                bw, bh, _, _ = content_bbox(os.path.join(UNI, d, name))
                bb = "%dx%d" % (bw, bh)
                area = str(bw * bh)
            rows.append("\t".join([cat, sub, jp, name, size, bb, area, mode, by, src, onm, cls, sp]))
            n += 1
        stat[cat] = n
        print("%s: %d 行" % (cat, n))
    atomic_write(os.path.join(UNI, "交付清单.tsv"), "\n".join(rows) + "\n")
    print("交付清单.tsv 合计 %d 行" % (len(rows) - 1))
    json.dump(stat, open(os.path.join(UNI, "_w11g_交付统计.json.tmp"), "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(os.path.join(UNI, "_w11g_交付统计.json.tmp"), os.path.join(UNI, "_w11g_交付统计.json"))


if __name__ == "__main__":
    main()