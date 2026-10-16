"""Error-path checks for lucifen_guest_ansi_prefix.read_ansi_prefix."""
import json

from lucifen_guest_ansi_prefix import read_ansi_prefix


def _err(source, limit, first=b"x"):
    calls = []

    def read(addr, size):
        calls.append(addr)
        return first

    try:
        read_ansi_prefix(read, source, limit)
        return -1
    except ValueError:
        return len(calls)


def _rt():
    err = RuntimeError("boom")

    def read(addr, size):
        raise err

    try:
        read_ansi_prefix(read, 1, 4)
    except RuntimeError as exc:
        return exc is err
    return False


def main():
    checks = {
        "source_true_no_read": _err(True, 4) == 0,
        "source_zero_no_read": _err(0, 4) == 0,
        "limit_true_no_read": _err(1, True) == 0,
        "limit_zero_no_read": _err(1, 0) == 0,
        "overrun_after_one_read": _err(0xFFFFFFFF, 3, b"a") == 1,
        "runtime_error_passthrough": _rt(),
    }
    assert all(checks.values()), checks
    print(json.dumps({"passed": all(checks.values()), "checks": checks}))


if __name__ == "__main__":
    main()
