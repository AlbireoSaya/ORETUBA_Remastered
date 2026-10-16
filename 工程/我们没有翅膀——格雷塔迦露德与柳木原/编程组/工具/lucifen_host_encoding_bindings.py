import ctypes

k = ctypes.WinDLL('kernel32.dll', use_last_error=True)

_u32 = ctypes.c_uint32
_int = ctypes.c_int
_vp = ctypes.c_void_p

_BINDINGS = (
    ((_u32, _u32, _vp, _int, _vp, _int, _vp, _vp), ('WideCharToMultiByte',)),
    ((_u32, _u32, _vp, _int, _vp, _int), ('MultiByteToWideChar', 'LCMapStringW', 'LCMapStringA')),
    ((_u32, _vp, _int, _vp), ('GetStringTypeW',)),
    ((_u32, _u32, _vp, _int, _vp), ('GetStringTypeA',)),
)

for _argtypes, _names in _BINDINGS:
    for _name in _names:
        _fn = getattr(k, _name)
        _fn.argtypes = _argtypes
        _fn.restype = _int
        globals()[_name] = _fn
del _argtypes, _names, _name, _fn
