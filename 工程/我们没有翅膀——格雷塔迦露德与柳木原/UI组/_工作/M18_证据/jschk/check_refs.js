// M18：离线结构校验（无浏览器）——flow.html 依赖的两份数据是否自洽
const fs = require('fs'), path = require('path');
const vm = require('vm');
const dir = process.argv[2];
const sandbox = { window: {} };
vm.createContext(sandbox);
for (const f of ['ui_layout.js', 'flow_data.js']) {
  vm.runInContext(fs.readFileSync(path.join(dir, f), 'utf8'), sandbox, { filename: f });
}
const L = sandbox.window.UI_LAYOUT, D = sandbox.window.UI_FLOW_DATA;
const errs = [];
if (!L) errs.push('ui_layout.js 未导出 window.UI_LAYOUT');
if (!D) errs.push('flow_data.js 未导出 window.UI_FLOW_DATA');
const sc = L.screens.flowchart;
if (!sc) errs.push('layout 缺 flowchart 屏');
const ids = new Set(sc.elements.map(e => e.id));
let checked = 0;
D.nodes.forEach(n => {
  for (const sfx of ['_fill', '_box', '_label', '_hit']) {
    checked++;
    if (!ids.has(n.el + sfx)) errs.push(`节点 ${n.id} 缺元素 ${n.el + sfx}`);
  }
  if (n.grid_col === undefined || n.grid_row === undefined) errs.push(`节点 ${n.id} 缺 grid_col/grid_row`);
});
D.edges.forEach(e => (e.els || []).forEach(x => { checked++; if (!ids.has(x)) errs.push(`边 ${e.id} 引用了不存在的元素 ${x}`); }));
D.buses.forEach(b => { if (b.el) { checked++; if (!ids.has(b.el)) errs.push(`总线 ${b.id} 引用了不存在的元素 ${b.el}`); } });
D.links.forEach(l => { checked++; if (!ids.has(l.el)) errs.push(`links 引用了不存在的元素 ${l.el}`); });
// 反向：flowchart 屏里的 flow.* 元素是否都被数据引用（bg/页眉页脚/图例/返回除外）
const dataRefs = new Set();
D.nodes.forEach(n => ['_fill', '_box', '_label', '_hit'].forEach(s => dataRefs.add(n.el + s)));
D.edges.forEach(e => (e.els || []).forEach(x => dataRefs.add(x)));
D.buses.forEach(b => { if (b.el) dataRefs.add(b.el); });
D.links.forEach(l => dataRefs.add(l.el));
['flow.wrap_a', 'flow.wrap_b', 'flow.wrap_c'].forEach(x => dataRefs.add(x));
const orphans = [...ids].filter(id => id.startsWith('flow.') && !dataRefs.has(id)
  && !['flow.bg', 'flow.hdr_band', 'flow.title', 'flow.info', 'flow.ftr_band',
       'flow.legend_fill', 'flow.legend_frame', 'flow.hit_back', 'flow.detail'].includes(id)
  && !/^flow\.lg\d/.test(id));
console.log('检查引用数 =', checked);
console.log('flowchart 屏元素数 =', sc.elements.length);
console.log('节点数 =', D.nodes.length, '｜ 边 =', D.edges.length, '｜ 总线 =', D.buses.length, '｜ 连接条 =', D.links.length);
console.log('layout.mode =', D.layout.mode, '｜ cols =', D.layout.cols, '｜ rows =', D.layout.rows);
console.log('无数据引用的 flow.* 元素 =', orphans.length ? orphans.join(', ') : '（无）');
if (errs.length) { console.log('ERRORS:'); errs.forEach(e => console.log('  - ' + e)); process.exit(1); }
console.log('RESULT: OK（引用全部存在、grid 字段齐备）');
