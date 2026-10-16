# -*- coding: utf-8 -*-
r"""test_text_ellipsis.py —— 「超框省略号」冻结期望表闸门（ISSUE-20260930-02 · 任务 A）

■ 判据出处（唯一依据，改前必读）
    `工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作\ISSUE-20260930-02_章节详情\接口冻结.md` §五
    （折行后行数 > `max_lines` ⇒ ① 保留前 `max_lines` 行；② **末行尾部追加 `……`（两个 U+2026）**，
      追加前**逐字回退**到 `宽度(末行 + "……") ≤ maxW`；③ 连 `……` 都放不下（`maxW - 宽度("……") ≤ 0`）
      ⇒ **该行不画**；④ 纯渲染、不参与布局）

■ 这张闸门查什么（同一张冻结期望表喂给**两端**）
    ① **HTML 侧实现**：`复刻/replica.js::wrapEllipsisLines()`（**渲染路径**也走它 —— 见
       `resolveClampCands`）。用**无头 Edge** 跑 `复刻/_probe_text_ellipsis.html`（同一份 replica.js，
       探针不自带实现），把「输入串 → 返回行」取回来。
    ② **Python 侧折算**：`gen_flow_layout.ui_theme_wrap`（折行）＋ `gen_flow_layout.apply_ellipsis`
       （省略号收尾）—— ★ **第 15 批归并后的唯一 Python 实现**（原先本文件自带一份内联 port、
       `复现脚本/m57_intro_fit.py` 另带一份 `ellipsize`，两份分叉 ⇒ 已统一到生成器一处；
       本文件只剩一个 3 行的适配器 `wrap_ellipsis()`）。
    断言（逐条对每个用例）：
      · 行数 / 是否截断 / 是否「少画一行」；
      · 末行是否以 `……` 结尾、且**不得**是 ASCII `...`；
      · 每行宽度（各自用**本端**度量）≤ 预算：末行（带 …… 时）≤ maxW；其余行 ≤ maxW＋一个字
        （行首禁则会把一个禁则字符**强行并入**上一行，这是 krkr 的既有行为，非本批引入）；
      · 末行前缀**已回退**（回退后放不上下一个字）—— 证明「逐字回退」判据非恒真；
      · 行首禁则：没有任何一行以禁则头字符开头（用例 `nohead_tail` 里 `）` 必须被并进上一行）；
      · **两端返回的行逐字相同**（同一判据 + 同族字体的直接证据）。

■ `--selfcheck`（变异自证，**判据必须非恒真**）
    把两端的省略号收尾关掉（Python：`ellipsis_on=False`；HTML：探针 URL 加 `&noellip=1`，
    由 replica.js 的 `UI_ELLIP_NOELLIP` 开关实现）⇒ 两端都必须**至少一个用例失败**。
    若关掉后仍全绿，说明该表恒真、没有牙齿 ⇒ 本步失败。

■ 用法
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python 工具/test_text_ellipsis.py            # 退出码 0 = 全过
    python 工具/test_text_ellipsis.py --selfcheck
    python 工具/test_text_ellipsis.py --no-html  # 无 Edge 时只跑 Python 折算（**会明确标注未跑 HTML**）

■ 落盘纪律：无头 Edge 的 `--user-data-dir` 与 DOM dump 一律落在**工作区内**的本 worktree `临时\`
    （`<worktree>\临时\ui_edge_probe\`，已被 .gitignore 的 `/临时/` 覆盖）⇒ **不产生 git 漂移**。
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))          # …\UI组\工具
UI = os.path.dirname(HERE)                                  # …\UI组
REP = os.path.join(UI, "复刻")
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))  # …\<worktree>（krkr\ 的 run_autotour.bat 同算法）
SCRATCH = os.path.join(WT, "临时", "ui_edge_probe")         # ★ 工作区内、且被 .gitignore 忽略

sys.path.insert(0, HERE)                                    # 同目录：取生成器的**唯一** Python 实现
import gen_flow_layout as G                                 # noqa: E402

PROBE = "_probe_text_ellipsis.html"
SIZE = 24                                                    # 冻结表口径：`fc.p_text_tx` 是 24px

# ---------------------------------------------------------------- 判据常量（三处同值）
DOTS = "……"                                                  # **两个 U+2026**（不得用 "..."）
NOHEAD = "、。，．！？：；）」』】》〉”’!?,.:;)]}"             # = ui_theme.tjs::UIThemeNoHeadChars
NOTAIL = "（「『【《〈“‘([{"                                  # = ui_theme.tjs::UIThemeNoTailChars

# ---------------------------------------------------------------- 冻结期望表
#   构造原则：只用 CJK 汉字 ＋ 显式 `\n` ⇒ 每字 1 em（24px）在**任何** CJK 字体下一致，
#   故「行数 / 后缀 / 预算」三项在 PIL 实测与浏览器实测下同值（不依赖具体字体文件）。
CASES = [
    # ① 明显超长中文串（216 字）：14 字/行 × 16 行 ⇒ 截到 4 行，末行回退后带 ……
    dict(id="long216", text="字" * 216, maxW=344, maxLines=4,
         nlines=4, truncated=True, dropped=False, ends_dots=True, last_prefix_lt_full=True),
    # ② 恰好不超（构造 3 行）⇒ 不截断、不加省略号
    dict(id="exact3", text="甲乙丙\n丁戊己\n庚辛壬", maxW=344, maxLines=4,
         nlines=3, truncated=False, dropped=False, ends_dots=False),
    # ③ 第 4 行只剩 1 字即溢出（第 5 行触发截断）⇒ 末行 = 「癸……」（无需回退，直接追加）
    dict(id="short4th", text="甲乙丙\n丁戊己\n庚辛壬\n癸\n子", maxW=344, maxLines=4,
         nlines=4, truncated=True, dropped=False, ends_dots=True, last_exact="癸……"),
    # ④ 末字符是**行首禁则**字符「）」：它被迫并入上一行（行 1 以「）」结尾），
    #    且**任何一行都不得以禁则头字符开头**；本用例同时考「回退 + 省略号」
    dict(id="nohead_tail", text=("字" * 14) + "）" + ("字" * 60), maxW=344, maxLines=4,
         nlines=4, truncated=True, dropped=False, ends_dots=True,
         last_prefix_lt_full=True, line0_ends="）", no_line_starts_nohead=True),
    # ⑤ 极窄 maxW=24（连「……」都放不下：宽度("……")=40 > 24）⇒ **该行不画**（比上限少一行）
    dict(id="narrow24", text="字" * 20, maxW=24, maxLines=4,
         nlines=3, truncated=True, dropped=True, ends_dots=False, no_line_starts_nohead=True),
    # ⑥ 回退的独立复核：100 字 / maxLines=2 ⇒ 末行必是「回退后的满行 + ……」
    dict(id="backoff2", text="字" * 100, maxW=344, maxLines=2,
         nlines=2, truncated=True, dropped=False, ends_dots=True, last_prefix_lt_full=True),
]

PASS = 0
FAIL = 0


def say(ok, what, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print("  %s %s%s" % ("PASS" if ok else "FAIL", what, ("   ｜ " + detail) if detail else ""))
    return ok


# ---------------------------------------------------------------- 度量（Python 侧）
def make_wof(size=SIZE):
    """返回 (width_of, 来源说明)。优先 PIL + 系统 msyh（= layout 的 fallback_faces[0]）。"""
    try:
        from PIL import ImageFont
        for p in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"):
            if os.path.exists(p):
                f = ImageFont.truetype(p, size)
                return (lambda s: float(f.getlength(s))), "PIL:%s@%d" % (os.path.basename(p), size)
    except Exception:
        pass

    def approx(s):
        w = 0.0
        for ch in s:
            # 全角（CJK 汉字 / 全角标点 / 「…」等省略号）
            w += size if (ord(ch) >= 0x2E80 or ch in "…‥—～·！？：；（）「」『』【】、。") else size * 0.5
        return w
    return approx, "class-width(近似：CJK+全角标点=size、其余=0.5size)"


# ---------------------------------------------------------------- Python 侧折算 port
def wrap_ellipsis(text, maxW, maxLines, wof, ellipsis_on=True):
    r"""折行 + 超框省略号 = **调用生成器的单一实现**（第 15 批归并）。

    · 折行：`gen_flow_layout.ui_theme_wrap(text, maxW, 0, wof)`（`maxLines=0` ⇒ 先拿**完整**折行）；
    · 省略号：`gen_flow_layout.apply_ellipsis(lines, maxW, maxLines, wof)`（冻结书 §五 的语义逐字实现）。
    ★ 本文件**不再自带折算实现**（第 15 批把原先分叉的两份 Python 折算 —— 本文件的内联 port 与
      `_工作/ISSUE-20260930-02_章节详情/复现脚本/m57_intro_fit.py::ellipsize` —— 归并到
      `工具/gen_flow_layout.py::apply_ellipsis` 一处）。本函数只是**适配器**（把生成器的两个函数串起来）。
    `ellipsis_on=False` **仅供 `--selfcheck` 构造变异**：关掉省略号收尾（复现改前的「整行直接丢弃」），
    不属生产路径。返回 `(lines, truncated, dropped)`。
    """
    lines, _tr0 = G.ui_theme_wrap(text, maxW, 0, wof)     # maxLines=0 ⇒ 不做任何截断
    over = bool(maxLines and maxLines > 0 and len(lines) > maxLines)
    if not ellipsis_on:                                    # ★ 变异（非生产路径）
        return (list(lines[:maxLines]) if over else list(lines)), over, False
    lines2, ellipsized, _notes = G.apply_ellipsis(lines, maxW, maxLines, wof)
    dropped = bool(ellipsized and maxLines and len(lines2) < maxLines)
    return lines2, ellipsized, dropped


# ---------------------------------------------------------------- 断言（两端共用）
def check_impl(name, lines_list, flags_list, wof, cases, charW, dotsW, widths_list=None):
    """lines_list / flags_list 与 cases 一一对应（flags = dict(truncated, dropped)）。
    widths_list 给了就用它（= **该端自己实测**的行宽，HTML 侧来自探针），否则用 wof 现算。"""
    ok_all = True
    for ci, (c, lines, fl) in enumerate(zip(cases, lines_list, flags_list)):
        tag = "%s/%s" % (name, c["id"])
        bad = []
        if len(lines) != c["nlines"]:
            bad.append("行数 %d≠%d" % (len(lines), c["nlines"]))
        if bool(fl.get("truncated")) != bool(c["truncated"]):
            bad.append("truncated=%s≠%s" % (fl.get("truncated"), c["truncated"]))
        if bool(fl.get("dropped")) != bool(c["dropped"]):
            bad.append("dropped=%s≠%s" % (fl.get("dropped"), c["dropped"]))
        got_dots = bool(lines) and lines[-1].endswith(DOTS)
        if got_dots != bool(c["ends_dots"]):
            bad.append("末行带……%s≠%s（末行=%r）" % (got_dots, c["ends_dots"], lines[-1] if lines else ""))
        if any("..." in x for x in lines):
            bad.append("出现 ASCII '...'（冻结书禁止）")
        if "last_exact" in c and (not lines or lines[-1] != c["last_exact"]):
            bad.append("末行 %r≠%r" % (lines[-1] if lines else None, c["last_exact"]))
        if c.get("line0_ends") and (not lines or not lines[0].endswith(c["line0_ends"])):
            bad.append("首行未以禁则字符 %r 结尾（行首禁则未生效）" % c["line0_ends"])
        if c.get("no_line_starts_nohead"):
            hit = [x for x in lines if x and x[0] in NOHEAD]
            if hit:
                bad.append("有行以禁则头字符开头：%r" % hit[0])
        # 预算：末行（带 …… 时）必须 ≤ maxW；其余行允许「行首禁则强行并入」的 +1 字
        widths = widths_list[ci] if widths_list else [wof(x) for x in lines]
        tol = 0.5 if got_dots else charW
        over = [("%r=%.1f" % (lines[i], widths[i])) for i in range(len(lines))
                if widths[i] > c["maxW"] + (tol if i == len(lines) - 1 else charW)]
        if over:
            bad.append("行超预算 maxW=%d（+%s）：%s" % (c["maxW"], tol, "、".join(over[:3])))
        if got_dots and widths and widths[-1] > c["maxW"] + 0.5:
            bad.append("末行（带 ……）宽 %.1f > maxW=%d" % (widths[-1], c["maxW"]))
        # 末行前缀「已回退」：再放一个字就超预算 ⇒ 回退判据非恒真
        if c.get("last_prefix_lt_full"):
            full = max(1, int(c["maxW"] // max(1.0, charW)))
            pre = lines[-1][:len(lines[-1]) - len(DOTS)].replace("\n", "")
            if len(pre) >= full:
                bad.append("末行前缀 %d 字 ≥ 满行 %d 字（回退未生效）" % (len(pre), full))
            if len(pre) + 1 <= full and wof(pre + "字") + dotsW <= c["maxW"]:
                bad.append("末行前缀还能再放一个字（回退不彻底）")
        if bad:
            ok_all = False
            say(False, tag, "；".join(bad))
        else:
            mid = lines[-1][-8:] if lines else ""
            say(True, tag, "%d 行 ｜ 末行 …%s ｜ 宽 %.0f≤%d" % (
                len(lines), mid, widths[-1] if widths else 0.0, c["maxW"]))
    return ok_all


# ---------------------------------------------------------------- HTML 侧探针（无头 Edge）
def find_edge():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if os.path.exists(p):
            return p
    w = shutil.which("msedge")
    return w or ""


def run_probe(mutate_off=False):
    """跑无头 Edge 探针页，返回 (结果 dict | None, 说明)。"""
    edge = find_edge()
    if not edge:
        return None, "未找到 msedge.exe"
    html = os.path.join(REP, PROBE)
    if not os.path.exists(html):
        return None, "探针页不存在：" + html

    cfg = dict(size=SIZE, bold=False,
               family='"微软雅黑", "Microsoft YaHei", sans-serif',
               cases=[dict(id=c["id"], text=c["text"], maxW=c["maxW"], maxLines=c["maxLines"])
                      for c in CASES])
    b64 = base64.b64encode(json.dumps(cfg, ensure_ascii=False).encode("utf-8")).decode("ascii")
    # 注意：必须用**标准** base64（`+/=`），因为探针页用 `atob` 解码 —— urlsafe 的 `-_` 会让 atob 报错。
    q = "?table=" + urllib.parse.quote(b64, safe="") + ("&noellip=1" if mutate_off else "")
    url = "file:///" + html.replace("\\", "/").replace(" ", "%20") + q

    os.makedirs(SCRATCH, exist_ok=True)
    ud = os.path.join(SCRATCH, "userdata_" + ("off" if mutate_off else "on"))
    dump = os.path.join(SCRATCH, "dom_" + ("off" if mutate_off else "on") + ".html")
    cmd = [edge, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + ud, "--hide-scrollbars",
           "--window-size=1400,900", "--virtual-time-budget=20000", "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    try:
        import io as _io
        _io.open(dump, "w", encoding="utf-8").write(dom)
    except Exception:
        pass
    m = re.search(r"RESULT_JSON_START(\{.*?\})RESULT_JSON_END", dom, re.S)
    if not m:
        e = re.search(r"PROBE_ERROR ([^<]*)", dom)
        return None, "探针无结果（%s）；dump=%s" % (e.group(1) if e else "未找到结果标记", dump)
    # `--dump-dom` 会把文本节点里的 `"` 转义成 `&quot;` ⇒ 先反转义再解析
    raw = m.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return json.loads(raw), dump


# ---------------------------------------------------------------- main
def main():
    selfcheck = "--selfcheck" in sys.argv
    no_html = "--no-html" in sys.argv

    print("=" * 78)
    print("test_text_ellipsis.py · 超框省略号冻结期望表闸门（ISSUE-20260930-02 · 任务 A）")
    print("  判据：_工作/ISSUE-20260930-02_章节详情/接口冻结.md §五")
    print("  期望表：%d 个用例；省略号 = %r（两个 U+2026）" % (len(CASES), DOTS))
    print("=" * 78)

    wof, src = make_wof(SIZE)
    charW, dotsW = wof("字"), wof(DOTS)
    # ★ 第 15 批：本文件与生成器**同源**（折行+省略号都调生成器）⇒ 禁则表必须逐字相同
    #   （不同源时这条会立刻报出来，而不是让「两端行逐字相同」这个结论悄悄失去意义）。
    same_charset = (G.NOHEAD == NOHEAD and G.NOTAIL == NOTAIL)
    print("\n[同源] 生成器 `ui_theme_wrap`/`apply_ellipsis` 与本文件禁则表一致：%s（NOHEAD/NOTAIL）"
          % ("✓" if same_charset else "✗ **禁止**"))
    if not same_charset:
        raise SystemExit("[FAIL] 禁则表与生成器不一致：G.NOHEAD=%r / 本地=%r" % (G.NOHEAD, NOHEAD))
    print("[度量] Python 侧 = %s" % src)
    print("       宽度('字')=%.2f  宽度(%r)=%.2f  （每行预算按 maxW 传入值，不做描边内缩）"
          % (charW, DOTS, dotsW))

    # ---- ① Python 侧折算 ----
    print("\n---- ① Python 侧折算 (%s) ----" % ("变异：关掉省略号" if selfcheck else "正常"))
    py_lines, py_flags = [], []
    for c in CASES:
        ls, tr, dr = wrap_ellipsis(c["text"], c["maxW"], c["maxLines"], wof,
                                   ellipsis_on=not selfcheck)
        py_lines.append(ls)
        py_flags.append(dict(truncated=tr, dropped=dr))
    py_ok = check_impl("PY", py_lines, py_flags, wof, CASES, charW, dotsW)

    # ---- ② HTML 侧（同一份 replica.js，经无头 Edge 探针页）----
    html_res, html_lines, html_flags = None, None, None
    html_ok = True
    if no_html:
        print("\n---- ② HTML 探针（--no-html：**本轮未跑**，结论只覆盖 Python 侧）----")
    else:
        print("\n---- ② HTML 探针（%s） ----" % ("变异：&noellip=1" if selfcheck else "正常"))
        html_res, info = run_probe(mutate_off=selfcheck)
        if html_res is None:
            html_ok = False
            say(False, "HTML/探针", info)
        else:
            got_ids = [x["id"] for x in html_res["cases"]]
            say(got_ids == [c["id"] for c in CASES], "HTML/用例回声",
                "、".join(got_ids))
            say(html_res.get("dots") == DOTS, "HTML/省略号字符串 == 两个 U+2026",
                repr(html_res.get("dots")))
            h_charW = float(html_res.get("charW") or 0)
            h_dotsW = float(html_res.get("dotsW") or 0)
            say(abs(h_charW - charW) <= 3.0 and abs(h_dotsW - dotsW) <= 3.0,
                "两端度量同量级（宽度('字') / 宽度('……')）",
                "HTML %.2f/%.2f ｜ PY %.2f/%.2f ｜ 解析族=%s" % (
                    h_charW, h_dotsW, charW, dotsW, html_res.get("family")))
            html_lines = [x["lines"] for x in html_res["cases"]]
            html_flags = [dict(truncated=x["truncated"], dropped=x["dropped"]) for x in html_res["cases"]]
            html_widths = [x.get("widths") for x in html_res["cases"]]
            h_wof = (lambda s, cw=h_charW, dw=h_dotsW: sum(
                cw if (ord(ch) >= 0x2E80 or ch in "…‥—～·！？：；（）「」『』【】、。") else cw * 0.5
                for ch in s))
            html_ok = check_impl("HTML", html_lines, html_flags, h_wof, CASES,
                                 h_charW, h_dotsW, widths_list=html_widths)
            # 两端行内容逐字相同（最强的一端对一端证据）
            same = [c["id"] for c, a, b in zip(CASES, py_lines, html_lines) if a != b]
            say(not same, "两端返回的行**逐字相同**",
                "全部 %d 例一致" % len(CASES) if not same else ("不一致：" + "、".join(same)))

    # ---- ③ 变异自证：关掉省略号后必须报失败 ----
    if selfcheck:
        print("\n---- ③ 变异自证（--selfcheck） ----")
        say(not py_ok, "Python 侧关掉省略号后**必须失败**（判据非恒真）",
            "PY %s" % ("仍全绿 ⇒ 表恒真、无牙齿" if py_ok else "已报失败 ✓"))
        if html_lines is not None:
            say(not html_ok, "HTML 侧关掉省略号（&noellip=1）后**必须失败**",
                "HTML %s" % ("仍全绿 ⇒ 表恒真、无牙齿" if html_ok else "已报失败 ✓"))
        print("\n（--selfcheck 的**期望**就是「有失败」；下面统计里的 FAIL 即自证成功，"
              "退出码按「变异检出」计。）")
        ok = (not py_ok) and (not no_html and html_lines is not None and not html_ok)
        print("\n自证结论：%s" % ("PASS —— 两端均检出变异（判据非恒真）" if ok else "FAIL —— 变异未被检出"))
        print("=" * 78)
        return 0 if ok else 1

    ok = py_ok and html_ok
    print("\n" + "=" * 78)
    print("汇总：PASS %d ｜ FAIL %d ｜ HTML 探针 %s" % (
        PASS, FAIL, "未跑(--no-html)" if no_html else ("已跑" if html_lines is not None else "不可用")))
    print("结论：%s" % ("ALL PASS" if ok else "FAILED"))
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
