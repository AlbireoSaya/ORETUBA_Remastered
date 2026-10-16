import ctypes

from lucifen_host_tls import current_thread_id, get_last_error, set_last_error
from lucifen_host_window_userdata_bindings import SetWindowLongPtrA

_GWL_STYLE = -16
_GWL_EXSTYLE = -20
_VALID_INDEXES = (_GWL_STYLE, _GWL_EXSTYLE)
_DWORD_MASK = 0xFFFFFFFF
_NATIVE_PTR_MAX = (1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1


def _require_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s must be a strict int" % (name,))
    return value


def _to_native_style_value(value32):
    # GWL_STYLE/GWL_EXSTYLE are DWORD style fields, not pointer fields.
    # On a 32-bit host the native slot is a signed c_ssize_t, so a DWORD with
    # the high bit set must be reinterpreted as a negative int32 before the
    # call. On a 64-bit host c_ssize_t is wide enough for the unsigned DWORD
    # value as-is.
    if ctypes.sizeof(ctypes.c_void_p) == 4 and value32 > 0x7FFFFFFF:
        return value32 - (1 << 32)
    return value32


def set_window_style(hwnd, index, value32, source_last_error):
    # Writes a DWORD style field; the returned native_result is the previous
    # raw DWORD reported as-is. No read-back, no success guessing, no
    # SetWindowPos follow-up, no GWL_WNDPROC (-4) / GWL_USERDATA (-21) support.
    _require_int("hwnd", hwnd)
    if hwnd <= 0 or hwnd > _NATIVE_PTR_MAX:
        raise ValueError("hwnd must be a positive int within native pointer range")
    _require_int("index", index)
    if index not in _VALID_INDEXES:
        raise ValueError("index must be -16 (GWL_STYLE) or -20 (GWL_EXSTYLE)")
    _require_int("value32", value32)
    if not 0 <= value32 <= _DWORD_MASK:
        raise ValueError("value32 must be within 0..0xFFFFFFFF")
    _require_int("source_last_error", source_last_error)
    if not 0 <= source_last_error <= _DWORD_MASK:
        raise ValueError("source_last_error must be within 0..0xFFFFFFFF")

    saved_error = get_last_error()
    try:
        set_last_error(source_last_error)
        native_result = SetWindowLongPtrA(hwnd, index, _to_native_style_value(value32))
        actual_error = get_last_error()
        actual_set_thread_id = current_thread_id()
    finally:
        set_last_error(saved_error)
    return {
        "previous_value32": native_result & _DWORD_MASK,
        "native_result": native_result,
        "actual_error": actual_error,
        "actual_set_thread_id": actual_set_thread_id,
    }