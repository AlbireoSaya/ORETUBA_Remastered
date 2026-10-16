# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · CG 候选集验收包构建脚本（幂等可复现）

输入（只读）：
  · 资源组\美术统一\清单_CG背景.tsv          —— 判读类别 == "CG" 的行 = CG 判读集（869）
  · 资源组\剧本\scene_*.jsonl                —— assets[] 中 kind=="pic" 的 out_relpath
  · 资源组\美术统一\CG背景\<统一名>           —— 源图

选择规则（由主代理实测确定，本脚本照抄，不另立规则）：
  1) CG 判读集   = 清单_CG背景.tsv 中 判读类别=="CG" 的行（869）
  2) 剧本层引用  = scene_*.jsonl 里 kind=="pic" 且 out_relpath 非空者，取
                   basename 去扩展名后按首个 "_" 切成 (源, stem)  —— 唯一 1168
  3) 连接键      = (选中源, 选中原名去掉 "<源>_" 前缀) ∩ 剧本层引用 —— 707
  4) 同场景归并  = 对 stem 做 re.sub(r"(\d)[a-z]$", r"\1", stem) 作组名 —— 357 组

输出（全部落在本脚本同级目录的上一级 = CG候选集\）：
  组\001_<组名>\<统一名>            每组的差分文件（文件名保持 统一名 不变）
  代表图\001_<组名>.png             每组代表图（差分序号最小的一张）
  清单.tsv                          357 行
  接触印相表\sheet_01.png …          6列×6行 = 36 栏/张
  抽查清单.tsv                       15 组（差分最多 5 组 + 固定种子随机 10 组）
  README_验收说明.md                 验收说明（含抽查结论，结论常量见文末）

用法：python build_cg_candidates.py
"""

from __future__ import annotations

import csv
import glob
import io
import json
import math
import os
import random
import re
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- 路径
ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
RES = os.path.join(ROOT, "资源组")
MANIFEST = os.path.join(RES, "美术统一", "清单_CG背景.tsv")
CGDIR = os.path.join(RES, "美术统一", "CG背景")
SCENES = os.path.join(RES, "剧本")
OUT = os.path.join(ROOT, "UI组", "_工作", "ISSUE-20260924-08_鉴赏模式", "CG候选集")

D_GROUP = os.path.join(OUT, "组")
D_REP = os.path.join(OUT, "代表图")
D_SHEET = os.path.join(OUT, "接触印相表")
D_SCRIPT = os.path.join(OUT, "复现脚本")

# ---------------------------------------------------------------- 版式
SHEET_W = 2400
COLS, ROWS = 6, 6
MARGIN = 16
GAP = 8
CELL_W = (SHEET_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS      # 388
CELL_H = 300
HEADER_H = 72
THUMB_MAX = 300                                                  # 最长边

BG_SHEET = (16, 17, 20)
BG_CELL = (34, 36, 41)
FG_CELL_BORDER = (72, 78, 90)
BG_THUMB = (10, 10, 12)
FG_TEXT = (236, 238, 242)
BG_BADGE = (0, 0, 0, 150)

SEED = 20260924

# ---------------------------------------------------------------- 字体
FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
)


def load_font(size):
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------- 选择
def load_selected():
    """返回 [(统一名, 选中源, stem)]，已按规则 1-3 求交集；保持清单原始行序。"""
    rows = [r for r in csv.DictReader(io.open(MANIFEST, encoding="utf-8"), delimiter="\t")
            if r["判读类别"] == "CG"]
    assert len(rows) == 869, "CG 判读集应为 869，实得 %d" % len(rows)

    refs, stems_any = load_refs()
    assert len(refs) == 1168, "剧本层唯一 pic 引用应为 1168，实得 %d" % len(refs)

    strict = select(rows, refs, stems_any, relaxed=False)
    # 旧规则（选中源必须与引用源一致）：707 件
    assert len(strict) == 707, "旧规则交集应为 707，实得 %d" % len(strict)
    sel = select(rows, refs, stems_any, relaxed=True)
    # 新规则（放宽：stem 在任一源下被引用即纳入）：717 件
    assert len(sel) == 717, "放宽后交集应为 717，实得 %d" % len(sel)
    return sel, strict


def load_refs():
    """返回 (refs, stems_any)：
    refs      = {(源, stem)}   —— 剧本层唯一 pic 引用（1168）
    stems_any = {stem: {源,…}} —— 同一 stem 被哪些源引用过（用于放宽后的连接键）
    """
    refs = set()
    stems_any = {}
    for fn in sorted(glob.glob(os.path.join(SCENES, "scene_*.jsonl"))):
        with io.open(fn, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                o = json.loads(line)
                for a in o.get("assets", []):
                    if a.get("kind") != "pic":
                        continue
                    p = a.get("out_relpath") or ""
                    if not p:
                        continue                                     # 无落盘路径 → 不计引用
                    b = os.path.basename(p)
                    stem = os.path.splitext(b)[0]
                    if "_" not in stem:
                        continue
                    pre, rest = stem.split("_", 1)
                    refs.add((pre, rest))
                    stems_any.setdefault(rest, set()).add(pre)
    return refs, stems_any


def select(rows, refs, stems_any, relaxed):
    """连接键（判读类别必须为 CG，由调用方保证）：
       relaxed=False（旧规则）—— (选中源, stem) 必须命中 refs
       relaxed=True （新规则）—— stem 只要在任一源下被引用即纳入
    改因：清单为每张画只保留一个「选中源」（取分辨率最高者），而剧本引用按源代号分目录；
    两者不一致时旧规则会把游戏内确实展示的画整张滤除（实测 6 件整组缺失 + 2 组差分漏计）。
    """
    sel = []
    for r in rows:
        src = r["选中源"]
        orig = r["选中原名"]
        stem = orig[len(src) + 1:] if orig.startswith(src + "_") else orig
        hit = (src, stem) in refs if not relaxed else ((src, stem) in refs or stem in stems_any)
        if hit:
            sel.append((r["统一名"], src, stem, r["尺寸(w,h)"]))
    return sel


def group_stem(stem):
    return re.sub(r"(\d)[a-z]$", r"\1", stem)


def build_groups(sel):
    """返回有序组列表 [{name, members:[(统一名,源,stem,尺寸)], rep}]
    members 按「差分序号」升序（base → a → b → c），用于清单与 组\\ 落盘；
    rep（代表图）= **优先最高分辨率，同分辨率取差分序号最小**。
    改因：代表图是 16:9 重制的缩略图入料，须取组内最清晰的一张（如 asu08 取 967x725 的 cg_asu08a.png）。
    """
    by = {}
    for 统一名, src, stem, size in sel:
        by.setdefault(group_stem(stem), []).append((统一名, src, stem, size))

    groups = []
    for name in sorted(by):
        members = by[name]

        def suf_key(m):
            s = m[2]
            rest = s[len(name):] if s.startswith(name) else s
            return (len(rest), rest)                                 # '' < 'a' < 'b' < …

        members.sort(key=suf_key)

        def rep_key(m):
            w, h = m[3].split("x")
            return (-(int(w) * int(h)),) + suf_key(m)                # 面积降序 → 序号升序

        rep = sorted(members, key=rep_key)[0]
        groups.append({"name": name, "members": members, "rep": rep})
    assert len(groups) == 363, "放宽后应得 363 组，实得 %d" % len(groups)
    return groups


# ---------------------------------------------------------------- 落盘：组 / 代表图
def write_dirs(groups):
    for d in (D_GROUP, D_REP):
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)

    for i, g in enumerate(groups, 1):
        tag = "%03d_%s" % (i, g["name"])
        gd = os.path.join(D_GROUP, tag)
        os.makedirs(gd)
        for 统一名, _src, _stem, _size in g["members"]:
            shutil.copy2(os.path.join(CGDIR, 统一名), os.path.join(gd, 统一名))
        shutil.copy2(os.path.join(CGDIR, g["rep"][0]), os.path.join(D_REP, tag + ".png"))


def write_manifest_tsv(groups):
    p = os.path.join(OUT, "清单.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow(["组序号", "组名", "差分件数", "差分文件名列表", "统一名列表", "来源源代号", "代表图尺寸"])
        for i, g in enumerate(groups, 1):
            srcs = sorted({m[1] for m in g["members"]})
            w.writerow([
                "%03d" % i,
                g["name"],
                len(g["members"]),
                "、".join(m[2] for m in g["members"]),
                "、".join(m[0] for m in g["members"]),
                "、".join(srcs),
                g["rep"][3],
            ])
    return p


# ---------------------------------------------------------------- 差异清单（旧规则 707/357 → 新规则 717/363）
def build_diff_rows(groups, strict):
    """逐组对比：旧规则（选中源须与引用源一致）下的组序 / 件数 vs 新规则。"""
    old = {}
    for 统一名, src, stem, size in strict:
        old.setdefault(group_stem(stem), []).append((统一名, src, stem, size))
    old_names = sorted(old)
    old_idx = {n: i for i, n in enumerate(old_names, 1)}
    new_idx = {g["name"]: i for i, g in enumerate(groups, 1)}

    rows = []
    for name in sorted(set(old_names) | {g["name"] for g in groups}):
        o = old.get(name, [])
        g = next((x for x in groups if x["name"] == name), None)
        n = g["members"] if g else []
        if not o:
            kind = u"新增组（旧规则整组缺失）"
        elif len(o) < len(n):
            kind = u"差分变多"
        elif len(o) == len(n):
            kind = u"不变"
        else:
            kind = u"差分变少"
        rows.append({
            "name": name,
            "old_idx": old_idx.get(name),
            "new_idx": new_idx.get(name),
            "old_n": len(o),
            "new_n": len(n),
            "kind": kind,
            "old_unified": u"、".join(m[0] for m in sorted(o, key=lambda x: x[2])),
            "new_unified": u"、".join(m[0] for m in n),
            "added": u"、".join(m[0] for m in n if m[0] not in {x[0] for x in o}),
        })
    return rows


def write_diff_tsv(rows):
    p = os.path.join(OUT, "差异清单_旧707_新717.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow(["组名", "旧组序号", "新组序号", "旧差分件数", "新差分件数", "变化类型",
                    "本次新增统一名", "旧统一名列表", "新统一名列表"])
        for r in rows:
            w.writerow([r["name"],
                        "" if r["old_idx"] is None else "%03d" % r["old_idx"],
                        "" if r["new_idx"] is None else "%03d" % r["new_idx"],
                        r["old_n"], r["new_n"], r["kind"],
                        r["added"], r["old_unified"], r["new_unified"]])
    return p


# ---------------------------------------------------------------- 接触印相表
def fit_thumb(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    k = min(THUMB_MAX / w, THUMB_MAX / h)
    return im.resize((max(1, int(round(w * k))), max(1, int(round(h * k)))), Image.LANCZOS)


def draw_badge(d, x, y, text, font, anchor):
    """半透明黑底 + 白字角标；anchor ∈ {'lt','rb'}，x/y 为贴边基准点。"""
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    padx, pady = 8, 4
    bw, bh = tw + 2 * padx, th + 2 * pady
    if anchor == "lt":
        bx, by = x, y
    else:
        bx, by = x - bw, y - bh
    layer = Image.new("RGBA", (bw, bh), BG_BADGE)
    d._image.paste(layer, (bx, by), layer)
    d.text((bx + padx - bb[0], by + pady - bb[1]), text, font=font, fill=FG_TEXT)


def build_sheets(groups):
    f_title = load_font(34)
    f_idx = load_font(26)
    f_cnt = load_font(28)
    per = COLS * ROWS
    K = int(math.ceil(len(groups) / per))
    paths = []

    os.makedirs(D_SHEET, exist_ok=True)
    for f in glob.glob(os.path.join(D_SHEET, "*.png")):
        os.remove(f)                       # 先清掉上一轮的 sheet（本函数可单独重跑）

    for k in range(K):
        chunk = groups[k * per:(k + 1) * per]
        nrow = int(math.ceil(len(chunk) / COLS))
        H = MARGIN + HEADER_H + nrow * CELL_H + (nrow - 1) * GAP + MARGIN
        sheet = Image.new("RGB", (SHEET_W, H), BG_SHEET)
        d = ImageDraw.Draw(sheet)

        a = k * per + 1
        b = k * per + len(chunk)
        title = u"CG 候选集  sheet %02d / %02d   ｜   组 %03d\u2013%03d" % (k + 1, K, a, b)
        d.text((MARGIN + 4, MARGIN + 8), title, font=f_title, fill=FG_TEXT)
        d.text((MARGIN + 4, MARGIN + 46),
               u"共 363 组 ｜ 每组一格，格内为代表图（优先最高分辨率） ｜ 左上角=组序号，右下角=差分总数（形如 N/N，仅差分>1 的组才画）",
               font=load_font(20), fill=(150, 156, 168))

        for j, g in enumerate(chunk):
            r, c = divmod(j, COLS)
            x0 = MARGIN + c * (CELL_W + GAP)
            y0 = MARGIN + HEADER_H + r * (CELL_H + GAP)
            cell = Image.new("RGB", (CELL_W, CELL_H), BG_CELL)
            cd = ImageDraw.Draw(cell)
            cd.rectangle([0, 0, CELL_W - 1, CELL_H - 1], outline=FG_CELL_BORDER, width=1)

            im = fit_thumb(os.path.join(CGDIR, g["rep"][0]))
            bx = (CELL_W - im.width) // 2
            by = (CELL_H - im.height) // 2
            cd.rectangle([bx, by, bx + im.width - 1, by + im.height - 1], fill=BG_THUMB)
            cell.paste(im, (bx, by))

            idx = k * per + j + 1
            draw_badge(cd, bx + 5, by + 5, "%03d" % idx, f_idx, "lt")
            if len(g["members"]) > 1:                                # 仅 N>1 画角标（贴合参考图）
                draw_badge(cd, bx + im.width - 6, by + im.height - 6,
                           "%d/%d" % (len(g["members"]), len(g["members"])), f_cnt, "rb")

            sheet.paste(cell, (x0, y0))

        p = os.path.join(D_SHEET, "sheet_%02d.png" % (k + 1))
        sheet.save(p, optimize=True)
        paths.append(p)
    return paths


# ---------------------------------------------------------------- 抽查清单
def pick_spotcheck(groups):
    """差分最多的 5 组（组名升序取前 5）+ 固定种子随机 10 组。返回 [(序号, 组名, 件数)]"""
    idx = {g["name"]: i for i, g in enumerate(groups, 1)}
    most = sorted([g for g in groups if len(g["members"]) == 4], key=lambda g: g["name"])[:5]
    chosen = {g["name"] for g in most}
    rest = [g["name"] for g in groups if g["name"] not in chosen]
    rnd = random.Random(SEED).sample(sorted(rest), 10)
    rows = [(idx[g["name"]], g["name"], len(g["members"])) for g in most]
    rows += [(idx[n], n, len(next(g for g in groups if g["name"] == n)["members"])) for n in sorted(rnd)]
    return rows


def write_spotcheck_tsv(rows, groups):
    byname = {g["name"]: g for g in groups}
    p = os.path.join(OUT, "抽查清单.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow(["组序号", "组名", "差分件数", "抽样理由", "代表图", "统一名列表", "结论", "理由"])
        for n, (idx, name, cnt) in enumerate(rows):
            g = byname[name]
            reason = "差分最多5组" if n < 5 else "随机10组(seed=%d)" % SEED
            concl = SPOTCHECK.get(name, ("", ""))
            w.writerow(["%03d" % idx, name, cnt, reason,
                        "代表图\\%03d_%s.png" % (idx, name),
                        "、".join(m[0] for m in g["members"]),
                        concl[0], concl[1]])
    return p


# ---------------------------------------------------------------- README
SPOTCHECK = {
    # —— 第二轮样本（放宽连接键后，见 README 第六节 B）——
    "ai_06":  (u"正确", u"同一场景同一姿势（特写），仅表情不同：普通／侧目／开口／闭眼笑。"
                        u"该组即旧包**差分漏计**的一组（旧包只取到 `ai_06c`，显示 `1/4`），放宽后 4 件齐，"
                        u"目视确认 4 件确为同场景同姿势，补足正确。"),
    "ai_32":  (u"正确", u"同一场景同一姿势（仰卧），仅表情不同：闭口／开口。"),
    "asu14":  (u"正确", u"同一场景同一姿势（俯卧侧脸），仅表情不同：普通／闭眼开口／侧目。"),
    "e_asu03": (u"单件，无可并差分", u"已核清单内该组仅 1 件（`e_asu03.png`），不存在被拆开的同场景兄弟件。"),
    "hiy10":  (u"正确", u"同一场景同一姿势（围巾街景），仅表情不同：睁眼／闭眼笑。"),
    "mas72":  (u"单件，无可并差分", u"已核清单内该组仅 1 件（`mas72.png`），不存在被拆开的同场景兄弟件。"),
    "nar21":  (u"正确", u"同一场景同一姿势（仰卧），仅表情不同：普通／闭眼／开口／开口·另表情。"),
    "nar62":  (u"正确", u"同一场景同一姿势（涂鸦板前），仅表情不同：开口笑／闭眼笑／开口／闭眼。"),
    "nar67":  (u"正确", u"同一场景同一姿势（车内吃便当），仅表情不同：闭眼笑／开口／侧目／闭眼。"),
    "xx_07":  (u"单件，无可并差分", u"已核清单内该组仅 1 件（`xx_07.png`），不存在被拆开的同场景兄弟件。"),
    "yy_06":  (u"单件，无可并差分", u"已核清单内该组仅 1 件（`yy_06.png`），不存在被拆开的同场景兄弟件。"),
    # —— 第一轮样本（旧 707/357 包，保留记录；组序号已随放宽迁移）——
    "ai_61":  (u"正确", u"同一场景同一姿势（窗边回头），仅表情不同：微笑／闭眼笑／难过／开口。背景与构图完全一致。"),
    "asu10":  (u"正确", u"同一场景同一姿势（仰卧），仅表情不同：普通／闭眼／开口／侧目。"),
    "asu13":  (u"正确", u"同一场景同一姿势（仰卧特写），仅表情不同：普通／开口／脸红／闭眼。"),
    "asu16":  (u"正确（差分含服装状态）",
               u"同一场景同一姿势（仰卧），差分除表情外**还含服装状态递进**（连体衫→开衫+内衣→裸→裸·另表情）。"
               u"按口径「**同场景差分 = 表情 / 动作 / 服装状态**」（主代理 2026-09-24 裁决）**仍按同一栏位**，合并不误。"),
    "asu19":  (u"正确", u"同一场景同一姿势（仰卧特写），仅表情不同：微笑／闭眼／开口／潮红。"),
    "ai_33":  (u"正确", u"同一场景同一姿势（天台便当），仅表情不同：普通／开口／闭眼笑。"),
    "asu15":  (u"正确", u"同一场景同一姿势，仅表情不同：闭口笑／开口。"),
    "e_asu09": (u"单件，无可并差分", u"已核清单内该组仅 1 件（`e_asu09.png`），不存在被拆开的同场景兄弟件。"),
    "hiy16":  (u"正确", u"同一场景同一姿势（女仆装），表情不同；b/c 另有手部位置小幅变化，仍属同场景。"),
    "mis61":  (u"正确", u"同一场景同一姿势（电车窗边比 V），仅表情不同。"),
    "nar61":  (u"单件，无可并差分", u"已核清单内该组仅 1 件（`nar61.png`），不存在被拆开的同场景兄弟件。"),
    "nar68":  (u"正确", u"同一场景同一姿势（车内），仅表情不同：普通／闭眼／侧目／开口。"),
    "ore04":  (u"正确", u"同一场景同一姿势（仰卧），仅表情不同。组内**无 base 件**（只有 `ore04a`–`ore04d`），"
                        u"代表图按规则取后缀最小的 `ore04a`。"),
    "xx_66":  (u"单件，无可并差分", u"已核清单内该组仅 1 件（`xx_66.png`），不存在被拆开的同场景兄弟件。"),
    "yy_12":  (u"单件，无可并差分", u"已核清单内该组仅 1 件（`yy_12.png`），不存在被拆开的同场景兄弟件。"),
}

# ---- 定向核查（超出随机 15 组的额外核查；证据见 抽查证据\补充\）----
# A. 跨源合并 4 组：同组含两个源代号，逐组目视全部成员
CROSS_SOURCE = [
    ("asu07", 3, u"正确", u"同一场景同一姿势（书店），仅表情不同。跨 `otv`/`ot` 两源合并无误。"),
    ("asu08", 3, u"正确", u"同一场景同一姿势（递信封），仅表情不同。跨 `ot`/`otv` 两源合并无误。"),
    ("kob02", 2, u"正确", u"同一场景同一姿势（吃吐司），仅表情不同。跨 `otv`/`ot` 两源合并无误。"),
    ("miy01", 2, u"正确", u"同一场景同一姿势（便利店冰箱前），仅表情不同。跨 `otv`/`ot` 两源合并无误。"),
]

# B. 因「清单选中源 ≠ 剧本引用源」被规则滤除的 10 行（其中 6 行导致整组缺失）
FILTERED = [
    ("ai_04",   "cg_ai_04.png",  "ot",  "otr", u"旧包整组缺失 → 已纳入", u"真事件 CG（角色抱住主人公）。"),
    ("ai_05",   "cg_ai_05.png",  "ot",  "otr", u"旧包整组缺失 → 已纳入", u"真事件 CG（角色吃汉堡）。"),
    ("hiy07",   "cg_hiy07.png",  "otv", "ot",  u"旧包整组缺失 → 已纳入", u"真事件 CG（女仆装角色伏案）。"),
    ("ec10",    "ec10.png",      "otv", "otp", u"旧包整组缺失 → 已纳入", u"角色结局卡（含角色名 + 作品 LOGO），游戏内确实展示。"),
    ("ec16",    "ec16.png",      "ot",  "otp", u"旧包整组缺失 → 已纳入", u"结局卡（角色剪影 + 作品 LOGO），游戏内确实展示。"),
    ("ec21",    "ec21.png",      "ot",  "otp", u"旧包整组缺失 → 已纳入", u"结局卡（角色剪影 + 作品 LOGO），游戏内确实展示。"),
    ("ai_06",   "cg_ai_06.png",  "ot",  "otr", u"旧包差分漏计 → 已修正", u"该组清单内有 4 件差分（同场景仅表情不同），旧包只取到 `ai_06c`（显示 `1/4`），现 4 件齐。"),
    ("ai_06a",  "cg_ai_06a.png", "ot",  "otr", u"旧包差分漏计 → 已修正", u"同上。"),
    ("ai_06b",  "cg_ai_06b.png", "ot",  "otr", u"旧包差分漏计 → 已修正", u"同上。"),
    ("asu01a",  "cg_asu01a.png", "otv", "ot",  u"旧包差分漏计 → 已修正", u"该组清单内有 2 件差分（同场景仅表情不同），旧包只取到 `asu01`（显示 `1/2`），现 2 件齐。"),
]

# C. 代表图分辨率
REP_RES_NOTE = u"代表图规则已由「差分序号最小」改为「**优先最高分辨率，同分辨率取序号最小**」"\
               u"（主代理 2026-09-24 裁决）。修正后 363 组的代表图**全部为组内最高分辨率**："\
               u"旧包里唯一不合格的 `asu08`（旧代表图 `cg_asu08.png` 800x600）现取 `cg_asu08a.png`（967x725）。"

README_HEAD = r"""# CG 候选集 · 用户验收说明

- Issue：ISSUE-20260924-08 ｜ 模块：CG 候选集验收包 ｜ 性质：**只读源 + 本目录产物**
- 源（只读）：`资源组\美术统一\清单_CG背景.tsv`、`资源组\剧本\scene_*.jsonl`、`资源组\美术统一\CG背景\`
- 复现：`复现脚本\build_cg_candidates.py`（幂等，重跑覆盖本目录产物）

---

## 一、这是什么

本作（《我们没有翅膀——格雷塔迦露德与柳木原》）**真正会在游戏里展示的 CG**，
按「同一场景的差分」归并成 **363 个栏位**，供用户亲自验收。

| 项 | 值 |
| --- | --- |
| CG 判读集（清单中 `判读类别=="CG"`） | 869 件 |
| 剧本层实际引用（`scene_*.jsonl` 的 `kind=="pic"`，去重） | 1168 个 (源, stem) |
| **两者交集 = 本交付候选 CG** | **717 件** |
| **归并后栏位数（= 拟做的鉴赏页栏位）** | **363 组** |
| 差分分布 | 1 件 192 组 ／ 2 件 62 组 ／ 3 件 35 组 ／ 4 件 74 组 |

**717 件 = 363 组**：把「同一场景的差分」合成一个栏位，
做法是对文件名 stem 去掉**数字后紧跟的单个小写字母**（`ai_07a` → `ai_07`）。

**「同场景差分」的口径 = 表情 / 动作 / 服装状态**。
即同一场景同一构图下，只差表情、只差动作、或只差服装状态（穿衣→脱衣等），**都算同一栏位**，合并为一格。

> **数字变更说明（主代理 2026-09-24 裁决）**：旧规则 **707 件 / 357 组** → 放宽后 **717 件 / 363 组**。
> 改因：清单为每张画只保留一个「选中源」（取分辨率最高者），而剧本层引用是按源代号分目录的；
> 旧规则要求「选中源 == 引用源」，两者不一致时会把**游戏内确实展示的画整张滤除**
> （实测 6 件整组缺失 + 2 组差分漏计）。放宽为「**stem 在任一源下被剧本引用即纳入**」（`判读类别` 仍必须是 `CG`）后修正。
> 逐组差异见 `差异清单_旧707_新717.tsv`。

## 二、怎么数（与鉴赏页栏位数的关系）

- **363 组 = 363 个栏位**（一组 = 鉴赏页里的一格）。
- 用户给的参考图《我们没有翅膀》鉴赏页为 **24 栏/页** ⇒ **363 / 24 ≈ 15.1 ⇒ 16 页**。
- 本验收包不做游戏内分页，改用 **6 列 × 6 行 = 36 栏/张的接触印相表**（一行放 6 个更省图），
  363 组 ⇒ **共 {NSHEET} 张**（`接触印相表\sheet_01.png` … `sheet_{NSHEETLAST}.png`）。
- 角标：**仅差分件数 N>1 的组才在右下角画 `N/N`**，贴合参考图观感；
  **N=1 的组只画左上角组序号，不画右下角角标**。
- **角标口径说明**：本验收包的 `N/N` 表示「**该栏共 N 张差分且全部在场**」（`N` = 该组差分件数）。
  **产品内角标语义（已解锁 / 总数，形如 `k/N`）在页面设计阶段另行定义，不要用本包的文案当产品口径。**

## 三、怎么挑（验收什么）

请只看两件事，其余不用管：

1. **归并是否正确**
   - 有没有**不同场景被并成一组**（同一格里其实是两张不同的画）；
   - 有没有**同场景被拆开**（本应一格、却占了两格，表现为两张图几乎一样却各占一格）。
   - 判据：**同场景差分 = 表情 / 动作 / 服装状态**（三者之一不同仍算同一栏位）。
2. **有没有不该进的混进来**
   - 背景（`判读类别=="背景"`，322 件）、立绘、系统 UI 一律不应出现在本候选集；
   - 本集只应是**事件 CG（角色入画）**。

对照材料：
- `代表图\<序号>_<组名>.png` —— 一组的代表图，**验收主要看这里**；
  代表图规则 = **优先组内最高分辨率，同分辨率取差分序号最小**（代表图是 16:9 重制的缩略图入料，故取最清晰的一张）；
- `组\<序号>_<组名>\` —— 该组全部差分文件（文件名保持统一名不变，便于溯源）；
- `清单.tsv` —— 363 行，含组名 / 差分件数 / 差分文件名 / 统一名 / 来源源代号 / 代表图尺寸；
- `差异清单_旧707_新717.tsv` —— 相对旧规则的逐组差异与组序号迁移；
- `抽查证据\` —— 构建者抽查时用的并排对照图（15 组 + `补充\` 里的定向核查）。

## 四、发现问题怎么报

请报**组序号 + 文件名**（如「第 042 组 `kob02`：格内是两张不同场景」或
「第 100 组与第 101 组其实是同一场景，应合并」），并可附上 `代表图\042_kob02.png`。
按组序号定位即可，组序号与 `清单.tsv`、`接触印相表`、`代表图`、`组\` 四处一致。

---

## 五、本包自查记录（构建者抽查）

从 363 组中抽 **15 组**逐组**打开全部差分并排目视**（不是只看代表图）：**差分最多的 5 组** +
**固定种子随机 10 组**（`random.Random(20260924)`）。逐组结论见下表，原始清单见 `抽查清单.tsv`。
（放宽连接键后样本组已随之更新；脚本内另保留第一轮 707/357 包已目视过的 11 组结论，作背景记录，不在下表渲染。）

"""

README_TAIL = r"""
---

## 六、定向核查发现（主代理 2026-09-24 已裁决，**本包已按裁决重出**）

15 组随机抽查之外，构建者另做了定向核查，证据在 `抽查证据\补充\`。
**结论：归并规则本身没问题；但旧连接键存在一处结构性缺陷，已按裁决修正**（见 B）。

### A. 跨源合并的 4 组 —— 逐组目视全部成员，**全部正确**

同组含两个源代号（`ot` 与 `otv`，即 PC 版与 PSV 版各存一份）的共 4 组，
逐组并排目视全部成员，**均为同一场景同一姿势、仅表情不同**，合并无误：

{CSROWS}

### B. ✅ 连接键缺陷 —— **已放宽修正**（旧 707/357 → 新 717/363）

**缺陷**：清单为每张画只保留**一个「选中源」**（取分辨率最高者），但剧本层引用是按**源代号分目录**的。
旧连接键要求「选中源 == 引用源」，两者不一致时该画被整张滤除。共 **10 行**受影响：

{FROWS}

- **6 件整组缺失**（`ai_04` / `ai_05` / `hiy07` / `ec10` / `ec16` / `ec21`）：这些画游戏内确实展示，旧包 357 组里没有它们。
  - `ai_04` / `ai_05` / `hiy07`：**真事件 CG**，旧包缺失属漏；
  - `ec10` / `ec16` / `ec21`：**角色结局卡**（角色名 / 剪影 + 作品 LOGO），游戏内确实展示，现按放宽规则一并纳入。
- **2 组差分漏计**：`ai_06`（旧包显示 `1/4`，现按放宽后实际 4 件显示）、`asu01`（旧包显示 `1/2`，现 2 件）。
- 注：另有 152 行 CG 判读集条目在任何源下都未被剧本引用，**按规则一并滤除，这是预期行为**（游戏内不展示）。

**修正方式**：连接键放宽为「**stem 在任一源下被剧本引用即纳入**」（`判读类别` 仍必须是 `CG`）。
结果 **717 件 / 363 组**，差分分布 1 件 192 ／ 2 件 62 ／ 3 件 35 ／ 4 件 74。

**逐组差异清单**（含**组序号迁移**，旧包序号已失效，请以新序号为准）见
`差异清单_旧707_新717.tsv`。摘要：

{DIFFROWS}

### C. 代表图规则 —— **已改为优先最高分辨率**

{REPRES}

---

## 七、构建脚本与复现

```
python 复现脚本\build_cg_candidates.py        # 主产物：组 / 代表图 / 清单.tsv / 差异清单 / 接触印相表 / 抽查清单.tsv / 本 README
python 复现脚本\build_spotcheck_evidence.py   # 抽查证据：抽查证据\组<序号>_<组名>.png（15 组，全部成员并排）
python 复现脚本\build_extra_evidence.py       # 定向核查证据：抽查证据\补充\（跨源 4 组 + 滤除 8 项）
```

主脚本内置断言（**869 / 1168 / 717 / 363** 与差分分布 192·62·35·74），任一不符即报错退出，不会产出半成品。
脚本内同时保留**旧规则断言 707**（`select(..., relaxed=False)`）用于生成差异清单——
**旧值未删**，注释写明「旧规则 707/357 → 放宽后 717/363，原因：选中源与引用源不一致时被滤除」。
重跑幂等：`组\`、`代表图\`、`接触印相表\` 先清空再重建，各 tsv 与本 README 覆盖重写。

## 八、未做 / 未测项

- **未**做游戏内 24 栏/页的真实分页与滚动验证（属 UI 组编辑器侧工作，不在本模块范围）。
- **未**对 717 件逐件做与 `资源组\美术统一\交付清单.tsv` 的交叉核对（本模块只按既定规则求交集）。
- **未**逐件核对 363 组全部 717 件（仅做了 15 组随机/最多差分抽查 + 4 组跨源定向核查 + 8 项滤除核查）。
- **未**复核旧包 357 组的序号到新包 363 组的全量人工映射（映射表由脚本自动生成，见 `差异清单_旧707_新717.tsv`）。
- **未**改任何源文件、未改 git 状态。
"""


def _md_table(rows, head):
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join(["---"] * len(head)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def write_readme(groups, nsheet, spot_rows, diff_rows):
    byname = {g["name"]: g for g in groups}
    lines = [README_HEAD.replace("{NSHEET}", str(nsheet)).replace("{NSHEETLAST}", "%02d" % nsheet)]
    lines.append(u"| 组序号 | 组名 | 差分件数 | 抽样理由 | 同组内是否同场景（表情/动作/服装状态） | 说明 |")
    lines.append(u"| --- | --- | --- | --- | --- | --- |")
    for n, (idx, name, cnt) in enumerate(spot_rows):
        reason = u"差分最多5组" if n < 5 else u"随机10组"
        concl, why = SPOTCHECK.get(name, (u"（待填）", u""))
        lines.append(u"| %03d | `%s` | %d | %s | %s | %s |" % (idx, name, cnt, reason, concl, why))

    cross = [i for i, g in enumerate(groups, 1) if len({m[1] for m in g["members"]}) > 1]
    lines.append(u"\n**跨源合并的 4 组（同组含两个源代号）组序号**：%s。\n"
                 % u"、".join("%03d `%s`" % (i, groups[i - 1]["name"]) for i in cross))

    changed = [r for r in diff_rows if r["kind"] != u"不变"]
    difftbl = _md_table(
        [[u"`%s`" % r["name"],
          u"—" if r["old_idx"] is None else u"%03d" % r["old_idx"],
          u"%03d" % r["new_idx"],
          u"%d → **%d**" % (r["old_n"], r["new_n"]),
          r["kind"],
          u"—" if not r["added"] else u"`%s`" % r["added"].replace(u"、", u"`、`")]
         for r in changed],
        [u"组名", u"旧组序号", u"新组序号", u"差分件数", u"变化类型", u"本次新增统一名"])

    tail = (README_TAIL
            .replace("{CSROWS}", _md_table([[u"`%s`" % a, str(b), c, d] for a, b, c, d in CROSS_SOURCE],
                                           [u"组名", u"差分件数", u"结论", u"说明"]))
            .replace("{FROWS}", _md_table([[u"`%s`" % g, u"`%s`" % n, u"`%s`" % s, u"`%s`" % t, imp, why]
                                           for g, n, s, t, imp, why in FILTERED],
                                          [u"组名", u"统一名", u"清单选中源", u"剧本实际引用源", u"影响", u"目视判定"]))
            .replace("{DIFFROWS}", difftbl)
            .replace("{REPRES}", REP_RES_NOTE))
    lines.append(tail)

    p = os.path.join(OUT, "README_验收说明.md")
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(u"\n".join(lines) + u"\n")
    return p


# ---------------------------------------------------------------- main
def main():
    """默认全量重出；`--sheets-only` 只重出 接触印相表 + README，
    不动 组\\ / 代表图\\ / 清单.tsv / 差异清单（角标等纯版式改动用，省掉 700MB 复制）。"""
    os.makedirs(D_SCRIPT, exist_ok=True)
    only_sheets = "--sheets-only" in sys.argv

    sel, strict = load_selected()
    groups = build_groups(sel)
    print(u"交集 %d 件 / %d 组（旧规则 %d 件 / %d 组）"
          % (len(sel), len(groups), len(strict), len({group_stem(s[2]) for s in strict})))
    dist = {}
    for g in groups:
        dist[len(g["members"])] = dist.get(len(g["members"]), 0) + 1
    print(u"差分分布 %s" % dict(sorted(dist.items())))

    diff_rows = build_diff_rows(groups, strict)

    if only_sheets:
        print(u"[--sheets-only] 跳过 组\\ / 代表图\\ / 清单.tsv / 差异清单")
    else:
        write_dirs(groups)
        print(u"清单 -> %s" % write_manifest_tsv(groups))
        print(u"差异清单 -> %s（变化组 %d）"
              % (write_diff_tsv(diff_rows), sum(1 for r in diff_rows if r["kind"] != u"不变")))

    sheets = build_sheets(groups)
    print(u"接触印相表 %d 张 -> %s" % (len(sheets), D_SHEET))

    spot_rows = pick_spotcheck(groups)
    if not only_sheets:
        print(u"抽查清单 -> %s" % write_spotcheck_tsv(spot_rows, groups))
    print(u"README -> %s" % write_readme(groups, len(sheets), spot_rows, diff_rows))
    print(u"DONE")


if __name__ == "__main__":
    main()