#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_staging_p0.py —— 「演出 P0 快修」＋「B1 背景换源」自检器（编程组）
================================================================
对 **已生成** 的 `krkr\game\story\scene_*.tjs` 做只读机检，逐项复核：

  P0-B 立绘 y=0：扫描 chr_add/chr_expr 行，凡**非整屏件**（h < 内容区高）却 `y==0` 者
        即记违规（这正是整屏→立绘时 cy 被继承为 0 的缺陷签名）。
  P0-C 立绘尺寸：统计立绘高度分布（基准应 945 ＝ 1080×0.875）；报「触发自适应降缩放」
        与「可见集上限收窄」的场景数。
  P0-D 重排：统计 `chr_place`（自造、瞬时）与 `chr_move`（源侧真移位）条数。

  ★ B1（ISSUE-20261006-04）背景换源（本器新增，**独立复算，不复用 build_story 实现**）：
    B1-① 生成物里「背景层事件 / `bg[]` 指向题卡族 `ec##`」必须为 **0**；
    B1-③ 有 PSV 覆盖的场：`PSV SpriteBG 条数` 与 `生成物 op=bg 条数` **逐场差必须为 0**
          （PSV 行取「delivery 非空 且 非停用件 且 交付层有实件」为应生成集；
           sub-diff 行按默认口径**采用**，故计入）；
          ★ Minor-2 增补：逐场再比**件 basename 多重集相等**（生成件去 `bg__` vs PSV delivery
          按 build 同款归一），防「条数相等但取错件」（原仅比条数、有留白）。
    B1-④ 回落场（无 PSV 覆盖的场）逐场列出，并复算其源侧 `op=bg` 里被剔除的题卡条数
          （回落口径＝演出表 op=bg 剔题卡，**无源侧卡/背景判别**，如实登记）。

  ★ B3（过场卡，本器原有复核）：
    `story/_eyecatch.tjs` ↔ PSV `EyeCatch` **首个可实现**去重集（Major-1 别名 + Major-2 判据，
    本器**独立复算**）；键＝(场景,seq)。
    ★ Minor-2 增补：每个插点 seq 必须 ∈ 该场语料行 `lines[].sq` 集合（防 seq 越界 ⇒ 永不弹）。

退出码：0 ＝ 全部 PASS；1 ＝ 有违规。

用法：
  python -X utf8 工具/audit_staging_p0.py \
      [--proj "<proj>"] [--data-root "E:/ZCode Workspace/Galgame"] [--story <story目录>]
"""
import argparse, csv, os, re, sys
from collections import Counter

SRC_ORDER = ["ot", "otr", "ota", "otp", "otv", "np"]
ROW_RE = re.compile(
    r'%\s*\[\s*seq:(-?\d+)\s*,\s*op:"([^"]*)"\s*,\s*slot:(-?\d+)\s*,\s*fam:"([^"]*)"\s*,'
    r'\s*t:"([^"]*)"\s*,\s*x:(-?\d+)\s*,\s*y:(-?\d+)\s*,\s*w:(-?\d+)\s*,\s*h:(-?\d+)\s*,'
    r'\s*z:(-?\d+)\s*\]')
BG_RE = re.compile(r'bg:\[(.*?)\],\s*se:', re.S)
BGE_RE = re.compile(r'%\s*\[\s*a:"([^"]*)"\s*,\s*w:(-?\d+)\s*,\s*h:(-?\d+)\s*\]')
SQP_RE = re.compile(r'sq:(-?\d+)')

# ★ B3 场景别名（Major-1，ISSUE-20261006-04 一审回执）：构建集场 → 持有其 EyeCatch 的 PSV 场。
#   依据 `编程组\剧情审计_重复场景.tsv` G43–G46（完全重复 / 相似度 1.0 / otv 不入构建、otp 入构建）。
#   本器**独立复算**（不复用 emit_eyecatch 实现），故自行抄一份常量。
EYECATCH_ALIAS = {
    "otp_p03_01a": "otv_P03_01A", "otp_p03_01b": "otv_P03_01B",
    "otp_p03_01c": "otv_P03_01C", "otp_p03_01d": "otv_P03_01D",
}
# ★ 旧表兜底白名单（用户 2026-10-06 裁定）：PSV 无 `EyeCatch` 覆盖的 np/ota 5 场保留旧表插点，
#   卡号取 `资源组\交接编程组\素材引用映射.tsv` 的 `CG背景/ec*` 引用、seq=1。仅此 5 场。
FALLBACK_SCENES = ("np_a01_b0", "np_a06_b1", "ota_11_3d1", "ota_41_5", "ota_42_5")


def load_fallback_cards(proj):
    """独立复算：`素材引用映射.tsv` 里 `CG背景/ec*` 引用 → {样例场景: card}。"""
    out = {}
    p = os.path.join(proj, "资源组", "交接编程组", "素材引用映射.tsv")
    if not os.path.isfile(p):
        return out
    with open(p, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f, delimiter="\t")
        next(rd, None)
        for c in rd:
            if len(c) < 8 or "CG背景/ec" not in c[2]:
                continue
            scene = (c[6] or "").strip()
            m = re.match(r"ec0*(\d+)", os.path.basename(c[2].replace("\\", "/")))
            if scene and m:
                out.setdefault(scene, int(m.group(1)))
    return out


def is_ec_card(path):
    """题卡族（`ec##`）判据：归一化（剥目录、反复剥 `<源>_`/`<kind>__` 前缀）后 `^ec<数字>`。
    依据：B1 排除项——任何 `ec##` 素材不得进入背景层（分析 §一.3）。`ec_bg*` 不算题卡。
    ⚠️ 必须兼容**游戏内扁平名**（`build_story.take_asset` 产出 `bg__ec28.png`）——
    只剥一次 `<源>_` 会把 `bg__ec28` 剥成 `_ec28` 而漏判（本器实测踩到，故改为循环剥前缀）。"""
    b = os.path.splitext(os.path.basename((path or "").replace("\\", "/")))[0]
    prev = None
    while b != prev:
        prev = b
        b = re.sub(r"^[a-z0-9]+__?", "", b, count=1)
    return bool(re.match(r"^ec\d", b, re.I))


def project_of(data_root):
    return os.path.join(data_root, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")


def load_content_h(proj):
    p = os.path.join(proj, "UI组", "layout", "_root.json")
    try:
        import json
        o = json.load(open(p, encoding="utf-8"))
        return {k: int(v.get("h", 1080)) for k, v in (o.get("content_boxes") or {}).items()}
    except Exception:
        return {}


def scan_story(story_dir):
    scenes = {}
    for fn in sorted(os.listdir(story_dir)):
        m = re.match(r"scene_(.+)\.tjs$", fn)
        if not m:
            continue
        sid = m.group(1)
        txt = open(os.path.join(story_dir, fn), encoding="utf-8").read()
        srcm = re.search(r'src:"([^"]*)"', txt)
        src = srcm.group(1) if srcm else ""
        bgs = []
        bm = BG_RE.search(txt)
        if bm:
            for a, w, h in BGE_RE.findall(bm.group(1)):
                bgs.append((a, int(w), int(h)))
        rows = [dict(seq=int(g[0]), op=g[1], slot=int(g[2]), fam=g[3], t=g[4],
                     x=int(g[5]), y=int(g[6]), w=int(g[7]), h=int(g[8]), z=int(g[9]))
                for g in ROW_RE.findall(txt)]
        # ★ B3 新闸门（Minor-2）：语料行 seq 全集＝`lines[].sq` ⇒ 供「插点 seq ∈ 该场 sq 集合」复核。
        #   解析口径：只在 `lines:[ … ]` 数组内取 `sq:N`（op 行用的是 `seq:`；限定数组防正文误命中）。
        sqs = set(int(x) for x in SQP_RE.findall(_lines_array(txt)))
        scenes[sid] = dict(src=src, bgs=bgs, rows=rows, sqs=sqs)
    return scenes


def _lines_array(txt):
    """取出 `lines:[ … ]` 数组文本（按括号配平），供 B3 复核语料行 seq 全集。"""
    i = txt.find("lines:[")
    if i < 0:
        return ""
    j = i + len("lines:")
    depth = 0
    for k in range(j, len(txt)):
        if txt[k] == "[":
            depth += 1
        elif txt[k] == "]":
            depth -= 1
            if depth == 0:
                return txt[j:k + 1]
    return txt[j:]


def load_disabled(proj):
    p = os.path.join(proj, "资源组", "交接编程组", "停用件_禁入成品.tsv")
    out = set()
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, encoding="utf-8-sig", newline=""), delimiter="\t"):
            v = (r.get("交付路径") or "").strip()
            if v:
                out.add(v)
    return out


def load_16x9(proj):
    """16:9 覆盖表 → {交付层相对路径: 相对 `资源组\\` 的新件路径}（与 build 同口径）。"""
    m = {}
    p = os.path.join(proj, "资源组", "美术统一_交付_16比9", "交付清单.tsv")
    if not os.path.isfile(p):
        return m
    for r in csv.DictReader(open(p, encoding="utf-8-sig", newline=""), delimiter="\t"):
        old = (r.get("原件交付层路径") or "").strip().replace("\\", "/")
        new = (r.get("新件路径") or "").strip().replace("\\", "/")
        if old and new:
            m[re.sub(r"^美术统一_交付/", "", old)] = new
    return m


def psv_expect(proj, built):
    """独立复算：PSV 覆盖场的「应生成背景层事件数」（不 import build_story）。

    返回 (expected, exp_names, covered, missing_rows, other_rows)：
      expected[sid]  = 有覆盖且有实件的 SpriteBG 条数；
      exp_names[sid] = 该场应生成件的 basename 多重集（＝delivery basename 按 build 同款
                       `[^0-9A-Za-z_.\\-]→_` 归一，供 B1-③ 多重集相等复核）；
      missing_rows  = delivery 为空（status=missing）而无法取件的条数；
      other_rows    = 有 delivery 但实件缺失/停用而无法取件的条数。
    """
    psv = os.path.join(proj, "编程组", "PSV演出")
    tl = os.path.join(psv, "时间线.tsv")
    mp = os.path.join(psv, "场景映射.tsv")
    covered = set()
    if os.path.isfile(mp):
        for r in csv.DictReader(open(mp, encoding="utf-8-sig", newline=""), delimiter="\t"):
            s = (r.get("scene_id") or "").strip()
            if s:
                covered.add(s)
    dis = load_disabled(proj)
    ov = load_16x9(proj)
    exp, exp_names, missing_rows, other_rows = Counter(), {}, 0, 0
    if os.path.isfile(tl):
        for r in csv.DictReader(open(tl, encoding="utf-8-sig", newline=""), delimiter="\t"):
            sid = (r.get("scene_id") or "").strip()
            if sid not in built or sid not in covered:
                continue
            if (r.get("op") or "").strip() != "bg" or (r.get("type") or "").strip() != "SpriteBG":
                continue
            d = (r.get("delivery") or "").strip()
            if not d:
                missing_rows += 1
                continue
            if d in dis:
                other_rows += 1
                continue
            key = d.replace("\\", "/")
            src = (os.path.join(proj, "资源组", ov[key].replace("/", os.sep))
                   if key in ov else os.path.join(proj, "资源组", "美术统一_交付", key))
            if not os.path.isfile(src):
                other_rows += 1
                continue
            exp[sid] += 1
            # ★ B1-③ 多重集复核：与 build_story.take_asset 同款归一（flatten 名去 `bg__`）。
            bn = re.sub(r"[^0-9A-Za-z_.\-]", "_", os.path.basename(key))
            exp_names.setdefault(sid, Counter())[bn] += 1
    return exp, exp_names, covered, missing_rows, other_rows


def fallback_report(proj, built, covered, scenes):
    """回落场（无 PSV 覆盖且入构建）复算：源侧 op=bg 里被剔除的题卡条数。

    含**无源侧 op=bg 行**的场（total=0），故这里先把全部回落场建条。"""
    sd = os.path.join(proj, "资源组", "演出")
    rows = {}
    for sid in sorted(built - covered):
        rows[sid] = dict(src=scenes[sid]["src"], total=0, ec=0, lay=0)
    for src in SRC_ORDER:
        p = os.path.join(sd, "演出_%s.tsv" % src)
        if not os.path.isfile(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8-sig", newline=""), delimiter="\t"):
            sid = (r.get("scene_id") or "").strip()
            if sid not in rows:
                continue
            if (r.get("op") or "").strip() != "bg":
                continue
            a3 = (r.get("arg3") or "").strip()
            lay = 0 if ((src == "otv") and (a3 != "") and (a3 != "SpriteBG")) else 1
            ec = 1 if is_ec_card((r.get("target") or "").strip()) else 0
            d = rows[sid]
            d["total"] += 1
            d["ec"] += ec
            d["lay"] += lay
    return rows


def audit_eyecatch(story_dir, game_dir, proj, built, scenes):
    """★ B3 独立复核：`story/_eyecatch.tjs` ↔ PSV EyeCatch **首个可实现**去重集。

    返回 dict(keys, uniq, bad_len, bad_dup, bad_file, bad_seq, bad_seq_ex, expected)。
    expected ＝ 独立复算的「可实现插点数」：候选＝(PSV 有 EyeCatch **或** 有别名) 且入构建；
      同场按 (seq, 文件序) 取**首个可实现**卡（跳过非 mode0 / `N=-1` / 越界 / 缺件）。
      ★ Major-1 别名与 Major-2 判据在此**独立复算**（不复用 emit_eyecatch 实现）。
    bad_seq ＝ 表内插点 seq 不在该场 `lines[].sq` 集合内的条数（Minor-2 新闸门）。
    """
    table = os.path.join(story_dir, "_eyecatch.tjs")
    keys, seqs, imgs = [], [], []
    if os.path.isfile(table):
        txt = open(table, encoding="utf-8").read()
        def arr(name):
            m = re.search(name + r"\s*=\s*\[(.*?)\];", txt, re.S)
            if not m:
                return []
            return [x.strip().strip('"') for x in m.group(1).split(",") if x.strip()]
        keys = arr("o.keys"); seqs = arr("o.seqs"); imgs = arr("o.imgs")
    bad_len = 0 if (len(keys) == len(seqs) == len(imgs)) else 1
    bad_dup = len(keys) - len(set(keys))
    bad_file = 0
    for p in imgs:
        if p and not os.path.isfile(os.path.join(game_dir, p.replace("/", os.sep))):
            bad_file += 1
    # ★ Minor-2 新闸门：每个插点 seq 必须 ∈ 该场语料行 `lines[].sq`（防 seq 越界 ⇒ 永不弹）。
    bad_seq, bad_seq_ex = 0, []
    for k, s2 in zip(keys, seqs):
        sc = scenes.get(k)
        try:
            sv = int(s2)
        except (TypeError, ValueError):
            sv = None
        if sv is None or sc is None or sv not in sc.get("sqs", set()):
            bad_seq += 1
            if len(bad_seq_ex) < 8:
                bad_seq_ex.append("%s#%s" % (k, s2))
    # 独立复算
    psv = os.path.join(proj, "编程组", "PSV演出")
    ec = {}
    tl = os.path.join(psv, "时间线.tsv")
    if os.path.isfile(tl):
        for r in csv.DictReader(open(tl, encoding="utf-8-sig", newline=""), delimiter="\t"):
            if (r.get("type") or "").strip() != "EyeCatch":
                continue
            sid = (r.get("scene_id") or "").strip()
            if sid:
                ec.setdefault(sid, []).append(r)
    arch = list(range(1, 20)) + list(range(21, 30)) + list(range(31, 38))
    deliv = os.path.join(proj, "资源组", "美术统一_交付", "CG背景")

    def resolvable(card):
        """与 emit_eyecatch.find_delivery_ec 同口径（含 alt 变体兜底）。"""
        if card == 28:
            return True          # EC28 走分件合成（缺 ot 题卡套件的场当前为 0，见构建日志）
        base = "ec%02d" % card
        for e in (".png", ".jpg"):
            if os.path.isfile(os.path.join(deliv, base + e)):
                return True
        return (os.path.isdir(deliv) and
                any(f.startswith(base) and os.path.splitext(f)[1].lower() in (".png", ".jpg")
                    for f in os.listdir(deliv)))

    def rseq(r):
        try:
            return int((r.get("seq") or "0").strip() or "0")
        except ValueError:
            return 0

    fb = load_fallback_cards(proj)

    def implementable(scene):
        rows = list(ec.get(scene, [])) + list(ec.get(EYECATCH_ALIAS.get(scene, ""), []))
        if rows:
            for _i, r in sorted(enumerate(rows), key=lambda t: (rseq(t[1]), t[0])):
                parts = [x.strip() for x in (r.get("image") or "").split(",")]
                if not parts or parts[0] != "0":
                    continue
                n = parts[1] if len(parts) >= 2 else ""
                if str(n) == "-1":
                    continue
                try:
                    n = int(n)
                except ValueError:
                    continue
                if not (1 <= n <= len(arch)):
                    continue
                if resolvable(arch[n - 1]):
                    return True
            return False
        # 无 PSV EyeCatch：仅白名单 5 场走旧表兜底（用户 2026-10-06 裁定）
        if scene in FALLBACK_SCENES and scene in fb:
            return resolvable(fb[scene])
        return False

    expected = 0
    for sid in sorted((set(ec) | set(EYECATCH_ALIAS) | set(FALLBACK_SCENES)) & built):
        if implementable(sid):
            expected += 1
    return dict(keys=len(keys), uniq=len(set(keys)), bad_len=bad_len, bad_dup=bad_dup,
                bad_file=bad_file, bad_seq=bad_seq, bad_seq_ex=bad_seq_ex, expected=expected)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", default=os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))                    # 工具/ → 编程组/ → <译名>/
    ap.add_argument("--data-root", default="")
    ap.add_argument("--story", default="")
    args = ap.parse_args()
    proj = args.proj
    dproj = project_of(args.data_root) if args.data_root else proj
    story = args.story or os.path.join(proj, "编程组", "krkr", "game", "story")
    if not os.path.isdir(story):
        print("[FATAL] story 目录不存在：%s" % story)
        return 2

    ch = load_content_h(dproj)
    scenes = scan_story(story)
    built = set(scenes.keys())
    n_bg = n_place = n_move = n_chr = 0
    bg_mismatch = []
    y0_viol = []
    heights = Counter()
    tight_scenes = set()
    bg_scenes = 0
    ec_bg = []            # B1-① 生成物里指向题卡的背景事件
    ec_bgarr = []
    for sid, s in scenes.items():
        cbh = ch.get(s["src"], 1080)
        bg_ev = [r for r in s["rows"] if r["op"] == "bg"]
        n_bg += len(bg_ev)
        if bg_ev:
            bg_scenes += 1
        # bg[] 应为背景层事件按序去重
        dedup = []
        seen = set()
        for r in bg_ev:
            if r["t"] in seen:
                continue
            seen.add(r["t"])
            dedup.append((r["t"], r["w"], r["h"]))
        if [x[0] for x in s["bgs"]] != [x[0] for x in dedup]:
            bg_mismatch.append(sid)
        for r in bg_ev:
            if is_ec_card(r["t"]):
                ec_bg.append((sid, r["seq"], r["t"]))
        for a, _w, _h in s["bgs"]:
            if is_ec_card(a):
                ec_bgarr.append((sid, a))
        for r in s["rows"]:
            if r["op"] in ("chr_add", "chr_expr"):
                n_chr += 1
                if r["h"] > 0:
                    heights[r["h"]] += 1
                    if r["h"] < cbh:
                        if r["h"] < int(round(cbh * 0.875)):
                            tight_scenes.add(sid)
                        if r["y"] == 0:
                            y0_viol.append((sid, r["seq"], r["fam"], r["t"], r["w"], r["h"]))
            elif r["op"] == "chr_place":
                n_place += 1
            elif r["op"] == "chr_move":
                n_move += 1

    # ---- B1：PSV 覆盖场逐场对账 + 回落场登记 ----
    exp, exp_names, covered, miss_rows, other_rows = psv_expect(dproj, built)
    cov_built = covered & built
    diffs = []
    name_diffs = []
    for sid in sorted(cov_built):
        _bg = [r for r in scenes[sid]["rows"] if r["op"] == "bg"]
        gen = len(_bg)
        if gen != exp[sid]:
            diffs.append((sid, exp[sid], gen))
        # ★ B1-③ 多重集相等（Minor-2）：生成件 basename（去 `bg__`）vs PSV delivery basename。
        gc = Counter((os.path.basename(r["t"])[4:] if os.path.basename(r["t"]).startswith("bg__")
                      else os.path.basename(r["t"])) for r in _bg)
        en = exp_names.get(sid, Counter())
        if gc != en:
            name_diffs.append((sid, list((en - gc).elements())[:4], list((gc - en).elements())[:4]))
    cov_empty = sorted(sid for sid in cov_built if exp[sid] == 0 and
                       len([r for r in scenes[sid]["rows"] if r["op"] == "bg"]) == 0)
    fb = fallback_report(dproj, built, covered, scenes)
    fb_ec = sum(v["ec"] for v in fb.values())
    fb_total = sum(v["total"] for v in fb.values())
    fb_lay = sum(v["lay"] for v in fb.values())
    fb_empty = sum(1 for v in fb.values() if v["total"] == 0)
    by_src = Counter(v["src"] for v in fb.values())

    print("=" * 72)
    print("P0/B1 自检（ISSUE-20261006-02 / 04）｜场景 %d ｜内容区高样本 %s" % (len(scenes), ch))
    print("-" * 72)
    print("[B1-①] 背景层事件指向题卡 ec##：%d 条 ｜ bg[] 含题卡：%d 个（均须为 0）"
          % (len(ec_bg), len(ec_bgarr)))
    if ec_bg:
        print("        样例：" + "、".join("%s#%s" % (a, b) for a, b, _ in ec_bg[:8]))
    print("[B1-③] PSV 覆盖场（入构建）%d 个：PSV 应生成 %d 条 ｜ 逐场差≠0 的场 %d 个（须为 0）"
          % (len(cov_built), sum(exp.get(s, 0) for s in cov_built), len(diffs)))
    if diffs:
        print("        差异场（前 12，格式 场:PSV/生成）：" +
              "、".join("%s:%d/%d" % d for d in diffs[:12]))
    print("        B1-③ 多重集：生成件 basename（去 `bg__`）与 PSV delivery basename **不等的场 %d 个**（须为 0）%s"
          % (len(name_diffs),
             ("  样例 " + "；".join("%s 缺%s 多%s" % d for d in name_diffs[:3])) if name_diffs else ""))
    print("        PSV delivery 为空(status=missing) 无法取件 %d 条 ｜ delivery 有值但实件缺失/停用 %d 条"
          % (miss_rows, other_rows))
    print("        覆盖但 PSV 无背景层事件（生成 0 条，靠跨场景延续）：%d 个%s"
          % (len(cov_empty), ("  " + "、".join(cov_empty[:10]) + " …") if len(cov_empty) > 10 else
             ("  " + "、".join(cov_empty) if cov_empty else "")))
    print("[B1-④] 回落场 %d 个（＝入构建且无 PSV 覆盖；按源：%s）｜ 其中源侧有 op=bg 行 %d 个、无行 %d 个"
          % (len(fb), "、".join("%s %d" % (k, by_src[k]) for k in SRC_ORDER if by_src.get(k)),
             len(fb) - fb_empty, fb_empty))
    print("        源侧 op=bg 合计 %d 条 ｜ 题卡被剔 %d 条 ｜ 计背景候选 %d 条 ｜ otv 叠加层仅登记 %d 条"
          % (fb_total, fb_ec, fb_lay, fb_total - fb_lay))
    print("        回落口径＝演出表 op=bg 剔题卡（**无源侧卡/背景判别**，按最接近还原）")
    print("-" * 72)
    print("[P0-A] 生成物 stage op=bg 事件：%d 条，覆盖 %d 场" % (n_bg, bg_scenes))
    print("[P0-A] bg[] 与「背景层事件按序去重」不一致的场景：%d 个%s"
          % (len(bg_mismatch), ("  " + "、".join(bg_mismatch[:8])) if bg_mismatch else ""))
    print("[P0-D] chr_place(自造瞬时) %d 条 ｜ chr_move(源侧真移位) %d 条" % (n_place, n_move))
    print("[P0-B] 非整屏立绘 y==0 违规行：%d 条%s"
          % (len(y0_viol), "" if len(y0_viol) <= 6 else
             ("  样例 " + "、".join("%s#%d" % (v[0], v[1]) for v in y0_viol[:6]))))
    top = heights.most_common(6)
    print("[P0-C] 立绘高度分布 Top：%s" % ("、".join("%dpx×%d" % (h, c) for h, c in top)))
    print("[P0-C] 触发自适应降缩放(h<%d)的场景：%d ｜ chr_add/chr_expr 总行 %d"
          % (int(round((ch.get("ot") or 1080) * 0.875)), len(tight_scenes), n_chr))

    # ---- ★ B3：过场卡插点表 ↔ PSV EyeCatch 去重集 独立复核 ----
    game_dir = os.path.dirname(os.path.abspath(story))
    ecr = audit_eyecatch(story, game_dir, dproj, built, scenes)
    ec_ok = (ecr["bad_len"] == 0 and ecr["bad_dup"] == 0 and ecr["bad_file"] == 0
             and ecr["bad_seq"] == 0 and ecr["keys"] == ecr["expected"])
    print("-" * 72)
    print("[B3] 插点表 `story/_eyecatch.tjs`：keys %d ｜ 去重后场数 %d ｜ keys/seqs/imgs 等长 %s ｜ 重复场 %d ｜ 缺件 %d"
          % (ecr["keys"], ecr["uniq"], "OK" if ecr["bad_len"] == 0 else "✗", ecr["bad_dup"], ecr["bad_file"]))
    print("[B3] 独立复算可实现插点 %d ｜ 表内 %d（须相等）｜ 触发＝(场景,seq)，弹卡/淡出/跳过机制未改"
          % (ecr["expected"], ecr["keys"]))
    print("[B3] ★ 插点 seq ∉ 该场 `lines[].sq` 的条数 %d（须为 0；防 seq 越界永不弹）%s"
          % (ecr["bad_seq"], ("  样例 " + "、".join(ecr["bad_seq_ex"])) if ecr["bad_seq_ex"] else ""))

    ok = ((not bg_mismatch) and (not y0_viol) and (not ec_bg) and (not ec_bgarr)
          and (not diffs) and (not name_diffs) and ec_ok)
    print("-" * 72)
    print(">>> %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
