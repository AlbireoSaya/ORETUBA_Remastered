# -*- coding: utf-8 -*-
"""verify_staging_psv.py —— PSV 金标时间线的**独立**校验器（不共用生成器实现）

与 `emit_staging_psv.py` 刻意走**不同的解析路径**：
生成器用「正则 + 块栈」；本器用**纯字符串切块**（`split("[Task")`）逐文件重算，
再与盘面产物交叉核对——两套实现同时错在同一处的概率极低。

判据（任一不成立即 FAIL 并打印证据行）
------------------------------------
A 场景数：`场景映射.tsv` 行数 == 生成器 `_index.json` 的 `scenes_mapped`
B 任务数守恒：对每个场景，`时间线.tsv` 该场行数 == 原文 `[TaskN]` 中带 `:Tasktype` 的块数
C 任务号存在：`时间线.tsv` 的每个 `task` 号都能在该场原文里找到 `[Task<号>]`
D 素材名覆盖：原文每个 `置換しました<<X>>` 归一化后，要么出现在该场时间线的 `name` 列，
  要么登记在 `缺口.tsv`（**不许静默丢名**）
E 时序越界：每个 `seq` ∈ 该场语料 `lines[].seq` 集合，且 1 <= seq <= line_count
F 交付路径：`status ∈ {ok,sub-eq}` 的行，其 `delivery` 必在 `交付清单.tsv` 的交付相对路径集合内
G 枚举封闭：列数恒 27、`op` ∈ 闭集、无 CR、无 BOM
H 幂等：重跑生成器 `--check` 为真（子进程）

用法：python -X utf8 工具/verify_staging_psv.py [--out <产出口>] [--data-root <根>]
"""
import argparse
import collections
import io
import json
import os
import re
import subprocess
import sys

ROOT_DEFAULT = r"E:\ZCode Workspace\Galgame"
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原")
PSV_REL = os.path.join("工程", "我们没有翅膀PSV", "脚本解包")

OP_CLOSED = {
    "bg", "bg_move", "bg_move_end", "bg_remove", "bg_priority",
    "chr_add", "chr_remove", "chr_move", "chr_expr", "chr_expr_end",
    "chr_priority", "chr_wait",
    "se", "se_stop", "bgm", "bgm_stop", "movie", "movie_stop", "voice",
    "effect", "ui", "control", "wait", "text", "other",
}
NCOL = 27
FAILS = []


def fail(tag, msg):
    FAILS.append("[%s] %s" % (tag, msg))


def rd(p):
    with open(p, "rb") as f:
        return f.read().decode("cp932", "replace")


def raw_task_chunks(text):
    """字符串切块：`[Task` 之间的片段。返回 [(num, body)]。"""
    out = []
    for ch in text.split("[Task")[1:]:
        i = ch.find("]")
        if i < 0:
            continue
        num = ch[:i].strip()
        if not num.isdigit():
            continue
        nxt = ch.find("[Task")
        out.append((num, ch[i:]))
    return out


def tasks_with_type(text):
    """返回 [(num, tasktype, raw_body)]，只用字符串切分。"""
    out = []
    for num, body in raw_task_chunks(text):
        tt = ""
        for ln in body.split("\n"):
            s = ln.strip()
            if s.startswith(":Tasktype"):
                v = s[len(":Tasktype"):].strip()
                if v.startswith('"'):
                    tt = v[1:].split('"')[0]
                break
        if tt:
            out.append((num, tt, body))
    return out


def _nz(s):
    s = os.path.splitext(s)[0].upper()
    return s[3:] if s.startswith("ST_") else s


RES_KEYS = (":Texture", ":SpriteNumber", ":Sprite", ":Number", ":Character",
            ":SE", ":Voice")


def names_in(body):
    """该任务体里每处**资源键行** → {原版名(首个 // 注释段若为纯 ASCII 词), 置換名}。

    与生成器同规则、**独立实现**：生成器优先取原版名（我方库是 PC 派生，实测 SE 两侧名不同），
    本器把两个名都算作「可接受」，只要时间线里有其一即算覆盖。
    只认资源键行——避免把 `// wait_se_stop` 这类**注释注解**误当名字（实测踩到）。
    """
    res = []
    for ln in body.split("\n"):
        if ln.lstrip().startswith("//"):
            continue
        mk = re.match(r"^\s*(:[\w_]+)[\s\t]", ln)
        if not mk or mk.group(1) not in RES_KEYS:
            continue
        exp = set()
        first = ln.split("//")[1].strip() if "//" in ln else ""
        if re.match(r"^[A-Za-z_][\w]*$", first):
            exp.add(_nz(first))
        for part in ln.split("置換しました<<")[1:]:
            if ">>" in part:
                exp.add(_nz(part.split(">>")[0].strip()))
        exp.discard("")
        if exp:
            res.append(exp)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=ROOT_DEFAULT)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = a.data_root
    proj = os.path.join(root, PROJ_REL)
    psv_dir = os.path.join(root, PSV_REL)
    out_dir = a.out or os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PSV演出"))
    corpus_dir = os.path.join(proj, "资源组", "剧本")

    tl_path = os.path.join(out_dir, "时间线.tsv")
    sm_path = os.path.join(out_dir, "场景映射.tsv")
    gp_path = os.path.join(out_dir, "缺口.tsv")
    ix_path = os.path.join(out_dir, "_index.json")
    for p in (tl_path, sm_path, gp_path, ix_path):
        if not os.path.isfile(p):
            fail("存在", "缺产物：%s" % p)
            print("\n".join(FAILS))
            return 1

    # ---- 读产物
    raw_tl = io.open(tl_path, "r", encoding="utf-8", newline="").read()
    if raw_tl.startswith("\ufeff"):
        fail("G", "时间线.tsv 带 BOM")
    if "\r" in raw_tl:
        fail("G", "时间线.tsv 含 CR")
    trows = raw_tl.split("\n")
    while trows and trows[-1] == "":
        trows.pop()
    head = trows[0].split("\t")
    if len(head) != NCOL:
        fail("G", "表头列数 %d != %d" % (len(head), NCOL))
    tl = [dict(zip(head, r.split("\t"))) for r in trows[1:]]
    for r in tl:
        if r["op"] not in OP_CLOSED:
            fail("G", "op 越界：%s" % r["op"])
            break

    smraw = io.open(sm_path, "r", encoding="utf-8", newline="").read().rstrip("\n").split("\n")
    smh = smraw[0].split("\t")
    sm = [dict(zip(smh, r.split("\t"))) for r in smraw[1:]]
    idx = json.loads(io.open(ix_path, "r", encoding="utf-8").read())

    gapnames = {}
    for r in io.open(gp_path, "r", encoding="utf-8").read().rstrip("\n").split("\n")[1:]:
        c = r.split("\t")
        if len(c) >= 2:
            gapnames[(c[0], c[1])] = int(c[3]) if len(c) > 3 and c[3].isdigit() else 0

    # ---- A 场景数
    if len(sm) != idx.get("scenes_mapped"):
        fail("A", "场景映射行数 %d != _index.scenes_mapped %s" % (len(sm), idx.get("scenes_mapped")))

    # ---- 语料 seq 集合
    corpus = {}
    for src in ("ot", "otv", "otp", "otr", "ota", "np"):
        p = os.path.join(corpus_dir, "scene_%s.jsonl" % src)
        if not os.path.isfile(p):
            continue
        for ln in io.open(p, "r", encoding="utf-8"):
            if ln.strip():
                d = json.loads(ln)
                corpus[d["scene_id"]] = d

    # 交付层集合
    deliv_ok = set()
    dp = os.path.join(proj, "资源组", "美术统一_交付", "交付清单.tsv")
    if os.path.isfile(dp):
        with io.open(dp, "r", encoding="utf-8-sig") as f:
            f.readline()
            for ln in f:
                c = ln.rstrip("\n").split("\t")
                if len(c) >= 5:
                    deliv_ok.add(c[4].replace("\\", "/").lower())
    else:
        fail("F", "缺交付清单：%s" % dp)
    lib_krkr = os.path.join(proj, "资源组", "krkr素材库")

    # ---- 按场聚合时间线
    by_scene = {}
    for r in tl:
        by_scene.setdefault(r["scene_id"], []).append(r)

    n_scene_chk = 0
    for s in sm:
        sid, fn = s["scene_id"], s["script"]
        rp = os.path.join(psv_dir, fn)
        if not os.path.isfile(rp):
            fail("C", "%s 原文缺失：%s" % (sid, rp))
            continue
        text = rd(rp)
        rtasks = tasks_with_type(text)
        rows = by_scene.get(sid, [])
        # B 任务类型多重集守恒：原文行首 `:Tasktype "X"` 的**逐类型计数** == 时间线里
        #   **去重后的 (task, type) 对**的逐类型计数（一任务多类型、多 Chara 同行都不影响；
        #   不依赖任何「匿名块」检测，故为独立判据）
        raw_types = collections.Counter(
            re.findall(r'^[ \t]*:Tasktype[ \t]+"([^"]*)"', text, re.M))
        pairs = set((r["task"], r["type"]) for r in rows)
        tl_types = collections.Counter(t for _, t in pairs)
        if tl_types != raw_types:
            diff = []
            for k in set(list(raw_types) + list(tl_types)):
                if raw_types.get(k) != tl_types.get(k):
                    diff.append("%s 原文%s/时间线%s" % (k, raw_types.get(k), tl_types.get(k)))
            fail("B", "%s 任务类型计数不符：%s" % (sid, "；".join(diff[:6])))
        # C 任务号存在（数字号须在原文有 `[TaskN]`；anon 号是无标号块，跳过）
        rnums = set(n for n, _, _ in rtasks)
        for tid in set(r["task"] for r in rows):
            if tid.startswith("anon"):
                continue
            if tid not in rnums:
                fail("C", "%s task %s 不在原文" % (sid, tid))
                break
        # D 素材名覆盖：原文每处资源行的名字（原版名/置換名任一）必须出现在该场时间线，
        #   或在 `缺口.tsv` 登记（语音名不在缺口表内，故用后缀白名单豁免）
        tl_names = set(r["name"] for r in rows if r["name"])
        for num, tt, body in rtasks:
            miss = None
            for exp in names_in(body):
                if exp & tl_names:
                    continue
                if tt in ("Message", "SceneJumpDialog", "SetSceneName", "Tag"):
                    continue
                if any((s["src"], n) in gapnames or any(k[1] == n for k in gapnames)
                       for n in exp):
                    continue
                miss = sorted(exp)
                break
            if miss:
                fail("D", "%s task %s (%s) 的名字 %s 既不在时间线也未登记缺口"
                     % (sid, num, tt, "/".join(miss)))
                break
        # E 时序越界
        d = corpus.get(sid)
        if d:
            seqs = set(x.get("seq") for x in d.get("lines", []))
            n = len(d.get("lines", []))
            for r in rows:
                try:
                    v = int(r["seq"])
                except ValueError:
                    fail("E", "%s seq 非整数：%r" % (sid, r["seq"]))
                    break
                if v not in seqs or v < 1 or v > n:
                    fail("E", "%s seq=%s 越界（line_count=%d）" % (sid, v, n))
                    break
        # F 交付路径（覆盖**所有**非空 delivery；se/bgm 不在交付清单内 ⇒ 直接查库盘）
        for r in rows:
            d = r["delivery"]
            if not d or r["status"] == "missing":
                continue
            dl = d.replace("\\", "/").lower()
            if dl.startswith(("se/", "bgm/")):
                src = sid.split("_", 1)[0]
                if not os.path.isfile(os.path.join(lib_krkr, src, d.replace("/", os.sep))):
                    fail("F", "%s SE/BGM 库盘缺件：%s" % (sid, d))
                    break
            elif dl not in deliv_ok:
                fail("F", "%s 交付路径不在清单：%s" % (sid, d))
                break
        n_scene_chk += 1

    # ---- D2 缺口表双向一致：时间线里 status=missing 的（源,名）集合 == 缺口.tsv 的键集合
    #      （语音名不入缺口表，故排除）
    # 时间线无 `src` 列（源由 scene_id 前缀唯一决定），就地推导
    tl_missing = set((r["scene_id"].split("_", 1)[0], r["name"]) for r in tl
                     if r["name"] and r["status"] == "missing" and r["kind"] != "voice")
    gap_set = set(gapnames.keys())
    if tl_missing != gap_set:
        only_tl = sorted(tl_missing - gap_set)[:6]
        only_gap = sorted(gap_set - tl_missing)[:6]
        fail("D2", "缺口表与时间线 missing 行不一致：仅时间线 %s；仅缺口表 %s"
             % (only_tl, only_gap))

    # ---- H 幂等（重跑生成器 --check）
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_staging_psv.py")
    try:
        pr = subprocess.run([sys.executable, "-X", "utf8", gen, "--check",
                             "--data-root", root, "--out", out_dir],
                            capture_output=True, timeout=900)
        if pr.returncode != 0:
            fail("H", "生成器 --check 非 0：%s" % pr.stdout.decode("utf-8", "replace")[-400:])
    except Exception as e:
        fail("H", "生成器 --check 调用失败：%s" % e)

    print("逐场核对 %d 场；时间线行 %d；缺口名 %d" % (n_scene_chk, len(tl), len(gapnames)))
    if FAILS:
        print("\n=== FAIL %d ===" % len(FAILS))
        for f in FAILS[:60]:
            print(" ", f)
        print("ALL_PASS = False")
        return 1
    print("ALL_PASS = True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
