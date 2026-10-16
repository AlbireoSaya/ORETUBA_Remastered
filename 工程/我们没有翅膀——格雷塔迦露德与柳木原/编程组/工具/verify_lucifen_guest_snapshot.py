import hashlib
import json
import struct

from lucifen_guest_u32_snapshot import snapshot_u32

BASE = 0x1000
DATA = struct.pack("<2I", 0xAABBCCDD, 0x11223344)
COUNT = len(DATA)


def _expect_value_error(label, fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("%s: expected ValueError" % label)


def _expect_untouched(label, base, byte_count):
    def read(b, c):
        raise AssertionError("%s: read() must not be called" % label)

    _expect_value_error(label, lambda: snapshot_u32(read, base, byte_count))


def main():
    calls = []

    def read(base, byte_count):
        calls.append((base, byte_count))
        return DATA

    got = snapshot_u32(read, BASE, COUNT)
    assert calls == [(BASE, COUNT)], calls
    assert got["base"] == BASE, got
    assert got["byte_count"] == COUNT, got
    assert got["words"] == [0xAABBCCDD, 0x11223344], got
    assert got["sha256"] == hashlib.sha256(DATA).hexdigest(), got

    for read_alt in (lambda b, c: memoryview(DATA), lambda b, c: bytearray(DATA)):
        assert snapshot_u32(read_alt, BASE, COUNT) == got, read_alt

    for label, read_bad in (
        ("wronglen", lambda b, c: DATA[:-1]),
        ("wrongtype", lambda b, c: "12345678"),
    ):
        _expect_value_error(label, lambda: snapshot_u32(read_bad, BASE, COUNT))

    _expect_untouched("bounds-bool", True, COUNT)
    _expect_untouched("bounds-zero", BASE, 0)
    _expect_untouched("bounds-unaligned", BASE, 6)

    def boom(base, byte_count):
        raise RuntimeError("boom")

    try:
        snapshot_u32(boom, BASE, COUNT)
    except RuntimeError as exc:
        assert str(exc) == "boom", exc
    else:
        raise AssertionError("RuntimeError must propagate unchanged")

    print(json.dumps({"passed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())