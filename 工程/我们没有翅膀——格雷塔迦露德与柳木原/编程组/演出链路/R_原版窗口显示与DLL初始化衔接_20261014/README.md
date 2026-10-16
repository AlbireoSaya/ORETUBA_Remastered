# R 原版窗口显示与 DLL 初始化衔接 · 2026-10-14

ISSUE-20261011-02；editor-easy 交付实现，root 进行原版 CPU / OS 验证与阶段批审。仍为初始化链路取证，不是四版本100%还原完成。


## editor-easy 证据说明：note-show-api

原版窗口显示与 DLL 初始化衔接实测：原 `ShowWindow(HWND, 5)`（`RA4A8501`）经真实 API 返回先前可见性 `0`，窗口状态由 false 变为 true；随后 23 次原 `49F860` 回调均无错误、无未决；后续实际 `SetForegroundWindow`（`RA4A8513`）返回 `0`，予以保留并继续 `GetWindowRect`。上述均为初始化消息层面的证据，不等同于原版游戏画面已出现、`GameInit` 已完成或关机已发生。路径：`R_原版窗口显示与DLL初始化衔接_20261014`。

## editor-easy 证据说明：note-abi-api

## 实测事实

WINDOWPOS：guest 28；host32 28，host64 40。NCCALCSIZE：guest 52；host32 52，host64 56。负坐标及数值回写双位数通过；HWND/insert/lppos 保持不变。错误 token、长度、超 32 位指针均被拒绝。NCC wParam1 当前仅做 ABI 检查，原 Show 未实际触发，不能记为动态通过。

## editor-easy 证据说明：note-ime-fix-api

原 WM_IME_SETCONTEXT（0x281）收到显示标志后，原 WndProc 将传给 DefWindowProcA 的 lParam 清为 0，真实 OS 按修改后的 0 调用；显示/激活中的 HWND、HDC、HICON 按类别映射与回传，其中借用的 HWND/HDC 不销毁，HICON 引用已有资源、其 owned fixture 图标仅在最终显式清理时 Destroy；线程 ID、DPI、可访问对象 ID 按标量传递。

## editor-easy 证据说明：note-dll-final-api

**静态事实**：静态 parent vtable 位于 51874C，其槽 +24 指向 40C0C0；对 40C0C0 的 409 条指令诊断结果为 0；该范围内包含 40C219→4A0CD0 与 40C23C→48A3F0 两条关系。

**动态观察与限制**：原 WinMain 已真实进入包装器，并请求 LoadLibrary(tvpgl.dll)/RA4A0D30；原 DLL 的 PROCESS_ATTACH 入口在客体 CPU 上执行并自行返回 1，包装器保存模块基址 12000000；原 GetProc 两次解析 tvpglConfig/GetLibrary（该 DLL 有 3 个命名导出）。原 GetLibrary 初始化且包装器返回后，原 setter 将真实 wrapper 指针写入 5357E4，同一实例上原 selector21 返回 1，并非手写占位。限制：客体装载器登记模型；DisableThreadLibraryCalls 仅为已登记、无静态 TLS 元数据的适配，未真实调用 OS；未通过 OS 加载原 DLL，完整 OS loader/线程、正常 GameInit/画音与关机均未证。静态关系与上述动态观察须分清。

## editor-easy 证据说明：note-rebase-api

tvpgl 源 SHA256 为 63e9308c2e89445daa1d427c5b5e1ed1ce863111ca722a5f3b6dd966d065a985。首选基址 10000000 与既有音频 CRT 客体堆冲突，故客体映射改至 12000000。

对原 4141 条 HIGHLOW 逐项做增量验证，所有变动字节均局限在重定位字段内，原 unbound ILT/IAT 保留。旧 pefile.write 方式会改变 ILT 序列因而失败，不计为通过；后续改为只使用已校验的原字节重定位副本。

新 CRT 堆 13000000..14000000 与 proxies 350C000 相互隔离，并共享已有 process guest 异常 filter。共 138 次 CRT 调用、29 类，其中包含 guest 模块路径/异常 filter 适配与真实宿主查询，并非这 138 次都是 OS API。整个过程只使用临时客体内存，原件不改，也不做 OS 加载。

## 验证用例与入口

窗口段文字中的23回调来自55夹具；63夹具为18回调，系统消息序列可变。两份原始JSON均保留。NCC wParam1没有动态触发。原tvpgl代码自行返回并发布状态；客体模块/线程通知登记是有限模型，不等同完整OS loader。

32位原版验证：从工作区根目录运行 Get-Content -LiteralPath "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原版窗口显示与DLL初始化衔接_20261014/verify-original-window-and-tvpgl.txt" -Raw | & "工具/python-3.13.12-embed-win32/python.exe" -X utf8 -B - "临时/ISSUE-20261011-02/<全新目录>"。仅一份完整WinMain同时运行；命名互斥量不能伪造。

新增9个独立editor-easy SDK模块、10个函数：32/64 ABI均通过；实际查询时钟、当前线程优先级、零超时等待和有符号MulDiv边界通过。消息注册/投递与时间精度修改仅核对声明，未执行，不能推断DS_SPRITE原入口已通过。

历史失败：pefile.write改动ILT的58夹具不计成功；61夹具在大表初始化指令预算处停止，不计包装器成功。62/63保留IAT与窗口安全检查，只在已知CPU大表期间移除全指令诊断deque并使用既有大表验证预算。原版退出/DLL detach/正常GameInit/VM画音、全部四版本与Win7/10兼容仍未验证。

SDK来源：[WINDOWPOS](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-windowpos)、[NCCALCSIZE_PARAMS](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-nccalcsize_params)、[DisableThreadLibraryCalls](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-disablethreadlibrarycalls)。


## editor-easy 后续 DLL / 消息组件交付：note-sprite-fix-api

# r-sprite-parallel-20261014 · 知识增量

## 1. 源侧请求链事实

| 项 | 事实 |
|---|---|
| 请求时机 | 原 `WinMain` 完成 `tvpgl` 初始化后，真实请求 `DS_SPRITE.DLL` |
| DLL CPU 入口 | `6000402B` |
| attach 行为 | `DLL_PROCESS_ATTACH(60000000, 1, 0)` 自行返回 `1` |
| 栈行为 | 精确 `ret12` |
| 原源 SHA256 | `8d02ffd1ab33b7f68c8dbe30607ead11d45c1b35774bd3a4d4293840ae0fc433` |
| 原请求导出 | `GetDllVersion` RVA `37C0`、`GetDShowGdiSpriteCtrl` RVA `3720`；原源为 2 个命名导出 |
| 解析后接续 | 两次 `GetProc` 解析后，原调用方接续到 `DS_MOVIE.DLL` |

## 2. 客体与共存

- 客体 CRT 区间 `14000000..15000000`。
- proxy `351C000`。
- 与 tvp / WUV 独立，共享 process guest filter。

## 3. helper：`DisableThreadLibraryCalls`

- 为已有 editor helper，对已登记且无静态 TLS 模块的**有限通知策略**。
- 未发生 OS 调用。
- 完整 OS loader / 线程行为未证。

## 4. SDK 独立组件验证边界（新增 13 模块，9+4 两批并行）

**9 模块批**

- 10 函数 32/64 ABI 通过。
- 只读或零超时系统调用通过。
- 6 条 `MulDiv` 边界通过。

**4 模块批**

- 定义宿主 MSG 布局：32 位 32 字节 / 64 位 48 字节（含 SDK `lPrivate`）。
- 同自有进程真实 `PostThreadMessage` / `PeekMessage` / `DispatchMessage` / `TranslateMessage` 通过。
- `WPARAM` 全宽与 `LPARAM` 有符号全宽通过。
- buffer guard 通过。
- 消息精确消费通过。

## 5. 未断言 / 未证事项

- 上述源侧请求链不等于 Sprite 实机渲染、线程或素材演出通过。
- `lPrivate` 是否被 OS 写入未断言。
- guest 原 MSG 布局未证。
- 未注册 guest 函数到 OS。


## editor-easy 后续 DLL / 消息组件交付：movie-attach-note-api

# DS_MOVIE.DLL 客体基址映射与 HIGHLOW 重定位验证

> 非翻译技术知识段。仅陈述已验证证据，不含推断。

## 1. 范围与状态

- 对象：`DS_MOVIE.DLL`
- 分支：共享 issue 分支
- 写入范围：仅本候选
- 规范缓存：root 规范缓存有效
- 操作约束：不 Git；不回退其他 editor 改动

## 2. 源指纹

| 项 | 值 |
|---|---|
| 算法 | SHA-256 |
| 源哈希 | `7eaad1746376f3a583b5b04c8c75a8dc57c1f0f334c22d21d269077857cc7ebb` |
| 原件 | 不变 |

## 3. 基址冲突与客体映射

| 项 | 值 |
|---|---|
| 首选基址 | `60000000` |
| 冲突方 | `DS_SPRITE` |
| 客体映射基址 | `61000000` |

首选 `60000000` 与 `DS_SPRITE` 冲突，故客体映射至 `61000000`。

## 4. HIGHLOW 重定位逐项验证

| 项 | 结果 |
|---|---|
| 重定位条目数 | 1523 |
| 验证方式 | 逐项验证 |
| 变更落点 | 仅在重定位字段 |
| ILT | 保持原貌 |
| 原件 | 不变 |

1523 条 HIGHLOW 逐项验证通过；被改写的位置仅为重定位项所指向的字段，导入查找表（ILT）未被改动。

## 5. 入口与装载返回

| 项 | 值 |
|---|---|
| 原 CPU 入口 | `6100464B` |
| 返回 | 以 `(61000000, 1, 0)` 自行返回 `1` |

原 CPU 入口为 `6100464B`；以 `(61000000, 1, 0)` 调用时自行返回 `1`。

## 6. 命名导出与原调用方解析

| 导出名 | RVA | 原调用方解析 |
|---|---|---|
| `GetDllVersion` | `3F80` | 已解析 |
| `GetMovieObject` | `3EF0` | 已解析 |

两个命名导出均为原调用方所解析。

## 7. 下一原请求

| 项 | 值 |
|---|---|
| 下一原请求 | `GetCursorPos` |

## 8. 未陈述项

本段不包含对上述证据之外的行为、调用顺序、失败模式或宿主进程状态的推断。


## root 验收状态与下一阶段行政交接

最终73夹具从正式helper目录运行，三新插件入口及原导出消费者、后DLL坐标读/写、两个自有事件ResetEvent接续到原CreateThread；源码仍未创建或执行此线程，未知进口保留严格停止。最终回调计数和系统API返回以canonical73原始JSON为准，不能固定成历史23回调或SetForeground0。宿主32/64MSG组件是独立SDK验证；原guest线程、TLS/CRT线程通知、并发调度、正常GameInit与画音留到下一主要阶段。所有canonical73 fixture由宿主显式清理，不是原shutdown；69失败夹具不计清理通过。
