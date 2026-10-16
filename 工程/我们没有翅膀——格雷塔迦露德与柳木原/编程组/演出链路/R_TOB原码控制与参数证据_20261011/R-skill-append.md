## 2026-10-11 增量：TOB 原码控制流与静态参数，不改旧知识。

- 工具参考 lucifen_tob_control_reference.py、lucifen_tob_literal_reference.py（均 editor-easy）；验证调用原方法、root 手定期望及批次复核，无 OS 加载原 EXE，预置 ctx 不是完整生命周期。
- 源备份 备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE SHA b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33；418 TOB 源 hash 逐文件全篇 guest 与磁盘前后不变。
- header label 4AC190（case 敏感 rawbytes 首个匹配，NULL 0，absent FFFFFFFF）；table 4AC200 unsigned index；same-module jump 4AD0A0 / call 4AD010 / return 4AD120；返回 PC 不主动写 ctx+42C。
- module=0 call 压 [-2, origin_relative] 即使 missing；return 先弹帧即使 missing。return override 0 保存 offset，FFFFFFFF 表示 codebegin，其他采用 override。
- 全部 840 labels + 58425 Tentries；lookup 1676 / table 59679 / jump 840 / call 2512 / return 2930 真实调用检查。完整 ctx/desc/guards 不变或精确允许变动。文件 corpus-control-results.json、corpus-control-summary.json。
- R 字节调度入口 42F880，看到 '[' 后消费再处理 ' ' 分支到 42FB50；原记录参数入口 42FB50 到精确“未派发前”42FDC2 断点：只 condition1 / static literal selectors 0/1；tag0=>[0,0]，tag2=>[0,u32]，其他非 zero tag + selector0=>[tag,u32]，selector1=>[tag|2,source_ptr]，长度0=>[tag|2,0]。
- 字符串长度计字节，不自行解码/复制/NUL 约束。验证 214821 records / 342881 items / 86094 source pointer items；其他 2287 unsupported selector records / 1507 nonliteral condition locator candidates 保持未验证。locator candidates 218615，signature locator 不证明完整分区。结果 corpus-literal-results.json、corpus-literal-summary.json。
- 手定 8 原记录夹具 + 6 helper groups 共 14（含错 flag / 错 pointer 负控），helper-and-synthetic-native-verification.json；12 入口静态 1069 行 58 direct edges 6 indirect gaps 0 diagnostics，tob-function-instruction-evidence.json，不说全 parser CFG 闭合。4AC640 是附属元数据加载非 main update。
- 复跑：Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/verify-native-control.txt' | python -X utf8 -B -；literal 用 verify-native-literals.txt，helper 用 verify-helper.txt，static 用 verify-instructions.txt。脚本创建新证据目录 临时/ISSUE-20261011-02/r-tob-control-replay-01，只新建不覆盖；顺序 control 创建目录然后其他；paths 用 PowerShell 相对 root。
- 批量短函数在 timeout=1000000 时迟迟无进度，终止已确认属于本批的进程，改 timeout 0 并保留指令 count 100000 后 control 3.5 秒通过；内部原因尚未定位。
- 本轮最初大派单 14000 / 独立 reference 7000 / probe 8500 均 reasoning finishlength 无候选；拆短后两个 helper stop；不是已有工程实现绕过 editor。
- 范围缺口：变量/表达式 selector、条件、跨模块加载/分配、真实 handler 全语义、帧音频、四版无损 IR 目标剧本及 100% 完整还原未验证。goalactive。