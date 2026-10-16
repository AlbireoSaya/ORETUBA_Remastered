# -*- coding: utf-8 -*-
"""SOB0「软表落地」审计探针 · ISSUE-20261007-10（**只读**，不写任何文件）

用途：把 `软表解出_说明.md`（ISSUE-20261007-09）里**尚属「顾问一次性测量 / 未复算」**
的数字，以及 `decode_sob0.py` T1 判据收紧的**前后对照**，全部以「可复跑」的方式固定下来。
本工具**只读**，不产出任何数据；`--json` 可选落盘机读结果。

用法
  python -X utf8 编程组/SOB0解码/_landing_audit.py --data-root "E:/ZCode Workspace/Galgame"
  python -X utf8 编程组/SOB0解码/_landing_audit.py --json 编程组/SOB0解码/_landing_audit.json

口径
  · 分母 N = 该源**语料场 ∩ PSV 金标场**（ot 362 / otp 14）。
  · V 场 = 该 V 出现过的场（该源语料 ∩ 金标）。
  · T 场 = 该 PSV type 至少出现一次的场（同上）。
  · 命中 = V 场 ∩ T 场；反例（假阳）= V 场 \\ T 场；漏检（假阴）= T 场 \\ V 场。
  · precision = 命中 / |V 场|（主判据，阈值 0.67，沿用既有「FadeOut 0.67 被采纳」口径）；
    recall = 命中 / |T 场|；base = |T 场| / N（type 自身的场覆盖率）。
  · **判别力门槛（本批新增）**：base ≥ 0.95 的 type 近乎无条件出现 ⇒ 逐场共现
    不再有鉴别力，一律判「未定（判别力不足）」，不得据此定名（防「全覆盖型 type 假通过」）。
"""
import argparse
import collections
import csv
import io
import json
import os
import re
import struct
import sys

MAGICS = (b"SOB0", b"SOB1", b"SOB2")

SOURCES = {
    "ot":  dict(dir="工程/我们没有翅膀/解包/SCRIPT", scene="scene_ot.jsonl", prefix=""),
    "otp": dict(dir="工程/我们没有翅膀 前奏诗/解包/SCRIPT", scene="scene_otp.jsonl", prefix=""),
    "otr": dict(dir="工程/我们没有翅膀R/参照/原版汉化SCRIPT_CHS",
                scene="scene_otr.jsonl", prefix="s03c_"),
}

FADE_CARRIER = {"ot": 0x19F9C, "otp": 0x172BC}
FADE_TYPES = ("FadeIn", "FadeOut")

# (V, 候选名, 待验 PSV type, 采纳标签覆盖；空串=用候选名)
# 注：`0x1AD18` 的**采纳标签**刻意用较弱的「EyeCatch 族（In/End 场级不可分）」——
#     PSV `EyeCatch` 与 `EyeCatchEnd` 场覆盖同为 316、场级完全共现，逐场法**不能**区分 In/End。
V_CANDIDATES = [
    (0x7480,  "Window",           "Window",          ""),
    (0x1C8D0, "章节名",            "SetSceneName",    ""),
    (0x1FAD4, "SceneJumpDialog",  "SceneJumpDialog", ""),
    (0x1B040, "InOut_Act",        "InOut_Act",       ""),
    (0x1AD18, "EyeCatch(End)",    "EyeCatchEnd",     "EyeCatch 族（In/End 场级不可分）"),
]
V_UNNAMED = [0x17514, 0x14084, 0x19A68]

NAME_PREC_THRESHOLD = 0.67
BASE_DISCRIMINATIVE_MAX = 0.95


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse_container(path):
    b = open(path, "rb").read()
    if b[:4] not in MAGICS:
        return None
    off = 8
    tabs = []
    for _ in range(6):
        n = u32(b, off)
        off += 4
        d = {}
        for _k in range(n):
            d[u32(b, off)] = u32(b, off + 4)
            off += 8
        tabs.append(d)
    ss, se = u32(b, off), u32(b, off + 4)
    he = off + 8
    if he + se > len(b):
        return None
    return dict(raw=b, magic=b[:4], maps=tabs, ss=ss, se=se, he=he,
                table_size=u32(b, 4))


def cells_of(c):
    return struct.unpack_from("<%dI" % (c["ss"] // 4), c["raw"], c["he"])


def node_args(c, i):
    """复刻 `decode_sob0.Sob0.node_args`：实参 = 节点前连续 `[08][arg]`。"""
    cells = cells_of(c)
    m0, m1, m3, m4 = c["maps"][0], c["maps"][1], c["maps"][3], c["maps"][4]
    ss, se = c["ss"], c["se"]
    argc = cells[i + 3] // 4

    def dec(wi):
        w = cells[wi]
        site = wi * 4
        if site in m4:
            v = m4[site]
            if ss <= v < se:
                return "S", v
            return "C", w
        if site in m3:
            return "A", m3[site]
        if site in m1:
            return "I", m1[site] + 1
        if site in m0:
            return "P", m0[site]
        return "N", w

    return [dec(i - 1 - 2 * t) for t in range(argc)]


def scan_classic(c):
    """旧判据（classic）：`[04][V][0C][k][03][尾REF→空串]`（不要求 maps[3] 背书）。"""
    cells = cells_of(c)
    m3, m4 = c["maps"][3], c["maps"][4]
    ss, se, he, raw = c["ss"], c["se"], c["he"], c["raw"]
    out = []
    for i in range(len(cells) - 5):
        if not (cells[i] == 4 and cells[i + 2] == 0x0C and cells[i + 4] == 3):
            continue
        tail = m4.get((i + 5) * 4)
        if tail is None:
            continue
        if ss <= tail < se:
            kind = "empty" if raw[he + tail] == 0 else "str"
        elif tail < ss:
            kind = "code"
        else:
            kind = "none"
        if kind != "empty":
            continue
        out.append(dict(i=i, V=cells[i + 1], k=cells[i + 3],
                        backed=(i + 1) * 4 in m3, tail=tail, tail_kind=kind))
    return out


def probe_fake_buckets(c):
    """复刻 `_probe_soft_tables.scan_commands` 的 fake 口径（含 else 分支）。"""
    cells = cells_of(c)
    m3, m4 = c["maps"][3], c["maps"][4]
    ss, se, he, raw = c["ss"], c["se"], c["he"], c["raw"]
    nb = bo = 0
    for i in range(len(cells) - 6):
        if not (cells[i] == 4 and cells[i + 2] == 0x0C and cells[i + 4] == 3):
            continue
        tail = m4.get((i + 5) * 4)
        if (i + 1) * 4 not in m3:
            nb += 1
            continue
        if tail is not None and ss <= tail < se:
            pass                                   # cmd
        elif tail is not None and tail < ss and cells[i + 3] == 4:
            pass                                   # jump
        else:
            bo += 1
    return dict(no_backing=nb, backed_other=bo)


def corpus_want(data_root, prj, name):
    spec = SOURCES[name]
    p = os.path.join(prj, "资源组", "剧本", spec["scene"])
    want = {}
    for line in io.open(p, encoding="utf-8"):
        o = json.loads(line)
        s = o["script"].lower()
        if spec["prefix"] and not s.startswith(spec["prefix"]):
            continue
        want[s] = o["scene_id"]
    return want


def load_psv(prj):
    p = os.path.join(prj, "编程组", "PSV演出", "时间线.tsv")
    by = collections.defaultdict(list)
    for r in csv.DictReader(io.open(p, encoding="utf-8"), delimiter="\t"):
        by[r["scene_id"]].append(r)
    return by


# ---------------------------------------------------------------- T1
def run_t1(data_root, prj, rep):
    rep["t1"] = {}
    for name, spec in SOURCES.items():
        d = os.path.join(data_root, spec["dir"])
        want = corpus_want(data_root, prj, name)
        classic = kept = removed = 0
        rem_samples = []
        files_used = 0
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".sob"):
                continue
            if os.path.splitext(fn)[0].lower() not in want:
                continue
            c = parse_container(os.path.join(d, fn))
            if c is None or c["magic"] == b"SOB1":
                continue
            files_used += 1
            for nd in scan_classic(c):
                classic += 1
                if nd["backed"]:
                    kept += 1
                else:
                    removed += 1
                    if len(rem_samples) < 20:
                        rem_samples.append(dict(
                            file=fn, off=hex(c["he"] + 4 * nd["i"]),
                            node_word=nd["i"], V="0x%X" % nd["V"],
                            k=nd["k"], tail=nd["tail"], tail_kind=nd["tail_kind"]))
        rep["t1"][name] = dict(files_decoded=files_used, classic=classic,
                               kept=kept, removed=removed,
                               removed_samples=rem_samples)
    # ot 全库 1,140 假阳性分解
    d = os.path.join(data_root, SOURCES["ot"]["dir"])
    nb = bo = n_classic_lib = n_cmd = n_removed_lib = 0
    samples = []
    per_file = collections.Counter()
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".sob"):
            continue
        c = parse_container(os.path.join(d, fn))
        if c is None or c["magic"] == b"SOB1":
            continue
        buck = probe_fake_buckets(c)
        nb += buck["no_backing"]
        bo += buck["backed_other"]
        cells = cells_of(c)
        m3, m4 = c["maps"][3], c["maps"][4]
        ss, se, he, raw = c["ss"], c["se"], c["he"], c["raw"]
        for i in range(len(cells) - 5):
            if not (cells[i] == 4 and cells[i + 2] == 0x0C and cells[i + 4] == 3):
                continue
            if (i + 1) * 4 in m3:
                continue
            tail = m4.get((i + 5) * 4)
            if tail is None:
                tk = "none"
            elif ss <= tail < se:
                tk = "empty" if raw[he + tail] == 0 else "str"
            elif tail < ss:
                tk = "code"
            else:
                tk = "none"
            per_file[fn] += 1
            if len(samples) < 20:
                samples.append(dict(file=fn, off=hex(he + 4 * i), node_word=i,
                                    V="0x%X" % cells[i + 1], k=cells[i + 3],
                                    tail=tail, tail_kind=tk))
        for nd in scan_classic(c):
            n_classic_lib += 1
            if nd["backed"]:
                n_cmd += 1
            else:
                n_removed_lib += 1
    rep["t1_library_ot"] = dict(
        fake_total=nb + bo, fake_no_backing=nb, fake_backed_other=bo,
        classic_lib=n_classic_lib, backed_cmd=n_cmd,
        removed_from_classic=n_removed_lib,
        top_files=per_file.most_common(12), samples=samples)
    return rep


# ---------------------------------------------------------------- T2
def run_t2(data_root, prj, rep):
    psv = load_psv(prj)
    rep["t2"] = {}
    for name, V in FADE_CARRIER.items():
        spec = SOURCES[name]
        d = os.path.join(data_root, spec["dir"])
        want = corpus_want(data_root, prj, name)
        gold = {sid for sid in want.values() if sid in psv}
        v_scenes = set()          # 载体 V 场 = 该源**语料全部场**（含无金标场）
        v_scenes_gold = set()
        ms_vals = collections.Counter()
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".sob"):
                continue
            nm = os.path.splitext(fn)[0].lower()
            if nm not in want:
                continue
            c = parse_container(os.path.join(d, fn))
            if c is None or c["magic"] != b"SOB0":
                continue
            sid = want[nm]
            for nd in scan_classic(c):
                if nd["V"] == V and nd["backed"]:
                    v_scenes.add(sid)
                    if sid in gold:
                        v_scenes_gold.add(sid)
                    args = node_args(c, nd["i"])
                    if args:
                        kk, vv = args[0]
                        if kk in ("N", "A", "I") and isinstance(vv, int):
                            ms_vals[vv] += 1
        out = dict(V="0x%X" % V, N=len(gold), scenes_with_V=len(v_scenes),
                   scenes_with_V_gold=len(v_scenes_gold),
                   ms_dist=ms_vals.most_common(6))
        for t in FADE_TYPES:
            t_scenes = set()
            for sid in gold:
                for r in psv[sid]:
                    if r.get("type") == t and (r.get("time") or "").isdigit() \
                            and int(r["time"]) > 0:
                        t_scenes.add(sid)
                        break
            inter = v_scenes & t_scenes
            out[t] = dict(t_scenes=len(t_scenes), inter=len(inter),
                          precision=round(len(inter) / len(v_scenes), 4) if v_scenes else None,
                          recall=round(len(inter) / len(t_scenes), 4) if t_scenes else None,
                          v_without_t_n=len(v_scenes - t_scenes),
                          v_without_t=sorted(v_scenes - t_scenes)[:20],
                          t_without_v_n=len(t_scenes - v_scenes),
                          t_without_v=sorted(t_scenes - v_scenes)[:20])
        rep["t2"][name] = out
    return rep


# ---------------------------------------------------------------- T3
def _score(vs, tset, N):
    inter = vs & tset
    return dict(inter=len(inter),
                precision=round(len(inter) / len(vs), 4) if vs else None,
                recall=round(len(inter) / len(tset), 4) if tset else None,
                base=round(len(tset) / N, 4) if N else None)


def _verdict(cand, s, vlabel=""):
    if s["precision"] is None or s["precision"] < NAME_PREC_THRESHOLD:
        return "未定"
    if s["base"] is not None and s["base"] >= BASE_DISCRIMINATIVE_MAX:
        return "未定（判别力不足：type 场覆盖 %.3f）" % s["base"]
    return "采纳：" + (vlabel or cand)


def run_t3(data_root, prj, rep):
    psv = load_psv(prj)
    rep["t3"] = {}
    for name, spec in SOURCES.items():
        if name == "otr":
            continue                      # otr 逐行 seq 不可靠，不参与定名（说明.md §5.1）
        d = os.path.join(data_root, spec["dir"])
        want = corpus_want(data_root, prj, name)
        gold = {sid for sid in want.values() if sid in psv}
        N = len(gold)
        type_scenes = collections.defaultdict(set)
        for sid in gold:
            for r in psv[sid]:
                type_scenes[r.get("type", "")].add(sid)
        v_scenes = collections.defaultdict(set)     # 场集合（**金标场**，用于打分）
        v_scenes_all = collections.defaultdict(set)  # 场集合（**全语料**，用于计数对齐）
        v_nodes = collections.Counter()              # 节点数（**全语料**，与任务书口径一致）
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".sob"):
                continue
            nm = os.path.splitext(fn)[0].lower()
            if nm not in want:
                continue
            c = parse_container(os.path.join(d, fn))
            if c is None or c["magic"] != b"SOB0":
                continue
            sid = want[nm]
            for nd in scan_classic(c):
                if nd["backed"]:
                    v_scenes_all[nd["V"]].add(sid)
                    v_nodes[nd["V"]] += 1
                    if sid in gold:
                        v_scenes[nd["V"]].add(sid)
        out = dict(N=N)
        for V, cand, ptype, vlabel in V_CANDIDATES:
            vs = v_scenes.get(V, set())
            ts = type_scenes.get(ptype, set())
            s = _score(vs, ts, N)
            out["0x%X" % V] = dict(
                candidate=cand, psv_type=ptype, v_nodes=v_nodes.get(V, 0),
                v_scenes=len(vs), v_scenes_all=len(v_scenes_all.get(V, set())),
                t_scenes=len(ts), **s,
                counterexamples=sorted(vs - ts)[:3],
                counterexample_n=len(vs - ts),
                missing_t=sorted(ts - vs)[:3], missing_t_n=len(ts - vs),
                verdict=_verdict(cand, s, vlabel))
        for V in V_UNNAMED:
            vs = v_scenes.get(V, set())
            best = []
            for tname, tset in type_scenes.items():
                ss = _score(vs, tset, N)
                if ss["inter"]:
                    best.append((ss["precision"], ss["recall"], ss["base"], tname,
                                 ss["inter"], ss))
            best.sort(reverse=True)
            top = best[0] if best else None
            if top:
                _p, _r, base, tname, _it, ss = top
                verdict = ("未定（判别力不足：type 场覆盖 %.3f）" % base
                           if base >= BASE_DISCRIMINATIVE_MAX or _p < NAME_PREC_THRESHOLD
                           else "候选：" + tname)
                out["0x%X" % V] = dict(
                    candidate="(未定名)", psv_type=tname, v_nodes=v_nodes.get(V, 0),
                    v_scenes=len(vs), v_scenes_all=len(v_scenes_all.get(V, set())),
                    t_scenes=len(type_scenes.get(tname, set())), **ss,
                    counterexamples=sorted(vs - type_scenes.get(tname, set()))[:3],
                    counterexample_n=len(vs - type_scenes.get(tname, set())),
                    missing_t=sorted(type_scenes.get(tname, set()) - vs)[:3],
                    missing_t_n=len(type_scenes.get(tname, set()) - vs),
                    best_types=[[round(a, 4), round(b, 4), c, it] for a, b, _c, c, it, _s in best[:4]],
                    verdict=verdict)
            else:
                out["0x%X" % V] = dict(candidate="(未定名)", v_scenes=len(vs),
                                       v_nodes=v_nodes.get(V, 0), verdict="未定")
        rep["t3"][name] = out
    return rep


# ---------------------------------------------------------------- T4
def run_t4(data_root, prj, rep):
    p = os.path.join(data_root, "工程", "我们没有翅膀", "解包", "SCRIPT", "func_lib.sob")
    c = parse_container(p)
    S = c["raw"][c["he"] + c["ss"]: c["he"] + c["se"]]
    strs = re.findall(rb"[ -~]{3,}", S)
    rule_like = [s.decode("ascii") for s in strs if b"RULE" in s]
    elg = [s.decode("ascii") for s in strs if b".ELG" in s]
    psv = load_psv(prj)
    rvals = collections.Counter()
    for rows in psv.values():
        for r in rows:
            if r.get("rule", ""):
                try:
                    rvals[int(r["rule"])] += 1
                except ValueError:
                    pass
    # PC 侧 rule_in 族（ot 0x1A96C）的实参值域，供「数值→编号」可推性判断
    rule_args = collections.Counter()
    d = os.path.join(data_root, SOURCES["ot"]["dir"])
    want = corpus_want(data_root, prj, "ot")
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".sob"):
            continue
        if os.path.splitext(fn)[0].lower() not in want:
            continue
        c = parse_container(os.path.join(d, fn))
        if c is None or c["magic"] != b"SOB0":
            continue
        for nd in scan_classic(c):
            if nd["V"] == 0x1A96C and nd["backed"]:
                for kk, vv in node_args(c, nd["i"]):
                    if kk in ("N", "A", "I") and isinstance(vv, int):
                        rule_args[vv] += 1
    rep["t4"] = dict(
        func_lib_string_bytes=len(S), ascii_strings=len(strs),
        rule_like=rule_like, elg_like=elg[:24],
        psv_rule_distinct=len(rvals),
        psv_rule_min=min(rvals) if rvals else None,
        psv_rule_max=max(rvals) if rvals else None,
        psv_rule_top=[[k, v] for k, v in rvals.most_common(12)],
        pc_rule_in_args_top=[[k, v] for k, v in rule_args.most_common(12)])
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--json", default="", help="把机读结果写到此路径（可选）")
    a = ap.parse_args()
    prj = os.path.join(a.data_root, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
    rep = dict(data_root=a.data_root,
               note="只读审计；分母 N = 语料场 ∩ PSV 金标场")
    run_t1(a.data_root, prj, rep)
    run_t2(a.data_root, prj, rep)
    run_t3(a.data_root, prj, rep)
    run_t4(a.data_root, prj, rep)
    sys.stdout.reconfigure(encoding="utf-8")
    txt = json.dumps(rep, ensure_ascii=False, indent=1)
    print(txt)
    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as f:
            f.write(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
