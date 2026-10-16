# -*- coding: utf-8 -*-
"""W11g · 交付前自检（8 项：V1_交付清单行数 … V8_判读类别schema）。只读，输出 JSON + 摘要。"""
import os, sys, json, hashlib, random
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
SRC = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g"))
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")

CATS = {"立绘": "清单_立绘.tsv", "CG背景": "清单_CG背景.tsv", "系统UI": "清单_系统UI.tsv"}
SPLITS = [("tl_01", "otp", "otp_tl_01.png"), ("tl_02", "otp", "otp_tl_02.png"), ("tl_03", "otp", "otp_tl_03.png"),
          ("tl_04", "otp", "otp_tl_04.png"), ("tl_new", "otp", "otp_tl_new.png"), ("tl_logo", "ota", "ota_tl_logo.png"),
          ("ec2_bg", "otp", "otp_ec2_bg.png"), ("ec3_bg", "otp", "otp_ec3_bg.png"),
          ("gl_music", "ot", "ot_gl_music.png"), ("gl_chr2", "ot", "ot_gl_chr2.png"),
          ("gl_chrbg", "ot", "ot_gl_chrbg.png"), ("gl_chr5", "ot", "ot_gl_chr5.png"), ("gl_chr4", "ot", "ot_gl_chr4.png")]


def read_tsv(p):
    lines = [ln.rstrip("\n") for ln in open(p, encoding="utf-8") if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


R = {}
# 1. 交付清单 == 三份清单之和
h, drow = read_tsv(os.path.join(UNI, "交付清单.tsv"))
sums = {}
for c, fn in CATS.items():
    _, rr = read_tsv(os.path.join(UNI, fn))
    sums[c] = len(rr)
R["V1_交付清单行数"] = {"交付清单": len(drow), "三清单之和": sum(sums.values()), "分类": sums,
                       "ok": len(drow) == sum(sums.values())}

# 2. 各目录文件数 == 清单行数；统一名唯一
R["V2_磁盘与清单一致"] = {}
for c, fn in CATS.items():
    _, rr = read_tsv(os.path.join(UNI, fn))
    names = [r[0] for r in rr]
    disk = sorted(x for x in os.listdir(os.path.join(UNI, c)) if x.lower().endswith(".png"))
    R["V2_磁盘与清单一致"][c] = {"清单": len(names), "磁盘": len(disk), "唯一名": len(set(names)),
                                 "重复名": [n for n in set(names) if names.count(n) > 1],
                                 "仅在盘": sorted(set(disk) - set(names)), "仅在单": sorted(set(names) - set(disk))}
    R["V2_磁盘与清单一致"][c]["ok"] = (len(names) == len(disk) == len(set(names))
                                       and not R["V2_磁盘与清单一致"][c]["仅在盘"]
                                       and not R["V2_磁盘与清单一致"][c]["仅在单"])

# 3. 跨目录同名
sets = {}
for c in CATS:
    sets[c] = set(x for x in os.listdir(os.path.join(UNI, c)) if x.lower().endswith(".png"))
inter = {("立绘", "CG背景"): sorted(sets["立绘"] & sets["CG背景"]),
         ("立绘", "系统UI"): sorted(sets["立绘"] & sets["系统UI"]),
         ("CG背景", "系统UI"): sorted(sets["CG背景"] & sets["系统UI"]),
         ("三者"): sorted(sets["立绘"] & sets["CG背景"] & sets["系统UI"])}
R["V3_跨目录同名"] = {("%s∩%s" % k if isinstance(k, tuple) else k): {"n": len(v), "样本": v[:12]} for k, v in inter.items()}

# 4. 13 个新拆产物 md5 == 源
bad = []
for stem, s, f in SPLITS:
    a = os.path.join(UNI, "系统UI", "%s_alt%s.png" % (stem, s))
    b = os.path.join(SRC, s, "sys", f)
    if not os.path.isfile(b):
        b = os.path.join(SRC, s, "etc", f)
    if not os.path.isfile(a) or not os.path.isfile(b) or md5(a) != md5(b):
        bad.append(stem)
R["V4_拆分产物原字节"] = {"检查": len(SPLITS), "不一致": bad, "ok": not bad}

# 5. 总量守恒 8022（来自 _最终清单.json，来源候选未变）
fin = json.load(open(os.path.join(UNI, "_最终清单.json"), encoding="utf-8"))
R["V5_来源候选守恒"] = {"来源候选合计": fin["来源候选合计"], "ok": fin["来源候选合计"] == 8022}

# 6. 38 组终裁表完整性
h38, r38 = read_tsv(os.path.join(UNI, "门控_38组目视终裁.tsv"))
empty = [r[0] for r in r38 if len(r) < 7 or len(r[5].strip()) < 20]
R["V6_38组终裁表"] = {"行数": len(r38), "依据过短行": empty,
                      "拆": sum(1 for r in r38 if r[4] == "拆"), "不拆": sum(1 for r in r38 if r[4] == "不拆"),
                      "ok": len(r38) == 38 and not empty}

# 7. 随机 20 个产物 md5 == 源（用清单的 选中源/选中原名 反查）
random.seed(20260919)
R["V7_原字节抽检"] = {}
for c, fn in CATS.items():
    _, rr = read_tsv(os.path.join(UNI, fn))
    hdr, _ = read_tsv(os.path.join(UNI, fn))
    ix = {x: i for i, x in enumerate(hdr)}
    pick = random.sample(rr, 20)
    n = 0
    fails = []
    for r in pick:
        name = r[ix["统一名"]]
        s = r[ix["选中源"]]
        onm = r[ix["选中原名"]]
        cand = None
        order = {"立绘": ("chr", "pic", "sys", "etc", "movie"),
                 "CG背景": ("pic", "chr", "sys", "etc", "movie"),
                 "系统UI": ("sys", "etc", "chr", "pic", "movie")}[c]
        for cand_name in (onm, onm + ".png"):
            for sub in order:
                p = os.path.join(SRC, s, sub, cand_name)
                if os.path.isfile(p):
                    cand = p
                    break
            if cand:
                break
        if cand is None:  # glob 兜底
            for dp, dn, fn in os.walk(os.path.join(SRC, s)):
                if onm in fn or onm + ".png" in fn:
                    cand = os.path.join(dp, onm if onm in fn else onm + ".png")
                    break
        if cand and md5(os.path.join(UNI, c, name)) == md5(cand):
            n += 1
        else:
            fails.append((name, s, onm, "no-src" if cand is None else "md5-diff"))
    R["V7_原字节抽检"][c] = "%d/20" % n
    if fails:
        R["V7_原字节抽检"][c + "_fail"] = fails
R["V7_原字节抽检"]["ok"] = all(v == "20/20" for k, v in R["V7_原字节抽检"].items() if k != "ok")

# 8. schema：分表 `类别` 为纯大类、`判读类别` 为子分类；总表 `判读类别` 与分表逐类一致
SUBCAT = {"立绘": {"立绘", "头像", "未识别"}, "CG背景": {"CG", "背景", "未判定", "其他"},
          "系统UI": {"其他", "菜单", "标题", "存档", "转场遮罩", "消息窗", "图标"}}
h, drow = read_tsv(os.path.join(UNI, "交付清单.tsv"))
tot = {}
for r in drow:
    tot.setdefault(r[0], {})
    tot[r[0]][r[1]] = tot[r[0]].get(r[1], 0) + 1
sub_ok, detail = True, {}
for c, fn in CATS.items():
    sh, rr = read_tsv(os.path.join(UNI, fn))
    six = {x: i for i, x in enumerate(sh)}
    if "判读类别" not in six:
        sub_ok = False
        detail[c] = {"ok": False, "原因": "分表缺 `判读类别` 列（未跑 w11g_fix_schema.py）"}
        continue
    cats = sorted({r[six["类别"]] for r in rr})
    dist = {}
    for r in rr:
        dist[r[six["判读类别"]]] = dist.get(r[six["判读类别"]], 0) + 1
    ok = (cats == [c] and set(dist) == SUBCAT[c] and dist == tot.get(c, {}))
    sub_ok &= ok
    detail[c] = {"ok": ok, "分表类别": cats, "分表判读类别": dist, "总表判读类别": tot.get(c, {})}
R["V8_判读类别schema"] = {"ok": sub_ok, "明细": detail, "总表列": h,
                          "说明": "分表 `类别`=纯大类、`判读类别`=子分类；总表 `判读类别` 与分表逐类一致"}

R["_all_ok"] = all(v.get("ok", True) for v in R.values() if isinstance(v, dict))
p = os.path.join(WORK, "_验收_W11g.json")
tmp = p + ".tmp"
json.dump(R, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
os.replace(tmp, p)
for k, v in R.items():
    print(k, "->", v)
print("\nALL_OK =", R["_all_ok"])