# R_父应用构造与原生窗口入口证据 2026-10-12

范围：本阶段仅在限定条件下核验父应用构造与原生窗口入口链路，不代表 OT/OTA/OTV/OTR full L0-L5 完成；root 复核待完成，不提前声称合并或 100%。OTV=MAGES TaskDSL/CRI，非 Lucifen。

复核命令（从 workspace 根执行）：python -X utf8 -B 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_父应用构造与原生窗口入口证据_20261012/verify-parent-scheduler.txt。工具位于 编程组/工具，原资料只读，Win32 子进程 temp 必须落在 workspace 内。证据文件：parent-constructor-boundary.json、parent-lifecycle.json、scheduler-boundary.json、actual-API-events.json、x87-setup.json、host-fixture-cleanup.json、root-source-integrity.json、host-leaf-fixtures.json、guest-module-path-fixtures.json、verify-parent-scheduler.txt、root-batch-review.json。

一、构造与窗口入口须分开描述。（1）父对象构造：actual 40A0A0，size 0x1C18，args[] -> parent 0x02003000，vtable 51874C，global 530C94 由原作写入；此时 parent+150 的 HWND 为 0。（2）WinMain 40A040/452CF0 未执行。实际 native 窗口的“无句柄分支”与“真实窗口创建”是不同判定，不得混写。

二、精度与系统叶子。受控 guest FNINIT 将 x87 控制字重置为 037F；实际原 CRT 5080B1->50C0B2 设 FPCW 023F，PC10=53bit，异常掩码 3F。完整 FPinit/CPU 特性初始化未执行。真实 Windows leaf heap/critical-section 替代、COM、events、version 156、wsprintf、registry DirectX32、locale、display 查询均在受控 provider 下发生。GetSystemInfo 36 与 GlobalMemoryStatus 32 取自真实独立 32bit WindowsPowerShell，保留原 dwLength A5A5A5A5，API 将该字段写回数值32。host-process manifest/DPI/volatile memory/tick 不等同原 OS 环境。裸注册表类型输出指针为 NULL：actual_type=null，不构成 REG_NONE 证据。

三、显示枚举。真实 EnumDisplayMonitors 仅取一台显示器快照；原回调 4ECFB0 以快照 rect + 映射 opaque HMONITOR 执行；原 GetMonitorInfoA 72、CreateDCA、GetDeviceCaps、DeleteDC 及 EnumDisplayDevicesA 424 调用 47 次（索引 0..45 为真、46 为假）生成列表。snapshot-then-guest-callback 属受控时序，不是完整 OS 回调或并发证据。

四、调度边界。在同一 actual 构造父对象上，使用受控 provider/list/cache0/localaux、预开只读归档，配原作缺失初始化 Cxx 恢复 currenthead zero frame 的 OS 仿真。main 9 + GameInit 17 = 26 次 dispatch；native slots 0，6（arg21 DLL availability 0），796/414530（actual 452BD0 空 HWND 分支），2（request3）。actual script branch 产出 0、moduledepth 3；不是完整 GameInit 或所有路径。child 4526 bytes、296 relocs 与原发布引用精确一致；parent 未手工填充，global 未打补丁。

五、清理与生命周期。原 pop/dtor/archive freeptd 清理后恢复 19 项 parent baseline；原 40A780 dtor 返回 1，19 heapblocks -> 4 remainingCRTglobal blocks；critical 13->6 global，2 events 关闭，COM 0，SEH 恢复。dtor 后 global 530C94 仍指向 parent，表明生命周期已结束、指针悬空，禁止在 dtor 后使用。最终 host fixture 释放 4 globals/heaps 并使全部 CS/TLS/handles 归零；这不是原作完整 CRT shutdown。

六、完整性与边界。1 EXE/8 LPK/446 SCRIPT/418 IR 经新查验未变，原文件从未被 OS 执行或修改。full L0-L5 目标仍 active；尚无 100% 恢复声明，也无完成忠实全路线 TJS 或渲染/音频。本文件所有结论仅限本限定阶段，root 复核待完成。
