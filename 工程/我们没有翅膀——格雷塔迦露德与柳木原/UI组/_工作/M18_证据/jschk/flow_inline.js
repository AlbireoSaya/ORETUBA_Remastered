
/* ============================================================================
   通用数据驱动渲染器（与 M3 replica.js 同口径；本页用到 rect/image/text/hit）
   ★ 本脚本不含任何来自 layout 的坐标 / 尺寸 / 字号 / 颜色字面量。
   ========================================================================== */
(function () {
  var L = window.UI_LAYOUT, D = window.UI_FLOW_DATA;
  var PAL = (L && L.palette) || {};
  var ASSET = '../' + String((L && L.asset_root) || 'krkr/assets/ui/');
  var SIZES = (L && L.fonts && L.fonts.sizes) || {};
  var LSP = (L && L.fonts && L.fonts.line_spacing) || {};
  var FACES = (L && L.fonts && L.fonts.fallback_faces) || [];
  var W = (L && L.canvas && L.canvas.width) || 1920;
  var H = (L && L.canvas && L.canvas.height) || 1080;
  /* M18：单屏总览 —— 与 krkr 侧 ui_flow.tjs 的 UIFlowMarkerPad / UIFlowCursorPad 对齐
     （色环外扩 3 + 标记 1 = 最外沿 4 px；行距 120 − 行槽 112 − 色环 3 = 5 px 余量） */
  var MARK_PAD = 4, MARK_THICK = 2, CURSOR_THICK = 1;

  document.documentElement.style.setProperty('--font-chain',
    FACES.map(function (f) { return '"' + f + '"'; }).concat(['sans-serif']).join(','));

  function col(v) {
    if (v === null || v === undefined) return null;
    var s = String(v);
    if (s.charAt(0) === '@') {
      var k = s.replace(/^@/, '').replace(/^palette\./, '');
      return (PAL[k] !== undefined && PAL[k] !== null) ? String(PAL[k]) : null;
    }
    return s;
  }
  function opa(v) {
    if (v === null || v === undefined) return 1;
    var n = Number(v); if (isNaN(n)) return 1;
    if (n < 0) n = 0; if (n > 255) n = 255;
    return n / 255;
  }
  function assetUrl(a) { return ASSET + String(a).replace(/^ui\//, ''); }
  function fontSize(f) {
    if (f && f.size !== null && f.size !== undefined) return Number(f.size);
    return Number(SIZES.body || 24);
  }
  function lineSp(e) {
    if (e.line_spacing !== null && e.line_spacing !== undefined) return Number(e.line_spacing);
    return Number(LSP.body || 1.4);
  }
  function px(v) { return v + 'px'; }
  function mk(tag, cls, st) {
    var d = document.createElement(tag);
    if (cls) d.className = cls;
    if (st) for (var k in st) d.style[k] = st[k];
    return d;
  }
  function box(d, e) {
    if (e.x !== undefined) d.style.left = px(e.x);
    if (e.y !== undefined) d.style.top = px(e.y);
    if (e.w !== undefined) d.style.width = px(e.w);
    if (e.h !== undefined) d.style.height = px(e.h);
  }
  function nine(d, e) {
    d.style.borderImageSource = 'url("' + assetUrl(e.asset) + '")';
    d.style.borderImageSlice = [e.nine.t, e.nine.r, e.nine.b, e.nine.l].join(' ');
    d.style.borderImageRepeat = 'stretch';
    d.style.borderWidth = [e.nine.t, e.nine.r, e.nine.b, e.nine.l].map(px).join(' ');
  }

  var C = document.getElementById('canvas');
  C.style.width = px(W); C.style.height = px(H);

  /* ---------------- 单元素渲染 ---------------- */
  function draw(e) {
    if (!e || e.visible_default === false) return null;
    var d;
    if (e.kind === 'rect') {
      d = mk('div', 'ui-el ui-rect', { background: col(e.color) || 'transparent', opacity: opa(e.opacity) });
      box(d, e);
    } else if (e.kind === 'image') {
      d = mk('div', 'ui-el');
      box(d, e);
      /* ★ M18：`nine:{l:0,t:0,r:0,b:0}` = 「允许整图等比缩放」（_schema.md §六）。
         HTML 侧**不能**用 border-image 表达它 —— border-width 全为 0 时 border-image
         不绘制任何像素（方框会整块消失）。故全零 nine 走普通 <img>：CSS 的
         `.ui-image-img{width:100%;height:100%}` 正是「整图拉伸到目标矩形」，
         与 krkr 侧 uiWidgetNine 在 l=t=r=b=0 时只画中格（operateStretch 整图）等价。
         非全零 nine 仍走 border-image（与 M3/M14 口径一致）。 */
      if (e.nine && (e.nine.l || e.nine.t || e.nine.r || e.nine.b)) {
        var n = mk('div', 'ui-nine'); nine(n, e); d.appendChild(n);
      } else {
        var im = mk('img', 'ui-image-img'); im.src = assetUrl(e.asset); im.alt = e.asset; d.appendChild(im);
      }
      if (e.opacity !== undefined) d.style.opacity = opa(e.opacity);
    } else if (e.kind === 'text') {
      d = mk('div', 'ui-el ui-text');
      box(d, e);
      var f = e.font || {};
      var inner = mk('div', 'ui-text-inner', {
        fontSize: px(fontSize(f)),
        lineHeight: String(lineSp(e)),
        color: col(f.color) || '#ffffff',
        textAlign: e.align || 'left',
        fontWeight: f.bold ? '700' : '400'
      });
      if (f.shadow) {
        var o = (f.shadow_ofs === undefined) ? 0 : Number(f.shadow_ofs);
        inner.style.textShadow = px(o) + ' ' + px(o) + ' 0 ' + (col(f.shadow_color) || '#000');
      }
      var va = e.valign || 'top';
      d.style.alignItems = (va === 'middle') ? 'center' : ((va === 'bottom') ? 'flex-end' : 'flex-start');
      if (e.wrap === true && e.max_lines > 0) {
        inner.style.display = '-webkit-box';
        inner.style.webkitLineClamp = String(e.max_lines);
        inner.style.webkitBoxOrient = 'vertical';
        inner.style.overflow = 'hidden';
      }
      inner.textContent = String(e.sample === undefined ? '' : e.sample);
      d.appendChild(inner);
    } else if (e.kind === 'hit') {
      d = mk('div', 'ui-el ui-hit');
      box(d, e);
      if (e.label) {
        var fh = e.font || {};
        var lab = mk('div', 'ui-hit-label', {
          fontSize: px(fontSize(fh)), color: col(fh.color) || '#e8e8f0',
          fontWeight: fh.bold ? '700' : '400'
        });
        lab.textContent = String(e.label);
        d.appendChild(lab);
      }
    } else if (e.kind === 'list') {
      return null;      /* 本屏 M14 起无 list 元素 */
    } else { return null; }
    d.setAttribute('data-el', e.id);
    return d;
  }

  function render(screenId, skipIds) {
    var sc = L.screens[screenId];
    if (!sc) return null;
    C.innerHTML = '';
    var els = sc.elements.slice().sort(function (a, b) { return (a.z || 0) - (b.z || 0); });
    els.forEach(function (e) {
      if (skipIds && skipIds[e.id]) return;
      var d = draw(e);
      if (d) { d.style.zIndex = String((e.z || 0) * 100 + 1); C.appendChild(d); }
    });
    return sc;
  }

  function q(elId) { return C.querySelector('[data-el="' + elId + '"]'); }
  function setText(elId, s) {
    var d = q(elId); if (!d) return;
    var inner = d.querySelector('.ui-text-inner') || d;
    inner.textContent = s;
  }
  function setRectColor(elId, key) {
    var d = q(elId); if (d) d.style.background = col('@palette.' + key) || d.style.background;
  }

  /* ---------------- 缩放 ---------------- */
  var stage = document.getElementById('stage');
  function setScale(s) {
    C.style.transform = 'scale(' + s + ')';
    stage.style.width = px(Math.round(W * s));
    stage.style.height = px(Math.round(H * s));
  }
  function fitScale() {
    var availW = window.innerWidth - 40;
    var availH = window.innerHeight - 240;
    var s = Math.min(availW / W, availH / H, 1);
    if (s < 0.2) s = 0.2;
    setScale(s);
  }
  document.getElementById('btn-1to1').onclick = function () { setScale(1); };
  document.getElementById('btn-fit').onclick = function () { fitScale(); };
  window.addEventListener('resize', fitScale);
  fitScale();

  /* ==========================================================================
     流程图运行期状态（与 krkr 侧 ui_flow.tjs 同规则）
       已读 visited ＞ 可前往 available ＞ 未解锁 locked
       available = 无入边（根节点）或任一入边的源节点已读
       连线：源与目标均已读=已读 / 源已读=可通行 / 源未读=未解锁
       总线：任一源节点已读=可通行
     ★ M18：单屏总览，无滚动 —— 屏上元素一律按 layout 的原始坐标绘制。
     ========================================================================== */
  var NODE = {}, IN = {}, EDGE = {}, BUS = {}, NODE_ORDER = [], EL2EDGE = {};
  D.nodes.forEach(function (n) { NODE[n.id] = n; NODE_ORDER.push(n.id); });
  D.edges.forEach(function (e) {
    EDGE[e.id] = e;
    (IN[e.to] = IN[e.to] || []).push(e);
    (e.els || []).forEach(function (x) { EL2EDGE[x] = e; });
  });
  D.buses.forEach(function (b) { if (b.el) { BUS[b.el] = b; EL2EDGE[b.el] = b; } });

  var SC = L.screens.flowchart;
  function layoutEl(id) {
    for (var i = 0; i < SC.elements.length; i++) if (SC.elements[i].id === id) return SC.elements[i];
    return null;
  }
  /* 阅读顺序：M18 网格是列优先填充，故按 (grid_col, grid_row) 排序；
     缺少该字段时回落到 layout 里的 y。二者在本屏结果一致（列优先 = 自上而下）。 */
  NODE_ORDER.sort(function (a, b) {
    var na = NODE[a], nb = NODE[b];
    if (na.grid_col !== undefined && nb.grid_col !== undefined) {
      if (na.grid_col !== nb.grid_col) return na.grid_col - nb.grid_col;
      return na.grid_row - nb.grid_row;
    }
    var ea = layoutEl(na.el + '_box'), eb = layoutEl(nb.el + '_box');
    return ((ea && ea.y) || 0) - ((eb && eb.y) || 0);
  });

  var visited = {}, current = '', cursor = '';

  function stateOf(id) {
    if (visited[id]) return 'visited';
    var ins = IN[id];
    if (!ins || !ins.length) return 'available';
    for (var i = 0; i < ins.length; i++) if (visited[ins[i].from]) return 'available';
    return 'locked';
  }
  function keyOf(st) { return st === 'visited' ? 'node_visited' : (st === 'available' ? 'node_available' : 'node_locked'); }
  function edgeKey(e) {
    var f = !!visited[e.from], t = !!visited[e.to];
    if (f && t) return 'node_visited';
    if (f) return 'node_available';
    return 'node_locked';
  }
  function busKey(b) {
    for (var i = 0; i < (b.sources || []).length; i++) if (visited[b.sources[i]]) return 'node_available';
    return 'node_locked';
  }
  function hint(id) {
    var ins = IN[id];
    if (!ins || !ins.length) return '无条件（起始节点）';
    return ins.map(function (e) { return '先到达 ' + e.from; }).join(' 或 ');
  }
  function visitedCount() { var n = 0; for (var k in visited) if (visited[k]) n++; return n; }

  var toastTimer = null;
  function toast(msg) {
    var t = C.querySelector('.ui-toast');
    if (!t) { t = mk('div', 'ui-toast'); C.appendChild(t); }
    t.textContent = msg;
    t.style.zIndex = '999999';
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 3200);
  }

  function frame(cls, r, pad, color, thick) {
    var d = mk('div', cls);
    d.style.left = px(r.x - pad); d.style.top = px(r.y - pad);
    d.style.width = px(r.w + pad * 2); d.style.height = px(r.h + pad * 2);
    d.style.borderWidth = px(thick); d.style.borderColor = col('@palette.' + color);
    d.style.zIndex = '9000';
    C.appendChild(d);
    return d;
  }
  /* 节点方框的矩形（M18：单屏无滚动，直接用 layout 坐标） */
  function boxRect(n) {
    var e = layoutEl(n.el + '_box');
    if (!e) return null;
    return { x: e.x, y: e.y, w: e.w, h: e.h };
  }

  function paint() {
    /* ① 节点三态：色环（_fill）色值 + 标签颜色 */
    D.nodes.forEach(function (n) {
      var st = stateOf(n.id);
      setRectColor(n.el + '_fill', keyOf(st));
      var lab = q(n.el + '_label');
      if (lab) {
        var inner = lab.querySelector('.ui-text-inner');
        /* ★ M18：标签色一律 @palette.node_locked —— 与 krkr 侧 ui_flow.tjs 同规则。
           实测对比度（WCAG）：node_locked 在四种方框上 6.02…6.15（AA 达标）；
           M14 未解锁用的 text_disabled 只有 1.49（重要章节饱和蓝框）…2.38（不达标）。
           三态信息由色环（_fill）承担，见下方 setRectColor。 */
        if (inner) inner.style.color = col('@palette.node_locked');
      }
    });
    /* ② 连线 / 总线三态 */
    Object.keys(EL2EDGE).forEach(function (elId) {
      var x = EL2EDGE[elId];
      if (!x) return;
      var key = x.sources ? busKey(x) : edgeKey(x);
      setRectColor(elId, key);
    });
    /* ③ 当前节点 / 选中框 */
    var olds = C.querySelectorAll('.ui-node-current, .ui-node-cursor');
    for (var i = 0; i < olds.length; i++) olds[i].parentNode.removeChild(olds[i]);
    var curNode = NODE[current], curRect = curNode ? boxRect(curNode) : null;
    if (curRect) frame('ui-node-current', curRect, MARK_PAD, 'node_current', MARK_THICK);
    var cn = NODE[cursor];
    if (cn && cursor !== current) {
      var kRect = boxRect(cn);
      if (kRect) frame('ui-node-cursor', kRect, MARK_PAD, 'accent', CURSOR_THICK);
    }
    /* ④ 详情行 */
    var s = '当前节点：' + current + ' ' + (NODE[current] ? NODE[current].label : '')
      + '\n已读 ' + visitedCount() + ' / ' + D.nodes.length + ' 节点'
      + '\n点击节点或按 Enter 前往；未解锁节点会给出解锁条件';
    setText('flow.detail', s);
  }

  function select(id) {
    cursor = id;
    var st = stateOf(id);
    if (st === 'locked') { paint(); toast('【未解锁】' + id + ' ' + NODE[id].label + '：' + hint(id)); return; }
    visited[id] = true;
    current = id;
    paint();
    toast('前往 ' + id + ' ' + NODE[id].label + (st === 'visited' ? '（已读节点）' : '（新解锁）')
      + '　已读 ' + visitedCount() + ' / ' + D.nodes.length);
  }

  function reset() {
    visited = {}; current = ''; cursor = '';
    for (var i = 0; i < NODE_ORDER.length; i++) {
      var id = NODE_ORDER[i];
      if (!IN[id] || !IN[id].length) { current = id; break; }
    }
    if (!current) current = NODE_ORDER[0];
    visited[current] = true; cursor = current;
    paint();
    toast('进度已重置：起始节点 ' + current);
  }

  /* ---------------- 渲染 + 事件 ---------------- */
  var sc = render('flowchart');
  if (!sc) { C.innerHTML = '<div class="ui-toast">layout 中缺少 flowchart 屏</div>'; }
  else {
    /* 节点热区 / 节点方框图 / 标签 / 色环 均可点；返回键 */
    C.querySelectorAll('.ui-hit').forEach(function (d) {
      var id = d.getAttribute('data-el');
      d.addEventListener('click', function (ev) {
        ev.stopPropagation();
        if (id && id.indexOf('flow_node_') === 0) { select(id.substring('flow_node_'.length)); return; }
        if (id === 'flow.hit_back') { toast('返回（krkr 侧为 M2 界面栈的 close 动作，弹回上一屏）'); return; }
      });
    });
    D.nodes.forEach(function (n) {
      [n.el + '_box', n.el + '_label', n.el + '_fill'].forEach(function (eid) {
        var d = q(eid);
        if (d) { d.classList.add('ui-node'); d.addEventListener('click', function (ev) { ev.stopPropagation(); select(n.id); }); }
      });
    });
    document.getElementById('btn-reset').onclick = reset;
    window.addEventListener('keydown', function (ev) {
      /* M18：阅读顺序 = 网格的列优先顺序（= FLOW_ORDER），故前后移动即按该顺序走 */
      if (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') {
        var i = NODE_ORDER.indexOf(cursor); cursor = NODE_ORDER[(i + 1 + NODE_ORDER.length) % NODE_ORDER.length];
        paint(); ev.preventDefault();
      } else if (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') {
        var j = NODE_ORDER.indexOf(cursor); cursor = NODE_ORDER[(j - 1 + NODE_ORDER.length) % NODE_ORDER.length];
        paint(); ev.preventDefault();
      } else if (ev.key === 'Enter') { select(cursor); ev.preventDefault(); }
    });
    reset();
  }

  /* 图例色块说明文字 */
  var lv = document.getElementById('lg-v'), la = document.getElementById('lg-a'), ll = document.getElementById('lg-l');
  if (lv) lv.style.color = col('@palette.node_visited');
  if (la) la.style.color = col('@palette.node_available');
  if (ll) ll.style.color = col('@palette.node_locked');
  var cn2 = document.getElementById('canvas-note'); if (cn2) cn2.textContent = W + '×' + H;
  var sn = document.getElementById('src-note'); if (sn) sn.textContent = ASSET;
})();
