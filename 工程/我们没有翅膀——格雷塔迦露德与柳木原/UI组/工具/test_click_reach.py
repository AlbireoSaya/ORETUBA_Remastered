# -*- coding: utf-8 -*-
r"""M8 · **全屏「点击可达性」守门**（数据层复算，不起引擎）
（屏数**按 `layout/screens/*.json` 实测**，脚本内不写死；
 ★ M43 删 `chapter` 屏后为 19 屏；★ M45 废除 `sysmenu` 屏后为 18 屏；★ M46 删 `sysbar` 屏后为 17 屏；★ M1 新增 `replay`/`gal_shell` 后为 19 屏；★ ISSUE-20260928-06 删 `fragment` 屏后为 18 屏；★ **ISSUE-20260928-07 删 `ending` 屏后为 17 屏**）—— 屏数一律按 `layout/screens/*.json` **实测**，本脚本内不写死任何屏数

■ 为什么要有它（一审 2026-09-22 打回的 Critical）
  上一轮 `test_quickbar_reach.py` 只覆盖 **quickbar 一屏**，故「存档屏 `sv.cpy`（复制）
  被 `sv.hit_back` 100% 吞掉」这类缺陷在**别的屏**上活着时，全部守门仍然全绿。
  本脚本把同一套复算口径**推广到 `layout/screens/*.json` 的每一屏**，
  并把「谁吞了谁 + 覆盖像素数/比例」逐条打印出来。

■ 复算口径（**与引擎逐字一致**，改判据必改此处，反之亦然）
  · 可见性 `uiScreenElementVisible`（`krkr/game/ui_screens.tjs:245`）：
      `visible_default !== false` 且（`vis_flag` 缺省 → 可见；否则 `vis_when=="*"` 要求非空字符串、
        否则要求严格相等）。flag 当前值 = 屏级 `flags_default` 的初值 + 本脚本枚举出的取值。
  · 元素矩形 `uiWidgetRect`（`krkr/game/ui_widget.tjs:55`）：list 的高度按**当页可见项数**算
      （`uiWidgetListSpan`），有 `stack_bottom` 时 `y = stack_bottom - h`；其余元素取 x/y/w/h。
  · 命中 `uiScreenClick`（`ui_screens.tjs:1288`）：在可见的 `kind ∈ {hit,list}` 里取**矩形包含该点**
      且 **z 最高**者（`if(z < bestZ) continue;` ⇒ **z 相等时声明更晚者胜**）；矩形取**半开区间**
      `[x, x+w) × [y, y+h)`。
  · 附加层优先 `uiScreenAttachClick`（`ui_screens.tjs:453`）：屏带 `attach` 时**先**在该层解析，
      命中即返回（不再看承载屏）；该层的 flag 表 = 承载屏 defaults 优先、附加层 defaults 补缺。
  · `dialog` 屏另走 `uiDialogClick`（`ui_dialog.tjs:328`）：只扫 `kind="hit"`（同样取最高 z），
      `list`（选择肢）仅在选择肢展开时按 `uiWidgetListHit` 解析。
  ⚠️ 这是**点击/派发层**。**悬停层**（`uiScreenHoverAt`，候选 = 带 `state_assets` 的任何元素 ∪
     带非空 `state_group` 的 hit）另由 `工具\test_state_targets.py` 守；两者口径不同，**不可互相替代**。
  ⚠️ 本脚本**只复算数据**：不起引擎、不看渲染。引擎内的实际派发由 probe / 巡演验证。

■ 断言（每屏、每个被枚举到的 flag 状态各做一遍）
  ① **可达性**：每个**可见**的 `hit`/`list` 元素的**几何中心**，命中胜出者必须是**它自己**；
     被别的元素赢走即 FAIL，并打印「谁吞了谁 + 重叠像素数 + 占被吞者比例」。
  ② **不完全覆盖**：胜出者覆盖某元素**100% 矩形**（且两者不是同一件）即 FAIL（该元素彻底不可点）。
  ③ **屏级**：`_index.json` 登记的屏必须有对应文件且能解析（缺文件即 FAIL）。
  ④ **模态浮层态**（★ ISSUE-20260930-02 第 15 批）：某 flag 取某值时屏进入「模态」（见 `MODAL_STATES`）
     —— 该态下**非模态元素**被浮层吞掉是**设计如此**（不计 ①②）；模态族自身仍照常复核。

■ 豁免表（`EXEMPT`，**唯一合法的「已知重叠」出口**）
  用于**设计上就允许**被覆盖的元素（如浮层的「点击空白关闭」全屏热区）。
  · 每条必须写 `(屏 id, 元素 id, 类别, 理由)`；**不得按屏跳过**（写屏 id 而不写元素 id 会被拒）。
  · 豁免项**不参与 ①②** 判定，但仍会被复算并打印「可达面积 / 被覆盖比例」——
    证明它是**活的**（不是死件）；`类别=REVIEW` 的会额外打上「★ 待裁决」标记。
  · 豁免表**自带过期检查**：指向不存在的元素 / 屏 → FAIL（表与数据脱钩即报错，防止悄悄扩大豁免面）。
  · 任何新的「被吞」都必须**显式登记**才会变绿，登记内容会出现在 diff 里接受审查。

■ 与 `layout/_schema.md` §四 两条铁律的口径关系（J3 核对，2026-09-22）
  · **铁律一**「只在状态上互斥的重叠热区必须靠 `vis_flag`，不得靠 z 排序」：本脚本**正是**它的执行器 ——
    quickbar 屏的 27 个 flag 状态逐个复算，两态里把手与 12 项**从不共存**（重叠对 0），
    任一方被另一方完全吞掉的组合会在 `vis_when` 写错时立刻 FAIL。
  · **铁律二**「同时可见的『整块区域热区 + 块内具体控件』→ 具体控件赢（抬它的 z）」：本脚本**不把该结果判成缺陷** ——
    区域热区（如 `sv.hit_back`、`sysicons.dismiss`、`cfg.it_facewindow_hit`）被块内控件吃掉**中心**时，
    只要它**未被完全覆盖**（仍有可点面积）就按铁律二登记为**合法重叠**（豁免表），并打印实测可达面积。
    ⚠️ 反过来，若块内控件被区域热区 100% 吞掉（M7 修前 `sv.cpy` 9516/9516）那是**缺陷**，必 FAIL ——
    铁律二要的正是这个方向（具体控件赢），本脚本判的也是这个方向。

■ 用法
  python 工具/test_click_reach.py                    # 退出码 0 = 全屏无未登记的可达性缺陷
  python 工具/test_click_reach.py --selfcheck        # ＋反向自证（三个注入，全部必须 FAIL）
  python 工具/test_click_reach.py --verbose          # ＋逐屏逐元素明细
  python 工具/test_click_reach.py --only 23_save     # 只跑某屏（排查用）

■ 反向自证（`--selfcheck`，全部在**内存**里做，绝不落盘）
  · A「区域热区全包块内控件（M7 修前语义）」：**注入几何由数据推导** —— 把 `sv.hit_back` 放到
      **当前编辑行四件（`sv.cpy/del/mod/mov`）的并集矩形四向外扩 4px** 处、z 抬到 96，
      并清掉它的 `vis_flag/vis_when`，同时把四件降回 z=95 ⇒ 区域热区**完整包住块内控件**，
      必须 FAIL 出「`sv.hit_back` 吞了 `sv.cpy/del/mod/mov`（各 9516 点 / 100%）」。
      （M7 已落盘时本注入即为「还原缺陷」，未落盘时该几何本来就是现状 ⇒ 两种情况都必 FAIL。）
      ★ **为什么不再写死几何**：写死「上一轮的编辑行位置」已**连续两轮**导致案例失效 ——
      S=122 那轮改成 y=838；本轮 S=60 后编辑行落在 904..965，838..906 只剩 312px 交叠、
      `sv.cpy` 不再 100% 被吞 ⇒ 案例 A 变成 PASS 的**假阴性**。改为从数据推导后，
      编辑行再移动也**不需要再改本函数**。
  · B「自造新破坏」：往 dress 屏注入一件 z=999 的热区，恰好盖住 `dr.hit_ctrl_left`
      ⇒ 必须 FAIL 且**只**报这一件（证明判定精确到元素，不是整屏报警）。
  · C「豁免表过期」：把一条豁免指向不存在的元素 ⇒ 必须 FAIL（证明豁免表受审，可扩不了）。
"""
import os, io, json, glob, itertools, sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCR = os.path.join(UI, "layout", "screens")
IDX = "_index.json"


# ══════════════════════════════════════════════════════════════════════
# 豁免表：**已知的合法重叠**（不是「跳过」的出口；每条都要能被数据证伪）
# ══════════════════════════════════════════════════════════════════════
DESIGN, REVIEW = "DESIGN", "REVIEW"
EXEMPT = [    ("sysicons", "sysicons.dismiss", DESIGN,
     "浮层的「点击空白关闭」全屏热区，**铁律二 / schema §六 规定的做法**：「整块区域热区（低 z）+ "
     "块内具体控件（高 z，此处为 9 个功能图标 z30..38）」⇒ 具体控件赢，正是「点图标不关屏」想要的。"
     "它本身**不是**被吞死的元素：矩形 1920×1080、被 9 个图标合计覆盖仅 ~4%，其余 96% 面积仍是它的命中区"
     "（本脚本打印实测值 96.0%）。"),
    # ★ 2026-09-26（ISSUE-20260926-06 · PSV 换皮）：`save/load 的 sv.hit_back` 两条豁免**已删除** ——
    #   编辑键条上移 S=122 后，`sv.hit_back` 整块不再被 `sv.cpy/del/mod/mov` 覆盖（100% 可达），
    #   豁免条件已不成立（本脚本自身会告警「请从表中删除」）。
    #   ★ 2026-09-26（ISSUE-20260926-07）：上移量回调为 S=60（编辑行 y904..965）后**结论仍成立**
    #     （编辑键条整体在 hit_back 上方，`sv.hit_back` 100% 可达）；此处「S=122」为历史理由。
    # ★ M49（2026-09-24，ISSUE-20260924-06 回想屏重排）：`("backlog", "bl.list", REVIEW, …)` 条目
    #   **已删除 —— 该项「待裁决」已被本轮重排解决**，不再是「仍在生效的重叠」：
    #   原条目说 `bl.spk_hit`（PSB `#rects/speaker` 1222×224「整条消息行可点」）盖住 `bl.list` 第 1 块，
    #   属「两个各有 PSB 依据的交互区争同一块像素」，待产品裁决（可选项：列表项点击限制到文本区 /
    #   语音重播热区缩到喇叭）。
    #   本轮按用户指令改为**逐块两个按钮**（`bl.list.item_buttons`：跳转 94×29 + 重新播放 44×44）
    #   ⇒ `bl.jump_hit` / `bl.spk_hit` 整体删除，「整条消息行可点」不再存在。
    #   实测（本脚本）：26_backlog 重叠对 4 → 1，`bl.list` 可达面积 100.0%、各块中心均可达，
    #   残留的 1 对是同 z 的 `bl.close_hit` 覆盖 `bl.up_hit` 196px（4.5%，**本轮之前就有**、不吞中心）。
    #   ⚠ 遗留待办（非本模块）：`bl.list.actions` 仍全为空串，逐块按钮的 `action` 是
    #   `backlog_jump:%row%` / `backlog_replay:%row%`（冻结书 §1b，机制侧尚未实现渲染与命中）。
]


# ══════════════════════════════════════════════════════════════════════
# **模态浮层态**（★ ISSUE-20260930-02 第 15 批新增）：某 flag 取某值时，屏进入「模态」——
#   该态的**设计意图**就是「压暗层 + 面板层吞掉其余一切命中」，故此时**非模态元素**的
#   不可达是**预期**，不得报成可达性缺陷（否则模态浮层永远无法通过本闸门）。
#   · 判据（模态态下）：① 模态自身的热区（`vis_flag == 该 flag` 的那批）仍照常要求可达；
#     ② 其余元素只**登记**「被浮层吞掉（设计如此）」、不计入 FAIL；
#     ③ `exempt_ids` 是模态族内**按设计**被同族更高 z 吞掉中心的件（逐条写明理由，与 EXEMPT 同口径）。
#   · 为什么不用 EXEMPT 表：EXEMPT 是**状态无关**的；而这些件只在 `open` 态被吞，在 `closed` 态
#     照常可达 ⇒ 写进 EXEMPT 会在 closed 态被判「豁免已失效」（噪音），且会把「闭态也可达」这层
#     信息丢掉。模态态是**状态相关**的概念，故单列本表。
# ══════════════════════════════════════════════════════════════════════
MODAL_STATES = {
    "flowchart": dict(
        flag="fc_intro", value="open",
        exempt_ids=("fc.intro_scrim_hit",),
        why="章节详情浮层（`fc.intro_*`，z200–235）是**同屏模态浮层**：压暗层 `fc.intro_scrim_hit`"
            "（z210，`flow_intro_close`）＋ 面板层 `fc.intro_panel_hit`（z230，空动作＝吞点击）"
            "**按设计吞掉其余一切命中**（冻结 §三.2「浮层打开时其余热区不可达」）。"
            "`fc.intro_scrim_hit` 又被面板层吞掉**中心** —— 设计＝点面板内不关闭、点面板外（环带）才关"
            "（同 `sysicons.dismiss` 的区域热区被块内控件吃中心的口径）。"),
}


def num(el, k, d=0):
    v = el.get(k, d)
    return d if v is None else v

# ══════════════════════════════════════════════════════════════════════
# 复算：与 ui_screens.tjs / ui_widget.tjs / ui_dialog.tjs 同口径
# ══════════════════════════════════════════════════════════════════════
def flag_visible(e, flags):
    """uiScreenElementVisible 的 python 复算（`ui_screens.tjs:245-256`）。"""
    if e.get("visible_default") is False:
        return False
    fn = e.get("vis_flag")
    if fn is None or fn == "":
        return True
    want = e.get("vis_when")
    want = "" if want is None else str(want)
    cur = flags.get(fn, "")
    if want == "*":
        return cur != ""
    return cur == want


def list_cols(el):
    """uiWidgetListCols（`ui_widget.tjs`，★ M1 新增）："h" ⇒ max_cols（缺省 = 全量一行），"v" ⇒ 1。"""
    if el.get("orientation") != "h":
        return 1
    n = len(el.get("labels") or [])
    mc = num(el, "max_cols", 0)
    if mc > 0:
        return mc
    return n if n > 0 else 1


def list_per_page(el):
    """uiWidgetListPage 的 perPage（`ui_widget.tjs`）。

    ★ M1（ISSUE-20260924-08）：`orientation:"h"` + `max_cols`×`max_rows` ⇒ perPage = 列×行
    （多行网格，与 HTML 侧 buildList 同一公式）；两者缺一 ⇒ 退化为单行（旧口径）。"""
    n = len(el.get("labels") or [])
    per = n
    if el.get("orientation") == "h":
        mc = num(el, "max_cols", 0)
        mr = num(el, "max_rows", 0)
        if mc > 0 and mr > 0:
            per = mc * mr                      # ★ M1：网格
        elif mc > 0 and per > mc:
            per = mc
    else:
        mr = num(el, "max_rows", 0)
        if mr > 0 and per > mr:
            per = mr
    sc = el.get("scroll")
    if sc is not None:
        ps = num(sc, "page_size", 0)
        if ps > 0 and per > ps:
            per = ps
    if per <= 0:
        per = n
    return per


def list_span(el, count):
    """uiWidgetListSpan（`ui_widget.tjs`）：count<0 = 用 labels 全量。

    ★ M1：`orientation:"h"` 返回**主跨（宽度）** = 列数×item_w + 列距（不再按项数铺一行）。"""
    n = len(el.get("labels") or []) if (count is None or count < 0) else count
    gap = num(el, "gap", 0)
    if el.get("orientation") == "h":
        cols = max(1, list_cols(el))
        return cols * num(el, "item_w", 0) + (max(0, cols - 1) * gap)
    return n * num(el, "item_h", 0) + (max(0, n - 1) * gap)


def el_rect(el):
    """uiWidgetRect（`ui_widget.tjs`）。

    ★ M1 修正：只有 `"v"` 的分页高度才按 `uiWidgetListSpan` 复算；`"h"` 网格的**外框**
    一律取数据 `w/h`（数据即外框，两端同源）—— 原先误把主跨宽度当成高度写进 r.h。"""
    r = [num(el, "x"), num(el, "y"), num(el, "w"), num(el, "h")]
    if el.get("kind") == "list":
        if el.get("orientation") != "h":
            span = -1
            if el.get("scroll") is not None:
                span = list_per_page(el)
            r[3] = list_span(el, span)
        if el.get("stack_bottom") is not None:
            r[1] = num(el, "stack_bottom") - r[3]
    return r


def list_item_rect(el, i):
    """uiWidgetListItemRect（`ui_widget.tjs`）：i = 当页**局部**序号。

    ★ M1：`"h"` 按 `max_cols` **折行**（col = i % cols、row = floor(i/cols)），与 HTML 同公式。"""
    gap = num(el, "gap", 0)
    r = el_rect(el)
    if el.get("orientation") == "h":
        iw, ih = num(el, "item_w", 0), num(el, "item_h", 0)
        cols = max(1, list_cols(el))
        c = i % cols
        row = i // cols
        return [r[0] + c * (iw + gap), r[1] + row * (ih + gap), iw, ih]
    ih = num(el, "item_h", 0)
    return [r[0], r[1] + i * (ih + gap), r[2], ih]


def list_hit(el, x, y):
    """uiWidgetListHit（`ui_widget.tjs:127-137`）→ 项序号，-1 = 未命中。"""
    per = list_per_page(el)
    for i in range(min(per, len(el.get("labels") or []))):
        r = list_item_rect(el, i)
        if r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]:
            return i
    return -1


def contains(r, x, y):
    return r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]


def click_winner(els, x, y, flags, kinds=("hit", "list"), force_ids=()):
    """uiScreenClick 通用分支：可见的 hit/list 里取最高 z（z 相等 ⇒ 声明更晚者胜）。"""
    best_z, best = -1, None
    for e in els:
        if e.get("kind") not in kinds:
            continue
        if e.get("id") not in force_ids and not flag_visible(e, flags):
            continue
        if not contains(el_rect(e), x, y):
            continue
        z = num(e, "z", 0)
        if z < best_z:
            continue
        best_z, best = z, e
    return best


def dialog_winner(els, x, y, flags, force_ids=()):
    """uiDialogClick 的 hit 扫描分支（`ui_dialog.tjs:349-366`）：只认 kind=hit。"""
    return click_winner(els, x, y, flags, kinds=("hit",), force_ids=force_ids)


def overlap_px(a, b):
    """两矩形交面积（半开区间）。"""
    x0 = max(a[0], b[0]); x1 = min(a[0] + a[2], b[0] + b[2])
    y0 = max(a[1], b[1]); y1 = min(a[1] + a[3], b[1] + b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


TOUCH_EPS = 0.5      # < 0.5 px² 视为「仅相切/浮点毛刺」，不计为重叠


def merge_flags(host_flags, attach_defaults):
    """附加层 flag 表：承载屏 defaults 优先、附加层 defaults 补缺（schema §四 attach 条）。"""
    f = dict(attach_defaults or {})
    f.update(host_flags or {})
    return f


def scan_counts(els, rect, flags, step=1, key=None):
    """对矩形**逐点**复算 uiScreenClick，返回 {胜者键: 点数}（含 "(无)"）。
    供 `test_quickbar_reach.py`（单屏逐点扫描）与排查共用，避免两处各写一套。"""
    x0, y0, w, h = rect
    out = {}
    for yy in range(int(y0), int(y0 + h), step):
        for xx in range(int(x0), int(x0 + w), step):
            w_ = click_winner(els, xx, yy, flags)
            k = key(w_) if key else (w_["id"] if w_ else "(无)")
            out[k] = out.get(k, 0) + 1
    return out


# ══════════════════════════════════════════════════════════════════════
# 屏级 flag 状态枚举（默认态 + 每个被引用 flag 的每个取值 → 笛卡尔积）
# ══════════════════════════════════════════════════════════════════════
STAR = "\x01*"
MAX_STATES = 256


def flag_states(scr):
    """产出 [(状态名, flags)]。`vis_when="*"` 用哨兵值表示「非空」。"""
    f0 = dict(scr.get("flags_default") or {})
    need = {}
    for e in scr.get("elements") or []:
        fn = e.get("vis_flag")
        if not fn:
            continue
        w = e.get("vis_when")
        w = "" if w is None else str(w)
        need.setdefault(fn, set()).add(STAR if w == "*" else w)
    if not need:
        return [("默认态", f0)]
    names = sorted(need)
    combos = list(itertools.product(*[sorted(need[k]) for k in names]))
    if len(combos) > MAX_STATES:
        combos = [c for c in combos if sum(1 for v in c if v == STAR) == 0][:MAX_STATES]
    states = [("默认态(flags_default)", f0)]
    for c in combos:
        f = dict(f0)
        for k, v in zip(names, c):
            f[k] = v
        states.append(("+".join("%s=%s" % (k, v.replace(STAR, "<非空>")) for k, v in zip(names, c)), f))
    return states


# ══════════════════════════════════════════════════════════════════════
# 一屏的检查
# ══════════════════════════════════════════════════════════════════════
def exempt_of(sid, eid):
    for s, i, kind, why in EXEMPT:
        if s == sid and i == eid:
            return kind, why
    return None, None


def stale_exemptions(screens, table):
    """豁免表过期检查：指向**不存在的屏 / 元素**的条目（表与数据脱钩 ⇒ 必须报错）。"""
    bad = []
    for s, i, kind, why in table:
        if s not in screens:
            bad.append("豁免表的屏 %s.%s 不存在" % (s, i))
        elif not any(e.get("id") == i for e in screens[s].get("elements") or []):
            bad.append("豁免表的元素 %s.%s 不存在（数据改了？豁免表须同步订正）" % (s, i))
    return bad


CHOICE = ".choices"       # uiDialogClick 认「id 含 .choices」的列表（`ui_dialog.tjs:338`）


def dispatch(sid, screens, x, y, flags, force_ids=()):
    """按引擎的派发次序解析该点的胜出者 → (winner_el, owner_sid)。"""
    sc = screens[sid]
    aid = sc.get("attach")
    if aid and aid in screens:
        af = merge_flags(flags, (screens[aid].get("flags_default") or {}))
        w = click_winner(screens[aid]["elements"], x, y, af)
        if w is not None:
            return w, aid
    if sid == "dialog":
        # uiDialogClick：选择肢展开时**先**解析 .choices 列表（命中某项才返回）
        for e in sc["elements"]:
            if e.get("kind") != "list" or CHOICE not in str(e.get("id", "")):
                continue
            if e.get("id") not in force_ids and not flag_visible(e, flags):
                continue
            if list_hit(e, x, y) >= 0:
                return e, sid
        return dialog_winner(sc["elements"], x, y, flags, force_ids), sid
    return click_winner(sc["elements"], x, y, flags, force_ids=force_ids), sid


def check_screen(sid, screens, verbose):
    """返回 (fails, infos, stats)。所有判定都在内存里做。"""
    sc = screens[sid]
    els = sc.get("elements") or []
    clk = [e for e in els if e.get("kind") in ("hit", "list")]
    fails, infos = [], []
    stats = {"elements": len(els), "clickable": len(clk), "states": 0,
             "overlaps": set(), "checked": 0, "exempt_hit": set()}

    # ★ 对话屏的「选择肢展开态」：该态由**运行期开关** `UIDlgChoicesOpen` 控制（不是 flag），
    #   `ui_dialog.tjs:332` 只在它为真时才解析 `.choices` 列表。故额外跑一遍
    #   「强制 .choices 可见」的等价态，把选择肢纳入可达性检查（默认态下它是隐藏的）。
    states = [(n, f, frozenset()) for n, f in flag_states(sc)]
    forced_all = set()
    if sid == "dialog":
        forced_all = {e.get("id") for e in clk
                      if CHOICE in str(e.get("id", "")) and not flag_visible(e, {})}
        if forced_all:
            states.append(("对话屏·选择肢展开态（等价 UIDlgChoicesOpen=true）",
                           states[0][1], frozenset(forced_all)))

    for sname, flags, forced in states:
        stats["states"] += 1
        sname = "%s·%s" % (sc.get("__file", sid), sname)      # 行首带屏文件名，便于定位
        vis = [e for e in clk if flag_visible(e, flags) or e.get("id") in forced]
        # ★ 第 15 批：**模态浮层态**（见 MODAL_STATES）—— 该态下非模态元素的不可达是**设计如此**，
        #   只登记、不计 FAIL；模态族自身仍照常复核（否则模态浮层永远过不了本闸门）。
        mod = MODAL_STATES.get(sid)
        in_modal = bool(mod) and str(flags.get(mod["flag"], "")) == mod["value"]
        if in_modal:
            infos.append("[%s] ★ **模态浮层态**（`%s=%s`）—— 非模态元素被浮层吞掉属设计、不判缺陷；"
                         "模态族自身仍照常复核。理由：%s"
                         % (sname, mod["flag"], mod["value"], mod["why"]))
        # ── 重叠清单（高 z 覆盖低 z 的可点击元素；同 z ⇒ 声明更晚者胜）──
        for i in range(len(vis)):
            for j in range(i + 1, len(vis)):
                a, b = vis[i], vis[j]
                ra, rb = el_rect(a), el_rect(b)
                ov = overlap_px(ra, rb)
                if ov < TOUCH_EPS:
                    continue
                za, zb = num(a, "z", 0), num(b, "z", 0)
                hi, lo = (a, b) if (za > zb or (za == zb and j > i)) else (b, a)
                lo_area = max(1.0, el_rect(lo)[2] * el_rect(lo)[3])
                stats["overlaps"].add((hi.get("id"), lo.get("id")))
                infos.append("[%s] 重叠：%s(z=%s) 覆盖 %s(z=%s)  %g px（占被覆盖者 %.1f%%）"
                             % (sname, hi.get("id"), num(hi, "z", 0), lo.get("id"),
                                num(lo, "z", 0), ov, 100.0 * ov / lo_area))
        # ── 逐元素：几何中心的可达性 + 完全覆盖判定 ──
        for e in vis:
            eid = e.get("id")
            # ★ 第 15 批：模态态下 —— ① 模态族内按设计被吞中心的件（`exempt_ids`）跳过；
            #   ② 非模态元素（被浮层吞掉）跳过 ①② 判定（设计如此）。
            if in_modal:
                if eid in mod["exempt_ids"]:
                    infos.append("[%s] [模态·设计豁免] %s 的**中心**被同族更高 z 吞掉 —— 设计如此：%s"
                                 % (sname, eid, mod["why"]))
                    continue
                if e.get("vis_flag") != mod["flag"]:
                    infos.append("[%s] [模态·设计] %s 在浮层打开态被浮层吞掉（**预期**，不计缺陷）"
                                 % (sname, eid))
                    continue
            r = el_rect(e)
            cx, cy = r[0] + r[2] / 2.0, r[1] + r[3] / 2.0
            w, owner = dispatch(sid, screens, cx, cy, flags, forced)
            wid = w.get("id") if w is not None else "(无)"
            kind, why = exempt_of(sid, eid)
            # 被更高 z 者覆盖的像素（含跨层）
            cover = 0
            if w is not None and w is not e:
                cover = overlap_px(r, el_rect(w))
            ratio = 100.0 * cover / max(1.0, r[2] * r[3])
            dead = (w is None) or (cover >= r[2] * r[3] and w is not e)
            line = ("[%s] %s 中心(%g,%g) → 胜者 %s%s%s"
                    % (sname, eid, cx, cy, wid, "(附加层)" if owner != sid else "",
                       "" if e is w else "  ⚠覆盖 %.1f%%" % ratio))
            if w is not e:
                line += "  期望 %s" % eid
            # ★ `list` 的中心可能落在**项间隙**（uiWidgetListHit 返回 -1），故对 list **不以中心为准**，
            #   改以**每个可见项的中心**为可达单元（与游戏内「点某一项」一致）。
            item_fails, item_info = [], ""
            if e.get("kind") == "list":
                n = min(list_per_page(e), len(e.get("labels") or []))
                reach = 0
                for k in range(n):
                    ir = list_item_rect(e, k)
                    ix, iy = ir[0] + ir[2] / 2.0, ir[1] + ir[3] / 2.0
                    w2, o2 = dispatch(sid, screens, ix, iy, flags, forced)
                    if w2 is e:
                        reach += 1
                    else:
                        item_fails.append(
                            "[%s] %s 的**第 %d 项**中心(%g,%g) 被 **%s** 吞掉（列表项不可达）"
                            % (sname, eid, k, ix, iy, w2.get("id") if w2 else "(无)"))
                item_info = "  项 %d/%d 各自中心可达" % (reach, n)
        # ── 判定 ──
            stats["checked"] += 1
            if kind:
                # ★ 豁免「是否需要」= 元素中心被吞 **或** 有列表项被吞（两处都算被覆盖）
                needed = (e is not w) or bool(item_fails)
                if not needed:
                    infos.append("[豁免·**已失效**] %s 已不再被覆盖（可达面积 %.1f%%）"
                                 "⇒ 该条可从豁免表删除（豁免只登记**仍在生效**的重叠）"
                                 % (eid, 100.0 - ratio))
                else:
                    stats["exempt_hit"].add(eid)
                    infos.append("[豁免·%s] %s 可达面积 %.1f%%（被覆盖 %.1f%%）%s\n       理由：%s%s"
                                 % (kind, eid, 100.0 - ratio, ratio,
                                    item_info or ("被 %s 吞掉中心" % wid), why,
                                    "\n       ★ **待裁决**（见豁免表 REVIEW 类）" if kind == REVIEW else ""))
                    for x in item_fails:
                        infos.append("       （豁免项内的列表项失配）" + x)
                if verbose:
                    infos.append("     " + line + item_info)
                continue
            if e.get("kind") == "list":
                if item_info.startswith("  项 0/") or item_fails:
                    fails += item_fails or [
                        "[%s] %s 的 %d 个可见项**全部不可达**" % (sname, eid, list_per_page(e))]
                if verbose:
                    infos.append("     " + line + item_info)
                continue
            if verbose:
                infos.append("     " + line + item_info)
            if e is not w:
                fails.append("[%s] %s 的几何中心(%g,%g) 被 **%s** 吞掉（%s）—— "
                             "胜者 z=%s、被吞者 z=%s，重叠 %g px = 被吞者的 %.1f%%%s"
                             % (sname, eid, cx, cy, wid,
                                "附加层优先" if owner != sid else "取最高 z",
                                num(w, "z", 0) if w else "-", num(e, "z", 0), cover, ratio,
                                "（**100% 覆盖 ⇒ 完全不可点**）" if dead else ""))
            elif ratio >= 50.0:
                infos.append("[警告·%s] %s 虽保住了中心，但 %.1f%% 的矩形被 %s 覆盖 —— "
                             "可点面积偏小，建议复核" % (sname, eid, ratio, wid))
    return fails, infos, stats


# ══════════════════════════════════════════════════════════════════════
# 载入
# ══════════════════════════════════════════════════════════════════════
def load_all():
    screens = {}
    for p in sorted(glob.glob(os.path.join(SCR, "*.json"))):
        b = os.path.basename(p)
        if b == IDX:
            continue
        sid = b.split("_", 1)[1][:-5]
        d = json.loads(io.open(p, encoding="utf-8").read())
        d["__file"] = b
        screens[sid] = d
    return screens


def check_index(screens):
    """屏清单 `_index.json` ↔ 实际文件的一致性（缺文件 / id 不符 / 未登记的多余屏）。"""
    p = os.path.join(SCR, IDX)
    fails = []
    if not os.path.exists(p):
        return ["[_index.json] 缺失 —— 屏清单不存在，无法确认本次扫描覆盖了应有的屏"]
    idx = json.loads(io.open(p, encoding="utf-8").read()).get("screens") or []
    listed = set()
    for it in idx:
        f = it.get("file")
        listed.add(f)
        q = os.path.join(SCR, f or "")
        if not f or not os.path.exists(q):
            fails.append("[_index.json] 登记的屏文件 %r 不存在" % f)
            continue
        d = json.loads(io.open(q, encoding="utf-8").read())
        if d.get("id") != it.get("id"):
            fails.append("[_index.json] %s 的 id 不符：清单 %r / 文件 %r"
                         % (f, it.get("id"), d.get("id")))
    for sid in sorted(screens):
        b = screens[sid]["__file"]
        if b not in listed:
            fails.append("[_index.json] 盘上有 %s（id=%s）但清单未登记" % (b, sid))
    return fails


def main():
    args = sys.argv[1:]
    verbose = "--verbose" in args
    only = None
    if "--only" in args:
        only = args[args.index("--only") + 1]
    screens = load_all()
    order = sorted(screens, key=lambda s: screens[s]["__file"])

    print("=" * 78)
    print("全屏点击可达性守门（复算 uiScreenClick / uiDialogClick / uiScreenAttachClick 口径）")
    print("  屏数 %d ｜ 目录 %s" % (len(screens), SCR))
    print("  豁免表 %d 条（DESIGN %d / REVIEW %d）—— 逐条打印可达面积以证明不是死件"
          % (len(EXEMPT), sum(1 for x in EXEMPT if x[2] == DESIGN),
             sum(1 for x in EXEMPT if x[2] == REVIEW)))
    print("=" * 78)

    # ── ③ 屏级：`_index.json` ↔ 文件（清单登记与否 + id 一致）──
    idx_fails = check_index(screens)
    if idx_fails:
        print("\n── _index.json（屏清单）FAIL %d" % len(idx_fails))
        for x in idx_fails:
            print("   ✗ " + x)
    else:
        print("\n── _index.json（屏清单）OK —— 登记 %d 屏，文件齐、id 一致、无未登记的屏" % len(screens))
    fails_all = list(idx_fails)
    fails_all += ["[豁免表] " + x for x in stale_exemptions(screens, EXEMPT)]

    tot = {"overlaps": 0, "checked": 0, "exempt": 0, "screens": 0}
    used_exempt, warns = set(), []
    for sid in order:
        if only and only not in (sid, screens[sid]["__file"],
                                 screens[sid]["__file"].rsplit(".", 1)[0]):
            continue
        tot["screens"] += 1
        f, infos, st = check_screen(sid, screens, verbose)
        tot["overlaps"] += len(st["overlaps"])
        tot["checked"] += st["checked"]
        tot["exempt"] += len(st["exempt_hit"])
        used_exempt |= {(sid, x) for x in st["exempt_hit"]}
        tag = "FAIL %d" % len(f) if f else "OK"
        print("\n── %-16s %-3s 元素 %3d（可点 %3d）｜ 状态 %d ｜ 重叠对 %d ｜ 中心检查 %d"
              % (screens[sid]["__file"], tag, st["elements"], st["clickable"],
                 st["states"], len(st["overlaps"]), st["checked"]))
        for x in infos:
            print("   " + x)
        fails_all += f

    # 未被任何屏触发到的豁免条目（说明豁免表已过期）
    if not only:
        for s, i, kind, why in EXEMPT:
            # ★ M49（2026-09-24）修：原写 `if (s, i) not in used_exempt and not stale:` ——
            #   `stale` **未定义**，属死分支里的 NameError：只要豁免表里出现**第一条「已不再被覆盖」
            #   的条目**（本工程史上第一次，由 ISSUE-20260924-06 删掉 `bl.spk_hit` 触发）就会在此抛异常，
            #   把「提示删表」的善意警告变成守门自身崩溃。现值 = 未被任何屏命中即提示删除。
            #   （指向**不存在**屏/元素的过期条目另由 stale_exemptions() 判 FAIL，见上方 fails_all。）
            if (s, i) not in used_exempt:
                warns.append("[豁免表] %s.%s 已不再被覆盖（豁免只登记仍在生效的重叠，请从表中删除）" % (s, i))

    print("\n" + "-" * 78)
    print("合计：屏 %d ｜ 重叠对 %d ｜ 中心可达性检查 %d 次 ｜ 豁免命中 %d 条"
          % (tot["screens"], tot["overlaps"], tot["checked"], tot["exempt"]))
    if warns:
        print("警告（不致命）：")
        for x in warns:
            print("  ~ " + x)
    if fails_all:
        print("结果：**%d 项失败**" % len(fails_all))
        for x in fails_all:
            print("  ✗ " + x)
        rc = 1
    else:
        print("结果：**全部通过**（无未登记的可达性缺陷；豁免项均已在表中写明理由）")
        rc = 0

    if "--selfcheck" in sys.argv:
        # ★ 自证结果与主判定取「或」：自证只能让退出码更坏，**不得掩盖**主判定的失败。
        rc = selfcheck(screens, rc) or rc
        print("（主判定退出码 = %d —— 自证不影响它，两者取或）" % rc)
    return rc


# ══════════════════════════════════════════════════════════════════════
# 反向自证
# ══════════════════════════════════════════════════════════════════════
def selfcheck(screens, rc_before):
    import copy
    print("\n" + "=" * 78)
    print("反向自证（全部在**内存**里做，不动磁盘）")
    print("=" * 78)
    ok = True

    # A：M7 修前的状态（区域热区全包块内控件）
    #   修前几何（见 m34 生成器修复注释与一审证据）：`sv.hit_back` = (1560,960,320×68) **z=96**，
    #   编辑行 4 件 `sv.cpy/del/mod/mov` = (x,964,156×61) **z=95**（< 96）
    #   ⇒ `sv.cpy`（1623..1779）被完整包住，逐像素 9516/9516 归把手。
    #   ★ 2026-09-26：以上 (1560,960,320×68) 只是 **M7 原始的修前几何记录**，**不再用于注入** ——
    #     编辑行历经 S=122 / S=60 两次移动，写死坐标已连续两轮令案例失效（见下方 mut_pre_m7 内注），
    #     现注入几何一律**从当前编辑行四件的并集矩形推导**。
    #   注：M7/G1 的修法是把 4 件提到 z=97（子控件赢），故还原必须**两处一起**：
    #   只动 hit_back 而不把 4 件降回 95 反而复现不出缺陷（2026-09-22 实测踩到过）。
    def mut_pre_m7(scs):
        # ★ 2026-09-26 更新（ISSUE-20260926-07）：编辑键条再下移（S=122 → 60，
        #   `sv.cpy/del/mod/mov` 的 y 842 → 904）。**注入几何改为从数据推导**，不再写死 y ——
        #   本案例已连续两轮因「写死上一轮的编辑行位置」而失效（S=122 那轮改成 y=838；
        #   本轮 S=60 后 838..906 已包不住 904..965 的新位置 ⇒ 只剩 312px 交叠、
        #   `sv.cpy` 不再 100% 被吞 ⇒ 案例 A 变成 PASS 的假阴性）。改法：把区域热区放到
        #   **当前编辑行四件的并集矩形**正上方（四向外扩 4px）且 z 更高，四件降回 z=95。
        #   这与 M7 修前语义一致（区域热区完整包住块内控件 ⇒ 后者逐像素归区域热区），
        #   且此后编辑行再移动也**不需要再改本函数**。
        #   注：M7/G1 的修法是把 4 件提到 z=97（子控件赢），故还原必须**两处一起**：
        #   只动 hit_back 而不把 4 件降回 95 反而复现不出缺陷（2026-09-22 实测踩到过）。
        for f in ("save", "load"):
            els = scs[f]["elements"]
            rows = [e for e in els if e.get("id") in ("sv.cpy", "sv.del", "sv.mod", "sv.mov")]
            hb = [e for e in els if e.get("id") == "sv.hit_back"][0]
            x0 = min(e["x"] for e in rows)
            x1 = max(e["x"] + e["w"] for e in rows)
            y0 = min(e["y"] for e in rows)
            y1 = max(e["y"] + e["h"] for e in rows)
            hb["x"], hb["w"] = x0 - 4, (x1 - x0) + 8
            hb["y"], hb["h"] = y0 - 4, (y1 - y0) + 8
            hb["z"] = 96
            hb.pop("vis_flag", None); hb.pop("vis_when", None)
            for e in rows:
                e["z"] = 95
    # B：自造新破坏（dress 屏注入 z=999 遮挡，恰好盖住 dr.hit_ctrl_left）
    def mut_occluder(scs):
        scs["dress"]["elements"].append(
            {"id": "zz.injected_occluder", "kind": "hit", "z": 999, "visible_default": True,
             "x": 0, "y": 78, "w": 104, "h": 104, "action": "close", "label": "",
             "note": "自证注入（内存）"})
    # C：豁免表指向不存在的元素
    def mut_stale_exempt():
        EXEMPT.append(("dress", "zz.does_not_exist", DESIGN, "自证注入：指向不存在的元素"))

    cases = []
    # 基线：未注入时的失败集合（自证只关心**注入引起**的那几条，避免把已知缺陷算成注入命中）
    base_fails = set()
    for sid in sorted(screens):
        base_fails |= set(check_screen(sid, screens, False)[0])
    print("  基线（未注入）失败 %d 项" % len(base_fails))

    for tag, why, fn, want, mode in (
            ("A 区域热区全包块内控件（注入几何按当前编辑行推导）",
             "注入态必须 FAIL 出 sv.cpy（注入后块内四件一并被吞；若基线本就是修复前状态，则该注入＝复现现状）",
             mut_pre_m7, "sv.cpy", "absolute"),
            ("B dress 屏注入 z=999 遮挡，恰好盖住 dr.hit_ctrl_left",
             "必须 FAIL 且**只**新增这一件", mut_occluder, "dr.hit_ctrl_left", "delta")):
        scs = copy.deepcopy(screens)
        fn(scs)
        print("\n【%s】预期：%s" % (tag, why))
        fails = []
        for sid in sorted(scs):
            f, inf, st = check_screen(sid, scs, False)
            fails += f
            for x in inf:
                if "重叠" in x and ("sv." in x or "dr.hit_ctrl_left" in x):
                    print("    · " + x)
        new_fails = fails if mode == "absolute" else [x for x in fails if x not in base_fails]
        hits = [x for x in new_fails if want in x]
        print("    → 结果：%s（%s失败 %d 项，其中命中预期缺陷「%s」%d 项）"
              % ("FAIL（符合预期）✓" if new_fails else "PASS（**不符合预期**）✗",
                 "注入态共" if mode == "absolute" else "注入新增",
                 len(new_fails), want, len(hits)))
        for x in new_fails[:3]:
            print("      ✗ " + x)
        if len(new_fails) > 3:
            print("      …共 %d 项" % len(new_fails))
        if mode == "delta" and len(new_fails) != 1:
            print("      ✗ 期望**只**新增注入的那一件（实际新增 %d 项）—— 判定不够精确" % len(new_fails))
            ok = False
        if not new_fails or not hits:
            ok = False
        cases.append(tag)

    print("\n【C 豁免表指向不存在的元素】预期：必须 FAIL")
    EXEMPT.append(("dress", "zz.does_not_exist", DESIGN, "自证注入：指向不存在的元素"))
    try:
        bad = stale_exemptions(screens, EXEMPT)
        print("    → 检出过期条目 %d 条：%s" % (len(bad), bad))
        if not bad:
            ok = False
            print("    ✗ 未检出（不符合预期）")
    finally:
        EXEMPT.pop()

    print("\n自证结果：%s" % ("三项均按预期 FAIL ✓" if ok else "**有项未按预期 FAIL** ✗"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
