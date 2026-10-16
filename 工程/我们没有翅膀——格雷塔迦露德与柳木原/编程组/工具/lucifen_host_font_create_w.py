import ctypes
from lucifen_host_logfont_w import LOGFONTW
system = ctypes.WinDLL('gdi32', use_last_error=True)
CreateFontIndirectW = system.CreateFontIndirectW
CreateFontIndirectW.argtypes = [ctypes.POINTER(LOGFONTW)]
CreateFontIndirectW.restype = ctypes.c_void_p
