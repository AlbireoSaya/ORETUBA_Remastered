#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
pair_place.py —— 立绘落位「配对/状态机」求值器（ISSUE-20261008-09 / PAIR 模块）

【要解决的问题】
PLACE 模块把「方向 token → x」的 DSL 实现完，但只在**本行控制串**存在时有效：
ot 立绘族 24,418 行里 21,098 行（86%）本行没有控制串，单靠 token 只能定出 4.33%（1,057 行）。
本模块把这些「本行无 token」的行解出来。

【本模块新解出的机制（全部对拍 PSV 金标得到，见 配对规则表.tsv）】
1. **位置枚举（显式档）** —— 开立节点自身带一个「位置枚举」实参：
     0 = 画面中央(c)   1 = 左槽(l)   2 = 右槽(r)   0xFFFFFFFF(-1) = 「保持该槽当前 x」
   （1920 空间取值 960 / 504 / 1416；金标口径 cx = 640 / 336 / 944）
   ★ 归因订正（2026-10-09）：位置取自「**按槽号索引的槽状态**」，枚举 / token / 槽首默认都只是
     写入该状态的方式——「位置＝由枚举档给出」的表述**不准确、未证伪**（单改槽号即改变位置；
     Round P 改枚举的「零效果」是**无效对照**——所改实例已被 `CharacterDelete` 清掉）。
     该归因解释**尚未独立验证**（登记为 UNP-9；数值口径不受影响）。见 `..\说明.md` §一.2、`会话交接_20261009.md` §二。
   * ot/otr：`CharacterOpen` V=0x1C43C 的 args[2]
   * ot/otr：`CharacterOpen` V=0x14084 的 args[2] 是**槽号**，位置枚举在**同一 (scene,seq)
     内、slot 相同**的 `0x17514` 节点的 args[2]
   * otp   ：V=0x1A618 args[0]；V=0x11078 经 V=0x14534 args[2]（结构类比，未对拍 ⇒ 见
     「未证但已采用.tsv」）
   对拍：显式档三值（0/1/2）在 ot 上命中 **99.9%（1,314/1,315）／95.2%（295/310）／
   95.4%（292/306）**，合计 1,901/1,931 = 98.45%（口径＝`0x1C43C`/`0x14084` 两族**显式枚举行**
   × 名称前缀 4 字唯一匹配金标 open 事件；反例 30 条；复跑 `_probe_10_enum_gold.py`——
   2026-10-09 补，回应审核 RV-A R-1：本组分数曾无口径登记、复算不出，现可复现）。
   ★ 2026-10-09 订正：原写 100.0% 属过度四舍五入。

2. **按槽的状态机（保持档）** —— 枚举 = -1 时 x 取「该槽当前的 x」。槽状态由
     * 本节点的显式枚举设置，或
     * 同场景内 token 节点（`0x18B74`/`0x186C8` 的 ctrl）按 PLACE 的 DSL 施加增量，或
     * 槽首次使用时的默认值 = **画面中央 960**（引擎 `CharacterOpen` 写 VAR#778[idx]=400
       的候选语义，EXE_POS §9.2 **未证**；本模块采用并标 `conf` —— 见「未证但已采用.tsv」）
   对拍：保持档在 ot 上命中 **93.9%**（n=11,849，含下述自动清屏）。

3. **清屏重置（自动证得）** —— `CharacterDelete` V=0x1C5B0 的实参恒为 `[0, -1, ms]`（无槽号）
   ⇒ 是「清空全部在场槽」；把它作为**槽状态全量重置**后，保持档命中率 0.9391 → **0.9455**
   （金标 `ot_s01_08d4` 等场独立佐证：清屏后槽 0 回到中央）。

4. **部分施加 token（对拍择优）** —— 控制串含未覆盖 token（裸数字等）时，仍施加其中已解出的
   方位 token（PLACE 采取「整串跳过」的保守口径；本模块在槽状态侧放宽）：严口径 0.9837 → 0.9901。

【覆盖率（本模块主要验收项）】ot 4.33% → **94.82%**（24,418 行中 **23,153** 行有 x1920；
除 del 外 97.20%）；otr 4.25% → **94.08%**（1,128/1,199）；otp 5.50% → **95.24%**（5,423/5,694）。
⚠️ 口径：**94.82% 是「导出率」不是「已证定位率」**——分子 23,153 含未证行
**按 conf 标签计 3,842 行（16.6% = ot 的 UNP-1 1,853 + UNP-7 1,989）**。
（★2026-10-09 订正：原「独立复算口径 3,191 行（13.8%）」经审核 RV-A/RV-C 与 FIX2 复算均
**无出处、作废**，不得引用。）按来源强度三分（分母 = 新增位置 28,283 行）：
**独立可定 17.08%（4,832，= pos_from∈{token-static,setter-abs}）／状态机推导 82.92%（23,451）**。
（★2026-10-09 订正：原「17.55%（4,964）／82.45%（23,319）」不可复算，已作废、不得引用。）
详见 `..\说明.md` §二。

【v2 的 conf 档（★ 未证不得与已证同标签）】
  `DSL已解`           —— 位置由本行 token / 显式位置枚举给出（ot 已对拍金标）
  `弱推断(UNP-7)`     —— CharacterActionEnd 沿用槽当前 x（2,803 行；弱推断，未证）
  `默认值未证(UNP-1)` —— 该槽**首次使用**时沿用默认 x=960（UNP-1；默认值本身未证）
  `源类比未对拍(otp)` —— otp 族映射按 ot 结构类比、未对拍（UNP-5；**otp 全源不出现 `DSL已解`**）
  `源类比未对拍(otr)` —— otr 沿用 ot 族/实参位、未单独对拍（UNP-6；同上）
  （`slot缺` / `token未覆盖` / `fb待定` / `画外(无像素)` 为原有的不可定位档，保持不变）

【运行前置（缺输入时报独立错误，不与「变异失败」混淆）】
  必需输入：`编程组\SOB0解码\解出_{ot,otr,otp}.tsv`（被 .gitignore 排除，须先跑
  `编程组\工具\decode_sob0.py --out 编程组\SOB0解码` 再生）＋ `编程组\PSV演出\立绘事件流.tsv`。
  **工作区根多候选解析**：`--ws-root <dir>` / 环境变量 `GRETA_WS_ROOT` ＞ 向上搜索 `Galgame.md`
  （就近者）＞ 继续向上的祖先（worktree 嵌套时可命中真实工作区里已生成的中间件，只读）。
  输入缺失 ⇒ 打印 `INPUT_MISSING` + 缺失路径，**退出码 3**（`--check` 的 1、变异自证的
  PASS/FAIL 均为不同判据）。

【对拍口径（与 PLACE 的 compare_gold.py 逐条一致，只扩展可比 V 的集合）】
   严口径：该 (scene_id,seq) 上我方恰 1 个可比节点 ∧ 金标恰 1 条 task_type 合规事件 ⇒ 单点相等
   宽口径：金标该 (scene_id,seq) ≥1 条合规事件 ⇒ 命中 = 任一相等
   画外档：`!l`/`!r` 行用不等式（`!l` ⇒ 任一 x1920<0 ；`!r` ⇒ 任一 x1920≥2250）
   另有【逐行口径】（本模块补充）：行级配对（(scene,seq)+角色名）单点比较，样本更大、更直指
   本模块新增的配对规则。
   终值（ot）：**严口径 0.9901（10,770/10,878）｜逐行 0.9544（12,846/13,460）｜
   宽口径 0.9545｜画外 0.9667（116/120）**

【纪律】
  * **不猜**：一切「疑似默认值 / 类比映射」都进「未证但已采用.tsv」并在行内 `conf` 体现；
    DSL 表里没有的 token 仍为 unresolved（沿用 PLACE 的判定）。
  * 绝不改动 v1 已解出的行（`abs_priority`）：v1 有 x 的行原样保留（pos_from=token-static），
    保证「v1 的 0.9616 存量不被本模块破坏」。
  * `--check` 严格只读幂等；`--selfcheck-mutate` 改坏一处配对规则 ⇒ 校验必须 FAIL。

CLI:
  python -X utf8 pair_place.py --emit              # 写 立绘落位_{src}_v2.tsv / 配对规则表.tsv
                                                   #    / 未证但已采用.tsv / 覆盖率_v1v2.tsv
  python -X utf8 pair_place.py --check             # 严格只读幂等复核（不写盘）
  python -X utf8 pair_place.py --selfcheck-mutate  # 变异自证（期望 check FAIL）
  python -X utf8 pair_place.py --gold              # 金标三口径对拍（只读打印）
  python -X utf8 pair_place.py --gold --emit       # 另写 金标对拍_ot_v2.tsv / _反例_v2.tsv
  python -X utf8 pair_place.py --diff              # v1↔v2 差异逐类计数
  python -X utf8 pair_place.py --stats             # 覆盖率
所有子命令均可加 `--ws-root <dir>` 覆盖工作区根；输入缺失一律退出码 3（见上「运行前置」）。
"""
import collections
import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 只读纪律：import PLACE 的模块不得在 PLACE 目录产生 __pycache__（写入边界仅限本模块目录）
sys.dont_write_bytecode = True

# ---- 工作区根：多候选解析（不按固定层数硬编码）
# 本脚本原开发位置 `子代理工作区\ISSUE-20261008-09\PAIR\`（距工作区根 3 层），入库后位于
# `工程\<译名>\编程组\新源侧\PAIR\`（5 层）。按固定 3 层推 WS 会在入库后错位 ⇒
# 既 import 不到 place_dsl（原 PLACE 目录在旧位置），也找不到输入。改为：
#   ① 环境变量 `GRETA_WS_ROOT` / `--ws-root <dir>` 显式覆盖（最高优先）；
#   ② 自脚本目录向上搜索含 `Galgame.md` 的目录（就近者 = worktree 根）；
#   ③ 继续向上把其余含 `Galgame.md` 的祖先列为候选（worktree 嵌套在工作区内时，
#      可命中真实工作区里已生成、被 `.gitignore` 的中间件；**只读，不写回**）。
_WS_ENV = "GRETA_WS_ROOT"


def _candidate_roots():
    env = os.environ.get(_WS_ENV)
    if env:
        return [os.path.abspath(env)]        # 显式指定 ⇒ 唯一根（不再向上回退）
    roots = []
    d = HERE
    while True:
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            roots.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    seen, out = set(), []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    if not out:                     # 兜底：按入库位置（5 层）推导
        out = [os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))]
    return out


WS_ROOTS = _candidate_roots()
WS = WS_ROOTS[0]
PROJ_REL = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")


def _resolve_input(rel_file, rel_dir):
    """按候选根顺序找输入文件；返回 (目录绝对路径, 是否命中)。未命中退回最近根的 rel_dir。"""
    for r in WS_ROOTS:
        p = os.path.join(r, rel_file)
        if os.path.isfile(p):
            return os.path.dirname(p), True
    return os.path.join(WS_ROOTS[0], rel_dir), False


# PLACE 模块导入路径：优先入库后的同树兄弟目录 `../PLACE`（HERE/../PLACE），
# 其次回退旧开发位置（子代理工作区）。
_SIB = os.path.abspath(os.path.join(HERE, "..", "PLACE"))
if os.path.isfile(os.path.join(_SIB, "place_dsl.py")):
    PLACE_DIR = _SIB
else:
    PLACE_DIR = os.path.join(WS_ROOTS[0], "子代理工作区", "ISSUE-20261008-09", "PLACE")
sys.path.insert(0, PLACE_DIR)
import place_dsl as P          # noqa: E402  （token DSL：tokenize_ctrl / apply_ops / 求值）
import layer_by_slot as L      # noqa: E402  （层序 z_rank）

SOB0_DIR = P.SOB0_DIR          # 单一真值源（与 PLACE 同口径的多候选解析）
PSV_DIR, _GOLD_OK = _resolve_input(os.path.join(PROJ_REL, "PSV演出", "立绘事件流.tsv"),
                                   os.path.join(PROJ_REL, "PSV演出"))
GOLD = os.path.join(PSV_DIR, "立绘事件流.tsv")


def set_ws_root(root):
    """`--ws-root` 显式覆盖：**唯一根**（不再向上回退），同步改本模块与 place_dsl 并重算输入目录。"""
    global WS_ROOTS, WS, SOB0_DIR, PSV_DIR, GOLD
    root = os.path.abspath(root)
    WS_ROOTS = [root]
    WS = root
    P.set_ws_root(root)
    SOB0_DIR = P.SOB0_DIR
    PSV_DIR, _ = _resolve_input(os.path.join(PROJ_REL, "PSV演出", "立绘事件流.tsv"),
                                os.path.join(PROJ_REL, "PSV演出"))
    GOLD = os.path.join(PSV_DIR, "立绘事件流.tsv")
    return SOB0_DIR


def missing_inputs():
    """必需输入缺失清单（绝对路径）。非空 ⇒ 不得把「输入缺失」当「校验/变异失败」。"""
    miss = list(P.missing_inputs())
    if not os.path.isfile(GOLD):
        miss.append(GOLD)
    return miss

SRCS = ("ot", "otr", "otp")

# 首个方位 token（供 dir_token 列；与 PLACE compare_gold 同式）
TOKRE = re.compile(r"![clr]|[lr]?[<>]\d+|[clr][+-]\d+|[<>]|[clr]|[+-]\d+|[du]|[_$]")

# ------------------------------------------------------------------ 规则（唯一真值源；变异自证会改写它）
# 位置枚举 → 1920 空间 x
ENUM_X = {0: 960, 1: 504, 2: 1416}
KEEP = -1                      # 0xFFFFFFFF
FRESH_X = 960                  # 槽首用默认 x（= 画面中心；EXE_POS §9.2 未证，本模块采用）
RULES = {
    "enum_x": ENUM_X,
    "fresh_x": FRESH_X,
    "setter_pick": "first",    # 0x14084 配到多个 0x17514 时取第一个（对拍：first 逐行 0.9544 / last 0.9520，见 UNP-4）
                               # ★2026-10-09 订正：原括注「first 0.9455 / last 0.9391」系 UNP-3（del_reset）的数字，误挂在本规则上
    "del_reset": True,         # CharacterDelete(无槽) ⇒ 槽状态全量重置
    "change_reset": False,     # 槽内角色易主时是否重置（对拍：False 更优）
    "abs_priority": True,      # v1（PLACE static）已解出的行不覆盖
    "token_partial": True,     # 控制串含未覆盖 token 时，仍施加已解出的方位 token
}

# ------------------------------------------------------------------ conf 档（可辨证据强度；写进 v2 的 conf 列）
# 目的：未证结论**不得与已证行同标签**，使任何按 conf 取数的下游无法把未证行当已证。
#   `DSL已解`            —— 位置由本行自身 token / 显式位置枚举给出，已对拍 ot 金标（已证）
#   `弱推断(UNP-7)`      —— CharacterActionEnd 的位置沿用槽当前 x（UNP-7，弱推断、未证）
#   `默认值未证(UNP-1)`  —— 该槽**首次使用**时沿用默认 x=960（UNP-1，默认值本身未证）
#   `源类比未对拍(otp)`  —— otp 族映射按 ot 结构类比、未对拍（UNP-5）
#   `源类比未对拍(otr)`  —— otr 沿用 ot 族/实参位、未单独对拍（UNP-6）
CONF_PROVEN = "DSL已解"
CONF_UNP7 = "弱推断(UNP-7)"
CONF_UNP1 = "默认值未证(UNP-1)"
CONF_ANALOG = {
    "otp": "源类比未对拍(otp)",     # UNP-5
    "otr": "源类比未对拍(otr)",     # UNP-6
}

# ------------------------------------------------------------------ 各族实参位（按源；一切位置都以实参向量为准）
#   kind → {arg位置}
FAM = {
    "ot": {
        # 开立档 A：位置枚举在本节点
        "open":    dict(v="0x1C43C", enum=2, slot=5, name=4),
        # 开立档 B：位置枚举在相邻 0x17514
        "open2":   dict(v="0x14084", slot=2, name=1, setter="0x17514", set_enum=2, set_slot=3),
        "setter":  dict(v="0x17514", enum=2, slot=3),
        # 带 token 的族（可施加到槽状态）
        "tok":     [dict(v="0x18B74", ctrl=2, slot=3), dict(v="0x186C8", ctrl=1, slot=2)],
        # 无槽的 token 族（精灵/背景类，独立求值，不参与立绘槽状态）
        "tokfree": [dict(v="0x10428", ctrl=5)],
        # 无 token 但可继承槽状态
        "end":     dict(v="0x19808", slot=2),
        # 退场（无槽 ⇒ 清屏）
        "del":     dict(v="0x1C5B0"),
    },
    "otp": {
        "open":    dict(v="0x1A618", enum=0, slot=3, name=2),
        "open2":   dict(v="0x11078", slot=2, name=1, setter="0x14534", set_enum=2, set_slot=3),
        "setter":  dict(v="0x14534", enum=2, slot=3),
        "tok":     [dict(v="0x15BAC", ctrl=2, slot=3), dict(v="0x156E8", ctrl=2, slot=3)],
        "tokfree": [],
        "end":     dict(v="0x16828", slot=2),
        "del":     dict(v="0x1A970"),
    },
}
FAM["otr"] = FAM["ot"]         # otr 与 ot 同引擎同 V 号（PLACE FAMILY 已登记，SOB0ARGS 对账 0 差异）


def fam_vmap(src):
    f = FAM[src]
    m = {}
    for kind in ("open", "open2", "setter", "end", "del"):
        m.setdefault(f[kind]["v"], kind)
    for d in f["tok"]:
        m.setdefault(d["v"], "tok")
    for d in f["tokfree"]:
        m.setdefault(d["v"], "tokfree")
    return m


# ------------------------------------------------------------------ 行装载（沿用 PLACE 的解析，保证与 v1 同源）
def load_rows(src):
    return P.load_src_rows(src)


def argN(a, i):
    """实参 i 的无符号十进制；`N:4294967295` → -1（保留哨兵语义）。"""
    if a is None or i is None or i >= len(a):
        return None
    v = P.arg_uint(a[i])
    if v is None:
        return None
    return -1 if v == 4294967295 else v


def argS(a, i):
    if a is None or i is None or i >= len(a):
        return None
    return P.arg_str(a[i])


# ------------------------------------------------------------------ 状态机
def new_slot():
    # fresh=True 表示该槽的 x 尚来自**未经证明的槽首默认值**（UNP-1）；
    # 一旦被显式枚举或绝对 token 定过，即置 False（此后 keep 档属已证）。
    return {"x": ("num", RULES["fresh_x"]), "y": P.BOTTOM_Y, "nm": None, "fresh": True}


def apply_enum(st, val, enum_x):
    """把位置枚举施加到槽状态（原地）。返回是否显式设置。"""
    if val in enum_x:
        st["x"] = ("num", enum_x[val])
        st["fresh"] = False          # 显式档 ⇒ 不再是「槽首默认值」
        return True
    return False                     # (-1 / 未知值) = 保持


def apply_ctrl(st, ctrl, dsl, rules=None):
    """把控制串的 token 增量施加到槽状态（原地）。返回 (ok, unks)。
    unks 非空时：`token_partial=False` ⇒ 整串跳过（PLACE 口径）；True ⇒ 仍施加已解出的方位
    token（裸数字等未覆盖 token 多半是 ms 时长，不承载位置），仅在 pos_from/note 上标注。"""
    rules = RULES if rules is None else rules
    ops, unks = P.tokenize_ctrl(ctrl, dsl)
    if unks and not rules.get("token_partial", False):
        return False, unks
    if not ops:
        return False, unks
    P.apply_ops(ops, st)
    # 出现绝对/画外档 ⇒ 该槽 x 由本串直接定出，不再依赖未证的槽首默认值
    if any(o[0] in ("abs", "off") for o in ops):
        st["fresh"] = False
    return True, unks


def resolve_src(src, rules=None, dsl=None):
    """跑状态机，返回 overrides: file_idx → dict(x, y, x_class, pos_from, conf, note)。
    只对本源立绘族内、且**配对/状态机解得出**的行给条目。
    """
    rules = RULES if rules is None else rules
    dsl = P.DSL if dsl is None else dsl
    enum_x = rules["enum_x"]
    vm = fam_vmap(src)
    rows = load_rows(src)
    overrides = {}
    scene_state = {}
    cur_scene = None
    # 预索引：每个 (scene,seq) 的 setter 节点列表
    setters = collections.defaultdict(list)
    for r in rows:
        v = vm.get((r["arg3"] or "").replace("V=", ""))
        if v == "setter":
            setters[(r["scene_id"], r["seq"])].append(
                (argN(r["args"], FAM[src]["setter"]["slot"]),
                 argN(r["args"], FAM[src]["setter"]["enum"])))
    open2 = FAM[src]["open2"]

    for r in rows:                              # 文件序 = 场景内 seq 升序
        v = vm.get((r["arg3"] or "").replace("V=", ""))
        if v is None:
            continue
        if r["scene_id"] != cur_scene:
            cur_scene = r["scene_id"]
            scene_state = {}
        st_all = scene_state
        key = (r["scene_id"], r["seq"])

        if v == "del":
            if rules["del_reset"]:
                st_all.clear()
            continue

        if v == "tokfree":
            d = FAM[src]["tokfree"][0]
            ctrl = argS(r["args"], d["ctrl"])
            if ctrl is None:
                continue
            st = new_slot()
            ok, unks = apply_ctrl(st, ctrl, dsl, rules)
            if not ok or st["x"] is None:
                continue
            overrides[r["file_idx"]] = dict(
                x=st["x"][1], y=st["y"], x_class="num",
                pos_from="token-free", conf=CONF_PROVEN,
                note="无槽族（精灵/背景），独立求值")
            continue

        if v == "tok":
            d = next(x for x in FAM[src]["tok"] if x["v"] == r["arg3"].replace("V=", ""))
            ctrl = argS(r["args"], d["ctrl"])
            slot = argN(r["args"], d["slot"])
            if ctrl is None or slot is None:
                continue
            st = st_all.setdefault(slot, new_slot())
            ok, unks = apply_ctrl(st, ctrl, dsl, rules)
            if not ok:
                continue
            if st["x"] is None:
                continue
            overrides[r["file_idx"]] = dict(
                x=st["x"][1] if st["x"][0] == "num" else None,
                y=st["y"], x_class=st["x"][0],
                pos_from="token-state",
                # 纯相对 token 施加在「槽首默认 960」上 ⇒ 仍依赖未证默认（UNP-1）；
                # 含绝对锚点（c/l/r/!*）者已由本行自身定出 ⇒ 已证。
                conf=CONF_UNP1 if st.get("fresh") else CONF_PROVEN,
                note="token 施加到槽状态"
                     + ("（基准=槽首默认，未证 UNP-1）" if st.get("fresh") else ""))
            continue

        if v == "end":
            slot = argN(r["args"], FAM[src]["end"]["slot"])
            if slot is None:
                continue
            st = st_all.get(slot)
            if st is None or st["x"] is None:
                continue
            overrides[r["file_idx"]] = dict(
                x=st["x"][1] if st["x"][0] == "num" else None,
                y=st["y"], x_class=st["x"][0],
                pos_from="state-inherit", conf=CONF_UNP7,
                note="动作结束站，沿用该槽当前 x（UNP-7 弱推断）")
            continue

        # ---- 开立档
        if v == "open":
            d = FAM[src]["open"]
            slot = argN(r["args"], d["slot"])
            name = argS(r["args"], d["name"])
            val = argN(r["args"], d["enum"])
            explicit = val in enum_x
            if slot is None:
                continue
            st = st_all.setdefault(slot, new_slot())
            if rules["change_reset"] and name and st.get("nm") and st["nm"][:4] != name[:4]:
                st_all[slot] = st = new_slot()
            if name:
                st["nm"] = name
            was_fresh = st.get("fresh", False)
            apply_enum(st, val, enum_x)
            overrides[r["file_idx"]] = dict(
                x=st["x"][1] if st["x"] and st["x"][0] == "num" else None,
                y=st["y"], x_class=st["x"][0] if st["x"] else None,
                pos_from="setter-abs" if explicit else "setter-keep",
                conf=CONF_PROVEN if (explicit or not was_fresh) else CONF_UNP1,
                note="本节点位置枚举=%s"
                     % ("%d" % val if explicit else
                        ("保持(-1)，槽首默认=未证(UNP-1)" if was_fresh else "保持(-1)")))
            continue

        if v == "open2":
            slot = argN(r["args"], open2["slot"])
            name = argS(r["args"], open2["name"])
            if slot is None:
                continue
            cand = [(s, e) for s, e in setters[key] if s == slot]
            if not cand:
                continue
            if rules["setter_pick"] == "last":
                val = cand[-1][1]
            else:
                val = cand[0][1]
            explicit = val in enum_x
            st = st_all.setdefault(slot, new_slot())
            if rules["change_reset"] and name and st.get("nm") and st["nm"][:4] != name[:4]:
                st_all[slot] = st = new_slot()
            if name:
                st["nm"] = name
            was_fresh = st.get("fresh", False)
            apply_enum(st, val, enum_x)
            overrides[r["file_idx"]] = dict(
                x=st["x"][1] if st["x"] and st["x"][0] == "num" else None,
                y=st["y"], x_class=st["x"][0] if st["x"] else None,
                pos_from="setter-abs" if explicit else "setter-keep",
                conf=CONF_PROVEN if (explicit or not was_fresh) else CONF_UNP1,
                note="同 (scene,seq) 同槽 %s 的位置枚举=%s（候选 %d 个，取%s）"
                     % (open2["setter"], ("%d" % val) if explicit else "保持(-1)",
                        len(cand), rules["setter_pick"]))
            continue

        if v == "setter":
            # setter 自身也可定位（它设的就是该槽的 x）
            slot = argN(r["args"], FAM[src]["setter"]["slot"])
            val = argN(r["args"], FAM[src]["setter"]["enum"])
            if slot is None:
                continue
            st = st_all.setdefault(slot, new_slot())
            was_fresh = st.get("fresh", False)
            explicit = apply_enum(st, val, enum_x)
            overrides[r["file_idx"]] = dict(
                x=st["x"][1] if st["x"] and st["x"][0] == "num" else None,
                y=st["y"], x_class=st["x"][0] if st["x"] else None,
                pos_from="setter-abs" if explicit else "setter-keep",
                conf=CONF_PROVEN if (explicit or not was_fresh) else CONF_UNP1,
                note="位置 setter 节点自身")
            continue
    return overrides


# ------------------------------------------------------------------ v2 行构建
V1_COLS = ["scene_id", "src", "seq", "ord", "fam", "name", "slot", "dir_token",
           "x1920", "y1920", "z_rank", "conf", "evidence"]
V2_COLS = V1_COLS + ["pos_from"]      # 14 列 = PLACE 的 13 列 + pos_from


def build_v2(src, rules=None, dsl=None):
    """返回 (v1_rows, v2_rows)：同为 build 的 (r,f) 行对，v2 行多 pos_from 且填了配对/状态解。"""
    rules = RULES if rules is None else rules
    build = P.build_rows(src, dsl=dsl, mode="static")     # v1 口径（static）
    _, zmap, _ = L.compute_z(src, build=build)
    overrides = resolve_src(src, rules=rules, dsl=dsl)
    v1_rows, v2_rows = [], []
    for r, f in build:
        fi = r["file_idx"]
        ctrl = f.get("ctrl") or ""
        m = TOKRE.search(ctrl) if ctrl else None
        base = dict(
            scene_id=r["scene_id"], src=src, seq=str(r["seq"]), ord=str(f["ord"]),
            fam=P.fam_short(f["fdef"]["role"]), name=f.get("name") or "",
            slot="" if f.get("slot") is None else str(f.get("slot")),
            dir_token=m.group(0) if m else "",
            x1920="" if f.get("x") is None else str(f.get("x")),
            y1920="" if f.get("y") is None else str(f.get("y")),
            z_rank=zmap.get((r["scene_id"], fi), ""),
            conf=f.get("conf") or "", evidence=r["evidence"])
        v1_rows.append(dict(base, pos_from="static" if f.get("x") is not None else ""))
        row = dict(base)
        row["pos_from"] = "token-static" if f.get("x") is not None else ""
        # 立项顺序：v1 已解 > 配对/状态机 > 原样
        if row["x1920"] == "" and fi in overrides and rules["abs_priority"]:
            ov = overrides[fi]
            if ov["x"] is not None:
                row["x1920"] = str(ov["x"])
                row["y1920"] = str(ov["y"])
                row["conf"] = ov["conf"]           # 证据档随来源（UNP-1/UNP-7 不再冒充 DSL已解）
                row["pos_from"] = ov["pos_from"]
            elif ov["x_class"] in ("off", "off_left", "off_right"):
                row["x1920"] = ""            # 画外档不给像素（与 v1 口径一致）
                row["y1920"] = str(ov["y"])
                row["conf"] = "画外(无像素)"   # 无像素 ⇒ 不参与「已证位置」；UNP-7/1 不适用于无 x 行
                row["pos_from"] = ov["pos_from"]
        # 源类比档：otp/otr 的**族映射**未对拍（UNP-5/6）⇒ 凡本可为 `DSL已解` 的行一律降级标记，
        # 使 `DSL已解` 在整个交付里只表示「ot（或已对拍源）上的已证行」。UNP-7/UNP-1 已是更具体的
        # 未证档，保持不动（同样不是 `DSL已解`，下游无法当已证）。
        if src in CONF_ANALOG and row["conf"] == CONF_PROVEN:
            row["conf"] = CONF_ANALOG[src]
        v2_rows.append(row)
    return v1_rows, v2_rows


def rows_to_tsv(rows, cols):
    out = ["\t".join(cols)]
    for r in rows:
        out.append("\t".join(r.get(c, "") for c in cols))
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ 金标对拍
ROLE_ALLOW = {
    "0x1C43C": {"CharacterOpen", "CharacterOpenBS"},
    "0x14084": {"CharacterOpen", "CharacterOpenBS"},
    "0x186C8": {"CharacterOpen", "CharacterOpenBS"},
    "0x18B74": {"CharacterMove", "CharacterAction"},
    "0x10428": {"SpriteMove", "SpriteBS", "SpriteBG"},
    "0x1A618": {"CharacterOpen", "CharacterOpenBS"},
    "0x11078": {"CharacterOpen", "CharacterOpenBS"},
}
TOKEN_VS = {"ot": ("0x1C43C", "0x14084", "0x186C8", "0x18B74", "0x10428"),
            "otr": ("0x1C43C", "0x14084", "0x186C8", "0x18B74", "0x10428"),
            "otp": ("0x1A618", "0x11078", "0x156E8", "0x15BAC")}
OFF_RIGHT_MIN = 1500 * 1.5      # 2250


def v_of(ev):
    i = ev.find("V=")
    if i < 0:
        return ""
    j = i + 2
    while j < len(ev) and ev[j] not in " \t":
        j += 1
    return ev[i + 2:j]


def load_gold(src):
    g = collections.defaultdict(list)
    with open(GOLD, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["src"] != src or r["cx"] == "":
                continue
            try:
                cx = int(r["cx"])
            except ValueError:
                continue
            x1920 = int(r["x1920"]) if r["x1920"] != "" else int(round(cx * 1.5))
            g[(r["scene_id"], int(r["seq"]))].append(
                (cx, x1920, r["task_type"], r["ps_name"], r["op"]))
    return g


def name_ok(a, b):
    if not a or not b:
        return True
    return a == b or a.startswith(b) or b.startswith(a)


def compare_gold(src="ot", rules=None):
    """返回 (res_rows, stat)。res_rows: (口径, scene, seq, v, token/名, 我x, 金标, 判据)"""
    rules = RULES if rules is None else rules
    _, v2 = build_v2(src, rules=rules)
    gold = load_gold(src)
    vs = TOKEN_VS[src]
    my_nodes = collections.defaultdict(list)
    for r in v2:
        if v_of(r["evidence"]) in vs:
            my_nodes[(r["scene_id"], int(r["seq"]))].append(r)
    stat = collections.Counter()
    per_tok = collections.defaultdict(lambda: [0, 0])
    per_from = collections.defaultdict(lambda: [0, 0])
    res = []
    for r in v2:
        v = v_of(r["evidence"])
        if v not in vs:
            continue
        key = (r["scene_id"], int(r["seq"]))
        allow = ROLE_ALLOW.get(v, set())
        cxlist = [c for c in gold.get(key, []) if c[2] in allow]
        tok = r["dir_token"]
        if not cxlist:
            continue
        if r["x1920"] != "":
            mine_x = int(r["x1920"])
            if len(my_nodes[key]) == 1 and len(cxlist) == 1:
                hit = (cxlist[0][1] == mine_x)
                stat["strict"] += 1
                per_tok[tok][1] += 1
                per_from[r["pos_from"]][1] += 1
                if hit:
                    stat["strict_hit"] += 1
                    per_tok[tok][0] += 1
                    per_from[r["pos_from"]][0] += 1
                else:
                    stat["strict_miss"] += 1
                res.append(("严", r["scene_id"], r["seq"], v, tok or "(无)", str(mine_x),
                            str(cxlist[0][1]), r["pos_from"],
                            "金标 %s/%s cx=%d" % (cxlist[0][0], cxlist[0][2], cxlist[0][1])))
            hit = any(c[1] == mine_x for c in cxlist)
            stat["loose"] += 1
            stat["loose_hit" if hit else "loose_miss"] += 1
            res.append(("宽", r["scene_id"], r["seq"], v, tok or "(无)", str(mine_x),
                        ",".join(str(c[1]) for c in cxlist), r["pos_from"],
                        "金标 %s" % ",".join("%s/%s cx=%d" % (c[0], c[2], c[1]) for c in cxlist)))
            # ---- 逐行口径（本模块补充）：名字唯一匹配
            named = [c for c in cxlist if name_ok(r["name"], c[3])]
            if len(named) == 1:
                h = (named[0][1] == mine_x)
                stat["row"] += 1
                stat["row_hit" if h else "row_miss"] += 1
                res.append(("逐行", r["scene_id"], r["seq"], v, tok or "(无)", str(mine_x),
                            str(named[0][1]), r["pos_from"],
                            "金标 %s/%s cx=%d" % (named[0][0], named[0][2], named[0][1])))
                per_from[r["pos_from"]][1] += 0
        elif tok in ("!l", "!r"):
            if tok == "!l":
                hit = any(c[1] < 0 for c in cxlist)
                need = "任一 x1920 < 0"
            else:
                hit = any(c[1] >= OFF_RIGHT_MIN for c in cxlist)
                need = "任一 x1920 >= 2250"
            stat["offscreen"] += 1
            per_tok[tok][1] += 1
            if hit:
                stat["offscreen_hit"] += 1
                per_tok[tok][0] += 1
            else:
                stat["offscreen_miss"] += 1
            res.append(("画外", r["scene_id"], r["seq"], v, tok or "(无)", "(画外,无像素)",
                        ",".join(str(c[1]) for c in cxlist), r["pos_from"], need))
    # 严口径内「我方 x 未解」计数
    unk = 0
    for key, nodes in my_nodes.items():
        if len(nodes) != 1:
            continue
        allow = ROLE_ALLOW.get(v_of(nodes[0]["evidence"]), set())
        cxlist = [c for c in gold.get(key, []) if c[2] in allow]
        if len(cxlist) == 1 and nodes[0]["x1920"] == "":
            unk += 1
    stat["strict_unknown"] = unk
    return res, stat, per_tok, per_from


def print_gold(res, stat, per_tok, per_from, src="ot"):
    print("== 金标对拍（src=%s；金标 %s）==" % (src, os.path.basename(GOLD)))
    for tag, keys in (("严口径（PC 单节点 ∧ 金标单事件 ∧ task_type 合规）", ("strict", "strict_hit", "strict_miss")),
                      ("宽口径（金标该 seq ≥1 条合规 cx）", ("loose", "loose_hit", "loose_miss")),
                      ("逐行口径（(scene,seq)+角色名 唯一匹配）", ("row", "row_hit", "row_miss")),
                      ("画外档（不等式判据）", ("offscreen", "offscreen_hit", "offscreen_miss"))):
        n, h, mi = stat[keys[0]], stat[keys[1]], stat[keys[2]]
        print("-- %s --" % tag)
        print("   样本量 = %d   命中 = %d   未命中 = %d   命中率 = %s"
              % (n, h, mi, ("%.4f" % (h / n)) if n else "N/A"))
    print("   （严口径内**我方 x 未解**而未判的行数 = %d）" % stat["strict_unknown"])
    print()
    print("-- 分 pos_from 命中率（**严口径**；口径说明：只统计严口径内 我方单节点 ∧ 金标单合规事件 的行）--")
    print("   %-14s %8s %8s %8s" % ("pos_from", "命中", "总数", "命中率"))
    for k in sorted(per_from, key=lambda t: -per_from[t][1]):
        a, b = per_from[k]
        print("   %-14s %8d %8d %8s" % (k or "(无)", a, b, ("%.4f" % (a / b)) if b else "-"))
    print()
    print("-- 分 token 命中率（严口径 + 画外）--")
    for k in sorted(per_tok, key=lambda t: -per_tok[t][1]):
        a, b = per_tok[k]
        print("   %-8s %8d %8d %8s" % (k or "(无)", a, b, ("%.4f" % (a / b)) if b else "-"))


def emit_gold(res):
    p1 = os.path.join(HERE, "金标对拍_ot_v2.tsv")
    p2 = os.path.join(HERE, "金标对拍_反例_v2.tsv")
    head = ["口径", "scene_id", "seq", "V", "dir_token/名", "我方x1920", "金标x1920", "pos_from", "判据"]
    with open(p1, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(head) + "\n")
        for r in res:
            f.write("\t".join(str(x) for x in r) + "\n")
    miss = [r for r in res if (r[0] == "严" and r[5] != r[6])]
    with open(p2, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(head) + "\n")
        for r in miss:
            f.write("\t".join(str(x) for x in r) + "\n")
    print("WROTE %s (%d 行)" % (os.path.basename(p1), len(res)))
    print("WROTE %s (%d 行)" % (os.path.basename(p2), len(miss)))


# ------------------------------------------------------------------ 覆盖率 / 差异
def coverage():
    out = []
    for src in SRCS:
        v1, v2 = build_v2(src)
        n = len(v2)
        x1 = sum(1 for r in v1 if r["x1920"] != "")
        x2 = sum(1 for r in v2 if r["x1920"] != "")
        byfam = collections.defaultdict(lambda: [0, 0, 0])
        for a, b in zip(v1, v2):
            t = byfam[a["fam"]]
            t[0] += 1
            t[1] += (a["x1920"] != "")
            t[2] += (b["x1920"] != "")
        for fam, (tot, a, b) in sorted(byfam.items(), key=lambda t: -t[1][0]):
            out.append((src, fam, tot, a, b))
        # 「unk」族捆了 0x14084/0x17514/0x10428 三个 V ⇒ 逐 V 细分（免得覆盖率被 setter 行抬高而不自知）
        byv = collections.defaultdict(lambda: [0, 0, 0])
        for a, b in zip(v1, v2):
            if a["fam"] != "unk":
                continue
            t = byv[v_of(a["evidence"])]
            t[0] += 1
            t[1] += (a["x1920"] != "")
            t[2] += (b["x1920"] != "")
        for v, (tot, a, b) in sorted(byv.items()):
            out.append((src, "unk:" + v, tot, a, b))
        # 「有位置语义的行」= 全体 − CharacterDelete（无槽、清屏，本身不承载角色位置）
        nz1 = sum(1 for a in v1 if a["fam"] != "del" and a["x1920"] != "")
        nz2 = sum(1 for b in v2 if b["fam"] != "del" and b["x1920"] != "")
        ntot = sum(1 for a in v1 if a["fam"] != "del")
        out.append((src, "(除 del 外合计)", ntot, nz1, nz2))
        out.append((src, "(合计)", n, x1, x2))
    return out


def diff_v1v2():
    cnt = collections.Counter()
    byfam = collections.defaultdict(collections.Counter)
    byfrom = collections.Counter()
    samples = collections.defaultdict(list)
    for src in SRCS:
        v1, v2 = build_v2(src)
        for a, b in zip(v1, v2):
            if a["x1920"] == "" and b["x1920"] != "":
                k = "新增位置"
                byfrom[b["pos_from"]] += 1
                if len(samples[src]) < 8:
                    samples[src].append((b["scene_id"], b["seq"], b["fam"], b["name"],
                                         b["x1920"], b["pos_from"]))
            elif a["x1920"] != "" and b["x1920"] == "":
                k = "位置丢失(异常)"
            elif a["x1920"] != "" and b["x1920"] != "" and a["x1920"] != b["x1920"]:
                k = "位置改变(异常)"
            elif a["x1920"] == "" and b["x1920"] == "":
                k = "均未解"
            else:
                k = "位置不变"
            cnt[k] += 1
            byfam[src][(b["fam"], k)] += 1
    return cnt, byfam, byfrom, samples


# ------------------------------------------------------------------ 产物与校验
OUT_RULES = "配对规则表.tsv"
OUT_UNPROVEN = "未证但已采用.tsv"
OUT_COV = "覆盖率_v1v2.tsv"
OUT_V2 = "立绘落位_%s_v2.tsv"


def rules_table():
    lines = ["\t".join(["节点族", "V(ot)", "V(otp)", "承载位置信息的实参位",
                        "展开式(1920)", "对拍命中率(ot)", "证据"])]
    spec = [
        ("CharacterOpen A", "0x1C43C", "0x1A618", "args[2] / args[0] = 位置枚举",
         "0→960 1→504 2→1416 -1→保持槽状态",
         "0→0.999（1,314/1,315）1→0.952（295/310）2→0.954（292/306）（显式档；合计 1,901/1,931＝98.45%，"
         "反例 30 条；口径与复跑＝`_probe_10_enum_gold.py`：两族显式枚举行 × 名称前缀 4 字唯一金标 open 事件；"
         "2026-10-09 订正：原写 1.000 属过度四舍五入）",
         "本模块对拍；金标 cx 640/336/944；★归因订正(2026-10-09)：位置取自「按槽号索引的槽状态」，"
         "枚举只是写入该状态的方式（单改槽号即改变位置；Round P 改枚举为无效对照）——`会话交接_20261009.md` §二"),
        ("CharacterOpen B", "0x14084", "0x11078", "args[2]=槽号；枚举取同(scene,seq)同槽 setter",
         "同上", "全套规则：严口径 0.9901（n=10878）", "本模块对拍"),
        ("位置 setter", "0x17514", "0x14534", "args[2] = 位置枚举，args[3] = 槽号",
         "同 A", "含在上行", "本模块对拍；0x14084 恒与其相邻"),
        ("CharacterAction/Move", "0x18B74", "0x15BAC", "args[2] = ctrl token，args[3] = 槽号",
         "PLACE DSL 增量", "单步位移 0.9838（XCROSS）", "PLACE / XCROSS"),
        ("CharacterOpen(chr_in)", "0x186C8", "0x156E8", "args[1] / args[2] = ctrl token",
         "PLACE DSL 增量", "入场定位 0.9952（XCROSS）", "PLACE / XCROSS"),
        ("Sprite/BG move", "0x10428", "—", "args[5] = ctrl token（无槽）",
         "PLACE DSL（独立求值）", "未对拍", "PLACE 登记"),
        ("CharacterActionEnd", "0x19808", "0x16828", "args[2] = 槽号（无自身 token）",
         "沿用该槽当前 x", "金标 CharacterActionEnd 无 cx ⇒ 无法单点对拍",
         "状态继承（未证级别的弱结论）"),
        ("CharacterDelete", "0x1C5B0", "0x1A970", "无槽号（实参=[0,-1,ms]）",
         "槽状态全量重置", "间接（UNP-3）", "本模块对拍"),
    ]
    for r in spec:
        lines.append("\t".join(r))
    return "\n".join(lines) + "\n"


def cov_table(cov):
    # ★ 「v2 覆盖率」是**导出率**（有 x1920 的比例），**不是已证定位率**：分子含未证行
    #   （UNP-7 弱推断、UNP-1 默认值未证；otp/otr 另全源为「源类比未对拍」）。
    #   末列「证据档」把每个 src 的覆盖率与其证据级别绑死，避免下游按覆盖率取数时误当已证。
    lines = ["\t".join(["src", "族", "总行数", "v1 有x1920", "v2 有x1920",
                        "v1 覆盖率", "v2 覆盖率", "证据档(口径)"])]
    for src, fam, tot, a, b in cov:
        lines.append("\t".join([src, fam, str(tot), str(a), str(b),
                                "%.4f" % (a / tot) if tot else "-",
                                "%.4f" % (b / tot) if tot else "-",
                                CONF_ANALOG.get(src, "导出率(ot 已对拍；含 UNP-7/UNP-1 未证行)")]))
    return "\n".join(lines) + "\n"


def artifacts(rules=None):
    out = {}
    for src in SRCS:
        _, v2 = build_v2(src, rules=rules)
        out[OUT_V2 % src] = rows_to_tsv(v2, V2_COLS)
    out[OUT_RULES] = rules_table()
    out[OUT_UNPROVEN] = unproven_table()
    out[OUT_COV] = cov_table(coverage())
    return out


def unproven_table():
    head = "\t".join(["编号", "已采用的规则", "取值", "依据", "证据级别", "行内体现", "备注"])
    rows = [
        ("UNP-1", "槽首次使用（无任何前序锚点）的默认 x = 960（画面中央）",
         "960", "EXE_POS §7：CharacterOpen 写 VAR#778[idx]=0x190=400（800 画布中心）⇒ 疑为新槽默认 x=中心；EXE_POS §9.2 明标未证",
         "未证（引擎旁证）", "conf=默认值未证(UNP-1)（2,393 行：setter-keep 2,263 + token-state 130）",
         "★ 已与前 12,886 行已证 setter-keep 分离（不再同为 `DSL已解`）。含纯相对 token 施加在槽首默认上的 token-state 行。"
         "金标佐证（**可复算口径**）：该子集在 ot 上金标可核 **1,783** 行、命中（任一金标 cx×1.5 == x1920）**1,503 = 84.30%**；"
         "~~槽首用 keep 行 cx=640 占 296/618=47.9%；独立复算该子集（slot-first KEEP，checkable 525）命中仅 256=48.8%~~"
         "（★2026-10-09 订正：这两组数无出处、审核 RV-A/RV-C 与 FIX2 独立复算均不吻合 ⇒ **已作废，不得引用**）；"
         "全源 UNP-1 承重 2,393 行（若 UNP-1 错，ot 94.82% → 86.62%）；**未证，不得当已证引用**"),
        ("UNP-2", "位置枚举 0/1/2 = 中央/左/右",
         "0→960 1→504 2→1416",
         "对拍金标(ot)：0→640 1,314/1,315；1→336 295/310；2→944 292/306；合计 1,901/1,931 = 98.45%"
         "（口径＝`0x1C43C`/`0x14084` 两族**显式枚举行** × 名称前缀 4 字唯一匹配金标 open 事件（恰 1 条）；"
         "反例 30 条；可复跑 `_probe_10_enum_gold.py`——2026-10-09 补，回应 RV-A R-1）",
         "对拍即证(ot)", "conf=DSL已解（仅 ot；otp/otr 同规则但降级为源类比档）",
         "反例 30 条＝本口径未命中（enum0/1/2 = 1/15/14；**全为 `0x14084`(B) 行**）——与严口径反例集"
         "（`金标对拍_反例_v2.tsv`）**不相交、不并入该件**（★2026-10-09 订正：原写「反例 30 行见"
         " 金标对拍_反例_v2.tsv」系误指）"),
        ("UNP-3", "CharacterDelete(0x1C5B0, 实参[0,-1,ms] 无槽号) = 清空全部在场槽 ⇒ 槽状态全量重置",
         "重置", "对拍：保持档 0.9391→0.9455（+0.64pt）；金标 ot_s01_08d4 独立佐证（清屏后槽 0 回中央）",
         "对拍佐证(ot)，非指令级", "conf=DSL已解（受其影响的行；重置本身不影响行标签）",
         "0x1C5B0 的 args[0] 恒为 0（597/597）"),
        ("UNP-4", "0x14084 配多个 0x17514 时取第一个",
         "first", "对拍：first 逐行 0.9544 vs last 0.9520（ot）",
         "对拍择优(ot)", "conf=DSL已解（ot）／源类比档（otp/otr）",
         "同键多 setter 共 734 键，0x14084 侧元组多为 (-1,2)/(-1,1)/(-1,0)；`--selfcheck-mutate` 即改此规则"),
        ("UNP-5", "otp 族映射按 ot 结构类比（0x1A618 args[0] 枚举；0x14534 args[2] 枚举）",
         "见 FAM['otp']", "0x14534 args[2] 取值集 {-1:709,0:134,1:64,2:87} 与 0x17514 同构；0x1A618 args[0] 同构",
         "**类比，未对拍**（otp 金标 1,199 行、seq 对齐不可靠）", "conf=源类比未对拍(otp)（4,268 行）",
         "★ otp **全源**不再出现 `DSL已解`（4,268 行源类比 + 726 UNP-7 + 413 UNP-1 = 原 5,407 行）；otp 只报导出率，不宣称已证"),
        ("UNP-6", "otr 沿用 ot 的族/实参位（同引擎同 V 号）",
         "同 ot", "PLACE FAMILY['otr']=FAMILY['ot']；SOB0ARGS 对账 slot/dir_token 0 差异",
         "结构同源，未单独对拍", "conf=源类比未对拍(otr)（893 行）",
         "★ otr 全源不再出现 `DSL已解`（893 行源类比 + 88 UNP-7 + 127 UNP-1 = 原 1,108 行）；任务书规定 otr 逐行 seq 不可靠 ⇒ 只报导出率"),
        ("UNP-7", "CharacterActionEnd(0x19808/0x16828) 的位置 = 该槽当前 x",
         "状态继承", "金标 CharacterActionEnd 无 cx ⇒ 无单点判据；语义上「动作结束」不改位",
         "**未证**（弱推断）", "conf=弱推断(UNP-7)（2,803 行；ot 1,989 / otr 88 / otp 726）",
         "★ 已与已证行分离（不再同为 `DSL已解`）。只为导出率给出，不得作为已证结论引用；"
         "`画外(无像素)` 的 state-inherit 行无像素、不计入 2,803"),
        ("UNP-8", "控制串含未覆盖 token（裸数字等）时，**仍施加已解出的方位 token**",
         "token_partial=True", "对拍：严口径 0.9837→0.9901、逐行 0.9467→0.9544（ot）；"
                              "依据：裸数字是 idx8 处理器、疑似 ms 时长（EXE_POS 未跟踪）",
         "对拍即证(ot)", "conf=DSL已解（若施加了绝对锚点）／默认值未证(UNP-1)（若基准为该槽默认）",
         "PLACE 采取「整串跳过」的保守口径（v1 未改动，存量行未受影响）；"
         "本模块在**槽状态**侧采用部分施加，仅影响 v1 未解出的行"),
        ("UNP-9", "**归因层**：位置＝「按槽号索引的槽状态」（枚举 / token / 槽首默认均为写入该状态的方式）",
         "归因（数值口径不变）",
         "Round S（只改槽号）⇒ 位置与层序同时变；Round P 只改枚举为**无效对照**（所改实例已被 CharacterDelete 清掉）；"
         "最简自洽解释＝槽状态模型——**该解释尚未独立验证**",
         "**未证（归因层）；数值不承重**", "无独立标签（不影响 conf 行分布）；与 conf 各档一并引用",
         "判据＝只改**单个**槽号格，看是否只有该点之后该角色的位置改变（`00_任务书.md` §8.7「仍未证」）；"
         "**数值不受影响**（本模块本就按槽索引做状态机）；见 `..\\说明.md` §一.2、`会话交接_20261009.md` §二"),
        ("UNP-10", "`0x14084`/`0x17514` 族：位置枚举取自**配对的 `0x17514` 节点**（同 (scene,seq) 同槽）",
         "setter_pick=first（同键多 setter 取第一个）",
         "对拍择优(ot)：first 逐行 0.9544 vs last 0.9520；但 `0x17514` 的枚举位**本轮实机未覆盖**",
         "**对拍择优(ot) ＋ 实机未覆盖**", "conf=DSL已解（ot；显式档行）／源类比档（otp/otr）",
         "覆盖判据＝在 `0x14084` 场景上改 `0x17514` 的枚举格，观察落位变化（`00_任务书.md` §8.7「仍未证」第 3 条）"),
    ]
    lines = [head]
    for r in rows:
        lines.append("\t".join(r))
    return "\n".join(lines) + "\n"


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def do_emit():
    arts = artifacts()
    for name in sorted(arts):
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(arts[name])
        b = arts[name].encode("utf-8")
        print("  WROTE %-28s %d bytes  sha256=%s" % (name, len(b), sha(b)))
    return True


def do_check(mutate=None):
    rules = dict(RULES)
    if mutate:
        rules.update(mutate)
    arts = artifacts(rules=rules)
    allpass, ndiff = True, 0
    for name in sorted(arts):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            print("  MISS     %-28s (磁盘缺文件)" % name)
            allpass, ndiff = False, ndiff + 1
            continue
        with open(p, "rb") as f:
            ondisk = f.read()
        new = arts[name].encode("utf-8")
        if sha(ondisk) == sha(new):
            print("  OK       %-28s %d bytes  sha256=%s" % (name, len(ondisk), sha(ondisk)))
        else:
            a = ondisk.decode("utf-8").splitlines()
            b = arts[name].splitlines()
            d = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            print("  DIFF     %-28s %d 行不一致" % (name, d))
            allpass, ndiff = False, ndiff + 1
    print("ALL_PASS=%s  files=%d  diff_files=%d" % (allpass, len(arts), ndiff))
    print("READONLY=True（本模式不写任何文件）")
    return allpass


def do_stats():
    cov = coverage()
    print(cov_table(cov))
    cnt, byfam, byfrom, samples = diff_v1v2()
    print("== v1 → v2 差异逐类计数 ==")
    for k, n in cnt.most_common():
        print("   %-16s %d" % (k, n))
    print("\n-- 新增位置的 pos_from 分布 --")
    for k, n in byfrom.most_common():
        print("   %-16s %d" % (k, n))
    for src in SRCS:
        print("\n-- %s 新增位置样例 --" % src)
        for s in samples.get(src, []):
            print("   %-16s:%-5s %-6s %-8s x1920=%-6s %s" % s)


def _ws_root_arg(argv):
    """取 `--ws-root <dir>` / `--ws-root=<dir>`；无则 None。"""
    for i, a in enumerate(argv):
        if a == "--ws-root" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--ws-root="):
            return a.split("=", 1)[1]
    return None


def _guard_inputs(mode):
    """输入缺失 ⇒ 打印 `INPUT_MISSING` + 明确路径，返回退出码 3（≠ 校验 1 / 变异 FAIL 1）。"""
    miss = missing_inputs()
    if not miss:
        return None
    print("== INPUT_MISSING（%s 无法执行：输入缺失，非「变异/校验失败」）==" % mode)
    for p in miss:
        print("   缺输入: %s" % p)
    print("  说明: `解出_*.tsv` 被 .gitignore 排除，须先跑：")
    print("        python -X utf8 编程组/工具/decode_sob0.py --out 编程组/SOB0解码")
    print("  再跑本命令，或用 `--ws-root <工作区根>` 指向已有输入的工作区（只读）。")
    print("CHECK_ERROR=INPUT_MISSING  files=%d" % len(miss))
    return 3


def main(argv):
    root = _ws_root_arg(argv)
    if root:
        set_ws_root(root)
    if not [a for a in argv if not a.startswith("--ws-root")]:
        print(__doc__)
        return 2
    rc = _guard_inputs(" ".join(argv))
    if rc is not None:
        if "--selfcheck-mutate" in argv:
            # 与「变异导致 check FAIL（MUTATE_SELFTEST=PASS）」和「变异未被检出（=FAIL）」均不同：
            print("MUTATE_SELFTEST=INPUT_MISSING（输入缺失，未执行变异自证；≠ 变异通过/失败）")
        return rc
    if "--gold" in argv:
        res, stat, per_tok, per_from = compare_gold("ot")
        print_gold(res, stat, per_tok, per_from, "ot")
        if "--emit" in argv:
            emit_gold(res)
        return 0
    if "--diff" in argv or "--stats" in argv:
        do_stats()
        return 0
    if "--emit" in argv:
        do_emit()
        return 0
    if "--check" in argv:
        return 0 if do_check() else 1
    if "--selfcheck-mutate" in argv:
        print("== CHECK(MUTATE: setter 配对规则 first -> last) ==")
        ok = do_check(mutate={"setter_pick": "last"})
        print("MUTATE_SELFTEST=%s（期望 check FAIL）" % ("PASS" if not ok else "FAIL"))
        return 0 if not ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
