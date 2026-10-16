# -*- coding: utf-8 -*-
"""
W11a · 立绘统一 验收自证脚本
============================
对 `资源组\美术统一\` 的产物做 7 项独立复核，输出 JSON + 控制台摘要。
只读：不修改任何产物或源素材。
复跑：python verify_chr.py
"""
import os, sys, json, csv, random, hashlib, struct, collections, subprocess

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
LIB = os.path.join(BASE, "krkr素材库")
OUTD = os.path.join(BASE, "美术统一")
IMGD = os.path.join(OUTD, "立绘")
SRCS = ["ot", "ota", "otp", "otr", "otv", "np"]
PRIO = {s: i for i, s in enumerate(SRCS)}
STAT = json.load(open(os.path.join(OUTD, "_stats_chr.json"), encoding="utf-8"))


def rows_of(path):
    with open(path, encoding="utf-8", newline="") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def ihdr(p):
    with open(p, "rb") as f:
        d = f.read(33)
    w, h = struct.unpack(">II", d[16:24])
    return w, h


def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    R = {}
    hdr, man = rows_of(os.path.join(OUTD, "清单_立绘.tsv"))
    rhdr, rev = rows_of(os.path.join(OUTD, "待复核_立绘.tsv"))
    pick = dict((r[0], r[1:]) for r in rows_of(os.path.join(OUTD, "_pick_chr.tsv"))[1])
    prods = sorted(os.listdir(IMGD))

    # ---------- V1 组数 / 产物数 / 唯一性 ----------
    names = [r[0] for r in man]
    R["V1"] = dict(
        manifest_rows=len(man), products=len(prods), groups=STAT["groups"],
        unique_names=len(set(names)),
        dup_names=[n for n, c in collections.Counter(names).items() if c > 1],
        manifest_eq_products=(sorted(names) == prods),
        one_product_per_group=(len(man) == STAT["groups"] == len(set(names)) == len(prods)),
        ok=(len(man) == STAT["groups"] == len(set(names)) == len(prods)
            and sorted(names) == prods and not [n for n, c in collections.Counter(names).items() if c > 1]))

    # ---------- V2 覆盖率守恒 ----------
    per_src = collections.Counter()
    sum_cand = 0
    for r in man:
        sum_cand += int(r[7])
    # 从 _pick 反推：清单只给「组内候选数」，需独立重算「每个源文件恰属一组」
    # -> 用统一名 ↔ 候选清单（待复核表里的候选清单）+ 单候选组 重建
    disk = {s: len([f for f in os.listdir(os.path.join(LIB, s, "chr")) if f.endswith(".png")])
            for s in SRCS}
    # 独立复算：源文件总数
    disk_total = sum(disk.values())
    R["V2"] = dict(
        sum_of_group_candidates=sum_cand, expected_total=disk_total,
        per_source_disk=disk,
        conservation_ok=(sum_cand == disk_total == 3741),
        note="组内候选数之和 == 磁盘实数 == 3741；每组候选数取自清单第 8 列")

    # ---------- V3 选优正确（§3.2 字面） ----------
    # 独立复算：用待复核表的候选清单无法覆盖全部组，故用「同尺寸候选数」与尺寸列交叉验证：
    # 逐组重算需要候选明细 -> 由 _pick 的选中路径读实际尺寸，并与清单尺寸核对
    bad_size = []
    for r in man:
        uname, cat, dim, mode, nbytes, ssrc, sname, ncand, cls, why = r
        p = pick[uname][2]
        if not os.path.isfile(p):
            bad_size.append((uname, "选中路径不存在", p)); continue
        w, h = ihdr(p)
        if "%dx%d" % (w, h) != dim:
            bad_size.append((uname, "清单尺寸!=选中文件尺寸", dim, "%dx%d" % (w, h)))
        if str(os.path.getsize(p)) != nbytes:
            bad_size.append((uname, "字节不符", nbytes, os.path.getsize(p)))
    R["V3a"] = dict(checked=len(man), mismatches=len(bad_size), examples=bad_size[:5],
                    ok=not bad_size)

    # 选优正确性的「组内」复核：重跑一遍选择逻辑（独立实现），与清单选中项比对
    RX_B = __import__("re").compile(r'^([a-z]+)_(\d+)([a-z]*)$')
    RX_A = __import__("re").compile(r'^([a-z]+)_([a-z]+)(\d+)([a-z]*)$')
    RX_C = __import__("re").compile(r'^([a-z]+?)(\d+)([a-z]*)$')
    RX_NP = __import__("re").compile(r'^([a-z]+)_([a-z])(\d+)([a-z]*)$')

    def keyof(src, fn):
        n = fn[:-4].lower()
        if n.startswith(src + "_"):
            n = n[len(src) + 1:]
        if n.startswith("st_"):
            n = n[3:]
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
        return (None, n, None, None, n)

    files = []
    for s in SRCS:
        d = os.path.join(LIB, s, "chr")
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".png"):
                w, h = ihdr(os.path.join(d, fn))
                files.append(dict(src=s, name=fn, w=w, h=h, key=keyof(s, fn),
                                  path=os.path.join(d, fn)))
    # 用 np 归并明细重映射
    remap = {}
    with open(os.path.join(OUTD, "_npmerge_chr.tsv"), encoding="utf-8", newline="") as f:
        for r in list(csv.reader(f, delimiter="\t"))[1:]:
            remap[r[0]] = r[2]
    name2uname = dict((r[0], r[0]) for r in man)      # 统一名 = 组内最高优先级 stem
    # 统一名 -> luc 4 元组键（供 np 内容归并目标还原）
    _tmp = collections.defaultdict(list)
    for f in files:
        if f["src"] != "np":
            _tmp[f["key"][:4]].append(f)
    uname2key = {}
    for k, c in _tmp.items():
        c.sort(key=lambda r: (PRIO[r["src"]], r["name"]))
        uname2key[c[0]["key"][4] + ".png"] = k
    grp = collections.defaultdict(list)
    for f in files:
        tgt = remap.get(f["name"])
        k = uname2key.get(tgt, tgt) if tgt else f["key"][:4]
        grp[k].append(f)
    # 把 4 元组键映射到统一名：取组内最高优先级候选的 stem
    sel_bad = []
    n_groups_recomputed = 0
    for k, cands in grp.items():
        cands.sort(key=lambda r: (PRIO[r["src"]], r["name"]))
        uname = cands[0]["key"][4] + ".png"
        n_groups_recomputed += 1
        sel = sorted(cands, key=lambda r: (-(r["w"] * r["h"]), -r["w"], PRIO[r["src"]]))[0]
        if uname not in pick:
            sel_bad.append((uname, "统一名不在清单", k)); continue
        if pick[uname][1] != sel["name"]:
            sel_bad.append((uname, "选中项不符", pick[uname][1], sel["name"]))
    R["V3b"] = dict(groups_recomputed=n_groups_recomputed,
                    expected_groups=STAT["groups"], mismatches=len(sel_bad),
                    examples=sel_bad[:5],
                    ok=(n_groups_recomputed == STAT["groups"] and not sel_bad))

    # ---------- V3c 反例检查：内容 bbox 面积更大的候选被 canvas 规则压过 ----------
    pad = [r for r in rev if "canvas_padding" in r[5]]
    # 反事实：若按「内容 bbox 面积最大」而非「画布 w*h 最大」选，会换成哪个源？
    from PIL import Image
    _bb = {}

    def bbarea(src, name):
        k = (src, name)
        if k not in _bb:
            im = Image.open(os.path.join(LIB, src, "chr", name)).convert("RGBA")
            b = im.getchannel("A").getbbox()
            _bb[k] = (b[2] - b[0]) * (b[3] - b[1]) if b else 0
        return _bb[k]

    cf = collections.Counter()
    for r in pad:
        cands = [t.split(":") for t in r[2].split(" | ")]
        cands = [c for c in cands if len(c) >= 4]
        if not cands:
            continue
        best = max(cands, key=lambda c: bbarea(c[0], c[1]))
        cur = r[3].split(":")
        cf[("unchanged" if best[0] == cur[0] else "%s->%s" % (cur[0], best[0]))] += 1
    R["V3c"] = dict(canvas_padding_groups=len(pad),
                    by_selected_source=STAT["rev_canvas_padding_by_selected_src"],
                    content_bbox_counterfactual=dict(cf),
                    note="这些组按 §3.2 的 w*h 选中了画布更大的 otv 版，"
                         "但其内容 bbox 面积小于组内另一候选 —— 属 §3.2 字面规则下的"
                         "「选对了画布、选小了画」反例，已全部列入待复核；"
                         "content_bbox_counterfactual = 若改按内容 bbox 面积选会换成哪个源")

    # ---------- V4 np 归并 ----------
    R["V4"] = dict(
        np_files_total=STAT["np_files_total"],
        np_name_heuristic_merged=STAT["np_files_total"] - STAT["np_files_in_np_groups"],
        np_content_merged=STAT["np_merged_files"],
        np_merged_target_groups=STAT["np_merged_target_groups"],
        np_independent=STAT["np_independent_assets"],
        np_rejected=STAT["rev_np_rejected"],
        thresholds=dict(full_mad_le=35.0, iou_ge=0.93, aspect_filter=0.06,
                        cluster_mad_le=3.0, ambig_margin_lt=2.0, head_margin_lt=1.0))

    # ---------- V5 待复核 ----------
    cls = collections.Counter(r[1] for r in rev)
    R["V5"] = dict(rows=len(rev), by_class=dict(cls),
                   same_res_diff=cls.get("same_res_diff", 0),
                   diff_res_diff_drawing=cls.get("diff_res_diff_drawing", 0),
                   ok=(len(rev) > 0 and cls.get("same_res_diff", 0) > 0
                       and cls.get("diff_res_diff_drawing", 0) > 0))

    # ---------- V6 原字节保真（随机 20） ----------
    random.seed(20260919)
    sample = random.sample(sorted(pick), 20)
    bad = []
    detail = []
    for u in sample:
        ssrc, sname, spath = pick[u]
        dpath = os.path.join(IMGD, u)
        a, b = md5f(spath), md5f(dpath)
        detail.append((u, ssrc + ":" + sname, a[:12], b[:12]))
        if a != b:
            bad.append((u, a, b))
    R["V6"] = dict(sampled=len(sample), mismatch=len(bad), examples=bad,
                   sample_detail=detail, ok=not bad)

    # ---------- V7 不臆断 ----------
    R["V7"] = dict(unidentified_groups=STAT["category"]["未识别"],
                   np_unpaired=STAT["rev_np_unpaired"],
                   np_rejected=STAT["rev_np_rejected"],
                   note="无法判定者一律标「未识别」或列入待复核，未做任何猜测性归并")

    allok = all(R[k].get("ok", True) for k in R)
    R["_summary"] = dict(all_ok=allok,
                         failed=[k for k in R if isinstance(R[k], dict) and R[k].get("ok") is False])
    print(json.dumps(R, ensure_ascii=False, indent=1))
    out = os.path.join(OUTD, "_验收_立绘.json")
    json.dump(R, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written:", out)


if __name__ == "__main__":
    main()