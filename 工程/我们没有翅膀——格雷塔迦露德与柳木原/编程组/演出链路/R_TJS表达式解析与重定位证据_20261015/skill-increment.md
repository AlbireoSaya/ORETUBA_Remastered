## R_TJS表达式解析与重定位证据_20261015（ISSUE-20261011-02）
- 11 个新生产模块落 `编程组/原作忠实层/R`：`r_expr_read/header/relocations`、`r_parse_expression`、`r_inline_expr_header/relocations`、`r_parse_inline_expression`、`r_relocation_pair/writes`、`r_record_value/arguments.tjs`。
- 两格式必须分开：参数 3349＝长度/size u16 ＋ count u8；inline 990＝`[s` 两 byte 标记后长度/size/count u32（`+` 不属于魔数）；保留 flag、顺序、重复／未对齐 reloc。
- 银行 0/1/2 group、3 字符串 base+index、4 codebase+index；u32 地址与 value；未知 bank 不猜、明确 throw。
- 覆盖：4339 源表达式重解析对旧 metadata；每表达式 2 状态、真 Unicorn 调原 430090 全 8678；16 个真 tvpwin32/64 并行约 8s 全过，每架构 4339 parsechecks＋8678 relocationplans。
- 178 synthetic checks 每架构通过（126 拒绝／48 recordprimitivecase／4 其他 positive）＋2 合成 relocation plans；record-value 六 kind 与 record-arguments opcode0 反转对 Python reference；expression 回调仅 fixture 返回值，非整合 TJS VM，本批未重跑原 42FB50。
- 故意错基址与条件反转两份注入均已检出；原件/脚本/IR 完整性复验不变，限本期范围。
- 限制：纯 relocation-write 计划尚未实际写回、不执行 flag 0→1／lazy cache，非完整绑定运行器；未串接 129 命令派发／native 生命周期／画音／四版 100%；原 PE 仅 Unicorn 不 OS load；OTV＝MAGES Task DSL+CRI 非 Lucifen；无新成品、无其他 Windows 版本验证。
