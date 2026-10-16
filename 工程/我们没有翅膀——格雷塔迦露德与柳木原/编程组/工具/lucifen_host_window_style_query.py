import ctypes

from lucifen_host_tls import current_thread_id, get_last_error, set_last_error
from lucifen_host_window_userdata_bindings import GetWindowLongPtrA

_GWL_STYLE = -16
_GWL_EXSTYLE = -20
_VALID_INDEXES = (_GWL_STYLE, _GWL_EXSTYLE)
_DWORD_MASK = 0xFFFFFFFF
_NATIVE_PTR_MAX = (1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1


def _require_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s must be a strict int" % (name,))
    return value


def query_window_style(hwnd, index, source_last_error):
    # GWL_STYLE/GWL_EXSTYLE are DWORD style fields, not pointer fields:
    # the native result is reported as-is, never assumed to be a valid pointer.
    _require_int("hwnd", hwnd)
    if hwnd <= 0 or hwnd > _NATIVE_PTR_MAX:
        raise ValueError("hwnd must be a positive int within native pointer range")
    _require_int("index", index)
    if index not in _VALID_INDEXES:
        raise ValueError("index must be -16 (GWL_STYLE) or -20 (GWL_EXSTYLE)")
    _require_int("source_last_error", source_last_error)
    if not 0 <= source_last_error <= _DWORD_MASK:
        raise ValueError("source_last_error must be within 0..0xFFFFFFFF")

    saved_error = get_last_error()
    try:
        set_last_error(source_last_error)
        native_result = GetWindowLongPtrA(hwnd, index)
        actual_error = get_last_error()
        actual_query_thread_id = current_thread_id()
    finally:
        set_last_error(saved_error)
    return {
        "value32": native_result & _DWORD_MASK,
        "actual_error": actual_error,
        "native_result": native_result,
        "actual_query_thread_id": actual_query_thread_id,
    }