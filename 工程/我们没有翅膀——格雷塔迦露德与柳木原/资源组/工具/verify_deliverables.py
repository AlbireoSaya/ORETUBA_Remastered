# -*- coding: utf-8 -*-
r"""
verify_deliverables.py —— ISSUE-20260929-12 只读验收器（不写任何文件）

断言：
  ① 主表 剧本\章节简介.tsv：1253 数据行；译文状态==需新译 为 0；空 简介cn 仅两条空占位（并列出）。
  ② 回填后同一重复组内 简介cn 完全一致。
  ③ 原文换行位置 列存在；非空数 == 61 条待译对应的重复组所覆盖的行数（107）；非空行集合恰为该 61 组。
  ④ 片尾\片尾清单.tsv：148 数据行；图 141 + 视频 7 守恒；且**逐件实算 148/148**——
     每个交付件的磁盘 字节数 与 md5 必须与清单 `字节`/`md5` 列一致（图 = `_src\r_staff\*`；视频 = `_src\psv_ed\*`）。
  ⑤ 剧本\简介\_待入表汇总.tsv：行数与去重自洽（原词唯一、序号连续、列数一致、出处 id 可解析）。
  ⑥ --neg-selftest：内存内打坏某重复组一行 简介cn ⇒ 断言② 必 FAIL；
     内存内打坏片尾清单某行 md5 ⇒ 断言④ 必 FAIL；两者还原 ⇒ ALL_PASS。

运行：
  export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
  python -X utf8 "资源组/工具/verify_deliverables.py"
  python -X utf8 "资源组/工具/verify_deliverables.py" --neg-selftest
"""
import os
import re
import sys
import csv
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
RESGROUP = os.path.dirname(HERE)

P_MASTER  = os.path.join(RESGROUP, "剧本", "章节简介.tsv")
P_GAP     = os.path.join(RESGROUP, "剧本", "简介", "_translate_gap.tsv")
P_ENDLIST = os.path.join(RESGROUP, "片尾", "片尾清单.tsv")
P_RUBIAO  = os.path.join(RESGROUP, "剧本", "简介", "_待入表汇总.tsv")

BS = chr(92)
NL_MARKER = "换行位置未逐条登记"

fails = []
def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)

def read_tsv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return [r for r in csv.reader(f, delimiter="\t")]

def fingerprint(text):
    t = text.replace(BS + "n", "")
    t = "".join(ch for ch in t if not ch.isspace())
    t = t.replace(chr(0x301C), chr(0xFF5E))
    return t

def group_consistency_failures(hdr, rows):
    """返回「同一重复组内 简介cn 不一致」的组列表。"""
    ix = {c: i for i, c in enumerate(hdr)}
    per = {}
    for r in rows:
        per.setdefault(r[ix["重复组id"]], set()).add(r[ix["简介cn"]])
    return sorted(g for g, s in per.items() if len(s) > 1)

def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def endlist_artifact_failures(hdr, rows, src_root):
    """逐件核账（断言④）：每个交付件的 磁盘字节数 / md5 必须与清单 `字节`/`md5` 一致。
    图 → `src_root\\r_staff\\<交付文件名>`；视频 → `src_root\\psv_ed\\<交付文件名>`。
    返回不一致说明列表（空 = N/N 全过）。"""
    ix = {c: i for i, c in enumerate(hdr)}
    bad = []
    for r in rows:
        cat = r[ix["类别(图/视频)"]]
        sub = "r_staff" if cat == "图" else "psv_ed"
        fn = r[ix["交付文件名"]]
        p = os.path.join(src_root, sub, fn)
        if not os.path.isfile(p):
            bad.append("缺件 %s" % p)
            continue
        sz = os.path.getsize(p)
        if str(sz) != r[ix["字节"]]:
            bad.append("%s 字节：清单=%s 磁盘=%d" % (fn, r[ix["字节"]], sz))
        md = md5_file(p)
        if md != r[ix["md5"]]:
            bad.append("%s md5：清单=%s 磁盘=%s" % (fn, r[ix["md5"]], md))
    return bad

def main():
    # ---------------- ① 主表
    print("[① 主表]")
    master = read_tsv(P_MASTER)
    hdr, rows = master[0], master[1:]
    ix = {c: i for i, c in enumerate(hdr)}
    check(len(rows) == 1253, "主表数据行 == 1253（实测 %d）" % len(rows))
    check("原文换行位置" in hdr, "新增列 原文换行位置 存在")
    need = [r for r in rows if r[ix["译文状态"]] == "需新译"]
    check(len(need) == 0, "译文状态==需新译 的行数 == 0（实测 %d）" % len(need))
    new = [r for r in rows if r[ix["译文来源"]].startswith("新译(2026-09-29")]
    check(len(new) == 107,
          "译文来源==新译(2026-09-29 · Txxx) 的行数 == 107（实测 %d）—— 即本次仅回填这 107 行" % len(new))
    st = {}
    for r in rows:
        st[r[ix["译文状态"]]] = st.get(r[ix["译文状态"]], 0) + 1
    check(set(st) <= {"已有(ot原译)", "已有(otv库内)", "已有(新译)"},
          "译文状态取值域 ⊆ 三值（实测 %s）" % st)
    empty = [r for r in rows if r[ix["简介cn"]] == ""]
    empty_ids = sorted((r[ix["来源"]], r[ix["脚本"]]) for r in empty)
    expect_ids = [("otv", "M09_02"), ("otv", "S01_01")]
    check(len(empty) == 2 and empty_ids == expect_ids,
          "空 简介cn 仅 2 条空占位（otv/S01_01、otv/M09_02）；实测 %d 条：%s"
          % (len(empty), empty_ids))
    for r in empty:
        print("        空行：序号%s %s/%s 重复组=%s 备注=%s"
              % (r[ix["序号"]], r[ix["来源"]], r[ix["脚本"]],
                 r[ix["重复组id"]], r[ix["备注"]]))

    # ---------------- ② 重复组一致性
    print("[② 重复组 简介cn 一致性]")
    bad = group_consistency_failures(hdr, rows)
    check(len(bad) == 0, "同一重复组内 简介cn 完全一致（不一致组 %d：%s）" % (len(bad), bad[:5]))

    # ---------------- ③ 原文换行位置
    print("[③ 原文换行位置]")
    gap = read_tsv(P_GAP)
    gi = {c: i for i, c in enumerate(gap[0])}
    fp2group = {}
    for r in rows:
        fp2group.setdefault(fingerprint(r[ix["简介jp"]]), set()).add(r[ix["重复组id"]])
    mapped_groups = set()
    tid2g = {}
    for r in gap[1:]:
        tid = r[gi["待译id"]]
        gs = sorted(fp2group.get(fingerprint(r[gi["简介jp"]]), []))
        check(len(gs) == 1, "缺口 %s 指纹唯一匹配重复组（%s）" % (tid, gs))
        if len(gs) == 1:
            mapped_groups.add(gs[0])
            tid2g[tid] = gs[0]
    check(len(mapped_groups) == 61, "缺口映射到 61 个不同重复组（实测 %d）" % len(mapped_groups))
    covered = [r for r in rows if r[ix["重复组id"]] in mapped_groups]
    nonempty = [r for r in rows if r[ix["原文换行位置"]] != ""]
    check(len(nonempty) == len(covered),
          "原文换行位置 非空数(%d) == 61 组所覆盖行数(%d)" % (len(nonempty), len(covered)))
    check(set(id(r) for r in nonempty) == set(id(r) for r in covered),
          "原文换行位置 非空行集合 == 61 组行集合")
    # 每组唯一值
    per_g = {}
    for r in covered:
        per_g.setdefault(r[ix["重复组id"]], set()).add(r[ix["原文换行位置"]])
    multi = sorted(g for g, s in per_g.items() if len(s) > 1)
    check(len(multi) == 0, "每个回填组内 原文换行位置 唯一（异常 %s）" % multi[:5])
    # 空值行必带备注标记
    marked = [r for r in rows if r[ix["原文换行位置"]] == "" and NL_MARKER in r[ix["备注"]]]
    check(len(marked) == 1253 - len(covered),
          "空 原文换行位置 的行均带备注「%s」（%d/%d）"
          % (NL_MARKER, len(marked), 1253 - len(covered)))
    print("        回填组 %d 个 / 覆盖行 %d" % (len(mapped_groups), len(covered)))

    # ---------------- ④ 片尾清单
    print("[④ 片尾清单]")
    el = read_tsv(P_ENDLIST)
    eh, er = el[0], el[1:]
    check(len(er) == 148, "片尾清单数据行 == 148（实测 %d）" % len(er))
    cats = {}
    for r in er:
        cats[r[1]] = cats.get(r[1], 0) + 1
    check(cats.get("图") == 141 and cats.get("视频") == 7,
          "类别守恒：图 141 + 视频 7（实测 %s）" % cats)
    widths = set(len(r) for r in er)
    check(widths == {16}, "逐行列数一致 == 16（实测 %s）" % widths)
    seqs = [int(r[0]) for r in er]
    check(seqs == list(range(1, 149)), "序号 1..148 连续")
    srcs = {}
    for r in er:
        srcs[r[4]] = srcs.get(r[4], 0) + 1
    check(srcs.get("otr") == 141 and srcs.get("otv") == 7,
          "来源守恒：otr 141 + otv 7（实测 %s）" % srcs)
    # 逐件实算 148/148：磁盘 字节数 / md5 必须与清单一致
    src_root = os.path.join(RESGROUP, "片尾", "_src")
    art_bad = endlist_artifact_failures(eh, er, src_root)
    check(len(art_bad) == 0,
          "逐件实算：%d/%d 交付件 字节+md5 与磁盘一致（不一致 %d%s）"
          % (len(er) - len(art_bad), len(er), len(art_bad),
             ("：" + "；".join(art_bad[:3])) if art_bad else ""))
    print("        逐件实算源：%s（图 r_staff / 视频 psv_ed）" % src_root)

    # ---------------- ⑤ 待入表汇总
    print("[⑤ 待入表汇总]")
    rb = read_tsv(P_RUBIAO)
    rh, rr = rb[0], rb[1:]
    terms = [r[1] for r in rr]
    check(len(terms) == len(set(terms)), "日文原词 无重复（%d 条，去重后 %d）"
          % (len(terms), len(set(terms))))
    check([int(r[0]) for r in rr] == list(range(1, len(rr) + 1)), "序号 1..N 连续")
    check(set(len(r) for r in rr) == {7}, "逐行列数一致 == 7")
    ok_ids = True
    for r in rr:
        if r[3] != "—" and not re.match(r"^T\d{3}$", r[3]):
            ok_ids = False
    check(ok_ids, "首次出处(待译id) 格式合法")
    layers = set(r[5] for r in rr)
    check(layers <= {"通用", "作品"}, "建议归层取值域 ⊆ {通用,作品}（实测 %s）" % layers)
    print("        待入表汇总 %d 条（通用 %d / 作品 %d）"
          % (len(rr), sum(1 for r in rr if r[5] == "通用"),
             sum(1 for r in rr if r[5] == "作品")))

    # ---------------- 结论
    print("")
    if fails:
        print("RESULT: FAIL  (%d 项未通过)" % len(fails))
        return 1
    print("RESULT: ALL_PASS")
    return 0

def neg_selftest():
    """负对照：内存内打坏某重复组一行 简介cn ⇒ 断言② 必报 FAIL；
    内存内打坏片尾清单某行 md5 ⇒ 断言④ 必报 FAIL；还原 ⇒ PASS。"""
    print("[⑥ 负对照 · 断言② ]")
    ok = True
    master = read_tsv(P_MASTER)
    hdr, rows = master[0], master[1:]
    ix = {c: i for i, c in enumerate(hdr)}
    check(len(group_consistency_failures(hdr, rows)) == 0, "基线：重复组 简介cn 一致")
    # 找第一个 size>=2 的重复组
    per = {}
    for r in rows:
        per.setdefault(r[ix["重复组id"]], []).append(r)
    target = None
    for g, rs in per.items():
        if len(rs) >= 2:
            target = (g, rs[0], rs[1]); break
    if target is None:
        print("  FAIL  找不到 size>=2 的重复组，无法负对照"); return 1
    g, r0, r1 = target
    orig = r0[ix["简介cn"]]
    r0[ix["简介cn"]] = orig + "★打坏★"
    bad = group_consistency_failures(hdr, rows)
    check(g in bad, "打坏重复组 %s 的一行后，断言② 命中该组（%s）" % (g, bad))
    ok = ok and (g in bad)
    r0[ix["简介cn"]] = orig
    check(len(group_consistency_failures(hdr, rows)) == 0, "还原后 断言② 恢复 PASS")

    # ── 负对照 · 断言④ 片尾清单逐件 md5 ──
    print("[⑥ 负对照 · 断言④ 片尾清单逐件 md5]")
    el = read_tsv(P_ENDLIST)
    eh, er = el[0], el[1:]
    eix = {c: i for i, c in enumerate(eh)}
    src_root = os.path.join(RESGROUP, "片尾", "_src")
    check(len(endlist_artifact_failures(eh, er, src_root)) == 0,
          "基线：%d/%d 交付件 字节+md5 与磁盘一致" % (len(er), len(er)))
    row = er[0]
    orig_md5 = row[eix["md5"]]
    row[eix["md5"]] = "0" * 32
    bad4 = endlist_artifact_failures(eh, er, src_root)
    check(bool(bad4), "打坏第 1 行 md5（%s）后，断言④ 必命中（%s）"
          % (row[eix["交付文件名"]], (bad4[:1] or ["<未命中，即变异未被检出>"])[0]))
    ok = ok and bool(bad4)
    row[eix["md5"]] = orig_md5
    check(len(endlist_artifact_failures(eh, er, src_root)) == 0, "还原后 断言④ 恢复 PASS")

    print("")
    print("RESULT: " + ("NEG_SELFTEST_PASS" if ok else "NEG_SELFTEST_FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    if "--neg-selftest" in sys.argv:
        sys.exit(neg_selftest())
    sys.exit(main())
