# -*- coding: utf-8 -*-
r"""W4b · 补归集 PSV 美咲线素材 → krkr素材库\otv\
====================================================================
背景（主代理派单 W4b）
  W3 只把 PSV 的 UI/系统素材（SystemData.cpk 182 + ETC.cpk 124 = 306）归入 `otv`，
  PSV 美咲线的图像 / 音频 / 影片（D7 裁决「完全采用并并入主线」）从未入库。
  本脚本把 `工程\我们没有翅膀PSV\素材\美咲线\`（**只读**）的素材按 I1 命名规范
  补归集到 `资源组\krkr素材库\otv\`，并把 `otv\_清单.json` **保序合并**（原 306 条一条不丢）。

源（**只读，严禁写入**）：工程\我们没有翅膀PSV\素材\美咲线\
  images\chr(253) images\cg(108) images\etc(3) images\eyecatch(12) audio\voice(1737)
  audio\bgm(28) audio\se(72) video(2)          ← script\(33) 属脚本，不归集
出（写）：
  krkr素材库\otv\{chr,pic,voice,bgm,se,movie}\otv_<原名小写>.<ext>
  krkr素材库\otv\_清单.json     保序合并：原 306 条 + 新增（追加，按 out_relpath 排序）
  krkr素材库\otv\_提取摘要.txt  追加「美咲线素材补充归集」小节（不覆盖 W3 原摘要）
  子代理工作区\ISSUE-20260918-06\W4b\W4b归集自证.json

冲突处置（实测）
  * `images\etc` 的 3 个文件（RULE000.PNG / black.png / white.png）与 W3 的 ETC.cpk
    产物**同名且逐字节相同** → 不重复归集、不重复登记（视为已存在）。
  * `images\eyecatch\EC28.png` 与 `images\cg\EC28.png` 同名且逐字节相同 → 去重为 1 条。
  * 其余跨源同名关系由 cross_source_conflict.py 全量复核（本脚本只做预览）。

用法：python -X utf8 collect_psv_route_assets.py
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

WS = r"E:\ZCode Workspace\Galgame"
PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
OTV = os.path.join(LIB, "otv")
SRC = os.path.join(WS, "工程", "我们没有翅膀PSV", "素材", "美咲线")
OUT_DIR = os.path.join(WS, "子代理工作区", "ISSUE-20260918-06", "W4b")

# (源子目录, 目标 kind 子目录, archive 标签)
MAP = [
    ("images/chr",      "chr",   "美咲线资源/images/CHR"),
    ("images/cg",       "pic",   "美咲线资源/images/CG"),
    ("images/eyecatch", "pic",   "美咲线资源/images/EyeCatch"),
    ("audio/voice",     "voice", "美咲线资源/audio/Voice"),
    ("audio/bgm",       "bgm",   "美咲线资源/audio/BGM"),
    ("audio/se",        "se",    "美咲线资源/audio/SE"),
    ("video",           "movie", "美咲线资源/video"),
]
ETC_SRC = "images/etc"
ETC_KIND = "etc"

NAME_RE = re.compile(r"^otv_[a-z0-9_.\-]+\.(png|ogg|mp4)$")


def log(*a):
    print(*a, flush=True)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def out_name(orig: str) -> str:
    base, ext = os.path.splitext(os.path.basename(orig))
    return "otv_" + base.lower() + ext.lower()


def list_files(d: str):
    return sorted((f for f in os.listdir(d) if not f.startswith("_")),
                  key=lambda s: s.lower())


def main():
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    assert os.path.isdir(SRC), SRC
    assert os.path.isdir(OTV), OTV

    # ---------- 0. 既有 306 条（保序基线） ----------
    mpath = os.path.join(OTV, "_清单.json")
    with open(mpath, encoding="utf-8") as f:
        old_entries = json.load(f)
    old_rel = {e["out_relpath"] for e in old_entries}
    log("[0] 既有 otv/_清单.json: %d 条" % len(old_entries))

    # 既有磁盘文件（用于同名冲突检测）
    old_disk = {}
    for root, _d, files in os.walk(OTV):
        for fn in files:
            if fn.startswith("_"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, OTV).replace("\\", "/")
            old_disk[rel] = full
    log("    既有磁盘文件: %d" % len(old_disk))

    # ---------- 1. 规划归集清单 ----------
    planned = []          # dict(src_abs, rel, orig, kind, archive, group)
    for sub, kind, archive in MAP:
        d = os.path.join(SRC, sub)
        for fn in list_files(d):
            planned.append({
                "src_abs": os.path.join(d, fn),
                "rel": "%s/%s" % (kind, out_name(fn)),
                "orig": fn,
                "kind": kind,
                "archive": archive,
                "group": sub,
            })
    log("[1] 规划归集 %d 个文件（7 个来源子目录）" % len(planned))

    # ---------- 2. 目标内同名去重（同 rel、逐字节相同 → 保留首个） ----------
    by_rel = collections.defaultdict(list)
    for r in planned:
        by_rel[r["rel"]].append(r)
    dedup = []
    for rel, rs in sorted(by_rel.items()):
        if len(rs) == 1:
            dedup.append(rs[0])
            continue
        base = rs[0]
        bmd5 = md5_of(base["src_abs"])
        keep, drop = [base], []
        for r in rs[1:]:
            if md5_of(r["src_abs"]) == bmd5:
                drop.append(r)
            else:
                keep.append(r)          # 同名不同内容：都保留计划，交由步骤 3 报冲突
        dedup.extend(keep)
        for r in drop:
            r["dedup_of"] = base["src_abs"]
        log("    [去重] %s: 同名 %d -> 保留 %d（逐字节相同者丢弃 %d）"
            % (rel, len(rs), len(keep), len(drop)))
    # 被去重丢弃的记录单独留证
    dropped = [r for rs in by_rel.values() for r in rs if r.get("dedup_of")]
    planned = dedup
    log("[2] 去重后待归集 %d 个文件" % len(planned))

    # ---------- 3. 逐文件复制 + 冲突处置 ----------
    copied, skipped_same, conflicts = [], [], []
    for r in planned:
        dst = os.path.join(OTV, r["rel"].replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        ssize = os.path.getsize(r["src_abs"])
        if os.path.exists(dst):
            if os.path.getsize(dst) == ssize and md5_of(dst) == md5_of(r["src_abs"]):
                skipped_same.append(r)
                r["action"] = "already_present_identical"
                continue
            conflicts.append({"rel": r["rel"], "src": r["src_abs"], "dst": dst,
                              "src_bytes": ssize, "dst_bytes": os.path.getsize(dst)})
            r["action"] = "conflict_same_name_diff_bytes"
            continue
        shutil.copy2(r["src_abs"], dst)
        r["dst_abs"] = dst
        r["bytes"] = os.path.getsize(dst)
        r["action"] = "copied"
        copied.append(r)
    log("[3] 复制 %d，已存在且逐字节相同跳过 %d，同名不同内容冲突 %d"
        % (len(copied), len(skipped_same), len(conflicts)))

    # ---------- 4. etc 专项（与既有 ETC.cpk 产物比对） ----------
    etc_rows = []
    for fn in list_files(os.path.join(SRC, ETC_SRC)):
        s = os.path.join(SRC, ETC_SRC, fn)
        rel = "%s/%s" % (ETC_KIND, out_name(fn))
        d = os.path.join(OTV, rel.replace("/", os.sep))
        row = {"orig": fn, "rel": rel, "src_bytes": os.path.getsize(s),
               "exists": os.path.exists(d)}
        if row["exists"]:
            row["same"] = (os.path.getsize(d) == row["src_bytes"]
                           and md5_of(d) == md5_of(s))
        else:
            row["same"] = None
        etc_rows.append(row)
        log("    [etc] %s -> %s  已存在=%s 逐字节相同=%s"
            % (fn, rel, row["exists"], row["same"]))

    # ---------- 5. 字节保真全量复核 ----------
    bad = []
    for r in copied:
        if (os.path.getsize(r["dst_abs"]) != os.path.getsize(r["src_abs"])
                or md5_of(r["dst_abs"]) != md5_of(r["src_abs"])):
            bad.append(r["rel"])
    log("[5] 字节保真全量复核：不符 %d" % len(bad))

    # ---------- 6. 保序合并 _清单.json ----------
    new_entries = []
    for r in sorted(copied, key=lambda x: x["rel"]):
        new_entries.append({
            "archive": r["archive"],
            "orig_name": r["orig"],
            "out_relpath": r["rel"],
            "src_bytes": os.path.getsize(r["src_abs"]),
            "out_bytes": os.path.getsize(r["dst_abs"]),
            "kind": r["kind"],
        })
    merged = list(old_entries) + new_entries
    rels = [e["out_relpath"] for e in merged]
    dup = [x for x, c in collections.Counter(rels).items() if c > 1]
    assert not dup, "清单 out_relpath 重复: %r" % dup[:5]
    assert all(e["out_relpath"] in old_rel for e in old_entries)
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
    log("[6] 保序合并 _清单.json：%d(旧) + %d(新) = %d 条，去重后 out_relpath 重复 %d"
        % (len(old_entries), len(new_entries), len(merged), len(dup)))

    # ---------- 7. 命名 / 零字节 / 磁盘对账 ----------
    name_bad, zero = [], []
    disk_n = 0
    for root, _d, files in os.walk(OTV):
        for fn in files:
            if fn.startswith("_"):
                continue
            disk_n += 1
            rel = os.path.relpath(os.path.join(root, fn), OTV).replace("\\", "/")
            if not NAME_RE.match(fn):
                name_bad.append(rel)
            if os.path.getsize(os.path.join(root, fn)) == 0:
                zero.append(rel)
    log("[7] 磁盘文件 %d；命名不合规 %d；零字节 %d" % (disk_n, len(name_bad), len(zero)))
    count_ok = (disk_n == len(merged))

    # ---------- 8. 随机抽样 cmp（每类 10 个） ----------
    rnd = random.Random(20260918)
    by_kind = collections.defaultdict(list)
    for r in copied:
        by_kind[r["kind"]].append(r)
    samples = {}
    for kind, rs in sorted(by_kind.items()):
        pick = rnd.sample(rs, min(10, len(rs)))
        samples[kind] = [{"rel": x["rel"], "src": x["src_abs"],
                          "identical": (md5_of(x["src_abs"]) == md5_of(x["dst_abs"]))}
                         for x in pick]
        assert all(s["identical"] for s in samples[kind])
    log("[8] 随机抽样 cmp（每类 %s）全部逐字节相同"
        % {k: len(v) for k, v in samples.items()})

    # ---------- 9. 跨源同名预览（复用 W4 scan/md5） ----------
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import cross_source_conflict as C
        other = {}
        for k in ["ot", "otr", "ota", "otp", "np"]:
            for e in C.scan(k):
                other.setdefault(e["stem"], []).append(e)
        hits = collections.Counter()
        details = []
        for r in copied:
            stem = os.path.splitext(os.path.basename(r["rel"]))[0]
            stem = stem[4:] if stem.startswith("otv_") else stem
            stem = stem.lower()
            ms = other.get(stem)
            if not ms:
                continue
            h = md5_of(r["dst_abs"])
            same = sum(1 for e in ms if e["full"] and md5_of(e["full"]) == h)
            hits["hit"] += 1
            hits["identical"] += 1 if same else 0
            hits["different"] += 0 if same else 1
            details.append({"rel": r["rel"], "stem": stem,
                            "others": ["%s/%s" % (e["src"], e["out_relpath"]) for e in ms],
                            "byte_identical_with_any": bool(same)})
        log("[9] 跨源同名预览：命中 %d（其中与他源某文件逐字节相同 %d / 不同 %d）"
            % (hits["hit"], hits["identical"], hits["different"]))
    except Exception as e:                       # 预览失败不影响归集
        hits, details = {}, []
        log("[9] 跨源同名预览失败：%r" % (e,))

    # ---------- 10. 摘要（追加，不覆盖 W3 原文） ----------
    spath = os.path.join(OTV, "_提取摘要.txt")
    per_group = collections.Counter(r["group"] for r in copied)
    lines = ["",
             "=" * 68,
             "# [W4b] PSV 美咲线素材补充归集摘要（追加）",
             "# 生成: %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
             "# 源（只读）: %s" % SRC,
             "# 说明: 原 W3 仅归集 UI/系统素材 306（SystemData.cpk 182 + ETC.cpk 124）。",
             "#       本段补归集 D7 裁决采用的 PSV 美咲线素材；脚本 collect_psv_route_assets.py",
             "#       （可复跑、可审计）。script\\ 33 个文件属脚本，不属素材库，未归集。",
             "",
             "%-22s %8s %8s %14s" % ("来源子目录", "计划", "新增", "新增字节"),
             "-" * 58,
             ]
    for sub, kind, _a in MAP:
        n_new = per_group.get(sub, 0)
        b_new = sum(r["bytes"] for r in copied if r["group"] == sub)
        lines.append("%-22s %8d %8d %14d" % (sub + " -> " + kind, n_new, n_new, b_new))
    lines += [
        "-" * 58,
        "%-22s %8s %8d %14d" % ("合计", "-", len(copied), sum(r["bytes"] for r in copied)),
        "",
        "etc 专项（与既有 ETC.cpk 产物同名比对）：",
    ]
    for row in etc_rows:
        lines.append("  %-14s -> %-22s 已存在=%s 逐字节相同=%s（不重复归集/登记）"
                     % (row["orig"], row["rel"], row["exists"], row["same"]))
    lines.append("")
    lines.append("同名去重：%s"
                 % ("; ".join("%s <= %s" % (r["rel"], r["dedup_of"]) for r in dropped)
                    or "无"))
    lines.append("同名不同内容冲突：%d %s" % (len(conflicts), conflicts or ""))
    lines.append("清单：原 %d 条 + 新增 %d 条 = %d 条（保序合并，原条目不丢）"
                 % (len(old_entries), len(new_entries), len(merged)))
    lines.append("磁盘文件：%d（== 清单条数 %s）" % (disk_n, count_ok))
    lines.append("命名不合规：%d；零字节：%d；字节保真不符：%d" % (len(name_bad), len(zero), len(bad)))
    lines.append("总耗时 %.1f 秒" % (time.time() - t0))
    lines.append("=" * 68)
    with open(spath, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("[10] 摘要追加 → %s" % spath)

    # ---------- 11. 自证 JSON ----------
    selfcheck = {
        "module": "W4b 补归集 PSV 美咲线素材",
        "issue": "ISSUE-20260918-06",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_root": SRC,
        "manifest_old": len(old_entries),
        "manifest_new": len(new_entries),
        "manifest_total": len(merged),
        "copied": len(copied),
        "skipped_already_present_identical": len(skipped_same),
        "conflicts": conflicts,
        "dedup_dropped": [{"rel": r["rel"], "src": r["src_abs"], "dedup_of": r["dedup_of"]}
                          for r in dropped],
        "etc": etc_rows,
        "disk_files": disk_n,
        "disk_equals_manifest": count_ok,
        "name_regex_bad": name_bad,
        "zero_byte": zero,
        "byte_fidelity_bad": bad,
        "per_group_new": dict(per_group),
        "samples_per_kind": samples,
        "cross_source_preview": {"counts": dict(hits), "rows": details},
        "elapsed_sec": round(time.time() - t0, 1),
    }
    with open(os.path.join(OUT_DIR, "W4b归集自证.json"), "w", encoding="utf-8") as f:
        json.dump(selfcheck, f, ensure_ascii=False, indent=1)
    log("[11] 自证 → %s" % os.path.join(OUT_DIR, "W4b归集自证.json"))
    log("完成：新增 %d 条，otv 共 %d 条，用时 %.1fs"
        % (len(new_entries), len(merged), time.time() - t0))


if __name__ == "__main__":
    main()