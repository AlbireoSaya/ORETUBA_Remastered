# -*- coding: utf-8 -*-
r"""
assemble_deliverables.py —— ISSUE-20260929-12 最终组装（任务 A / B / C）

一条命令完成：
  A. 把三段新译文（_cn_T001-T061）按「归一化指纹 → 重复组」并入主表 剧本\章节简介.tsv，
     新增 原文换行位置 列；回填后 需新译 == 0，空 简介cn 仅两条空占位。
  B. 合并 片尾\_raw_r_sr.tsv（图 141）+ 片尾\_raw_psv_ed.tsv（视频 7）= 片尾\片尾清单.tsv（148 行）。
     并在 片尾\片尾说明.md 顶部追加「§〇、片尾清单.tsv（合并清单）」小节。
  C. 汇总三段译文的「待入表条目」= 剧本\简介\_待入表汇总.tsv（只汇总、不裁决、不改任何术语表）。

特性：
  * 幂等：重复执行产物字节不变。
  * 硬校验：一切输出必须落在本工作树的 资源组\ 内（本工程有 os.path.join(main,'..') 逃逸前例）。
  * 只读源：_raw_*、_cn_T*.tsv、_translate_gap.tsv、_raw_r_sr.tsv、_raw_psv_ed.tsv 一律不写。

运行：
  export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
  python -X utf8 "资源组/工具/assemble_deliverables.py"
"""
import os
import re
import sys
import csv
import hashlib

# ---------------------------------------------------------------- 路径与硬校验
HERE = os.path.dirname(os.path.abspath(__file__))          # <WT>/资源组/工具
RESGROUP = os.path.dirname(HERE)                            # <WT>/资源组
WT = os.path.dirname(RESGROUP)                              # <WT>

def guard_write(path):
    """输出路径硬校验：必须落在 资源组\\ 内，且 资源组\\ 必须位于 临时\\ 工作树内。"""
    rp = os.path.realpath(os.path.abspath(path))
    rg = os.path.realpath(RESGROUP)
    if not (rp == rg or rp.startswith(rg + os.sep)):
        raise SystemExit("[FATAL] 输出越界（不在工作树 资源组\\ 内）：%s" % rp)
    parts = os.path.realpath(WT).split(os.sep)
    if "临时" not in parts:
        raise SystemExit("[FATAL] 资源组\\ 不在 临时\\ 工作树内：%s" % rg)
    return rp

P_MASTER   = os.path.join(RESGROUP, "剧本", "章节简介.tsv")
P_GAP      = os.path.join(RESGROUP, "剧本", "简介", "_translate_gap.tsv")
P_CN       = [os.path.join(RESGROUP, "剧本", "简介", "_cn_T001-T021.tsv"),
              os.path.join(RESGROUP, "剧本", "简介", "_cn_T022-T041.tsv"),
              os.path.join(RESGROUP, "剧本", "简介", "_cn_T042-T061.tsv")]
P_SR       = os.path.join(RESGROUP, "片尾", "_raw_r_sr.tsv")
P_PSVED    = os.path.join(RESGROUP, "片尾", "_raw_psv_ed.tsv")
P_ENDLIST  = os.path.join(RESGROUP, "片尾", "片尾清单.tsv")
P_ENDDOC   = os.path.join(RESGROUP, "片尾", "片尾说明.md")
P_RUBIAO   = os.path.join(RESGROUP, "剧本", "简介", "_待入表汇总.tsv")
P_PSVED_DIR = os.path.join(RESGROUP, "片尾", "_src", "psv_ed")

BS = chr(92)   # 反斜杠：避免源码里出现易被转义处理吞掉的字面量

# ---------------------------------------------------------------- 工具
def read_tsv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return [r for r in csv.reader(f, delimiter="\t")]

def write_tsv(path, header, rows):
    guard_write(path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        w.writerows(rows)

def fingerprint(text):
    """归一化指纹（规则见 _merge_README.md §一）：
       ① 去字面 '\\n'  ② 去全部空白（含 U+3000）  ③ 〜(U+301C)→～(U+FF5E)。只做这三步。"""
    t = text.replace(BS + "n", "")
    t = "".join(ch for ch in t if not ch.isspace())
    t = t.replace(chr(0x301C), chr(0xFF5E))
    return t

NL_MARKER = "换行位置未逐条登记"

def strip_nl_marker(s):
    s = s.replace("；" + NL_MARKER, "").replace(NL_MARKER, "")
    return s.rstrip("；")

def append_note(s, note):
    s = strip_nl_marker(s)
    return (s + "；" + note) if s else note

# ================================================================ 任务 A
def task_a():
    master = read_tsv(P_MASTER)
    hdr, data = master[0], master[1:]

    # 兼容自产物：确保 原文换行位置 列存在（位于 备注 之前）
    if "原文换行位置" not in hdr:
        i_remark = hdr.index("备注")
        hdr = hdr[:i_remark] + ["原文换行位置"] + hdr[i_remark:]
        data = [r[:i_remark] + [""] + r[i_remark:] for r in data]
    ix = {c: i for i, c in enumerate(hdr)}
    for c in ("序号", "场景id", "来源", "脚本", "简介jp", "简介cn", "译文状态",
              "译文来源", "重复组id", "备注", "原文换行位置"):
        if c not in ix:
            raise SystemExit("[FATAL] 主表缺列：%s" % c)

    if len(data) != 1253:
        raise SystemExit("[FATAL] 主表行数 != 1253：%d" % len(data))

    # 1) 主表 重复组 -> 指纹
    group2fp = {}
    fp2group = {}
    for r in data:
        g, f = r[ix["重复组id"]], fingerprint(r[ix["简介jp"]])
        if g in group2fp and group2fp[g] != f:
            raise SystemExit("[FATAL] 同一重复组指纹不一致：%s" % g)
        group2fp[g] = f
        fp2group.setdefault(f, set()).add(g)

    # 2) 三段译文
    tr = {}
    for p in P_CN:
        rr = read_tsv(p)
        ii = {c: i for i, c in enumerate(rr[0])}
        for row in rr[1:]:
            tid = row[ii["待译id"]]
            if tid in tr:
                raise SystemExit("[FATAL] 待译id 重复：%s" % tid)
            tr[tid] = {"jp": row[ii["简介jp"]], "cn": row[ii["简介cn"]],
                       "nl": row[ii["原文换行位置"]], "rubiao": row[ii["待入表条目"]],
                       "note": row[ii["备注"]]}
    if sorted(tr) != ["T%03d" % i for i in range(1, 62)]:
        raise SystemExit("[FATAL] 待译id 非 T001..T061 连续")

    # 3) 缺口表：按指纹匹配（不得按 id 顺序 / 行号硬对）
    gap = read_tsv(P_GAP)
    gi = {c: i for i, c in enumerate(gap[0])}
    g2tid, tid2g = {}, {}
    for row in gap[1:]:
        tid = row[gi["待译id"]]
        f = fingerprint(row[gi["简介jp"]])
        if f != fingerprint(tr[tid]["jp"]):
            raise SystemExit("[FATAL] 缺口/译文 简介jp 指纹不一致：%s" % tid)
        groups = sorted(fp2group.get(f, []))
        if len(groups) != 1:
            raise SystemExit("[FATAL] 缺口 %s 指纹未唯一匹配重复组：%s" % (tid, groups))
        g = groups[0]
        if g in g2tid and g2tid[g] != tid:
            raise SystemExit("[FATAL] 重复组 %s 被多个待译id 命中" % g)
        g2tid[g] = tid
        tid2g[tid] = g
    if len(g2tid) != 61:
        raise SystemExit("[FATAL] 缺口映射数 != 61：%d" % len(g2tid))

    # 4) 回填 + 新增列
    backfilled_rows = 0
    covered_rows = 0
    for r in data:
        g = r[ix["重复组id"]]
        if g in g2tid:
            tid = g2tid[g]
            r[ix["简介cn"]] = tr[tid]["cn"]
            r[ix["译文来源"]] = "新译(2026-09-29 · %s)" % tid
            r[ix["译文状态"]] = "已有(新译)"
            r[ix["原文换行位置"]] = tr[tid]["nl"]
            covered_rows += 1
        else:
            if r[ix["原文换行位置"]] == "":
                r[ix["备注"]] = append_note(r[ix["备注"]], NL_MARKER)
    # 统计回填行（= 覆盖行，全部之前为 需新译）
    backfilled_rows = covered_rows

    # 4.5) 术语统一（作品层术语表 §二·补 2.7.2 裁决）：交付集内的异写统一
    #   「羽田宅」→「羽田家」（该异写出自 _raw_ot 的既有 ot 译法 s03_12j / s03c_04c；
    #    本表是独立交付物，借自既有 ot 译文的行也一并在交付层统一；语料侧回改另记为待办）。
    #   ⚠ 与 N6（既有译文的其他体例差异不改、只登记）不冲突：本项是术语表已裁决的统一项。
    unified_rows = []
    for r in data:
        if "羽田宅" in r[ix["简介cn"]]:
            r[ix["简介cn"]] = r[ix["简介cn"]].replace("羽田宅", "羽田家")
            unified_rows.append(r[ix["序号"]])

    # 5) 落盘
    write_tsv(P_MASTER, hdr, data)

    # 6) 汇总自检
    need = sum(1 for r in data if r[ix["译文状态"]] == "需新译")
    empty = [(r[ix["序号"]], r[ix["来源"]], r[ix["脚本"]], r[ix["重复组id"]])
             for r in data if r[ix["简介cn"]] == ""]
    return {"rows": len(data), "backfilled": backfilled_rows,
            "groups": len(g2tid), "need_new": need, "empty_cn": empty,
            "unified_ada_title": unified_rows, "header": hdr}

# ================================================================ 任务 B
def family_of(name):
    if name.startswith("sr2_c"):
        return "sr2_c"
    if name.startswith("sr2_t"):
        return "sr2_t"
    m = re.match(r"^(sr\d+)_", name)
    if m:
        return m.group(1)
    if name.startswith("ec"):
        return "ec"
    return "—"

def norm_lang(s):
    """片尾清单 `文字语言` 列口径统一（N7）：PSV 侧源清单写「日语」，
    交付清单与图行统一作「日文」（图行源列本即「日文」/「英文」/「无」）。幂等。"""
    return "日文" if s == "日语" else s

def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def task_b():
    sr = read_tsv(P_SR)
    si = {c: i for i, c in enumerate(sr[0])}
    srows = sr[1:]
    if len(srows) != 141:
        raise SystemExit("[FATAL] _raw_r_sr 行数 != 141：%d" % len(srows))

    # R 版内部同图重复（同 md5）→ DUP-0x（按交付主表行序首次出现赋号）
    by_md5 = {}
    for r in srows:
        by_md5.setdefault(r[si["PNG的md5"]], []).append(r[si["原名"]])
    dup_ids = {}
    n = 0
    for r in srows:
        m = r[si["PNG的md5"]]
        if len(by_md5[m]) > 1 and m not in dup_ids:
            n += 1
            dup_ids[m] = "DUP-%02d" % n

    out = []
    seq = 0
    for r in srows:
        seq += 1
        name = r[si["原名"]]
        j = r[si["与ot篇同名件"]]
        tags = []
        if r[si["PNG的md5"]] in dup_ids:
            tags.append(dup_ids[r[si["PNG的md5"]]])
        if j.startswith("逐像素相同"):
            tags.append("OTDUP-" + name)
        dup = "；".join(tags) if tags else "—"
        out.append([str(seq), "图", r[si["用途"]], family_of(name), "otr",
                    r[si["输出文件名"]], "PNG", "%sx%s" % (r[si["宽"]], r[si["高"]]),
                    r[si["PNG字节"]], r[si["PNG的md5"]], r[si["含图片化文字"]],
                    r[si["W19口径"]], norm_lang(r[si["文字语言"]]), dup, j, r[si["备注"]]])

    ved = read_tsv(P_PSVED)
    vi = {c: i for i, c in enumerate(ved[0])}
    vrows = ved[1:]
    # 容错：若首数据行误等于表头则剔除
    if vrows and vrows[0] == ved[0]:
        vrows = vrows[1:]
    if len(vrows) != 7:
        raise SystemExit("[FATAL] _raw_psv_ed 行数 != 7：%d" % len(vrows))

    for r in vrows:
        seq += 1
        src = r[vi["源文件"]]
        stem = os.path.splitext(os.path.basename(src.replace("/", BS)))[0].lower()
        mpg_name = stem + ".mpg"
        mpg_path = os.path.join(P_PSVED_DIR, mpg_name)
        if not os.path.isfile(mpg_path):
            raise SystemExit("[FATAL] 视频交付件缺失：%s" % mpg_path)
        out.append([str(seq), "视频", "片尾ED", r[vi["归属角色"]], "otv", mpg_name,
                    "MPEG-1/MP2 (.mpg)", "%s / %s" % (r[vi["分辨率"]], r[vi["时长"]]),
                    r[vi["mpg字节"]], md5_file(mpg_path), r[vi["含图片化文字(是|否)"]],
                    "计入", norm_lang(r[vi["文字语言"]]), "—", "—", r[vi["备注"]]])

    header = ["序号", "类别(图/视频)", "用途", "归属角色/范围", "来源(otr/otv)",
              "交付文件名", "格式", "宽/高或时长", "字节", "md5", "含图片化文字",
              "W19口径", "文字语言", "重复组", "与ot篇同名件", "备注"]
    write_tsv(P_ENDLIST, header, out)
    return {"rows": len(out), "images": len(srows), "videos": len(vrows),
            "dup_groups": sorted(set(dup_ids.values()))}

END_SEC_HEAD = "## 〇、片尾清单.tsv（合并清单）"

def apply_end_doc_section():
    with open(P_ENDDOC, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    body = "\n".join([
        END_SEC_HEAD,
        "",
        "> 本节由 `资源组\\工具\\assemble_deliverables.py`（ISSUE-20260929-12 任务 B）生成，**幂等可复算**；",
        "> **不删改下方既有小节**（既有 §1–§8 保持原样）。",
        "",
        "**`片尾清单.tsv` 是本工程片尾交付集的唯一交付清单**（制表符 / LF / UTF-8 无 BOM），",
        "把 R 版（`otr`）图与 PSV（`otv`）视频两批产物合并为一张统一账：",
        "",
        "| 类别 | 件数 | 来源 | 清单来源（只读） | 交付物 |",
        "| --- | ---: | --- | --- | --- |",
        "| **图** | **141** | `otr`（R 版片尾/结局） | `_raw_r_sr.tsv` | `_src\\r_staff\\` 141 张 PNG |",
        "| **视频** | **7** | `otv`（PSV 7 支 ED） | `_raw_psv_ed.tsv` | `_src\\psv_ed\\` 7 支 `.mpg` |",
        "| **合计** | **148** | | | |",
        "",
        "构成明细：图 141 = `片尾STAFF` 97（`sr0`–`sr5`，含片尾 STAFF 分页）＋ `结局卡` 31（`ec`）",
        "＋ `歌词` 7（`sr2_t`）＋ `胸像` 6（`sr2_c`）；视频 7 = 亚衣 / 明日香 / 日和子 / 小鸠 / 美咲 / 京 / 凤鸣 各一支 ED。",
        "",
        "**`重复组` 列口径**：标记交付集内的同图重复关系——`DUP-01`..`DUP-04` = R 版内部同图重复",
        "（同 md5，4 组各 2 件：`sr0_05=sr1_05`、`sr0_07=sr1_07`、`sr0_09=sr1_09`、`sr0_10=sr1_10`）；",
        "`OTDUP-<原名>` = 该 R 件与其 **ot 篇同名件逐像素相同**（同一重复组，ot 件不在本清单、以同名件标识）；",
        "`—` = 与 ot **像素不同** 或 **ot 无此件**，且不属任何 R 内部同图组。两关系并存者以「；」并列。",
        "",
        "**⚠ 风险项（须随交付一并登记）**：**PSV 7 支视频为 MPEG-1 零损失转码**（视频流 `-c:v copy` 逐字节保真，",
        "仅音轨转 MP2 224k 有损；转码必要性见下 §8 及 `片尾说明_PSV侧.md`），**但 krkrz 实机播放尚未验证**",
        "（系统 DirectShow 链路 MCI 探针 7/7 OPEN-OK 且 `mode=playing`，`960×544` 超出 MPEG-1 *constrained parameters*，",
        "**须编程组接入后实机确认**；退路为有损转码）。",
        "",
        "列口径补充：`md5` 列 = **交付件文件本身的 md5**（图 = `_src\\r_staff\\*.png`；视频 = `_src\\psv_ed\\*.mpg`），",
        "PSV 侧「视频 ES 逐字节保真」的 ES md5 另见逐行 `备注` 与 `片尾说明_PSV侧.md`；`宽/高或时长` 列，",
        "图写 `宽x高`、视频写 `分辨率 / 时长`；图行 `归属角色/范围` = 该件所属族（`sr0`–`sr5`／`sr2_c`／`sr2_t`／`ec`）。",
    ])
    if END_SEC_HEAD in text:
        i = text.index(END_SEC_HEAD)
        j = text.index("---\n", i)
        text = text[:i] + text[j:]
    k = text.index("\n---\n")
    text = text[:k + 1] + body + "\n\n" + text[k + 1:]
    guard_write(P_ENDDOC)
    with open(P_ENDDOC, "w", encoding="utf-8", newline="") as f:
        f.write(text)

# ================================================================ 任务 C
SEP = "；"

def parse_ids(s):
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        m = re.match(r"^(T\d+)-(T\d+)$", tok)
        if m:
            a, b = int(m.group(1)[1:]), int(m.group(2)[1:])
            out += ["T%03d" % i for i in range(a, b + 1)]
        elif re.match(r"^T\d+$", tok):
            out.append(tok)
    return out

def parse_rubiao(s):
    if not s or s.strip() in ("无", ""):
        return []
    entries = []
    for seg in s.split(SEP):
        seg = seg.strip()
        if not seg:
            continue
        parts = seg.split("｜")
        if len(parts) >= 3 and parts[0] and parts[1]:
            entries.append({"term": parts[0].strip(), "trans": parts[1].strip(),
                            "ids": parse_ids(parts[2].strip()),
                            "yiju": "｜".join(parts[3:]).strip(), "notes": []})
        elif entries:
            entries[-1]["notes"].append(seg)
    return entries

def suggest_layer(term, yiju, notes):
    s = (yiju or "") + " " + " ".join(notes or [])
    if "建议通用层" in s:
        return "通用"
    if "建议作品层" in s:
        return "作品"
    has_g = "通用" in s
    has_w = ("作品层" in s) or ("作品skill" in s)
    if has_g and not has_w:
        return "通用"
    if has_w:
        return "作品"
    # ≪≫ 家族：纯符号转换（≪≫／≪…≫）＝通用标点通则；带具体词的 ≪X≫＝该词定译，归作品层
    if term in ("≪≫", "≪…≫"):
        return "通用"
    if term.startswith("≪"):
        return "作品"
    return "作品"

def task_c():
    allentries = {}
    order = []
    for p in P_CN:
        rr = read_tsv(p)
        ii = {c: i for i, c in enumerate(rr[0])}
        for row in rr[1:]:
            tid = row[ii["待译id"]]
            for e in parse_rubiao(row[ii["待入表条目"]]):
                term = e["term"]
                if term not in allentries:
                    allentries[term] = {"trans": [], "ids": [], "yiju": [], "notes": []}
                    order.append(term)
                m = allentries[term]
                if e["trans"] not in m["trans"]:
                    m["trans"].append(e["trans"])
                for i in e["ids"]:
                    if i not in m["ids"]:
                        m["ids"].append(i)
                if e["yiju"] and e["yiju"] not in m["yiju"]:
                    m["yiju"].append(e["yiju"])
                for nt in e["notes"]:
                    if nt not in m["notes"]:
                        m["notes"].append(nt)

    def key(t):
        ids = allentries[t]["ids"]
        return (min(ids) if ids else "T999")
    rows = []
    for i, term in enumerate(sorted(order, key=key), 1):
        m = allentries[term]
        trans = " / ".join(m["trans"]) if m["trans"] else "—"
        first = min(m["ids"]) if m["ids"] else "—"
        yiju = "；".join(m["yiju"])
        layer = suggest_layer(term, yiju, m["notes"])
        note = list(m["notes"])
        if len(m["ids"]) > 1:
            note.append("全部出处：%s" % "、".join(sorted(m["ids"])))
        if len(m["trans"]) > 1:
            note.append("⚠ 多译法并存，待主代理裁决")
        rows.append([str(i), term, trans, first, yiju, layer, "；".join(note)])

    header = ["序号", "日文原词/符号", "临时译法", "首次出处(待译id)",
              "原始依据文本", "建议归层(通用/作品)", "备注"]
    write_tsv(P_RUBIAO, header, rows)
    return {"rows": len(rows)}

# ================================================================ main
def main():
    a = task_a()
    b = task_b()
    apply_end_doc_section()
    c = task_c()
    print("[A] 主表 %d 行 | 回填重复组 %d | 回填行 %d | 需新译 %d | 空简介cn %d 条"
          % (a["rows"], a["groups"], a["backfilled"], a["need_new"], len(a["empty_cn"])))
    print("[A·术语统一] 「羽田宅」→「羽田家」在交付主表内统一 %d 行（序号 %s）"
          % (len(a["unified_ada_title"]), ", ".join(a["unified_ada_title"]) or "—"))
    print("[B] 片尾清单 %d 行 = 图 %d + 视频 %d | R 内部同图组 %s"
          % (b["rows"], b["images"], b["videos"], ",".join(b["dup_groups"])))
    print("[C] 待入表汇总 %d 条" % c["rows"])
    print("空 简介cn 行：")
    for row in a["empty_cn"]:
        print("    序号%s %s/%s 重复组=%s" % row)

if __name__ == "__main__":
    main()
