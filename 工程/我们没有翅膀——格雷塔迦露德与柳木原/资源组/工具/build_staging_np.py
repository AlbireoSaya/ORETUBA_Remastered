#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
np（涅布＊普拉斯 / BGI-Ethornell）逐行演出表生成器
================================================================================
ISSUE-20261001-14 ｜ 消费契约提出方＝编程组（`编程组\移交资源组_逐行演出数据任务书.md` §三）
产物：`资源组\演出\演出_np.tsv`（UTF-8 无 BOM、TAB、无引号、首行表头、9 列固定顺序）。

契约唯一实现＝同目录 `_staging_common.py`（本模块**只用它的** `Ledger` / `SeqMap` / `row` /
`skip_row` / `write_tsv` / `assert_scene_coverage` / `path_ref` / `family_of`，不另写一份）。

--------------------------------------------------------------------------------
复跑命令
--------------------------------------------------------------------------------
    # 生成（写本 checkout 的 资源组\演出\演出_np.tsv）
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_np.py"

    # 幂等自检：不落盘，只把「本次重算的字节」与磁盘现有产物逐字节比对
    python -X utf8 "…/build_staging_np.py" --check

    # 附加：把本表 op=bgm 行与既有 `交接编程组\BGM切换点.tsv` 的 np 段逐条比对（只读）
    python -X utf8 "…/build_staging_np.py" --compare-bgm

    读 = `GRETA_DATA_ROOT`（默认 `E:\ZCode Workspace\Galgame`）；写 = 本脚本所在 checkout。

--------------------------------------------------------------------------------
口径（**与 `_staging_common` 文档头一致，不另立口径**）
--------------------------------------------------------------------------------
* `seq`：1-based，与 `剧本\scene_np.jsonl` 的 `lines[].seq` 同坐标系（实测 np 无空槽，
  `len(lines)==line_count`，且 `lines[k].seq == k+1`）。某常量落在常量池下标 p ⇒ 其 `seq`
  ＝**紧随 p 之后的第一个文本行的行号**；之后本场无文本行 ⇒ 末行行号（`after_last_line`）；
  在首行之前 ⇒ 1（`before_first_line`）。`skip` 行 `seq=0`。→ 用 `_staging_common.SeqMap`。
* `op`：闭集 `chr_add chr_remove chr_move chr_expr bg se bgm movie wait effect other skip`。
  本源只产出**资源常量**对应的 op：`chr→chr_add`、`pic→bg`、`se→se`、`bgm→bgm`、`movie→movie`。
* `target`：`krkr素材库\资源总账.json` 的 `out_relpath`，**按源分域** `Ledger.target(kind, token, 'np')`。
* `evidence`：`script=<脚本名>; .bs5 常量池偏移 0x<hex> '<常量串>' 邻近命令 <_Command>`；**不写注释行号**。
  当该常量在池中**紧邻**的后续条目不是命令名时（命令名已在池内去重，见下「上限」），写
  `邻近命令 <不可见：该命令名已于池内去重>`，不臆造。
* `confidence`：np 只能靠**常量池首次引用序**推定（任务书 §3.4：`exact` 仅留给源侧直证）⇒ 一律 `inferred`；
  `skip` 行 `unknown`。

--------------------------------------------------------------------------------
np `.bs5` 常量池模型（实测，ISSUE-20261001-14）
--------------------------------------------------------------------------------
* `data01100.arc\` 下 82 个脚本（文件头 magic `BurikoCompiledScriptVer1.00`）＋ `_文本样例.txt`（非脚本）。
* 池是「**首次引用序**」的扁平静态串表：文本槽、资源令牌、命令名交错，**无 opcode 表**。
* **命令名每个脚本恰好注册一次**（全 82 脚本实测 `count==once_in_script`），无论它被调用几次；
  故命令名只能定位到**首次调用**，且**同一令牌的第二次引用不再入池** ⇒ 同场第二次播放 / 纯淡出 /
  纯停止 / 数值操作数（时长·坐标·音量·淡入时间）**一律不可见**。
* 资源令牌是**裸令牌**（`BG72` / `SE768` / `bgm05A` / `ASU_D05S`），**不是 `PIC\…` 路径串**
  （`_staging_common.path_ref` 对本源池实测返回 `(None,None)`，即本源无路径形引用）。
* 识别资源令牌的唯一判据＝**在 `Ledger` 的 `(kind,'np')` 域内命中**（token = `splitext(orig_name)[0].upper()`），
  并附加「纯 ASCII 可打印」过滤以排除字节码区噪声解出的伪串。

--------------------------------------------------------------------------------
本表**未**产出的 op（及其理由，如实登记）
--------------------------------------------------------------------------------
* `wait` / `effect` / `other`：命令名在池中只出现一次，**调用次数不可见**；若按「一次一条」落表，
  会把「本场 20 次 `_Quake`」写成「一次」，属误导 ⇒ 不产出（见交付报告「未决问题」）。
* `chr_remove` / `chr_move` / `chr_expr`：池内**无删除类命令名**（全 127 个命令令牌里无 `_DeleteBS`/
  `_HideBS`/`_EraseBS`），且命令名去重使「哪次调用对应哪个令牌」不可辨 ⇒ 立绘子动作不可判定，
  统一记 `chr_add`（**立绘引用**）并在 `evidence` 注明（任务书 §4.3 已列该上限）。
* `movie`：np 场景池内无 movie 令牌（`np_makerlogo` / `np_navelplusop.mpg` 属非场景引用）⇒ 0 行。

--------------------------------------------------------------------------------
生成器内置闸门（**都能真失败**）
--------------------------------------------------------------------------------
 1. **文本槽守恒**：每个场景池内按 `lines[].jp` 顺序匹配到的文本槽数 == `line_count`
    （并预断言 `len([l.jp for l in lines if l.jp]) == line_count`，即无空槽）。
 2. **逐场景集合守恒**：本场 `op=bg` 的 target 令牌集 ⊇ 本场 `assets[]` 中 `kind=pic` 且 `hit=true`；
    `op=se` ⊇ `kind=se`；`op=bgm` ⊇ `kind=bgm`；`op=chr_*` ⊇ `kind=chr`（kind 为空则跳过）。
    `hit=false` 的 assets（不在资源总账，无统一名）**不参与**该闸门，逐条登记进报告。
 3. **场景覆盖**：`_staging_common.assert_scene_coverage(rows, 全部 scene_id, 'np')`。
 4. **幂等**：`--check` 下本次重算字节与磁盘产物逐字节相同，否则 FAIL。
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import sys

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _staging_common as C      # noqa: E402  契约唯一实现（必须共用）

SRC = "np"
NP_ARC = C.NP_ARC                                                        # 读：主工作区
SCENE_JSONL = os.path.join(C.RES, "剧本", "scene_np.jsonl")              # 读：主工作区
BGM_SWITCH_TSV = os.path.join(C.RES_LOCAL, "交接编程组", "BGM切换点.tsv")  # 读：本 checkout 既有产物
TSV_OUT = C.tsv_path(SRC)                                                # 写：本 checkout 演出\演出_np.tsv

MAGIC = b"BurikoCompiledScriptVer1.00"
CMD_RE = re.compile(r"^_[A-Za-z][A-Za-z0-9_]{1,}$")   # 真命令名（滤掉噪声 `_` / `_q`）
NUM_RE = re.compile(r"^[+-]?\d+$")
SEP_RE = re.compile(r"^[_\$\[\]\^ ]+$")
VOICE_RE = re.compile(r"^(?:VOICE|Voice)[\\/]")
ASCII_RE = re.compile(r"^[\x20-\x7e]+$")

KIND_ORDER = ("chr", "pic", "se", "bgm", "movie")
KIND_OP = {"chr": "chr_add", "pic": "bg", "se": "se", "bgm": "bgm", "movie": "movie"}

# 「邻近命令」只在**命令与该令牌 kind 语义一致**时才写入 evidence（否则记 <不可见>）。
# 依据：命令名每脚本只注册一次 ⇒ 相邻命令名**未必**是它的所属命令（实测反例 `bg`→`_DrawBS`、
# `se`→`_Font`、`bgm`→`_ScrollBG` 等跨 kind 误配）。故保守化，只保留可判定的同语义命令。
KIND_CMDS = {
    "pic": {"_DrawScene", "_FadeScene", "_DrawBG", "_FadeBG", "_WaveBG", "_ScrollBG",
            "_EnlargeBG", "_RotateBG", "_ShakeBG", "_StartBGShaking", "_StopShakingBG",
            "_DrawSceneByVirtualBG", "_WaitToFinishBGControlling", "_FadeSceneSkipping",
            "_EyeCatchIn", "_EyeCatchOut", "_DrawFilm", "_FadeFilm", "_DrawFilmSx",
            "_WaitToFinishFilmControlling",
            "_DrawSPR", "_FadeSPR", "_MoveSPR", "_ShakeSPR", "_ShiftSPR", "_StopShakingSPR"},
    "chr": {"_DrawBS", "_FadeBS", "_MoveBS", "_MoveRepeatBS", "_ShakeBS", "_RecipBS",
            "_ShiftBS", "_StopShakingBS", "_StartBSShaking",
            "_SetBustshotForSynchronizedFaceDrawing", "_OrderBS",
            "_RegisterSynchronizedFaceDrawing", "_StartSynchronizedFaceDrawingRegister",
            "_EndSynchronizedFaceDrawingRegister"},
    "se": {"_PlaySE", "_PlayStreamSE", "_FadeSE", "_FadeStreamSE", "_StopSE",
           "_StopStreamSE", "_WaitToFinishSE", "_ChangeVolumeOfStreamSE"},
    "bgm": {"_PlayBGM", "_FadeBGM", "_StopBGM", "_ChangeVolumeOfBGM"},
    "movie": {"_PlayMovie"},
}


# ================================================================ 常量池扫描
def scan_pool(path):
    """扫 `.bs5` 全文件 → 按偏移升序的 `(offset, string)`（NUL/非可打印字节为界，cp932 解码）。

    与 `build_bgm_switch_points.py::scan_pool` 同口径（cp932 合法尾字节含 0x80–0xFC）。
    """
    data = open(path, "rb").read()
    out = []
    cur = bytearray()
    start = None
    for i, b in enumerate(data):
        if 0x20 <= b <= 0x7E or 0x80 <= b <= 0xFC:
            if start is None:
                start = i
            cur.append(b)
        else:
            if start is not None and len(cur) >= 1:
                try:
                    out.append((start, cur.decode("cp932")))
                except UnicodeDecodeError:
                    pass
            cur, start = bytearray(), None
    return out


def ledger_kind(ledger, s):
    """池串 → `(kind, TOKEN)`；非资源令牌返回 `(None, None)`。按 `KIND_ORDER` 分域命中断言唯一。"""
    if not s or not ASCII_RE.match(s):
        return None, None
    su = s.upper()
    hit = [k for k in KIND_ORDER if ledger.target(k, su, SRC) is not None]
    if not hit:
        return None, None
    if len(hit) > 1:
        raise SystemExit("!! 令牌跨 kind 命中（不应发生）：%r -> %s" % (s, hit))
    return hit[0], su


def next_command(pool, i, kind_of_index):
    """常量池下标 i 起，跳过紧随其后的**同 kind** 资源令牌，若下一个条目是**同语义**命令名则返回之。

    命令名每个脚本恰好注册一次 ⇒ 命令名只可能紧邻其**首次调用**的实参。跳过同 kind 连续令牌，
    是为让 A/B 成对（`bgm05A`,`bgm05B`,`_PlayBGM`）的两个令牌都拿到命令；跨 kind 则停，
    避免把孤立的旧令牌误配到后面新注册的别的命令上（实测 `SE772`,`KUR01D`,`_MoveBS`）。
    再用 `KIND_CMDS` 白名单过滤：**跨语义的命令名一律不采**（命令名去重使其相邻未必是所属）。
    """
    kind = kind_of_index.get(i)
    j = i + 1
    while j < len(pool) and kind_of_index.get(j) == kind:
        j += 1
    if j < len(pool):
        s = pool[j][1]
        if CMD_RE.match(s) and s in KIND_CMDS.get(kind, ()):
            return s
    return None


def classify_drop(s):
    """非文本/非命令/非资源 的池串 → 丢弃类别（`_staging_common.DROP_KINDS` 子集或 `noise`）。"""
    if s == "":
        return "empty"
    if NUM_RE.match(s):
        return "numeric"
    if SEP_RE.match(s):
        return "separator"
    if VOICE_RE.match(s):
        return "voice"
    if "ScSkip" in s or "SsSkip" in s:
        return "scskip"
    return "noise"


# ================================================================ 核心
def build(ledger):
    scenes = [json.loads(ln) for ln in io.open(SCENE_JSONL, encoding="utf-8") if ln.strip()]
    scene_ids = [o["scene_id"] for o in scenes]

    rows = []
    stats = {
        "scenes": len(scenes),
        "lines": sum(o["line_count"] for o in scenes),
        "text_slots": 0,
        "pool_entries": 0,
        "commands_seen": 0,
        "drops": collections.Counter(),
        "resource_hits": collections.Counter(),
        "skip": [],
    }
    conserve_fail = []
    extras_by_scene = {}
    unresolved_assets = []          # hit=false（无统一名），逐条
    covered_by_rows = collections.defaultdict(set)   # scene -> "kind:ref"
    skip_scene_assets = []          # skip 场景里 hit=true 的 assets（无法锚定）

    for o in scenes:
        sid, script = o["scene_id"], o["script"]
        path = os.path.join(NP_ARC, script)
        if not os.path.isfile(path):
            raise SystemExit("!! 脚本缺失：%s" % path)

        jp_lines = [l for l in o["lines"] if l.get("jp")]
        if len(jp_lines) != o["line_count"]:
            raise SystemExit("!! [%s] 存在空槽行（jp 为空）：%d != line_count %d"
                             % (script, len(jp_lines), o["line_count"]))
        want = [l["jp"] for l in jp_lines]

        pool = scan_pool(path)
        stats["pool_entries"] += len(pool)

        idx = 0
        matched = []                 # [(pool_index, lines[].seq)]，单调递增
        hits = []                    # [(pool_index, offset, token, kind)]
        seen_tok = set()             # 去重：同一令牌只认首次引用
        for i, (off, s) in enumerate(pool):
            if idx < len(want) and s == want[idx]:
                matched.append((i, jp_lines[idx]["seq"]))
                idx += 1
                continue
            if s.startswith("_") and CMD_RE.match(s):
                stats["commands_seen"] += 1
                continue
            kind, tok = ledger_kind(ledger, s)
            if kind is not None:
                key = (kind, tok)
                if key in seen_tok:
                    continue
                seen_tok.add(key)
                hits.append((i, off, tok, kind))
                continue
            # 路径形引用（本源实测 0 条；保留以复用契约的 path_ref）
            pk, ptok = C.path_ref(s)
            if pk is not None and ptok is not None:
                raise SystemExit("!! [%s] 池内出现路径形资源引用（未预期）：%r -> %s/%s"
                                 % (script, s, pk, ptok))
            stats["drops"][classify_drop(s)] += 1

        if idx != len(want):
            raise SystemExit("!! [闸门1] [%s] 文本槽守恒失败：池内匹配 %d / 期望 %d"
                             % (script, idx, len(want)))
        stats["text_slots"] += idx

        if not matched:
            reason = "0 文本行（仅 END 类素材常量，无法锚定到任何 lines[].seq）"
            rows.append(C.skip_row(sid, script, reason))
            stats["skip"].append([script, reason])
            for a in o["assets"]:
                if a["hit"]:
                    skip_scene_assets.append([script, a["kind"], a["ref"]])
            continue
        if not hits:
            reason = "脚本常量池无逐行演出资源常量（菜单/控制脚本）"
            rows.append(C.skip_row(sid, script, reason))
            stats["skip"].append([script, reason])
            for a in o["assets"]:
                if a["hit"]:
                    skip_scene_assets.append([script, a["kind"], a["ref"]])
            continue

        sm = C.SeqMap(matched)
        kind_of_index = {i: k for (i, _o, _t, k) in hits}
        for i, off, tok, kind in hits:
            target = ledger.target(kind, tok, SRC)
            assert target, "target 解析失败：%s/%s" % (kind, tok)
            seq, tag = sm.seq_for(i)
            cmd = next_command(pool, i, kind_of_index)
            ev = "script=%s; .bs5 常量池偏移 0x%05X '%s' 邻近命令 %s" % (
                script, off, tok,
                cmd if cmd else "<不可见：该命令名已于池内去重>")
            if kind == "chr":
                fam = C.family_of(tok)
                if fam:
                    ev += "；族=%s" % fam
            if tag == "before_first_line":
                ev += "；before_first_line"
            elif tag == "after_last_line":
                ev += "；after_last_line"
            rows.append(C.row(sid, seq, KIND_OP[kind], target=target,
                              arg1=("play" if kind == "bgm" else ""),
                              arg2="", arg3="", evidence=ev, confidence="inferred"))
            stats["resource_hits"][kind] += 1
            covered_by_rows[sid].add("%s:%s" % (kind, tok))

        # ---- 闸门2：逐场景集合守恒（仅 hit=true 的 assets 参与）
        for a in o["assets"]:
            if not a["hit"]:
                unresolved_assets.append([script, a["kind"], a["ref"]])
        for kind in KIND_ORDER:
            need = {a["ref"].upper() for a in o["assets"] if a["hit"] and a["kind"] == kind}
            have = {t for (_i, _o, t, k) in hits if k == kind}
            if not need <= have:
                conserve_fail.append([script, kind, sorted(need - have)])
            extra = have - {a["ref"].upper() for a in o["assets"] if a["kind"] == kind}
            if extra:
                extras_by_scene.setdefault(script, {})[kind] = sorted(extra)

    stats["drops"] = dict(stats["drops"])

    if conserve_fail:
        for x in conserve_fail:
            print("   x 集合守恒失败:", x)
        raise SystemExit("!! [闸门2] 逐场景集合守恒失败 %d 处" % len(conserve_fail))
    C.assert_scene_coverage(rows, scene_ids, SRC)     # 闸门3

    # 排序：场景（jsonl 顺序）× seq；Python sort 稳定 ⇒ 同 seq 保留插入序（＝池内物理先后）
    order = {sid: n for n, sid in enumerate(scene_ids)}
    rows.sort(key=lambda r: (order[r["scene_id"]], r["seq"]))

    stats["rows"] = len(rows)
    stats["resource_hits"] = dict(stats["resource_hits"])
    stats["by_op"] = dict(collections.Counter(r["op"] for r in rows))
    stats["by_confidence"] = dict(collections.Counter(r["confidence"] for r in rows))
    stats["scenes_with_rows"] = len({r["scene_id"] for r in rows if r["op"] != "skip"})
    stats["skip_scenes"] = [s for s, _ in stats["skip"]]
    stats["extras_vs_assets"] = extras_by_scene
    stats["assets_without_target"] = unresolved_assets
    stats["skip_scene_assets_unanchored"] = skip_scene_assets
    return rows, stats


def serialize(rows):
    """与 `_staging_common.write_tsv` 完全同式的字节串（供 `--check` 逐字节比对）。"""
    out = ["\t".join(C.HEADER)]
    for r in rows:
        out.append("\t".join(str(r[c]) for c in C.HEADER))
    return ("\n".join(out) + "\n").encode("utf-8")


# ================================================================ 与 BGM切换点.tsv 比对
def compare_bgm(rows):
    if not os.path.isfile(BGM_SWITCH_TSV):
        return {"status": "SKIP", "reason": "无 %s" % BGM_SWITCH_TSV}
    theirs = []
    with io.open(BGM_SWITCH_TSV, encoding="utf-8", newline="") as f:
        head = f.readline().rstrip("\n").split("\t")
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) != len(head):
                continue
            r = dict(zip(head, p))
            if r.get("源") == SRC:
                theirs.append(r)
    mine = collections.defaultdict(set)      # (scene, seq) -> {编号}
    for r in rows:
        if r["op"] != "bgm":
            continue
        num = re.search(r"bgm(\d+)", os.path.basename(r["target"]), re.I)
        mine[(r["scene_id"], r["seq"])].add(num.group(1).lstrip("0") or "0"
                                            if num else "?")

    diffs, ok = [], 0
    for t in theirs:
        exp_seq = int(t["在seq之后"]) + 1     # 口径换算：本表 seq = 「在seq之后」+1
        num = str(int(t["bgm编号"]))
        got = mine.get((t["场景id"], exp_seq))
        if got == {num}:
            ok += 1
        else:
            diffs.append({"场景id": t["场景id"], "在seq之后": t["在seq之后"],
                          "本表应有seq": exp_seq, "编号": num,
                          "本表该点实有": sorted(got) if got else None})
    their_keys = {(t["场景id"], int(t["在seq之后"]) + 1) for t in theirs}
    extra = [{"scene": k[0], "seq": k[1], "编号": sorted(v)}
             for k, v in sorted(mine.items()) if k not in their_keys]
    return {"status": "OK", "切换点表行数": len(theirs), "一致": ok,
            "不一致": diffs, "本表多出（无对应切换点）": extra,
            "口径": "本表 seq = BGM切换点.tsv 的「在seq之后」+ 1；"
                    "切换点表把 A/B 成对合并为 1 点，本表按素材总账各留 1 行（A、B 各一）"}


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="不落盘，仅把本次重算字节与磁盘产物逐字节比对")
    ap.add_argument("--compare-bgm", action="store_true",
                    help="附加：与 交接编程组\\BGM切换点.tsv 的 np 段逐条比对（只读）")
    a = ap.parse_args()

    ledger = C.Ledger.load()
    rows, stats = build(ledger)
    payload = serialize(rows)

    if a.check:
        if not os.path.isfile(TSV_OUT):
            raise SystemExit("!! [闸门4] --check 失败：产物不存在 %s" % TSV_OUT)
        # 行尾规范化后比较（autocrlf 检出的盘面是 CRLF；见 交接说明 C12）
        on_disk = C.read_artifact_bytes(TSV_OUT)
        same = (on_disk == payload)
        stats["check_bytes_equal"] = same
        stats["check_len_bytes"] = [len(on_disk), len(payload)]
        print(json.dumps(stats, ensure_ascii=False, indent=1))
        if not same:
            raise SystemExit("!! [闸门4] 幂等失败：重算字节与磁盘产物不同")
        print("[闸门4] 幂等 PASS（逐字节相同；行尾已规范化比较）")
    else:
        n = C.write_tsv(TSV_OUT, rows)      # 闸门：枚举/列数/seq/evidence 内置
        stats["written"] = n
        stats["out"] = TSV_OUT
        stats["ledger_collisions"] = len(ledger.collisions)
        print(json.dumps(stats, ensure_ascii=False, indent=1))

    if a.compare_bgm:
        print(json.dumps(compare_bgm(rows), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
