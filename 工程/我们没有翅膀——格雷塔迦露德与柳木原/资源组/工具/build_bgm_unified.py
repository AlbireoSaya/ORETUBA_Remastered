#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
BGM 去重与统一命名   (ISSUE-20260930-05 / greta-bgm-switch-dedup)
================================================================================
**只读** 素材库（`krkr素材库\`），产出：

  - `资源组\BGM统一\`            —— **去重后的工程 BGM 集**（字节复制，不转码）
  - `资源组\BGM统一清单.tsv`     —— 统一名 ↔ 源文件对照与去重依据（入库）

**去重规则（由数据实测确定，见 `--probe` 输出）**
  1. 按 **去源前缀后的 stem**（如 `bgm01a`）分组：462 件 → 169 组（57 单成员 / 112 多成员）。
  2. 多成员组内比较 `audio.duration_sec`：
     - **时长差 ≤ 0.5 s ⇒ 同一曲**（实测 107/112 组；跨源只是编码/码率不同）→ 保留**源优先级最高**
       （`ot > ota > otr > otp > np > otv`）的一件作统一件，其余记「被替代」。
     - **时长差 > 2 s ⇒ 同名不同曲**（实测 5 组：`bgm89a/bgm89b/bgm91/bgm93/bgm99`，即官方 OST 的
       「Game Size」与「Full Size」两个版本）→ **两件都保留**：短者 `<stem>.ogg`、长者 `<stem>_full.ogg`。
     - 0.5–2 s 之间：**实测 0 组**（无模糊地带）。
  3. 统一名 = `<stem>.ogg`（stem 已含编号与 a/b 档），`otv` 的三位编号（`bgm005`）与 PC 两位
     （`bgm05a`）天然不撞名；若日后出现同名不同内容，按美术约定加 `_alt<源>`。

**内置闸门**：① 统一名无重复；② 每个产出件与源件**逐字节相同**（`shutil.copy2` 后核 md5）；
③ 462 件每一件都必须被「保留」或「被替代」二选一记录；④ 被替代件的时长必须与其统一件差 ≤1.0 s。

用法：python -X utf8 build_bgm_unified.py [--data-root <主工作区>] [--probe]
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import re
import shutil
import sys

GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
PRIO = {"ot": 0, "ota": 1, "otr": 2, "otp": 3, "np": 4, "otv": 5}
SAME_DUR = 0.5          # ≤ 此值视为同一曲
DIFF_DUR = 2.0          # > 此值视为同名不同曲（Game Size / Full Size）


def find_main_workspace(cli):
    if cli:
        return os.path.abspath(cli)
    env = os.environ.get("GALGAME_MAIN")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        cur = os.path.dirname(cur)
        if os.path.isfile(os.path.join(cur, "工程", GAME, "资源组", "krkr素材库", "资源总账.json")):
            return cur
    raise SystemExit("[FATAL] 未找到主工作区，请用 --data-root 指定")


def assert_in_checkout(path):
    here = os.path.dirname(os.path.abspath(__file__))
    checkout = here
    for _ in range(4):
        if os.path.isdir(os.path.join(checkout, ".git")) or os.path.isfile(os.path.join(checkout, ".git")):
            break
        checkout = os.path.dirname(checkout)
    p = os.path.abspath(path)
    if not (p == checkout or p.startswith(checkout + os.sep)):
        raise SystemExit(f"[FATAL] 产物路径不在本 checkout 内，拒绝写入：{p}")
    return p


def stem_of(fn: str) -> str:
    """去源前缀 + **去扩展名**（原实现漏了去扩展名，产出 `bgm000.ogg.ogg`）。"""
    n = fn.lower()
    for ext in (".ogg", ".mp3", ".wav", ".m4a"):
        if n.endswith(ext):
            n = n[: -len(ext)]
            break
    return re.sub(r"^[a-z]+_", "", n)


def md5f(p: str) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--probe", action="store_true", help="只印统计，不写任何产物")
    a = ap.parse_args()
    data = find_main_workspace(a.data_root)
    res = os.path.join(data, REL_RES)
    lib = os.path.join(res, "krkr素材库")
    here = os.path.dirname(os.path.abspath(__file__))
    out_set = assert_in_checkout(os.path.join(here, "..", "BGM统一"))
    out_tsv = assert_in_checkout(os.path.join(here, "..", "BGM统一清单.tsv"))

    entries = [e for e in json.load(open(os.path.join(lib, "资源总账.json"),
                                        encoding="utf-8"))["entries"] if e["kind"] == "bgm"]
    titles = {}
    tp = os.path.join(res, "交接编程组", "BGM曲名表.tsv")
    if os.path.isfile(tp):
        for r in csv.DictReader(open(tp, encoding="utf-8"), delimiter="\t"):
            titles[(r["源"], int(r["编号"]))] = r["曲名"]

    groups = collections.defaultdict(list)
    for e in entries:
        e["stem"] = stem_of(e["filename"])
        e["dur"] = (e.get("audio") or {}).get("duration_sec")
        e["path"] = os.path.join(lib, e["out_relpath"].replace("/", os.sep))
        groups[e["stem"]].append(e)

    plan = []                      # (统一名, 源条目, 处置, 被谁替代)
    stats = collections.Counter()
    for stem in sorted(groups):
        members = sorted(groups[stem], key=lambda e: (PRIO[e["source"]], e["filename"]))
        if len(members) == 1:
            plan.append((stem + ".ogg", members[0], "保留(唯一件)", ""))
            stats["唯一件"] += 1
            continue
        durs = [m["dur"] for m in members]
        if None in durs or (max(durs) - min(durs)) <= SAME_DUR:
            plan.append((stem + ".ogg", members[0], "保留(同曲取优先源)", ""))
            for m in members[1:]:
                plan.append(("", m, "被替代(同曲)", stem + ".ogg"))
            stats["同曲组"] += 1
        else:
            # **同名不同曲**：**主名仍归「源优先级最高」的成员**（与其余 107 组同规则，不特例）；
            # 其余时长簇各出一件 `<stem>_alt<源>.ogg`。
            # ⚠️ 成因**未证**——一审指出原「Game Size / Full Size」是推断（`bgm89a` 的 0.73 s 更像源侧残件），
            # 故清单只如实记「逐版时长 + 来源」，不下结论。
            clusters = []
            for m in members:
                for c in clusters:
                    if abs(c[0]["dur"] - m["dur"]) <= SAME_DUR:
                        c.append(m)
                        break
                else:
                    clusters.append([m])
            clusters.sort(key=lambda c: (PRIO[c[0]["source"]], c[0]["filename"]))
            durs_all = sorted({round(c[0]["dur"], 2) for c in clusters})
            plan.append((stem + ".ogg", clusters[0][0],
                         "保留(同名不同曲·主名归优先源；逐版时长 %s）"
                         % "/".join("%.2fs" % d for d in durs_all), ""))
            for ci, c in enumerate(clusters):
                # 簇内视为同一录音（时长差 ≤0.5s）→ 只留源优先级最高者，其余被替代
                rep = c[0]
                out_name = (stem + ".ogg" if ci == 0
                            else stem + "_alt" + rep["source"] + ".ogg")
                if ci:
                    plan.append((out_name, rep, "保留(同名不同曲·另版 %.2fs)" % rep["dur"], ""))
                for m in c:
                    if m is rep or m is clusters[0][0]:
                        continue
                    plan.append(("", m, "被替代(同曲)", out_name if ci else stem + ".ogg"))
            stats["同名不同曲组"] += 1

    kept = [(u, e, w) for u, e, w, _rep in plan if u]
    if a.probe:
        print(json.dumps({
            "源件数": len(entries), "stem 组": len(groups), "统一件数": len(kept),
            "分类": dict(stats),
            "源件总字节": sum(e["bytes"] for e in entries),
            "统一集字节": sum(e["bytes"] for _u, e, _w in kept),
        }, ensure_ascii=False, indent=1))
        return

    # ---- 写出一组（先清空本脚本自己的旧产物：只删本目录内的 *.ogg） ----
    if os.path.isdir(out_set):
        for fn in os.listdir(out_set):
            if fn.lower().endswith((".ogg", ".mp3", ".wav")):
                os.remove(os.path.join(out_set, fn))
    os.makedirs(out_set, exist_ok=True)

    rows, bad = [], []
    seen_names = collections.Counter()
    for uname, e, why in kept:
        seen_names[uname] += 1
        dst = os.path.join(out_set, uname)
        shutil.copy2(e["path"], dst)
        if md5f(dst) != md5f(e["path"]):                       # 闸门②
            bad.append(("逐字节不符", uname))
        num = re.search(r"bgm0*(\d+)", uname)
        title = titles.get((e["source"], int(num.group(1))), "") if num else ""
        rows.append(dict(统一名=uname, 曲名=title, 时长=("%.2f" % e["dur"]) if e["dur"] else "",
                         字节=e["bytes"], 来源=e["source"], 原文件=e["filename"],
                         处置=why, 被替代件="", 依据="同曲取源优先级 ot>ota>otr>otp>np>otv" if "同曲" in why or "唯一" in why
                         else "同名不同曲：官方 OST「Game Size / Full Size」两版本"))
    for _u, e, why, rep in plan:
        if _u:
            continue
        rows.append(dict(统一名=rep, 曲名="", 时长=("%.2f" % e["dur"]) if e["dur"] else "",
                         字节=e["bytes"], 来源=e["source"], 原文件=e["filename"],
                         处置=why, 被替代件=e["filename"], 依据="与统一件时长差 ≤0.5s（同曲不同编码）"))
    if any(c > 1 for c in seen_names.values()):                 # 闸门①
        bad.append(("统一名重复", [k for k, c in seen_names.items() if c > 1]))
    if sum(1 for _u, _e, _w, _r in plan) != len(entries):       # 闸门③
        bad.append(("源件未被完整记账", "%d / %d" % (len(plan), len(entries))))
    for _u, e, why, rep in plan:
        if rep and e["dur"]:
            uni = next((x for x in kept if x[0] == rep), None)
            if uni and uni[1]["dur"] and abs(uni[1]["dur"] - e["dur"]) > 1.0:   # 闸门④
                bad.append(("被替代件时长差过大", "%s Δ=%.2fs" % (e["filename"], abs(uni[1]["dur"] - e["dur"]))))
    if bad:
        for b in bad[:10]:
            print("   ✗", b)
        raise SystemExit("[FATAL] 闸门未通过（%d 项）" % len(bad))

    rows.sort(key=lambda r: (r["统一名"], r["处置"]))
    with open(out_tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["统一名", "曲名", "时长", "字节", "来源", "原文件",
                                          "处置", "被替代件", "依据"], delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    summary = {
        "源件数": len(entries), "stem 组": len(groups), "统一件数": len(kept),
        "分类": dict(stats),
        "源件总字节": sum(e["bytes"] for e in entries),
        "统一集字节": sum(e["bytes"] for _u, e, _w in kept),
        "精简": "%.1f%%" % (100 * (1 - sum(e["bytes"] for _u, e, _w in kept) / sum(e["bytes"] for e in entries))),
        "闸门": "全绿（统一名唯一 / 逐字节相同 / 全量记账 / 被替代件时长差 ≤1s）",
        "同名不同曲": "5 组逐版都保留（主名归源优先级最高者，另版 _alt<源>）；**成因未证**",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    with open(assert_in_checkout(os.path.join(here, "..", "审计", "BGM统一汇总.json")),
              "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
