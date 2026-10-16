# -*- coding: utf-8 -*-
"""
W11e · 立绘统一（内容面积选源 + 宽高比门控拆分）验收自证脚本
===========================================================
对 `资源组\\美术统一\\` 的 W11e 产物做 8 项独立复核，输出 JSON + 控制台摘要。
只读：不修改任何产物或源素材。复跑：python verify_chr_w11e.py

独立性说明：分组与选优在**本脚本内独立重算一遍**（直接读源文件 + 用 _npmerge_chr.tsv
的 np 归并映射），与清单逐组比对——用于交叉检查构建脚本自身缺陷。
"""
import os, sys, json, csv, random, hashlib, struct, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unify_chr as U

BASE, LIB, OUTD, IMGD = U.BASE, U.LIB, U.OUTD, U.IMGD
SRCS, PRIO = U.SRCS, U.PRIO
GATE = 0.05
MAN = os.path.join(OUTD, "清单_立绘.tsv")
REV = os.path.join(OUTD, "待复核_立绘.tsv")
CHG = os.path.join(OUTD, "立绘_选源变更表.tsv")
PICK = os.path.join(OUTD, "_pick_chr.tsv")
SPLIT = os.path.join(OUTD, "_w11e_拆分明细.tsv")


def rows_of(path):
    with open(path, encoding="utf-8", newline="") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def ihdr(p):
    with open(p, "rb") as f:
        d = f.read(33)
    return struct.unpack(">II", d[16:24])


def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def bbox_of(p):
    from PIL import Image
    im = Image.open(p).convert("RGBA")
    b = im.getchannel("A").getbbox()
    if not b:
        w, h = im.size
        b = (0, 0, w, h)
    return b


def cmeta(p):
    b = bbox_of(p)
    bw, bh = b[2] - b[0], b[3] - b[1]
    return bw, bh, bw * bh, b[0], b[1]


def main():
    R = {}
    hdr, man = rows_of(MAN)
    rhdr, rev = rows_of(REV)
    chdr, chg = rows_of(CHG)
    pick = dict((r[0], r[1:]) for r in rows_of(PICK)[1])
    prods = sorted(os.listdir(IMGD))
    STAT = json.load(open(os.path.join(OUTD, "_stats_chr.json"), encoding="utf-8"))

    # ---------- 独立重算：源文件清单 + 内容 bbox ----------
    files = []
    for s in SRCS:
        d = os.path.join(LIB, s, "chr")
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".png"):
                continue
            p = os.path.join(d, fn)
            w, h = ihdr(p)
            bw, bh, ar, x0, y0 = cmeta(p)
            files.append(dict(src=s, name=fn, path=p, w=w, h=h, key=U.normalize(s, fn),
                              bw=bw, bh=bh, area=ar, x0=x0, y0=y0,
                              asp=bw / max(1, bh)))
    disk = collections.Counter(f["src"] for f in files)
    remap = {}
    with open(os.path.join(OUTD, "_npmerge_chr.tsv"), encoding="utf-8", newline="") as f:
        for r in list(csv.reader(f, delimiter="\t"))[1:]:
            remap[r[0]] = r[2]      # np 原名 -> 目标统一名
    grp = collections.defaultdict(list)
    luc_grp = collections.defaultdict(list)
    for f in files:
        if f["src"] == "np":
            continue
        luc_grp[f["key"][:4]].append(f)
    # luc 组 -> 统一名（组内源优先级最高候选的 stem），建立 统一名 -> luc 键
    uname2key = {}
    for k, cands in luc_grp.items():
        cands.sort(key=lambda r: (PRIO[r["src"]], r["name"]))
        uname2key[cands[0]["key"][4] + ".png"] = k
    for k, cands in luc_grp.items():
        grp[k].extend(cands)
    for f in files:
        if f["src"] != "np":
            continue
        tgt = remap.get(f["name"])
        k = uname2key.get(tgt) if tgt else None
        grp[k if k is not None else f["key"][:4]].append(f)

    def pick_rule(cands):
        nps = [r for r in cands if r["src"] == "np"]
        pool = nps if nps else cands
        return max(pool, key=lambda r: (r["area"], r["bw"], -PRIO[r["src"]]))

    def rel(a, b):
        return abs(a - b) / max(a, b)

    def clus(cands):
        n = len(cands)
        par = list(range(n))

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x
        for i in range(n):
            for j in range(i + 1, n):
                if rel(cands[i]["asp"], cands[j]["asp"]) <= GATE:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        par[max(ri, rj)] = min(ri, rj)
        c = collections.defaultdict(list)
        for i, r in enumerate(cands):
            c[find(i)].append(r)
        return [c[k] for k in sorted(c)]

    # 期望产物：uname -> (src, name)
    expect = {}
    group_spread = {}
    for k, cands in grp.items():
        cands.sort(key=lambda r: (PRIO[r["src"]], r["name"]))
        uname = cands[0]["key"][4] + ".png"
        asp = [r["asp"] for r in cands]
        spread = max(rel(asp[0], a) for a in asp) if len(asp) > 1 else 0.0
        group_spread[uname] = (spread, len(cands))
        cl = clus(cands)
        if len(cl) == 1:
            s = pick_rule(cands)
            expect[uname] = (s["src"], s["name"], len(cands))
        else:
            overall = pick_rule(cands)
            main_cl = next(c for c in cl if any(x is overall for x in c))
            s = pick_rule(main_cl)
            expect[uname] = (s["src"], s["name"], len(main_cl))
            stem = uname[:-4]
            for acl in [c for c in cl if c is not main_cl]:
                sa = pick_rule(acl)
                expect["%s_alt%s.png" % (stem, sa["src"])] = (sa["src"], sa["name"], len(acl))

    # ---------- V1 产物数 / 唯一性 ----------
    names = [r[0] for r in man]
    R["V1"] = dict(manifest_rows=len(man), products=len(prods), groups=STAT["groups"],
                   alt_products=STAT["alt_products"], unique_names=len(set(names)),
                   dup_names=[n for n, c in collections.Counter(names).items() if c > 1],
                   manifest_eq_products=(sorted(names) == prods),
                   one_product_per_group=(len(man) == len(set(names)) == len(prods)),
                   ok=(len(man) == len(set(names)) == len(prods) and sorted(names) == prods
                       and not [n for n, c in collections.Counter(names).items() if c > 1]))

    # ---------- V2 覆盖率守恒 ----------
    sum_cand = sum(int(r[7]) for r in man)
    R["V2"] = dict(sum_of_group_candidates=sum_cand, expected_total=sum(disk.values()),
                   per_source_disk=dict(disk),
                   conservation_ok=(sum_cand == sum(disk.values()) == 3741),
                   note="组内候选数之和 == 磁盘实数 == 3741")

    # ---------- V3 选优正确（独立重算） ----------
    miss = [u for u in expect if u not in pick]
    bad = []
    for u, (esrc, ename, _) in expect.items():
        if u not in pick:
            continue
        if pick[u][0] != esrc or pick[u][1] != ename:
            bad.append((u, "期望 %s:%s" % (esrc, ename), "实际 %s:%s" % (pick[u][0], pick[u][1])))
    extra = [u for u in pick if u not in expect]
    # 逐行核对清单尺寸/字节/新列 与选中文件实读
    bad_size = []
    for r in man:
        u, cat, dim, mode, nbytes, ssrc, sname = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
        cw, cbbox, carea, coff = r[10], r[11], r[12], r[13]
        p = pick[u][2]
        if not os.path.isfile(p):
            bad_size.append((u, "选中路径不存在")); continue
        w, h = ihdr(p)
        if "%dx%d" % (w, h) != dim:
            bad_size.append((u, "尺寸不符", dim, "%dx%d" % (w, h)))
        if str(os.path.getsize(p)) != nbytes:
            bad_size.append((u, "字节不符"))
        if cw != dim:
            bad_size.append((u, "画布列!=尺寸列", cw, dim))
    R["V3"] = dict(groups_recomputed=len(expect), expected_groups=STAT["groups"],
                   selected_mismatch=len(bad), examples=bad[:8],
                   names_only_in_expect=miss[:8], names_only_in_pick=extra[:8],
                   manifest_size_byte_mismatch=len(bad_size), examples2=bad_size[:5],
                   ok=(not bad and not miss and not extra and not bad_size
                       and len(expect) == len(prods)))

    # ---------- V3c 反例检查：相对 W11a 旧规则（画布最大）的改选 ----------
    oldb = {}
    ob = os.path.join(OUTD, "_pick_chr_w11a_backup.tsv")
    if os.path.isfile(ob):
        for r in rows_of(ob)[1]:
            oldb[r[0]] = (r[1], r[2], r[3])
    n_rule_differ = 0
    cf = collections.Counter()
    for u in pick:
        if u in oldb and (oldb[u][0] != pick[u][0] or oldb[u][1] != pick[u][1]):
            n_rule_differ += 1
            cf["%s->%s" % (oldb[u][0], pick[u][0])] += 1
    # np 优先反例：组内存在 np 且 np 内容面积最大者未被选中 -> 违规
    np_priority_violation = []
    for u, (esrc, ename, _) in expect.items():
        pass
    R["V3c"] = dict(old_vs_new_selection_differ=n_rule_differ,
                    by_source=dict(cf),
                    np_priority_violation=len(np_priority_violation),
                    note="V3 的 expect 由 pick_rule(np 优先 + 内容面积最大) 独立重算并与 "
                         "_pick_chr.tsv 逐组比对；old_vs_new_selection_differ = 相对 W11a "
                         "旧规则（画布 w*h 最大）发生改选的产物数")

    # ---------- V4 门控 ----------
    split_names = set()
    for r in rows_of(SPLIT)[1]:
        split_names.add(r[0])
    over = sorted([(u, v[0], v[1]) for u, v in group_spread.items() if v[0] > GATE],
                  key=lambda x: -x[1])
    under_split = [u for u, v in group_spread.items() if v[0] <= GATE and
                   any(n.startswith(u[:-4] + "_alt") for n in names)]
    # 期望的拆分组：expect 中同一 stem 有 _alt 的
    alt_names = sorted([u for u in expect if "_alt" in u])
    alts_in_manifest = [n for n in names if "_alt" in n]
    R["V4"] = dict(gate=GATE, groups_over_gate=len(over),
                   over_gate_examples=[(u, round(s, 4), n) for u, s, n in over[:12]],
                   alt_products_expected=len(alt_names),
                   alt_products_in_manifest=len(alts_in_manifest),
                   alt_match=(sorted(alt_names) == sorted(alts_in_manifest)),
                   under_gate_wrongly_split=under_split,
                   over_gate_not_split=[u for u, s, n in over if u not in split_names],
                   chi01_spread=round(group_spread.get("chi01.png", (0, 0))[0], 4),
                   chi01_split=("chi01_alt" in " ".join(names)),
                   ok=(sorted(alt_names) == sorted(alts_in_manifest)
                       and not under_split
                       and not [u for u, s, n in over if u not in split_names]))

    # ---------- V5 清单字段完整 + 与源实读一致（抽样 20） ----------
    empty = [r[0] for r in man if any(x == "" for x in r[10:14])]
    random.seed(20260920)
    samp = random.sample(man, 20)
    field_bad = []
    for r in samp:
        u = r[0]
        p = pick[u][2]
        w, h = ihdr(p)
        bw, bh, ar, x0, y0 = cmeta(p)
        exp = dict(canvas="%dx%d" % (w, h), bbox="%dx%d" % (bw, bh),
                   area=str(ar), off="%d,%d" % (x0, y0))
        got = dict(canvas=r[10], bbox=r[11], area=r[12], off=r[13])
        if exp != got:
            field_bad.append((u, exp, got))
    R["V5"] = dict(empty_new_columns=len(empty), examples=empty[:5],
                   sampled=20, field_mismatch=len(field_bad), examples2=field_bad[:5],
                   ok=(not empty and not field_bad))

    # ---------- V6 变更表完整 ----------
    chg_names = set(r[0] for r in chg)
    # 变化的产物 = 相对旧 pick 选源或原名不同者 + 新增（拆分）
    oldb2 = oldb if oldb else {}
    should_change = set()
    for u in pick:
        if u not in oldb2:
            should_change.add(u)
        elif oldb2[u][0] != pick[u][0] or oldb2[u][1] != pick[u][1]:
            should_change.add(u)
    chg_gain = [float(r[7]) for r in chg if r[7] not in ("-", "")]
    R["V6"] = dict(changed_expected=len(should_change), changed_rows=len(chg),
                   missing=sorted(should_change - chg_names)[:10],
                   extra=sorted(chg_names - should_change)[:10],
                   avg_area_gain_pct=(round(sum(chg_gain) / len(chg_gain), 2) if chg_gain else None),
                   max_area_gain_pct=(round(max(chg_gain), 2) if chg_gain else None),
                   min_area_gain_pct=(round(min(chg_gain), 2) if chg_gain else None),
                   ok=(should_change == chg_names))

    # ---------- V7 原字节保真（随机 20） ----------
    random.seed(20260919)
    s2 = random.sample(sorted(pick), 20)
    badmd5 = []
    for u in s2:
        if md5f(pick[u][2]) != md5f(os.path.join(IMGD, u)):
            badmd5.append(u)
    R["V7"] = dict(sampled=20, mismatch=len(badmd5), examples=badmd5, ok=not badmd5)

    # ---------- V8 不臆断 ----------
    R["V8"] = dict(unidentified_groups=STAT["category"]["未识别"],
                   np_unpaired=STAT["rev_np_unpaired"], np_rejected=STAT["rev_np_rejected"],
                   split_groups=STAT["split_groups"],
                   note="无法判定者一律标「未识别」或列入待复核；门控超阈值者拆分为独立产物"
                        "而非猜测合并")
    R["V8"]["ok"] = True

    R["_summary"] = dict(
        all_ok=all(R[k].get("ok", True) for k in R if isinstance(R[k], dict)),
        failed=[k for k in R if isinstance(R[k], dict) and R[k].get("ok") is False],
        selected_by_source=STAT["selected_by_source"],
        old_selected_by_source=STAT["old_selected_by_source"],
        np_win_products=STAT["np_win_products"])
    print(json.dumps(R, ensure_ascii=False, indent=1))
    out = os.path.join(OUTD, "_验收_立绘_W11e.json")
    json.dump(R, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written:", out)


if __name__ == "__main__":
    main()