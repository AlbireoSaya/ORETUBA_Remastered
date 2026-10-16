# README

本批 9 文件：7 SDK（PE 指令元数据、guest snapshot 边界、u32 snapshot、u32 diff、rawGetFocus、SetFocus、GetForegroundWindow）＋2 真实模块自检（snapshot/diff 32/64 通过；focusOS 32/64 过，hidden 窗口会改 foreground）。GetCurrentThread、SetThreadPriority 复用旧有，不重复入库。

- 157：初始导出名错误，启动前停止。
- 158：synthetic 请求 (715,385) 与光标实际 client (491,116) 不一致；23 轮未接 PostMessageA hintRVA00126F7C，非未知 VM 字节码。
- 159：ownClientToScreen+SetCursorPos 对齐 (715,385)，非物理按键注入；原缓冲 START 橙＋提示，窗口仍有白边带，ReleaseDC 末次比对 351009 颜色字节不同，负例保留，不保证整帧还原；13 轮未接 SetThreadPriority hintRVA00126BEE。
- 160：过早移除 guestThreadHandles 映射致 rootValueError，真实 native HANDLE 仍在。
- 161：映射保留至 join/close，parent 40 轮正常、worker_errors 空、BeginPaint/EndPaint 各 1、cleanup 通过；source_late_OS_calls 为空，两个新 OS 接口原码未验证。targets 00481F70/00481F80，parent this 02003000。

原码验证配方依赖 ignored 本地缓存，非 standalone checkout；四版均未完成，不称 100%。

## 2026-10-15 case162真实输入设备与线程优先级

162动态source：11父轮，AL类型=2，device=0x71ce080，manager=parent+0xC94。地址源方法 0x459020 源按下：device+4=0、+14=0→0x10、+24=0→0x80；地址源方法 0x459050 源松开：device+4=1、+14=0x10、+24=0x80→0。设备非父对象内嵌状态；父对象范围零差异不能证明按钮未被处理，真实设备字段变化已由原码证实。SetThreadPriority original RA 0x40cca5/0x40cd46，guest HANDLE 0x69D80000 map own host，actual same worker TID 23232，priority 0→-2→0，真实BOOL 1/error 0，worker owner cleanup再恢复0。PostMessageA本例未执行，不写已验证。本例下一未映射 KERNEL32 API 为 lstrcpynA，hintRVA 0x00126C16，不是未知 VM 指令；root 另记 next-source-boundary。worker_errors空/17 cleanup receipts仅fixture，不等全引擎成功。新动态输入仍不等正文开始/目标TJS 100%。源输入/device精确JSON见input-state-162-derived.json。
