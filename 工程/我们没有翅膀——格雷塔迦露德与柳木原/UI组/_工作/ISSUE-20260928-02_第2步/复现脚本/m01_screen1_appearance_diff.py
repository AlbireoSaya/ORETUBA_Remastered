# -*- coding: utf-8 -*-
r"""m01_screen1_appearance_diff.py —— ★ 外观变更自证（`ISSUE-20260928-02` 第 2 步 · 批次自证）

**要证的事**：把**主代理明确裁决的、有意变更**与**意外变更**分开。判据 = 盘上现值 vs
**`git HEAD`（本批之前的已并入版本）** 的逐元素、逐字段对比。

  · 共有元素：**影响外观/行为的字段**（`kind/x/y/w/h/asset/z/color/opacity/font/align/valign/
    wrap/max_lines/sample/nine/state_assets/action/label/visible_default/line_spacing`）
    ⇒ **每一处差异都必须落在「声明表」里**，否则判失败（＝意外变更）。
    ★ 声明表里的字段若**实际未变**，同样判失败（声明表过期 = 豁免失效，必须报出）。
  · 纯**溯源字段**（`source`）不改像素 ⇒ 单列 informational，但**只允许出现在声明过的元素上**。
  · 新增元素：只允许**无美术热区**，或**声明表里点名的新元素 / 新元素族**。
  · ★ **第 3 批 item 1**：**可见性旗标**（`vis_flag`/`vis_when`）**不在 APPEARANCE_FIELDS 里**（不改像素）
    ⇒ 单列【①b】核对：**外壳件**删除旗标（逐 id 清单 + 计数）为**声明内**；
    **非外壳件**丢旗标 ⇒ 判失败（见 `VISIBILITY_FIELDS` / `LAYER_OWNED_PREFIXES`）。
    ★ **`ISSUE-20260929-02`**：该禁令新增**具名豁免集 `SHELL_FLAG_EXEMPT`**（＝播放/暂停键一对，
    状态互斥用，非层旗标）—— 豁免集**过期**（集内件不再带旗标）同样判失败，防「空壳豁免」。
  · `links`：`pts` 逐点相同、`color`/`w`/`arrow` 相同；只允许 `kind` → `state` 的键名替换。
  · 三个交付样例预设（`screen1`/`screen2`/`ref150`）必须**素净**：不写 `flow_state`、连线全 `normal`、
    `(color,w,arrow)` 恒 `0xFF266080/4/True`。

★★ **`ISSUE-20260928-03` 重钉（批次自证的基线问题 + 新增变异自证）**：
  本脚本是**批次自证** —— 声明表描写的对象是「**本批相对 `git HEAD`**」。此前各批（第 2/3/5 批）的变更
  **已并入 `main`** ⇒ HEAD 现值即含它们 ⇒ 旧声明表整体「过期」（③b 每条都报「声明了却没变」、
  `unused_pat` 报「元素族正则一个都没命中」）⇒ `run_all.py` 第 25 步**恒红**（**与本次数据改动无关**）。
  ⇒ 按本批事实**重新声明**：**本批 `screen1` 的外观/行为字段一处未动**（两处改动只作用于 `--preset states`；
  对 `screen1` 的唯一改动是**屏 `note` 措辞**，而 note 不在判据里）⇒ 声明表为空。
  ⇒ 另加 **③c 变异自证**：在内存副本里注入 2 处字段变异，判据**必须**检出为未声明差异
    —— 证明「未声明差异 0 处」这个结论不是判据恒真的产物。

★★ **第 9 批更正（2026-09-28）—— 上面那条重钉的**前提被实测推翻**，而「恢复声明表」的处置**也是错的****：
  ① `git HEAD` 里那份 `layout/screens/32_flowchart.json` 实测是 **`--preset states` 的产出**
     （126 元素、`flags_default` 含 `fc.state.*`、无 `fc.frag*`），**不是 screen1 变体**
     ⇒ 「历史各批已并入 main、故不构成相对 HEAD 的差异」**不成立**（那是拿 states 当基线）。
     事故与修法（重出产物 + 提交）见 `m06_delivered_sample_ledger.py` 文件头与工程记录 §风险 10。
  ② 但**声明表并不能因此恢复**：本表的对照是 `git HEAD`，而**任何提交都让 HEAD ＝ 盘上**
     ⇒ 「相对 HEAD 的差异」在提交完成后**恒为 0**；表非空即被判「③b 声明表过期」，为空则无证据。
     故两张表**按设计保持为空**（理由见 `DECLARED_CHANGES` 上方注释），跨批总账一律查 `m06`。
  ③ 本脚本收窄为两条职责：**⓪ HEAD 基线健全性（★ 硬失败，不跳过）** 与 **现值侧 ①b/⑥/⑦**。
     硬失败的理由：修复前「跳过」路径让 `run_all` 第 25 步**是绿的却什么都没验** —— 那种绿比红更糟。

**幂等**：只读（`git show` ＋ 读盘）＋ 往 `_out/` 落预设产物（生成物，可覆盖再生）；**不动屏文件**。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260928-02_第2步/复现脚本/m01_screen1_appearance_diff.py"
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
OUT = os.path.join(HERE, "_out")
SCREEN_REL = "layout/screens/32_flowchart.json"
SCREEN = os.path.join(UI, SCREEN_REL)


def load_ledger():
    r"""★ 第 10 批：从 `m06_delivered_sample_ledger.py` **取用「有意变更总账」**。

    为什么这么做（一审 `ISSUE-20260928-04` 打回项的根因修复）：
      `m01` 的对照是 `git HEAD`，而**本批自己的改动在提交前必然与 HEAD 不同** ⇒ `③` 恒报若干
      「未声明差异」⇒ `run_all` 在**审查窗口内确定性红**，「34/34 全绿」这条证据**在提交前拿不到**。
      而「哪些差异是有意的」这件事**已经有唯一的权威落点**——`m06` 的固定基线总账（不随 HEAD 漂移）。
      ⇒ 本脚本不再自带声明表，而是**消费 `m06` 的总账**当「允许 vs HEAD 出现的差异」：
        · 台账里 `old` **未落入 HEAD**（HEAD 值 == old）⇒ 盘上必须 == `new`（本批未提交的改动）；
        · 台账里 `old` **已落入 HEAD**（HEAD 值 == new）⇒ 已合并的旧批，vs HEAD 无差异，正常；
        · HEAD 值既非 `old` 也非 `new` ⇒ 台账与实际不符 ⇒ **判失败**（防台账与盘面脱节）。
      这样一张总账同时服务两个窗口，且**没有任何跳过路径**（既不放宽、也不靠「提交后才绿」）。
    """
    import importlib.util
    p = os.path.join(HERE, "m06_delivered_sample_ledger.py")
    spec = importlib.util.spec_from_file_location("_m06", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return (m.DECLARED, m.DECLARED_NEW_IDS, m.DECLARED_REMOVED_IDS, m.DECLARED_LINKS,
            m.APPEARANCE_FIELDS)


LEDGER, LEDGER_NEW_IDS, LEDGER_REMOVED_IDS, LEDGER_LINKS, APPEARANCE_FIELDS = load_ledger()

# 影响观感 / 行为 ⇒ 差异必须逐条落在声明表里
#   ★ E5 订正（`ISSUE-20260929-04` · S3）：本清单原先**是 `m06` 的副本**（两边各写一份 ⇒ 有漂移风险，
#     `m06` 文件头却写「与 `m01` 保持同一份清单」）。现改为**从 `m06` 直接取用**（上方 `load_ledger`
#     一并返回）⇒ **真正单一来源**：此后只改 `m06` 的 `APPEARANCE_FIELDS`，本脚本自动同源。
#     同批补入的 4 个字段（`vis_flag`/`vis_when`/`layer`/`dynamic`）即由此自动生效。
# 纯溯源（不改像素）⇒ informational，但只允许出现在声明过的元素上
PROVENANCE_FIELDS = ["source"]

# ══════════════════════════════════════════════════════════════════════
# ★★ 第 10 批：**自带声明表废弃 → 直接消费 `m06` 的「基线总账」**（见 `load_ledger`）
# ══════════════════════════════════════════════════════════════════════
#   ★★ 第 9 批收口时订正（2026-09-28）★★
#   早先几轮反复「重钉」本表，是因为把它当成了「交付样例的有意变更台账」；**那是用错了仪器**：
#     · 本表的对照是 `git HEAD`，而**任何提交都让 HEAD ＝ 盘上** ⇒ 「相对 HEAD 的差异」在提交之后
#       **恒为 0**，表非空就立刻被判「③b 声明表过期：声明了却没变」；表为空则是恒 0 差异 ——
#       两种写法都**产不出证据**。跨批的台账必须钉在**固定引用**上，那是 `m06` 的职责。
#     · 本批实测还证明：HEAD 这个靶子**会坏**。初版提交 `98b43dd` 把 **`--preset states` 的产出**
#       提进了 `layout/screens/32_flowchart.json`（126 元素、含 `_dim`/`_read`/`_new`、无 `fc.frag*`），
#       于是「相对 HEAD 的差异」变成了「拿 states 当 screen1」的一堆**假差异**，而为了让它变绿，
#       只会去追认那些假差异（上一版注释与表就是这么长出来的）。事故与修法见 `m06` 文件头与
#       工程记录 §风险 10。
#   ⇒ 分工（**第 10 批定型**，此后**不要再重钉任何自带声明表**）：
#      · `m06_delivered_sample_ledger.py`：**对照固定引用 `ef68dcf`**，管「交付样例自基线以来的
#        有意变更总账」（逐元素/逐字段/连线/屏级 + 变异自证）—— 新批有意图改动就往 `m06` 追加一条；
#      · 本脚本：管 **⓪ 提交面健全性（硬失败）** ＋ **③ 账内/未声明比对（消费 `m06` 总账）**
#        ＋ **③b 总账 vs HEAD 一致性** ＋ **现值侧检查（①b / ⑥ / ⑦）**。
#        ★ 关键改动：`③` 里「哪些差异是有意的」**取 `m06` 的 `DECLARED`** ⇒ **未提交窗口内也能全绿**
#          （此前 `③` 恒把本批未提交的改动报成「未声明」⇒ `run_all` 在审查窗口内**确定性红**，
#           「34/34 全绿」这条证据根本拿不到）。
#   · 第 2/3/5·7 批的历史变更（7 件占位换真件、独立层六族、组名底托）**不属于本表语义**
#     （它们早在基线之内），其内容留档在 `复现脚本/README.md` 的「第 2/3/5 批落点小结」
#     与 `layout/_schema.md` 的静态件表。
# `fields` = 允许与 HEAD 不同的字段（**必须真的不同**，否则报「声明表过期」）
# `appearance` = 是否影响静止态观感（用于外观变化清单）
# `reason` = 依据
DECLARED_CHANGES = {}
#   ★★ 第 9 批（主代理收口）：**本表按设计为空，且必须为空** ★★
#   理由（一条硬事实）：本表的对照是 `git HEAD`，而**任何提交都会让 HEAD ＝ 盘上** ⇒
#   「相对 HEAD 的差异」在**提交完成之后恒为 0** ⇒ 表只能是空的（非空即立刻被判「③b 声明表过期：
#   声明了却没变」）。上一版曾把它恢复成 `{fc.frag6.0007_tx: sample}` + 8 条元素族正则，
#   前提是「HEAD 坏掉（＝ states 档）」这个**不合法状态**；基线一旦修好，那些族**两侧都在**、
#   那条 `sample` **两侧相同** ⇒ 恢复出来的表必然过期（`unused_pat` 与 ③b 齐报），
#   而它「看起来在验」的那批差异其实**一条都不存在**。
#   ⇒ 第 9 批起，**交付样例的「有意变更总账」由 `m06_delivered_sample_ledger.py` 承担**
#     （固定引用 `ef68dcf`，不随 HEAD 漂移，逐元素/逐字段/连线/屏级四节 + 变异自证）。
#     `m01` 自己的职责收窄为两条，都已生效：**①「提交进去的那份是不是交付样例」（⓪ 硬失败）**
#     与 **② 现值侧检查（①b 旗标口径 / ⑥ 三档素净 / ⑦ 清单）**。
#   · 旧声明表所记载的真实历史（第 2 批 7 件占位换真件 / 第 3 批独立层六族 / 第 5·7 批组名底托）
#     **不属于本表的语义**（它们早已在基线之内、不是「相对 HEAD 的差异」），其内容仍在
#     `复现脚本\README.md` 的「第 2/3/5 批落点小结」与 `layout/_schema.md` 的静态件表里留档。
# `fields` = 允许与 HEAD 不同的字段（**必须真的不同**，否则报「声明表过期」）
# `appearance` = 是否影响静止态观感（用于外观变化清单）
# `reason` = 依据
# ★ 声明内的**新增元素**（本批：无）
DECLARED_NEW_ELEMENTS = {}
# ★ 声明内的**新增元素族**（正则；本批：无 —— 第 2/3/5·7 批那些族早已在 `HEAD` 之内，
#   对本表而言**不是「相对 HEAD 的差异」**；其留档见上方注释与 `复现脚本/README.md`）
DECLARED_NEW_PATTERNS = []
# ★ 声明内的**可见性旗标删除**（★ 第 3 批 item 1）：外壳件不再写 `vis_flag`/`vis_when`。
#   判据：HEAD 上有 `fc_layer`+`main` 而现值没有，且 id **不属图内容层**（前缀表见生成器 `LAYER_OWNED_PREFIXES`）。
#   这类差异**不在 APPEARANCE_FIELDS 里**（不改变像素），故单列一节核对（逐 id 清单 + 计数）。
VISIBILITY_FIELDS = ("vis_flag", "vis_when")
LAYER_OWNED_PREFIXES = ("fc.node.", "fc.branch.", "fc.label.", "fc.entry.", "fc.frag")

# ★★ `ISSUE-20260929-02`（右栏大改）：外壳件层旗标禁令的**具名豁免集**（**状态互斥对**，非层旗标）
#   本批右栏新增「播放键 / 暂停键」一对（`fc.pbkick` / `fc.pbkick_pause`）：同矩形、同 z、
#   靠屏级 flag `fc_replay` 的 `"play"` / `"pause"` **互斥显示**（用户 2026-09-29 指令 1+3）。
#   ⚠ **为什么可以豁免**：`fc_replay` **不是层旗标** —— 它不参与 `fc_layer` 的层切换，
#      初值 `"play"` 在**任何层**都成立 ⇒ 播放键恒可见。本禁令要防的风险（「外壳件随层隐藏，
#      把深墨色组名/网格画到无底图的透明或黑画面上」，见 `E3_frag_frag1.png`）**不存在**。
#   ⚠ **豁免集必须保持「最小且在用」**：集内的件若不再带旗标 ⇒ 判「豁免集过期」（见 ①b），
#      以免留下一个什么都放行的空壳豁免。集外仍**严格拒绝**（生成器侧同名常量 `STATIC_FLAG_EXEMPT`
#      在 `STATIC_ELEMENTS_JSON` 载入处与 `build()` 落盘前两处自检同时收紧）。
#   ★★ 第 15 批（`ISSUE-20260930-02`）：新增 **6 件 `fc.intro_*`**（章节详情浮层）—— 理由同款：
#      它们挂的是屏级 flag **`fc_intro`**（`"closed"`/`"open"`）、**不是层旗标**（不参与 `fc_layer`
#      切层），初值在**任何层**都成立 ⇒ 浮层开合与「主干/番外独立层」切换互不干扰。
#      ★★ 第 15 批 · 第 2 轮（用户裁定 5）：**再新增 2 件** —— 浮层**关闭件** `fc.intro_close`
#      （按钮）/ `fc.intro_close_hit`（热区），同挂 `fc_intro`、理由同上。
#      （`fc.p_plus`/`fc.p_plus_hit` **不带** `vis_flag` ⇒ 不进本集。本集必须**逐字等于**
#       生成器 `STATIC_FLAG_EXEMPT`，否则 ①b 的反向自证「原始谓词命中 == 豁免集」会报失败。）
SHELL_FLAG_EXEMPT = {"fc.pbkick", "fc.pbkick_pause",
                     "fc.intro_scrim", "fc.intro_scrim_hit", "fc.intro_bg",
                     "fc.intro_panel_hit", "fc.intro_title_tx", "fc.intro_text_tx",
                     "fc.intro_close", "fc.intro_close_hit"}

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print("      ✗ %s" % msg)


# ★ 第 11 批第 4 轮（合并验证时实测）：**盘面 md5 必须按 LF 规范化后再比**。
#   金标（`GOLDEN` / `PRESET_TABLE` / `layout\_schema.md` 金标表）按定义是 **LF 规范化值**
#   （`_schema.md` 金标表明载：「LF 规范化值；盘面 CRLF 因 `core.autocrlf=true`，字节 md5 …」）。
#   而**新检出的 worktree 是 CRLF** ⇒ 直接对盘面字节取 md5 会得到另一个值（同一份内容：
#   LF `a84a1876…` vs CRLF `a7a47fb0…`）⇒ 在 CRLF 检出面上**假失败**，还会给出误导性提示
#   （「多半是上一次跑了别的预设」），诱导人无谓地重跑生成器。
#   （`git show <rev>:` 取到的是 git 存储形态＝LF，故基线侧本来就没有这个问题。）

def lf_bytes(b):
    """把盘面字节按 **LF 规范化**（`core.autocrlf=true` 下检出面可能是 CRLF）——见上方注。"""
    return b.replace(b"\r\n", b"\n")

def git_show_head(path_rel):
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                         capture_output=True, text=True).stdout.strip()
    rel = os.path.relpath(path_rel, top).replace("\\", "/")
    r = subprocess.run(["git", "show", "HEAD:" + rel], cwd=top, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[FAIL] git show HEAD:%s 失败：%s" % (rel, r.stderr[-300:]))
    return json.loads(r.stdout)


def brief(v):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 46 else s[:43] + "…"


def check_sample_presets():
    r"""★ 三个交付样例预设必须「素净」：不写 flow_state、连线全 normal、色宽箭头＝上一批值。"""
    print("\n【⑥ 三个交付样例预设的「素净」自证（不写 flow_state、连线全 normal、色宽箭头＝上一批值）】")
    for preset in ("screen1", "screen2", "ref150"):
        out = os.path.join(OUT, "32_flowchart.%s.json" % preset)
        r = subprocess.run([sys.executable, os.path.join(UI, "工具", "gen_flow_layout.py"),
                            "--preset", preset, "--out", out],
                           cwd=UI, capture_output=True, text=True)
        if r.returncode != 0:
            fail("生成 %s 失败：%s" % (preset, r.stderr[-200:]))
            continue
        scr = json.load(open(out, encoding="utf-8"))
        n_fs = [e["id"] for e in scr["elements"] if "flow_state" in e]
        sts = sorted({lk.get("state") for lk in scr["links"]})
        geo = sorted({(lk["color"], lk["w"], lk["arrow"]) for lk in scr["links"]})
        ok = (not n_fs) and sts == ["normal"] and geo == [(0xFF266080, 4, True)]
        print("      %-8s 带 flow_state 元素 %d 个 ｜ links.state %s ｜ (color,w,arrow) %s ⇒ %s"
              % (preset, len(n_fs), sts, ["0x%08X/%d/%s" % g for g in geo], "✓" if ok else "✗"))
        if not ok:
            fail("%s 不是「素净交付样例」：flow_state=%s / states=%s / geo=%s" % (preset, n_fs, sts, geo))


def ensure_screen1_on_disk():
    r"""★ 前置守卫：m01 的对照对象是**交付样例 screen1**，盘上若不是它，本自证毫无意义。

    做法：读生成器模块取 `GOLDEN['screen1']`，与盘上 md5 比对；不一致 ⇒ 跑一次**无参**生成器
    （它有金标自检 ⇒ 只可能写出交付样例），再重新读。故本脚本是**幂等**的：
    无论盘上是 states / frag / ref150 变体，跑完 m01 后盘上都回到 screen1。
    """
    import hashlib
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_gfl", os.path.join(UI, "工具", "gen_flow_layout.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    want = mod.GOLDEN["screen1"][0]
    got = hashlib.md5(lf_bytes(open(SCREEN, "rb").read())).hexdigest()
    if got == want:
        print("  盘上 32_flowchart.json = 交付样例 screen1（md5 %s）✓" % got)
        return
    print("  ⚠ 盘上 32_flowchart.json md5=%s ≠ 交付样例 %s（多半是上一次跑了别的预设，"
          "如派单九条命令的最后一条 `--preset frag`）⇒ **先跑一次无参生成还原**" % (got, want))
    r = subprocess.run([sys.executable, os.path.join(UI, "工具", "gen_flow_layout.py")],
                       cwd=UI, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[FAIL] 无参生成失败：%s" % r.stderr[-400:])
    got2 = hashlib.md5(lf_bytes(open(SCREEN, "rb").read())).hexdigest()
    print("  还原后 md5 = %s %s" % (got2, "✓" if got2 == want else "✗ 仍不一致"))
    if got2 != want:
        raise SystemExit("[FAIL] 还原失败：期望 %s，实为 %s" % (want, got2))


def diff_fields(om, nm):
    r"""逐元素逐字段比对「影响外观/行为的字段」，按 **`m06` 的总账** 分成（声明内, 未声明, 值不符）。

    第 10 批起不再用本脚本自带的声明表（那玩意儿在提交窗口内必然过期或为空），改为消费 `m06`：
      · 台账某条 `(id, 字段) = (old, new)`：若 `om`（HEAD）值 == `old` 且 `nm`（盘上）值 == `new` ⇒ 计入**声明内**；
        若两侧值与台账都不符 ⇒ 计入 **值不符**（台账与盘面脱节，必须报出来）。
      · 未在台账里的差异 ⇒ **未声明**（失败）。

    纯函数（供**变异自证**对内存副本调用）⇒ 可证判据非恒真。
    """
    declared_hits, undeclared, mismatch = {}, [], []
    for i in sorted(set(om) & set(nm)):
        for k in APPEARANCE_FIELDS:
            if om[i].get(k) == nm[i].get(k):
                continue
            entry = LEDGER.get(i, {}).get(k)
            if entry is None:
                undeclared.append((i, k, om[i].get(k), nm[i].get(k)))
            elif entry[0] == om[i].get(k) and entry[1] == nm[i].get(k):
                declared_hits.setdefault(i, []).append((k, om[i].get(k), nm[i].get(k)))
            else:
                mismatch.append((i, k, om[i].get(k), nm[i].get(k), entry))
    return declared_hits, undeclared, mismatch


def mutate_selfcheck(om, nm):
    r"""★ `ISSUE-20260928-03` 新增：**变异自证** —— 证明 ③ 的判据不是恒真。

    本批 `DECLARED_CHANGES` 为空，「未声明差异 0 处」这个结论只有当判据**确实能发现差异**时才有意义。
    做法：在**内存副本**里把第一个共有元素的 `x`（或若干字段）改 1px ⇒ 复算必须报出**未声明差异**。
    不落任何盘。
    """
    print("\n【③c ★ 变异自证（证明 ③ 非恒真）】")
    import copy
    mut = copy.deepcopy(nm)
    ids = sorted(set(om) & set(mut))
    if not ids:
        fail("变异自证无法构造：没有共有元素")
        return
    tgt = ids[0]
    mut[tgt] = dict(mut[tgt])
    mut[tgt]["x"] = (mut[tgt].get("x") or 0) + 1          # 几何挪 1px（必属未声明）
    mut[tgt]["asset"] = "__mut__.png"                     # 换件（必属未声明）
    _dh, und, _mm = diff_fields(om, mut)
    tagged = [u for u in und if u[0] == tgt]
    print("      注入：`%s` 的 `x` +1px、`asset` 换成 `__mut__.png` ⇒ 复算报未声明差异 **%d 处**（其中本元素 %d 处）%s"
          % (tgt, len(und), len(tagged), "✓ 判据非恒真" if len(tagged) >= 2 else "✗ **判据恒真**"))
    if len(tagged) < 2:
        fail("变异自证失败：注入 2 处字段变异后判据未全部检出（③ 恒真、无判别力）")


def main():
    old = git_show_head(SCREEN)
    print("=" * 78)
    print("m01 · 外观变更自证（git HEAD 版 vs 盘上现值）——「声明内」与「意外」分开列")
    print("=" * 78)
    ensure_screen1_on_disk()
    new = json.load(open(SCREEN, encoding="utf-8"))
    om = {e["id"]: e for e in old["elements"]}
    nm = {e["id"]: e for e in new["elements"]}
    print("=" * 78)
    print("  元素数：HEAD %d → 现行 %d" % (len(old["elements"]), len(new["elements"])))

    # ── ⓪ ★ 第 9 批：**HEAD 基线健全性闸门（硬失败）** ──────────────────
    #   m01 的语义是「盘上 screen1 ↔ 上一次**同为 screen1** 的提交」。若 HEAD 里那份屏文件
    #   根本不是 screen1 变体（本批实测：`98b43dd` 把 **`--preset states` 的产出**提交了进去），
    #   则 ①②③④⑤ 全部失去判别力（会把 states 专有的 `_dim`/`_read`/`_new` 报成「被删除」、
    #   把 screen1 的独立层族报成「意外新增」）。
    #   ★ 判**硬失败**，不跳过：早先「不健康就跳过」的写法会让闸门**恰好在真出事的方向上失效**
    #   （修复前 `run_all` 第 25 步是绿的，却什么都没验 —— 那种绿比红更糟）。
    #   ★ 「交付样例自基线以来的**内容总账**」不在这里查，而在 `m06_delivered_sample_ledger.py`
    #   （对照**固定引用**、不随 HEAD 漂移）；本节的职责只是「**提交进去的那份是不是交付样例**」。
    def _looks_like_screen1(doc):
        fl = doc.get("flags_default") or {}
        if any(str(k).startswith("fc.state.") for k in fl):
            return False, "flags_default 含逐节点运行态键 `fc.state.*`（那是 `states` 档的特征）"
        if not any(e["id"].startswith("fc.frag") for e in doc["elements"]):
            return False, "屏内没有 `fc.frag*` 族（screen1 应含 6 组独立层）"
        return True, ""

    baseline_ok, why = _looks_like_screen1(old)
    if not baseline_ok:
        fail("HEAD 基线不健全：git HEAD 版 `%s` **不是 screen1 变体**（%s）⇒ 站上不合法的交付样例"
             "（第 ①②③③b④⑤ 节的比对一并失去判别力）。**修法**：跑一次无参 "
             "`python 工具/gen_flow_layout.py`，把重生成的 `layout/screens/32_flowchart.json` "
             "（含同批 `layout/ui_layout.json`、`krkr/game/ui_layout.tjs`、`复刻/ui_layout.js`）"
             "提交，使 HEAD 恢复为交付样例" % (SCREEN_REL, why))
    else:
        print("  HEAD 基线健全（含 `fc.frag*` 族、无 `fc.state.*`）✓")

    # ── ① 新增元素 ────────────────────────────────────────────────
    #   ★ 第 11 批（`ISSUE-20260929-02`）：与 `③` 同源 —— 「哪些增删是有意的」**取 `m06` 总账**
    #     （`LEDGER_NEW_IDS` / `LEDGER_REMOVED_IDS`），本脚本自带的 `DECLARED_NEW_ELEMENTS` 仍为空
    #     （理由同 `③`：提交后相对 HEAD 的增删恒为 0）。这样**审查窗口内也能全绿**，且不需要任何跳过路径。
    added = [i for i in nm if i not in om] if baseline_ok else []
    removed = [i for i in om if i not in nm] if baseline_ok else []
    print("\n【① 新增元素】%d 件：%s" % (len(added), added if baseline_ok else "（基线不健全 ⇒ 跳过）"))
    print("【② 删除元素】%d 件%s" % (len(removed), "：" + str(removed) if removed else "（无 ✓）"))
    bad_rm = [i for i in removed if i not in LEDGER_REMOVED_IDS]
    for i in removed:
        if i in LEDGER_REMOVED_IDS:
            print("      %-16s 总账内删除 ✓ —— %s" % (i, LEDGER_REMOVED_IDS[i]))
    if bad_rm:
        fail("有元素被删除（且未在 `m06` 总账内追认）：%s" % bad_rm)
    n_pat = 0
    for i in added:
        if i in LEDGER_NEW_IDS:
            print("      %-16s 总账内新增元素 ✓ —— %s" % (i, LEDGER_NEW_IDS[i]))
        elif i in DECLARED_NEW_ELEMENTS:
            print("      %-16s 声明内新元素 ✓ —— %s" % (i, DECLARED_NEW_ELEMENTS[i]))
        elif nm[i].get("kind") == "hit":
            print("      %-16s 无美术热区 ✓（kind=hit）" % i)
        else:
            hit_pat = next(((rx, why) for rx, why in DECLARED_NEW_PATTERNS if re.match(rx, i)), None)
            if hit_pat is not None:
                n_pat += 1
                print("      %-16s 声明内新元素**族** ✓（%s）—— %s" % (i, hit_pat[0], hit_pat[1]))
            else:
                fail("新增元素 %s 既非 `m06` 总账内新元素 / 声明内新元素族、也非热区（kind=%s）⇒ 疑似意外新增"
                     % (i, nm[i].get("kind")))
    print("      （其中 %d 件命中 `DECLARED_NEW_PATTERNS` 的元素族声明）" % n_pat)
    stale_new = [i for i in DECLARED_NEW_ELEMENTS if i not in added]
    if stale_new:
        fail("声明表过期：声明的新元素并不存在：%s" % stale_new)
    if not baseline_ok:
        print("      元素族声明 %d 条：**基线不健全 ⇒ 命中判定跳过**（见 ⓪ 节；基线修好后自动生效）"
              % len(DECLARED_NEW_PATTERNS))
    else:
        unused_pat = [rx for rx, _w in DECLARED_NEW_PATTERNS
                      if not any(re.match(rx, i) for i in added)]
        if unused_pat:
            fail("声明表过期：以下元素族正则**一个都没命中**：%s" % unused_pat)
        else:
            print("      %d 条元素族声明全部有命中 ✓" % len(DECLARED_NEW_PATTERNS))

    # ── ①b ★ 第 3 批 item 1：**外壳件不参与层旗标**（逐 id 清单 + 计数）────────
    #   ⚠️ 对照基线说明：本脚本的 HEAD 基线是**上一批并入 main 时的版本**（比第 2 批早），
    #      故「外壳件由有旗标 → 无旗标」这一步在 HEAD↔现值上**看不出**（HEAD 侧本来也没有旗标）。
    #      ⇒ 本节按**现值口径**判（这才是本批的硬约束）：任何**非图内容层**元素都不得带旗标；
    #        并如实登记「相对 HEAD 新增旗标的件」全部落在图内容层内（含第 2 批的 fc.node/entry/label）。
    print("\n【①b 可见性旗标（第 3 批 item 1：外壳件不参与层旗标）】")
    # ★ `ISSUE-20260929-02`：先取**原始谓词**的命中集（不做任何豁免），再减去具名豁免集
    #   —— 保住「原始判据仍有判别力」这一事实（豁免集里的件必须恰好等于被豁免的那几件，
    #   多一件少一件都判失败，见下方两条）。
    shell_flagged_raw = sorted(i for i in nm
                               if not i.startswith(LAYER_OWNED_PREFIXES)
                               and any(k in nm[i] for k in VISIBILITY_FIELDS))
    shell_flagged = [i for i in shell_flagged_raw if i not in SHELL_FLAG_EXEMPT]
    shell_exempt_hit = sorted(i for i in shell_flagged_raw if i in SHELL_FLAG_EXEMPT)
    content_flagged = sorted(i for i in nm
                             if i.startswith(LAYER_OWNED_PREFIXES)
                             and any(k in nm[i] for k in VISIBILITY_FIELDS))
    content_unflagged = sorted(i for i in nm
                               if i.startswith(LAYER_OWNED_PREFIXES)
                               and not any(k in nm[i] for k in VISIBILITY_FIELDS))
    gained = sorted(i for i in set(om) & set(nm)
                    if not any(k in om[i] for k in VISIBILITY_FIELDS)
                    and any(k in nm[i] for k in VISIBILITY_FIELDS))
    lost = sorted(i for i in set(om) & set(nm)
                  if any(k in om[i] for k in VISIBILITY_FIELDS)
                  and not any(k in nm[i] for k in VISIBILITY_FIELDS))
    print("      外壳件（非图内容层）带旗标：原始谓词 **%d 件** ⇒ 减豁免集后 **%d 件违规**%s"
          % (len(shell_flagged_raw), len(shell_flagged),
             "（✓ 外壳不参与层旗标）" if not shell_flagged else " ← **违规**"))
    if shell_flagged_raw:
        print("        原始命中：%s" % "、".join(shell_flagged_raw))
    print("        具名豁免集 `%s` 命中 **%d 件**：%s"
          % ("/".join(sorted(SHELL_FLAG_EXEMPT)), len(shell_exempt_hit),
             "、".join(shell_exempt_hit) if shell_exempt_hit else "（无）"))
    if shell_flagged:
        print("        %s" % "、".join(shell_flagged))
        fail("外壳件不得带 vis_flag/vis_when（第 3 批 item 1）：%s" % shell_flagged)
    # ★ 豁免集的**过期检测**（防「空壳豁免」）——豁免集里的件必须真的带旗标
    stale_exempt = sorted(i for i in SHELL_FLAG_EXEMPT if i not in shell_flagged_raw)
    if stale_exempt:
        fail("豁免集过期：`SHELL_FLAG_EXEMPT` 声明豁免 %s，但它并未带 vis_flag/vis_when"
             "（或元素已不存在）⇒ 删除该条，否则豁免变成空壳" % stale_exempt)
    # ★ 反向自证（★ 第 11 批收口 · 一审阻断项）：**必须是真断言**。
    #   一审实测原写法 `[i for i in shell_flagged_raw if i not in set()]` 里 `set()` 为空集 ⇒
    #   `i not in set()` **恒真** ⇒ 那个条件恒成立，只能打印、永远不能失败（「看着在做自证、
    #   其实没有牙齿」）。现改为真断言：**原始谓词的命中集必须恰等于豁免集** ——
    #   多一件 ⇒ 有集外件被放行（禁令被稀释）；少一件 ⇒ 豁免集变空壳（上面的过期检测已报，
    #   此处再兜一层）。这样「豁免是减法、集外零放行」这句话才被机检住。
    if SHELL_FLAG_EXEMPT:
        if set(shell_flagged_raw) != set(SHELL_FLAG_EXEMPT):
            fail("反向自证失败：原始谓词命中 %s ≠ 豁免集 %s ⇒ 有集外件被放行 / 集内件漏判"
                 % (shell_flagged_raw, sorted(SHELL_FLAG_EXEMPT)))
        else:
            print("        反向自证：原始谓词命中 == 豁免集（%d 件，%s）⇒ 豁免是**减法**、集外零放行 ✓"
                  % (len(shell_flagged_raw), "、".join(shell_flagged_raw)))
    print("      图内容层（%s 前缀）带旗标 %d 件 ／ 缺旗标 **%d 件**%s"
          % ("/".join(x.rstrip(".") for x in LAYER_OWNED_PREFIXES), len(content_flagged),
             len(content_unflagged), "✓" if not content_unflagged else " ← **违规**"))
    if content_unflagged:
        fail("图内容层件缺 vis_flag/vis_when（层归属未声明）：%s" % content_unflagged)
    gained_bad_cand = [i for i in gained if not i.startswith(LAYER_OWNED_PREFIXES)]
    gained_exempt = [i for i in gained_bad_cand if i in SHELL_FLAG_EXEMPT]
    bad_gain = [i for i in gained_bad_cand if i not in SHELL_FLAG_EXEMPT]
    print("      相对 HEAD：新增旗标 %d 件（图内容层 %d 件 + 豁免集 %d 件）｜ 删除旗标 %d 件"
          % (len(gained), len(gained) - len(gained_bad_cand), len(gained_exempt), len(lost)))
    if gained_exempt:
        print("        豁免集内新增旗标（合法）：%s" % "、".join(gained_exempt))
    if bad_gain:
        fail("有**外壳件**新增了层旗标（第 3 批口径相反）：%s" % bad_gain)
    print("      依据：外壳件（视口/迷你地图/滚条/页签/标题牌/关闭/付箋/回放/进入本章/右栏详情）"
          "是**两种层共用的舞台**，随层隐藏会让组名与网格画在无底图的透明/黑画面上（`E3_frag_frag1.png`）。")

    if baseline_ok:
        # ── ③…⑤ 以 **git HEAD** 为对照；「哪些差异是有意的」由 `m06` 的总账给出（见 `load_ledger`）──
        # ── ③ 影响外观/行为的字段差异（账内 vs 意外）──────────────────
        declared_hits, undeclared, mismatch = diff_fields(om, nm)
        n_hit = sum(len(v) for v in declared_hits.values())
        print("\n【③ 影响外观/行为的 %d 个字段】账内（`m06` 总账）差异 %d 处 ／ **未声明差异 %d 处** ／ 值不符 %d 处"
              % (len(APPEARANCE_FIELDS), n_hit, len(undeclared), len(mismatch)))
        for i in sorted(declared_hits):
            for k, a, b in declared_hits[i]:
                print("      账内    %-18s %-12s %s → %s" % (i, k, brief(a), brief(b)))
        for i, k, a, b in undeclared:
            fail("未声明变更 %s.%s：%s → %s" % (i, k, brief(a), brief(b)))
        for i, k, a, b, e in mismatch:
            fail("总账值不符 %s.%s：账记 %s → %s，实际（HEAD→盘上）%s → %s"
                 % (i, k, brief(e[0]), brief(e[1]), brief(a), brief(b)))

        # ── ③b 总账 vs HEAD 一致性（★ 这是能在**未提交窗口**工作的关键）─────────
        #   台账里 `old` 尚未落入 HEAD（HEAD == old）⇒ 盘上必须 == `new`；
        #   已落入 HEAD（HEAD == new）⇒ 本批之前的旧改动，无待验差异；
        #   HEAD 既非 old 也非 new ⇒ 台账与盘面脱节 ⇒ 判失败。
        print("\n【③b 总账 vs HEAD 一致性（`old` 未落入 HEAD ⇒ 盘上必须 == `new`）】")
        for i in sorted(LEDGER):
            for k in sorted(LEDGER[i]):
                old_v, new_v, _why = LEDGER[i][k]
                hv = om.get(i, {}).get(k)
                dv = nm.get(i, {}).get(k)
                if hv == new_v:
                    print("      已落地  %-18s %-12s（HEAD ＝ 账内 new ⇒ 无待验差异）" % (i, k))
                elif hv == old_v and dv == new_v:
                    print("      待落地  %-18s %-12s %s → %s ✓" % (i, k, brief(old_v), brief(new_v)))
                elif hv == old_v:
                    fail("总账待落地但盘上不符 %s.%s：HEAD=%s ｜ 账内 new=%s ｜ 盘上=%s"
                         % (i, k, brief(hv), brief(new_v), brief(dv)))
                else:
                    fail("总账与 HEAD 都不符 %s.%s：HEAD=%s 既非账内 old=%s 也非 new=%s"
                         % (i, k, brief(hv), brief(old_v), brief(new_v)))
        print("      总账：%d 个元素 / %d 个字段（落点＝`m06_delivered_sample_ledger.py` 的 `DECLARED`）"
              % (len(LEDGER), sum(len(v) for v in LEDGER.values())))

        mutate_selfcheck(om, nm)

        # ── ④ 纯溯源字段（不改像素）─────────────────────────────────
        prov = [(i, k) for i in sorted(set(om) & set(nm)) for k in PROVENANCE_FIELDS
                if om[i].get(k) != nm[i].get(k)]
        print("\n【④ 纯溯源字段 `source`（不影响像素）】%d 处：%s" % (len(prov), [i for i, _k in prov]))
        bad_prov = [i for i, _k in prov if i not in LEDGER]
        if bad_prov:
            fail("未声明元素出现 `source` 漂移：%s" % bad_prov)

        # ── ⑤ links ─────────────────────────────────────────────────
        ol, nl = old["links"], new["links"]
        print("\n【⑤ 连线】HEAD %d 条 → 现行 %d 条" % (len(ol), len(nl)))
        if len(ol) != len(nl):
            fail("连线条数变了：%d → %d" % (len(ol), len(nl)))
        same_pts = all(ol[k]["pts"] == nl[k]["pts"] for k in range(min(len(ol), len(nl))))
        print("      `pts` 逐点相同：%s" % ("✓" if same_pts else "✗"))
        if not same_pts:
            fail("`pts` 有变化")
        chg = [(ol[k].get("kind"), nl[k].get("state"), ol[k]["color"], nl[k]["color"],
                ol[k]["w"], nl[k]["w"], ol[k]["arrow"], nl[k]["arrow"])
               for k in range(min(len(ol), len(nl)))
               if (ol[k]["color"], ol[k]["w"], ol[k]["arrow"]) != (nl[k]["color"], nl[k]["w"], nl[k]["arrow"])]
        print("      `color`/`w`/`arrow` 变化 %d 处%s" % (len(chg), ("：" + str(chg)) if chg else "（无 ✓）"))
        if chg:
            fail("有连线的色/宽/箭头变化")
        keys = sorted({k for lk in nl for k in lk})
        print("      现行 links 键集：%s（`kind` 已消失 ⇒ %s）"
              % (keys, "✓" if "kind" not in keys and "state" in keys else "✗"))

    else:
        print("\n【③–⑤ 相对 HEAD 的字段/连线比对】**已跳过**（HEAD 基线不健全，见上方 ⓪ 节警告）")
        print("      现值侧检查（①b 旗标口径 / ⑥ 素净 / ⑦ 清单）不受影响，照常执行。")
    check_sample_presets()

    # ── ⑦ ★ 「外观变化清单」（第 9 批收口：口径改由 m06 的固定基线总账承担）──────────
    print("\n【⑦ 「外观变化清单」（交付样例 `screen1`）—— 本批由 `m06` 的**固定基线总账**给出】")
    print("      **本批（第 8 批侧）**：`_dim` 由 `rect` 改 `image`、新增 `_read` 已读对勾 ——"
          "**只作用于 `--preset states`**（`screen1`/`screen2`/`ref150`/`frag` 不写 `flow_state`"
          "⇒ 不产 `_dim`/`_new`/`_read`）⇒ 那四档的元素内容与行为字段一处未动。"
          "机检见 `m02_states_frag_variants.py`【A】（`_dim`/`_read`）与【E】。")
    print("      **本批（第 9/10 批侧）**：交付样例 `screen1` 的**有意变更累计 3 处**（均取自 `m06` 总账）："
          "`fc.frag6.0007_tx.sample`（第 9 批：单行 255px → 两行）、`fc.frag4.0008_tx.sample` 与"
          "`fc.frag4.0009_tx.sample`（第 10 批：「零间隙边界簇」补硬断行）。**`m06` 是唯一权威落点**，"
          "`fc.frag6.0007_tx.sample`（单行 255px → 两行 122/133px，「已读对勾」不变量）。"
          "该笔与「自第 2 批交付以来的全部有意变更」由 **`m06_delivered_sample_ledger.py`**"
          "（对照**固定引用** `ef68dcf`）逐元素/逐字段/连线/屏级四节机检，并带变异自证。")
    print("      ★ ★ **第 9 批订正（两处作废的说法）**：")
    print("        ① 旧文「历史各批已并入 `main` ⇒ 本表重钉为空」——**前提错误**：实测 `git HEAD` 里"
          "那份屏文件是 **`--preset states` 的产出**（126 元素、含 `_dim`/`_read`/`_new`、无 `fc.frag*`），"
          "**不是 screen1 变体**（事故与修法见 `m06` 文件头与工程记录 §风险 10）。")
    print("        ② 由此**本表必须为空**：任何提交都让 `HEAD` ＝ 盘上 ⇒ 本表的差异恒为 0；"
          "「历史各批的变更」**不属于本表的语义**（它们早已在基线内），其留档在 `复现脚本/README.md`"
          "与 `layout/_schema.md`；**跨批的交付样例总账一律查 `m06`**。")
    print("      ⇒ 故**不恢复**自带声明表：两张表（`DECLARED_CHANGES` / `DECLARED_NEW_PATTERNS`）"
          "**保持为空**；差异的「有意/意外」判据**统一取 `m06` 总账**。`m01` 现职责＝⓪ 提交面健全性"
          "（提交进去的那份**是不是交付样例**，硬失败）＋ ③ 账内/未声明比对（消费 `m06` 总账）"
          "＋ ③b 总账 vs HEAD 一致性 ＋ 现值侧 ①b/⑥/⑦。")
    for i, why in sorted(DECLARED_NEW_ELEMENTS.items()):
        e = nm.get(i)
        if e:
            print("      %-16s %-26s %-28s %-30s %s"
                  % (i, "（无 —— 新增）", (e.get("asset") or "").replace("ui/", ""),
                     "%sx%s @%s,%s" % (e.get("w"), e.get("h"), e.get("x"), e.get("y")), "**是（新增）**"))

    print("\n" + "-" * 78)
    if FAILS:
        print("结果：**不通过**（退出码 1）—— %d 处" % len(FAILS))
        return 1
    if not baseline_ok:
        # 到不了这里：⓪ 的 `fail()` 已把 FAILS 置非空。留着只为「万一有人删掉那个 fail() 时**不静默放行**」。
        print("结果：**不通过**（退出码 1）—— HEAD 基线不健全而 ⓪ 未报失败 ⇒ 本脚本的状态不一致，请勿放行。")
        return 1
    print("结果：**通过**（退出码 0）—— 影响外观/行为的差异 **%d 处全部在声明表内**、"
          "未声明差异 **0 处**；`pts`/`color`/`w`/`arrow` 与 HEAD 一致；三个交付样例素净；"
          "HEAD 基线健全" % n_hit)
    if n_hit == 0:
        # ★ 第 11 批第 3 轮（二审 C1）：本脚本的对照是 `HEAD`，**提交之后差异恒为 0** ⇒
        #   汇总句极易被读成「本批什么都没改」。此处显式点明退化，并指向权威落点。
        print("      ⚠ **退化提示**：差异计 0 处有两种含义 —— ①本批真的只动 note；②**本批已提交**"
              "（对照靶 `HEAD` ＝ 盘上 ⇒ 恒 0）。**「本批改了什么」一律查 `m06` 的固定基线总账**"
              "（`BASE_REF=%s`），不要据本条判断有无改动。" % "ef68dcf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
