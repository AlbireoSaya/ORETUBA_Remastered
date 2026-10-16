## R_TJS 九项 VM 指令扩展证据_20261016（ISSUE-20261011-02）

本批新增 9 个 opcode（decimal 14/15/21/22/24/25/42/43/46 ＝ sub/mul/xor/not/sar/shl/signed<=/signed>/neq），目标 **17/47 → 26/47**，余 21（control 8/div 3/memory 10）。生产代码＝6 个新函数文件（`r_value_extra_arithmetic`/`bits`/`compare`/`mul`、`r_vm_extra_operands`/`value`）＋ `r_vm_step` 新增路由，另 2 个 microfixture；落 `编程组/原作忠实层/R`，**6 个新文件须与原 VM 模块显式一同加载，不自动接 startup**。

语义：u32 位宽；shift 取 count 低 5 位；sar 先 s32；mul 用四个 16 位 limb 只算低 32。Operand 读序 op15＝b→dest→a，21＝b→a→dest，22＝a→dest，其余 a→b→dest；写 dest 后重读 `ctx+8` 再加 8/12，不得提前缓存 PC。原 R47 表 `4a7f54` 中本批 9 项逐 handler 已核对；不声称本轮全部 47 项已核；原 EXE SHA `b26795b1…`，仅 Unicorn、不 OS 加载，原件／备份只读，不外发。

验证：1343 个完整 VM 用例在真实原 `4a7a30` 运行，原 CPU 有序写／PC op／return／终值比对，目标 `global.RVMRun` 双架构各 1343/1343 通过（非 stub）；216 个原 handler 微步（ESI ctx／EDI operand p／EBP4／EBX12，hook `4a7a75` 取指前）双架构各 216 通过。旧 1390/1391 双架构回归通过；真实源 group0 的 242 条动态记录六态冷暖，每架构 2904 次（118574 caller／35520 VM 写／9552 步／2556 VM／480 native）通过——旧 45528 全矩阵未重跑，不冒作新覆盖。三类故障（乘法 operand 读序换位、shift 取低 6 位、先缓存 PC 再写 dest）×双架构 6 次全检出。**微步仅覆盖新 9 handler，不代表整个 `RVMRun` 读序完全匹配。**

边界：余 21 VM、全读序／回调与任意帧别名、银行增长、ctx434／129 dispatch、native 生命周期、全部路线画音、四版 100% 均未完；OTV＝MAGES Task DSL＋CRI，非 Lucifen；无新成品，goal 仍 active。阶段目录 `工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS九项VM指令扩展证据_20261016`；下一步余 21 按 control8／div3／memory10 分小批并行，先原 CPU 证据后真实运行器，阶段批审。