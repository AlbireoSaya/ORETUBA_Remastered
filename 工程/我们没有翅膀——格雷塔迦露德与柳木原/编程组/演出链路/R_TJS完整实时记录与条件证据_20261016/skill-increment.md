## 2026-10-16 完整实时记录与条件（ISSUE-20261011-02）

阶段证据：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS完整实时记录与条件证据_20261016`；目标工程 `编程组/原作忠实层/R`。

本批新增 4 个生产 TJS：`r_live_array_value` / `r_live_condition` / `r_live_record_gate` / `r_live_record`；旧 3 个 API（payload / item / parameters）追加**可选** `arrayValue=void` 回调，旧调用默认行为不变。条件 tag：0＝即时 DWORD 常量、1＝常 1 不读 payload、2＝数组、3＝绑定/真实 VM/后置取结果；保存入口 opcode，opcode 0 反相；假分支只读 length 并 u32 推进，真分支先 `rd(ctx+434)` 再 `rb(count)`。数组先 `rd global5355f0` 再 bank index，依赖 `ensureBank`；**银行增长未实现、显式抛**。

**op30 修复**：`r_vm_control` 的 op30 原漏中间 PC 写（原码 `4a7d4d` 先 `wr(ctx+8,p+4)`，`4a7d52` 再 `wr(ctx+8,rd(p+4))`，非零路径照旧）；TJS 与 Python 工具 `lucifen_inline_vm_reference` 同修，并重新生成 1390 自主合成 VM 用例 / 1391 段，经原 CPU 逐条写序核查，目标 32/64 位均通过。

**规模与结果**：原 45 组自主合成、88 次连续记录（每架构），1703 条限定 caller pre/post 读写、525 条有序 VM 写、133 条 `[runIndex,PC,op]`、60 次 VM 运行与返回、4 次原 native `411c40` 只读查询 frame；32/64 各全部通过。旧 11 liveparam/91 scoped 与 18 组 33 liveeval/735 caller/248 writes/62 trace 回归通过。五类故障 × 双架构共 10 次全检出。

**主要限制**：仅 17/47 opcode（本轮覆盖全部已支持 17 种，不等于 47 全实现）；记录止于 ctx434 发布 / 129 dispatch 之前；VM 访存读序与 native 内部栈不比；heap/PE 快照仅作写覆盖核查；临时 cell 不代表任意机器帧别名建模；无真实银行增长、native 生命周期、inline live 头、全路线画音与四版 100%。**OTV 为 MAGES Task DSL + CRI，非 Lucifen**。原件只读，原 PE/DLL 仅 Unicorn 执行，不 OS 装载。