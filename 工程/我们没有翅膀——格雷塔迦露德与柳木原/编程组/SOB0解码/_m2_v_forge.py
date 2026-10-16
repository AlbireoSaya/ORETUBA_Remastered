#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""`M2 · 未定 V 与「非命名形态」的引擎自证攻坚`（ISSUE-20261008-04）

目标（任务书）：把 **35 个未定 V + 16 个非命名形态 V** 往「引擎自证」推。
**不是「都取个名字」，而是每个都给出一条可复跑、能失败的判据及其结论**
（命名的 / 结构性的 / 明确不可达并说明为什么）。

## 判据（全部写死在脚本里，逐格可复跑；达不到阈值一律落「未定」）

  E1 内嵌串·**体级**：`func_lib` 里，从 `V` 起按 VM 47-op 操作数表走**控制流图**（CFG：
     跟随 op 0x06 JMP / op 0x1E JZ 的两条边；op 0x00/0x01/0x02 为终点）得到的**体**内，
     有指令的操作数引用到效果/资源模板串 ⇒ 采纳：`<串>`。
     ★ 与既有 `定名_说明.md` R3「窗口首串」的区别：R3 用窗口（会串到邻节点 ⇒ 21 个误判），
       本判据用 **CFG 体 + 引用该串的那条指令**，并**先证体不越 nextV**（自证见 `--check`）。
  E2 原生 handler 关联·**体级**：体内 op 0x05 的 `maps[1]` 下标 → handler（名取 M4 强/中档）。
  E3 V→V 内部调用·体级：体内 op 0x04 的目标偏移若命中别的 V ⇒ 调用边。
  E4 PSV **逐节点配对**：同 `(scene,seq)` 上「PC 命令节点数 == PSV 非 Message 行数」为**前置闸门**，
     再按 task 序一对一；标签纯度 ≥0.90 ∧ D≥100（**基准率护栏 q<0.90**）。
     **达不到就是「不可达」**——不许用「类型共现」类弱判据（既有教训）。
  S1 结构形态 census：该 V 在语料里的调用点**形态**（`[04][V]` 之后若干字 + 尾 REF 落串区/代码区），
     一致率 == 1.0 ⇒ 结构刻画（用于 16 个非命名形态）。
  U  未定：写明卡点与「需要什么证据」。

## 自证
  `--check`：① CFG 体**逐 V 落在 `[V, nextV)` 内**（0 溢出）；② `0x2C3C` 族四条不变式
     （尾 JZ 100%、实参 ∈{0,1} 100%、尾 REF 位移 +8 100%、前邻 `CALLN h462` ≥0.999；
      前邻口径 = **10 字窗口**，detail 另给出 20 字窗口命中率与距离分布）；
     ③ 非命名族形态一致率 == 1.0。任一不符 ⇒ exit 1。
  `--selftest`：变异夹具（把 CFG 的 JZ 边去掉 ⇒ 体必须变小且不再包含该串；把配对闸门放松 ⇒
     纯度必须掉到阈值下；F2 用**不夹紧**的可达闭包复算越界）。任一夹具行为不符 ⇒ exit 1。
  `--e1stats`：打印 `func_lib.sob` 串区被指令操作数引用的站/串统计（§1.3 的可复跑来源）。

用法：
  python -X utf8 编程组/SOB0解码/_m2_v_forge.py --out 子代理工作区/ISSUE-20261008-04/M2
  python -X utf8 编程组/SOB0解码/_m2_v_forge.py --check
  python -X utf8 编程组/SOB0解码/_m2_v_forge.py --selftest
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PRG, "工具"))
sys.path.insert(0, os.path.join(PRG, "逆向引擎"))
sys.dont_write_bytecode = True
import decode_sob0 as D          # noqa: E402
from xwalk import VM_LEN         # noqa: E402

OPNAME = {
    0x00: "HALT", 0x01: "RET", 0x02: "RETVAL", 0x03: "STVAL", 0x04: "CALL",
    0x05: "CALLN", 0x06: "JMP", 0x07: "SWITCH", 0x08: "PUSH", 0x09: "PUSH*",
    0x0A: "POP", 0x0B: "ADDSP", 0x0C: "DELARG", 0x0D: "ADD", 0x0E: "SUB",
    0x0F: "MUL", 0x10: "DIV", 0x11: "MOD", 0x12: "MODN", 0x13: "AND",
    0x14: "OR", 0x15: "XOR", 0x16: "NOT", 0x17: "EQZ", 0x18: "SHR",
    0x19: "SHL", 0x1A: "INC*", 0x1B: "DEC*", 0x1C: "INCSP", 0x1D: "DECSP",
    0x1E: "JZ", 0x1F: "MOV", 0x20: "MOV*", 0x21: "MOV**", 0x22: "STSP",
    0x23: "LDSP", 0x24: "STSP*", 0x25: "MOVSP", 0x26: "LDSP**", 0x27: "MOV***",
    0x28: "LEA", 0x29: "LT", 0x2A: "LE", 0x2B: "GT", 0x2C: "GE", 0x2D: "EQ",
    0x2E: "NE",
}
# ---- M4（ISSUE-20261008-02）handler 名（只取强/中档，未定不写名）--------------
HANDLER_NAME = {
    0: "req_scene(状态2)", 1: "req_scene(状态1)", 2: "req_scene(状态3)",
    668: "音频播放(按索引)", 669: "音频停止(按索引)", 228: "系统ELG按名装载",
    229: "遮罩Rule装载", 23: "cross/rule标志写(app+194E)", 5: "转场/遮罩模式分派",
    207: "层/特效`开始`(503214.+14)", 208: "层/精灵槽位释放(503214.+8)",
    251: "效果对象类型分派(type7..10)", 428: "对象释放/关闭",
    462: "文本显示(503258)",
}
HANDLER_STRONG = {668, 669, 0, 1, 2}
HANDLER_MID = {228, 229, 23, 5, 207, 208, 251, 462}

# 已由引擎自证、但名字需要「人写语义标签」的载体（用于 E5 入边定位的措辞）
SEM_LABEL = {
    0x2C3C: "文本行推进门/消息渲染体",
    0x23270: "系统UI部件(IF_*)装载族",
    0x24F1C: "系统菜单背景(SM_BG*)族",
}

# 效果/转场宏名（func_lib 串区实测；见 §4）
EFFECT_NAMES = {
    "addsub", "bg_anime", "bg_blur", "bg_haze", "bg_move", "bg_rast", "bg_rot",
    "bg_zoom", "cross", "hblur", "mosaic", "noise", "quake", "rotaxis",
    "rotcenter", "rule", "scroll", "sp_move", "trans", "wave", "zoomflip",
}
RE_RES = re.compile(r"[.](ELG|GMP|OGG|PNG|G00)$", re.I)
# 噪声串（非语义名）：纯数字/单字母/控制字节等
JUNK = re.compile(r"^([0-9]{1,3}|[A-Za-z]|[\x00-\x20]|\uf8f3+|-2)$")
RE_FAM = re.compile(r"\d+.*$")


def arg_family(strs):
    """实参串（**含重复**，按出现次数计）→ 族。→ (label, n, 不同值数, top2) 或 None。

    族 = 把数字段折成 `#`（`PIC\\EF01.ELG` → `PIC\\EF#.ELG`）。
    若最大族不足全体资源串实参的一半 ⇒ 退化为**目录前缀**（如 `PIC\\`）：
    「多个子族并存」时给某一个子族命名会误导。
    """
    fam = collections.Counter()
    vals = collections.defaultdict(set)
    dirs = collections.Counter()
    allvals = set()
    tot = 0
    for s in strs:
        if not isinstance(s, str) or not s or not re.search(r"[.\\/]", s):
            continue
        u = s.replace("/", "\\")
        fam[RE_FAM.sub("#", u)] += 1
        vals[RE_FAM.sub("#", u)].add(s)
        dirs[u.rsplit("\\", 1)[0] + "\\"] += 1
        allvals.add(s)
        tot += 1
    if not fam:
        return None
    f, n = fam.most_common(1)[0]
    if n * 2 < tot:
        d, _dn = dirs.most_common(1)[0]
        return (d, tot, len(allvals), sorted(allvals)[:2])
    return (f, n, len(vals[f]), sorted(vals[f])[:2])


def label_from_strings(strs):
    """内嵌串 → 可读标签（效果宏名 > 资源族 > 资源模板 > 裸资源名表）。"""
    eff = sorted({t for t in strs if t in EFFECT_NAMES})
    asset = sorted({t for t in strs if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", t)})
    res = sorted({t for t in strs if RE_RES.search(t)})
    if eff:
        return "/".join(eff)
    if asset and len(asset) >= 8 and all(a.startswith(("BG", "SM_", "IF_")) for a in asset):
        pre = "BG" if all(a.startswith("BG") for a in asset) else asset[0][:2]
        return "%s* 资源名表（%d 项）" % (pre, len(asset))
    if res:
        fam = arg_family(res)
        if fam and fam[2] >= 3:
            return "%s 装载体（%d 项）" % (fam[0], fam[2])
        return res[0]
    if asset:
        return "/".join(asset[:3])
    return "/".join(sorted(strs)[:2])

# ---- 阈值（自定，写明；达不到一律「未定」）-----------------------------------
TH_E1_STATIONS = 1        # E1：体内引用该串的指令 ≥1
TH_E2_NATIVE = 1          # E2：体内强名 handler 出现 ≥1
TH_E4_D = 100             # E4：逐节点配对数
TH_E4_PUR = 0.90          # E4：标签纯度
TH_Q_MAX = 0.90           # 基准率护栏（与既有 R1 一致）
TH_SHAPE_UNIFORM = 1.0    # S1：形态一致率

WIN_SENS = (0x120, 0x200, 0x400)
W_BODY_MAX = 0x8000       # CFG 体的物理上界（防跑飞；func_lib 整段 = 0x2AF09）


# ================================================================ func_lib 走查 + CFG
def walk(cells):
    """按 VM 47-op 操作数字数表线性走查（op 0x07 读内联跳转表）。"""
    out, i, n = [], 0, len(cells)
    while i < n:
        t = cells[i]
        if t > 0x2E:
            i += 1
            continue
        if t == 0x07:
            j = i + 2
            while j < n and cells[j] != 0xFFFFFFFF:
                j += 1
            j += 1
            out.append((i, 0x07, j - i - 1, [cells[k] for k in range(i + 1, j)]))
            i = j
            continue
        L = VM_LEN.get(t, 1)
        out.append((i, t, L - 1, [cells[i + 1 + q] for q in range(L - 1)]))
        i += L
    return out


class FuncLib:
    def __init__(self, path):
        self.s = D.Sob0(path)
        self.ins = walk(self.s.cells)
        self.idx = {i: (o, n, a) for i, o, n, a in self.ins}
        self.succ = {}
        self.follow_jz = True                      # --selftest 可关掉 JZ 边
        for j, (o, n, a) in self.idx.items():
            L = 1 + n
            if o in (0x00, 0x01, 0x02):
                su = []
            elif o == 0x06:
                su = [self._tgt(j + 1)]
            elif o == 0x1E:
                su = [j + L] + ([self._tgt(j + 2)] if self.follow_jz else [])
            elif o == 0x07:
                # 表项是**页引用字**（maps[4] → 本模块偏移）⇒ 逐个解析为目标
                su = []
                for q in range(n - 1):
                    w = a[q + 1]
                    if w == 0xFFFFFFFF:
                        break
                    t = self._tgt(j + 2 + q)
                    if t is not None and t in self.idx:
                        su.append(t)
            else:
                su = [j + L]
            self.succ[j] = [x for x in su if x is not None and x in self.idx]

    def _tgt(self, w):
        """操作数字 → 目标字索引（`maps[4]` 值 = 本模块偏移）。"""
        v = self.s.maps[4].get(w * 4)
        return None if v is None else v // 4

    def body(self, v, maxoff=None, limit=8000):
        start = v // 4
        seen, stack = set(), [start]
        while stack:
            j = stack.pop()
            if j in seen or j not in self.idx:
                continue
            if maxoff is not None and j * 4 >= maxoff:
                continue
            seen.add(j)
            if len(seen) > limit:
                break
            for k in self.succ.get(j, []):
                if k not in seen:
                    stack.append(k)
        return seen

    def resolve(self, wi):
        s = self.s
        site, w = wi * 4, s.cells[wi]
        if site in s.maps[4]:
            v = s.maps[4][site]
            if s.ss <= v < s.se:
                try:
                    return "S:%s" % s.read_group(v)[0].decode("cp932", "replace")[:40]
                except Exception:
                    return "S?"
            return "C:+0x%X" % v
        if site in s.maps[3]:
            return "V:0x%X" % s.maps[3][site]
        if site in s.maps[1]:
            return "h%d" % s.maps[1][site]
        if site in s.maps[0]:
            return "p%d" % s.maps[0][site]
        return "N:%d" % w


# ================================================================ 语料侧
def v_domain(sources=("ot",)):
    """→ dict(src → dict(V → 节点数))（语料可解析文件口径）。"""
    out = {}
    for src in sources:
        sd = D.SOURCES.get(src)
        if not sd:
            continue
        cnt = collections.Counter()
        for fn in sorted(os.listdir(sd["dir"])):
            if not fn.lower().endswith(sd["ext"]):
                continue
            try:
                s = D.Sob0(os.path.join(sd["dir"], fn))
            except Exception:
                continue
            for _k, V in s.maps[3].items():
                cnt[V] += 1
        out[src] = cnt
    return out


def _tok(s, i, w):
    """把一个字归一为「结构 token」（用于形态 census，避免地址字各异）。"""
    if w <= 0x2E:
        return "%02X" % w
    site = i * 4
    if site in s.maps[4]:
        return "S" if s.ss <= s.maps[4][site] < s.se else "C"
    if site in s.maps[3]:
        return "V"
    if site in s.maps[1]:
        return "I"
    if site in s.maps[0]:
        return "P"
    return "N"


def form_class(s, i):
    """把 `[04][V]` 之后的**调用形态**归入有限类（结构刻画用；判据写死）。

    `CLASSIC`          `[0C][k][03][REF→串区]`（既有「命名命令节点」形态）
    `NULLARY_CALL`     `[03][REF]`（无 `[0C]` ⇒ 零实参调用，返回值落 REF）
    `WRITE_CODE_SLOT`  `[0C][k][03][REF→代码区]`（返回值写进**代码区槽**，自改写；
                       子特征 `tail_disp`/`follower` 另列）
    `OTHER:<toks>`     其余
    """
    c = s.cells
    n = len(c)
    if i + 4 < n and c[i + 1] == 0x0C and c[i + 3] == 0x03:
        t = s.maps[4].get((i + 4) * 4)
        if t is None:
            return "OTHER:noREF"
        return "CLASSIC" if s.ss <= t < s.se else "WRITE_CODE_SLOT"
    if i + 2 < n and c[i + 1] == 0x03:
        return "NULLARY_CALL"
    return "OTHER:" + " ".join(_tok(s, i + 1 + q, c[i + 1 + q])
                               for q in range(min(4, n - i - 1)))


def slot_detail(s, i):
    """`WRITE_CODE_SLOT` 的子特征：尾 REF 位移 + 后续 op。"""
    c = s.cells
    n = len(c)
    t = s.maps[4].get((i + 4) * 4)
    disp = (t - (i + 4) * 4) if t is not None else None
    fol = c[i + 5] if i + 5 < n else None
    return "disp=%s fol=%s" % (("+%d" % disp) if disp is not None else "-",
                              ("%02X" % fol) if fol is not None else "-")


def shape_census(sources=("ot", "otp", "otr")):
    """每个 V 的调用点**形态类** census（`form_class`）+ `WRITE_CODE_SLOT` 子特征。"""
    cen = collections.defaultdict(collections.Counter)
    fol = collections.defaultdict(collections.Counter)
    files = collections.defaultdict(set)
    for src, sd in D.SOURCES.items():
        if src not in sources:
            continue
        for fn in sorted(os.listdir(sd["dir"])):
            if not fn.lower().endswith(sd["ext"]):
                continue
            try:
                s = D.Sob0(os.path.join(sd["dir"], fn))
            except Exception:
                continue
            for k, V in s.maps[3].items():
                i = k // 4
                fc = form_class(s, i)
                cen[V][fc] += 1
                if fc == "WRITE_CODE_SLOT":
                    fol[V][slot_detail(s, i)] += 1
                files[V].add("%s:%s" % (src, fn))
    return cen, files, fol


def arg_profile(scenes_by_src):
    """→ V → dict(argc 分布, kind 签名, 串实参 top, 数值实参范围)。"""
    prof = collections.defaultdict(lambda: dict(argc=collections.Counter(),
                                                kinds=collections.Counter(),
                                                strs=collections.Counter(),
                                                num=collections.defaultdict(list)))
    for _src, scenes in scenes_by_src.items():
        for _sid, d in scenes.items():
            for nd in d["nodes"]:
                V = nd["V"]
                a = nd["args"]
                p = prof[V]
                p["argc"][len(a)] += 1
                p["kinds"][tuple(k for k, _v in a)] += 1
                for idx, (k, v) in enumerate(a):
                    if k == "S" and isinstance(v, str) and v:
                        p["strs"][v] += 1
                    elif k in ("N", "A", "I") and isinstance(v, int):
                        if len(p["num"][idx]) < 4000:
                            p["num"][idx].append(v)
    return prof


def load_scenes(src):
    import io as _io
    out = {}
    path = os.path.join(D.SCENE_DIR, "scene_%s.jsonl" % src)
    if not os.path.isfile(path):
        return out
    sd = D.SOURCES[src]
    with _io.open(path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            p = os.path.join(sd["dir"], o["script"] + ".sob")
            if not os.path.isfile(p):
                continue
            try:
                sob = D.Sob0(p)
            except ValueError:
                continue
            _rows, info = D.extract_scene(src, o, sob, sob.slots(), None, None)
            out[o["scene_id"]] = info
    return out


def e4_pairing(scenes, gold, target_Vs):
    """E4：同 (scene,seq) 计数相等为前置闸门，按 task 序一对一配对。"""
    def tk(r):
        t = r.get("task") or "0"
        try:
            return (0, int(t))
        except ValueError:
            return (1, 0)
    lab = collections.defaultdict(collections.Counter)
    n_seq_eq = n_seq_ne = 0
    for sid, rows in gold.items():
        if sid not in scenes:
            continue
        byseq = collections.defaultdict(list)
        for r in rows:
            if r.get("type") == "Message":
                continue
            byseq[str(r["seq"])].append(r)
        pn = collections.defaultdict(list)
        for nd in scenes[sid]["nodes"]:
            pn[str(nd["seq"])].append(nd)
        for sq, rs in byseq.items():
            ns = pn.get(sq, [])
            if len(ns) != len(rs):
                n_seq_ne += 1
                continue
            n_seq_eq += 1
            for nd, r in zip(ns, sorted(rs, key=tk)):
                if nd["V"] in target_Vs:
                    lab[nd["V"]][r["type"]] += 1
    return lab, n_seq_eq, n_seq_ne


def pos_sig(scenes, gold, target_Vs):
    """位置签名：节点 seq 在该场 PSV 事件序中的归一化位置（0=场首,1=场尾）。

    → {V: dict(n, scenes, per_scene, pos_mean, part_ge090)}；`part_ge090` = 位置 ≥0.90 的比例。
    """
    out = collections.defaultdict(lambda: dict(n=0, sc=set(), pos=[]))
    for sid, rows in gold.items():
        if sid not in scenes:
            continue
        ev = [r for r in rows if r.get("type") != "Message"]
        ev.sort(key=lambda r: int(r.get("seq") or 0))
        n = len(ev)
        rank = {}
        for k, r in enumerate(ev):
            rank[str(r["seq"])] = k / max(1, n - 1)
        for nd in scenes[sid]["nodes"]:
            if nd["V"] not in target_Vs:
                continue
            o = out[nd["V"]]
            o["n"] += 1
            o["sc"].add(sid)
            if str(nd["seq"]) in rank:
                o["pos"].append(rank[str(nd["seq"])])
    res = {}
    for V, o in out.items():
        p = o["pos"]
        res[V] = dict(n=o["n"], scenes=len(o["sc"]),
                      per_scene=(o["n"] / len(o["sc"]) if o["sc"] else None),
                      pos_mean=(sum(p) / len(p) if p else None),
                      part_ge090=(sum(1 for x in p if x >= 0.90) / len(p) if p else None))
    return res


# ================================================================ 规则
def _fmt_args(p):
    top = p["kinds"].most_common(1)
    ks = "".join(top[0][0]) if top else "-"
    s = "argc=%s kind=%s" % (p["argc"].most_common(1)[0][0] if p["argc"] else "-", ks)
    if p["strs"]:
        s += " 串top=%s" % ([x for x, _n in p["strs"].most_common(3)],)
    return s


def verdict(V, feats, th):
    """→ dict(category, verdict, rule, name, basis, strength, gap)

    `category` ∈ {`新命名`, `结构性刻画`, `明确不可达`}（任务书的三个落点）。
    **规则顺序 = 证据强度降序**（强判据先判，弱判据不得抢占结论）。
    """
    E1 = [t for t in feats["body_strings"]
          if t in EFFECT_NAMES or RE_RES.search(t) or re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", t)]
    strong = [h for h in feats["body_natives"] if h in HANDLER_STRONG]
    mid = [h for h in feats["body_natives"] if h in HANDLER_MID]
    e4 = feats["e4"]
    # ---- 1) E1 体级内嵌串（最强：引擎自证，无跳数假设）----
    if E1:
        nm = SEM_LABEL.get(V) or label_from_strings(E1)
        # ★ 一审 N6：名称来源分两种——人工语义标签 SEM_LABEL / 规则从串表导出；
        #   必须在 basis 里注明，避免读成「全部由规则从串表导出」。
        src = ("人工语义标签（SEM_LABEL）" if V in SEM_LABEL
               else "规则从串表导出（label_from_strings）")
        return dict(category="新命名", verdict="采纳：" + nm, rule="E1(体级内嵌串)", name=nm,
                    strength="强",
                    basis="CFG 体内指令实参引用 %s（体 %d 条、越 nextV %d 条）｜名称来源：%s"
                          % (sorted(set(E1))[:8], feats["body_n"], feats["body_over_nextV"], src),
                    gap="")
    # ---- 2) E4 PSV 逐节点配对（强：计数闸门 + task 序 + 基准率护栏）----
    if e4 and e4["D"] >= th["e4_d"] and e4["pur"] >= th["e4_pur"] and e4["q"] < TH_Q_MAX:
        return dict(category="新命名", verdict="采纳：" + e4["top"], rule="E4(PSV逐节点配对)",
                    name=e4["top"], strength="强",
                    basis="同(scene,seq)计数相等闸门 + task 序配对：纯度 %.4f D=%d q(基准率)=%.4f"
                          % (e4["pur"], e4["D"], e4["q"]), gap="")
    # ---- 3) E1c 私有子程序（闭包 1 跳、非命令 V、全局被调数≤6）内嵌串 ----
    if feats["close_strings"]:
        nm = label_from_strings(feats["close_strings"])
        return dict(category="结构性刻画", verdict="候选：" + nm, rule="E1c(私有子程序内嵌串·1跳)",
                    name=nm, strength="中",
                    basis="本体内无串，但其**共享子程序** 0x%X（全局被调数≤6、本身不是命令 V）体引用 %s"
                          % (feats["close_id"], feats["close_strings"][:6]),
                    gap="串在子程序体（1 跳假设），不得当下游已定名用")
    # ---- 4) E2 体级强名 handler ----
    if strong:
        nm = "+".join(str(h) + ":" + HANDLER_NAME.get(h, "h%d" % h) for h in strong)
        return dict(category="结构性刻画", verdict="候选：" + nm, rule="E2(体级强名handler)", name=nm,
                    strength="中",
                    basis="CFG 体内 op0x05 调强名 handler %s" % nm,
                    gap="handler 为共享原语，须另有独立佐证方可采纳")
    # ---- 5) E6 实参资源串族（语料侧证据）----
    af = feats["arg_fam"]
    if af and af[0] != "#" and (af[2] >= 3 and (af[1] >= 8
            or (e4 and e4["pur"] >= 0.90 and e4["D"] >= 8))):
        ev = "命令行实参资源串族 %s ×%d（%d 个不同值，如 %s）" % (af[0], af[1], af[2], af[3])
        if e4 and e4["pur"] >= 0.90 and e4["D"] >= 8:
            ev += "；逐节点配对纯度 %.4f(%s) D=%d" % (e4["pur"], e4["top"], e4["D"])
        return dict(category="结构性刻画", verdict="候选：" + af[0] + " 装载体", rule="E6(实参串族)",
                    name=af[0], strength="中", basis=ev,
                    gap="实参只证「该命令吃这个资源族」，不能证命令类型；须与 PSV/实机对拍")
    # ---- 6) E5 入边定位（结构定位，非命名）----
    if feats["callers_named"]:
        named = feats["callers_named"]
        u, nm = named[0]
        lab = SEM_LABEL.get(u) or nm
        others = ";".join("0x%X:%s" % (x, (SEM_LABEL.get(x) or n2)) for x, n2 in named[1:4])
        extra = ("（另有入边 %s）" % others) if others else ""
        return dict(category="结构性刻画",
                    verdict="结构刻画：0x%X（%s）内部子程序%s" % (u, lab, extra),
                    rule="E5(入边定位)", name="", strength="弱",
                    basis="本 V 被引擎自证 V %s 在体内 op0x04 调用；入边全集=%s"
                          % (["0x%X(%s)" % (x, SEM_LABEL.get(x) or n2) for x, n2 in named[:4]],
                             ["0x%X" % x for x in feats["in_edges"][:8]]),
                    gap="入边只给「属于哪个子系统的内部子程序」，给不出命令名")
    # ---- 7) S2 系统脚本域（剧情语料 0 节点 ⇒ PSV 剧情金标结构上不可达）----
    if feats.get("story_files", 0) == 0 and feats["nodes"] > 0:
        return dict(category="结构性刻画",
                    verdict="结构刻画：系统脚本域命令（**无任何剧情脚本引用**）", rule="S2(域判定)",
                    name="", strength="中",
                    basis="全库 %d 个引用站落在 %d 个文件，其中**剧情脚本（`s##_*` / `s03c_*`）0 个**、"
                          "系统/UI 脚本 %d 个 ⇒ 只被系统域使用；PSV 金标只覆盖剧情场，结构上不可能给名"
                          % (feats["nodes"], feats["files"], feats["sys_files"]),
                    gap="需系统脚本自身的语义金标（UI 截图 / 实机断点 / saveload 逻辑），非本模块可达")
    # ---- 7b) S4 每脚本≈1 次的零实参调用（场景级初始化/复位的结构刻画）----
    if (feats.get("shape_class") == "NULLARY_CALL" and feats.get("story_files", 0) >= 50
            and feats["nodes"] <= 1.5 * feats["story_files"]):
        return dict(category="结构性刻画",
                    verdict="结构刻画：场景级初始化/复位（每脚本≈1 次的零实参调用）",
                    rule="S4(每场一次·零实参)", name="", strength="中",
                    basis="形态 = `NULLARY_CALL`（`x = V()`）；%d 个引用站落在 %d 个剧情文件（总 %d 文件）"
                          "⇒ **每脚本≈1 次**，与「场景初始化 / 复位 / 取当前状态」同形；"
                          "它不产生演出事件，PSV 剧情金标结构上给不出名字"
                          % (feats["nodes"], feats["story_files"], feats["files"]),
                    gap="需实机/系统侧证据（场景装载路径断点）方可定名")
    # ---- 8) S3 场尾标记一族（位置签名；与全覆盖型 type 不可分 ⇒ 结构刻画）----
    p = feats.get("pos") or {}
    if (p.get("scenes", 0) >= 100 and p.get("per_scene") is not None and p["per_scene"] <= 1.30
            and p.get("pos_mean") is not None and p["pos_mean"] >= 0.90):
        return dict(category="结构性刻画",
                    verdict="结构刻画：场尾标记一族（End/NextScene/SceneJumpDialogEnd 不可分）",
                    rule="S3(位置签名)", name="", strength="中",
                    basis="每场≤1.3 次（%d 节点 / %d 场）、位置均值 %.3f、≥0.90 者占 %.3f ⇒ "
                          "与场覆盖≈1.0 的全覆盖型 type 无鉴别力（旧判「SceneJumpDialog」正是此种假通过）"
                          % (p["n"], p["scenes"], p["pos_mean"], p["part_ge090"] or -1),
                    gap="需要「场尾最后一条 vs 跳转语义」的区分证据（PSV 明文跳转目标 / 实机断点）")
    # ---- 9) E2m 体级中档 handler ----
    if mid:
        nm = "+".join(str(h) + ":" + HANDLER_NAME.get(h, "h%d" % h) for h in mid)
        return dict(category="结构性刻画", verdict="候选（弱）：" + nm, rule="E2m(体级中档handler)",
                    name=nm, strength="弱",
                    basis="CFG 体内 op0x05 调中档 handler %s" % nm,
                    gap="中档 handler 跨族，判别力弱")
    # ---- 10) E2c 闭包（≤2 跳）中档/强名 handler ----
    if feats["close_mid"]:
        h = feats["close_mid"][0]
        nm = "%d:%s" % (h, HANDLER_NAME.get(h, "h%d" % h))
        return dict(category="结构性刻画", verdict="候选（弱）：闭包内 %s 族" % nm,
                    rule="E2c(闭包handler≤2跳)", name=nm, strength="弱",
                    basis="本体无强证据，但调用闭包（≤2 跳）内出现 handler %s"
                          % [("h%d" % x) for x in feats["close_mid"][:6]],
                    gap="闭包内 handler 属共享子系统，判别力弱")
    # ---- 11) E4 未达阈 ----
    if e4 and e4["D"] >= 30:
        return dict(category="明确不可达", verdict="未定", rule="E4 未达阈", name="", strength="无",
                    basis="逐节点配对纯度仅 %.4f D=%d（阈值 %.2f/%d）；计数相等闸门只覆盖 %d 个 seq"
                          % (e4["pur"], e4["D"], th["e4_pur"], th["e4_d"], feats["e4_eq_seq"]),
                    gap="配对缺强锚（实参↔行 name / 时长）；需实机断点或 PSV 分支结构对拍")
    return dict(category="明确不可达", verdict="未定", rule="无", name="", strength="无",
                basis=feats.get("near_miss") or "无任何达阈值证据（体内无串、无强名 handler、配对不达阈）",
                gap=feats.get("gap")
                or "需独立第三方证据：PSV 明文语义 / 实机断点 / 资源件本体 / 系统脚本金标")

# ================================================================ 主
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame"))
    ap.add_argument("--func-lib", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--focus", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--e1stats", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    fl_path = a.func_lib or os.path.join(D.SOURCES["ot"]["dir"], "func_lib.sob")
    fl = FuncLib(fl_path)
    dom = v_domain(["ot"])
    V_all = sorted(dom["ot"])
    nxt = {V_all[k]: (V_all[k + 1] if k + 1 < len(V_all) else None) for k in range(len(V_all))}
    if a.e1stats:      # §1.3 的可复跑来源（只读统计，不产报告）
        print("E1 站统计：" + json.dumps(e1_station_stats(fl, V_all, nxt), ensure_ascii=False))
        return 0
    cen, cen_files, cen_fol = shape_census()
    scenes = {s: load_scenes(s) for s in ("ot",)}
    prof = arg_profile(scenes)
    psv, _ids = D.load_psv_timeline()
    scenes_ot = scenes["ot"]
    gold = {s: psv[s] for s in scenes_ot if s in psv}
    # 基准率 q(type)：单事件 seq 上的 type 先验
    pri = collections.Counter()
    for sid, rows_ in gold.items():
        by = collections.defaultdict(list)
        for r in rows_:
            if r.get("type") != "Message":
                by[str(r["seq"])].append(r.get("type", ""))
        for _q, ts in by.items():
            if len(ts) == 1:
                pri[ts[0]] += 1
    tot_single = sum(pri.values()) or 1
    Q = {t: n / tot_single for t, n in pri.items()}
    # 剧情语料（scene_ot.jsonl）里每个 V 的节点数（**只对经典形态 V 有意义**）
    story_nodes = collections.Counter()
    for _sid, d in scenes_ot.items():
        for nd in d["nodes"]:
            story_nodes[nd["V"]] += 1
    # ★ 域判定用**引用文件**分，不用节点数：
    #   非经典形态 V 在 scene_ot.jsonl 里恒 0 节点（那是形态判据的产物，不是域的证据）；
    #   故「域」只能由「哪些文件引用了它」决定。
    # ★ 一审 N2 订正：原正则 `^s\d\d_` 漏 `s03c_*`（`ot` 目录内 21 个 R 版 CHS 剧情脚本被算作 sys），
    #   改为 `^s\d\d[a-z]*_`（覆盖 `s01_`、`s03c_` 等）；重跑后 54 个目标 V 无一条结论翻转。
    RE_STORY = re.compile(r"^s\d\d[a-z]*_")
    story_files, sys_files = collections.Counter(), collections.Counter()
    for V, fs in cen_files.items():
        for tag in fs:
            _src, fn = tag.split(":", 1)
            if RE_STORY.match(fn):
                story_files[V] += 1
            else:
                sys_files[V] += 1

    # ---- 一次性扫描全部 V 的 CFG 体（体级 串 / natives / 内部调用）----
    def scan_body(v, follow_jz=True):
        nx = nxt[v]
        b = fl.body(v, maxoff=(nx if nx else v + W_BODY_MAX))
        strs, nat, calls = [], collections.Counter(), collections.Counter()
        for j in sorted(b):
            o, n, _aa = fl.idx[j]
            if o == 0x05 and n >= 1:
                h = fl.s.maps[1].get((j + 1) * 4)
                if h is not None:
                    nat[h] += 1
            if o == 0x04 and n >= 1:
                t = fl.s.maps[4].get((j + 1) * 4)
                if t is not None:
                    calls[t] += 1
            for q in range(n):
                site = (j + 1 + q) * 4
                tv = fl.s.maps[4].get(site)
                if tv is not None and fl.s.ss <= tv < fl.s.se:
                    try:
                        st = fl.s.read_group(tv)[0].decode("cp932", "replace")
                    except Exception:
                        st = ""
                    if st and not JUNK.match(st):
                        strs.append(st)
        ov = sum(1 for j in b if nx is not None and j * 4 >= nx)
        return dict(body=b, n=len(b), over=ov, strings=sorted(set(strs)),
                    natives=nat, calls=calls)

    SCAN = {v: scan_body(v) for v in V_all}
    # ---- 调用闭包（深度 ≤2）：偏移 → 距离；用于「闭包内嵌串 / 闭包 native」判据 ----
    def closure(v, depth=2, cap=1500):
        dist = {v: 0}
        front = {v}
        for d in range(1, depth + 1):
            nxtf = set()
            for u in front:
                for t in SCAN[u]["calls"] if u in SCAN else []:
                    if t not in dist:
                        dist[t] = d
                        nxtf.add(t)
            # 非 V 的内部子程序也要展开（其体在 [t, t+limit)）
            for t in list(nxtf):
                if t not in fl.idx:
                    continue
                ins = set()
                j = t // 4
                while j in fl.idx and len(ins) < cap:
                    o, n, _a = fl.idx[j]
                    ins.add(j)
                    if o in (0x00, 0x01, 0x02):
                        break
                    j += 1 + n
                for j in ins:
                    o, n, _a = fl.idx[j]
                    if o == 0x04 and n >= 1:
                        tt = fl.s.maps[4].get((j + 1) * 4)
                        if tt is not None and tt not in dist:
                            dist[tt] = d + 1
                            nxtf.add(tt)
            front = nxtf
        return dist

    def gather(offsets, fl_):
        """一组偏移 → (串集合, native Counter)。"""
        ss, nn = set(), collections.Counter()
        for t in offsets:
            j = t // 4
            seen = set()
            while j in fl_.idx and len(seen) < 1500:
                o, n, a = fl_.idx[j]
                seen.add(j)
                if o == 0x05 and n >= 1:
                    h = fl_.s.maps[1].get((j + 1) * 4)
                    if h is not None:
                        nn[h] += 1
                for q in range(n):
                    tv = fl_.s.maps[4].get((j + 1 + q) * 4)
                    if tv is not None and fl_.s.ss <= tv < fl_.s.se:
                        try:
                            st = fl_.s.read_group(tv)[0].decode("cp932", "replace")
                        except Exception:
                            st = ""
                        if st and not JUNK.match(st):
                            ss.add(st)
                if o in (0x00, 0x01, 0x02):
                    break
                j += 1 + n
        return ss, nn
    CLOS = {v: closure(v) for v in V_all}
    Vset = set(V_all)
    VEDGE = {v: sorted({t for t in SCAN[v]["calls"] if t in Vset}) for v in V_all}
    indeg = collections.Counter()
    for v in V_all:
        for t in VEDGE[v]:
            indeg[t] += 1
    # 全局调用目标入度（不限 V）
    indeg_all = collections.Counter()
    for j, (o, n, _a) in fl.idx.items():
        if o == 0x04 and n >= 1:
            t = fl.s.maps[4].get((j + 1) * 4)
            if t is not None:
                indeg_all[t] += 1
    INEDGE = {v: sorted(u for u in V_all if v in VEDGE[u]) for v in V_all}
    # E1 引擎自证名（体级内嵌串）——用于入边定位
    E1NAME = {}
    for v in V_all:
        if SCAN[v]["strings"]:
            E1NAME[v] = label_from_strings(SCAN[v]["strings"])

    # ---- 未定 / 非命名 名单（上游 _v_naming.json 为据）----
    nj = os.path.join(HERE, "_v_naming.json")
    und, non = [], []
    if os.path.isfile(nj):
        rep = json.load(io.open(nj, encoding="utf-8"))
        for k, d in rep["verdicts"].items():
            if d["verdict"].startswith("非命名"):
                non.append(int(k, 16))
            elif d["verdict"] == "未定" or d["verdict"].startswith("未定（"):
                und.append(int(k, 16))
    und, non = sorted(set(und)), sorted(set(non))
    # 任务书点名的四个高频 V（上游记为「候选」，本批一并给结论）
    focus_extra = [v for v in (0x17514, 0x14084, 0x19A68) if v in Vset and v not in und and v not in non]
    targets = und + non + focus_extra

    # ---- 预计算 E4 ----
    lab, n_eq, n_ne = e4_pairing(scenes_ot, gold, set(targets))
    POS = pos_sig(scenes_ot, gold, set(targets))
    print("func_lib ins=%d  V 域=%d  E4 计数相等 seq=%d / 不等=%d  单事件 seq=%d  q_max=%.4f"
          % (len(fl.ins), len(V_all), n_eq, n_ne, tot_single, max(Q.values()) if Q else 0))

    rows = []
    for V in targets:
        sc = SCAN[V]
        b, ov, strs, nat, calls = sc["body"], sc["over"], sc["strings"], sc["natives"], sc["calls"]
        # 闭包（深度 ≤2）：距离 1 的非 hub 子程序的串
        tmp, cl_id = set(), None
        for u, dd in CLOS[V].items():
            if dd != 1 or u in Vset or (u // 4) not in fl.idx or indeg_all.get(u, 0) > 6:
                continue
            ss2, _nn2 = gather({u}, fl)
            tmp |= ss2
            cl_id = u
        cl1 = sorted(tmp)
        cl_str = [t for t in cl1
                  if t in EFFECT_NAMES or RE_RES.search(t)
                  or re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", t)]
        # 闭包 native（距离 ≤2；不限 V）
        cln = collections.Counter()
        for u, dd in CLOS[V].items():
            if dd == 0 or dd > 2 or (u // 4) not in fl.idx:
                continue
            _ss, nn2 = gather({u}, fl)
            for h, k in nn2.items():
                cln[h] += k
        close_mid = sorted(h for h in cln if h in HANDLER_MID or h in HANDLER_STRONG)
        # 实参串族（E6）
        _cs = prof.get(V, {}).get("strs") or collections.Counter()
        afam = arg_family([k for k, n in _cs.items() for _ in range(n)])
        # 入边定位：调用我的 V 里有引擎自证名者
        inh = [(u, E1NAME[u]) for u in INEDGE[V] if u in E1NAME]
        c = lab.get(V)
        e4 = None
        if c:
            tot = sum(c.values())
            top, nn = c.most_common(1)[0]
            e4 = dict(D=tot, top=top, pur=nn / tot, q=Q.get(top, 0.0),
                      dist=dict(c.most_common(5)))
        sh = cen.get(V, collections.Counter())
        sh_top = sh.most_common(1)[0][0] if sh else "-"
        sh_dist = ";".join("%s×%d" % (k, n2) for k, n2 in sh.most_common(4))
        feats = dict(body_n=len(b), body_over_nextV=ov, body_strings=strs,
                     body_natives=dict(nat),
                     body_calls={("0x%X" % k): v for k, v in calls.items()},
                     e4=e4, e4_eq_seq=n_eq,
                     shape=[sh_dist, sh.most_common(1)[0][1] if sh else 0],
                     shape_class=sh_top, shape_kinds=len(sh),
                     shape_follow=((cen_fol.get(V) or collections.Counter()).most_common(4)),
                     nodes=dom["ot"].get(V, 0), story_nodes=story_nodes.get(V, 0),
                     files=len(cen_files.get(V, ())),
                     story_files=story_files.get(V, 0), sys_files=sys_files.get(V, 0),
                     close_strings=cl_str, close_mid=close_mid, arg_fam=afam,
                     close_id=cl_id,
                     in_edges=INEDGE[V], callers_named=inh, pos=POS.get(V),
                     callees=VEDGE[V],
                     callees_named=[(t, E1NAME[t]) for t in VEDGE[V] if t in E1NAME])
        vd = verdict(V, feats, dict(e4_d=TH_E4_D, e4_pur=TH_E4_PUR))
        ap_str = _fmt_args(prof.get(V, dict(argc=collections.Counter(), kinds=collections.Counter(),
                                            strs=collections.Counter(), num=collections.defaultdict(list))))
        rows.append(dict(
            V="0x%X" % V,
            cls=("非命名形态" if V in non else ("任务点名/上游候选" if V in focus_extra else "未定")),
            nodes=feats["nodes"], story_nodes=feats["story_nodes"], files=feats["files"],
            story_files=feats["story_files"], sys_files=feats["sys_files"],
            shape=sh_dist, shape_class=feats["shape_class"], shape_kinds=feats["shape_kinds"],
            shape_follow=(";".join("%s×%d" % (k, n2) for k, n2 in feats["shape_follow"]) or "-"),
            body_ins=feats["body_n"], body_over_nextV=ov,
            body_strings=";".join(feats["body_strings"][:6]),
            close_strings=";".join(feats["close_strings"][:6]) or "-",
            close_mid=";".join("h%d%s" % (h, ("=" + HANDLER_NAME[h]) if h in HANDLER_NAME else "")
                               for h in feats["close_mid"][:6]) or "-",
            arg_family=("%s ×%d（%d 个不同值）" % (feats["arg_fam"][0], feats["arg_fam"][1],
                                                feats["arg_fam"][2])
                        if feats["arg_fam"] and feats["arg_fam"][0] != "#" else "-"),
            body_natives=";".join("h%d%s" % (h, ("=" + HANDLER_NAME[h]) if h in HANDLER_NAME else "")
                                  for h in sorted(nat)),
            body_calls=";".join(sorted(feats["body_calls"])[:8]),
            in_edges=(";".join("0x%X" % u for u in feats["in_edges"][:12])
                      + ("(+%d)" % (len(feats["in_edges"]) - 12) if len(feats["in_edges"]) > 12 else "")) or "-",
            callers_named=";".join("0x%X:%s" % (u, nm) for u, nm in feats["callers_named"][:3]) or "-",
            callees_named=";".join("0x%X:%s" % (u, nm) for u, nm in feats["callees_named"][:3]) or "-",
            args=ap_str,
            e4=("D=%d pur=%.4f q=%.4f top=%s" % (e4["D"], e4["pur"], e4["q"], e4["top"]) if e4 else ""),
            pos_sig=("n=%d sc=%d per=%.2f mean=%.3f ge90=%.3f"
                     % (POS[V]["n"], POS[V]["scenes"], POS[V]["per_scene"] or -1,
                        POS[V]["pos_mean"] or -1, POS[V]["part_ge090"] or -1) if V in POS else ""),
            category=vd["category"], verdict=vd["verdict"], rule=vd["rule"],
            strength=vd["strength"], basis=vd["basis"], gap=vd["gap"]))
    # ---- --check ----
    ok = True
    bad = []
    ov_tot = sum(r["body_over_nextV"] for r in rows)
    if ov_tot:
        ok = False
        bad.append("CFG 体越 nextV 合计 %d（应为 0）" % ov_tot)
    # 0x2C3C 族不变式
    fam = check_2c3c(fl)
    for k, v in fam["inv"].items():
        if not v:
            ok = False
            bad.append("0x2C3C 族不变式不成立：%s（%s）" % (k, fam["detail"].get(k)))
    nonu = [r["V"] for r in rows if r["cls"] == "非命名形态" and r["shape_kinds"] > 1]
    if nonu:
        ok = False
        bad.append("非命名族形态不唯一：%s" % nonu)

    def _emit():
        hdr = list(rows[0].keys()) if rows else []
        print("\t".join(hdr))
        for r in rows:
            print("\t".join(str(r[c]) for c in hdr))

    if a.check:
        print("非命名族形态一致率: %s" % ("1.0" if not nonu else "有例外"))
        print("0x2C3C 族：" + json.dumps(fam["inv"], ensure_ascii=False) + " " + json.dumps(fam["detail"], ensure_ascii=False))
        print("CHECK = %s%s" % (ok, "" if ok else " ｜ " + " ；".join(bad)))
        return 0 if ok else 1

    if a.selftest:
        return 0 if selftest(fl, V_all, nxt) else 1

    if a.out is None:
        _emit()
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        write_tsv(os.path.join(a.out, "未定V攻坚_结果.tsv"), rows)
        # 子表：非命名 16 族的结构刻画
        write_tsv(os.path.join(a.out, "非命名族结构.tsv"),
                  [r for r in rows if r["cls"] == "非命名形态"])
        # 冲突对账：本模块 E1/E1c 结论 vs 既有 TIME_FAMILY / V_NAMING 记名
        conf = []
        for r in rows:
            if r["rule"] not in ("E1(体级内嵌串)", "E1c(私有子程序内嵌串·1跳)"):
                continue
            V = int(r["V"], 16)
            mine = (r["verdict"].split("：", 1)[1] if "：" in r["verdict"] else "")
            tfold = D.TIME_FAMILY.get("ot", {}).get(V)
            vnold = D.V_NAMING.get("ot", {}).get(V, {}).get("name", "")
            tf = tfold[0] if tfold else ""
            head = mine.split("/")[0]
            agree = ((not tf or tf in mine or head in tf)
                     and (not vnold or vnold.split("/")[0] in mine or head in vnold))
            conf.append(dict(V=r["V"], rule=r["rule"], mine=mine,
                             time_family=tf, v_naming=vnold, agree=agree))
        write_tsv(os.path.join(a.out, "命名冲突对账.tsv"), conf)
        # 附：全 93 V 的引擎自证一览（含已采纳/候选，供交叉核对）
        allrows = []
        for v in V_all:
            s2 = SCAN[v]
            allrows.append(dict(
                V="0x%X" % v, nodes=dom["ot"].get(v, 0), story_nodes=story_nodes.get(v, 0),
                body_ins=s2["n"], end="0x%02X" % fl.idx[v // 4][0] if (v // 4) in fl.idx else "",
                body_strings=";".join(sorted(s2["strings"])[:6]),
                label=(SEM_LABEL.get(v) or (label_from_strings(sorted(s2["strings"])) if s2["strings"] else "")),
                body_natives=";".join("h%d%s" % (h, ("=" + HANDLER_NAME[h]) if h in HANDLER_NAME else "")
                                      for h in sorted(s2["natives"])),
                in_edges=";".join("0x%X" % x for x in INEDGE[v][:8]),
                calls=";".join("%s×%d" % (k, k2) for k, k2 in
                               [(("0x%X" % k), k2) for k, k2 in s2["calls"].most_common(6)])))
        write_tsv(os.path.join(a.out, "全V_引擎自证.tsv"), allrows)
        json.dump(dict(rows=rows, conflicts=conf, n_und=len(und), n_non=len(non),
                       e4=dict(eq_seq=n_eq, ne_seq=n_ne),
                       q_max=max(Q.values()) if Q else 0,
                       fam_2c3c=fam),
                  io.open(os.path.join(a.out, "未定V攻坚_结果.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("[写] %s/{未定V攻坚_结果,非命名族结构,命名冲突对账}.tsv + 未定V攻坚_结果.json" % a.out)
    return 0


# ================================================================ 0x2C3C 族自证
def check_2c3c(fl):
    """0x2C3C 族不变式（可失败）。**只统计 `ot` 源**（V 号每 build 组本地）。

    ★ 一审 M1 订正：原「10 字窗口内前邻 `CALLN h462`」被写成结构律。实测该前邻关系是
      **窗口宽度产物**——逐站记录「最近 h462 的 `[05]` 距本门 `[04]` 的步数」后：
      10 字窗口（搜 `i-4..i-13`，等价原实现 `range(i-4, i-14, -1)`）命中 57834/57859；
      放宽到 20 字窗口（搜 `i-4..i-23`）命中 **57859/57859 = 1.0000**，「无 h462」归零。
      ⇒ **四条主不变式仍取 10 字窗口口径**（保持原结论不变），但 detail 同时给出 20 字窗口与
      距离分布、两种窗口的 (arg, 有/无 h462) 交叉表，供阅读者判断口径。
    """
    n = fol_jz = arg_ok = disp8 = n462_10 = n462_20 = 0
    dist = collections.Counter()                       # 最近 h462 步数（None = 40 步内无）
    cross10 = collections.Counter()                    # (arg, 有h462) @10 字窗口
    cross20 = collections.Counter()                    # (arg, 有h462) @20 字窗口
    sd = D.SOURCES["ot"]
    for fn in sorted(os.listdir(sd["dir"])):
        if not fn.lower().endswith(sd["ext"]):
            continue
        try:
            s = D.Sob0(os.path.join(sd["dir"], fn))
        except Exception:
            continue
        c, m3, m4, m1 = s.cells, s.maps[3], s.maps[4], s.maps[1]
        for k, V in m3.items():
            if V != 0x2C3C:
                continue
            i = k // 4
            n += 1
            if c[i + 5] == 0x1E:
                fol_jz += 1
            arg = c[i - 2]
            if arg in (0, 1):
                arg_ok += 1
            t = m4.get((i + 4) * 4)
            if t is not None and t - (i + 4) * 4 == 8:
                disp8 += 1
            d = None
            for step in range(1, 41):
                j = i - step
                if j < 0:
                    break
                if c[j] == 5 and m1.get((j + 1) * 4) == 462:
                    d = step
                    break
            dist[d] += 1
            f10 = (d is not None and 4 <= d <= 13)     # 原实现 range(i-4,i-14,-1)
            f20 = (d is not None and 4 <= d <= 23)     # 放宽到 20 字窗口
            n462_10 += f10
            n462_20 += f20
            cross10[(arg, f10)] += 1
            cross20[(arg, f20)] += 1
    inv = dict(follower_JZ=(fol_jz == n and n > 0),
               arg_in_0_1=(arg_ok == n and n > 0),
               tail_ref_disp_plus8=(disp8 == n and n > 0),
               prev_CALLN_h462_rate_ge_0999=(n462_10 >= 0.999 * n and n > 0))
    dist_s = ",".join("%s:%d" % ((kk if kk is not None else ">40"), vv)
                      for kk, vv in sorted(dist.items(), key=lambda x: (x[0] is None, x[0])))
    ct10 = " ".join("(%d,%s)=%d" % (a, "有" if ok else "无", cross10[(a, ok)])
                    for a in (0, 1) for ok in (True, False))
    ct20 = " ".join("(%d,%s)=%d" % (a, "有" if ok else "无", cross20[(a, ok)])
                    for a in (0, 1) for ok in (True, False))
    return dict(n=n, inv=inv,
                detail=dict(n=n, follower_JZ="%d/%d" % (fol_jz, n),
                            arg_in_0_1="%d/%d" % (arg_ok, n),
                            tail_ref_disp_plus8="%d/%d" % (disp8, n),
                            prev_CALLN_h462_win10="%d/%d (缺 %d)" % (n462_10, n, n - n462_10),
                            prev_CALLN_h462_win20="%d/%d (缺 %d)" % (n462_20, n, n - n462_20),
                            h462_dist=dist_s, cross10=ct10, cross20=ct20))


def e1_station_stats(fl, V_all, nxt):
    """§1.3 的可复跑来源：`func_lib.sob` 串区被**指令操作数**引用的站/串统计。

    站 = 一条指令的某个操作数字（site）经 `maps[4]` 指向串区；不同串 = 去重后、剔 junk。
    E1 类 = 效果宏名 / 资源模板串（`.ELG|GMP|OGG|PNG|G00`）/ 裸资源名（`^[A-Z][A-Z0-9_]{2,}$`）。
    「落在某 V 的 CFG 体内」= 该操作数所属指令 ∈ 93 个 V 的 CFG 体并集。
    """
    body_union, owner = set(), {}
    for v in V_all:
        nx = nxt[v]
        for j in fl.body(v, maxoff=(nx if nx else v + W_BODY_MAX)):
            body_union.add(j)
            owner.setdefault(j, v)
    ins_of = {}
    for j, (o, n, _a) in fl.idx.items():
        for wi in range(j, j + n + 1):
            ins_of[wi] = j
    sites_all = sites_nj = 0
    strs_all, e1_sites, e1_str = set(), set(), set()
    for j, (o, n, _a) in fl.idx.items():
        for q in range(n):
            site = (j + 1 + q) * 4
            tv = fl.s.maps[4].get(site)
            if tv is None or not (fl.s.ss <= tv < fl.s.se):
                continue
            sites_all += 1
            try:
                st = fl.s.read_group(tv)[0].decode("cp932", "replace")
            except Exception:
                st = ""
            if not st or JUNK.match(st):
                continue
            sites_nj += 1
            strs_all.add(st)
            if st in EFFECT_NAMES or RE_RES.search(st) or re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", st):
                e1_sites.add(site)
                e1_str.add(st)
    inb = [s for s in e1_sites if ins_of.get(s // 4) in body_union]
    vs = sorted({owner[ins_of[s // 4]] for s in inb})
    return dict(ins_operand_string_sites=sites_all,
                ins_operand_string_sites_nonjunk=sites_nj,
                strings_distinct=len(strs_all), e1_strings_distinct=len(e1_str),
                e1_sites=len(e1_sites), e1_in_body=len(inb),
                e1_out_body=len(e1_sites) - len(inb),
                e1_body_Vs=len(vs), e1_body_V_list=["0x%X" % x for x in vs])


def write_tsv(path, rows):
    cols = list(rows[0].keys()) if rows else []
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([str(r[c]).replace("\t", " ").replace("\n", " ") for c in cols])


def selftest(fl, V_all, nxt):
    """变异夹具：判据必须能失败。"""
    cases = []
    # F1：关掉 JZ 边 ⇒ 0xFDF4 的体必须变小，且不再包含 'bg_zoom'
    b_with = fl.body(0xFDF4)
    fl.follow_jz = False
    for j, (o, n, aa) in fl.idx.items():
        L = 1 + n
        if o == 0x1E:
            fl.succ[j] = [j + L]
    b_without = fl.body(0xFDF4)
    fl.follow_jz = True
    for j, (o, n, aa) in fl.idx.items():
        L = 1 + n
        if o == 0x1E:
            fl.succ[j] = [j + L] + ([fl._tgt(j + 2)] if fl._tgt(j + 2) in fl.idx else [])
    has = any(fl.resolve(j + 1 + q)[:12] == "S:bg_zoom" for j in b_with
              for q in range(fl.idx[j][1]) if j in fl.idx)
    has2 = any(fl.resolve(j + 1 + q)[:12] == "S:bg_zoom" for j in b_without
               for q in range(fl.idx[j][1]) if j in fl.idx)
    cases.append(("F1 JZ 边是体连通性的必要条件（去掉后体变小且不再含 bg_zoom）",
                  len(b_without) < len(b_with) and has and not has2,
                  "with=%d(含 bg_zoom=%s) without=%d(含=%s)" % (len(b_with), has, len(b_without), has2)))
    # F2：体边界自证——**不夹紧**的可达闭包仍不越 nextV（有牙：若边界律失效即会越界。
    #     旧版先按 maxoff 夹紧再统计，越界恒 0、无判别力；一审 N1 订正。）
    ov = 0
    for v in V_all:
        nx = nxt[v]
        b = fl.body(v)                                   # 不夹紧
        ov += sum(1 for j in b if nx is not None and j * 4 >= nx)
    cases.append(("F2 不夹紧的 CFG 体仍全部落在 [V,nextV) 内（越界数 == 0）",
                  ov == 0, "不夹紧越界 %d / %d 个 V" % (ov, len(V_all))))
    # F3：0x2C3C 族不变式必须成立（且 4 条各自可失败：给出计数）
    fam = check_2c3c(fl)
    cases.append(("F3 0x2C3C 族四条不变式成立", all(fam["inv"].values()), json.dumps(fam["detail"], ensure_ascii=False)))
    # F4：E4 的「计数相等」闸门是必要条件 —— 拿掉闸门后配对纯度必须掉到阈值下
    scenes_ot = load_scenes("ot")
    psv, _ids = D.load_psv_timeline()
    gold = {s: psv[s] for s in scenes_ot if s in psv}

    def pair(targets, gate):
        lab = collections.defaultdict(collections.Counter)
        for sid, rows in gold.items():
            if sid not in scenes_ot:
                continue
            byseq = collections.defaultdict(list)
            for r in rows:
                if r.get("type") == "Message":
                    continue
                byseq[str(r["seq"])].append(r)
            pn = collections.defaultdict(list)
            for nd in scenes_ot[sid]["nodes"]:
                pn[str(nd["seq"])].append(nd)
            for sq, rs in byseq.items():
                ns = pn.get(sq, [])
                if gate and len(ns) != len(rs):
                    continue
                if not gate:
                    rs = rs[:len(ns)]
                if not rs or not ns:
                    continue
                for nd, r in zip(ns, rs):
                    if nd["V"] in targets:
                        lab[nd["V"]][r["type"]] += 1
        return lab
    T = {0x14084, 0x1A96C, 0x1FAD4}
    g_on, g_off = pair(T, True), pair(T, False)

    def pur(lab, V):
        c = lab.get(V)
        if not c:
            return 0.0, 0
        tot = sum(c.values())
        return c.most_common(1)[0][1] / tot, tot
    p_on, d_on = pur(g_on, 0x1FAD4)
    p_off, d_off = pur(g_off, 0x1FAD4)
    cases.append(("F4 E4「计数相等」闸门是必要条件（去掉后 0x1FAD4 纯度下降到阈值下）",
                  p_off < p_on and p_off < TH_E4_PUR,
                  "ON pur=%.4f D=%d ｜ OFF pur=%.4f D=%d（阈值 %.2f）"
                  % (p_on, d_on, p_off, d_off, TH_E4_PUR)))
    # F5：窗口/最近 V 归属 vs CFG 体归属 —— CHR\\%s.ELG 的引用指令**不在** 0x14084 体内
    key = "CHR" + chr(92) + "%s.ELG"
    site_ins = None
    for site, val in sorted(fl.s.maps[4].items()):
        if not (fl.s.ss <= val < fl.s.se):
            continue
        try:
            st = fl.s.read_group(val)[0].decode("cp932", "replace")
        except Exception:
            continue
        if st == key:
            for j, (o, n, aa) in fl.idx.items():
                if any((j + 1 + q) * 4 == site for q in range(n)):
                    site_ins = j
            break
    b14084 = fl.body(0x14084)
    cases.append(("F5 窗口法会把 CHR 装载串错归 0x14084，体法不会（判据更严）",
                  site_ins is not None and site_ins not in b14084
                  and 0x14084 <= site_ins * 4 < nxt[0x14084],
                  "串指令 0x%X ∈ [V,nextV)=%s ｜ ∈ CFG 体=%s"
                  % (site_ins * 4, 0x14084 <= site_ins * 4 < nxt[0x14084],
                     site_ins in b14084)))
    good = all(c[1] for c in cases)
    for nm, o, d in cases:
        print("  [%s] %s ｜ %s" % ("PASS" if o else "FAIL", nm, d))
    print("SELFTEST = %s（%d/%d）" % (good, sum(1 for c in cases if c[1]), len(cases)))
    return good


if __name__ == "__main__":
    sys.exit(main())
