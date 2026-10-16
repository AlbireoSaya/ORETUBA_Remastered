# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · M1 鉴赏模式机制 —— **HTML 复刻端**：四承载屏 attach 复用 + 栏位内差分 + 两端一致截图

■ 为什么自建临时页
  `复刻\index.html` 是交付文件、不含测试数据；而机制验收需要「页屏挂 gal_shell + 一个带
  `item_variants` 的网格页」。本脚本把 index.html 读进来、改写相对路径 + 注入一段
  **只在临时页里生效**的钩子（造测试屏 `__gal_grid`、给四承载屏补 `attach:'gal_shell'`、
  隐藏页面外壳 + `setScale(1)`），落到本目录（跑完删除）。**不写任何交付文件**。

■ 本脚本回答三件事
  ① **attach 能否被四个不同承载屏复用**（HTML 侧）：逐屏断言 `attachScreen()=='gal_shell'`、
     外壳元素在 DOM 里、外壳热区**真实点击**派发自身 action、`gal_tab` 派生成本屏 id；
  ② **栏位内差分**（HTML 侧）：渲染数量 / n-N 文本 / 点 next 换图 + 派发 / 边界 clamp /
     守卫负向（容器级 + 逐栏非法逐条 REJECT）；
  ③ **两端一致**：同一份测试页在 HTML 与引擎各出一张 1:1 截图，对**网格首栏区**与
     **外壳页签条区**做逐像素量化（平均绝对差 + 非背景占比），如实登记数字。

■ 用法
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m08_html_shots.py
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m08_html_shots.py --engine-png <引擎导图目录>
"""
import io
import os
import re
import subprocess
import sys
import urllib.parse

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)                      # …\ISSUE-20260924-08_鉴赏模式
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # …\UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_m08"
PAGE = os.path.join(EVID, "_m08_temp_page.html")   # 临时页（跑完删）
SHOTS = os.path.join(EVID, "HTML截图")

STRIP_REGION = (23, 26, 951, 86)          # 外壳页签条（39_gal_shell.json 的 gs.strip 外扩 4px）
GRID_REGION = (57, 187, 1863, 884)        # CG 页网格内容区（6×4 栏的整块）
CELL0_REGION = (57, 187, 348, 353)        # 网格首栏（57,187 291×166 外扩 4px）
# ★ M1 机制自身的 chrome 带：首栏底部（块内局部 y 132..158 = 左右差分按钮 + `n/N` 文本）。
#   为什么单列一条：首栏整区还含 `gal.bg`（九宫格拉伸的整幅底）——**九宫格两端实现本就不同**
#   （krkr `uiWidgetNine` 中格拉伸 vs HTML `border-image`），会把机制自身的差异淹掉。
BTN_BAND_REGION = (57, 315, 348, 353)     # 首栏底部带（y 315..353）
HOSTS = ("gallery", "music", "dress", "replay")

# 引擎侧导图目录（用于两端一致量化；默认找最近一次 --rundir 私有目录）
DEF_ENGINE_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(UI))), "临时", n, "runtime", "savedata")
    for n in ("ui_run_m08_m1inject", "ui_run_m08_m1real", "ui_run_m08")
]

HOOK = r"""
<script>
/* ★ M1 证据专用钩子（**不进任何交付文件**）：
   ① 在内存里造测试屏 `__gal_grid`（6×4 网格 / 30 栏 / 每栏 3 张差分，资产复用既有件）；
   ② 给四个承载屏补 `attach:'gal_shell'`（M4 的 dress/replay 可能还没落盘）；
   ③ 页面外壳隐藏 + setScale(1) ⇒ 截图左上 1920×1080 就是画布本体；
   ④ 跑断言，把结果写进一个 id=M08OUT 的 pre（供 --dump-dom 采集与 Python 侧判定）。
   ⚠️ 本注释**刻意不写尖括号形式的标签**：--dump-dom 会把 <script> 的正文原样序列化，
   注释里的标签字面量会被 Python 侧的正则误当成真元素（实测踩过）。 */
(function () {
  var st = document.createElement('style');
  st.textContent = '.shell{max-width:none!important;padding:0!important;margin:0!important}'
    + '.shell-head,.shell-foot{display:none!important}'
    + '#stage-wrap{justify-content:flex-start!important;display:block!important}'
    + '#stage{box-shadow:none!important}';
  document.head.appendChild(st);

  var ID = '__gal_grid';
  var COEX = '__gal_coexist';   /* 三者共存的测试屏 */
  var N_ROWS = 30, N_DIFF = 3, COLS = 6, ROWS = 4, IW = 291, IH = 166, GAP = 12;
  var A = ['ui/x_ui_cfg_tab_on.png', 'ui/x_ui_cfg_name_sel.png', 'ui/x_ui_menuicon_gallery.png'];
  var BTN_OFF = 'ui/x_ui_cfg_tab_off.png', BTN_ON = 'ui/x_ui_cfg_tab_on.png';   /* 与引擎侧同 */
  function buildTestScreen() {
    var frames = [];
    for (var r = 0; r < N_ROWS; r++) {
      var row = [];
      for (var k = 0; k < N_DIFF; k++) row.push(A[(r + k) % A.length]);
      frames.push(row);
    }
    frames[5] = [];
    var labels = [], actions = [];
    for (var i = 0; i < N_ROWS; i++) { labels.push('测试栏 ' + (i + 1)); actions.push(''); }
    return { id: ID, title_cn: '㉑ 鉴赏机制测试屏', owner: 'M1', attach: 'gal_shell', elements: [{
      id: ID + '.bg', kind: 'image', z: 0, visible_default: true,
      asset: 'ui/x_ui_cfg_frame.png', x: 0, y: 0, w: 1920, h: 1080, opacity: 60,
      nine: { l: 20, t: 20, r: 20, b: 20 }
    }, {
      id: ID + '.list', kind: 'list', z: 30, visible_default: true,
      orientation: 'h', x: 57, y: 187,
      w: COLS * IW + (COLS - 1) * GAP, h: ROWS * IH + (ROWS - 1) * 11,
      item_w: IW, item_h: IH, gap: GAP, max_cols: COLS, max_rows: ROWS,
      labels: labels, actions: actions,
      font: { size: 20, color: '@palette.text_menu' }, align: 'center',
      scroll: { mode: 'page', page_size: COLS * ROWS },
      /* ★ 与引擎侧测试页（m08_gallery_tour.make_test_screen）**逐字对齐**：两端截图要能
         逐像素比，数据就必须同一份。**刻意不放 `item_frame`**（九宫格件两端实现不同，
         会把机制差异淹掉）；共存另立断言 coexistence.*。 */
      item_variants: {
        frames: frames,
        thumb: { x: 8, y: 8, w: IW - 16, h: IH - 46 },
        prev: { key: 'vprev', x: 8, y: IH - 34, w: 48, h: 26, asset: BTN_OFF,
                state_assets: { normal: BTN_OFF, hover: BTN_ON, pressed: BTN_ON },
                action: 'gallery_prev:%row%' },
        next: { key: 'vnext', x: IW - 56, y: IH - 34, w: 48, h: 26, asset: BTN_OFF,
                state_assets: { normal: BTN_OFF, hover: BTN_ON, pressed: BTN_ON },
                action: 'gallery_next:%row%' },
        text: { x: 60, y: IH - 34, w: IW - 120, h: 26, align: 'center',
                font: { size: 20, bold: true, color: '@palette.text_primary' } },
        edge: 'clamp'
      }
    }, {
      id: ID + '.page_tx', kind: 'text', z: 40, visible_default: true,
      x: 57, y: 920, w: 600, h: 60,
      font: { size: 26, color: '@palette.text_menu' }, align: 'left', valign: 'middle',
      wrap: false, max_lines: 1, sample: '第 1 / 2 页（测试）'
    }, {
      id: ID + '.page_prev', kind: 'hit', z: 96, visible_default: true,
      x: 700, y: 920, w: 190, h: 60, action: 'gallery_page_prev', label: '上一页', align: 'center',
      font: { size: 26, color: '@palette.text_menu' }
    }, {
      id: ID + '.page_next', kind: 'hit', z: 96, visible_default: true,
      x: 910, y: 920, w: 190, h: 60, action: 'gallery_page_next', label: '下一页', align: 'center',
      font: { size: 26, color: '@palette.text_menu' }
    }] };
  }

  var out = [];
  function log(s) { out.push(s); }
  function chk(tag, ok, detail) {
    log('★M08CHECK★ tag=' + tag + ' ok=' + (ok ? 1 : 0) + ' | ' + detail);
  }
  function base(p) { return String(p || '').replace(/^.*\//, '').replace(/["')]/g, ''); }

  /* 注入（**总是先做**）：造测试屏 + 给四承载屏补 attach:'gal_shell' */
  function inject() {
    var L = window.UI_LAYOUT;
    L.screens[ID] = buildTestScreen();
    L.screens[COEX] = buildCoexistScreen();
    HOSTS.forEach(function (h) {
      if (!L.screens[h]) L.screens[h] = { id: h, title_cn: h + '（注入占位）', owner: 'M1',
        elements: [{ id: h + '.bg', kind: 'rect', z: 0, visible_default: true,
                     x: 0, y: 0, w: 1920, h: 1080, color: '@palette.backdrop', opacity: 200 }] };
      L.screens[h].attach = 'gal_shell';
    });
  }

  /* 三者共存的测试屏：同一行上同时挂 `item_frame.state_assets`（逐项三态）
     + `item_buttons`（逐块按钮）+ `item_variants`（栏位内差分）—— 验证互不冲突。 */
  function buildCoexistScreen() {
    var rows = 3, IH = 80, IW = 600;
    return { id: COEX, title_cn: '共存测试屏', owner: 'M1', elements: [{
      id: COEX + '.list', kind: 'list', z: 30, visible_default: true,
      orientation: 'v', x: 60, y: 200, w: IW, item_h: IH, max_rows: rows,
      labels: ['共存行 1', '共存行 2', '共存行 3'],
      actions: ['coexist_row_0', 'coexist_row_1', 'coexist_row_2'],
      font: { size: 20, color: '@palette.text_menu' }, align: 'center',
      item_frame: { asset: A[0], state_assets: { normal: A[0], hover: A[1], pressed: A[2] } },
      item_buttons: [{ key: 'b1', x: 8, y: 8, w: 60, h: 24, asset: BTN_OFF,
                       state_assets: { normal: BTN_OFF, hover: BTN_ON, pressed: BTN_ON },
                       action: 'coexist_btn:%row%' }],
      item_variants: {
        frames: [[A[0], A[1]], [A[1], A[2]], [A[2], A[0]]],
        thumb: { x: 80, y: 8, w: 200, h: 64 },
        prev: { key: 'vprev', x: 300, y: 8, w: 48, h: 24, asset: BTN_OFF,
                state_assets: { normal: BTN_OFF, hover: BTN_ON, pressed: BTN_ON },
                action: 'gallery_prev:%row%' },
        next: { key: 'vnext', x: 360, y: 8, w: 48, h: 24, asset: BTN_OFF,
                state_assets: { normal: BTN_OFF, hover: BTN_ON, pressed: BTN_ON },
                action: 'gallery_next:%row%' },
        text: { x: 420, y: 8, w: 120, h: 24, align: 'center',
                font: { size: 20, bold: true, color: '@palette.text_primary' } },
        edge: 'clamp'
      }
    }] };
  }

  function run() {
    var L = window.UI_LAYOUT, R = window.UI_REPLICA;
    if (!L || !R) { log('★M08CHECK★ tag=PRE ok=0 | UI_LAYOUT / UI_REPLICA 未加载'); render(); return; }
    inject();

    /* ---------- ① 栏位内差分（测试网格页） ---------- */
    R.renderScreen(ID, { noHistory: true });
    R.setScale(1);
    function q(sel) { return document.querySelector(sel); }
    function qa(sel) { return document.querySelectorAll(sel); }
    function vBtn(row, which) {
      return q('[data-ui-kind="list-item-var-btn"][data-ui-var-index="' + row
        + '"][data-ui-var-which="' + which + '"]');
    }
    function vThumb(row) { return q('[data-ui-kind="list-item-var-thumb"][data-ui-var-index="' + row + '"]'); }
    function vText(row) { return q('[data-ui-kind="list-item-var-text"][data-ui-var-index="' + row + '"]'); }

    chk('grid.count', qa('[data-ui-kind="list-item"]').length === COLS * ROWS,
      '网格项 ' + qa('[data-ui-kind="list-item"]').length + '（期望 ' + (COLS * ROWS) + '）');
    chk('grid.varThumb', qa('[data-ui-kind="list-item-var-thumb"]').length === COLS * ROWS - 1,
      '缩略图 ' + qa('[data-ui-kind="list-item-var-thumb"]').length + '（留空 1 栏 ⇒ 期望 '
      + (COLS * ROWS - 1) + '）');
    var st0 = R.galleryState();
    st0.lastAct = ''; st0.lastRow = -1; st0.count = 0;
    var a0 = base(vThumb(0).style.backgroundImage);
    var t0 = vText(0).textContent;
    vBtn(0, 'next').dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    var a1 = base(vThumb(0).style.backgroundImage);
    var t1 = vText(0).textContent;
    chk('var.next', a1 !== a0 && t0 === '1/3' && t1 === '2/3'
        && R.galleryState().lastAct === 'gallery_next:0' && R.galleryState().lastRow === 0,
      '点 next：缩略图 ' + a0 + ' → ' + a1 + '，n/N ' + t0 + ' → ' + t1
      + '，派发 ' + R.galleryState().lastAct + ' 行号 ' + R.galleryState().lastRow);
    vBtn(0, 'prev').dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    chk('var.prev', base(vThumb(0).style.backgroundImage) === a0 && vText(0).textContent === '1/3'
        && R.galleryState().lastAct === 'gallery_prev:0',
      '点 prev：回到 ' + vText(0).textContent + '（' + base(vThumb(0).style.backgroundImage) + '）');
    var cnt = R.galleryState().count;
    vBtn(0, 'prev').dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    chk('var.clamp', vText(0).textContent === '1/3' && R.galleryState().count === cnt + 1,
      '边界 clamp：第 1 张再点 prev ⇒ 仍 ' + vText(0).textContent + '（派发仍发生 '
      + cnt + ' → ' + R.galleryState().count + '）');
    chk('var.empty-row', !vThumb(5) && !vBtn(5, 'prev') && !vText(5),
      '留空栏（frames=[]）不画：缩略图=' + !!vThumb(5) + ' 按钮=' + !!vBtn(5, 'prev'));
    var rej0 = (R.galleryState().rejects || []).length;
    chk('var.no-reject', rej0 === 0, '合法数据下守卫判词 ' + rej0 + ' 条（期望 0）');

    /* 守卫负向（内存副本） */
    var grid = null;
    L.screens[ID].elements.forEach(function (e) { if (e && e.item_variants) grid = e; });
    if (!grid) { log('★M08CHECK★ tag=grid.lookup ok=0 | 测试屏里找不到带 item_variants 的元素'); render(); return; }
    var keepV = grid.item_variants;
    grid.item_variants = 'oops';
    R.renderScreen(ID, { noHistory: true });
    grid.item_variants = { frames: 'oops' };
    R.renderScreen(ID, { noHistory: true });
    var rej1 = (R.galleryState().rejects || []).slice();
    var want1 = [ID + '.list[(item_variants)] item_variants 不是对象',
                 ID + '.list[(frames)] frames 不是数组'];
    /* ⚠️ `Array.indexOf` 是**元素全等**匹配，不是子串匹配 —— 判词带 `★M08VARIANT-REJECT★ ` 前缀，
         用 indexOf 永远 -1（实测踩过：判词明明都在、断言却恒 FAIL）。改用子串扫描。 */
    var miss1 = want1.filter(function (s) { return !rej1.some(function (l) { return l.indexOf(s) >= 0; }); });
    chk('guard.container', miss1.length === 0 && qa('[data-ui-kind="list-item-var-thumb"]').length === 0,
      '容器级非法逐条 REJECT：' + rej1.join('；') + '；缩略图节点 '
      + qa('[data-ui-kind="list-item-var-thumb"]').length + '（期望 0）');
    grid.item_variants = JSON.parse(JSON.stringify(keepV));
    grid.item_variants.frames[7] = 'oops';
    grid.item_variants.frames[8] = [''];
    R.renderScreen(ID, { noHistory: true });
    var rej2 = (R.galleryState().rejects || []).slice();
    var want2 = [ID + '.list[frames[7]] 第 7 栏差分列表不是数组',
                 ID + '.list[frames[8]] 差分素材为空（第 1 张）'];
    var miss2 = want2.filter(function (s) { return !rej2.some(function (l) { return l.indexOf(s) >= 0; }); });
    chk('guard.row', miss2.length === 0 && qa('[data-ui-var-index="7"]').length === 0,
      '逐栏非法逐条 REJECT：' + rej2.slice(-2).join('；') + '；坏栏 DOM 节点 '
      + qa('[data-ui-var-index="7"]').length + '（期望 0）');
    grid.item_variants = keepV;

    /* 页内翻页 */
    R.renderScreen(ID, { noHistory: true });
    var p0 = q('[data-ui-kind="list-item"]').getAttribute('data-ui-index');
    R.doGalleryAction('gallery_page_next');
    var p1 = q('[data-ui-kind="list-item"]').getAttribute('data-ui-index');
    R.doGalleryAction('gallery_page_prev');
    var p2 = q('[data-ui-kind="list-item"]').getAttribute('data-ui-index');
    chk('page.flip', p0 === '0' && p1 === String(COLS * ROWS) && p2 === '0',
      '页内翻页：首栏全局序号 ' + p0 + ' → ' + p1 + ' → ' + p2);

    /* ---------- ①b 三者共存：同一行上 item_frame.state_assets + item_buttons + item_variants ---------- */
    R.renderScreen(COEX, { noHistory: true });
    R.setScale(1);
    var cq = function (sel) { return document.querySelector(sel); };
    var cqa = function (sel) { return document.querySelectorAll(sel); };
    chk('coexist.render',
      cqa('[data-ui-kind="list-item"][data-ui-item-states="1"]').length === 3
      && cqa('[data-ui-kind="list-item-btn"][data-ui-item-btn="b1"]').length === 3
      && cqa('[data-ui-kind="list-item-var-btn"]').length === 6
      && cqa('[data-ui-kind="list-item-var-thumb"]').length === 3,
      '同行三件共存：逐项态行 ' + cqa('[data-ui-kind="list-item"][data-ui-item-states="1"]').length
      + '/3、逐块按钮 ' + cqa('[data-ui-kind="list-item-btn"]').length + '/3、差分按钮 '
      + cqa('[data-ui-kind="list-item-var-btn"]').length + '/6、差分缩略图 '
      + cqa('[data-ui-kind="list-item-var-thumb"]').length + '/3');
    /* 逐项三态：悬停第 2 行 ⇒ 该行 frame 换 hover 图，而差分缩略图仍 = frames[1][0] */
    var row1 = cq('[data-ui-kind="list-item"][data-ui-index="1"]');
    var f1 = row1 ? row1.querySelector('.ui-list-item-frame') : null;
    var fAsset0 = f1 ? String(f1.style.borderImageSource || f1.style.backgroundImage) : '';
    row1.dispatchEvent(new MouseEvent('mouseenter', { bubbles: false, cancelable: true, view: window }));
    var fAsset1 = f1 ? String(f1.style.borderImageSource || f1.style.backgroundImage) : '';
    var th1 = cq('[data-ui-kind="list-item-var-thumb"][data-ui-var-index="1"]');
    var thAsset = th1 ? String(th1.style.backgroundImage) : '';
    row1.dispatchEvent(new MouseEvent('mouseleave', { bubbles: false, cancelable: true, view: window }));
    chk('coexist.frame-state', fAsset0 !== fAsset1 && fAsset1.indexOf(base(A[1])) >= 0
        && thAsset.indexOf(base(A[1])) >= 0,
        '悬停第 2 行 ⇒ 逐项 frame 换 hover 图（' + base(fAsset0) + ' → ' + base(fAsset1)
        + '），差分缩略图不受影响（' + base(thAsset) + '）');
    /* 优先级：逐块按钮（声明在前）赢；差分按钮次之；块内其余区走整行 */
    if (window.__toastEl === undefined) { /* 无直接句柄：用 doAction 的可观测副作用 */ }
    /* ⚠️ 逐块按钮的探针属性是 `data-ui-item-btn-index`（不是 `data-ui-item-index`） */
    var b1 = cq('[data-ui-kind="list-item-btn"][data-ui-item-btn="b1"][data-ui-item-btn-index="1"]');
    if (!b1) { log('★M08CHECK★ tag=coexist.priority-btn ok=0 | 取不到第 2 行的逐块按钮节点'); }
    else {
    b1.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    }
    var toastTxt = (document.querySelector('.ui-toast') || {}).textContent || '';
    chk('coexist.priority-btn', toastTxt.indexOf('coexist_btn:1') >= 0,
      '点逐块按钮 ⇒ 派发它自己的 action 且 `%row%` 换成该行（toast="' + toastTxt.slice(0, 60) + '"）');
    var vn = cq('[data-ui-kind="list-item-var-btn"][data-ui-var-index="1"][data-ui-var-which="next"]');
    R.galleryState().lastAct = '';
    vn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    chk('coexist.priority-var', R.galleryState().lastAct === 'gallery_next:1'
        && R.galleryState().lastRow === 1,
      '点差分按钮（同一行上还挂着逐块按钮）⇒ 仍派发 gallery_next:1（实得 '
      + R.galleryState().lastAct + ' 行号 ' + R.galleryState().lastRow + '）');

    /* ---------- ② 四个承载屏的 attach 复用（绘制 + 命中） ---------- */
    HOSTS.forEach(function (h) {
      R.renderScreen(h, { noHistory: true });
      R.setScale(1);
      var attachOk = R.attachScreen() === 'gal_shell';
      var shellEls = qa('[data-ui-id^="gs."]').length;
      var tabFlag = R.getFlag('gal_tab');
      /* 外壳热区：真实点击（走 buildHit 的 click 监听 → doAction），断言**派发的是它自己的
         action**（页签动作的可观测副作用 = `galleryState().lastAct`；返回键 `close` 的副作用
         = 换屏）。每条点完把承载屏复位，保证互不干扰。 */
      var hitOk = 0, hits = 0, hitBad = [];
      var shell = L.screens.gal_shell;
      (shell && shell.elements ? shell.elements : []).forEach(function (e) {
        if (e.kind !== 'hit') return;
        hits++;
        var nd = q('[data-ui-id="' + e.id + '"]');
        if (!nd) { hitBad.push(e.id + ' 缺节点'); return; }
        R.galleryState().lastAct = '';
        var beforeScreen = R.state.screen;
        nd.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        var acted;
        if (String(e.action).indexOf('gallery_tab_') === 0) {
          acted = (R.galleryState().lastAct === e.action);
        } else {
          acted = (R.state.screen !== beforeScreen);
        }
        if (acted) hitOk++;
        else hitBad.push(e.id + '(' + e.action + ') 点击后 lastAct='
                         + R.galleryState().lastAct + ' 屏=' + R.state.screen);
        R.renderScreen(h, { noHistory: true });   /* 复位，供下一件 */
        R.setScale(1);
      });
      chk('attach.' + h, attachOk && shellEls > 0 && hits > 0 && hitOk === hits
          && tabFlag === h,
        '承载屏 ' + h + '：attach=' + R.attachScreen() + ' 外壳元素=' + shellEls
        + ' 热区命中 ' + hitOk + '/' + hits + ' gal_tab=' + tabFlag + '（期望 ' + h + '）'
        + (hitBad.length ? ' 失败：' + hitBad.join('；') : ''));
    });

    /* 复位到测试页，供截图 */
    R.renderScreen(ID, { noHistory: true });
    R.setScale(1);
    log('★M08CHECK★ tag=DONE ok=1 | 断言结束');
    render();
  }

  function render() {
    var pre = document.createElement('pre');
    pre.id = 'M08OUT';
    pre.textContent = 'M08OUTBEGIN\n' + out.join('\n') + '\nM08OUTEND';
    document.body.appendChild(pre);
  }

  var HOSTS = ['gallery', 'music', 'dress', 'replay'];
  /* 模式（`?m08=<assert|grid|host>`）：
       · assert —— 跑全部 DOM 断言并把结果写进 id=M08OUT 的 pre（供 --dump-dom 采集）；
       · grid   —— 只把测试网格页画出来（并重放 `?hover=` / `?press=` 探针）供截图；
       · host / 缺省 —— 只做注入，然后把深链的承载屏**重画一遍**（这样 dress/replay 的
         attach 补丁才会生效、外壳才画得出来）供截图。
       ⚠️ 本注释**刻意不写标签字面量**（尖括号形式）：--dump-dom 会把 script 正文原样序列化，
       注释里的标签字面量会被 Python 侧正则误当成真元素（实测踩过）。 */
  window.addEventListener('load', function () { setTimeout(function () {
    var R = window.UI_REPLICA;
    if (!R || !window.UI_LAYOUT) { log('★M08CHECK★ tag=PRE ok=0 | 未加载'); render(); return; }
    try { inject(); } catch (e) { log('★M08CHECK★ tag=EXC ok=0 | inject: ' + e.message); }
    var m = /[?&]m08=([a-z]+)/.exec(location.search || '');
    var mode = m ? m[1] : 'host';
    try {
      if (mode === 'assert') { run(); return; }
      if (mode === 'grid') {
        R.renderScreen(ID, { noHistory: true });
        R.setScale(1);
        /* ★ 两端同态可比：引擎侧 `shot_57_gallery.png` 是**巡演跑完 `galvar auto:next` 之后**
           的帧（首栏序号 = 1、`n/N` = 2/3）⇒ 这里把首栏序号预置成 1，否则比的是两个不同状态
           （实测踩过：首栏整区 MAD 86/255 里大部分来自「缩略图不同一张」而非机制差异）。 */
        R.varIdxSet(ID + '.list', 0, 1);
        R.renderScreen(ID, { noHistory: true });
        R.setScale(1);
        var hm = /[?&]hover=([A-Za-z0-9_.\-~]+)/.exec(location.search || '');
        if (hm) R.hoverProbe(hm[1]);
        var pm = /[?&]press=([A-Za-z0-9_.\-~]+)/.exec(location.search || '');
        if (pm) R.pressProbe(pm[1]);
      } else {
        var dm = /[?&]screen=([A-Za-z0-9_]+)/.exec(location.search || '');
        if (dm && window.UI_LAYOUT.screens[dm[1]]) R.renderScreen(dm[1], { noHistory: true });
        R.setScale(1);
      }
    } catch (e) { log('★M08CHECK★ tag=EXC ok=0 | ' + e.message); }
    render();
  }, 1500); });
})();
</script>
"""


def build_page():
    html = io.open(os.path.join(REP, "index.html"), encoding="utf-8").read()
    # 临时页落在 `_工作\ISSUE-20260924-08_鉴赏模式\`（**两层**）⇒ 退两层回到 `UI组\`
    P = "../../"
    for a, b in (('href="replica.css"', 'href="' + P + '复刻/replica.css"'),
                 ('src="ui_layout.js"', 'src="' + P + '复刻/ui_layout.js"'),
                 ('src="flow_data.js"', 'src="' + P + '复刻/flow_data.js"'),
                 ('src="replica.js"', 'src="' + P + '复刻/replica.js"')):
        html = html.replace(a, b)
    html = html.replace('<script src="' + P + '复刻/ui_layout.js"></script>',
                        "<script>window.UI_ASSET_ROOT='" + P + "krkr/assets/';</script>\n"
                        '<script src="' + P + '复刻/ui_layout.js"></script>')
    html = html.replace('</body>', HOOK + '\n</body>')
    io.open(PAGE, "w", encoding="utf-8").write(html)
    return PAGE


def url(query=""):
    return "file:///" + urllib.parse.quote(PAGE.replace("\\", "/")) + query


def edge(args, query):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1920,1080", "--virtual-time-budget=12000"] + args + [url(query)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace")


def region_stats(png, box):
    from collections import Counter
    im = Image.open(png).convert("RGBA")
    crop = im.crop(box)
    px = crop.load()
    w, h = crop.size
    c = Counter(px[i, j][:3] for i in range(0, w, 2) for j in range(0, h, 2))
    bg, bgn = c.most_common(1)[0]
    tot = sum(c.values())
    return bg, bgn / tot, (tot - bgn) / tot


def region_mad(png_a, png_b, box):
    from PIL import ImageChops
    a = Image.open(png_a).convert("RGB").crop(box)
    b = Image.open(png_b).convert("RGB").crop(box)
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    tot = sum(hist[0:256]) + sum(hist[256:512]) + sum(hist[512:768])
    s = sum(i * hist[i] for i in range(256)) + sum(i * hist[256 + i] for i in range(256)) \
        + sum(i * hist[512 + i] for i in range(256))
    return (s / tot) if tot else 0.0


def find_engine_pngs(engine_dir):
    """引擎导图目录 → {屏名: 最新一张 PNG}（shot_NN_<screen>.png）。"""
    out = {}
    if not os.path.isdir(engine_dir):
        return out
    for f in sorted(os.listdir(engine_dir)):
        m = re.match(r"shot_(\d+)_([a-z_]+)\.png$", f)
        if not m:
            continue
        out[m.group(2)] = os.path.join(engine_dir, f)     # 后者覆盖前者 ⇒ 留最新
    return out


def main():
    os.makedirs(SHOTS, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    build_page()
    fails = []
    info = []

    # ---- DOM 断言（--dump-dom） ----
    dom = edge(["--dump-dom"], "?m08=assert")
    dump_p = os.path.join(EVID, "诊断_HTML探针.dom.html")
    io.open(dump_p, "w", encoding="utf-8").write(dom)
    m = re.search(r"M08OUTBEGIN\r?\n(.*?)\r?\nM08OUTEND", dom, re.S)
    txt = m.group(1).strip() if m else ""
    for a, b in (("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")):
        txt = txt.replace(a, b)
    print("===== HTML DOM 断言（★M08CHECK★）=====")
    checks = {}
    for tag, ok, detail in re.findall(r"★M08CHECK★ tag=([\w.\-]+) ok=(\d) \| (.*)", txt):
        checks[tag] = (ok == "1", detail)
        print("  [%s] %-16s %s" % ("OK" if ok == "1" else "FAIL", tag, detail[:220]))
    if not checks:
        fails.append("未取到 HTML 探针输出（页面可能未渲染完）")
    for tag in ("grid.count", "grid.varThumb", "var.next", "var.prev", "var.clamp",
                "var.empty-row", "var.no-reject", "guard.container", "guard.row",
                "page.flip", "coexist.render", "coexist.frame-state",
                "coexist.priority-btn", "coexist.priority-var",
                "attach.gallery", "attach.music", "attach.dress",
                "attach.replay", "DONE"):
        if tag not in checks:
            fails.append("缺少断言 %s" % tag)
        elif not checks[tag][0]:
            fails.append("断言 %s 失败：%s" % (tag, checks[tag][1]))

    # ---- 截图（四承载屏 + 测试网格页 + 悬停/按下态） ----
    print("\n===== HTML 无头截图 =====")
    shots = {}
    for h in HOSTS:
        p = os.path.join(SHOTS, "html_%s.png" % h)
        edge(["--screenshot=" + p], "?screen=" + h)
        shots[h] = p
        _bg, _rbg, roth = region_stats(p, STRIP_REGION)
        print("  %-22s 页签条区非背景 %.3f" % ("html_%s.png" % h, roth))
        if roth < 0.02:
            fails.append("HTML 侧 %s 的页签条区非背景仅 %.3f（外壳没画出来？）" % (h, roth))
    pg = os.path.join(SHOTS, "html_grid.png")
    edge(["--screenshot=" + pg], "?m08=grid")
    edge(["--screenshot=" + os.path.join(SHOTS, "html_grid_hover.png")],
         "?m08=grid&hover=__gal_grid.list~0~vnext")
    edge(["--screenshot=" + os.path.join(SHOTS, "html_grid_press.png")],
         "?m08=grid&press=__gal_grid.list~0~vnext")

    # ---- 两端一致（引擎自导 PNG vs HTML 截图） ----
    engine_dir = ""
    for i, a in enumerate(sys.argv[1:]):
        if a == "--engine-png":
            engine_dir = sys.argv[1:][i + 1]
    if not engine_dir:
        for d in DEF_ENGINE_DIRS:
            if os.path.isdir(d):
                engine_dir = d
                break
    print("\n===== 两端一致量化（引擎自导 PNG vs HTML 无头截图）=====")
    print("  引擎导图目录：%s" % (engine_dir or "(未找到)"))
    epng = find_engine_pngs(engine_dir)
    if not epng:
        fails.append("未找到引擎导图（先跑 m08_gallery_tour.py）")
    else:
        # 网格首栏：引擎的 gallery 导图 vs HTML 的 __gal_grid 截图
        if "gallery" in epng:
            mad = region_mad(epng["gallery"], pg, CELL0_REGION)
            _bg, _rbg, roth_e = region_stats(epng["gallery"], CELL0_REGION)
            _bg2, _rbg2, roth_h = region_stats(pg, CELL0_REGION)
            info.append("网格首栏区 %s：引擎非背景 %.3f / HTML 非背景 %.3f / 平均绝对差 %.1f/255"
                        % (str(CELL0_REGION), roth_e, roth_h, mad))
            print("  " + info[-1])
            mad2 = region_mad(epng["gallery"], pg, BTN_BAND_REGION)
            info.append("（测试页自比，仅登记）首栏底部带 %s（左右差分按钮 + n/N 文本）："
                        "平均绝对差 %.1f/255" % (str(BTN_BAND_REGION), mad2))
            print("  " + info[-1])
        # 外壳页签条 + 内容区：**优先用 --real 的导图目录**（同屏同数据才可比）
        #   ★ M8 一审修复轮（2026-09-24）小改：调用方显式给 `--engine-png` 时**同样用于本段** ——
        #   原先 real_dir 只在三个硬编码目录名里挑（含 "real" 字样者），本轮 `--rundir
        #   ui_run_m08_r2fix` 的 --real 导图因此落不进来、对照一直用 M1 期的旧导图（旧布局 vs
        #   新布局，MAD 虚高且信息失真）。显式参数 = 调用方声明「就用这份导图」⇒ 尊重之。
        real_dir = ""
        if engine_dir:
            real_dir = engine_dir
        else:
            for d in DEF_ENGINE_DIRS:
                if os.path.isdir(d) and "real" in os.path.basename(os.path.dirname(os.path.dirname(d))):
                    real_dir = d
                    break
        rpng = find_engine_pngs(real_dir) if real_dir else {}
        if rpng:
            info.append("两端一致（**真实数据**，引擎 --real 导图 vs HTML 同屏截图）：")
            print("  " + info[-1])
            for h in ("gallery", "music", "dress"):
                if h not in rpng:
                    continue
                hp = shots[h]
                m_strip = region_mad(rpng[h], hp, STRIP_REGION)
                m_grid = region_mad(rpng[h], hp, GRID_REGION)
                _bg, _rbg, re_ = region_stats(rpng[h], STRIP_REGION)
                _bg2, _rbg2, rh_ = region_stats(hp, STRIP_REGION)
                info.append("  %-8s 页签条区 引擎 %.3f / HTML %.3f，MAD %.1f ｜ 内容区 MAD %.1f"
                            % (h, re_, rh_, m_strip, m_grid))
                print("  " + info[-1])
                if re_ < 0.02 or rh_ < 0.02:
                    fails.append("页签条区 %s：一端几乎无内容（引擎 %.3f / HTML %.3f）" % (h, re_, rh_))
                if m_strip > 90:
                    fails.append("页签条区 %s：两端平均绝对差 %.1f/255 偏大" % (h, m_strip))
                if m_grid > 60:
                    fails.append("内容区 %s：两端平均绝对差 %.1f/255 偏大" % (h, m_grid))
        else:
            info.append("（未找到 --real 导图目录 ⇒ 真实数据的同屏对照跳过；"
                        "跑 m08_gallery_tour.py --real 后再跑本脚本即可）")
            print("  " + info[-1])
        # 测试页（注入模式）的 gallery 页签条：与 html_grid.png 同数据
        if "gallery" in epng:
            mad = region_mad(epng["gallery"], pg, STRIP_REGION)
            info.append("（测试页自比）页签条区 gallery：MAD %.1f/255" % mad)
            print("  " + info[-1])

    os.remove(PAGE)
    print("\n===== 判定 =====")
    print("MODE=NORMAL")
    for l in info:
        print("  " + l)
    print("  " + ("\n  ".join(fails) if fails else "全部断言通过"))
    print("RESULT=" + ("FAIL" if fails else "OK"))
    print("★ 退出码：", 1 if fails else 0)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())