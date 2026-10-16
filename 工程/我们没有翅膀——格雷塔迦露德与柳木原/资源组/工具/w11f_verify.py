# -*- coding: utf-8 -*-
"""
W11f · 收口验收自证（8 项） + _最终清单.json
只读产物；输出 JSON 到工作区与 美术统一\\_最终清单.json。
"""
import os, sys, json, random, hashlib, collections

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
UNI = os.path.join(PROJ, "资源组", "美术统一")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")

CATS = {"立绘": "立绘", "CG背景": "CG背景", "系统UI": "系统UI"}
LIST = {"立绘": "清单_立绘.tsv", "CG背景": "清单_CG背景.tsv", "系统UI": "清单_系统UI.tsv"}


def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_tsv(p):
    with open(p, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def main():
    res = {}
    meta = json.load(open(os.path.join(WORK, "_meta_cache.json"), encoding="utf-8"))
    # 源路径 -> md5（用于保真校验）
    srcmd5 = {(m["src"], m["kind"], m["name"]): m["md5"] for m in meta.values()}

    files = {k: sorted(fn for fn in os.listdir(os.path.join(UNI, d)) if fn.lower().endswith(".png"))
             for k, d in CATS.items()}
    lists = {k: read_tsv(os.path.join(UNI, LIST[k])) for k in CATS}

    counts = {k: dict(files=len(files[k]), rows=len(lists[k][1])) for k in CATS}
    res["counts"] = counts
    res["products_total"] = sum(v["files"] for v in counts.values())

    # 唯一名
    res["dup_names"] = {k: [n for n, c in collections.Counter(files[k]).items() if c > 1] for k in CATS}

    # Σ候选数
    def sum_cand(k):
        hdr, rows = lists[k]
        i = hdr.index("组内候选数")
        return sum(int(r[i]) for r in rows)
    res["sum_candidates"] = {k: sum_cand(k) for k in CATS}
    res["sum_candidates_total"] = sum(res["sum_candidates"].values())

    # 撞名
    res["collision_立绘_CG背景"] = sorted(set(files["立绘"]) & set(files["CG背景"]))
    res["collision_立绘_系统UI"] = len(set(files["立绘"]) & set(files["系统UI"]))
    res["collision_CG背景_系统UI"] = len(set(files["CG背景"]) & set(files["系统UI"]))

    # 文件 vs 清单 一致性
    for k in CATS:
        hdr, rows = lists[k]
        i = hdr.index("统一名")
        names = {r[i] for r in rows}
        res["manifest_vs_disk_%s" % k] = dict(
            only_disk=len(set(files[k]) - names), only_list=len(names - set(files[k])))

    # 原字节保真：每类随机 20（以清单的 选中源/选中原名/尺寸 定位源）
    rng = random.Random(20260919)
    fid = {}
    for k in CATS:
        hdr, rows = lists[k]
        ix = {c: i for i, c in enumerate(hdr)}
        ok = bad = 0
        detail = []
        sample = rng.sample(rows, min(20, len(rows)))
        for r in sample:
            uname = r[ix["统一名"]]
            src = r[ix["选中源"]]
            orig = r[ix["选中原名"]]
            kind = "pic" if k == "CG背景" else ("chr" if k == "立绘" else None)
            cand = []
            for nm in (orig, orig + ".png"):
                if kind:
                    cand.append((src, kind, nm))
                if k == "系统UI":
                    cand += [(src, "sys", nm), (src, "etc", nm)]
                if k == "立绘":
                    cand.append((src, "pic", nm))     # np\pic 10 个
            m = None
            for c in cand:
                if c in srcmd5:
                    m = srcmd5[c]
                    break
            if m is None:
                detail.append((uname, "NO_SRC_META")); bad += 1; continue
            got = md5f(os.path.join(UNI, CATS[k], uname))
            if got == m:
                ok += 1
            else:
                bad += 1; detail.append((uname, "MISMATCH"))
        fid[k] = dict(ok=ok, bad=bad, detail=detail, sample=[r[ix["统一名"]] for r in sample])
    res["byte_fidelity"] = fid

    # 分类分布 / 源占比
    dist = {}
    for k in CATS:
        hdr, rows = lists[k]
        ix = {c: i for i, c in enumerate(hdr)}
        dist[k] = dict(
            by_source=dict(collections.Counter(r[ix["选中源"]] for r in rows)),
            by_category=dict(collections.Counter(r[ix["类别"]] for r in rows)),
            by_class=dict(collections.Counter(r[ix["分类"]] for r in rows)))
    res["distribution"] = dist

    json.dump(res, open(os.path.join(WORK, "_验收_W11f.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # _最终清单.json
    final = {
        "立绘": counts["立绘"]["files"],
        "CG背景": counts["CG背景"]["files"],
        "系统UI": counts["系统UI"]["files"],
        "合计": res["products_total"],
        "各源占比": {k: dist[k]["by_source"] for k in CATS},
        "分类分布": {k: dist[k]["by_category"] for k in CATS},
        "来源候选总数": res["sum_candidates"],
        "来源候选合计": res["sum_candidates_total"],
        "口径": ("立绘=chr 3741 + np\\pic 并入 10 = 3751；CG背景=pic 1920 − np\\pic 10 = 1910；"
                 "系统UI=sys 2237 + etc 124 = 2361；合计 8022（与 W11d 口径一致，仅 10 个在两类间转移）"),
        "生成": "W11f / 2026-09-19",
    }
    tmp = os.path.join(UNI, "_最终清单.json.tmp_w11f")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(UNI, "_最终清单.json"))

    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()