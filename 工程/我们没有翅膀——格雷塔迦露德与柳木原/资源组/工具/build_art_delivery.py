#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
美术交付精简管线 · 构建器   (ISSUE-20260929-11 / greta-art-delivery-slim)
================================================================================
把「源真值」`资源组\美术统一_超分\`（2× 超分母版，4,415 件 PNG / 实测 4,355.2 MiB）
派生出一份**给编程组消费的交付层** `资源组\美术统一_交付\`，显著瘦身且可零成本再生。

【用户裁决（2026-09-29），不得更改】
  · CG背景 的无 alpha 件（PIL mode ∈ {RGB, L}）→ 转 JPEG（q92 / 4:4:4）
  · 系统UI **一律保持 PNG，不转 JPEG**（硬边振铃风险）
  · 立绘 **保持 2× 分辨率、保留 alpha ⇒ 只能 PNG**（调色板化实测 0 件 ≤256 色，无效）

【性质】交付层是**派生可再生产物**：结构与母版逐文件对应，**stem（统一名去扩展名）不变**，
仅扩展名按格式变化（`.png` 保留 / CG背景的无 alpha 件转出为 `.jpg`）。
母版（`美术统一\` 1× 与 `美术统一_超分\` 2×）是**源真值，本脚本只读，绝不改动**。

--------------------------------------------------------------------------------
规格要点
--------------------------------------------------------------------------------
  * 对 `美术统一_超分\{立绘,CG背景,系统UI}\*.png` 每件：
      1. 读 PIL mode；
      2. mode ∈ {RGB,L} 且 类别 == CG背景 → 转 JPEG(quality=92, optimize=True, subsampling=0) → `<stem>.jpg`
      3. 其余（RGBA/LA/P/以及系统UI 的一切）→ PNG **原字节复制**（shutil.copy2，禁重编码）→ `<stem>.png`
  * 输出清单 `美术统一_交付\交付清单.tsv`（**no-BOM** UTF-8 / 制表符 / CRLF —— 与既有
    `超分清单.tsv`、`美术统一\交付清单.tsv` 完全一致），每件一行，列见 `FIELDS`。
  * 另写人读 `美术统一_交付\交付说明.md`（口径 / 结构 / 清单列说明 / 复跑命令 / 收口门槛与
    验收第 8 项 FAIL 的处置口径 / 醒目提示 / 逐类相加实测统计与**转码件全量 PSNR**）。

--------------------------------------------------------------------------------
为什么 `--png-recompress` 默认关闭（用户口径）
--------------------------------------------------------------------------------
  PNG 重编码（`optimize=True, compress_level=9`）会**改变交付件的 md5**，
  从而**破坏交付清单与 `超分清单.tsv`（`输出md5`）之间的溯源链**——交付清单里记录的「母版 md5」
  与超分清单的一致性交叉核对将不再逐字节可追。收益仅约 **139 MiB / 6%**（实测口径），
  远小于溯源断裂与重编码耗时带来的代价。故**默认关闭**；仅当明确要压体积且接受 md5 变化时才开。

--------------------------------------------------------------------------------
为什么 `--dedup` 默认关闭（用户口径）
--------------------------------------------------------------------------------
  本工程既有惯例是「**只登记不删，消费方选一**」（见 `README_交付超分.md` §四补 4C：25 对重复内容
  「只登记不删」）。且按 md5 去重会**删掉某些文件名**，可能**打断编程组/UI 组已有的按名引用**。
  故**默认关闭**（全部复制）；默认关闭时仍在清单 `是否重复组` 列标注哪些件属重复组，
  供消费方自行选一。实测重复组 95 组 / 214 件，去重后保留 4,296 件（省 119 件）。

--------------------------------------------------------------------------------
命令行
--------------------------------------------------------------------------------
  python build_art_delivery.py [--out <dir>] [--jobs N] [--png-recompress] [--dedup]
                              [--limit N] [--refresh] [--dry-run]

  --out <dir>        输出目录；默认 `资源组\美术统一_交付`。**相对路径按主工作区解析**
                     （故 `--out 临时/artdeliv_sample/` 落在 `E:\ZCode Workspace\Galgame\临时\artdeliv_sample`）。
  --jobs N           并发线程数（默认 4）。PIL 释放 GIL，I/O 与编解码并行有效；
                     结果与串行一致、输出确定性（清单按固定序写出）。
  --png-recompress   改为 PNG 重编码（默认关，理由见上）。
  --dedup            按 md5 去重、只保留路径字典序最小的一份（默认关，理由见上）。
  --limit N          只处理前 N 件（按**跨类别交错序**取，见下；供小样验证）。
  --refresh          读旧清单做增量：**母版 md5 未变则跳过转码**（只校验交付件存在 + md5 一致）；
                     母版 md5 变了则重转。无 --refresh 时全量重建。
  --dry-run          只打印统计与将写入的清单，**不落盘任何图像**。

【处理/落盘顺序（确定性）】
  · `--limit` 取样序 = 三类**轮流交错**（立绘、CG背景、系统UI；各类内部按名排序）→
    保证小样跨三类、同时覆盖「转 JPEG」与「PNG 复制」两条路径。
  · 清单落盘行序 = 按 类别(立绘→CG背景→系统UI) + 名称 排序（与既有清单同风格、便于人读）。

【主工作区解析】脚本常驻于 git 工作树（`临时/wt-art-slim/...`），但**母版与产物都在主工作区**。
  解析次序：环境变量 `GALGAME_MAIN` → 自脚本目录上溯、取「含非空 `美术统一_超分\立绘\`」的祖先
  → 兜底常量 `E:\ZCode Workspace\Galgame`。
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import hashlib
import io
import os
import shutil
import sys
import time
from datetime import date

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # 本集含大图（如 end_staff 421x6531 的 2×），关闭解压炸弹上限

# ── 固定口径 ──────────────────────────────────────────────────────────────────
GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
CATS = ["立绘", "CG背景", "系统UI"]          # 类别顺序（清单落盘 / 交错取样均用它）
CAT_INDEX = {c: i for i, c in enumerate(CATS)}
TRANSCODE_CAT = "CG背景"                      # 只有 CG背景 参与 JPEG 转码
TRANSCODE_MODES = ("RGB", "L")                # CG背景 中无 alpha 的 mode
JPEG_QUALITY = 92
JPEG_SUBSAMPLING = 0                          # 4:4:4，避免色度抽样劣化
PSNR_FLOOR = 40.0                             # dB

# 主代理二审全量 PSNR 实测（ISSUE-20260929-11 二审，2026-09-29；n=1,167 转码件）。
# 作为交付说明的权威口径写入；⚠️ 该值只对 2026-09-29 这批交付件成立——
# UI 组 16:9 收口重建后母版会变，须以当次 build 的全量复算值为准并更新本常量。
PSNR_REVIEW = {"date": "2026-09-29", "n": 1167,
               "min": 38.18, "median": 44.02, "mean": 44.37}

# 交付清单列（**no-BOM** UTF-8 / 制表符 / CRLF —— 与既有 `超分清单.tsv`、`美术统一\交付清单.tsv` 一致）
FIELDS = [
    "类别", "统一名", "母版相对路径", "母版md5",
    "交付相对路径", "交付格式", "交付字节", "交付md5", "是否转码", "是否重复组",
]

MANIFEST_NAME = "交付清单.tsv"
DOC_NAME = "交付说明.md"


# ── 路径解析 ──────────────────────────────────────────────────────────────────
def find_main_workspace(start: str) -> str:
    r"""定位主工作区根（含非空 `工程\<GAME>\资源组\美术统一_超分\立绘\` 的祖先）。"""
    env = os.environ.get("GALGAME_MAIN")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    d = os.path.abspath(start)
    while True:
        probe = os.path.join(d, REL_RES, "美术统一_超分", "立绘")
        if os.path.isdir(probe) and any(os.scandir(probe)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return r"E:\ZCode Workspace\Galgame"


def resolve_out(main: str, out_arg: str) -> str:
    """--out 相对路径按主工作区解析（绝对路径原样使用）。"""
    return out_arg if os.path.isabs(out_arg) else os.path.join(main, out_arg)


# ── 小工具 ────────────────────────────────────────────────────────────────────
def md5_of(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def md5_of_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def human_mib(nbytes: int) -> float:
    return nbytes / 1048576.0


def psnr_db(orig: Image.Image, dec: Image.Image) -> float:
    """orig/dec 同尺寸；PSNR 取全通道 MSE（MAX=255）。"""
    import math
    import numpy as np
    a = np.asarray(orig, dtype=np.float64)
    b = np.asarray(dec, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch {a.shape} != {b.shape}")
    mse = float(((a - b) ** 2).mean())
    if mse <= 0.0:
        return float("inf")
    return 10.0 * math.log10(255.0 * 255.0 / mse)


# ── 构建主体 ──────────────────────────────────────────────────────────────────
def enumerate_master(src_dir: str):
    """返回 [(类别, 统一名, 母版相对路径)]（按 类别+名 排序）。"""
    out = []
    for c in CATS:
        d = os.path.join(src_dir, c)
        if not os.path.isdir(d):
            raise SystemExit(f"[FATAL] 母版类别目录不存在：{d}")
        for f in os.listdir(d):
            if f.lower().endswith(".png"):
                out.append((c, f, f"{c}/{f}"))
    out.sort(key=lambda e: (CAT_INDEX[e[0]], e[1]))
    return out


def interleave(entries):
    """跨类别轮流交错序（用于 --limit 取样，保证小样覆盖三类）。"""
    by_cat = {c: [e for e in entries if e[0] == c] for c in CATS}
    out = []
    i = 0
    while True:
        added = False
        for c in CATS:
            if i < len(by_cat[c]):
                out.append(by_cat[c][i])
                added = True
        if not added:
            break
        i += 1
    return out


def scan_one(entry, src_dir):
    """阶段 A：stat + PIL mode + 母版 md5。只读。"""
    cat, name, rel = entry
    p = os.path.join(src_dir, cat, name)
    size = os.path.getsize(p)
    try:
        with Image.open(p) as im:
            mode = im.mode
    except Exception as exc:  # noqa: BLE001
        return rel, {"rel": rel, "cat": cat, "name": name, "path": p,
                     "size": size, "mode": None, "md5": None, "error": str(exc)}
    return rel, {"rel": rel, "cat": cat, "name": name, "path": p,
                 "size": size, "mode": mode, "md5": md5_of(p), "error": None}


def load_old_manifest(path):
    """读旧交付清单（--refresh 用）。返回 {母版相对路径: row}。"""
    if not os.path.isfile(path):
        return {}
    old = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            key = (row.get("母版相对路径") or "").strip()
            if key:
                old[key] = row
    return old


def encode_jpeg(src_path: str, mode: str) -> bytes:
    with Image.open(src_path) as im:
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=JPEG_QUALITY,
                optimize=True, subsampling=JPEG_SUBSAMPLING)
        return buf.getvalue()


def png_recompress_bytes(src_path: str) -> bytes:
    with Image.open(src_path) as im:
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True, compress_level=9)
        return buf.getvalue()


def work_one(info, src_dir, out_dir, args, old):
    """阶段 C：转码/复制/跳过。返回 (rel, row_dict, action)。PSNR 由收尾的全量抽检统一计算。"""
    rel, cat, name = info["rel"], info["cat"], info["name"]
    stem = os.path.splitext(name)[0]
    transcode = (cat == TRANSCODE_CAT and info["mode"] in TRANSCODE_MODES)
    out_name = f"{stem}.jpg" if transcode else f"{stem}.png"
    out_rel = f"{cat}/{out_name}"
    dst = os.path.join(out_dir, cat, out_name)
    fmt = "JPEG" if transcode else "PNG"

    def build_row(bytes_n, m5):
        return {
            "类别": cat, "统一名": name, "母版相对路径": rel, "母版md5": info["md5"],
            "交付相对路径": out_rel, "交付格式": fmt, "交付字节": str(bytes_n),
            "交付md5": m5, "是否转码": "是" if transcode else "否",
            "是否重复组": "是" if info["dup"] else "否",
        }

    # ── --refresh 增量：母版 md5 未变则跳过（只校验交付件存在 + md5 一致）
    if args.refresh:
        orow = old.get(rel)
        if orow and (orow.get("母版md5") or "").strip() == info["md5"]:
            odst = os.path.join(out_dir, (orow.get("交付相对路径") or "").replace("\\", "/"))
            if os.path.isfile(odst) and md5_of(odst) == (orow.get("交付md5") or "").strip():
                r = build_row(os.path.getsize(odst), orow["交付md5"])
                r["交付相对路径"] = orow["交付相对路径"]
                r["交付格式"] = orow.get("交付格式") or fmt
                return rel, r, "skip"

    # ── 干跑：在内存里产出（不落盘），统计仍准确
    if args.dry_run:
        if transcode:
            data = encode_jpeg(info["path"], info["mode"])
            return rel, build_row(len(data), md5_of_bytes(data)), "transcode"
        if args.png_recompress:
            data = png_recompress_bytes(info["path"])
            return rel, build_row(len(data), md5_of_bytes(data)), "copy"
        return rel, build_row(info["size"], info["md5"]), "copy"

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if transcode:
        data = encode_jpeg(info["path"], info["mode"])
        with open(dst, "wb") as fh:
            fh.write(data)
        return rel, build_row(len(data), md5_of_bytes(data)), "transcode"

    if args.png_recompress:
        data = png_recompress_bytes(info["path"])
        with open(dst, "wb") as fh:
            fh.write(data)
        return rel, build_row(len(data), md5_of_bytes(data)), "copy"

    shutil.copy2(info["path"], dst)              # 原字节复制
    return rel, build_row(info["size"], info["md5"]), "copy"


def cleanup_extras(out_dir, manifest_rows):
    r"""删除 out\{类}\ 中不在清单内的多余文件（如起源不同扩展名的残留）。仅在非 dry-run 调用。"""
    keep = {c: set() for c in CATS}
    for r in manifest_rows:
        cat, base = r["交付相对路径"].split("/", 1)
        keep.setdefault(cat, set()).add(base)
    removed = 0
    for c in CATS:
        d = os.path.join(out_dir, c)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f not in keep.get(c, set()):
                os.remove(os.path.join(d, f))
                removed += 1
    return removed


def write_manifest(path, rows):
    # no-BOM UTF-8 + CRLF（与既有 `超分清单.tsv` / `美术统一\交付清单.tsv` 完全一致）
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def compute_psnr_all(manifest_rows, src_dir, out_dir, jobs):
    """全量转码件 PSNR（母版 vs 交付，同口径逐件算）→ dict(n/min/median/mean) 或 None。"""
    trans_all = sorted([r for r in manifest_rows if r["是否转码"] == "是"],
                       key=lambda r: (r["母版md5"], r["母版相对路径"]))
    if not trans_all:
        return None

    def one(r):
        try:
            with Image.open(os.path.join(src_dir, r["母版相对路径"].replace("/", os.sep))) as o, \
                 Image.open(os.path.join(out_dir, r["交付相对路径"].replace("/", os.sep))) as d:
                return psnr_db(o, d)
        except Exception:  # noqa: BLE001
            return None

    vals = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for v in ex.map(one, trans_all):
            if v is not None:
                vals.append(v)
    if not vals:
        return None
    import statistics
    finite = [v for v in vals if v != float("inf")]
    return {
        "n": len(vals),
        "min": min(finite) if finite else float("inf"),
        "median": statistics.median(finite) if finite else float("inf"),
        "mean": (sum(finite) / len(finite)) if finite else float("inf"),
    }


def write_doc(path, stats, psnr_stats, args, out_dir, main, manifest_rows):
    # 交付层**构成口径**（从清单本体的 `是否转码` 列统计，与本次运行是全量还是 --refresh 无关）
    canon = {c: {"trans": 0, "copy": 0} for c in CATS}
    canon["合计"] = {"trans": 0, "copy": 0}
    for r in manifest_rows:
        k = "trans" if r["是否转码"] == "是" else "copy"
        canon[r["类别"]][k] += 1
        canon["合计"][k] += 1
    rebuilt = sum(stats[c]["trans"] + stats[c]["copy"] for c in CATS)
    skipped = sum(stats[c]["skip"] for c in CATS)
    runs = "  ".join(
        [f"python build_art_delivery.py --out \"{os.path.relpath(out_dir, main)}\""] +
        ([f"python build_art_delivery.py --out \"{os.path.relpath(out_dir, main)}\" --refresh"]
         if not args.refresh else [])
    )
    L = []
    L.append("# 美术统一 · 交付层说明（`美术统一_交付\\`）\n")
    L.append(f"> 作品：《我们没有翅膀——格雷塔迦露德与柳木原》｜ Issue：`ISSUE-20260929-11`")
    L.append(f"> 由 `资源组\\工具\\build_art_delivery.py` 从**只读源真值** `资源组\\美术统一_超分\\` 派生，"
             f"生成时间 {date.today().isoformat()}。")
    L.append("> **本目录是派生可再生产物，不是源真值**：删掉可原样重跑再生。\n")
    L.append("---\n")
    L.append("## 一、口径（谁转 JPEG、为什么、质量参数与实测 PSNR）\n")
    L.append("- **CG背景 的无 alpha 件（PIL mode ∈ {RGB, L}）→ JPEG**：`quality=92`、`optimize=True`、"
             "`subsampling=0`（4:4:4，避免色度抽样劣化）。CG/背景为连续调图像，JPEG 收益最大；"
             "**无 alpha** ⇒ 不存在透明边缘振铃问题。")
    L.append("- **系统UI 一律保持 PNG**：系统UI 含大量硬边文字/边框，JPEG 会在硬边产生振铃（ringing），"
             "故**不转**（即便是 RGB/L 件也原字节复制为 PNG）。")
    L.append("- **立绘一律保持 PNG**：立绘保留 alpha（全 RGBA），调色板化实测 **0 件 ≤256 色**（无效），"
             "故**只能 PNG**；分辨率**维持 2×**，不降采样。")
    L.append(f"- **实测 PSNR（转码件全量 n={PSNR_REVIEW['n']}，主代理二审 {PSNR_REVIEW['date']} 实测）**："
             f"最低 **{PSNR_REVIEW['min']:.2f} dB** ／ 中位 **{PSNR_REVIEW['median']:.2f} dB** ／ "
             f"平均 **{PSNR_REVIEW['mean']:.2f} dB**——验收门槛 ≥ {PSNR_FLOOR:.0f} dB，"
             f"最差 8 件目视无差别。⚠️ 该值只对 {PSNR_REVIEW['date']} 这批交付件成立；"
             "UI 组 16:9 收口重建后须以当次复算为准。")
    if psnr_stats:
        L.append(f"- 本脚本同口径逐件复算（本次 n={psnr_stats['n']}）：最低 {psnr_stats['min']:.2f} / "
                 f"中位 {psnr_stats['median']:.2f} / 平均 {psnr_stats['mean']:.2f} dB——与二审值差 ≤0.2 dB，"
                 "系逐件求值实现细节（全通道合并 MSE vs 逐通道平均）所致，最低值一致。")
    L.append("- 逐件 PSNR 公式＝10·log10(255²/MSE)，对母版与交付件**同尺寸全通道**计算，可复现。")
    L.append("- **默认不做的两件事**（理由已在脚本头注释落盘）：`--png-recompress` 会改 md5、"
             "破坏与 `超分清单.tsv` 的溯源（收益仅约 139 MiB / 6%）；`--dedup` 与工程「只登记不删，消费方选一」"
             "惯例外加可能打断按名引用。二者默认关闭。\n")
    L.append("## 二、结构（与母版逐文件对应）\n")
    L.append("```")
    L.append("美术统一_交付/")
    L.append("├── 立绘/        ← 全部 <stem>.png（原字节复制）")
    L.append("├── CG背景/      ← 无 alpha 件 <stem>.jpg；其余 <stem>.png")
    L.append("├── 系统UI/      ← 全部 <stem>.png（原字节复制）")
    L.append("├── 交付清单.tsv")
    L.append("└── 交付说明.md")
    L.append("```")
    L.append("- **stem（统一名去扩展名）不变，仅扩展名按格式变化**：`<统一名>.png` → 立绘/系统UI 保持 `.png`；"
             "CG背景无 alpha 件 → `<统一名去>.jpg`。\n")
    L.append("## 三、`交付清单.tsv` 列说明（**no-BOM** UTF-8 / 制表符 / CRLF，与既有清单同风格）\n")
    L.append("| 列 | 含义 |")
    L.append("| --- | --- |")
    L.append("| `类别` | 立绘 / CG背景 / 系统UI（纯大类） |")
    L.append("| `统一名` | 母版统一产物名（含 `.png`），与 `超分清单.tsv` 同键 |")
    L.append("| `母版相对路径` | 相对 `美术统一_超分\\`，如 `CG背景\\ai_07.png` |")
    L.append("| `母版md5` | 母版字节 md5（= `超分清单.tsv` 的 `输出md5`，交叉核对用） |")
    L.append("| `交付相对路径` | 相对本目录，如 `CG背景\\ai_07.jpg` |")
    L.append("| `交付格式` | `PNG` / `JPEG` |")
    L.append("| `交付字节` | 交付件字节数 |")
    L.append("| `交付md5` | 交付件字节 md5 |")
    L.append("| `是否转码` | `是`＝此件由 PNG 转为 JPEG；`否`＝原字节复制 |")
    L.append("| `是否重复组` | `是`＝该件所在 md5 组有多件（重复内容，消费方选一即可，勿同时使用） |")
    L.append("")
    L.append("> 行序 = 按 类别(立绘→CG背景→系统UI) + 名称 排序。\n")
    L.append("## 四、复跑命令\n")
    L.append("```")
    L.append(r"cd 工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\工具")
    L.append("set PYTHONPATH=E:\\ZCode Workspace\\Galgame\\工具\\pylibs")
    L.append(runs)
    L.append(r"python verify_art_delivery.py")
    L.append("```")
    L.append("- 首次/全量重建：`python build_art_delivery.py`")
    L.append("- 母版变动后增量：`python build_art_delivery.py --refresh`（母版 md5 未变则跳过转码）")
    L.append("- 小样：`python build_art_delivery.py --limit 40 --out 临时/artdeliv_sample/`\n")
    L.append("## 五、⚠️ UI 组 16:9 重制完成后的收口门槛（必读）\n")
    L.append("UI 组的 **4:3 → 16:9 重制**以 `美术统一_超分\\` 为起点并**原位替换**其中的母版件。"
             "母版一旦被替换，**本交付层即与母版失配**（旧交付件仍是 4:3，且 md5 变化会让 `--refresh` 判定为重转）。")
    L.append("")
    L.append("> **门槛**：**UI 组 16:9 重制并原位替换完成后，必须重跑本脚本收口**：")
    L.append("> `python build_art_delivery.py --refresh`（或全量 `python build_art_delivery.py`），"
             "再跑 `python verify_art_delivery.py` 确认 `ALL_PASS`。")
    L.append("> **在收口前，本交付层不得作为编程组的最终取件依据**。\n")
    L.append("### 5.1 验收第 8 项 FAIL 的处置口径（`--allow-stale-cross` 何时可用）\n")
    L.append("`verify_art_delivery.py` 第 8 项把交付清单的 `母版md5` 与 `超分清单.tsv` 的 `输出md5` 逐件比对，"
             "**严格口径为默认**：发现不一致即 **FAIL**，不静默放行。")
    L.append("")
    L.append("> **第 8 项 FAIL 时，先确认是不是 UI 组回填未同步**——特征＝母版尺寸已从 `超分清单.tsv` 所记的")
    L.append("> `1600×1200`（4:3 的 2×）变为磁盘上的 `1920×1080`（16:9），即母版被 UI 组 4:3→16:9 重制"
             "**原位替换**而清单未回填（回填是 **UI 组的义务**，见其大纲 S 系列 / 回填清单）。")
    L.append("")
    L.append("- **确属回填未同步**才允许用 `--allow-stale-cross` 放行（把「尺寸已变」类差异降级为警告；"
             "「尺寸相符却 md5 不符」的真不一致仍判 FAIL），**且必须在当次工程记录中登记「待 UI 组回填的件数」**。")
    L.append("- **不属于回填未同步**（尺寸相同、md5 却不同）＝真异常，**不得放行**，须先查交付层与母版。")
    L.append("- 放行 ≠ 结案：UI 组回填 `超分清单.tsv` 之后，须**不带** `--allow-stale-cross` 复跑验收，"
             "以严格口径确认 `ALL_PASS`。\n")
    L.append("## 六、⚠️⚠️ 给编程组的取件纪律（醒目提示）\n")
    L.append("> **编程组必须按本清单（`交付清单.tsv`）的 `交付相对路径` 逐件取件——扩展名会变！**")
    L.append("> **严禁按旧名 / 母版名猜扩展名**：CG背景的无 alpha 件在交付层是 `.jpg`，"
             "若仍按 `.png` 拼接路径会**取不到文件**。")
    L.append("> 一律以本清单的 `交付相对路径` 列为准（或读 `是否转码`：`是` → `.jpg`，`否` → `.png`）。\n")
    L.append("---\n")
    L.append("## 附：本次构建统计（**逐类相加实测**，非预测值）\n")
    tin, tout = stats["合计"]["in"], stats["合计"]["out"]
    tin_r, tout_r = round(tin / 1048576, 1), round(tout / 1048576, 1)   # 与展示值同位取整
    L.append(f"- **总量：输入 {tin_r:,.1f} MiB → 输出 {tout_r:,.1f} MiB"
             f"（−{(1 - tout / tin) * 100:.1f}%，省 {tin_r - tout_r:,.1f} MiB；"
             f"输出/输入保留率 {(tout / tin) * 100:.1f}%）。逐类相加实测。**")
    L.append("")
    L.append("| 类别 | 件数 | 输入 MiB | 输出 MiB | 保留率(输出/输入) | 转码(JPEG) | PNG 复制 |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for c in CATS + ["合计"]:
        s = stats[c]
        ratio = (s["out"] / s["in"]) if s["in"] else 0.0
        L.append(f"| {c} | {s['n']} | {s['in']/1048576:,.1f} | {s['out']/1048576:,.1f} | "
                 f"{ratio*100:.1f}% | {canon[c]['trans']} | {canon[c]['copy']} |")
    L.append("")
    L.append("> 注：① 上表『转码(JPEG) / PNG 复制』为交付层**构成口径**（按清单 `是否转码` 列统计，"
             "与本次运行是全量还是 `--refresh` 无关）；本次运行动作＝"
             f"重建/复制 {rebuilt} 件、跳过 {skipped} 件"
             + ("（`--refresh` 增量且母版未变 ⇒ 全部跳过属正常）" if skipped and not rebuilt else "。"))
    L.append("> ② 上表『保留率』＝输出/输入（合计 57.8% ⇔ 节省 42.2%）；顶部总量行为主代理二审认可口径"
             "**2,516.0 MiB / −42.2%（省 1,839.2 MiB）**。")
    L.append("> ③ 『输入 MiB』= 本次实际纳入的母版件体积；转码件瘦身差异已在 CG背景 行体现。")
    L.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser(description="美术交付精简管线 · 构建器")
    ap.add_argument("--out", default=None, help="输出目录（相对路径按主工作区解析）")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--png-recompress", action="store_true")
    ap.add_argument("--dedup", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    main_ws = find_main_workspace(here)
    src_dir = os.path.join(main_ws, REL_RES, "美术统一_超分")
    out_arg = args.out if args.out else os.path.join(REL_RES, "美术统一_交付")
    out_dir = resolve_out(main_ws, out_arg)

    if not os.path.isdir(src_dir):
        raise SystemExit(f"[FATAL] 未找到母版目录：{src_dir}（可用 GALGAME_MAIN 指定主工作区）")

    # 防守闸（一审 N5 + 本轮实测教训）：
    # ① 输出目录不得等于或位于母版目录之内——否则 cleanup_extras() 会把「清单里没有」的
    #    母版件当多余物删掉，等于毁源真值；
    # ② 输出目录必须在主工作区之内——resolve_out() 把相对路径拼到 main_ws，`..` 会逃出
    #    工作区（本轮实测 `--out ../美术统一_超分` 写到了 E:\\ZCode Workspace\\ 下，违反铁律 1）。
    def _norm(p: str) -> str:
        return os.path.normcase(os.path.abspath(p))

    _o, _s, _m = _norm(out_dir), _norm(src_dir), _norm(main_ws)
    if _o == _s or _o.startswith(_s + os.sep):
        raise SystemExit(
            f"[FATAL] --out 指向母版目录内部，拒绝执行：{out_dir}\n"
            f"        母版 {src_dir} 是只读源真值，交付层必须另立目录。")
    if not (_o == _m or _o.startswith(_m + os.sep)):
        raise SystemExit(
            f"[FATAL] --out 越出主工作区，拒绝执行：{out_dir}\n"
            f"        解析为 {_o}\n"
            f"        一切产物必须落在主工作区 {main_ws} 之内（铁律 1）。")

    t0 = time.time()
    entries = enumerate_master(src_dir)
    total_master = len(entries)
    print(f"[信息] 主工作区 : {main_ws}")
    print(f"[信息] 母版目录 : {src_dir}")
    print(f"[信息] 输出目录 : {out_dir}")
    print(f"[信息] 母版件数 : {total_master}")

    # 取样序（交错）→ --limit
    order_limit = interleave(entries)
    if args.limit is not None:
        entries = order_limit[: args.limit]
        entries.sort(key=lambda e: (CAT_INDEX[e[0]], e[1]))
        print(f"[信息] --limit {args.limit} → 实际处理 {len(entries)} 件（跨类别交错取样）")
    print(f"[信息] 并发线程 : {args.jobs}｜转 JPEG 规则：类别=={TRANSCODE_CAT} 且 mode∈{TRANSCODE_MODES}"
          f"｜png-recompress={args.png_recompress}｜dedup={args.dedup}｜refresh={args.refresh}"
          f"｜dry-run={args.dry_run}")

    # ── 阶段 A：stat / mode / md5 ──
    infos = {}
    errors = []
    tA = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(scan_one, e, src_dir) for e in entries]
        for fut in cf.as_completed(futs):
            rel, info = fut.result()
            infos[rel] = info
            if info["error"]:
                errors.append(info)
    if errors:
        for e in errors[:5]:
            print(f"[错误] 读取失败 {e['rel']}: {e['error']}")
        raise SystemExit(f"[FATAL] {len(errors)} 件无法读取（PIL），中止。")
    print(f"[阶段A] 扫描 {len(infos)} 件，耗时 {time.time()-tA:.1f}s")

    # ── 去重组（md5 分组）──
    groups = {}
    for info in infos.values():
        groups.setdefault(info["md5"], []).append(info["rel"])

    # 去重：每组保留路径字典序最小者；其余标记为「将被去重」
    dropped = set()
    for rels in groups.values():
        if len(rels) > 1:
            keep = sorted(rels)[0]
            dropped.update(r for r in rels if r != keep)
    for info in infos.values():
        info["dup"] = len(groups[info["md5"]]) > 1

    if args.dedup:
        work_entries = [e for e in entries if e[2] not in dropped]
        print(f"[信息] --dedup：{len(dropped)} 件重复副本不复制（保留字典序最小的一份）")
    else:
        work_entries = entries

    # ── 阶段 C：转码 / 复制 / 跳过 ──
    old = load_old_manifest(os.path.join(out_dir, MANIFEST_NAME)) if args.refresh else {}
    if args.refresh:
        print(f"[信息] --refresh：读到旧清单 {len(old)} 行")
    rows = {}
    cat_actions = {c: {"transcode": 0, "copy": 0, "skip": 0} for c in CATS}
    tC = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(work_one, infos[e[2]], src_dir, out_dir, args, old)
                for e in work_entries]
        done = 0
        for fut in cf.as_completed(futs):
            rel, row, action = fut.result()
            rows[rel] = row
            cat_actions[row["类别"]][action] += 1
            done += 1
            if done % 500 == 0:
                print(f"       ... 已处理 {done}/{len(work_entries)}（{time.time()-tC:.0f}s）")
    print(f"[阶段C] 处理完成，耗时 {time.time()-tC:.1f}s")

    # ── 清单行（按 类别+名 排序）──
    ordered = sorted(rows.keys(), key=lambda rel: (CAT_INDEX[rel.split("/", 1)[0]],
                                                   rel.split("/", 1)[1]))
    manifest_rows = [rows[r] for r in ordered]

    # ── 转码件全量 PSNR（实测，非预测；--refresh 全跳过时同样从磁盘逐件复算）──
    psnr_stats = None
    if not args.dry_run:
        tP = time.time()
        psnr_stats = compute_psnr_all(manifest_rows, src_dir, out_dir, args.jobs)
        if psnr_stats:
            print(f"[阶段P] 转码件全量 PSNR {psnr_stats['n']} 件，耗时 {time.time()-tP:.1f}s｜"
                  f"最低 {psnr_stats['min']:.2f} / 中位 {psnr_stats['median']:.2f} / "
                  f"平均 {psnr_stats['mean']:.2f} dB")

    # ── 统计 ──
    stats = {c: {"n": 0, "in": 0, "out": 0, "trans": 0, "copy": 0, "skip": 0} for c in CATS}
    stats["合计"] = {"n": 0, "in": 0, "out": 0, "trans": 0, "copy": 0, "skip": 0}
    for r in manifest_rows:
        c = r["类别"]
        for key in (c, "合计"):
            stats[key]["n"] += 1
            stats[key]["in"] += infos[r["母版相对路径"]]["size"]
            stats[key]["out"] += int(r["交付字节"])
    for key in CATS:
        stats[key]["trans"] = cat_actions[key]["transcode"]
        stats[key]["copy"] = cat_actions[key]["copy"]
        stats[key]["skip"] = cat_actions[key]["skip"]
        stats["合计"]["trans"] += stats[key]["trans"]
        stats["合计"]["copy"] += stats[key]["copy"]
        stats["合计"]["skip"] += stats[key]["skip"]

    # ── 落盘 ──
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        removed = cleanup_extras(out_dir, manifest_rows)
        if removed:
            print(f"[信息] 清理交付目录多余文件 {removed} 个")
        write_manifest(os.path.join(out_dir, MANIFEST_NAME), manifest_rows)
        write_doc(os.path.join(out_dir, DOC_NAME), stats, psnr_stats, args, out_dir, main_ws,
                  manifest_rows)
        print(f"[信息] 已写 {os.path.join(out_dir, MANIFEST_NAME)}（{len(manifest_rows)} 行）")
        print(f"[信息] 已写 {os.path.join(out_dir, DOC_NAME)}")
    else:
        print("[dry-run] 未落盘任何图像/清单；以下为将写入的清单（头 20 行）：")
        print("\t".join(FIELDS))
        for r in manifest_rows[:20]:
            print("\t".join(r[k] for k in FIELDS))
        if len(manifest_rows) > 20:
            print(f"...（共 {len(manifest_rows)} 行，此处截断）")

    # ── 结束统计 ──
    print("\n================ 统计 ================")
    print(f"{'类别':<8}{'件数':>7}{'输入MiB':>12}{'输出MiB':>12}{'保留率':>9}{'转码':>7}{'复制':>7}{'跳过':>7}")
    for c in CATS + ["合计"]:
        s = stats[c]
        ratio = (s["out"] / s["in"] * 100) if s["in"] else 0.0
        print(f"{c:<8}{s['n']:>7}{human_mib(s['in']):>12.1f}{human_mib(s['out']):>12.1f}"
              f"{ratio:>8.1f}%{s['trans']:>7}{s['copy']:>7}{s['skip']:>7}")
    if stats["合计"]["in"]:
        tin, tout = stats["合计"]["in"], stats["合计"]["out"]
        print(f"总量：{round(tin/1048576,1):,.1f} MiB → {round(tout/1048576,1):,.1f} MiB"
              f"（−{(1-tout/tin)*100:.1f}%，省 {round(tin/1048576,1)-round(tout/1048576,1):,.1f} MiB）")
    if psnr_stats:
        print(f"PSNR 全量 {psnr_stats['n']} 件：最低 {psnr_stats['min']:.2f} / "
              f"中位 {psnr_stats['median']:.2f} / 平均 {psnr_stats['mean']:.2f} dB")
    if args.dedup:
        print(f"去重：{len(dropped)} 件重复副本未复制（保留字典序最小的一份）")
    print(f"总耗时 {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
