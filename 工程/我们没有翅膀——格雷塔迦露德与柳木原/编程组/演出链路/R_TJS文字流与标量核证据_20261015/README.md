# R_TJS文字流与标量核证据_20261015

本阶段交付 2 个真实目标模块与 5 个验证文件，共 7 个文件；其中**只有 2 个 TJS 目标模块与 1 个 TJS 校验器在真实 krkrz TJS2 解释器（tvpwin32 / tvpwin64）上执行**，另外 **4 个 Python 助手在 Python 中执行并生成校验数据**，并非 7 个文件全部由 TJS 解释。只涉及自有 SDK 源码与自有派生元数据，原件只读、未 Git、未回退他人改动。

## 目标模块（2，相对「编程组/」）

- `原作忠实层/R/r_u32.tjs`：RValueOp 仅接受 ops 13/19/20/23/41/44/45，严格 TJSInteger、u32mask 与 signed32 比较，未知操作一律抛异常；它不是完整表达式 VM。
- `原作忠实层/R/r_literal_run.tjs`：RLiteralRun 只按首 byte 分 1/2，lead 81..9F / E0..FC 的第二 byte 允许 00/5B；首 byte 00/5B 即停且不消费；不含 Unicode 解码、绘制与标签语义。

## 验证文件（5）

- 本证据目录的 `r_byteflow_verify.tjs`：真实 TJS 校验器，回调以显式 incontextof 字典（quoted keys）绑定，`Octet.length` / `Array.count` 可用。
- 只读向量助手四支（`编程组/工具/`）：`r_tjs_numeric_vectors.py`、`r_tjs_case_lines.py`、`r_tjs_ir_payload.py`、`r_tjs_ir_parts.py`，只产出与逐条比对，不写原件。

## 真实解释器结果

- 向量合计 1830：1378 算术边界/随机 reference 向量 + 434 原码字符单元 fixtures + 7 补充 literal + 11 非法/未知拒绝；32 位与 64 位各自 1830 全过。
- 8 个真实解释器（2 架构 × 4 组）并行约 8 秒全过：每架构 59367 checks，逐 unit 校验绝对偏移与 width、逐 payload byte/end/stop 精确相等，而非只比 checksum；8 个新鲜 nonce、日志与 process exit 0、job cleanup 均通过。
- 全源文字切分对账：418 TOB / 9,538,168 原 bytes / 59,367 个结构 island；island 合计 4,118,728 bytes、payload 3,904,210 bytes、1,952,105 units，marker 990 / nul 418 / limit 57959；464 个本地 Octet batch 合计 16,995,242 bytes。
- 原 CPU 42F880 / 42FB00 的完整 59367 行 native 轨迹（SHA d76de631…f35e06）已核实，本次每文件 sourceSHA、island 起止、consumed end、bytes、units、stop、payloadSHA 逐条一致；本轮未重跑原 PE，明确复用旧有原码证据。

## 负控

- 10 个 Python guard 负例通过；两个故意破坏「加法」与「81 lead」的临时 TJS copy 被实际检出差异，engine 均 exit 0 但 verdict = false，说明不以进程 0 当通过。
- probe01 因 unquoted 字典 key 导致 Octet 转 string 报错，已修，错误 fixture 保留。
- 3 个过大 reader/generator 因 length 无产物，已拆成小 pure 函数，high 档不变。

## 数据路径

本证据目录平铺：`source-runtime-summary.json`、`source-vector-generation.json`、`original-native-reconciliation.json`、`negative-controls.json`、`synthetic-generation.json`、`tjs-synthetic-32/64-verdict.json`、`tjs-source-32/64-group0..3-verdict.json`、`root-source-integrity.json`、`candidate-provenance.json`、`verify-target-runtime.txt`、`verify-source-target-vectors.txt`、`verify-target-faults.txt` 及输入 data manifests。完整 raw 日志与原文 Octet 仅在 ignored 临时目录存路径与 SHA，不复制进库；不把本证据目录称为 standalone 游戏。

## 未覆盖与下一有限路径

- 未覆盖：本批不执行 218615 条 TOB command，不运行 990 表达式 body 或 3349 参数 expr，不等于覆盖所有 island 语义；不负责可达性、分支、全剧本、原窗口、字形、语音、音乐、完整画音与四版 100%。TJS 仅当前 Win 环境 32/64 解释器测试，Win7 / Win10 未测；OTV 的 MAGES Task DSL + CRI 非 Lucifen。本批无新成品。
- 下一有限路径：把已原码验证的 VM memory / control / yield PC / SP 续行移入 TJS，对 native 请求与未支持生命周期明确拒绝，再接逐指令源映射与原剧情画音；不以空 stub / noop 代替。