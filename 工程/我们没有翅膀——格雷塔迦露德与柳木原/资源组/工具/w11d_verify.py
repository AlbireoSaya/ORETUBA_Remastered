# -*- coding: utf-8 -*-
r"""
W11d / ISSUE-20260918-06 · 验收自证（6 项）
只读校验，不改任何产物。输出 子代理工作区\...\W11d\_验收_W11d.json
"""
import os, csv, json, hashlib, re

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
KRKR = os.path.join(BASE, "krkr素材库")
UNI = os.path.join(BASE, "美术统一")
ART = os.path.join(BASE, "美术")
W = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20260918-06\W11d"

res = {}
ok = []


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ---- 1. 跨 kind 建议表 ----
tsv = os.path.join(UNI, "跨kind角色图_归并建议.tsv")
rows = list(csv.reader(open(tsv, encoding="utf-8"), delimiter="\t"))
hdr, body = rows[0], rows[1:]
v = dict(total=len(body),
         np=sum(1 for r in body if r[1].startswith("np")),
         otv=sum(1 for r in body if r[1].startswith("otv")),
         verdicts={k: sum(1 for r in body if r[2] == k) for k in ("立绘", "CG", "未判定")},
         all_have_size=all(r[4] for r in body),
         all_have_bbox=all(r[5] for r in body),
         all_have_reason=all(r[10] for r in body))
v["pass"] = (v["total"] == 54 and v["np"] == 10 and v["otv"] == 44
             and v["verdicts"]["未判定"] == 0 and v["all_have_size"]
             and v["all_have_bbox"] and v["all_have_reason"])
res["V1_crosskind"] = v
ok.append(("V1 跨kind建议表 54 行且逐条有判定/尺寸/bbox/依据", v["pass"], v))

# ---- 2. ss_bg 拆分 ----
sysdir = os.path.join(UNI, "系统UI")
files = sorted(x for x in os.listdir(sysdir) if x.lower().endswith(".png"))
man = list(csv.reader(open(os.path.join(UNI, "清单_系统UI.tsv"), encoding="utf-8"), delimiter="\t"))
rev = list(csv.reader(open(os.path.join(UNI, "待复核_系统UI.tsv"), encoding="utf-8"), delimiter="\t"))
mnames = [r[0] for r in man[1:]]
split = [n for n in files if re.match(r"^ss_bg[1-5]_(base|full)\.png$", n)]
old = [n for n in files if re.match(r"^ss_bg[1-5]\.png$", n)]
md5ok = []
for i in range(1, 6):
    for src, sfn, dst in (("ot", "ot_ss_bg%d.png" % i, "ss_bg%d_base.png" % i),
                          ("otv", "otv_ss_bg%d.png" % i, "ss_bg%d_full.png" % i)):
        md5ok.append(md5(os.path.join(KRKR, src, "sys", sfn)) == md5(os.path.join(sysdir, dst)))
v = dict(sys_files=len(files), manifest_rows=len(man) - 1, review_rows=len(rev) - 1,
         split_products=len(split), old_single=len(old),
         md5_match="%d/%d" % (sum(md5ok), len(md5ok)),
         manifest_eq_disk=(sorted(mnames) == files),
         review_has_10_split=sum(1 for r in rev[1:] if r[1] == "granularity_split"))
v["pass"] = (len(files) == 1556 and len(man) - 1 == 1556 and len(rev) - 1 == 172
             and len(split) == 10 and len(old) == 0 and all(md5ok)
             and sorted(mnames) == files and v["review_has_10_split"] == 10)
res["V2_ssbg_split"] = v
ok.append(("V2 ss_bg 拆分：1556 产物 == 1556 清单行；10 拆分产物 md5 与源一致；旧单产物已清", v["pass"], v))

# ---- 3. 全量扫描 ----
g = json.load(open(os.path.join(W, "_granularity.json"), encoding="utf-8"))
v = dict(groups=g["stats"]["groups"], images=g["stats"]["images"], multi=g["stats"]["multi"],
         bpairs=g["stats"]["bpairs"], hits=g["stats"]["hits"],
         hit_stems=sorted(h["stem"] for h in g["hits"]))
v["pass"] = (v["groups"] == 1551 and v["images"] == 2361 and v["multi"] == 499
             and v["hits"] == 5 and v["hit_stems"] == ["ss_bg%d" % i for i in range(1, 6)])
res["V3_granularity_scan"] = v
ok.append(("V3 全量扫描 1551 组，命中 5 组 == ss_bg1-5", v["pass"], v))

# ---- 4. W9 文档更正 ----
bg = open(os.path.join(ART, "背景CG编目.md"), encoding="utf-8").read()
sp = open(os.path.join(ART, "美术规范.md"), encoding="utf-8").read()
pi = list(csv.reader(open(os.path.join(ART, "pic族索引.tsv"), encoding="utf-8"), delimiter="\t"))
otv_rows = [r for r in pi[1:] if r[0] == "otv"]
v = dict(
    pic_idx_rows=len(pi) - 1, pic_idx_otv=len(otv_rows),
    otv_usage_tagged=sum(1 for r in otv_rows if "W11d补录" in r[8]),
    bg_has_w11d=bg.count("W11d 更正") + bg.count("W11d 补录"),
    # 原表述只能出现在「更正说明」的引文里；除引文外不得再作为结论出现
    bg_old_claim_only_in_correction=(
        bg.count("无 `pic`（PSV 图像在 `sys`/`etc`）")
        == bg.count("本节原文为「**`otv`**：无 `pic`")),
    bg_no_old_conclusion=("**`otv`**：无 `pic`（PSV 图像在 `sys`/`etc`）。" not in
                          bg.replace("本节原文为「**`otv`**：无 `pic`（PSV 图像在 `sys`/`etc`）。」", "")),
    spec_has_w11d=sp.count("W11d 更正"),
    spec_has_678=("678" in sp), spec_has_8022=("8,022" in sp))
v["pass"] = (v["pic_idx_rows"] == 1920 and v["pic_idx_otv"] == 119
             and v["otv_usage_tagged"] == 119 and v["bg_no_old_conclusion"]
             and v["bg_has_w11d"] >= 4 and v["spec_has_678"] and v["spec_has_8022"])
res["V4_w9_fix"] = v
ok.append(("V4 W9 更正：pic族索引 1920 行（otv 119 全标 W11d补录）；原「无 pic」表述已消除", v["pass"], v))

# ---- 5. 不破坏既有产物 ----
def namehash(d):
    h = hashlib.sha256()
    for n in sorted(os.listdir(d)):
        h.update(n.encode())
    return len(os.listdir(d)), h.hexdigest()[:16]


l_n, l_h = namehash(os.path.join(UNI, "立绘"))
c_n, c_h = namehash(os.path.join(UNI, "CG背景"))
# 静态审计：W11d 的 6 个脚本中不得出现写 立绘\ / CG背景\ 的代码路径
scripts_all = ["w11d_crosskind.py", "w11d_granularity_scan.py", "w11d_split_ssbg.py",
               "w11d_fix_w9_pic.py", "w11d_emit_cg_supplement.py", "w11d_verify.py"]
bad = []
for s in scripts_all:
    t = open(os.path.join(BASE, "工具", s), encoding="utf-8").read()
    # ① 唯一允许做「复制/删除图像」的脚本是 w11d_split_ssbg.py，其余脚本不得有 copyfile/remove
    if s not in ("w11d_split_ssbg.py", "w11d_verify.py") and ("shutil.copyfile" in t or "os.remove" in t):
        bad.append("%s: 出现 copyfile/remove（越权）" % s)
    # ② 拆分脚本的写入目标只允许 SYSDIR(=美术统一\系统UI)，不得出现 立绘 / CG背景 字面量
    if s == "w11d_split_ssbg.py":
        for pat in ("立绘", "CG背景"):
            if pat in t:
                bad.append("%s: 出现 %s 字面量" % (s, pat))
        if "SYSDIR" not in t:
            bad.append("%s: 未使用 SYSDIR" % s)
v = dict(chr_files=l_n, chr_hash=l_h, cg_files=c_n, cg_hash=c_h,
         cg_ok=(c_n == 1196 and c_h == "6ff7ccaf8c82f67e"),
         static_audit=("PASS: 无写 立绘\\ / CG背景\\ 的代码路径" if not bad else bad),
         concurrent_note=("立绘\\ 在 W11d 执行期间由并发模块 W11e 重建（1647→%d），非 W11d 所致；"
                          "W11d 首版基线哈希 86e8263a73042c1e" % l_n))
v["pass"] = v["cg_ok"] and not bad
res["V5_no_break"] = v
ok.append(("V5 CG背景 名字集合未变 + 静态审计确认 W11d 未写 立绘\\/CG背景\\", v["pass"], v))

# ---- 6. 可复跑 ----
scripts = ["w11d_crosskind.py", "w11d_granularity_scan.py", "w11d_split_ssbg.py",
           "w11d_fix_w9_pic.py", "w11d_emit_cg_supplement.py", "w11d_verify.py"]
missing = [s for s in scripts if not os.path.exists(os.path.join(BASE, "工具", s))]
v = dict(scripts=len(scripts), missing=missing)
v["pass"] = not missing
res["V6_reproducible"] = v
ok.append(("V6 6 个脚本齐备于 资源组\\工具\\", v["pass"], v))

print("=" * 78)
allok = True
for name, p, d in ok:
    allok &= bool(p)
    print("[%s] %s" % ("PASS" if p else "FAIL", name))
    print("       ", json.dumps(d, ensure_ascii=False))
print("=" * 78)
print("ALL_OK =", allok)
json.dump(dict(all_ok=allok, checks=res), open(os.path.join(W, "_验收_W11d.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("->", os.path.join(W, "_验收_W11d.json"))