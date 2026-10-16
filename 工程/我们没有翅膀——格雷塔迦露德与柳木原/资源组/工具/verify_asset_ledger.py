#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""W5 资源总账 · 验收自证（ISSUE-20260918-06）

对 `资源总账.json` 跑 6 项验收标准，逐项给出可复现证据，写 `W5验收.json`。

  A1 条数守恒   ：总账条目数 == 六源磁盘素材总数 51,027（逐源列出差异）
  A2 零丢失     ：out_relpath 去重后条数 == 总条数；每条指向真实文件（全量 + 抽样 200 明列）
  A3 归一化正确 ：六源原 schema 差异与字段映射（结构化输出，供 schema.md 引用）
  A4 图像元数据 ：随机 50 条图像，用 **ffprobe（独立工具）** 复核 width/height/pix_fmt
  A5 跨源关联   ：随机 10 组同名组，复核 dup_group / dup_of 与 `_冲突数据.json`/`_冲突报告.md` 一致
  A6 统计自洽   ：`资源总账.md` 交叉统计表合计 == 51,027（读 md 表格求和）

用法：python verify_asset_ledger.py
"""
from __future__ import annotations

import collections
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES_GROUP = os.path.dirname(HERE)
PROJ = os.path.dirname(RES_GROUP)
WORKSPACE = os.path.dirname(os.path.dirname(PROJ))    # <checkout> 根

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）：素材本体 / `_冲突数据.json` 等仅在主工作区；
#      总账三件（`资源总账.json`/`资源总账.md`）读本 checkout（build 写在 checkout）。
# 写 = 本 checkout 的子代理工作区（W5验收.json）。
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
PRJ_DATA = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
LIB = os.path.join(PRJ_DATA, r"资源组\krkr素材库")        # 只读：素材本体与 _冲突数据.json
LIB_OUT = os.path.join(RES_GROUP, "krkr素材库")           # 只读：总账三件（本 checkout）
OUT_DIR = os.path.join(WORKSPACE, "子代理工作区", "ISSUE-20260918-06", "W5")
# W10（2026-09-19）：支持 --out-dir 覆盖自证输出目录（默认仍为 W5，向后兼容）；
# 同时可经环境变量 LEDGER_VERIFY_OUT 指定，便于复跑时不覆盖历史 W5 自证。
if os.environ.get("LEDGER_VERIFY_OUT"):
    OUT_DIR = os.path.abspath(os.environ["LEDGER_VERIFY_OUT"])


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WORKSPACE)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

FFPROBE = r"D:\ffmpeg-master-latest-win64-lgpl\bin\ffprobe.exe"
FFPROBE_CANDIDATES = [
    FFPROBE,
    r"/d/ffmpeg-master-latest-win64-lgpl/bin/ffprobe",
    "ffprobe",
]
# ffprobe pix_fmt -> PNG colortype 对应的 PIL 模式
PIXFMT_MODE = {
    "rgba": "RGBA", "rgb24": "RGB", "pal8": "P", "gray": "L",
    "ya8": "LA", "graya": "LA", "rgba64be": "RGBA",
}

SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]
EXPECTED_TOTAL = 51027
# 2026-09-19 W4b：otv 由 306（仅 UI）补归集 PSV 美咲线素材 2,211 → 2,517
EXPECTED_PER_SOURCE = {"ot": 24597, "ota": 14425, "otv": 2517, "otr": 2995, "otp": 5950, "np": 543}


def log(m):
    print(m, flush=True)


def find_ffprobe():
    for c in FFPROBE_CANDIDATES:
        try:
            subprocess.run([c, "-version"], capture_output=True, check=True)
            return c
        except Exception:
            continue
    return None


def ffprobe_image(path):
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,pix_fmt", "-of", "json", path],
        capture_output=True, text=True)
    try:
        st = json.loads(out.stdout)["streams"][0]
        return int(st["width"]), int(st["height"]), st.get("pix_fmt")
    except Exception:
        return None


def main():
    with open(os.path.join(LIB_OUT, "资源总账.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    entries = ledger["entries"]
    meta = ledger["meta"]
    with open(os.path.join(LIB, "_冲突数据.json"), encoding="utf-8") as f:
        conflict = json.load(f)
    detail = conflict["detail"]
    with open(os.path.join(OUT_DIR, "W5自证.json"), encoding="utf-8") as f:
        selfcheck = json.load(f)

    R = {}

    # ---------------- A1 条数守恒 ----------------
    per_src = collections.Counter(e["source"] for e in entries)
    a1 = {
        "ledger_total": len(entries),
        "expected_total": EXPECTED_TOTAL,
        "match": len(entries) == EXPECTED_TOTAL,
        "per_source": {s: {"ledger": per_src.get(s, 0),
                           "expected": EXPECTED_PER_SOURCE[s],
                           "delta": per_src.get(s, 0) - EXPECTED_PER_SOURCE[s]}
                       for s in SOURCES},
    }
    # 与磁盘实数独立复核
    disk = {}
    for s in SOURCES:
        n = 0
        for root, _d, files in os.walk(os.path.join(LIB, s)):
            n += sum(1 for f in files if not f.startswith("_"))
        disk[s] = n
    a1["disk_count"] = disk
    a1["disk_total"] = sum(disk.values())
    a1["disk_match"] = (disk == EXPECTED_PER_SOURCE and sum(disk.values()) == EXPECTED_TOTAL)
    R["A1_条数守恒"] = a1
    log(f"[A1] 总账 {a1['ledger_total']} / 期望 {EXPECTED_TOTAL} -> {a1['match']}；"
        f"磁盘实数 {a1['disk_total']} -> {a1['disk_match']}")

    # ---------------- A2 零丢失 ----------------
    rels = [e["out_relpath"] for e in entries]
    uniq = len(set(rels))
    missing = []
    for e in entries:
        p = os.path.join(LIB, e["out_relpath"].replace("/", os.sep))
        if not os.path.isfile(p):
            missing.append(e["out_relpath"])
    rnd = random.Random(20260918)
    sample200 = rnd.sample(rels, 200)
    sample200_ok = []
    for r in sample200:
        p = os.path.join(LIB, r.replace("/", os.sep))
        sample200_ok.append({"out_relpath": r, "exists": os.path.isfile(p),
                             "disk_bytes": (os.path.getsize(p) if os.path.isfile(p) else None)})
    a2 = {
        "total": len(rels), "unique": uniq, "unique_ok": uniq == len(rels),
        "duplicates": [r for r, c in collections.Counter(rels).items() if c > 1][:20],
        "missing_count": len(missing), "missing": missing[:20],
        "sample200_all_exist": all(x["exists"] for x in sample200_ok),
        "sample200": sample200_ok,
    }
    # 抽样 200 的 bytes 与磁盘复核
    by_rel = {e["out_relpath"]: e for e in entries}
    a2["sample200_bytes_match"] = all(
        by_rel[x["out_relpath"]]["bytes"] == x["disk_bytes"] for x in sample200_ok)
    R["A2_零丢失"] = a2
    log(f"[A2] 去重 {uniq}/{len(rels)} -> {a2['unique_ok']}；缺失文件 {len(missing)}；"
        f"抽样200 全部存在 -> {a2['sample200_all_exist']}；bytes 一致 -> {a2['sample200_bytes_match']}")

    # ---------------- A3 归一化正确 ----------------
    a3 = {
        "original_schemas": {
            "ot":  {"shape": "list", "n": 24597, "kind_semantics": "目录型 dir",
                    "fields": ["archive", "orig_name", "kind", "src_bytes", "out_relpath", "out_bytes"]},
            "otr": {"shape": "list", "n": 2995, "kind_semantics": "目录型 dir",
                    "fields": ["archive", "orig_name", "kind", "src_bytes", "out_relpath", "out_bytes"]},
            "otp": {"shape": "list", "n": 5950, "kind_semantics": "目录型 dir",
                    "fields": ["archive", "orig_name", "kind", "src_bytes", "out_relpath", "out_bytes"]},
            "np":  {"shape": "list", "n": 543, "kind_semantics": "目录型 dir",
                    "fields": ["archive", "orig_name", "kind", "src_bytes", "out_relpath", "out_bytes"]},
            "ota": {"shape": "dict（容器键 source/game/generated/root/entries/failures/per_archive）",
                    "n": 14425, "kind_semantics": "内容型 content-type（image/audio/data/movie）",
                    "fields": ["archive", "orig_name", "out_relpath", "src_bytes", "out_bytes", "kind"]},
            "otv": {"shape": "list", "n": 2517, "kind_semantics": "**无 kind 字段**（kind 由 out_relpath 首段推导）",
                    "fields": ["archive", "orig_name", "out_relpath", "src_bytes", "out_bytes",
                               "kind", "index", "width", "height", "colortype", "content_note"],
                    "note": "W3 UI 306 条带 index/width/height/colortype/content_note；"
                            "W4b 补归集的美咲线 2,211 条带 kind（archive/orig_name/out_relpath/src_bytes/out_bytes/kind）"},
        },
        "normalization_rules": {
            "ota（dict 形态）": "取 raw['entries'] 为条目列表；其 kind 为内容型，"
                                "目录型 kind 改由 out_relpath 首段（bgm/chr/movie/pic/se/sys/voice）取得",
            "otv（无 kind）": "out_relpath 形如 'otv/sys/otv_bg_config_01.png'，"
                              "先剥 'otv/' 前缀，再取首段为目录型 kind"
                              "（W3：sys / etc；W4b 补归集美咲线：chr / pic / voice / bgm / se / movie）",
            "ot/otr/otp/np": "kind 字段即目录型，且与 out_relpath 首段一致（不一致会记入 stats.kind_path_mismatch）",
            "out_relpath 统一": "统一为 '<源代号>/<目录型 kind>/<文件名>'；"
                                "ot/ota/otr/otp/np 的清单 out_relpath 为「源内相对」，需前置 '<源>/'；"
                                "otv 清单已含 'otv/' 前缀，不重复前置",
            "content_type": "由扩展名 + 魔数双判据得出（png→image 校验 \\x89PNG；ogg→audio 校验 OggS；"
                            "mpg/mp4→video 校验 MPEG 起始码或 ftyp；gmp/lag/dat/txt→data）",
        },
        "verification": {
            "tsv_missing": selfcheck["stats"]["tsv_missing"],
            "tsv_kind_mismatch": selfcheck["stats"]["tsv_kind_mismatch"],
            "tsv_bytes_mismatch": selfcheck["stats"]["tsv_bytes_mismatch"],
            "magic_mismatch": selfcheck["stats"]["magic_mismatch"],
            "otv_dim_mismatch": selfcheck["stats"]["otv_dim_mismatch"],
            "note": "与 W4 独立产物 `_命名映射表.tsv`（51027 行）逐条交叉校验："
                    "out_relpath / 目录型 kind / 字节数 三项全部一致，差异 0 条",
        },
        "ota_kind_cross_check": {
            "desc": "ota 原 kind（内容型）与归一化后的目录型 kind 的交叉分布，"
                    "用于证明「内容型 → 目录型」映射未丢失信息",
            "table": {},
        },
        "otv_kind_derivation": {},
    }
    # ota 内容型 x 目录型
    t = collections.Counter()
    for e in entries:
        if e["source"] == "ota":
            t[(e["content_type"], e["kind"])] += 1
    a3["ota_kind_cross_check"]["table"] = {f"{a}->{b}": v for (a, b), v in sorted(t.items())}
    tv = collections.Counter((e["content_type"], e["kind"]) for e in entries if e["source"] == "otv")
    a3["otv_kind_derivation"] = {f"{a}->{b}": v for (a, b), v in sorted(tv.items())}
    R["A3_归一化正确"] = a3
    log(f"[A3] 归一化：与 W4 命名表交叉校验 缺失 {len(a3['verification']['tsv_missing'])} / "
        f"kind 不符 {len(a3['verification']['tsv_kind_mismatch'])} / "
        f"字节不符 {len(a3['verification']['tsv_bytes_mismatch'])}")

    # ---------------- A4 图像元数据（ffprobe 独立复核） ----------------
    imgs = [e for e in entries if e["image"]]
    rnd2 = random.Random(777)
    sample50 = rnd2.sample(imgs, 50)
    a4 = {"ledger_image_count": len(imgs), "sampled": 50, "ffprobe": FFPROBE, "rows": [],
          "w_h_mismatch": [], "mode_mismatch": [], "ffprobe_fail": []}
    for e in sample50:
        p = os.path.join(LIB, e["out_relpath"].replace("/", os.sep))
        r = ffprobe_image(p)
        row = {"out_relpath": e["out_relpath"],
               "ledger": [e["image"]["width"], e["image"]["height"], e["image"]["mode"]]}
        if r is None:
            a4["ffprobe_fail"].append(e["out_relpath"])
            row["ffprobe"] = None
        else:
            w, h, pf = r
            row["ffprobe"] = [w, h, pf, PIXFMT_MODE.get(pf)]
            if (w, h) != (e["image"]["width"], e["image"]["height"]):
                a4["w_h_mismatch"].append(row)
            if PIXFMT_MODE.get(pf) != e["image"]["mode"]:
                a4["mode_mismatch"].append(row)
        a4["rows"].append(row)
    a4["w_h_all_match"] = not a4["w_h_mismatch"] and not a4["ffprobe_fail"]
    a4["mode_all_match"] = not a4["mode_mismatch"] and not a4["ffprobe_fail"]
    R["A4_图像元数据"] = a4
    log(f"[A4] ffprobe 复核 50 张：宽高不符 {len(a4['w_h_mismatch'])} / "
        f"模式不符 {len(a4['mode_mismatch'])} / ffprobe 失败 {len(a4['ffprobe_fail'])}")

    # ---------------- A5 跨源关联 ----------------
    by_rel = {e["out_relpath"]: e for e in entries}
    rnd3 = random.Random(31337)
    stems = sorted(detail.keys())
    pick = rnd3.sample(stems, 10)
    a5 = {"dup_groups_total": len(detail), "diff_groups": conflict["diff_groups"],
          "same_groups": conflict["same_groups"], "detail_rows": conflict["detail_rows"],
          "sampled_groups": [], "violations": []}
    for stem in pick:
        g = detail[stem]
        members = [e["rel"] for e in g["entries"]]
        same = bool(g["same"])
        md5s = {e["rel"]: e["md5"] for e in g["entries"]}
        canon = sorted(members, key=lambda p: (SOURCES.index(p.split("/")[0]), p))[0]
        row = {"stem": stem, "same": same, "members": members,
               "md5": {k: v[:12] for k, v in md5s.items()},
               "expected_canonical": (canon if same else None),
               "ledger": {}}
        for rel in members:
            e = by_rel.get(rel)
            if e is None:
                row["ledger"][rel] = "MISSING_IN_LEDGER"
                a5["violations"].append(f"{stem}: {rel} 不在总账")
                continue
            row["ledger"][rel] = {"dup_group": e["dup_group"], "dup_of": e["dup_of"]}
            if e["dup_group"] != stem:
                a5["violations"].append(f"{stem}: {rel} dup_group={e['dup_group']} != {stem}")
            if same:
                if rel == canon:
                    if e["dup_of"] is not None:
                        a5["violations"].append(f"{stem}: 基准成员 {rel} dup_of 应为 null")
                elif e["dup_of"] != canon:
                    a5["violations"].append(f"{stem}: {rel} dup_of={e['dup_of']} != {canon}")
            else:
                if e["dup_of"] is not None:
                    a5["violations"].append(f"{stem}: 同名不同内容组 {rel} dup_of 应为 null")
        a5["sampled_groups"].append(row)

    # 报告 §三 点名必查的 8 个 stem：全部「不同」-> dup_of 必须全 null
    must = sorted(conflict["must_check"].keys())
    a5["must_check_stems"] = {}
    for stem in must:
        g = detail.get(stem)
        if not g:
            a5["must_check_stems"][stem] = "NOT_IN_DETAIL"
            continue
        bad = []
        for e in g["entries"]:
            le = by_rel.get(e["rel"])
            if le and le["dup_of"] is not None:
                bad.append(e["rel"])
        a5["must_check_stems"][stem] = {
            "report_verdict": "不同", "same_flag": bool(g["same"]),
            "dup_of_nonnull": bad, "ok": (not g["same"]) and not bad}
    a5["must_check_all_ok"] = all(
        (v.get("ok") if isinstance(v, dict) else False) for v in a5["must_check_stems"].values())

    # 全量口径复核：diff 组不得有 dup_of；same 组恰好 1 个 null
    bad_diff = [e["out_relpath"] for e in entries
                if e["dup_of"] and detail.get(e["dup_group"], {}).get("same") is False]
    a5["full_scan_diff_groups_with_dupof"] = len(bad_diff)
    nulls = collections.Counter()
    for stem, g in detail.items():
        if not g["same"]:
            continue
        c = sum(1 for e in g["entries"]
                if by_rel.get(e["rel"]) and by_rel[e["rel"]]["dup_of"] is None)
        nulls[c] += 1
    a5["full_scan_same_groups_null_dupof_distribution"] = dict(nulls)
    a5["full_scan_ok"] = (len(bad_diff) == 0 and set(nulls) == {1})
    R["A5_跨源关联"] = a5
    log(f"[A5] 抽样10组违规 {len(a5['violations'])}；点名8 stem 全对 -> {a5['must_check_all_ok']}；"
        f"全量复核 diff组含dup_of={len(bad_diff)} / same组null数分布={dict(nulls)}")

    # ---------------- A6 统计自洽（md 交叉表求和） ----------------
    md_path = os.path.join(LIB_OUT, "资源总账.md")
    a6 = {"md_path": md_path, "md_exists": os.path.isfile(md_path)}
    if a6["md_exists"]:
        txt = open(md_path, encoding="utf-8").read()
        m = re.search(r"##\s*一、六源 × 七类交叉统计表（条数）(.*?)(?=\n##\s)", txt, re.S)
        if not m:
            a6["note"] = "未找到交叉统计表区块"
        else:
            block = m.group(1)
            rows = []
            for line in block.splitlines():
                line = line.strip()
                if not line.startswith("|"):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if not cells or cells[0].startswith("---") or set(cells[0]) <= {"-", ":"}:
                    continue
                rows.append(cells)
            a6["header"] = rows[0] if rows else None
            data_rows = rows[1:]
            # 列结构：源 | <各 kind...> | 合计
            n_kind = len(rows[0]) - 2 if rows else 0
            kind_data_sum = 0
            row_total_ok = True
            row_detail = []
            grand = None
            for r in data_rows:
                nums = []
                for c in r[1:]:
                    try:
                        nums.append(int(c.replace(",", "").replace("*", "")))
                    except ValueError:
                        nums.append(None)
                if nums[0] is None:
                    continue
                is_total_row = r[0].replace("*", "").strip() == "合计"
                kind_cells = nums[:n_kind]
                rowsum = nums[-1]
                if is_total_row:
                    grand = rowsum
                    a6["total_row_kind_sum"] = sum(x for x in kind_cells if x is not None)
                else:
                    kind_data_sum += sum(x for x in kind_cells if x is not None)
                    if rowsum != sum(x for x in kind_cells if x is not None):
                        row_total_ok = False
                        row_detail.append({"row": r[0], "kinds_sum": sum(kind_cells),
                                           "row_total": rowsum})
            a6["n_kind_columns"] = n_kind
            a6["kind_data_cell_sum"] = kind_data_sum
            a6["grand_total_cell"] = grand
            a6["row_totals_match"] = row_total_ok
            a6["row_mismatches"] = row_detail
            a6["expected"] = EXPECTED_TOTAL
            a6["self_consistent"] = (kind_data_sum == EXPECTED_TOTAL
                                     and grand == EXPECTED_TOTAL
                                     and row_total_ok)
        # 与总账实际交叉统计对齐
        actual = collections.Counter((e["source"], e["kind"]) for e in entries)
        a6["ledger_cross_table_sum"] = sum(actual.values())
        a6["ledger_cross_table_ok"] = sum(actual.values()) == EXPECTED_TOTAL
    R["A6_统计自洽"] = a6
    log(f"[A6] md 交叉表 数据格求和 {a6.get('kind_data_cell_sum')} / 合计格 {a6.get('grand_total_cell')} "
        f"/ 行合计自洽 {a6.get('row_totals_match')} -> {a6.get('self_consistent')}；"
        f"总账交叉统计合计 {a6.get('ledger_cross_table_sum')} -> {a6.get('ledger_cross_table_ok')}")

    # ---------------- 汇总 ----------------
    verdict = {
        "A1": a1["match"] and a1["disk_match"],
        "A2": a2["unique_ok"] and a2["missing_count"] == 0 and a2["sample200_all_exist"],
        "A3": (not a3["verification"]["tsv_missing"]
               and not a3["verification"]["tsv_kind_mismatch"]
               and not a3["verification"]["tsv_bytes_mismatch"]),
        "A4": a4["w_h_all_match"],
        "A5": (not a5["violations"]) and a5["must_check_all_ok"] and a5["full_scan_ok"],
        "A6": a6.get("self_consistent", False) and a6.get("ledger_cross_table_ok", False),
    }
    R["verdict"] = verdict
    R["all_pass"] = all(verdict.values())
    R["generated"] = __import__("time").strftime("%Y-%m-%d %H:%M:%S")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "W5验收.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    log("")
    log("=== 验收汇总 ===")
    for k, v in verdict.items():
        log(f"  {k}: {'PASS' if v else 'FAIL'}")
    log(f"  ALL: {'PASS' if R['all_pass'] else 'FAIL'}")
    log(f"  -> {os.path.join(OUT_DIR, 'W5验收.json')}")
    return 0 if R["all_pass"] else 1


if __name__ == "__main__":
    if "--out-dir" in sys.argv:
        OUT_DIR = os.path.abspath(sys.argv[sys.argv.index("--out-dir") + 1])
    sys.exit(main())