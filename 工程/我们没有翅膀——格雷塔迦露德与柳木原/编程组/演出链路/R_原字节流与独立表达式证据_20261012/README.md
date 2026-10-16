# R原字节流与独立表达式（2026-10-12）

阶段README：本阶段记录r-literal-run与inline expression候选核验。角色editor-easy不独占代码库、不回退他人、不执行Git，候选交root批次审查。写入限E:/ZCode Workspace/Galgame内，本派单不联网，不改原版和历史成果；原件只guestCPU、不OS启动，primary失败事实已记录。输入仅抽象格式/派单与数值事实，不含原剧本、指令转储、素材或凭据。

原字节流事实：42F880字节调度→42FB00字符读取；lead闭区间81..9F/E0..FC时盲消费两字节，trail可0/5B且不验证；边界0终止、5B marker，不能文本解码后查指令。434 native单元fixtures通过。59,367结构island全部首literal run与reference相等：3,904,210 bytes / 1,952,105 units；stop marker 990、nul 418、limit 57959。剩余恰为990独立[s格式expr 214100 bytes + 418终止0；原island 4118728全部字节机械对账，语义全明、各路可达、画音还原不等同已证明。

独立expr头为n u32LE、compiledflag 1 byte、table_size u32LE；表5组count u32LE，每条offset、index各u32LE；不同于参数内短计数expr。990 code 116418 bytes、8374 relocs，全表尾和slot范围精确校验，源只读。

原VM初探990×6=5940：受控空查询向量与零channel manager下5274返回、666在native0入口显式停止；不能fake返回或称通过、无独立VM对比。58的case10实际查地址列表，676实际通道清理路径，零count只证无效索引返回；0待系统字符串import和外部控制。当前新增结构/文字核验，不证明全VM或画面音频。

候选子代理工作区/ISSUE-20261011-02/r-literal-run-01；formal临时/ISSUE-20261011-02/r-literal-run-replay-01/；正式回放状态以root receipt为准。工具为lucifen_literal_run_reference.py与lucifen_inline_expression_reference.py。新输出目录复跑，历史不覆盖。

保留完整OT/OTA/OTV/OTR忠实剧本与帧目标，未知不得noop。root仅分析与运行核验，技术工具由editor-easy提供。后续需补独立VM对比、系统字符串import、外部控制与最终画面音频验证，再交批次审查。

root行政归档注记：十份完整JSON、两个参考源码与正式回放一致，其中VM结果保留passed=false。990表达式原4303F0冷/热准备3960次、真实430090绑定1980次，止于VM前；凭据见inline-expression-binding-summary.json。先verify-native-units建立新目录，依次source-literal-runs、island-partition，之后binding/parser可独立；VM-discovery另建新输出目录。所有recipe是验证命令，需改副本输出路径后再次复跑，不能覆盖历史。
