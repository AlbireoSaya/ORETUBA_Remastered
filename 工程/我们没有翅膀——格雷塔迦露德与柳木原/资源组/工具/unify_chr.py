# -*- coding: utf-8 -*-
"""
W11a · 人物立绘（chr）六源统一
===============================
规格：资源组\美术统一_规格.md（v1.0）
输入：资源组\krkr素材库\{ot,ota,otp,otr,otv,np}\chr\   （3741 个 png，只读）
输出：资源组\美术统一\{立绘\*, 清单_立绘.tsv, 待复核_立绘.tsv, 统一说明_立绘.md}

设计要点
--------
1. 归一化键 = (scope, family, base:int, suffix)
   - 去来源前缀、去 `st_`，再按 §二 的形态 A/B/C 拆；np 用 `asu_a01l` 专用形态。
   - 解析失败的（`cin_red`）单独成组，键用整段 stem。
2. 统一名 = 组内「源优先级最高」的候选的归一化 stem（即原名去前缀去 st_），
   这样 §二.1 的示例 `ai_01a / asu01a / kur02e / mis03n` 逐字成立。
3. 选优：§3.2 字面实现（w*h 最大 → w 最大 → 源优先级 ot>otr>ota>otp>otv>np）。
4. 分类：§3.3，其中「同 md5」按规格用 md5；md5 不同但**像素逐字节相同**的
   追加判为 same_res_same（并在疑点里记 md5 差异），避免把 PNG 重编码差异误报为内容冲突。
5. np 归并：先按名归并（`lr201e/yuu02/yuu02m` 天然落进 luc 组），
   其余按内容比对（bbox 裁切 + 128x128 归一 + MAD / alpha-IoU），阈值实测标定。
6. 只复制、不改像素。
"""
import os, re, sys, json, shutil, hashlib, struct, collections, random, time

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
LIB  = os.path.join(BASE, "krkr素材库")
OUTD = os.path.join(BASE, "美术统一")
IMGD = os.path.join(OUTD, "立绘")
SRCS = ["ot", "ota", "otp", "otr", "otv", "np"]
PRIO = {s: i for i, s in enumerate(SRCS)}          # ot=0 最高
S = 128                                            # 相似度归一尺寸
MAD_TH = 35.0                                      # 内容配对 MAD 阈值（标定见说明）
IOU_TH = 0.93                                      # 内容配对 IoU 阈值
ASP_FILTER = 0.06                                  # bbox 宽高比预筛（相对差）
AMBIG_D = 2.0                                      # 次优「组键」MAD 差 < 此值 视为歧义
CLUST_TH = 3.0                                     # np 内部近同内容聚类阈值
HEAD_AMBIG = 1.0                                   # 头部区域 MAD 最优/次优差 < 此值 视为表情歧义
HEAD_BOX = (0, 0, S, int(S * 0.42))                # 归一化图上的头部区域

RX_A  = re.compile(r'^([a-z]+)_([a-z]+)(\d+)([a-z]*)$')   # cin_blk2 / f_mis01
RX_B  = re.compile(r'^([a-z]+)_(\d+)([a-z]*)$')           # ai_01a
RX_C  = re.compile(r'^([a-z]+?)(\d+)([a-z]*)$')           # asu01a
RX_NP = re.compile(r'^([a-z]+)_([a-z])(\d+)([a-z]*)$')    # asu_a01l


def log(*a):
    print(*a); sys.stdout.flush()


# ---------------------------------------------------------------- 归一化
def strip_prefix(src, fn):
    n = fn[:-4].lower()
    if n.startswith(src + "_"):
        n = n[len(src) + 1:]
    if n.startswith("st_"):
        n = n[3:]
    return n


def normalize(src, fn):
    """-> (scope, family, base, suffix, stem) ; scope 'luc'/'np'/None"""
    n = strip_prefix(src, fn)
    if src == "np":
        m = RX_NP.match(n)
        if m:
            return ("np", m.group(1) + "_" + m.group(2), int(m.group(3)), m.group(4), n)
    m = RX_B.match(n)
    if m:
        return ("luc", m.group(1), int(m.group(2)), m.group(3), n)
    m = RX_A.match(n)
    if m:
        return ("luc", m.group(1) + "_" + m.group(2), int(m.group(3)), m.group(4), n)
    m = RX_C.match(n)
    if m:
        return ("luc", m.group(1), int(m.group(2)), m.group(3), n)
    return (None, n, None, None, n)     # 解析失败：整段作 family，独立成组


# ---------------------------------------------------------------- 图像
def png_ihdr(p):
    with open(p, "rb") as f:
        d = f.read(33)
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not png: " + p)
    w, h = struct.unpack(">II", d[16:24])
    return w, h, {0: "L", 2: "RGB", 3: "P", 4: "LA", 6: "RGBA"}.get(d[25], "?")


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def inventory():
    rows = []
    for s in SRCS:
        d = os.path.join(LIB, s, "chr")
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".png"):
                continue
            p = os.path.join(d, fn)
            w, h, mode = png_ihdr(p)
            rows.append(dict(src=s, name=fn, path=p, w=w, h=h, mode=mode,
                             bytes=os.path.getsize(p), md5=md5_file(p)))
    return rows


def pixel_meta(rows):
    """解码一次：像素哈希 + alpha bbox。只保留小图预览用于相似度。"""
    from PIL import Image
    for r in rows:
        im = Image.open(r["path"])
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        r["pxhash"] = hashlib.md5(im.tobytes()).hexdigest()
        bb = im.getchannel("A").getbbox()
        r["bbox"] = bb if bb else (0, 0, r["w"], r["h"])
    return rows


def preview(r, cache={}):
    from PIL import Image
    k = r["path"]
    if k in cache:
        return cache[k]
    im = Image.open(k).convert("RGBA")
    bb = r["bbox"]
    if bb and bb[2] > bb[0] and bb[3] > bb[1]:
        im = im.crop(bb)
    cache[k] = im.resize((S, S), Image.LANCZOS)
    return cache[k]


def sim(ra, rb):
    from PIL import Image, ImageChops, ImageStat
    a, b = preview(ra), preview(rb)
    aa = a.getchannel("A").point(lambda v: 255 if v > 60 else 0)
    ba = b.getchannel("A").point(lambda v: 255 if v > 60 else 0)
    m = ImageChops.multiply(aa, ba)
    cnt = ImageStat.Stat(m).sum[0] / 255.0
    if cnt < 200:
        return None
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    mad = sum(ImageStat.Stat(d, m).mean) / 3.0
    union = ImageStat.Stat(ImageChops.lighter(aa, ba)).sum[0] / 255.0
    return mad, cnt / union


def aspect(r):
    b = r["bbox"]
    return (b[2] - b[0]) / max(1, (b[3] - b[1]))


def mad_head(ra, rb):
    """仅比较归一化图头部区域（表情判据；全图 MAD 被身体/姿势差异淹没）。"""
    from PIL import Image, ImageChops, ImageStat
    a, b = preview(ra), preview(rb)
    aa = a.getchannel("A").point(lambda v: 255 if v > 60 else 0)
    ba = b.getchannel("A").point(lambda v: 255 if v > 60 else 0)
    m = ImageChops.multiply(aa, ba).crop(HEAD_BOX)
    if ImageStat.Stat(m).sum[0] / 255.0 < 50:
        return None
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).crop(HEAD_BOX)
    return sum(ImageStat.Stat(d, m).mean) / 3.0


# ---------------------------------------------------------------- 主流程
def main():
    t0 = time.time()
    os.makedirs(IMGD, exist_ok=True)
    rows = inventory()
    log("inventory:", len(rows), collections.Counter(r["src"] for r in rows))
    pixel_meta(rows)
    for r in rows:
        r["key"] = normalize(r["src"], r["name"])
    unparsed = [r for r in rows if r["key"][0] is None]
    log("unparsed:", [(r["src"], r["name"]) for r in unparsed])

    # 分组（先按 scope 分；np 组稍后可能并入 luc 组）
    groups = collections.OrderedDict()
    for r in rows:
        sc, fam, base, suf, stem = r["key"]
        k = (sc, fam, base, suf)
        groups.setdefault(k, []).append(r)
    luc_keys = [k for k in groups if k[0] == "luc"]
    np_keys = [k for k in groups if k[0] == "np"]
    log("groups raw: luc=%d np=%d" % (len(luc_keys), len(np_keys)))

    # ---------- np 内容归并 ----------
    luc_fam = collections.defaultdict(list)
    for k in luc_keys:
        luc_fam[k[1]].append(k)

    def candidates_for(npkey):
        fam = npkey[1].split("_")[0]
        return luc_fam.get(fam, [])

    # 1) np 内容近同聚类（同 (np 家族, 变体) 桶内做；把「同一张画」的重复条目绑在一起，
    #    避免近同内容各自配到不同 Lucifen 后缀）
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
    np_clusters = 0
    for bkey, mem in buckets.items():
        for i in range(len(mem)):
            for j in range(i + 1, len(mem)):
                r2 = sim(mem[i], mem[j])
                if r2 and r2[0] <= CLUST_TH:
                    union(mem[i]["name"], mem[j]["name"])
    clusters = collections.defaultdict(list)
    for r in np_rows:
        clusters[find(r["name"])].append(r)
    np_clusters = len(clusters)
    log("np near-identical clusters:", np_clusters,
        "(singletons=%d)" % sum(1 for v in clusters.values() if len(v) == 1))

    # 2) 逐簇求「每个 Lucifen 组键」的最优 MAD，取最优键
    assign = {}            # np name -> (luc_key, mad, iou, ambiguous, margin)
    best_mad_hist = []
    pair_margins = []
    rank_detail = []
    np_reject = {}
    for cid, mem in clusters.items():
        per_key = {}
        for r in mem:
            asp = aspect(r)
            for lk in candidates_for(r["key"]):
                for cand in groups[lk]:
                    if abs(asp / aspect(cand) - 1) > ASP_FILTER:
                        continue
                    r2 = sim(r, cand)
                    if not r2 or r2[0] > 60:
                        continue
                    cur = per_key.get(lk)
                    if cur is None or r2[0] < cur[0] - 1e-9:
                        per_key[lk] = (r2[0], r2[1], cand, r)
        if not per_key:
            continue
        # 按「候选像素内容」折叠：ot_asu01 与 ot_asu01i 像素几乎相同 -> 视为同一内容，
        # 否则会把「同一张画的重复后缀」误判成歧义
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
        # 姿势归属唯一性：前三名「不同内容」是否同属一个 Lucifen base（<family,base号>）
        base_best = (lk[1], lk[2])
        pose_unique = all((kv[0][1], kv[0][2]) == base_best for kv in ranked[:3])
        # 表情级判据：同 base 内改用「头部区域 MAD」（全图 MAD 被身体差异淹没）
        head_margin = None
        same_base = [(kv[0], kv[1]) for kv in ranked if (kv[0][1], kv[0][2]) == base_best]
        if len(same_base) >= 2:
            hm = []
            for lk1, (m1, i1, c1, r1) in same_base:
                v = mad_head(rep, c1)
                if v is not None:
                    hm.append((v, lk1, c1))
            hm.sort(key=lambda x: x[0])
            if len(hm) >= 2:
                head_margin = hm[1][0] - hm[0][0]
        if len(ranked) > 1:
            rank_detail.append((rep["name"], mad, margin, pose_unique, head_margin,
                                [(kv[0], round(kv[1][0], 2), kv[1][2]["name"]) for kv in ranked[:3]]))
        best_mad_hist.append(mad)
        pair_margins.append(margin)
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
    log("np contents paired:", len(assign), "/", len(np_rows),
        "  (keys with any MAD<=60 candidate: n=%d)" % len(best_mad_hist))
    if best_mad_hist:
        h = collections.Counter(int(m // 10) * 10 for m in best_mad_hist)
        log("  best-MAD histogram (10-bucket):", dict(sorted(h.items())))
    if pair_margins:
        log("  margin(min-MAD - 2nd-MAD) histogram:",
            dict(sorted(collections.Counter(
                "amb<2" if m < 2 else ("2-5" if m < 5 else ">=5")
                for m in pair_margins).items())))
    n_headamb = sum(1 for r in rank_detail if r[4] is not None and r[4] < HEAD_AMBIG)
    log("  pose_unique=False clusters:", sum(1 for r in rank_detail if not r[3]),
        " ; head-margin<%.1f clusters:" % HEAD_AMBIG, n_headamb,
        " ; total ranked clusters:", len(rank_detail))
    for nm, mm, mg, pu, hmg, top in sorted(rank_detail)[:10]:
        log("   RANK", nm, "mad=%.2f" % mm, "margin=%.2f" % mg, "poseUnique=%s" % pu,
            "headMargin=%s" % (round(hmg, 2) if hmg is not None else "-"), top)

    # 3) 合并：把命中的 np 行搬进 luc 组（键级重映射；未命中的行保持原 4 元组键）
    np_merge_detail = dict(assign)
    groups = collections.OrderedDict()
    for r in rows:
        k = np_merge_detail.get(r["name"], (r["key"][:4],))[0] if r["src"] == "np" \
            else r["key"][:4]
        groups.setdefault(k, []).append(r)

    log("groups after np merge:", len(groups))

    # ---------- 统一名 ----------
    for k, cands in groups.items():
        cands.sort(key=lambda r: (PRIO[r["src"]], r["name"]))
        sc, fam, base, suf, _ = cands[0]["key"]
        cands[0]["_uname"] = cands[0]["key"][4] + ".png"
        for r in cands[1:]:
            r["_uname"] = cands[0]["_uname"]

    name_owner = {}
    for k, cands in groups.items():
        nm = cands[0]["_uname"]
        if nm in name_owner:
            log("!! NAME COLLISION", nm, k, name_owner[nm])
        name_owner[nm] = k

    # ---------- 分类 + 选优 ----------
    def aspect_rel(a, b):
        return abs(a - b) / max(a, b)

    records = []
    for k, cands in groups.items():
        uname = cands[0]["_uname"]
        dims = set((r["w"], r["h"]) for r in cands)
        px = set(r["pxhash"] for r in cands)
        md5s = set(r["md5"] for r in cands)
        if len(cands) == 1:
            cls = "single"
        elif len(dims) == 1:
            cls = "same_res_same" if len(px) == 1 else "same_res_diff"
        else:
            asp = [aspect(r) for r in cands]
            if max(aspect_rel(asp[0], a) for a in asp) <= 0.02:
                cls = "diff_res_same_drawing"
            else:
                cls = "diff_res_diff_drawing"
        sel = sorted(cands, key=lambda r: (-(r["w"] * r["h"]), -r["w"], PRIO[r["src"]]))[0]
        # 内容 bbox 面积最大的候选（用于 canvas padding 疑似检测）
        bb_sel = (sel["bbox"][2] - sel["bbox"][0]) * (sel["bbox"][3] - sel["bbox"][1])
        bb_max = max((r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])
                     for r in cands)
        records.append(dict(key=k, uname=uname, cands=cands, cls=cls, sel=sel,
                            md5_same=(len(md5s) == 1), px_same=(len(px) == 1),
                            bb_sel=bb_sel, bb_max=bb_max))
    log("records:", len(records))

    # ---------- 头像识别 ----------
    AVATAR_FAM = {"f_mis"}                      # ota/chr 148x147 面部差分（实测目视确认）
    NONCHAR_FAM = {"cin", "cit", "cin_red", "cin_blk"}   # 非角色立绘，未识别
    def category(rec):
        fam = rec["key"][1]
        if fam in AVATAR_FAM:
            return "头像"
        if fam in NONCHAR_FAM:
            return "未识别"
        if rec["cls"] == "single" and max(rec["sel"]["w"], rec["sel"]["h"]) <= 260 \
           and 0.9 <= rec["sel"]["w"] / rec["sel"]["h"] <= 1.1:
            return "未识别"
        return "立绘"

    # ---------- 复制产物 ----------
    # 先清理上一轮遗留（统一名可能因算法调整而变化，避免残留旧名文件）
    stale = 0
    for fn in os.listdir(IMGD):
        p = os.path.join(IMGD, fn)
        if os.path.isfile(p) and fn not in name_owner:
            os.remove(p); stale += 1
    log("stale products removed:", stale)
    for rec in records:
        dst = os.path.join(IMGD, rec["uname"])
        shutil.copyfile(rec["sel"]["path"], dst)
    log("copied:", len(records))

    # ---------- 清单 ----------
    def reason(rec):
        c = rec["cls"]
        sel = rec["sel"]
        if c == "single":
            return "组内唯一候选"
        if c == "same_res_same":
            if rec["md5_same"]:
                return "同尺寸同 md5，按源优先级取 %s" % sel["src"]
            return "同尺寸且像素逐字节相同（md5 因 PNG 重编码不同），按源优先级取 %s" % sel["src"]
        if c == "same_res_diff":
            return "同尺寸但像素不同，按源优先级取 %s（内容冲突，见待复核）" % sel["src"]
        if c == "diff_res_same_drawing":
            return "尺寸不同、宽高比接近（同画），取 w*h 最大者 %s %dx%d" % (sel["src"], sel["w"], sel["h"])
        return "尺寸不同且宽高比差异>2%%，取 w*h 最大者 %s %dx%d（见待复核）" % (sel["src"], sel["w"], sel["h"])

    lines = ["统一名\t类别\t尺寸(w,h)\t模式\t字节\t选中源\t选中原名\t组内候选数\t分类\t理由"]
    for rec in sorted(records, key=lambda r: r["uname"]):
        s = rec["sel"]
        lines.append("\t".join([
            rec["uname"], category(rec), "%dx%d" % (s["w"], s["h"]), s["mode"],
            str(s["bytes"]), s["src"], s["name"], str(len(rec["cands"])),
            rec["cls"], reason(rec)]))
    with open(os.path.join(OUTD, "清单_立绘.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # ---------- 待复核 ----------
    rev = ["统一名\t分类\t候选清单\t选中项\t选中理由\t疑点"]
    def candstr(rec):
        return " | ".join("%s:%s:%dx%d:%s%s" % (r["src"], r["name"], r["w"], r["h"],
                                                r["md5"][:8], "（像素同）" if r["pxhash"] == rec["sel"]["pxhash"] and r is not rec["sel"] else "")
                          for r in sorted(rec["cands"], key=lambda r: PRIO[r["src"]]))
    n_srd = n_drd = n_pad = n_npfail = n_nprej = n_amb = n_unid = 0
    for rec in sorted(records, key=lambda r: r["uname"]):
        sus = []
        if rec["cls"] == "same_res_diff":
            sus.append("content_conflict：同尺寸像素不同"); n_srd += 1
        if rec["cls"] == "diff_res_diff_drawing":
            sus.append("aspect_mismatch：宽高比差>2%，可能非同一张画"); n_drd += 1
        if rec["bb_sel"] < rec["bb_max"] * 0.98 and rec["cls"] != "single":
            sus.append("canvas_padding：选中项画布最大但**内容 bbox 面积**（%d）小于组内最大（%d），"
                       "实际绘制分辨率可能更低" % (rec["bb_sel"], rec["bb_max"])); n_pad += 1
        if category(rec) == "未识别":
            sus.append("非角色立绘（疑 cut-in / 演出层），未识别"); n_unid += 1
        np_amb = [d for d in (np_merge_detail.get(r["name"]) if r["src"] == "np" else None
                              for r in rec["cands"]) if d and d[3]]
        np_pu = [d for d in (np_merge_detail.get(r["name"]) if r["src"] == "np" else None
                             for r in rec["cands"]) if d and not d[5]]
        if np_amb:
            sus.append("np_pair_ambiguous：np 内容配对次优 MAD 差<%.1f，表情/姿势归属存疑" % AMBIG_D); n_amb += 1
        if not sus:
            continue
        rev.append("\t".join([rec["uname"], rec["cls"], candstr(rec),
                              "%s:%s" % (rec["sel"]["src"], rec["sel"]["name"]),
                              reason(rec), "；".join(sus)]))
    # np 配对失败（独立保留）
    for k, cands in groups.items():
        if k[0] != "np":
            continue
        r = cands[0]
        fam = k[1].split("_")[0]
        rev.append("\t".join([
            r["_uname"], "np_unpaired", "%s:%s:%dx%d:%s" % (r["src"], r["name"], r["w"], r["h"], r["md5"][:8]),
            "%s:%s" % (r["src"], r["name"]), "独立保留（np 原生 1280x720）",
            "np_unpaired：内容比对未在 `%s` 族中找到 MAD<=%.0f 且 IoU>=%.2f 的对应项，"
            "已作独立素材保留（未强行配对）" % (fam, MAD_TH, IOU_TH)]))
        n_npfail += 1
    # np 有候选但被判不配对（姿势归属不唯一 / 置信不足）
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
    with open(os.path.join(OUTD, "待复核_立绘.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rev) + "\n")

    # ---------- 统计 ----------
    cat = collections.Counter(category(r) for r in records)
    cls = collections.Counter(r["cls"] for r in records)
    per_src = collections.Counter(r["src"] for r in rows)
    tot_cand = sum(len(r["cands"]) for r in records)
    uniq_px = len(set((r["pxhash"], r["w"], r["h"]) for r in rows))
    bytes_sel = sum(r["sel"]["bytes"] for r in records)
    bytes_all = sum(r["bytes"] for r in rows)
    merged_np_rows = len(np_merge_detail)
    np_merged_groups_cnt = len(set(d[0] for d in np_merge_detail.values()))
    np_indep = len([1 for r in records if r["key"][0] == "np"])
    np_merged_files = len(np_merge_detail)
    np_all = len([r for r in rows if r["src"] == "np"])
    pad_src = collections.Counter()
    for rec in records:
        if rec["bb_sel"] < rec["bb_max"] * 0.98 and rec["cls"] != "single":
            pad_src[rec["sel"]["src"]] += 1
    stat = dict(
        files=len(rows), per_source=dict(per_src), groups=len(records),
        sum_candidates=tot_cand, category=dict(cat), classification=dict(cls),
        uniq_pixel_contents=uniq_px, bytes_all=bytes_all, bytes_selected=bytes_sel,
        np_files_total=np_all, np_files_in_np_groups=len(np_rows),
        np_unique_contents=len(by_px),
        np_paired_contents=len(assign), np_merged_files=np_merged_files,
        np_merged_target_groups=np_merged_groups_cnt, np_independent_assets=np_indep,
        review_rows=len(rev) - 1, rev_same_res_diff=n_srd, rev_diff_res_diff_drawing=n_drd,
        rev_canvas_padding=n_pad, rev_canvas_padding_by_selected_src=dict(pad_src),
        rev_unidentified=n_unid, rev_np_ambig=n_amb,
        rev_np_unpaired=n_npfail, rev_np_rejected=n_nprej,
        elapsed_sec=round(time.time() - t0, 1))
    with open(os.path.join(OUTD, "_stats_chr.json"), "w", encoding="utf-8") as f:
        json.dump(stat, f, ensure_ascii=False, indent=1)
    log(json.dumps(stat, ensure_ascii=False, indent=1))

    # np 归并明细（供审计）
    with open(os.path.join(OUTD, "_npmerge_chr.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("np原名\tnp尺寸\t配对目标组(统一名)\t全图MAD\tIoU\t全图次优差值\t头部次优差值\t歧义\n")
        for nm, (lk, mad, iou, amb, margin, pu, hmg) in sorted(np_merge_detail.items()):
            tgt = next((x["_uname"] for x in groups[lk]), "")
            f.write("%s\t%s\t%s\t%.2f\t%.4f\t%.2f\t%s\t%s\n" % (
                nm, "1280x720", tgt, mad, iou, margin,
                ("%.2f" % hmg) if hmg is not None else "-", "Y" if amb else ""))

    # 复现用中间表（供 verify 脚本抽查）
    with open(os.path.join(OUTD, "_pick_chr.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("统一名\t选中源\t选中原名\t选中路径\n")
        for rec in sorted(records, key=lambda r: r["uname"]):
            f.write("\t".join([rec["uname"], rec["sel"]["src"], rec["sel"]["name"],
                               rec["sel"]["path"]]) + "\n")


if __name__ == "__main__":
    main()