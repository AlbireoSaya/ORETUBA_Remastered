# -*- coding: utf-8 -*-
"""W11g · 执行 38 组目视终裁中判定为「拆」的组：
把「不同内容」的那一版按 <名>_alt<源>.png 独立成产物，并同步 清单_系统UI / 待复核_系统UI。
- 原字节复制（shutil.copyfile），无像素改动
- 原子写；先备份原清单到 子代理工作区\ISSUE-20260918-06\W11g\_backup_W11g\
- 幂等：已存在同名产物则跳过复制，但清单行只加一次
"""
import os, sys, shutil
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
SRC = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g"))
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")

# (stem, alt_src, alt_src_fname, 目视理由)
SPLITS = [
    ("tl_01",    "otp", "otp_tl_01.png",    "ota=「その後のタカシ」/ otp=「ある日の明日香」，文案不同（不同剧集入口）"),
    ("tl_02",    "otp", "otp_tl_02.png",    "ota=「その後の鷲介」/ otp=「ある日の京」，文案不同"),
    ("tl_03",    "otp", "otp_tl_03.png",    "ota=「その後の隼人」/ otp=「ある日の美咲」，文案不同"),
    ("tl_04",    "otp", "otp_tl_04.png",    "ota=「その後のヨージ」/ otp=「千歳 鷲介編 プロローグ」，文案不同"),
    ("tl_new",   "otp", "otp_tl_new.png",   "ota=「New!」含感叹号 / otp=「New」无感叹号，文案不同"),
    ("tl_logo",  "ota", "ota_tl_logo.png",  "ota=「After Story」LOGO / otp=「～Prelude～」LOGO，不同作品的 LOGO"),
    ("ec2_bg",   "otp", "otp_ec2_bg.png",   "otp=暖色餐厅店面「Alexander Restaurant」街景，与 ot/ota/otv 的钢笔章卡完全不同"),
    ("ec3_bg",   "otp", "otp_ec3_bg.png",   "otp=夜晚霓虹街道（剧场前），与 ot/ota/otv 的安全帽章卡完全不同"),
    ("gl_music", "ot",  "ot_gl_music.png",  "ot=「音楽鑑賞 / music」/ ota=「AfterStory 音楽 / after story music」，文案不同"),
    ("gl_chr2",  "ot",  "ot_gl_chr2.png",   "ot=「山科 京 / yamashina miyako」/ ota=「玉泉 日和子 / tamaizumi hiyoko」，不同角色"),
    ("gl_chrbg", "ot",  "ot_gl_chrbg.png",  "ot=「背景 / background」/ ota=「AfterStory 背景 / after story back」，文案不同"),
    ("gl_chr5",  "ot",  "ot_gl_chr5.png",   "ot=「羽田 小鳩 / haneda kobato」/ ota=「その他 / others」，不同条目"),
    ("gl_chr4",  "ot",  "ot_gl_chr4.png",   "ot=「鳳 鳴 / ootori naru」/ ota=「羽田 小鳩 / haneda kobato」，不同角色"),
]


def atomic_write(path, text):
    tmp = path + ".tmp_w11g"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def read_tsv(p):
    lines = [ln.rstrip("\n") for ln in open(p, encoding="utf-8") if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def find_src(src, fname):
    for sub in ("sys", "etc", "pic", "chr"):
        p = os.path.join(SRC, src, sub, fname)
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(fname)


def main():
    bk = os.path.join(WORK, "_backup_W11g")
    os.makedirs(bk, exist_ok=True)
    cl = os.path.join(UNI, "清单_系统UI.tsv")
    rv = os.path.join(UNI, "待复核_系统UI.tsv")
    for f in (cl, rv):
        shutil.copyfile(f, os.path.join(bk, os.path.basename(f)))

    hdr, rows = read_tsv(cl)
    ix = {c: i for i, c in enumerate(hdr)}
    by = {r[ix["统一名"]]: r for r in rows}
    newrows, detail = [], ["统一名\t主产物\t主产物源\t拆出产物\t拆出产物源\t目视理由"]
    for stem, asrc, afname, why in SPLITS:
        main_name = stem + ".png"
        m = by[main_name]
        alt_name = "%s_alt%s.png" % (stem, asrc)
        dst = os.path.join(UNI, "系统UI", alt_name)
        sp = find_src(asrc, afname)
        if not os.path.isfile(dst):
            shutil.copyfile(sp, dst)
        im = Image.open(dst)
        mode = im.mode
        b = os.path.getsize(dst)
        if alt_name not in by:
            row = [alt_name, m[ix["类别"]], "%dx%d" % im.size, mode, str(b), asrc, afname, "1",
                   "diff_res_diff_drawing", "启发式",
                   "W11g 目视终裁拆分：%s；与 %s 非同一素材，独立产物" % (why, main_name)]
            newrows.append(row)
            by[alt_name] = row
        # 主产物理由追加说明
        if "W11g" not in m[ix["理由"]]:
            m[ix["理由"]] = m[ix["理由"]] + "；W11g 目视终裁：已拆出 %s（不同内容）" % alt_name
        detail.append("\t".join([main_name, m[ix["选中原名"]], m[ix["选中源"]], alt_name, afname, why]))
        print("拆出 %-20s <- %s/%s  %s" % (alt_name, asrc, afname, im.size))

    allrows = rows + newrows
    atomic_write(cl, "\t".join(hdr) + "\n" + "\n".join("\t".join(r) for r in allrows) + "\n")
    atomic_write(os.path.join(UNI, "_w11g_拆分明细.tsv"), "\n".join(detail) + "\n")

    # ---- 待复核：主产物疑点更新 + 新增 alt 行 ----
    h2, rows2 = read_tsv(rv)
    ix2 = {c: i for i, c in enumerate(h2)}
    by2 = {r[0]: r for r in rows2}
    split_stems = {s for s, _, _, _ in SPLITS}
    added = []
    for r in rows2:
        stem = r[0][:-4]
        if stem in split_stems and not r[0].endswith("_alt"):
            r[ix2["分类"]] = "diff_res_diff_drawing"
            r[ix2["疑点"]] = "W11g 目视终裁：**非同一素材**，已拆出独立产物（不同内容/文案），见 门控_38组目视终裁.tsv"
    for stem, asrc, afname, why in SPLITS:
        alt_name = "%s_alt%s.png" % (stem, asrc)
        if alt_name in by2:
            continue
        main = by[stem + ".png"]
        im = Image.open(os.path.join(UNI, "系统UI", alt_name))
        import hashlib
        md5 = hashlib.md5(open(os.path.join(UNI, "系统UI", alt_name), "rb").read()).hexdigest()[:8]
        r = [alt_name, "diff_res_diff_drawing",
             "%s:%s %dx%d md5=%s" % (asrc, afname, im.size[0], im.size[1], md5),
             "%s:%s" % (asrc, afname), "W11g 目视终裁：独立产物（%s）" % why,
             "W11g_拆分_alt：与 %s 非同一素材，已拆为独立产物" % (stem + ".png")]
        rows2.append(r)
        added.append(alt_name)
    atomic_write(rv, "\t".join(h2) + "\n" + "\n".join("\t".join(r) for r in rows2) + "\n")
    print("清单_系统UI: %d -> %d 行" % (len(rows), len(allrows)))
    print("待复核_系统UI: %d -> %d 行 (新增 %d)" % (len(by2) and len(rows2) - len(added), len(rows2), len(added)))


if __name__ == "__main__":
    main()