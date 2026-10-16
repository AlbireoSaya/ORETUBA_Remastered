## 2026-10-11 增量：TOB 动态绑定与无损 IR
R418 TOB 扫描 218615 条记录，59367 条未分类孤岛，3349 条表达式，结构错误 0。
430090 原始绑定函数处理 5 组 variable/native/temp/string/local，6698 例受控 bank 绑定；890 数组条件验证至 42FC44 前，1725 数组参数执行 42FCEC→42FD42 有界块。
42FB50→4A7A30 首表达式入口 2904 条记录，cold/warm 11616 例；原版标志 0→1 时运行时绑定一次、预热跳过；全 VM 未执行。
IR 子代理工作区/ISSUE-20261011-02/r-tob-lossless-ir-02/：418 项字节精确重建 9538168 字节，raw+typed 部分语义未定。
证据位于 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB动态绑定与无损IR证据_20261011/，已完成 root batch review。
工具 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/lucifen_tob_dynamic_structure.py、lucifen_tob_binding_reference.py，editor 作者。
缺失 native callbacks、表达式 VM、完整 handlers、跨模块、全部 4 IR、忠实 TJS、全路线帧与音频；目标仍 active。
实际 bank 分配与全局默认值均未证明。