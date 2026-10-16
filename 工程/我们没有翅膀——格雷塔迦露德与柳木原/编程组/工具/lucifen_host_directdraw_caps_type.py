"""IDirectDraw7::GetCaps FFI prototype declaration.

HRESULT WINAPI GetCaps(this, DDCAPS *driver, DDCAPS *HEL); slot 11 of verified real IDirectDraw7.

Construct only from a full-width real owned interface vtable address.
Caller checks the exact guest dwSize (380 for DX7 in this phase),
independently guarded buffers, ownership/thread, and input/output copying.
DDCAPS has DWORD fields, no pointer translation; null pointers remain null.
Preserve actual HRESULT and bytes even for failure.
No DLL load or function invocation here.
No sandbox, address/buffer validation, guest OS callbacks, or rendering completion claim.
"""

import ctypes

IDirectDrawGetCapsProto = ctypes.WINFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
