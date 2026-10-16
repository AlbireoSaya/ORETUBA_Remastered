# R_TJS完整实时记录与条件证据_20261016 阶段 README

- 日期 / Issue：2026-10-16 ｜ `ISSUE-20261011-02` ｜ 分支 `issue/ISSUE-20261011-02-original-fidelity` ｜ main 基线 `bffa02420a267cac67057be9d2efa9efc2cff30d`
- 目标工程：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/原作忠实层/R`
- 证据阶段：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS完整实时记录与条件证据_20261016`
- 分工：editor-easy high 实现；root 研判、原码验证、平台装配、批次审查、Git 行政。

## 一、本阶段交付

新增 4 个生产 TJS：`r_live_array_value`、`r_live_condition`、`r_live_record_gate`、`r_live_record`。旧 3 个 `payload`、`item`、`parameters` 追加可选 `arrayValue = void`，未传时保持旧调用默认行为。另修 `r_vm_control` 的 op30，Python 工具 `lucifen_inline_vm_reference` 同步修正。配套 13 个 fixture。

## 二、SDK 接口与依赖

- 依赖真实 `runVM` / `global.RVMRun` 签名；透明 adapter 只记录并再委托，不是 stub，native / bank 不支持时显式抛。
- 数组读取必须先 `rd global5355f0` 再取 bank index，并依赖 `ensureBank(desc, bank)` 返回 vector；只支持既存 bank，增长未实现且显式抛。
- 旧 `resolveBank` 返回 entry，不能满足“先 element index，再 `rd vector + bank*12`，再 `rd base + element*4`”的完整顺序，故新增可选 `arrayValue` 回调。
- 临时 cell 按观测准备；除此以外源、heap、VM ctx、SP 连续保留。

## 三、关键顺序

条件 tag 语义如下：

| tag | 行为 |
| --- | --- |
| 0 | 即时 DWORD 常量 |
| 1 | 常 1，不读 payload |
| 2 | 数组 |
| 3 | 绑定 / 真实 VM / 后置取结果 |

保存入口 opcode；opcode 0 反相。表达式修改源 opcode 只影响下一次记录。假分支只读 length 并按 u32 推进，不读 `ctx434`、count、items；真分支先 `rd(ctx+434)` 再 `rb(count)`，不读 length。即使 count 为 0 仍 `rd ctx434`，但不解引用 param_base，故允许 poison param pointer。next 不是简单 length，而是实时读取推进。

phase 编排：首次 pre，VM 期间 vm（不比 VM 读取），之后 post；次表达式绑定不重置 pre。

## 四、opcode30 修复

旧 VM op30 在零条件下漏掉中间 PC 写。原码 `4a7d4d` 先 `wr(ctx+8, p+4)`，`4a7d52` 再 `wr(ctx+8, rd(p+4))`；非零路径照旧。TJS 与 Python 参考均修。

新增重新生成的 1390 自主合成 VM 用例、1391 段；加入原 CPU 有序写 hook，逐条确认原码写序及旧有全内存 / trace / return。32/64 各 1390/1391 通过。旧 1390 数据存在 branch0 预期遗漏，保留历史不覆盖；新集替代相关写序预期，此前原码全内存 / trace 结论不变。

## 五、原码与目标证据

原 `42FB50` 只在 Unicorn 执行，备份 EXE SHA 为 `b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`；原件只读，不 OS 装载 EXE / DLL，原作 PE、剧本、素材未外发。

原码取得 45 组自主合成、88 次连续记录的参考：1703 条限定 caller pre/post 读写、525 条有序 VM 写、133 条 `[runIndex, PC, op]`、60 次 VM 运行与返回、4 次真实原 native `411c40` 只读查询 frame。目标 32/64 各全部通过，逐 source 512 字节、写 DWORD、condition / opcode / accepted / next / paramend / count、binding / nativeframe 精确比较。这是合成证据，不能替代正文。

## 六、故障与回归

五类故障 × 双架构共 10 次全检出：ctx / count 倒序、假分支读 ctx、array element / entry 倒序、表达式后重读 opcode、漏中间 PC 写。故障注入全部在私有副本，生产候选未受影响；第五类会故意修改私有 VM helper，不能说所有故障连私有 VM 都不改。

回归：旧 11 liveparam / 91 scoped 事件双架构通过；旧 18 组 33 liveeval / 735 caller / 248 writes / 62 trace 双架构通过。

## 七、限制与下一步

仍只支持 17/47 opcode，本轮组合覆盖全部已支持 17 种，不等于 47 全实现。完整实时记录只到 ctx434 发布 / 129 dispatch 之前；VM 访存读序和 native 内部栈不比；heap / PE 快照仅写覆盖核查；临时 cell 不代表任意机器帧别名建模。

未完成：真实银行增长、native 生命周期、inline live 头、剩余 30 VM、全路线画音、四版 100%。OTV 为 MAGES Task DSL + CRI，非 Lucifen。无新成品，不改游戏 startup。

下一步：扩大 3794 真实动态记录原字节覆盖，与余下 VM / native / 演出接口并行；合成例不能替代正文。goal 保持 active。