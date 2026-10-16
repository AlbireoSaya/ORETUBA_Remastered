### 2026-10-14 线程启动握手与父线程消息接续
阶段入口 `R_线程启动握手与消息接续证据_20261014`。root 精确装配，按批审记录推进。

- editor SDK 现 10 个：原 8 个含 guest thread HANDLE 纯登记、guest MSG pack/unpack 32 字节、GetMessageA signed int、TranslateAcceleratorA、SetWindowPos NOACTIVATE、GetForegroundWindow、wvsprintfA typed fixed 3 args；本批 ReadOnlyFilesLarge 实例 max_transfer 默认 32 MiB/上限 64 MiB；bridge_ReadFile_large 单调用 max_read。保留旧全局 1 MiB/readonly 白名单/guard/错误/短读 EOF/offset wrap 及 overlap 验证。
- root32/64 owned OS/ABI 测试通过：native MSG 32/48 bytes，guest MSG 32，host 指针不截断；register dup/invalid 不修改映射；bool/overflow 拒绝；32/64 真实合成 ReadFile 1571162 bytes 守卫/短读 EOF/无效参数预检/旧 cap 不变/cleanup 通过。
- real WM_QUIT 返回 0 guarded；无 accelerator 非键返回 0；wvsprintf host va slot4/8 真实 OS 匹配 guard。SetWindowPos 仅 owned 合成对象测试，未称修复原窗口。
- source 121/122 实际 CreateThread consumer：object+4 HANDLE、+8 TID、+5C ready event；原 4F8D91 SetEvent 在业务虚调用之前，故启动握手不是 GameInit 完成。
- 122 wait_zero 成功会消费 auto-reset 信号，不能作为非侵入 peek，不回写假 SetEvent。
- 123 新重放未探测直接真实原无限等待返回 0，原 CloseHandle ready event 并清零 5C 后进入 GetMessageA。
- 124 真实队列首 0x31F，保守暂停；125 实际 GetMessageA/MSG 显式 HWND 映射、TranslateAcceleratorA 0、进入 TranslateMessage。
- 127 实际 TranslateMessage 0、DispatchMessageA 0、原 WNDPROC 49F860/真实 GetWindowLongA/DefWindowProcA，回到 GetMessageA；唯一真实系统消息 0x31F/wParam1/lParam0，未注入源消息，没有任何原消息广覆盖证明。
- 128 原码实际 4 次 one-string wvsprintfA，host va slot4bytes 重建，所有输入输出 guard/结果通过，推进至 >1MiB ReadFile 旧 cap 边界；131 原码 ReadFile 1571162 字节成功，继续原图像解码，8 个 native 1M slices 预算停，不是未知 API/原作损坏；132 继续解码进行中无结论。
- 129 会话消失且无活原流程/完整 receipt，不计成功或原游戏失败；130 root 取证 late legacy imports 覆盖 new aliases，未越过旧 cap；131 修正全局导入并运行时 assert final bindings，源码 helper 未改。
- 主代理规范源：MS DWM WM_DWMNCRENDERINGCHANGED，完整链接 https://learn.microsoft.com/en-us/windows/win32/dwm/wm-dwmncrenderingchanged。原 PE/DLL 只 Unicorn 非 OS 加载。
- worker 仍有限 guard 结束非原退出，消息分发仅此非绘制消息；并发调度、aliveworker、字体/DC 跨线程生命周期、WM_PAINT/键鼠/动画/音频、四版全路线、忠实 TJS 未完成；旧 NULLREGION 反例未宣称修复。
- root126 取证缩进编译失败未启动原流程，改 127；源 SetRect 旧 8 次取证预算停，改 512 次真实 API 有 guard 并保留有限预算。128 已按上述推进，132 未结论，不先报通过。
