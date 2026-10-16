# R IME输入与VM窗口消费者证据（2026-10-14）

Issue：ISSUE-20261011-02。工程阶段；root负责分析、原码/平台验证、批次复核和Git行政；editor-easy DeepSeek high负责三份工程helper与本页技术增量。原版PE/DLL只在Unicorn内执行，不OS加载。既有R与自建作品知识沿用增量路径，非翻译规范使用未变更哈希缓存。

## 技术增量（editor-easy交付）

1. canonical 39 与 43 实际退出 0，且 HOST_FIXTURE_CLEANUP_PASS；该阶段验证包含 IME、17 次手柄查询与已知 fixture 资源清理，不等于原版 shutdown。32 位原码只覆盖 Unicorn；五函数旧静态 CFG 229 instr / 4 direct / 12 indirect 只是静态覆盖声明，不是动态 100%。因此不能据此宣告全四版、画音、忠实 TJS 完成，当前仅为 workspace 候选，由 root 应用。

2. IME 与输入路径需按实际调用断言：原 `GetModuleHandleA` borrowed imm32 及 `GetProcAddress` 仅解析 `ImmAssociateContextEx`，未调用；实际 disable 分支调用 `ImmAssociateContext(HWND,0)`，原 parent+0xE7D 标志 `1 -> 0`，前 HIMC borrowed 映射不 Destroy。原键状态 Scroll145 / Caps20 / Num144 / Ctrl17 实际是 SHORT 查询，不是文本输入。测试不应误判 `ImmAssociateContextEx` 被调用或 HIMC 被销毁。

3. 手柄与并发边界需修正预期：`joyGetNumDevs` 实际返回容量 16，不是连接设备数；随后 16 次 `joyGetDevCapsA` id 0..15 / 404 bytes，实际 MMRESULT 165，且两侧 guard 完整，总计 17 call；原 WinMain 停在 `ShowWindow(HWND,5)` 前未返回。35 与原 live31 同时运行时，35 在 `OpenMutex` 之后走 `FindWindowA` 分支被挡，不能当作 helper 故障；31 正常 fixture 清理后同源码 39 通过，不篡改 OS mutex 结果。

- R 原生 `GameInit` 调度独立快照 `dispatch` 计 22 次；native 槽 796 的 frame 形态为 `[0, 源指针, 4]`，源指针可定位发布 module body `offset 4484`。root 侧已将该源指针映射到本地精确 42 bytes 尾段，该尾段为必要 DLL 加载失败提示。
- 在已初始化原 parent 与真实隐藏窗口的 Unicorn 中运行原 `414530 -> 452BD0`，`IsWindow=1`；原 `9001` 包经 `wParam` 传入而非 `lParam`。已定义字段：`offset0 u8=0`、`offset4 u32=映射源指针`、`offset8 u32=0`、`offset12 u8=4`、`offset13 u8初值1`；其余 padding 语义不可猜。
- 原 WndProc 直接重放而非 OS `SendMessage`，实测链 `49F860 -> 49F8F0 -> 注册 adapter 485920`；adapter 四 words 为 `[vtable 51A424, parent 02003000, 485B00, 0]`，`485B00` 经 parent 真实 vtable `51874C+C8` 跳 `481FF0`，control0 分支至 `4529C0/4527D0`，停在嵌套 `SendMessage(69F50000,9000,1,0)` RA `45281C`。静态 `4529C0` 后续 IAT `5183D0` 为 `MessageBoxA`，但未实际显示/返回弹窗，native 796 未返回 VM；该链仅为 R 失败提示路径证据，不称标题/模式设置或 100% 正常 VM/WinMain 整链。知识用于两作品，root 应用与批次复核，不 Git、不回退别人。

## 收件与复验索引（root行政）

- 原码闭环配方：verify-original-IME-joystick.txt。以便携32位Python运行，argv指定工作区临时内一个未存在的新目录；39为纯IME/joy闭环，43为同源码叠加下面的消费者取证，两者均退出0并HOST_FIXTURE_CLEANUP_PASS。输入JSON与清理JSON取自45（包含同一消费者验证与新增selector21），后者仍是显式fixture清理，不是原版shutdown。
- 消费者配方：verify-original-native796-consumer.txt，同样接收fresh目录argv；正常初始化后在ShowWindow前直接调用原native796并重放原WndProc，明确未调用OS SendMessage，也未改变该停止条件为弹窗成功。原GameInit参数指针从独立VM快照映射到同源42bytes；不声称VM与WinMain正常调度整链。
- 独立原SOB调度：verify-native-SOB-frame.txt与SOB-native-frame-boundary.json、SOB-recovery-summary.json；22次调度与实际frame三words、296次GameInit重定位是独立上下文，地址只在该次运行有效。未把独立快照与消费者重放拼成正常GameInit流程。
- 原码静态：native-consumer-CFG.json含五个真实函数229instr/4direct/12indirect；native-9001-adapter-CFG.json、native-9001-parent-slot-C8-CFG.json、native-9001-control0-CFG.json与imports对应实际注册适配器、parent槽位C8和控制0函数。静态MessageBoxA下游未动态调用；非法猜测函数边界的试验未收录。
- 三份正式helper：编程组/工具/lucifen_host_imm_export.py、lucifen_host_joy_count.py、lucifen_host_joy_query.py，均为editor候选原样交付，43从正式工具目录加载。IMM Ex未被原码调用；joyGetPos/Ex仅声明未调用。
- 窗口显示准备：WINDOWPOS/NCCALCSIZE布局与纯guest打包的32/64 ABI自验通过，候选仍留子代理工作区，未合并、未调用ShowWindow、未证明复制回写或显示消息。JSON为准备证据，不计画面完成。
- source-integrity.json验证1原EXE、8LPK、3DLL、446原SCRIPT、418IR与111bytes USER.CFG未改；原版备份与日文介质源未写。API外发仅自有通用接口与派生事实，不包含原始剧本、游戏资产或凭据。

## 验证命令

从工作区根运行；fresh名称每次另取，禁止覆盖历史目录。

    工具/python-3.13.12-embed-win32/python.exe -X utf8 -B 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_IME输入与VM窗口消费者证据_20261014/verify-original-native796-consumer.txt 临时/ISSUE-20261011-02/fresh-IME-consumer-01

上述原码配方同一时间只运行一个：原游戏系统命名mutex使第二实例走FindWindowA分支；保留实际OS返回值，不改mutex名或伪造不存在。其他互不依赖的API候选、ABI与静态取证可以并行。

## 未完成项与复核范围

本批覆盖IME/原键状态/手柄与错误提示消费者取证、三份helper和知识/行政文档；没有绘制、PCM、影片或忠实TJS完结证据。全部四版本L0–L5目标继续active。正常VM初始化依赖、nested9000、实际MessageBox与ShowWindow待后续；不能将22 dispatch、17 API或静态指令数作为作品100%覆盖率。

## 原初始化依赖增量（editor-easy交付）

- 原 native 系统槽 6（`4114D0`）selector 21 经精确 jump table `4115F4[21] -> 4115DA` 读取 global `5357E4`，返回该指针非零的布尔值；独立 SOB fixture 与该 global 为 0 的场景一致，canonical45 中已完成真实原 parent/窗口创建/IME/17 手柄初始化但该 global 仍为 0，故真实原 cdecl 执行返回 0，CPU/stack 检查通过且未伪造 pointer——可确认 `GameInit` 的 DLL 失败提示属尚未满足的初始化依赖，不能以“窗口已创建”推断可运行正常剧本，后续仍需追该 global 的实际写入点与后续原初始化链；45 退出码 0 且已知 fixture 已清理，本证据不构成完整原 VM/演出验证，仅为技术证据追加，不宣称已攻破，不 Git、不回退他人改动、不调用暂停角色，不输出原作内容。

Root收件：original-system-selector21-in-initialized-parent.json与native-4114D0两份CFG对照原getter。既有R调度与DLL证据_20261011已证明受控0/1和setter；此批新增真实parent初始化到ShowWindow前的0值，不重复将受控1当作真实加载结果。消费者最终配方45退出0；独立SOB配方44以64位宿主Python3.14.7运行，通过原x86调度与既有release检查；误用32位解释器的首次44在Unicorn库加载前失败，没有进入原码。
独立SOB命令使用 E:/Tools/Python/python.exe -X utf8 -B 加 verify-native-SOB-frame.txt 与fresh目录参数；它使用工具/unicorn-2.1.4-py314，不能用上述32位解释器。本目录主要WinMain/消费者配方仍用便携32位解释器。
