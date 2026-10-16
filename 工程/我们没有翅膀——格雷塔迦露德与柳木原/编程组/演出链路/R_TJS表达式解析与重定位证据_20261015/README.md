# R_TJS 表达式解析与重定位证据_20261015

入口：本目录 `source-runtime-summary.json`、`receipts/`、`reference-provenance.json`、`root-audit.json`、`phase-manifest.json`。生产模块十一个落 `编程组/原作忠实层/R/`：`r_expr_read`、`r_expr_header`、`r_expr_relocations`、`r_parse_expression`、`r_inline_expr_header`、`r_inline_expr_relocations`、`r_parse_inline_expression`、`r_relocation_pair`、`r_relocation_writes`、`r_record_value`、`r_record_arguments.tjs`。

两种表达式格式严格分开。参数 3349：长度/size 为 u16、count 为 u8；inline 990：`[s` 两 byte 标记后长度/size/count 均为 u32（`+` 不属于魔数）。保留 flag、顺序、重复与未对齐 relocation。bank 覆盖 group 0/1/2、3 为字符串 base+index、4 为 code base+index，地址与 value 按 u32；未知 bank 一律拒绝，不猜。TJS 侧一律纯回调与数据，`throw new Exception` 处理非法输入，不用 OS/UI/IO。

范围：4339 条 source 表达式由 Python 重新解析并与旧 metadata 对拍。每条表达式取两状态，在真实 Unicorn 内调用原 `0x430090` 全 8678 次，逐有序 write、full source、live bytes 与 PE 无写核对，非复用旧原 VM 结论。受控 bank 为预分配，不证明 allocator 行为。

并行：8 个生成任务并行，最长 15.64 秒。随后 16 个真实 `tvpwin32`/`tvpwin64` 并行约 8 秒全部通过，每架构 4339 parse checks 与 8678 relocation plans，各字段、relocations 与每条计划 write 精确比较。JSON 回执的 case/check 与 segment/plan 兼容槽已注明，plan 不是 VM 执行段。

合成：178 条 synthetic checks 每架构通过，含 126 条拒绝、48 条 record primitive case、4 条其他 positive，另有 2 份合成 relocation plan。record-value 六 kind、record-arguments opcode 0 反转、false 不评参数、真实 callback 事件顺序均与自有 Python reference 对齐。expression 回调只返回 fixture 值，不是整合 TJS VM，本期也未重跑原 `0x42FB50`；旧 45528 dynamic record case 不得冒充本批通过。

复跑：`verify-source-bind-vectors.txt` 参数 `kind group groups out [limit]`；`verify-bind-runtime.txt` 参数 `bits tag manifest [timeout<=60]`；`verify-bind-synthetic.txt` 参数 `out`；`verify-bind-faults.txt` 参数 `bits tag manifest timeout mutation`。

限制：当前纯 relocation-write 计划尚未实际写回，不执行 flag 0→1 与 lazy cache，绑定运行器仍不完整，解析、flag、banks、VM 与记录参数尚未串成正式 runtime；129 command 派发、真实 native 生命周期、全部画音与四版 100% 均未完成。原 PE 仅经 Unicorn，不经 OS 加载；源 bytes 与 Octet local 均 ignored，不入库不外发；无新成品，无其他 Windows 版本验证。OTV 为 MAGES Task DSL+CRI，非 Lucifen。两处故障注入已由 root 核实：故意错 group4 基址 32 bit 检出 synthetic-bind-order，故意错 opcode0 反转 64 bit 检出 RECORD_CONDITION；两者 engine exit 0 且 verdict false / cleanup true。源 1EXE 8LPK 3DLL 2refs 446SCRIPT 418IR 与 111 byte USER.CFG 未变。

下一步：按证据并行实现 lazy binder 与内存写入，并与现有 VM、record argument 串接；随后用原 `0x42FB50` 受控原码重跑对照。目标不缩小。
