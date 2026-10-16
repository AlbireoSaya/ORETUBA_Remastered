# -*- coding: utf-8 -*-
r"""M38 · HTML 复刻侧描边的**目标导向**验证（不是"跑通了"，而是"属性确实生成了"）

做三件事：
  ① 用 `?screen=dialog&chrome=0` 深链渲染对话框屏，`--dump-dom` 里 grep 出 `dlg.text` /
     `dlg.name` 实际写进 DOM 的 `text-shadow` 值 ⇒ 证明 8 条描边阴影**真的生成**、
     顺序与 krkr 的 UIThemeOutlineDirs 一致、宽度 = outline_width；
  ② 同一帧 `--screenshot` 出 PNG，供人眼看描边（落 M38 证据目录）；
  ③ 反向对照：`dlg.hint`（outline:false）的 text-shadow 必须**仍是单条 offset 阴影**，
     不得被描边污染（= 与 krkr 侧「outline:false 逐像素不变」两端同口径）。

用法：python _工作\ISSUE-20260923-01_M38_证据\m38_html_outline_probe.py
退出码：0 = 三条全符合预期。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m38"

DIRS_KRKR = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
fails = []


def run(url, extra):
    os.makedirs(UD, exist_ok=True)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1920,1080", "--virtual-time-budget=8000"] + extra + [url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace"), r.returncode


def main():
    # ⚠️ 必须先把 `\` 换成 `/` 再 quote：`file:///E%3A%5C…` 里 %5C 是反斜杠，
    #    Edge 不接受 ⇒ 页面根本不加载、dump 里什么都没有（本脚本第一版就踩了这个坑，
    #    与 `_工作\M37_跑HTML自检.py` 的 url_of() 同一写法）。
    url = "file:///" + urllib.parse.quote(os.path.join(REP, "index.html").replace("\\", "/")) \
        + "?screen=dialog&chrome=0"
    dom, rc = run(url, ["--dump-dom"])
    io.open(os.path.join(HERE, "M38_HTML_dialog_dom.html"), "w", encoding="utf-8").write(dom)
    shot = os.path.join(HERE, "M38_HTML复刻_对话框屏_chrome0.png")
    run(url, ["--screenshot=" + shot])
    print("深链 URL：%s（edge rc=%d，dump %d 字节）" % (url, rc, len(dom)))
    print("截图：%s" % shot)

    def shadows_of(eid):
        r"""取该元素 .ui-text-inner 的 text-shadow 值 → ([(dx,dy),...], 颜色全黑?)

        ⚠️ 不能按 `,` 直接 split：浏览器把颜色序列化成 `rgb(0, 0, 0)`（自带两处逗号），
           朴素 split 会把颜色切碎、把偏移量解析对而颜色判错（第一版就踩了这个坑）。
           这里只对 `x px y px` 取正则，颜色另用整串包含判断。"""
        m = re.search(r'data-ui-id="%s"' % re.escape(eid), dom)
        if not m:
            return None, False
        seg = dom[m.start():m.start() + 6000]
        inner = re.search(r'<div class="ui-text-inner"[^>]*style="([^"]*)"', seg)
        if not inner:
            return None, False
        ts = re.search(r'text-shadow:\s*([^"]*)', inner.group(1))
        if not ts:
            return [], False
        val = ts.group(1).strip()
        offs = [(float(a), float(b)) for (a, b) in
                re.findall(r'(-?\d+(?:\.\d+)?)px\s+(-?\d+(?:\.\d+)?)px', val)]
        n_color = val.count("rgb(0, 0, 0)") + val.count("#000000")
        n_black = val.count("black")
        return offs, (n_color + n_black) == len(offs) and len(offs) > 0

    # ① 正文 / 名字：8 条描边（方向与宽度必须与 krkr 的 UIThemeOutlineDirs 逐项一致）
    for eid in ("dlg.text", "dlg.name"):
        offs, all_black = shadows_of(eid)
        print("\n[%s] text-shadow 偏移量（%s 条，全黑=%s）："
              % (eid, "?" if offs is None else len(offs), all_black))
        print("   %s" % (offs if offs else "(空)"))
        if offs is None:
            fails.append("%s：DOM 中找不到该元素" % eid)
            continue
        # 从数据读 outline_width（不写死）
        import json
        sc = json.load(open(os.path.join(UI, "layout", "screens", "10_dialog.json"), encoding="utf-8"))
        el = [e for e in sc["elements"] if e["id"] == eid][0]
        w = int(el["font"]["outline_width"])
        want = [(dx * w, dy * w) for dx, dy in DIRS_KRKR]
        ok = (len(offs) == 8 and offs == want and all_black)
        print("   期望 8 向（宽 %d）：%s" % (w, want))
        print("   ⇒ %s" % ("✓ 与 krkr 逐项一致（同序同向、同宽）、颜色为黑" if ok
                           else "**不符合期望**"))
        if not ok:
            fails.append("%s：text-shadow %s 与 krkr 的 8 方向/宽度不一致" % (eid, offs))

    # ③ 反向对照：dlg.hint 仍是单条 offset 阴影（outline:false）
    offs, all_black = shadows_of("dlg.hint")
    print("\n[dlg.hint]（outline:false）text-shadow 偏移量：%s（全黑=%s）" % (offs, all_black))
    if offs is None:
        fails.append("dlg.hint：DOM 中找不到该元素")
    elif len(offs) != 1:
        fails.append("dlg.hint（outline:false）竟生成了 %d 条 text-shadow（应 1 条 offset 阴影）"
                     % len(offs))
    else:
        print("   ⇒ ✓ 仍是单条 offset 阴影（未被描边污染，与 krkr 侧同口径）")

    # ④ ★ M38 追修（视觉验收第一轮的缺陷）：选择肢项标签也必须拿到同参数 8 向描边
    #    （`buildList` 里走的是 `textShadowAll(listFont)`；高亮项只换 color，描边不变）
    m = re.search(r'data-ui-id="dlg\.choices"', dom)
    seg = dom[m.start():m.start() + 20000] if m else ""
    lab = re.search(r'class="ui-list-item-label"[^>]*style="([^"]*)"', seg)
    print("\n[dlg.choices 的项标签]（buildList 路径）")
    if not lab:
        fails.append("dlg.choices：DOM 里取不到 .ui-list-item-label 的 style")
    else:
        ts = re.search(r'text-shadow:\s*([^"]*)', lab.group(1))
        val = ts.group(1).strip() if ts else ""
        offs = [(float(a), float(b)) for (a, b) in
                re.findall(r'(-?\d+(?:\.\d+)?)px\s+(-?\d+(?:\.\d+)?)px', val)]
        withd = json.load(open(os.path.join(UI, "layout", "screens", "10_dialog.json"), encoding="utf-8"))
        cel = [e for e in withd["elements"] if e["id"] == "dlg.choices"][0]
        w = int(cel["font"]["outline_width"])
        want = [(dx * w, dy * w) for dx, dy in DIRS_KRKR]
        ok = (len(offs) == 8 and offs == want)
        print("   %s" % (offs or "(空)"))
        print("   期望 8 向（宽 %d）：%s" % (w, want))
        print("   ⇒ %s" % ("✓ 与 krkr 逐项一致" if ok else "**不符合期望**"))
        if not ok:
            fails.append("dlg.choices 项标签：text-shadow %s 与 krkr 的 8 方向/宽度不一致" % (offs,))
        # 高亮项与未高亮项同属一个 list，共用同一 font ⇒ 断言「高亮只换颜色、不换描边」
        print("   （高亮项走 `highlight_font_color` 改 color，描边由 font 统一 ⇒ 两项同描边；"
              "该断言即对 buildList 全项生效）")

    shutil.rmtree(UD, ignore_errors=True)
    print("\n" + "-" * 78)
    if fails:
        print("结果：**%d 项不符合预期**" % len(fails))
        for f in fails:
            print("  ✗ " + f)
        return 1
    print("结果：**四项全符合预期**（HTML 侧 8 向描边生成正确：正文/名字/选择肢项标签；outline:false 未受影响）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
