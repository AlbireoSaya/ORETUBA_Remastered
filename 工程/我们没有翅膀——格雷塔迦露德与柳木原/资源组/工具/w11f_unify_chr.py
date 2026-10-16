# -*- coding: utf-8 -*-
"""
W11f · 立绘重建（在 W11e 基础上并入 np\\pic 的 10 个立绘）
==========================================================
做法：复用 W11e 的**全部**逻辑（内容面积选源 + np 优先 + 5% 门控拆分），
      仅把 `np\\pic\\` 的 10 个已判定为立绘的文件追加进 chr 候选清单
      （src='np'，命名 `np_aki02b` 经 normalize 落进 luc 组 → 参与 np 优先选优）。
      → 不改动 W11e 的任何判据/阈值，差异只来自「候选集合 +10」。

纪律：只读源；产物原字节复制；原子写由 W11e 的 atomic_write 保证。
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unify_chr as U            # noqa: E402
import unify_chr_w11e as W       # noqa: E402

NP_PIC_10 = ["np_aki02b.png", "np_ban01a.png", "np_chi01i.png", "np_kaz01h.png",
             "np_kob02c.png", "np_kur01d.png", "np_mas01c.png", "np_mas01e.png",
             "np_mis01h.png", "np_miy02a.png"]

# ---- W11f 目视终裁：以下组经目视确认为「同一张画的不同裁切」→ 强制单簇（撤销门控拆分）----
# 依据见 美术统一\门控拆分_目视终裁表.tsv（W11f / 2026-09-19）。
FORCE_MERGE = set(
    ["cin008", "cin_blk2",
     "kur01", "kur01a", "kur01b", "kur01c", "kur01d", "kur01e", "kur01f", "kur01g",
     "kur01h", "kur01i",
     "kur02", "kur02a", "kur02b", "kur02c", "kur02d", "kur02e", "kur02f", "kur02g",
     "kur02h", "kur02i",
     "miy02a", "chi01i", "lr201e"])

_orig_clusters = W.clusters_by_aspect


def clusters_forced(cands):
    stem = min(cands, key=lambda r: (W.PRIO[r["src"]], r["name"]))["key"][4]
    if stem in FORCE_MERGE:
        return [list(cands)]
    return _orig_clusters(cands)


W.clusters_by_aspect = clusters_forced

_orig_inventory = U.inventory


def inventory_with_np_pic():
    rows = _orig_inventory()
    names = {r["name"] for r in rows}
    for fn in NP_PIC_10:
        if fn in names:
            raise SystemExit("duplicate name in chr inventory: " + fn)
        p = os.path.join(U.LIB, "np", "pic", fn)
        if not os.path.isfile(p):
            raise SystemExit("missing: " + p)
        w, h, mode = U.png_ihdr(p)
        rows.append(dict(src="np", name=fn, path=p, w=w, h=h, mode=mode,
                         bytes=os.path.getsize(p), md5=U.md5_file(p)))
    return rows


# ------------------------------------------------------------------ 收尾后处理
WORK = os.path.abspath(os.path.join(U.BASE, "..", "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")
BACKUP = os.path.join(WORK, "_backup_W11e")


def _read_tsv(p):
    with open(p, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def _write(p, hdr, rows):
    tmp = p + ".tmp_w11f"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(["\t".join(hdr)] + ["\t".join(r) for r in rows]) + "\n")
    os.replace(tmp, p)


def finalize():
    """1) 把 FORCE_MERGE 组在清单/待复核里由「不同素材」改标为「同画不同裁切」；
       2) 生成 W11e → W11f 的选源变更表。"""
    # (1) 清单
    lp = os.path.join(U.OUTD, "清单_立绘.tsv")
    hdr, rows = _read_tsv(lp)
    ix = {c: i for i, c in enumerate(hdr)}
    n = 0
    for r in rows:
        stem = r[ix["统一名"]][:-4]
        if stem in FORCE_MERGE and r[ix["分类"]] == "diff_res_diff_drawing":
            r[ix["分类"]] = "diff_res_same_drawing"
            r[ix["理由"]] = r[ix["理由"]] + "；W11f 目视终裁：同一张画的不同裁切，已撤销门控拆分"
            n += 1
    _write(lp, hdr, rows)
    print("[finalize] 清单改标 diff_res_same_drawing:", n)

    # (2) 待复核
    rp = os.path.join(U.OUTD, "待复核_立绘.tsv")
    rhdr, rrows = _read_tsv(rp)
    rix = {c: i for i, c in enumerate(rhdr)}
    m = 0
    for r in rrows:
        stem = r[rix["统一名"]][:-4]
        if stem in FORCE_MERGE and "aspect_mismatch" in r[rix["疑点"]]:
            r[rix["分类"]] = "diff_res_same_drawing"
            r[rix["疑点"]] = ("framing_merged：内容宽高比差>5%，但 W11f 目视终裁为**同一张画的不同裁切**，"
                             "已撤销门控拆分、合并为单一产物（证据见 门控拆分_目视终裁表.tsv）")
            m += 1
    _write(rp, rhdr, rrows)
    print("[finalize] 待复核改标 framing_merged:", m)

    # (3) W11e → W11f 选源变更表
    _, old_pick = _read_tsv(os.path.join(BACKUP, "_pick_chr.tsv"))
    _, old_lst = _read_tsv(os.path.join(BACKUP, "清单_立绘.tsv"))
    old_by_name = {r[0]: r for r in old_lst}       # 统一名 -> 行
    _, new_pick = _read_tsv(os.path.join(U.OUTD, "_pick_chr.tsv"))
    _, new_lst = _read_tsv(os.path.join(U.OUTD, "清单_立绘.tsv"))
    new_by_name = {r[0]: r for r in new_lst}
    ol = {r[0]: r for r in old_pick}
    nl = {r[0]: r for r in new_pick}

    def area_of(row):
        # 清单列: 0统一名 2尺寸 10画布 11内容bbox 12内容面积
        try:
            return int(row[12])
        except Exception:
            return 0

    chg = []
    for u in sorted(set(nl) | set(ol)):
        o = ol.get(u)
        nw = nl.get(u)
        if o and nw and o[1] == nw[1] and o[2] == nw[2]:
            continue
        ol_row = old_by_name.get(u)
        nw_row = new_by_name.get(u)
        oa = area_of(ol_row) if ol_row else 0
        na = area_of(nw_row) if nw_row else 0
        gain = ("%.1f" % ((na - oa) / oa * 100.0)) if oa else "-"
        if not o:
            ctype = "新增（拆分/合并产物）"
        elif not nw:
            ctype = "删除（撤销拆分）"
        elif oa and na > oa:
            ctype = "内容面积改选"
        else:
            ctype = "改选"
        chg.append([u,
                    ("%s:%s" % (o[1], o[2])) if o else "-",
                    ("%s:%s" % (nw[1], nw[2])) if nw else "-",
                    ol_row[10] if ol_row else "-",
                    nw_row[10] if nw_row else "-",
                    str(oa) if oa else "-", str(na) if na else "-", gain,
                    nw_row[8] if nw_row else (ol_row[8] if ol_row else "-"), ctype])
    _write(os.path.join(U.OUTD, "立绘_选源变更表.tsv"),
           ["统一名", "旧选源", "新选源", "旧画布", "新画布", "旧内容面积", "新内容面积",
            "面积增益%", "分类", "变更类型"], chg)
    print("[finalize] W11e→W11f 选源变更表行数:", len(chg))


if __name__ == "__main__":
    U.inventory = inventory_with_np_pic
    W.main()
    finalize()