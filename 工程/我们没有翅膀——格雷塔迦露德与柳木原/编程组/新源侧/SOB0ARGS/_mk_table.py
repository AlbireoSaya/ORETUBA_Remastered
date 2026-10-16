# -*- coding: utf-8 -*-
"""只读：把 位置token映射.tsv 渲染为 markdown 表（供 说明.md 粘贴）。"""
import csv, io

rows = list(csv.DictReader(io.open("位置token映射.tsv", encoding="utf-8"), delimiter="\t"))
out = []
out.append("| token | 出现数 | 档位 | map_cx(1280) | map_x(1920) | 粒度 | 严口径 命中/总数 | 命中率 | 宽口径 命中/总数 | 严反例 | 宽反例 | 备注 |")
out.append("| --- | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |")
for r in rows:
    tok = "`%s`" % r["token"]
    out.append("| %s | %s | %s | %s | %s | %s | %s/%s | %s | %s/%s | %s | %s | %s |" % (
        tok, r["count_all"], r["tier"], r["map_cx1280"] or "—", r["map_x1920"] or "—",
        r["granularity"], r["strict_hit"], r["strict_n"], r["strict_rate"] or "—",
        r["loose_hit"], r["loose_n"], r["ce_strict_n"], r["ce_loose_n"],
        (r["note"] or "").replace("|", "/")))
io.open("_table.md", "w", encoding="utf-8", newline="").write("\n".join(out) + "\n")
print("wrote _table.md  rows=%d" % len(rows))
