"""Ownership contract for raw host user32 icon/cursor bindings.

Full-width host HICON/HCURSOR handles are preserved. Caller must guard the
DWORD-aligned original RT_GROUP_ICON validated data and RT_ICON buffers before
system calls; LookupIconIdFromDirectoryEx does not validate them.
CreateIconFromResourceEx with flags 0 creates an owned icon released by
DestroyIcon; never destroy a borrowed system cursor. A caller-local cache
substitutes for original LoadIconA sharing without actually loading the
original PE through the OS. GetIconInfo output uses an architecture-dependent
caller-owned layout, and returned HBITMAPs must be released with DeleteObject.
User, callback, and guest pointers are never passed to the OS.
"""

import ctypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)

LookupIconIdFromDirectoryEx = _user32.LookupIconIdFromDirectoryEx
LookupIconIdFromDirectoryEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
LookupIconIdFromDirectoryEx.restype = ctypes.c_int

CreateIconFromResourceEx = _user32.CreateIconFromResourceEx
CreateIconFromResourceEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
CreateIconFromResourceEx.restype = ctypes.c_void_p

DestroyIcon = _user32.DestroyIcon
DestroyIcon.argtypes = [ctypes.c_void_p]
DestroyIcon.restype = ctypes.c_int

LoadCursorA = _user32.LoadCursorA
LoadCursorA.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
LoadCursorA.restype = ctypes.c_void_p

GetIconInfo = _user32.GetIconInfo
GetIconInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
GetIconInfo.restype = ctypes.c_int
