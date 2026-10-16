"""lucifen_host_directdraw_com_types.py — ISSUE-20261011-02 原始 Win32/COM ABI 类型绑定。

本文件是唯一产物：只提供 ole32 / CoCreateInstance 原始绑定与两个 WINFUNCTYPE 原型，
不含任何调用、校验、包装、sandbox 或复现逻辑。

硬性约束（全部由 caller 自负，本模块既检查也不保证）：
- 本模块不 sandbox、不验证：不检查 HRESULT，不重试，不改写失败。
- CoCreate GUID 白名单由 caller 唯一自负：caller 仅准许使用经原作实测并以 SDK
  交叉核对的 CLSID_DirectDraw {d7b70ee0-4340-11cf-b063-0020afc2cd35}；
  dwClsContext 仅 CLSCTX_INPROC_SERVER = 1；pUnkOuter = NULL；
  riid = IID_IDirectDraw7 {15e65ec0-3b9c-11d2-b92f-00609797ea5b}。
  后续 QI 仅准许 IID_IDirect3D7 {f5049e77-4861-11d2-a407-00a0c90629a8}
  （SDK d3d.h 第 41 行；该 GUID 不是 IDirectDrawGammaControl，
  真正的 IDirectDrawGammaControl IID 为 {69c11c3e-b46b-11d1-ad7a-00c04fc29b4e}，
  本模块既不绑定也不授权它）。
  其他 CLSID / IID / 上下文组合一律不在授权范围内。
- 不得经 OS 加载任何游戏 DLL：不 LoadLibrary、不注入、不向 OS 注册任何东西。
- 禁止把 guest 指针带入 OS：任何 guest 地址、guest 函数或 guest 缓冲区都不得
  作为参数、回调或上下文交给 ole32 / COM / 任何主机 API。
- GUID16 使用自有 guard 缓冲区；out-pointer、full-host ptr、生命周期与引用计数均由 caller 负责。
- COM vtable slot 按真实满宽（full-width）指针布局：IUnknown::QueryInterface 实际位于
  slot 0；IDirectDraw7::Initialize 实际位于 slot 18。完整函数地址只可从真实 owned
  接口的 VTBL 读出后构造，禁止凭偏移臆测。
- 所有失败 HRESULT 必须真实原样保留、原样向上返回；真实 IUnknown::Release 由已有模块
  负责，本模块不代劳。
- 主机 COM 线程的 CoInitialize/CoUninitialize 必须平衡。
- 这些原型不构成、也不得被声称构成图形功能或原作行为的已完成复现。
"""

import ctypes
from ctypes import POINTER, WINFUNCTYPE, c_int32, c_uint32, c_void_p

ole32 = ctypes.WinDLL("ole32", use_last_error=True)

CoCreateInstance = ole32.CoCreateInstance
CoCreateInstance.argtypes = [c_void_p, c_void_p, c_uint32, c_void_p, POINTER(c_void_p)]
CoCreateInstance.restype = c_int32

IUnknownQueryInterfaceProto = WINFUNCTYPE(c_int32, c_void_p, c_void_p, POINTER(c_void_p))
IDirectDrawInitializeProto = WINFUNCTYPE(c_int32, c_void_p, c_void_p)
