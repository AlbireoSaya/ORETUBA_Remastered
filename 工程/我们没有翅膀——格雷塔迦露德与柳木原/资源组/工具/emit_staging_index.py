# -*- coding: utf-8 -*-
r"""
`emit_staging_index.py` · 逐行演出表**机读汇总**（ISSUE-20261001-14，任务书 §4.4）

产物（写本 checkout）
    `资源组\演出\_index.json` —— 各源行数 / `exact·inferred·unknown` 分布 / 场景与 skip 统计 /
    op 分布 / 文件 md5 与字节数 / **闸门结果**（由独立校验器 `verify_staging.py` 现场跑出来）

口径
    * 表内统计**只读六张 TSV**，不重复实现任何生成逻辑；
    * 闸门结果**不自己判**——`subprocess` 调 `verify_staging.py`（独立实现）并把它的
      `ALL_PASS` 与逐源结论原样落进 `gates`，避免"两处口径"。
    * 幂等：连跑两轮产物逐字节相同（`gates` 只收校验器的结构化结论：`ran / exit_code /
      all_pass / per_source / note`，不含 stdout 原文）。

复跑
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_staging_index.py"
    python -X utf8 "…/emit_staging_index.py" --check
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
OUT_DIR = os.path.join(RES, "演出")
SOURCES = ("ot", "ota", "otp", "otr", "otv", "np")
EXPECT = {"ot": 367, "ota": 172, "otp": 59, "otr": 55, "otv": 31, "np": 28}
CHECK = "--check" in sys.argv
VERIFY = os.path.join(HERE, "verify_staging.py")
INDEX = os.path.join(OUT_DIR, "_index.json")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def stats(src):
    p = os.path.join(OUT_DIR, "演出_%s.tsv" % src)
    raw = open(p, "rb").read()
    # sha256 一律算在 **LF 规范化**后的字节上：仓库版（blob）为 LF，而 `core.autocrlf=true`
    # 的检出（如主工作树）盘面为 CRLF、字节数恰好多出行数（见 `交接说明.md` C12）。
    # 不规范化会让同一提交在两处检出给出不同 sha256，台账就失去校验价值。
    norm = raw.replace(b"\r\n", b"\n")
    lines = norm.decode("utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    head = lines[0].split("\t")
    rows = [dict(zip(head, ln.split("\t"))) for ln in lines[1:]]
    ops = collections.Counter(r["op"] for r in rows)
    conf = collections.Counter(r["confidence"] for r in rows)
    scenes = collections.OrderedDict()
    for r in rows:
        scenes.setdefault(r["scene_id"], 0)
    skips = {r["scene_id"] for r in rows if r["op"] == "skip"}
    seq_max = max((int(r["seq"]) for r in rows if r["op"] != "skip"), default=0)
    return dict(
        file="演出_%s.tsv" % src,
        # ⚠️ 行尾：**规范形态是 LF**（仓库 blob）；`core.autocrlf=true` 的检出盘面为 CRLF、
        #    字节数恰好多出行数（见 `交接说明.md` C12）。
        #    **台账只记「与检出形态无关」的事实**——生成机当时的盘面尺寸/形态**不记**：
        #    它们随读者的 checkout 漂移，会让 `--check` 在 CRLF 检出必红（本批真发生过）。
        bytes_lf_normalized=len(norm),
        line_ending_canonical="LF（仓库 blob 形态；core.autocrlf=true 的检出盘面为 CRLF，见 交接说明.md C12）",
        sha256=sha256(norm),
        sha256_over="LF 规范化后的字节（与检出形态无关；见 交接说明.md C12）",
        header_ok=head == ["scene_id", "seq", "op", "target", "arg1", "arg2",
                           "arg3", "evidence", "confidence"],
        rows=len(rows),
        scenes=len(scenes),
        scenes_expected=EXPECT[src],
        skip_scenes=len(skips),
        skip_rows=ops.get("skip", 0),
        seq_max=seq_max,
        op_distribution=dict(sorted(ops.items())),
        confidence_distribution=dict(sorted(conf.items())),
    )


def run_gates():
    """调独立校验器，取它的结论（不自己判）。"""
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", VERIFY],
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
    except Exception as e:                                   # noqa: BLE001
        return dict(ran=False, error="%s: %s" % (type(e).__name__, e))
    out = r.stdout or ""
    per = {}
    for ln in out.splitlines():
        m = re.match(r"^\[([a-z]+)\] 行 (\d+) ｜ 场景 (\d+)", ln)
        if m:
            cur = m.group(1)
            per[cur] = dict(rows=int(m.group(2)), scenes=int(m.group(3)))
            continue
        m = re.match(r"^\[([a-z]+)\] !! 缺产物", ln)
        if m:
            per[m.group(1)] = dict(missing=True)
            continue
        if ln.strip().startswith("①②③④⑤⑦ 全绿"):
            per[cur]["verdict"] = "PASS"
            per[cur]["detail"] = ln.strip()
        elif ln.strip().startswith("!! 违规"):
            per[cur]["verdict"] = "FAIL"
            per[cur]["detail"] = ln.strip()
    m = re.search(r"^ALL_PASS = (True|False)$", out, re.M)
    return dict(ran=True, exit_code=r.returncode,
                all_pass=(m.group(1) == "True") if m else None,
                per_source=dict(sorted(per.items())),
                note="⑥ 实机抽查对照不在此列（须运行态，由编程组执行）")


def main():
    data = dict(
        module="逐行演出表 · 机读汇总",
        issue="ISSUE-20261001-14",
        generated_by="工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_staging_index.py",
        contract="编程组\\移交资源组_逐行演出数据任务书.md §三 / §五",
        seq_semantics="op 的 seq = 紧随其后第一个文本行的行号；其后无文本行 ⇒ 末行行号"
                      "（evidence 注 after_last_line）；首行之前 ⇒ 1（注 before_first_line）；skip 行 seq=0",
        sources={},
        gates=None,
        total={},
    )
    for src in SOURCES:
        data["sources"][src] = stats(src)
    data["gates"] = run_gates()
    data["total"] = dict(
        rows=sum(v["rows"] for v in data["sources"].values()),
        scenes=sum(v["scenes"] for v in data["sources"].values()),
        skip_scenes=sum(v["skip_scenes"] for v in data["sources"].values()),
    )
    body = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if CHECK:
        with io.open(INDEX, encoding="utf-8", newline="") as f:
            # 行尾规范化后比较（autocrlf 检出的盘面是 CRLF；见 交接说明 C12）
            if f.read().replace("\r\n", "\n") != body:
                raise SystemExit("!! 幂等失败：重算与磁盘 _index.json 不同")
        print("[_index.json] 幂等 PASS（行尾已规范化比较）")
    else:
        os.makedirs(OUT_DIR, exist_ok=True)
        with io.open(INDEX, "w", encoding="utf-8", newline="") as f:
            f.write(body)
        print("[_index.json] 写入 %s" % INDEX)

    for src in SOURCES:
        s = data["sources"][src]
        g = data["gates"]["per_source"].get(src, {}) if data["gates"].get("ran") else {}
        print("  %-4s 行 %-6d 场景 %-4d skip %d ｜ 闸门 %s"
              % (src, s["rows"], s["scenes"], s["skip_scenes"],
                 g.get("verdict", "?")))
    t = data["total"]
    print("  合计 行 %d ｜ 场景 %d ｜ skip 场景 %d" % (t["rows"], t["scenes"], t["skip_scenes"]))
    ga = data["gates"].get("all_pass") if data["gates"].get("ran") else None
    print("  ALL_PASS（来自 verify_staging.py）= %s" % ga)
    return 0 if ga else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
