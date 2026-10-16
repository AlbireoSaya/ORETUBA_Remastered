"""Verify guest lstrcpyn bridge error paths: overlap rejection and read passthrough."""

import json

from lucifen_guest_lstrcpyn_guarded import bridge_lstrcpyn_bounded


def check_overlap_rejected_without_io():
    calls = []

    def read(addr, size):
        calls.append(("read", addr, size))
        raise AssertionError("read must not be called on overlap")

    def write(addr, data):
        calls.append(("write", addr, bytes(data)))

    try:
        bridge_lstrcpyn_bounded(read, write, 0x1000, 0x1000, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("overlap must raise ValueError")
    if calls:
        raise AssertionError("no io expected, got %r" % (calls,))


def check_read_error_propagated_without_write():
    boom = RuntimeError("boom")
    writes = []

    def read(addr, size):
        raise boom

    def write(addr, data):
        writes.append(("write", addr, bytes(data)))

    try:
        bridge_lstrcpyn_bounded(read, write, 0x1000, 0x2000, 4)
    except RuntimeError as exc:
        if exc is not boom:
            raise AssertionError("read error object not propagated identically")
    else:
        raise AssertionError("read RuntimeError must propagate")
    if writes:
        raise AssertionError("write must not run, got %r" % (writes,))


def main():
    check_overlap_rejected_without_io()
    check_read_error_propagated_without_write()
    print(json.dumps({"passed": True}))


if __name__ == "__main__":
    main()
