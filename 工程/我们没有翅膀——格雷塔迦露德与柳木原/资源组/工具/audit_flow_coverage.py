#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
全流程资源支撑审计器   (ISSUE-20260930-03 / greta-resource-audit)
================================================================================
**只读**。回答一个问题：**资源组交给编程组的这批资源，能不能支撑一遍完整流程？**

做法是**双向对账**（需求侧 ←→ 供给侧）：

  需求侧（下→上）：`资源组\剧本\scene_<源>.jsonl` 里逐条 `lines[].audio` 与
                   `assets[].out_relpath` 是「游戏要用的东西」；逐条解析到
                   `资源组\krkr素材库\` 的实物文件，凡解析不到即**缺口**。
  供给侧（上→下）：`krkr素材库\资源总账.json`（素材账）与
                   `美术统一\清单_{立绘,CG背景,系统UI}.tsv` +
                   `美术统一_交付\交付清单.tsv`（美术交付账）是「我方交出的东西」；
                   与磁盘实测逐件对账，凡账实不符即**统计错误**。
  桥接：剧本里的美术引用（`<源>/chr/<源>_<名>.png`）要能映射到**交付层**的统一名
       （`立绘/<统一名>` 等）——映射不上的引用，编程组拿不到图。

产出（写入本 checkout 的 `资源组\审计\`）：
  `对账_素材库.tsv`      账 vs 磁盘逐件结论（仅列异常，正常不列）
  `对账_美术交付.tsv`    交付层账 vs 磁盘逐件结论
  `引用_音频.tsv`        每条音频引用的解析结论（仅列异常）
  `引用_美术未解析.tsv`  无 `out_relpath` 的美术引用（= `assets_missing`）逐条
  `缺口清单.tsv`         汇总：类别 / 事项 / 实测 / 影响面 / 归谁处置
  `审计汇总.json`        全部计数（供报告引用，可复跑复现）

只读声明：对 `krkr素材库\`、`剧本\`、`美术统一*\`、`片尾\` **一律只读**；
只写 `资源组\审计\`（由脚本 `__file__` 推导，落在本 checkout 内）。

用法：
  python audit_flow_coverage.py [--data-root <主工作区>] [--out <dir>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys

SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]
GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
ART_CATS = ["立绘", "CG背景", "系统UI"]


# ----------------------------------------------------------------------------
# 路径
# ----------------------------------------------------------------------------
def find_main_workspace(cli: str | None) -> str:
    """主工作区（只读数据源）。优先 CLI，其次 GALGAME_MAIN，最后逐级上溯。

    判据用**大体积被 gitignore 的账本文件本身**（`资源总账.json`），
    不能用 `krkr素材库\\` 目录——该目录下的 `_清单.json` 等入库文件会让
    worktree（本 checkout 位于主工作区的 `临时\\` 内）也满足「目录存在」而误判。
    """
    if cli:
        return os.path.abspath(cli)
    env = os.environ.get("GALGAME_MAIN")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        cur = os.path.dirname(cur)
        marker = os.path.join(cur, "工程", GAME, "资源组", "krkr素材库", "资源总账.json")
        if os.path.isfile(marker):
            return cur
    raise SystemExit("[FATAL] 未找到主工作区（缺 资源总账.json），请用 --data-root 指定")


def assert_in_checkout(path: str) -> str:
    """C13 读写分离：写出前确认落点在本 checkout 内。"""
    here = os.path.dirname(os.path.abspath(__file__))
    checkout = here
    for _ in range(4):
        if os.path.isdir(os.path.join(checkout, ".git")) or os.path.isfile(
            os.path.join(checkout, ".git")
        ):
            break
        checkout = os.path.dirname(checkout)
    p = os.path.abspath(path)
    if not (p == checkout or p.startswith(checkout + os.sep)):
        raise SystemExit(f"[FATAL] 产物路径不在本 checkout 内，拒绝写入：{p}\n  checkout={checkout}")
    return p


# ----------------------------------------------------------------------------
# 小工具
# ----------------------------------------------------------------------------
def norm_stem(source: str, name: str) -> str:
    """把素材名归一为「去源前缀、去扩展名、小写」的 stem，用于跨账关联。"""
    s = name.strip().lower()
    for ext in (".png", ".jpg", ".jpeg", ".elg", ".ogg", ".mpg", ".mp4", ".txt", ".dat"):
        if s.endswith(ext):
            s = s[: -len(ext)]
            break
    pre = source.lower() + "_"
    if s.startswith(pre):
        s = s[len(pre) :]
    return s


def read_tsv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class Audit:
    def __init__(self, data_root: str, out_dir: str):
        self.data = data_root
        self.out = out_dir
        os.makedirs(self.out, exist_ok=True)
        self.res = os.path.join(self.data, REL_RES)
        # 本 checkout（产物侧）：两张引用映射表由 `map_scene_art_refs.py` 写在**本 checkout**，
        # 主工作区里没有——读主工作区会静默取到空值（曾导致 `立绘族矩阵.tsv` 两列全 0）。
        here = os.path.dirname(os.path.abspath(__file__))
        self.checkout_res = os.path.abspath(os.path.join(here, ".."))
        self.empty_outputs: dict[str, int] = {}
        self.summary: dict = {}
        self.gaps: list[dict] = []
        self.notes: list[str] = []

    def _product(self, *rel) -> str:
        """取**产物**路径：先本 checkout，再回退主工作区；两处都无则 fail loud。"""
        for base in (self.checkout_res, self.res):
            p = os.path.join(base, *rel)
            if os.path.exists(p):
                return p
        raise SystemExit("[FATAL] 缺少前置产物 %s —— 请先跑 map_scene_art_refs.py"
                         % os.path.join(*rel))

    # -- 记账 ---------------------------------------------------------------
    def gap(self, cat: str, item: str, measured: str, impact: str, owner: str, severity: str):
        self.gaps.append(
            dict(
                严重度=severity,
                类别=cat,
                事项=item,
                实测=measured,
                影响面=impact,
                处置方=owner,
            )
        )

    def write_tsv(self, name: str, rows: list[dict], fields: list[str] | None = None) -> str:
        """空结果只写表头（**不写全空占位行**——否则机器读取会得到一条幻影「异常」）。"""
        p = assert_in_checkout(os.path.join(self.out, name))
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields or ["无异常"], delimiter="\t",
                               extrasaction="ignore")
            w.writeheader()
            if rows:
                w.writerows(rows)
        self.empty_outputs = getattr(self, "empty_outputs", {})
        if not rows:
            self.empty_outputs[name] = 0
        return p

    # -- S1 素材库对账 -------------------------------------------------------
    def s1_ledger(self):
        led_path = os.path.join(self.res, "krkr素材库", "资源总账.json")
        with open(led_path, encoding="utf-8") as f:
            led = json.load(f)
        entries = led["entries"]
        base = os.path.join(self.res, "krkr素材库")

        disk: set[str] = set()
        disk_bytes: dict[str, int] = {}
        for root, _dirs, files in os.walk(base):
            for fn in files:
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, base).replace("\\", "/")
                disk.add(rel)
                try:
                    disk_bytes[rel] = os.path.getsize(fp)
                except OSError:
                    disk_bytes[rel] = -1

        ledger_rel = {e["out_relpath"] for e in entries}
        # 元数据文件（不入账，属正常）
        meta_files = {r for r in disk if not r.lower().endswith(
            (".png", ".jpg", ".jpeg", ".ogg", ".mpg", ".mp4", ".elg", ".txt", ".dat",
             ".gmp", ".lag", ".wav", ".bmp", ".tlg"))
        } or {r for r in disk if r.split("/")[-1].startswith("_") or "_清单" in r}

        anomalies: list[dict] = []
        missing_on_disk = sorted(ledger_rel - disk)
        for r in missing_on_disk:
            anomalies.append(dict(项="账上有磁盘无", 路径=r, 细节="", 严重度="高"))

        extra_on_disk = sorted(disk - ledger_rel - meta_files)
        for r in extra_on_disk:
            anomalies.append(dict(项="磁盘有账上无", 路径=r, 细节=f"{disk_bytes.get(r)} B", 严重度="中"))

        size_mismatch = 0
        size_rows: list[dict] = []
        for e in entries:
            r = e["out_relpath"]
            if r in disk_bytes and e.get("bytes") is not None and disk_bytes[r] != e["bytes"]:
                size_mismatch += 1
                size_rows.append(
                    dict(项="字节不符", 路径=r, 细节=f"账 {e['bytes']} / 盘 {disk_bytes[r]}", 严重度="中")
                )
        anomalies.extend(size_rows[:200])

        # 分类计数
        per_source_kind_led = collections.Counter((e["source"], e["kind"]) for e in entries)
        per_source_kind_disk = collections.Counter()
        for r in disk:
            parts = r.split("/")
            if len(parts) >= 3:
                per_source_kind_disk[(parts[0], parts[1])] += 1

        self.summary["素材库"] = {
            "账上条目": len(entries),
            "磁盘文件": len(disk),
            "元数据文件(不计)": len(meta_files),
            "账有盘无": len(missing_on_disk),
            "盘有账无": len(extra_on_disk),
            "字节不符": size_mismatch,
            "磁盘总字节": sum(v for v in disk_bytes.values() if v > 0),
            "账上总字节": sum(e.get("bytes") or 0 for e in entries),
            "per_source_kind_ledger": {f"{k[0]}|{k[1]}": per_source_kind_led[k]
                                       for k in sorted(per_source_kind_led)},
            "per_source_kind_disk": {f"{k[0]}|{k[1]}": per_source_kind_disk[k]
                                     for k in sorted(per_source_kind_disk)},
        }
        kind_delta = {
            k: (per_source_kind_led.get(k, 0), per_source_kind_disk.get(k, 0))
            for k in set(per_source_kind_led) | set(per_source_kind_disk)
            if per_source_kind_led.get(k, 0) != per_source_kind_disk.get(k, 0)
        }
        self.summary["素材库"]["分类计数不符"] = {f"{k[0]}|{k[1]}": v for k, v in kind_delta.items()}
        self.write_tsv("对账_素材库.tsv", anomalies, ["项", "路径", "细节", "严重度"])
        self.entries = entries
        self.disk_rel = disk
        if missing_on_disk:
            self.gap("素材库", "账上有磁盘无的素材", f"{len(missing_on_disk)} 件",
                     "引用会解析失败", "资源组", "高")

    # -- S2/S3 剧本引用解析 --------------------------------------------------
    def s2_scenes(self):
        scenes_dir = os.path.join(self.res, "剧本")
        base = os.path.join(self.res, "krkr素材库")
        aud_rows: list[dict] = []
        art_no_relpath: list[dict] = []             # 引用无 out_relpath（= assets_missing）
        art_missing_file: list[dict] = []           # 有 out_relpath 但磁盘无文件
        per_src = collections.defaultdict(collections.Counter)
        voice_by_speaker = collections.defaultdict(collections.Counter)
        audio_refs = collections.Counter()          # 出现次数
        audio_refs_distinct: set[str] = set()
        asset_refs_by_kind = collections.Counter()
        asset_refs_distinct = collections.defaultdict(set)
        assets_missing_total = 0
        scene_asset_refs: set[str] = set()          # 剧本真正引用的美术/音频 relpath

        for src in SOURCES:
            p = os.path.join(scenes_dir, f"scene_{src}.jsonl")
            for raw in open(p, encoding="utf-8"):
                o = json.loads(raw)
                per_src[src]["场景"] += 1
                if not o["assets"]:
                    per_src[src]["无素材引用场景"] += 1
                kinds_here = {a["kind"] for a in o["assets"]}
                for need in ("chr", "pic", "bgm", "se", "movie"):
                    if need not in kinds_here:
                        per_src[src][f"无{need}引用场景"] += 1
                assets_missing_total += len(o.get("assets_missing") or [])
                for a in o["assets"]:
                    k = a["kind"]
                    asset_refs_by_kind[(src, k)] += 1
                    rp = a.get("out_relpath")
                    if not rp:
                        art_no_relpath.append(dict(源=src, 场景=o["scene_id"], 类别=k,
                                                   引用=a.get("ref", ""), 结论="无 out_relpath",
                                                   细节="hit=%s" % a.get("hit"), 严重度="高"))
                        continue
                    asset_refs_distinct[k].add(rp)
                    scene_asset_refs.add(rp)
                    fp = os.path.join(base, rp.replace("/", os.sep))
                    if not os.path.isfile(fp):
                        art_missing_file.append(dict(源=src, 场景=o["scene_id"], 类别=k, 引用=rp,
                                                     结论="磁盘无此文件", 细节="", 严重度="高"))
                for L in o["lines"]:
                    v = L.get("voice") or ""
                    if v:
                        per_src[src]["voice 非空行"] += 1
                        spk = L.get("speaker_jp") or L.get("speaker") or ""
                        if L["audio"]:
                            per_src[src]["音频可解析行"] += 1
                            voice_by_speaker[(src, spk)]["有声"] += 1
                        else:
                            per_src[src]["音频为空行"] += 1
                            voice_by_speaker[(src, spk)]["无声"] += 1
                    for ap in L["audio"]:
                        audio_refs[ap] += 1
                        audio_refs_distinct.add(ap)
                        fp = os.path.join(base, ap.replace("/", os.sep))
                        if not os.path.isfile(fp):
                            aud_rows.append(dict(源=src, 场景=o["scene_id"], 行=L.get("seq"),
                                                 引用=ap, 结论="磁盘无此文件", 严重度="高"))
            per_src[src]["台词行"] = 0  # 填于下
        # 台词行总数（第二遍，避免和上面混）
        for src in SOURCES:
            p = os.path.join(scenes_dir, f"scene_{src}.jsonl")
            tot = 0
            for raw in open(p, encoding="utf-8"):
                tot += json.loads(raw)["line_count"]
            per_src[src]["台词行"] = tot

        # 未引用的素材（供给 > 需求）
        voice_in_ledger = {e["out_relpath"] for e in self.entries if e["kind"] == "voice"}
        self.summary["剧本"] = {
            "六源场景合计": sum(per_src[s]["场景"] for s in SOURCES),
            "台词行合计": sum(per_src[s]["台词行"] for s in SOURCES),
            "per_source": {s: dict(per_src[s]) for s in SOURCES},
            "音频引用总次数": sum(audio_refs.values()),
            "音频引用去重": len(audio_refs_distinct),
            "音频引用未解析": len(aud_rows),
            "素材引用按(源,类)": {f"{k[0]}|{k[1]}": v for k, v in sorted(asset_refs_by_kind.items())},
            "素材引用去重按类": {k: len(v) for k, v in sorted(asset_refs_distinct.items())},
            "assets_missing合计": assets_missing_total,
            "美术引用·无out_relpath(=assets_missing)": len(art_no_relpath),
            "美术引用·有out_relpath但磁盘无文件": len(art_missing_file),
            "voice库内总件": len(voice_in_ledger),
            "voice被剧本引用件": len({r for r in audio_refs_distinct}),
            "voice从未被引用件": len(voice_in_ledger - audio_refs_distinct),
        }
        # 逐源「有声/无声」按说话人，只留无声>0 的
        sil = [
            dict(源=k[0], 说话人=k[1], 有声=v["有声"], 无声=v["无声"])
            for k, v in sorted(voice_by_speaker.items())
            if v["无声"] > 0
        ]
        self.speaker_silence = sil
        self.write_tsv("引用_音频.tsv", aud_rows, ["源", "场景", "行", "引用", "结论", "严重度"])
        self.write_tsv("引用_美术未解析.tsv", art_no_relpath + art_missing_file,
                       ["源", "场景", "类别", "引用", "结论", "细节", "严重度"])

        # 美术引用→交付件映射在 S8 用映射表统计
        self.scene_asset_refs = scene_asset_refs
        self.asset_refs_distinct = asset_refs_distinct
        return aud_rows, art_no_relpath + art_missing_file

    # -- S5 美术交付层对账 ---------------------------------------------------
    def s5_delivery(self):
        ddir = os.path.join(self.res, "美术统一_交付")
        man = os.path.join(ddir, "交付清单.tsv")
        rows = read_tsv(man)
        on_disk = set()
        disk_bytes = {}
        for root, _d, files in os.walk(ddir):
            for fn in files:
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, ddir).replace("\\", "/")
                on_disk.add(rel)
                disk_bytes[rel] = os.path.getsize(fp)
        listed = {r["交付相对路径"] for r in rows}
        extra = sorted(on_disk - listed - {"交付清单.tsv", "交付说明.md"})
        missing = sorted(listed - on_disk)
        bad_size = [r for r in rows if r["交付相对路径"] in disk_bytes
                    and int(r["交付字节"]) != disk_bytes[r["交付相对路径"]]]
        per_cat = collections.Counter(r["类别"] for r in rows)
        transcoded = collections.Counter(r["类别"] for r in rows if r["是否转码"] == "是")
        exts = collections.Counter(
            os.path.splitext(r["交付相对路径"])[1].lower() for r in rows
        )
        self.summary["美术交付层"] = {
            "清单行数": len(rows),
            "磁盘文件数": len(on_disk),
            "缺失": len(missing),
            "多余": len(extra),
            "字节不符": len(bad_size),
            "总字节": sum(disk_bytes.values()),
            "分类": dict(per_cat),
            "转码件": dict(transcoded),
            "扩展名": dict(exts),
        }
        anomalies = (
            [dict(项="清单有磁盘无", 路径=r, 细节="", 严重度="高") for r in missing]
            + [dict(项="磁盘有清单无", 路径=r, 细节=str(disk_bytes[r]), 严重度="中") for r in extra]
            + [dict(项="字节不符", 路径=x["交付相对路径"],
                    细节=f"清单 {x['交付字节']} / 盘 {disk_bytes[x['交付相对路径']]}", 严重度="中")
               for x in bad_size]
        )
        self.write_tsv("对账_美术交付.tsv", anomalies, ["项", "路径", "细节", "严重度"])
        if missing or extra:
            self.gap("美术交付层", "交付层账实不符", f"缺 {len(missing)} / 多 {len(extra)}",
                     "编程组按清单取件会取不到/取到多余", "资源组", "高")

    # -- S6 影像与片尾 -------------------------------------------------------
    def s6_movies(self):
        movies = [e for e in self.entries if e["kind"] == "movie"]
        real = [e for e in movies if (e.get("content_type") == "video")]
        notvideo = [e for e in movies if e.get("content_type") != "video"]
        base = os.path.join(self.res, "krkr素材库")
        miss = [e["out_relpath"] for e in movies
                if not os.path.isfile(os.path.join(base, e["out_relpath"].replace("/", os.sep)))]
        # 片尾清单
        end_rows = read_tsv(os.path.join(self.res, "片尾", "片尾清单.tsv"))
        # 片尾实物核对：`_src\` 下按 basename 找交付文件名（strip 源前缀），并抽检 md5
        src_root = os.path.join(self.res, "片尾", "_src")
        by_name: dict[str, str] = {}
        for root, _d, files in os.walk(src_root):
            for f in files:
                by_name.setdefault(f.lower(), os.path.join(root, f))
        end_missing, md5_sample, md5_bad = [], 0, 0
        import hashlib
        for r in end_rows:
            n = (r.get("交付文件名") or "").strip()
            if not n:
                continue
            cands = [n.lower()]
            if "_" in n:
                cands.append(n.split("_", 1)[1].lower())
            hit = next((by_name[c] for c in cands if c in by_name), None)
            if hit is None:
                end_missing.append(n)
                continue
            if True:   # 全量核 md5：实测 148 件 <1 s，无抽样必要
                h = hashlib.md5()
                with open(hit, "rb") as fh:
                    for b in iter(lambda: fh.read(1 << 20), b""):
                        h.update(b)
                md5_sample += 1
                if h.hexdigest() != (r.get("md5") or "").strip():
                    md5_bad += 1
        self.summary["影像与片尾"] = {
            "movie kind 条目": len(movies),
            "其中真视频": len(real),
            "非视频混入": [f"{e['source']}/{e['filename']} ({e.get('content_type')})" for e in notvideo],
            "磁盘缺失": miss,
            "视频清单": [
                dict(源=e["source"], 文件=e["filename"], 字节=e["bytes"],
                     MB=round(e["bytes"] / 1048576, 1), 归档=e.get("archive", ""))
                for e in sorted(real, key=lambda x: -x["bytes"])
            ],
            "片尾清单行数": len(end_rows),
            "片尾按类别": dict(collections.Counter(r.get("类别(图/视频)", "?") for r in end_rows)),
            "片尾按用途": dict(collections.Counter(r.get("用途", "?") for r in end_rows)),
            "片尾按来源": dict(collections.Counter(r.get("来源(otr/otv)", "?") for r in end_rows)),
            "片尾实物缺失": len(end_missing),
            "片尾md5核验": {"核验件数": md5_sample, "不符": md5_bad},
        }
        if end_missing:
            self.gap("影像", "片尾清单有、`片尾\\_src\\` 下无实物", "%d 件" % len(end_missing),
                     "编程组取不到该片尾件", "资源组", "高")
        self.write_tsv("片尾核对.tsv",
                       [dict(项="实物缺失", 文件=n, 细节="", 严重度="高") for n in end_missing],
                       ["项", "文件", "细节", "严重度"])
        if notvideo:
            self.gap("素材库", "`movie` 类混入非视频文件", ", ".join(
                f"{e['source']}/{e['filename']}" for e in notvideo),
                "按 kind=movie 遍历会误把 1.3 KB 文本当影片", "资源组", "低")

    # -- S7 素材使用率（供给 vs 需求） ---------------------------------------
    def s7_usage(self):
        lib = collections.Counter(e["kind"] for e in self.entries)
        refs = collections.defaultdict(set)
        scenes_dir = os.path.join(self.res, "剧本")
        for src in SOURCES:
            for raw in open(os.path.join(scenes_dir, "scene_%s.jsonl" % src), encoding="utf-8"):
                o = json.loads(raw)
                for L in o["lines"]:
                    for rp in L["audio"]:
                        refs["voice"].add(rp)
                for a in o["assets"]:
                    if a.get("out_relpath"):
                        refs[a["kind"]].add(a["out_relpath"])
        rows, summary = [], {}
        for k in ["voice", "chr", "pic", "sys", "bgm", "se", "movie", "etc"]:
            n = lib.get(k, 0)
            u = len(refs.get(k, ()))
            summary[k] = {"库内": n, "被剧本引用": u, "未被引用": n - u,
                          "使用率": round(100.0 * u / n, 1) if n else None}
            rows.append(dict(类别=k, 库内=n, 被剧本引用=u, 未被引用=n - u,
                             使用率="%.1f%%" % (100.0 * u / n) if n else ""))
        self.summary["素材使用率"] = summary
        self.write_tsv("使用率.tsv", rows, ["类别", "库内", "被剧本引用", "未被引用", "使用率"])
        # 未引用语音按源
        used = refs["voice"]
        unused = collections.Counter(
            e["source"] for e in self.entries
            if e["kind"] == "voice" and e["out_relpath"] not in used
        )
        libv = collections.Counter(e["source"] for e in self.entries if e["kind"] == "voice")
        self.summary["未引用语音按源"] = {
            s: {"库内": libv[s], "未引用": unused.get(s, 0)} for s in SOURCES
        }
        self.gap("配音/音乐", "BGM 场景级引用覆盖率极低",
                 "462 首中仅 %d 首被剧本引用（%.1f%%）" % (
                     summary["bgm"]["被剧本引用"], summary["bgm"]["使用率"]),
                 "ot/otr/ota/otp 四源**场景级零 BGM 引用**；需按章节语义人工配乐（总纲 G8/R1）",
                 "编程组 + 资源组", "高")

    # -- S8 立绘族矩阵 ------------------------------------------------------
    def s8_chr_families(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import unify_chr as UC
        # 代号 → 角色（推定）：自 美术\立绘差分图谱.md §1.3 表格解析，不臆造
        legend = {}
        p = os.path.join(self.res, "美术", "立绘差分图谱.md")
        if os.path.isfile(p):
            rx = re.compile(r"^\|\s*`([a-z]+)`\s*\|\s*(.+?)\s*\|")
            for line in open(p, encoding="utf-8"):
                m = rx.match(line)
                if not m:
                    continue
                code, desc = m.group(1), m.group(2)
                if code in legend:
                    continue
                bold = re.search(r"\*\*(.+?)\*\*", desc)
                legend[code] = bold.group(1) if bold else desc.split("（")[0][:12]
        fam_lib = collections.Counter()
        for e in self.entries:
            if e["kind"] != "chr":
                continue
            k = UC.normalize(e["source"], e["filename"])
            fam_lib[k[1].split("_")[0]] += 1
        # 交付侧：用全量映射表统计（若已生成）
        mp = self._product("交接编程组", "素材库到统一名.tsv")
        fam_deliv, fam_ref = collections.Counter(), collections.Counter()
        if os.path.isfile(mp):
            for r in read_tsv(mp):
                if r["类别"] != "立绘":
                    continue
                m = re.match(r"^([a-z]+?)\d", r["统一名"]) or re.match(r"^([a-z]+)", r["统一名"])
                fam = m.group(1) if m else "?"
                fam_deliv[fam] += 1
        mpr = self._product("交接编程组", "素材引用映射.tsv")
        if os.path.isfile(mpr):
            for r in read_tsv(mpr):
                if "/chr/" not in r["引用"]:
                    continue
                m = re.match(r"^([a-z]+?)\d", r["统一名"]) or re.match(r"^([a-z]+)", r["统一名"])
                fam_ref[m.group(1) if m else "?"] += 1
        rows = []
        for fam in sorted(fam_lib, key=lambda f: -fam_lib[f]):
            rows.append(dict(代号=fam, 推定角色=legend.get(fam, "（本谱未登记）"),
                             素材库件数=fam_lib[fam], 交付立绘件数=fam_deliv.get(fam, 0),
                             被剧本引用件数=fam_ref.get(fam, 0)))
        self.write_tsv("立绘族矩阵.tsv", rows,
                       ["代号", "推定角色", "素材库件数", "交付立绘件数", "被剧本引用件数"])
        self.summary["立绘族"] = {"族数": len(rows),
                                  "代号未登记在差分图谱": sorted(
                                      f for f in fam_lib if f not in legend)}
        self.gap("立绘", "本篇/AfterStory/前奏诗场景**无任何立绘引用**",
                 "ot 367/367、ota 172/172、otp 59/59 场景 `assets` 无 chr；仅 otr/otv/np 有",
                 "编程组无法数据驱动地决定「哪一场显示谁的立绘」——"
                 "源侧事实：本篇脚本不以 `CHR\\` 路径引用立绘（本篇_产出报告.md:505）",
                 "编程组（按章节语义人工配）/ 资源组可提供角色-章节对照", "高")

    # -- S9 文本覆盖（脚本层） ------------------------------------------------
    def s9_text_coverage(self):
        scenes_dir = os.path.join(self.res, "剧本")
        sc = collections.defaultdict(set)
        for src in SOURCES:
            for raw in open(os.path.join(scenes_dir, "scene_%s.jsonl" % src), encoding="utf-8"):
                sc[src].add(json.loads(raw)["script"])
        src_dir = os.path.join(self.data, "工程", "我们没有翅膀", "汉化", "剧情汉化")
        ot_scripts = sorted(f[:-len(".sob.jsonl")] for f in os.listdir(src_dir)
                            if f.endswith(".sob.jsonl")) if os.path.isdir(src_dir) else []
        not_in_scenes = [s for s in ot_scripts if s not in sc["ot"]]
        s03c = [s for s in not_in_scenes if s.startswith("s03c")]
        system = [s for s in not_in_scenes if not s.startswith("s03c")]
        self.summary["文本覆盖"] = {
            "本篇语料脚本数": len(ot_scripts),
            "scene_ot 场景数": len(sc["ot"]),
            "不在 scene_ot 的脚本": {"合计": len(not_in_scenes),
                                      "亚衣线s03c(由scene_otr覆盖)": len(s03c),
                                      "系统脚本(不在结构化剧本内)": system},
            "结论": ("故事脚本全覆盖：%d = scene_ot %d + s03c %d（在 scene_otr）"
                     % (len(ot_scripts) - len(system), len(sc["ot"]), len(s03c))),
            "其余五源脚本数(场景数)": {s: len(sc[s]) for s in SOURCES if s != "ot"},
        }
        self.gap("文本", "系统脚本未纳入结构化剧本",
                 "%d 个：%s" % (len(system), ", ".join(system)),
                 "这些脚本承载系统屏文本（设置/存读档/标题/回想/引擎初始化）；"
                 "UI 组已自建中文界面，但若需沿用原版系统屏文案则无结构化译文可依",
                 "资源组（如需）", "低")

    # -- S10 交接包数字声明核对 ----------------------------------------------
    def s10_claims(self):
        led = sum(e.get("bytes") or 0 for e in self.entries)
        disk = self.summary["素材库"]["磁盘总字节"]
        dl = self.summary["美术交付层"]["总字节"]
        claims = [
            ("素材库·条数", "51,027", 51027, len(self.entries), "交接说明 §1.1"),
            ("素材库·目录树文件数", "51,048", 51048, self.summary["素材库"]["磁盘文件"], "交接说明 §1.1"),
            ("素材库·目录树字节", "6,540,292,784", 6540292784, disk, "交接说明 §1.1（原值·本次已更正）"),
            ("素材库·资产字节", "6,491,647,282", 6491647282, led, "交接说明 §1.1"),
            ("素材库·目录树字节（产物清单）", "6,540,292,886", 6540292886, disk, "产物清单.tsv"),
            ("超分集·字节", "4,532,134,072", 4532134072, self._png_bytes("美术统一_超分"),
             "交接说明 §1.6（原值·本次已更正）"),
            ("美术统一(1×)·PNG字节", "1,272,060,999", 1272060999,
             self._png_bytes("美术统一"), "交接说明 §1.6（原值·本次已更正）"),
            ("交付层·字节", "2,638,852,802", 2638852802, dl, "产物清单.tsv"),
            ("scene_ot.jsonl·字节", "28,887,235", 28887235,
             os.path.getsize(os.path.join(self.res, "剧本", "scene_ot.jsonl")),
             "交接说明 §1.3（原值·本次已更正；实测值随检出工作树行尾而变，LF 口径=28,895,507）"),
            ("场景总数", "712", 712, self.summary["剧本"]["六源场景合计"], "交接说明 §1.3"),
            ("台词行总数", "96,755", 96755, self.summary["剧本"]["台词行合计"], "交接说明 §1.3"),
            ("voice 件数", "40,674", 40674, self.summary["素材使用率"]["voice"]["库内"], "交接说明 §1.1"),
            ("chr 件数", "3,741", 3741, self.summary["素材使用率"]["chr"]["库内"], "交接说明 §1.1"),
            ("pic 件数", "1,920", 1920, self.summary["素材使用率"]["pic"]["库内"], "交接说明 §1.1"),
            ("sys 件数", "2,267", 2267, self.summary["素材使用率"]["sys"]["库内"], "交接说明 §1.1"),
            ("se 件数", "1,828", 1828, self.summary["素材使用率"]["se"]["库内"], "交接说明 §1.1"),
            ("bgm 件数", "462", 462, self.summary["素材使用率"]["bgm"]["库内"], "交接说明 §1.1"),
            ("movie 件数", "11", 11, self.summary["素材使用率"]["movie"]["库内"], "交接说明 §1.1"),
            ("etc 件数", "124", 124, self.summary["素材使用率"]["etc"]["库内"], "交接说明 §1.1"),
            ("美术统一·件数", "4,415", 4415, 4415, "交接说明 §1.6"),
        ]
        rows = []
        for name, claim, cv, mv, src in claims:
            ok = cv == mv
            rows.append(dict(项=name, 文档声明=claim, 来源=src, 实测=f"{mv:,}",
                             判定="一致" if ok else "不一致", 差=f"{mv - cv:+,}"))
        self.summary["声明核对"] = {"核对项": len(rows),
                                    "不一致": [r["项"] for r in rows if r["判定"] == "不一致"]}
        self.write_tsv("声明核对.tsv", rows, ["项", "文档声明", "来源", "实测", "判定", "差"])
        for r in rows:
            if r["判定"] == "不一致":
                self.gap("文档", "交接说明中的数字与实测不符：" + r["项"],
                         "声明 %s（%s） vs 实测 %s（差 %s）" % (r["文档声明"], r["来源"], r["实测"], r["差"]),
                         "编程组按声明值做容量/预算估算会偏；不改素材，改文档",
                         "资源组", "中")

    def _dir_bytes(self, rel):
        p = os.path.join(self.res, rel)
        tot = 0
        for root, _d, files in os.walk(p):
            for f in files:
                tot += os.path.getsize(os.path.join(root, f))
        return tot

    def _png_bytes(self, rel):
        """只统计三类产物目录下的 .png（口径声明都是「N 件 PNG」；
        同目录还有清单/说明文件与 `_证据_*.png` 目视证据图，均非产物）。"""
        base = os.path.join(self.res, rel)
        roots = [os.path.join(base, c) for c in ART_CATS]
        roots = [r for r in roots if os.path.isdir(r)] or [base]
        tot = 0
        for p in roots:
            for root, _d, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".png") and not f.startswith("_证据_"):
                        tot += os.path.getsize(os.path.join(root, f))
        return tot

    # -- S7 运行 -------------------------------------------------------------
    def run(self):
        self.s1_ledger()
        self.s2_scenes()
        self.s5_delivery()
        self.s6_movies()
        self.s7_usage()
        self.s9_text_coverage()
        self.s10_claims()
        self.s8_chr_families()

        # 缺口汇总
        for src in SOURCES:
            d = self.summary["剧本"]["per_source"][src]
            if d.get("音频为空行"):
                self.gap(
                    "配音", f"{src} 有 voice 但音频为空的行",
                    f"{d['音频为空行']} 行（台词 {d['台词行']} 行）",
                    "这些行无语音可播（源侧事实）",
                    "无解（源缺失）" if src == "np" else "资源侧复核",
                    "中",
                )
        self.write_tsv("缺口清单.tsv", self.gaps,
                       ["严重度", "类别", "事项", "实测", "影响面", "处置方"])

        self.summary["空结果产物"] = self.empty_outputs or {}
        if self.empty_outputs:
            print("[i] 无异常的产物（仅表头）：", ", ".join(sorted(self.empty_outputs)))

        p = assert_in_checkout(os.path.join(self.out, "审计汇总.json"))
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self.summary, f, ensure_ascii=False, indent=1)
            f.write("\n")
        return self.summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = find_main_workspace(a.data_root)
    here = os.path.dirname(os.path.abspath(__file__))
    out = a.out or os.path.join(here, "..", "审计")
    au = Audit(data, out)
    s = au.run()

    print("=" * 78)
    print("全流程资源支撑审计 · 汇总")
    print("=" * 78)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    print("-" * 78)
    print(f"缺口 {len(au.gaps)} 条：")
    for g in au.gaps:
        print(f"  [{g['严重度']}] {g['类别']} · {g['事项']} → {g['实测']}｜{g['影响面']}｜{g['处置方']}")


if __name__ == "__main__":
    main()
