editor-easy 技术文档 README
============================

范围：R 418 TOB 无损 IR 与绑定结构解析。仅陈述既有事实。

结构解析
- R 418 TOB：218615 records，59367 unclassified islands，3349 expressions 结构化解析，errors 0。
- 原码 430090，覆盖全部 5 个 binding groups，6698 two-state cases。
- group 0 variable array ptr；1 native ptr；2 temp array ptr；3 string base+index；4 expr base+index。
- 另有 15 synthetic groups。

动态结构
- Original 42FB50 → first 4A7A30 entry：cold/warm 11616 cases，跨 2904 records；flag 0->1 仅绑定一次，cached skip bind；VM 未运行。
- Array conditions 890×2=1780，op0 invert；array items 1725×2=3450，仅 interior 42FCEC→42FD42 block。
- 全部 preallocated banks，无实际 allocation/default global values。

产物与工具
- 子代理工作区/ISSUE-20261011-02/r-tob-lossless-ir-02/：418 compressed JSON，9538168 original bytes，9071136 gzip bytes。
- original raw base64；418 全部 byte-exact reconstructed。
- unresolved semantics expr/native/full 仍为 goal active。
- 工具 lucifen_tob_dynamic_structure.py、lucifen_tob_binding_reference.py 由 editor 编写；root original code verification/batch review。
- Static 5 entries，307 instructions、9 direct edges、1 indirect gap、0 diagnostics。

回放与修正
- Formal replay 临时/ISSUE-20261011-02/r-tob-dynamic-replay-01/；8 verify*.txt recipes 顺序 structure first，再 binding、lazy-caller、variables、helper、ir-emit、ir-independent、instructions；原码有界调用已执行，未通过 OS 启动原游戏。
- IR01 metadata hash naming/implicit gzip mode 由 editor 在 new 02 修正，never overwrite。
- Bridge length failed outputs 不是 deliveries；slim function dispatch stop。

下一步
- 下一步实际 expression VM + native slots 9/58/571（static candidates），未达完整 TJS fidelity。边界保持简洁。