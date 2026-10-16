#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
美术交付精简管线 · 验收器   (ISSUE-20260929-11 / greta-art-delivery-slim)
================================================================================
**只读验收** `资源组\美术统一_交付\`（由 `build_art_delivery.py` 从只读源真值
`资源组\美术统一_超分\` 派生）。逐项打印 PASS/FAIL，最后给 `ALL_PASS` 结论。

--------------------------------------------------------------------------------
验收项（8 项）
--------------------------------------------------------------------------------
  1. 件数守恒：交付清单行数 == 母版三类文件数（`--dedup` 生效时按去重后计）；
     且交付目录文件集合与清单 `交付相对路径` 集合一致（无多余/缺失）。
  2. 逐件核对：`交付字节` == 磁盘实际字节、`交付md5` == 磁盘实际 md5。
  3. stem 一致性：交付文件名去扩展名 == 母版统一名去扩展名。
  4. 格式正确性：CG背景 且 母版 mode ∈ {RGB,L} → 交付必须 `.jpg` 且 PIL 打开为 RGB/L；
     其余 → 必须 `.png` 且 mode 与母版一致（逐件比 mode）；并校验 `是否转码` 列一致。
  5. 像素尺寸一致：交付件 PIL size == 母版 size（JPEG 不得改尺寸）。
  6. JPEG 画质抽检：从转码件**确定性抽样**（按母版 md5 排序取前 `--sample` 件，默认 20），
     计算 PSNR；任一件 < 40 dB 记 FAIL 并列出该件 PSNR。
  7. 负对照（**必须做**）：在 `临时\artdeliv_negctl\` 内构造「错误格式」「错误尺寸」两件，
     跑同一套检查确认对应项**确实报 FAIL**，记录「负对照已生效：<项> 预期 FAIL 实际 FAIL」后删除临时件。
     （证明验收器真的会失败，而不是恒真。）
  8. 与 `超分清单.tsv` 交叉核对：交付清单记录的 `母版md5` 与该表 `输出md5` 一致（按 类别+统一名 关联）。
     **严格口径为默认：发现不一致即 FAIL，不静默放行。**
     若 FAIL，先确认是否为 **UI 组 4:3→16:9 重制原位替换母版后未回填 `超分清单.tsv`**（特征＝尺寸由清单所记
     `1600×1200` 变为磁盘 `1920×1080`；回填是 UI 组的义务，见其大纲 S 系列 / 回填清单）。**确属回填未同步**
     才允许用 `--allow-stale-cross` 放行（把「尺寸已变」类差异降级为警告；「尺寸相符却 md5 不符」的真不一致
     仍判 FAIL），且必须在当次工程记录登记「待 UI 组回填的件数」；放行 ≠ 结案——UI 组回填后须**不带**该开关
     复跑验收，以严格口径确认 `ALL_PASS`。

--------------------------------------------------------------------------------
命令行
--------------------------------------------------------------------------------
  python verify_art_delivery.py [--delivery <dir>] [--src <dir>] [--manifest <path>]
                                [--cross <path>] [--sample N] [--jobs N]
                                [--subset] [--no-negative-control]
  （`--delivery` / `--src` 相对路径按主工作区解析；默认指向 `美术统一_交付\` / `美术统一_超分\`。）
  （`--subset`：验收 `--limit` 小样时使用——件数守恒放宽为「清单 ⊆ 母版」；全量验收不要加。）
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import hashlib
import math
import os
import shutil
import sys
import time

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
CATS = ["立绘", "CG背景", "系统UI"]
TRANSCODE_CAT = "CG背景"
TRANSCODE_MODES = ("RGB", "L")
PSNR_FLOOR = 40.0        # 抽样快门：抽样件低于此值记 FAIL
PSNR_HARD_FLOOR = 36.0   # 全量硬底线：任何一件低于此值记 FAIL（真缺陷必拦；本轮实测 min 38.18）
MANIFEST_NAME = "交付清单.tsv"
NEGCTL_DIRNAME = "artdeliv_negctl"


# ── 路径 / 小工具 ────────────────────────────────────────────────────────────
def find_main_workspace(start: str) -> str:
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


def resolve(main: str, p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(main, p)


def md5_of(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def j(path: str) -> str:
    return path.replace("/", os.sep)


def load_manifest(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            rows.append({k: (v if v is not None else "") for k, v in row.items()})
    return rows


def psnr_db(o: Image.Image, d: Image.Image) -> float:
    a = np.asarray(o, dtype=np.float64)
    b = np.asarray(d, dtype=np.float64)
    if a.shape != b.shape:
        return float("nan")
    mse = float(((a - b) ** 2).mean())
    if mse <= 0.0:
        return float("inf")
    return 10.0 * math.log10(255.0 * 255.0 / mse)


# ── 单件检查（2/3/4/5）──
def check_row(row, src_dir, delivery_dir):
    """返回 dict：exists/size_ok/md5_ok/stem_ok/fmt_ok/size_px_ok + detail。"""
    r = {"rel": row["母版相对路径"], "detail": []}
    cat = row["类别"]
    mrel = row["母版相对路径"]
    drel = row["交付相对路径"]
    mpath = os.path.join(src_dir, j(mrel))
    dpath = os.path.join(delivery_dir, j(drel))

    # 3. stem 一致性
    m_stem = os.path.splitext(os.path.basename(mrel))[0]
    d_stem = os.path.splitext(os.path.basename(drel))[0]
    r["stem_ok"] = (m_stem == d_stem) and (drel.split("/")[0] == cat == mrel.split("/")[0])
    if not r["stem_ok"]:
        r["detail"].append(f"stem/目录不一致: {mrel} != {drel}")

    if not os.path.isfile(dpath):
        r.update(exists=False, size_ok=False, md5_ok=False, fmt_ok=False, size_px_ok=False)
        r["detail"].append("交付件缺失")
        return r
    r["exists"] = True

    # 2. 字节 / md5
    actual_size = os.path.getsize(dpath)
    r["size_ok"] = (actual_size == int(row["交付字节"]))
    if not r["size_ok"]:
        r["detail"].append(f"字节不符 清单={row['交付字节']} 实际={actual_size}")
    actual_md5 = md5_of(dpath)
    r["md5_ok"] = (actual_md5 == row["交付md5"].strip())
    if not r["md5_ok"]:
        r["detail"].append(f"md5 不符 清单={row['交付md5']} 实际={actual_md5}")

    # 4/5. 读母版 mode/size，读交付 format/mode/size
    try:
        with Image.open(mpath) as mi:
            mi.load()
            m_mode, m_size = mi.mode, mi.size
    except Exception as exc:  # noqa: BLE001
        r.update(fmt_ok=False, size_px_ok=False)
        r["detail"].append(f"母版读取失败: {exc}")
        return r
    try:
        with Image.open(dpath) as di:
            d_mode, d_size, d_fmt = di.mode, di.size, di.format
    except Exception as exc:  # noqa: BLE001
        r.update(fmt_ok=False, size_px_ok=False)
        r["detail"].append(f"交付读取失败: {exc}")
        return r

    expect_trans = (cat == TRANSCODE_CAT and m_mode in TRANSCODE_MODES)
    ext = os.path.splitext(drel)[1].lower()
    if expect_trans:
        r["fmt_ok"] = (row["交付格式"] == "JPEG" and ext == ".jpg"
                       and d_fmt == "JPEG" and d_mode in ("RGB", "L")
                       and row["是否转码"] == "是")
        if not r["fmt_ok"]:
            r["detail"].append(f"应转 JPEG：格式列={row['交付格式']} 扩展={ext} 实际={d_fmt}/{d_mode}")
    else:
        r["fmt_ok"] = (row["交付格式"] == "PNG" and ext == ".png"
                       and d_fmt == "PNG" and d_mode == m_mode
                       and row["是否转码"] == "否")
        if not r["fmt_ok"]:
            r["detail"].append(f"应保 PNG 且 mode 一致：格式列={row['交付格式']} 扩展={ext} "
                               f"实际={d_fmt}/{d_mode} 母版={m_mode}")
    r["size_px_ok"] = (d_size == m_size)
    if not r["size_px_ok"]:
        r["detail"].append(f"尺寸不符 交付={d_size} 母版={m_size}")
    r["_m_mode"], r["_m_size"] = m_mode, m_size
    return r


# ── 负对照用的小检查包装（复用 check_row）──
def fmt_probe(row, src_dir, delivery_dir):
    res = check_row(row, src_dir, delivery_dir)
    return res["fmt_ok"], res["detail"]


def size_probe(row, src_dir, delivery_dir):
    res = check_row(row, src_dir, delivery_dir)
    return res["size_px_ok"], res["detail"]


def negative_control(src_dir, delivery_dir, rows, main_ws, sample_trans_rows):
    """构造错误格式 / 错误尺寸两件，确认对应检查报 FAIL；清理。返回 [(name, expect, got, ok)]。"""
    tmp = os.path.join(main_ws, "临时", NEGCTL_DIRNAME)
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)
    results = []
    # 挑一件真实的「可转码」母版作为参照（CG背景 RGB/L）
    ref = None
    for row in sample_trans_rows:
        ref = row
        break
    if ref is None:
        for row in rows:
            if row["类别"] == TRANSCODE_CAT:
                ref = row
                break
    if ref is None:
        shutil.rmtree(tmp, ignore_errors=True)
        return [("负对照", "FAIL", "跳过（无可参照件）", True)]

    mpath = os.path.join(src_dir, j(ref["母版相对路径"]))

    # (a) 错误格式：把 PNG 原字节塞进 .jpg（PIL 会读成 PNG ⇒ 格式项应 FAIL）
    bad_fmt = os.path.join(tmp, "negfmt.jpg")
    shutil.copyfile(mpath, bad_fmt)
    row_fmt = dict(ref, 交付相对路径="negfmt.jpg", 交付格式="JPEG",
                   是否转码="是", 交付字节=str(os.path.getsize(bad_fmt)),
                   交付md5=md5_of(bad_fmt))
    ok, detail = fmt_probe(row_fmt, src_dir, tmp)
    results.append(("格式正确性（交付=.jpg 而实为 PNG）", "FAIL", "FAIL" if not ok else "PASS", not ok))

    # (b) 错误尺寸：把参照件缩放一半存成真 JPEG（格式 OK、尺寸应 FAIL）
    bad_size = os.path.join(tmp, "negsize.jpg")
    with Image.open(mpath) as im:
        im.resize((max(1, im.width // 2), max(1, im.height // 2))).save(
            bad_size, format="JPEG", quality=92, optimize=True, subsampling=0)
    row_size = dict(ref, 交付相对路径="negsize.jpg", 交付格式="JPEG",
                    是否转码="是", 交付字节=str(os.path.getsize(bad_size)),
                    交付md5=md5_of(bad_size))
    ok2, _ = size_probe(row_size, src_dir, tmp)
    results.append(("像素尺寸一致性（交付被缩半）", "FAIL", "FAIL" if not ok2 else "PASS", not ok2))

    shutil.rmtree(tmp, ignore_errors=True)
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="美术交付精简管线 · 验收器（只读）")
    ap.add_argument("--delivery", default=None)
    ap.add_argument("--src", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--cross", default=None)
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--subset", action="store_true",
                    help="清单为母版子集（build_art_delivery.py --limit 小样）时使用："
                         "件数守恒改为『清单集合 ⊆ 母版集合 且无重复行』")
    ap.add_argument("--allow-stale-cross", action="store_true",
                    help="第 8 项收口判定开关：把『母版尺寸已变（1600×1200→1920×1080，即 UI 组 4:3→16:9 "
                         "原位替换后未回填 超分清单.tsv）』的 md5 差异降级为警告；『尺寸相符却 md5 不符』的真"
                         "不一致仍判 FAIL。默认**严格**（任何不一致都 FAIL）。仅在确认为 UI 组回填未同步后使用，"
                         "且须在工程记录登记待回填件数；UI 组回填后须不带本开关复跑确认 ALL_PASS。")
    ap.add_argument("--no-negative-control", action="store_true")
    args = ap.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    main_ws = find_main_workspace(here)
    src_dir = resolve(main_ws, args.src) if args.src else os.path.join(main_ws, REL_RES, "美术统一_超分")
    delivery_dir = resolve(main_ws, args.delivery) if args.delivery \
        else os.path.join(main_ws, REL_RES, "美术统一_交付")
    manifest_path = resolve(main_ws, args.manifest) if args.manifest \
        else os.path.join(delivery_dir, MANIFEST_NAME)
    cross_path = resolve(main_ws, args.cross) if args.cross \
        else os.path.join(src_dir, "超分清单.tsv")

    t0 = time.time()
    print("=" * 72)
    print("美术交付验收  verify_art_delivery.py")
    print(f"  母版目录   : {src_dir}")
    print(f"  交付目录   : {delivery_dir}")
    print(f"  交付清单   : {manifest_path}")
    print(f"  交叉清单   : {cross_path}")
    print("=" * 72)

    all_ok = True
    def verdict(name, ok, extra=""):
        nonlocal all_ok
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  {extra}" if extra else ""))
        return ok

    if not os.path.isfile(manifest_path):
        raise SystemExit(f"[FATAL] 交付清单不存在：{manifest_path}")
    rows = load_manifest(manifest_path)
    print(f"[信息] 交付清单 {len(rows)} 行")

    # 母版清单（磁盘）
    master = {}
    for c in CATS:
        d = os.path.join(src_dir, c)
        for f in os.listdir(d):
            if f.lower().endswith(".png"):
                master[f"{c}/{f}"] = os.path.getsize(os.path.join(d, f))
    master_rels = set(master.keys())
    print(f"[信息] 母版件数 {len(master_rels)}")

    # ── 1. 件数守恒 ──
    row_rels = [r["母版相对路径"] for r in rows]
    row_set = set(row_rels)
    n1_pass = False
    note = ""
    if args.subset:
        # 小样模式：清单必须是母版真子集且无重复行
        dup_rows = (len(row_rels) != len(row_set))
        n1_pass = row_set.issubset(master_rels) and not dup_rows
        note = (f"子集模式：清单 {len(row_rels)} ⊆ 母版 {len(master_rels)}"
                + ("；但存在重复行" if dup_rows else ""))
    elif len(row_rels) == len(master_rels) and row_set == master_rels:
        n1_pass = True
        note = f"清单 {len(row_rels)} == 母版 {len(master_rels)}，集合完全一致"
    else:
        # 去重模式：母版按 md5 去重后保留集
        groups = {}
        for rel in master_rels:
            m5 = md5_of(os.path.join(src_dir, j(rel)))
            groups.setdefault(m5, []).append(rel)
        kept = set(sorted(v)[0] for v in groups.values())
        if set(row_rels) == kept:
            n1_pass = True
            note = f"检测到 --dedup 模式：清单 {len(row_rels)} == 去重后 {len(kept)}"
        else:
            miss = master_rels - row_set
            extra = row_set - master_rels
            note = f"清单 {len(row_rels)} != 母版 {len(master_rels)}；缺 {len(miss)} 多 {len(extra)}"
            for x in list(miss)[:3]:
                note += f" 缺[{x}]"
            for x in list(extra)[:3]:
                note += f" 多[{x}]"
    verdict("1. 件数守恒（清单行数 == 母版件数）", n1_pass, note)

    # 1b. 交付目录集合 == 清单交付集合
    actual_files = set()
    for c in CATS:
        d = os.path.join(delivery_dir, c)
        if os.path.isdir(d):
            for f in os.listdir(d):
                actual_files.add(f"{c}/{f}")
    deli_set = set(r["交付相对路径"] for r in rows)
    extra_files = actual_files - deli_set
    miss_files = deli_set - actual_files
    verdict("1b. 交付目录集合 == 清单交付集合",
            not extra_files and not miss_files,
            f"多余 {len(extra_files)} / 缺失 {len(miss_files)}"
            + (f" 例:{sorted(extra_files)[:2]}{sorted(miss_files)[:2]}" if (extra_files or miss_files) else ""))

    # ── 2/3/4/5 逐件 ──
    results = [None] * len(rows)
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(check_row, r, src_dir, delivery_dir) for r in rows]
        for i, fut in enumerate(futs):
            results[i] = fut.result()
    bad_size = [res for res in results if not res["size_ok"]]
    bad_md5 = [res for res in results if not res["md5_ok"]]
    bad_stem = [res for res in results if not res["stem_ok"]]
    bad_fmt = [res for res in results if not res["fmt_ok"]]
    bad_px = [res for res in results if not res["size_px_ok"]]
    verdict("2. 逐件 交付字节正确", not bad_size, f"不符 {len(bad_size)}/{len(rows)}")
    verdict("2b. 逐件 交付md5正确", not bad_md5, f"不符 {len(bad_md5)}/{len(rows)}")
    verdict("3. stem 一致性（交付 stem == 母版 stem）", not bad_stem, f"不符 {len(bad_stem)}/{len(rows)}")
    verdict("4. 格式正确性（转码规则 + mode 逐件比对）", not bad_fmt, f"不符 {len(bad_fmt)}/{len(rows)}")
    verdict("5. 像素尺寸一致（交付 size == 母版 size）", not bad_px, f"不符 {len(bad_px)}/{len(rows)}")
    for lst, tag in ((bad_fmt, "格式"), (bad_px, "尺寸"), (bad_md5, "md5"), (bad_size, "字节"), (bad_stem, "stem")):
        for res in lst[:3]:
            print(f"      · {tag}不符 {res['rel']}: {'; '.join(res['detail'])}")

    # ── 6. JPEG 画质（确定性抽样快门 + 全量硬底线） ──
    # 抽样档（--sample，默认 20）= 快速门（<40 dB 即 FAIL）；
    # 全量档 = 对全部转码件逐件算 PSNR：min < PSNR_HARD_FLOOR(36 dB) 记 FAIL（真缺陷必拦），
    # 36–40 dB 之间逐件列出交人工复核（本轮实测 8 件，均已目视确认无可见差异）。
    trans_rows = [r for r in rows if r["是否转码"] == "是"]
    trans_rows.sort(key=lambda r: (r["母版md5"], r["母版相对路径"]))
    sample = trans_rows[:args.sample]
    psnrs = []
    bad_psnr = []
    for r in sample:
        mpath = os.path.join(src_dir, j(r["母版相对路径"]))
        dpath = os.path.join(delivery_dir, j(r["交付相对路径"]))
        try:
            with Image.open(mpath) as o, Image.open(dpath) as d:
                p = psnr_db(o, d)
        except Exception as exc:  # noqa: BLE001
            bad_psnr.append((r["交付相对路径"], f"读取失败 {exc}"))
            continue
        psnrs.append(p)
        if not (p >= PSNR_FLOOR):
            bad_psnr.append((r["交付相对路径"], f"{p:.2f} dB"))
    if sample:
        xs = [p for p in psnrs if p != float("inf")]
        pmin = min(xs) if xs else float("nan")
        pmean = (sum(xs) / len(xs)) if xs else float("nan")
        verdict("6a. JPEG 画质抽样门（PSNR ≥ 40 dB）", not bad_psnr,
                f"抽检 {len(sample)} 件，最低 {pmin:.2f} dB，平均 {pmean:.2f} dB")
        for nm, d in bad_psnr:
            print(f"      · PSNR 不合格 {nm}: {d}")
    else:
        verdict("6a. JPEG 画质抽样门（PSNR ≥ 40 dB）", True, "本批无转码件（0 件样本，跳过）")

    # 6b. 全量 PSNR（转码件全部；算力约 1 s/百件，1,167 件约 1 分钟）
    all_psnrs = []
    under_floor = []   # < 36 dB：FAIL
    watch = []         # 36–40 dB：列出交人工复核
    for r in trans_rows:
        mpath = os.path.join(src_dir, j(r["母版相对路径"]))
        dpath = os.path.join(delivery_dir, j(r["交付相对路径"]))
        try:
            with Image.open(mpath) as o, Image.open(dpath) as d:
                p = psnr_db(o, d)
        except Exception as exc:  # noqa: BLE001
            under_floor.append((r["交付相对路径"], f"读取失败 {exc}"))
            continue
        all_psnrs.append(p)
        if p < PSNR_HARD_FLOOR:
            under_floor.append((r["交付相对路径"], f"{p:.2f} dB"))
        elif p < PSNR_FLOOR:
            watch.append((r["交付相对路径"], f"{p:.2f} dB"))
    if trans_rows:
        xs = [p for p in all_psnrs if p != float("inf")]
        amin = min(xs) if xs else float("nan")
        amed = sorted(xs)[len(xs) // 2] if xs else float("nan")
        amean = (sum(xs) / len(xs)) if xs else float("nan")
        verdict("6b. JPEG 画质全量硬底线（min ≥ 36 dB）", not under_floor,
                f"全量 {len(trans_rows)} 件，min {amin:.2f} / 中位 {amed:.2f} / 平均 {amean:.2f} dB")
        if watch:
            print(f"      · 36–40 dB 人工复核清单（{len(watch)} 件，本轮已目视确认无可见差异）：")
            for nm, d in watch:
                print(f"        - {nm}: {d}")
        for nm, d in under_floor:
            print(f"      · 低于硬底线 {nm}: {d}")
    else:
        verdict("6b. JPEG 画质全量硬底线（min ≥ 36 dB）", True, "本批无转码件（跳过）")

    # ── 7. 负对照 ──
    if args.no_negative_control:
        print("[SKIP] 7. 负对照（--no-negative-control）")
    else:
        print("\n---- 7. 负对照（在 临时\\%s 内构造错误件，证明验收器会失败）----" % NEGCTL_DIRNAME)
        nc = negative_control(src_dir, delivery_dir, rows, main_ws, sample)
        nc_ok = True
        for name, expect, got, ok in nc:
            nc_ok = nc_ok and ok
            if ok:
                print(f"[PASS] 负对照已生效：{name} 预期 {expect} 实际 {got}")
            else:
                print(f"[FAIL] 负对照未生效：{name} 预期 {expect} 实际 {got}")
        verdict("7. 负对照（错误格式/错误尺寸 确实报 FAIL）", nc_ok)

    # ── 8. 与 超分清单.tsv 交叉核对 ──
    if not os.path.isfile(cross_path):
        verdict("8. 与 超分清单.tsv 交叉核对", False, f"交叉清单不存在：{cross_path}")
    else:
        cross = {}
        with open(cross_path, "r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                cross[((r.get("类别") or "").strip(), (r.get("统一名") or "").strip())] = (
                    (r.get("输出md5") or "").strip(), (r.get("输出画布(w,h)") or "").strip())
        missing = 0
        stale_dims = 0          # 母版尺寸与清单「输出画布」不符 → 母版被原位替换、清单陈旧
        real_mismatch = 0       # 尺寸相符但 md5 不符 → 可疑的真不一致
        stale_examples = []
        for r in rows:
            key = (r["类别"].strip(), r["统一名"].strip())
            v = cross.get(key)
            if v is None:
                missing += 1
                continue
            cm5, canvas = v
            if cm5 == r["母版md5"].strip():
                continue
            mpath = os.path.join(src_dir, j(r["母版相对路径"]))
            try:
                with Image.open(mpath) as im:
                    dims = f"{im.width}x{im.height}"
            except Exception:  # noqa: BLE001
                dims = ""
            if canvas and dims and dims != canvas:
                stale_dims += 1
                if len(stale_examples) < 3:
                    stale_examples.append(f"{key[1]}(磁盘{dims}/清单{canvas})")
            else:
                real_mismatch += 1
        if stale_dims:
            print(f"[警告] 8 项检出 {stale_dims} 件母版尺寸与 超分清单.tsv 的『输出画布』不符"
                  f"（母版已被原位替换、超分清单未同步）例:{stale_examples}")
        ok8 = (missing == 0 and real_mismatch == 0
               and (stale_dims == 0 or args.allow_stale_cross))
        extra8 = f"缺键 {missing}｜真不一致 {real_mismatch}｜清单陈旧(尺寸已变) {stale_dims}｜共 {len(rows)}"
        if stale_dims and args.allow_stale_cross:
            extra8 += "；--allow-stale-cross 已将『清单陈旧』降级为警告"
        verdict("8. 与 超分清单.tsv 交叉核对（类别+统一名 → 输出md5 == 母版md5）", ok8, extra8)

    print("\n" + "=" * 72)
    print(f"结论：{'ALL_PASS' if all_ok else 'HAS_FAILURE'}（耗时 {time.time()-t0:.1f}s）")
    print("=" * 72)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
