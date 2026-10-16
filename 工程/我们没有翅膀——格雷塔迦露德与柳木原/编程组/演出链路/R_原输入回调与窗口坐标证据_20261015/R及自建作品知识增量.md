## 2026-10-15 原输入回调与坐标证据
适用：R版及其自建还原基准skill。159/161 用 ownClientToScreen+SetCursorPos 对齐 (715,385)，非物理注入。真实尾转发：原 WNDPROC 49F860→49F8F0；513/514 485920→485B20/485B50；161 最终 targets 00481F70/00481F80，manager +C94→44D9C0/44D9F0。161 source_late_OS_calls 空，不得称两新 OS 接口原码已验证，仅有限 recipe；源 native≠TJS 100%。

## 2026-10-15 case162真实输入设备与线程优先级

162动态source：11父轮，AL类型=2，device=0x71ce080，manager=parent+0xC94。地址源方法 0x459020 源按下：device+4=0、+14=0→0x10、+24=0→0x80；地址源方法 0x459050 源松开：device+4=1、+14=0x10、+24=0x80→0。设备非父对象内嵌状态；父对象范围零差异不能证明按钮未被处理，真实设备字段变化已由原码证实。SetThreadPriority original RA 0x40cca5/0x40cd46，guest HANDLE 0x69D80000 map own host，actual same worker TID 23232，priority 0→-2→0，真实BOOL 1/error 0，worker owner cleanup再恢复0。PostMessageA本例未执行，不写已验证。本例下一未映射 KERNEL32 API 为 lstrcpynA，hintRVA 0x00126C16，不是未知 VM 指令；root 另记 next-source-boundary。worker_errors空/17 cleanup receipts仅fixture，不等全引擎成功。新动态输入仍不等正文开始/目标TJS 100%。源输入/device精确JSON见input-state-162-derived.json。
