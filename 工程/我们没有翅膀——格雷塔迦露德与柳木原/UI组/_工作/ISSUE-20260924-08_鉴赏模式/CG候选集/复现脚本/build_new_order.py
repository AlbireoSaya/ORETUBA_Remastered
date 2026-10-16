# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · 「新顺序」落位：按主代理最终落位规格重做映射与验收图（幂等）

输入（只读）：
  CG候选集\清单.tsv                  —— 本包 363 组（旧 ID = 组序号）
  CG候选集\用户新顺序_20260924.txt    —— 用户给定的新顺序 + 删除清单
  CG候选集\代表图\<旧ID>_<组名>.png   —— 各栏代表图

输出（只写 CG候选集\新顺序\）：
  映射.tsv                    286 行（新ID / 旧ID / 组名 / 差分件数 / 并入旧ID列表 / 该栏统一名列表 / 代表图路径）
  接触印相表\sheet_01…08.png  6×6=36 栏/张，左上角新 ID，右下角 N/N 仅 N>1 时画
  校验.txt                    5 条断言的逐条实际输出 + 覆盖算术四项明细
  待裁决.tsv                  225/228 保留项 + 本次核对发现的冲突

落位规格（主代理 2026-09-24 最终版）：
  · 重复行取第一次出现 ⇒ 135/177/242/275 四栏主件作废（134.284 / 115.176 / 154.207 / 274.336 保留）
  · 空栏位补位：135←285(nar21) 177←340(yy_02) 242←341(yy_03) 245←344(yy_06) 275←345(yy_07)
  · A 组 8 件「无孪生」安置：077→并入198；093/126/127→并入285（131 之后，序 93,126,127）；
    106→并入284（348 之后）；278→并入129；318→并入256；285→新135 主件
  · 删除：091/182/199/347（删除清单中「有孪生」）+ 076/097/099/102/107/108/109（A 组剩余 7 件）
  · 待裁决（先保留）：225 mis51 / 228 mis54
"""
from __future__ import annotations

import csv
import hashlib
import io
import glob
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
CG = os.path.join(ROOT, "UI组", "_工作", "ISSUE-20260924-08_鉴赏模式", "CG候选集")
USERLIST = os.path.join(CG, "用户新顺序_20260924.txt")
MANIFEST = os.path.join(CG, "清单.tsv")
REPDIR = os.path.join(CG, "代表图")
GROUPDIR = os.path.join(CG, "组")
CGDIR = os.path.join(ROOT, "资源组", "美术统一", "CG背景")
OUT = os.path.join(CG, "新顺序")
D_SHEET = os.path.join(OUT, "接触印相表")

# ---- 规格常量 ----
FILL = {135: 285, 177: 340, 242: 341, 245: 344, 275: 345}
DEDUP_SECOND = {135: 284, 177: 207, 242: 176, 275: 336}
A_MERGE = {198: [77], 285: [93, 126, 127], 284: [106], 129: [278], 256: [318]}
A_MERGE_AFTER = {285: 131, 284: 348}
DEL_TWIN = [91, 182, 199, 347]
DEL_A = [76, 97, 99, 102, 107, 108, 109]
DEL_PENDING = [225, 228]      # 主代理 2026-09-24 裁决：用户「剩下的全删」⇒ 由待裁决转为删除
PENDING = []                  # 待裁决 = 0
DEL_NOTE = {
    225: u"967x725 高清版删除后不再进鉴赏；内容由旧 092 e_mis51（新 211）承载",
    228: u"967x725 高清版删除后不再进鉴赏；内容由旧 093 e_mis54（并入新 285）承载",
}

# 位置迁移（主代理 2026-09-24 最后一条）：把「当前新 045」整栏取出后插到「当前新 282」的位置，其余顺延。
# 语义：新 001..044 = 原 001..044；新 045..281 = 原 046..282；新 282 = 原 045；新 283..286 = 原 283..286。
MOVE_FROM, MOVE_TO = 45, 282
PENDING_STATUS = u"用户已确认无需处理（2026-09-24）"

# ---- 版式 ----
SHEET_W = 2400
COLS = ROWS = 6
MARGIN, GAP = 16, 8
CW = (SHEET_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
CH = 300
HEAD = 72
THUMB = 300
BG, BG_CELL, BORDER = (16, 17, 20), (34, 36, 41), (72, 78, 90)
FG, FG_DIM = (236, 238, 242), (150, 156, 168)
BG_BADGE = (0, 0, 0, 150)
FONTS = (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf")


def font(sz):
    for p in FONTS:
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------- 数据
def load():
    rows = list(csv.DictReader(io.open(MANIFEST, encoding="utf-8-sig"), delimiter="\t"))
    by = {int(r["组序号"]): r for r in rows}
    assert len(by) == 363, len(by)
    info = {i: {"name": by[i]["组名"], "n": int(by[i]["差分件数"]),
                "size": by[i]["代表图尺寸"], "unis": by[i]["统一名列表"].split("、")} for i in by}
    rep = {i: os.path.join(REPDIR, "%03d_%s.png" % (i, info[i]["name"])) for i in by}
    repmd5 = {i: md5(rep[i]) for i in by}
    return by, info, rep, repmd5


def parse_userlist():
    slots, deleted = {}, []
    seg = 1
    for line in io.open(USERLIST, encoding="utf-8"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            if u"段二" in s:
                seg = 2
            continue
        if seg == 1:
            m = re.match(r"^(\d+)\.(\d+)\s*(?:\(\+(.*)\))?\s*$", s)
            assert m, s
            merged = [int(x) for x in re.split(r"[+\s]+", m.group(3).strip()) if x] if m.group(3) else []
            slots[int(m.group(1))] = [int(m.group(2)), merged]
        else:
            m = re.match(r"^(\d+)\.(\d+)\s*$", s)
            assert m, s
            deleted.append(int(m.group(2)))
    return slots, deleted


def apply_spec(slots):
    for nid, old in DEDUP_SECOND.items():
        assert slots[nid][0] == old, (nid, slots[nid][0], old)
        slots[nid][0] = None
    for nid, old in FILL.items():
        slots.setdefault(nid, [None, []])
        assert slots[nid][0] is None, (nid, slots[nid][0])
        slots[nid][0] = old
    for nid, members in A_MERGE.items():
        lst = slots[nid][1]
        if nid in A_MERGE_AFTER and A_MERGE_AFTER[nid] in lst:
            at = lst.index(A_MERGE_AFTER[nid]) + 1
            lst[at:at] = list(members)
        else:
            lst.extend(members)
    return slots


def apply_move(slots):
    """取出后插入：把 MOVE_FROM 那一栏移到 MOVE_TO 的位置，其余顺延；返回 (final, orig_of)。
    final[新ID] = [主件, [并入…]]（内容原样搬），orig_of[新ID] = 迁移前的用户新 ID。"""
    keys = sorted(slots)
    order = keys[:MOVE_FROM - 1] + keys[MOVE_FROM:MOVE_TO] + [keys[MOVE_FROM - 1]] + keys[MOVE_TO:]
    assert len(order) == len(keys) and sorted(order) == keys
    final, orig_of = {}, {}
    for i, k in enumerate(order, 1):
        final[i] = slots[k]
        orig_of[i] = k
    return final, orig_of


# ---------------------------------------------------------------- 断言 / 校验
def verify(slots, info, deleted_user, pre_slots=None, orig_of=None):
    main_ids = [slots[n][0] for n in sorted(slots)]
    merged_ids = [m for n in sorted(slots) for m in slots[n][1]]
    del_ids = sorted(set(DEL_TWIN + DEL_A + DEL_PENDING))
    pend_ids = sorted(PENDING)
    L = []
    A = L.append

    A(u"=== 校验 · CG候选集 新顺序（build_new_order.py 生成）===")
    A(u"源：清单.tsv（本包 363 组）｜ 用户新顺序_20260924.txt ｜ 落位规格 = 主代理 2026-09-24 最终版 + 三条裁决")
    A(u"")

    # ① 行数
    n_user = len(slots)
    A(u"【断言 ①】映射行数 = %d 栏（主代理规格原写 285 系笔误，已更正）" % n_user)
    A(u"  实际 = %d  → 以 286 为准（主代理 2026-09-24 裁决 #1 确认）" % n_user)
    A(u"  说明：用户段一有 285 行（新 ID 1..286，唯一缺号 = 245）；规格「4 个空栏位」里的 245")
    A(u"        并不在段一那 285 行之内 ⇒ 补位后栏位数 = 285 + 1 = 286。")
    A(u"        规格原算式 363 = 285 + 并入 + 删除 + 待裁决 按 285 计得 362 ≠ 363，系漏算 245 那一栏；")
    A(u"        按 286 计得 363 ✔。本包取 286 栏，新 ID 连续 001..286。")
    A(u"")

    # ② 新 ID 连续
    ns = sorted(slots)
    cont = ns == list(range(1, len(ns) + 1))
    A(u"【断言 ②】新 ID 连续 001..%03d 无空号：%s" % (len(ns), u"OK" if cont else u"失败"))
    A(u"  实际新 ID 范围 = %03d..%03d ｜ 缺号 = %s" % (ns[0], ns[-1], sorted(set(range(ns[0], ns[-1] + 1)) - set(ns)) or u"无"))
    A(u"")

    # ③ 旧 ID 唯一 + 覆盖至 363
    ok_uniq = len(set(main_ids)) == len(main_ids) and len(set(merged_ids)) == len(merged_ids) \
        and not (set(main_ids) & set(merged_ids))
    four = set(main_ids) | set(merged_ids) | set(del_ids) | set(pend_ids)
    missing = sorted(set(range(1, 364)) - four)
    A(u"【断言 ③】旧 ID 唯一：%s" % (u"OK" if ok_uniq else u"失败"))
    A(u"  主件 %d 个（唯一）｜ 并入成员 %d 个（唯一）｜ 两者不重叠 = %s"
      % (len(main_ids), len(merged_ids), not (set(main_ids) & set(merged_ids))))
    A(u"  覆盖至 363：四类并集 = %d / 363 ｜ 遗漏 = %s ｜ 重复占位 = 无"
      % (len(four), missing or u"无"))
    A(u"")

    # ④ 覆盖算术
    A(u"【断言 ④】覆盖算术")
    A(u"  363 = 286（新栏主件） + 并入成员数 + 删除数 + 待裁决数")
    A(u"  实际：363 = %d + %d + %d + %d = %d  %s"
      % (len(main_ids), len(merged_ids), len(del_ids), len(pend_ids),
         len(main_ids) + len(merged_ids) + len(del_ids) + len(pend_ids),
         u"✔ 成立" if len(main_ids) + len(merged_ids) + len(del_ids) + len(pend_ids) == 363 else u"✘ 不成立"))
    A(u"  规格原写的 285（系笔误）对应 285 + %d + %d + %d = %d ≠ 363；已按裁决 #1 更正为 286。"
      % (len(merged_ids), len(del_ids), len(pend_ids),
         285 + len(merged_ids) + len(del_ids) + len(pend_ids)))
    A(u"  四项明细：")
    A(u"    ① 新栏主件 %d 个：" % len(main_ids))
    for n in ns:
        A(u"         新 %03d ← 旧 %03d %s" % (n, slots[n][0], info[slots[n][0]]["name"]))
    A(u"    ② 并入成员 %d 个（按所属新栏）：" % len(merged_ids))
    for n in ns:
        if slots[n][1]:
            A(u"         新 %03d ← %s" % (n, u"、".join("旧%03d %s" % (m, info[m]["name"]) for m in slots[n][1])))
    A(u"    ③ 删除 %d 个：" % len(del_ids))
    for i in del_ids:
        if i in DEL_TWIN:
            src = u"用户删除清单（有孪生）"
        elif i in DEL_A:
            src = u"A 组剩余 7 件（有孪生）"
        else:
            src = u"原「待裁决保留」→ 用户「剩下的全删」⇒ 转为删除（裁决 #2）"
        note = (u"　【留痕】" + DEL_NOTE[i]) if i in DEL_NOTE else u""
        A(u"         旧 %03d %-10s  %s%s" % (i, info[i]["name"], src, note))
    A(u"    ④ 待裁决 %d 个：%s" % (len(pend_ids), u"无" if not pend_ids else u"、".join("%03d" % x for x in pend_ids)))
    A(u"         说明：225/228 已按裁决 #2 由待裁决转为删除（见 ③ 留痕）；")
    A(u"               待裁决.tsv 的 4 行（2 对跨栏重复 + 2 处并入重复）已由用户 2026-09-24 确认「其他都没有问题」")
    A(u"               ⇒ 状态改为「%s」，**可执行待裁决项 = 0**。" % PENDING_STATUS)
    A(u"")

    # ⑥ 位置迁移：旧 ID 集合不变
    A(u"【断言 ⑥】位置迁移后 286 栏、旧 ID 集合与迁移前完全相同")
    A(u"  迁移动作：把「原新 %03d」整栏（主件 + 全部并入成员，原样搬）取出后插入到「原新 %03d」的位置，其余顺延。"
      % (MOVE_FROM, MOVE_TO))
    A(u"  语义：新 001..%03d = 原 001..%03d ｜ 新 %03d..%03d = 原 %03d..%03d ｜ 新 %03d = 原 %03d ｜ 新 %03d..%03d = 原 %03d..%03d"
      % (MOVE_FROM - 1, MOVE_FROM - 1, MOVE_FROM, MOVE_TO - 1, MOVE_FROM + 1, MOVE_TO,
         MOVE_TO, MOVE_FROM, MOVE_TO + 1, 286, MOVE_TO + 1, 286))
    A(u"  栏位数 = %d（迁移前 286）→ %s" % (len(slots), u"OK" if len(slots) == 286 else u"失败"))
    pre_set = set(main_ids) | set(merged_ids)
    if pre_slots is not None:
        pre_set = {pre_slots[k][0] for k in pre_slots} | {m for k in pre_slots for m in pre_slots[k][1]}
        post_set = set(main_ids) | set(merged_ids)
        moved = [n for n in sorted(slots) if orig_of and orig_of[n] != n]
        A(u"  实际发生位移的栏位 = %d 个（原 %03d 与 原 %03d..%03d）" % (len(moved), MOVE_FROM, MOVE_FROM + 1, MOVE_TO))
        A(u"  迁移表摘要（完整逐行见 位置迁移表.tsv）：")
        for n in (MOVE_FROM, MOVE_TO - 1, MOVE_TO):
            o = slots[n]
            A(u"    新 %03d ← 原 %03d ｜ 旧 %03d %-10s ｜ N=%d ｜ 并入 %s"
              % (n, orig_of[n], o[0], info[o[0]]["name"],
                 info[o[0]]["n"] + sum(info[m]["n"] for m in o[1]),
                 u"、".join("%03d" % m for m in o[1]) or u"—"))
        A(u"  迁移前旧 ID 集合 = %d 个 ｜ 迁移后 = %d 个 ｜ 完全相同 = %s"
          % (len(pre_set), len(post_set), u"OK" if pre_set == post_set else u"失败"))
        A(u"    差集：仅在迁移前 = %s ｜ 仅在迁移后 = %s"
          % (sorted(pre_set - post_set) or u"无", sorted(post_set - pre_set) or u"无"))
    A(u"    核对方式：迁移只是重排顺序，不增不减栏位与并入成员 ⇒ 主件 %d + 并入 %d = %d 个旧 ID 逐一比对一致。"
      % (len(main_ids), len(merged_ids), len(set(main_ids) | set(merged_ids))))
    A(u"")

    # ⑤ 并入成员在 组\ 里能找到
    miss = [m for m in merged_ids if not os.path.isdir(os.path.join(GROUPDIR, "%03d_%s" % (m, info[m]["name"])))]
    A(u"【断言 ⑤】每个并入成员的旧 ID 都能在 组\\ 里找到：%s" % (u"OK（%d/%d 全部命中）" % (len(merged_ids), len(merged_ids)) if not miss else u"失败：%s" % miss))
    A(u"  逐项核对方式：按 组\\<旧ID>_<组名>\\ 目录存在性 + 该目录内统一名数量 = 清单差分件数")
    for m in merged_ids:
        d = os.path.join(GROUPDIR, "%03d_%s" % (m, info[m]["name"]))
        got = len(os.listdir(d)) if os.path.isdir(d) else -1
        A(u"    旧 %03d %-10s 目录存在=%s 目录内件数=%d 清单件数=%d 一致=%s"
          % (m, info[m]["name"], os.path.isdir(d), got, info[m]["n"], got == info[m]["n"]))
    A(u"")

    # 附 A：删除项内容是否由孪生保留
    repmd5 = {i: md5(os.path.join(REPDIR, "%03d_%s.png" % (i, info[i]["name"]))) for i in info}
    # 最终清单里出现的旧 ID（主件 + 并入成员）
    present = set(main_ids) | set(merged_ids)
    slot_of = {}
    for n in ns:
        slot_of[slots[n][0]] = n
        for m in slots[n][1]:
            slot_of[m] = n
    # 代表图 md5 -> [(栏位, 持有旧ID)]
    hold_rep = {}
    for o in present:
        hold_rep.setdefault(repmd5[o], []).append((slot_of[o], o))
    # 差分 md5 -> (栏位, 统一名)
    diffmd5 = {o: {u: md5(os.path.join(CGDIR, u)) for u in info[o]["unis"]} for o in info}
    hold_diff = {}
    for o in present:
        for u, h in diffmd5[o].items():
            hold_diff.setdefault(h, []).append((slot_of[o], o, u))

    A(u"【附 A】删除项的内容是否仍被保留（先查代表图 md5，再查差分逐字节相同）")
    lost = []
    for i in del_ids:
        hit_rep = sorted({(n, o) for n, o in hold_rep.get(repmd5[i], []) if o != i})
        if hit_rep:
            A(u"    旧 %03d %-10s → 代表图逐字节同图，持有者：%s"
              % (i, info[i]["name"],
                 u"、".join(u"新 %03d 旧 %03d %s" % (n, o, info[o]["name"]) for n, o in hit_rep)))
            continue
        hit_d = sorted({(n, o, u) for u, h in diffmd5[i].items() for (n, o, uu) in hold_diff.get(h, []) if o != i})
        if hit_d:
            A(u"    旧 %03d %-10s → 差分逐字节同图（代表图 md5 不同）：%s"
              % (i, info[i]["name"],
                 u"、".join(u"新 %03d 旧 %03d %s 的 %s" % (n, o, info[o]["name"], u) for n, o, u in hit_d)))
            continue
        lost.append(i)
        if i in DEL_NOTE:
            A(u"    旧 %03d %-10s → 逐字节口径无持有者（其 967x725 高清版为独有字节）：%s"
              % (i, info[i]["name"], DEL_NOTE[i]))
        else:
            A(u"    旧 %03d %-10s → ⚠ 最终清单中无同图持有者（内容会丢）" % (i, info[i]["name"]))
    A(u"    小结：删除 %d 件 ｜ 逐字节同图持有者 %d 件 ｜ 无逐字节持有者 %d 件%s"
      % (len(del_ids), len(del_ids) - len(lost), len(lost),
         (u"（%s —— 均为 225/228 高清版；同画的 800x600 版仍在清单内，非整张丢失）"
          % u"、".join("%03d" % x for x in lost))
         if lost and all(x in DEL_NOTE for x in lost) else
         ((u"（%s）" % u"、".join("%03d" % x for x in lost)) if lost else u"")))
    A(u"")

    # 附 B：最终清单内「同一代表图跨栏重复」
    A(u"【附 B】最终清单内「同一代表图跨栏重复」（同一栏内与其并入成员同图属正常归并，不计）")
    A(u"  分两类：① 由本次「按旧号最近补」造成的 4 对 = 预期内、用户知情（主代理已明确告知「这 4 件都是")
    A(u"          重复图，栏位会显示与别处相同的图」），保留不改；② 来自用户清单本身的 2 对 = 已列 待裁决.tsv，")
    A(u"          用户 2026-09-24 回「其他都没有问题」⇒ 状态「%s」，按现状保留、不再处理。" % PENDING_STATUS)
    cross = []
    for h, lst in sorted(hold_rep.items(), key=lambda kv: min(n for n, _ in kv[1])):
        ns_ = sorted({n for n, _ in lst})
        if len(ns_) > 1:
            oids = [o for _, o in lst]
            from_fill = any(o in FILL.values() for o in oids)
            cross.append((h, set(ns_), from_fill))
            A(u"    [%s] %s ｜ 代表图 md5 = %s"
              % (u"预期内·用户知情" if from_fill else u"%s" % PENDING_STATUS,
                 u" 与 ".join(u"新 %03d（旧 %03d %s）" % (n, o, info[o]["name"]) for n, o in sorted(lst)),
                 h[:16] + u"…"))
    if not cross:
        A(u"    无")
    A(u"")
    return L, {"main": main_ids, "merged": merged_ids, "del": del_ids, "pend": pend_ids}, cross


# ---------------------------------------------------------------- 落盘
def build_rows(slots, info, rep, orig_of=None):
    out = []
    for n in sorted(slots):
        oid, mem = slots[n]
        unis = list(info[oid]["unis"])
        cnt = info[oid]["n"]
        for m in mem:
            unis += info[m]["unis"]
            cnt += info[m]["n"]
        out.append({"nid": n, "oid": oid, "name": info[oid]["name"], "n": cnt,
                    "mem": mem, "unis": unis, "rep": os.path.relpath(rep[oid], OUT),
                    "orig": (orig_of or {}).get(n, n)})
    return out


def write_map(rows):
    p = os.path.join(OUT, "映射.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow([u"新ID", u"原新ID", u"旧ID", u"组名", u"差分件数", u"并入旧ID列表",
                    u"该栏统一名列表", u"代表图路径"])
        for r in rows:
            w.writerow(["%03d" % r["nid"], "%03d" % r["orig"], "%03d" % r["oid"], r["name"], r["n"],
                        u"、".join("%03d" % m for m in r["mem"]),
                        u"、".join(r["unis"]), r["rep"]])
    return p


def write_move_table(rows):
    """位置迁移表：新ID ← 原新ID，逐行列出（45 与 46..282 的迁移在内）。"""
    p = os.path.join(OUT, "位置迁移表.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow([u"新ID", u"原新ID", u"是否位移", u"旧ID", u"组名", u"差分件数"])
        for r in rows:
            w.writerow(["%03d" % r["nid"], "%03d" % r["orig"],
                        u"是" if r["orig"] != r["nid"] else u"否",
                        "%03d" % r["oid"], r["name"], r["n"]])
    return p


def badge(d, x, y, text, f, anchor="lt"):
    """半透明黑底 + 白字角标。anchor='lt' → (x,y) 为左上角；anchor='rb' → (x,y) 为右下角。"""
    bb = d.textbbox((0, 0), text, font=f)
    bw, bh = bb[2] - bb[0] + 16, bb[3] - bb[1] + 8
    px, py = (x, y) if anchor == "lt" else (x - bw, y - bh)
    px = max(0, min(px, d._image.width - bw))          # 防溢出画布
    py = max(0, min(py, d._image.height - bh))
    lay = Image.new("RGBA", (bw, bh), BG_BADGE)
    d._image.paste(lay, (px, py), lay)
    d.text((px + 8 - bb[0], py + 4 - bb[1]), text, font=f, fill=FG)


def build_sheets(rows):
    os.makedirs(D_SHEET, exist_ok=True)
    for fn in os.listdir(D_SHEET):
        if fn.endswith(".png"):
            os.remove(os.path.join(D_SHEET, fn))
    per = COLS * ROWS
    K = int(math.ceil(len(rows) / per))
    paths = []
    for k in range(K):
        chunk = rows[k * per:(k + 1) * per]
        nrow = int(math.ceil(len(chunk) / COLS))
        H = MARGIN + HEAD + nrow * CH + (nrow - 1) * GAP + MARGIN
        sh = Image.new("RGB", (SHEET_W, H), BG)
        d = ImageDraw.Draw(sh)
        d.text((MARGIN + 4, MARGIN + 6),
               u"CG 候选集 · 新顺序  sheet %02d / %02d   ｜   新 ID %03d\u2013%03d"
               % (k + 1, K, chunk[0]["nid"], chunk[-1]["nid"]), font=font(34), fill=FG)
        d.text((MARGIN + 4, MARGIN + 46),
               u"共 %d 栏 ｜ 格内=该栏代表图 ｜ 左上角=新 ID，右下角=差分总数（形如 N/N，仅差分>1 的栏才画；并入项的差分计入 N）"
               % len(rows), font=font(20), fill=FG_DIM)

        for j, r in enumerate(chunk):
            rr, cc = divmod(j, COLS)
            x0 = MARGIN + cc * (CW + GAP)
            y0 = MARGIN + HEAD + rr * (CH + GAP)
            cell = Image.new("RGB", (CW, CH), BG_CELL)
            cd = ImageDraw.Draw(cell)
            cd.rectangle([0, 0, CW - 1, CH - 1], outline=BORDER, width=1)
            im = Image.open(os.path.join(OUT, r["rep"])).convert("RGB")
            kk = min(THUMB / im.width, THUMB / im.height)
            im = im.resize((max(1, int(round(im.width * kk))), max(1, int(round(im.height * kk)))), Image.LANCZOS)
            bx, by = (CW - im.width) // 2, (CH - im.height) // 2
            cd.rectangle([bx, by, bx + im.width - 1, by + im.height - 1], fill=(10, 10, 12))
            cell.paste(im, (bx, by))
            badge(cd, bx + 5, by + 5, "%03d" % r["nid"], font(26), "lt")
            if r["n"] > 1:
                badge(cd, bx + im.width - 6, by + im.height - 6,
                      "%d/%d" % (r["n"], r["n"]), font(28), "rb")
            sh.paste(cell, (x0, y0))
        p = os.path.join(D_SHEET, "sheet_%02d.png" % (k + 1))
        sh.save(p, optimize=True)
        paths.append(p)
    return paths


def write_pending(rows, info, repmd5, cross):
    """最终待裁决 = 4 行：① 来自用户清单本身的 2 对跨栏重复（待用户定）；
    ② 2 处并入后内容重复（待用户定）。
    说明：由本次「按旧号最近补」造成的 4 对跨栏重复属预期内、用户知情 ⇒ 不进本表（见 校验.txt 附 B）。"""
    p = os.path.join(OUT, "待裁决.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow([u"类别", u"旧ID", u"组名", u"差分件数", u"尺寸", u"事项", u"说明"])
        # ① 来自用户清单本身的跨栏重复
        for h, slotset, from_fill in cross:
            if from_fill:
                continue                                   # 预期内，用户知情 ⇒ 不进待裁决
            ns_ = sorted(slotset)
            who = u" 与 ".join(u"新 %03d（旧 %03d）" % (n, rows[n - 1]["oid"]) for n in ns_)
            last = rows[ns_[-1] - 1]
            w.writerow([u"待裁决·跨栏重复", "%03d" % last["oid"], last["name"], last["n"],
                        info[last["oid"]]["size"], PENDING_STATUS,
                        u"%s 两栏代表图逐字节相同（md5=%s…）。该重复来自用户清单本身"
                        u"（用户的并入未覆盖到），非本次补位造成。用户 2026-09-24 回「其他都没有问题」"
                        u"⇒ 按现状保留、不再处理。" % (who, h[:16])])
        # ② 并入后内容重复
        for mem, nid, note in (
                (106, 284, u"新 284 的并入成员 106 e_yy_10，其差分 e_yy_10a.png 与同栏既有成员 348 yy_10 的差分逐字节相同（同栏内重复差分）"),
                (77, 198, u"新 198 的并入成员 077 e_ai_06，其差分 e_ai_06a.png 与 新 197 主件 006 ai_06 的差分逐字节相同（相邻栏重复差分）")):
            w.writerow([u"待裁决·并入重复", "%03d" % mem, info[mem]["name"], info[mem]["n"],
                        info[mem]["size"], PENDING_STATUS,
                        note + u"。判断依据：这说明 077/106 并非「独有内容」，而是与 197/284 已有内容重复 ——"
                               u"主代理原先按「代表图 md5」判它们无孪生，口径偏窄（其孪生关系在差分层面）。"
                               u"用户 2026-09-24 回「其他都没有问题」⇒ 按现状保留、不再处理。"])
    return p


# ---------------------------------------------------------------- main
def main():
    """默认全量重出；`--no-sheets` 只重写 映射.tsv / 校验.txt / 待裁决.tsv，
    不动 接触印相表\\（删除项与备注口径变化不影响栏位内容时用，省掉 32MB 重写）。"""
    os.makedirs(OUT, exist_ok=True)
    no_sheets = "--no-sheets" in sys.argv
    by, info, rep, repmd5 = load()
    slots, deleted_user = parse_userlist()
    slots = apply_spec(slots)
    pre_slots = {k: [v[0], list(v[1])] for k, v in slots.items()}      # 迁移前快照
    slots, orig_of = apply_move(slots)

    L, sets, cross = verify(slots, info, deleted_user, pre_slots, orig_of)
    rows = build_rows(slots, info, rep, orig_of)

    pm = write_map(rows)
    pv = write_move_table(rows)
    if no_sheets:
        sheets = sorted(glob.glob(os.path.join(D_SHEET, "sheet_*.png")))
        print(u"[--no-sheets] 保留既有 接触印相表（%d 张），不重写" % len(sheets))
    else:
        sheets = build_sheets(rows)
    pp = write_pending(rows, info, repmd5, cross)

    L.append(u"")
    L.append(u"=== 产物 ===")
    L.append(u"映射.tsv            %s（数据行 %d，含「原新ID」对照列）" % (pm, len(rows)))
    L.append(u"位置迁移表.tsv      %s（数据行 %d，新ID ← 原新ID 逐行）" % (pv, len(rows)))
    L.append(u"接触印相表          %d 张：%s" % (len(sheets), u"、".join(os.path.basename(x) for x in sheets)))
    L.append(u"待裁决.tsv          %s（4 行，均「%s」⇒ 可执行待裁决项 = 0）" % (pp, PENDING_STATUS))
    L.append(u"校验.txt            本文件")
    L.append(u"")
    L.append(u"注：因最后一步「取出后插入」位移，新 ID 不再等于用户清单的新 ID；映射.tsv 的「原新ID」列"
             u"即用户清单的新 ID，可用它反查用户原顺序（逐行对照另见 位置迁移表.tsv）。")

    with io.open(os.path.join(OUT, "校验.txt"), "w", encoding="utf-8") as f:
        f.write(u"\n".join(L) + u"\n")

    print(u"栏位 %d ｜ 主件 %d ｜ 并入 %d ｜ 删除 %d ｜ 待裁决 %d ｜ 合计 %d"
          % (len(rows), len(sets["main"]), len(sets["merged"]), len(sets["del"]), len(sets["pend"]),
             len(sets["main"]) + len(sets["merged"]) + len(sets["del"]) + len(sets["pend"])))
    print(u"接触印相表 %d 张" % len(sheets))
    print(u"映射 -> %s" % pm)
    print(u"校验 -> %s" % os.path.join(OUT, "校验.txt"))
    print(u"待裁决 -> %s" % pp)
    print(u"DONE")


if __name__ == "__main__":
    main()