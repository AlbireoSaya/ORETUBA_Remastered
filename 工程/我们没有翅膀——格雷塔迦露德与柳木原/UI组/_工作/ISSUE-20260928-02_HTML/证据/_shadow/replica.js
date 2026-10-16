/* ============================================================================
   replica.js — 《我们没有翅膀——格雷塔迦露德与柳木原》UI 1:1 HTML 复刻渲染器
   M3 模块 ｜ Issue: ISSUE-20260919-11 ｜ 分支: issue/ISSUE-20260919-11-greta-ui

   ── 1:1 保证方式 ────────────────────────────────────────────────────────────
   本文件是「数据驱动的通用渲染器」：
     · 布局数据唯一来源 = window.UI_LAYOUT（由 复刻/ui_layout.js 定义）
     · ui_layout.js 由 UI组/工具/gen_layout.py 从 layout/screens/*.json +
       layout/palette.json 生成；krkr 侧 krkr/game/ui_layout.tjs 由**同一份**
       screens/*.json 生成。→ 两侧同源，不存在人工对齐。
     · 本文件内**不含任何来自 layout 的坐标 / 尺寸 / 字号 / 颜色常量**；
       所有 x / y / w / h / font.size / line_spacing / color / opacity / nine /
       z / labels / actions 一律从 UI_LAYOUT 读取后写入 inline style。

   ── 离线约束 ────────────────────────────────────────────────────────────────
   · 不使用 fetch() / XMLHttpRequest（file:// 下会被 CORS 拦）
   · 不依赖网络与 CDN；布局数据由 <script src="ui_layout.js"> 同步加载
   · 贴图走相对路径（默认 ../krkr/assets/ui/，与 UI_LAYOUT.asset_root 对应），
     与 krkr 侧共用 M1 产出的**同一份资产集**，不复制第二份

   ── 契约实现 ────────────────────────────────────────────────────────────────
   实现 layout/_schema.md §四 的全部 kind：image / text / rect / hit / list / anim
   实现 §六 动作名表的全部 action

   ── M15 扩展（2026-09-20）────────────────────────────────────────────────────
   本轮画布基线由 1280×720 改为 **1920×1080**（总纲 D1 修订注·第三条），屏数
   15 → **16**（新增 `sysicons` 右键图标浮层）。本文件按「扩展而非重写」处理：
     ① 画布尺寸**只从 UI_LAYOUT.canvas 读**（页面里已无任何 1280/720 字面量）；
     ② `overlay:true` 的屏（sysicons）**先把下层屏画出来再叠本屏**——对齐 krkr 侧
        `ui_screens.tjs` 的 overlay 分支，否则屏内全屏压暗 rect 压的是空画面 → 纯黑；
     ③ 右键改为「呼出/收起 sysicons 浮层」（原先绑的是 open_backlog），语义与
        krkr 侧 `startup.tjs` 的 `toggleSysIcons()` 逐条对齐；
     ④ `nine:{l:0,t:0,r:0,b:0}` = 「允许整图缩放」的合法写法，**不能走 border-image**
        （border-width 全 0 时 border-image 不绘制任何像素，M18 在 复刻\flow.html 已实测），
        改走普通 `<img>` 整图拉伸，且**不校验 w/h 与 PNG 实尺寸**（该写法下二者本就不同）；
     ⑤ `dynamic:"gallery_preview"`（M14 新增）与 story_background / slot_thumb 同待遇：
        未填充时画占位底色 + 标注，**不跳过**；
     ⑥ 屏切换一律清空旧 DOM（fragment 83 元素 / flowchart 92 元素不逐帧重建）。

   ── M3 扩展（2026-09-22，ISSUE-20260922-28）· 右端竖排快捷条 ────────────────
   把系统菜单改成「鼠标贴屏幕右端呼出、平时收起」的竖排快捷条（数据
   `layout/screens/35_quickbar.json`）。**M1 已落地机制层**（屏级状态 flag，见 §4.5），
   本轮补**运行时行为**，与 krkr 侧 M2 的实现必须逐字一致（契约见 §4.6）：
     ① 屏级 `attach` 附加层：承载屏画完后再叠画附加屏的元素（同一容器、z-index 整体上移）；
     ② 画布级 mousemove/mouseleave 驱动呼出/收起（阈值全部读 `reveal`，脚本内不写死）；
     ③ `open_sysmenu` 不再换屏，改为「展开竖条」；新增 `quick_pin` / `next_choice`；
     ④ 支持 `index.html?screen=<屏>&flags=<名>:<值>[,…]` 覆盖 flag 后渲染（供无头截图）。
   ============================================================================ */

(function () {
  'use strict';

  /* ==========================================================================
     0. 数据根
     ========================================================================== */
  var L = window.UI_LAYOUT;
  if (!L || !L.screens) {
    document.addEventListener('DOMContentLoaded', function () {
      var box = document.getElementById('stage-wrap') || document.body;
      var pre = document.createElement('pre');
      pre.style.cssText = 'color:#ffb4ad;padding:20px;white-space:pre-wrap';
      pre.textContent = '错误：未加载布局数据（window.UI_LAYOUT 不存在）。\n'
        + '请确认 复刻/ui_layout.js 与 index.html 同目录，且通过 <script src="ui_layout.js"> 加载。';
      box.appendChild(pre);
    });
    return;
  }

  var CANVAS = L.canvas || { width: 1280, height: 720 };
  var FONTS = L.fonts || {};
  var SIZES = FONTS.sizes || {};
  var LSP = FONTS.line_spacing || {};
  var PAL = L.palette || {};
  var SCREENS = L.screens || {};
  var BOXES = L.content_boxes || {};

  /* 资产根：`krkr/assets/`（= asset_root 去掉末段 `ui/`），相对 复刻/ 的路径。
     ★ M47（主代理 2026-09-24 裁决 · 与守门侧 `工具\verify_ui.py` 的 `asset_to_relpath()`
       同一口径）：**命名空间 = asset 串的首段** —— `ui/x.png` 与 `face/asu07.png` 各自
       落到 `krkr/assets/ui/`…、`krkr/assets/face/`…。
     为什么必须放开：krkr 侧的取件规则（`ui_asset.tjs` 的 `uiAssetCandidates`）是「把 asset 串
       **原样**当存储名，依次试 `<项目根>/<串>`、`<项目根>/assets/<串>`」，而 `run_loose.bat`
       把 `krkr\assets` 整体镜像成 `game\assets` ⇒ **两种前缀引擎都能命中**；本端原先写死
       `…/krkr/assets/ui/` 再拼串 ⇒ 只有 `ui/` 能解析，W2 的设置屏角色形象预览
       `face/<族><NN>.png`（33 件，方案 §1.3）会 404 成缺件红框 —— 与引擎**分叉**。
     兼容口径（两条都要成立，缺一即回归）：
       ① 无 `/` 的**裸文件名**一律按 `ui/` 前缀（代码内 DEMO_BG_CANDIDATES 等）；
       ② 外挂覆盖 `window.UI_ASSET_BASE` / `window.UI_ASSET_ROOT` 行为不变 ——
          两者都接受「assets 父目录」写法；**历史夹具**写的是「ui/ 子树的根」
          （如 `'../../krkr/assets/ui/'`），故这里先把末尾的 `ui/` 归一掉再拼，两代写法都能用。 */
  var ASSET_BASE = String(window.UI_ASSET_ROOT || window.UI_ASSET_BASE
    || ('../' + String(L.asset_root || 'krkr/assets/ui/'))).replace(/(^|\/)ui\/?$/, '$1');
  var ASSET_ROOT = ASSET_BASE;      // 同义别名（对外探针沿用 ASSET_ROOT 这个名字）

  /* ==========================================================================
     1. 屏清单快照
     ── 来源：UI组/layout/screens/_index.json（M0 维护）
     ── 用途：**仅**用于 ① 复核工具条的屏切换下拉；② 屏数据尚未产出时的
              「该界面尚未产出布局数据」占位屏内容（id / 中文名 / 归属 / 必需元素）。
     ── 不参与任何坐标计算；屏数据一旦出现在 UI_LAYOUT.screens 中即以数据为准。
     ========================================================================== */
  var SCREEN_CATALOG = [
    { id: 'title',     title_cn: '标题画面',                owner: 'M0', required: ['标题文字', '副标题', '主菜单 6 项', '版权行', '背景图'] },
    { id: 'dialog',    title_cn: '对话框/名字框/系统条/选择肢', owner: 'M0', required: ['对话窗底', '名字框', '正文文本区', '系统条 8 键', '选择肢列表', '文本光标'] },
    /* ★ M45：`sysmenu`（系统菜单）条目**已删除** —— 该屏已整体废除（用户 2026-09-23 裁定：
       「现在废除『系统菜单 sysmenu』页，因为我们已有药丸按钮系统」）。系统功能由右端竖排
       快捷条（`quickbar`）承担；`open_sysmenu` **动作**保留（语义＝展开竖条），但不再有屏。 */
    /* ★ M46（2026-09-23，用户裁定）：`sysbar`（系统条）屏**已删除**（用户原话「把系统条
       sysbar 页删了，但底条素材保留（防冲突）」）—— 本目录（`SCREEN_CATALOG`）与复核页
       导航**从来就没有 `sysbar` 条目**（同 `quickbar`/`choices`/`dress`：这四屏只以
       `UI_LAYOUT.screens` 数据驱动，不进 catalog）⇒ 本轮数据侧删除后本表**无需增删条目**。
       该屏自 M34 建立起就不可达（无任何动作能打开它），删除后仍不可达；屏数据快照与回滚见
       `_工作\M46_旧素材归档\`。**素材一律保留原位**（`x_ui_sysbar.png` 与流程图屏 `fc.sysbar` 共用）。 */
    { id: 'confirm',   title_cn: '确认框',                  owner: 'M5', required: ['九宫格边框', '提示文本', '是/否 按钮'] },
    { id: 'loading',   title_cn: '加载提示',                owner: 'M5', required: ['居中提示图 320×120', '全屏遮罩'] },
    { id: 'save',      title_cn: '存档',                    owner: 'M5', required: ['底图', '槽列表 8 槽', '槽内缩略图/日期/摘要', '翻页', '返回'] },
    { id: 'load',      title_cn: '读档',                    owner: 'M5', required: ['底图', '槽列表 8 槽', '翻页', '返回'] },
    { id: 'config',    title_cn: '配置',                    owner: 'M5', required: ['底图', '设置项列表 ≥12 项', '说明栏', '返回'] },
    { id: 'backlog',   title_cn: '回想',                    owner: 'M5', required: ['底板', '文本列表', '滚动条', '返回'] },
    { id: 'gallery',   title_cn: 'CG 画廊',                 owner: 'M5', required: ['底板', '缩略图网格', '页码', '返回'] },
    { id: 'music',     title_cn: '音乐鉴赏',                owner: 'M5', required: ['底板', '曲目条列表', '播放控制', '返回'] },
    { id: 'ending',    title_cn: '片尾（STAFF/歌词）',        owner: 'M5', required: ['滚动区', '歌词条', '跳过'] },
    /* ★ M43：`chapter`（主线·章节选择）条目**已删除** —— 该屏已整体移除（用户 2026-09-23 裁定），
       剧情入口改由 `flowchart` 屏的 `fc.jump_hit`（动作 `flow_enter`）承担。 */
    { id: 'fragment',  title_cn: '番外（Fragment）选择',     owner: 'M4', required: ['碎片格阵', '未解锁态', '收集计数', '详情栏', '进入键', '返回'] },
    { id: 'flowchart', title_cn: '剧情流程图',               owner: 'M4', required: ['节点三态（已读/可去/未解锁）', '连线', '当前节点标记', '图例', '返回'] },
    /* M15：第 16 屏。屏对象带 overlay:true —— 叠在对话框之上的浮层，不是独立屏。 */
    { id: 'sysicons',  title_cn: '右键图标浮层',            owner: 'M13', required: ['全屏压暗遮罩', '9 个功能图标（3×3）', '每项热区', '点击空白关闭热区'] }
  ];

  /* ==========================================================================
     2. 演示台词（**真实中文台词，非自造剧情**）
     ── 来源：资源组/剧本/scene_ot.jsonl  →  场景 ot_s01_08c0
              「ＢＥＮＴＯ　ＦＯＲ　ＹＯＵ」（route: s01 鹰志线）
              lines[].seq 3–123（对应 s01_08c0.sob 的行号见 lineno 字段）
              选择肢取自同一场景的 choices[]（文本为该 jsonl 的 text_cn 原样）
              分支目标取自同一场景的 next[]（s01_08c1 / s01_08c2 / s01_08c3）
     ── 由 _工作/M3_证据/mk_demo_script.py 注入，未做任何改写。
     ========================================================================== */
  var DEMO_SCRIPT = /*__DEMO_SCRIPT_JSON__*/
  {
   "scene_id": "ot_s01_08c0",
   "scene_title_cn": "ＢＥＮＴＯ ＦＯＲ ＹＯＵ",
   "scene_route": "s01 鹰志线",
   "source": "ot",
   "source_file": "资源组/剧本/scene_ot.jsonl",
   "lineno_basis": "s01_08c0.sob 行号（scene_ot.jsonl lines[].lineno）",
   "seq_scope": [
    3,
    123
   ],
   "line_count": 121,
   "lines": [
    {
     "seq": 3,
     "lineno": 13,
     "kind": "dialogue",
     "speaker": "高内",
     "cn": "“班长，给我过来一下”"
    },
    {
     "seq": 4,
     "lineno": 15,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“嗯？”"
    },
    {
     "seq": 5,
     "lineno": 17,
     "kind": "other",
     "speaker": "",
     "cn": "午休。我正想去食堂买面包，高内同学叫住了我。真伤脑筋，不快点去的话面包马上就卖光了。"
    },
    {
     "seq": 6,
     "lineno": 19,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“什么事”"
    },
    {
     "seq": 7,
     "lineno": 21,
     "kind": "other",
     "speaker": "",
     "cn": "但也不能无视她，我走向高内同学的桌子。但愿两三句话就能结束。"
    },
    {
     "seq": 8,
     "lineno": 25,
     "kind": "dialogue",
     "speaker": "高内",
     "cn": "“不好意思啦，纪念册这个，能帮我按学号顺序整理一下吗”"
    },
    {
     "seq": 9,
     "lineno": 28,
     "kind": "other",
     "speaker": "",
     "cn": "高内同学的桌上，一沓用夹子夹住的稿纸啪地落了下来。一眼看去，绝不是午休时间能处理完的量。而且——"
    },
    {
     "seq": 10,
     "lineno": 31,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“——这个工作，按前几天定下的分工，应该是高内同学你们那组做的吧……”"
    },
    {
     "seq": 11,
     "lineno": 35,
     "kind": "dialogue",
     "speaker": "高内",
     "cn": "“是啊，嗯。所以我才拜托你嘛。你不明白？”"
    },
    {
     "seq": 12,
     "lineno": 37,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶”"
    },
    {
     "seq": 13,
     "lineno": 40,
     "kind": "other",
     "speaker": "",
     "cn": "她把稿纸往我这边用力一推。快从桌上掉下去了，我不由得接住。"
    },
    {
     "seq": 14,
     "lineno": 44,
     "kind": "dialogue",
     "speaker": "高内",
     "cn": "“呐，可以吧，拜托了羽田——。你把这个做了，之前你放我鸽子那事也能一笔勾销，谁也不欠谁了嘛。嗯？行吧？”"
    },
    {
     "seq": 15,
     "lineno": 49,
     "kind": "other",
     "speaker": "",
     "cn": "高内同学啪地拍了一下我的屁股。不疼，但那一瞬间，我觉得稿纸变沉了。"
    },
    {
     "seq": 16,
     "lineno": 52,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“嗯，那个……”"
    },
    {
     "seq": 17,
     "lineno": 54,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“嗯……”"
    },
    {
     "seq": 18,
     "lineno": 56,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“知道了”"
    },
    {
     "seq": 19,
     "lineno": 63,
     "kind": "dialogue",
     "speaker": "高内",
     "cn": "“哎呀，不愧是班长！那我现在要去吃午饭了，拜托你啦～”"
    },
    {
     "seq": 20,
     "lineno": 67,
     "kind": "other",
     "speaker": "",
     "cn": "高内同学从包里掏出钱包，跑向总跟她在一起的两个朋友那里去了。"
    },
    {
     "seq": 21,
     "lineno": 73,
     "kind": "other",
     "speaker": "",
     "cn": "我反过来把钱包收起来，把稿纸啪地放到桌上。本来坐在我桌上的鸿野君哼哼着挪开屁股，给我腾出了干活的空间。"
    },
    {
     "seq": 22,
     "lineno": 76,
     "kind": "other",
     "speaker": "",
     "cn": "我取下夹住厚厚一沓稿纸的夹子，毫无意义地一张张翻着。我不知道自己想做什么，但大概是不想让班上的同学看到我什么都没干地坐着。"
    },
    {
     "seq": 23,
     "lineno": 79,
     "kind": "other",
     "speaker": "",
     "cn": "翻到最后一页时，我忽然想起以前吃过的蔬菜三明治的味道。里面有我不擅长的黄瓜，青涩味很冲，真难受。"
    },
    {
     "seq": 24,
     "lineno": 82,
     "kind": "other",
     "speaker": "",
     "cn": "我又回到第一页。然后又翻了起来。自己果然还是不知道在做什么。但我明白，要停下这无意义的动作是件相当痛苦的事。"
    },
    {
     "seq": 25,
     "lineno": 84,
     "kind": "other",
     "speaker": "",
     "cn": "开始第三次翻页时，我莫名地想起了高内同学。她现在大概在食堂挑菜单吧。"
    },
    {
     "seq": 26,
     "lineno": 86,
     "kind": "other",
     "speaker": "",
     "cn": "嗯，总比高内同学不吃午饭饿着肚子好嘛。我无论何时都想成为别人的力量。赶紧做完吧。"
    },
    {
     "seq": 27,
     "lineno": 88,
     "kind": "other",
     "speaker": "",
     "cn": "我停下手。把稿纸立起来，在桌上咚咚地磕齐下边。好，干吧——"
    },
    {
     "seq": 28,
     "lineno": 91,
     "kind": "dialogue",
     "speaker": "声音",
     "cn": "“做完了？”"
    },
    {
     "seq": 29,
     "lineno": 93,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶？”"
    },
    {
     "seq": 30,
     "lineno": 98,
     "kind": "other",
     "speaker": "",
     "cn": "我鼓起劲卷起校服的袖子，渡来同学出现了。"
    },
    {
     "seq": 31,
     "lineno": 100,
     "kind": "other",
     "speaker": "",
     "cn": "她把手背在身后，心神不宁地晃着。怎么回事，看起来比平时沉不住气——"
    },
    {
     "seq": 32,
     "lineno": 102,
     "kind": "other",
     "speaker": "",
     "cn": "——我正这么想着，她先开了口。"
    },
    {
     "seq": 33,
     "lineno": 106,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“好像看到你跟高内在说话，事情已经办完了？”"
    },
    {
     "seq": 34,
     "lineno": 108,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“不，与其说办完了，不如说活儿才刚要开始……诶，怎么，你找我有事？”"
    },
    {
     "seq": 35,
     "lineno": 112,
     "kind": "other",
     "speaker": "",
     "cn": "我不由得问了出来。回过神时，渡来同学正板着一副莫名的苦脸。"
    },
    {
     "seq": 36,
     "lineno": 114,
     "kind": "other",
     "speaker": "",
     "cn": "可是她没回答我的问题。不如说根本没在听我说话的样子。她把背在身后的手松开，一下子把什么东西怼到我眼前。"
    },
    {
     "seq": 37,
     "lineno": 120,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“这个”"
    },
    {
     "seq": 38,
     "lineno": 122,
     "kind": "other",
     "speaker": "",
     "cn": "她一脸眉心紧皱的僵硬表情。渡来同学不知为何好像在生气。至少在我记忆里，没有惹她不高兴的事。"
    },
    {
     "seq": 39,
     "lineno": 124,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“这个？这是什么？”"
    },
    {
     "seq": 40,
     "lineno": 126,
     "kind": "other",
     "speaker": "",
     "cn": "那个用黄色布包着的长方体，飘出温热的空气，以及对空腹的身体来说难以忍耐的香味。"
    },
    {
     "seq": 41,
     "lineno": 129,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“给男朋友做了便当带过来”"
    },
    {
     "seq": 42,
     "lineno": 131,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶”"
    },
    {
     "seq": 43,
     "lineno": 133,
     "kind": "other",
     "speaker": "",
     "cn": "渡来同学给我？哈？什么？"
    },
    {
     "seq": 44,
     "lineno": 135,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶，为什么——”"
    },
    {
     "seq": 45,
     "lineno": 137,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“还问为什么，我们不是男女朋友吗。做个便当不是理所当然的嘛”"
    },
    {
     "seq": 46,
     "lineno": 139,
     "kind": "other",
     "speaker": "",
     "cn": "渡来同学一言不发，把餐巾包一个劲儿地往我这边推。看意思是要我收下。"
    },
    {
     "seq": 47,
     "lineno": 141,
     "kind": "other",
     "speaker": "",
     "cn": "高兴。非常高兴。可她的表情明显不正常。这到底是怎么回事。是有什么内情吗。我真的可以收下吗。"
    },
    {
     "seq": 48,
     "lineno": 143,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“那个，你为什么在生气”"
    },
    {
     "seq": 49,
     "lineno": 145,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“哈？我可没在生气啊”"
    },
    {
     "seq": 50,
     "lineno": 147,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶，可是……”"
    },
    {
     "seq": 51,
     "lineno": 149,
     "kind": "other",
     "speaker": "",
     "cn": "表情和声音都只能让人觉得她在不高兴。怎么回事。难道我在没察觉的地方犯了什么失态的事吗。"
    },
    {
     "seq": 52,
     "lineno": 151,
     "kind": "other",
     "speaker": "",
     "cn": "我一直不收下，周围便传来了窃窃私语。现在才发现，刚才明明还吵吵嚷嚷的，此刻却几乎听不到闲聊的声音了。"
    },
    {
     "seq": 53,
     "lineno": 153,
     "kind": "other",
     "speaker": "",
     "cn": "取而代之，压低了音量的窃窃私语里传来我的名字。其间还夹着渡来同学的名字。"
    },
    {
     "seq": 54,
     "lineno": 155,
     "kind": "other",
     "speaker": "",
     "cn": "难道说，我现在正把全班的视线都吸引过来了吗。这么一想，就觉得好丢人。"
    },
    {
     "seq": 55,
     "lineno": 160,
     "kind": "other",
     "speaker": "",
     "cn": "回过神时，渡来同学的脸颊也淡淡地染上了红晕。板着生气的脸却满脸通红的渡来同学，我竟觉得那样也挺可爱的。"
    },
    {
     "seq": 56,
     "lineno": 162,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“什么？”"
    },
    {
     "seq": 57,
     "lineno": 164,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“啊，不是……我在想该怎么办才好”"
    },
    {
     "seq": 58,
     "lineno": 166,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“什么。不收下，就是说你不要了吧”"
    },
    {
     "seq": 59,
     "lineno": 168,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“不，我想要……可是，诶，那这个，我可以收下吗？”"
    },
    {
     "seq": 60,
     "lineno": 170,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“可以哦？”"
    },
    {
     "seq": 61,
     "lineno": 172,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“嗯，谢谢，可是你为什么在生气……”"
    },
    {
     "seq": 62,
     "lineno": 174,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“都说了我没生气。别管了——”"
    },
    {
     "seq": 63,
     "lineno": 188,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“——就、就是觉得丢人啦，你快点收下啊！”"
    },
    {
     "seq": 64,
     "lineno": 190,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“啊”"
    },
    {
     "seq": 65,
     "lineno": 199,
     "kind": "other",
     "speaker": "",
     "cn": "我慌忙把手伸过去。手上一沉。比想象中更有分量。"
    },
    {
     "seq": 66,
     "lineno": 201,
     "kind": "other",
     "speaker": "",
     "cn": "可渡来同学刚才说了，她觉得丢人。"
    },
    {
     "seq": 67,
     "lineno": 203,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“啊啊，这样啊。什么嘛。渡来同学，你不是在生气，而是——”"
    },
    {
     "seq": 68,
     "lineno": 205,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“——是在害羞啊”"
    },
    {
     "seq": 69,
     "lineno": 207,
     "kind": "other",
     "speaker": "",
     "cn": "原来如此，渡来同学一害羞，看起来就像在生气啊。"
    },
    {
     "seq": 70,
     "lineno": 211,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“吵死了”"
    },
    {
     "seq": 71,
     "lineno": 213,
     "kind": "other",
     "speaker": "",
     "cn": "她红着脸瞪了我一眼。"
    },
    {
     "seq": 72,
     "lineno": 217,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“那种事，就算发现了也别说出来啊”"
    },
    {
     "seq": 73,
     "lineno": 219,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“啊，也对。抱歉。不过太好了，渡来同学并不是在生气”"
    },
    {
     "seq": 74,
     "lineno": 223,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“呼～！”"
    },
    {
     "seq": 75,
     "lineno": 225,
     "kind": "other",
     "speaker": "",
     "cn": "她突然大大地呼了一口气。之后，表情就像肩膀卸了力一样缓和下来。"
    },
    {
     "seq": 76,
     "lineno": 229,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“啊——好紧张”"
    },
    {
     "seq": 77,
     "lineno": 231,
     "kind": "other",
     "speaker": "",
     "cn": "语气也少了棱角。"
    },
    {
     "seq": 78,
     "lineno": 235,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“早知道这么丢人，果然还是别带来比较好”"
    },
    {
     "seq": 79,
     "lineno": 237,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶？”"
    },
    {
     "seq": 80,
     "lineno": 241,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“我是那种一到正式场合就不行的类型。反过来说，也可能是在站上舞台之前，我都意识不到事情有多大”"
    },
    {
     "seq": 81,
     "lineno": 243,
     "kind": "other",
     "speaker": "",
     "cn": "渡来同学还真是常常喜欢用不读字里行间就听不懂的方式说话啊。"
    },
    {
     "seq": 82,
     "lineno": 245,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“什么意思？”"
    },
    {
     "seq": 83,
     "lineno": 249,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“你看，我不是欠着羽田君一个人情嘛”"
    },
    {
     "seq": 84,
     "lineno": 253,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“然后，上次羽田君说中午是面包派嘛。那我想着反正自己也要做，顺便给你带一份吧。嗯，就这样”"
    },
    {
     "seq": 85,
     "lineno": 257,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“唔～，在班上大家面前我们不是男女朋友嘛，我还想着递个便当而已算什么普通事……好难啊。啊——好丢人。再也不带来了”"
    },
    {
     "seq": 86,
     "lineno": 261,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“嘛，吃吧羽田君”"
    },
    {
     "seq": 87,
     "lineno": 263,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“嗯”"
    },
    {
     "seq": 88,
     "lineno": 268,
     "kind": "other",
     "speaker": "",
     "cn": "她把在我前面的椅子转过来，用优雅的动作稳稳坐下。"
    },
    {
     "seq": 89,
     "lineno": 271,
     "kind": "other",
     "speaker": "",
     "cn": "她一言不发地打开了包布，我也跟着照做。里面整整齐齐地排着那几样堪称便当代名词的配菜。"
    },
    {
     "seq": 90,
     "lineno": 273,
     "kind": "other",
     "speaker": "",
     "cn": "我在羽田家偶尔也会做点东西，所以渡来同学的厨艺水平，我一看就清楚了。"
    },
    {
     "seq": 91,
     "lineno": 275,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“嘿，原来渡来同学做菜这么厉害”"
    },
    {
     "seq": 92,
     "lineno": 279,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“对了，我们聊聊全球变暖之类的话题吧”"
    },
    {
     "seq": 93,
     "lineno": 281,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“诶，为什么要这么明显地岔开话题？”"
    },
    {
     "seq": 94,
     "lineno": 289,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“不、不、不，因为，太丢人了嘛……”"
    },
    {
     "seq": 95,
     "lineno": 292,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“为什么。难得渡来同学做菜这么棒，就聊这个嘛”"
    },
    {
     "seq": 96,
     "lineno": 296,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“拜托，饶了我吧。你别吃了也没关系”"
    },
    {
     "seq": 97,
     "lineno": 298,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“为什么。我要吃。别说那种话啦。难得你给我做的，我就是想吃渡来同学的便当啊”"
    },
    {
     "seq": 98,
     "lineno": 302,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“……谢谢”"
    },
    {
     "seq": 99,
     "lineno": 304,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“你看，这个煎蛋卷多好吃啊。我啊，最喜欢这种东西了”"
    },
    {
     "seq": 100,
     "lineno": 308,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“…………”"
    },
    {
     "seq": 101,
     "lineno": 312,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“……太好了，我做来是对的”"
    },
    {
     "seq": 102,
     "lineno": 314,
     "kind": "other",
     "speaker": "",
     "cn": "吃饭时，我忽然想起已达成的残务处理“２：在食堂吃鸡排＆炸虾套餐”，那行字忽然让我觉得难为情起来。"
    },
    {
     "seq": 103,
     "lineno": 316,
     "kind": "other",
     "speaker": "",
     "cn": "今天这顿午饭是三年里最高级的一顿——这一点，我就毫无异议地断言了吧。"
    },
    {
     "seq": 104,
     "lineno": 327,
     "kind": "other",
     "speaker": "",
     "cn": "果然，被塞过来的活儿一个午休根本做不完，放学后还在继续。"
    },
    {
     "seq": 105,
     "lineno": 330,
     "kind": "other",
     "speaker": "",
     "cn": "只是，也不能一口咬定这是苦修行。因为现在的我，有一个强力的伙伴。"
    },
    {
     "seq": 106,
     "lineno": 335,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“哎呀～。光让人干活，自己偷什么懒～”"
    },
    {
     "seq": 107,
     "lineno": 337,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“我没偷懒，只是稍微想了点事情而已”"
    },
    {
     "seq": 108,
     "lineno": 341,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“嗯，那种事就叫偷懒啊。羽田君，说不定是个大男子主义的家伙呢”"
    },
    {
     "seq": 109,
     "lineno": 343,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“怎么说呢。不过现在这状况，倒更像是老婆当家吧”"
    },
    {
     "seq": 110,
     "lineno": 347,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“什么”"
    },
    {
     "seq": 111,
     "lineno": 349,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“对、对不起。我确实稍微偷了下懒”"
    },
    {
     "seq": 112,
     "lineno": 353,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“嗯。那，你在想什么？”"
    },
    {
     "seq": 113,
     "lineno": 355,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“想什么，想渡来同学的事之类的”"
    },
    {
     "seq": 114,
     "lineno": 357,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“…………”"
    },
    {
     "seq": 115,
     "lineno": 361,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“诶？”"
    },
    {
     "seq": 116,
     "lineno": 363,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“因为我本来正绝望，觉得毕业纪念册的制作要全由我一个人来做。所以现在渡来同学能在这里，我真的非常感谢”"
    },
    {
     "seq": 117,
     "lineno": 365,
     "kind": "other",
     "speaker": "",
     "cn": "我有点不好意思，就没看渡来同学的脸，装出专心干活的样子。"
    },
    {
     "seq": 118,
     "lineno": 369,
     "kind": "other",
     "speaker": "",
     "cn": "可渡来同学特意把脸歪到旁边，探过来看这样的我。"
    },
    {
     "seq": 119,
     "lineno": 373,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“因为是我自己要求进羽田君这组的嘛。当然的啊”"
    },
    {
     "seq": 120,
     "lineno": 375,
     "kind": "dialogue",
     "speaker": "鹰志",
     "cn": "“没那回事。渡来同学愿意加入，我很高兴”"
    },
    {
     "seq": 121,
     "lineno": 379,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“高兴……”"
    },
    {
     "seq": 122,
     "lineno": 381,
     "kind": "other",
     "speaker": "",
     "cn": "她的嘴角缓缓地画出一道弧线。"
    },
    {
     "seq": 123,
     "lineno": 385,
     "kind": "dialogue",
     "speaker": "明日香",
     "cn": "“啊啊，组员当然是多点好嘛。哪怕只多一个人也更高兴，对吧，那肯定的”"
    }
   ],
   "choices": [
    {
     "text_cn": "不对，是因为渡来同学啊",
     "text_jp": "ちがうよ、渡来さんだからだよ"
    },
    {
     "text_cn": "是啊，正是如此呢",
     "text_jp": "そうだね、まさにその通りだね"
    },
    {
     "text_cn": "不，我一个人也足够了",
     "text_jp": "いや、おれ一人でも充分だけど"
    }
   ],
   "branch_targets": [
    "s01_08c1",
    "s01_08c2",
    "s01_08c3"
   ]
  };

  /* 演示背景候选（全部为 krkr/assets/ui/ 内的**真实素材**，按序取第一张可加载者）。
     仅用于填充 dynamic:"story_background" 层，属占位演示，非剧情素材。
     ★ M15：首位改为 `tl2_bg1.png` —— 它与 krkr 侧演示脚本用的**是同一张**
     （krkr/game/ui_demo_script.tjs 的 UIDemoBgAsset），且实测 1200×900
     与 content_boxes.ot（1920 基线下 360,90,1200,900）**完全同尺寸 ⇒ 1:1 摆放**，
     不再被 background-size:cover 拉伸。M15 逐屏对照因此把 dialog 的
     「演示背景不同」这一噪声降到最低（剩余差异只有演示台词不同，见 README）。 */
  var DEMO_BG_CANDIDATES = ['tl2_bg1.png', 'tl1_bg1.png', 'ui_bg01.png', 'gc_asu01.png'];

  /* ==========================================================================
     3. 工具
     ========================================================================== */
  function px(v) { return v + 'px'; }

  /* "@palette.<key>" → 色值；"#RRGGBB" 直写 → 原样；其余 → null */
  function col(v) {
    if (v === null || v === undefined) return null;
    if (typeof v === 'string' && v.charAt(0) === '@') {
      var k = v.replace(/^@/, '').replace(/^palette\./, '');
      return (PAL[k] !== undefined && PAL[k] !== null) ? String(PAL[k]) : null;
    }
    return String(v);
  }

  /* 0–255 → 0–1 */
  function opa(v) {
    if (v === null || v === undefined) return 1;
    var n = Number(v);
    if (isNaN(n)) return 1;
    if (n < 0) n = 0; if (n > 255) n = 255;
    return n / 255;
  }

  /* ★ M47：**命名空间感知**的资产解析（与 krkr 侧 ui_asset.tjs 的候选序、以及守门侧
     `verify_ui.py` 的 `asset_to_relpath()` 同口径）：
       · 有前缀（`ui/…` / `face/…`）→ `ASSET_BASE`（= `krkr/assets/`）+ **原串**
       · 裸文件名 → 补 `ui/` 前缀后再拼（老口径，逐字不变）
     ⇒ 现有 400+ 条 `ui/…` 引用解析结果与改动前**完全一致**，`face/…` 新增可用。 */
  function assetUrl(a) {
    var s = String(a);
    if (s.indexOf('/') < 0) s = 'ui/' + s;
    return ASSET_BASE + s;
  }

  /* 字号：元素 font.size 优先，回退 UI_LAYOUT.fonts.sizes.<role>，再回退 body */  function fontSize(f, role) {
    if (f && f.size !== null && f.size !== undefined) return Number(f.size);
    if (role && SIZES[role] !== null && SIZES[role] !== undefined) return Number(SIZES[role]);
    if (SIZES.body !== undefined) return Number(SIZES.body);
    return 24;
  }

  /* 行距：元素 line_spacing 优先，回退 UI_LAYOUT.fonts.line_spacing.<role> */
  function lineSpacing(e, role) {
    if (e.line_spacing !== null && e.line_spacing !== undefined) return Number(e.line_spacing);
    if (role && LSP[role] !== undefined) return Number(LSP[role]);
    if (LSP.body !== undefined) return Number(LSP.body);
    return 1.4;
  }

  /* ★ ISSUE-20260927-05（E3 二审）：**下伸部不被裁** —— `-webkit-line-clamp` 的裁切只在
     「文本真的超出 N 行」时才有语义；不超出时它唯一的作用是**把行盒之外的墨迹裁掉**
     （行盒 = 字号 × `line_spacing`，契约量，可为 1.0；字形盒 = 1.31–1.33 em ⇒ 行盒更矮时
     基线下方墨迹（`_` `g` `y` 等下伸部）落在行盒之外）。krkr 自绘文字按墨迹画、不裁 ⇒ 两端分叉
     （实测 `fc.node.0011_tx`「s01_14h」的 `_`：krkr 有、HTML 无 —— 见
     `_工作\ISSUE-20260927-05_流程图实现\取证\E3_下划线字形_两端差异.txt`）。
     ⇒ 做法：**先按不裁切铺一遍量自然行数，真的超行才加 `-webkit-line-clamp`**：
        · **未超行** ⇒ 不加 clamp（`display:block` + `overflow:visible`）⇒ 下伸部照画，
          行数与元素高度都与「加了 clamp 但没超行」时**相同** ⇒ 文字位置不变；
        · **超行**   ⇒ 加 clamp（`-webkit-box` + `-webkit-line-clamp:N` + `overflow:hidden`）
          ⇒ 截断语义与改动前**逐字相同**。
     ★ 测量时机：**必须在元素进入文档之后**（`buildText` 只把 inner 挂到 wrap 上，wrap 还在
       文档外 ⇒ `scrollHeight` 读出来是 0，会把超行误判成「不超行」——实测栽过）。
       故 buildText 只把候选登记进 `clampCands`，由 `renderElements` 在**整屏元素都 append 完**
       之后统一判定：先**读**一遍（一次布局）、再对需要的那批**写** clamp（第二次布局）。
     ⚠ 两个反例（实测，别再走）：
       ① 「加 clamp 后量 `scrollHeight` 判断是否超行」——量不出来：clamp 会把 scrollHeight 截到
          N 行（实测超长文本仍报 `scrollHeight == N×行盒`）⇒ 必须先量、后加；
       ② 「给裁切盒加 `padding-bottom` 把下伸部让出来」——**超行时第 N+1 行的字顶就在行盒底 +2px**
          （而第 N 行下伸部要到 +3px），同一竖直带里两者无法用一条水平裁切界分开 ⇒ 实测会露出
          下一行字顶（夹具第 3 行带出现 986 个文字色像素），且 padding 还会连带抬高居中 ⇒ 不用。 */
  var clampCands = null;             // 本次 renderElements 期间登记、屏内元素入文档后统一判定
  function applyClamp(inner, maxLines) {
    inner.style.display = '-webkit-box';
    inner.style.webkitBoxOrient = 'vertical';
    inner.style.webkitLineClamp = String(maxLines);
    inner.style.overflow = 'hidden';
  }
  function resolveClampCands() {
    if (!clampCands || !clampCands.length) return;
    var list = clampCands; clampCands = null;      // 防重入（判定期间不再登记）
    var i, c;
    for (i = 0; i < list.length; i++) {            // ① 统一读（首次读触发一次布局）
      c = list[i];
      try { c.nat = c.inner.scrollHeight; } catch (e) { c.nat = null; }
    }
    for (i = 0; i < list.length; i++) {            // ② 只给真的超行的加 clamp
      c = list[i];
      /* 判据用**行数**而不是块高比大小：实测自然块高 = 行数 × 行盒 + 常数尾巴（微软雅黑@19px
         为 +3px，来自末行行盒的小数进位），直接比 `nat <= N×行盒` 会把「正好 N 行」的标签
         误判成超行（实测 `fc.node.0007_tx`：2 行 = 41px > 38px ⇒ 误裁、括号下伸部仍被切）。
         四舍五入到行数后该尾巴被吸收（3 < 行盒/2）⇒ 稳健。 */
      var lines = isFinite(c.nat) ? Math.round(c.nat / c.lh) : NaN;
      var fits = isFinite(lines) && lines <= c.maxLines;
      if (!fits) applyClamp(c.inner, c.maxLines);  // 量不到（NaN）⇒ 保守：按超行处理（= 改动前行为）
    }
  }

  /* 字体回退链：f（元素 font 规格）给了 faces 就用它，否则用全局 fallback_faces。
     逐元素覆盖用于「某个屏要用特定字体」的场景（如标题菜单用 DejaVu Sans Mono Bold）。 */
  function fontChain(f) {
    var faces = (f && f.faces && f.faces.length) ? f.faces : (FONTS.fallback_faces || []);
    var parts = faces.map(function (x) { return '"' + String(x).replace(/"/g, '') + '"'; });
    parts.push('sans-serif');
    return parts.join(',');
  }

  /* 单向 offset 阴影（既有机制，字段 font.shadow / shadow_color / shadow_ofs）。 */
  function textShadow(f) {
    if (!f || !f.shadow) return null;
    var o = (f.shadow_ofs === null || f.shadow_ofs === undefined) ? 0 : Number(f.shadow_ofs);
    return px(o) + ' ' + px(o) + ' 0 ' + (col(f.shadow_color) || '#000000');
  }

  /* ★ M38（2026-09-23）：**文字四向描边** —— 与 krkr 侧逐项对应的同构实现。
     krkr 端：`krkr/game/ui_theme.tjs` 的 `uiThemeDrawOutline()`（在 `uiThemeDrawLine()` 里
              先按 8 个方向用 outline_color 各画一次同文本，**最后画正文**）；
     本端：    用**同样 8 个方向**的 text-shadow 表达（CSS 的多重 text-shadow 天生按
              声明顺序层叠、字形本体恒在最上层 ⇒ 与「先描边后正文」等价）。

     方向表（**两端同序同向，改一处必须改两处**；偏移量 = 方向 × outline_width）：
       ① (1,0)  ② (-1,0)  ③ (0,1)  ④ (0,-1)  ⑤ (1,1)  ⑥ (-1,1)  ⑦ (1,-1)  ⑧ (-1,-1)
     宽度：`font.outline_width`（px，缺省 1，与 krkr 的 UIThemeOutlineDefaultWidth 同值）。

     ⚠️ **描边只影响渲染，绝不参与布局**：本函数不进任何度量路径（buildText 里换行/截断
        仍按 `e.w / e.max_lines` 与正文文本计算），与 krkr 的 uiThemeWrap/uiThemeLayoutText
        只按正文度量完全一致。 */
  function textOutlineShadow(f) {
    if (!f || !f.outline) return null;
    var w = (f.outline_width === null || f.outline_width === undefined) ? 1 : Number(f.outline_width);
    if (!(w > 0)) return null;
    var c = col(f.outline_color) || '#000000';
    var dirs = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, 1], [1, -1], [-1, -1]];
    return dirs.map(function (d) {
      return px(d[0] * w) + ' ' + px(d[1] * w) + ' 0 ' + c;
    }).join(', ');
  }

  /* 阴影 + 描边合成一条 text-shadow（描边在前、阴影在后；两者都关则返回 null）。
     两字段可共存，但对话框屏按用户裁决**只用描边**（shadow:false），避免双重发虚。 */
  function textShadowAll(f) {
    var ol = textOutlineShadow(f), sh = textShadow(f);
    if (!ol && !sh) return null;
    return [ol, sh].filter(Boolean).join(', ');
  }

  /* content_box：支持 "@auto"（运行期定源，取当前演示源）与具体源代号 */
  function resolveBox(e) {
    var b = { x: e.x, y: e.y, w: e.w, h: e.h };
    var cbName = e.content_box;
    if (!cbName) return b;
    var key = (cbName === '@auto') ? state.demoSource : cbName;
    var cb = BOXES[key];
    if (cb) b = { x: cb.x, y: cb.y, w: cb.w, h: cb.h };
    return b;
  }

  function applyBox(el, b) {
    if (b.x !== null && b.x !== undefined) el.style.left = px(b.x);
    if (b.y !== null && b.y !== undefined) el.style.top = px(b.y);
    if (b.w !== null && b.w !== undefined) el.style.width = px(b.w);
    if (b.h !== null && b.h !== undefined) el.style.height = px(b.h);
  }

  /* z 序 → CSS z-index。
     layout 的 z 允许重复（同 z 按声明顺序），故映射为 z*100 + 声明序号，
     保持「先按 z、再按声明顺序」的严格同序关系。
     ★ M3：`curZBase` = 附加层（屏级 attach）整体加在承载屏之上的偏移。
       承载屏自身 z 最高可到 30（dialog 的 dlg.choices；★ M38 起 dlg.window 已随无框化退场），
       而附加层（quickbar）
       的 z 从 28 起（M37 的形态：药丸 28 / 白字 30 / 圆形 icon 90 / 钉住叠层 93 / 热区 95）
       —— 原样写 z-index 会让附加层的低 z 元素被承载屏的高 z 元素盖住，与契约「附加层压在
       上层、点击优先级高于承载屏」矛盾。故叠画附加层前把偏移置为「承载屏最大 z-index + 1」，
       附加层内部的相对次序保持不变（仍是 z*100 + 声明序）。 */
  var curZBase = 0;
  function zIndex(e, orderIdx) {
    var z = (e.z === null || e.z === undefined) ? orderIdx : Number(e.z);
    return curZBase + z * 100 + orderIdx;
  }

  function mk(tag, cls) {
    var d = document.createElement(tag);
    if (cls) d.className = cls;
    return d;
  }

  /* 缺件占位：可读报错，不崩 */
  function missingLabel(text) {
    var d = mk('div', 'ui-missing-label');
    d.style.fontSize = px(fontSize(null, 'small'));
    d.textContent = text;
    return d;
  }

  /* ★ M15：全零九宫格判定。`nine:{l:0,t:0,r:0,b:0}` 在 krkr 侧是**合法的「整图缩放」**
     （uiWidgetNine 只画中格），但 HTML 侧**不能**用 border-image 表达：border-width
     全为 0 时 border-image 不绘制任何像素 → 图整块消失（M18 在 复刻\flow.html 实测，
     见 _工作\M18_报告.md §5.2）。故全零 nine 必须改走普通 <img>/background 整图拉伸，
     且**不校验 w/h 与 PNG 实尺寸**——该写法下二者本就不同（flowchart 方框 0.4785×）。 */
  function isZeroNine(n) {
    return !!n && Number(n.l) === 0 && Number(n.t) === 0
                && Number(n.r) === 0 && Number(n.b) === 0;
  }

  /* ★ M06：逐块按钮（`item_buttons`）/ 逐块文案区（`item_text`）守卫的判词出口。
     判词字面量与 krkr 侧 `uiWidgetItemBtnReject` **逐字相同**（`★M06ITEMBTN-REJECT★ <list>[<key>] <理由>`）
     —— 两端同一套判据、同一个判词串，审查可逐条对账；去重后同时进 `console.warn` 与
     `state.backlog.rejects`（后者供 `?selftest=1` / 自检页机检）。 */
  function itemBtnReject(listId, key, reason) {
    var line = '★M06ITEMBTN-REJECT★ ' + listId + '[' + key + '] ' + reason;
    if (state.backlog && state.backlog.rejects && state.backlog.rejects.indexOf(line) < 0)
      state.backlog.rejects.push(line);
    try { console.warn('[UI][REJECT] ' + line); } catch (e) { }
    return line;
  }

  /* ★ M1（ISSUE-20260924-08）：`item_variants`（栏位内差分翻页）守卫的判词出口。
     判词字面量与 krkr 侧 `uiWidgetItemVariantReject` **逐字相同**
     （`★M08VARIANT-REJECT★ <list>[<key>] <理由>`）—— 两端同一套判据、同一个判词串。
     去重后同时进 `console.warn` 与 `state.gallery.rejects`（供自检页/探针机检）。 */
  function variantReject(listId, key, reason) {
    var line = '★M08VARIANT-REJECT★ ' + listId + '[' + key + '] ' + reason;
    if (state.gallery && state.gallery.rejects && state.gallery.rejects.indexOf(line) < 0)
      state.gallery.rejects.push(line);
    try { console.warn('[UI][REJECT] ' + line); } catch (e) { }
    return line;
  }

  /* ★ M1：`item_variants` 的字段校验 —— **绘制、命中、自检守卫共用这一套**
     （与 krkr 侧 uiWidgetItemVariantProblems / uiWidgetItemVariantRowProblem 逐条同口径）。 */
  function variantsOf(e) {
    if (!e || e.item_variants === null || e.item_variants === undefined) return null;
    var v = e.item_variants;
    if (typeof v !== 'object' || typeof v.length === 'number') return null;   // 数组 ⇒ 非对象
    return v;
  }
  function variantFrames(e) {
    var v = variantsOf(e);
    if (!v) return null;
    var fr = v.frames;
    if (!fr || typeof fr !== 'object' || typeof fr.length !== 'number') return null;
    return fr;
  }
  function variantRow(e, row) {
    var fr = variantFrames(e);
    if (!fr) return null;
    if (row < 0 || row >= fr.length) return null;
    var r = fr[row];
    if (!r || typeof r !== 'object' || typeof r.length !== 'number') return null;
    return r;
  }
  function variantBtnKey(b, def) {
    if (!b || typeof b !== 'object') return def;
    var k = (b.key === null || b.key === undefined) ? '' : String(b.key);
    return (k === '') ? def : k;
  }
  function variantRectProblem(e, r, what, itemW, itemH) {
    if (r === null || r === undefined) return '';
    if (typeof r !== 'object') return what + '不是对象';
    var w = Number(r.w) || 0, h = Number(r.h) || 0;
    if (w <= 0 || h <= 0) return what + '零/负面积（' + w + '×' + h + '）';
    var x = Number(r.x) || 0, y = Number(r.y) || 0;
    if (x < 0 || y < 0 || x + w > itemW || y + h > itemH)
      return what + '出块（局部 ' + x + ',' + y + ' ' + w + '×' + h
        + ' 不在 ' + itemW + '×' + itemH + ' 内）';
    return '';
  }
  function variantBtnProblem(e, b, itemW, itemH) {
    if (!b || typeof b !== 'object') return '不是对象';
    var k = (b.key === null || b.key === undefined) ? '' : String(b.key);
    if (k === '') return '缺 key';
    var bw = Number(b.w) || 0, bh = Number(b.h) || 0;
    var bx = Number(b.x) || 0, by = Number(b.y) || 0;
    if (bw <= 0 || bh <= 0) return '矩形零/负面积（' + bw + '×' + bh + '）';
    if (bx < 0 || by < 0 || bx + bw > itemW || by + bh > itemH)
      return '矩形出块（局部 ' + bx + ',' + by + ' ' + bw + '×' + bh
        + ' 不在 ' + itemW + '×' + itemH + ' 内）';
    var act = (b.action === null || b.action === undefined) ? '' : String(b.action);
    if (act === '') return 'action 为空';
    if (!b.asset && !b.state_assets) return '既无 asset 也无 state_assets';
    return '';
  }
  function variantProblems(e, itemW, itemH) {
    var out = [];
    if (e.item_variants === null || e.item_variants === undefined) return out;
    var v = variantsOf(e);
    if (!v) { out.push({ key: '(item_variants)', reason: 'item_variants 不是对象' }); return out; }
    if (!variantFrames(e)) { out.push({ key: '(frames)', reason: 'frames 不是数组' }); return out; }
    var rp = variantBtnProblem(e, v.prev, itemW, itemH);
    if (rp !== '') out.push({ key: variantBtnKey(v.prev, 'prev'), reason: rp });
    var rn = variantBtnProblem(e, v.next, itemW, itemH);
    if (rn !== '') out.push({ key: variantBtnKey(v.next, 'next'), reason: rn });
    var rt = variantRectProblem(e, v.text, '文本区', itemW, itemH);
    if (rt !== '') out.push({ key: 'text', reason: rt });
    var rth = variantRectProblem(e, v.thumb, '缩略区', itemW, itemH);
    if (rth !== '') out.push({ key: 'thumb', reason: rth });
    if (v.edge !== null && v.edge !== undefined && String(v.edge) !== 'clamp')
      out.push({ key: 'edge', reason: 'edge 取值非法（只认 "clamp"）：' + String(v.edge) });
    return out;
  }
  function variantRowProblem(e, row) {
    if (variantsOf(e) === null) return '';
    var fr = variantFrames(e);
    if (!fr) return '';
    if (row < 0 || row >= fr.length) return '';
    var r = fr[row];
    if (r === null || r === undefined) return '';
    if (typeof r !== 'object' || typeof r.length !== 'number')
      return '第 ' + row + ' 栏差分列表不是数组';
    if (r.length === 0) return '';
    for (var i = 0; i < r.length; i++) {
      var a = r[i];
      if (a === null || a === undefined || typeof a !== 'string' || a === '')
        return '差分素材为空（第 ' + (i + 1) + ' 张）';
    }
    return '';
  }

  /* 探针：判断资产是否真的存在（file:// 下 new Image() 可用，无 CORS 限制） */
  function probe(url, ok, fail) {    var im = new Image();
    im.onload = function () { ok(url); };
    im.onerror = function () { fail(url); };
    im.src = url;
  }

  /* ==========================================================================
     4. 运行期状态
     ========================================================================== */
  var state = {
    screen: null,          // 当前屏 id（浮层打开时 = 浮层屏 id）
    underScreen: null,     // ★ M15：浮层屏的下层屏 id（非浮层时为 null）
    baseScreenId: null,    // ★ M15：下层容器当前承载的屏 id（判断能否原地保留 DOM）
    history: [],           // 屏历史（返回键回上一屏）
    demoSource: 'ot',      // content_box "@auto" 的当前源代号
    scale: 1,
    /* ★ M1（ISSUE-20260922-28）：屏级状态 flag（当前绘制屏）——对应 krkr 侧的
       `UIScrFlags`（ui_screens.tjs）。取值/重置语义见下方 §4.5 的四个函数。 */
    svFlags: {},
    /* ★ M3：当前屏附加层（屏级 `attach`）的屏 id；无附加层时为 null。
       附加层**不改「当前屏」语义**（state.screen 仍是承载屏），它只多画一层。 */
    attachId: null,
    /* ★ M1（ISSUE-20260924-08）：鉴赏模式运行期 ——
       · `varIdx`：栏位内差分序号，**嵌套** `{ <listId>: { <全局行号>: 序号 } }`
         （与 krkr 侧 `UIScrVarIdx` 同构；渲染器只读，换屏/切页签时按页清空）；
       · `rejects`：`★M08VARIANT-REJECT★` 判词台账（守卫的负向证据）；
       · `lastAct` / `lastRow` / `count` / `lastTab`：动作的可观测状态（自检与探针用，
         与 krkr 侧 `UIScrGalLastAct/LastRow/ActCount/LastTab` 同口径）。 */
    varIdx: {},
    gallery: { rejects: [], lastAct: '', lastRow: -1, count: 0, lastTab: '' },
    /* ★ M47：设置仓（设置键 → 值；缺键回落 SETTING_DEF 的 def）。对应 krkr 侧
       `krkr/game/ui_settings.tjs` 的 `UISettingStore`（读写 = `UISettingGet/Set`）。
       ⚠️ 键表精度如实写：**M47 第三轮（一审打回 C2）起**，本仓与 `UISettingDef` 一样是
       **25 键**（9 数值 + 16 开关键），键名 / kind / 值域 / 默认值**逐条与 `UISettingDef` 对齐**；
       在该轮之前只实现了 9 个数值键（越前面那句「两端逐字相同」当时**不成立**，已订正）。
       两端任一改动必须同步另一边。见 §4.7。 */
    settings: {},
    refs: {},              // 顶层屏 元素 id → { el, def }
    baseRefs: {},          // ★ M15：下层屏 元素 id → { el, def }（浮层打开时二者并存）
    dlg: {
      idx: 0, reveal: 0, typing: false, timer: null,
      skip: false, auto: false, hidden: false,
      choosing: false, done: false, autoTimer: null
    },
    /* ★ M43：流程图运行期状态（与 krkr 侧 UIFlowVisited / UIFlowCurrent / UIFlowCursor 同口径）。
       ready=false 表示尚未初始化（flow_data.js 未加载时保持 false，见 §7.0 flowEnsure）。 */
    flow: { ready: false, visited: {}, current: '', cursor: '' },
    /* ★ M06：回想屏逐块按钮的**可观测状态** + 守卫判词台账。
       `lastAct` / `lastRow` / `count` 与 krkr 侧 `UIScrBacklogLastAct` / `UIScrBacklogLastRow` /
       `UIScrBacklogActCount` 同名同义（「派发到的行号 = 点的那一行」的机检依据）；
       `rejects` 收 `★M06ITEMBTN-REJECT★` 判词（去重），供自检与审查对账。
       本轮语义 = **接口冻结/占位**：复刻层同样无音频 ⇒ 音频/跳转生效留给编程组。 */
    backlog: { lastAct: '', lastRow: -1, count: 0, lastBtn: null, rejects: [] },
    /* ★ E3（ISSUE-20260927-05）：连线（`links`）的**绘制台账** + 守卫判词台账。
       `drawn` 每条 = 一次成功绘制（折线必有，`polygon` 非空表示画了箭头三角）；
       `rejects` 收 `★E3LINKS-REJECT★ <id> <理由>`（去重）—— 自检 ㉒ 与审查据此对账。
       台账**不参与渲染**，只做机检依据（canvas 上的像素无法反查条数，故必须留账）。
       ★ 第 2 步（ISSUE-20260928-02）追加两个字段：
         · `blocked` —— 最近一次 `drawLinks` 是否因**层判据**（`fc_layer != main`）而**整批不画**
           （冻结 §四.1 的硬判据；自检 ㉔a 据它 + `drawn.length === 0` 双向对账）；
         · `layer` —— 该屏的**层 flag 名与当前值**（从数据推，见 `flowLayerFlagName`）。 */
    links: { drawn: [], rejects: [], blocked: false, layer: '' },
    /* ★ 第 2 步（ISSUE-20260928-02）：`flow_layer` 动作 + `current` 高亮环的**可观测状态**
       （与 krkr 侧 `ui_flow_links.tjs` 的层判据 / 环绘制同口径；台账不参与渲染，只做机检依据）。
         · `lastAct` / `lastLayer` / `count` —— 最近一次 `flow_layer` 派发的动作串、目标层、累计次数；
         · `flag` / `flagValue` —— 本屏层 flag 名与当前值（从数据推，非写死）；
         · `rejects` —— `★E3LAYER-REJECT★ <动作串> <理由>`（去重）；
         · `ring` —— 实际画出的高亮环逐条几何（自检 ㉔c 与数据对账；canvas 像素另作独立锚点）。 */
    flowLayer: { lastAct: '', lastLayer: '', count: 0, flag: '', flagValue: '', rejects: [] },
    ring: { drawn: [] }
  };

  var canvasEl = null;     // #canvas
  var layerEl = null;      // #canvas > 下层屏容器（base，z-index 0）
  var overlayEl = null;    // #canvas > 浮层屏容器（overlay:true 的屏，z-index 1）
  var toastEl = null;
  var toastTimer = null;

  /* ==========================================================================
     4.5 ★ M1（ISSUE-20260922-28）· 屏级状态 flag（可见性由数据驱动）
     —— 判定语义（**唯一定义**，与 krkr 侧 ui_screens.tjs 的 uiScreenElementVisible 逐字一致）：
        元素可见 / 可交互 ⟺ e.visible_default !== false
                           且（e.vis_flag 未给 → 通过；给了 → 当前 flag 值满足：
                                vis_when === '*' 时要求**非空字符串**，否则要求**严格相等**）
     —— 两端对应关系：
        state.svFlags  ↔ var UIScrFlags
        setFlag        ↔ uiScreenFlagSet     （返回值 = 是否发生变化）
        getFlag        ↔ uiScreenFlagGet     （未设置返回 ""）
        initFlagsFor   ↔ uiScreenFlagsInitFor
        elementVisible ↔ uiScreenElementVisible
     —— flag 名来源 = 该屏元素的 vis_flag ∪ reveal.flag ∪ reveal.tip_flag（**两端同一算法**）：
        TJS2 的 Dictionary 没有枚举接口（不能 for...in，见 引擎工作原理.md §5.1），
        故这边也不直接枚举 flags_default；未被引用的键不参与任何可见性判定 ⇒ 无行为差异。
     —— 本表是「当前绘制屏」的 flags。附加层（屏级 attach，如 quickbar 叠在 dialog 上）
        的 flag 与承载屏**共用同一张表**：叠画前把附加屏 `flags_default` 里承载屏**未定义**
        的键并进来（`mergeAttachFlags`，见 §4.6），**只为未定义键补初值、不重置运行值**
        （展开/收起/气泡/钉住这些 flag 在叠画之后仍要持续读写，切换+还原会在下次同步时被清空）。
        承载屏自己的 defaults 优先。（主代理 2026-09-22 已就此刻正 `layout/_schema.md` §四，
        两端同一口径；M2 侧对应 `uiScreenFlagsEnsureFor`。）
     ========================================================================== */
  /* ★ M3：flag 名口径（**两端同一算法**，从 initFlagsFor 里抽出来复用）——
     = 该屏元素的 vis_flag ∪ reveal.flag ∪ reveal.tip_flag ∪ reveal.pin_flag
     （`layout/_schema.md` §四「flag 名的枚举口径」：reveal 的**全部键**都要参与，
       含 2026-09-22 修复 C 补入的 pin_flag）。附加层并表（mergeAttachFlags）用的是同一口径。 */
  function flagNamesOf(def) {
    var names = [];
    if (!def) return names;
    (def.elements || []).forEach(function (e) { if (e && e.vis_flag) names.push(String(e.vis_flag)); });
    if (def.reveal) {
      if (def.reveal.flag) names.push(String(def.reveal.flag));
      if (def.reveal.tip_flag) names.push(String(def.reveal.tip_flag));
      if (def.reveal.pin_flag) names.push(String(def.reveal.pin_flag));
    }
    return names;
  }

  function initFlagsFor(screenId) {
    state.svFlags = {};
    var def = SCREENS[screenId];
    if (!def) return;
    var dflt = def.flags_default || {};
    flagNamesOf(def).forEach(function (n) {
      if (!n) return;
      var v = dflt[n];
      state.svFlags[n] = (v === null || v === undefined) ? '' : String(v);
    });
  }

  function getFlag(name) {
    if (name === null || name === undefined) return '';
    var v = state.svFlags[String(name)];
    return (v === null || v === undefined) ? '' : String(v);
  }

  /* 置值；返回 true = 值发生了变化（调用方据此决定是否重画 / 重新渲染） */
  function setFlag(name, value) {
    if (name === null || name === undefined || String(name) === '') return false;
    var nv = (value === null || value === undefined) ? '' : String(value);
    if (getFlag(name) === nv) return false;
    state.svFlags[String(name)] = nv;
    return true;
  }

  function elementVisible(e) {
    if (!e) return false;
    if (e.visible_default === false) return false;
    var n = e.vis_flag;
    if (n === null || n === undefined || String(n) === '') return true;
    var cur = getFlag(n);
    var want = (e.vis_when === null || e.vis_when === undefined) ? '' : String(e.vis_when);
    if (want === '*') return cur !== '';
    return cur === want;
  }

  /* ★ M1：flag 变化后，把**已渲染 DOM** 的显隐同步到最新值（不重建 DOM，保住
     hover/press 台账与运行期节点引用）。供 M2/M3 在 setFlag() 之后调用。
     只碰带 `vis_flag` 的元素 —— 其余元素的 display 由对话框运行期（打字机/隐藏窗口/
     选择肢）自己管，本函数不得越权复位。默认 flags 下不改变任何既有画面。 */
  function applyFlagVisibility() {
    [state.refs, state.baseRefs].forEach(function (map) {
      if (!map) return;
      Object.keys(map).forEach(function (id) {
        var r = map[id];
        if (!r || !r.def || r.def.vis_flag === undefined) return;
        r.el.style.display = elementVisible(r.def) ? '' : 'none';
      });
    });
  }

  /* ==========================================================================
     4.6 ★ M3（ISSUE-20260922-28）· 附加层（屏级 attach）与右端快捷条的呼出/收起
     —— **契约**（与 krkr 侧 M2 必须逐字一致；字段语义见 layout/_schema.md §四）：
       ① 附加层：承载屏（`10_dialog.json` 的 `attach:"quickbar"`）**元素画完之后**，
          把附加屏的元素渲染进**同一容器**；附加层的点击/悬停优先级高于承载屏
          ⇒ 其 z-index 整体上移（见 zIndex 的 curZBase）。
       ② 共用一张 flag 表：叠画前把附加屏 `flags_default` 里**承载屏未定义**的键
          填进 `state.svFlags`（承载屏自己的 defaults 优先）—— 附加层元素的 vis_flag
          判定、以及下面的呼出驱动，读写的是同一张表。
       ③ 附加层**不改「当前屏」语义**：`state.screen` 仍是承载屏 id，
          剧情推进 / 动作派发 / 屏历史都不受影响。
       ④ 呼出/收起（画布坐标；`in_x` / `out_x` / `delay_ms` / `pin_flag` / `tip_flag`
          一律读 `reveal`，脚本内**不写死任何一个**，含 flag 名 —— `layout/_schema.md` §四）：
            x ≥ in_x              → 置展开、撤销收起计时
            x < out_x             → 起 delay_ms 计时；到点才收起（flag=collapsed、
                                    tip_flag=""）；期间回到 ≥ out_x → 撤销计时
            滞回带 out_x ≤ x < in_x → 保持现状、撤销计时（避免边界抖动）
            钉住（`reveal.pin_flag` 的值为 "1"）→ 不自动收起（气泡仍随指针）
            指针离开画布（mouseleave）→ 按 x < out_x 处理（★ krkr 无等价事件，见 README §五.18）
            展开中 tip_flag = 「指针所在项 key」，不在任何项内 → ""
          每次改动后调用 applyFlagVisibility() 同步已渲染 DOM（**不重建 DOM**，
          以免打断 hover/press 台账与运行期节点引用）。
     ========================================================================== */
  /* 钉住 flag 名 —— **从数据读**（`reveal.pin_flag`，`layout/_schema.md` §四 ⑥）。
     数据里缺该键时返回 ""（= 本屏没有钉住功能：getFlag("") 恒为 ""、setFlag("", v) 恒为 false）。 */
  function pinFlagOf(reveal) {
    return (reveal && reveal.pin_flag) ? String(reveal.pin_flag) : '';
  }
  function isPinned(reveal) {
    var n = pinFlagOf(reveal);
    return n !== '' && getFlag(n) === '1';
  }

  /* 呼出驱动的运行期状态：收起计时器 + 最近一次指针位置（画布坐标，null = 不在画布内） */
  var revealRt = { timer: null, lastX: null, lastY: null };

  function attachIdOf(def) { return (def && def.attach) ? String(def.attach) : ''; }

  /* 把附加屏的 flag 初值并进当前表：**只填尚未存在的键**（承载屏 defaults 优先）。
     幂等 —— 重复调用不会改动已运行的 flag 值。 */
  function mergeAttachFlags(aid) {
    var ad = SCREENS[aid];
    if (!ad) return;
    var dflt = ad.flags_default || {};
    flagNamesOf(ad).forEach(function (n) {
      if (!n || state.svFlags[n] !== undefined) return;
      var v = dflt[n];
      state.svFlags[n] = (v === null || v === undefined) ? '' : String(v);
    });
  }

  /* 当前生效的呼出配置：优先「承载屏的附加层」（dialog 的 quickbar），
     其次本屏自身的 `reveal`（`?screen=quickbar` 单屏预览走这条）。
     浮层（sysicons）压在其上时不生效 —— 浮层是模态的，快捷条此时不可见也不可点。 */
  function activeReveal() {
    if (state.underScreen) return null;
    var aid = state.attachId;
    if (aid && SCREENS[aid] && SCREENS[aid].reveal) {
      return { def: SCREENS[aid], reveal: SCREENS[aid].reveal, owner: aid };
    }
    var sd = state.screen ? SCREENS[state.screen] : null;
    if (sd && sd.reveal) return { def: sd, reveal: sd.reveal, owner: state.screen };
    return null;
  }

  /* 指针所在项的 key；不在任何「有说明文字的项」内 → ""。
     口径（★ 主代理 2026-09-22 裁决 D1，**两端以此为准**；全部由数据推出，无坐标写死）：
       ① 候选 key 集 = 该屏内 `vis_flag == reveal.tip_flag 且 vis_when != "*"` 的元素取值
          —— 本数据即 `quick.tx_*` 的 lock/save/load/qsave/qload/auto/skip/next/prev/log/chart/option
          共 12 个（`quick.tips` 底图的 `vis_when="*"` 是「非空即显示」，不算候选）；
       ② 命中候选 = `kind=hit` 且 **`vis_flag` 非空** 且 id 尾段形如 `hit_<key>`（key 在 ① 的集合内）、
          且当前可见（收起态的项不参与）；
       ③ 矩形判定用**半开区间** `[x, x+w)` × `[y, y+h)`（与 krkr 侧 `uiScreenRevealTipAt` 一致）；
       ④ 多点命中取 **z 最高**；z 相同时**声明在后者胜**（同序约定与渲染一致）。
     ⇒ **不带 `vis_flag` 的热区**（如 M37 之前的整条把手 `quick.hit_toggle`）**天然不产生气泡**
       ——本判据对它们一律不选（`vis_flag` 非空是 ② 的前置）。M37 形态下 12 个项热区
       恰好是唯一一批带 `vis_flag=quickbar` 的 `hit_*`，故可用气泡 key 集（12 条白字
       `quick.tx_*`）把它们精确筛出；其余元素（圆形 icon / 药丸 / 钉住叠层）都不是 `hit`，
       不参与气泡解析。 */
  function tipKeyAt(def, reveal, x, y) {
    if (!def || !reveal) return '';
    var keys = {};
    (def.elements || []).forEach(function (e) {
      if (!e) return;
      if (e.vis_flag !== undefined && String(e.vis_flag) === String(reveal.tip_flag)
          && e.vis_when && String(e.vis_when) !== '*') keys[String(e.vis_when)] = 1;
    });
    var best = '', bestZ = -Infinity;
    (def.elements || []).forEach(function (e, i) {
      if (!e || e.kind !== 'hit' || !e.id) return;
      if (e.vis_flag === undefined || String(e.vis_flag) === '') return;   // ② 非空 vis_flag
      var m = /\.hit_(.+)$/.exec(String(e.id));
      if (!m || !keys[m[1]]) return;
      if (!elementVisible(e)) return;
      var bx = Number(e.x), by = Number(e.y), bw = Number(e.w), bh = Number(e.h);
      if (!(x >= bx && x < bx + bw && y >= by && y < by + bh)) return;     // ③ 半开区间
      var z = zIndex(e, i);
      if (z >= bestZ) { bestZ = z; best = m[1]; }                          // ④ 同 z 后者胜
    });
    return best;
  }

  function cancelRevealTimer() {
    if (revealRt.timer) { clearTimeout(revealRt.timer); revealRt.timer = null; }
  }

  function startRevealTimer(act) {
    if (revealRt.timer) return;                 // 已在计时：滞回带内不重排（只算一次 delay）
    var ms = Number(act.reveal.delay_ms);
    if (!isFinite(ms) || ms < 0) ms = 0;
    revealRt.timer = setTimeout(function () {
      revealRt.timer = null;
      setFlag(act.reveal.flag, 'collapsed');
      setFlag(act.reveal.tip_flag, '');
      applyFlagVisibility();
    }, ms);
  }

  /* 指针移动（画布坐标）——展开 / 收起计时 / 气泡跟随 */
  function onRevealMove(x, y) {
    var act = activeReveal();
    if (!act) return;
    var R = act.reveal, inX = Number(R.in_x), outX = Number(R.out_x);
    revealRt.lastX = x; revealRt.lastY = y;
    if (x >= inX) {
      cancelRevealTimer();
      setFlag(R.flag, 'expanded');
    } else if (x < outX) {
      if (!isPinned(R)) startRevealTimer(act);
    } else {
      cancelRevealTimer();                      // 滞回带：保持现状、撤销计时
    }
    setFlag(R.tip_flag, getFlag(R.flag) === 'expanded' ? tipKeyAt(act.def, R, x, y) : '');
    applyFlagVisibility();
  }

  /* 指针离开画布：视为 out_x 之外（钉住时不动）。
     注：契约只规定「离开 ⇒ 走收起计时」，未规定气泡；此处**不动气泡**（最小实现）。 */
  function onRevealLeave() {
    var act = activeReveal();
    if (!act) return;
    revealRt.lastX = null; revealRt.lastY = null;
    if (!isPinned(act.reveal)) startRevealTimer(act);
  }

  /* 展开竖条（`open_sysmenu` 的新语义）：撤销收起计时、置 expanded、**不钉住**。
     气泡按最近一次指针位置刷新（指针位置未知时置空）。 */
  function expandQuickbar() {
    var act = activeReveal();
    if (!act) { toast('当前屏没有快捷条（系统菜单已改为右端快捷条）'); return false; }
    cancelRevealTimer();
    setFlag(act.reveal.flag, 'expanded');
    setFlag(act.reveal.tip_flag,
            revealRt.lastX === null ? '' : tipKeyAt(act.def, act.reveal, revealRt.lastX, revealRt.lastY));
    applyFlagVisibility();
    return true;
  }

  /* 钉住开关（`quick_pin`）：钉住 ⇒ 立即展开且不再自动收起；
     解除 ⇒ 若指针此刻已在收起区（x < out_x）则重新起计时（否则保持展开）。
     钉住 flag 名一律读 `reveal.pin_flag`（无该键 ⇒ 本屏无钉住功能，整体空操作）。 */
  function toggleQuickPin() {
    var act = activeReveal();
    if (!act) { toast('当前屏没有快捷条'); return false; }
    var pn = pinFlagOf(act.reveal);
    if (pn === '') { toast('当前屏未声明 reveal.pin_flag（无钉住功能）'); return false; }
    var on = getFlag(pn) === '1';
    setFlag(pn, on ? '' : '1');
    if (!on) {
      cancelRevealTimer();
      setFlag(act.reveal.flag, 'expanded');
    } else if (revealRt.lastX !== null && revealRt.lastX < Number(act.reveal.out_x)) {
      startRevealTimer(act);
    }
    applyFlagVisibility();
    return true;
  }

  /* 承载屏元素里最大的 CSS z-index（含 bg；与 zIndex 同一算法） */
  function maxZIndexOf(def) {
    if (!def) return 0;
    var mx = 0, i;
    for (i = 0; i < (def.elements || []).length; i++) {
      var zi = zIndex(def.elements[i], i);
      if (zi > mx) mx = zi;
    }
    if (def.bg) { var zb = zIndex(def.bg, -1); if (zb > mx) mx = zb; }
    return mx;
  }

  /* 叠画附加层：parent/map 与承载屏相同（DOM 顺序在后）+ z-index 整体上移
     （curZBase = 承载屏最大 z-index + 1）⇒ 「压在上层、点击优先级更高」两条同时成立。 */
  function renderAttachLayer(def, parent, map) {
    var aid = attachIdOf(def);
    if (!aid) return;
    var ad = SCREENS[aid];
    if (!ad) {
      if (window.console && console.warn) console.warn('attach 屏缺数据：' + aid);
      return;
    }
    mergeAttachFlags(aid);
    curZBase = maxZIndexOf(def) + 1;
    try {
      if (ad.bg) renderElement(ad.bg, parent, -1, map);
      renderElements(ad, parent, map);
    } finally {
      curZBase = 0;
    }
    state.attachId = aid;
  }

  /* ==========================================================================
     4.7 ★ M47（ISSUE-20260924-01 · W4）· 设置仓 + `slider`（滑块）运行期
     —— 唯一依据：《M47_设置屏重设方案》§三.1–§三.4（**接口冻结书**）与
        `layout/_schema.md` 的「`slider` 元素字段 / 拖动契约 / 设置仓」三节。
     —— 与 krkr 侧**逐条同口径**，两端任一改动必须同步另一边：
        · `krkr/game/ui_settings.tjs` —— UISettingDef / UISettingStore / UISettingGet /
          UISettingSet / uiSettingAlign / uiSettingResetAll / uiSettingBrief；
        · `krkr/game/ui_widget.tjs`   —— uiWidgetSliderSpan / Clamp / Default / Value /
          XOf / ValueAt / Hot / HandleAsset / DrawSlider；
        · `krkr/game/ui_screens.tjs`  —— uiScreenSliderHitEl / DragTo / Store / InitFor /
          SyncSetting、以及 config_tab_* / config_char_* / config_set_* / config_reset 四个动作。
     —— 命名对应：`state.settings` ↔ `UISettingStore`；`sliderValsRt` ↔ `UIScrSliderVal`；
        `sliderDragId` ↔ `UIScrDragSlider`；`sliderHoverId` ↔ `UIScrHoverSlider`。
     —— 实时生效（方案 §三.3 的**唯一实现路径**）：`dlg_winopac` 同时驱动
        `dlg.mask_bottom`（对话框底部渐变遮罩）与 `cfg.pv_mask`（设置屏预览遮罩）的**元素
        opacity**。krkr 侧由每帧重建的 ctx 读设置仓（`ctx.opacityOverride`，ui_widget.tjs 的
        image 分支早已支持读它）；HTML 侧没有「每帧重建」这回事 ⇒ 用
        applySettingOverrides() 改写**已渲染 DOM** 的 `style.opacity`（**不重建 DOM**，
        时机与做法都仿 applyFlagVisibility）。
        ⚠️ **两个口径别搞混**：映射式是 `alpha = floor(255 × value / 100)`（**0..255**，
           与遮罩素材的 alpha 上限同轴，M39 定下的旋钮）；CSS 的 `opacity` 是 **0..1**
           ⇒ 落盘时**再除以 255**（`style.opacity = floor(255×value/100) / 255`）。
           value=40 ⇒ 引擎 102、HTML `style.opacity = 0.4` —— **是同一个数**，不是两套算法。
     ========================================================================== */
  /* 设置定义表（**与 krkr 侧 `krkr/game/ui_settings.tjs` 的 `UISettingDef` 同名 /
     同 kind / 同值域 / 同默认值**，两侧任一改动必须同步另一边）。
     ★ M47 第三轮追补（一审打回 C2）：**从 9 键补齐到 25 键** —— 9 个数值键（`kind:"int"`）
       + 16 个开关键（`kind:"enum"`：系统页 10 个选项 + 声音页 6 个静音），
       默认值逐条与 `layout/screens/25_config.json` 的 `flags_default` 一致。
     为什么要补：`config_reset` = 恢复**全部**设置（引擎 `uiSettingResetAll()` 就是 25 键）
       ⇒ 只重置 9 个数值键的话，「改全屏 → 切声音页 → 点初始化」在 HTML 侧仍显示全屏
       （值来自切页记忆）、而引擎回到窗口模式 ✗（两端分叉，一审复现）。
       补了 16 键后：`config_set_<键>` 的「同名设置项同步」分支也从「无数据可达」变为**真实生效**
       （值以设置仓为准、flag 从仓里派生），与引擎同一条真相。
     16 键的 `kind:"enum"`：值域写在 `values`，写仓时按值域校验（域外回落 `def`，不抛）。 */
  var SETTING_KEYS = ['dlg_winopac', 'text_speed', 'auto_speed',
                      'vol_master', 'vol_bgm', 'vol_se', 'vol_sysse', 'vol_voice', 'vol_char',
                      'display', 'facewindow', 'drama', 'effect', 'voicecut', 'curhide',
                      'savedialog', 'loaddialog', 'allskip', 'textcolchg',
                      'mute_vol_master', 'mute_vol_bgm', 'mute_vol_se', 'mute_vol_sysse',
                      'mute_vol_voice', 'mute_vol_char'];
  var SETTING_DEF = {
    /* ---- 9 个数值键（kind 缺省 = int）---- */
    dlg_winopac: { min: 0, max: 100, def: 90, step: 5, apply: true,  label: '文本窗口的不透明度' },
    text_speed:  { min: 0, max: 100, def: 60, step: 5, apply: false, label: '文字显示速度' },
    auto_speed:  { min: 0, max: 100, def: 50, step: 5, apply: false, label: '自动播放速度' },
    vol_master:  { min: 0, max: 100, def: 80, step: 5, apply: false, label: '主音量' },
    vol_bgm:     { min: 0, max: 100, def: 80, step: 5, apply: false, label: '背景音乐' },
    vol_se:      { min: 0, max: 100, def: 80, step: 5, apply: false, label: '音效' },
    vol_sysse:   { min: 0, max: 100, def: 80, step: 5, apply: false, label: '系统音效' },
    vol_voice:   { min: 0, max: 100, def: 80, step: 5, apply: false, label: '主音量（语音）' },
    vol_char:    { min: 0, max: 100, def: 80, step: 5, apply: false, label: '角色音量' },
    /* ⚠️ 音量类与 text_speed / auto_speed 是「只存值」：**本作引擎无任何音频代码**
       （无 SoundBuffer / 无 volume 调用），打字机节拍也还是固定 ms；`display`（画面模式）
       同理无 `setFullScreen` 调用 ⇒ 一律不得声称已生效（方案 §三.3 与 §六 风险 2 的如实登记）。 */
    /* ---- 系统页 10 个开关键（kind: enum；def 与 flags_default 逐条一致）---- */
    display:     { kind: 'enum', values: ['window', 'full'], def: 'window', apply: false, label: '画面模式' },
    facewindow:  { kind: 'enum', values: ['on', 'off'], def: 'on',  apply: false, label: '立绘窗口' },
    drama:       { kind: 'enum', values: ['on', 'off'], def: 'on',  apply: false, label: '演出效果' },
    effect:      { kind: 'enum', values: ['on', 'off'], def: 'on',  apply: false, label: '特效' },
    voicecut:    { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '语音截断' },
    curhide:     { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '隐藏光标' },
    savedialog:  { kind: 'enum', values: ['on', 'off'], def: 'on',  apply: false, label: '存档时的确认信息' },
    loaddialog:  { kind: 'enum', values: ['on', 'off'], def: 'on',  apply: false, label: '读档时的确认信息' },
    allskip:     { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '全部跳过' },
    textcolchg:  { kind: 'enum', values: ['on', 'off'], def: 'on',  apply: false, label: '文字变色' },
    /* ---- 声音页 6 个静音键（def 全 off；动作语义 = **toggle**，见 doConfigAction）---- */
    mute_vol_master: { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '主音量·静音' },
    mute_vol_bgm:    { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '背景音乐·静音' },
    mute_vol_se:     { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '音效·静音' },
    mute_vol_sysse:  { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '系统音效·静音' },
    mute_vol_voice:  { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '主音量（语音）·静音' },
    mute_vol_char:   { kind: 'enum', values: ['on', 'off'], def: 'off', apply: false, label: '角色音量·静音' }
  };

  function settingDef(key) {
    if (key === null || key === undefined) return null;
    var d = SETTING_DEF[String(key)];
    return d ? d : null;
  }
  function settingHas(key) { return settingDef(key) !== null; }
  /* 该键的类型（'int' | 'enum'；未声明 = 'int'，与 uiSettingKind 同） */
  function settingKind(key) {
    var d = settingDef(key);
    return (d && d.kind === 'enum') ? 'enum' : 'int';
  }
  /* 仓里**是否有**该键的值（用来区分「真存过」与「回落 def」——三级优先链的第①级要求真存过，
     与 uiSettingStored 同；否则未存过的键会遮住第②级的切页记忆） */
  function settingStored(key) {
    var d = settingDef(key);
    if (!d) return false;
    var v = state.settings[String(key)];
    if (v === null || v === undefined) return false;
    return String(v) !== '';
  }

  /* 取值：未设置过 → 定义表的 def（与 UISettingGet 同）。
     enum 键返回**字符串**（值域校验在写仓时做，与 UISettingGet 同：Get 不做校验）。 */
  function settingGet(key) {
    var d = settingDef(key);
    if (!d) return 0;
    var v = state.settings[String(key)];
    if (v === null || v === undefined || String(v) === '') return d.def;
    if (settingKind(key) === 'enum') return String(v);
    var n = Number(v);
    return isFinite(n) ? n : Number(d.def);
  }

  /* enum 值域校验（返回**字符串**值；域外/脏值 ⇒ 回落 def，不抛。与 uiSettingEnumAlign 同） */
  function settingEnumAlign(d, value) {
    var v = (value === null || value === undefined) ? '' : String(value);
    var vals = d.values || [];
    if (vals.indexOf(v) >= 0) return v;
    return String(d.def);
  }

  /* 值标准化：enum ⇒ 值域校验；int ⇒ 取整 → step 对齐 → clamp（与 uiSettingAlign 同序） */
  function settingAlign(key, value) {
    var d = settingDef(key);
    if (!d) return 0;
    if (settingKind(key) === 'enum') return settingEnumAlign(d, value);
    var n = Number(value);
    if (!isFinite(n)) n = 0;
    n = Math.round(n);
    var step = Number(d.step);
    if (step > 0) n = Math.round(n / step) * step;
    if (n < Number(d.min)) n = Number(d.min);
    if (n > Number(d.max)) n = Number(d.max);
    return n;
  }

  /* 写仓：clamp + step 对齐 → 同步滑块运行值（手柄位置跟着走）→ 实时生效
     返回 true = 值确实变了（调用方据此决定是否重画）。与 UISettingSet 同。 */
  function settingSet(key, value) {
    var k = String(key), d = settingDef(k);
    if (!d) return false;
    var nv = settingAlign(k, value), old = settingGet(k);
    state.settings[k] = nv;
    sliderSyncSetting(k, nv);
    applySettingOverrides();     // 每次设置值变化之后各跑一次（方案 §三.3）
    return old !== nv;
  }

  /* 全部恢复定义表的 def（设置屏「初始化」= 动作 config_reset 的目标，与 uiSettingResetAll 同）。
     ★ 25 键全恢复（9 数值 + 16 enum）：`def` 本身已是正确类型（number / string），
     故**不要**强转 Number —— 强转会把 enum 键的 'window'/'on' 变成 NaN。 */
  function settingResetAll() {
    var n = 0;
    SETTING_KEYS.forEach(function (k) {
      var d = SETTING_DEF[k];
      if (!d) return;
      state.settings[k] = d.def;
      sliderSyncSetting(k, d.def);
      n++;
    });
    applySettingOverrides();
    return n;
  }

  /* 可读摘要（对应 uiSettingBrief；用于动作反馈消息） */
  function settingBrief() {
    return SETTING_KEYS.map(function (k) { return k + '=' + settingGet(k); }).join(' ');
  }

  /* 设置值 → 遮罩 **0..255** 口径的 alpha（**唯一的映射式**：floor(255×value/100)）。
     ÷255 那一步只在写 CSS 时做（见 applySettingOverrides），不要写进这里。 */
  function settingMaskAlpha(value) {
    var v = Number(value);
    if (!isFinite(v)) v = 0;
    return Math.floor(255 * v / 100);
  }

  /* ★ 实时生效：把 dlg_winopac 灌进两个遮罩节点的 `style.opacity`（**不重建 DOM**）。
     两个落点与引擎逐字一致（ui_screens.tjs / ui_dialog.tjs 的 `ctx.opacityOverride`）：
       · `dlg.mask_bottom` —— 对话框底部渐变遮罩（10_dialog，与 dlg.face 同批的对话框件）
       · `cfg.pv_mask`     —— 设置屏预览遮罩（25_config；与对话框同一素材算法口径）
     节点当前不在屏上时 refOf() 返回 null ⇒ 跳过；换到该屏时 renderScreen 会再跑一次。 */
  function applySettingOverrides() {
    /* CSS 的 opacity 是 0..1，引擎口径是 0..255 ⇒ 这里除 255（见上方长注释的「两个口径」） */
    var css = String(settingMaskAlpha(settingGet('dlg_winopac')) / 255);
    ['dlg.mask_bottom', 'cfg.pv_mask'].forEach(function (id) {
      var r = refOf(id);
      if (r && r.el) r.el.style.opacity = css;
    });
  }

  /* ---- 滑块运行期（与 ui_widget.tjs 的 uiWidgetSlider* 逐条同口径） ---- */
  /* 手柄素材天然尺寸 —— `ui/x_ui_cfg_knob.png` 实为 29×29（方案 §三.1 / §1.3；
     与引擎 uiWidgetBlitAsset 按素材自身尺寸绘制同口径）。手柄**不随元素框裁剪**
     （元素 h=24 < 29 ⇒ 上下各溢出 2–3px，见 buildSlider 的 overflow:visible）。 */
  var SLIDER_KNOB = 29;
  var sliderValsRt = {};       // 滑块 id → 运行值（**不随换屏重置**，与 UIScrSliderVal 同）
  var sliderDragId = '';       // 正在拖动的滑块 id（"" = 未拖动；与 UIScrDragSlider 同）
  var sliderHoverId = '';      // 指针悬停的滑块 id（"" = 无；与 UIScrHoverSlider 同）

  /* `x..x+w` → `min..max` 的跨度；max < min 时退化（避免除零，与 uiWidgetSliderSpan 同） */
  function sliderSpan(e) {
    var a = Number(e.min); if (!isFinite(a)) a = 0;
    var b = Number(e.max); if (!isFinite(b)) b = 0;
    if (b < a) b = a;
    var s = Number(e.step); if (!isFinite(s)) s = 0;
    return { min: a, max: b, step: s };
  }
  /* 值标准化：取整 → step 对齐 → clamp（与 uiWidgetSliderClamp 同） */
  function sliderClamp(e, v) {
    var sp = sliderSpan(e);
    var n = Number(v); if (!isFinite(n)) n = 0;
    n = Math.round(n);
    if (sp.step > 0) n = Math.round(n / sp.step) * sp.step;
    if (n < sp.min) n = sp.min;
    if (n > sp.max) n = sp.max;
    return n;
  }
  /* 元素的设置键名（空串 = 纯视觉滑块，不写仓） */
  function settingOf(e) {
    return (e && e.setting !== null && e.setting !== undefined) ? String(e.setting) : '';
  }
  /* 初值：有 `setting` 且设置仓认这个键 ⇒ 用**仓里的值**（复位/读档后的值必须一进来就体现）；
     否则用元素自己的 `value`。与 uiWidgetSliderDefault 同。 */
  function sliderDefault(e) {
    var st = settingOf(e);
    if (st !== '' && settingHas(st)) return settingGet(st);
    var v = Number(e.value);
    return isFinite(v) ? v : 0;
  }
  /* 运行值：只在「该 id 尚无值」时用初值初始化；此后用户拖出来的值一直有效
     （方案「换屏返回保留运行期值」⇒ 与 UIScrSliderVal 同口径）。 */
  function sliderValue(e) {
    var id = String(e.id || '');
    var v = sliderValsRt[id];
    if (v === null || v === undefined) { v = sliderClamp(e, sliderDefault(e)); sliderValsRt[id] = v; }
    return sliderClamp(e, v);
  }
  /* 值 → 手柄中心 x（`min` 落在轨道左端、`max` 落在右端；与 uiWidgetSliderXOf 同：**四舍五入**） */
  function sliderXOf(e, v) {
    var sp = sliderSpan(e);
    if (sp.max <= sp.min) return Number(e.x);
    var t = (sliderClamp(e, v) - sp.min) / (sp.max - sp.min);
    return Number(e.x) + Math.round(t * Number(e.w));
  }
  /* 轨道 x → 值（clamp + step 对齐）。**拖动与键盘/探针共用这一条换算**（单一真相源）；
     指针拖到轨道外 ⇒ 夹到两端、**不取消拖动**（与 uiWidgetSliderValueAt 同）。 */
  function sliderValueAt(e, x) {
    var sp = sliderSpan(e);
    if (!(Number(e.w) > 0) || sp.max <= sp.min) return sp.min;
    var t = (Number(x) - Number(e.x)) / Number(e.w);
    if (t < 0) t = 0;
    if (t > 1) t = 1;
    return sliderClamp(e, sp.min + t * (sp.max - sp.min));
  }
  /* 该滑块此刻是否「活动」（拖动中 或 指针悬停其命中热区）⇒ 手柄用 hover 图。
     与 uiWidgetSliderHot 同（引擎读 ctx.dragSlider / ctx.hoverSlider，这边读两个运行期 id）。 */
  function sliderHot(id) {
    var k = (id === null || id === undefined) ? '' : String(id);
    if (k === '') return false;
    return (sliderDragId === k) || (sliderHoverId === k);
  }
  /* 手柄素材：活动态 → `state_assets.hover`；否则 `state_assets.normal`；缺键回落 `handle.asset`
     （回落口径与 uiWidgetSliderHandleAsset 同）。 */
  function sliderHandleAsset(e, hot) {
    var h = (e && e.handle) ? e.handle : {};
    var sa = h.state_assets || {};
    if (hot && sa.hover) return String(sa.hover);
    if (sa.normal) return String(sa.normal);
    return h.asset ? String(h.asset) : '';
  }
  /* 设置仓 → 滑块运行值（对应 uiScreenSliderSyncSetting：**遍历全部屏**的 slider 元素）。
     值一变（拖动 / config_reset / 将来的读档）⇒ 所有 `setting` 指向该键的滑块运行值改成新值
     ⇒ 手柄位置跟着走（否则「初始化」后手柄会停在上一次拖动的位置）。 */
  function sliderSyncSetting(key, value) {
    var k = String(key), n = 0;
    Object.keys(SCREENS).forEach(function (sid) {
      var sc = SCREENS[sid];
      if (!sc || !sc.elements) return;
      sc.elements.forEach(function (el) {
        if (!el || el.kind !== 'slider') return;
        if (settingOf(el) !== k) return;
        sliderValsRt[String(el.id || '')] = value;
        n++;
      });
    });
    return n;
  }
  /* 把一个**已存在的**滑块节点按当前值重画（手柄位置 + data-ui-slider-value + 手柄图）。
     ⚠️ 只改节点样式，**不重建 DOM**（同 applyFlagVisibility / applySettingOverrides 的做法）。
     位置式与引擎一致：引擎 `uiWidgetBlitAsset(素材, xOf - floor(w/2), y + floor((h-hh)/2))`
     是在**舞台（画布）绝对坐标**上画；HTML 的 knob 是**相对 wrap** 定位的
     ⇒ 必须把 wrap 的原点减掉（`wrap.__box.x/y` = buildSlider 时 resolveBox 的实值，
        content_box 元素上 e.x 与实框不同，故不能直接用 e.x）。
     ★ 这个减法是**实测抓到的真 bug**：首版漏减 ⇒ 手柄比轨道右端多偏一个元素 x（winopac 偏了
       307px，手柄跑到 x=928 而轨道只到 671）；⑲a 因此改成**量渲染后的真实矩形**（见自检）。 */
  function sliderPaint(wrap, e) {
    if (!wrap || !e || !wrap.__knob) return false;
    var knob = wrap.__knob;
    var ox = (wrap.__box && wrap.__box.x !== null && wrap.__box.x !== undefined)
      ? Number(wrap.__box.x) : Number(e.x);
    var v = sliderValue(e);
    var hh = Number(e.h);
    if (!isFinite(hh)) hh = SLIDER_KNOB;
    knob.style.left = px(sliderXOf(e, v) - Math.floor(SLIDER_KNOB / 2) - ox);
    knob.style.top = px(Math.floor((hh - SLIDER_KNOB) / 2));
    var ha = sliderHandleAsset(e, sliderHot(e.id));
    knob.style.backgroundImage = ha ? 'url("' + assetUrl(ha) + '")' : 'none';
    wrap.setAttribute('data-ui-slider-value', String(v));
    return true;
  }
  /* 按 id 重画（节点不在屏上时静默跳过 —— 换到该屏时 buildSlider 会按运行值重画） */
  function sliderSyncDom(id) {
    var r = refOf(String(id));
    if (!r || !r.el) return false;
    return sliderPaint(r.el, r.def);
  }
  /* 当前在屏上的**全部**滑块各同步一次（复位 / 设置变化 / 连动后调用） */
  function sliderSyncAllDom() {
    [state.refs, state.baseRefs].forEach(function (map) {
      if (!map) return;
      Object.keys(map).forEach(function (id) {
        var r = map[id];
        if (r && r.def && r.def.kind === 'slider') sliderPaint(r.el, r.def);
      });
    });
  }
  /* 结束拖动（抬起 / 指针取消 / 换屏）。与 uiScreenPressClear 逐条同：**两个 id 一起清** ——
     指针若仍停在热区上，下一次移动会重新置上悬停（引擎同口径）。返回 true = 原本确实在拖动。 */
  function sliderDragEnd() {
    var was = sliderDragId, hadHover = sliderHoverId;
    if (was === '' && hadHover === '') return false;
    sliderDragId = ''; sliderHoverId = '';
    if (was !== '') sliderSyncDom(was);
    else if (hadHover !== '') sliderSyncDom(hadHover);
    return was !== '';
  }
  /* 写值：① 更新运行值仓；② 有 `setting` ⇒ 写设置仓（**实时生效路径**），并从仓里读回
     （仓会做自己的 clamp + step 对齐）⇒ 仓值与滑块值**不分叉**（与 uiScreenSliderStore 同）。 */
  function sliderStore(e, nv) {
    var id = String(e.id || '');
    var st = settingOf(e);
    if (st !== '') { settingSet(st, nv); nv = settingGet(st); }
    sliderValsRt[id] = nv;
    return true;
  }
  /* 拖动到画布 x —— 拖动期间**唯一**的值更新入口：越界 clamp，**绝不因移出热区/轨道而中断**
     （⚠️ 与 M35 规则③「指针移出即取消按下态」**语义不同**：那是「按下态不跟指针飘」，
       而拖动要求「按住不放、指针可以离开命中矩形甚至轨道两端而拖动继续」。两个出口：
       左键抬起、换屏 —— 与 uiScreenHoverUpdate 的长注释逐条对应）。 */
  function sliderDragTo(x) {
    var id = sliderDragId;
    if (id === '') return false;
    var r = refOf(id);
    if (!r || !r.def || r.def.kind !== 'slider') {
      /* 目标消失（换屏竞态 / 数据被换掉）⇒ 结束拖动，不让它悬挂（与 uiScreenSliderDragTo 同） */
      sliderDragId = ''; sliderHoverId = '';
      return true;
    }
    sliderStore(r.def, sliderValueAt(r.def, x));
    sliderSyncDom(id);
    return true;
  }
  /* 键盘 ±step：与拖动**同一条取值路径**（clamp + step 对齐 + 写仓 + 重画）。
     step 缺省（<=0）时按 1 走（与 uiWidgetSliderClamp 的「step<=0 不对齐」不冲突：
     那只影响对齐，键盘仍要有一个步长）。 */
  function sliderKeyStep(id, dir) {
    var r = refOf(String(id));
    if (!r || !r.def) return false;
    var sp = sliderSpan(r.def);
    var step = (sp.step > 0) ? sp.step : 1;
    sliderStore(r.def, sliderValue(r.def) + Number(dir) * step);
    sliderSyncDom(String(id));
    return true;
  }
  /* 拖动期间的指针兜底：把 pointermove / pointerup 也挂到 document 上（**捕获阶段**）。
     为什么要它：`setPointerCapture` 在**合成事件 / 无头环境**下可能抛（指针未真正活跃），
     此时若不兜底，指针一移出热区就丢事件 ⇒ 拖动中断（与引擎语义不符）。
     幂等：一次拖动只挂一次，抬起/取消即摘（dragDocUnbind）。 */
  var dragDocBound = false, dragDocMove = null, dragDocUp = null;
  function bindDragDoc() {
    if (dragDocBound) return;
    dragDocBound = true;
    dragDocMove = function (ev) {
      if (sliderDragId === '') return;
      if (ev && ev.button !== undefined && ev.button !== 0 && ev.buttons === 0) return;
      sliderDragTo(canvasPoint(ev).x);
    };
    dragDocUp = function (ev) {
      if (ev && ev.button !== undefined && ev.button !== 0) return;   // 右键抬起不结束拖动
      dragDocUnbind();
      sliderDragEnd();
    };
    document.addEventListener('pointermove', dragDocMove, true);
    document.addEventListener('pointerup', dragDocUp, true);
    document.addEventListener('pointercancel', dragDocUp, true);
  }
  function dragDocUnbind() {
    if (!dragDocBound) return;
    dragDocBound = false;
    document.removeEventListener('pointermove', dragDocMove, true);
    document.removeEventListener('pointerup', dragDocUp, true);
    document.removeEventListener('pointercancel', dragDocUp, true);
    dragDocMove = null; dragDocUp = null;
  }

  /* ==========================================================================
     5. 渲染器
     ========================================================================== */
  /* 屏内元素：稳定排序（先 z，缺省按声明序；同 z 按声明序）后逐个渲染到 parent。
     map = 元素 id → {el, def} 的目标表（顶层屏用 state.refs，浮层下层用 state.baseRefs）。 */
  /* ==========================================================================
     4.9 ★ E3（ISSUE-20260927-05）· 连线渲染（`links`，**顶层键、不走 elements 管道**）
     —— 唯一依据：《_工作\ISSUE-20260927-05_流程图实现\边与节点数据契约.md》§三（v1.1）。
     —— **同判据的另一端** = krkr 侧 `krkr/game/ui_flow_links.tjs`（E2 产出，layerExDraw 封装）；
        改一处必须改另一处。几何来自**同一份** `layout/screens/32_flowchart.json`
        （经 `工具\gen_layout.py` 透传进 `ui_layout.js` / `ui_layout.tjs`）——本层**不另起一份**，
        也不自行做路由（点集由生成器算好，两端只描线画箭头 ⇒ 路由不可能两端分叉）。
     —— 口径（**逐字照契约 §三**，不得自由发挥）：
        · 描线：按 `pts` 顺序连线；`lineJoin:"round"` + `lineCap:"round"`（**不做半径圆弧**，
          契约明确「圆角就是笔的圆角连接」）；线宽 = `w`；颜色 = `color`（`0xAARRGGBB` 整数）。
        · 箭头：`arrow:true` ⇒ 在 `pts[-1]` 画**实心三角多边形**（**不得用** SVG marker /
          `AdjustableArrowCap` / 任何自动箭头机制）：顶点 = `pts[-1]`；沿末段方向后退
          `L = 2.0×w` 为底边中点；底边半宽 `= 1.5×w`。`2.0` / `1.5` 是**契约冻结的算法口径**
          （不是坐标/尺寸常量，禁止改写）。
        · 画在哪一层：见 `linksAnchorZ()` —— **从数据导出，不写死**。
     —— 用 `<canvas>` 而非 DOM 拼 rect：契约要求两端「逐像素可比」，canvas 的
        lineJoin/lineCap 与 krkr 侧 GDI+/layerExDraw 的线端帽同为「笔的圆角」语义
        （两端统一画显式三角多边形，是本轮**唯一有意偏离参照作**之处，契约 §三 已登记）。
     ========================================================================== */

  /* 取该屏的 links（**同一份 ui_layout.js 数据**；空 / 缺键 ⇒ 空数组，零副作用）。
     现有全部屏（除流程图外）都没有这个键 ⇒ 本模块对它们**一个像素都不画**。 */
  function linksOf(def) {
    if (!def) return [];
    return (def.links && def.links.length) ? def.links : [];
  }

  /* `0xAARRGGBB` 整数 → canvas 色串。
     `>>>`（无符号）保证 A 通道 ≥ 0x80（整数 > 2^31）不被符号位污染。
     契约给的是**整数**；另容忍 8 位十六进制串（`0x…` / 裸 8 位）——其余一律判非法
     （宁可显式拒绝并打判词，也不猜一个颜色）。 */
  function linkColorStr(c) {
    var n = null;
    if (typeof c === 'number' && isFinite(c)) n = Math.floor(c);
    else if (typeof c === 'string' && /^((0x)|#)?[0-9A-Fa-f]{8}$/.test(c)) n = parseInt(c.replace(/^(0x|#)/, ''), 16);
    if (n === null || n < 0 || n > 4294967295) return null;
    return 'rgba(' + ((n >>> 16) & 255) + ',' + ((n >>> 8) & 255) + ',' + (n & 255)
      + ',' + (((n >>> 24) & 255) / 255) + ')';
  }

  /* 逐条校验（**绘制与自检共用同一判据**，且**与 krkr 侧 `uiFlowLinkDrawOne` 同一放行集**
     —— 两端对「哪条能画」必须给出同一个答案，否则同一条脏数据会一端画一端不画）。
     放行集（逐条对齐 E2 的 `uiFlowLinkDrawOne`）：
       · 对象、`pts` 为数组且 ≥2 点、每点是 [x,y] 有限数；
       · `w` 是有限数且**四舍五入后** > 0（E2: `w = Math.round(w); if(w <= 0) return false`）；
       · `color` 能解析成色值。
     **不在放行集内**的一项：末段长度为 0 —— 它**不影响折线**，只在 `arrow:true` 时让箭头
     画不出方向；E2 的口径是「折线照画、放弃箭头」，本层同口径（见 drawLinks 的箭头分支）。 */
  function linkProblems(l) {
    var bad = [];
    if (!l || typeof l !== 'object') return ['非对象'];
    var pts = l.pts;
    if (!pts || !pts.length || pts.length < 2) {
      bad.push('pts 少于 2 点');
    } else {
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        if (!p || p.length !== 2 || !isFinite(Number(p[0])) || !isFinite(Number(p[1])))
          bad.push('pts[' + i + '] 非 [x,y] 有限数');
      }
    }
    var w = Number(l.w);
    if (!isFinite(w) || Math.round(w) <= 0) bad.push('w 非正数（四舍五入后；E2 同判据）');
    if (!linkColorStr(l.color)) bad.push('color 非 0xAARRGGBB 整数（契约闸门⑥：取值须能在 palette.json 找到）');
    return bad;
  }

  /* 连线层的 **z 阈值**（**契约 §三.1 的唯一口径 —— 与 krkr 侧
     `krkr/game/ui_flow_links.tjs::uiFlowLinkLayerZ` 逐字同口径**）。
     它是**普通 z 刻度**上的一条分界线：
       元素 `z < 阈值` ⇒ 画在连线**之下**；`z ≥ 阈值` ⇒ 画在连线**之上**。
       ① **有节点族**（id 以 `fc.node.` 开头，契约 §二）⇒ 取节点族**最小普通 z** − 1；
       ② **无节点族**（旧样板数据）⇒ 取「`kind=="rect"` 且面积 ≥ 画布 30%」的**最大普通 z** + 1；
       ③ 两者皆无 ⇒ 0。
     返回 `null` ⟺ 本屏没有可画的 links（调用方据此**完全不建**连线层）。
     ★ 为什么比的是**普通 z**而不是渲染 raw z（`z*100+声明序`）：契约 §三.1 明写该口径，且
       「两端都在读同一份数据、比较同一个量」才可逐条对账；raw z 是本层**内部实现细节**，
       把它当契约口径等于让另一端来模仿本实现（一审 Major：两端曾各写一套，后果是 28 件
       既有 UI 件在 krkr 画在连线之上、在 HTML 画在连线之下）。 */
  function linksLayerZ(def, links) {
    if (!links || !links.length) return null;
    var els = (def && def.elements) || [];
    if (!els.length) return null;
    var nodeMin = null, backMax = null;
    for (var i = 0; i < els.length; i++) {
      var e = els[i];
      if (!e) continue;
      var z = plainZOf(e, i);
      if (z === null) continue;
      if (String(e.id || '').indexOf('fc.node.') === 0) {           // ① 节点族（契约 §二 的 id）
        if (nodeMin === null || z < nodeMin) nodeMin = z;
      } else if (isBackdropRect(e)) {                               // ② 压暗层 / 视口底板
        if (backMax === null || z > backMax) backMax = z;
      }
    }
    if (nodeMin !== null) return nodeMin - 1;
    if (backMax !== null) return backMax + 1;
    return 0;
  }

  /* 元素的**普通 z**：数据里就有的字段；未写 z 时按声明序（与 `zIndex()` 同一回落，
     生成器会给每个元素补 z，故该回落只为鲁棒）。 */
  function plainZOf(e, orderIdx) {
    if (!e) return null;
    var z = e.z;
    if (z === null || z === undefined || isNaN(Number(z))) return (orderIdx === undefined) ? null : orderIdx;
    return Number(z);
  }

  /* 「压暗层 / 视口底板」判据 —— 与 krkr `uiFlowLinkIsBackdropRect` **逐字同口径**：
     `kind=="rect"` 且 `w*h*100 >= canvasW*canvasH*30`（占画布 ≥30%）。 */
  function isBackdropRect(e) {
    if (!e || e.kind !== 'rect') return false;
    var w = Number(e.w), h = Number(e.h);
    if (!(w > 0) || !(h > 0)) return false;
    var area = Number(CANVAS.width) * Number(CANVAS.height);
    if (!(area > 0)) return false;
    return (w * h * 100 >= area * 30);
  }

  /* 把上面的**普通 z 阈值**折算成本层实际写入 canvas 的 **CSS z-index**。
     元素各自的 CSS z-index 仍是既有公式 `zIndex(e,i) = z*100 + 声明序`（本层内部实现，不改）；
     连线只需落在「阈值之上那一群」里**最小 raw z-index 的下一位**：
       raw = min{ zIndex(e,i) : 普通 z(e) ≥ 阈值 } − 1
     ⇒ 逐元素关系「z < 阈值 ⇒ 在连线之下；z ≥ 阈值 ⇒ 在连线之上」**恒成立**：
       该群最小 raw 必然 ≤ 群内任一件（故连线在其全部之下），而阈值之下那批的 raw 也必然
       小于它（z 档间距 100 远大于元素数从 0 起的声明序，本屏实测差值 ≥800）。
     阈值之上**一件都没有**时（② 兜底分支可能如此）⇒ 画在全部元素之上（max raw + 1）。
     ⚠ 本函数**只做刻度折算**，判据（谁在阈值之上）仍由 `linksLayerZ()` 的普通 z 决定。 */
  function linksLayerZIndex(def, links) {
    var lz = linksLayerZ(def, links);
    if (lz === null) return null;
    var els = (def && def.elements) || [];
    var aboveMin = null, allMax = null;
    for (var i = 0; i < els.length; i++) {
      var e = els[i];
      if (!e) continue;
      var r = zIndex(e, i);
      if (allMax === null || r > allMax) allMax = r;
      var z = plainZOf(e, i);
      if (z === null || z < lz) continue;
      if (aboveMin === null || r < aboveMin) aboveMin = r;
    }
    if (aboveMin !== null) return aboveMin - 1;
    return (allMax === null) ? 0 : allMax + 1;
  }

  /* 判词出口（与 M06/M08 同款：去重后进 console.warn + state.links.rejects 台账）。 */
  function linksReject(id, reason) {
    var line = '★E3LINKS-REJECT★ ' + id + ' ' + reason;
    if (state.links.rejects.indexOf(line) < 0) state.links.rejects.push(line);
    try { console.warn('[UI][REJECT] ' + line); } catch (e) { }
    return line;
  }

  /* 画该屏的全部连线。**父容器与 z-index 与既有元素同一条 z 公式**（不另立一套层序）。
     `pointer-events:none`：连线是纯装饰层，不参与命中（krkr 侧同 —— 它不注册任何热区）。
     台账 `state.links.drawn` 每条记录实际画出的图元 ⇒ 自检 ㉒ 据此与数据对账。 */
  function drawLinks(def, parent, map) {
    /* ★ 第 2 步：重画前先撤掉本 parent 里**上一次**画的连线层（`flow_layer` 切层 / 重画同一屏
       都会再进来一次；不撤会叠出第二张 canvas ⇒ 台账与实际图元数分叉）。本函数因此**幂等**。
       台账 `state.links.drawn` 同步清空 —— 它的语义是「**现在**这块 canvas 上有哪几条」，
       而不是「本屏历次画过的累计」（切层后 `blocked` 分支不画任何东西，累计会让它谎报条数）。 */
    clearCanvasIn(parent, 'ui-linklayer');
    state.links.drawn = [];
    /* ★ 第 2 步 · 冻结 §四.1 硬判据：`fc_layer != main` ⇒ **不画任何连线**。
       判据从**数据**推（层 flag 名 = 声明 `action:"flow_layer"` 的热区所带的 `vis_flag`；
       「主干」值 = 该屏 `flags_default` 里这个 flag 的初值）——机制里不写死 `fc_layer` / `main`。 */
    var lflag = flowLayerFlagName(def);
    var lmain = flowLayerMainValue(def, lflag);
    state.links.layer = lflag ? (lflag + '=' + getFlag(lflag)) : '';
    state.links.blocked = (lflag !== '' && lmain !== '' && getFlag(lflag) !== lmain);
    if (state.links.blocked) return;
    var links = linksOf(def);
    if (!links.length) return;
    var layerZ = linksLayerZIndex(def, links) + curZBase;
    var cv = mk('canvas', 'ui-el ui-linklayer');
    cv.width = CANVAS.width;
    cv.height = CANVAS.height;
    cv.style.left = '0';
    cv.style.top = '0';
    cv.style.width = px(CANVAS.width);
    cv.style.height = px(CANVAS.height);
    cv.style.zIndex = layerZ;
    cv.style.pointerEvents = 'none';
    cv.setAttribute('data-ui-kind', 'links');
    cv.setAttribute('data-ui-links-z', String(layerZ));
    var ctx = cv.getContext ? cv.getContext('2d') : null;
    if (!ctx) { linksReject('(全部)', 'canvas 2d 上下文不可用'); return; }
    for (var i = 0; i < links.length; i++) {
      var l = links[i];
      var id = String((l && l.id) || ('(#' + i + ')'));
      var bad = linkProblems(l);
      if (bad.length) { linksReject(id, bad.join('；')); continue; }
      var pts = l.pts, w = Math.round(Number(l.w)), cstr = linkColorStr(l.color);
      /* ① 折线：圆角连接 + 圆端帽（笔的属性，不做半径圆弧） */
      ctx.lineWidth = w;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.strokeStyle = cstr;
      ctx.fillStyle = cstr;
      ctx.beginPath();
      ctx.moveTo(Number(pts[0][0]), Number(pts[0][1]));
      for (var k = 1; k < pts.length; k++) ctx.lineTo(Number(pts[k][0]), Number(pts[k][1]));
      ctx.stroke();
      /* ② 箭头：显式实心三角（顶点 = 末点，底边中点沿末段后退 2.0×w，底边半宽 1.5×w） */
      var poly = null;
      if (l.arrow) {
        var n = pts.length, tip = pts[n - 1], prev = pts[n - 2];
        var dx = Number(tip[0]) - Number(prev[0]), dy = Number(tip[1]) - Number(prev[1]);
        var len = Math.sqrt(dx * dx + dy * dy);
        if (len <= 0) {
          /* 零长末段：方向未定义 ⇒ **折线照画、放弃箭头**（与 krkr 侧
             `uiFlowLinkArrowPts` 的 `if(len <= 0) return null;` **逐字同口径**），并打判词，
             不静默。全条不画是另一端的旧口径，已按 E2 实现统一。 */
          linksReject(id, '末段长度为 0：放弃箭头（折线照画）');
        } else {
          var ux = dx / len, uy = dy / len;
          var L = 2.0 * w, HW = 1.5 * w;                   // 契约冻结系数（见上方模块注）
          var bx = Number(tip[0]) - ux * L, by = Number(tip[1]) - uy * L;   // 底边中点
          var nx = -uy, ny = ux;                                          // 底边方向的单位向量
          ctx.beginPath();
          ctx.moveTo(Number(tip[0]), Number(tip[1]));
          ctx.lineTo(bx + nx * HW, by + ny * HW);
          ctx.lineTo(bx - nx * HW, by - ny * HW);
          ctx.closePath();
          ctx.fill();
          poly = { tip: [Number(tip[0]), Number(tip[1])], base: [bx, by], half: HW, back: L };
        }
      }
      var rec = { id: id, kind: String(l.kind || ''), w: w, arrow: !!l.arrow, layerZ: layerZ,
                  pts: [], polyline: true, polygon: poly };
      for (var q = 0; q < pts.length; q++) rec.pts.push([Number(pts[q][0]), Number(pts[q][1])]);
      state.links.drawn.push(rec);
    }
    parent.appendChild(cv);
  }

  /* ==========================================================================
     ★ 第 2 步（ISSUE-20260928-02）· 流程图「主干 / 番外独立层」切换（`flow_layer`）
       与 `current` 高亮环（**程序化绘制，不产元素**）
     —— 唯一依据：《_工作\ISSUE-20260928-02_第2步\接口冻结.md》§二 / §四；
        `layout\_schema.md` §四「屏级状态 flag」的「第 2 步：流程图屏的 `fc_layer`」小节
        与 §六 动作名表的 `flow_layer` 行。
     —— **同判据的另一端** = krkr 侧 `krkr/game/ui_flow_links.tjs`（E2 产出）；改一处必须改另一处。
     —— 机制**不写死任何层名 / flag 名 / 坐标 / 色值**（`layout\_schema.md` §四 铁律）：
        · 层 flag 名   ← 该屏**声明 `action:"flow_layer"` 的热区**所带的 `vis_flag`（数据唯一出处）；
        · 「主干」取值 ← 该屏 `flags_default` 里这个 flag 的**初值**（数据唯一出处）；
        · 合法层取值集 ← 该 flag 出现在元素 `vis_when` 上的**全部取值** ∪ {主干初值}（数据导出）；
        · 环的色       ← `palette.json` 的 `node_current`（**键名**是接口冻结项，**色值不直写**）；
        · 环的矩形     ← 数据里 `flow_state == "current"` 的**节点元素矩形内缩 1px**。
     —— `flow_state` 语义（§四 元素通用字段表）：**缺省 = "available"**；只有 `"current"`
        由两端程序化画环（`locked` / `new` 的叠加件是**独立元素**，走 `vis_flag` 机制，本模块不管）。
        `flow_state`（落在**节点元素**上）与 `fc_Layer`（落在**全部主干元素**上）是**两组不同的旗标**，
        「一个元素只允许一对 `vis_flag`」铁律照旧。
     ========================================================================== */

  /* `current` 高亮环的**接口冻结常量**（冻结书 §一.1 / `layout\_schema.md` §四：
     圆角半径 16、线宽 3、矩形＝节点元素矩形内缩 1px、色＝`@palette.node_current`）。
     导出给自检 / 探针读；自检 ㉔c 另以 **canvas 像素**作独立锚点实测半径，不只比常量。
     ⚠️ 这是**唯一**一处允许在机制里出现的几何常量（数据里没有环，无从"从数据推"）。
        两端必须同值 —— 改这里必须同步 krkr 侧 `ui_flow_links.tjs` 的对应常量。 */
  var FLOW_RING = { r: 16, lw: 3, inset: 1, palette: 'node_current' };

  /* 撤掉 parent 里上一次画的某一类 canvas（按 class 名）。幂等：没有就什么都不做。 */
  function clearCanvasIn(parent, cls) {
    if (!parent || !parent.querySelectorAll) return 0;
    var olds = parent.querySelectorAll('.' + cls), n = olds.length;
    for (var i = 0; i < n; i++) if (olds[i].parentNode) olds[i].parentNode.removeChild(olds[i]);
    return n;
  }

  /* 层 flag 名：该屏**声明 `action:"flow_layer"` 的热区**所带 `vis_flag`（数据唯一出处）。
     恰好一个 ⇒ 返回它；0 个 ⇒ ''（本屏无层机制，层判据整体不生效）；
     多个 ⇒ 仍取首个但**打判词**（不静默择一；也不因数据异常打断渲染）。 */
  function flowLayerFlagName(def) {
    if (!def) return '';
    var names = [];
    (def.elements || []).forEach(function (e) {
      if (!e || e.kind !== 'hit') return;
      if (String(e.action || '') !== 'flow_layer') return;
      var v = (e.vis_flag === null || e.vis_flag === undefined) ? '' : String(e.vis_flag);
      if (v !== '' && names.indexOf(v) < 0) names.push(v);
    });
    if (names.length > 1) flowLayerReject('(数据)', '声明 flow_layer 的热区带多个 vis_flag：' + names.join('、'));
    return names.length ? names[0] : '';
  }

  /* 「主干」取值：该屏 `flags_default` 里层 flag 的**初值**（数据唯一出处）。缺 ⇒ ''。 */
  function flowLayerMainValue(def, flag) {
    if (!def || !flag) return '';
    var v = (def.flags_default || {})[flag];
    return (v === null || v === undefined) ? '' : String(v);
  }

  /* 合法层取值集（**全部从数据推**，三个来源取并集）：
     ① 该屏 `flags_default` 里层 flag 的初值（＝「主干」）；
     ② 该 flag 出现在元素 `vis_when` 上的全部取值（＝真正有内容可显示的层）；
     ③ **声明 `action:"flow_layer"` 的热区自带的 `layer`**（＝数据亲手点名的目标层）。
     ★ ③ 不可省：交付样例 `screen1` 只有入口热区、**没有番外独立层元素**（那 6 件是 `frag`
       预设才产的演示件）⇒ 若只按 ② 收集，`frag1..frag6` 会被判成"未知层"而拒绝，
       与数据自己的意图正面冲突（实测：点击 `fc.entry.*_hit` 完全不生效）。
       `"*"` 不是具体层名，排除。 */
  function flowLayerValues(def, flag) {
    var vals = [];
    if (!def || !flag) return vals;
    function add(v) { if (v !== '' && v !== '*' && vals.indexOf(v) < 0) vals.push(v); }
    add(flowLayerMainValue(def, flag));
    (def.elements || []).forEach(function (e) {
      if (!e) return;
      if (e.vis_flag !== null && e.vis_flag !== undefined && String(e.vis_flag) === flag)
        add((e.vis_when === null || e.vis_when === undefined) ? '' : String(e.vis_when));
      if (e.kind === 'hit' && String(e.action || '') === 'flow_layer' && e.layer !== null && e.layer !== undefined)
        add(String(e.layer));
    });
    return vals;
  }

  /* 判词出口（与 M06/M08/E3LINKS 同款：去重后进 console.warn + `state.flowLayer.rejects`）。 */
  function flowLayerReject(act, reason) {
    var line = '★E3LAYER-REJECT★ ' + act + ' ' + reason;
    if (state.flowLayer.rejects.indexOf(line) < 0) state.flowLayer.rejects.push(line);
    try { console.warn('[UI][REJECT] ' + line); } catch (e) { }
    return line;
  }

  /* 重画**本屏的程序化叠加层**（连线 + `current` 环）—— `flow_layer` 切层后必须调，
     否则「DOM 显隐已改、canvas 还是上一层的」⇒ 同一状态下画面与数据分叉。
     绘制顺序与 `renderScreen` 一致：连线在节点之下、环在全部元素之上。 */
  function refreshFlowLayers(screenId) {
    var id = screenId || state.screen;
    if (id !== 'flowchart') return false;                 /* 现仅流程图有这两层 */
    var def = SCREENS[id];
    if (!def || !layerEl) return false;
    drawLinks(def, layerEl, state.refs);
    drawCurrentRing(def, layerEl, state.refs);
    return true;
  }

  /* ★ 动作 `flow_layer` 的实现（`hit.action`，带 `layer` 参数；冻结 §二 / `_schema.md` §六）。
     语义：把**屏级 flag**（`flowLayerFlagName`）置为 `layer` 并**重绘 / 重算命中**。
     —— 只切层：「哪些节点已读 / 已解锁」属运行态（`flow_state` + `fc.state.<NNNN>`，交编程组）。
     —— 未知层 / 本屏无层机制 / 热区未带 `layer` ⇒ **显式拒绝 + 判词**，不静默、不猜；
        拒绝时**不改任何状态**（避免"点了个坏热区却把画面搞花"）。 */
  function flowLayerSet(layer, actStr) {
    var def = SCREENS[state.screen];
    var act = (actStr === null || actStr === undefined) ? 'flow_layer' : String(actStr);
    var lf = (layer === null || layer === undefined) ? '' : String(layer);
    if (!def) { flowLayerReject(act, '当前无屏'); return false; }
    var flag = flowLayerFlagName(def);
    state.flowLayer.flag = flag;
    if (flag === '') { flowLayerReject(act, '本屏数据里没有声明 action:"flow_layer" 的热区 ⇒ 无层机制'); return false; }
    if (lf === '') { flowLayerReject(act, '热区未带 layer 字段'); return false; }
    var vals = flowLayerValues(def, flag);
    if (vals.indexOf(lf) < 0) {
      flowLayerReject(act, '未知层 "' + lf + '"（数据里的合法层：' + vals.join('/') + '）');
      return false;
    }
    state.flowLayer.lastAct = act;
    state.flowLayer.lastLayer = lf;
    state.flowLayer.count++;
    setFlag(flag, lf);
    state.flowLayer.flagValue = getFlag(flag);
    /* ① 元素显隐（**不重建 DOM**：保住 hover/press 台账与运行期节点引用，同 applyFlagVisibility 契约；
        `display:none` 的元素自然不参与命中 ⇒ 「不可见的 hit 不得命中」由浏览器保证）
       ② 程序化叠加层（连线 + 环）按新层重画。 */
    applyFlagVisibility();
    refreshFlowLayers(state.screen);
    return true;
  }

  /* 数据里 `flow_state == "current"` **且当前可见**的节点元素（`current` 环的绘制主语）。
     —— 「可见」= `elementVisible`：`flow_layer != main` 时主干节点整体不可见 ⇒ 环随之不画
        （与冻结 §四.5「命中与绘制恒同集」同源：画出来的必须与数据允许的一致）。 */
  function flowCurrentNodes(def) {
    var out = [];
    ((def && def.elements) || []).forEach(function (e, i) {
      if (!e) return;
      if (String(e.flow_state || '') !== 'current') return;
      if (!elementVisible(e)) return;
      out.push({ el: e, idx: i });
    });
    return out;
  }

  /* `current` 环所在层的 z-index：**在全部元素之上**（冻结 §一.1「画在全部节点之上」）。
     推导式沿用既有 CSS z 公式（`zIndex`）：取该屏元素的最大 raw z-index + 1。
     ⚠️ 已知边界：本屏（flowchart）无 `attach` 附加层；若日后挂附加层，其 raw z 会整体上移
        （`curZBase`），届时本函数须改成「附加层最大 z + 1」。 */
  function flowRingZIndex(def) { return maxZIndexOf(def) + 1; }

  /* 圆角矩形**路径**（只建路径，不 fill / 不 stroke）—— 用 `arcTo`（主流浏览器与无头 Edge
     均支持；`roundRect` 是较新 API，不赌它）。四角各一段半径 r 的弧，与 krkr 侧的
     「圆角矩形描边」同几何；线宽由调用方设（描边**以路径为中心**，两端同款）。 */
  function roundRectPath(ctx, x, y, w, h, r) {
    var rr = Math.max(0, Math.min(Number(r), w / 2, h / 2));
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.lineTo(x + w - rr, y);
    ctx.arcTo(x + w, y, x + w, y + rr, rr);
    ctx.lineTo(x + w, y + h - rr);
    ctx.arcTo(x + w, y + h, x + w - rr, y + h, rr);
    ctx.lineTo(x + rr, y + h);
    ctx.arcTo(x, y + h, x, y + h - rr, rr);
    ctx.lineTo(x, y + rr);
    ctx.arcTo(x, y, x + rr, y, rr);
    ctx.closePath();
  }

  /* 画 `current` 高亮环。**不产元素**（冻结 §一.1）：由 `flow_state == "current"` 驱动，
     一屏一条 canvas（与连线同款：`pointer-events:none`、不参与命中）。
     几何（逐字照冻结）：矩形 = 节点元素矩形**内缩 1px**；圆角半径 16；线宽 3；
     色 = `palette.json` 的 `node_current`（键名冻结、色值不直写）。 */
  function drawCurrentRing(def, parent, map) {
    clearCanvasIn(parent, 'ui-currentring');
    state.ring.drawn = [];
    if (!def || !parent) return;
    var nodes = flowCurrentNodes(def);
    if (!nodes.length) return;
    var cstr = col('@palette.' + FLOW_RING.palette) || '#D8A83C';
    var cv = mk('canvas', 'ui-el ui-currentring');
    cv.width = CANVAS.width;
    cv.height = CANVAS.height;
    cv.style.left = '0';
    cv.style.top = '0';
    cv.style.width = px(CANVAS.width);
    cv.style.height = px(CANVAS.height);
    cv.style.zIndex = flowRingZIndex(def) + curZBase;
    cv.style.pointerEvents = 'none';
    cv.setAttribute('data-ui-kind', 'currentring');
    cv.setAttribute('data-ui-ring-z', String(cv.style.zIndex));
    var ctx = cv.getContext ? cv.getContext('2d') : null;
    if (!ctx) { flowLayerReject('(全部)', 'current 环：canvas 2d 上下文不可用'); return; }
    ctx.lineWidth = FLOW_RING.lw;
    ctx.lineJoin = 'round';
    ctx.strokeStyle = cstr;
    nodes.forEach(function (o) {
      var e = o.el;
      var x = Number(e.x) + FLOW_RING.inset, y = Number(e.y) + FLOW_RING.inset;
      var w = Number(e.w) - 2 * FLOW_RING.inset, h = Number(e.h) - 2 * FLOW_RING.inset;
      if (!(w > 0) || !(h > 0)) return;
      roundRectPath(ctx, x, y, w, h, FLOW_RING.r);
      ctx.stroke();
      state.ring.drawn.push({ id: String(e.id || ''), x: x, y: y, w: w, h: h,
                              r: FLOW_RING.r, lw: FLOW_RING.lw, zoom: flowRingZIndex(def) });
    });
    parent.appendChild(cv);
  }

  function renderElements(def, parent, map) {
    var els = def.elements || [];
    var ordered = els.map(function (e, i) { return { e: e, i: i }; });
    ordered.sort(function (a, b) {
      var za = (a.e.z === null || a.e.z === undefined) ? a.i : Number(a.e.z);
      var zb = (b.e.z === null || b.e.z === undefined) ? b.i : Number(b.e.z);
      if (za !== zb) return za - zb;
      return a.i - b.i;
    });
    clampCands = [];                    // ★ E3 二审：本次调用期间登记的 clamp 候选
    ordered.forEach(function (o) { renderElement(o.e, parent, o.i, map); });
    /* ★ E3 二审：整屏元素已 append 进文档 ⇒ 此刻才量「折行后是否超行」，给真的超行的加 clamp
       （见 resolveClampCands 的长注释：文档外量 scrollHeight 会得到 0）。 */
    resolveClampCands();
  }

  /* ★ M35b：取点击点下方**被遮挡的交互元素**（用于 canvas 兜底派发）。
     用 `elementsFromPoint` 拿到命中栈（已含 z-index 与 CSS transform），自上而下找第一个
     `[data-ui-interactive]`；跳过 `ev.target` 自己（它是非交互元素才走到这里）。
     与 krkr 的 `uiScreenClick`（几何扫描 `kind ∈ {hit,list}` 取 z 最高）**同口径**：
     两者都是「最上面的交互元素赢」。 */
  function interactiveUnderPoint(ev) {
    if (!document.elementsFromPoint || typeof ev.clientX !== 'number') return null;
    var stack;
    try { stack = document.elementsFromPoint(ev.clientX, ev.clientY); } catch (e) { return null; }
    for (var i = 0; i < stack.length; i++) {
      var el = stack[i];
      if (!el || el === ev.target || !el.closest) continue;
      var node = el.closest('[data-ui-interactive]');
      if (node) return node;
    }
    return null;
  }

  function renderScreen(id, opts) {
    opts = opts || {};
    var def = SCREENS[id];
    var isOverlay = !!(def && def.overlay);

    /* ★ M35：规则 ④ —— 换屏即清按下态（旧屏的 DOM 已销毁，台账必须跟着清，
       否则 pressHolder 会指向游离节点）。与 krkr 侧 uiScreenHoverClear 里的清除对齐。 */
    pressRelease();

    /* ★ M47：换屏即**结束滑块拖动并清悬停**（对应 krkr 的 uiScreenHoverClear 里
       `UIScrDragSlider = ""; UIScrHoverSlider = "";` 两条）—— 旧屏的 slider id 必须不留，
       否则下次进屏时手柄会带着旧屏的「活动」图，且拖动会指向已销毁的节点。 */
    dragDocUnbind();
    sliderDragEnd();

    /* ★ M3：换屏（含 push/pop）取消呼出收起计时、复位附加层与指针台账 ——
       旧 DOM 已销毁/换屏，任何在途的收起延时都必须作废（krkr 侧同口径）。 */
    cancelRevealTimer();
    state.attachId = null;
    revealRt.lastX = null; revealRt.lastY = null;
    /* ★ E3：换屏即复位连线台账（本屏绘制的连线由 drawLinks 重新记账）。
       ★ 第 2 步：`flow_layer` 台账与 `current` 环台账同款复位（环由 drawCurrentRing 重新记账）。 */
    state.links.drawn = [];
    state.links.rejects = [];
    state.links.blocked = false;
    state.links.layer = '';
    state.flowLayer.lastAct = '';
    state.flowLayer.lastLayer = '';
    state.flowLayer.count = 0;
    state.flowLayer.rejects = [];
    state.flowLayer.flag = '';
    state.flowLayer.flagValue = '';
    state.ring.drawn = [];

    if (!isOverlay) {
      var prevScreen = state.screen;
      /* push 形进入 = 与 krkr `uiScreenPush` 对应的那一支（open_* 动作 / 深链首进）；
         goBack（= pop）与页签切屏（= replace，noHistory）不算。 */
      var isPushEntry = !opts.noHistory && prevScreen && prevScreen !== id && !state.underScreen;
      /* 普通屏：浮层屏不入历史（它是「栈上的浮层」，收起即回到下层，不是一次导航） */
      if (isPushEntry) {
        state.history.push(prevScreen);
      }
      state.screen = id;
      state.underScreen = null;
      state.baseScreenId = id;
      state.refs = {};
      state.baseRefs = {};
      if (overlayEl) overlayEl.innerHTML = '';
      layerEl.innerHTML = '';
      /* ★ M35b 修（一审 Critical-1）：**DOM 重建前必须复位组注册表**。
         注册表是模块级、跨渲染代际的容器；旧代成员若留在表里，其 ownHover/ownPress 会**冻结**
         （元素在指针悬停状态下被 innerHTML='' 移除时，浏览器**不会**派发 mouseleave），
         此后 groupSync 会把僵尸成员的 ownHover OR 进去 ⇒ **悬停永久不灭，只能刷新页面**。
         krkr 侧不受影响（每帧由 ctx 重算，无跨代状态），故不做复位会造成两端分叉。
         复位点选在这里（真正清空 DOM 的分支），浮层屏保留下层 DOM 时不清，避免误清下层成员。 */
      resetStates();
      /* ★ M1：换屏即按新屏的 flags_default 重置屏级 flag（与 krkr 侧 uiScreenReset/
         uiScreenPush/uiScreenPop 里的 uiScreenFlagsInitFor(栈顶屏) 对齐）。 */
      initFlagsFor(id);
      /* ★ M47：紧接着做**值 flag 派生**（与引擎 uiScreenConfigFlagsInitFor 同位置、同语义）——
         见该函数的长注释：`flags_default` 只描述「某个值」，值元素不带页 flag ⇒ 进屏那一刻
         非本页的值元素会残留可见（实测系统页初值态 4 件）。 */
      configFlagsInitFor(id);
      /* ★ M1（ISSUE-20260924-08）：鉴赏外壳的**当前页签高亮**按承载屏 id 派生
         （与 krkr 侧 `uiScreenGalleryShellSyncFor` 同位置、同语义；别的屏返回 0，零副作用）。 */
      galleryShellSyncFor(id);
      /* ★ M8 一审 + 主代理追认项⑥（2026-09-24）：挂壳屏「重进」⇒ 页码/差分序号/页码 flag 归零。
         与 krkr 的 `uiScreenGalleryEntryResetFor`（Reset/Push/Pop 三路径）同口径；HTML 侧
         「重进」= push 形进入（isPushEntry）或首进（prevScreen 为空）。页签切屏与同屏重画
         （翻页动作的 renderScreen）都不在此列 ⇒ 不会把刚翻到的页清掉。 */
      if (def && String(def.attach || '') === GALLERY_SHELL_ID
          && (isPushEntry || !prevScreen || opts.popEntry)) {
        galleryPageVariantClearFor(id);
      }
      /* ★ M43：进入流程图屏时把光标节点对齐到当前节点（与 krkr 侧 uiFlowOnOpen 的
         `UIFlowCursor = UIFlowCurrent` 逐条同口径）——否则「进入本章」按钮在没按过方向键时
         会读到空光标。无节点数据（flow_data.js 未加载）时 flowEnsure 返回 false，此处不写状态。 */
      if (id === 'flowchart' && flowEnsure()) state.flow.cursor = state.flow.current;
      layerEl.className = 'ui-screen ui-screen-' + id;
      if (!def) { renderNoScreen(id); syncScreenChrome(id); return; }
      if (def.bg) renderElement(def.bg, layerEl, -1, state.refs);
      /* ★ E3：连线层 —— 与 bg 之后、节点元素之前（层序由 linksLayerZ 从数据推，见 §4.9） */
      drawLinks(def, layerEl, state.refs);
      renderElements(def, layerEl, state.refs);
      /* ★ 第 2 步：`current` 高亮环 —— 在**全部元素之上**（见 drawCurrentRing）。仅在主屏分支调用；
         浮层分支另有自己的调用点（`flowchart` 从不是浮层，此处分支只为口径一致）。 */
      drawCurrentRing(def, layerEl, state.refs);
      /* ★ M3：附加层（屏级 attach）——承载屏元素之后叠画（与 krkr 侧 M2 同契约） */
      renderAttachLayer(def, layerEl, state.refs);
      /* ★ M47：**每次 renderScreen 之后**把设置仓灌进渲染层（方案 §三.3 的时机惯例，
         同 applyFlagVisibility）。HTML 侧没有「每帧重建 ctx」这回事，故在这里补一遍：
         换到 config / dialog 时遮罩的 opacity 必须立刻等于 dlg_winopac（**不重建 DOM**）。 */
      applySettingOverrides();
      syncScreenChrome(id);
      updateDemoNote(def);
      /* keepDialog：由 closeOverlay() 传 true —— 收起浮层回到对话框时**不得重播台词** */
      if (id === 'dialog' && !opts.keepDialog) startDialog();
      return;
    }

    /* ★ M15：浮层屏（屏对象 overlay:true，如 sysicons）——必须**先把下层屏画出来**，
       再叠本屏。对齐 krkr 侧 ui_screens.tjs:175-216 的同一分支；否则屏内的全屏压暗
       rect（sysicons.veil，色 @palette.backdrop）压的是一张被清空的透明画面 → 实机纯黑。 */
    var under = state.underScreen || state.screen || 'title';
    if (!SCREENS[under] || SCREENS[under].overlay) under = 'title';
    state.underScreen = under;
    state.screen = id;
    /* ★ M1：浮层屏也是「换屏」，flags 归当前绘制屏（= 浮层屏）。
       注：本分支会把下层屏一并画进 layerEl，若那屏的元素带 vis_flag，其判定会用到
       浮层屏的 flags —— 现有数据无此用法（`attach` 附加层须由叠画方自行切换 flags）。 */
    initFlagsFor(id);
    /* ★ M47：浮层屏同样在 flag 初始化后派生值 flag（与普通屏同规则；浮层屏
       （sysicons）屏内没有 `config_set_*` / `config_char_*` ⇒ 该函数对它自动返回 0）。 */
    configFlagsInitFor(id);
    /* ★ M3：承载屏若带附加层，把它的 flag 初值也并进当前表 —— 这样下层屏（dialog）
       被重画时，附加的 quickbar 元素能按同一张表判定（默认即收起态）。 */
    var udefA = SCREENS[under];
    if (udefA && udefA.attach) mergeAttachFlags(String(udefA.attach));
    var prevRefs = state.refs;      // ★ 下层屏当前的元素引用（见下方 else 分支）
    state.refs = {};

    /* 下层屏若已由同一屏渲染且 DOM 尚在，则**原地保留**（保住对话框运行期 DOM，
       如已弹出的选择肢），只重画浮层——语义等同 krkr 的 uiScreenPush（下层不重建）。 */
    if (state.baseScreenId !== under || !layerEl.firstChild) {
      layerEl.innerHTML = '';
      layerEl.className = 'ui-screen ui-screen-' + under;
      state.baseRefs = {};
      var udef = SCREENS[under];
      if (udef) {
        if (udef.bg) renderElement(udef.bg, layerEl, -1, state.baseRefs);
        drawLinks(udef, layerEl, state.baseRefs);        /* ★ E3：下层屏的连线 */
        renderElements(udef, layerEl, state.baseRefs);
        drawCurrentRing(udef, layerEl, state.baseRefs);  /* ★ 第 2 步：下层屏的 current 环 */
        /* ★ M3：附加层在浮层下同样要画出来（浮层是叠在上面的，下层该有的都得有） */
        renderAttachLayer(udef, layerEl, state.baseRefs);
      }
      state.baseScreenId = under;
    } else {
      /* ★ M15 自检抓到的真缺陷（?selftest=1 的 sysicons.base-DOM-preserved 曾 FAIL）：
         下层 DOM 原地保留时，它的元素引用还留在 state.refs 里；若不搬进 state.baseRefs，
         浮层打开期间 refOf() 就取不到对话框元素 —— 打字机 / 隐藏窗口 / 选择肢会静默失效
         （定时器仍在跑、只是画不出来，关掉浮层后文字会「跳」）。故此处必须搬移。 */
      state.baseRefs = prevRefs;
    }

    overlayEl.innerHTML = '';
    overlayEl.className = 'ui-screen ui-screen-' + id;
    if (def.bg) renderElement(def.bg, overlayEl, -1, state.refs);
    drawLinks(def, overlayEl, state.refs);               /* ★ E3：浮层屏自己的连线 */
    renderElements(def, overlayEl, state.refs);
    drawCurrentRing(def, overlayEl, state.refs);         /* ★ 第 2 步：浮层屏自己的 current 环 */
    /* ★ M47：浮层分支同样要在渲染后灌一遍设置仓（浮层压在下层屏上，
       下层的 dlg.mask_bottom 与浮层自己的遮罩都要按当前值画）—— 不重建 DOM。 */
    applySettingOverrides();
    syncScreenChrome(id);
  }

  function renderElement(e, parent, orderIdx, map) {
    if (!map) map = state.refs;
    var node = null;
    switch (e.kind) {
      case 'image': node = buildImage(e, orderIdx); break;
      case 'text':  node = buildText(e, orderIdx); break;
      case 'rect':  node = buildRect(e, orderIdx); break;
      case 'hit':   node = buildHit(e, orderIdx); break;
      case 'slider': node = buildSlider(e, orderIdx); break;   /* ★ M47 */
      case 'list':  node = buildList(e, orderIdx); break;
      case 'anim':  node = buildAnim(e, orderIdx); break;
      default:
        node = buildUnknown(e, orderIdx);
    }
    if (!node) return;
    if (e.id) {
      node.setAttribute('data-ui-id', e.id);
      map[e.id] = { el: node, def: e };
    }
    /* ★ M1：可见性统一走 elementVisible（= visible_default 且 屏级 flag 判定） */
    if (!elementVisible(e)) node.style.display = 'none';
    parent.appendChild(node);
  }

  /* ★ M15：元素引用查询——浮层打开时，下层屏（对话框）的元素在 state.baseRefs 里，
     运行期改写（打字机、窗口隐藏、选择肢）必须两层都查得到，否则浮层一开台词就停更。 */
  function refOf(id) { return state.refs[id] || state.baseRefs[id] || null; }

  /* ---------------------------------------------------------------- image */
  function buildImage(e, orderIdx) {
    var box = resolveBox(e);
    var wrap = mk('div', 'ui-el ui-image');
    applyBox(wrap, box);
    wrap.style.zIndex = zIndex(e, orderIdx);
    var o = opa(e.opacity);
    if (o < 1) wrap.style.opacity = String(o);
    wrap.setAttribute('data-ui-kind', 'image');

    if ((e.asset === null || e.asset === undefined) && e.dynamic) {
      buildDynamic(e, wrap, box);
      return wrap;
    }
    /* ★ M35b：带 `state_assets` 的 image —— 改用与 hit **同一套**「贴图 + 状态机」画法
       （而不是 <img>），这样文字图也能有悬停/按下形态，并能与图标用 `state_group` 组绑定。
       放在 `if (!e.asset)` 之前：允许「只给 state_assets、不给 asset」的文字按钮。
       ★★ 必须区分 nine 口径：带九宫格的按钮底图（迁移后态图落在 x_ui_spk_off 这类
          25×27 美术上、版面 25×35）要按**九宫格**画，若走 background-image 整图拉伸，
          就退回了我们要消除的那种涂抹。故 nine（且非全零）走 border-image 状态机。 */
    if (e.state_assets && e.nine && !isZeroNine(e.nine)) {
      var stN = e.state_assets, nN = e.nine;
      var dn = mk('div', 'ui-nine');
      dn.style.borderWidth = [nN.t, nN.r, nN.b, nN.l].map(px).join(' ');
      dn.style.borderImageSlice = [nN.t, nN.r, nN.b, nN.l].join(' ') + ' fill';
      dn.style.borderImageRepeat = 'stretch';
      dn.setAttribute('data-ui-stateimage', 'nine');
      var selfN = attachStates(dn, stN, e.state_group, stateNinePainer(dn, stN, e.asset));
      selfN.apply();
      attachStateEvents(wrap, selfN);
      wrap.appendChild(dn);
      applyAnim(e, dn, e.anim);
      return wrap;
    }
    if (e.state_assets) {
      var st = e.state_assets;
      var sd = mk('div', 'ui-stateimage');
      sd.style.position = 'absolute';
      sd.style.left = '0'; sd.style.top = '0';
      sd.style.width = '100%'; sd.style.height = '100%';
      sd.style.backgroundSize = '100% 100%';
      sd.style.backgroundRepeat = 'no-repeat';
      sd.setAttribute('data-ui-stateimage', '1');
      /* ⚠️ **监听挂在 wrap 上、绘制落在 sd 上**：`data-ui-id` 在 wrap（探针与外部脚本按它定位），
         若把监听挂在 sd 上，`?hover=<该元素id>` 在 wrap 上派发的 mouseenter 到不了 sd
         ⇒ 悬停文字完全没反应（v1 实测 0 像素差异）。真实鼠标两者都会触发，但探针只认 wrap。 */
      var selfI = attachStates(sd, st, e.state_group, stateImagePainer(sd, st, e.asset));
      selfI.apply();
      attachStateEvents(wrap, selfI);
      wrap.appendChild(sd);
      applyAnim(e, sd, e.anim);
      return wrap;
    }

    if (!e.asset) {
      wrap.classList.add('ui-missing');
      wrap.appendChild(missingLabel('asset 为空：' + (e.id || '?')));
      return wrap;
    }

    var url = assetUrl(e.asset);

    /* ★ M15：全零 nine（整图缩放语义）必须绕开 border-image —— 见 isZeroNine() 注释。
       该分支下 w/h 与 PNG 实尺寸**本就不同**，故不做任何尺寸校验、不画占位。 */
    if (e.nine && !isZeroNine(e.nine)) {
      var d = mk('div', 'ui-nine');
      var n = e.nine;
      d.style.borderWidth = [n.t, n.r, n.b, n.l].map(px).join(' ');
      d.style.borderImageSource = 'url("' + url + '")';
      d.style.borderImageSlice = [n.t, n.r, n.b, n.l].join(' ') + ' fill';
      d.style.borderImageRepeat = 'stretch';
      wrap.appendChild(d);
      probe(url, function () { /* 已由 CSS 渲染 */ }, function () {
        d.style.borderImageSource = 'none';
        wrap.classList.add('ui-missing');
        wrap.appendChild(missingLabel('缺件：' + e.asset));
      });
    } else {
      /* 无 nine，或**全零 nine**（= 允许整图缩放）→ 普通 <img>。
         .ui-image-img 的 width/height:100% 即「整图拉伸到元素矩形」，与 krkr
         uiWidgetNine 在全零时只画中格（operateStretch 整图缩放）等价。 */
      var img = mk('img', 'ui-image-img');
      img.alt = e.asset;
      img.draggable = false;
      if (e.nine) wrap.setAttribute('data-ui-nine', 'zero');
      img.onerror = function () {
        img.remove();
        wrap.classList.add('ui-missing');
        wrap.appendChild(missingLabel('缺件：' + e.asset));
      };
      img.src = url;
      wrap.appendChild(img);
    }

    applyAnim(e, wrap.lastChild, e.anim);
    return wrap;
  }

  /* dynamic 层：asset=null 且给出 dynamic 名。未填充时画占位底色，不跳过。
     演示实现：story_background 用 krkr/assets/ui/ 内的真实素材填充（占位演示）。 */
  function buildDynamic(e, wrap, box) {
    wrap.setAttribute('data-ui-dynamic', e.dynamic);
    /* ★ M15：**不给 wrap 铺底色**。krkr 的占位是 `colorRect(node_locked, panel_fill_opa)`
       ——半透明色块**叠在它下面已画好的画面上**（画廊底图 / 面板填充 …），故观感偏亮。
       若 HTML 侧先给 wrap 铺一层不透明的 panel_fill，半透明占位就会与这层深色混合，
       实测预览区采样 (62,63,74) vs krkr (108,110,122)，明显偏暗（M15 首轮对照抓到）。
       故 wrap 保持透明，让占位色块与「下面真正的画面」混合，与 krkr 逐像素对齐。 */
    wrap.style.background = 'transparent';

    var demo = mk('div', 'ui-dynamic-demo');
    demo.style.position = 'absolute';
    demo.style.left = '0'; demo.style.top = '0';
    demo.style.width = '100%'; demo.style.height = '100%';
    demo.style.backgroundSize = 'cover';
    demo.style.backgroundPosition = 'center';
    demo.style.backgroundRepeat = 'no-repeat';
    wrap.appendChild(demo);

if (e.dynamic === 'story_background' && DEMO_BG_CANDIDATES.length) {
      var i = 0;
      (function tryNext() {
        if (i >= DEMO_BG_CANDIDATES.length) {
          markDynamicEmpty(wrap, demo, box, e.dynamic);
          return;
        }
        var name = DEMO_BG_CANDIDATES[i++];
        var u = assetUrl(name);
        probe(u, function () {
          demo.style.backgroundImage = 'url("' + u + '")';
          wrap.setAttribute('data-demo-asset', 'ui/' + name);
          if (typeof onDemoAsset === 'function') onDemoAsset('ui/' + name);
        }, tryNext);
      })();
    } else {
      /* ★ M15：`gallery_preview`（M14 新增的鉴赏预览层）与 `slot_thumb` / `story_background`
         同待遇——**未填充时画占位底色 + 标注，不得跳过**（layout/_schema.md §四 dynamic 条）。
         用中性的 .ui-dynamic-empty 而非「缺件」红框：这是「运行期待填充」的正常状态，
         不是资产缺失。 */
      markDynamicEmpty(wrap, demo, box, e.dynamic);
    }
    return wrap;
  }

  /* 动态层未填充的占位：**画法与 krkr 侧逐条对齐**
     （ui_widget.tjs:454 uiWidgetDrawPlaceholder）：
       · 底色 = @palette.node_locked，不透明度 = @palette.panel_fill_opa（只作用于底色层，
         文字仍全不透明——krkr 的 colorRect 与 DrawLine 是两个独立调用）；
       · 文字色 = @palette.text_small，**左上对齐**（krkr 从 r.x / r.y 起画）；
       · 两行：「[占位] 动态层」+「dynamic:<名>」，框高不足两行时只画第一行（krkr 同规则）。
     差异（如实登记，见 README）：字号按元素高自适应收敛——krkr 对 168×95 的
     slot_thumb 也按全局字号画，实测文字越出框外；HTML 侧不复制该溢出。 */
  function markDynamicEmpty(wrap, demo, box, dynName) {
    wrap.classList.add('ui-dynamic-empty');
    demo.style.background = col('@palette.node_locked') || '#4A4A56';
    var po = opa(col('@palette.panel_fill_opa'));
    if (po < 1) demo.style.opacity = String(po);

    var fs = fontSize(null, 'small');
    if (box && box.h) fs = Math.max(11, Math.min(fs, Math.round(Number(box.h) / 3)));
    var lineH = Math.max(1, Math.round(fs * 1.25));
    var lines = ['[占位] 动态层'];
    if (!box || !box.h || Number(box.h) >= lineH * 2) lines.push('dynamic:' + dynName);

    var lbl = mk('div', 'ui-dynamic-label');
    lbl.style.fontSize = px(fs);
    lbl.style.lineHeight = px(lineH);
    lbl.style.color = col('@palette.text_small') || '#C8C8D2';
    lbl.textContent = lines.join('\n');
    wrap.title = 'dynamic:' + dynName + ' —— 运行期由调用方填充（layout/_schema.md §四）';
    wrap.appendChild(lbl);
  }

  /* ---------------------------------------------------------------- text */
  /* ★ M15：**文字纵向定位按 krkr 的算法逐式复刻**。
     背景（M15 逐屏对照实测）：krkr 的 `uiThemeLayoutText` 取
         y = el.y + floor((el.h - blockH)/2)        （valign=middle，blockH = 行数 × lineH）
     然后把**行框顶**画在 y 上；而 CSS 在 `line-height > font-size` 时每行会多出
     半行距 `(lineH - size)/2` 的 leading，使字形落点比 krkr 低约 12 px
     （实测 config.title：krkr 墨迹 y=140..182，HTML 152..194，字号与字高一致、只差位移）。
     修法：行框顶按同一公式定位（用 top:50% + translateY(-50%) 居中真实块高，
     等价于 krkr 的 floor((h-blockH)/2)），再整体上移半行距抵消 CSS 的 leading。
     残留约 2–3 px 是「TJS 与浏览器对同一字号的墨迹内边距不同」，属字体栅格化差异。 */
  function buildText(e, orderIdx) {
    var box = resolveBox(e);
    var wrap = mk('div', 'ui-el ui-text');
    applyBox(wrap, box);
    wrap.style.zIndex = zIndex(e, orderIdx);
    wrap.setAttribute('data-ui-kind', 'text');
    wrap.style.display = 'block';       // 不再用 flex 做对齐（改为按 krkr 公式算行框顶）

    var f = e.font || {};
    var size = fontSize(f, e.font_role);
    var lh = size * lineSpacing(e, e.line_spacing_role || 'body');
    var halfLeading = (lh - size) / 2;

    var align = e.align || 'left';
    /* krkr 缺省 valign 为 "top"（ui_theme.tjs:uiThemeLayoutText），与之对齐 */
    var valign = e.valign || 'top';

    var inner = mk('div', 'ui-text-inner');
    inner.style.position = 'absolute';
    inner.style.left = '0';
    inner.style.width = '100%';
    if (valign === 'middle') {
      inner.style.top = '50%';
      inner.style.transform = 'translateY(calc(-50% - ' + px(halfLeading) + '))';
    } else if (valign === 'bottom') {
      inner.style.top = '100%';
      inner.style.transform = 'translateY(calc(-100% - ' + px(halfLeading) + '))';
    } else {
      inner.style.top = '0';
      if (halfLeading) inner.style.transform = 'translateY(' + px(-halfLeading) + ')';
    }
    inner.style.fontSize = px(size);
    inner.style.lineHeight = px(lh);
    inner.style.fontWeight = f.bold ? 'bold' : 'normal';
    if (f.faces && f.faces.length) inner.style.fontFamily = fontChain(f);
    inner.style.color = col(f.color) || (col('@palette.text_primary') || '#ffffff');
    inner.style.textAlign = align;
    /* ★ M15：**显式换行必须保留**。krkr 的 uiThemeWrap 先 `src.split("\n")` 按显式换行
       切段、再逐段折行（ui_theme.tjs:uiThemeWrap）；而 CSS 的 `white-space: normal`
       会把 \n 折叠成空格 —— 实测 flowchart 13 个节点标签因此把「节点名」与
       「otp · 22 场景 / 3531 行」挤成一行再自然折行，与 krkr 的两行结构不符
       （另涉 confirm.text / config.desc_text / music.now_playing / flow.detail，共 17 处）。
       用 `pre-line`：保留 \n、合并连续空格、仍允许自动折行 —— 与 krkr 语义一致。 */
    var hasNL = typeof e.sample === 'string' && e.sample.indexOf('\n') >= 0;
    inner.style.whiteSpace = e.wrap ? (hasNL ? 'pre-line' : 'normal') : (hasNL ? 'pre-line' : 'nowrap');
    if (e.wrap) inner.style.wordBreak = 'break-word';
    /* ★ M38：`text-shadow` 由 textShadowAll() 合成（描边 8 向 + 可选 offset 阴影）。
       它**只改渲染**：下面的 max_lines/-webkit-line-clamp 截断仍按正文字形计算。 */
    var sh = textShadowAll(f);
    if (sh) inner.style.textShadow = sh;
    if (e.wrap && e.max_lines) {
      /* ★ E3 二审：**先不加 clamp** 铺一遍（要量自然行数：clamp 会把 scrollHeight 截到 N 行），
         由 `renderElements` 在整屏元素入文档后统一判定（见 resolveClampCands 的长注释）。
         若本函数不是经 renderElements 调用（无登记表）⇒ 退回「总是加 clamp」= 改动前行为。 */
      inner.style.display = 'block';
      inner.style.overflow = 'visible';
    }
    inner.textContent = (e.sample !== null && e.sample !== undefined) ? String(e.sample) : '';
    wrap.appendChild(inner);
    if (e.wrap && e.max_lines) {
      if (clampCands) clampCands.push({ inner: inner, maxLines: Number(e.max_lines), lh: lh });
      else applyClamp(inner, e.max_lines);          // 兜底：拿不到登记表 ⇒ 与改动前逐字相同
    }
    return wrap;
  }

  /* ---------------------------------------------------------------- rect */
  function buildRect(e, orderIdx) {
    var box = resolveBox(e);
    var d = mk('div', 'ui-el ui-rect');
    applyBox(d, box);
    d.style.zIndex = zIndex(e, orderIdx);
    d.style.background = col(e.color) || '#000000';
    var o = opa(e.opacity);
    if (o < 1) d.style.opacity = String(o);
    d.setAttribute('data-ui-kind', 'rect');
    return d;
  }

  /* ---------------------------------------------------------------- slider（★ M47） */
  /* `kind:"slider"` —— 画法与 krkr 的 `uiWidgetDrawSlider`（ui_widget.tjs）**逐条同口径**：
      ① 轨道：以元素**垂直中心线**为轴。几何由**引擎源码**定档（`uiWidgetDrawSlider:1435`）：
         `rh = (rail.nine 存在) ? el.h : 素材高`，再 `blit(el.w, rh, rail.nine)` ⇒ 三条分支：
           · nine 非全零 ⇒ 九宫格拉满元素框（HTML `border-image`，border-width = nine 的四边）；
           · **nine 全零** ⇒ rh = `el.h`，经 `uiWidgetNine` 的全零分支（只画中格）
             = **整图拉伸到元素框**（HTML `background-size:100% 100%`）；
           · 无 nine ⇒ rh = **素材高**，即 `el.w × 素材高`（HTML `100% auto`，仅当
             素材宽 == 元素宽时与之等价 —— 数据侧义务，见下方注释）。
         ★ 2026-09-28 修正：全零 nine 原先与「无 nine」共用 `100% auto`（等比），
           与引擎的「取 el.h」分叉：本屏声音滑轨素材 360×30、元素 330×30 ⇒
           旧写法实绘高 27.5px、引擎 30px，**两端差 2.5px**（六条声音滑轨全部命中）。已按上式改开。
      ② 手柄：`handle` 的素材（活动时 `state_assets.hover`），按**素材自身尺寸**（29×29）画在
         「值对应的轨道 x」为中心处，**不随元素框裁剪**（元素 h=24 < 29 ⇒ 上下各溢出 2–3px，
         故 wrap 显式 `overflow:visible`）。位置式与引擎同：左 = 中心 x − floor(宽/2)，
         上 = y + floor((h − 高)/2)（见 sliderPaint）。
      ③ 值：`state.settings`（有 `setting` 且仓认该键）→ 滑块运行值仓 → 元素 `value` 初值，
         见 §4.7 的 sliderValue()。**换屏回来保留运行期值**（与 UIScrSliderVal 同）。
      ④ 拖动由**配对的热区**驱动（`kind:"hit"` + 字段 `slider:"<slider 元素 id>"`），
         见 buildHit 的滑块分支；本 kind **不参与**任何悬停候选并集（不改既有判据）。 */
  function buildSlider(e, orderIdx) {
    var box = resolveBox(e);
    var wrap = mk('div', 'ui-el ui-slider');
    applyBox(wrap, box);
    wrap.__box = box;                      // ★ 手柄定位要用**实框原点**（见 sliderPaint 的说明）
    wrap.style.zIndex = zIndex(e, orderIdx);
    wrap.style.overflow = 'visible';       // ② 手柄不按元素框裁剪
    wrap.style.pointerEvents = 'none';     // 滑块本身不吃命中（拖动只走配对热区，与引擎同口径）
    wrap.setAttribute('data-ui-kind', 'slider');

    /* ① 轨道 */
    var rail = e.rail || {};
    if (rail.asset) {
      var rd = mk('div', 'ui-slider-rail');
      rd.style.position = 'absolute';
      rd.style.left = '0';
      rd.style.width = '100%';
      rd.style.top = '0';
      rd.style.height = '100%';
      var ru = 'url("' + assetUrl(rail.asset) + '")';
      if (rail.nine && !isZeroNine(rail.nine)) {
        var n = rail.nine;
        rd.style.borderStyle = 'solid';
        rd.style.borderColor = 'transparent';
        rd.style.borderWidth = [n.t, n.r, n.b, n.l].map(px).join(' ');
        rd.style.borderImageSource = ru;
        rd.style.borderImageSlice = [n.t, n.r, n.b, n.l].join(' ') + ' fill';
        rd.style.borderImageRepeat = 'stretch';
      } else if (isZeroNine(rail.nine)) {
        /* ★ 全零 nine 的轨道：引擎 `uiWidgetDrawSlider` 的 `rh2 = (rNine != void) ? el.h : 素材高`
           ——**给了 nine（哪怕全零）就取元素高**，再由 `uiWidgetNine` 的全零分支
           （只画中格 = 整图拉伸）拉成 `el.w × el.h`。
           ⇒ HTML 必须写 `100% 100%`（**整图拉伸到元素框**），**不能**用 `100% auto`（等比）：
           二者只在「素材宽 == 元素宽」时才相等，本屏声音滑轨素材 360 宽、元素 330 宽 ⇒
           旧写法实绘高 27.5px（30×330/360），引擎 30px ⇒ **两端差 2.5px**（2026-09-28 实测；
           `cfg.sl_master/bgm/se/sysse/voice/char` 六条声音滑轨）。 */
        rd.style.backgroundImage = ru;
        rd.style.backgroundRepeat = 'no-repeat';
        rd.style.backgroundPosition = 'center center';
        rd.style.backgroundSize = '100% 100%';
      } else {
        /* 无 nine ⇒ 引擎 `rh2 = 素材高`，blit 到 `el.w × 素材高`（**横向铺满、纵向 1:1**）。
           `100% auto` 与它等价**当且仅当素材宽 == 元素宽**（本工程 3 条无 nine 滑轨
           `cfg.sl_winopac/textspeed/autospeed` 均 360 == 360，实测等价）。
           ⚠️ 数据侧义务：无 nine 的 rail 必须满足 `el.w == 素材宽`，否则这里会等比缩放、
           与引擎分叉（登记在 `layout\_schema.md` 的 slider 节）。 */
        rd.style.backgroundImage = ru;
        rd.style.backgroundRepeat = 'no-repeat';
        rd.style.backgroundPosition = 'center center';
        rd.style.backgroundSize = '100% auto';
      }
      wrap.appendChild(rd);
      wrap.__rail = rd;
    }

    /* ② 手柄（自己一个节点，超出元素框的部分不裁剪） */
    var knob = mk('div', 'ui-slider-knob');
    knob.style.position = 'absolute';
    knob.style.width = px(SLIDER_KNOB);
    knob.style.height = px(SLIDER_KNOB);
    knob.style.backgroundRepeat = 'no-repeat';
    knob.style.backgroundSize = '100% 100%';
    knob.setAttribute('data-ui-slider-knob', '1');
    wrap.appendChild(knob);
    wrap.__knob = knob;

    /* ③ 初始值 / 位置 / 手柄图 —— 与拖动更新走**同一个出口**（sliderPaint），保证两条路径同式。
       注：此时 renderElement 还没把本节点登记进 refs，故这里**不能用 sliderSyncDom(按 id)**，
       必须直接拿节点画。 */
    sliderPaint(wrap, e);
    if (!knob.style.backgroundImage || knob.style.backgroundImage === 'none') {
      if (!sliderHandleAsset(e, false)) {
        /* handle.asset 与 state_assets.normal 都没有 ⇒ 可读缺件标注（不崩） */
        wrap.classList.add('ui-missing');
        wrap.appendChild(missingLabel('handle.asset 为空：' + (e.id || '?')));
      }
    }
    return wrap;
  }

  /* ★ M35：按下态（pressed）的**全局台账** + ★ M35b：**state_group 组绑定**。
     规则表（**与 krkr 的 ui_screens.tjs / ui_widget.tjs 必须逐条一致**，改一处就要改两处）：
       ① 左键在元素上按下      -> 该元素进入按下态（同一时刻至多一个）
       ② 左键抬起（不论位置）  -> 清除      ← 由本文件的 document mouseup 兜底
       ③ 指针移出该元素        -> 清除
       ④ 换屏 / 重渲染         -> 清除      ← 由 renderScreen 调 pressRelease()
                                               （HTML 侧比 krkr 多一种：**同屏重渲染也清**。
                                                因为 DOM 会重建、监听器随之消失，不清反而会留
                                                pressHolder 悬挂引用；krkr 只需在换屏（栈操作）时清。）
       ⑤ 绘制优先级            -> pressed > hover > normal，缺键逐级回落
       ⑥ **组绑定（M35b）**     -> 带同一 `state_group` 的元素共享 ①–③ 的结果：
                                   鼠标落在组内任意一者上、或组内任意一者被按住，
                                   **全组一起**进入悬停/按下形态。
     变体：`state_assets` 不再只属于 hit —— 任何元素（含 image）都能带三态图。
     ★ 本台账修的是**旧实现的真实 bug**：旧代码只给 mousedown 换了图，**没有抬起复位**，
       按住后在元件内松开，贴图会一直粘在 pressed 态，直到鼠标移出（mouseleave）才复位。
     ★ HTML 是「DOM 状态」模型（每个元件维护自己的 flag，组内广播），
       krkr 是「每帧重算」模型（ctx 带着 hoverHit/hoverGroup 重新判定）——
       两边模型不同、**表现必须相同**。 */
  var pressHolder = null;      // { el: DOM 节点, release: function }
  function pressRelease() {
    if (!pressHolder) return;
    var h = pressHolder;
    pressHolder = null;
    try { h.release(); } catch (e) {}
  }
  /* 抬起兜底：监听 document，元素上没接住（在元件外松开 / 拖出窗口 / 失焦）也能复位。
     只注册一次，不是每个元素一份。
     ★ M35 一审 Minor-2：**必须过滤 `ev.button === 0`** —— 否则右键抬起会把仍按住的左键
     状态一起清掉（krkr 侧不会：右键不触发 onClick）。 */
  document.addEventListener('mouseup', function (ev) { if (ev && ev.button !== 0) return; pressRelease(); });
  document.addEventListener('blur', function () { pressRelease(); });
  window.addEventListener('blur', function () { pressRelease(); });

  /* ---- state_group 组注册表：group 名 -> [成员] ---- */
  var stateGroups = {};
  /* ★ M35b 修（一审 Critical-1）：复位组注册表 —— 必须在**清空 DOM 的同一个渲染分支**里调用，
     否则旧代成员留在表里，其 ownHover 会冻结为真（见 renderScreen 里的长注释）⇒ 悬停永不熄灭。 */
  function resetStates() {
    pressRelease();
    stateGroups = {};
  }
  /* 成员：{ own(自身指针状态), eff(生效状态, 含组内其它成员), apply() } */
  function groupSync(g) {
    var ms = stateGroups[g];
    if (!ms) return;
    var hov = false, prs = false;
    for (var i = 0; i < ms.length; i++) {
      /* 防御（一审建议的双保险）：已被移出文档的成员不再参与 OR —— 即便哪天漏了 resetStates，
         僵尸成员也不会把状态钉死。`isConnected` 在现代浏览器与无头 Edge 上均可用；
         老引擎不支持时该表达式为 undefined，`=== false` 不成立 ⇒ 退化为「不跳过」，行为不变。 */
      if (ms[i].d && ms[i].d.isConnected === false) continue;
      if (ms[i].ownHover) hov = true;
      if (ms[i].ownPress) prs = true;
    }
    for (var j = 0; j < ms.length; j++) {
      if (ms[j].d && ms[j].d.isConnected === false) continue;
      ms[j].effHover = hov;
      ms[j].effPress = prs;
      ms[j].apply();
    }
  }

  /* 给一个元素挂上「三态贴图」状态机。hit 与 image 共用（M35b）。
     st = state_assets；d = DOM 节点；group = state_group（"" = 无组）
     ★ 第 2 步（ISSUE-20260928-02）修一处**静默分叉**（原实现对「无组元素」永不换态）：
       `apply()` 读的是 `effHover`/`effPress`（生效态），而这两个字段原先**只在 `groupSync` 里被赋值**
       ⇒ `group === ''` 时 `publish()` 走 `self.apply()`，读到的恒为初始 `false`，
       **该元素的 `state_assets` 除初态外一次都不生效**（`ownHover` 被置了、但没人把它抄进 `eff`）。
       为什么一直没被发现：此前所有元素级 `state_assets` 都同时带 `state_group`（M35b/M37 把「组」
       当成了常规写法），自检 ⑴–⑸/⑱ 的主语也都带组 ⇒ 这条路**零覆盖**。
       第 2 步的流程图数据里 22 件带 `state_assets` 的件**无组**（`fc.scr_up/dn`、`fc.zoom_*`、
       `fc.shift_*`、`fc.fusen_*`、`fc.pbkick`、`fc.node.*`），实测「悬停/按下贴图恒为常态」。
       修法 = 无组时把 own 抄进 eff（组内的 OR 语义不变）。 */
  function attachStates(d, st, group, applyFn) {
    var self = { d: d, st: st, group: group || '',
                 ownHover: false, ownPress: false, effHover: false, effPress: false };
    /* ★ M35b：`applyFn` 允许为 null —— 用于**没有态图的纯热区**（迁移后热区退回纯热区，
       但仍要参与状态检测，才能把状态广播给同组的 image）。此时 apply() 是空操作。 */
    self.apply = function () { if (applyFn) applyFn(self.effHover, self.effPress); };
    function publish() {
      if (self.group) {
        groupSync(self.group);
      } else {
        /* 无组：本元素自己的指针状态就是生效态（与组内「任一成员 ⇒ 全组」的 OR 不同） */
        self.effHover = self.ownHover;
        self.effPress = self.ownPress;
        self.apply();
      }
    }
    if (self.group) {
      (stateGroups[self.group] = stateGroups[self.group] || []).push(self);
    }
    self.publish = publish;
    return self;
  }

  /* 段位回落选图（与 krkr 的 uiWidgetStateAsset 同序）：
     按下 → pressed/hover/normal；悬停 → hover/normal；否则 normal；再回落 fallback。 */
  function pickState(st, hovering, pressing, fallback) {
    var a = null;
    if (pressing && st.pressed) a = st.pressed;
    if (!a && (pressing || hovering) && st.hover) a = st.hover;
    if (!a && st.normal) a = st.normal;
    if (!a) a = fallback || null;
    return a;
  }

  /* 三态贴图的选图函数（背景图口径）。**段位最高且存在**的那一态胜出；缺键沿段位向下逐级回落。
     ★ M35b 修（与 krkr 同一 bug）：旧写法是「浅回落」——只在 `pressing && st.pressed` 时才用按下态，
       于是「按下 + 该元素没填 pressed + 未悬停」会掉回 normal（实机实测文字区 0 像素差异）。 */
  function stateImagePainer(d, st, fallbackAsset) {
    return function (hovering, pressing) {
      var a = pickState(st, hovering, pressing, fallbackAsset);
      if (a) d.style.backgroundImage = 'url("' + assetUrl(a) + '")';
      else d.style.backgroundImage = 'none';
    };
  }

  /* 同上，但走**九宫格口径**（border-image）—— 用于带 `nine` 的可拉伸按钮底图。
     ★ M35b：热区迁移后，态图落在这些九宫格底图上（x_ui_spk_off 等 25×27 美术要按九宫格拉到
       25×35 的版面），所以必须支持「态图 + nine」，否则会退回整图拉伸（正是我们要消除的涂抹）。 */
  function stateNinePainer(d, st, fallbackAsset) {
    return function (hovering, pressing) {
      var a = pickState(st, hovering, pressing, fallbackAsset);
      if (a) d.style.borderImageSource = 'url("' + assetUrl(a) + '")';
      else d.style.borderImageSource = 'none';
    };
  }


  /* 给元素绑定 hover / pressed 的 DOM 事件（hit 与 image 共用） */
  function attachStateEvents(d, self) {
    d.addEventListener('mouseenter', function () { self.ownHover = true; self.publish(); });
    d.addEventListener('mouseleave', function () {          // 规则 ③
      self.ownHover = false;
      if (self.ownPress) {
        self.ownPress = false;
        if (pressHolder && pressHolder.el === d) pressHolder = null;
      }
      self.publish();
    });
    d.addEventListener('mousedown', function (ev) {         // 规则 ①（只认左键，与 krkr 一致）
      if (ev.button !== 0) return;
      pressRelease();                                        // 同一时刻至多一个按下态
      self.ownPress = true;
      pressHolder = { el: d, release: function () { self.ownPress = false; self.publish(); } };
      self.publish();
    });
    d.addEventListener('mouseup', function () {              // 规则 ②（document 上还有一层兜底）
      if (!self.ownPress) return;
      self.ownPress = false;
      if (pressHolder && pressHolder.el === d) pressHolder = null;
      self.publish();
    });
  }

  function buildHit(e, orderIdx) {
    var box = resolveBox(e);
    var d = mk('div', 'ui-el ui-hit');
    applyBox(d, box);
    d.style.zIndex = zIndex(e, orderIdx);
    d.setAttribute('data-ui-kind', 'hit');
    d.setAttribute('data-ui-interactive', '1');
    if (e.action) d.setAttribute('data-ui-action', e.action);
    if (e.index !== undefined) d.setAttribute('data-ui-index', String(e.index));
    if (e.slot !== undefined) d.setAttribute('data-ui-slot', String(e.slot));

    /* 可选三态贴图（★ M35b：抽成公共状态机，hit 与 image 共用；规则见文件上方规则表）
       ★★ M35b 热区迁移后：**hit 一律挂状态机**，即使它自己没有态图 ——
       迁移把「热区拉伸态图」改成了「热区退回纯热区 + 态图挪到旁边的 1:1 image」，
       此时热区必须仍能被 hover/按下检测到，才能把状态广播给同组的 image（规则⑥）。
       没有态图的 hit 传 null painter（apply 为空操作），只是当状态源。 */
    /* ★ M35b 二审：判据与 krkr 的 uiScreenHoverAt 对齐 —— 只有「带 state_assets」或
       「带非空 state_group」的 hit 才挂状态机。纯热区（既无态图又无组）挂了也没意义，
       还多 4 个监听；更重要的是**有组的热区要打上 ui-hit-hasstate 类**，
       否则 replica.css 的 `:hover`/`:active` 会给它整块热区刷一层半透明蓝，
       而 krkr 侧无态图的 hit 什么都不画 ⇒ 两端观感分叉（二审 Major-4）。 */
    var stH = e.state_assets;
    var grpH = e.state_group || '';
    /* ⚠️ 这里**绝不能提前 return** —— buildHit 后面还有「标签渲染 / click 监听 / applyAnim」。
       我第一版写成 `if (!stH && !grpH) return d;`（只想着省掉状态机），结果**所有纯热区
       的点击监听一并被跳过**：浮层「点空白收起」的 dismiss 热区正是纯热区 ⇒ 浮层收不起来。
       自带自检套件（index.html?selftest=1）当场报出 4 条 sysicons.* 失败。
       正确做法是**只跳过状态机、继续走完函数**（即下面这个 if 块）。 */
    if (stH || grpH) {
      /* ★ 主代理 2026-09-20 修：background-image 默认按**图片自然尺寸**绘制，
         不写 background-size 时贴图会溢出热区（实测标题菜单 439x122 的贴图画进
         290x81 的热区 → 7 个按钮互相重叠）。krkr 侧 uiWidgetDrawHit 是按 el.w/el.h
         画的，故此处对齐为 100% 100%。 */
      d.style.backgroundSize = '100% 100%';
      d.style.backgroundRepeat = 'no-repeat';
      /* ★ M35 一审 Major-3：带 state_assets 的 hit 打上类名，让 replica.css 的
         `:hover` / `:active` 叠色**不作用**于它（那两处叠色只服务于「没有态图的 hit」）。
         否则 HTML 按住时 = 按下态贴图 **+ 34% 蓝底**，而 krkr 只画贴图 ⇒ 两侧口径不一致。 */
      d.classList.add('ui-hit-hasstate');
    }
    var self = attachStates(d, stH, e.state_group,
                            stH ? stateImagePainer(d, stH, e.asset) : null);
    if (stH) self.apply();
    attachStateEvents(d, self);

    if (e.label !== null && e.label !== undefined) {
      var f = e.font || {};
      /* ★ M15：热区标签也按 krkr 的算法定位（krkr 把它包成 valign=middle 的 text 元素：
         `ui_widget.tjs::uiWidgetDrawHit`）。.ui-hit 已是 flex 居中 ⇒ 等价于 krkr 的
         floor((h - lineH)/2)；再上移半行距抵消 CSS leading（理由见 buildText 注释）。
         ★ ISSUE-20260927-03（模块 I · 用户裁决「统一两端按钮标签墨迹口径」）：与 list 的
         `item_buttons[].label` **同族同病**（同一构造）⇒ 同样**再 +3px**，让热区标签的
         **墨迹**落在按钮**可见体**中线（理由与算式同 `buildList` 该处注释；引擎端同款落点
         `ui_widget.tjs::uiWidgetDrawHit` 一并 +6 ⇒ 两端口径仍恒等）。 */
      var labSize = fontSize(f, 'body');
      var labLh = labSize * lineSpacing(e, e.line_spacing_role || 'body');
      var lab = mk('div', 'ui-hit-label');
      lab.style.fontSize = px(labSize);
      lab.style.lineHeight = px(labLh);
      var labHL = (labLh - labSize) / 2;
      lab.style.transform = 'translateY(' + px(3 - labHL) + ')';
      lab.style.fontWeight = f.bold ? 'bold' : 'normal';
      lab.style.color = col(f.color) || (col('@palette.text_menu') || '#e8e8f0');
      var sh = textShadowAll(f);   /* ★ M38：与 buildText 同一合成（描边 + 阴影） */
      if (sh) lab.style.textShadow = sh;
      lab.textContent = String(e.label);
      d.appendChild(lab);
    }

    /* ★ M47：**滑块拖动热区** —— `kind:"hit"` 上带字段 `slider:"<slider 元素 id>"`
       （方案 §三.2 / `layout/_schema.md`「拖动契约」；字段名是冻结接口，不得改名）。
       契约（与 krkr 侧 ui_screens.tjs 的 uiScreenPressUpdate / uiScreenHoverUpdate /
       uiScreenPressClear 三处**逐条对应**；那边每帧按指针重算，这边靠 DOM 事件重算）：
         · 按下（**只认左键**，同 krkr 的 mbLeft）⇒ 绑定该滑块为拖动目标 + **立刻按 x 置值**；
         · 拖动期间每次指针移动都按 x 更新；**越界 clamp、移出热区/轨道都不取消拖动**
           （⚠️ 与 M35 规则③「指针移出该元素 ⇒ 取消按下态」**语义不同**：那是「按下态不跟
            指针飘」，拖动却必须跟指针走 —— 两个出口只有「左键抬起」与「换屏」）；
         · 抬起 / 指针取消 / 换屏 ⇒ 结束拖动（换屏即清）；
         · 拖动中或悬停该滑块时，手柄换 `state_assets.hover` 图（见 sliderPaint/sliderHot）。
       ★ 为什么用 pointer 事件而不是 mousedown：pointerdown 可 `setPointerCapture`，
         让「指针移出热区」也继续收到 pointermove —— 这是拖动语义的实现手段
         （引擎不需要它，因为那边的更新走全局鼠标移动）。合成事件/无头环境下
         `setPointerCapture` 可能抛（指针未真正活跃），故 try/catch，并以 document 级
         pointermove/pointerup（捕获阶段）兜底（bindDragDoc）。
       ★ 热区加 `ui-hit-hasstate` 类：抑制 replica.css 里**纯热区**的 `:hover`/`:active` 蓝底。
         理由与 M35b 同款 —— krkr 侧拖动/悬停滑块时画的是**手柄 hover 图**，热区本身
         **什么都不画**；不抑制的话 HTML 会多出一整块 382×59 的蓝底（两端观感分叉）。
         该类只影响叠色，不影响命中；也不影响 ⑰ 的纯热区主语（那件是 `cfg.tab1_hit`）。 */
    var slId = (e.slider === null || e.slider === undefined) ? '' : String(e.slider);
    if (slId !== '') {
      d.setAttribute('data-ui-slider-hit', slId);
      d.classList.add('ui-hit-hasstate');
      d.classList.add('ui-slider-hit');
      d.setAttribute('tabindex', '0');            // 键盘可达：聚焦后左右箭头 ±step（可选增强）
      d.style.touchAction = 'none';               // 触摸拖动时不滚动页面
      d.title = '拖动以调整「' + slId + '」（键盘左右箭头 ±step）';
      d.addEventListener('mouseenter', function () {
        if (sliderDragId === slId) return;        // 拖动中：悬停态由拖动维持（引擎同）
        sliderHoverId = slId;
        sliderSyncDom(slId);
      });
      d.addEventListener('mouseleave', function () {
        if (sliderDragId === slId) return;        // ⚠️ 拖动期间移出**不清**悬停（拖动语义）
        if (sliderHoverId === slId) { sliderHoverId = ''; sliderSyncDom(slId); }
      });
      d.addEventListener('pointerdown', function (ev) {
        if (ev && ev.button !== undefined && ev.button !== 0) return;   // 只认左键
        ev.preventDefault();
        try { d.setPointerCapture(ev.pointerId); } catch (e0) {}
        sliderDragId = slId;                      // ① 进入拖动（同一时刻至多一个）
        sliderHoverId = slId;                     // ② 立刻进入活动外观
        sliderDragTo(canvasPoint(ev).x);          // ③ 按 x 立即置值（clamp + step + 写仓）
        bindDragDoc();                            // ④ 指针兜底（移出热区也不中断）
      });
      d.addEventListener('pointermove', function (ev) {
        if (sliderDragId !== slId) {
          /* 未拖动：指针在本热区内 ⇒ 悬停态（引擎每帧按指针重算，这边由事件重算） */
          if (sliderHoverId !== slId) { sliderHoverId = slId; sliderSyncDom(slId); }
          return;
        }
        sliderDragTo(canvasPoint(ev).x);
      });
      /* 抬起 / 取消（document 级兜底见 bindDragDoc，两条路径都会走 sliderDragEnd） */
      d.addEventListener('pointerup', function () { dragDocUnbind(); sliderDragEnd(); });
      d.addEventListener('pointercancel', function () { dragDocUnbind(); sliderDragEnd(); });
    }

    d.addEventListener('click', function (ev) {
      ev.stopPropagation();
      /* ★ M35：这里的 .ui-hit-pressed 是**点击瞬闪**（110ms 的一次性反馈，CSS 背景色，
         见 replica.css），与上面的 `state_assets.pressed` **按下态贴图是两套东西**：
           · .ui-hit-pressed  —— 点击那一瞬的反馈，"点到了"的触觉，110ms 后自动消失；
           · state_assets.pressed —— 按住期间持续显示的状态图，抬起/移出才复位。
         两者语义不重叠、可同时存在（按下时贴图变按下态，点击时再叠一层瞬闪）。
         命名相近容易混，故在此写明；改任意一侧请勿把另一侧一起改错。 */
      d.classList.add('ui-hit-pressed');
      setTimeout(function () { d.classList.remove('ui-hit-pressed'); }, 110);
      doAction(e.action, e);
    });
    return d;
  }

  /* ---------------------------------------------------------------- list */
  /* ★ M1（2026-09-24 · ISSUE-20260924-08）：list 的**每页栏数**与**列数** ——
     与 krkr 侧 `ui_widget.tjs` 的 `uiWidgetListPage` / `uiWidgetListCols` **逐字同公式**
     （改一处须改两处）。原先 HTML 的 perPage 是 `cols × rowsCap`，而引擎是
     「v: min(标签数, max_rows)」「h: max_cols×max_rows（两者都有时）」⇒ 在
     `max_rows > 标签数` 的列表上两端分叉（如 `ch.choices` 3 标签 / max_rows 6：
     引擎 3、HTML 6）。本轮统一到引擎口径。 */
  function listCols(e) {
    if (e.orientation !== 'h') return 1;
    var n = (e.labels || []).length;
    var mc = Number(e.max_cols) || 0;
    if (mc > 0) return mc;
    return n > 0 ? n : 1;
  }
  function listPerPage(e) {
    var n = (e.labels || []).length;
    var per = n;
    if (e.orientation === 'h') {
      var mc = Number(e.max_cols) || 0, mr = Number(e.max_rows) || 0;
      if (mc > 0 && mr > 0) per = mc * mr;
      else if (mc > 0 && per > mc) per = mc;
    } else {
      var mr2 = Number(e.max_rows) || 0;
      if (mr2 > 0 && per > mr2) per = mr2;
    }
    if (e.scroll && Number(e.scroll.page_size) > 0 && per > Number(e.scroll.page_size))
      per = Number(e.scroll.page_size);
    if (per <= 0) per = n;
    return per;
  }

  function buildList(e, orderIdx) {
    var box = resolveBox(e);
    var container = mk('div', 'ui-el ui-list');
    applyBox(container, box);
    container.style.zIndex = zIndex(e, orderIdx);
    container.setAttribute('data-ui-kind', 'list');

    var labels = e.labels || [];
    var actions = e.actions || [];
    var orient = e.orientation === 'h' ? 'h' : 'v';
    var gap = Number(e.gap || 0);
    var cols = listCols(e);
    var perPage = Math.max(1, listPerPage(e));

    var total = labels.length;
    var pages = Math.max(1, Math.ceil(total / perPage));
    var page = listPageOf(e.id);
    if (page < 0) page = 0;
    if (page > pages - 1) page = pages - 1;
    container.__page = page;
    var start = page * perPage;
    var slice = labels.slice(start, start + perPage);

    /* 纵向：y 由 stack_bottom 反推（选择肢由下往上堆） */
    var baseX = 0, baseY = 0;
    var itemW = (e.item_w !== null && e.item_w !== undefined) ? Number(e.item_w) : box.w;
    var itemH = (e.item_h !== null && e.item_h !== undefined) ? Number(e.item_h) : 0;
    if (orient === 'v') {
      if (e.stack_bottom !== null && e.stack_bottom !== undefined) {
        var rowsUsed = Math.max(1, Math.ceil(slice.length / cols));
        var totalH = rowsUsed * itemH + (rowsUsed - 1) * gap;
        baseY = Number(e.stack_bottom) - totalH;
      }
    }

    var listFont = e.font || {};
    var fSize = fontSize(listFont, 'body');      // krkr uiThemeElementFontSize 缺省用 body
    /* ★ M15：列表标签按 krkr 定位（krkr：ty = item.y + floor((item.h - lineH)/2)，
       lineH = floor(size × 行距)，见 ui_widget.tjs:338/356）。.ui-list-item 是 flex 居中
       ⇒ 等价于该公式；再上移半行距抵消 CSS leading。 */
    var fLh = fSize * lineSpacing(e, e.line_spacing_role || 'body');
    var fHalfLeading = (fLh - fSize) / 2;
    var hl = e.highlight || null;
    var hlColor = hl ? (col(hl.color) || null) : null;
    var hlOpa = hl ? opa(hl.opacity) : 0;
    var hlFontColor = col(e.highlight_font_color);
    var baseFontColor = col(listFont.color) || (col('@palette.text_menu') || '#e8e8f0');
    /* ★ M46：本 list 是否带**逐项态图**（`item_frame.state_assets`）—— 决定悬停反馈用「图换态」
       还是「高亮块 + 文字变色」（两者不得同时生效，见下方两处 perItemStates 守卫）。 */
    var perItemStates = !!(e.item_frame && e.item_frame.state_assets);

    /* ★★ M06（2026-09-24 · ISSUE-20260924-06_回想屏重排 · 冻结书 §2）：**逐块按钮 `item_buttons`**
       ＋ **逐块文案区 `item_text`**（与 krkr 侧 ui_widget.tjs 的 uiWidgetDrawList /
       uiWidgetItemButtonProblems / uiWidgetItemButtonAt **逐条同口径**，改一处须改两处）：
         · `item_buttons[]`：块内局部坐标（相对项矩形左上）+ `asset`/`nine`/`state_assets`
           + `action`（串内 `%row%` = **全局项序号**）+ 可选 `label`/`font`/`align`；
         · `item_text`：块内局部矩形，给了才走「折行 + 内缩 + 行距」新口径；
           **没给就必须与旧版逐字相同**（单行、无内缩、整项垂直居中）。
       守卫（与 krkr 同一套判据，**不静默**）：结构非法 / 缺 key / key 重复 / 矩形零面积或出块 /
       `action` 为空 / 既无 asset 又无 state_assets ⇒ 该按钮**不画、不可点**，并打
       `★M06ITEMBTN-REJECT★ <listId>[<key>] <理由>`（同一出口见 itemBtnReject）。 */
    /* ★ M06 一审 A3（2026-09-24）：**容器级结构非法**也必须与引擎同口径 REJECT ——
       原先对 `item_buttons` 非数组 / `item_text` 非对象**静默当作未声明**，而引擎
       （uiWidgetItemButtonProblems / uiWidgetItemText）会显式拒绝。判据与判词**逐字同引擎**：
         · `item_buttons` 给了（非 void/null）但不是数组 ⇒ key=`(item_buttons)`、
           reason=`item_buttons 不是数组`（对应 TJS 的 `typeof != "Object"` 或 `count === void`）；
         · `item_text` 给了但不是对象 ⇒ key=`item_text`、reason=`item_text 不是对象`。
       **仅当字段存在但类型不对**才报；**缺字段仍视为未声明**（不报、走旧路径）。
       （`uiWidgetItemButtons` 对 void/null 直接返回 null 且不报；`uiWidgetItemText` 同理。） */
    var itemBtns = null, itemText = null;
    if (e.item_buttons !== null && e.item_buttons !== undefined) {
      if (typeof e.item_buttons === 'object' && typeof e.item_buttons.length === 'number')
        itemBtns = e.item_buttons;
      else
        itemBtnReject(e.id, '(item_buttons)', 'item_buttons 不是数组');
    }
    if (e.item_text !== null && e.item_text !== undefined) {
      if (typeof e.item_text === 'object') itemText = e.item_text;
      else itemBtnReject(e.id, 'item_text', 'item_text 不是对象');
    }
    var btnBad = {};
    /* 逐块按钮的**系统键**（守卫台账的查找键；绘制与命中共用）：
       有非空 key ⇒ 用它；缺 key / key 为空串 ⇒ `#<下标>`。**不得用空串当键** ——
       JS 对象里 `btnBad['']` 与「有非空 key」的按钮撞不到一起，会让「缺 key」的那一条
       照样被画、照样可点，而它已被守卫判为非法（首轮实测：判词打了、按钮还在）。
       与 krkr 侧 uiWidgetItemBtnSysKey **同口径**。 */
    function btnSysKey(b, i) {
      var k = (b && b.key !== null && b.key !== undefined) ? String(b.key) : '';
      return (k === '') ? ('#' + i) : k;
    }
    if (itemBtns) {
      var itemSizeW = (orient === 'h') ? itemW : box.w;
      var itemSizeH = itemH;
      var seenKeys = {};
      for (var _b = 0; _b < itemBtns.length; _b++) {
        var _bb = itemBtns[_b];
        var _bk = (_bb && _bb.key !== null && _bb.key !== undefined) ? String(_bb.key) : '';
        var _lbl = btnSysKey(_bb, _b);
        if (!_bb || typeof _bb !== 'object') { btnBad[_lbl] = true; itemBtnReject(e.id, _lbl, '第 ' + _b + ' 项不是对象'); continue; }
        if (_bk === '') { btnBad[_lbl] = true; itemBtnReject(e.id, _lbl, '第 ' + _b + ' 项缺 key'); continue; }
        if (seenKeys[_bk]) { btnBad[_bk] = true; itemBtnReject(e.id, _bk, 'key 重复'); continue; }
        seenKeys[_bk] = true;
        var _bw = Number(_bb.w) || 0, _bh = Number(_bb.h) || 0;
        var _bx = Number(_bb.x) || 0, _by = Number(_bb.y) || 0;
        if (_bw <= 0 || _bh <= 0) { btnBad[_bk] = true; itemBtnReject(e.id, _bk, '矩形零/负面积（' + _bw + '×' + _bh + '）'); continue; }
        if (_bx < 0 || _by < 0 || _bx + _bw > itemSizeW || _by + _bh > itemSizeH) {
          btnBad[_bk] = true;
          itemBtnReject(e.id, _bk, '矩形出块（局部 ' + _bx + ',' + _by + ' ' + _bw + '×' + _bh
            + ' 不在 ' + itemSizeW + '×' + itemSizeH + ' 内）');
          continue;
        }
        var _bact = (_bb.action === null || _bb.action === undefined) ? '' : String(_bb.action);
        if (_bact === '') { btnBad[_bk] = true; itemBtnReject(e.id, _bk, 'action 为空'); continue; }
        if (!_bb.asset && !_bb.state_assets) { btnBad[_bk] = true; itemBtnReject(e.id, _bk, '既无 asset 也无 state_assets'); continue; }
      }
    }
    if (itemText) {
      var _tw = Number(itemText.w) || 0, _th = Number(itemText.h) || 0;
      var _tx = Number(itemText.x) || 0, _ty = Number(itemText.y) || 0;
      var _iw = (orient === 'h') ? itemW : box.w;
      if (_tw <= 0 || _th <= 0) { itemText = null; itemBtnReject(e.id, 'item_text', '文本区零/负面积（' + _tw + '×' + _th + '）'); }
      else if (_tx < 0 || _ty < 0 || _tx + _tw > _iw || _ty + _th > itemH) {
        itemText = null;
        itemBtnReject(e.id, 'item_text', '文本区出块（局部 ' + _tx + ',' + _ty + ' ' + _tw + '×' + _th
          + ' 不在 ' + _iw + '×' + itemH + ' 内）');
      }
    }

    slice.forEach(function (label, k) {
      var row = Math.floor(k / cols);
      var c = k % cols;
      var it = mk('div', 'ui-list-item');
      it.style.left = px(baseX + c * (itemW + gap));
      it.style.top = px(baseY + row * (itemH + gap));
      it.style.width = px(itemW);
      it.style.height = px(itemH);
      it.setAttribute('data-ui-interactive', '1');
      it.setAttribute('data-ui-kind', 'list-item');
      var globalIdx = start + k;
      it.setAttribute('data-ui-index', String(globalIdx));
      var act = actions[globalIdx] !== undefined ? actions[globalIdx] : null;
      if (act) it.setAttribute('data-ui-action', act);

      /* 每项背景框（九宫格）—— ★ M46：带 `item_frame.state_assets` 时**逐项换图**（悬停/按下） */
      if (e.item_frame) {
        var fr = mk('div', 'ui-list-item-frame');
        var nine = e.item_frame.nine;
        var fsa = e.item_frame.state_assets || null;
        /* ★ M46（2026-09-23）：回落规则与 krkr 的 uiWidgetItemFrameAsset **完全一致**
           （pressed > hover > normal > asset）；换图（不是叠色），选择支条整条美术换一张。 */
        var setFrame = function (state) {
          var url = e.item_frame.asset;
          if (fsa) {
            if (state === 'pressed') url = fsa.pressed || fsa.hover || fsa.normal || url;
            else if (state === 'hover') url = fsa.hover || fsa.normal || url;
            else url = fsa.normal || url;
          }
          var u = 'url("' + assetUrl(url) + '")';
          if (nine && !isZeroNine(nine)) fr.style.borderImageSource = u;
          else fr.style.backgroundImage = u;
        };
        if (nine && !isZeroNine(nine)) {
          fr.style.borderWidth = [nine.t, nine.r, nine.b, nine.l].map(px).join(' ');
          fr.style.borderImageSlice = [nine.t, nine.r, nine.b, nine.l].join(' ') + ' fill';
          fr.style.borderImageRepeat = 'stretch';
        } else {
          /* 无 nine / 全零 nine（整图缩放语义）：background 整图拉伸，不走 border-image
             （border-width 全 0 时 border-image 不绘制任何像素，见 isZeroNine 注释）。 */
          fr.style.backgroundSize = '100% 100%';
          fr.style.backgroundRepeat = 'no-repeat';
        }
        setFrame('normal');
        var fo = opa(e.item_frame.opacity);
        if (fo < 1) fr.style.opacity = String(fo);
        it.appendChild(fr);
        if (fsa) {
          /* ★ M46：逐项三态（与 krkr 的 ctx.hoverIndex/pressIndex 同语义，规则表见本文件
             顶部的 §按下态台账 —— **改一处就要改两处**）：
               · 逐项自有 ownHover/ownPress，优先级 pressed > hover > normal；
               · 抬起用**全局 pressHolder 台账**兜底（在项外松开 / 拖出窗口 / 失焦都能复位），
                 与元素级 state_assets 走同一套机制，不是每项各写一遍。
               · ★ 两类**必须与元素级一致**的细节（一审 Major-1 打回后补）：
                 ① 只认**左键**（`ev.button !== 0` 直接返回）—— krkr 侧只认 mbLeft
                    （startup.tjs 的 onMouseDown 分支），否则右键点选项条会把该项**钉**在按下态；
                 ② 置按下态前先 `pressRelease()` —— 「同一时刻至多一个按下态」。
               · ★ 拖拽语义（一审 Major-2）：按住左键**移出本项**即取消按下态（规则 ③ 的逐项版）。
                 依据：规则表 ③ 写的是「指针移出**该元素**」，逐项语境下即「移出**该项**」——
                 故按下态**锚定在被按的那一项**上，不跟着鼠标飘（跟着飘等于把 hover 当 pressed）。
                 krkr 侧同一收口：按下时**锁存**项序号（`UIScrPressIndex`），指针移到别项即清
                 （见 ui_screens.tjs 的 uiScreenPressUpdate / uiScreenHoverUpdate）。 */
          var ownHover = false, ownPress = false;
          var applyItemState = function () {
            setFrame(ownPress ? 'pressed' : (ownHover ? 'hover' : 'normal'));
          };
          it.addEventListener('mouseenter', function () {
            ownHover = true;
            applyItemState();
          });
          it.addEventListener('mouseleave', function () {
            ownHover = false;                      /* 规则 ③：指针移出即取消按下态 */
            ownPress = false;
            if (pressHolder && pressHolder.el === it) pressHolder = null;
            applyItemState();
          });
          it.addEventListener('mousedown', function (ev) {
            if (ev && ev.button !== 0) return;     /* 见上 ①：与元素级 / krkr 的 mbLeft 一致 */
            pressRelease();                        /* 见上 ②：同一时刻至多一个按下态 */
            ownPress = true;
            applyItemState();
            pressHolder = { el: it, release: function () { ownPress = false; applyItemState(); } };
          });
          it.addEventListener('mouseup', function () {
            ownPress = false;
            if (pressHolder && pressHolder.el === it) pressHolder = null;
            applyItemState();
          });
          it.setAttribute('data-ui-item-states', '1');   /* 供自检/探针识别：本项有逐项态图 */
        }
      }

      /* 高亮块 */
      if (hl) {
        var hld = mk('div', 'ui-list-item-hl');
        hld.style.background = hlColor || 'transparent';
        if (hlOpa < 1) hld.style.opacity = String(hlOpa);
        it.appendChild(hld);
      }

      /* 标签 —— ★ M06：给了 `item_text` 就走「折行 + 内缩 + 行距」新口径
         （与 `buildText` **同一条路径**：line-height 半行距补偿 + white-space/word-break
         + `-webkit-line-clamp` 截断，故禁则/换行/截断口径与既有文本元素一致；
         ★ 行首/行尾禁则由 CSS 行断规则承担 —— krkr 侧 uiThemeWrap 另有显式禁则表，
         两端在**本工程语料**下实测断行位置一致，见证据图）；
         **没给 `item_text` 就必须与旧版逐字相同**（单行、无内缩、整项垂直居中）。 */
      var lab = mk('div', 'ui-list-item-label');
      var labInner = null;
      if (itemText) {
        var tSize = fontSize(itemText.font || listFont, itemText.font_role || e.font_role || 'body');
        var tLs = (itemText.line_spacing !== null && itemText.line_spacing !== undefined)
          ? Number(itemText.line_spacing) : lineSpacing(e, e.line_spacing_role || 'body');
        var tLh = tSize * tLs;
        var tHalf = (tLh - tSize) / 2;
        lab.classList.add('ui-list-item-text');
        lab.style.position = 'absolute';
        lab.style.left = px(Number(itemText.x) || 0);
        lab.style.top = px(Number(itemText.y) || 0);
        lab.style.width = px(Number(itemText.w) || 0);
        lab.style.height = px(Number(itemText.h) || 0);
        lab.style.padding = '0';
        lab.style.transform = 'none';
        lab.style.overflow = 'hidden';
        /* ★ M08 收尾修复（2026-09-24，ISSUE-20260924-08 · 用户截图「BGM 行文字骑在条带上缘」）：
           本路径原先**没实现 `item_text.valign`** —— `lab.style.top` 恒 = itemText.y（顶对齐），
           而引擎端（krkr ui_theme.tjs `uiThemeLayoutText`：middle ⇒ y + floor((h-blockH)/2)）
           是真居中 ⇒ 28_music（文字区 y0..59 全项高、胶囊可见体 y10..47）HTML 文字带 y≈0..22
           骑出条上缘 10px，引擎端无此问题（引擎截图另证）。修法与引擎同口径：
           middle/bottom 用 flex column 垂直居中/贴底（浏览器自算折行 blockH，与
           floor((h-blockH)/2) 在单行下仅 ≤0.5px 舍入差；折行场景两端本就各有禁则实现）；
           top（含缺省）保持原行为逐字不变 —— 26_backlog（valign=top）零变化。 */
        var tValign = itemText.valign || 'top';             /* 与 krkr uiWidgetItemText 同缺省 */
        if (tValign === 'middle' || tValign === 'bottom') {
          lab.style.display = 'flex';
          lab.style.flexDirection = 'column';
          lab.style.justifyContent = (tValign === 'middle') ? 'center' : 'flex-end';
        }
        lab.style.color = baseFontColor;                    /* selectListItem 改这里的颜色 */
        labInner = mk('div', 'ui-list-item-text-inner');
        labInner.style.display = 'block';
        labInner.style.width = '100%';
        labInner.style.fontSize = px(tSize);
        labInner.style.lineHeight = px(tLh);
        labInner.style.fontWeight = (itemText.font || listFont).bold ? 'bold' : 'normal';
        var tFaces = (itemText.font || listFont).faces;
        if (tFaces && tFaces.length) labInner.style.fontFamily = fontChain(itemText.font || listFont);
        labInner.style.color = 'inherit';                   /* 颜色跟着外层（选中变色才生效） */
        labInner.style.textAlign = itemText.align || e.align || 'left';
        var tSh = textShadowAll(itemText.font || listFont);
        if (tSh) labInner.style.textShadow = tSh;
        var tWrap = (itemText.wrap === false) ? false : true;
        var tNL = typeof label === 'string' && label.indexOf('\n') >= 0;
        labInner.style.whiteSpace = tWrap ? (tNL ? 'pre-line' : 'normal') : (tNL ? 'pre-line' : 'nowrap');
        if (tWrap) labInner.style.wordBreak = 'break-word';
        if (tHalf) labInner.style.transform = 'translateY(' + px(-tHalf) + ')';
        var tMax = Number(itemText.max_lines) || 0;
        if (tWrap && tMax > 0) {
          labInner.style.display = '-webkit-box';
          labInner.style.webkitBoxOrient = 'vertical';
          labInner.style.webkitLineClamp = String(tMax);
          labInner.style.overflow = 'hidden';
        }
        labInner.textContent = String(label);
        lab.appendChild(labInner);
        it.appendChild(lab);
      } else {
        lab.style.fontSize = px(fSize);
        lab.style.lineHeight = px(fLh);
        if (fHalfLeading) lab.style.transform = 'translateY(' + px(-fHalfLeading) + ')';
        lab.style.fontWeight = listFont.bold ? 'bold' : 'normal';
        if (listFont.faces && listFont.faces.length) lab.style.fontFamily = fontChain(listFont);
        lab.style.color = baseFontColor;
        lab.style.textAlign = e.align || 'center';
        var sh = textShadowAll(listFont);   /* ★ M38：与 buildText 同一合成（描边 + 阴影） */
        if (sh) lab.style.textShadow = sh;
        lab.textContent = String(label);
        it.appendChild(lab);
      }

      /* ★ M06：**逐块按钮**（`item_buttons`）—— 渲染 + 逐按钮三态 + 逐按钮动作。
         · 几何**全部来自数据**（块内局部坐标），机制里不写死任何按钮几何；
         · `action` 里的 `%row%` 换成**全局项序号**（含分页偏移，= `globalIdx`）；
         · 按钮**吃掉整行命中**：mousedown / click 一律 stopPropagation，故整行 action
           与 `selectListItem` 都不会因点在按钮上而触发（与 krkr `uiScreenClick` 的
           「按钮优先」逐条同义）；
         · 逐按钮三态 = M46 逐项态那张规则表的**主语细化版**（①左键按下 ②抬起 ③移出该按钮
           ④换屏/重渲染 ⑤pressed > hover > normal），共用全局 `pressHolder` 台账。 */
      if (itemBtns) {
        itemBtns.forEach(function (b, bi) {
          var bk = btnSysKey(b, bi);                    /* 系统键：与校验/判词同一把键 */
          if (btnBad[bk]) return;                       /* 非法项：已打 REJECT，不画、不可点 */
          var bn = mk('div', 'ui-list-item-btn');
          bn.style.left = px(Number(b.x) || 0);
          bn.style.top = px(Number(b.y) || 0);
          bn.style.width = px(Number(b.w) || 0);
          bn.style.height = px(Number(b.h) || 0);
          bn.setAttribute('data-ui-kind', 'list-item-btn');
          bn.setAttribute('data-ui-item-btn', bk);
          bn.setAttribute('data-ui-item-btn-index', String(globalIdx));
          bn.setAttribute('data-ui-interactive', '1');
          /* 未替换 / 已替换两种串都挂上：`data-ui-action` 供探针（`?hover=bl.list~0~jump` 与
             真实点击）定位，`data-ui-item-action-raw` 保留数据原文便于对账。 */
          var bAct = (b.action === null || b.action === undefined) ? '' : String(b.action);
          bn.setAttribute('data-ui-item-action-raw', bAct);
          var bResolved = bAct.split('%row%').join(String(globalIdx));
          if (bResolved) bn.setAttribute('data-ui-action', bResolved);

          var bNine = (b.nine && !isZeroNine(b.nine)) ? b.nine : null;
          var bImg = mk('div', bNine ? 'ui-nine' : 'ui-stateimage');
          if (bNine) {
            bImg.style.borderWidth = [bNine.t, bNine.r, bNine.b, bNine.l].map(px).join(' ');
            bImg.style.borderImageSlice = [bNine.t, bNine.r, bNine.b, bNine.l].join(' ') + ' fill';
            bImg.style.borderImageRepeat = 'stretch';
          } else {
            bImg.style.backgroundSize = '100% 100%';
            bImg.style.backgroundRepeat = 'no-repeat';
          }
          bImg.setAttribute('data-ui-stateimage', bNine ? 'nine' : '1');
          /* 回落规则与 krkr 的 uiWidgetItemButtonAsset **完全一致**
             （pressed > hover > normal > asset，缺键逐级回落） */
          var bsa = b.state_assets || null;
          var setBtnAsset = function (state) {
            var url = b.asset;
            if (bsa) {
              if (state === 'pressed') url = bsa.pressed || bsa.hover || bsa.normal || url;
              else if (state === 'hover') url = bsa.hover || bsa.normal || url;
              else url = bsa.normal || url;
            }
            if (!url) { bImg.style.backgroundImage = 'none'; bImg.style.borderImageSource = 'none'; return; }
            var u = 'url("' + assetUrl(url) + '")';
            if (bNine) bImg.style.borderImageSource = u;
            else bImg.style.backgroundImage = u;
          };
          setBtnAsset('normal');
          if (b.opacity !== null && b.opacity !== undefined && opa(b.opacity) < 1)
            bn.style.opacity = String(opa(b.opacity));
          bn.appendChild(bImg);
          /* 可选文字（**引擎绘制** → HTML 同口径：单行、居中、valign=middle）。
             ★ M06 一审 Major 打回（2026-09-24）：原来只设 fontSize/justifyContent，
             **漏了半行距补偿** —— `.ui-list-item-btn-label` 是 flex 居中（等价 krkr 的
             floor((h-lineH)/2)），但 CSS 行框比字号高出一整个行距，字形因此整体下沉
             halfLeading。实测 4 块「跳转」墨迹中心恒 +6.5px（其中 4px = (20×1.4−20)/2 即此，
             余 ~2.5px 是本工程既有的「TJS/浏览器墨迹内边距差」，见 buildText 注释）。
             修法照同文件既有 `buildHit` 的 hit.label 口径（**三行**）：设 lineHeight = size×行距，
             再 translateY(-(lineH-size)/2) 抵消 CSS leading。**只改 HTML 侧**，不动引擎
             `uiWidgetDrawText`（全 18 屏共用路径，须单独立项）。
             ★ ISSUE-20260927-03（模块 I · 用户裁决「统一两端按钮标签墨迹口径」）：在既有
             半行距补偿之上**再 +3px** —— 补偿后仍余約 3px 的「TJS/浏览器墨迹放置差」
             （本端实测：标签墨迹中线比胶囊可见体中线**高 3.0px**，四块一致；引擎端高 **6.0px**
             ⇒ 两端恒差 3.0px）。故本端 `translateY(3 - blHL)`、引擎端 `br.y + 6`
             （`krkr\game\ui_widget.tjs::uiWidgetDrawList`）是**同一条算式的两端解**
             （引擎 6 = 本端 3 ＋ 两端差 3）⇒ 两端墨迹中线都落在胶囊可见体中线。**改一处须改两处。**
             ⚠️ 只动标签落点：按钮几何 / 命中矩形 / 三态素材 / action / labels 一律未动。
             同款落点：`buildHit` 的 `hit.label`（同为按钮标签，一并 +3）。 */
          if (b.label !== null && b.label !== undefined && String(b.label) !== '') {
            var bf = b.font || listFont;
            var blSize = fontSize(bf, 'body');
            var blLh = blSize * lineSpacing(b, 'body');
            var bl = mk('div', 'ui-list-item-btn-label');
            bl.style.fontSize = px(blSize);
            bl.style.lineHeight = px(blLh);
            var blHL = (blLh - blSize) / 2;
            bl.style.transform = 'translateY(' + px(3 - blHL) + ')';
            bl.style.fontWeight = bf.bold ? 'bold' : 'normal';
            if (bf.faces && bf.faces.length) bl.style.fontFamily = fontChain(bf);
            bl.style.color = col(bf.color) || baseFontColor;
            bl.style.justifyContent = ((b.align || 'center') === 'left') ? 'flex-start'
              : (((b.align || 'center') === 'right') ? 'flex-end' : 'center');
            var bSh = textShadowAll(bf);
            if (bSh) bl.style.textShadow = bSh;
            bl.textContent = String(b.label);
            bn.appendChild(bl);
          }
          it.appendChild(bn);

          var bOwnHover = false, bOwnPress = false;
          var applyBtnState = function () {
            setBtnAsset(bOwnPress ? 'pressed' : (bOwnHover ? 'hover' : 'normal'));
          };
          bn.addEventListener('mouseenter', function () { bOwnHover = true; applyBtnState(); });
          bn.addEventListener('mouseleave', function () {
            bOwnHover = false; bOwnPress = false;              /* 规则 ③：移出该按钮即取消按下态 */
            if (pressHolder && pressHolder.el === bn) pressHolder = null;
            applyBtnState();
          });
          bn.addEventListener('mousedown', function (ev) {
            ev.stopPropagation();                              /* 按钮吃掉整行（不触发整行按下态） */
            if (ev && ev.button !== 0) return;                 /* 只认左键（与 krkr mbLeft 一致） */
            pressRelease();                                    /* 同一时刻至多一个按下态 */
            bOwnPress = true;
            applyBtnState();
            pressHolder = { el: bn, release: function () { bOwnPress = false; applyBtnState(); } };
          });
          bn.addEventListener('mouseup', function (ev) {
            ev.stopPropagation();
            bOwnPress = false;
            if (pressHolder && pressHolder.el === bn) pressHolder = null;
            applyBtnState();
          });
          bn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            if (state.backlog) {
              state.backlog.lastBtn = { list: e.id, row: globalIdx, key: bk, action: bResolved };
            }
            doAction(bResolved, e, globalIdx);
          });
        });
      }

      /* 悬停 / 选中反馈：高亮块 + 文字色
         ★ M46：**带逐项态图**（`item_frame.state_assets`）的 list **不再**叠这套悬停反馈 ——
         悬停反馈由图换态承担（`_over` 图）。理由：krkr 侧 `uiWidgetDrawList` 的高亮块
         **只跟 focus（选中项）走、不跟悬停走**，而这两条 HTML-only 的悬停反馈
         （文字变色 + CSS `:hover > hl`）会在换图之上再叠一层 ⇒ 两端观感不一致。
         M45f 当初给 list 加这套反馈，是因为那时**逐项态图不存在**（本轮已补上，见 M46 注释）。 */
      if (hlFontColor && !perItemStates) {
        it.addEventListener('mouseenter', function () { lab.style.color = hlFontColor; });
        it.addEventListener('mouseleave', function () {
          lab.style.color = (it.classList.contains('ui-selected') && hlFontColor) ? hlFontColor : baseFontColor;
        });
      }
      it.addEventListener('click', function (ev) {
        ev.stopPropagation();
        selectListItem(it, lab, hlFontColor, baseFontColor);
        doAction(act, e, globalIdx);
      });

      container.appendChild(it);
    });

      /* ★★ M1（ISSUE-20260924-08 · 鉴赏模式）：**栏位内差分翻页 `item_variants`**
         （与 krkr 侧 ui_widget.tjs 的 uiWidgetDrawListVariants / uiWidgetItemVariantButtonAt
         **逐条同口径**，改一处须改两处）：
           · `frames[row]` 按**全局项序号**索引（含分页偏移）；空数组/越界 = 该栏留空（合法）；
           · 画：当前差分的缩略图（画进 `thumb` 区，缺省 = 整项矩形）+ 左右子按钮 + `n/N` 文本；
           · 命中：`item_buttons`（声明序）→ `prev` → `next` → 整行（按钮 stopPropagation）；
           · 边界 = **clamp**：到第 1/N 张时按钮照常画/照常点/照常派发，序号夹在 [0,N-1]；
           · 守卫：容器级非法 ⇒ 逐条 REJECT 且**整段不画**；逐栏非法 ⇒ 该栏不画并 REJECT。 */
      /* ⚠️ 容器级校验**必须无条件跑**（只要字段存在）—— 包括「字段存在但不是对象」这种
         `variantsOf()` 直接返回 null 的形态；否则那一条永远不报（实测踩过：
         `item_variants:'oops'` 时整段被 `if(vspec)` 挡掉，判词一条都不出，
         而引擎侧 `uiWidgetDrawList` 是「先查 has 再查 problems」，会如实报出 ⇒ 两端分叉）。 */
      if (e.item_variants !== null && e.item_variants !== undefined) {
        var vspec = variantsOf(e);
        var vBad = {};
        var vProbs = variantProblems(e, itemW, itemH);
        vProbs.forEach(function (p) { vBad[String(p.key)] = true; variantReject(e.id, p.key, p.reason); });
        if (vspec && vProbs.length === 0) {
          var vIdxMap = state.varIdx[e.id] || null;
          /* 块内局部矩形 → 容器内矩形（与 list-item 同一套折行公式：c = i % cols、row = floor(i/cols)） */
          var vPartRect = function (idxLocal, part) {
            var ix = baseX + (idxLocal % cols) * (itemW + gap);
            var iy = baseY + Math.floor(idxLocal / cols) * (itemH + gap);
            var sp = null;
            if (part === 'thumb') sp = (vspec.thumb && typeof vspec.thumb === 'object')
              ? vspec.thumb : { x: 0, y: 0, w: itemW, h: itemH };
            else sp = vspec[part];
            if (!sp || typeof sp !== 'object') return null;
            return { x: ix + (Number(sp.x) || 0), y: iy + (Number(sp.y) || 0),
                     w: Number(sp.w) || 0, h: Number(sp.h) || 0 };
          };
          for (var _vi = 0; _vi < slice.length; _vi++) {
            var vRow = start + _vi;
            var vrp = variantRowProblem(e, vRow);
            if (vrp !== '') { variantReject(e.id, 'frames[' + vRow + ']', vrp); continue; }
            var vFr = variantRow(e, vRow);
            if (!vFr || vFr.length === 0) continue;              /* 留空（合法） */
            var vN = vFr.length;
            var vCur = 0;
            if (vIdxMap) { var _c = vIdxMap[String(vRow)]; if (_c !== null && _c !== undefined) vCur = Number(_c) || 0; }
            if (vCur < 0) vCur = 0;
            if (vCur >= vN) vCur = vN - 1;
            /* ① 缩略图（当前差分） */
            var vThumbR = vPartRect(_vi, 'thumb');
            if (vThumbR) {
              var vTh = mk('div', 'ui-list-item-var-thumb');
              vTh.style.left = px(vThumbR.x);
              vTh.style.top = px(vThumbR.y);
              vTh.style.width = px(vThumbR.w);
              vTh.style.height = px(vThumbR.h);
              vTh.style.backgroundImage = 'url("' + assetUrl(String(vFr[vCur])) + '")';
              vTh.style.backgroundSize = '100% 100%';
              vTh.style.backgroundRepeat = 'no-repeat';
              vTh.setAttribute('data-ui-kind', 'list-item-var-thumb');
              vTh.setAttribute('data-ui-var-index', String(vRow));
              vTh.setAttribute('data-ui-var-asset', String(vFr[vCur]));
              container.appendChild(vTh);
            }
            /* ② 左右差分按钮（逐按钮三态，与 M06 逐块按钮共用 pressHolder 台账） */
            ['prev', 'next'].forEach(function (which) {
              var sp = vspec[which];
              if (!sp || typeof sp !== 'object') return;
              if (vBad[variantBtnKey(sp, which)]) return;          /* 非法件：已 REJECT，不画 */
              var br = vPartRect(_vi, which);
              if (!br) return;
              var vk = String(sp.key);
              var vn = mk('div', 'ui-list-item-var-btn');
              vn.style.left = px(br.x);
              vn.style.top = px(br.y);
              vn.style.width = px(br.w);
              vn.style.height = px(br.h);
              vn.setAttribute('data-ui-kind', 'list-item-var-btn');
              vn.setAttribute('data-ui-var-btn', vk);
              vn.setAttribute('data-ui-var-which', which);
              vn.setAttribute('data-ui-var-index', String(vRow));
              vn.setAttribute('data-ui-interactive', '1');
              var vAct = (sp.action === null || sp.action === undefined) ? '' : String(sp.action);
              vn.setAttribute('data-ui-item-action-raw', vAct);
              var vResolved = vAct.split('%row%').join(String(vRow));
              if (vResolved) vn.setAttribute('data-ui-action', vResolved);
              var vNine = (sp.nine && !isZeroNine(sp.nine)) ? sp.nine : null;
              var vImg = mk('div', vNine ? 'ui-nine' : 'ui-stateimage');
              if (vNine) {
                vImg.style.borderWidth = [vNine.t, vNine.r, vNine.b, vNine.l].map(px).join(' ');
                vImg.style.borderImageSlice = [vNine.t, vNine.r, vNine.b, vNine.l].join(' ') + ' fill';
                vImg.style.borderImageRepeat = 'stretch';
              } else {
                vImg.style.backgroundSize = '100% 100%';
                vImg.style.backgroundRepeat = 'no-repeat';
              }
              var vsa = sp.state_assets || null;
              var vSet = function (state) {
                var url = sp.asset;
                if (vsa) {
                  if (state === 'pressed') url = vsa.pressed || vsa.hover || vsa.normal || url;
                  else if (state === 'hover') url = vsa.hover || vsa.normal || url;
                  else url = vsa.normal || url;
                }
                if (!url) { vImg.style.backgroundImage = 'none'; vImg.style.borderImageSource = 'none'; return; }
                var u = 'url("' + assetUrl(url) + '")';
                if (vNine) vImg.style.borderImageSource = u; else vImg.style.backgroundImage = u;
              };
              vSet('normal');
              vn.appendChild(vImg);
              container.appendChild(vn);
              var vOwnHover = false, vOwnPress = false;
              var vApply = function () { vSet(vOwnPress ? 'pressed' : (vOwnHover ? 'hover' : 'normal')); };
              vn.addEventListener('mouseenter', function () { vOwnHover = true; vApply(); });
              vn.addEventListener('mouseleave', function () {
                vOwnHover = false; vOwnPress = false;
                if (pressHolder && pressHolder.el === vn) pressHolder = null;
                vApply();
              });
              vn.addEventListener('mousedown', function (ev) {
                ev.stopPropagation();
                if (ev && ev.button !== 0) return;
                pressRelease();
                vOwnPress = true; vApply();
                pressHolder = { el: vn, release: function () { vOwnPress = false; vApply(); } };
              });
              vn.addEventListener('mouseup', function (ev) {
                ev.stopPropagation();
                vOwnPress = false;
                if (pressHolder && pressHolder.el === vn) pressHolder = null;
                vApply();
              });
              vn.addEventListener('click', function (ev) {
                ev.stopPropagation();
                doAction(vResolved, e, vRow);
              });
            });
            /* ③ `n/N` 文本（引擎绘制口径：单行居中 + 半行距补偿） */
            if (vspec.text && typeof vspec.text === 'object') {
              var vtR = vPartRect(_vi, 'text');
              if (vtR) {
                var vt = mk('div', 'ui-list-item-var-text');
                vt.style.left = px(vtR.x);
                vt.style.top = px(vtR.y);
                vt.style.width = px(vtR.w);
                vt.style.height = px(vtR.h);
                var vtf = vspec.text.font || listFont;
                var vtSize = fontSize(vtf, 'body');
                var vtLh = vtSize * lineSpacing(vspec.text, 'body');
                var vtHL = (vtLh - vtSize) / 2;
                vt.style.fontSize = px(vtSize);
                vt.style.lineHeight = px(vtLh);
                if (vtHL) vt.style.transform = 'translateY(' + px(-vtHL) + ')';
                vt.style.fontWeight = vtf.bold ? 'bold' : 'normal';
                if (vtf.faces && vtf.faces.length) vt.style.fontFamily = fontChain(vtf);
                vt.style.color = col(vtf.color) || baseFontColor;
                vt.style.justifyContent = ((vspec.text.align || 'center') === 'left') ? 'flex-start'
                  : (((vspec.text.align || 'center') === 'right') ? 'flex-end' : 'center');
                vt.setAttribute('data-ui-kind', 'list-item-var-text');
                vt.setAttribute('data-ui-var-index', String(vRow));
                vt.setAttribute('data-ui-var-text', (vCur + 1) + '/' + vN);
                vt.textContent = (vCur + 1) + '/' + vN;
                container.appendChild(vt);
              }
            }
          }
        }
      }


    /* 翻页（仅当超出容量时生成；属 HTML 侧补充 chrome，见 README）
       ★ M8 一审 R4（2026-09-24）：`scroll.pager === false` ⇒ **跳过本段** —— 屏数据自带页码控件
       （27_gallery / 28_music / 38_replay 的 `*_pg_*` 三件式）时，HTML 的自动 `ui-list-pager`
       是重复 chrome（krkr 端本无此物 ⇒ 两端不一致）。缺省 / true = 照旧生成（旧数据零变化）。 */
    if (pages > 1 && !(e.scroll && e.scroll.pager === false)) {
      var pager = mk('div', 'ui-list-pager');
      pager.style.fontSize = px(fontSize(null, 'small'));
      var prev = mk('span', 'pg-btn'); prev.textContent = '◀';
      var num = mk('span', 'pg-num'); num.textContent = (page + 1) + ' / ' + pages;
      var next = mk('span', 'pg-btn'); next.textContent = '▶';
      function go(delta) {
        var p = container.__page + delta;
        /* ★ M46（一审 Minor-3）：翻页会**重建整个 list DOM**（下面的 replaceChild）⇒ 旧项的
           ownHover/ownPress 与全局 pressHolder 句柄都会悬空，必须按规则 ④「重渲染即清」复位
           （krkr 侧每帧按指针重算，不存在这个形态）。 */
        pressRelease();
        if (p < 0) p = 0;
        if (p > pages - 1) p = pages - 1;
        if (p === container.__page) return;
        var visible = container.style.display;
        container.__page = p;
        state.listPage = state.listPage || {};
        state.listPage[e.id] = p;              /* ★ M1：页码表（与 krkr 的 UIScrPage 同义） */
        var def = state.refs[e.id] ? state.refs[e.id].def : e;
        var rebuilt = buildList(def, orderIdx);
        rebuilt.__page = p;
        rebuilt.style.display = visible;
        container.parentNode.replaceChild(rebuilt, container);
        if (e.id) state.refs[e.id] = { el: rebuilt, def: def };
      }
      prev.addEventListener('click', function (ev) { ev.stopPropagation(); go(-1); });
      next.addEventListener('click', function (ev) { ev.stopPropagation(); go(1); });
      pager.appendChild(prev); pager.appendChild(num); pager.appendChild(next);
      container.appendChild(pager);

      container.addEventListener('wheel', function (ev) {
        ev.preventDefault(); ev.stopPropagation();
        go(ev.deltaY > 0 ? 1 : -1);
      }, { passive: false });
    }

    container.addEventListener('click', function (ev) { ev.stopPropagation(); });
    return container;
  }

  function selectListItem(it, lab, hlFontColor, baseFontColor) {
    if (!it.parentNode) return;
    var sibs = it.parentNode.querySelectorAll('.ui-list-item');
    for (var i = 0; i < sibs.length; i++) {
      sibs[i].classList.remove('ui-selected');
      var l = sibs[i].querySelector('.ui-list-item-label');
      if (l) l.style.color = baseFontColor;
    }
    it.classList.add('ui-selected');
    if (hlFontColor) lab.style.color = hlFontColor;
  }

  /* ---------------------------------------------------------------- anim（独立粒子/循环动画层） */
  function buildAnim(e, orderIdx) {
    var box = resolveBox(e);
    var wrap = mk('div', 'ui-el ui-anim');
    applyBox(wrap, box);
    wrap.style.zIndex = zIndex(e, orderIdx);
    wrap.setAttribute('data-ui-kind', 'anim');
    var o = opa(e.opacity);
    if (o < 1) wrap.style.opacity = String(o);

    var frames = e.asset_frames || [];
    var count = Number(e.count || frames.length || 1);
    var period = Number(e.period_ms || 0);
    var i = 0;
    if (frames.length) {
      var im = mk('img', 'ui-image-img');
      im.draggable = false;
      im.src = assetUrl(frames[0]);
      wrap.appendChild(im);
      if (count > 1 && period > 0) {
        var step = period / count;
        var t = setInterval(function () {
          if (!im.parentNode) { clearInterval(t); return; }
          i = (i + 1) % count;
          im.src = assetUrl(frames[i % frames.length]);
        }, step);
      }
    }
    applyAnim(e, wrap.firstChild, e.anim);
    return wrap;
  }

  function buildUnknown(e, orderIdx) {
    var box = resolveBox(e);
    var d = mk('div', 'ui-el ui-missing');
    applyBox(d, box);
    d.style.zIndex = zIndex(e, orderIdx);
    d.appendChild(missingLabel('未知 kind: ' + e.kind + '（' + (e.id || '') + '）'));
    return d;
  }

  /* ---------------------------------------------------------------- anim.mode */
  function applyAnim(e, node, anim) {
    if (!anim || !node) return;
    var period = Number(anim.period_ms || 0);
    if (anim.mode === 'blink') {
      node.classList.add('ui-anim-blink');
      if (period > 0) node.style.animationDuration = px(period);
    } else if (anim.mode === 'scroll_x' || anim.mode === 'scroll_y') {
      node.classList.add(anim.mode === 'scroll_x' ? 'ui-anim-scroll-x' : 'ui-anim-scroll-y');
      if (period > 0) node.style.animationDuration = px(period);
    }
  }

  /* ==========================================================================
     6. 缺屏占位（M4/M5 的屏数据尚未产出时不报错、不崩）
     ========================================================================== */
  function renderNoScreen(id) {
    var cat = null;
    for (var i = 0; i < SCREEN_CATALOG.length; i++) if (SCREEN_CATALOG[i].id === id) cat = SCREEN_CATALOG[i];
    var box = mk('div', 'ui-noscreen');
    box.style.background = col('@palette.panel_fill') || '#141824';

    var inner = mk('div', 'ui-noscreen-box');
    var h = mk('h2');
    h.style.fontSize = px(fontSize({ size: SIZES.subtitle }, 'subtitle'));
    h.style.color = col('@palette.text_title') || '#f5e9c8';
    h.textContent = '该界面尚未产出布局数据';
    inner.appendChild(h);

    var p1 = mk('div');
    p1.style.fontSize = px(fontSize(null, 'body'));
    p1.style.color = col('@palette.text_primary') || '#ffffff';
    p1.textContent = '屏 id：' + id + (cat ? '　·　' + cat.title_cn : '') + (cat ? '　·　归属模块 ' + cat.owner : '');
    inner.appendChild(p1);

    var p2 = mk('div');
    p2.style.fontSize = px(fontSize(null, 'small'));
    p2.style.color = col('@palette.text_hint') || '#b8b8c8';
    p2.textContent = '本页渲染器为通用数据驱动：layout/screens/ 中该屏的 JSON 一经生成并重新生成 ui_layout.js，'
      + '本页即自动按同一份数据渲染，无需改动任何代码。';
    inner.appendChild(p2);

    if (cat && cat.required) {
      var pr = mk('div', 'req');
      pr.style.fontSize = px(fontSize(null, 'small'));
      pr.style.color = col('@palette.text_hint') || '#b8b8c8';
      pr.textContent = '该屏必需元素（layout/screens/_index.json）：';
      var ul = mk('ul');
      ul.style.fontSize = px(fontSize(null, 'small'));
      cat.required.forEach(function (r) {
        var li = mk('li');
        li.textContent = r;
        ul.appendChild(li);
      });
      pr.appendChild(ul);
      inner.appendChild(pr);
    }

    var back = mk('div', 'ui-hit');
    back.style.position = 'static';
    back.style.display = 'inline-flex';
    back.style.marginTop = px(fontSize(null, 'small'));
    back.style.padding = '6px 18px';
    back.style.borderColor = col('@palette.panel_edge') || '#5a6a8a';
    back.style.cursor = 'pointer';
    var bl = mk('span');
    bl.style.fontSize = px(fontSize(null, 'menu'));
    bl.style.color = col('@palette.text_menu') || '#e8e8f0';
    bl.textContent = '返回（Esc）';
    back.appendChild(bl);
    back.addEventListener('click', function (ev) { ev.stopPropagation(); goBack(); });
    inner.appendChild(back);

    box.appendChild(inner);
    (layerEl || document.getElementById('canvas')).appendChild(box);
  }

  /* ==========================================================================
     ★ M43（2026-09-23）· 7.0 流程图运行期状态（已读 / 当前节点 / 光标节点）
     ── 为什么需要它：用户裁定「彻底删除主页·章节选择 chapter 屏，只能从流程图选择剧情」，
        原 `chapter` 屏的「进入剧情」能力迁到流程图屏的**既有按钮** `fc.jump_hit`
        （动作 `flow_enter`）。该动作必须知道「要进入哪个节点」，故复刻端也要有节点状态。
     ── 与 krkr 侧 `ui_flow.tjs` 的 UIFlowVisited / UIFlowCurrent / UIFlowCursor **同口径**：
        · 节点数据来自 `window.UI_FLOW_DATA`（`复刻/flow_data.js`，由 工具/gen_flow_data.py
          从 资源组\剧本\spine.json 生成，与 krkr 侧 `ui_flow_data.tjs` 同一上游）；
        · 首次进入时「起始节点 = 无入边的节点」（krkr `uiFlowEnsureReady` 同规则），并标记已读；
        · 三态判定：已读 visited ＞ 可前往 available ＞ 未解锁 locked（同 krkr uiFlowStateOf）。
     ── 降级：未加载 flow_data.js 的页面（如 `_selftest_states.html`）不会崩 ——
        flowNodes() 返回空数组，flowEnter() 给「无可进入节点」提示。
     ========================================================================== */
  function flowData() {
    return (typeof window !== 'undefined' && window.UI_FLOW_DATA) ? window.UI_FLOW_DATA : null;
  }
  function flowNodes() {
    var d = flowData();
    return (d && d.nodes && d.nodes.length) ? d.nodes : [];
  }
  function flowNodeById(id) {
    var ns = flowNodes();
    for (var i = 0; i < ns.length; i++) if (String(ns[i].id) === String(id)) return ns[i];
    return null;
  }
  function flowInEdgesOf(id) {
    var d = flowData(), out = [];
    if (!d || !d.edges) return out;
    for (var i = 0; i < d.edges.length; i++) if (String(d.edges[i].to) === String(id)) out.push(d.edges[i]);
    return out;
  }
  function flowVisitedCount() {
    var n = 0, ns = flowNodes();
    for (var i = 0; i < ns.length; i++) if (state.flow.visited[String(ns[i].id)]) n++;
    return n;
  }
  /* 惰性初始化（同 krkr uiFlowEnsureReady）：只在有节点数据时动状态 */
  function flowEnsure() {
    if (state.flow.ready) return true;
    var ns = flowNodes();
    if (!ns.length) return false;                       // 无节点数据 → 保持未就绪，不写任何状态
    state.flow.ready = true;
    if (!state.flow.current || !flowNodeById(state.flow.current)) {
      var start = '';
      for (var i = 0; i < ns.length; i++) {
        if (!flowInEdgesOf(ns[i].id).length) { start = String(ns[i].id); break; }
      }
      if (!start) start = String(ns[0].id);
      state.flow.current = start;
      state.flow.visited[start] = true;
    }
    state.flow.cursor = state.flow.current;
    return true;
  }
  function flowStateOf(id) {
    var k = String(id);
    if (state.flow.visited[k]) return 'visited';
    var ins = flowInEdgesOf(k);
    if (!ins.length) return 'available';                // 根节点恒可前往（同 krkr）
    for (var i = 0; i < ins.length; i++) if (state.flow.visited[String(ins[i].from)]) return 'available';
    return 'locked';
  }
  function flowUnlockHint(id) {
    var ins = flowInEdgesOf(id);
    if (!ins.length) return '无条件（起始节点）';
    var parts = [];
    for (var i = 0; i < ins.length; i++) parts.push('先到达 ' + ins[i].from);
    return parts.join(' 或 ');
  }
  /* 光标移动（环状，同 krkr uiFlowFlowchartKey 的方向键分支）
     ★ M43 一审 Minor-4 澄清（**两端的 Enter 语义有意不同，勿当缺陷改**）：
       方向键：两端同口径（环状移动光标）。
       Enter ：krkr 走 `flow_node_<cursor>`（= uiFlowSelectNode「前往」，只标记已读、**不 push dialog**，
               因为 krkr 的流程图有节点热区可点）；复刻端**流程图屏没有节点几何**（PSB 复刻版已无
               `flow.*_box`），故 Enter 兼作「进入本章」（走 flowEnter）。两端各自自洽。 */
  function flowCursorMove(step) {
    if (!flowEnsure()) return;
    var ns = flowNodes(), cur = -1;
    for (var i = 0; i < ns.length; i++) if (String(ns[i].id) === state.flow.cursor) { cur = i; break; }
    if (cur < 0) cur = 0;
    cur += step;
    while (cur < 0) cur += ns.length;
    while (cur >= ns.length) cur -= ns.length;
    state.flow.cursor = String(ns[cur].id);
    toast('选中 ' + state.flow.cursor + '（Enter 进入本章）');
  }
  /* ★ 动作 `flow_enter` 的实现 —— 与 krkr `uiFlowEnterCurrent()` 逐条同口径：
       ① 无光标节点 → 明确提示，不静默；
       ② 未解锁 → **不进剧情**，只给解锁条件（同 uiFlowSelectNode 的 locked 分支）；
       ③ 已解锁 → 标记已读 + 置当前节点 → uiDialogReset() 的等价物（startDialog）
                   + 切到 dialog 屏。
⚠️ 复刻端**不做**「定位/滚动到该节点」：PSB 复刻版流程图屏里已无 `flow.*_box` 节点
         几何（krkr 侧同样取不到，`uiFlowScrollToCursor` 自然空转）⇒ 两端一致。
      ★ M43 一审 Minor-2（有意微差，勿当分叉改）：未解锁提示里**本端含幕名 `n.label`**，
         krkr 侧不含（`ui_flow.tjs` 的 locked 分支只给 `nid`+解锁条件）——krkr 那侧是为了
         适配 `flow.detail`（260×3 行的短提示区）不折行溢出。关键片段（`【未解锁】`+解锁条件）
         两端逐字一致，判据不受影响。 */
  function flowEnter() {
    if (!flowEnsure()) {
      toast('【无可进入节点】流程图节点数据未加载（flow_data.js 缺失）');
      return false;
    }
    var nid = String(state.flow.cursor || '');
    if (!nid) { toast('【无可进入节点】请先选中一个节点'); return false; }
    var n = flowNodeById(nid);
    if (!n) { toast('【无可进入节点】没有节点 ' + nid); return false; }
    var st = flowStateOf(nid);
    if (st === 'locked') {
      toast('【未解锁】' + nid + ' ' + n.label + '：' + flowUnlockHint(nid));
      return false;
    }
    var first = !state.flow.visited[nid];
    state.flow.visited[nid] = true;
    state.flow.current = nid;
    state.flow.cursor = nid;
    toast('进入 ' + nid + ' ' + n.label + (first ? '（首次进入）' : '（重入）')
          + '　已读 ' + flowVisitedCount() + ' / ' + flowNodes().length);
    renderScreen('dialog');              // = krkr 侧 uiScreenPush("dialog")（入栈，Esc 可弹回流程图）
    startDialog();                       // = krkr 侧 uiDialogReset()
    return true;
  }

  /* ==========================================================================
     7. 动作名表（layout/_schema.md §六）→ 行为
     ========================================================================== */
  var NAV = {
    game_start:      { screen: 'dialog', dialog: 'restart' },
    game_continue:   { screen: 'dialog', dialog: 'restart' },
    /* ★ M43：`open_chapter: { screen: 'chapter' }` **已删除**（`chapter` 屏整体移除，
       用户 2026-09-23 裁定）。进入剧情改由流程图屏的 `fc.jump_hit`（动作 `flow_enter`）。 */
    open_fragment:   { screen: 'fragment' },
    open_gallery:    { screen: 'gallery' },
    open_music:      { screen: 'music' },
    open_config:     { screen: 'config' },
    open_save:       { screen: 'save' },
    open_load:       { screen: 'load' },
    open_backlog:    { screen: 'backlog' },
    open_flowchart:  { screen: 'flowchart' },
    /* ★ M3（ISSUE-20260922-28）：`open_sysmenu` **不再是换屏动作** —— 系统菜单已改为
       「鼠标贴右端呼出的竖排快捷条」，本动作改为「展开竖条」（见 doAction 的 case）。
       ★ M45（2026-09-23，用户裁定）：`sysmenu` 屏**已整体废除** —— `20_sysmenu.json`
       已删除、`_index.json` 条目已移除、`SCREEN_CATALOG` 条目也已移除（NAV 里本就没有它）；
       快照归档 `_工作\M45_旧素材归档\`。`open_sysmenu` 动作保留（语义＝展开竖条）。 */
    open_title:      { screen: 'title' },
    quit_game:       { toast: '退出游戏（演示：不实际退出）' },
    close:           { back: true }
  };

  /* ★ M15：右键图标浮层（sysicons）的开关。语义与 krkr 侧 startup.tjs 的
     toggleSysIcons() **逐条对齐**：
       · 浮层已开 → 收起（uiScreenPop）；
       · 当前屏非 dialog → 不支持（浮层是「游戏内」的功能菜单）；
       · 否则 push 浮层。
     与「返回上一屏」的区别：收起浮层不是一次导航，不入屏历史。 */
  function toggleSysIcons() {
    if (state.screen === 'sysicons') { closeOverlay(); return true; }
    if (state.screen !== 'dialog') {
      toast('右键浮层仅在对话框内可用（当前屏 ' + (state.screen || '无') + '）');
      return false;
    }
    if (!SCREENS.sysicons) { toast('layout 缺 sysicons 屏，右键忽略'); return false; }
    renderScreen('sysicons');
    return true;
  }

  /* 收起浮层：**原地保留下层 DOM**（等同 krkr uiScreenPop —— 下层屏本就在栈上画着，
     不重建），只清空浮层容器与浮层元素表。这样对话框的打字机进度、已弹出的选择肢
     都不会因呼出一次浮层而丢失。 */
  function closeOverlay() {
    if (state.screen !== 'sysicons' && !state.underScreen) return;
    var under = state.underScreen;
    state.underScreen = null;
    state.refs = {};
    if (overlayEl) { overlayEl.innerHTML = ''; overlayEl.className = 'ui-layer'; }
    if (!under) { renderScreen('title', { noHistory: true }); return; }
    state.screen = under;
    state.baseScreenId = under;
    /* ★ M3：浮层收起 = 回到下层屏 ⇒ 按**新栈顶屏**的 flags_default 重置
       （与 krkr 侧 uiScreenPop 的 `uiScreenFlagsInitFor(栈顶屏)` 一致），
       并把该屏附加层的 flag 初值并回来、恢复 attachId，最后同步一次已渲染 DOM。
       注：下层 DOM 原地保留（不重建），故必须显式 applyFlagVisibility()，
       否则 flag 表与 DOM 的显隐会不一致（例如快捷条停在展开态）。 */
    initFlagsFor(under);
    var udefC = SCREENS[under];
    if (udefC && udefC.attach) {
      mergeAttachFlags(String(udefC.attach));
      state.attachId = String(udefC.attach);
    }
    applyFlagVisibility();
    /* ★ M47：下层 DOM 原地保留 ⇒ 设置仓也要补灌一遍（理由同上面的 applyFlagVisibility：
       flag 表与 DOM 的显隐会脱钩，设置仓与遮罩 opacity 同理）。 */
    applySettingOverrides();
    syncScreenChrome(under);
  }

  function doAction(action, def, index) {
    if (!action) return;
    /* ★ M15：浮层屏内的动作。对齐 krkr 侧 handleClick 的 sysicons 分支：
       「无论点哪儿，浮层都收起」，随后才派发动作。故除 open_sysicons 外，
       一律先 closeOverlay() 再继续走动作表。 */
    if (action === 'open_sysicons') { toggleSysIcons(); return; }
    if (state.screen === 'sysicons') {
      closeOverlay();
      /* close = 纯收起（不是「返回上一屏」，故不再走 NAV.close → goBack） */
      if (action === 'close') return;
    }
    if (NAV[action]) {
      var n = NAV[action];
      if (n.back) { goBack(); return; }
      if (n.toast) { toast(n.toast); return; }
      if (n.screen) {
        renderScreen(n.screen);
        if (n.dialog === 'restart') startDialog();
        return;
      }
    }
    /* ★ M47：**设置屏（config）的动作是前缀族**（config_char_<族> / config_set_<键>），
       switch 只能精确匹配 ⇒ 在这一层先派发（见 doConfigAction 的全表）。 */
    if (doConfigAction(action, def)) return;
    /* ★ M1（ISSUE-20260924-08）：鉴赏模式的动作族（gallery_tab_* / gallery_page_* /
       gallery_prev|next:<行>），理由同上（前缀族）。见 doGalleryAction。 */
    if (doGalleryAction(action, def)) return;
    /* ★ M06：回想屏逐块按钮的动作（`backlog_jump:<行号>` / `backlog_replay:<行号>`），
       理由同上（前缀族）。见 doBacklogAction。 */
    if (doBacklogAction(action)) return;
    switch (action) {
      /* ★ M3：系统菜单的替代 —— 展开右端快捷条（不换屏、不入历史、不钉住） */
      case 'open_sysmenu': expandQuickbar(); return;
      /* ★ M3：钉住开关（快捷条第 1 项「锁定」） */
      case 'quick_pin':    toggleQuickPin(); return;
      case 'skip_on':      toggleDialogMode('skip'); return;
      case 'auto_on':      toggleDialogMode('auto'); return;
      case 'hide_window':  toggleDialogMode('hide'); return;
      case 'select_choice':
        if (state.dlg.choosing) chooseIndex(Number(def && def.index !== undefined ? def.index : index));
        else toast('当前无选择肢');
        return;
      case 'do_save':
        toast('已写入第 ' + ((def && def.slot !== undefined) ? def.slot : '?') + ' 槽（演示：不实际落盘）');
        return;
      case 'do_load':
        toast('已读取第 ' + ((def && def.slot !== undefined) ? def.slot : '?') + ' 槽（演示：不实际读盘）');
        return;
      /* ★ M15：M13 追加的动作（右键图标浮层的 9 键，layout/_schema.md §六 M13 追加表）。
         这些动作在 krkr 侧由 uiActionDispatch 实现；HTML 复核页只做「可读反馈」，
         不实际落盘/改状态（见 README 已知差异）。 */
      case 'do_quicksave': toast('快速存档（演示：不实际落盘）'); return;
      case 'do_quickload': toast('快速读档（演示：不实际读盘）'); return;
      case 'prev_choice':  toast('返回上一选择点（演示：不实际回退）'); return;
      /* ★ M3：`next_choice` = prev_choice 的镜像实现（本页无流程状态模型，
         与 prev_choice 同样只给可读反馈；krkr 侧由 M2 实现真实前进） */
      case 'next_choice':  toast('前进到下一选择点（演示：不实际前进）'); return;
      case 'replay_voice': toast('重复语音（演示：无音效）'); return;
      case 'page_prev':    toast('上一页'); return;
      case 'page_next':    toast('下一页'); return;
      case 'flow_enter':   flowEnter(); return;   /* ★ M43：流程图屏「进入本章」（fc.jump_hit） */
      /* ★ 第 2 步（ISSUE-20260928-02）：流程图「主干 / 番外独立层」切换。
         `fc.entry.<NNNN>_hit`（layer:"frag<G>"）与 `fc.frag<G>_back_hit`（layer:"main"，
         按组返回键 —— 单件 `fc.fragback_hit` 已按冻结 §二 第 3 批拆成按组，本注释已同步）
         都走这里；目标层名**从数据读**（热区的 `layer` 字段），机制不写死任何层名。 */
      case 'flow_layer':   flowLayerSet(def && def.layer, action); return;
      case 'fragment_enter': toast('进入番外 ' + ((def && def.fragment_id) || '?') + '（演示：番外内容留空待后续）'); return;
      default:
        toast('未实现的动作：' + action);
    }
  }

  /* ==========================================================================
     ★ M06 · 回想屏（backlog）逐块按钮的两个动作 —— **与 krkr 侧 ui_screens.tjs 的
     uiActionDispatch 同名同语义**（动作名是接口冻结项，不得改名；见 layout/_schema.md §六）：
       backlog_jump:<行号>    → 跳到该行继续播放
       backlog_replay:<行号>  → 重播该行语音
     行号 = **全局项序号**（含分页偏移），由 buildList 用 `%row%` 换出来。
     ★ 本轮语义 = **接口冻结/占位**：引擎与复刻层都**没有音频代码** ⇒ 这两个动作只做
       「命中 → 派发 → 日志/状态可见」；**音频接线与真正的跳转生效留给编程组**
       （不得声称已生效，见冻结书 §2 末段）。可观测状态 = `state.backlog`。
     行号非法（非「非负十进制整数字面量」）⇒ 显式拒绝并打 `★M06ACT-REJECT★`，不猜、不静默
     （口径与 krkr 的 uiScreenRowNumber 一致：`Number('')`→0、`parseInt('abc')`→NaN 这类
     宽松解析会把错误吞掉，故必须正则严格判）。
     ========================================================================== */
  function doBacklogAction(action) {
    var act = (action === null || action === undefined) ? '' : String(action);
    var isJump = act.indexOf('backlog_jump:') === 0;
    var isRep = act.indexOf('backlog_replay:') === 0;
    if (!isJump && !isRep) return false;
    var pre = isJump ? 'backlog_jump:' : 'backlog_replay:';
    var rowS = act.slice(pre.length);
    if (!/^\d+$/.test(rowS)) {
      state.backlog.lastAct = act;
      state.backlog.lastRow = -1;
      toast('★M06ACT-REJECT★ ' + act + ' 行号非法（应为非负十进制整数）');
      return true;
    }
    var row = Number(rowS);
    state.backlog.lastAct = act;
    state.backlog.lastRow = row;
    state.backlog.count++;
    toast((isJump ? '回想·跳转' : '回想·重新播放') + ' 第 ' + row
      + ' 行（本轮仅派发 + 状态可见；音频/跳转生效留给编程组）');
    return true;
  }

  /* ==========================================================================
     ★ M47 · 设置屏（config）的四个动作 —— **与 krkr 侧 ui_screens.tjs 的
     uiScreenActionDispatch 同名同语义**（动作名是接口冻结项，不得改名）：
       config_tab_1 / config_tab_2  → 页签：cfg_page = "sys" / "snd"
       config_char_<族>             → 角色语音设定选中：cfg_vchar = "<族名>"
       config_set_<键>              → ON/OFF（或二选一）值按钮：cfg_v_<键> = 热区自带的 value
       config_reset                 → 全部设置恢复默认 + 回系统页（参考作「初始化」语义）
     每个分支都在 setFlag 之后调 applyFlagVisibility()：**不重建 DOM**，只同步已渲染节点的
     显隐 —— 与 krkr 每帧按 flag 重算等价（HTML 是 DOM 状态模型，见 flag 一节的长注释）。
     返回 true = 本函数已处理（doAction 不再往下走）。
     ========================================================================== */
  function doConfigAction(action, def) {
    var act = (action === null || action === undefined) ? '' : String(action);
    if (act === '') return false;

    /* ① 页签：系统页 / 声音页（用户要求 2：进入设置默认「系统」页 —— 由 flags_default 落地）。
       ★ 切页除置 `cfg_page` 外还要**派生值 flag**（见 configDerivePageFlags 的长注释）。 */
    if (act === 'config_tab_1' || act === 'config_tab_2') {
      var page = (act === 'config_tab_2') ? 'snd' : 'sys';
      var chp = setFlag('cfg_page', page);
      var dnum = configDerivePageFlags(page);
      applyFlagVisibility();
      toast('设置页签 → ' + ((page === 'snd') ? '声音' : '系统') + '（cfg_page=' + page + '）'
        + (chp ? '' : '（原本已在该页）')
        + '；值 flag 派生 ' + dnum + ' 项（非本页值元素置空 ⇒ 不跨页残留）');
      return true;
    }

    /* ② 初始化：恢复**全部 25 键**（9 数值 + 16 开关键）+ 回系统页 + **清空切页记忆**。
       ★ 一审打回 C2 的两处修正（与引擎 `config_reset` 分支逐条对齐）：
         (a) `settingResetAll()` 现在覆盖 25 键（补齐 16 个 enum 键之前只重置 9 个数值键 ⇒
             「改全屏 → 切声音页 → 点初始化」在 HTML 侧仍显示全屏、引擎回窗口模式，两端分叉）；
         (b) 必须 `configMemoClear()`（引擎 `uiScreenConfigMemoClear()`）—— 不清记忆的话，
             旧记忆会盖住刚恢复的默认值（三级优先链的第②级压过第③级）。
       仍**只重置设置值与页签**，不动其它状态（方案 §三.4：参考作的「初始化」还含更多项，
       本作只做这一层；`cfg_vchar` 这类无设置项的值键按引擎同序在派生时被重新捕获）。 */
    if (act === 'config_reset') {
      var nres = settingResetAll();
      configMemoClear();
      setFlag('cfg_page', 'sys');
      /* ★ 与切页同规则：回到系统页后必须**派生系统页的值 flag**，否则「从声音页点初始化」
         会让系统页的值按钮全不可见（它们在离开系统页时被置成了空串）。 */
      var drn = configDerivePageFlags('sys');
      applyFlagVisibility();
      sliderSyncAllDom();       // 复位后手柄位置必须跟着走（同 uiSettingSyncHook 的用途）
      toast('初始化：恢复默认（' + nres + ' 键）＋清空切页记忆，回系统页；值 flag 派生 '
        + drn + ' 项');
      return true;
    }

    /* ③ 角色语音设定：选中某族（选中态的**视觉**由 vis_flag=cfg_vchar 的两个元素表达）。
       ★ 一审打回 C3：写完之后必须**按当前页重派生一次**（与 `config_set_*` 同口径）——
         若此刻不在声音页（例如在**系统页**上程序化派发 `config_char_kob`：巡演 / 探针 /
         深链 / 将来的侧边栏入口），选中值必须**只进记忆、不上屏**；否则 33 件只带
         `cfg_vchar`、不带 `cfg_page` 的选中元素（胶囊 / 选中名 / 头像 / 名字）会在系统页显形 ⇒ 泄漏。
         切回声音页时由三级优先链（设置仓 → 记忆 → 数据初值）把选择恢复出来。 */
    if (act.indexOf('config_char_') === 0) {
      var fam = act.slice('config_char_'.length);
      if (fam === '') { toast('config_char_ 之后缺族名：' + act); return true; }
      cfgVarRemember['cfg_vchar'] = fam;            // ★ 值记忆（cfg_vchar 无设置项，只靠它存活）
      var chc = setFlag('cfg_vchar', fam);
      configDerivePageFlags(getFlag('cfg_page'));   // ★ 非本页 ⇒ 只进记忆、不上屏
      applyFlagVisibility();
      var vlab = (getFlag('cfg_vchar') === '') ? '(空：不在本页，值已存记忆)' : getFlag('cfg_vchar');
      toast('角色语音设定选中 → ' + fam + '（cfg_vchar=' + vlab
        + '，记忆=' + (cfgVarRemember['cfg_vchar'] || '(无)') + '）'
        + (chc ? '' : '（原本已是选中项）'));
      return true;
    }

    /* ④ 值按钮：键名以 `mute_` 开头 ⇒ **取反 toggle**（忽略热区自带的 `value`）；
       其余键 ⇒ 置成热区自带的 `value`（`on|off|window|full`）。
       该键**同时是一个设置项**时（16 个 enum 键补齐后**全部命中**）⇒ 值以**设置仓**为准、
       flag 从仓里派生，切页重派生 / 持久化 / toggle 三件事共用同一份真相（与引擎同）。
       最后按**当前页**重派生一次：非本页的键其值**只留仓与记忆、不上屏**。 */
    if (act.indexOf('config_set_') === 0) {
      var ckey = act.slice('config_set_'.length);
      var cx2 = ckey.indexOf(':');                  // 动作串可带 `:<值>` 后缀（程序化派发用）
      if (cx2 >= 0) ckey = ckey.slice(0, cx2);
      var cflag = 'cfg_v_' + ckey;
      var cval;
      if (ckey.indexOf('mute_') === 0) {
        /* `mute_` 前缀 = **取反 toggle**：静音勾选框只有「当前值」一种语义 —— 数据里
           `_on_hit`（勾选框）与 `_off_hit`（「静音」标签）**同指一个键**，
           值只能由当前有效值取反得出（否则两个热区各写各的值、互相打脸）。
           当前有效值取 `configValueOf`（**仓优先**）—— 本页键被置空时 flag 是 ""，
           直接读 flag 会把已存的 'on' 判成 'off'。 */
        cval = (configValueOf(ckey, cflag) === 'on') ? 'off' : 'on';
      } else {
        cval = configActionHitValue(act, def);
        if (cval === '') {
          toast('config_set_' + ckey + '：取不到值（命中热区未带 value 字段）——忽略，不猜');
          return true;
        }
      }
      if (settingHas(ckey)) {
        settingSet(ckey, cval);                     // 写仓（enum 值域校验在 settingAlign 内）
        cval = String(settingGet(ckey));            // 从仓里读回 ⇒ 仓值与 flag 值不分叉
      }
      cfgVarRemember[cflag] = cval;                 // ★ 值记忆（与引擎 uiScreenConfigMemoSet 同）
      configDerivePageFlags(getFlag('cfg_page'));   // ★ 写完后按当前页重派生（非本页不上屏）
      applyFlagVisibility();
      var chs = (getFlag(cflag) === cval);
      toast('配置项 ' + ckey + ' → ' + cval + '（' + cflag + '='
        + ((getFlag(cflag) === '') ? '(空：不在本页)' : getFlag(cflag)) + '）'
        + (settingHas(ckey) ? '' : '；★ 该键不在设置仓（SETTING_DEF），只置 flag + 记忆')
        + (chs ? '' : '；★ 该键不属于当前页 ⇒ 值已存但**不显示**（切回该页才显示）'));
      return true;
    }
    return false;
  }

  /* 值按钮「值」的取值口径（**与 krkr 的 uiScreenActionHitValue 同序**）：
     ① 命中热区自带的 `value` 字段（W2 数据：`"on"|"off"`，画面模式是 `"window"|"full"`）；
     ② 动作串的 `:<值>` 后缀（方案 §三.4 说两种写法都合法）。
     取不到 ⇒ 返回 ""，调用方**回报并忽略、不猜**（不得把值域写死成 on/off ——
     写死会把「画面模式」那两个热区全判成非法）。 */
  function configActionHitValue(act, def) {
    var v = (def && def.value !== null && def.value !== undefined) ? String(def.value) : '';
    if (v !== '') return v;
    var i = String(act).indexOf(':');
    return (i >= 0) ? String(act).slice(i + 1) : '';
  }

  /* ==========================================================================
     ★ M47（主代理裁决 · **与引擎端逐条同规则**）· 值键的跨页泄漏 + 切页值记忆
     背景（W2 实测的阻断项）：`vis_flag` 只允许**一对**（`layout/_schema.md` §四；
        krkr 的 uiScreenElementVisible 亦然，且那条判据有指纹守门、不得放宽），而本屏大量元素
        **同时**需要「页归属」（`cfg_page`）与「当前值 / 选中角色」（`cfg_v_<key>` / `cfg_vchar`）
        两个维度 ⇒ 数据侧只能二选一：**hit 一律带页 flag**（否则跨页抢点击、违反 §四 铁律一）、
        **值元素带值 flag** ⇒ 后果是「非本页的值元素残留可见」。
     机制（数据零改；键→页映射**从本屏数据导出**，机制里不写死第二份默认值）：
        · **切页 / 初始化 / 角色选中 / 值按钮**四处动作 + **进屏**一处装点，全部走同一个出口
          `configDerivePageFlags(page, captureMemo)`（= 引擎 `uiScreenConfigSyncPage`）；
        · **进屏装点**（`configFlagsInitFor`）传 `captureMemo = false`（同级 C4）：
          进屏时 flag 刚被重置成 `flags_default`，此刻捕获记忆 = 用默认值冲掉用户的选择；
        · 记忆表 `cfgVarRemember` = 引擎 `UIScrCfgVarMemo`；**空串不写**；`config_reset` 清空。
     三级优先链（**两端同序，不得各写一份**）：
        ① 设置仓（该键**真存过**才算 —— `settingStored`；16 个开关键补齐后本节多数命中此级）
        ② 切页记忆 `cfgVarRemember[<值键>]`（`cfg_vchar` 这类**无设置项**的键只靠它跨页存活）
        ③ `flags_default`（该屏数据里的初值）
     ========================================================================== */
  /* 切页时被清空的 `cfg_v_<键>` 的旧值（仅用于「回页时派生回来」；不是设置仓，
     不是持久化 —— 只活在本次会话的运行期）。 */
  var cfgVarRemember = {};

  /* ★ M47（主代理 2026-09-24 追加要求 ①）：**屏级 flag 初始化之后的派生入口**
     —— 与引擎 `uiScreenConfigFlagsInitFor` **同位置、同语义**（紧随 `initFlagsFor` /
     `uiScreenFlagsInitFor` 之后），只对「屏内有 `config_set_*` / `config_char_*` 热区」的屏生效
     （即设置屏；其它屏立即返回 0，零副作用）。
     为什么必须有这一处（两轮实测的残留面）：
       · **进屏那一刻**：`flags_default.cfg_vchar = "asu"` 会让 asu 的头像 / 名字 / 胶囊 /
         选中名在**系统页**上可见（4 件）—— 切页派生管不到「刚进屏」；
       · **深链 `?flags=cfg_page:snd`**：flag 是渲染**之后**由 URL 覆盖的，页面重出后派生
         又要按新页重做一遍（否则声音页留 17 件系统页值元素）。
     两处都在「DOM 渲染之前」调用 ⇒ 画出来就是对的；派生**不看 flag 从哪来**（默认值或 URL）。
     ★★ 一审打回 C4（同批修 `captureMemo`）：**进屏路径必须 `captureMemo = false`** ——
        进屏时 flag 刚被 `initFlagsFor` 重置成 `flags_default`，此刻「捕获记忆」等于用**默认值
        冲掉用户的选择**（`cfg_vchar` 这类无设置项的键会因此丢掉，表现为「离开设置屏再回来，
        选中的角色跳回 asu」）。引擎侧在同一批加同名形参、同一处传 false（两端同规则）。
     返回值 = 变化的项数（0 = 该屏不需要派生 / 派生后无变化）。 */
  function configFlagsInitFor(id) {
    var def = SCREENS[id];
    if (!def || !def.elements || !SCREENS.config) return 0;
    var need = false;
    for (var i = 0; i < def.elements.length; i++) {
      var a = def.elements[i].action ? String(def.elements[i].action) : '';
      if (a.indexOf('config_set_') === 0 || a.indexOf('config_char_') === 0) { need = true; break; }
    }
    if (!need) return 0;
    return configDerivePageFlags(getFlag('cfg_page'), false);   // ★ false = 不捕获记忆（见上）
  }

  /* ---- 值键映射（**从本屏数据导出**，与引擎 `uiScreenConfigMap` 同算法）----
     返回并行数组 { flags, setkeys, pages }：
       flags[i]   = 值标志名（`cfg_v_<键>` 或 `cfg_vchar`）
       setkeys[i] = 对应的**设置键名**（"" = 该值键没有设置项，如 `cfg_vchar`）
       pages[i]   = 所属页（取自该 hit 的 `vis_when`；**仅当 hit 自己带 `vis_flag == "cfg_page"`** 时采纳）
     判据：只认 `kind:"hit"` 且 `action` 以 `config_set_` / `config_char_` 开头者
       （页归属只认 hit —— 值元素本身不带页信息）；同 flag 只收一次（声明在前者胜）；
       未声明页归属（`pages` 为空）的值键**不进映射**（不做无依据的置空）。
     ★ 一审打回 C3 的根因就在这里：`config_char_*` 的页归属也必须**从数据导出**，
       先前把 `cfg_vchar` 写死成 'snd' 只够切页用，键→页映射与「非本页不上屏」的判定
       一旦分家就会漏。 */
  function configValueKeyMap() {
    var def = SCREENS.config;
    var out = { flags: [], setkeys: [], pages: [] };
    if (!def || !def.elements) return out;
    var seen = {};
    def.elements.forEach(function (el) {
      if (!el || el.kind !== 'hit') return;
      var a = el.action ? String(el.action) : '';
      var flag = '', sk = '';
      if (a.indexOf('config_set_') === 0) {
        sk = a.slice('config_set_'.length);
        var cx = sk.indexOf(':');                   // 动作串可带 `:<值>` 后缀 ⇒ 键名截到冒号前
        if (cx >= 0) sk = sk.slice(0, cx);
        flag = 'cfg_v_' + sk;
      } else if (a.indexOf('config_char_') === 0) {
        flag = 'cfg_vchar'; sk = '';
      } else return;
      if (flag === '' || flag === 'cfg_v_') return;
      if (seen[flag]) return;
      var pg = '';
      if (el.vis_flag !== undefined && String(el.vis_flag) === 'cfg_page') {
        pg = (el.vis_when === null || el.vis_when === undefined) ? '' : String(el.vis_when);
      }
      if (pg === '') return;                        // 未声明页归属 ⇒ 不进映射
      seen[flag] = 1;
      out.flags.push(flag); out.setkeys.push(sk); out.pages.push(pg);
    });
    return out;
  }

  /* 某值键的**当前有效值**（不含记忆）：有设置项 ⇒ 从**设置仓**取；否则取当前 flag 值
     （与引擎 `uiScreenConfigValueOf` 同）。 */
  function configValueOf(setKey, flagName) {
    if (setKey !== '' && settingHas(setKey)) return String(settingGet(setKey));
    return getFlag(flagName);
  }
  /* 该屏数据里某值标志的初值（`flags_default`；与引擎 `uiScreenFlagDefaultFor` 同） */
  function configFlagDefault(flagName) {
    var dflt = (SCREENS.config && SCREENS.config.flags_default) || {};
    var v = dflt[String(flagName)];
    return (v === null || v === undefined) ? '' : String(v);
  }
  /* **三级优先链**取值：① 设置仓（**真存过**才算，与引擎 `uiSettingStored` 同）
     → ② 切页记忆 → ③ `flags_default`。与引擎 `uiScreenConfigRestoreValue` 同序。 */
  function configRestoreValue(setKey, flagName) {
    if (setKey !== '' && settingHas(setKey) && settingStored(setKey)) return String(settingGet(setKey));
    var m = cfgVarRemember[String(flagName)];
    if (m !== undefined && m !== null && String(m) !== '') return String(m);
    return configFlagDefault(flagName);
  }

  /* 按新页派生全部值 flag；返回**实际发生变化的项数**。
     —— 全流程唯一的派生出口：`configFlagsInitFor`（进屏 / 深链，captureMemo=false）、
        `doConfigAction` 的页签 / 初始化 / 角色选中 / 值按钮四个分支（captureMemo 缺省 = true）。
     三个步骤**与引擎 `uiScreenConfigSyncPage` 同序同语义**（顺序不能换）：
       ① 捕获记忆：把每个值键的**当前有效值**记进 `cfgVarRemember`（**必须排在任何置空之前**）；
          空串不写（不得覆盖已有记忆）；`captureMemo === false` 时整步跳过（进屏路径，见上）。
       ② 播种：把「仓里还没有」的设置键按**当前 flag 值**写进设置仓（数据初值兜底），
          同样必须排在置空之前，否则非本页的键会丢数据默认值。
       ③ 派生：新页的键按三级优先链取回；**非新页的键置空串**（两个 `vis_when` 都不匹配
          ⇒ 该页值元素全不可见 —— 这就是挡跨页泄漏的那一刀）。 */
  function configDerivePageFlags(page, captureMemo) {
    var mp = configValueKeyMap();
    if (!mp.flags.length) return 0;                 // 该屏没有「值键」⇒ 本机制不适用（零影响）
    var pg = (page === null || page === undefined || String(page) === '')
      ? getFlag('cfg_page') : String(page);
    var i;
    /* ① 捕获记忆（先于任何置空） */
    if (captureMemo !== false) {
      for (i = 0; i < mp.flags.length; i++) {
        var cur = configValueOf(mp.setkeys[i], mp.flags[i]);
        if (cur !== '') cfgVarRemember[mp.flags[i]] = cur;
      }
    }
    /* ② 播种设置仓（**仓里没有**的键才写；用当前 flag 值 = 数据默认兜底） */
    for (i = 0; i < mp.setkeys.length; i++) {
      var sk0 = mp.setkeys[i];
      if (sk0 === '' || !settingHas(sk0)) continue;
      if (settingStored(sk0)) continue;        // ★ 仓里**已有合法值** ⇒ 绝不覆盖（主代理第四轮要求）
      var fv0 = getFlag(mp.flags[i]);
      /* ★ 只接受**非空**值（防御性空判，主代理第四轮要求）：空串没有信息量，写进仓只会让
         三级链的第①级拿到一个假值。当前键集下这是**无操作**——值键全是 `kind:"enum"`，
         而 `settingEnumAlign('')` 本就回落 `def`（不会存空串）；引擎侧由
         `uiSettingEnumAlign` 提供同一层保护。加这一句是为将来「值键改 int 型」时兜底
         （那时 `Number('')=0` 会真的存 0，第①级就会用 0 盖住真值）。 */
      if (fv0 === '') continue;
      settingSet(sk0, fv0);
    }
    /* ③ 派生 */
    var changed = 0;
    for (i = 0; i < mp.flags.length; i++) {
      var fl = mp.flags[i];
      if (mp.pages[i] !== pg) {
        if (setFlag(fl, '')) changed++;
        continue;
      }
      if (setFlag(fl, configRestoreValue(mp.setkeys[i], fl))) changed++;
    }
    return changed;
  }

  /* 清空切页记忆（引擎 `uiScreenConfigMemoClear`；`config_reset` 调用 ——
     不清会把刚恢复的默认值又盖回去）。 */
  function configMemoClear() {
    cfgVarRemember = {};
    return true;
  }

  /* ==========================================================================
     ★ M1（ISSUE-20260924-08）· 鉴赏模式：**页签 = 切屏** + 页内翻页 + 栏位内差分翻页
     —— 与 krkr 侧 `ui_screens.tjs` 的 `uiScreenMapGalleryTab` / `uiScreenGalleryShellSyncFor`
     / `gallery_tab_*` / `gallery_page_*` / `gallery_prev|next:<行>` 逐条同口径。
     接口冻结（主代理 2026-09-24 跨模块裁决）：
       gallery_tab_1..4        → 切到 gallery / music / dress / replay（**同级换屏**）
       gallery_page_prev|next  → 页内翻页（当前屏第一个可见 list，clamp）
       gallery_prev|next:<行号> → 栏位内差分翻页（`item_variants`；行号 = 全局项序号）
     外壳页签高亮用 `gal_tab` flag（值 = 承载屏 id）—— 唯一一处派生，出口 = galleryShellSyncFor。
     ========================================================================== */
  var GALLERY_SHELL_ID = 'gal_shell';     /* **接口冻结**（与 39_gal_shell.json 一致） */
  var GALLERY_TAB_FLAG = 'gal_tab';

  function galleryMapTab(action) {
    var a = String(action);
    if (a === 'gallery_tab_1') return 'gallery';
    if (a === 'gallery_tab_2') return 'music';
    if (a === 'gallery_tab_3') return 'dress';
    if (a === 'gallery_tab_4') return 'replay';
    return '';
  }

  /* 外壳数据里 `gal_tab` 的取值集是否含 tabValue（= 有没有对应的页签高亮件） */
  function galleryTabKnown(shellId, tabValue) {
    var def = SCREENS[shellId];
    if (!def || !def.elements) return false;
    var want = String(tabValue);
    for (var i = 0; i < def.elements.length; i++) {
      var e = def.elements[i];
      if (!e || e.vis_flag === null || e.vis_flag === undefined) continue;
      if (String(e.vis_flag) !== GALLERY_TAB_FLAG) continue;
      if (e.vis_when === null || e.vis_when === undefined) continue;
      if (String(e.vis_when) === want) return true;
    }
    return false;
  }

  /* 派生出口：承载屏挂了鉴赏外壳 ⇒ 把 `gal_tab` 置成**承载屏 id**。返回 1/0（别的屏恒 0）。 */
  function galleryShellSyncFor(id) {
    if (!id) return 0;
    var def = SCREENS[id];
    if (!def) return 0;
    if (String(def.attach || '') !== GALLERY_SHELL_ID) return 0;
    if (!galleryTabKnown(GALLERY_SHELL_ID, id)) return 0;
    if (getFlag(GALLERY_TAB_FLAG) === String(id)) return 0;
    setFlag(GALLERY_TAB_FLAG, String(id));
    applyFlagVisibility();
    return 1;
  }

  /* 清掉某屏所有 list 的页码与差分序号（切页签时调用 ⇒ 新页从第 1 页 / 第 1 张开始）
     ★ M8 一审 R3（2026-09-24）：归零时**同步把该屏页码 flag 复位 "1"**（与 krkr 的
     `uiScreenPageVariantClearFor` 同口径），否则 flag 停在旧页号 ⇒ 页码文本与实际页码分叉。 */
  function galleryPageVariantClearFor(id) {
    var def = SCREENS[id];
    if (!def || !def.elements) return 0;
    var n = 0;
    def.elements.forEach(function (e) {
      if (!e || e.kind !== 'list') return;
      state.listPage = state.listPage || {};
      if (state.listPage[e.id] !== undefined) state.listPage[e.id] = 0;
      state.varIdx[e.id] = {};
      n++;
    });
    var pf = pageFlagOf(id);
    if (pf) setFlag(pf, '1');
    return n;
  }

  function variantListId() {
    var def = SCREENS[state.screen];
    if (!def || !def.elements) return '';
    for (var i = 0; i < def.elements.length; i++) {
      var e = def.elements[i];
      if (!e || e.kind !== 'list') continue;
      if (!elementVisible(e)) continue;
      if (variantsOf(e) === null) continue;
      return String(e.id);
    }
    return '';
  }

  function firstListId() {
    var def = SCREENS[state.screen];
    if (!def || !def.elements) return '';
    for (var i = 0; i < def.elements.length; i++) {
      var e = def.elements[i];
      if (!e || e.kind !== 'list') continue;
      if (!elementVisible(e)) continue;
      return String(e.id);
    }
    return '';
  }

  function varIdxGet(listId, row) {
    var m = state.varIdx[listId];
    if (!m) return 0;
    var v = m[String(row)];
    return (v === null || v === undefined) ? 0 : Number(v);
  }
  function varIdxSet(listId, row, idx) {
    if (!state.varIdx[listId]) state.varIdx[listId] = {};
    state.varIdx[listId][String(row)] = idx;
  }

  /* 页内翻页的页码表（HTML 侧原先是 buildList 的 container.__page；为让「页内翻页」动作
     可驱动，这里补一张按元素 id 的运行表 —— 与 krkr 侧 `UIScrPage` 同义）。 */
  function listPageOf(id) {
    state.listPage = state.listPage || {};
    var p = state.listPage[id];
    return (p === null || p === undefined) ? 0 : Number(p);
  }

  /* ★ M8 一审 R3（2026-09-24）：屏级**页码 flag** 名（`page_flag` 字段；与 krkr 侧
     `uiScreenPageFlagOf` 同语义）。空串 = 该屏不声明（如 dress 无页码 ⇒ 不参与）。
     语义：翻页动作把 **1 基页号**写进该 flag ⇒ 屏内互斥页码文本（`vis_flag` = 该名、
     `vis_when` = "1"/"2"/…）随页切换；`galleryPageVariantClearFor` 归零时复位 "1"。
     **名字一律从数据读，机制不写死。** */
  function pageFlagOf(id) {
    var def = SCREENS[id];
    if (!def || def.page_flag === null || def.page_flag === undefined) return '';
    return String(def.page_flag);
  }

  /* 鉴赏动作族（前缀族 ⇒ 在 doAction 的 switch 之前派发）。返回 true = 已处理。 */
  function doGalleryAction(action, def) {
    var a = String(action);
    if (a.indexOf('gallery_tab_') === 0) {
      var target = galleryMapTab(a);
      if (target === '') { toast('★M08TAB-REJECT★ ' + a + '：未知页签（只认 gallery_tab_1..4）'); return true; }
      var host = state.screen;
      var hdef = SCREENS[host];
      if (!hdef || String(hdef.attach || '') !== GALLERY_SHELL_ID) {
        toast('★M08TAB-REJECT★ ' + a + '：当前屏 ' + host + ' 未挂鉴赏外壳（attach != '
              + GALLERY_SHELL_ID + '）');
        return true;
      }
      var nclr = galleryPageVariantClearFor(host);
      /* **同级换屏**：noHistory ⇒ 不压历史、上一页**不在屏栈里**（与 krkr uiScreenReplace 同义） */
      renderScreen(target, { noHistory: true });
      state.gallery.lastAct = a; state.gallery.lastRow = -1;
      state.gallery.count++; state.gallery.lastTab = target;
      toast('鉴赏页签 -> ' + target + '（' + host + ' → ' + target + '；同级换屏；清理该页 list '
            + nclr + ' 个；' + GALLERY_TAB_FLAG + '=' + getFlag(GALLERY_TAB_FLAG) + '）');
      return true;
    }
    if (a === 'gallery_page_prev' || a === 'gallery_page_next') {
      var lid = firstListId();
      if (lid === '') {
        toast('★M08PAGE-REJECT★ ' + a + '：当前屏 ' + state.screen + ' 没有可见的 list（页内翻页无目标）');
        return true;
      }
      var el = null;
      (SCREENS[state.screen].elements || []).forEach(function (e) { if (e && String(e.id) === lid) el = e; });
      if (!el) { toast('★M08PAGE-REJECT★ ' + a + '：找不到元素 ' + lid); return true; }
      var per = listPerPage(el);
      var total = (el.labels || []).length;
      var pages = Math.max(1, Math.ceil(total / per));
      var cur = listPageOf(lid);
      var np = cur + ((a === 'gallery_page_next') ? 1 : -1);
      if (np < 0) np = 0;
      if (np > pages - 1) np = pages - 1;
      state.listPage[lid] = np;
      state.gallery.lastAct = a; state.gallery.lastRow = -1; state.gallery.count++;
      /* 重画当前屏（页码变了 ⇒ 列表内容随页走） */
      renderScreen(state.screen, { noHistory: true, keepDialog: true });
      /* ★ M8 一审 R3（2026-09-24）：写完页码后**同步写页码 flag**（1 基）—— 与 krkr 的
         gallery_page_prev/next 处理器同口径。必须在 renderScreen **之后** set（renderScreen
         会按 flags_default 重置 flag 表，先写会被冲掉）；set 后补 applyFlagVisibility
         （setFlag 本身不刷显隐，与 galleryShellSyncFor 同款）。 */
      var pf = pageFlagOf(state.screen);
      if (pf) { setFlag(pf, String(np + 1)); applyFlagVisibility(); }
      toast('鉴赏·页内翻页 ' + lid + ' -> 第 ' + (np + 1) + '/' + pages + ' 页（每页 ' + per
            + ' 栏，共 ' + total + ' 栏）' + (pf ? '；' + pf + '=' + getFlag(pf) : '')
            + (np === cur ? '（已在边界，钳制）' : ''));
      return true;
    }
    if (a.indexOf('gallery_prev:') === 0 || a.indexOf('gallery_next:') === 0) {
      var isNext = a.indexOf('gallery_next:') === 0;
      var rowS = a.slice(isNext ? 'gallery_next:'.length : 'gallery_prev:'.length);
      if (!/^\d+$/.test(rowS)) { toast('★M08ACT-REJECT★ ' + a + ' 行号非法（应为非负十进制整数）'); return true; }
      var row = Number(rowS);
      var vid = variantListId();
      if (vid === '') {
        toast('★M08ACT-REJECT★ ' + a + '：当前屏 ' + state.screen + ' 没有带 item_variants 的可见 list');
        return true;
      }
      var vel = null;
      (SCREENS[state.screen].elements || []).forEach(function (e) { if (e && String(e.id) === vid) vel = e; });
      if (!vel) { toast('★M08ACT-REJECT★ ' + a + '：找不到元素 ' + vid); return true; }
      var vfr = variantRow(vel, row);
      if (!vfr || vfr.length === 0) {
        toast('★M08ACT-REJECT★ ' + a + '：第 ' + row + ' 栏没有差分内容（留空或越界）'); return true;
      }
      var n = vfr.length;
      var cur2 = varIdxGet(vid, row);
      if (cur2 < 0) cur2 = 0;
      if (cur2 >= n) cur2 = n - 1;
      var nx = cur2 + (isNext ? 1 : -1);
      if (nx < 0) nx = 0;                      /* ★ 边界口径 = clamp（钳制） */
      if (nx > n - 1) nx = n - 1;
      varIdxSet(vid, row, nx);
      state.gallery.lastAct = a; state.gallery.lastRow = row; state.gallery.count++;
      /* 重画当前屏（缩略图 + n/N 文本随之更新） */
      renderScreen(state.screen, { noHistory: true, keepDialog: true });
      toast('鉴赏·栏位内差分 ' + vid + ' 行=' + row + ' -> ' + (nx + 1) + '/' + n
            + '（素材 ' + String(vfr[nx]) + '）' + (nx === cur2 ? '（已在边界，钳制）' : ''));
      return true;
    }
    return false;
  }

  function goBack() {
    /* 浮层优先：返回 = 收起浮层（与右键再按一次的语义一致） */
    if (state.screen === 'sysicons') { closeOverlay(); return; }
    if (state.history.length) {
      var prev = state.history.pop();
      /* popEntry：返回 = krkr 的 uiScreenPop —— 挂壳屏重进也归零（M8 一审⑥，两端同口径） */
      renderScreen(prev, { noHistory: true, popEntry: true });
    } else {
      renderScreen('title', { noHistory: true });
    }
  }

  /* ★ H1（ISSUE-20260922-28，主代理 2026-09-22 裁决）· Esc = 「返回上一层 ／ 退出」，
     与 krkr 侧 `ui_screens.tjs:1340-1345`（`UIScrStack.count > 1` → `close`＝返回上一层；
     栈底 → `quit_game`）逐条对齐：
       ① 有浮层打开（`sysicons` 等 overlay）→ 关浮层（在 keydown 分支里先处理）
       ② 还能返回上一层（`state.history` 非空）→ 返回上一层（= krkr 的 `close`）
       ③ 栈底 → 真机 `quit_game`；**复刻端没有进程可退** ⇒ 退到标题屏 + 一行提示
          （**必然差异**，已登记 README §五）。
     注：`open_sysmenu` 动作**保留**（= 「展开竖条（不钉住）」的**编程入口**，
     `uiQuickbarOpen()` / `expandQuickbar()` 同一语义）；★ M37 起**数据里已无元素指向它**
     （整条把手 `quick.hit_toggle` 随「整条带」一起退场）⇒ 它与 Esc 都不再是鼠标入口，
     展开的唯一鼠标入口是**指针移到 x ≥ `reveal.in_x`**。
     ★ M45（2026-09-23）：它指向的 `sysmenu` 屏**已废除**，本动作**语义不变**（展开竖条）。 */
  function escBack() {
    if (state.history.length) { goBack(); return; }          // ② 返回上一层
    if (state.screen === 'title') {                          // ③ 已在栈底且就在标题屏
      toast('已在标题屏（复刻端无进程可退出）');
      return;
    }
    renderScreen('title', { noHistory: true });              // ③ 栈底：退到标题屏
    toast('复刻端无进程可退出：已返回标题');
  }

  /* ==========================================================================
     8. 对话框运行期（打字机 / 推进 / 选择肢 / 系统条状态）
     ========================================================================== */
  /* ★ M15：对话框元素可能位于 state.refs（对话框为顶层屏）或 state.baseRefs
     （右键浮层压在对话框上时），故一律走 refOf 两层查。 */
  function dlgEl(id) { var r = refOf(id); return r ? r.el : null; }

  function show(id, on) {
    var el = dlgEl(id);
    if (el) el.style.display = on ? '' : 'none';
  }

  function setText(id, txt) {
    var el = dlgEl(id);
    if (!el) return;
    var inner = el.querySelector('.ui-text-inner');
    if (inner) inner.textContent = txt;
  }

  /* 打字机：已显示部分 + 不可见占位（保持换行不回流，与 krkr 逐字绘制观感一致） */
  function setTextPartial(id, full, n) {
    var el = dlgEl(id);
    if (!el) return;
    var inner = el.querySelector('.ui-text-inner');
    if (!inner) return;
    var a = full.slice(0, n), b = full.slice(n);
    inner.textContent = '';
    var s1 = document.createElement('span'); s1.textContent = a;
    var s2 = document.createElement('span'); s2.style.visibility = 'hidden'; s2.textContent = b;
    inner.appendChild(s1); inner.appendChild(s2);
  }

  function startDialog() {
    var d = state.dlg;
    if (d.timer) { clearInterval(d.timer); d.timer = null; }
    if (d.autoTimer) { clearTimeout(d.autoTimer); d.autoTimer = null; }
    d.idx = 0; d.reveal = 0; d.typing = false;
    d.choosing = false; d.done = false;
    show('dlg.choices', false);
    setDialogMode();
    loadLine(0);
  }

  function curLine() {
    if (!DEMO_SCRIPT || !DEMO_SCRIPT.lines) return null;
    return DEMO_SCRIPT.lines[state.dlg.idx] || null;
  }

  function loadLine(i) {
    var d = state.dlg;
    if (!DEMO_SCRIPT) {
      setText('dlg.text', '（未注入演示台词：DEMO_SCRIPT 为空）');
      return;
    }
    if (i >= DEMO_SCRIPT.lines.length) { endDialog(); return; }
    d.idx = i; d.reveal = 0; d.typing = true;
    var ln = DEMO_SCRIPT.lines[i];
    var sp = ln.speaker || '';
    show('dlg.namebox', !!sp);
    show('dlg.name', !!sp);
    if (sp) setText('dlg.name', sp);
    show('dlg.cursor', false);
    setTextPartial('dlg.text', ln.cn || '', 0);
    tickType();
  }

  function typeIntervalMs() { return state.dlg.skip ? 0 : 28; }

  function tickType() {
    var d = state.dlg;
    if (d.timer) { clearInterval(d.timer); d.timer = null; }
    if (d.skip) { finishLine(); return; }
    d.timer = setInterval(function () {
      var ln = curLine();
      if (!ln) { clearInterval(d.timer); d.timer = null; return; }
      var full = ln.cn || '';
      d.reveal += 1;
      if (d.reveal >= full.length) { setTextPartial('dlg.text', full, full.length); finishLine(); return; }
      setTextPartial('dlg.text', full, d.reveal);
    }, typeIntervalMs());
  }

  function finishLine() {
    var d = state.dlg;
    if (d.timer) { clearInterval(d.timer); d.timer = null; }
    d.typing = false;
    var ln = curLine();
    if (ln) setTextPartial('dlg.text', ln.cn || '', (ln.cn || '').length);
    show('dlg.cursor', !d.hidden);
    if (d.auto) scheduleAuto();
  }

  function scheduleAuto() {
    var d = state.dlg;
    if (d.autoTimer) clearTimeout(d.autoTimer);
    d.autoTimer = setTimeout(function () { advance(); }, d.skip ? 260 : 1200);
  }

  function advance() {
    var d = state.dlg;
    if (d.choosing || d.done) return;
    if (d.typing) { finishLine(); return; }
    if (!DEMO_SCRIPT) return;
    if (d.idx + 1 >= DEMO_SCRIPT.lines.length) { endDialog(); return; }
    loadLine(d.idx + 1);
  }

  function stopTyping() {
    var d = state.dlg;
    if (d.timer) { clearInterval(d.timer); d.timer = null; }
    if (d.autoTimer) { clearTimeout(d.autoTimer); d.autoTimer = null; }
  }

  /* 台词播完：若本场景带选择肢，则**保留最后一句台词**并弹出选择肢；
     否则给出「演示台词结束」提示。 */
  function endDialog() {
    var d = state.dlg;
    stopTyping();
    d.typing = false; d.done = true;
    show('dlg.cursor', false);
    if (DEMO_SCRIPT.choices && DEMO_SCRIPT.choices.length) {
      openChoices();
      return;
    }
    setText('dlg.text', '（演示台词结束：场景 ' + DEMO_SCRIPT.scene_id + ' 共 ' + DEMO_SCRIPT.lines.length + ' 条真实中文台词）');
    show('dlg.namebox', false); show('dlg.name', false);
  }

  /* 选择肢：**几何/字体/高亮/动作全部取自屏数据 dlg.choices**（x/w/item_h/gap/
     stack_bottom/max_rows/item_frame/highlight/font/actions 一律不改）；
     只有 labels 由运行期填充——这与 krkr 侧一致（布局定义版式，脚本在运行期
     把当前场景的选项文本填进去）。文本取自 scene_ot.jsonl 的 choices[].text_cn。 */
  function openChoices() {
    var d = state.dlg;
    stopTyping();
    d.choosing = true;
    var cur = refOf('dlg.choices');
    if (!cur) return;
    var def = cur.def;
    var real = (DEMO_SCRIPT.choices || []).map(function (c) { return c.text_cn; });
    if (real.length) {
      var rebuiltDef = JSON.parse(JSON.stringify(def));
      rebuiltDef.labels = real;
      pressRelease();          /* ★ M46（一审 Minor-3）：重建前复位按下台账，同 go() */
      var node = buildList(rebuiltDef, 0);
      node.style.display = '';
      cur.el.parentNode.replaceChild(node, cur.el);
      state.refs['dlg.choices'] = { el: node, def: rebuiltDef };
    }
    show('dlg.choices', true);
  }

  function chooseIndex(i) {
    var d = state.dlg;
    var ch = (DEMO_SCRIPT.choices || [])[i];
    if (!ch) return;
    d.choosing = false;
    show('dlg.choices', false);
    var tgt = (DEMO_SCRIPT.branch_targets || [])[i] || '（未登记）';
    show('dlg.namebox', false); show('dlg.name', false);
    setText('dlg.text', '已选择：「' + ch.text_cn + '」\n分支目标：' + tgt
      + '（该分支场景正文未纳入本次演示台词集）\n再点一次返回标题。');
    d.done = true;
    d.afterChoice = true;
  }

  function toggleDialogMode(which) {
    var d = state.dlg;
    if (which === 'skip') {
      d.skip = !d.skip;
      if (d.skip) { d.auto = false; finishLine(); advance(); }
    } else if (which === 'auto') {
      d.auto = !d.auto;
      if (d.auto) { d.skip = false; if (!d.typing) scheduleAuto(); }
      else if (d.autoTimer) { clearTimeout(d.autoTimer); d.autoTimer = null; }
    } else if (which === 'hide') {
      d.hidden = !d.hidden;
      /* ★ M38：原表含 `dlg.window` / `dlg.cursor` / `dlg.sysbar` 三个**数据里已不存在**的 id
         （dialog 屏无框化后 `dlg.window` 退场归档，`dlg.sysbar` 更早已删）。
         `refOf()` 对缺失 id 返回 null、for 循环会跳过，故不是 bug；此处按现数据订正为
         「无框方案下参数确实还存在的层」：正文 + 角色名（`dlg.hint`/`dlg.mode_tag` 不隐藏，
         后者正是「窗口已隐藏」提示的宿主）。 */
      ['dlg.namebox', 'dlg.name', 'dlg.text'].forEach(function (id) {
        var r = refOf(id);
        if (r) r.el.style.display = d.hidden ? 'none' : (elementVisible(r.def) ? '' : 'none');
      });
      if (!d.hidden) show('dlg.cursor', !d.typing);
    }
    setDialogMode();
  }

  function setDialogMode() {
    var d = state.dlg;
    var tag = dlgEl('dlg.mode_tag');
    if (!tag) return;
    var txt = d.hidden ? '窗口已隐藏（点击画面恢复）'
            : d.skip ? '快进中'
            : d.auto ? '自动播放中' : '';
    var inner = tag.querySelector('.ui-text-inner');
    if (txt) {
      if (inner) inner.textContent = txt;
      tag.style.display = '';
    } else {
      tag.style.display = 'none';
    }
  }

  /* ==========================================================================
     9. 画布交互
     ========================================================================== */
  /* ★ M3：客户端坐标 → 画布坐标。`#canvas` 只经 transform:scale 缩放
     （内部坐标系恒为 UI_LAYOUT.canvas），故按实测矩形比例换算即可；
     不假定缩放系数与画布位置（无头截图/1:1/适应窗口三种情形都成立）。 */
  function canvasPoint(ev) {
    if (!canvasEl) return { x: 0, y: 0 };
    var r = canvasEl.getBoundingClientRect();
    var sx = r.width ? CANVAS.width / r.width : 1;
    var sy = r.height ? CANVAS.height / r.height : 1;
    return { x: (ev.clientX - r.left) * sx, y: (ev.clientY - r.top) * sy };
  }

  function bindCanvas() {
    canvasEl.addEventListener('click', function (ev) {
      var t = ev.target;
      if (t && t.closest && t.closest('[data-ui-interactive]')) return;
      /* ★ M35b 修（一审 Major-3）：**被遮挡的交互元素兜底**。
         问题：z 更高但「非交互」的元素会吃掉点击 —— 标题屏的菜单文字图（z 96..102）压在
         图标热区（z 95）之上、两者重叠 12px，于是每个菜单项有一条 12×96 的死区：
         krkr 会触发动作（它按几何扫描 `kind ∈ {hit,list}`），HTML 什么都不发生 ⇒ 两端分叉。
         做法：用浏览器自己的命中栈（`elementsFromPoint`，已含 z 与 transform）往下找第一个
         **交互元素**，再 `.click()` 到它自己的节点上 —— 复用既有 click 监听（含 list 的下标逻辑
         与点击瞬闪），不另写一套动作分发，避免双触发。
         注意只在「目标是**非交互**元素」时才会走到这里（上一行已 return），故不存在重复派发。 */
      var under = interactiveUnderPoint(ev);
      if (under) { under.click(); return; }
      /* ★ M15：浮层内左键点空白处 → 收起（对齐 krkr handleClick 的 sysicons 分支：
         命中判定为空白时 uiScreenPop）。控件热区（z 更高）已在上行 return。 */
      if (state.screen === 'sysicons') { closeOverlay(); return; }
      if (state.screen !== 'dialog') return;
      var d = state.dlg;
      if (d.hidden) { toggleDialogMode('hide'); return; }
      if (d.afterChoice) { d.afterChoice = false; renderScreen('title'); return; }
      if (d.choosing || d.done) return;
      advance();
    });

    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') {
        ev.preventDefault();
        /* ★ H1（主代理裁决）：Esc = 返回上一层／退出，与 krkr 的 uiScreenKey 对齐
           （栈深>1 → close＝返回上一层；栈底 → quit_game）。**不再触发 open_sysmenu**。 */
        if (state.screen === 'sysicons') { closeOverlay(); return; }   /* ① 浮层打开 → 关浮层 */
        escBack();                                                     /* ②③ 见 escBack() */
        return;
      }
      if (state.screen !== 'dialog') {
        /* ★ M47：**滑块热区的左右箭头**（可选增强，方案 §三.2 提到「建议」）。
           只认「事件目标就是滑块热区本身」的按键（ev.target.closest）—— 不依赖全局焦点
           台账，也就不会影响任何既有屏的键盘行为；取值走与拖动**同一条**路径
           （sliderKeyStep → sliderStore → 写设置仓 → 重画手柄）。 */
        var shEl = (ev.target && ev.target.closest) ? ev.target.closest('[data-ui-slider-hit]') : null;
        if (shEl && (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight')) {
          ev.preventDefault();
          sliderKeyStep(shEl.getAttribute('data-ui-slider-hit'), (ev.key === 'ArrowRight') ? 1 : -1);
          return;
        }
        /* ★ M43：流程图屏的方向键 / Enter（与 krkr 侧 uiFlowFlowchartKey 同口径）——
           方向键环状移动光标节点，Enter = 进入本章（动作 flow_enter 同一实现）。 */
        if (state.screen === 'flowchart') {
          if (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') { ev.preventDefault(); flowCursorMove(1); return; }
          if (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') { ev.preventDefault(); flowCursorMove(-1); return; }
          if (ev.key === 'Enter') { ev.preventDefault(); flowEnter(); return; }
        }
        if (ev.key === 'Backspace') { ev.preventDefault(); goBack(); }
        return;
      }
      var d = state.dlg;
      if (ev.key === ' ' || ev.key === 'Enter') {
        ev.preventDefault();
        if (d.afterChoice) { d.afterChoice = false; renderScreen('title'); return; }
        if (!d.choosing && !d.done) advance();
        return;
      }
      if (ev.key === 'Control') { d.skip = true; finishLine(); setDialogMode(); return; }
      if (ev.key === 'h' || ev.key === 'H') { toggleDialogMode('hide'); return; }
      if (ev.key === 'a' || ev.key === 'A') { toggleDialogMode('auto'); return; }
      if (ev.key === 'Backspace') { ev.preventDefault(); goBack(); }
    });
    document.addEventListener('keyup', function (ev) {
      if (ev.key === 'Control' && state.screen === 'dialog') { state.dlg.skip = false; setDialogMode(); }
    });

    /* ★ M15：右键 = 呼出/收起 9 图标功能浮层（sysicons）。
       原先绑的是 open_backlog（回想），本轮按 krkr 侧语义改为浮层开关；
       回想仍在浮层的 REPEAT/系统条「回想」键可达（dlg.sysbar 第 6 键 action=open_backlog）。
       语义与 krkr startup.tjs toggleSysIcons() 一致：dialog 呼出、浮层内再按收起、
       其它屏忽略（给出 toast 说明，不静默）。 */
    canvasEl.addEventListener('contextmenu', function (ev) {
      ev.preventDefault();
      toggleSysIcons();
    });

    /* ★ M3：画布级指针监听 —— 右端竖排快捷条的呼出/收起。
       原先只有逐元素的 mouseenter/mouseleave（buildHit），**没有全局 mousemove**，
       故本行为必须新增在本层（挂在画布容器上；坐标经 canvasPoint 换算成画布坐标）。
       mousemove 会从子元素冒泡上来，故指针落在任何元素上都能收到。
       阈值 in_x / out_x / delay_ms 全部读 `reveal`（脚本内不写死）。 */
    canvasEl.addEventListener('mousemove', function (ev) {
      var p = canvasPoint(ev);
      onRevealMove(p.x, p.y);
    });
    /* 指针离开画布 → 视为 out_x 之外（钉住时不动）。mouseleave 不冒泡，直接挂容器。 */
    canvasEl.addEventListener('mouseleave', function () { onRevealLeave(); });
  }

  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.style.display = '';
    toastEl.style.fontSize = px(fontSize(null, 'small'));
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.style.display = 'none'; }, 1800);
  }

  /* ==========================================================================
     10. 缩放（画布内部坐标系 = UI_LAYOUT.canvas，M15 起为 1920×1080；
         只改 transform:scale，内部坐标永不变）
     ========================================================================== */
  function setScale(s) {
    state.scale = s;
    var stage = document.getElementById('stage');
    canvasEl.style.transform = 'scale(' + s + ')';
    stage.style.width = px(CANVAS.width * s);
    stage.style.height = px(CANVAS.height * s);
  }

  function fitScale() {
    var head = document.querySelector('.shell-head');
    var foot = document.querySelector('.shell-foot');
    var reserved = (head ? head.offsetHeight : 0) + (foot ? foot.offsetHeight : 0) + 70;
    var availW = window.innerWidth - 40;
    var availH = window.innerHeight - reserved;
    var s = Math.min(availW / CANVAS.width, availH / CANVAS.height);
    if (!isFinite(s) || s <= 0) s = 1;
    if (s > 2) s = 2;
    return s;
  }

  /* ==========================================================================
     11. 外壳装配
     ========================================================================== */
  function syncScreenChrome(id) {
    var btns = document.querySelectorAll('[data-screen-btn]');
    for (var i = 0; i < btns.length; i++) {
      var on = btns[i].getAttribute('data-screen-btn') === id;
      btns[i].classList.toggle('on', on);
      var has = !!SCREENS[btns[i].getAttribute('data-screen-btn')];
      btns[i].classList.toggle('miss', !has);
      btns[i].title = has ? 'layout 数据已就绪' : 'layout 数据尚未产出';
    }
    var backBtn = document.getElementById('btn-back');
    if (backBtn) backBtn.disabled = false;
  }

  function buildShell() {
    /* 屏切换按钮 */
    var host = document.getElementById('screen-btns');
    if (host) {
      SCREEN_CATALOG.forEach(function (s) {
        var b = mk('button', 'btn');
        b.setAttribute('data-screen-btn', s.id);
        b.textContent = s.title_cn;
        b.addEventListener('click', function () { renderScreen(s.id); });
        host.appendChild(b);
      });
    }
    /* ★ M43：屏数标签改为**按目录实测**（原先硬编码「16 屏」，早已与数据脱钩；
       屏数随 `chapter` 屏删除由 20 → 19，硬编码值必然再次过期）。 */
    var scn = document.getElementById('screen-count');
    if (scn) scn.textContent = String(SCREEN_CATALOG.length);
    /* content_box 源选择 */
    var sel = document.getElementById('demo-source');
    if (sel) {
      Object.keys(BOXES).forEach(function (k) {
        var o = document.createElement('option');
        o.value = k; o.textContent = k;
        sel.appendChild(o);
      });
      sel.value = state.demoSource;
      sel.addEventListener('change', function () {
        state.demoSource = sel.value;
        if (state.screen) renderScreen(state.screen, { noHistory: true });
      });
    }
    /* 缩放按钮 */
    var b11 = document.getElementById('btn-1to1');
    var bfit = document.getElementById('btn-fit');
    if (b11) b11.addEventListener('click', function () {
      setScale(1); markZoom(b11);
    });
    if (bfit) bfit.addEventListener('click', function () {
      setScale(fitScale()); markZoom(bfit);
    });
    function markZoom(active) {
      [b11, bfit].forEach(function (b) { if (b) b.classList.remove('on'); });
      if (active) active.classList.add('on');
    }
    /* 隐藏面板 */
    var bt = document.getElementById('btn-panel');
    if (bt) bt.addEventListener('click', function () {
      document.body.classList.toggle('panel-off');
      bt.textContent = document.body.classList.contains('panel-off') ? '显示面板' : '隐藏面板';
      if (state.scale === fitScale()) setScale(fitScale());
    });
    /* 返回 */
    var bb = document.getElementById('btn-back');
    if (bb) bb.addEventListener('click', goBack);
    /* 重播演示 */
    var br = document.getElementById('btn-replay');
    if (br) br.addEventListener('click', function () { renderScreen('dialog'); });

    window.addEventListener('resize', function () {
      if (document.getElementById('btn-fit') && document.getElementById('btn-fit').classList.contains('on')) {
        setScale(fitScale());
      }
    });
  }

  /* ==========================================================================
     11.5 渲染性能基准（供 M15 自证：fragment 83 元素 / flowchart 92 元素
          「逐屏目视不得有明显卡顿或残留」的量化依据）
     ── 只测 renderScreen（含清空旧 DOM + 建新 DOM），不测资源加载。
     ── 同时回报每次渲染后 **DOM 节点总数**，用于证明「切屏清理旧 DOM」生效
        （若残留，节点数会随切屏次数单调增长）。
     ========================================================================== */
  function bench(rounds) {
    rounds = Math.max(1, Number(rounds) || 3);
    var ids = Object.keys(SCREENS);
    var out = [];
    for (var i = 0; i < ids.length; i++) {
      var id = ids[i];
      var def = SCREENS[id];
      var els = (def.elements || []).length + (def.bg ? 1 : 0);
      var t0 = 0, best = Infinity, worst = 0, nodes = 0;
      for (var r = 0; r < rounds; r++) {
        t0 = (window.performance && performance.now) ? performance.now() : Date.now();
        renderScreen(id, { noHistory: true, keepDialog: true });
        var dt = ((window.performance && performance.now) ? performance.now() : Date.now()) - t0;
        if (dt < best) best = dt;
        if (dt > worst) worst = dt;
        nodes = canvasEl.getElementsByTagName('*').length;
      }
      out.push({
        id: id, elements: els, overlay: !!def.overlay,
        best_ms: Math.round(best * 100) / 100,
        worst_ms: Math.round(worst * 100) / 100,
        dom_nodes: nodes
      });
    }
    return out;
  }

  /* ==========================================================================
     11.6 DOM 级自检（?selftest=1）
     ── 目的：本模块**不得做 OS 级 GUI 自动化**，故右键呼出 / 点空白收起 /
        点图标派发 / 全零 nine / dynamic 占位 这些交互路径改用 **DOM 级合成事件**
        （`el.click()`，直接走 buildHit 里注册的同一个监听器）与直接 API 调用来验证，
        结果写成纯文本供 `--dump-dom` 采集。
     ── 明确边界：这里**没有**任何 OS 级鼠标/键盘注入，也没有浏览器自动化工具；
        它验证的是「事件处理器 + 状态机」的逻辑正确性，**不能替代**真人在浏览器里
        的实际点击手感（见 README 已知差异与 M15 报告）。
     ========================================================================== */
  /* ★ ISSUE-20260927-03（模块 I · 一审 Major 遗留）：本套自检的**期望值一律从数据推**，
     其中「素材**存在性**」这一条独立锚点需要 `复刻\asset_index.js`（`工具\emit_asset_index.py`
     的生成物）。`复刻\index.html`（本套 B 的宿主页）**没有**加载它（模块 I 白名单不给改
     index.html），故这里按 replica.js 自身的 URL **动态注入**（`editor_ui.js` 的热重载同一
     手法，file:// 下实测可用），装完再跑原有自检体。
     装载失败 / 清单为空 ⇒ 由守卫**判 FAIL 并明示**（见 `flags.icon-hover-material-guard`），
     不静默降级成「无规范可依」—— 与 `复刻\_selftest_states.html::stateGuard` 同款口径。 */
  function ensureAssetIndex() {
    return new Promise(function (resolve) {
      if (window.UI_ASSET_INDEX && window.UI_ASSET_INDEX.items) { resolve('已随页面加载'); return; }
      var base = '';
      try {
        var ss = document.getElementsByTagName('script');
        for (var i = 0; i < ss.length; i++) {
          var s = String(ss[i].getAttribute('src') || '');
          if (/replica\.js$/.test(s)) { base = s.replace(/replica\.js$/, ''); break; }
        }
      } catch (e) { }
      var url = base + 'asset_index.js';
      var done = false;
      function fin(how) { if (done) return; done = true; resolve(how + '｜' + url); }
      var sc = document.createElement('script');
      sc.src = url;
      sc.onload = function () { fin('已动态装载'); };
      sc.onerror = function () { fin('装载失败'); };
      document.head.appendChild(sc);
      setTimeout(function () { fin('装载超时'); }, 4000);   // 兜底：不把整段自检挂死
    });
  }

  function runSelfTest() {
    return ensureAssetIndex().then(function (idxLoad) {
      return runSelfTestChecks(idxLoad);
    });
  }

  function runSelfTestChecks(idxLoad) {
    return new Promise(function (resolve) {
    var out = [];
    function chk(name, cond, detail) {
      out.push((cond ? 'PASS' : 'FAIL') + '\t' + name + '\t' + (detail === undefined ? '' : detail));
    }
    /* ★ M35b：主语已被 M34 重建移除的断言 —— 明确记 SKIP 并写清原因，
       不再让它以 FAIL 的形态误导（二审指出：这套 M15 期自检长期吐 RESULT=NG，
       其中一部分是失效主语、不是真失败）。SKIP 不计入失败数。 */
    function skip(name, why) {
      out.push('SKIP	' + name + '	' + why);
    }
    function kids(el) { return el ? el.childNodes.length : -1; }
    function elOf(id) { var r = refOf(id); return r ? r.el : null; }

    /* ① 对话框基线 */
    renderScreen('dialog', { noHistory: true });
    chk('canvas-1920', canvasEl.style.width === '1920px' && canvasEl.style.height === '1080px',
        canvasEl.style.width + 'x' + canvasEl.style.height);
    chk('dialog.screen', state.screen === 'dialog', state.screen);
    chk('dialog.under=null', state.underScreen === null, String(state.underScreen));
    chk('dialog.overlay-empty', kids(overlayEl) === 0, kids(overlayEl));
    var dlgKids = kids(layerEl);
    var dlgNameEl = elOf('dlg.name');

    /* ② 右键呼出浮层：必须先把下层屏画出来（overlay 屏的核心契约） */
    var ok = toggleSysIcons();
    chk('sysicons.open', ok === true && state.screen === 'sysicons', state.screen);
    chk('sysicons.under=dialog', state.underScreen === 'dialog', String(state.underScreen));
    chk('sysicons.base-painted', kids(layerEl) === dlgKids && layerEl.firstChild !== null, kids(layerEl));
    chk('sysicons.base-DOM-preserved', elOf('dlg.name') === dlgNameEl && dlgNameEl !== null);
    chk('sysicons.overlay-children', kids(overlayEl) === 20, kids(overlayEl));
    var veil = elOf('sysicons.veil');
    var veilCS = veil ? window.getComputedStyle(veil) : null;
    chk('sysicons.veil-dim', !!veil && Number(veilCS.opacity) < 1 && veilCS.backgroundColor !== 'rgba(0, 0, 0, 0)',
        veil ? (veilCS.backgroundColor + ' opa=' + veilCS.opacity) : 'veil 缺件');
    chk('sysicons.icons-9', (overlayEl.querySelectorAll('img.ui-image-img').length === 9),
        overlayEl.querySelectorAll('img.ui-image-img').length);

    /* ③ 左键点空白热区收起（走 sysicons.dismiss 的 action=close） */
    var dismiss = elOf('sysicons.dismiss');
    if (dismiss) dismiss.click();
    chk('sysicons.dismiss-click', state.screen === 'dialog' && state.underScreen === null, state.screen);
    chk('sysicons.overlay-cleared', kids(overlayEl) === 0, kids(overlayEl));
    chk('sysicons.back-to-dialog-DOM-preserved', elOf('dlg.name') === dlgNameEl);

    /* ④ 再呼出一次，然后点 SAVE 图标 → 浮层收起并派发 open_save */
    toggleSysIcons();
    chk('sysicons.reopen', state.screen === 'sysicons', state.screen);
    var saveHit = elOf('sysicons.hit_05_save');
    if (saveHit) saveHit.click();
    chk('sysicons.icon-dispatch', state.screen === 'save' && state.underScreen === null, state.screen);

    /* ⑤ 全零 nine（整图缩放）必须走 <img>，不得走 border-image（M18 已证其不绘制）
       ★ M3 / C1 订正（M35 独立复审 Major-4）—— 本条原先**不可证伪**，两处缺陷：
         ① 主语是**硬编码的 13 个 id**（数据一变就假失败，且换屏重建后主语可能根本不存在）；
         ② 「走 <img> 的比例」与「被拉伸到元素盒的比例」取自**同一个过滤后集合**
            （`znImgs` 只收「存在且走 <img>」的件）⇒ `stretched === znImgs.length` 在
            「全部元素都改走 border-image」时退化为 `0 === 0`，**恒真假通过**。
       现改为：**主语由数据推导**（该屏所有 `nine` 全零的 image 元素），
       计数主语是**推导出的全集**（不是过滤后的子集），并加一条「主语非空」前置断言。
       ⇒ 任一件改走 border-image / 缺件 / 不再有零 nine 元素，本组断言都会 FAIL
          （反向验证见 `_工作/ISSUE-20260922-28_M3_证据/reverse_c1/`）。 */
    renderScreen('save', { noHistory: true });
    var znDef = SCREENS.save || {};
    var zeroNineIds = (znDef.elements || []).filter(function (e) {
      return e && e.kind === 'image' && isZeroNine(e.nine);
    }).map(function (e) { return e.id; });
    chk('zeronine.subject-nonempty', zeroNineIds.length >= 1,
        'save 屏 nine 全零的 image 元素 ' + zeroNineIds.length + ' 件（数据推导）');
    var znOk = 0, znBad = [];
    var znImgs = [];      // ★ 图片是异步加载的，naturalWidth 需等 load 后才能查（见下方 async 段）
    zeroNineIds.forEach(function (id) {
      var el = elOf(id);
      if (!el) { znBad.push(id + '(缺件)'); return; }
      var img = el.querySelector('img.ui-image-img');
      var nine = el.querySelector('.ui-nine');
      if (img && !nine) {
        znOk++;
        /* ★ 布局尺寸必须在**还挂在文档里**时取：切屏后元素脱离文档，clientWidth 归零。
           img 的 CSS 盒是 width/height:100%，与图片是否已解码无关，故此处的值有效。 */
        znImgs.push({ id: id, el: el, img: img,
                      elW: el.clientWidth, elH: el.clientHeight,
                      imgW: img.clientWidth, imgH: img.clientHeight });
      } else znBad.push(id + (nine ? '(走了 border-image)' : '(无 img)'));
    });
    chk('zeronine.img-not-borderimage', znOk === zeroNineIds.length,
        znOk + '/' + zeroNineIds.length + '（主语 = 数据推导的全集） ' + znBad.join(','));
    chk('zeronine.no-placeholder', znBad.length === 0, znBad.join(','));

    /* ⑥ dynamic 占位：**主语由数据推导**（该屏所有带 `dynamic` 的元素）都必须画出来、不跳过。
       ★ M1（2026-09-24 · ISSUE-20260924-08）：M2 重写 `27_gallery.json`（CG 页改为 6×4 网格
         列表 + 栏位内差分）后 `gallery.preview` 已**退场** ⇒ 原断言的主语不存在，
         旧写法会以 FAIL 的形态误导（与 M35b 修 `save.slot1_thumb` 同一类问题）。
         现改为：主语从数据推导；**该屏已无 dynamic 层时记 SKIP 并写清原因**（不是静默通过）。 */
    renderScreen('gallery', { noHistory: true });
    var galDyn = ((SCREENS.gallery && SCREENS.gallery.elements) || [])
      .filter(function (e) { return e && e.dynamic; }).map(function (e) { return String(e.id); });
    if (!galDyn.length) {
      skip('dynamic.gallery_preview-placeholder',
           'gallery 屏已无 dynamic 层（M2 重写 27_gallery.json：CG 页改为网格列表 + 栏位内差分）');
    } else {
      var dynBad = [];
      galDyn.forEach(function (id) {
        var nd = elOf(id);
        var lbl = nd ? nd.querySelector('.ui-dynamic-label') : null;
        if (!nd || !nd.classList.contains('ui-dynamic-empty') || !lbl
            || !/^\[占位\]/.test(lbl.textContent || ''))
          dynBad.push(id + (lbl ? '（' + lbl.textContent.replace('\n', ' | ') + '）' : '（无占位）'));
      });
      chk('dynamic.gallery_preview-placeholder', dynBad.length === 0,
          galDyn.length + ' 件 dynamic 层（数据推导）：' + (dynBad.length ? dynBad.join('；') : '全部画了占位'));
    }
    /* ★ M35b：`save.slot1_thumb` 这个动态层已被 M34 重建时移除（现为 `sv.thumb1..12` 普通 image）
       ⇒ 本断言**无主语**，明确 SKIP，不再以 FAIL 的形态误导。 */
    skip('dynamic.slot_thumb-placeholder',
         '主语 save.slot1_thumb 已在 M34 重建中移除（现为 sv.thumb1..12，非动态层）');

    /* ⑦ 切屏清理：连续遍历 16 屏后 DOM 节点数不得随次数增长 */
    var ids = Object.keys(SCREENS);
    for (var pass = 0; pass < 3; pass++) {
      for (var i = 0; i < ids.length; i++) renderScreen(ids[i], { noHistory: true, keepDialog: true });
    }
    renderScreen('fragment', { noHistory: true });
    var n1 = canvasEl.getElementsByTagName('*').length;
    for (var p2 = 0; p2 < 3; p2++) renderScreen('fragment', { noHistory: true });
    var n2 = canvasEl.getElementsByTagName('*').length;
    chk('dom.no-leak', n1 === n2, 'fragment 连切 1 次=' + n1 + ' 节点，再切 3 次=' + n2 + ' 节点');

    /* ⑧ 浮层屏不占历史 */
    state.history = [];
    renderScreen('dialog', { noHistory: true });
    renderScreen('title', { noHistory: true });
    var h0 = state.history.length;
    renderScreen('dialog', { noHistory: true });
    renderScreen('sysicons');
    /* ★ M35b 二审订正：这里原写作 `state.history.length === state.history.length` ——
       **同一表达式自比、恒为真**，而上一行算出的 `h0` 反而从未被用（典型的“假通过”断言）。
       改成比对「开浮层前记录的 h0」，才真的在验「浮层屏不入历史」。 */
    chk('overlay.no-history-entry', state.history.length === h0,
        '开浮层前 history=' + h0 + '，开浮层后=' + state.history.length);
    closeOverlay();
    chk('overlay.close-overlay', state.screen === 'dialog' && state.underScreen === null, state.screen);

    /* ⑧.5 ★ M3（ISSUE-20260922-28）+ ★ M37（ISSUE-20260923-01）：右端快捷条 = 屏级 `attach` 附加层。
       与 krkr 侧同契约：附加层画进同一画布并压在上层、默认收起、`open_sysmenu` 不再换屏而是展开竖条、
       气泡按悬停项设置。
       ★ M37 形态变更：**一排独立圆形 icon**（`quick.ic_<key>`，image + `state_assets{normal,hover}`
       + `state_group`）＋悬停时**左侧浮出的名称药丸**（`quick.pl_<key>`）与白字（`quick.tx_<key>`）；
       旧「展开整条 `quick.btn` / slim 把手 `quick.tgl` / 高面板 `quick.tips` / 整条把手热区
       `quick.hit_toggle`」四件**已退场**（收起态一个元素都不画）。 */
    renderScreen('dialog', { noHistory: true });
    var qbIcon = elOf('quick.ic_lock'), qbHit = elOf('quick.hit_lock'),
        qbPin = elOf('quick.pin_mark');
    chk('flags.attach-rendered-on-dialog',
        !!qbIcon && !!qbHit && !!qbPin && state.attachId === 'quickbar',
        'attachId=' + state.attachId + '，quick.ic_lock/hit_lock/pin_mark 齐备='
        + (!!qbIcon) + '/' + (!!qbHit) + '/' + (!!qbPin));
    chk('flags.old-structure-gone',
        !elOf('quick.tgl') && !elOf('quick.btn') && !elOf('quick.tips') && !elOf('quick.hit_toggle'),
        'M37 退场四件都不在 DOM：tgl/btn/tips/hit_toggle = '
        + (!!elOf('quick.tgl')) + '/' + (!!elOf('quick.btn')) + '/' + (!!elOf('quick.tips'))
        + '/' + (!!elOf('quick.hit_toggle')));
    chk('flags.collapsed-by-default',
        getFlag('quickbar') === 'collapsed' && qbIcon.style.display === 'none'
          && qbHit.style.display === 'none' && qbPin.style.display === 'none',
        'quickbar=' + getFlag('quickbar') + '，ic_lock.display=' + qbIcon.style.display
        + '，hit_lock.display=' + qbHit.style.display + '，pin_mark.display=' + qbPin.style.display);
    setFlag('quickbar', 'expanded');
    applyFlagVisibility();
    chk('flags.expanded-shows-icons-and-items-not-pin',
        qbIcon.style.display !== 'none' && qbHit.style.display !== 'none'
          && qbPin.style.display === 'none',
        'ic_lock=' + qbIcon.style.display + '，hit_lock=' + qbHit.style.display
        + '，pin_mark=' + qbPin.style.display);
    /* 探针点一律由**数据**算出（本文件不写死任何坐标，同既有约定）：
       取对应 hit 矩形的中心；「项外的空白点」取 hit_lock 的**下缘**（y = y+h，半开区间外、
       仍是竖条区域内）——该处不属于任何一项 ⇒ 气泡必须为空。 */
    (function () {
      var qb = SCREENS.quickbar, R = qb.reveal, els = qb.elements || [];
      function boxOf(sfx) {
        for (var i = 0; i < els.length; i++) {
          if (String(els[i].id || '').slice(-sfx.length) === sfx) return els[i];
        }
        return null;
      }
      function mid(e) { return { x: Number(e.x) + Number(e.w) / 2, y: Number(e.y) + Number(e.h) / 2 }; }
      var bl = boxOf('hit_lock'), bo = boxOf('hit_option');
      var tLock = bl ? tipKeyAt(qb, R, mid(bl).x, mid(bl).y) : '(取不到 hit_lock)';
      var tOpt = bo ? tipKeyAt(qb, R, mid(bo).x, mid(bo).y) : '(取不到 hit_option)';
      var tGap = bl ? tipKeyAt(qb, R, mid(bl).x, Number(bl.y) + Number(bl.h)) : '(取不到 hit_lock)';
      chk('flags.tip-follows-item', tLock === 'lock' && tOpt === 'option' && tGap === '',
          'hit_lock 中心→"' + tLock + '"，hit_option 中心→"' + tOpt
          + '"，项外空白→"' + tGap + '"');
    })();
    /* ★ M37 新增（**目标导向**，与 krkr 侧 `uiScreenHoverAtIn` 的组绑定同契约）：
       悬停「第 N 项的热区」⇒ **第 N 个 icon 换态图**，其余 icon 保持常态；移出后复位。
       断言的是「哪个 icon 显示哪张图」（不是「两端一致」）。
       ★ ISSUE-20260927-03（模块 I · 一审 Major 遗留）：原实现把**素材名写死在断言里**
       （`nameOf` 用正则 `/x_ui_qbicon_[a-z_]+\.png/` 抓名，再与 `x_ui_qbicon_save.png` /
       `_on.png` / `load.png` 三个**字面量**比）⇒ 快捷条图标一旦改名（合法数据变更），
       本套就由绿转红。现改为**期望值一律从 `ui_layout.js` 的数据推**，范式与
       `复刻\_selftest_states.html` 的 ⑬c 同款：
         · `qbStatesOf()` —— 三态图名读数据，回落链 `pressed > hover > normal > asset`
           （与 `setFrame` / krkr 的 `uiWidgetItemFrameAsset` 同一条）；
         · `qbGuard`      —— 两条**独立锚点**（否则「数据推期望」会对称地跟着数据一起错）：
              ① 素材**存在性**（查 `asset_index.js` 清单，见 `ensureAssetIndex`）
              ② 常态 ≠ 悬停（否则「换态图」这条断言恒真、**看起来全绿却什么都没验**）。
       清单缺失 / 为空 / 三态缺件 / 无区分力 ⇒ 判 FAIL 并明示（不得静默放过）。 */
    var hoverMat = (function () {
      function nameBase(p) { return String(p || '').replace(/^.*\//, ''); }
      function stateImg(id) {
        var w = elOf(id);
        if (!w) return '';
        var s = w.querySelector('.ui-stateimage') || w.querySelector('.ui-nine');
        if (!s) return '';
        return String(s.style.backgroundImage || s.style.borderImageSource || '');
      }
      /* 图名一律取 URL 的 basename（**不认前缀、不认命名规则**；本文件不写死任何素材名） */
      function nameOf(v) {
        var m = /url\("?([^")]+)"?\)/.exec(String(v));
        return m ? nameBase(decodeURIComponent(m[1])) : '';
      }
      function hoverHit(id, on) {
        var w = elOf(id);
        if (!w) return;
        w.dispatchEvent(new MouseEvent(on ? 'mouseenter' : 'mouseleave',
                                       { bubbles: false, cancelable: true, view: window }));
      }
      /* 数据侧主语（**从 ui_layout.js 推**，不是写死的主语）：快捷条的圆形徽章两枚 */
      var qbEls = (SCREENS.quickbar || {}).elements || [];
      function qbElemOf(id) {
        for (var i = 0; i < qbEls.length; i++) if (qbEls[i].id === id) return qbEls[i];
        return null;
      }
      function qbStatesOf(e) {
        var host = e || {}, sa = host.state_assets || {}, bs = host.asset || '';
        return {
          normal: nameBase(sa.normal || bs),
          hover: nameBase(sa.hover || sa.normal || bs),
          pressed: nameBase(sa.pressed || sa.hover || sa.normal || bs)
        };
      }
      /* 素材存在性清单（**独立锚点**：与数据无关；缺失 ⇒ 明示判失败，不静默放过） */
      var ASSET_SET = (function () {
        var idx = window.UI_ASSET_INDEX, s = {};
        if (idx && idx.items) for (var i = 0; i < idx.items.length; i++) s[idx.items[i].n] = 1;
        return s;
      })();
      function assetCount() { return Object.keys(ASSET_SET).length; }
      var stS = qbStatesOf(qbElemOf('quick.ic_save')), stL = qbStatesOf(qbElemOf('quick.ic_load'));
      var guard = [];
      if (assetCount() === 0) {
        guard.push('素材清单 asset_index.js 未装载/为空（' + idxLoad + '）⇒ 存在性无从判，不得静默放过');
      } else {
        [['quick.ic_save', stS], ['quick.ic_load', stL]].forEach(function (p) {
          ['normal', 'hover', 'pressed'].forEach(function (k) {
            if (!p[1][k] || ASSET_SET[p[1][k]] !== 1)
              guard.push(p[0] + '.' + k + '="' + (p[1][k] || '(空)') + '" 不在素材清单');
          });
          if (p[1].normal === p[1].hover)
            guard.push(p[0] + '：normal 与 hover 同为 "' + p[1].normal + '" ⇒ 「换态图」断言恒真（失去区分力）');
        });
      }
      chk('flags.icon-hover-material-guard', guard.length === 0,
          guard.length ? guard.slice(0, 3).join('；')
                       : ('三态均在清单（' + assetCount() + ' 件）且区分力达标：save='
                          + stS.normal + '/' + stS.hover + '，load=' + stL.normal + '/' + stL.hover
                          + '（清单来源：' + idxLoad + '）'));
      var n2 = nameOf(stateImg('quick.ic_save')), n3 = nameOf(stateImg('quick.ic_load'));
      hoverHit('quick.hit_save', true);                   // 悬停存档热区（组 quick.save）
      var h2 = nameOf(stateImg('quick.ic_save')), h3 = nameOf(stateImg('quick.ic_load'));
      hoverHit('quick.hit_save', false);                  // 移出
      var r2 = nameOf(stateImg('quick.ic_save'));
      var okH = n2 === stS.normal && n3 === stL.normal
                && h2 === stS.hover && h3 === stL.normal
                && r2 === stS.normal;
      return { ok: okH, detail: '数据期望 save=' + stS.normal + '→' + stS.hover + '（悬停）/ '
                                + stS.normal + '（移出），load 恒为 ' + stL.normal
                                + '；悬停前 save/load=' + n2 + '/' + n3
                                + '；悬停存档热区后=' + h2 + '/' + h3 + '；移出后=' + r2 };
    })();
    chk('flags.icon-hover-material-via-group', hoverMat.ok, hoverMat.detail);
    var scBefore = state.screen;
    setFlag('quickbar', 'collapsed');
    applyFlagVisibility();
    doAction('open_sysmenu');
    /* ★ M45（2026-09-23，用户裁定）：断言**主语收窄 + 新增废除项自证** ——
       原断言末项 `!!SCREENS.sysmenu`（「屏数据仍保留」）随本屏废除**已不成立**，
       故改为断言其**已不存在**（`!SCREENS.sysmenu`）：动作语义（展开竖条、不换屏）保持不变，
       同时把「屏已真废除」锁进断言，防止屏数据被无声复活。 */
    chk('flags.open_sysmenu-expands-not-navigates',
        state.screen === scBefore && getFlag('quickbar') === 'expanded' && !SCREENS.sysmenu,
        'screen ' + scBefore + ' → ' + state.screen + '（未换屏），quickbar=' + getFlag('quickbar')
        + '，20_sysmenu 已废除=' + !SCREENS.sysmenu);
    chk('flags.pin-toggle',
        (function () {
          var PN = pinFlagOf(SCREENS.quickbar.reveal);      // ★ 从 reveal.pin_flag 读，不写死
          toggleQuickPin();
          var on = getFlag(PN) === '1' && getFlag('quickbar') === 'expanded'
                   && qbPin.style.display !== 'none';
          toggleQuickPin();
          return on && getFlag(PN) === '' && qbPin.style.display === 'none';
        })(),
        '钉住 flag 名（reveal.pin_flag）=' + pinFlagOf(SCREENS.quickbar.reveal)
        + '，解除后 pin_mark.display=' + qbPin.style.display);
    chk('flags.attach-absent-on-title',
        (function () { renderScreen('title', { noHistory: true });
          return state.attachId === null && !elOf('quick.ic_lock'); })(),
        'title 上 attachId=' + state.attachId + '，quick.ic_lock 存在=' + !!elOf('quick.ic_lock'));

    /* ⑧.6 ★ M3 / C4（主代理 2026-09-22 追加）：展开态「点第 N 项 = 派发第 N 项的 action」。
       背景：M36 阻断项 A —— 整条把手曾与 12 项热区重叠且 z 更高，点第 N 项实际派发的是
       把手动作（`open_sysmenu`）。数据已修（M37 起整条把手**整体退场**），但**接线正确性**
       必须由断言锁死，不能只靠可见性断言（可见 ≠ 点得到、点得到 ≠ 派对动作）。
       做法：逐项走**真实命中栈**（document.elementsFromPoint → 最上面的交互元素）
       取该项中心的节点并 `.click()`，再观测**该项 action 的可辨副作用**（spy）。
       ★ M37 主语口径：热区 id 一律形如 `quick.hit_<key>`（整条把手已不存在 ⇒ 不再需要排除）。 */
    (function () {
      var items = (SCREENS.quickbar.elements || []).filter(function (e) {
        return e && e.kind === 'hit' && e.action && /^quick\.hit_[a-z]+$/.test(String(e.id));
      });
      chk('flags.item-subject-count', items.length === 12,
          '快捷条「项」热区（quick.hit_<key> 且有 action）' + items.length + ' 件（应为 12）');

      /* 命中栈扫描要求被查的点**落在视口内**：无头默认视口可能只有 756×472，
         而本页 fitScale 在可用高度为负时会退化为 1（画布 1920 宽溢出屏幕）⇒
         elementsFromPoint 会返回空栈、断言假失败。故本段临时收起外壳面板并把画布缩到
         「整幅放得下」，扫完恢复。（setScale 只改 transform，不改布局尺寸，
         不影响 ⑤ 已捕获的 clientWidth。） */
      var sScale = state.scale, sPanel = document.body.classList.contains('panel-off');
      document.body.classList.add('panel-off');
      setScale(Math.max(0.05, Math.min((window.innerWidth - 16) / CANVAS.width,
                                       (window.innerHeight - 16) / CANVAS.height)));

      function topNodeAt(cx, cy) {                    // 画布坐标 → 命中栈里最上面的交互元素
        var r = canvasEl.getBoundingClientRect();
        var sx = r.width ? CANVAS.width / r.width : 1, sy = r.height ? CANVAS.height / r.height : 1;
        var st = [];
        try { st = document.elementsFromPoint(r.left + cx / sx, r.top + cy / sy) || []; } catch (e) { st = []; }
        for (var i = 0; i < st.length; i++) {
          var n = st[i].closest && st[i].closest('[data-ui-interactive]');
          if (n) return n;
        }
        return null;
      }
      function modeTagText() { var t = dlgEl('dlg.mode_tag'); return t ? (t.textContent || '') : ''; }
      /* 各 action 的「可辨副作用」= 派发 spy。**不写死「第 N 项是什么 action」** ——
         每项该派发什么一律读数据（`it.action`），本表只回答「该 action 生效时能看到什么」。 */
      var expect = {
        quick_pin:      function () { return getFlag(pinFlagOf(SCREENS.quickbar.reveal)) === '1'; },
        do_save:        function () { return /已写入第/.test(toastEl ? toastEl.textContent : ''); },
        do_load:        function () { return /已读取第/.test(toastEl ? toastEl.textContent : ''); },
        open_save:      function () { return state.screen === 'save'; },
        open_load:      function () { return state.screen === 'load'; },
        do_quicksave:   function () { return /快速存档/.test(toastEl ? toastEl.textContent : ''); },
        do_quickload:   function () { return /快速读档/.test(toastEl ? toastEl.textContent : ''); },
        auto_on:        function () { return /自动播放中/.test(modeTagText()); },
        skip_on:        function () { return /快进中/.test(modeTagText()); },
        next_choice:    function () { return /前进到下一选择点/.test(toastEl ? toastEl.textContent : ''); },
        prev_choice:    function () { return /返回上一选择点/.test(toastEl ? toastEl.textContent : ''); },
        open_backlog:   function () { return state.screen === 'backlog'; },
        open_flowchart: function () { return state.screen === 'flowchart'; },
        open_config:    function () { return state.screen === 'config'; }
      };
      var bad = [], okN = 0, unk = [];
      items.forEach(function (it) {
        var key = /\.hit_(.+)$/.exec(String(it.id))[1];
        var act = String(it.action);
        if (!expect[act]) { unk.push(key + ':' + act); return; }
        renderScreen('dialog', { noHistory: true });     // 每项独立复现初始态
        setFlag('quickbar', 'expanded');                 // 展开（数据默认 collapsed）
        applyFlagVisibility();
        if (toastEl) { toastEl.textContent = ''; toastEl.style.display = 'none'; }
        var cx = Number(it.x) + Number(it.w) / 2, cy = Number(it.y) + Number(it.h) / 2;
        var top = topNodeAt(cx, cy);
        var topId = top ? String(top.getAttribute('data-ui-id') || '') : '(无)';
        if (top) top.click();
        var eff = !!expect[act]();
        if (topId === it.id && eff) okN++;
        else bad.push(key + '(' + act + ') 命中栈顶=' + topId + ' 效果=' + eff);
      });
      chk('flags.item-N-click-dispatch-N', items.length === 12 && okN === items.length && !unk.length,
          okN + '/' + items.length + ' 项：命中该项 且 该 action 的可辨副作用出现'
          + (unk.length ? '；未覆盖的 action：' + unk.join(',') : '')
          + (bad.length ? '；失败：' + bad.join(' | ') : ''));
      /* 边界 1px：气泡的矩形判定是**半开区间** `[x, x+w)`（裁决 D1，与 krkr 一致）
         —— 取项 1 的右缘与下缘各查一列/一行。 */
      var b0 = items[0], k0 = /\.hit_(.+)$/.exec(String(b0.id))[1];
      var qDef = SCREENS.quickbar, qRv = qDef.reveal;
      var bx = Number(b0.x), by = Number(b0.y), bw = Number(b0.w), bh = Number(b0.h);
      renderScreen('dialog', { noHistory: true });
      setFlag('quickbar', 'expanded');
      applyFlagVisibility();
      var tXin = tipKeyAt(qDef, qRv, bx + bw - 1, by + bh / 2);
      var tXout = tipKeyAt(qDef, qRv, bx + bw, by + bh / 2);
      var tYin = tipKeyAt(qDef, qRv, bx + bw / 2, by + bh - 1);
      var tYout = tipKeyAt(qDef, qRv, bx + bw / 2, by + bh);
      chk('flags.tip-halfopen-boundary', tXin === k0 && tXout === '' && tYin === k0 && tYout === '',
          'x=w-1→"' + tXin + '" / x=w→"' + tXout + '" / y=h-1→"' + tYin + '" / y=h→"' + tYout
          + '"（半开区间，项=' + k0 + '）');
      /* 恢复外壳与缩放（本段只为命中栈扫描临时收窄视口占用） */
      if (!sPanel) document.body.classList.remove('panel-off');
      setScale(sScale);
    })();

    /* ⑧.7 ★ H1（主代理 2026-09-22 裁决）：Esc = 「返回上一层 ／ 退出」，
       与 krkr 侧 uiScreenKey（栈深>1 → close＝返回上一层；栈底 → quit_game）逐条对齐。
       ① 浮层打开 → 关浮层；② 还能返回 → 返回上一层；③ 栈底 → 复刻端退到标题 + 一行提示。
       **必须走真实 keydown 路径**（document 上的 Esc 监听），不能直调内部函数 —— 否则
       断言不到"键位映射"，只断言到函数本身。 */
    function pressEsc() {
      document.dispatchEvent(new KeyboardEvent('keydown',
        { key: 'Escape', bubbles: true, cancelable: true, view: window }));
    }
    function toastText() { return toastEl ? (toastEl.textContent || '') : ''; }
    function toastShown() { return !!(toastEl && toastEl.style.display !== 'none' && toastEl.textContent); }
    /* ② 还能返回上一层：dialog → save（history 里压入 dialog）→ Esc 必须回到 dialog，且不弹提示 */
    state.history = [];                                   // 先清空栈（本套件前面已压入多条），只看本步
    renderScreen('dialog', { noHistory: true });
    renderScreen('save');                                 // 不带 noHistory ⇒ history=[dialog]
    var histDepth = state.history.length;
    if (toastEl) { toastEl.textContent = ''; toastEl.style.display = 'none'; }
    pressEsc();
    chk('esc.back-to-previous-screen',
        histDepth === 1 && state.screen === 'dialog' && state.history.length === 0 && !toastShown(),
        'save（history=' + histDepth + '）→ Esc → screen=' + state.screen
        + '（应 dialog），提示="' + toastText() + '"（应无）');
    /* ① 浮层打开 → Esc 关浮层（不返回、不提示） */
    toggleSysIcons();
    var ovOk = (state.screen === 'sysicons' && state.underScreen === 'dialog');
    if (toastEl) { toastEl.textContent = ''; toastEl.style.display = 'none'; }
    pressEsc();
    chk('esc.closes-overlay',
        ovOk && state.screen === 'dialog' && state.underScreen === null && !toastShown(),
        '浮层打开=' + ovOk + ' → Esc → screen=' + state.screen
        + '/under=' + String(state.underScreen) + '，提示="' + toastText() + '"（应关浮层且无提示）');
    /* ③ 栈底 → 退到标题屏 + 一行提示（真机是 quit_game：**必然差异**，已登记 README §五） */
    state.history = [];                                   // 栈底条件：history 空
    renderScreen('save', { noHistory: true });
    if (toastEl) { toastEl.textContent = ''; toastEl.style.display = 'none'; }
    pressEsc();
    chk('esc.bottom-goes-title-with-toast',
        state.screen === 'title' && toastShown() && /无进程可退出/.test(toastText()),
        '栈底（Esc 前 history=0，当前屏 save）→ Esc → screen=' + state.screen
        + '，提示="' + toastText() + '"');
    renderScreen('dialog', { noHistory: true });

    /* ⑨ 异步段：等贴图 load 完成后，验证「整图拉伸到元素矩形」
          且「w/h ≠ PNG 实尺寸也不报错、不画占位」——这正是全零 nine 的语义。
          （图片是异步加载的，同步阶段 naturalWidth 恒为 0，故必须等 load。）
          ★ M3 / C1：这里的计数主语是**⑤ 推导出的全集 zeroNineIds**（不是过滤后的 znImgs）
          ⇒ 任一件没走 <img>（或已切屏 / 画了占位）都会计入 bad 并让断言 FAIL，
            不再出现「`stretched === znImgs.length` 自比恒真」的假通过。 */
    var pending = znImgs.filter(function (z) { return !(z.img.complete && z.img.naturalWidth > 0); });
    var settled = false;
    function finalize() {
      if (settled) return;
      settled = true;
      var byId = {};
      znImgs.forEach(function (z) { byId[z.id] = z; });
      var stretched = 0, diffs = 0, bad = [], firstImg = znImgs.length ? znImgs[0].img : null;
      zeroNineIds.forEach(function (id) {
        var z = byId[id];
        if (!z) { bad.push(id + '(未走 <img> / 已切屏)'); return; }
        var nw = z.img.naturalWidth;
        if (nw > 0 && z.elW > 0 && Math.abs(z.imgW - z.elW) <= 1 && Math.abs(z.imgH - z.elH) <= 1) stretched++;
        else bad.push(z.id + '(nw=' + nw + ',elW=' + z.elW + ',imgW=' + z.imgW + ')');
        if (nw > 0 && z.elW > 0 && nw !== z.elW) diffs++;
        if (z.el.querySelector('.ui-missing')) bad.push(z.id + '(画了占位)');
      });
      /* 主语全集 = 数据推导；每件都必须走 <img> 且被拉伸到元素盒（可证伪）。 */
      chk('zeronine.all-subjects-stretched-to-element-box', stretched === zeroNineIds.length,
          stretched + '/' + zeroNineIds.length + '（主语 = ⑤ 的全集） ' + (bad.length ? bad.join(',') : ''));
      chk('zeronine.size-differs-from-png-still-rendered', diffs >= 1 && diffs <= zeroNineIds.length,
          diffs + '/' + zeroNineIds.length + ' 张 PNG 实宽(' + (firstImg ? firstImg.naturalWidth : '?')
          + ') ≠ 元素宽(' + (znImgs[0] ? znImgs[0].elW : '?') + ')，仍正常绘制');
      var fail = out.filter(function (l) { return l.indexOf('FAIL') === 0; }).length;
      resolve({ lines: out, fail: fail, total: out.length });
    }
    if (!pending.length) { finalize(); return; }
    var t = setTimeout(finalize, 4000);
    var left = pending.length;
    pending.forEach(function (z) {
      function one() { if (--left <= 0) { clearTimeout(t); finalize(); } }
      z.img.addEventListener('load', one, { once: true });
      z.img.addEventListener('error', one, { once: true });
    });
    });
  }

  /* 外壳脚注的「演示背景」一行：当前屏没有 story_background 层时不应永远停在「探测中…」 */
  function updateDemoNote(def) {
    var el = document.getElementById('demo-bg-note');
    if (!el) return;
    var has = ((def && def.elements) || []).some(function (e) { return e.dynamic === 'story_background'; });
    el.textContent = has ? '（探测中…）' : '（当前屏无 story_background 层）';
  }

  /* 演示背景实况（写入外壳脚注） */
  function onDemoAsset(name) {
    var el = document.getElementById('demo-bg-note');
    if (el) el.textContent = name;
  }

  /* ==========================================================================
     12. 启动
     ========================================================================== */
  function boot() {
    document.documentElement.style.setProperty('--font-chain', fontChain());

    /* 画布 */
    var wrap = document.getElementById('stage-wrap');
    var stage = document.getElementById('stage');
    canvasEl = document.getElementById('canvas');
    canvasEl.style.width = px(CANVAS.width);
    canvasEl.style.height = px(CANVAS.height);
    /* 两个同尺寸容器，各自建立独立层叠上下文：
         layerEl   —— 下层屏（base，z-index 0）
         overlayEl —— 浮层屏（overlay:true，z-index 1，整体压在 base 之上）
       必须显式给 z-index，否则两容器的子元素 z-index 会在同一上下文里互相穿插
       （浮层 veil 的 z=0 会被对话框 window 的 z=20 盖住 → 压暗遮罩失效）。 */
    layerEl = mk('div', 'ui-layer ui-layer-base');
    layerEl.style.position = 'absolute';
    layerEl.style.left = '0'; layerEl.style.top = '0';
    layerEl.style.width = px(CANVAS.width);
    layerEl.style.height = px(CANVAS.height);
    layerEl.style.zIndex = '0';
    canvasEl.appendChild(layerEl);

    overlayEl = mk('div', 'ui-layer ui-layer-overlay');
    overlayEl.style.position = 'absolute';
    overlayEl.style.left = '0'; overlayEl.style.top = '0';
    overlayEl.style.width = px(CANVAS.width);
    overlayEl.style.height = px(CANVAS.height);
    overlayEl.style.zIndex = '1';
    canvasEl.appendChild(overlayEl);

    toastEl = mk('div', 'ui-toast');
    toastEl.style.display = 'none';
    toastEl.style.zIndex = '5';
    canvasEl.appendChild(toastEl);

    /* ★ M3 / C2：`?chrome=0` —— 「纯净截图」开关（M35 独立复审 Minor-5）。
       关掉**画布内 HTML 侧独有的 chrome**：纯热区（无态图 / 无组）的 hover / active /
       点击瞬闪叠色（krkr 侧什么都没有，这层蓝会进 1:1 截图），以及动作反馈 toast
       （HTML 侧的演示夹具）。规则见 replica.css 的 `#canvas.chrome-off`。
       **默认（不传该参数）保持现状**；`.ui-missing` / `.ui-dynamic-*` / `.ui-noscreen`
       与 list 悬停高亮**不**在关闭之列 —— 它们在 krkr 侧同样存在（那边也画占位与高亮）。 */
    if (/[?&]chrome=0/.test(location.search || '')) canvasEl.classList.add('chrome-off');

    /* 文档标题 = 标题屏 title.text_main.sample + title.text_sub.sample + UI_LAYOUT.signature
       （对应 krkr 侧 startup.tjs 写 Window.caption；AGENTS.md §六 署名规则） */
    var t = SCREENS.title;
    var cap = '';
    if (t) {
      (t.elements || []).forEach(function (e) {
        if (e.id === 'title.text_main' || e.id === 'title.text_sub') cap += (e.sample || '');
      });
    }
    if (L.signature) cap += ' ' + L.signature;
    if (cap) document.title = cap;

    /* 外壳脚注中的静态信息也取自数据 */
    var sig = document.getElementById('sig-note');
    if (sig && L.signature) sig.textContent = L.signature;
    var canv = document.getElementById('canvas-note');
    if (canv) canv.textContent = CANVAS.width + '×' + CANVAS.height;
    var src = document.getElementById('src-note');
    if (src) src.textContent = String(L.asset_root || 'krkr/assets/ui/');

    buildShell();
    bindCanvas();
    setScale(fitScale());
    var bfit = document.getElementById('btn-fit');
    if (bfit) bfit.classList.add('on');

    // 深链：?screen=<id> 或 #<id> 可直接打开指定界面（供人类复核与无头截图验收用）
    var want = null;
    try {
      var m = /[?&]screen=([A-Za-z0-9_]+)/.exec(location.search || '');
      if (m) want = m[1];
      else if (location.hash && /^#[A-Za-z0-9_]+$/.test(location.hash)) want = location.hash.slice(1);
    } catch (e) { want = null; }
    /* 性能基准模式：?bench=<轮数> —— 逐屏计时后把结果写成纯文本页面，
       供无头浏览器 --dump-dom 采集（M15 自证用；不影响正常渲染路径）。 */
    var benchN = null;
    try {
      var bm = /[?&]bench=(\d*)/.exec(location.search || '');
      if (bm) benchN = bm[1] ? Number(bm[1]) : 5;
    } catch (e) { benchN = null; }
    if (benchN) {
      var rows = bench(benchN);
      var pre = document.createElement('pre');
      pre.id = 'bench-out';
      pre.textContent = 'BENCH rounds=' + benchN + '\n'
        + rows.map(function (r) {
            return [r.id, r.elements, r.overlay ? 'overlay' : '-',
                    r.best_ms, r.worst_ms, r.dom_nodes].join('\t');
          }).join('\n')
        + '\nHEADER\tid\telements\toverlay\tbest_ms\tworst_ms\tdom_nodes';
      document.body.innerHTML = '';
      document.body.appendChild(pre);
      return;
    }

    /* DOM 级自检模式：?selftest=1（见 §11.6） */
    var doSelfTest = false;
    try { doSelfTest = /[?&]selftest=1/.test(location.search || ''); } catch (e) { doSelfTest = false; }
    if (doSelfTest) {
      runSelfTest().then(function (st) {
        var spre = document.createElement('pre');
        spre.id = 'selftest-out';
        spre.textContent = 'SELFTEST total=' + st.total + ' fail=' + st.fail + '\n'
          + st.lines.join('\n') + '\nRESULT=' + (st.fail === 0 ? 'OK' : 'NG');
        document.body.innerHTML = '';
        document.body.appendChild(spre);
      });
      return;
    }

    if (want && SCREENS[want]) {
      /* 浮层屏不能独占：它的**唯一真实入口**是对话框上按右键（krkr toggleSysIcons），
         故深链到浮层时先摆好对话框作下层——这样压暗遮罩压的才是游戏画面，
         与实机观感一致（若让它独占，按 krkr 语义只能叠在空画面上 → 纯黑）。 */
      if (SCREENS[want].overlay) renderScreen('dialog', { noHistory: true });
      renderScreen(want);
    } else {
      renderScreen('title');
    }

    /* ★ M3：`?flags=<名>:<值>[,<名>:<值>…]` —— 渲染完当前屏后覆盖屏级 flag 并同步显隐。
       用途：**无头单帧截图**（收起态 / 展开态 / 钉住 + 气泡），例如
         index.html?screen=dialog&flags=quickbar:expanded,qbar_tip:lock,qbar_pin:1
       覆盖只作用于本次渲染；后续换屏仍按新屏的 flags_default 重置（与实机一致）。 */
    applyFlagParam();

    /* 悬停态探针：?hover=<action 或 元素id> —— 渲染后对匹配的交互元素派发一次
       mouseenter，使**无头截图也能验收 hover 态**。走的正是真人鼠标那条 DOM 事件
       路径（见 buildHit 注册的 mouseenter 监听），不是另画一套。 */
    var hoverSel = null;
    try { var hm = /[?&]hover=([A-Za-z0-9_.\-~]+)/.exec(location.search || ''); if (hm) hoverSel = hm[1]; } catch (e) { hoverSel = null; }
    if (hoverSel) hoverProbe(hoverSel);

    /* ★ M35 按下态探针：?press=<action 或 元素id> —— 渲染后对匹配元素派发一次**左键
       mousedown 并保持按住**，使无头截图也能验收 pressed 态。同样走真人鼠标那条 DOM
       事件路径（buildHit 注册的 mousedown 监听 + 全局台账），不是另画一套。
       与 krkr 侧的**按下态探针**（项目根 `press_probe.tjs` → `UIScrPressProbe`）是**同一用途的两端实现**
       （那边只能按元素 id，这边还接受 action 名，方便按动作定位）。 */
    var pressSel = null;
    try { var pm = /[?&]press=([A-Za-z0-9_.\-~]+)/.exec(location.search || ''); if (pm) pressSel = pm[1]; } catch (e) { pressSel = null; }
    if (pressSel) pressProbe(pressSel);
  }

  /* ★ M3：解析并应用 `?flags=`（格式见 boot 里的说明）。返回实际被改动的 flag 数。
     支持 `名:值` 与裸 `名`（= 置空串）；值与名都做 trim；不可解析的片段忽略。 */
  function applyFlagParam() {
    var m = null;
    try { m = /[?&]flags=([^&#]*)/.exec(location.search || ''); } catch (e) { m = null; }
    if (!m || !m[1]) return 0;
    var n = 0;
    String(m[1]).split(',').forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf(':');
      var name = (i < 0 ? kv : kv.slice(0, i)).trim();
      var val = (i < 0 ? '' : kv.slice(i + 1)).trim();
      if (!name) return;
      if (setFlag(name, val)) n++;
    });
    /* ★ M47：`?flags=` 是**渲染之后**才覆盖 flag 的 ⇒ 序列屏（设置屏）的值 flag 必须
       在此刻**按覆盖后的 cfg_page 重新派生**一遍，否则深链出的声音页会留着系统页的值元素
       （实测 17 件）。派生只看「当前 flag 值」，与它来自默认值还是 URL 无关。 */
    if (state.screen) configFlagsInitFor(state.screen);
    /* ★ M1：`?flags=` 覆盖之后，鉴赏外壳的页签高亮也要按（覆盖后的）当前屏重派生 */
    if (state.screen) galleryShellSyncFor(state.screen);
    applyFlagVisibility();
    return n;
  }

  /* 解析探针目标选择子 → DOM 节点数组。
     语法（★ M46 扩展 · ★ M06 再扩展）：
       · `<元素id>` 或 `<action>`        —— 行为与旧版完全一致（匹配 data-ui-id/data-ui-action）；
       · `<元素id>~<项序号>`             —— **该 list 内 `data-ui-index` 相符的那一项**
                                            （逐项态图的探针入口；项序号是**全局序号**，
                                             与 krkr 合成指针的 `ch.choices:1` 同义）；
       · `<元素id>~<项序号>~<按钮key>`    —— ★ M06：**该 list 第 N 项的某个逐块按钮**
                                            （`data-ui-item-btn` 相符；与 krkr 巡演
                                             `itembtn` 步骤的 `<listId>:<行>:<key>` 同义 ——
                                             URL 里用 `~` 分隔，因为 `:` 在 `?hover=` 的正则里
                                             不在允许字符集内、`#` 会被当 fragment 截断）。
       为什么不用 `#`：`#` 在 URL 里是 fragment 分隔符，`?hover=a#1` 到不了 location.search。 */
  function probeTargets(sel) {
    var out = [];
    var i;
    var parts = String(sel).split('~');
    if (parts.length >= 3) {
      var base3 = parts[0], idx3 = parts[1], key3 = parts.slice(2).join('~');
      var hosts = document.querySelectorAll('[data-ui-action],[data-ui-id]');
      for (i = 0; i < hosts.length; i++) {
        var hd = hosts[i];
        if (hd.getAttribute('data-ui-action') !== base3 && hd.getAttribute('data-ui-id') !== base3) continue;
        var btns = hd.querySelectorAll('[data-ui-kind="list-item-btn"]');
        for (var q = 0; q < btns.length; q++) {
          if (btns[q].getAttribute('data-ui-item-btn-index') === idx3
              && btns[q].getAttribute('data-ui-item-btn') === key3) out.push(btns[q]);
        }
      }
      return out;
    }
    var tilde = String(sel).indexOf('~');
    if (tilde > 0) {
      var base = String(sel).slice(0, tilde), idx = String(sel).slice(tilde + 1);
      var nodes = document.querySelectorAll('[data-ui-action],[data-ui-id]');
      for (i = 0; i < nodes.length; i++) {
        var d = nodes[i];
        if (d.getAttribute('data-ui-action') !== base && d.getAttribute('data-ui-id') !== base) continue;
        var items = d.querySelectorAll('[data-ui-kind="list-item"]');
        for (var j = 0; j < items.length; j++)
          if (items[j].getAttribute('data-ui-index') === idx) out.push(items[j]);
      }
      return out;
    }
    var all = document.querySelectorAll('[data-ui-action],[data-ui-id]');
    for (i = 0; i < all.length; i++) {
      var n = all[i];
      if (n.getAttribute('data-ui-action') === sel || n.getAttribute('data-ui-id') === sel) out.push(n);
    }
    return out;
  }

  /* 对匹配 `sel`（data-ui-action 或 data-ui-id；★ M46 起支持 `id~项序号`）的交互元素
     派发 mouseenter；返回命中数。非交互元素（image/text/rect）没有 hover 监听，不在此列。 */
  function hoverProbe(sel) {
    var nodes = probeTargets(sel);
    var n = 0;
    for (var i = 0; i < nodes.length; i++) {
      var d = nodes[i];
      try { d.dispatchEvent(new MouseEvent('mouseenter', { bubbles: false })); } catch (e) {}
      d.setAttribute('data-ui-hover-probe', '1');
      n++;
    }
    return n;
  }

  /* ★ M35：对匹配 `sel` 的元素派发一次左键 mousedown 并**保持按住**（不派发 mouseup），
     让 pressed 态停在画面上供截图。返回命中数。（★ M46 起同样支持 `id~项序号`） */
  function pressProbe(sel) {
    var nodes = probeTargets(sel);
    var n = 0;
    for (var i = 0; i < nodes.length; i++) {
      var d = nodes[i];
      try {
        d.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true,
          view: window, button: 0, buttons: 1 }));
      } catch (e) {}
      d.setAttribute('data-ui-press-probe', '1');
      n++;
    }
    return n;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  /* 供自检 / 外部调用（reviewer 与编程组可用作视觉基线脚本接口） */
  window.UI_REPLICA = {
    state: state,
    renderScreen: renderScreen,
    goBack: goBack,
    doAction: doAction,
    setScale: setScale,
    fitScale: fitScale,
    screens: function () { return Object.keys(SCREENS); },
    catalog: function () { return SCREEN_CATALOG.slice(); },
    /* —— 以下为对话框运行期的驱动接口（供无头截图自检，不改变渲染逻辑）—— */
    layout: L,
    script: function () { return DEMO_SCRIPT; },
    jumpToLine: function (i) { loadLine(Number(i) || 0); },
    advance: advance,
    endDialog: endDialog,
    choose: chooseIndex,
    setDemoSource: function (s) { state.demoSource = s; if (state.screen) renderScreen(state.screen, { noHistory: true }); },
    setMode: toggleDialogMode,
    /* —— M15：右键浮层（供无头截图与人工复核直接驱动，不改变渲染逻辑）—— */
    toggleSysIcons: toggleSysIcons,
    openSysicons: function () { if (state.screen !== 'sysicons') toggleSysIcons(); },
    closeOverlay: closeOverlay,
    isOverlay: function () { return state.screen === 'sysicons'; },
    underScreen: function () { return state.underScreen; },
    /* M15 性能基准（见 §11.5）：返回 16 屏逐屏渲染耗时与 DOM 节点数 */
    bench: bench,
    /* M27 悬停态探针（?hover=<action|id>）：供无头截图与人工复核直接驱动 hover 态 */
    hoverProbe: hoverProbe,
    /* ★ M35 按下态探针（?press=<action|id>）：同上，驱动 pressed 态；
       附 pressRelease 供复核脚本手工复位（正常情况下 document 的 mouseup 已兜底） */
    pressProbe: pressProbe,
    pressRelease: pressRelease,
    /* ★ M1 屏级状态 flag（可见性机制）：与 krkr 侧 ui_screens.tjs 的
       uiScreenFlagSet / uiScreenFlagGet / uiScreenFlagsInitFor / uiScreenElementVisible 同源。
       —— M2/M3 的交互（贴边呼出、延时收起、钉住、动作派发）用这组接口驱动。 */
    initFlagsFor: initFlagsFor,
    getFlag: getFlag,
    setFlag: setFlag,
    elementVisible: elementVisible,
    applyFlagVisibility: applyFlagVisibility,
    flags: function () { return state.svFlags; },
    /* ★ M3 附加层与快捷条呼出（ISSUE-20260922-28）：与 krkr 侧 M2 同契约。
       供无头截图自检与人工复核直接驱动（不改变渲染逻辑）。 */
    attachScreen: function () { return state.attachId; },   // 当前附加层屏 id（无 = null）
    activeReveal: activeReveal,                             // { def, reveal, owner } | null
    expandQuickbar: expandQuickbar,                         // open_sysmenu 的新语义
    toggleQuickPin: toggleQuickPin,                         // quick_pin
    tipKeyAt: tipKeyAt,                                     // (def, reveal, x, y) → 项 key | ""
    applyFlagParam: applyFlagParam,                         // ?flags= 解析与应用
    pinFlag: function () {                                  // 当前生效的钉住 flag 名（读 reveal.pin_flag）
      var a = activeReveal();
      return a ? pinFlagOf(a.reveal) : '';
    },
    chromeOff: function () {                                // ?chrome=0 是否生效（纯净截图开关）
      return !!(canvasEl && canvasEl.classList && canvasEl.classList.contains('chrome-off'));
    },
    /* ★ M43：流程图运行期状态与动作（供无头 DOM 探针做**目标导向**自证）——
       flowEnter() 返回 true ⟺ 真的进入了剧情（已解锁并切屏）；返回 false 表示被拒（附 toast 原因）。 */
    flowState: function () { return state.flow; },
    flowEnter: flowEnter,
    flowCursorMove: flowCursorMove,
    flowStateOf: flowStateOf,
    flowVisitedCount: flowVisitedCount,
    /* ★ M47（ISSUE-20260924-01 · W4）：设置仓 + 滑块运行期 ——
       与 krkr 侧 `ui_settings.tjs`（UISettingGet/Set/ResetAll/Brief）与 `ui_widget.tjs`
       的滑块取值链同口径。供无头 DOM 探针与人工复核直接驱动（**不改变渲染逻辑**）。 */
    SETTING_DEF: SETTING_DEF,
    settingKeys: function () { return SETTING_KEYS.slice(); },
    settingGet: settingGet,
    settingSet: settingSet,
    settingResetAll: settingResetAll,
    settingBrief: settingBrief,
    settingMaskAlpha: settingMaskAlpha,     // 设置值 → **0..255** 口径的遮罩 alpha（映射式唯一入口）
    applySettingOverrides: applySettingOverrides,
    doConfigAction: doConfigAction,
    /* ★ M06：回想屏逐块按钮 —— 动作分派器与**可观测状态**（与 krkr 侧
       `uiActionDispatch` 的 backlog_* 分支、`UIScrBacklogLastAct/LastRow/ActCount` 同口径）。
       `backlogState()` 返回 { lastAct, lastRow, count, lastBtn, rejects }；
       `rejects` 是 `★M06ITEMBTN-REJECT★` 判词台账（守卫的负向证据）。 */
    doBacklogAction: doBacklogAction,
    backlogState: function () { return state.backlog; },
    /* ★ M47：切页值 flag 派生（与 W3 同规则）—— 供探针直接驱动 */
    configDerivePageFlags: configDerivePageFlags,
    configFlagsInitFor: configFlagsInitFor,   // 进屏 / 深链后的派生入口（见该函数注释）
    /* ★ M1（ISSUE-20260924-08）：鉴赏模式 —— 与 krkr 侧同名同语义。
       `galleryState()` 返回 { lastAct, lastRow, count, lastTab, rejects }；
       `varIdx` 是栏位内差分序号的运行表（嵌套）；`galleryShellSyncFor` 是页签高亮的派生出口。 */
    doGalleryAction: doGalleryAction,
    galleryState: function () { return state.gallery; },
    galleryShellSyncFor: galleryShellSyncFor,
    galleryMapTab: galleryMapTab,
    galleryPageVariantClearFor: galleryPageVariantClearFor,  /* ★ M8 一审 R3：归零出口（页码+差分+页码flag） */
    pageFlagOf: pageFlagOf,                                  /* ★ M8 一审 R3：屏级页码 flag 名（数据导出） */
    varIdxGet: varIdxGet,
    varIdxSet: varIdxSet,
    listPerPage: listPerPage,
    listCols: listCols,
    /* ★ M47 第三轮（一审打回 C2/C3/C4）：值键映射 / 三级链 / 记忆的三件公开探针 */
    configValueKeyMap: configValueKeyMap,     // { flags, setkeys, pages }（从屏数据导出）
    configValueOf: configValueOf,             // 某值键的当前有效值（不含记忆）
    configRestoreValue: configRestoreValue,   // 三级优先链取值
    configMemoClear: configMemoClear,         // 清空切页记忆（config_reset 用）
    settingStored: settingStored,             // 仓里是否真存过该键（三级链第①级的判据）
    settingKind: settingKind,
    cfgVarRemember: function () { return cfgVarRemember; },
    /* 滑块（按**元素 id**；屏上不存在该 id 时返回 null/false，不抛） */
    sliderValue: function (id) { var r = refOf(id); return (r && r.def) ? sliderValue(r.def) : null; },
    sliderValueAt: function (id, x) { var r = refOf(id); return (r && r.def) ? sliderValueAt(r.def, x) : null; },
    sliderStore: function (id, v) {
      var r = refOf(id);
      if (!r || !r.def || r.def.kind !== 'slider') return false;
      sliderStore(r.def, v);
      sliderSyncDom(id);
      return true;
    },
    sliderXOf: function (id, v) { var r = refOf(id); return (r && r.def) ? sliderXOf(r.def, v) : null; },
    sliderHot: sliderHot,
    sliderDragId: function () { return sliderDragId; },
    sliderHoverId: function () { return sliderHoverId; },
    sliderDragEnd: sliderDragEnd,
    sliderSyncAllDom: sliderSyncAllDom,
    sliders: function () { return Object.keys(sliderValsRt).slice(); },   // 有运行值的滑块 id 清单
    /* ★ E3（ISSUE-20260927-05）：连线（`links`）的**绘制台账**与守卫判词（与 krkr 侧
       `ui_flow_links.tjs` 同判据）。`linksState()` = `{ drawn, rejects }`：自检 ㉒ 据 `drawn`
       与数据对账（折线数 / 箭头多边形数 / 每点的实际坐标），据 `rejects` 判非法数据未静默。
       `linksAnchorZ` 一并导出，供探针核对「层序确实从数据导出」而非写死。 */
    linksState: function () { return state.links; },
    linksLayerZ: linksLayerZ,               /* 契约阈值（普通 z 刻度：z<阈值 ⇒ 在连线之下） */
    linksLayerZIndex: linksLayerZIndex,     /* 本层实际写入 canvas 的 CSS z-index（换算自阈值） */
    isBackdropRect: isBackdropRect,         /* 压暗层判据（与 krkr uiFlowLinkIsBackdropRect 同口径） */
    linkProblems: linkProblems,
    /* ★ 第 2 步（ISSUE-20260928-02）：`flow_layer` 动作 + `current` 高亮环。
       —— 与 krkr 侧 `ui_flow_links.tjs` 的层判据 / 环绘制同口径。
       `flowLayerState()` = { lastAct, lastLayer, count, flag, flagValue, rejects }；
       `ringState()`      = { drawn: [ {id,x,y,w,h,r,lw,zoom} ] }（环的**实际**几何，供自检对账）；
       `FLOW_RING`        = 冻结的环常量（{r,lw,inset,palette}；自检按它比对，并可用变异证明）。
       机制**不写死层名/flag 名**：`flowLayerFlagName` / `flowLayerValues` 全部从屏数据推。 */
    flowLayerSet: flowLayerSet,
    flowLayerState: function () { return state.flowLayer; },
    ringState: function () { return state.ring; },
    FLOW_RING: FLOW_RING,
    flowLayerFlagName: flowLayerFlagName,
    flowLayerMainValue: flowLayerMainValue,
    flowLayerValues: flowLayerValues,
    flowCurrentNodes: flowCurrentNodes,
    refreshFlowLayers: refreshFlowLayers,
    flowRingZIndex: flowRingZIndex,
    drawLinks: drawLinks,                   /* 供自检在切层后强制重画（与 refreshFlowLayers 同出口） */
    drawCurrentRing: drawCurrentRing,
  };
})();