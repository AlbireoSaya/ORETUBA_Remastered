# R 线程启动握手与消息接续阶段；阶段入口 R_线程启动握手与消息接续证据_20261014
主代理已记录规范源 DWM WM_DWMNCRENDERINGCHANGED，完整链接 https://learn.microsoft.com/en-us/windows/win32/dwm/wm-dwmncrenderingchanged；原 PE/DLL 仅 Unicorn 非 OS 加载。
本批现在 10 个 SDK：原 8 个 editor SDK + ReadOnlyFilesLarge 实例 max_transfer 默认 32 MiB/上限 64 MiB、bridge_ReadFile_large 单调用 max_read。
保留旧全局 1 MiB/readonly 白名单/guard/错误/短读 EOF/offset wrap 及 overlap 验证。
原 8 个 editor SDK 已由 root32/64 owned OS/ABI 测试通过：guest thread HANDLE 纯登记、guest MSG pack/unpack 32 字节、GetMessageA signedint、TranslateAcceleratorA、SetWindowPos NOACTIVATE、GetForegroundWindow、wvsprintfA typed fixed3args。
native MSG 分别 32/48 bytes，guest MSG 32；host 指针不截断；registerdup/invalid 不修改映射，bool/overflow 拒绝；real WM_QUIT 返回 0 guarded；无 accelerator 非键返回 0；wvsprintf host va slot4/8 真实 OS 匹配 guard。
SetWindowPos 仅 owned 合成对象测试，未称修复原窗口。
32/64 真实合成 ReadFile 1571162 bytes 守卫/短读 EOF/无效参数预检/旧 cap 不变/cleanup 通过。
128 原码实际 4 次 one-string wvsprintfA，host va slot4bytes 重建，所有输入输出 guard/结果通过，推进至 >1 MiB ReadFile 旧 cap 边界。
131 原码实际 ReadFile 1571162 字节成功，继续原图像解码，8 个 native 1M slices 预算停，不是未知 API/原作损坏；132 继续解码进行中无结论。
source121/122 实际 CreateThread consumer：object+4 HANDLE、+8 TID、+5C ready event；原 4F8D91 SetEvent 在业务虚调用之前，故启动握手不是 GameInit 完成。
122 wait_zero 成功会消费 auto-reset 信号，不能作为非侵入 peek，不回写假 SetEvent。
123 新重放未探测直接真实原∞等待返回 0，原 CloseHandle ready event 并清零 5C 后进入 GetMessageA。
124 真实队列首 0x31F，保守暂停；125 实际 GetMessageA/MSG 显式 HWND 映射 + TranslateAcceleratorA 0 + 进入 TranslateMessage。
127 实际 TranslateMessage 0、DispatchMessageA 0、原 WNDPROC 49F860/真实 GetWindowLongA/DefWindowProcA，回到 GetMessageA；唯一真实系统消息 0x31F/wParam 1/lParam 0，未注入源消息，没有任何原消息广覆盖证明。
129 会话消失且无活原流程/完整 receipt，不计成功或原游戏失败；130 root 取证 late legacy imports 覆盖 new aliases，未越过旧 cap；131 修正全局导入并运行时 assert final bindings，源码 helper 未改。
root126 取证缩进编译失败未启动原流程，改 127；源 SetRect 旧 8 次取证预算停，改 512 次真实 API 有 guard 并保留有限预算。
128 源码 va-list 边界验证进行中，不先报通过；worker 仍有限 guard 结束非原退出，消息分发仅此非绘制消息；并发调度、aliveworker、字体/DC 跨线程生命周期、WM_PAINT/键鼠/动画/音频、四版全路线、忠实 TJS 未完成；旧 NULLREGION 反例未宣称修复。
保留边界：启动握手非 GameInit、自动复位 probe 消耗、单真实系统消息、worker guard 非原退出、aliveworker、字体 DC、键鼠 WM_PAINT、动画音频、四版忠实 TJS 及 NULLREGION 未完成。

## 2026-10-14 原资源解码与阶段终点
- 本批10个SDK/32及64 OS或ABI自测通过。
- 131：原始ReadFile实际1,571,162字节，8片段执行预算停，非缺资源。
- 132：root 30秒观察deadline中止缺完整receipt，不判断原游戏失败；先前“进行中”文本由本补充纠正。
- 133：短10秒观察循环等待有限worker，22个1M原码片段退出0/cleanup通过，停在原tvpgl执行区0x12039486（根取证续跑仅限EXE原因，不是未知API）。
- 134：扩原EXE/4DLL已核验可执行区，26个片段退出0，停Root旧SelectObject将所有worker对象路由为font；原owned bitmap不是font。
- 135：按registered object kind区分实际字体与bitmap，44个片段真实EXE/tvpgl执行、源bitmap选择成功，退出0/worker_errors空/cleanup通过，停SetCursorPos原请求[960,540]，source return 44E009、hint 126D2E。
- 两次类型/导入/observer误判均为root验证器边界；未改原码、未伪造结果。
- 现状：尚未达完整初始化/动画/音频/生存线程/WM_PAINT/键鼠或四版TJS 100%；NULLREGION反例未宣称修复；源资料最终完整性复验前保持待审。
- 下一步：有界接Cursor API，将source parent/worker以实际OS活线程与资源生命周期的串行Unicorn协作模式接通，随后走原素材画音/忠实TJS/全四版全部路线。
- 规范引用保留正确WM_DWMNCRENDERINGCHANGED；不复制巨大trace。

root行政状态：135之后源完整性复验通过，最终复核范围与结论以本阶段batch-review-manifest.json为准；并非最终还原验收。