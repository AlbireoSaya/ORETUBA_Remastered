# R TOB 原码控制流与静态参数对照

## 概述
本阶段对 R 版 TOB（ORETUBAR.EXE）做字节码控制流与静态参数字面量的原码对照：header label 查找、table unsigned index、同模块 jump/call/return 语义、module=0 调用帧压栈/弹栈、return override 规则，以及 R 字节调度入口 42F880 → 参数入口 42FB50 至 42FDC2 断点的“未派发前”静态参数取值。产物包含本地原始指令证据、验证元数据与参考工具；不改原版与历史成果，不执行网络，不通过操作系统加载原 EXE，预置 ctx 非完整生命周期。

## 证据目录
工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/
- corpus-control-results.json / corpus-control-summary.json
- corpus-literal-results.json / corpus-literal-summary.json
- helper-and-synthetic-native-verification.json / tob-function-instruction-evidence.json
- verify-native-control.txt / verify-native-literals.txt / verify-helper.txt / verify-instructions.txt

## 源与完整性
- 备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE SHA256 b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33
- 418 TOB 源逐文件 hash 全篇 guest 与磁盘前后不变。

## 控制流要点
- 4AC190 header label：case 敏感 rawbytes 首个匹配；NULL 返回 0；absent 返回 FFFFFFFF。4AC200 table 用 unsigned index。
- 同模块 jump 4AD0A0 / call 4AD010 / return 4AD120；返回 PC 不主动写 ctx+42C。
- module=0 的 call 压 [-2, origin_relative]，即使 missing；return 先弹帧，即使 missing。
- return override 0 保存 offset；FFFFFFFF 表示 codebegin；其他采用 override。
- 规模：840 labels + 58425 Tentries；lookup 1676 / table 59679 / jump 840 / call 2512 / return 2930 真实调用检查。完整 ctx/desc/guards 不变或仅精确允许变动。

## 静态参数要点
- 调度入口 42F880 遇 '[' 后消费并处理 ' ' 分支到 42FB50；参数入口 42FB50 到 42FDC2。
- 只 condition1 / static literal selectors 0/1：tag0=>[0,0]；tag2=>[0,u32]；其他非 zero tag + selector0=>[tag,u32]；selector1=>[tag|2,source_ptr]；长度0=>[tag|2,0]。
- 字符串长度计字节，不自行解码/复制，不施加 NUL 约束。
- 验证 214821 records / 342881 items / 86094 source pointer items；2287 unsupported selector records、1507 nonliteral condition locator candidates 保持未验证。locator candidates 218615；signature locator 不证明完整分区。

## 夹具与静态指令
手定 8 原记录夹具 + 6 helper groups 共 14（含错 flag / 错 pointer 负控）→ helper-and-synthetic-native-verification.json；12 入口静态 1069 行 / 58 direct edges / 6 indirect gaps / 0 diagnostics → tob-function-instruction-evidence.json；不声称全 parser CFG 闭合。4AC640 为附属元数据加载，非 main update。

## 复跑 cmd（PowerShell，root 相对路径）
Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/verify-native-control.txt' | python -X utf8 -B -
Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/verify-native-literals.txt' | python -X utf8 -B -
Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/verify-helper.txt' | python -X utf8 -B -
Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/verify-instructions.txt' | python -X utf8 -B -
脚本创建新证据目录 临时/ISSUE-20261011-02/r-tob-control-replay-01，只新建不覆盖；先 control 创建目录，其余随后。

## 范围缺口
变量/表达式 selector、条件、跨模块加载/分配、真实 handler 全语义、帧音频、四版无损 IR 目标剧本及 100% 完整还原均未验证。goalactive。

## 真实失败
- 批量短函数在 timeout=1000000 时迟迟无进度；终止已确认属于本批的进程，改 timeout 0 并保留指令 count 100000 后 control 3.5 秒通过；内部原因尚未定位。
- 最初大派单 14000 / 独立 reference 7000 / probe 8500 均 reasoning、finish length 无候选；拆短后两个 helper stop。
- 不是已有工程实现绕过 editor。