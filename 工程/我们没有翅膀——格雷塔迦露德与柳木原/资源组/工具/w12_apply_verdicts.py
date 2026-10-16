# -*- coding: utf-8 -*-
r"""
W12 判读终裁回写 + 「立绘 → CG背景」迁移（**幂等**，2026-09-19）

作用（对应 ISSUE-20260919-05 的 W12 判读收尾）：
  1. 把 `子代理工作区\ISSUE-20260919-05\W12_判读\_判读终裁.tsv` 的 403 条结论写回清单：
     - `交付清单.tsv` 403 行 `判读类别` 改写；其中 167 行 `类别` 立绘 → CG背景
     - `清单_立绘.tsv` 删去 167 行、其余 403 行改 `判读类别`
     - `清单_CG背景.tsv` 追加 167 行（**列映射**见 `MAP_L2C`）、其余 403 行改 `判读类别`
     - `清单_系统UI.tsv` 不在本次 403 之内，不动
     - `超分清单.tsv` 167 行 `类别` 同步改 CG背景（其余列不动）
  2. 把 167 个 PNG 从 `美术统一\立绘\` → `美术统一\CG背景\`、
     `美术统一_超分\立绘\` → `美术统一_超分\CG背景\`（**只移动，不改名、不改像素**），
     逐件 md5 前后比对，不一致即中止。
  3. 保持既有不变量：`交付清单 = 清单_立绘 + 清单_CG背景 + 清单_系统UI`（行序一致）、
     `超分清单` 行序与 `交付清单` 逐行相同。

`待复核_*.tsv` 三张表**没有** `类别` / `判读类别` 列（schema 为 统一名/分类/…），
故本次**无需同步**（脚本会打印确认）。

用法：
    python w12_apply_verdicts.py --check     # 只校验不写盘（含撞名/枚举/md5 前置检查）
    python w12_apply_verdicts.py             # 执行
    python w12_apply_verdicts.py --proj <工程目录>   # 覆盖受控清单所在工程目录

幂等：重复执行第二次应为「移动 0 / 写盘 0」。
"""

import argparse
import hashlib
import io
import os
import shutil
import sys

# ---------------------------------------------------------------- 路径
WORKTREE_PROJ = r"E:\ZCode Workspace\Galgame\临时\wt-19-05\工程\我们没有翅膀——格雷塔迦露德与柳木原"
MAIN_PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
VERDICT_DIR = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20260919-05\W12_判读"

# 受控清单（.tsv/.md）所在根：worktree 优先
CONTROL_ROOT = WORKTREE_PROJ if os.path.isdir(WORKTREE_PROJ) else MAIN_PROJ
# PNG 本体所在根：主工作树
ASSET_ROOT = MAIN_PROJ
# 资源组根（清单与素材都在其下）
RES_CONTROL = os.path.join(CONTROL_ROOT, "资源组")
RES_ASSET = os.path.join(ASSET_ROOT, "资源组")

UNIFIED = "美术统一"
UPSCALE = "美术统一_超分"
CAT_L2C = ["立绘", "CG背景", "系统UI"]

# 立绘分表 → CG背景分表 的**列映射**（目标列顺序见 CG 表头）
#   组名：立绘表无对应列 → 填空串（CG 表现有 1,139/1,187 行本就为空）
#   画布(w,h) / 内容bbox(w,h) / 内容面积 / bbox偏移(x0,y0)：CG 表无对应列 → 丢弃
MAP_L2C = {
    "统一名": "统一名",
    "类别": "类别",           # 写 CG背景
    "判读类别": "判读类别",   # 取终裁新判读类别
    "尺寸(w,h)": "尺寸(w,h)",
    "模式": "模式",
    "字节": "字节",
    "选中源": "选中源",
    "选中原名": "选中原名",
    "组内候选数": "组内候选数",
    "分类": "分类",
    "理由": "理由",
}

# 判读类别枚举口径（§美术统一_规格.md 六）
ENUM = {"立绘": {"立绘", "头像"}, "CG背景": {"CG", "背景", "其他"}}

CHANGES = {"moved": 0, "written": 0, "cells": 0, "rows_moved": 0}


# ---------------------------------------------------------------- 工具
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_tsv(path):
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    lines = raw.split("\r\n")
    if lines and lines[-1] == "":
        lines.pop()
    rows = [ln.split("\t") for ln in lines]
    return rows[0], rows[1:]


def tsv_bytes(header, rows):
    return ("\r\n".join(["\t".join(header)] + ["\t".join(r) for r in rows]) + "\r\n").encode("utf-8")


def write_tsv(path, header, rows, apply_):
    new = tsv_bytes(header, rows)
    old = open(path, "rb").read()
    if new == old:
        return False
    if apply_:
        with open(path, "wb") as f:
            f.write(new)
    return True


def die(msg):
    print("!! ABORT:", msg)
    sys.exit(2)


# ---------------------------------------------------------------- 载入终裁
def load_verdicts():
    h, rows = read_tsv(os.path.join(VERDICT_DIR, "_判读终裁.tsv"))
    assert h == ["类别", "统一名", "原判读类别", "新判读类别", "依据", "置信度", "是否可当立绘或背景使用"], h
    vmap = {}
    for r in rows:
        vmap[r[1]] = {"cur": r[0], "new": r[3]}
    h2, rows2 = read_tsv(os.path.join(VERDICT_DIR, "_建议归属.tsv"))
    smap = {}
    for r in rows2:
        smap[r[0]] = {"into": r[3], "action": r[4]}
    return vmap, smap


def validate(vmap, smap):
    if set(vmap) != set(smap):
        die("终裁表与建议归属表的统一名集合不一致")
    mig, keep = [], []
    for n, v in vmap.items():
        target = smap[n]["into"]
        if target not in ENUM:
            die("建议归入清单取值非法：%s -> %s" % (n, target))
        if v["new"] not in ENUM[target]:
            die("判读类别越界：%s 目标类别 %s 不允许 %s" % (n, target, v["new"]))
        if "移入" in smap[n]["action"]:
            if v["cur"] != "立绘" or target != "CG背景":
                die("迁移方向异常：%s cur=%s target=%s" % (n, v["cur"], target))
            mig.append(n)
        else:
            if v["cur"] != target:
                die("非迁移项目标类别异常：%s" % n)
            keep.append(n)
    return sorted(mig), sorted(keep)


# ---------------------------------------------------------------- 移动 PNG
def plan_moves(mig):
    """返回 [(根, 名, 源, 目标)]；已迁移的跳过（幂等）。"""
    plan, skipped = [], []
    for root in (UNIFIED, UPSCALE):
        src_dir = os.path.join(RES_ASSET, root, "立绘")
        dst_dir = os.path.join(RES_ASSET, root, "CG背景")
        if not os.path.isdir(src_dir) or not os.path.isdir(dst_dir):
            die("素材目录缺失：%s / %s" % (src_dir, dst_dir))
        for n in mig:
            s = os.path.join(src_dir, n)
            d = os.path.join(dst_dir, n)
            if os.path.exists(s) and os.path.exists(d):
                die("目标已存在同名文件（拒绝覆盖）：%s" % d)
            if not os.path.exists(s) and not os.path.exists(d):
                die("源与目标均不存在：%s" % s)
            if not os.path.exists(s):
                skipped.append((root, n))   # 已迁移
                continue
            plan.append((root, n, s, d))
    return plan, skipped


def do_moves(plan, apply_):
    if not apply_:
        return
    done = []
    for root, n, s, d in plan:
        before = md5(s)
        shutil.move(s, d)
        after = md5(d)
        if before != after:
            # 回滚本件并中止
            shutil.move(d, s)
            for (r2, n2, s2, d2) in done:
                shutil.move(d2, s2)
            die("md5 不一致，已回滚：%s" % d)
        done.append((root, n, s, d))
    CHANGES["moved"] = len(done)


# ---------------------------------------------------------------- 清单改写
def rewrite_lists(vmap, mig):
    mig_set = set(mig)
    res = {}

    hl, sl = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_立绘.tsv"))
    hc, sc = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_CG背景.tsv"))
    hu, su = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_系统UI.tsv"))
    hd, sd = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "交付清单.tsv"))
    hs, ss = read_tsv(os.path.join(RES_CONTROL, UPSCALE, "超分清单.tsv"))

    for h in (hl, hc, hu, hd, hs):
        if len(h) != len(set(h)):
            die("表头存在重复列名：%s" % h)

    # --- 清单_立绘：删 167 行 + 其余 403 行改判读类别
    new_l, moved_rows = [], {}
    for r in sl:
        n = r[0]
        if n in mig_set:
            moved_rows[n] = list(r)
            continue
        if n in vmap:
            r = list(r)
            r[hl.index("判读类别")] = vmap[n]["new"]
        new_l.append(r)

    # --- 清单_CG背景：现有 403 行改判读类别；追加迁移行（列映射）
    new_c = []
    cg_names = set(r[0] for r in sc)
    for r in sc:
        n = r[0]
        if n in vmap:
            r = list(r)
            r[hc.index("判读类别")] = vmap[n]["new"]
        new_c.append(r)
    for n in mig:
        if n in cg_names:      # 幂等：已迁移过，CG 表已含该行
            continue
        if n not in moved_rows:
            die("迁移项既不在立绘分表也不在 CG背景分表：%s" % n)
        src = moved_rows[n]
        m = dict(zip(hl, src))
        row = []
        for col in hc:
            if col == "组名":
                row.append("")
            else:
                k = None
                for a, b in MAP_L2C.items():
                    if b == col:
                        k = a
                        break
                row.append(m[k] if k is not None else "")
        row[hc.index("类别")] = "CG背景"
        row[hc.index("判读类别")] = vmap[n]["new"]
        new_c.append(row)
    new_c.sort(key=lambda r: r[0])   # 分表恒按统一名排序

    # --- 清单_系统UI：不动（403 件中无系统UI）
    for n in mig_set:
        if any(r[0] == n for r in su):
            die("迁移项竟出现在系统UI清单：%s" % n)

    # --- 交付清单：改 类别/判读类别 + 重排为 立绘→CG背景→系统UI
    dd = {r[2]: list(r) for r in sd}
    if len(dd) != len(sd):
        die("交付清单存在重复统一名")
    for n, r in dd.items():
        if n in vmap:
            r[hd.index("判读类别")] = vmap[n]["new"]
            if n in mig_set:
                r[hd.index("类别")] = "CG背景"
    order = [r[0] for r in new_l] + [r[0] for r in new_c] + [r[0] for r in su]
    if sorted(order) != sorted(dd):
        die("重排顺序与交付清单统一名集合不一致")
    new_d = [dd[n] for n in order]

    # --- 超分清单：167 行改 类别；行序对齐新交付清单
    sd2 = {r[1]: list(r) for r in ss}
    if len(sd2) != len(ss):
        die("超分清单存在重复统一名")
    for n, r in sd2.items():
        if n in mig_set:
            r[hs.index("类别")] = "CG背景"
    if sorted(sd2) != sorted(dd):
        die("超分清单与交付清单统一名集合不一致")
    new_s = [sd2[n] for n in order]

    res["清单_立绘.tsv"] = (hl, new_l)
    res["清单_CG背景.tsv"] = (hc, new_c)
    res["交付清单.tsv"] = (hd, new_d)
    res["超分清单.tsv"] = (hs, new_s)
    res["_counts"] = (len(new_l), len(new_c), len(su))
    res["_moved_rows"] = len(moved_rows)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验不写盘")
    ap.add_argument("--proj", default=None, help="受控清单所在工程目录")
    args = ap.parse_args()
    apply_ = not args.check

    global CONTROL_ROOT, RES_CONTROL
    if args.proj:
        CONTROL_ROOT = args.proj
        RES_CONTROL = os.path.join(CONTROL_ROOT, "资源组")

    print("[W12] 受控清单根 :", CONTROL_ROOT)
    print("[W12] 素材本体根 :", ASSET_ROOT)

    vmap, smap = load_verdicts()
    print("[W12] 终裁 %d 条；原判读分布 %s" % (len(vmap), _dist(vmap, "cur")))
    mig, keep = validate(vmap, smap)
    print("[W12] 迁移(立绘→CG背景) %d 件；留在立绘 %d 件" % (len(mig), len(keep)))
    print("[W12] 新判读类别分布 %s" % _dist(vmap, "new"))

    plan, skipped = plan_moves(mig)
    print("[W12] 待移动 PNG %d 件（已迁移跳过 %d）" % (len(plan), len(skipped)))

    res = rewrite_lists(vmap, mig)
    l, c, u = res["_counts"]
    print("[W12] 迁移后行数：立绘 %d / CG背景 %d / 系统UI %d = %d" % (l, c, u, l + c + u))
    print("[W12] 待复核表 schema 无 类别/判读类别 列 -> 本次无需同步")

    # 逐文件写盘（内容相同则不写）
    written = []
    for name, key in (("清单_立绘.tsv", "清单_立绘.tsv"),
                      ("清单_CG背景.tsv", "清单_CG背景.tsv"),
                      ("交付清单.tsv", "交付清单.tsv")):
        p = os.path.join(RES_CONTROL, UNIFIED, name)
        h, rows = res[key]
        if write_tsv(p, h, rows, apply_):
            written.append(name)
    p = os.path.join(RES_CONTROL, UPSCALE, "超分清单.tsv")
    h, rows = res["超分清单.tsv"]
    if write_tsv(p, h, rows, apply_):
        written.append("超分清单.tsv")

    do_moves(plan, apply_)

    print("[W12] 移动 %d 件；写盘 %d 个文件：%s" % (CHANGES["moved"], len(written), ", ".join(written) or "-"))
    if args.check:
        print("[W12] --check 模式：未写盘、未移动（以上为将要发生的改动）")
    return 0


def _dist(vmap, k):
    d = {}
    for v in vmap.values():
        d[v[k]] = d.get(v[k], 0) + 1
    return " / ".join("%s %d" % (a, b) for a, b in sorted(d.items()))


if __name__ == "__main__":
    sys.exit(main())