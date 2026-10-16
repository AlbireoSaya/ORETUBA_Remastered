import ctypes
import lucifen_readonly_io_bridge as _base

class ReadOnlyFilesLarge(_base.ReadOnlyFiles):
    def __init__(self, allowed_paths, max_transfer=32 << 20):
        if type(max_transfer) is not int or max_transfer < 1 or max_transfer > (64 << 20):
            raise ValueError("max_transfer out of range 1..67108864")
        super().__init__(allowed_paths)
        self._max_transfer = max_transfer

    def read(self, token, count):
        self._require_int(count, "count")
        if count < 0 or count > self._max_transfer:
            raise ValueError("count out of range 0..%d" % self._max_transfer)
        handle = self._live_handle(token)
        total = _base.GUARD_SIZE * 2 + count
        buffer = (ctypes.c_ubyte * total)()
        address = ctypes.addressof(buffer)
        ctypes.memset(address, _base.GUARD_BYTE, total)
        bytes_read = _base.wintypes.DWORD(0)
        ok = _base._kernel32.ReadFile(
            handle,
            ctypes.byref(buffer, _base.GUARD_SIZE),
            count,
            ctypes.byref(bytes_read),
            None,
        )
        error = 0 if ok else ctypes.get_last_error()
        head = ctypes.string_at(address, _base.GUARD_SIZE)
        tail = ctypes.string_at(address + _base.GUARD_SIZE + count, _base.GUARD_SIZE)
        if head != _base._GUARD_PATTERN or tail != _base._GUARD_PATTERN:
            raise RuntimeError("host read buffer guard was modified")
        transferred = bytes_read.value
        if transferred > count:
            raise RuntimeError("ReadFile reported more bytes than requested")
        actual_bytes = ctypes.string_at(address + _base.GUARD_SIZE, transferred)
        return (bool(ok), actual_bytes, error)
