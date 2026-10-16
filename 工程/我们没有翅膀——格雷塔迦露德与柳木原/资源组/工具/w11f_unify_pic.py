# -*- coding: utf-8 -*-
"""
W11f · CG背景（pic）收口：剔除 np\\pic 的 10 个立绘 + 撞名加 cg_ 前缀
=====================================================================
依据：任务 W11f 第 2、3 项。
 - 第 2 项：np\\pic 10 个（已判定为立绘）从 CG背景 侧移除（其 np 候选并入 立绘）。
 - 第 3 项：CG背景 侧统一名若与 立绘\\ 同名 → 加 `cg_` 前缀（立绘侧不动）。
只读源；产物原字节复制；清单/待复核原子写。
"""
import os, sys, json, shutil, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
RES = os.path.join(PROJ, "资源组")
LIB = os.path.join(RES, "krkr素材库")
UNI = os.path.join(RES, "美术统一")
IMGD = os.path.join(UNI, "CG背景")
LIRITSU = os.path.join(UNI, "立绘")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")

NP10 = ["aki02b", "ban01a", "chi01i", "kaz01h", "kob02c", "kur01d",
        "mas01c", "mas01e", "mis01h", "miy02a"]
PREFIX = "cg_"


def atomic_write(path, text):
    tmp = path + ".tmp_w11f"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def read_tsv(p):
    with open(p, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def main():
    meta = json.load(open(os.path.join(WORK, "_meta_cache.json"), encoding="utf-8"))
    by_name = {}
    for m in meta.values():
        by_name[(m["src"], m["kind"], m["name"])] = m

    hdr, rows = read_tsv(os.path.join(UNI, "清单_CG背景.tsv"))
    print("清单_CG背景 rows:", len(rows), "hdr", hdr)
    idx = {c: i for i, c in enumerate(hdr)}

    # 立绘 名字集合
    liri_names = {fn for fn in os.listdir(LIRITSU) if fn.lower().endswith(".png")}

    removed, reselected, renamed = [], [], []
    new_rows = []
    for r in rows:
        uname = r[idx["统一名"]]
        stem = uname[:-4]
        if stem in NP10:
            # np/pic 立绘：从 CG背景 移除
            if r[idx["选中源"]] == "np":
                # 若该 stem 无其它源候选 → 删除产物
                others = [k for k in by_name
                          if k[1] == "pic" and k[2][:-4][len(k[0]) + 1:].lower() == stem
                          and k[0] != "np"]
                if not others:
                    p = os.path.join(IMGD, uname)
                    if os.path.isfile(p):
                        os.remove(p)
                    removed.append(uname)
                    continue
                # 有其它源（仅 miy02a）：改选内容面积最大者
                cands = [by_name[k] for k in others]
                pick = max(cands, key=lambda m: (
                    (m["bbox"][2] - m["bbox"][0]) * (m["bbox"][3] - m["bbox"][1]),
                    m["bbox"][2] - m["bbox"][0], -["ot", "otr", "ota", "otp", "otv", "np"].index(m["src"])))
                src_path = os.path.join(LIB, pick["src"], "pic", pick["name"])
                shutil.copyfile(src_path, os.path.join(IMGD, uname))
                old = (r[idx["选中源"]], r[idx["选中原名"]], r[idx["尺寸(w,h)"]])
                r[idx["选中源"]] = pick["src"]
                r[idx["选中原名"]] = pick["name"]
                r[idx["尺寸(w,h)"]] = "%dx%d" % (pick["w"], pick["h"])
                r[idx["模式"]] = pick["mode"]
                r[idx["字节"]] = str(pick["bytes"])
                r[idx["组内候选数"]] = str(len(cands))
                r[idx["理由"]] = r[idx["理由"]] + "；W11f：np\\pic 立绘并入 立绘\\ 后改选 %s" % pick["src"]
                reselected.append((uname, old, (pick["src"], pick["name"])))
                new_rows.append(r)
                continue
            else:
                removed.append(uname + "(非np选中，未删)")
                new_rows.append(r)
                continue
        new_rows.append(r)

    # ---- 撞名加 cg_ 前缀 ----
    coll = sorted({r[idx["统一名"]] for r in new_rows} & liri_names)
    print("撞名（加前缀前）:", len(coll))
    coll_set = set(coll)
    for r in new_rows:
        uname = r[idx["统一名"]]
        if uname in coll_set:
            newname = PREFIX + uname
            src = os.path.join(IMGD, uname)
            dst = os.path.join(IMGD, newname)
            shutil.copyfile(src, dst)
            os.remove(src)
            r[idx["统一名"]] = newname
            r[idx["理由"]] = r[idx["理由"]] + "；W11f：与 立绘\\ 同名，CG侧加 cg_ 前缀"
            renamed.append((uname, newname))

    # 写清单（按统一名排序，保持原列序）
    new_rows.sort(key=lambda r: r[idx["统一名"]])
    atomic_write(os.path.join(UNI, "清单_CG背景.tsv"),
                 "\n".join(["\t".join(hdr)] + ["\t".join(r) for r in new_rows]) + "\n")

    # ---- 待复核表：更新统一名/选中项 ----
    rhdr, rrows = read_tsv(os.path.join(UNI, "待复核_CG背景.tsv"))
    ridx = {c: i for i, c in enumerate(rhdr)}
    rem_set = set(removed)
    newname_map = dict(renamed)
    out = []
    dropped = 0
    for r in rrows:
        u = r[ridx["统一名"]]
        if u in rem_set:
            dropped += 1
            continue
        if u in newname_map:
            r[ridx["统一名"]] = newname_map[u]
        # 选中项里的 np 引用（miy02a）已由清单更新，这里补注
        out.append(r)
    atomic_write(os.path.join(UNI, "待复核_CG背景.tsv"),
                 "\n".join(["\t".join(rhdr)] + ["\t".join(r) for r in out]) + "\n")

    summary = dict(removed=removed, reselected=reselected,
                   renamed_n=len(renamed), renamed=renamed,
                   review_dropped=dropped,
                   products_after=len(new_rows))
    json.dump(summary, open(os.path.join(WORK, "_pic_rebuild.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: (v if k != "renamed" else len(v)) for k, v in summary.items()},
                     ensure_ascii=False, indent=1))
    print("CG背景 files after:", len(os.listdir(IMGD)))
    print("removed:", removed)
    print("reselected:", reselected)


if __name__ == "__main__":
    main()