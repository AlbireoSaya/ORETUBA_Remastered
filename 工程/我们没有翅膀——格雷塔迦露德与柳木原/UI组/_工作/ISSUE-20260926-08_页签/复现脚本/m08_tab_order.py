# -*- coding: utf-8 -*-
r"""m08 · 存/读档屏页签「位置固定、高亮跟随」修复 + 自证（`ISSUE-20260926-08`）

目标屏：`layout\screens\24_load.json`（唯一被改的屏文件；`23_save.json` 只作参照，一字未改）。
用户裁决（2026-09-26）：页签＝**位置固定、仅高亮随页移动**（与 `39_gal_shell` 鉴赏外壳四页签同口径）
⇒ 左上格(x340) 固定＝**存档**、右上格(x526) 固定＝**读档**，只有「当前页」换高亮件。

规范终态（canonical target，与 `23_save.json` 逐项一致）：

    x340  ⇒  文案「存档」 ⇒  热区 `open_save`   ｜ 选件随屏：存档屏=`x_ui_psv_tab_sel.png`、读档屏=`x_ui_tab_off.png`
    x526  ⇒  文案「读档」 ⇒  热区 `open_load`   ｜ 选件随屏：读档屏=`x_ui_psv_tab_sel.png`、存档屏=`x_ui_tab_off.png`

★ **与派单背景的实测分歧（本脚本按验收口径执行，理由见下）**
  派单背景称「`24_load` 左格热区动作仍是 `open_save`、右格 `open_load`，热区一律不动」。
  **盘面实测不是这样**：改动前盘上 `sv.tab_a_hit`(x340) 已是 `open_load`、`sv.tab_b_hit`(x526) 已是 `open_save`
  —— 那是上一轮 `ISSUE-20260926-06`「④-轻」把左页签的 label/action 一起订正到「读档/open_load」的结果
  （证据：本屏 note 与 `sv.tab_a_tx`/`sv.tab_b_tx` 的 note 原文）。
  ⇒ 若只换 4 个字段（文案/选件）而「热区不动」，终态会变成
   **x340＝存档 ⇒ `open_load`**（点「存档」跳读档屏、且在本屏是死键），正是要根除的「标签/动作倒置」的镜像。
  ⇒ 本脚本据派单**自证口径**（x340⇒存档⇒`open_save`；x526⇒读档⇒`open_load`，与 `23_save` 一致）
   把两件热区动作一并归位 ⇒ 共动 **6 个字段**；几何 `x/y/w/h/z` 一律未改。

本脚本的两种「旧值」都收敛到同一终态（幂等）：
  · 盘面旧态（`open_load`/`open_save`）→ 交换两件热区动作；
  · 若某处已是目标值 → 只报不写。
写盘前一律断言「盘上值 ∈ {旧, 新}」，出现第三种取值即硬失败退出。

用法（全部带退出码，可反复跑）：
    python m08_tab_order.py --pre        # 改动**前**：快照 `24_load.json` + 出「改前」数据合成单图 + 存实机改前导图
    python m08_tab_order.py --apply      # 应用改动（幂等；已应用则只报不写）
    python m08_tab_order.py --check      # 终态断言（6 件对齐 `23_save`）+ 与快照逐行 diff
    python m08_tab_order.py --diffscope  # 范围自证：除 6 字段与 note 外零改动；23_save 零改动
        ★ 本项只证「**范围**」（无第三类改动），**不证「6 个目标字段的取值正确」**——
          [B] 会把 6 个目标字段无条件还原成旧值再比对，故其中任一字段若是「第三种值」时 [A]/[B] 仍放行；
          note 内容亦被 strip_notes() 摘除、不在本项范围内。取值正确性由 --check 第 1 节的终态断言
          与 --apply 的「值 ∉ {旧,新} ⇒ 拒绝写盘」两处保证（2026-09-26 复审的变异表逐条实测）。
    python m08_tab_order.py --composite  # 出 `取证\改前改后_页签2x.png`
    python m08_tab_order.py --runtime    # 从实机导图实测「哪一格高亮」→ `取证\页签对照.txt`
"""
import sys, os, json, shutil, hashlib, difflib

sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SCR = os.path.join(BASE, "layout", "screens")
UI = os.path.join(BASE, "krkr", "assets", "ui")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-08_页签")
BAK = os.path.join(WORK, "原形备份")
EV = os.path.join(WORK, "取证")
SHOTS = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\临时\ui_run\runtime\savedata"
TARGET_PNG = "24_load.json"
REF_PNG = "23_save.json"
REF_MD5 = "524828efd09ac961264bbbb5dac7ec89"   # 23_save.json 基准（本轮全程未改）
# ⚠️ 本值是**工作树 CRLF 文件**的 md5（core.autocrlf=true 下与 blob 不同）⇒ 若在 autocrlf=false 的
#    克隆/检出上复跑，[C] 会因换行口径不同误报 FAIL。此时请改用「git 对 23_save.json 无 diff」
#    或对该文件 blob（LF）取 md5 作为基准，不要改判定逻辑。

SEL = "ui/x_ui_psv_tab_sel.png"
OFF = "ui/x_ui_tab_off.png"
CELL_L, CELL_R, CELL_Y, CELL_W, CELL_H = 340, 526, 24, 181, 60
CROP = (300, 10, 760, 90)          # 页签观察窗（派单建议区间）
SHOT_PNG = {"save": "shot_10_save.png", "load": "shot_11_load.png"}
BG_PNG = {"save": "x_ui_psv_save_bg.png", "load": "x_ui_psv_load_bg.png"}
TXT_COLS = (50, 130)               # 格内「文字带」列区间（两侧留白列用于取样色，避开字迹）
MARK = "ISSUE-20260926-08"

# (id, field, 旧值, 新值)
PAIRS = [
    ("sv.tab_a",     "asset",  SEL,       OFF),
    ("sv.tab_a_tx",  "sample", "读档",     "存档"),
    ("sv.tab_a_hit", "action", "open_load", "open_save"),
    ("sv.tab_b",     "asset",  OFF,       SEL),
    ("sv.tab_b_tx",  "sample", "存档",     "读档"),
    ("sv.tab_b_hit", "action", "open_save", "open_load"),
]
NOTE_IDS = ["sv.tab_a", "sv.tab_a_tx", "sv.tab_a_hit", "sv.tab_b", "sv.tab_b_tx", "sv.tab_b_hit"]

# ── 追加段（首句＝「派单口径」，按一轮打回**即时作废**；实测订正段不变） ──
APPEND_HEAD = (
    "\n★ 2026-09-26（`" + MARK + "`）用户裁决：页签改为**位置固定、高亮跟随**（与 `39_gal_shell` 惯例一致）"
    "—— 左上格固定＝存档、右上格固定＝读档，仅高亮件随所在屏移动")
CLAUSE_OLD = (
    "；修掉上一轮『只改文案未交换热区』导致的标签/动作倒置"
    "（原读档屏左格显示「读档」但点击执行 `open_save`）。")
CLAUSE_NEW = (
    "。★ **派单背景口径（已作废，见下段实测订正）**：派单称本屏存在"
    "「左格显示读档却执行 `open_save`」的倒置 —— 盘面实测**无此状态**"
    "（改动前左格＝读档/`open_load` 本已配对）；本屏真正的缺陷是"
    "**两屏页签顺序不一致**（存档屏「存档｜读档」、读档屏「读档｜存档」）。")
APPEND_TAIL = (
    "\n★ **实测订正（盘面事实，优先于派单背景）**：改动前盘上 `sv.tab_a_hit`(x340) 已是 `open_load`、"
    "`sv.tab_b_hit`(x526) 已是 `open_save` —— 上一轮 `ISSUE-20260926-06`「④-轻」已把左页签的"
    "label/action 一并订正为「读档/open_load」（证据 = 本屏 note 与 `sv.tab_a_tx`/`sv.tab_b_tx` 的 note 原文）"
    "⇒ 派单所述『热区已是 open_save/open_load、一律不动』与盘面不符。"
    "若只换 4 个字段（文案/选件）而热区不动，终态将是 **x340＝存档 ⇒ `open_load`**"
    "（点「存档」跳读档屏、在本屏成死键）＝要根除的倒置的镜像；故按派单**自证口径**"
    "（x340⇒存档⇒`open_save`、x526⇒读档⇒`open_load`，与 `23_save` 逐项一致）"
    "把这两件热区 `action` 一并归位 ⇒ 本轮共动 **6 个字段**（4 件文案/选件 ＋ 2 件热区 `action`）。"
    "几何 `x/y/w/h/z`、`font`、`nine`、`source`、`vis_flag`/`vis_when` 与全部机制字段未改。"
)
APPEND_OLD = APPEND_HEAD + CLAUSE_OLD + APPEND_TAIL
APPEND_NEW = APPEND_HEAD + CLAUSE_NEW + APPEND_TAIL

# 06 轮口径的**轮次限定**（按「只追加不覆盖」惯例，不删旧句）：(待加限定的旧片段, 加限定后的片段)
QUAL_SCREEN = "（该口径属 06 轮；本屏页签的 `asset`/`sample`/`action` 已于 `ISSUE-20260926-08` 归位，见下段）"
QUALIFIERS = [
    ("、`close` 原样。",
     "、`close` 原样" + QUAL_SCREEN + "。"),
    ("；`sv.tab_*` 的 `action` 仍未改。",
     "；`sv.tab_*` 的 `action` 仍未改" + QUAL_SCREEN + "。"),
    ("（M34 历史笔误，label 与 action 曾错配）。",
     "（M34 历史笔误，label 与 action 曾错配）。（06 轮状态；本屏左格已于 08 轮改为「存档」）"),
]

FAILS = []
for p in (BAK, EV):
    os.makedirs(p, exist_ok=True)


# ── IO：json 逐字节保形（本仓 screens/*.json 为「indent=1 + CRLF + 无尾换行」） ──
def read_text(path):
    return open(path, "r", encoding="utf-8", newline="").read()


def load_json(path):
    return json.loads(read_text(path))


def write_json(obj, path):
    open(path, "w", encoding="utf-8", newline="").write(
        json.dumps(obj, ensure_ascii=False, indent=1).replace("\n", "\r\n"))


def roundtrip_probe(path):
    """断言「load→dump」逐字节无损（否则本脚本的 diff 就不能只归因到被改字段）。"""
    txt = read_text(path)
    obj = json.loads(txt)
    out = json.dumps(obj, ensure_ascii=False, indent=1).replace("\n", "\r\n")
    return txt == out


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def by_id(scr):
    return {e["id"]: e for e in scr["elements"]}


def ink_color():
    raw = load_json(os.path.join(BASE, "layout", "palette.json"))
    v = raw["colors"]["node_locked"]["value"].lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


INK = ink_color()


def flat(im):
    im = im.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")


def stretch(base, asset, x, y, w, h):
    """九宫格 l=t=r=b=0 ⇒ 整图双轴拉伸（与 uiWidgetNine 的 operateStretch 等价口径）。"""
    src = Image.open(os.path.join(UI, asset.split("/")[-1])).convert("RGBA")
    base.paste(flat(src.resize((w, h), Image.BILINEAR)), (x, y))


def data_panel(scr):
    """按布局数据合成「页签区域」：底图 + 两格底件 + 两格文案（引擎绘字的等效近似）。"""
    els = by_id(scr)
    bg = os.path.join(UI, els["sv.bg"]["asset"].split("/")[-1])
    img = flat(Image.open(bg))
    for eid in ("sv.tab_a", "sv.tab_b"):
        e = els[eid]
        stretch(img, e["asset"], e["x"], e["y"], e["w"], e["h"])
    d = ImageDraw.Draw(img)
    for eid in ("sv.tab_a_tx", "sv.tab_b_tx"):
        e = els[eid]
        f = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", e["font"]["size"])
        tw = d.textlength(e["sample"], font=f)
        d.text((e["x"] + (e["w"] - tw) / 2.0, e["y"] + (e["h"] - e["font"]["size"]) / 2.0 - 2),
               e["sample"], font=f, fill=INK)
    return img.crop(CROP)


def engine_panel(shot):
    return flat(Image.open(shot)).crop(CROP)


def up2(im):
    return im.resize((im.width * 2, im.height * 2), Image.LANCZOS)


# ════════════════════════ --pre ════════════════════════
def mode_pre():
    live = os.path.join(SCR, TARGET_PNG)
    if not roundtrip_probe(live):
        FAILS.append("load→dump 非逐字节无损 ⇒ 本脚本不宜用于写盘（先查缩进/换行口径）")
        return report("--pre")
    bak = os.path.join(BAK, TARGET_PNG)
    if os.path.exists(bak):
        print("[--pre] 快照已存在（不覆盖）：%s  md5=%s" % (bak, md5(bak)))
    else:
        shutil.copyfile(live, bak)
        print("[--pre] 写出改前快照：%s  md5=%s" % (bak, md5(bak)))
    print("[--pre] 现盘 md5=%s" % md5(live))

    # 数据合成「改前」单图
    a = up2(data_panel(load_json(live)))
    a.save(os.path.join(EV, "改前_页签2x_单图.png"))
    print("[--pre] → 取证\\改前_页签2x_单图.png %s" % (a.size,))

    # 实机改前导图（巡演在改动前跑 ⇒ 就是改前实机）
    for key, fn in SHOT_PNG.items():
        sp = os.path.join(SHOTS, fn)
        if not os.path.exists(sp):
            print("[--pre] !! 缺实机导图 %s（跳过；实机改前对照将缺席）" % sp)
            continue
        shutil.copyfile(sp, os.path.join(EV, "改前实机_%s.png" % ("存档" if key == "save" else "读档")))
        print("[--pre] → 取证\\改前实机_%s.png（源 %s，mtime=%s）"
              % ("存档" if key == "save" else "读档", fn, os.path.getmtime(sp)))
    return report("--pre")


# ════════════════════════ --apply ════════════════════════
def mode_apply():
    live = os.path.join(SCR, TARGET_PNG)
    if not roundtrip_probe(live):
        FAILS.append("load→dump 非逐字节无损 ⇒ 拒绝写盘")
        return report("--apply")
    scr = load_json(live)
    els = by_id(scr)
    written, already = [], []
    for eid, field, old, new in PAIRS:
        el = els[eid]
        cur = el.get(field)
        if cur not in (old, new):
            FAILS.append("%s.%s 盘上值 %r ∉ {旧,新} ⇒ 拒绝写盘" % (eid, field, cur))
            continue
        if cur == new:
            already.append("%s.%s 已是目标值 %r" % (eid, field, new))
        else:
            el[field] = new
            written.append("%s.%s  %r → %r" % (eid, field, old, new))
    if FAILS:
        return report("--apply")

    # note 文本轮：① 追加段（旧句 → 作废标注；新装则直接追加）② 06 轮口径加轮次限定
    notes = []

    def fix_note(owner, note):
        if APPEND_OLD in note:
            note = note.replace(APPEND_OLD, APPEND_NEW)
            notes.append(owner + "：追加段订正（首句改为「派单口径·已作废」）")
        elif APPEND_NEW in note:
            notes.append(owner + "：追加段已是终态（只报不写）")
        else:
            note = note + APPEND_NEW
            notes.append(owner + "：追加段（新装）")
        for frag, post in QUALIFIERS:
            if frag in note and post not in note:
                note = note.replace(frag, post)
                notes.append(owner + "：06 轮口径加轮次限定「%s…」" % frag[:10])
        return note

    scr["note"] = fix_note("(屏级 note)", scr.get("note") or "")
    for eid in NOTE_IDS:
        els[eid]["note"] = fix_note(eid + ".note", els[eid].get("note") or "")

    if not written and not [n for n in notes if "只报不写" not in n]:
        print("[--apply] 已是终态，只报不写（幂等）")
    else:
        write_json(scr, live)
        print("[--apply] 字段改动 %d 处：" % len(written))
        for w in written:
            print("   ·", w)
        print("[--apply] note 处理 %d 处：" % len(notes))
        for n in notes:
            print("   ·", n)
        print("[--apply] 现盘 md5=%s" % md5(live))
    for a in already:
        print("[--apply] （已在终态）", a)
    return report("--apply")


# ════════════════════════ --check ════════════════════════
def cell_table(scr, tag):
    els = by_id(scr)
    rows = []
    for side, x in (("左", CELL_L), ("右", CELL_R)):
        img = els["sv.tab_a" if side == "左" else "sv.tab_b"]
        tx = els["sv.tab_a_tx" if side == "左" else "sv.tab_b_tx"]
        hit = els["sv.tab_a_hit" if side == "左" else "sv.tab_b_hit"]
        cls = "sel" if img["asset"] == SEL else ("off" if img["asset"] == OFF else "?" + img["asset"])
        rows.append((side, x, tx["sample"], cls, hit["action"]))
        print("  %s %s x=%-4d 文案=%-3s 选件=%-4s 动作=%s  [%s x%d y%d w%d h%d z%d ｜ "
              "%s x%d y%d w%d h%d ｜ %s x%d y%d w%d h%d z%d]"
              % (tag, side, x, tx["sample"], cls, hit["action"], img["id"],
                 img["x"], img["y"], img["w"], img["h"], img["z"],
                 tx["id"], tx["x"], tx["y"], tx["w"], tx["h"],
                 hit["id"], hit["x"], hit["y"], hit["w"], hit["h"], hit["z"]))
    return rows


def mode_check():
    live_p = os.path.join(SCR, TARGET_PNG)
    bak_p = os.path.join(BAK, TARGET_PNG)
    live = load_json(live_p)
    ref = load_json(os.path.join(SCR, REF_PNG))
    els, rels = by_id(live), by_id(ref)

    print("[--check 1] 字段终态（24_load vs 23_save）")
    for eid, field, old, new in PAIRS:
        cur = els[eid].get(field)
        ok = cur == new
        if not ok:
            FAILS.append("%s.%s = %r，期望 %r" % (eid, field, cur, new))
        print("  %-13s %-7s = %-32r（期望 %r）%s" % (eid, field, cur, new, "OK" if ok else "**FAIL**"))

    # 23_save 侧的对应件（除「哪一件是选中件」外必须逐项一致）
    ref_pairs = [("sv.tab_a", "asset", SEL), ("sv.tab_a_tx", "sample", "存档"),
                 ("sv.tab_a_hit", "action", "open_save"),
                 ("sv.tab_b", "asset", OFF), ("sv.tab_b_tx", "sample", "读档"),
                 ("sv.tab_b_hit", "action", "open_load")]
    for eid, field, want in ref_pairs:
        cur = rels[eid].get(field)
        if cur != want:
            FAILS.append("参照屏 %s.%s = %r，与既有事实不符（期望 %r）" % (eid, field, cur, want))

    print("[--check 2] 三元对齐：x340 ⇒ 存档 ⇒ open_save ｜ x526 ⇒ 读档 ⇒ open_load")
    a = cell_table(live, "24_load")
    print("  ---- 参照屏 23_save ----")
    b = cell_table(ref, "23_save")
    for r_l, r_s in zip(a, b):
        side = r_l[0]
        if r_l[2] != r_s[2]:
            FAILS.append("%s格 文案位置不一致：24_load=%s / 23_save=%s" % (side, r_l[2], r_s[2]))
        if r_l[4] != r_s[4]:
            FAILS.append("%s格 热区动作不一致：24_load=%s / 23_save=%s" % (side, r_l[4], r_s[4]))
        if r_l[3] == r_s[3]:
            FAILS.append("%s格 选件与参照屏相同（高亮未随屏移动）：%s" % (side, r_l[3]))
    print("[--check 3] 全屏唯一高亮件断言")
    sel_ids = [e["id"] for e in live["elements"] if e.get("asset") == SEL]
    if sel_ids != ["sv.tab_b"]:
        FAILS.append("24_load 的选中件集 = %r，期望恰为 ['sv.tab_b']" % (sel_ids,))
    print("  24_load 用 %s 的元素 = %r ｜ 23_save 用它的元素 = %r"
          % (SEL, sel_ids, [e["id"] for e in ref["elements"] if e.get("asset") == SEL]))
    # 位置固定：两屏的 6 件几何逐项相同
    for eid in NOTE_IDS:
        ga = (els[eid]["x"], els[eid]["y"], els[eid]["w"], els[eid]["h"], els[eid]["z"])
        gb = (rels[eid]["x"], rels[eid]["y"], rels[eid]["w"], rels[eid]["h"], rels[eid]["z"])
        if ga != gb:
            FAILS.append("%s 几何/层序与 23_save 不同：%r vs %r" % (eid, ga, gb))
    print("  6 件几何/层序与 23_save 逐项相同（位置固定）")

    print("[--check 4] 与改动前快照逐行 diff")
    if not os.path.exists(bak_p):
        FAILS.append("缺快照 %s ⇒ 无法逐行 diff" % bak_p)
        return report("--check")
    A = read_text(bak_p).split("\r\n")
    B = read_text(live_p).split("\r\n")
    diff = [(i + 1, x, y) for i, (x, y) in enumerate(zip(A, B)) if x != y]
    if len(A) != len(B):
        FAILS.append("行数变化 %d → %d" % (len(A), len(B)))
    print("  行数 %d → %d ｜ 差异行 %d 行" % (len(A), len(B), len(diff)))
    for no, x, y in diff:
        print("  L%-5d - %s" % (no, x.strip()[:110]))
        print("         + %s" % (y.strip()[:110],))
    exp_fields = {("asset", "sv.tab_a"), ("sample", "sv.tab_a_tx"), ("action", "sv.tab_a_hit"),
                  ("asset", "sv.tab_b"), ("sample", "sv.tab_b_tx"), ("action", "sv.tab_b_hit")}
    import re as _re
    FIELDLINE = _re.compile(r'^\s*"(asset|sample|action)":\s*"[^"]*",?$')
    got = sum(1 for _, x, y in diff if FIELDLINE.match(x.strip()) and FIELDLINE.match(y.strip()))
    note_lines = len(diff) - got
    print("  差异行构成：字段行 %d ｜ 其余（note 追加）%d" % (got, note_lines))
    if got != 6:
        FAILS.append("字段差异行 %d ≠ 6" % got)
    if got + note_lines != 13:
        FAILS.append("差异行合计 %d ≠ 13（期望 6 字段 + 7 note：屏级 1 + 元素 6）" % (got + note_lines,))
    if any(not (FIELDLINE.match(x.strip()) and FIELDLINE.match(y.strip())) and '"note"' not in y
           for _, x, y in diff):
        FAILS.append("发现「既非被改字段行、也非 note 行」的差异行 ⇒ 有越界改动")
    return report("--check")


# ════════════════════════ --composite ════════════════════════
def mode_composite():
    live = load_json(os.path.join(SCR, TARGET_PNG))
    bak_p = os.path.join(BAK, TARGET_PNG)
    if not os.path.exists(bak_p):
        FAILS.append("缺改前快照 %s" % bak_p)
        return report("--composite")
    before = load_json(bak_p)
    ref = load_json(os.path.join(SCR, REF_PNG))

    # ① ② 数据合成（参照屏 + 24 读档的改前/改后）
    rows = [("① 改前", [("23 存档（参照·全程未改）", data_panel(ref)),
                        ("24 读档（改前）", data_panel(before))]),
            ("② 改后", [("23 存档（参照·全程未改）", data_panel(ref)),
                        ("24 读档（改后）", data_panel(live))])]
    # ③ ④ 实机巡演导图
    pre_row, post_row = [], []
    for key in ("save", "load"):
        nm = "存档" if key == "save" else "读档"
        pre_p = os.path.join(EV, "改前实机_%s.png" % nm)
        post_p = os.path.join(SHOTS, SHOT_PNG[key])
        if os.path.exists(pre_p):
            pre_row.append(("%s %s（改前实机）" % ("23" if key == "save" else "24", nm), engine_panel(pre_p)))
        if os.path.exists(post_p):
            post_row.append(("%s %s（改后实机）" % ("23" if key == "save" else "24", nm), engine_panel(post_p)))
    if pre_row:
        rows.append(("③ 实机巡演导图 · 改前（引擎离屏导出）", pre_row))
    if post_row:
        rows.append(("④ 实机巡演导图 · 改后（引擎离屏导出）", post_row))

    PW, PH = (CROP[2] - CROP[0]) * 2, (CROP[3] - CROP[1]) * 2
    COLGAP, ROWHDR, CELLGAP = 30, 52, 14
    cols = max(len(r[1]) for r in rows)
    width = 24 + cols * PW + (cols - 1) * COLGAP + 24
    height = 24 + sum(ROWHDR + PH + CELLGAP for _ in rows) + 30
    F1 = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 26)
    F2 = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 18)
    sh = Image.new("RGB", (width, height), (236, 239, 246))
    d = ImageDraw.Draw(sh)
    d.text((24, 4), "存/读档屏「页签区」改前 / 改后 2×（观察窗 x%d..%d ｜ y%d..%d，画布坐标 1920×1080）"
           % (CROP[0], CROP[2], CROP[1], CROP[3]), font=F1, fill=(30, 36, 60))
    y = 4 + ROWHDR
    for title, cells in rows:
        d.text((24, y - 44), title, font=F1, fill=(40, 48, 76))
        for i, (cl, img) in enumerate(cells):
            x = 24 + i * (PW + COLGAP)
            d.text((x + 4, y - 22), cl, font=F2, fill=(70, 76, 96))
            sh.paste(up2(img), (x, y))
            d.rectangle([x, y, x + PW - 1, y + PH - 1], outline=(150, 156, 172), width=1)
        y += ROWHDR + PH + CELLGAP
    d.text((24, height - 26), "★ 位置固定、仅高亮跟随：左格恒为「存档」、右格恒为「读档」；"
           "高亮件（深色霜面）」随所在屏移动 —— 存档屏亮左格、读档屏亮右格。", font=F2, fill=(60, 66, 84))
    out = os.path.join(EV, "改前改后_页签2x.png")
    sh.save(out)
    print("→", out, sh.size)
    return report("--composite")


# ════════════════════════ --diffscope ════════════════════════
def strip_notes(node):
    if isinstance(node, dict):
        return {k: strip_notes(v) for k, v in node.items() if k != "note"}
    if isinstance(node, list):
        return [strip_notes(v) for v in node]
    return node


def walk_diff(a, b, path="", out=None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((path + "/" + k, a.get(k, "<缺>"), b.get(k, "<缺>")))
            else:
                walk_diff(a[k], b[k], path + "/" + k, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path + "/len", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            walk_diff(x, y, path + "[%d]" % i, out)
    elif a != b:
        out.append((path, a, b))
    return out


def mode_diffscope():
    """范围自证：**除 6 个数据字段与 note 文本外，24_load.json 零改动**；`23_save.json` 零改动。
       [A] 抹掉全部 note 键后 diff（现盘 vs 改动前快照）⇒ 必须**恰为那 6 个字段路径**；
       [B] 再把这 6 个字段还原成旧值后，两侧必须**完全同一**（⇒ 无第三类改动）；
       [C] `23_save.json` md5 必须仍等于登记值（参照屏未被触碰）。"""
    live = load_json(os.path.join(SCR, TARGET_PNG))
    before = load_json(os.path.join(BAK, TARGET_PNG))
    a, b = strip_notes(before), strip_notes(live)
    d1 = walk_diff(a, b)
    exp_paths = ["/elements[%d]/%s" % (i, f) for i, f in
                 ((2, "asset"), (3, "sample"), (4, "action"), (5, "asset"), (6, "sample"), (7, "action"))]
    got_paths = [p for p, _, _ in d1]
    print("[A] 抹掉全部 note 后的差异 = %d 处：" % len(d1))
    for p, x, y in d1:
        print("    %s : %r → %r" % (p, x, y))
    if sorted(got_paths) != sorted(exp_paths):
        FAILS.append("[A] 差异路径 %r ≠ 期望 6 字段 %r" % (sorted(got_paths), sorted(exp_paths)))
    else:
        print("    ⇒ 恰为 6 个数据字段（sv.tab_a.asset / sv.tab_a_tx.sample / sv.tab_a_hit.action / "
              "sv.tab_b.asset / sv.tab_b_tx.sample / sv.tab_b_hit.action）✓")

    # [B] 把 6 字段还原成旧值 ⇒ 两侧必须完全同一
    rev = json.loads(json.dumps(b, ensure_ascii=False))
    for eid, field, old, new in PAIRS:
        for el in rev["elements"]:
            if el["id"] == eid:
                el[field] = old
    same = json.dumps(rev, ensure_ascii=False, sort_keys=True) == json.dumps(a, ensure_ascii=False, sort_keys=True)
    print("[B] 6 字段还原旧值后与「抹 note 的改动前快照」逐键同一 = %s" % same)
    if not same:
        FAILS.append("[B] 还原 6 字段后仍不一致 ⇒ 存在第三类改动")

    # [C] 23_save.json 零改动
    ref = os.path.join(SCR, REF_PNG)
    print("[C] 23_save.json md5 = %s（登记值 %s）" % (md5(ref), REF_MD5))
    if md5(ref) != REF_MD5:
        FAILS.append("[C] 23_save.json md5 变化 ⇒ 参照屏被改动")
    else:
        print("    ⇒ 参照屏零改动 ✓")
    return report("--diffscope")


# ════════════════════════ --runtime ════════════════════════
def cell_sample(shot_path, x):
    """在导图上取该格「带体两侧留白列」的均值色（避开中间字带）。"""
    im = flat(Image.open(shot_path))
    px = im.load()
    tot = [0, 0, 0]
    n = 0
    for cx in list(range(x + 6, x + TXT_COLS[0])) + list(range(x + TXT_COLS[1], x + CELL_W - 6)):
        for cy in range(CELL_Y + 5, CELL_Y + CELL_H - 5):
            r, g, b = px[cx, cy]
            tot[0] += r; tot[1] += g; tot[2] += b
            n += 1
    return tuple(round(v / float(n), 2) for v in tot), n


def ref_sample(bg_name, asset, x):
    """参照件：把底件（181×70）按 181×60 拉到该格，压在同源底图对应区域上 —— 与引擎同一合成口径。"""
    base = flat(Image.open(os.path.join(UI, bg_name)))
    stretch(base, asset, x, CELL_Y, CELL_W, CELL_H)
    px = base.load()
    tot = [0, 0, 0]; n = 0
    for cx in list(range(x + 6, x + TXT_COLS[0])) + list(range(x + TXT_COLS[1], x + CELL_W - 6)):
        for cy in range(CELL_Y + 5, CELL_Y + CELL_H - 5):
            r, g, b = px[cx, cy]
            tot[0] += r; tot[1] += g; tot[2] += b
            n += 1
    return tuple(round(v / float(n), 2) for v in tot)


def mode_runtime():
    lines = []
    lines.append("页签对照 · 实机巡演导图实测「哪一格是高亮」（%s）" % MARK)
    lines.append("导图目录：%s" % SHOTS)
    lines.append("观察格：左格 x%d..%d、右格 x%d..%d，y%d..%d（画布坐标）"
                 % (CELL_L, CELL_L + CELL_W, CELL_R, CELL_R + CELL_W, CELL_Y, CELL_Y + CELL_H))
    lines.append("取样口径：每格取「带体内两侧留白列」的均值 RGB（列 x+6..x+%d 与 x+%d..x+%d，"
                 "行 y+5..y+55）= %d 像素/格 ⇒ 完全避开中间字带（字带列 %d..%d），"
                 "读数不受「存档/读档」两字差异影响。"
                 % (TXT_COLS[0], TXT_COLS[1], CELL_W - 6,
                    (TXT_COLS[0] - 6 + CELL_W - 6 - TXT_COLS[1]) * (CELL_H - 10),
                    TXT_COLS[0], TXT_COLS[1]))
    lines.append("参照件：把 `%s`（高亮/选中件）与 `%s`（未选中件）各按 181×60 贴在**同源底图**对应格上，"
                 "用同一取样口径取参照色。" % (SEL, OFF))
    lines.append("")
    ref = {}
    for key in ("save", "load"):
        ref[(key, "sel")] = ref_sample(BG_PNG[key], SEL, CELL_L)
        ref[(key, "off")] = ref_sample(BG_PNG[key], OFF, CELL_L)

    verdicts = {}
    for key, tag in (("save", "23 存档"), ("load", "24 读档")):
        for phase, path in (("改前", os.path.join(EV, "改前实机_%s.png" % ("存档" if key == "save" else "读档"))),
                            ("改后", os.path.join(SHOTS, SHOT_PNG[key]))):
            if not os.path.exists(path):
                FAILS.append("缺导图 %s（%s %s）" % (path, tag, phase))
                continue
            lines.append("── %s ｜ %s ｜ %s" % (tag, phase, os.path.basename(path)))
            lines.append("   参照色：sel=%s ｜ off=%s（底图 %s）"
                         % (ref[(key, "sel")], ref[(key, "off")], BG_PNG[key]))
            got = {}
            for side, x in (("左格", CELL_L), ("右格", CELL_R)):
                c, n = cell_sample(path, x)
                dsel = sum(abs(c[i] - ref[(key, "sel")][i]) for i in range(3))
                doff = sum(abs(c[i] - ref[(key, "off")][i]) for i in range(3))
                who = "sel(高亮)" if dsel < doff else "off(未选中)"
                got[side] = who
                lines.append("   %s x=%d 实测均值色=%s（%d px）｜ Σ|Δ| vs sel=%6.2f ｜ vs off=%6.2f ⇒ 判为 **%s**"
                             % (side, x, c, n, dsel, doff, who))
            lum = {}
            for side, x in (("左格", CELL_L), ("右格", CELL_R)):
                c, _ = cell_sample(path, x)
                lum[side] = sum(c) / 3.0
            lines.append("   交叉校验（亮度）：左 %.1f ／ 右 %.1f ⇒ 较暗者（高亮件为深色霜面）= %s"
                         % (lum["左格"], lum["右格"], "左格" if lum["左格"] < lum["右格"] else "右格"))
            verdicts[(key, phase)] = got
            lines.append("")

    lines.append("结论")
    for key, tag in (("save", "23 存档"), ("load", "24 读档")):
        for phase in ("改前", "改后"):
            g = verdicts.get((key, phase))
            if g:
                lines.append("  · %s %s：左格=%s ｜ 右格=%s" % (tag, phase, g["左格"], g["右格"]))
    exp = {("save", "改前"): ("sel(高亮)", "off(未选中)"), ("save", "改后"): ("sel(高亮)", "off(未选中)"),
           ("load", "改前"): ("sel(高亮)", "off(未选中)"), ("load", "改后"): ("off(未选中)", "sel(高亮)")}
    for k, want in exp.items():
        got = verdicts.get(k)
        if got is None:
            continue
        real = (got["左格"], got["右格"])
        if real != want:
            FAILS.append("实机判读不符：%s %s 实测=%r 期望=%r" % (k[0], k[1], real, want))
    lines.append("")
    lines.append("（期望：存档屏恒亮左格；读档屏改前亮左格、改后亮右格 —— 即「位置固定、高亮跟随」的实机证据。）")
    out = os.path.join(EV, "页签对照.txt")
    open(out, "w", encoding="utf-8", newline="").write("\r\n".join(lines))
    for l in lines:
        print(l)
    print("\n→", out)
    return report("--runtime")


def report(tag):
    print("\n%s 结论：%s" % (tag, "全部通过" if not FAILS else "**失败 %d 项**" % len(FAILS)))
    for f in FAILS:
        print("  FAIL:", f)
    return 1 if FAILS else 0


def main():
    args = sys.argv[1:]
    if "--pre" in args:
        return mode_pre()
    if "--apply" in args:
        return mode_apply()
    if "--check" in args:
        return mode_check()
    if "--diffscope" in args:
        return mode_diffscope()
    if "--composite" in args:
        return mode_composite()
    if "--runtime" in args:
        return mode_runtime()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
