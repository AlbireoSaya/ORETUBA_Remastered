# lucifen_host_crt_bootstrap_bindings.py
# Raw ctypes bindings only. No wrapping, no calls, no I/O.

import ctypes

kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

__all__ = [
    "GetVersion",
    "GetACP",
    "GetOEMCP",
    "IsProcessorFeaturePresent",
    "GetModuleHandleA",
    "GetProcAddress",
    "GetCommandLineA",
    "GetStdHandle",
    "GetFileType",
    "GetStartupInfoA",
    "GetEnvironmentStrings",
    "FreeEnvironmentStringsA",
    "GetEnvironmentStringsW",
    "FreeEnvironmentStringsW",
    "GetCPInfo",
]

GetVersion = kernel32.GetVersion
GetVersion.argtypes = []
GetVersion.restype = ctypes.c_uint32
kernel32.GetVersion = GetVersion

GetACP = kernel32.GetACP
GetACP.argtypes = []
GetACP.restype = ctypes.c_uint32
kernel32.GetACP = GetACP

GetOEMCP = kernel32.GetOEMCP
GetOEMCP.argtypes = []
GetOEMCP.restype = ctypes.c_uint32
kernel32.GetOEMCP = GetOEMCP

IsProcessorFeaturePresent = kernel32.IsProcessorFeaturePresent
IsProcessorFeaturePresent.argtypes = [ctypes.c_uint32]
IsProcessorFeaturePresent.restype = ctypes.c_int
kernel32.IsProcessorFeaturePresent = IsProcessorFeaturePresent

GetModuleHandleA = kernel32.GetModuleHandleA
GetModuleHandleA.argtypes = [ctypes.c_char_p]
GetModuleHandleA.restype = ctypes.c_void_p
kernel32.GetModuleHandleA = GetModuleHandleA

GetProcAddress = kernel32.GetProcAddress
GetProcAddress.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
GetProcAddress.restype = ctypes.c_void_p
kernel32.GetProcAddress = GetProcAddress

GetCommandLineA = kernel32.GetCommandLineA
GetCommandLineA.argtypes = []
GetCommandLineA.restype = ctypes.c_void_p
kernel32.GetCommandLineA = GetCommandLineA

GetStdHandle = kernel32.GetStdHandle
GetStdHandle.argtypes = [ctypes.c_uint32]
GetStdHandle.restype = ctypes.c_void_p
kernel32.GetStdHandle = GetStdHandle

GetFileType = kernel32.GetFileType
GetFileType.argtypes = [ctypes.c_void_p]
GetFileType.restype = ctypes.c_uint32
kernel32.GetFileType = GetFileType

GetStartupInfoA = kernel32.GetStartupInfoA
GetStartupInfoA.argtypes = [ctypes.c_void_p]
GetStartupInfoA.restype = None
kernel32.GetStartupInfoA = GetStartupInfoA

GetEnvironmentStrings = kernel32.GetEnvironmentStrings
GetEnvironmentStrings.argtypes = []
GetEnvironmentStrings.restype = ctypes.c_void_p
kernel32.GetEnvironmentStrings = GetEnvironmentStrings

FreeEnvironmentStringsA = kernel32.FreeEnvironmentStringsA
FreeEnvironmentStringsA.argtypes = [ctypes.c_void_p]
FreeEnvironmentStringsA.restype = ctypes.c_int
kernel32.FreeEnvironmentStringsA = FreeEnvironmentStringsA

GetEnvironmentStringsW = kernel32.GetEnvironmentStringsW
GetEnvironmentStringsW.argtypes = []
GetEnvironmentStringsW.restype = ctypes.c_void_p
kernel32.GetEnvironmentStringsW = GetEnvironmentStringsW

FreeEnvironmentStringsW = kernel32.FreeEnvironmentStringsW
FreeEnvironmentStringsW.argtypes = [ctypes.c_void_p]
FreeEnvironmentStringsW.restype = ctypes.c_int
kernel32.FreeEnvironmentStringsW = FreeEnvironmentStringsW

GetCPInfo = kernel32.GetCPInfo
GetCPInfo.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
GetCPInfo.restype = ctypes.c_int
kernel32.GetCPInfo = GetCPInfo
