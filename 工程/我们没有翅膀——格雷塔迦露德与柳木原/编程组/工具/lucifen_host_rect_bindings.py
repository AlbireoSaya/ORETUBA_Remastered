"""Raw ctypes prototypes for user32 SetRect and AdjustWindowRectEx.

Prototype-only module. It declares exactly two Windows user32 entry points as
Microsoft surfaces them: no wrappers, no helpers, no computational substitutes,
no __all__/exports, no errcheck, no sandboxing, no UI window creation, no GPU
work.

Caller contract (entirely the caller's responsibility, not enforced here):
  * RECT storage must be a full host-owned buffer of 16 bytes: four signed
    int32 fields (left, top, right, bottom), lifetime owned by the caller.
  * Both prototypes take c_void_p pointing at that host RECT. The pointer must
    reference host memory; a guest address must never be passed as the host
    pointer, and no guest-to-host translation is performed by this module.
  * Style, menu-present, and extended-style values are passed through as given.
  * Bounds guards, staging, host/guest conversion, and post-call validation all
    happen in the caller around these calls.

user32 is loaded at import time with use_last_error=True so callers can read
ctypes.get_last_error() themselves.

Issue context: ISSUE-20261011-02-original-fidelity.
"""

import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

SetRect = user32.SetRect
SetRect.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int32,
    ctypes.c_int32,
    ctypes.c_int32,
    ctypes.c_int32,
]
SetRect.restype = ctypes.c_int

AdjustWindowRectEx = user32.AdjustWindowRectEx
AdjustWindowRectEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_int,
    ctypes.c_uint32,
]
AdjustWindowRectEx.restype = ctypes.c_int
