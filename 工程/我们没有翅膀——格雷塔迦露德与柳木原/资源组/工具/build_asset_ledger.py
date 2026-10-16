#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
W5 资源总账构建器  (ISSUE-20260918-06)
================================================================
把六源素材清单（schema 不统一）归一化，汇总为 `资源总账.json`。

输入（只读）
  krkr素材库\{ot,ota,otv,otr,otp,np}\_清单.json        六源原始清单
  krkr素材库\_冲突数据.json                            W4 跨源同名 md5 全量扫描结果
  krkr素材库\_命名映射表.tsv                           W4 归一化命名表（独立交叉校验源）

输出（写）
  krkr素材库\资源总账.json
  krkr素材库\资源总账.md
  krkr素材库\资源总账.schema.md
  <out-dir>\W5自证.json                                验收自证（默认 子代理工作区\ISSUE-20260918-06\W5）

设计原则
  * 归一化层显式处理三种异构 schema（list / dict / 无 kind），不假设格式一致
  * 图像尺寸只读 PNG 头（不解码像素），音频只解析 Ogg 页头（不调外部进程）
  * 无法判定的字段一律 null / 空数组，不猜测填充
  * 可复跑、幂等；只读素材本体

用法
  python build_asset_ledger.py                 # 全量构建
  python build_asset_ledger.py --no-audio      # 跳过音频时长（快速冒烟）
  python build_asset_ledger.py --limit 200     # 每源只处理 N 条（冒烟）
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import re
import struct
import sys
import time

# ---------------------------------------------------------------- 常量

HERE = os.path.dirname(os.path.abspath(__file__))
RES_GROUP = os.path.dirname(HERE)                       # 资源组\
PROJ = os.path.dirname(RES_GROUP)
WORKSPACE = os.path.dirname(os.path.dirname(PROJ))   # <checkout> 根

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）：素材本体 / 六源 _清单.json / _冲突数据.json 等大体积
#      或 gitignore 数据仅在主工作区，故经 DATA_ROOT 读取；
# 写 = 本 checkout（LIB_OUT 的总账三件、WORKSPACE 下的验收自证）。
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
PRJ_DATA = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
LIB = os.path.join(PRJ_DATA, r"资源组\krkr素材库")        # 只读：素材本体与原始清单
LIB_OUT = os.path.join(RES_GROUP, "krkr素材库")           # 只写：总账三件（本 checkout）


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WORKSPACE)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]      # 总纲 §四 源序
# 冲突报告/W4 使用的稳定排序（用于 dup_of 的「首个」判定，确定性可复现）
SOURCE_RANK = {s: i for i, s in enumerate(SOURCES)}

DIR_KINDS = {"chr", "pic", "sys", "bgm", "se", "voice", "movie", "etc"}
CONTENT_TYPES = {"image", "audio", "video", "data"}

EXT_CONTENT = {
    ".png": "image",
    ".ogg": "audio",
    ".mpg": "video",
    ".mp4": "video",
    ".gmp": "data",
    ".lag": "data",
    ".dat": "data",
    ".txt": "data",
}

# PSV content_note -> usage 标签（W4 已人工判读，直接映射；非启发式）
OTV_NOTE_RULES = [
    ("加载提示", "loading"),
    ("EyeCatch", "eyecatch"),
    ("转场遮罩", "transition_mask"),
    ("场景选择画面", "scene_select"),
    ("配置画面", "config"),
    ("回想", "backlog"),
    ("品牌 logo", "logo"),
    ("logo", "logo"),
    ("对话窗样式", "message_window"),
]

KIND_BASE_USAGE = {
    "chr": "立绘",
    "pic": "CG/背景",
    "sys": "系统UI",
    "bgm": "BGM",
    "se": "音效",
    "voice": "语音",
    "movie": "影片",
    "etc": "其他",
}


# ---------------------------------------------------------------- 工具

def log(msg: str) -> None:
    print(msg, flush=True)


def load_manifest(src: str) -> list[dict]:
    """归一化层 · 第 1 步：把三种异构 schema 统一为 list[dict]。

    实测差异（W4 登记）：
      ot / otr / otp / np : list，6 字段，kind = 目录型
      ota                 : dict（含 entries），kind = 内容型
      otv                 : list，W3 UI 306 无 kind 字段 / W4b 美咲线 2,211 带 kind（一律忽略，
                            由 out_relpath 首段推导），out_relpath 含 'otv/' 前缀
    """
    path = os.path.join(LIB, src, "_清单.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        # ota 形态：dict 容器，条目在 entries
        entries = raw.get("entries")
        if not isinstance(entries, list):
            raise ValueError(f"{src}: dict 清单缺少 entries 列表")
        return entries
    if isinstance(raw, list):
        return raw
    raise ValueError(f"{src}: 未知清单形态 {type(raw).__name__}")


def normalize_record(src: str, rec: dict) -> dict:
    """归一化层 · 第 2 步：单条记录 -> 统一中间形态。

    产出键：source, dir_kind, orig_kind, orig_name, relpath(源内相对),
            manifest_out_bytes, src_bytes, archive, extra
    """
    out = {
        "source": src,
        "orig_kind": rec.get("kind"),          # otv 为 None
        "orig_name": rec["orig_name"],
        "archive": rec.get("archive"),
        "src_bytes": rec.get("src_bytes"),
        "manifest_out_bytes": rec.get("out_bytes"),
        "extra": {},
    }

    rel = rec["out_relpath"].replace("\\", "/").lstrip("/")

    if src == "otv":
        # otv: out_relpath 已含 'otv/' 前缀 -> 剥掉，再取首段为目录型 kind
        if rel.startswith(src + "/"):
            rel = rel[len(src) + 1:]
        parts = rel.split("/")
        if len(parts) < 2:
            raise ValueError(f"otv: out_relpath 无法解析出 kind: {rec['out_relpath']!r}")
        out["dir_kind"] = parts[0]
        out["relpath"] = rel
        # otv 清单自带尺寸/色型/内容注记，作为交叉校验与 note 来源
        if rec.get("width") is not None:
            out["extra"]["manifest_w"] = rec["width"]
            out["extra"]["manifest_h"] = rec["height"]
            out["extra"]["manifest_mode"] = rec.get("colortype")
        if rec.get("content_note"):
            out["extra"]["content_note"] = rec["content_note"]
    else:
        parts = rel.split("/")
        if len(parts) < 2:
            raise ValueError(f"{src}: out_relpath 无法解析出 kind: {rec['out_relpath']!r}")
        if src == "ota":
            # ota: kind 是内容型（image/audio/data/movie），目录型取 out_relpath 首段
            out["dir_kind"] = parts[0]
        else:
            # ot / otr / otp / np: kind 已是目录型；与 out_relpath 首段必须一致
            out["dir_kind"] = rec["kind"]
            if parts[0] != rec["kind"]:
                out["extra"]["kind_path_mismatch"] = f"{rec['kind']}!={parts[0]}"
        out["relpath"] = rel

    out["relpath"] = out["relpath"].lower()
    return out


# ---------------------------------------------------------------- 元数据读取

_PNG_MODE = {0: "L", 1: "L", 2: "RGB", 3: "P", 4: "LA", 5: "LA", 6: "RGBA"}


def read_png_head(path: str):
    """只读 PNG 头（IHDR），不解码像素。返回 (w,h,mode,bitdepth) 或 None。"""
    try:
        with open(path, "rb") as f:
            h = f.read(33)
    except OSError:
        return None
    if len(h) < 33 or h[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if h[12:16] != b"IHDR":
        return None
    w, ht = struct.unpack_from(">II", h, 16)
    bitdepth = h[24]
    ctype = h[25]
    mode = _PNG_MODE.get(ctype)
    if mode is None:
        return None
    # 低位深调色板/灰度按 PIL 口径折算（P 恒为 P；灰度 <8bpp 归 L）
    return w, ht, mode, bitdepth


def read_ogg_head(path: str):
    """轻量 Ogg Vorbis 头解析（不调外部进程）。

    返回 (sample_rate, channels, granule_total) 或 None。
    - 采样率/声道：第 1 页内 identification header packet (`\\x01vorbis`) 偏移 +11/+12
    - 总样点：最后一个自洽 Ogg 页的 granule position（Vorbis 语义 = 总样点数）
    """
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
            if head[:4] != b"OggS":
                return None
            i = head.find(b"\x01vorbis")
            if i < 0 or i + 16 > len(head):
                return None
            channels = head[i + 11]
            sample_rate = struct.unpack_from("<I", head, i + 12)[0]
            if sample_rate == 0:
                return None
            f.seek(0, os.SEEK_END)
            size = f.tell()
            tail_len = min(size, 1 << 17)          # 128 KiB > Ogg 单页上限 65307
            f.seek(size - tail_len)
            tail = f.read(tail_len)
    except OSError:
        return None

    granule = None
    pos = len(tail)
    while True:
        j = tail.rfind(b"OggS", 0, pos)
        if j < 0:
            break
        # 页头自洽性：version 字节必须为 0，且 header_type 合法
        if j + 27 <= len(tail) and tail[j + 4] == 0:
            g = struct.unpack_from("<Q", tail, j + 6)[0]
            if g != 0xFFFFFFFFFFFFFFFF:
                granule = g
                break
        pos = j
    return sample_rate, channels, granule


def sniff_content_type(path: str, ext: str):
    """扩展名 + 魔数双判据。返回 (content_type, magic_ok, mismatch_note)"""
    by_ext = EXT_CONTENT.get(ext)
    magic_ok = None
    try:
        with open(path, "rb") as f:
            head = f.read(8)
    except OSError:
        return by_ext, None, None
    if ext == ".png":
        magic_ok = head[:8] == b"\x89PNG\r\n\x1a\n"
    elif ext == ".ogg":
        magic_ok = head[:4] == b"OggS"
    elif ext in (".mpg", ".mp4"):
        magic_ok = head[:4] in (b"\x00\x00\x01\xba", b"\x00\x00\x01\xb3") or head[4:8] == b"ftyp"
    note = None
    if magic_ok is False:
        note = f"魔数与扩展名 {ext} 不符"
    return by_ext, magic_ok, note


# ---------------------------------------------------------------- usage

def usage_of(src, dir_kind, stem, filename, ext, img, extra):
    """返回 (usage:list, usage_src:str|None)。不编造：判不出即空数组 + None。"""
    if src == "otv":
        note = extra.get("content_note") or ""
        tags = []
        for kw, tag in OTV_NOTE_RULES:
            if kw in note:
                tags.append(tag)
        if tags:
            return sorted(set(tags)), "content_note"
        if note:
            # W3 有 content_note 但未命中关键词映射者：维持原口径（空数组 + None，不臆造），
            # 其原始 content_note 仍保留在 `note` 字段，信息未丢失。
            return [], None
        # W10（2026-09-19，主代理裁决）：W4b 补归集的 2,211 条美咲线素材**无 `content_note`**，
        # 原实现直接返回 []/None（未编造）。现启用**与兄弟源同口径的启发式标签**
        # （chr→立绘、pic 的 bg*/ec* 前缀→背景/事件CG、bgm/se/voice/movie→类别名），
        # `usage_src` 标 `heuristic`（**须人工复核**，不得当作确定结论）。
        # 不在此 return，落下方通用启发式分支。

    base = KIND_BASE_USAGE.get(dir_kind)
    if base is None:
        return [], None

    if dir_kind in ("chr", "sys", "bgm", "se", "voice", "movie", "etc"):
        return [base], "heuristic"

    if dir_kind == "pic":
        tags = []
        if stem.startswith("bg"):
            tags.append("背景")
        elif stem.startswith("ec"):
            tags.append("事件CG")
        elif stem.startswith("ef"):
            tags.append("特效")
        elif stem.startswith("th_"):
            tags.append("缩略图")
        # 尺寸启发式：宽幅/竖幅 = 演出用拼接 CG
        if img and img.get("width") and img.get("height"):
            w, h = img["width"], img["height"]
            if w / h >= 1.8 or h / w >= 1.8:
                tags.append("演出CG（宽幅/竖幅）")
        tags.append(base)
        return sorted(set(tags)), "heuristic"

    return [], None


# ---------------------------------------------------------------- 主流程

def build(limit: int | None, do_audio: bool, out_dir: str):
    t0 = time.time()

    # --- 载入 W4 跨源同名全量扫描结果（复用其 md5，不重算） ---
    with open(os.path.join(LIB, "_冲突数据.json"), encoding="utf-8") as f:
        conflict = json.load(f)
    detail = conflict["detail"]                    # stem -> {entries:[{src,kind,rel,bytes,md5}], same, n_md5}
    log(f"[1] 载入 _冲突数据.json: detail={len(detail)} 组, "
        f"cross_source_stems={conflict['cross_source_stems']}, "
        f"diff={conflict['diff_groups']}, same={conflict['same_groups']}")

    # --- 载入 W4 命名映射表（独立交叉校验源） ---
    tsv = {}
    with open(os.path.join(LIB, "_命名映射表.tsv"), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            tsv[(r["来源代号"], r["新相对路径"].replace("\\", "/").lower())] = r
    log(f"[2] 载入 _命名映射表.tsv: {len(tsv)} 行")

    records = []
    stats = {
        "schema": {},
        "magic_mismatch": [],
        "tsv_missing": [],
        "tsv_kind_mismatch": [],
        "tsv_bytes_mismatch": [],
        "missing_files": [],
        "ogg_no_granule": 0,
        "ogg_fail": 0,
        "png_fail": 0,
        "otv_dim_mismatch": [],
    }

    for src in SOURCES:
        entries = load_manifest(src)
        stats["schema"][src] = {
            "manifest_shape": "dict" if src == "ota" else "list",
            "manifest_kind_semantics": (
                "content-type" if src == "ota"
                else ("mixed(W3 absent / W4b dir)" if src == "otv" else "dir")
            ),
            "entries": len(entries),
            "fields": sorted({k for e in entries[:50] for k in e}),
        }
        if limit:
            entries = entries[:limit]
        for rec in entries:
            n = normalize_record(src, rec)
            rel = n["relpath"]
            disk = os.path.join(LIB, src, rel.replace("/", os.sep))
            if not os.path.exists(disk):
                stats["missing_files"].append(f"{src}/{rel}")
                continue
            size = os.path.getsize(disk)
            ext = os.path.splitext(rel)[1].lower()
            stem = os.path.basename(rel)
            stem = stem[len(src) + 1:] if stem.startswith(src + "_") else stem
            stem = os.path.splitext(stem)[0].lower()

            ctype, magic_ok, magic_note = sniff_content_type(disk, ext)
            if magic_ok is False:
                stats["magic_mismatch"].append({"path": f"{src}/{rel}", "note": magic_note})
            if n["extra"].get("kind_path_mismatch"):
                stats["magic_mismatch"].append(
                    {"path": f"{src}/{rel}", "note": n["extra"]["kind_path_mismatch"]})

            img = None
            audio = None
            if ctype == "image" and ext == ".png":
                ph = read_png_head(disk)
                if ph is None:
                    stats["png_fail"] += 1
                else:
                    img = {"width": ph[0], "height": ph[1], "mode": ph[2]}
                    if n["extra"].get("manifest_w") is not None:
                        if (n["extra"]["manifest_w"] != ph[0]
                                or n["extra"]["manifest_h"] != ph[1]
                                or n["extra"].get("manifest_mode") != ph[2]):
                            stats["otv_dim_mismatch"].append(
                                {"path": f"{src}/{rel}",
                                 "manifest": [n["extra"]["manifest_w"],
                                              n["extra"]["manifest_h"],
                                              n["extra"].get("manifest_mode")],
                                 "disk": [ph[0], ph[1], ph[2]]})
            note_extra = []
            if ctype == "audio" and ext == ".ogg" and do_audio:
                oh = read_ogg_head(disk)
                if oh is None:
                    # 头部损坏：不猜测采样率/声道/时长，字段全 null 并在 note 说明（W5 发现 F2）
                    stats["ogg_fail"] += 1
                    audio = {"duration_sec": None, "sample_rate": None, "channels": None}
                    note_extra.append(
                        "Ogg 首页头损坏（无 Vorbis identification header），采样率/声道/时长无法解析")
                else:
                    sr, ch, gran = oh
                    if gran is None:
                        stats["ogg_no_granule"] += 1
                    audio = {
                        "duration_sec": (round(gran / sr, 3) if gran is not None else None),
                        "sample_rate": sr,
                        "channels": ch,
                    }

            note_parts = []
            if n["extra"].get("content_note"):
                note_parts.append(n["extra"]["content_note"])
            if magic_note:
                note_parts.append(magic_note)
            note_parts.extend(note_extra)

            rec_out = {
                "source": src,
                "kind": n["dir_kind"],
                "content_type": ctype,
                "orig_name": n["orig_name"],
                "out_relpath": f"{src}/{rel}",
                "filename": os.path.basename(rel),
                "bytes": size,
                "ext": ext.lstrip("."),
                "image": img,
                "audio": audio,
                "dup_group": None,
                "dup_of": None,
                "usage": [],
                "note": "；".join(note_parts),
            }
            if n["src_bytes"] is not None:
                rec_out["src_bytes"] = n["src_bytes"]
            if n["archive"]:
                rec_out["archive"] = n["archive"]

            u, us = usage_of(src, n["dir_kind"], stem, rec_out["filename"], ext, img, n["extra"])
            rec_out["usage"] = u
            rec_out["usage_src"] = us

            records.append((stem, rec_out))

            # 交叉校验 W4 命名映射表
            key = (src, rec_out["out_relpath"].lower())
            trow = tsv.get(key)
            if trow is None:
                stats["tsv_missing"].append(rec_out["out_relpath"])
            else:
                if trow["类型"] != n["dir_kind"]:
                    stats["tsv_kind_mismatch"].append(
                        {"path": rec_out["out_relpath"], "tsv": trow["类型"], "mine": n["dir_kind"]})
                try:
                    if int(trow["字节"]) != size:
                        stats["tsv_bytes_mismatch"].append(
                            {"path": rec_out["out_relpath"], "tsv": int(trow["字节"]), "disk": size})
                except ValueError:
                    pass

        log(f"    {src}: {len(entries)} 条处理完成 (累计 {len(records)})")

    log(f"[3] 归一化完成：{len(records)} 条，用时 {time.time()-t0:.1f}s")

    # --- 挂 dup_group / dup_of ---
    by_rel = {r["out_relpath"]: r for _, r in records}
    n_group = n_dup = 0
    for stem, group in detail.items():
        members = [e["rel"] for e in group["entries"]]
        same = bool(group.get("same"))
        canon = None
        if same:
            canon = sorted(members, key=lambda p: (SOURCE_RANK.get(p.split("/")[0], 99), p))[0]
        for rel in members:
            r = by_rel.get(rel)
            if r is None:
                continue
            r["dup_group"] = stem
            n_group += 1
            if same:
                if rel != canon:
                    r["dup_of"] = canon
                    n_dup += 1
    log(f"[4] 挂接同名关系：dup_group 命中 {n_group} 条，dup_of 指向 {n_dup} 条")

    # --- 同名组差异性质有界探针（只读 首 512B + 尾 64B，见 W5 发现 F1/F3） ---
    artifact = analyze_near_dup(detail, LIB)
    log(f"[4b] 同名差异性质探针：抽样 {artifact['sampled_groups']} 组 / 差异组池 "
        f"{artifact['diff_groups_total']} 组（跳过 {artifact['skipped_groups']}）；"
        f"素材对 {artifact['sampled_pairs']} 对 -> {artifact['counts']}")

    # --- 写 资源总账.json ---
    entries_out = [r for _, r in records]
    kind_ct = collections.Counter((r["source"], r["kind"]) for r in entries_out)
    payload = {
        "meta": {
            "module": "W5 资源总账",
            "issue": "ISSUE-20260918-06",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "builder": os.path.relpath(os.path.abspath(__file__), WORKSPACE).replace("\\", "/"),
            "source_order": SOURCES,
            "source_rank_note": "dup_of 的「首个」按 source_order 顺序 + out_relpath 字典序确定",
            "count": len(entries_out),
            "audio_metadata": "ok" if do_audio else "skipped",
            "dup_groups_total": len(detail),
            "dup_groups_same": conflict["same_groups"],
            "dup_groups_diff": conflict["diff_groups"],
            "per_source": {s: sum(1 for r in entries_out if r["source"] == s) for s in SOURCES},
            "per_source_kind": {f"{s}|{k}": v for (s, k), v in sorted(kind_ct.items())},
            "known_artifacts": {
                "F1_trailing_bytes": (
                    "跨源同名 Ogg 常仅『文件末尾约 12–16 字节』不同（同一录音、同一编码），"
                    "逐字节 md5 会因此判为『同名不同内容』。dup_of 仍按字节相同口径置 null。"),
                "F2_ot_se_header_corruption": (
                    "【W5b 已定位并修复】原 ot/se 全部 582 个 .ogg 首页头损坏（无 Vorbis "
                    "identification header，ffmpeg 报 CRC mismatch，不可播放）。根因＝社区 "
                    "LPK-Keys.json 中 SE.LPK 的 Key1 写错 1 字节（0x9A5AF6DE→0x935AF6DE，"
                    "仅影响 decrypt_content_1_first_256 的前 256 字节）。已由 "
                    "lpk_media.KEY_OVERRIDES 覆盖（值取自 gameinit.sob 游戏自述）并重提；"
                    "现 582/582 可解析，三字段不再为 null。其他源同 stem 文件正常。"),
                "F3_probe": artifact,
            },
        },
        "entries": entries_out,
    }
    out_json = os.path.join(LIB_OUT, "资源总账.json")
    _assert_in_checkout(out_json, "资源总账.json")
    os.makedirs(LIB_OUT, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    log(f"[5] 写出 {out_json}  ({os.path.getsize(out_json):,} B)")

    # --- 统计 ---
    agg = aggregate(entries_out, conflict)
    agg["stats"] = stats
    agg["near_dup_probe"] = artifact
    agg["elapsed_sec"] = round(time.time() - t0, 1)
    with open(os.path.join(out_dir, "W5自证.json"), "w", encoding="utf-8") as f:
        json.dump(agg, f, ensure_ascii=False, indent=1)
    log(f"[6] 写出 {os.path.join(out_dir, 'W5自证.json')}")
    return payload, agg


def analyze_near_dup(detail: dict, lib: str, per_kind: int = 100,
                     max_bytes: int = 32 * 1024 * 1024) -> dict:
    """同名组差异性质 —— **分层抽样 + 全文件逐字节比对**。

    对 `_冲突数据.json` 中 `same == false` 的 11,082 组，按 kind 分层、按 stem 排序后
    等距抽取至多 `per_kind` 组，对每组**完整读取所有成员并逐字节比对**（跳过单文件
    > max_bytes 者，避免读大影片）。

    **口径说明**：这是**抽样**结论（样本量见 `sampled_groups`），不是全量证明；
    `dup_of` 仍严格按 W4 的全量 md5 口径（逐字节相同才置值）。

    每组的分类：
      tail_only   所有差异都落在文件末尾 16 字节内（同一录音、同一编码）
      head_tail   差异落在「首 300B 内」+「末尾 16B 内」两处
      low_ratio   差异字节占比 ≤ 1%（但分布不在上述两处）
      high_ratio  差异字节占比 > 1%（疑为真正不同的素材）
    """
    # 分层抽样
    by_kind = collections.defaultdict(list)
    for stem, group in detail.items():
        if group.get("same"):
            continue
        by_kind[group["entries"][0]["kind"]].append(stem)

    sample_stems = []
    for kind, stems in sorted(by_kind.items()):
        stems.sort()
        k = min(per_kind, len(stems))
        step = max(1, len(stems) // k)
        sample_stems.extend(stems[::step][:k])

    cnt = collections.Counter()
    by_kind_cnt = collections.defaultdict(collections.Counter)
    pair_by_kind = collections.defaultdict(collections.Counter)
    samples = collections.defaultdict(list)
    ratios = []
    skipped = 0
    n_pairs = 0

    for stem in sample_stems:
        group = detail[stem]
        kind = group["entries"][0]["kind"]
        blobs = []
        for e in group["entries"]:
            p = os.path.join(lib, e["rel"].replace("/", os.sep))
            try:
                if os.path.getsize(p) > max_bytes:
                    blobs = []
                    break
                with open(p, "rb") as f:
                    blobs.append((e["rel"], f.read()))
            except OSError:
                blobs = []
                break
        if len(blobs) < 2:
            skipped += 1
            continue
        # 逐「对」比对：把多成员组拆成所有两两组合，避免与不同长度成员混淆
        for i in range(len(blobs)):
            for j in range(i + 1, len(blobs)):
                ra, a = blobs[i]
                rb, b = blobs[j]
                n = min(len(a), len(b))
                tail_zone = min(16, n)
                head_len = n - tail_zone
                diffs_head = [k for k in range(head_len) if a[k] != b[k]]
                size_gap = abs(len(a) - len(b))
                if not diffs_head:
                    if size_gap == 0:
                        cls = "tail_only"          # 前缀全同、长度相同 → 同一文件仅尾 16B 不同
                    elif size_gap <= 16:
                        cls = "tail_truncated"     # 前缀全同、尾部截断 → 同一录音
                    else:
                        cls = "prefix_only"        # 前缀全同但长度差大 → 罕见
                elif max(diffs_head) < 300:
                    cls = "head_zone"              # 差异仅在文件头 300B 内（头部元数据/损坏）
                elif len(diffs_head) / head_len <= 0.01:
                    cls = "low_ratio"              # 差异 ≤1%
                else:
                    cls = "content_differs"        # 疑为真正不同的素材
                n_pairs += 1
                cnt[cls] += 1
                by_kind_cnt[kind][cls] += 1
                pair_by_kind[f"{ra.split('/')[0]}|{rb.split('/')[0]}"][cls] += 1
                ratios.append(len(diffs_head) / head_len)
                if len(samples[cls]) < 6:
                    samples[cls].append({
                        "stem": stem, "kind": kind, "pair": [ra, rb],
                        "sizes": [len(a), len(b)],
                        "ndiff_head": len(diffs_head),
                        "max_diff_offset": (max(diffs_head) if diffs_head else None),
                    })

    ratios.sort()
    med = ratios[len(ratios) // 2] if ratios else None
    return {
        "probe_note": ("分层抽样 + 全文件逐字节比对，以**素材对（pair）**为单位分类；"
                       "样本为筛查性结论，非全量证明。dup_of 仍按 W4 全量 md5 口径（逐字节相同才置值）"),
        "class_definitions": {
            "tail_only": "前缀逐字节全同、长度相同 → 同一文件，仅末尾 ≤16B 不同",
            "tail_truncated": "前缀逐字节全同、长度差 ≤16B → 同一录音，一方尾部截断",
            "head_zone": "差异全部落在文件头 300B 内 → 头部元数据/头部损坏",
            "low_ratio": "头部差异 ≤1%（但超出首 300B）",
            "content_differs": "头部差异 >1% → 疑为真正不同的素材",
            "prefix_only": "前缀全同但长度差 >16B（罕见）",
        },
        "diff_groups_total": sum(len(v) for v in by_kind.values()),
        "sampled_groups": len(sample_stems) - skipped,
        "sampled_pairs": n_pairs,
        "skipped_groups": skipped,
        "per_kind_pool": {k: len(v) for k, v in sorted(by_kind.items())},
        "counts": dict(cnt.most_common()),
        "by_kind": {k: dict(v) for k, v in sorted(by_kind_cnt.items())},
        "by_source_pair": {k: dict(v) for k, v in sorted(pair_by_kind.items())},
        "median_head_diff_ratio": (round(med, 6) if med is not None else None),
        "samples": dict(samples),
    }


def aggregate(entries, conflict):
    """产出供 md/自证使用的一切统计（全部来自总账本身，可复算）。"""
    by_src_kind = collections.Counter()
    bytes_src_kind = collections.Counter()
    for r in entries:
        by_src_kind[(r["source"], r["kind"])] += 1
        bytes_src_kind[(r["source"], r["kind"])] += r["bytes"]

    size_dist = collections.defaultdict(collections.Counter)
    for r in entries:
        if r["image"]:
            size_dist[r["source"]][f'{r["image"]["width"]}x{r["image"]["height"]}'] += 1
    mode_dist = collections.defaultdict(collections.Counter)
    for r in entries:
        if r["image"]:
            mode_dist[r["source"]][r["image"]["mode"]] += 1

    audio_dist = collections.defaultdict(collections.Counter)
    for r in entries:
        if r["audio"]:
            sr = r["audio"]["sample_rate"]
            if sr is None:
                audio_dist[r["source"]]["无法解析（Ogg 首页头损坏，见 F2）"] += 1
            else:
                audio_dist[r["source"]][f'{sr}Hz/{r["audio"]["channels"]}ch'] += 1

    dur = [r["audio"]["duration_sec"] for r in entries
           if r["audio"] and r["audio"]["duration_sec"] is not None]

    return {
        "count": len(entries),
        "by_source": dict(collections.Counter(r["source"] for r in entries)),
        "by_kind": dict(collections.Counter(r["kind"] for r in entries)),
        "by_content_type": dict(collections.Counter(r["content_type"] for r in entries)),
        "by_source_kind": {f"{s}|{k}": v for (s, k), v in sorted(by_src_kind.items())},
        "bytes_by_source_kind": {f"{s}|{k}": v for (s, k), v in sorted(bytes_src_kind.items())},
        "bytes_by_source": {
            s: sum(r["bytes"] for r in entries if r["source"] == s) for s in SOURCES},
        "total_bytes": sum(r["bytes"] for r in entries),
        "image_size_dist": {s: dict(c.most_common(20)) for s, c in size_dist.items()},
        "image_mode_dist": {s: dict(c) for s, c in mode_dist.items()},
        "audio_spec_dist": {s: dict(c) for s, c in audio_dist.items()},
        "audio_count": sum(1 for r in entries if r["audio"]),
        "audio_duration_total_sec": round(sum(dur), 1) if dur else 0,
        "audio_duration_missing": sum(
            1 for r in entries if r["audio"] and r["audio"]["duration_sec"] is None),
        "usage_tagged": sum(1 for r in entries if r["usage"]),
        "usage_untagged": sum(1 for r in entries if not r["usage"]),
        "dup_members": sum(1 for r in entries if r["dup_group"]),
        "dup_of_set": sum(1 for r in entries if r["dup_of"]),
        "dup_diff_members_with_dupof": sum(
            1 for r in entries
            if r["dup_of"] and conflict["detail"].get(r["dup_group"], {}).get("same") is False),
        "relpath_unique": len({r["out_relpath"] for r in entries}),
        "conflict_counts": conflict["counts"],
        "pair_matrix": conflict["pair_matrix"],
        "per_source_kind_all": {f"{s}|{k}": v for (s, k), v in sorted(by_src_kind.items())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--out-dir", default=os.path.join(
        WORKSPACE, "子代理工作区", "ISSUE-20260918-06", "W5"))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    build(a.limit, not a.no_audio, a.out_dir)


if __name__ == "__main__":
    main()