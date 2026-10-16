# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · M1 鉴赏模式机制 —— **引擎巡演**（私有运行目录版）+ 判词断言

■ 为什么需要本脚本
  `krkr\run_autotour.bat` 每次 `del savedata\*.*`，且并发会话可能共用 `临时\ui_run`
  ⇒ 本脚本自建 `临时\ui_run_m08\`，镜像 game + assets + runtime，只动自己那份日志与导图。

■ 数据依赖（M2/M3/M4 尚未落盘时）
  机制验收需要「页屏挂 gal_shell + CG 页 list 带 item_variants」。M2/M3/M4 的数据没落盘时，
  本脚本把**最小测试数据注入私有运行目录的 `ui_layout.tjs`**（`--inject`，默认开）：
    · 给 gallery/music/dress/replay 四个承载屏补 `attach:"gal_shell"`；
    · 把 gallery 屏替换成测试页（`gal.list` = 6×4 网格 / 30 栏 / 每栏 3 张差分 + 缩略图 + 左右键 + n/N）；
    · 补一个 `replay` 屏（情景回想）。
  **不写 `layout/screens/`、不改工作区任何交付文件**（只动 `临时\ui_run_m08\`）。
  数据落盘后跑 `--real`（不注入）复跑全量。

■ 判定
  逐条抓 `★M08TAB★` / `★M08PAGE★` / `★M08VAR★` / `★M08GUARD★`（PASS/FAIL），
  并断言负向判词 `★M08TAB-REJECT★` 出现。任一 FAIL / 缺判词 ⇒ 退出码 1。

■ 用法
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m08_gallery_tour.py            # 注入测试数据
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m08_gallery_tour.py --real     # 真实数据
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))                 # …\ISSUE-20260924-08_鉴赏模式\复现脚本
EVID = os.path.dirname(HERE)                                      # …\ISSUE-20260924-08_鉴赏模式
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))      # …\UI组
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))        # …\wt-qbicons
SRC = os.path.join(UI, "krkr")
TOOLS = os.path.join(UI, "工具")
# ★ 唯一运行目录（**并发安全**）：三个模块可能同时在跑引擎巡演，共用 `临时\ui_run` 会被锁目录、
#   日志互相覆盖（主代理 2026-09-24 登记的同源问题）⇒ 本脚本默认自建**带后缀**的目录，
#   `--rundir <名>` 可显式指定。**不动**别人的运行目录。
_RUNDIR_NAME = "ui_run_m08"
for _i, _a in enumerate(sys.argv[1:]):
    if _a == "--rundir" and _i + 2 <= len(sys.argv[1:]):
        _RUNDIR_NAME = sys.argv[1:][_i + 1]
RUN = os.path.join(WT, "临时", _RUNDIR_NAME)
SAVE = os.path.join(RUN, "runtime", "savedata")
LOG = os.path.join(SAVE, "krkr.console.log")

PAGE_SCREENS = ("gallery", "music", "dress", "replay")
GRID_COLS, GRID_ROWS = 6, 4
GRID_X, GRID_Y, ITEM_W, ITEM_H = 57, 187, 291, 166
COL_GAP = 12        # 列距；**行距同值**（list 的 gap 两轴共用，见 _schema.md）
ROW_GAP = COL_GAP
N_ROWS = 30                       # 30 栏 ⇒ 2 页（每页 24）
N_DIFF = 3                        # 每栏 3 张差分
THUMB_ASSETS = ["ui/x_ui_cfg_tab_on.png", "ui/x_ui_cfg_name_sel.png",
                "ui/x_ui_menuicon_gallery.png"]
BTN_OFF = "ui/x_ui_cfg_tab_off.png"
BTN_ON = "ui/x_ui_cfg_tab_on.png"


def make_test_screen():
    """最小测试页：6×4 网格 / 30 栏 / 每栏 N_DIFF 张差分（资产全部复用既有件，不新增素材）。"""
    frames = [[THUMB_ASSETS[(r + k) % len(THUMB_ASSETS)] for k in range(N_DIFF)]
              for r in range(N_ROWS)]
    el = [
        {"id": "gal.bg", "kind": "image", "z": 0, "visible_default": True,
         "asset": "ui/x_ui_cfg_frame.png", "x": 0, "y": 0, "w": 1920, "h": 1080,
         "opacity": 60, "nine": {"l": 20, "t": 20, "r": 20, "b": 20},
         "source": "ui/x_ui_cfg_frame.png（测试数据）",
         "note": "测试页底（注入用，非交付数据）"},
        {"id": "gal.list", "kind": "list", "z": 30, "visible_default": True,
         "orientation": "h",
         "x": GRID_X, "y": GRID_Y,
         "w": GRID_COLS * ITEM_W + (GRID_COLS - 1) * COL_GAP,
         "h": GRID_ROWS * ITEM_H + (GRID_ROWS - 1) * COL_GAP,   # 行距 = gap（两轴共用）
         "item_w": ITEM_W, "item_h": ITEM_H, "gap": COL_GAP,
         "max_cols": GRID_COLS, "max_rows": GRID_ROWS,
         "labels": ["测试栏 %d" % (i + 1) for i in range(N_ROWS)],
         "actions": [""] * N_ROWS,
         "font": {"size": 20, "bold": False, "color": "@palette.text_menu",
                  "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "align": "center",
         "scroll": {"mode": "page", "page_size": GRID_COLS * GRID_ROWS},
         # ⚠️ 测试页**刻意不放 `item_frame`**：九宫格件在两端本就不同（krkr uiWidgetNine 中格
         #   拉伸 vs HTML border-image），会把「机制自身差异」淹掉（实测：底部带 MAD 121/255）。
         #   `item_frame.state_assets` 与 `item_variants` 的**共存**另立断言（HTML 探针 coexistence.*）。
         "item_variants": {
             "frames": frames,
             "thumb": {"x": 8, "y": 8, "w": ITEM_W - 16, "h": ITEM_H - 46},
             "prev": {"key": "vprev", "x": 8, "y": ITEM_H - 34, "w": 48, "h": 26,
                      "asset": BTN_OFF,
                      "state_assets": {"normal": BTN_OFF, "hover": BTN_ON, "pressed": BTN_ON},
                      "action": "gallery_prev:%row%"},
             "next": {"key": "vnext", "x": ITEM_W - 56, "y": ITEM_H - 34, "w": 48, "h": 26,
                      "asset": BTN_OFF,
                      "state_assets": {"normal": BTN_OFF, "hover": BTN_ON, "pressed": BTN_ON},
                      "action": "gallery_next:%row%"},
             "text": {"x": 60, "y": ITEM_H - 34, "w": ITEM_W - 120, "h": 26,
                      "align": "center", "valign": "middle",
                      "font": {"size": 20, "bold": True, "color": "@palette.text_primary",
                               "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}},
             "edge": "clamp"
         },
         "source": "测试数据（注入，非交付）",
         "note": "测试网格列表（注入用）：6×4 = 24 栏/页，30 栏 ⇒ 2 页；每栏 3 张差分。"},
        {"id": "gal.page_tx", "kind": "text", "z": 40, "visible_default": True,
         "x": 57, "y": 920, "w": 600, "h": 60,
         "font": {"size": 26, "bold": False, "color": "@palette.text_menu",
                  "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "align": "left", "valign": "middle", "wrap": False, "max_lines": 1,
         "sample": "第 1 / 2 页（测试）",
         "note": "测试页页码（注入用）"},
        {"id": "gal.page_prev", "kind": "hit", "z": 96, "visible_default": True,
         "x": 700, "y": 920, "w": 190, "h": 60, "action": "gallery_page_prev",
         "label": "上一页", "align": "center",
         "font": {"size": 26, "bold": False, "color": "@palette.text_menu",
                  "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "note": "测试页翻页（注入用）"},
        {"id": "gal.page_next", "kind": "hit", "z": 96, "visible_default": True,
         "x": 910, "y": 920, "w": 190, "h": 60, "action": "gallery_page_next",
         "label": "下一页", "align": "center",
         "font": {"size": 26, "bold": False, "color": "@palette.text_menu",
                  "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
         "note": "测试页翻页（注入用）"},
    ]
    return {"id": "gallery", "title_cn": "CG 鉴赏（测试数据）", "owner": "M1",
            "attach": "gal_shell", "elements": el,
            "note": "**注入的测试页**（非交付数据）：供 ISSUE-20260924-08 的 M1 机制巡演使用。"}


def build(inject):
    if os.path.isdir(RUN):
        shutil.rmtree(RUN)
    shutil.copytree(os.path.join(SRC, "game"), os.path.join(RUN, "game"))
    for sub in ("assets",):
        s = os.path.join(SRC, sub)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(RUN, "game", sub))
    shutil.copytree(os.path.join(SRC, "runtime"), os.path.join(RUN, "runtime"),
                    ignore=shutil.ignore_patterns("savedata"))
    os.makedirs(SAVE, exist_ok=True)
    io.open(os.path.join(RUN, "game", "autotour.txt"), "w", encoding="utf-8").write("autotour\n")
    if inject:
        inject_layout(os.path.join(RUN, "game", "ui_layout.tjs"))
    print("私有运行目录已建：", RUN, "（inject=%s）" % inject)


def inject_layout(tjs_path):
    """把测试数据注入**私有副本**的 ui_layout.tjs（不改 layout/ 与生成物）。"""
    sys.path.insert(0, TOOLS)
    import gen_layout as G                                   # 只读复用其 TJS 字面量生成器
    tree = json.load(io.open(os.path.join(UI, "layout", "ui_layout.json"), encoding="utf-8"))
    sc = tree["screens"]
    sc["gallery"] = make_test_screen()
    for sid in PAGE_SCREENS:
        if sid not in sc:
            sc[sid] = {"id": sid, "title_cn": "（注入占位）" + sid, "owner": "M1",
                       "attach": "gal_shell",
                       "elements": [{"id": sid + ".bg", "kind": "rect", "z": 0,
                                     "visible_default": True, "x": 0, "y": 0,
                                     "w": 1920, "h": 1080,
                                     "color": "@palette.backdrop", "opacity": 200,
                                     "note": "注入占位屏（非交付数据）"}],
                       "note": "注入占位屏（非交付数据）"}
        sc[sid]["attach"] = "gal_shell"
    io.open(tjs_path, "w", encoding="utf-8").write(G.to_tjs(tree))
    print("已注入测试数据：gallery 测试页 + 四承载屏 attach=gal_shell + replay 占位屏")


def run_engine(wait_s=300):
    exe = os.path.join(RUN, "runtime", "tvpwin32.exe")
    assert os.path.exists(exe), "找不到引擎：" + exe
    p = subprocess.Popen([exe, os.path.join(RUN, "game")], cwd=os.path.join(RUN, "runtime"))
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < wait_s:
        time.sleep(3)
    if p.poll() is None:
        print("⚠️ %d 秒未自退，强制结束" % wait_s)
        p.kill()
    print("引擎退出码=%s，用时 %.0f 秒" % (p.poll(), time.time() - t0))


def read_log():
    raw = io.open(LOG, "rb").read()
    return raw.decode("utf-16-le", "replace").splitlines()


JUDGE_TAGS = ("★M08TAB★", "★M08PAGE★", "★M08VAR★", "★M08GUARD★", "★M08ATTACH★")


def pair_steps(lines):
    """把 `[UI][PNG] OK` 行与它前面最近的 `-> 下一步：<label>` 配对（导图顺序即步骤顺序）。"""
    cur, out = "", []
    for l in lines:
        m = re.search(r"-> 下一步：(.*?)\s+屏=", l)
        if m:
            cur = m.group(1).strip()
        if "[UI][PNG] OK" in l:
            out.append((os.path.basename(l.strip().split()[-1]), cur))
    return out


def strip_stats(png, box):
    """外壳页签条区域的**非背景占比**（引擎自导 PNG 的绘制见证）。"""
    from PIL import Image
    from collections import Counter
    im = Image.open(png).convert("RGBA")
    crop = im.crop(box)
    px = crop.load()
    w, h = crop.size
    c = Counter(px[i, j][:3] for i in range(0, w, 2) for j in range(0, h, 2))
    bg, bgn = c.most_common(1)[0]
    tot = sum(c.values())
    return bg, bgn / tot, (tot - bgn) / tot


# 外壳页签条所在区域（39_gal_shell.json 的 gs.strip：27,30 920×52，向外留 4px 余量）
STRIP_REGION = (23, 26, 951, 86)


def main():
    inject = "--real" not in sys.argv[1:]
    print("运行目录：", RUN)
    build(inject)
    run_engine()
    lines = read_log()
    io.open(os.path.join(EVID, "引擎巡演日志_原始.txt"), "w", encoding="utf-8").write(
        "\n".join(lines))

    print("\n===== M1 鉴赏机制判词（★M08*★）=====")
    judged, rejects = [], []
    for l in lines:
        if any(t in l for t in JUDGE_TAGS):
            # 只取判词本体（Debug.message 前缀可能带 [UI][REJECT] 等）
            idx = min([l.index(t) for t in JUDGE_TAGS if t in l])
            judged.append(l[idx:])
    for l in lines:
        if "★M08" in l and "-REJECT★" in l:
            idx = l.index("★M08")
            rejects.append(l[idx:])
    for j in judged:
        print("  " + j[:1400])
    print("\n----- 负向判词（★M08…-REJECT★）-----")
    seen = set()
    for r in rejects:
        if r in seen:
            continue
        seen.add(r)
        print("  " + r[:260])

    # ---- 外壳在四个承载屏下的**绘制见证**（引擎自导 PNG 的页签条区域非背景占比） ----
    pairs = pair_steps(lines)
    attach_shots = [(n, lab) for n, lab in pairs if "外壳复用" in lab]
    print("\n----- attach 四承载屏绘制见证（页签条区域 %s）-----" % (STRIP_REGION,))
    strip_lines = []
    for n, lab in attach_shots:
        p = os.path.join(SAVE, n)
        if not os.path.exists(p):
            strip_lines.append("%s 缺图" % n)
            print("  %-22s 缺图" % n)
            continue
        bg, rbg, roth = strip_stats(p, STRIP_REGION)
        strip_lines.append("%s\t%.3f\t%s" % (n, roth, lab))
        print("  %-22s 页签条区非背景 %.3f  ← %s" % (n, roth, lab[:70]))

    fails = []
    got_tags = {}
    for j in judged:
        m = re.match(r"(★M08[A-Z]+★) (PASS|FAIL)", j)
        if not m:
            continue
        got_tags.setdefault(m.group(1), []).append(m.group(2))
    for tag in JUDGE_TAGS:
        vals = got_tags.get(tag, [])
        if not vals:
            fails.append("缺少判词 %s（数据未落盘时会如实缺失，见脚本头部说明）" % tag)
            continue
        if any(v == "FAIL" for v in vals):
            fails.append("%s 有 FAIL：%s" % (tag, vals))
    if not any("★M08TAB-REJECT★" in r for r in rejects):
        fails.append("缺少负向判词 ★M08TAB-REJECT★（未知页签必须被挡下）")
    if not any("★M08VARIANT-REJECT★" in r for r in rejects):
        fails.append("缺少负向判词 ★M08VARIANT-REJECT★（galguard 的 12 例必须逐条出现）")
    if len(attach_shots) != 4:
        fails.append("attach 四承载屏的导图不足（实得 %d 张，期望 4）" % len(attach_shots))
    else:
        screens_seen = []
        for n, lab in attach_shots:
            p = os.path.join(SAVE, n)
            m = re.search(r"shot_\d+_([a-z_]+)\.png$", n)
            if m:
                screens_seen.append(m.group(1))
            if not os.path.exists(p):
                fails.append("attach 导图缺失：%s" % n)
                continue
            _bg, _rbg, roth = strip_stats(p, STRIP_REGION)
            if roth < 0.02:
                fails.append("attach 绘制见证不足：%s 页签条区非背景仅 %.3f（期望 ≥0.02）"
                             % (n, roth))
        if sorted(set(screens_seen)) != ["dress", "gallery", "music", "replay"]:
            fails.append("attach 四承载屏导图的屏名不齐：实得 %s（期望 dress/gallery/music/replay）"
                         % sorted(set(screens_seen)))

    txt = []
    txt.append("MODE=" + ("REAL" if not inject else "INJECT"))
    for tag in JUDGE_TAGS:
        txt.append("%s 判词：%s" % (tag, got_tags.get(tag, [])))
    txt.append("负向判词条数：%d（去重后 %d）" % (len(rejects), len(seen)))
    txt.append("attach 四承载屏导图（页签条区非背景占比）：")
    for s in strip_lines:
        txt.append("  " + s)
    txt.append("")
    txt.append("\n".join("FAIL " + f for f in fails) if fails else "全部断言通过")
    txt.append("RESULT=" + ("FAIL" if fails else "OK"))
    io.open(os.path.join(EVID, "引擎巡演判定.txt"), "w", encoding="utf-8").write("\n".join(txt))
    print("\n===== 判定 =====")
    print("\n".join(txt))
    print("★ 退出码：", 1 if fails else 0)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())