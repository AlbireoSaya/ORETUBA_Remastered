"""Verify the guarded guest lstrcpynA bridge on the single real case."""
import json

from lucifen_guest_lstrcpyn_guarded import bridge_lstrcpyn_bounded

SRC, DST, LIMIT = 0x2000, 0x1000, 41


def main():
    src_bytes = {SRC: b"a", SRC + 1: b"\x00"}
    dst_bytes = bytes([90]) * LIMIT
    src_log, writes = [], []

    def read(q, n):
        if q == DST:
            assert n == LIMIT
            return dst_bytes
        if n != 1 or q not in src_bytes:
            raise EOFError("unexpected read %#x/%d" % (q, n))
        src_log.append((q, 1))
        return src_bytes[q]

    def write(q, blob):
        writes.append((q, bytes(blob)))

    returned = bridge_lstrcpyn_bounded(read, write, DST, SRC, LIMIT)
    expected = b"a\x00" + b"Z" * 39
    assert returned == DST
    assert writes == [(DST, expected)]
    assert src_log == [(SRC, 1), (SRC + 1, 1)]
    print(json.dumps({"passed": True, "returned": returned, "src_reads": src_log}))


if __name__ == "__main__":
    main()
