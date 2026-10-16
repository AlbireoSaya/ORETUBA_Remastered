# -*- coding: utf-8 -*-
r"""M35b：把用户导出的「图标 + 文字」绑成一组（标题屏）。

用户 2026-09-22 要求：
  「把图标和文字按钮的鼠标悬停检测绑定到一起，当鼠标悬停到图标和文字任意一者（或两者同时）时，
    同步展示它们的悬停形态。」

■ 做法
  · 图标热区 `title.menu_hit_N` 与对应的文字图 `title.menu_txt_<key>` **同属一个 `state_group`**
    （`title.menu_<key>`）⇒ 鼠标落在任意一者上，两者**同时**换态（组绑定实现见
    `krkr/game/ui_widget.tjs` 的 uiWidgetStateFlags 与 `复刻/replica.js` 的 groupSync）。
  · 文字图从「编辑器自动命名的 `new.<素材名>`」改为语义 id `title.menu_txt_<key>`，
    并挂上 `state_assets`（normal = 合成层常态、hover = 合成层悬停版）。
  · **不给 pressed**：用户 2026-09-22 决定不做点击态图（`_press` 素材已删），
    按「缺键逐级回落」按下时显示 hover 图 —— 与图标热区现有做法一致
    （图标的 pressed 也指向 `_on`）。

■ 幂等：重复运行结果一致（按 id/asset 定位，不依赖既有顺序）。
"""
import os, io, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCREEN = os.path.join(UI, "layout", "screens", "01_title.json")

# 菜单项顺序：(热区 id, action, 素材 key, 中文)
ITEMS = [
    ("title.menu_hit_1", "game_start",      "start",     "开始游戏"),
    ("title.menu_hit_2", "game_continue",   "continue",  "继续游戏"),
    ("title.menu_hit_3", "open_load",       "load",      "读取存档"),
    ("title.menu_hit_4", "open_flowchart",  "flowchart", "流程图"),
    ("title.menu_hit_5", "open_config",     "config",    "设置"),
    ("title.menu_hit_6", "open_gallery",    "gallery",   "画廊"),
    ("title.menu_hit_7", "quit_game",       "exit",      "离开游戏"),
]


def main():
    d = json.load(io.open(SCREEN, encoding="utf-8"))
    els = d["elements"]
    by_id = {e.get("id"): e for e in els}

    # 1) 取出编辑器放的那 7 张文字图（id 形如 new.x_ui_btntxt2c_<key>），按 y 与菜单项对齐
    placed = {}
    for e in els:
        i = str(e.get("id", ""))
        if not i.startswith("new.x_ui_btntxt2c_"):
            continue
        key = i[len("new.x_ui_btntxt2c_"):]
        placed[key] = e
    missing = [k for _h, _a, k, _c in ITEMS if k not in placed]
    if missing:
        print("✗ 导出里缺这些文字图：%s —— 请先在编辑器里摆好再跑" % missing)
        return 1

    # 2) 图标热区加 state_group；并校验文字图 y 与热区对齐
    report = []
    for idx, (hid, action, key, cn) in enumerate(ITEMS):
        hit = by_id.get(hid)
        if hit is None:
            print("✗ 找不到热区 %s" % hid); return 1
        grp = "title.menu_" + key
        if hit.get("state_group") != grp:
            report.append("热区 %s 接入组 %s" % (hid, grp))
        hit["state_group"] = grp
        img = placed[key]
        if round(float(img.get("y", -1))) != round(float(hit.get("y", -2))):
            print("⚠ %s 的 y=%s 与热区 y=%s 不齐（仍按导出位置保留，请核对）"
                  % (key, img.get("y"), hit.get("y")))

    # 3) 文字图改名 + 挂 state_assets + 组绑定；z 归一到 96..102（按菜单顺序）
    new_texts = []
    for idx, (hid, action, key, cn) in enumerate(ITEMS):
        img = placed[key]
        base = "ui/x_ui_btntxt2c_%s.png" % key
        img["id"] = "title.menu_txt_" + key
        img["kind"] = "image"
        img["z"] = 96 + idx
        img["asset"] = base
        img["state_group"] = "title.menu_" + key
        img["state_assets"] = {"normal": base, "hover": "ui/x_ui_btntxt2c_%s_on.png" % key}
        img["source"] = "用户 2026-09-22 在 UI 布局编辑器（M35）摆放；M35b 接入 state_group 与悬停态"
        img["note"] = ("标题菜单文字「%s」（第 %d 项）。与图标热区 %s **同属 state_group「%s」**"
                       "⇒ 鼠标落在图标或文字任意一者上、或两者同时，两者**同步**进入悬停形态。"
                       "hover 用 `x_ui_btntxt2c_%s_on.png`（+白晕的悬停版）；"
                       "**无 pressed 图**（用户 2026-09-22 定不做点击态图）⇒ 按下按缺键回落显示 hover。"
                       % (cn, idx + 1, hid, img["state_group"], key))
        new_texts.append(img)

    # 4) 重排：bg / logo / hits / texts / copyright / 其余
    #    ⚠️ 必须按**对象身份**排除已处理的元素——第 3 步已把文字图改名（不再匹配 `new.` 前缀），
    #       若按 id 前缀排除会把它们当成「其余」再加一遍 ⇒ id 重复（v1 踩过，gen_layout 报 7 条硬错误）。
    head = [e for e in els if e.get("id") in ("title.bg", "title.logo")]
    hits = [by_id[hid] for hid, _a, _k, _c in ITEMS]
    tail = [e for e in els if e.get("id") == "title.text_copyright"]
    used = set()
    for e in head + hits + new_texts + tail:
        used.add(id(e))
    others = [e for e in els if id(e) not in used]
    d["elements"] = head + hits + new_texts + tail + others
    d["owner"] = "M34"
    d["note"] = d.get("note", "") + (
        "\n★ **M35b（2026-09-22）· 标题菜单「图标 + 文字」组绑定**（用户要求）："
        "7 个图标热区与 7 张文字图同属 `state_group: \"title.menu_<key>\"` ⇒ "
        "鼠标落在任意一者上（或两者同时）两者**同步**换态；文字图的 `state_assets` = "
        "合成层常态 / 合成层 `_on`（悬停）。文字位置由**用户在编辑器里摆放**"
        "（导出件见 `编辑器修改区\\01_title.json`），文字图 id 由编辑器自动名 `new.*` "
        "改成语义名 `title.menu_txt_<key>`。"
        "\n★ **给后续编辑者的提醒**：在编辑器里继续改本屏前，请先**刷新页面/点「重载」**，"
        "让它从更新后的 `ui_layout.js` 读入（否则旧会话里没有 `state_group` 与文字态图，"
        "导出会把这两项覆盖掉）。")

    io.open(SCREEN, "w", encoding="utf-8", newline="\n").write(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("已改写 %s" % SCREEN)
    print("  组绑定：7 组（title.menu_<key>），每组 = 1 个图标热区 + 1 张文字图")
    print("  文字图 state_assets：normal + hover（无 pressed，按用户决定）")
    for line in report:
        print("  · " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
