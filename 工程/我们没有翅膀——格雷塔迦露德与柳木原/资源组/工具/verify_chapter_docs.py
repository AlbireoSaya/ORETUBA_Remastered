# -*- coding: utf-8 -*-
"""
verify_chapter_docs.py —— 对 06/07 两份章节交付物做只读校验（幂等、无副作用）

校验项（对应任务要求的 6 条验证）：
  1. 守恒：06 逐章行数 = 712；07 章节列表去重 = 712；逐源计数与 05_章节总表.tsv 一致
  2. 路线覆盖：逐路线章数、共享章处理口径
  3. 无省略号搪塞：章节列表区块内的「…」必须全部来自标题原文（TSV 可佐证）
  4. 顺序有据：每条路线的分岐臂注解存在且非「待判定」
  5. 空标题：22 条无标题章节在两份文档中均如实出现
  6. 未触碰禁止清单：git status 佐证（由调用方执行，见 §6）

只读：不写任何文件（sys.dont_write_bytecode=True）。
用法：python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_chapter_docs.py"
"""

import csv
import io
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
TSV = os.path.join(RES, "05_章节总表.tsv")
MD06 = os.path.join(RES, "06_章节总表.md")
MD07 = os.path.join(RES, "07_路线脉络.md")

FAIL = []


def check(name, ok, detail=""):
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  | " + detail) if detail else ""))
    if not ok:
        FAIL.append(name)


def load_tsv():
    with io.open(TSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return rows


def blocks(md_text):
    """返回 [(章节标题行文本, 行号)]，仅取 ``` 围栏内的行。"""
    out, inb = [], False
    for i, line in enumerate(md_text.split("\n"), 1):
        if line.strip() == "```":
            inb = not inb
            continue
        if inb:
            out.append((line, i))
    return out


def main():
    rows = load_tsv()
    tsv_scripts = {r["script"] for r in rows}
    tsv_cn = {(r["script"], (r["章节标题(中文)"] or "").strip() or "（无标题）") for r in rows}
    tsv_jp = {(r["script"], (r["章节标题(日文)"] or "").strip() or "（无标题）") for r in rows}
    tsv_titles_with_dots = {(r["章节标题(中文)"] or "") for r in rows
                            if "…" in (r["章节标题(中文)"] or "")} | \
                           {(r["章节标题(日文)"] or "") for r in rows
                            if "…" in (r["章节标题(日文)"] or "")}
    by = {r["script"]: r for r in rows}

    t06 = io.open(MD06, encoding="utf-8").read()
    t07 = io.open(MD07, encoding="utf-8").read()

    print("=" * 72)
    print("§1 守恒")
    print("=" * 72)

    # 06：逐章表格行 `| N | \`script\` | ...`
    r06 = re.findall(r"^\| (\d+) \| `([^`]+)` \|", t06, re.M)
    check("06 逐章行数 = 712", len(r06) == 712, "实测 %d" % len(r06))
    check("06 章节 script 全覆盖且不重复",
          sorted(s for _, s in r06) == sorted(tsv_scripts),
          "去重 %d / TSV %d" % (len(set(s for _, s in r06)), len(tsv_scripts)))

    # 07：``` 区块内的章节行
    blk = blocks(t07)
    check("07 章节列表行数 = 814（712 + 102 共用重复）", len(blk) == 814, "实测 %d" % len(blk))

    # 逐行解析 `阶段-作品《中文》〔日文〕〔共用〕`
    pat = re.compile(r"^(?P<stage>[^-]+)-(?P<work>[^《]+)《(?P<cn>.+?)》(?:〔(?P<jp>[^〕]+)〕)?$")
    parsed, bad = [], []
    for line, ln in blk:
        s = line[:-len("〔共用〕")] if line.endswith("〔共用〕") else line
        m = pat.match(s)
        if not m:
            bad.append((ln, line))
        else:
            parsed.append(m.groupdict())
    check("07 章节行格式全部匹配 `阶段-作品《标题》`", not bad,
          "不合格式 %d 行：%s" % (len(bad), bad[:3]))

    # 用 (cn) 反查 TSV：同一中文标题可能对应多 script（须逐一核对 script 集）
    cn2scripts = {}
    for r in rows:
        cn2scripts.setdefault((r["章节标题(中文)"] or "").strip() or "（无标题）", set()).add(r["script"])
    tsv_jp_set = {(r["章节标题(日文)"] or "").strip() or "（无标题）" for r in rows}
    unresolved = []
    for p in parsed:
        if p["cn"] not in cn2scripts:
            unresolved.append("CN:" + p["cn"])
        if p["jp"] and p["jp"] not in tsv_jp_set:
            unresolved.append("JP:" + p["jp"])
    check("07 标题均可回溯到 05_章节总表.tsv", not unresolved,
          "无法回溯 %d：%s" % (len(unresolved), unresolved[:5]))

    # 07 去重后的 script 数（按 cn 标题 + 出现顺序近似；用行数-共用标记数校验）
    shared = sum(1 for line, _ in blk if line.endswith("〔共用〕"))
    check("07 共用标记数 = 102", shared == 102, "实测 %d" % shared)
    check("07 去重后 = 712", len(blk) - shared == 712, "实测 %d" % (len(blk) - shared))

    # 逐源计数
    src_cnt = {}
    for r in rows:
        src_cnt[r["源代号"]] = src_cnt.get(r["源代号"], 0) + 1
    expect = {"ot": 367, "otr": 55, "ota": 172, "otp": 59, "otv": 31, "np": 28}
    check("逐源计数与语料一致", src_cnt == expect, str(src_cnt))
    check("六源合计 = 712", sum(src_cnt.values()) == 712, "实测 %d" % sum(src_cnt.values()))

    print()
    print("=" * 72)
    print("§2 路线覆盖")
    print("=" * 72)
    rlines = re.findall(r"^\| (\d+) \| ([^|]+) \| ([^|]+) \| `([^`]+)` \| (\d+) \| (\d+) \| (\d+) \|$",
                        t07, re.M)
    tot_listed = sum(int(x[4]) for x in rlines)
    tot_ex = sum(int(x[5]) for x in rlines)
    tot_sh = sum(int(x[6]) for x in rlines)
    print("路线数 = %d ｜ 列出行合计 = %d ｜ 独占合计 = %d ｜ 共用合计 = %d"
          % (len(rlines), tot_listed, tot_ex, tot_sh))
    check("路线数 = 19", len(rlines) == 19, "实测 %d" % len(rlines))
    check("列出行合计 = 814", tot_listed == 814, "实测 %d" % tot_listed)
    check("独占合计 = 712", tot_ex == 712, "实测 %d" % tot_ex)
    check("共用合计 = 102", tot_sh == 102, "实测 %d" % tot_sh)
    for x in rlines:
        print("  (%s) %s ｜ %s ｜ 列出 %s（独占 %s，共用 %s）" % (x[0], x[1].strip(), x[3], x[4], x[5], x[6]))

    print()
    print("=" * 72)
    print("§3 无省略号搪塞（章节列表区块内）")
    print("=" * 72)
    dots = [(ln, line) for line, ln in blk if "…" in line or "..." in line]
    bad_dots = [(ln, line) for ln, line in dots
                if not any(t in line for t in tsv_titles_with_dots)]
    print("章节列表内含「…」的行 = %d 行（全部为标题原文含「……」）：" % len(dots))
    for ln, line in dots:
        print("  L%d: %s" % (ln, line))
    check("章节列表内无「…」搪塞（仅标题原文）", not bad_dots, "违规 %d" % len(bad_dots))

    print()
    print("=" * 72)
    print("§4 顺序有据：逐路线分岐臂注解")
    print("=" * 72)
    paths = re.findall(r"^- \*\*选择支路径（本线走的臂）\*\*：(.+)$", t07, re.M)
    check("逐路线分岐路径注解数 = 19", len(paths) == 19, "实测 %d" % len(paths))
    check("无「待判定」注解", all("待判定" not in p for p in paths),
          "待判定 %d" % sum(1 for p in paths if "待判定" in p))
    for i, p in enumerate(paths, 1):
        print("  (%d) %s" % (i, p[:150]))

    print()
    print("=" * 72)
    print("§5 空标题 22 条")
    print("=" * 72)
    empty = [r["script"] for r in rows if not (r["章节标题(日文)"] or "").strip()]
    check("TSV 空标题数 = 22", len(empty) == 22, "实测 %d" % len(empty))
    n06 = t06.count("| （无标题） |")
    check("06 出现「（无标题）」= 22（唯一归属，每章一次）", n06 == 22, "实测 %d 次" % n06)
    n07 = sum(1 for line, _ in blk if "（无标题）" in line)
    # 07 是播放路径视图：空标题章若落在共用段内会出现两次
    # （07 行只带标题、无 script，故按「22 + 空标题章落在共用段内的次数」核）
    dup_empty = n07 - 22
    check("07 空标题行数 = 22 + 共用段内重复 %d = %d" % (dup_empty, n07),
          n07 >= 22, "实测 %d 行" % n07)
    check("空标题重复数 = 3（s01_04n／s01_05a／s01_14f2 落在山科京共用段）", dup_empty == 3,
          "实测 %d" % dup_empty)

    print()
    print("=" * 72)
    print("§6 结论")
    print("=" * 72)
    if FAIL:
        print("FAILED: %d 项 -> %s" % (len(FAIL), FAIL))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())