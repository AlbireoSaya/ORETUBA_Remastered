# R 模块调度与 DLL 依赖证据

本目录为 ISSUE-20261011-02 的阶段证据，由 root 集中复核。原版 EXE SHA256 b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33。没有宿主运行原游戏或 DLL，没有画音对照，也没有绕过未知原生接口填返回值。

| 证据 | 已验证范围 |
| --- | --- |
| r-main-scheduler-gameinit-request.json / r-main-final-tools-recheck.json | 原 main 的9条VM指令、native0本体及调度器连续到 GameInit 装载请求；唯一API为有效非重叠字符串的 lstrcpyA 成功模型 |
| r-scheduler-state-matrix.json | 11个合成状态/VM返回组合，原调度器到首次装载、清理、返回或第二次VM入口；不执行装载/清理体 |
| r-gameinit-publication-first-native.json | 仅原装载发布块，已重定位GameInit的5条VM指令到首原生接口体前；不是完整装载器 |
| r-gameinit-selector21-word-0-next-native.json / word-1 | 受控依赖字段0/1，执行原getter，再到native796或7体前；1不是实际对象/启动真值 |
| r-dll-state-setter-selector21.json | 原setter与selector21三对象夹具；未知对象完整构造未执行 |
| r-dll-wrapper-contract.json | 静态IAT/有效调用块核实 tvpgl.dll、LoadLibraryA、对象+4模块句柄、GetProcAddress和tvpglConfig |
| r-four-dll-interface-inventory.json / pefile-receipt.json | 4个原DLL仅PE32元数据，47导出；成熟pefile便携ZIPimport，不全局安装 |
| guest-api-host-crosscheck.json | 3个成功字串与当前宿主kernel32逐字节一致，3个不支持输入拒绝，x86 stdcall寄存器核验；不模拟SEH/完整Windows |
| 最终工具复核.json | 最终helper原文一致与main CPU重跑，4DLL全部元数据相同；Path输入仅分隔符表示不同，JSON可序列化 |
| *xrefs.json / *callers.json | Capstone可执行段字面引用候选；不作为全部可达控制流证明 |
| 原码复核命令.md / 交付来源.json | root平台验证命令、editor-easy DeepSeek high交付与失败收据；不含原剧本/素材/凭据 |

## 依赖与复验

Python3.14.7 Windows，Unicorn2.1.4 x86-32（工作区工具/unicorn-2.1.4-py314），成熟pefile2024.8.26：工具/pefile-2024.8.26-py3-none-any.whl，SHA256 76f8b485dcd3b1bb8166f1128d395fa3d87af26360c2358fb75b80019b957c6f；官方来源 https://pypi.org/project/pefile/2024.8.26/ 。使用sys.path的ZIPimport，不安装到外部。生产工具在编程组/工具/lucifen_guest_api.py、lucifen_pe_inventory.py。原码命令仍需本机只读原作及前批R静态native向量，不能宣称无本体的新clone可运行。

lstrcpyA对照依据 https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrcpya 与 https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170 。260只为夹具保护，不是引擎字符容量；错误/重叠/SEH不在兼容模型内。

原 main 有12字节局部区，因此父PC必须按运行时VM_SP-4读取，不能硬猜stack+4。Opcode0为yield成功(1)，opcode1遇NULL返回失败/结束(0)；state3实际分派表直接return0，不能凭邻近代码猜表项。完整加载、DLL工厂ABI、真实启动依赖、TOB演出和全部忠实剧本仍待验证。下一阶段从tvpgl接口继续，不能把所有导出已列出当成引擎已懂。
