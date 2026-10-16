
(function () {
  var log = [], fails = 0;
  function say(ok, name, detail) {
    if (!ok) fails++;
    log.push((ok ? 'SELFTEST OK   ' : 'SELFTEST FAIL ') + name + (detail ? '  —— ' + detail : ''));
  }
  /* 取某元素当前实际用的贴图文件名。★ M35b：带态图的 `image` 把贴图挂在**内层节点**上
     （`.ui-stateimage` 走 background-image、`.ui-nine` 走 border-image），
     热区/inline 元素才挂在外层 —— 故内外都看一遍，否则 image 一律读成「(无)」，
     ⑥ 那几条断言会**假通过**（v1 实测：文字列恒为「(无)」，比不出差异）。
     ★ M46：list 的**逐项**态图挂在 `.ui-list-item-frame`（同样是内层节点），一并纳入。 */
  function curAsset(d) {
    var inner = d.querySelector
      ? (d.querySelector('.ui-stateimage') || d.querySelector('.ui-nine') || d.querySelector('.ui-list-item-frame'))
      : null;
    var n = inner || d;
    var s = n.style.backgroundImage || n.style.borderImageSource || '';
    var m = /url\("?([^")]+)"?\)/.exec(s);
    return m ? decodeURIComponent(m[1]).replace(/^.*\//, '') : '(无)';
  }
  /* ================= 通用：三态图名一律**从 ui_layout.js 的数据推** =================
     ★ ISSUE-20260927-02：本文件不得写死任何素材文件名。
     回落链与 replica.js 的 `setFrame` / krkr 的 `uiWidgetItemFrameAsset` **逐字一致**：
         pressed > hover > normal > asset（缺键逐级回落）。
     `sub`：list 的逐项态图挂在 `item_frame` 下 ⇒ 传 'item_frame'；元素级（image/hit）不传。 */
  function basename(p) { return String(p || '').replace(/^.*\//, ''); }
  function elemOf(screenId, elemId) {
    var sc = (window.UI_LAYOUT.screens || {})[screenId];
    if (!sc || !sc.elements) return null;
    for (var i = 0; i < sc.elements.length; i++)
      if (sc.elements[i].id === elemId) return sc.elements[i];
    return null;
  }
  function statesOf(elem, sub) {
    var host = (sub && elem) ? (elem[sub] || {}) : (elem || {});
    var sa = host.state_assets || {};
    var base = host.asset || (elem ? elem.asset : '');
    return {
      normal: basename(sa.normal || base),
      hover: basename(sa.hover || sa.normal || base),
      pressed: basename(sa.pressed || sa.hover || sa.normal || base)
    };
  }

  /* ================= 通用：素材**存在性**清单（独立锚点） =================
     ★ 期望素材名从数据推 ⇒ 单比「DOM == 数据」是**对称**的：数据指向一个不存在的文件时
     两边一起错、断言恒真。故补一条与数据无关的锚点：文件必须在 `复刻\asset_index.js`
     （工具\emit_asset_index.py 生成的素材清单）里 ⇒ 「数据改成不存在的素材」能报警。
     清单缺失 ⇒ **判失败并明示**（不静默降级成"无规范可依"）。 */
  var ASSET_SET = (function () {
    var idx = window.UI_ASSET_INDEX, s = {};
    if (idx && idx.items) for (var i = 0; i < idx.items.length; i++) s[idx.items[i].n] = 1;
    return s;
  })();
  function assetExists(n) { return !!n && ASSET_SET[n] === 1; }
  function assetCount() { return Object.keys(ASSET_SET).length; }
  /* 素材池里任取一件（排除 exclude）—— 供「注入互异态图」的探针用，避免写死素材名。 */
  function anyAssetExcept(exclude) {
    var ks = Object.keys(ASSET_SET);
    for (var i = 0; i < ks.length; i++) if (exclude.indexOf(ks[i]) < 0) return ks[i];
    return '';
  }

  /* ================= 通用：数据侧守卫（存在性 + 区分力） =================
     mode：'none' 只查存在性；'hover' 另要求 normal ≠ hover；'all' 另要求三态两两互异。
     ★ 为什么需要「区分力」这一条：断言是「DOM == 数据里那张图」——
     若数据把常态与悬停折叠成同一张，断言恒真、**看起来全绿却什么都没验**。
     这正是本文件历史上栽过的坑（⑳m 注释里的"修空断言"），故把它显式判成失败。 */
  function stateGuard(label, pairs, mode) {
    if (!ASSET_SET || assetCount() === 0) {
      say(false, label, '素材清单 asset_index.js 未加载 / 为空 ⇒ 存在性无从判（不得静默放过）');
      return;
    }
    var bad = [], seen = [];
    pairs.forEach(function (p) {
      var s = statesOf(p.elem, p.sub);
      ['normal', 'hover', 'pressed'].forEach(function (k) {
        if (!assetExists(s[k])) bad.push((p.elem ? p.elem.id : '?') + '.' + k + '="' + (s[k] || '(空)') + '" 不在素材清单');
      });
      if (mode === 'hover' && s.normal === s.hover) {
        bad.push((p.elem ? p.elem.id : '?') + '：normal 与 hover 同为 "' + s.normal + '" ⇒ 悬停断言恒真（失去区分力）');
      }
      if (mode === 'all') {
        if (s.normal === s.hover) bad.push(p.elem.id + '：normal == hover（' + s.normal + '）');
        if (s.pressed === s.hover) bad.push(p.elem.id + '：pressed == hover（' + s.pressed + '）⇒ 按下断言恒真');
        if (s.pressed === s.normal) bad.push(p.elem.id + '：pressed == normal（' + s.pressed + '）⇒ ② 抬起复位恒真');
      }
      seen.push((p.elem ? p.elem.id : '?') + '=' + s.normal + '/' + s.hover + '/' + s.pressed);
    });
    say(bad.length === 0, label,
      bad.length ? bad.slice(0, 4).join('；')
        : ('三态均在清单（' + assetCount() + ' 件）' + (mode === 'none' ? '' : '且区分力达标') + '：' + seen.join('，')));
  }

  /* ================= 负向对照开关 `?mut=<mode>`（默认 "" = 线上路径一字不改）=================
     ★ ISSUE-20260927-02：复现脚本 `m02_mut_selftest_A.py` 用它在**内存里**把数据改坏，
     证明修好后的断言**仍能报警**（与 ⑳m / ⑳n 的"内存副本"惯用法同源，不写磁盘）：
       missing    数据 state_assets 指向**不存在的素材**    ⇒ 存在性守卫必须 FAIL
       foldhover  数据删掉 hover（回落常态）                 ⇒ 区分力守卫必须 FAIL
       swap       对调 hover / normal（**合法重映射**，见 36_choices.json 的 note
                  「若日后判定"粉＝常态、蓝紫＝悬停"，只改本字段三者映射即可」）⇒ 必须 PASS
       drift      **渲染之后**再改数据（DOM 与数据脱钩）      ⇒ 比较类断言必须 FAIL
       expect     期望值恢复成**修前那组写死的素材名**        ⇒ 复现修前的 10 项 FAIL（回归夹具）
     ★ 口径说明：期望值从数据推 ⇒ **数据本身改动不该 FAIL**（那正是本修复的目的）；
     能报警的对象是「数据 × 机制/素材存在性/期望口径」不一致。 */
  var MUT = (function () {
    var m = /[?&]mut=([A-Za-z0-9_]+)/.exec(window.location.search);
    return m ? m[1].toLowerCase() : '';
  })();
  var MUT_DONE = {};
  function noteMut(step, detail) {
    if (!MUT || MUT_DONE[step]) return;
    MUT_DONE[step] = 1;
    log.push('SELFTEST NOTE ⚠ 负向对照 ?mut=' + MUT + ' · ' + step + ' —— ' + detail);
  }
  /* 在**渲染前**改坏数据（missing / foldhover / swap） */
  function mutPre(el) {
    var sa = el && el.item_frame && el.item_frame.state_assets;
    if (!MUT || !sa) return;
    if (MUT === 'missing') { sa.normal = 'ui/__mut_no_such_asset__.png'; noteMut('pre', 'state_assets.normal 改指不存在的文件'); }
    else if (MUT === 'foldhover') { delete sa.hover; noteMut('pre', 'state_assets.hover 已删除（回落常态）'); }
    else if (MUT === 'swap') { var t = sa.normal; sa.normal = sa.hover; sa.hover = t; noteMut('pre', 'hover 与 normal 已对调'); }
  }
  /* 在**渲染后**改坏数据（drift）：DOM 保持旧图、数据已变 ⇒ 比较类断言必须报错 */
  function mutPost(el) {
    var sa = el && el.item_frame && el.item_frame.state_assets;
    if (MUT !== 'drift' || !sa || MUT_DONE.drift) return;
    MUT_DONE.drift = 1;
    sa.normal = anyAssetExcept([basename(sa.normal), basename(sa.hover), basename(sa.pressed)]);
    noteMut('post', 'state_assets.normal 已在渲染后改为 ' + sa.normal + '（DOM 未重渲染）');
  }
  function fire(d, type, props) {
    var p = { bubbles: true, cancelable: true, view: window, button: 0, buttons: 1 };
    if (props) for (var k in props) p[k] = props[k];
    d.dispatchEvent(new MouseEvent(type, p));
  }

  function run() {
    var doc = document;
    if (!window.UI_REPLICA || !window.UI_LAYOUT) { say(false, '前置', 'UI_REPLICA/UI_LAYOUT 未加载'); return done(); }
    /* ★ ISSUE-20260927-02：负向对照模式一律先打一条 NOTE —— 防止把「有意改坏」的运行
       误读成正常结果（NOTE 不参与 PASS/FAIL 计数，但会出现在 grep SELFTEST 的输出里）。 */
    noteMut('mode', '本页数据/期望值被**有意改坏**，仅用于证明断言仍有牙齿；正常回归请不带 ?mut= 运行');

    /* ★ M46：①–⑤ 的被测元素**回到「元素级」主语** `title.menu_txt_start`
       （`image`，三态互不相同：`x_ui_btntxt2c_start.png` / `_on` / `_press`）。
       ★ 为什么必须回到元素级（一审 Major-3 打回后改）：M46 初版把 ①–⑤ 整体迁到了
         **列表项**上 —— 于是「元素级按下路径」在全套自检里**一条断言都不剩**。
         变异实验坐实了后果：把元素级 `attachStateEvents` 的左键分支整条打废
         （全库 34 件元素级态图元素一起失效），套 A 仍报 ALL PASS。
       列表项自己的三态在 **⑱a–⑱j** 里另有十条断言（逐项、隔离性、台账兜底），两者并存。 */
    window.UI_REPLICA.renderScreen('title');
    var d = doc.querySelector('[data-ui-id="title.menu_txt_start"]');
    /* ★ ISSUE-20260927-02：三态图名**从数据推**（原为写死 `x_ui_btntxt2c_start[_on|_press].png`）。
       本段主语是「元素级 image、三态互不相同」的元素 —— mode:'all' 要求三态两两互异，
       否则 ①②③⑤ 四条迁移断言里必有一条恒真（失去区分力）。 */
    var sel5 = elemOf('title', 'title.menu_txt_start');
    var st5 = statesOf(sel5);
    var NORMAL = st5.normal, HOVER = st5.hover, PRESS = st5.pressed;
    if (!sel5) {
      say(false, '①–⑤ 取数据侧主语 title.menu_txt_start', 'ui_layout.js 里没有该元素 ⇒ 期望值无从推');
    } else {
      stateGuard('①–⑤ 数据侧守卫：三态素材须存在、且三态互异（否则迁移断言恒真）',
        [{ elem: sel5 }], 'all');
    }
    if (!d) {
      /* ★ 一审建议：主语缺失时**记失败但继续跑**，不要 `return done()` ——
         否则「一个主语缺失 = 整套 40+ 条断言静默空转」（M45f 那轮就是这样漏过套 A 的）。 */
      say(false, '取元素级主语 title.menu_txt_start', '没找到 ⇒ ①–⑤ 跳过（其余断言继续）');
    } else {
      say(curAsset(d) === NORMAL, '初态 = normal', curAsset(d));

      /* 规则 ① 按下 -> pressed */
      fire(d, 'mousedown');
      say(curAsset(d) === PRESS, '① 左键按下 -> pressed', curAsset(d));

      /* 规则 ② **抬起复位**（旧实现漏掉的正是这条：不派发 mouseleave，只在元件内抬起） */
      fire(d, 'mouseup');
      say(curAsset(d) !== PRESS, '② 元素内抬起 -> 离开 pressed（本 bug 的正身）', curAsset(d));

      /* 规则 ② 兜底：在**元件外**抬起（元素上接不到）也要复位 —— 由 document 的 mouseup 兜底 */
      fire(d, 'mousedown');
      var before = curAsset(d);
      fire(doc, 'mouseup');                       // 派给 document，不经元素
      say(before === PRESS && curAsset(d) !== PRESS, '② document 抬起兜底复位', before + ' -> ' + curAsset(d));

      /* 规则 ② 回归：只按下、不抬起，必须**保持** pressed（别把"保持"一起修没了） */
      fire(d, 'mousedown');
      say(curAsset(d) === PRESS, '② 按住期间保持 pressed', curAsset(d));
      fire(d, 'mouseup');

      /* 规则 ③ 按住期间移出 -> 取消 */
      fire(d, 'mousedown');
      fire(d, 'mouseleave', { buttons: 1 });
      say(curAsset(d) !== PRESS, '③ 按住移出 -> 取消按下态', curAsset(d));

      /* 规则 ①+⑤ 同时悬停与按下 -> pressed 优先 */
      fire(d, 'mouseenter');
      var hovOnly = curAsset(d);
      fire(d, 'mousedown');
      say(hovOnly === HOVER && curAsset(d) === PRESS, '⑤ pressed 优先于 hover', hovOnly + ' -> ' + curAsset(d));
      fire(d, 'mouseup');
      say(curAsset(d) === HOVER, '⑤ 抬起后回落 hover（仍在悬停）', curAsset(d));
      fire(d, 'mouseleave');
      say(curAsset(d) === NORMAL, '⑤ 移出后回落 normal', curAsset(d));
      say(curAsset(d) === NORMAL, '初态 = normal（收尾）', curAsset(d));
    }

    /* 规则 ④ 换屏 -> 清除（台账不能指向已销毁的节点）
       ★ 措辞订正（M35b 一审）：这条只证明 pressHolder 的宿主节点已从 DOM 移除；
         对**组注册表 stateGroups** 并不成立——那要靠下面的规则 ⑥ 回归来钉。 */
    if (d) {
      fire(d, 'mousedown');
      var pressedNow = curAsset(d) === PRESS;
      window.UI_REPLICA.renderScreen('config');
      var d2 = doc.querySelector('[data-ui-id="title.menu_txt_start"]');
      say(pressedNow && !d2, '④ 换屏后旧节点已销毁（pressHolder 随之复位）',
          '旧元素在 DOM 中=' + (d2 ? '仍在' : '已移除'));
    }

    /* ================= 规则 ⑥ 组绑定（M35b 一审打回后补） =================
       用**真实带 state_group 的数据**（标题屏 title.menu_start 组 = 图标 hit + 文字 image），
       这条同时是对「注册表跨代泄漏导致悬停永久不灭」那个 Critical 的回归。 */
    window.UI_REPLICA.renderScreen('title');
    var g1 = doc.querySelector('[data-ui-id="title.menu_hit_1"]');       // 图标（hit）
    var g2 = doc.querySelector('[data-ui-id="title.menu_txt_start"]');   // 文字（image）
    var other = doc.querySelector('[data-ui-id="title.menu_hit_2"]');    // 另一组，作对照
    if (!g1 || !g2) {
      say(false, '⑥ 取组内两件元素', '找不到 title.menu_hit_1 / title.menu_txt_start');
    } else {
      var N1 = curAsset(g1), N2 = curAsset(g2), NO = other ? curAsset(other) : '(无)';
      /* ⑥-a 悬停图标 -> 文字同步换态 */
      fire(g1, 'mouseenter');
      var h1 = curAsset(g1), h2 = curAsset(g2);
      say(h1 !== N1 && h2 !== N2, '⑥a 悬停**图标** -> 图标与文字同步换态',
          '图标 ' + N1 + '→' + h1 + ' ｜ 文字 ' + N2 + '→' + h2);
      /* ⑥-b 换成悬停文字（先把上面那件移出），结果必须与 ⑥-a 完全一致 */
      fire(g1, 'mouseleave');
      var afterLeave = curAsset(g2) === N2;
      fire(g2, 'mouseenter');
      say(afterLeave && curAsset(g1) === h1 && curAsset(g2) === h2,
          '⑥b 悬停**文字** -> 与悬停图标结果逐项相同',
          '图标 ' + curAsset(g1) + ' ｜ 文字 ' + curAsset(g2));
      /* ⑥-c 别的组不受影响 */
      say(other ? curAsset(other) === NO : true, '⑥c 其它组不受影响', '另一组 = ' + NO);
      fire(g2, 'mouseleave');
      say(curAsset(g1) === N1 && curAsset(g2) === N2, '⑥d 移出后全组回落常态',
          '图标 ' + curAsset(g1) + ' ｜ 文字 ' + curAsset(g2));

      /* ⑥-e ★ 跨渲染代际回归（原 Critical 的复现路径）：
         在**悬停状态下**换屏（旧 DOM 在指针下被销毁，浏览器不发 mouseleave）再回来，
         然后悬停再移出 —— 必须回落常态，不能永久停住。 */
      fire(g1, 'mouseenter');                       // 先悬停
      window.UI_REPLICA.renderScreen('config');     // 悬停中换屏（旧节点被 innerHTML='' 移除）
      window.UI_REPLICA.renderScreen('title');      // 回到标题
      var r1 = doc.querySelector('[data-ui-id="title.menu_hit_1"]');
      var r2 = doc.querySelector('[data-ui-id="title.menu_txt_start"]');
      fire(r1, 'mouseenter'); fire(r1, 'mouseleave');   // 悬停再移出
      var s1 = curAsset(r1), s2 = curAsset(r2);
      say(s1 === N1 && s2 === N2,
          '⑥e 悬停中换屏再回来 -> 悬停移出后仍能回落常态（原 Critical 的回归）',
          '图标 ' + s1 + ' ｜ 文字 ' + s2);
    }

    /* ================= 规则 ⑦：被遮挡的交互元素兜底（M35b 修 Major-3） =================
       标题屏的菜单文字图（z 96..102）压在图标热区（z 95）之上、两者重叠 12px。
       在重叠带点击必须与实机一致（触发动作），不能是死区 —— 原先 HTML 会被文字图吞掉。 */
    window.UI_REPLICA.renderScreen('title');
    var img7 = doc.querySelector('[data-ui-id="title.menu_txt_start"]');
    var hit7 = doc.querySelector('[data-ui-id="title.menu_hit_1"]');
    if (!img7 || !hit7) {
      say(false, '⑦ 取标题屏图标与文字', '找不到 title.menu_hit_1 / title.menu_txt_start');
    } else {
      var hr = hit7.getBoundingClientRect(), ir = img7.getBoundingClientRect();
      var bx0 = Math.max(hr.left, ir.left), bx1 = Math.min(hr.right, ir.right);
      var by0 = Math.max(hr.top, ir.top), by1 = Math.min(hr.bottom, ir.bottom);
      var ow = Math.round(bx1 - bx0), oh = Math.round(by1 - by0);
      var cx = (bx0 + bx1) / 2, cy = (by0 + by1) / 2;
      /* ★ M3 订正：本页在无头默认视口（756×472）下由 replica 的 fitScale 自动缩放到
         ≈0.372 倍，故设计稿里 12 画布 px 的重叠带在这里只有 **4 设备 px**；旧判据
         `ow > 4` 恰好卡死在取整下界上 ⇒ 该断言长期假失败（实测 ow=4/oh=36）。
         阈值改为「≥ 4 设备 px（≈12 画布 px）」，语义不变（重叠带确实存在）。 */
      say(ow >= 4 && oh >= 4, '⑦ 重叠带确实存在（前置）', ow + '×' + oh);
      var sc0 = window.UI_REPLICA.state.screen;
      try {
        img7.dispatchEvent(new MouseEvent('click',
          { bubbles: true, cancelable: true, view: window, button: 0, clientX: cx, clientY: cy }));
      } catch (e) {}
      var sc1 = window.UI_REPLICA.state.screen;
      say(sc0 === 'title' && sc1 !== 'title',
          '⑦ 重叠带点击 -> 触发动作（原为死区；实机本来就会触发）', sc0 + ' → ' + sc1);
    }

    /* ============ 规则 ⑱：list **逐项**三态（★ M46 · 用户指令「让现在选择支能有三态效果」）============
       被测行为：`item_frame.state_assets` 存在时，每个列表项**各自**独立换图 ——
         悬停/按住哪一项，就只换那一项；邻项与常态不变。
       ★ 这条断言的存在理由：M45f 把本屏换成 list 时，**逐项态图整体丢失**（当时如实登记为
         「取舍」），M46 恢复后必须有自动断言钉住——否则下次再改渲染器会静默回归。
       ★ 与 krkr 侧的关系：krkr 由 `ctx.hoverIndex/pressIndex` 逐项选图（巡演里的
         `ch.choices:1` / `ch.choices:2:press` 合成指针步骤做同一件事），两端**同判据**。 */
    (function () {
      /* ★ ISSUE-20260927-02：本段**不写死任何素材名** —— 三态图名一律从 `ui_layout.js` 的
         `ch.choices`（list）经回落链推出（`item_frame.state_assets`，口径见文件头 statesOf）。
         修前此处写死 `x_ui_choice_off/over/press.png`，而 PSV 换皮（ISSUE-20260926-06）后
         数据已改为 `x_ui_psv_choice_norm/sel.png` ⇒ 断言主语与数据脱钩、在 HEAD 上恒 FAIL 10 项。 */
      var chEl = elemOf('choices', 'ch.choices');
      if (!chEl) { say(false, '⑱ 取数据侧主语 ch.choices', 'ui_layout.js 里没有 ch.choices'); return; }
      mutPre(chEl);                                     /* 负向对照（默认空操作，见 MUT 注释） */
      var st18 = statesOf(chEl, 'item_frame');
      var NORMAL = st18.normal, HOVER = st18.hover, PRESS = st18.pressed;
      /* ★ 为何 mode:'hover' 而不是 'all'：现行数据把 hover 与 pressed **折叠成同一张图**
         （PSV 只给两态、主代理 2026-09-26 口径），这是**合法取舍**；但常态与悬停必须可分辨，
         否则逐项悬停断言恒真 ⇒ 判失败。按下优先于悬停的**机制**牙齿由下面的 ⑱e2 注入探针保证。 */
      stateGuard('⑱ 数据侧守卫：三态素材须存在、常态 ≠ 悬停（否则逐项三态断言恒真）',
        [{ elem: chEl, sub: 'item_frame' }], 'hover');
      if (MUT === 'expect') {
        /* 回归夹具：把期望值退回**修前那组写死的素材名** ⇒ 必须复现修前的 10 项 FAIL。 */
        NORMAL = 'x_ui_choice_off.png'; HOVER = 'x_ui_choice_over.png'; PRESS = 'x_ui_choice_press.png';
      }
      window.UI_REPLICA.renderScreen('choices');
      mutPost(chEl);                                    /* drift：渲染后再改数据（DOM 脱钩） */
      var items = doc.querySelectorAll('[data-ui-id="ch.choices"] [data-ui-kind="list-item"]');
      var listEl = chEl;
      var want = listEl.labels ? listEl.labels.length : -1;
      say(items.length === want && want > 0,
          '⑱a 列表项数 == layout 标签数（项数自适应，不写死 3）',
          'DOM ' + items.length + ' 项 / layout ' + want + ' 项');
      if (items.length < 3) { say(false, '⑱ 需要 ≥3 项才能验"只换一项"', items.length + ' 项'); return; }

      function assets() {
        var out = [];
        for (var k = 0; k < items.length; k++) out.push(curAsset(items[k]));
        return out;
      }
      var isc = items[0].getAttribute('data-ui-item-states') === '1';
      say(isc, '⑱b 每项都带 data-ui-item-states=1（探针可识别）',
          items[0].getAttribute('data-ui-item-states'));
      var a0 = assets();
      var allNormal = a0.every(function (a) { return a === NORMAL; });
      say(allNormal, '⑱c 初态：所有项都是 normal', a0.join(' | '));

      /* 悬停第 2 项 -> 只有第 2 项换 hover */
      fire(items[1], 'mouseenter');
      var a1 = assets();
      say(a1[1] === HOVER && a1[0] === NORMAL && a1[2] === NORMAL,
          '⑱d 悬停第 2 项 -> **仅第 2 项**换 hover（邻项不动）', a1.join(' | '));

      /* 同项按下 -> pressed 优先 */
      fire(items[1], 'mousedown');
      var a2 = assets();
      say(a2[1] === PRESS && a2[0] === NORMAL && a2[2] === NORMAL,
          '⑱e 第 2 项按下 -> 仅该项 pressed', a2.join(' | '));

      /* 项内抬起 -> 回落 hover（指针仍在项上） */
      fire(items[1], 'mouseup');
      say(assets()[1] === HOVER, '⑱f 项内抬起 -> 回落 hover（仍在悬停）', assets().join(' | '));

      /* document 抬起兜底：按下后移出项，在文档层抬起 —— 不得粘住 pressed */
      fire(items[2], 'mousedown');
      var press3 = assets()[2] === PRESS;
      fire(doc, 'mouseup');
      var a3 = assets();
      say(press3 && a3[2] === NORMAL && a3[1] === HOVER,
          '⑱g 第 3 项按住 -> document 抬起兜底复位（且不影响第 2 项的悬停）', a3.join(' | '));

      /* 移出第 2 项 -> 全回常态 */
      fire(items[1], 'mouseleave');
      var a4 = assets();
      say(a4.every(function (a) { return a === NORMAL; }), '⑱h 移出后全部回落 normal', a4.join(' | '));

      /* 按下期间移出 -> 取消（规则③的逐项版） */
      fire(items[2], 'mousedown');
      var p2 = assets()[2] === PRESS;
      fire(items[2], 'mouseleave', { buttons: 1 });
      say(p2 && assets()[2] === NORMAL, '⑱i 按住第 3 项期间移出 -> 取消按下态（规则③逐项版）',
          assets().join(' | '));

      /* ★ ⑱k（一审 Major-1 的回归）：**右键**不得让该项进入按下态 ——
         元素级只认左键（replica.js 的 `if (ev.button !== 0) return`），逐项同一口径；
         修前实现会把右键点中的项**钉**在 pressed 直到指针移出（引擎侧不会）。 */
      fire(items[0], 'mouseenter');
      fire(items[0], 'mousedown', { button: 2, buttons: 2 });
      var rBtn = assets();
      say(rBtn[0] === HOVER && rBtn[1] === NORMAL,
          '⑱k 右键按下不得置 pressed（项保持 hover）', rBtn.join(' | '));
      fire(items[0], 'mouseup', { button: 2, buttons: 0 });

      /* ★ ⑱l（一审 Major-2 的回归）：按住左键**移出该项**⇒ 取消按下态（规则 ③ 逐项版）；
         拖到相邻项只显示 hover，**不**把按下态带过去（按下态锚定在被按的那一项）。
         引擎侧同一收口：按下时锁存项序号，指针移到别项即清（见 ui_screens.tjs）。 */
      fire(items[0], 'mouseenter');
      fire(items[0], 'mousedown', { buttons: 1 });
      fire(items[0], 'mouseleave', { button: 0, buttons: 1 });
      fire(items[1], 'mouseenter', { button: 0, buttons: 1 });
      var drag = assets();
      say(drag[0] === NORMAL && drag[1] === HOVER && drag[2] === NORMAL,
          '⑱l 按住拖到相邻项 → 按下态被取消、新项只显示 hover（不跟随指针）', drag.join(' | '));
      fire(items[1], 'mouseleave', { button: 0, buttons: 1 });
      fire(doc, 'mouseup');
      say(assets().every(function (a) { return a === NORMAL; }),
          '⑱l 拖拽结束后全回 normal（台账无悬挂）', assets().join(' | '));

      /* ★ ISSUE-20260927-02 · ⑱e2「⑤ 阶梯」探针（内存注入，不写磁盘；与 ⑳m 同惯用法）：
         出厂数据把 hover 与 pressed **折叠成同一张图**（PSV 只给两态）⇒
         「按下优先于悬停」在出厂数据上**不可分**（⑱e 只能证明"变成了那张选中图"）。
         这是数据的取舍、不是机制的缺陷，但会让该规则**失去牙齿**。故这里临时给 hover / pressed
         各注入一张**互异且确实存在**的素材（从素材清单里取，不写死名字），逐格验阶梯：
         常态 → 悬停 → 按下 → 抬起(回悬停) → 移出(回常态)；断言完**还原数据并重渲染**。 */
      (function () {
        var Hv = anyAssetExcept([NORMAL, HOVER, PRESS]);
        var Pv = anyAssetExcept([NORMAL, HOVER, PRESS, Hv]);
        if (!Hv || !Pv || !chEl.item_frame || !chEl.item_frame.state_assets) {
          say(false, '⑱e2 前置：素材池另有两件可注入的素材 + 数据带 state_assets',
            'Hv=' + (Hv || '(无)') + ' Pv=' + (Pv || '(无)'));
          return;
        }
        var keep18 = chEl.item_frame.state_assets;
        chEl.item_frame.state_assets = { normal: NORMAL, hover: Hv, pressed: Pv };
        RPC.renderScreen('choices');
        var it2 = doc.querySelectorAll('[data-ui-id="ch.choices"] [data-ui-kind="list-item"]');
        var c0 = curAsset(it2[1]);
        fire(it2[1], 'mouseenter');
        var c1 = curAsset(it2[1]);
        fire(it2[1], 'mousedown');
        var c2 = curAsset(it2[1]);
        fire(it2[1], 'mouseup');
        var c3 = curAsset(it2[1]);
        fire(it2[1], 'mouseleave');
        var c4 = curAsset(it2[1]);
        say(c0 === NORMAL && c1 === Hv && c2 === Pv && c3 === Hv && c4 === NORMAL && Hv !== Pv,
            '⑱e2 ⑤阶梯探针（注入互异 hover/pressed）：常态→悬停→按下→抬起→移出 逐格正确（按下优先于悬停）',
            c0 + ' → ' + c1 + ' → ' + c2 + ' → ' + c3 + ' → ' + c4
            + '（注入 hover=' + Hv + ' pressed=' + Pv + '）');
        chEl.item_frame.state_assets = keep18;          /* 还原（内存，不写盘） */
        RPC.renderScreen('choices');
      })();

      /* 无态图的 list（对话框内联 `dlg.choices`）不得受影响：不注册逐项事件、不换图 */
      window.UI_REPLICA.renderScreen('dialog');
      var dl = doc.querySelector('[data-ui-id="dlg.choices"]');
      if (!dl) { say(false, '⑱j 取 dlg.choices', '没找到'); return; }
      var its = dl.querySelectorAll('[data-ui-kind="list-item"]');
      say(its.length > 0 && its[0].getAttribute('data-ui-item-states') === null,
          '⑱j 无 item_frame.state_assets 的 list 不注册逐项态（回归：老列表行为不变）',
          its.length + ' 项，首项 data-ui-item-states=' + its[0].getAttribute('data-ui-item-states'));
    })();

    /* ============ 规则 ⑧–⑯：右端竖排快捷条（M3 · ISSUE-20260922-28） ============
       被测行为与 krkr 侧 M2 同契约（`layout/_schema.md` §四「屏级状态 flag」）：
       附加层 attach、贴边呼出、延时收起、钉住、气泡、动作派发。

       ★ 假计时（本段专用）：把 window.setTimeout / clearTimeout 换成探针，以便**同步**
         断言「移到 x<out_x 只起计时、回到 x≥in_x 撤销计时、延时到期才收起」——
         手动触发被捕获的回调即等价于「延时到期」，无需真的等 delay_ms。
         阈值/延时一律从 `ui_layout.js` 的 `reveal` 读，本文件不写死任何数值。
         断言跑完（done 前）必须 restoreTimers()，否则会污染后续页面行为。 */
    var realST = window.setTimeout, realCT = window.clearTimeout;
    var timers = {}, timerSeq = 900000, clearedIds = [];
    window.setTimeout = function (fn, ms) { var id = ++timerSeq; timers[id] = { fn: fn, ms: ms }; return id; };
    window.clearTimeout = function (id) { delete timers[id]; clearedIds.push(id); };
    function pendings(ms) {
      return Object.keys(timers).filter(function (k) { return timers[k].ms === ms; }).map(Number);
    }
    function fireTimer(id) { var t = timers[id]; delete timers[id]; if (t) t.fn(); }
    function restoreTimers() { window.setTimeout = realST; window.clearTimeout = realCT; }

    var RPC = window.UI_REPLICA, LAY = window.UI_LAYOUT, CV = LAY.canvas;
    var QB = LAY.screens.quickbar, RV = QB.reveal, DELAY = RV.delay_ms;
    function qbBox(id) {
      for (var i = 0; i < QB.elements.length; i++) if (QB.elements[i].id === id) return QB.elements[i];
      return null;
    }
    function midOf(id) {
      var e = qbBox(id);
      return e ? { x: Number(e.x) + Number(e.w) / 2, y: Number(e.y) + Number(e.h) / 2 } : null;
    }
    function clientOf(x, y) {                       // 画布坐标 → 视口坐标（含自动缩放）
      var r = doc.getElementById('canvas').getBoundingClientRect();
      return { x: r.left + x * (r.width / CV.width), y: r.top + y * (r.height / CV.height) };
    }
    function mv(x, y) {                             // 派发一次真实 mousemove（走 replica 的画布监听）
      var p = clientOf(x, y);
      doc.getElementById('canvas').dispatchEvent(new MouseEvent('mousemove',
        { bubbles: true, cancelable: true, view: window, clientX: p.x, clientY: p.y }));
    }
    function leaveCanvas() {
      doc.getElementById('canvas').dispatchEvent(new MouseEvent('mouseleave',
        { bubbles: false, cancelable: true, view: window }));
    }
    function topAt(x, y) {                          // 真实命中栈里最上面的交互元素（含被遮挡者）
      var p = clientOf(x, y);
      var st = doc.elementsFromPoint(p.x, p.y) || [];
      for (var i = 0; i < st.length; i++) {
        var n = st[i].closest && st[i].closest('[data-ui-interactive]');
        if (n) return n;
      }
      return null;
    }
    function nodeOf(id) { return doc.querySelector('[data-ui-id="' + id + '"]'); }
    function flagOf(n) { return RPC.getFlag(n); }

    /* ⑧ 附加层只挂在承载屏上：dialog 有、title 没有（★ M37：主语由「整条/把手/高面板」
       换成新形态的四件代表 —— 圆形 icon / 项热区 / 钉住叠层 / 名称药丸）。 */
    RPC.renderScreen('dialog', { noHistory: true });
    var qbIcon = nodeOf('quick.ic_lock'), qbHit = nodeOf('quick.hit_lock'),
        qbPin = nodeOf('quick.pin_mark'), qbPill = nodeOf('quick.pl_lock');
    RPC.renderScreen('title', { noHistory: true });
    var onTitleIcon = nodeOf('quick.ic_lock');
    RPC.renderScreen('dialog', { noHistory: true });
    qbIcon = nodeOf('quick.ic_lock'); qbHit = nodeOf('quick.hit_lock');
    qbPin = nodeOf('quick.pin_mark'); qbPill = nodeOf('quick.pl_lock');
    say(!!qbIcon && !!qbHit && !!qbPin && !!qbPill && !onTitleIcon
        && RPC.attachScreen() === 'quickbar',
        '⑧ 附加层只在 dialog 上出现（title 上不出现）',
        'dialog: icon/hit/pin/pill=' + (!!qbIcon) + '/' + (!!qbHit) + '/' + (!!qbPin)
        + '/' + (!!qbPill) + '，attachScreen=' + RPC.attachScreen()
        + '；title: icon=' + !!onTitleIcon);

    /* ⑧b ★ M37：旧结构（展开整条 `quick.btn` / slim 把手 `quick.tgl` / 高面板 `quick.tips` /
       整条把手热区 `quick.hit_toggle`）**必须不得复活** —— 数据里没有、DOM 里也没有。 */
    var oldLeft = ['quick.btn', 'quick.tgl', 'quick.tips', 'quick.hit_toggle'].filter(function (id) {
      return nodeOf(id) !== null || qbBox(id) !== null;
    });
    say(oldLeft.length === 0,
        '⑧b M37 退场四件（整条/把手/高面板/整条把手热区）均不在数据与 DOM 中',
        oldLeft.length ? '仍在：' + oldLeft.join('、') : '四件全部已退场 ✓');

    /* ⑨ 初始态 = 收起：**整列一个元素都不绘制**（12 icon + 12 药丸 + 12 白字 + 12 项热区） */
    var hides = 0, expected = 0, vhits = 0;
    QB.elements.forEach(function (e) {
      if (!e.vis_flag || String(e.vis_flag) !== 'quickbar') return;
      expected++;
      var n = nodeOf(e.id);
      if (n && n.style.display === 'none') hides++;
    });
    QB.elements.forEach(function (e) {
      if (String(e.id).indexOf('.hit_') < 0) return;
      var n = nodeOf(e.id);
      if (n && n.style.display !== 'none') vhits++;
    });
    var allHidden = QB.elements.every(function (e) {
      var n = nodeOf(e.id);
      return !n || n.style.display === 'none';
    });
    say(flagOf('quickbar') === 'collapsed' && allHidden && vhits === 0 && expected === 24,
        '⑨ 初始态 collapsed：整列**不绘制**（24 件 quickbar flag 元素全隐藏、0 个可见 hit）',
        'quickbar=' + flagOf('quickbar') + '，quickbar-flag 元素 ' + hides + '/' + expected
        + ' 隐藏，可见 hit 数=' + vhits + '（应为 0）');

    /* ⑩ x ≥ in_x → 展开（阈值取自 reveal.in_x，本文件不写死） */
    mv(RV.in_x + 4, 300);
    say(flagOf('quickbar') === 'expanded', '⑩ x ≥ in_x → 展开', 'x=' + (RV.in_x + 4)
        + '（in_x=' + RV.in_x + '）⇒ quickbar=' + flagOf('quickbar'));

    /* ⑪ 收起是**延时**行为：移到 out_x 之外只起计时；回到 ≥ in_x 撤销计时；到期才收起 */
    var lx = RV.out_x - 40;
    mv(lx, 300);
    var t1 = pendings(DELAY);
    say(flagOf('quickbar') === 'expanded' && t1.length === 1,
        '⑪a 指针移到 x < out_x → 仅起计时（delay_ms 内**未**收起）',
        'out_x=' + RV.out_x + '，x=' + lx + '，排入 ' + DELAY + 'ms 计时=' + t1.length
        + ' 个，quickbar=' + flagOf('quickbar'));
    mv(RV.in_x + 4, 300);
    say(clearedIds.indexOf(t1[0]) >= 0 && flagOf('quickbar') === 'expanded' && pendings(DELAY).length === 0,
        '⑪b 期间指针回到 x ≥ in_x → 撤销收起计时（clearTimeout 命中）',
        'clearTimeout(' + t1[0] + ') 已调用=' + (clearedIds.indexOf(t1[0]) >= 0)
        + '，quickbar=' + flagOf('quickbar'));
    mv(lx, 300); mv(lx, 300);                       // 滞回带外连移两次：不得排第二个计时
    var t2 = pendings(DELAY);
    say(t2.length === 1 && flagOf('quickbar') === 'expanded',
        '⑪c 延时未到前保持展开（重复移动不叠加计时器）',
        '在途 ' + DELAY + 'ms 计时=' + t2.length + ' 个，quickbar=' + flagOf('quickbar'));
    RPC.setFlag(RV.tip_flag, 'save');               // 预置一个气泡，验证收起时一并清空
    fireTimer(t2[0]);                               // 手动触发 = 延时到期
    say(flagOf('quickbar') === 'collapsed' && flagOf(RV.tip_flag) === '',
        '⑪d 延时到期 → 才收起，并清空气泡',
        'quickbar=' + flagOf('quickbar') + '，' + RV.tip_flag + '="' + flagOf(RV.tip_flag) + '"');

    /* ⑫ 钉住（quick_pin）：立即展开、不自动收起（指针移出与离开画布都不收） */
    mv(RV.in_x + 4, 300);
    nodeOf('quick.hit_lock').click();               // action=quick_pin
    say(flagOf('qbar_pin') === '1' && flagOf('quickbar') === 'expanded',
        '⑫a 点「锁定」→ 钉住且保持展开（action=quick_pin）',
        'qbar_pin=' + flagOf('qbar_pin') + '，quickbar=' + flagOf('quickbar'));
    mv(lx, 300);
    say(flagOf('quickbar') === 'expanded' && pendings(DELAY).length === 0,
        '⑫b 钉住后指针移到 out_x 之外 → **不起计时、不收起**',
        'quickbar=' + flagOf('quickbar') + '，在途计时=' + pendings(DELAY).length + ' 个');
    leaveCanvas();
    say(flagOf('quickbar') === 'expanded' && pendings(DELAY).length === 0,
        '⑫c 钉住时指针离开画布 → 仍不收起',
        'quickbar=' + flagOf('quickbar') + '，在途计时=' + pendings(DELAY).length + ' 个');

    /* ⑬ 名称气泡跟随悬停项（展开中；钉住状态下同样跟随 ⇒ 一并验证）。
       第三个探针点取 hit_lock 的**下缘**（y = y+h，半开区间之外、仍在竖条列内）——
       M37 已无「整条把手」可作「项外空白」的探针，改用**项与项之间的空隙**。 */
    var bLock = qbBox('quick.hit_lock');
    var cSave = midOf('quick.hit_save'), cChart = midOf('quick.hit_chart');
    mv(cSave.x, cSave.y);
    var tip1 = flagOf(RV.tip_flag);
    var txSave = nodeOf('quick.tx_save'), txChart = nodeOf('quick.tx_chart');
    var plSave = nodeOf('quick.pl_save');
    var txShown = txSave ? txSave.style.display !== 'none' : false;
    var plShown = plSave ? plSave.style.display !== 'none' : false;
    mv(cChart.x, cChart.y);
    var tip2 = flagOf(RV.tip_flag);
    var txSaveHidden = txSave ? txSave.style.display === 'none' : false;
    var plSaveHidden = plSave ? plSave.style.display === 'none' : false;
    /* 项间空隙：在列内、不属任何一项。★ 取 y+h**再 +1**（不用正好 y+h）：mv() 走
       「画布坐标 → 视口坐标 → 画布坐标」的浮点往返，正好落在边界上会因 0.0000x 的
       误差被算进上一条（实测 80 → 79.99999 ⇒ 判成 lock）。取空隙**中部**即稳定。 */
    mv(cSave.x, Number(bLock.y) + Number(bLock.h) + 1);
    var tip3 = flagOf(RV.tip_flag);
    say(tip1 === 'save' && tip2 === 'chart' && tip3 === '',
        '⑬ 名称浮出跟随悬停项：hit_save→save、hit_chart→chart、项间空隙→空',
        'save→"' + tip1 + '"，chart→"' + tip2 + '"，项外→"' + tip3 + '"');
    say(txShown && plShown && txSaveHidden && plSaveHidden,
        '⑬b 白字与药丸随 flag 同步显隐（save 时 tx_save+pl_save 亮 → 切 chart 后双双灭）',
        'save 时 tx_save 显示=' + txShown + ' / pl_save 显示=' + plShown
        + '；切到 chart 后 tx_save 隐藏=' + txSaveHidden + ' / pl_save 隐藏=' + plSaveHidden);

    /* ⑬c ★ M37 新增（**目标导向**）：**悬停材质** —— 悬停第 N 项的热区 ⇒ 第 N 个圆形 icon
       换 `_on` 图，**其它 icon 保持常态**；移出后复位。
       ★ 机制说明：真实鼠标的悬停状态机是 **DOM 事件驱动**（`attachStateEvents` 挂
       `mouseenter/mouseleave`），而 `mv()` 派发的是画布级 `mousemove`（只驱动 reveal 呼出），
       **不产生**元素的 mouseenter ⇒ 这里必须像真实鼠标那样在**热区节点**上派发 mouseenter。
       这同时是**组绑定**的证据：悬停的是 75×73 的**热区**、被点亮的却是**图标**本身
       （图标画布尺寸由数据给出，本文件不写死 —— M37 为 56、L1 起为 64）。 */
    function iconStateName(id) {                    // 复用本文件既有的 curAsset（内层节点取图名）
      var w = nodeOf(id);
      return w ? curAsset(w) : '(无)';
    }
    function hoverNode(id, on) {
      var w = nodeOf(id);
      if (!w) return;
      w.dispatchEvent(new MouseEvent(on ? 'mouseenter' : 'mouseleave',
                                     { bubbles: false, cancelable: true, view: window }));
    }
    /* ★ ISSUE-20260927-02：期望图名**从数据推**（原为写死 `x_ui_qbicon_save[_on].png` 等）。
       主语是 `quickbar` 屏的 `quick.ic_save` / `quick.ic_load`（元素级 image + state_assets）。 */
    var icS = elemOf('quickbar', 'quick.ic_save'), icL = elemOf('quickbar', 'quick.ic_load');
    if (!icS || !icL) {
      say(false, '⑬c 取数据侧主语 quick.ic_save / quick.ic_load', 'ui_layout.js 里缺这两件图标');
    } else {
      stateGuard('⑬c 数据侧守卫：save/load 的常态与悬停图须存在且互异（否则"换 _on 图"恒真）',
        [{ elem: icS }, { elem: icL }], 'hover');
    }
    var eS = statesOf(icS), eL = statesOf(icL);
    var hm0s = iconStateName('quick.ic_save'), hm0l = iconStateName('quick.ic_load');
    hoverNode('quick.hit_save', true);              // 悬停「存档」热区（组 quick.save）
    var hm1s = iconStateName('quick.ic_save'), hm1l = iconStateName('quick.ic_load');
    hoverNode('quick.hit_save', false);             // 移出
    var hm2s = iconStateName('quick.ic_save');
    say(hm0s === eS.normal && hm0l === eL.normal
        && hm1s === eS.hover && hm1l === eL.normal
        && hm2s === eS.normal,
        '⑬c 悬停第 N 项热区 → 第 N 个 icon 换 `_on` 图、其它保持常态、移出后复位（组绑定）',
        '悬停前 save/load=' + hm0s + '/' + hm0l + '（数据期望 ' + eS.normal + '/' + eL.normal + '）'
        + '；悬停存档后=' + hm1s + '/' + hm1l + '（数据期望 ' + eS.hover + '/' + eL.normal + '）'
        + '；移出后=' + hm2s);

    /* ⑭ ★ M37：收起态 **整列不绘制 ⇒ 12 项位置上一个快捷条元素都没有**。
       （M36 之前此处验的是「整条把手独占命中」；M37 起把手退场，等价断言 = **无任何
       quick.* 命中**，且整列元素 display:none。） */
    nodeOf('quick.hit_lock').click();               // 再点一次「锁定」→ 解除钉住
    mv(lx, 300); fireTimer(pendings(DELAY)[0]);     // 收起
    var scPrev = RPC.state.screen;
    var badCol = [];
    qbItems().forEach(function (it) {
      var t = topAt(Number(it.x) + Number(it.w) / 2, Number(it.y) + Number(it.h) / 2);
      var id = t ? String(t.getAttribute('data-ui-id') || '') : '';
      if (id.indexOf('quick.') === 0) badCol.push(it.id + '→' + id);
    });
    say(flagOf('quickbar') === 'collapsed' && badCol.length === 0,
        '⑭ 收起态整列不可点（12 项中心处**没有任何 quick.* 命中** —— 整条把手已随 M37 退场）',
        'quickbar=' + flagOf('quickbar') + '，命中到快捷条元素的点：'
        + (badCol.length ? badCol.join('、') : '无 ✓') + '，screen=' + RPC.state.screen);
    say(RPC.state.screen === scPrev,
        '⑭b 收起态下状态未被改变（未换屏、无动作派发）',
        'screen ' + scPrev + ' → ' + RPC.state.screen);

    /* ⑭c/⑭d ★ M37 新结构的命中层复核：
       ⑭c 展开态：逐项抽样（每项 5 点：中心 + 四角内缩 1px）**必须全部命中该项热区自己**
              （圆形 icon 是 image、不参与点击 ⇒ 点在圆面上方的点也由热区派发）；
       ⑭d 收起态：同样 60 点**必须全部命中不到任何快捷条元素**（整列被 flag 挡掉）。
       —— 这两条正是「展开态点第 N 项 = 第 N 项」的命中层证据（动作层见 index.html?selftest=1 的 C4 断言）。 */
    function qbItems() {
      return QB.elements.filter(function (e) {
        return e && e.kind === 'hit' && /^quick\.hit_[a-z]+$/.test(String(e.id));
      });
    }
    function scanHits(items) {
      var n = 0, good = 0, bad = [];
      items.forEach(function (it) {
        var bx = Number(it.x), by = Number(it.y), bw = Number(it.w), bh = Number(it.h);
        var pts = [[bx + bw / 2, by + bh / 2],
                   [bx + 1, by + 1], [bx + bw - 1, by + 1],
                   [bx + 1, by + bh - 1], [bx + bw - 1, by + bh - 1]];
        pts.forEach(function (p) {
          n++;
          var t = topAt(p[0], p[1]);
          var id = t ? String(t.getAttribute('data-ui-id') || '') : '(无)';
          if (id === it.id) good++; else bad.push(it.id + '@' + Math.round(p[0]) + ',' + Math.round(p[1]) + '→' + id);
        });
      });
      return { n: n, good: good, bad: bad };
    }
    mv(RV.in_x + 4, 300);                            // 展开
    var scExp = scanHits(qbItems());
    say(scExp.n === 60 && scExp.good === scExp.n && flagOf('quickbar') === 'expanded',
        '⑭c 展开态 12 项 × 5 点全部命中**该项热区自己**（圆形 icon 不参与点击，不吃命中）',
        scExp.good + '/' + scExp.n + ' 点命中该项' + (scExp.bad.length ? '；例外：' + scExp.bad.slice(0, 6).join(', ') : ''));
    mv(lx, 300); fireTimer(pendings(DELAY)[0]);      // 收起
    var scCol = scanHits(qbItems());
    var quickLeft = scCol.bad.filter(function (s) { return /→quick\./.test(s); });
    say(scCol.n === 60 && scCol.good === 0 && quickLeft.length === 0,
        '⑭d 收起态同一批 60 点**命中不到任何快捷条元素**（整列被 flag 挡掉 ⇒ 完全不绘制）',
        '0/' + scCol.n + ' 点命中项；其中命中快捷条元素的=' + quickLeft.length
        + '（应为 0）' + (scCol.bad.length ? '；首例：' + scCol.bad[0] : ''));
    mv(RV.in_x + 4, 300);                            // 复位为展开，供 ⑮ 使用

    /* ⑮ 展开态**派发**路径逐项验证（spy 计数）：直派到项节点本身 ——
       与 ⑭c 的截获问题正交：证明「动作接线正确」（接线与命中层是两件事）。 */
    var pinClicks = 0, pinSeen = [];
    nodeOf('quick.hit_lock').click();               // quick_pin → 钉住
    pinClicks++; pinSeen.push(flagOf('qbar_pin'));
    nodeOf('quick.hit_lock').click();               // quick_pin → 解除
    pinClicks++; pinSeen.push(flagOf('qbar_pin'));
    nodeOf('quick.hit_next').click();               // next_choice（本轮新增动作）
    var toastEl = doc.querySelector('.ui-toast');
    var toastTxt = toastEl ? (toastEl.textContent || '') : '';
    var scAfterNext = RPC.state.screen;
    nodeOf('quick.hit_option').click();             // open_config → 换到 config 屏
    var scAfterCfg = RPC.state.screen;
    say(pinClicks === 2 && pinSeen[0] === '1' && pinSeen[1] === '' && /前进/.test(toastTxt)
        && scAfterNext === 'dialog' && scAfterCfg === 'config',
        '⑮ 展开态逐项派发（spy 计数）：quick_pin 两次切换=1/空，next_choice 有反馈，open_config 换屏',
        'quick_pin 派发 ' + pinClicks + ' 次 → ' + pinSeen.join('→')
        + '；next_choice 提示="' + toastTxt + '"（screen 仍 ' + scAfterNext + '）'
        + '；open_config → ' + scAfterCfg);

    /* ⑯ open_sysmenu（**动作本身**）不再打开传统系统菜单屏，而是「展开竖条」。
       注：★ H1 裁决后 **Esc 已不挂该动作**（Esc = 返回上一层／退出，断言在
       `index.html?selftest=1` 的 `esc.*` 三条）；★ M37 起**数据里已无元素指向它**
       （整条把手 `quick.hit_toggle` 随「整条带」退场）⇒ 它现在是**编程入口**
       （深链 / 将来的键位），故这里直调动作本身验其语义并未改变。
       ★ M45（2026-09-23，用户裁定）：原断言末项 `!!LAY.screens.sysmenu`（「屏数据仍保留」）
       随 `sysmenu` 屏**整体废除**已不成立 ⇒ 改为断言其**已不存在**（`!LAY.screens.sysmenu`）：
       动作语义（展开竖条、不换屏）不变，同时把「屏已真废除」锁进断言。 */
    RPC.renderScreen('dialog', { noHistory: true });
    var sc0 = RPC.state.screen;
    RPC.doAction('open_sysmenu');
    say(RPC.state.screen === sc0 && flagOf('quickbar') === 'expanded' && !LAY.screens.sysmenu,
        '⑯ open_sysmenu 不再换屏，改为展开竖条（20_sysmenu 已废除）',
        'screen ' + sc0 + ' → ' + RPC.state.screen + '，quickbar=' + flagOf('quickbar')
        + '，20_sysmenu 已废除=' + !LAY.screens.sysmenu);

    /* ⑰ ★ C2（M35 独立复审 Minor-5）：`?chrome=0` 必须压掉**纯热区**的点击瞬闪叠色。
       用 computedStyle 直接量（不依赖真实指针的 `:hover`，无头下无法触发），
       加/去 `#canvas.chrome-off` 各读一次 —— 两次必须不同，且默认那次是那层蓝。

       ★ M38 主语迁移（等价断言，**判据不放宽**）：原主语 `dlg.icon_hit_01_qsave` 属对话框屏
       右下九宫格，**该九宫格已按用户裁决整体删除**（无框化）；且无框化后 dialog 屏已**不含任何
       纯热区**（唯一可点件是选择肢 list，它不是 hit）⇒ 本断言必须换一个**同类主语**。
       选取口径与原断言逐项相同：kind=hit ∧ 无 state_assets ∧ 无 state_group
       （= buildHit 不会给它加 `ui-hit-hasstate`，即 replica.css 的
       `.ui-hit:not(.ui-hit-hasstate).ui-hit-pressed` 正是它的默认样式）。
       新主语 `cfg.hit_reset`（配置屏「初始化」，25_config.json）满足该口径，故断言的
       语义与阈值一字未改：仅「被测元素」换了一件。

       ★ M47 主语再迁移（同款等价断言，**判据仍不放宽**）：M47 把整个 config 屏按
       接口冻结书重写（W2），旧 id 一律未沿用 ⇒ `cfg.hit_reset` **已不存在**
       （新屏的「初始化」是 `cfg.reset_hit`，但它带 `state_group="cfg.reset"` ⇒ 不再是
       纯热区，不能当主语）。故本轮取**同类主语** `cfg.tab1_hit`（页签 1 的热区：
       `kind:hit` ∧ 无 `state_assets` ∧ 无 `state_group`，且**两页都在场**、不受分页影响）。
       断言文字、阈值、判据一字未改。 */
    RPC.renderScreen('config', { noHistory: true });
    var PURE_ID = 'cfg.tab1_hit';                     // ★ M47：主语（见上条注释的迁移理由）
    var pureHit = doc.querySelector('[data-ui-id="' + PURE_ID + '"]');
    if (!pureHit) {
      say(false, '⑰ ?chrome=0 压掉纯热区叠色', '取不到纯热区 ' + PURE_ID + '（配置屏页签 1 热区）');
    } else {
      var isPure = !pureHit.classList.contains('ui-hit-hasstate');
      say(isPure, '⑰ 前置：主语确为纯热区（无 state_assets / state_group）',
          PURE_ID + ' 带 ui-hit-hasstate=' + !isPure);
      pureHit.classList.add('ui-hit-pressed');       // = 真实点击路径加的同一个类
      var bgOn = getComputedStyle(pureHit).backgroundColor;
      doc.getElementById('canvas').classList.add('chrome-off');
      var bgOff = getComputedStyle(pureHit).backgroundColor;
      doc.getElementById('canvas').classList.remove('chrome-off');
      pureHit.classList.remove('ui-hit-pressed');
      say(bgOn !== bgOff && /122, 176, 232/.test(bgOn) && !/122, 176, 232/.test(bgOff),
          '⑰ ?chrome=0 压掉纯热区的点击瞬闪叠色（computedStyle 实测）',
          '默认=' + bgOn + '　→　chrome=0=' + bgOff);
    }
    restoreTimers();

    /* ============ 规则 ⑲：`kind:"slider"` 滑块（★ M47 · ISSUE-20260924-01 · W4）============
       被测行为（契约来源：《M47_设置屏重设方案》§三.1–§三.4 = **接口冻结书**，
                以及 `layout/_schema.md` 的「`slider` 元素字段 / 拖动契约 / 设置仓」三节）：
         · 渲染：`rail`（以元素垂直中心线为轴）+ `handle`（29×29，不随元素框裁剪）；
           `data-ui-id` / `data-ui-kind="slider"` / `data-ui-slider-value` 三个探针属性齐备；
         · 拖动：由**配对热区**（hit 带 `slider:"<slider id>"`）的 pointerdown 驱动，
           按下即按 x 置值、移动持续更新、**移出热区不中断**（与规则③「移出即取消按下态」
           语义不同）；拖动中手柄用 `handle.state_assets.hover` 图；
         · 写设置仓：值变化 ⇒ `state.settings["dlg_winopac"]`（与 krkr 的 UISettingSet 同口径，
           clamp + step 对齐）；
         · 实时生效：`dlg_winopac` 同时驱动 `cfg.pv_mask` 与 `dlg.mask_bottom` 的
           `style.opacity`，映射式 `opacity = floor(255×value/100) / 255`
           （0..255 口径 → CSS 0..1 口径，见 replica.js §4.7 的长注释）；
         · 分页：`cfg_page` 在 sys/snd 间互斥切换（两页元素严格互斥的那一批）；
         · 选中态：`cfg_vchar` 决定角色名胶囊与选中名的显隐。
       ★ 断言里**不写死任何坐标 / 素材名 / 屏 id**：元素定义、素材名、动作名、flag 值
         一律从 `ui_layout.js` 的数据里推（同 ⑱ 的口径），数据改动时断言不假失败。
       ★ 已知契约冲突（如实登记，**不是本段的断言**）：`vis_flag` 只允许一对 ⇒ 本屏带
         **值 flag**（`cfg_v_<key>` / `cfg_vchar`）的元素不带页 flag（见 25_config.json 的
         note ⑥）⇒ 切页时「主值胶囊 / 主值标签 / 选中角色名」会**跨页残留**。本段只断言
         **带页 flag 的元素**互斥（那批是严格互斥的），残留问题留给主代理裁决。
       与 krkr 侧的对应断言：巡演的新 `kind:"drag"` 步骤（拖动 → 判词比对设置值 + 预览遮罩
       opacity）与 `cfg.tab2_hit` / `cfg.ch_<族>_hit` 的指针步骤 —— 两端**同判据**。 */
    (function () {
      var SID = 'cfg.sl_winopac';                 // 主语滑块（方案 §三.1 的示例元素）
      var SET = 'dlg_winopac';                    // 它的设置键（冻结名）
      var cfgDef = LAY.screens.config;
      if (!cfgDef || !cfgDef.elements) { say(false, '⑲ 取 config 屏数据', 'ui_layout.js 里没有 config 屏'); return; }

      function elDef(id) {
        for (var i = 0; i < cfgDef.elements.length; i++)
          if (cfgDef.elements[i].id === id) return cfgDef.elements[i];
        return null;
      }
      function baseName(a) {                       // 素材引用 → PNG 文件名
        return a ? String(a).replace(/^.*\//, '') : '';
      }
      function knobAsset(w) {                      // 手柄当前用的图（内层节点，复用 curAsset 的取法）
        var k = w ? w.querySelector('[data-ui-slider-knob]') : null;
        var s = k ? (k.style.backgroundImage || '') : '';
        var m = /url\("?([^")]+)"?\)/.exec(s);
        return m ? decodeURIComponent(m[1]).replace(/^.*\//, '') : '(无)';
      }
      function canvasScale() {                      // 缩放比：从 #canvas 的实测矩形推（不猜）
        var cr = doc.getElementById('canvas').getBoundingClientRect();
        return cr.width ? (Number(LAY.canvas.width) / cr.width) : 1;
      }
      /* 手柄中心在**画布坐标**里的 x —— 用**渲染后的真实矩形**量（不是读 inline left）：
         ★ 这条口径的由来：本段首版读的是 `knob.style.left`（**相对 wrap**），于是漏掉了
           「wrap 原点没减」这个真 bug（手柄整体偏一个元素 x，winopac 偏 307px）而**假通过**。
           量真实矩形才能钉住「手柄真的落在轨道上」。 */
      function knobCenterCanvasX(w) {
        var k = w ? w.querySelector('[data-ui-slider-knob]') : null;
        if (!k) return null;
        var kr = k.getBoundingClientRect();
        var cr = doc.getElementById('canvas').getBoundingClientRect();
        if (!kr.width || !cr.width) return null;
        var s = Number(LAY.canvas.width) / cr.width;
        return (kr.left + kr.width / 2 - cr.left) * s;
      }
      function xForValue(el, v) {                  // 值 → 轨道 x（与机制侧同一线性映射）
        var mn = Number(el.min), mx = Number(el.max);
        if (!(mx > mn)) return Number(el.x);
        return Number(el.x) + (Number(v) - mn) / (mx - mn) * Number(el.w);
      }
      function shown(id) { var n = nodeOf(id); return n ? (n.style.display !== 'none') : null; }
      function countShown(ids) {
        var n = 0;
        for (var i = 0; i < ids.length; i++) if (shown(ids[i]) === true) n++;
        return n;
      }
      /* 屏内某 flag 的各取值 → 元素 id 清单（数据推导） */
      function idsOfFlag(fname, fval) {
        var out = [];
        cfgDef.elements.forEach(function (el) {
          if (!el.vis_flag || String(el.vis_flag) !== fname) return;
          if (String(el.vis_when === undefined ? '' : el.vis_when) !== fval) return;
          out.push(el.id);
        });
        return out;
      }
      function nodeIdByAction(act) {
        for (var i = 0; i < cfgDef.elements.length; i++)
          if (String(cfgDef.elements[i].action) === act) return cfgDef.elements[i].id;
        return null;
      }
      /* ★ 主代理 2026-09-24 追加：**切页值 flag 派生**的审计（与 replica.js 的
         configDerivePageFlags 同一推导式，数据驱动）：
           · 值 flag 的「所属页」：凡 `action=config_set_<键>` 的元素其 `vis_when` 即该键的页；
             `config_char_*` 一律声音页（键 = cfg_vchar）；
           · 逐件比对「DOM 显隐」与「按当前 flag 值算出的可见性」（模型 vs DOM）；
           · 另摘出「**非当前页**却仍可见」的值元素（= 跨页残留，规则 1 要消灭的东西）。 */
      function valueFlagPage() {
        var mp = { cfg_vchar: 'snd' };
        cfgDef.elements.forEach(function (el) {
          var m = el.action ? /^config_set_(.+)$/.exec(String(el.action)) : null;
          if (m) mp['cfg_v_' + m[1]] = String(el.vis_when === undefined ? '' : el.vis_when);
        });
        return mp;
      }
      function valueFlagAudit(page) {
        var vp = valueFlagPage(), bad = [], other = [];
        cfgDef.elements.forEach(function (el) {
          var f = el.vis_flag ? String(el.vis_flag) : '';
          /* ⚠️ `cfg_vchar` **不带下划线**（是 `cfg_v_` + `char` 的巧合写法）⇒ 不能只用
             `/^cfg_v_/` 判定，否则角色选中态会被静默跳过（本段第一版就栽在这里）。 */
          if (!(f === 'cfg_vchar' || /^cfg_v_/.test(f))) return;
          var vis = shown(el.id);
          if (vis === null) return;
          var want = (String(RPC.getFlag(f)) === String(el.vis_when === undefined ? '' : el.vis_when));
          if (vis !== want) {
            bad.push(el.id + '（' + f + '=' + RPC.getFlag(f) + ' / vis_when=' + el.vis_when
              + ' / DOM 可见=' + vis + '）');
          }
          if (vis && String(vp[f]) !== String(page)) other.push(el.id + '（' + f + '，属 ' + vp[f] + ' 页）');
        });
        return { bad: bad, other: other };
      }

      var e0 = elDef(SID);
      if (!e0 || e0.kind !== 'slider') {
        say(false, '⑲ 前置：config 屏有 ' + SID + '（kind=slider）', e0 ? ('kind=' + e0.kind) : '没找到');
        return;
      }
      /* 配对热区：数据里带 `slider === SID` 字段的那一件（方案 §3.2 冻结写法） */
      var hitId = null;
      cfgDef.elements.forEach(function (el) {
        if (el.kind === 'hit' && String(el.slider) === SID) hitId = el.id;
      });
      if (!hitId) { say(false, '⑲ 前置：存在 slider=' + SID + ' 的拖动热区', '数据里没找到'); return; }
      var hitPure = !(elDef(hitId).state_assets || elDef(hitId).state_group);

      RPC.renderScreen('config', { noHistory: true });
      var wrap = nodeOf(SID), hit = nodeOf(hitId);

      /* ---- ⑲a 初值渲染：探针属性 + 手柄位置比例 ---- */
      if (!wrap || !hit) {
        say(false, '⑲a 取滑块节点与拖动热区', 'wrap=' + !!wrap + ' hit=' + !!hit);
      } else {
        var v0 = RPC.sliderValue(SID);
        var attr0 = wrap.getAttribute('data-ui-slider-value');
        var kindOk = wrap.getAttribute('data-ui-kind') === 'slider';
        var cx = knobCenterCanvasX(wrap);
        var want = xForValue(e0, v0);
        var dx = (cx === null) ? 999 : Math.abs(cx - want);
        /* 误差上界 = 1px：机制侧的位置式是 `x + Math.round(t×w)`（≤0.5px 取整）
           + 手柄宽 29 为奇数（`floor(29/2)=14` ⇒ 中心恒比 xOf 偏 0.5px，引擎同式）
           ⇒ 理论最坏 1.0px，故阈值取「≤1px」并留 1e-6 浮点余量。
           ★ 另加一条**结构判据**：手柄中心必须落在轨道的矩形内（x..x+w）——
             这条与「比例正确」正交，能抓住「整体偏移」类错误（首版的 307px 偏移就是它抓的
             那类；若只比比例，偏移 307px 的手柄会同时逃过比例检查）。 */
        /* 初值口径：有 setting 且仓认该键 ⇒ 仓里的值（未设置过 = 定义表 def）；否则元素 value */
        var expect0 = (e0.setting && RPC.SETTING_DEF && RPC.SETTING_DEF[e0.setting])
          ? RPC.settingGet(e0.setting) : e0.value;
        var inRail = (cx !== null) && cx >= Number(e0.x) - 0.5
                     && cx <= Number(e0.x) + Number(e0.w) + 0.5;
        say(kindOk && attr0 !== null && Number(attr0) === Number(v0)
            && Number(v0) === Number(expect0) && dx <= (1 + 1e-6) && inRail,
          '⑲a 初值渲染：data-ui-kind/data-ui-slider-value 齐备且手柄 x 比例正确（误差 ≤1px，且落在轨道内）',
          'kind=' + wrap.getAttribute('data-ui-kind') + '，data-ui-slider-value=' + attr0
          + '，运行值=' + v0 + '（期望 ' + expect0 + '），手柄中心 x=' + cx
          + '（期望 ' + want.toFixed(1) + '，误差 ' + dx.toFixed(2) + 'px）'
          + '，轨道 x..x+w=' + e0.x + '..' + (Number(e0.x) + Number(e0.w)) + '（命中=' + inRail + '）');
        say(baseName(((e0.handle || {}).state_assets || {}).normal) === knobAsset(wrap),
          '⑲a 手柄常态用 handle.state_assets.normal',
          knobAsset(wrap) + '（期望 ' + baseName(((e0.handle || {}).state_assets || {}).normal) + '）');
      }

      /* ---- ⑲b 拖动到 40：真实 pointer 事件的按下 → 移动 → 抬起 ---- */
      var hoverAsset = baseName((((e0.handle || {}).state_assets) || {}).hover);
      var normalAsset = baseName((((e0.handle || {}).state_assets) || {}).normal);
      var dragY = Number(e0.y) + Number(e0.h) / 2;
      var pA = clientOf(xForValue(e0, 40), dragY);
      fire(hit, 'pointerdown', { clientX: pA.x, clientY: pA.y });
      var hotAsset = knobAsset(wrap);                       // 拖动中（活动外观）
      var dragBound = RPC.sliderDragId();
      fire(hit, 'pointermove', { clientX: pA.x, clientY: pA.y });
      var v40 = RPC.sliderValue(SID);
      var attr40 = wrap.getAttribute('data-ui-slider-value');
      var set40 = RPC.state.settings[SET];
      var pvNode = nodeOf('cfg.pv_mask');
      var pvOp = pvNode ? pvNode.style.opacity : '(无 cfg.pv_mask)';
      /* 越界也不中断：把指针拖到轨道**右侧之外**（值应被 clamp 到 max，且拖动仍在进行） */
      var pOut = clientOf(Number(e0.x) + Number(e0.w) + 120, dragY);
      fire(hit, 'pointermove', { clientX: pOut.x, clientY: pOut.y });
      var vOut = RPC.sliderValue(SID);
      var stillDrag = RPC.sliderDragId() === SID;
      fire(hit, 'pointerup', { clientX: pOut.x, clientY: pOut.y, buttons: 0, button: 0 });
      var afterUp = { drag: RPC.sliderDragId(), hover: RPC.sliderHoverId(), knob: knobAsset(wrap) };
      /* 回到 40（后续 ⑲c/⑲d 的期望值以 40 为准） */
      var pB = clientOf(xForValue(e0, 40), dragY);
      fire(hit, 'pointerdown', { clientX: pB.x, clientY: pB.y });
      fire(hit, 'pointermove', { clientX: pB.x, clientY: pB.y });
      fire(hit, 'pointerup', { clientX: pB.x, clientY: pB.y, buttons: 0, button: 0 });

      var want40 = 40;
      say(v40 === want40 && attr40 === '40' && set40 === want40
          && Math.abs(parseFloat(pvOp) - (102 / 255)) < 1e-9,
          '⑲b 拖动到 40 ⇒ 值=40 且 state.settings.' + SET + '=40 且 cfg.pv_mask 的 opacity=102/255',
          '值=' + v40 + '，data-ui-slider-value=' + attr40 + '，settings.' + SET + '=' + set40
          + '，cfg.pv_mask.style.opacity=' + pvOp + '（期望 ' + (102 / 255) + ' = 102/255）');
      say(hotAsset === hoverAsset && dragBound === SID && vOut === Number(e0.max) && stillDrag
          && afterUp.drag === '' && afterUp.hover === '' && afterUp.knob === normalAsset,
          '⑲b 拖动中手柄用 hover 图 / 拖出轨道右侧仍不中断且 clamp 到 max / 抬起后回常态图',
          '按下后手柄=' + hotAsset + '（期望 ' + hoverAsset + '），拖动目标=' + dragBound
          + '，拖出右侧后值=' + vOut + '（期望 max=' + e0.max + '）且拖动仍在=' + stillDrag
          + '；抬起后 drag="' + afterUp.drag + '" hover="' + afterUp.hover + '" 手柄=' + afterUp.knob
          + '（期望 ' + normalAsset + '）');

      /* ---- ⑲c 实时生效穿透到对话框：换到 dialog 屏后 dlg.mask_bottom 的 opacity 同样 ---- */
      RPC.renderScreen('dialog', { noHistory: true });
      var dm = nodeOf('dlg.mask_bottom');
      var dmOp = dm ? dm.style.opacity : '(无 dlg.mask_bottom)';
      say(!!dm && Math.abs(parseFloat(dmOp) - (102 / 255)) < 1e-9,
          '⑲c 切到 dialog 屏后 dlg.mask_bottom 的 opacity 同样 = 102/255（实时生效穿透）',
          'dlg.mask_bottom.style.opacity=' + dmOp + '（期望 ' + (102 / 255) + '）');
      /* 换屏回来：运行期值必须保留（方案：值仓不随换屏重置） */
      RPC.renderScreen('config', { noHistory: true });
      var keep = nodeOf(SID);
      var keepVal = keep ? keep.getAttribute('data-ui-slider-value') : '(无)';
      say(keepVal === '40' && RPC.sliderValue(SID) === 40,
          '⑲c 换屏返回保留运行期值（config → dialog → config 后仍为 40）',
          'data-ui-slider-value=' + keepVal);

      /* ---- ⑲d 分页：cfg_page 默认 sys，点 config_tab_2 后互斥反转 ---- */
      var sysIds = idsOfFlag('cfg_page', 'sys'), sndIds = idsOfFlag('cfg_page', 'snd');
      var tab2 = nodeIdByAction('config_tab_2'), tab1 = nodeIdByAction('config_tab_1');
      if (!sysIds.length || !sndIds.length || !tab1 || !tab2) {
        say(false, '⑲d 前置：两页元素与两个页签热区齐备',
          'sys=' + sysIds.length + ' snd=' + sndIds.length + ' tab1=' + tab1 + ' tab2=' + tab2);
      } else {
        var pg0 = RPC.getFlag('cfg_page');
        var audit0 = valueFlagAudit('sys');                // 进入时的状态（默认系统页）
        var sys0 = countShown(sysIds), snd0 = countShown(sndIds);
        nodeOf(tab2).click();                              // action=config_tab_2
        var pg1 = RPC.getFlag('cfg_page');
        var sys1 = countShown(sysIds), snd1 = countShown(sndIds);
        var audit1 = valueFlagAudit('snd');                // 切到声音页之后
        say(pg0 === 'sys' && sys0 === sysIds.length && snd0 === 0
            && pg1 === 'snd' && snd1 === sndIds.length && sys1 === 0,
            '⑲d 默认 cfg_page=sys（系统页全可见 / 声音页 0 可见），点页签 2 后互斥反转',
            '初始 cfg_page=' + pg0 + '：sys 可见 ' + sys0 + '/' + sysIds.length + '、snd 可见 ' + snd0
            + '；点 ' + tab2 + ' 后 cfg_page=' + pg1 + '：snd 可见 ' + snd1 + '/' + sndIds.length
            + '、sys 可见 ' + sys1);
        /* ★ 主代理 2026-09-24 追加（本轮数据侧最易回归处）：切页**值 flag 派生** —— 切到声音页后
           **系统页的值元素必须全不可见**（display:none），且每件值元素的 DOM 显隐与「按当前
           flag 值算出的可见性」逐件一致。切回系统页再验一次（回页要能派生回来 ⇒ 不丢状态）。
           ★★ 第二轮补强（主代理补单 ①②）：**进屏那一刻**（`initFlagsFor` 之后、
             `configFlagsInitFor` 同位置）与**深链 `?flags=` 覆盖之后**也必须已派生 ⇒
             把原先只作「如实登记」的 `audit0.other`（曾是 4 件 asu 残留）升级为**硬断言 == 0**。
             另单列一条 `cfg_vchar` 专项：系统页上「角色预览/选中」元素（pill / tx_sel /
             pv_face_* / pv_name_*）的可见数必须 == 0 —— 这组是 `flags_default.cfg_vchar`
             最容易漏出来的一族，且与数据版本无关（按 flag 名推导，不数死件数）。 */
        nodeOf(tab1).click();                              // action=config_tab_1 → 切回系统页
        var pg2 = RPC.getFlag('cfg_page');
        var audit2 = valueFlagAudit('sys');
        /* 进屏那一刻的态：重新渲染（= 走 `initFlagsFor` + `configFlagsInitFor` 这条真实路径） */
        RPC.renderScreen('config', { noHistory: true });
        var auditEntry = valueFlagAudit('sys');
        function chrVisibleOn(page) {                      // 系统页上仍可见的 cfg_vchar 元素
          var n = 0, ids = [];
          cfgDef.elements.forEach(function (el) {
            if (String(el.vis_flag) !== 'cfg_vchar') return;
            if (shown(el.id) === true) { n++; ids.push(el.id); }
          });
          return { n: n, ids: ids, page: page };
        }
        var chrEntry = chrVisibleOn('sys');
        say(pg2 === 'sys' && audit1.bad.length === 0 && audit1.other.length === 0
            && audit2.bad.length === 0 && audit2.other.length === 0
            && auditEntry.other.length === 0 && chrEntry.n === 0,
            '⑲d 切页值 flag 派生：非本页值元素 display:none（0 件残留）+ 每件值元素显隐与 flag 值一致'
            + ' + **进屏那一刻同样已派生**（cfg_vchar 组在系统页可见数 = 0）',
            '切到声音页后：模型不符 ' + audit1.bad.length + ' 件、**非本页仍可见 ' + audit1.other.length
            + ' 件**' + (audit1.other.length ? '（' + audit1.other.slice(0, 4).join('、') + '）' : '')
            + '；切回系统页后：模型不符 ' + audit2.bad.length + ' 件、非本页仍可见 ' + audit2.other.length + ' 件'
            + '；★ **进屏那一刻**（默认系统页）：模型不符 ' + auditEntry.bad.length + ' 件、非本页仍可见 '
            + auditEntry.other.length + ' 件'
            + (auditEntry.other.length ? '（' + auditEntry.other.slice(0, 4).join('、') + '）' : '')
            + '；cfg_vchar 组在系统页可见 ' + chrEntry.n + ' 件'
            + (chrEntry.ids.length ? '（' + chrEntry.ids.slice(0, 4).join('、') + '）' : '')
            + '；点页签前（同一进屏态）非本页可见 ' + audit0.other.length + ' 件');
      }

      /* ---- ⑲e 选中态：点某 cfg.ch_<族>_hit ⇒ cfg_vchar 与该族一致，且该族的
              `_pill` / `_tx_sel` 可见、其它族不可见 ---- */
      var fams = [], famHit = {}, famPill = {}, famSel = {};
      cfgDef.elements.forEach(function (el) {
        var m = el.action ? /^config_char_(.+)$/.exec(String(el.action)) : null;
        if (m) { fams.push(m[1]); famHit[m[1]] = el.id; }
        if (el.vis_flag && String(el.vis_flag) === 'cfg_vchar') {
          var id = String(el.id || '');
          if (/_pill$/.test(id)) famPill[String(el.vis_when)] = id;
          else if (/_tx_sel$/.test(id)) famSel[String(el.vis_when)] = id;
        }
      });
      if (fams.length < 2 || !famPill[fams[0]] || !famSel[fams[0]]) {
        say(false, '⑲e 前置：角色列表 ≥2 族且族内有 _pill / _tx_sel',
          '族 ' + fams.length + ' 个，首族的 pill/sel=' + famPill[fams[0]] + '/' + famSel[fams[0]]);
      } else {
        if (tab2) nodeOf(tab2).click();                    // 角色列表属**声音页**，先切过去
        var pgPre = RPC.getFlag('cfg_page');
        var auditE = valueFlagAudit('snd');                // 声音页上：系统页的值元素必须全不可见
        var prevFam = RPC.getFlag('cfg_vchar');
          var tgt = '';
          for (var fi = 0; fi < fams.length; fi++) if (fams[fi] !== prevFam) { tgt = fams[fi]; break; }
          if (tgt === '') { say(false, '⑲e 取一个与当前选中不同的族', '全部族都等于 ' + prevFam); }
          else {
            var wrong = 0;      // 点击前：**旧选中族**（= 默认 asu）的 pill/sel 可见数（属预期）
            [String(famPill[prevFam]), String(famSel[prevFam])].forEach(function (id) {
              if (shown(id) === true) wrong++;
            });
            nodeOf(famHit[tgt]).click();                     // action=config_char_<族>
            var nowFam = RPC.getFlag('cfg_vchar');
            var okShown = shown(famPill[tgt]) === true && shown(famSel[tgt]) === true;
            var wrongAfter = 0, wrongAfterIds = [];
            fams.forEach(function (f) {
              if (f === tgt) return;
              if (shown(famPill[f]) === true) { wrongAfter++; wrongAfterIds.push(famPill[f]); }
              if (shown(famSel[f]) === true) { wrongAfter++; wrongAfterIds.push(famSel[f]); }
            });
            say(pgPre === 'snd' && nowFam === tgt && okShown && wrongAfter === 0
                && auditE.other.length === 0,
                '⑲e 点 ' + famHit[tgt] + ' ⇒ cfg_vchar=' + tgt + '，该族 _pill 与 _tx_sel 可见、其它族全不可见'
                + '（且声音页上**系统页的值元素 0 件可见**）',
                'cfg_page=' + pgPre + '（声音页前置）；cfg_vchar ' + prevFam + ' → ' + nowFam
                + '；该族 pill/sel 可见=' + okShown + '；**其它族误显 ' + wrongAfter + ' 件**'
                + (wrongAfterIds.length ? '（' + wrongAfterIds.slice(0, 4).join('、') + '）' : '')
                + '；声音页上非本页值元素可见 ' + auditE.other.length + ' 件'
                + (auditE.other.length ? '（' + auditE.other.slice(0, 4).join('、') + '）' : '')
                + '；点击前旧选中族（' + prevFam + '）可见 ' + wrong + ' 件（预期：它是切换前的选中项）');

            /* ★★ M47 第三轮（一审打回 C3 + C4）· 三条硬断言，专盯「非本页不上屏」与「记忆层」：
               (C3) 在**系统页**上程序化派发 `config_char_<族>`（巡演 / 探针 / 深链 / 将来侧边栏
                    入口都是这条路径）⇒ 选中值必须**只进记忆、不上屏**：该族 pill/tx_sel 可见数
                    == 0，且 flag 被置空；否则 33 件只带 `cfg_vchar` 的选中元素会在系统页显形。
               (C3) 切回声音页 ⇒ 该族 pill/tx_sel 各可见 1 件（记忆被三级链取回）。
               (C4) **跨屏往返**（config → dialog → config）后回声音页 ⇒**仍是该族**，
                    不是 `flags_default` 的 asu —— 这一条是**记忆层与 captureMemo=false 的鉴别器**：
                    若进屏路径也捕获记忆（旧实现），返回时 flag 的默认值会冲掉记忆 ⇒ 判成 asu。
               ⚠️ 用**非默认族**做主语（默认 asu 与 flags_default 同值，鉴别不出记忆层）。 */
            var memFam = (fams.indexOf('kob') >= 0) ? 'kob' : fams[(fams.indexOf(tgt) + 1) % fams.length];
            if (memFam === prevFam) memFam = tgt;
            nodeOf(tab1).click();                            // 先回**系统页**
            RPC.doAction('config_char_' + memFam);           // 程序化派发（= 巡演/探针同一入口）
            var sysFamFlag = RPC.getFlag('cfg_vchar');
            var sysShownN = 0;
            [String(famPill[memFam]), String(famSel[memFam])].forEach(function (id) {
              if (shown(id) === true) sysShownN++;
            });
            var memNow = (RPC.cfgVarRemember() || {})['cfg_vchar'];
            say(RPC.getFlag('cfg_page') === 'sys' && sysShownN === 0 && sysFamFlag === ''
                && String(memNow) === memFam,
                '⑲e 系统页上派发 config_char_' + memFam + ' ⇒ **不上屏**（该族 pill/tx_sel 可见 0 件、'
                + 'cfg_vchar 置空），值只进记忆',
                'cfg_page=' + RPC.getFlag('cfg_page') + '；cfg_vchar="' + sysFamFlag + '"（期望空串）；'
                + '该族 pill/tx_sel 可见 ' + sysShownN + ' 件（期望 0）；记忆 cfg_vchar='
                + String(memNow) + '（期望 ' + memFam + '）');
            nodeOf(tab2).click();                            // 切回声音页 ⇒ 记忆取回
            var sndShownN = 0;
            [String(famPill[memFam]), String(famSel[memFam])].forEach(function (id) {
              if (shown(id) === true) sndShownN++;
            });
            say(RPC.getFlag('cfg_vchar') === memFam && sndShownN === 2,
                '⑲e 切回声音页 ⇒ 记忆取回：cfg_vchar=' + memFam + '，该族 pill/tx_sel 各可见 1 件',
                'cfg_vchar=' + RPC.getFlag('cfg_vchar') + '（期望 ' + memFam + '）；该族 pill/tx_sel 可见 '
                + sndShownN + ' 件（期望 2）');
            /* (C4) 跨屏往返：进屏路径**不得**捕获记忆（captureMemo=false） */
            RPC.renderScreen('dialog', { noHistory: true });
            RPC.renderScreen('config', { noHistory: true });
            var backEntry = RPC.getFlag('cfg_vchar');        // 回来时在系统页 ⇒ 应为空串（已派生）
            nodeOf(tab2).click();                            // 回声音页
            var backFam = RPC.getFlag('cfg_vchar');
            say(backFam === memFam && RPC.getFlag('cfg_page') === 'snd',
                '⑲e 跨屏往返（config → dialog → config → 声音页）后仍是 ' + memFam
                + '（记忆层生效；若进屏捕获记忆会被默认值 asu 冲掉）',
                '往返后 cfg_page=' + RPC.getFlag('cfg_page') + '，cfg_vchar=' + backFam
                + '（期望 ' + memFam + '；默认值 asu 表示记忆被冲掉）；进屏那一刻 flag="'
                + backEntry + '"（期望空串：非本页不上屏）');

            /* ★★ ⑲f（M47 第三轮 · 一审打回 C2）· 初始化 = **全部 25 键复位 + 清空切页记忆**：
               复现路径：改「全屏模式」→ 切声音页 → 点「初始化」⇒ 必须回窗口模式。
               逐项断言：设置仓 display 复位 'window'、cfg_v_display 派生回 'window'（且窗口模式
               那枚胶囊可见）、cfg_page 回 'sys'、记忆表已清空（引擎 uiScreenConfigMemoClear 同）。
               改前（只复位 9 个数值键、不清记忆）此条必失败 —— 见变异 m6。 */
            var fullHit = null, winHit = null;
            cfgDef.elements.forEach(function (el) {
              if (String(el.action) !== 'config_set_display') return;
              if (String(el.value) === 'full') fullHit = el.id;
              if (String(el.value) === 'window') winHit = el.id;
            });
            var resetHit = nodeIdByAction('config_reset');
            if (!fullHit || !winHit || !resetHit) {
              say(false, '⑲f 前置：取画面模式两个值按钮与「初始化」热区',
                'full=' + fullHit + ' window=' + winHit + ' reset=' + resetHit);
            } else {
              nodeOf(tab1).click();                        // 系统页
              nodeOf(fullHit).click();                     // 改「全屏模式」
              var d1 = RPC.getFlag('cfg_v_display');
              nodeOf(tab2).click();                        // 切声音页（捕获记忆）
              nodeOf(resetHit).click();                    // 点「初始化」
              var d2 = RPC.getFlag('cfg_v_display');
              var store2 = String(RPC.settingGet('display'));
              var memNow2 = RPC.cfgVarRemember() || {};
              var memKeys = Object.keys(memNow2);
              var winShown = (winHit && shown(winHit) === true);
              /* ⚠️ 不断言「记忆表为空」：`config_reset` 清空后紧接着的派生会**重新捕获**一遍
                 （捕获到的已是复位后的默认值 —— 对仓型键无害；`cfg_vchar` 无仓项，按引擎同序
                 保留用户的选择）。C2 要钉的是「**仓复位后记忆不得压过默认值**」，
                 即 `cfg_v_display` 必须回 window —— 下面这几条即是该判据。 */
              say(d1 === 'full' && d2 === 'window' && store2 === 'window'
                  && RPC.getFlag('cfg_page') === 'sys' && winShown
                  && String(memNow2['cfg_v_display']) === 'window',
                  '⑲f 初始化：改「全屏」→ 切声音页 → 点初始化 ⇒ 回窗口模式'
                  + '（仓 25 键复位 + 派生回 window + 页签回系统页；记忆重捕获后也是默认值）',
                  '改后 cfg_v_display=' + d1 + '（期望 full）；初始化后 cfg_v_display=' + d2
                  + '（期望 window）、仓 display=' + store2 + '、cfg_page=' + RPC.getFlag('cfg_page')
                  + '、窗口模式胶囊可见=' + winShown + '；记忆重捕获 ' + memKeys.length
                  + ' 键（cfg_v_display=' + String(memNow2['cfg_v_display']) + '，应 window —— '
                  + '仓复位后记忆已不可能压过默认值）');
            }
          }
      }
    })();

    /* ============ 规则 ⑳：list 的**逐块按钮**（item_buttons）与**逐块文案区**（item_text）
       （★ M06 · ISSUE-20260924-06_回想屏重排 · 与 krkr 侧 ui_widget.tjs 的 uiWidgetDrawList /
        uiWidgetItemButtonState / uiWidgetItemButtonAt 同口径）============
       主语一律**从 ui_layout.js 的数据推**（同 ⑱/⑲ 的口径）：行数 = min(labels, max_rows)、
       按钮的 key / 局部矩形 / 三态图名全部读数据 ⇒ 数据一改断言不假失败。 */
    (function () {
      var scr = LAY.screens.backlog;
      if (!scr || !scr.elements) { say(false, '⑳ 取 backlog 屏数据', 'ui_layout.js 里没有 backlog 屏'); return; }
      var L = null;
      scr.elements.forEach(function (e) { if (e.id === 'bl.list') L = e; });
      var nb = (L && L.item_buttons && L.item_buttons.length) ? L.item_buttons.length : 0;
      if (!L || nb < 2 || !L.item_text) {
        say(false, '⑳ 前置：bl.list 带 item_text + ≥2 个 item_buttons',
          'list=' + !!L + ' item_buttons=' + nb + ' item_text=' + !!(L && L.item_text));
        return;
      }
      RPC.renderScreen('backlog', { noHistory: true });
      var rows = Math.max(1, Math.min(Number(L.max_rows) || (L.labels || []).length || 1,
                                        (L.labels || []).length || 1));
      function itemAt(idx) {
        return doc.querySelector('[data-ui-kind="list-item"][data-ui-index="' + idx + '"]');
      }
      function btnAt(idx, key) {
        var it = itemAt(idx);
        return it ? it.querySelector('[data-ui-kind="list-item-btn"][data-ui-item-btn="' + key + '"]') : null;
      }
      function baseName(p) { return String(p || '').replace(/^.*\//, ''); }

      /* ---- ⑳a 渲染数量：可见行 × 按钮数（逐块渲染 ⇒ 天然随分页/滚动走） ---- */
      var domBtns = doc.querySelectorAll('[data-ui-kind="list-item-btn"]');
      var domItems = doc.querySelectorAll('[data-ui-kind="list-item"]');
      say(domBtns.length === rows * nb && domItems.length === rows,
        '⑳a 逐块渲染数量：DOM ' + domBtns.length + ' ＝ 可见行 ' + rows + ' × 按钮 ' + nb,
        'list-item=' + domItems.length + '（期望 ' + rows + '）、list-item-btn=' + domBtns.length
        + '（期望 ' + (rows * nb) + '）');

      /* ---- ⑳b 几何一律数据驱动：每按钮的位置/尺寸 = 项矩形 + 块内局部矩形 ---- */
      var bad = [];
      for (var r = 0; r < rows; r++) {
        for (var bi = 0; bi < nb; bi++) {
          var b = L.item_buttons[bi], nd = btnAt(r, b.key);
          if (!nd) { bad.push('行' + r + '/' + b.key + ' 缺节点'); continue; }
          if (nd.style.left !== Number(b.x) + 'px' || nd.style.top !== Number(b.y) + 'px'
              || nd.style.width !== Number(b.w) + 'px' || nd.style.height !== Number(b.h) + 'px') {
            bad.push('行' + r + '/' + b.key + ' 实际 ' + nd.style.left + ',' + nd.style.top + ' '
              + nd.style.width + '×' + nd.style.height);
          }
        }
      }
      say(bad.length === 0, '⑳b 按钮几何 = 数据里的块内局部矩形（机制不写死任何按钮几何）',
        bad.length ? bad.slice(0, 4).join('；') : '全部与数据一致');

      /* ---- ⑳c–⑳f 逐按钮三态 + 隔离性（规则表：①按下 ②抬起 ③移出 ⑤pressed>hover>normal） ---- */
      var b0 = L.item_buttons[0], b1 = L.item_buttons[1];
      var sa0 = b0.state_assets || {};
      var N0 = baseName(sa0.normal || b0.asset), H0 = baseName(sa0.hover || sa0.normal || b0.asset);
      var P0 = baseName(sa0.pressed || sa0.hover || sa0.normal || b0.asset);
      var sa1 = b1.state_assets || {};
      var N1 = baseName(sa1.normal || b1.asset);
      var n0 = btnAt(0, b0.key), n1 = btnAt(0, b1.key);
      if (!n0 || !n1) {
        say(false, '⑳c 前置：第 1 行的两个按钮节点', 'n0=' + !!n0 + ' n1=' + !!n1);
      } else {
        say(curAsset(n0) === N0 && curAsset(n1) === N1,
          '⑳c 初态：第 1 行两按钮各是自己的 normal 图', curAsset(n0) + ' / ' + curAsset(n1));
        fire(n0, 'mouseenter');
        var hovA = curAsset(n0), hovB = curAsset(n1);
        say(hovA === H0 && hovB === N1,
          '⑳d 悬停 ' + b0.key + ' ⇒ **仅它**换 hover 图（邻按钮不动）', hovA + ' / ' + hovB);
        fire(n0, 'mousedown');
        var prsA = curAsset(n0), prsB = curAsset(n1);
        say(prsA === P0 && prsB === N1,
          '⑳e 按住 ' + b0.key + ' ⇒ 仅它换 pressed 图（悬停/按下只影响被指到的那一个按钮）',
          prsA + ' / ' + prsB);
        fire(n0, 'mouseup');
        say(curAsset(n0) === H0, '⑳f 抬起 ⇒ 回落 hover（仍在悬停，未粘住 pressed）', curAsset(n0));
        fire(n0, 'mouseleave');
        say(curAsset(n0) === N0 && curAsset(n1) === N1,
          '⑳f 移出 ⇒ 双按钮全回 normal（台账无悬挂）', curAsset(n0) + ' / ' + curAsset(n1));
        /* 反向对照：右键按下**不得**置 pressed（与元素级/逐项态同规矩：只认左键） */
        fire(n0, 'mouseenter');
        fire(n0, 'mousedown', { button: 2 });
        say(curAsset(n0) === H0, '⑳g 右键按下不得置 pressed（按钮保持 hover）', curAsset(n0));
        fire(n0, 'mouseleave');
      }

      /* ---- ⑳h 派发：`%row%` 必须换成**点中的那一行**（逐行各验一次，含动作名与行号） ---- */
      var st0 = RPC.backlogState();
      st0.lastAct = ''; st0.lastRow = -1; st0.count = 0;      // 归零后再逐条验
      var dispBad = [];
      for (var rr = 0; rr < rows; rr++) {
        for (var bj = 0; bj < nb; bj++) {
          var bb = L.item_buttons[bj];
          var wantAct = String(bb.action).split('%row%').join(String(rr));
          var node = btnAt(rr, bb.key);
          if (!node) { dispBad.push('行' + rr + '/' + bb.key + ' 缺节点'); continue; }
          var before = RPC.backlogState().count;
          node.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
          var st = RPC.backlogState();
          if (st.lastAct !== wantAct || st.lastRow !== rr || st.count !== before + 1) {
            dispBad.push('行' + rr + '/' + bb.key + ' ⇒ ' + st.lastAct + '（期望 ' + wantAct
              + '）行号 ' + st.lastRow + '（期望 ' + rr + '）');
          }
        }
      }
      say(dispBad.length === 0,
        '⑳h 逐行逐按钮派发：action 的 %row% 换成**该行**全局序号（' + (rows * nb) + ' 条全验）',
        dispBad.length ? dispBad.slice(0, 3).join('；') : '全部一致（末次 ' + RPC.backlogState().lastAct
          + ' 行号 ' + RPC.backlogState().lastRow + '）');

      /* ---- ⑳i 按钮**吃掉**整行命中：点块内非按钮区（文案区）不得派发任何按钮动作 ---- */
      var lab = itemAt(0) ? itemAt(0).querySelector('.ui-list-item-text') : null;
      if (!lab) {
        say(false, '⑳i 前置：第 1 行的 item_text 文案节点', '没找到 .ui-list-item-text');
      } else {
        var b4 = RPC.backlogState().count, a4 = RPC.backlogState().lastAct;
        lab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        var st4 = RPC.backlogState();
        say(st4.count === b4 && st4.lastAct === a4,
          '⑳i 点块内**非按钮区**（文案区）不派发按钮动作（整行 action 数据为空 ⇒ 按契约不派发）',
          '派发次数 ' + b4 + ' → ' + st4.count + '，lastAct 未变=' + (st4.lastAct === a4));
      }

      /* ---- ⑳j `item_text` 生效：内缩位置/宽度/行数上限；⑳k 回归：无 item_text 的 list 走旧路径 ---- */
      var t = L.item_text;
      var box = itemAt(0) ? itemAt(0).querySelector('.ui-list-item-text') : null;
      say(!!box && box.style.left === Number(t.x) + 'px' && box.style.top === Number(t.y) + 'px'
          && box.style.width === Number(t.w) + 'px' && box.style.height === Number(t.h) + 'px',
        '⑳j item_text 生效：文案区按块内局部矩形**内缩**定位（' + t.x + ',' + t.y + ' ' + t.w + '×' + t.h + '）',
        box ? (box.style.left + ',' + box.style.top + ' ' + box.style.width + '×' + box.style.height) : '缺节点');
      var inner = box ? box.querySelector('.ui-list-item-text-inner') : null;
      var clamp = inner ? (inner.style.webkitLineClamp || inner.style['-webkit-line-clamp'] || '') : '';
      var tSize = (t.font && t.font.size) ? Number(t.font.size) : Number((L.font || {}).size || 0);
      say(!!inner && String(clamp) === String(t.max_lines) && Number(inner.style.lineHeight.replace('px', '')) ===
          tSize * Number((LAY.fonts.line_spacing || {}).body || 1),
        '⑳j item_text 折行口径：max_lines=' + t.max_lines + '（-webkit-line-clamp）+ 行距 = 字号 '
        + tSize + ' × 全局行距',
        inner ? ('lineClamp=' + clamp + ' lineHeight=' + inner.style.lineHeight + ' fontSize=' + inner.style.fontSize) : '缺内层');
      /* ⑳k 回归：没给 item_text 的 list（对话框选择肢）**必须**仍是旧路径（单行、无内缩） */
      var dlg = LAY.screens.dialog, ch = null;
      if (dlg && dlg.elements) dlg.elements.forEach(function (e) { if (e.kind === 'list') ch = e; });
      if (ch && !ch.item_text) {
        RPC.renderScreen('dialog', { noHistory: true });
        var ci = doc.querySelector('[data-ui-kind="list-item"]');
        var oldLab = ci ? ci.querySelector('.ui-list-item-label') : null;
        if (oldLab && !oldLab.classList.contains('ui-list-item-text')) {
          /* 旧路径把文字直接写在 .ui-list-item-label 上（无内层、无内缩） */
          var okOld = !oldLab.querySelector('.ui-list-item-text-inner') && (oldLab.textContent || '').length > 0;
          say(okOld, '⑳k 回归：无 item_text 的 list（' + ch.id + '）仍走旧路径（单行、无内缩）',
            'label 文本="' + (oldLab.textContent || '').slice(0, 12) + '…" 含内层=' + !!oldLab.querySelector('.ui-list-item-text-inner'));
        } else {
          say(false, '⑳k 回归：' + ch.id + ' 的标签节点', 'oldLab=' + !!oldLab);
        }
      } else {
        say(false, '⑳k 前置：dialog 屏有一个无 item_text 的 list', '屏/元素缺失');
      }
      /* ⑳l 守卫台账：合法数据下必须**零** REJECT（正例） */
      var rej = (RPC.backlogState().rejects || []).slice();
      say(rej.length === 0, '⑳l 合法数据下 item_buttons/item_text 守卫判词必须为 0 条',
        rej.length ? rej.slice(0, 3).join('；') : '0 条（★M06ITEMBTN-REJECT★ 未触发）');

      /* ---- ⑳m 守卫**负向对照**（内存副本，不写磁盘；与 krkr 巡演 `kind:"itemguard"` 同口径）：
         把 item_buttons 改坏三种形态 ⇒ ①判词必须逐条出现 ②坏按钮**不画、不可点**。
         判据与绘制共用同一个 `itemBtnReject`/校验流程（见 replica.js 的 buildList）。 ---- */
      var keep = L.item_buttons.slice();
      var mutated = [
        { key: '__mut_emptyact', x: 500, y: 90, w: 40, h: 20, asset: 'ui/x_ui_jump_off.png', action: '' },
        { key: '__mut_outblock', x: 9999, y: 90, w: 40, h: 20, asset: 'ui/x_ui_jump_off.png', action: 'backlog_jump:%row%' },
        { key: '__mut_nokey', x: 600, y: 90, w: 40, h: 20, asset: 'ui/x_ui_jump_off.png', action: 'backlog_jump:%row%' }
      ];
      mutated[2].key = '';
      L.item_buttons = keep.concat(mutated);
      RPC.renderScreen('backlog', { noHistory: true });
      var rej2 = RPC.backlogState().rejects || [];
      var wantSubs = ['action 为空', '矩形出块', '缺 key'];
      var missSub = wantSubs.filter(function (s) { return !rej2.some(function (l) { return l.indexOf(s) >= 0; }); });
      /* ★ M06 一审 A2（2026-09-24）：**修空断言** —— 原来「缺 key」那条用
         `[data-ui-item-btn=""]` 兜，但 `btnSysKey` 对缺 key **恒返回 `#<下标>`**
         （见 replica.js，与 krkr 的 uiWidgetItemBtnSysKey 同口径）⇒ 该选择器**永不匹配**，
         断言恒真（一审已用变异证明：放行 `#` 开头键后 DOM 出现 4 个
         `data-ui-item-btn="#4"`，而旧写法仍打印「坏按钮 DOM 节点=0」ALL PASS）。
         改按**系统键前缀**兜：缺 key 的键一律以 `#` 开头，合法键（jump/replay）不会。 */
      var badNodes = doc.querySelectorAll(
        '[data-ui-item-btn="__mut_emptyact"],[data-ui-item-btn="__mut_outblock"],[data-ui-item-btn^="#"]');
      var goodNodes = doc.querySelectorAll('[data-ui-item-btn="' + b0.key + '"]');
      var badKeys = [];
      for (var _bi = 0; _bi < badNodes.length; _bi++)
        badKeys.push(badNodes[_bi].getAttribute('data-ui-item-btn'));
      say(missSub.length === 0 && badNodes.length === 0 && goodNodes.length === rows,
        '⑳m 守卫负向对照：3 种非法形态逐条 REJECT（' + (3 - missSub.length) + '/3）且坏按钮**不画**（合法按钮不受影响）',
        '判词 ' + rej2.length + ' 条' + (rej2.length ? '（' + rej2.slice(0, 3).join('；') + '）' : '')
        + '；缺的判词=' + (missSub.length ? missSub.join('、') : '无')
        + '；坏按钮 DOM 节点=' + badNodes.length + '（期望 0'
        + (badKeys.length ? '，实得键=' + badKeys.join(',') : '') + '）；合法按钮 ' + b0.key + ' 节点='
        + goodNodes.length + '（期望 ' + rows + '）');
      L.item_buttons = keep;                                  // 还原（内存，不动磁盘）
      RPC.renderScreen('backlog', { noHistory: true });

      /* ---- ⑳n **容器级**结构非法也必须 REJECT（M06 一审 A3 自证）----
         原先 HTML 侧对 `item_buttons` 非数组 / `item_text` 非对象**静默当作未声明**，
         而 krkr 的 `uiWidgetItemButtonProblems` / `uiWidgetItemText` 会显式拒绝。
         契约：判词串**与引擎逐字相同**，且**仅当字段存在但类型不对**才报；
         **缺字段仍视为未声明**（不报、走旧路径）。 */
      var keepText = L.item_text;
      var rejN0 = (RPC.backlogState().rejects || []).length;
      L.item_buttons = 'not-an-array';                        /* 给了但不是数组 */
      L.item_text = 42;                                       /* 给了但不是对象 */
      RPC.renderScreen('backlog', { noHistory: true });
      var rejN = (RPC.backlogState().rejects || []).slice(rejN0);
      var wantN = ['bl.list[(item_buttons)] item_buttons 不是数组', 'bl.list[item_text] item_text 不是对象'];
      var missN = wantN.filter(function (s) { return !rejN.some(function (l) { return l.indexOf(s) >= 0; }); });
      var noBtnN = doc.querySelectorAll('[data-ui-kind="list-item-btn"]').length;
      say(missN.length === 0 && noBtnN === 0 && rejN.length === 2,
        '⑳n 容器级结构非法也 REJECT（判词串与 krkr 逐字相同）：item_buttons 非数组 / item_text 非对象',
        '判词 ' + rejN.length + ' 条' + (rejN.length ? '（' + rejN.join('；') + '）' : '')
        + '；缺的判词=' + (missN.length ? missN.join('、') : '无') + '；按钮 DOM 节点=' + noBtnN + '（期望 0）');

      /* 反向对照：**缺字段**不得报（仍视为未声明） */
      var rejM0 = (RPC.backlogState().rejects || []).length;
      delete L.item_buttons;
      delete L.item_text;
      RPC.renderScreen('backlog', { noHistory: true });
      var rejM = (RPC.backlogState().rejects || []).slice(rejM0);
      say(rejM.length === 0,
        '⑳n 反向对照：缺 item_buttons / item_text 字段**不报**（视为未声明，走旧路径）',
        '新增判词 ' + rejM.length + ' 条（期望 0）' + (rejM.length ? '（' + rejM.join('；') + '）' : ''));

      L.item_buttons = keep;                                  /* 还原（内存，不动磁盘） */
      L.item_text = keepText;
      RPC.renderScreen('backlog', { noHistory: true });
    })();

    /* ============ 规则 ㉑：鉴赏模式 —— 栏位内差分 `item_variants` / 页内翻页 / 页签切屏
       （★ M1 · ISSUE-20260924-08 · 与 krkr 侧 ui_widget.tjs 的 uiWidgetDrawListVariants /
        uiWidgetItemVariantButtonAt、ui_screens.tjs 的 gallery_* 动作 **同口径**）============
       ⚠️ 主语**不依赖 M2/M3/M4 的数据**：本节在**内存里**造一个测试屏 `__gal_grid`
       （6 列 × 4 行网格 / 30 栏 / 每栏 3 张差分）与一个测试外壳 `__gal_shell`，
       断言完把内存改动**全部还原**（不写磁盘、不动 ui_layout.js）。 */
    (function () {
      var ID = '__gal_grid';
      var N_ROWS = 30, N_DIFF = 3, COLS = 6, ROWS = 4, IW = 291, IH = 166, GAP = 12;
      var A = ['ui/x_ui_cfg_tab_on.png', 'ui/x_ui_cfg_name_sel.png', 'ui/x_ui_menuicon_gallery.png'];
      var frames = [];
      for (var r = 0; r < N_ROWS; r++) {
        var row = [];
        for (var k = 0; k < N_DIFF; k++) row.push(A[(r + k) % A.length]);
        frames.push(row);
      }
      frames[5] = [];                                   /* 第 6 栏留空（合法） */
      var gridEl = {
        id: ID + '.list', kind: 'list', z: 30, visible_default: true,
        orientation: 'h', x: 57, y: 187,
        w: COLS * IW + (COLS - 1) * GAP, h: ROWS * IH + (ROWS - 1) * GAP,
        item_w: IW, item_h: IH, gap: GAP, max_cols: COLS, max_rows: ROWS,
        labels: [], actions: [],
        font: { size: 20, color: '@palette.text_menu' }, align: 'center',
        scroll: { mode: 'page', page_size: COLS * ROWS },
        item_variants: {
          frames: frames,
          thumb: { x: 8, y: 8, w: IW - 16, h: IH - 46 },
          prev: { key: 'vprev', x: 8, y: IH - 34, w: 48, h: 26, asset: A[0],
                  state_assets: { normal: A[0], hover: A[1], pressed: A[2] },
                  action: 'gallery_prev:%row%' },
          next: { key: 'vnext', x: IW - 56, y: IH - 34, w: 48, h: 26, asset: A[0],
                  state_assets: { normal: A[0], hover: A[1], pressed: A[2] },
                  action: 'gallery_next:%row%' },
          text: { x: 60, y: IH - 34, w: IW - 120, h: 26, align: 'center',
                  font: { size: 20, bold: true, color: '@palette.text_primary' } },
          edge: 'clamp'
        }
      };
      for (var L2i = 0; L2i < N_ROWS; L2i++) { gridEl.labels.push('栏 ' + (L2i + 1)); gridEl.actions.push(''); }
      var testScreen = { id: ID, title_cn: '㉑ 鉴赏机制测试屏', owner: 'M1', elements: [gridEl] };
      LAY.screens[ID] = testScreen;
      RPC.renderScreen(ID, { noHistory: true });

      function q(sel) { return doc.querySelector(sel); }
      function qa(sel) { return doc.querySelectorAll(sel); }
      /* ⚠️ `backgroundImage` 是 `url("…")` 形态 ⇒ 末尾的 `")` 必须一并剥掉，
         否则与数据里的裸文件名比不相等（实测踩过：断言明明对却恒 FAIL）。 */
      function base(p) { return String(p || '').replace(/^.*\//, '').replace(/["')]/g, ''); }
      function itemOf(idx) { return q('[data-ui-kind="list-item"][data-ui-index="' + idx + '"]'); }
      function varBtn(row, which) {
        return q('[data-ui-kind="list-item-var-btn"][data-ui-var-index="' + row
          + '"][data-ui-var-which="' + which + '"]');
      }
      function varThumb(row) {
        return q('[data-ui-kind="list-item-var-thumb"][data-ui-var-index="' + row + '"]');
      }
      function varText(row) {
        return q('[data-ui-kind="list-item-var-text"][data-ui-var-index="' + row + '"]');
      }
      var L2 = gridEl;

      /* ---- ㉑a 多行网格折行几何（h 网格：col = i%cols、row = floor(i/cols)） ---- */
      var geoBad = [];
      for (var gi = 0; gi < COLS * ROWS; gi++) {
        var it = itemOf(gi);
        if (!it) { geoBad.push('栏 ' + gi + ' 缺节点'); continue; }
        /* 项 div 的 left/top 是**容器相对**（容器自身由 applyBox 定位在 57,187）⇒ 只算折行偏移 */
        var ex = (gi % COLS) * (IW + GAP);
        var ey = Math.floor(gi / COLS) * (IH + GAP);   /* 行距 = `gap`（同一 list 的 gap 两轴共用） */
        if (it.style.left !== ex + 'px' || it.style.top !== ey + 'px') {
          geoBad.push('栏 ' + gi + ' 实际 ' + it.style.left + ',' + it.style.top
            + '（期望 ' + ex + ',' + ey + '）');
        }
      }
      say(geoBad.length === 0,
        '㉑a 多行网格折行几何：' + (COLS * ROWS) + ' 栏的 (col,row) 折行位置与公式一致',
        geoBad.length ? geoBad.slice(0, 3).join('；') : ('cols=' + COLS + ' rows=' + ROWS
          + ' item=' + IW + '×' + IH + ' gap=' + GAP));

      /* ---- ㉑b 渲染数量：可见栏（24）× (缩略图 1 + 按钮 2 + 文本 1)，留空栏不画 ---- */
      var firstPageVis = 0;
      for (var vr2 = 0; vr2 < COLS * ROWS; vr2++) if (frames[vr2] && frames[vr2].length) firstPageVis++;
      say(qa('[data-ui-kind="list-item-var-thumb"]').length === firstPageVis
          && qa('[data-ui-kind="list-item-var-btn"]').length === firstPageVis * 2
          && qa('[data-ui-kind="list-item-var-text"]').length === firstPageVis,
        '㉑b 逐栏渲染数量：本页 ' + firstPageVis + ' 栏（留空 1 栏不画）⇒ 缩略图 '
          + qa('[data-ui-kind="list-item-var-thumb"]').length + ' / 按钮 '
          + qa('[data-ui-kind="list-item-var-btn"]').length + ' / 文本 '
          + qa('[data-ui-kind="list-item-var-text"]').length,
        '全表 ' + N_ROWS + ' 栏（每页 ' + (COLS * ROWS) + ' 栏）');

      /* ---- ㉑c 几何一律数据驱动：缩略图/按钮/文本 = 项矩形 + 块内局部矩形 ---- */
      var cBad = [];
      for (var ci = 0; ci < 3; ci++) {
        var bx = (ci % COLS) * (IW + GAP);        /* 容器相对（同 ㉑a） */
        var by = Math.floor(ci / COLS) * (IH + GAP);
        var chk = [[varThumb(ci), L2.item_variants.thumb, 'thumb'],
                   [varBtn(ci, 'prev'), L2.item_variants.prev, 'prev'],
                   [varBtn(ci, 'next'), L2.item_variants.next, 'next'],
                   [varText(ci), L2.item_variants.text, 'text']];
        chk.forEach(function (p) {
          var nd = p[0], sp = p[1], nm = p[2];
          if (!nd) { cBad.push('栏' + ci + '/' + nm + ' 缺节点'); return; }
          var want = { left: bx + Number(sp.x), top: by + Number(sp.y),
                       w: Number(sp.w), h: Number(sp.h) };
          if (nd.style.left !== want.left + 'px' || nd.style.top !== want.top + 'px'
              || nd.style.width !== want.w + 'px' || nd.style.height !== want.h + 'px') {
            cBad.push('栏' + ci + '/' + nm + ' 实际 ' + nd.style.left + ',' + nd.style.top + ' '
              + nd.style.width + '×' + nd.style.height);
          }
        });
      }
      say(cBad.length === 0, '㉑c 差分件几何 = 数据里的块内局部矩形（机制不写死任何几何）',
        cBad.length ? cBad.slice(0, 3).join('；') : '缩略图/左右按钮/n-N 文本四件全一致');

      /* ---- ㉑d 初态：缩略图 = frames[row][0]、n/N = 1/N ---- */
      say(base(varThumb(0).style.backgroundImage) === base(frames[0][0])
          && (varText(0).textContent || '') === '1/' + N_DIFF,
        '㉑d 初态：第 1 栏缩略图 = frames[0][0]、n/N = 1/' + N_DIFF,
        base(varThumb(0).style.backgroundImage) + ' / ' + varText(0).textContent);

      /* ---- ㉑e 点 next ⇒ 换图 + n/N 变 + 派发 gallery_next:0（行号 = 该栏） ---- */
      var gst = RPC.galleryState();
      gst.lastAct = ''; gst.lastRow = -1; gst.count = 0;
      var beforeAsset = base(varThumb(0).style.backgroundImage);
      fire(varBtn(0, 'next'), 'click');
      var afterAsset = base(varThumb(0).style.backgroundImage);
      say(afterAsset === base(frames[0][1]) && afterAsset !== beforeAsset
          && (varText(0).textContent || '') === '2/' + N_DIFF
          && gst.lastAct === 'gallery_next:0' && gst.lastRow === 0 && gst.count === 1,
        '㉑e 点 next：缩略图确实换图 + n/N 2/' + N_DIFF + ' + 派发 gallery_next:0',
        beforeAsset + ' → ' + afterAsset + '；n/N=' + varText(0).textContent
        + '；派发=' + gst.lastAct + ' 行号=' + gst.lastRow + ' 次数=' + gst.count);

      /* ---- ㉑f 点 prev ⇒ 回第 1 张 ---- */
      fire(varBtn(0, 'prev'), 'click');
      say(base(varThumb(0).style.backgroundImage) === base(frames[0][0])
          && (varText(0).textContent || '') === '1/' + N_DIFF
          && gst.lastAct === 'gallery_prev:0',
        '㉑f 点 prev：回到第 1 张（' + (varText(0).textContent || '') + '）',
        base(varThumb(0).style.backgroundImage) + '；派发=' + gst.lastAct);

      /* ---- ㉑g 边界口径 = clamp：第 1 张再点 prev ⇒ 仍 1/N（派发发生但序号钳制） ---- */
      var cntG = gst.count;
      fire(varBtn(0, 'prev'), 'click');
      say((varText(0).textContent || '') === '1/' + N_DIFF
          && base(varThumb(0).style.backgroundImage) === base(frames[0][0])
          && gst.count === cntG + 1 && gst.lastAct === 'gallery_prev:0',
        '㉑g 边界 clamp：第 1 张再点 prev ⇒ 序号钳制在 1/' + N_DIFF + '（派发仍发生）',
        'n/N=' + varText(0).textContent + ' 派发次数 ' + cntG + ' → ' + gst.count);

      /* ---- ㉑h 逐按钮三态（只影响被指到的那一个按钮） ---- */
      var n0 = varBtn(0, 'next'), n1 = varBtn(1, 'next');
      var N0 = base(A[0]), H0 = base(A[1]), P0 = base(A[2]);
      function imgOf(nd) {
        var i = nd.querySelector('.ui-stateimage, .ui-nine');
        return base(i && (i.style.backgroundImage || i.style.borderImageSource));
      }
      fire(n0, 'mouseenter');
      var hA = imgOf(n0), hB = imgOf(n1);
      fire(n0, 'mousedown');
      var pA = imgOf(n0);
      fire(n0, 'mouseup');
      fire(n0, 'mouseleave');
      say(imgOf(n0) === N0 && hA === H0 && hB === N0 && pA === P0 && imgOf(n0) === N0,
        '㉑h 逐按钮三态：悬停换 hover、按住换 pressed、移出回落 normal（邻栏按钮不动）',
        N0 + ' / 悬停=' + hA + '（邻=' + hB + '）/ 按下=' + pA);

      /* ---- ㉑i 缩略图（非按钮区）不得派发任何差分动作 ---- */
      var cntI = gst.count, actI = gst.lastAct;
      fire(varThumb(0), 'click');
      say(gst.count === cntI && gst.lastAct === actI,
        '㉑i 点缩略图（块内非按钮区）不派发差分动作（该 list 整行 action 为空 ⇒ 不派发）',
        '派发次数 ' + cntI + ' → ' + gst.count);

      /* ---- ㉑j 留空栏（frames[row] = []）不画、不可点、且**不报**（留空是合法状态） ---- */
      say(!varThumb(5) && !varBtn(5, 'prev') && !varText(5),
        '㉑j 留空栏（第 6 栏 frames=[]）不画缩略图/按钮/文本',
        '缩略图=' + !!varThumb(5) + ' 按钮=' + !!varBtn(5, 'prev') + ' 文本=' + !!varText(5));

      /* ---- ㉑k 合法数据零 REJECT（正例） ---- */
      var rejK = (RPC.galleryState().rejects || []).slice();
      say(rejK.length === 0, '㉑k 合法数据下 item_variants 守卫判词必须为 0 条',
        rejK.length ? rejK.slice(0, 3).join('；') : '0 条（★M08VARIANT-REJECT★ 未触发）');

      /* ---- ㉑l 容器级非法 REJECT（内存副本） ---- */
      var keepV = L2.item_variants;
      L2.item_variants = 'not-an-object';
      RPC.renderScreen(ID, { noHistory: true });
      L2.item_variants = { frames: 'not-an-array' };
      RPC.renderScreen(ID, { noHistory: true });
      var rl2 = (RPC.galleryState().rejects || []).slice();
      var wantL = [ID + '.list[(item_variants)] item_variants 不是对象',
                   ID + '.list[(frames)] frames 不是数组'];
      var missL = wantL.filter(function (s) { return !rl2.some(function (l) { return l.indexOf(s) >= 0; }); });
      var noVarNodes = qa('[data-ui-kind="list-item-var-thumb"]').length;
      say(missL.length === 0 && noVarNodes === 0,
        '㉑l 容器级非法 REJECT（判词与 krkr 逐字相同）：item_variants 非对象 / frames 非数组',
        '判词 ' + rl2.length + ' 条；缺=' + (missL.length ? missL.join('、') : '无')
        + '；缩略图节点=' + noVarNodes + '（期望 0）');

      /* ---- ㉑m 逐栏非法 REJECT：frames[row] 非数组 / 空素材 ⇒ 该栏不画 ---- */
      L2.item_variants = JSON.parse(JSON.stringify(keepV));
      L2.item_variants.frames[7] = 'oops';
      L2.item_variants.frames[8] = [''];
      RPC.renderScreen(ID, { noHistory: true });
      var rl3 = (RPC.galleryState().rejects || []).slice();
      var wantM = [ID + '.list[frames[7]] 第 7 栏差分列表不是数组',
                   ID + '.list[frames[8]] 差分素材为空（第 1 张）'];
      var missM = wantM.filter(function (s) { return !rl3.some(function (l) { return l.indexOf(s) >= 0; }); });
      var badRowNodes = doc.querySelectorAll(
        '[data-ui-var-index="7"],[data-ui-var-index="8"]').length;
      say(missM.length === 0 && badRowNodes === 0
          && qa('[data-ui-kind="list-item-var-thumb"]').length === firstPageVis - 2,
        '㉑m 逐栏非法 REJECT：frames[row] 非数组 / 空素材 ⇒ 该栏不画且逐条打判词',
        '判词 ' + rl3.length + ' 条；缺=' + (missM.length ? missM.join('、') : '无')
        + '；坏栏 DOM 节点=' + badRowNodes + '（期望 0）；缩略图 '
        + qa('[data-ui-kind="list-item-var-thumb"]').length + '（期望 ' + (firstPageVis - 2) + '）');

      /* ---- ㉑n 页内翻页（gallery_page_next/prev）：页码 ±1 + 栏位随页走 ---- */
      L2.item_variants = keepV;
      RPC.renderScreen(ID, { noHistory: true });
      var pg0 = RPC.state.listPage[gridEl.id] || 0;
      var firstIdx0 = q('[data-ui-kind="list-item"]').getAttribute('data-ui-index');
      RPC.doGalleryAction('gallery_page_next');
      var pg1 = RPC.state.listPage[gridEl.id] || 0;
      var firstIdx1 = q('[data-ui-kind="list-item"]').getAttribute('data-ui-index');
      RPC.doGalleryAction('gallery_page_prev');
      var pg2 = RPC.state.listPage[gridEl.id] || 0;
      say(pg0 === 0 && pg1 === 1 && pg2 === 0 && firstIdx0 === '0'
          && firstIdx1 === String(COLS * ROWS),
        '㉑n 页内翻页：第 1 页 → 第 2 页 → 回第 1 页，且本页首栏全局序号 = 页×每页',
        'page ' + pg0 + '→' + pg1 + '→' + pg2 + '；首栏 ' + firstIdx0 + '→' + firstIdx1);

      /* ---- ㉑p 页码 flag 接线（★ M8 一审 R3）：翻页动作把 1 基页号写进屏级 `page_flag` ----
         内存测试屏临时声明 `page_flag:'__gal_page'` + `flags_default` + 两件互斥页码文本
         （vis_flag/vis_when），断言 ① 翻页后 flag 值随页变；② 互斥文本的显隐随 flag 切换；
         ③ `galleryPageVariantClearFor` 归零时 flag 复位 "1"。断言完还原内存改动。 */
      var PFLAG = '__gal_page';
      testScreen.page_flag = PFLAG;
      testScreen.flags_default = {}; testScreen.flags_default[PFLAG] = '1';
      var ptxKeep = testScreen.elements.length;
      testScreen.elements.push(
        { id: ID + '.ptx1', kind: 'text', z: 41, visible_default: true, x: 57, y: 900,
          w: 300, h: 40, font: { size: 20, color: '@palette.text_menu' },
          align: 'left', valign: 'middle', wrap: false, max_lines: 1, sample: '1 / 2',
          vis_flag: PFLAG, vis_when: '1', note: '㉑p 测试页码文本 1' },
        { id: ID + '.ptx2', kind: 'text', z: 41, visible_default: true, x: 57, y: 900,
          w: 300, h: 40, font: { size: 20, color: '@palette.text_menu' },
          align: 'left', valign: 'middle', wrap: false, max_lines: 1, sample: '2 / 2',
          vis_flag: PFLAG, vis_when: '2', note: '㉑p 测试页码文本 2' });
      RPC.renderScreen(ID, { noHistory: true });
      RPC.doGalleryAction('gallery_page_next');
      var pflag1 = RPC.getFlag(PFLAG);
      var t1v = vis(ID + '.ptx1'), t2v = vis(ID + '.ptx2');
      RPC.doGalleryAction('gallery_page_prev');
      var pflag0 = RPC.getFlag(PFLAG);
      var t1v2 = vis(ID + '.ptx1'), t2v2 = vis(ID + '.ptx2');
      RPC.galleryPageVariantClearFor(ID);
      var pflagClr = RPC.getFlag(PFLAG);
      say(pflag1 === '2' && pflag0 === '1' && pflagClr === '1'
          && !t1v && t2v && t1v2 && !t2v2,
        '㉑p 页码 flag 接线：翻页写 1 基页号（1→2→1）+ 两件互斥页码文本随 flag 切换 + 归零复位 "1"',
        PFLAG + ' ' + pflag0 + '→' + pflag1 + '→' + pflag0 + '，归零后=' + pflagClr
        + '；文本1/2 可见性 第1页=' + t1v2 + '/' + (!t2v2) + ' 第2页=' + (!t1v) + '/' + t2v);
      testScreen.elements.length = ptxKeep;
      delete testScreen.page_flag;
      delete testScreen.flags_default;

      /* ---- ㉑q scroll.pager:false（★ M8 一审 R4）：屏数据自带页码控件 ⇒ 关闭 HTML 自动分页器 ----
         本测试页 30 栏 / 每页 24 ⇒ pages=2：不声明 pager 时 HTML 会生成 .ui-list-pager（对照）；
         声明 `scroll.pager:false` 后必须没有该节点（krkr 端本无此 chrome ⇒ 两端一致）。 */
      var pagerSel = '.ui-list-pager';
      RPC.renderScreen(ID, { noHistory: true });
      var pagerDefault = qa(pagerSel).length;
      L2.scroll = { mode: 'page', page_size: COLS * ROWS, pager: false };
      RPC.renderScreen(ID, { noHistory: true });
      var pagerOff = qa(pagerSel).length;
      L2.scroll = { mode: 'page', page_size: COLS * ROWS };
      say(pagerDefault >= 1 && pagerOff === 0,
        '㉑q scroll.pager:false：声明 false ⇒ 不生成自动分页器（缺省时照旧 ' + pagerDefault
        + ' 枚，krkr 端本无此 chrome ⇒ 关掉才两端一致）',
        '缺省 pager 节点=' + pagerDefault + '，pager:false 后=' + pagerOff);

      /* ---- ㉑r 挂壳屏重进归零（★ M8 一审 + 主代理追认项⑥）：push 形进入 ⇒ 页码/差分/页码flag 清零 ----
         测试屏临时 `attach:'gal_shell'`（gal_shell 的页签值集不含本屏 id ⇒ 页签派生返回 0，零副作用），
         翻到第 2 页后从 title 以 **push 形**（不带 noHistory）进入 ⇒ `galleryPageVariantClearFor`
         应把 listPage/varIdx/页码 flag 全部归零。 */
      var histKeepR = RPC.state.history.length;
      testScreen.attach = 'gal_shell';
      RPC.renderScreen('title', { noHistory: true });
      RPC.renderScreen(ID, { noHistory: true });
      RPC.doGalleryAction('gallery_page_next');            // 翻到第 2 页
      var rPageBefore = RPC.state.listPage[gridEl.id] || 0;
      RPC.renderScreen('title', { noHistory: true });
      RPC.renderScreen(ID);                                // push 形进入（重进）
      var rPageAfter = RPC.state.listPage[gridEl.id] || 0;
      var rVarAfter = JSON.stringify(RPC.state.varIdx[gridEl.id] || {});
      say(rPageBefore === 1 && rPageAfter === 0 && rVarAfter === '{}',
        '㉑r 挂壳屏重进归零：push 形进入后 listPage 1→0、差分序号表清空（与 krkr uiScreenPush 同口径）',
        '重进前 page=' + rPageBefore + '，重进后 page=' + rPageAfter + ' varIdx=' + rVarAfter);
      delete testScreen.attach;
      RPC.state.history.length = histKeepR;                // 还原巡演历史栈
      RPC.state.varIdx = {};
      RPC.state.listPage = {};
      RPC.renderScreen(ID, { noHistory: true });

      /* ---- ㉑o 页签 = 切屏：内存里给 gallery/music 挂测试外壳，断言
             「同级换屏 + 历史不涨 + 上一屏不在 DOM + gal_tab 派生 + 外壳仍叠画」 ---- */
      /* ⚠️ 外壳 id **必须用真值 `gal_shell`**：replica.js 的 `doGalleryAction` 硬比常量
         `GALLERY_SHELL_ID = 'gal_shell'`（与 39_gal_shell.json 的屏 id 一致，接口冻结）。
         早先本夹具用合成 id `__gal_shell` ⇒ 换屏前就被 `★M08TAB-REJECT★` 挡下（实测
         「屏 gallery→gallery」）。故这里**临时替换**真外壳的数据（断言完还原）。 */
      var SHELL = 'gal_shell';
      var shellDef = { id: SHELL, title_cn: '㉑ 测试外壳', flags_default: { gal_tab: 'gallery' },
        elements: [
          { id: SHELL + '.ind_gallery', kind: 'rect', z: 12, visible_default: true,
            x: 0, y: 0, w: 100, h: 40, color: '@palette.highlight', opacity: 210,
            vis_flag: 'gal_tab', vis_when: 'gallery', note: '㉑ 测试用' },
          { id: SHELL + '.ind_music', kind: 'rect', z: 12, visible_default: true,
            x: 0, y: 0, w: 100, h: 40, color: '@palette.highlight', opacity: 210,
            vis_flag: 'gal_tab', vis_when: 'music', note: '㉑ 测试用' },
          { id: SHELL + '.back_hit', kind: 'hit', z: 96, visible_default: true,
            x: 1660, y: 30, w: 230, h: 52, action: 'close', label: '', note: '㉑ 测试用' }
        ] };
      var keepGallery = LAY.screens.gallery, keepMusic = LAY.screens.music;
      var keepShell = LAY.screens[SHELL];
      LAY.screens[SHELL] = shellDef;
      LAY.screens.gallery = { id: 'gallery', title_cn: '㉑ gallery 测试宿主', owner: 'M1',
        attach: SHELL, elements: [{ id: 'gallery.bg', kind: 'rect', z: 0,
          visible_default: true, x: 0, y: 0, w: 1920, h: 1080,
          color: '@palette.backdrop', opacity: 200, note: '㉑ 测试用' }] };
      LAY.screens.music = { id: 'music', title_cn: '㉑ music 测试宿主', owner: 'M1',
        attach: SHELL, elements: [{ id: 'music.bg', kind: 'rect', z: 0,
          visible_default: true, x: 0, y: 0, w: 1920, h: 1080,
          color: '@palette.backdrop', opacity: 200, note: '㉑ 测试用' }] };
      RPC.renderScreen('gallery', { noHistory: true });
      var histBefore = RPC.state.history.length;
      var attachOnGallery = RPC.state.attachId === SHELL;
      /* ⚠️ 判据是**可见性**（`applyFlagVisibility` 只改 display、节点仍在 DOM 里）——
         用 querySelector 存在性判会永远为真（实测踩过：切到 music 后 gallery 指示件「仍在」。） */
      function vis(id) {
        var n = doc.querySelector('[data-ui-id="' + id + '"]');
        return !!n && window.getComputedStyle(n).display !== 'none';
      }
      var indGallery = vis(SHELL + '.ind_gallery');
      var indMusic = vis(SHELL + '.ind_music');
      var tabFlag0 = RPC.getFlag('gal_tab');
      RPC.doGalleryAction('gallery_tab_2');
      var histAfter = RPC.state.history.length;
      var screenAfter = RPC.state.screen;
      var galleryGone = !doc.querySelector('[data-ui-id="gallery.bg"]');
      var musicThere = !!doc.querySelector('[data-ui-id="music.bg"]');
      var indMusic2 = vis(SHELL + '.ind_music');
      var indGallery2 = vis(SHELL + '.ind_gallery');
      var tabFlag1 = RPC.getFlag('gal_tab');
      var shellDraw = !!doc.querySelector('[data-ui-id="' + SHELL + '.back_hit"]');
      say(attachOnGallery && indGallery && !indMusic && tabFlag0 === 'gallery'
          && screenAfter === 'music' && histAfter === histBefore && galleryGone && musicThere
          && indMusic2 && !indGallery2 && tabFlag1 === 'music' && shellDraw,
        '㉑o 页签 = 切屏：gallery → music（同级换屏、历史不涨、上一屏不在 DOM）+ gal_tab 派生 + 外壳仍叠画',
        'attach=' + RPC.state.attachId + ' 屏 gallery→' + screenAfter
        + ' 历史 ' + histBefore + '→' + histAfter + ' gal_tab ' + tabFlag0 + '→' + tabFlag1
        + ' 上一屏残留=' + (!galleryGone) + ' 外壳命中件=' + shellDraw
        + ' 指示件 gallery/music=' + indGallery2 + '/' + indMusic2);

      /* ---- 还原内存改动（不写磁盘、不动 ui_layout.js） ---- */
      LAY.screens.gallery = keepGallery;
      LAY.screens.music = keepMusic;
      if (keepShell) LAY.screens[SHELL] = keepShell; else delete LAY.screens[SHELL];
      delete LAY.screens[ID];
      RPC.state.varIdx = {};
      RPC.state.listPage = {};
      RPC.renderScreen('title', { noHistory: true });
    })();

    done();
  }

  function done() {
    log.push('SELFTEST ' + (fails ? ('FAILED ' + fails + ' 项') : 'ALL PASS'));
    document.getElementById('verdict').innerHTML =
      log.map(function (l) {
        return '<span class="' + (l.indexOf('FAIL') >= 0 ? 'bad' : 'ok') + '">' + l + '</span>';
      }).join('\n');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();
