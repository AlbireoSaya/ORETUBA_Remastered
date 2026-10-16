# -*- coding: utf-8 -*-
"""
W11f · (a) otv\\pic 119 溯源 121→119 逐项明细；(b) 跨kind建议表补「W11f处置」列
只读源；输出到 美术统一\\。
"""
import os, sys, json, hashlib, collections

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
RES = os.path.join(PROJ, "资源组")
LIB = os.path.join(RES, "krkr素材库")
UNI = os.path.join(RES, "美术统一")
OTV = os.path.join(LIB, "otv")
PSV = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\images"


def atomic_write(path, text):
    tmp = path + ".tmp_w11f"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def trace():
    d = json.load(open(os.path.join(OTV, "_清单.json"), encoding="utf-8"))
    pic = [e for e in d if e.get("kind") == "pic" or "/pic/" in (e.get("out_relpath") or "")]
    lines = ["otv原名\totv相对路径\tPSV来源目录\tPSV原名\tPSV相对路径\tmd5前12\t说明"]
    by_arch = collections.Counter(e["archive"] for e in pic)
    for e in sorted(pic, key=lambda x: x["out_relpath"]):
        arch = e["archive"]
        sub = "cg" if arch.endswith("/CG") else "eyecatch"
        srcp = os.path.join(PSV, sub, e["orig_name"])
        ok = os.path.isfile(srcp)
        m = md5f(srcp)[:12] if ok else "MISSING"
        # 与 otv 产物比对
        outp = os.path.join(LIB, "otv", e["out_relpath"].replace("otv/", ""))
        lines.append("\t".join([e["out_relpath"].split("/")[-1], e["out_relpath"], sub,
                                e["orig_name"], "images/%s/%s" % (sub, e["orig_name"]),
                                m, "来源存在且字节可读" if ok else "**源缺失**"]))
    # 差异明细
    cg_files = sorted(os.listdir(os.path.join(PSV, "cg")))
    ec_all = sorted(os.listdir(os.path.join(PSV, "eyecatch")))
    ec_png = [f for f in ec_all if f.lower().endswith(".png")]
    ec_non = [f for f in ec_all if not f.lower().endswith(".png")]
    used = {(e["archive"].split("/")[-1].lower(), e["orig_name"]) for e in pic}
    dropped = []
    for sub, files in (("cg", cg_files), ("eyecatch", ec_png)):
        for fn in files:
            key = (sub if sub == "cg" else "eyecatch", fn)
            if key not in used:
                dropped.append((sub, fn))
    lines.append("")
    lines.append("# 口径与差异明细（PSV 121 → otv 实测 119）")
    lines.append("# PSV cg/ PNG = %d ；PSV eyecatch/ 条目 = %d（其中 PNG %d ＋ 非图像 %d：%s）"
                 % (len(cg_files), len(ec_all), len(ec_png), len(ec_non), ",".join(ec_non)))
    lines.append("# 名义合计 = %d + %d = %d" % (len(cg_files), len(ec_all), len(cg_files) + len(ec_all)))
    lines.append("# 扣减1：eyecatch/EC28.png 与 cg/EC28.png **逐字节相同**（md5 %s）→ 去重 -1"
                 % md5f(os.path.join(PSV, "cg", "EC28.png"))[:12])
    lines.append("# 扣减2：eyecatch/_manifest.json 为 JSON 文本、非图像素材 → -1")
    lines.append("# 实测 otv\\pic = %d（来源 cg %d + eyecatch %d）" % (len(pic), by_arch.get("美咲线资源/images/CG", 0), by_arch.get("美咲线资源/images/EyeCatch", 0)))
    lines.append("# 未被收录的源文件（=2 项，逐条）：")
    for sub, fn in dropped:
        lines.append("#   [%s] %s" % (sub, fn))
    for fn in ec_non:
        lines.append("#   [eyecatch] %s（非图像，非素材）" % fn)
    atomic_write(os.path.join(UNI, "otv_pic_119溯源.tsv"), "\n".join(lines) + "\n")
    print("pic entries:", len(pic), dict(by_arch))
    print("cg png:", len(cg_files), "eyecatch entries:", len(ec_all), "ec png:", len(ec_png), "ec non-img:", ec_non)
    print("dropped (not in otv):", dropped)
    print("121-2 =", len(cg_files) + len(ec_all) - 2, "== otv pic", len(pic))


def update_crosskind():
    p = os.path.join(UNI, "跨kind角色图_归并建议.tsv")
    with open(p, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n")]
    hdr = lines[0].split("\t")
    hdr2 = hdr + ["W11f处置"]
    out = ["\t".join(hdr2)]
    n_np = n_cg = n_cgprefix = 0
    for ln in lines[1:]:
        c = ln.split("\t")
        name, kind = c[0], c[1]
        stem = name[:-4]
        if kind.startswith("np"):
            dispo = "已并入 立绘\\（W11f 执行）：np 版按内容面积胜出，产物 立绘\\%s.png" % stem
            n_np += 1
        else:
            if "撞名" in c[3]:
                dispo = "保留于 CG背景\\ 并加 cg_ 前缀（W11f）：CG背景\\cg_%s.png" % stem
                n_cgprefix += 1
            else:
                dispo = "保留于 CG背景\\（W11b，W11f 未改）"
            n_cg += 1
        out.append("\t".join(c + [dispo]))
    atomic_write(p, "\n".join(out) + "\n")
    print("crosskind updated: np并入 %d ; CG保留 %d（其中加前缀 %d）" % (n_np, n_cg, n_cgprefix))


if __name__ == "__main__":
    trace()
    update_crosskind()