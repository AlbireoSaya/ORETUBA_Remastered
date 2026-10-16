#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W7-3 · 作品层术语表全量交叉比对（可复跑、可审计）

读取四份作品层术语表（AS / PSV / R / 涅布），提取 (日文原词 → 中文译法) 对，
自动检出**同一原词在不同作品表中译法不一致**的条目，并按「是否属同一角色」分类。

另附 本篇 / 前奏诗 两表作为**旧写法证据**（非必比对对象，但 D3 的旧写法来源）。

输出：`子代理工作区\\ISSUE-20260918-06\\W7-3\\cross_compare.json`
"""
import json
import os
import re
from collections import OrderedDict, defaultdict

ROOT = r"E:\ZCode Workspace\Galgame"
TABLES = OrderedDict([
    ("AS",   r"工程\我们没有翅膀 After Story\作品skill\术语表.md"),
    ("PSV",  r"工程\我们没有翅膀PSV\作品skill\术语表.md"),
    ("R",    r"工程\我们没有翅膀R\作品skill\术语表.md"),
    ("涅布", r"工程\涅布＊普拉斯\作品skill\术语表.md"),
    ("本篇", r"工程\我们没有翅膀\作品skill\术语表.md"),
    ("前奏诗", r"工程\我们没有翅膀 前奏诗\作品skill\术语表.md"),
])
OUT = r"子代理工作区\ISSUE-20260918-06\W7-3\cross_compare.json"

# 非术语表头 / 非专名行（说明性、统计性）
SKIP_FIRST = {
    "日文原词", "项目", "事项", "原词日文", "#", "编号", "角色", "图片（SystemData.cpk）",
    "图片", "来源", "日文", "槽", "（翻译开工后填写）", "全作 362 条", "统计",
}
# 判断是否像日文原词（含假名 或 全角 或 汉字专名）
KANA = re.compile(r"[ぁ-んァ-ヶー]")
CJK = re.compile(r"[\u4e00-\u9fff]")


def looks_like_jp(s):
    s = s.strip()
    if not s or s in SKIP_FIRST:
        return False
    if s.startswith("（") or s.startswith("⚠"):
        return False
    if "→" in s or "＝" in s:
        return False
    if len(s) > 24:
        return False
    return bool(KANA.search(s) or CJK.search(s))


def extract(path):
    """返回 [(jp, cn, section, rowno)]，仅取 4 列以上且首列像日文原词的行。"""
    out = []
    section = ""
    for i, line in enumerate(open(os.path.join(ROOT, path), encoding="utf-8"), 1):
        s = line.strip()
        if s.startswith("#"):
            section = s.lstrip("# ").strip()
            continue
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        jp = cells[0]
        if not looks_like_jp(jp):
            continue
        # 中文译法列：4 列 → cells[1]；5 列（含读音）→ cells[2]；3 列（项目|裁决|说明）→ cells[1]
        if len(cells) >= 5:
            cn = cells[2]
        else:
            cn = cells[1]
        if not cn or cn.startswith("（待"):
            continue
        if "不译" in cn or cn.strip("*") in ("俺", "我", "余", "你"):
            continue  # R 表「标签不译」策略行 / 语气人称行，非专名译法
        # 首列含多原词（如 `御影クリヤ` / `栗山`）→ 拆分为多键
        keys = [k.strip().strip("`*").strip() for k in re.split(r"\s*[/／]\s*", jp)]
        for k in keys:
            if k and looks_like_jp(k):
                out.append((k, cn, section, i))
    return out


def norm_cn(cn):
    """归一化以便比较：去空白/加粗/书名号引号，全角→半角数字字母。"""
    s = cn.replace("*", "")
    for ch in "《》“”‘’「」『』　 ":
        s = s.replace(ch, "")
    s = s.replace("・", "·").replace("－", "-").replace("―", "-")
    s = re.sub(r"\s+", "", s)
    return s


def main():
    data = {k: extract(p) for k, p in TABLES.items()}

    # jp -> {table: [(cn, section, row)]}
    idx = defaultdict(lambda: defaultdict(list))
    for tbl, rows in data.items():
        for jp, cn, sec, row in rows:
            idx[jp][tbl].append((cn, sec, row))

    CORE = ("AS", "PSV", "R", "涅布")   # 任务要求比对的四份
    conflicts = []
    intra = []
    for jp, per in idx.items():
        present = {t: per[t] for t in CORE if t in per}
        # 同表内多译法 → 单列
        for t, lst in present.items():
            vs = {norm_cn(cn) for cn, _, _ in lst}
            if len(vs) > 1:
                intra.append({"jp": jp, "table": t,
                              "rows": [{"cn": cn, "section": sec, "row": row}
                                       for cn, sec, row in lst]})
        if len(present) < 2:
            continue
        variants = defaultdict(list)
        for t, lst in present.items():
            for cn, sec, row in lst:
                variants[norm_cn(cn)].append((t, cn, sec, row))
        if len(variants) > 1:
            # 附 本篇/前奏诗 的同词译法作证据
            ext = {}
            for t in ("本篇", "前奏诗"):
                if t in per:
                    ext[t] = [{"cn": cn, "section": sec, "row": row}
                              for cn, sec, row in per[t]]
            conflicts.append({
                "jp": jp,
                "variants": [
                    {"cn_norm": k, "occurs": [{"table": t, "cn": cn, "section": sec, "row": row}
                                              for t, cn, sec, row in v]}
                    for k, v in variants.items()
                ],
                "ext_evidence": ext,
            })

    conflicts.sort(key=lambda x: -len(x["variants"]))
    intra.sort(key=lambda x: x["jp"])
    rep = {
        "_meta": {
            "script": "cross_compare.py", "issue": "ISSUE-20260918-06 / W7-3",
            "note": "四份必比对表＝AS/PSV/R/涅布；本篇/前奏诗仅作旧写法证据。归一化后比较。",
        },
        "table_rows": {k: len(v) for k, v in data.items()},
        "conflict_count": len(conflicts),
        "intra_table_count": len(intra),
        "conflicts": conflicts,
        "intra_table": intra,
    }
    out = os.path.join(ROOT, OUT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("表行数：", rep["table_rows"])
    print("跨表不一致条目：", len(conflicts))
    for c in conflicts[:60]:
        v = " ｜ ".join(
            "%s=%s" % ("/".join(x["table"] for x in var["occurs"]), var["occurs"][0]["cn"])
            for var in c["variants"])
        print(f"  {c['jp']:<22} {v}")
    print("\n同表内多译法（需回修该表）：", len(intra))
    for c in intra:
        vs = " ｜ ".join("%s(第%s行)" % (r["cn"], r["row"]) for r in c["rows"])
        print(f"  [{c['table']}] {c['jp']:<20} {vs}")


if __name__ == "__main__":
    main()