#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
BGM 精确切换点生成器   (ISSUE-20260930-05 / greta-bgm-switch-dedup)
================================================================================
**只读** 源脚本 + 结构化剧本；产出 `交接编程组\BGM切换点.tsv`：
「**在第 <seq> 条台词之后 → 切换到第 <n> 首 BGM**」，供编程组按槽位精确切曲。

覆盖：
  - `otv`（PSV 美咲线 31 场景）——脚本是 Shift-JIS 纯文本 DSL，**BGM 与文本槽同处一个线性
    Task 序列**（`[TaskN]` 块按文件物理序执行；无分支跳转标签、无 End 之后不可达 BGM），
    故可精确到「第几条台词之后」。**含 `BgmStop` 静音点**。
  - `np`（涅布明日香篇 26/28 场景）——`.bs5` 为 BGI 字节码，**opcode 表不可枚举**，但其
    **常量池是一条「首次引用序」线性序列**（实参串先于函数名）⇒ 曲名常量在池中的位置
    天然落在前后两条台词之间，同样可给「第几条之后」。**上限**：同场同曲重复播放、
    纯 `_FadeBGM`/`_StopBGM` 淡出、数值参数不可见（如实标注为「首次引用位置」）。

**内置闸门（必须全绿，否则说明解析规则复刻有误）**
  1. 每场景解析出的**文本槽数**必须等于 `scene_*.jsonl` 的 `line_count`；
  2. `otv` 的 BGM 序列**去重后**必须与 `assets[].kind=="bgm"` 的集合一致；
  3. 每个 BGM 编号必须能在素材库找到对应文件（otv 用 `BGM.AWB\<n>` 派生的文件名，np 用曲名串）。

用法：python -X utf8 build_bgm_switch_points.py [--data-root <主工作区>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys

GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
NP_ARC = os.path.join("工程", "涅布＊普拉斯", "解包", "data01100.arc")
OTV_SCRIPT_DIR = os.path.join("工程", "我们没有翅膀PSV", "素材", "美咲线", "script")

TEXT_TASKTYPES = {"Message", "SceneJumpDialog", "MessageSwitch_Tag"}
BGM_RE = re.compile(r"^bgm(\d+)([a-b]?)$", re.I)   # 脚本里大小写混用（bgm05A / BGM86A / bgm11a）


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


def strip_comment(line: str) -> str:
    """引号感知地剥掉 `//` 行尾注释。"""
    out, inq = [], False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"':
            inq = not inq
        if not inq and c == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        out.append(c)
        i += 1
    return "".join(out)


def parse_otv(path: str):
    """→ (文本槽数, [事件]) ；事件 = dict(kind, seq, bgm, div, line)"""
    raw = open(path, "rb").read().decode("cp932", errors="replace")
    slots = 0
    events = []
    cur_type = None
    cur_fields = {}
    cur_line = 0

    def flush():
        nonlocal slots, cur_type, cur_fields, cur_line
        if cur_type in TEXT_TASKTYPES and (":Message" in cur_fields or ":Text" in cur_fields):
            slots += 1
        elif cur_type == "BgmPlay":
            events.append(dict(kind="切曲", seq=slots, bgm=int(cur_fields[":BGM"]),
                               div=cur_fields.get(":Div", ""), line=cur_line))
        elif cur_type == "BgmStop":
            events.append(dict(kind="停止", seq=slots, bgm=None,
                               div=cur_fields.get(":Div", ""), line=cur_line))
        cur_type, cur_fields, cur_line = None, {}, 0

    for ln, line in enumerate(raw.splitlines(), 1):
        s = strip_comment(line)
        m_task = re.match(r"\s*:Tasktype\s+\"([^\"]+)\"", s)
        if m_task:
            if cur_type is not None:
                flush()
            cur_type = m_task.group(1)
            cur_line = ln
            continue
        m = re.match(r"\s*(:[A-Za-z_]+)\s+(.*?)\s*$", s)
        if m and cur_type is not None:
            key, val = m.group(1), m.group(2).strip()
            if key == ":BGM":
                val = re.match(r"(\d+)", val).group(1)
            cur_fields[key] = val
    if cur_type is not None:
        flush()
    return slots, events


def scan_pool(path: str):
    """扫 .bs5 常量池 → 按偏移升序的 (offset, 字符串) 列表（NUL 结尾、cp932/ASCII）。"""
    data = open(path, "rb").read()
    out = []
    cur = bytearray()
    start = None
    for i, b in enumerate(data):
        # cp932 的**合法尾字节**含 0x40–0x7E 与 **0x80**–0xFC（0x80 极易漏掉，曾致串被截断）
        if 0x20 <= b <= 0x7E or 0x80 <= b <= 0xFC:
            if start is None:
                start = i
            cur.append(b)
        else:
            if start is not None and len(cur) >= 1:
                try:
                    out.append((start, cur.decode("cp932")))
                except UnicodeDecodeError:
                    pass
            cur, start = bytearray(), None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    a = ap.parse_args()
    data = find_main_workspace(a.data_root)
    res = os.path.join(data, REL_RES)
    here = os.path.dirname(os.path.abspath(__file__))
    out = assert_in_checkout(os.path.join(here, "..", "交接编程组"))
    os.makedirs(out, exist_ok=True)

    scenes = collections.defaultdict(dict)
    for s in ("otv", "np"):
        for line in open(os.path.join(res, "剧本", "scene_%s.jsonl" % s), encoding="utf-8"):
            o = json.loads(line)
            scenes[s][o["script"]] = o

    # **统一名映射**（`BGM统一清单.tsv`：源文件 → 统一名；被替代件亦指向其统一件）
    uni = {}
    # 清单由 build_bgm_unified.py 写在本 checkout（产物侧）；主工作区可能还没有 → 两处都找
    up = next((x for x in (os.path.join(here, "..", "BGM统一清单.tsv"),
                           os.path.join(res, "BGM统一清单.tsv")) if os.path.isfile(x)), "")
    if up:
        for r in csv.DictReader(open(up, encoding="utf-8"), delimiter="\t"):
            if r["处置"].startswith("保留"):
                uni[(r["来源"], r["原文件"])] = r["统一名"]
            else:
                uni[(r["来源"], r["被替代件"])] = r["统一名"]

    def uni_name(src, num):
        """按 (源, 编号) 取该曲在统一集里的文件名（np 的 a/b 档按实际存在者）。"""
        out = []
        cands = (("%s_bgm%03d.ogg" % (src, num),) if src == "otv"
                 else tuple("%s_bgm%02d%s.ogg" % (src, num, x) for x in ("a", "b", "")))
        for c in cands:
            if (src, c) in uni:
                out.append(uni[(src, c)])
        return sorted(set(out))

    # 曲名（ot/ota 有曲名位图；见 11_演出挂接说明.md）
    titles = {}
    tp = os.path.join(res, "交接编程组", "BGM曲名表.tsv")
    if os.path.isfile(tp):
        for r in csv.DictReader(open(tp, encoding="utf-8"), delimiter="\t"):
            titles[(r["源"], int(r["编号"]))] = r["曲名"]

    rows, problems = [], []
    stat = collections.Counter()

    # ---------------- otv ----------------
    for script, o in sorted(scenes["otv"].items()):
        p = os.path.join(data, OTV_SCRIPT_DIR, script)
        if not os.path.isfile(p):
            problems.append("otv 脚本缺失: %s" % script)
            continue
        slots, events = parse_otv(p)
        if slots != o["line_count"]:
            problems.append("otv 槽数不符 %s：脚本 %d / jsonl %d" % (script, slots, o["line_count"]))
        anchors = [x["out_relpath"].split("/")[-1] for x in o["assets"] if x["kind"] == "bgm"]
        got = []
        for e in events:
            if e["kind"] != "切曲":
                continue
            fn = re.search(r"bgm0*(\d+)", anchors[len(got)]) if len(got) < len(anchors) else None
            got.append(str(e["bgm"]))
        # 闸门：去重后的编号序列 == assets 里的编号序列
        want = [str(int(re.search(r"(\d+)", os.path.basename(x)).group(1))) for x in anchors]
        if [str(x) for x in dict.fromkeys(int(g) for g in got)] != [str(x) for x in dict.fromkeys(int(w) for w in want)]:
            problems.append("otv BGM 序列去重后不一致 %s：脚本 %s / assets %s" % (script, got, want))
        seen = set()
        for e in events:
            key = e["bgm"]
            dup = "" if key is None or key not in seen else "同场重复触发（assets[] 已去重）"
            if key is not None:
                seen.add(key)
            rows.append(dict(场景id=o["scene_id"], 源="otv", 事件=e["kind"],
                             在seq之后=e["seq"], bgm编号=("" if e["bgm"] is None else e["bgm"]),
                             统一名=(" ".join(uni_name("otv", e["bgm"])) if e["bgm"] is not None else ""),
                             曲名=titles.get(("otv", e["bgm"]), "") if e["bgm"] is not None else "",
                             淡入帧=e["div"], 物理行=e["line"],
                             依据="源脚本 [TaskN] 线性序（BgmPlay/BgmStop）", 备注=dup))
            stat[e["kind"]] += 1

    # ---------------- np ----------------
    for script, o in sorted(scenes["np"].items()):
        p = os.path.join(data, NP_ARC, script)
        if not os.path.isfile(p):
            problems.append("np 脚本缺失: %s" % script)
            continue
        pool = scan_pool(p)
        want = [l["jp"] for l in o["lines"] if l.get("jp")]
        idx = 0
        pending = []                              # [(编号, 是否带 AB 后缀, offset)]
        for off, s in pool:
            if idx < len(want) and s == want[idx]:
                idx += 1
                continue
            m = BGM_RE.match(s)
            if m:
                pending.append((m.group(1), bool(m.group(2)), off, idx))
        # A/B 成对（连续同号）合并为**一个切换点**；切换点取组内最小 idx
        i = 0
        while i < len(pending):
            num = pending[i][0]
            j = i
            while j + 1 < len(pending) and pending[j + 1][0] == num:
                j += 1
            grp = pending[i:j + 1]
            rows.append(dict(场景id=o["scene_id"], 源="np", 事件="切曲",
                             在seq之后=min(g[3] for g in grp),
                             bgm编号=num.lstrip("0") or "0",
                             统一名=" ".join(uni_name("np", int(num))),
                             曲名="", 淡入帧="", 物理行="常量池 0x%X" % grp[0][2],
                             依据=".bs5 常量池「首次引用序」（**推断**：非 opcode 级，未证实池序=执行序）",
                             备注=(("a/b 成对出现（**语义未证**）" if len(grp) >= 2 else "单曲") +
                                   ("；**场景开头**（本场首条台词之前）" if min(g[3] for g in grp) == 0 else ""))))
            i = j + 1
        if idx != len(want):
            problems.append("np 文本槽仅匹配 %d/%d：%s" % (idx, len(want), script))

    # 闸门：BGM 编号必须能在素材库找到文件
    all_names = set()
    for e in json.load(open(os.path.join(res, "krkr素材库", "资源总账.json"),
                            encoding="utf-8"))["entries"]:
        if e["kind"] == "bgm":
            all_names.add(e["filename"].lower())
    missing = []
    for r in rows:
        if r["源"] == "otv" and r["bgm编号"]:
            n = int(r["bgm编号"])
            cands = [f"otv_bgm{n:03d}.ogg", f"otv_bgm{n}.ogg"]
            if not any(c in all_names for c in cands):
                missing.append((r["场景id"], r["bgm编号"]))
        if r["源"] == "np" and r["bgm编号"]:
            n = int(r["bgm编号"])
            if not any(f"np_bgm{n:02d}{x}.ogg" in all_names for x in ("a", "b", "")):
                missing.append((r["场景id"], r["bgm编号"]))
    if problems or missing:
        for x in problems:
            print("   ✗", x)
        for x in missing:
            print("   ✗ 素材库缺文件:", x)
        raise SystemExit("[FATAL] 闸门未通过：problems=%d missing=%d" % (len(problems), len(missing)))

    with open(os.path.join(out, "BGM切换点.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["场景id", "源", "事件", "在seq之后", "bgm编号", "统一名", "曲名",
                                          "淡入帧", "物理行", "依据", "备注"], delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    summary = {
        "行数": len(rows),
        "按源": dict(collections.Counter(r["源"] for r in rows)),
        "按事件": dict(stat),
        "覆盖场景数": len({r["场景id"] for r in rows}),
        "闸门": "全绿（槽数相符 / otv 序列一致 / 素材库有文件）",
        "np 上限": "常量池为「首次引用序」：同场同曲重复播放、纯淡出、数值参数不可见",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
