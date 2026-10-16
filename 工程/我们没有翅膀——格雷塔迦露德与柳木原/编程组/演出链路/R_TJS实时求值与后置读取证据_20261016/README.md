# R 实时求值与后置读取（2026-10-16）

本批在 `编程组/原作忠实层/R` 新增两个生产 TJS：`r_live_expression_result.tjs`、`r_live_expression_evaluate.tjs`，另 9 个 fixture。证据目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS实时求值与后置读取证据_20261016`。

Evaluate 依赖真实 runVM 签名与 `RVMRun` 一致；本批仅在未改动的 `global.RVMRun` 外套一层透明 adapter，记录后原样委托，不是 stub。native/bank 不支持时显式抛出，真实 native 生命周期未验证。结果函数必须在 VM 之后按 `global5355e8 → RH(table) → rd(desc+4) → rd(vector) → rd(resultPtr)` 顺序读取，`next = (table + (size & 0xffff)) & 0xffffffff`。

已通过：原 18 组合成输入连续运行 33 次；双架构各 18 组 33 记录、735 条 caller 前后事件、248 条有序 VM 写、62 条 PC/op 及 VM 返回码、512 source 最终字节与已写 words、游标，全部一致。须分清：735 是调用者事件，248 是 VM 写，trace 为 62 条 PC/op；VM 读与 native 内部栈本批未参与比较，故不得称全部 CPU 访问一致。原 heap / guest PE 快照仅核查写覆盖，不是独立语义 oracle。

边界：暂停返回 1 仍取结果；compiled 暖态不等于 VM resume——每次 runVM 的最后一个实参为 false，进入真实 VM 时重新压零；VM 清 flag 时第二次仍冷绑定。VM 可改 size、global、`descriptor+4`、`vector[0]`，后续必须重新读取；改原 code length 也不能重解析 header。真实 VM 改下一 item tag 后按新 tag 解码，第二参数字 `0xaa443322`。

本批用 opcode 0/1/26/31/32/40，底层仍为 17/47 子集，未扩 opcode 覆盖。准备阶段每段只重设原 native 临时游标 cell 初值，guest VM ctx/SP 与脚本、全局状态跨段保留，不重置造暖态。

当前仅覆盖 TOB 参数 u16 格式；尚未完成 inline live 头、条件表达式组合、银行真实增长、ctx434/129 dispatch、完整画音、四版 100%；OTV 非 Lucifen。四类故障在双架构共八次全部检出，详情见 `root-review.json`。

不改 startup 与成品；原件只读，原码仅 Unicorn 执行、不 OS 加载；原脚本 / PE / 素材不外发。