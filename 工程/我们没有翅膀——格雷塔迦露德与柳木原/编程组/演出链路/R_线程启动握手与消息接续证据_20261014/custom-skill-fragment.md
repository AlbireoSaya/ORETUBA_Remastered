### 2026-10-14 原父线程消息入口有限证据
阶段入口：R_线程启动握手与消息接续证据_20261014；只小增量，依据主代理已验证事实，root精确装配，批审继续。
- 当前10个editor SDK：原8项（guest thread HANDLE纯登记、guest MSG pack/unpack 32字节、GetMessageA signedint、TranslateAcceleratorA、SetWindowPos NOACTIVATE、GetForeground、wvsprintfA typed fixed3args）+ ReadOnlyFilesLarge实例max_transfer默认32MiB/上限64MiB、bridge_ReadFile_large单调用max_read；保留旧全局1MiB/readonly白名单/guard/错误/短读EOF/offset wrap及overlap验证。
- root 32/64 owned OS/ABI测试通过：native MSG分别32/48字节而guest MSG 32字节；host指针不截断，register dup/invalid不修改映射，bool/overflow拒绝；real WM_QUIT返回0 guarded；无accelerator非键返回0；wvsprintf host va slot4/8真实OS匹配guard。
- 32/64真实合成ReadFile 1571162 bytes守卫、短读EOF、无效参数预检、旧cap不变、cleanup通过。
- SetWindowPos仅owned合成对象测试，未称修复原窗口。
- source121/122实际CreateThread consumer，object+4 HANDLE、+8 TID、+5C ready event；原SetEvent在业务虚调用之前，故启动握手不是GameInit完成。
- 122 wait_zero会消费auto-reset信号，不能作为非侵入peek，不回写假SetEvent。
- 123新重放未探测直接真实原∞等待返回0，原CloseHandle ready event并清零+5C后进入GetMessageA。
- 124真实队列首0x31F，保守暂停；125实际GetMessageA/MSG显式HWND映射+TranslateAcceleratorA返回0+进入TranslateMessage。
- 127实际TranslateMessage返回0、DispatchMessageA返回0、原WNDPROC/真实GetWindowLongA/DefWindowProcA，回到GetMessageA；真实系统消息0x31F/wParam1/lParam0，未注入源消息，无任何原消息广覆盖证明。
- 主代理规范源采用MS DWM WM_DWMNCRENDERINGCHANGED：https://learn.microsoft.com/en-us/windows/win32/dwm/wm-dwmncrenderingchanged；原PE/DLL仅Unicorn非OS加载。
- 128原码实际4次one-string wvsprintfA，host va slot4bytes重建，所有输入输出guard/结果通过，推进至>1MiB ReadFile旧cap边界；131原码实际ReadFile 1571162字节成功，继续原图像解码，8个native 1M slices预算停，不是未知API/原作损坏；132继续解码进行中无结论。
- 129会话消失且无活原流程/完整receipt，不计成功或原游戏失败；130 root取证late legacy imports覆盖new aliases，未越过旧cap；131修正全局导入并运行时assert final bindings，源码helper未改。
- root126取证缩进编译失败未启动原流程，已改127；源SetRect旧8次取证预算停止，改512次真实API有guard并保留有限预算。
- worker仍有限guard结束非原退出，消息分发仅此非绘制消息；启动握手非GameInit、auto-reset probe消耗、单真实系统消息、并发调度、aliveworker、字体/DC跨线程生命周期、WM_PAINT/键鼠/动画/音频、四版全路线、忠实TJS未完成；旧NULLREGION反例未宣称修复。
- 本增量未Git、未回退、未外查、未假报。
