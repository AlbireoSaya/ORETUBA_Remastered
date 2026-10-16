import ctypes
import os
import stat
from ctypes import wintypes
from pathlib import Path

_kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
INVALID_SET_FILE_POINTER = 0xFFFFFFFF
OPEN_FAILED_TOKEN = 0xFFFFFFFF

TOKEN_BASE = 0x60000000
TOKEN_LIMIT = 0xFFFFFFFE

MAX_TRANSFER = 0x100000
GUARD_SIZE = 128
GUARD_BYTE = 0xA5
_GUARD_PATTERN = bytes((GUARD_BYTE,)) * GUARD_SIZE

_kernel32.CreateFileW.argtypes = (
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
)
_kernel32.CreateFileW.restype = wintypes.HANDLE

_kernel32.ReadFile.argtypes = (
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
)
_kernel32.ReadFile.restype = wintypes.BOOL

_kernel32.SetFilePointer.argtypes = (
    wintypes.HANDLE,
    wintypes.LONG,
    wintypes.LPVOID,
    wintypes.DWORD,
)
_kernel32.SetFilePointer.restype = wintypes.DWORD

_kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
_kernel32.CloseHandle.restype = wintypes.BOOL


class ReadOnlyFiles:
    def __init__(self, allowed_paths):
        allowed = set()
        for candidate in allowed_paths:
            resolved = self._resolve_regular(candidate)
            allowed.add(os.path.normcase(str(resolved)))
        self._allowed = frozenset(allowed)
        self._handles = {}
        self._next_token = TOKEN_BASE

    @staticmethod
    def _resolve_regular(path):
        resolved = Path(os.fspath(path)).resolve(strict=True)
        if not stat.S_ISREG(os.stat(resolved).st_mode):
            raise ValueError("path is not a regular file")
        return resolved

    @staticmethod
    def _require_int(value, name):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("%s must be an int" % name)

    def _next_guest_token(self):
        if self._next_token > TOKEN_LIMIT:
            raise OverflowError("guest token space exhausted")
        token = self._next_token
        self._next_token += 1
        return token

    def _live_handle(self, token):
        self._require_int(token, "token")
        handle = self._handles.get(token)
        if handle is None:
            raise ValueError("token is not a live open handle")
        return handle

    def open(self, path):
        resolved = self._resolve_regular(path)
        if os.path.normcase(str(resolved)) not in self._allowed:
            raise PermissionError("path is not whitelisted")
        if self._next_token > TOKEN_LIMIT:
            raise OverflowError("guest token space exhausted")
        handle = _kernel32.CreateFileW(
            str(resolved),
            GENERIC_READ,
            FILE_SHARE_READ,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None,
        )
        if not handle or handle == INVALID_HANDLE_VALUE:
            return (OPEN_FAILED_TOKEN, ctypes.get_last_error())
        token = self._next_guest_token()
        self._handles[token] = handle
        return (token, 0)

    def read(self, token, count):
        self._require_int(count, "count")
        if count < 0 or count > MAX_TRANSFER:
            raise ValueError("count out of range 0..1048576")
        handle = self._live_handle(token)
        total = GUARD_SIZE * 2 + count
        buffer = (ctypes.c_ubyte * total)()
        address = ctypes.addressof(buffer)
        ctypes.memset(address, GUARD_BYTE, total)
        bytes_read = wintypes.DWORD(0)
        ok = _kernel32.ReadFile(
            handle,
            ctypes.byref(buffer, GUARD_SIZE),
            count,
            ctypes.byref(bytes_read),
            None,
        )
        error = 0 if ok else ctypes.get_last_error()
        head = ctypes.string_at(address, GUARD_SIZE)
        tail = ctypes.string_at(address + GUARD_SIZE + count, GUARD_SIZE)
        if head != _GUARD_PATTERN or tail != _GUARD_PATTERN:
            raise RuntimeError("host read buffer guard was modified")
        transferred = bytes_read.value
        if transferred > count:
            raise RuntimeError("ReadFile reported more bytes than requested")
        actual_bytes = ctypes.string_at(address + GUARD_SIZE, transferred)
        return (bool(ok), actual_bytes, error)

    def seek(self, token, low_signed, method):
        self._require_int(low_signed, "low_signed")
        if low_signed < -0x80000000 or low_signed > 0x7FFFFFFF:
            raise ValueError("low_signed out of int32 range")
        self._require_int(method, "method")
        if method not in (0, 1, 2):
            raise ValueError("method must be 0, 1 or 2")
        handle = self._live_handle(token)
        ctypes.set_last_error(0)
        low = _kernel32.SetFilePointer(handle, low_signed, None, method) & 0xFFFFFFFF
        error = ctypes.get_last_error()
        if low == INVALID_SET_FILE_POINTER and error != 0:
            return (low, error)
        return (low, 0)

    def close(self, token):
        handle = self._live_handle(token)
        ok = _kernel32.CloseHandle(handle)
        if not ok:
            return (False, ctypes.get_last_error())
        del self._handles[token]
        return (True, 0)

    def close_all(self):
        failures = []
        for token in list(self._handles):
            handle = self._handles[token]
            if _kernel32.CloseHandle(handle):
                del self._handles[token]
            else:
                failures.append((token, ctypes.get_last_error()))
        return failures

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        failures = self.close_all()
        if failures:
            raise RuntimeError(
                "failed to close %d handle(s)" % len(failures)
            ) from exc_value
        return False