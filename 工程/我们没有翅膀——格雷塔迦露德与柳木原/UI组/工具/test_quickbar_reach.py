# -*- coding: utf-8 -*-
r"""quickbar 屏**端到端可达性守门**（数据层复算，不起引擎）

■ 历史（为什么有它）
  M1 阻断项（ISSUE-20260922-28 坑 17）：`quick.hit_toggle`（x1842 y7 w78 h898，z=96）的矩形
  **完整包住** 12 个项热区（x1845 w75 h73，z=95）。命中取「最高 z」，故两态都可见时展开态点竖条
  任何位置都只派发把手动作 ⇒ **12 项全部不可达**（而自检全绿、截图正常、日志无异常）。

■ ★ M37（ISSUE-20260923-01）形态重构后，本守门守什么
  用户裁定「整条带太丑」⇒ 整条把手 `quick.hit_toggle` / 收起 slim 把手 `quick.tgl` /
  展开整条 `quick.btn` / 高面板 `quick.tips` **全部退场**，改为「一排独立圆形 icon 徽章 +
  悬停时左侧浮出中文名称药丸」，且**平时完全隐藏**（收起态不画任何东西）。
  ⇒ 断言随之改为（仍是**目标导向**，不是「两端一致」）：
    ① **收起态**：整条区域（12 个项热区的并集矩形）逐点扫描 **全部无命中** ——
       右端没有可点热区（点空＝落到承载屏的剧情推进），且**旧把手不得复活**；
    ② **展开态**：12 个项热区各自的几何中心胜出者 = **该项自身**，且 `action` 与数据一致；
       同时**新结构齐备**：12 个圆形 icon（image，带 `state_assets{normal,hover}`）可见、
       12 对「药丸 image + 白字 text」按 key 齐全、icon 的 `state_group` 与同 key 热区一致、
       icon 圆心与热区中心偏差 ≤ 1px（**坐标由数据推出的等价性，不是抄常量**）；
       ★ **icon 画布尺寸以磁盘 PNG 实测为准**（`icon_png_size()`）——L1 把画布由 56 改 64 时，
       本脚本**不需要跟着改数字**；药丸间距取 `PILL_GAP`（= 生成器 `QUICK_GAP`，另带区间断言）；
    ③ **展开 + 气泡 + 钉住**：与 ② 同（防止 `qbar_tip`/`qbar_pin` flag 影响命中）。

■ 复算口径（**与 `krkr/game/ui_screens.tjs` 的 `uiScreenClick` 逐字一致**，:1288-1301）
  在屏内可见元素中，取 `kind ∈ {hit, list}` 且「元素矩形包含该点」者里 **z 最高**的一个
  （`if(z < bestZ) continue;` ⇒ z 相等时**声明更晚者胜**）；可见性走 `uiScreenElementVisible`
  （`visible_default !== false` 且 `vis_flag` 缺省或 `vis_when` 匹配；`"*"` = 非空）。
  ⚠️ 这是**点击/派发层**的解析。**悬停层**（`uiScreenHoverAt`，候选并集 = 带态图的任何元素 ∪
     带非空组的 hit）另由 `工具\test_state_targets.py` 守 —— 两者口径不同，**不能互相替代**
     （M37 起 12 个 icon + 12 个热区都进**悬停层**候选，由那条守门覆盖）。
  ⚠️ 本脚本**只复算数据**：不起引擎、不看渲染。引擎内的实际派发由巡演/探针验证。

■ 用法
  python 工具/test_quickbar_reach.py      # 退出码 0 = 通过

■ 反向自证（不必改磁盘，脚本内置 `--selfcheck`，两项都必须 FAIL）
  · A：往第 1 项注入一件 **z=999 的异组热区**（恰好盖住它的中心）⇒ ② 必须 FAIL
       （证明「中心胜出者=自身」真的可证伪，而不是恒真）。
  · B：抹掉 12 个项热区的 `vis_flag/vis_when`（= **收起态也可见**，展开/收起互斥被破坏）
       ⇒ ① 必须 FAIL（证明「收起态右端无任何命中」真的在验东西）。

★ 复算口径单一来源：`flag_visible` / `click_winner` / `scan_counts` 一律从
  `工具\test_click_reach.py`（全屏守门，屏数按数据实测）引入 —— 两处各写一套判据会在改口径时分叉。
"""
import os
import io
import json
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCREEN = os.path.join(UI, "layout", "screens", "35_quickbar.json")

sys.path.insert(0, HERE)      # 同一目录，直接复用全屏守门的复算口径
from test_click_reach import flag_visible, click_winner, scan_counts  # noqa: E402

ITEMS = ["lock", "save", "load", "qsave", "qload", "auto", "skip",
         "next", "prev", "log", "chart", "option"]
OLD_HANDLE = "quick.hit_toggle"     # ★ M37 已退场；仍在数据里出现即视为「旧结构复活」


def scan(els, rect, flags, step=1):
    """对 rect 内 pixel 逐点复算，返回 胜者id → 点数（含 "(无)"）。"""
    return scan_counts(els, [rect[0], rect[1], rect[2], rect[3]], flags, step,
                       lambda w: w["id"] if w else "(无)")


def by_id(els):
    return {e.get("id"): e for e in els}


# ══════════════════════════════════════════════════════════════════════
# 尺寸 / 公式的**唯一来源**（★ L1 去写死；★ P1 起宽度公式也来自生成器）
#   · icon 画布尺寸 = **PNG 实测尺寸**（PIL 读盘）——G1 交付契约是「常态/悬停两态同尺寸」，
#     由素材决定；写死 56/64 会在换规格时静默失守（L1 正是 56→64 的一次改动）。
#   · 药丸的**宽度公式与全部几何常量一律从屏生成器 import**（`m34_build_screens`）——
#     本脚本**不复制公式**（P1 要求「公式写在生成器里，不要硬编码到校验脚本」）。
#   · 「丸体右缘 ↔ icon 左缘」的间距是版式选择，数据侧无法反推 ⇒ 取生成器的 `QUICK_GAP`，
#     另加一条合理区间断言（0 < gap ≤ 16）兜住手改数据时的粗错。
# ══════════════════════════════════════════════════════════════════════
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
sys.path.insert(0, HERE)
import m34_build_screens as gen          # noqa: E402  （生成器 = 公式与常量的唯一出处）

PILL_GAP = gen.QUICK_GAP                  # 丸体右缘 ↔ icon 左缘


def icon_png_size(key="lock"):
    """从磁盘**实测**常态 icon 的像素尺寸（不依赖 PIL 之外的任何常量）。"""
    from PIL import Image
    p = os.path.join(ASSETS, "x_ui_qbicon_%s.png" % key)
    if not os.path.exists(p):
        return None
    with Image.open(p) as im:
        return im.size


def pill_png_report():
    """药丸素材实测：PNG 尺寸 / 丸体是否 44 高且居中 / 外晕是否在画布内衰减到 0。
    返回 (失败清单, 说明字符串)。几何取自**生成器常量**，像素取自**素材本身**。"""
    from PIL import Image
    p = os.path.join(ASSETS, "x_ui_qbtip_pill.png")
    if not os.path.exists(p):
        return ["读不到药丸素材 %s" % p], ""
    with Image.open(p) as im:
        im = im.convert("RGBA")
        w, h = im.size
        px = im.load()
        edge_a = max(px[0, h // 2][3], px[w - 1, h // 2][3], px[w // 2, 0][3], px[w // 2, h - 1][3])
        # 丸体（近似不透明）的竖直范围：丸体最上/最下行是 1px 描边，与外侧外晕做了抗锯齿
        # ⇒ alpha 为 252 而非 255，故用阈值 240 判定「属于丸体」，否则会少算 2 行。
        A_SOLID = 240
        ys = [y for y in range(h) if px[w // 2, y][3] >= A_SOLID]
        body_top, body_bot = (min(ys), max(ys)) if ys else (-1, -1)
    fails = []
    if h != gen.QUICK_PILL_H:
        fails.append("药丸 PNG 高 %d ≠ 元素高 %d（九宫格 t=b=0 且竖向 1:1 ⇒ 两者必须相等）"
                     % (h, gen.QUICK_PILL_H))
    if w < gen.QUICK_PILL_NINE["l"] + gen.QUICK_PILL_NINE["r"]:
        fails.append("药丸 PNG 宽 %d < 九宫格左右端点之和 %d"
                     % (w, gen.QUICK_PILL_NINE["l"] + gen.QUICK_PILL_NINE["r"]))
    if (body_bot - body_top + 1) != gen.QUICK_PILL_BODY_H:
        fails.append("药丸丸体实高 %d ≠ 常量 %d" % (body_bot - body_top + 1, gen.QUICK_PILL_BODY_H))
    if edge_a != 0:
        fails.append("药丸素材画布边缘仍有 alpha=%d ⇒ 外晕被裁（应在画布内衰减到 0）" % edge_a)
    return fails, ("PNG %dx%d；丸体 y=%d..%d（%d 高，居中）；画布四缘 alpha=0（外晕未被裁）"
                   % (w, h, body_top, body_bot, body_bot - body_top + 1))


def union_rect(elist):
    """一组元素的**并集矩形**（收起态「整条区域」= 12 项热区的并集，从数据推出）。"""
    x0 = min(e["x"] for e in elist)
    y0 = min(e["y"] for e in elist)
    x1 = max(e["x"] + e["w"] for e in elist)
    y1 = max(e["y"] + e["h"] for e in elist)
    return (x0, y0, x1 - x0, y1 - y0)


# ══════════════════════════════════════════════════════════════════════
# 断言
# ══════════════════════════════════════════════════════════════════════
def expansion_flags(idx, flags0):
    """**从数据推出**「展开态」的 flag 取值：12 项自身的 (vis_flag, vis_when) 取样（不写死名字）。
    返回 (flags, 该态的取值, 失败说明或 None)。"""
    pair = None
    for k in ITEMS:
        e = idx.get("quick.hit_%s" % k)
        if e is None:
            continue
        p = (e.get("vis_flag"), e.get("vis_when"))
        if pair is None:
            pair = p
        elif p != pair:
            return None, None, "12 项的 (vis_flag, vis_when) 不一致：%s" % p
    if pair is None or not pair[0]:
        return None, None, "12 项热区没有 vis_flag —— 无法推出「展开态」（本屏的展收互斥靠 vis_flag）"
    f = dict(flags0)
    f[pair[0]] = "" if pair[1] is None else pair[1]
    return f, f[pair[0]], None


def check_structure(idx, fails):
    """★ M37 新结构校验（数据层，与命中无关）：icon / 药丸 / 白字 / 组绑定 / 坐标等价。

    ★ L1：icon 画布尺寸**不写死** —— 以磁盘 PNG 实测尺寸为准（`icon_png_size()`）。
    """
    pops = []      # (要点, 说明)
    pill_fails, pill_note = pill_png_report()      # ★ P1：药丸素材实测（尺寸/丸体/外晕未被裁）
    fails += pill_fails
    if not pill_fails:
        pops.append("药丸素材：" + pill_note)
    png_wh = icon_png_size()
    if png_wh is None:
        fails.append("读不到 icon 素材 krkr/assets/ui/x_ui_qbicon_lock.png（尺寸断言无法进行）")
        return pops
    # 旧结构不得复活
    for dead in (OLD_HANDLE, "quick.tgl", "quick.btn", "quick.tips"):
        if dead in idx:
            fails.append("旧结构 `%s` 仍在数据里 —— M37 已裁定退场（整条带/把手/高面板），"
                         "若确要恢复须先改生成器与两端自检" % dead)
    # 每项：icon / 药丸 / 白字 / 热区四件齐备，且彼此 key 一致
    for i, k in enumerate(ITEMS):
        h = idx.get("quick.hit_%s" % k)
        ic = idx.get("quick.ic_%s" % k)
        pl = idx.get("quick.pl_%s" % k)
        tx = idx.get("quick.tx_%s" % k)
        for eid, e in (("quick.hit_%s" % k, h), ("quick.ic_%s" % k, ic),
                       ("quick.pl_%s" % k, pl), ("quick.tx_%s" % k, tx)):
            if e is None:
                fails.append("屏里找不到 %s（M37 新结构要求 12×4 件齐备）" % eid)
        if None in (h, ic, pl, tx):
            continue
        # ① icon：image + normal/hover 两态 + 组绑定 + 仅展开态可见
        if ic.get("kind") != "image":
            fails.append("%s 的 kind=%r（应为 image —— 圆形徽章是贴图，不是热区）"
                         % (ic["id"], ic.get("kind")))
        sa = ic.get("state_assets") or {}
        want_n, want_h = "ui/x_ui_qbicon_%s.png" % k, "ui/x_ui_qbicon_%s_on.png" % k
        if (sa.get("normal"), sa.get("hover")) != (want_n, want_h):
            fails.append("%s 的 state_assets=(%r,%r)，应为 (%r,%r)（常态/悬停各一件，G1 契约）"
                         % (ic["id"], sa.get("normal"), sa.get("hover"), want_n, want_h))
        # ★ L1：尺寸断言不写死 —— 以**磁盘 PNG 实测尺寸**为准（G1 交付契约：两态同尺寸）
        if (ic.get("w"), ic.get("h")) != (png_wh[0], png_wh[1]):
            fails.append("%s 的 w×h=%s×%s，应为 PNG 实测 %d×%d（G1 交付契约）"
                         % (ic["id"], ic.get("w"), ic.get("h"), png_wh[0], png_wh[1]))
        # ② 组绑定：icon 与同 key 热区同组（悬停整块热区即点亮徽章）
        if ic.get("state_group") != h.get("state_group") or not ic.get("state_group"):
            fails.append("%s 与 %s 的 state_group 不一致（icon=%r hit=%r）—— 组绑定断了，"
                         "悬停热区不会点亮徽章" % (ic["id"], h["id"], ic.get("state_group"),
                                                   h.get("state_group")))
        # ③ icon 圆心 = 热区中心（±1px：热区边长 75/73 与 icon 画布边长的奇偶差，整数像素向下取整）
        icx, icy = ic["x"] + ic["w"] / 2.0, ic["y"] + ic["h"] / 2.0
        hcx, hcy = h["x"] + h["w"] / 2.0, h["y"] + h["h"] / 2.0
        if abs(icx - hcx) > 1 or abs(icy - hcy) > 1:
            fails.append("%s 圆心(%g,%g) 偏离热区中心(%g,%g) 超过 1px"
                         % (ic["id"], icx, icy, hcx, hcy))
        # ④ icon 必须完整落在热区内（否则圆面有一部分点不到）
        if not (h["x"] <= ic["x"] and ic["x"] + ic["w"] <= h["x"] + h["w"]
                and h["y"] <= ic["y"] and ic["y"] + ic["h"] <= h["y"] + h["h"]):
            fails.append("%s 没有完整落在热区 %s 内" % (ic["id"], h["id"]))
        # ⑤ 药丸：image + 九宫格（只横向拉伸）+ 丸体右缘 = icon 左缘 − QUICK_GAP
        if pl.get("kind") != "image" or not pl.get("nine"):
            fails.append("%s 必须是带 nine 的 image（药丸底按字数各自定宽、九宫格横向拉伸）"
                         % pl["id"])
        # ★ P1：间距按**可见丸体**量（元素左右各含 QUICK_PILL_MARGIN 的透明边）
        body_right = pl["x"] + pl["w"] - gen.QUICK_PILL_MARGIN
        gap = ic["x"] - body_right
        if gap != PILL_GAP:
            fails.append("%s 丸体右缘(%d) 与 icon 左缘(%d) 的间距 = %d，应为 %d（= 生成器 QUICK_GAP）"
                         % (pl["id"], body_right, ic["x"], gap, PILL_GAP))
        if not (0 < gap <= 16):
            fails.append("%s 与 icon 的间距 %d 超出合理区间 (0,16] —— 药丸贴得太远/穿进图标"
                         % (pl["id"], gap))
        # ★ P1：宽度**由生成器公式推出**（本脚本不复制公式）；丸体左缘还要与白字框对齐
        want_w = gen.pill_w(tx.get("sample") or "")
        if pl["w"] != want_w:
            fails.append("%s 宽 %d ≠ 生成器公式 pill_w(%d 字)=%d（24×n + 2×26 + 2×4）"
                         % (pl["id"], pl["w"], len(tx.get("sample") or ""), want_w))
        if pl["h"] != gen.QUICK_PILL_H:
            fails.append("%s 高 %d ≠ QUICK_PILL_H=%d（= 素材画布高）"
                         % (pl["id"], pl["h"], gen.QUICK_PILL_H))
        # ★ P1：白字框 = **丸体矩形**（不是整个元素框；元素框左右各含透明外晕边、比丸体高 20px）
        want_box = (pl["x"] + gen.QUICK_PILL_MARGIN,
                    pl["y"] + (gen.QUICK_PILL_H - gen.QUICK_PILL_BODY_H) // 2,
                    gen.pill_body_w(tx.get("sample") or ""), gen.QUICK_PILL_BODY_H)
        if (tx["x"], tx["y"], tx["w"], tx["h"]) != want_box:
            fails.append("%s 的框 %s ≠ 丸体矩形 %s（文字须居中压在**丸体**上）"
                         % (tx["id"], (tx["x"], tx["y"], tx["w"], tx["h"]), want_box))
        # ⑥ 药丸与白字：挂在 tip flag 的该 key 上（收起态 tip 为空 ⇒ 不绘制）
        tflag = (idx.get("quick.tx_%s" % ITEMS[0]) or {}).get("vis_flag")
        for e in (pl, tx):
            if (e.get("vis_flag"), e.get("vis_when")) != (tflag, k):
                fails.append("%s 的 (vis_flag,vis_when)=(%r,%r)，应为 (%r,%r)（悬停本项才浮出）"
                             % (e["id"], e.get("vis_flag"), e.get("vis_when"), tflag, k))
        # ⑦ 药丸九宫格常量必须与生成器一致（§⑤ 已用生成器公式校验宽度，此处校验 nine 本身）
        if pl.get("nine") != gen.QUICK_PILL_NINE:
            fails.append("%s 的 nine=%s ≠ 生成器 QUICK_PILL_NINE=%s"
                         % (pl["id"], pl.get("nine"), gen.QUICK_PILL_NINE))
    if not fails:
        pops.append("旧结构（整条/把手/高面板）确已退场")
        pops.append("12×(icon %d×%d 两态（= PNG 实测）+ 药丸九宫格 + 白字 + 热区) 齐备且 key 对应"
                    % (png_wh[0], png_wh[1]))
        pops.append("icon 与热区同组、圆心偏差 ≤1px、icon 完整落在热区内")
        pops.append("丸体右缘 = icon 左缘 − %d；药丸宽度 = 生成器公式 pill_w(字数)"
                    "（= %d×n + 2×%d + 2×%d，逐条独立）"
                    % (PILL_GAP, gen.QUICK_PILL_CHAR_EM, gen.QUICK_PILL_PAD, gen.QUICK_PILL_MARGIN))
    return pops


def check(screen, mutate=None):
    """返回失败清单（[] = 全通过）。mutate(els, flags) 供反向自证注入。"""
    d = json.loads(json.dumps(screen))          # 深拷贝：反向自证绝不改磁盘
    els = d["elements"]
    flags0 = dict(d.get("flags_default") or {})
    if mutate:
        mutate(els, flags0)
    idx = by_id(els)
    fails = []

    # ── ⓪ 结构（只在正式检查里判；反向自证注入的是命中层破坏，不重复报）──
    if mutate is None:
        for line in check_structure(idx, fails):
            print("  ⓪ 结构：%s ✓" % line)

    item_ids = ["quick.hit_%s" % k for k in ITEMS]
    present = [i for i in item_ids if i in idx]
    if len(present) != 12:
        fails.append("12 项热区不齐（找到 %d 件）" % len(present))
        return fails

    # ── ① 收起态（= flags_default 原值）：整条区域**无任何命中** ──
    flags = dict(flags0)
    vis_items = [i for i in item_ids if flag_visible(idx[i], flags)]
    if vis_items:
        fails.append("① 收起态：12 项里有 %d 件在本态**可见**（期望全部不可见）：%s"
                     % (len(vis_items), "、".join(vis_items)))
    region = union_rect([idx[i] for i in item_ids])
    wins = scan(els, region, flags)
    if wins.get("(无)") != sum(wins.values()):
        others = {k: v for k, v in wins.items() if k != "(无)"}
        fails.append("① 收起态：整条区域 %s 内有 %d 点被派发（期望**全部无命中** = 完全隐藏）：%s"
                     % (region, sum(v for k, v in others.items()), others))
    if not vis_items and wins.get("(无)") == sum(wins.values()):
        print("  ① 收起态：整条区域 %s 共 %d 点**全部无命中**（右端无可点热区，12 项不可见）✓"
              % (region, wins["(无)"]))

    # ── ② 展开态 / ③ 展开+气泡+钉住（取值一律从数据推出，不写死 flag 名/取值）──
    xflags, _xval, why = expansion_flags(idx, flags0)
    if why:
        fails.append("② 无法构造「展开态」：%s" % why)
        return fails
    f3 = dict(xflags)
    tx0 = idx.get("quick.tx_%s" % ITEMS[0])
    pin = idx.get("quick.pin_mark")
    if tx0 and tx0.get("vis_flag"):
        f3[tx0["vis_flag"]] = tx0.get("vis_when") or "1"
    if pin and pin.get("vis_flag"):
        f3[pin["vis_flag"]] = pin.get("vis_when") or "1"
    for tag, label, flags in (("②", "展开态", dict(xflags)), ("③", "展开+气泡+钉住", f3)):
        bad = []
        for k in ITEMS:
            eid = "quick.hit_%s" % k
            e = idx.get(eid)
            if not flag_visible(e, flags):
                bad.append("%s 在 %s **不可见**（vis_flag 互斥写反了？）" % (eid, label)); continue
            cx = e["x"] + e["w"] / 2.0
            cy = e["y"] + e["h"] / 2.0
            w_ = click_winner(els, cx, cy, flags)
            wid = w_["id"] if w_ else "(无)"
            if wid != eid:
                # ★「是谁吞了谁」：把胜者矩形 ∩ 本项矩形 的点数算出来
                cnt = 0
                if w_ is not None:
                    x0 = max(e["x"], w_["x"]); x1 = min(e["x"] + e["w"], w_["x"] + w_["w"])
                    y0 = max(e["y"], w_["y"]); y1 = min(e["y"] + e["h"], w_["y"] + w_["h"])
                    cnt = max(0, int(x1 - x0)) * max(0, int(y1 - y0))
                bad.append("中心(%g,%g) 被 **%s**(z=%s) 吞掉 —— 期望 %s(z=%s)；两者重叠 %d 点"
                           % (cx, cy, wid, w_.get("z") if w_ else "-", eid, e.get("z"), cnt))
                continue
            act = (w_ or {}).get("action")
            if act != e.get("action"):
                bad.append("%s 胜出但 action=%r ≠ 数据里的 %r（**动作派发错**）"
                           % (eid, act, e.get("action")))
        if bad:
            fails += ["%s %s" % (tag, b) for b in bad]
        else:
            print("  %s %s：12 项中心各自胜出=自身、action 与数据一致 ✓" % (tag, label))
    return fails


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════
def load():
    return json.load(io.open(SCREEN, encoding="utf-8"))


def main():
    screen = load()
    print("=" * 74)
    print("quickbar 端到端可达性守门（复算 uiScreenClick 口径）｜ %s" % SCREEN)
    print("  屏内元素 %d 件 ｜ flags_default=%s"
          % (len(screen["elements"]), json.dumps(screen.get("flags_default") or {}, ensure_ascii=False)))
    fails = check(screen)
    print("-" * 74)
    if fails:
        print("结果：**%d 项失败**" % len(fails))
        for f in fails:
            print("  ✗ " + f)
        return 1
    print("结果：**全部通过**（收起态整条区域无命中 / 展开态 12 项各自可达且 action 正确 / "
          "M37 新结构齐备）")

    if "--selfcheck" in sys.argv:
        print("\n" + "=" * 74)
        print("反向自证（全部在内存里做，**不动磁盘**）")
        print("=" * 74)

        def m_occluder(els, flags):
            """A：给第一项注入一件 z=999 的异组遮挡热区（盖住它的中心）。"""
            e = els[0]
            for x in els:
                if x.get("id") == "quick.hit_%s" % ITEMS[0]:
                    e = x
            els.append({"id": "quick.zz_occluder", "kind": "hit", "z": 999, "action": "open_sysmenu",
                        "x": e["x"], "y": e["y"], "w": e["w"], "h": e["h"], "label": "",
                        "note": "自证注入"})

        def m_no_flag(els, flags):
            """B：抹掉 12 项热区的 vis_flag/vis_when（= 收起态也可见，互斥被破坏）。"""
            for x in els:
                if str(x.get("id", "")).startswith("quick.hit_"):
                    x.pop("vis_flag", None); x.pop("vis_when", None)

        ok = True
        for tag, mut, why in (
                ("A 注入 z=999 异组遮挡（盖住第 1 项中心）", m_occluder, "必须 FAIL"),
                ("B 抹掉 12 项热区的 vis_flag（收起态也可见）", m_no_flag, "必须 FAIL")):
            f = check(screen, mutate=mut)
            print("\n【%s】%s ⇒ %s" % (tag, why, "FAIL（符合预期）✓" if f else "PASS（**不符合预期**）✗"))
            for x in f[:6]:
                print("    ✗ " + x)
            if len(f) > 6:
                print("    …共 %d 项" % len(f))
            if not f:
                ok = False
        print("\n自证结果：%s" % ("两项均按预期 FAIL ✓" if ok else "**有项未按预期 FAIL** ✗"))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
