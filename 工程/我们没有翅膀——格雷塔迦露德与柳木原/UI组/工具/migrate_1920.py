# -*- coding: utf-8 -*-
r"""
migrate_1920.py -- UI 组 M12 · 布局 ×1.5 迁移器（1280×720 基线 -> 1920×1080 基线）
================================================================================
Issue  : UI 美术组 · M12（布局 ×1.5 迁移到 1920×1080）
依据   : 资源组\04_1920画布与双分辨率方案.md §9.3 迁移对照表 / §9.4 不必改的部分 / §十 U5、U6
        项目总纲 D1 修订注·画布基线（第三条，2026-09-19）

作用
----
把 `layout/` 下全部布局数据从 1280×720 基线机械迁移到 1920×1080 基线：
  * `layout/_root.json`：canvas / content_boxes / fonts.sizes 数值 ×1.5；
    `content_box_rule` 与 `font_rule` 文案改写为 1920×1080 口径（U6）；
    写入幂等标记 `"canvas_baseline": "1920x1080"`。
  * `layout/screens/*.json`：**只改数值**，不动任何语义结构
    （`kind` / 字段名 / `dynamic` / `hit.action` / `labels` / `actions` / `note` 语义不变）。

取整口径（**固定，U5 由 UI 组定**）
----------------------------------
    几何值与字号：  round_half_up(v × 1.5)          —— 四舍五入（.5 一律进位）
    九宫格边距：    max(1, round_half_up(v × 1.5))  —— 同上，且下限 1（0 边距会退化为不切片）
其中 `round_half_up(x) = floor(x + 0.5)`。
**不用** Python 内置 `round()`：它是 banker's rounding（round-half-to-even），
对 7×1.5=10.5 会得 10、对 5×1.5=7.5 会得 8，同批数据出现两种进位方向，不可复现。
本脚本统一 half-up，跨语言（Python / TJS / JS）结果一致，故可写进 `UI清单.md` 作为交付口径。

×1.5 的字段（**白名单，其余一律不动**）
--------------------------------------
    x  y  w  h  item_w  item_h  gap  stack_bottom
    font.size  font.shadow_ofs
    nine.{l,t,r,b}（元素顶层 `nine` 与 `item_frame.nine` 两处）
**明确不 ×1.5**（对照 §9.3「line_spacing 不变」及语义判断，逐条见 §十）：
    z（层序）｜ opacity / item_frame.opacity / highlight.opacity（alpha 0–255，与画布无关）
    line_spacing（行距倍数）｜ max_rows / max_cols（**项数**，不是长度）｜ max_lines
    anim.period_ms（时间）｜ anim.count｜ scroll.page_size（**页内项数**）
    slot_base / index（槽号 / 序号）｜ 一切字符串字段

幂等
----
`_root.json` 写入 `"canvas_baseline": "1920x1080"` 标记；再次运行即识别为「已迁移」，
打印「已是 1920 基线，跳过」并**不写任何文件**（文件 md5 不变）。见 `--check`。

备份
----
迁移**前**把 `_root.json` 与 `screens/*.json` 复制到 `_工作/M12_备份_1280/`（只建不改）；
目录已存在时不覆盖，避免把已迁移版本冲掉备份。

用法
----
    cd "工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\工具"
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python migrate_1920.py            # 迁移（已迁移则跳过）
    python migrate_1920.py --check    # 只报告当前基线，不写文件
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)                          # …/UI组
LAYOUT = os.path.join(UI, "layout")
SCREENS = os.path.join(LAYOUT, "screens")
WORK = os.path.join(UI, "_工作")
BACKUP = os.path.join(WORK, "M12_备份_1280")
EVID = os.path.join(WORK, "M12_证据")

SCALE = 1.5
BASELINE_1280 = "1280x720"
BASELINE_1920 = "1920x1080"

# ── 字段白名单 ────────────────────────────────────────────────────────
GEOM_FIELDS = ("x", "y", "w", "h", "item_w", "item_h", "gap", "stack_bottom")
FONT_FIELDS = ("size", "shadow_ofs")
NINE_FIELDS = ("l", "t", "r", "b")

# ── §9.3 对照表（用于断言，防脚本自身算错）───────────────────────────
SPEC_CONTENT_BOXES = {
    "ot":  (360, 90, 1200, 900),
    "otr": (360, 90, 1200, 900),
    "ota": (360, 90, 1200, 900),
    "otp": (360, 90, 1200, 900),
    "otv": (240, 132, 1440, 816),
    "np":  (0, 0, 1920, 1080),
}
SPEC_FONT_SIZES = {"title": 69, "subtitle": 36, "name": 30, "body": 36,
                   "menu": 33, "small": 24, "tag": 27}

NEW_CONTENT_BOX_RULE = (
    "D1（第三条修订注·画布基线，2026-09-19）：设计画布 1920×1080，窗口化按 setZoom(2,3) 呈现 1280×720。"
    "4:3 源 800×600 按 ×1.5 迁移为 1200×900，居中于 (360,90)，左右各 360、上下各 90 黑边；"
    "otv 960×544 迁移为 1440×816，居中于 (240,132)；np 1920×1080 满幅。"
    "素材本体不放大——2× 超分素材按 ×1.5 呈现（= 0.75 倍下采样，更锐），不违反 D1 不放大原则。"
    "（过渡期口径；4:3→16:9 重制完成后按 04_1920画布与双分辨率方案 §5.2 的「按实际宽高比 contain」简化。）"
)

NEW_FONT_RULE = (
    "krkr 不自带字体，靠系统字体 + 运行时 Font.getList() 探测回退（工程缺口 G2）。"
    "字号按 1920×1080 画布定（M12 于 2026-09-20 由 1280×720 基线 ×1.5 迁移），"
    "不得沿用 1280×720 或 800×600 时代字号。"
)

# ── 文案同步（note 里内嵌的「画布派生数值」也要跟着改，否则留下假陈述）──
# 只改**由画布/坐标派生**的数字；**素材自身尺寸**（如「原版空白件 182×348」）属资产事实，
# 由素材侧（M11）负责，本脚本不动。键 = (文件, 元素 id, 字段)，值 = (旧全文, 新全文)。
NOTE_REWRITES = {
    ("01_title.json", "title.bg", "note"): (
        "标题背景（1280×720 满幅）",
        "标题背景（1920×1080 满幅）",
    ),
    ("10_dialog.json", "dlg.letterbox", "note"): (
        "留边底（最先绘制，铺满黑）。D1：4:3 源内容 1:1 居中，左右各 240px 黑边即由此而来。",
        "留边底（最先绘制，铺满黑）。D1：4:3 源内容 ×1.5 后为 1200×900，居中于 (360,90)，"
        "左右各 360px 黑边即由此而来。",
    ),
    ("10_dialog.json", "dlg.content", "note"): (
        "剧情背景层（压在留边底之上）：由编程组/演示层按当前场景源代号从根 content_boxes 取框位后填入"
        "（ot/otr/ota/otp→240,60,800,600；otv→160,88,960,544；np→0,0,1280,720）。"
        "此处 x/y/w/h 为 ot 框位默认值。",
        "剧情背景层（压在留边底之上）：由编程组/演示层按当前场景源代号从根 content_boxes 取框位后填入"
        "（ot/otr/ota/otp→360,90,1200,900；otv→240,132,1440,816；np→0,0,1920,1080）。"
        "此处 x/y/w/h 为 ot 框位默认值。",
    ),
    ("10_dialog.json", "dlg.window", "note"): (
        "对话窗底（原版空白贴图；宽 1057 = 画布 82.6%，比例与 1280×720 画布协调，无需拉伸）",
        "对话窗底（原版空白贴图；宽 1586 = 画布 82.6%，比例与 1920×1080 画布协调，无需拉伸）",
    ),
    ("10_dialog.json", "dlg.text", "note"): (
        "对话正文区（3 行 × 24px × 1.4 = 100.8px，容于 118px 高）",
        "对话正文区（3 行 × 36px × 1.4 = 151.2px，容于 177px 高）",
    ),
    ("31_fragment.json", "fragment.g6_grid", "note"): (
        "第 6 组碎片格阵（20 片，一屏 20 列 = 20 列 × 42px + 19 × 3px = 897px，容于 900px）",
        "第 6 组碎片格阵（20 片，一屏 20 列 = 20 列 × 63px + 19 × 5px = 1355px，"
        "**超出列表宽 1350px 5px**——M12 ×1.5 取整（gap 3→5，half-up）所致，见 _工作\\M12_迁移报告.md 未决项）",
    ),
    # ── 屏级 note（键用空串表示屏根 note）──
    ("10_dialog.json", "", "note"): (
        "本屏是游戏主界面的常驻层。对话窗底用 meswin（1057×174，原版空白贴图，无日文烘焙）1:1 居中贴底；"
        "名字框用 nm_frm_b（222×36）。所有文字由引擎绘制。",
        "本屏是游戏主界面的常驻层。对话窗底用 meswin（源件 1057×174，原版空白贴图，无日文烘焙），"
        "M12 起按 ×1.5 呈现为 1586×261、居中贴底；名字框用 nm_frm_b（源件 222×36，呈现 333×54）。"
        "所有文字由引擎绘制。（画布基线 1280×720 → 1920×1080，全部尺寸由 ×1.5 迁移而来。）",
    ),
    ("28_music.json", "", "note"): (
        "音乐鉴赏屏。底板自建（九宫格件 panel_frame.png + rect 填充；原版 mu_bg 为 PSV 整页音乐界面文字图，"
        "属 R1 类不可用），底图沿用 tl1_bg1。曲目条列表每行由引擎绘字；原版 gl_bgm01…12（1900×37）与 "
        "mc_bgm01…96（实存 58 件，2036×37）**经 M1 目视实测确认含烘焙曲名**"
        "（且宽度 1900/2036 > 画布 1280，亦不满足 R3 滚动前提），一律不用。"
        "播放控制为引擎绘字按钮；进度条滑块取原版空白件 cf_vbar(56×6)，1:1 摆放。⚠ 曲目内容为**演示数据**。",
        "音乐鉴赏屏。底板自建（九宫格件 panel_frame.png + rect 填充；原版 mu_bg 为 PSV 整页音乐界面文字图，"
        "属 R1 类不可用），底图沿用 tl1_bg1。曲目条列表每行由引擎绘字；原版 gl_bgm01…12（1900×37）与 "
        "mc_bgm01…96（实存 58 件，2036×37）**经 M1 目视实测确认含烘焙曲名**，一律不用"
        "（M12 备注：画布已由 1280 改为 1920，故 1900 宽现可容纳、2036 宽仍超出——"
        "但**主因仍是含烘焙曲名**，与画布宽度无关）。"
        "播放控制为引擎绘字按钮；进度条滑块取原版空白件 cf_vbar(源件 56×6)，按 ×1.5 摆放为 84×9。"
        "⚠ 曲目内容为**演示数据**。",
    ),
}


# ── 取整 ──────────────────────────────────────────────────────────────
def round_half_up(x: float) -> int:
    """四舍五入（.5 一律进位）。刻意不用内置 round()（banker's rounding，方向不定）。"""
    return int(math.floor(float(x) + 0.5))


def sc(v) -> int:
    return round_half_up(float(v) * SCALE)


def sc_nine(v) -> int:
    return max(1, sc(v))


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_state() -> tuple:
    """(_root.json md5, screens 聚合 md5)。用于幂等自证：两次运行应完全一致。"""
    root = os.path.join(LAYOUT, "_root.json")
    files = sorted(glob.glob(os.path.join(SCREENS, "*.json")))
    agg = hashlib.md5()
    for p in files:
        agg.update(os.path.basename(p).encode("utf-8"))
        agg.update(md5(p).encode("ascii"))
    return md5(root), agg.hexdigest(), len(files)


# ── 元素迁移 ──────────────────────────────────────────────────────────
def migrate_element(el: dict, where: str, changes: list, notes: list):
    """就地修改一个元素 dict；只动白名单字段。"""
    if not isinstance(el, dict):
        return
    eid = el.get("id", "?")
    tag = "%s/%s" % (where, eid)

    for k in GEOM_FIELDS:
        if k in el and is_num(el[k]):
            old = el[k]
            el[k] = sc(old)
            changes.append((tag, k, old, el[k]))

    font = el.get("font")
    if isinstance(font, dict):
        for k in FONT_FIELDS:
            if k in font and is_num(font[k]):
                old = font[k]
                font[k] = sc(old)
                changes.append((tag, "font." + k, old, font[k]))

    for container, prefix in ((el.get("nine"), "nine"),
                              ((el.get("item_frame") or {}).get("nine")
                               if isinstance(el.get("item_frame"), dict) else None,
                               "item_frame.nine")):
        if isinstance(container, dict):
            for k in NINE_FIELDS:
                if k in container and is_num(container[k]):
                    old = container[k]
                    container[k] = sc_nine(old)
                    changes.append((tag, "%s.%s" % (prefix, k), old, container[k]))
                    if old == 0:
                        notes.append("%s %s.%s: 0 -> 1（九宫格边距下限 1）" % (tag, prefix, k))


# ── 文案同步 ──────────────────────────────────────────────────────────
def rewrite_notes(data: dict, name: str, changes: list, applied: set):
    """把 note/source 里内嵌的旧画布派生数值改成新口径。文案与预期不符即硬失败。

    键用元素 id；**空串表示屏根 note**（`screens/*.json` 顶层 `note` 字段）。
    """
    targets = [(data, "")]
    for el in data.get("elements", []):
        if isinstance(el, dict):
            targets.append((el, el.get("id", "")))
    for holder, eid in targets:
        for k in ("note", "source"):
            t = holder.get(k)
            if not isinstance(t, str):
                continue
            rw = NOTE_REWRITES.get((name, eid, k))
            if not rw:
                continue
            old, new = rw
            if t != old:
                raise SystemExit(
                    "[FAIL] %s/%s 的 %s 与预期的 1280 基线文案不符，拒绝改写：\n"
                    "       期望：%r\n       实为：%r" % (name, eid or "<屏根>", k, old, t))
            holder[k] = new
            applied.add((name, eid, k))
            changes.append(("%s/%s" % (name, eid or "<屏根>"), k,
                            "<旧口径文案>", "<1920 口径文案>"))


# ── 根元数据迁移 ──────────────────────────────────────────────────────
def migrate_root(root: dict, changes: list):
    # canvas
    cv = root.get("canvas", {})
    for k in ("width", "height"):
        if k in cv:
            old = cv[k]
            cv[k] = sc(old)
            changes.append(("_root.json", "canvas." + k, old, cv[k]))

    # content_boxes（先按 ×1.5 算，再与 §9.3 对照表逐条断言）
    cbs = root.get("content_boxes", {})
    for name in ("ot", "otr", "ota", "otp", "otv", "np"):
        box = cbs.get(name)
        if not isinstance(box, dict):
            continue
        got = []
        for k in ("x", "y", "w", "h"):
            old = box[k]
            box[k] = sc(old)
            changes.append(("_root.json", "content_boxes.%s.%s" % (name, k), old, box[k]))
            got.append(box[k])
        want = list(SPEC_CONTENT_BOXES[name])
        if got != want:
            raise SystemExit("[FAIL] content_boxes.%s 迁移结果 %s 与 §9.3 对照表 %s 不符，已中止"
                             % (name, tuple(got), tuple(want)))

    # fonts.sizes
    sizes = root.get("fonts", {}).get("sizes", {})
    for k, old in list(sizes.items()):
        if not is_num(old):
            continue
        sizes[k] = sc(old)
        changes.append(("_root.json", "fonts.sizes." + k, old, sizes[k]))
        want = SPEC_FONT_SIZES.get(k)
        if want is not None and sizes[k] != want:
            raise SystemExit("[FAIL] fonts.sizes.%s 迁移结果 %s 与 §9.3 对照表 %s 不符，已中止"
                             % (k, sizes[k], want))

    # 文案（U6）
    changes.append(("_root.json", "content_box_rule", root.get("content_box_rule"), "<1920 口径文案>"))
    root["content_box_rule"] = NEW_CONTENT_BOX_RULE
    if "font_rule" in root:
        changes.append(("_root.json", "font_rule", root.get("font_rule"), "<1920 口径文案>"))
        root["font_rule"] = NEW_FONT_RULE

    # 幂等标记
    root["canvas_baseline"] = BASELINE_1920


# ── 备份 ──────────────────────────────────────────────────────────────
def backup_1280():
    os.makedirs(BACKUP, exist_ok=True)
    copied, kept = [], []
    pairs = [(os.path.join(LAYOUT, "_root.json"), os.path.join(BACKUP, "_root.json"))]
    for p in sorted(glob.glob(os.path.join(SCREENS, "*.json"))):
        pairs.append((p, os.path.join(BACKUP, os.path.basename(p))))
    for src, dst in pairs:
        if os.path.exists(dst):
            kept.append(os.path.basename(dst))
            continue
        shutil.copy2(src, dst)
        copied.append(os.path.basename(dst))
    return copied, kept


# ── main ──────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报告当前基线，不写文件")
    args = ap.parse_args()

    root_path = os.path.join(LAYOUT, "_root.json")
    root = json.load(open(root_path, encoding="utf-8"))

    canvas = root.get("canvas", {})
    marker = root.get("canvas_baseline")
    is_1920 = (marker == BASELINE_1920) or (canvas.get("width") == 1920 and canvas.get("height") == 1080)

    print("=" * 78)
    print("migrate_1920.py · UI 组 M12 布局 ×1.5 迁移（1280×720 -> 1920×1080）")
    print("  取整口径：几何/字号 round_half_up(v*1.5) ｜ 九宫格 max(1, round_half_up(v*1.5))")
    print("  layout : %s" % LAYOUT)
    print("  当前 canvas = %sx%s ｜ canvas_baseline = %r"
          % (canvas.get("width"), canvas.get("height"), marker))
    print("=" * 78)

    if is_1920:
        print("[SKIP] 已是 1920 基线，跳过（未写任何文件）。")
        r, a, n = digest_state()
        print("       幂等自证：_root.json md5=%s ｜ screens 聚合 md5=%s（%d 屏）" % (r, a, n))
        print("=" * 78)
        return 0

    if canvas.get("width") != 1280 or canvas.get("height") != 720:
        print("[FAIL] 当前 canvas 既非 1280×720 也非 1920×1080（%sx%s），拒绝迁移。"
              % (canvas.get("width"), canvas.get("height")))
        return 2

    if args.check:
        print("[CHECK] 当前为 1280×720 基线，**尚未迁移**（--check 不写文件）。")
        r, a, n = digest_state()
        print("        _root.json md5=%s ｜ screens 聚合 md5=%s（%d 屏）" % (r, a, n))
        return 0

    before = digest_state()
    copied, kept = backup_1280()
    print("[备份] %s" % os.path.relpath(BACKUP, UI))
    print("       新复制 %d 件：%s" % (len(copied), ", ".join(copied) if copied else "（无）"))
    if kept:
        print("       已存在未覆盖 %d 件（保留更早的 1280 版）：%s" % (len(kept), ", ".join(kept)))

    changes, notes = [], []
    migrate_root(root, changes)
    with open(root_path, "w", encoding="utf-8") as f:
        json.dump(root, f, ensure_ascii=False, indent=2)
        f.write("\n")

    files = sorted(glob.glob(os.path.join(SCREENS, "*.json")))
    per_file = {}
    applied = set()
    for p in files:
        name = os.path.basename(p)
        if name.startswith("_"):
            continue                                   # _index.json：屏清单，无几何数值
        data = json.load(open(p, encoding="utf-8"))
        n0 = len(changes)
        for el in data.get("elements", []):
            migrate_element(el, name, changes, notes)
        bg = data.get("bg")
        if isinstance(bg, dict):
            migrate_element(dict(bg, id="bg"), name, changes, notes)
        rewrite_notes(data, name, changes, applied)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        per_file[name] = len(changes) - n0

    missing = set(NOTE_REWRITES) - applied
    if missing:
        raise SystemExit("[FAIL] 以下文案改写点未命中（数据已漂移，请核对）：%s"
                         % ", ".join("%s/%s.%s" % m for m in sorted(missing)))

    # 证据落盘
    os.makedirs(EVID, exist_ok=True)
    ev = os.path.join(EVID, "迁移明细.json")
    with open(ev, "w", encoding="utf-8") as f:
        json.dump({"scale": SCALE,
                   "rounding": "geom/font: round_half_up(v*1.5); nine: max(1, round_half_up(v*1.5))",
                   "baseline_from": BASELINE_1280, "baseline_to": BASELINE_1920,
                   "field_count": len(changes),
                   "per_file": per_file,
                   "notes": notes,
                   "changes": [{"where": w, "field": k, "from": a, "to": b} for w, k, a, b in changes]},
                  f, ensure_ascii=False, indent=2)

    after = digest_state()
    print("-" * 78)
    print("[迁移] 共改写 %d 个字段（含 %d 处 note 内嵌画布派生数值的文案同步）"
          % (len(changes), len(applied)))
    for name in sorted(per_file):
        print("       %-20s %4d 字段" % (name, per_file[name]))
    if notes:
        print("[注意] %d 条下限修正：" % len(notes))
        for n in notes:
            print("       - %s" % n)
    print("[明细] %s" % os.path.relpath(ev, UI))
    print("-" * 78)
    print("[自证] 迁移前：_root.json md5=%s ｜ screens 聚合 md5=%s（%d 屏）" % before)
    print("[自证] 迁移后：_root.json md5=%s ｜ screens 聚合 md5=%s（%d 屏）" % after)
    print("[OK] 已迁移到 1920×1080 基线（canvas_baseline=%s）。再次运行应打印 [SKIP]。"
          % BASELINE_1920)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())