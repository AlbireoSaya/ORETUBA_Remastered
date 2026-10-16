"""Minimal host binding for kernel32!SetHandleCount (no invocation)."""

import ctypes

kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

SetHandleCount = kernel32.SetHandleCount
SetHandleCount.argtypes = [ctypes.c_uint32]
SetHandleCount.restype = ctypes.c_uint32
