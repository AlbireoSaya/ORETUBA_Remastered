# R_TJS表达式VM与暂停恢复证据_20261015

日期：2026-10-15

已实现：6 生产核 `r_vm_entry/memory/control/value/step/run.tjs` 位于 `编程组/原作忠实层/R`，复用已提交 `r_u32.tjs`；13 TJS fixture 在本证据目录，5 Python 辅助 `r_vm_shadow_range/read/write`、`r_vm_access_log`、`r_vm_tjs_literal.py` 位于 `编程组/工具`。
原 VM 有 47 opcode；目标仅 17：0,1,5,8,12,13,19,20,23,26,30,31,32,40,41,44,45；未知 throw。
cold 写入口/压 0；warm 不重置 PC/SP；opcode 0 保留 fetch 后 PC 暂停。
callback 读写 guest 逻辑地址，非 host 指针；maxSteps 只是验证守卫，非游戏 limit。
验证：3349 参数 expr + 990 inline 共 4339×6 states=26034 cases、672 resume，26706 segments 每架构；真实 `tvpwin32/64` 全部通过，各 494442 有序写事件，逐 PC/op trace、native 帧、observedwords、PC/SP、返回精确比较。
原全内存 hash 与原 CPU 旧 oracle 逐条 reconcile；本批源 cases 新跑原 430090 binder，未新跑全部 sourceVM，不冒称新原 CPU 运行；旧 original oracle hashes anchored 提交 `root-replay-comparison.json`。
另 1390 合成 cases/1391 segments 本批确实在 Unicorn 运行原 4A7A30/50 VM 并比全 live/source/PE 字节，两 TJS 架构也过。
14 guard 两架构通过；两故意错实现 warm 重新入栈/错误 increment 均被检出，engine exit0 而 verdict false。
最初 fixture 字典/typeof 错误已修；unicode probe 错用 JS charCodeAt 属 root 配方错误，TJS 用 `#(charAt)`；TJS 不认 JSON `\u`，encoder 改 `\xHHHH`；NUL 必须显式拒绝，不悄悄丢；472265 既有 ASCII 字符串 token 新 encoder byte exact。
Unicode 最终 32/64 各 14 项（10 字符串+4 Integer64 极值）通过，Python 9 拒绝场景通过。
依赖：本地原 IR 与旧 oracle、便携引擎，非 standalone。
入口：`source-runtime-summary.json`、`receipts/`、`reference-provenance.json`、`root-audit.json`、`phase-manifest.json`。
复跑参数：target-runtime bits tag manifest [timeout<=60]；source-vectors kind group groups outputdir [limit]。
限制：5 native fixture 仅 flags/固定 keyboardstates/querylist/invalidchannel/controlcopy，非 production；valid channel 显式拒绝，无真实 audio cleanup。
controlcopy 仅原全局 5355C0=2 和零终止 260byte guard，不执行 SOB/scenecontroller；260/12288 都是 fixture guard 非游戏 limit；resume 未运行外部 controller；稀疏 fixture memory 非正式 loader/allocator。
62,074,836 bytes source fixture 留 ignored 临时，不 Git 不外发，不含剧本/游戏/PE 外发；原 PE 只 Unicorn 不 OS load。
本期无视觉/音频/完整 TOB/命令调度/存档/原 window 前台/四版 100% 结论，无新成品；OTV 是 MAGES Task DSL+CRI 非 Lucifen。
下一步：binder/relocation 连接及其余 opcode 按独立小模块并行，再接真实 native/TOB 执行/演出画音；不降低目标。