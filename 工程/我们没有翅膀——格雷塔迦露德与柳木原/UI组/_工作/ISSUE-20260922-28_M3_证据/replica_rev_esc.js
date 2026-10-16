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

  /* 资产根：默认由 UI_LAYOUT.asset_root（"krkr/assets/ui/"）推导为 复刻/ 的相对路径。
     允许外部覆盖（仅供自检用的临时夹具，正式交付恒为默认值）。 */
  var ASSET_BASE = window.UI_ASSET_BASE || ('../' + String(L.asset_root || 'krkr/assets/ui/'));

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
    { id: 'sysmenu',   title_cn: '系统菜单',                owner: 'M5', required: ['面板', '菜单项 10 条', '关闭键'] },
    { id: 'confirm',   title_cn: '确认框',                  owner: 'M5', required: ['九宫格边框', '提示文本', '是/否 按钮'] },
    { id: 'loading',   title_cn: '加载提示',                owner: 'M5', required: ['居中提示图 320×120', '全屏遮罩'] },
    { id: 'save',      title_cn: '存档',                    owner: 'M5', required: ['底图', '槽列表 8 槽', '槽内缩略图/日期/摘要', '翻页', '返回'] },
    { id: 'load',      title_cn: '读档',                    owner: 'M5', required: ['底图', '槽列表 8 槽', '翻页', '返回'] },
    { id: 'config',    title_cn: '配置',                    owner: 'M5', required: ['底图', '设置项列表 ≥12 项', '说明栏', '返回'] },
    { id: 'backlog',   title_cn: '回想',                    owner: 'M5', required: ['底板', '文本列表', '滚动条', '返回'] },
    { id: 'gallery',   title_cn: 'CG 画廊',                 owner: 'M5', required: ['底板', '缩略图网格', '页码', '返回'] },
    { id: 'music',     title_cn: '音乐鉴赏',                owner: 'M5', required: ['底板', '曲目条列表', '播放控制', '返回'] },
    { id: 'ending',    title_cn: '片尾（STAFF/歌词）',        owner: 'M5', required: ['滚动区', '歌词条', '跳过'] },
    { id: 'chapter',   title_cn: '主线·章节选择',            owner: 'M4', required: ['幕/章卡片列表', '选中态', '进入键', '返回'] },
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

  function assetUrl(a) {
    return ASSET_BASE + String(a).replace(/^ui\//, '');
  }

  /* 字号：元素 font.size 优先，回退 UI_LAYOUT.fonts.sizes.<role>，再回退 body */
  function fontSize(f, role) {
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

  /* 字体回退链：f（元素 font 规格）给了 faces 就用它，否则用全局 fallback_faces。
     逐元素覆盖用于「某个屏要用特定字体」的场景（如标题菜单用 DejaVu Sans Mono Bold）。 */
  function fontChain(f) {
    var faces = (f && f.faces && f.faces.length) ? f.faces : (FONTS.fallback_faces || []);
    var parts = faces.map(function (x) { return '"' + String(x).replace(/"/g, '') + '"'; });
    parts.push('sans-serif');
    return parts.join(',');
  }

  function textShadow(f) {
    if (!f || !f.shadow) return null;
    var o = (f.shadow_ofs === null || f.shadow_ofs === undefined) ? 0 : Number(f.shadow_ofs);
    return px(o) + ' ' + px(o) + ' 0 ' + (col(f.shadow_color) || '#000000');
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
       承载屏自身 z 最高可到 30（dialog 的 dlg.window/choices），而附加层（quickbar）
       的 z 从 10 起 —— 原样写 z-index 会让附加层的低 z 元素（quick.tgl 10 / btn 11 /
       tips 12）被承载屏的高 z 元素盖住，与契约「附加层压在上层、
       点击优先级高于承载屏」矛盾。故叠画附加层前把偏移置为「承载屏最大 z-index + 1」，
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

  /* 探针：判断资产是否真的存在（file:// 下 new Image() 可用，无 CORS 限制） */
  function probe(url, ok, fail) {
    var im = new Image();
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
    refs: {},              // 顶层屏 元素 id → { el, def }
    baseRefs: {},          // ★ M15：下层屏 元素 id → { el, def }（浮层打开时二者并存）
    dlg: {
      idx: 0, reveal: 0, typing: false, timer: null,
      skip: false, auto: false, hidden: false,
      choosing: false, done: false, autoTimer: null
    }
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
     ⇒ 整条把手 `quick.hit_toggle`（其 key `toggle` 不在 ① 的集合内）**天然不产生气泡**，
       与数据意图一致（气泡 = 竖条 + 该行说明文字）；展开态它本身也被 `vis_when=collapsed` 挡掉。 */
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
     5. 渲染器
     ========================================================================== */
  /* 屏内元素：稳定排序（先 z，缺省按声明序；同 z 按声明序）后逐个渲染到 parent。
     map = 元素 id → {el, def} 的目标表（顶层屏用 state.refs，浮层下层用 state.baseRefs）。 */
  function renderElements(def, parent, map) {
    var els = def.elements || [];
    var ordered = els.map(function (e, i) { return { e: e, i: i }; });
    ordered.sort(function (a, b) {
      var za = (a.e.z === null || a.e.z === undefined) ? a.i : Number(a.e.z);
      var zb = (b.e.z === null || b.e.z === undefined) ? b.i : Number(b.e.z);
      if (za !== zb) return za - zb;
      return a.i - b.i;
    });
    ordered.forEach(function (o) { renderElement(o.e, parent, o.i, map); });
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

    /* ★ M3：换屏（含 push/pop）取消呼出收起计时、复位附加层与指针台账 ——
       旧 DOM 已销毁/换屏，任何在途的收起延时都必须作废（krkr 侧同口径）。 */
    cancelRevealTimer();
    state.attachId = null;
    revealRt.lastX = null; revealRt.lastY = null;

    if (!isOverlay) {
      /* 普通屏：浮层屏不入历史（它是「栈上的浮层」，收起即回到下层，不是一次导航） */
      if (!opts.noHistory && state.screen && state.screen !== id && !state.underScreen) {
        state.history.push(state.screen);
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
      layerEl.className = 'ui-screen ui-screen-' + id;
      if (!def) { renderNoScreen(id); syncScreenChrome(id); return; }
      if (def.bg) renderElement(def.bg, layerEl, -1, state.refs);
      renderElements(def, layerEl, state.refs);
      /* ★ M3：附加层（屏级 attach）——承载屏元素之后叠画（与 krkr 侧 M2 同契约） */
      renderAttachLayer(def, layerEl, state.refs);
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
        renderElements(udef, layerEl, state.baseRefs);
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
    renderElements(def, overlayEl, state.refs);
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
    if (e.nine && (!isZeroNine(e.nine)
                 || (window.__REV_FORCE_NINE && e.id === 'sv.tab_a'))) {   /* REV R1 */
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
    var sh = textShadow(f);
    if (sh) inner.style.textShadow = sh;
    if (e.wrap && e.max_lines) {
      inner.style.display = '-webkit-box';
      inner.style.webkitBoxOrient = 'vertical';
      inner.style.webkitLineClamp = String(e.max_lines);
      inner.style.overflow = 'hidden';
    }
    inner.textContent = (e.sample !== null && e.sample !== undefined) ? String(e.sample) : '';
    wrap.appendChild(inner);
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
     st = state_assets；d = DOM 节点；group = state_group（"" = 无组） */
  function attachStates(d, st, group, applyFn) {
    var self = { d: d, st: st, group: group || '',
                 ownHover: false, ownPress: false, effHover: false, effPress: false };
    /* ★ M35b：`applyFn` 允许为 null —— 用于**没有态图的纯热区**（迁移后热区退回纯热区，
       但仍要参与状态检测，才能把状态广播给同组的 image）。此时 apply() 是空操作。 */
    self.apply = function () { if (applyFn) applyFn(self.effHover, self.effPress); };
    function publish() {
      if (self.group) groupSync(self.group);
      else self.apply();
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
         ui_widget.tjs:291）。.ui-hit 已是 flex 居中 ⇒ 等价于 krkr 的
         floor((h - lineH)/2)；再上移半行距抵消 CSS leading（理由见 buildText 注释）。 */
      var labSize = fontSize(f, 'body');
      var labLh = labSize * lineSpacing(e, e.line_spacing_role || 'body');
      var lab = mk('div', 'ui-hit-label');
      lab.style.fontSize = px(labSize);
      lab.style.lineHeight = px(labLh);
      var labHL = (labLh - labSize) / 2;
      if (labHL) lab.style.transform = 'translateY(' + px(-labHL) + ')';
      lab.style.fontWeight = f.bold ? 'bold' : 'normal';
      lab.style.color = col(f.color) || (col('@palette.text_menu') || '#e8e8f0');
      var sh = textShadow(f);
      if (sh) lab.style.textShadow = sh;
      lab.textContent = String(e.label);
      d.appendChild(lab);
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
    var cols = (orient === 'h') ? Number(e.max_cols || labels.length || 1) : 1;
    var rowsCap = (orient === 'v') ? Number(e.max_rows || labels.length || 1)
                                   : Number(e.max_rows || 1);
    var perPage = Math.max(1, cols * rowsCap);

    var total = labels.length;
    var pages = Math.max(1, Math.ceil(total / perPage));
    if (!container.__page) container.__page = 0;
    var page = container.__page;
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

      /* 每项背景框（九宫格） */
      if (e.item_frame) {
        var fr = mk('div', 'ui-list-item-frame');
        var nine = e.item_frame.nine;
        if (nine && !isZeroNine(nine)) {
          fr.style.borderWidth = [nine.t, nine.r, nine.b, nine.l].map(px).join(' ');
          fr.style.borderImageSource = 'url("' + assetUrl(e.item_frame.asset) + '")';
          fr.style.borderImageSlice = [nine.t, nine.r, nine.b, nine.l].join(' ') + ' fill';
          fr.style.borderImageRepeat = 'stretch';
        } else {
          /* 无 nine / 全零 nine（整图缩放语义）：background 整图拉伸，不走 border-image
             （border-width 全 0 时 border-image 不绘制任何像素，见 isZeroNine 注释）。 */
          fr.style.backgroundImage = 'url("' + assetUrl(e.item_frame.asset) + '")';
          fr.style.backgroundSize = '100% 100%';
          fr.style.backgroundRepeat = 'no-repeat';
        }
        var fo = opa(e.item_frame.opacity);
        if (fo < 1) fr.style.opacity = String(fo);
        it.appendChild(fr);
      }

      /* 高亮块 */
      if (hl) {
        var hld = mk('div', 'ui-list-item-hl');
        hld.style.background = hlColor || 'transparent';
        if (hlOpa < 1) hld.style.opacity = String(hlOpa);
        it.appendChild(hld);
      }

      /* 标签 */
      var lab = mk('div', 'ui-list-item-label');
      lab.style.fontSize = px(fSize);
      lab.style.lineHeight = px(fLh);
      if (fHalfLeading) lab.style.transform = 'translateY(' + px(-fHalfLeading) + ')';
      lab.style.fontWeight = listFont.bold ? 'bold' : 'normal';
      if (listFont.faces && listFont.faces.length) lab.style.fontFamily = fontChain(listFont);
      lab.style.color = baseFontColor;
      lab.style.textAlign = e.align || 'center';
      var sh = textShadow(listFont);
      if (sh) lab.style.textShadow = sh;
      lab.textContent = String(label);
      it.appendChild(lab);

      /* 悬停 / 选中反馈：高亮块 + 文字色 */
      if (hlFontColor) {
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

    /* 翻页（仅当超出容量时生成；属 HTML 侧补充 chrome，见 README） */
    if (pages > 1) {
      var pager = mk('div', 'ui-list-pager');
      pager.style.fontSize = px(fontSize(null, 'small'));
      var prev = mk('span', 'pg-btn'); prev.textContent = '◀';
      var num = mk('span', 'pg-num'); num.textContent = (page + 1) + ' / ' + pages;
      var next = mk('span', 'pg-btn'); next.textContent = '▶';
      function go(delta) {
        var p = container.__page + delta;
        if (p < 0) p = 0;
        if (p > pages - 1) p = pages - 1;
        if (p === container.__page) return;
        var visible = container.style.display;
        container.__page = p;
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
     7. 动作名表（layout/_schema.md §六）→ 行为
     ========================================================================== */
  var NAV = {
    game_start:      { screen: 'dialog', dialog: 'restart' },
    game_continue:   { screen: 'dialog', dialog: 'restart' },
    open_chapter:    { screen: 'chapter' },
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
       注：`20_sysmenu.json` 数据与素材按契约**保留不删**（只是不再可达）；
       `SCREEN_CATALOG` 里的 sysmenu 条目同样保留（复核页仍可直接跳转查看）。 */
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
      case 'chapter_enter': toast('进入章节 ' + ((def && def.chapter_id) || '?') + '（演示：章节数据待 M4 产出）'); return;
      case 'fragment_enter': toast('进入番外 ' + ((def && def.fragment_id) || '?') + '（演示：番外内容留空待后续）'); return;
      default:
        toast('未实现的动作：' + action);
    }
  }

  function goBack() {
    /* 浮层优先：返回 = 收起浮层（与右键再按一次的语义一致） */
    if (state.screen === 'sysicons') { closeOverlay(); return; }
    if (state.history.length) {
      var prev = state.history.pop();
      renderScreen(prev, { noHistory: true });
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
     注：`open_sysmenu` 动作**保留**（数据里收起态把手 `quick.hit_toggle` 仍指向它，点把手＝展开竖条），
     只是**不再挂到 Esc 上**。 */
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
      ['dlg.window', 'dlg.namebox', 'dlg.name', 'dlg.text', 'dlg.cursor', 'dlg.sysbar'].forEach(function (id) {
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
        doAction('open_sysmenu');   /* REV H3：旧行为（Esc = 展开竖条） */
        return;
      }
      if (state.screen !== 'dialog') {
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
  function runSelfTest() {
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

    /* ⑥ dynamic 占位：gallery_preview（M14 新增）与 slot_thumb 都必须画出来、不跳过 */
    renderScreen('gallery', { noHistory: true });
    var gp = elOf('gallery.preview');
    var gpl = gp ? gp.querySelector('.ui-dynamic-label') : null;
    chk('dynamic.gallery_preview-placeholder',
        !!gp && gp.classList.contains('ui-dynamic-empty') && !!gpl && /^\[占位\]/.test(gpl.textContent || ''),
        gpl ? gpl.textContent.replace('\n', ' | ') : '无占位');
    /* ★ M35b：`save.slot1_thumb` 这个动态层已被 M34 重建时移除（现为 `sv.thumb1..12` 普通 image）
       ⇒ 本断言**无主语**，明确 SKIP，不再以 FAIL 的形态误导。
       现存的动态层只剩两件（dlg.content / gallery.preview），其中 gallery 已由上一句覆盖。 */
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

    /* ⑧.5 ★ M3（ISSUE-20260922-28）：右端快捷条 = 屏级 `attach` 附加层。
       与 krkr 侧 M2 同契约：附加层画进同一画布并压在上层、默认收起、
       `open_sysmenu` 不再换屏而是展开竖条、气泡按悬停项设置。 */
    renderScreen('dialog', { noHistory: true });
    var qbBar = elOf('quick.btn'), qbTgl = elOf('quick.tgl'),
        qbHit = elOf('quick.hit_lock'), qbPin = elOf('quick.pin_mark');
    chk('flags.attach-rendered-on-dialog',
        !!qbBar && !!qbTgl && !!qbHit && state.attachId === 'quickbar',
        'attachId=' + state.attachId + '，quick.btn/quick.tgl/quick.hit_lock 齐备='
        + (!!qbBar) + '/' + (!!qbTgl) + '/' + (!!qbHit));
    chk('flags.collapsed-by-default',
        getFlag('quickbar') === 'collapsed' && qbBar.style.display === 'none'
          && qbTgl.style.display !== 'none' && qbHit.style.display === 'none',
        'quickbar=' + getFlag('quickbar') + '，btn.display=' + qbBar.style.display
        + '，tgl.display=' + qbTgl.style.display + '，hit_lock.display=' + qbHit.style.display);
    setFlag('quickbar', 'expanded');
    applyFlagVisibility();
    chk('flags.expanded-shows-bar-items-not-pin',
        qbBar.style.display !== 'none' && qbHit.style.display !== 'none'
          && qbPin.style.display === 'none',
        'btn=' + qbBar.style.display + '，hit_lock=' + qbHit.style.display
        + '，pin_mark=' + qbPin.style.display);
    /* 探针点一律由**数据**算出（本文件不写死任何坐标，同既有约定）：
       取对应 hit 矩形的中心；「把手内的空白点」取 quick.hit_toggle 左缘 +1px
       （该处落在竖条内、但不在 12 项任何一项的矩形里）。 */
    (function () {
      var qb = SCREENS.quickbar, R = qb.reveal, els = qb.elements || [];
      function boxOf(sfx) {
        for (var i = 0; i < els.length; i++) {
          if (String(els[i].id || '').slice(-sfx.length) === sfx) return els[i];
        }
        return null;
      }
      function mid(e) { return { x: Number(e.x) + Number(e.w) / 2, y: Number(e.y) + Number(e.h) / 2 }; }
      var bl = boxOf('hit_lock'), bo = boxOf('hit_option'), bt = boxOf('hit_toggle');
      var tLock = bl ? tipKeyAt(qb, R, mid(bl).x, mid(bl).y) : '(取不到 hit_lock)';
      var tOpt = bo ? tipKeyAt(qb, R, mid(bo).x, mid(bo).y) : '(取不到 hit_option)';
      var tGap = bt ? tipKeyAt(qb, R, Number(bt.x) + 1, bl ? mid(bl).y : Number(bt.y) + 1) : '(取不到 toggle)';
      chk('flags.tip-follows-item', tLock === 'lock' && tOpt === 'option' && tGap === '',
          'hit_lock 中心→"' + tLock + '"，hit_option 中心→"' + tOpt
          + '"，把手内空白→"' + tGap + '"');
    })();
    var scBefore = state.screen;
    setFlag('quickbar', 'collapsed');
    applyFlagVisibility();
    doAction('open_sysmenu');
    chk('flags.open_sysmenu-expands-not-navigates',
        state.screen === scBefore && getFlag('quickbar') === 'expanded' && !!SCREENS.sysmenu,
        'screen ' + scBefore + ' → ' + state.screen + '（未换屏），quickbar=' + getFlag('quickbar')
        + '，20_sysmenu 数据保留=' + !!SCREENS.sysmenu);
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
          return state.attachId === null && !elOf('quick.btn'); })(),
        'title 上 attachId=' + state.attachId + '，quick.btn 存在=' + !!elOf('quick.btn'));

    /* ⑧.6 ★ M3 / C4（主代理 2026-09-22 追加）：展开态「点第 N 项 = 派发第 N 项的 action」。
       背景：本轮阻断项 A —— 整条把手曾与 12 项热区重叠且 z 更高，点第 N 项实际派发的是
       把手动作（`open_sysmenu`）。数据已修（把手 `vis_when=collapsed`），但**接线正确性**
       必须由断言锁死，不能只靠可见性断言（可见 ≠ 点得到、点得到 ≠ 派对动作）。
       做法：逐项走**真实命中栈**（document.elementsFromPoint → 最上面的交互元素）
       取该项中心的节点并 `.click()`，再观测**该项 action 的可辨副作用**（spy）。 */
    (function () {
      var items = (SCREENS.quickbar.elements || []).filter(function (e) {
        return e && e.kind === 'hit' && e.action
               && /\.hit_(.+)$/.test(String(e.id)) && String(e.id) !== 'quick.hit_toggle';
      });
      chk('flags.item-subject-count', items.length === 12,
          '快捷条「项」热区（有 action 且非整条把手）' + items.length + ' 件（应为 12）');

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
      /* —— 反向验证用（REV R2）：复现 C1 修之前的两种写法 —— */
      chk('REV-old-stretch-self-referential', stretched === znImgs.length,
          '旧写法 stretched(' + stretched + ') === znImgs.length(' + znImgs.length + ') ⇒ '
          + ((stretched === znImgs.length) ? 'PASS（**假通过**：被破坏的那件不在 znImgs 里）' : 'FAIL'));
      var allIdsOld = ['sv.thumb1', 'sv.thumb2', 'sv.thumb3', 'sv.thumb4', 'sv.thumb5', 'sv.thumb6',
                       'sv.thumb7', 'sv.thumb8', 'sv.thumb9', 'sv.thumb10', 'sv.thumb11', 'sv.thumb12',
                       'sv.tab_a'];
      chk('REV-old-hardcoded-13', znOk === 13,
          '旧写法 znOk(' + znOk + ') === 硬编码 13（实际主语 ' + zeroNineIds.length + ' 件）');
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
    try { var hm = /[?&]hover=([A-Za-z0-9_.\-]+)/.exec(location.search || ''); if (hm) hoverSel = hm[1]; } catch (e) { hoverSel = null; }
    if (hoverSel) hoverProbe(hoverSel);

    /* ★ M35 按下态探针：?press=<action 或 元素id> —— 渲染后对匹配元素派发一次**左键
       mousedown 并保持按住**，使无头截图也能验收 pressed 态。同样走真人鼠标那条 DOM
       事件路径（buildHit 注册的 mousedown 监听 + 全局台账），不是另画一套。
       与 krkr 侧的**按下态探针**（项目根 `press_probe.tjs` → `UIScrPressProbe`）是**同一用途的两端实现**
       （那边只能按元素 id，这边还接受 action 名，方便按动作定位）。 */
    var pressSel = null;
    try { var pm = /[?&]press=([A-Za-z0-9_.\-]+)/.exec(location.search || ''); if (pm) pressSel = pm[1]; } catch (e) { pressSel = null; }
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
    applyFlagVisibility();
    return n;
  }

  /* 对匹配 `sel`（data-ui-action 或 data-ui-id）的交互元素派发 mouseenter；返回命中数。
     非交互元素（image/text/rect）没有 hover 监听，不在此列。 */
  function hoverProbe(sel) {
    var nodes = document.querySelectorAll('[data-ui-action],[data-ui-id]');
    var n = 0;
    for (var i = 0; i < nodes.length; i++) {
      var d = nodes[i];
      if (d.getAttribute('data-ui-action') === sel || d.getAttribute('data-ui-id') === sel) {
        try { d.dispatchEvent(new MouseEvent('mouseenter', { bubbles: false })); } catch (e) {}
        d.setAttribute('data-ui-hover-probe', '1');
        n++;
      }
    }
    return n;
  }

  /* ★ M35：对匹配 `sel` 的元素派发一次左键 mousedown 并**保持按住**（不派发 mouseup），
     让 pressed 态停在画面上供截图。返回命中数。 */
  function pressProbe(sel) {
    var nodes = document.querySelectorAll('[data-ui-action],[data-ui-id]');
    var n = 0;
    for (var i = 0; i < nodes.length; i++) {
      var d = nodes[i];
      if (d.getAttribute('data-ui-action') === sel || d.getAttribute('data-ui-id') === sel) {
        try {
          d.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true,
            view: window, button: 0, buttons: 1 }));
        } catch (e) {}
        d.setAttribute('data-ui-press-probe', '1');
        n++;
      }
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
    }
  };
})();