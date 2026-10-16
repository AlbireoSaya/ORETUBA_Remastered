# -*- coding: utf-8 -*-
"""W11g · 产出 交付统计.md（三类产物数/来源候选/节省/选源分布/分类分布/统一前后对比）。"""
import os, sys, json
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")
CATS = [("立绘", "清单_立绘.tsv"), ("CG背景", "清单_CG背景.tsv"), ("系统UI", "清单_系统UI.tsv")]
fin = json.load(open(os.path.join(UNI, "_最终清单.json"), encoding="utf-8"))


def read_tsv(p):
    lines = [ln.rstrip("\n") for ln in open(p, encoding="utf-8") if ln.strip("\n") != ""]
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def atomic_write(path, text):
    tmp = path + ".tmp_w11g"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


L = []
prod, cand, src_dist, cls_dist = {}, {}, {}, {}
for c, fn in CATS:
    hdr, rr = read_tsv(os.path.join(UNI, fn))
    ix = {x: i for i, x in enumerate(hdr)}
    prod[c] = len(rr)
    cand[c] = fin["来源候选总数"][c]
    src_dist[c] = Counter(r[ix["选中源"]] for r in rr)
    cls_dist[c] = Counter(r[ix["分类"]] for r in rr)
tot_p, tot_c = sum(prod.values()), sum(cand.values())

L.append("# W11g · 美术统一最终交付统计\n")
L.append("> Issue `ISSUE-20260918-06` ｜ 模块 W11g ｜ 2026-09-19 ｜ 依据 `交付清单.tsv`（程序化合并三份 `清单_*.tsv`）\n")
L.append("## 一、三类产物与来源候选\n")
L.append("| 类别 | 产物数（去重后） | 来源候选数（去重前） | 去重率 | 选源分布 |")
L.append("| --- | ---: | ---: | ---: | --- |")
for c, _ in CATS:
    L.append("| **%s** | **%d** | %d | %.1f%% | %s |" % (
        c, prod[c], cand[c], 100.0 * (1 - prod[c] / cand[c]),
        " / ".join("%s %d" % (k, v) for k, v in src_dist[c].most_common())))
L.append("| **合计** | **%d** | **%d** | **%.1f%%** | — |" % (tot_p, tot_c, 100.0 * (1 - tot_p / tot_c)))

L.append("\n## 二、与统一前的对比（六源原始素材 → 统一产物）\n")
L.append("| 项 | 统一前 | 统一后（W11g 交付） |")
L.append("| --- | ---: | ---: |")
L.append("| 图像文件总数 | **8,022**（六源去重前） | **%d**（三类统一产物） |" % tot_p)
L.append("| 去重/归并节省 | — | **%d** 个（%.1f%%） |" % (tot_c - tot_p, 100.0 * (1 - tot_p / tot_c)))
L.append("| 立绘 | 3,751 | %d |" % prod["立绘"])
L.append("| CG背景 | 1,910 | %d |" % prod["CG背景"])
L.append("| 系统UI | 2,361 | %d |" % prod["系统UI"])
L.append("\n> 注：W11f 收口时三类合计为 **4,395**；W11g 对 38 组非 4:3/16:9 门控候选做目视终裁，")
L.append("> 其中 **19 组判为「拆」**——13 组新增 `_alt` 独立产物（+13），5 组 `ss_bg*` 与 1 组 `miy02a` 此前已分离（不新增）。")
L.append("> 故产物数 **4,395 → 4,408**；来源候选总数 **8,022 不变**（拆分不改变输入文件数）。\n")

L.append("## 三、分类分布\n")
L.append("| 类别 | 分类分布 |")
L.append("| --- | --- |")
for c, _ in CATS:
    L.append("| %s | %s |" % (c, " / ".join("%s %d" % (k, v) for k, v in cls_dist[c].most_common())))

L.append("\n## 四、本次（W11g）改动\n")
L.append("- **门控 38 组目视终裁**：拆 19 / 不拆 19（见 `门控_38组目视终裁.tsv`）。")
L.append("- **执行拆分 13 组**（新增产物，均 `_alt<源>` 命名，原字节复制）：")
L.append("  - 标题菜单按钮文案不同：`tl_01/02/03/04`（otp「ある日の◯◯」）、`tl_new`（otp「New」无叹号）、`tl_logo`（ota「After Story」LOGO）")
L.append("  - 章标题卡内含完全不同的图：`ec2_bg`（otp 餐厅街景）、`ec3_bg`（otp 夜晚霓虹街道）")
L.append("  - 画廊菜单条目文案/角色不同：`gl_music`、`gl_chrbg`、`gl_chr2`、`gl_chr5`、`gl_chr4`")
L.append("- **判定为「不拆」的 19 组**（保留现状）：`bg41/bg41a/bg72/bg72b/ef05a/bg01/bg01b`（同画不同裁切）、")
L.append("  `tl_galry/tl_cfg/tl_exit/tl_load/tl_chk/ec2_name/ec3_name`（同一 UI 元素的不同皮肤/配色）、")
L.append("  `ec1_bg/ec4_bg/ec6_bg`（同章卡底图，otv 为含字整卡）、`gl_chr1/gl_scene`（文案/设计一致）。")
L.append("- **已分离（无需再动）**：`miy02a`（np 立绘 → `立绘\\`；ot/pic CG → `CG背景\\cg_miy02a.png`）、`ss_bg1–5`（W11d 底板/整页）。")

L.append("\n## 五、可复现\n")
L.append("```bash")
L.append("cd 资源组\\工具 && set PYTHONPATH=E:\\ZCode Workspace\\Galgame\\工具\\pylibs")
L.append("python w11g_gate_classify2.py   # 复核 160/38 划分")
L.append("python w11g_sheets.py           # 生成 38 组目视证据图")
L.append("python w11g_compare.py          # 客观比对（md5/亮度/两两 MAD）")
L.append("python w11g_verdict.py          # 产出 门控_38组目视终裁.tsv")
L.append("python w11g_split.py            # 执行 13 组拆分 + 同步清单/待复核（分表生成/同步）")
L.append("python w11g_fix_schema.py       # 分表 `类别` 拆为 `类别` + `判读类别`（幂等；--check 只校验）")
L.append("python w11g_deliver.py          # 产出 交付清单.tsv（含 `判读类别`）")
L.append("python w11g_stats.py            # 产出 交付统计.md")
L.append("python w11g_verify.py           # 8 项自检 -> _验收_W11g.json（all_ok=true）")
L.append("python w11g_check_doc_paths.py  # 抽检文档路径引用是否存在")
L.append("```")
L.append("")
L.append("> **管线顺序（不得颠倒）**：分表生成/同步（`w11g_split.py`）→ `w11g_fix_schema.py`（列迁移）→ `w11g_deliver.py`（总表）→ `w11g_verify.py`（自检）。")
L.append("> `w11g_fix_schema.py` **必须排在 `w11g_deliver.py` 之前**：总表的 `判读类别` 列由分表带出，分表未迁移则总表子分类丢失")
L.append("> （`w11g_deliver.py` 对旧版分表会回退取旧 `类别` 列，从而把 `未识别`/`未判定` 混进大类）。")
L.append("> 与 `README_交付超分.md` §八 的管线说明一致；README 另有 `w11g_stats.py`、`w11g_check_doc_paths.py` 两条，本次已补齐。")

atomic_write(os.path.join(UNI, "交付统计.md"), "\n".join(L) + "\n")
print("写出 交付统计.md；产物合计 %d，来源候选 %d" % (tot_p, tot_c))
print("选源:", {k: dict(v) for k, v in src_dist.items()})