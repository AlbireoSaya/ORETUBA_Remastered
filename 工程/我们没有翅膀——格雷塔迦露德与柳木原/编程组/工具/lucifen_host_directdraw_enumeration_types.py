"""Raw ctypes prototypes for DirectDrawEnumerateExA host enumeration.

This module only declares two raw ctypes.WINFUNCTYPE types. It does not load
DLLs, call APIs, register callbacks, or implement any business/enumeration
logic.

DDENUMCALLBACKEXA corresponds to:
    BOOL WINAPI (GUID *lpGUID, LPSTR lpstrDescription, LPSTR lpstrModule,
                 LPVOID lpContext, HMONITOR hMonitor)
The five parameters are kept as ctypes.c_void_p to preserve raw addresses,
including the string parameters (LPSTR).

DirectDrawEnumerateExAProto corresponds to:
    HRESULT WINAPI DirectDrawEnumerateExA(
        LPDDENUMCALLBACKEXA lpCallback,
        LPVOID lpContext,
        DWORD dwFlags)

Safety and usage notes:
- These raw types provide neither sandboxing nor address validation.
- A caller must only construct these with a complete host address obtained via
  GetProcAddress from a verified system-directory ddraw DLL.
- Only real host Python callbacks may be registered with the OS. Guest
  function addresses are forbidden.
- Host GUID and string pointers are valid only during the callback; they must
  be copied if retained.
- Original guest callbacks are invoked separately when no emu_start is active.
- The original BOOL return value decides whether the real enumeration
  continues or stops.
- All host pointers are full-width.
- Do not leak original content outside the workspace.
"""

import ctypes

DDENUMCALLBACKEXA = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
)

DirectDrawEnumerateExAProto = ctypes.WINFUNCTYPE(
    ctypes.c_int32,
    DDENUMCALLBACKEXA,
    ctypes.c_void_p,
    ctypes.c_uint32,
)
