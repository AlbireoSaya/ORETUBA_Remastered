# -*- coding: utf-8 -*-
r"""M8 · **生成器 ↔ 磁盘一致性守门**（`layout/screens/*.json` 是否还能由生成器复现）

■ 它守的是什么（一审 2026-09-22 打回的 Major）
  `layout/screens/*.json` 是**唯一真相源**，但它们**由生成器产出**（如 `工具\m34_build_screens.py`
  的 `build_quickbar()`）。一旦有人只改 JSON 不改生成器（编辑器导出、手工补丁、M35b 类级迁移都会这样），
  **下一次 `python 工具\m34_build_screens.py` 就会把那些改动静默抹掉** ——
  实测后果：`01_title.json` 重跑会**删掉 `title.menu_txt_*` 共 7 件并丢掉 7 个 `state_group`**
  （M35b 的「图标↔文字」组绑定全没了），`36_choices.json` 重跑会删掉 `ch.bg_1/2/3`。
  交接 §三.20 早写明「改 JSON 必须同步生成器」，但**没有任何机器检查** ⇒ 本脚本补上。

■ 做法（`write()` 内存捕获法，**绝不落盘**）
  把生成器模块的 `write(...)` 换成一个只往 dict 里塞的函数（`monkeypatch`），
  逐个调用它的 build 函数，得到「生成器现在会写出什么」，再与磁盘解析结果**逐字段**比对。
  · 本脚本**只 import 生成器模块并调用 build 函数**，不执行生成器的 `__main__`；
  · 生成器里所有 `write` 都经 patch 后的函数 ⇒ **磁盘一个字节都不会变**（脚本末尾会自证）。

■ 判定（三档 + 登记表）
  | 档 | 含义 | 是否 FAIL |
  | --- | --- | --- |
  | `SYNCED` | 逐字段一致 | 否 |
  | `DRIFT`  | 有差异但**不丢数据**（note/注释、z/几何、值的改写）——属"改一处忘同步"的轻微档 | 否（打印清单；`--strict` 下 FAIL） |
  | `LOSS`   | **重跑会丢东西**：元素 id 被删、或受保护字段被抹（`state_group` / `state_assets` / `vis_flag` / `vis_when` / 屏级 `flags_default`/`reveal`/`attach`） | **是**（除非该屏在 `ACK_UNSYNC` 里显式登记） |
  | `NO_GEN` | 该屏**没有** build 函数（历史直接写盘 + 补丁脚本链）⇒ 不存在"被重跑抹掉"的风险 | 否（打印来源链） |

  **`ACK_UNSYNC`（已知不同步登记表）**：每条写 `屏文件 → (责任方, 理由)`；
  只有**真的仍在 LOSS** 的屏才会被它豁免（已修好的条目会打印「可删除」提示，不会静默留着）。
  这和可达性守门的豁免表同规矩：登记内容是**审得动**的（含"重跑会删什么"的逐条清单），
  **不允许**按屏整片跳过而不给理由。

■ 反向自证（`--selfcheck`，内存里造，不动磁盘）
  · A「磁盘多于生成器」：给某屏的**磁盘侧**注入一件生成器没有的元素 ⇒ 必须判 `LOSS`（元素被删）。
  · B「受保护字段被抹」：把磁盘某元素多带一个 `state_group` ⇒ 必须判 `LOSS`（组绑定会被抹）。
  · C「只差 note」：只改备注 ⇒ 必须判 `DRIFT`（不误报成 LOSS）。
  · 另有落盘自证：跑完打印 `layout/screens/` 的 md5 汇总，与运行前一致（脚本自己验，见输出末尾）。

■ 非屏产物专项闸门（★ 第 3 批 · `ISSUE-20260928-02` 收口 · **主判定的一部分**）
  `GENERATED_ARTIFACTS` 登记「生成器产出、但不在 `screens/` 下」的产物；本脚本对其跑两条**常驻闸门**
  （每条自带自证，且**都计入退出码**）：
  · **G-3a `ui_layout.tjs` 不得含带引号的字典键**（`check_tjs_quoted_keys()`）：
    TJS2 内联字典只接受裸标识符键 `k: v` 或**逗号式** `"k", v`；写 `"k": v` 是**语法错误**
    （`execStorage` 整份 FATAL）—— 主代理 2026-09-28 修掉的语法炸弹（`--preset states` 因屏级
    `flags_default` 的带点键 `fc.state.0001` 而装载失败）的**防回归守卫**。自证三条：
    ① 注入旧写法必须被抓；② 合法逗号式 + 值内转义引号不得误判；③ 真生成器对非标识符键
    确实发射逗号式且该输出过闸门（非恒真 —— 交付态文件里根本没有带引号的键，只扫磁盘会得到恒真的绿）。
  · **G-3b `ui_flow_data.tjs` 不得再含旧元素寻址值**（`check_flow_data_no_legacy_ids()`）：
    旧 M18 期元素 id（`flow.n01`/`flow.seq01`/`flow.bus_c`…）不得再作为值出现；并做**非空自证**
    （拓扑结构 `UIFlowData/nodes/edges/buses/fragments` 必须仍在）与**退场登记**核对。

■ 用法
  python 工具/test_gen_sync.py              # 退出码 0 = 无未登记的"重跑即抹"风险
  python 工具/test_gen_sync.py --strict     # DRIFT 也算失败（合并前自查用）
  python 工具/test_gen_sync.py --verbose    # 打印每屏全部差异
  python 工具/test_gen_sync.py --selfcheck  # ＋反向自证
"""
import os, io, json, re, sys, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCR = os.path.join(UI, "layout", "screens")
sys.path.insert(0, HERE)

# 受保护字段：磁盘上有、生成器却没有 ⇒ 视为**丢数据**（重跑即抹掉）
PROTECTED = ("state_group", "state_assets", "vis_flag", "vis_when", "nine", "opacity")
PROTECTED_SCREEN = ("flags_default", "reveal", "attach", "overlay")

# 生成器登记表：(模块名, 说明, 调用风格, 状态, [(build 函数, 产出文件)])
#   调用风格 "internal" = build 函数**自己**调 write（m34）；
#            "return"   = build 函数**返回**对象、由 __main__ 调 write(name, obj)（m33）。
#   状态     "live"      = 当前有效生成器，产出即真相；
#            "superseded"= 已被后续工作整体取代（**产出引用不存在的素材**）——
#                          其结论只作「不得再运行」的告知，不计入 FAIL。
GENERATORS = [
    ("m34_build_screens", "m34_build_screens.py（M34 · 按《交汇协奏曲》PSB 坐标重建）", "internal", "live", [
        ("build_title", "01_title.json"),
        # ★ M46（2026-09-23，用户裁定）：`("build_sysbar", "34_sysbar.json")` 条目**已移除** ——
        #   `sysbar`（系统条）屏已整体删除（屏文件删除、`_index.json` 条目移除、巡演白名单与两端
        #   活引用清理），生成器侧的 `build_sysbar()` 与 `__main__` 的 write 调用亦已删除 ⇒ 无产物可比。
        #   素材不归档（`x_ui_sysbar.png` 与流程图屏 `fc.sysbar` 共用），见 `_工作\M46_旧素材归档\`。
        ("build_quickbar", "35_quickbar.json"),
        ("build_confirm", "21_confirm.json"),
        ("build_choices", "36_choices.json"),
        # ★ M4（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`("build_dress", "37_dress.json")` 条目
        #   **已移除** —— 该屏改为**手工维护**。依据：M4 结构性对齐（加 `attach:"gal_shell"`、
        #   删越出底图的第 12 行角色名、补 ▼ 选中指示与差分名槽两件），后续还有内容方案落地
        #   （角色名/差分接线）⇒ 回写生成器收益 < 两真相源互踩的风险（同 M51 退休 build_music 的先例）。
        #   ⚠️ `m34_build_screens.build_dress()` **函数本体未删除**（该文件不在 M4 白名单内）——
        #   已在 SUPERSEDED 留档「不得运行」，**删除动作留给主代理**。
        #   先例：M45 build_sysmenu / M46 build_sysbar / M47 build_config / M49 build_backlog / M51 build_music。
        # ★ M49（2026-09-24，主代理裁决 A）：`("build_backlog", "26_backlog.json")` 条目**已移除** ——
        #   该屏改为**手工维护**（生成器已退休，见 m34_build_screens.py §73 注）。
        #   依据：本屏自 M35b 起即手工维护（三态图从 hit 挪到 image + `state_group`），
        #   ISSUE-20260924-06 又是「4 行 + 逐块按钮」的结构性重排（`item_text` / `item_buttons` /
        #   底板九宫格 t/b），几何随容量实测微调 ⇒ 回写生成器收益 < 两真相源互踩的风险。
        #   先例：M45 build_sysmenu / M46 build_sysbar / M47 build_config（同一文件内退休）。
        ("build_saveload_save", "23_save.json"),
        ("build_saveload_load", "24_load.json"),
        # ★ M47（2026-09-24）：`("build_config", "25_config.json")` 条目**已移除** ——
        #   该屏已改为**手工维护**（生成器已退休，见 m34_build_screens.py 处注释）。
        # ★ M51（2026-09-24 · ISSUE-20260924-08_鉴赏模式 · 主代理裁决「生成器 = 退休」）：
        #   `("build_music", "28_music.json")` 条目**已移除** —— 该屏改为**手工维护**
        #   （首版由 M3 的一次性脚手架 `_工作/ISSUE-20260924-08_鉴赏模式/M3_BGM/m51_build_music.py`
        #   产出；本屏是结构性重绘：30 件静态曲目行 → 1 个二维网格 list + 逐项 item_buttons +
        #   音量 slider + 翻页键）。生成器侧的 `build_music()` 与 `__main__` 调用亦已删除
        #   （同 M45 删 build_sysmenu / M46 删 build_sysbar / M47 删 build_config / M49 删 build_backlog）
        #   ⇒ 不存在「重跑即抹」风险，故登记在 NO_GEN（而非 ACK_UNSYNC）。
        ("build_flowchart", "32_flowchart.json"),
    ]),
    ("m33_rebuild_screens", "m33_rebuild_screens.py（M33 · 系统屏重排）", "return", "superseded", [
        # ★ M45（2026-09-23，用户裁定）：`("build_sysmenu", "20_sysmenu.json")` 条目**已移除** ——
        #   `sysmenu` 屏已整体废除（屏文件删除、`_index.json` 条目移除、两端活引用清理），
        #   生成器侧的 `build_sysmenu()` 与 `__main__` 的 write 调用亦已删除 ⇒ 无产物可比。
        # ★ PSV 换皮（2026-09-26 · ISSUE-20260926-06）：`22_loading.json` 自 M34 起即由
        #   **手工维护**（素材经 M34 重映射为 `x_ui_*`），本轮 PSV 换皮又把它改为
        #   `ui/x_ui_psv_loading.png`（640×240，1:1 无 nine）并让 `ld.text` 退场。
        #   **本条目保留**（不删）是刻意的：m33 已整体标"失效、不得再运行"，本条目让 `test_gen_sync`
        #   每次都在「盘上仍会被它改坏的屏」清单里点名 `22_loading.json`（含受保护字段 `nine` 会被抹），
        #   即**隐患是登记可见的、不是静默的**。产物脚本：
        #   `_工作\ISSUE-20260926-06_A基础组三屏换皮\复现脚本\psv_build_abasic_screens.py`（一次性脚手架）。
        ("build_loading", "22_loading.json"),
    ]),
]

# 被后续模块取代的 build 函数（同一屏已由 GENERATORS 里的新函数负责）——不参与比对，仅留档
SUPERSEDED = {
    "m33_rebuild_screens.build_confirm": "同一屏由 m34_build_screens.build_confirm 重建（owner 已是 M34）",
    "m33_rebuild_screens.build_save/load": "同一屏由 m34_build_screens.build_saveload_* 重建",
    "m33_rebuild_screens.build_config": "该屏自 M47 起为**手工维护**（m34 的 build_config 亦已退休删除）",
    "m33_rebuild_screens.build_backlog": "该屏自 M49 起为**手工维护**（m34 的 build_backlog 亦已退休删除）",
    # ★ M51（2026-09-24）：原注「同一屏由 m34_build_screens.build_music 重建」**已订正** ——
    #   m34 的 `build_music()` 亦已退休删除（该屏现由 M3 的一次性脚手架产出、此后手工维护，
    #   见上方 `NO_GEN`）⇒ 本屏**已无任何 build 函数**，`m33` 与 `m34` 两版都不得再运行。
    "m33_rebuild_screens.build_music": "该屏现为**手工维护**（m33 与 m34 两版 build_music 均已退休删除）",
    "m33_rebuild_screens.patch_flowchart": "作用于 `flow.tab*`——该结构已由 m34 的 `fc.*` 重建取代（死代码）",
    # ★ M4（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：37_dress 退册后的留档。函数本体仍在
    #   m34_build_screens.py。★ M8 一审 R1（2026-09-24）订正：`__main__` 里的调用**已退接线**
    #   （照 M51 先例注释式退休，函数体保留、删除留主代理）⇒ `python m34_build_screens.py`
    #   整跑**不再产出** 37_dress.json；仅当有人显式调用 `build_dress()` 才有「重跑即抹」风险。
    "m34_build_screens.build_dress": "该屏自 M4 起为**手工维护**（37_dress 结构性对齐后登记进 NO_GEN；"
                                     "M8 一审 R1 已退 `__main__` 接线；函数体保留、显式调用仍不得运行，"
                                     "删除留主代理）",
}

# 无 build 函数的屏（历史直接写盘 / 由补丁脚本生成）——不存在"被重跑抹掉"的风险，但登记来源
NO_GEN = {
    "10_dialog.json": "M23_gen.py（系统条改通用 hit 扫描 + 对话框换图）＋ migrate_1920.py",
    "27_gallery.json": "_工作/M14_gen_screens.py",
    # ★ ISSUE-20260928-07（2026-09-28，用户裁定）：`29_ending.json` 条目**已移除** —— 该屏已整体删除
    #   （用户：未来改用一段视频代替片尾）。
    # ★ M43（2026-09-23）：`30_chapter.json` 条目**已移除** —— 该屏已整体删除（用户裁定）。
    # ★ ISSUE-20260928-06（2026-09-28）：`31_fragment.json` 条目**已移除** —— 该屏已整体删除
    #   （番外内容由流程图屏的独立层承载；动作 `open_fragment`/`fragment_enter` 与素材保留）。
    "33_sysicons.json": "_工作/M23_gen.py",
    # ★ M47（2026-09-24）：设置屏**整体重做**（两页：系统/声音）后改为**手工维护** ——
    #   首版由 `_工作/M47_设置屏重设/复现脚本/m47_build_config.py` **一次性**产出；
    #   m34 的 `build_config()` 已随之**退休删除**（同 M45 删 build_sysmenu / M46 删 build_sysbar）
    #   ⇒ 不存在「重跑即抹」风险，故登记在 NO_GEN（而非 ACK_UNSYNC）。
    #   ★ PSV 换皮（C 组 · 2026-09-26 · ISSUE-20260926-06）：本屏再度结构性重排（PSV 两页底图 +
    #     14 个无字药丸壳作行名标签底 + 9 条 PSV 滑槽轨 + 5 张盖槽片），改为在本 NO_GEN 基础上
    #     用 `_工作/ISSUE-20260926-06_C设置屏换皮/复现脚本/psv_build_config_screen.py`（**一次性脚手架**）
    #     从 M47 备份起步重排 ⇒ **仍属手工维护**；**两件旧件已退场**：`cfg.frame` / `cfg.page_strip`
    #     （被 PSV 整屏底图取代；`x_ui_cfg_page_strip.png` 仍被 39 鉴赏外壳屏共用，**素材不归档**；
    #     `x_ui_cfg_frame.png` 因此变为零引用，保留未删）。**后果明文登记：本屏不再能被整屏重生成**。
    "25_config.json": "_工作/M47_设置屏重设/复现脚本/m47_build_config.py（**一次性脚手架**；此后手工维护）"
                      "★ PSV 换皮（C 组）：_工作/ISSUE-20260926-06_C设置屏换皮/复现脚本/"
                      "psv_build_config_screen.py（自 M47 备份起步；`cfg.frame`/`cfg.page_strip` 已退场）",
    # ★ M49（2026-09-24，主代理裁决 A）：回想屏**结构性重排**（4 行 + 逐块「跳转」「重新播放」按钮、
    #   `item_text` / `item_buttons` / 底板九宫格 t/b）后改为**手工维护** ——
    #   首版由 `_工作/ISSUE-20260924-06_回想屏重排/复现脚本/m06_build_backlog.py` **一次性**产出；
    #   m34 的 `build_backlog()` 已随之**退休删除**（同 M45 删 build_sysmenu / M46 删 build_sysbar /
    #   M47 删 build_config）⇒ 不存在「重跑即抹」风险，故登记在 NO_GEN（而非 ACK_UNSYNC）。
    #   **后果明文登记：本屏不再能被整屏重生成**；改动只改 `layout/screens/26_backlog.json`。
    "26_backlog.json": "_工作/ISSUE-20260924-06_回想屏重排/复现脚本/m06_build_backlog.py"
                       "（**一次性脚手架**；此后手工维护。生成器 `m34_build_screens.build_backlog()` 已退休删除）",
    # ★ M51（2026-09-24 · ISSUE-20260924-08_鉴赏模式 · 主代理裁决「生成器 = 退休」）：
    #   BGM 鉴赏页**结构性重绘**（30 件静态曲目行 → 1 个二维网格 `list`（`max_cols`×`max_rows`）
    #   + 逐项 `item_buttons` 播放键 + 逐项三态 `item_frame` + 音量 `slider` + 翻页键）后改为
    #   **手工维护** —— 首版由 `_工作/ISSUE-20260924-08_鉴赏模式/M3_BGM/m51_build_music.py`
    #   **一次性**产出；m34 的 `build_music()` 已随之**退休删除**（同 M45 删 build_sysmenu /
    #   M46 删 build_sysbar / M47 删 build_config / M49 删 build_backlog）⇒ 不存在「重跑即抹」风险，
    #   故登记在 NO_GEN（而非 ACK_UNSYNC）。**后果明文登记：本屏不再能被整屏重生成**；
    #   改动只改 `layout/screens/28_music.json`。
    "28_music.json": "_工作/ISSUE-20260924-08_鉴赏模式/M3_BGM/m51_build_music.py"
                     "（**一次性脚手架**；此后手工维护。生成器 `m34_build_screens.build_music()` 已退休删除）",
    # ★ M1（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`39_gal_shell.json` 是**本轮新建**的
    #   鉴赏模式**共享外壳浮层屏**（页签条 4 热区 + 标题 + 返回键；`owner = M1`）——
    #   由主代理跨模块裁决「页签 = 切屏」时指定新建 ⇒ **手工维护、无生成器**（也没有历史生成器）。
    "39_gal_shell.json": "ISSUE-20260924-08 · M1 新建的鉴赏外壳浮层屏（手工维护；无生成器）",
    # ★ M4（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`38_replay.json` 是**本轮新建**的
    #   **情景回想屏**（两页 5×5 = 50 栏网格 list；`owner = M4`）——首版由
    #   `临时\m52_build_replay_screen.py` **一次性**产出（此后该 JSON 手工维护；无生成器）。
    "38_replay.json": "ISSUE-20260924-08 · M4 新建的情景回想屏"
                      "（首版由 临时\\m52_build_replay_screen.py 一次性脚手架产出；此后手工维护）",
    # ★ M4（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`37_dress.json` **结构性对齐**（加
    #   `attach:"gal_shell"`、删第 12 行角色名、补 `dr.sel_mark`/`dr.face_tx`）后改为**手工维护** ——
    #   生成器登记条目已移除（见 GENERATORS 注）。**后果明文登记：本屏不再能被整屏重生成**；
    #   ★ M8 一审 R1（2026-09-24）订正：`m34_build_screens.build_dress()` 的 **`__main__` 调用已退接线**
    #   （照 M51 先例，函数体保留、删除留主代理）⇒ 整跑 `m34_build_screens.py` 已无本屏产物；
    #   M8 守门（SUPERSEDED「不得显式调用」）拦截的是**显式调用** `build_dress()` 这一条路径。
    "37_dress.json": "m34_build_screens.build_dress()（登记已退册；M8 一审 R1 已退 `__main__` 接线、"
                     "函数体保留，显式调用仍不得运行；此后手工维护，改动只改 layout/screens/37_dress.json）",
}

# ★ 已知不同步登记表：屏文件 → (责任方, 生成器入口, 理由)；**只对仍在 LOSS 的屏生效**
#   · 「生成器入口」= 该屏**当前**的产出函数（有入口 ⇒ 属「有生成器但落后」，重跑会真抹数据）；
#     与 `NO_GEN`（无 build 函数 ⇒ 不存在被重跑抹掉的风险）是两种不同性质，不得混为一谈。
#   · 已修好（SYNCED）的屏**不在本表**；本表条目若不再命中 LOSS，脚本会打印「可删除」提示。
#   ★ M41（2026-09-23）：`01_title.json` 条目已移除 —— build_title() 改为「忠实透传盘上元素」，
#     重跑字节幂等、不再回退用户改动（M35b 组绑定 / M40 x+200 / M41 删署名行）⇒ 报 SYNCED，条目无必要。
ACK_UNSYNC = {
    "36_choices.json": (
        "待回写（M35b 后续 / 主代理指派）★ M46 追加：本屏自 M45f 起属**手工维护**，见理由"
        "★ PSV 换皮（2026-09-26 · ISSUE-20260926-06）追加：条框换 PSV 两态件，重跑会一并抹掉",
        "m34_build_screens.build_choices()",
        "`_工作\\M35b_热区态图迁移.py` 把 `ch.sel` 拆成 `ch.bg_1/2/3`（per-row 态图）并把三态从 hit 挪到 image，"
        "仅改 JSON。重跑会删 `ch.bg_1/2/3` 并让 3 个 hit 重新持有 `state_assets`（热区拉伸涂抹问题回归）。"
        "★ M46 追加：此后本屏又经 M45e（全屏 y −170）→ M45f（整体换成 1 个 `list` `ch.choices`，项数自适应）"
        "→ M46（`item_frame.state_assets` 逐项三态换图）三轮回**手工**改动，而生成器仍停在 9 元素旧形；"
        "即重跑不仅回归热区涂抹，还会**删掉 `ch.choices` 并丢掉逐项态图**（后者现由 `_would_lose` 的"
        "嵌套字段保护 `PROTECTED_NESTED` 拦得住）。若日后真要回写生成器，先跑 `--selfcheck` 与 `_would_lose` 对拍。"
        "★ PSV 换皮（2026-09-26 · ISSUE-20260926-06 · 产物脚本 `_工作\\ISSUE-20260926-06_A基础组三屏换皮\\复现脚本\\"
        "psv_build_abasic_screens.py`，**一次性脚手架、此后手工维护**）：本屏条框改为 PSV 两态件——"
        "`item_frame` 换成 `ui/x_ui_psv_choice_norm.png`（蓝紫＝常态）/ `ui/x_ui_psv_choice_sel.png`（粉＝悬停与按下），"
        "几何 `x 404→340`、`w 1113→1240`、`item_h 83→107`、字号 `34→44`。"
        "★ A 基础组修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复，产物脚本 "
        r"`_工作\ISSUE-20260926-06_A基础组修复\复现脚本\psv_fix_confirm_choices.py`）：再订正 "
        "`item_h 107→128`（与素材 1240×128 **1:1、零缩放**）、`gap 17→2`（6 行 = 6×128+5×2 = 778 ≤ 780 不出画布）；"
        "两态素材按双阈值重裁（水平 α≥2 / 纵向 α≥11，装进 128 行画布）。**重跑同样会抹掉这两处**。"
        "**重跑 build_choices() 会把这些字段整体改回 M34 旧形**（含删掉 `ch.choices`），已由上面的 `_would_lose` 拦下并列出。"),
    "21_confirm.json": (
        "待回写（M35b 后续 / 主代理指派）★ PSV 换皮（2026-09-26 · ISSUE-20260926-06）追加："
        "本屏已整体改为 PSV 22 板选板形，重跑会抹掉 53 件全部结构（见理由）"
        "★ A 基础组修复轮（2026-09-26）追加：22 张板一律 1044×540（裁去板体之外的白色羽毛 YES/NO 徽章带，原 602 高）、两热区加 `vis_flag:cf_which` + `vis_when:\"*\"`（有板在位才生效）；重跑会一并抹掉。",
        "m34_build_screens.build_confirm()",
        "`_工作\\M35b_热区态图迁移.py` 把 `cf.hit_yes/no` 的 `state_assets` 挪到 `cf.yes/no` image + `state_group` 联动；"
        "重跑会把三态塞回 hit（拉伸涂抹回归）并抹掉 4 个 `state_group`。"
        "★ PSV 换皮（2026-09-26 · ISSUE-20260926-06 · 用户裁决「22 张中文弹窗全部采用」；产物脚本 "
        "`_工作\\ISSUE-20260926-06_A基础组三屏换皮\\复现脚本\\psv_build_abasic_screens.py`，**一次性脚手架、此后手工维护**）："
        "本屏由 9 件（`cf.dim`/`cf.panel`/`cf.msg`/`cf.yes(.no)`×2/`cf.hit_yes(.no)`×2）改为 **53 件**——"
        "① 屏级 `flags_default` `{cf_which:\"01\"}` 选板；② **22 张** `cf.panel_<板号>`（PSV 中文弹窗板，"
        "`vis_flag=cf_which` + `vis_when=<板号>`）；③ **两型板共用**的一对透明热区 `cf.hit_yes/no`（`action` 沿用 "
        "`confirm_yes/no`）；④ **7×4 = 28 件** `cf.yes_b<板号>`/`cf.no_b<板号>`（+ `_tx`）——7 张无 YES/NO 的板"
        "（20–24/42/45）补我方是/否按钮（`vis_flag=cf_which`）。"
        "**重跑 build_confirm() 会**：抹掉 `flags_default`、删掉全部 22 张板与 28 件补按钮、并**重新加回** "
        "`cf.panel`/`cf.msg`/`cf.yes`/`cf.no` 等旧件（画面整体退回《交汇协奏曲》AI 面板形）。"
        "★ 推荐处置（**留主代理**，超出本轮授权）：照 M47 `build_config` / M49 `build_backlog` / M51 `build_music` "
        "先例**退休 `build_confirm()`**（函数与 `__main__` 调用一并删）并把本屏登记进 `NO_GEN`；"
        "在那之前本条目是**唯一**记录「重跑会丢什么」的地方。"),
    # ★ M49（2026-09-24，主代理裁决 A）：`26_backlog.json` 条目**已移除** —— 生成器入口
    #   `m34_build_screens.build_backlog()` 已退休删除（该屏进 NO_GEN），不再有「重跑会丢什么」的对象。
    #   ★ PSV 换皮（2026-09-26 · ISSUE-20260926-06 · B 组）追加确认：本轮把该屏的 `bl.list` 几何/底板
    #   与 `bl.up/slider/down`(+hit) 全部重排，**因为已无生成器 ⇒ 不需要 ACK 条目**（这正是 M49 退休的收益）。
    "23_save.json": (
        "待回写（M35b 后续 / 主代理指派）★ PSV 换皮（2026-09-26 · ISSUE-20260926-06 · B 组）追加："
        "本屏已整体改为「PSV 底图 + 12 槽 4×3 网格 + 槽三态 flag」形，重跑会抹掉 155 件全部结构与 12 键 flags_default"
        "★ A 基础组修复轮（2026-09-26）追加：件数 155 → 165（新增 10 件互斥页码文本 `sv.pgnum_01..10`），并新增屏级 `page_flag:\"sv_page\"`（+ `flags_default` 第 13 键 `sv_page`）；当前页签换件 `ui/x_ui_psv_tab_sel.png`；重跑会一并抹掉。"
        "★ 未愈缺陷修复轮（2026-09-26）追加：`sv.pgnum_01..10` 由「N / 10」改为**只绘前导页数字**"
        "（盒 (1699,83,60,48)、字号 48、样文「1」..「10」）；`sv.sys_game|title|end`（各含 `_tx`/`_hit`，共 9 件）"
        "整体**上移 22px**（按钮/文字 y44→22、热区 y36→14）；重跑会一并抹掉。",
        "m34_build_screens.build_saveload_save()",
        "本屏自 M45（`sv.num*/sv.info*` 平移 + 三系统按钮 2× 自动重排）起即**手工维护**，生成器停在"
        "M34 的 118 件旧形（`test_gen_sync` 长期报 DRIFT ~78 处）。"
        "★ PSV 换皮（2026-09-26 · ISSUE-20260926-06 · 用户裁决「深度换皮」；产物脚本 "
        "`_工作\\ISSUE-20260926-06_BC存读档与回想换皮\\复现脚本\\psv_build_bc_screens.py`，"
        "**一次性脚手架、此后手工维护**）：本屏由 118 件改为 **155 件**——"
        "① 新增整屏底图 `sv.bg`（`ui/x_ui_psv_save_bg.png`，z=2）；"
        "② 12 槽槽框改 4 列×3 行（415×122；x 64/523/982/1441、y 317/483/649）；"
        "③ **每槽三态各一件**（`sv.slotN` / `sv.slotN_off` / `sv.slotN_warn`，共 36 件）"
        "带 `vis_flag:sv_sN` + `vis_when:on|off|warn`；④ 新增 12 件空槽标签 `sv.nodataN`；"
        "⑤ `sv.thumb*` 换 `x_ui_psv_slot_thumbwin.png`；⑥ `sv.num*/sv.info*` 24 件按新槽几何重排；"
        "⑦ `sv.tab_a/b`(+`_tx`/`_hit`) x+315、页码键 30 件 x−56。"
        "**重跑 build_saveload_save() 会**：抹掉屏级 `flags_default`（12 键）与全部 `vis_flag`/`vis_when`、"
        "删掉 36+12+12 件新结构、并把这些元素整体改回《交汇协奏曲》旧形（118 件、12 槽 256×345）。"
        "★ 推荐处置（**留主代理**，超出本轮授权）：照 M47 `build_config` / M49 `build_backlog` / "
        "M51 `build_music` 先例**退休 `build_saveload_save/load()`**（函数与 `__main__` 调用一并删）"
        "并把两屏登记进 `NO_GEN`；在那之前本条目是**唯一**记录「重跑会丢什么」的地方。"),
    "24_load.json": (
        "待回写（M35b 后续 / 主代理指派）★ PSV 换皮（2026-09-26 · ISSUE-20260926-06 · B 组）追加："
        "同 23_save（读档屏与存档屏结构同源），重跑会抹掉 155 件全部结构与 12 键 flags_default",
        "m34_build_screens.build_saveload_load()",
        "同 `23_save.json`（两屏除 `sv.bg` 的底图件（save_bg / load_bg）与 action（`open_save`/`open_load`）"
        "外结构逐字相同）。读档屏的 `sv_s1..sv_s12` 语义为**启用/禁用**（无可读档 ⇒ `off`），"
        "由编程组按存档数据写值；默认 `on` 与存档屏一致。"
        "★ 未愈缺陷修复轮（2026-09-26）追加：与 23_save 同款改动（`sv.pgnum_01..10` 只绘前导页数字"
        "盒 (1699,83,60,48)/字号 48；`sv.sys_*` 9 件上移 22px）。"),
    "32_flowchart.json": (
        "已并入 main 的产品态（`ISSUE-20260927-05` · 2026-09-27 · 主代理维护）",
        "m34_build_screens.build_flowchart()",
        "**本条目的豁免范围已由「关闭键三态」扩大为「整个图内容层 + 顶层键 `links`」**："
        "① 旧行为（M35b 起）：重跑会抹掉 `flowchart.close` 组、把关闭键三态按 56×56 热区拉伸；"
        "② **现行**：`32_flowchart.json` 的图内容层由新生成器 `工具/gen_flow_layout.py` 从真实剧情数据"
        "（`资源组/08_全系列章节流程图.html` 内嵌 `const DATA`，712 节点 / 760 边）产出 —— "
        "含 `fc.node.*`（image/text/hit 三件套）、`fc.label.*`、`fc.entry.*`，以及**顶层键 `links`**（连线路由折线）；"
        "③ 故重跑 m34 的 `build_flowchart()` 会：抹掉全部 `fc.node./label./entry.` 元素与其 `state_assets`、"
        "**丢掉顶层键 `links`（连线全部消失）**、并恢复 `fc.n_section/n_select/n_extra/label/branch/newmark` 那批旧样板。"
        "④ **正确重生成路径＝`python 工具/gen_flow_layout.py` → `python 工具/gen_layout.py`**；"
        "**m34 的 `build_flowchart()` 已实质退休，不得再运行**。"),
    # ★ M46（2026-09-23，用户裁定）：`"34_sysbar.json"` 条目**已移除** —— 该屏已整体删除，
    #   生成器侧 `build_sysbar()` 亦已删除 ⇒ 不再有「重跑会丢什么」的对象（M45 移除 `sysmenu` 同例）。
    # ★ M4（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`"37_dress.json"` 条目**已移除** ——
    #   该屏的生成器登记条目已退册（见 GENERATORS / NO_GEN / SUPERSEDED 三处注），不再参与比对，
    #   本表不再需要豁免它。
}

# ★ 非屏产物登记表（★ 第 3 批 · `ISSUE-20260928-02` 收口）
#   本表**不属于**上面的屏比对管道（那是 `layout/screens/*.json` 专用），而是给
#   「**同样由生成器产出、但不在 `screens/` 下**」的产物登记**来源链 + 已知缺口 + 专项闸门**。
#   每条：(相对 UI 组的路径, 生成器, 状态, 说明)。
GENERATED_ARTIFACTS = [
    ("krkr/game/ui_layout.tjs",
     "工具/gen_layout.py（`layout/screens/*.json` + `layout/palette.json` → 三处产物）",
     "live",
     "屏布局的 krkr 侧产物。★ 专项闸门 `check_tjs_quoted_keys()`（见本文件下方）："
     "**不得含带引号的字典键**（TJS2 内联字典只接受裸标识符键 `k: v` 或**逗号式** `\"k\", v`；"
     "写 `\"k\": v` 是**语法错误**——`execStorage` 整份 FATAL）。这是主代理 2026-09-28 修掉的"
     "一颗语法炸弹（`--preset states` 因屏级 `flags_default` 的带点键 `fc.state.0001` 而装载失败）"
     "的**防回归守卫**；闸门自带**变异自证**（构造一行旧写法必须被抓住）。"),
    ("krkr/game/ui_flow_data.tjs",
     "工具/gen_flow_data.py（`资源组/剧本/spine.json` + `01_剧情流程图.md` + `主线编排方案.md` → "
     "`复刻/flow_data.js` ＋ `krkr/game/ui_flow_data.tjs`）",
     "synced",
     "★ **第 3 批（2026-09-28）**：六个**旧元素寻址字段已删除**（`nodes[].el` / `edges[].els` / "
     "`buses[].el` / `links[].el` / `layout.wrap_elements` / `layout.bypass_elements`；值曾是 "
     "`flow.n01`/`flow.seq01`/`flow.bus_c`/`flow.cv1_a` 等**早已不在屏数据里**的旧 id ⇒ "
     "「按旧 id 静默空转」的隐患源）；专项闸门 `check_flow_data_no_legacy_ids()` 守着。"
     "★★ **第 6 批订正（2026-09-28 收口）——本文件与 `复刻/flow_data.js` 均已同步、且与生成器输出「逐字节相同」**："
     "`krkr/game/ui_flow_data.tjs` md5 `4f4c5611e11bc902b445cd0dfa462530`（39,252 B）；"
     "`复刻/flow_data.js` md5 `fa4a16957837e8d7c82dfd0f0e0725d5c`（43,872 B）——后者由**主代理在收口时亲手**"
     "跑 `python 工具/gen_flow_data.py` 完成（**不是子代理越权**）。两个产物正文均**无**旧 `\"flow.*\"` 值（实测 0 处）、"
     "**无** `\"el\"`/`\"els\"`，且 `retired_addressing` 标记齐备。**缺口 G-5（`box_png` 缺图）已修**：`BOX_PNG` "
     "已回写为盘上**存在**的 4 件（`ui/x_ui_node_section_off.png` / `x_ui_node_select_off.png` / "
     "`x_ui_node_frag_off.png` / `x_ui_label_off.png`），连跑两次产出的两个产物里 **box_png 引用 4 种、缺件 0**"
     "（`x_gen_flownode` 仅在**头部注释的订正句**里出现，**不是**任何字段的值）。"
     "⇒ 上一版「盘上现值与生成器输出不等价 / 重跑会把 `box_png` 静默回退成缺图引用 / JS 产物未同步」三条**全部作废**；"
     "重跑是**幂等**的（两次产出字节相同）。**后续 agent 不要再跑一次去「修一个已修的东西」**。"),
]


def _gen_layout_comma_form_probe():
    r"""非恒真自证（不落盘）：拿**真生成器**的 `tjs_literal` 造一个**非标识符键**，
    证明（a）它确实发射**逗号式** `"a.b", 1`、（b）该写法**不被**本闸门判为非法。

    为什么需要它：交付屏 `ui_layout.tjs` 的键**全是合法标识符**（`fc_layer`/`elements`…），
    盘上根本没有带引号的键 ⇒ 只扫磁盘会得到一个「恒真」的绿 —— 上面那条
    「文件里必须存在逗号式带引号键」的自证正是为此，但它对**交付态**必然失败。
    故非恒真性改由**生成器能力**证明：键不是标识符时，生成器必须走逗号式（并且能过本闸门）。
    """
    import importlib.util
    gp = os.path.join(UI, "工具", "gen_layout.py")
    spec = importlib.util.spec_from_file_location("_gl_probe", gp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    LINE_RE = r'^\s*"(?:[^"\\]|\\.)*"\s*:'
    lit = mod.tjs_literal({"a.b": 1, "ok": 2}, 0)          # 运行期字典，非标识符键在前
    comma = ('"a.b", 1' in lit)
    illegal = any(re.match(LINE_RE, ln) for ln in lit.split("\n"))
    mod.assert_no_quoted_dict_keys(lit)                     # 生成器自己的落盘前自检必须放行
    return lit, comma, illegal


def check_tjs_quoted_keys(path=None, text=None):
    r"""★ 第 3 批专项闸门：`ui_layout.tjs` **不得含带引号的字典键**（TJS2 语法炸弹防回归）。

    判据（与 `工具/gen_layout.py::assert_no_quoted_dict_keys` **逐字同一句话**）：
    行首（缩进后）一个**未转义**的双引号 + 引号内内容 + 冒号 ⇒ 非法。
    值里的引号都被 `tjs_literal` 转义成 `\"`、且不在行首 ⇒ 不会误判。

    ★ **四条自证**（前三条在内存里造，不落盘）：
      ① **正向变异**：插一行 `  "fc.state.0001": "locked",` ⇒ **必须被判为命中**；
      ② **反向变异**：合法逗号式 + 值里带转义引号（`"k", "a\"b:c"`）⇒ **不得误判**；
      ③ **生成器能力（非恒真）**：真生成器对**非标识符键**确实发射逗号式，
         且该输出必须过闸门 —— 见 `_gen_layout_comma_form_probe()`；
      ④ 盘上文件扫描：`hits == 0` 才算过（这是主判据）。
    返回 (fails, notes)。
    """
    fails, notes = [], []
    p = path or os.path.join(UI, "krkr", "game", "ui_layout.tjs")
    if text is None:
        if not os.path.exists(p):
            return ["[ui_layout.tjs] 缺文件：%s（`工具/gen_layout.py` 的产物）" % p], notes
        text = io.open(p, encoding="utf-8").read()
    tjs_path = os.path.relpath(p, UI)
    LINE_RE = r'^\s*"(?:[^"\\]|\\.)*"\s*:'
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        if re.match(LINE_RE, line):
            hits.append((i, line.strip()))
    if hits:
        fails.append("[%s] 含**带引号的字典键** %d 处（TJS2 语法错误 ⇒ execStorage 整份 FATAL）：%s"
                     % (tjs_path, len(hits),
                        ["第 %d 行: %s" % (i, s[:70]) for i, s in hits[:5]]))
    notes.append("正文扫描：%d 行，疑似非法字典键 **%d 处**（主判据：必须为 0）"
                 % (len(text.split("\n")), len(hits)))
    n_comma = len(re.findall(r'^\s*"(?:[^"\\]|\\.)*"\s*,', text, re.M))
    notes.append("附注：盘上文件里逗号式合法带引号键 %d 处（交付态键全是标识符 ⇒ 通常为 0，属正常；"
                 "非恒真性由下方 ③ 生成器能力自证保证）" % n_comma)
    # ① 正向变异：插一行旧写法，判据必须命中
    mut = text + '\nUILayoutData.mutation_probe = %[\n  "fc.state.0001": "locked",\n];\n'
    mut_hit = [i for i, line in enumerate(mut.split("\n"), 1) if re.match(LINE_RE, line)]
    notes.append("① 正向变异：注入 `\"fc.state.0001\": \"locked\",` ⇒ 判据命中 %d 行%s"
                 % (len(mut_hit), "（✓ 按预期）" if mut_hit else "（✗ 未命中 ⇒ 闸门失效）"))
    if not mut_hit:
        fails.append("[%s] ① 正向变异自证失败：注入的旧写法未被判据抓住（闸门恒假）" % tjs_path)
    # ② 反向变异：值里的转义引号不得误判
    mut2 = 'UILayoutData.p = %[\n  "k", "a\\"b:c",\n];\n'
    mut2_hit = [i for i, line in enumerate(mut2.split("\n"), 1) if re.match(LINE_RE, line)]
    notes.append("② 反向变异：`\"k\", \"a\\\"b:c\"` ⇒ 命中 %d 行%s"
                 % (len(mut2_hit), "（✓ 未误判）" if not mut2_hit else "（✗ 误判 ⇒ 判据过宽）"))
    if mut2_hit:
        fails.append("[%s] ② 反向变异失败：值里的转义引号被误判为非法键" % tjs_path)
    # ③ 生成器能力（非恒真）：真生成器对非标识符键必须发射逗号式、且该输出过闸门
    try:
        lit, comma, illegal = _gen_layout_comma_form_probe()
        notes.append("③ 生成器能力自证：`tjs_literal({\"a.b\":1,\"ok\":2})` = %r ⇒ 逗号式=%s ／ "
                     "被判为非法=%s ／ 生成器自检放行=✓%s"
                     % (lit, comma, illegal, "" if (comma and not illegal) else " ← ✗"))
        if not comma:
            fails.append("[%s] ③ 非恒真自证失败：生成器对非标识符键没发射逗号式" % tjs_path)
        if illegal:
            fails.append("[%s] ③ 非恒真自证失败：生成器的逗号式输出被本闸门误判为非法" % tjs_path)
    except Exception as ex:
        fails.append("[%s] ③ 生成器能力自证无法执行：%r" % (tjs_path, ex))
    return fails, notes


def check_flow_data_no_legacy_ids(path=None):
    r"""★ 第 3 批专项闸门：`ui_flow_data.tjs` **不得再含旧元素寻址值**（`ISSUE-20260928-02` §7.2）。

    判据：文件正文里不得出现旧屏版式的元素 id **字面量**（`"flow.…"` 形态）。
    旧 id 的形态：`flow.n01` / `flow.b01` / `flow.seq01` / `flow.wrap_a` / `flow.e02_a` /
    `flow.bus_c` / `flow.cv1_a` / `flow.cv_n09`（M18 期元素，早已不在屏数据里）。
    ★ 该文件由生成器产出（`工具/gen_flow_data.py` 现已不产这些字段）——
      本闸门守「**不再按旧 id 静默空转**」；同时做**非空自证**（拓扑结构必须仍在）。
    ★ 顺带记录补丁前后的对照：git HEAD 版为 57 处旧 id（本批清零）。
    返回 (fails, notes)。
    """
    fails, notes = [], []
    p = path or os.path.join(UI, "krkr", "game", "ui_flow_data.tjs")
    if not os.path.exists(p):
        return ["[ui_flow_data.tjs] 缺文件：%s" % p], notes
    text = io.open(p, encoding="utf-8").read()
    tjs_path = os.path.relpath(p, UI)
    legacy = re.findall(r'"flow\.[A-Za-z0-9_]+"', text)
    if legacy:
        which = sorted(set(legacy))
        fails.append("[%s] 仍含 %d 处旧元素寻址值（旧 id 早已不在屏数据里 ⇒ 按旧 id 静默空转）：%s"
                     % (tjs_path, len(legacy), which[:8]))
    notes.append("旧元素寻址值 `\"flow.*\"`：**%d 处**（主判据：必须为 0）" % len(legacy))
    # 非空自证：文件里必须有拓扑数据本身（否则「扫不到旧 id」可能只是文件空了/被清空）
    miss = []
    for need in ("UIFlowData", "nodes", "edges", "buses", "fragments"):
        if need not in text:
            miss.append(need)
    notes.append("非空自证：拓扑结构 `UIFlowData`/`nodes`/`edges`/`buses`/`fragments` ⇒ %s"
                 % ("齐备 ✓" if not miss else "缺 %s ✗" % miss))
    for need in miss:
        fails.append("[%s] 缺关键结构 `%s` ⇒ 文件被清空/损坏（本闸门的「无旧 id」结论不可信）"
                     % (tjs_path, need))
    # 退场登记（文件头 + 数据键）
    reg_head = ("旧元素寻址字段" in text.split("var UIFlowData")[0])
    reg_key = ("retired_addressing" in text)
    notes.append("退场登记：文件头=%s ／ 数据键 `retired_addressing`=%s"
                 % ("✓" if reg_head else "✗", "✓" if reg_key else "✗"))
    if not (reg_head and reg_key):
        fails.append("[%s] 退场未登记（文件头=%s / retired_addressing=%s）"
                     % (tjs_path, reg_head, reg_key))
    return fails, notes


# ══════════════════════════════════════════════════════════════════════
# 比对
# ══════════════════════════════════════════════════════════════════════
def compare(gen, disk, screen_file):
    """gen = 生成器会写出的 dict；disk = 磁盘现值。→ (cls, loss[], drift[])
    cls ∈ {"SYNCED","DRIFT","LOSS"}"""
    loss, drift = [], []
    for k in sorted(set(list(gen) + list(disk))):
        if k == "elements":
            continue
        if k in PROTECTED_SCREEN and k in disk and k not in gen:
            loss.append("屏级字段 `%s` 在磁盘上存在、生成器不再产出（重跑即抹）：%r"
                        % (k, disk[k]))
        elif gen.get(k) != disk.get(k):
            drift.append("屏级字段 `%s` 不同：生成器 %r ／ 磁盘 %r" % (k, gen.get(k), disk.get(k)))
    ge = {e.get("id"): e for e in gen.get("elements") or []}
    de = {e.get("id"): e for e in disk.get("elements") or []}
    for i in sorted(set(de) - set(ge)):
        loss.append("元素 `%s` 只在磁盘上、生成器不再产出 ⇒ **重跑会删掉它**" % i)
    for i in sorted(set(ge) - set(de)):
        drift.append("元素 `%s` 只在生成器里（磁盘没有）⇒ 重跑会新增它" % i)
    for i in sorted(set(ge) & set(de)):
        g, d = ge[i], de[i]
        for k in sorted(set(list(g) + list(d))):
            if g.get(k) == d.get(k):
                continue
            if k in PROTECTED and k in d and k not in g:
                loss.append("元素 `%s` 的受保护字段 `%s` 只存在于磁盘（重跑即抹）：%r" % (i, k, d[k]))
            else:
                drift.append("元素 `%s.%s` 不同：生成器 %r ／ 磁盘 %r" % (i, k, g.get(k), d.get(k)))
    cls = "LOSS" if loss else ("DRIFT" if drift else "SYNCED")
    return cls, loss, drift


# ══════════════════════════════════════════════════════════════════════
# 内存捕获
# ══════════════════════════════════════════════════════════════════════
def capture(mod, calls, style):
    """把模块的 write(...) 换成内存捕获，按 calls 调 build 函数。返回 {文件名: dict}。"""
    cap = {}

    def grab(*a, **k):
        # 兼容两种 write 形状：m34 的 (name, sid, title, note, els, extra=None) /
        # m33 的 (name, obj)。以后生成器改签名时，这里只需加一支。
        a = list(a)
        if len(a) >= 5 and isinstance(a[4], (list, tuple)):
            name, sid, title, note, els = a[0], a[1], a[2], a[3], a[4]
            extra = a[5] if len(a) > 5 else k.get("extra")
            d = {"id": sid, "title_cn": title, "owner": "M34", "note": note}
            if extra:
                d.update(extra)
            d["elements"] = list(els)
        elif len(a) == 2 and isinstance(a[1], dict):
            name, d = a[0], a[1]
        else:
            raise AssertionError("未知的 write() 调用形状：%r / %r（生成器改了签名？）" % (a, k))
        cap[name] = json.loads(json.dumps(d, ensure_ascii=False))
        return None

    orig = mod.write
    mod.write = grab
    try:
        for fn, out in calls:
            if fn == "build_saveload_save":
                mod.build_saveload("save", "存档", "存档", "读档")
            elif fn == "build_saveload_load":
                mod.build_saveload("load", "读档", "读档", "存档")
            elif style == "return":
                # build 函数返回对象、由 __main__ 调 write（m33 的形状）
                mod.write(out, getattr(mod, fn)())
            else:
                getattr(mod, fn)()
    finally:
        mod.write = orig
    return cap


def load_module(name):
    import importlib
    return importlib.import_module(name)


def disk_of(f):
    p = os.path.join(SCR, f)
    if not os.path.exists(p):
        return None
    return json.loads(io.open(p, encoding="utf-8").read())


def files_md5():
    out = {}
    for p in sorted(glob.glob(os.path.join(SCR, "*.json"))):
        out[os.path.basename(p)] = hashlib.md5(io.open(p, "rb").read()).hexdigest()
    return out


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════
def main():
    args = sys.argv[1:]
    verbose = "--verbose" in args
    strict = "--strict" in args
    before = files_md5()

    print("=" * 78)
    print("生成器 ↔ 磁盘 一致性守门（write() 内存捕获法；**不写盘**）")
    print("  目录 %s ｜ 屏 %d 个 ｜ 模式 %s" % (SCR, len(before), "strict" if strict else "normal"))
    print("=" * 78)

    fails, warns, covered, ack_used, sup = [], [], set(), set(), []
    for modname, desc, style, status, calls in GENERATORS:
        print("\n### 生成器 %s%s" % (desc, "　★**已失效，不得再运行**" if status == "superseded" else ""))
        try:
            mod = load_module(modname)
        except Exception as ex:
            fails.append("[%s] 无法 import：%r" % (modname, ex))
            continue
        try:
            cap = capture(mod, calls, style)
        except Exception as ex:
            fails.append("[%s] 调用 build 函数失败：%r" % (modname, ex))
            continue
        for fn, out in calls:
            f = out
            covered.add(f)
            gen = cap.get(f)
            disk = disk_of(f)
            if disk is None:
                fails.append("[%s] 磁盘缺文件 %s（生成器会产出它）" % (modname, f))
                continue
            if gen is None:
                fails.append("[%s.%s] 未捕获到 %s（build 函数没调 write？）" % (modname, fn, f))
                continue
            cls, loss, drift = compare(gen, disk, f)
            if cls == "SYNCED":
                print("  %-20s SYNCED ✓（生成器可完整复现磁盘）" % f)
                continue
            ack = ACK_UNSYNC.get(f)
            tag = {"LOSS": "**LOSS**（重跑会丢数据）", "DRIFT": "DRIFT（有差异但不丢数据）"}[cls]
            verdict = "已登记（ACK）" if (cls == "LOSS" and ack) else ("FAIL" if cls == "LOSS" else "只警告")
            print("  %-20s %-28s → %s ｜ 元素 %d 件 ｜ 差异 丢%d/改%d"
                  % (f, tag, verdict, len(gen.get("elements") or []), len(loss), len(drift)))
            if ack:
                ack_used.add(f)
                print("        ⚠ **已知不同步**（责任方：%s）" % ack[0])
                print("          本屏的生成器入口：%s（有入口 ⇒ 属「有生成器但落后」，重跑会真抹数据）"
                      % ack[1])
                print("          理由：%s" % ack[2])
                print("          **重跑会丢的清单**：")
                for x in loss:
                    print("            - %s" % x)
            else:
                for x in loss:
                    if status == "superseded":
                        sup.append("[%s] %s" % (f, x))
                    else:
                        print("        ✗ " + x)
                        if cls == "LOSS":
                            fails.append("[%s] %s" % (f, x))
            for x in (drift if verbose else drift[:6]):
                print("        ~ " + x)
            if len(drift) > 6 and not verbose:
                print("        ~ …另有 %d 处值差异（--verbose 全列）" % (len(drift) - 6))
            if status == "superseded":
                sup.append("[%s] 与失效生成器有 %d 处值差异" % (f, len(drift)))
            elif cls == "DRIFT" and strict:
                fails.append("[%s] --strict：与生成器不一致（%d 处）" % (f, len(drift)))
            elif cls == "DRIFT":
                warns.append("[%s] 与生成器有 %d 处值差异（不丢数据；重跑会改写它们）" % (f, len(drift)))

    if sup:
        print("\n### ★ 已失效生成器的处置（**不得再运行**，否则覆盖盘上数据 + 引用缺图）")
        print("  %s 的 build 函数产出的是**旧素材体系**（`ui/x_gen_sd_*.png` 等，"
              "盘上已不存在）" % "m33_rebuild_screens.py")
        print("  盘上现值由后续工作改写（M12/M13 的 1920 迁移 + M34 的 `x_ui_*` 素材统一）⇒")
        print("  重跑它 = 覆盖 + 引用缺图（`verify_ui` 的 [1][2] 会失败）。")
        print("  该模块其余 build 函数（同一屏已由 m34 重建）已整体作废，留档如下：")
        for k, v in sorted(SUPERSEDED.items()):
            print("    · %s —— %s" % (k, v))
        print("  盘上仍会被它改坏的屏（清单）：")
        for x in sup:
            print("    · %s" % x)

    # 无生成器的屏（登记来源；不存在"被重跑抹掉"的风险）
    print("\n### 无 build 函数的屏（不会被任何生成器重跑抹掉）")
    for p in sorted(glob.glob(os.path.join(SCR, "*.json"))):
        b = os.path.basename(p)
        if b in covered or b == "_index.json":
            continue
        if b in NO_GEN:
            print("  %-20s 来源：%s" % (b, NO_GEN[b]))
        else:
            print("  %-20s ⚠ 未登记来源（生成器没有它、NO_GEN 也没写它）" % b)
            warns.append("[%s] 未登记来源（既无 build 函数也未在 NO_GEN 说明）" % b)

    # 登记表过期检查
    for f, (owner, gen, why) in ACK_UNSYNC.items():
        if f not in ack_used:
            warns.append("[ACK_UNSYNC] %s 已不再丢数据（生成器已修好 / 已被别的生成器接管）"
                         "⇒ 该条目可删除" % f)

    # ── ★ 第 3 批：非屏产物专项闸门（`GENERATED_ARTIFACTS`）────────────────
    print("\n### 非屏产物（生成器产出、但不在 `screens/` 下）· 专项闸门")
    for rel, gen_desc, status, why in GENERATED_ARTIFACTS:
        print("  %-28s 生成器：%s" % (rel, gen_desc))
        print("  %-28s 状态：%s" % ("", status))
    qk, qk_notes = check_tjs_quoted_keys()
    print("\n  【闸门 G-3a】`ui_layout.tjs` 不得含带引号的字典键（TJS2 语法炸弹防回归）")
    for n in qk_notes:
        print("      · %s" % n)
    if qk:
        for x in qk:
            print("      ✗ %s" % x)
            fails.append(x)
    else:
        print("      ✓ 通过（正文无 `\"k\": v` 非法键；正向变异必被抓、反向变异不误判；"
              "生成器对非标识符键确实走逗号式 ⇒ 非恒真）")
    fl, fl_notes = check_flow_data_no_legacy_ids()
    print("\n  【闸门 G-3b】`ui_flow_data.tjs` 不得再含旧元素寻址值（`flow.*`）")
    for n in fl_notes:
        print("      · %s" % n)
    if fl:
        for x in fl:
            print("      ✗ %s" % x)
            fails.append(x)
    else:
        print("      ✓ 通过（无 `flow.*` 旧 id；拓扑结构 `UIFlowData/nodes/edges/buses/fragments` 齐备）")

    print("\n" + "-" * 78)
    print("覆盖：生成器产出屏 %d 个 ｜ 登记表 ACK 命中 %d 条 ｜ 失效生成器待处置 %d 条"
          % (len(covered), len(ack_used), len(sup)))
    if warns:
        print("警告（不致命）：")
        for x in warns:
            print("  ~ " + x)
    after = files_md5()
    same = (after == before)
    print("落盘自证：运行前后 layout/screens/*.json 的 md5 %s（%d 个文件）"
          % ("**完全一致** ✓" if same else "**不一致** ✗", len(before)))
    if not same:
        for k in sorted(set(list(before) + list(after))):
            if before.get(k) != after.get(k):
                print("   ✗ %s：%s → %s" % (k, before.get(k), after.get(k)))
        fails.append("[自证] 本脚本改动了 layout/screens（守门必须只读！）")
    if fails:
        print("结果：**%d 项失败**" % len(fails))
        for x in fails[:40]:
            print("  ✗ " + x)
        rc = 1
    else:
        print("结果：**全部通过**（没有「重跑即抹」的未登记风险；已知不同步均已登记并列出会丢什么）")
        rc = 0

    if "--selfcheck" in sys.argv:
        rc = selfcheck(rc) or rc
        print("（主判定退出码 = %d；自证不影响它）" % rc)
    return rc


# ══════════════════════════════════════════════════════════════════════
# 反向自证（内存里造，不动磁盘）
# ══════════════════════════════════════════════════════════════════════
def selfcheck(rc_before):
    import copy
    print("\n" + "=" * 78)
    print("反向自证（内存构造，不动磁盘）")
    print("=" * 78)
    base = {
        "id": "zz", "title_cn": "自证", "owner": "M34", "note": "n",
        "elements": [
            {"id": "z.a", "kind": "hit", "z": 1, "x": 0, "y": 0, "w": 10, "h": 10, "action": "close"},
            {"id": "z.b", "kind": "image", "z": 2, "x": 0, "y": 0, "w": 10, "h": 10, "asset": "ui/x.png"},
        ],
    }
    ok = True

    # A：磁盘多于生成器（多一件元素）= title/choices 那类静默清空
    gen = copy.deepcopy(base)
    disk = copy.deepcopy(base)
    disk["elements"].append({"id": "z.c", "kind": "image", "z": 3, "x": 0, "y": 0, "w": 5, "h": 5,
                             "asset": "ui/y.png", "state_group": "zz.g"})
    cls, loss, drift = compare(gen, disk, "zz.json")
    print("\n【A 磁盘多一件元素（重跑会删它）】预期 LOSS")
    print("    → 判为 %s；丢 %d 条：%s" % (cls, len(loss), loss))
    if cls != "LOSS" or not loss:
        ok = False; print("    ✗ 未判为 LOSS（不符合预期）")

    # B：受保护字段被抹（磁盘带 state_group，生成器没有）
    gen = copy.deepcopy(base)
    disk = copy.deepcopy(base)
    disk["elements"][0]["state_group"] = "zz.g"
    disk["elements"][1]["state_assets"] = {"normal": "ui/x.png"}
    cls, loss, drift = compare(gen, disk, "zz.json")
    print("\n【B 受保护字段（state_group / state_assets）在磁盘上、生成器没有】预期 LOSS")
    print("    → 判为 %s；丢 %d 条：%s" % (cls, len(loss), loss))
    if cls != "LOSS" or len(loss) != 2:
        ok = False; print("    ✗ 未判为 LOSS/条数不对（不符合预期）")

    # C：只差 note / 只差一个值 ⇒ DRIFT（不误报成 LOSS）
    gen = copy.deepcopy(base)
    disk = copy.deepcopy(base)
    disk["elements"][0]["note"] = "备注改过"
    disk["elements"][1]["z"] = 9
    cls, loss, drift = compare(gen, disk, "zz.json")
    print("\n【C 只差 note 与一个 z 值】预期 DRIFT（不得误报 LOSS）")
    print("    → 判为 %s；丢 %d 条 / 值差 %d 条" % (cls, len(loss), len(drift)))
    if cls != "DRIFT" or loss:
        ok = False; print("    ✗ 误报（不符合预期）")

    print("\n自证结果：%s" % ("三项均按预期 ✓" if ok else "**有项不符合预期** ✗"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
