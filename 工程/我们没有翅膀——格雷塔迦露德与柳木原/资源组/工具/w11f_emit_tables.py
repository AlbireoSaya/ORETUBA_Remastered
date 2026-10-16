# -*- coding: utf-8 -*-
"""W11f · 产出 门控拆分_目视终裁表.tsv 与 门控未拆候选_W11f.tsv。"""
import os, json

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")


def atomic_write(path, text):
    tmp = path + ".tmp_w11f"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def read_tsv(p):
    with open(p, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


VERDICT = {
    "cin008": ("同一张画的不同裁切", "MAIN(otv 960×540) 与 ALT(ot 800×448) 均为「怒目」眼部特写：瞳孔、眉、头发走向、闪电纹样逐一致，仅取景/纵横比不同"),
    "cin_blk2": ("同一张画的不同裁切", "均为深底中央白色模糊光斑（转场遮罩），斑形与模糊程度一致，仅画幅纵横比不同"),
    "miy02a": ("同一张画的不同裁切", "MAIN(np 1280×720 内 404×664) 与 ALT(ot 381×557)：同姿势（双手胸前交叠）、同表情（闭眼微笑）、同服装（白+粉蝴蝶结系带），仅画幅与裁切不同"),
    "chi01i": ("同一张画的不同裁切", "MAIN(np) 与 ALT(ota 517×600)：同姿势（抱臂）、同表情（叼牙签）、同服装（橙色花纹衬衫），仅裁切/分辨率不同"),
    "lr201e": ("同一张画的不同裁切", "MAIN(np) 与 ALT(ota 536×600)：同角色（戴耳机黑人男性）、同服装（校队夹克＋和平项链）、同姿势（竖拇指）、同表情，仅裁切范围不同"),
    "mis01": ("不同素材（服装不同）", "MAIN(ot)=白色水手裙＋蓝色系带；ALT(ota)=白色冬装外套＋粉格围巾。同一角色的不同服装版本 → 属不同素材"),
    "mis01a": ("不同素材（服装不同）", "同上：MAIN 水手裙 / ALT 冬装外套＋围巾"),
    "mis01b": ("不同素材（服装不同）", "同上；且表情不同（MAIN 睁眼 / ALT 闭眼带音符）"),
    "mis01c": ("不同素材（服装不同）", "同上：MAIN 水手裙闭眼唱歌 / ALT 冬装外套睁眼"),
    "cit001": ("不同素材（语义不同）", "MAIN(otp)=橙发角色立绘（旗袍）；ALT(ota)=文字横幅「がっこう やすみじかん」。归一化键 cit01→cit001 去前导零误并，属不同素材"),
}
_KUR = ("同一张画的不同裁切",
        "MAIN 与 ALT(otp) 为同一角色的同一姿势/服装/表情（黑发校服少年，姿势与表情逐组一致）；"
        "otp 版仅取景更窄（内容宽高比 0.72/0.52 vs 0.79/0.57，差 8.5–8.8%）→ 同一张画的不同裁切")
for _i in range(1, 11):
    _suf = "" if _i == 1 else chr(96 + _i - 1)
    for _f in ("kur01" + _suf, "kur02" + _suf):
        VERDICT[_f] = _KUR


def main():
    # ---- 目视终裁表（30 组 = W11e 的 28 组 + W11f 因 np\pic 并入新增的 chi01i/miy02a）----
    _, chg = read_tsv(os.path.join(UNI, "立绘_选源变更表.tsv"))
    ch = {r[0]: r for r in chg}
    hdr, cur = read_tsv(os.path.join(UNI, "清单_立绘.tsv"))
    ix = {c: i for i, c in enumerate(hdr)}
    cur_by = {r[ix["统一名"]]: r for r in cur}
    _, bak = read_tsv(os.path.join(WORK, "_backup_W11e", "清单_立绘.tsv"))
    bix = {c: i for i, c in enumerate(hdr)}
    bak_by = {r[0]: r for r in bak}
    meta = json.load(open(os.path.join(WORK, "_meta_cache.json"), encoding="utf-8"))
    msz = {(m["src"], m["name"]): "%dx%d" % (m["w"], m["h"]) for m in meta.values()}

    # 30 组的 (stem, alt名, alt 源定位)
    groups = []
    for _, _, _ in ():
        pass
    for r in read_tsv(os.path.join(WORK, "_backup_W11e", "_w11e_拆分明细.tsv"))[1]:
        stem = r[0][:-4]
        for a in r[4].split("、"):
            groups.append((stem, a))
    groups.append(("chi01i", "chi01i_altota.png"))
    groups.append(("miy02a", "miy02a_altot.png"))

    rows = ["统一名\t主产物尺寸\t拆出产物\t拆出产物尺寸\t目视结论\t依据\tW11f处置"]
    for stem, a in groups:
        mp = stem + ".png"
        main_size = cur_by.get(mp, [None] * 3)[ix["尺寸(w,h)"]] if mp in cur_by else "-"
        if a in cur_by:
            asize = cur_by[a][ix["尺寸(w,h)"]]
        elif a in bak_by:
            asize = bak_by[a][bix["尺寸(w,h)"]]
        else:
            asize = {"chi01i_altota.png": msz.get(("ota", "ota_chi01i.png"), "-"),
                     "miy02a_altot.png": msz.get(("ot", "ot_miy02a.png"), "-")}.get(a, "-")
        v, why = VERDICT.get(stem, ("待判", "-"))
        action = "撤销拆分（已合并为单产物）" if v.startswith("同一张画") else "保留拆分"
        rows.append("\t".join([mp, main_size or "-", a, asize or "-", v, why, action]))
    atomic_write(os.path.join(UNI, "门控拆分_目视终裁表.tsv"), "\n".join(rows) + "\n")
    n_merge = sum(1 for r in rows[1:] if r.split("\t")[4].startswith("同一张画"))
    n_keep = sum(1 for r in rows[1:] if r.split("\t")[4].startswith("不同素材"))
    print("目视终裁表:", len(rows) - 1, "行；撤销拆分", n_merge, "；保留拆分", n_keep)

    # ---- 门控未拆候选 ----
    gc = json.load(open(os.path.join(WORK, "_gate_candidates.json"), encoding="utf-8"))
    out = ["类别\t统一名\t候选数\t内容宽高比最大相对差\t候选（源:原名 画布 ar）"]
    for label, key in (("CG背景", "pic_gate"), ("系统UI", "sys_gate")):
        for g in sorted(gc[key], key=lambda x: -x["max_rel"]):
            out.append("\t".join([label, g["stem"] + ".png", str(g["n"]), "%.4f" % g["max_rel"],
                                  " ; ".join(g["cands"])]))
    atomic_write(os.path.join(UNI, "门控未拆候选_W11f.tsv"), "\n".join(out) + "\n")
    print("门控未拆候选:", len(out) - 1, "行")


if __name__ == "__main__":
    main()