## R_TJS表达式VM与暂停恢复证据_20261015
- 6 生产核 `r_vm_entry/memory/control/value/step/run.tjs`（`编程组/原作忠实层/R`，复用已提交 `r_u32.tjs`）；13 个 TJS fixture 在本证据目录，5 个 Python 辅助 `r_vm_shadow_range/read/write`、`r_vm_access_log`、`r_vm_tjs_literal.py` 在 `编程组/工具`。
- 原 VM 47 opcode，目标仅 17：0,1,5,8,12,13,19,20,23,26,30,31,32,40,41,44,45；未知操作 throw；cold 写入口/压 0，warm 不重置 PC/SP，opcode 0 保留 fetch 后 PC 暂停。
- callback 读写 guest 逻辑地址而非 host 指针；maxSteps 只是验证守卫，不是游戏 limit。
- 3349 参数 expr + 990 inline 共 4339 × 6 states = 26034 cases、672 resume、26706 segments 每架构；真实 tvpwin32/64 全部通过，各 494442 有序写事件，逐 PC/op trace、native 帧、observed words、PC/SP 与返回精确比较。
- 原全内存 hash 与旧原 CPU oracle 逐条 reconcile，旧 oracle hashes anchored 于 `root-replay-comparison.json`；本批源 cases 新跑原 430090 binder，未新跑全部 source VM。
- 另 1390 合成 cases/1391 segments 本批确实在 Unicorn 运行原 4A7A30/50 VM，比全 live/source/PE 字节，两 TJS 架构同过。
- 14 guard 两架构通过；两个故意错实现（warm 重新入栈、错误 increment）均被检出，engine exit0 而 verdict false。
- 5 个 native fixture 仅 flags/固定 keyboard states/query list/invalid channel/control copy，非真实 lifecycle（valid channel 显式拒绝、无真实 audio cleanup，不执行 SOB/scene controller）；四版 100% 未完，OTV 是 MAGES Task DSL+CRI 非 Lucifen；下一步 binder/relocation 连接及其余 opcode 按独立小模块并行，再接真实 native/TOB 执行与演出画音。
