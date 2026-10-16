# -*- coding: utf-8 -*-
r"""
W12 · 门控 160 组复核后「7 件被误并素材」补回（**幂等**，2026-09-19）

背景：`ISSUE-20260919-05` 的「跨平台宽高比门控」当初把 160 组判为「不拆」；
vision 全量复核（`子代理工作区\ISSUE-20260919-05\W12d_160组复核\_160组终裁.tsv`）
确证其中 **5 组是真正不同的素材**，且被丢弃的候选**已不在交付集**（全量 md5 查无）——
属实质素材丢失。用户裁决「只拆真正不同的」，故补回 **7 件**：

    bg12b_altot.png    ← krkr素材库\ot\pic\ot_bg12b.png    （含人 vs 空景）
    bg55_altot.png     ← krkr素材库\ot\pic\ot_bg55.png     （含人 vs 空景）
    ec10_altotp.png    ← krkr素材库\otp\pic\otp_ec10.png   （另一名角色）
    ec28_altotp.png    ← krkr素材库\otp\pic\otp_ec28.png   （LOGO「～Prelude～」）
    ec28_altotr.png    ← krkr素材库\otr\pic\otr_ec28.png   （LOGO 大号「R」）
    ec01_altotp.png    ← krkr素材库\otp\pic\otp_ec01.png   （LOGO「～Prelude～」）
    ec01_altot.png     ← krkr素材库\ot\pic\ot_ec01.png     （粉底 vs 场景底）

命名规则沿用既有拆分产物口径：`<统一名去掉扩展名>_alt<源代号>.png`（参照现有 18 件 `*_alt*.png`）。

三件事（对应任务书 A / B / C）：
  A. **原图入集**：7 件字节复制到 `美术统一\CG背景\`，逐件 md5 前后比对，不一致即中止。
  B. **补超分**：复用既有 bbox 管线 `upscale_by_bbox.py`（2× / `upscayl-lite-4x`），
     输出到 `美术统一_超分\CG背景\`，文件名与 A 完全一致；逐件核对
     `输出画布 == 输入画布 × 2` 且 `输出内容bbox == 输入内容bbox × 2`，不一致即中止。
  C. **清单补行**：`交付清单.tsv` / `清单_CG背景.tsv` / `超分清单.tsv` 各补 7 行，
     列与既有行完全同构，并维持既有不变量：
       - `清单_CG背景.tsv` 恒按 `统一名` 升序；
       - `交付清单.tsv` 行序 = `清单_立绘` + `清单_CG背景` + `清单_系统UI`（按统一名）；
       - `超分清单.tsv` 行序与 `交付清单.tsv` 逐行相同。

**路径纪律**（与 `w12_apply_verdicts.py` 同源）：
  - 受控清单（.tsv）在 **worktree** `临时\wt-19-05\...`；
  - PNG 本体（含 `krkr素材库\` 只读源）在 **主工作树** `工程\我们没有翅膀——...\...`。
  - `krkr素材库\` 一律**只读**，本脚本不写、不删其中任何文件。

用法：
    python w12_restore_split.py --check    # 只校验：报告将要发生什么，不复制、不超分、不写盘
    python w12_restore_split.py            # 执行 A + B + C
    python w12_restore_split.py --verify   # 执行后自检（不改盘）
    python w12_restore_split.py --proj <工程目录>   # 覆盖受控清单所在工程目录

幂等：重复执行第二次应为「复制 0 / 超分 0 / 写盘 0」。
"""

import argparse
import csv
import hashlib
import io
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- 路径
WORKTREE_PROJ = r"E:\ZCode Workspace\Galgame\临时\wt-19-05\工程\我们没有翅膀——格雷塔迦露德与柳木原"
MAIN_PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"

CONTROL_ROOT = WORKTREE_PROJ if os.path.isdir(WORKTREE_PROJ) else MAIN_PROJ
ASSET_ROOT = MAIN_PROJ
RES_CONTROL = os.path.join(CONTROL_ROOT, "资源组")
RES_ASSET = os.path.join(ASSET_ROOT, "资源组")

UNIFIED = "美术统一"
UPSCALE = "美术统一_超分"
CAT = "CG背景"

WS = r"E:\ZCode Workspace\Galgame"
PYLIBS = os.path.join(WS, "工具", "pylibs")
PIPELINE = os.path.join(WS, ".zcode", "skills", "asset-upscale", "upscale_by_bbox.py")
TMP = os.path.join(WS, "临时", "w12_restore_split")

SCALE = 2
MODEL = "upscayl-lite-4x"

# ---------------------------------------------------------------- 待补回清单
# (新产物名, 源代号, 源原名, 保留件统一名, 判读类别, 分类, 依据)
ITEMS = [
    ("bg12b_altot.png", "ot", "ot_bg12b.png", "bg12b.png", "背景", "diff_res_diff_drawing",
     "门控拆分：与 bg12b.png（np 空景）非同素材——ot/ota/otp/otr 四源同 md5 的夜晚圣诞街景含约 10 人人群，独立产物"),
    ("bg55_altot.png", "ot", "ot_bg55.png", "bg55.png", "背景", "diff_res_diff_drawing",
     "门控拆分：与 bg55.png（np 空景）非同素材——ot/ota/otp 三源同 md5 的办公室含 3 个人物，独立产物"),
    ("ec01_altot.png", "ot", "ot_ec01.png", "ec01.png", "CG", "diff_res_diff_drawing",
     "门控拆分：与 ec01.png（np 场景底）非同素材——ot 为粉底＋基础 LOGO，独立产物"),
    ("ec01_altotp.png", "otp", "otp_ec01.png", "ec01.png", "CG", "diff_res_diff_drawing",
     "门控拆分：与 ec01.png 非同素材——otp 带「～Prelude～」LOGO（交付集所无），独立产物"),
    ("ec10_altotp.png", "otp", "otp_ec10.png", "ec10.png", "CG", "diff_res_diff_drawing",
     "门控拆分：与 ec10.png（otv 山科京）非同素材——otp 为另一名角色（深色长发＋绿色领结），独立产物"),
    ("ec28_altotp.png", "otp", "otp_ec28.png", "ec28.png", "CG", "diff_res_diff_drawing",
     "门控拆分：与 ec28.png 非同素材——otp 的 LOGO 为「～Prelude～」，独立产物"),
    ("ec28_altotr.png", "otr", "otr_ec28.png", "ec28.png", "CG", "diff_res_diff_drawing",
     "门控拆分：与 ec28.png 非同素材——otr 的 LOGO 为大号艺术字「R」，独立产物"),
]

# 清单列名（2026-09-19 W13 追加 `图片化日文` / `分片角色` 两列后同步）
# 兼容两版表头：`*_LEGACY` = W13 之前（无两列）的旧表头；两版都接受，故本脚本在
# 「已跑 W13」与「未跑 W13」的树上都能工作。其余列一律按列名取（`ix()`），不依赖固定下标。
H_DELIV = ["类别", "判读类别", "图片化日文", "统一名", "尺寸(w,h)", "内容bbox(w,h)", "内容面积",
           "模式", "字节", "选中源", "选中原名", "分类", "分片角色"]
H_CG = ["统一名", "类别", "判读类别", "图片化日文", "组名", "尺寸(w,h)", "模式", "字节",
        "选中源", "选中原名", "组内候选数", "分类", "理由", "分片角色"]
H_UP = ["类别", "图片化日文", "统一名", "输入画布(w,h)", "输入内容bbox(w,h)", "输出画布(w,h)",
        "输出内容bbox(w,h)", "倍数", "输入md5", "输出md5", "状态", "备注"]
_W13COLS = ("图片化日文", "分片角色")
H_DELIV_LEGACY = [c for c in H_DELIV if c not in _W13COLS]
H_CG_LEGACY = [c for c in H_CG if c not in _W13COLS]
H_UP_LEGACY = [c for c in H_UP if c not in _W13COLS]


def ix(hdr):
    """列名 -> 下标（一律按列名取，避免列增删后固定下标失效）。"""
    return {c: i for i, c in enumerate(hdr)}


def head_bad(hdr, *variants):
    """表头不符任一可接受变体则返回 True。"""
    return not any(hdr == v for v in variants)

CHANGES = {"copied": 0, "upscaled": 0, "files_written": 0}


# ---------------------------------------------------------------- 基础工具
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


def pil():
    if PYLIBS not in sys.path:
        sys.path.insert(0, PYLIBS)
    from PIL import Image
    return Image


def probe(path):
    """实测几何：画布 / 内容bbox / 模式 / 是否带 alpha（与 upscale_by_bbox.py 同判据）。"""
    Image = pil()
    with Image.open(path) as im:
        canvas = im.size
        alpha = (im.mode in ("RGBA", "LA")
                 or (im.mode == "P" and "transparency" in im.info))
        if alpha:
            bb = im.convert("RGBA").getchannel("A").getbbox()
            bbox = bb if bb else (0, 0, canvas[0], canvas[1])
        else:
            bbox = (0, 0, canvas[0], canvas[1])
        mode = im.mode
    return canvas, bbox, mode, alpha


def src_path(src_kind, src_name):
    return os.path.join(RES_ASSET, "krkr素材库", src_kind, "pic", src_name)


def tgt_path(root, name):
    return os.path.join(RES_ASSET, root, CAT, name)


# ---------------------------------------------------------------- 前置校验
def precheck():
    problems = []
    # 1) 源文件存在（krkr素材库 只读引用）
    for new, kind, src, keep, jc, cls, why in ITEMS:
        p = src_path(kind, src)
        if not os.path.isfile(p):
            problems.append("源文件缺失：%s" % p)
    # 2) 交付集内同名文件：允许「幂等重跑」（已存在且内容一致），内容不一致则拒绝覆盖
    for new, kind, src, *_ in ITEMS:
        sp = src_path(kind, src)
        dp = tgt_path(UNIFIED, new)
        if os.path.exists(dp):
            if not os.path.isfile(sp) or md5(dp) != md5(sp):
                problems.append("目标已存在且与源 md5 不一致（拒绝覆盖）：%s" % dp)
        op = tgt_path(UPSCALE, new)
        if os.path.exists(op):
            if not os.path.isfile(dp):
                problems.append("超分产物存在但原图缺失：%s" % op)
            else:
                ic, ibb, _, _ = probe(dp)
                oc, obb, _, _ = probe(op)
                if oc != (ic[0] * SCALE, ic[1] * SCALE) or obb != tuple(v * SCALE for v in ibb):
                    problems.append("超分产物几何不符（输出应 = 输入 × %d）：%s" % (SCALE, op))
    # 3) 保留件必须在交付清单里，且其 判读类别/分类 与 ITEMS 声明一致
    hd, dd = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "交付清单.tsv"))
    if head_bad(hd, H_DELIV, H_DELIV_LEGACY):
        problems.append("交付清单表头与预期不符：%s" % hd)
    byname = {}
    di = ix(hd)
    for r in dd:
        if r[di["统一名"]] in byname:
            problems.append("交付清单存在重复统一名：%s" % r[di["统一名"]])
        byname[r[di["统一名"]]] = r
    for new, kind, src, keep, jc, cls, why in ITEMS:
        if keep not in byname:
            problems.append("保留件不在交付清单：%s" % keep)
            continue
        r = byname[keep]
        if r[di["类别"]] != CAT:
            problems.append("保留件类别异常：%s -> %s" % (keep, r[di["类别"]]))
        if r[di["判读类别"]] != jc:
            problems.append("保留件判读类别与声明不一致：%s 清单=%s 声明=%s" % (keep, r[di["判读类别"]], jc))
        if r[di["分类"]] != cls:
            problems.append("保留件分类与声明不一致：%s 清单=%s 声明=%s" % (keep, r[di["分类"]], cls))
    # 4) 分表 / 超分清单表头
    hc, _ = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_CG背景.tsv"))
    hu, _ = read_tsv(os.path.join(RES_CONTROL, UPSCALE, "超分清单.tsv"))
    if head_bad(hc, H_CG, H_CG_LEGACY):
        problems.append("清单_CG背景表头与预期不符：%s" % hc)
    if head_bad(hu, H_UP, H_UP_LEGACY):
        problems.append("超分清单表头与预期不符：%s" % hu)
    # 5) 源/目标 md5 一致性（幂等重跑时目标已存在则此处已被 2) 拦下，故只报源可读）
    for new, kind, src, *_ in ITEMS:
        if os.path.isfile(src_path(kind, src)):
            md5(src_path(kind, src))
    return problems


# ---------------------------------------------------------------- A · 原图入集
def do_copy(apply_):
    todo = []
    for new, kind, src, *_ in ITEMS:
        s, d = src_path(kind, src), tgt_path(UNIFIED, new)
        todo.append((new, s, d))
    done, skipped = [], []
    for new, s, d in todo:
        before = md5(s)
        if os.path.isfile(d) and md5(d) == before:
            skipped.append(new)                            # 幂等：已入集且字节一致
            continue
        if not apply_:
            print("   [plan] 复制 %s -> %s (md5 %s)" % (os.path.basename(s), new, before))
            continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, d)
        after = md5(d)
        if before != after:
            os.remove(d)                                   # 回滚本件
            for (n2, d2) in done:
                if os.path.exists(d2):
                    os.remove(d2)
            die("md5 不一致，已回滚（含此前已复制件）：%s" % d)
        done.append((new, d))
        print("   [copy] %s  md5=%s == 源" % (new, after))
    if skipped:
        print("   [skip] 已入集且 md5 一致，跳过 %d 件：%s" % (len(skipped), ", ".join(skipped)))
    CHANGES["copied"] = len(done)
    return done


# ---------------------------------------------------------------- B · 补超分
def do_upscale(apply_):
    """复用既有 bbox 管线。返回 {统一名: 超分清单行(dict)}。"""
    # 已在超分清单里的条目（幂等）：若输出文件存在且 md5 与清单一致，则跳过
    hu, su = read_tsv(os.path.join(RES_CONTROL, UPSCALE, "超分清单.tsv"))
    ui = ix(hu)
    have = {}
    for r in su:
        if r[ui["类别"]] == CAT:
            have[r[ui["统一名"]]] = dict(zip(hu, r))

    need, reused = [], {}
    for new, kind, src, *_ in ITEMS:
        rec = have.get(new)
        op = tgt_path(UPSCALE, new)
        if rec and os.path.isfile(op) and md5(op) == rec["输出md5"]:
            reused[new] = rec
            continue
        need.append((new, kind, src))

    if not need:
        print("   [skip] 7 件超分产物均已存在且 md5 与清单一致 -> 超分 0 件")
        return reused
    if not apply_:
        for new, *_ in need:
            print("   [plan] 超分 %s（2× / %s）" % (new, MODEL))
        return reused

    os.makedirs(TMP, exist_ok=True)
    man_in = os.path.join(TMP, "补回_输入清单.tsv")
    man_out = os.path.join(TMP, "补回_超分清单.tsv")
    stage = os.path.join(TMP, "stage")

    # 管线所需最小列：类别 / 统一名 / 尺寸(w,h) / 内容bbox(w,h) / 模式
    rows = []
    for new, kind, src in need:
        p = tgt_path(UNIFIED, new)
        canvas, bbox, mode, alpha = probe(p)
        rows.append({"类别": CAT, "统一名": new,
                     "尺寸(w,h)": "%dx%d" % canvas,
                     "内容bbox(w,h)": "%dx%d" % (bbox[2] - bbox[0], bbox[3] - bbox[1]),
                     "模式": mode})
    cols = ["类别", "统一名", "尺寸(w,h)", "内容bbox(w,h)", "模式"]
    with io.open(man_in, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print("   [pipeline] 调用 %s（%d 件，--scale %d --model %s）"
          % (os.path.basename(PIPELINE), len(rows), SCALE, MODEL))

    env = dict(os.environ)
    env["PYTHONPATH"] = PYLIBS
    r = subprocess.run([sys.executable, PIPELINE,
                        "--src", os.path.join(RES_ASSET, UNIFIED),
                        "--out", os.path.join(RES_ASSET, UPSCALE),
                        "--manifest", man_in, "--manifest-out", man_out,
                        "--stage", stage, "--scale", str(SCALE), "--model", MODEL,
                        "--categories", CAT],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        die("upscale_by_bbox.py 失败（returncode=%s）" % r.returncode)

    hu2, su2 = read_tsv(man_out)
    out = {}
    for rec in su2:
        out[rec[hu2.index("统一名")]] = dict(zip(hu2, rec))

    # 逐件复核几何 + md5（不一致即中止）
    for new, kind, src in need:
        rec = out[new]
        ip, op = tgt_path(UNIFIED, new), tgt_path(UPSCALE, new)
        ic, ibb, imode, _ = probe(ip)
        oc, obb, omode, _ = probe(op)
        if oc != (ic[0] * SCALE, ic[1] * SCALE):
            die("输出画布 != 输入画布 × %d：%s (%s vs %s)" % (SCALE, new, oc, ic))
        if (obb[2] - obb[0], obb[3] - obb[1]) != ((ibb[2] - ibb[0]) * SCALE, (ibb[3] - ibb[1]) * SCALE):
            die("输出 bbox != 输入 bbox × %d：%s" % (SCALE, new))
        if tuple(v * SCALE for v in ibb) != tuple(obb):
            die("输出 bbox 偏移 != 输入 bbox × %d：%s %s vs %s" % (SCALE, new, obb, ibb))
        if md5(ip) != rec["输入md5"]:
            die("输入 md5 与清单不符：%s" % new)
        if md5(op) != rec["输出md5"]:
            die("输出 md5 与清单不符：%s" % new)
        if rec["状态"] != "ok" or rec["倍数"] != str(SCALE):
            die("状态/倍数异常：%s -> %s / %s" % (new, rec["状态"], rec["倍数"]))
        print("   [up] %s  %dx%d -> %dx%d  bbox %dx%d -> %dx%d  md5=%s"
              % (new, ic[0], ic[1], oc[0], oc[1],
                 ibb[2] - ibb[0], ibb[3] - ibb[1], obb[2] - obb[0], obb[3] - obb[1], rec["输出md5"]))
    CHANGES["upscaled"] = len(out)
    out.update(reused)
    return out


# ---------------------------------------------------------------- C · 清单补行
def build_rows():
    """用磁盘实测值构造三张表的 7 行。"""
    deliv, cg = [], {}
    for new, kind, src, keep, jc, cls, why in ITEMS:
        ip = tgt_path(UNIFIED, new)
        canvas, bbox, mode, alpha = probe(ip)
        size = os.path.getsize(ip)
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        src_name = src                            # 与既有 _alt 行同构：<源代号>_<原名>.png（= 源文件名）
        deliv.append({"类别": CAT, "判读类别": jc, "统一名": new,
                      "尺寸(w,h)": "%dx%d" % canvas,
                      "内容bbox(w,h)": "%dx%d" % (bbox[2] - bbox[0], bbox[3] - bbox[1]),
                      "内容面积": str(area), "模式": mode, "字节": str(size),
                      "选中源": kind, "选中原名": src_name, "分类": cls})
        cg[new] = {"统一名": new, "类别": CAT, "判读类别": jc, "组名": "",
                   "尺寸(w,h)": "%dx%d" % canvas, "模式": mode, "字节": str(size),
                   "选中源": kind, "选中原名": src_name, "组内候选数": "1",
                   "分类": cls, "理由": why + "（内容 %dx%d=%d）" % (bbox[2] - bbox[0], bbox[3] - bbox[1], area)}
    return deliv, cg


def rewrite_lists(up_rows, deliv_rows, cg_rows, apply_):
    res = {}
    p_deliv = os.path.join(RES_CONTROL, UNIFIED, "交付清单.tsv")
    p_cg = os.path.join(RES_CONTROL, UNIFIED, "清单_CG背景.tsv")
    p_l = os.path.join(RES_CONTROL, UNIFIED, "清单_立绘.tsv")
    p_u = os.path.join(RES_CONTROL, UNIFIED, "清单_系统UI.tsv")
    p_up = os.path.join(RES_CONTROL, UPSCALE, "超分清单.tsv")

    hd, sd = read_tsv(p_deliv)
    hc, sc = read_tsv(p_cg)
    hl, sl = read_tsv(p_l)
    hu_, su_ = read_tsv(p_u)
    hup, sup = read_tsv(p_up)
    if (head_bad(hd, H_DELIV, H_DELIV_LEGACY) or head_bad(hc, H_CG, H_CG_LEGACY)
            or head_bad(hup, H_UP, H_UP_LEGACY)):
        die("清单表头与预期不符，拒绝写入")

    # --- 清单_CG背景：追加（幂等：同名行已存在则跳过）后按统一名排序
    ci = ix(hc); li = ix(hl); si = ix(hu_); di = ix(hd); upi = ix(hup)
    have_c = {r[ci["统一名"]] for r in sc}
    new_c = list(sc)
    added_c = 0
    for new, *_ in ITEMS:
        if new in have_c:
            continue
        new_c.append([cg_rows[new][c] for c in hc])
        added_c += 1
    new_c.sort(key=lambda r: r[ci["统一名"]])

    # --- 交付清单：追加（幂等）后按 立绘 + CG背景 + 系统UI 重排
    dd = {r[di["统一名"]]: list(r) for r in sd}
    if len(dd) != len(sd):
        die("交付清单存在重复统一名")
    dmap = {r["统一名"]: r for r in deliv_rows}
    added_d = 0
    for new, *_ in ITEMS:
        if new in dd:
            continue
        dd[new] = [dmap[new][c] for c in hd]
        added_d += 1
    order = ([r[li["统一名"]] for r in sl] + [r[ci["统一名"]] for r in new_c]
             + [r[si["统一名"]] for r in su_])
    if sorted(order) != sorted(dd):
        die("重排顺序与交付清单统一名集合不一致（立绘 %d + CG %d + 系统UI %d vs 交付 %d）"
            % (len(sl), len(new_c), len(su_), len(dd)))
    new_d = [dd[n] for n in order]

    # --- 超分清单：追加（幂等）后行序对齐交付清单
    su_map = {r[upi["统一名"]]: list(r) for r in sup}
    if len(su_map) != len(sup):
        die("超分清单存在重复统一名")
    added_u = 0
    for new, *_ in ITEMS:
        if new in su_map:
            continue
        if new not in up_rows:
            die("缺少 %s 的超分清单行（超分未完成？）" % new)
        su_map[new] = [up_rows[new][c] for c in hup]
        added_u += 1
    if sorted(su_map) != sorted(dd):
        die("超分清单与交付清单统一名集合不一致")
    new_up = [su_map[n] for n in order]

    res["清单_CG背景.tsv"] = (hc, new_c, added_c)
    res["交付清单.tsv"] = (hd, new_d, added_d)
    res["超分清单.tsv"] = (hup, new_up, added_u)

    for name, (h, rows, _n) in res.items():
        p = p_cg if name == "清单_CG背景.tsv" else (p_deliv if name == "交付清单.tsv" else p_up)
        if write_tsv(p, h, rows, apply_):
            CHANGES["files_written"] += 1
            print("   [list] %s 补 %d 行 -> 共 %d 行（已写盘）" % (name, _n, len(rows)))
        else:
            print("   [list] %s 补 %d 行 -> 共 %d 行（无变化，未写盘）" % (name, _n, len(rows)))
    return res


# ---------------------------------------------------------------- 自检
def verify():
    """不改盘；逐条核对补回结果与既有不变量。"""
    ok = True
    print("=" * 68)
    print("【A】原图入集 + md5 == 源")
    for new, kind, src, *_ in ITEMS:
        s, d = src_path(kind, src), tgt_path(UNIFIED, new)
        a = md5(s) if os.path.isfile(s) else "-"
        b = md5(d) if os.path.isfile(d) else "-"
        flag = "OK " if a == b != "-" else "FAIL"
        ok &= (a == b != "-")
        print("   [%s] %-20s %s" % (flag, new, b))
    print("【B】超分产物几何（输出画布 == 输入画布 × 2；输出 bbox == 输入 bbox × 2，含偏移）")
    for new, *_ in ITEMS:
        ip, op = tgt_path(UNIFIED, new), tgt_path(UPSCALE, new)
        if not os.path.isfile(op):
            print("   [FAIL] %s 输出缺失" % new); ok = False; continue
        ic, ibb, im, _ = probe(ip)
        oc, obb, om, _ = probe(op)
        want_c = (ic[0] * SCALE, ic[1] * SCALE)
        want_b = tuple(v * SCALE for v in ibb)
        flag = "OK " if (oc == want_c and obb == want_b) else "FAIL"
        ok &= (oc == want_c and obb == want_b)
        print("   [%s] %-20s 画布 %dx%d->%dx%d  bbox %s->%s (期望 %s)"
              % (flag, new, ic[0], ic[1], oc[0], oc[1], ibb, obb, want_b))
    print("【C】清单行数与双向一致")
    hd, sd = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "交付清单.tsv"))
    hc, sc = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_CG背景.tsv"))
    hup, sup = read_tsv(os.path.join(RES_CONTROL, UPSCALE, "超分清单.tsv"))
    cnt = {}
    di = ix(hd); ui = ix(hup)
    for r in sd:
        cnt[r[di["类别"]]] = cnt.get(r[di["类别"]], 0) + 1
    print("   交付清单 %d 行 ｜ %s" % (len(sd), cnt))
    print("   清单_CG背景 %d 行 ｜ 超分清单 %d 行" % (len(sc), len(sup)))
    hl2, sl2 = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_立绘.tsv"))
    hu2, su2 = read_tsv(os.path.join(RES_CONTROL, UNIFIED, "清单_系统UI.tsv"))
    ci2, li2, si2 = ix(hc), ix(hl2), ix(hu2)
    print("   交付清单行序 == 立绘+CG+系统UI 拼接 :",
          [r[li2["统一名"]] for r in sl2]
          + [r[ci2["统一名"]] for r in sc]
          + [r[si2["统一名"]] for r in su2]
          == [r[di["统一名"]] for r in sd])
    print("   超分清单行序 == 交付清单行序 :",
          [r[ui["统一名"]] for r in sup] == [r[di["统一名"]] for r in sd])
    print("=" * 68)
    print("结论:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验不写盘（不复制、不超分）")
    ap.add_argument("--verify", action="store_true", help="只做结果自检（不改盘）")
    ap.add_argument("--proj", default=None, help="受控清单所在工程目录")
    args = ap.parse_args()

    global CONTROL_ROOT, RES_CONTROL
    if args.proj:
        CONTROL_ROOT = args.proj
        RES_CONTROL = os.path.join(CONTROL_ROOT, "资源组")

    if args.verify:
        return verify()

    apply_ = not args.check
    print("[W12-restore] 受控清单根 :", CONTROL_ROOT)
    print("[W12-restore] 素材本体根 :", ASSET_ROOT)
    print("[W12-restore] 待补回     : %d 件" % len(ITEMS))

    problems = precheck()
    if problems:
        print("[W12-restore] 前置检查发现问题 %d 项：" % len(problems))
        for p in problems:
            print("   -", p)
        if not args.check:
            die("前置检查未通过，中止（未做任何改动）")
    else:
        print("[W12-restore] 前置检查：通过（源齐备 / 目标无内容冲突 / 表头与保留件声明一致）")

    print("\n[A] 原图入集 ->", os.path.join(RES_ASSET, UNIFIED, CAT))
    do_copy(apply_)

    print("\n[B] 补超分（2× / %s）" % MODEL)
    up_rows = do_upscale(apply_)
    if apply_ and not up_rows:
        die("超分行缺失，中止")

    if not apply_:
        print("\n[C] 清单补行（--check：仅报告，不写盘）")
        print("   将向 交付清单.tsv / 清单_CG背景.tsv / 超分清单.tsv 各补 %d 行" % len(ITEMS))
        print("\n[W12-restore] --check 完成：以上为将要发生的改动（未复制 / 未超分 / 未写盘）")
        return 0

    print("\n[C] 清单补行")
    deliv_rows, cg_rows = build_rows()
    rewrite_lists(up_rows, deliv_rows, cg_rows, apply_)

    print("\n[W12-restore] 补回 %d 件 ｜ 复制 %d ｜ 超分 %d ｜ 写盘 %d 个清单文件"
          % (len(ITEMS), CHANGES["copied"], CHANGES["upscaled"], CHANGES["files_written"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())