## R_TJS 十项内存栈指令扩展证据_20261016

- 新增 memory/stack 10 opcode（27/28/29/33–39），目标 **26/47 → 36/47**，余 control 8（2/3/4/6/7/9/10/11）＋ division 3（16/17/18）共 11。
- 生产代码＝10 单指令函数（`r_vm_mem_27..39.tjs`）＋ router（`r_vm_extra_memory.tjs`），`r_vm_step` 仅加 10 路与注释，原 26 条路径保留；11 新文件须与原 VM 及既有 6 数值扩展显式同载，不接 startup、无新成品。合计 12 生产＋1 micro fixture。
- 语义顺序不可重排：27 指针目标−1；28/29 SP-offset 字 ±1；33 经 slot 所存 dest 写 literal；34 literal 写 SP-offset；35 stack 字→dest；36 间接 src 字→stack 槽；37 stack 槽复制（SP 只读一次）；38 slot 所存 ptr 再读 value；39 两级间接。u32 地址/值/回绕；27–29 写后 PC fresh+4，其余 +8；dest 可为 PC/SP/operand/slot，不得提前缓存 PC、多读 SP 或丢一级 deref。
- 验证：原 CPU 自构完整程序 **405 组**（`4a7a30` 有序写／PC-op／return／终值），目标 `RVMRun` 32/64 各 405 例通过；原 handler 微步 **1188 组**（hook 止 `4a7a75` 取指前），两架构各 1188 通过；含 0/1/7fffffff/80000000/ffffffff、非对齐、自别名、dest=ctxPC/SP、SP0 与 offset 回绕。
- 回归：旧 17 的 1390/1391、旧 9 的 1343/1343 双架构通过；真实 group0 242 记录六态冷暖每架构 2904 次通过；**未重跑 45528 全矩阵，不计新增样本**。
- 故障：四类（33 operand 序、37 多读 SP、38 少一级 deref、27 写 dest 前缓存 PC）×双架构 **8 次全检出**。
- 边界：micro 仅新 10 handler 读序，**不证明整个 `RVMRun` 入口/guard/native 栈全读序**，亦非非法地址或全状态可构造之证。仍缺 control8／division3、全 VM 读序与任意回调/机器帧别名、银行真实增长、ctx434／129 dispatch、native 生命周期、**全路线画音**及四版 100%；**OTV＝MAGES Task DSL＋CRI，非 Lucifen**，36/47 仅为 opcode 数非游戏进度。
- 证据：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS十项内存栈指令扩展证据_20261016`；原 EXE SHA `b26795b1…`，仅 Unicorn、原件只读、不外发。