# -*- coding: utf-8 -*-
r"""M06 · 编辑器「list 派生高度」缺陷修复的无头探针（冻结书 §5 第 2 条）

■ 为什么要有它
  冻结书 §5 登记的缺陷：`kind:"list"` 且**无 `h`** 的元素在编辑器里**可选矩形高度为 0** ⇒ 点不中。
  修法 = 编辑器按 `uiWidgetListSpan` 同一公式派生高度（`工具\test_state_targets.py::rect_of()`
  已有同口径实现），属性面板把 `h` 显示为「（派生，只读）」。
  这条修复在既有自检里**零断言**（`_selftest_states.html` 是状态机、`index.html?selftest=1`
  是复刻页），故本探针把编辑器真的跑起来、**在画布上真的点一下**，逐项读结果。

■ 断言（跑两遍：改后 / `--mut` 变异回改前口径）
  ① 数据自证：`bl.list` 有 labels 4 条 / item_h 205 / max_rows 4 / **无 `h` 键**；
     `UI_EDITOR.derivedH` = true、`elemH` = 820；
  ② 实算高度：`elemH` == `max_rows × item_h + (max_rows−1) × gap`（逐项复算，不写死 820）；
  ③ 选中框：选 `bl.list` 后叠加层里 `.box.sel` 的 height == 派生高（改前为 0px）；
  ④ 属性面板：`h` 输入框 **disabled**、值为派生高、文案含「派生，只读」与公式；
  ⑤ **画布点中**（真·指针事件）：在**块 3 内部**与**块 4 内部**各派发一次 `pointerdown`
     ⇒ `ED.sel` 必须含 `bl.list`；同一探针在 `--mut`（`elemH` 回改前口径 ⇒ 0）下必须**点不中**
     —— 这就是「改前 vs 改后」的对照；
  ⑥ 竖向 resize 守卫：`derivedH` 为真时不进入竖向拉伸（无 `data-hd` 手柄按下后的 dragging 状态），
     且给出可读提示。

■ 做法（同 `w4_editor_probe.py`）
  把 `复刻\editor.html` 读进来、改写相对路径 + 注入钩子，落到本 issue 证据目录（跑完删除），
  用无头 Edge `--dump-dom` 取回探针输出。**不改 editor.html 本体**。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_editor_probe.py
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_editor_probe.py --mut
"""
import hashlib
import io
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
EVID = os.path.join(ISSUE, "证据")
UI = os.path.dirname(os.path.dirname(ISSUE))          # …\UI组  （_工作\ISSUE… → _工作 → UI组）
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_m06"
PAGE = os.path.join(EVID, "_m06_editor_probe.html")

SID = "backlog"
LID = "bl.list"

HOOK = r"""
<script>
(function () {
  function log(s) { window.__probe = (window.__probe || []); window.__probe.push(s); }
  window.addEventListener('load', function () {
    setTimeout(function () {
      try { run(); } catch (e) { log('EXCEPTION ' + e.message); }
      render();
    }, 400);
  });
  function render() {
    var pre = document.createElement('pre');
    pre.id = 'probe-out';
    pre.textContent = 'EDITORPROBE\n' + (window.__probe || []).join('\n') + '\nEDITORPROBE-END';
    document.body.innerHTML = '';
    document.body.appendChild(pre);
  }
  function run() {
    var E = window.UI_EDITOR;
    if (!E) { log('FAIL 编辑器未加载（UI_EDITOR 缺失）'); return; }
    var MUT = __MUT__;
    E.loadScreen('__SID__');
    var el = E.byId('__LID__');
    if (!el) { log('FAIL 数据里没有元素 __LID__'); return; }

    /* ① 数据自证 */
    var nLab = (el.labels || []).length;
    log('① 数据：labels=' + nLab + ' item_h=' + el.item_h + ' gap=' + (el.gap == null ? 0 : el.gap)
        + ' max_rows=' + el.max_rows + ' 有h键=' + (el.h !== undefined && el.h !== null)
        + ' kind=' + el.kind);
    log('① derivedH=' + E.derivedH(el) + '（期望 true） elemH=' + E.elemH(el)
        + ' listSpanH=' + E.listSpanH(el));

    /* ② 逐项复算（不写死 820） */
    var rows = Math.max(1, Math.min(nLab, Number(el.max_rows) || nLab || 1));
    var want = rows * Number(el.item_h) + (rows - 1) * Number(el.gap || 0);
    log('② 逐项复算：行数 ' + rows + ' × item_h ' + el.item_h + ' + (' + rows + '−1) × gap '
        + Number(el.gap || 0) + ' = ' + want + '；elemH 与之一致=' + (E.elemH(el) === want));

    /* ③ 选中框高度 */
    E.ED.sel = ['__LID__'];
    E.drawOverlay(); E.refreshProp();
    var boxSel = document.querySelector('#ed-overlay .box.sel');
    var boxH = boxSel ? boxSel.style.height : '(无选中框)';
    log('③ 选中框 height=' + boxH + '（期望 ' + want + 'px；改前口径会是 0px）');

    /* ④ 属性面板：h 只读 + 派生说明 */
    var prop = document.getElementById('ed-prop');
    var hInp = null, all = prop.querySelectorAll('input');
    for (var i = 0; i < all.length; i++) if (all[i].disabled && /^\d+$/.test(all[i].value)) hInp = all[i];
    var propTxt = (prop.textContent || '').replace(/\s+/g, ' ');
    log('④ 属性面板：h 输入框 disabled=' + (hInp ? 'true' : 'false')
        + ' 值=' + (hInp ? hInp.value : '(无)')
        + ' 文案含「派生，只读」=' + /派生，只读/.test(propTxt)
        + ' 文案含公式=' + (/uiWidgetListSpan/.test(propTxt) && /rect_of/.test(propTxt)));

    /* ⑤ 画布点中（真·指针事件；坐标由 canvas 的 clientRect 反算，兼容编辑器缩放） */
    var canvas = document.getElementById('canvas');
    var cr = canvas.getBoundingClientRect();
    function clientOf(cx, cy) {
      return { x: cr.left + cx * (cr.width / E.CW), y: cr.top + cy * (cr.height / E.CH) };
    }
    var overlayEl = document.getElementById('ed-overlay');
    /* ⚠️ 合成 PointerEvent 的 `pointerId` 不是「活动指针」，而 onDown 第一件事就是
       `overlay.setPointerCapture(ev.pointerId)` —— 真实浏览器下会抛 InvalidPointerId，
       把 onDown **打断在守卫之前**（首轮实测：状态行出现「❌ Script error. @:0」，
       于是⑥读到的是「没进拖动」而不是「守卫拒绝」，**证据无效**）。
       那是合成事件的固有伪影、不是被测代码的问题 ⇒ 这里把它打桩掉（只去掉这一处伪影，
       其余路径一字不动；打桩前后 ⑤ 的判定结果相同）。 */
    var realSPC = overlayEl.setPointerCapture;
    overlayEl.setPointerCapture = function () { };
    function clickAt(cx, cy) {
      E.ED.sel = [];
      var p = clientOf(cx, cy);
      var ev = new PointerEvent('pointerdown', { bubbles: true, cancelable: true,
        clientX: p.x, clientY: p.y, button: 0, buttons: 1, pointerId: 1 });
      overlayEl.dispatchEvent(ev);
      window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1 }));
      return E.ED.sel.slice();
    }
    var hit3 = clickAt(700, 560);      // 块 3（y518..722）内部
    var hit4 = clickAt(700, 800);      // 块 4（y723..927）内部
    var hitOut = clickAt(120, 560);    // 块**左外侧**（x < 208）：不应命中 bl.list
    log('⑤ 画布点中：块3内(700,560)→' + JSON.stringify(hit3)
        + '；块4内(700,800)→' + JSON.stringify(hit4)
        + '；块左外(120,560)→' + JSON.stringify(hitOut));
    var okHit = hit3.indexOf('__LID__') >= 0 && hit4.indexOf('__LID__') >= 0
      && hitOut.indexOf('__LID__') < 0;
    log('⑤ 判定：' + (okHit ? 'PASS' : 'FAIL')
        + (MUT ? '（★ 本行为 --mut 变异：改前口径 elemH=0 ⇒ 上面必然点不中，这就是对照）'
               : '（改后口径：块内任意点可选中该 list）'));

    /* ⑥ 竖向 resize 守卫：派生高度的 list **不得**进入竖向拖动，且必须给出可读提示 */
    E.ED.sel = ['__LID__'];
    E.drawOverlay(); E.refreshProp();
    var hd = document.querySelector('#ed-overlay .hd.n');
    if (hd) {
      var sm0 = document.getElementById('ed-status');
      if (sm0) sm0.textContent = '';
      var p2 = clientOf(Number(el.x) + Number(el.w) / 2, Number(el.y));
      hd.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true,
        clientX: p2.x, clientY: p2.y, button: 0, buttons: 1, pointerId: 2 }));
      var stTxt = (sm0 && sm0.textContent) || '';
      var okGuard = (E.ED.dragging === null) && /不能竖向拉伸/.test(stTxt);
      log('⑥ 竖向手柄 pointerdown：dragging='
          + ((E.ED.dragging === null) ? '(未进入拖动)' : ('(**进入了拖动** mode=' + E.ED.dragging.mode + ')'))
          + ' 状态行「' + stTxt + '」'
          + ' 判定=' + (okGuard ? 'PASS（派生高度被守卫拦下 + 提示可读）'
                               : 'FAIL（期望 dragged=null 且提示含「不能竖向拉伸」）'));
      /* 反向对照：横向手柄（e）**必须**仍能进入拖动（守卫只针对竖向） */
      E.ED.dragging = null;
      var hde = document.querySelector('#ed-overlay .hd.e');
      if (sm0) sm0.textContent = '';
      if (hde) {
        hde.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true,
          clientX: p2.x, clientY: p2.y, button: 0, buttons: 1, pointerId: 3 }));
        log('⑥ 反向对照·横向手柄 pointerdown：dragging='
            + ((E.ED.dragging === null) ? '(未进入拖动) **预期外**'
                                        : ('进入了拖动 mode=' + E.ED.dragging.mode + '（预期）')));
        E.ED.dragging = null;
      }
    } else {
      log('⑥ 未找到竖向手柄（.hd.n）—— 见 ③ 的选中框是否画出来了');
    }
    overlayEl.setPointerCapture = realSPC;
    log('MUT=' + (MUT ? 'true（改前口径 elemH）' : 'false（改后口径）'));
  }
})();
</script>
"""


def build_page(mut):
    html = io.open(os.path.join(REP, "editor.html"), encoding="utf-8").read()
    for a, b in (('href="replica.css"', 'href="../../../复刻/replica.css"'),
                 ('href="editor.css"', 'href="../../../复刻/editor.css"'),
                 ('src="ui_layout.js"', 'src="../../../复刻/ui_layout.js"'),
                 ('src="asset_index.js"', 'src="../../../复刻/asset_index.js"'),
                 ('src="screen_index.js"', 'src="../../../复刻/screen_index.js"'),
                 ('src="replica.js"', 'src="../../../复刻/replica.js"'),
                 ('src="editor_core.js"', 'src="../../../复刻/editor_core.js"'),
                 ('src="editor_ui.js"', 'src="../../../复刻/editor_ui.js"')):
        html = html.replace(a, b)
    html = html.replace('<script src="../../../复刻/ui_layout.js"></script>',
                        "<script>window.UI_ASSET_ROOT='../../../krkr/assets/';</script>\n"
                        '<script src="../../../复刻/ui_layout.js"></script>')
    hook = HOOK.replace('__SID__', SID).replace('__LID__', LID).replace(
        '__MUT__', 'true' if mut else 'false')
    html = html.replace('</body>', hook + '\n</body>')
    os.makedirs(EVID, exist_ok=True)
    io.open(PAGE, "w", encoding="utf-8").write(html)


# ---- 变异锚点：把 elemH 换回**改前**口径（一律读 e.h ⇒ list 得 0） ----
MUT_OLD = "  function elemH(e) { return derivedH(e) ? listSpanH(e) : num(e.h); }"
MUT_NEW = "  function elemH(e) { return num(e.h); }   /* __mut：改前口径 */"


def run_once(mut):
    os.makedirs(UD, exist_ok=True)
    build_page(mut)
    url = "file:///" + urllib.parse.quote(PAGE.replace("\\", "/"))
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1600,1000", "--virtual-time-budget=20000", "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    dump = os.path.join(EVID, "_m06_editor_probe_dump.html")
    io.open(dump, "w", encoding="utf-8").write(dom)
    # ⚠️ 不锚定换行符：无头 Edge 的 `--dump-dom` 序列化里换行可能是 \n / \r\n 混排，
    #    故只按哨兵串取区间，再自行归一化（首轮实测锚 `\n` 会取不到）。
    m = re.search(r"EDITORPROBE(.*?)EDITORPROBE-END", dom, re.S)
    if not m:
        print("（未取到探针输出，edge rc=%d；原始 dump 已存 %s）" % (r.returncode, dump))
        print("  含 probe-out 节点=%s ｜ dump 末 1200 字：" % ("probe-out" in dom))
        print(dom[-1200:])
        err = r.stderr.decode("utf-8", "replace")
        if err.strip():
            print("  ---- edge stderr ----")
            print(err[:1200])
        return 1, []
    lines = m.group(1).replace("\r", "").split("\n")
    lines = [x for x in lines if x.strip() != ""]
    print("=" * 84)
    print("M06 编辑器「list 派生高度」无头探针  【%s】"
          % ("--mut 变异：改前口径" if mut else "改后口径（当前工作区）"))
    print("=" * 84)
    for l in lines:
        print("  " + l)
    print()
    txt = "\n".join(lines)
    # 改后口径必须同时满足：① derivedH ② elemH == 逐项复算 ③ 选中框 = 派生高
    #                       ④ h 只读 + 文案 ⑤ 块内点中 PASS ⑥ 竖向被拦（提示可读）+ 横向仍可拖
    NEED = ["derivedH=true", "elemH 与之一致=true", "选中框 height=820px",
            "h 输入框 disabled=true 值=820", "文案含「派生，只读」=true",
            "⑤ 判定：PASS", "判定=PASS（派生高度被守卫拦下 + 提示可读）",
            "进入了拖动 mode=resize（预期）"]
    if mut:
        # 变异对照：改前口径 elemH 恒 0 ⇒ 块内**点不中**（这就是缺陷本体）
        ok = ("⑤ 判定：FAIL" in txt)
        print("  ★ 变异对照期望：⑤ 判定 FAIL（改前口径 elemH=0 ⇒ 块内点不中）⇒ %s"
              % ("符合预期 ✓" if ok else "**不符合预期**"))
    else:
        miss = [x for x in NEED if x not in txt]
        ok = (len(miss) == 0)
        print("  ★ 改后期望：①–⑥ 全绿 ⇒ %s" % ("通过 ✓" if ok else ("**未通过** 缺：" + " / ".join(miss))))
    return (0 if ok else 1), lines


def main():
    mut = "--mut" in sys.argv
    src_path = os.path.join(REP, "editor_core.js")
    # ★ M06 一审 Minor 修（2026-09-24）：原来**文本模式**读写被跟踪文件 —— 读时 CRLF 折成 LF、
    #   写时按 `newline=""` 落 LF ⇒ 变异窗口里把 editor_core.js 的行尾改写了；而「逐字节一致」
    #   又是拿**文本**比文本（恒真），等于没验。现改为**按字节**读写 + md5 比对，行尾原样不动。
    src = open(src_path, "rb").read()
    orig_md5 = hashlib.md5(src).hexdigest()
    bak = os.path.join(EVID, "editor_core_原始备份.js")
    if mut:
        old_b, new_b = MUT_OLD.encode("utf-8"), MUT_NEW.encode("utf-8")
        assert old_b in src, "变异锚点未找到（elemH 的改后写法）：" + MUT_OLD
        open(bak, "wb").write(src)
        open(src_path, "wb").write(src.replace(old_b, new_b))
        print("（--mut：elemH 已换回改前口径 `num(e.h)`）\n")
    try:
        rc, _ = run_once(mut)
        return rc
    finally:
        if mut:
            open(src_path, "wb").write(src)
            same = (hashlib.md5(open(src_path, "rb").read()).hexdigest() == orig_md5)
            if os.path.exists(bak):
                os.remove(bak)
            print("\n（已还原 editor_core.js：逐字节一致=%s，备份已删除）" % same)
        if os.path.exists(PAGE):
            os.remove(PAGE)


if __name__ == "__main__":
    sys.exit(main())
