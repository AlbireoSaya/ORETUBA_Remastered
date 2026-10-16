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
    zoom: 1,
    /* ★ M3（ISSUE-20260922-28）：屏级 flag 预览。
       flagPreview=false（默认）⇒ **忽略 flag**：编辑口径 = 只看 visible_default，
       与 M35 之前的体验完全一致（不会被收起态的 flag 挡住看不见元素）；
       flagPreview=true ⇒ 按 flagVals 里选定的取值套用 §四 的可见性谓词，
       渲染与命中/选中口径都跟着走（与 replica 的 elementVisible 同一语义）。 */
    flagPreview: false,
    flagVals: {},           // flag 名 → 当前预览取值（字符串）
    /* ★ M47：**上一次派生所用的页取值**（`cfg_page`；用法见 applyFlagsMode）。
       作用：判断「页变了没有」—— 页没变就不重跑派生，好让手选的单个值键（`cfg_v_*`）
       留得住（口径：唯一派生触发键是 `cfg_page`）。换屏 / 开预览时清空 ⇒ 那些路径照样派生。 */
    derivedPage: null
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
    /* ★ M3：换屏时清空 flag 预览取值（按新屏的 flags_default 重新初始化，见 syncFlagVals） */
    ED.flagVals = {};
    /* ★ M47：换屏（含重载同一屏）后强制在下次重渲染时重跑一次切页派生（见 applyFlagsMode） */
    ED.derivedPage = null;
    syncFlagVals();
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
    applyFlagsMode();
    syncOverlay();
    drawGrid();
    drawOverlay();
  }

  /* =============================================== 屏级 flag 预览（★ M3） ======
     契约（layout/_schema.md §四「屏级状态 flag」）：
       元素可见/可编辑 ⟺ visible_default !== false
                          且（无 vis_flag → 通过；有 → 当前取值满足 vis_when，
                              vis_when === "*" 时要求非空）
     · flagPreview 关（默认）：**忽略 flag** —— 编辑口径只看 visible_default，
       并把本屏（含屏级 attach 附加层）所有带 vis_flag 的元素在 DOM 上强制恢复显示，
       避免「编辑快捷条时它默认收起、看不见元素」。不影响 layout 数据本身。
     · flagPreview 开：**预览 = 与产品同口径（含派生）** —— 先把 flagVals 写进 replica 的
       flag 表，再按当前 `cfg_page` 跑一次**机制侧的切页派生**（`configDerivePageFlags` /
       `configFlagsInitFor`，见下方 derivePageFlagsForPreview），把派生后的**实际生效值**
       **回读**进 flagVals，最后 applyFlagVisibility()。渲染 / 命中 / 选中全部按派生后的值过滤。
       ⇒ 为什么必须有这一步：M47 的分页机制里 `vis_flag` **一个元素只能带一对**
         （`layout\_schema.md` §四），值元素带的是**值 flag**（`cfg_v_<键>` / `cfg_vchar`），
         **页归属只写在同行的 hit 上**（否则非本页的热区会跨页抢点击）⇒ 值元素的页归属
         **只能是算出来的**。只做逐元素 flag 比对（不跑派生）就会把「另一页的值 / 选中元素」
         照样画出来，与产品（引擎实机 / 复刻页）分叉。
     开关与取值只在编辑器内存里，**不写回 layout**。 */
  /* 预览涉及的屏对象 = 本屏（+ 屏级 attach 的附加层，其 flag 与承载屏共用一张表） */
  function previewScreens(sid) {
    var out = [], sc = screenOf(sid), ad;
    if (sc) out.push(sc);
    if (sc && sc.attach) { ad = screenOf(String(sc.attach)); if (ad) out.push(ad); }
    return out;
  }
  /* 该屏要预览的 flag 名 = 各屏 flags_default 的键 ∪ 元素 vis_flag ∪ reveal.flag/tip_flag */
  function flagNamesOfScreen(sid) {
    var names = [], seen = {};
    function add(n) {
      n = (n === null || n === undefined) ? '' : String(n);
      if (!n || seen[n]) return;
      seen[n] = 1; names.push(n);
    }
    previewScreens(sid).forEach(function (sc) {
      Object.keys(sc.flags_default || {}).forEach(add);
      (sc.elements || []).forEach(function (e) { if (e && e.vis_flag) add(e.vis_flag); });
      if (sc.reveal) { add(sc.reveal.flag); add(sc.reveal.tip_flag); }
    });
    return names;
  }
  /* 某 flag 的可选取值 = 该屏（含附加层）元素里出现过的 vis_when（不含通配 "*"）+ 空串
     （`quick.tips` 的 "*" 是「非空即显示」，不代表某个具体取值，故不入候选） */
  function flagValuesOfScreen(sid, flagName) {
    var vals = [], seen = {};
    function add(v) {
      v = (v === null || v === undefined) ? '' : String(v);
      if (seen[v]) return;
      seen[v] = 1; vals.push(v);
    }
    add('');                                        // 空串恒在候选里（= 不显示/未设置）
    previewScreens(sid).forEach(function (sc) {
      var fd = sc.flags_default || {};
      if (fd[flagName] !== undefined) add(fd[flagName]);
      (sc.elements || []).forEach(function (e) {
        if (!e || e.vis_flag === undefined) return;
        if (String(e.vis_flag) !== String(flagName)) return;
        var w = (e.vis_when === null || e.vis_when === undefined) ? '' : String(e.vis_when);
        if (w === '*') return;
        add(w);
      });
    });
    return vals;
  }
  /* 预览涉及的**全部元素定义**（本屏 + 附加层），供「关闭预览」时按各自 visible_default 恢复 */
  function previewDefs(sid) {
    var out = [];
    previewScreens(sid).forEach(function (sc) {
      (sc.elements || []).forEach(function (e) { if (e && e.id) out.push(e); });
    });
    return out;
  }
  function flagVal(n) {
    var v = ED.flagVals[String(n)];
    return (v === null || v === undefined) ? '' : String(v);
  }

  /* 唯一派生触发键 = 屏级页 flag（`layout\_schema.md` §四「分页与选中态」）。
     机制侧 `configDerivePageFlags()` 自身也按 `getFlag(PAGE_FLAG)` 取页，此处沿用同一名字。 */
  var PAGE_FLAG = 'cfg_page';

  /* ★ M47：派生后**回读实际生效值** —— 派生改的是 replica 的 flag 表（非本页的值键被置空、
     本页的按三级优先链取回），而编辑器的可见性判据 `isVisible()`（命中测试 / 选中口径）
     读的是 `ED.flagVals`。不回读 ⇒「画出来的」与「编辑器以为的」分叉。
     缺值回落 ''（与 R.getFlag 一致）。 */
  function readBackFlagVals() {
    flagNamesOfScreen(ED.sid).forEach(function (n) {
      var v = R.getFlag(n);
      ED.flagVals[n] = (v === null || v === undefined) ? '' : String(v);
    });
  }
  /* 按当前 `cfg_page` 跑一次**机制侧派生**并把结果回读进 flagVals。
     走**进屏语义**入口 `R.configFlagsInitFor(ED.sid)`（它内部固定 `captureMemo = false`，
     对应一审 C4 的裁定：进屏那一刻 flag 刚被 `flags_default` 重置，捕获记忆 = 用默认值
     冲掉用户的选择）—— 换屏 / 开预览 / 重载路径都用它，**不要**在这些路径传 captureMemo=true。
     非设置屏（屏内无 `config_set_*` / `config_char_*` 热区）它返回 0、完全无副作用。 */
  function derivePageFlagsForPreview() {
    var n = R.configFlagsInitFor(ED.sid);
    readBackFlagVals();
    ED.derivedPage = flagVal(PAGE_FLAG);
    return n;
  }

  /* 把 flagVals 与 replica 的 flag 表对齐（仅预览开启时），并同步 DOM 显隐 */
  function applyFlagsMode() {
    var host = $('canvas');
    var i, j;
    if (ED.flagPreview) {
      flagNamesOfScreen(ED.sid).forEach(function (n) { R.setFlag(n, flagVal(n)); });
      /* 与产品同口径：预览态下按当前 `cfg_page` 派生值标志。
         **只在页真的变了（或换屏 / 刚开预览 ⇒ derivedPage 已被清空）时才重跑**：
         `cfg_page` 是唯一派生触发键 —— 若每次重渲染都派生，用户手选 `cfg_v_display=full`
         之类的**单项探查**会被立刻覆写（下拉写值不触发派生；下一次改 `cfg_page` 才重新派生
         = 与产品一致：切页重算值）。这是刻意的口径，不是 bug。 */
      if (ED.derivedPage !== flagVal(PAGE_FLAG)) derivePageFlagsForPreview();
      R.applyFlagVisibility();
      return;
    }
    if (!host) return;
    /* 关闭预览：忽略 flag ⇒ 把带 vis_flag 的元素按 visible_default 恢复显示。
       只碰带 vis_flag 的元素，其余元素的 display 由运行期（打字机/隐藏窗口等）自己管。 */
    var defs = previewDefs(ED.sid), nodes = host.querySelectorAll('[data-ui-id]');
    for (i = 0; i < nodes.length; i++) {
      var id = nodes[i].getAttribute('data-ui-id');
      for (j = 0; j < defs.length; j++) {
        if (defs[j].id !== id) continue;
        if (defs[j].vis_flag === undefined) break;
        nodes[i].style.display = (defs[j].visible_default === false) ? 'none' : '';
        break;
      }
    }
  }
  /* 初始化/纠正 flagVals：
     · 该 flag 尚无取值 → 取它在该屏（或附加层）flags_default 里的初值；
     · 已有取值但不在候选集里（换屏/改数据后失效）→ 同样回到初值。
     ⚠️ 不能只做「现值是否合法」的判断：缺值与显式空串在 flagVal() 里同为 ""，
     而 "" 恒是合法候选 ⇒ 缺值会被当成「合法空串」而漏掉初始化（首次实现即踩到此坑）。 */
  function syncFlagVals() {
    var names = flagNamesOfScreen(ED.sid);
    var own = screenOf(ED.sid) || {};
    var fd = own.flags_default || {};
    var att = (own.attach ? screenOf(String(own.attach)) : null) || null;
    var afd = (att && att.flags_default) || {};
    names.forEach(function (n) {
      if (ED.flagVals[n] !== undefined && flagValuesOfScreen(ED.sid, n).indexOf(flagVal(n)) >= 0) return;
      var d = (fd[n] !== undefined) ? fd[n] : ((afd[n] !== undefined) ? afd[n] : '');
      ED.flagVals[n] = (d === null || d === undefined) ? '' : String(d);
    });
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
  /* ★ M3：可见性口径由「按 flag 预览」开关决定（语义见上方 applyFlagsMode 的注释）。
     关闭（默认）时与改动前完全一致 = 只看 visible_default。 */
  function isVisible(e) {
    if (!e || e.visible_default === false) return false;
    if (!ED.flagPreview) return true;
    var n = e.vis_flag;
    if (n === null || n === undefined || String(n) === '') return true;
    var want = (e.vis_when === null || e.vis_when === undefined) ? '' : String(e.vis_when);
    var cur = flagVal(n);
    return (want === '*') ? (cur !== '') : (cur === want);
  }

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
  /* ★ M06（2026-09-24 · ISSUE-20260924-06 · 冻结书 §5「编辑器侧已知缺陷」）：
     **`list` 的高度是派生量** —— layout JSON 里没有 `h` 键。
     渲染期高度 = `uiWidgetListSpan`（`ui_widget.tjs`）= 可见行数 × `item_h` + (行数−1) × `gap`，
     行数 = `min(labels 条数, max_rows)`（纵向）／`ceil(labels / max_cols)`（横向）。
     编辑器原先一律读 `e.h` ⇒ 该元素 `elemH` 为 **0** ⇒ 选中框高度 0、**画布上点不中**
     （这正是冻结书点名的缺陷）。公式与 `工具\test_state_targets.py::rect_of()` **逐字相同**
     （那份实现当年也是为同一原因补的，两边口径必须一致）。
     ★ 影响面：命中测试 / 选中框 / 框选 / 吸附 / 居中 —— 全部走 elemH，故一处修好全部生效。
     ★ 导出侧不写 `h`：本函数只服务**编辑器交互**，数据里仍是「无 h ⇒ 派生」（见 resize 的竖向守卫）。
     ⚠️ **已知缺口（非本轮回归，M06 一审登记）**：本式只算「span」（高度），**不含**
     `uiWidgetRect` 的两项修正 —— ① `stack_bottom`（有则 `y = stack_bottom - h`，选择肢由下往上堆）；
     ② `scroll.page_size`（分页时按**当页可见项数**算 span，而非 labels 全量）。
     故对带 `stack_bottom` 的 list（如 `dlg.choices`）编辑器框会落在 `y=e.y` 而非引擎实际的
     `stack_bottom-h`（实测 `dlg.choices`：编辑器 y=0..136，引擎 531..667）。
     `工具\test_state_targets.py::rect_of()` 有**同一缺口**；两处要一起补才不至于口径分叉，
     属独立立项，本轮只订正提示、不动公式。 */
  function listSpanH(e) {
    var itemH = num(e.item_h);
    var gap = num(e.gap);
    var n = (e.labels && e.labels.length) ? e.labels.length : 0;
    var rows;
    if (e.orientation === 'h') {
      var cols = Math.max(1, num(e.max_cols) || n || 1);
      rows = Math.max(1, Math.ceil(n / cols));
    } else {
      rows = Math.max(1, Math.min(n, num(e.max_rows) || n || 1));
    }
    return rows * itemH + (rows - 1) * gap;
  }
  /* 该元素的 `h` 是否为**派生**（= 是 list 且数据里确实没有 `h`） */
  function derivedH(e) {
    return !!(e && e.kind === 'list' && (e.h === null || e.h === undefined));
  }
  function elemW(e) { return num(e.w); }
  function elemH(e) { return derivedH(e) ? listSpanH(e) : num(e.h); }

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
      /* ★ M06：**派生高度的 list 不得竖向拉伸** —— 它的 h 由 item_h / max_rows / labels
         算出来，两端渲染器都**不读** `e.h`（uiWidgetRect 走 uiWidgetListSpan；HTML 的
         buildList 也按 item_h 排布）⇒ 竖向 resize 写进去的 h 是一句没人读的假数据。
         显式拒绝并给出正确改法（不静默改写、也不静默无效）。 */
      if (derivedH(e) && (hd === 'n' || hd === 's' || hd === 'ne' || hd === 'nw'
                          || hd === 'se' || hd === 'sw')) {
        setStatus('list 的高度是派生值（item_h × 行数），不能竖向拉伸 —— 请改 item_h / max_rows / labels');
        return;
      }
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
      e2.w = Math.max(1, Math.round(nw));
      /* ★ M06：派生高度的 list（数据里没有 `h`）**不得**因为横向 resize 就往数据里写出一个
         `h` —— 那是别人不读的假数据，且会让「无 h ⇒ 派生」这条契约在数据里消失。
         故该情形下只改 w（竖向已被 onDown 的守卫拦住）。 */
      if (!derivedH(e2)) e2.h = Math.max(1, Math.round(nh));
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
  /* ★ M3：flag 预览条（由 editor_ui.js 挂入）—— 换屏/重载后要重建下拉 */
  function refreshFlags() { syncFlagVals(); ED.ui.flags && ED.ui.flags(); }
  function refreshAll() { refreshStatus(); refreshProp(); refreshTree(); refreshCheck(); refreshFlags(); }

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
    /* ★ M06：list 的派生高度（供属性面板显示「派生，只读」与竖向 resize 守卫共用同一入口） */
    listSpanH: listSpanH, derivedH: derivedH,
    /* 由 editor_ui.js 填充 */
    _ui: ED.ui,
    refreshProp: refreshProp, refreshTree: refreshTree,
    refreshCheck: refreshCheck, refreshAll: refreshAll,
    /* ★ M3：屏级 flag 预览（供 editor_ui.js 的操作栏与无头自检使用） */
    refreshFlags: refreshFlags,
    flagNamesOfScreen: flagNamesOfScreen,
    flagValuesOfScreen: flagValuesOfScreen,
    syncFlagVals: syncFlagVals,
    setFlagPreview: function (on) {                     // 开关（true = 按 flag 过滤）
      ED.flagPreview = !!on;
      /* ★ M47：开关切换后强制在下次重渲染里重跑一次派生（derivedPage 清空，见 applyFlagsMode） */
      ED.derivedPage = null;
      if (ED.flagPreview) syncFlagVals();
      reRender(); refreshAll();
      return ED.flagPreview;
    },
    setFlagValue: function (name, val) {                // 设置某 flag 的预览取值
      var n = String(name);
      ED.flagVals[n] = (val === null || val === undefined) ? '' : String(val);
      /* ★ M47：改的若是**页 flag**（唯一派生触发键），**必须在重渲染之前**跑一次派生 ——
         与产品切页同口径：`config_tab_1` / `config_tab_2` 动作内部调的就是这个函数
         （captureMemo 缺省 = 先捕获切页记忆 ⇒ 回页时能按三级优先链把本页的值取回来）。
         不先派生就会先重渲染出一屏「未派生的中间态」（另一页的值元素残留）。
         改其它 flag（如手选 `cfg_v_display=full` 做单项探查）**不触发派生**，见
         applyFlagsMode 里的说明。 */
      if (ED.flagPreview && n === PAGE_FLAG) {
        R.setFlag(n, ED.flagVals[n]);                   // replica 的页 flag 先跟上，再派生
        R.configDerivePageFlags(ED.flagVals[n]);
        readBackFlagVals();
        ED.derivedPage = flagVal(PAGE_FLAG);
      }
      /* refreshAll 内含 refreshFlags ⇒ 预览条按（派生后的）值重建：非本页的值键下拉显示「（空）」 */
      reRender(); refreshAll();
      return ED.flagVals[n];
    }
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
    /* ★ M3 自检钩子：?fp=1 开「按 flag 预览」，`?flags=<名>:<值>[,…]` 指定各 flag 取值
       （与复刻页 index.html 的 ?flags= 同格式）。供无头截图验收两种状态。 */
    var fpm = /[?&]fp=1/.test(location.search || '');
    var fvm = /[?&]flags=([^&#]*)/.exec(location.search || '');
    if (fvm && fvm[1]) {
      String(fvm[1]).split(',').forEach(function (kv) {
        var i = kv.indexOf(':');
        var n = (i < 0 ? kv : kv.slice(0, i)).trim();
        if (!n) return;
        ED.flagVals[n] = (i < 0 ? '' : kv.slice(i + 1).trim());
      });
    }
    if (fpm) ED.flagPreview = true;
    if (fpm || (fvm && fvm[1])) { syncFlagVals(); reRender(); refreshAll(); }
    setTimeout(function () { syncOverlay(); drawGrid(); }, 60);
    setTimeout(function () { syncOverlay(); drawGrid(); }, 300);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
