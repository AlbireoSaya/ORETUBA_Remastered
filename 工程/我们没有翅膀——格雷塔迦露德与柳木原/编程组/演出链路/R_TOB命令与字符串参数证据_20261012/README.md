R TOB命令表、全源使用与字符串参数边界（2026-10-12）

本README记录当前已验证事实。129个原TOB槽对应102个不同handler；418 TOB的218615条记录全部编号可对账，无未知编号，但4118728字节孤岛语义未定。静态handler为2576行、146条直接边、11个间接缺口；向下direct graph覆盖684函数、54842行、1004个间接缺口。0解码诊断不代表完成。

工具lucifen_tob_command_census.py由editor提供，root依据原码验证。命令25原址43FDA0，两个字符串位于ctx+64D1、+64E2，长度17、16且含终止；IAT518188由原PE描述符确认为lstrcpynA。35472条原record全部经42FB50真实解析、真实调度、真实handler，在首次import call前于43FDC0或43FDDC停止；涉及409个源文件。形状为inline/inline 21118、inline/empty 14054、empty/inline 300。已检查全部参数word、真实首次复制调用参数、empty首项清零及边界、source、PE不变。未执行或伪造lstrcpynA，因此不证明完整handler、truncation或OS调用。43F7F0消费双字段并交444740写目标+3B8、+3C9，且清空原字段；此为静态推断，不称其为语音名或说话人名，须查真实消费链。

候选产物在子代理工作区/ISSUE-20261011-02/r-tob-command-audit-01/；正式产物在临时/ISSUE-20261011-02/r-tob-command-audit-replay-01/，三项正式回放已退出0，七份完整JSON与候选全对象一致。大census、完整指令、35472结果保持忽略目录；入库JSON摘要、directgraph、消费者、IAT边界、三recipe、工具与README。复跑顺序：verify-command-census.txt创建新目录，再verify-command-graph.txt，再verify-source-command25.txt；根目录运行Get-Content -Raw -LiteralPath '<证据>/verify-*.txt' | python -X utf8 -B -，改副本的新输出路径，不改历史。

受控预分配，不证明全生命周期、真实allocator、未知handler、完整画音、忠实TJS或四版全还原。宿主primary仍失败，禁止无约束OS启动原件。审查与正式回放状态以root凭据为准，完整目标不变。

行政归档：本目录为已审证据；API的17/16长度是否含终止符另由[Microsoft lstrcpynA文档](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrcpyna)核对，文档不能替代未执行的原系统复制调用。
