# -*- coding: utf-8 -*-
"""
W11e · 人物立绘（chr）六源统一 —— 「内容面积」选源 + 宽高比门控拆分
===================================================================
规格：资源组\\美术统一_规格.md（§3.2 / §3.3 于 2026-09-19 修订版）
输入：资源组\\krkr素材库\\{ot,ota,otp,otr,otv,np}\\chr\\   （3741 个 png，只读）
输出：资源组\\美术统一\\{立绘\\*, 清单_立绘.tsv, 待复核_立绘.tsv, 立绘_选源变更表.tsv,
                        统一说明_立绘.md, _stats_chr.json, _pick_chr.tsv, _npmerge_chr.tsv}

与 W11a（unify_chr.py）的差异（本次修订的**全部**改动点）
--------------------------------------------------------
1. **选源度量**：由「画布 w*h 最大」改为 **内容 bbox 面积（bw*bh）最大**；
   并新增 **np 优先**——通过门控的候选中若有 np，取 np 中内容面积最大者。
   （W11a 恒选 otv 的透明加边版，实际画面反而更小，见规格 §3.2 修订说明。）
2. **宽高比门控**：由 2% 改为 **5%**（内容 bbox 宽高比相对差）；
   超阈值判为**不同素材**，拆成 `<名>.png` 与 `<名>_alt<源>.png` 两个独立产物并记入待复核。
3. **清单新增 4 列**：`画布(w,h)` / `内容bbox(w,h)` / `内容面积` / `bbox偏移(x0,y0)`
   （追加在原有 10 列之后，保证按前 10 列定位的读取方不被打断）。
4. **分类判据**改用**内容 bbox 尺寸 / 内容宽高比**（规格 §3.3 修订版口径）。
5. 新增 `立绘_选源变更表.tsv`（旧选源 → 新选源逐组对照）。

复用：分组、归一化键、np 内容归并（含阈值与歧义判定）**原样复用 W11a 的实现**
（`unify_chr.py` 的 `inventory/pixel_meta/normalize/sim/aspect/mad_head` 与 np 归并段），
以保证本模块的差异**只来自规格修订点**，不引入新的分组口径变化。

只复制、不改像素（shutil.copyfile，无缩放 / 无重编码）。
"""
import os, re, sys, json, shutil, hashlib, collections, csv, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unify_chr as U          # noqa: E402  复用 W11a 的原语与阈值

BASE, LIB, OUTD, IMGD = U.BASE, U.LIB, U.OUTD, U.IMGD
SRCS, PRIO = U.SRCS, U.PRIO
MAD_TH, IOU_TH, ASP_FILTER = U.MAD_TH, U.IOU_TH, U.ASP_FILTER
AMBIG_D, CLUST_TH, HEAD_AMBIG = U.AMBIG_D, U.CLUST_TH, U.HEAD_AMBIG

GATE = 0.05                     # §3.3 修订：内容宽高比相对差门控阈值 5%
log = U.log


# ------------------------------------------------------------------ 工具
def atomic_write(path, text):
    """先写临时文件再原子替换，避免并发读取方读到半截。"""
    tmp = path + ".tmp_w11e"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def cmeta(r):
    """内容 bbox 元数据 -> (bw, bh, area, x0, y0)"""
    b = r["bbox"]
    bw, bh = b[2] - b[0], b[3] - b[1]
    return bw, bh, bw * bh, b[0], b[1]


def caspect(r):
    bw, bh, _, _, _ = cmeta(r)
    return bw / max(1, bh)


def rel(a, b):
    return abs(a - b) / max(a, b)


def pick_by_rule(cands):
    """§3.2 修订版：np 优先 → 内容面积最大 → 内容 bw 最大 → 源优先级。"""
    nps = [r for r in cands if r["src"] == "np"]
    pool = nps if nps else cands
    return max(pool, key=lambda r: (cmeta(r)[2], cmeta(r)[0], -PRIO[r["src"]]))


def clusters_by_aspect(cands):
    """按内容宽高比做单链聚类（相对差 <= GATE 相连）。"""
    n = len(cands)
    par = list(range(n))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if rel(caspect(cands[i]), caspect(cands[j])) <= GATE:
                ri, rj = find(i), find(j)
                if ri != rj:
                    par[max(ri, rj)] = min(ri, rj)
    cl = collections.defaultdict(list)
    for i, r in enumerate(cands):
        cl[find(i)].append(r)
    return [cl[k] for k in sorted(cl)]


# ------------------------------------------------------------------ 主流程
def main():
    t0 = time.time()
    os.makedirs(IMGD, exist_ok=True)

    # ---- 扫描 + 像素元数据（内容 bbox） ----
    rows = U.inventory()
    log("inventory:", len(rows), collections.Counter(r["src"] for r in rows))
    U.pixel_meta(rows)
    for r in rows:
        r["key"] = U.normalize(r["src"], r["name"])
    by_path = {r["path"]: r for r in rows}

    # ---- 分组（与 W11a 一致：4 元组键） ----
    groups = collections.OrderedDict()
    for r in rows:
        groups.setdefault(r["key"][:4], []).append(r)
    luc_keys = [k for k in groups if k[0] == "luc"]
    np_keys = [k for k in groups if k[0] == "np"]
    log("groups raw: luc=%d np=%d" % (len(luc_keys), len(np_keys)))

    # ================= np 内容归并（原样复用 W11a 实现） =================
    luc_fam = collections.defaultdict(list)
    for k in luc_keys:
        luc_fam[k[1]].append(k)

    def candidates_for(npkey):
        fam = npkey[1].split("_")[0]
        return luc_fam.get(fam, [])

    np_rows = [r for k in np_keys for r in groups[k]]
    by_px = collections.OrderedDict()
    for r in np_rows:
        by_px.setdefault((r["pxhash"], r["w"], r["h"]), []).append(r)
    log("np unique pixel contents:", len(by_px), "of", len(np_rows))

    parent = {r["name"]: r["name"] for r in np_rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    buckets = collections.defaultdict(list)
    for r in np_rows:
        buckets[(r["key"][1], r["key"][3])].append(r)
    for bkey, mem in buckets.items():
        for i in range(len(mem)):
            for j in range(i + 1, len(mem)):
                r2 = U.sim(mem[i], mem[j])
                if r2 and r2[0] <= CLUST_TH:
                    union(mem[i]["name"], mem[j]["name"])
    clusters = collections.defaultdict(list)
    for r in np_rows:
        clusters[find(r["name"])].append(r)
    log("np near-identical clusters:", len(clusters),
        "(singletons=%d)" % sum(1 for v in clusters.values() if len(v) == 1))

    assign = {}
    np_reject = {}
    for cid, mem in clusters.items():
        per_key = {}
        for r in mem:
            asp = U.aspect(r)
            for lk in candidates_for(r["key"]):
                for cand in groups[lk]:
                    if abs(asp / U.aspect(cand) - 1) > ASP_FILTER:
                        continue
                    r2 = U.sim(r, cand)
                    if not r2 or r2[0] > 60:
                        continue
                    cur = per_key.get(lk)
                    if cur is None or r2[0] < cur[0] - 1e-9:
                        per_key[lk] = (r2[0], r2[1], cand, r)
        if not per_key:
            continue
        by_content = {}
        for lk0, (m0, i0, c0, r0) in per_key.items():
            ck = (c0["pxhash"], c0["w"], c0["h"])
            cur = by_content.get(ck)
            if cur is None or m0 < cur[1][0] - 1e-9:
                by_content[ck] = (lk0, (m0, i0, c0, r0))
        ranked = sorted(by_content.values(),
                        key=lambda kv: (kv[1][0], -kv[1][1], PRIO[kv[1][2]["src"]], str(kv[0])))
        lk, (mad, iou, cand, rep) = ranked[0]
        margin = (ranked[1][1][0] - mad) if len(ranked) > 1 else 999.0
        base_best = (lk[1], lk[2])
        pose_unique = all((kv[0][1], kv[0][2]) == base_best for kv in ranked[:3])
        head_margin = None
        same_base = [(kv[0], kv[1]) for kv in ranked if (kv[0][1], kv[0][2]) == base_best]
        if len(same_base) >= 2:
            hm = []
            for lk1, (m1, i1, c1, r1) in same_base:
                v = U.mad_head(rep, c1)
                if v is not None:
                    hm.append((v, lk1, c1))
            hm.sort(key=lambda x: x[0])
            if len(hm) >= 2:
                head_margin = hm[1][0] - hm[0][0]
        amb = (margin < AMBIG_D) or (head_margin is not None and head_margin < HEAD_AMBIG)
        if mad <= MAD_TH and iou >= IOU_TH and pose_unique:
            for r in mem:
                assign[r["name"]] = (lk, mad, iou, amb, margin, pose_unique, head_margin)
        else:
            why = "np_pose_ambiguous" if not pose_unique else "np_low_confidence"
            for r in mem:
                np_reject[r["name"]] = (why, lk, mad, iou, margin, head_margin,
                                        [(kv[0], round(kv[1][0], 2), kv[1][2]["name"])
                                         for kv in ranked[:3]])
    log("np contents paired:", len(assign), "/", len(np_rows), "rejected:", len(np_reject))

    np_merge_detail = dict(assign)
    groups = collections.OrderedDict()
    for r in rows:
        k = np_merge_detail.get(r["name"], (r["key"][:4],))[0] if r["src"] == "np" \
            else r["key"][:4]
        groups.setdefault(k, []).append(r)
    log("groups after np merge:", len(groups))
    # ================= np 归并段结束 =================

    # ---- 统一名（= 组内源优先级最高候选的 stem，与 W11a 一致） ----
    for k, cands in groups.items():
        cands.sort(key=lambda r: (PRIO[r["src"]], r["name"]))
        uname = cands[0]["key"][4] + ".png"
        for r in cands:
            r["_uname"] = uname

    name_owner = {}
    for k, cands in groups.items():
        nm = cands[0]["_uname"]
        if nm in name_owner:
            log("!! NAME COLLISION", nm, k, name_owner[nm])
        name_owner[nm] = k

    # ---- 旧选源（W11a 规则）复算：画布 w*h 最大 -> w 最大 -> 源优先级 ----
    # 说明：W11a 的 _pick_chr.tsv 已被本模块输出覆盖，且未被 git 追踪，无法直接读取；
    # 旧规则完全确定，故在**同一分组**上按 W11a 的排序键复算，作为变更表基准（可复跑、可审计）。
    old_pick = {}
    for k, cands in groups.items():
        o = sorted(cands, key=lambda r: (-(r["w"] * r["h"]), -r["w"], PRIO[r["src"]]))[0]
        old_pick[cands[0]["_uname"]] = (o["src"], o["name"], o["path"])
    atomic_write(os.path.join(OUTD, "_pick_chr_w11a_backup.tsv"),
                 "\n".join(["统一名\t选中源\t选中原名\t选中路径\t# W11a 旧规则(画布 w*h 最大)复算快照"] +
                           ["\t".join([u, v[0], v[1], v[2]]) for u, v in sorted(old_pick.items())]) + "\n")
    log("old pick (W11a rule recomputed) rows:", len(old_pick))

    # ---- 分类 + 选优 + 门控拆分 ----
    records = []          # 每行 = 一个产物
    split_groups = []     # 门控拆分明细
    for k, cands in groups.items():
        uname = cands[0]["_uname"]
        stem = uname[:-4]
        cl = clusters_by_aspect(cands)

        def classify(sub):
            cdims = set((cmeta(r)[0], cmeta(r)[1]) for r in sub)
            px = set(r["pxhash"] for r in sub)
            md5s = set(r["md5"] for r in sub)
            if len(sub) == 1:
                return "single"
            if len(cdims) == 1:
                return "same_res_same" if len(px) == 1 else "same_res_diff"
            asp = [caspect(r) for r in sub]
            ok = max(rel(asp[0], a) for a in asp) <= GATE
            return "diff_res_same_drawing" if ok else "diff_res_diff_drawing"

        if len(cl) == 1:
            sel = pick_by_rule(cands)
            cls = classify(cands)
            records.append(dict(uname=uname, cands=cands, cls=cls, sel=sel,
                                area=cmeta(sel)[2], split=False, alt_of=None))
            continue

        # ---- 门控：>5% → 拆分 ----
        overall = pick_by_rule(cands)
        main_cl = next(c for c in cl if any(x is overall for x in c))
        alts = [c for c in cl if c is not main_cl]
        sel_main = pick_by_rule(main_cl)
        records.append(dict(uname=uname, cands=main_cl, cls="diff_res_diff_drawing",
                            sel=sel_main, area=cmeta(sel_main)[2], split=True, alt_of=None))
        used = set()
        for acl in alts:
            sel_a = pick_by_rule(acl)
            aname = "%s_alt%s.png" % (stem, sel_a["src"])
            if aname in used:
                aname = "%s_alt%s-2.png" % (stem, sel_a["src"])
            used.add(aname)
            records.append(dict(uname=aname, cands=acl, cls="diff_res_diff_drawing",
                                sel=sel_a, area=cmeta(sel_a)[2], split=True, alt_of=uname))
        split_groups.append(dict(uname=uname, stem=stem,
                                 clusters=[[r["name"] for r in c] for c in cl],
                                 main=sel_main, alts=[r for r in records if r["alt_of"] == uname],
                                 aspects=dict((r["name"], round(caspect(r), 4)) for r in cands)))

    log("records (products):", len(records), " split groups:", len(split_groups))

    # ---- 重名断言 ----
    dup = [n for n, c in collections.Counter(r["uname"] for r in records).items() if c > 1]
    assert not dup, ("duplicate product names", dup[:10])
    coll = [r["uname"] for r in records if r["uname"] in name_owner
            and r["alt_of"] is not None]
    assert not coll, ("alt name collides with existing uname", coll[:10])

    # ---- 头像 / 未识别（沿用 W11a 口径） ----
    AVATAR_FAM = {"f_mis"}
    NONCHAR_FAM = {"cin", "cit", "cin_red", "cin_blk"}

    def category(rec):
        fam = rec["cands"][0]["key"][1]
        if fam in AVATAR_FAM:
            return "头像"
        if fam in NONCHAR_FAM:
            return "未识别"
        s = rec["sel"]
        if rec["cls"] == "single" and max(s["w"], s["h"]) <= 260 \
           and 0.9 <= s["w"] / s["h"] <= 1.1:
            return "未识别"
        return "立绘"

    # ---- 复制产物（原子：先写临时目录再整体替换） ----
    new_names = set(r["uname"] for r in records)
    stale = 0
    for fn in os.listdir(IMGD):
        p = os.path.join(IMGD, fn)
        if os.path.isfile(p) and fn not in new_names:
            os.remove(p)
            stale += 1
    log("stale products removed:", stale)
    for rec in records:
        shutil.copyfile(rec["sel"]["path"], os.path.join(IMGD, rec["uname"]))
    log("copied:", len(records))

    # ---- 理由 ----
    def reason(rec):
        c = rec["cls"]
        s = rec["sel"]
        bw, bh, ar, x0, y0 = cmeta(s)
        tag = "np 优先" if any(r["src"] == "np" for r in rec["cands"]) else "内容面积"
        if c == "single":
            return "组内唯一候选"
        if c == "same_res_same":
            return "同内容尺寸且像素逐字节相同，按源优先级取 %s" % s["src"]
        if c == "same_res_diff":
            return "同内容尺寸但像素不同，按源优先级取 %s（内容冲突，见待复核）" % s["src"]
        if c == "diff_res_same_drawing":
            return "内容尺寸不同、宽高比差<=5%%（同取景），按%s取 %s（内容 %dx%d=%d）" % (
                tag, s["src"], bw, bh, ar)
        if rec["alt_of"]:
            return "门控拆分：宽高比差>5%%，与 %s 非同一取景，独立产物（内容 %dx%d=%d）" % (
                rec["alt_of"], bw, bh, ar)
        return "门控拆分：宽高比差>5%%，取主取景 %s（内容 %dx%d=%d）" % (s["src"], bw, bh, ar)

    # ---- 清单（原 10 列 + 新增 4 列） ----
    hdr = ["统一名", "类别", "尺寸(w,h)", "模式", "字节", "选中源", "选中原名",
           "组内候选数", "分类", "理由",
           "画布(w,h)", "内容bbox(w,h)", "内容面积", "bbox偏移(x0,y0)"]
    lines = ["\t".join(hdr)]
    for rec in sorted(records, key=lambda r: r["uname"]):
        s = rec["sel"]
        bw, bh, ar, x0, y0 = cmeta(s)
        lines.append("\t".join([
            rec["uname"], category(rec), "%dx%d" % (s["w"], s["h"]), s["mode"],
            str(s["bytes"]), s["src"], s["name"], str(len(rec["cands"])),
            rec["cls"], reason(rec),
            "%dx%d" % (s["w"], s["h"]), "%dx%d" % (bw, bh), str(ar), "%d,%d" % (x0, y0)]))
    atomic_write(os.path.join(OUTD, "清单_立绘.tsv"), "\n".join(lines) + "\n")

    # ---- 待复核 ----
    rev = ["统一名\t分类\t候选清单\t选中项\t选中理由\t疑点"]

    def candstr(cands, sel=None):
        return " | ".join(
            "%s:%s:%dx%d:%s%s" % (r["src"], r["name"], r["w"], r["h"], r["md5"][:8],
                                  "（像素同）" if sel is not None and r["pxhash"] == sel["pxhash"] and r is not sel else "")
            for r in sorted(cands, key=lambda r: PRIO[r["src"]]))

    n_srd = n_drd = n_unid = n_amb = 0
    split_of = {r["uname"]: r["alt_of"] for r in records if r["alt_of"]}
    for rec in sorted(records, key=lambda r: r["uname"]):
        sus = []
        if rec["cls"] == "same_res_diff":
            sus.append("content_conflict：同内容尺寸像素不同")
            n_srd += 1
        if rec["cls"] == "diff_res_diff_drawing":
            if rec["alt_of"]:
                sus.append("framing_split_alt：宽高比差>5%%，已拆为独立产物（对应主产物 %s）"
                           % rec["alt_of"])
            else:
                sg = next((g for g in split_groups if g["uname"] == rec["uname"]), None)
                if sg:
                    sus.append("framing_split：宽高比差>5%%，判为不同取景，已拆出 %s"
                               % "、".join(a["uname"] for a in sg["alts"]))
                else:
                    sus.append("aspect_mismatch：宽高比差>5%%，可能非同一张画")
            n_drd += 1
        if category(rec) == "未识别":
            sus.append("非角色立绘（疑 cut-in / 演出层），未识别")
            n_unid += 1
        np_amb = [d for d in (np_merge_detail.get(r["name"]) if r["src"] == "np" else None
                              for r in rec["cands"]) if d and d[3]]
        if np_amb:
            sus.append("np_pair_ambiguous：np 内容配对次优 MAD 差<%.1f，表情/姿势归属存疑" % AMBIG_D)
            n_amb += 1
        if not sus:
            continue
        rev.append("\t".join([rec["uname"], rec["cls"], candstr(rec["cands"], rec["sel"]),
                              "%s:%s" % (rec["sel"]["src"], rec["sel"]["name"]),
                              reason(rec), "；".join(sus)]))
    # np 配对失败（独立保留）
    n_npfail = 0
    for k, cands in groups.items():
        if k[0] != "np":
            continue
        r = cands[0]
        fam = k[1].split("_")[0]
        rev.append("\t".join([
            r["_uname"], "np_unpaired",
            "%s:%s:%dx%d:%s" % (r["src"], r["name"], r["w"], r["h"], r["md5"][:8]),
            "%s:%s" % (r["src"], r["name"]), "独立保留（np 原生 1280x720）",
            "np_unpaired：内容比对未在 `%s` 族中找到 MAD<=%.0f 且 IoU>=%.2f 的对应项，"
            "已作独立素材保留（未强行配对）" % (fam, MAD_TH, IOU_TH)]))
        n_npfail += 1
    # np 有候选但被判不配对（姿势归属不唯一 / 置信不足）
    n_nprej = 0
    for nm, (why, lk, mad, iou, margin, hmg, top3) in sorted(np_reject.items()):
        r = next(x for x in rows if x["name"] == nm)
        rev.append("\t".join([
            r["key"][4], why,
            "%s:%s:%dx%d:%s" % (r["src"], r["name"], r["w"], r["h"], r["md5"][:8]),
            "%s:%s" % (r["src"], r["name"]), "独立保留（np 原生 1280x720）",
            "%s：全图 MAD=%.2f IoU=%.3f（阈值 MAD<=%.0f, IoU>=%.2f），最优 Lucifen 组键 %s；"
            "前三候选 %s —— 「同画」可判但**姿势/表情归属不唯一或置信不足**，"
            "按 §四.4「不得强行配对」保留为独立素材，待主代理/vision 裁决"
            % (why, mad, iou, MAD_TH, IOU_TH, lk, top3)]))
        n_nprej += 1
    atomic_write(os.path.join(OUTD, "待复核_立绘.tsv"), "\n".join(rev) + "\n")

    # ---- 选源变更表 ----
    new_pick = dict((r["uname"], (r["sel"]["src"], r["sel"]["name"], r["sel"]["path"],
                                  r["cls"], r["alt_of"])) for r in records)
    chg = []
    for rec in sorted(records, key=lambda r: r["uname"]):
        u = rec["uname"]
        if u in old_pick:
            osrc, oname, opath = old_pick[u]
            orow = by_path.get(opath)
            if orow is not None and osrc == rec["sel"]["src"] and oname == rec["sel"]["name"]:
                continue                     # 未变化
            ocw, och = (orow["w"], orow["h"]) if orow else (0, 0)
            oarea = cmeta(orow)[2] if orow else 0
        else:
            osrc, oname, ocw, och, oarea = "-", "-", "-", "-", "-"    # 新增（拆分产物）
        bw, bh, ar, x0, y0 = cmeta(rec["sel"])
        gain = ("%.1f" % ((ar - oarea) / oarea * 100.0)) if oarea != "-" and oarea else "-"
        if rec["alt_of"]:
            ctype = "门控拆分_alt"
        elif u not in old_pick:
            ctype = "新增"
        elif osrc != rec["sel"]["src"] and oarea != "-" and ar > oarea:
            ctype = "内容面积改选"
        else:
            ctype = "改选"
        chg.append((u, osrc, rec["sel"]["src"],
                    ("%dx%d" % (ocw, och)) if ocw != "-" else "-",
                    "%dx%d" % (rec["sel"]["w"], rec["sel"]["h"]),
                    str(oarea), str(ar), gain, rec["cls"], ctype))
    chg_hdr = ["统一名", "旧选源", "新选源", "旧画布", "新画布", "旧内容面积", "新内容面积",
               "面积增益%", "分类", "变更类型"]
    atomic_write(os.path.join(OUTD, "立绘_选源变更表.tsv"),
                 "\n".join(["\t".join(chg_hdr)] + ["\t".join(c) for c in chg]) + "\n")

    # ---- 中间表 ----
    atomic_write(os.path.join(OUTD, "_pick_chr.tsv"),
                 "\n".join(["统一名\t选中源\t选中原名\t选中路径"] +
                           ["\t".join([r["uname"], r["sel"]["src"], r["sel"]["name"],
                                       r["sel"]["path"]])
                            for r in sorted(records, key=lambda r: r["uname"])]) + "\n")

    npu = {}
    for k, cands in groups.items():
        for r in cands:
            npu[r["name"]] = cands[0]["_uname"]
    atomic_write(os.path.join(OUTD, "_npmerge_chr.tsv"),
                 "\n".join(["np原名\tnp尺寸\t配对目标组(统一名)\t全图MAD\tIoU\t全图次优差值\t头部次优差值\t歧义"] +
                           ["%s\t%s\t%s\t%.2f\t%.4f\t%.2f\t%s\t%s" % (
                               nm, "1280x720", npu.get(nm, ""), mad, iou, margin,
                               ("%.2f" % hmg) if hmg is not None else "-", "Y" if amb else "")
                            for nm, (lk, mad, iou, amb, margin, pu, hmg)
                            in sorted(np_merge_detail.items())]) + "\n")

    # ---- 统计 ----
    cat = collections.Counter(category(r) for r in records)
    cls = collections.Counter(r["cls"] for r in records)
    per_src = collections.Counter(r["src"] for r in rows)
    sel_src = collections.Counter(r["sel"]["src"] for r in records)
    old_sel_src = collections.Counter(v[0] for v in old_pick.values())
    tot_cand = sum(len(r["cands"]) for r in records)
    bytes_all = sum(r["bytes"] for r in rows)
    bytes_sel = sum(r["sel"]["bytes"] for r in records)
    np_win_groups = sum(1 for r in records if r["sel"]["src"] == "np")
    stat = dict(
        files=len(rows), per_source=dict(per_src), groups=len(groups),
        products=len(records), alt_products=len(records) - len(groups),
        sum_candidates=tot_cand, category=dict(cat), classification=dict(cls),
        bytes_all=bytes_all, bytes_selected=bytes_sel,
        selected_by_source=dict(sel_src), old_selected_by_source=dict(old_sel_src),
        np_win_products=np_win_groups,
        np_files_total=len([r for r in rows if r["src"] == "np"]),
        np_files_in_np_groups=len(np_rows), np_merged_files=len(np_merge_detail),
        np_merged_target_groups=len(set(d[0] for d in np_merge_detail.values())),
        np_independent_assets=len([1 for r in records if r["cands"][0]["key"][0] == "np"]),
        split_groups=len(split_groups),
        review_rows=len(rev) - 1, rev_same_res_diff=n_srd, rev_diff_res_diff_drawing=n_drd,
        rev_unidentified=n_unid, rev_np_ambig=n_amb, rev_np_unpaired=n_npfail,
        rev_np_rejected=n_nprej,
        changed_rows=len(chg), elapsed_sec=round(time.time() - t0, 1))
    atomic_write(os.path.join(OUTD, "_stats_chr.json"),
                 json.dumps(stat, ensure_ascii=False, indent=1))
    log(json.dumps(stat, ensure_ascii=False, indent=1))

    # ---- 拆分明细（审计） ----
    sl = ["统一名\t内容宽高比\t簇\t主产物\t拆出产物"]
    for g in split_groups:
        sl.append("%s\t%s\t%s\t%s\t%s" % (
            g["uname"],
            " ; ".join("%s=%.4f" % (k, v) for k, v in g["aspects"].items()),
            " || ".join(",".join(c) for c in g["clusters"]),
            g["main"]["name"],
            "、".join(a["uname"] for a in g["alts"])))
    atomic_write(os.path.join(OUTD, "_w11e_拆分明细.tsv"), "\n".join(sl) + "\n")
    log("split groups detail written:", len(split_groups))


if __name__ == "__main__":
    main()