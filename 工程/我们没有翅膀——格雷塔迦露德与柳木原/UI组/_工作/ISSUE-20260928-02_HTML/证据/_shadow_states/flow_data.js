// ============================================================
// flow_data.js —— 【自动生成，禁止手改】
// 生成器：UI组/工具/gen_flow_data.py
// 数据源：资源组\剧本\spine.json + 资源组\01_剧情流程图.md（§五 结局矩阵）
//         + 资源组\剧本\主线编排方案.md（§二 分幕表，交叉核对）
// 幕名 / 番外组名 / 结局一律取自上述资源组产物，不得自造。
// 几何不在本文件：节点盒与连线的 x/y/w/h 由 layout/screens/32_flowchart.json
// 声明（→ ui_layout.js / ui_layout.tjs），两侧同读同一份布局数据。
//
// ★★ 第 3 批（ISSUE-20260928-02 · 2026-09-28）· 旧元素寻址字段**已删除** ★★
// ------------------------------------------------------------------
//   下列六个字段**已从本文件与生成器一并删除**（不再是「保留待检」）：
//     `nodes[].el` / `branches[].el`（值 `flow.n01`…/`flow.b01`…）
//     `edges[].els`（值 `flow.seq*` / `flow.cv*` / `flow.bus_c` 数组）
//     `buses[].el`（值 `flow.bus_c`）
//     `links[].el`（值 `flow.seq01`…）
//     `layout.wrap_elements` / `layout.bypass_elements`（值 `flow.wrap_*` / `flow.e02_*`）
//   理由：这些值是 **M18 期屏版式**的元素 id，那批元素**早已不在屏数据里**
//   （现行屏是 `layout/screens/32_flowchart.json` 的 `fc.node.<NNNN>` 族，由
//   `工具\gen_flow_layout.py` 产出）⇒ 六个字段**没有任何消费者**：
//     · krkr 侧按它们寻址的函数（`uiFlowSyncFlowchart` / `uiFlowBuildScroll` /
//       `uiFlowScrollToCursor` / `uiFlowPage` / `uiFlowDrawMarkers`）已**整批删除**；
//     · 退场前的实测证据：每轮巡演日志都打 `滚动就绪：视口 0–0 ｜ 滚动元素 0 件`
//       （按旧 id 取不到任何元素 ⇒ 那一整套三态色环/滚动/标记框全是空转）。
//   ⇒ 现保留的只有**拓扑与语义**（`nodes`/`edges`/`links`/`buses`/`branches`/`fragments`
//     的 id 与 from/to/basis/sources 等），**不得**再据任何字段索引屏上元素 ——
//     屏上元素一律按 `fc.node.*` / `fc.entry.*` / `fc.frag<G>.*`；
//     机器可读的退场标记见数据顶层 `retired_addressing` / `retired_addressing_note`。
//   ⚠️ 缺口登记（G-5）：本文件属「**生成器产出后手工维护**」——生成器的 `BOX_PNG` 曾指向
//      4 个已不存在的 M18 期素材（`ui/x_gen_flownode_*.png`），盘上 `box_png` 已手工改成
//      存在的 `ui/x_ui_*` 件；本批已把盘上真值**回写生成器**（`BOX_PNG`），此后可安全重跑。
// ============================================================
window.UI_FLOW_DATA = {
  "retired_addressing": [
    "nodes[].el",
    "edges[].els",
    "buses[].el",
    "links[].el",
    "layout.wrap_elements",
    "layout.bypass_elements"
  ],
  "retired_addressing_note": "★ 第 3 批（ISSUE-20260928-02 · 2026-09-28）：上述六个**旧元素寻址字段已删除**（不只是「保留待检」）——它们的值是 M18 期屏版式的元素 id（`flow.n01`/`flow.seq01`/`flow.bus_c`/`flow.cv1_a`…），那批元素**早已不在屏数据里** ⇒ 这六个字段没有任何消费者（krkr 侧按它们寻址的函数已整批删除；实测证据：每轮巡演日志打 `滚动就绪：视口 0–0 ｜ 滚动元素 0 件`）。现行寻址：`fc.node.<NNNN>` / `fc.entry.*` / `fc.frag<G>.*`（生成器 `工具\\gen_flow_layout.py`）。",
  "generated_from": {
    "spine": "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/剧本/spine.json",
    "flow_md": "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/01_剧情流程图.md",
    "main_md": "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/剧本/主线编排方案.md"
  },
  "counts": {
    "acts": 11,
    "scenes_total": 712,
    "acts_scenes": 627,
    "excluded": 32,
    "side_stories": 53,
    "side_groups": 6,
    "branch_points": 50,
    "choices_in_spine": 147,
    "endings": 12
  },
  "rules": {
    "visited": "节点已到达（当前进度中该幕/分歧点已被走过）",
    "available": "节点未到达，但其任一入边的源节点已到达（= 可前往）",
    "locked": "节点未到达且所有入边的源节点均未到达（= 未解锁）",
    "current": "当前所在节点，单独用 @palette.node_current 外框标记",
    "priority": "已到达 > 可前往 > 未解锁（三态互斥，判定顺序固定）",
    "root": "无入边的节点（N01）恒为可前往（起始节点）",
    "progress_source": "已到达集合由 ui_state.tjs 的持久化机制保存（跨启动读回），键名 flow_visited",
    "edge": "连线颜色按**源节点是否已到达**判定：源与目标均已读=node_visited / 源已读（可通行）=node_available / 源未读=node_locked；汇流总线取「任一源节点已读」即 node_available，否则 node_locked",
    "layout": "**M18（2026-09-20）版式**：流程图改**单屏 2 列 × 7 行网格总览**（13 个节点全部一屏可见、无需滚动）。节点方框为 M11 交来的 1152×217–234 横条 PNG，经主代理授权用 `nine:{l:0,t:0,r:0,b:0}`（_schema.md §六 允许的「整图等比缩放」语义）缩到 **0.4785×**（552×104–112）。列优先填充，列内自上而下 = FLOW_ORDER。由此 E04/E05 两条跨行边在网格里无屏上元素，属**已知信息损失**（拓扑保留在 edges/buses 里）；相比 M14 多表达了真实边 E02（左侧旁路）。★ 第 3 批（2026-09-28）：M18 期元素 id（`flow.*`）的**寻址字段已整批删除**（`nodes[].el`/`edges[].els`/`buses[].el`/`links[].el`/`layout.wrap_elements`/`layout.bypass_elements`）—— 现行屏元素按 `fc.node.<NNNN>` 寻址。几何推导与可读性实测见 32_flowchart.json 的屏 note 与 _工作\\M18_报告.md。"
  },
  "acts": [
    {
      "act": 1,
      "node": "N01",
      "name": "前奏诗·框架剧与四短篇",
      "source": "otp",
      "scenes": 22,
      "lines": 3531,
      "note": "火烈鸟三人（西特拉斯/米内奥拉/椪柑）＋ＡＤさん主持的剧场框架，包裹四个角色短篇；前奏诗独有的 22 场景（D15 保留部分）。",
      "basis": "流程图 §4.1 调度顺序（MAIN→…→P01→P02→P03→P04→02→03→BURU01–04）与 §六 6.2（前奏诗为全系列最早，2008 先行作）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 2,
      "node": "N02",
      "name": "前奏诗·系统脚本",
      "source": "otp",
      "scenes": 5,
      "lines": 92,
      "note": "非剧情场景：引擎初始化/回想/制作人员/标题画面。**无剧情时序**，编程组按系统功能（菜单、回想、ED、标题）处理，不排入叙事顺序。",
      "basis": "流程图 §4.1 末行「系统」分组（gameinit/history/staff/title/title2）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 3,
      "node": "N03",
      "name": "本篇·序文",
      "source": "ot",
      "scenes": 1,
      "lines": 2,
      "note": "s00「序文 ～俺たちに翼はない～」，全篇开篇。",
      "basis": "流程图 §4.2 脚本分组表（s00 1 脚本 / 2 槽）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 4,
      "node": "N04",
      "name": "本篇·s01 鹰志线",
      "source": "ot",
      "scenes": 114,
      "lines": 13969,
      "note": "羽田鹰志 → 渡来明日香（主）/ 山科京（副）；含明日香 END（s01_16a）与京 END（s01_18a）。**与 s02/s03 为同一时间带的平行线**，先后由编程组按路线选择决定。（W10b：亚衣线 `s03c` 不是独立平行线，而是 `s03` 内的分支，见第 6/7 幕说明。）",
      "basis": "流程图 §4.2 s01 章节序列；§六 6.1 日期锚点 12/3、12/24",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 5,
      "node": "N05",
      "name": "本篇·s02 鹫介线",
      "source": "ot",
      "scenes": 83,
      "lines": 12327,
      "note": "千岁鹫介 → 玉泉日和子（主）/ 日野英里子、望月纪奈子（副）；日和子 END（s02_16a）。**与 s01/s03 平行**（W10b：`s03c` 属 `s03` 内分支，不在此平行之列）。",
      "basis": "流程图 §4.2 s02 章节序列；§六 6.1 日期锚点 11/29、12/4",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 6,
      "node": "N06",
      "name": "本篇·s03 隼人线",
      "source": "ot",
      "scenes": 95,
      "lines": 17389,
      "note": "成田隼人 → 凤鸣（主）；鸣 END（s03_22a）。含大量 (N)/(C) 成对变体脚本。**与 s01/s02 平行**；**亚衣线 `s03c` 是 s03 内的分支**——`s03_09a` 有 (N)/(C) 两变体：`s03_09a1`「世间万象（Ｎ）」继续鸣线（`next=s03_09b`），`s03_09a2`「世间种种（Ｃ）」`next=['s03c_01a']` 分叉到亚衣线（W10b 实测更正；见 §七.2）。",
      "basis": "流程图 §4.2 s03 章节序列；§六 6.1 日期锚点 11/22–11/28、12/1；亚衣线入口＝`scene_ot.jsonl` 的 `s03_09a2.next=['s03c_01a']`（W10b 实测）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 7,
      "node": "N07",
      "name": "亚衣线·s03c（R 版 55 场景版）",
      "source": "otr",
      "scenes": 55,
      "lines": 6911,
      "note": "香田亚衣线。**取自 scene_otr.jsonl（R 版 55 场景），不在 scene_ot 内**——21 共有 + 3 分支 + 31 新增（D14：共有取本篇译文、新增取 R 版本项目新译）。亚衣 END（s03c_20a）。**入口＝`s03_09a2`「世间种种（Ｃ）」→ `next=['s03c_01a']`**（`scene_ot.jsonl` 实测，W10b 更正）——即**亚衣线是 `s03` 隼人线内的分支**，**不是与 s01/s02/s03 并列的第四条平行线**。",
      "basis": "亚衣线入口＝`scene_ot.jsonl` 的 `s03_09a2.next=['s03c_01a']`（W10b 实测；`s03_09a1` 为 (N) 变体继续鸣线）；§六 6.1 日期锚点 11/22–11/26（s03c_01c）；流程图 §4.2 已于 2026-09-19 同步更正",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 8,
      "node": "N08",
      "name": "PSV 美咲线（同期分支）",
      "source": "otv",
      "scenes": 31,
      "lines": 4931,
      "note": "林田美咲线，M01–M09 + P03 四短篇。**承 s01 鹰志线 Bad End（S01_14J2）的同期分支**（D7 完全采用并并入主线）。线性、无剧情选择支；美咲 END（M09_01/M09_02）。",
      "basis": "流程图 §4.4；§六 6.2（PSV 美咲线为同期鷹志线分支，游戏内 12/13–12/24）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 9,
      "node": "N09",
      "name": "大路线 s04（最终章）",
      "source": "ot",
      "scenes": 74,
      "lines": 11993,
      "note": "多元世界真相 → 假统合 → 真·兄妹再会 → 不完全统合；**收束全线的唯一真结局**。真 END（s04_28b → s04_29a）。",
      "basis": "流程图 §4.2 s04 章节序列；§六 6.2（12/5 起，经新年 → 仮統合）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 10,
      "node": "N10",
      "name": "After Story·主线",
      "source": "ota",
      "scenes": 119,
      "lines": 13139,
      "note": "11/12/13/14 对决四篇（鹰志/鹫介/隼人/洋治）＋ 21 美咲 ＋ 24 最终统合线（24_1a「仮統合の崩壊」→ 24_5b G-END / 24_5c B-END）。",
      "basis": "流程图 §4.5 五层结构 A/B 层；§六 6.2（s04 之后；24_1a 明示接「仮統合」）",
      "cross_check": "与分幕表一致"
    },
    {
      "act": 11,
      "node": "N11",
      "name": "涅布＊プラス 明日香篇",
      "source": "np",
      "scenes": 28,
      "lines": 1961,
      "note": "毕业后 2 月；a01–a06 子篇目菜单式短篇集（start_oretuba 为菜单脚本，34 条选择支全部挂于该脚本）。",
      "basis": "流程图 §4.6；§六 6.2（毕业后·2 月，毕业前）",
      "cross_check": "与分幕表一致"
    }
  ],
  "nodes": [
    {
      "id": "N01",
      "kind": "act",
      "act": 1,
      "label": "前奏诗·框架剧与四短篇",
      "sub": "otp · 22 场景 / 3531 行",
      "box": "normal",
      "box_cn": "一般剧情",
      "box_png": "ui/x_ui_node_section_off.png",
      "box_reason": "acts[0].note：火烈鸟三人＋ＡＤさん主持的剧场框架，包裹四个角色短篇；§五 结局矩阵无其结局 → 开篇铺垫，一般剧情",
      "row": 0,
      "grid_col": 0,
      "grid_row": 0
    },
    {
      "id": "N02",
      "kind": "act",
      "act": 2,
      "label": "前奏诗·系统脚本",
      "sub": "otp · 5 场景 / 92 行",
      "box": "normal",
      "box_cn": "一般剧情",
      "box_png": "ui/x_ui_node_section_off.png",
      "box_reason": "acts[1].note：引擎初始化/回想/制作人员/标题画面，**无剧情时序**，不排入叙事顺序；§五 无其结局 → 一般剧情",
      "row": 1,
      "grid_col": 0,
      "grid_row": 1
    },
    {
      "id": "N03",
      "kind": "act",
      "act": 3,
      "label": "本篇·序文",
      "sub": "ot · 1 场景 / 2 行",
      "box": "normal",
      "box_cn": "一般剧情",
      "box_png": "ui/x_ui_node_section_off.png",
      "box_reason": "acts[2].note：s00「序文 ～俺たちに翼はない～」，全篇开篇（1 场景 / 2 槽）；§五 无其结局 → 一般剧情",
      "row": 2,
      "grid_col": 0,
      "grid_row": 2
    },
    {
      "id": "N04",
      "kind": "act",
      "act": 4,
      "label": "本篇·s01 鹰志线",
      "sub": "ot · 114 场景 / 13969 行",
      "box": "goodend",
      "box_cn": "GOOD END（包括女主角非坏结局的结尾）",
      "box_png": "ui/x_ui_label_off.png",
      "box_reason": "acts[3].note：含明日香 END（s01_16a）与京 END（s01_18a）；§五 结局矩阵两行均为女主角非坏结局 → GOOD END",
      "row": 3,
      "grid_col": 0,
      "grid_row": 3
    },
    {
      "id": "N05",
      "kind": "act",
      "act": 5,
      "label": "本篇·s02 鹫介线",
      "sub": "ot · 83 场景 / 12327 行",
      "box": "goodend",
      "box_cn": "GOOD END（包括女主角非坏结局的结尾）",
      "box_png": "ui/x_ui_label_off.png",
      "box_reason": "acts[4].note：日和子 END（s02_16a）；§五 结局矩阵 → GOOD END",
      "row": 6,
      "grid_col": 0,
      "grid_row": 6
    },
    {
      "id": "N06",
      "kind": "act",
      "act": 6,
      "label": "本篇·s03 隼人线",
      "sub": "ot · 95 场景 / 17389 行",
      "box": "goodend",
      "box_cn": "GOOD END（包括女主角非坏结局的结尾）",
      "box_png": "ui/x_ui_label_off.png",
      "box_reason": "acts[5].note：鸣 END（s03_22a）；§五 结局矩阵 → GOOD END",
      "row": 7,
      "grid_col": 1,
      "grid_row": 0
    },
    {
      "id": "N07",
      "kind": "act",
      "act": 7,
      "label": "亚衣线·s03c（R 版 55 场景版）",
      "sub": "otr · 55 场景 / 6911 行",
      "box": "goodend",
      "box_cn": "GOOD END（包括女主角非坏结局的结尾）",
      "box_png": "ui/x_ui_label_off.png",
      "box_reason": "acts[6].note：亚衣 END（s03c_20a「エピローグ～隼人君と亜衣～」）；§五 结局矩阵 → GOOD END",
      "row": 9,
      "grid_col": 1,
      "grid_row": 2
    },
    {
      "id": "N08",
      "kind": "act",
      "act": 8,
      "label": "PSV 美咲线（同期分支）",
      "sub": "otv · 31 场景 / 4931 行",
      "box": "goodend",
      "box_cn": "GOOD END（包括女主角非坏结局的结尾）",
      "box_png": "ui/x_ui_label_off.png",
      "box_reason": "acts[7].note：美咲 END（M09_01 / M09_02）；§五 结局矩阵 → GOOD END。（备选判定：本线入口为 s01 鹰志编 Bad End「S01_14J2」，若按「入口结局定档」则应标 badend —— 见 M14 报告「备选判定」）",
      "row": 5,
      "grid_col": 0,
      "grid_row": 5
    },
    {
      "id": "N09",
      "kind": "act",
      "act": 9,
      "label": "大路线 s04（最终章）",
      "sub": "ot · 74 场景 / 11993 行",
      "box": "goodend",
      "box_cn": "GOOD END（包括女主角非坏结局的结尾）",
      "box_png": "ui/x_ui_label_off.png",
      "box_reason": "acts[8].note：真 END（s04_28b → s04_29a），**收束全线的唯一真结局**；§五 结局矩阵 → GOOD END",
      "row": 10,
      "grid_col": 1,
      "grid_row": 3
    },
    {
      "id": "N10",
      "kind": "act",
      "act": 10,
      "label": "After Story·主线",
      "sub": "ota · 119 场景 / 13139 行",
      "box": "badend",
      "box_cn": "BAD END / 普通结局",
      "box_png": "ui/x_ui_node_select_off.png",
      "box_reason": "acts[9].note：24 最终统合线含 24_5c「Ｂ－ＥＮＤ：俺の涙よ誰かに届け」（失败，GAME OVER）；§五 结局矩阵 → BAD END。（该幕同时含 24_5b「Ｇ－ＥＮＤ」——见 M14 报告「备选判定」）",
      "row": 11,
      "grid_col": 1,
      "grid_row": 4
    },
    {
      "id": "N11",
      "kind": "act",
      "act": 11,
      "label": "涅布＊プラス 明日香篇",
      "sub": "np · 28 场景 / 1961 行",
      "box": "normal",
      "box_cn": "一般剧情",
      "box_png": "ui/x_ui_node_section_off.png",
      "box_reason": "acts[10].note：子篇目菜单式短篇集（start_oretuba 为菜单脚本，34 条选择支挂其下）；§五 结局矩阵未列其结局 → 一般剧情",
      "row": 12,
      "grid_col": 1,
      "grid_row": 5
    },
    {
      "id": "B01",
      "scene": "ot_s01_02c",
      "kind": "branch",
      "route": "s01 鹰志线",
      "options": 2,
      "choices": [
        "为了国家与民众",
        "为了阿斯嘉公主"
      ],
      "label": "分歧点 s01 鹰志线",
      "sub": "2 选项 · ot_s01_02c",
      "note": "s01 鹰志线内分歧点：国家 / 阿斯嘉公主 二选一（spine.json branch_points[0]）",
      "box": "important",
      "box_cn": "重要章节（影响后续剧情发展）",
      "box_png": "ui/x_ui_node_frag_off.png",
      "box_reason": "spine.json branch_points[0] ot_s01_02c：s01 鹰志线内 2 选项关键分歧点，决定后续（其 Bad End 分支即 PSV 美咲线入口）→ 重要章节",
      "row": 4,
      "grid_col": 0,
      "grid_row": 4
    },
    {
      "id": "B02",
      "scene": "s03_09a",
      "kind": "branch",
      "route": "",
      "options": 0,
      "choices": [],
      "label": "分歧点 s03_09a",
      "sub": "0 选项 · s03_09a",
      "note": "s03 隼人线内分歧点：世间万象（Ｎ）继续鸣线 / 世间种种（Ｃ）分叉到亚衣线 s03c（主线编排方案.md §二 第 6 幕说明，W10b 实测）",
      "box": "important",
      "box_cn": "重要章节（影响后续剧情发展）",
      "box_png": "ui/x_ui_node_frag_off.png",
      "box_reason": "s03_09a 的 (N)/(C) 两变体：s03_09a1 继续鸣线 / s03_09a2 → next=['s03c_01a'] 分叉亚衣线（W10b 实测，主线编排方案.md §二 第 6/7 幕说明）→ 重要章节",
      "row": 8,
      "grid_col": 1,
      "grid_row": 1
    }
  ],
  "edges": [
    {
      "id": "E01",
      "from": "N01",
      "to": "N02",
      "basis": "幕 2 为前奏诗系统脚本，挂在幕 1 之后作旁支（主线编排方案.md §二 第 2 幕说明：无剧情时序）"
    },
    {
      "id": "E02",
      "from": "N01",
      "to": "N03",
      "basis": "主线顺序 1 → 3（主线编排方案.md §三）"
    },
    {
      "id": "E03",
      "from": "N03",
      "to": "N04",
      "basis": "主线顺序 3 → 4（主线编排方案.md §三）"
    },
    {
      "id": "E04",
      "from": "N03",
      "to": "N05",
      "basis": "主线顺序 3 → 5（s01/s02/s03 为同一时间带的平行线，§二 第 4/5 幕说明）"
    },
    {
      "id": "E05",
      "from": "N03",
      "to": "N06",
      "basis": "主线顺序 3 → 6（主线编排方案.md §三）"
    },
    {
      "id": "E06",
      "from": "N04",
      "to": "B01",
      "basis": "s01 线内分歧点 ot_s01_02c（spine.json branch_points[0]）"
    },
    {
      "id": "E07",
      "from": "B01",
      "to": "N08",
      "basis": "PSV 美咲线承 s01 鹰志线 Bad End（S01_14J2）的同期分支（§二 第 8 幕说明）"
    },
    {
      "id": "E08",
      "from": "N06",
      "to": "B02",
      "basis": "s03 线内分歧点 s03_09a（主线编排方案.md §二 第 6 幕说明）"
    },
    {
      "id": "E09",
      "from": "B02",
      "to": "N07",
      "basis": "亚衣线入口 s03_09a2 → next=['s03c_01a']（W10b 实测更正，§二 第 7 幕说明）"
    },
    {
      "id": "E10",
      "from": "N04",
      "to": "N09",
      "basis": "s04 收束全线（§二 第 9 幕说明：唯一真结局）"
    },
    {
      "id": "E11",
      "from": "N08",
      "to": "N09",
      "basis": "s04 收束全线（含 PSV 美咲线）"
    },
    {
      "id": "E12",
      "from": "N05",
      "to": "N09",
      "basis": "s04 收束全线"
    },
    {
      "id": "E13",
      "from": "N06",
      "to": "N09",
      "basis": "s04 收束全线"
    },
    {
      "id": "E14",
      "from": "N07",
      "to": "N09",
      "basis": "s04 收束全线（含亚衣线）"
    },
    {
      "id": "E15",
      "from": "N09",
      "to": "N10",
      "basis": "After Story 在 s04 之后（24_1a 明示接「仮統合」；§二 第 10 幕说明）"
    },
    {
      "id": "E16",
      "from": "N10",
      "to": "N11",
      "basis": "涅布＊プラス 明日香篇在 AS 之后（毕业后 2 月；§二 第 11 幕说明）"
    }
  ],
  "links": [
    {
      "from": "N01",
      "to": "N02",
      "edge": "E01"
    },
    {
      "from": "N02",
      "to": "N03",
      "edge": ""
    },
    {
      "from": "N03",
      "to": "N04",
      "edge": "E03"
    },
    {
      "from": "N04",
      "to": "B01",
      "edge": "E06"
    },
    {
      "from": "B01",
      "to": "N08",
      "edge": "E07"
    },
    {
      "from": "N08",
      "to": "N05",
      "edge": ""
    },
    {
      "from": "N06",
      "to": "B02",
      "edge": "E08"
    },
    {
      "from": "B02",
      "to": "N07",
      "edge": "E09"
    },
    {
      "from": "N07",
      "to": "N09",
      "edge": "E14"
    },
    {
      "from": "N09",
      "to": "N10",
      "edge": "E15"
    },
    {
      "from": "N10",
      "to": "N11",
      "edge": "E16"
    }
  ],
  "buses": [
    {
      "id": "BUS_C1C2",
      "sources": [
        "N03"
      ],
      "note": "N03 之后三条平行线（s01/s02/s03）共用的汇流纵线。**M18：2×7 网格仍无法表达 ⇒ 无屏上元素**（`el` 字段已按第 3 批删除）"
    },
    {
      "id": "BUS_C2C3",
      "sources": [
        "N04",
        "N05",
        "N06",
        "N07",
        "N08"
      ],
      "note": "五条线（s01/s02/s03/亚衣/PSV）汇入 s04 的汇流纵线；M18 画在**列间空隙的中线 x=960**，远端四源各用短横条接入，另一条引入段接到 N09 左边界；N07→N09 与 N09 同列相邻，故不进总线（`el` 字段已按第 3 批删除）"
    }
  ],
  "branches": [
    {
      "id": "B01",
      "scene": "ot_s01_02c",
      "kind": "branch",
      "route": "s01 鹰志线",
      "options": 2,
      "choices": [
        "为了国家与民众",
        "为了阿斯嘉公主"
      ],
      "label": "分歧点 s01 鹰志线",
      "sub": "2 选项 · ot_s01_02c",
      "note": "s01 鹰志线内分歧点：国家 / 阿斯嘉公主 二选一（spine.json branch_points[0]）",
      "box": "important",
      "box_cn": "重要章节（影响后续剧情发展）",
      "box_png": "ui/x_ui_node_frag_off.png",
      "box_reason": "spine.json branch_points[0] ot_s01_02c：s01 鹰志线内 2 选项关键分歧点，决定后续（其 Bad End 分支即 PSV 美咲线入口）→ 重要章节",
      "row": 4,
      "grid_col": 0,
      "grid_row": 4
    },
    {
      "id": "B02",
      "scene": "s03_09a",
      "kind": "branch",
      "route": "",
      "options": 0,
      "choices": [],
      "label": "分歧点 s03_09a",
      "sub": "0 选项 · s03_09a",
      "note": "s03 隼人线内分歧点：世间万象（Ｎ）继续鸣线 / 世间种种（Ｃ）分叉到亚衣线 s03c（主线编排方案.md §二 第 6 幕说明，W10b 实测）",
      "box": "important",
      "box_cn": "重要章节（影响后续剧情发展）",
      "box_png": "ui/x_ui_node_frag_off.png",
      "box_reason": "s03_09a 的 (N)/(C) 两变体：s03_09a1 继续鸣线 / s03_09a2 → next=['s03c_01a'] 分叉亚衣线（W10b 实测，主线编排方案.md §二 第 6/7 幕说明）→ 重要章节",
      "row": 8,
      "grid_col": 1,
      "grid_row": 1
    }
  ],
  "box_legend": [
    {
      "type": "normal",
      "png": "ui/x_ui_node_section_off.png",
      "cn": "一般剧情"
    },
    {
      "type": "badend",
      "png": "ui/x_ui_node_select_off.png",
      "cn": "BAD END / 普通结局"
    },
    {
      "type": "important",
      "png": "ui/x_ui_node_frag_off.png",
      "cn": "重要章节（影响后续剧情发展）"
    },
    {
      "type": "goodend",
      "png": "ui/x_ui_label_off.png",
      "cn": "GOOD END（包括女主角非坏结局的结尾）"
    }
  ],
  "layout": {
    "version": "M18-2026-09-20",
    "mode": "single-screen-grid",
    "cols": 2,
    "rows": 7,
    "row_order": [
      "N01",
      "N02",
      "N03",
      "N04",
      "B01",
      "N08",
      "N05",
      "N06",
      "B02",
      "N07",
      "N09",
      "N10",
      "N11"
    ],
    "grid": {
      "N01": [
        0,
        0
      ],
      "N02": [
        0,
        1
      ],
      "N03": [
        0,
        2
      ],
      "N04": [
        0,
        3
      ],
      "B01": [
        0,
        4
      ],
      "N08": [
        0,
        5
      ],
      "N05": [
        0,
        6
      ],
      "N06": [
        1,
        0
      ],
      "B02": [
        1,
        1
      ],
      "N07": [
        1,
        2
      ],
      "N09": [
        1,
        3
      ],
      "N10": [
        1,
        4
      ],
      "N11": [
        1,
        5
      ]
    },
    "note": "M18 单屏网格版式：13 个节点按 grid（列优先）排进 2 列 × 7 行，全部一屏可见、无需滚动。方框由 1152×217–234 等比缩到 0.4785×（552×104–112，用 nine:{l:0,t:0,r:0,b:0} 表达整图缩放）。同列相邻节点用纵向连接条（links）；跨列用当时的三段折线；E02 用当时左侧旁路；五线汇入 s04 用列间空隙中线 x=960 的汇流总线 + 四条短横条。E04/E05 在网格中无屏上元素 —— 拓扑保留在 edges/buses 里，属已知信息损失。★ 第 3 批（2026-09-28）：M18 期元素 id（`flow.*`）的**寻址字段整批删除**，上面提到的连线元素名只作历史背景；现行屏元素一律按 `fc.node.*` / `fc.entry.*` / `fc.frag<G>.*`（`工具\\gen_flow_layout.py` 产出）寻址。"
  },
  "endings": [
    {
      "ending": "明日香 END",
      "script": "s01_16a",
      "name_jp": "エピローグ～羽田君と渡来さん～",
      "meaning": "鷹志 × 明日香"
    },
    {
      "ending": "京 END",
      "script": "s01_18a",
      "name_jp": "エピローグ～鷹志君と京ちゃん～",
      "meaning": "鷹志 × 山科京"
    },
    {
      "ending": "日和子 END",
      "script": "s02_16a",
      "name_jp": "エピローグ～シュウちゃんと日和子さん～",
      "meaning": "鷲介 × 日和子"
    },
    {
      "ending": "鳴 END",
      "script": "s03_22a",
      "name_jp": "エピローグ～隼人さんと鳴～",
      "meaning": "隼人 × 鳴"
    },
    {
      "ending": "亜衣 END（原版）",
      "script": "s03c_05a",
      "name_jp": "レーゾン・デートル",
      "meaning": "亜衣线收束（21 场景版）"
    },
    {
      "ending": "亜衣 END（R 版）",
      "script": "s03c_20a",
      "name_jp": "エピローグ～隼人君と亜衣～",
      "meaning": "R 版亜衣线正式结局"
    },
    {
      "ending": "美咲 END（PSV）",
      "script": "M09_01` / `M09_02",
      "name_jp": "エピローグ～林田さんと僕～ / 解纜～バーサス羽田鷹志～",
      "meaning": "美咲线"
    },
    {
      "ending": "解纜（各线收束）",
      "script": "s01_19a` / `s02_17a` / `s03_23a",
      "name_jp": "解纜～バーサス各主角～",
      "meaning": "人格统合 / 向观察者告别"
    },
    {
      "ending": "真 END（大路线）",
      "script": "s04_28b` → `s04_29a",
      "name_jp": "エピローグ～お兄ちゃんと小鳩～ → 解纜～バーサス羽田鷹志たち～",
      "meaning": "五人走向不完全统合，与妹妹重逢"
    },
    {
      "ending": "AS ヨージ线收束",
      "script": "14_8a",
      "name_jp": "閉幕～バーサス羽田ヨージ～",
      "meaning": "ヨージ × 小鳩"
    },
    {
      "ending": "AS G-END",
      "script": "24_5b",
      "name_jp": "Ｇ－ＥＮＤ：やったねお兄ちゃん",
      "meaning": "小鳩救助成功"
    },
    {
      "ending": "AS B-END",
      "script": "24_5c",
      "name_jp": "Ｂ－ＥＮＤ：俺の涙よ誰かに届け",
      "meaning": "失败，GAME OVER"
    }
  ],
  "ending_note": "§五 结局矩阵 12 行",
  "fragments": {
    "total": 53,
    "group_count": 6,
    "groups": [
      {
        "name": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "count": 7
      },
      {
        "name": "番外·苍女X日",
        "count": 7
      },
      {
        "name": "番外·各线 after",
        "count": 4
      },
      {
        "name": "番外·群像（新年行军 / 格兰玛尼耶）",
        "count": 10
      },
      {
        "name": "番外·おれつば剧场",
        "count": 5
      },
      {
        "name": "番外·おまけ（成人向）",
        "count": 20
      }
    ],
    "onscreen": 40,
    "cells": [
      {
        "index": 0,
        "row": 0,
        "col": 0,
        "scene_id": "ota_22_1a",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "如今我们的胸部再度开始",
        "title_jp": "今ふたたび俺たちのおっぱいが始まる",
        "source": "ota",
        "script": "22_1a"
      },
      {
        "index": 1,
        "row": 0,
        "col": 1,
        "scene_id": "ota_22_2a",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "回归招牌女孩",
        "title_jp": "出戻り看板娘",
        "source": "ota",
        "script": "22_2a"
      },
      {
        "index": 2,
        "row": 0,
        "col": 2,
        "scene_id": "ota_22_2b",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "超级·上等·帮手",
        "title_jp": "ハイパー・アッパー・ヘルパー",
        "source": "ota",
        "script": "22_2b"
      },
      {
        "index": 3,
        "row": 0,
        "col": 3,
        "scene_id": "ota_22_2c",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "忙碌女编辑的烦恼",
        "title_jp": "多忙なる女性編集の悩み",
        "source": "ota",
        "script": "22_2c"
      },
      {
        "index": 4,
        "row": 0,
        "col": 4,
        "scene_id": "ota_22_2d",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "恐怖！怪人黑内裤大猩猩的逆袭",
        "title_jp": "恐怖！　怪人黒パンツゴリラの逆襲",
        "source": "ota",
        "script": "22_2d"
      },
      {
        "index": 5,
        "row": 1,
        "col": 0,
        "scene_id": "ota_22_2e",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "不平安的平安夜",
        "title_jp": "Ｎｏｔ　Ｓｉｌｅｎｔ　Ｎｉｇｈｔ",
        "source": "ota",
        "script": "22_2e"
      },
      {
        "index": 6,
        "row": 1,
        "col": 1,
        "scene_id": "ota_22_2f",
        "group": "番外·阿雷克桑德平安夜（おっぱい系列）",
        "title_cn": "我们的奶子啊直到永远",
        "title_jp": "俺たちのおっぱいよ永遠に",
        "source": "ota",
        "script": "22_2f"
      },
      {
        "index": 7,
        "row": 1,
        "col": 2,
        "scene_id": "ota_23_1a",
        "group": "番外·苍女X日",
        "title_cn": "４天前：今日的苍女",
        "title_jp": "４日前：今日のアオ女",
        "source": "ota",
        "script": "23_1a"
      },
      {
        "index": 8,
        "row": 1,
        "col": 3,
        "scene_id": "ota_23_1b",
        "group": "番外·苍女X日",
        "title_cn": "３天前：放学后萨满",
        "title_jp": "３日前：放課後シャーマニック",
        "source": "ota",
        "script": "23_1b"
      },
      {
        "index": 9,
        "row": 1,
        "col": 4,
        "scene_id": "ota_23_1c",
        "group": "番外·苍女X日",
        "title_cn": "２天前：没有回报的努力",
        "title_jp": "２日前：報われない努力",
        "source": "ota",
        "script": "23_1c"
      },
      {
        "index": 10,
        "row": 2,
        "col": 0,
        "scene_id": "ota_23_1d",
        "group": "番外·苍女X日",
        "title_cn": "２天前：黄昏忧郁",
        "title_jp": "２日前：黄昏メランコリック",
        "source": "ota",
        "script": "23_1d"
      },
      {
        "index": 11,
        "row": 2,
        "col": 1,
        "scene_id": "ota_23_1e",
        "group": "番外·苍女X日",
        "title_cn": "１天前：彷徨的低年级生",
        "title_jp": "１日前：さまよえる下級生",
        "source": "ota",
        "script": "23_1e"
      },
      {
        "index": 12,
        "row": 2,
        "col": 2,
        "scene_id": "ota_23_1f",
        "group": "番外·苍女X日",
        "title_cn": "１天前：去问问阿基米德",
        "title_jp": "１日前：アルキメデスに聞いてみろ",
        "source": "ota",
        "script": "23_1f"
      },
      {
        "index": 13,
        "row": 2,
        "col": 3,
        "scene_id": "ota_23_2a",
        "group": "番外·苍女X日",
        "title_cn": "Ｘ日：蹦跳的小姑娘们",
        "title_jp": "Ｘデー：ジャンピング小娘たち",
        "source": "ota",
        "script": "23_2a"
      },
      {
        "index": 14,
        "row": 2,
        "col": 4,
        "scene_id": "ota_31_1",
        "group": "番外·各线 after",
        "title_cn": "那天的思念禁止覆盖",
        "title_jp": "あの日の想いは上書き禁止",
        "source": "ota",
        "script": "31_1"
      },
      {
        "index": 15,
        "row": 3,
        "col": 0,
        "scene_id": "ota_32_1",
        "group": "番外·各线 after",
        "title_cn": "每天都是浪漫书店篇",
        "title_jp": "毎日がロマンス書店編",
        "source": "ota",
        "script": "32_1"
      },
      {
        "index": 16,
        "row": 3,
        "col": 1,
        "scene_id": "ota_33_1",
        "group": "番外·各线 after",
        "title_cn": "归来的成田工务店",
        "title_jp": "帰ってきた成田工務店",
        "source": "ota",
        "script": "33_1"
      },
      {
        "index": 17,
        "row": 3,
        "col": 2,
        "scene_id": "ota_34_1",
        "group": "番外·各线 after",
        "title_cn": "公主·滚动雷霆",
        "title_jp": "プリンセス・ザ・ローリングサンダー",
        "source": "ota",
        "script": "34_1"
      },
      {
        "index": 18,
        "row": 3,
        "col": 3,
        "scene_id": "ota_41_1",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "羽田部队１２３１新年行军",
        "title_jp": "羽田部隊１２３１ニューイヤー行軍",
        "source": "ota",
        "script": "41_1"
      },
      {
        "index": 19,
        "row": 3,
        "col": 4,
        "scene_id": "ota_41_2",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "身高１４０厘米的世界",
        "title_jp": "身長１４０センチの世界",
        "source": "ota",
        "script": "41_2"
      },
      {
        "index": 20,
        "row": 4,
        "col": 0,
        "scene_id": "ota_41_3",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "山科队员的脱离",
        "title_jp": "山科隊員の離脱",
        "source": "ota",
        "script": "41_3"
      },
      {
        "index": 21,
        "row": 4,
        "col": 1,
        "scene_id": "ota_41_4",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "狮子心王即将出阵",
        "title_jp": "獅子心王いざ出陣す",
        "source": "ota",
        "script": "41_4"
      },
      {
        "index": 22,
        "row": 4,
        "col": 2,
        "scene_id": "ota_41_5",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "ＶＳ生剥鬼世纪对决特别篇",
        "title_jp": "ＶＳなまはげ世紀の対決スペシャル",
        "source": "ota",
        "script": "41_5"
      },
      {
        "index": 23,
        "row": 4,
        "col": 3,
        "scene_id": "ota_42_1",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "没有面对的报应",
        "title_jp": "向きあわなかった酬い",
        "source": "ota",
        "script": "42_1"
      },
      {
        "index": 24,
        "row": 4,
        "col": 4,
        "scene_id": "ota_42_2",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "格兰·玛尼耶（ＨＡＷＫ）",
        "title_jp": "グラン・マルニエ（ＨＡＷＫ）",
        "source": "ota",
        "script": "42_2"
      },
      {
        "index": 25,
        "row": 5,
        "col": 0,
        "scene_id": "ota_42_3",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "格兰·玛尼耶（ＥＡＧＬＥ）",
        "title_jp": "グラン・マルニエ（ＥＡＧＬＥ）",
        "source": "ota",
        "script": "42_3"
      },
      {
        "index": 26,
        "row": 5,
        "col": 1,
        "scene_id": "ota_42_4",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "格兰玛·露尼耶（ＦＡＬＣＯＮ）",
        "title_jp": "グランマ・ルニエ（ＦＡＬＣＯＮ）",
        "source": "ota",
        "script": "42_4"
      },
      {
        "index": 27,
        "row": 5,
        "col": 2,
        "scene_id": "ota_42_5",
        "group": "番外·群像（新年行军 / 格兰玛尼耶）",
        "title_cn": "大家和和气气八等分",
        "title_jp": "みんな仲よく八等分",
        "source": "ota",
        "script": "42_5"
      },
      {
        "index": 28,
        "row": 5,
        "col": 3,
        "scene_id": "ota_50_1",
        "group": "番外·おれつば剧场",
        "title_cn": "没翅剧场～开幕篇～",
        "title_jp": "おれつば劇場～開幕編～",
        "source": "ota",
        "script": "50_1"
      },
      {
        "index": 29,
        "row": 5,
        "col": 4,
        "scene_id": "ota_51_1",
        "group": "番外·おれつば剧场",
        "title_cn": "没翅剧场～女人们的决战～",
        "title_jp": "おれつば劇場～女たちの決戦～",
        "source": "ota",
        "script": "51_1"
      },
      {
        "index": 30,
        "row": 6,
        "col": 0,
        "scene_id": "ota_52_1",
        "group": "番外·おれつば剧场",
        "title_cn": "没翅剧场～小丑们的喜剧～",
        "title_jp": "おれつば劇場～道化師たちの喜劇～",
        "source": "ota",
        "script": "52_1"
      },
      {
        "index": 31,
        "row": 6,
        "col": 1,
        "scene_id": "ota_53_1",
        "group": "番外·おれつば剧场",
        "title_cn": "没翅剧场～笨蛋们的友情～",
        "title_jp": "おれつば劇場～馬鹿野郎たちの友情～",
        "source": "ota",
        "script": "53_1"
      },
      {
        "index": 32,
        "row": 6,
        "col": 2,
        "scene_id": "ota_54_1",
        "group": "番外·おれつば剧场",
        "title_cn": "没翅剧场～终幕篇～",
        "title_jp": "おれつば劇場～終幕編～",
        "source": "ota",
        "script": "54_1"
      },
      {
        "index": 33,
        "row": 6,
        "col": 3,
        "scene_id": "ota_61_1a",
        "group": "番外·おまけ（成人向）",
        "title_cn": "在宾馆街的一角",
        "title_jp": "ホテル街のほとりで",
        "source": "ota",
        "script": "61_1a"
      },
      {
        "index": 34,
        "row": 6,
        "col": 4,
        "scene_id": "ota_61_1b",
        "group": "番外·おまけ（成人向）",
        "title_cn": "第一次的休息",
        "title_jp": "はじめてのご休憩",
        "source": "ota",
        "script": "61_1b"
      },
      {
        "index": 35,
        "row": 7,
        "col": 0,
        "scene_id": "ota_61_1c",
        "group": "番外·おまけ（成人向）",
        "title_cn": "不是澡堂却摆出战斗架势",
        "title_jp": "銭湯でもないのに戦闘体勢",
        "source": "ota",
        "script": "61_1c"
      },
      {
        "index": 36,
        "row": 7,
        "col": 1,
        "scene_id": "ota_61_2a",
        "group": "番外·おまけ（成人向）",
        "title_cn": "近况～鹰志君与小京～",
        "title_jp": "近況　～鷹志君と京ちゃん～",
        "source": "ota",
        "script": "61_2a"
      },
      {
        "index": 37,
        "row": 7,
        "col": 2,
        "scene_id": "ota_61_2b",
        "group": "番外·おまけ（成人向）",
        "title_cn": "和京同学卿卿我我",
        "title_jp": "いちゃいちゃ京さん",
        "source": "ota",
        "script": "61_2b"
      },
      {
        "index": 38,
        "row": 7,
        "col": 3,
        "scene_id": "ota_62_1a",
        "group": "番外·おまけ（成人向）",
        "title_cn": "情书·来自小日和",
        "title_jp": "ラブレター・フロム・ひょこ",
        "source": "ota",
        "script": "62_1a"
      },
      {
        "index": 39,
        "row": 7,
        "col": 4,
        "scene_id": "ota_62_1b",
        "group": "番外·おまけ（成人向）",
        "title_cn": "无论何时·棱镜（性的意义上）",
        "title_jp": "いつだってプリズム（性的な意味で）",
        "source": "ota",
        "script": "62_1b"
      }
    ],
    "note": "番外（Fragment）：spine.json side_stories[] 共 53 条 / 6 组。M11 交来的 Fragment 底图实测为 **5 列 × 8 行 = 40 格**，故本期**只上屏前 40 条**（cells，标题逐条取自 spine.json，不得手写）；余 13 条的呈现方式（第 2 页 / 滚动 / 另开屏）待定，见 M14 报告。"
  },
  "note": "幕名/番外组名/结局一律取自资源组产物（见 generated_from），M4/M14 不得自造。"
};
