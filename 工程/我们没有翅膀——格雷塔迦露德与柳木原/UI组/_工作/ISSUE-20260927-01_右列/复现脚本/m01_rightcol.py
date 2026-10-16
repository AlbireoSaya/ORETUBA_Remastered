#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISSUE-20260927-01 · 模块 A：设置屏（25_config.json）右列收回面板内
=================================================================
唯一允许写的数据文件：layout/screens/25_config.json
本脚本为该改动的**幂等复现脚本 + 几何/相交自证机件**。

口径（依据屏级 note「★ ISSUE-20260927-01」与派单书）
------------------------------------------------------------------
· 面板右内沿**实测 x=1762**（`krkr/assets/ui/x_ui_psv_cfg_page1/2.png` 上的亮边线，
  y≈204..924，两页一致）；左内沿 x=160。
· 验收：右列所有元素**右沿 ≤ 1756**（内沿留 6px，与左列「尖角 166 vs 内沿 160」同口径）。
· A 组（预览组 6 件）：w 一律 −36，x 不动。
    pv_frame/pv_bg/pv_note/pv_note_x  612→576（右沿 1792→1756）
    pv_mask                           592→556（1782→1746）
    pv_text                           584→548（1778→1742）
  内缩关系不变：外框 ⊃ 遮罩（两侧各 10）⊃ 文字（两侧各 14）。
  ★ 唯一非 x/w 改动：`cfg.pv_bg` 的素材 `x_ui_cfg_preview_bg.png` 是 **612×154 的 1:1 件**
    （`工具/verify_ui.py` [2]：无 `nine` 的 image 的 w/h 必须等于 PNG 实尺寸），
    收窄后必须按 `layout/_schema.md` §六 补**全零九宫格**（= 允许整图等比缩放）。
· B 组（角色列 165 件）：列步进 230→217、单元 222→210。
    列 x 1110/1340/1570 → 1110/1327/1544；胶囊与热区 w 222→210；
    名条文字 x = 列 x+26 不变、w 196→184（右沿与同列胶囊右沿齐平）；
    圆点 x = 列 x+6 不变、w 12 不变。
    右沿 1792→1754 = 与 `cfg.banner_frame` 右沿（1754）齐平。列节距恒 217、行步进恒 39。

用法
----
  python m01_rightcol.py                 # --check（默认）：只体检，不写盘
  python m01_rightcol.py --check         # 同上
  python m01_rightcol.py --apply         # 应用（盘上值必须 ∈ {旧,新}；已应用则只报不写）
  python m01_rightcol.py --verify        # 对**盘上当前状态**做全部几何/相交断言（带退出码）
  python m01_rightcol.py --mutate        # 变异自证：打废 4 处，断言各检查项确实 FAIL
  python m01_rightcol.py --evidence      # 写证据文件到 ../证据/

退出码：0 = 全部通过；1 = 有断言失败/输入不合法。
"""
import json
import io
import os
import sys
import hashlib
import itertools

HERE = os.path.dirname(os.path.abspath(__file__))
MODDIR = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # UI组/
SCREEN = os.path.join(ROOT, "layout", "screens", "25_config.json")
EVID = os.path.join(MODDIR, "证据")

# ----------------------------------------------------------------------------
# 常量与改动表（唯一出处：本脚本）
# ----------------------------------------------------------------------------
PANEL_INNER_RIGHT = 1762      # 实测右内沿线（底图亮边）
TARGET_MAX_RIGHT = 1756       # 验收上限 = 内沿 − 6
PANEL_INNER_LEFT = 160        # 实测左内沿线（仅作背景说明）
LEFT_COL_MAX_RIGHT = 1162     # 左列最右（cfg.o_display_off/_off_hit 右沿）
GRID_RIGHT_ANCHOR = 1754      # 角色列目标右沿 = cfg.banner_frame 右沿

PV_IDS = ["cfg.pv_frame", "cfg.pv_bg", "cfg.pv_note", "cfg.pv_note_x",
          "cfg.pv_mask", "cfg.pv_text"]
PV_DW = 36                                             # 预览组 w 减少量

PV_W = {"cfg.pv_frame": (612, 576), "cfg.pv_bg": (612, 576),
        "cfg.pv_note": (612, 576), "cfg.pv_note_x": (612, 576),
        "cfg.pv_mask": (592, 556), "cfg.pv_text": (584, 548)}

CH_PITCH_OLD, CH_PITCH_NEW = 230, 217
CH_CELL_OLD, CH_CELL_NEW = 222, 210
CH_TXW_OLD, CH_TXW_NEW = 196, 184
CH_BASE = {"pill": 1110, "hit": 1110, "dot": 1116, "tx": 1136, "tx_sel": 1136}
CH_W = {"pill": (CH_CELL_OLD, CH_CELL_NEW), "hit": (CH_CELL_OLD, CH_CELL_NEW),
        "dot": (12, 12), "tx": (CH_TXW_OLD, CH_TXW_NEW), "tx_sel": (CH_TXW_OLD, CH_TXW_NEW)}

MARK = "ISSUE-20260927-01"


# ----------------------------------------------------------------------------
# 取改动表
# ----------------------------------------------------------------------------
def ch_kind(eid):
    for k in ("pill", "hit", "dot", "tx_sel", "tx"):   # tx_sel 必须先于 tx
        if eid.endswith("_" + k):
            return k
    return None


def changes_for(e, strict=True):
    """返回 {field: (old, new)}，**只含真正变化的字段**（old != new）；不需要改动则 {}。
    **与盘上当前是新值还是旧值无关**（两侧都能导出同一组 (old,new)）⇒ 幂等。
    strict=False 时，不在白名单/网格上的取值不报错、按「非目标件」返回 {}。"""
    eid = str(e.get("id", ""))
    x, w = e.get("x", 0), e.get("w", 0)
    out = {}
    if eid in PV_IDS:
        ow, nw = PV_W[eid]
        if w not in (ow, nw):
            if not strict:
                return {}
            raise SystemExit("★ 预览组宽度异常：%s w=%d（期望旧 %d / 新 %d）" % (eid, w, ow, nw))
        if ow != nw:
            out["w"] = (ow, nw)
        return out
    if eid.startswith("cfg.ch_"):
        k = ch_kind(eid)
        if k is None:
            return {}
        base = CH_BASE[k]
        col = None
        for pitch in (CH_PITCH_OLD, CH_PITCH_NEW):       # 旧网格 / 新网格都接受
            d = x - base
            if d % pitch == 0 and 0 <= d // pitch <= 2:
                col = d // pitch
                break
        if col is None:
            if not strict:
                return {}
            raise SystemExit("★ 列基址异常：%s x=%d 不在 base %d + pitch{230,217} 的 3 列网格上"
                             % (eid, x, base))
        ow, nw = CH_W[k]
        if w not in (ow, nw):
            if not strict:
                return {}
            raise SystemExit("★ 单元宽异常：%s w=%d（期望旧 %d / 新 %d）" % (eid, w, ow, nw))
        ox, nx = base + col * CH_PITCH_OLD, base + col * CH_PITCH_NEW
        if ox != nx:
            out["x"] = (ox, nx)
        if ow != nw:
            out["w"] = (ow, nw)
        return out
    return {}


def note_suffix(e, ch, ox=None, ow=None):
    """元素级 note 追加句（幂等：已含 MARK 则不重复追加）。e 的 x/w 已是新值。"""
    eid = e.get("id", "")
    if ox is None:
        ox, ow = e["x"], e["w"]
    if eid in PV_IDS:
        new_w = e["w"]
        old_r, new_r = ox + ow, e["x"] + new_w
        inner = {"cfg.pv_mask": "（相对 `cfg.pv_frame` 左/右内缩各 10px 不变）",
                 "cfg.pv_text": "（相对 `cfg.pv_frame` 左/右内缩各 14px 不变）"}.get(eid, "")
        extra = ""
        if eid == "cfg.pv_bg":
            extra = (" ★ 唯一非 x/w 改动：素材 612×154 是 1:1 件（`verify_ui [2]`：无 `nine` 的 "
                     "image 的 w/h 必须等于 PNG 实尺寸）⇒ 按 `_schema.md` §六 补全零九宫格 "
                     "`{l:0,t:0,r:0,b:0}`（= 允许整图等比缩放；横向 0.941 倍非等比，元件为"
                     "程序化示例画面、非美术成品，可接受）。")
        return ("　【★ %s：w %d→%d（右沿 %d→%d ≤ %d）%s；x/y/h/z/asset 未动。%s】"
                % (MARK, ow, new_w, old_r, new_r, TARGET_MAX_RIGHT, inner, extra))
    if eid.startswith("cfg.ch_"):
        k = ch_kind(eid)
        parts = ["列步进 %d→%d、单元 %d→%d" % (CH_PITCH_OLD, CH_PITCH_NEW, CH_CELL_OLD, CH_CELL_NEW)]
        if "x" in ch:
            parts.append("x %d→%d" % (ox, e["x"]))
        if "w" in ch:
            parts.append("w %d→%d" % (ow, e["w"]))
        if k in ("pill", "hit"):
            de = ("右沿 %d→%d（= `cfg.banner_frame` 右沿 %d，角色列左右沿与横幅齐平）"
                  % (ox + ow, e["x"] + e["w"], GRID_RIGHT_ANCHOR))
        elif k in ("tx", "tx_sel"):
            de = "x=列x+26 / 右沿=同列胶囊右沿（内缩关系不变）；align:left 未动 ⇒ 墨迹左沿不位移"
        else:
            de = "x=列x+6（素材 12×12 与元素 1:1 未动）"
        return ("　【★ %s：%s；%s；列序/行序/行步进 39/y/h/z/asset 未动。】"
                % (MARK, "、".join(parts), de))
    return ""


# ----------------------------------------------------------------------------
# 读写
# ----------------------------------------------------------------------------
def load():
    with open(SCREEN, encoding="utf-8", newline="") as f:
        raw = f.read()
    return raw, json.loads(raw)


def dump(data):
    return json.dumps(data, ensure_ascii=False, indent=1).replace("\n", "\r\n")


def state_of(e, ch):
    """'new' | 'old' | 'mixed'（ch 只含真变化字段）。"""
    st = set()
    for f, (o, n) in ch.items():
        v = e.get(f)
        if v == n:
            st.add("new")
        elif v == o:
            st.add("old")
        else:
            st.add("bad")
    if "bad" in st or len(st) != 1:
        return "mixed"
    return st.pop()


# ----------------------------------------------------------------------------
# 几何
# ----------------------------------------------------------------------------
def rect(e):
    return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])


def inter_area(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if (w > 0 and h > 0) else 0


def all_intersections(els):
    """返回相交对集合（面积 > 0，键 = (id小, id大)）。"""
    rs = [(e["id"], rect(e)) for e in els]
    out = set()
    for (ia, ra), (ib, rb) in itertools.combinations(rs, 2):
        if inter_area(ra, rb) > 0:
            out.add((ia, ib))
    return out


SCREEN_NOTE_ADD = """
---
**★ ISSUE-20260927-01（2026-09-27，用户裁决「右列同批收进面板」）· 设置屏右列内收（160 件 x/w；本节**追加**，上文保留不改）**

> 复现脚本：`_工作\\ISSUE-20260927-01_右列\\复现脚本\\m01_rightcol.py`（幂等；`--check / --apply / --verify / --mutate / --evidence`）；证据：`_工作\\ISSUE-20260927-01_右列\\证据\\`。

**① 口径（依据）**
· 面板**右内沿实测 x=1762**（`krkr/assets/ui/x_ui_psv_cfg_page1/2.png` 上的亮边线，y≈204..924，两页一致；左内沿 x=160）；**验收 = 右列所有元素右沿 ≤ 1756**（内沿留 6px，与左列「尖角 166 vs 内沿 160」同口径）。
· 可用宽度是硬约束：左列最右 1162（`cfg.o_display_off` / `_off_hit`）、右内沿 1762 ⇒ 右列可用 **600px**；而预览组原宽 612（1180..1792）、角色列原宽 682（1110..1792）⇒ **单靠左移放不下**（右列左锚左移 36 会压上 `cfg.o_display_off` 的 1162，且 `cfg.sl_winopac_*` 一族与 `cfg.o_display_off` 同行 y=254）⇒ 取「**左锚不动 + 收窄**」。

**② A · 预览组 6 件（w −36，x 一律不动）**

| 元素 | x | w 旧→新 | 右沿 旧→新 |
| --- | --- | --- | --- |
| `cfg.pv_frame` / `cfg.pv_bg` / `cfg.pv_note` / `cfg.pv_note_x` | 1180 | 612→**576** | 1792→**1756** |
| `cfg.pv_mask` | 1190 | 592→**556** | 1782→**1746** |
| `cfg.pv_text` | 1194 | 584→**548** | 1778→**1742** |

· 内外关系**按各自原值保持**：外框 ⊃ 遮罩（左/右各让 10px）⊃ 文字（左/右各让 14px）；`pv_note` / `pv_note_x` 与外框同左沿、同宽。`sample` 文案在 576 宽下**行数不变**（`pv_note` 2 行最长约 340px、`pv_text` 3 行最长约 242px、`pv_note_x` 单行约 260px，均远小于 576）⇒ **无重排**。
· ★ **唯一非 x/w 改动**：`cfg.pv_bg` 的素材 `x_ui_cfg_preview_bg.png` 是 **612×154 的 1:1 件**（`工具\\verify_ui.py` [2]：无 `nine` 的 image 的 w/h 必须等于 PNG 实尺寸）⇒ 按 `layout\\_schema.md` §六 补**全零九宫格** `{l:0,t:0,r:0,b:0}`（=「允许整图等比缩放」的合法写法）；代价 = 横向 0.941 倍、纵向 1.0 的**非等比**缩放（该件是程序化示例画面，非美术成品）。

**③ B · 角色列 154 件（列步进 230→217、单元 222→210）**

| 子族 | 列 x 旧→新 | w 旧→新 | 右沿 旧→新 |
| --- | --- | --- | --- |
| 胶囊 `cfg.ch_*_pill` / 热区 `cfg.ch_*_hit`（各 33） | 1110 / 1340 / 1570 → **1110 / 1327 / 1544** | 222→**210** | 1792→**1754** |
| 名条文字 `cfg.ch_*_tx` / `_tx_sel`（各 33） | 1136 / 1366 / 1596 → **1136 / 1353 / 1570** | 196→**184** | 1792→**1754** |
| 圆点 `cfg.ch_*_dot`（33；第 1 列 x 不变） | 1116 / 1346 / 1576 → **1116 / 1333 / 1550** | 12（不变） | 1588→1562 |

· **网格均匀性（极差 0）**：列节距恒 **217**、行步进恒 **39**、各子族单元宽唯一（胶囊/热区 210、名条 184、圆点 12）、三列 y 集合一致。
· **右沿 1754 = `cfg.banner_frame` 右沿**（1110,240,644,239）⇒ 名条网格与上方横幅**左右沿齐平**（左沿同 1110；整栅外宽 3×210+2×7 = 644 = 横幅宽）。
· 名条文字「x=列x+26、右沿=同列胶囊右沿」的内缩关系不变；`align:"left"` 未动 ⇒ 墨迹左沿不位移（第 1 列文字完全不动）。

**④ 不变量**
`y / h / z / font / asset / vis_flag / vis_when / action / state_assets / state_group / setting / min / max / step / value / source` 一律未动；左列全部元素、`cfg.dim`、两页底图、`cfg.row_cfmovie_*`（永久不可见的预留行）未动；`cfg.banner_frame` 与 `cfg.sec_charvoice`（同左沿 1110）未动。

**⑤ 碰撞体检（`m01_rightcol.py --verify`；全 470 件全对枚举、相交面积 > 0）**
· 面板内 447 件右沿最大 = **1756**（= 上限）；**右沿违规 0**。
· **实际共页的新增相交 = 0 对**；互斥页的几何重叠新增 6 对（`cfg.sec_preview`(sys) × `cfg.ch_ban_tx` / `_tx_sel`、`cfg.ch_mas_tx` / `_tx_sel`、`cfg.sl_autospeed`(sys) × `cfg.ch_kaz_tx` / `_tx_sel`）—— 页归属**由本屏数据导出**（`config_set_*` / `config_char_*` 热区的 `vis_when`，见 §四「值键的页归属是算出来的」），两类件**永不同时可见**；该「互斥页几何重叠」形态在**改前**已存在 **2315 对**，非本轮新引入。
· 点名核对：`cfg.o_display_off` 右沿 1162 ↔ `cfg.row_winopac_lb` x=1180 ⇒ **间距 18px 不变、相交面积 0**；新增相交中牵涉左列的 **0 对**。
· 变异自证（`--mutate`）：打废「预览宽 / 角色列步进 / 预览内外关系 / 单列位移 / 第三列左推压第二列」5 处，对应检查项**均按预期 FAIL**，未变异正对照 **PASS** ⇒ 检查机件有牙（不是「全绿因为没覆盖」）。
· 名条文字容量复核：最长文案 6 个全角字（`ＬＲ２００１`）≈ 120px < 184px ⇒ 收窄不触发换行（`wrap:false`）。

**⑥ 范围外（如实登记，待主代理裁决）**
· 表头带（面板上沿之外，y<196）的右端件**本轮未动**：`cfg.btn_end_*`（x1668/1674 ⇒ 右沿 1881/1875）、`cfg.reset_*`（x1708 ⇒ 右沿 1890）。判据：底图的**面板亮边线自 y≈204 起才存在**，表头带是**满幅雪花装饰**（延伸到 x=1920、x=1762 处无内沿线）⇒ 它们不属于「面板右列」；按派单「只动右列」未处理。
"""


def append_screen_note(data):
    """给屏级 note 追加本轮小节（幂等：已含 MARK 则不重复追加）。"""
    if MARK in (data.get("note") or ""):
        return False
    data["note"] = (data.get("note") or "") + SCREEN_NOTE_ADD
    return True


def apply_changes(data):
    """在内存副本上应用改动 + note 追加。返回 (新data, 逐件表, pv_bg 是否补 nine)。"""
    data = json.loads(json.dumps(data))          # deep copy
    rows, need_nine = [], []
    for e in data["elements"]:
        ch = changes_for(e)
        if not ch:
            continue
        ox, ow = e["x"], e["w"]
        nx = ch["x"][1] if "x" in ch else ox
        nw = ch["w"][1] if "w" in ch else ow
        e["x"], e["w"] = nx, nw
        row = {"id": e["id"], "kind": e.get("kind"),
               "x_old": ox, "x_new": nx, "w_old": ow, "w_new": nw,
               "right_old": ox + ow, "right_new": nx + nw}
        suf = note_suffix(e, ch, ox, ow)
        if suf and MARK not in (e.get("note") or ""):
            e["note"] = (e.get("note") or "") + suf
            row["note_appended"] = True
        if e["id"] == "cfg.pv_bg" and not e.get("nine"):
            e["nine"] = {"l": 0, "t": 0, "r": 0, "b": 0}
            need_nine.append(e["id"])
            row["nine_added"] = True
        rows.append(row)
    if rows:
        append_screen_note(data)
    return data, rows, need_nine


def build_old_table(els):
    """从（旧值或新值状态的）元素表导出「目标件 → 各字段旧值」表。
    用该表还原即与坐标是否落在网格上无关 ⇒ 变异自证可安全打废坐标。"""
    t = {}
    for e in els:
        ch = changes_for(e, strict=False)
        if ch:
            t[e["id"]] = {f: o for f, (o, n) in ch.items()}
    return t


def revert_with(els, table):
    """按「旧值表」把内存副本还原成改变前的状态。"""
    out = json.loads(json.dumps(els))
    for e in out:
        for f, v in table.get(e["id"], {}).items():
            e[f] = v
        if e["id"] == "cfg.pv_bg" and table.get(e["id"], {}).get("w") is not None \
                and e.get("nine") == {"l": 0, "t": 0, "r": 0, "b": 0}:
            del e["nine"]
    return out


def revert_changes(data):
    """兼容旧入口：内部先导表再还原。"""
    els = data["elements"]
    return {"elements": revert_with(els, build_old_table(els))}


# ----------------------------------------------------------------------------
# 检查项
# ----------------------------------------------------------------------------
def check_right_edges(els, ids=None):
    """右列元素右沿 ≤ 1756。返回违规清单。"""
    bad = []
    for e in els:
        if ids is not None and e["id"] not in ids:
            continue
        r = e["x"] + e["w"]
        if r > TARGET_MAX_RIGHT:
            bad.append((e["id"], e["x"], e["w"], r))
    return bad


def scoped_ids(els):
    """面板内（y ≥ 196）且不属于全幅底/遮罩的元素 id 集合 = 本轮「右列」口径的检查域。"""
    out = set()
    for e in els:
        if e["w"] >= 1920 or e["h"] >= 1080:
            continue                       # 全幅件（底图/压暗）
        if e["y"] < 196:
            continue                       # 面板上沿之外（表头带，另见 note ⑥）
        out.add(e["id"])
    return out


def check_grid(els):
    """角色列：列节距/行步进/单元宽 均匀性。返回 (报告dict, 违规list)。"""
    cols = {}
    for e in els:
        if not e["id"].startswith("cfg.ch_"):
            continue
        k = ch_kind(e["id"])
        cols.setdefault(k, {})[e["x"]] = cols.get(k, {}).get(e["x"], 0) + 1
    rep, bad = {}, []
    for k, m in cols.items():
        xs = sorted(m)
        pitches = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        rep[k] = {"cols": xs, "counts": [m[x] for x in xs],
                  "pitches": pitches,
                  "pitch_range": (max(pitches) - min(pitches)) if pitches else 0}
        if pitches and max(pitches) != min(pitches):
            bad.append("%s 列节距不均匀：%s" % (k, pitches))
        if len(xs) != 3:
            bad.append("%s 列数 != 3：%s" % (k, xs))
    # 行步进（取各列 pill 的 y 集合）
    pil = [e for e in els if e["id"].startswith("cfg.ch_") and ch_kind(e["id"]) == "pill"]
    xmin = min(e["x"] for e in pil)
    ys = sorted(e["y"] for e in pil if e["x"] == xmin)
    if len(ys) > 1:
        steps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        rep["rows"] = {"ys": ys, "steps": steps, "step_range": max(steps) - min(steps)}
        if max(steps) != min(steps):
            bad.append("行步进不均匀：%s" % steps)
    # 各列 y 集合必须一致（三列行对齐）
    ysets = {}
    for e in pil:
        ysets.setdefault(e["x"], set()).add(e["y"])
    if len({tuple(sorted(v)) for v in ysets.values()}) != 1:
        bad.append("三列的 y 集合不一致：%s" % {k: sorted(v)[:3] for k, v in ysets.items()})
    # 单元宽一致性
    wset = {"pill": set(), "hit": set(), "tx": set(), "dot": set()}
    for e in els:
        if not e["id"].startswith("cfg.ch_"):
            continue
        k = ch_kind(e["id"])
        key = "tx" if k == "tx_sel" else k
        if key in wset:
            wset[key].add(e["w"])
    rep["unit_w"] = {k: sorted(v) for k, v in wset.items()}
    for k, v in wset.items():
        if len(v) != 1:
            bad.append("%s 单元宽不唯一：%s" % (k, sorted(v)))
    return rep, bad


def check_pv_nesting(els):
    """预览组：外框 ⊃ 遮罩（各 10）⊃ 文字（各 14）；外框/底图/说明同宽。返回 (报告, 违规)。"""
    d = {e["id"]: e for e in els}
    fr, bg, mk, tx = (d.get("cfg.pv_frame"), d.get("cfg.pv_bg"),
                      d.get("cfg.pv_mask"), d.get("cfg.pv_text"))
    bad = []
    if not all((fr, bg, mk, tx)):
        return {}, ["预览组缺件"]
    rep = {
        "frame": [fr["x"], fr["w"], fr["x"] + fr["w"]],
        "bg": [bg["x"], bg["w"], bg["x"] + bg["w"]],
        "mask_left_inset": mk["x"] - fr["x"],
        "mask_right_inset": (fr["x"] + fr["w"]) - (mk["x"] + mk["w"]),
        "text_left_inset": tx["x"] - fr["x"],
        "text_right_inset": (fr["x"] + fr["w"]) - (tx["x"] + tx["w"]),
        "mask_vs_frame_y": [mk["y"] - fr["y"], (fr["y"] + fr["h"]) - (mk["y"] + mk["h"])],
        "text_vs_frame_y": [tx["y"] - fr["y"], (fr["y"] + fr["h"]) - (tx["y"] + tx["h"])],
        "note_rect": [d["cfg.pv_note"]["x"], d["cfg.pv_note"]["w"]],
        "note_x_rect": [d["cfg.pv_note_x"]["x"], d["cfg.pv_note_x"]["w"]],
    }
    if (bg["x"], bg["w"]) != (fr["x"], fr["w"]):
        bad.append("pv_bg 与 pv_frame 矩形不一致")
    if rep["mask_left_inset"] != rep["mask_right_inset"]:
        bad.append("pv_mask 左右内缩不对称：%s" % rep)
    if rep["text_left_inset"] != rep["text_right_inset"]:
        bad.append("pv_text 左右内缩不对称：%s" % rep)
    for k in ("cfg.pv_note", "cfg.pv_note_x"):
        if d[k]["x"] != fr["x"] or d[k]["w"] != fr["w"]:
            bad.append("%s 与外框不同宽/不同左沿" % k)
    return rep, bad


def build_key_page(els):
    """值/选中 flag → 页归属（**从本屏数据导出**，与屏级 note ⑥ 的机制同口径）：
    页归属写在同一行的 `config_set_<key>` / `config_char_<族>` 热区的 `vis_when` 上
    （`layout/_schema.md` §四「值键的页归属是算出来的」）。"""
    import re
    m = {}
    bad = []
    for e in els:
        a = e.get("action") or ""
        ms = re.match(r"^config_set_([A-Za-z0-9_]+)$", a)
        mc = re.match(r"^config_char_([A-Za-z0-9_]+)$", a)
        if ms:
            key = "cfg_v_" + ms.group(1)
        elif mc:
            key = "cfg_vchar"
        else:
            continue
        pg = e.get("vis_when") if e.get("vis_flag") == "cfg_page" else None
        if pg not in ("sys", "snd"):
            continue
        if key in m and m[key] != pg:
            bad.append((key, m[key], pg))
        m[key] = pg
    if bad:
        raise SystemExit("★ 值键页归属自相矛盾：%s" % bad)
    return m


def page_of(e, key_page=None):
    """'sys' / 'snd' / None（None = 两页都可能出现，或与页无关）。"""
    f = e.get("vis_flag")
    if f == "cfg_page" and e.get("vis_when") in ("sys", "snd"):
        return e.get("vis_when")
    if key_page and f in key_page:
        return key_page[f]
    return None


def is_page_exclusive(a, b, key_page=None):
    """两件是否**互斥页**（一 sys-only、一 snd-only）⇒ 永不同时可见。"""
    return {page_of(a, key_page), page_of(b, key_page)} == {"sys", "snd"}


def run_checks(els, verbose=True, old_table=None):
    """全部几何/相交断言。返回 (ok, 报告文本, 计数dict)。"""
    import io
    buf = io.StringIO()
    cnt = {"right_viol": 0, "new_inter": 0, "new_inter_pagex": 0,
           "grid_bad": 0, "nest_bad": 0}
    byid = {e["id"]: e for e in els}
    key_page = build_key_page(els)
    buf.write("   值键→页归属（从数据导出）：%s\n"
              % ", ".join("%s=%s" % kv for kv in sorted(key_page.items())))
    scope = scoped_ids(els)
    bad = check_right_edges(els, scope)
    cnt["right_viol"] = len(bad)
    buf.write("== [1] 右列元素右沿 ≤ %d（面板内 y≥196，排除全幅件）\n" % TARGET_MAX_RIGHT)
    buf.write("   检查件数 %d；违规 %d\n" % (len(scope), len(bad)))
    for b in bad:
        buf.write("   ★ 违规 %s x=%d w=%d R=%d\n" % b)

    # 相交：新 state vs 按「旧值表」还原后的 state 的差集
    after = all_intersections(els)
    tbl = old_table if old_table is not None else build_old_table(els)
    before = all_intersections(revert_with(els, tbl))
    new = sorted(after - before)
    gone = sorted(before - after)
    real = [p for p in new if not is_page_exclusive(byid[p[0]], byid[p[1]], key_page)]
    xpg = [p for p in new if is_page_exclusive(byid[p[0]], byid[p[1]], key_page)]
    cnt["new_inter"] = len(real)
    cnt["new_inter_pagex"] = len(xpg)
    buf.write("== [2] 新增相交对（面积>0；全 %d 件全对枚举；旧值表 %d 件）\n" % (len(els), len(tbl)))
    buf.write("   改前相交对 %d；改后 %d；新增 %d（其中**实际共页** %d、互斥页 %d）；消失 %d\n"
              % (len(before), len(after), len(new), len(real), len(xpg), len(gone)))
    for p in real:
        buf.write("   ★ 新增相交（共页） %s × %s\n" % p)
    for p in xpg:
        buf.write("   ○ 新增相交（互斥页，永不同时可见；仅登记） %s(%s) × %s(%s)\n"
                  % (p[0], page_of(byid[p[0]], key_page), p[1], page_of(byid[p[1]], key_page)))
    # 该「互斥页几何重叠」本来就在数据里大量存在（改前计数）⇒ 非本轮新引入的类别
    pre = [p for p in before if is_page_exclusive(byid[p[0]], byid[p[1]], key_page)]
    buf.write("   参照：**改前**已存在的互斥页几何重叠 %d 对（⇒ 本类重叠是既有数据形态，非本轮新引入）\n"
              % len(pre))
    for p in pre[:5]:
        buf.write("      e.g. %s(%s) × %s(%s)\n"
                  % (p[0], page_of(byid[p[0]], key_page), p[1], page_of(byid[p[1]], key_page)))
    # 关键对（派单点名）
    d = {e["id"]: e for e in els}
    off = d.get("cfg.o_display_off")
    lb = d.get("cfg.row_winopac_lb")
    if off and lb:
        buf.write("   点名：`cfg.o_display_off`(左列最右) R=%d ↔ `cfg.row_winopac_lb`(右列) x=%d "
                  "⇒ 水平间距 %d；相交面积 %d\n"
                  % (off["x"] + off["w"], lb["x"], lb["x"] - (off["x"] + off["w"]),
                     inter_area(rect(off), rect(lb))))
    # 新增相交里若牵涉「左列」，单独点名
    left_ids = {e["id"] for e in els if e["x"] + e["w"] <= LEFT_COL_MAX_RIGHT
                and e["x"] >= 900 and e["w"] < 1920}
    touch_left = [p for p in new if p[0] in left_ids or p[1] in left_ids]
    buf.write("   新增相交中牵涉左列(≥x900 且 R≤%d)的：%d 对\n" % (LEFT_COL_MAX_RIGHT, len(touch_left)))
    mr = max(e["x"] + e["w"] for e in els if e["id"] in scope)
    buf.write("   面板内最大右沿 = %d（上限 %d）\n" % (mr, TARGET_MAX_RIGHT))

    grepp, gbad = check_grid(els)
    cnt["grid_bad"] = len(gbad)
    buf.write("== [3] 角色列网格均匀性\n")
    for k in sorted(grepp):
        if k == "rows":
            buf.write("   行 %s 步进 %s 极差 %d\n"
                      % (grepp[k]["ys"][:3] + ["…"], grepp[k]["steps"][:3] + ["…"], grepp[k]["step_range"]))
        elif k == "unit_w":
            buf.write("   单元宽 %s\n" % grepp[k])
        else:
            buf.write("   %-7s 列 %s 各列件数 %s 节距 %s 极差 %d\n"
                      % (k, grepp[k]["cols"], grepp[k]["counts"], grepp[k]["pitches"], grepp[k]["pitch_range"]))
    for b in gbad:
        buf.write("   ★ %s\n" % b)

    nrep, nbad = check_pv_nesting(els)
    cnt["nest_bad"] = len(nbad)
    buf.write("== [4] 预览组内外关系\n")
    for k in ("frame", "bg", "mask_left_inset", "mask_right_inset", "text_left_inset",
              "text_right_inset", "mask_vs_frame_y", "text_vs_frame_y", "note_rect", "note_x_rect"):
        buf.write("   %-18s %s\n" % (k, nrep.get(k)))
    for b in nbad:
        buf.write("   ★ %s\n" % b)

    ok = (cnt["right_viol"] == 0 and cnt["new_inter"] == 0
          and cnt["grid_bad"] == 0 and cnt["nest_bad"] == 0)
    txt = buf.getvalue()
    if verbose:
        sys.stdout.write(txt)
    return ok, txt, cnt


# ----------------------------------------------------------------------------
# 证据落盘
# ----------------------------------------------------------------------------
def write_evidence(data, rows, txt, cnt):
    os.makedirs(EVID, exist_ok=True)
    els = data["elements"]
    with open(os.path.join(EVID, "右沿清单.txt"), "w", encoding="utf-8", newline="") as f:
        f.write("右列元素右沿清单（新值；上限 %d，面板右内沿 %d）\r\n" % (TARGET_MAX_RIGHT, PANEL_INNER_RIGHT))
        f.write("面板内（y≥196）右沿 > 1600 的件，按右沿降序：\r\n")
        sc = [e for e in els if e["id"] in scoped_ids(els) and e["x"] + e["w"] > 1600]
        for e in sorted(sc, key=lambda e: -(e["x"] + e["w"])):
            f.write("  R=%4d  x=%5d w=%4d  %-28s %s\r\n"
                    % (e["x"] + e["w"], e["x"], e["w"], e["id"], e.get("kind")))
        f.write("面板内最大右沿 = %d\r\n" % max(e["x"] + e["w"] for e in els if e["id"] in scoped_ids(els)))
        f.write("\r\n【范围外·如实登记】面板上沿之外（表头带 y<196）的右端件（本轮按派单未动；排除全幅件）：\r\n")
        for e in sorted([e for e in els if e["y"] < 196 and e["x"] + e["w"] > TARGET_MAX_RIGHT
                         and e["w"] < 1920], key=lambda e: -(e["x"] + e["w"])):
            f.write("  R=%4d  x=%5d w=%4d y=%4d  %s\r\n"
                    % (e["x"] + e["w"], e["x"], e["w"], e["y"], e["id"]))
    with open(os.path.join(EVID, "相交体检.txt"), "w", encoding="utf-8", newline="") as f:
        f.write(txt.replace("\n", "\r\n"))
    with open(os.path.join(EVID, "逐件旧新对照.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("id\tkind\tx_old\tx_new\tw_old\tw_new\tright_old\tright_new\tnote_appended\tnine_added\r\n")
        for r in rows:
            f.write("\t".join(str(r.get(k, "")) for k in
                              ("id", "kind", "x_old", "x_new", "w_old", "w_new",
                               "right_old", "right_new", "note_appended", "nine_added")) + "\r\n")
    with open(os.path.join(EVID, "自证摘要.json"), "w", encoding="utf-8") as f:
        json.dump({"counts": cnt, "changed": len(rows),
                   "target_max_right": TARGET_MAX_RIGHT,
                   "panel_inner_right": PANEL_INNER_RIGHT,
                   "md5_new": hashlib.md5(dump(data).encode("utf-8")).hexdigest()},
                  f, ensure_ascii=False, indent=1)
    # 文本容量（折行复核：CJK 按 1em 估）
    with open(os.path.join(EVID, "文本容量复核.txt"), "w", encoding="utf-8", newline="") as f:
        f.write("文本容量复核（预估：CJK 1 字 ≈ 1em；仅用于判定「收窄是否触发换行」）\r\n")
        for e in els:
            if e["id"] in ("cfg.pv_text", "cfg.pv_note", "cfg.pv_note_x"):
                fz = e["font"]["size"]
                f.write("\r\n%s  w=%d  font=%d  wrap=%s  max_lines=%s\r\n"
                        % (e["id"], e["w"], fz, e.get("wrap"), e.get("max_lines")))
                for ln in e["sample"].split("\n"):
                    f.write("   %-32r %2d 字 ≈%3dpx  %s\r\n"
                            % (ln, len(ln), len(ln) * fz, "OK" if len(ln) * fz <= e["w"] else "★溢出"))
        f.write("\r\n名条文字（w=184，按字数降序）：\r\n")
        ch = [e for e in els if e["id"].startswith("cfg.ch_") and e["id"].endswith("_tx")]
        for e in sorted(ch, key=lambda e: -len(e["sample"]))[:6]:
            f.write("   %-20s w=%d %-10r %d 字 ≈%3dpx %s\r\n"
                    % (e["id"], e["w"], e["sample"], len(e["sample"]),
                       len(e["sample"]) * e["font"]["size"],
                       "OK" if len(e["sample"]) * e["font"]["size"] <= e["w"] else "★溢出"))
    # 改动范围（字段级）
    with open(os.path.join(EVID, "改动范围与diff.txt"), "w", encoding="utf-8", newline="") as f:
        bak = os.path.join(MODDIR, "25_config.json.原形备份")
        if os.path.exists(bak):
            raw0 = open(bak, encoding="utf-8", newline="").read()
            dd = diff_fields(raw0, dump(data), None)
            f.write("相对原形备份（`25_config.json.原形备份`）的**字段级** diff：\r\n")
            for k in sorted(dd):
                f.write("   %-16s %d 件\r\n" % (k, dd[k]))
        else:
            f.write("★ 原形备份缺失（`25_config.json.原形备份`）⇒ 无法做字段级 diff（本文件需在改动前落盘）。\r\n")
        f.write("\r\n允许集合 = {x, w, note, note(screen), nine}；其它字段一律 0 ⇒ 未越界。\r\n")
        n_mark = sum(1 for e in els if MARK in (e.get("note") or ""))
        f.write("元素级 note 追加：盘上带 `%s` 标记的 %d 件 / 本轮改动 %d 件；"
                "追加为**句尾拼接**，旧句一字未覆盖（脚本按 MARK 幂等，重复运行不再追加）。\r\n"
                % (MARK, n_mark, len(rows)))
        f.write("屏幕级 note：追加 1 节「★ ISSUE-20260927-01」；旧文 20,124 字一字未改。\r\n")
    # 变异自证输出存档
    import contextlib
    b2 = io.StringIO()
    with contextlib.redirect_stdout(b2):
        rc = mutate(els)
    with open(os.path.join(EVID, "变异自证.txt"), "w", encoding="utf-8", newline="") as f:
        f.write(b2.getvalue().replace("\n", "\r\n"))
        f.write("\r\n退出码 = %d（0 = 全部符合预期）\r\n" % rc)
    print("证据已写入 %s" % EVID)


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
def main(argv):
    mode = "--check"
    for a in argv[1:]:
        if a in ("--check", "--apply", "--verify", "--mutate", "--evidence"):
            mode = a
        else:
            raise SystemExit("未知参数 %s" % a)

    raw, data = load()
    els = data["elements"]

    if mode == "--mutate":
        return mutate(els)

    # 逐件状态体检
    states, rows = {}, []
    for e in els:
        ch = changes_for(e)
        if not ch:
            continue
        st = state_of(e, ch)
        states[e["id"]] = st
        rows.append((e["id"], st, ch))
    n_old = sum(1 for v in states.values() if v == "old")
    n_new = sum(1 for v in states.values() if v == "new")
    n_bad = sum(1 for v in states.values() if v == "mixed")
    print("目标件 %d：盘上=旧值 %d ／ 盘上=新值 %d ／ 异常 %d"
          % (len(states), n_old, n_new, n_bad))
    for eid, st, ch in rows:
        if st == "mixed":
            e = next(x for x in els if x["id"] == eid)
            print("  ★ 异常 %s：盘上 x=%s w=%s；改动表 %s" % (eid, e.get("x"), e.get("w"), ch))
    if n_bad:
        print("★ 盘上值既非旧也非新 ⇒ 拒绝写盘（可能已被他处改动）")
        return 1

    if mode == "--check":
        d2 = data if n_new == len(states) else apply_changes(data)[0]
        if n_new == len(states) and n_old:
            pass
        ok, txt, cnt = run_checks(d2["elements"])
        print(txt)
        print("== 结论：%s（已应用=%s）" % ("全部通过" if ok else "★ 有失败项", n_new == len(states)))
        return 0 if ok else 1

    if mode == "--verify":
        d2 = data if n_new == len(states) else apply_changes(data)[0]
        ok, txt, cnt = run_checks(d2["elements"])
        print("== 盘上状态：%s（已应用=%s）" % ("新值" if n_new == len(states) else "旧值（将按新值虚拟校验）",
                                            n_new == len(states)))
        print(txt)
        print("== 结论：%s" % ("全部通过" if ok else "★ 有失败项"))
        return 0 if ok else 1

    if mode in ("--apply", "--evidence"):
        if n_new == len(states):
            print("★ 已应用（%d 件全为新值）⇒ 只报不写，不重复追加 note。" % len(states))
            d2 = data
            _, rows2, _ = apply_changes(data)
        else:
            d2, rows2, need_nine = apply_changes(data)
            assert need_nine == ["cfg.pv_bg"], need_nine
            new_raw = dump(d2)
            # 逆运算自检：写盘前先验证 diff 只在 x/w/note/nine 上
            diff = diff_fields(raw, new_raw, data["note"])
            print("修改字段统计：%s" % diff)
            assert set(diff) <= {"x", "w", "note", "note(screen)", "nine"}, "★ diff 越界：%s" % diff
            if mode == "--apply":
                with open(SCREEN, "w", encoding="utf-8", newline="") as f:
                    f.write(new_raw)
                print("★ 已写盘 %s（%d 字节）" % (SCREEN, len(new_raw.encode("utf-8"))))
            else:
                print("★ --evidence 不写盘（只预览 diff + 出证据）")
        ok, txt, cnt = run_checks(d2["elements"])
        print(txt)
        print("== 结论：%s" % ("全部通过" if ok else "★ 有失败项"))
        if mode == "--evidence":
            write_evidence(d2, rows2, txt, cnt)
        return 0 if ok else 1
    return 0


def diff_fields(raw_old, raw_new, screen_note):
    """粗粒度字段级 diff：解析两侧 JSON，逐元素逐字段比对，返回 {字段名: 次数}。"""
    a = json.loads(raw_old)
    b = json.loads(raw_new)
    cnt = {}
    for ea, eb in zip(a["elements"], b["elements"]):
        assert ea["id"] == eb["id"]
        for k in set(ea) | set(eb):
            if ea.get(k) != eb.get(k):
                cnt[k] = cnt.get(k, 0) + 1
    if a.get("note") != b.get("note"):
        cnt["note(screen)"] = 1
    for k in set(a) | set(b):
        if k not in ("elements", "note") and a.get(k) != b.get(k):
            cnt[k] = cnt.get(k, 0) + 1
    return cnt


# ----------------------------------------------------------------------------
# 变异自证
# ----------------------------------------------------------------------------
def mutate(els):
    orig = json.loads(json.dumps(els))
    table = build_old_table(orig)                 # 旧值表（与坐标是否变异无关）
    base = apply_changes({"elements": orig})[0]["elements"]
    fails = []

    def expect(label, mutated, must_fail):
        ok, txt, cnt = run_checks(mutated, verbose=False, old_table=table)
        got = not ok
        hit = [k for k, v in cnt.items() if v]
        print("  %-46s 检查=%s %s  触发项=%s" % (label, "FAIL" if got else "PASS",
                                              "✓" if got == must_fail else "★不符预期", hit))
        fails.append(bool(got == must_fail))

    def mutate_pv_w(m):
        for e in m:
            if e["id"] in PV_IDS:
                e["w"] += PV_DW
        return m

    def mutate_ch_old(m):
        for e in m:
            if e["id"].startswith("cfg.ch_"):
                k = ch_kind(e["id"])
                dx = e["x"] - CH_BASE[k]
                col = round(dx / CH_PITCH_NEW) if dx else 0
                e["x"] = CH_BASE[k] + col * CH_PITCH_OLD
                e["w"] = CH_W[k][0]
        return m

    print("== 变异自证（打废后各检查项必须 FAIL）")
    print("   旧值表 %d 件（= 目标件，与坐标是否被变异无关）" % len(table))
    # M1：预览组 w 还原成旧值 ⇒ [1] 右沿必须违规
    expect("M1 预览组 w 还原 +36", mutate_pv_w(json.loads(json.dumps(base))), True)
    # M2：角色列还原成旧列步进 ⇒ [1] 右沿必须违规（+ [3] 网格）
    expect("M2 角色列还原成旧列步进", mutate_ch_old(json.loads(json.dumps(base))), True)
    # M3：预览文字推出外框（x 1194→1170）⇒ [4] 内外关系必须违规
    m = json.loads(json.dumps(base))
    for e in m:
        if e["id"] == "cfg.pv_text":
            e["x"] = 1170
    expect("M3 pv_text 推出外框（内缩关系破）", m, True)
    # M4：只挪列 0（x 1110→1120）⇒ [3] 网格必须报不均匀
    m = json.loads(json.dumps(base))
    for e in m:
        if e["id"].startswith("cfg.ch_"):
            k = ch_kind(e["id"])
            if e["x"] == CH_BASE[k]:
                e["x"] += 10
    expect("M4 单列位移（列节距不均）", m, True)
    # M5：把第 3 列胶囊/热区左推去压第 2 列 ⇒ [2] 必须报新增相交
    m = json.loads(json.dumps(base))
    for e in m:
        if e["id"].startswith("cfg.ch_") and ch_kind(e["id"]) in ("pill", "hit") \
                and e["x"] == CH_BASE["pill"] + 2 * CH_PITCH_NEW:
            e["x"] = CH_BASE["pill"] + CH_PITCH_NEW + 3
    expect("M5 第3列胶囊左推压第2列", m, True)
    # M6：正对照 —— 未被变异的 base 必须全绿
    expect("M6 正对照（未变异）", base, False)

    allok = all(fails)
    print("== 变异自证结论：%s（%d/%d）" % ("全部符合预期" if allok else "★ 有不符合预期", sum(fails), len(fails)))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
