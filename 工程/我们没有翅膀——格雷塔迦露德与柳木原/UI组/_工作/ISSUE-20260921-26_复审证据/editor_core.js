/* ==========================================================================
   editor_core.js —— 编辑器内核（M35）
   状态 / 渲染钩子 / 叠加层 / 选中 / 拖拽 / 缩放 / 吸附 / 撤销重做
   依赖：replica.js（渲染内核）、ui_layout.js（数据）、asset_index.js（资料库索引）
   全局导出：window.UI_EDITOR
   ========================================================================== */
(function () {
  'use strict';

  var R = window.UI_REPLICA, L = window.UI_LAYOUT, AIX = window.UI_ASSET_INDEX;
  if (!R || !L) { alert('editor_core.js：需要先加载 ui_layout.js 与 replica.js'); return; }

  var CW = L.canvas.width, CH = L.canvas.height;
  var SNAP = 6;              // 吸附阈值（画布坐标 px）

  var ED = {
    sid: null,               // 当前屏 id
    els: [],                 // 当前屏元素（编辑态，深拷贝）
    sel: [],                 // 选中 id 数组
    undo: [], redo: [],
    snap: true, grid: false, outline: false,
    gridStep: 10,
    dragging: null,
    ui: {},                 // 由 editor_ui.js 挂入 prop/tree/check 三个刷新器
    zoom: 1
  };

  /* ------------------------------------------------------------ DOM */
  var $ = function (id) { return document.getElementById(id); };
  var stage, canvas, overlay;

  function q(sel, root) { return (root || document).querySelector(sel); }

  /* ------------------------------------------------------- 数据读写 */
  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  function screenOf(sid) { return L.screens[sid]; }

  function loadScreen(sid) {
    var sc = screenOf(sid);
    if (!sc) { setStatus('该屏不存在：' + sid, 'bad'); return false; }
    ED.sid = sid;
    ED.els = clone(sc.elements || []);
    ED.sel = [];
    ED.undo = []; ED.redo = [];
    syncToLayout();
    reRender();
    refreshAll();
    setStatus('已载入「' + (sc.title_cn || sid) + '」，' + ED.els.length + ' 个元素');
    return true;
  }

  /* 把编辑态写回 ui_layout（replica 从它渲染，于是 DOM 永远等于编辑态） */
  function syncToLayout() {
    var sc = screenOf(ED.sid);
    if (sc) sc.elements = ED.els;
  }

  function reRender() {
    syncToLayout();
    R.renderScreen(ED.sid, { noHistory: true });
    syncOverlay();
    drawGrid();
    drawOverlay();
  }

  /* ------------------------------------------------------- 叠加层定位 */
  function syncOverlay() {
    canvas = canvas || $('canvas');
    overlay = overlay || $('ed-overlay');
    stage = stage || $('ed-stage');
    if (!canvas || !overlay) return;
    var cr = canvas.getBoundingClientRect(), sr = stage.getBoundingClientRect();
    var s = cr.width / CW;
    ED.zoom = s;
    overlay.style.left = (cr.left - sr.left) + 'px';
    overlay.style.top = (cr.top - sr.top) + 'px';
    overlay.style.width = CW + 'px';
    overlay.style.height = CH + 'px';
    overlay.style.transform = 'scale(' + s + ')';
    var g = document.getElementById('ed-gridlayer');
    if (g) {
      g.style.left = (cr.left - sr.left) + 'px';
      g.style.top = (cr.top - sr.top) + 'px';
      g.style.transform = 'scale(' + s + ')';
    }
    var z = $('ed-zoom'); if (z) z.textContent = (s * 100).toFixed(1) + '%';
  }

  /* 鼠标 → 画布坐标 */
  function toCanvas(ev) {
    var cr = canvas.getBoundingClientRect();
    return { x: (ev.clientX - cr.left) / (cr.width / CW),
             y: (ev.clientY - cr.top) / (cr.height / CH) };
  }

  /* ------------------------------------------------------------ 查询 */
  function byId(id) { for (var i = 0; i < ED.els.length; i++) if (ED.els[i].id === id) return ED.els[i]; return null; }
  function idxOf(id) { for (var i = 0; i < ED.els.length; i++) if (ED.els[i].id === id) return i; return -1; }
  function isVisible(e) { return e.visible_default !== false; }

  /* 命中测试：z 从高到低；**默认跳过 hit**（热区常与贴图同矩形，会挡住选中），
     只有没命中任何实体元素时才回退到 hit。 */
  function hitTest(p) {
    var cand = ED.els.slice().sort(function (a, b) { return (b.z || 0) - (a.z || 0); });
    for (var pass = 0; pass < 2; pass++) {
      for (var i = 0; i < cand.length; i++) {
        var e = cand[i];
        if (!isVisible(e)) continue;
        if (pass === 0 && e.kind === 'hit') continue;
        if (pass === 1 && e.kind !== 'hit') continue;
        var x = num(e.x), y = num(e.y), w = elemW(e), h = elemH(e);
        if (p.x >= x && p.x <= x + w && p.y >= y && p.y <= y + h) return e;
      }
    }
    return null;
  }

  function num(v) { return typeof v === 'number' ? v : (parseFloat(v) || 0); }

  /* 点是否落在某元素的版面矩形内（用于「选中即可拖」） */
  function inRect(p, e) {
    if (!e || !isVisible(e)) return false;
    var x = num(e.x), y = num(e.y), w = elemW(e), h = elemH(e);
    return p.x >= x && p.x <= x + w && p.y >= y && p.y <= y + h;
  }
  /* 点是否落在当前选区的任一元素内 */
  function inSelection(p) {
    for (var i = 0; i < ED.sel.length; i++) if (inRect(p, byId(ED.sel[i]))) return true;
    return false;
  }
  /* 选中项是否已被拖起（供光标提示） */
  function selRects() {
    var out = [];
    for (var i = 0; i < ED.sel.length; i++) { var e = byId(ED.sel[i]); if (e) out.push(e); }
    return out;
  }
  function elemW(e) { return num(e.w); }
  function elemH(e) { return num(e.h); }

  /* -------------------------------------------------------- 撤销重做 */
  function snapshot(label) {
    ED.undo.push({ label: label || 'edit', els: clone(ED.els) });
    if (ED.undo.length > 120) ED.undo.shift();
    ED.redo.length = 0;
    refreshHistory();
  }
  function doUndo() {
    if (!ED.undo.length) return;
    ED.redo.push({ label: 'redo', els: clone(ED.els) });
    ED.els = ED.undo.pop().els;
    ED.sel = ED.sel.filter(function (id) { return byId(id); });
    reRender(); refreshAll(); setStatus('已撤销');
  }
  function doRedo() {
    if (!ED.redo.length) return;
    ED.undo.push({ label: 'undo', els: clone(ED.els) });
    ED.els = ED.redo.pop().els;
    ED.sel = ED.sel.filter(function (id) { return byId(id); });
    reRender(); refreshAll(); setStatus('已重做');
  }
  function refreshHistory() {
    var u = $('ed-undo'), r = $('ed-redo');
    if (u) u.disabled = !ED.undo.length;
    if (r) r.disabled = !ED.redo.length;
  }

  /* ------------------------------------------------------------ 吸附 */
  var guides = [];
  function snapTargets(excludeIds) {
    var xs = [0, CW / 2, CW], ys = [0, CH / 2, CH];
    for (var i = 0; i < ED.els.length; i++) {
      var e = ED.els[i];
      if (excludeIds && excludeIds.indexOf(e.id) >= 0) continue;
      if (!isVisible(e)) continue;
      var x = num(e.x), y = num(e.y), w = elemW(e), h = elemH(e);
      xs.push(x, x + w / 2, x + w);
      ys.push(y, y + h / 2, y + h);
    }
    // ★ 网格吸附由 snapRect 直接做（见下），这里不再塞伪目标。
    return { xs: xs, ys: ys };
  }

  /* 把 (x,y,w,h) 对齐到最近的目标线；返回修正量 */
  function snapRect(x, y, w, h, excludeIds) {
    guides = [];
    if (!ED.snap) return { x: x, y: y };
    var t = snapTargets(excludeIds);
    var bx = null, by = null;
    var selfX = [x, x + w / 2, x + w], selfY = [y, y + h / 2, y + h];
    for (var i = 0; i < selfX.length; i++) {
      for (var j = 0; j < t.xs.length; j++) {
        var d = t.xs[j] - selfX[i];
        if (Math.abs(d) <= SNAP && (bx === null || Math.abs(d) < Math.abs(bx.d))) bx = { d: d, line: t.xs[j] };
      }
    }
    for (var k = 0; k < selfY.length; k++) {
      for (var m = 0; m < t.ys.length; m++) {
        var d2 = t.ys[m] - selfY[k];
        if (Math.abs(d2) <= SNAP && (by === null || Math.abs(d2) < Math.abs(by.d))) by = { d: d2, line: t.ys[m] };
      }
    }
    // 网格吸附：元素左/上边离最近网格线 ≤ SNAP 时对齐过去
    if (ED.grid) {
        var gx = snapGridVal(x), gy = snapGridVal(y);
        if (gx !== null && (bx === null || Math.abs(gx - x) <= Math.abs(bx.d))) { x = gx; bx = { d: gx - x, line: gx }; }
        if (gy !== null && (by === null || Math.abs(gy - y) <= Math.abs(by.d))) { y = gy; by = { d: gy - y, line: gy }; }
    }
    if (bx) { guides.push({ axis: 'x', v: bx.line }); }
    if (by) { guides.push({ axis: 'y', v: by.line }); }
    return { x: Math.round(x), y: Math.round(y) };
  }

  /* ------------------------------------------------------------ 网格 */
  function snapGridVal(v) {
    var st = ED.gridStep || 20;
    var nearest = Math.round(v / st) * st;
    return Math.abs(nearest - v) <= SNAP ? nearest : null;
  }

  /* 全屏网格：用一个 div 的 repeating-linear-gradient 画（零 DOM 子节点），
     另加中心十字与坐标刻度。鼠标穿透（pointer-events:none）。 */
  function drawGrid() {
    var g = document.getElementById('ed-gridlayer');
    if (!g) return;
    if (!ED.grid) { g.className = 'ed-gridlayer'; g.innerHTML = ''; return; }
    var st = ED.gridStep || 20;
    var c = ['rgba(122,176,232,.55)', 'rgba(122,176,232,.22)'];   // 主刻度 / 次刻度
    g.className = 'ed-gridlayer on';
    g.style.width = CW + 'px';
    g.style.height = CH + 'px';
    // 主刻度 = 5 格
    var grid = 'linear-gradient(to right,' + c[1] + ' 1px,transparent 1px),'
             + 'linear-gradient(to bottom,' + c[1] + ' 1px,transparent 1px),'
             + 'linear-gradient(to right,' + c[0] + ' 1px,transparent 1px),'
             + 'linear-gradient(to bottom,' + c[0] + ' 1px,transparent 1px)';
    g.style.backgroundImage = grid;
    g.style.backgroundSize = st + 'px ' + st + 'px,' + st + 'px ' + st + 'px,'
                           + (st * 5) + 'px ' + (st * 5) + 'px,' + (st * 5) + 'px ' + (st * 5) + 'px';
    // 中心十字 + 画布边框
    var parts = ['<div class="frame"></div>',
      '<div class="cross" style="left:' + (CW / 2) + 'px;top:0;width:1px;height:' + CH + 'px"></div>',
      '<div class="cross" style="left:0;top:' + (CH / 2) + 'px;width:' + CW + 'px;height:1px"></div>'];
    // 坐标刻度：每 5 格标一个数（步长太小时隔 10 格）
    var every = st * 5;
    for (var x = 0; x <= CW; x += every) {
      parts.push('<div class="tick h" style="left:' + x + 'px">' + x + '</div>');
    }
    for (var y = 0; y <= CH; y += every) {
      if (y === 0) continue;
      parts.push('<div class="tick v" style="top:' + y + 'px">' + y + '</div>');
    }
    g.innerHTML = parts.join('');
  }

  /* -------------------------------------------------------- 绘制叠加层 */
  function drawOverlay() {
    if (!overlay) return;
    var parts = [];
    // 选中框 + 手柄
    for (var i = 0; i < ED.sel.length; i++) {
      var e = byId(ED.sel[i]);
      if (!e) continue;
      var x = num(e.x), y = num(e.y), w = elemW(e), h = elemH(e);
      parts.push('<div class="box sel" style="left:' + x + 'px;top:' + y + 'px;width:' + w
        + 'px;height:' + h + 'px;background:rgba(255,208,96,.07)"></div>');
      if (ED.sel.length === 1) {
        parts.push('<div class="tag" style="left:' + x + 'px;top:' + (y - 15) + 'px">' + esc(e.id) + ' · ' + e.kind + '</div>');
        var hs = [['nw', x, y], ['n', x + w / 2, y], ['ne', x + w, y], ['e', x + w, y + h / 2],
                  ['se', x + w, y + h], ['s', x + w / 2, y + h], ['sw', x, y + h], ['w', x, y + h / 2]];
        for (var j = 0; j < hs.length; j++) {
          parts.push('<div class="hd ' + hs[j][0] + '" data-hd="' + hs[j][0] + '" style="left:' + hs[j][1] + 'px;top:' + hs[j][2] + 'px"></div>');
        }
      }
    }
    // 吸附参考线
    for (var g = 0; g < guides.length; g++) {
      var gl = guides[g];
      parts.push(gl.axis === 'x'
        ? '<div class="snap" style="left:' + gl.v + 'px;top:0;width:1px;height:' + CH + 'px"></div>'
        : '<div class="snap" style="left:0;top:' + gl.v + 'px;width:' + CW + 'px;height:1px"></div>');
    }
    overlay.innerHTML = parts.join('');
    overlay.style.display = '';
  }

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }

  /* ------------------------------------------------------- 指针交互 */
  function setupPointer() {
    overlay.addEventListener('pointerdown', onDown);
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('resize', function () { syncOverlay(); });
  }

  function onDown(ev) {
    if (ev.button !== 0) return;
    var hd = ev.target.getAttribute && ev.target.getAttribute('data-hd');
    var p = toCanvas(ev);
    ev.preventDefault();
    overlay.setPointerCapture && overlay.setPointerCapture(ev.pointerId);

    if (hd) {                                    // 缩放
      var e = byId(ED.sel[0]);
      if (!e) return;
      snapshot('resize');
      ED.dragging = { mode: 'resize', hd: hd, start: p, o0: { x: num(e.x), y: num(e.y), w: elemW(e), h: elemH(e) }, id: e.id };
      return;
    }

    // ★ 选中即可拖：指针落在已选元素范围内 → 直接拖动选区，**不再重新命中测试**，
    //   从而避免「按下去命中它上面/下面的另一层」。要强制重选请按 Alt 点击。
    if (!ev.altKey && !ev.shiftKey && ED.sel.length && inSelection(p)) {
      snapshot('move');
      ED.dragging = { mode: 'move', start: p,
                      orig: ED.sel.map(function (id) { var o = byId(id); return { id: id, x: num(o.x), y: num(o.y) }; }) };
      return;
    }

    var hit = hitTest(p);
    if (!hit) {                                  // 空白 → 框选
      if (!ev.shiftKey) { ED.sel = []; drawOverlay(); refreshProp(); refreshTree(); }
      ED.dragging = { mode: 'marquee', start: p };
      return;
    }
    if (ev.shiftKey) {
      var k = ED.sel.indexOf(hit.id);
      if (k >= 0) ED.sel.splice(k, 1); else ED.sel.push(hit.id);
    } else if (ED.sel.indexOf(hit.id) < 0) {
      ED.sel = [hit.id];
    }
    drawOverlay(); refreshProp(); refreshTree();
    snapshot('move');
    ED.dragging = { mode: 'move', start: p,
                    orig: ED.sel.map(function (id) { var o = byId(id); return { id: id, x: num(o.x), y: num(o.y) }; }) };
  }

  function onMove(ev) {
    var p = toCanvas(ev);
    var cu = $('ed-cursor'); if (cu) cu.textContent = Math.round(p.x) + ', ' + Math.round(p.y);
    if (!ED.dragging) {
      // 光标提示：落在已选元素内 → move；按 Alt 时回调为默认（可重选）
      overlay.style.cursor = (ED.sel.length && !ev.altKey && inSelection(p)) ? 'move' : '';
      return;
    }
    var d = ED.dragging;

    if (d.mode === 'move') {
      var dx = p.x - d.start.x, dy = p.y - d.start.y;
      if (ev.shiftKey) { if (Math.abs(dx) > Math.abs(dy)) dy = 0; else dx = 0; }   // Shift 轴向约束
      var first = d.orig[0];
      var snapped = snapRect(first.x + dx, first.y + dy, 0, 0, ED.sel);
      var sdx = snapped.x - first.x, sdy = snapped.y - first.y;
      for (var i = 0; i < d.orig.length; i++) {
        var e = byId(d.orig[i].id); if (!e) continue;
        e.x = Math.round(d.orig[i].x + sdx);
        e.y = Math.round(d.orig[i].y + sdy);
      }
      reRender();
      return;
    }

    if (d.mode === 'resize') {
      var e2 = byId(d.id); if (!e2) return;
      var o = d.o0, hd = d.hd;
      var nx = o.x, ny = o.y, nw = o.w, nh = o.h;
      var mx = p.x - d.start.x, my = p.y - d.start.y;
      if (hd.indexOf('e') >= 0) nw = o.w + mx;
      if (hd.indexOf('s') >= 0) nh = o.h + my;
      if (hd.indexOf('w') >= 0) { nx = o.x + mx; nw = o.w - mx; }
      if (hd.indexOf('n') >= 0) { ny = o.y + my; nh = o.h - my; }
      if (ev.shiftKey && hd.length === 2) {       // Shift 等比
        var k = Math.max(nw / o.w, nh / o.h);
        nw = o.w * k; nh = o.h * k;
        if (hd.indexOf('w') >= 0) nx = o.x + (o.w - nw);
        if (hd.indexOf('n') >= 0) ny = o.y + (o.h - nh);
      }
      var sp = snapRect(nx, ny, nw, nh, [d.id]);
      nx += (sp.x - nx);  ny += (sp.y - ny);
      e2.x = Math.round(nx); e2.y = Math.round(ny);
      e2.w = Math.max(1, Math.round(nw)); e2.h = Math.max(1, Math.round(nh));
      if (e2.kind === 'image' && e2.nine) {       // 九宫格：保证 w>=l+r、h>=t+b
        var n = e2.nine, lr = num(n.l) + num(n.r), tb = num(n.t) + num(n.b);
        if (lr > 0) e2.w = Math.max(e2.w, lr);
        if (tb > 0) e2.h = Math.max(e2.h, tb);
      }
      reRender();
      return;
    }

    if (d.mode === 'marquee') {
      var x0 = Math.min(d.start.x, p.x), y0 = Math.min(d.start.y, p.y);
      var x1 = Math.max(d.start.x, p.x), y1 = Math.max(d.start.y, p.y);
      ED.sel = ED.els.filter(function (e) {
        if (!isVisible(e) || e.kind === 'hit') return false;
        var ex = num(e.x), ey = num(e.y), ew = elemW(e), eh = elemH(e);
        return !(ex > x1 || ex + ew < x0 || ey > y1 || ey + eh < y0);
      }).map(function (e) { return e.id; });
      drawOverlay();
      overlay.insertAdjacentHTML('beforeend',
        '<div class="marquee" style="left:' + x0 + 'px;top:' + y0 + 'px;width:' + (x1 - x0) + 'px;height:' + (y1 - y0) + 'px"></div>');
      return;
    }
  }

  function onUp() {
    if (!ED.dragging) return;
    var was = ED.dragging.mode;
    ED.dragging = null;
    guides = [];
    reRender(); refreshProp(); refreshTree(); refreshCheck(); refreshStatus();
    if (was === 'move' || was === 'resize') setStatus('已修改几何（记得导出 JSON）');
  }

  /* --------------------------------------------------------- 状态行 */
  function setStatus(msg, cls) {
    var el = $('ed-status'); if (!el) return;
    el.textContent = msg || '';
    el.className = cls || '';
  }
  function refreshStatus() {
    var c = $('ed-count'); if (c) c.textContent = ED.els.length;
    var s = $('ed-selcount'); if (s) s.textContent = ED.sel.length;
    var cv = $('ed-canvas'); if (cv) cv.textContent = CW + '×' + CH;
  }

  /* ------------------------------------------- 刷新分发（模块级，供内部调用） */
  /* ★ 注意：这四个必须定义在**模块作用域**——初版只把它们放进了导出对象里，
     内部 at 模块级调用 `refreshProp()` 会 ReferenceError（已实测踩到）。 */
  function refreshProp() { ED.ui.prop && ED.ui.prop(); }
  function refreshTree() { ED.ui.tree && ED.ui.tree(); }
  function refreshCheck() { ED.ui.check && ED.ui.check(); }
  function refreshAll() { refreshStatus(); refreshProp(); refreshTree(); refreshCheck(); }

  /* ------------------------------------------------------------ 导出 */
  function exportJSON() {
    var sc = screenOf(ED.sid);
    var out = {
      id: sc.id,
      title_cn: sc.title_cn || '',
      owner: sc.owner || 'M35',
      note: sc.note || '',
      elements: ED.els
    };
    return JSON.stringify(out, null, 2);
  }

  /* ------------------------------------------- 对外暴露（供 editor_ui.js） */
  window.UI_EDITOR = {
    ED: ED, CW: CW, CH: CH,
    loadScreen: loadScreen, reRender: reRender, syncOverlay: syncOverlay,
    drawOverlay: drawOverlay, exportJSON: exportJSON, snapshot: snapshot,
    doUndo: doUndo, doRedo: doRedo, refreshStatus: refreshStatus,
    setStatus: setStatus, byId: byId, idxOf: idxOf, esc: esc, num: num,
    drawGrid: drawGrid, inSelection: inSelection, inRect: inRect,
    elemW: elemW, elemH: elemH, isVisible: isVisible,
    /* 由 editor_ui.js 填充 */
    _ui: ED.ui,
    refreshProp: refreshProp, refreshTree: refreshTree,
    refreshCheck: refreshCheck, refreshAll: refreshAll
  };

  /* ------------------------------------------------------------ 启动 */
  /* 错误兜底：把未捕获异常显示到底栏 + 画面左上角，便于自查（编辑器也该有） */
  window.addEventListener('error', function (ev) {
    var m = (ev && ev.message) || 'unknown error';
    var src = (ev && ev.filename ? ev.filename.split('/').pop() : '') + ':' + (ev && ev.lineno);
    var st = document.getElementById('ed-status');
    if (st) { st.textContent = '❌ ' + m + '  @' + src; st.className = 'bad'; }
    var box = document.getElementById('ed-errbox');
    if (!box) {
      box = document.createElement('div');
      box.id = 'ed-errbox';
      box.style.cssText = 'position:fixed;left:0;top:0;right:0;z-index:99999;background:#5c1a1a;'
        + 'color:#ffd0d0;font:12px/1.6 Consolas,monospace;padding:8px 12px;white-space:pre-wrap;max-height:40vh;overflow:auto';
      document.body.appendChild(box);
    }
    box.textContent += '❌ ' + m + '\n     @ ' + src + '\n';
  });

  function boot() {
    canvas = $('canvas'); overlay = $('ed-overlay'); stage = $('ed-stage');
    if (!canvas || !overlay) { console.error('editor: 缺 #canvas 或 #ed-overlay'); return; }
    setupPointer();
    // 默认载入深链指定屏，否则 title
    var m = /[?&]screen=([A-Za-z0-9_]+)/.exec(location.search || '');
    var sid = (m && m[1]) ? m[1] : 'title';
    if (!screenOf(sid)) sid = 'title';
    loadScreen(sid);
    // 自检钩子：?sel=<元素id>[,<id>...] 预选中，供无头截图验证选中框与手柄
    var sm = /[?&]sel=([A-Za-z0-9_.\-,]+)/.exec(location.search || '');
    if (sm) {
      ED.sel = sm[1].split(',').filter(function (id) { return byId(id); });
      drawOverlay(); refreshAll();
      setStatus('自检：已预选中 ' + ED.sel.length + ' 个元素');
    }
    // 自检钩子：?all=1 选中全部实体元素（看整体边界）
    if (/[?&]all=1/.test(location.search || '')) {
      ED.sel = ED.els.filter(function (e) { return e.kind !== 'hit'; }).map(function (e) { return e.id; });
      drawOverlay(); refreshAll();
      setStatus('自检：已选中全部 ' + ED.sel.length + ' 个实体元素');
    }
    // 自检钩子：?grid=<步长> 直接开网格（无头截图验收用）
    var gm = /[?&]grid=([0-9]+)/.exec(location.search || '');
    if (gm) {
      ED.grid = true; ED.gridStep = Number(gm[1]) || 20;
      var gsel = document.getElementById('ed-grid-step');
      if (gsel) gsel.value = String(ED.gridStep);
    }
    setTimeout(function () { syncOverlay(); drawGrid(); }, 60);
    setTimeout(function () { syncOverlay(); drawGrid(); }, 300);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
