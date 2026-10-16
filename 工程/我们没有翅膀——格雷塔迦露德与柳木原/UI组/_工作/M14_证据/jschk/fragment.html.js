
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

  function draw(e) {
    if (!e || e.visible_default === false) return null;
    var d;
    if (e.kind === 'rect') {
      d = mk('div', 'ui-el ui-rect', { background: col(e.color) || 'transparent', opacity: opa(e.opacity) });
      box(d, e);
    } else if (e.kind === 'image') {
      d = mk('div', 'ui-el');
      box(d, e);
      if (e.nine) { var n = mk('div', 'ui-nine'); nine(n, e); d.appendChild(n); }
      else { var im = mk('img', 'ui-image-img'); im.src = assetUrl(e.asset); im.alt = e.asset; d.appendChild(im); }
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

  function render(screenId) {
    var sc = L.screens[screenId];
    if (!sc) return null;
    C.innerHTML = '';
    sc.elements.slice().sort(function (a, b) { return (a.z || 0) - (b.z || 0); }).forEach(function (e) {
      var d = draw(e);
      if (d) { d.style.zIndex = String((e.z || 0) * 100 + 1); C.appendChild(d); }
    });
    return sc;
  }

  function q(elId) { return C.querySelector('[data-el="' + elId + '"]'); }
  function setText(elId, s) { var d = q(elId); if (!d) return; var inner = d.querySelector('.ui-text-inner') || d; inner.textContent = s; }

  var stage = document.getElementById('stage');
  function setScale(s) {
    C.style.transform = 'scale(' + s + ')';
    stage.style.width = px(Math.round(W * s));
    stage.style.height = px(Math.round(H * s));
  }
  function fitScale() {
    var s = Math.min((window.innerWidth - 40) / W, (window.innerHeight - 240) / H, 1);
    if (s < 0.2) s = 0.2;
    setScale(s);
  }
  document.getElementById('btn-1to1').onclick = function () { setScale(1); };
  document.getElementById('btn-fit').onclick = function () { fitScale(); };
  window.addEventListener('resize', fitScale);
  fitScale();

  /* ==========================================================================
     番外（Fragment）运行期状态（与 krkr 侧 ui_fragment.tjs 同规则）
       · 格 id = "c0".."c39"（5 列 × 8 行，行优先），与 layout 的
         fragment.cN_hit / fragment.cN_title 一一对应
       · collected：已收集集合（krkr 侧持久化到 ui_flow_state.txt）
       · 进入 = 只更新进度，**不跳转剧情**
     ========================================================================== */
  var FG = D.fragments;
  var CELLS = (FG.cells || []).map(function (c, i) { return { id: 'c' + i, info: c }; });
  var COLS = 5;
  var collected = {}, collectedList = [];
  var cursor = CELLS.length ? CELLS[0].id : '';

  /* 演示占位（非剧情进度）：与 krkr 侧 UIFragDemoSeedCell 对应 */
  var DEMO_SEED = 'c0';
  if (DEMO_SEED) { collected[DEMO_SEED] = true; collectedList.push(DEMO_SEED); }

  var toastTimer = null;
  function toast(msg) {
    var t = C.querySelector('.ui-toast');
    if (!t) { t = mk('div', 'ui-toast'); C.appendChild(t); }
    t.textContent = msg; t.style.zIndex = '999999';
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 3200);
  }

  function cellIdx(id) {
    for (var i = 0; i < CELLS.length; i++) if (CELLS[i].id === id) return i;
    return -1;
  }
  function cellText(id) {
    var i = cellIdx(id);
    if (i < 0) return id;
    return '第 ' + (i + 1) + ' 格「' + CELLS[i].info.title_cn + '」';
  }
  function hitEl(id) { return q('fragment.' + id + '_hit'); }

  /* 已收集环 / 选中框：与 krkr 侧 uiFlowFrame 同口径 */
  function frame(cls, el, pad, colorKey, thick) {
    var d = mk('div', cls);
    d.style.left = px(el.x - pad); d.style.top = px(el.y - pad);
    d.style.width = px(el.w + pad * 2); d.style.height = px(el.h + pad * 2);
    d.style.borderWidth = px(thick); d.style.borderColor = col('@palette.' + colorKey);
    d.style.zIndex = '9000';
    C.appendChild(d);
    return d;
  }

  var SC = L.screens.fragment;
  function layoutEl(id) {
    for (var i = 0; i < SC.elements.length; i++) if (SC.elements[i].id === id) return SC.elements[i];
    return null;
  }

  function paint() {
    /* ① 标题颜色按收集态 */
    CELLS.forEach(function (c) {
      var t = q('fragment.' + c.id + '_title');
      if (!t) return;
      var inner = t.querySelector('.ui-text-inner');
      if (inner) inner.style.color = col(collected[c.id] ? '@palette.highlight' : '@palette.text_disabled');
    });
    /* ② 已收集环 + 选中框（重画） */
    var olds = C.querySelectorAll('.ui-cell-ring, .ui-cell-cur');
    for (var i = 0; i < olds.length; i++) olds[i].parentNode.removeChild(olds[i]);
    CELLS.forEach(function (c) {
      var el = layoutEl('fragment.' + c.id + '_hit');
      if (!el) return;
      if (collected[c.id]) frame('ui-cell-ring', el, 0, 'node_available', 3);
      if (c.id === cursor) frame('ui-cell-cur', el, 4, 'node_current', 3);
    });
    /* ③ 计数行 */
    setText('fragment.count',
      '已收集 ' + collectedList.length + ' / ' + CELLS.length + '（本期上屏）｜ 番外总 '
      + FG.total + ' 条 / ' + FG.group_count + ' 组（余 ' + (FG.total - CELLS.length) + ' 条呈现方式待定）');
  }

  function enter() {
    var id = cursor;
    if (!id) return;
    var first = !collected[id];
    if (first) { collected[id] = true; collectedList.push(id); }
    paint();
    toast('进入番外 ' + cellText(id) + (first ? '（首次进入，已记录进度）' : '（重入）')
      + ' —— 只更新进度，不跳转剧情（跳转属编程组）');
  }

  function toggle() {
    if (!cursor) return;
    if (collected[cursor]) {
      delete collected[cursor];
      collectedList = collectedList.filter(function (c) { return c !== cursor; });
    } else { collected[cursor] = true; collectedList.push(cursor); }
    paint();
    toast('演示：' + cursor + ' 收集态 → ' + (collected[cursor] ? '已收集' : '未解锁'));
  }

  var sc = render('fragment');
  if (!sc) { C.innerHTML = '<div class="ui-toast">layout 中缺少 fragment 屏</div>'; }
  else {
    /* 40 个格子热区：点击 → 选中 + 进入 */
    CELLS.forEach(function (c) {
      var d = hitEl(c.id);
      if (!d) return;
      d.addEventListener('click', function (ev) { ev.stopPropagation(); cursor = c.id; enter(); });
    });
    var hb = q('fragment.hit_back');
    if (hb) hb.addEventListener('click', function (ev) { ev.stopPropagation(); toast('返回（krkr 侧为 M2 界面栈的 close 动作）'); });
    document.getElementById('btn-toggle').onclick = toggle;
    window.addEventListener('keydown', function (ev) {
      var i = cellIdx(cursor);
      if (i < 0) i = 0;
      var colIdx = i % COLS;
      if (ev.key === 'ArrowRight') { cursor = CELLS[colIdx === COLS - 1 ? i - COLS + 1 : i + 1].id; paint(); ev.preventDefault(); }
      else if (ev.key === 'ArrowLeft') { cursor = CELLS[colIdx === 0 ? i + COLS - 1 : i - 1].id; paint(); ev.preventDefault(); }
      else if (ev.key === 'ArrowDown') { cursor = CELLS[(i + COLS) % CELLS.length].id; paint(); ev.preventDefault(); }
      else if (ev.key === 'ArrowUp') { cursor = CELLS[(i - COLS + CELLS.length) % CELLS.length].id; paint(); ev.preventDefault(); }
      else if (ev.key === 'Enter') { enter(); ev.preventDefault(); }
    });
    paint();
  }

  var cn = document.getElementById('canvas-note');
  if (cn) cn.textContent = W + '×' + H;
  var sn = document.getElementById('src-note'); if (sn) sn.textContent = ASSET;
})();
