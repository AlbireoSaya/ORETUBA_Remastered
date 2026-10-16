# -*- coding: utf-8 -*-
r"""e2_patch_static_snapshot.py —— `ISSUE-20260929-05` E2 一次性补丁：

把 `工具\gen_flow_layout.py` 的内嵌静态快照 `STATIC_ELEMENTS_JSON` 改为
**删 18 件（12 `fc.mtab*` ＋ 6 `fc.fusen_*`）／加 6 件（`fc.mode_*`）**。

做法（为什么用脚本而不是手改）：
  · 该快照是 `json.dumps(els, ensure_ascii=False, indent=1)` 的**逐字产物**（已实测：round-trip 逐字节相同）
    ⇒ 用 json 读写可保证**除本批 18/6 件之外，其余 34 件的字节一律不变**（含键序与缩进）。
  · 落笔前先自证 round-trip 相同，再落笔；落笔后打印前后件数差与清点结果。

幂等：重复运行第二次会因「旧的 18 件已不在」而报错退出（不静默双改）。
"""
from __future__ import annotations

import json
import sys

GEN = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\工具\gen_flow_layout.py"
OPEN = 'STATIC_ELEMENTS_JSON = r"""'
CLOSE = '"""'

# ── 本批要删的 18 件 ────────────────────────────────────────────────
REMOVE = (
    ["fc.mtab%d%s" % (n, s) for n in (1, 2, 3, 4) for s in ("", "_tx", "_hit")]
    + ["fc.fusen_%s%s" % (k, s) for k in ("edit", "reset") for s in ("", "_tx", "_hit")]
)

# ── 本批要加的 6 件（逐字照接口冻结 §B；素材名以 E1 实际产出为准）──
ASSET_SRC = (
    "素材组产出（ISSUE-20260929-05 · E1）：`ui/x_ui_modetab_{off,over,press}.png` "
    "**180×60 RGBA ×3**（同一枚柔和白淡光的弱/强/实底三档）；"
    "**两个模式入口共用同一套 3 张**（形状一致，冻结 §D 允许复用、优先省件数）。"
)
SN = "state_assets"
TRI = {"normal": "ui/x_ui_modetab_off.png",
       "hover": "ui/x_ui_modetab_over.png",
       "pressed": "ui/x_ui_modetab_press.png"}


def glow(eid, x, group, note):
    return {
        "id": eid,
        "kind": "image",
        "z": 10,
        "visible_default": True,
        "asset": "ui/x_ui_modetab_off.png",
        "x": x, "y": 25, "w": 180, "h": 60,
        "opacity": 255,
        "source": ASSET_SRC,
        "note": note,
        SN: dict(TRI),
        "state_group": group,
    }


def tx(eid, x, sample, note):
    return {
        "id": eid,
        "kind": "text",
        "z": 20,
        "visible_default": True,
        "x": x, "y": 25, "w": 180, "h": 60,
        "font": {"size": 30, "bold": False, "color": "@palette.text_primary",
                 "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0,
                 "outline": True, "outline_color": "#000000", "outline_width": 2},
        "align": "center",
        "valign": "middle",
        "wrap": False,
        "max_lines": 1,
        "sample": sample,
        "note": note,
    }


def hit(eid, x, group, action, note):
    return {
        "id": eid,
        "kind": "hit",
        "z": 95,
        "visible_default": True,
        "x": x, "y": 25, "w": 180, "h": 60,
        "action": action,
        "label": "",
        "state_group": group,
        "font": {"size": 30, "bold": False, "color": "@palette.text_primary",
                 "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
        "align": "center",
        "note": note,
    }


_COMMON = (
    "★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——"
    "**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，"
    "在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**"
    "（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。"
    "几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；"
    "左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n"
    "· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，"
    "三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` "
    "⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n"
    "· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、"
    "`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，"
    "且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n"
    "· **动作** `%s`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，"
    "切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n"
    "· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**"
    "（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n"
    "· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠"
    "（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。"
)


def main():
    raw = open(GEN, encoding="utf-8", newline="").read()
    a = raw.index(OPEN)
    b = raw.index(CLOSE, a + len(OPEN))
    blob = raw[a + len(OPEN):b]
    els = json.loads(blob)

    # 落笔前自证：现快照 == json 重排（逐字节）⇒ 读写不会动其它元素
    if json.dumps(els, ensure_ascii=False, indent=1) != blob:
        raise SystemExit("[FAIL] 快照不是 `indent=1` 的 json 产物 ⇒ 拒绝用脚本改写（会动到其它字节）")

    ids = [e["id"] for e in els]
    missing = [i for i in REMOVE if i not in ids]
    if missing:
        raise SystemExit("[FAIL] 待删件不在快照里（可能已打过补丁）：%s" % missing)

    idx = ids.index("fc.mtab1")
    new6 = [
        glow("fc.mode_main_glow", 34, "mode_main",
             "模式入口「本篇集合」的**底光图**（三态承载者）。" + _COMMON % "flow_mode_main"),
        tx("fc.mode_main_tx", 34, "本篇集合",
           "模式入口「本篇集合」的**文字**（引擎绘制，30px / `bold:false` ⇒ 引擎默认字体族首位即**微软雅黑 Regular**"
           "（`layout\\_root.json` 的 `fonts.fallback_faces[0]`）；白字 ＋ 黑描边 2px ＋ 白淡光由底层 `_glow` 图给）。"
           "文字**不参与换态**（schema 不支持文字带 `state_assets`）。" + _COMMON % "flow_mode_main"),
        hit("fc.mode_main_hit", 34, "mode_main", "flow_mode_main",
            "模式入口「本篇集合」的**热区**（与底光图/文字同矩形 180×60，z95 最高 ⇒ 指针落在按钮任意位置都由它胜出，"
            "再经 `state_group:\"mode_main\"` 联动底层 `_glow` 换三态）。" + _COMMON % "flow_mode_main"),
        glow("fc.mode_frag_glow", 254, "mode_frag",
             "模式入口「番外故事」的**底光图**（三态承载者，与 `fc.mode_main_glow` 共用同一套 3 张素材）。"
             + _COMMON % "flow_mode_frag"),
        tx("fc.mode_frag_tx", 254, "番外故事",
           "模式入口「番外故事」的**文字**（引擎绘制；口径与 `fc.mode_main_tx` 逐字段相同，仅 `sample` 不同）。"
           "文字**不参与换态**。" + _COMMON % "flow_mode_frag"),
        hit("fc.mode_frag_hit", 254, "mode_frag", "flow_mode_frag",
            "模式入口「番外故事」的**热区**（同矩形 180×60 / z95；`state_group:\"mode_frag\"` 与同组 `_glow` 联动）。"
            + _COMMON % "flow_mode_frag"),
    ]

    keep = []
    for i, e in enumerate(els):
        if i == idx:
            keep.extend(new6)       # 插在原 `fc.mtab1` 的位置（声明序 ⇒ 与旧页签同段）
        if e["id"] in REMOVE:
            continue
        keep.append(e)

    new_blob = json.dumps(keep, ensure_ascii=False, indent=1)
    out = raw[:a + len(OPEN)] + new_blob + raw[b:]
    open(GEN, "w", encoding="utf-8", newline="").write(out)

    print("[ok] 快照：%d → %d 件（−%d ＋%d）"
          % (len(els), len(keep), len(REMOVE), len(new6)))
    print("[ok] 清点：mtab 残留 %d ｜ fusen 残留 %d ｜ mode 入表 %d"
          % (sum(1 for e in keep if e["id"].startswith("fc.mtab")),
             sum(1 for e in keep if e["id"].startswith("fc.fusen")),
             sum(1 for e in keep if e["id"].startswith("fc.mode"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
