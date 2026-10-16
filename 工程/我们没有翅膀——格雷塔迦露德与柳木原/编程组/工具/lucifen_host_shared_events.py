"""Host-side shared Windows unnamed event objects (kernel32) for the Lucifen host process.

Ownership model: every handle in this module is a host (Win64) HANDLE created and
owned by a single host thread. Handles are kept at full pointer width; nothing here
is a guest-handle ABI and nothing here starts an original engine thread. A
HostSharedEvents instance additionally tracks the set of registered host threads
(identified by real Win64 DWORD thread IDs, never by Python thread identity) that
are permitted to operate on its handles.
"""

import ctypes
import threading

from lucifen_host_event import HostEvents, _k32, WAIT_OBJECT_0, WAIT_TIMEOUT, WAIT_FAILED
from lucifen_host_tls import current_thread_id


class HostSharedEvents(HostEvents):
    """Event handles usable from a registered set of real host OS threads.

    The creating host thread is the only thread allowed to register other host
    threads, and only real Win64 DWORD thread IDs of already-existing self-owned
    OS threads may be registered. _state_lock guards ownership, permission and
    lifecycle state; the blocking WaitForSingleObject path never holds it,
    because other registered threads must remain able to SetEvent the object
    being waited on.
    """

    def __init__(self):
        super().__init__()
        self._owner_tid = current_thread_id()
        self._allowed = {self._owner_tid}
        self._state_lock = threading.RLock()
        self._waiters = {}
        self._waiting_threads = {}

    def register_thread(self, tid):
        with self._state_lock:
            if current_thread_id() != self._owner_tid:
                raise RuntimeError("register_thread may only be called by the creating thread")
            if type(tid) is not int or tid < 1 or tid > 0xFFFFFFFF:
                raise ValueError("tid must be an int in 1..0xFFFFFFFF")
            if tid in self._allowed:
                raise ValueError("tid is already registered")
            self._allowed.add(tid)

    def _check_thread(self):
        with self._state_lock:
            if current_thread_id() not in self._allowed:
                raise RuntimeError("HostSharedEvents may only be used from a registered thread")

    def unregister_current_thread(self):
        with self._state_lock:
            tid = current_thread_id()
            if tid not in self._allowed:
                raise RuntimeError("current thread is not registered")
            if tid == self._owner_tid:
                raise RuntimeError("the creating thread cannot unregister itself")
            if self._waiting_threads.get(tid, 0) != 0:
                raise RuntimeError("current thread is still waiting on an event")
            self._allowed.discard(tid)

    def set(self, handle):
        with self._state_lock:
            self._check_thread()
            self._check_owned(handle)
            super().set(handle)

    def reset(self, handle):
        with self._state_lock:
            self._check_thread()
            self._check_owned(handle)
            super().reset(handle)

    def close(self, handle):
        with self._state_lock:
            self._check_thread()
            self._check_owned(handle)
            if self._waiters.get(handle, 0) != 0:
                raise RuntimeError("cannot close handle while host threads are waiting on it")
            super().close(handle)

    def wait(self, handle, timeout):
        if isinstance(timeout, bool) or not isinstance(timeout, int):
            raise TypeError("timeout must be a non-bool integer")
        if timeout < 0 or timeout > 0xFFFFFFFF:
            raise ValueError("timeout must be in range 0..0xFFFFFFFF")
        tid = current_thread_id()
        with self._state_lock:
            self._check_thread()
            self._check_owned(handle)
            self._waiters[handle] = self._waiters.get(handle, 0) + 1
            self._waiting_threads[tid] = self._waiting_threads.get(tid, 0) + 1
        try:
            rc = _k32.WaitForSingleObject(ctypes.c_void_p(handle), timeout)
            if rc == WAIT_OBJECT_0:
                return WAIT_OBJECT_0
            if rc == WAIT_TIMEOUT:
                return WAIT_TIMEOUT
            if rc == WAIT_FAILED:
                raise OSError(ctypes.get_last_error(), "WaitForSingleObject failed")
            raise OSError(ctypes.get_last_error(), "WaitForSingleObject returned unexpected status")
        finally:
            with self._state_lock:
                remaining = self._waiters.get(handle, 0) - 1
                if remaining > 0:
                    self._waiters[handle] = remaining
                else:
                    self._waiters.pop(handle, None)
                t_remaining = self._waiting_threads.get(tid, 0) - 1
                if t_remaining > 0:
                    self._waiting_threads[tid] = t_remaining
                else:
                    self._waiting_threads.pop(tid, None)

    def wait_zero(self, handle):
        return self.wait(handle, 0)

    def close_all(self):
        with self._state_lock:
            if current_thread_id() != self._owner_tid:
                raise RuntimeError("close_all may only be called from the owner thread")
            if self._allowed != {self._owner_tid}:
                raise RuntimeError("close_all requires exclusive ownership of every handle")
            if self._waiters or self._waiting_threads:
                raise RuntimeError("close_all refused while waiters or waiting threads are registered")
            return super().close_all()
