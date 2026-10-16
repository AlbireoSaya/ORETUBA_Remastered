# -*- coding: utf-8 -*-
r"""
verify_synopsis_master.py —— 章节简介合并产物的**只读**验收器

╔══════════════════════════════════════════════════════════════════════════╗
║ ★ 适用范围（先读本条，避免误用）★                                         ║
║   本器只验收『组装前』产物 —— 即 `build_synopsis_master.py` 阶段的产物：    ║
║     主表 `剧本\章节简介.tsv` = **16 列**（无 `原文换行位置`）               ║
║     译文状态 `需新译` = **107 行**（61 个缺口组）                         ║
║   交付态（组装后：**17 列** 含 `原文换行位置` / `需新译` = **0**）           ║
║   请改用 **`verify_deliverables.py`**（交付态验收，见下 §交付态）。         ║
║   —— 在交付态下本器不适用；此时本器会输出「NOT_APPLICABLE」并退出码 2，     ║
║      **不会**给出误导性的 VERIFY FAIL（这不是交付物缺陷，而是验收器选错）。  ║
╚══════════════════════════════════════════════════════════════════════════╝

Issue：ISSUE-20260929-12-greta-synopsis-and-ending

验收口径（组装前；任一项 FAIL 退出码非 0；只读，不写任何文件）：
  ① 三份产出的存在性 / 表头 / 列数 / 编码（UTF-8 无 BOM、LF）
  ② 逐源守恒：主表每源行数 == 该源 `_raw_*.tsv` 记录数，且 (脚本, 简介jp, md5) 多重集逐一相等（不漏不增）
  ③ 重复组一致：同指纹必同组、异指纹必异组；组号连续
  ④ 排序单调：序号连续 1..N；场景顺序与 `05_章节总表.tsv` 行序一致；同场景内 ot→otr→otv；场景号在全集内
  ⑤ `需新译` 集合 == **独立重算**的「无中文组」集合；`需新译` 行 cn 为空；`需新译` 行数 > 缺口组数；缺口表自洽
  ⑥ 负对照：同文本不同脚本必同组（真数据 + 合成行）；指纹改坏必异组；归一化确有判别力；跨「真换行 / 字面 \n」必同组

交付态（组装后：17 列 / `需新译`=0）—— 用 `verify_deliverables.py`：
  ① 主表 1253 行、`需新译`=0、空 `简介cn` 仅 2 条空占位；② 重复组内 `简介cn` 一致；
  ③ `原文换行位置` 列存在且非空行集合 == 61 组覆盖行；④ 片尾清单 148 行（图 141 + 视频 7）
     且**字节 / md5 与磁盘逐件一致**；⑤ `_待入表汇总.tsv` 自洽。

复跑：
    cd "E:/ZCode Workspace/Galgame/临时/wt-syn"
    python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_synopsis_master.py"
    python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_deliverables.py"   # 交付态
"""
import collections
import csv
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import build_synopsis_master as B          # 复用同一份指纹 / 路径 / 读取实现（只读导入，无副作用）

FAILS = []
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    if not ok:
        FAILS.append(name)
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  | " + detail) if detail else ""))
    return ok


def read_tsv(path):
    return list(csv.DictReader(io.open(path, encoding="utf-8", newline=""), delimiter="\t"))


def main():
    print("== verify_synopsis_master ==")
    print("工作树根（资源组）：%s\n" % B.ROOT)
    print("【适用范围】本器只验收『组装前』产物（build_synopsis_master.py：16 列 / 需新译=107）；"
          "交付态（17 列 / 需新译=0）请用 verify_deliverables.py。\n")

    # ── ① 文件 / 表头 / 列数 / 编码 ──
    for p in (B.OUT_MASTER, B.OUT_GAP, B.OUT_README):
        check("产出存在：%s" % os.path.basename(p), os.path.isfile(p))
    for p in (B.OUT_MASTER, B.OUT_GAP, B.OUT_README):
        raw = io.open(p, "rb").read()
        check("UTF-8 无 BOM 且无 CR：%s" % os.path.basename(p),
              not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw, "bytes=%d" % len(raw))

    m_head = io.open(B.OUT_MASTER, encoding="utf-8").read().split("\n")[0].split("\t")
    g_head = io.open(B.OUT_GAP, encoding="utf-8").read().split("\n")[0].split("\t")

    # ── ★ 状态判别：组装前 vs 交付态 ──
    #  组装前 = build_synopsis_master.py 产物（16 列、无 `原文换行位置`、需新译=107）
    #  交付态 = assemble_deliverables.py 并入新译后（17 列、需新译=0）
    rows_probe = read_tsv(B.OUT_MASTER)
    need_probe = sum(1 for r in rows_probe if (r.get("译文状态") or "") == B.ST_NEW)
    has_nlcol = "原文换行位置" in m_head
    is_assembled = has_nlcol or (len(m_head) != len(B.MASTER_HEADER)) or (need_probe == 0)
    if is_assembled:
        print("")
        print("=" * 74)
        print("【本器不适用 · NOT_APPLICABLE】检测到『组装后（交付态）』产物：")
        print("  主表表头 %d 列%s ｜ 译文状态『需新译』= %d 行"
              % (len(m_head), "（含 `原文换行位置`）" if has_nlcol else "", need_probe))
        print("  本器只验收『组装前』产物（build_synopsis_master.py 阶段：16 列 / 需新译=107）。")
        print("  ⇒ 交付态请改用：**verify_deliverables.py**（见 `_merge_README.md` §六）。")
        print("  ※ 这不是交付物缺陷，而是验收器选错；退出码 2 仅表示『本器不适用于当前状态』。")
        print("  ※ 提醒：单独跑 build_synopsis_master.py 会把主表打回 16 列 / 需新译=107")
        print("     （抹掉新译与 `原文换行位置`），必须接跑 assemble_deliverables.py。")
        print("=" * 74)
        print("RESULT: NOT_APPLICABLE（交付态；请用 verify_deliverables.py）  [exit=2]")
        return 2

    check("主表表头逐字一致", m_head == B.MASTER_HEADER, "|".join(m_head))
    check("缺口表表头逐字一致", g_head == B.GAP_HEADER, "|".join(g_head))
    m_rows = read_tsv(B.OUT_MASTER)
    g_rows = read_tsv(B.OUT_GAP)
    check("主表每行 16 列", all(len(r) == 16 for r in m_rows), "行数=%d" % len(m_rows))
    check("缺口表每行 6 列", all(len(r) == 6 for r in g_rows), "行数=%d" % len(g_rows))

    raw_rows = {src: read_tsv(os.path.join(B.INTRO_DIR, fname)) for src, fname in B.RAW_FILES}
    n_in = sum(len(v) for v in raw_rows.values())
    check("主表行数 == 三源输入行数之和", len(m_rows) == n_in,
          "%d vs %d（ot %d / otr %d / otv %d）" % (len(m_rows), n_in, len(raw_rows["ot"]),
                                                   len(raw_rows["otr"]), len(raw_rows["otv"])))

    # ── ② 逐源守恒（(脚本, jp, md5) 多重集逐一相等） ──
    for src, fname in B.RAW_FILES:
        in_ms = collections.Counter((r["script"], r["简介jp"], r["jp的md5"]) for r in raw_rows[src])
        out_ms = collections.Counter((r["脚本"], r["简介jp"], r["jp的md5"])
                                     for r in m_rows if r["来源"] == src)
        check("逐源守恒（%s）行数" % src, sum(out_ms.values()) == sum(in_ms.values()),
              "%d vs %d" % (sum(out_ms.values()), sum(in_ms.values())))
        check("逐源守恒（%s）(脚本,jp,md5) 多重集逐一相等" % src, in_ms == out_ms,
              "缺 %d / 多 %d" % (sum((in_ms - out_ms).values()), sum((out_ms - in_ms).values())))

    # ── ③ 重复组一致 ──
    fp_by_group = collections.defaultdict(set)
    group_by_fp, bad_mix, bad_inj = {}, [], []
    for r in m_rows:
        g, fp = r["重复组id"], B.fingerprint(r["简介jp"])
        fp_by_group[g].add(fp)
        if fp in group_by_fp and group_by_fp[fp] != g:
            bad_inj.append((fp[:16], group_by_fp[fp], g))
        group_by_fp[fp] = g
        if len(fp_by_group[g]) > 1:
            bad_mix.append(g)
    check("重复组：同组只含一个指纹（同指纹必同组）", not bad_mix, "越界组=%s" % bad_mix[:5])
    check("重复组：同一指纹只属一个组（异指纹必异组）", not bad_inj, "冲突=%s" % bad_inj[:5])
    gids = sorted({r["重复组id"] for r in m_rows})
    check("重复组号连续 R001..R%03d" % len(gids),
          gids == ["R%03d" % i for i in range(1, len(gids) + 1)], "%d 组" % len(gids))

    # ── ④ 排序单调 ──
    check("序号连续 1..N",
          [int(r["序号"]) for r in m_rows] == list(range(1, len(m_rows) + 1)), "N=%d" % len(m_rows))
    chap, _ = B.load_chapters()
    prev, mono = None, True
    for r in m_rows:
        if r["场景id"] == B.UNMATCHED:
            continue
        o = chap[r["场景id"]]["order"]
        if prev is not None and o < prev:
            mono = False
        prev = o
    check("排序单调：场景顺序与 05_章节总表.tsv 行序一致（未匹配置尾）", mono)
    check("未匹配行全部排在末尾",
          [i for i, r in enumerate(m_rows) if r["场景id"] == B.UNMATCHED] ==
          list(range(len(m_rows) - sum(1 for r in m_rows if r["场景id"] == B.UNMATCHED), len(m_rows))))
    per_scene_srcs = collections.OrderedDict()
    for r in m_rows:
        per_scene_srcs.setdefault(r["场景id"], []).append(B.SRC_RANK[r["来源"]])
    off = [(s, v) for s, v in per_scene_srcs.items() if v != sorted(v)]
    check("同场景内来源顺序为 ot → otr → otv", not off, "%s" % off[:3])
    scenes_exp = set()
    for src, fname in B.SCENE_FILES:
        for line in io.open(os.path.join(B.SCEN_DIR, fname), encoding="utf-8"):
            scenes_exp.add(json.loads(line)["scene_id"])
    scenes_out = {r["场景id"] for r in m_rows} - {B.UNMATCHED}
    check("输出的场景 ⊆ 712 场景全集", scenes_out <= scenes_exp,
          "输出 %d / 全集 %d" % (len(scenes_out), len(scenes_exp)))

    # ── ⑤ 需新译 集合 == 独立重算的「无中文组」 ──
    grp_rows = collections.defaultdict(list)
    for r in m_rows:
        grp_rows[r["重复组id"]].append(r)
    all_fp, covered_fp = set(), set()
    for src, fname in B.RAW_FILES:
        for r in raw_rows[src]:
            fp = B.fingerprint(r["简介jp"])
            all_fp.add(fp)
            if src == "ot" and (r["简介cn"] or "").strip():
                covered_fp.add(fp)
            if src == "otv" and (r.get("是否已在我方库") or "").strip() == "是":
                covered_fp.add(fp)                       # 含空槽型库内命中（M09_02）
    need_fp = all_fp - covered_fp
    master_need_fp = {B.fingerprint(r["简介jp"]) for r in m_rows if r["译文状态"] == B.ST_NEW}
    check("需新译 集合 == 独立重算的无中文组集合", need_fp == master_need_fp,
          "独立=%d 主表=%d 差=%d" % (len(need_fp), len(master_need_fp), len(need_fp ^ master_need_fp)))
    check("需新译 组的全部成员都是 需新译",
          all(all(r["译文状态"] == B.ST_NEW for r in rs)
              for g, rs in grp_rows.items() if B.fingerprint(rs[0]["简介jp"]) in master_need_fp))
    check("需新译 行 简介cn 全为空",
          all(r["简介cn"] == "" for r in m_rows if r["译文状态"] == B.ST_NEW))
    check("非需新译 行 简介cn 全非空（空占位/空槽库内命中除外）",
          all(r["简介cn"].strip() for r in m_rows
              if r["译文状态"] != B.ST_NEW and "空槽" not in r["译文来源"]
              and B.fingerprint(r["简介jp"]) != ""),
          str([(r["来源"], r["脚本"]) for r in m_rows
               if r["译文状态"] != B.ST_NEW and not r["简介cn"].strip()
               and "空槽" not in r["译文来源"] and B.fingerprint(r["简介jp"]) != ""][:5]))
    check("译文状态取值合法", {r["译文状态"] for r in m_rows} <= {B.ST_OT, B.ST_OTV, B.ST_NEW},
          str(sorted({r["译文状态"] for r in m_rows})))
    all_new_groups = sum(1 for rs in grp_rows.values() if all(r["译文状态"] == B.ST_NEW for r in rs))
    check("需新译 的组数 == 缺口行数", all_new_groups == len(g_rows),
          "%d vs %d" % (all_new_groups, len(g_rows)))
    tids = [r["待译id"] for r in g_rows]
    check("待译id 唯一且连续", tids == ["T%03d" % i for i in range(1, len(tids) + 1)])
    ok_rep = ok_scene = ok_src = ok_order = True
    orders = []
    for gr in g_rows:
        m = re.search(r"重复组 (R\d+)", gr["备注"])
        gid = m.group(1) if m else None
        rs = grp_rows.get(gid, [])
        if not rs:
            ok_rep = False
            continue
        if not any(r["简介jp"] == gr["简介jp"] for r in rs):
            ok_rep = False
        if set(gr["涉及场景"].split(";")) != {r["场景id"] for r in rs}:
            ok_scene = False
        if set(gr["涉及来源"].split(";")) != {r["来源"] for r in rs}:
            ok_src = False
        orders.append(min([chap[s]["order"] for s in {r["场景id"] for r in rs} if s in chap] or [10 ** 9]))
    check("缺口：简介jp 与组内某成员逐字相同", ok_rep)
    check("缺口：涉及场景 == 组内场景集合", ok_scene)
    check("缺口：涉及来源 == 组内来源集合", ok_src)
    check("缺口：按剧情顺序排列（T 号随 05 行序单调不减）", orders == sorted(orders))
    n_new_rows = sum(1 for r in m_rows if r["译文状态"] == B.ST_NEW)
    check("缺口行数 < 需新译行数（按组去重确实生效）", len(g_rows) < n_new_rows,
          "缺口 %d 组 ← 需新译 %d 行" % (len(g_rows), n_new_rows))

    # ── ⑥ 负对照 ──
    real_pos = [g for g, rs in grp_rows.items() if len({r["脚本"] for r in rs}) > 1]
    check("正对照（真数据）：同文本不同脚本被分到同一组", bool(real_pos),
          "此类组 %d 个，例 %s / %s" % (len(real_pos), real_pos[0],
          [(r["来源"], r["脚本"]) for r in grp_rows[real_pos[0]]]))
    cross_rep = [g for g, rs in grp_rows.items()
                 if len({r["来源"] for r in rs}) > 1 and len({r["简介jp"] for r in rs}) > 1]
    check("正对照（真数据）：跨源「换行写法不同」仍被判为同一组", bool(cross_rep),
          "%d 组，例 %s" % (len(cross_rep), cross_rep[0] if cross_rep else None))

    def group_of(items):
        gg = collections.defaultdict(list)
        for k, v in items:
            gg[v].append(k)
        return gg

    t = "\u3000これはテスト用の同一文案です。\n"
    check("正对照（合成）：同文本不同脚本 → 同一组",
          len(group_of([("A/s01_01a", B.fingerprint(t)), ("B/S01_01A", B.fingerprint(t))])) == 1)
    check("负对照（合成）：把一条指纹改坏 → 分到不同组",
          len(group_of([("A/s01_01a", B.fingerprint(t)),
                        ("B/S01_01A", B.fingerprint(t + "改坏"))])) == 2)
    a, b = "あい\nうえ", "あい" + B.ESC_BSN + "うえ"
    check("正对照：真换行 vs 字面 \\n 归一化后为同一指纹（原串不同）",
          a != b and B.fingerprint(a) == B.fingerprint(b))
    check("负对照：指纹吃掉字面 \\n / U+3000 / 〜～ 三类差异",
          B.fingerprint("あ\nい\u3000う〜え") == B.fingerprint("あい う～え"))
    check("负对照：指纹不吃真实字符差异",
          B.fingerprint("あい") != B.fingerprint("あい。"))
    check("负对照：指纹对空占位为空串（S01_01/M09_02 特例的成因可复现）",
          B.fingerprint("\u3000") == "" and B.fingerprint("\u3000\n") == "")

    # ── ⑦ 「采用」列（主代理裁决 B）──
    check("采用列取值合法（是/否）", {r["采用"] for r in m_rows} <= {"是", "否"},
          str(sorted({r["采用"] for r in m_rows})))
    per_scene_ = collections.OrderedDict()
    for r in m_rows:
        per_scene_.setdefault(r["场景id"], []).append(r)
    bad_multi, bad_single, bad_pick, bad_unm = [], [], [], []
    for sid, rs in per_scene_.items():
        if sid == B.UNMATCHED:
            if {r["采用"] for r in rs} != {"否"}:
                bad_unm.append(sid)
            continue
        fps = {B.fingerprint(r["简介jp"]) for r in rs}
        yes = [r for r in rs if r["采用"] == "是"]
        if len(fps) > 1:
            if len(yes) != 1:
                bad_multi.append((sid, len(yes)))
            pick = fps
            for want in ("ot", "otr", "otv"):
                row = next((r for r in rs if r["来源"] == want), None)
                if row is not None:
                    pick = {B.fingerprint(row["简介jp"])}
                    break
            if yes and {B.fingerprint(r["简介jp"]) for r in yes} != pick:
                bad_pick.append(sid)
        else:
            if len(yes) != len(rs):
                bad_single.append((sid, len(yes), len(rs)))
    check("多文本场景恰有 1 行 采用=是（裁决 B 规则 ①②）", not bad_multi, "%s" % bad_multi[:5])
    check("文本一致的场景全部 采用=是（裁决 B 规则 ③）", not bad_single, "%s" % bad_single[:5])
    check("采用=是 的那一版 == ot > otr > otv 优先级所选版", not bad_pick, "%s" % bad_pick[:5])
    check("未匹配行 采用=否", not bad_unm, "%s" % bad_unm[:3])
    check("采用=否 且场景有效 的行 备注均写明未采用原因",
          all(("变体留档，非采用版" in r["备注"]) or ("非首选载体" in r["备注"])
              for r in m_rows if r["采用"] == "否" and r["场景id"] != B.UNMATCHED))
    multi = {sid: {B.fingerprint(r["简介jp"]) for r in rs}
             for sid, rs in per_scene_.items() if sid != B.UNMATCHED
             and len({B.fingerprint(r["简介jp"]) for r in rs}) > 1}
    check("多文本场景：与采用版同文本的 否 行标「非首选载体」；异文本的 否 行标「变体留档」",
          all((("非首选载体" in r["备注"]) if B.fingerprint(r["简介jp"]) == B.fingerprint(
              next(x for x in per_scene_[sid] if x["采用"] == "是")["简介jp"]) else
               ("变体留档" in r["备注"]))
              for sid in multi for r in per_scene_[sid] if r["采用"] == "否"))
    check("采用=是 且多文本场景 的行 备注不含「变体留档」",
          all("变体留档" not in r["备注"] for r in m_rows
              if r["采用"] == "是" and len({B.fingerprint(x["简介jp"]) for x in per_scene_[r["场景id"]]}) > 1))
    check("采用=是 行数 + 采用=否 行数 == 主表行数",
          sum(1 for r in m_rows if r["采用"] == "是") + sum(1 for r in m_rows if r["采用"] == "否") == len(m_rows),
          "是=%d 否=%d" % (sum(1 for r in m_rows if r["采用"] == "是"),
                          sum(1 for r in m_rows if r["采用"] == "否")))
    check("裁决 C 已落地：两行 s00_00 备注含「非简介（序文标题）」且 译文状态 != 需新译",
          all("非简介（序文标题）" in r["备注"] and r["译文状态"] != B.ST_NEW
              for r in m_rows if r["脚本"] == "s00_00"),
          "%d 行" % sum(1 for r in m_rows if r["脚本"] == "s00_00"))
    check("裁决 D 已落地：未匹配行备注含「源为空占位，无正文」且 译文状态 != 需新译",
          all("源为空占位，无正文" in r["备注"] and r["译文状态"] != B.ST_NEW
              for r in m_rows if r["场景id"] == B.UNMATCHED))
    # ── ⑧ 裁决 A：供体冲突的未采用译法必须留痕（不删）
    conf_rows = [r for r in m_rows if "供体冲突" in r["备注"]]
    check("供体冲突 4 例两侧均留痕（另一译法未采用，不删行）",
          len(conf_rows) == 8 and any("未采用" in r["备注"] for r in conf_rows),
          "%d 行带供体冲突备注" % len(conf_rows))

    # ── ⑨ 缺口表不含 C/D 两类行（裁决后再次核对）──
    gap_scenes = set()
    for gr in g_rows:
        gap_scenes |= set(gr["涉及场景"].split(";"))
    check("缺口表不含裁决 C 的行（ot_s00_00）", "ot_s00_00" not in gap_scenes)
    check("缺口表不含未匹配伪场景行（裁决 D）", B.UNMATCHED not in gap_scenes)
    check("缺口表不含空指纹行（空占位组，裁决 D）",
          all(B.fingerprint(gr["简介jp"]) != "" for gr in g_rows))
    check("裁决 C/D 的行 译文状态 均非 需新译",
          all(r["译文状态"] != B.ST_NEW for r in m_rows
              if r["脚本"] == "s00_00" or r["场景id"] == B.UNMATCHED))

    print("\n统计：主表 %d 行（ot %d / otr %d / otv %d）｜重复组 %d｜需新译 %d 行 / 缺口 %d 组 / %d 字" % (
        len(m_rows), sum(1 for r in m_rows if r["来源"] == "ot"),
        sum(1 for r in m_rows if r["来源"] == "otr"),
        sum(1 for r in m_rows if r["来源"] == "otv"),
        len(gids), n_new_rows, len(g_rows), sum(int(r["jp字符数"]) for r in g_rows)))
    print("检查项：%d，通过 %d，失败 %d" % (len(CHECKS), len(CHECKS) - len(FAILS), len(FAILS)))
    print("VERIFY " + ("ALL_PASS" if not FAILS else "FAIL：%s" % FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
