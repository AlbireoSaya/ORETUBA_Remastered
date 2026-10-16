# 2026-09-30 对于《我们没有翅膀——格雷塔迦露德与柳木原》`term_unify` 词形级的修改

- Issue：`ISSUE-20260930-12` ｜ 模式：**工程** ｜ 分支：`issue/ISSUE-20260930-12-greta-term-unify-word-level` → `main`
- 参与代理：editor×3（消费方/校验器、文档与产物清单、枚举与负向自证）、reviewer×1（一审）
- 工作树：`临时\wt-tu`（**未在主工作树动手**——主工作树仍停在 `issue/ISSUE-20260918-06-greta-res-phase2`，见「风险」第 4 条）

## 任务目的

把 `fix_type=term_unify`（`资源组\修正\修正表_裁决20260930.tsv`，**123 行**）的语义由
**「整槽覆盖 `cn`」** 改为 **「词形级替换」**，消除「整槽覆盖会把该槽**别的字**一并写回旧句 ⇒
上游一旦润色/重译，这行会静默把改进顶回去」这一**正确性级**隐患，并顺带解除对本项目之外
`工程\我们没有翅膀\汉化\剧情汉化\` 的**整句基准层依赖**。

**验收标准**（三项全部达成才可交付）：

1. 六源 `资源组\剧本\scene_*.jsonl` 重跑后与 `main` **逐字节相同**（同替换、同结果 ⇒ 只允许表示形式变，不允许产物变）；
2. 全部闸门 `ALL_PASS`：六源校验器 ＋ `verify_schema_enums.py` ＋ 生成器两级硬闸门 ＋ 交付包自检 ＋ 负向自证脚本；
3. **每条判据都能真的失败**（改坏即变红，改回即复绿）——含消费侧三分支与校验侧判据。

## 改动清单

### 新增（2）

| 文件 | 行为 |
| --- | --- |
| `资源组\工具\_term_unify.py` | **`term_unify` 语义的唯一实现**（六源构建器共用，杜绝六处实现漂移）：`apply(cn, old, new)` 三分支——命中词形即 `re.sub`（`applied`）／已是后态即**幂等 no-op**（`noop`，不记 `fix_refs`、不计命中）／两者都不是即 **fail loud**（`SystemExit`）；另有校验器专用的 `verify(...)`（与 `apply` **刻意不共用实现**，避免自证），`ignore_u3000` 只豁免 U+3000 一个字符 |
| `资源组\工具\selftest_term_unify.py` | **负向自证**（只读、幂等）：子串陷阱（`空学`/`空学院`/`美空学` ⊆ `美空学院`，裸替换会自爆成 `美美空学院院`）／`apply` 三分支（fail loud **必须真抛**）／表内 123 行 `old_text` 的 G0b 独立复核（可编译、非空、**不得匹配空串**）／`verify` 正负两例与 `ignore_u3000` 四种对照 |

### 修改（23）

**生成器与六源消费方（7）**

| 文件 | 行为变化 |
| --- | --- |
| `资源组\工具\build_rulings_fixtable.py` | `old_text` 改为**词形正则**、`new_text` 改为**替换值**；**删除 `OT_BASE` 外部基准层**，槽位发现改为「六源成品语料 `fix_refs[0].cn_before`（若有）否则 `cn`」；新增 **G0b**（每行 `old_text` 必须可 `re.compile`、非空、**不匹配空串**）；G5/G5b/G6 判据改为作用于**模拟替换结果**；G6 改为「locator 往返 ＋ JP 门控 ＋ 基准句命中词形」 |
| `build_scene_ot.py` / `build_scene_otp.py` / `build_scene_ota.py` / `build_scene_otv.py` / `build_scene_np.py` / `build_scene_jsonl.py` | `term_unify` 分支改为调用 `_term_unify.apply`（**其余 `fix_type` 的整句覆盖与逐字符断言一字未动**）；新增 `TERM_NOOP` 留痕并计入构建统计（`term_unify_noop`）与打印；同目录共享模块导入前统一置 `sys.dont_write_bytecode = True`（不在工具目录留 `__pycache__`） |

**六源校验器（6）** —— 由旧「整句假设」改为**按 `fix_type` 分叉**：

| 文件 | 行为变化 |
| --- | --- |
| `verify_scene_ot.py` / `verify_scene_ota.py` / `verify_scene_otp.py` / `verify_scene_otv.py` / `verify_scene_np.py` | `term_unify` 行改用 `_term_unify.verify`；**层边界文本**优先取「下一条 `fix_ref` 的 `cn_before`」＞「`name_replaced[0].before`」＞「最终 `cn`」；`later_layers_touched` 降为**理论兜底**（本工程实测 **0 处**，另报 `term_later_waived`）；U+3000 由 `ignore_u3000` 单独豁免而**不再**并进「别的层」 |
| `verify_scene_jsonl.py` | `tables` 补 `修正表_裁决20260930.tsv`（此前缺席 ⇒ 账目等式必不成立）；**新增 otr 46 槽的逐槽词值复核**（`A3_term_checks`/`A3_term_ok`）——此前该源**只数命中条数、无任何词值判据**，而带 U+3000 的 19 槽全在 otr ⇒ 那 19 槽原本无人按判据 ② 复核；`SKIP_ENV` 降级语义保持不变 |
| 账目口径 | 各源「范围内 = 生效 ＋ 门控排除 ＋ 未命中」一律改为**由表内容推导**，删除写死的常量（如 np 的 `len(corr_rows)==153`、otv 的 `len(applied)==1`）——此前加入裁决表后出现 `未命中 -57` 这类**负数**账目 |

**枚举、审计与产物清单（4）**

| 文件 | 行为变化 |
| --- | --- |
| `verify_schema_enums.py` | `FIX_REF_ENUMS["fix_type"]` 补 `term_unify`；`SOURCE_DOMAIN["cn_origin"]["ot"]` 补 `fix_table`（`term_unify` 行在 ot 侧生效所产生） |
| `emit_handoff_manifest.py` | 本表与生成器两条描述的**已作废口径**改正（`old_text = 取文基准层` → 词形正则/替换值）；新增 `_term_unify.py`、`selftest_term_unify.py` 两条产物行（**产物清单 99 → 101 行**） |
| `audit_handoff_package.py` | 产物清单行数期望 99 → 101（跟随产物集，非放宽判据） |
| `交接编程组\产物清单.tsv` | 随之重跑（本表规模 124 行 / 49,784 B → **124 行 / 24,866 B**，词形化后体积降至约 1/2） |

**文档（6）**

| 文件 | 行为变化 |
| --- | --- |
| `资源组\修正\_README.md` | §一 目录表补本表行（九表合计 **456** 条）；§二 `old_text`/`new_text` 两行标注**语义按 `fix_type` 分叉**；**§三.3 整节重写**（词形级语义、正则守卫理由、三分支、`noop` 的已知边界、旧述作废、生成器闸门清单）；§四.5 门控例外理由链对齐 |
| `资源组\剧本\schema.md` | §四.6 声明集合 7→**8 值**（补 `term_unify` 行 ＋ ⚠️ 语义分叉提示）；§三.2 `cn_origin` 的 `fix_table` 行补 `term_unify` 并把行级计数更新为 **145**；§2.1 `fix_refs` 字段说明补语义分叉；§二.0 `cn_origin` 实测计数按重建后刷新 |
| `资源组\工具\_README_运行方式.md` | §二 复跑顺序在六源之前补 `build_rulings_fixtable.py`、末尾补 `selftest_term_unify.py`；**新增 §七**（共享模块与负向自证）；§六 订正 otv 范围内条目 1 → **14** |
| `资源组\03_资源总账_全量现状.md` | 修正层口径 **6 表 221 条 / 译名表 114 行 → 9 张 456 数据行 / 128 行（57 原词）**（三处：交付物总览、§4.2 明细表、§八 速查）；消费顺序补「`term_unify` 为唯一不受门控的例外」；`fix_type` 枚举「5 类」→「8 值」 |
| `资源组\交接编程组\交接说明.md`、`编程组开工指南.md` | 本表行补词形级语义与唯一实现出处 |
| `Galgame.md` | 本工程行**原地更新**：状态列修正层口径订正 ＋ 追加本 issue 交付说明；相关记录列追加本次记录文件名 |

## 验证方式与结果

工作树 `临时\wt-tu`，`export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"`，Python 3.14.7。

### 1. 六源语料逐字节不变（**核心判据**）

`build_rulings_fixtable.py` → 六源构建器全量重跑后，与 `main`（`604f849`）逐字节比对（去除 CR 后取 md5）：

| 源 | md5（重跑后） | 与 main |
| --- | --- | --- |
| `scene_ot.jsonl` | `5052aa59cf9c2dfbf3e46caa570dbaea` | **相同** |
| `scene_ota.jsonl` | `9120af66e5a81b4336edacaa2f94e910` | **相同** |
| `scene_otp.jsonl` | `39176ef38e1296822176d7e59f4cfcdd` | **相同** |
| `scene_otr.jsonl` | `2e3d9e83bff099ff3a62c4b44a9fd3e2` | **相同** |
| `scene_otv.jsonl` | `df75071e205e869bb0bb04891c8d2339` | **相同** |
| `scene_np.jsonl` | `e0f0d84f3791c57bb62f3629fe99efeb` | **相同** |

`build_spine.py` 复跑后 `spine.json` / `主线编排方案.md` **无改动**（下游无涟漪）。

**表侧不变量**：新表与 `main` 版表的 `(source,file,locator)` 集合**完全相同**（123 行逐行对齐）
⇒ 本次只改「同一批目标槽的表示形式」，未增删任何目标槽。

### 2. 闸门全绿

**判据说明（一审订正）**：六源 `verify_scene_*.py` **不传播退出码**（既无 `sys.exit`，`main` 版亦然，
属既有工具惯例）⇒ 对它们**以打印的 `ALL_PASS` 为判据**，不以退出码为判据；`verify_schema_enums.py`、
`selftest_term_unify.py`、`audit_handoff_package.py`、生成器 `--check` 则确有退出码，一并记录。

| 闸门 | 结果 |
| --- | --- |
| `build_rulings_fixtable.py`（G0–G8，11 项） | 123 行；`--check` **0 改动（幂等）PASS**（exit 0） |
| `verify_scene_ot / ota / otp / otv / np / jsonl` | 六源 **`ALL_PASS = True`**（打印判据；jsonl 的 A3 为真判 PASS，非 `SKIP_ENV`） |
| `verify_schema_enums.py` | **`ALL_PASS = True`**（exit 0；全局越界 0、分源取值域越界 0） |
| `selftest_term_unify.py` | **`ALL_PASS = True`**（exit 0） |
| `audit_handoff_package.py`（exit 0） | A 引用路径／B 计数口径（26 项，不符 **0**）／C 产物清单（101 行，路径缺失 0）／D 处置不变量／E 序章段／F 过期口径／**G 语料残留（六源合计 0 槽）** 全 PASS |
| 构建期 `term_unify` 幂等 no-op | 六源均 **0 条** |
| 工具目录 `__pycache__` | 补 `sys.dont_write_bytecode = True`（须在 import 兄弟模块**之前**）后，八道闸门与六源构建器复跑**均不再生成** |

### 3. 主代理独立复算（不依赖子代理与审计脚本）

- **残留归零（负向）**：按审计同一口径（13 条非采用变体 ＋ 畸形拼接正则）逐槽复算六源
  `lines[].cn` ⇒ **残留 0 / 明细空**。
- **采用值落盘（正向）**：`美空学院` 132 槽／`羽田家` 93／`GLORIOUS` 33／`柳警广场` 25／
  `低语材料` 13／`洛伊希滕` 10／`苍穹女子学院` 9（`隼` 1,081 为含 `隼人` 等的全部出现）。
- **豁免口径实测**：`term_unify` 槽共 **123**（ot 57／otr 46／otv 13／ota 5／otp 2）；其中带
  U+3000 的 **19 槽全在 otr**；走 `later_layers_touched` 兜底的 **0 槽**（改造前为 ot 1 槽，
  已改为按 `name_replaced[0].before` 层边界文本真判）。

### 4. 负向自证（**每条判据都证明「能失败」**）

| 判据 | 临时破坏 | 观察 |
| --- | --- | --- |
| 消费侧词形替换（ot/ota/otp/otv/jsonl 各自） | `new_text` 末尾加 `！` | 对应源 `ALL_PASS = False`（如 ot 账目行由 `未命中 0 : True` 变 `False`；jsonl `failed term checks = 46/46`） |
| 账目表派生（ot/jsonl/otv） | 从 `tables` 移除裁决表 | 复现旧缺陷形态（ot `未命中 -57`；otv `source=otv 1 命中 14`；jsonl `范围内 83 命中 122`）⇒ `ALL_PASS = False` |
| otr 的 U+3000 豁免（本次新判据） | `ignore_u3000=False` | `A3 term_unify 词值复核` 变 `False`，落盘 JSON 复算失败 **恰好 19 条**（= 带 U+3000 的槽数）⇒ `ALL_PASS = False` |
| 层边界文本真判（本次新判据） | 把边界文本退回 `l["cn"]` | `verify_scene_ot.py` 变红（该 ot 槽 `why: cn_after != re.sub(...)`） |
| `selftest` 子串陷阱 | 断言期望值改成 `美美空学院院` | 4 条 `[FAIL]`、退出码 1 |
| `selftest` fail loud 分支 | 把 `apply(无关句)` 换成 `pass` | 该条 `[FAIL]`、退出码 1 |
| `selftest` `ignore_u3000` 对照 8d | `ignore_u3000=False` 改 `True` | 8d 由 OK 变 `[FAIL]`、退出码 1 |

所有临时破坏均用 `Edit` 反向改回（**未用 `git checkout`**，以免抹掉未提交改动），复核 `grep` 无
`TEMP-NEGTEST` 残留，`py_compile` 全部通过。

## 风险、警示与未完成项

1. **`noop` 分支的已知边界（如实登记，不当检错器用）**：`noop` = 「文本已含采用值且不含变体」，
   采用值越短（如 `隼` 仅 1 字）越易被无关文本误触发 ⇒ **它不是 locator 漂移的检出器**；
   漂移由生成器 **G6**（独立消费键定位 ＋ JP 门控 ＋ 基准句命中词形）承担。因此 `noop` 命中时
   一律**留痕**（`term_unify_noop` 计入构建统计并打印），不得静默；构建期应恒为 0（实测 0）。
2. **`noop` 分支在「从基准层全量重建」路径下不会触发**（每个目标槽都应命中词形）。它是
   「半应用状态可判定 / 幂等重跑」的健壮性路径，由 `selftest` 覆盖（第 3 项成立、第 4 项必须抛错、
   第 7 项证明谓词非恒真）；**不构成死判据**。
3. **`fix_refs` 不携带 `old_text`/`new_text`**：消费方须回原表按 `locator` 取用（`schema.md` §四.6
   ⚠️ 块已注明）。语义按 `fix_type` 分叉是**本 issue 新增的第二种语义**（先例：`speaker_split` 的
   `old_text`/`new_text` = `#` 后标记头），已写进 `_README.md` §二/§三.3 与 `schema.md` §2.1/§四.6。
4. **主工作树未同步（接手须知）**：主工作树 `E:\ZCode Workspace\Galgame` 当前停在
   `issue/ISSUE-20260918-06-greta-res-phase2`（`9a8e4c5`），**其盘面 `资源组\` 副本落后于 `main`**
   （实测：`修正表_裁决20260930.tsv` 仅 92 行、`03_资源总账_全量现状.md` 为旧 U1 口径），
   且新增文件 `_term_unify.py` 在该处**不存在**。本次改动与交付物在 **`main` 分支**
   （经 `issue/ISSUE-20260930-12-*` 分支合并），**未回写该盘面**——按并发会话纪律，
   不在主工作树切分支/写文件。若需让该盘面与 `main` 同步，须由用户（或按其指示）单独执行。
5. **流程违规（如实登记）**：本会话为比对基线，曾**两次**把临时文件写入 **C 盘 `/tmp`**
   （`bash` 的 `/tmp` 不是工作区路径，违反 AGENTS.md 铁律 1/3），均在**同一条命令内 `rm` 删除**，
   未在工作区外留下任何产物。教训：基线数据一律内联在会话里或落 `临时\`，不要用 `/tmp`。
6. **另一处无条件放行路径（已消除）**：改造前 ot 有 **1 槽**走 `later_layers_touched` 无条件放行
   （`s04_03a&seq=3`：词形替换后又过 ③ 译名替换）。本次改为用**层边界文本**
   （`name_replaced[0].before`）真判 ⇒ 该路径命中数降为 **0**，`later_layers_touched` 仅作理论兜底，
   且校验器会报出 `term_later_waived` 计数。
7. **未完成/移交**：`03_资源总账_全量现状.md` §7.2 的 U3/U7 等**既有待裁决项**仍未裁决
   （属上游遗留，非本次引入）；本 issue 只做 `term_unify` 语义收口与其遗留红项结清。
8. **回滚方式**：本次改动全在 issue 分支；如需回退，`git revert` 本 issue 的合并提交即可
   （六源语料本就与 `main` 逐字节相同，回退后产物不变；需要改回的只有工具/文档/表）。原版与
   既有交付物均有备份：六源原始目录全程只读，`备份\`、`资源组\美术统一*\` 未触碰。

## 审查结论

- **一审：通过**（独立 reviewer，未参与本次改动；基线 `main` = `604f849`）。可判定项**全部独立复现**：自跑生成器与六源构建器后六源 md5 与 `main` 逐字节相同；八道闸门全过；`noop`／`ignore_u3000`／层边界文本优先级／账目是否放宽／jsonl 新增复核是否装饰／文档与枚举计数／作废口径残留／工程记录自述**逐条质证成立**；并**自行**做了一次临时破坏实验（`verify_scene_jsonl.py` 的 `ignore_u3000=False` ⇒ 真变红，改回后 md5 复原并复绿）。**无阻断级、无重要级**。
  - **一审「次要」项 1（已修）**：`交接编程组\交接说明.md` 记 `_README.md` = 391 行（`main` 版旧值），本 issue 重写 §三.3 后实测 428 行 ⇒ 已改为 **428 行**并注明口径（`产物清单.tsv` 按 for-line 迭代计；`wc -l` 计 427，因末行无换行）。
  - **一审「次要」项 2（已修）**：五个校验器 import 兄弟模块时**未**先置 `sys.dont_write_bytecode = True`（`verify_scene_otp.py` 虽有该行但在 import 之后、无效），会在工具目录生成 `__pycache__` ⇒ 六个校验器均已把该行**上移到 import 之前**（otp 的重复行已删），复跑确认不再生成。
  - **一审「无法判定」2 项（如实登记，均非本 issue 缺陷）**：① `作品skill\术语表.md:226` 的「全库含 `隼` 7,302 槽」与六源语料实测（1,081 槽）不符，因该处**未注明统计基准语料**而无法判定——该文件本轮未改，属上游既有内容；② 六源校验器不传播退出码（既有惯例），故本记录已改用「打印的 `ALL_PASS`」为判据（见上节）。
- **二审 / 合并**：主代理亲自复核（读 diff、复跑全部闸门、独立复算残留与采用值、独立核验 19/1/0 豁免计数与 `schema.md` 全部分源计数）后**合并**。
  - 分支提交 `953e2f7` → 合并提交 **`8d75522`**（`git merge --no-ff`，在检出了 `main` 的独立 worktree `临时\wt-qbicons` 内执行；**未在主工作树切分支**）。合并后以 `git merge-base --is-ancestor 953e2f7 main` 自检 ⇒ **YES**（防「两 worktree 同检 main 静默丢提交」那类事故）。
  - **合并后复验（在 `main` 检出内）**：`verify_scene_ot/ota/otp/np/otv` 与 `verify_schema_enums`、`selftest_term_unify` 全部 `ALL_PASS`；`verify_scene_jsonl` `ALL_PASS = True` 且 `ALL_PASS_STRICT` 可评（其 A3 为真判 PASS）；`audit_handoff_package` 六类全 PASS（exit 0）；生成器 `--check` 幂等 PASS；六源 `scene_*.jsonl` md5 **与合并前逐一相同** ⇒ **`main` 处于可验证状态**。
  - 合并前后清理：`wt-qbicons` 内一张修正表的 **CRLF 假差异**（`git diff` 内容为空，仅换行形式）已 `git checkout --` 复原；工具目录一个 **mtime 21:33 的陈旧 `__pycache__`**（早于本 issue，无脚本 import 该模块）已删除。
