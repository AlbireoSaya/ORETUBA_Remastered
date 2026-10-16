"""Prototype-only raw ctypes bindings for kernel32 named-mutex primitives.

This module is a prototype binding layer only. Importing it loads the real
system DLL (kernel32) and declares function signatures; it does NOT call any
API, does NOT errcheck, does NOT sandbox, and does NOT auto-validate.
The caller is responsible for:
  - ANSI name buffer lifetime and encoding for OpenMutexA / CreateMutexA;
  - full owned host handle lifetime (creation, ownership, Release, Close);
  - thread/ownership/Release/Close semantics;
  - guest ABI conversion across the raw boundary.
Security: only the genuine system DLL is loaded and declared here; no object is
created at import time; source-game DLLs are never loaded.
No original content or credentials are embedded.
"""

import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# RAW / DRAFT DECLARATIONS ONLY -- NOT VALIDATED, NOT EXERCISED HERE.
OpenMutexA = kernel32.OpenMutexA
OpenMutexA.restype = ctypes.c_void_p
OpenMutexA.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_void_p]

CreateMutexA = kernel32.CreateMutexA
CreateMutexA.restype = ctypes.c_void_p
CreateMutexA.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

ReleaseMutex = kernel32.ReleaseMutex
ReleaseMutex.restype = ctypes.c_int
ReleaseMutex.argtypes = [ctypes.c_void_p]
