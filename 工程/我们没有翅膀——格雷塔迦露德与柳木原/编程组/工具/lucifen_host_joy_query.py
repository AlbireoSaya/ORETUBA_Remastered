"""Host-side joystick query bindings (winmm) for the Lucifen host layer.

Raw read-only declarations only. Every output structure is mapped by the
caller into a caller-owned host buffer; no guest pointers cross this
boundary, no SetCapture, no input injection, no original-game loading.
"""

import ctypes

winmm = ctypes.WinDLL("winmm", use_last_error=True)

joyGetDevCapsA = winmm.joyGetDevCapsA
joyGetDevCapsA.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_uint32]
joyGetDevCapsA.restype = ctypes.c_uint32

joyGetPos = winmm.joyGetPos
joyGetPos.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
joyGetPos.restype = ctypes.c_uint32

joyGetPosEx = winmm.joyGetPosEx
joyGetPosEx.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
joyGetPosEx.restype = ctypes.c_uint32

JOYERR_NOERROR = 0

__all__ = (
    "winmm",
    "joyGetDevCapsA",
    "joyGetPos",
    "joyGetPosEx",
    "JOYERR_NOERROR",
)