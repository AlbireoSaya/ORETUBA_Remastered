import ctypes
import threading


class HostCOM:
    """Minimal single-threaded host COM initializer."""

    def __init__(self):
        self._tid = threading.get_ident()
        self._count = 0
        self._ole32 = ctypes.WinDLL("ole32", use_last_error=True)
        self._ole32.CoInitialize.argtypes = [ctypes.c_void_p]
        self._ole32.CoInitialize.restype = ctypes.c_long
        self._ole32.CoUninitialize.argtypes = []
        self._ole32.CoUninitialize.restype = None

    def _require_thread(self):
        if threading.get_ident() != self._tid:
            raise RuntimeError("HostCOM must be used from its creating thread")

    def init(self):
        self._require_thread()
        hr = self._ole32.CoInitialize(None)
        if hr >= 0:
            self._count += 1
        return hr

    def uninit(self):
        self._require_thread()
        if self._count <= 0:
            raise RuntimeError("HostCOM is not initialized")
        self._ole32.CoUninitialize()
        self._count -= 1

    def close_all(self):
        self._require_thread()
        while self._count > 0:
            self.uninit()

    @property
    def live_count(self):
        return self._count
