# `config` 屏（`25_config.json`）标签定稿 · 死行删除与用词定稿

- Issue：`ISSUE-20260930-06` ｜ 分支：`issue/ISSUE-20260930-06-greta-ui-handover` ｜ 角色：editor（config 屏两处收尾）
- 依据：本目录 `接口冻结.md` §三（config 全部事实与判读证据表）、`立案.md`
- 改动落点：`布局/screens/25_config.json`（屏数据）、`krkr/game/ui_settings.tjs`（设置仓，仅 `vol_voice.label`）
- 证据目视：`PSV系统UI参考/超分2x/otv_bg_config_01.png`、`otv_bg_config_02.png`（原版两页真身）、本目录 `证据/cfmovie_row_check.png`

> **证据图缺件（如实登记）**：冻结书 §六与派单点名的 `证据/cf_labels_A.png`、`cf_labels_B.png`、`bg_config_01_2x.png`、`bg_config_02_2x.png` **在本 worktree 中不存在**（`find` 全库 0 命中；`证据/` 目录只有 `cfmovie_row_check.png`）。因此：
> - **原版两页行名**已用仍存在的真身 `PSV系统UI参考/超分2x/otv_bg_config_01/02.png` **目视逐行复核**（见 §1 表「原件日文」列的「★目视」标记），与冻结书 §3.3 的 14 行清单**逐行一致**；
> - 逐件 `cf_*` 读数（如 `cf_voice`=音声、`cf_skip1/2`=既読のみ/全て、`cf_aon/aoff`=全てON/全てOFF）**无法独立复核**，本文件一律标注为「引自冻结书 §3.3」（`cf_*` 素材与接触印相均不在本 worktree：全库 `find -iname 'cf_*.png'` 0 命中）。**此点须由主代理确认判读证据是否需要补落盘**。

---

## §1 定稿表（现行屏内 19 个设置行 ＋ 6 个「静音」toggle ＋ 页签 / 区段标题）

「屏内行标签（现行）」＝ `sample` 字段实测（`25_config.json`）；「原件日文」＝ 目视原文（★目视＝本次亲读真身图，余为引自冻结书 §3.3）。

### 1.1 系统页 · 枚举行 12（删 `cfmovie` 后；原 13）

| 设置键 | 屏内行标签（现行） | 原版对应件 | 原件日文（目视原文） | 是否改 | 依据 |
| --- | --- | --- | --- | --- | --- |
| `display` | 画面模式 | `cf_disp1` / `cf_disp2` | **ウィンドウ / フル画面**（选项值，非行标签） | 否 | 冻结书 §3.3；原版两页无该行 |
| `facewindow` | 立绘窗口 | — | — | 否 | 本屏自定（冻结书 §3.4②） |
| `drama` | 演出效果 | — | — | 否 | 本屏自定 |
| `effect` | 特效 | — | — | 否 | 本屏自定 |
| `voicecut` | 语音截断 | （原版 `音声スキップ` 语义相关，非同一行） | 音声スキップ（する / しない）★目视 | 否 | 冻结书 §3.4① 把 `音声スキップ` 列为「原版有本屏无」；见 §2 备注 |
| `curhide` | 隐藏光标 | — | — | 否 | 本屏自定 |
| `savedialog` | 存档时的确认信息 | — | — | 否 | 本屏自定（原版 `自動クイックセーブ` 语义不同） |
| `loaddialog` | 读档时的确认信息 | — | — | 否 | 本屏自定 |
| `text_speed` | 文字显示速度 | （原版 `メッセージ速度` 行） | **メッセージ速度**（遅い / 普通 / 早い / 一括）★目视 | 否 | 目视 `otv_bg_config_01`；本屏实现为滑条（四档→0–100） |
| `auto_speed` | 自动播放速度 | — | — | 否 | 本屏自定（原版无「自动播放速度」行） |
| `allskip` | 全部跳过 | （原版 `スキップモード` 语义相关） | スキップモード（既読のみ / 全て）★目视 | 否 | 冻结书 §3.4① 把 `スキップモード` 列为「原版有本屏无」；见 §2 备注 |
| `textcolchg` | 文字变色 | （冻结书 §3.3：`cf_bold` 项「原版项本屏未采用」） | 太字（`cf_bold`，引自冻结书） | 否 | 本屏自定 |
| ~~`cfmovie`~~ | ~~播放影片~~ | — | — | **本批删除** | 冻结书 §3.1/§3.2、用户裁定 #11；见 §4 |

### 1.2 声音页 · 音量子行 6（滑条行名）

| 设置键 | 屏内行标签（现行） | 原版对应件 | 原件日文（目视原文） | 是否改 | 依据 |
| --- | --- | --- | --- | --- | --- |
| `vol_master` | 主音量 | — | — | 否 | 本屏自定（原版无「主音量」总行） |
| `vol_bgm` | 背景音乐 | `otv_bg_config_02` 行 | **BGM ボリューム** ★目视 | 否 | 目视 |
| `vol_se` | 音效 | `otv_bg_config_02` 行 | **SE ボリューム** ★目视 | 否 | 目视 |
| `vol_sysse` | 系统音效 | `otv_bg_config_02` 行 | **システムボリューム** ★目视 | 否 | 目视 |
| `vol_voice` | **语音音量**（改前「主音量（语音）」） | `otv_bg_config_02` 行 | **Voice ボリューム** ★目视 | **是（本批·唯一）** | 冻结书 §3.2；改名理由：与 `vol_master`「主音量」撞名、语义不准。原版对应 `Voice ボリューム` |
| `vol_char` | 角色音量 | （原版 `キャラクター音声` 语义相关，非同一行） | キャラクター音声（全て ON / 全て OFF）★目视 | 否 | 冻结书 §3.4① 把「角色语音 全体 ON・OFF」列为「原版有本屏无」；见 §2 备注 |

### 1.3 滑条 9（无独立文案；行名见 1.1／1.2，此处登记技术参数）

| 滑条元素 id | 设置键 | min | max | step | value | 屏 | 是否改 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `cfg.sl_winopac` | `dlg_winopac` | 0 | 100 | 5 | 90 | sys | 否 |
| `cfg.sl_textspeed` | `text_speed` | 0 | 100 | 5 | 60 | sys | 否 |
| `cfg.sl_autospeed` | `auto_speed` | 0 | 100 | 5 | 50 | sys | 否 |
| `cfg.sl_master` | `vol_master` | 0 | 100 | 5 | 80 | snd | 否 |
| `cfg.sl_bgm` | `vol_bgm` | 0 | 100 | 5 | 80 | snd | 否 |
| `cfg.sl_se` | `vol_se` | 0 | 100 | 5 | 80 | snd | 否 |
| `cfg.sl_sysse` | `vol_sysse` | 0 | 100 | 5 | 80 | snd | 否 |
| `cfg.sl_voice` | `vol_voice` | 0 | 100 | 5 | 80 | snd | 否（仅行名改「语音音量」） |
| `cfg.sl_char` | `vol_char` | 0 | 100 | 5 | 80 | snd | 否 |

> 行名对应：`dlg_winopac`→`cfg.row_winopac_lb`「文本窗口的不透明度」（目视原版 `ウィンドウの不透明度`★目视）；`text_speed`/`auto_speed`→`cfg.row_textspeed_lb`/`cfg.row_autospeed_lb`；6 个音量行名→`cfg.snd_vol_*_lb`。

### 1.4 声音页 · 「静音」toggle 6

| 设置键 | 屏内行标签（现行） | 原版对应件 | 原件日文 | 是否改 | 依据 |
| --- | --- | --- | --- | --- | --- |
| `mute_vol_master` / `_bgm` / `_se` / `_sysse` / `_voice` / `_char` | **静音**（6 处，元素 `cfg.snd_vol_*_mute_lb`） | `cf_vchk`（复选框三态） | （控件件，非文案） | 否 | 冻结书 §3.3「`cf_vchk`＝控件件，非文案」；本屏为 M47 自定项 |

### 1.5 页签 / 区段标题 / 功能键

| 元素 id | 屏内标签（现行） | 原版对应件 | 原件日文（目视原文） | 是否改 | 依据 |
| --- | --- | --- | --- | --- | --- |
| `cfg.tab1_tx` | 系统 | `otv_bg_config_01` 页眉 | **基本設定** ★目视 | 否 | 目视；本屏页签「系统」对原版页1 |
| `cfg.tab2_tx` | 声音 | `otv_bg_config_02` 页眉 | **サウンド設定** ★目视 | 否 | 目视；本屏页签「声音」对原版页2 |
| `cfg.sec_picture` | 画面设定 | — | — | 否 | 本屏自定分区标题（原版每页仅 1 个区段标题） |
| `cfg.sec_text` | 文本设定 | — | — | 否 | 本屏自定分区 |
| `cfg.sec_preview` | 预览 | — | — | 否 | 本屏自定（用户要求复刻预览区） |
| `cfg.sec_volume` | 音量设定 | — | — | 否 | 本屏自定分区 |
| `cfg.sec_voice` | 语音设定 | — | — | 否 | 本屏自定分区 |
| `cfg.sec_charvoice` | 角色语音设定 | — | — | 否 | 本屏自定分区 |
| `cfg.reset_tx` | 初始化 | `cf_init` | **初期設定に戻す**（引自冻结书 §3.3） | 否 | 冻结书 §3.3 |
| `cfg.btn_game_tx` | 返回游戏 | 页脚 `戻る` | **戻る** ★目视（页脚 Ⓐデフォルト設定 Ⓑ選択 Ⓒ戻る） | 否 | 目视；本屏扩为三键 |
| `cfg.btn_title_tx` | 返回标题画面 | 页脚（无对应） | — | 否 | 本屏自定 |
| `cfg.btn_end_tx` | 退出游戏 | 页脚（无对应） | — | 否 | 本屏自定 |

---

## §2 两向差异表（**只登记不补**；用户裁定 #10）

### 2.1 原版有、本屏无（8 项；冻结书 §3.4①；原件日文 ★目视）

| # | 原版行（页） | 原件日文（目视原文） | 原版取值 |
| ---: | --- | --- | --- |
| 1 | 场景跳过功能（页1） | シーンスキップ機能 | ON / OFF |
| 2 | 语音跳过（页1） | 音声スキップ | する / しない |
| 3 | 跳过模式（页1） | スキップモード | 既読のみ / 全て |
| 4 | 选择后跳过（页1） | 選択後のスキップ | 持続 / 解除 |
| 5 | 已选选项变色（页1） | 選んだ選択肢の色を変更 | ON / OFF |
| 6 | 自动快速存档（页1） | 自動クイックセーブ | 選択肢毎 / シーン毎 / 選択肢+シーン毎 / しない |
| 7 | 播放语音时降低 BGM 音量（页2） | 音声再生時に BGM 音量を下げる | ON / OFF |
| 8 | 角色语音（页2） | キャラクター音声 | 全て ON / 全て OFF |

### 2.2 本屏有、原版无

**（A）冻结书 §3.4② 明列（本批权威口径）**：画面模式／立绘窗口／演出效果／特效／隐藏光标／存档时的确认信息／读档时的确认信息／文字变色／（本批删除的）播放影片／6 个「静音」toggle。

**（B）冻结书 §3.4 两向表未列、但原版两页确无对应行的其余本屏行（本次判读补登，标注供主代理确认）**：

| 本屏行（设置键） | 原版两页是否有对应行 | 说明 |
| --- | --- | --- |
| `voicecut` 语音截断 | 无（`音声スキップ` 归 2.1） | 语义与 `音声スキップ` 相近但方向不同（本屏=是否截断语音；原版=是否跳过语音），冻结书未列入任一方向 |
| `auto_speed` 自动播放速度 | 无 | 原版页1 的 `メッセージ速度` 已对 `text_speed`，自动播放速度系本屏自定 |
| `allskip` 全部跳过 | 无（`スキップモード` 归 2.1） | 语义相关但非同一行，冻结书未列入任一方向 |
| `vol_master` 主音量 | 无 | 原版只有 Voice/BGM/SE/システム 四路，无总音量行 |
| `vol_char` 角色音量 | 无（`キャラクター音声` 归 2.1） | 原版 `キャラクター音声` 是逐角色 ON/OFF「全てON/OFF」，本屏是「当前选中角色」的音量滑条 |

> 处置：**只登记、本批不补**（用户裁定 #10）。上表 B 组为本次目视比对两页后的补充判读，**方向判定请主代理确认**（若与冻结书 §3.4 口径冲突，以主代理裁定为准）。

---

## §3 待入表条目（**交主代理写入作品层术语表**；子代理只提交不落表）

> 落点：`工程\我们没有翅膀——格雷塔迦露德与柳木原\作品skill\术语表.md`（UI 词节）。
> 格式：日文原词 → 中文定稿 → 出处（件名／屏内元素 id）。

| 日文原词 | 中文定稿 | 出处（件名／屏内元素 id） | 备注 |
| --- | --- | --- | --- |
| `Voice ボリューム` | **语音音量** | `otv_bg_config_02`（原版页2 行名）／`cfg.snd_vol_voice_lb.sample` | ★ 本批唯一用词改动（原「主音量（语音）」，与 `vol_master` 撞名） |
| `BGM ボリューム` | 背景音乐 | `otv_bg_config_02`／`cfg.snd_vol_bgm_lb` | 本屏现行 |
| `SE ボリューム` | 音效 | `otv_bg_config_02`／`cfg.snd_vol_se_lb` | 本屏现行 |
| `システムボリューム` | 系统音效 | `otv_bg_config_02`／`cfg.snd_vol_sysse_lb` | 本屏现行 |
| `ウィンドウの不透明度` | 文本窗口的不透明度 | `otv_bg_config_01`／`cfg.row_winopac_lb` | 本屏现行 |
| `メッセージ速度` | 文字显示速度 | `otv_bg_config_01`／`cfg.row_textspeed_lb` | 本屏现行 |
| `初期設定に戻す` | 初始化 | `cf_init`／`cfg.reset_tx` | 本屏现行 |
| `キャラクター音声` | （本屏未直接采用；语义近邻＝「角色语音设定」`cfg.sec_charvoice` / 「角色音量」`cfg.snd_vol_char_lb`） | `otv_bg_config_02` | **语义不同**（原版=全体 ON/OFF），入表时须注明 |
| `音声スキップ` | （未采用，登记对照） | `otv_bg_config_01` | 差异表 2.1 #2 |
| `スキップモード`（`既読のみ` / `全て`） | （未采用，登记对照） | `cf_skip1` / `cf_skip2`（引自冻结书 §3.3） | 差异表 2.1 #3 |
| `選択後のスキップ`（`持続` / `解除`） | （未采用，登记对照） | `cf_sskp1` / `cf_sskp2`（引自冻结书 §3.3） | 差异表 2.1 #4 |
| `全てON` / `全てOFF` | （未采用，登记对照） | `cf_aon` / `cf_aoff`（引自冻结书 §3.3） | 原版为「全选」按钮，非「自动播放」（旧 M5 表误标） |
| `音声再生時に BGM 音量を下げる` | （未采用，登记对照） | `cf_bgmdn`（引自冻结书 §3.3） | 差异表 2.1 #7 |

> **同时请主代理在本屏 note 或本批工程记录里登记「行名改定」**：`25_config.json` 内仍有 5 行 note（§5.3）以旧行名「主音量（语音）」指代该行——均属 2026-09-26 的**变更记录留痕**，本批**未改写**（遵「历史留痕不改写」）。

---

## §4 四路引用扫描（`cfmovie` 删除的安全性证据）

扫描命令：`grep -rl "cfmovie" .`（全 UI 组）＋ 逐文件计数。结论：**无任何活引用**。

| 路 | 范围 | 命中 | 逐路结论 |
| --- | --- | --- | --- |
| ① 屏数据 | `layout/screens/*.json` | 仅 `25_config.json`（3 元素 ＋ note 1 处） | **即本次被删的 3 件本身**；其余 16 屏零引用 ⇒ 无跨屏引用 |
| ② 出货 `.tjs` | `krkr/**/*.tjs` | 仅 `krkr/game/ui_layout.tjs`（4 处） | **生成物**（由 `工具/gen_layout.py` 从屏数据生成；主代理统一重生成）。**逻辑层 `.tjs`（`ui_settings.tjs`/`ui_screens.tjs`/`ui_widget.tjs`/`ui_state.tjs`/`ui_dialog.tjs`…）零引用** ⇒ 无按 id 解引用 |
| ③ 复刻 `.js` | `复刻/*.js` | 仅 `复刻/ui_layout.js`（4 处） | **生成物**（同上，主代理重生成）。`复刻/replica.js`（手工维护渲染器）**零引用** ⇒ 无按 id 解引用 |
| ④ 巡演与脚本 | `工具/**`、`_工作/**/*.py`、`run_*.bat` | `工具/` **0 命中**；`_工作/**/*.py` 命中 6 支**均为历史复现脚本** | 6 支＝`m47_build_config.py`（**已退休的旧生成器**，重跑会覆盖手改）、`m09_selfcheck.py`（其期望清单含 `cfg.row_cfmovie_lb`）、`m01_rightcol.py`（注释留痕）、`psv_build_config_screen.py`／`psv_fix_config_screen.py`／`psv_config_audit.py`（2026-09-26 换皮期复现脚本）。**`run_all.py` 不调用其中任何一支**（已核：`run_all.py` 对上述 6 名 `25_config` 均 0 命中）⇒ **非活闸门**，不构成引用 |

**判定线补充（`invoke` 层）**：`layout/screens/_index.json` 的 `config` 条目 `required=["底图","设置项列表 ≥12 项","说明栏","返回"]`，删行后仍 12 行 ⇒ **≥12 仍满足**，且该文件零 `cfmovie` 引用。

**结论**：`cfg.row_cfmovie_lb` / `_bg` / `_hit` 三件**无任何活引用**（活引用只存在于「生成物」与「历史脚本/证据」两类，前者由主代理重生成、后者不参与运行），**可安全删除**。屏数据元素数 **470 → 467**。

---

## §5 自跑命令与输出原文

### 5.1 JSON 合法性 ＋ 元素计数 ＋ 无 `cfmovie`

```
$ export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
$ cd "…\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
$ python -c "import json,io; d=json.load(io.open('layout/screens/25_config.json',encoding='utf-8')); print(len(d['elements'])); assert not [e for e in d['elements'] if 'cfmovie' in e['id']]"
467
$ echo $?
0
```

（`json.load` 成功 ⇒ JSON 合法、无悬空逗号；`assert` 通过 ⇒ 无 `cfmovie` 前缀 id；计数 **467** ✓）

### 5.2 改后 grep「主音量（语音）」（`--include=*.json --include=*.tjs --include=*.js`）

**活体树（出货/源，排除 `_工作/` 历史证据）**：

```
krkr/game/ui_layout.tjs          7   ← 生成物（主代理重生成）
layout/ui_layout.json            7   ← 生成物（主代理重生成）
复刻/ui_layout.js                7   ← 生成物（主代理重生成）
layout/screens/25_config.json    6   ← 5 行 note 留痕（§5.3）
复刻/replica.js                  2   ← ★ line2006 = 活体镜像（须改，见 §5.4）；line2027 = 缩写标签
```

**历史（`_工作/`）**：8 文件 / 27 处（`25_config.*` 旧快照 3 档、`replica.js`/`ui_layout.js` 影子副本）⇒ **历史留痕，不改写**。

- `krkr/game/ui_settings.tjs` 改后 **0 命中** ✓
- 逐处判定见 §5.3 / §5.4。

### 5.3 `25_config.json` 内 6 处残留（5 行）逐处判定

| 行 | 元素 | 文本摘要 | 判定 |
| ---: | --- | --- | --- |
| 3788 | `cfg.sec_voice`.note | 「…节题『语音设定』上移…原槽位由下移一个节距的『主音量（语音）』行顶替…页2 后两行（主音量（语音）/角色音量）整体下移 74px」 | **历史留痕**（★ 2026-09-26 C 组修复 变更记录） |
| 4991 | `cfg.sl_voice`.note | 「…声音页左列滑条族『移 +30 并收窄』…（主音量（语音） 行的滑轨）」 | **历史留痕**（★ 2026-09-26 订正①） |
| 5015 | `cfg.sl_voice_hit`.note | 「…（主音量（语音） 行的滑块热区）」 | **历史留痕**（★ 2026-09-26 订正①） |
| 5041 | `cfg.sl_voice_end_lo`.note | 「…x 732 → 762（主音量（语音） 行的 MIN 端点文字）」 | **历史留痕**（★ 2026-09-26 订正①） |
| 5066 | `cfg.sl_voice_end_hi`.note | 「…主音量（语音） 行的 MAX 端点文字…本件不动」 | **历史留痕**（★ 2026-09-26 订正①） |

⇒ 5 行**全部为「已完结变更的日期化记录」**（均带 `★ …（2026-09-26…）` 前缀），**属历史留痕**，按本工程「历史留痕不改写」纪律**本批未改**。**若主代理要求出货产物内旧行名归零**，需一并决定是否改写这 5 行（改之＝改写变更记录，建议改由主代理在本批 note 追加「2026-09-30 行名由『主音量（语音）』改为『语音音量』」的现行陈述，而非回改旧日期块）。

### 5.4 ★ 必须由主代理/另一 editor 处理的一处（**超出本 editor 的写入边界，未改**）

`复刻/replica.js` 第 2006 行（HTML 复刻端**手工维护**的设置仓，与 `ui_settings.tjs` 逐键镜像）：

```js
vol_voice:   { min: 0, max: 100, def: 80, step: 5, apply: false, label: '主音量（语音）' },
```

- 该文件在派单中列为「**绝对不要改**」（归另一 editor/主代理），故**本次未改**。
- **但它是活体镜像**：`ui_settings.tjs` 头部明言「krkr 侧 / HTML 侧……改任一侧的口径都必须改另一侧」；不改则两端设置仓的 `vol_voice.label` 出现分歧（Critical 类双端分叉）。**请主代理在 `复刻/replica.js` 同步改为 `'语音音量'`**。
- 同文件第 2027 行 `mute_vol_voice.label = '主音量（语音）·静音'`：本屏/引擎的静音键标签口径为「静音（语音）」（`ui_settings.tjs`），HTML 侧则为「`<行名>·静音`」⇒ **这一差异系本批之前既有**（非本批引入）；若主代理统一口径，宜把该处改为 `'语音音量·静音'`（或按统一约定改全 6 个 `mute_vol_*`）。**本 editor 不改**。

### 5.5 12 行标签 ↔ `ui_settings.tjs` 逐条同名核对（19 项：13 枚举行 ＋ 6 滑条行名）

| 屏内元素 id | 设置键 | 屏内 `sample` | `ui_settings.tjs` `label` | 一致 |
| --- | --- | --- | --- | --- |
| `cfg.row_winopac_lb` | `dlg_winopac` | 文本窗口的不透明度 | 文本窗口的不透明度 | ✓ |
| `cfg.row_display_lb` | `display` | 画面模式 | 画面模式 | ✓ |
| `cfg.row_facewindow_lb` | `facewindow` | 立绘窗口 | 立绘窗口 | ✓ |
| `cfg.row_drama_lb` | `drama` | 演出效果 | 演出效果 | ✓ |
| `cfg.row_effect_lb` | `effect` | 特效 | 特效 | ✓ |
| `cfg.row_voicecut_lb` | `voicecut` | 语音截断 | 语音截断 | ✓ |
| `cfg.row_curhide_lb` | `curhide` | 隐藏光标 | 隐藏光标 | ✓ |
| `cfg.row_savedialog_lb` | `savedialog` | 存档时的确认信息 | 存档时的确认信息 | ✓ |
| `cfg.row_loaddialog_lb` | `loaddialog` | 读档时的确认信息 | 读档时的确认信息 | ✓ |
| `cfg.row_textspeed_lb` | `text_speed` | 文字显示速度 | 文字显示速度 | ✓ |
| `cfg.row_autospeed_lb` | `auto_speed` | 自动播放速度 | 自动播放速度 | ✓ |
| `cfg.row_allskip_lb` | `allskip` | 全部跳过 | 全部跳过 | ✓ |
| `cfg.row_textcolchg_lb` | `textcolchg` | 文字变色 | 文字变色 | ✓ |
| `cfg.snd_vol_master_lb` | `vol_master` | 主音量 | 主音量 | ✓ |
| `cfg.snd_vol_bgm_lb` | `vol_bgm` | 背景音乐 | 背景音乐 | ✓ |
| `cfg.snd_vol_se_lb` | `vol_se` | 音效 | 音效 | ✓ |
| `cfg.snd_vol_sysse_lb` | `vol_sysse` | 系统音效 | 系统音效 | ✓ |
| `cfg.snd_vol_voice_lb` | `vol_voice` | **语音音量** | **语音音量** | ✓（本批同改） |
| `cfg.snd_vol_char_lb` | `vol_char` | 角色音量 | 角色音量 | ✓ |

**结论：19/19 逐条同名，0 不一致**（核对脚本见 §5.6 输出）。

**另注（既有口径差异，非本批引入、本 editor 不改）**：6 个「静音」toggle 的**屏内常显标签统一为「静音」**（`cfg.snd_vol_*_mute_lb`），而 `ui_settings.tjs` 的 6 个 `mute_vol_*` 键 `label` 为「静音（主音量）／静音（背景音乐）／…」（HTML 侧 `replica.js` 又作「主音量·静音」）。三处对「静音」标签的写法不统一 ⇒ **登记，请主代理裁决是否统一**（本批若改会牵动屏数据/引擎/HTML 三端，故不在本 editor 两处范围）。

### 5.6 核对脚本输出原文

```
screen_id                key          screen_sample    tjs_label        match
cfg.row_winopac_lb       dlg_winopac  文本窗口的不透明度        文本窗口的不透明度        OK
cfg.row_display_lb       display      画面模式             画面模式             OK
…（略，逐条 OK）…
cfg.snd_vol_voice_lb     vol_voice    语音音量             语音音量             OK
cfg.snd_vol_char_lb      vol_char     角色音量             角色音量             OK
rows= 19 diff= 0
--- mute labels in tjs ---
mute_vol_master = 静音（主音量）
mute_vol_voice  = 静音（语音）
--- screen mute_lb samples ---
cfg.snd_vol_master_mute_lb = 静音
cfg.snd_vol_voice_mute_lb  = 静音
```

### 5.7 git 变更面（`git diff --numstat`）

```
1   1    …/UI组/krkr/game/ui_settings.tjs          ← 仅 vol_voice.label 一行
1   66   …/UI组/layout/screens/25_config.json      ← 删 65 行（3 元素）＋ 改 1 行（sample）
```

- `25_config.json` 行尾：改前/改后均 **CRLF**（10948 = 10948），字节 569209 → 567381（`-65 行` 与 `主音量（语音）`→`语音音量` = −3 汉字）。
- `ui_settings.tjs` 行尾：改前/改后均 **LF**（HEAD blob 与工作区同为 LF，`git diff` 明示 `1 1`，未整文件改行尾）。`git diff` 的「LF will be replaced by CRLF」为 **core.autocrlf 既有提示**（HEAD blob 本就是 LF），非本次改动引入。

---

## §6 未决问题 / 需主代理裁决点

1. **判读证据图缺件**：派单点名的 `证据/cf_labels_A.png`、`cf_labels_B.png`、`bg_config_01_2x.png`、`bg_config_02_2x.png` 全库不存在（`证据/` 仅 `cfmovie_row_check.png`）。本次改用仍存在的 `PSV系统UI参考/超分2x/otv_bg_config_01/02.png` 目视复核原版两页（14 行），与冻结书 §3.3 **逐行一致**；逐件 `cf_*` 读数无法独立复核（`cf_*` 素材全库 0 命中）。**是否补落盘判读证据请主代理定**。<br>→ ✅ **已办（2026-09-30 · 主代理补落盘）**：这 4 件现已在 `_工作\ISSUE-20260930-06_收尾交接\证据\`（`cf_labels_A.png` 84,474 B／`cf_labels_B.png` 79,422 B／`bg_config_01_2x.png` 1,453,626 B／`bg_config_02_2x.png` 1,160,116 B，连同 `cfmovie_row_check.png`）⇒ **本条关闭**。
2. **`复刻/replica.js` 第 2006 行须同步改**（活体镜像，见 §5.4）——超出本 editor 写入边界，**未改，请主代理/负责 `复刻/*.js` 的 editor 落实**。<br>→ ✅ **已办（2026-09-30 · 主代理落实）**：盘面实测 `复刻/replica.js:2006` ＝ `label: '语音音量'`、`:2027` ＝ `label: '语音音量·静音'` ⇒ **本条关闭**（屏数据／`ui_settings.tjs`／HTML 三端 `vol_voice` 行名一致）。
3. **`25_config.json` 内 5 行旧行名留痕**（§5.3）：本批按「历史留痕不改写」未动。若要求出货产物内旧串归零，需主代理决定改写方式（建议追加现行陈述，不回改 2026-09-26 旧块）。
4. **「静音」标签三处写法不统一**（§5.5 末注）——屏数据「静音」/ `ui_settings.tjs`「静音（X）」/ `replica.js`「X·静音」；**登记，请主代理裁决是否统一**（本批未改）。
5. **§2.2(B) 的 5 行方向判定**（`voicecut`/`auto_speed`/`allskip`/`vol_master`/`vol_char`）：为本次目视补登，冻结书 §3.4 两向表未列，**方向判定请主代理确认**。
6. 生成物（`layout/ui_layout.json`、`krkr/game/ui_layout.tjs`、`复刻/ui_layout.js`）仍含旧行名 7 处 / `cfmovie` 4 处，**待主代理统一重生成**（本 editor 未跑 `gen_layout.py`，遵派单纪律）。<br>→ ✅ **已办（2026-09-30 · 主代理统一重生成）**：现盘面三处产物对「主音量（语音）」各 **5 处**、对 `cfmovie` 各 **1 处**，**全部落在 `note` 字段内（历史变更留痕，按「历史留痕不改写」保留）**，**无一处是活跃字段**（`sample`/`label`）；三处产物一致性由 `verify_ui [3]` 守 ⇒ **本条关闭**（验收口径已由冻结书 §7.3-2 由「全库 0 命中」改为「**活跃字段 0 命中**」）。另：`layout/screens/25_config.json` 的 M47 设计 note 仍称该 3 件「永久预留」——由主代理按冻结书 §7.3-3 **追加**一句现行陈述（「2026-09-30 起该 3 件已按用户裁定 #11 删除」），不回改 2026-09-24 旧块。
