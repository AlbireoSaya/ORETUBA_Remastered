"""Raw ctypes prototypes for a subset of host kernel32.

Importing this module loads kernel32 from the host process via
ctypes.WinDLL(\"kernel32\", use_last_error=True).  Only four raw prototype
declarations are made here: no errcheck is installed and no API is called.

The caller is responsible for work-area path mapping, Unicode buffer
lifetimes, complete host handles, and guest-pointer mapping.  These
prototypes are not a sandbox.
"""

import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

CreateDirectoryW = kernel32.CreateDirectoryW
CreateDirectoryW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
CreateDirectoryW.restype = ctypes.c_int

CopyFileW = kernel32.CopyFileW
CopyFileW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
CopyFileW.restype = ctypes.c_int

SetFileAttributesW = kernel32.SetFileAttributesW
SetFileAttributesW.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
SetFileAttributesW.restype = ctypes.c_int

GetFileSize = kernel32.GetFileSize
GetFileSize.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
GetFileSize.restype = ctypes.c_uint32