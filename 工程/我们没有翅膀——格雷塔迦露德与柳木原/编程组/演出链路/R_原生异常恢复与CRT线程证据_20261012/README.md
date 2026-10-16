# R_原生异常恢复与CRT线程证据 20261012（主合并待评审）

## 范围与路径
阶段: g/演出链路/R_原生异常恢复与CRT线程证据_20261012
g = 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组
通用工具: lucifen_host_read_probe.py、lucifen_host_write_probe.py、lucifen_host_tls.py、lucifen_guest_unwind.py。
证据产物: sob-recovery-summary.json、original-Cxx-handler-probe-summary.json、missing-initialization-exception-summary.json、boot-API-results.json、fixtures.json、root-source-integrity.json、root-batch-review.json、verify-recovery.txt、verify-fixtures.txt。

## 核心事实（自有数值证据）
只读原始R EXE x86代码经Unicorn执行 original 4A67E0/controller 809注册/read/decrypt。缺失原始SCRIPT/SOB_INIT.DAT时，真实CreateFileA错误2/3引发原始C++ RaiseException E06D7363，flags=1不可继续，3参 19930520/throwobject/ThrowInfo 522F38。
root拦截后构造受控guest EXCEPTION_RECORD 80/CONTEXT 716，在较低的原栈 02007000调用 original handler 515C60（FuncInfo 523170）。C++类型匹配/对象复制基于真实guest内存，并在单独守护的宿主替身上调用真实Windows IsBadReadPtr/IsBadWritePtr（各1次），而非原始宿主guest地址或通用内存安全。
original RtlUnwind thunk 5120A8→IAT 5181F4 wrapper 5053E1 continuation 505409，target==实际FS0，目标即当前链首；目标以上没有待展开帧（目标帧自身不在该RtlUnwind调用中展开）：仅此窄guest OS边界由strict planner模拟（flags OR2、ESP+20、EAX、IP转移）。original 505409清bit2/恢复FS，实际507994局部unwind，507AAD catch→typed catch 49275D→native continuation 492776。非真实宿主RtlUnwind，非完整SEH。
真实HostTLS：分配实际TLS index，供给original 52D970；original 507EF3_getptd实际calloc 50BEBE HeapAlloc flags 8、0x74取整128；TLS set/GetCurrentThreadId/PTD init执行；+6C/+70在catch后恢复0。original 507F5A_freeptd释放实际PTD并TlsSetValue 0；真实TlsFree由宿主清理，非original CRT teardown。完整original _mtinit 507E8C/critical sections未执行。
native 4A67E0到达original哨兵0200F000/EAX0/ESP02008018/SEH FFFFFFFF；本阶段无合成元数据。USER_VAR/SOB1 768 decl、3724 initial bytes、3数组、2局部重定位、全部3数据集精确参照。FUNC_LIB +21 SOB0 original publish/relocate/pop free 22容器42690重定位607129字节精确参照809 native 3命名。157 HeapAlloc/157 HeapFree、23 GlobalAlloc/23 GlobalFree、25 ReadFile、24 CreateFileA、23 SetFilePointer、1 CloseHandle。无泄漏自有块/句柄/TLS。native指针探针各1，Rtl guest模拟1，GetLastError 6/TlsGetValue 7/TlsSetValue 2/GetCurrentThreadId 1/SetLastError 6。Fixtures：36指针、28 TLS检查、1 unwind接受/53拒绝（他帧/空/标志/类型/范围拒绝）；实际64ptr >FFFFFFFF保留；错误线程在变更前拒绝；HostTLS 包装器不释放调用者所有的内存；PTD 由原版 _freeptd 释放。

## 限制
其余受控：provider/list/prefix/cache0/预打开归档/allocator Win mode1/PTD index输入/records/context/零帧OS模拟。非原始OS引导/完整CRT/父应用/native body/完整script/render/audio/OTOTAOTVOTR 100%。

## 结论与下一步
原始EXE/8LPK/446SCRIPT/418IR哈希将由root校验；root评审待最终。本阶段证据为窄载荷证明。下一步：original VM指令调度/控制续延，再做original native bodies/resource/task/render/audio比较。不声称目标完成。
