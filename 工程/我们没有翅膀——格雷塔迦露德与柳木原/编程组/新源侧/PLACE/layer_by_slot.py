#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
layer_by_slot.py —— 立绘层序器（ISSUE-20261008-09 / PLACE 模块）

机制（「层序 = 槽号」**成立但证据有限**——仅 2 个数据点、无有效阴性对照，**不作「已定论」处理**；
      口径见 `会话交接_20261009.md` §二/§三）:
  * 层序 = **槽号升序绘制，槽号大者在前**；**不存在「名次→z 表」**。
    证据: (a) `00_任务书.md` **§8.7** 活体差分**重做实验**（改明日香槽 0→2 ⇒ 位置与层序同时变；
              §8.1–8.3 的决定轮已被一审打回 ⇒ 只作背景）；
          (b) `EXE_POS\\k人排布表_结论.md` §五 离线逐像素判据（与槽 1 全等 95.34% vs 槽 0 **0.00%**）
              ——**与 (a) 同源（同一 baseline 帧）⇒ 非独立**，且 `_probe_25` 的 V4 对 §8.7 那一帧
              **不具判别力**（§8.7「仍未证」）⇒ 只作同源复核、不得当独立第二证据；
          (c) `EXE_POS\\k人排布表_结论.md` §六 排序键 = 槽号数值（依据同为 §8.1–8.3 两轮对照 ⇒ 只作背景）。

做法:
  对每个场景 (src, scene_id) 按 (seq, ord) 顺序维护**在场槽集合**；
  在场槽按槽号升序排名 ⇒ 名次即绘制序，**名次越大 z 越大（越靠前）**。

已知边界（如实登记，不掩盖）:
  1. `CharacterDelete`(0x1C5B0 / otp 0x1A970) 的实参里**没有槽号**（`[0,-1,ms]`）
     ⇒ 无法在退场时把槽移出在场集合 ⇒ 本模块的在场集合是**单调累积**的。
     仅影响被退场者**自身**的绝对 rank 值；对**仍在场者之间的相对次序无影响**
     （被退场者不参与绘制）。
  2. `f`/`b`（Front/Back 标志，EXE_POS §9.4 未决项③）**未跟踪其消费点**
     ⇒ 带 f/b 的行其层序**不计为已解**（z_rank 留空），并在主表 conf 标 `fb待定`。

CLI:
  python -X utf8 layer_by_slot.py --emit               # 生成 层序_场景槽集合.tsv
  python -X utf8 layer_by_slot.py --check              # 严格只读幂等复核
  python -X utf8 layer_by_slot.py --selfproof          # 可失败自证（P1 结构 + P2 外证 + P3 阴性对照）
  python -X utf8 layer_by_slot.py --selfcheck-mutate   # 变异自证：反转层序方向 ⇒ 自证必须 FAIL
"""
import collections
import hashlib
import os
import sys

# 只读纪律：import PLACE 的模块不得在 PLACE 目录产生 __pycache__
sys.dont_write_bytecode = True
import place_dsl as P       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_SCENE = "层序_场景槽集合.tsv"

# 外证钉死站（`00_任务书.md` §8.7 / `EXE_POS\k人排布表_结论.md` §4.1）: s01_04i，同屏 高内(MAS01B,槽1) 与 明日香(ASU02A,槽0)
PROOF_SCENE = "ot_s01_04i"
PROOF_A = ("MAS01B", 1)      # 高内，槽 1 —— 逐像素证据: 在上
PROOF_B = ("ASU02A", 0)      # 明日香，槽 0 —— 逐像素证据: 在下


# ------------------------------------------------------------------ 在场槽集合 / rank
def scene_rank_map(rows, reverse=False):
    """rows: [(row_dict, field_dict)]（同一场景，任意序）。
    返回 {slot: rank}（升序 rank；reverse=True 为**变坏**的反向，供变异自证）。
    """
    slots = sorted({f["slot"] for _, f in rows if f.get("slot") is not None})
    if reverse:
        slots = list(reversed(slots))
    return {s: i for i, s in enumerate(slots)}


def compute_z(src, build=None, reverse=False):
    """返回 (rows, zmap)。rows = build_rows 的行对；zmap[(scene_id, file_idx)] = z_rank(str)。
    z_rank 只对「有槽号」且「不带 f/b」的行给出；其余留空。
    """
    if build is None:
        build = P.build_rows(src)
    by_scene = collections.defaultdict(list)
    for r, f in build:
        by_scene[r["scene_id"]].append((r, f))
    zmap = {}
    scenes = {}
    for scene, lst in by_scene.items():
        # 在场集合单调累积（按 (seq, ord) 顺序扫描；本模块只取并集，故顺序对结果无影响）
        l2 = sorted(lst, key=lambda t: (t[0]["seq"], t[1]["ord"]))
        seen = []
        for r, f in l2:
            s = f.get("slot")
            if s is not None and s not in seen:
                seen.append(s)
        slots = sorted(seen)
        if reverse:
            slots = list(reversed(slots))
        rank = {s: i for i, s in enumerate(slots)}
        for r, f in lst:
            s = f.get("slot")
            if s is None:
                zmap[(scene, r["file_idx"])] = ""
                continue
            if f.get("has_fb"):
                zmap[(scene, r["file_idx"])] = ""      # 层序规则未覆盖
                continue
            zmap[(scene, r["file_idx"])] = str(rank[s])
        scenes[scene] = (slots, rank)
    return build, zmap, scenes


def write_scene_table(reverse=False):
    head = ["scene_id", "src", "在场槽(升序)", "槽数", "rank映射", "行数", "z_rank可用行"]
    lines = ["\t".join(head)]
    for src in P.SRCS:
        build, zmap, scenes = compute_z(src, reverse=reverse)
        cnt = collections.Counter(r["scene_id"] for r, f in build)
        zcnt = collections.Counter()
        for (sc, fi), v in zmap.items():
            if v != "":
                zcnt[sc] += 1
        for scene in sorted(scenes):
            slots, rank = scenes[scene]
            lines.append("\t".join([
                scene, src, ",".join(str(s) for s in slots), str(len(slots)),
                ";".join("%d:%d" % (k, v) for k, v in sorted(rank.items())),
                str(cnt[scene]), str(zcnt[scene]),
            ]))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ 自证
def selfproof(reverse=False, verbose=True):
    """可失败自证。返回 (ok, msgs)。"""
    msgs = []
    ok = True

    def chk(cond, tag, detail):
        nonlocal ok
        if not cond:
            ok = False
        msgs.append(("  [%s] %s  %s" % ("PASS" if cond else "FAIL", tag, detail)))
        return cond

    # ---- P1 结构不变式（全体场景）
    nscene = 0
    nbad_bi = 0
    nbad_mono = 0
    for src in P.SRCS:
        build, zmap, scenes = compute_z(src, reverse=reverse)
        for scene, (slots, rank) in scenes.items():
            nscene += 1
            vals = sorted(rank.values())
            if vals != list(range(len(slots))):
                nbad_bi += 1
            s_sorted = sorted(slots)
            r_expect = list(range(len(s_sorted))) if not reverse else list(range(len(s_sorted) - 1, -1, -1))
            if [rank[s] for s in s_sorted] != r_expect:
                nbad_mono += 1
    chk(nbad_bi == 0, "P1a rank 是 {0..n-1} 的双射",
        "场景 %d，违规 %d" % (nscene, nbad_bi))
    chk(nbad_mono == 0, "P1b 槽号升序 ⇒ rank 升序（方向未被反转）",
        "违规 %d" % nbad_mono)

    # ---- P2 外证：s01_04i 高内(槽1) 压 明日香(槽0)（逐像素 95.34% vs 0.00%——与活体实验**同源、非独立**，只作同源复核）
    build, zmap, scenes = compute_z("ot", reverse=reverse)
    rows = [(r, f) for r, f in build if r["scene_id"] == PROOF_SCENE]
    chk(len(rows) > 0, "P2a 外证场景 %s 在语料中" % PROOF_SCENE, "%d 行" % len(rows))
    found = {}
    for r, f in rows:
        if f.get("name") in ("MAS01B", "ASU02A"):
            found.setdefault((f["name"], f["slot"]), r["file_idx"])
    chk(("MAS01B", 1) in found, "P2b 高内 MAS01B 槽=1 实测",
        "命中槽=%s" % (str(1) if ("MAS01B", 1) in found else "未命中"))
    chk(("ASU02A", 0) in found, "P2c 明日香 ASU02A 槽=0 实测",
        "命中槽=%s" % (str(0) if ("ASU02A", 0) in found else "未命中"))
    if ("MAS01B", 1) in found and ("ASU02A", 0) in found:
        r1 = zmap[(PROOF_SCENE, found[("MAS01B", 1)])]
        r0 = zmap[(PROOF_SCENE, found[("ASU02A", 0)])]
        chk(r1 != "" and r0 != "" and int(r1) > int(r0),
            "P2d 基线: rank(槽1=高内) > rank(槽0=明日香) ⇒ 高内在前（与逐像素 95.34% vs 0.00% 一致）",
            "rank1=%s rank0=%s"
            "（★2026-10-09 注：P2d 与 P2e 同属 P1b 的蕴涵式＝自证同义反复，只检出「排序方向被反转」，"
            "对层序结论不构成独立证据；逐像素判据与活体实验同源、非独立）" % (r1, r0))

    # ---- P2e 活体实验的**变异复算**：把明日香全部槽 0→2 ⇒ 明日香在前（`00_任务书.md` §8.7 Round S 实测；§8.2 决定轮已被一审打回，只作背景）
    mut = []
    for r, f in build:
        g = dict(f)
        if g.get("slot") == 0 and r["scene_id"] == PROOF_SCENE:
            g["slot"] = 2
        mut.append((r, g))
    _, zmap2, _ = compute_z("ot", build=mut, reverse=reverse)
    r1b = zmap2[(PROOF_SCENE, found[("MAS01B", 1)])]
    r2b = zmap2[(PROOF_SCENE, found[("ASU02A", 0)])]
    chk(r1b != "" and r2b != "" and int(r2b) > int(r1b),
        "P2e 改槽(明日香 0→2)后: rank(槽2=明日香) > rank(槽1=高内) ⇒ 明日香在前（对照 `00_任务书.md` §8.7 Round S 实测；§8.2 决定轮已被一审打回，只作背景）",
        "rank2=%s rank1=%s（★2026-10-09 注：本判据为 P1b 的蕴涵式＝自证同义反复，不构成独立证据）" % (r2b, r1b))

    if verbose:
        for m in msgs:
            print(m)
    return ok, msgs


# ------------------------------------------------------------------ 校验 / 写出
def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def do_emit():
    art = {OUT_SCENE: write_scene_table()}
    for name, txt in art.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
        b = txt.encode("utf-8")
        print("  WROTE %-28s %d bytes  sha256=%s" % (name, len(b), sha(b)))
    return True


def do_check(reverse=False):
    art = {OUT_SCENE: write_scene_table(reverse=reverse)}
    allpass, ndiff = True, 0
    for name, txt in sorted(art.items()):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            print("  MISS     %-28s" % name)
            allpass, ndiff = False, ndiff + 1
            continue
        with open(p, "rb") as f:
            ondisk = f.read()
        new = txt.encode("utf-8")
        if sha(ondisk) == sha(new):
            print("  OK       %-28s %d bytes  sha256=%s" % (name, len(ondisk), sha(ondisk)))
        else:
            a = ondisk.decode("utf-8").splitlines()
            b = txt.splitlines()
            d = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            print("  DIFF     %-28s %d 行不一致" % (name, d))
            allpass, ndiff = False, ndiff + 1
    print("ALL_PASS=%s  files=%d  diff_files=%d" % (allpass, len(art), ndiff))
    print("READONLY=True（本模式不写任何文件）")
    return allpass


def _ws_root_arg(argv):
    for i, a in enumerate(argv):
        if a == "--ws-root" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--ws-root="):
            return a.split("=", 1)[1]
    return None


def main(argv):
    root = _ws_root_arg(argv)
    if root:
        P.set_ws_root(root)
    miss = P.missing_inputs()
    if miss:
        print("== INPUT_MISSING（layer_by_slot 无法执行：输入缺失，非「自证/变异失败」）==")
        for p in miss:
            print("   缺输入: %s" % p)
        print("CHECK_ERROR=INPUT_MISSING  files=%d" % len(miss))
        return 3
    if "--emit" in argv:
        do_emit()
        return 0
    if "--check" in argv:
        return 0 if do_check() else 1
    if "--selfproof" in argv:
        print("== 层序自证（升序=正解）==")
        ok, _ = selfproof(reverse=False)
        print("SELFPROOF=%s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1
    if "--selfcheck-mutate" in argv:
        print("== 层序自证(变异: 层序方向反转为降序) ==")
        ok, _ = selfproof(reverse=True)
        print("MUTATE_SELFTEST=%s（期望 FAIL）" % ("PASS" if not ok else "FAIL"))
        return 0 if not ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
