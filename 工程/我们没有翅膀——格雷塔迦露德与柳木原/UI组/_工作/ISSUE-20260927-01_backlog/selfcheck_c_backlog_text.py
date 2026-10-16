# -*- coding: utf-8 -*-
r"""ISSUE-20260927-01 · C 组自证脚本（只读工程文件、只写本证据目录）。

三个断言组：
  data    —— 从数据算四块文案的渲染盒：左沿 / 宽 / 字号 / 行高 / 首行行盒中线；
             断言「四块左沿同 x」「y + h ≤ item_h」「字号行距与设计口径一致」。
  ends    —— 两端消费点存在性 + 语义逐字校验（`文件::函数名`，不引行号）；
             并用「改坏一份内存副本」做**负向对照**（把 align 断言打废必须报 FAIL）。
  engine  —— 实机导图实测：四块墨迹左沿 + 首行墨迹带 vs 两个按钮带；
             给「改前（用户导图原样）/ 改后（按新 y 合成的示意）」对照图。

用法：
    python selfcheck_c_backlog_text.py
"""
import io, os, sys, json, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")
BACKUP = os.path.join(HERE, "原形备份", "26_backlog.json")
SHOT = os.path.join(WT, "临时", "ui_run", "runtime", "savedata", "shot_29_backlog.png")
KRKR_W = os.path.join(UI, "krkr", "game", "ui_widget.tjs")
KRKR_T = os.path.join(UI, "krkr", "game", "ui_theme.tjs")
HTML = os.path.join(UI, "复刻", "replica.js")

OUT = []
def say(s=""):
    OUT.append(s); print(s)

def log_to(path):
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")

def lst_of(d):
    return [e for e in d["elements"] if e["id"] == "bl.list"][0]

# ---------------------------------------------------------------- data
def check_data():
    say("=" * 78)
    say("【data】逐块文案渲染盒（从数据算；块内局部坐标 → 画布坐标）")
    d = json.load(io.open(SCREEN, encoding="utf-8"))
    e = lst_of(d); it = e["item_text"]
    size = (it.get("font") or e["font"])["size"]
    ls = it.get("line_spacing", d.get("line_spacing") or 1.4)
    lineH = int(size * ls)
    say("  item_text = %s" % json.dumps(it, ensure_ascii=False, sort_keys=True))
    say("  字号 = %s（%s）  行距系数 = %s  行高 = floor(%s×%s) = %d  最多 %s 行 ⇒ 文本块高 %d"
        % (size, "item_text.font" if it.get("font") else "list.font", ls, size, ls, lineH,
           it["max_lines"], lineH * it["max_lines"]))
    say("  list: x=%d y=%d w=%d item_h=%d gap=%d max_rows=%d  align=%s"
        % (e["x"], e["y"], e["w"], e["item_h"], e["gap"], e["max_rows"], e.get("align")))
    lefts, rights = [], []
    for i in range(e["max_rows"]):
        top = e["y"] + i * (e["item_h"] + e["gap"])
        L = e["x"] + it["x"]; R = L + it["w"]; T = top + it["y"]
        lefts.append(L); rights.append(R)
        say("   块%d  项矩形=(%d,%d,%d,%d)  文案盒=(左 %d, 上 %d, 右 %d, 下 %d)  "
            "首行行盒 %d..%d  中线 %s"
            % (i, e["x"], top, e["w"], e["item_h"], L, T, R, T + it["h"],
               T, T + lineH, T + lineH / 2.0))
    ok = True
    def assert_(cond, msg):
        nonlocal ok
        say("   %s %s" % ("PASS" if cond else "FAIL", msg))
        if not cond: ok = False
    assert_(len(set(lefts)) == 1, "四块左沿同一条竖线：%s（极差 %dpx）" % (lefts, max(lefts) - min(lefts)))
    assert_(len(set(rights)) == 1, "四块文案盒右沿一致：%s" % rights)
    assert_(it.get("align") == "left", "item_text.align = left（逐块左对齐）")
    assert_(it.get("valign") == "top", "item_text.valign = top（块内贴顶，按钮在首行侧）")
    assert_(it["y"] + it["h"] <= e["item_h"], "y + h = %d ≤ item_h %d（不触发出块守卫）"
            % (it["y"] + it["h"], e["item_h"]))
    assert_(lineH * it["max_lines"] == it["h"], "行高×最多行数 = 文本盒高（容量与盒一致）")
    # 按钮中线 vs 首行行盒中线
    bj = [b for b in e["item_buttons"] if b["key"] == "jump"][0]
    br = [b for b in e["item_buttons"] if b["key"] == "replay"][0]
    line1c = it["y"] + lineH / 2.0
    say("  按钮中线：jump y%d+h%d ⇒ %.1f ｜ replay y%d+h%d ⇒ %.1f ｜ 首行行盒中线 %.1f"
        % (bj["y"], bj["h"], bj["y"] + bj["h"] / 2.0, br["y"], br["h"],
           br["y"] + br["h"] / 2.0, line1c))
    assert_(abs(line1c - (bj["y"] + bj["h"] / 2.0)) <= 1.0,
            "首行行盒中线与 jump 中线同高（Δ=%.1fpx，设计口径 ≤1px）"
            % abs(line1c - (bj["y"] + bj["h"] / 2.0)))
    assert_(abs(line1c - (br["y"] + br["h"] / 2.0)) <= 1.0,
            "首行行盒中线与 replay 中线同高（Δ=%.1fpx）"
            % abs(line1c - (br["y"] + br["h"] / 2.0)))
    # 备份对比
    ob = json.load(io.open(BACKUP, encoding="utf-8"))
    oi = lst_of(ob)["item_text"]
    say("  原形备份（改前）item_text = %s" % json.dumps(oi, ensure_ascii=False, sort_keys=True))
    assert_(oi["y"] == 10 and it["y"] == 19, "本轮唯一数值改动：item_text.y 10 → 19")
    for k in ("x", "w", "h", "align", "valign", "wrap", "max_lines"):
        assert_(oi[k] == it[k], "item_text.%s 未变（%s）" % (k, it[k]))
    return ok

# ---------------------------------------------------------------- ends
ENDS = [
    (KRKR_W, "function uiWidgetItemText",
     'align: (it.align !== void) ? it.align : ((el.align !== void) ? el.align : "left")',
     "krkr 文案对齐缺省链：item_text.align → list.align → left"),
    (KRKR_W, "function uiWidgetDrawList",
     "align: itemTextSpec.align, valign: itemTextSpec.valign",
     "krkr 逐块文案把 align/valign 交给 uiWidgetDrawText"),
    (KRKR_T, "function uiThemeLayoutText",
     'var align = (el.align !== void) ? el.align : "left"',
     "krkr 行布局读 align（缺省 left）"),
    (KRKR_T, "function uiThemeRenderText",
     'if(layout.align == "center")',
     "krkr 逐行按 align 定 x（left ⇒ x = el.x，四块同左沿）"),
    (KRKR_W, "function uiWidgetDrawList",
     'var align = (el.align !== void) ? el.align : "center";',
     "krkr 【旧标签路径】缺省 center（本屏不走）：旧路径才是「按自身宽度居中」的成因"),
    (HTML, "function buildList",
     "labInner.style.textAlign = itemText.align || e.align || 'left'",
     "HTML 文案对齐缺省链：itemText.align → list.align → left"),
    (HTML, "function buildList",
     "lab.style.left = px(Number(itemText.x) || 0)",
     "HTML 文案盒左沿 = itemText.x（与 krkr uiWidgetItemLocalRect 同口径）"),
    (HTML, "function buildList",
     "lab.style.textAlign = e.align || 'center'",
     "HTML 【旧标签路径】缺省 center（本屏不走）"),
    (HTML, "function buildList",
     "var tLh = tSize * tLs;",
     "HTML 行高 = 字号 × 行距（与 krkr floor(size×line_spacing) 同口径）"),
]

def fn_body(src, fn):
    """该函数体的正文：从 `function <fn>` 起到下一个顶层 `\n  function ` 之前。"""
    i = src.find(fn)
    if i < 0:
        return ""
    j = src.find("\n  function ", i + 1)
    return src[i:j if j > 0 else len(src)]


def check_ends():
    say()
    say("=" * 78)
    say("【ends】两端消费点（文件::函数名；判据 = 该函数体内出现逐字相同的语句）")
    ok = True
    cache = {}
    for path, fn, needle, desc in ENDS:
        src = cache.get(path) or io.open(path, encoding="utf-8", errors="replace").read()
        cache[path] = src
        body = fn_body(src, fn)
        hit = (needle in body)
        say("  %s %s  [%s::%s]" % ("PASS" if hit else "FAIL", desc,
                                  os.path.basename(path), fn))
        if not hit: ok = False
    # 负向对照：把 align 判据打废 ⇒ 必须报 FAIL
    say("  --- 负向对照（内存副本，不写盘）：删掉 krkr 的 align 缺省链 ---")
    src = cache[KRKR_W]
    broken = src.replace(
        'align: (it.align !== void) ? it.align : ((el.align !== void) ? el.align : "left")',
        'align: "center"', 1)
    hit = ENDS[0][2] in fn_body(broken, "function uiWidgetItemText")
    say("  %s 负向对照：判据被打废后必须 FAIL（实测 %s）"
        % ("PASS" if not hit else "FAIL", "FAIL" if not hit else "PASS"))
    if hit: ok = False
    return ok

# ---------------------------------------------------------------- engine
def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

def ink_extent(px, box, thr_off=60, min_cols=2, lineH=42):
    """返回 (左沿, 右沿, 全墨迹行范围, 首行墨迹行范围)。首行 = 首个墨迹行起 lineH 内的行。"""
    x0, y0, w, h = box
    vals = sorted(lum(px[x, y]) for y in range(y0, y0 + h, 2) for x in range(x0, x0 + w, 2))
    thr = vals[len(vals) // 2] - thr_off
    cols, rows = [], []
    for x in range(x0, x0 + w):
        c = sum(1 for y in range(y0, y0 + h) if lum(px[x, y]) < thr)
        cols.append(c)
    for y in range(y0, y0 + h):
        c = sum(1 for x in range(x0, x0 + w) if lum(px[x, y]) < thr)
        rows.append(c)
    left = next((x0 + k for k, c in enumerate(cols) if c >= min_cols), None)
    right = next((x0 + k for k in range(len(cols) - 1, -1, -1) if cols[k] >= min_cols), None)
    rr = [y0 + k for k, c in enumerate(rows) if c >= min_cols]
    if not rr:
        return left, right, (None, None), (None, None)
    first = [y for y in rr if y < rr[0] + lineH]
    return left, right, (rr[0], rr[-1]), (first[0], first[-1])

def blue_extent(px, box):
    """按钮带：淡蓝/深蓝像素（B 明显大于 R）的纵向范围。"""
    x0, y0, w, h = box
    rr = []
    for y in range(y0, y0 + h):
        c = 0
        for x in range(x0, x0 + w):
            r, g, b = px[x, y]
            if b - r > 25 and b > 120:
                c += 1
        if c >= 3: rr.append(y)
    return (rr[0], rr[-1]) if rr else (None, None)

def check_engine(shot_path, meas_item_text, tag, crop_x=0, crop_y=0, panel_off=0):
    """在 shot_path 上按 meas_item_text 的几何量四块文案（左沿/右沿/墨迹行）。
    crop_x/crop_y/panel_off：图可能是「按列表矩形裁出的面板」（合成图用），需换算回数据坐标。"""
    say()
    say("=" * 78)
    say("【engine·%s】%s" % (tag, os.path.relpath(shot_path, WT) if os.path.exists(shot_path) else shot_path))
    if not os.path.exists(shot_path):
        say("  缺图，跳过（报告须说明）"); return None
    from PIL import Image
    im = Image.open(shot_path).convert("RGB"); px = im.load()
    d = json.load(io.open(SCREEN, encoding="utf-8")); e = lst_of(d)
    it = meas_item_text
    pitch = e["item_h"] + e["gap"]
    lefts, ink, ink1 = [], [], []
    for i in range(e["max_rows"]):
        top = e["y"] + i * pitch
        box = (e["x"] + it["x"] - crop_x, top + it["y"] - crop_y + panel_off, it["w"], it["h"])
        L, R, rr, f1 = ink_extent(px, box)
        kmy = crop_y - panel_off                       # 图坐标 → 数据坐标
        lefts.append(L + crop_x); ink.append((rr[0] + kmy, rr[1] + kmy))
        ink1.append((f1[0] + kmy, f1[1] + kmy))
        say("   块%d 项顶=%d  测量带 y=%d..%d（数据坐标）  墨迹左沿=%s 右沿=%s 全墨迹行=%s 首行墨迹行=%s 首行中线=%.1f"
            % (i, top, box[1] + kmy, box[1] + it["h"] + kmy, L + crop_x, R + crop_x,
               ink[-1], ink1[-1], (ink1[-1][0] + ink1[-1][1]) / 2.0))
    return lefts, ink, ink1


def check_engine_all(compo, compo_offset):
    d = json.load(io.open(SCREEN, encoding="utf-8")); e = lst_of(d); it = e["item_text"]
    pitch = e["item_h"] + e["gap"]
    ob = json.load(io.open(BACKUP, encoding="utf-8")); oi = lst_of(ob)["item_text"]
    ok = True
    def assert_(c, m):
        nonlocal ok
        say("   %s %s" % ("PASS" if c else "FAIL", m))
        if not c: ok = False

    # 改前：用**导图当时**的几何（原形备份的 y=10）
    r = check_engine(SHOT, oi, "改前·实机导图（用备份几何 y=10）", crop_x=0, crop_y=0)
    if r:
        lefts, ink, ink1 = r
        assert_(len(set(lefts)) == 1,
                "改前实机·四块墨迹左沿 = %s（极差 %dpx）⇒ 左沿本就一致" % (lefts, max(lefts) - min(lefts)))
        # 按钮带：数据（冻结）+ 态差 bbox 交叉验证
        bj = [b for b in e["item_buttons"] if b["key"] == "jump"][0]
        top0 = e["y"]
        y0, y1 = top0 + bj["y"], top0 + bj["y"] + bj["h"]
        say("   jump 胶囊带（数据·frozen）= y%d..%d ⇒ 中线 %.1f" % (y0, y1, (y0 + y1) / 2.0))
        # 态差证据（shot_29 vs shot_30：悬停那一帧）
        s30 = os.path.join(os.path.dirname(SHOT), "shot_30_backlog.png")
        if os.path.exists(s30):
            from PIL import Image, ImageChops
            A = Image.open(SHOT).convert("RGB"); B = Image.open(s30).convert("RGB")
            bbox = ImageChops.difference(A, B).getbbox()
            say("   态差 bbox（shot_29 vs shot_30，= jump 按钮实绘矩形）= %s" % (bbox,))
            assert_(bbox == (e["x"] + bj["x"], y0, e["x"] + bj["x"] + bj["w"], y1),
                    "态差矩形与数据 jump 矩形逐像素吻合 ⇒ 按钮带由该几何决定")
        deltas = []
        for i in range(len(ink1)):
            bc = e["y"] + i * pitch + bj["y"] + bj["h"] / 2.0
            ic = (ink1[i][0] + ink1[i][1]) / 2.0
            deltas.append(round(bc - ic, 1))
        say("   改前：各行「按钮中线 − 首行墨迹中线」Δ = %s（平均 %.1fpx）"
            % (deltas, sum(deltas) / len(deltas)))
        assert_(all(d > 8 for d in deltas),
                "改前·四块按钮都明显低于首行墨迹（Δ>8px）⇒ 这就是实机可见的「没对齐」")

    # 改后：改后**无实机渲染**（禁跑巡演）⇒ 用合成图（把文案带整体 +9px）量
    if compo:
        r2 = check_engine(compo, it, "改后·合成示意（y=19）",
                          crop_x=e["x"], crop_y=e["y"], panel_off=compo_offset)
        if r2:
            lefts2, ink2, ink12 = r2
            assert_(len(set(lefts2)) == 1,
                    "改后合成·四块墨迹左沿 = %s（极差 %dpx）⇒ 纵向平移不改变左沿"
                    % (lefts2, max(lefts2) - min(lefts2)))
            assert_(min(lefts2) >= e["x"] + it["x"],
                    "改后合成左沿 ≥ 数据左沿 %d（实测 %s，+1px 为字形留白）"
                    % (e["x"] + it["x"], lefts2))
            line1 = [e["y"] + i * pitch + it["y"] + 21 for i in range(4)]
            bc = [e["y"] + i * pitch + bj["y"] + bj["h"] / 2.0 for i in range(4)]
            say("   改后：首行行盒中线 %s vs 按钮中线 %s ⇒ Δ=%s"
                % (line1, bc, ["%.1f" % (b - l) for l, b in zip(line1, bc)]))
        say("   合成图：%s（下方面板 = 改后示意，面板偏移 %dpx）"
            % (os.path.basename(compo), compo_offset))
    return ok


def composite():
    say()
    say("=" * 78)
    say("【composite】改后示意合成（**非实机渲染**：只把每块文案带整体下移 9px，按钮/底板原样）")
    from PIL import Image, ImageDraw
    im = Image.open(SHOT).convert("RGB")
    d = json.load(io.open(SCREEN, encoding="utf-8")); e = lst_of(d); it = e["item_text"]
    ob = json.load(io.open(BACKUP, encoding="utf-8")); oi = lst_of(ob)["item_text"]
    dy = it["y"] - oi["y"]                                  # = 9
    pitch = e["item_h"] + e["gap"]
    X0, X1 = e["x"], e["x"] + e["w"]
    Y0, Y1 = e["y"], e["y"] + e["max_rows"] * pitch
    a = im.crop((X0, Y0, X1, Y1))
    b = a.copy(); pb = b.load()
    for i in range(e["max_rows"]):
        top = i * pitch
        tx, ty, tw, th = oi["x"], top + oi["y"], oi["w"], oi["h"]
        band = a.crop((tx, ty, tx + tw, ty + th))
        fill = a.crop((tx, ty + 70, tx + tw, ty + th))
        pf = fill.load()
        for x in range(tw):
            col = [pf[x, y] for y in range(0, fill.height, 4)]
            col.sort(key=lambda c: c[0] + c[1] + c[2])
            c = col[len(col) // 2]
            for y in range(dy):
                pb[tx + x, ty + y] = c
        b.paste(band, (tx, ty + dy))
    out = Image.new("RGB", (a.width, a.height * 2 + 8), (20, 24, 32))
    out.paste(a, (0, 0)); out.paste(b, (0, a.height + 8))
    dr = ImageDraw.Draw(out)
    bj = [x for x in e["item_buttons"] if x["key"] == "jump"][0]
    for y0, ty in ((0, oi["y"]), (a.height + 8, it["y"])):
        for i in range(e["max_rows"]):
            top = y0 + i * pitch
            dr.line([(4, top + bj["y"] + bj["h"] / 2.0), (out.width - 1, top + bj["y"] + bj["h"] / 2.0)],
                    fill=(220, 40, 40), width=1)
            dr.line([(4, top + ty + 21), (out.width - 1, top + ty + 21)], fill=(0, 170, 60), width=1)
    dr.text((6, 2), "BEFORE  item_text.y=10 : red=button centre(40.5)  green=first-line box centre(31)  gap 9.5px",
            fill=(255, 255, 255))
    dr.text((6, a.height + 12), "AFTER (synthetic shift +9px)  y=19 : red/green coincide (40.5 / 40)",
            fill=(255, 255, 255))
    p = os.path.join(HERE, "合成_改前改后_块内纵向对齐_1x.png")
    out.save(p)
    say("   已出图：%s（%dx%d；上=实机原样，下=合成示意；±%dpx 为唯一变量）"
        % (os.path.basename(p), out.width, out.height, dy))
    return p, a.height + 8


if __name__ == "__main__":
    ok = check_data()
    ok = check_ends() and ok
    compo, off = composite()
    ok = check_engine_all(compo, off) and ok
    say()
    say("总体：%s" % ("ALL PASS" if ok else "存在 FAIL"))
    log_to(os.path.join(HERE, "自证_终值.txt"))
    sys.exit(0 if ok else 1)
