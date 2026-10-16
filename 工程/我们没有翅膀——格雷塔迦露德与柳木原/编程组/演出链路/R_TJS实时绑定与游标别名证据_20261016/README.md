# R 实时绑定与游标别名（2026-10-16）

## 路径

- 部署：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/原作忠实层/R`
- 证据：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS实时绑定与游标别名证据_20261016`

## 本批模块

新增 6 个生产 TJS：`r_live_relocation_count`、`r_live_relocation_row`、`r_live_relocations`、`r_live_relocation_value`、`r_live_expression_header`、`r_live_expression_bind`；另附 7 个 fixture。

## 接口顺序（依原码实测）

重定位：先读组 count，再写 cursor cell；逐行顺序为「读 slot → 写 cursor → 读 index → 写 cursor → resolve → 写回」，下一项与下一组即时重读。表达式参数：最小头只读 u16 长度以推 code/flag/table；冷态先写 flag=1 再绑定，暖态非 0 不碰 table 与 cursor，flag=2 亦按暖处理；冷态 table size 为 0 仍绑定。存在重定位再次清 flag 的情形，故最终 flag 不保证为 1。mode 只取低 8 位，测 0/1/256/65537；重复、未对齐、u32 回绕，以及修改后续 index/count/cursor 与全局字符串 base 的写法均保留；group3 每次读 guest `5355e4`。

## 有限证据

新增原码 23 例（16 例直调 `430090`，7 例在 `42FB50`→`42FD75`、进入 VM 前停止），共 739 条限定读写。目标 32/64 位各 23 例、739 事件，512 源最终字节与全部已写 DWORD、游标逐项一致；exit 0、nonce、cleanup 通过。三类故障（先写游标后读 count、晚写读 index 前游标、错误缓存字符串 base）× 两架构共 6 次全部检出，属检查器证据，非游戏失败。

## 边界（未完成）

无 VM，亦无 VM 后 size 推进；银行仅为合法既存 vector fixture，真实增长未实现。原客体 heap 与 guest PE 快照对照仅作写覆盖核查，非独立语义 oracle；目标是比对原 CPU 事件，非完整目标镜像哈希。内部 native 调用栈与参数帧的任意别名改写未建模（compact/codeBase 按值），全部可能别名与非法输入未证。原件只读、只经 Unicorn 不经 OS 加载，不改 startup 与成品。live VM、VM 后 size、inline live 头、ctx434、129 dispatch、正文画音及四版 100% 仍未完成；OTV 非 Lucifen。