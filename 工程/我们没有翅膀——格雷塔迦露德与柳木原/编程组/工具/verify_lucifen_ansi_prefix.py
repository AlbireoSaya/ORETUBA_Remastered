import json
from lucifen_guest_ansi_prefix import read_ansi_prefix

def main():
    def make(data, base=0x1000):
        log = []
        def read(q, n):
            log.append((q, n))
            if q < base or q + n > base + len(data):
                raise EOFError(q)
            return data[q - base:q - base + n]
        return read, log

    read, log = make(b"a\0")
    got = read_ansi_prefix(read, 0x1000, 41)
    assert got == b"a"
    assert log == [(0x1000, 1), (0x1001, 1)]

    read, log = make(b"a\0")
    got = read_ansi_prefix(read, 0x1000, 1)
    assert got == b""
    assert log == []

    read, log = make(b"abc")
    got = read_ansi_prefix(read, 0x1000, 3)
    assert got == b"ab"
    assert log == [(0x1000, 1), (0x1001, 1)]

    print(json.dumps({"passed": True}))

if __name__ == "__main__":
    main()
