"""ctypes bindings for advapi32 registry APIs only.

No permission, handle or buffer management is provided here.
Callers must use these solely to read the two Windows system keys,
solely with an HKEY and buffer they already own, and must never
fabricate real state.
"""
import ctypes
from ctypes import POINTER, WinDLL, c_char_p, c_long, c_uint32, c_void_p
_advapi32 = WinDLL("advapi32")
RegOpenKeyExA = _advapi32.RegOpenKeyExA
RegOpenKeyExA.argtypes = [c_void_p, c_char_p, c_uint32, c_uint32, POINTER(c_void_p)]
RegOpenKeyExA.restype = c_long
RegQueryValueExA = _advapi32.RegQueryValueExA
RegQueryValueExA.argtypes = [c_void_p, c_char_p, c_void_p, POINTER(c_uint32), c_void_p, POINTER(c_uint32)]
RegQueryValueExA.restype = c_long
RegCloseKey = _advapi32.RegCloseKey
RegCloseKey.argtypes = [c_void_p]
RegCloseKey.restype = c_long
HKLM = c_void_p(-2147483646)
KEY_READ_32 = 0x20219
