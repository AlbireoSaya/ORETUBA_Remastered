"""Raw kernel32 GetDriveTypeA binding (declaration only).

Prototype (raw, as declared by kernel32):

    UINT GetDriveTypeA(
        LPCSTR lpRootPathName   // c_void_p here: caller owns the ANSI buffer
    );

No calling, no errcheck, no fallback, no wrapper, no validation.
The caller owns the ANSI buffer lifecycle and the full host pointer.
NULL is a legal raw input and is passed through untouched.
"""

import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GetDriveTypeA = kernel32.GetDriveTypeA
GetDriveTypeA.argtypes = [ctypes.c_void_p]
GetDriveTypeA.restype = ctypes.c_uint32
