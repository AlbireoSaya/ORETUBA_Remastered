# R对象接口与合成证据（20261011）

## 一、证据口径
结论出自受控 Unicorn x86-32 原 CPU 执行，guest 存储预分配；原分配器、Windows 加载器、DIB 与真实场景均未执行。工具为 lucifen_instruction_evidence.py 与 lucifen_cdecl_observer.py，产物见证据目录“R对象接口与合成证据_20261011”。所有测试处于预分配受控状态、无 child、非生产接入；0 diagnostics 与候选槽映射不构成完整性证明。

## 二、238/239 输出槽与边界
238：入口 0x41E850、工厂 0x4BA6A0、type 9；239：入口 0x41E880、工厂 0x4BA7C0、type 10。公共帧四 u32：width、height、format_low8、extra_low8。隐藏输出槽为原调用者栈 SP0+4，其 framePtr 复用为输出槽。工厂栈为 return_pc、SP0+4、width32、height32、caller_EDX_upper24|format_low8、caller_ECX_upper24|extra_low8。序言清零输出槽后，以 0xD8 调用原 operator-new 0x50577F 并在分配器 body 前停止，故属未分配边界。wrapper_return 对输出槽的最终读取仅静态观察，工厂成功/失败未动态证明。

## 三、429 转换、真值与绘制
429 入口 0x4249E0，帧 u32：object、bitmap_argument、mode_word、id_word、truth_word。object cast 静态接受 type7..10；动态 type9/10 经 embedded+0x30 得 outer+0xBC 的 auxiliary。bitmap cast 实为两条各自独立、均已验证的选择：其一，type4 对象自身即作为 bitmap；其二，outer type9/10 经 cast 返回 owned bitmap+0x34。二者不得写成需要两种类型同时存在才能成立。aux 被调方 0x45AFF0，栈为 return_pc、bitmap_argument_ptr、(truth_word&0xFFFFFF00)|mode_low8、id32、(truth_word&0xFFFFFF00)|bool(truth_word!=0)。真值用整个 DWORD：非零即真，高 24 位保留，不只看低 8 位。返回：源 cast 失败 -1；目标 cast 或 aux 缺失 -2；成功 0；argument 无像素 1；绑定缺失/尺寸不匹配 2。绘制上，空列表原 renderer 写 bitmap argument；aux 绑定 bitmap 仅在 disjoint 时不变；same-object alias 也写 bound 像素。

## 四、清屏与全局
aux+0x50 clear32 写整个 u32 含高字节；aux+0x52 clear8 取 (colour32>>16)&255，调色板语义未知；aux+0x55 非零则空列表保留像素。全局 0x529E6D 受控 0/1，真实启动值未知。

## 五、验证数量、notify 失败与未验证
计数：direct_cfg_entries 18、instruction_rows 1336、direct_edges 59、indirect_gaps 47、diagnostics 0、instruction_helper_groups 9、observer_helper_groups 6、238_239_call_cases 16、factory_allocator_boundary_cases 8、429_cast_call_cases 14、empty_compositor_pilot_cases 4、empty_compositor_matrix_cases 48、alias_and_clear_boundary_cases 11、aux_attach_cases 4。

notify1 失败：两类型 aux_bitmap 在无效 fetch 前已赋值；trace 末次调用 0x50762A 经 IAT 0x51814C 指向 KERNEL32.HeapAlloc，客体 IAT 未绑定，实际跳到未映射的 0x1277C8，该异常既非 API 失败返回，也非分配成功，本身未执行 Windows loader。

未验证：原堆与 Win32 DIB 分配、原 manager/全局启动、notify=1 完成、非空 child/list 绘制、type7/8 动态状态、真实原生向量/VM 参数、四版本全场景/脚本/音频/帧对比、TJS 生产接入。

## 六、下一阶段
解析 IAT 与真实分配器边界，恢复 notify=1 与非空 child/list 路径，补 type7/8 动态状态与真实 VM 参数，再做四版本对比和 TJS 生产接入；在此之前，候选槽映射与 0 diagnostics 不得视为完整覆盖。