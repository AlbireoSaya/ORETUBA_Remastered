# 资源组工具链 · 运行方式与路径约定

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（工具链运行方式与路径约定） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> 适用：`资源组\工具\` 下的**全部构建器与校验器**（`build_scene_*.py`、`verify_scene_*.py`、
> `build_spine.py`、`build_asset_ledger.py`、`emit_ledger_docs.py`、`verify_asset_ledger.py`、
> `build_rulings_fixtable.py`）。
> 最后更新：2026-09-30（ISSUE-20260930-12：§二 复跑顺序补 `build_rulings_fixtable.py`；新增 §七
> `term_unify` 共享模块与负向自证；此前 §六 为 ISSUE-20260919-10 补充）。

## 一、读写分离（所有脚本统一）

本工程的大体积只读源被 `.gitignore` 排除，**仅存在于主工作区**（源工程语料 / `krkr素材库`
实体文件 / `资源总账.json`）。为使 issue 分支的 checkout（含 git worktree）能独立复跑，
所有脚本一律采用**读写分离**：

| 角色 | 取值 | 内容 |
| --- | --- | --- |
| **读** | `DATA_ROOT` | 源工程（`我们没有翅膀` / `我们没有翅膀R` / `After Story` / `前奏诗` / `涅布＊普拉斯` / `我们没有翅膀PSV`）、`资源组\krkr素材库\` 实体文件、`资源总账.json`、`_冲突数据.json` |
| **写** | 本 checkout（由脚本自身 `__file__` 推导） | `资源组\剧本\scene_*.jsonl`、`spine.json`、`主线编排方案.md`、`krkr素材库\{资源总账.json,.md,.schema.md}`、`子代理工作区\ISSUE-20260918-06\W*\*`（构建统计 / 验收自证） |

- `DATA_ROOT` 默认 `E:\ZCode Workspace\Galgame`（主工作区），可用环境变量覆盖：

  ```bat
  set GRETA_DATA_ROOT=D:\some\other\checkout
  ```

- **从主工作区运行**：读写根重合，行为与历史一致。
- **从 worktree / issue 分支运行**：数据仍从主工作区**只读**读取，**产物全部落在本 checkout 内**，
  不会误写主工作区。
- **边界断言**：每个脚本在写出产物前调用 `_assert_in_checkout()`；若产物路径不在本 checkout 内，
  立即 `SystemExit` 报错中止（fail loud，绝不静默写错位置）。

## 二、复跑顺序（全链路）

在 checkout 根目录依次执行（`python` 需 3.10+；本机为 3.14）：

```bat
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_rulings_fixtable.py" :: 生成 修正表_裁决20260930.tsv；六源构建器以该表为输入，必须先跑
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_jsonl.py"   :: otr 亚衣线
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ot.py"        :: ot 本篇
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_ota.py"       :: ota After Story
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_otp.py"       :: otp 前奏诗
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_np.py"        :: np 涅布明日香篇
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_otv.py"       :: otv PSV 美咲线
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_spine.py"           :: 主线编排（须在六源之后）

python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_asset_ledger.py"    :: 总账
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_ledger_docs.py"      :: 总账 md/schema
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_asset_ledger.py"   :: 总账验收

python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_jsonl.py"    :: 以下六源校验器，全部 ALL_PASS 方可交付
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_ot.py"
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_ota.py"
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_otp.py"
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_np.py"
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_otv.py"
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_schema_enums.py"  :: 枚举 × 数据一致性
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/selftest_term_unify.py"    :: term_unify 负向自证（见 §七）
```

**幂等**：构建器以 `newline="\n"` 写出，可反复执行；同一 checkout 内连跑两轮，六源
`scene_*.jsonl` 逐字节一致。

## 三、行尾约定（**统一 LF**）

- 六源 `资源组\剧本\scene_*.jsonl` **约定 LF（`\n`）**，与构建器 `open(..., newline="\n")` 一致；
  校验器按 LF 读取，不依赖平台默认换行。
- 仓库根 `.gitattributes` 已对 `工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/剧本/*.jsonl`
  声明 `text eol=lf`，避免 `core.autocrlf=true` 在下次 checkout 时把工作区改回 CRLF。
- 若手工改动这些 jsonl，请保持 LF；不要引入 CRLF（否则校验器仍可读，但会产生无意义的换行差异）。

## 四、引用命名空间（消费侧关键）

`lines[].audio[]` 与 `assets[].out_relpath` 必须是**素材库相对路径**
（`<源代号>/<kind>/<源代号>_<名>`，如 `otv/voice/otv_16862_misaki_000.ogg`），
且必须能在 `DATA_ROOT\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\krkr素材库\`
下 `isfile`。六源校验器均已内置该项检查（otr 记为 `A9`，其余记为 `A8`）：

1. 以该源代号前缀开头；
2. 在 `krkr素材库\` 下真实存在（`isfile`）；
3. `assets[].hit` 与库内存在性严格一致；
4. `assets_missing[]` == `hit=false` 的 ref 集合。

任一项不满足即该项 FAIL → `ALL_PASS=False`。

## 五、已知非缺陷缺口（校验器如实登记，不阻断 ALL_PASS）

- `ota`：87 行 `voice` 非空但 `audio=[]`（立绘名被误判为语音，源侧事实）。
- `np`：1,325 行 `voice` 非空但 `audio=[]`（ASU 音库本机缺失，B5 无解）。
- `ot`：1 个素材引用无 `out_relpath`（`assets_missing` 如实登记）。

## 六、校验器对 gitignored 中间产物的依赖（ISSUE-20260919-10 补充）

### 6.1 现状

`verify_scene_jsonl.py`（otr）的 **A3 来源门控**判据需要构建器落盘的门控留痕
`corrections_gated_out`，该留痕只存在于：

```
子代理工作区\ISSUE-20260918-06\W6a2\_build_stats.json
```

**该文件被 `.gitignore` 排除**（属构建统计，不入库）。因此在一个**干净 checkout**（新 worktree /
CI 式干净克隆）里该文件**必然不存在**。

- **产物 `scene_otr.jsonl` 不编码门控信息**（其 md5 必须稳定，不得为校验器新增字段），故该统计
  缺失时**门控留痕不可从产物自证**。
- 该依赖**只影响校验器，不影响产物**：有无 `_build_stats.json`，`scene_otr.jsonl` 的 md5
  **完全不变**（实测 `ea3703183e88d23ff17625676234e56e`）。

### 6.2 缺件时的行为（已按此实现）

`verify_scene_jsonl.py` 不再因缺件而报 FAIL：

| 情形 | `A3_status` | `A3_pass` | 说明 |
| --- | --- | --- | --- |
| 有 `_build_stats.json` | `PASS` / `FAIL` | `True` / `False` | 判据与修前**逐项完全一致** |
| 缺件，且范围内条目**全部生效**（无未命中、账目自洽） | `PASS` | `True` | 无需门控即可判定 |
| 缺件，且存在未命中条目 | **`SKIP_ENV`** | `None` | **不判 FAIL**；打印可执行提示 |

- 缺件时会打印可执行提示：**「请先运行 `build_scene_jsonl.py` 生成该统计后复跑本校验器。」**
- 汇总口径：`ALL_PASS` 只在**可判定项**上取合取（SKIP 不计入 FAIL）；未复核项另记
  `A_skipped`，并单列 `ALL_PASS_STRICT`（要求无任何 SKIP）。**SKIP 不会被静默掩盖**。

### 6.3 运行顺序（otr 专用）

`verify_scene_jsonl.py` **必须排在 `build_scene_jsonl.py` 之后**：

```bat
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_jsonl.py"   :: 先跑，产出 scene_otr.jsonl + W6a2\_build_stats.json
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_scene_jsonl.py"   :: 后跑，A3 可完整判定
```

- 若只跑校验器（例如干净 checkout 只想核产物），A3 会标 `SKIP_ENV`；**这属于环境缺件，不是产物缺陷**。
- 同类依赖在 `verify_scene_otv.py` 亦存在（读 `W6e\_build_stats_otv.json`）；otv 的范围内条目
  **现行 14 条**（`修正表_otv.tsv` 1 ＋ `修正表_裁决20260930.tsv` 13；ISSUE-20260930-12 订正，
  旧记「只有 1 条」为 2026-09-19 口径），故缺件时该源的 A3 会退化为 `SKIP_ENV`、**不判 FAIL**；
  `verify_scene_ot/ota/otp/np.py` 不依赖该统计（其门控期望值由修正表自身推导，账目表派生）。

## 七、`term_unify` 共享模块与负向自证（ISSUE-20260930-12）

- **`_term_unify.py`**（同目录共享模块，**非独立运行**）：`fix_type=term_unify` 的**唯一**消费实现，
  六个语料构建器（`build_scene_{ot,otp,ota,otv,np,jsonl}.py`）共用，保证**语义只有一处实现**。
  规则：`old_text` = 被替换**词形（正则）**、`new_text` = **替换值**（**不是整句**）——命中即
  `re.sub(old_text, new_text, cn)`、未命中但已是后态即**幂等 no-op**（留痕 `term_unify_noop`）、
  两者都不是即 **fail loud**。语义权威说明与理由见 `资源组\修正\_README.md` §三.3。
- **`selftest_term_unify.py`**（同目录**负向自证**脚本，由本 issue 另一并行任务新增）：回归测试——
  `_term_unify.apply` 的三个分支（`applied` / `noop` / fail loud）必须**都能真的走到**，
  且「子串陷阱」不得自爆（采用值 `美空学院` 不得被替换成 `美美空学院院`）。用法：
  `python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/selftest_term_unify.py"`
  （退出码非 0 即失败）。

## 八、逐行演出表（ISSUE-20261001-14）

产物落 `资源组\演出\`（**新建目录**）：六张 `演出_<源>.tsv` ＋ `头像族判读.tsv` ＋ `_index.json` ＋ `演出表说明.md`。
消费契约（**编程组要看的那份**）＝ `资源组\交接编程组\交接说明.md` **§三 C21**；一页总纲＝ `演出\演出表说明.md`。

**跑的顺序**（读写分离：读 `GRETA_DATA_ROOT`，写本 checkout）：

```
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_sob0.py"   # ot / otp
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_otv.py"    # otv
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_tob.py"    # otr / ota
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_staging_np.py"     # np
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_face_family_verdict.py"
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_staging.py"       # 独立机检 → ALL_PASS
python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/emit_staging_index.py"  # _index.json
```

- **`_staging_common.py`**（同目录共享模块，**非独立运行**）：本族的**唯一契约实现**
  （`Ledger` 按源分域 / `ArtFamilies` 权威族别 / `SeqMap` / `write_tsv` / `row()` 的枚举与 `script=` 闸门），
  四个生成器共用。**⚠️ 改它必须重跑上面四个生成器 + `verify_staging.py` + `emit_staging_index.py`**——
  本批曾因「改了共享模块没重跑」致 `np`/`ota` 两表与生成器不一致，**由一审抓出并重出**。
- **`verify_staging.py`**（**独立校验器**）：**刻意不 import 任何生成器与 `_staging_common`**（AST 已证），
  故「生成器写错、校验器跟着错」不会同时发生。闸门 ①外键守恒 ②素材存在 ③角色名封闭 ④行数守恒
  ⑤枚举封闭 ⑦集合守恒（整源＋**逐场**双口径，`skip` 场景单列豁免并计数）；**⑥ 实机抽查不在其内**。
- **各生成器与 `emit_*` 均支持 `--check`**（幂等自检，**不写产物**）。`build_staging_tob.py` 的 `--check`
  是后补的（原先缺失 ⇒ 以 `--check` 调用会**静默重写**，属缺陷，已修）。
- **口径要点**：`seq` = 「紧随该 op 之后第一个文本行的行号」（`after_last_line`/`before_first_line` 逐行注明）；
  `target` = 总账 `out_relpath` 全路径且**按源分域**；`chr_add`/`chr_expr` 的二分是**文档化启发式**（不入 `confidence`）。
- **本族的硬边界**（源侧事实，详见 C21 与 `演出表说明.md` §二）：立绘**退场无信号**（不产出 `chr_remove`）／
  `ot`·`ota`·`otp`·`otr` **拿不到 BGM**／`np` 只到「首次引用位」／`ot_s04_13b` 引 `SE\SE23.OGG` 对不上素材账。