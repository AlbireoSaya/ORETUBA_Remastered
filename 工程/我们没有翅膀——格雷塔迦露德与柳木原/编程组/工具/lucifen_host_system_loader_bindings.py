"""Raw ctypes bindings for host system loader primitives.

Issue: ISSUE-20261011-02-original-fidelity
Write scope: E:/ZCode Workspace/Galgame

Security/contract notes:
- This module only declares raw Win32 prototypes.
- rawLoadLibraryW can load an arbitrary library; it does not automatically
  restrict loads to system32.
- The caller must enforce a strict whitelist of complete system paths, exact
  module source, owned full HANDLE and reference lifetime, and buffer
  guard/capacity handling.
- These prototypes provide no sandbox and no validation. Source EXE/DLL files
  must not be host-loaded.
- Root current validation permits only the real system-directory ddraw.dll.
- Do not duplicate the existing official GetProcAddress binding here.
- Candidate only; staged only; no Git; no disabling the three roles; no
  exclusivity; do not revert others' changes; non-translation cache remains
  valid; do not falsely report tests.
"""

import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GetSystemDirectoryW = kernel32.GetSystemDirectoryW
GetSystemDirectoryW.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
GetSystemDirectoryW.restype = ctypes.c_uint32

LoadLibraryW = kernel32.LoadLibraryW
LoadLibraryW.argtypes = [ctypes.c_void_p]
LoadLibraryW.restype = ctypes.c_void_p

GetModuleFileNameW = kernel32.GetModuleFileNameW
GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
GetModuleFileNameW.restype = ctypes.c_uint32

FreeLibrary = kernel32.FreeLibrary
FreeLibrary.argtypes = [ctypes.c_void_p]
FreeLibrary.restype = ctypes.c_int
