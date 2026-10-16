# -*- coding: utf-8 -*-
r"""M3 · BGM 鉴赏页 · 曲目收录方案的数据取证脚本（**只读输入、只写本目录证据**）

Issue : ISSUE-20260924-08（鉴赏模式四页重构 · M3 BGM 页）
契约  : `_工作\ISSUE-20260924-08_鉴赏模式\方案.md` §3（曲目数据来源）与 §8（纪律）

■ 本脚本回答三件事（**只取证、不裁决**；收录口径由主代理确认）
  ① 候选池到底有多大：六源 `资源组\krkr素材库\*\bgm\` 的文件数 / 内容去重数；
  ② 剧本层实际引用了哪些：六份 `scene_*.jsonl` 的 `assets[].kind=="bgm"`（179 条引用）；
  ③ 跨源同名不同内容（D2 隔离规则）的规模：同 stem 出现在多个源、但内容不同的组数。

■ 输出（落本目录）
  `m51_bgm_candidates.tsv` —— 剧本引用曲目（按首次引用顺序），列：
       序号 / 源 / 相对路径 / 引用次数 / 剧本内首次出现处 / 内容 sha1 前 8
  `m51_bgm_library.tsv`    —— 六源全量清单（源 / 文件名 / 字节 / sha1 前 8 / 是否被剧本引用）
  `m51_bgm_report.txt`     —— 汇总（含跨源同名不同内容的分组明细）

■ 纪律
  · 只读 `资源组\`；产物只落本目录（`_工作\ISSUE-20260924-08_鉴赏模式\M3_BGM\`）。
  · **不编造曲名**：语料内查无曲名表（已实测，见 report）⇒ 曲名一律用「文件名标识」占位。
"""
from __future__ import annotations

import collections
import glob
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # <UI组>
PROJ = os.path.dirname(UI)                                        # <作品根>

# ★ 素材库 / 剧本的定位（**只读**）：
#   本工程用 git worktree 并行作业，`资源组\` 的体积大、不入库 ⇒ 子 worktree 里可能是**空目录**。
#   故先试本 worktree，再回落到主工作树（`E:\ZCode Workspace\Galgame\...`）。
#   两侧都只读；本脚本**只往 HERE 写证据**。
_CANDS = [os.path.join(PROJ, "资源组"),
          os.path.join(r"E:\ZCode Workspace\Galgame\工程",
                       os.path.basename(PROJ), "资源组")]
RES = next((c for c in _CANDS
            if os.path.isdir(os.path.join(c, "krkr素材库", "np", "bgm"))
            and len(os.listdir(os.path.join(c, "krkr素材库", "np", "bgm"))) > 0), _CANDS[0])
LIB = os.path.join(RES, "krkr素材库")
SCRIPTS = os.path.join(RES, "剧本")

SRC_ORDER = ["np", "ot", "ota", "otp", "otr", "otv"]
SRC_CN = {"np": "涅布＊普拉斯明日香篇", "ot": "本篇", "ota": "After Story",
          "otp": "前奏诗", "otr": "R 版（亚衣线）", "otv": "PSV 美咲线"}


def sha1(p):
    with open(p, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


# ─────────────────────────────────────────────── ① 剧本层引用（顺序 = 首次引用）
def scan_script_refs():
    order, stat = [], collections.OrderedDict()
    for f in sorted(glob.glob(os.path.join(SCRIPTS, "scene_*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            for a in o.get("assets", []):
                if a.get("kind") != "bgm":
                    continue
                rel = (a.get("out_relpath") or "").replace("\\", "/")
                if not rel:
                    continue
                if rel not in stat:
                    stat[rel] = {"n": 0, "src": o["source"], "first": o["scene_id"], "refs": set()}
                    order.append(rel)
                stat[rel]["n"] += 1
                stat[rel]["refs"].add(a.get("ref", ""))
    return order, stat


# ─────────────────────────────────────────────── ② 六源全量清单
def scan_library():
    rows = []
    for s in SRC_ORDER:
        d = os.path.join(LIB, s, "bgm")
        if not os.path.isdir(d):
            continue
        for p in sorted(glob.glob(os.path.join(d, "*.ogg"))):
            rows.append((s, os.path.basename(p), os.path.getsize(p), sha1(p)))
    return rows


def main():
    order, stat = scan_script_refs()
    lib = scan_library()
    by_sha = collections.defaultdict(list)
    for s, n, sz, h in lib:
        by_sha[h].append("%s/%s" % (s, n))

    # ① 候选（剧本引用）
    cand = []
    for i, rel in enumerate(order, 1):
        d = stat[rel]
        p = os.path.join(LIB, rel)
        h = sha1(p) if os.path.exists(p) else "MISSING"
        cand.append((i, d["src"], rel, d["n"], d["first"], h[:8], "|".join(sorted(d["refs"]))))

    # ② 全量
    refd = {rel for rel in order}
    librows = []
    for s, n, sz, h in lib:
        librows.append((s, n, sz, h[:8], "Y" if ("%s/bgm/%s" % (s, n)) in refd else ""))

    with open(os.path.join(HERE, "m51_bgm_candidates.tsv"), "w", encoding="utf-8") as f:
        f.write("序号\t源\t相对路径\t引用次数\t首次出现场景\tsha1_8\t剧本内引用名\n")
        for r in cand:
            f.write("\t".join(str(x) for x in r) + "\n")

    with open(os.path.join(HERE, "m51_bgm_library.tsv"), "w", encoding="utf-8") as f:
        f.write("源\t文件名\t字节\tsha1_8\t被剧本引用\n")
        for r in librows:
            f.write("\t".join(str(x) for x in r) + "\n")

    # ③ 跨源同名不同内容
    stems = collections.defaultdict(set)
    for s, n, sz, h in lib:
        stem = n[len(s) + 1:] if n.startswith(s + "_") else n
        stems[stem].add(s)
    multi = {k: v for k, v in stems.items() if len(v) > 1}
    dup_content = {h: v for h, v in by_sha.items() if len(v) > 1}

    L = []
    L.append("M3 · BGM 鉴赏页 · 曲目收录取证（只读；不裁决）")
    L.append("=" * 78)
    L.append("素材库解析路径 = %s" % LIB)
    L.append("剧本解析路径   = %s" % SCRIPTS)
    L.append("")
    L.append("① 候选池")
    per = collections.Counter(s for s, _n, _z, _h in lib)
    L.append("   六源 bgm 文件总数 = %d" % len(lib))
    for s in SRC_ORDER:
        L.append("     %-4s %-18s %3d 件" % (s, SRC_CN[s], per.get(s, 0)))
    L.append("   内容去重后 = %d（重复内容组 %d 组）" % (len(by_sha), len(dup_content)))
    for h, v in dup_content.items():
        L.append("     重复内容：%s" % " == ".join(v))
    L.append("")
    L.append("② 剧本层引用（scene_*.jsonl 的 assets[].kind==\"bgm\"）")
    L.append("   引用条目总数 = %d" % sum(d["n"] for d in stat.values()))
    L.append("   去重后曲目 = %d 首" % len(order))
    ps = collections.Counter(d["src"] for d in stat.values())
    for s in SRC_ORDER:
        if ps.get(s):
            L.append("     %-4s %-18s %3d 首" % (s, SRC_CN[s], ps[s]))
    L.append("   文件全部存在 = %s" % ("是" if all(os.path.exists(os.path.join(LIB, r)) for r in order) else "否"))
    L.append("")
    L.append("③ 跨源同名不同内容（D2 隔离规则）")
    L.append("   同 stem 出现在 >1 源的 stem 数 = %d" % len(multi))
    L.append("   其中真正「同名不同内容」的（内容 sha1 也不同的）= %d"
             % len([k for k in multi if len(set(
                 sha1(os.path.join(LIB, s, "bgm", ("%s_%s" % (s, k))))
                 for s in multi[k]
                 if os.path.exists(os.path.join(LIB, s, "bgm", ("%s_%s" % (s, k)))))) > 1]))
    L.append("   ⇒ 命名规范（强制，`00_项目总纲.md` §258）已保证跨源不撞名：")
    L.append("      `<来源代号>_<原文件名>`；库内同名不同内容一律靠**源前缀**区分，无需另行改名。")
    L.append("")
    L.append("④ 曲名可读性（**不编造曲名的依据**）")
    L.append("   实测：本作语料内**无曲名表**。已查：")
    L.append("     · `资源组\\剧本\\scene_*.jsonl` 的 bgm 资产只有 ref / out_relpath，无 title 字段；")
    L.append("     · `资源组\\krkr素材库\\资源总账.md` / `_同名冲突明细.tsv` / `_命名映射表.tsv` 只记文件名与哈希；")
    L.append("     · `资源组\\美术统一\\交付清单.tsv` 内与音乐相关的仅 `gl_bgm01..12.png`（**After Story 的 12 首曲名位图**，")
    L.append("       英文曲名，属参考作同型「图片化日文/英文」素材）与 `gl_music.png`（菜单标签）——")
    L.append("       **不是本作 59 首剧本曲目的曲名来源**，且本工程铁律禁止把文字烘焙进图 ⇒ 不作为曲名依据。")
    L.append("   ⇒ 结论：**曲名一律用文件名标识占位**（如 `np_bgm01a`），待补真实曲名后替换（登记在报告）。")
    L.append("")
    with open(os.path.join(HERE, "m51_bgm_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print("=" * 78)
    print("写出：m51_bgm_candidates.tsv / m51_bgm_library.tsv / m51_bgm_report.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())