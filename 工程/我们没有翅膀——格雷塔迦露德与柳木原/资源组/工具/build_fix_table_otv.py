# -*- coding: utf-8 -*-
r"""W4b · 生成 `修正表_otv.tsv`（source=otv，PSV 美咲线）
====================================================================
判据（与 `修正\_README.md` §五 B1 教训一致）：
    「原文含 `「` / `」`  ⇒  译文须含 `“` / `”`」——**双向校验中「该出现却没出现」的一侧**。

本脚本对 PSV 美咲线**全库**（`工程\我们没有翅膀PSV\汉化\台词对照.json`，4,931 行 =
台词 4,904 + 梗概 27）重扫，列出全部命中并逐条生成修正条目。

输出（写）：
  `资源组\修正\修正表_otv.tsv`           11 列，与 `修正表_B1B3.tsv` 完全一致
  子代理工作区\ISSUE-20260918-06\W4b\W4b修正表自证.json

定位形态（otv 专属，见 `修正\_README.md` §二）：
  `file`    = `台词对照.json`（otv 取文语料文件；含 `脚本` + `行序` 复合键）
  `locator` = `script=<脚本名>&lineno=<行序>`（PSV 脚本无 offset/seq；
              `行序` 为**每脚本内** 1-based 序号，故必须带 `script=` 才能唯一定位）

只读：源 `工程\我们没有翅膀PSV\` 一律只读（`cp` 语义，不改一字节）。
用法：python -X utf8 build_fix_table_otv.py
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

WS = r"E:\ZCode Workspace\Galgame"
PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
FIX_DIR = os.path.join(PROJ, "资源组", "修正")
CORPUS = os.path.join(WS, "工程", "我们没有翅膀PSV", "汉化", "台词对照.json")
SCENE = os.path.join(PROJ, "资源组", "剧本", "scene_otv.jsonl")
OUT_DIR = os.path.join(WS, "子代理工作区", "ISSUE-20260918-06", "W4b")

CORPUS_NAME = "台词对照.json"
COLS = ["source", "file", "locator", "kind", "field", "old_text", "new_text",
        "fix_type", "method", "evidence", "confidence"]


def log(*a):
    print(*a, flush=True)


def has_jp_quote(s):
    return ("「" in s) or ("」" in s)


def has_cn_quote(s):
    return ("“" in s) or ("”" in s)


def main():
    t0 = time.time()
    rows = json.load(open(CORPUS, encoding="utf-8"))
    log("语料：%s（%d 行）" % (CORPUS, len(rows)))

    hits = []
    for r in rows:
        jp = r.get("日文") or ""
        cn = r.get("中文") or ""
        if has_jp_quote(jp) and not has_cn_quote(cn):
            hits.append(r)
    log("全库重扫：日文含「/」而译文无“/”者 = %d 条" % len(hits))

    # 交叉复核：scene_otv.jsonl 是否一致（只读）
    scene_hits = []
    n_scene_lines = 0
    if os.path.isfile(SCENE):
        for line in open(SCENE, encoding="utf-8"):
            o = json.loads(line)
            for l in o["lines"]:
                n_scene_lines += 1
                if has_jp_quote(l.get("jp") or "") and not has_cn_quote(l.get("cn") or ""):
                    scene_hits.append((o["script"], l["lineno"]))
        log("交叉复核 scene_otv.jsonl：%d 行，命中 %d 条 %s"
            % (n_scene_lines, len(scene_hits), scene_hits))

    # 生成 TSV
    os.makedirs(FIX_DIR, exist_ok=True)
    tpath = os.path.join(FIX_DIR, "修正表_otv.tsv")
    written = []
    with open(tpath, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(COLS) + "\n")
        for r in hits:
            script = r.get("脚本")
            lineno = r.get("行序")
            jp = r.get("日文") or ""
            old = r.get("中文") or ""
            new = "“" + old + "”"
            kind = "dialogue" if (r.get("类别") == "台词") else "other"
            rec = {
                "source": "otv",
                "file": CORPUS_NAME,
                "locator": "script=%s&lineno=%s" % (script, lineno),
                "kind": kind,
                "field": "cn",
                "old_text": old,
                "new_text": new,
                "fix_type": "quote_add",
                "method": "programmatic",
                "evidence": ("JP含「」、CN无任何引号（整行引语）；"
                             "PSV 美咲线全库重扫 4,931 行（台词 4,904 + 梗概 27）仅此 1 例；"
                             "判据=「原文含「/」⇒译文须含“/”」（修正层 §五 B1 双向校验）"),
                "confidence": "high",
            }
            f.write("\t".join(rec[c] for c in COLS) + "\n")
            written.append(rec)
            log("  写入：%s %s | %s -> %s" % (script, rec["locator"], old, new))

    # 逐字符断言 old_text == 源语料 中文
    src_by_key = {(r.get("脚本"), r.get("行序")): (r.get("中文") or "") for r in rows}
    assert all(src_by_key[(rec["locator"].split("=")[1].split("&")[0],
                           int(rec["locator"].split("=")[2]))] == rec["old_text"]
               for rec in written), "old_text 与源语料不符"
    log("断言：old_text 逐字符等于源语料 中文 —— 通过")

    # 自证
    os.makedirs(OUT_DIR, exist_ok=True)
    sc = {
        "module": "W4b 修正表_otv",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "corpus": CORPUS,
        "corpus_rows": len(rows),
        "corpus_categories": {c: sum(1 for r in rows if r.get("类别") == c)
                              for c in sorted({r.get("类别") for r in rows})},
        "criterion": "jp 含 「/」 且 cn 不含 “/”",
        "violations": len(hits),
        "scene_otv_lines": n_scene_lines,
        "scene_otv_hits": scene_hits,
        "table": tpath,
        "rows": written,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    with open(os.path.join(OUT_DIR, "W4b修正表自证.json"), "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=1)
    log("表：%s（%d 条 + 表头）" % (tpath, len(written)))
    log("自证：%s" % os.path.join(OUT_DIR, "W4b修正表自证.json"))


if __name__ == "__main__":
    main()