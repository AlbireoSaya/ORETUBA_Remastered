/* ==========================================================================
   editor_ui.js —— 编辑器界面层（M35）
   屏选择 / 素材资料库 / 元素树 / 属性面板 / 即时校验 / 导出 / 快捷键 / 工具按钮
   依赖：editor_core.js（window.UI_EDITOR）
   ========================================================================== */
(function () {
  'use strict';
  var E = window.UI_EDITOR;
  if (!E) { console.error('editor_ui.js：需要先加载 editor_core.js'); return; }

  var ED = E.ED, L = window.UI_LAYOUT, AIX = window.UI_ASSET_INDEX;
  var $ = function (id) { return document.getElementById(id); };
  var esc = E.esc, num = E.num;

  /* ══════════════════════════════ 屏选择 ══════════════════════════════ */
  function buildScreenSel() {
    var sel = $('ed-screen-sel');
    if (!sel) return;
    var list = (window.UI_SCREEN_INDEX || []).map(function (x) { return x.id; });
    if (!list.length) list = Object.keys(L.screens);
    sel.innerHTML = list.map(function (sid) {
      var sc = L.screens[sid];
      return '<option value="' + sid + '">' + esc(sc.title_cn || sid) + '（' + sid + '）</option>';
    }).join('');
    sel.value = ED.sid;
    sel.onchange = function () {
      if (!confirmChange()) { sel.value = ED.sid; return; }
      E.loadScreen(sel.value);
      syncToolbar();
    };
  }
  function confirmChange() {
    if (!ED.undo.length) return true;
    return confirm('当前屏有未导出的改动（' + ED.undo.length + ' 步）。确定切换并丢弃？');
  }

  /* ══════════════════════ 屏级 flag 预览（★ M3） ══════════════════════
     操作栏的「按 flag 预览」开关 + 该屏 flags_default 里每个 flag 的下拉。
     · 默认关闭 ⇒ 忽略 flag（全部元素可见可编辑，等价于改动前的编辑体验）；
     · 开启 ⇒ 按所选取值套用可见性过滤（渲染与命中/选中/点选口径一并跟着走，
       见 editor_core.js 的 isVisible / applyFlagsMode）。
     取值候选 = 该屏（含屏级 attach 附加层）元素里实际出现过的 vis_when（含空串）。 */
  function buildFlagBar() {
    var host = $('ed-flag-sels');
    var btn = $('ed-flag-preview');
    if (btn) {
      btn.textContent = '按 flag 预览：' + (ED.flagPreview ? '开' : '关');
      btn.className = 'ed-btn' + (ED.flagPreview ? ' on' : '');
    }
    if (!host) return;
    var names = E.flagNamesOfScreen(ED.sid);
    if (!names.length) {
      host.innerHTML = '<span style="color:#6b8098;font-size:12px">该屏无 flag</span>';
      return;
    }
    host.innerHTML = names.map(function (n) {
      var vals = E.flagValuesOfScreen(ED.sid, n);
      var cur = ED.flagVals[n];
      if (cur === null || cur === undefined) cur = '';
      var opts = vals.map(function (v) {
        return '<option value="' + esc(v) + '"' + (String(cur) === v ? ' selected' : '') + '>'
          + (v === '' ? '（空）' : esc(v)) + '</option>';
      }).join('');
      return '<span style="font-size:12px;color:#8d9aad">' + esc(n) + '</span>'
        + '<select class="ed-sel" data-flag="' + esc(n) + '">' + opts + '</select>';
    }).join('');
    host.onchange = function (ev) {
      var sel = ev.target;
      if (!sel || !sel.getAttribute) return;
      var fn = sel.getAttribute('data-flag');
      if (!fn) return;
      /* ★ M47：一律走 `E.setFlagValue`（不要直接写 ED.flagVals）—— 改 `cfg_page` 时它会在
         重渲染前跑一次机制侧的切页派生并回读，预览条再用派生后的值重建（非本页的值键显示
         「（空）」，本页显示真实值）。直接写 flagVals 会绕过派生，把「另一页的值元素仍显示」
         这个中间态又摆回来（与产品分叉）。改其它 flag 不触发派生，可做单项探查。 */
      E.setFlagValue(fn, sel.value);
      E.setStatus('flag 预览：' + fn + ' = ' + (sel.value === '' ? '（空）' : sel.value)
        + (ED.flagPreview ? '' : '（开关当前为「关」，先点「按 flag 预览」才生效）'));
    };
  }

  /* ══════════════════════════════ 素材资料库 ══════════════════════════ */
  var LIB = { cat: '全部', q: '', shown: 60, STEP: 60 };
  function buildLibCats() {
    var box = $('ed-lib-cats');
    if (!box || !AIX) return;
    var cats = ['全部'].concat(Object.keys(AIX.groups));
    box.innerHTML = cats.map(function (c) {
      var n = c === '全部' ? AIX.count : AIX.groups[c].length;
      return '<button data-cat="' + esc(c) + '" class="' + (c === LIB.cat ? 'on' : '') + '">'
        + esc(c) + ' ' + n + '</button>';
    }).join('');
    box.onclick = function (ev) {
      var b = ev.target.closest && ev.target.closest('button[data-cat]');
      if (!b) return;
      LIB.cat = b.getAttribute('data-cat'); LIB.shown = LIB.STEP;
      buildLibCats(); renderLib();
    };
  }
  function libItems() {
    if (!AIX) return [];
    var arr = LIB.cat === '全部' ? AIX.items
      : AIX.items.filter(function (i) { return i.g === LIB.cat; });
    var q = LIB.q.trim().toLowerCase();
    if (q) arr = arr.filter(function (i) { return i.n.toLowerCase().indexOf(q) >= 0; });
    return arr;
  }
  function renderLib() {
    var grid = $('ed-lib-grid'), more = $('ed-lib-more');
    if (!grid) return;
    if (!AIX) { grid.innerHTML = ''; if (more) more.textContent = '未找到 asset_index.js（先跑 工具\\emit_asset_index.py）'; return; }
    var arr = libItems(), head = arr.slice(0, LIB.shown);
    grid.innerHTML = head.map(function (i) {
      return '<div class="ed-lib-item" data-n="' + esc(i.n) + '" title="' + esc(i.n) + '  ' + i.w + '×' + i.h + '">'
        + '<img loading="lazy" src="../krkr/assets/ui/' + encodeURIComponent(i.n) + '" alt="">'
        + '<div class="nm">' + esc(i.n.replace(/^x_(ui|gen|mask|title|bg)_/, '')) + '</div>'
        + '<div class="sz">' + i.w + '×' + i.h + '</div></div>';
    }).join('');
    if (more) more.textContent = arr.length > head.length
      ? '还有 ' + (arr.length - head.length) + ' 件 —— 点此再显示 ' + LIB.STEP + ' 件'
      : '共 ' + arr.length + ' 件';
  }
  /* ---------------------------------------------------------- 热重载
     不刷新页面重新读取 `asset_index.js`：动态注入 <script src="asset_index.js?t=…">，
     加载完成后 `window.UI_ASSET_INDEX` 已被整体替换 → 重建分类与网格。
     （`file://` 下 fetch 被 CORS 挡死，但动态 script 注入是允许的。） */
  function reloadLib(silent) {
    var btn = $('ed-lib-reload');
    if (btn) { btn.disabled = true; btn.textContent = '↻ 读取中…'; }
    var sc = document.createElement('script');
    sc.src = 'asset_index.js?t=' + Date.now();
    sc.onload = function () {
      AIX = window.UI_ASSET_INDEX;
      LIB.shown = LIB.STEP;
      buildLibCats(); renderLib(); syncLibStat();
      if (btn) { btn.disabled = false; btn.textContent = '↻ 热重载'; }
      if (!silent) E.setStatus('素材库已热重载：' + (AIX ? AIX.count : 0) + ' 件 / '
        + (AIX ? Object.keys(AIX.groups).length : 0) + ' 组');
    };
    sc.onerror = function () {
      if (btn) { btn.disabled = false; btn.textContent = '↻ 热重载'; }
      if (!silent) E.setStatus('热重载失败：读不到 asset_index.js（先跑 工具\emit_asset_index.py）', 'bad');
    };
    document.head.appendChild(sc);
  }

  function syncLibStat() {
    var el = $('ed-lib-stat');
    if (!el) return;
    if (!AIX) { el.textContent = '（未加载索引）'; return; }
    el.textContent = AIX.count + ' 件 · ' + Object.keys(AIX.groups).length + ' 组 · '
      + (AIX.generated || '');
  }

  function setupLib() {
    var btn = $('ed-lib-reload');
    if (btn) btn.onclick = function () { reloadLib(false); };
    var s = $('ed-lib-search');
    if (s) s.oninput = function () { LIB.q = s.value; LIB.shown = LIB.STEP; renderLib(); };
    var more = $('ed-lib-more');
    if (more) more.onclick = function () { LIB.shown += LIB.STEP; renderLib(); };
    var grid = $('ed-lib-grid');
    if (grid) grid.onclick = function (ev) {
      var it = ev.target.closest && ev.target.closest('.ed-lib-item');
      if (!it) return;
      addImageAsset(it.getAttribute('data-n'));
    };
  }

  /* 在画布中心新增一个 image 元素（w/h = PNG 实尺寸 → 满足 verify_ui 检查 [2]） */
  function addImageAsset(name) {
    var meta = null;
    for (var i = 0; i < AIX.items.length; i++) if (AIX.items[i].n === name) { meta = AIX.items[i]; break; }
    if (!meta) { E.setStatus('资料库索引里没有 ' + name, 'bad'); return; }
    E.snapshot('add ' + name);
    var base = name.replace(/\.png$/i, '').replace(/[^A-Za-z0-9_\-]/g, '_');
    var id = 'new.' + base;
    var k = 2; while (E.byId(id)) { id = 'new.' + base + '_' + (k++); }
    var zmax = 0;
    for (var j = 0; j < ED.els.length; j++) zmax = Math.max(zmax, ED.els[j].z || 0);
    ED.els.push({
      id: id, kind: 'image', z: zmax + 1, visible_default: true,
      asset: 'ui/' + name,
      x: Math.round((E.CW - meta.w) / 2), y: Math.round((E.CH - meta.h) / 2),
      w: meta.w, h: meta.h, opacity: 255,
      source: '编辑器资料库新增（' + name + '）',
      note: '★ 由 UI 布局编辑器（M35）新增。w/h 取 PNG 实尺寸 ' + meta.w + '×' + meta.h + '。'
    });
    ED.sel = [id];
    E.reRender(); E.refreshAll();
    E.setStatus('已新增 ' + name + '（' + meta.w + '×' + meta.h + '）');
  }

  /* ══════════════════════════════ 元素树 ══════════════════════════════ */
  function renderTree() {
    var box = $('ed-el-list');
    if (!box) return;
    var arr = ED.els.slice().sort(function (a, b) { return (b.z || 0) - (a.z || 0); });
    box.innerHTML = arr.map(function (e) {
      var on = ED.sel.indexOf(e.id) >= 0 ? ' on' : '';
      var vis = E.isVisible(e) ? '' : ' style="opacity:.45"';
      return '<div class="ed-el-item' + on + '"' + vis + ' data-id="' + esc(e.id) + '">'
        + '<span class="k">z' + (e.z || 0) + '</span>'
        + '<span class="k">' + esc(e.kind) + '</span>'
        + '<span>' + esc(e.id) + '</span></div>';
    }).join('');
    box.onclick = function (ev) {
      var it = ev.target.closest && ev.target.closest('.ed-el-item');
      if (!it) return;
      var id = it.getAttribute('data-id');
      if (ev.shiftKey) { var k = ED.sel.indexOf(id); if (k >= 0) ED.sel.splice(k, 1); else ED.sel.push(id); }
      else ED.sel = [id];
      E.drawOverlay(); E.refreshProp(); renderTree();
    };
  }

  /* ══════════════════════════════ 属性面板 ══════════════════════════════ */
  function row(label, html) {
    return '<div class="ed-row"><label>' + esc(label) + '</label>' + html + '</div>';
  }
  function inp(path, value, type) {
    return '<input class="ed-num" data-p="' + esc(path) + '" type="' + (type || 'text') + '" value="'
      + esc(value == null ? '' : value) + '">';
  }

  function renderProp() {
    var box = $('ed-prop');
    if (!box) return;
    if (!ED.sel.length) { box.innerHTML = '<div class="ed-hint">未选中元素。</div>'; return; }
    if (ED.sel.length > 1) {
      box.innerHTML = '<div class="ed-hint">已选 ' + ED.sel.length + ' 个元素 —— 仅支持整体拖动 / 方向键微调。</div>';
      return;
    }
    var e = E.byId(ED.sel[0]);
    if (!e) { box.innerHTML = '<div class="ed-hint">元素已不存在。</div>'; return; }
    var h = [];
    h.push(row('id', '<input class="ed-num" data-p="id" value="' + esc(e.id) + '">'));
    h.push(row('kind', '<input class="ed-num" value="' + esc(e.kind) + '" disabled>'));
    h.push('<div class="ed-row wide"><label>z</label>' + inp('z', e.z, 'number')
      + '<label>不透明</label>' + inp('opacity', e.opacity == null ? 255 : e.opacity, 'number') + '</div>');
    h.push('<div class="ed-row wide"><label>x</label>' + inp('x', e.x, 'number')
      + '<label>y</label>' + inp('y', e.y, 'number') + '</div>');
    /* ★ M06：`list` 的 `h` 是**派生量**（数据里没有这个键）⇒ 面板**只读显示派生值**并标明公式，
       不再给一个「写进去也没人读」的可编辑输入框（冻结书 §5 的第二条要求）。 */
    var dH = !!(E.derivedH && E.derivedH(e));
    if (dH) {
      var spanH = E.listSpanH(e);
      var nLab = (e.labels && e.labels.length) ? e.labels.length : 0;
      var rowsN = (e.orientation === 'h')
        ? Math.max(1, Math.ceil(nLab / Math.max(1, num(e.max_cols) || nLab || 1)))
        : Math.max(1, Math.min(nLab, num(e.max_rows) || nLab || 1));
      h.push('<div class="ed-row wide"><label>w</label>' + inp('w', e.w, 'number')
        + '<label>h</label><input class="ed-num" value="' + spanH + '" disabled title="派生，只读"></div>');
      h.push('<div class="ed-hint">h <b>（派生，只读）</b> = 可见行数 ' + rowsN + ' × item_h '
        + num(e.item_h) + ' + (' + rowsN + '−1) × gap ' + num(e.gap) + ' = <b>' + spanH
        + '</b>（span 口径同 krkr <code>uiWidgetListSpan</code> 与 '
        + '<code>test_state_targets.py::rect_of</code>；'
        + '<b>未含</b> <code>stack_bottom</code> 与 <code>scroll.page_size</code> —— '
        + '带 <code>stack_bottom</code> 的 list 在引擎里会落到 <code>stack_bottom−h</code>，'
        + '本框仍按 <code>y</code> 画，属既有缺口）。'
        + '改行数请动 <code>labels</code> / <code>max_rows</code>，改行高请动 <code>item_h</code>。</div>');
    } else {
      h.push('<div class="ed-row wide"><label>w</label>' + inp('w', e.w, 'number')
        + '<label>h</label>' + inp('h', e.h, 'number') + '</div>');
    }
    h.push('<label class="ed-chk" style="margin:4px 0"><input type="checkbox" data-p="visible_default"'
      + (e.visible_default !== false ? ' checked' : '') + '> visible_default</label>');

    if (e.kind === 'image') {
      h.push(row('asset', inp('asset', e.asset)));
      var meta = assetMeta(e.asset);
      h.push('<div class="ed-hint">' + (meta
        ? 'PNG 实尺寸 ' + meta.w + '×' + meta.h + (e.nine ? '（有 nine，允许拉伸）'
          : (Math.round(num(e.w)) === meta.w && Math.round(num(e.h)) === meta.h
            ? ' ✓ 与版面一致' : ' ✗ 无 nine 时必须等于实尺寸'))
        : '资料库索引里查不到该素材') + '</div>');
      var n = e.nine || { l: 0, t: 0, r: 0, b: 0 };
      h.push('<div class="ed-row wide"><label>nine l</label>' + inp('nine.l', n.l, 'number')
        + '<label>t</label>' + inp('nine.t', n.t, 'number') + '</div>');
      h.push('<div class="ed-row wide"><label>r</label>' + inp('nine.r', n.r, 'number')
        + '<label>b</label>' + inp('nine.b', n.b, 'number') + '</div>');
      h.push('<div class="ed-multi" style="margin:4px 0 8px">'
        + '<button class="ed-btn" data-act="nine-fit">按实尺寸</button>'
        + '<button class="ed-btn" data-act="nine-zero">整图缩放</button>'
        + '<button class="ed-btn" data-act="nine-none">去掉 nine</button>'
        + '<button class="ed-btn" data-act="fit-rect">裁到实尺寸</button></div>');
    }
    if (e.kind === 'text') {
      var f = e.font || {};
      h.push('<div class="ed-row wide"><label>字号</label>' + inp('font.size', f.size, 'number')
        + '<label>行距</label>' + inp('line_spacing', e.line_spacing, 'number') + '</div>');
      h.push(row('颜色', inp('font.color', f.color)));
      h.push('<div class="ed-row wide"><label>对齐</label><select class="ed-sel" data-p="align">'
        + ['left', 'center', 'right'].map(function (v) { return '<option' + (e.align === v ? ' selected' : '') + '>' + v + '</option>'; }).join('')
        + '</select><label>垂直</label><select class="ed-sel" data-p="valign">'
        + ['top', 'middle', 'bottom'].map(function (v) { return '<option' + (e.valign === v ? ' selected' : '') + '>' + v + '</option>'; }).join('')
        + '</select></div>');
      h.push('<div class="ed-row wide"><label>折行</label><select class="ed-sel" data-p="wrap">'
        + ['false', 'true'].map(function (v) { return '<option value="' + v + '"' + (String(!!e.wrap) === v ? ' selected' : '') + '>' + v + '</option>'; }).join('')
        + '</select><label>最大行</label>' + inp('max_lines', e.max_lines, 'number') + '</div>');
      h.push(row('字体链', inp('font.faces_raw', (f.faces || []).join(', '))));
      h.push(row('粗体', '<label class="ed-chk"><input type="checkbox" data-p="font.bold"' + (f.bold ? ' checked' : '') + '> bold</label>'));
      h.push(row('样例', '<input class="ed-num" data-p="sample" value="' + esc(e.sample || '') + '">'));
    }
    if (e.kind === 'rect') {
      h.push(row('颜色', inp('color', e.color)));
    }
    if (e.kind === 'hit') {
      h.push(row('action', inp('action', e.action)));
      h.push(row('label', inp('label', e.label)));
      /* ★ M47：热区上的 `slider` 字段 —— 非空 = 本热区是**某滑块的拖动热区**
         （值写成 `<slider 元素 id>`，如 `cfg.sl_winopac`；字段名是接口冻结项）。
         机制侧据此在按下时绑定拖动、悬停时点亮该滑块的手柄（见 replica.js 的 buildHit）。 */
      h.push(row('slider', inp('slider', e.slider)));
      h.push('<div class="ed-hint">slider：填某 `kind:slider` 元素的 id ⇒ 本热区成为**它的拖动热区**'
        + '（按下即按 x 置值、拖动中持续更新、越界 clamp 且不中断）。留空 = 普通热区。</div>');
    }
    /* ★ M47：`kind:"slider"`（滑块）—— 字段按 `layout/_schema.md`「slider 元素字段」：
       `min/max/step/value`（**value 是初值**）+ `setting`（设置仓键名；空串 = 纯视觉滑块）
       + `rail`（轨道素材，以元素**垂直中心线**为轴；给 nine 则九宫格铺满元素框）
       + `handle`（手柄素材，**不随元素框裁剪**；活动态用 `state_assets.hover`）。
       ★ 运行期值 / 拖动 / 写设置仓由机制侧负责（replica.js §4.7 与 krkr 的 ui_settings.tjs
         同口径），编辑器只负责「形状 + 素材 + 初值 + 设置键」这一层。
       ★ 新增元素的入口仍只有 image（kind 输入框是 disabled）⇒ 滑块需在 JSON 里写
         或由数据脚本产出（方案 §三.1 已如实登记；本轮不扩新增入口）。 */
    if (e.kind === 'slider') {
      h.push('<div class="ed-row wide"><label>min</label>' + inp('min', e.min, 'number')
        + '<label>max</label>' + inp('max', e.max, 'number') + '</div>');
      h.push('<div class="ed-row wide"><label>step</label>' + inp('step', e.step, 'number')
        + '<label>value</label>' + inp('value', e.value, 'number') + '</div>');
      h.push(row('setting', inp('setting', e.setting)));
      var sKeys = (window.UI_REPLICA && UI_REPLICA.settingKeys)
        ? UI_REPLICA.settingKeys().join(' / ')
        : 'dlg_winopac / text_speed / auto_speed / vol_master / vol_bgm / vol_se / vol_sysse / vol_voice / vol_char';
      h.push('<div class="ed-hint">setting = 设置仓键名（9 个冻结键：' + esc(sKeys)
        + '）；留空 = 纯视觉滑块（不写仓）。<b>value 是初值</b> —— 运行期值在内存仓，'
        + 'setting 非空时初值以<b>仓里的值</b>为准（换屏返回保留用户拖出来的值）。</div>');
      h.push(row('rail.asset', assetSelect('rail.asset', (e.rail || {}).asset)));
      h.push(row('handle.asset', assetSelect('handle.asset', (e.handle || {}).asset)));
      h.push(row('handle.state_assets.normal',
        assetSelect('handle.state_assets.normal', ((e.handle || {}).state_assets || {}).normal)));
      h.push(row('handle.state_assets.hover',
        assetSelect('handle.state_assets.hover', ((e.handle || {}).state_assets || {}).hover)));
      var rn = (e.rail && e.rail.nine) || { l: 0, t: 0, r: 0, b: 0 };
      h.push('<div class="ed-row wide"><label>rail nine l</label>' + inp('rail.nine.l', rn.l, 'number')
        + '<label>t</label>' + inp('rail.nine.t', rn.t, 'number')
        + '<label>r</label>' + inp('rail.nine.r', rn.r, 'number')
        + '<label>b</label>' + inp('rail.nine.b', rn.b, 'number') + '</div>');
      h.push('<div class="ed-hint">rail 默认按素材**自身高度**居中（1:1，如 364×11）；填了非全零 nine '
        + '就改成九宫格铺满元素框（全零 = 整图缩放，与无 nine 同路径 —— border-width 全 0 时 '
        + 'border-image 不绘制任何像素）。手柄 29×29、**不随元素框裁剪**（元素 h=24 时上下各溢出 2–3px）。</div>');
    }
    if (e.kind === 'list') {
      h.push(row('item_h', inp('item_h', e.item_h, 'number')));
      h.push(row('max_rows', inp('max_rows', e.max_rows, 'number')));
      h.push(row('labels', '<input class="ed-num" data-p="labels_raw" value="' + esc((e.labels || []).join('|')) + '">'));
    }
    /* ★ M35b：三态贴图槽 —— **对任意 kind 的元素都可用**（不只 hit）。
       文字按钮就靠它：文字是 `image`，同样能挂 normal/hover 两态，再与图标用 state_group 绑定。
       规则（与 krkr 的 uiWidgetStateAsset、复刻的 attachStates 一致）：
         · 态图按元素**自身矩形**铺满绘制（image 与 hit 都是 100% 100%）；
         · 绘制优先级 pressed > hover > normal，缺键逐级回落（所以只填 normal 或只填 hover 都可用）；
         · 选「（无）」= 删除该键（三个都空则删掉整个 state_assets）；
         · `asset` 仍是「无态图时」的回落素材，建议保留（v2 编辑器不要求它等于 normal）。 */
    var sa = e.state_assets || {};
    h.push('<div class="ed-hint">state_assets 三态图（任意元素可用；缺键逐级回落：pressed &gt; hover &gt; normal）'
      + (e.kind === 'hit' ? '。带态图的 hit 会按自身矩形把图**拉伸**绘制，注意与同位置的 image 重复' : '')
      + '</div>');
    h.push(row('normal', assetSelect('state_assets.normal', sa.normal)));
    h.push(row('hover', assetSelect('state_assets.hover', sa.hover)));
    h.push(row('pressed', assetSelect('state_assets.pressed', sa.pressed)));
    /* ★ M35b：state_group 组绑定 —— 同一组的元素共享悬停/按下状态
       （图标 + 文字同组 ⇒ 鼠标落在任意一者上，两者同时进入悬停/按下形态）。 */
    h.push(row('state_group', inp('state_group', e.state_group)));
    h.push('<div class="ed-hint">state_group：同名的元素**共享**悬停/按下状态（如「图标 + 文字」绑成一个按钮）。'
      + '留空 = 不参与组绑定。</div>');

    h.push(row('note', '<input class="ed-num" data-p="note" value="' + esc(e.note || '') + '">'));
    box.innerHTML = h.join('');
    bindProp(box);
  }

  /* ★ M35：素材下拉（三态贴图槽用）。选项来自 asset_index.js 的资料库索引，
     值写成 layout 里使用的引用口径 `ui/<文件名>`。空值 = 该态不设（绘制时逐级回落）。
     ★ 一审 Minor-6：当前值若**不在索引里**（新加素材但没跑 emit_asset_index.py，
       或引用了已删素材），旧写法会静默显示成「（无）」→ 用户以为没设，其实是值不对。
       现在把该值单独列一条并标注，让问题可见（renderCheck 另有一条告警）。 */
  function assetSelect(path, cur) {
    var items = (window.UI_ASSET_INDEX && window.UI_ASSET_INDEX.items) || [];
    var h = ['<select class="ed-sel ed-sel-asset" data-p="' + path + '"><option value="">（无）</option>'];
    var known = false;
    for (var i = 0; i < items.length; i++) {
      var v = 'ui/' + items[i].n;
      if (cur === v) known = true;
      h.push('<option value="' + esc(v) + '"' + (cur === v ? ' selected' : '') + '>'
        + esc(items[i].n) + '</option>');
    }
    if (cur && !known) {
      h.splice(1, 0, '<option value="' + esc(cur) + '" selected>' + esc(cur) + '（不在资料库索引里）</option>');
    }
    h.push('</select>');
    return h.join('');
  }

  function assetMeta(a) {
    if (!a || !window.UI_ASSET_INDEX) return null;
    var b = String(a).replace(/^ui\//, '');
    for (var i = 0; i < window.UI_ASSET_INDEX.items.length; i++)
      if (window.UI_ASSET_INDEX.items[i].n === b) return window.UI_ASSET_INDEX.items[i];
    return null;
  }

  function setPath(obj, path, val) {
    var ps = path.split('.'), o = obj;
    for (var i = 0; i < ps.length - 1; i++) { if (!o[ps[i]]) o[ps[i]] = {}; o = o[ps[i]]; }
    o[ps[ps.length - 1]] = val;
  }

  /* ★ M47：删「清空后的空壳子对象」—— `rail` / `handle`（含 `handle.state_assets`）。
     只删**空值**叶子与空对象，不碰非空键；全空则把整个键删掉。
     ⚠️ **空值 = 空串 / null / undefined，`0` 是合法值**（一审 m1 打回的真 bug）：
       旧写法 `if (!o[k]) delete o[k]` 把 **0 当空** ⇒ 在 `rail.nine` 任一格输入 **0**
       会删掉该子键（`rail.nine` 变缺键字典）⇒ HTML 侧 `isZeroNine` 拿到 `NaN` 判否、
       走 border-image 且 `border-width` 含 `undefined` ⇒ **轨道不绘制**；引擎侧
       `uiWidgetNine` 后续坐标 NaN。故一律用 isEmptyVal() 判空。 */
  function isEmptyVal(v) { return v === null || v === undefined || v === ''; }
  function pruneSub(e, key, rest) {
    var o = e[key];
    if (!o) return;
    var sub = rest.split('.');
    if (sub.length === 1) {
      if (isEmptyVal(o[sub[0]])) delete o[sub[0]];
    } else if (sub.length === 2) {
      var inner = o[sub[0]];
      if (inner) {
        if (isEmptyVal(inner[sub[1]])) delete inner[sub[1]];
        if (!Object.keys(inner).length) delete o[sub[0]];
      }
    }
    if (!Object.keys(o).length) delete e[key];
  }

  function bindProp(box) {
    box.oninput = function (ev) {
      var t = ev.target, p = t.getAttribute && t.getAttribute('data-p');
      if (!p) return;
      var e = E.byId(ED.sel[0]); if (!e) return;
      var v;
      if (t.type === 'checkbox') v = t.checked;
      else if (t.type === 'number') v = t.value === '' ? undefined : Number(t.value);
      else v = t.value;
      if (p === 'font.faces_raw') { v = v.split(',').map(function (s) { return s.trim(); }).filter(Boolean); p = 'font.faces'; }
      if (p === 'labels_raw') { v = v.split('|'); p = 'labels'; }
      if (p === 'nine.l' || p === 'nine.t' || p === 'nine.r' || p === 'nine.b') {
        if (!e.nine) e.nine = { l: 0, t: 0, r: 0, b: 0 };
      }
      if (p === 'id') {
        if (!v || E.byId(v)) { E.setStatus('id 为空或重复', 'bad'); return; }
        var old = e.id, k = ED.sel.indexOf(old);
        delete e.id; e.id = v;
        if (k >= 0) ED.sel[k] = v;
      } else {
        setPath(e, p, v);
      }
      if (p === 'nine.l' || p === 'nine.t' || p === 'nine.r' || p === 'nine.b' || p === 'nine') {
        if (e.nine && !e.nine.l && !e.nine.t && !e.nine.r && !e.nine.b) delete e.nine;
      }
      /* ★ M35：三态贴图槽——选「（无）」时删键，三个都空则连 state_assets 一起删
         （不写空字符串进 JSON，否则 verify_ui 会报「素材不存在」）。 */
      if (p.indexOf('state_assets.') === 0) {
        if (e.state_assets) {
          var sk = p.split('.')[1];
          if (!v) delete e.state_assets[sk];
          if (!Object.keys(e.state_assets).length) delete e.state_assets;
        }
      }
      /* ★ M35b 一审（Minor）：state_group 清空时**删键**，不留 `state_group: ""` 脏字段
         （两端都把空串当「无组」，删掉只是让 JSON 干净、diff 更可读）。 */
      if (p === 'state_group' && !v) delete e.state_group;
      /* ★ M47：滑块的两个子对象与两个「空串即无」的字段 —— 清空后删壳/删键，
         不留 `rail:{}` / `handle:{}` / `handle.state_assets:{}` / `setting:""` / `slider:""`
         （verify_ui 对空 asset 会报「素材不存在」；两端都把空串当「无」）。 */
      if (p.indexOf('rail.') === 0) pruneSub(e, 'rail', p.slice(5));
      if (p.indexOf('handle.') === 0) pruneSub(e, 'handle', p.slice(7));
      if (p === 'setting' && !v) delete e.setting;
      if (p === 'slider' && !v) delete e.slider;
      E.reRender(); E.refreshCheck(); renderTree();
    };
    box.onchange = function (ev) {
      var t = ev.target;
      if (t.tagName === 'SELECT') box.oninput(ev);
    };
    box.onclick = function (ev) {
      var b = ev.target.closest && ev.target.closest('button[data-act]');
      if (!b) return;
      var e = E.byId(ED.sel[0]); if (!e) return;
      var act = b.getAttribute('data-act'), meta = assetMeta(e.asset);
      E.snapshot(act);
      if (act === 'nine-fit' && meta) { e.w = meta.w; e.h = meta.h; delete e.nine; }
      if (act === 'nine-zero') { e.nine = { l: 0, t: 0, r: 0, b: 0 }; }
      if (act === 'nine-none') { delete e.nine; }
      if (act === 'fit-rect' && meta) { delete e.nine; e.w = meta.w; e.h = meta.h;
        e.x = Math.round(num(e.x)); e.y = Math.round(num(e.y)); }
      E.reRender(); E.refreshProp(); E.refreshCheck();
    };
  }

  /* ══════════════════════════════ 即时校验 ══════════════════════════════ */
  function renderCheck() {
    var box = $('ed-check');
    if (!box) return;
    var errs = [], warns = [], ids = {};
    for (var i = 0; i < ED.els.length; i++) {
      var e = ED.els[i];
      if (ids[e.id]) errs.push('id 重复：' + e.id); else ids[e.id] = 1;
      if (!e.id) errs.push('第 ' + i + ' 个元素缺 id');
      if (!e.kind) errs.push(e.id + ' 缺 kind');
      if (e.kind === 'image') {
        /* ★ M45d（2026-09-23，用户报「dlg.content 缺 asset」硬错误后修）：**动态层**是
           `layout/_schema.md` §四 的合法写法 —— `"asset": null, "dynamic": "<名>"`
           （`story_background` / `story_chara` / `slot_thumb` / `gallery_preview` …），
           运行期由调用方填充、**未填充时两侧渲染器画占位底色**（不得跳过、也不得报缺件）。
           ⇒ 动态层**不参与**「缺 asset」与「无 nine 必须等于实尺寸」这两项校验，
           否则 `dlg.content`、`gallery.preview` 会被误报硬错误（`verify_ui.py` 是过的）。 */
        if (e.dynamic) {
          /* 动态层：跳过素材与尺寸校验 */
        } else {
        /* ★ M35b：带 state_assets 的 image 允许 `asset` 留空（用 normal 当尺寸依据） */
        /* ★ M35b 一审（Minor）：参照物取**实际会被绘制的**那张 —— 有 state_assets 时
           `asset` 根本不会被画（引擎只在三键全空时才回落它），拿它比尺寸会产生假硬错误。 */
        var sizeRef = (e.state_assets && e.state_assets.normal) || e.asset;
        if (!sizeRef) errs.push(e.id + ' 缺 asset（也没给 state_assets.normal）');
        var m = assetMeta(sizeRef);
        if (!m) { warns.push(e.id + '：素材不在索引里（' + sizeRef + '）'); }
        else if (!e.nine) {
          if (Math.round(num(e.w)) !== m.w || Math.round(num(e.h)) !== m.h)
            errs.push(e.id + '：无 nine 时 w/h 必须等于 PNG 实尺寸 ' + m.w + '×' + m.h
              + '（现 ' + Math.round(num(e.w)) + '×' + Math.round(num(e.h)) + '）');
        } else {
          var lr = num(e.nine.l) + num(e.nine.r), tb = num(e.nine.t) + num(e.nine.b);
          if (lr > 0 && num(e.w) < lr) errs.push(e.id + '：w < nine.l+r（' + num(e.w) + ' < ' + lr + '）');
          if (tb > 0 && num(e.h) < tb) errs.push(e.id + '：h < nine.t+b（' + num(e.h) + ' < ' + tb + '）');
        }
        }
      }
      /* ★ M47：`kind:"slider"` 的即时校验（口径照 `layout/_schema.md`「拖动契约 / 设置仓」）：
         硬错误 = 机制侧画不出来或值域非法；警告 = 可自动修正 / 语义退化，改完仍可用。 */
      if (e.kind === 'slider') {
        var sRail = e.rail || {}, sHd = e.handle || {}, sSA = sHd.state_assets || {};
        if (!sRail.asset) errs.push(e.id + '：slider 缺 rail.asset（轨道素材 —— 没有它滑块画不出轨道）');
        else if (!assetMeta(sRail.asset)) warns.push(e.id + '：rail.asset 不在资料库索引里（' + sRail.asset + '）');
        if (!sHd.asset && !sSA.normal && !sSA.hover) {
          errs.push(e.id + '：slider 缺 handle.asset（也没给 handle.state_assets.normal/hover）');
        } else {
          if (sHd.asset && !assetMeta(sHd.asset)) warns.push(e.id + '：handle.asset 不在资料库索引里（' + sHd.asset + '）');
          ['normal', 'hover'].forEach(function (k) {
            var a = sSA[k];
            if (a && !assetMeta(a)) warns.push(e.id + '：handle.state_assets.' + k + ' 不在资料库索引里（' + a + '）');
          });
        }
        var sMin = num(e.min), sMax = num(e.max);
        if (!(sMax > sMin)) {
          errs.push(e.id + '：slider 的 min>=max（' + sMin + '>=' + sMax + '）⇒ 值域非法'
            + '（机制侧会退化成「只有一个值」，手柄恒在左端）');
        }
        if (e.value === undefined || e.value === null) {
          warns.push(e.id + '：slider 未给 value（初值）⇒ 运行期按 0 起步');
        } else {
          var sV = num(e.value);
          if (sV < sMin || sV > sMax) {
            /* 越界 ⇒ **警告 + 自动 clamp**（方案：机制侧写仓时也会 clamp，这里提前对齐） */
            e.value = Math.min(Math.max(sV, sMin), sMax);
            warns.push(e.id + '：value=' + sV + ' 越出 ' + sMin + '..' + sMax + ' ⇒ **已自动 clamp 为 '
              + e.value + '**（机制侧写仓同样会 clamp，此处提前对齐）');
          }
        }
        if (num(e.step) <= 0) {
          warns.push(e.id + '：step<=0 ⇒ 不做步进对齐（拖动仍按连续值换算，键盘 ±step 退化为 ±1）');
        }
        var sKeys = (window.UI_REPLICA && UI_REPLICA.SETTING_DEF) ? Object.keys(UI_REPLICA.SETTING_DEF) : null;
        if (e.setting && sKeys && sKeys.indexOf(e.setting) < 0) {
          warns.push(e.id + '：setting="' + e.setting + '" 不在设置仓定义表（' + sKeys.join('/')
            + '）里 ⇒ 运行期按**纯视觉滑块**处理（不写仓）');
        }
      }
      if (e.kind === 'text' && !e.sample) warns.push(e.id + '：text 无 sample');
      if (e.kind === 'text' && !e.font) errs.push(e.id + '：text 无 font');
      if (e.state_assets) {
        /* ★ M35b：三态图检查对**任意 kind** 都做（不再只查 hit）
           —— 旧版编辑器只列文本、不做这项检查，而 verify_ui.py 的 [1] 引用完整性那时也
           **完全不覆盖 state_assets**（见 M35_悬停按下态_代码缺口诊断.md §2.5），
           三态图缺件会一路绿灯。两边现在都补上了。 */
        ['normal', 'hover', 'pressed'].forEach(function (k) {
          var a = e.state_assets[k];
          if (!a) return;
          if (!assetMeta(a)) warns.push(e.id + '：state_assets.' + k + ' 不在资料库索引里（' + a + '）');
        });
      }
      if (e.kind === 'hit' && e.state_assets) {
        var dup = ED.els.some(function (o) { return o.id !== e.id && o.kind === 'image'
          && num(o.x) === num(e.x) && num(o.y) === num(e.y)
          && o.asset && e.state_assets.normal && ('ui/' + o.asset.replace(/^ui\//, '')) === e.state_assets.normal; });
        if (dup) warns.push(e.id + '：与同位置的 image 用同一张图 —— hit 会按自身矩形把它再画一遍（可能"两层"）');
      }
      /* ★ M35b：组绑定自检 —— 同组元素应当**至少两个**（单元素成组说明多半是打错了组名） */
      if (e.state_group) {
        var gn = ED.els.filter(function (o) { return o.state_group === e.state_group; }).length;
        if (gn < 2) warns.push(e.id + '：state_group「' + e.state_group + '」只有它自己，组绑定不会生效（检查组名是否拼错）');
      }
    }
    var h = [];
    if (!errs.length && !warns.length) h.push('<div class="ed-hint ok">✓ ' + ED.els.length + ' 个元素，未发现硬错误</div>');
    /* ★ M47 第三轮（一审 m2 打回）：旧文案写「（会导致 verify_ui.py 失败）」——**不实**：
       `verify_ui` 不校验 slider 的 min/max（[7] 只查 opacity 范围），slider 类的硬错误
       只在编辑器这一层被拦。改为如实口径。 */
    if (errs.length) h.push('<div class="ed-err">硬错误 ' + errs.length + ' 条（会被编辑器自身拦住；'
      + '其中 image 尺寸 / 素材缺件类 verify_ui.py 也会拦）</div>');
    errs.slice(0, 24).forEach(function (s) { h.push('<div class="ed-err">• ' + esc(s) + '</div>'); });
    if (errs.length > 24) h.push('<div class="ed-hint">…还有 ' + (errs.length - 24) + ' 条</div>');
    if (warns.length) h.push('<div class="ed-warn">提示 ' + warns.length + ' 条</div>');
    warns.slice(0, 16).forEach(function (s) { h.push('<div class="ed-warn">• ' + esc(s) + '</div>'); });
    box.innerHTML = h.join('');
  }

  /* ══════════════════════════════ 工具栏 ══════════════════════════════ */
  function syncToolbar() {
    var s = $('ed-snap'); if (s) { s.textContent = '吸附：' + (ED.snap ? '开' : '关'); s.className = 'ed-btn' + (ED.snap ? ' on' : ''); }
    var g = $('ed-grid'); if (g) g.className = 'ed-btn' + (ED.grid ? ' on' : '');
    var o = $('ed-outline'); if (o) o.className = 'ed-btn' + (ED.outline ? ' on' : '');
  }
  function toggleGrid() {
    ED.grid = !ED.grid;
    syncToolbar();
    E.drawGrid();
    E.drawOverlay();
    E.setStatus(ED.grid
      ? '网格已开：步长 ' + ED.gridStep + 'px（主刻度每 5 格）｜拖动时左/上边会吸附到网格线'
      : '网格已关');
  }

  function setupToolbar() {
    var gs = $('ed-grid-step');
    if (gs) gs.onchange = function () {
      ED.gridStep = Number(gs.value) || 20;
      E.drawGrid();
      if (ED.grid) E.setStatus('网格步长 = ' + ED.gridStep + 'px');
    };
    $('ed-undo').onclick = E.doUndo;
    $('ed-redo').onclick = E.doRedo;
    $('ed-snap').onclick = function () { ED.snap = !ED.snap; syncToolbar(); };
    $('ed-grid').onclick = toggleGrid;
    $('ed-outline').onclick = function () {
      ED.outline = !ED.outline; syncToolbar();
      var c = $('canvas');
      c.style.filter = ED.outline ? 'grayscale(1) brightness(.45)' : '';
      E.drawOverlay();
    };
    $('ed-reload').onclick = function () {
      if (!confirmChange()) return;
      E.loadScreen(ED.sid);
    };
    $('ed-front').onclick = function () { reorder(1); };
    $('ed-back').onclick = function () { reorder(-1); };
    /* ★ M3：「按 flag 预览」开关 —— 只改编辑器内存里的预览态，不写回 layout 数据 */
    var fp = $('ed-flag-preview');
    if (fp) fp.onclick = function () {
      var on = E.setFlagPreview(!ED.flagPreview);
      E.setStatus(on
        ? '已开启 flag 预览：元素按下面各 flag 的取值过滤（收起/展开/钉住/气泡等状态可逐个预览）'
        : '已关闭 flag 预览：忽略 flag，全部元素可见可编辑（等同既有编辑体验）');
    };
    $('ed-dup').onclick = duplicate;
    $('ed-del').onclick = delSel;
    /* ★ M35b：居中（对任意 kind 可用；多选时逐个居中到画布） */
    $('ed-center-h').onclick = function () { centerSel('h'); };
    $('ed-center-v').onclick = function () { centerSel('v'); };
    $('ed-center-b').onclick = function () { centerSel('b'); };
    $('ed-export').onclick = openExport;
    $('ed-modal-close').onclick = function () { $('ed-modal').classList.remove('on'); };
    $('ed-modal-copy').onclick = function () {
      var t = $('ed-modal-text'); t.select();
      try { document.execCommand('copy'); E.setStatus('已复制到剪贴板'); }
      catch (err) { E.setStatus('复制失败，请手动 Ctrl+C', 'bad'); }
    };
    $('ed-modal-dl').onclick = downloadJSON;
    // 折叠
    Array.prototype.forEach.call(document.querySelectorAll('.ed-sec > h3'), function (h) {
      h.onclick = function () { h.parentNode.classList.toggle('folded'); };
    });
  }

  function reorder(dir) {
    if (!ED.sel.length) return;
    E.snapshot('z');
    var zs = ED.els.map(function (e) { return e.z || 0; });
    var zmin = Math.min.apply(null, zs), zmax = Math.max.apply(null, zs);
    ED.sel.forEach(function (id) {
      var e = E.byId(id); if (!e) return;
      e.z = dir > 0 ? zmax + 1 : zmin - 1;
    });
    E.reRender(); E.refreshProp(); renderTree();
  }

  /* ★ M35b：居中 —— 把选中元素（任意 kind）在画布上摆正。
     mode 'h' = 水平居中（只改 x）｜'v' = 垂直居中（只改 y）｜'b' = 双向居中。
     画布尺寸取 E.CW / E.CH（editor_core 从 ui_layout.js 的 canvas 读入，本文件不写死 1920×1080）。
     多选时**逐个**居中（各自摆到画布正中；不改变元素之间的相对关系以外的语义）。 */
  function centerSel(mode) {
    if (!ED.sel.length) return;
    var CW = num(E.CW), CH = num(E.CH);
    var needH = (mode === 'h' || mode === 'b'), needV = (mode === 'v' || mode === 'b');
    if ((needH && !CW) || (needV && !CH)) { E.setStatus('拿不到画布尺寸', 'bad'); return; }
    /* ★ M35b 一审（Minor）：缺 w/h 的元素（elemW/elemH 返回 0）会被摆到画布中心贴左上角，
       而 renderCheck 对非 image 元素不要求 w/h —— 这里挡一道，避免"看起来居中其实偏了"。 */
    var noSize = ED.sel.filter(function (id) {
      var o = E.byId(id); return o && (E.elemW(o) === 0 || E.elemH(o) === 0);
    });
    if (noSize.length) { E.setStatus('这些元素没有 w/h，无法居中：' + noSize.join('、'), 'bad'); return; }
    E.snapshot('center-' + mode);
    var n = 0;
    ED.sel.forEach(function (id) {
      var e = E.byId(id); if (!e) return;
      if (mode === 'h' || mode === 'b') { if (CW) e.x = Math.round((CW - E.elemW(e)) / 2); }
      if (mode === 'v' || mode === 'b') { if (CH) e.y = Math.round((CH - E.elemH(e)) / 2); }
      n++;
    });
    E.reRender(); E.refreshProp(); E.refreshCheck(); renderTree();
    E.setStatus('已居中（' + (mode === 'h' ? '水平' : (mode === 'v' ? '垂直' : '水平+垂直')) + '）：' + n + ' 个元素');
  }

  function duplicate() {
    if (!ED.sel.length) return;
    E.snapshot('dup');
    var news = [];
    ED.sel.forEach(function (id) {
      var e = E.byId(id); if (!e) return;
      var c = JSON.parse(JSON.stringify(e));
      var base = c.id + '_copy', k = 2, nid = base;
      while (E.byId(nid)) { nid = base + '_' + (k++); }
      c.id = nid; c.x = num(c.x) + 16; c.y = num(c.y) + 16; c.z = (c.z || 0) + 1;
      ED.els.push(c); news.push(nid);
    });
    ED.sel = news;
    E.reRender(); E.refreshAll(); renderTree();
  }

  function delSel() {
    if (!ED.sel.length) return;
    if (!confirm('删除 ' + ED.sel.length + ' 个元素？')) return;
    E.snapshot('del');
    ED.els = ED.els.filter(function (e) { return ED.sel.indexOf(e.id) < 0; });
    ED.sel = [];
    E.reRender(); E.refreshAll(); renderTree();
  }

  /* 键盘：方向键微调 / Del / Ctrl+D / PageUp-Down / Esc / Ctrl+Z-Y / S G O */
  function setupKeys() {
    window.addEventListener('keydown', function (ev) {
      var t = ev.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT')) return;
      var step = ev.shiftKey ? 10 : 1;
      if (ev.key === 'Escape') { ED.sel = []; E.drawOverlay(); E.refreshProp(); renderTree(); return; }
      if (ev.key === 'Delete' || ev.key === 'Backspace') { delSel(); ev.preventDefault(); return; }
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'z') { E.doUndo(); ev.preventDefault(); return; }
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'y') { E.doRedo(); ev.preventDefault(); return; }
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'd') { duplicate(); ev.preventDefault(); return; }
      if (ev.key === 'PageUp') { reorder(1); ev.preventDefault(); return; }
      if (ev.key === 'PageDown') { reorder(-1); ev.preventDefault(); return; }
      if (ev.key === 's' && !ev.ctrlKey) { ED.snap = !ED.snap; syncToolbar(); return; }
      if (ev.key === 'g' && !ev.ctrlKey) { toggleGrid(); return; }
      if (ev.key === 'o' && !ev.ctrlKey) { $('ed-outline').onclick(); return; }
      /* ★ M35b：居中快捷键 —— C = 双向居中，Shift+C = 只水平，Alt+C = 只垂直 */
      if (ev.key === 'c' && !ev.ctrlKey && !ev.metaKey) {
        centerSel(ev.altKey ? 'v' : (ev.shiftKey ? 'h' : 'b'));
        ev.preventDefault(); return;
      }
      var dx = 0, dy = 0;
      if (ev.key === 'ArrowLeft') dx = -step;
      else if (ev.key === 'ArrowRight') dx = step;
      else if (ev.key === 'ArrowUp') dy = -step;
      else if (ev.key === 'ArrowDown') dy = step;
      else return;
      if (!ED.sel.length) return;
      ev.preventDefault();
      E.snapshot('nudge');
      ED.sel.forEach(function (id) {
        var e = E.byId(id); if (!e) return;
        e.x = Math.round(num(e.x) + dx); e.y = Math.round(num(e.y) + dy);
      });
      E.reRender(); E.refreshProp();
    });
  }

  /* ══════════════════════════════ 导出 ══════════════════════════════ */
  function openExport() {
    var sc = L.screens[ED.sid];
    $('ed-modal-title').textContent = '导出 · screens/' + fileName() + '  （覆盖回 layout/screens/ 后跑 gen_layout.py → verify_ui.py）';
    $('ed-modal-text').value = E.exportJSON();
    $('ed-modal').classList.add('on');
  }
  function fileName() {
    var si = window.UI_SCREEN_INDEX || [];
    for (var i = 0; i < si.length; i++) if (si[i].id === ED.sid) return si[i].file;
    return ED.sid + '.json';
  }
  function downloadJSON() {
    var txt = E.exportJSON();
    var blob = new Blob([txt], { type: 'application/json;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fileName();
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    E.setStatus('已导出 ' + fileName());
  }

  /* ══════════════════════════════ 启动 ══════════════════════════════ */
  function boot() {
    E._ui.prop = renderProp;
    E._ui.tree = renderTree;
    E._ui.check = renderCheck;
    E._ui.flags = buildFlagBar;             // ★ M3：flag 预览条（换屏/重载后重建）
    buildScreenSel();
    buildLibCats(); renderLib();
    setupLib(); setupToolbar(); setupKeys(); syncLibStat();
    syncToolbar();
    buildFlagBar();
    window.UI_EDITOR.reloadLib = reloadLib;
    E.refreshAll();
    renderTree();
    E.refreshStatus();
    var st = $('ed-status');
    if (st) st.textContent = '就绪｜屏 ' + ED.sid + '｜元素 ' + ED.els.length + ' 个'
      + '｜左侧资料库点缩略图加素材，画布拖动元素，右侧改属性，完事点「导出 JSON」。'
      + '【选中即可拖】按在选中元素的范围内即可拖动它；要重选别的元素，按 Alt 点击或用元素树。';
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function(){ setTimeout(boot, 20); });
  else setTimeout(boot, 20);
})();
