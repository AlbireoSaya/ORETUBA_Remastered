# UI清单.md —— 《我们没有翅膀——格雷塔迦露德与柳木原》UI 组 M1 资产契约

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：历史快照（M1–M22 期资产契约；正文数字多数已被后续批次取代，保留留痕） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`
> **2026-10-09 校准指针**：现行资产＝**1359 件 / 95.94 MiB**（族级计数见 `UI组_交付总纲.md` §2.1 与 `交付包校验收据.md` ①；逐件文件清单见 `复刻\asset_index.js`）——本件末节「当前口径见 §一.4（153 件）」已不成立；§二 图片化日文的现行处置＝**保留 132 / 弃用 497**（见 `素材裁决与图片化日文风险上报.md` §七）。

> Issue：`ISSUE-20260919-11`（UI 美术组 · M1）｜ 分支：`issue/ISSUE-20260919-11-greta-ui`
> **本文件是总纲 §七 I3 契约件**：编程组按「在 krkr 中的加载方式」列直接调用，无需再翻素材目录。
> 生成链：`工具/make_assets.py` 产出资产 + `_工作/M1_证据/asset_manifest.tsv`；
> 一致性由 `工具/verify_ui.py` 强制校验（引用完整性 / 尺寸 / 三处数据一致 / 硬编码扫描 / PNG 合法性 / 体积预算）。

## 〇、命名与路径契约（**先读这一节**）

| 项 | 约定 |
| --- | --- |
| 资产根 | `工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/krkr/assets/ui/` |
| layout 的 asset 串 | `ui/<原名>.png`（如 `ui/meswin.png`） |
| 物理文件名 | **asset 串的 basename** → `<原名>.png`（如 `meswin.png`）。**目录本身已提供 `ui/` 语义，文件名不加前缀** |
| UI 组自制 / 重制件 | `x_<语义>.png`（如 `x_mask_rule000_1x.png`）；`panel_frame.png` 由 `if_*` 八件拼合 |
| 取件原则 | A 类**逐字节 1:1**（不缩放、不重编码）；B 类只做「缩小 / 重采样 / 拼合」，**任何素材本体都不放大** |
| 体积 | 本集 **119 件 / 14.57 MB**（预算 **16 MB**，主代理 2026-09-19 由 12 MB 放宽；含片尾角色卡 `sr_01..24`）。**M12 起预算 40 MB**，见下方 M12 注。<br>🔁 **M16 更正（2026-09-20，主代理裁决）**：件数 **119 → 138 件**，总体积 **14.57 → 45.04 MB**（磁盘实测），预算 **40 → 48 MB**。依据：画布 ×1.5 后资产像素面积 ×2.25（16 × 2.25 = 36），再加 M11 的 `x_gen_*` 17 件（9.34 MB）与 `x_title_*` 2 件，取整留余量定为 **48 MB**。沿革：12 MB（M1 原定）→ 16 MB（2026-09-19）→ 40 MB（M12）→ **48 MB（本注）** |
| 画布基线 | **1920×1080**（M12 于 2026-09-20 由 1280×720 基线 ×1.5 迁移；窗口化按 `setZoom(2,3)` 呈现 1280×720）。`layout/_root.json` 的 `canvas_baseline` 字段即幂等标记 |
| 九宫格边框件现参数 | `panel_frame.png` 现为 **41×17**，九宫格边距 **`l=20, t=8, r=20, b=8`**（= 20/1/20 × 8/1/8，中心 1×1 透明）；拼合原料 `if_*` 现为 `20×8`（四角，4 件）/ `2×8`（上下边，2 件）/ `20×2`（左右边，2 件）。旧值 27×11 / `l=13,t=5,r=13,b=5` 见 §三 与 M12 注 |
| ×1.5 取整口径（资源组方案 §十 **U5**，UI 组裁定） | 几何值与字号：`round_half_up(v × 1.5)`；九宫格边距：`max(1, round_half_up(v × 1.5))`。其中 `round_half_up(x) = floor(x + 0.5)`（**.5 一律进位**）。**不用** Python 内置 `round()`——它是 banker's rounding（对 7×1.5=10.5 得 10、对 5×1.5=7.5 得 8），同批数据两个进位方向，不可复现；half-up 在 Python / TJS / JS 下结果一致 |

> ✅ **命名口径已裁决（主代理 2026-09-19）**：物理文件名 = asset 串的 **basename**（`ui/meswin.png` → `meswin.png`），
> 目录 `krkr/assets/ui/` 本身提供 `ui/` 语义，**文件名不加 `ui_` 前缀**。
> M2（`krkr/game/ui_asset.tjs`）与 M3（`复刻/replica.js`）的既有解析方式与此一致，**无需改动**；
> M1 的产物已按此口径重命名（119 件），`verify_ui.py` 已同步并通过。原裁决点 R-1 关闭。

> 🔁 **M12 画布基线迁移注（2026-09-20）**：画布 1280×720 → **1920×1080**（总纲 D1 第三条修订注）。
> `layout/` 全部数值由 `工具/migrate_1920.py` 机械 ×1.5 迁移（可复跑、幂等、带自证）；
> 迁移前 1280 版留档在 `_工作/M12_备份_1280/`，回滚方式与逐屏对照见 `_工作/M12_迁移报告.md`。
> **本表的「尺寸」列仍是 1280 基线资产的原尺寸**——M11 换入 ×1.5 资产集后须整表更新；
> `verify_ui.py` 的体积预算同步由 16 MB 调至 **40 MB**（像素面积 ×2.25，16 × 2.25 = 36，取整留余量）。
> 九宫格参数（如 `panel_frame.png` 的 `l=13,t=5,r=13,b=5`）在 layout 侧已按上表口径变为 `l=20,t=8,r=20,b=8`；
> 资产侧是否同步重做边距由 M11 决定。

> 🔁 **M16 文档同步注（2026-09-20）**：本表口径由 **M1 的 1280×720 / 119 件 / 14.57 MB / 预算 16 MB** 全面更新为
> **1920×1080 / 138 件 / 45.04 MB / 预算 48 MB**。资产集实际状态以 **§一.2（138 行全量表，磁盘实测）** 为准；
> §一（95 行）与 §一.1（17 行）保留为历史口径，仅作溯源。

> ★ **M17 收口注（2026-09-20）**：本表口径再更新为 **1920×1080 / 137 件 / 预算 48 MB**，并完成两项命名收口：
> ① **满屏遮罩族更名**：原文件名后缀 `_1280`（1280 基线时代遗留，实际已 1920×1080，名实不符）
>    → 现为 **`x_mask_ruleNNN_full.png`**（18 件）；`x_mask_ruleNNN_1x.png`（18 件）**不改名**（1× = 1440×816 是 4:3 内容区尺寸，名字仍对）。
>    同步更新：`krkr/game/startup.tjs` 的 `UI_TRANS_RULE` 常量、`工具/build_assets_1920.py` 的命名逻辑、本文档全部引用。
> ② **标题屏满幅背景件删除**：M13 已把标题屏背景改为 `ui/x_bg_system.png`，原件**已零引用**，
>    故从 `krkr/assets/ui/` 删除、并从 `工具/build_assets_1920.py` 的产出中移除（避免复跑又生成）。件数 138 → **137**。
> ③ **9 件功能图标缩小**：`工具/prep_generated.py` 的 `ICON_W` 由 **384 改 192** 并重跑（原 384 宽时 3×3 原生行高 1476px > 画布 1080，
>    迫使 `33_sysicons.json` 用 `nine{l:0,t:0,r:0,b:0}` 整图缩放，`w/h` ≠ PNG 实尺寸，绕开 `verify_ui.py` [2] 的 1:1 防线）；
>    现 9 件为宽 192 / 高 192–280，可**原生 1:1 摆放**，`33_sysicons.json` 已随之改为不带 `nine`。
> ④ §一.1 的图标尺寸列（M11 增量口径）亦按 ③ 更新为 192 宽；§一 的 1280 基线行仅作文件名更名，其「尺寸」列仍为 1280 时代口径。
> 原 M16 注中「后缀不改」的裁决**已被本注取代**。

> ★ **M20 注（2026-09-20）**：M20 新增 **15 件** AI 重导派生件（`x_gen_logo.png` 1 件 + `x_gen_menu_*` 14 件），
> 目录内 PNG 由 **137 → 152 件**，总体积 **45.04 → 43.80 MB**（M20 后磁盘实测；预算 48 MB 仍有余量）。
> 当前口径以 **§一.3** 为准（§一.2 保留为 M17 时点历史口径，其自证行已加 M20 注指向 §一.3）。
> 用途：标题屏（`01_title.json`）改用 AI 素材 logo + 两态菜单按钮，取代 M9 的 `x_title_logo.png` 与文字菜单。

## 一、资产总表

**五列：文件名 / 尺寸 / 九宫格或锚点参数 / 在 krkr 中的加载方式 / 对应原版 UI 元素**

| # | 文件名 | 尺寸 | 九宫格或锚点参数 | 在 krkr 中的加载方式 | 对应原版 UI 元素 |
|---:|---|---|---|---|---|
| 1 | `panel_frame.png` | 27×11 | 九宫格 `l=13, t=5, r=13, b=5`（源 27×11：左中右 13/1/13，上中下 5/1/5，中心 1×1 透明） | `loadImages("ui/panel_frame.png")` + `copy9Patch(13,5,13,5, w, h)`（签名未实测，M2 实测）；退路 `copyRect` 三切片：四角 13×5 1:1、上下边 1×5 横向拉伸、左右边 13×1 纵向拉伸 | 原版通用窗框（`if_*` 八件拼合；中心透明，面板填充由 `rect` 元素承担） |
| ~~2~~ | ~~`ec5_bg.png`~~ | 800×600 | ~~卡内 1:1（不拉伸，H6）~~ | ~~`loadImages` + `setSizeToImageSize()`（1:1）~~ | 原版章标题卡 `ec5_bg`（红羽；同族 ec1–ec4/ec6 含烘焙章名已剔除，见 C 表）。**★ M43（2026-09-23，用户裁定）**：`chapter`（主线·章节选择）屏**已删除** ⇒ 本件不再被任何屏引用；实测 `krkr/assets/ui/` 内**本无 `ec5*` 件**（未接入资产集）。条目保留作溯源。 |
| 3 | `selwin.png` | 650×193 | 锚点 左上（M5 定） | `loadImages` + `setSizeToImageSize()`（1:1） | 原版选择支窗 `selwin`（空白件） |
| 4 | `cf_frame.png` | 322×42 | 按行 1:1 平铺 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版配置行框 `cf_frame` / `cf_frm_a`（空白件） |
| 5 | `cf_frm_a.png` | 322×42 | 按行 1:1 平铺 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版配置行框 `cf_frame` / `cf_frm_a`（空白件） |
| 6 | `meswin.png` | 1057×174 | 锚点 左上 (112,522)（layout `dlg.window`） | `loadImages("ui/meswin.png")` + `setSizeToImageSize()`（1:1 不拉伸） | 原版对话窗底 `meswin`（蓝紫渐变 + 羽毛装饰；原 800×600 对话框底图） |
| 7 | `dlg_bg_26.png` | 522×270 | 锚点 左上（M5 对话窗备选皮肤） | `loadImages` + `setSizeToImageSize()`（1:1） | PSV 纯空白对话窗 `dlg_bg_26/27/28`（三件逐字节相同） |
| 8 | `dlg_bg_27.png` | 522×270 | 锚点 左上（M5 对话窗备选皮肤） | `loadImages` + `setSizeToImageSize()`（1:1） | PSV 纯空白对话窗 `dlg_bg_26/27/28`（三件逐字节相同） |
| 9 | `dlg_bg_28.png` | 522×270 | 锚点 左上（M5 对话窗备选皮肤） | `loadImages` + `setSizeToImageSize()`（1:1） | PSV 纯空白对话窗 `dlg_bg_26/27/28`（三件逐字节相同） |
| 10 | `x_mask_rule000_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule000_full.png")`；同上 | 原版 PSV 转场遮罩 `rule000`（水平条纹(百叶窗,密度渐变)）→ 1280×720 重采样版 |
| 11 | `x_mask_rule001_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule001_full.png")`；同上 | 原版 PSV 转场遮罩 `rule001`（对角渐变(亮->暗)）→ 1280×720 重采样版 |
| 12 | `x_mask_rule002_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule002_full.png")`；同上 | 原版 PSV 转场遮罩 `rule002`（同心圆(靶心)）→ 1280×720 重采样版 |
| 13 | `x_mask_rule003_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule003_full.png")`；同上 | 原版 PSV 转场遮罩 `rule003`（对角渐变(暗带)）→ 1280×720 重采样版 |
| 14 | `x_mask_rule004_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule004_full.png")`；同上 | 原版 PSV 转场遮罩 `rule004`（径向渐变(vignette)）→ 1280×720 重采样版 |
| 15 | `x_mask_rule005_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule005_full.png")`；同上 | 原版 PSV 转场遮罩 `rule005`（噪波dissolve(粗颗粒)）→ 1280×720 重采样版 |
| 16 | `x_mask_rule006_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule006_full.png")`；同上 | 原版 PSV 转场遮罩 `rule006`（噪波dissolve(细颗粒)）→ 1280×720 重采样版 |
| 17 | `x_mask_rule008_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule008_full.png")`；同上 | 原版 PSV 转场遮罩 `rule008`（垂直条纹(密度渐变)）→ 1280×720 重采样版 |
| 18 | `x_mask_rule009_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule009_full.png")`；同上 | 原版 PSV 转场遮罩 `rule009`（垂直条纹(等密中等)）→ 1280×720 重采样版 |
| 19 | `x_mask_rule013_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule013_full.png")`；同上 | 原版 PSV 转场遮罩 `rule013`（水平条纹(等密极密)）→ 1280×720 重采样版 |
| 20 | `x_mask_rule026_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule026_full.png")`；同上 | 原版 PSV 转场遮罩 `rule026`（放射星芒）→ 1280×720 重采样版 |
| 21 | `x_mask_rule047_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule047_full.png")`；同上 | 原版 PSV 转场遮罩 `rule047`（径向光晕(中心亮)）→ 1280×720 重采样版 |
| 22 | `x_mask_rule061_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule061_full.png")`；同上 | 原版 PSV 转场遮罩 `rule061`（四象限擦除）→ 1280×720 重采样版 |
| 23 | `x_mask_rule065_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule065_full.png")`；同上 | 原版 PSV 转场遮罩 `rule065`（扇形擦除）→ 1280×720 重采样版 |
| 24 | `x_mask_rule067_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule067_full.png")`；同上 | 原版 PSV 转场遮罩 `rule067`（棋盘(3D网格)）→ 1280×720 重采样版 |
| 25 | `x_mask_rule071_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule071_full.png")`；同上 | 原版 PSV 转场遮罩 `rule071`（云状噪波dissolve）→ 1280×720 重采样版 |
| 26 | `x_mask_rule076_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule076_full.png")`；同上 | 原版 PSV 转场遮罩 `rule076`（Voronoi晶格）→ 1280×720 重采样版 |
| 27 | `x_mask_rule097_full.png` | 1280×720 | 满屏 1280×720（重采样新建素材） | `loadImages("ui/x_mask_rule097_full.png")`；同上 | 原版 PSV 转场遮罩 `rule097`（螺旋(涡旋)）→ 1280×720 重采样版 |
| 28 | `x_mask_rule000_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule000_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule000`（水平条纹(百叶窗,密度渐变)；960×544 **L 灰度**） |
| 29 | `x_mask_rule001_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule001_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule001`（对角渐变(亮->暗)；960×544 **L 灰度**） |
| 30 | `x_mask_rule002_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule002_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule002`（同心圆(靶心)；960×544 **L 灰度**） |
| 31 | `x_mask_rule003_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule003_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule003`（对角渐变(暗带)；960×544 **L 灰度**） |
| 32 | `x_mask_rule004_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule004_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule004`（径向渐变(vignette)；960×544 **L 灰度**） |
| 33 | `x_mask_rule005_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule005_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule005`（噪波dissolve(粗颗粒)；960×544 **L 灰度**） |
| 34 | `x_mask_rule006_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule006_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule006`（噪波dissolve(细颗粒)；960×544 **L 灰度**） |
| 35 | `x_mask_rule008_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule008_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule008`（垂直条纹(密度渐变)；960×544 **L 灰度**） |
| 36 | `x_mask_rule009_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule009_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule009`（垂直条纹(等密中等)；960×544 **L 灰度**） |
| 37 | `x_mask_rule013_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule013_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule013`（水平条纹(等密极密)；960×544 **L 灰度**） |
| 38 | `x_mask_rule026_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule026_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule026`（放射星芒；960×544 **L 灰度**） |
| 39 | `x_mask_rule047_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule047_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule047`（径向光晕(中心亮)；960×544 **L 灰度**） |
| 40 | `x_mask_rule061_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule061_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule061`（四象限擦除；960×544 **L 灰度**） |
| 41 | `x_mask_rule065_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule065_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule065`（扇形擦除；960×544 **L 灰度**） |
| 42 | `x_mask_rule067_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule067_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule067`（棋盘(3D网格)；960×544 **L 灰度**） |
| 43 | `x_mask_rule071_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule071_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule071`（云状噪波dissolve；960×544 **L 灰度**） |
| 44 | `x_mask_rule076_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule076_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule076`（Voronoi晶格；960×544 **L 灰度**） |
| 45 | `x_mask_rule097_1x.png` | 960×544 | 满屏 1:1（960×544，覆盖 `otv` 内容区；不在 1280 画布上拉伸） | `loadImages("ui/x_mask_rule097_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule097`（螺旋(涡旋)；960×544 **L 灰度**） |
| 46 | `nm_frm_a.png` | 222×36 | 锚点 左上 (150,486)（layout `dlg.namebox`） | `loadImages("ui/nm_frm_b.png")` + `setSizeToImageSize()` | 原版角色名框 `nm_frm_*`（a/b/g 三皮肤，本作取 b） |
| 47 | `nm_frm_b.png` | 222×36 | 锚点 左上 (150,486)（layout `dlg.namebox`） | `loadImages("ui/nm_frm_b.png")` + `setSizeToImageSize()` | 原版角色名框 `nm_frm_*`（a/b/g 三皮肤，本作取 b） |
| 48 | `nm_frm_g.png` | 222×36 | 锚点 左上 (150,486)（layout `dlg.namebox`） | `loadImages("ui/nm_frm_b.png")` + `setSizeToImageSize()` | 原版角色名框 `nm_frm_*`（a/b/g 三皮肤，本作取 b） |
| 49 | `if_bbar.png` | 1×5 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 50 | `if_lb.png` | 13×5 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 51 | `if_lbar.png` | 13×1 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 52 | `if_lt.png` | 13×5 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 53 | `if_rb.png` | 13×5 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 54 | `if_rbar.png` | 13×1 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 55 | `if_rt.png` | 13×5 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 56 | `if_tbar.png` | 1×5 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 57 | `paper_0.png` | 192×8 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 58 | `paper_1.png` | 192×8 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 59 | `paper_2.png` | 192×8 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 60 | `paper_3.png` | 192×8 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 61 | `paper_4.png` | 384×16 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 62 | `paper_5.png` | 384×16 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 63 | `paper_6.png` | 384×16 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 64 | `paper_7.png` | 384×16 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 65 | `snow_0.png` | 6×6 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 66 | `snow_1.png` | 8×8 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 67 | `snow_2.png` | 10×10 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 68 | `snow_3.png` | 12×12 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 69 | `snow_4.png` | 14×14 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 70 | `cf_bar.png` | 26×36 | 滑块按比例摆放 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版滚动条滑块 `cf_bar`（纵向）/ `cf_vbar`（横向） |
| 71 | `cf_vbar.png` | 56×6 | 滑块按比例摆放 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版滚动条滑块 `cf_bar`（纵向）/ `cf_vbar`（横向） |
| 72 | `sel00a.png` | 723×7 | **本作不使用**（宽 723 > 面板 376，且不缩放） | 不加载；仅作原版素材溯源保留 | 原版选择高亮条 `sel00a/b/g`、`sel01b`、`sel02b` |
| 73 | `sel00b.png` | 723×7 | **本作不使用**（宽 723 > 面板 376，且不缩放） | 不加载；仅作原版素材溯源保留 | 原版选择高亮条 `sel00a/b/g`、`sel01b`、`sel02b` |
| 74 | `sel00g.png` | 723×7 | **本作不使用**（宽 723 > 面板 376，且不缩放） | 不加载；仅作原版素材溯源保留 | 原版选择高亮条 `sel00a/b/g`、`sel01b`、`sel02b` |
| 75 | `sel01b.png` | 723×30 | **本作不使用**（宽 723 > 面板 376，且不缩放） | 不加载；仅作原版素材溯源保留 | 原版选择高亮条 `sel00a/b/g`、`sel01b`、`sel02b` |
| 76 | `sel02b.png` | 723×8 | **本作不使用**（宽 723 > 面板 376，且不缩放） | 不加载；仅作原版素材溯源保留 | 原版选择高亮条 `sel00a/b/g`、`sel01b`、`sel02b` |
| 77 | `sm_base.png` | 182×348 | 锚点 左上（M5 定） | `loadImages` + `setSizeToImageSize()`（1:1） | 原版系统菜单底板 `sm_base` / `sm_base2`（空白件） |
| 78 | `sm_base2.png` | 182×265 | 锚点 左上（M5 定） | `loadImages` + `setSizeToImageSize()`（1:1） | 原版系统菜单底板 `sm_base` / `sm_base2`（空白件） |
| 79 | `ms_cursr.png` | 138×11 | 锚点 左上 (1002,668)（layout `dlg.cursor`） | `loadImages("ui/ms_cursr.png")` + `setSizeToImageSize()`；`anim.mode=blink` 周期 700ms | 原版文本推进光标 `ms_cursr` |
| 80 | `ec_bg01.png` | 388×570 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 81 | `gc_asu01.png` | 280×105 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 82 | `th_ai.png` | 198×99 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 83 | `th_asu.png` | 198×99 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 84 | `th_bar.png` | 68×5 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 85 | `ui_bg01.png` | 280×105 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 86 | `tl1_bg.png` | 800×600 | 锚点 左上 (40,150)（layout `title.bg_art`，仅 tl1_bg1） | `loadImages` + `setSizeToImageSize()`（1:1 不拉伸） | 原版标题背景 `tl1_bg1`/`tl1_bg2`（幻想侧风景 1200×450）、`tl1_bg`/`tl2_bg1`（含女主立绘 800×600） |
| 87 | `tl1_bg1.png` | 1200×450 | 锚点 左上 (40,150)（layout `title.bg_art`，仅 tl1_bg1） | `loadImages` + `setSizeToImageSize()`（1:1 不拉伸） | 原版标题背景 `tl1_bg1`/`tl1_bg2`（幻想侧风景 1200×450）、`tl1_bg`/`tl2_bg1`（含女主立绘 800×600） |
| 88 | `tl1_bg2.png` | 1200×450 | 锚点 左上 (40,150)（layout `title.bg_art`，仅 tl1_bg1） | `loadImages` + `setSizeToImageSize()`（1:1 不拉伸） | 原版标题背景 `tl1_bg1`/`tl1_bg2`（幻想侧风景 1200×450）、`tl1_bg`/`tl2_bg1`（含女主立绘 800×600） |
| 89 | `tl2_bg1.png` | 800×600 | 锚点 左上 (40,150)（layout `title.bg_art`，仅 tl1_bg1） | `loadImages` + `setSizeToImageSize()`（1:1 不拉伸） | 原版标题背景 `tl1_bg1`/`tl1_bg2`（幻想侧风景 1200×450）、`tl1_bg`/`tl2_bg1`（含女主立绘 800×600） |
| 90 | `ga_frame.png` | 166×126 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |
| 91 | `sv_f1.png` | 17×11 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |
| 92 | `sv_f2.png` | 18×11 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |
| 93 | `sv_f3.png` | 18×11 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |
| 94 | `sv_f4.png` | 18×11 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |
| 95 | `sv_f5.png` | 18×11 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |

**自证：本表数据行数 = 95 ｜ 目录内 PNG 件数 = 95 ｜ 二者相等 = 是。**

> 🔁 **M16 更正注（2026-09-20）**：上行自证**已过期，保留不改**。目录内实际 PNG 现为 **138 件**（磁盘实测），
> 故「95 == 95」仅对 M1 时点成立。**当前口径见 §一.2（138 行全量表）**，其自证行为「行数 == 目录内 PNG 数 == 138」。

> ⚠ **2026-09-20 M11 实测更正（只补不改本表）**：本表是 **M1（1280×720 基线）**口径。
> 目录内实际 PNG 为 **121 件** = 本表 95 + `sr_01..24`（24 件，§二.1 递延族）+ 标题屏自制 2 件（`x_title_logo.png` 与已删的标题满幅背景件，见 §三 自制表）。
> **M11 起全部 121 件的尺寸已按 1920×1080 基线重建（`round_half_up(原尺寸 × 1.5)`，来源改用 `资源组\美术统一_超分\系统UI\` 的 2× 版）**，
> ★ **M17 更正**：上行的标题满幅背景件已删除（M13 起零引用），故**当前目录内 PNG = 137 件**（= 120 + 17），以 §一.2 为准。
> 故**本表「尺寸」列（除九宫格参数外）一律失效**，以 `_工作\M11_证据\build_assets_1920_manifest.json` 为准。
> 新增件见下节 §一.1；重建器 `工具\build_assets_1920.py`（幂等可复跑）。

### 一.1 M11 新增资产（AI 生图派生 + 系统屏满幅背景，1920×1080 基线）

> 生成器：`工具\prep_generated.py`（幂等可复跑）｜ 几何：`_工作\M11_生成几何.json`｜ 证据：`_工作\M11_证据\`
> 命名前缀 `x_gen_` = 「AI 生图派生」；源素材在 `生图入料\生成结果\`，**全程只读**（只在内存副本上裁/缩）。
> 五列口径同 §一。

| # | 文件名 | 尺寸 | 九宫格或锚点参数 | 在 krkr 中的加载方式 | 对应原版 UI 元素 |
|---:|---|---|---|---|---|
| 1 | `x_gen_icon_01_qsave.png` | **351×234（M22 重做）** | 锚点 左上；**1:1**（9 件同尺寸，按 `_工作\M22_生成几何.json` 的 `icons.grid` 摆放；内容位置见 `content_bbox_in_cell`） | `loadImages("ui/x_gen_icon_01_qsave.png")` + `setSizeToImageSize()`（1:1） | 原版功能键**文字**（`sm_save`/`sv_*` 族）与 `skp1_icon` 的烘焙状态文字——中文界面须**引擎绘字**，故图标由 AI 生图补 |
| 2 | `x_gen_icon_02_qload.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版「クイックロード」文字位（原版无独立图标） |
| 3 | `x_gen_icon_03_skip.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版 `sm_skip` / `skp1_icon` 的 SKIP 状态 |
| 4 | `x_gen_icon_04_prev.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版回想/上一页（`01_prev`）文字位 |
| 5 | `x_gen_icon_05_save.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版 `sm_save`（セーブ） |
| 6 | `x_gen_icon_06_load.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版 `sm_load`（ロード） |
| 7 | `x_gen_icon_07_config.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版 `sm_cfg`（環境設定） |
| 8 | `x_gen_icon_08_close.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版 `th_close` / `sm_win`（ウィンドウ消去） |
| 9 | `x_gen_icon_09_repeat.png` | **351×234（M22 重做）** | 同上 | 同上 | 原版 `sm_auto`（オート，循环箭头） |
| 10 | `x_gen_dialog.png` | 1680×946 | 锚点 左上；**1:1**（宽度 = 1920 画布的 87.5%）；名字框/正文区矩形见 `_工作\M11_生成几何.json` 的 `dialog` | `loadImages("ui/x_gen_dialog.png")` + `setSizeToImageSize()`（1:1 不拉伸） | 原版对话窗底 `meswin`（1057×174）+ 角色名框 `nm_frm_*` —— **一张整图含名字框**，取代两者。**M22 起保留不删**，是否切换到 `x_gen_dialog2.png` 由 M23 决定 |
| 11 | `x_gen_flownode_1_normal.png` | **562×108（M22 重做）** | 锚点 左上；**1:1**（4 件倍率相同、尺寸各异，属源设计）；矩形见 `_工作\M22_生成几何.json` 的 `flownodes` | `loadImages` + `setSizeToImageSize()`（1:1） | 原版**无**（`flowchart` 屏是新屏）；对应剧情流程图「普通章节」节点条 |
| 12 | `x_gen_flownode_2_badend.png` | **584×112（M22 重做）** | 同上 | 同上 | 原版无；对应「Bad End」节点条（羽毛 + 血滴） |
| 13 | `x_gen_flownode_3_important.png` | **577×112（M22 重做）** | 同上 | 同上 | 原版无；对应「重要章节」节点条（雪花 + 高亮蓝） |
| 14 | `x_gen_flownode_4_goodend.png` | **572×110（M22 重做）** | 同上 | 同上 | 原版无；对应「Good End」节点条（粉色 + 心） |
| 15 | `x_gen_fragpage.png` | 1920×1080 | **满幅 (0,0) 1:1**；标题/面板外框/**40 个格子（5 列 × 8 行，行优先）**矩形见 `_工作\M11_生成几何.json` 的 `fragpage` | `loadImages("ui/x_gen_fragpage.png")` + `setSizeToImageSize()`（满幅 1:1） | 原版**无**（`fragment` 屏是新屏）；版式参照 PSV 场景选择整页 `ss_bg1…5_full`（含烘焙文字，**不可用**）。★ **ISSUE-20260928-06（2026-09-28，用户裁定）**：`fragment`（番外·Fragment 选择）屏**已整体删除** ⇒ 本件不再被任何屏引用；**素材 `krkr/assets/ui/x_gen_fragpage.png` 保留原位不删**（用户「只删屏、保留动作/素材」）。条目保留作溯源。 |
| 16 | `x_gen_gallerypage.png` | 1920×1080 | **满幅 (0,0) 1:1**；左侧 4 框 / 预览大框 / 深色章节名条 / 4 条简介条矩形见 `_工作\M11_生成几何.json` 的 `gallerypage` | `loadImages("ui/x_gen_gallerypage.png")` + `setSizeToImageSize()`（满幅 1:1） | 原版 PSV 画廊整页 `gm_bg1`（960×659，含烘焙文字，**不可用**）+ `gl_chr1…12` 角色筛选标签 |
| 17 | `x_bg_system.png` | 1920×1080 | **满幅 (0,0) 1:1**（系统屏满幅背景，**不留黑边**） | `loadImages("ui/x_bg_system.png")` + `setSizeToImageSize()`（满幅 1:1）；压暗层 `veil` 保留 | 原版系统屏整页底图 `sys_menu` / `gm_bg1` / `bg_config_01`（均含烘焙文字，**不可用**） |

> **逐件变换方向**（详见 `_工作\M11_证据\prep_generated.log`）：
> 9 个图标 = **M22 重做**：整图 ×**0.685547** 一次缩放 → 3×3 等分（每件 351×234）。原做法（3×3 网格切分 → 每格 alpha 包围盒裁紧 → 缩到宽 192，M17 收口）**已废止**——它给 9 个元素施加了 0.762×–1.116× 的**不同倍率**，破坏相对大小（详见 §一.3 更正注）；
> `x_gen_dialog` = 1672×941 → 1680×946（**放大 1.0048×**）；4 条节点条 = **M22 重做**：整图 ×**0.491228** 一次缩放 → 按局部极小 y=240/468/696 切 4 条带（原「裁紧后缩到宽 1152」已废止，它给 4 条施加 0.970×–1.007× 的不同倍率）；
> `x_gen_fragpage` / `x_gen_gallerypage` = 整幅缩到 1920×1080（**放大 1.1483×**，用户明确授权超分/改分辨率）；
> `x_bg_system` = `bg63.png` 2904×1440 **中心裁 2560×1440**（裁掉两侧各 172 px，源宽高比 2.0167 > 16:9）→ **0.75× 下采样**到 1920×1080。

## 一.2 1920 基线资产总表（**137 行全量 · 磁盘实测 2026-09-20；M17 收口后**）

> **本表是当前唯一有效的资产契约表**（取代 §一 的 95 行历史口径与 §一.1 的 17 行增量口径，后两者保留不改作溯源）。
> 尺寸全部来自**磁盘实测**（PNG IHDR 解析，命令见本表末自证行），**非估算、非沿用旧值**。
> 五列口径同 §一；排列顺序：§一 原有 95 件 → `sr_01..24` → `x_title_*` → M11 的 `x_gen_*` / `x_bg_system`。
> 生成器：`工具\build_assets_1920.py`（基础 **120** 件，M17 删去标题满幅背景件后；几何与变换见 `_工作\M11_证据\build_assets_1920_manifest.json`）
> ＋ `工具\prep_generated.py`（AI 派生 17 件，几何见 `_工作\M11_生成几何.json`）。

| # | 文件名 | 尺寸（磁盘实测） | 九宫格或锚点参数 | 在 krkr 中的加载方式 | 对应原版 UI 元素 |
|---:|---|---|---|---|---|
| 1 | `panel_frame.png` | 41×17 | 九宫格 `l=20, t=8, r=20, b=8`（源 41×17：左中右 20/1/20，上中下 8/1/8，中心 1×1 透明） | `loadImages("ui/panel_frame.png")` + `copy9Patch(20,8,20,8, w, h)`（签名未实测，M2 实测）；退路 `copyRect` 三切片：四角 20×8 1:1、上下边 2×8 横向拉伸、左右边 20×2 纵向拉伸 | 原版通用窗框（`if_*` 八件拼合；中心透明，面板填充由 `rect` 元素承担） |
| ~~2~~ | ~~`ec5_bg.png`~~ | 1200×900 | ~~卡内 1:1（不拉伸，H6）~~ | ~~`loadImages` + `setSizeToImageSize()`（1:1）~~ | 原版章标题卡 `ec5_bg`（红羽；同族 ec1–ec4/ec6 含烘焙章名已剔除，见 C 表）。**★ M43（2026-09-23，用户裁定）**：`chapter`（主线·章节选择）屏**已删除** ⇒ 本件不再被任何屏引用；实测 `krkr/assets/ui/` 内**本无 `ec5*` 件**（未接入资产集）。条目保留作溯源。 |
| 3 | `selwin.png` | 975×290 | 锚点 左上（M5 定） | `loadImages` + `setSizeToImageSize()`（1:1） | 原版选择支窗 `selwin`（空白件） |
| 4 | `cf_frame.png` | 483×63 | 按行 1:1 平铺 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版配置行框 `cf_frame` / `cf_frm_a`（空白件） |
| 5 | `cf_frm_a.png` | 483×63 | 按行 1:1 平铺 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版配置行框 `cf_frame` / `cf_frm_a`（空白件） |
| 6 | `meswin.png` | 1586×261 | 锚点 左上（layout `dlg.window`） | `loadImages("ui/meswin.png")` + `setSizeToImageSize()`（1:1 不拉伸） | 原版对话窗底 `meswin`（蓝紫渐变 + 羽毛装饰；原 800×600 对话框底图） |
| 7 | `dlg_bg_26.png` | 783×405 | 锚点 左上（M5 对话窗备选皮肤） | `loadImages` + `setSizeToImageSize()`（1:1） | PSV 纯空白对话窗 `dlg_bg_26/27/28`（三件逐字节相同） |
| 8 | `dlg_bg_27.png` | 783×405 | 锚点 左上（M5 对话窗备选皮肤） | `loadImages` + `setSizeToImageSize()`（1:1） | PSV 纯空白对话窗 `dlg_bg_26/27/28`（三件逐字节相同） |
| 9 | `dlg_bg_28.png` | 783×405 | 锚点 左上（M5 对话窗备选皮肤） | `loadImages` + `setSizeToImageSize()`（1:1） | PSV 纯空白对话窗 `dlg_bg_26/27/28`（三件逐字节相同） |
| 10 | `x_mask_rule000_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材；后缀 `_full` = M17 由 1280 基线时代的旧后缀更名而来，原名与实尺寸不符） | `loadImages("ui/x_mask_rule000_full.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule000`（水平条纹(百叶窗,密度渐变)）→ 1920×1080 版 |
| 11 | `x_mask_rule001_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule001`（对角渐变(亮->暗)）→ 1920×1080 版 |
| 12 | `x_mask_rule002_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule002`（同心圆(靶心)）→ 1920×1080 版 |
| 13 | `x_mask_rule003_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule003`（对角渐变(暗带)）→ 1920×1080 版 |
| 14 | `x_mask_rule004_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule004`（径向渐变(vignette)）→ 1920×1080 版 |
| 15 | `x_mask_rule005_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule005`（噪波dissolve(粗颗粒)）→ 1920×1080 版 |
| 16 | `x_mask_rule006_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule006`（噪波dissolve(细颗粒)）→ 1920×1080 版 |
| 17 | `x_mask_rule008_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule008`（垂直条纹(密度渐变)）→ 1920×1080 版 |
| 18 | `x_mask_rule009_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule009`（垂直条纹(等密中等)）→ 1920×1080 版 |
| 19 | `x_mask_rule013_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule013`（水平条纹(等密极密)）→ 1920×1080 版 |
| 20 | `x_mask_rule026_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule026`（放射星芒）→ 1920×1080 版 |
| 21 | `x_mask_rule047_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule047`（径向光晕(中心亮)）→ 1920×1080 版 |
| 22 | `x_mask_rule061_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule061`（四象限擦除）→ 1920×1080 版 |
| 23 | `x_mask_rule065_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule065`（扇形擦除）→ 1920×1080 版 |
| 24 | `x_mask_rule067_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule067`（棋盘(3D网格)）→ 1920×1080 版 |
| 25 | `x_mask_rule071_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule071`（云状噪波dissolve）→ 1920×1080 版 |
| 26 | `x_mask_rule076_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule076`（Voronoi晶格）→ 1920×1080 版 |
| 27 | `x_mask_rule097_full.png` | 1920×1080 | 满屏 1920×1080（重采样新建素材） | 同上 | 原版 PSV 转场遮罩 `rule097`（螺旋(涡旋)）→ 1920×1080 版 |
| 28 | `x_mask_rule000_1x.png` | 1440×816 | 满屏 1:1（1440×816，覆盖 `otv` 内容区；不在画布上拉伸） | `loadImages("ui/x_mask_rule000_1x.png")`；转场经 `beginTransition(name, …, transsrc, options)` 或自行按 alpha 合成（**无 `setMaskImage`**） | 原版 PSV 转场遮罩 `rule000`（水平条纹(百叶窗,密度渐变)；源 960×544 **L 灰度**） |
| 29 | `x_mask_rule001_1x.png` | 1440×816 | 满屏 1:1（1440×816，覆盖 `otv` 内容区） | 同上 | 原版 PSV 转场遮罩 `rule001`（对角渐变(亮->暗)；源 **L 灰度**） |
| 30 | `x_mask_rule002_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule002`（同心圆(靶心)；源 **L 灰度**） |
| 31 | `x_mask_rule003_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule003`（对角渐变(暗带)；源 **L 灰度**） |
| 32 | `x_mask_rule004_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule004`（径向渐变(vignette)；源 **L 灰度**） |
| 33 | `x_mask_rule005_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule005`（噪波dissolve(粗颗粒)；源 **L 灰度**） |
| 34 | `x_mask_rule006_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule006`（噪波dissolve(细颗粒)；源 **L 灰度**） |
| 35 | `x_mask_rule008_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule008`（垂直条纹(密度渐变)；源 **L 灰度**） |
| 36 | `x_mask_rule009_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule009`（垂直条纹(等密中等)；源 **L 灰度**） |
| 37 | `x_mask_rule013_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule013`（水平条纹(等密极密)；源 **L 灰度**） |
| 38 | `x_mask_rule026_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule026`（放射星芒；源 **L 灰度**） |
| 39 | `x_mask_rule047_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule047`（径向光晕(中心亮)；源 **L 灰度**） |
| 40 | `x_mask_rule061_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule061`（四象限擦除；源 **L 灰度**） |
| 41 | `x_mask_rule065_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule065`（扇形擦除；源 **L 灰度**） |
| 42 | `x_mask_rule067_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule067`（棋盘(3D网格)；源 **L 灰度**） |
| 43 | `x_mask_rule071_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule071`（云状噪波dissolve；源 **L 灰度**） |
| 44 | `x_mask_rule076_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule076`（Voronoi晶格；源 **L 灰度**） |
| 45 | `x_mask_rule097_1x.png` | 1440×816 | 满屏 1:1（1440×816） | 同上 | 原版 PSV 转场遮罩 `rule097`（螺旋(涡旋)；源 **L 灰度**） |
| 46 | `nm_frm_a.png` | 333×54 | 锚点 左上（layout `dlg.namebox`） | `loadImages("ui/nm_frm_b.png")` + `setSizeToImageSize()` | 原版角色名框 `nm_frm_*`（a/b/g 三皮肤，本作取 b） |
| 47 | `nm_frm_b.png` | 333×54 | 锚点 左上（layout `dlg.namebox`） | `loadImages("ui/nm_frm_b.png")` + `setSizeToImageSize()` | 原版角色名框 `nm_frm_*`（a/b/g 三皮肤，本作取 b） |
| 48 | `nm_frm_g.png` | 333×54 | 锚点 左上（layout `dlg.namebox`） | `loadImages("ui/nm_frm_b.png")` + `setSizeToImageSize()` | 原版角色名框 `nm_frm_*`（a/b/g 三皮肤，本作取 b） |
| 49 | `if_bbar.png` | 2×8 | 九宫格**原料**（不直接整张贴） | 作为 `panel_frame.png` 的拼合原料；散件保留供 M2 手工三切片备用 | 原版通用窗框九宫格八件 `if_*` |
| 50 | `if_lb.png` | 20×8 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 51 | `if_lbar.png` | 20×2 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 52 | `if_lt.png` | 20×8 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 53 | `if_rb.png` | 20×8 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 54 | `if_rbar.png` | 20×2 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 55 | `if_rt.png` | 20×8 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 56 | `if_tbar.png` | 2×8 | 九宫格**原料** | 同上 | 原版通用窗框九宫格八件 `if_*` |
| 57 | `paper_0.png` | 288×12 | 按粒子系统随机摆放 | `loadImages` + `setSizeToImageSize()`（1:1）；anim 循环 | 原版粒子 `paper_0..7`（纸屑）、`snow_0..4`（雪） |
| 58 | `paper_1.png` | 288×12 | 按粒子系统随机摆放 | 同上 | 同上 |
| 59 | `paper_2.png` | 288×12 | 按粒子系统随机摆放 | 同上 | 同上 |
| 60 | `paper_3.png` | 288×12 | 按粒子系统随机摆放 | 同上 | 同上 |
| 61 | `paper_4.png` | 576×24 | 按粒子系统随机摆放 | 同上 | 同上 |
| 62 | `paper_5.png` | 576×24 | 按粒子系统随机摆放 | 同上 | 同上 |
| 63 | `paper_6.png` | 576×24 | 按粒子系统随机摆放 | 同上 | 同上 |
| 64 | `paper_7.png` | 576×24 | 按粒子系统随机摆放 | 同上 | 同上 |
| 65 | `snow_0.png` | 9×9 | 按粒子系统随机摆放 | 同上 | 同上 |
| 66 | `snow_1.png` | 12×12 | 按粒子系统随机摆放 | 同上 | 同上 |
| 67 | `snow_2.png` | 15×15 | 按粒子系统随机摆放 | 同上 | 同上 |
| 68 | `snow_3.png` | 18×18 | 按粒子系统随机摆放 | 同上 | 同上 |
| 69 | `snow_4.png` | 21×21 | 按粒子系统随机摆放 | 同上 | 同上 |
| 70 | `cf_bar.png` | 39×54 | 滑块按比例摆放 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版滚动条滑块 `cf_bar`（纵向）/ `cf_vbar`（横向） |
| 71 | `cf_vbar.png` | 84×9 | 滑块按比例摆放 | 同上 | 同上 |
| 72 | `sel00a.png` | 1085×11 | **本作不使用**（宽 1085 > 面板，且不缩放） | 不加载；仅作原版素材溯源保留 | 原版选择高亮条 `sel00a/b/g`、`sel01b`、`sel02b` |
| 73 | `sel00b.png` | 1085×11 | **本作不使用** | 不加载；仅作溯源保留 | 同上 |
| 74 | `sel00g.png` | 1085×11 | **本作不使用** | 不加载；仅作溯源保留 | 同上 |
| 75 | `sel01b.png` | 1085×45 | **本作不使用** | 不加载；仅作溯源保留 | 同上 |
| 76 | `sel02b.png` | 1085×12 | **本作不使用** | 不加载；仅作溯源保留 | 同上 |
| 77 | `sm_base.png` | 273×522 | 锚点 左上（M5 定） | `loadImages` + `setSizeToImageSize()`（1:1） | 原版系统菜单底板 `sm_base` / `sm_base2`（空白件） |
| 78 | `sm_base2.png` | 273×398 | 锚点 左上（M5 定） | 同上 | 同上 |
| 79 | `ms_cursr.png` | 207×17 | 锚点 左上（layout `dlg.cursor`） | `loadImages("ui/ms_cursr.png")` + `setSizeToImageSize()`；`anim.mode=blink` 周期 700ms | 原版文本推进光标 `ms_cursr` |
| 80 | `ec_bg01.png` | 582×855 | 格内 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版角色头像缩略图 `th_asu`/`th_ai`/`th_bar`、场景/CG 缩略图 `ui_bg01`/`gc_asu01`/`ec_bg01` |
| 81 | `gc_asu01.png` | 420×158 | 格内 1:1 | 同上 | 同上 |
| 82 | `th_ai.png` | 297×149 | 格内 1:1 | 同上 | 同上 |
| 83 | `th_asu.png` | 297×149 | 格内 1:1 | 同上 | 同上 |
| 84 | `th_bar.png` | 102×8 | 格内 1:1 | 同上 | 同上 |
| 85 | `ui_bg01.png` | 420×158 | 格内 1:1 | 同上 | 同上 |
| 86 | `tl1_bg.png` | 1200×900 | 锚点 左上（layout `title.bg_art`，仅 tl1_bg1） | `loadImages` + `setSizeToImageSize()`（1:1 不拉伸） | 原版标题背景 `tl1_bg1`/`tl1_bg2`（幻想侧风景）、`tl1_bg`/`tl2_bg1`（含女主立绘） |
| 87 | `tl1_bg1.png` | 1800×675 | 锚点 左上（layout `title.bg_art`，仅 tl1_bg1） | 同上 | 同上 |
| 88 | `tl1_bg2.png` | 1800×675 | 锚点 左上（layout `title.bg_art`，仅 tl1_bg1） | 同上 | 同上 |
| 89 | `tl2_bg1.png` | 1200×900 | 锚点 左上（layout `title.bg_art`，仅 tl1_bg1） | 同上 | 同上 |
| 90 | `ga_frame.png` | 249×189 | 1:1 | `loadImages` + `setSizeToImageSize()`（1:1） | 原版相册框 `ga_frame`；`sv_f1..5` 为**烘焙 Latin 键帽「F1」–「F5」**（保留但不得当无字件用） |
| 91 | `sv_f1.png` | 26×17 | 1:1 | 同上 | 同上 |
| 92 | `sv_f2.png` | 27×17 | 1:1 | 同上 | 同上 |
| 93 | `sv_f3.png` | 27×17 | 1:1 | 同上 | 同上 |
| 94 | `sv_f4.png` | 27×17 | 1:1 | 同上 | 同上 |
| 95 | `sv_f5.png` | 27×17 | 1:1 | 同上 | 同上 |
| 96 | `sr_01.png` | 612×462 | 卡内 1:1（不拉伸，H6） | `loadImages` + `setSizeToImageSize()`（1:1） | 片尾角色卡 `sr_01..24`（目视确认无烘焙文字；M11 已纳入资产集） |
| 97 | `sr_02.png` | 612×462 | 同上 | 同上 | 同上 |
| 98 | `sr_03.png` | 612×462 | 同上 | 同上 | 同上 |
| 99 | `sr_04.png` | 612×462 | 同上 | 同上 | 同上 |
| 100 | `sr_05.png` | 612×462 | 同上 | 同上 | 同上 |
| 101 | `sr_06.png` | 612×462 | 同上 | 同上 | 同上 |
| 102 | `sr_07.png` | 612×462 | 同上 | 同上 | 同上 |
| 103 | `sr_08.png` | 612×462 | 同上 | 同上 | 同上 |
| 104 | `sr_09.png` | 612×462 | 同上 | 同上 | 同上 |
| 105 | `sr_10.png` | 612×462 | 同上 | 同上 | 同上 |
| 106 | `sr_11.png` | 612×462 | 同上 | 同上 | 同上 |
| 107 | `sr_12.png` | 612×462 | 同上 | 同上 | 同上 |
| 108 | `sr_13.png` | 612×462 | 同上 | 同上 | 同上 |
| 109 | `sr_14.png` | 612×462 | 同上 | 同上 | 同上 |
| 110 | `sr_15.png` | 612×462 | 同上 | 同上 | 同上 |
| 111 | `sr_16.png` | 612×462 | 同上 | 同上 | 同上 |
| 112 | `sr_17.png` | 612×462 | 同上 | 同上 | 同上 |
| 113 | `sr_18.png` | 612×462 | 同上 | 同上 | 同上 |
| 114 | `sr_19.png` | 612×462 | 同上 | 同上 | 同上 |
| 115 | `sr_20.png` | 612×462 | 同上 | 同上 | 同上 |
| 116 | `sr_21.png` | 612×462 | 同上 | 同上 | 同上 |
| 117 | `sr_22.png` | 612×462 | 同上 | 同上 | 同上 |
| 118 | `sr_23.png` | 612×462 | 同上 | 同上 | 同上 |
| 119 | `sr_24.png` | 612×462 | 同上 | 同上 | 同上 |
| 120 | `x_title_logo.png` | 723×252 | 锚点 左上（layout `title.logo`） | `loadImages("ui/x_title_logo.png")` + `setSizeToImageSize()`（1:1） | UI 组自制（M9）：中文标题 logo（108px 重绘 + `tl1_logo.png` 2× 版羽毛带 0.75× 下采样） |
| 121 | `x_gen_icon_01_qsave.png` | **351×234（M22 重做）** | 锚点 左上；**UI 内按 96×64 框等比 contain 摆放**（`x_gen_icon_01..09` 同） | `loadImages("ui/x_gen_icon_01_qsave.png")` + `setSize(w,h)`（contain） | AI 生图派生：原版功能键文字（`sm_save`/`sv_*` 族）与 `skp1_icon` 的烘焙状态文字 → 中文界面须引擎绘字，故图标由 AI 生图补 |
| 122 | `x_gen_icon_02_qload.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版「クイックロード」文字位（原版无独立图标） |
| 123 | `x_gen_icon_03_skip.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版 `sm_skip` / `skp1_icon` 的 SKIP 状态 |
| 124 | `x_gen_icon_04_prev.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版回想/上一页（`01_prev`）文字位 |
| 125 | `x_gen_icon_05_save.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版 `sm_save`（セーブ） |
| 126 | `x_gen_icon_06_load.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版 `sm_load`（ロード） |
| 127 | `x_gen_icon_07_config.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版 `sm_cfg`（環境設定） |
| 128 | `x_gen_icon_08_close.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版 `th_close` / `sm_win`（ウィンドウ消去） |
| 129 | `x_gen_icon_09_repeat.png` | **351×234（M22 重做）** | 同上 | 同上 | AI 生图派生：原版 `sm_auto`（オート，循环箭头） |
| 130 | `x_gen_dialog.png` | 1680×946 | 锚点 左上；**1:1**（宽度 = 1920 画布的 87.5%）；名字框/正文区矩形见 `_工作\M11_生成几何.json` 的 `dialog` | `loadImages("ui/x_gen_dialog.png")` + `setSizeToImageSize()`（1:1 不拉伸） | AI 生图派生：原版对话窗底 `meswin` + 角色名框 `nm_frm_*` —— **一张整图含名字框**，取代两者 |
| 131 | `x_gen_flownode_1_normal.png` | **562×108（M22 重做）** | 锚点 左上；**1:1**（宽度 = 画布的 60%） | `loadImages` + `setSizeToImageSize()`（1:1） | AI 生图派生：原版**无**（`flowchart` 屏是新屏）；剧情流程图「普通章节」节点条 |
| 132 | `x_gen_flownode_2_badend.png` | **584×112（M22 重做）** | 同上 | 同上 | AI 生图派生：「Bad End」节点条（羽毛 + 血滴） |
| 133 | `x_gen_flownode_3_important.png` | **577×112（M22 重做）** | 同上 | 同上 | AI 生图派生：「重要章节」节点条（雪花 + 高亮蓝） |
| 134 | `x_gen_flownode_4_goodend.png` | **572×110（M22 重做）** | 同上 | 同上 | AI 生图派生：「Good End」节点条（粉色 + 心） |
| 135 | `x_gen_fragpage.png` | 1920×1080 | **满幅 (0,0) 1:1**；标题/面板外框/**40 个格子（5 列 × 8 行，行优先）**矩形见 `_工作\M11_生成几何.json` 的 `fragpage` | `loadImages("ui/x_gen_fragpage.png")` + `setSizeToImageSize()`（满幅 1:1） | AI 生图派生：原版**无**（`fragment` 屏是新屏）；版式参照 PSV 场景选择整页 `ss_bg1…5_full`（含烘焙文字，**不可用**）。★ **ISSUE-20260928-06（2026-09-28，用户裁定）**：`fragment`（番外·Fragment 选择）屏**已整体删除** ⇒ 本件不再被任何屏引用；**素材 `krkr/assets/ui/x_gen_fragpage.png` 保留原位不删**（用户「只删屏、保留动作/素材」）。条目保留作溯源。 |
| 136 | `x_gen_gallerypage.png` | 1920×1080 | **满幅 (0,0) 1:1**；左侧 4 框 / 预览大框 / 深色章节名条 / 4 条简介条矩形见 `_工作\M11_生成几何.json` 的 `gallerypage` | `loadImages("ui/x_gen_gallerypage.png")` + `setSizeToImageSize()`（满幅 1:1） | AI 生图派生：原版 PSV 画廊整页 `gm_bg1`（含烘焙文字，**不可用**）+ `gl_chr1…12` 角色筛选标签 |
| 137 | `x_bg_system.png` | 1920×1080 | **满幅 (0,0) 1:1**（系统屏满幅背景，**不留黑边**） | `loadImages("ui/x_bg_system.png")` + `setSizeToImageSize()`（满幅 1:1）；压暗层 `veil` 保留 | AI 生图派生：原版系统屏整页底图 `sys_menu` / `gm_bg1` / `bg_config_01`（均含烘焙文字，**不可用**）；由 `资源组\美术统一_超分\CG背景\bg63.png` 中心裁 16:9 → 0.75× 下采样 |

**自证：本表数据行数 = 137 ｜ 目录内 PNG 件数 = 137 ｜ 二者相等 = 是。**（M17 收口后；原为 138/138）
**核对命令**（逐行尺寸与本表逐条比对，输出为空即全等）：

```bash
cd "E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
ls -1 krkr/assets/ui/*.png | wc -l        # 期望 137
python -c "import os,struct;d='krkr/assets/ui';[print(f,struct.unpack('>II',open(os.path.join(d,f),'rb').read(33)[16:24])) for f in sorted(os.listdir(d))]"
```

> ★ **M20 注（2026-09-20）**：上行自证**已过期，保留不改**。M20 新增 **15 件** AI 派生件
> （`x_gen_logo.png` 1 件 + `x_gen_menu_*` 14 件，见 **§一.3**），目录内 PNG 现为 **152 件**。
> 本表（§一.2）**一字未动**，仍作 M17 时点的历史口径；当前口径见 §一.3。
> ⚠ 本表 **#120 `x_title_logo.png`** 的「锚点 左上（layout `title.logo`）」**已失效**：M20 起标题屏
> 改用 `x_gen_logo.png`，该件**零引用**（文件仍留在 `krkr/assets/ui/`，未删除；其重建脚本
> `工具/make_title_assets.py` 未改，若复跑会重新生成它——是否删除/退役该脚本留给主代理裁决）。

### 一.3 M20 新增资产（AI 重导素材派生 · 真 alpha · 1920×1080 基线）

> ⚠ **M22 更正注（2026-09-20，用户根因指令）**：M22 起，**压缩素材**（= 多个素材放进一张图的
> 生图件）一律改为「**整图统一倍率缩放 → 按网格切分**」，**取消逐件归一化**（原做法导致相对大小
> 失真——实测 9 个图标被施加 0.762×–1.116× 的不同倍率、7 个菜单 0.650×–0.721×、4 条方框
> 0.970×–1.007×，故实机演示里「大小不一、乱七八糟」）。
> 本节的 **14 件菜单尺寸已按 M22 口径就地更新为 439×122**（k=0.70）；`x_gen_logo.png`（单元素，
> 不属压缩素材）**未改**。三族的新尺寸与依据见 **§一.4**。

> 生成器：`工具\prep_generated.py`（幂等可复跑，连跑两次 15 件 md5 全等）｜ 几何：`_工作\M20_生成几何.json`｜ 证据：`_工作\M20_证据\`
> 源素材：`生图入料\生成结果\游戏logo重置.png`（1697×927 **RGBA**）、`系统屏底图重置.png`（1254×1254 **RGBA**）—— 用户 2026-09-20 重新导出，**真 alpha**（实测 p90=253 / p99=254），源目录**全程只读**。
> 命名前缀 `x_gen_` = 「AI 生图派生」。五列口径同 §一。
> 用途：**标题屏**（`layout/screens/01_title.json`）——logo 取代 M9 自制的 `x_title_logo.png`；14 件菜单按钮取代原「list + 引擎绘字」文字菜单。

| # | 文件名 | 尺寸 | 九宫格或锚点参数 | 在 krkr 中的加载方式 | 对应原版 UI 元素 |
|---:|---|---|---|---|---|
| 1 | `x_gen_logo.png` | 900×317 | 锚点 左上 `(60,45)`（layout `title.logo`）；1:1 | `loadImages("ui/x_gen_logo.png")` + `setSizeToImageSize()`（1:1） | 原版标题 logo `tl1_logo`（含日文，不可用）→ **取代 M9 自制 `x_title_logo.png`**（中文标题重绘 + 羽毛带） |
| 2 | `x_gen_menu_1_start.png` | **439×122（M22 重做）** | 锚点 左上 `(1563,180)`（layout `title.menu_img_1`）；1:1 | `loadImages("ui/x_gen_menu_1_start.png")` + `setSizeToImageSize()`（1:1） | 原版标题菜单 `tl_01…tl_06`（日文，不可用）→ 新按钮图（烘焙中文「开始游戏」+ 英文 START） |
| 3 | `x_gen_menu_1_start_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；layout `title.menu_hit_1.state_assets.hover` | 同屏 `hit` 元素按 `state_assets` 两态切换（`ui_widget.tjs` `uiWidgetDrawHit`） | 原版菜单条高亮态（`sel00g` 族）→ 金色高亮按钮图 |
| 4 | `x_gen_menu_2_continue.png` | **439×122（M22 重做）** | 锚点 左上 `(1563,296)`（layout `title.menu_img_2`）；1:1 | 同 #2 | 同 #2；烘焙「继续游戏 / CONTINUE」 |
| 5 | `x_gen_menu_2_continue_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；`title.menu_hit_2.state_assets.hover` | 同 #3 | 同 #3（源图本行两态长宽比差 3.56%，为全表最大） |
| 6 | `x_gen_menu_3_load.png` | **439×122（M22 重做）** | 锚点 左上 `(1565,412)`（layout `title.menu_img_3`）；1:1 | 同 #2 | 同 #2；烘焙「读取存档 / LOAD」 |
| 7 | `x_gen_menu_3_load_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；`title.menu_hit_3.state_assets.hover` | 同 #3 | 同 #3 |
| 8 | `x_gen_menu_4_flowchart.png` | **439×122（M22 重做）** | 锚点 左上 `(1560,528)`（layout `title.menu_img_4`）；1:1 | 同 #2 | 同 #2；烘焙「流程图 / FLOWCHART」（文字最长 → 最宽 289） |
| 9 | `x_gen_menu_4_flowchart_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；`title.menu_hit_4.state_assets.hover` | 同 #3 | 同 #3 |
| 10 | `x_gen_menu_5_extra.png` | **439×122（M22 重做）** | 锚点 左上 `(1600,644)`（layout `title.menu_img_5`）；1:1 | 同 #2 | 同 #2；烘焙「鉴赏 / EXTRA」（文字最短 → 最窄 209） |
| 11 | `x_gen_menu_5_extra_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；`title.menu_hit_5.state_assets.hover` | 同 #3 | 同 #3 |
| 12 | `x_gen_menu_6_config.png` | **439×122（M22 重做）** | 锚点 左上 `(1563,760)`（layout `title.menu_img_6`）；1:1 | 同 #2 | 同 #2；烘焙「环境设定 / CONFIG」 |
| 13 | `x_gen_menu_6_config_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；`title.menu_hit_6.state_assets.hover` | 同 #3 | 同 #3 |
| 14 | `x_gen_menu_7_exit.png` | **439×122（M22 重做）** | 锚点 左上 `(1566,876)`（layout `title.menu_img_7`）；1:1 | 同 #2 | 同 #2；烘焙「退出游戏 / EXIT」 |
| 15 | `x_gen_menu_7_exit_on.png` | **439×122（M22 重做）** | 悬停态，与常态**同尺寸**；`title.menu_hit_7.state_assets.hover` | 同 #3 | 同 #3 |

**逐件变换方向**（详见 `_工作\M20_证据\prep_generated.log`）：
- `x_gen_logo` = alpha 包围盒(th=8) `(0,143,1671,732)` 裁紧 **1671×589** → 等比缩到宽 **900**（**下采样 0.5386×**）。⚠ 源图内容**贴到左边界 x=0**（原画导出时已被裁切，非本脚本所致，已如实登记）。
- 14 件菜单 = **M22 重做**：整图 ×**0.70** 一次缩放 → 2 列 × 7 行**统一网格**切分（列等分 439；行统一行高 122、原点 y=8），每件 439×122、**14 件同尺寸**。原做法（行/列投影分离 7×2 → 每格 alpha 包围盒裁紧 → 两态统一缩到高 104）**已废止**——它给 14 件施加了 0.650×–0.721× 的不同倍率。⚠ 源行的**真实间距不等**（第 5–6 行间隙仅 8 px），故**等分 2×7 会切到第 6/7 项内容**（实测坐实，证据 `_工作\M22_证据\menu_equalgrid.png`），行网格改用「统一行高 + 统一原点」并逐行校验内容全部落格。
- **语义顺序按源图自上而下**：1 开始游戏 START / 2 继续游戏 CONTINUE / 3 读取存档 LOAD / 4 流程图 FLOWCHART / 5 鉴赏 EXTRA / 6 环境设定 CONFIG / 7 退出游戏 EXIT。⚠ 与用户早前口述顺序（「开始游戏 / 读档 / 继续 / …」）**不同**：源图 **CONTINUE 在 LOAD 之前**，本表与 layout **以图为准**。

**自证：本表数据行数 = 15 ｜ §一.2 行数 137 + 本表 15 = 152 ｜ 目录内 PNG 件数 = 152 ｜ 三者相符 = 是。**

```bash
ls -1 krkr/assets/ui/*.png | wc -l        # 期望 152
```

### 一.4 M22 重做 / 新增资产（**压缩素材统一缩放** · 1920×1080 基线）

> 生成器：`工具\prep_generated.py`（幂等可复跑，**连跑两次 35 件产物 md5 全等**）｜
> 几何：`_工作\M22_生成几何.json`（供 M23 直接消费）｜ 证据：`_工作\M22_证据\`（`sheet_icons.png` /
> `sheet_menu.png` / `sheet_flownodes.png` / `overlay_dialog2.png` / `menu_equalgrid.png` / `menu_actualbands.png`）
> 源素材：`生图入料\生成结果\功能图标.png`（1536×1024 RGBA）、`系统屏底图重置.png`（1254×1254 RGBA）、
> `流程图的章节方框.png`（1672×941 RGBA）、`暂定对话框.png`（1672×941 RGBA）—— **全程只读**
> （改前改后 md5 与 mtime 逐件核验一致）。
> **规则**：① 每件定一个**件内共用**的 k → ② 用 `Image.LANCZOS` 把**整张源图**按 k 缩放**一次** →
> ③ 再按网格切分（切分线同样 ×k）。**禁止对切出来的元素再单独缩放**。

| # | 文件名 | 尺寸 | 九宫格或锚点参数 | 在 krkr 中的加载方式 | 备注 |
|---:|---|---|---|---|---|
| 1–9 | `x_gen_icon_01_qsave.png` … `x_gen_icon_09_repeat.png` | **351×234**（9 件同尺寸） | 锚点 左上；1:1。网格 = 3×3 等分（缩放后 1053×702，格 351×234）；`k = 0.685547`（3×3 网格整体高 702 px = 画布 1080 的 **65.0%**，取要求 60–70% 的区间中点）；网格原点 `(0,0)` | `loadImages(...)` + `setSizeToImageSize()` | **M22 重做**（原 192×192…192×280，逐件归一化到宽 192）。每格**内容**在格内的位置见 `M22_生成几何.json` → `icons.items[].content_bbox_in_cell` |
| 10–23 | `x_gen_menu_1_start.png` … `x_gen_menu_7_exit_on.png` | **439×122**（14 件同尺寸） | 锚点 左上；1:1。网格 = 2 列 × 7 行统一网格（缩放后 878×878；列界 `[0,439,878]`，行界 `8 + 122i`，i=0..7）；`k = 0.70`；网格原点 `(0,8)` | `loadImages(...)` + `setSizeToImageSize()`；悬停态同尺寸不跳位 | **M22 重做**（原 209–289×104，逐件归一化到高 104）。**每格内容包围盒（相对该格）见 `M22_生成几何.json` → `menu.items[].{normal,hover}.content_bbox_in_cell`，供 M23 做「按内容右边缘对齐」** |
| 24–27 | `x_gen_flownode_1_normal.png` / `_2_badend.png` / `_3_important.png` / `_4_goodend.png` | **562×108 / 584×112 / 577×112 / 572×110**（**尺寸各异是对的**——源里本来就不同；**倍率相同**） | 锚点 左上；1:1。`k = 0.491228`（使最高那条 112 px，落在要求 110–130 px 内，与 M14 版式已算好的「行槽 112」一致）；源切点 y=240/468/696（行剖面局部极小） | `loadImages(...)` + `setSizeToImageSize()` | **M22 重做**（原 1152×217…234，逐件归一化到宽 1152）。源行区间见 `M22_生成几何.json` → `flownodes.items[].src_band` |
| 28 | `x_gen_dialog2.png` | **1628×319** | 锚点 左上；1:1。`k = 1.0`（源 alpha>64 包围盒 `(20,598,1648,917)` 裁切即 319 px 高，**天然落在用户要求的 290–320 内**，不做任何缩放）。**名字框内可写区** `[185, 22, 345, 56]`、**正文可写区** `[100, 80, 940, 210]`（坐标**相对裁切图左上角**，见 `M22_生成几何.json` → `dialog2`） | `loadImages("ui/x_gen_dialog2.png")` + `setSizeToImageSize()`（1:1） | **M22 新增**（源 `暂定对话框.png`）。正文区左避羽毛（x≤85）、右避雪花装饰（x≥1050）。**旧 `x_gen_dialog.png` 保留不删**，切换引用由 M23 决定 |

**旧 vs 新 倍率对照（核心验收项 · 同一 builder 内倍率极差 = 1.000×）**

| builder | 旧（逐件归一化）倍率范围 | 极差 | 新（统一 k） | 极差 |
|---|---|---|---|---|
| 9 图标 | 0.7619 – 1.1163 | **1.465×** | **0.685547** | 1.000× |
| 14 菜单 | 0.6500 – 0.7075 | **1.088×** | **0.700000** | 1.000× |
| 4 方框 | 0.9697 – 1.0070 | **1.038×** | **0.491228** | 1.000× |

**自证**：目录内 PNG 件数 152 + `x_gen_dialog2.png` = **153**（`verify_ui.py` [5] 实测 153 件 / 43.23 MB）。

```bash
ls -1 krkr/assets/ui/*.png | wc -l        # 期望 153
```

## 二、不可直接使用登记表（C 类 · 含日文 / 文字烘焙，**不得进入资产集**）

| 族名 | 件数 | 尺寸 | 烘焙内容举例 | 处置建议 |
|---|---:|---|---|---|
| `op_01…op_56` | 39 | 201–731×35–39 | 整句日文选项文本图（如「これは“たとえば”の話だけど」） | 选项一律**引擎绘字**；选项框用 panel_frame.png 九宫格 |
| `sm_save/load/cfg/skip/auto/win/log/ret/title/end/s_s_ret` | 10 | 612×26（sm_auto 1224×26） | 菜单条日文（セーブ / ロード / 環境設定 / スキップ / オート …） | 系统菜单条**引擎绘字**；条底用九宫格/纯色 rect |
| `tl_01…tl_06 / tl_01_altotp…` | 10 | 897×39 / 807×49 | 标题菜单日文 | 标题菜单**引擎绘字**（01_title.json 的 list 元素已如此实现） |
| `if_ok/ok2/yes/no/cancl` | 5 | 168–228×25 | 确认按钮日文（はい / いいえ / キャンセル） | 确认框按钮**引擎绘字** + 九宫格边框 |
| `th_close / cf_ret / sv_ret / ld_ret / ex_ret / ga_ret / gl_exit` | 7 | 92×17…417×28 | 返回 / 关闭 / 退出 等动作文字 | **引擎绘字** |
| `sv_data / ld_data / sv_chk / ld_chk` | 4 | 1116×83 / 918×33 | 存读档页签与勾选态文字 | 存读档页签**引擎绘字**（M5） |
| `sv_pg01…10 / ld_pg01…10` | 24 | 152×25（20 件）/ 224×25（4 件） | 页码 / 页签文字 | 页码**引擎绘字** |
| `sv_memo / ld_memo` | 2 | 132×17 | 「メモ」等标签文字 | **引擎绘字** |
| `cf_disp1/2 / cf_bgm / cf_se / cf_dfrm / cf_bold / cf_anti / cf_skip1/2 / cf_sskp1/2 等` | 37 | 256×16 / 336×16 / 376×23 … | 配置项标签日文（画面表示 / BGM / 効果音 / スキップ …） | 配置项标签**引擎绘字**（M5 配置屏）；本族中 cf_frame/cf_frm_a/cf_bar/cf_vbar 为空白件，已作 A 类取用 |
| `ec_0108…（日期条）` | 44 | 224×24 | 日期条日文文字 | **引擎绘字**（M4 章节屏） |
| `ec1_name / ec1_chap / ec*_wing` | 17 | 126–227×17–24 | 章名 / 章副题 / 「Wing of …」英文题 | **引擎绘字**（章名取自 spine.json，不得自造） |
| `ec1_bg / ec2_bg / ec3_bg / ec4_bg / ec6_bg` | 5 | 1013×658 | 烘焙章名（「羽田 鷹志 編」「千歳 鷺介 編」「成田 隼人 編」「奈落の底」+ 英文 “Chapter : …” / “Abyss”） | **M1 目视实测**：章名占卡面主区，不可作卡底；章标题卡须重制（取纹理区 + 引擎绘中文章名） |
| `ec5_1_bg / ec5_2_bg` | 2 | 1013×658 | 烘焙章名「伊丹 伽楼羅 編」/ “Chapter : Karura Itami” / “Wing of Garuda”（ec5_2 另有彩色大字 +「12月3日（日）」） | **M1 目视实测（本次新增）**：同为红羽章卡但含烘焙章名 → 不可用。⚠ 与 `00_UI组认知与接口契约.md` §3.1 的「`ec1_bg…ec6_bg` 1013×658」不符：**`ec5_bg` 实测为 800×600 且无字**（已作 A 类取用），1013×658 的是 `ec5_1_bg`/`ec5_2_bg` |
| `sc_50_1…54_1` | 5 | 280×105 | 卡面标题文字 | **引擎绘字**（画廊/场景卡） |
| `ex_10…ex_26` | 23 | 225×467 / 340×29 / 800×600 | 整页界面文字 | 不使用（R1 类整页图，须重制） |
| `title_bg` | 1 | 960×965 | PSV 标题整页文字 | 不使用（R1：竖幅超画布，重制为 1280×720 版式） |
| `bg_config_01/02` | 2 | 960×833 / 960×761 | 配置整页文字 | 不使用（R1：重制配置屏版式） |
| `ss_bg1…5_full / ss_bg*_base` | 10 | 800×600 / 960×1012 | 场景选择整页文字 | 不使用（R1：重制场景选择版式） |
| `sl_data` | 1 | 426×511 | 存读档整页文字 | 不使用（重制） |
| `gm_bg1 / mu_bg / mv_bg / sys_menu` | 4 | 960×659…960×1626 | 画廊/音乐/影片/系统菜单整页文字 | 不使用（R1：重制为 1280×720 版式） |
| `gl_chr1…12` | 12 | 414×29–32 | 角色名标签（角色名文字） | **引擎绘字**（画廊角色筛选） |
| `gl_bgm01…gl_bgm12` | 12 | 1900×37 | 曲目标题（英文，如 “Eternal Prelude”“Main Theme “HAWK””） | **M1 目视实测确认含烘焙文字**（任务书 C 类已列「gl_bgm*(ota 1900×37 版)」）。音乐条须改为**引擎绘字 + 纯色/九宫格条底**；宽度 1900 > 画布 1280，亦不满足 R3 的滚动前提 |
| `mc_bgm01…mc_bgm96（实存 58 件）` | 58 | 2036×37 | 曲目标题（日文，如「放課後の小娘たち」「世界が平和でありますように」） | **M1 目视实测确认含烘焙文字**。同上：引擎绘字 + 纯色条底 |
| `ev_*` | 9 | 768×456 / 768×684 / 768×798 | 事件画面整页文字 | 不使用（R4 类：超画布/竖幅） |
| `quick-save` | 1 | 276×600 | 「クイックセーブ」等文字 | **引擎绘字** |
| `sv_bg / ld_over` | 2 | 800×600 | 存读档整页文字 | 不使用（重制） |
| `dm00…dm11` | 12 | 320×120 | 「ロード中…」加载提示文字（H5） | **引擎绘字**；加载屏底可用纯色/九宫格（loading 屏属 M5） |
| `ui_ec_bg15a…` | 8 | 388×570 | 竖幅场景卡面标题文字 | **引擎绘字**（M5 画廊/场景卡） |
| `skp1_icon` | 1 | 256×256 | 烘焙文字雪碧图（AUTO / SKIP / STOP / Quick Saved + 播放控制图标） | **M1 目视实测确认**：非「图标」而是状态文字图集 → 须重制为引擎绘字 + 独立图标 |
| `noise` | 1 | - | 噪波贴图（非文字） | 未纳入 A 类（本次无引用需求；如需由 M2 按需取） |
| **`俺翼logo.png`**（AI 生图，M11 新登记） | 1 | 1697×927 **RGB** | **棋盘格假透明**：图像为 RGB（**无 alpha 通道**），棋盘格是**烘焙进像素**的，不是真透明 | **不可直接使用（M11 判定，主代理已试 5 种去背算法全部失败）**：亮度阈值 / 局部棋盘纹理 / 多偏移交替 / 逐行相位推定 / 跳变计数定极性 —— 原画的半透明白与棋盘白在像素层**已混合，信息已丢失**。证据 `_工作\M10_证据\prev_dark_logo.png`（棋盘残留 + 羽毛被掏空）。**不重试去背、不产出 `x_gen_logo*`、不用替代物冒充**。标题 logo 沿用 M9 的 `x_title_logo.png`（中文标题 108px 重绘 + `tl1_logo.png` 2× 版羽毛带 0.75× 下采样） |
| **`系统屏底图.png`**（AI 生图，M11 新登记） | 1 | 1254×1254 **RGB** | **棋盘格假透明**（同上：RGB 无 alpha，棋盘烘焙进像素） | **不可直接使用（M11 判定，同上 5 种去背算法全部失败）**。系统屏满幅背景改用 **`x_bg_system.png`**（`资源组\美术统一_超分\CG背景\bg63.png` 中心裁 16:9 → 0.75× 下采样到 1920×1080）；**不产出 `x_gen_menu*`、不用替代物冒充** |

> C 类合计 **约 300 件**（`资源组/美术统一/系统UI/` 共 1,569 件，占约 19%）。
> 一句话原则：**UI 骨架用空白贴图件，一切文字由引擎绘制** —— 既绕开日文烘焙，又满足「按 1280×720 重新排版」。

> ★ **M20 注（2026-09-20）—— 本表末两行状态已变更，行内容保留不改**：
> - **`俺翼logo.png`** → **已由用户重导为 `游戏logo重置.png`（1697×927 RGBA，真 alpha），现已可用**；
>   派生件 `x_gen_logo.png`（900×317）已接入标题屏（见 §一.3 #1）。
> - **`系统屏底图.png`** → **已由用户重导为 `系统屏底图重置.png`（1254×1254 RGBA，真 alpha），现已可用**；
>   派生 14 件 `x_gen_menu_*` 已接入标题屏（见 §一.3 #2–15）。
> - 旧的两张（RGB / 棋盘格假透明）**仍为不可用**，本脚本已**停止读取**；本条只登记「用户已重导可用」，
>   上表两行的历史判定（去背不可行、5 种算法失败）**依然成立、不作废**。
> 实测确认含烘焙的族已逐族登记（`ec1–ec4/ec6_bg`、`gl_bgm01–12`、`mc_bgm01–96`、`skp1_icon` 为 M1 本次目视实测新增，其中 `gl_bgm`/`mc_bgm`/`skp1_icon` 在 `00_UI组认知与接口契约.md` §3.1 曾被列为「可直接使用」，**实测与之不一致**，见报告 §五）。

### 二.1 预算递延族（**非烘焙**，仅因体积超预算未纳入本集）

| 族名 | 件数 | 尺寸 | 烘焙 | 处置 |
|---|---:|---|---|---|
| `sr_01…sr_24` | 24 | 408×308 | **无烘焙**（片尾角色 CG，已目视确认） | 体积 4.88 MB，纳入后总体积 14.57 MB > 12 MB 预算 → **递延**；`make_assets.py --with-ending-cards` 可复现完整档（须先取得主代理对预算的裁决，见报告 §六 裁决点 **R-2**） |

> 🔁 **M16 更正注（2026-09-20）**：`sr_01…sr_24` **已不再是递延族**——M11 已将其纳入资产集（现 612×462，24 件，见 §一.2 #96–119）；预算亦已由 12 MB 放宽至 **48 MB**（§〇）。上表保留不改，作历史记录。

### 二.2 重新导出要求（**给用户的 AI 素材重导清单**，M16 新增 2026-09-20）

以下两件 AI 生图**不可用**（棋盘格烘焙进像素，RGB 无 alpha，见上表末两行）。**去背不可行**（主代理已试 5 种算法全部失败），必须**重新导出**。

> ★ **M20 注（2026-09-20）—— 本清单已履行完毕**：用户已按下列要求重新导出，且**确为真 alpha（RGBA）**：
> - **① `俺翼logo.png` → `游戏logo重置.png`**（1697×927 **RGBA**，实测 p90=253 / p99=254）→ 派生 `x_gen_logo.png`。
> - **② `系统屏底图.png` → `系统屏底图重置.png`**（1254×1254 **RGBA**）→ 派生 14 件 `x_gen_menu_*`。
> - 差异登记：② 实际导出为 **7 行 × 2 列 = 14 个按钮**（本清单原文要求「6 行 × 2 列 = 12 个」）；7 行**恰好对应标题屏 7 个菜单项**，优于原要求，已按图接入。两件均未按「每个按钮单独出一张」的建议，而是整张网格图，由 `prep_generated.py` 用行/列投影自动切分（见 §一.3）。
> 下列两段原始要求**保留不改**，作溯源。

**① `俺翼logo.png`**
- **尺寸**：**1697×927 或更大**（当前实测 1697×927，RGB）。
- **格式**：**PNG-32（真 alpha）**。
- **背景**：**必须完全透明**——无棋盘格、无白底、无任何底色。
- **内容**：仅标题 logo 本体（羽毛 + 中/日文标题字形），四周留透明边。

**② `系统屏底图.png`**
- **当前实测**：1254×1254，RGB（**正方形**，与 16:9 系统屏不符；棋盘格假透明）。
- **需求**：**6 行 × 2 列共 12 个按钮**——**左列常态、右列高亮态**，**PNG-32 真 alpha**。
- **强烈建议**：**每个按钮单独出一张**（比一整张更易接入），命名 `M1_start.png` … `M6_config_on.png`（`_on` = 高亮态；常态不带后缀）。单张建议 ≥ 256×256、背景全透明。
- **背景**：若仍需整幅系统屏底图，另出一张 **1920×1080 或更大、真 alpha 的满幅背景**（当前已用 `x_bg_system.png` 顶替，但那是资源组超分素材，非本 AI 系）。

**自检方法（导出后请务必自查）**
- **看图法**：用 Windows 画图 / Photoshop 打开——看到**透明格子**（棋盘是软件的透明提示，会随背景变化）＝真透明；看到**灰白棋盘图案且随缩放不变**＝假透明（已烘焙），需重导。
- **命令行法**（输出必须为 `RGBA`，若为 `RGB` 则无 alpha，必重导）：
  ```bash
  python -c "from PIL import Image;print(Image.open('俺翼logo.png').mode)"
  python -c "from PIL import Image;print(Image.open('系统屏底图.png').mode)"
  ```
- **教训（务必遵守）**：导出必须是**真 alpha（PNG-32）**；**不要用「透明背景预览」截图**——那会把棋盘格烘焙进像素，导致原画半透明白与棋盘白在像素层混合、信息丢失，事后**不可恢复**。详见 `生图入料\README.md`。

## 三、自制 / 重制登记表（B 类，含生成依据）

> ★ **M17 注**：本表是 **M1（1280×720 基线）** 口径，**尺寸列保留不改作溯源**。
> 表内满屏遮罩族 18 行的**文件名已按 M17 收口更名为 `_full`**（原名后缀为 1280 基线时代遗留，实际尺寸 M11 起已是 1920×1080）；
> 实际尺寸与变换方向以 **§一.2** 与 `_工作\M11_证据\build_assets_1920_manifest.json` 为准。
> 标题屏满幅背景件（M9 自制）**已删除**（M13 起零引用），故本表不再列。

| 文件名 | 尺寸 | 生成方式 | 生成依据 |
|---|---|---|---|
| `panel_frame.png` | 27×11 | 由 `if_lt`+`if_rt`+`if_lb`+`if_rb`（13×5 四角）+ `if_tbar`/`if_bbar`（1×5 上下边）+ `if_lbar`/`if_rbar`（13×1 左右边）**拼合**（左中右 13/1/13，上中下 5/1/5，中心 1×1 透明） | layout `ui/panel_frame.png`（`10_dialog.json` `dlg.choices`、`01_title.json` `title.menu_frame` 的 `item_frame`）；九宫格边距 l=13 t=5 r=13 b=5 |
| `x_mask_rule000_1x.png` | 960×544 | 原版 `rule000.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：水平细条纹（百叶窗，条纹密度向左渐增） |
| `x_mask_rule013_1x.png` | 960×544 | 原版 `rule013.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：水平细条纹（极密） |
| `x_mask_rule008_1x.png` | 960×544 | 原版 `rule008.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：垂直细条纹（百叶窗） |
| `x_mask_rule009_1x.png` | 960×544 | 原版 `rule009.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：垂直条纹（中等） |
| `x_mask_rule001_1x.png` | 960×544 | 原版 `rule001.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：对角渐变（左上亮→右下暗） |
| `x_mask_rule003_1x.png` | 960×544 | 原版 `rule003.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：对角暗带（斜向渐变） |
| `x_mask_rule004_1x.png` | 960×544 | 原版 `rule004.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：径向暗角渐变（vignette） |
| `x_mask_rule047_1x.png` | 960×544 | 原版 `rule047.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：径向光晕（中心亮） |
| `x_mask_rule002_1x.png` | 960×544 | 原版 `rule002.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：同心圆环（靶心/涟漪，中心暗） |
| `x_mask_rule026_1x.png` | 960×544 | 原版 `rule026.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：放射状星芒（中心密集） |
| `x_mask_rule097_1x.png` | 960×544 | 原版 `rule097.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：螺旋（涡旋） |
| `x_mask_rule067_1x.png` | 960×544 | 原版 `rule067.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：方格棋盘（3D 网格渐变） |
| `x_mask_rule061_1x.png` | 960×544 | 原版 `rule061.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：四象限擦除（左上亮） |
| `x_mask_rule065_1x.png` | 960×544 | 原版 `rule065.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：对角扇形擦除（自左上角放射） |
| `x_mask_rule005_1x.png` | 960×544 | 原版 `rule005.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：噪波 dissolve（粗颗粒） |
| `x_mask_rule006_1x.png` | 960×544 | 原版 `rule006.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：噪波 dissolve（细颗粒） |
| `x_mask_rule071_1x.png` | 960×544 | 原版 `rule071.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：云状噪波 dissolve |
| `x_mask_rule076_1x.png` | 960×544 | 原版 `rule076.png`（960×544 **L 灰度**）→ **alpha = 灰度值，RGB 置白** → RGBA | `otv素材内容判读.tsv` 判读：晶格/多边形噪波（Voronoi） |
| `x_mask_rule000_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule013_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule008_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule009_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule001_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule003_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule004_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule047_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule002_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule026_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule097_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule067_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule061_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule065_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule005_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule006_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule071_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |
| `x_mask_rule076_full.png` | 1280×720 | 由 1x 版 **双线性（bilinear）重采样** 1.333× | **美术规范 §6.2 R2**：「在 1280×720 下重绘/重采样为画布尺寸，**属 UI 组新建素材，非缩放既有素材**」；§三 缩放算法：必须缩小时用双线性（nearest 会丢细线、产生摩尔纹） |

## 四、族级尺寸索引

| 族 | 件数 | 尺寸（众数） | 文件前缀 |
|---|---:|---|---|
| `dialog_window` | 1 | 1057×174（1 件） | `ui*` |
| `name_frame` | 3 | 222×36（3 件） | `ui_nm_frm*` |
| `text_cursor` | 1 | 138×11（1 件） | `ui_ms*` |
| `ninepatch_src` | 8 | 13×5（4 件）; 1×5（2 件）; 13×1（2 件） | `ui_if*` |
| `config_frame` | 2 | 322×42（2 件） | `ui_cf*` |
| `scrollbar` | 2 | 26×36（1 件）; 56×6（1 件） | `ui_cf*` |
| ~~`sysmenu_base`~~ | ~~2~~ | ~~182×348（1 件）; 182×265（1 件）~~ | ~~`ui_sm*`~~（**★ M45：`sysmenu` 屏已废除；该族**从未接入资产集**，`krkr/assets/ui/` 内无 `ui_sm*` 件；`工具\make_assets.py` 的取件条目已就地停用**） |
| `choice_window` | 1 | 650×193（1 件） | `ui*` |
| `dlg_blank` | 3 | 522×270（3 件） | `ui_dlg_bg*` |
| `title_bg` | 4 | 1200×450（2 件）; 800×600（2 件） | `ui_tl1*` |
| `thumbnail` | 6 | 198×99（2 件）; 280×105（2 件）; 68×5（1 件） | `ui_th*` |
| ~~`chapter_card`~~ | ~~1~~ | ~~800×600（1 件）~~ | ~~`ui_ec5*`~~（**★ M43：`chapter` 屏已删除；该族未接入资产集，`krkr/assets/ui/` 内无此件**） |
| `widget` | 6 | 18×11（4 件）; 166×126（1 件）; 17×11（1 件） | `ui_ga*` |
| `particle` | 13 | 192×8（4 件）; 384×16（4 件）; 6×6（1 件） | `ui_paper*` |
| `select_bar_unused` | 5 | 723×7（3 件）; 723×30（1 件）; 723×8（1 件） | `ui*` |
| `ninepatch_built` | 1 | 27×11（1 件） | `ui_panel*` |
| `mask_1x` | 18 | 960×544（18 件） | `ui_x_mask_*_1x` |
| `mask_1280` | 18 | 1280×720（18 件） | `ui_x_mask_*_1280` |

> 🔁 **M16 重算（2026-09-20，1920 基线，全部磁盘实测；上表为 M1 的 1280 口径，保留不改作溯源）**

| 族 | 件数 | 尺寸（众数，磁盘实测） | 文件前缀 |
|---|---:|---|---|
| `dialog_window` | 1 | 1586×261（1 件） | `meswin*` |
| `name_frame` | 3 | 333×54（3 件） | `nm_frm*` |
| `text_cursor` | 1 | 207×17（1 件） | `ms_cursr*` |
| `ninepatch_src` | 8 | 20×8（4 件）; 2×8（2 件）; 20×2（2 件） | `if_*` |
| `ninepatch_built` | 1 | 41×17（1 件） | `panel_frame*` |
| `config_frame` | 2 | 483×63（2 件） | `cf_frame`/`cf_frm_a` |
| `scrollbar` | 2 | 39×54（1 件）; 84×9（1 件） | `cf_bar`/`cf_vbar` |
| ~~`sysmenu_base`~~ | ~~2~~ | ~~273×522（1 件）; 273×398（1 件）~~ | ~~`sm_base*`~~（**★ M45：`sysmenu` 屏已废除；该族**从未接入资产集**，`krkr/assets/ui/` 内无 `sm_base*` 件；`工具\make_assets.py` 的取件条目已就地停用**） |
| `choice_window` | 1 | 975×290（1 件） | `selwin*` |
| `dlg_blank` | 3 | 783×405（3 件） | `dlg_bg_*` |
| `title_bg` | 4 | 1800×675（2 件）; 1200×900（2 件） | `tl1_*`/`tl2_*` |
| `thumbnail` | 6 | 420×158（2 件）; 297×149（2 件）; 582×855（1 件）; 102×8（1 件） | `th_*`/`ui_bg01`/`gc_asu01`/`ec_bg01` |
| ~~`chapter_card`~~ | ~~1~~ | ~~1200×900（1 件）~~ | ~~`ec5_bg*`~~（**★ M43：`chapter` 屏已删除；该族未接入资产集，`krkr/assets/ui/` 内无此件**） |
| `widget` | 6 | 27×17（4 件）; 26×17（1 件）; 249×189（1 件） | `sv_f*`/`ga_frame*` |
| `particle_paper` | 8 | 288×12（4 件）; 576×24（4 件） | `paper_*` |
| `particle_snow` | 5 | 9×9 / 12×12 / 15×15 / 18×18 / 21×21（各 1 件） | `snow_*` |
| `select_bar_unused` | 5 | 1085×11（3 件）; 1085×45（1 件）; 1085×12（1 件） | `sel0*` |
| `ending_card` | 24 | 612×462（24 件） | `sr_*` |
| `title_new` | 1 | 723×252（1 件） | `x_title_logo*`（M17：标题满幅背景件已删） |
| `mask_1x` | 18 | 1440×816（18 件） | `x_mask_*_1x` |
| `mask_1920`（原 `mask_1280`） | 18 | **1920×1080（18 件）** | `x_mask_*_full` |
| `gen_icon` | 9 | 192×宽不定（192×192 … 192×280） | `x_gen_icon_*` |
| `gen_flownode` | 4 | 1152×217…234（各 1 件） | `x_gen_flownode_*` |
| `gen_page` | 3 | 1920×1080（2 件）; 1680×946（1 件） | `x_gen_fragpage`/`x_gen_gallerypage`/`x_gen_dialog` |
| `bg_system` | 1 | 1920×1080（1 件） | `x_bg_system*` |

> 自证：上表件数合计 = 1+3+1+8+1+2+2+2+1+3+4+6+1+6+8+5+5+24+1+18+18+9+4+3+1 = **137**，与目录内 PNG 数相等（M17 收口后；原为 138）。

> ★ **M20 注（2026-09-20）**：上表口径由 137 更新为 **152 件**（+15），另新增两族：
> `gen_logo` 1 件（`x_gen_logo.png` 900×317）｜ `gen_menu` 14 件（`x_gen_menu_{1..7}_*` 与 `_on`，高 104 / 宽 209–289）。
> 其中 `title_new`（`x_title_logo*`）**已零引用**（标题屏改用 `x_gen_logo`），文件保留未删。
> 上表与自证行**保留不改**，作 M17 时点历史口径；当前口径见 **§一.3 / §一.4**。

> ★ **M22 注（2026-09-20）**：口径更新为 **153 件**（+`x_gen_dialog2.png`）。上表四族尺寸已变，**新值如下**（历史值见上表，作 M17 时点口径）：
> `gen_icon` 9 件 → **351×234（9 件同尺寸）**｜ `gen_flownode` 4 件 → **562×108 / 584×112 / 577×112 / 572×110**（倍率相同、尺寸各异）｜
> `gen_menu` 14 件 → **439×122（14 件同尺寸）**｜ 新增 `gen_dialog2` 1 件（`x_gen_dialog2.png` 1628×319）。
> 当前口径见 **§一.4**。

