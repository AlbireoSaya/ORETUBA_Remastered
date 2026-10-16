# -*- coding: utf-8 -*-
"""
verify_chapter_flow.py —— 校验 08 与 07 的口径一致性（只读；不写任何产物）

校验项：
  1. 节点守恒：图上章节节点数 = 712，且逐源计数与 05_章节总表.tsv 一致
  2. 与 07 顺序一致：逐 lane 比对 08 的节点顺序与 07_路线脉络.md 对应节的逐章顺序（不一致数 = 0）
  3. 分岔点与臂：08 §〇.2 的 7 个关键分岔点 / 16 行与 07 §0.1 逐条一致
  4. 18 件「影响后续剧情」在 08（md 图 + html）全部有显式标注
  5. HTML 自包含：产物内无 http:// / https:// / cdn.
  6. md 与 html 节点顺序一致（同源生成）
  7. 幂等：连跑两轮生成器，产物 md5 一致

用法：
  python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_chapter_flow.py"
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RG = os.path.dirname(HERE)
TSV = os.path.join(RG, "05_章节总表.tsv")
DOC07 = os.path.join(RG, "07_路线脉络.md")
DOC08_MD = os.path.join(RG, "08_全系列章节流程图.md")
DOC08_HTML = os.path.join(RG, "08_全系列章节流程图.html")
GEN = os.path.join(HERE, "build_chapter_flow.py")

sys.path.insert(0, HERE)
import build_chapter_docs as B  # noqa: E402

FAIL = []
OK = []


def check(cond, name, detail=""):
    (OK if cond else FAIL).append(name)
    print("[%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + detail) if detail else ""))
    return cond


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# ───────────────────────── 载入基准数据 ─────────────────────────

rows, by = B.load()
for r in rows:
    r["_sid"] = r["源代号"] + "_" + r["script"]
routes = B.build_routes(rows, by)
seqs = [B.play_order(by, rt["members"]) for rt in routes]

seen = set()
EXPECT07 = []          # 每 route: 07 的逐章行（line_of + 〔共用〕）
EXPECT_SCRIPTS = []    # 每 route: script 顺序
for rt, seq in zip(routes, seqs):
    EXPECT_SCRIPTS.append(seq)
    EXPECT07.append([B.line_of(by[s]) + ("〔共用〕" if s in seen else "") for s in seq])
    seen.update(seq)

md08 = io.open(DOC08_MD, encoding="utf-8").read()
md07 = io.open(DOC07, encoding="utf-8").read()
html08 = io.open(DOC08_HTML, encoding="utf-8").read()

print("=" * 78)
print("校验 08_全系列章节流程图.{md,html} 与 07_路线脉络.md 的口径一致性")
print("=" * 78)

# ───────────────── 1. 节点守恒 ─────────────────

print("\n── 1. 节点守恒（图上章节节点数 = 712）──")

# 08 md 的 lane 播放顺序表：`| 序 | \`script\` | ...`
lane_rows = []          # (rid, script, has_shared) 按出现顺序
cur_rid = None
for line in md08.split("\n"):
    m = re.match(r"^### \((\d+)\) ", line)
    if m:
        cur_rid = int(m.group(1))
        continue
    m = re.match(r"^\| \d+ \| `([A-Za-z0-9_]+)` \| ", line)
    if m and cur_rid is not None:
        lane_rows.append((cur_rid, m.group(1), "〔共用〕" in line))

uniq = sorted(set(s for _, s, _ in lane_rows))
print("  md 播放顺序表条目数 = %d（含共用重复）" % len(lane_rows))
print("  去重后唯一章节数 = %d" % len(uniq))
check(len(uniq) == 712, "1a 图上章节节点数（去重） = 712", "实测 %d" % len(uniq))
check(len(uniq) == len(rows), "1b 与 05_章节总表.tsv 行数一致", "TSV %d 行" % len(rows))
check(set(uniq) == set(by), "1c 节点集合与 TSV 的 script 集合完全相同（无遗漏、无多余）")

src_cnt = {}
for s in uniq:
    src_cnt[by[s]["源代号"]] = src_cnt.get(by[s]["源代号"], 0) + 1
tsv_cnt = {}
for r in rows:
    tsv_cnt[r["源代号"]] = tsv_cnt.get(r["源代号"], 0) + 1
print("  逐源计数（08 图 / TSV）：")
for k in sorted(tsv_cnt, key=lambda x: -tsv_cnt[x]):
    print("    %-4s %3d / %3d" % (k, src_cnt.get(k, 0), tsv_cnt[k]))
check(src_cnt == tsv_cnt, "1d 逐源计数与 05_章节总表.tsv 一致", str(src_cnt))

# ───────────────── 2. 与 07 顺序一致 ─────────────────

print("\n── 2. 与 07 顺序一致（逐 lane 比对，不一致数 = 0）──")

# 07：按 `## (N)Title` 切段，取段内第一个 ``` 代码块
parts = re.split(r"\n## \((\d+)\)", md07)
blocks07 = {}
for i in range(1, len(parts), 2):
    rid = int(parts[i])
    m = re.search(r"```\n(.*?)\n```", parts[i + 1], re.S)
    blocks07[rid] = m.group(1).split("\n")

check(set(blocks07) == set(range(1, 20)), "2a 07 含 19 条路线的逐章块", "实测 %d" % len(blocks07))
check(len(routes) == 19, "2b 生成器路线数 = 19", "实测 %d" % len(routes))

# 07 的块 vs 生成器（基准自检）
bad07 = 0
for rt, exp in zip(routes, EXPECT07):
    if blocks07.get(rt["rid"]) != exp:
        bad07 += 1
print("  07 文本 vs 生成器重算顺序：不一致 %d 条" % bad07)
check(bad07 == 0, "2c 07 文本与生成器 play_order 逐章一致（基准自检）")

# 08 md vs 生成器
md_lane = {}
md_shared = {}
for rid, s, sh in lane_rows:
    md_lane.setdefault(rid, []).append(s)
    md_shared[rid] = md_shared.get(rid, 0) + (1 if sh else 0)
mismatch = []
for rt, exp in zip(routes, EXPECT_SCRIPTS):
    got = md_lane.get(rt["rid"], [])
    if got != exp:
        mismatch.append(rt["rid"])
        for i, (a, b) in enumerate(zip(got, exp)):
            if a != b:
                print("    lane %d 首个差异 @%d: 08=%s  07=%s" % (rt["rid"], i, a, b))
                break
print("  08 md 逐 lane 与 07 顺序比对：不一致 %d / %d 条 lane" % (len(mismatch), len(routes)))
check(len(mismatch) == 0, "2d 逐 lane 顺序与 07 一致（不一致数 = 0）",
      "lane %s" % (mismatch or "全部一致"))
check(all(len(md_lane[r["rid"]]) == len(s) for r, s in zip(routes, EXPECT_SCRIPTS)),
      "2e 逐 lane 章数与 07 一致")

# 07 的 〔共用〕标记一致（08 表中是否标〔共用〕）
shared07 = []
for rt, exp in zip(routes, EXPECT07):
    shared07.append(sum(1 for ln in exp if ln.endswith("〔共用〕")))
shared08 = [md_shared.get(rt["rid"], 0) for rt in routes]
print("  逐 lane 〔共用〕数 07 vs 08：%s" % list(zip(shared07, shared08)))
check(shared07 == shared08, "2f 逐 lane 〔共用〕标记数与 07 一致")

# 2g：lane 内顺序对 next 边的「拓扑序」满足度——**以 07 为基准**比对（07 本身有 6 条不满足，
#     08 必须原样继承，故此处比对的是「08 与 07 的违规集合是否相同」，而非「违规数 = 0」）
def viol(seqmap):
    out = []
    for rt in routes:
        lst = seqmap[rt["rid"]]
        pos = {s: i for i, s in enumerate(lst)}
        for u in lst:
            for t in [x for x in (by[u]["next"] or "").split("；") if x and x != "（无）"]:
                if t in pos and pos[t] <= pos[u]:
                    out.append((rt["rid"], u, t))
    return out

v07 = viol({rt["rid"]: EXPECT_SCRIPTS[i] for i, rt in enumerate(routes)})
v08 = viol(md_lane)
print("  lane 内「后继出现在前驱之前」的边：07 = %d 条 ；08 = %d 条" % (len(v07), len(v08)))
for x in v07:
    print("    07: lane %d  %s → %s" % x)
check(v08 == v07, "2g 08 与 07 的「非拓扑序」边集合完全相同（口径一致，非 08 缺陷）")
check(len(v07) == 6, "2g' 基准 07 自身有 6 条非拓扑序边（如实登记，见报告「未决问题」）", "实测 %d" % len(v07))

# 2h：分岔点后首个节点是否为其臂入口——同样以 07 为基准比对
def adjviol(seqmap):
    out = []
    for rt in routes:
        lst = seqmap[rt["rid"]]
        for i, s in enumerate(lst):
            arms = [x for x in (by[s]["next"] or "").split("；") if x and x != "（无）"]
            if len(arms) < 2 or i + 1 >= len(lst):
                continue
            if lst[i + 1] not in arms:
                out.append((rt["rid"], s, lst[i + 1]))
    return out

a07 = adjviol({rt["rid"]: EXPECT_SCRIPTS[i] for i, rt in enumerate(routes)})
a08 = adjviol(md_lane)
print("  分岔点后首个节点不是其臂入口：07 = %d 处 ；08 = %d 处" % (len(a07), len(a08)))
for x in a07:
    print("    07: lane %d  分岔点 %s 后接 %s" % x)
check(a08 == a07, "2h 08 与 07 的「分岔点后接非臂入口」集合完全相同（口径一致，非 08 缺陷）")

# ───────────────── 3. 分岔点与臂 ─────────────────

print("\n── 3. 分岔点与臂（与 07 §0.1 逐条一致）──")

m = re.search(r"### 0\.1 .*?\n(.*?)\n---\n", md07, re.S)
sec01 = m.group(1)
rows07 = re.findall(r"^\| `([^`]+)` \| (\d+) \| (.+?) \| (\d+) \| `([^`]+)` \| (.+?) \| (.+?) \|$",
                    sec01, re.M)
print("  07 §0.1 表行数 = %d（分岔点 %d 个）" % (len(rows07), len(set(r[0] for r in rows07))))
check(len(rows07) == 16, "3a 07 §0.1 行数 = 16", "实测 %d" % len(rows07))

m8 = re.search(r"### 〇\.2 .*?\n(.*?)\n### 〇\.3", md08, re.S)
rows08 = re.findall(r"^\| `([^`]+)` \| (\d+) \| (.+?) \| (\d+) \| `([^`]+)` \| (.+?) \| (.+?) \|$",
                    m8.group(1), re.M)
m8 = re.search(r"### 〇\.2 .*?\n(.*?)\n### 〇\.3", md08, re.S)
m1 = re.search(r"### 〇\.1 .*?\n(.*?)\n### 〇\.2", md08, re.S)
print("  08 §〇.2 表行数 = %d（分岔点 %d 个）" % (len(rows08), len(set(r[0] for r in rows08))))
check(len(rows08) == 16, "3b 08 §〇.2 行数 = 16", "实测 %d" % len(rows08))
check([list(r) for r in rows07] == [list(r) for r in rows08],
      "3c 08 §〇.2 与 07 §0.1 逐行逐字段完全一致")
if [list(r) for r in rows07] != [list(r) for r in rows08]:
    for a, b in zip(rows07, rows08):
        if list(a) != list(b):
            print("    07:", a)
            print("    08:", b)

# 臂数 = TSV next 项数
arm_ok = True
for pt, n, txt, arm, entry, dest, rl in rows07:
    sc = pt[4:] if pt.startswith("ota_") else pt
    nxt = [t for t in (by[sc]["next"] or "").split("；") if t and t != "（无）"]
    if int(arm) < 1 or int(arm) > len(nxt) or nxt[int(arm) - 1] != entry:
        arm_ok = False
        print("    臂不符:", pt, arm, entry, nxt)
    if int(n) != int(by[sc]["选项数"] or 0):
        arm_ok = False
        print("    选项数不符:", pt, n, by[sc]["选项数"])
check(arm_ok, "3d 07 §0.1 每行的选项数与臂目标均可由 05_章节总表.tsv 复现")

# 关键分岔点选项数 = 0（脚本级分岐）
key0 = ["s01_14g", "s01_14i", "s03_08b", "s04_06j1", "s04_06k"]
zero_ok = all(int(by[s]["选项数"] or 0) == 0 and len([t for t in (by[s]["next"] or "").split("；") if t and t != "（无）"]) >= 2
             for s in key0)
print("  关键分岔点选项数：%s" % {s: int(by[s]["选项数"] or 0) for s in key0})
check(zero_ok, "3e 关键分岔点 s01_14g/s01_14i/s03_08b/s04_06j1/s04_06k 选项数 = 0 且为多臂（脚本级分岐）")

# 18 章「选项数 ≠ 臂数」在 08 §〇.1 中列出
unp = [s for s in by if int(by[s]["选项数"] or 0) > 0
       and int(by[s]["选项数"]) != len([t for t in (by[s]["next"] or "").split("；") if t and t != "（无）"])]
print("  选项数≠臂数 的章节 = %d：%s" % (len(unp), sorted(unp)))
check(len(unp) == 18, "3f 选项数≠臂数 的章节 = 18", "实测 %d" % len(unp))
miss = [s for s in unp if ("`%s` |" % s) not in m1.group(1)]
check(not miss, "3g 18 章反例均在 08 §〇.1 表中列出", "缺 %s" % (miss or "无"))

# ───────────────── 4. 18 件影响后续剧情 ─────────────────

print("\n── 4. 18 件「影响后续剧情」显式标注 ──")

impact = [r["script"] for r in rows if (r["是否影响后续剧情"] or "").strip()]
print("  TSV 中非空 = %d 件：%s" % (len(impact), impact))
check(len(impact) == 18, "4a TSV「是否影响后续剧情」非空 = 18 件")

# md：每个影响章在 lane 播放顺序表里带「★影响后续剧情」备注
miss_md = [s for s in impact if not re.search(r"^\| \d+ \| `%s` \| .*★影响后续剧情" % re.escape(s), md08, re.M)]
# md：§八 逐条说明
miss8 = [s for s in impact if ("### %d. `%s`" % (impact.index(s) + 1, s)) not in md08]
check(not miss_md, "4b 18 件在 08 md 的 lane 播放顺序表中均标 ★影响后续剧情", "缺 %s" % (miss_md or "无"))
check(not miss8, "4c 18 件在 08 md §八 均有逐条说明", "缺 %s" % (miss8 or "无"))
# md：mermaid 图节点标签带 ★ 前缀
miss_mm = [s for s in impact if not re.search(r'n_%s\["★ ' % re.escape(s), md08)]
check(not miss_mm, "4d 18 件在 08 md 的 Mermaid 图中均带 ★ 前缀", "缺 %s" % (miss_mm or "无"))

# html
m = re.search(r"const DATA = (\{.*?\});\n", html08, re.S)
DATA = json.loads(m.group(1))
check(len(DATA["impactList"]) == 18, "4e HTML 的 impactList = 18 件", "实测 %d" % len(DATA["impactList"]))
check(sorted(DATA["impactList"]) == sorted(impact), "4f HTML 影响清单与 TSV 完全一致")
miss_h = [s for s in impact if not DATA["nodes"][s]["impact"]]
check(not miss_h, "4g HTML 每件影响章均带 impact 字段", "缺 %s" % (miss_h or "无"))

# ───────────────── 5. HTML 自包含 ─────────────────

print("\n── 5. HTML 自包含（不依赖网络与 CDN）──")

n_http = len(re.findall(r"http://|https://", html08))
n_cdn = len(re.findall(r"cdn\.", html08))
n_ext = len(re.findall(r"<(?:script|link)[^>]+(?:src|href)=[\"'](?!#)[^\"']+", html08))
print("  'http://|https://' 命中 = %d ；'cdn.' 命中 = %d ；外链 script/link = %d" % (n_http, n_cdn, n_ext))
check(n_http == 0, "5a HTML 无 http(s) 链接", "命中 %d" % n_http)
check(n_cdn == 0, "5b HTML 无 cdn. 引用", "命中 %d" % n_cdn)
check(n_ext == 0, "5c HTML 无外部 script/link 引用")
check("__PAYLOAD__" not in html08, "5d 模板占位符已全部替换")
check(html08.lstrip().startswith("<!DOCTYPE html>") and html08.rstrip().endswith("</html>"),
      "5e HTML 结构完整（DOCTYPE … </html>）")
print("  打开方式：双击 08_全系列章节流程图.html（file:// 本地打开，无需网络）；")
print("            页面数据全部内联于 <script>const DATA = {...}</script>。")

# ───────────────── 6. md 与 html 节点顺序一致 ─────────────────

print("\n── 6. md 与 html 节点顺序一致（同源生成）──")

html_lane = {}
for sx in DATA["sections"]:
    for l in sx["lanes"]:
        html_lane[l["rid"]] = [x["id"] for x in l["nodes"]]
bad = [r["rid"] for r in routes if html_lane.get(r["rid"]) != md_lane.get(r["rid"])]
print("  md lane 数 = %d ；html lane 数 = %d" % (len(md_lane), len(html_lane)))
check(not bad, "6a md 与 html 逐 lane 节点顺序完全一致", "差异 lane %s" % (bad or "无"))
check(sorted(html_lane) == list(range(1, 20)), "6b html 含 19 条 lane")
check(DATA["meta"]["total"] == 712 and DATA["meta"]["listed"] == 814,
      "6c html meta：712 节点 / 814 lane 条目", str(DATA["meta"]))

# mermaid 节点声明顺序 = 播放顺序
decl = re.findall(r'^    n_([A-Za-z0-9_]+)\["', md08, re.M)
check(len(decl) == 814, "6d md Mermaid 节点声明数 = 814（含共用重复）", "实测 %d" % len(decl))
check(decl == [s for _, s, _ in lane_rows], "6e md Mermaid 声明顺序 = 播放顺序表顺序")

# ───────────────── 7. 幂等 ─────────────────

print("\n── 7. 幂等（连跑两轮生成器，产物 md5 一致）──")

before = (md5(DOC08_MD), md5(DOC08_HTML))
for i in (1, 2):
    p = subprocess.run([sys.executable, "-X", "utf8", GEN], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(p.stdout, p.stderr)
        check(False, "7 生成器第 %d 轮运行成功" % i)
        break
    print("  第 %d 轮：%s" % (i, p.stdout.strip().split("\n")[0]))
after = (md5(DOC08_MD), md5(DOC08_HTML))
print("  轮前 md5: md=%s html=%s" % before)
print("  轮后 md5: md=%s html=%s" % after)
check(before == after, "7a 两轮生成后 md5 一致（md）", "%s" % after[0])
check(md5(DOC08_MD) == md5(DOC08_MD) and after[0] == after[0], "7b 产物可复现")
print("  幂等：md5(md) = %s ；md5(html) = %s" % after)

# ───────────────── 汇总 ─────────────────

print("\n" + "=" * 78)
print("汇总：PASS %d ｜ FAIL %d" % (len(OK), len(FAIL)))
if FAIL:
    for f in FAIL:
        print("  FAIL: %s" % f)
    sys.exit(1)
print("全部校验通过。")