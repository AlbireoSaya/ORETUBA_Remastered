# -*- coding: utf-8 -*-
r"""m02_states_frag_variants.py —— ★ 运行态 / 番外独立层 数据自证（`ISSUE-20260928-02` 第 2 步）

**要证的事**（冻结 §一 / §二，逐条机检）：
  A. `--preset states`：`flow_state` 五档全部出现；`locked` 有 `_dim`、`new` 有 `_new`、
     `visited` 有 `_read`、`current` **不产元素**；
     ★ **`ISSUE-20260928-03` 修正后的 `_dim` 口径**：`kind=="image"`、`asset` **按节点种类**取件
     （section/select/frag 三族）、几何与 `nine` **与同 tag 节点底图件逐字段一致**、`opacity==110`、
     `z`＝节点 `z+1`、`vis_when=="locked"`；**全库不得再出现 `kind:"rect"` 的 `_dim`**；
     ★ **`ISSUE-20260928-03` 新增 `_read`**：20×20、1:1（**无 `nine`**）、**完全落在节点可见实体面内**
     （给数值）、`vis_when=="visited"`、`z`＝节点 `z+6`、`opacity 255`、**与 `_new` 不共存**、
     不越出图表视口与画布；
     `_new` 尺寸 50×17、位置＝参照作 `(x,y−12)` 或回落 `(x+6,y+8)`、`z`＝节点 `z+6`；
     `flags_default` 的 `fc.state.<NNNN>` 与节点 `flow_state` 一一对应；
     **连线三档同屏**（normal/visited/noroute 各 ≥1）。
  B. `--preset frag`：`fc.frag<G>.*` 网格几何＝每行 3 个 / 横步 375 / 纵步 192 / 行首偏移 90 /
     原点＝视口左上 +(6,6)；★ **2026-09-30（`ISSUE-20260930-06` · 用户裁定 5）改口径**：
     **行数 = ceil(章数/3)、不设上限、组内全量产出**（旧「视口 4 行 × 3 列 ＝ 12 格、超出者不产」**作废**）
     ⇒ 本节判据＝「**产出数 == 该组章数**」（章数取自 `spine.json` 真实分组）＋逐格几何复算；
     并附**变异自证**（① 删一格 ⇒ 产出≠章数须被检出；② 某格 y +1px ⇒ 几何须被检出）；
     ★ **冻结 §7.2（2026-09-30 一审后返修）· 溢出行可见性契约**（B3 节）：交付样例 G6 的 8 个溢出格 ×3 件
     一律 `visible_default:false`（**数据完整、默认不画**；纵滚到位时置真）⇒ 双向断言（溢出却默认可画 /
     未溢出却默认不画**均须被检出**）＋ **变异自证**（把溢出件的 `visible_default` 改回 `true` 必须被检出）；
     文字口径与主干节点**逐字段一致**；**独立层不产连线**（无 links 端点在独立层锚点）；
     `fc.entry.*_hit` 的 `layer` 指向该组、**按组**返回键 `fc.frag<G>_back_hit` 的 `layer == "main"`
     （★ 第 3 批：单件 `fc.fragback*` 已退场，改按组拆；并核对 `_back` 三态键、`_back_tx` 文案「返回主干」与 27px 口径）；
     主干件 `vis_when=="main"`、独立层件 `vis_when=="frag<G>"`（**一个元素一对 flag**）。
  F. ★ **第 13 批（`ISSUE-20260929-05`）**：**两枚模式入口 `fc.mode_*`** 的载荷核对（几何/z/kind/
     `state_group`/`action`/`sample` 逐条；**每枚的三态素材在库且 1:1、无 `nine`**；
     `_hit.action` **非空且能在 `layout/_schema.md` §六 动作表里查到**；`_glow`↔`_hit` **同 `state_group`**
     且三态齐）＋ **反向断言**：本批删的 **18 件旧件**（`fc.mtab*` 12 ＋ `fc.fusen_*` 6）**均不在屏数据里**。
     （原 `GROUP_NINE` 的 `fc.fusen_edit`/`fc.fusen_reset` 两件**已删** ⇒ 移出该名单，由本节**等强度接手**：**只增不减覆盖**。）

**幂等**：只把两个预设的产出落到 `复现脚本/_out/`（生成物，可覆盖再生），**不动屏文件**；退出码 0 = 自证通过。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260928-02_第2步/复现脚本/m02_states_frag_variants.py"
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
GEN = os.path.join(UI, "工具", "gen_flow_layout.py")
OUT = os.path.join(HERE, "_out")
NODE_W, NODE_H = 296, 65

# ══════════════════════════════════════════════════════════════════════
# ★★ 2026-09-30（`ISSUE-20260930-06` · 用户裁定 5）：**番外独立层改纵向流水** ★★
#   行数 = ceil(章数 / 3)、**不设上限**、**组内全量产出**（旧口径「视口只容 4 行 × 3 列 = 12 格、
#   组内超出者不产」**已作废**）。几何常量与旧口径**逐字相同**（只取消上限）。
#   本表**独立写出**（不 import 生成器）⇒ 不自证恒真（照 `DIM_ASSET_BY_KIND` 的先例）。
# ══════════════════════════════════════════════════════════════════════
FRAG_COLS_M02 = 3
FRAG_STEP_X_M02 = 375
FRAG_STEP_Y_M02 = 192
FRAG_LEAD_Y_M02 = 90
FRAG_ORIGIN_M02 = (6, 6)


def frag_rows_m02(n):
    """独立层行数 = ceil(章数 / 3)（★ 2026-09-30 新口径；不设上限）。"""
    return (n + FRAG_COLS_M02 - 1) // FRAG_COLS_M02


def load_gen():
    """按路径加载生成器模块（取 `entry_groups()` / `load_spine()` 读真实章数；照 m03 的既用写法）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_gfl_m02", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def frag_layer_cells(els, g):
    """`fc.frag<g>.<NNNN>` 本体（**排除** `_tx`/`_hit`），按 id 排序（＝组内序）。"""
    return sorted([e for e in els if e["id"].startswith("fc.frag%d." % g)
                   and e["id"].count(".") == 2 and e.get("kind") == "image"],
                  key=lambda e: e["id"])


def frag_grid_fails(els, g, n_chapters):
    """★ 独立层网格逐格复算（**纯函数**，返回失败描述列表；空 ＝ 通过）。

    判据（2026-09-30 新口径）：① **产出数 == 该组章数**（纵向流水口径 ⇒ 不得因视口裁剪而少产）；
    ② 逐格几何 == `(视口左+6 + col×375, 视口顶+6+90 + row×192)`，`col = k%3`、`row = k//3`（k 为组内序）；
    ③ 尺寸 296×65；④ `vis_flag=="fc_layer"` / `vis_when=="frag<g>"`。
    """
    out = []
    by = {e["id"]: e for e in els}
    vp = by.get("fc.scroll")
    if vp is None:
        return ["屏内缺 `fc.scroll`（独立层网格原点无从判定）"]
    ox = vp["x"] + FRAG_ORIGIN_M02[0]
    oy = vp["y"] + FRAG_ORIGIN_M02[1] + FRAG_LEAD_Y_M02
    cells = frag_layer_cells(els, g)
    if len(cells) != n_chapters:
        out.append("独立层 %d 组产出 **%d 格** ≠ 章数 **%d**（纵向流水口径须组内全量产出 ⇒ 少产即违、"
                   "旧 12 格上限不得回归）" % (g, len(cells), n_chapters))
    for k, e in enumerate(cells):
        col, row = k % FRAG_COLS_M02, k // FRAG_COLS_M02
        want = (ox + col * FRAG_STEP_X_M02, oy + row * FRAG_STEP_Y_M02)
        if (e["x"], e["y"]) != want:
            out.append("%s 网格位 %s ≠ 期望 %s（3/行、横步 %d、纵步 %d、行首 %d、原点视口+(6,6)、"
                       "行数=ceil(章数/3)）" % (e["id"], (e["x"], e["y"]), want,
                                             FRAG_STEP_X_M02, FRAG_STEP_Y_M02, FRAG_LEAD_Y_M02))
        if (e["w"], e["h"]) != (NODE_W, NODE_H):
            out.append("%s 尺寸 %s×%s ≠ 296×65" % (e["id"], e["w"], e["h"]))
        if e.get("vis_flag") != "fc_layer" or e.get("vis_when") != "frag%d" % g:
            out.append("%s 的 flag 对不合法：%s/%s" % (e["id"], e.get("vis_flag"), e.get("vis_when")))
    return out


def mutate_frag_grid_selfcheck(frag, g, n_chapters):
    """★ 变异自证（证明 `frag_grid_fails` 非恒真）：真数据 0 失败；**节点数 −1** 与 **几何偏 1px**
    两条变异各须被对应判据检出。"""
    print("\n【B2 · ★ 2026-09-30 独立层网格判据的变异自证（证明 B 的网格判据非恒真）】")
    base = frag_grid_fails(frag["elements"], g, n_chapters)
    print("      真数据（章数 %d、rows %d）：失败 **%d 处**%s"
          % (n_chapters, frag_rows_m02(n_chapters), len(base), " ✓" if not base else " ✗"))
    if base:
        bad("独立层网格真数据已有失败（判据或数据错）：%s" % base[:3])
    ok = True
    # 变异①：删末格（含 `_tx`/`_hit`）⇒ 产出 6 ≠ 章数 7 ⇒ 必须被「产出 == 章数」判据检出
    drop_id = "fc.frag%d.%04d" % (g, n_chapters)
    mut = json.loads(json.dumps(frag))
    mut["elements"] = [e for e in mut["elements"]
                       if e["id"] not in (drop_id, drop_id + "_tx", drop_id + "_hit")]
    f1 = frag_grid_fails(mut["elements"], g, n_chapters)
    hit1 = [x for x in f1 if "≠ 章数" in x]
    print("      变异①（删 `%s` ×3 件 ⇒ 产出 %d ≠ 章数 %d）：失败 **%d 处**，其中「产出≠章数」**%d 处** %s"
          % (drop_id, len(frag_layer_cells(mut["elements"], g)), n_chapters, len(f1), len(hit1),
             "✓ 判据非恒真" if hit1 else "✗ **判据恒真**"))
    if not hit1:
        bad("变异自证失败①：少产 1 格**未被检出** ⇒ 「组内全量产出」判据恒真（旧 12 格上限回归会漏判）")
        ok = False
    # 变异②：首格 y 下移 1px ⇒ 必须被「网格位」判据检出
    mut2 = json.loads(json.dumps(frag))
    for e in mut2["elements"]:
        if e["id"] == "fc.frag%d.0001" % g:
            e["y"] += 1
    f2 = frag_grid_fails(mut2["elements"], g, n_chapters)
    hit2 = [x for x in f2 if "网格位" in x]
    print("      变异②（`fc.frag%d.0001.y` +1px）：失败 **%d 处**，其中「网格位」**%d 处** %s"
          % (g, len(f2), len(hit2), "✓ 判据非恒真" if hit2 else "✗ **判据恒真**"))
    if not hit2:
        bad("变异自证失败②：几何偏 1px **未被检出** ⇒ 网格几何判据恒真")
        ok = False
    return ok


# ══════════════════════════════════════════════════════════════════════
# ★★ 冻结 §7.2（2026-09-30 一审后返修）：**溢出行的可见性契约** ★★
#   元素盒下沿 `y + h > 视口底`（1017）的独立层元素 ⇒ `visible_default` 必须为 **False**；
#   未溢出者必须为 **True**（**双向卡**：溢出却默认可画 ＝ vision 缺陷本体；未溢出却默认不画 ＝ 误藏）。
#   纯函数（受 `screen1` 的 G6 检验；`--preset frag` 只有第 1 组、7 格全在视口内 ⇒ 不产生溢出格）。
# ══════════════════════════════════════════════════════════════════════
FRAG_CELL_ID_RE_M02 = re.compile(r"^fc\.frag(\d+)\.(\d{4})(?:_tx|_hit)?$")


def overflow_visible_fails(els, g):
    """冻结 §7.2 判据（纯函数）：返回违规描述列表（空 ＝ 通过）。"""
    out = []
    by = {e["id"]: e for e in els}
    vp = by.get("fc.scroll")
    if vp is None:
        return ["屏内缺 `fc.scroll`（视口底无从判定）"]
    vb = vp["y"] + vp["h"]
    n_ov = n_in = 0
    for e in els:
        m = FRAG_CELL_ID_RE_M02.match(str(e.get("id", "")))
        if m is None or int(m.group(1)) != g:
            continue
        want = (e["y"] + e["h"]) <= vb
        if want:
            n_in += 1
        else:
            n_ov += 1
        if bool(e.get("visible_default", True)) != want:
            out.append("%s 下沿 %d %s 视口底 %d ⇒ `visible_default` 应为 **%s**，实为 %r"
                       % (e["id"], e["y"] + e["h"], "≤" if want else ">", vb, want,
                          e.get("visible_default")))
    return out


def mutate_overflow_visible_selfcheck(scr, g, n_expect_overflow):
    """★ 变异自证（证明 §7.2 判据非恒真）：把**溢出格**的 `visible_default` 改回 `true`（三件）
    ⇒ 必须被检出；再把**未溢出格**改成 `false` ⇒ 也必须被检出（双向判据都要能失败）。"""
    print("\n【B3 · ★ 冻结 §7.2 溢出行可见性契约 —— 真数据核对 ＋ 变异自证】")
    els = scr["elements"]
    bads = overflow_visible_fails(els, g)
    ov_ids = sorted({e["id"] for e in els
                     if FRAG_CELL_ID_RE_M02.match(str(e.get("id", "")))
                     and int(FRAG_CELL_ID_RE_M02.match(str(e["id"])).group(1)) == g
                     and (e["y"] + e["h"]) > (next(x for x in els if x["id"] == "fc.scroll")["y"]
                                              + next(x for x in els if x["id"] == "fc.scroll")["h"])})
    print("      真数据（G%d）：带 `visible_default:false` 的溢出件 **%d 件**（预期 %d）｜ 违规 **%d 处**%s"
          % (g, len(ov_ids), n_expect_overflow, len(bads), " ✓" if not bads else " ✗"))
    if bads:
        bad("§7.2 真数据违规：%s" % bads[:3])
    if len(ov_ids) != n_expect_overflow:
        bad("§7.2 溢出件数 %d ≠ 预期 %d" % (len(ov_ids), n_expect_overflow))
    ok = True
    # 变异①：把**溢出格**的 `visible_default` 全改回 true ⇒ 必须被检出
    mut = json.loads(json.dumps(scr))
    for e in mut["elements"]:
        if e["id"] in ov_ids:
            e["visible_default"] = True
    f1 = overflow_visible_fails(mut["elements"], g)
    hit1 = [x for x in f1 if "应为 **False**" in x]
    print("      变异①（把 %d 件溢出件改回 `visible_default:true`）：失败 **%d 处**，"
          "其中「应为 False」**%d 处** %s"
          % (len(ov_ids), len(f1), len(hit1), "✓ 判据非恒真" if hit1 else "✗ **判据恒真**"))
    if not hit1:
        bad("变异自证失败①：溢出件改回默认可画**未被检出** ⇒ §7.2 判据恒真（vision 缺陷会漏判）")
        ok = False
    # 变异②：把**未溢出格**改成 false ⇒ 必须被检出（防「一律置 false」蒙过判据）
    in_ids = [e["id"] for e in scr["elements"]
              if FRAG_CELL_ID_RE_M02.match(str(e.get("id", "")))
              and int(FRAG_CELL_ID_RE_M02.match(str(e["id"])).group(1)) == g
              and e["id"] not in ov_ids]
    mut2 = json.loads(json.dumps(scr))
    for e in mut2["elements"]:
        if e["id"] in in_ids:
            e["visible_default"] = False
    f2 = overflow_visible_fails(mut2["elements"], g)
    hit2 = [x for x in f2 if "应为 **True**" in x]
    print("      变异②（把 %d 件未溢出件改成 `visible_default:false`）：失败 **%d 处**，"
          "其中「应为 True」**%d 处** %s"
          % (len(in_ids), len(f2), len(hit2), "✓ 判据非恒真" if hit2 else "✗ **判据恒真**"))
    if not hit2:
        bad("变异自证失败②：未溢出件改默认不画**未被检出** ⇒ §7.2 判据恒真（误藏会漏判）")
        ok = False
    return ok


# ★ ISSUE-20260928-03：逐种类压暗件（与生成器 `DIM_ASSET_BY_KIND` 同表；此处独立写出＝不自证恒真）
DIM_ASSET_BY_KIND = {
    "section": "ui/x_ui_node_section_dim.png",
    "select":  "ui/x_ui_node_select_dim.png",
    "frag":    "ui/x_ui_node_frag_dim.png",
}
NODE_ASSET_BY_KIND = {
    "section": "ui/x_ui_node_section_off.png",
    "select":  "ui/x_ui_node_select_off.png",
    "frag":    "ui/x_ui_node_frag_off.png",
}
# 节点可见实体面（相对节点元素矩形）：x+6, y+8, 284×48
PLATE_OFF_X, PLATE_OFF_Y, PLATE_W, PLATE_H = 6, 8, 284, 48
READ_ASSET = "ui/x_ui_read_check.png"
READ_W, READ_H = 20, 20
READ_OFF = (10, 12)

# ══════════════════════════════════════════════════════════════════════
# ★★ 第 13 批（`ISSUE-20260929-05`）：两枚**模式入口** `fc.mode_*` 的载荷核对（【F】节）
#   口径与素材名以**接口冻结 §B ＋ E1 实际产出**为准（E1 产出 **3 件共用**、两入口共用同一套）。
#   本表**独立写出**（不 import 生成器）⇒ 不自证恒真（照 DIM_ASSET_BY_KIND 的先例）。
# ══════════════════════════════════════════════════════════════════════
MODE_ASSET_TRI = {"normal": "ui/x_ui_modetab_off.png",
                  "hover": "ui/x_ui_modetab_over.png",
                  "pressed": "ui/x_ui_modetab_press.png"}
#   id → (kind, x, y, w, h, z, state_group|None, action|None, sample|None)
#   ★ E5 一轮（用户 2026-09-29 裁决「两个模式入口的文字下移 8px」）：两件 `_tx` 的 y **25 → 33**
#     （`_glow`/`_hit` 仍 25；口径＝「同 x/w/h、`y = _glow.y + 8`」，与生成器 `MODE_ENTRY_TX_DY` 同值）。
MODE_SPEC = {
    "fc.mode_main_glow": ("image", 34, 25, 180, 60, 10, "mode_main", None, None),
    "fc.mode_main_tx":   ("text", 34, 33, 180, 60, 20, None, None, "本篇集合"),
    "fc.mode_main_hit":  ("hit", 34, 25, 180, 60, 95, "mode_main", "flow_mode_main", None),
    "fc.mode_frag_glow": ("image", 254, 25, 180, 60, 10, "mode_frag", None, None),
    "fc.mode_frag_tx":   ("text", 254, 33, 180, 60, 20, None, None, "番外故事"),
    "fc.mode_frag_hit":  ("hit", 254, 25, 180, 60, 95, "mode_frag", "flow_mode_frag", None),
}
# 反向断言：本批**已删**的 18 件旧件（12 模式页签 ＋ 6 备注键）**均不得再出现在屏数据里**
REMOVED_BATCH13 = (
    ["fc.mtab%d%s" % (n, s) for n in (1, 2, 3, 4) for s in ("", "_tx", "_hit")]
    + ["fc.fusen_%s%s" % (k, s) for k in ("edit", "reset") for s in ("", "_tx", "_hit")]
)

FAILS = []


def bad(msg):
    FAILS.append(msg)
    print("      ✗ %s" % msg)


def gen(preset, path):
    os.makedirs(OUT, exist_ok=True)
    r = subprocess.run([sys.executable, GEN, "--preset", preset, "--out", path],
                       cwd=UI, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[FAIL] 生成 %s 失败（rc=%d）：%s" % (preset, r.returncode, r.stderr[-400:]))
    return json.load(open(path, encoding="utf-8"))


def is_node_image(e):
    """`fc.node.<NNNN>` 本体（**排除** `_tx`/`_hit`/`_dim`/`_new` 这些后缀件）。"""
    i = e.get("id", "")
    if e.get("kind") != "image" or not i.startswith("fc.node."):
        return False
    tail = i.split(".")[-1]
    return len(tail) == 4 and tail.isdigit()


def check_states(scr):
    print("\n【A · --preset states（冻结 §一 运行态）】")
    els = scr["elements"]
    by = {e["id"]: e for e in els}
    nodes = [e for e in els if is_node_image(e)]
    sts = {}
    for e in nodes:
        s = e.get("flow_state")
        if s is None:
            bad("%s 缺 `flow_state`（states 预设应逐节点写出）" % e["id"])
            continue
        sts[s] = sts.get(s, 0) + 1
    print("      flow_state 分布：%s" % sts)
    for s in ("locked", "available", "visited", "current", "new"):
        if s not in sts:
            bad("states 预设未演示状态 `%s`（冻结 §一.1 五档都要能演示）" % s)
    print("      五档齐备：%s" % ("✓" if len(sts) == 5 else "✗"))

    # _dim / _new / _read：数量、几何、z、flag
    ndim = nnew = nread = 0
    dim_rows, read_rows = [], []
    for e in nodes:
        tag = e["id"].split(".")[-1]
        s = e.get("flow_state")
        dim = by.get("fc.node.%s_dim" % tag)
        new = by.get("fc.node.%s_new" % tag)
        read = by.get("fc.node.%s_read" % tag)
        kind = e.get("kind")   # 节点本体 kind（image）；节点**种类**须由底图件反推
        nkind = next((k for k, a in NODE_ASSET_BY_KIND.items() if a == e.get("asset")), None)
        if nkind is None:
            bad("%s 的底图件 %r 不在三种底图内（无法判种类 ⇒ `_dim` 无法核对）" % (e["id"], e.get("asset")))
        if s == "locked":
            if dim is None:
                bad("%s 为 locked 但无 `_dim` 叠层" % e["id"]); continue
            ndim += 1
            # ★ ISSUE-20260928-03：`_dim` 改 image、按种类取件、几何与 nine 与**底图件逐字段一致**
            if dim.get("kind") != "image":
                bad("%s 的 `_dim` kind=%r ≠ image（ISSUE-20260928-03 修正：rect 方角⇒image）"
                    % (e["id"], dim.get("kind")))
            if nkind is not None and dim.get("asset") != DIM_ASSET_BY_KIND[nkind]:
                bad("%s（%s）的 `_dim` asset=%r ≠ 该种类应取 %r"
                    % (e["id"], nkind, dim.get("asset"), DIM_ASSET_BY_KIND[nkind]))
            for f in ("x", "y", "w", "h"):
                if dim.get(f) != e.get(f):
                    bad("%s 的 `_dim`.%s=%r ≠ 节点底图件 %r（ISSUE-20260928-03：几何逐字段一致）"
                        % (e["id"], f, dim.get(f), e.get(f)))
            if dim.get("nine") != e.get("nine"):
                bad("%s 的 `_dim`.nine=%r ≠ 节点底图件 nine %r（逐字段一致）"
                    % (e["id"], dim.get("nine"), e.get("nine")))
            if "color" in dim:
                bad("%s 的 `_dim` 仍有 `color` 键（改 image 后不得再有）" % e["id"])
            if dim.get("z") != e.get("z", 20) + 1:
                bad("%s 的 `_dim` z=%s ≠ 节点 z+1" % (e["id"], dim.get("z")))
            if dim.get("vis_flag") != "fc.state." + tag or dim.get("vis_when") != "locked":
                bad("%s 的 `_dim` flag 对不合法：%s/%s" % (e["id"], dim.get("vis_flag"), dim.get("vis_when")))
            if dim.get("opacity") != 110:
                bad("%s 的 `_dim` opacity=%s ≠ 110（强度旋钮保持 110）" % (e["id"], dim.get("opacity")))
            dim_rows.append((e["id"], nkind, dim.get("asset"), (dim.get("x"), dim.get("y"),
                           dim.get("w"), dim.get("h")), dim.get("nine"), dim.get("z"), dim.get("opacity")))
        elif s == "new":
            if new is None:
                bad("%s 为 new 但无 `_new` 角标" % e["id"]); continue
            nnew += 1
            if (new["w"], new["h"]) != (50, 17):
                bad("%s 的 `_new` 尺寸 %s×%s ≠ 50×17" % (e["id"], new["w"], new["h"]))
            pref = (e["x"], e["y"] - 12)
            fb = (e["x"] + 6, e["y"] + 8)
            if (new["x"], new["y"]) not in (pref, fb):
                bad("%s 的 `_new` 落点 %s 既非参照作 %s 也非回落 %s"
                    % (e["id"], (new["x"], new["y"]), pref, fb))
            if new.get("z") != e.get("z", 20) + 6:
                bad("%s 的 `_new` z=%s ≠ 节点 z+6" % (e["id"], new.get("z")))
            if new.get("vis_flag") != "fc.state." + tag or new.get("vis_when") != "new":
                bad("%s 的 `_new` flag 对不合法" % e["id"])
        elif s == "visited":
            # ★ ISSUE-20260928-03 新增：已读绿对勾 `_read`
            if read is None:
                bad("%s 为 visited 但无 `_read` 已读对勾（ISSUE-20260928-03 新增）" % e["id"]); continue
            nread += 1
            if read.get("kind") != "image":
                bad("%s 的 `_read` kind=%r ≠ image" % (e["id"], read.get("kind")))
            if read.get("asset") != READ_ASSET:
                bad("%s 的 `_read` asset=%r ≠ %r" % (e["id"], read.get("asset"), READ_ASSET))
            if (read.get("w"), read.get("h")) != (READ_W, READ_H):
                bad("%s 的 `_read` 尺寸 %s×%s ≠ %d×%d" % (e["id"], read.get("w"), read.get("h"),
                                                        READ_W, READ_H))
            if "nine" in read:
                bad("%s 的 `_read` 不应带 `nine`（1:1 件）" % e["id"])
            # 机检①：**完全落在节点可见实体面内**（给数值）
            px0, py0 = e["x"] + PLATE_OFF_X, e["y"] + PLATE_OFF_Y
            inx = read["x"] >= px0 and read["x"] + read["w"] <= px0 + PLATE_W
            iny = read["y"] >= py0 and read["y"] + read["h"] <= py0 + PLATE_H
            if not (inx and iny):
                bad("%s 的 `_read` 落点 %s 越出可见实体面 %s"
                    % (e["id"], (read["x"], read["y"], read["w"], read["h"]),
                       (px0, py0, PLATE_W, PLATE_H)))
            if (read.get("x") - e["x"], read.get("y") - e["y"]) != READ_OFF:
                bad("%s 的 `_read` 相对落点 %s ≠ %s（节点可见实体面左上角内缘）"
                    % (e["id"], (read.get("x") - e["x"], read.get("y") - e["y"]), READ_OFF))
            if read.get("z") != e.get("z", 20) + 6:
                bad("%s 的 `_read` z=%s ≠ 节点 z+6（与 `_new` 同档）" % (e["id"], read.get("z")))
            if read.get("opacity") != 255:
                bad("%s 的 `_read` opacity=%s ≠ 255" % (e["id"], read.get("opacity")))
            if read.get("vis_flag") != "fc.state." + tag or read.get("vis_when") != "visited":
                bad("%s 的 `_read` flag 对不合法：%s/%s" % (e["id"], read.get("vis_flag"), read.get("vis_when")))
            if new is not None:
                bad("%s 同时产了 `_new` 与 `_read`（new/visited 语义互斥 ⇒ 不得共存）" % e["id"])
            read_rows.append((e["id"], (read["x"], read["y"], read["w"], read["h"]),
                              (px0, py0, PLATE_W, PLATE_H),
                              (read["x"] - px0, read["y"] - py0,
                               px0 + PLATE_W - (read["x"] + read["w"]), py0 + PLATE_H - (read["y"] + read["h"])),
                              read.get("z")))
        else:
            if dim is not None or new is not None or read is not None:
                bad("%s 为 %s（无叠加档）却产出了叠加件" % (e["id"], s))
    print("      `_dim` %d 件 / `_new` %d 件 / `_read` %d 件（locked %d / new %d / visited %d）%s"
          % (ndim, nnew, nread, sts.get("locked", 0), sts.get("new", 0), sts.get("visited", 0),
             "✓" if (ndim == sts.get("locked", 0) and nnew == sts.get("new", 0)
                      and nread == sts.get("visited", 0)) else "✗"))
    print("      ★ `_dim`（ISSUE-20260928-03 修正后）：kind=image、按种类取件、几何/nine 与底图件逐字段一致")
    for i, nk, a, g, nine, z, op in dim_rows:
        print("        %-11s 种类 %-7s asset %-30s 几何 %s nine %s z=%s opacity=%s"
              % (i, nk, (a or "").split("/")[-1], g, nine, z, op))
    print("      ★ `_read`（ISSUE-20260928-03 新增）：20×20、落点与可见实体面的余量（左/上 | 右/下）")
    for i, g, plate, margins, z in read_rows:
        print("        %-12s 落点 %s ｜ 实体面 %s ｜ 余量 左%d/上%d ｜ 右%d/下%d ｜ z=%s ⇒ 完全落在实体面内 ✓"
              % (i, g, plate, margins[0], margins[1], margins[2], margins[3], z))
    print("      `current` 不产元素：%s" % ("✓" if not any(i.endswith("_cur") for i in by) else "✗"))

    flags = scr.get("flags_default") or {}
    if flags.get("fc_layer") != "main":
        bad("屏级 flags_default 缺 {\"fc_layer\":\"main\"}：%s" % flags)
    bad_kv = []
    for e in nodes:
        tag = e["id"].split(".")[-1]
        if flags.get("fc.state." + tag) != e.get("flow_state"):
            bad_kv.append(tag)
    print("      flags_default 逐节点 fc.state.<NNNN> 与 flow_state 一致：%s"
          % ("✓" if not bad_kv else "✗ " + str(bad_kv)))
    if bad_kv:
        bad("flags_default 与 flow_state 不一致：%s" % bad_kv)

    hist = {}
    for lk in scr["links"]:
        hist[lk["state"]] = hist.get(lk["state"], 0) + 1
    print("      连线三档：%s %s" % (hist, "✓" if len(hist) == 3 else "✗ 未同屏"))
    if len(hist) != 3:
        bad("states 预设未做到「三档连线同屏」：%s" % hist)


def check_frag(scr, n_chapters):
    print("\n【B · --preset frag（★ 2026-09-30 纵向流水口径）】")
    els = scr["elements"]
    by = {e["id"]: e for e in els}
    G = 1
    cells = frag_layer_cells(els, G)
    rows = frag_rows_m02(n_chapters)
    print("      独立层节点 %d 格（章数 %d ⇒ rows = ceil(%d/3) = **%d**；★ 纵向流水：无 12 格上限）"
          % (len(cells), n_chapters, n_chapters, rows))
    if not cells:
        bad("frag 预设没有独立层节点（fc.frag%d.<NNNN>）" % G)
        return
    vp = by["fc.scroll"]
    ox, oy = vp["x"] + FRAG_ORIGIN_M02[0], vp["y"] + FRAG_ORIGIN_M02[1] + FRAG_LEAD_Y_M02
    grid_fails = frag_grid_fails(els, G, n_chapters)
    ok_grid = not grid_fails
    for x in grid_fails:
        bad(x)
    # 文字口径 / 三件套（几何由 `frag_grid_fails` 复算 ⇒ 此处只管文字与件齐）
    for k, e in enumerate(cells):
        tx = by.get(e["id"] + "_tx")
        if tx is None:
            bad("%s 缺 `_tx`" % e["id"]); continue
        if (tx["x"], tx["y"], tx["w"], tx["h"]) != (e["x"] + 28, e["y"], 240, NODE_H):
            bad("%s 的 `_tx` 几何 %s ≠ (x+28,y,240,65)（与主干节点同口径）"
                % (e["id"], (tx["x"], tx["y"], tx["w"], tx["h"])))
        if tx.get("font", {}).get("size") != 19 or tx.get("line_spacing") != 1.0 \
                or tx.get("max_lines") != 2 or not tx.get("sample"):
            bad("%s 的文字口径 ≠ 19px / 行距 1.0 / max_lines 2 / 有 sample" % e["id"])
        if by.get(e["id"] + "_hit") is None:
            bad("%s 缺 `_hit`" % e["id"])
    print("      网格（3/行、横步 375、纵步 192、行首 90、原点视口+(6,6)、**rows=ceil(章数/3)**、"
          "**产出 == 章数**）%s ｜ 文字口径（19/1.0/240/max2）与主干一致 ✓"
          % ("✓" if ok_grid else "✗"))

    # 独立层不产连线
    main_anchor, frag_anchor = set(), set()
    for e in els:
        if e.get("kind") != "image":
            continue
        i = e["id"]
        if i.startswith("fc.node.") and (e["w"], e["h"]) == (NODE_W, NODE_H):
            main_anchor.add((e["x"] + 148, e["y"] + NODE_H))
            main_anchor.add((e["x"] + 148, e["y"]))
        elif i.startswith("fc.frag%d." % G) and (e["w"], e["h"]) == (NODE_W, NODE_H) and "." in i:
            frag_anchor.add((e["x"] + 148, e["y"] + NODE_H))
            frag_anchor.add((e["x"] + 148, e["y"]))
    hit = [lk["id"] for lk in scr["links"]
           if tuple(lk["pts"][0]) in frag_anchor or tuple(lk["pts"][-1]) in frag_anchor]
    print("      独立层不产连线：%s（%d 条连线中命中独立层锚点 %d 条）"
          % ("✓" if not hit else "✗", len(scr["links"]), len(hit)))
    if hit:
        bad("有连线端点在独立层节点上：%s" % hit)

    # 入口热区 / **按组**返回键的 layer（★ 第 3 批：`fc.fragback*` 单件 → `fc.frag<G>_back*` 按组）
    ents = [e for e in els if e["id"].startswith("fc.entry.") and e["id"].endswith("_hit")]
    back_img = "fc.frag%d_back" % G
    back_tx = "fc.frag%d_back_tx" % G
    back_hit = "fc.frag%d_back_hit" % G
    print("      入口热区 %d 个（layer 指向 %s…）｜ 按组返回键 %s / %s / %s"
          % (len(ents), ents[0].get("layer") if ents else "-", back_img, back_tx, back_hit))
    for e in ents:
        if e.get("action") != "flow_layer" or not str(e.get("layer", "")).startswith("frag"):
            bad("%s 的 action/layer 不合法：%s/%s" % (e["id"], e.get("action"), e.get("layer")))
    if by.get(back_hit, {}).get("action") != "flow_layer" or by.get(back_hit, {}).get("layer") != "main":
        bad("%s 必须是 action=flow_layer / layer=main（★ 第 3 批按组）" % back_hit)
    if "fc.fragback" in by or "fc.fragback_hit" in by:
        bad("第 3 批口径：单件 `fc.fragback`/`fc.fragback_hit` 应已退场（改按组 `%s`）" % back_hit)
    bimg = by.get(back_img, {})
    if bimg.get("state_assets", {}).get("on") is not None:
        bad("%s 的 state_assets 键应为 normal/hover/pressed" % back_img)
    if bimg.get("vis_when") != "frag%d" % G or by.get(back_hit, {}).get("vis_when") != "frag%d" % G:
        bad("%s / %s 的 vis_when 必须同组 `frag%d`" % (back_img, back_hit, G))
    btx = by.get(back_tx)
    if btx is None:
        bad("缺按组返回键文字件 %s（第 3 批新增）" % back_tx)
    else:
        if btx.get("sample") != "返回主干":
            bad("%s 的文案应为「返回主干」，实为 %r" % (back_tx, btx.get("sample")))
        if btx.get("font", {}).get("size") != 27:
            bad("%s 的字号应取 `fc.jump_tx` 口径 27，实为 %s" % (back_tx, btx.get("font", {}).get("size")))
    # 主干件 vis_when == main、独立层件 vis_when == frag<G>
    layer_vals = sorted({e.get("vis_when") for e in els if e.get("vis_flag") == "fc_layer"})
    print("      fc_layer 的 vis_when 取值集：%s %s"
          % (layer_vals, "✓" if layer_vals == ["frag1", "main"] else "（期望 [frag1, main]）"))
    if layer_vals != ["frag1", "main"]:
        bad("fc_layer 的取值集不是 [frag1, main]：%s" % layer_vals)
    dup = [e["id"] for e in els if "vis_flag" in e and "vis_when" not in e]
    if dup:
        bad("有元素只写 vis_flag 没写 vis_when：%s" % dup)


def check_overlay_global(arts):
    r"""★ ISSUE-20260928-03 全库机检（五预设一起卡，不只是 states）：

      ① **全库再无 `kind:"rect"` 的 `_dim`**（「未解锁压暗件方角」缺陷不得回潮）；
      ② 任何 `_read` 与同 tag 的 `_new` **不共存**（`new`/`visited` 语义互斥）；
      ③ 任何 `_read` **不越出图表视口**（`fc.scroll`）**与画布**（`layout/_root.json` 的 canvas）。
    """
    print("\n【E · ★ ISSUE-20260928-03 全库机检（`_dim` 无 rect / `_read`↔`_new` 不共存 / `_read` 不出视口画布）】")
    root = json.load(open(os.path.join(UI, "layout", "_root.json"), encoding="utf-8"))
    cw, ch = root["canvas"]["width"], root["canvas"]["height"]
    rect_dims, coexist, out_vp, out_cv, n_read_total = [], [], [], [], 0
    for name, scr in sorted(arts.items()):
        els = scr["elements"]
        ids = {e["id"] for e in els}
        by = {e["id"]: e for e in els}
        for e in els:
            if e["id"].endswith("_dim") and e.get("kind") == "rect":
                rect_dims.append((name, e["id"]))
        for i in sorted(x for x in ids if x.endswith("_read")):
            n_read_total += 1
            if (i[:-5] + "_new") in ids:
                coexist.append((name, i))
            r = by[i]
            vp = by["fc.scroll"]
            inside_vp = (vp["x"] <= r["x"] and r["x"] + r["w"] <= vp["x"] + vp["w"]
                         and vp["y"] <= r["y"] and r["y"] + r["h"] <= vp["y"] + vp["h"])
            inside_cv = (0 <= r["x"] and r["x"] + r["w"] <= cw
                         and 0 <= r["y"] and r["y"] + r["h"] <= ch)
            if not inside_vp:
                out_vp.append((name, i))
            if not inside_cv:
                out_cv.append((name, i))
    print("      ① 全库 `kind:\"rect\"` 的 `_dim`：**%d 件**%s"
          % (len(rect_dims), "（✓ 方角件已绝迹）" if not rect_dims else " ← **缺陷回潮**：%s" % rect_dims))
    if rect_dims:
        bad("仍有 rect 版 `_dim`：%s" % rect_dims)
    print("      ② `_read` 与同 tag `_new` 共存：**%d 对**%s"
          % (len(coexist), "（✓ 互斥成立）" if not coexist else " ← **违规**：%s" % coexist))
    if coexist:
        bad("`_read` 与 `_new` 共存：%s" % coexist)
    print("      ③ `_read` 越出图表视口 %d 件 ｜ 越出画布（%d×%d） %d 件（全库 `_read` 共 %d 件）%s"
          % (len(out_vp), cw, ch, len(out_cv), n_read_total,
             "✓" if not out_vp and not out_cv else " ← **违规**"))
    if out_vp or out_cv:
        bad("`_read` 越界：视口 %s / 画布 %s" % (out_vp, out_cv))


def check_other_presets_pristine(arts):
    r"""★ 主代理裁决 6：**只有 `states` 预设**写 `fc.state.<NNNN>` / `flow_state`，其余预设不得出现这些键。

    ★ 第 11 批（`ISSUE-20260929-02`）订正：屏级 `flags_default` 现**合法地**多出一个非运行态键
    **`fc_replay`**（右栏播放/暂停键的互斥 flag，初值 `"play"`，五档都该有）⇒ 白名单放行它；
    但**放行的只是这一个具名键**（其余任何额外键仍判失败），`fc.state.*` / `flow_state` 的素净要求不变；
    并新增一条正向断言：五档都必须有 `fc_replay` 且初值为 `"play"`。
    ★ 第 15 批（`ISSUE-20260930-02`）再订正：**`fc_intro`**（章节详情浮层开合 flag，初值 `"closed"`，
      五档都该有）**同样具名放行**；并新增正向断言「五档都必须有 `fc_intro` 且初值为 `"closed"`」。
    """
    print("\n【C · 裁决 6：`fc.state.*` / `flow_state` 只允许出现在 states 预设】")
    # ★ 第 11 批放行 `fc_replay`；★ 第 15 批放行 `fc_intro`（两者都是**非运行态**的具名屏级 flag）
    allowed_extra = {"fc_replay", "fc_intro"}
    for name, scr in arts.items():
        flags = scr.get("flags_default") or {}
        extra = sorted(k for k in flags if k != "fc_layer")
        extra_bad = [k for k in extra if k not in allowed_extra]
        has_replay = "fc_replay" in flags
        has_intro = "fc_intro" in flags
        n_fs = [e["id"] for e in scr["elements"] if "flow_state" in e]
        n_sf = sorted({e.get("vis_flag") for e in scr["elements"]
                       if str(e.get("vis_flag") or "").startswith("fc.state.")})
        if name == "states":
            ok = extra and n_fs and n_sf
            print("      %-8s flags_default 额外键 %d 个 ｜ 带 flow_state %d 件 ｜ fc.state.* 旗标 %d 种 ⇒ %s（演示必需）"
                  % (name, len(extra), len(n_fs), len(n_sf), "✓" if ok else "✗ 未见演示要素"))
            if not ok:
                bad("states 预设缺演示要素：flags=%s / flow_state=%d / fc.state=%d" % (extra, len(n_fs), len(n_sf)))
        else:
            ok = ((not extra_bad) and (not n_fs) and (not n_sf) and flags.get("fc_layer") == "main")
            print("      %-8s flags_default = %s ｜ 额外键 %s（白名单外 %s）｜ fc_replay=%s ｜ 带 flow_state %d 件 ⇒ %s"
                  % (name, flags, extra, extra_bad or "无", has_replay, len(n_fs),
                     "✓ 素净" if ok else "✗ 不应出现"))
            if not ok:
                bad("%s 预设不应出现 fc.state.*/flow_state/白名单外屏级键：flags=%s / flow_state=%d 件 / 旗标 %s"
                    % (name, flags, len(n_fs), n_sf))
        if not has_replay:
            bad("%s 缺屏级 flag `fc_replay`（第 11 批：右栏播放/暂停键互斥用，初值 \"play\"）" % name)
        elif flags.get("fc_replay") != "play":
            bad("%s 的 `fc_replay` 初值应为 \"play\"，实为 %r" % (name, flags.get("fc_replay")))
        if not has_intro:
            bad("%s 缺屏级 flag `fc_intro`（第 15 批：章节详情浮层开合用，初值 \"closed\"）" % name)
        elif flags.get("fc_intro") != "closed":
            bad("%s 的 `fc_intro` 初值应为 \"closed\"（进屏默认关闭浮层），实为 %r" % (name, flags.get("fc_intro")))


def check_batch2_wiring(scr):
    r"""★ 第 2 批补接线自证（主代理裁决 1 + 二.1–4）：8 件静态件的 `state_assets` 与几何。

    判据：① 三态键齐全（normal/hover/pressed）且文件存在；② **`normal` 与元素矩形 1:1**（无 nine 时
    `verify_ui [2]` 的硬判据）；③ 7 件**无 `nine`**；④ `action` 保持空串；⑤ **★ 第 11 批换口径**：
    原 `fc.pbk_panel` 判据随该件**退场**作废，改为 —— 退场 12 件**必须真的不在**数据里 ＋ 新四件
    （`fc.play_win` / `fc.play_view` / `fc.pbkick` / `fc.pbkick_pause` / `fc.pbkick_hit`）逐件查几何、
    1:1、无 `nine`、`vis_flag:"fc_replay"` **严格互斥**、`dynamic:"flow_scene_frames"`、`action:"flow_replay_toggle"`
    （**同强度的替代判据，不是降低覆盖**）。
    """
    print("\n【D · 静态件接线自证（★ 第 11 批：原「7 件占位换真件 ＋ 1 件新增」口径已随右栏大改重写 —— 见下）】")
    by = {e["id"]: e for e in scr["elements"]}
    assets_dir = os.path.join(UI, "krkr", "assets", "ui")
    # ★ 两组口径不同（主代理裁决 二.5）：
    #   · `GROUP_1TO1`：第二批 7 件占位换真件 —— **必须 1:1 且删 nine**（新件与元素矩形等尺寸）
    #   · `GROUP_NINE`：第一批 2 件付箋 —— 元素是 145×48 的设计盒、素材 86×48 ⇒ **仍走 nine 横向拉伸**
    #     （删 nine 会把整图 1.69× 拉伸变形）；只要求 `nine` 边距 ≤ 素材短边一半、且 w ≥ l+r、h ≥ t+b
    GROUP_1TO1 = ("fc.pbkick", "fc.zoom_minus", "fc.zoom_plus",
                  "fc.shift_lf", "fc.shift_rg", "fc.scr_up", "fc.scr_dn")
    # ★★ 第 13 批（`ISSUE-20260929-05`）：原 `GROUP_NINE = ("fc.fusen_edit", "fc.fusen_reset")`
    #   —— 用户裁定「不再需要备注功能」⇒ **两件元素已删**，再按旧名单核会直接 `bad("不在屏数据里")`。
    #   处置：**移出**该两件；覆盖不得减少 ⇒ 由【F】节的**三段新断言**接手（六件 `fc.mode_*` 的三态素材在库
    #   且 1:1 无 `nine`／`_hit.action` 非空且**在 §六 动作表内**／同 `state_group` 的 `_glow`+`_hit` 配对且三态齐），
    #   另有【F】④ 的**反向断言**（18 件旧件均不在屏数据里）。**只增不减覆盖**。
    GROUP_NINE = ()
    for eid in GROUP_1TO1 + GROUP_NINE:
        e = by.get(eid)
        if e is None:
            bad("%s 不在屏数据里" % eid); continue
        sa = e.get("state_assets") or {}
        keys = sorted(sa)
        if keys != ["hover", "normal", "pressed"]:
            bad("%s 的 state_assets 键不是 normal/hover/pressed：%s" % (eid, keys)); continue
        miss_files = [v for v in sa.values() if not os.path.exists(os.path.join(assets_dir, os.path.basename(v)))]
        if miss_files:
            bad("%s 的三态件缺文件：%s" % (eid, miss_files))
        nrm = sa["normal"].split("/")[-1]
        with Image.open(os.path.join(assets_dir, nrm)) as im:
            nsz = im.size
        act_ok = e.get("action", "") == ""
        if eid in GROUP_1TO1:
            one2one = nsz == (e.get("w"), e.get("h"))
            no_nine = "nine" not in e
            ok = one2one and no_nine and act_ok and not miss_files
            print("      %-14s ｜ normal %s %sx%s ＝ 元素 %sx%s ⇒ %s ｜ 无 nine=%s ｜ action=%r ⇒ %s"
                  % (eid, nrm, nsz[0], nsz[1], e.get("w"), e.get("h"),
                     "1:1 ✓" if one2one else "**非 1:1**", no_nine, e.get("action", ""), "✓" if ok else "✗"))
            if not one2one:
                bad("%s 的 normal 素材 %sx%s ≠ 元素 %sx%s（无 nine 时 verify_ui [2] 会红）"
                    % (eid, nsz[0], nsz[1], e.get("w"), e.get("h")))
            if not no_nine:
                bad("%s 仍带 `nine`（第二批口径：1:1 件删除 nine）" % eid)
        # ★ E5 S2（2026-09-29）：**删死码** —— 原 `else:` 分支是 `GROUP_NINE`（九宫格两件付箋）的口径，
        #   而该名单自第 13 批起为 `()`（两件元素已删）⇒ 分支**永不进入**。留着会让后人以为付箋两件
        #   还在名单里。**只删死码、不动任何在跑的判据**：`GROUP_1TO1` 那一支逐字未动，
        #   付箋两件的覆盖由【F】节的三段等强度断言 ＋ 反向 18 件断言接手（见上方 `GROUP_NINE` 注）。
        #   （原 `else` 分支原文见 `git show HEAD:…m02_states_frag_variants.py`。）
        if not act_ok:
            bad("%s 的 action 应为空串（行为属编程组）：%r" % (eid, e.get("action")))

    # ── ★ 第 11 批（`ISSUE-20260929-02`）：右栏大改 —— 旧「回放窗底板」退场，改查新的四段件 ──
    #   口径替换说明：原 `fc.pbk_panel` 六项判据（几何/`z=fc.p_player−1`/外壳无旗标/素材 426×241/无 nine）
    #   随该元素**退场**整体作废（不是删掉覆盖，而是**换成对新件的同强度判据**）：
    #     · 退场件必须**真的不在**数据里（防「删了又悄悄加回」）；
    #     · 新四件（大播放窗底板 / 画面层 / 播放键 / 暂停键 / 共用热区）逐件查几何、1:1、无 nine、
    #       `vis_flag:"fc_replay"` 严格互斥、`dynamic:"flow_scene_frames"`、`action:"flow_replay_toggle"`。
    if "fc.pbk_panel" in by:
        bad("`fc.pbk_panel` 已随第 11 批退场（用户裁决「场景回放组退场」）⇒ 数据里不应再有")
    if "fc.p_player" in by or "fc.p_player_tx" in by or "fc.mapview" in by \
            or any(("fc.mini%d" % _n) in by for _n in range(1, 9)):
        bad("第 11 批退场的 12 件仍有残留：%s"
            % [i for i in ("fc.p_player", "fc.p_player_tx", "fc.mapview")
               + tuple("fc.mini%d" % _n for _n in range(1, 9)) if i in by])

    def _chk_image(eid, want, asset, size, no_nine=True):
        e = by.get(eid)
        if e is None:
            bad("第 11 批：缺 `%s`" % eid)
            return None
        got = (e.get("x"), e.get("y"), e.get("w"), e.get("h"))
        s = None
        if asset:
            sub = os.path.join(assets_dir, os.path.basename(e.get("asset") or ""))
            s = Image.open(sub).size if os.path.exists(sub) else None
        ok = (got == want) and (asset is None or e.get("asset") == asset) \
            and (size is None or s == size) and ((not no_nine) or ("nine" not in e))
        print("      %-16s %s %s ｜ 素材 %s ⇒ %s"
              % (eid, e.get("asset"), got, s, "✓" if ok else "✗"))
        if got != want:
            bad("%s 几何 %s ≠ 第 11 批冻结 %s" % (eid, got, want))
        if asset is not None and e.get("asset") != asset:
            bad("%s 的 asset=%r ≠ 冻结 %r" % (eid, e.get("asset"), asset))
        if size is not None and s != size:
            bad("%s 素材尺寸 %s ≠ %s（应 1:1）" % (eid, s, size))
        if no_nine and "nine" in e:
            bad("%s 不应带 nine（1:1）" % eid)
        return e

    _chk_image("fc.play_win", (1448, 214, 380, 300), "ui/x_ui_playwin_bg.png", (380, 300))
    pv = _chk_image("fc.play_view", (1454, 220, 368, 288), None, None)
    if pv is not None:
        if pv.get("asset") is not None or pv.get("dynamic") != "flow_scene_frames":
            bad("fc.play_view 应为动态层 `asset:null` + `dynamic:\"flow_scene_frames\"`，实为 asset=%r dynamic=%r"
                % (pv.get("asset"), pv.get("dynamic")))
    b1 = _chk_image("fc.pbkick", (1578, 304, 119, 119), "ui/x_ui_pbkick_off.png", (119, 119))
    b2 = _chk_image("fc.pbkick_pause", (1578, 304, 119, 119),
                    "ui/x_ui_pbkick_pause_off.png", (119, 119))
    for e, want_when, tag in ((b1, "play", "播放键"), (b2, "pause", "暂停键")):
        if e is None:
            continue
        if e.get("vis_flag") != "fc_replay" or e.get("vis_when") != want_when:
            bad("fc.%s（%s）应 `vis_flag:\"fc_replay\"` / `vis_when:\"%s\"`，实为 %r/%r"
                % (e["id"], tag, want_when, e.get("vis_flag"), e.get("vis_when")))
        if e.get("visible_default") is not True:
            bad("fc.%s 的 visible_default 应为 true（靠 flag 控显隐写 false 会成死件）" % e["id"])
    if b1 is not None and b2 is not None:
        if (b1.get("x"), b1.get("y"), b1.get("w"), b1.get("h"), b1.get("z")) != \
                (b2.get("x"), b2.get("y"), b2.get("w"), b2.get("h"), b2.get("z")):
            bad("播放键与暂停键必须**同矩形同 z**（互斥对）：%s vs %s"
                % ((b1.get("x"), b1.get("y"), b1.get("w"), b1.get("h"), b1.get("z")),
                   (b2.get("x"), b2.get("y"), b2.get("w"), b2.get("h"), b2.get("z"))))
        if b1.get("vis_when") == b2.get("vis_when"):
            bad("播放/暂停键的 vis_when 相同 ⇒ 不互斥（应 play / pause）")
    hit = by.get("fc.pbkick_hit")
    if hit is None:
        bad("第 11 批：缺 `fc.pbkick_hit`（播放/暂停共用热区）")
    else:
        got = (hit.get("x"), hit.get("y"), hit.get("w"), hit.get("h"))
        ok = got == (1575, 301, 125, 125) and hit.get("action") == "flow_replay_toggle"
        print("      %-16s %s %s ｜ action=%r ⇒ %s"
              % ("fc.pbkick_hit", "", got, hit.get("action"), "✓" if ok else "✗"))
        if got != (1575, 301, 125, 125):
            bad("fc.pbkick_hit 几何 %s ≠ 第 11 批冻结 (1575, 301, 125, 125)" % (got,))
        if hit.get("action") != "flow_replay_toggle":
            bad("fc.pbkick_hit 的 action 应为 \"flow_replay_toggle\"（第 11 批定稿名），实为 %r"
                % hit.get("action"))

    # ★ 第 11 批收口（一审建议项 3）：补一条**右栏 z 序**断言 —— 原 `fc.pbk_panel` 那批判据
    #   查过「z = 底板 − 1」，本批换成新四件后**漏了 z 关系**。数据本身正确，但判据要跟上：
    #   栏底(5) < 窗底板(6) = 三槽底(6) < 画面层(7) < 两键(20) < 热区(95)。
    # ★ **第 12 批（`ISSUE-20260929-04`）**：新增满幅背景 `fc.bg` ⇒ **把它补进本链的最低位**
    #   （`fc.bg`(0) < `fc.dim`(1) < 栏底(5) …）—— 满幅底必须压在所有内容之下，
    #   否则背景会盖住节点/连线/右栏（截图上的表现是整屏被照片糊住）。
    _z = {}
    for _eid in ("fc.bg", "fc.dim", "fc.smallmap", "fc.play_win", "fc.p_title", "fc.p_text",
                 "fc.p_message", "fc.play_view", "fc.pbkick", "fc.pbkick_pause", "fc.pbkick_hit"):
        _e = by.get(_eid)
        if _e is None:
            bad("右栏 z 序断言：缺 `%s`" % _eid)
        else:
            _z[_eid] = _e.get("z")
    if len(_z) == 11:
        zok = (_z["fc.bg"] < _z["fc.dim"] < _z["fc.smallmap"]
               < _z["fc.play_win"] == _z["fc.p_title"] == _z["fc.p_text"]
               == _z["fc.p_message"] < _z["fc.play_view"] < _z["fc.pbkick"]
               == _z["fc.pbkick_pause"] < _z["fc.pbkick_hit"])
        print("      z 序（含满幅背景）：%s ⇒ %s" % (_z, "✓" if zok else "✗"))
        if not zok:
            bad("z 序应为「满幅背景 < 压暗 < 栏底 < 窗底板/三槽底 < 画面层 < 两键 < 热区」，实测 %s" % (_z,))


def check_mode_entries(scr):
    r"""★ 第 13 批（`ISSUE-20260929-05`）·【F】**模式入口与删件反向**（**覆盖只增不减**）：

      ① 六件 `fc.mode_*` 的几何/`z`/`kind`/`state_group`/`action`/`sample` 与冻结 §B 逐条一致；
      ② **每枚入口的三态素材**（`_glow` 的 `state_assets{normal,hover,pressed}`）**在库**、键齐全、
         `normal == asset`、**与元素等尺寸（1:1）且不带 `nine`**（两入口共用同一套 3 张也要逐枚核）；
      ③ 每枚 `fc.mode_*_hit` 的 `action` **非空**，且该动作名**能在 `layout/_schema.md` §六 动作表里查到**
         （「不得臆造 action 名」的机检形式）；
      ④ 两个 `_glow` 的 `state_group` **与对应 `_hit` 同组**；
      ⑤ **反向**：本批删的 18 件旧件**均不在屏数据里**（防「删了又悄悄加回」；与 `m03` ①/`m06` ① 同口径，
         这里再独立卡一道）。
    """
    print("\n【F · ★ 第 13 批 模式入口（六件 `fc.mode_*`：几何/三态/动作/配对）＋ 删件反向 18 件】")
    by = {e["id"]: e for e in scr["elements"]}
    assets_dir = os.path.join(UI, "krkr", "assets", "ui")

    # ③ 的判据来源：`_schema.md` §六 动作表正文（**从文件读**，不写死「已登记」）
    schema_txt = open(os.path.join(UI, "layout", "_schema.md"), encoding="utf-8").read()
    p6 = schema_txt.find("## 六、动作名表")
    p6_end = schema_txt.find("\n## ", p6 + 1) if p6 >= 0 else -1
    action_table = schema_txt[p6:p6_end if p6_end > 0 else len(schema_txt)] if p6 >= 0 else ""
    if p6 < 0:
        bad("`layout/_schema.md` 找不到「## 六、动作名表」⇒ 本节的 ③ 无从判定")

    n_ok = 0
    for eid, (kind, x, y, w, h, z, sg, action, sample) in sorted(MODE_SPEC.items()):
        e = by.get(eid)
        if e is None:
            bad("模式入口缺件：`%s`" % eid); continue
        got = (e.get("x"), e.get("y"), e.get("w"), e.get("h"))
        if got != (x, y, w, h):
            bad("%s 几何 %s ≠ 冻结 (%d,%d,%d,%d)" % (eid, got, x, y, w, h))
        if e.get("z") != z:
            bad("%s z=%s ≠ 冻结 %s" % (eid, e.get("z"), z))
        if e.get("kind") != kind:
            bad("%s kind=%r ≠ 冻结 %r" % (eid, e.get("kind"), kind))
        if sg is not None and e.get("state_group") != sg:
            bad("%s state_group=%r ≠ 冻结 %r" % (eid, e.get("state_group"), sg))
        if sample is not None and e.get("sample") != sample:
            bad("%s sample=%r ≠ 冻结 %r" % (eid, e.get("sample"), sample))
        if action is not None:
            act = str(e.get("action") or "")
            if act.strip() == "":
                bad("%s 的 action 为空串（本批要求非空：命中即派发）" % eid)
            elif action_table and ("`%s`" % action) not in action_table:
                bad("%s 的 action=%r **未登记**在 `layout/_schema.md` §六 动作表里" % (eid, act))
            elif act != action:
                bad("%s 的 action=%r ≠ 冻结 %r" % (eid, act, action))
        if kind == "image":
            sa = e.get("state_assets") or {}
            if sorted(sa) != ["hover", "normal", "pressed"]:
                bad("%s 的 state_assets 键不是 normal/hover/pressed：%s" % (eid, sorted(sa))); continue
            if sa.get("normal") != e.get("asset"):
                bad("%s 的 state_assets.normal=%r ≠ asset=%r" % (eid, sa.get("normal"), e.get("asset")))
            if "nine" in e:
                bad("%s 不应带 `nine`（素材与元素等尺寸 ⇒ 1:1）" % eid)
            for k in ("normal", "hover", "pressed"):
                v = sa.get(k)
                fp = os.path.join(assets_dir, os.path.basename(v or ""))
                if not os.path.exists(fp):
                    bad("%s 的 %s 三态素材缺文件：%s" % (eid, k, v))
                else:
                    sz = Image.open(fp).size
                    if sz != (w, h):
                        bad("%s 的 %s 素材 %s×%s ≠ 元素 %d×%d（应 1:1，否则 verify_ui [2] 会红）"
                            % (eid, k, sz[0], sz[1], w, h))
        n_ok += 1
    print("      六件 `fc.mode_*` 逐条核对（几何/z/kind/state_group/action/sample）⇒ 命中 **%d/6**" % n_ok)

    # ④ `_glow` ↔ `_hit` 同组配对
    for g in ("main", "frag"):
        gl, ht = by.get("fc.mode_%s_glow" % g), by.get("fc.mode_%s_hit" % g)
        if gl is None or ht is None:
            bad("模式入口 %s 缺 `_glow`/`_hit`（glow=%s hit=%s）" % (g, gl is not None, ht is not None))
            continue
        same = gl.get("state_group") == ht.get("state_group")
        tri_ok = sorted(gl.get("state_assets") or {}) == ["hover", "normal", "pressed"]
        print("      %-6s `_glow`.state_group=%r ≡ `_hit`.state_group=%r ⇒ %s ｜ 三态齐全=%s"
              % (g, gl.get("state_group"), ht.get("state_group"),
                 "✓ 同组（换态联动）" if same else "✗ **不同组**", tri_ok))
        if not same:
            bad("模式入口 %s：`_glow` 与 `_hit` 的 state_group 不同 ⇒ 不会联动换态" % g)
        if not tri_ok:
            bad("模式入口 %s：`_glow` 的 state_assets 三态不齐" % g)
        print("            三态素材（两入口共用同一套）：%s" % json.dumps(gl.get("state_assets"), ensure_ascii=False))

    # ⑤ 反向：18 件旧件均不在屏数据里
    left = [i for i in REMOVED_BATCH13 if i in by]
    print("      反向核对：本批删的 18 件旧件（`fc.mtab*` 12 ＋ `fc.fusen_*` 6）**残留在屏数据里 %d 件**%s"
          % (len(left), "（✓ 已全部退场）" if not left else " ← **违规**：%s" % left))
    if left:
        bad("本批已删的旧件仍出现在屏数据里：%s" % left)


def main():
    states = gen("states", os.path.join(OUT, "32_flowchart.states.json"))
    frag = gen("frag", os.path.join(OUT, "32_flowchart.frag.json"))
    others = {n: gen(n, os.path.join(OUT, "32_flowchart.%s.json" % n))
              for n in ("screen1", "screen2", "ref150")}
    # ★ 2026-09-30：独立层章数取自 `spine.json`（真实分组）⇒ 判据「产出 == 章数」有据可依
    _m = load_gen()
    _groups = _m.entry_groups(_m.load_spine())
    n_ch_g1 = len(_groups[0][1])
    print("=" * 78)
    print("m02 · states / frag 预设数据自证（冻结 §一 / §二）＋ 裁决 6 ＋ 第 2 批接线自证")
    print("=" * 78)
    check_states(states)
    check_frag(frag, n_ch_g1)
    mutate_frag_grid_selfcheck(frag, 1, n_ch_g1)
    # ★ 冻结 §7.2（一审后返修）：溢出行可见性契约 —— 交付样例的 G6（唯一有溢出行的组：20 格 = 12 可见 + 8 需纵滚）
    #   溢出件 = 8 格 × 3 件（image/text/hit）= **24 件**
    mutate_overflow_visible_selfcheck(others["screen1"], 6, 24)
    arts = dict(others)
    arts["states"] = states
    check_other_presets_pristine(arts)
    check_overlay_global(arts)
    check_batch2_wiring(others["screen1"])
    check_mode_entries(others["screen1"])
    print("\n" + "-" * 78)
    if FAILS:
        print("结果：**不通过**（退出码 1）—— %d 处失败" % len(FAILS))
        return 1
    print("结果：**通过**（退出码 0）—— 运行态五档 / `_dim`（image、按种类取件、与底图件同几何同 nine）/ "
          "`_read`（20×20、落在可见实体面内、与 `_new` 不共存）/ 独立层网格与文字口径 "
          "（★ 2026-09-30 纵向流水：rows=ceil(章数/3)、产出==章数、含变异自证）/ "
          "入口与返回键接线 / 独立层不产连线 / `fc.state.*` 只出现在 states 预设 / 第 2 批 8 件接线 / "
          "**第 13 批模式入口六件（含三态在库 1:1、action 入动作表、同组配对）与删件反向 18 件** 全部机检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
