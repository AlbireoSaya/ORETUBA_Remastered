"""Read-only ASCII file I/O for pre-whitelisted existing paths.

Scope limited to ASCII paths in the whitelist and GetFileSize with NULL high pointer.
"""

import ctypes
import os
from ctypes import wintypes

from lucifen_readonly_io_bridge import (
    INVALID_HANDLE_VALUE,
    OPEN_FAILED_TOKEN,
    TOKEN_LIMIT,
    ReadOnlyFiles,
    _kernel32 as kernel32,
)


class ReadOnlyAsciiFiles(ReadOnlyFiles):
    """Inherit base close/read/seek/context; add ASCII CreateFileA and size."""

    def open_ascii(self, payload, access, share, security, creation, flags, template):
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        if not (1 <= len(payload) <= 259):
            raise ValueError("payload length must be 1..259")
        if b"\x00" in payload:
            raise ValueError("payload must not contain NUL")
        try:
            decoded = payload.decode("ascii")
        except UnicodeDecodeError:
            raise ValueError("payload must be ASCII")

        expected = (0x80000000, 1, 0, 3, 0x80, 0)
        args = (access, share, security, creation, flags, template)
        names = ("access", "share", "security", "creation", "flags", "template")
        for val, exp, name in zip(args, expected, names):
            self._require_int(val, name)
            if isinstance(val, bool) or val != exp:
                raise ValueError(f"{name} must be {exp:#x}")

        resolved = self._resolve_regular(decoded)
        norm = os.path.normcase(str(resolved))
        if norm not in self._allowed:
            raise PermissionError("resolved path is not whitelisted")

        if self._next_token > TOKEN_LIMIT:
            raise OverflowError

        path_str = str(resolved)
        try:
            path_bytes = path_str.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("resolved path must be ASCII")
        if len(path_bytes) > 259:
            raise ValueError("resolved path too long")

        create_file_a = kernel32.CreateFileA
        create_file_a.argtypes = [
            wintypes.LPCSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        create_file_a.restype = wintypes.HANDLE

        ctypes.set_last_error(0)
        handle = create_file_a(
            path_bytes,
            access,
            share,
            security,
            creation,
            flags,
            template,
        )
        err = ctypes.get_last_error()

        if handle is None or handle == 0 or handle == INVALID_HANDLE_VALUE:
            return OPEN_FAILED_TOKEN, err

        token = self._next_guest_token()
        self._handles[token] = handle
        return token, 0

    def size(self, token, high_pointer=0):
        self._require_int(high_pointer, "high_pointer")
        if isinstance(high_pointer, bool) or high_pointer != 0:
            raise ValueError("high_pointer must be 0")

        handle = self._live_handle(token)

        get_file_size = kernel32.GetFileSize
        get_file_size.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        get_file_size.restype = wintypes.DWORD

        ctypes.set_last_error(0)
        low = get_file_size(handle, None)
        err = ctypes.get_last_error()

        if low == 0xFFFFFFFF and err != 0:
            return low, err
        return low, 0