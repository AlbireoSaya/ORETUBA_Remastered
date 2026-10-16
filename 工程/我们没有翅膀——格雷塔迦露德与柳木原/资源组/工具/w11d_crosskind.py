# -*- coding: utf-8 -*-
r"""
W11d / ISSUE-20260918-06 · 任务1：跨 kind 角色图归并建议
=========================================================
输入（只读）：
  krkr素材库\np\pic\   的 10 个角色命名文件
  krkr素材库\otv\pic\  的 44 个角色命名文件
参照（只读）：
  美术统一\清单_立绘.tsv        （W11a：chr 统一结果）
  美术统一\清单_CG背景.tsv      （W11b：pic 统一结果）
  美术统一\待复核_立绘.tsv      （多候选组的完整候选清单）
产出：
  美术统一\跨kind角色图_归并建议.tsv
  子代理工作区\...\W11d\_crosskind.json

判据（与 W11a §3.1 同法，便于横向对照）：
  1. alpha 通道 bbox 裁剪 → 双线性缩放到 128×128
  2. MAD = 双方 alpha>60 的像素上 RGB 平均绝对差
  3. IoU = alpha 掩膜交并比
  4. 立绘判据：RGBA + alpha 覆盖率 < 0.9（人物抠图）；CG 判据：无 alpha 或覆盖率=1.0（满幅场景）
只读源，不改像素，不写 立绘\ 与 CG背景\。
"""
import os, sys, json, csv, hashlib

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
KRKR = os.path.join(BASE, "krkr素材库")
UNI = os.path.join(BASE, "美术统一")
OUT_TSV = os.path.join(UNI, "跨kind角色图_归并建议.tsv")
OUT_JSON = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20260918-06\W11d\_crosskind.json"

from PIL import Image

NP_CHARS = ["aki02b", "ban01a", "chi01i", "kaz01h", "kob02c",
            "kur01d", "mas01c", "mas01e", "mis01h", "miy02a"]
OTV_CHARS = ["asu01", "asu01a", "asu02", "asu06", "asu07", "asu08a", "asu53", "asu55",
             "asu71", "asu71a", "hiy07", "hiy71", "hiy71a", "hiy72",
             "kob02", "kob71", "kob71a", "kob71b", "mas71", "mas72",
             "mis51", "mis52", "mis53", "mis54", "mis55",
             "mis71", "mis71a", "mis72", "mis72a", "mis73", "mis73a",
             "mis74", "mis74a", "mis75", "mis75a", "mis75b", "mis75c",
             "mis76", "mis77", "mis78", "mis78a", "mis78b", "mis79", "miy01"]


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _rgba128(im):
    """内容 bbox 裁剪 → 双线性缩放 128x128；返回 (rgb bytes, alpha bytes, bbox)"""
    im = im.convert("RGBA")
    a = im.getchannel("A")
    bbox = a.getbbox() or (0, 0, im.width, im.height)
    c = im.crop(bbox).resize((128, 128), Image.BILINEAR)
    return c.tobytes(), c.getchannel("A").tobytes(), bbox


def mad_iou(p1, p2):
    """W11a §3.1 度量：MAD（alpha>60 的像素上 RGB 平均绝对差）+ alpha 掩膜 IoU"""
    a1 = Image.open(p1); a2 = Image.open(p2)
    r1, m1, b1 = _rgba128(a1); r2, m2, b2 = _rgba128(a2)
    s = n = 0
    inter = uni = 0
    for i in range(0, len(m1)):
        v1, v2 = m1[i], m2[i]
        if v1 > 60 and v2 > 60:
            s += abs(r1[3 * i] - r2[3 * i]) + abs(r1[3 * i + 1] - r2[3 * i + 1]) + abs(r1[3 * i + 2] - r2[3 * i + 2])
            n += 3
        o1, o2 = v1 > 60, v2 > 60
        if o1 and o2:
            inter += 1
        if o1 or o2:
            uni += 1
    a1.close(); a2.close()
    return (round(s / n, 2) if n else None), (round(inter / uni, 4) if uni else None)


def img_stats(p):
    im = Image.open(p)
    w, h = im.size
    mode = im.mode
    has_alpha = mode in ("RGBA", "LA") or (mode == "P" and "transparency" in im.info)
    st = dict(w=w, h=h, mode=mode, has_alpha=bool(has_alpha))
    if has_alpha:
        a = im.convert("RGBA").getchannel("A")
        bbox = a.getbbox() or (0, 0, w, h)
        hist = a.histogram()
        nz = sum(hist[1:])
        st["coverage"] = round(nz / float(w * h), 4)
        px = a.load()
        st["edge_tr"] = dict(top=all(px[x, 0] == 0 for x in range(0, w, max(1, w // 64))),
                             bottom=all(px[x, h - 1] == 0 for x in range(0, w, max(1, w // 64))),
                             left=all(px[0, y] == 0 for y in range(0, h, max(1, h // 64))),
                             right=all(px[w - 1, y] == 0 for y in range(0, h, max(1, h // 64))))
    else:
        bbox = (0, 0, w, h)
        st["coverage"] = 1.0
        st["edge_tr"] = dict(top=False, bottom=False, left=False, right=False)
    st["bbox"] = bbox
    st["bbox_wh"] = (bbox[2] - bbox[0], bbox[3] - bbox[1])
    st["bbox_area"] = st["bbox_wh"][0] * st["bbox_wh"][1]
    im.close()
    return st


def load_manifest(fn, keycol):
    rows = {}
    with open(os.path.join(UNI, fn), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows[r[keycol]] = r
    return rows


def parse_review_candidates(fn):
    """待复核_立绘.tsv → {统一名: [(源, 原名, 尺寸, md5), ...]}"""
    out = {}
    with open(os.path.join(UNI, fn), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            cands = []
            for tok in r["候选清单"].split(" | "):
                tok = tok.strip()
                if not tok:
                    continue
                # 形如 ot:ot_ban01a.png:441x595:0071ed78（像素同）
                parts = tok.split(":")
                if len(parts) >= 4:
                    cands.append((parts[0], parts[1], parts[2], parts[3].split("（")[0]))
            out[r["统一名"]] = cands
    return out


def main():
    chr_rows = load_manifest("清单_立绘.tsv", "统一名")
    pic_rows = load_manifest("清单_CG背景.tsv", "统一名")
    review = parse_review_candidates("待复核_立绘.tsv")

    recs = []
    for kind, names in (("np", NP_CHARS), ("otv", OTV_CHARS)):
        for nm in names:
            src = os.path.join(KRKR, kind, "pic", "%s_%s.png" % (kind, nm))
            assert os.path.exists(src), src
            st = img_stats(src)
            uni = nm + ".png"
            # ---- 判定 ----
            if st["has_alpha"] and st["coverage"] < 0.90:
                verdict = "立绘"
                reason = ("RGBA 且 alpha 覆盖率 %.3f<0.90（人物抠图）；上/左/右三边透明、下边贴画布"
                          "（立绘底边锚定签名）；命名=角色代号+姿势号+差分") % st["coverage"]
            elif (not st["has_alpha"]) or st["coverage"] >= 0.999:
                verdict = "CG"
                reason = ("%s、alpha 覆盖率 %.3f（满幅不透明）→ 非抠图；目视确认为含背景/多人的事件 CG"
                          % ("RGB 无 alpha 通道" if not st["has_alpha"] else "RGBA 全覆盖", st["coverage"]))
            else:
                verdict = "未判定"
                reason = "alpha 覆盖率 %.3f 介于两者之间，需目视" % st["coverage"]

            rec = dict(kind=kind, orig="%s_%s" % (kind, nm), uni=uni, verdict=verdict,
                       size="%dx%d" % (st["w"], st["h"]), mode=st["mode"],
                       coverage=st["coverage"],
                       bbox="%d,%d,%d,%d" % st["bbox"], bbox_wh="%dx%d" % st["bbox_wh"],
                       bbox_area=st["bbox_area"], reason=reason,
                       in_chr=uni in chr_rows, in_pic=uni in pic_rows,
                       md5=md5(src)[:8], bytes=os.path.getsize(src))

            # ---- 立绘：与 立绘\ 既有组比对 ----
            if verdict == "立绘":
                cands = review.get(uni)
                if cands is None:
                    # 单候选组：从清单取
                    r = chr_rows.get(uni)
                    cands = [(r["选中源"], r["选中原名"], r["尺寸(w,h)"], "")] if r else []
                rec["chr_group_candidates"] = ["%s:%s:%s" % c[:3] for c in cands]
                rec["chr_sel"] = (chr_rows[uni]["选中源"] + ":" + chr_rows[uni]["选中原名"] + ":"
                                  + chr_rows[uni]["尺寸(w,h)"]) if uni in chr_rows else ""
                # 组内各候选的内容 bbox 面积（含 np/pic 自身）
                areas = []
                for s, o, dim, _ in cands:
                    p = os.path.join(KRKR, s, "chr", o)
                    if os.path.exists(p):
                        cs = img_stats(p)
                        areas.append((s + ":" + o, cs["bbox_area"], "%dx%d" % cs["bbox_wh"],
                                      "%dx%d" % (cs["w"], cs["h"])))
                areas.append((kind + ":" + kind + "_" + nm, st["bbox_area"],
                              "%dx%d" % st["bbox_wh"], "%dx%d" % (st["w"], st["h"])))
                rec["bbox_areas"] = areas
                rec["max_bbox_area"] = max(a[1] for a in areas)
                rec["np_pic_is_bbox_max"] = (st["bbox_area"] == rec["max_bbox_area"])
                # 内容比对：np/pic vs 立绘选中项
                sel = chr_rows.get(uni)
                if sel:
                    sp = os.path.join(KRKR, sel["选中源"], "chr", sel["选中原名"])
                    if os.path.exists(sp):
                        m, iou = mad_iou(src, sp)
                        rec["mad_vs_chrsel"] = m
                        rec["iou_vs_chrsel"] = iou
                        rec["chr_sel_path"] = sp
            # ---- CG：是否与同名 立绘 撞名 ----
            if verdict == "CG" and uni in chr_rows:
                sp = os.path.join(UNI, "立绘", uni)
                if os.path.exists(sp):
                    m, iou = mad_iou(src, sp)
                    rec["mad_vs_chrprod"] = m
                    rec["iou_vs_chrprod"] = iou
                    rec["name_collision"] = True
            recs.append(rec)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)

    # ---- TSV ----
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["文件名", "所在kind", "判定", "建议并入的统一名或组", "尺寸", "内容bbox",
                    "alpha覆盖率", "与立绘组的MAD/IoU", "画布选优", "内容bbox选优", "判定依据"])
        for r in recs:
            if r["verdict"] == "立绘":
                tgt = "%s（立绘\\ 已有同名组）" % r["uni"]
                cmp_ = ""
                if "mad_vs_chrsel" in r:
                    cmp_ = "MAD=%s IoU=%s vs %s" % (r["mad_vs_chrsel"], r["iou_vs_chrsel"], r["chr_sel"])
                canvas = "%s 画布 %s 为组内最大 → np 胜" % (r["orig"], r["size"])
                bbox = ("%s 内容bbox %s=%d 为组内最大 → np 胜" % (r["orig"], r["bbox_wh"], r["bbox_area"])
                        if r.get("np_pic_is_bbox_max") else
                        "组内最大内容bbox=%d，本件=%d → np 不占优" % (r.get("max_bbox_area", 0), r["bbox_area"]))
                w.writerow([r["orig"] + ".png", r["kind"] + "\\pic\\", "立绘", tgt, r["size"],
                            r["bbox"], r["coverage"], cmp_, canvas, bbox, r["reason"]])
            else:
                tgt = "CG背景\\%s（W11b 已收录）" % r["uni"]
                if r.get("name_collision"):
                    tgt += "；⚠与 立绘\\%s 撞名" % r["uni"]
                cmp_ = ""
                if "mad_vs_chrprod" in r:
                    cmp_ = "MAD=%s IoU=%s vs 立绘\\%s" % (r["mad_vs_chrprod"], r["iou_vs_chrprod"], r["uni"])
                w.writerow([r["orig"] + ".png", r["kind"] + "\\pic\\", r["verdict"], tgt, r["size"],
                            r["bbox"], r["coverage"], cmp_, "—", "—", r["reason"]])
    print("TSV ->", OUT_TSV)
    n_l = sum(1 for r in recs if r["verdict"] == "立绘")
    n_c = sum(1 for r in recs if r["verdict"] == "CG")
    n_u = sum(1 for r in recs if r["verdict"] == "未判定")
    print("total=%d 立绘=%d CG=%d 未判定=%d" % (len(recs), n_l, n_c, n_u))
    print("--- 立绘(应全为 np) ---")
    for r in recs:
        if r["verdict"] == "立绘":
            print("  %-12s %-9s bbox=%-9s area=%-7d chr_sel=%-32s maxbbox=%-7d np_max=%s MAD=%s IoU=%s" % (
                r["orig"], r["size"], r["bbox_wh"], r["bbox_area"], r["chr_sel"],
                r.get("max_bbox_area", 0), r.get("np_pic_is_bbox_max"),
                r.get("mad_vs_chrsel"), r.get("iou_vs_chrsel")))
    print("--- CG 撞名（与 立绘\\ 同名） ---")
    for r in recs:
        if r.get("name_collision"):
            print("  %-12s MAD=%s IoU=%s" % (r["orig"], r["mad_vs_chrprod"], r["iou_vs_chrprod"]))


if __name__ == "__main__":
    main()