# -*- coding: utf-8 -*-
r"""M34 · 按《交汇协奏曲》PSB 坐标重建各屏 layout。

数据源：`临时\cc_psb_layers\idx_<n>.json`（dump_psb_layers.py 产出，1920×1080 绝对坐标）
素材：`krkr\assets\ui\x_ui_*.png`（ui_slice.py 产出）

★★★ **警告：本文件直写 `layout/screens/*.json`，改 JSON 必须同步回本文件** ★★★
  这些屏 JSON **由本脚本产出**。任何「只改 JSON、不回写本文件」的改动
  （编辑器导出入库、M35b 类级迁移补丁、手工补丁脚本……）都会在**下一次运行本脚本时被静默抹掉**。
  实测过的静默清空（2026-09-22 一审）：
    · `01_title.json` → 重跑会删 `title.menu_txt_*` 7 件 + 丢 7 个 `state_group`（M35b 组绑定全失）
    · `36_choices.json` → 重跑会删 `ch.bg_1/2/3` 并让 3 个 hit 重新持有 `state_assets`（拉伸涂抹回归）
    · `21/32/37_*.json` → 重跑会把 M35b 迁移过的三态图塞回热区 + 抹掉组绑定
      （`26_backlog.json` 已于 M49 删 `build_backlog` 改为手工维护，不再在列；
        `34_sysbar.json` 已于 M46 随屏删除，`25_config.json` 已于 M47 删 `build_config`）
  ⇒ **规矩**：改 JSON 必须同时改本文件（如把字段提成 override 常量，见 `M35B_OVERRIDES`），
     并跑 `python 工具\test_gen_sync.py` 自证「生成器能完整复现磁盘」。
     例外（**已退休、改为手工维护**的屏，不在本规矩范围）：`25_config.json`（M47 删 `build_config`）、
     `26_backlog.json`（**M49 删 `build_backlog`**，见 §73 注）；连同已删屏
     `20_sysmenu`（M45）/ `34_sysbar`（M46）——这几屏与「重跑即抹」无关，因为已无产出函数。
  ⇒ 本文件的 `write()` 已加**防静默清空守门**：若一次写入会删掉元素 id 或抹掉受保护字段
     （`state_group`/`state_assets`/`vis_flag`/`vis_when`/`nine`/屏级 `flags_default`/`reveal`/`attach`），
     它会**拒绝落盘并打印会丢什么**；确需覆盖时用 `--force`（或环境变量 `M34_FORCE=1`）。

**「100% 复刻」的界定**：几何与结构逐字照搬 PSB；配色与材质换成冰蓝霜白；**文字一律引擎绘制**
（《交汇协奏曲》把按钮文字烘焙进图，本工程铁律禁止，故素材留空、文字由引擎画）。

九宫格规则（`verify_ui.py` 检查 [2] 硬要求）：
  - 元素 w/h == PNG 实尺寸  → 不带 nine
  - 元素 w/h ≠ PNG 实尺寸  → **必须带 nine**；按需拉伸的那一维取内缩，另一维 0（避免整体模糊）
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
SCR = os.path.join(UI, "layout", "screens")
LAY = r"E:/ZCode Workspace/Galgame/临时/cc_psb_layers"

from PIL import Image as _PILImage
SIZE = {os.path.basename(p): _PILImage.open(p).size
        for p in glob.glob(os.path.join(ASSETS, "*.png"))}
SRC_UI = "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器"
FONT_MENU, FONT_BODY, FONT_SMALL, FONT_TAG = 33, 36, 24, 27


def nine_for(a, d):
    """a=素材尺寸, d=设计尺寸；返回 nine 或 None。

    ★ M34 修正（实机目视发现）：初版启发式「只拉伸需要更多缩放的那一维、另一维内缩取 0」
      在**横竖都需要拉伸**时会把另一维也整体拉伸 → **横向/纵向涂抹**（配置页签条、
      曲名列表板、标题条均中招）。
      改为**标准九宫格**：四边各取内缩（角块 1:1 保留、中段双向拉伸），
      这才是九宫格的本意，且不会涂抹。
    """
    if a == d:
        return None
    aw, ah = a
    dw, dh = d
    if aw >= dw and ah >= dh:
        return {"l": 0, "t": 0, "r": 0, "b": 0}          # 整体等比缩小（不切片）
    # 细条（高 < 8）不做纵向内缩，否则内缩吃掉整条高度
    it = 0 if ah < 8 else max(1, min(ah // 4, 120))
    il = 0 if aw < 8 else max(1, min(aw // 4, 120))
    # 内缩和不得超过版面尺寸（verify [2]：w >= l+r、h >= t+b）
    it = min(it, max(0, (dh - 1) // 2))
    il = min(il, max(0, (dw - 1) // 2))
    return {"l": il, "t": it, "r": il, "b": it}


def img(eid, z, asset, x, y, w, h, note, opacity=255, source=SRC_UI):
    a = SIZE[os.path.basename(asset)]
    e = {"id": eid, "kind": "image", "z": z, "visible_default": True,
         "asset": "ui/" + asset, "x": x, "y": y, "w": w, "h": h,
         "opacity": opacity, "source": source, "note": note}
    n = nine_for(a, (w, h))
    if n:
        e["note"] = note + "（素材 %d×%d ≠ 设计 %d×%d → nine %s）" % (a[0], a[1], w, h, n)
        e["nine"] = n
    return e


def txt(eid, z, x, y, w, h, sample, size, note, align="center", valign="middle",
        wrap=False, max_lines=1, color="@palette.node_locked", bold=True, ls=None):
    e = {"id": eid, "kind": "text", "z": z, "visible_default": True, "x": x, "y": y, "w": w, "h": h,
         "font": {"size": size, "bold": bold, "color": color, "shadow": False,
                  "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "align": align, "valign": valign, "wrap": wrap, "max_lines": max_lines}
    if ls:
        e["line_spacing"] = ls
    e["sample"] = sample
    e["note"] = note
    return e


def hit(eid, z, x, y, w, h, action, label, note, states=None):
    e = {"id": eid, "kind": "hit", "z": z, "visible_default": True, "x": x, "y": y,
         "w": w, "h": h, "action": action, "label": label,
         "font": {"size": FONT_SMALL, "bold": False, "color": "@palette.node_locked",
                  "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "align": "center", "note": note}
    if states:
        e["state_assets"] = states
    return e


def rect(eid, z, x, y, w, h, color, opacity, note):
    return {"id": eid, "kind": "rect", "z": z, "visible_default": True, "x": x, "y": y,
            "w": w, "h": h, "color": color, "opacity": opacity, "note": note}


def load(idx):
    return json.load(open(os.path.join(LAY, "idx_%d.json" % idx), encoding="utf-8"))["normalized"]


# ── 防静默清空守门（M8，2026-09-22）──────────────────────────────────
#   本脚本的产出（`layout/screens/*.json`）常被**别的工序**在盘上继续加工
#   （编辑器导出、M35b 类级迁移补丁、手工补丁），若那些改动没回写本文件，
#   **一次重跑就会把它们静默抹掉**（实测：title 的 7 件文字图 + 7 个 state_group、choices 的 ch.bg_1/2/3 …）。
#   故这里在落盘前比一次：**只拦「会丢东西」的写入**（删元素 id / 抹受保护字段），
#   纯新增或值改动一律放行（那些不是"抹掉别人的活"）。
#   确需覆盖（例如已把改动搬进生成器、要重建某个屏）：`--force` 或 `M34_FORCE=1`。
PROTECTED_FIELDS = ("state_group", "state_assets", "vis_flag", "vis_when", "nine", "opacity")
PROTECTED_SCREEN = ("flags_default", "reveal", "attach", "overlay")


# ★ M46（一审 Major-5 打回后补）：**嵌套**保护字段。
#   原实现只比「元素顶层键是否存在」（PROTECTED_FIELDS），于是像
#   `item_frame.state_assets`（M46 新增的逐项态图）、`font.outline` 这类**嵌套**新字段
#   在「生成器产出同名字段、但内层少了几键」时**不会被拦** ⇒ 一跑生成器就静默丢功能。
#   这里按 `路径.子路径` 递归取值比较（只在「磁盘有、本次不产出」时拦）。
PROTECTED_NESTED = (
    "item_frame.state_assets",
    "item_frame.asset",
    "state_assets.normal",
    "font.outline",
    "font.faces",
)


def _nested_get(obj, path):
    cur = obj
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None, False
        cur = cur[k]
    return cur, True


def _would_lose(p, d):
    """返回「本次写入会丢掉什么」的清单（[] = 安全）。只读磁盘，不改。"""
    if not os.path.exists(p):
        return []
    try:
        old = json.load(open(p, encoding="utf-8"))
    except Exception as ex:
        return ["（磁盘上的 %s 解析失败：%r —— 为避免覆盖，拒绝写入）" % (os.path.basename(p), ex)]
    lost = []
    for k in PROTECTED_SCREEN:
        if k in old and k not in d:
            lost.append("屏级字段 `%s`（磁盘有、本次不产出）：%r" % (k, old[k]))
    oe = {e.get("id"): e for e in old.get("elements") or []}
    ne = {e.get("id"): e for e in d.get("elements") or []}
    for i in sorted(set(oe) - set(ne)):
        lost.append("元素 `%s`（磁盘有、本次不产出 ⇒ 会被删掉）" % i)
    for i in sorted(set(oe) & set(ne)):
        for k in PROTECTED_FIELDS:
            if k in oe[i] and k not in ne[i]:
                lost.append("元素 `%s` 的字段 `%s`（磁盘有、本次不产出）：%r" % (i, k, oe[i][k]))
        for path in PROTECTED_NESTED:
            ov, has_o = _nested_get(oe[i], path)
            nv, has_n = _nested_get(ne[i], path)
            if has_o and not has_n:
                lost.append("元素 `%s` 的嵌套字段 `%s`（磁盘有、本次不产出）：%r"
                            % (i, path, ov))
    return lost


def write(name, sid, title, note, els, extra=None):
    """extra：可选的**屏级**字段（如 flags_default / reveal / attach，见 layout/_schema.md §四）。
    不给时输出与旧版逐字节一致（键序 id/title_cn/owner/note/elements 不变）。

    ★ M8：落盘前跑 `_would_lose`；会丢东西就**拒绝写**（见上方守门说明）。
    """
    p = os.path.join(SCR, name)
    d = {"id": sid, "title_cn": title, "owner": "M34", "note": note}
    if extra:
        d.update(extra)
    d["elements"] = els
    if not force():
        lost = _would_lose(p, d)
        if lost:
            print("\n" + "!" * 74)
            print("!! 拒绝写入 %s —— 本次重跑会**丢数据**（防静默清空守门，M8）" % name)
            for x in lost:
                print("!!   ✗ %s" % x)
            print("!! 正确做法：把盘上的这些改动**回写进本文件**（提成 override 常量），")
            print("!!          再跑 `python 工具\\test_gen_sync.py` 自证「生成器可完整复现磁盘」。")
            print("!! 确需强行覆盖：`python 工具/m34_build_screens.py --force`（或 set M34_FORCE=1）")
            print("!" * 74)
            raise SystemExit(2)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("%-22s %2d 元素" % (name, len(els)))


def force():
    return ("--force" in sys.argv) or (os.environ.get("M34_FORCE", "") == "1")


HEAD = ("**M34（2026-09-21）· 按《交汇协奏曲》PSB 坐标 100%% 复刻**（用户裁定：「完全复刻《交汇协奏曲》的 UI 系统…"
        "只是配色不同」）。\n"
        "★ **几何与结构逐字照搬**：本屏每个元素的 x/y/w/h 均取自《交汇协奏曲》`locale_cn.xp3` 内 PSB 容器 "
        "idx %d 的图层 `left/top/width/height`（基准 1920×1080，与本作画布一致）。\n"
        "★ **配色与材质另起一套**：冰蓝霜白磨砂玻璃（实测配色见 `_工作\\M34_风格锚点.md`），**无雪花要素**"
        "（用户 2026-09-21 裁定）。\n"
        "★ **文字一律引擎绘制**：原作的按钮文字/角色名/标题是**烘焙进图**的，本工程铁律禁止，故 AI 素材留空面、"
        "文字由引擎画 —— 这是唯一有意偏离（见 `M34_UI复刻总纲.md` §七）。\n"
        "★ 素材：`ui/x_ui_*.png`（153 件新 UI 资产）；坐标台账：`_工作\\M34_交汇协奏曲UI布局规格.md`。")


# ══════════════════════════════════════════════════════════════════════
# 84 标题画面（V1 裁决：竖排条）
# ══════════════════════════════════════════════════════════════════════
def build_title():
    old = json.load(open(os.path.join(SCR, "01_title.json"), encoding="utf-8"))
    # ★ M41（2026-09-23）——本屏改为**忠实透传**（不再重建）：
    #   本屏自 M35b 起由用户/编辑器持续手工调整（7 条文字层 `title.menu_txt_*` + `state_group` 组绑定、
    #   M40 的「控件 x+200」、M41 的「删署名行」）。原先「读盘只保留 bg/logo/text_copyright + 硬编码重建 7 行
    #   （RX=56）」的写法在重跑时会**回退这些用户改动**（x 退回 56、丢掉 7 条文字层与组绑定、复活署名行；
    #   M41 删掉 `text_copyright` 后还会 `KeyError` 崩溃）。
    #   ⇒ 改为：**元素与屏 note 原样写回**，使「重跑生成器」对本屏**幂等、绝不回退人工作品**。
    #   （下面 M34 期的重建代码保留备查但已不可达；若确需重建该屏，请走 `--force` 并自行承担覆盖风险。）
    write("01_title.json", "title", old.get("title_cn") or "标题画面",
          old.get("note") or ((HEAD % 84) + "\n★ **V1 裁决（用户 2026-09-21）**：标题菜单改**竖排条**，推翻 M28 的底部横排。"),
          old.get("elements") or [])
    return
    keep = {e["id"]: e for e in old["elements"]}
    els = []
    els.append(keep["title.bg"])
    els.append(keep["title.logo"])
    els[-1]["note"] = ("左上角标题 logo（**用户 2026-09-21 裁定保留**）。位置保持本作既有值 "
                       "（《交汇协奏曲》的 logo 在 PSB 里是 x37 y35 w533 h276 —— 见注）。")
    # PSB idx84：主菜单竖排条 x99 y423 w248 h565（三态同矩形）；行热区 #1..#7 x73 y408+87i w385 h72
    # ★ 用户 2026-09-21：改用**圆形图标**代替文字 → 行几何相应放宽
    #   （图标 96px、步距 100、左沿 x=56；原 PSB 的 385×72 行矩形是为文字排版定的）
    RX, RW, RH, RY0, STEP = 56, 385, 96, 360, 100
    CX = RX + RW / 2.0                       # 265.5：条与文字共同的水平中心
    SW, SH = 248, 594                        # 条拉伸到覆盖 7 行（408..1002）
    SX, SY = CX - SW / 2.0, RY0
    # ★ 用户 2026-09-21 裁定：**不要矩形背景**，改用 Gen Jyuu Gothic XP Bold 的**透明底英文
    #   按钮字图**（由 工具\lyai-image-api\gen_menutxt.py 从字体直出 PNG）。
    #   行几何仍取 PSB （x73 y408+87i w385 h72），字图在行内**居中**。
    MENU = [("start", "START", "game_start"),
            ("continue", "CONTINUE", "game_continue"),
            ("load", "LOAD", "open_load"),
            ("flowchart", "FLOWCHART", "open_flowchart"),
            ("config", "CONFIG", "open_config"),
            ("gallery", "GALLERY", "open_gallery"),
            ("exit", "EXIT", "quit_game")]
    for i, (key, en, act) in enumerate(MENU, 1):
        y = RY0 + (i - 1) * STEP
        a = SIZE["x_ui_menuicon_%s.png" % key]
        # ★ 用户 2026-09-21：**居左竖向排列**，只要求**高度一致**，右端不必对齐
        x = RX
        yy = y + (RH - a[1]) / 2.0
        # ★ 关键修复：**不再单独放 image 元素**。 规定「带 state_assets 的 hit
        #   会按 normal/hover 态画图」，绘制矩形 = hit 的矩形；若另放一个 image，就会**同一张图
        #   按两种尺寸画两遍** → 用户看到的「两层字」（一层原尺寸、一层被拉伸）。
        #   故：hit 矩形 = 字图**原尺寸**（不拉伸），两态由 state_assets 提供；不再有重复层。
        els.append(hit("title.menu_hit_%d" % i, 95, x, yy, a[0], a[1], act, "",
                       "菜单项热区（action=%s）。**state_assets 为字图两态**（常态深蓝 #2E6BB4 / "
                       "悬停亮冰蓝 #71AAF3）—— 无矩形底，仅文字换色。" % act,
                       states={"normal": "ui/x_ui_menuicon_%s.png" % key,
                               "hover": "ui/x_ui_menuicon_%s_on.png" % key,
                               "pressed": "ui/x_ui_menuicon_%s_on.png" % key}))
    els.append(keep["title.text_copyright"])
    write("01_title.json", "title", "标题画面",
          (HEAD % 84) + "\n★ **V1 裁决（用户 2026-09-21）**：标题菜单改**竖排条**，推翻 M28 的底部横排。",
          els)


# ══════════════════════════════════════════════════════════════════════
# 78 底部系统条 —— ★ M46（2026-09-23，用户裁定）：**已整体删除**
#   · 屏数据 `layout/screens/34_sysbar.json`（8 元素）按用户裁定删除（18 → 17 屏），
#     `_index.json` 条目 / 巡演白名单（`ui_screens.tjs` 的 `probe`）/ 两端活引用 / 文档清单同清；
#   · 本文件的 `build_sysbar()` 与 `__main__` 的调用一并删除（M45 删 `build_sysmenu()` 同例）；
#   · ★ **素材一律保留原位、不归档、不删除**：`x_ui_sysbar.png` 与流程图屏 `fc.sysbar` **共用**
#     （`build_flowchart()` 仍引用它）；`x_ui_snap_*` / `x_ui_hide_*` / `x_ui_spk_*` 亦留在
#     `krkr/assets/ui/`（`x_ui_spk_*` 另被 `backlog` 屏 `bl.spk` 共用）。
#   · 屏用途 / 元素清单 / 回滚方式：`_工作/M46_旧素材归档/说明.md`。
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 81 系统菜单快捷条（**M37 形态：一排独立圆形 icon 按钮**）
#
#   ★ M37（ISSUE-20260923-01）· 用户裁定：**原「整条带」太丑**，改为
#       · 12 个彼此独立的**圆形 icon 徽章**（`quick.ic_<key>`，64×64 画布 / 圆径 56，悬停换 `_on` 材质）；
#       · 悬停时在该 icon **左侧**浮出**中文名称药丸**（`quick.pl_<key>` 底 + `quick.tx_<key>` 白字）；
#       · **平时完全隐藏，鼠标贴到屏幕右端才整列淡入**（不再有 slim 把手）。
#     ⇒ 退场四件：`quick.btn`（展开整条 63×888）、`quick.tgl`（收起 slim 把手 63×513）、
#       `quick.tips`（高面板 197×876）、`quick.hit_toggle`（整条把手热区）。
#       7 件旧素材已**移入** `_工作\M37_旧素材归档\`（不删；旧 JSON 快照同目录）。
#
#   ★ 机制侧**未新增任何字段**，全部复用既有两端能力（见 layout/_schema.md §四）：
#     · `vis_flag`/`vis_when` 控显隐（收起态 12 icon + 12 药丸 + 12 文字全不绘制）；
#     · `state_assets{normal,hover}` 管悬停材质（`image` 也能带三态图，M35b 起支持）；
#     · `state_group` **组绑定**：icon 与**同 key 的热区**同组 ⇒
#       指针落在 75×73 热区内的**任何位置**（不只是 64×64 画布/56 圆径上）都会点亮该 icon
#       —— 悬停材质与左侧名称药丸因此**同步出现**（气泡 key 由热区 id 推出，见
#       `uiScreenRevealTipAt` / `tipKeyAt`）；
#     · `qbar_tip` flag = 「当前悬停项 key」，药丸与白字都挂在它上面。
#
#   ★ z 序（三层，理由逐条）：
#       hits 95 > pin_mark 93 > icons 90 > 文字 30 > 药丸 28
#     · hit 最高：**点击只认 hit/list**（`uiScreenClick`），图标是 image 不参与点击 ⇒
#       点在徽章上仍由热区派发动作（HTML 侧走 `interactiveUnderPoint` 的遮挡兜底，规则⑦）；
#     · pin_mark 在 hit 之下（不吃点击）而在 icon 之上（叠加可见）；
#     · **icon 的 z 必须低于 hit**：同组后悬停胜出者恒为 hit（z 更高）⇒
#       `工具\test_state_targets.py` 的「几何中心胜出者须同组」成立（icon 与 hit 同组）。
#
#   ★ 坐标口径（**一律写死在数据里，不在 TJS/JS 写死**）：
#     · icon 圆心 = 该 key 热区矩形中心（热区 x1845 w75 / y7+75n h73）；
#       因 75 与 73 均为奇数、icon 画布 64 为偶数，**整数像素无法精确对中**，
#       故统一向下取整：icon.x = 1845 + (75-64)//2 = 1850，icon.y = y + (73-64)//2 = y+4，
#       与热区中心的偏差为 (0.5, 0.5) px（不影响命中，icon 完整落在热区内）。
#       ★ L1（2026-09-23，主代理裁决）：画布 **56 → 64**（圆径仍 56、保留圆外柔光、描边加粗到 ~2px），
#         由 G1 按新规格重切；理由：实际渲染下 56 画布「图标偏小偏苍白」。
#     · 药丸右缘 = icon 左缘 − 8（L1 由 −6 微调到 −8）；药丸宽 = 34×字数 + 44（端点圆角 22 + 左右各 12 内衬）；
#       **每条一个独立 image 元素**（各自宽度），九宫格 l=r=22 / t=b=0 横向拉伸。
#
#   本函数产出的 35_quickbar.json 是**唯一数据源**（不得只改 JSON 不改这里，否则重跑会被抹掉）。
# ══════════════════════════════════════════════════════════════════════
# ── M37 几何常量（**唯一出处**；元素 note 里复述同值便于人读）────────────
QUICK_HIT_X, QUICK_HIT_W, QUICK_HIT_H, QUICK_HIT_Y0, QUICK_HIT_STEP = 1845, 75, 73, 7, 75
QUICK_ICON = 64                      # G1 交付契约：严格 64×64 画布（圆径 56、圆外柔光）—— L1 由 56 改 64
QUICK_GAP = 8                        # icon 左缘 − 药丸右缘 —— L1 由 6 微调到 8
# ── 名称药丸（★ P1 重做：入我方冰蓝族；宽度**公式化**，唯一出处在此）──────
#   机制：**只横向拉伸**（nine l=r=25 / t=b=0），竖向 1:1 —— 故元素高必须 == PNG 高（64）。
#   丸体 44 高居中于 64 画布（上下各 10 留白）⇒ 约 3px 外晕在画布内自然衰减为 0，不被裁。
QUICK_PILL_H = 64                    # ★ 元素高 = PNG 画布高（P1：由 44 改 64；丸体仍居中，视觉位置不变）
QUICK_PILL_BODY_H = 40               # ★ Q2：丸体高 44 → 40（vision：形态与徽章"同重"；参照丸/徽比 0.57）
QUICK_PILL_GLOW = 3                  # 外晕最大半径（px）——@palette 之外的美术常量，直接烘进 PNG
QUICK_PILL_MARGIN = QUICK_PILL_GLOW + 1   # 元素左右各留的透明边（外晕半径 + 1px：外晕在素材画布内已衰减到 0）
QUICK_PILL_R = 20                    # 圆角半径 = 丸体高/2（Q2：40/2）
QUICK_PILL_NINE = {"l": 23, "t": 0, "r": 23, "b": 0}   # 端点 = 半径 20 + 外晕 3 = 23（Q2 实测更新），纵向不切片
QUICK_PILL_CHAR_EM = 21              # ★ 字号 = CJK 字宽（1em）：24 → 21（实测三标签墨高 21/22/21，最大 22
                                     #   ⇒ 占丸高 40 的 55%，落在 vision 要求的 52–55%；参照 50%）
QUICK_PILL_PAD = 24                  # 丸体左右内边距（须 ≥ 圆角半径 20，字不进圆角区；左右天然对称）
# ★ Q1：12 条药丸白字加深色描边（照参照做法：可读性靠描边）。**用既有机制**（M38 的 font.outline*，
#   两端已通、纯渲染不参与布局），不动引擎、不动主题。
QUICK_PILL_TEXT_OUTLINE = {"outline": True, "outline_color": "#16305A", "outline_width": 1}
SRC_QPILL_DESC = ("程序化生成（PIL）→ `_工作\\M37_占位件与药丸生成.py::draw_pill()`；"
                  "底色竖向渐变 #6FA8E8→#3F6FB4（渐变在丸体顶部 10px 内收敛，全体白字对比度 ≥4.9:1）、"
                  "1px 描边 #A0C9F7、约 3px 青蓝外晕（64 高画布内衰减为 0）——"
                  "**不新增色板键**（这些值烘进 PNG，layout 侧不引用；palette.json 未改）")


def pill_body_w(label):
    """丸体宽 = 字号×字数 + 2×内边距（左/右内边距**天然对称**：文字在丸体内居中）。"""
    return QUICK_PILL_CHAR_EM * len(label) + 2 * QUICK_PILL_PAD


def pill_w(label):
    """元素宽 = 丸体宽 + 2×QUICK_PILL_MARGIN（元素左右各含「外晕 + 1px 全透明」边）。"""
    return pill_body_w(label) + 2 * QUICK_PILL_MARGIN
QUICK_Z_ICON, QUICK_Z_PILL, QUICK_Z_TX, QUICK_Z_PIN, QUICK_Z_HIT = 90, 28, 30, 93, 95
SRC_QBICON = ("G1 AI 直出（`krkr/assets/ui/x_ui_qbicon_<key>.png` 常态 / `_on.png` 悬停，各 64×64）；"
              "**本轮落盘的是 G2 程序化占位件**（`_工作\\M37_占位件与药丸生成.py`，56×56 纯色圆环），"
              "G1 落盘后同名覆盖 —— 占位判定见 `_工作\\M37_判定是否G1覆盖.py`（像素统计）")
def build_quickbar():
    els = []

    def vis(e, flag, when):
        """加元素级可见性（vis_flag / vis_when **成对出现**，见 layout/_schema.md §四）。"""
        e["vis_flag"] = flag
        e["vis_when"] = when
        return e

    def icon_elem(eid, key, x, y, note):
        """圆形 icon 徽章：image + 三态图中的 normal/hover 两态（组绑定同 key）。"""
        e = {"id": eid, "kind": "image", "z": QUICK_Z_ICON, "visible_default": True,
             "asset": "ui/x_ui_qbicon_%s.png" % key,
             "state_assets": {"normal": "ui/x_ui_qbicon_%s.png" % key,
                              "hover": "ui/x_ui_qbicon_%s_on.png" % key},
             "state_group": "quick.%s" % key,
             "x": x, "y": y, "w": QUICK_ICON, "h": QUICK_ICON,
             "opacity": 255, "source": SRC_QBICON, "note": note}
        return e

    def pill_elem(eid, key, x, y, w, note):
        """名称药丸底：九宫格**只横向拉伸**（端点 25 = 半径 22 + 外晕 3，1:1 保留；t=b=0）。"""
        return {"id": eid, "kind": "image", "z": QUICK_Z_PILL, "visible_default": True,
                "asset": "ui/x_ui_qbtip_pill.png", "x": x, "y": y, "w": w, "h": QUICK_PILL_H,
                "opacity": 255, "source": SRC_QPILL_DESC, "note": note,
                "nine": dict(QUICK_PILL_NINE)}

    # ── 钉住指示（qbar_pin=="1" 才显示）────────────────────────────────
    #   ★ M37 改为**复用锁定 icon 的悬停态图**（`x_ui_qbicon_lock_on.png`）作叠加层（二选一，理由）：
    #     ① 语义直给：钉住 = 「锁定」处于激活态，直接用该按钮自己的悬停/激活材质，
    #        用户一眼可见「锁定已生效」，不必再学一个几何高亮块的含义；
    #     ② 与新的圆形按钮形态一致：旧的 63×73 半透明矩形是按「整条 63 宽条体」设计的，
    #        在「一排独立圆徽章」上会画出一个**方形**高亮，与圆形徽章格格不入；
    #     ③ 代价可控：多引用一件既有 PNG（G1 交付物），不新增美术、不新增色板键。
    #   ★ 几何 = 锁定 icon 的矩形（64×64，无 nine ⇒ w/h 必须等于 PNG 实尺寸，verify_ui [2]）。
    #   ★ z=93：**低于 hit（95）**⇒ 不吃点击；**高于 icon（90）**⇒ 叠加在常态徽章之上。
    #   ★ visible_default **必须为 True**（靠 flag 控显隐，见 _schema §四 铁律）；默认
    #     `flags_default.qbar_pin=""` ≠ "1" ⇒ 默认仍不显示。
    lock_icon_x = QUICK_HIT_X + (QUICK_HIT_W - QUICK_ICON) // 2
    lock_icon_y = QUICK_HIT_Y0 + (QUICK_HIT_H - QUICK_ICON) // 2
    pin = {"id": "quick.pin_mark", "kind": "image", "z": QUICK_Z_PIN, "visible_default": True,
           "asset": "ui/x_ui_qbicon_lock_on.png",
           "x": lock_icon_x, "y": lock_icon_y, "w": QUICK_ICON, "h": QUICK_ICON,
           "opacity": 255, "source": SRC_QBICON,
           "note": "钉住（lock）状态指示：**复用锁定 icon 的悬停态图** `x_ui_qbicon_lock_on.png` "
                   "叠加在常态徽章之上（x%d y%d w%d h%d，与 `quick.ic_lock` 同矩形），"
                   "**opacity=255**（★ L2 订正，2026-09-23：原为 200 —— 半透明叠在常态图上会读作"
                   "「被洗白的重影」而不是「已激活」；两态几何已由 G1 归一化到逐像素同位，"
                   "255 时该叠层**就是**这个按钮的悬停材质，语义直给且无重影）。"
                   "vis_flag=qbar_pin / vis_when=\"1\"。"
                   "★ 二选一说明（M37 报告）：**不**保留旧的引擎绘制高亮矩形（那是给「63 宽整条」设计的，"
                   "画在圆徽章上会露方形高亮）；**也不采用**「钉住时把常态 icon 用 vis_when 排除」的方案 —— "
                   "那要让 12 个 icon 各自多带一套互斥 vis_when（数据复杂度 +12 件），而 255 叠层在"
                   "同矩形下已经等价于「只画 `_on` 图」，故取更简的一种。"
                   "★ z=%d：低于热区（%d，不吃点击）高于 icon（%d，叠加可见）。"
                   "★ **visible_default 必须为 True**：判定语义「可见 ⟺ visible_default !== false 且 "
                   "flag 满足」下写 false 会让它**永远不可见**；取 True 时默认 "
                   "`flags_default.qbar_pin=\"\"` ≠ \"1\" ⇒ 默认仍不显示（同 M1 裁决）。"
                   % (lock_icon_x, lock_icon_y, QUICK_ICON, QUICK_ICON, QUICK_Z_PIN, QUICK_Z_HIT,
                      QUICK_Z_ICON)}
    els.append(vis(pin, "qbar_pin", "1"))

    # ── 12 项：key / 中文标签 / action（次序 = 纵向次序）────────────────
    #   ★ action 由派单契约指定（save/load = **打开**存/读档画面，另有 qsave/qload 两项才做快存快读）。
    ITEMS = [("lock", "锁定", "quick_pin"),
             ("save", "存档", "open_save"),
             ("load", "读档", "open_load"),
             ("qsave", "快速存档", "do_quicksave"),
             ("qload", "快速读档", "do_quickload"),
             ("auto", "自动播放", "auto_on"),
             ("skip", "快进", "skip_on"),
             ("next", "下一选项", "next_choice"),
             ("prev", "上一选项", "prev_choice"),
             ("log", "回想", "open_backlog"),
             ("chart", "流程图", "open_flowchart"),
             ("option", "设置", "open_config")]
    for i, (key, label, act) in enumerate(ITEMS):
        hy = QUICK_HIT_Y0 + i * QUICK_HIT_STEP
        ix = QUICK_HIT_X + (QUICK_HIT_W - QUICK_ICON) // 2
        iy = hy + (QUICK_HIT_H - QUICK_ICON) // 2
        # ★ P1：宽度一律由公式推出（唯一出处 = pill_w/pill_body_w），元素与文字框分开定位：
        #   元素含左右各 QUICK_PILL_GLOW 的透明外晕边；文字框 = **丸体矩形**（更窄）。
        pw = pill_w(label)                       # 元素宽 = 丸体宽 + 2×外晕
        body_w = pill_body_w(label)              # 丸体宽 = 字号×字数 + 2×内边距
        body_right = ix - QUICK_GAP              # 「药丸右缘 − icon 左缘 = QUICK_GAP」按**可见丸体**量
        body_left = body_right - body_w
        px = body_left - QUICK_PILL_MARGIN       # 元素左 = 丸体左 − (外晕 + 1px)
        py = iy                                  # 元素高 = 画布高 64 = icon 高 ⇒ 丸体自动居中于 icon
        py_body = py + (QUICK_PILL_H - QUICK_PILL_BODY_H) // 2   # 丸体顶（= iy + 10，与 P1 前同位）
        # ① 圆形 icon 徽章（仅展开态可见；组绑定 = 同 key 热区）
        els.append(vis(icon_elem(
            "quick.ic_%s" % key, key, ix, iy,
            "快捷条第 %d 项「%s」的**圆形 icon 徽章**（常态 `x_ui_qbicon_%s.png` / 悬停 "
            "`x_ui_qbicon_%s_on.png`，各 64×64 画布 / 圆径 56；素材由 G1 AI 直出）。"
            "圆心 = 该 key 热区矩形中心（热区 x%d y%d w%d h%d）——75/73 为奇数、画布 64 为偶数，"
            "整数像素无法精确对中，故**向下取整**（x=%d y=%d，与热区中心偏 (0.5,0.5) px，"
            "icon 仍完整落在热区内）；x 列与 y 行一律由生成器算出，**不在 TJS/JS 写死**。"
            "`state_group=quick.%s`：与同 key 热区**组绑定** ⇒ 指针落在 75×73 热区内的任何位置"
            "都点亮本徽章（不只是圆面上），左侧名称药丸也同步出现。"
            "z=%d（**低于热区 %d**：同组后悬停胜出者恒为热区，"
            "`test_state_targets.py` 的「中心胜出者须同组」因此成立；点击只认 hit/list，"
            "徽章不吃点击）。vis_flag=quickbar / vis_when=expanded。"
            % (i + 1, label, key, key, QUICK_HIT_X, hy, QUICK_HIT_W, QUICK_HIT_H,
               ix, iy, key, QUICK_Z_ICON, QUICK_Z_HIT)),
            "quickbar", "expanded"))
        # ② 名称药丸底 + ③ 白字（同 key，挂在 qbar_tip 上）
        els.append(vis(pill_elem(
            "quick.pl_%s" % key, key, px, py, pw,
            "「%s」名称药丸底（**程序化合成** `x_ui_qbtip_pill.png`：70×64 源，丸体 44 高居中、"
            "竖向渐变 + 1px 青蓝描边 + 约 3px 外晕；九宫格 %s **只横向拉伸**）。"
            "本元素 w=%d = 丸体宽 %d + 2×透明边 %d（外晕 3 + 1px 余量），其中丸体宽 = 字号 %d×%d字 + 2×内边距 %d"
            "（**按字数各自定宽**，2 字名不会顶着一个 4 字宽的药丸）。"
            "位置：**丸体右缘 = icon 左缘 − %d**（丸体右缘 x=%d = %d − %d），"
            "元素左 x=%d = 丸体左 − %d；元素 y=%d 与 icon 同顶（丸体自动居中于 icon）。"
            "素材配色（渐变 #6FA8E8→#3F6FB4 / 描边 #A0C9F7 / 青蓝外晕）**烘进 PNG，不新增色板键**。"
            "vis_flag=qbar_tip / vis_when=\"%s\"（= 鼠标悬停本项 key；收起态 tip 为空 ⇒ 不绘制）。"
            % (label, QUICK_PILL_NINE, pw, body_w, QUICK_PILL_MARGIN, QUICK_PILL_CHAR_EM, len(label),
               QUICK_PILL_PAD, QUICK_GAP, body_right, ix, QUICK_GAP, px, QUICK_PILL_MARGIN, py, key)),
            "qbar_tip", key))
        tx_el = txt("quick.tx_%s" % key, QUICK_Z_TX, body_left, py_body, body_w,
                    QUICK_PILL_BODY_H, label, QUICK_PILL_CHAR_EM,
                    "「%s」名称**白字**（引擎绘制；框 = 该 key **丸体**矩形 x%d y%d w%d h%d，"
                           "align=center / valign=middle）。字号 %d（= CJK 字宽 1em）："
                           "墨迹高 %d 与丸高 %d 之比 ≈55%%（旧版字号 28 为 61%%，用户判定「偏满」）；"
                           "墨迹宽 %d ≤ 丸体内区 %d（左右内边距各 %d，**天然对称**，"
                           "且 %d > 圆角半径 %d ⇒ 字不进圆角区）。"
                           "颜色 @palette.text_primary（#FFFFFF，白字压深蓝丸体，字带对比度 ≥4.9:1）。"
                           "vis_flag=qbar_tip / vis_when=\"%s\"（与药丸同 key ⇒ 同步显隐）。"
                           % (label, body_left, py_body, body_w, QUICK_PILL_BODY_H,
                              QUICK_PILL_CHAR_EM, QUICK_PILL_CHAR_EM, QUICK_PILL_BODY_H,
                              QUICK_PILL_CHAR_EM * len(label), body_w - 2 * QUICK_PILL_PAD,
                              QUICK_PILL_PAD, QUICK_PILL_PAD, QUICK_PILL_R, key),
                    align="center", color="@palette.text_primary")
        # ★ Q1：加深色描边（照参照做法：丸底为中等蓝，白字的可读性靠描边而非靠提亮底）
        tx_el["font"].update(QUICK_PILL_TEXT_OUTLINE)
        tx_el["note"] += ("　★ Q1：`outline`/%s 宽 %dpx（M38 的四向描边机制，"
                          "两端已实现、纯渲染不参与布局）——白字压中等蓝丸底，靠近黑藏青描边获得"
                          "「印刷标签」式的边缘锐度；底色保持 5.07:1 的对比余量不动。"
                          % (QUICK_PILL_TEXT_OUTLINE["outline_color"],
                             QUICK_PILL_TEXT_OUTLINE["outline_width"]))
        els.append(vis(tx_el, "qbar_tip", key))
        # ④ 热区（x/y/w/h/action **不变**；新增 state_group 以驱动图标与药丸）
        h = hit("quick.hit_%s" % key, QUICK_Z_HIT, QUICK_HIT_X, hy, QUICK_HIT_W, QUICK_HIT_H,
                act, "",
                "快捷条第 %d 项「%s」热区（PSB idx81 `#rects/%s`，x%d y%d w%d h%d —— "
                "几何**沿用 M34 的 1:1 复刻值，本轮不变**）。action=%s。"
                "★ M37 新增 `state_group=quick.%s`：热区退回纯热区（无态图），但**参与状态检测**"
                "（判据见 `uiScreenHoverAtIn`：「带非空 state_group 的 hit」），"
                "把悬停状态广播给同组的圆形徽章 ⇒ 悬停整块热区即点亮图标；"
                "左侧名称气泡的 key 也由本热区 id 推出（`uiScreenRevealTipAt` / `tipKeyAt`）。"
                "z=%d（最高；点击只认 hit/list ⇒ 点在徽章上仍派发本项动作）。"
                "vis_flag=quickbar / vis_when=expanded。"
                % (i + 1, label, key, QUICK_HIT_X, hy, QUICK_HIT_W, QUICK_HIT_H, act, key,
                   QUICK_Z_HIT))
        h["state_group"] = "quick.%s" % key
        els.append(vis(h, "quickbar", "expanded"))

    # ── 已退场：`quick.tgl` / `quick.btn` / `quick.tips` / `quick.hit_toggle` ──
    #   ★ M37：用户裁定「整条太丑」⇒ 整条带、slim 把手、高面板、整条把手热区**全部退场**
    #     （素材移入 `_工作\M37_旧素材归档\`，不删；旧 JSON 快照同目录）。
    #   ★ `open_sysmenu` 动作**保留**（Esc 已不用它；它仍是「展开竖条（不钉住）」的**编程入口**，
    #     语义见 ui_screens.tjs 的 uiQuickbarOpen()）。本轮**数据里不再有元素指向它** ⇒
    #     收起态在右端**没有任何可点热区**（点空＝剧情推进，符合用户「平时完全隐藏」的裁决）；
    #     展开的唯一鼠标入口＝指针移到 x ≥ reveal.in_x（贴右端）。
    write("35_quickbar.json", "quickbar", "系统菜单快捷条",
          (HEAD % 81) + "\n"
          "★ **V2 裁决（用户 2026-09-21）**：与右键 9 图标浮层（`sysicons`）**并存**，"
          "`sysicons` 屏与其素材保留不动。\n★ 本屏为**新增**。\n"
          "★ **M1（ISSUE-20260922-28）**：接线屏级 `flags_default`/`reveal` 与元素级 "
          "`vis_flag`/`vis_when`；12 项热区 `action` 由派单契约指定；新增 `quick.pin_mark`。\n"
          "★ **M37（ISSUE-20260923-01，用户裁定 2026-09-23）· 形态重构**：\n"
          "  · 退场四件：`quick.btn`（展开整条 63×888）/`quick.tgl`（slim 把手 63×513）/ "
          "`quick.tips`（高面板 197×876）/`quick.hit_toggle`（整条把手热区，曾 action=open_sysmenu）；"
          "  7 件旧素材**移入** `_工作\\M37_旧素材归档\\`（不删，含旧 JSON 快照）。\n"
          "  · 新增 12 个**圆形 icon 徽章** `quick.ic_<key>`（image 64×64 画布 / 圆径 56，"
          "`state_assets{normal,hover}`，`state_group=quick.<key>`）+ 12 个**名称药丸** "
          "`quick.pl_<key>`（image，九宫格 l=r=22/t=b=0，按字数各自定宽）+ 12 条白字 "
          "`quick.tx_<key>`（字号 28，颜色 @palette.text_primary）；12 个热区 `quick.hit_<key>` "
          "几何与 action **不变**，仅新增 `state_group` 以驱动图标/气泡同步。\n"
          "  · `quick.pin_mark` 由「引擎绘制矩形」改为**复用锁定 icon 悬停态图** "
          "（`x_ui_qbicon_lock_on.png` 叠加，**opacity 255**（L2 订正，原 200 会读作重影），z=93）。\n"
          "  · 「完全隐藏」由 flag 值实现：`collapsed` 时 12 icon + 12 药丸 + 12 文字全不绘制 ⇒ "
          "**收起态右端无任何可点热区**（整条把手退场）；展开入口 = 指针移到 x ≥ `reveal.in_x`。\n"
          "  · **机制侧未新增任何字段**：全部复用既有 `vis_flag`/`state_assets`/`state_group`/"
          "`qbar_tip`/`attach`（两端落点见 `layout/_schema.md` §四）。\n"
          "  · 素材：24 件 icon 由 G1 AI 直出（本轮为 G2 程序化占位件）；"
          "  · ★ **P1（2026-09-23）药丸重做**：vision 判定旧丸底（#3A5A9A×0.85 纯平实色 + 1px 浅边、"
          "无渐变/无外晕）与圆徽章「不是一套材质」⇒ 改为**竖向渐变 #6FA8E8→#3F6FB4 + 1px 描边 "
          "#A0C9F7 + 约 3px 青蓝外晕**（源画布 64 高、丸体居中，九宫格只横向拉伸）；"
          "**不新增色板键**（配色烘进 PNG；palette.json 未改）。\n"
          "  · ★ **Q1/Q2（2026-09-23，vision 非阻断精修）**：① 12 条白字加 **1px 深藏青描边**"
          "（`font.outline=true` / `#16305A` / 宽 1，用 M38 的既有机制，不动引擎）；"
          "② 丸体高 **44 → 40**（形态由「与徽章同重」收到「细标签」一档；纯丸体 40 / 徽章 54 = 0.74），"
          "字号 **24 → 21**（三标签墨高 21/22/21，最大 22 / 丸高 40 = 55%，参照 50%），"
          "宽度公式随之 `24n+60` → `21n+56`（内边距 24 不变、左右仍对称），九宫格端点 25 → 23。",
          els,
          extra={"flags_default": {"quickbar": "collapsed", "qbar_tip": "", "qbar_pin": ""},
                 "reveal": {"flag": "quickbar", "in_x": 1842, "out_x": 1780,
                            "delay_ms": 400, "tip_flag": "qbar_tip",
                            "pin_flag": "qbar_pin"}})


# ══════════════════════════════════════════════════════════════════════
# 74 确认框
# ══════════════════════════════════════════════════════════════════════
def build_confirm():
    els = []
    els.append(rect("cf.dim", 1, 0, 0, 1920, 1080, "@palette.backdrop", 120, "全屏压暗遮罩"))
    els.append(img("cf.panel", 10, "x_ui_confirm_panel.png", 610, 333, 697, 362,
                   "确认框面板（PSB idx74 `ダイアログ/base`，x610 y333 w697 h362）"))
    els.append(txt("cf.msg", 20, 612, 421, 693, 52, "要结束游戏吗？", 32,
                   "确认文案（引擎绘制；PSB 占位层 `#text` x612 y421 w693 h52）"))
    # ★ 用户 2026-09-21 裁定：「右边两个选项框明显大小不一致」。
    #   根因：PSB 的  是按**日文原文宽度**定的（はい 2 字 → 179 宽；いいえ 3 字 → 227 宽）。
    #   本作文字由引擎绘制、两键文案等长（是 / 否），故改为**等宽 + 以面板中心对称**。
    BW, BH, GAP = 203, 51, 70
    _cx = 610 + 697 / 2.0                       # 面板中心 958.5
    YES = (_cx - GAP / 2.0 - BW, 552, BW, BH)
    NO = (_cx + GAP / 2.0, 552, BW, BH)
    for eid, (x, y, w, h), label, act in (("cf.yes", YES, "是", "confirm_yes"),
                                          ("cf.no", NO, "否", "confirm_no")):
        els.append(img(eid, 20, "x_ui_btn_l_off.png", x, y, w, h,
                       "「%s」按钮底（PSB idx74 `#rect` x%d y%d w%d h%d；原作此二键的文字是**烘焙进 32×30 小图**的，"
                       "本作改为引擎绘字 + 通用按钮底）" % (label, x, y, w, h)))
        els.append(txt(eid + "_tx", 25, x, y, w, h, label, 28, "按钮文字（引擎绘制）"))
        els.append(hit("cf.hit_" + ("yes" if act == "confirm_yes" else "no"), 95, x, y, w, h, act, "",
                       "「%s」热区（action=%s；PSB `#rect` 同矩形）" % (label, act),
                       states={"normal": "ui/x_ui_btn_l_off.png", "hover": "ui/x_ui_btn_l_over.png",
                               "pressed": "ui/x_ui_btn_l_on.png"}))
    write("21_confirm.json", "confirm", "确认框", (HEAD % 74), els)


# ══════════════════════════════════════════════════════════════════════
# 83 选择支
# ══════════════════════════════════════════════════════════════════════
def build_choices():
    els = []
    els.append(img("ch.sel", 20, "x_ui_choice_off.png", 404, 470, 1113, 83,
                   "选择支条（PSB idx83 `選択肢/オフ`，条图 1113×83）。原作三条整图（オフ/オンマウス/無効）"
                   "同矩形，本作同法。**位置为暂定**：idx83 容器本身只有 1113×83，"
                   "**运行时摆放坐标不在 PSB 里**（见 `M34_交汇协奏曲UI布局规格.md` 待确认项）→ "
                   "此处按本作画布居中摆放（x404 = (1920-1113)/2，y470 居中），待编程组按选择支数量定位。"))
    for i, (label, act) in enumerate([("选项一", "select_choice"), ("选项二", "select_choice"),
                                      ("选项三", "select_choice")]):
        y = 470 + i * 100
        els.append(txt("ch.tx_%d" % (i + 1), 25, 404, y, 1113, 83, label, 34,
                       "选项文字（引擎绘制；真值取自资源组 `scene_*.jsonl` 的 `choices[].text_cn`）"))
        els.append(hit("ch.hit_%d" % (i + 1), 95, 404, y, 1113, 83, act, "",
                       "选项热区（index=%d）。**state_assets 三态整图**（原作即三态整条）" % i,
                       states={"normal": "ui/x_ui_choice_off.png", "hover": "ui/x_ui_choice_over.png",
                               "pressed": "ui/x_ui_choice_dis.png"}))
    write("36_choices.json", "choices", "选择支", (HEAD % 83) + "\n★ 本屏为**新增**。", els)



# ══════════════════════════════════════════════════════════════════════
# 76 立绘鉴赏 / 换装（V3 裁决：先做静态版式，数据由编程组接）
# ══════════════════════════════════════════════════════════════════════
def build_dress():
    els = []
    els.append(rect("dr.dim", 1, 0, 0, 1920, 1080, "@palette.backdrop", 70, "全屏压暗遮罩"))
    els.append(img("dr.top", 10, "x_ui_dress_top.png", 0, 69, 1920, 96,
                   "顶部标题条（PSB idx76 `caption`，x0 y69 w1920 h96）"))
    # 左栏角色名列表：条 x0 y184 w186 h641；12 行热区 x0 y181+60i w192 h47
    els.append(img("dr.namelist", 20, "x_ui_dress_name_off.png", 0, 184, 186, 641,
                   "角色名列表底（PSB idx76 `名前/オフ`，x0 y184 w186 h641）"))
    NAMES = ["八重垣 悟", "八重垣 瑠璃", "稲田 鏡花", "初芝 未来", "西ノ宮 透子", "西条 美加",
             "中野 綾", "初芝 香苗", "藤波 竜太", "土橋 健吾", "神凪 莉都", "（第 12 行）"]
    for i, nm in enumerate(NAMES):
        y = 181 + i * 60
        els.append(txt("dr.name_tx_%d" % (i + 1), 25, 0, y, 192, 47, nm, FONT_SMALL,
                       "角色名第 %d 行（引擎绘制）。**行几何取自 PSB `名前/#rect/%d`：x0 y%d w192 h47**"
                       "（step 60）。**V3 裁决：静态版式，真值由编程组接**。" % (i + 1, i, y), align="left"))
        els.append(hit("dr.hit_name_%d" % (i + 1), 95, 0, y, 192, 47, "", "",
                       "角色选择热区第 %d 行（action 留空待编程组定义）" % (i + 1)))
    # 顶部控制条 755×38 @ x34 y114 + 11 个控制热区
    els.append(img("dr.ctrl", 20, "x_ui_dress_ctrl_off.png", 34, 114, 755, 38,
                   "控制条（PSB idx76 `ボタン/コントロール/オフ`，x34 y114 w755 h38）"))
    CTRL = [("left", 24, 102, 56, 56, "左移"), ("bg", 88, 102, 68, 56, "背景"),
            ("right", 165, 102, 56, 56, "右移"), ("time", 229, 102, 56, 56, "时间"),
            ("text", 294, 102, 56, 56, "文本"), ("textwin", 358, 102, 103, 56, "文本窗"),
            ("capture", 469, 102, 61, 56, "截图"), ("save", 538, 102, 61, 56, "存档"),
            ("load", 607, 102, 61, 56, "读档"), ("hide", 676, 102, 56, 56, "隐藏"),
            ("help", 741, 102, 56, 56, "帮助")]
    for key, x, y, w, h, label in CTRL:
        els.append(hit("dr.hit_ctrl_%s" % key, 95, x, y, w, h, "", "",
                       "控制「%s」热区（PSB idx76 `コントロール/#rect/%s`，x%d y%d w%d h%d）。"
                       "action 留空待编程组定义。" % (label, key, x, y, w, h)))
    # 主按钮区（服装/姿势/差分/大小）
    els.append(img("dr.big", 15, "x_ui_dress_big_off.png", 288, 189, 672, 278,
                   "主操作区面板（PSB idx76 `ボタン/オフ`，x288 y189 w672 h278）"))
    TAG = [("服装", 288, 249, 113, 38, 1), ("時間用", 288, 189, 113, 38, 2),
           ("表情", 347, 493, 45, 22, 3), ("背景", 431, 554, 44, 22, 4)]
    for label, x, y, w, h, n in TAG:
        els.append(img("dr.tag_%s" % label, 20, "x_ui_dress_tag_%d.png" % n, x, y, w, h,
                       "「%s」标签底（PSB idx76 `%s`，x%d y%d w%d h%d）"
                       % (label, "服装" if label == "服装" else "表情用/背景用", x, y, w, h)))
        els.append(txt("dr.tag_tx_%s" % label, 25, x, y, w, h, label, FONT_SMALL,
                       "标签文字（引擎绘制）"))
    SMALL = [("keep", 277, 177, 131, 56, "保留"), ("hide", 418, 177, 131, 56, "隐藏"),
             ("dress0", 277, 237, 131, 56, "服装 1"), ("dress1", 418, 237, 131, 56, "服装 2"),
             ("dress2", 558, 237, 131, 56, "服装 3"), ("dress3", 699, 237, 131, 56, "服装 4"),
             ("dress4", 837, 237, 131, 56, "服装 5"),
             ("pose0", 277, 297, 56, 56, "姿势 1"), ("pose1", 342, 297, 56, 56, "姿势 2"),
             ("pose2", 406, 297, 56, 56, "姿势 3"),
             ("diff0", 277, 357, 56, 56, "差分 1"), ("diff1", 342, 357, 56, 56, "差分 2"),
             ("diff3", 406, 357, 56, 56, "差分 3"),
             ("level0", 277, 417, 56, 56, "大小 S"), ("level1", 342, 417, 56, 56, "大小 M"),
             ("level2", 408, 417, 56, 56, "大小 L"), ("faceright", 218, 488, 53, 30, "表情右")]
    for key, x, y, w, h, label in SMALL:
        els.append(img("dr.btn_%s" % key, 20, "x_ui_sqkey_s_off.png", x, y, w, h,
                       "「%s」按钮底（PSB idx76 `#rect/%s`，x%d y%d w%d h%d）" % (label, key, x, y, w, h)))
        els.append(txt("dr.btn_tx_%s" % key, 25, x, y, w, h, label, 20, "按钮文字（引擎绘制）"))
        els.append(hit("dr.hit_%s" % key, 95, x, y, w, h, "", "", "「%s」热区（action 留空）" % label))
    # 时间图标（昼/夕/夜/夜2）
    for key, art, x, y, w, h, label in [("day", "day", 243, 115, 29, 29, "昼"),
                                        ("dusk", "dawn", 243, 121, 29, 16, "夕"),
                                        ("night", "night", 243, 117, 26, 26, "夜"),
                                        ("night2", "star", 244, 117, 26, 26, "夜 2")]:
        els.append(img("dr.time_%s" % key, 20, "x_ui_time_%s.png" % art, x, y, w, h,
                       "时间图标「%s」（PSB idx76 `時間/%s`，x%d y%d w%d h%d）" % (label, label, x, y, w, h)))
    els.append(img("dr.reset", 20, "x_ui_reset_off.png", 1264, 44, 78, 25,
                   "「初始化」键（PSB idx76 `reset/オフ`，x1264 y44 w78 h25）"))
    els.append(txt("dr.reset_tx", 25, 1264, 44, 78, 25, "初始化", 20, "按钮文字（引擎绘制）"))
    els.append(hit("dr.hit_reset", 95, 1264, 44, 78, 25, "", "", "「初始化」热区（action 留空）",
                   states={"normal": "ui/x_ui_reset_off.png", "hover": "ui/x_ui_reset_over.png",
                           "pressed": "ui/x_ui_reset_on.png"}))
    els.append(hit("dr.hit_back", 96, 0, 1038, 1317, 42, "close", "返回",
                   "底部返回热区（PSB idx76 `#helptip`，x0 y1038 w1317 h42）"))
    write("37_dress.json", "dress", "立绘鉴赏/换装",
          (HEAD % 76) + "\n★ **V3 裁决（用户 2026-09-21）**：**先做静态版式，数据由编程组接** —— "
                        "槽位留空、不塞示例数据；本轮无法目视验证「换装」真实效果（如实登记）。\n"
                        "★ 本屏为**新增**。", els)


# ══════════════════════════════════════════════════════════════════════
# 73 回想（バックログ）★ M49（2026-09-24，主代理裁决 A）：**build_backlog() 已退休删除**
#   Issue ISSUE-20260924-06（用户指令：渲染 4 行 + 重新排版 + 每块加「跳转」「重新播放」）。
#   · 退休依据：本屏自 M35b 起即为**手工维护**（`state_assets` 从 hit 挪到 image + `state_group` 组绑定，
#     早已登记在 `工具\test_gen_sync.py` 的 `ACK_UNSYNC`）；本轮又是「4 行 + 逐块按钮」的**结构性重排**
#     （`max_rows` / `item_h` / `item_text` / `item_buttons` / 底板九宫格 t/b），几何还会随容量实测微调。
#     ⇒ 回写生成器的收益远小于「两个真相源互踩」的风险。
#   · 先例：M45 `build_sysmenu` / M46 `build_sysbar` / **M47 `build_config`（同一个本文件里退休）**。
#   · 处置：函数与 `__main__` 调用一并删除；`26_backlog.json` 归入 `test_gen_sync.py` 的 `NO_GEN`；
#     `ACK_UNSYNC` 的 26 条目删除（不再有「重跑即抹」的对象）。
#   · **后果（明文登记）**：本屏**不再能被整屏重生成**；此后一切改动都在
#     `layout\screens\26_backlog.json` 上手工进行（首版由一次性脚手架
#     `_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_build_backlog.py` 产出）。
#   · 数据源与素材不动：块底板 `ui/x_ui_msgblock.png`、跳跃键 `ui/x_ui_jump_*`、
#     重播键**新件** `ui/x_ui_spk2_*`（44×44，`工具\m49_make_backlog_assets.py`；旧件 `x_ui_spk_*` 保留不删）。
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 82 存档 / 读档
# ══════════════════════════════════════════════════════════════════════
def build_saveload(sid, title, tab_on, tab_off):
    els = [rect("sv.dim", 1, 0, 0, 1920, 1080, "@palette.backdrop", 70, "全屏压暗遮罩")]
    # 页签（PSB `#rects/save` (25,24,181,60) / `#rects/load` (211,24,181,60)）
    for eid, x, label, act in (("sv.tab_a", 25, tab_on, "open_save"), ("sv.tab_b", 211, tab_off, "open_load")):
        art = "on" if label == tab_on else "off"
        els.append(img(eid, 10, "x_ui_tab_%s.png" % art, x, 24, 181, 60,
                       "页签「%s」（PSB idx82 `#rects/%s` x%d y24 w181 h60）"
                       % (label, "save" if x == 25 else "load", x)))
        els.append(txt(eid + "_tx", 20, x, 24, 181, 60, label, FONT_TAG, "页签名（引擎绘制）"))
        els.append(hit(eid + "_hit", 95, x, 24, 181, 60, act, "", "页签热区（action=%s）" % act))
    # 槽位网格：PSB `代表/#rect` (121,192,256,345) 与 `データ/#step` (406,549,256,345)
    #   → 列距 285、行距 357 ⇒ 6 列 × 2 行 = 每页 12 槽
    CW, CH, CX, CY, DX, DY = 256, 345, 121, 192, 285, 357
    for r in range(2):
        for c in range(6):
            n = r * 6 + c + 1
            x, y = CX + c * DX, CY + r * DY
            els.append(img("sv.slot%d" % n, 20, "x_ui_slot_empty.png", x, y, CW, CH,
                           "槽位 %d 空态（PSB idx82 `代表/#rect` 256×345，列距 285 / 行距 357）" % n))
            els.append(img("sv.thumb%d" % n, 21, "x_ui_slot_thumb.png", x + 18, y + 43, 217, 122,
                           "槽位 %d 缩略图框（PSB `代表/サムネイル` 217×122 @(+18,+43)）" % n))
            els.append(txt("sv.num%d" % n, 25, x + 18, y + 10, 217, 31, "第 %d 号" % n, 22,
                           "槽位号（引擎绘制；PSB `item/number` 121×31）", align="left"))
            els.append(txt("sv.info%d" % n, 25, x + 18, y + 169, 217, 120,
                           "2026-09-21 04:30\n第 1 章 前奏诗", 20,
                           "槽位信息（引擎绘制；PSB `item/text` 217×94 + `item/date` 217×26）",
                           align="left", valign="top", wrap=True, max_lines=3))
            els.append(hit("sv.hit%d" % n, 95, x, y, CW, CH, "slot_%d" % n, "", "槽位 %d 热区" % n))
    # 页码 01–10（PSB x120+90i，y933/939，53×53 / on 65×65）
    for i in range(10):
        x = 120 + i * 90
        els.append(img("sv.pg%02d" % (i + 1), 20, "x_ui_pg_off.png", x, 939, 53, 53,
                       "页码键 %02d（PSB idx82 `ボタン/オフ/%02d` x%d y939 w53 h53）" % (i + 1, i + 1, x)))
        els.append(txt("sv.pg%02d_tx" % (i + 1), 25, x, 939, 53, 53, str(i + 1), 22,
                       "页码（引擎绘制）"))
        els.append(hit("sv.pg%02d_hit" % (i + 1), 95, x, 939, 53, 53, "page_%d" % (i + 1), "",
                       "页码热区（PSB `ボタン/オン/%02d` 65×65 @ y933）" % (i + 1)))
    # 编辑条 + 4 个编辑热区（PSB `エディット` 684×49 @(1089,970)）
    els.append(img("sv.edit", 20, "x_ui_edit_off.png", 1089, 970, 684, 49,
                   "编辑条（PSB idx82 `エディット/オフ` x1089 y970 w684 h49）"))
    for eid, x, label in (("sv.del", 1083, "删除"), ("sv.mod", 1263, "编辑"),
                          ("sv.mov", 1443, "移动"), ("sv.cpy", 1623, "复制")):
        els.append(txt(eid + "_tx", 25, x, 964, 156, 61, label, 22, "编辑键文字（引擎绘制）"))
        # ★ G1 修复（主代理 2026-09-22 一审打回 · 同类不可达缺陷）：z 95 → 97。
        #   缺陷：`sv.hit_back`（x1560 y960 w320 h68, **z=96**）矩形覆盖本行右段 ——
        #     逐像素复算：`sv.cpy`（1623,964,156×61）**9516/9516 点全被 sv.hit_back 吃掉**
        #     （其 action="close"）⇒ 点「复制」直接关掉存档/读档屏；`sv.mov` 也被吃掉 2379/9516。
        #   修法（**选「更具体的子控件赢」，raise z**）：本行 4 件是 PSB `エディット/#删除|#编辑|#移动|#复制`
        #     的**精确交互矩形**（各 156×61），而 `sv.hit_back` 是一条**无对应美术**的宽热区
        #     （320 宽；该区域只有 sv.edit 编辑条美术 1089..1773，右侧并无「返回」图案），
        #     故按「具体控件优先」把 4 件提到 97（新增一档，屏内原只有 95/96 两档，不冲突）。
        #   ★ 为何不选「收窄 hit_back」：它的意图范围无从由美术推出（无 返回 图案可量），
        #     收窄等于凭空决定「返回」按钮在哪、并把它让出的区域变成死区；抬 z 则完整保留
        #     hit_back 在 4 件矩形之外的全部区域。
        els.append(hit(eid, 97, x, 964, 156, 61, "", "",
                       "「%s」热区（PSB `エディット/#%s` 156×61）。★ M1/G1 修复（2026-09-22）："
                       "z 95→97 —— 本件原被 `sv.hit_back`(x1560 y960 w320 h68, z=96) 完整/部分覆盖"
                       "（`sv.cpy` 9516/9516 点全归它、`sv.mov` 2379 点归它），点「复制」会误触发"
                       "action=\"close\" 关屏；按「更具体的子控件赢」提到 97。" % (label, label)))
    # 系统共通按钮（PSB 三键 off 态）
    for eid, x, w, label in (("sv.sys_game", 1282, 105, "返回游戏"),
                             ("sv.sys_title", 1476, 159, "返回标题画面"),
                             ("sv.sys_end", 1723, 105, "退出游戏")):
        els.append(img(eid, 20, "x_ui_btn_m_off.png", x, 44, w, 25,
                       "系统共通键「%s」（PSB idx82 `システム共通/オフ` x%d y44 w%d h25）" % (label, x, w)))
        els.append(txt(eid + "_tx", 25, x, 44, w, 25, label, 18, "按钮文字（引擎绘制）"))
        els.append(hit(eid + "_hit", 95, x - 8, 36, w + 16, 41, "", "", "「%s」热区" % label))
    # 说明条
    els.append(img("sv.help", 20, "x_ui_btn_l_off.png", 1186, 907, 488, 45,
                   "说明条（PSB idx82 `セーブロード/help` x1186 y907 w488 h45）"))
    els.append(txt("sv.help_tx", 25, 1186, 907, 488, 45, "选择槽位后按编辑键可管理存档", 20,
                   "说明文字（引擎绘制）"))
    els.append(hit("sv.hit_back", 96, 1560, 960, 320, 68, "close", "返回", "返回热区"))
    write("2%d_%s.json" % (3 if sid == "save" else 4, sid), sid, title, (HEAD % 82), els)


# ══════════════════════════════════════════════════════════════════════
# 80 配置・设定（Config）
# ══════════════════════════════════════════════════════════════════════
# ----------------------------------------------------------------------
# ★ M1（2026-09-22）· **M35b 手工迁移回写**（M1 代录，逐字照抄当时磁盘数据）
#   M35b 曾把「静音 / 试听」两行的三态图从 hit 迁到同矩形的 image，并加 state_group 联动，
#   但那批改动**只改了 25_config.json、没回写本生成器** ⇒ 该屏一度无法由生成器复现
#   （M1 一审前实测：磁盘与生成器输出差 4 件 × 3 字段）。M1 把当时的字段逐字录回本表，
#   使生成器重新成为唯一数据源，从而 G2 的 z 修复能够以「重跑生成器」的方式落地。
#   表值 = 该元素的**最终** `state_group` / `state_assets` / `note`（note 为全文，整串替换）。
#   M35b / M8 若要改写这段，请直接改本表或改上面的创建处并删除本表 —— 二者不要并存。
# ----------------------------------------------------------------------
M35B_OVERRIDES = {
    'cfg.mute_hit': {
        "state_group": 'config.mute',
        "state_assets": None,
        "note_append": '静音热区（PSB `mute/#範囲`）\u3000★ M34 互斥态分组：属「声音」页签，默认隐藏（运行时由编程组按页签切换）。 ★ M35b：**退回纯热区**（不再持有美术，避免按热区矩形拉伸绘制）；三态图改由同矩形的 image `cfg.mute_off` 绘制，两者 state_group「config.mute」联动。  ★ M35b 二审核查（**未改动本元素数据**）：曾有审查意见认为本件会抢走静音勾选框的悬停命中、使 `cfg.mute_off` 的按下态画不出来。实测**不成立** —— 本件与 `cfg.mute_lb`、`cfg.mute_off` 三者的 `visible_default` **都是 false**（M34 把整行关掉了，本屏 121 件里 35 件如此：五组滑条 + 静音行 + 试听行），因此那里本就没有可亮的东西。真正的加固在引擎侧：判据已收紧为「带非空 state_group 的 hit」（见 ui_screens.tjs 的 uiScreenHoverAt），使「声明更晚的无组热区抢走有组热区」这一类**不再可能**。',
    },
    'cfg.mute_off': {
        "state_group": 'config.mute',
        "state_assets": {'normal': 'ui/x_ui_check_off.png', 'hover': 'ui/x_ui_check_off.png', 'pressed': 'ui/x_ui_check_on.png'},
        "note_append": "静音勾选框（PSB `mute/オフ` x843 y318 w21 h21）（素材 19×21 ≠ 设计 21×21 → nine {'l': 4, 't': 5, 'r': 4, 'b': 5}）\u3000★ M34 互斥态分组：属「声音」页签，默认隐藏（运行时由编程组按页签切换）。 ★ M35b：接收原热区 `cfg.mute_hit` 的三态图（热区矩形是 PSB 的交互区，比美术大得多，由热区画会拉伸涂抹）——美术在 1:1/九宫格口径下画，与热区用 state_group「config.mute」联动。",
    },
    'cfg.replay_hit': {
        "state_group": 'config.replay',
        "state_assets": None,
        "note_append": '试听热区（PSB `再生/#範囲`）\u3000★ M34 互斥态分组：属「声音」页签，默认隐藏（运行时由编程组按页签切换）。 ★ M35b：**退回纯热区**（不再持有美术，避免按热区矩形拉伸绘制）；三态图改由同矩形的 image `cfg.replay` 绘制，两者 state_group「config.replay」联动。',
    },
    'cfg.replay': {
        "state_group": 'config.replay',
        "state_assets": {'normal': 'ui/x_ui_replay_off.png', 'hover': 'ui/x_ui_replay_off.png', 'pressed': 'ui/x_ui_replay_on.png'},
        "note_append": "试听键（PSB `再生/オフ` x196 y315 w22 h32）（素材 22×24 ≠ 设计 22×32 → nine {'l': 5, 't': 6, 'r': 5, 'b': 6}）\u3000★ M34 互斥态分组：属「声音」页签，默认隐藏（运行时由编程组按页签切换）。 ★ M35b：接收原热区 `cfg.replay_hit` 的三态图（热区矩形是 PSB 的交互区，比美术大得多，由热区画会拉伸涂抹）——美术在 1:1/九宫格口径下画，与热区用 state_group「config.replay」联动。",
    },
}

# ══════════════════════════════════════════════════════════════════════
# ★ M47（2026-09-24）：`build_config()` **已退休并删除**（连同其 M1_G2_Z_FIX 表）。
#   新设置屏（25_config.json）由 _工作\M47_设置屏重设\复现脚本\m47_build_config.py
#   一次性产出，此后**手工维护**（用户会在编辑器里微调）⇒ 不能再由生成器重建，
#   否则重跑会静默回退手改（M41 教训）。同 M45 删 build_sysmenu / M46 删 build_sysbar 的处置。
#   配套：test_gen_sync.py 的 GENERATORS 条目已同步移除 ⇒ 该屏判 NO_GEN（无「重跑即抹」风险）。
# ══════════════════════════════════════════════════════════════════════




# ══════════════════════════════════════════════════════════════════════
# ★ M51（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`build_music()` **已退休并删除**。
#   新 BGM 鉴赏页（`28_music.json`）由
#   `_工作\ISSUE-20260924-08_鉴赏模式\M3_BGM\m51_build_music.py` **一次性**产出，
#   此后**手工维护**。理由：本屏是**结构性重绘** —— 30 件静态曲目行（旧版 `mu.row1..30`
#   各带 `_tx`/`_hit`，翻页即散）改为 **1 个二维网格 `list`**（`orientation:"h"` +
#   `max_cols`×`max_rows`，M1 于本 issue 实现的机制）+ 逐项 `item_buttons` 播放键 +
#   逐项三态 `item_frame` + 音量 `slider` + 翻页键；用户 2026-09-24 明确要求
#   「按参考结构重绘、**必须标准化**」⇒ 回写生成器收益 < 两真相源互踩的风险。
#   同 M45 删 `build_sysmenu` / M46 删 `build_sysbar` / M47 删 `build_config` /
#   M49 删 `build_backlog` 的处置。
#   配套：`test_gen_sync.py` 的 `GENERATORS` 条目已同步移除 ⇒ 该屏判 `NO_GEN`
#   （无 build 函数 ⇒ 不存在「重跑即抹」风险）。
#   **后果明文登记：本屏不再能被整屏重生成**；改动只改 `layout\screens\28_music.json`。
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 77 剧情流程图（フローチャート）
# ══════════════════════════════════════════════════════════════════════
def build_flowchart():
    els = [rect("fc.dim", 1, 0, 0, 1920, 1080, "@palette.backdrop", 60, "全屏压暗遮罩")]
    # 顶部页签（PSB `modetabs/1|2|3` 的 `p0/p1/p2/frg`，on 态坐标）
    MT = [("序章", 34, 33, 179), ("本篇", 304, 33, 157), ("After Story", 559, 33, 236),
          ("Fragment", 859, 33, 193)]
    for i, (label, x, y, w) in enumerate(MT):
        els.append(img("fc.mtab%d" % (i + 1), 10, "x_ui_ftab_%s.png" % ("on" if i == 0 else "off"),
                       x, y, w, 44, "模式页签 %d「%s」（PSB `modetabs/%d` x%d y%d w%d h44）"
                       % (i + 1, label, (i % 3) + 1, x, y, w)))
        els.append(txt("fc.mtab%d_tx" % (i + 1), 20, x, y, w, 44, label, FONT_SMALL,
                       "页签名（引擎绘制）"))
        els.append(hit("fc.mtab%d_hit" % (i + 1), 95, x, y, w, 44, "", "", "页签热区"))
    # 标题牌（PSB `フローチャート/Flowchart` 385×68 @(58,93)）
    els.append(img("fc.titleplate", 10, "x_ui_dress_top.png", 58, 93, 385, 68,
                   "标题牌（PSB `フローチャート/Flowchart` x58 y93 w385 h68）"))
    els.append(txt("fc.title", 11, 58, 93, 385, 68, "剧情流程图", FONT_TAG, "屏标题（引擎绘制）"))
    # 左侧滚动视口（PSB `#rects/scroll` x60 y190 w1235 h827）
    els.append(rect("fc.scroll", 5, 60, 190, 1235, 827, "@palette.panel_edge", 40,
                    "流程图滚动视口底（PSB `#rects/scroll` x60 y190 w1235 h827；程序化 rect）"))
    # 节点演示（PSB `blocks` 系：节点块 296×65、标签 333×38、分支 65×65、分隔条 1233×2）
    els.append(img("fc.sep", 20, "x_ui_label_off.png", 60, 286, 1233, 2,
                   "章分隔条（PSB `blocks/separator/@separator/lay` 1233×2 @(60,286)）"))
    for i, (eid, art, label) in enumerate([("fc.n_section", "node_section_off", "章节点"),
                                           ("fc.n_select", "node_select_off", "选择支节点"),
                                           ("fc.n_extra", "node_extra_off", "番外节点")]):
        y = 330 + i * 90
        a = "node_frag_off" if art == "node_extra_off" else art
        els.append(img(eid, 20, "x_ui_%s.png" % a, 550, y, 296, 65,
                       "%s（PSB `blocks/*/off` 296×65 @(550,%d)）" % (label, y)))
        els.append(txt(eid + "_tx", 25, 550, y, 296, 65, label, 22, "节点标签（引擎绘制）"))
        els.append(hit(eid + "_hit", 95, 550, y, 296, 65, "", "", "%s热区" % label))
    els.append(img("fc.label", 20, "x_ui_label_off.png", 531, 549, 333, 38,
                   "关联标签块（PSB `blocks/label/label` x531 y549 w333 h38）"))
    els.append(txt("fc.label_tx", 25, 531, 549, 333, 38, "关联标签", 20, "标签文字（引擎绘制）"))
    els.append(img("fc.branch", 20, "x_ui_branch_s.png", 666, 501, 65, 65,
                   "分支底座（PSB `blocks/branch` x666 y501 w65 h65）"))
    els.append(img("fc.newmark", 21, "x_ui_lock_s.png", 552, 483, 50, 17,
                   "NEW 标记（PSB `blocks/fragment/NEW` x552 y483 w50 h17）"))
    # 右侧信息面板（PSB `#rects` 逐字）
    PANEL = [("title", "标题", 1416, 214, 443, 73), ("text", "说明", 1425, 309, 422, 171),
             ("player", "场景回放", 1423, 495, 424, 237), ("message", "台词", 1425, 750, 422, 171)]
    for key, label, x, y, w, h in PANEL:
        els.append(rect("fc.p_%s" % key, 6, x, y, w, h, "@palette.panel_edge", 35,
                        "右栏「%s」视口底（PSB `#rects/%s` x%d y%d w%d h%d；程序化 rect）"
                        % (label, key, x, y, w, h)))
        els.append(txt("fc.p_%s_tx" % key, 25, x + 12, y + 10, w - 24, 40, label, FONT_SMALL,
                       "「%s」标签（引擎绘制）" % label, align="left"))
    # 迷你地图（PSB `#rects/smallmap` x1416 y190 w443 h829）
    els.append(rect("fc.smallmap", 5, 1416, 190, 443, 829, "@palette.panel_edge", 40,
                    "缩略总览（minimap）底（PSB `#rects/smallmap` x1416 y190 w443 h829）"))
    for i in range(8):
        els.append(rect("fc.mini%d" % (i + 1), 20, 1450 + (i % 2) * 200, 240 + (i // 2) * 150, 150, 70,
                        "@palette.node_available", 180, "缩略图节点块（程序化 rect）"))
    els.append(rect("fc.mapview", 21, 1440, 225, 380, 300, "@palette.accent", 60,
                    "缩略图可视区框（程序化 rect）"))
    # 滚动条（PSB `ボタン/上|下` + `スライダー`）
    for eid, art, x, y, w, h, label in [("fc.scr_up", "arrow_up", 1321, 190, 31, 31, "上"),
                                        ("fc.scr_knob", "scroll_knob", 1321, 556, 31, 73, "滑块"),
                                        ("fc.scr_dn", "arrow_down", 1321, 987, 31, 30, "下")]:
        els.append(img(eid, 20, "x_ui_%s.png" % art, x, y, w, h,
                       "滚动%s（PSB `ボタン/%s` x%d y%d w%d h%d）" % (label, label, x, y, w, h)))
    els.append(rect("fc.scr_rail", 19, 1321, 221, 31, 766, "@palette.letterbox", 140,
                    "滚动条轨（PSB `フローチャート/スクロールバー` 31×767）"))
    # 缩放条（PSB `zoom`）
    els.append(img("fc.zoom_rail", 20, "x_ui_zoom_rail.png", 1047, 112, 270, 31,
                   "缩放条轨（PSB `zoom/rail` x1047 y112 w270 h31）"))
    els.append(img("fc.zoom_knob", 21, "x_ui_zoom_knob.png", 1174, 112, 40, 31,
                   "缩放条滑块（PSB `zoom/slider` x1174 y112 w40 h31）"))
    els.append(img("fc.zoom_minus", 20, "x_ui_arrow_left.png", 1006, 123, 29, 8,
                   "缩放「－」（PSB `zoom/オフ/－` x1006 y123 w29 h8）"))
    els.append(img("fc.zoom_plus", 20, "x_ui_arrow_right.png", 1321, 112, 29, 29,
                   "缩放「＋」（PSB `zoom/オフ/＋` x1321 y112 w29 h29）"))
    # 平移条（PSB `shift`）
    els.append(img("fc.shift_rail", 20, "x_ui_shift_rail.png", 130, 1018, 1094, 25,
                   "平移条轨（PSB `shift/rail` x130 y1018 w1094 h25）"))
    els.append(img("fc.shift_knob", 21, "x_ui_shift_knob.png", 466, 1018, 73, 25,
                   "平移条滑块（PSB `shift/slider` x466 y1018 w73 h25）"))
    els.append(img("fc.shift_lf", 20, "x_ui_arrow_left.png", 100, 1018, 31, 25,
                   "平移「左」（PSB `shift/ボタン/オフ/左` x100 y1018 w31 h25）"))
    els.append(img("fc.shift_rg", 20, "x_ui_arrow_right.png", 1224, 1018, 30, 25,
                   "平移「右」（PSB `shift/ボタン/オフ/右` x1224 y1018 w30 h25）"))
    # 读取剧情 / 备注键 / 场景回放 / 关闭
    els.append(img("fc.jump", 20, "x_ui_jumpfc_off.png", 1474, 943, 328, 61,
                   "「读取剧情」键（PSB `ボタン/オフ/シナリオを読み込む` x1474 y943 w328 h61）"))
    els.append(txt("fc.jump_tx", 25, 1474, 943, 328, 61, "读取剧情", FONT_TAG, "按钮文字（引擎绘制）"))
    els.append(hit("fc.jump_hit", 95, 1474, 943, 328, 61, "", "", "读取剧情热区"))
    for eid, x, label in (("fc.fusen_edit", 499, "编辑备注"), ("fc.fusen_reset", 679, "备注初始化")):
        els.append(img(eid, 20, "x_ui_fusen_off.png", x, 99, 145, 48,
                       "「%s」键（PSB `fusen/オフ/%s` x%d y99 w145 h48）" % (label, label, x)))
        els.append(txt(eid + "_tx", 25, x, 99, 145, 48, label, 20, "按钮文字（引擎绘制）"))
        els.append(hit(eid + "_hit", 95, x, 99, 145, 48, "", "", "「%s」热区" % label))
    # ★ 互斥态分组：右栏「场景回放」视口与 minimap 区域重叠（原作按模式互斥）→ 默认隐藏
    for e in els:
        if e["id"] in ("fc.p_player", "fc.p_player_tx"):
            e["visible_default"] = False
            e["note"] = (e.get("note") or "") + "　★ M34 互斥态分组：与 minimap 重叠，默认隐藏。"
    els.append(img("fc.pbkick", 20, "x_ui_branch_l.png", 1576, 555, 119, 119,
                   "场景回放键（PSB `pbkick/@pbkick:n:off` x1576 y555 w119 h119）"))
    els.append(hit("fc.pbkick_hit", 95, 1573, 552, 125, 125, "", "", "场景回放热区"))
    els.append(img("fc.close", 20, "x_ui_close_off.png", 1843, 177, 26, 26,
                   "关闭键（PSB `close/off` x1843 y177 w26 h26）"))
    els.append(hit("fc.close_hit", 95, 1830, 159, 56, 56, "close", "", "关闭热区（PSB `close/#rect`）",
                   states={"normal": "ui/x_ui_close_off.png", "hover": "ui/x_ui_close_over.png",
                           "pressed": "ui/x_ui_close_on.png"}))
    els.append(img("fc.sysbar", 20, "x_ui_sysbar.png", 1227, 32, 648, 41,
                   "系统共通条（PSB `システム共通` x1227 y32 w648 h41）"))
    write("32_flowchart.json", "flowchart", "剧情流程图", (HEAD % 77), els)


if __name__ == "__main__":
    build_title()
    # ★ M46（2026-09-23，用户裁定）：`build_sysbar()` 调用**已删除** —— `sysbar` 屏已整体删除
    #   （屏文件 / `_index.json` 条目 / 巡演白名单 / 两端活引用全清；素材保留不删）。详见本文件 §78 注。
    build_quickbar()
    build_confirm()
    build_choices()
    # ★ M8（2026-09-24 · ISSUE-20260924-08_鉴赏模式 · 一审 R1）：`build_dress()` 调用**已删除（退接线）** ——
    #   37_dress 改为**手工维护**（M4 已结构性对齐、M8 一审/vision 又重排 38 件：删 10 件叠印/白带/重影、
    #   人名 x34、单字符小方块 + chstate 行标签、初始化放大；函数体**保留**在 §69，删除动作留主代理裁决）。
    #   **后果：`python m34_build_screens.py` 整跑不再产出 37_dress.json**（重跑会抹掉手工改动的风险已消除）；
    #   改动只改 `layout\screens\37_dress.json`。先例：M45 build_sysmenu / M46 build_sysbar /
    #   M47 build_config / M49 build_backlog / **M51 build_music（同文件同款处置）**。
    #   配套：`test_gen_sync.py` 的 SUPERSEDED / NO_GEN 登记文案已同步订正。
    # build_dress()
    # ★ M49（2026-09-24，主代理裁决 A）：`build_backlog()` 调用**已删除** —— 该屏改为**手工维护**
    #   （本屏自 M35b 起已手工维护，本轮「4 行 + 逐块按钮」结构性重排后更不可能回写；
    #   先例 M45 build_sysmenu / M46 build_sysbar / M47 build_config）。详见本文件 §73 注。
    #   **后果：本屏不再能被整屏重生成**；改动只改 `layout\screens\26_backlog.json`。
    build_saveload("save", "存档", "存档", "读档")
    build_saveload("load", "读档", "读档", "存档")
    # ★ M51（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`build_music()` 调用**已删除** ——
    #   该屏改为**手工维护**（首版由 M3 的一次性脚手架产出）。详见本文件 §75 注。
    #   **后果：本屏不再能被整屏重生成**；改动只改 `layout\screens\28_music.json`。
    build_flowchart()
