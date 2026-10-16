import ctypes

from lucifen_host_glyph_types import MAT2, GLYPHMETRICS

system = ctypes.WinDLL('gdi32', use_last_error=True)

GDI_ERROR = 0xFFFFFFFF

GetGlyphOutlineA = system.GetGlyphOutlineA
GetGlyphOutlineA.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.POINTER(GLYPHMETRICS),
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.POINTER(MAT2),
]
GetGlyphOutlineA.restype = ctypes.c_uint32
