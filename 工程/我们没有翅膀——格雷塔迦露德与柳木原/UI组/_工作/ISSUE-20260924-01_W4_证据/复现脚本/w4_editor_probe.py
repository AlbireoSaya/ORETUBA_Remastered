# -*- coding: utf-8 -*-
r"""W4 · 编辑器（复刻\editor.html）「slider 分组 + 滑块校验」无头探针

■ 为什么要有它
  W4 的编辑器改动（`editor_ui.js` 的 renderProp / renderCheck / pruneSub）在既有自检里
  **零断言**（`_selftest_states.html` 是状态机自检，`index.html?selftest=1` 是复刻页自检）。
  本探针把编辑器真的跑起来、真的选中一根滑块元素，然后逐项读属性面板与校验面板：
    ① slider 分组出现（min/max/step/value/setting 五个输入 + rail/handle 素材下拉）；
    ② 校验：合法数据 ⇒ 无硬错误；
    ③ 变异：`min>=max` ⇒ 硬错误；`value` 越界 ⇒ 警告 + **自动 clamp**；
       `handle` 摘空 ⇒ 硬错误；
    ④ `setting` 不在设置仓定义表 ⇒ 警告（不硬失败）；
    ⑤ 点「（无）」摘掉 handle.state_assets.hover ⇒ 只删该键、不留空壳（pruneSub）。

■ 做法（同 w4_html_config_shots.py）
  把 `复刻\editor.html` 读进来、改写相对路径 + 注入 `?` 钩子，落到本证据目录（跑完删除），
  用无头 Edge `--dump-dom` 取回探针输出。**不改 editor.html 本体**（不在 W4 白名单内）。

■ 用法
    python _工作\ISSUE-20260924-01_W4_证据\复现脚本\w4_editor_probe.py
"""
import io
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_w4"
PAGE = os.path.join(EVID, "_w4_editor_probe.html")

PID = "cfg.sl_winopac"

HOOK = """
<script>
(function () {
  function log(s) { window.__probe = (window.__probe || []); window.__probe.push(s); }
  window.addEventListener('load', function () {
    setTimeout(function () {
      var E = window.UI_EDITOR;
      if (!E) { log('FAIL 编辑器未加载（UI_EDITOR 缺失）'); render(); return; }
      E.loadScreen('config');
      var prop = document.getElementById('ed-prop'), chk = document.getElementById('ed-check');
      function sel(id) { E.ED.sel = [id]; E.refreshProp(); E.refreshCheck(); }
      function fields() {
        var out = [];
        ['min', 'max', 'step', 'value', 'setting', 'rail.asset', 'handle.asset',
         'handle.state_assets.normal', 'handle.state_assets.hover'].forEach(function (p) {
          var n = prop.querySelector('[data-p="' + p + '"]');
          out.push(p + '=' + (n ? (n.tagName === 'SELECT' ? ('<select> ' + n.value) : n.value) : '**缺**'));
        });
        return out.join(' | ');
      }
      function checkTxt() { return (chk.textContent || '').replace(/\\s+/g, ' ').slice(0, 300); }
      function fullTxt() { return (chk.textContent || '').replace(/\\s+/g, ' '); }
      function errs() { var m = /硬错误 (\\d+) 条/.exec(fullTxt()); return m ? m[1] : 0; }
      function warns() { var m = /提示 (\\d+) 条/.exec(fullTxt()); return m ? m[1] : 0; }

      sel('__none__');                       // 先清空选择，确保下面读到的是新渲染的
      sel('<ID>');
      log('① slider 分组出现：' + fields());
      log('① 校验（合法数据）：硬错误块 ' + errs() + ' / 警告块 ' + warns() + ' —— ' + checkTxt());

      var el = E.byId('<ID>');
      var all = E.ED.els.slice();
      /* ⚠️ 校验面板只列**前 16 条**提示，而本屏有 254 条「素材不在索引里」噪声（emit_asset_index.py
         未重跑所致）⇒ 逐条断言必须**把元素表临时缩到被测那一件**，否则断言文本被噪声挤出面板。 */
      function only(id, fn) {
        E.ED.els = [E.byId(id)];
        E.refreshCheck();
        var r = fn();
        E.ED.els = all;
        E.refreshCheck();
        return r;
      }
      var saveMin = el.min, saveMax = el.max, saveVal = el.value;
      var saveHandle = JSON.parse(JSON.stringify(el.handle || {}));

      only('<ID>', function () {
        log('① 单件校验（合法滑块）：硬错误=' + errs() + '、提示=' + warns() + '；文本「' + fullTxt().slice(0, 160) + '」');
      });

      /* ③a min>=max ⇒ 硬错误 */
      el.min = 100; el.max = 0;
      only('<ID>', function () {
        log('③ min>=max ⇒ 硬错误=' + errs() + '（期望 2：值域非法 + value 越界警告）；文本「'
            + fullTxt().slice(0, 220) + '」');
      });
      el.min = saveMin; el.max = saveMax;

      /* ③b value 越界 ⇒ 警告 + 自动 clamp */
      el.value = 999;
      var clamped = 0;
      only('<ID>', function () {
        clamped = el.value;
        log('③ value=999 越界 ⇒ 被 clamp 为 ' + el.value + '（期望 ' + saveMax + '）；提示=' + warns()
            + '；文本含「已自动 clamp」=' + /已自动 clamp/.test(fullTxt()));
      });
      el.value = saveVal;

      /* ③c handle 摘空 ⇒ 硬错误 */
      delete el.handle;
      only('<ID>', function () {
        log('③ handle 摘空 ⇒ 硬错误=' + errs() + '（期望 1）；文本含「缺 handle.asset」='
            + /缺 handle\\.asset/.test(fullTxt()));
      });
      el.handle = JSON.parse(JSON.stringify(saveHandle));

      /* ③d setting 不在定义表 ⇒ 警告（不硬失败） */
      var saveSet = el.setting;
      el.setting = '__not_a_setting__';
      only('<ID>', function () {
        log('③ setting=__not_a_setting__ ⇒ 硬错误=' + errs() + '（期望 0）、提示=' + warns()
            + '；文本含该键=' + /__not_a_setting__/.test(fullTxt())
            + '，含「纯视觉滑块」=' + /纯视觉滑块/.test(fullTxt()));
      });
      el.setting = saveSet;

      /* ③e rail 摘空 ⇒ 硬错误 */
      var saveRail = JSON.parse(JSON.stringify(el.rail || {}));
      delete el.rail;
      only('<ID>', function () {
        log('③ rail 摘空 ⇒ 硬错误=' + errs() + '（期望 1）；文本含「缺 rail.asset」='
            + /缺 rail\\.asset/.test(fullTxt()));
      });
      el.rail = saveRail;

      /* ---- ⑥ ★ M47 第三轮（一审 m1）：`rail.nine` 里**填 0** 不得被当成空值删键 ---- */
      function setField(path, val) {
        var n = prop.querySelector('[data-p="' + path + '"]');
        if (!n) { log('   找不到字段 ' + path); return false; }
        n.value = String(val);
        var ev = document.createEvent('HTMLEvents'); ev.initEvent('input', true, true);
        n.dispatchEvent(ev);
        return true;
      }
      var did = [setField('rail.nine.l', 0), setField('rail.nine.t', 0),
                 setField('rail.nine.r', 4), setField('rail.nine.b', 6)].join(',');
      var el2 = E.byId('<ID>');
      var nine1 = JSON.parse(JSON.stringify((el2.rail && el2.rail.nine) || null));
      log('⑥ rail.nine 依次填 l=0,t=0,r=4,b=6（字段命中 ' + did + '）⇒ 数据 = '
          + JSON.stringify(nine1));
      log('     l/t 两个 0 **必须保留**（改前 `!o[k]` 判空会删掉它们）⇒ l0保留='
          + Boolean(nine1 && nine1.l === 0) + '、t0保留=' + Boolean(nine1 && nine1.t === 0)
          + '、r=' + (nine1 && nine1.r) + '、b=' + (nine1 && nine1.b));
      /* 反向对照：**空串** 仍应删键（空壳清理必须还在） */
      setField('rail.nine.l', '');
      var el3 = E.byId('<ID>');
      var nine2 = JSON.parse(JSON.stringify((el3.rail && el3.rail.nine) || null));
      log('     反向对照：把 l 清成空串 ⇒ 该键被删（仍要能清空）='
          + Boolean(nine2 && nine2.l === undefined) + '（现数据 ' + JSON.stringify(nine2) + '）');
      el3.rail = JSON.parse(JSON.stringify(saveRail));
      el3.handle = JSON.parse(JSON.stringify(saveHandle));
      el3.value = saveVal;
      sel('<ID>');

      /* ⑤ 清空 handle.state_assets.hover ⇒ 只删该键、不留空壳（pruneSub） */
      var box = prop;
      var hovSel = box.querySelector('[data-p="handle.state_assets.hover"]');
      var keysBefore = Object.keys(el.handle.state_assets || {}).join(',');
      if (hovSel) {
        hovSel.value = '';
        var ev = document.createEvent('HTMLEvents'); ev.initEvent('change', true, true);
        hovSel.dispatchEvent(ev);
      }
      log('⑤ 选「（无）」后 handle=' + JSON.stringify(el.handle)
          + '（state_assets 键 前=[' + keysBefore + '] 后=['
          + Object.keys((el.handle || {}).state_assets || {}).join(',') + ']）');
      el.handle = JSON.parse(JSON.stringify(saveHandle));
      sel('<ID>');
      render();
    }, 300);
  });
  function render() {
    var pre = document.createElement('pre');
    pre.id = 'probe-out';
    pre.textContent = 'EDITORPROBE\\n' + (window.__probe || []).join('\\n') + '\\nEDITORPROBE-END';
    document.body.innerHTML = '';
    document.body.appendChild(pre);
  }
})();
</script>
"""


def build_page():
    html = io.open(os.path.join(REP, "editor.html"), encoding="utf-8").read()
    for a, b in (('href="editor.css"', 'href="../../复刻/editor.css"'),
                 ('src="ui_layout.js"', 'src="../../复刻/ui_layout.js"'),
                 ('src="asset_index.js"', 'src="../../复刻/asset_index.js"'),
                 ('src="screen_index.js"', 'src="../../复刻/screen_index.js"'),
                 ('src="replica.js"', 'src="../../复刻/replica.js"'),
                 ('src="editor_core.js"', 'src="../../复刻/editor_core.js"'),
                 ('src="editor_ui.js"', 'src="../../复刻/editor_ui.js"')):
        html = html.replace(a, b)
    html = html.replace('<script src="../../复刻/ui_layout.js"></script>',
                        "<script>window.UI_ASSET_ROOT='../../krkr/assets/';</script>\n"
                        '<script src="../../复刻/ui_layout.js"></script>')
    html = html.replace('</body>', HOOK.replace('<ID>', PID) + '\n</body>')
    io.open(PAGE, "w", encoding="utf-8").write(html)


def main():
    # ---- ★ `--mut`：把 `isEmptyVal` 换回**改前**的 `!v` 口径（0 当空），跑同一条探针，
    #      用来给报告出「改前 vs 改后」对照（改前 `rail.nine` 填 0 会被删键）。
    mut = "--mut" in sys.argv
    src_path = os.path.join(REP, "editor_ui.js")
    src = io.open(src_path, encoding="utf-8").read()
    bak = os.path.join(EVID, "editor_ui_原始备份.js")
    if mut:
        old = "  function isEmptyVal(v) { return v === null || v === undefined || v === ''; }"
        new = "  function isEmptyVal(v) { return !v; }   /* __mut：改前口径（0 当空） */"
        assert old in src, "变异锚点未找到"
        io.open(bak, "w", encoding="utf-8").write(src)
        io.open(src_path, "w", encoding="utf-8").write(src.replace(old, new))
        print("（--mut：isEmptyVal 已换回改前口径 `!v`）\n")
    try:
        return run_once()
    finally:
        if mut:
            io.open(src_path, "w", encoding="utf-8").write(src)      # 逐字节还原
            ok = (io.open(src_path, encoding="utf-8").read() == src)
            os.remove(bak)
            print("\n（已还原 editor_ui.js：逐字节一致=%s，备份已删除）" % ok)


def run_once():
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    build_page()
    url = "file:///" + urllib.parse.quote(PAGE.replace("\\", "/"))
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1600,1000", "--virtual-time-budget=12000", "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    out_html = os.path.join(EVID, "W4_编辑器探针.dom.html")
    io.open(out_html, "w", encoding="utf-8").write(dom)
    m = re.search(r"EDITORPROBE(.*?)EDITORPROBE-END", dom, re.S)
    txt = m.group(1).strip() if m else "(未取到探针输出 —— 编辑器可能未渲染完)"
    txt = (txt.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
              .replace("&amp;", "&"))
    print("原始 dump：" + out_html)
    print(txt)
    os.remove(PAGE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
