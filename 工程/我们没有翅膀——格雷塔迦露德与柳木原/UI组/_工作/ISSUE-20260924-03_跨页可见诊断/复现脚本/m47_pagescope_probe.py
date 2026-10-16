# -*- coding: utf-8 -*-
r"""M47 设置屏「跨页可见」探针 —— 编辑器「按 flag 预览」与产品同口径（**断言 + 退出码**）

■ 触发（用户 2026-09-24 报告）
  用户在编辑器里把 `cfg_page` 切到某一页后，发现另一页的元素仍然显示；并给出一份
  人工核对名单（17 件系统页值元素 + 角色列表 4 类），怀疑这些元素「没打 flag（空）」。

■ 本探针回答三件事（全部以**渲染出的 DOM** 为口径，不靠脚本自行复算）
  ① 编辑器里：切页后到底有多少件残留可见？残留的是不是就是用户点名的那批？
  ② 原因：编辑器「按 flag 预览」的可见性判据是什么？它跑不跑切页派生？
  ③ 对照：在同一个已渲染的页面上，直接调用机制侧的派生入口（`configDerivePageFlags`，
     即引擎 `config_tab_2` 动作内部调用的同一函数）之后，残留是否归零？
     ⇒ 同一页、同一份数据，只差「有没有跑派生」这一个变量。

■ 本轮的验收口径（E1 修完后，本脚本即验收机件：**读数是断言，不是打印**）
  · A1（`cfg_page=sys`）：可见总数 **115**、跨页残留 **0**
  · A2（`cfg_page=snd`）：可见总数 **187**、跨页残留 **0**
  · B / C（机制侧派生，只看 DOM）：残留 **0**，总数 **187 / 115**
  · A1/A2 的 `domSameAsPred` 必须为真（编辑器判据与 DOM 不得分叉）
  · D：手选非页 flag（`cfg_v_display=full`）仍能做单项探查（raw 口径保留）
  任一不符 ⇒ 打印 `RESULT=FAIL` 并 **exit(1)**；全符 ⇒ `RESULT=OK` 并 exit(0)。

■ `--mutate`（变异自证，**不改工作区任何交付文件**）
  在临时页里把机制侧的两个派生入口（`configDerivePageFlags` / `configFlagsInitFor`）
  替换为返回 0 的空实现 —— 等价于「把新增的派生调用整条注释掉」。
  此时读数必须**回到修复前**（A1 119/4、A2 204/17、B 204/17、C 119/4），
  否则本脚本没有判别力。变异模式下的期望值是修复前的读数，故同样以 exit(0) 表示
  「变异被探针逮到」。

■ 做法（同 w4_editor_probe.py）
  把 `复刻\editor.html` 读进来、改写相对路径 + 注入钩子，落到本目录（跑完删除），
  用无头 Edge `--dump-dom` 取回探针输出。**不改 editor.html 本体，不改任何交付文件。**

■ 用法
    python _工作\ISSUE-20260924-03_跨页可见诊断\复现脚本\m47_pagescope_probe.py
    python _工作\ISSUE-20260924-03_跨页可见诊断\复现脚本\m47_pagescope_probe.py --mutate
"""
import io
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))    # …\UI组\_工作\ISSUE-20260924-03_跨页可见诊断\复现脚本
EVID = os.path.dirname(HERE)                          # …\ISSUE-20260924-03_跨页可见诊断（读数落这里，与上一轮基线同目录）
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # …\UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_pagescope"

# ============================ 期望读数（两种模式） ============================
# 修复后：编辑器预览跑与产品同一份切页派生 ⇒ 另一页的值 / 选中元素不再残留
EXPECT_FIXED = {"A1": (115, 0), "A2": (187, 0), "B": (187, 0), "C": (115, 0)}
# 变异（派生被整条打废）⇒ 必须回到修复前的读数，否则探针无判别力
EXPECT_MUTATED = {"A1": (119, 4), "A2": (204, 17), "B": (204, 17), "C": (119, 4)}

HOOK = """
<script>
(function () {
  var out = [];
  /* 把读数同时打印成人读行与机器行（后者由 Python 侧解析并判定 exit code） */
  function log(s) { out.push(s); }
  function check(tag, o) {
    var kv = Object.keys(o).map(function (k) { return k + '=' + o[k]; }).join(' ');
    log('★CHECK★ tag=' + tag + ' ' + kv);
  }
  /* 步骤标签形如「A1 编辑器·…」⇒ 取首段作机器标签 */
  function tagKey(s) { return String(s).split(' ')[0]; }
  function render() {
    var d = document.createElement('pre');
    d.id = 'PAGESCOPE';
    d.textContent = 'PAGESCOPEOUT\\n' + out.join('\\n') + '\\nPAGESCOPEEND';
    document.body.appendChild(d);
  }
  function boot() {
    try { run(); } catch (e) { log('EXCEPTION ' + e.message + ' @' + (e.lineNumber || '?')); }
    render();
  }
  window.addEventListener('load', function () { setTimeout(boot, 1200); });

  /* 用户点名清单（原样抄自 2026-09-24 报告） */
  var SYS_LIST = ['cfg.o_display_on_tx_sel', 'cfg.o_display_on', 'cfg.o_facewindow_on_tx_sel',
    'cfg.o_facewindow_on', 'cfg.o_drama_on_tx_sel', 'cfg.o_drama_on', 'cfg.o_effect_on_tx_sel',
    'cfg.o_effect_on', 'cfg.o_voicecut_on_tx', 'cfg.o_curhide_on_tx', 'cfg.o_savedialog_on_tx_sel',
    'cfg.o_savedialog_on', 'cfg.o_loaddialog_on_tx_sel', 'cfg.o_loaddialog_on', 'cfg.o_allskip_on_tx',
    'cfg.o_textcolchg_on_tx_sel', 'cfg.o_textcolchg_on'];
  var SND_LIST = ['cfg.ch_asu_tx_sel', 'cfg.ch_asu_pill', 'cfg.pv_name_asu',
    'cfg.pv_face_asu',      /* 用户点名的是 `cfg.pv_face_miy`（举「所有人物头像」为例）；*/
    'cfg.pv_face_miy'];     /* 默认选中族是 asu ⇒ 真正该显形的是 `cfg.pv_face_asu`，两件都测 */

  function run() {
    var E = window.UI_EDITOR, R = window.UI_REPLICA;
    if (!E || !R) { log('FAIL 编辑器未加载（UI_EDITOR / UI_REPLICA 缺失）'); return; }
    E.loadScreen('config');
    var els = E.ED.els;

    /* --- 值键 → 所属页：与机制侧同一条规则（只认 hit，且 hit 自带 cfg_page 页 flag）--- */
    var pageOf = {}, seen = {};
    els.forEach(function (e) {
      if (!e || e.kind !== 'hit') return;
      var a = e.action ? String(e.action) : '', flag = '';
      if (a.indexOf('config_set_') === 0) {
        var sk = a.slice('config_set_'.length); var cx = sk.indexOf(':');
        if (cx >= 0) sk = sk.slice(0, cx);
        flag = 'cfg_v_' + sk;
      } else if (a.indexOf('config_char_') === 0) { flag = 'cfg_vchar'; } else return;
      if (flag === 'cfg_v_' || seen[flag]) return;
      if (String(e.vis_flag) !== 'cfg_page') return;
      var w = (e.vis_when === null || e.vis_when === undefined) ? '' : String(e.vis_when);
      if (w === '') return;
      seen[flag] = 1; pageOf[flag] = w;
    });
    log('① 值键→页映射（从本屏数据导出，共 ' + Object.keys(pageOf).length + ' 项）：'
        + Object.keys(pageOf).map(function (k) { return k + '=' + pageOf[k]; }).join(' '));

    /* --- 可见性：DOM 口径（真被画出来）+ 编辑器判据口径（isVisible，命中测试用）--- */
    function domVis(id) {
      var n = document.querySelector('[data-ui-id="' + id + '"]');
      if (!n) return null;
      return window.getComputedStyle(n).display !== 'none';
    }
    function scan(tag, withPred, cur) {
      var cnt = { page: { sys: 0, snd: 0 }, val: 0, valResidual: [], total: 0,
                  domSameAsPred: true };
      els.forEach(function (e) {
        if (!e || !e.id) return;
        var d = domVis(e.id);
        if (d === null) return;                       // 该元素没渲染出节点
        var p = withPred ? E.isVisible(e) : null;
        if (p !== null && p !== d) cnt.domSameAsPred = false;
        var v = withPred ? p : d;                     // 判据口径（步骤 A）；DOM 口径（步骤 B/C）
        if (!v) return;
        cnt.total++;
        var fn = e.vis_flag;
        if (fn === null || fn === undefined || String(fn) === '') return;
        fn = String(fn);
        if (fn === 'cfg_page') { cnt.page[String(e.vis_when)]++; return; }
        if (pageOf[fn]) {
          /* ★ 残留判据 = **该值键所属页 ≠ 当前页**（不是「vis_when ≠ 页名」——
             值元素自己的 vis_when 是取值，永远不等于页名，那样会把本页元素全误判成残留）。 */
          if (pageOf[fn] === cur) cnt.val++;
          else cnt.valResidual.push(fn + ':' + e.id);
        }
      });
      log('   [' + tag + '] 可见总数=' + cnt.total
          + ' | cfg_page 页元素 sys=' + cnt.page.sys + ' snd=' + cnt.page.snd
          + ' | 本页值/选中元素=' + cnt.val
          + ' | **跨页残留=' + cnt.valResidual.length + '**'
          + (cnt.domSameAsPred ? '' : '  ⚠️ 判据与 DOM 不一致'));
      check(tagKey(tag), { total: cnt.total, residual: cnt.valResidual.length,
                   dom: cnt.domSameAsPred ? 1 : 0 });
      return cnt;
    }
    function list2(tag) {
      var a = [], b = [];
      SYS_LIST.concat(SND_LIST).forEach(function (id) {
        if (!domVis(id)) return;
        var fn = E.byId(id).vis_flag;
        (String(fn) === 'cfg_page') ? null : (pageOf[String(fn)] === 'sys' ? a : b).push(id);
      });
      log('   [' + tag + '] 名单里当前可见：系统页值元素 ' + a.length + '/' + SYS_LIST.length
          + ' 件、声音页角色元素 ' + b.length + '/' + SND_LIST.length + ' 件');
      log('      · 可见的系统页值元素：' + (a.join(', ') || '（无）'));
      log('      · 可见的声音页角色元素：' + (b.join(', ') || '（无）'));
    }

    log('② 编辑器「按 flag 预览」开关：' + E.setFlagPreview(true));
    E.setFlagValue('cfg_page', 'sys');  E.reRender();
    var r1 = scan('A1 编辑器·按 flag 预览：cfg_page=sys（DOM＝判据）', true, 'sys');
    E.setFlagValue('cfg_page', 'snd');  E.reRender();
    var r2 = scan('A2 编辑器·按 flag 预览：cfg_page=snd（DOM＝判据）', true, 'snd');
    log('   ⇒ A1（系统页）的跨页残留 ' + r1.valResidual.length + ' 件、A2（声音页）的跨页残留 '
        + r2.valResidual.length + ' 件');
    log('   A1（系统页）残留：' + r1.valResidual.join(' , '));
    log('   A2（声音页）残留：' + r2.valResidual.join(' , '));
    list2('A2 声音页');
    E.setFlagValue('cfg_page', 'sys');  E.reRender();
    list2('A1 系统页');

    /* --- D：非页 flag 仍是 raw 口径（手选单项探查必须留得住） --- */
    E.setFlagValue('cfg_v_display', 'full');  E.reRender();
    var rawKept = (String(R.getFlag('cfg_v_display')) === 'full');
    var fullVis = domVis('cfg.o_display_on_tx');      // vis_when="full"
    var winVis  = domVis('cfg.o_display_on');         // vis_when="window"
    var predFull = E.isVisible(E.byId('cfg.o_display_on_tx'));
    var predWin  = E.isVisible(E.byId('cfg.o_display_on'));
    log('   [D 手选非页 flag：cfg_v_display=full（raw 口径）] replica 值=' + R.getFlag('cfg_v_display')
        + ' | full 件可见=' + fullVis + ' / window 件可见=' + winVis
        + ' | 判据 full=' + predFull + ' window=' + predWin);
    check('D', { rawprobe: rawKept ? 1 : 0,
                 hit: (fullVis === true && winVis === false && predFull === true && predWin === false) ? 1 : 0,
                 dom: (predFull === fullVis && predWin === winVis) ? 1 : 0 });
    E.setFlagValue('cfg_v_display', 'window');  E.reRender();   // 复原

    /* --- E：**非设置屏零副作用**（屏内无值键 ⇒ 派生返回 0，且可见集不因本轮改动而变） --- */
    function snapVis() {
      var nodes = document.querySelectorAll('#canvas [data-ui-id]'), a = [];
      for (var i = 0; i < nodes.length; i++) {
        a.push(nodes[i].getAttribute('data-ui-id') + ':'
             + (window.getComputedStyle(nodes[i]).display !== 'none' ? 1 : 0));
      }
      return a.sort().join('|');
    }
    E.setFlagPreview(true);
    var others = ['title', 'dialog', 'quickbar', 'dress', 'sysicons'], eFails = 0, eInfo = [];
    others.forEach(function (sid) {
      E.loadScreen(sid);
      var before = snapVis();
      var dnum = R.configFlagsInitFor(sid);            // 非设置屏必须返回 0（机制侧零影响）
      E.reRender();
      var same = (before === snapVis());
      if (dnum !== 0 || !same) eFails++;
      eInfo.push(sid + '（派生返回=' + dnum + '，重渲染后可见集不变=' + same + '）');
    });
    log('   [E 非设置屏零副作用] ' + eInfo.join('；'));
    check('E', { screens: others.length, fails: eFails });

    /* --- 对照：直接调机制侧派生入口（config_tab_2 动作内部调的就是它） --- */
    E.loadScreen('config'); E.setFlagPreview(true);
    R.setFlag('cfg_page', 'snd');
    var n = R.configDerivePageFlags('snd');
    R.applyFlagVisibility();
    log('③ 机制侧派生（按当前页= snd 派生，返回值=' + n + ' 项发生变化）之后：');
    var r3 = scan('B 机制侧派生后：cfg_page=snd（只看 DOM）', false, 'snd');
    log('   ⇒ 跨页残留 ' + r3.valResidual.length + ' 件');
    /* 反方向对照：系统页也要归零（用户报的是「两页均可见」，两个方向都得证） */
    R.setFlag('cfg_page', 'sys');
    var n2 = R.configDerivePageFlags('sys');
    R.applyFlagVisibility();
    log('③b 机制侧派生（按当前页= sys 派生，返回值=' + n2 + ' 项发生变化）之后：');
    var r4 = scan('C 机制侧派生后：cfg_page=sys（只看 DOM）', false, 'sys');
    log('   ⇒ 跨页残留 ' + r4.valResidual.length + ' 件');

    log('④ 判据出处：editor_core.js 的「按 flag 预览」= 写 flag 表 → 按当前 cfg_page 跑机制侧派生'
        + '（页变更走 configDerivePageFlags＝config_tab_* 的同一出口；换屏/开预览/重载走'
        + ' configFlagsInitFor＝进屏语义、captureMemo=false）→ 回读 R.getFlag 进 ED.flagVals'
        + ' → applyFlagVisibility()；isVisible() 仍读 ED.flagVals，故判据与 DOM 同源。');
  }
})();
</script>
"""

# 变异注入：把机制侧两个派生入口换成为返回 0 的空实现
# （等价于「把编辑器里新增的派生调用整条注释掉」；不改工作区任何文件）
MUTATE = """
<script>
window.__MUTATE_NO_DERIVE__ = 1;
(function () {
  function z() { return 0; }
  var R = window.UI_REPLICA;
  if (!R) return;
  R.configDerivePageFlags = z;
  R.configFlagsInitFor = z;
})();
</script>
"""


def build_page(mutate):
    html = io.open(os.path.join(REP, "editor.html"), encoding="utf-8").read()
    # 相对前缀：临时页落在 `_工作\ISSUE-20260924-03_跨页可见诊断\复现脚本\` ⇒ 退三层才回到 `UI组\`
    P = "../../../"
    for a, b in (('href="editor.css"', 'href="' + P + '复刻/editor.css"'),
                 ('src="ui_layout.js"', 'src="' + P + '复刻/ui_layout.js"'),
                 ('src="asset_index.js"', 'src="' + P + '复刻/asset_index.js"'),
                 ('src="screen_index.js"', 'src="' + P + '复刻/screen_index.js"'),
                 ('src="replica.js"', 'src="' + P + '复刻/replica.js"'),
                 ('src="editor_core.js"', 'src="' + P + '复刻/editor_core.js"'),
                 ('src="editor_ui.js"', 'src="' + P + '复刻/editor_ui.js"')):
        html = html.replace(a, b)
    html = html.replace('<script src="' + P + '复刻/ui_layout.js"></script>',
                        "<script>window.UI_ASSET_ROOT='" + P + "krkr/assets/';</script>\n"
                        '<script src="' + P + '复刻/ui_layout.js"></script>')
    if mutate:
        # 必须紧跟 replica.js（它末尾才挂 window.UI_REPLICA）且早于 editor_core.js
        html = html.replace('<script src="' + P + '复刻/editor_core.js"></script>',
                            MUTATE + '<script src="' + P + '复刻/editor_core.js"></script>')
    html = html.replace('</body>', HOOK + '\n</body>')
    page = os.path.join(HERE, "_pagescope_probe_mut.tmp.html" if mutate else "_pagescope_probe.tmp.html")
    io.open(page, "w", encoding="utf-8").write(html)
    return page


def main():
    mutate = '--mutate' in sys.argv[1:]
    expect = EXPECT_MUTATED if mutate else EXPECT_FIXED
    suffix = "_变异" if mutate else ""
    os.makedirs(UD, exist_ok=True)
    page = build_page(mutate)
    url = "file:///" + urllib.parse.quote(page.replace("\\", "/"))
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1600,1000", "--virtual-time-budget=15000", "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    dump = os.path.join(EVID, "诊断_编辑器探针" + suffix + ".dom.html")
    io.open(dump, "w", encoding="utf-8").write(dom)
    m = re.search(r"<pre id=\"PAGESCOPE\">(.*?)</pre>", dom, re.S)
    txt = m.group(1).strip() if m else "(未取到探针输出 —— 编辑器可能未渲染完)"
    for a, b in (("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")):
        txt = txt.replace(a, b)
    print("原始 dump：" + dump)

    # ---------------- 判定：读数是断言 ----------------
    got = {}
    for tag, tot, res, dv in re.findall(r"★CHECK★ tag=(\w+) total=(\d+) residual=(\d+) dom=(\d)", txt):
        got[tag] = (int(tot), int(res), int(dv))
    gotD = {}
    for tag, rp, hit, dv in re.findall(r"★CHECK★ tag=(\w+) rawprobe=(\d+) hit=(\d+) dom=(\d)", txt):
        gotD[tag] = (int(rp), int(hit), int(dv))
    gotE = {}
    for tag, n, f in re.findall(r"★CHECK★ tag=(\w+) screens=(\d+) fails=(\d+)", txt):
        gotE[tag] = (int(n), int(f))

    fails = []
    for tag in ("A1", "A2", "B", "C"):
        want = expect[tag]
        have = got.get(tag)
        if have is None:
            fails.append(tag + "：未取到读数")
            continue
        if (have[0], have[1]) != want:
            fails.append("%s：期望 total=%d residual=%d，实测 total=%d residual=%d"
                         % (tag, want[0], want[1], have[0], have[1]))
        if have[2] != 1:
            fails.append(tag + "：⚠️ 判据与 DOM 不一致（domSameAsPred 必须为真）")
    d = gotD.get("D")
    if d is None:
        fails.append("D：未取到读数")
    elif d != (1, 1, 1):
        fails.append("D：期望 rawprobe=1 hit=1 dom=1，实测 %s" % (d,))
    e = gotE.get("E")
    if e is None:
        fails.append("E：未取到读数")
    elif e[1] != 0:
        fails.append("E：非设置屏零副作用未成立（fails=%d，应为 0）" % e[1])

    txt += "\n■ 判定（%s模式｜期望 %s）\n" % ("变异" if mutate else "正常", expect)
    txt += "   " + ("\n   ".join(fails) if fails else "全部断言通过")
    txt += "\nRESULT=" + ("FAIL" if fails else "OK")
    txt = ("MODE=" + ("MUTATE" if mutate else "NORMAL")
           + "  ⚠️ 变异模式的 exit 0 含义是「变异被逮到」，不是「一切正常」\n" + txt)
    with io.open(os.path.join(EVID, "诊断_编辑器探针" + suffix + ".txt"), "w", encoding="utf-8") as f:
        f.write(txt)

    print(txt)
    os.remove(page)
    print("★ 退出码：", 1 if fails else 0)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
