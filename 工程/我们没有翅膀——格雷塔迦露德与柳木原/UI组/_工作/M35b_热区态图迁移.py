# -*- coding: utf-8 -*-
r"""M35b：把「热区拉伸态图」改成「热区只当地标 + 态图挪到 1:1 的 image 上」（用户 2026-09-22 裁定）。

■ 缺陷（一审顺带发现，M34 系统性做法，非本轮引入）
  10 个 `hit` 的热区矩形取自《交汇协奏曲》PSB 的 **`#rects/*` 交互区**（比按钮美术大得多，
  例如回溯屏 `#rects/speaker` = 1222×224「整条消息行可点」），而 `state_assets` 放的是小图标，
  于是引擎按热区矩形把它**拉伸**绘制 —— 最大 48.9×8.3（回溯屏喇叭），最小 1.4×1.5（系统条）。
  涂抹由此而来。**热区矩形本身是对的**（忠实复刻），错的是「让热区去画美术」。

■ 修法（用户裁定：保热区 + 态图挪到 1:1 image）
  每一对 = 「1 个 hit（PSB 热区）+ 1 个同矩形的 image（同一张美术）」：
    · hit：**移走 `state_assets`**（退回纯热区，不再画美术）+ 加 `state_group`
    · image：**接收那三态** + 加同一个 `state_group`
  ⇒ 美术由 image 在 1:1/九宫格口径下正确绘制；热区仍是原来那么大（**交互范围不变**）；
     两者用组绑定联动 ⇒ 悬停/按下热区任意处，美术同步换态（见 replica.js / ui_widget.tjs 规则⑥）。
  **零新增美术。**

■ 配对规则（**两级，缺一不可**；实测两轮才定下）
  ① 先按**矩形完全相等**：确认框的「是」「否」共用同一张 `x_ui_btn_l_off.png`，
     **单按图名会错配**（「否」会被配到「是」的 image 上）；
  ② 配不上再按**图名唯一**：多数同类的 image 是按**美术自己的 PSB 坐标**摆的
     （如回溯屏喇叭 x349 y138 w25 h35），与热区矩形（PSB 交互区 1222×224）**本来就不同**，
     按矩形配不上，此时若屏内只有一件 image 用同一张图，就是它。
  （本 docstring 曾写成「按矩形、不能按图名」单一规则，与代码两级实况不符，已订正。）
  脚本对每对断言「恰好一个匹配」，配不上即拒绝迁移。

■ 选择支（choices）特殊
  它只有一个 `ch.sel`（画第 1 行）+ 三个 hit 各自拉伸画 —— 行 2/3 **没有** companion image。
  故需把 `ch.sel` 改名为 `ch.bg_1` 并**新增 `ch.bg_2` / `ch.bg_3`**（同矩形、九宫格、带三态），
  三个 hit 退回纯热区 + 组绑定。
"""
import os, io, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCREENS = os.path.join(UI, "layout", "screens")

# (屏文件, 热区 id, 组名)  —— companion image 由「矩形完全相等」在运行时自动配对
PAIRS = [
    ("21_confirm.json",  "cf.hit_yes",       "confirm.yes"),
    ("21_confirm.json",  "cf.hit_no",        "confirm.no"),
    ("25_config.json",   "cfg.mute_hit",     "config.mute"),
    ("25_config.json",   "cfg.replay_hit",   "config.replay"),
    ("26_backlog.json",  "bl.spk_hit",       "backlog.spk"),
    ("32_flowchart.json", "fc.close_hit",    "flowchart.close"),
    ("34_sysbar.json",   "sysbar.hit_snap",  "sysbar.snap"),
    ("34_sysbar.json",   "sysbar.hit_hide",  "sysbar.hide"),
    ("34_sysbar.json",   "sysbar.hit_vreplay", "sysbar.vreplay"),
    ("37_dress.json",    "dr.hit_reset",     "dress.reset"),
]

# choices 屏：把 ch.sel 拆成 per-row 的 ch.bg_1/2/3（行 2/3 是新增）
CHOICES = ("36_choices.json", ["ch.hit_1", "ch.hit_2", "ch.hit_3"], "ch.bg_%d", "choices.%d")


def load(f):
    return json.load(io.open(os.path.join(SCREENS, f), encoding="utf-8"))


def save(f, d):
    io.open(os.path.join(SCREENS, f), "w", encoding="utf-8", newline="\n").write(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n")


def same_rect(a, b):
    return all(abs(float(a.get(k, 0)) - float(b.get(k, 0))) < 0.51 for k in ("x", "y", "w", "h"))


def migrate_pair(els, hit_id, group, log):
    hit = next((e for e in els if e.get("id") == hit_id), None)
    if hit is None:
        log.append("  ✗ 找不到热区 %s" % hit_id); return False
    sa = hit.get("state_assets")
    if not sa:
        log.append("  – %s 已无态图（已迁移过 / 或本是纯热区）" % hit_id)
        return True
    # ★ 配对规则（实测两轮才定下）：
    #   ① **先按「矩形完全相等」**——确认框「是/否」共用同一张 `x_ui_btn_l_off.png`，
    #      按图名配会把「否」错配到「是」的 image 上；按矩形则精确命中 cf.no ✓
    #   ② 再按**图名唯一**——多数同类的 image 是按**美术自己的 PSB 坐标**摆的（如回溯屏喇叭
    #      x349 y138 w25 h35），与热区矩形（PSB 的交互区 1222×224）**本来就不同**，按矩形配不上。
    #      此时若该屏内只有一件 image 用同一张图，就是它。
    def cands_of(pred):
        return [e for e in els if e.get("kind") == "image" and pred(e)]
    img = None
    c1 = cands_of(lambda e: same_rect(e, hit))
    if len(c1) == 1:
        img = c1[0]; how = "矩形相等"
    else:
        c2 = cands_of(lambda e: e.get("asset") == sa.get("normal")
                      and not e.get("state_assets"))
        if len(c2) == 1:
            img = c2[0]; how = "图名唯一"
        else:
            # 幂等：若已迁移过（companion 已带同组态图），直接用那个
            c3 = cands_of(lambda e: e.get("asset") == sa.get("normal")
                          and e.get("state_group") == group)
            if len(c3) == 1:
                log.append("  – %s 已迁移过（companion=%s）" % (hit_id, c3[0]["id"])); return True
            log.append("  ✗ %s 配对失败：同矩形 %d 件、同图名 %d 件（期望恰好 1）"
                       % (hit_id, len(c1), len(c2)))
            return False

    img["state_assets"] = sa
    img["state_group"] = group
    img["note"] = (img.get("note", "") + " ★ M35b：接收原热区 `%s` 的三态图（热区矩形是 PSB 的"
                   "交互区，比美术大得多，由热区画会拉伸涂抹）——美术在 1:1/九宫格口径下画，"
                   "与热区用 state_group「%s」联动。" % (hit_id, group))
    del hit["state_assets"]
    hit["state_group"] = group
    hit["note"] = (hit.get("note", "") + " ★ M35b：**退回纯热区**（不再持有美术，避免按热区矩形拉伸"
                   "绘制）；三态图改由同矩形的 image `%s` 绘制，两者 state_group「%s」联动。"
                   % (img["id"], group))
    log.append("  ✓ %s ⇄ %s（组 %s，配对依据：%s）" % (hit_id, img["id"], group, how))
    return True


def migrate_choices(log):
    f, hit_ids, pat, gpat = CHOICES
    d = load(f)
    els = d["elements"]
    sel = next((e for e in els if e.get("id") == "ch.sel"), None)
    if sel is None:
        if any(e.get("id") == "ch.bg_1" for e in els):
            log.append("  – choices 已迁移过（ch.bg_1 存在）"); return True
        log.append("  ✗ choices 既无 ch.sel 也无 ch.bg_1"); return False
    sel["id"] = "ch.bg_1"
    # 为行 2/3 复制出 ch.bg_2 / ch.bg_3（同矩形、同九宫格口径）
    made = [sel]
    for i in (2, 3):
        h = next(e for e in els if e.get("id") == hit_ids[i - 1])
        nu = json.loads(json.dumps(sel))
        nu["id"] = pat % i
        nu["x"], nu["y"], nu["w"], nu["h"] = h["x"], h["y"], h["w"], h["h"]
        nu["note"] = ("选择支行底（第 %d 行，M35b 新增：原结构只有第 1 行有 image，"
                      "行 2/3 全靠热区拉伸绘制）" % i)
        idx = els.index(h)
        els.insert(idx, nu)
        made.append(nu)
    for i, hid in enumerate(hit_ids, 1):
        if not migrate_pair(els, hid, gpat % i, log):
            return False
    for i, m in enumerate(made, 1):
        m["note"] = (m.get("note", "") + " ★ M35b：持有选择支三态图（normal/hover/pressed），"
                     "与热区 `%s` 用 state_group「%s」联动。" % (hit_ids[i - 1], gpat % i))
    save(f, d)
    log.append("  ✓ choices：ch.sel → %s，并新增 %s" % (pat % 1, "、".join(pat % i for i in (2, 3))))
    return True


def main():
    log = []
    by_file = {}
    for f, hid, grp in PAIRS:
        by_file.setdefault(f, []).append((hid, grp))
    ok = True
    for f, items in by_file.items():
        log.append("== %s" % f)
        d = load(f)
        for hid, grp in items:
            if not migrate_pair(d["elements"], hid, grp, log):
                ok = False
        save(f, d)
    log.append("== %s" % CHOICES[0])
    d = load(CHOICES[0])
    if not migrate_choices(log):
        ok = False
    print("\n".join(log))
    if not ok:
        print("\n✗ 有失败项 —— 未全部迁移，请检查")
        return 1
    print("\n✓ 迁移完成（热区退回纯热区 + 态图挪到 1:1 image + 组绑定）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
