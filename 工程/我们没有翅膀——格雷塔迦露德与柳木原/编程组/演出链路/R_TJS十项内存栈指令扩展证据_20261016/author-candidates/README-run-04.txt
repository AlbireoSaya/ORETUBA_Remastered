# R_TJS 十项内存与栈指令扩展 · 阶段 README

- Issue：`ISSUE-20261011-02` ｜ 分支：`issue/ISSUE-20261011-02-original-fidelity`（main 基线 `3dea002b`）
- 阶段目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS十项内存栈指令扩展证据_20261016`
- 性质：R 原作忠实层 VM 的**指令扩展增量**，非翻译、非成品；goal 仍 active。

## 一、本批内容与装载依赖

新增十进制 **27 / 28 / 29 / 33 / 34 / 35 / 36 / 37 / 38 / 39** 共 10 条指令：10 个单指令函数 `RVMExtraMemNN`（`r_vm_mem_NN.tjs`）＋ 1 个路由 `RVMExtraMemoryStep`（`r_vm_extra_memory.tjs`），共 **11 个新生产文件**；`r_vm_step` 仅**新增 10 路路由与注释**，原 26 条代码路径保留不动。另加 1 份 micro case fixture，复用既有 `RExtraRD` / `RExtraWR` 与 `RVMF` 严格比较器。合计 13 份代码 = 12 生产（11 新 + step 改）＋ 1 fixture。

**这批文件必须与原 VM 模块、既有 6 个数值扩展模块显式一同加载**；不接游戏 startup，不产出新成品。装载后覆盖 **36 / 47**，剩余 control 8 与 division 3 共 11 条。

## 二、读序不可重排（核心约束）

顺序按 `numeric-contracts.json`，不得按普通表达式习惯重排：

- 27：指针目标减 1；28 / 29：SP-offset 指向字 ±1。
- 33：先读 `p+4` 再读 `p` 再读 slot，由 slot 所存 dest 写 literal。
- 35：先 SP / off，后 dest，再取 source 字；34：literal 写 SP-offset。
- 36：先 src pointer，再 SP / destOff，最后 src 字。
- 38：先 SP / off / dest，再 slot / ptr 字；39：先 slot / dest，再 slot 内容，最后最终字。

27 / 28 / 29 写后取新 PC **+4**，其余 **+8**。dest 可能落在 PC、SP、operand、slot 自身，因此**不得提前缓存 PC、不得多加一次 SP 读、不得丢一级 deref**；地址与值全 u32 含回绕。

## 三、原码与目标双向证据

原 R 表 `4a7f54` 中**仅本批 10 个 handler 逐项本地核对**，不声称 47 项已全核。原 EXE SHA `b26795b1…`，**仅 Unicorn 执行、不 OS 加载原 EXE / DLL**，原件与备份只读。

- 原 CPU 自构完整程序 **405 组**：以原 `4a7a30` 的有序写、PC-op、return 与最终访问字为参考；目标 `RVMRun` 32 / 64 位**各 405 例、405 段通过**。
- 原 handler 微步 **1188 组**，hook **止于 `4a7a75` 取指前**，逐 guest DWORD 读写与终值比对，双架构各 1188 通过。
- 输入为自构 program 与 microstate，**不是原剧本**；微步是受控寄存器 / 内存状态，不代表所有状态都能由普通 VM 入口构造，也不构成非法地址的穷尽证明。

## 四、回归与故障检出

- 旧 17 指令的 1390 / 1391、旧 9 指令的 1343 / 1343，双架构均回归通过。
- 真实 group0 的 242 条记录、六态冷暖，每架构 2904 次通过。**本轮未重跑 45528 全矩阵，不作为新增样本。**
- 故障：33 operand 顺序错、37 多读一次 SP、38 少一级 deref、27 写 dest 前缓存 PC，四类 × 双架构共 **8 次全部检出**；故障只改私有副本，比较器与生产候选未被改动。

## 五、范围边界与剩余工作

本批只计 **36 / 47**，约 76.6% 属 **opcode 数量比，不等于游戏进度**；micro 只覆盖新 10 个 handler 的读序，**不证明整个 `RVMRun` 入口 / guard / native 内部栈的全读序**。

仍缺：control 8（2 / 3 / 4 / 6 / 7 / 9 / 10 / 11）、division 3（16 / 17 / 18）、全 VM 读序与任意回调 / 机器帧别名、银行真实增长、ctx434 发布 / 129 dispatch、native 生命周期、全路线画音与四版 100%。`OTV` 为 MAGES Task DSL + CRI，非 Lucifen。阶段目录只保存自构输入、原 CPU 参考、候选与故障、root recipes 与 summary，**不存原游戏字节**；规范按哈希缓存，skill 追加后失效。

## 六、流程说明

12 份首轮小实现派单与 1 份克隆曾全 stop 且无 length；root 平台 patch 出现两次文本转义与模板引号解析失败，**均在写入前报错**，修正后首轮 405 / 1188 全部通过，未产生原码或目标语义差异。此类属平台工具错误，**不记为实现错误**。下一批 control 8 另行并行，未验收前不计支持 44。