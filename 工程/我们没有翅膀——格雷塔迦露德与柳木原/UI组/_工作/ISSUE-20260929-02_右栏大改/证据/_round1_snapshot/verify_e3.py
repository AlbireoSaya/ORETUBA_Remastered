# -*- coding: utf-8 -*-
r"""verify_e3.py —— ISSUE-20260929-02 · E3（载入屏 + 文档）交付自检（可重跑）

查什么（全部为「断言 + 退出码」，非打印读数）：
  A. 屏数据 `layout/screens/22_loading.json`：`ld.bg` 已删、余 2 件，
     且与 `git show HEAD:<file>` 逐字段比对 ⇒ **只有 ld.bg 被删、其余两件零改动**。
  B. 文档（`UI组交接编程组.md` §四·补 ／ `流程图系统_版式规范.md` §〇.2 等）里出现的
     **每一个元素 id / 动作名 / flag 名 / 素材文件名 / 几何数字**，逐条与
     **E2 已落盘的生成器** `工具/gen_flow_layout.py` 的 `STATIC_ELEMENTS_JSON` 对照。
  C. 退场 12 件**确已不在**生成器的静态元素快照里；素材文件**仍在**。
  D. 新素材文件**已在库**（E1）。
  E. `ld.bg` 用的素材 `ui/x_ui_backlog_bg.png` **仍在**，且在 `layout/screens/*.json` 中**零元素引用**。

用法（幂等、只读）：
    cd "工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260929-02_右栏大改/证据/verify_e3.py"
退出码 0 = 全通过。
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
SCR = os.path.join(UI, "layout", "screens")
GEN = os.path.join(UI, "工具", "gen_flow_layout.py")
DOC_A = os.path.join(UI, "UI组交接编程组.md")
DOC_B = os.path.join(UI, "流程图系统_版式规范.md")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")

fails: list[str] = []
oks = 0

GEOM = ("x", "y", "w", "h", "z")

# E3 文档里写死的元素契约（id → x,y,w,h,z + 关键字段）——**必须与生成器逐字一致**
EXPECT = {
    "fc.play_win":     (1448, 214, 380, 300, 6),
    "fc.play_view":    (1454, 220, 368, 288, 7),
    "fc.p_title":      (1416, 536, 443, 73, 6),
    "fc.p_title_tx":   (1428, 546, 419, 40, 25),
    "fc.p_text":       (1425, 631, 422, 171, 6),
    "fc.p_text_tx":    (1437, 637, 398, 159, 25),
    "fc.p_message":    (1425, 824, 422, 171, 6),
    "fc.p_message_tx": (1437, 830, 398, 159, 25),
    "fc.pbkick":       (1578, 304, 119, 119, 20),
    "fc.pbkick_pause": (1578, 304, 119, 119, 20),
    "fc.pbkick_hit":   (1575, 301, 125, 125, 95),
    "fc.smallmap":     (1416, 190, 443, 829, 5),
}
RETIRED = ["fc.mapview", "fc.pbk_panel", "fc.p_player", "fc.p_player_tx"] + \
          ["fc.mini%d" % i for i in range(1, 9)]
NEW_ASSETS = ["x_ui_playwin_bg.png", "x_ui_pbkick_pause_off.png",
              "x_ui_pbkick_pause_over.png", "x_ui_pbkick_pause_on.png"]


def check(cond, msg):
    global oks
    if cond:
        oks += 1
        print("  PASS  " + msg)
    else:
        fails.append(msg)
        print("  FAIL  " + msg)


def static_elements():
    """生成器 `STATIC_ELEMENTS_JSON`（右栏这些件是它的内嵌静态快照）。"""
    src = io.open(GEN, encoding="utf-8").read()
    m = re.search(r'STATIC_ELEMENTS_JSON\s*=\s*r?"""(.*?)"""', src, re.S)
    if not m:
        raise SystemExit("[FAIL] 生成器里找不到 STATIC_ELEMENTS_JSON")
    els = json.loads(m.group(1))
    return {e["id"]: e for e in els}, src


def screen_elements():
    """屏数据 `layout/screens/32_flowchart.json`（**E2 落盘后即为此为准**）。"""
    p = os.path.join(SCR, "32_flowchart.json")
    d = json.load(io.open(p, encoding="utf-8"))
    return {e["id"]: e for e in d["elements"]}, d


def bounded_pick(el, keys):
    """只取关心字段，便于两源逐字段比对。"""
    return {k: el.get(k) for k in keys}


CMP_KEYS = ("kind", "z", "x", "y", "w", "h", "asset", "dynamic", "vis_flag",
            "vis_when", "action", "valign", "wrap", "max_lines", "sample",
            "state_assets", "font")


def git_show_head(relpath_from_ui):
    """取 HEAD 版本内容。注意 `git show <rev>:<path>` 的 path 是**仓库根相对**（不是 cwd 相对）。"""
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                         capture_output=True, text=True, encoding="utf-8").stdout.strip()
    full = os.path.join(UI, relpath_from_ui.replace("/", os.sep))
    rootrel = os.path.relpath(full, top).replace("\\", "/")
    r = subprocess.run(["git", "-c", "core.quotepath=false", "show", "HEAD:" + rootrel],
                       cwd=top, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print("      （git 取 HEAD 失败：%s）" % (r.stderr or "").strip()[:200])
        return None
    return r.stdout


def rel(p):
    return os.path.relpath(p, UI).replace("\\", "/")


def main():
    print("=" * 78)
    print("verify_e3.py · ISSUE-20260929-02 · E3（载入屏 + 文档）交付自检")
    print("  UI组 = %s" % UI)
    print("=" * 78)

    # ── A. 屏数据 ──────────────────────────────────────────────────
    print("\n### A. `layout/screens/22_loading.json`")
    now = json.load(io.open(os.path.join(SCR, "22_loading.json"), encoding="utf-8"))
    ids = [e["id"] for e in now["elements"]]
    check(ids == ["ld.dim", "ld.text"], "元素恰为 ['ld.dim','ld.text']（实测 %s）" % ids)
    check(all(e["id"] != "ld.bg" for e in now["elements"]), "`ld.bg` 已删除")

    head_txt = git_show_head("layout/screens/22_loading.json")
    check(head_txt is not None, "能取到 HEAD 版本的 22_loading.json（供逐字段比对）")
    if head_txt:
        old = json.loads(head_txt)
        old_by = {e["id"]: e for e in old["elements"]}
        new_by = {e["id"]: e for e in now["elements"]}
        check(set(old_by) - set(new_by) == {"ld.bg"},
              "相对 HEAD：**唯一被删的元素是 ld.bg**（差集 %s）" % (set(old_by) - set(new_by)))
        check(set(new_by) - set(old_by) == set(),
              "相对 HEAD：**没有新增元素**（差集 %s）" % (set(new_by) - set(old_by)))
        for eid in ("ld.dim", "ld.text"):
            check(type(old_by[eid]) is type(new_by[eid]) and old_by[eid] == new_by[eid],
                  "`%s` 与 HEAD **逐字段完全相同**（一个字段未改）" % eid)

    # ── B. 文档 ↔ 数据（**两源**：生成器静态快照 ＋ 屏数据）────────────
    print("\n### B. 文档 ↔ 数据 逐条对照（两源：生成器 STATIC_ELEMENTS_JSON ＋ 屏数据 32_flowchart.json）")
    st, src = static_elements()
    scr_el, scr_obj = screen_elements()
    landed = "fc.play_win" in scr_el
    print("  （屏数据落盘状态：%s；元素 %d 件）" % ("**已落盘**" if landed else "尚未重跑", len(scr_obj["elements"])))
    docA = io.open(DOC_A, encoding="utf-8").read()
    docB = io.open(DOC_B, encoding="utf-8").read()

    sources = [("生成器 STATIC_ELEMENTS_JSON", st)]
    if landed:
        sources.append(("屏数据 32_flowchart.json", scr_el))

    for label, S in sources:
        for eid, (x, y, w, h, z) in EXPECT.items():
            e = S.get(eid)
            check(e is not None, "[%s] 存在 `%s`" % (label, eid))
            if not e:
                continue
            check((e["x"], e["y"], e["w"], e["h"], e["z"]) == (x, y, w, h, z),
                  "[%s] `%s` 几何＝文档所记 %s（实取 %s）"
                  % (label, eid, (x, y, w, h, z), (e["x"], e["y"], e["w"], e["h"], e["z"])))
        still = [i for i in RETIRED if i in S]
        check(still == [], "[%s] 12 件退场元素零残留（残留 %s）" % (label, still))

    # 两源逐字段一致（防止「生成器改了、屏数据没重跑」这类中间态被当成通过）
    if landed:
        for eid in EXPECT:
            ga, gb = bounded_pick(st[eid], CMP_KEYS), bounded_pick(scr_el[eid], CMP_KEYS)
            check(ga == gb, "两源逐字段一致：`%s`（生成器 vs 屏数据）" % eid)
        check(scr_obj.get("flags_default", {}).get("fc_replay") == "play",
              "屏级 `flags_default.fc_replay` = \"play\"（屏数据实测）")
        check(scr_obj.get("flags_default", {}).get("fc_layer") == "main",
              "屏级 `flags_default.fc_layer` = \"main\"（保留）")

    # 文档侧的几何字符串（抽 vacuous：仅对已比对源均应出现）
    for eid, (x, y, w, h, z) in EXPECT.items():
        token = "(%d, %d, %d×%d)" % (x, y, w, h)
        check(token in docA, "文档（编程组交接 §四·补）含该几何字符串 `%s`" % token)

    P = scr_el if landed else st      # 主源：屏数据落盘后以屏数据为准

    # 三个文字槽的字体/排版字段
    for eid, valign, wrap, maxl in (("fc.p_title_tx", "middle", False, 1),
                                    ("fc.p_text_tx", "top", True, 5),
                                    ("fc.p_message_tx", "top", True, 5)):
        e = P[eid]
        f = e["font"]
        check(f["color"] == "@palette.text_primary", "`%s` 字色 = @palette.text_primary（白字）" % eid)
        check(f.get("outline") is True and f.get("outline_color") == "#000000"
              and f.get("outline_width") == 2 and f.get("shadow") is False,
              "`%s` 描边 = outline:true / #000000 / 2px / shadow:false" % eid)
        check(f["size"] == 24 and f["bold"] is True, "`%s` 字号 24 / bold 保持" % eid)
        check(e["valign"] == valign and e["wrap"] is wrap and e["max_lines"] == maxl,
              "`%s` valign/wrap/max_lines = %s/%s/%d" % (eid, valign, wrap, maxl))

    # 播放/暂停键
    pb, ps = P["fc.pbkick"], P["fc.pbkick_pause"]
    check(pb.get("vis_flag") == "fc_replay" and pb.get("vis_when") == "play",
          "`fc.pbkick` vis_flag/vis_when = fc_replay/play")
    check(ps.get("vis_flag") == "fc_replay" and ps.get("vis_when") == "pause",
          "`fc.pbkick_pause` vis_flag/vis_when = fc_replay/pause")
    check(pb.get("state_assets") == {"normal": "ui/x_ui_pbkick_off.png",
                                    "hover": "ui/x_ui_pbkick_over.png",
                                    "pressed": "ui/x_ui_pbkick_on.png"},
          "`fc.pbkick` state_assets 三槽 = x_ui_pbkick_{off,over,on}")
    check(ps.get("state_assets") == {"normal": "ui/x_ui_pbkick_pause_off.png",
                                    "hover": "ui/x_ui_pbkick_pause_over.png",
                                    "pressed": "ui/x_ui_pbkick_pause_on.png"},
          "`fc.pbkick_pause` state_assets 三槽 = x_ui_pbkick_pause_{off,over,on}")
    check(P["fc.pbkick_hit"].get("action") == "flow_replay_toggle",
          "`fc.pbkick_hit` action = flow_replay_toggle")

    # 屏级 flag 初值（生成器常量）
    check(re.search(r'REPLAY_FLAG\s*=\s*"fc_replay"', src) is not None,
          "生成器 REPLAY_FLAG = \"fc_replay\"")
    check(re.search(r'REPLAY_PLAY\s*=\s*"play"', src) is not None,
          "生成器 REPLAY_PLAY = \"play\"")
    check(re.search(r'flags_default\s*=\s*\{LAYER_FLAG:\s*LAYER_MAIN,\s*REPLAY_FLAG:\s*REPLAY_PLAY\}', src) is not None,
          "生成器 flags_default = {fc_layer: main, fc_replay: play}")
    check(re.search(r'STATIC_FLAG_EXEMPT\s*=\s*\{\s*"fc\.pbkick"\s*,\s*"fc\.pbkick_pause"\s*\}', src) is not None,
          "生成器 STATIC_FLAG_EXEMPT = {\"fc.pbkick\",\"fc.pbkick_pause\"}（与文档同名）")
    check("fc.pbkick_pause" in docA and "fc.play_btn_pause" not in docA,
          "文档用 `fc.pbkick_pause` 且**未出现** `fc.play_btn_pause`（与生成器一致；冻结书 §B.2 的写法未采用）")

    # dynamic
    pv = P["fc.play_view"]
    check(pv.get("asset") is None and pv.get("dynamic") == "flow_scene_frames",
          "`fc.play_view` asset:null + dynamic:\"flow_scene_frames\"")
    check("flow_scene_frames" in docA and "contain" in docA,
          "文档写明 dynamic 名与 contain 适配提醒")

    # ── C. 退场 12 件 ─────────────────────────────────────────────
    print("\n### C. 退场 12 件")
    still = [i for i in RETIRED if i in P]
    check(still == [], "12 件退场元素**均不在**主源（%s）里（残留 %s）"
          % ("屏数据" if landed else "生成器静态快照", still))
    check(all(("%s" % i) in docA for i in RETIRED), "文档列全 12 件退场 id")
    for fn in ("x_ui_replay_panel.png",):
        check(os.path.exists(os.path.join(ASSETS, fn)), "退场件素材仍在库：%s" % fn)

    # ── D. 新增素材（E1）─────────────────────────────────────────
    print("\n### D. 新增素材（E1 落盘）")
    for fn in NEW_ASSETS:
        p = os.path.join(ASSETS, fn)
        check(os.path.exists(p), "素材已在库：%s" % fn)
        if os.path.exists(p):
            try:
                from PIL import Image
                im = Image.open(p)
                check(im.size == (119, 119) if "pbkick_pause" in fn else im.size == (380, 300),
                      "%s 尺寸 = %s（期望 %s）" % (fn, im.size,
                                                  (119, 119) if "pbkick_pause" in fn else (380, 300)))
                check(im.mode == "RGBA", "%s 模式 = RGBA（真 alpha）" % fn)
            except ImportError:
                print("  SKIP  PIL 不可用，跳过尺寸/模式核对：%s" % fn)

    # ── E. backlog_bg 素材与引用 ─────────────────────────────────
    print("\n### E. `ui/x_ui_backlog_bg.png`")
    check(os.path.exists(os.path.join(ASSETS, "x_ui_backlog_bg.png")),
          "素材仍在库（保留不删）")
    refs = []
    for fn in sorted(os.listdir(SCR)):
        if not fn.endswith(".json") or fn == "_index.json":
            continue
        scr = json.load(io.open(os.path.join(SCR, fn), encoding="utf-8"))
        blob = json.dumps(scr.get("elements", []), ensure_ascii=False)
        if "x_ui_backlog_bg" in blob:
            refs.append(fn)
    check(refs == [], "全 screens/*.json 的**元素字段中零引用**（实测命中 %s；注：屏级 note 里的说明文字不计）" % refs)
    bl = json.load(io.open(os.path.join(SCR, "26_backlog.json"), encoding="utf-8"))
    check(bl["elements"][0].get("asset") == "ui/x_ui_psv_backlog_bg.png",
          "`26_backlog` 底图 = ui/x_ui_psv_backlog_bg.png（冻结书「仍被 26_backlog 引用」不成立）")
    check("26_backlog" in docA and "x_ui_psv_backlog_bg.png" in docA,
          "文档已写入该勘误")

    # ── F. 版式规范同步痕迹 ─────────────────────────────────────
    print("\n### F. `流程图系统_版式规范.md` 订正痕迹")
    check("〇.2" in docB, "新增 §〇.2 我方版本订正块")
    check(docB.count("【订正 · 20260929】") >= 5,
          "就地订正标记 【订正 · 20260929】 出现 %d 处（≥5）" % docB.count("【订正 · 20260929】"))
    for tok in ("fc.play_win", "fc.play_view", "fc.pbkick_pause", "fc_replay",
                "flow_replay_toggle", "x_ui_playwin_bg.png"):
        check(tok in docB, "版式规范含 `%s`" % tok)

    print("\n" + "=" * 78)
    print("PASS %d ｜ FAIL %d" % (oks, len(fails)))
    for m in fails:
        print("  ✗ " + m)
    print("结果：**%s**" % ("全部通过" if not fails else "不通过"))
    print("=" * 78)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
