# -*- coding: utf-8 -*-
r"""
build_rulings_fixtable.py — 把用户 2026-09-30 的术语裁决落成**可机械消费的修正表**（ISSUE-20260930-10）

产出：`资源组\修正\修正表_裁决20260930.tsv`（11 列，schema 同既有修正表；见 `修正\_README.md` §二）

覆盖（**只收「非采用变体 → 采用译法」**；已正确的槽不入表）：

**第一组：2026-09-30 用户十项术语裁决（ISSUE-20260930-10）**
  1 `古罗利亚斯` → **GLORIOUS**（保留拉丁）                        （ot / otr）
  2 `游隼` → **隼**                                                （ot / otr；**门控：JP 含 `ハヤブサ`**）
  3 `耳语材料` / `细语材质` → **低语材料**                          （otp / otv）
  4 `罗伊希滕` → **洛伊希滕**                                       （otv；所在短语「罗伊希滕·格雷塔」）
  5 独立 `空学院`（排除「美空学院」子串） → **美空学院**              （otv）
  6 独立 `空学`（排除「美空」前缀、排除后接 `院|府`） → **美空学院**    （ot/otp/ota/otr/otv/np，统一「美空学院」）

**第二组：`作品skill\术语表.md` §2.7.4「本轨未采用、需回改的异译」整族回改（ISSUE-20260930-11）**
用户 2026-09-30 裁决「整族做完，31 槽」；采用值均已在 §2.7.4 定下，本组只是把它们写进修正表：
  7 `美空学园`（`美空学園` 的「学园」写形） → **美空学院**            （ot 2 / otr 8）
  8 `柳木原普利广场` / `柳波广场` / `柳木原广场` → **柳警广场**        （otr 3+2 / otv 1）
  9 `羽田宅` / `羽田宅邸` → **羽田家**                               （ot 8 / ota 2 / otr 2 / otv 2）
 10 `苍羽女学院` → **苍穹女子学院**                                  （otr 1；低置信项，经用户 2026-09-30 确认沿用）

**locator 形态随源分派**（`修正\_README.md` §二，**以消费方实现为准**）：
  ot  → `script=<脚本名>&seq=<语料 lines[].lineno>`（`build_scene_ot.py:530` 用 `l["seq"]`）
  otp → `seq=<语料 lines[].index>`（`build_scene_otp.py:511/530/600`：locator 用源 SOB0 槽序，**落在语料 `index` 字段**）
  otv → `script=<脚本名>&lineno=<语料 lines[].lineno>`，`file=台词对照.json`
  ota → `idx=<语料 lines[].index>`；np → `offset=<语料 lines[].index>`
  otr → `offset=<n>`（取自 `工程\我们没有翅膀R\亜衣线资源\剧本\台词对照.json`）
      **或 `idx=<语料 lines[].index>`**——后者给**消息表里没有地址的「梗概槽」**用（`台词对照.json` 该槽
      `offset=None` 且 `jp` 为空；otr 语料共 58 个此类槽，每个场景 1 个，此前**任何修正表都够不到**）。
      消费方 `build_scene_jsonl.py` 在 `offset is None` 时**退化按语料 `index` 定位**（ISSUE-20260930-11 新增；
      additive——仅当表内确有该键时才生效，且命中前断言 `old_text` 与源语料逐字符相等 ⇒ 错位即 fail loud）。

硬闸门（都能真失败）
  G0 **每条规则必须显式给替换值**（无 `repl` 即 fail loud——防「未给值 → 静默替换成别的词」这类缺陷）
  G0b **每行 `old_text` 必须能 `re.compile`**，且**必须在基准句上至少命中一次**（坏正则 / 词形写错即 fail loud）
  G1 各变体槽数与实测常量一致（古罗利亚斯 29 / 游隼 27 / 耳语材料 2 / 细语材质 4 / 罗伊希滕 2 / 独立空学院 4
     / 美空学园写形 10 / 柳木原普利广场 3 / 柳波广场 2 / 柳木原广场 1 / 羽田宅 14 / 苍羽女学院 1）
  G2 `游隼` 每槽 JP 含 `ハヤブサ`；G3 空格学院/空学/美空学园 每槽 JP 含 `学園`/`ソラ学`/`ソラガク`/`美空`
  G4 otr 行全部能取到 locator：`jp` 非空者须从 `台词对照.json` 取到**唯一非 None** 的 `offset`；
     `jp` 为空者须能给出 `idx=<index>`（0 未命中、0 多义）
  G5 **替换后不得残留该词形**（用 `re.sub` 模拟）；G5b **畸形拼接**（`美空学院` 后不得紧跟 院/园/生/府；
     `羽田家` 后不得紧跟 邸/宅；`柳警广场` 后不得紧跟 广/场；`苍穹女子学院` 后不得紧跟 学院/院。
     ★「苍穹女子学院**学生**」是合法中文，故只判重复后缀）
  G6 **locator 往返 ＋ 独立证据**：按 `CONSUMER_KEY` **独立声明的消费键**重新定位每一行，然后
     ① 该槽 `jp` 必须仍满足该家族的 **JP 门控**（jp 取自源语料，与生成路径相互独立——**这是最强的一条**）；
     ② 该槽基准句必须**至少命中一次**该行 `old_text`（否则 locator 疑漂移）
  G7 **消费方挂接**：本表出现的每个 source，其构建器（`build_scene_*.py`）都必须挂载本表**且**该构建器的
     `CORR_SOURCE_TO_BASE` 覆盖本表出现的全部 source——否则「行在表里、消费方没加载/映射缺项」，
     两侧都看不见（静默不生效）或装载即崩
  G8 `--check` 幂等（槽位发现走成品 `fix_refs`，故**语料重建后仍可复现**）

**`old_text` / `new_text` 的语义（★ ISSUE-20260930-12 起＝词形级替换）**

本表全部行 `fix_type=term_unify`，其 `old_text` = **被替换词形的正则**、`new_text` = **替换值**（**不是整句**）。
消费方语义（六源一致）：

    if re.search(old_text, cn):     cn = re.sub(old_text, new_text, cn)      # 命中即替换
    elif new_text in cn:            留痕 no-op（本表已生效，幂等）             # 已修过
    else:                           fail loud（定位漂移 / 词形已变）

- **为什么是正则而不是裸 `str.replace`**：实测 3 个变体是**采用值的子串**（`空学`／`空学院`／`美空学` ⊆ `美空学院`），
  裸替换会自爆（`美空学院` → `美美空学院院`）⇒「空学族」必须留上下文守卫（`(?<!美)空学(?!院|府|园)` 等）。
  **实测全部 16 个变体均不含正则元字符**（`.-^$*+?()[]{}|\` 全无），故其余 95 行以正则可读性无损失。
- **为什么不再需要整句基准层**：旧语义下消费方 `cn = new_text`（整句覆盖），于是该槽**别的字**会被一并写回旧句——
  上游一旦润色/重译，这条行会**静默把改进顶回去**，只能靠「`old_text` 逐字符等于基准层」把它转成 fail loud。
  词形级替换只碰术语那几个字，**其余字永远是当前值** ⇒ 不再依赖整句基准层、也不再依赖本项目之外的
  `工程\我们没有翅膀\汉化\剧情汉化\`。

**槽位发现（不依赖任何外部基准语料）**：逐规则扫六源成品语料，`base_text = fix_refs[0].cn_before`（若有）否则 `cn`；
`re.search(pat, base_text)` 命中即为目标槽。已生效的槽其变体已不在成品 `cn` 里，但**消费方记录在
`fix_refs[].cn_before` 的基准句仍含该变体** ⇒ 语料重建后照样能复现整张表（`--check` 幂等）。
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
PROJ = os.path.dirname(RES)
WS = os.path.dirname(os.path.dirname(PROJ))
OUT = os.path.join(RES, "修正", "修正表_裁决20260930.tsv")
LESSON = "用户 2026-09-30 裁决："


def roots():
    out = [PROJ, os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原"), WS]
    d = PROJ
    while True:
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            out.append(d)
    seen, res = set(), []
    for r in out:
        if r and r not in seen:
            seen.add(r); res.append(r)
    return res


def find(rel):
    for base in roots():
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            return p
    raise SystemExit("找不到：" + rel)


SCENES = os.path.join(RES, "剧本")
OTR_SRC = r"工程\我们没有翅膀R\亜衣线资源\剧本\台词对照.json"
ALL_SRC = ["ot", "otp", "ota", "otr", "otv", "np"]
SRC_FILE = {"ot": "sob", "otp": "sob", "otv": "otv", "otr": "tob", "ota": "tob", "np": "tob"}


def base_index(src):
    """槽位发现用的「基准句」索引：键 = (source, file, locator)，值 = 该槽**最早一次修正前**的 cn。

    取自**消费方自己记录**在成品语料 `fix_refs[].cn_before` 的原文（`fix_refs` 按应用顺序追加，
    故取**先到的**一条＝最早一次修正之前）。**这不是整句 pin**（本表已改成词形级替换，
    `old_text` 只是词形正则）——这里用基准句只是为了**发现哪些槽是该术语的目标槽**：
    已生效的槽其变体已不在成品 `cn` 里，但基准句里还在，故语料重建后仍能复现整张表。
    没有 `fix_refs` 的槽（没被任何表碰过）⇒ 成品 `cn` 即基准句。
    """
    out = {}
    for script, L in load_corpus(src):
        for fr in (L.get("fix_refs") or []):
            loc = fr.get("locator")
            base = fr.get("cn_before") or fr.get("old_text")
            if not loc or not base:
                continue
            out.setdefault((src, fname(src, script), loc), base)   # 先到的即最早一次修正
    return out


def fname(src, script):
    if src in ("ot", "otp"):
        return script + ".sob.jsonl"
    if src == "otv":
        return "台词对照.json"
    return script + ".tob"


# ★ 消费方定位键（**独立声明**，G6 用它重建索引；与 `locate()` 分开写，
#   这样「生成路径字段取错」会被 G6 抓住，而不是自证）
CONSUMER_KEY = {"ot": "lineno", "otp": "index", "ota": "index",
                "otv": "lineno", "np": "index", "otr": "offset"}


def consumer_locator(src, script, L, otr_idx):
    """**只按 `CONSUMER_KEY` 声明的字段**拼 locator（G6 专用，故意不复用 `locate()`）。"""
    key = CONSUMER_KEY[src]
    if src == "otr":
        # 梗概槽（jp 为空）在消息表里没有地址 ⇒ 消费键退化为 index（见模块头 otr 条）
        if not (L.get("jp") or "").strip():
            return "idx=%s" % L.get("index")
        cands = otr_idx.get((fname("otr", script), L.get("jp"))) or []
        return ("offset=%d" % cands[0]) if (len(cands) == 1 and cands[0] is not None) else None
    if src == "np":
        return "offset=%s" % L.get(key)
    if src == "ot":
        return "script=%s&seq=%s" % (script, L.get(key))
    if src == "otv":
        return "script=%s&lineno=%s" % (script, L.get(key))
    if src == "ota":
        return "idx=%s" % L.get(key)
    return "seq=%s" % L.get(key)          # otp


def locate(src, script, L, otr_idx):
    """按**消费方语义**拼 locator；返回 (locator, 该定位键下的 cn)。"""
    if src == "ot":
        return "script=%s&seq=%s" % (script, L.get("lineno")), L.get("cn")
    if src == "otp":
        return "seq=%s" % L.get("index"), L.get("cn")          # 消费方用 index（见模块头）
    if src == "otv":
        return "script=%s&lineno=%s" % (script, L.get("lineno")), L.get("cn")
    if src == "ota":
        return "idx=%s" % L.get("index"), L.get("cn")
    if src == "np":
        return "offset=%s" % L.get("index"), L.get("cn")
    if src == "otr":
        jp = L.get("jp") or ""
        if not jp.strip():
            return "idx=%s" % L.get("index"), L.get("cn")       # 梗概槽（消息表无地址）
        cands = otr_idx.get((fname("otr", script), jp)) or []
        if len(cands) == 1 and cands[0] is not None:
            return "offset=%d" % cands[0], L.get("cn")
        return None, L.get("cn")
    raise SystemExit("未预期的源：" + src)


# (源, 变体名, 正则, 替换值[必填], 门控, 证据, 置信)
RULES = [
    ("ot", "古罗利亚斯", re.compile("古罗利亚斯"), "GLORIOUS", None,
     LESSON + "`グロリアス` 采「保留拉丁 GLORIOUS」（不音译）", "high"),
    ("otr", "古罗利亚斯", re.compile("古罗利亚斯"), "GLORIOUS", None, None, "high"),
    ("ot", "游隼", re.compile("游隼"), "隼", lambda jp: "ハヤブサ" in jp,
     LESSON + "`ハヤブサ` 采「隼」（弃用「游隼」；与本篇 §三之三十三的冲突以本裁决为准）", "high"),
    ("otr", "游隼", re.compile("游隼"), "隼", lambda jp: "ハヤブサ" in jp, None, "high"),
    ("otp", "耳语材料", re.compile("耳语材料"), "低语材料", None,
     LESSON + "`ささやきマテリアル` 采「低语材料」（统一《耳语材料》/细语材质）", "high"),
    ("otv", "细语材质", re.compile("细语材质"), "低语材料", None, None, "high"),
    ("otv", "罗伊希滕", re.compile("罗伊希滕"), "洛伊希滕", None,
     LESSON + "`ロイヒテン・グレタ` 采「洛伊希滕·格雷塔」", "high"),
    ("otv", "独立空学院", re.compile(r"(?<!美)空学院"), "美空学院",
     lambda jp: ("学園" in jp or "ソラ学" in jp or "ソラガク" in jp),
     LESSON + "`ソラ学`/`ソラガク` 采「美空学院」（源侧三写并存已确认；独立「空学院」归一）", "high"),
]
# 独立「空学」→「美空学院」：覆盖六源（同一裁决的下半）
for _s in ALL_SRC:
    RULES.append((_s, "独立空学", re.compile(r"(?<!美)空学(?!院|府|园)"), "美空学院",
                  lambda jp: ("学園" in jp or "ソラ学" in jp or "ソラガク" in jp),
                  None if _s != "ot" else LESSON + "同上（独立「空学」归一「美空学院」）", "high"))
# 「美空学」截断写形（后不接 院/府/园）→「美空学院」：otr 实测 20 槽 JP 全为 `ソラ学`
for _s in ALL_SRC:
    RULES.append((_s, "美空学截断", re.compile(r"美空学(?!院|府|园|生)"), "美空学院",
                  lambda jp: ("ソラ学" in jp or "ソラガク" in jp or "学園" in jp),
                  None if _s != "otr" else LESSON + "同上（「美空学」截断写形归一「美空学院」）", "high"))
# 「空学园」（不含「美」前缀）→「美空学院」：一审复核抓出的畸形源（原规则命中其「空学」留孤字「园」）
for _s in ALL_SRC:
    RULES.append((_s, "空学园", re.compile(r"(?<!美)空学园"), "美空学院",
                  lambda jp: ("ソラ学" in jp or "ソラガク" in jp or "学園" in jp),
                  None if _s != "otr" else LESSON + "同上（「空学园」整词归一「美空学院」）", "high"))

# ================================================================ 第二组（§2.7.4 整族回改）
# 7 `美空学园` 写形 → 美空学院（ot 2 / otr 8）。9 槽 JP 作 `美空学園`，1 槽（otr s03c_09b）JP 作
#   `美空の学力`（译者在 CN 里补全为「美空学园」）——故门控同时接受 `美空` 与 `学園`/`ソラ学`/`ソラガク`。
for _s in ("ot", "otr"):
    RULES.append((_s, "美空学园写形", re.compile("美空学园"), "美空学院",
                  lambda jp: ("美空" in jp or "学園" in jp or "ソラ学" in jp or "ソラガク" in jp),
                  None if _s != "ot" else LESSON + "`美空学園` 归一「美空学院」（§2.7.4；「学园」写形与采用值不一致）",
                  "high"))
# 8 `ヤナポリ広場` 的三异写 → 柳警广场（otr 3+2 / otv 1）。采用值「柳警广场」有 ot 侧原文自带词源支撑
#   （ot 实测 12 槽；§2.7.4）。三写形互不为子串，故三条规则并列、各按整词替换。
for _s, _lab in (("otr", "柳木原普利广场"), ("otr", "柳波广场"), ("otv", "柳木原广场")):
    RULES.append((_s, _lab, re.compile(_lab), "柳警广场",
                  lambda jp: "ヤナポリ広場" in jp,
                  None if (_s, _lab) != ("otr", "柳木原普利广场")
                  else LESSON + "`ヤナポリ広場` 归一「柳警广场」（§2.7.4；ot 原文自带词源）",
                  "high"))
# 9 `羽田宅` / `羽田宅邸` → 羽田家（ot 8 / ota 2 / otr 2 / otv 2）。整词含「羽田宅邸」，
#   避免只替二字留下孤字「邸」。otr 那 2 槽之一（s03c_04c）是**无地址梗概槽**（jp 为空），
#   故门控放行空 jp —— 该槽的安全由 locator（idx=）+ 消费方 old_text 断言 + G6 往返共同承担。
for _s in ("ot", "ota", "otr", "otv"):
    RULES.append((_s, "羽田宅", re.compile(r"羽田宅邸?"), "羽田家",
                  lambda jp: ("羽田邸" in jp) or (not jp.strip()),
                  None if _s != "ot" else LESSON + "`羽田邸` 归一「羽田家」（§2.7.4；「羽田宅邸」整词一并替换）",
                  "high"))
# 10 `苍羽女学院` → 苍穹女子学院（otr 1）。§2.7.4 标「低置信」，经用户 2026-09-30 确认沿用现采用值。
RULES.append(("otr", "苍羽女学院", re.compile("苍羽女学院"), "苍穹女子学院",
              lambda jp: "蒼穹女学院" in jp,
              LESSON + "`蒼穹女学院` 沿用「苍穹女子学院」（低置信项经用户确认；我方语料另 8 槽已用该写形）",
              "medium"))

EXPECT = {("ot", "古罗利亚斯"): 22, ("otr", "古罗利亚斯"): 7,
          ("ot", "游隼"): 25, ("otr", "游隼"): 2,
          ("otp", "耳语材料"): 2, ("otv", "细语材质"): 4,
          ("otv", "罗伊希滕"): 2, ("otv", "独立空学院"): 4,
          # 第二组（§2.7.4 整族，合计 31 槽）
          ("ot", "美空学园写形"): 2, ("otr", "美空学园写形"): 8,
          ("otr", "柳木原普利广场"): 3, ("otr", "柳波广场"): 2, ("otv", "柳木原广场"): 1,
          ("ot", "羽田宅"): 8, ("ota", "羽田宅"): 2, ("otr", "羽田宅"): 2, ("otv", "羽田宅"): 2,
          ("otr", "苍羽女学院"): 1}
HEAD = ["source", "file", "locator", "kind", "field", "old_text", "new_text",
        "fix_type", "method", "evidence", "confidence"]


def load_corpus(src):
    rows = []
    p = os.path.join(SCENES, "scene_%s.jsonl" % src)
    for ln in io.open(p, encoding="utf-8"):
        d = json.loads(ln)
        for L in d.get("lines") or []:
            rows.append((d["script"], L))
        for c in d.get("choices") or []:
            rows.append((d["script"], c))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    for r in RULES:                                  # G0
        if not r[3]:
            raise SystemExit("[G0 失败] 规则 %s/%s 未给替换值（禁止静默兜底）" % (r[0], r[1]))

    otr_idx = {}
    d = json.load(io.open(find(OTR_SRC), encoding="utf-8"))
    for e in d["scenes"]:
        for L in e["lines"]:
            otr_idx.setdefault((e["file"], L.get("jp")), []).append(L.get("offset"))

    base_of = {s: base_index(s) for s in ALL_SRC}

    rows, counts, g2, g3, g4, g5 = [], Counter(), [], [], [], []
    for src, label, pat, repl, gate, evid, conf in RULES:
        for script, L in load_corpus(src):
            cn = L.get("cn") or L.get("text_cn") or ""
            jp = L.get("jp") or L.get("text_jp") or ""
            if not cn:
                continue
            loc, _ = locate(src, script, L, otr_idx)
            key = (src, fname(src, script), loc) if loc else None
            # 基准句（**只用于发现槽位**，不是整句 pin）：优先消费方记录的 fix_refs 基准，
            # 否则成品 cn（没被任何表碰过 ⇒ 成品即基准句）。
            text = (base_of[src].get(key) if key else None) or cn
            if not pat.search(text):
                continue
            if gate and not gate(jp):
                (g2 if label == "游隼" else g3).append((src, label, script, jp[:50]))
                continue
            if pat.sub(repl, text) == text:
                continue
            if pat.search(pat.sub(repl, text)):
                g5.append((src, label, script, pat.pattern))
            if loc is None:
                g4.append((src, label, script, jp[:40],
                           len(otr_idx.get((fname("otr", script), jp)) or [])))
            counts[(src, label)] += 1
            rows.append({"source": src, "file": fname(src, script), "locator": loc,
                         "kind": L.get("kind") or "other", "field": "cn",
                         # ★ 词形级替换：old_text = 词形正则，new_text = 替换值（**不是整句**）
                         "old_text": pat.pattern, "new_text": repl, "fix_type": "term_unify",
                         "method": "programmatic",
                         "evidence": evid or "", "confidence": conf,
                         # 以下仅内部用（不写盘，写盘只按 HEAD 列）：模拟结果 + 标签，供 G5b / G6
                         "_sim": pat.sub(repl, text), "_text": text, "_label": label})

    last = {}
    for r in rows:
        if r["evidence"]:
            last[r["source"]] = r["evidence"]
        else:
            r["evidence"] = last.get(r["source"], LESSON + "同上")

    errs = []
    for k, want in EXPECT.items():
        if counts.get(k, 0) != want:
            errs.append("G1 %s/%s 槽数 %d != %d" % (k[0], k[1], counts.get(k, 0), want))
    # G0b 每行 old_text 必须能编译、非空、且**不得匹配空串**（能匹配空串的正则会让 `re.sub` 在每个字符间插值）
    for r in rows:
        try:
            cpat = re.compile(r["old_text"])
        except re.error as e:
            errs.append("G0b old_text 非合法正则：%s %s（%s）" % (r["source"], r["locator"], e))
            continue
        if not r["old_text"].strip() or cpat.search(""):
            errs.append("G0b old_text 为空或可匹配空串（危险）：%s %s %r"
                        % (r["source"], r["locator"], r["old_text"]))
    if g2:
        errs.append("G2 游隼有 %d 槽 JP 不含 ハヤブサ" % len(g2))
    if g3:
        errs.append("G3 有 %d 槽门控未过（JP 不含该家族所需原词/写形）：%s" % (len(g3), g3[:5]))
    if g4:
        errs.append("G4 otr 有 %d 条取不到 locator（offset 非唯一非 None / idx 缺失）：%s" % (len(g4), g4[:3]))
    if g5:
        errs.append("G5 替换后仍残留词形：%s" % g5[:3])
    # G5b 畸形拼接：替换后不得拼出别的词（每家族一条，防「空学园→美空学院园」这类残字）。
    #   判据作用于**模拟替换结果**（`_sim`），不是 `new_text`（后者现在只是替换值）。
    MAL = [re.compile("美空学院(?:院|园|生|府)"),
           re.compile("羽田家(?:邸|宅)"),
           re.compile("柳警广场(?:广|场)"),
           # 「苍穹女子学院学生」是合法中文，故只判**重复后缀**（学院+学/院）
           re.compile("苍穹女子学院(?:学院|院)")]
    mal = [(r["source"], r["locator"], p.pattern)
           for r in rows for p in MAL if p.search(r["_sim"])]
    if mal:
        errs.append("G5b 出现畸形拼接 %d 条：%s" % (len(mal), mal[:3]))
    for r in rows:
        if r["old_text"] == r["new_text"] or not r["locator"]:
            errs.append("G5 行异常：%s/%s" % (r["source"], r["file"]))

    # G6 往返（**独立键 + 独立证据**）：按 `CONSUMER_KEY` 重新定位每一行，然后
    #   ① 复核该槽的 `jp` 仍满足该家族的 **JP 门控**——jp 取自源语料，与生成路径的基准层推导
    #      相互独立；locator 漂移指到别的槽时，那槽的 jp 极难同时命中门控；
    #   ② 该槽的**基准句**必须至少命中一次该行 `old_text`（词形正则）——否则 locator 疑漂移。
    #   ★ 词形级替换后 ② 不再需要「逐字符比整句」：`old_text` 已只是词形正则，与整句无关。
    GATE_OF = dict(((s, l), g) for s, l, p, r, g, e, c in RULES)
    rt = {}
    for src in ALL_SRC:
        for script, L in load_corpus(src):
            loc = consumer_locator(src, script, L, otr_idx)      # ← 独立键，非 locate()
            if not loc:
                continue
            key = (src, fname(src, script), loc)
            base = base_of[src].get(key) or L.get("cn") or ""
            rt.setdefault(key, []).append((base, L.get("jp") or ""))

    for r in rows:
        got = rt.get((r["source"], r["file"], r["locator"]))
        gate = GATE_OF.get((r["source"], r["_label"]))
        if not got:
            errs.append("G6 往返定位失败：%s %s %s" % (r["source"], r["file"], r["locator"]))
            continue
        if gate and not any(gate(jp) for _, jp in got):
            errs.append("G6 定位槽 jp 不满足该家族门控（locator 疑漂移）：%s %s %s"
                        % (r["source"], r["file"], r["locator"]))
        elif not any(re.search(r["old_text"], txt) for txt, _ in got):
            errs.append("G6 定位槽的基准句未命中该行词形（locator 疑漂移）：%s %s %s"
                        % (r["source"], r["file"], r["locator"]))

    # G7 消费方挂接：凡本表出现的 source，其构建器都必须挂载本表、且其「来源门控映射」
    #   覆盖本表出现的**全部** source。两处任一缺失都会造成静默不生效或直接崩：
    #     ① 未挂载 ⇒ 行在表里、消费方没加载，两侧都看不见；
    #     ② 映射缺项 ⇒ 消费方装载时 `CORR_SOURCE_TO_BASE` 查不到 → fail loud（或按旧逻辑静默跳过）。
    CONSUMER_OF = {"ot": "build_scene_ot.py", "otp": "build_scene_otp.py", "ota": "build_scene_ota.py",
                   "otv": "build_scene_otv.py", "otr": "build_scene_jsonl.py", "np": "build_scene_np.py"}
    tbl = os.path.basename(OUT)
    all_src = sorted(set(r["source"] for r in rows))
    for src in all_src:
        b = os.path.join(HERE, CONSUMER_OF[src])
        txt = io.open(b, encoding="utf-8").read()
        if tbl not in txt:
            errs.append("G7 %s 未挂载 %s（该源 %d 行将静默不生效）"
                        % (CONSUMER_OF[src], tbl, sum(1 for r in rows if r["source"] == src)))
    for fn in sorted(set(CONSUMER_OF.values())):
        txt = io.open(os.path.join(HERE, fn), encoding="utf-8").read()
        if tbl not in txt:
            continue                              # 未挂载本表的构建器不受本闸门约束
        blk = txt.split("CORR_SOURCE_TO_BASE", 1)[-1][:600]
        missing = [s for s in all_src if ('"%s"' % s) not in blk]
        if missing:
            errs.append("G7 %s 已挂载 %s，但来源门控映射缺 %s（装载即 fail loud / 该源不生效）"
                        % (fn, tbl, "/".join(missing)))

    if errs:
        print("[闸门失败]")
        for e in errs:
            print("  -", e)
        sys.exit(1)

    def key(r):
        m = re.search(r"(\d+)", r["locator"])
        return (r["source"], r["file"], int(m.group(1)) if m else 0)
    rows.sort(key=key)

    def write(path):
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(HEAD) + "\n")
            for r in rows:
                f.write("\t".join(str(r[c]) for c in HEAD) + "\n")

    if a.check:
        if not os.path.isfile(OUT):
            print("[--check] 产物不存在"); sys.exit(1)
        old = io.open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        write(OUT)
        new = io.open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        print("[--check] %s" % ("0 改动（幂等）PASS" if old == new else "有改动 → 非幂等"))
        sys.exit(0 if old == new else 1)

    write(OUT)
    print("写出 %s（%d 行）" % (os.path.relpath(OUT, PROJ), len(rows)))
    for k in sorted(counts):
        print("   %-4s %-12s %d" % (k[0], k[1], counts[k]))
    print("合计 %d 行" % len(rows))


if __name__ == "__main__":
    main()
