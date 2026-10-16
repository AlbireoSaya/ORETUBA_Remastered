# -*- coding: utf-8 -*-
r"""M35b/M4 · 状态目标可达性验证 + 判据指纹（**不依赖引擎、纯数据 + 判据复算**）

■ 为什么需要它
  二审 Major-1 的教训：**探针天然绕开了 `uiScreenHoverAt`**（探针直接写 pressHit），
  所以「某个元素能不能被状态检测命中」这一类缺陷，探针与截图**都发现不了**。
  本脚本把 `krkr/game/ui_screens.tjs` 的判据与平票规则复算到数据上。

■ 本脚本实际覆盖什么、不覆盖什么（**M4 订正：此前写「任何改动后都能秒级复跑」属过度宣称**）
  覆盖：
    ① 逐屏断言「每个参与状态检测的元素（= 带 `state_assets` 的任何元素 ∪ 带非空 `state_group` 的 hit），
       在**它自己的几何中心**处，胜出者是它自己或同组元素」；每件元素按其**自身可见所需的 flag 取值**复算
       （`vis_flag` 为真），故 `flags_default` 关掉的元素也会在「它应该可见的那一态」下被检查。
    ② **判据指纹**：把 `ui_screens.tjs` 里 `uiScreenElementVisible` 与 `uiScreenHoverAtIn` 两个函数
       的正文（去注释、去空白后）做 sha256，并与本文件内记录的指纹比对；同时用**成对令牌表**
       （TJS 片段 ↔ 本文件的 python 复算片段）给出可读的一致性断言。
       ⇒ **判据被放宽/改写 ⇒ 本守门 FAIL**（这正是 M35b 一审的失效点：当时把判据换回宽松版仍报全绿）。
  不覆盖（**别把它当全量证明**）：
    · 只查**几何中心点**，不做整屏逐像素扫描 —— 被部分遮挡（中心没被覆盖）的元素不算失败；
      全像素扫描见 `工具\test_quickbar_reach.py`（点击/派发层）。
    · 不查**点击派发**（`uiScreenClick` 的 hit/list 解析）—— 那是另一套判据。
    · 不查 HTML 复刻端（`复刻/replica.js`），也不查引擎实测（探针/截图）。
    · 只覆盖 `layout/screens/*.json` 里当前带状态字段的元素；新增屏/新增元素会自动纳入。

■ 判据（**必须与 krkr/game/ui_screens.tjs 保持逐字一致**）
  候选 = 「带 state_assets 的任何元素」∪「带非空 state_group 的 hit」
  可见 = `visible_default !== false` 且 `vis_flag` 缺省或当前值满足 `vis_when`（`"*"` = 非空）
  平票 = z 相等时**声明更晚者胜**（TJS2 侧是 `if(z < bestZ) continue;`）
  ⚠️ 改引擎判据时必须同步本文件的 `JUDGE_FINGERPRINT` 与 `JUDGE_TOKENS`，否则本守门会 FAIL
     （这是**有意设计**：判据一动就必须有人重新确认这道守门还成立）。

■ 用法
  python 工具/test_state_targets.py        # 退出码 0 = 通过
"""
import os, io, json, glob, sys, re, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCREENS = os.path.join(UI, "layout", "screens")
TJS = os.path.join(UI, "krkr", "game", "ui_screens.tjs")


# ══════════════════════════════════════════════════════════════════════
# 一、数据侧复算
# ══════════════════════════════════════════════════════════════════════
def group_of(e):
    return e.get("state_group") or ""


def is_candidate(e):
    """与 uiScreenHoverAtIn 的判据一致（候选并集）。

    ★ M46（2026-09-23）：新增「**带逐项态图的 list**」（`item_frame.state_assets` 非空）——
      鼠标落在这种列表上要能按**项序号**点亮（见 `ui_widget.tjs` 的 `uiWidgetListItemState`
      与 `uiWidgetItemFrameAsset`）；判据只认「显式声明了逐项态图」的 list，普通列表不受影响。
    """
    if e.get("state_assets") is not None:
        return True
    if e.get("kind") == "list":
        fr = e.get("item_frame") or {}
        return fr.get("state_assets") is not None
    return e.get("kind") == "hit" and group_of(e) != ""


def flag_visible(e, flags):
    """与 uiScreenElementVisible 一致：visible_default 前置 + vis_flag/vis_when。"""
    if e.get("visible_default") is False:
        return False
    fn = e.get("vis_flag")
    if fn is None or fn == "":
        return True
    want = e.get("vis_when")
    want = "" if want is None else str(want)
    cur = flags.get(fn, "")
    if want == "*":
        return cur != ""
    return cur == want


def rect_of(e):
    """元素在命中测试里用的矩形 `(x, y, w, h)`。

    ★ M46（一审 Major-3 打回后补）：**list 在 layout JSON 里没有 `h` 键** —— 它的高度是
    渲染期按 `uiWidgetListSpan`（u_widget.tjs）算出来的：`行数 × item_h + (行数-1) × gap`，
    行数 = `min(标签数, max_rows)`（纵向 list）。原先直接 `e["h"]` ⇒ M46 把带逐项态图的 list
    放进候选并集后，`winner()` 一旦真的走到这一支就会 `KeyError` 崩掉（当前靠「该屏没有
    带 state_group 的元素、根本不会调 winner()」侥幸不炸）。这里按同一公式复算。"""
    if e.get("kind") == "list" and e.get("h") is None:
        item_h = float(e.get("item_h") or 0)
        gap = float(e.get("gap") or 0)
        n = len(e.get("labels") or [])
        if e.get("orientation") == "h":
            cols = int(e.get("max_cols") or n or 1)
            rows = max(1, -(-n // max(1, cols)))          # ceil
            item_w = float(e.get("item_w") or e.get("w") or 0)
            w = cols * item_w + (cols - 1) * gap
            h = rows * item_h + (rows - 1) * gap
            return (e.get("x", 0), e.get("y", 0), w, h)
        rows = max(1, min(n, int(e.get("max_rows") or n or 1)))
        h = rows * item_h + (rows - 1) * gap
        return (e.get("x", 0), e.get("y", 0), e.get("w") or 0, h)
    return (e.get("x", 0), e.get("y", 0), e.get("w", 0), e.get("h", 0))


def winner(els, x, y, flags):
    """复算 uiScreenHoverAtIn：返回胜出元素（None = 无）。"""
    best_z, best = -1, None
    for e in els:
        if not is_candidate(e):
            continue
        if not flag_visible(e, flags):
            continue
        ex, ey, ew, eh = rect_of(e)
        if not (ex <= x < ex + ew and ey <= y < ey + eh):
            continue
        if e.get("z", 0) < best_z:
            continue
        best_z, best = e.get("z", 0), e
    return best


def flags_for(e, base):
    """让**本元素自身可见**所需的 flag 取值（其它 flag 保持屏级初值）。"""
    f = dict(base)
    fn = e.get("vis_flag")
    if fn:
        want = e.get("vis_when")
        f[fn] = "1" if (want is None or str(want) == "*") else str(want)
    return f


# ══════════════════════════════════════════════════════════════════════
# 二、判据指纹（TJS 源码 ↔ 本文件复算）
# ══════════════════════════════════════════════════════════════════════
JUDGE_FUNCS = ("uiScreenElementVisible", "uiScreenHoverAtIn")

# ★ 记录的是「去注释、去空白」后的函数正文 sha256。判据一改即不匹配 ⇒ FAIL。
#   更新办法：先人工核对 TJS 新判据，确认本文件的 winner()/is_candidate()/flag_visible()
#   仍与之一致，再运行 `python 工具/test_state_targets.py --print-fingerprint` 取新值贴回。
JUDGE_FINGERPRINT = {
    "uiScreenElementVisible":
        "a985f281284603ae27ec9f3468b403a8217072e38c2708a9813062d3901a259d",   # 319 字节
    "uiScreenHoverAtIn":
        "2c72e1bc8c01f152fb5c49abb60ead1b3c454a7ac379f9f51cc8ef53648d1c1c",   # 679 字节（M46 加入「带逐项态图的 list」分支）
}

# 成对令牌表：(环节, TJS 片段【去空白后】, 本文件 python 片段【原样】)
JUDGE_TOKENS = (
    ("候选并集·带 state_assets 的任何元素",
     'if(el.state_assets===void){', 'e.get("state_assets") is not None'),
    ("候选并集·缺态图时只认 kind==hit",
     'if(el.kind!="hit")continue;', 'e.get("kind") == "hit"'),
    ("候选并集·★ M46 带逐项态图的 list 也是状态目标",
     'if(el.kind=="list"){', 'e.get("kind") == "list"'),
    ("候选并集·热区必须带非空 state_group",
     'if(uiWidgetStateGroup(el)=="")continue;', 'group_of(e) != ""'),
    ("可见性·visible_default 前置",
     'if(el.visible_default===false)returnfalse;', 'e.get("visible_default") is False'),
    ("可见性·vis_flag / vis_when 成对",
     'varfn=el.vis_flag;', 'e.get("vis_flag")'),
    ("可见性·vis_when 通配 \"*\" = 非空即显示",
     'if(want=="*")return(cur!="");', 'if want == "*":'),
    ("平票·z 相等时声明更晚者胜",
     'if(z<bestZ)continue;', 'e.get("z", 0) < best_z'),
)


def strip_tjs_comments(src):
    """去掉 // 与 /* */ 注释（保留字符串字面量）。"""
    out, i, n = [], 0, len(src)
    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1]); i = j + 1
        else:
            out.append(src[i]); i += 1
    return "".join(out)


def squeeze(src):
    return re.sub(r"\s+", "", src)


def extract_func(norm, name):
    """从**已去注释、已去空白**的源码里取出 function <name>(...){...} 全文。"""
    i = norm.find("function%s(" % name)
    if i < 0:
        return None
    j = norm.find("{", i)
    if j < 0:
        return None
    depth = 0
    for k in range(j, len(norm)):
        if norm[k] == "{":
            depth += 1
        elif norm[k] == "}":
            depth -= 1
            if depth == 0:
                return norm[i:k + 1]
    return None


def check_fingerprint(tjs_text, print_only=False):
    """返回 (失败清单, 打印行)；打印新指纹模式不判失败。"""
    fails, lines = [], []
    norm = squeeze(strip_tjs_comments(tjs_text))
    for name in JUDGE_FUNCS:
        body = extract_func(norm, name)
        if body is None:
            fails.append("判据指纹：在 ui_screens.tjs 里找不到函数 %s()（被改名/删除？）" % name)
            continue
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()
        lines.append("  %-26s sha256=%s  (%d 字节)" % (name, h, len(body)))
        if print_only:
            continue
        if JUDGE_FINGERPRINT.get(name) != h:
            fails.append("判据指纹：%s() 正文已被改写（期望 %s…，实际 %s…）—— 先核对新判据，"
                         "再更新本文件的 JUDGE_FINGERPRINT"
                         % (name, (JUDGE_FINGERPRINT.get(name) or "?")[:12], h[:12]))
    return fails, lines


def strip_py_comments(src):
    """去掉 python 注释（**尊重字符串字面量**内的 `#`）。

    ★ M46（一审 Major-3 的连带修复）：`check_tokens` 原先在「去掉 JUDGE_TOKENS
    表之后」**全文**找 token 串 —— 于是**注释里提到该串**也会被算成「判据代码还在」。
    实测：把 `is_candidate` 的组守卫整行删掉（自证 C 的变异），只因别处一句注释里写了同样的
    串，令牌检查照样全绿 ⇒ 自证 C 长期**假通过**。这里按「逐字符扫描、引号内不算注释」剥注释，
    使 token 只可能命中**真代码**。
    """
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == "'" or c == '"':
            q = c
            if src[i:i + 3] in ('"""', "'''"):
                q = src[i:i + 3]
            out.append(q)
            i += len(q)
            while i < n:
                if src[i] == "\\":
                    out.append(src[i:i + 2]); i += 2; continue
                if src.startswith(q, i):
                    out.append(q); i += len(q); break
                out.append(src[i]); i += 1
            continue
        if c == "#":
            while i < n and src[i] != "\n":
                i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


def py_code_only(src):
    """留给 token 检查的「真代码」：先去掉 `JUDGE_TOKENS` 表字面量本身（否则「期望令牌」
    会被算作「代码里有」），再剥掉注释（见 `strip_py_comments` 的长注释）。"""
    i = src.find("JUDGE_TOKENS = (")
    if i >= 0:
        j = src.find("\n)\n", i)
        if j >= 0:
            src = src[:i] + src[j:]
    return strip_py_comments(src)


def check_tokens(tjs_text, py_text):
    """成对令牌：TJS 判据片段与 python 复算片段必须同时存在（**表字面量除外**）。"""
    fails, lines = [], []
    tjs_norm = squeeze(strip_tjs_comments(tjs_text))
    py_code = py_code_only(py_text)
    for what, tjs_tok, py_tok in JUDGE_TOKENS:
        bad = []
        if tjs_tok not in tjs_norm:
            bad.append("ui_screens.tjs 里找不到 %s" % tjs_tok)
        if py_tok not in py_code:
            bad.append("本文件 python 复算里找不到 %s" % py_tok)
        if bad:
            fails.append("判据令牌·%s：%s" % (what, "；".join(bad)))
        else:
            lines.append("  ✓ %s" % what)
    return fails, lines


def check_reach(docs):
    """docs = [(屏名, 屏对象), …]；返回 (失败清单, 覆盖统计, 跳过清单)。"""
    fails = []
    n_a = n_g = 0
    skipped = []
    for name, d in docs:
        els = d.get("elements") or []
        base = d.get("flags_default") or {}
        for e in els:
            # ★ M46（一审 Major-3）：判据与 uiScreenHoverAtIn 的候选并集一致 ——
            #   `state_assets` 非空、或 `state_group` 非空的 hit、**或带逐项态图的 list**。
            #   初版这里仍写 `group_of(e) == "" → 跳过`，导致 M46 新纳入的候选类
            #   （ch.choices 无 state_group）在可达性断言上零覆盖。
            if not is_candidate(e):
                continue
            if group_of(e) == "" and e.get("state_assets") is None                and not (e.get("kind") == "list"
                        and (e.get("item_frame") or {}).get("state_assets") is not None):
                continue
            # 元素**永不显示**（visible_default=false 且无 vis_flag 可救）⇒ 本就不该期望它悬停可亮
            if e.get("visible_default") is False:
                skipped.append("%s :: %s（visible_default=false）" % (name, e.get("id")))
                continue
            # 计数口径：a = 靠**自身态图**（含 list 的**逐项**态图）；g = 靠 state_group 绑定
            has_item_states = (e.get("kind") == "list"
                               and (e.get("item_frame") or {}).get("state_assets") is not None)
            if e.get("state_assets") is not None or has_item_states:
                n_a += 1
            else:
                n_g += 1
            flags = flags_for(e, base)
            rx, ry, rw, rh = rect_of(e)
            cx = rx + rw / 2.0
            cy = ry + rh / 2.0
            w = winner(els, cx, cy, flags)
            # 期望：同组胜出；**无组的候选**（带 state_assets 的元素 / 带逐项态图的 list）
            # 期望胜出的是**它自己**（它没有组可依靠）。
            # ⚠️ 这里刻意**不**写出字面量 `group_of(e) != ""` —— 那是 JUDGE_TOKENS 里
            #    「热区必须带非空 state_group」那一对 token 的判别串；本文件其它地方再出现一次，
            #    自证 C（把判据换回宽松版）就会因为「别处还留着该串」而假通过（M46 一审踩过）。
            ge = group_of(e)
            gw = group_of(w) if w is not None else "无"
            ok = (w is not None) and ((gw == ge) if ge else (w["id"] == e["id"]))
            if not ok:
                fails.append("%s :: %s 中心(%g,%g) 胜出 %s（组 %s），期望 %s"
                             % (name, e["id"], cx, cy,
                                w["id"] if w else "(无)", gw,
                                ("同组 " + ge) if ge else "它自己"))
    return fails, (n_a, n_g), skipped


def load_docs():
    out = []
    for f in sorted(glob.glob(os.path.join(SCREENS, "[0-9]*.json"))):
        out.append((os.path.basename(f), json.load(io.open(f, encoding="utf-8"))))
    return out


# ══════════════════════════════════════════════════════════════════════
# 三、主流程
# ══════════════════════════════════════════════════════════════════════
def selfcheck():
    """反向自证（全部在内存里做，**不动磁盘**）：两项都必须 FAIL。"""
    tjs = io.open(TJS, encoding="utf-8").read()
    py_src = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    docs = load_docs()
    ok = True

    # ── A：注入一件 z=999 的异组遮挡，盖住某一状态目标的几何中心 ──
    victim_f, victim = None, None
    for name, d in docs:
        base = d.get("flags_default") or {}
        for e in d.get("elements") or []:
            if group_of(e) and is_candidate(e) and e.get("visible_default") is not False:
                victim_f, victim = name, e
                break
        if victim:
            break
    d2 = dict((n, x) for n, x in docs)
    for name, d in docs:
        if name != victim_f:
            continue
        dd = json.loads(json.dumps(d))
        cx = victim["x"] + victim["w"] / 2.0
        cy = victim["y"] + victim["h"] / 2.0
        dd["elements"].append({"id": "zz.occluder", "kind": "hit", "z": 999,
                               "action": "open_sysmenu", "label": "", "note": "自证注入",
                               "x": cx - 2, "y": cy - 2, "w": 4, "h": 4,
                               "state_group": "zz.other"})
        d2[name] = dd
    f, _, _ = check_reach([(n, d2[n]) for n, _ in docs])
    hit = any(("zz.occluder" in x) and (victim["id"] in x) for x in f)
    print("【A 注入 z=999 异组遮挡（盖住 %s 的中心）】必须 FAIL ⇒ %s"
          % (victim["id"], "FAIL（符合预期）✓" if hit else "**未按预期 FAIL** ✗"))
    for x in f[:4]:
        if "zz.occluder" in x:
            print("    ✗ " + x)
    ok = ok and hit

    # ── B：把 TJS 判据**临时放宽**（在内存副本里，不动原文件）──
    loosened = tjs.replace('if(uiWidgetStateGroup(el) == "") continue;',
                           '/* 自证：临时放宽掉「必须带非空组」 */')
    if loosened == tjs:
        loosened = tjs.replace('if(uiWidgetStateGroup(el) == "") continue;', '')
    b1, _ = check_fingerprint(loosened)
    b2, _ = check_tokens(loosened, py_src)
    print("\n【B 把 TJS 判据临时放宽（删掉「必须带非空组」守卫）】指纹检查必须 FAIL ⇒ %s"
          % ("FAIL（符合预期）✓" if b1 and b2 else "**未按预期 FAIL** ✗"))
    for x in (b1 + b2)[:4]:
        print("    ✗ " + x)
    ok = ok and bool(b1) and bool(b2)

    # ── C：把**本文件的 python 复算**放宽（= 「换回收紧前的宽松版」）──
    # 拼接出待替换串：本文件里**任何一处**出现该字面量都会让 check_tokens 误判「判据还在」
    # （check_tokens 只剥 JUDGE_TOKENS 表本身，不剥其它字符串），故这里不写字面量。
    _guard = '    return e.get("kind") == "hit" and group_of(e) ' + chr(33) + '= ""'
    py_loose = py_src.replace(_guard, '    return e.get("kind") == "hit"')
    assert py_loose != py_src, "自证 C 未生效：python 判据行没被改写"
    c1, _ = check_tokens(tjs, py_loose)
    print("\n【C 把本文件 python 判据换回**收紧前的宽松版**（候选并集去掉「必须有组」）】"
          "令牌检查必须 FAIL ⇒ %s" % ("FAIL（符合预期）✓" if c1 else "**未按预期 FAIL** ✗"))
    for x in c1[:4]:
        print("    ✗ " + x)
    ok = ok and bool(c1)

    print("\n自证结果：%s" % ("三项均按预期 FAIL ✓" if ok else "**有项未按预期 FAIL** ✗"))
    return 0 if ok else 1


def main():
    print_only = "--print-fingerprint" in sys.argv
    if "--selfcheck" in sys.argv:
        print("=" * 74)
        print("状态目标守门 · 反向自证（内存内构造，不改磁盘）")
        print("=" * 74)
        return selfcheck()

    tjs = io.open(TJS, encoding="utf-8").read()
    py_src = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    fails = []
    print("=" * 74)
    print("状态目标可达性验证 ｜ 数据=%s" % SCREENS)

    # ── 1. 判据指纹 ──
    fp_fails, fp_lines = check_fingerprint(tjs, print_only)
    print("\n[1] 判据指纹（ui_screens.tjs ↔ 本文件复算）")
    for l in fp_lines:
        print(l)
    if print_only:
        print("（--print-fingerprint：只打印，不判失败）")
    fails += fp_fails
    if not print_only:
        tk_fails, tk_lines = check_tokens(tjs, py_src)
        print("\n[2] 判据令牌（成对一致性）")
        for l in tk_lines:
            print(l)
        for f in tk_fails:
            print("  ✗ " + f)
        fails += tk_fails

    # ── 2. 可达性（态图+组 ∪ 纯组热区）──
    doc_fails, (n_a, n_g), skipped = check_reach(load_docs())
    print("\n[3] 可达性（几何中心）")
    print("  覆盖：态图+组 %d 件 ｜ 纯组热区 %d 件 ⇒ 合计 %d 件（按各自可见所需的 flag 取值复算）"
          % (n_a, n_g, n_a + n_g))
    for s in skipped:
        print("  – 跳过 " + s)
    for f in doc_fails:
        print("  ✗ " + f)
    fails += doc_fails

    print("\n" + "=" * 74)
    if fails:
        print("结果：**%d 项失败**" % len(fails))
        for f in fails:
            print("  · " + f)
        return 1
    print("结果：**全部通过**（判据指纹一致 + %d 件元素几何中心可达）" % (n_a + n_g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
