"""Guest thread entry frame packing helper (pure stdlib).

Packs a thread-entry frame made of two little-endian unsigned 32-bit words:
the return sentinel and the parameter word.

Scope limits: this module is a byte-format utility only. It performs no OS
interaction, does not create threads, does not fabricate HANDLEs or TIDs, and
does not simulate completion of any source thread.

Bounds handling: arguments are not masked or truncated. Values outside the
unsigned 32-bit range (negative, or greater than 0xFFFFFFFF) are rejected by
``struct.error`` raised from ``struct.pack``.
"""

import struct

__all__ = ["pack_thread_entry_frame"]

_ENTRY_FRAME_FORMAT = "<2I"


def pack_thread_entry_frame(return_sentinel, parameter):
    """Pack ``return_sentinel`` and ``parameter`` into an 8-byte frame.

    The frame layout is ``<2I``: two little-endian unsigned 32-bit integers,
    sentinel first, parameter second.

    Both arguments must be integers that fit in an unsigned 32-bit word.
    No masking is applied; out-of-range values raise ``struct.error``.
    """
    return struct.pack(_ENTRY_FRAME_FORMAT, return_sentinel, parameter)
