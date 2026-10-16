# -*- coding: utf-8 -*-
r"""m03_shell_and_delivery_loop.py —— ★ 机检自证（`ISSUE-20260928-02` 第 3 批 + 第 5 批收口）

**要证的六件事**（逐条机检）：
  ⓪ ★ **第 9 批**：「**已读对勾**」不变量（全量 712 条**首行墨迹左缘 ≥ x_node+30**，等价「首行墨迹 ≤ 236px」；
     与 `_read` 对勾 20×20 @(x+10,y+12) 的右缘 +30 对齐）＋ `TITLE_HARD_BREAK` 12 条逐条两行 ≤230px
     ＋ 交付样例唯一受表影响的 `fc.frag6.0007_tx` 的 `sample` **逐字**等于表值
     ＋ `--preset states` 元素数 **107**（含 `_read` 3 件；★ 第 11 批 `ISSUE-20260929-02` 由 126 改：
        右栏共用静态件 −12＋3；★ **第 12 批 `ISSUE-20260929-04`：117 → 111** —— 6 件 `fc.label.<NNNN>` 底板退场；
        ★ **第 13 批 `ISSUE-20260929-05`：111 → 99** —— 删 4 个模式页签 `fc.mtab*`（12 件）与备注键 `fc.fusen_*`（6 件）、
        增两枚模式入口 `fc.mode_*`（6 件）⇒ 净 −12；★ **第 15 批 `ISSUE-20260930-02`：99 → 107** ——
        章节详情加 8 件外壳元素（加号按钮 2 ＋ 详情浮层 6））；
  ① **全部外壳件已无 `vis_flag`**（逐 id 清单 + 计数）——「外壳不参与层旗标」的机检；
     反向：图内容层件必须**全部带** `vis_flag`/`vis_when`（层归属已声明）；
     ★ **`ISSUE-20260929-02`**：该禁令新增**具名豁免集 `SHELL_FLAG_EXEMPT`**（＝播放/暂停键一对，
     状态互斥用、非层旗标）—— **豁免集过期**（集内件不再带旗标）同样判失败，防「空壳豁免」；
     并打印**原始谓词命中数**作反向自证（证明豁免是减法、判据未恒真）。
  ①b ★ **第 5 批**：6 组**组名标签底板** `fc.frag<G>_title_bg` **齐备**（6 件），且逐组
     **与各自 `fc.frag<G>_title` 同矩形、同层 `vis_when`、z 关系正确**（底板 z = 标题 z − 1），
     并**逐组复算对比度 ≥4.5:1**（WCAG 相对亮度比；墨色 `@palette.psv_ink` vs 底板核心实色），
     同时打印**基坑对照**——★ **第 12 批改口径**：`fc.bg`（满幅背景，视口区像素均值）
     ＋ `fc.dim`(#000000, opacity 60) ＋ `fc.scroll`(panel_edge, opacity 40)；
     **旧口径（`fc.dim`＋`fc.scroll` over 黑 ≈(14,17,22) ⇒ 1.19:1）随加背景而作废**；
     新口径下舞台**变亮**（≥4.5:1 ⇒「墨色画在舞台上不可读」在交付样例上已不成立），
     但**通过判据（组名底板 ≥4.5:1）与底线不变**；
     ★ **第 7 批追加更严的四条** —— ① 元素尺寸 == **素材尺寸（1:1）**；② **不带 `nine`**；
     ③ 板内「文字墨迹区（含上下外扩 2px）」**整片 alpha=255**（无渐隐带吃掉笔画）；④ 最长组名墨迹
     + 2×`FRAG_TITLE_BG_PAD` ≤ 底板宽（**余量 ≥0**）且文字在板内上下各留 ≥10px；
  ② **交付样例的进出闭环**：`screen1` 的 6 个入口热区各自的 `layer` 在屏内**都有对应元素组**
     （`vis_flag:"fc_layer"` 且 `vis_when=="frag<G>"` ⇒「进得去」），且每组都有**按组返回键**
     `fc.frag<G>_back[_tx/_hit]`（`layer=="main"` ⇒「回得来」）；
  ③ **独立层元素仍不带 `flow_state` / `_dim` / `_new`**（主代理裁决 4：独立层运行态未定义）；
  ④ **每格仍过文字四判据**（用生成器自己的 `check_text_criteria` 复算独立层每格 `sample`）。

**幂等**：只把 `screen1` 的产出落到 `_out/`（生成物，可覆盖再生），**不动屏文件**；退出码 0 = 全过。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260928-02_第2步/复现脚本/m03_shell_and_delivery_loop.py"
"""
from __future__ import annotations

import importlib.util
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
SCREEN = os.path.join(UI, "layout", "screens", "32_flowchart.json")
NODE_W, NODE_H = 296, 65
FRAG_NODE_RE = re.compile(r"^fc\.frag(\d+)\.(\d{4})$")
FRAG_BACK_RE = re.compile(r"^fc\.frag(\d+)_back(?:_tx|_hit)?$")
FRAG_TITLEBG_RE = re.compile(r"^fc\.frag(\d+)_title_bg$")

# ── WCAG 2.x 相对亮度比（★ 第 5 批：组名底托的验收口径）─────────────────────
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    r, g, b = (_lin(float(x)) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _plate_core_rgb(png):
    """底板核心实色：取图中央 50% 区域里 **alpha≥250** 像素的众数（避开边缘柔光）。"""
    from collections import Counter
    im = Image.open(png).convert("RGBA")
    w, h = im.size
    c = im.crop((int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75)))
    px = [p for p in c.getdata() if p[3] >= 250]
    if not px:
        px = list(c.getdata())
    return Counter(px).most_common(1)[0][0][:3]


FAILS = []


def bad(msg):
    FAILS.append(msg)
    print("      ✗ %s" % msg)


def load_gen():
    spec = importlib.util.spec_from_file_location("_gfl_m03", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    gen = load_gen()
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "32_flowchart.screen1.json")
    r = subprocess.run([sys.executable, GEN, "--preset", "screen1", "--out", out],
                       cwd=UI, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[FAIL] 生成 screen1 失败（rc=%d）：%s" % (r.returncode, r.stderr[-400:]))
    scr = json.load(open(out, encoding="utf-8"))
    els = scr["elements"]
    by = {e["id"]: e for e in els}
    OWNED = gen.LAYER_OWNED_PREFIXES
    # ★ `ISSUE-20260929-02`：外壳件层旗标禁令的**具名豁免集**（**状态互斥对**，非层旗标）。
    #   播放键 `fc.pbkick` / 暂停键 `fc.pbkick_pause`：同矩形同 z、靠屏级 `fc_replay` 的
    #   `"play"`/`"pause"` 互斥显示。`fc_replay` 不参与 `fc_layer` 切层、初值在任何层皆成立
    #   ⇒ 不触发本禁令要防的「切层丢外壳」风险。生成器侧同名常量 `STATIC_FLAG_EXEMPT` 同步收紧。
    #   集内件若不再带旗标 ⇒ 判「豁免集过期」（见 ①），防留下空壳豁免。
    SHELL_FLAG_EXEMPT = set(getattr(gen, "STATIC_FLAG_EXEMPT", ())) or {
        "fc.pbkick", "fc.pbkick_pause"}
    flags = scr.get("flags_default") or {}
    print("=" * 78)
    print("m03 · 第 3 批四条机检自证（外壳不参与层旗标 / 交付样例进出闭环 /")
    print("      独立层不带运行态叠加件 / 每格过文字四判据）")
    print("  屏 = screen1（%d 元素）｜ 屏级 flags_default = %s" % (len(els), flags))
    print("=" * 78)

    # ── ⓪ ★ 第 9 批：「已读对勾」不变量 + `TITLE_HARD_BREAK` 硬断行表 ──────────
    print("\n【⓪ 第 9 批·「已读对勾」不变量（首行墨迹左缘 ≥ x_node+%d）＋ 硬断行表】" % gen.TITLE_CHECK_GAP)
    _viol, (_min_left, _min_id, _n, _n2, _maxink) = gen.check_title_first_line(gen.load_data()["nodes"])
    print("      复算全量 %d 条：违规 **%d 条** ｜ 最紧 首行左缘 %+.2f（%s）｜ 两行条数 %d ｜ 全量最宽行 %.1fpx"
          % (_n, len(_viol), _min_left, _min_id, _n2, _maxink))
    if _viol:
        for nid, t, w0, left, ln in _viol:
            print("        ✗ %-10s 首行 %.1fpx 左缘 %+.2f（%d 行）｜「%s」" % (nid, w0, left, ln, t))
        bad("「已读对勾」不变量违规 %d 条（对勾右缘 +%d 会压首字）" % (len(_viol), gen.TITLE_CHECK_GAP))
    else:
        print("      ✓ 不变量全绿（%d 条全部 ≥ +%d；等价「首行墨迹 ≤ %dpx」）"
              % (_n, gen.TITLE_CHECK_GAP, gen.TEXT_W - 2 * (gen.TITLE_CHECK_GAP - (gen.NODE_W - gen.TEXT_W) // 2)))
    print("      硬断行表 %d 条（目标两行 ≤ %dpx）：" % (len(gen.TITLE_HARD_BREAK), gen.TITLE_BREAK_MAX_LINE))
    _wof2, _ = gen.width_fn(gen.TEXT_SIZE)
    for _nid, _parts in gen.TITLE_HARD_BREAK.items():
        _w = [_wof2(p) for p in _parts]
        _ok = all(w <= gen.TITLE_BREAK_MAX_LINE for w in _w)
        print("        %-9s 「%s」%.0f ＋ 「%s」%.0f ⇒ %s"
              % (_nid, _parts[0], _w[0], _parts[1], _w[1], "✓" if _ok else "✗ 超 %d" % gen.TITLE_BREAK_MAX_LINE))
        if not _ok:
            bad("%s 断行后仍有行 > %dpx" % (_nid, gen.TITLE_BREAK_MAX_LINE))
    # 第 9 批那条的逐字核对（`fc.frag6.0007_tx` ← `62_1b`）；第 10 批起交付样例另有 2 件，
    # 由下面「由表推导」的整节统一核对（此处只保留对首条的定点核对）
    _tx = by.get("fc.frag6.0007_tx")
    _want = "\n".join(gen.TITLE_HARD_BREAK["62_1b"])
    print("      定点核对：`fc.frag6.0007_tx`（62_1b）的 `sample` = %r ⇒ %s"
          % (_tx.get("sample") if _tx else None, "✓ 与表一致" if _tx and _tx.get("sample") == _want else "✗ 与表不符"))
    if not (_tx and _tx.get("sample") == _want):
        bad("fc.frag6.0007_tx.sample 与 TITLE_HARD_BREAK 不一致（期望 %r）" % _want)
    # ★ 第 10 批：把「交付样例里受表影响的文字件」改为**由表推导**（原先硬编码「应为 1 个」，
    #   表一扩容就误报）。判据＝屏内每个带 `\n` 的文字件，其 `sample` 必须**逐字等于**表内某条的拼接。
    _want_map = {"\n".join(v): k for k, v in gen.TITLE_HARD_BREAK.items()}
    _broken = {e["id"]: e.get("sample") for e in els
               if e.get("kind") == "text" and "\n" in (e.get("sample") or "")}
    _undeclared = {i: s for i, s in _broken.items() if s not in _want_map}
    print("      screen1 内带硬断行的文字件：**%d 个**（＝表内 %d 条中落在交付样例里的那些；由表推导，不再硬编码）"
          % (len(_broken), len(gen.TITLE_HARD_BREAK)))
    for _i, _s in sorted(_broken.items()):
        print("        %-20s ← 表内 `%s`：%r" % (_i, _want_map.get(_s, "**未登记**"), _s))
    if _undeclared:
        bad("交付样例里有**表外**硬断行文字件：%s" % sorted(_undeclared))
    _hit_ids = sorted(_want_map[_s] for _s in _broken.values() if _s in _want_map)
    print("        命中表内 id：%s ｜ 其余 %d 条不在交付样例四档（如无此断行则其首行左缘 < +34）"
          % (_hit_ids, len(gen.TITLE_HARD_BREAK) - len(_hit_ids)))
    # states 档元素数（第 11 批 `ISSUE-20260929-02`：126 → **117**，因右栏共用静态件 −12＋3；
    #   ★ 第 12 批 `ISSUE-20260929-04`：117 → **111**，因 6 件 `fc.label.<NNNN>` 底板退场；
    #   ★ 第 13 批 `ISSUE-20260929-05`：111 → **99**，因删 12 件 `fc.mtab*` ＋ 6 件 `fc.fusen_*`、增 6 件 `fc.mode_*`）
    #   ★ 第 15 批 `ISSUE-20260930-02`：99 → **107**，因章节详情加 8 件外壳元素（加号按钮 2 ＋ 详情浮层 6））
    #   ★ 第 15 批·第 2 轮（用户裁定 5）：107 → **109**，浮层再增关闭件 2 件
    #     （`fc.intro_close` / `fc.intro_close_hit`））
    _st = os.path.join(OUT, "32_flowchart.states.json")
    _r2 = subprocess.run([sys.executable, GEN, "--preset", "states", "--out", _st],
                         cwd=UI, capture_output=True, text=True)
    if _r2.returncode != 0:
        bad("生成 states 失败：%s" % _r2.stderr[-200:])
    else:
        _se = json.load(open(_st, encoding="utf-8"))["elements"]
        _reads = [e["id"] for e in _se if e["id"].endswith("_read")]
        print("      `--preset states` 元素数 **%d**（含 `_read` %d 件）⇒ %s"
              % (len(_se), len(_reads), "✓（109、3 件）" if len(_se) == 109 and len(_reads) == 3 else "✗ 与预期不符"))
        if len(_se) != 109 or len(_reads) != 3:
            bad("states 元素数/`_read` 件数与预期（109 / 3）不符：%d / %d" % (len(_se), len(_reads)))

    # ── ① 外壳件无层旗标（逐 id 清单 + 计数）+ 图内容层全带旗标 ──────────────
    print("\n【① 外壳件不参与层旗标（逐 id 清单 + 计数）】")
    shell = [e["id"] for e in els if not e["id"].startswith(OWNED)]
    # ★ `ISSUE-20260929-02`：先取**原始谓词**命中集（不豁免），再减具名豁免集
    #   （`fc.pbkick`/`fc.pbkick_pause` 一对：同矩形同 z、靠屏级 `fc_replay` 的 play/pause 互斥 ——
    #    非层旗标，初值 "play" 在任何层皆成立 ⇒ 不触发本禁令要防的「切层丢外壳」风险）。
    #   豁免集**过期**（集内件不再带旗标）判失败，防「空壳豁免」；集外仍严格拒绝。
    shell_flagged_raw = sorted(i for i in shell if "vis_flag" in by[i] or "vis_when" in by[i])
    shell_bad = [i for i in shell_flagged_raw if i not in SHELL_FLAG_EXEMPT]
    shell_exempt_hit = sorted(i for i in shell_flagged_raw if i in SHELL_FLAG_EXEMPT)
    content = [e["id"] for e in els if e["id"].startswith(OWNED)]
    content_bad = [i for i in content if "vis_flag" not in by[i] or "vis_when" not in by[i]]
    print("      外壳件 **%d 件**，带 vis_flag/vis_when：原始谓词 **%d 件** ⇒ 减豁免集后 **%d 件违规**%s"
          % (len(shell), len(shell_flagged_raw), len(shell_bad), "（✓）" if not shell_bad else " ← 违规"))
    if shell_flagged_raw:
        print("        原始命中：%s" % "、".join(shell_flagged_raw))
    print("        具名豁免集 `%s` 命中 **%d 件**：%s"
          % ("/".join(sorted(SHELL_FLAG_EXEMPT)), len(shell_exempt_hit),
             "、".join(shell_exempt_hit) if shell_exempt_hit else "（无）"))
    if shell_exempt_hit:
        # ★ 第 11 批收口（一审阻断项）：原为**无条件打印**（看起来在自证、实际恒真）⇒ 改真断言：
        #   「原始谓词命中集 == 豁免集」才成立；多/少一件都失败（多＝集外被放行，少＝空壳豁免）。
        if set(shell_flagged_raw) != set(SHELL_FLAG_EXEMPT):
            bad("反向自证失败：原始谓词命中 %s ≠ 豁免集 %s ⇒ 有集外件被放行 / 集内件漏判"
                % (shell_flagged_raw, sorted(SHELL_FLAG_EXEMPT)))
        else:
            print("        反向自证：原始谓词命中 == 豁免集（%d 件）⇒ 豁免是**减法**、集外零放行 ✓"
                  % len(shell_flagged_raw))
    stale_exempt = sorted(i for i in SHELL_FLAG_EXEMPT if i not in shell_flagged_raw)
    if stale_exempt:
        bad("豁免集过期：`SHELL_FLAG_EXEMPT` 声明豁免 %s，但它并未带 vis_flag/vis_when（或元素已不存在）"
            "⇒ 删除该条，否则豁免变成空壳" % stale_exempt)
    print("      逐 id 清单（%d 件）：" % len(shell))
    _line = "        "
    for i in sorted(shell):
        if len(_line) + len(i) + 2 > 108:
            print(_line)
            _line = "        "
        _line += i + "、"
    if _line.strip():
        print(_line.rstrip("、"))
    if shell_bad:
        bad("外壳件带层旗标：%s" % shell_bad)
    print("      图内容层 **%d 件**（前缀 %s），缺旗标：**%d 件**%s"
          % (len(content), "/".join(x.rstrip(".") for x in OWNED), len(content_bad),
             "（✓）" if not content_bad else " ← 违规"))
    if content_bad:
        bad("图内容层件缺 flags：%s" % content_bad)
    print("      ⇒ 合计 %d + %d = %d（应等于元素总数 %d）%s"
          % (len(shell), len(content), len(shell) + len(content),
             len(els), "✓" if len(shell) + len(content) == len(els) else "✗"))
    if len(shell) + len(content) != len(els):
        bad("外壳件 + 图内容层件 ≠ 元素总数（分类有漏）")

    # ── ①b ★ 第 5 批：独立层组名「标签底板」齐备 + z/同层关系 + 逐组对比度 ────
    print("\n【①b 第 5 批·组名底托（6 组齐备 / z 关系 / 同层 vis_when / 对比度 ≥4.5:1）】")
    import json as _json
    pal = _json.load(open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]
    ink_hex = pal["psv_ink"]["value"].lstrip("#")
    ink = tuple(int(ink_hex[i:i + 2], 16) for i in (0, 2, 4))
    # 基坑（回归对照）：★ 第 12 批起舞台底色**不再是黑** —— 改为
    #   `fc.bg`（满幅背景素材，第 12 批新增）→ `fc.dim`(#000000, opacity 60) → `fc.scroll`(panel_edge, opacity 40)。
    #   背景是**照片**（无单色值）⇒ 代表色取「**fc.scroll 视口矩形内**的背景像素均值」（组名底板就落在该视口内）。
    dim = by.get("fc.dim") or {}
    scr_el = by.get("fc.scroll") or {}
    bg_el = by.get("fc.bg") or {}

    def _resolve_color(v, palette_map):
        """屏 JSON 里色值是 `@palette.<key>` 引用（未解析）或 `#RRGGBB` 或 0xAARRGGBB 整数。"""
        if isinstance(v, str) and v.startswith("@palette."):
            c = palette_map.get(v.split(".", 1)[1], {}).get("value")
            v = c if c else v
        if isinstance(v, str) and v.startswith("#") and len(v) == 7:
            return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
        if isinstance(v, int):
            return ((v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF)
        return None

    a_sc = (scr_el.get("opacity", 0) or 0) / 255.0
    sc_rgb = _resolve_color(scr_el.get("color"), pal)
    dim_rgb = _resolve_color(dim.get("color"), pal) or (0, 0, 0)
    dim_a = (dim.get("opacity", 0) or 0) / 255.0
    # ★ 第 12 批：`fc.bg` 必须是**最底层**（z0）且在 `fc.dim` 之下，本口径才成立
    if not bg_el:
        bad("基坑口径要求 `fc.bg`（满幅背景）存在（第 12 批新增）—— 屏内没有该元素")
        base_rgb = (0, 0, 0)
    else:
        if (bg_el.get("z"), dim.get("z")) != (0, 1):
            bad("基坑口径：应 z(fc.bg)=0 < z(fc.dim)=1，实测 %s / %s"
                % (bg_el.get("z"), dim.get("z")))
        # 代表色 = fc.scroll 视口矩形内的背景像素均值（照片 ⇒ 用均值作舞台色，非单色）
        _assets_dir = os.path.join(UI, "krkr", "assets", "ui")
        _bgsrc = os.path.join(_assets_dir, os.path.basename(bg_el.get("asset") or ""))
        try:
            _im = Image.open(_bgsrc).convert("RGB")
            _box = (int(scr_el.get("x", 0)), int(scr_el.get("y", 0)),
                    int(scr_el.get("x", 0)) + int(scr_el.get("w", 0)),
                    int(scr_el.get("y", 0)) + int(scr_el.get("h", 0)))
            _crop = _im.crop(_box)
            # BOX 重采样到 1×1 ＝ 该区**精确均值**（避开 `getdata()` 的 Pillow 弃用告警）
            base_rgb = tuple(float(v) for v in _crop.resize((1, 1), Image.BOX).getpixel((0, 0)))
            print("      基坑底座 `fc.bg`（%s，z=%s）＝ 视口区 %s 内像素均值 RGB %s（相片底 ⇒ 取均值）"
                  % (bg_el.get("asset").split("/")[-1], bg_el.get("z"), _box,
                     tuple(round(x, 1) for x in base_rgb)))
        except Exception as _e:
            bad("基坑口径读 `fc.bg` 素材失败：%s" % _e)
            base_rgb = (0, 0, 0)
    # 叠序：fc.bg(z0) ← fc.dim(z1) ← fc.scroll(z5)
    under = tuple(base_rgb[i] * (1 - dim_a) + dim_rgb[i] * dim_a for i in range(3))
    stage = tuple(under[i] * (1 - a_sc) + (sc_rgb or (0, 0, 0))[i] * a_sc for i in range(3))
    print("      墨色 = `@palette.psv_ink` %s ｜ 回归对照·**基坑**（fc.bg 均值 ＋ fc.dim%s ＋ fc.scroll%s）= %s"
          % (pal["psv_ink"]["value"], (dim.get("color"), dim.get("opacity")),
             (scr_el.get("color"), scr_el.get("opacity")), tuple(round(x) for x in stage)))
    print("      （基坑口径对墨色对比度 = **%.3f:1** —— ★ 第 12 批加背景后舞台**变亮**："
          "旧口径（fc.dim ＋ fc.scroll over **黑**）为 ≈(14,17,22)、**1.19:1**（不可读的根因，本批已作废）；"
          "现口径 ≥4.5:1 ⇒ 「组名墨色画在舞台上不可读」这条**在交付样例上已不成立**，"
          "但 6 组底托**保留不改**、通过判据（逐组 ≥4.5:1）**不变**）"
          % contrast(ink, stage))
    assets_dir = os.path.join(UI, "krkr", "assets", "ui")
    ok_bg = True
    # ★ 第 7 批：底托换**专用硬边件** ⇒ 追加两条机检（1:1 无 nine ＋ 板内不透明核心覆盖整张）
    bg_sizes = set()
    ink_w = 0.0
    _wof, _wof_src = gen.width_fn(gen.FRAG_TITLE_SIZE)
    for g in range(1, 7):
        bg = by.get("fc.frag%d_title_bg" % g)
        tx = by.get("fc.frag%d_title" % g)
        lyr = "frag%d" % g
        if bg is None or tx is None:
            bad("第 %d 组缺底托/标题件（bg=%s tx=%s）" % (g, bg is not None, tx is not None))
            ok_bg = False
            continue
        same_rect = all(bg.get(k) == tx.get(k) for k in ("x", "y", "w", "h"))
        zok = (bg.get("z") == tx.get("z", 25) - 1)
        visok = (bg.get("vis_flag") == "fc_layer" and bg.get("vis_when") == lyr
                 and tx.get("vis_when") == lyr)
        png = os.path.join(assets_dir, os.path.basename(bg.get("asset") or ""))
        if not os.path.exists(png):
            bad("第 %d 组底托素材缺文件：%s" % (g, bg.get("asset")))
            ok_bg = False
            continue
        # ★ 第 7 批①②：素材尺寸 == 元素尺寸（1:1）且**不带 nine**
        from PIL import Image as _Im
        asz = _Im.open(png).size
        one2one = (asz == (bg.get("w"), bg.get("h")))
        no_nine = ("nine" not in bg)
        # ★ 第 7 批③：板内「文字墨迹区」必须整片 alpha=255（硬边无渐隐带吃掉笔画）
        _im = _Im.open(png).convert("RGBA")
        _px = _im.load()
        vpad = (bg.get("h") - gen.FRAG_TITLE_SIZE) // 2          # 行盒顶（局部）
        bad_px = [(x, y) for y in range(max(0, vpad - 2), min(bg.get("h"), vpad + gen.FRAG_TITLE_SIZE + 2))
                  for x in range(bg.get("w")) if _px[x, y][3] != 255]
        # ★ 第 7 批④：最长组名墨迹 + 2×PAD ≤ 底板宽（与生成器同尺同判据）
        ink_w = max(ink_w, _wof(str(tx.get("sample") or "")))
        core = _plate_core_rgb(png)
        cr = contrast(ink, core)
        cr_ok = cr >= 4.5
        bg_sizes.add((bg.get("w"), bg.get("h"), asz, one2one, no_nine))
        print("      G%d `%s` 元素 %s ／素材 %s ⇒ 1:1=%s、无 nine=%s ｜ 与 title **同矩形**=%s ｜ "
              "z %s＝title %s−1 =%s ｜ 同层 vis_when=%s ｜ 板内墨迹区非全不透明像素 **%d** ｜ "
              "底板核心 %s ⇒ 对比度 **%.2f:1** %s"
              % (g, bg.get("asset").split("/")[-1],
                 "%dx%d@(%d,%d)" % (bg["w"], bg["h"], bg["x"], bg["y"]), "%dx%d" % asz,
                 one2one, no_nine, same_rect, bg.get("z"), tx.get("z"), zok, visok, len(bad_px),
                 core, cr, "✓" if cr_ok else "✗ <4.5"))
        for cond, msg in ((same_rect, "与标题不同矩形（fc.label 惯例：同矩形）"),
                          (zok, "z=%s 应 = 标题 z−1" % bg.get("z")),
                          (visok, "底托/标题不同层 vis_when（应同为 %s）" % lyr),
                          (cr_ok, "组名对比度 %.2f:1 < 4.5:1（底托没起作用）" % cr),
                          (one2one, "元素 %s ≠ 素材 %s ⇒ 非 1:1" % ((bg.get("w"), bg.get("h")), asz)),
                          (no_nine, "1:1 件不应带 `nine`"),
                          (not bad_px, "板内墨迹区有 %d 个非全不透明像素（渐隐带会吃掉笔画）" % len(bad_px))):
            if not cond:
                bad("第 %d 组底托：%s" % (g, msg))
                ok_bg = False
    # 底托宽度自检（与生成器同一判据）+ 纵向上下留白 ≥10px
    slack = gen.FRAG_TITLE_BG_W - ink_w - 2 * gen.FRAG_TITLE_BG_PAD
    vpad_ok = (gen.FRAG_TITLE_BG_H - gen.FRAG_TITLE_SIZE) // 2 >= 10
    print("      底托尺寸集（w,h,素材w,h,1:1,无nine）：%s" % sorted(bg_sizes))
    print("      宽度自检：最长组名墨迹 %.1fpx + 2×%d = %.1f ≤ %d ⇒ **余量 %.1fpx**（两侧实边距各 %.1fpx）%s ｜ "
          "纵向：文字在 %d 高板内上下各留 %dpx（要求 ≥10）%s"
          % (ink_w, gen.FRAG_TITLE_BG_PAD, ink_w + 2 * gen.FRAG_TITLE_BG_PAD, gen.FRAG_TITLE_BG_W,
             slack, (gen.FRAG_TITLE_BG_W - ink_w) / 2.0, "✓" if slack >= 0 else "✗",
             gen.FRAG_TITLE_BG_H, (gen.FRAG_TITLE_BG_H - gen.FRAG_TITLE_SIZE) // 2,
             "✓" if vpad_ok else "✗"))
    if slack < 0:
        bad("最长组名墨迹超出底托（余量 %.1fpx）" % slack)
        ok_bg = False
    if not vpad_ok:
        bad("文字在板内上下留白 <10px")
        ok_bg = False
    if len(bg_sizes) != 1:
        bad("6 组底托尺寸/口径不一致：%s" % sorted(bg_sizes))
        ok_bg = False
    print("      ⇒ 6 组底托齐备且口径正确：%s（底托总数 %d 件）"
          % ("✓" if ok_bg else "✗",
             sum(1 for e in els if FRAG_TITLEBG_RE.match(e["id"]))))
    if sum(1 for e in els if FRAG_TITLEBG_RE.match(e["id"])) != 6:
        bad("底托件数 ≠ 6")

    # ── ② 交付样例：6 个入口热区 × 对应独立层 × 按组返回键（进出闭环）────────
    print("\n【② 交付样例进出闭环（入口 → 独立层 → 按组返回键 → 主干）】")
    if flags.get("fc_layer") != "main":
        bad("屏级 flags_default 缺 {\"fc_layer\":\"main\"}：%s" % flags)
    ents = [e for e in els if e["id"].startswith("fc.entry.") and e["id"].endswith("_hit")]
    layers = sorted({e["vis_when"] for e in els
                     if e.get("vis_flag") == "fc_layer" and str(e.get("vis_when", "")).startswith("frag")})
    print("      入口热区 %d 个 ｜ 屏内独立层取值 %d 个：%s" % (len(ents), len(layers), layers))
    if len(ents) != 6:
        bad("交付样例应有 6 个入口热区，实为 %d" % len(ents))
    if layers != ["frag%d" % g for g in range(1, 7)]:
        bad("交付样例应产全部 6 组独立层，实为 %s" % layers)
    ok_all = True
    for e in sorted(ents, key=lambda x: x["id"]):
        g = str(e.get("layer", ""))
        grp = re.match(r"^frag(\d+)$", g)
        if g not in layers:
            bad("%s 的 layer=%r 在屏内**无对应独立层**（进不去/进去了是空屏）" % (e["id"], g))
            ok_all = False
            continue
        cells = [x["id"] for x in els if FRAG_NODE_RE.match(x["id"]) and FRAG_NODE_RE.match(x["id"]).group(1) == grp.group(1)]
        trio = ["fc.%s_back" % g, "fc.%s_back_tx" % g, "fc.%s_back_hit" % g]
        miss = [t for t in trio if t not in by]
        back_ok = (by.get(trio[2], {}).get("action") == "flow_layer"
                   and by.get(trio[2], {}).get("layer") == "main"
                   and by.get(trio[0], {}).get("vis_when") == g
                   and by.get(trio[1], {}).get("vis_when") == g
                   and by.get(trio[2], {}).get("vis_when") == g)
        print("      %s → layer=%-6s ｜ 该层节点 %2d 格 ｜ 按组返回键 %s ｜ 返回键 layer/action=%s/%s ⇒ %s"
              % (e["id"], g, len(cells), "齐 ✓" if not miss else "缺 %s ✗" % miss,
                 by.get(trio[2], {}).get("layer"), by.get(trio[2], {}).get("action"),
                 "✓" if (not miss and back_ok and cells) else "✗"))
        if miss:
            bad("%s 有入口但缺返回键件：%s（进得去回不来）" % (g, miss))
        elif not back_ok:
            bad("%s 的按组返回键接线/同组 vis_when 不符（layer=main / action=flow_layer / vis_when=%s）" % (g, g))
        if not cells:
            bad("独立层 %s 无节点（点进去是空屏）" % g)
        ok_all = ok_all and (not miss) and back_ok and bool(cells)
    # 反向：每个已产独立层都必须有入口（去得了）
    for lyr in layers:
        if not any(e.get("layer") == lyr for e in ents):
            bad("独立层 %s 已产出但无入口热区（去不了）" % lyr)
            ok_all = False
    print("      ⇒ 6 组各自「进得去 + 回得来」：%s" % ("✓" if ok_all else "✗"))

    # ── ③ 独立层元素不带 flow_state / _dim / _new（裁决 4）────────────────
    print("\n【③ 独立层元素不带 `flow_state` / `_dim` / `_new`（裁决 4：独立层运行态未定义）】")
    frag_els = [e for e in els if e["id"].startswith("fc.frag")
                and (FRAG_NODE_RE.match(e["id"]) or FRAG_BACK_RE.match(e["id"])
                     or FRAG_TITLEBG_RE.match(e["id"]) or e["id"].endswith("_title"))]
    with_fs = [e["id"] for e in frag_els if "flow_state" in e]
    dims = [e["id"] for e in frag_els if e["id"].endswith("_dim")]
    news = [e["id"] for e in frag_els if e["id"].endswith("_new")]
    print("      独立层元素 %d 件 ｜ 带 flow_state **%d 件** ｜ `_dim` **%d 件** ｜ `_new` **%d 件**"
          % (len(frag_els), len(with_fs), len(dims), len(news)))
    if with_fs or dims or news:
        bad("独立层不得带运行态字段：flow_state=%s / _dim=%s / _new=%s" % (with_fs, dims, news))
    else:
        print("      ✓ 三者皆 0（与主干节点的 fc.state.* 机制互不干扰）")

    # ── ④ 每格仍过文字四判据（复用生成器自己的复算）───────────────────────
    print("\n【④ 独立层每格过文字四判据（复用 `gen.check_text_criteria` 逐格复算）】")
    synth = {}
    for e in els:
        m_ = FRAG_NODE_RE.match(e["id"])
        if m_ is None:
            continue
        tx = by.get(e["id"] + "_tx")
        if tx is None:
            bad("%s 缺 `_tx`" % e["id"])
            continue
        synth[e["id"]] = {"cn": tx.get("sample") or ""}
        if (tx.get("font", {}).get("size") != 19 or tx.get("line_spacing") != 1.0
                or tx.get("w") != 240 or tx.get("max_lines") != 2):
            bad("%s 的文字口径 ≠ 19px/行距 1.0/盒宽 240/max_lines 2" % e["id"])
    tc = gen.check_text_criteria(synth)
    print("      逐格复算 %d 格（参数 f=%d / 行距 %s / 盒宽 %d / max_lines %d / plate rows %d..%d）："
          % (len(synth), tc["size"], tc["spacing"], tc["box_w"], gen.TEXT_MAX_LINES,
             tc["plate"][0], tc["plate"][1]))
    print("        上留最小 %dpx ｜ 下留最小 %dpx ｜ 最宽行 %.1fpx（%s）｜ 截断 %d ｜ 两行格 %d"
          % (tc["min_top"], tc["min_bottom"], tc["max_ink"], tc["widest"][0], tc["trunc"], tc["n_two"]))
    if tc["fails"]:
        for x in tc["fails"]:
            bad("独立层文字判据：" + x)
    else:
        print("        ✓ 四判据全绿（A/B ≥%dpx、C ≤263px、D 零截断）" % gen.PLATE_MARGIN_MIN)

    print("\n" + "-" * 78)
    if FAILS:
        print("结果：**不通过**（退出码 1）—— %d 处" % len(FAILS))
        return 1
    print("结果：**通过**（退出码 0）—— 外壳件 %d 件零层旗标、图内容层 %d 件全带旗标；"
          "6 组组名底托齐备且对比度 ≥4.5:1；6 组独立层「进得去 + 回得来」；"
          "独立层无运行态字段；%d 格文字四判据全绿"
          % (len(shell), len(content), len(synth)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
