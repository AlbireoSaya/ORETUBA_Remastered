"""Guest exception filter state for a controlled guest harness.

This module stores a single guest exception filter pointer as a 32-bit
unsigned integer.  The state is single-threaded and caller-controlled:
it is explicitly NOT atomic and NOT thread-safe, and callers must
serialize access themselves.

This is also NOT a Win32 host exception filter.  Nothing here performs
OS calls, I/O, or code execution.  The mere existence of this module
does not prove that any original guest process ever started, was
launched, or produced this value.

A non-zero pointer is only a caller-supplied claim.  This module does
not validate it in any way; the caller is responsible for verifying
that a non-zero pointer refers to already-mapped guest code before
relying on it.
"""

_U32_MAX = 0xFFFFFFFF


class GuestExceptionFilter:
    """Single-threaded holder for a guest exception filter pointer.

    See the module docstring for the deliberately limited guarantees of
    this class: single-threaded, caller-controlled guest state, not
    atomic, not thread-safe, not a Win32 host filter, and not evidence
    that the original guest ever started.
    """

    __slots__ = ("current",)

    def __init__(self):
        """Initialize the stored filter pointer to zero.

        ``current == 0`` represents "no guest exception filter
        installed".  No validation, OS call, or I/O is performed.
        """
        self.current = 0

    def exchange(self, pointer):
        """Store ``pointer`` and return the previously stored pointer.

        ``pointer`` must be an exact ``int`` (checked with
        ``type(pointer) is int``; ``bool`` and other ``int`` subclasses
        are rejected) within the unsigned 32-bit range ``0 ..
        0xFFFFFFFF``.  The previous value is read and returned before
        the new value is saved, so the caller observes exactly the
        value that was replaced.

        This operation provides no atomicity, no locking, and no
        thread-safety; it is intended for single-threaded,
        caller-controlled use only.  It performs no OS calls, no I/O,
        and no execution of guest or host code, and it is not a Win32
        host exception filter.  A non-zero ``pointer`` is not checked
        against any mapping table: the caller must verify that it
        refers to already-mapped guest code.
        """
        if type(pointer) is not int:
            raise TypeError(
                "pointer must be exactly int, got %s"
                % (type(pointer).__name__,)
            )
        if pointer < 0 or pointer > _U32_MAX:
            raise ValueError(
                "pointer out of u32 range [0, %d]: %d"
                % (_U32_MAX, pointer)
            )
        previous = self.current
        self.current = pointer
        return previous
