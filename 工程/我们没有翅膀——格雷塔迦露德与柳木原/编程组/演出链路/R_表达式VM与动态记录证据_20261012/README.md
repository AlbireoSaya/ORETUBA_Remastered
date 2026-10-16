# R_表达式VM与动态记录证据 20261012

本目录是自建验证证据归档，不含完整原作脚本与凭据，但包含保留在本地的原码静态指令证据，不能错误说“不含机器码”；原件只在Unicorn执行。 原 ORETUBAR.EXE SHA256 为 b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33。

已验证事实：

VM 4A7A30/4A7A50。3349 个原表达式乘 6 个受控状态，共 20094 条，对照 editor 独立 lucifen_expression_reference.py；轨迹、真实回调帧、全部 1 MiB live 内存、source 自修改、PE 不变、stack 平衡全部一致。只观察 14 种 VM 操作，不宣称 47 种通用语义。

真实 callback 9/58/571 分别位于 411C40/418650/414160，控制配置 byte、module 两个 flag OR、modifier 键；真实 getter 为 47A230，active XOR1 另一 bank，key 低 8、state 高 bit、AL 与 EAX 上位存在区别。边界组包括：256 设置、50 flag/null、7680 getter、576 modifier 短路、4 未证拒绝、ctor 只到 47A390 前。

418 TOB 内 3794 条动态记录，乘 6 再乘 cold/warm，共 45528；accepted 35094、declined 10434，表达式 40188，首次 bind 20094，实际 native 7512。原 42FB50 真条件/参数执行到 42FDC2 未派发前；false 时实际原函数返回记录末端，opcode 0 反转，false 不读参数；warm 不再绑定但表达式副作用重复。全内存、source、PE、trace 一致。

129 TOB 命令表：原构造片段 42ED56 至 42F374 前，helper 4304C0，ctx+653C 指针；129/256 两种预分配容量均 129 次原 push 一致。与 809 SOB/native 编号不同，尚未证明全部 handler 语义或真实 allocator。

正式回放已完成于 临时/ISSUE-20261011-02/r-expression-vm-replay-01/，12 JSON 与候选全对象一致。完整大结果保留在上述忽略目录与 子代理工作区/ISSUE-20261011-02/r-expression-vm/；入库5验证摘要/边界JSON（native-vm-prefix-summary、native-vm-complete-summary、independent-vm-summary、dynamic-record-summary、native-and-boundary-fixtures），另tob-command-registration.json及expression-vm-instruction-evidence.json，8复跑recipe、README与root批次审查；12完整结果JSON仍在忽略目录。

复跑说明：在工作区根，先将八 recipe 中的 replay-01 改为尚不存在的新目录，仅复跑副本，历史不改；verify-prefix.txt 创建目录，再 verify-index.txt；然后 verify-native、verify-independent、verify-native-fixtures、verify-dynamic-records、verify-command-registration、verify-instructions.txt。每个执行 Get-Content -Raw -LiteralPath '<本证据目录>/verify-*.txt' | python -X utf8 -B -。环境为 Python 3.14.7，Unicorn 2.1.4 工作区工具；不自动覆盖。输入依赖已入库的先前动态绑定证据和原本地 418 TOB。

限制：本证据基于受控预分配、静态 native vector；不是完整 allocator、OS 输入生命周期、全部演出 handler、真实场景、忠实 TJS、四版全部画音。宿主 primary 前置仍失败，禁无约束 OS 启动原件。未知情况明确报错，不 noop；完整四版目标不缩小。审查与合并状态以root批次审查和Git记录为准，不永久写“审查尚未写”。